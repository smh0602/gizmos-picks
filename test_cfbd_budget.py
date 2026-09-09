#!/usr/bin/env python3
"""
💰 THE CFBD CALL BUDGET — THE GUARD THAT DID NOT EXIST.

`[2026-09-09]` CFBD answered **429 on every endpoint from 2026-09-06**,
the college Trends table froze on 09-04 and the stored schedule on 09-06,
and **five days passed before anyone did the arithmetic.**

    CFBD free tier                    1,000 calls / month
    one cfb-probe rebuild, before        39 calls (32 of them /plays)
    rebuilds actually attempted         ~7 / day
    => burn                          ~8,200 / month   🔴 8x the plan

⛔ **THE ODDS API HAS HAD `budget.py` SINCE AUGUST FOR EXACTLY THIS.** The
lesson — *never put a count anywhere you cannot auto-update* — was learned,
written down, and then applied to ONE of the two metered sources. The
other had no number at all, so there was nothing to be wrong.

🔴 THE POINT OF THIS FILE IS THAT THE NUMBER IS DERIVED. If a cron is
added, a routing arm changes league, or a loop bound moves, the projection
moves with it and this test says so BEFORE the month's quota is gone.

⚠️ AND IT PRICES THE RETRY CASE, because that is what actually happened.
A schedule that fits at one attempt per build does not fit at seven.
"""
import os
import subprocess
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import cfbd_budget as B   # noqa: E402

print("\n═══ 1. 🔴 THE NUMBER IS DERIVED, NOT TYPED IN ═══")
src = open("cfbd_budget.py", encoding="utf-8").read()
ck("it reads the crons out of the deployed workflow",
   "parse_routes(wf)" in src,
   "the ONE routing-table parser — never a second copy")
ck("...and the loop bounds out of cfb.py",
   'open(os.path.join(ROOT, "cfb.py")' in src,
   "build_pace looped range(1,17) until 09-08; a hardcoded number here "
   "would still say 32")

print("\n═══ 2. ⛔ IT NOTICES THE FIX THAT MADE THE DIFFERENCE ═══")
per = B.calls_per_build(weeks_played=3)
ck("🔴 the early stop in build_pace is detected, not assumed",
   per["_early_stop"] is True,
   "if this reads False, build_pace is back to a flat 32 calls a rebuild")
ck("...and a rebuild costs far less than it did",
   per["cfb-probe"] < 39,
   f"{per['cfb-probe']} calls/rebuild now, against 39 before 2026-09-08")
note(f"fb-scores {per['fb-scores']} call(s)/build; cfb-teams "
     f"{per['cfb-teams']}")

print("\n═══ 3. 🔴 THE PROJECTION, AND THE TIER IT HAS TO FIT ═══")
r = subprocess.run([sys.executable, "cfbd_budget.py"],
                   capture_output=True, text=True, cwd=ROOT)
out = r.stdout
ck("the budget script runs and reports a monthly figure",
   "/month" in out and r.returncode in (0, 1), out[-200:])
month = None
for line in out.splitlines():
    if "/month" in line and "=" in line:
        try:
            month = int(line.split("=")[1].split("/month")[0].strip())
        except Exception:
            pass
ck("...and it is a real number", isinstance(month, int) and month > 0,
   f"{month} calls/month at one attempt per scheduled build")

# 🔴 THE BAR. The free tier is 1,000/month. ⛔ This does NOT assert we fit
#    it — Sam's tier is his decision and the Academic tier (free, .edu) is
#    3,000. What it asserts is that the projection is KNOWN and has not
#    silently exploded past the tier this repo is configured for.
PLAN = int(os.environ.get("CFBD_PLAN", "3000"))
if month:
    ck(f"🔴 the deployed schedule fits the configured {PLAN}/month plan",
       month < PLAN,
       f"{month}/month = {100.0 * month / PLAN:.0f}% of {PLAN}. "
       f"⛔ Over 100% means the quota runs out mid-month and every CFBD "
       f"mode 429s until the 1st.")
    note(f"⚠️ against CFBD's FREE tier (1,000) this is "
         f"{100.0 * month / 1000:.0f}% — the Academic tier (.edu, also "
         f"free) is 3,000 and Tier 1 is $1/month for 5,000.")

print("\n═══ 4. ⚠️ AND IT PRICES THE THING THAT ACTUALLY BLEW THE QUOTA ═══")
# ⛔ A schedule that fits at one attempt per build does not fit at seven.
#    Converge retried a FAILING source ~7 times a day, measured from the
#    commit history of backfill-report.txt across 09-06..09-08.
r7 = subprocess.run([sys.executable, "cfbd_budget.py", "--retries", "7"],
                    capture_output=True, text=True, cwd=ROOT)
ck("🔴 --retries prices the converge-storm case",
   "ATTEMPTS/DAY" in r7.stdout,
   "the floor number alone is what let this go unnoticed")
ck("...and it is materially larger than the floor",
   "OVER" in r7.stdout or "🔴" in r7.stdout,
   "7 attempts a day is ~7x the floor; on the free tier that is 6x over")
note("⛔ THE FLOOR IS NOT THE ANSWER. Always run --retries before calling "
     "a schedule affordable.")

print("\n═══ 5. ⛔ THE TIER NUMBERS ARE QUOTED, AND SAY SO ═══")
ck("the pricing figures are marked as read off CFBD's page, not derived",
   "QUOTED FROM CFBD'S PRICING PAGE, NOT DERIVED" in src,
   "a third party's pricing is not ours to compute — re-read it")
ck("⚠️ and the script says which half it owns",
   "WHAT THIS SCRIPT OWNS" in src,
   "it owns the schedule's implied volume; CFBD owns the limit")
