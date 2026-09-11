#!/usr/bin/env python3
"""
🔴 THE GUARD FAILED A HEALTHY BUILD FOR THE SECOND TIME, ONE WEEK LATER.

`[2026-09-11, the live cfb-probe run]`

    RuntimeError: ahead_out_lastwk is CONSTANT 0 across 1,870 rows
    spanning 2 week(s) [1, 2] — a join failure, not a result

**It was not a join failure.** ⛔ Rule 175 said a column constant by
ARITHMETIC is not a broken join, and the 09-10 fix set the bar at **two
distinct weeks** for all three point-in-time columns. **One of the three
needs THREE.**

## THE ARITHMETIC, AND IT IS A PROOF RATHER THAN AN ARGUMENT

`ahead_out_lastwk` counts players **ahead of you** who **did not play
last week**. To be *ahead* you must have a trailing usage, which requires
having played a **strictly earlier** week. In week 2 the only earlier
week is week 1 — **so anyone ahead of you necessarily PLAYED week 1, and
therefore cannot have been out last week.**

⛔ **The two sets are mutually exclusive. The column is zero by
construction until week 3**, and no amount of real data changes that.

## ⚠️ WHY THE NFL IS NOT CHANGED, THOUGH THE STANDING RULE SAYS MIRROR IT

*"Everything we do for CFB we do for NFL"* — and here that would be
**wrong**, because the two columns are not the same measurement:

    NFL      out_set is an INJURY REPORT keyed (player, week):
             "OUT/DOUBTFUL **this** week". A player can be OUT in week 2
             AND have played week 1, so the two conditions are
             INDEPENDENT and the column can vary from week 2.

    COLLEGE  CFBD publishes NO injury report and NO snap data, so absence
             is inferred from "did not play last week" — which is what
             creates the mutual exclusion above.

✅ **The college column is a documented RE-SPECIFICATION of the NFL's**
(`cfb.py`: *"its original mechanism — zero snaps last week — DOES NOT
EXIST, because college publishes no snap data at all"*). **Same name,
different question, different floor.**

⛔ **AND THE FIX IS NARROWER THAN A BLANKET BUMP TO THREE.** Raising the
floor for all three would stop judging `depth_rank` and `trailing_usage`
for an extra week — and those two are where a genuinely broken join shows
up FIRST. The floor is now a property of the column.
"""
import os
import sys

from tcheck import ck, eq, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import cfb  # noqa: E402


def roster(weeks_a, weeks_b):
    """Two players, one team/position. B out-touches A, then misses a week."""
    mk = lambda w, u: {"team": "T", "pos": "RB", "week": w, "wk_i": w,
                       "usage": u}
    return {"A": {"pos": "RB", "g": [mk(w, 5) for w in weeks_a]},
            "B": {"pos": "RB", "g": [mk(w, 50) for w in weeks_b]}}


def ao(weeks_a, weeks_b):
    P = cfb.rank_and_cascade(roster(weeks_a, weeks_b))
    return {g["ahead_out_lastwk"] for p in P.values() for g in p["g"]}


print("\n═══ 1. 🔴 THE COLUMN CANNOT VARY BEFORE WEEK 3 ═══")
ck("🔴 TWO weeks, and the player ahead MISSED week 2 -> still all zero",
   ao([1, 2], [1]) == {0},
   "⛔ THIS IS THE LIVE FAILURE. To be 'ahead' you must have played a "
   "STRICTLY EARLIER week; in week 2 that is week 1; so anyone ahead of "
   "you played week 1 and cannot have been out last week. Mutually "
   "exclusive — zero by construction, not by a broken join")
ck("✅ THREE weeks, ahead player missed the MIDDLE one -> it reaches 1",
   1 in ao([1, 2, 3], [1, 3]),
   "week 3 is the first row that can see a week-2 absence behind a "
   "week-1 appearance")
ck("⚠️ ...and missing the LAST week is still zero",
   ao([1, 2, 3], [1, 2]) == {0},
   "his absence has not been 'last week' for any row yet — there is no "
   "week 4. The column is lagged, and the lag is the point")

print("\n═══ 2. ⛔ THE OTHER TWO COLUMNS ARE NOT RELAXED ═══")
P = cfb.rank_and_cascade(roster([1, 2], [1, 2]))
for col in ("depth_rank", "trailing_usage"):
    vals = {g[col] for p in P.values() for g in p["g"]}
    ck("✅ %s DOES vary on a two-week log" % col,
       len(vals) > 1,
       "⛔ so its floor of 2 was right and stays 2 — these are the "
       "columns a genuinely broken join shows up in FIRST, and a "
       "blanket bump to 3 would stop judging them for an extra week. "
       "Values: %s" % vals)
eq(cfb.__dict__.get("TRAILING") is None, True,
   "⚠️ the floors live inside verify(), not as a module constant")

print("\n═══ 3. 🔴 DRIVEN THROUGH THE REAL verify() ═══")


def doc(weeks, n=1870):
    per = max(1, n // len(weeks))
    P = {i: {"pos": "RB", "g": [
        {"week": w, "wk_i": w, "seasonType": "regular", "team": "T",
         "usage": 0.05 * (i % 7 + 1), "depth_rank": (i % 3) + 1,
         "trailing_usage": 0.1 * w + i % 5, "ahead_out_lastwk": 0,
         "opp_elo": 1500, "oppClass": "fbs"} for w in weeks]}
        for i in range(per)}
    return {"players": P, "scope_conferences": None, "unfiltered": True}


def findings(d):
    try:
        return [b for b in (cfb.verify(d, log=lambda m: None) or [])]
    except Exception as e:
        return ["RAISED %s: %s" % (type(e).__name__, e)]


_two = [b for b in findings(doc([1, 2])) if "ahead_out_lastwk" in b]
ck("🔴 the LIVE SHAPE — 2 weeks, constant zero — no longer fails",
   not _two,
   "⛔ this is the exact run that went red: 'ahead_out_lastwk is "
   "CONSTANT 0 across 1,870 rows spanning 2 week(s) [1, 2]'. Findings: %s"
   % [b[:60] for b in _two])
_three = [b for b in findings(doc([1, 2, 3])) if "ahead_out_lastwk" in b]
ck("⛔ ...but a genuinely constant column over THREE weeks STILL fails",
   _three,
   "🔴 THE GUARD IS NARROWED, NOT REMOVED. By week 3 the column CAN "
   "vary, so a flat zero is evidence again")
# ⛔ THE FIXTURE ABOVE VARIES depth_rank BY PLAYER, so the guard has
#    nothing to catch and the first form of this check FAILED on correct
#    code. A constant column is what the guard is for, so build one.
def const_doc(weeks, n=1870):
    per = max(1, n // len(weeks))
    P = {i: {"pos": "RB", "g": [
        {"week": w, "wk_i": w, "seasonType": "regular", "team": "T",
         "usage": 0.05 * (i % 7 + 1), "depth_rank": 1,
         "trailing_usage": 0.1 * w + i % 5, "ahead_out_lastwk": 0,
         "opp_elo": 1500, "oppClass": "fbs"} for w in weeks]}
        for i in range(per)}
    return {"players": P, "scope_conferences": None, "unfiltered": True}


_dr = [b for b in findings(const_doc([1, 2])) if "depth_rank" in b]
ck("✅ ...and a CONSTANT depth_rank is still judged at two weeks",
   _dr,
   "⛔ this is the column a genuinely broken join breaks first, and its "
   "floor stays at 2 — the fix is per-column, not a blanket bump: %s"
   % [b[:56] for b in _dr])
_dr1 = [b for b in findings(const_doc([1])) if "depth_rank" in b]
ck("⛔ ...but NOT at one week, which is rule 175's original finding",
   not _dr1,
   "on a one-week log nothing has an earlier week to trail from, so "
   "constant is correct for all three columns")

print("\n═══ 4. ⚠️ THE NFL IS DELIBERATELY NOT CHANGED ═══")
nfl_src = open("nfl.py", encoding="utf-8").read()
ck("🔴 the NFL's ahead_out reads an INJURY REPORT, not last week's absence",
   'if (q, str(g["week"])) not in out_set:' in nfl_src,
   "⛔ keyed on (player, THIS week) — so a player can be OUT in week 2 "
   "AND have played week 1. The two conditions are INDEPENDENT there, "
   "so the NFL column can vary from week 2 and its floor of 2 is right")
ck("✅ ...and that report is a real injury file, not inferred",
   'FILES["injuries"]' in nfl_src and "out_set.add(key)" in nfl_src,
   "college has no such file — CFBD publishes neither injuries nor "
   "snaps — which is the whole reason the two columns differ")
note("⚠️ 'EVERYTHING WE DO FOR CFB WE DO FOR NFL' IS SAM'S STANDING RULE "
     "AND IT DOES NOT APPLY HERE. ⛔ The college column is a documented "
     "RE-SPECIFICATION of the NFL's, not a copy: same name, different "
     "question, different floor. Mirroring this change into nfl.py would "
     "stop judging a column that is genuinely capable of varying.")
note("➡️ THE RULE THIS LEAVES BEHIND: a point-in-time column is judged "
     "only once the log holds enough weeks for it to be CAPABLE of "
     "varying, and that number is a property of the COLUMN, not of the "
     "check. ⛔ Do not raise a shared floor to silence one column.")
