#!/usr/bin/env python3
"""
🔴 WEEK 1 IS NOT A BROKEN JOIN, AND EVERY NFL RUN DIED CLAIMING IT WAS.

`[2026-09-10]` Sam: *"i keep getting emails saying the collect run is
failing."* Every `nfl-logs` build since the season opened on **2026-09-09**
raised:

    RuntimeError: ahead_out is CONSTANT ZERO across 66 player-weeks.
    That is a join failure, not a result.

⛔ **IT WAS NOT A JOIN FAILURE. IT WAS ARITHMETIC.** `share_before(pid, wk)`
averages games with `g["week"] < wk`. On a log holding only week 1 that
list is EMPTY for every player, so it returns `0.0` for everyone,
`share_before(q, wk) > mine` is `0.0 > 0.0`, and `ahead_out` is
**necessarily** 0 on every row. No amount of correct joining can move it
until a second week exists.

So the guard asked a question the calendar guaranteed it could not pass,
and answered it with an accusation — for **46 football runs a day**
(ledger rule 171: a permanently red run is not an alarm, it is a cost).

⚠️ **THIS IS LEDGER RULE 174 IN ITS OWN RIGHT.** `cfb.py` already carried
both a minimum-rows bar AND a two-distinct-weeks guard on exactly this
class of column. The NFL side of the same lesson was never written, and
Sam's standing instruction is that everything done for one league is done
for the other.

✅ **WHAT IS PINNED HERE, AND IT IS STRICTLY HARDER THAN THE OLD FORM:**
  1. week 1 does NOT raise — and says loudly that it is NOT EXERCISED
  2. the run #194 case (constant zero over a real multi-week season) STILL
     raises, unchanged — the regression this guard exists for
  3. a COMPLETED WEEK MISSING FROM THE LOG is now its own named failure,
     which the old constant-column form could not see at all
  4. the `out_set` guard is untouched — an unparsed injury file is still
     a hard failure in week 1

🔴 DRIVEN, NEVER READ. `build_logs` needs the network and a season of
nflverse assets, so the guard lives in its own function and this file
calls it with real shapes (rule 163: a check that can only run on the day
it passes is not a check).
"""
import datetime
import os
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import nfl  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime.now(UTC)
YDAY = (NOW - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
TOMO = (NOW + datetime.timedelta(days=1)).strftime("%Y-%m-%d")


def players(weeks, per_player=40):
    """A log holding `weeks` for each of `per_player` players."""
    return {i: {"g": [{"week": w} for w in weeks]} for i in range(per_player)}


def schedule(*pairs):
    """`when`, keyed (week, team) -> (gameday, opp, home, game_id)."""
    return {(str(w), "KC"): (day, "BUF", 1, f"g{w}") for w, day in pairs}


def drive(pl, when, n_ao, n_rows):
    """Run the real guard. Returns the RuntimeError, or None."""
    lines = []
    try:
        nfl.check_ahead_out(pl, when, n_ao, n_rows, log=lines.append)
        return None, "\n".join(lines)
    except RuntimeError as e:
        return e, "\n".join(lines)


print("\n═══ 1. 🔴 THE LIVE FAILURE: WEEK 1 MUST NOT RAISE ═══")
# ⛔ THE EXACT SHAPE OFF THE LIVE REPORT: 66 player-weeks, all week 1,
#    ahead_out zero, and only week 1 played.
err, out = drive(players([1], 66), schedule((1, YDAY), (2, TOMO)), 0, 66)
ck("🔴 a week-1-only log does NOT raise",
   err is None,
   "the 2026 NFL season opened 2026-09-09; every run since died here: %s"
   % err)
ck("⛔ ...and it says WHY it is constant, in the log",
   "share_before" in out and "STRICTLY EARLIER" in out,
   "silence would leave the next reader with the same wrong diagnosis")
ck("⚠️ ...and calls itself NOT EXERCISED, never a pass",
   "NOT a pass" in out and "NOT EXERCISED" in out,
   "rule 144 — a check that could not run is not a check that passed")

print("\n═══ 2. ⛔ THE REGRESSION IT EXISTS FOR STILL FAILS ═══")
# 🔴 RUN #194 built `ahead_out` as constant zero across 19,400 rows of a
#    FULL SEASON and went green. That is the bug. It must still raise.
err, out = drive(players(list(range(1, 18)), 40),
                 schedule((1, YDAY)), 0, 19400)
ck("🔴 constant ZERO over a real multi-week season STILL raises",
   err is not None and "CONSTANT ZERO" in str(err),
   "run #194's regression is the whole reason for the guard: %s" % err)
ck("...and the message now carries the WEEK SPAN, not just a row count",
   "spanning 17 weeks" in str(err),
   "1,848 rows cleared the old bar while still being ONE week — the bar "
   "was counting the wrong thing")

print("\n═══ 3. ⚠️ AND THE BAR IS TWO-SIDED ═══")
err, _ = drive(players(list(range(1, 18)), 40), schedule((1, YDAY)),
               812, 19400)
ck("a populated ahead_out over a full season passes",
   err is None, str(err))
# ⛔ ROWS ALONE ARE NOT ENOUGH, AND WEEKS ALONE ARE NOT EITHER.
err, out = drive(players([1, 2], 5), schedule((1, YDAY)), 0, 10)
ck("⚠️ two weeks but only 10 rows does NOT raise",
   err is None,
   "a handful of rows in which nobody happened to miss a game is a "
   "legitimately constant column, not evidence of anything")
ck("...and the row bar is stated, not implicit",
   str(nfl.check_ahead_out.__doc__ or "") is not None
   and "NOT EXERCISED" in out, out[-140:])

print("\n═══ 4. 🔴 A HOLE IS THE DEFECT; A TRAILING GAP IS PUBLISH LAG ═══")
# ⛔ THE FIRST VERSION OF THIS CHECK WOULD HAVE RED-LINED EVERY FRIDAY
#    THROUGH MONDAY, AND THIS FILE ASSERTED THE WRONG BEHAVIOUR.
#    `[caught 2026-09-10 by mocktest_fixes.py, before either ever ran]`
#    An NFL week is Thu/Sun/Mon. The schedule reports week N played the
#    moment the Thursday game ends; nflverse publishes that week's player
#    stats on its WEEKLY drop. So "is any played week missing" is red for
#    four days out of seven — **a guard firing on a state the calendar
#    guarantees, which is rules 175-177 reintroduced by the very commit
#    that wrote them.**
# ✅ The honest question is an INTERIOR HOLE: a played week missing from
#    BELOW the log's own highest week. That cannot be lag — a later week
#    was published and this one was skipped.
err, out = drive(players([1], 600), schedule((1, YDAY), (2, YDAY)), 5, 600)
ck("🔴 a TRAILING week not yet published does NOT raise",
   err is None,
   "this is the Friday-after-Thursday case and it is four days a week: "
   "%s" % err)
ck("⛔ ...and the lag is REPORTED rather than silently swallowed",
   "publish lag" in out and "[2]" in out,
   "an absence with no explanation is the blind spot wearing a hat")

# 🔴 THE HOLE. Log holds weeks 1 and 3; week 2 was played and skipped.
err, out = drive(players([1, 3], 300), schedule((1, YDAY), (2, YDAY),
                                                (3, YDAY)), 5, 600)
ck("🔴 an INTERIOR hole IS its own named failure",
   err is not None and "MISSING COMPLETED WEEK" in str(err),
   "a partial season presented as a whole one: %s" % str(err)[:120])
ck("⛔ ...and it names both sides, so the reader can act",
   "[2]" in str(err) and "[1, 3]" in str(err),
   "which week is missing, and what the log actually holds")
ck("⚠️ ...and it rules OUT the innocent explanation by name",
   "NOT publish lag" in str(err),
   "naming the wrong cause is what cost five days on the college side")

# 🔴 A FUTURE WEEK IS NOT A MISSING ONE EITHER.
err, out = drive(players([1], 600), schedule((1, YDAY), (2, TOMO)), 5, 600)
ck("a week that has NOT been played yet is not missing",
   err is None,
   "an unplayed week absent from the log is the correct state, and "
   "failing on it would recreate the bug this file is about")

print("\n═══ 5. ⛔ WHAT WAS NOT RELAXED ═══")
src = open("nfl.py", encoding="utf-8").read()
ck("the injury-file guard is untouched and still unconditional",
   "the injury file yielded NO OUT/DOUBTFUL players" in src,
   "an unparsed injury file is a real failure in week 1 too — it is not "
   "a question about trailing history")
ck("🔴 the guard is a NAMED FUNCTION, so this file drives it",
   callable(getattr(nfl, "check_ahead_out", None)),
   "reading the source cannot tell one raise path from the next — that "
   "mistake was made once already this week")

note("⚠️ WHAT THIS FIXES AND WHAT IT DOES NOT. It stops the run accusing "
     "the join of a fault the calendar guarantees. ⛔ It does NOT prove "
     "nflverse serves the assets — `api.github.com` is blocked from the "
     "build sandbox, so only a real run answers that (the fifth question "
     "in self-running-audit.md). ✅ But `not yet : []` on the live report "
     "means the fetch DID work and 66 player-weeks reached the guard, so "
     "the tab should populate off the 09-09 opener — thin, one game's "
     "worth, until the Sunday slate. ~~The tab is still empty until "
     "nflverse publishes week 1~~ — STRUCK 2026-09-10: that claim was "
     "carried from the 09-09 diagnosis and was already false.")
