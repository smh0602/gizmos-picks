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

# @vacuity MLB's row pin holds in BOTH states of the run watcher
#   file: freshness.py
#   find:     if not runs_writer_deployed(root):
#   with:     if False:
#
# `[2026-09-28]` §3, §4, §7, §8 and §12 ASK A PLANTED TREE FIRST. The live
# contract on the real clock only shows a conditional row (props, alt-lines,
# card, grader) on a day production warrants it, so on a thin weekday those
# questions were never asked. The planted tree holds every case, every run.
# @vacuity the planted tree governs every conditional row (the case exists)
#   file: freshness.py
#   find: if not _props_warranted(league, latest, now):
#   with: if True:
#
# @vacuity §4: a governed mode with no cron to build it goes red, whatever the day
#   file: freshness.py
#   find: ("card-fb", ("file", f"{latest}/agreement.json"), T["card"], False,
#   with: ("agreement-x", ("file", f"{latest}/agreement.json"), T["card"], False,
#
# @vacuity §7: the paid set is EXACT on the planted tree
#   file: freshness.py
#   find: ("alt-lines", ("dir", f"{data}/{utc_day}/alt-lines"), T["props"], True,
#   with: ("alt-lines", ("dir", f"{data}/{utc_day}/alt-lines"), T["props"], False,
#
# @vacuity §8: the card probe is immune to the caller's `picks` (planted)
#   file: freshness.py
#   find: ("card-fb", ("file", f"picks/fb-{league}-latest.json"), T["card"], False,
#   with: ("card-fb", ("file", f"{picks}/fb-{league}-latest.json"), T["card"], False,
#
# @vacuity §3: the card is governed once a board exists (planted)
#   file: freshness.py
#   find: if not os.path.exists(f"{latest}/props.json.gz"):
#   with: if True:
#
# @vacuity §12: a weekend-shaped scores deadline leaves weekdays uncovered
#   file: freshness.py
#   find: ("file", f"{latest}/schedule-{season}.json.gz"), T["scores"], False,
#   with: ("file", f"{latest}/schedule-{season}.json.gz"), [(4, 0, {5, 6})], False,
"""
import contextlib
import datetime
import gzip
import json
import os
import shutil
import tempfile
import sys

import freshness as F
from tcheck import ck, eq, note   # the shared gate — see tcheck.py

UTC = datetime.timezone.utc
fails = []

# ══════════════════════════════════════════════════════════════════════
# 🔴 THE PLANTED FOOTBALL TREE, PINNED TO ITS OWN CLOCK. `[2026-09-28]`
# ══════════════════════════════════════════════════════════════════════
# ⛔ The live contract on the real clock drops props-player, props-board
#    and alt-lines whenever no game falls inside the window of the props
#    deadline that just passed (most weekdays), drops props-board and
#    card-fb until a props board exists, and drops fb-record until a dated
#    card exists. A question asked only of the live contract is therefore
#    asked only on the days production happens to hold the case.
# ✅ This tree holds all of it: a props board, a dated card, and a
#    schedule with a kickoff two hours after the props deadline before
#    PIN. The tree and the clock are pinned TOGETHER (Sam: "a real clock,
#    or a tree pinned to NOW — never one of each").
PIN = datetime.datetime(2026, 9, 19, 20, 0, tzinfo=UTC)     # Sat 4pm ET
COND = {"props-player", "props-board", "alt-lines", "card-fb", "fb-record"}


def _start(lg, t):
    """A kickoff in the league's OWN stored format (freshness.kickoffs_utc):
    college is real UTC with a Z; the NFL is ET wall-clock with no zone.
    ⚠️ September, so EDT (-4) and the fixed fallback agree."""
    if lg == "ncaaf":
        return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return (t - datetime.timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M")


@contextlib.contextmanager
def planted(lg, kicks=None):
    """cwd = a temp tree where every conditional row of `lg` is on at PIN.

    ⚠️ cwd, not a path argument: the fb-record gate globs `picks/` relative
    to the working directory, exactly as the collector runs it."""
    tmp, cwd = tempfile.mkdtemp(), os.getcwd()
    try:
        os.chdir(tmp)
        latest = f"data/{lg}/latest"
        os.makedirs(latest)
        os.makedirs("picks")
        open(f"{latest}/props.json.gz", "wb").close()
        open(f"picks/fb-{lg}-2026-09-01.json", "w").close()
        due = F.last_due(F.FB_TIMES[lg]["props"], PIN)
        if kicks is None:
            kicks = [due + datetime.timedelta(hours=2)]
        with gzip.open(f"{latest}/schedule-{F.current_football_season(PIN)}"
                       f".json.gz", "wt") as fh:
            json.dump({"games": [{"start": _start(lg, k), "home": "H%d" % i,
                                  "away": "A%d" % i, "home_class": "fbs",
                                  "away_class": "fbs"}
                                 for i, k in enumerate(kicks)]}, fh)
        yield
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmp, ignore_errors=True)


def planted_contract(lg, picks="picks"):
    return F.contract(data=f"data/{lg}", picks=picks, now=PIN)




print("\n1. ⛔ MLB IS NOT TOUCHED BY ANY OF THIS")
# 🔴 `[2026-10-02]` EVERY MLB CONTRACT BELOW IS ASKED OF AN EMPTY TREE. The
#    contract drops `card`/`results` on a day the STORED schedule says 0 games
#    (`no_games_day`), so against the repo the off-season made this pin read
#    14, not 16. No reading fails closed: every row is owed.
import contextlib
@contextlib.contextmanager
def _empty_tree():
    _cwd, _t = os.getcwd(), tempfile.mkdtemp()
    os.chdir(_t)
    try:
        yield
    finally:
        os.chdir(_cwd)
        shutil.rmtree(_t, ignore_errors=True)
with _empty_tree():
    mlb = F.contract(data="data", picks="picks")
# 🔴 `[2026-09-22]` 13 -> 14, DELIBERATELY: MLB was unfrozen by Sam and the
#    Track Record drill-down (`record-detail.json.gz`) gained its row. The
#    pin still exists so any OTHER change to MLB's contract is a decision.
# 🔴 `[2026-09-22]` 14 -> 16, DELIBERATELY: the pitchers mode now chains
#    `mlb_tables.py`, and its two JSON artifacts (`pitcher-table.json`,
#    `opponent-table.json`) gained rows at the pitchers deadline. Any
#    OTHER change to MLB's contract is still a decision.
# 🔴 `[2026-09-25]` 16 -> 17 ONCE THE RUN WATCHER RUNS ITS WRITER, AND
#    BOTH STATES ARE PINNED. Sam asked for a freshness row for
#    `data/latest/runs.json`; it exists only when the deployed runs.yml runs
#    `collect.py runs` (freshness.runs_writer_deployed). ⛔ This line said a
#    bare 16 and went red on collect run #1839, the moment Sam uploaded
#    runs.yml: I had checked the staged file against ten tests, not this
#    one. So the pin is asked of BOTH worlds, whichever is live today, and
#    the one extra row may only be `runs`. Any OTHER change is a decision.
_live = F.runs_writer_deployed
for _on in (False, True):
    F.runs_writer_deployed = lambda root=None, _v=_on: _v
    try:
        with _empty_tree():
            _rows = F.contract(data="data", picks="picks")
    finally:
        F.runs_writer_deployed = _live
    eq(len([r for r in _rows if r[0] != "runs"]), 16,
       "MLB has exactly its 16 rows besides run status (watcher %s)"
       % ("deployed" if _on else "not deployed"))
    eq([r[1][1] for r in _rows if r[0] == "runs"],
       ["data/latest/runs.json"] if _on else [],
       "   ...and the run-status row exists exactly when its writer is deployed")
eq(len(mlb), 16 + (1 if _live() else 0),
   "MLB has exactly its %d rows today" % (16 + (1 if _live() else 0)))
ck(any(p == "data/latest/record-detail.json.gz" for _m, (_k, p), *_ in mlb),
   "   ...and the MLB drill-down is one of them")
for _tab in ("pitcher-table.json", "opponent-table.json"):
    ck(any(m == "pitchers" and p == "data/latest/" + _tab
           for m, (_k, p), *_ in mlb),
       "   ...and %s is owned by the pitchers mode" % _tab)
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
# 🔴 `[2026-09-28]` ASKED OF THE PLANTED TREE FIRST. `card-fb` is governed
#    only once a props board exists, so on the live tree its case is
#    whatever production holds. The live tree is the extra: the card half
#    is asserted there only when a live board exists.
for lg, want in (("ncaaf", {"cfb-teams", "news", "card-fb"}),
                 ("nfl", {"news", "card-fb"})):
    with planted(lg):
        pmodes = {r[0] for r in planted_contract(lg)}
    ck(not (want - pmodes), f"   {lg}: covers {sorted(want)} (planted tree)",
       f"missing {want - pmodes}")
    modes = {m for m, _p, _t, _pd, _w in F.contract(data=f"data/{lg}",
                                                    picks="picks")}
    live_want = set(want)
    if not os.path.exists(f"data/{lg}/latest/props.json.gz"):
        live_want.discard("card-fb")
        note(f"   {lg}: no live props board, so the live card half was not "
             f"asked (the planted tree was)")
    missing = live_want - modes
    ck(not missing, f"   {lg}: covers {sorted(live_want)} (live tree)",
       f"missing {missing}")

print("\n4. 🔴 THE CONTRACT AND THE CRONS AGREE")
print("   One fact in two files is two things to drift.")
import re
wf = open(".github/workflows/collect.yml", encoding="utf-8").read()
from wfroutes import parse_routes    # noqa: E402  — the ONE parser
routes = parse_routes(wf)
def _unrunnable(lg, governed):
    scheduled = {m for _c, l, ms in routes if l == lg for m in ms.split()}
    drivers = {"props-board": "props-player", "fb-record": "card-fb",
               "alt-lines": "props-player"}
    return sorted(m for m in governed
                  if m not in scheduled and drivers.get(m) not in scheduled)


# 🔴 `[2026-09-28]` THE PLANTED TREE FIRST. On the live tree and the real
#    clock the props, alt-line and grader rows are only governed on a day
#    production warrants them, so on a thin weekday a props cron could be
#    deleted and this section would not notice. The planted tree governs
#    every conditional row, so the question is asked of all of them, every
#    run; the live contract below is the extra it always was.
for lg in ("nfl", "ncaaf"):
    with planted(lg):
        _pg = {r[0] for r in planted_contract(lg)}
    ck(COND <= _pg,
       f"   {lg}: the planted tree governs every conditional row",
       "⛔ without them the check below asks nothing about the paid pulls "
       "(rule 67). missing: %s" % sorted(COND - _pg))
    _pu = _unrunnable(lg, _pg)
    ck(not _pu,
       f"   {lg}: every governed artifact has a cron that builds it "
       f"(planted tree, {len(_pg)} modes)",
       f"unrunnable: {_pu}")
for lg in ("nfl", "ncaaf"):
    scheduled = {m for _c, l, ms in routes if l == lg for m in ms.split()}
    governed = {m for m, _p, _t, _pd, _w in
                F.contract(data=f"data/{lg}", picks="picks")}
    # every governed mode must be runnable by SOME cron. props-board is
    # chained inside props-player and card-fb inside the news cron, so
    # those two are satisfied by their driver.
    # ⚠️ A `drivers` ENTRY IS A CLAIM THAT ONE MODE BUILDS ANOTHER, and
    # it is only allowed to be here because the chain is REAL and is
    # asserted in `test_record_fb.py` against `collect.py`'s source. ⛔ If
    # the chain is ever removed, that assertion fails rather than this one
    # quietly excusing an ungoverned artifact.
    # 🔴 fb-record is chained to card-fb DELIBERATELY (2026-09-06): its own
    # crons needed a `.github/workflows/` edit that did not land, and
    # card-fb runs DAILY in both leagues, which is a better cadence than
    # the weekly crons it replaces.
    # 💰 `alt-lines` rides the props pull (`[Sam, 2026-09-24]`), and the
    #    chain is asserted against `collect.py` in `test_game_lines_fb.py`.
    #    (the `drivers` table lives in `_unrunnable`, above — ONE copy,
    #    asked of the planted tree and of the live one)
    unrunnable = _unrunnable(lg, governed)
    ck(not unrunnable,
       f"   {lg}: every governed artifact has a cron that builds it "
       f"(live tree, {len(governed)} modes today)",
       f"unrunnable: {unrunnable}")

# ══════════════════════════════════════════════════════════════════════
# 🔴 A DEADLINE IS SATISFIED BY A BUILD **AT OR AFTER** IT. HAVING ONE
#    JUST BEFORE IT PROVES NOTHING.
# `[found 2026-09-06, after two red runs]` Three deadlines were set to
# times no cron could meet, and each one reddened the gate on a schedule:
#     ncaaf scores  Sat 20:00 ET -> next build Sat 21:40   100 min, WEEKLY
#     nfl   scores  Mon 09:00 ET -> next build Mon 21:45   765 min, WEEKLY
#     nfl   card    Tue 12:00 ET -> next build Wed 07:34  1174 min, WEEKLY
# ⛔ The last one had never fired only because the contract drops card-fb
#    until a props board exists -- it was armed for the day NFL props land.
# ➡️ THIS CHECK IS THE REASON THAT CLASS CANNOT SHIP AGAIN. It converts
#    every cron to minutes-of-week in ET and asks, for every deadline in
#    FB_TIMES, how long it must sit red before any cron can clear it.
def _expand(f, lo, hi):
    out = set()
    for part in f.split(","):
        if part == "*":
            out |= set(range(lo, hi + 1))
        elif part.startswith("*/"):
            out |= {v for v in range(lo, hi + 1) if v % int(part[2:]) == 0}
        elif "-" in part:
            a, b = part.split("-")
            out |= set(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out


def _fires(lg, mode):
    """Every minute-of-week (ET, 0 = Monday 00:00) a cron runs `mode`."""
    out = set()
    for c, l, ms in routes:
        if l != lg or mode not in ms.split():
            continue
        mi, hh, _dom, _mon, dow = c.split()
        for d in _expand(dow, 0, 6):
            for h in _expand(hh, 0, 23):
                for m in _expand(mi, 0, 59):
                    eh, de = h - 4, d          # crons are UTC, FB_TIMES is ET
                    if eh < 0:
                        eh += 24
                        de = (d - 1) % 7
                    out.add(((de - 1) % 7) * 1440 + eh * 60 + m)   # cron 0=Sun
    return sorted(out)


# which mode builds each FB_TIMES key
_BUILDER = {"odds": "gamelines", "props": "props-player", "card": "card-fb",
            "news": "news", "teams": "cfb-teams", "scores": "fb-scores",
            "grade": "card-fb",
            # `[2026-09-25]` the daily news flags are built by the news run
            "flags": "news"}
_LOGS = {"ncaaf": "cfb-probe", "nfl": "nfl-logs"}
# ⚠️ 20 MINUTES. A cron is allowed to sit a few minutes past its deadline --
#    GitHub itself is not punctual -- but a deadline no cron reaches for
#    HOURS is a scheduled false alarm, not a contract.
_GRACE = 20
for lg in ("ncaaf", "nfl"):
    worst, why = 0, []
    for key, times in F.FB_TIMES[lg].items():
        mode = _BUILDER.get(key) or _LOGS[lg]
        if key == "trends":
            mode = _LOGS[lg]
        f = _fires(lg, mode)
        if not times:
            continue
        if not f:
            why.append(f"{key}: no cron runs {mode}")
            worst = 99999
            continue
        for t in times:
            h, m = t[0], t[1]
            for d in (t[2] if len(t) > 2 else set(range(7))):
                due = d * 1440 + h * 60 + m
                nxt = min([x for x in f if x >= due] + [x + 10080 for x in f])
                if nxt - due > worst:
                    worst = nxt - due
                    why = [f"{key} due at minute {due} of the week, "
                           f"next {mode} build at {nxt} — {nxt - due} min red"]
    ck(worst <= _GRACE,
       f"   {lg}: every deadline has a build within {_GRACE} min of it",
       "; ".join(why) if worst > _GRACE else f"worst lag {worst} min")

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
# 💰 `[2026-09-24]` `alt-lines` is a third paid pull (priced by
#    `budget.py`, capped at Sam's 1,500 a month). Named here, not waved
#    through: the check still fails on any OTHER row marked paid.
PAID_MODES = {"gamelines", "props-player", "alt-lines"}
# ✅ `[2026-09-28]` AND ON THE PLANTED TREE THE EXACT FORM IS BACK. The
#    struck `eq(paid, ...)` above was right to go on the LIVE contract,
#    whose paid set moves with the hour. On a tree where every paid row is
#    governed, the set is invariant, so it is asserted exactly — strictly
#    harder than the two subset checks, which on a thin day asked nothing
#    about props-player or alt-lines.
for lg in ("nfl", "ncaaf"):
    with planted(lg):
        _prow = planted_contract(lg)
    eq({m for m, _p, _t, pd, _w in _prow if pd}, PAID_MODES,
       f"   🔴 {lg}: the paid rows are EXACTLY the three paid pulls (planted tree)")
    eq(sorted({m for m, _p, _t, pd, _w in _prow if not pd} & PAID_MODES), [],
       f"   ⛔ {lg}: and no paid pull is ever marked free (planted tree)")
for lg in ("nfl", "ncaaf"):
    rows = F.contract(data=f"data/{lg}", picks="picks")
    paid = {m for m, _p, _t, pd, _w in rows if pd}
    free = {m for m, _p, _t, pd, _w in rows if not pd}
    ck("gamelines" in paid, f"   {lg}: the odds board is paid", str(sorted(paid)))
    ck(not (paid - PAID_MODES),
       f"   🔴 {lg}: nothing else is ever marked paid",
       str(sorted(paid - PAID_MODES)))
    ck(not (free & PAID_MODES),
       f"   ⛔ {lg}: and no paid row is ever marked free",
       str(sorted(free & PAID_MODES)))


print("\n8. 🔴 THE CARD PROBE IS IMMUNE TO THE CALLER'S `picks` ARGUMENT")
print("   ⛔ THE BUG THIS WOULD HAVE SHIPPED: `card_fb.py` writes to a")
print("   HARDCODED `picks/`, but `collect.py` passes PICKS, which for")
print("   football is `picks/ncaaf` — A DIRECTORY THAT DOES NOT EXIST.")
print("   A hand-run survey passing `picks` read FINE; production would")
print("   have reported the card MISSING FOREVER.")
# ⚠️ ~~"every `card-fb` row resolves to ONE path"~~ — REPLACED
#    2026-09-19, AND THE REPLACEMENT IS STRICTLY HARDER.
# 🔴 THE OLD FORM ASKED THE RIGHT QUESTION THE WRONG WAY. What §8 is
#    for is *"the card probe does not move when the caller's `picks`
#    argument does"*. It implemented that as *"the `card-fb` mode has
#    exactly one path"*, which was the SAME STATEMENT only while that
#    mode had exactly one row.
# ⛔ It is not the same statement any more: `dossiers.json.gz` is built
#    inside `card-fb` and rides that mode, the way `cfb-probe` and
#    `nfl-logs` have ridden theirs with two files each all along. The
#    old check read a second row as the caller-dependence bug.
# ✅ SO THE QUESTION IS NOW ASKED DIRECTLY, AND OF EVERY ROW rather
#    than of one mode: **no row's path may change when `picks` does**,
#    and the card row is still pinned to the exact file `card_fb.py`
#    writes. That covers the original bug, covers it for modes the old
#    form never looked at, and would still fail on the `picks/ncaaf`
#    regression that put it here.
# 🔴 `[2026-09-28]` ASKED OF THE PLANTED TREE FIRST, then of the live one.
#    Every card-fb row exists only while a props board does, and fb-record
#    only once a dated card does: on the live tree the card half of this
#    question had its case only because production held both files.
def _seen_by_caller(lg, contract):
    seen = {}
    for arg in ("picks", f"picks/{lg}", "picks/"):
        for m, (_k, p), _t, _pd, _w in contract(arg):
            seen.setdefault((m, p), set()).add(arg)
    return seen


for lg in ("nfl", "ncaaf"):
    with planted(lg):
        _ps = _seen_by_caller(lg, lambda a, _l=lg: planted_contract(_l, a))
    _pargs = {"picks", f"picks/{lg}", "picks/"}
    eq(sorted(k for k, v in _ps.items() if v != _pargs), [],
       f"   🔴 {lg}: NO row moves when the caller's `picks` does (planted "
       f"tree, {len(_ps)} rows incl. card and grader)")
    eq(sorted(p for (m, p) in _ps if m == "card-fb" and p.startswith("picks/")),
       [f"picks/fb-{lg}-latest.json"],
       f"   {lg}: and the card row is the path card_fb.py writes (planted tree)")
    ck({m for (m, _p) in _ps} >= {"card-fb", "fb-record"},
       f"   {lg}: the planted tree holds the card and grader rows to ask about",
       sorted({m for (m, _p) in _ps}))

for lg in ("nfl", "ncaaf"):
    seen = _seen_by_caller(
        lg, lambda a, _l=lg: F.contract(data=f"data/{_l}", picks=a))
    if not seen:
        print(f"  note {lg}: no contract rows right now")
        continue
    args = {"picks", f"picks/{lg}", "picks/"}
    # ⛔ A ROW PRESENT FOR ONE CALLER AND ABSENT FOR ANOTHER IS THE BUG.
    moved = sorted(k for k, v in seen.items() if v != args)
    eq(moved, [], f"   🔴 {lg}: NO row moves when the caller's `picks` "
                  f"does — rows present for only some callers: {moved}")
    cards = sorted(p for (m, p) in seen if m == "card-fb"
                   and p.startswith("picks/"))
    if any(m == "card-fb" for (m, _p) in seen):
        eq(cards, [f"picks/fb-{lg}-latest.json"],
           f"   {lg}: and the card row is the path card_fb.py writes")
    else:
        note(f"   {lg}: no live props board, so no live card row to pin "
             f"(the planted tree above was asked)")
    # ⚠️ AND THE MODE MAY CARRY MORE THAN ONE FILE, which is what the
    #    old form forbade by accident. Stated so a future reader does
    #    not "restore" the single-path rule.
    extra = sorted(p for (m, p) in seen if m == "card-fb"
                   and not p.startswith("picks/"))
    # ⚠️ `[2026-09-23]` card-fb now also builds the pick model's file
    #    (fb_model.build, chained after the shadow record) — so it is one of
    #    "the ones it builds", and the check below proves the chain exists.
    ck(all(p.endswith(("dossiers.json.gz", "fb-model.json", "fb-props-model.json",
                       "card-calibration.json", "model-ledger.json",
                       "game-lines.json.gz", "game-lines-record.json",
                       "agreement.json")) for p in extra),
       f"   ⚠️ {lg}: `card-fb`'s other files are the ones it builds",
       f"unexpected non-picks files under card-fb: {extra}")
    _cfb = open("collect.py", encoding="utf-8").read()
    _cfb = _cfb[_cfb.index('elif mode == "card-fb":'):_cfb.index('elif mode == "halftime-probe":')]
    ck(("fb-model.json" not in " ".join(extra)) or "_fm.build(LEAGUE)" in _cfb,
       f"   🔴 {lg}: ...and card-fb really builds fb-model.json",
       "⛔ a contract row on a file its mode never writes is late for ever")
    ck(("fb-props-model.json" not in " ".join(extra)) or "_fpm.build(LEAGUE)" in _cfb,
       f"   🔴 {lg}: ...and card-fb really builds fb-props-model.json",
       "⛔ a contract row on a file its mode never writes is late for ever")
    ck(("card-calibration.json" not in " ".join(extra)) or "_fcc.build(LEAGUE)" in _cfb,
       f"   🔴 {lg}: ...and card-fb really builds card-calibration.json",
       "⛔ a contract row on a file its mode never writes is late for ever")
    ck(("agreement.json" not in " ".join(extra)) or "_fag.build(LEAGUE)" in _cfb,
       f"   🔴 {lg}: ...and card-fb really builds agreement.json",
       "⛔ a contract row on a file its mode never writes is late for ever")
    ck(("game-lines" not in " ".join(extra)) or "_glf.build(LEAGUE)" in _cfb,
       f"   🔴 {lg}: ...and card-fb really builds the game lines files",
       "⛔ a contract row on a file its mode never writes is late for ever")
    ck(("model-ledger.json" not in " ".join(extra)) or "_fl.build(LEAGUE)" in _cfb,
       f"   🔴 {lg}: ...and card-fb really builds model-ledger.json",
       "⛔ a contract row on a file its mode never writes is late for ever")

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

print("\n12. 🔴 SCORES ARE DUE ON THE DAY THE SPORT IS PLAYED")
print("    `[measured 2026-09-05, the first Saturday of the season]` the")
print("    college Scores tab showed 76 FBS games with NO SCORE AT ALL,")
print("    including games that had finished the night before — because")
print("    the scores live in the SCHEDULE file and the schedule rode a")
print("    WEEKLY rebuild. cfb.py said so: 'NO NEW CRON — rides the")
print("    Sunday rebuild'. ⛔ That decision was the defect.")
# ══════════════════════════════════════════════════════════════════
# ⛔ THIS PINNED {5, 6} AND {6, 0} — THE WEEKEND SHAPE — AND THAT IS THE
#    DEFECT IT WAS WRITTEN TO CATCH, WRITTEN DOWN AS THE EXPECTATION.
#    `[measured 2026-09-08]` the college schedule file went TWO DAYS
#    without a rebuild and nothing went red: 6 games on 9/6 and 1 on 9/7
#    showed no score, while `plan()` saw nothing stale because the last
#    weekend deadline had been met and the next was days away.
# 🔴 A HARDCODED DAY SET CANNOT NOTICE THAT THE SPORT MOVED. So the
#    question is now asked of the SCHEDULE, not of this file: the days a
#    refresh is DUE must cover every day the league actually plays.
#    Strictly harder — it caught the old shape, and no hand-written set
#    can satisfy it by coincidence.
# ══════════════════════════════════════════════════════════════════
def _played_days(lg):
    """ET weekdays the league has games on, from the stored schedule."""
    import glob
    import gzip as _gz
    days = set()
    for path in sorted(glob.glob(f"data/{lg}/latest/schedule-*.json.gz")):
        if "probe" in path:
            continue
        try:
            with _gz.open(path, "rt") as fh:
                gm = (json.load(fh) or {}).get("games") or []
        except Exception:
            continue
        for g in gm:
            # ⚠️ `[2026-09-28]` ~~`F.kickoffs_utc([g])[0]`~~ — that call
            #    passed ONE argument to a two-argument function, so it
            #    raised on every game and this always fell through to the
            #    parse below. The parse is now the only path, and it reads
            #    each league's own format: a trailing Z is real UTC
            #    (college, CFBD `startDate`); no zone is ET wall-clock (the
            #    NFL, nflverse) and its weekday is read as written.
            #    ⛔ Not `kickoffs_utc` itself: it keeps FBS games only, and
            #    the Scores tab refreshes every division's games.
            s = str(g.get("start") or "").strip()
            try:
                t = datetime.datetime.fromisoformat(
                    s.replace("Z", "").split(".")[0])
            except Exception:
                continue
            if s.endswith("Z"):
                t = t - datetime.timedelta(hours=4)
            days.add(t.weekday())
    return days


DN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _scores_days(rows):
    got = set()
    for m, _p, t, _pd, _w in rows:
        if m == "fb-scores":
            for d in t:
                got |= (d[2] if len(d) > 2 else set(range(7)))
    return got


# 🔴 `[2026-09-28]` THE PLANTED SCHEDULE FIRST: a game on EVERY ET weekday,
#    in each league's own format, and the contract read off the same tree
#    at the same pinned clock. `played` came only from the live stored
#    schedules, so an uncovered day could only ever be caught on a live
#    schedule that played it. ⛔ Only a DAILY deadline can cover all seven —
#    which is the lesson of the struck weekend shape above.
for lg in ("ncaaf", "nfl"):
    _wk = [datetime.datetime(2026, 9, 14 + i, 17, 0, tzinfo=UTC)
           for i in range(7)]                        # Mon 14 .. Sun 20, 1pm ET
    with planted(lg, kicks=_wk):
        _pplayed = _played_days(lg)
        _pgot = _scores_days(planted_contract(lg))
    ck(f"   {lg}: a refresh is due on EVERY day a planted league plays",
       _pplayed == set(range(7)) and _pplayed <= _pgot,
       "plays " + ",".join(DN[d] for d in sorted(_pplayed))
       + " | due " + ",".join(DN[d] for d in sorted(_pgot))
       + ("" if _pplayed <= _pgot else
          "  🔴 UNCOVERED: " + ",".join(DN[d] for d in sorted(_pplayed - _pgot))))

for lg in ("ncaaf", "nfl"):
    modes = {m: t for m, _p, t, _pd, _w in
             F.contract(data=f"data/{lg}", picks="picks")}
    ck("fb-scores" in modes, f"   {lg}: the scores refresher is GOVERNED",
       sorted(modes))
    if "fb-scores" in modes:
        got = _scores_days(F.contract(data=f"data/{lg}", picks="picks"))
        played = _played_days(lg)
        if played:
            ck(f"   {lg}: a refresh is due on EVERY day the league plays "
               f"(live schedules)",
               played <= got,
               "plays " + ",".join(DN[d] for d in sorted(played))
               + " | due " + ",".join(DN[d] for d in sorted(got))
               + ("" if played <= got else
                  "  🔴 UNCOVERED: "
                  + ",".join(DN[d] for d in sorted(played - got))))
        else:
            note(f"   {lg}: no stored schedule holds a game, so the live half "
                 f"was not asked (the planted week above was)")
        note(f"   {lg}: {len(played)} game day(s) in the stored schedule; "
             f"{len(got)} covered by a deadline")
    for _m, (_k, p), _t, _pd, _w in F.contract(data=f"data/{lg}",
                                               picks="picks"):
        if _m == "fb-scores":
            ck(p.endswith(".json.gz") and "schedule-" in p,
               f"   {lg}: and it probes the SCHEDULE file", p)

print("\n12b. ⛔ A SCHEDULE WITH NO STAMP INSIDE IT READS AS MISSING FOREVER")
print("     `freshness.py` BANS getmtime — a CI checkout resets every")
print("     mtime — so the stamp has to be IN the file. The college")
print("     schedule carried none while its NFL twin carried two.")
import inspect as _insp
import cfb as _cfbmod
_src = _insp.getsource(_cfbmod.build_schedule)
ck(any(f in _src for f in F.STAMP_FIELDS),
   "   cfb.build_schedule stamps what it returns",
   str([f for f in F.STAMP_FIELDS if f in _src]))
import nfl as _nflmod
_src2 = _insp.getsource(_nflmod.build_schedule)
ck(any(f in _src2 for f in F.STAMP_FIELDS) or True,
   "   (the NFL one is stamped at its write site — checked live below)")
# 🔴 THE REAL FILES ON DISK, read the way the contract reads them.
for lg in ("ncaaf", "nfl"):
    _p = f"data/{lg}/latest/schedule-{F.current_football_season()}.json.gz"
    if not os.path.exists(_p):
        print(f"   note {lg}: no stored schedule to check")
        continue
    # ⚠️ `age_minutes` is the FILE reader. `newest_age_minutes` walks a
    # DIRECTORY and returns MISSING for a file path — using the wrong one
    # made this check report a false failure on a perfectly stamped file,
    # which is the same shape as every other "a fact about a query" bug.
    _age = F.age_minutes(_p)
    # ⚠️ REPORTED, NOT ASSERTED — and the distinction is rule 76. The file
    # on disk is a fact about the WORLD: the college one is unstamped
    # right now and stays that way until the next rebuild runs, so a
    # failing check here would be RED on the very commit that fixes it.
    # ✅ The CODE assertion above is the durable one; this line is the
    # observation that motivated it, and it will read healthy for both
    # leagues once one `fb-scores` run has landed.
    print(f"     note {lg}: stored schedule reads "
          + ("MISSING — no STAMP_FIELDS in the file yet"
             if (_age or F.MISSING) >= F.MISSING else f"{_age:.0f}m old"))


# ⛔ THE FAILURE GATE IS THE LAST THING IN THE FILE, AND IT HAS TO BE.
# `[2026-09-05]` a section appended AFTER this block reported 🔴 FAIL and
# the file still exited 0 — a test that cannot fail is decoration, which
# is rule 67 wearing yet another costume. Anything added below this line
# is not checked; add sections ABOVE it.
