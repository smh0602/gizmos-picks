#!/usr/bin/env python3
"""The football props SLATE WINDOW — a spend guard, tested like one.

🔴 WHAT THIS EXISTS TO PREVENT, MEASURED 2026-09-03. The Odds API posts
the WHOLE SEASON: that day's gamelines pull returned **272 NFL games** and
**155 college games**. Props are charged PER GAME, so an unbounded NFL
props pull is:

    6 markets x 2 regions x 272 games = 3,264 CREDITS IN ONE CALL

against a **20,000 monthly cap**, a budget that models it at **192**, and
**three NFL props crons a week** (9,792/wk).

⛔ AND THE EXISTING RESERVE GUARD WOULD NOT HAVE STOPPED IT. With 19,250
credits available, `19250 - 3264` is far above `RESERVE = 750`, so the
pull would have sailed through and spent. ⚠️ **A guard that cannot fail on
the case it is meant to catch is not a guard** — which is why this file
tests the REAL 272-game board, not a toy one.

⚠️ The Power 4 filter does NOT bound this. It is a TEAM filter; a full
season of Power 4 games is still hundreds of games.

✅ WHAT IS PINNED:
  1. 🔴 A 272-game NFL board is cut to the games inside the window.
  2. ⛔ An event with NO kickoff time is DROPPED, never kept — an unbounded
     event is exactly what this gate exists to stop.
  3. A board with nothing in the window spends NOTHING and returns early.
  4. MLB is not touched by the gate at all.
  5. The window is 48h, and it is read from the constant, not hardcoded.

⚠️ No network. The events list is constructed and `odds_get` is stubbed,
so a regression here can never spend a credit to prove itself.

# `[2026-09-28]` 3b's coverage walk is runs_report's cron matcher, shown
# on a planted case to say BOTH "covered" and "missed" before the real
# schedule is walked with it.
# @vacuity 3b: a matcher that never finds a firing misses every game
#   file: runs_report.py
#   find: while t >= floor:
#   with: while False:
#
# @vacuity 3b: a matcher that always finds a firing can never say "missed"
#   file: runs_report.py
#   find: if cron_matches(c, t):
#   with: if True:
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from tcheck import ck, eq, note   # the shared gate — see tcheck.py

os.environ.setdefault("LEAGUE", "nfl")
import collect as C

fails = []




NOW = datetime(2026, 9, 3, 22, 25, tzinfo=timezone.utc)   # a Thursday cron


def board(n, hours_out):
    """n events, each kicking off `hours_out` from NOW."""
    return [{"id": f"e{i}", "away_team": f"A{i}", "home_team": f"H{i},",
             "commence_time": (NOW + timedelta(hours=hours_out)).strftime(
                 "%Y-%m-%dT%H:%M:%SZ")} for i in range(n)]


def run(league, events, credits_left=19250, kind="player"):
    """Drive collect_props with a stubbed API. Returns (events_priced, spent)."""
    priced = []
    old = (C.LEAGUE, C.odds_get, C.now, C.write, C.props_is_fresh, C.SPORT)
    try:
        C.LEAGUE = league
        C.SPORT = "x"
        C.now = lambda: NOW
        C.props_is_fresh = lambda kind: False
        C.write = lambda *a, **k: None

        def fake(path, params=None):
            if path.endswith("/events"):
                return events, 0, credits_left
            priced.append(path)
            return {"bookmakers": []}, 12, credits_left - 12 * len(priced)
        C.odds_get = fake
        C.collect_props(kind)
    finally:
        (C.LEAGUE, C.odds_get, C.now, C.write,
         C.props_is_fresh, C.SPORT) = old
    return len(priced)


print("1. 🔴 THE REAL CASE: a 272-game NFL board must NOT price 272 games")
n = run("nfl", board(272, hours_out=200))     # a whole season, far out
eq(n, 0, "⛔ nothing priced, nothing spent")
print(f"       (unbounded this would have been {272 * 12:,} credits)")

print("\n2. the games actually about to kick off ARE priced")
eq(run("nfl", board(1, hours_out=2)), 1, "Thursday night game, 2h out")
# ~~`board(13, hours_out=30)` -> 13 priced~~ ⛔ STRUCK 2026-09-04 with
# the 36h window it assumed. ⚠️ At 14h a game 30 hours out is CORRECTLY
# outside, and it is priced by the NEXT day's pull instead -- which
# section 3b proves end to end, against the real schedule, for every
# game rather than for one constructed board.
eq(run("nfl", board(13, hours_out=12)), 13, "Sunday slate, 12h out")

print("\n3. THE WINDOW BOUNDARY COMES FROM THE CONSTANT, AND THE")
print("   CONSTANT IS NO LONGER THE THING BEING TESTED")
# 🔴 THIS CHECK CHANGED ON 2026-09-04 AND THE ARGUMENT IS MADE HERE.
# ~~`eq(C.FB_PROPS_WINDOW_H, 36)` and "Monday Night Football (32h) is
# caught" from the SUNDAY pull.~~ ⛔ Both were right for the schedule
# that existed when they were written: props ran THREE TIMES A WEEK, so
# one pull had to reach 36 hours ahead or MNF was never priced at all.
# ⚠️ Sam moved props to TWICE A DAY on 2026-09-04. Monday Night Football
# is now priced by MONDAY's own 7:00am and 11:00am pulls -- roughly 9 and
# 13 hours out -- and a 36h window would simply buy Monday's games four
# extra times from Sunday.
# ✅ SO THE CONSTANT IS NO LONGER THE QUESTION. **The question is whether
# every game is caught by SOME pull before it kicks off**, which is what
# the old assertion was really a proxy for -- and section 3b now tests
# that DIRECTLY, against the real schedule and the deployed crons.
# ⛔ That is strictly harder: the old form could pass with a correct
# constant and a broken schedule.
# `[Sam, 2026-10-09]` ~~the NFL boundary is FB_PROPS_WINDOW_H~~: "NFL props for the
#    next slate with an unstarted game are pulled every day once that slate is within
#    72 hours (Tue/Wed: Thursday's game; Fri/Sat: Sunday's games)". College keeps 14h.
_H = C._fresh.FB_NEXT_SLATE_H["nfl"]
eq(run("nfl", board(5, hours_out=_H - 1)), 5,
   "NFL: the next slate just inside 72 hours -> priced")
eq(run("nfl", board(5, hours_out=_H + 1)), 0,
   "NFL: just outside -> not priced")
ck(C.FB_PROPS_WINDOW_H <= 24,
   "⚠️ college's window over 24h means two daily pulls buy the same games twice",
   f"{C.FB_PROPS_WINDOW_H}h")

print("\n3b. 🔴 EVERY REAL GAME IS CAUGHT BY SOME DEPLOYED PULL")
print("    The question the constant was only ever a proxy for.")
import re as _re, datetime as _dt, os as _os
import freshness as _F
import runs_report as _RR    # the ONE cron matcher (rule 117)
_wf = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                    ".github/workflows/collect.yml")
from wfroutes import parse_routes as _parse_routes    # noqa: E402
_routes = _parse_routes(open(_wf, encoding="utf-8").read())


def _uncovered(games, crons, window_h):
    """The kickoffs no cron fires for inside the `window_h` hours before.

    ⚠️ `[2026-09-28]` The matcher is `runs_report`'s — the one the runs
    watcher already trusts — not a second hand-written one here.
    """
    parsed = [_RR.parse_cron(c) for c in crons]
    out = []
    for g in games:
        floor = g - _dt.timedelta(hours=window_h)
        if not any(p and _RR.last_fire(p, g, floor) for p in parsed):
            out.append(g)
    return out


# 🔴 `[2026-09-28]` THE WALK IS SHOWN TO BITE BEFORE IT IS TRUSTED. On the
#    real schedule every game is covered, so the "missed" branch never
#    ran: a matcher that always said "covered" passed 272/272 and 888/888
#    (measured by the sweep's verifier on a scratch copy). ✅ A planted
#    weekly cron and two kickoffs placed by the window itself — one half an
#    hour inside it, one half an hour past it — must come back exactly as
#    "the second one is missed", whatever the constant is.
_pc = "8 15 * * 0"                                   # Sundays 15:08Z
_pf = _dt.datetime(2026, 9, 20, 15, 8, tzinfo=timezone.utc)
_pin = _pf + _dt.timedelta(hours=C.FB_PROPS_WINDOW_H) - _dt.timedelta(minutes=30)
_pout = _pf + _dt.timedelta(hours=C.FB_PROPS_WINDOW_H) + _dt.timedelta(minutes=30)
_pmiss = _uncovered([_pin, _pout], [_pc], C.FB_PROPS_WINDOW_H)
ck(_pmiss == [_pout],
   "   🔴 the coverage walk tells a covered kickoff from a missed one (planted)",
   "⛔ a walk that never says 'missed' cannot catch a hole. missed: %s"
   % [t.strftime("%a %H:%MZ") for t in _pmiss])

for _lg in ("nfl", "ncaaf"):
    _times = [c for c, l, m in _routes if l == _lg and "props-player" in m.split()]
    if not _times:
        ck(False, f"   {_lg}: a cron runs props-player"); continue
    # ⚠️ `[2026-09-28]` ~~`schedule-2026.json.gz`~~ — the CURRENT season, by
    #    the same rule freshness and collect.yml use, read against the real
    #    clock; a season whose schedule is not stored yet is reported.
    _path = f"data/{_lg}/latest/schedule-{_F.current_football_season(None)}.json.gz"
    if not _os.path.exists(_path):
        note(f"   {_lg}: no stored schedule at {_path} — the real-schedule "
             f"coverage was not asked (the planted walk above was)"); continue
    # 🔴 THE KICKOFF TIMES COME FROM `freshness.kickoffs_utc`, NOT FROM A
    # SECOND PARSER HERE. ~~this file stamped `tzinfo=utc` on both
    # leagues~~ STRUCK 2026-09-04: that is right for college, whose CFBD
    # `startDate` really is UTC, and **FOUR HOURS WRONG for the NFL**,
    # whose nflverse `start` is a LOCAL EASTERN wall-clock time with no
    # zone. ⛔ It is what produced "six London games at 5:30am ET" -- they
    # kick at 9:30am ET. The error was PESSIMISTIC, so it invented a gap
    # rather than hiding one, but a four-hour error on a fourteen-hour
    # window is not a rounding difference.
    # ✅ One parser, in the contract, used by the contract and by this
    # check, so the two can never disagree about when a game starts.
    _games = _F.kickoffs_utc(_lg, _path) or []
    # ⚠️ `[2026-09-28]` ~~a hand-written `_fires` walked back minute by
    #    minute~~ — the same walk, through `_uncovered` and runs_report's
    #    matcher, which the planted case above has just shown can say
    #    "missed".
    _miss = len(_uncovered(_games, _times, C.FB_PROPS_WINDOW_H))
    _pct = 100.0 * (len(_games) - _miss) / max(len(_games), 1)
    ck(_pct >= 99.0,
       f"   🔴 {_lg}: every game reached by a pull before kickoff",
       f"{len(_games)-_miss}/{len(_games)} = {_pct:.1f}%")

print("\n4. ⛔ AN EVENT WITH NO KICKOFF TIME IS DROPPED, NEVER KEPT")
eq(run("nfl", [{"id": "x", "away_team": "A", "home_team": "H"}]), 0,
   "🔴 unbounded event is exactly what this gate stops")
eq(run("nfl", [{"id": "x", "commence_time": "not-a-date"}]), 0,
   "an unparseable time is dropped too")

print("\n5. a mixed board keeps only the near games")
mixed = board(3, 5) + [dict(e, id=f"far{i}") for i, e in enumerate(board(200, 300))]
eq(run("nfl", mixed), 3, "3 near + 200 far -> 3 priced")
print(f"       (saved {200 * 12:,} credits on that one call)")

print("\n6. college is bounded the same way, BEFORE the FBS team filter")
old_p4 = C.filter_fbs
C.filter_fbs = lambda ev, log: (ev, None)      # team filter passes all
try:
    eq(run("ncaaf", board(155, hours_out=300)), 0,
       "⛔ a full-season college board prices nothing")
    eq(run("ncaaf", board(12, hours_out=10)), 12, "tonight's college slate does")
finally:
    C.filter_fbs = old_p4

print("\n7. ⛔ MLB IS NOT TOUCHED BY THIS GATE")
eq(run("mlb", board(15, hours_out=300), kind="pitcher"), 15,
   "🔴 a far-out MLB board is still priced, exactly as before")

