#!/usr/bin/env python3
"""`build_schedule` for both leagues, against synthetic feeds.

🔴 WHY A FIXTURE. Neither collector's score columns have ever been read
by this project. `cfb.py` reads a dozen `/games` fields and NOT ONE is a
score; `nfl.py` reads ten schedule columns and NOT ONE is a score. ⛔ So
`homePoints` / `home_score` are DOCUMENTATION until something has seen
them, and this project has been burned by exactly that: the
`stats_player_reg` season-totals trap, the participation filename, a
name join that matched 0 of 1,848.

✅ THE THINGS THIS PINS, ALL OF WHICH WOULD LOOK FINE IF BROKEN:
  1. A SCORE OF 0 IS A REAL SCORE. A shutout must not read as "not
     played". ⛔ This is the single easiest bug to ship here and the
     hardest to see -- it only appears on a blowout.
  2. A season with a schedule and NO scores yet is the NORMAL state in
     September, and must produce a usable file, not a failure.
  3. Both leagues emit the SAME SHAPE, so one renderer serves both.
  4. Missing score columns still ship the SCHEDULE. A schedule with no
     scores is a real product; an invented score is not.
  5. The wrong season's rows are excluded (nflverse ships every season
     in one file).

⚠️ No network, no data files, no clock.
"""
import sys

import cfb
import nfl

fails = []


def eq(got, want, label):
    ok = got == want
    print(f"  {'ok  ' if ok else '🔴 FAIL'} {label:<52} {got!r}")
    if not ok:
        fails.append(f"{label} (got {got!r} want {want!r})")


QUIET = lambda *a, **k: None


# ── CFB ───────────────────────────────────────────────────────────────
def cfb_run(rows, season=2026):
    cfb.get = lambda path, params, **k: (
        rows if params.get("seasonType") == "regular" else [])
    return cfb.build_schedule(season, QUIET)


print("1. CFB — a played game, a SHUTOUT, and an unplayed one")
doc, rep = cfb_run([
    {"id": 1, "week": 1, "startDate": "2026-09-03T22:00:00.000Z",
     "homeTeam": "Rutgers", "awayTeam": "UMass",
     "homePoints": 31, "awayPoints": 10, "completed": True},
    # 🔴 THE SHUTOUT. 0 is a real score.
    {"id": 2, "week": 1, "startDate": "2026-09-04T23:00:00.000Z",
     "homeTeam": "Ohio State", "awayTeam": "Akron",
     "homePoints": 45, "awayPoints": 0, "completed": True},
    {"id": 3, "week": 2, "startDate": "2026-09-12T20:00:00.000Z",
     "homeTeam": "Texas", "awayTeam": "Michigan",
     "homePoints": None, "awayPoints": None, "completed": False},
])
eq(rep["usable"], True, "usable")
eq(rep["games"], 3, "3 games")
eq(rep["final"], 2, "2 final")
g = {x["id"]: x for x in doc["games"]}
eq(g["2"]["away_score"], 0, "🔴 shutout keeps a score of 0")
eq(g["2"]["final"], True, "  ...and is still marked FINAL")
eq(g["3"]["final"], False, "unplayed game is not final")
eq(g["3"]["home_score"], None, "unplayed game has no score")
eq(rep["columns_used"]["home_score"], "homePoints", "named the score column")

print("\n2. CFB — schedule published, NO scores yet (September's normal state)")
doc, rep = cfb_run([
    {"id": 9, "week": 1, "startDate": "2026-09-03T22:00:00.000Z",
     "homeTeam": "Rutgers", "awayTeam": "UMass"},
])
eq(rep["usable"], True, "⚠️ still USABLE — a schedule is a product")
eq(rep["final"], 0, "nothing final")
eq(doc["games"][0]["final"], False, "game not final")
eq(rep["columns_used"]["home_score"], None, "no score column found, and it says so")

print("\n3. CFB — CFBD returns nothing: reported, not written")
doc, rep = cfb_run([])
eq(doc, None, "writes nothing")
eq(rep["usable"], False, "reported unusable")
eq("no games" in str(rep.get("error", "")), True, "error names the cause")


# ── NFL ───────────────────────────────────────────────────────────────
def nfl_run(rows, season=2026):
    nfl._rows = lambda seen, tag, fname, log: rows
    return nfl.build_schedule(season, seen={}, log=QUIET)


print("\n4. NFL — same shape, and a SHUTOUT again")
doc, rep = nfl_run([
    {"season": "2026", "week": "1", "gameday": "2026-09-10",
     "gametime": "20:20", "game_id": "2026_01_A_B",
     "home_team": "KC", "away_team": "BUF",
     "home_score": "27", "away_score": "0", "game_type": "REG"},
    {"season": "2026", "week": "2", "gameday": "2026-09-17",
     "gametime": "13:00", "game_id": "2026_02_C_D",
     "home_team": "PHI", "away_team": "DAL",
     "home_score": "", "away_score": "", "game_type": "REG"},
    # ⛔ WRONG SEASON — nflverse ships every year in ONE file.
    {"season": "2025", "week": "1", "gameday": "2025-09-04",
     "game_id": "2025_01_X_Y", "home_team": "X", "away_team": "Y",
     "home_score": "10", "away_score": "7"},
])
eq(rep["usable"], True, "usable")
eq(rep["games"], 2, "🔴 2 games — the 2025 row is excluded")
eq(rep["final"], 1, "1 final")
n = {x["id"]: x for x in doc["games"]}
eq(n["2026_01_A_B"]["away_score"], 0, "🔴 shutout keeps a score of 0")
eq(n["2026_01_A_B"]["final"], True, "  ...and is still marked FINAL")
eq(n["2026_02_C_D"]["final"], False, "empty string is not a score")
eq(n["2026_01_A_B"]["start"], "2026-09-10T20:20", "local date+time, no invented zone")

print("\n5. NFL — no rows for the requested season")
doc, rep = nfl_run([{"season": "2025", "week": "1", "game_id": "x",
                     "home_team": "X", "away_team": "Y"}])
eq(doc, None, "writes nothing")
eq("no 2026 rows" in str(rep.get("error", "")), True, "error names the season")


# ── the contract that lets one renderer serve both ────────────────────
print("\n6. 🔴 BOTH LEAGUES EMIT THE SAME SHAPE")
c, _ = cfb_run([{"id": 1, "week": 1, "startDate": "2026-09-03T22:00:00.000Z",
                 "homeTeam": "A", "awayTeam": "B",
                 "homePoints": 7, "awayPoints": 3, "completed": True}])
n2, _ = nfl_run([{"season": "2026", "week": "1", "gameday": "2026-09-10",
                  "gametime": "20:20", "game_id": "g", "home_team": "A",
                  "away_team": "B", "home_score": "7", "away_score": "3"}])
eq(sorted(c["games"][0]), sorted(n2["games"][0]),
   "per-game keys are identical")
eq(c["kind"] == n2["kind"] == "DESCRIPTIVE", True,
   "both stamped DESCRIPTIVE (rule 55)")

print()
if fails:
    print(f"🔴 {len(fails)} FAILED:")
    for f in fails:
        print("   " + f)
    sys.exit(1)
print("✅ schedule collectors OK")
