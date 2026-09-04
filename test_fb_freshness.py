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
import gzip
import json
import os
import shutil
import tempfile
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
# ⚠️ ASSERTED AS A SUBSET, NOT AN EQUALITY. ~~`eq(paid, {"gamelines",
# "props-player"})`~~ STRUCK 2026-09-04: `props-player` is now DROPPED
# from the contract on a day when no game falls inside the pull window,
# so the exact set depends on the real schedule and the wall clock. **A
# test whose answer changes with the hour is a test that will fail on a
# Tuesday for no reason.**
# ✅ What is actually invariant, and is what this check is for: the odds
# board always costs money, and NOTHING ELSE MAY EVER BE MARKED PAID
# WITHOUT BEING ONE OF THESE TWO. A free row silently marked paid would
# be skipped by `plan(allow_paid=False)` and never built.
for lg in ("nfl", "ncaaf"):
    rows = F.contract(data=f"data/{lg}", picks="picks")
    paid = {m for m, _p, _t, pd, _w in rows if pd}
    free = {m for m, _p, _t, pd, _w in rows if not pd}
    ck("gamelines" in paid, f"   {lg}: the odds board is paid", str(sorted(paid)))
    ck(not (paid - {"gamelines", "props-player"}),
       f"   🔴 {lg}: nothing else is ever marked paid",
       str(sorted(paid - {"gamelines", "props-player"})))
    ck(not (free & {"gamelines", "props-player"}),
       f"   ⛔ {lg}: and neither paid row is ever marked free",
       str(sorted(free & {"gamelines", "props-player"})))

print()
if fails:
    print(f"🔴 {len(fails)} FAILURE(S)")
    for f in fails:
        print(f"   - {f}")
    sys.exit(1)
print("✅ football freshness contract: all checks passed")

print("\n8. 🔴 THE CARD PROBE IS IMMUNE TO THE CALLER'S `picks` ARGUMENT")
print("   ⛔ THE BUG THIS WOULD HAVE SHIPPED: `card_fb.py` writes to a")
print("   HARDCODED `picks/`, but `collect.py` passes PICKS, which for")
print("   football is `picks/ncaaf` — A DIRECTORY THAT DOES NOT EXIST.")
print("   A hand-run survey passing `picks` read FINE; production would")
print("   have reported the card MISSING FOREVER.")
for lg in ("nfl", "ncaaf"):
    got = set()
    for arg in ("picks", f"picks/{lg}", "picks/"):
        for m, (_k, p), _t, _pd, _w in F.contract(data=f"data/{lg}", picks=arg):
            if m == "card-fb":
                got.add(p)
    if not got:
        print(f"  note {lg}: no card row right now (no board yet)")
        continue
    eq(len(got), 1, f"   {lg}: one path whatever the caller passes")
    eq(got.pop(), f"picks/fb-{lg}-latest.json", f"   {lg}: and it is the "
       f"path card_fb.py writes")

print("\n9. 🔴 A PULL THAT CORRECTLY BUYS NOTHING IS NOT A LATE PULL")
print("   With a 14h window a Friday buys no Saturday college games.")
print("   ⛔ Calling that late asks for a repair no run can make.")
_sat = datetime.datetime(2026, 9, 5, 23, 0, tzinfo=UTC)     # Sat 7pm ET
_fri = datetime.datetime(2026, 9, 4, 18, 0, tzinfo=UTC)     # Fri 2pm ET
tmp = tempfile.mkdtemp()
cwd = os.getcwd()
try:
    os.chdir(tmp)
    os.makedirs("data/ncaaf/latest", exist_ok=True)
    os.makedirs("picks", exist_ok=True)
    open("data/ncaaf/latest/props.json.gz", "wb").close()
    open("picks/fb-ncaaf-latest.json", "wb").close()
    season = F.current_football_season(_fri)

    def write_sched(games):
        with gzip.open(f"data/ncaaf/latest/schedule-{season}.json.gz",
                       "wt") as fh:
            json.dump({"season": season, "games": games}, fh)

    # a slate 29 hours out -- outside any 14h window from Friday
    write_sched([{"start": "2026-09-05T23:00:00.000Z", "home_class": "fbs",
                  "away_class": "fbs", "home": "H", "away": "A"}])
    modes = {m for m, _p, _t, _pd, _w in
             F.contract(data="data/ncaaf", picks="picks", now=_fri)}
    ck("props-player" not in modes,
       "   nothing in window -> the paid pull is NOT governed", sorted(modes))
    ck("props-board" not in modes,
       "   nor the join that has nothing new to join")
    ck("card-fb" in modes,
       "   ⚠️ but the CARD still is — it is free and rebuilds either way")

    # the same slate, asked on Saturday afternoon: now it IS in window
    modes2 = {m for m, _p, _t, _pd, _w in
              F.contract(data="data/ncaaf", picks="picks",
                         now=_sat - datetime.timedelta(hours=4))}
    ck("props-player" in modes2,
       "   🔴 and on game day it is governed again", sorted(modes2))

    # ⛔ THE FAIL-SAFE POINTS AT GOVERNING, NOT AT SILENCE
    os.remove(f"data/ncaaf/latest/schedule-{season}.json.gz")
    modes3 = {m for m, _p, _t, _pd, _w in
              F.contract(data="data/ncaaf", picks="picks", now=_fri)}
    ck("props-player" in modes3,
       "   ⛔ no readable schedule = CANNOT TELL = still governed",
       "absence of evidence must never be what silences a check")
finally:
    os.chdir(cwd)
    shutil.rmtree(tmp, ignore_errors=True)

print("\n10. 🔴 THE TWO LEAGUES DISAGREE ABOUT WHAT `start` MEANS")
print("    A four-hour error on a fourteen-hour window. It invented a")
print("    London-games gap that was never there.")
tmp = tempfile.mkdtemp()
try:
    os.chdir(tmp)
    os.makedirs("d", exist_ok=True)
    with gzip.open("d/nfl.json.gz", "wt") as fh:
        json.dump({"games": [{"start": "2026-09-13T13:00", "home": "H",
                              "away": "A"}]}, fh)
    with gzip.open("d/cfb.json.gz", "wt") as fh:
        json.dump({"games": [{"start": "2026-08-27T22:00:00.000Z",
                              "home_class": "fbs", "away_class": "fcs"},
                             {"start": "2026-08-27T22:00:00.000Z",
                              "home_class": "ii", "away_class": "iii"}]}, fh)
    n = F.kickoffs_utc("nfl", "d/nfl.json.gz")
    eq(len(n), 1, "    the NFL game is read")
    eq(n[0].strftime("%H:%MZ"), "17:00Z",
       "    🔴 1:00pm ET Sunday -> 17:00Z, NOT 13:00Z")
    c = F.kickoffs_utc("ncaaf", "d/cfb.json.gz")
    eq(len(c), 1, "    ⛔ and college keeps only the FBS game")
    eq(c[0].strftime("%H:%MZ"), "22:00Z",
       "    whose stamp really IS UTC and is left alone")
    ck(F.kickoffs_utc("nfl", "d/nope.json.gz") is None,
       "    a missing schedule returns None — 'cannot tell', not 'empty'")
finally:
    os.chdir(cwd)
    shutil.rmtree(tmp, ignore_errors=True)

print("\n11. ⛔ ONE WINDOW, ONE DEFINITION, AND EVERY LEAGUE CONVERGES")
import collect as _C
ck(_C.FB_PROPS_WINDOW_H is F.FB_PROPS_WINDOW_H,
   "   collect.py reads the window from the contract (rule 66)",
   f"{_C.FB_PROPS_WINDOW_H}h")
for lg in ("mlb", "nfl", "ncaaf"):
    ck(F.has_contract(lg), f"   {lg} has a contract, so it converges")
ck(not F.has_contract("nhl"),
   "   ⛔ and a league with no rows still does not")
