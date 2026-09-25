#!/usr/bin/env python3
"""game_lines_fb.py — the football Game Lines tab (Sam, 2026-09-24).

    LEAGUE=nfl python game_lines_fb.py

For the current slate (the card's single-day rule), every game's main
spread, total and moneyline at Hard Rock, FanDuel and DraftKings, then every
alternate spread and total rung those three books post — no cap, no
pre-filter — each with its price at each book, the best price, the
break-even, the game model's probability and the edge.

  data/<lg>/latest/game-lines.json.gz        the tab
  data/<lg>/<day>/game-lines/<HHMM>.json.gz  FROZEN copies (daystore, write-once)
  data/<lg>/<day>/game-lines-grades/…        grades, stored once, never redone
  data/<lg>/latest/game-lines-record.json    the alt-rung track record

⛔ RULE 55. Prices, best prices, break-evens and lines are MARKET; the
model's %, its edge and its fair lines are MODEL; counts and records are
DESCRIPTIVE. The `bases` map in the file names the basis of every field.
⛔ THE LABEL COMES FROM THE PRE-REGISTERED CHECK (`fb_alt_lines.py`,
`research/fb_alt_lines_spec.md`): a rung that fails it is still SHOWN, with
the warning. Nothing is hidden for being unflattering.
⛔ No price is invented: every number traces to a stored alt-line or
gamelines pull. A price is compared only at the exact signed number.
⚠️ STDLIB ONLY. Rides the free `card-fb` run and the paid `alt-lines` run.
"""
import datetime
import glob
import gzip
import hashlib
import json
import math
import os
import statistics
import sys

import calibration                   # band_flags — the ONE per-band rule
import card_fb                       # build_parlays_fb, slate_date, et_date, PRICE_FLOOR
import collect                       # league_books — football's three books
import daystore                      # the ONE dated, write-once writer
import dossier_fb as D               # team_codes, _near — the board-to-schedule join
import fb_alt_lines as A             # label(), WARNING — the pre-registered check
import fb_model as F                 # predict, features, decimal, record

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUE = os.environ.get("LEAGUE", "nfl")
ALT_DAYS = 3
BASES = {
    "pt": "MARKET", "prices": "MARKET", "best": "MARKET", "be": "MARKET",
    "p": "MODEL", "edge": "MODEL", "dist": "DESCRIPTIVE",
    "main": "MARKET", "fair_spread": "MODEL", "fair_total": "MODEL",
}
JOINT_NOTE = (
    "The game model's probabilities for each leg, multiplied together — MODEL, "
    "and every leg carries the model's label. Legs are in different games, so "
    "they are treated as independent; that assumption is not free and has never "
    "been tested here.")


def log(m):
    print(m, flush=True)


def _gz(path):
    try:
        return json.load(gzip.open(path, "rt", encoding="utf-8"))
    except (OSError, ValueError, EOFError):
        return None


def _json(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _data(lg, root=None):
    return os.path.join(root or ROOT, "data", lg)


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def books_named(lg):
    """{book key: name}. ⛔ Hard Rock's Ohio skin is the same book, used only
    when the main one is absent, and never counted twice."""
    return dict(collect.league_books(lg))


def _book_blocks(bookmakers, names):
    """[(name, block)] with one block per book NAME, the main key first."""
    by = {}
    for b in sorted(bookmakers or [], key=lambda b: b.get("key", "").endswith("_oh")):
        n = names.get(b.get("key"))
        if n and n not in by:
            by[n] = b
    return sorted(by.items())


# ══════════════════════════════════════════════════════════════════════
# INPUTS
# ══════════════════════════════════════════════════════════════════════
def latest_gamelines(lg, root=None):
    for p in reversed(sorted(glob.glob(os.path.join(_data(lg, root), "20*", "gamelines", "*.json.gz")))):
        d = _gz(p)
        if d and d.get("games"):
            return d
    return None


def alt_events(lg, root=None, now=None, days=ALT_DAYS):
    """{event id: (pulled_at, event)} — the NEWEST alt pull of each game."""
    now = now or _now()
    out = {}
    for back in range(days, -1, -1):
        day = (now - datetime.timedelta(days=back)).strftime("%Y-%m-%d")
        for p in sorted(glob.glob(os.path.join(_data(lg, root), day, "alt-lines", "*.json.gz"))):
            d = _gz(p) or {}
            for ev in d.get("events") or []:
                if ev.get("id") and (ev["id"] not in out or d.get("pulled_at", "") > out[ev["id"]][0]):
                    out[ev["id"]] = (d.get("pulled_at"), ev)
    return out


def ladders(ev, names, home, away):
    """{"spread": {(side, pt): {book: price}}, "total": {...}} from one alt
    pull. ⛔ Keyed on the EXACT signed point and the side it belongs to."""
    out = {"spread": {}, "total": {}}
    for name, b in _book_blocks(ev.get("bookmakers"), names):
        for mk in b.get("markets") or []:
            key = mk.get("key")
            for o in mk.get("outcomes") or []:
                pt, px = o.get("point"), o.get("price")
                if pt is None or px is None:
                    continue
                if key == "alternate_spreads":
                    side = "home" if o.get("name") == home else "away" if o.get("name") == away else None
                    m = "spread"
                elif key == "alternate_totals":
                    side = {"Over": "over", "Under": "under"}.get(o.get("name"))
                    m = "total"
                else:
                    continue
                if side:
                    out[m].setdefault((side, float(pt)), {})[name] = px
    return out


def main_lines(g, names):
    """Per book: the main spread, total and moneyline from the gamelines pull."""
    out = {}
    home, away = g.get("home"), g.get("away")
    blocks = [dict(v, key=k) for k, v in (g.get("books") or {}).items()]
    for name, b in _book_blocks(blocks, names):
        sp, to, ml = b.get("spreads") or {}, b.get("totals") or {}, b.get("h2h") or {}
        row = {}
        if home in sp and away in sp:
            row["spread"] = {"home": [sp[home].get("pt"), sp[home].get("px")],
                             "away": [sp[away].get("pt"), sp[away].get("px")]}
        if "Over" in to and "Under" in to:
            row["total"] = {"over": [to["Over"].get("pt"), to["Over"].get("px")],
                            "under": [to["Under"].get("pt"), to["Under"].get("px")]}
        if home in ml and away in ml:
            row["moneyline"] = {"home": ml[home], "away": ml[away]}
        if row:
            out[name] = row
    return out


def main_values(mains):
    """(home line M, total T): the median main line across the three books."""
    Ms = [-float(v["spread"]["home"][0]) for v in mains.values()
          if v.get("spread") and v["spread"]["home"][0] is not None]
    Ts = [float(v["total"]["over"][0]) for v in mains.values()
          if v.get("total") and v["total"]["over"][0] is not None]
    return (statistics.median(Ms) if Ms else None, statistics.median(Ts) if Ts else None)


def match_row(pricing, g, resolve):
    """The model's row for one board game, or None. ⛔ By the board's own
    names and kickoff first; then by resolved codes within a day."""
    for r in pricing:
        if r.get("names") == [g.get("home"), g.get("away")] and r.get("commence") == g.get("commence"):
            return r
    h, a = resolve(g.get("home")), resolve(g.get("away"))
    try:
        kick = datetime.datetime.strptime(g.get("commence", "")[:10], "%Y-%m-%d")
    except ValueError:
        return None
    hits = [r for r in pricing if h and a and r.get("home") == h and r.get("away") == a
            and D._near(r.get("day"), kick)]
    return hits[0] if len(hits) == 1 else None


# ══════════════════════════════════════════════════════════════════════
# THE MODEL'S PRICE — the live fit, at any line
# ══════════════════════════════════════════════════════════════════════
def model_p(models, row, market, side, pt):
    """P(this side wins) at this exact line. ⛔ The live model, never a copy."""
    m = (models or {}).get(market)
    if not m or row is None:
        return None
    if market == "spread":
        if side == "home":
            return F.predict(m, F.features(row, "spread", M=-pt))
        return 1.0 - F.predict(m, F.features(row, "spread", M=pt))
    p = F.predict(m, F.features(row, "total", T=pt))
    return p if side == "over" else 1.0 - p


def fair_line(models, row, market, main):
    """(line, why) — where the model's probability is 50%. The model is
    linear in the line on the logit scale, so two points fix it.
    ⛔ If its probability does not FALL as the line rises it has no fair
    line, and it says so rather than printing one."""
    m = (models or {}).get(market)
    if not m or row is None or main is None:
        return None, "no model or no main line"
    kw = (lambda x: {"M": x}) if market == "spread" else (lambda x: {"T": x})
    p0 = F.predict(m, F.features(row, market, **kw(main)))
    p1 = F.predict(m, F.features(row, market, **kw(main + 1.0)))
    lg0, lg1 = math.log(p0 / (1 - p0)), math.log(p1 / (1 - p1))
    slope = lg1 - lg0
    if slope >= -1e-6:
        return None, "the model's probability does not fall as the line rises"
    return round(main - lg0 / slope, 1), None


# ══════════════════════════════════════════════════════════════════════
# THE TAB
# ══════════════════════════════════════════════════════════════════════
def rungs_for(lad, market, main, models, row, check):
    out = []
    for (side, pt), prices in sorted(lad.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        best_book = max(prices, key=lambda b: F.decimal(prices[b]))
        best = prices[best_book]
        be = 1.0 / F.decimal(best)
        p = model_p(models, row, market, side, pt)
        line = (-pt if side == "home" else pt) if market == "spread" else pt
        dist = abs(line - main) if main is not None else None
        cal, warn = A.label(check, market, p, dist)
        out.append({"m": market, "side": side, "pt": pt, "prices": prices, "best": best,
                    "book": best_book, "be": round(100 * be, 1),
                    "p": round(100 * p, 1) if p is not None else None,
                    "edge": round(100 * (p * F.decimal(best) - 1.0), 1) if p is not None else None,
                    "dist": round(dist, 1) if dist is not None else None,
                    "cal": cal, "warn": warn,
                    "floor": best >= card_fb.PRICE_FLOOR})
    return out


def build_doc(lg, root=None, now=None):
    now = now or _now()
    names = books_named(lg)
    snap = latest_gamelines(lg, root) or {}
    latest = os.path.join(_data(lg, root), "latest")
    fm = _json(os.path.join(latest, "fb-model.json")) or {}
    pricing = (fm.get("pricing") or {})
    models, prow = pricing.get("models") or {}, pricing.get("games") or []
    check = _json(os.path.join(latest, "alt-lines-check.json"))
    alts = alt_events(lg, root, now)
    resolve = D.team_codes(lg)
    cut = _iso(now - datetime.timedelta(hours=12))
    upcoming = [g for g in snap.get("games") or [] if (g.get("commence") or "") >= cut]
    # ⚠️ The slate is the day of the next game NOT YET KICKED OFF (the card's
    #    `slate_date` on those games); that day's started games stay listed.
    ahead = [g for g in upcoming if (g.get("commence") or "") > _iso(now)]
    slate = card_fb.slate_date({"games": ahead or upcoming}) if upcoming else None
    games = []
    for g in upcoming:
        if card_fb.et_date(g.get("commence")) != slate:
            continue
        mains = main_lines(g, names)
        M, T = main_values(mains)
        row = match_row(prow, g, resolve)
        pulled, ev = alts.get(g.get("id"), (None, {}))
        lad = ladders(ev or {}, names, g.get("home"), g.get("away"))
        fs, fs_why = fair_line(models, row, "spread", M)
        ft, ft_why = fair_line(models, row, "total", T)
        s_cal, s_warn = A.label(check, "spread", None, 0.0)
        t_cal, t_warn = A.label(check, "total", None, 0.0)
        games.append({
            "id": g.get("id"), "sched_id": (row or {}).get("id"), "commence": g.get("commence"),
            "home": g.get("home"), "away": g.get("away"), "main": mains,
            "main_spread_home": (-M if M is not None else None), "main_total": T,
            # ⛔ the fair SPREAD is shown as the home team's number, like a book's
            "fair_spread": (-fs if fs is not None else None), "fair_spread_why": fs_why,
            "fair_total": ft, "fair_total_why": ft_why,
            "fair_spread_warn": s_warn, "fair_total_warn": t_warn,
            "modelled": row is not None,
            "alt_pulled_at": pulled,
            "spread": rungs_for(lad["spread"], "spread", M, models, row, check),
            "total": rungs_for(lad["total"], "total", T, models, row, check),
        })
    games.sort(key=lambda x: (x["commence"] or "", x["home"] or ""))
    doc = {"league": lg, "kind": "MARKET + MODEL", "built_at": _iso(now), "slate_date": slate,
           "single_day": True, "books": sorted(set(names.values())), "bases": BASES,
           "gamelines_pulled_at": snap.get("pulled_at"),
           "check": {mk: {k: ((check or {}).get("markets") or {}).get(mk, {}).get(k)
                          for k in ("state", "n", "games", "mean_d", "p")}
                     for mk in A.MARKETS},
           "warning": A.WARNING, "spec": "research/fb_alt_lines_spec.md",
           "n_rungs": sum(len(x["spread"]) + len(x["total"]) for x in games),
           "games": games,
           "note": ("Every rung the three books post, none capped or filtered. "
                    "Prices and break-evens are the books' (MARKET); the model's % "
                    "and edge are the game model's (MODEL), labelled by the "
                    "pre-registered alt-lines check.")}
    doc["parlays"], doc["parlay_meta"] = parlays(doc, now)
    return doc


# ══════════════════════════════════════════════════════════════════════
# PARLAYS — the card's builder, the card's rules, alt rungs only
# ══════════════════════════════════════════════════════════════════════
def _leg_text(r):
    return r["text"]


def parlay_legs(doc, now=None):
    """One leg per rung side per book, games not yet kicked off. ⛔ The
    builder applies Sam's rules: -700 floor, one book per slip, different
    game ids, 1.8x / 3x floors, no ceiling, ranked by joint chance."""
    now_s = _iso(now or _now())
    legs = []
    for g in doc["games"]:
        if (g.get("commence") or "") <= now_s:
            continue
        for r in g["spread"] + g["total"]:
            if r["p"] is None:
                continue
            who = (g["home"] if r["side"] == "home" else g["away"]) if r["m"] == "spread" \
                else r["side"].title()
            pt = ("%+g" % r["pt"]) if r["m"] == "spread" else ("%g" % r["pt"])
            text = "%s %s (%s @ %s)" % (who, pt, g["away"], g["home"])
            for book, px in r["prices"].items():
                legs.append({"confidence": r["p"], "price": px,
                             "clears_price_floor": px >= card_fb.PRICE_FLOOR,
                             "game_id": g["id"], "book": book,
                             "player": "%s|%s" % (g["id"], r["m"]),
                             "game": "%s @ %s" % (g["away"], g["home"]),
                             "side": r["side"], "line": r["pt"], "market": r["m"],
                             "text": text, "cal": r["cal"]})
    return legs


def parlays(doc, now=None):
    legs = parlay_legs(doc, now)
    if not legs:
        return {}, {"rated_legs": 0, "note": "no priced alt rung on this slate yet"}
    out, meta = card_fb.build_parlays_fb(legs, leg_text=_leg_text, joint_basis="MODEL",
                                         joint_note=JOINT_NOTE)
    cal = {l["text"]: l["cal"] for l in legs}
    for size in out.values():
        for p in size:
            p["warning"] = None if all(cal.get(t) for t in p["legs"]) else A.WARNING
    return out, meta


# ══════════════════════════════════════════════════════════════════════
# FREEZE — what the tab showed, stored when built, never edited
# ══════════════════════════════════════════════════════════════════════
def frozen_view(doc, now=None):
    """The rungs of games not yet kicked off, with prices, model % and time."""
    now_s = _iso(now or _now())
    games = [{"id": g["id"], "sched_id": g["sched_id"], "commence": g["commence"],
              "home": g["home"], "away": g["away"],
              "rungs": [{k: r[k] for k in ("m", "side", "pt", "prices", "best", "book", "be",
                                           "p", "edge", "cal")} for r in g["spread"] + g["total"]]}
             for g in doc["games"] if (g.get("commence") or "") > now_s and (g["spread"] or g["total"])]
    body = json.dumps(games, sort_keys=True)
    return games, hashlib.sha256(body.encode("utf-8")).hexdigest()


def freeze(doc, lg, root=None, now=None, log=log):
    """Archive what is shown via daystore, when it differs from the newest
    frozen copy. -> path written, or None."""
    now = now or _now()
    games, fp = frozen_view(doc, now)
    if not games:
        return None
    newest = None
    for p in sorted(glob.glob(os.path.join(_data(lg, root), "20*", "game-lines", "*.json.gz"))):
        newest = p
    if newest and (_gz(newest) or {}).get("fingerprint") == fp:
        return None
    path, wrote = daystore.archive({"league": lg, "taken_at": _iso(now), "fingerprint": fp,
                                    "games": games, "bases": BASES}, _data(lg, root),
                                   "game-lines", log=log, when=now)
    return path if wrote else None


# ══════════════════════════════════════════════════════════════════════
# THE RECORD — last frozen copy before kickoff, graded once from the final
# ══════════════════════════════════════════════════════════════════════
def frozen_rungs(lg, root=None):
    """spec of the record: for each game, the rungs of the LAST frozen copy
    taken before its kickoff."""
    chosen = {}
    for p in sorted(glob.glob(os.path.join(_data(lg, root), "20*", "game-lines", "*.json.gz"))):
        d = _gz(p) or {}
        for g in d.get("games") or []:
            if d.get("taken_at", "") < (g.get("commence") or ""):
                chosen[g["id"]] = (d["taken_at"], g)
    out = []
    for gid, (taken, g) in chosen.items():
        for r in g["rungs"]:
            out.append(dict(r, game_id=gid, sched_id=g.get("sched_id"), taken_at=taken,
                            commence=g["commence"], key="%s|%s|%s|%s" % (gid, r["m"], r["side"], r["pt"])))
    return out


def grade_rung(market, side, pt, hs, as_):
    """True / False / None (push)."""
    margin = float(hs) - float(as_)
    if market == "spread":
        v = (margin + pt) if side == "home" else (-margin + pt)
    else:
        tot = float(hs) + float(as_)
        v = (tot - pt) if side == "over" else (pt - tot)
    return None if v == 0 else v > 0


def schedule_by_id(lg, root=None):
    out = {}
    for s in F.SEASONS:
        for g in (_gz(os.path.join(_data(lg, root), "latest", "schedule-%d.json.gz" % s)) or {}).get("games") or []:
            out[str(g.get("id"))] = g
    return out


def stored_grades(lg, root=None):
    out = {}
    for p in sorted(glob.glob(os.path.join(_data(lg, root), "20*", "game-lines-grades", "*.json.gz"))):
        for g in (_gz(p) or {}).get("grades") or []:
            out.setdefault(g["key"], g)          # ⛔ the FIRST stored grade stands
    return out


def grade_new(lg, rungs, stored, root=None, now=None, log=log):
    sched = schedule_by_id(lg, root)
    new = []
    for r in rungs:
        if r["key"] in stored:
            continue
        g = sched.get(str(r.get("sched_id")))
        if not g or not g.get("final") or g.get("home_score") is None or g.get("away_score") is None:
            continue
        won = grade_rung(r["m"], r["side"], r["pt"], g["home_score"], g["away_score"])
        new.append({"key": r["key"], "state": "void" if won is None else "graded", "won": won,
                    "graded_at": _iso(now or _now())})
    if new:
        daystore.archive({"league": lg, "grades": new}, _data(lg, root), "game-lines-grades",
                         log=log, when=now)
    return new


def record_doc(lg, rungs, grades):
    out = {"league": lg, "kind": "DESCRIPTIVE", "spec": "research/fb_alt_lines_spec.md",
           "note": ("Every alt rung the Game Lines tab showed, frozen before kickoff and graded "
                    "once from the final score. Kept apart from every other record. Rates use "
                    "the effective n clustered by game."),
           "markets": {}}
    for mk in A.MARKETS:
        rs = [r for r in rungs if r["m"] == mk and r.get("p") is not None]
        graded = [dict(r, won=grades[r["key"]]["won"]) for r in rs
                  if r["key"] in grades and grades[r["key"]]["state"] == "graded"]
        voids = sum(1 for r in rs if r["key"] in grades and grades[r["key"]]["state"] == "void")
        plays = [{"won": r["won"], "break_even": r["be"] / 100.0, "game_id": r["game_id"],
                  "assumed": False} for r in graded if (r.get("edge") or 0) > 0]
        acc = {}
        for r in graded:
            b = acc.setdefault(A.band_of(r["p"] / 100.0), [0, 0, 0.0])
            b[0] += 1
            b[1] += 1 if r["won"] else 0
            b[2] += r["p"]
        cal = [{"bucket": k, "n": n, "w": w, "stated": s / n} for k, (n, w, s) in sorted(acc.items())]
        out["markets"][mk] = {
            "shown": len(rs), "graded": len(graded), "voids": voids,
            "pending": len(rs) - len(graded) - voids,
            "games": len({r["game_id"] for r in graded}),
            "positive_edge": F.record(plays),
            "bands": calibration.band_flags(cal),
        }
    return out


def build(lg=None, root=None, now=None, log=log):
    lg = (lg or LEAGUE).lower()
    now = now or _now()
    doc = build_doc(lg, root, now)
    latest = os.path.join(_data(lg, root), "latest")
    path = os.path.join(latest, "game-lines.json.gz")
    tmp = path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        json.dump(doc, fh)
    os.replace(tmp, path)
    frz = freeze(doc, lg, root, now, log)
    rungs = frozen_rungs(lg, root)
    stored = stored_grades(lg, root)
    new = grade_new(lg, rungs, stored, root, now, log)
    for g in new:
        stored.setdefault(g["key"], g)
    rec = record_doc(lg, rungs, stored)
    rec["built_at"] = _iso(now)
    with open(os.path.join(latest, "game-lines-record.json"), "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
    log("game lines %s: %d game(s) on %s, %d rung(s), %d parlay(s); frozen %s; "
        "%d rung(s) graded now, %d graded in all" % (
            lg, len(doc["games"]), doc["slate_date"], doc["n_rungs"],
            sum(len(v) for v in doc["parlays"].values()), frz or "unchanged", len(new),
            sum(m["graded"] for m in rec["markets"].values())))
    return doc


if __name__ == "__main__":
    build()
    sys.exit(0)
