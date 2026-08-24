#!/usr/bin/env python3
"""
Gizmo's Picks -- the daily card, generated on the runner.

This is the last manual step in the project, automated. It runs the v4.0
projection model over the game logs the collector already stores, joins it
to the Hard Rock prop board, and writes picks/<date>.json.

WHAT IT DOES NOT DO, DELIBERATELY:

  * It does not pick. Every qualifying pitcher prop on the board is
    printed with its numbers attached (ledger rule 53). A play that fails
    a check is LABELLED, never deleted. The selection is Sam's.
  * It does not adopt an unadopted test. T21 (perfect-record shrinkage)
    and T22 (the shuttled-starter penalty) are PRE-REGISTERED AND NOT
    ADOPTED. So `blend` -- the number that enters the calibration table --
    is the plain 50/50, exactly as every other play in that table is, and
    the flagged number lives in a separate `carried` column that enters no
    denominator. Both are written. This mirrors the 8/22 card.
  * It does not fold the matched class into anything. STEP 4B is a flag.
  * It does not show a pair below 1.8x. Sam's own instruction, and the one
    deliberate exception to rule 53.
  * It does not invent a price. Every price here came out of a raw pull
    and carries the minute it was pulled (ledger rule 49).

USAGE:  python card.py            -- write today's card
        python card.py --dry      -- print it, write nothing
"""

import gzip
import json
import math
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone

MODEL_VERSION = "v4.0"

# Sam's board size, in his words: "i would like to see 25-50 players
# everytime, including hitters props as well as pitchers."
BOARD_MIN, BOARD_MAX = 25, 50

# ---------------------------------------------------------------- model
# claude/mlb-projection-model.md. Do not edit a coefficient here without
# editing it there, and do not edit it there without a re-fit.
K_INTERCEPT, K_TRAIL_B, K_TRAIL_C = 4.939, 0.673, 4.949
K_OPP_B, K_HOME = 0.575, 0.151
O_INTERCEPT, O_TRAIL_C = 15.899, 15.903
O_NP_B, O_NP_C = 0.0371, 86.6
O_HOME = 0.189
TRAIL_N = 8


def outs_k(trailing_outs):
    """The trailing-outs slope is TIERED on his own level. Pooled 0.525 is
    a reference figure for the v3.4 comparison and is NOT shipped."""
    if trailing_outs < 15.25:
        return 0.638
    if trailing_outs < 17.0:
        return 0.759
    return 0.317


# T21's measured grid (claude/owed-tests.md). NOT ADOPTED -- used only for
# the shadow `carried` column, never for `blend`.
T21_PERFECT_LONG = 88.8      # 100% on 9+ prior starts -> 88.8% next
T21_PERFECT_SHORT = 78.0     # 100% on 3-8 prior starts -> 78.0% next
T22_SHUTTLE_PENALTY = 14.4   # point-in-time, z = 6.97

# Calibration bands, from claude/calibration-accumulators.md. These are a
# LABEL on the row, not a filter.
def band_of(p):
    if p < 60:
        return ("under-60", "too few graded plays in this range to say anything")
    if p < 70:
        return ("60-70", "the record in this band runs -25.9 against the claim")
    if p < 80:
        return ("70-80", "the only band whose record supports the number")
    return ("80-plus", "the record in this band runs -18.0 against the claim")


# ------------------------------------------------------------ distributions
def pois_cdf(lam, k):
    """P(X <= k) for integer k >= 0."""
    if k < 0:
        return 0.0
    t, s = math.exp(-lam), 0.0
    for i in range(0, k + 1):
        s += t
        t *= lam / (i + 1)
    return min(1.0, s)


def norm_cdf(x, mu, sd):
    if sd <= 0:
        return 1.0 if x >= mu else 0.0
    return 0.5 * (1.0 + math.erf((x - mu) / (sd * math.sqrt(2.0))))


def implied(american):
    a = float(american)
    return 100.0 / (a + 100.0) if a > 0 else (-a) / (-a + 100.0)


def decimal(american):
    a = float(american)
    return 1.0 + (a / 100.0 if a > 0 else 100.0 / -a)


# ---------------------------------------------------------------- helpers
ABBR = {
    'Cincinnati Reds': 'CIN', 'Los Angeles Angels': 'LAA', 'New York Yankees': 'NYY',
    'Pittsburgh Pirates': 'PIT', 'Baltimore Orioles': 'BAL', 'Athletics': 'ATH',
    'Chicago White Sox': 'CWS', 'Colorado Rockies': 'COL', 'Philadelphia Phillies': 'PHI',
    'San Diego Padres': 'SD', 'Seattle Mariners': 'SEA', 'Chicago Cubs': 'CHC',
    'Miami Marlins': 'MIA', 'Houston Astros': 'HOU', 'Boston Red Sox': 'BOS',
    'Texas Rangers': 'TEX', 'New York Mets': 'NYM', 'Washington Nationals': 'WSH',
    'Detroit Tigers': 'DET', 'Milwaukee Brewers': 'MIL', 'Los Angeles Dodgers': 'LAD',
    'Atlanta Braves': 'ATL', 'Kansas City Royals': 'KC', 'San Francisco Giants': 'SF',
    'Minnesota Twins': 'MIN', 'Toronto Blue Jays': 'TOR', 'Cleveland Guardians': 'CLE',
    'St. Louis Cardinals': 'STL', 'Arizona Diamondbacks': 'AZ', 'Tampa Bay Rays': 'TB',
}


def norm_name(n):
    """Same fold the collector uses, so a ladder key matches a prop name."""
    if not n:
        return ""
    n = unicodedata.normalize("NFKD", n)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower().replace(".", "").replace("'", "").replace("-", " ")
    n = n.replace(" jr", "").replace(" sr", "").replace(" iii", "").replace(" ii", "")
    return " ".join(n.split())


def ab(name):
    return ABBR.get(name, (name or "")[:3].upper())


def starts_of(p):
    """His starts, oldest first. Relief outings are not evidence about a
    starter's line and mixing them in silently deflates every rate."""
    rows = [r for r in p["g"] if r.get("gs")]
    rows.sort(key=lambda r: r.get("d") or "")
    return rows


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def sd(xs):
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


# ------------------------------------------------------- opponent table
def opponent_table(players):
    """Rebuild the opponent meanK from the same pull the model reads, and
    take the centering constant from that same rebuild.

    claude/mlb-opponent-database.md owns the published table, and its own
    regeneration recipe is exactly this: group the start table by opponent,
    take the mean of strikeOuts. The published copy can only be rebuilt in
    an interactive browser session, so it goes stale by a slate at a time;
    this one rebuilds nightly off the collector's pool.

    ⚠️ The pool is IP-filtered, so it holds ~99% of season starts rather
    than all of them. Measured 2026-08-23 against the published table:
    mean |dE[K]| difference 0.021 K, max 0.064 K -- inside the ~0.045 K
    the opponent doc itself quotes as the cost of a one-slate lag. The
    variable and its centering constant come from the SAME pull, which is
    the property that actually matters: a meanK from one scale centred on
    a constant from another is this project's oldest documented bug.
    """
    opp, tot, n = {}, 0, 0
    for v in players.values():
        for r in v["g"]:
            if r.get("gs") and r.get("k") is not None and r.get("o"):
                opp.setdefault(r["o"], []).append(r["k"])
    for v in opp.values():
        tot += sum(v)
        n += len(v)
    means = {t: sum(v) / len(v) for t, v in opp.items()}
    return means, {t: len(v) for t, v in opp.items()}, (tot / n if n else 0.0), n


# --------------------------------------------------------- matched class
def matched_class_k(players, opp_team, line, side, k9, today):
    """STEP 4B on the strikeout axis: starters within +/-1.5 season K/9."""
    allh = alln = fh = fn = 0
    notable = []
    for v in players.values():
        rows = starts_of(v)
        tot_o = sum(r["outs"] for r in rows if r.get("outs") is not None)
        tot_k = sum(r["k"] for r in rows if r.get("k") is not None)
        if tot_o < 30:
            continue
        their_k9 = tot_k * 27.0 / tot_o
        if abs(their_k9 - k9) > 1.5:
            continue
        for r in rows:
            if r.get("o") != opp_team or r.get("k") is None or (r.get("d") or "") >= today:
                continue
            hit = (r["k"] > line) if side == "over" else (r["k"] < line)
            alln += 1
            allh += 1 if hit else 0
            if (r.get("outs") or 0) >= 12:
                fn += 1
                fh += 1 if hit else 0
            notable.append((r["k"], v["name"], r["d"], r["outs"], hit))
    notable.sort(key=lambda x: -x[0])
    return allh, alln, fh, fn, notable


def matched_class_outs(players, opp_team, line, side, trail_bucket, today):
    """STEP 4B on the DURABILITY axis -- owed test T24.

    Sam's correction, 8/22: 'how many of those pitchers are tiers above
    ryan johnson.' An outs line is a workload question, so the comparison
    class is trailing mean outs AT THE TIME OF THE START, point-in-time --
    not K/9, which is what a first pass used and which put Irvin at 46.9%
    when the durability-matched class said 66.7%.
    """
    allh = alln = fh = fn = 0
    notable = []
    for v in players.values():
        rows = starts_of(v)
        for i, r in enumerate(rows):
            if r.get("o") != opp_team or r.get("outs") is None or (r.get("d") or "") >= today:
                continue
            prior = [x["outs"] for x in rows[max(0, i - TRAIL_N):i] if x.get("outs") is not None]
            if len(prior) < 3:
                continue
            if outs_bucket(sum(prior) / len(prior)) != trail_bucket:
                continue
            hit = (r["outs"] > line) if side == "over" else (r["outs"] < line)
            alln += 1
            allh += 1 if hit else 0
            if r["outs"] >= 12:
                fn += 1
                fh += 1 if hit else 0
            notable.append((r["outs"], v["name"], r["d"], r["outs"], hit))
    notable.sort(key=lambda x: -x[0])
    return allh, alln, fh, fn, notable


def outs_bucket(m):
    if m < 14:
        return "<14"
    if m < 16:
        return "14-16"
    if m < 18:
        return "16-18"
    return "18+"


# ------------------------------------------------------------- one play
def build_play(prop, p, players, oppK, centerC, oppn, game, today):
    """Every number on one row. Returns None only when the inputs to the
    model are genuinely absent -- never because the answer was unflattering."""
    market = "strikeouts" if prop["market"] == "pitcher_strikeouts" else "outs"
    line, side = float(prop["line"]), prop["side"]
    rows = starts_of(p)
    prior = [r for r in rows if (r.get("d") or "") < today]
    if len(prior) < 3:
        return None
    trail = prior[-TRAIL_N:]

    home = 1 if p["team"] == game["home"] else 0
    if p["team"] not in (game["home"], game["away"]):
        return None                      # rule 32: never guess a team

    tot_o = sum(r["outs"] for r in prior if r.get("outs") is not None)
    tot_k = sum(r["k"] for r in prior if r.get("k") is not None)
    k9 = tot_k * 27.0 / tot_o if tot_o else 0.0
    era = float(p["era"]) if p.get("era") not in (None, "-", "") else None

    # ---- model
    if market == "strikeouts":
        mK8 = mean([r["k"] for r in trail])
        if mK8 is None or oppK is None:
            return None
        lam = (K_INTERCEPT + K_TRAIL_B * (mK8 - K_TRAIL_C)
               + K_OPP_B * (oppK - centerC) + (K_HOME if home else -K_HOME))
        lam = max(0.05, lam)
        cdf = pois_cdf(lam, int(math.floor(line)))
        model = (1.0 - cdf) if side == "over" else cdf
        central = round(lam, 2)
        inputs = {"trailing8_K": round(mK8, 2), "opp_meanK": round(oppK, 3),
                  "centering_constant": round(centerC, 4), "home": bool(home),
                  "E_K": central}
    else:
        mO8 = mean([r["outs"] for r in trail])
        prevNP = trail[-1].get("np")
        if mO8 is None or prevNP is None:
            return None
        mu = (O_INTERCEPT + outs_k(mO8) * (mO8 - O_TRAIL_C)
              + O_NP_B * (prevNP - O_NP_C) + (O_HOME if home else -O_HOME))
        season_outs = mean([r["outs"] for r in prior])
        s_sd = sd([r["outs"] for r in prior])
        if not season_outs or not s_sd:
            return None
        cvO = s_sd / season_outs
        spread = cvO * season_outs
        model = (1.0 - norm_cdf(line, mu, spread)) if side == "over" else norm_cdf(line, mu, spread)
        central = round(mu, 2)
        inputs = {"trailing8_outs": round(mO8, 2), "k_tier": outs_k(mO8),
                  "prev_start_pitches": prevNP, "home": bool(home),
                  "cvO": round(cvO, 3), "mu": central,
                  "opponent_term": "none -- measured null on outs, t=-0.34"}
    model *= 100.0

    # ---- raw, at this exact number, ALL starts.
    # T23: the 4+IP filter is provably biased on an outs UNDER at T >= 12,
    # where it deletes only winners. The unbiased all-starts rate leads.
    stat = (lambda r: r.get("k")) if market == "strikeouts" else (lambda r: r.get("outs"))
    vals = [stat(r) for r in prior if stat(r) is not None]
    h = sum(1 for v in vals if (v > line if side == "over" else v < line))
    n = len(vals)
    raw = 100.0 * h / n if n else None
    if raw is None:
        return None

    blend = 0.5 * model + 0.5 * raw

    # ---- matched class
    opp_team = game["home"] if home == 0 else game["away"]
    if market == "strikeouts":
        ah, an, fh, fn, notable = matched_class_k(players, opp_team, line, side, k9, today)
        axis = f"season K/9 within +/-1.5 of {k9:.2f}"
    else:
        bucket = outs_bucket(mean([r["outs"] for r in trail]))
        ah, an, fh, fn, notable = matched_class_outs(players, opp_team, line, side, bucket, today)
        axis = f"trailing mean outs in the {bucket} band, point-in-time (T24)"
    cls_all = 100.0 * ah / an if an else None
    cls_4 = 100.0 * fh / fn if fn else None

    # ---- head-to-head (STEP 4C), reported whenever it exists
    h2h = [r for r in prior if r.get("o") == opp_team]
    h2h_hit = sum(1 for r in h2h if stat(r) is not None
                  and (stat(r) > line if side == "over" else stat(r) < line))

    # ---- price.
    # 🔴 Hard Rock is the book Sam bets, so Hard Rock's OWN number is the
    # one quoted. "Best price across books" answers a different question.
    # When Hard Rock did not post the market in this pull, the play is
    # still printed -- rule 53 -- with the fact stated on the row, and it
    # is barred from pairs, because only Hard Rock multiplies.
    hrq = prop.get("hr") or {}
    on_hr = bool(hrq.get("price") is not None)
    if on_hr:
        price, book, link = hrq["price"], hrq.get("book", "hardrockbet"), hrq.get("link")
    else:
        price, book, link = prop.get("price"), prop.get("book"), prop.get("link")

    # ---- the shadow column. T21/T22 are NOT ADOPTED; `blend` above is
    # what enters calibration, and `carried` enters no denominator.
    flags, carried = [], blend
    if h == n and n >= 9:
        carried = 0.5 * model + 0.5 * T21_PERFECT_LONG
        flags.append({"kind": "warn", "test": "T21", "text":
                      f"{h}-for-{n} is not 100%. A perfect record over 9+ prior starts "
                      f"delivers about {T21_PERFECT_LONG}% going forward. Measured at the "
                      f"4+ K threshold; applying it here is an extrapolation."})
    elif h == n and n >= 3:
        carried = 0.5 * model + 0.5 * T21_PERFECT_SHORT
        flags.append({"kind": "warn", "test": "T21", "text":
                      f"{h}-for-{n} on a short sample is worth no more than a merely good "
                      f"record -- the measured cell is {T21_PERFECT_SHORT}%."})
    elif h == 0 and n >= 9:
        carried = 0.5 * model + 0.5 * (100 - T21_PERFECT_LONG)
    shuttled = any((not r.get("gs")) and (r.get("d") or "") < today for r in p["g"])
    if shuttled:
        nrel = sum(1 for r in p["g"] if not r.get("gs") and (r.get("d") or "") < today)
        carried -= T22_SHUTTLE_PENALTY
        flags.append({"kind": "warn", "test": "T22", "text":
                      f"{nrel} relief appearance(s) this season -- a shuttled arm reads "
                      f"{T22_SHUTTLE_PENALTY} points worse point-in-time (z=6.97)."})
    carried = max(1.0, min(99.0, carried))

    if abs(model - raw) > 10:
        flags.append({"kind": "flag", "test": "rule 15", "text":
                      f"model {model:.1f}% vs raw {raw:.1f}% -- a {abs(model-raw):.1f}-point gap. "
                      "The model is the suspect, but see the class rate."})
    # 🔴 The reference figure is the ALL-STARTS rate, not the 4+IP one.
    # The blueprint says quote both and do not pick the flattering one, and
    # T23 showed the 4+IP filter is the biased one -- it deletes short
    # outings, which are where the losers live. Both are printed either way.
    cls_ref = cls_all if an >= 8 else None
    if cls_ref is not None and abs(cls_ref - blend) >= 15:
        flags.append({"kind": "flag", "test": "STEP 4B", "text":
                      f"matched class {cls_ref:.0f}% ({ah}/{an} all starts"
                      + (f", {fh}/{fn} on 4+ innings" if fn else "")
                      + f") vs blend {blend:.1f}% -- {abs(cls_ref-blend):.0f} points apart. "
                      "Suspect. Post-hoc subgroup; the class is a flag and is never "
                      "folded into the blend."})
    if an < 8:
        flags.append({"kind": "note", "test": "STEP 4B", "text":
                      f"matched class n={an} -- UNINFORMATIVE, do not use it."})
    if not on_hr:
        flags.append({"kind": "note", "test": "STEP 5", "text":
                      f"Hard Rock did not post this market in the pull. The price shown is "
                      f"{prop.get('book')}'s, which is a number Sam cannot bet -- and the "
                      f"absence is evidence about the FEED, never about the book. Ask for "
                      f"the app price. Barred from pairs."})

    be = 100.0 * implied(price) if price is not None else None
    grp = "GOOD" if (k9 >= 9.0 and era is not None and era <= 3.50) else \
          ("BAD" if (k9 < 9.0 and era is not None and era > 3.50) else "MIXED")
    bnd, bnd_note = band_of(blend)
    # Sam's -700 floor: the shortest rung he will take. His rule, not a
    # judgment call of Claude's -- so it sorts the board rather than
    # hiding anything. Every below-floor rung is still written out in full.
    floor_ok = price is None or price > -700

    return {
        "pitcher": p["name"], "pid": prop.get("pid"), "team": p["team"], "throws": p.get("throws"),
        "market": market, "side": side, "line": line,
        "game": f"{ab(game['away'])} @ {ab(game['home'])}",
        "game_id": game["id"], "away": game["away"], "home": game["home"],
        "commence": game["commence"], "opponent": opp_team, "home_side": bool(home),
        "group": grp, "k9": round(k9, 2), "era": era, "whip": p.get("whip"),
        "book": book, "price": price, "link": link, "on_hardrock": on_hr,
        "best_elsewhere": (None if on_hr else
                           {"book": prop.get("book"), "price": prop.get("price")}),
        "ladder": prop.get("_ladder") or [],
        "alt_rung": bool(prop.get("_alt")),
        "break_even": round(be, 1) if be is not None else None,
        "edge": round(blend - be, 1) if be is not None else None,
        "model": round(model, 1), "raw_pct": round(raw, 1), "raw": f"{h}/{n}",
        "blend": round(blend, 1), "carried": round(carried, 1),
        "confidence": round(blend),
        "band": bnd, "band_note": bnd_note, "clears_price_floor": floor_ok,
        "class": {"axis": axis, "all": f"{ah}/{an}" if an else None,
                  "all_pct": round(cls_all, 1) if cls_all is not None else None,
                  "four_plus": f"{fh}/{fn}" if fn else None,
                  "four_plus_pct": round(cls_4, 1) if cls_4 is not None else None,
                  "n": an,
                  "best": [f"{x[1]} {x[2]} -- {x[0]}" for x in notable[:2]],
                  "worst": [f"{x[1]} {x[2]} -- {x[0]}" for x in notable[-1:]]},
        "h2h": (f"{len(h2h)} start(s) vs {ab(opp_team)} -- cleared {h2h_hit}/{len(h2h)}"
                if h2h else f"never faced {ab(opp_team)} this season"),
        "model_inputs": inputs, "central": central,
        "first_pitch": et(game["commence"]),
        "why": why_lines(p, market, side, line, h, n, model, raw, blend,
                         ah, an, fh, fn, axis, oppK, centerC, inputs, opp_team,
                         price, be, k9, era, grp, book),
        "flags": flags,
    }


def why_lines(p, market, side, line, h, n, model, raw, blend,
              ah, an, fh, fn, axis, oppK, centerC, inputs, opp_team,
              price, be, k9, era, grp, book):
    """The reasoning, assembled from the row's own numbers. Nothing here is
    an adjective the data did not earn."""
    w = []
    unit = "strikeouts" if market == "strikeouts" else "outs"
    verb = "cleared" if side == "over" else "stayed under"
    w.append(f"{verb.capitalize()} {line} {unit} in {h} of {n} starts this season "
             f"({raw:.0f}%). All starts, no minimum-innings filter -- that filter is "
             f"provably biased on this kind of line (T23).")
    if an >= 8:
        w.append(f"Comparable arms ({axis}) facing {ab(opp_team)} this season went "
                 f"{ah} of {an} ({100.0*ah/an:.0f}%)"
                 + (f", and {fh} of {fn} on starts that reached four innings."
                    if fn >= 8 else "."))
    else:
        w.append(f"Only {an} comparable start(s) against {ab(opp_team)} exist, so the "
                 f"matched-class check cannot speak here. That is a finding, not a blank.")
    if market == "strikeouts":
        d = 0.575 * (oppK - centerC)
        where = ("an easy lineup to strike out" if d > 0.15 else
                 "a hard lineup to strike out" if d < -0.15 else
                 "a mid-pack lineup, so this term contributes almost nothing")
        w.append(f"{ab(opp_team)} allow {oppK:.2f} K per start against a league "
                 f"{centerC:.2f} -- {where} ({d:+.2f} K on the projection). "
                 f"He is at {inputs['trailing8_K']:.1f} K over his last eight, "
                 f"{'home' if inputs['home'] else 'on the road'}, "
                 f"which lands E[K] at {inputs['E_K']}.")
    else:
        w.append(f"{inputs['trailing8_outs']:.1f} outs over his last eight and "
                 f"{inputs['prev_start_pitches']} pitches last time out -- persistence, "
                 f"not fatigue: a high previous pitch count predicts MORE outs, not fewer. "
                 f"That puts the projection at {inputs['mu']} outs "
                 f"({'home' if inputs['home'] else 'road'}). "
                 f"There is no opponent term on an outs line; it measured null.")
    w.append(f"{grp} arm by the STEP 1 split: {k9:.2f} K/9"
             + (f", {era} ERA." if era is not None else "."))
    if price is not None and be is not None:
        gap = blend - be
        w.append(f"{price:+d} at {book} breaks even at {be:.1f}%. This card has it at "
                 f"{blend:.1f}% -- {'an edge of' if gap >= 0 else 'a shortfall of'} "
                 f"{abs(gap):.1f} points."
                 + ("" if book in ("hardrockbet", "hardrockbet_oh") else
                    " That is not a book Sam bets, so the edge is not actionable as "
                    "quoted -- it is here to show where the market sits."))
    return w


# -------------------------------------------------------------- hitters
# 🔴 THERE IS NO HITTER MODEL. Ledger rule 55: a MARKET number never
# carries a Gizmo's confidence %. So a hitter row carries NO `blend`, NO
# `confidence` and NO band -- it carries the player's own record and the
# market's own de-vigged price, and says which is which.
#
# The estimate is his season rate at that exact line with a JEFFREYS
# PRIOR -- (hits + 0.5) / (games + 1). That is smoothing, not modelling:
# without it a 3-for-4 sample tops the board on noise every night. It is
# labelled DESCRIPTIVE and it is not a projection.
#
# ⛔ Do not add a confidence number here until a hitter model exists,
# has been backtested, and has beaten the raw rate on a pre-registered
# test. That is the next build, not this one.
HITTER_LABEL = {
    "batter_hits": "Hits", "batter_total_bases": "Total bases",
    "batter_home_runs": "Home runs", "batter_rbis": "RBIs",
    "batter_hits_runs_rbis": "Hits+Runs+RBIs",
}
MIN_HITTER_GAMES = 25


def parse_rate(s):
    """'38/125' -> (38, 125). Returns (None, None) on anything else."""
    try:
        h, n = str(s).split("/")
        return int(h), int(n)
    except Exception:
        return (None, None)


def hitter_play(prop, game, ids, team_games):
    ev = prop.get("evidence") or {}
    h, n = parse_rate(ev.get("season"))
    if h is None or n is None or n < MIN_HITTER_GAMES:
        return None

    # 🔴 LINEUP RISK. `n` counts games he actually BATTED. A player who has
    # batted in 41 of his team's 128 games is a bench bat, and his rate --
    # however true -- is conditional on him being in the lineup at all. If
    # he is not, the bet is usually VOID, not a win. The rate cannot see
    # that, so it is stated on the row instead of being folded into it.
    tg = team_games.get(prop.get("team")) or 0
    share = (n / tg) if tg else None
    risk = bool(share is not None and share < 0.70)

    hrq = prop.get("hr") or {}
    on_hr = hrq.get("price") is not None
    price = hrq["price"] if on_hr else prop.get("price")
    book = hrq.get("book", "hardrockbet") if on_hr else prop.get("book")
    link = hrq.get("link") if on_hr else prop.get("link")
    if price is None:
        return None

    rate = 100.0 * (h + 0.5) / (n + 1)          # Jeffreys, not a projection
    be = 100.0 * implied(price)
    mkt = prop.get("implied")                    # de-vigged, from the board

    def r(k):
        a, b = parse_rate(ev.get(k))
        return None if a is None or not b else round(100.0 * a / b, 1)

    return {
        "kind": "hitter",
        "basis": "MARKET + DESCRIPTIVE — no model, no confidence rating (rule 55)",
        "player": prop.get("player"), "pid": prop.get("pid"),
        "team": prop.get("team"), "bats": ev.get("bats"),
        "market": prop.get("market"),
        "market_label": HITTER_LABEL.get(prop.get("market"), prop.get("market")),
        "side": prop.get("side"), "line": prop.get("line"),
        "game": f"{ab(game['away'])} @ {ab(game['home'])}",
        "game_id": game["id"], "away": game["away"], "home": game["home"],
        "away_id": ids.get(game["away"]), "home_id": ids.get(game["home"]),
        "commence": game["commence"], "first_pitch": et(game["commence"]),
        "opponent": ev.get("opp"),
        "book": book, "price": price, "link": link, "on_hardrock": bool(on_hr),
        "rate": round(rate, 1), "raw": f"{h}/{n}",
        "break_even": round(be, 1),
        "market_implied": mkt,
        "edge": round(rate - be, 1),
        "edge_vs_market": None if mkt is None else round(rate - mkt, 1),
        "games_batted": n, "team_games": tg or None,
        "lineup_share": None if share is None else round(100 * share, 1),
        "lineup_risk": risk,
        "splits": {"season": ev.get("season"), "last15": ev.get("last15"),
                   "home": ev.get("home"), "road": ev.get("road"),
                   "vs_opp": ev.get("vs_opp"),
                   "last15_pct": r("last15"), "home_pct": r("home"),
                   "road_pct": r("road")},
        "why": hitter_why(prop, ev, h, n, rate, be, price, book, share, risk),
    }


def hitter_why(prop, ev, h, n, rate, be, price, book, share, risk):
    lbl = HITTER_LABEL.get(prop.get("market"), prop.get("market"))
    verb = "cleared" if prop.get("side") == "over" else "stayed under"
    w = [f"{verb.capitalize()} {prop.get('line')} {lbl.lower()} in {h} of {n} games "
         f"({100.0*h/n:.0f}%). Smoothed to {rate:.0f}% so a short hot streak cannot "
         f"top the board on noise."]
    l15h, l15n = parse_rate(ev.get("last15"))
    if l15n:
        w.append(f"Last 15 games: {l15h}/{l15n}.")
    hh, hn = parse_rate(ev.get("home"))
    rh, rn = parse_rate(ev.get("road"))
    if hn and rn:
        w.append(f"Home {hh}/{hn}, road {rh}/{rn}. ⚠️ Home/road is DESCRIPTIVE here "
                 f"— it has never been tested on hitters in this project.")
    vh, vn = parse_rate(ev.get("vs_opp"))
    if vn:
        w.append(f"Against {ev.get('opp')} this season: {vh}/{vn}."
                 + (" ⚠️ Too few to mean anything." if vn < 8 else ""))
    else:
        w.append(f"Has not faced {ev.get('opp')} this season.")
    if risk:
        w.append(f"🔴 LINEUP RISK: he has batted in only {100*share:.0f}% of his team's "
                 f"games. This rate is conditional on him being in the lineup — if he "
                 f"is not, the bet is usually VOIDED, not won. Check the lineup card.")
    elif share is not None:
        w.append(f"In the lineup for {100*share:.0f}% of his team's games.")
    w.append(f"{price:+d} at {book} breaks even at {be:.1f}%. "
             f"🔴 This row has NO model behind it — the number is his own record, "
             f"not a projection, and it carries no confidence rating.")
    return w


# --------------------------------------------------------------- pairs
FLOOR, TARGET = 1.80, 2.10


def build_pairs(plays, limit=8):
    """STEP 6. Two legs, ONE book, TWO DIFFERENT GAMES, product >= 1.80.

    🔴 The different-games test is on GAME IDENTITY, never on opponent name
    (ledger rule 54). In every game on every slate the two starters have
    DIFFERENT opponents and the SAME game, so a name comparison passes on
    precisely the pairs it exists to catch. A live card shipped four
    impossible parlays that way, including the #1 recommendation.

    Below 1.8x is never shown -- not printed, not labelled, not listed as
    declined. Sam's own instruction, and the one deliberate exception to
    ledger rule 53. Above 2.1x IS shown, marked ABOVE BAND.
    """
    out = []
    priced = [p for p in plays if p.get("price") is not None and p.get("on_hardrock")
              and p.get("clears_price_floor")]
    for i in range(len(priced)):
        for j in range(i + 1, len(priced)):
            a, b = priced[i], priced[j]
            if a["game_id"] == b["game_id"]:
                continue
            if a["pid"] == b["pid"]:
                continue
            mult = decimal(a["price"]) * decimal(b["price"])
            if mult < FLOOR:
                continue
            joint = a["blend"] / 100.0 * b["blend"] / 100.0
            be = 100.0 / mult
            out.append({
                "legs": [f"{a['pitcher']} {a['side'][0]}{a['line']} "
                         f"{'K' if a['market']=='strikeouts' else 'outs'}",
                         f"{b['pitcher']} {b['side'][0]}{b['line']} "
                         f"{'K' if b['market']=='strikeouts' else 'outs'}"],
                "games": [a["game"], b["game"]],
                "game_ids": [a["game_id"], b["game_id"]],
                "book": "hardrockbet",
                "decimals": [round(decimal(a["price"]), 3), round(decimal(b["price"]), 3)],
                "prices": [a["price"], b["price"]],
                "multiplier": round(mult, 3),
                "in_band": FLOOR <= mult <= TARGET,
                "label": "IN BAND" if FLOOR <= mult <= TARGET else "ABOVE BAND",
                "joint": round(100 * joint, 1),
                "leg_blends": [a["blend"], b["blend"]],
                "leg_models": [a["model"], b["model"]],
                "leg_raws": [a["raw"], b["raw"]],
                "break_even": round(be, 1),
                "edge": round(100 * joint - be, 1),
                "ev_30": round(30 * (joint * mult - 1), 2),
            })
    out.sort(key=lambda x: -x["joint"])
    return out[:limit]


# ---------------------------------------------------------------- main
def load(path, gz=False):
    if not os.path.exists(path):
        raise RuntimeError(f"{path} missing -- the collector has not run")
    return json.load(gzip.open(path, "rt")) if gz else json.load(open(path))


TEAM_IDS = {
    'Tampa Bay Rays': 139, 'Baltimore Orioles': 110, 'St. Louis Cardinals': 138,
    'Philadelphia Phillies': 143, 'Toronto Blue Jays': 141, 'New York Yankees': 147,
    'Washington Nationals': 120, 'Miami Marlins': 146, 'Detroit Tigers': 116,
    'Kansas City Royals': 118, 'Athletics': 133, 'Houston Astros': 117,
    'New York Mets': 121, 'Chicago White Sox': 145, 'Los Angeles Angels': 108,
    'Texas Rangers': 140, 'Cleveland Guardians': 114, 'Colorado Rockies': 115,
    'San Francisco Giants': 137, 'Boston Red Sox': 111, 'Pittsburgh Pirates': 134,
    'Los Angeles Dodgers': 119, 'Chicago Cubs': 112, 'Seattle Mariners': 136,
    'Minnesota Twins': 142, 'San Diego Padres': 135, 'Cincinnati Reds': 113,
    'Arizona Diamondbacks': 109, 'Atlanta Braves': 144, 'Milwaukee Brewers': 158,
}


def team_ids():
    """Prefer the stored schedule -- a name the league changes (Athletics)
    breaks a hardcoded map silently, and the schedule is authoritative."""
    import glob
    m = dict(TEAM_IDS)
    snaps = sorted(glob.glob("data/*/schedule/*.json.gz"))
    if snaps:
        try:
            D = json.load(gzip.open(snaps[-1], "rt"))
            for dd in (D.get("schedule") or {}).get("dates") or []:
                for g in dd.get("games", []):
                    for sidek in ("away", "home"):
                        t = ((g.get("teams") or {}).get(sidek) or {}).get("team") or {}
                        if t.get("name") and t.get("id"):
                            m[t["name"]] = t["id"]
        except Exception:
            pass
    return m


def et(iso):
    """ET clock time for an ISO-Z kickoff. MLB is entirely inside DST in
    August, so a fixed -4 is exact for this season's card."""
    try:
        return (datetime.fromisoformat(iso.replace("Z", "+00:00"))
                - timedelta(hours=4)).strftime("%-I:%M%p").lower()
    except Exception:
        return None


def et_date(iso):
    return (datetime.fromisoformat(iso.replace("Z", "+00:00"))
            - timedelta(hours=4)).strftime("%Y-%m-%d")


def et_today():
    """The slate date in ET. A 10pm PT first pitch is still tonight's card."""
    return (datetime.now(timezone.utc) - timedelta(hours=4)).strftime("%Y-%m-%d")


def main(dry=False):
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    P = load("data/latest/pitchers.json.gz", gz=True)
    B = load("data/latest/props.json.gz", gz=True)
    players = P["players"]

    means, ns, centerC, npop = opponent_table(players)
    by_pid = {int(k): v for k, v in players.items()}

    now = datetime.now(timezone.utc)
    ids = team_ids()

    # 🔴 The card is dated by the SLATE, not by the clock. At 11pm ET the
    # board already holds tomorrow's games and none of today's; dating it
    # off the wall clock would file tomorrow's card under today and the
    # page would never find it. The date is the ET date of the earliest
    # game that has NOT started.
    upcoming = [g for g in B["games"]
                if datetime.fromisoformat(g["commence"].replace("Z", "+00:00")) > now]
    if not upcoming:
        print("[card] every game on the board has started -- nothing to write")
        return None
    today = min(et_date(g["commence"]) for g in upcoming)

    # A team's games played, approximated by the most games any of its
    # hitters has batted in. Used only to size lineup risk, never to price.
    team_games = {}
    for g0 in B["games"]:
        for pr in g0["props"]:
            if pr.get("kind") != "batter":
                continue
            _h, _n = parse_rate((pr.get("evidence") or {}).get("season"))
            if _n and pr.get("team"):
                team_games[pr["team"]] = max(team_games.get(pr["team"], 0), _n)

    plays, hitters, skipped = [], [], {}
    for g in B["games"]:
        # A started game is off the board. Every tab does this; the card must too.
        try:
            if datetime.fromisoformat(g["commence"].replace("Z", "+00:00")) <= now:
                skipped["already started"] = skipped.get("already started", 0) + 1
                continue
        except Exception:
            pass
        # 🔴 STEP 5: the alt ladder is part of the board, not an extra.
        # Walking a rung is the main tool for landing a pair inside 1.8x-2.1x,
        # so every Hard Rock rung becomes a play in its own right, priced
        # through the same model. The feed carries only the OVER side of Hard
        # Rock's strikeout ladder; the book offers both, so a wanted UNDER rung
        # is NAMED with its price asked for, never invented.
        lad = g.get("ladders") or {}
        rungs = []
        for prop in g["props"]:
            if prop["market"] != "pitcher_strikeouts" or prop["side"] != "over":
                continue
            key = norm_name(prop["player"])
            mine = sorted([r for r in lad.get(key, []) if r["market"] == "strikeouts"],
                          key=lambda r: r["line"])
            for r in mine:
                if abs(r["line"] - prop["line"]) < 1e-9 and r["side"] == prop["side"]:
                    continue
                rungs.append(dict(prop, line=r["line"], side=r["side"],
                                  price=r["price"], book=r["book"],
                                  link=r.get("link"), app_label=r.get("app_label"),
                                  hr={"price": r["price"], "book": r["book"],
                                      "link": r.get("link")},
                                  _alt=True, _ladder=mine))
            prop["_ladder"] = mine

        for prop in g["props"]:
            if prop.get("kind") != "batter" or prop["market"] not in HITTER_LABEL:
                continue
            hp = hitter_play(prop, g, ids, team_games)
            if hp is None:
                skipped["hitter: too few games or no price"] = \
                    skipped.get("hitter: too few games or no price", 0) + 1
                continue
            hitters.append(hp)

        for prop in list(g["props"]) + rungs:
            if prop["market"] not in ("pitcher_strikeouts", "pitcher_outs"):
                continue
            pid = prop.get("pid")
            p = by_pid.get(pid) if pid else None
            if not p:
                skipped["no game log"] = skipped.get("no game log", 0) + 1
                continue
            opp_team = g["home"] if p["team"] == g["away"] else g["away"]
            row = build_play(prop, p, players, means.get(opp_team), centerC,
                             ns.get(opp_team, 0), g, today)
            if row is None:
                skipped["insufficient inputs"] = skipped.get("insufficient inputs", 0) + 1
                continue
            row["away_id"] = ids.get(g["away"])
            row["home_id"] = ids.get(g["home"])
            row["kind"] = "pitcher"
            plays.append(row)

    # 🔴 An alt rung is a RUNG, not a separate pick. Printing all of them as
    # top-level rows turned a 13-play card into 147 near-duplicates. Each
    # rung is priced through the same model and hung under its own pitcher,
    # which is what STEP 7's `Alt ladder:` line asks for and what a rung-walk
    # into the 1.8x band actually reads.
    for x in plays:
        if not x["alt_rung"]:
            continue
        x["ladder_row"] = {
            "line": x["line"], "side": x["side"], "price": x["price"],
            "app_label": (f"To Record {int(x['line'] + 0.5)}+"
                          if x["side"] == "over" and x["market"] == "strikeouts" else None),
            "model": x["model"], "raw": x["raw"], "blend": x["blend"],
            "carried": x["carried"], "band": x["band"],
            "break_even": x["break_even"], "edge": x["edge"],
            "clears_price_floor": x["clears_price_floor"], "link": x["link"],
        }
    standard = [x for x in plays if not x["alt_rung"]]
    for x in standard:
        rungs = sorted(
            (y["ladder_row"] for y in plays
             if y["alt_rung"] and y["pid"] == x["pid"] and y["market"] == x["market"]),
            key=lambda r: r["line"])
        x["ladder"] = rungs
        # ★ the rung this card would take: the safest one that still clears
        # Sam's -700 floor. At a flat-ish payout, climbing is a donation.
        ok = [r for r in rungs if r["clears_price_floor"] and r["side"] == x["side"]]
        x["ladder_pick"] = (min(ok, key=lambda r: -r["blend"]) if ok else None)

    # The under of a 90% over is the same number written backwards. Both
    # sides are kept -- the losing one hangs on its own row as `other_side`
    # with its price and its blend -- but only one of the pair gets a card,
    # so the board is 32 numbers rather than 64 mirror images.
    for x in standard:
        mirror = next((y for y in standard
                       if y["pid"] == x["pid"] and y["market"] == x["market"]
                       and y["line"] == x["line"] and y["side"] != x["side"]), None)
        x["other_side"] = ({"side": mirror["side"], "price": mirror["price"],
                            "model": mirror["model"], "raw": mirror["raw"],
                            "blend": mirror["blend"], "link": mirror["link"]}
                           if mirror else None)
    standard = [x for x in standard
                if x["other_side"] is None or x["blend"] >= x["other_side"]["blend"]]

    plays_all = plays
    plays = standard
    pairs = build_pairs(plays_all)

    # ---- THE BOARD -------------------------------------------------
    # 🔴 THIS IS A FILTERED BOARD, AND THE FILTER IS SAM'S, NOT CLAUDE'S.
    # Sam, 2026-08-23: "gizmos picks should only include the picks the
    # model likes, i would like to see 25-50 players everytime, including
    # hitters props as well as pitchers." Asked what "likes" means, he
    # chose BIGGEST EDGE VS THE PRICE and THE CALIBRATED BAND, together.
    # ⚠️ Ledger rule 53 says a play is never absent because CLAUDE did not
    # like it. This exclusion is Sam's own instruction, the same authority
    # as the 1.8x pair floor -- and every count that was excluded is
    # printed below so the size of what is hidden stays visible.
    for x in plays:
        x["in_band"] = (x.get("band") == "70-80")
        x["clears_price_floor"] = x.get("clears_price_floor", True)
    for x in hitters:
        x["in_band"] = False          # no model, so no calibration band

    liked = [x for x in plays + hitters
             if (x.get("edge") is not None and x["edge"] > 0)
             and x.get("clears_price_floor", True)]
    # Band-qualifying plays lead, then everything by edge.
    # Band first, then solid-lineup plays, then by edge. A lineup-risk row
    # is SHOWN with its flag — it is just not allowed to crowd out the top
    # of the board on a rate that assumes he plays.
    liked.sort(key=lambda x: (not x["in_band"], bool(x.get("lineup_risk")),
                              -(x.get("edge") or 0)))

    board = liked[:BOARD_MAX]
    if len(board) < BOARD_MIN:
        # Not enough positive-edge plays. Top up by edge, and SAY SO on the
        # row rather than quietly padding the board with plays that lose to
        # their own price.
        rest = sorted([x for x in plays + hitters if x not in liked],
                      key=lambda x: -(x.get("edge") if x.get("edge") is not None else -999))
        for x in rest[:BOARD_MIN - len(board)]:
            x["below_price"] = True
            board.append(x)

    for i, x in enumerate(board, 1):
        x["rank"] = i
    below = [x for x in plays if not x.get("clears_price_floor", True)]
    for x in below:
        x["rank"] = None

    doc = {
        "date": today,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": "gizmos-card",
        "generated_by": "card.py -- automated, unattended",
        "model_version": MODEL_VERSION,
        "odds_pulled_at": B.get("pitcher_odds_at"),
        "logs_pulled_at": P.get("pulled_at"),
        "opponent_table": {
            "rebuilt_from": "the same pitcher pull the model reads",
            "starts": npop,
            "centering_constant": round(centerC, 4),
            "note": ("meanK and its centering constant come from the SAME pull. "
                     "The published table in claude/mlb-opponent-database.md needs an "
                     "interactive browser session to rebuild and lags by a slate at a "
                     "time; this one rebuilds nightly. Measured 2026-08-23 the two "
                     "agree to a mean |dE[K]| of 0.021 K, max 0.064 K."),
        },
        "board_rule": (
            "Sam's filter, not Claude's: plays whose estimate beats the price's "
            "break-even, calibrated-band plays first, then by edge. "
            f"{len(plays)} pitcher and {len(hitters)} hitter rows were priced; "
            f"{len(board)} are shown."),
        "hitter_note": (
            "Hitter rows carry NO confidence rating and NO band. There is no hitter "
            "model in this project, and ledger rule 55 forbids a MARKET number from "
            "carrying a Gizmo's confidence %. Their number is the player's own season "
            "rate at that exact line with a Jeffreys prior — DESCRIPTIVE, not a "
            "projection. A real hitter model is the next build."),
        "coverage": (f"{len(board)} plays across {len({x['game_id'] for x in board})} games, "
                     f"ranked by blend. {len(pairs)} pairs clear the 1.8x floor. "
                     f"Generated unattended from the collector's own data -- no human "
                     f"chose which plays appear."),
        "coverage_detail": {"pitchers_with_logs": len(players), "plays": len(board),
                     "below_price_floor": len(below), "pairs": len(pairs),
                     "skipped": skipped},
        "calibration_warning": (
            "Only the 70-80% band has a record that supports its own number. "
            "60-70% runs -25.9 and 80%+ runs -18.0. Every play carries its band."),
        "selection_note": (
            "Nothing here is a recommendation to bet. Every qualifying pitcher prop on "
            "the board is printed with its failing numbers attached (ledger rule 53); "
            "which of them to bet is Sam's call. The one thing withheld is a PAIR below "
            "1.8x, which is his own instruction."),
        "shadow_note": (
            "`blend` is the carded estimate and the ONLY column that enters calibration. "
            "`carried` is the blend after the T21/T22 flags -- both PRE-REGISTERED AND "
            "NOT ADOPTED -- and enters no denominator. It is a shadow ladder kept so the "
            "September re-fit can measure whether the flagged number would have won."),
        "picks": board,
        "below_price_floor": below,
        "pairs": pairs,
        "schema_note": ("picks[] are the standard lines, ranked by blend, each carrying "
                        "its Hard Rock alt ladder in .ladder with every rung priced "
                        "through the same model. pairs[] may use any rung. Every price "
                        "is Hard Rock's own, from a us2 pull, at the minute stamped above."),
    }
    if dry:
        print(json.dumps({k: v for k, v in doc.items()
                          if k not in ("picks", "pairs", "below_price_floor")}, indent=1))
        for x in board[:16]:
            who = x.get("pitcher") or x.get("player")
            unit = ("K" if x["market"] == "strikeouts"
                    else "outs" if x["market"] == "outs"
                    else x.get("market_label", x["market"])[:12])
            if x["kind"] == "pitcher":
                extra = (f"model {x['model']:5.1f}  blend {x['blend']:5.1f}  "
                         f"carried {x['carried']:5.1f}  [{x['band']}]")
            else:
                extra = f"rate  {x['rate']:5.1f}  NO MODEL           lineup {x.get('lineup_share')}%"
            print(f"  {x['rank']:2}. {x['kind'][:3]} {who[:20]:21} "
                  f"{x['side'][0]}{x['line']:<5} {unit:12} {x['game']:11} "
                  f"{str(x['price']):>6}  raw {x['raw']:>7}  edge {x['edge']:+6.1f}  {extra}")
        print(f"\n  {len(pairs)} pairs")
        for p in pairs[:6]:
            print(f"   {p['multiplier']:.2f}x {p['label']:10} joint {p['joint']:5.1f}%  "
                  f"EV${p['ev_30']:>7}  {p['legs'][0]} + {p['legs'][1]}")
        return doc
    os.makedirs("picks", exist_ok=True)
    with open(f"picks/{today}.json", "w") as f:
        json.dump(doc, f, separators=(",", ":"))
    print(f"[card] wrote picks/{today}.json -- {len(plays)} plays, {len(pairs)} pairs")
    return doc


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
