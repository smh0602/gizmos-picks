#!/usr/bin/env python3
"""shadow_fb.py — THE SHADOW RECORD. Grade the BOARD, publish the CARD.

    LEAGUE=nfl python shadow_fb.py [YYYY-MM-DD ...]

══════════════════════════════════════════════════════════════════════
🔴🔴 THE SEASON DOES NOT CONTAIN ENOUGH ROWS, AND THE RATE IS A DISPLAY
CAP RATHER THAN A DATA LIMIT.

Break-even at -110 is 52.38%. Showing a 3-point edge at p < 0.01 needs
about 2,774 graded rows. `[measured on main, 2026-09-17]`

    graded football rows today      222     (NFL 125 / 5 days, CFB 97 / 4)
    required                      2,774
    at the card's rate         ~111/week   ->  25 weeks

College ends in early December and the NFL regular season in early
January, so that test would finish in the 2027 season.

✅ BUT WE ALREADY BUY THE WHOLE BOARD. `[measured on one NFL day,
data/nfl/2026-09-13/props-player/]`

    raw priced outcomes                      21,413
    distinct (game, market, player, line)     2,081
    ...with a side, i.e. distinct wagers       3,731
    `card_fb.TOP_N`                              20

The credits are spent. Grading the rest reads a stored snapshot and
joins it to box scores the collector already fetches free. ⛔ Zero
additional Odds credits, zero CFBD calls, no new pull, no new cron.

🔴 AND THE PAGE DOES NOT CHANGE. Sam, 2026-08-26: "we have to advertise
a clean look to the website that doesnt include nonsense users dont need
to read and cant understand." This repo already has the pattern —
`carried` is a shadow column, and the T21/T22/rule-15 diagnostics are
computed, stored and never displayed. Same move: the record grades what
the board priced; the card still publishes its top 20.

⛔ THE GRADER IS `record_fb.grade_card`, NOT A SECOND ONE. The shadow
rows and the published rows are graded by the SAME CODE, so they cannot
disagree about what a win is (rule 117). This file only decides WHICH
wagers to hand it.
══════════════════════════════════════════════════════════════════════
"""
import ast
import collections
import datetime
import glob
import gzip
import json
import math
import os
import sys

import card_fb
import daystore
import record_fb

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUE = os.environ.get("LEAGUE", "nfl")
DATA = os.path.join(ROOT, "data", LEAGUE)

# 🔴 T60's BAR, AS `claude/owed-tests.md` FIXES IT: rate >= 55.4%,
#    one-sided p < 0.01, fresh archived rows only.
T60_RATE = 0.554
T60_P = 0.01

# ⚠️ BREAK-EVEN AT -110, WHICH IS THE NULL THE p-VALUE IS TAKEN AGAINST.
# 110/210 = 0.523809..., the figure the brief itself frames the whole
# problem around.
# 📌 AND IT IS MY READING, NOT A QUOTE. The bar Sam quotes fixes the rate
# and the alpha; it does not name the null, and "beats the price" is the
# only null a betting edge can sensibly be tested against. ⛔ If
# `claude/owed-tests.md` names a different one, this is the line to
# change and the stored documents carry `p_basis` so every past row says
# which null it was scored under.
BREAK_EVEN = 110.0 / 210.0

# 🔴🔴 THE FOURTH TERM, SUPPLIED BY SAM ON 2026-09-18 AND NOT DERIVED
# HERE. `claude/owed-tests.md` holds the bar and this repository does not
# contain that file; the figure was ASKED FOR rather than inferred, and
# it arrived with its own derivation:
#
#     one-sided, α = 0.01, power 0.80, p0 = 0.5238, p1 = 0.554  ->  2774
#
# ⛔ AND IT IS A MINIMUM ON THE **EFFECTIVE** n, NOT THE RAW ROW COUNT.
# The power calculation assumes independent observations, which is
# exactly the quantity `cluster()` estimates — so comparing it against
# the raw count would be comparing a number to a different number that
# happens to share a name.
# ⚠️ `test_shadow_fb.py` FAILS IF THIS BECOMES ANYTHING ELSE, including
# `None`. Changing it is a decision about a pre-registered test, not a
# code tidy-up, and a bar edited after seeing data is not pre-registered.
T60_MIN_EFF_N = 2774

# ⚠️ THE MARKETS ARE `card_fb.MARKETS`, NOT A LIST HERE. Those are the
#    ones `record_fb._val` can actually read a result for; a market this
#    file "supported" that the grader cannot score would produce rows
#    that are permanently ungradable (rule 66: one list).
MARKETS = card_fb.MARKETS

# ⛔ A ROW IS ONLY EVIDENCE IF WE COULD HAVE BET IT. The price used is
#    from the NEWEST SNAPSHOT STRICTLY BEFORE KICKOFF. A snapshot pulled
#    after the game started carries live in-play prices, and grading
#    those would be the wrong-game bug wearing a clock.
#    ⚠️ Stated as a rule rather than a tolerance: `pulled_at < commence`.


def log(m):
    print("[%s] %s" % (datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"), m))


def books():
    """Sam's five books, AST-PARSED OUT OF `collect.py`, never retyped.

    ⛔ Parsed rather than imported, exactly as `dossier_fb.team_codes`
    does it: importing the collector runs its module-level league
    handling, and a reporting tool must not be able to trip that."""
    src = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
    for n in ast.parse(src).body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "BOOKS":
            return set(ast.literal_eval(n.value))
    return set()


def snapshots(day, data=None):
    return sorted(glob.glob(os.path.join(data or DATA, day,
                                         "props-player", "*.json.gz")))


def priceable(day, data=None, log=log):
    """{board_id: (pulled_at, event)} — the newest PRE-KICKOFF snapshot.

    ⛔ THE KEY IS THE ODDS FEED'S OWN EVENT ID, which is the same
    namespace as `board.json`'s `id` and therefore as the dossier's
    `board_id` (measured: they intersect exactly on the games both
    files hold). ⛔ Never a team name — CLAUDE.md: two legs are in
    different games only if the GAME ID differs, and a live MLB card
    shipped four impossible parlays off a name check. ⛔ Never a kickoff
    time — that is `boardFor()`'s nearest-first-pitch problem."""
    out = {}
    for f in snapshots(day, data):
        try:
            d = json.load(gzip.open(f, "rt"))
        except Exception as e:
            log("  skipping %s: %s: %s" % (f, type(e).__name__, e))
            continue
        pulled = d.get("pulled_at") or ""
        for ev in d.get("events") or []:
            com, gid = ev.get("commence_time") or "", ev.get("id")
            if not (com and gid) or pulled >= com:
                continue
            cur = out.get(gid)
            if cur is None or pulled > cur[0]:
                out[gid] = (pulled, ev)
    return out


def wagers(day, data=None, bk=None, log=log):
    """Every distinct wager the board priced that day, one row each.

    A wager is (game, market, player, line, SIDE) — the side matters
    because Over 60.5 and Under 60.5 are opposite bets, and CLAUDE.md is
    explicit that two prices are only comparable at the exact signed
    number."""
    bk = books() if bk is None else bk
    out = []
    for gid, (pulled, ev) in priceable(day, data, log).items():
        rungs = {}
        for b in ev.get("bookmakers") or []:
            if b.get("key") not in bk:
                continue        # ⛔ Sam's five, the same filter as every pull
            for mk in b.get("markets") or []:
                m = mk.get("key")
                if m not in MARKETS:
                    continue
                for o in mk.get("outcomes") or []:
                    who = o.get("description")
                    side = (o.get("name") or "").lower()
                    px = o.get("price")
                    if not who or px is None:
                        continue
                    r = rungs.setdefault((who, m, o.get("point"), side),
                                         {"n_books": 0, "price": None,
                                          "book": None})
                    r["n_books"] += 1
                    # ⚠️ BEST = LEAST NEGATIVE / MOST POSITIVE. American
                    #    odds do not order numerically for a bettor.
                    if r["price"] is None or px > r["price"]:
                        r["price"], r["book"] = px, b.get("key")
        for (who, m, pt, side), r in sorted(rungs.items(),
                                            key=lambda kv: (kv[0][1], kv[0][0],
                                                            kv[0][2] or 0,
                                                            kv[0][3])):
            out.append({
                "player": who, "market": m,
                "market_label": card_fb.LABEL.get(m), "side": side,
                "line": pt, "price": r["price"], "book": r["book"],
                "n_books_for_this_side": r["n_books"],
                "board_id": gid,
                "game": "%s at %s" % (ev.get("away_team"), ev.get("home_team")),
                "commence": ev.get("commence_time"),
                "priced_at": pulled,
            })
    return out


# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 CLUSTER BY GAME, OR THE ANSWER IS FALSE.
# ⛔ 2,081 rows are NOT 2,081 independent observations. The same player
# appears across six markets; the same game across dozens of players.
# Correlated rows inflate significance, so a p-value on the raw n reports
# an edge that is not there — and it reports it convincingly.
#
# ✅ THE ESTIMATOR IS THE STANDARD RATIO-ESTIMATOR CLUSTER-ROBUST
# VARIANCE, one cluster per GAME:
#
#     Var(p) = G/((G-1) * N^2) * SUM_g (w_g - p * m_g)^2
#     eff_n  = p(1-p) / Var(p)
#
# ⚠️ IT ASSUMES NO ICC AND FITS NOTHING. That is deliberate: a
# design-effect form would need an intra-cluster correlation estimated
# from the same data, which is a model, and a model needs a
# pre-registered test.
# ⛔ eff_n IS CAPPED AT THE RAW n and floored at the cluster count. One
# game cannot carry more information than one game, and it cannot carry
# less than one observation.
# ══════════════════════════════════════════════════════════════════════
def pair_key(r):
    """The wager a row is one SIDE of. ⛔ Over 60.5 and Under 60.5 on one
    player in one game are ONE coin flip read twice."""
    return (r.get("board_id"), r.get("market"), r.get("player"),
            r.get("line"))


def pair_bound(rows):
    """The MOST independent observations these rows can carry.

    ══════════════════════════════════════════════════════════════════
    🔴🔴 THE BRIEF GUARDED ONE DIRECTION AND THE DATA PRODUCED THE
    OTHER. `[2026-09-17, and recorded this way on Sam's instruction]`
    The task specified a guard against correlated rows INFLATING n. What
    the board actually does is the reverse.

    ➡️ THE CLASS, WHICH IS WORTH MORE THAN THE FIX: **A DESIGN EFFECT CAN
    BE LESS THAN ONE, AND THEN THE CLUSTER CORRECTION ADDS CONFIDENCE
    INSTEAD OF REMOVING IT.** A variance-based effective n therefore
    needs a COMBINATORIAL CEILING, because the number of independent
    observations cannot exceed the number of distinct outcomes the market
    resolves — and a complementary pair resolves once. Taking the minimum
    of the two, and naming which bound applied, is the construction.
    ⛔ The brief was wrong and the running was right.

    🔴 FOUND BY DRIVING IT, NOT BY READING IT. The cluster estimator
    below reported `deff 1.0` on 1,331 real graded rows across 16 games —
    i.e. "1,331 independent observations" — and it was RIGHT about its
    own estimand and USELESS as a headline.
    ⛔ The reason is that the board prices BOTH SIDES: measured on those
    rows, 509 keys carried both an Over and an Under (1,018 rows) beside
    313 one-sided anytime-TD rows. Within a game, every Over that wins
    is an Under that loses, so the per-game rate is pinned — the 16
    games ran 0.408 to 0.474 — the between-game variance nearly
    vanishes, and a variance-based effective n comes back at the raw
    count. THE OPPOSITE FAILURE FROM THE ONE T60 GUARDS AGAINST, and it
    would have let a p-value be computed on what is effectively raw n.
    ✅ SO THERE IS A SECOND, COMBINATORIAL BOUND, and it fits nothing: a
    complementary pair collapses to ONE observation. 1,331 rows -> at
    most 822. ⛔ It is arithmetic, not a model, and `eff_n` is the SMALLER
    of the two.
    ══════════════════════════════════════════════════════════════════
    """
    pk = collections.Counter(pair_key(r) for r in rows
                             if (r.get("side") or "") in ("over", "under"))
    doubled = sum(v for v in pk.values() if v >= 2)
    pairs = sum(1 for v in pk.values() if v >= 2)
    return {"bound": len(rows) - doubled + pairs,
            "pairs": pairs, "rows_in_a_pair": doubled,
            "one_sided_rows": len(rows) - doubled}


def cluster(rows, key="board_id"):
    """Raw n, cluster count, and the effective n a p-value may use.

    ══════════════════════════════════════════════════════════════════
    🔴🔴 UNGRADED ROWS LEAVE HERE, AND THE FILTER IS IN THIS FUNCTION
    RATHER THAN IN ITS CALLERS. `[2026-09-18]`
    ⛔ `this_reading` divided 541 wins by 1,374 WAGERS and reported
    39.37%, while `pooled_all_rows` divided the same wins by the 1,245
    GRADED rows and reported 43.45% — two blocks of one document
    disagreeing by 4.1 points about the same rows, because one counted
    every ungraded wager as a LOSS.
    ⛔ AND 14 OF THEM WERE VOIDS. CLAUDE.md, on `verify_record.py`:
    "Voids stay out of every denominator." The MLB grader enforces that;
    this file broke the same rule in a new place.
    ⚠️ A "no log for this player" row is not a loss either. It is a row
    we could not grade, and telling those apart is the entire reason
    `state` exists rather than a bare boolean.
    ✅ SO ONE CALLER CANNOT GET IT RIGHT WHILE ANOTHER GETS IT WRONG —
    the denominator is decided once, here, and what was dropped is
    REPORTED rather than silently vanishing.
    ══════════════════════════════════════════════════════════════════
    """
    dropped = collections.Counter(str(r.get("state") or "not graded")
                                  for r in rows if r.get("won") is None)
    rows = [r for r in rows if r.get("won") is not None]
    g = collections.defaultdict(lambda: [0, 0])      # cluster -> [wins, m]
    for r in rows:
        c = g[r.get(key)]
        c[0] += 1 if r.get("won") else 0
        c[1] += 1
    n = sum(m for _w, m in g.values())
    w = sum(wv for wv, _m in g.values())
    G = len(g)
    pb = pair_bound(rows)
    rep = {"n": n, "wins": w, "games": G,
           # ⚠️ NAMED, NOT SILENT. "n went down" with no reason beside it
           #    is how a denominator change gets mistaken for a data loss.
           "ungraded_excluded": sum(dropped.values()),
           "ungraded_by_state": dict(dropped.most_common()),
           "rate": (w / n) if n else None,
           "rows_per_game": round(n / G, 2) if G else None,
           "pair_bound": pb["bound"], "complementary_pairs": pb["pairs"],
           "rows_in_a_pair": pb["rows_in_a_pair"],
           "one_sided_rows": pb["one_sided_rows"]}
    if not n:
        return {**rep, "eff_n": 0, "eff_wins": 0, "deff": None,
                "eff_n_from_variance": None, "eff_basis": "no rows"}
    p = w / n
    if G < 2:
        # ⚠️ ONE CLUSTER: the variance is not estimable and the honest
        #    information content is one observation. ⛔ Reporting n here
        #    is the exact overstatement this function exists to refuse.
        return {**rep, "eff_n": G, "eff_wins": int(round(p * G)),
                "deff": (n / G) if G else None,
                "eff_n_from_variance": None,
                "eff_basis": "one game — variance not estimable, so the "
                             "effective n is the cluster count"}
    ss = sum((wv - p * m) ** 2 for wv, m in g.values())
    var = (G / ((G - 1) * float(n) ** 2)) * ss
    if var <= 0 or p in (0.0, 1.0):
        # ⚠️ EVERY CLUSTER AT THE SAME RATE, or a degenerate 0%/100%.
        #    The between-cluster variance carries no information, so the
        #    cluster count is what is left.
        return {**rep, "eff_n": G, "eff_wins": int(round(p * G)),
                "deff": n / float(G),
                "eff_n_from_variance": None,
                "eff_basis": "no between-game variance — the effective n "
                             "is the cluster count"}
    var_eff = p * (1 - p) / var
    # ⛔ THE SMALLER OF THE TWO BOUNDS, ALWAYS, and the basis says which
    #    one bound. Reporting only the variance estimate is what put
    #    "1,331 independent observations" on a set carrying at most 822.
    eff = min(var_eff, float(n), float(pb["bound"]))
    eff = max(eff, float(G))
    if eff >= float(n):
        basis = ("cluster-robust ratio-estimator variance over %d game(s) "
                 "— neither bound binds" % G)
    elif eff == float(G):
        basis = "floored at the %d game(s) the rows come from" % G
    elif abs(eff - float(pb["bound"])) < 1e-9:
        basis = ("capped by the complementary-pair bound: %d pair(s) "
                 "collapse to one observation each, so %d row(s) carry at "
                 "most %d" % (pb["pairs"], n, pb["bound"]))
    else:
        basis = ("cluster-robust ratio-estimator variance over %d game(s)"
                 % G)
    return {**rep, "eff_n": round(eff, 2), "eff_wins": int(round(p * eff)),
            "eff_n_from_variance": round(var_eff, 2),
            "deff": round(n / eff, 3), "eff_basis": basis}


def one_sided_p(wins, n, p0):
    """P(X >= wins | n, p0) under the binomial, summed IN LOG SPACE.

    ⛔ NOT A NORMAL APPROXIMATION. At the n this file starts with, the
    tail is where the whole question lives and the approximation is worst
    exactly there.
    ⚠️ AND NOT `math.comb` EITHER: `comb(1000, 500)` is a ~300-digit
    integer and multiplying it by a float raises OverflowError, which is
    how the first draft of this died. `lgamma` keeps every term finite
    for any n this will ever see."""
    if not n or wins is None:
        return None
    n = int(n)
    if n <= 0:
        return None
    wins = max(0, min(int(wins), n))
    if p0 <= 0 or p0 >= 1:
        return None
    lp, lq = math.log(p0), math.log(1 - p0)
    ln = math.lgamma(n + 1)
    tot = 0.0
    for k in range(wins, n + 1):
        tot += math.exp(ln - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                        + k * lp + (n - k) * lq)
    # ⚠️ CLAMPED. Floating-point summation of a full tail can land a
    #    hair above 1.0, and a probability above 1 in a stored document
    #    is the kind of number that gets quoted.
    return min(1.0, max(0.0, tot))


def t60(rows, min_eff_n=None):
    """T60's accounting. ⛔ THE p-VALUE IS COMPUTED ON THE CLUSTERED n.

    A p-value on the raw n is not a refinement of this — it is a
    different and wrong number, and it is a pre-registration condition
    of T60 that it never appears."""
    c = cluster(rows)
    floor = T60_MIN_EFF_N if min_eff_n is None else min_eff_n
    out = {**c, "bar_rate": T60_RATE, "bar_p": T60_P,
           "min_eff_n": floor,
           "p_value": one_sided_p(c["eff_wins"], c["eff_n"], BREAK_EVEN),
           "p_basis": ("one-sided exact binomial against break-even "
                       "(%.2f%% at -110), on the CLUSTERED effective n"
                       % (100 * BREAK_EVEN)),
           # ⛔ NAMED SO NOTHING CAN QUIETLY GROW ONE. A raw-n p-value is
           #    the defect; the field says it is absent on purpose.
           "p_value_on_raw_n": None,
           "p_value_on_raw_n_note": (
               "⛔ NEVER COMPUTED. The same player appears across six "
               "markets and the same game across dozens of players, so a "
               "p-value on the raw row count reports an edge that is not "
               "there. This is a pre-registration condition of T60, not "
               "a refinement.")}
    if floor is None:
        out["verdict"] = "AWAITING_PRE_REGISTERED_N"
        out["why"] = ("The bar's minimum n lives in `claude/owed-tests.md`, "
                      "which this repository does not contain. It is not "
                      "guessed here, so nothing can pass yet.")
        return out
    if c["eff_n"] < floor:
        out["verdict"] = "NOT YET MEASURABLE"
        out["why"] = ("%s effective row(s) against a pre-registered "
                      "minimum of %s. Not a pass and not a fail."
                      % (c["eff_n"], floor))
        return out
    ok = (c["rate"] is not None and c["rate"] >= T60_RATE
          and out["p_value"] is not None and out["p_value"] < T60_P)
    out["verdict"] = "PASS" if ok else "FAIL"
    out["why"] = ("%.1f%% over %s effective row(s), one-sided p=%s against "
                  "the %.1f%% bar."
                  % (100 * c["rate"], c["eff_n"],
                     ("%.4g" % out["p_value"]) if out["p_value"] is not None
                     else "n/a", 100 * T60_RATE))
    return out


# ══════════════════════════════════════════════════════════════════════
# 🔴 WHICH DAYS ARE GRADED, AND WHY EACH IS GRADED EXACTLY ONCE.
# ⛔ `card-fb` fires on EIGHT cron arms a day. Re-writing the same day's
# rows on every arm would put eight copies of ~1,000 rows into the
# archive daily — 44 MiB a season against the 5.17 MiB the dated design
# budgets, and eight counts of every row for anything that pools them.
# ✅ SO A DAY IS WRITTEN WHEN ITS GRADING IS FINAL: the player log must
# already cover through that day. Before that the day is PENDING and a
# later arm picks it up; after it, the verdicts cannot change, so one
# reading is the complete one.
# ⚠️ AND A DAY ALREADY IN THE ARCHIVE IS NEVER REWRITTEN. The check reads
# the archive rather than trusting the clock.
# ══════════════════════════════════════════════════════════════════════
LOOKBACK_DAYS = 8       # a week plus one, so a missed arm still catches up


def shadow_files(data=None):
    return sorted(glob.glob(os.path.join(data or DATA, "*", "shadow",
                                         "*.json.gz")))


def already_written(data=None, log=log):
    """{source day} -> the days some earlier reading already graded."""
    done = set()
    for f in shadow_files(data):
        try:
            d = json.load(gzip.open(f, "rt"))
        except Exception as e:
            log("  unreadable shadow file %s: %s" % (f, type(e).__name__))
            continue
        done |= set(d.get("days") or [])
    return done


def sections_for(day, data=None):
    """{board_id: {section name: state}} from THAT DAY's dossier archive.

    ⛔ THE DATED ARCHIVE, NEVER `latest/`. `latest/` is overwritten on
    every arm, so by the time a game is final it describes a different
    slate — reading it would attach today's sections to last week's
    result, which is the same class of error as the wrong-game bug.
    ⚠️ THE NEWEST ARCHIVE OF THAT DAY, because it is the reading closest
    to kickoff and therefore the one a bettor would have seen."""
    fs = sorted(glob.glob(os.path.join(data or DATA, day, "dossiers",
                                       "*.json.gz")))
    if not fs:
        # ⚠️ AND IT SAYS WHICH ABSENCE THIS IS. `[2026-09-18]` A row with
        #    `sections: null` reads identically whether the JOIN MISSED
        #    or the dossier DID NOT EXIST, and those are opposite facts:
        #    the first is a defect, the second is the calendar. The
        #    dossier archive only begins the day the panel shipped, so
        #    every board graded before it has nothing to join to — which
        #    is correct and self-resolving, and unreadable if unsaid.
        #    ⛔ Same reason `state` exists on a graded row rather than a
        #    bare boolean.
        have = sorted({os.path.basename(os.path.dirname(os.path.dirname(x)))
                       for x in glob.glob(os.path.join(data or DATA, "*",
                                                       "dossiers",
                                                       "*.json.gz"))})
        return {}, None, (
            "no dossier archive for %s — %s. This is the calendar, not a "
            "failed join."
            % (day, ("the archive begins %s, so boards graded before it "
                     "have nothing to join to" % have[0]) if have else
               "nothing has been archived yet, so there is nothing to "
               "join to at all"))
    f = fs[-1]
    try:
        doc = json.load(gzip.open(f, "rt"))
    except Exception:
        return {}, None, ("%s's dossier archive could not be read"
                          % day)
    out = {}
    for x in doc.get("dossiers") or []:
        if x.get("board_id"):
            out[x["board_id"]] = {s.get("name"): s.get("state")
                                  for s in (x.get("sections") or [])}
    return out, os.path.basename(f), None


def possession_validated(root=None):
    """(ok, {league: bool}) — is the possession signal live in BOTH?

    🔴 T60 VOIDS ROWS GRADED BEFORE BOTH LEAGUES' POSSESSION VALIDATION
    PASSES: a signal that was wrong when the row was written is not
    evidence about the signal. ⛔ So this is a GATE on eligibility, not a
    filter on what gets stored — the rows are kept either way, because
    throwing a row away is the irreversible move and marking it is not.
    ⚠️ AND IT IS MEASURED FROM DISK, not assumed: `possession.py` refuses
    to write a partial table, so the EXISTENCE of `top-<season>.json.gz`
    is the validation having passed."""
    root = root or ROOT
    per = {}
    for lg in ("nfl", "ncaaf"):
        hit = glob.glob(os.path.join(root, "data", lg, "latest",
                                     "top-[0-9][0-9][0-9][0-9].json.gz"))
        per[lg] = bool(hit)
    return (all(per.values()), per)


def grade_day(day, data=None, bk=None, log=log):
    """(rows, note) for one day. ⛔ `record_fb.grade_card` does the grading.

    ⚠️ THE JOIN BACK IS POSITIONAL AND IT IS ASSERTED. `grade_card`
    appends exactly one row per pick, in order, and drops the fields it
    does not know about — `board_id` among them. Zipping is the cheapest
    way to put them back, and a length mismatch means that contract
    changed, so it REFUSES rather than mis-attributing a result to
    another game."""
    w = wagers(day, data, bk, log)
    if not w:
        return [], "no pre-kickoff snapshot"
    season = int(day[:4])
    doc, P = record_fb.load_log(season)
    if not P:
        return [], "no %d player log stored yet" % season
    idx = card_fb.index_by_name(P)
    covers = max((g.get("d") or "" for pl in P.values()
                  for g in (pl.get("g") or [])), default="")
    if covers < day:
        return [], ("the player log only covers through %s"
                    % (covers or "nothing"))
    graded = record_fb.grade_card({"picks": w, "logs_season": season},
                                  P, idx, covers)
    if len(graded) != len(w):
        raise AssertionError(
            "record_fb.grade_card returned %d rows for %d wagers — the "
            "one-row-per-pick contract this join relies on has changed"
            % (len(graded), len(w)))
    sec, sec_from, no_arch = sections_for(day, data)
    rows = []
    for src, g in zip(w, graded):
        got = sec.get(src["board_id"])
        rows.append({**g, "day": day, "board_id": src["board_id"],
                     "priced_at": src["priced_at"],
                     "n_books_for_this_side": src["n_books_for_this_side"],
                     "sections": got,
                     "sections_from": sec_from,
                     # ⛔ `None` WHEN THERE IS NOTHING TO EXPLAIN. A
                     #    reason on a row that HAS its sections is noise.
                     "sections_absent": None if got else (
                         no_arch or ("this game is not in %s's dossier — "
                                     "the archive exists and does not "
                                     "describe it, which IS a gap worth "
                                     "looking at" % day))})
    return rows, None


def accumulate(data=None, log=log):
    """Every stored shadow row, deduped. ⛔ The pooled question is T60's.

    ⚠️ DEDUPED ON THE WAGER PLUS ITS SOURCE DAY, and the FIRST reading
    wins. A day is meant to be written once, but a dedupe that trusts
    that is a dedupe that stops working the day something writes twice."""
    seen, rows = set(), []
    for f in shadow_files(data):
        try:
            d = json.load(gzip.open(f, "rt"))
        except Exception:
            continue
        for r in d.get("rows") or []:
            k = (r.get("day"), r.get("board_id"), r.get("market"),
                 r.get("player"), r.get("line"), r.get("side"))
            if k in seen:
                continue
            seen.add(k)
            rows.append(r)
    return rows


def eligible(rows, ok_possession):
    """T60's fresh rows: graded, described, and after the gate."""
    if not ok_possession:
        return []
    return [r for r in rows if r.get("won") is not None and r.get("sections")]


def build(league=None, data=None, root=None, log=log, when=None):
    """-> 0 on a clean write or a clean nothing-to-do, 1 on a refusal."""
    lg = (league or LEAGUE or "nfl").strip().lower()
    if lg == "mlb":
        # ⛔ MLB IS FROZEN AND THIS FILE HAS NO PATH INTO IT. The absence
        #    is the guard, and the caller is unconditional so a new
        #    football league starts working the day it has data.
        log("shadow_fb: mlb is not built here — the freeze, not a gap.")
        return 1
    data = data or os.path.join(root or ROOT, "data", lg)
    today = (when or datetime.datetime.now(datetime.timezone.utc)).date()
    done = already_written(data, log)
    bk = books()
    rows, per_day, pending = [], [], []
    for back in range(LOOKBACK_DAYS, 0, -1):
        day = (today - datetime.timedelta(days=back)).strftime("%Y-%m-%d")
        if day in done:
            continue
        if not snapshots(day, data):
            continue
        try:
            got, why = grade_day(day, data, bk, log)
        except AssertionError as e:
            log("shadow_fb: ⛔ REFUSING — %s" % e)
            return 1
        if why:
            pending.append({"day": day, "why": why})
            continue
        g = [r for r in got if r.get("won") is not None]
        _why = sorted({r["sections_absent"] for r in got
                       if r.get("sections_absent")})
        per_day.append({"day": day, "wagers": len(got), "graded": len(g),
                        "wins": sum(1 for r in g if r["won"]),
                        "games": len({r.get("board_id") for r in got}),
                        "described": len([r for r in got if r.get("sections")]),
                        # ⚠️ ONCE BOARDS FROM THE ARCHIVE'S FIRST DAY ARE
                        #    GRADED, `described` SHOULD START CLIMBING. If
                        #    it does not, that is a real defect and this
                        #    field is how anyone would notice.
                        "not_described_why": _why})
        rows += got
    ok_poss, poss = possession_validated(root)
    pooled = accumulate(data, log) + rows
    elig = eligible(pooled, ok_poss)
    doc = {
        "kind": "SHADOW_RECORD",
        "league": lg,
        "built_at": datetime.datetime.now(datetime.timezone.utc)
                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": ("⛔ NOT PUBLISHED AND NOT PUBLISHABLE. This grades every "
                 "wager the board priced, so the sample can answer a "
                 "question in weeks that the card's top %d answers in "
                 "seasons. The page shows the card; this is a report on "
                 "it, the same way `carried` is a shadow column."
                 % card_fb.TOP_N),
        "days": [d["day"] for d in per_day],
        "pending": pending,
        "per_day": per_day,
        "n_rows": len(rows),
        "possession_validated": poss,
        "t60_gate": (
            "rows count toward T60 only once possession validation has "
            "passed in BOTH leagues AND the row carries the dossier "
            "sections it was described by. ⛔ Rows are kept either way — "
            "discarding one is irreversible, marking it is not."),
        # ⚠️ BOTH BLOCKS NOW SHARE ONE DENOMINATOR BY CONSTRUCTION:
        #    `cluster()` drops ungraded rows itself, so a caller cannot
        #    hand one block wagers and the other graded rows. They
        #    disagreed by 4.1 points before that moved.
        "this_reading": t60(rows),
        "pooled_all_rows": t60([r for r in pooled
                                if r.get("won") is not None]),
        "t60": {**t60(elig), "n_eligible": len(elig),
                "n_pooled_graded": len([r for r in pooled
                                        if r.get("won") is not None])},
        "rows": rows,
    }
    if not rows and not pending:
        log("shadow_fb[%s]: no newly gradable day in the last %d — nothing "
            "to write, and that is not a failure."
            % (lg, LOOKBACK_DAYS))
        return 0
    if not rows:
        log("shadow_fb[%s]: nothing final yet — %s"
            % (lg, "; ".join("%s: %s" % (p["day"], p["why"])
                             for p in pending)))
        return 0
    p, wrote = daystore.archive(doc, data, "shadow", log=log, when=when)
    log("shadow_fb[%s]: %d wager(s) over %d day(s) -> %s%s"
        % (lg, len(rows), len(per_day), p, "" if wrote else " (left as it was)"))
    for d in per_day:
        log("   %s: %d graded of %d wager(s) across %d game(s), %d described"
            % (d["day"], d["graded"], d["wagers"], d["games"], d["described"]))
    _t = doc["t60"]
    log("   T60: %s — %s (%d eligible of %d pooled graded row(s))"
        % (_t["verdict"], _t["why"], _t["n_eligible"], _t["n_pooled_graded"]))
    if not ok_poss:
        log("   ⚠️ possession validation has NOT passed in %s, so every row "
            "so far is VOID for T60 — stored, counted, and not eligible."
            % ", ".join(k for k, v in poss.items() if not v))
    return 0


if __name__ == "__main__":
    sys.exit(build())
