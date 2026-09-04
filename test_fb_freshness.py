#!/usr/bin/env python3
"""FOOTBALL'S FRESHNESS CONTRACT — the hole three bugs came through.

🔴 UNTIL 2026-09-04 `survey()` RETURNED 13 ROWS, EVERY ONE MLB. A football
artifact could rot indefinitely and nothing noticed, nothing said so, and
no run repaired it. **Three separate defects got through that hole in four
days**, and every one of them would have been a late row here:

  `cfb-teams`  a logo directory that existed only because one ad-hoc run
               wrote it — Sam reported "mo team logos"
  `news`       feeds adopted 09-03, never collected, both tabs empty
  `card-fb`    a board that only rebuilt inside a PAID pull, so the live
               college card sat four days stale showing a +5000 top row

⛔ THE CONTRACT AND THE CRONS ARE ONE FACT IN TWO FILES. A contract that
disagrees with the schedule reports lateness no run can clear, and a
banner nobody can fix is a banner everybody ignores. **Section 4 checks
they agree.**

⚠️ No network. Everything is read off disk or constructed.
"""
import datetime
import os
import sys

import freshness as F

UTC = datetime.timezone.utc
fails = []


def ck(cond, label, detail=""):
    print(f"  {'ok  ' if cond else '🔴 FAIL'} {label:<58} {detail}")
    if not cond:
        fails.append(label)


def eq(got, want, label):
    ck(got == want, label, f"{got!r}")
    if got != want and fails and fails[-1] == label:
        fails[-1] = f"{label} (got {got!r} want {want!r})"


print("\n1. ⛔ MLB IS NOT TOUCHED BY ANY OF THIS")
mlb = F.contract(data="data", picks="picks")
eq(len(mlb), 13, "MLB still has exactly its 13 rows")
ck(all(len(t) == 2 for _m, _p, times, _pd, _w in mlb for t in times),
   "🔴 no MLB deadline carries a day filter — they are all daily")

print("\n2. THE LEAGUE COMES FROM THE PATH, so no caller had to change")
for data, lg in (("data/nfl", "nfl"), ("data/ncaaf", "ncaaf")):
    rows = F.contract(data=data, picks="picks")
    ck(bool(rows), f"   {data} -> a {lg} contract", f"{len(rows)} rows")
    ck(all(data in p for _m, (_k, p), _t, _pd, _w in rows
           if not p.startswith("picks")),
       f"   every {lg} probe points inside {data}")

print("\n3. THE ARTIFACTS THAT ACTUALLY BROKE ARE NOW GOVERNED")
for lg, want in (("ncaaf", {"cfb-teams", "news", "card-fb"}),
                 ("nfl", {"news"})):
    modes = {m for m, _p, _t, _pd, _w in F.contract(data=f"data/{lg}",
                                                    picks="picks")}
    missing = want - modes
    ck(not missing, f"   {lg}: covers {sorted(want)}", f"missing {missing}")

print("\n4. 🔴 THE CONTRACT AND THE CRONS AGREE")
print("   One fact in two files is two things to drift.")
import re
wf = open(".github/workflows/collect.yml", encoding="utf-8").read()
routes = re.findall(
    r'"([\d ,*/-]+)"\)\s*LEAGUE=(\w+);\s*MODES="([a-z0-9 -]+)"', wf)
for lg in ("nfl", "ncaaf"):
    scheduled = {m for _c, l, ms in routes if l == lg for m in ms.split()}
    governed = {m for m, _p, _t, _pd, _w in
                F.contract(data=f"data/{lg}", picks="picks")}
    # every governed mode must be runnable by SOME cron. props-board is
    # chained inside props-player and card-fb inside the news cron, so
    # those two are satisfied by their driver.
    drivers = {"props-board": "props-player"}
    unrunnable = sorted(m for m in governed
                        if m not in scheduled
                        and drivers.get(m) not in scheduled)
    ck(not unrunnable,
       f"   {lg}: every governed artifact has a cron that builds it",
       f"unrunnable: {unrunnable}")

print("\n5. A WEEKLY DEADLINE IS NOT LATE SIX DAYS OUT OF SEVEN")
print("   ⛔ The failure that would make the banner noise.")
tue_noon = [(12, 0, {1})]
# a file built Tuesday 12:30pm ET is fresh all week
built = datetime.datetime(2026, 9, 8, 16, 30, tzinfo=UTC)   # Tue 12:30 ET
for probe_day, label in ((9, "Wednesday"), (11, "Friday"), (13, "Sunday")):
    now = datetime.datetime(2026, 9, probe_day, 20, 0, tzinfo=UTC)
    due = F.last_due(tue_noon, now)
    ck(due is not None and built >= due,
       f"   {label}: a Tuesday-built file is still fresh",
       f"due {due:%a %d %H:%MZ}" if due else "no due")
# and it IS late once the next Tuesday passes
now = datetime.datetime(2026, 9, 15, 20, 0, tzinfo=UTC)     # next Tue
due = F.last_due(tue_noon, now)
ck(due is not None and built < due,
   "   🔴 the NEXT Tuesday, it is late — the deadline still bites")

print("\n6. ⚠️ AN ARTIFACT THAT CANNOT EXIST YET IS NOT LATE")
print("   A banner nobody can clear is a banner everybody ignores.")
import tempfile
import shutil
tmp = tempfile.mkdtemp()
cwd = os.getcwd()
try:
    os.chdir(tmp)
    os.makedirs("data/nfl/latest", exist_ok=True)
    modes = {m for m, _p, _t, _pd, _w in F.contract(data="data/nfl",
                                                    picks="picks")}
    ck("card-fb" not in modes,
       "   before the first props board, the CARD is not governed")
    ck("props-board" not in modes,
       "   nor is the board it would be built from")
    open("data/nfl/latest/props.json.gz", "wb").close()
    modes2 = {m for m, _p, _t, _pd, _w in F.contract(data="data/nfl",
                                                     picks="picks")}
    ck("card-fb" in modes2,
       "   🔴 and they rejoin the moment a board exists", sorted(modes2))
finally:
    os.chdir(cwd)
    shutil.rmtree(tmp, ignore_errors=True)

print("\n7. THE PAID ROWS ARE MARKED PAID")
for lg in ("nfl", "ncaaf"):
    paid = {m for m, _p, _t, pd, _w in F.contract(data=f"data/{lg}",
                                                  picks="picks") if pd}
    eq(paid, {"gamelines", "props-player"}, f"   {lg} paid rows")

print()
if fails:
    print(f"🔴 {len(fails)} FAILURE(S)")
    for f in fails:
        print(f"   - {f}")
    sys.exit(1)
print("✅ football freshness contract: all checks passed")
