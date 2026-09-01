#!/usr/bin/env python3
"""Cron arithmetic for budget.py.

🔴 WHY THIS FILE EXISTS. `budget.py` has now silently UNDER-REPORTED
TWICE, and its own header says why that is the worst failure available to
it: **a budget tool that under-counts still prints ✅ fits.**

  1. `[2026-08-2x]` the mode pattern was `[a-z-]+`, which could not match
     a batched mode list, so every batched cron read as UNMAPPED and the
     props vanished. Reported 126/day against a true 606.
  2. `[2026-09-01]` `fires()` tested for "*" and for "-" and fell through
     to `t += 1` on everything else -- so **`*/6` counted as ONE fire a
     day instead of FOUR.** Both football line-movement crons use `*/6`.
     Under-reported by 108 credits a week.

⛔ BOTH BUGS WERE IN CODE THAT LOOKED FINE AND PRINTED A PLAUSIBLE
NUMBER. That is the whole problem: nothing about 13,406 looks wrong next
to 13,871. ✅ So the arithmetic gets pinned to expectations written down
by hand, from cron's actual grammar -- not from what the code does.

⚠️ These are pure-arithmetic tests. No network, no data files, no clock.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(ROOT, "budget.py"), encoding="utf-8").read()

# ⚠️ Import the two functions WITHOUT running budget.py's body, which
# reads the workflow, walks data/ and prints a report. A test that needs
# the whole repo present is a test that gets deleted the first time it is
# inconvenient.
_m = re.search(r"def _slots.*?return _slots\(mins, 60\) \* _slots\(hours, 24\)",
               SRC, re.S)
if not _m:
    print("🔴 FAIL: budget.py no longer defines _slots/fires as expected.")
    print("   ⛔ The parser moved and this test went blind. Fix the test.")
    sys.exit(1)
NS = {}
exec(compile(_m.group(0), "budget-parser", "exec"), NS)
fires, _slots = NS["fires"], NS["_slots"]

fails = []


def eq(got, want, label):
    ok = got == want
    print(f"  {'ok  ' if ok else '🔴 FAIL'} {label:<34} got {got:<4} want {want}")
    if not ok:
        fails.append(label)


print("fires() — runs per DAY")
# ── the shapes actually deployed ──────────────────────────────────────
eq(fires("4 10 * * *"),        1,  "single minute+hour")
eq(fires("5 13,19,1 * * *"),   3,  "hour LIST")
eq(fires("9 */3 * * *"),       8,  "hour STEP */3")
eq(fires("20 */6 * * 4,5,6"),  4,  "hour STEP */6  (was 1)")
eq(fires("25 */6 * * 0,1,4"),  4,  "hour STEP */6  (was 1)")
eq(fires("20 15 * * 6"),       1,  "Saturday, one hour")
eq(fires("30 22 * * 4"),       1,  "Thursday, one hour")
# ── shapes we do not deploy but cron permits, so the parser must hold ─
eq(fires("0 9-17 * * *"),      9,  "hour RANGE 9-17")
eq(fires("0 9/3 * * *"),       5,  "bare value WITH step (9,12,15,18,21)")
eq(fires("0 0-23/6 * * *"),    4,  "RANGE with step")
eq(fires("0,30 * * * *"),     48,  "minute list x every hour")
eq(fires("*/15 * * * *"),     96,  "minute step x every hour")
eq(fires("0 1,9-11 * * *"),    4,  "list containing a range")

print("\n_slots() — day-of-week field, range size 7")
eq(_slots("*", 7),      7, "every day")
eq(_slots("4,5,6", 7),  3, "Thu/Fri/Sat")
eq(_slots("0,1,4", 7),  3, "Sun/Mon/Thu")
eq(_slots("6", 7),      1, "Saturday only")
eq(_slots("1-5", 7),    5, "weekdays")
eq(_slots("*/2", 7),    4, "every other day  (would have read 1)")

# ══════════════════════════════════════════════════════════════════════
print("\nREGRESSION — the exact bug, stated as the bug")
# 🔴 The old parser: `if f == "*": return 24` else count comma-parts,
# treating anything without "-" as a single value. Pin the DIFFERENCE so
# nobody reintroduces it by "simplifying".
_old_would_say = 1
eq("differs" if fires("20 */6 * * 4,5,6") != _old_would_say else "SAME",
   "differs", "*/6 no longer counts as 1")
# ⛔ AND THE MONEY CONSEQUENCE, so the test says what it protects.
# 6 credits/run x 4 runs/day x 3 days = 72/wk, per league, two leagues.
eq(6 * fires("20 */6 * * 4,5,6") * _slots("4,5,6", 7), 72,
   "CFB line movement, credits/week")
eq(6 * fires("25 */6 * * 0,1,4") * _slots("0,1,4", 7), 72,
   "NFL line movement, credits/week")

print()
if fails:
    print(f"🔴 {len(fails)} FAILED: {', '.join(fails)}")
    sys.exit(1)
print("✅ budget cron arithmetic OK")
