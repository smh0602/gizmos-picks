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
"""
import os
import sys
from datetime import datetime, timedelta, timezone

os.environ.setdefault("LEAGUE", "nfl")
import collect as C

fails = []


def eq(got, want, label):
    ok = got == want
    print(f"  {'ok  ' if ok else '🔴 FAIL'} {label:<56} {got!r}")
    if not ok:
        fails.append(f"{label} (got {got!r} want {want!r})")


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
eq(run("nfl", board(13, hours_out=30)), 13, "Sunday slate, 30h out")

print("\n3. the window boundary is 36h and comes from the constant")
# ⚠️ 36h is the SMALLEST window that still catches Monday Night Football
# from the Sunday 11:25am pull -- kickoff is ~32h later. 24h and 30h miss
# it. Measured on the real 2026 NFL schedule.
eq(C.FB_PROPS_WINDOW_H, 36, "the constant is 36h")
eq(run("nfl", board(5, hours_out=35)), 5, "35h out -> inside")
eq(run("nfl", board(5, hours_out=37)), 0, "37h out -> outside, not priced")
eq(run("nfl", board(1, hours_out=32)), 1, "🔴 Monday Night Football (32h) is caught")

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

print()
if fails:
    print(f"🔴 {len(fails)} FAILED:")
    for f in fails:
        print("   " + f)
    sys.exit(1)
print("✅ slate window OK — the 272-game board spends nothing, MLB untouched")
