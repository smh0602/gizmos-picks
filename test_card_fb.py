#!/usr/bin/env python3
"""`card_fb.py` — the football picks board.

🔴 WHAT THIS FILE IS REALLY GUARDING. This board shows a CONFIDENCE
PERCENTAGE next to a price on a page Sam bets from. Every failure below
produces a board that renders perfectly and is wrong:

  1. ⛔ A COLLEGE ROW MUST NEVER CARRY A RATE. Measured 2026-09-03: CFBD
     publishes no snap data, so a college player appears in the log only
     in games where he TOUCHED THE BALL — 3.5% of college receiver games
     have zero catches against 25.8% in the NFL, and the median college
     receiver is missing SIX of his team's THIRTEEN games. A rate over
     that denominator reads too high on every over. ⚠️ Nothing about the
     resulting number would look wrong.
  2. 🔴 THE SNAP FLOOR MUST BITE. Without it a WR3 on 16% of snaps who
     catches nothing counts as evidence about a WR1's line — worth 23.9
     points on under 2.5 receptions. This is MLB's cameo bug, and it put
     bench bats on top of the board before `pa >= 3` replaced `pa > 0`.
  3. ⛔ NO ROW MAY EVER CLAIM `MODEL` (ledger rule 55). Three football
     models were tested and all three lost to a season average.
  4. 🔴 AN AMBIGUOUS NAME GETS NO RATE, NOT A GUESS. Attaching one
     player's record to another player's price is silent and total.
  5. THE CARD IS DATED BY THE SLATE IN ET, never by the UTC wall clock
     (ledger rule 60).

⚠️ No network. Every input here is constructed.
"""
import importlib
import json
import os
import sys
import tempfile

fails = []


def eq(got, want, label):
    ok = got == want
    print(f"  {'ok  ' if ok else '🔴 FAIL'} {label:<54} {got!r}")
    if not ok:
        fails.append(f"{label} (got {got!r} want {want!r})")


def load(league):
    os.environ["LEAGUE"] = league
    for m in list(sys.modules):
        if m == "card_fb":
            del sys.modules[m]
    return importlib.import_module("card_fb")


def game(snap, rec=0, rec_yds=0, rush_yds=0, td=0):
    return {"snap_pct": snap, "rec": rec, "rec_yds": rec_yds,
            "rush_yds": rush_yds, "rec_td": td, "rush_td": 0,
            "pass_yds": 0, "pass_td": 0}


print("1. ⛔ COLLEGE CARRIES NO RATE — the finding this file exists for")
C = load("ncaaf")
eq(C.RATES_OK, False, "🔴 rates are OFF for college")
eq(C.LEAGUE, "ncaaf", "league read from env")
eq("touched the ball" in C.COLLEGE_NOTE, True, "and the page is told why")

print("\n2. 🔴 THE SNAP FLOOR BITES (MLB's cameo bug, in football)")
N = load("nfl")
eq(N.RATES_OK, True, "rates are ON for the NFL")
eq(N.SNAP_FLOOR, 0.50, "the floor is the pre-registered 0.50")
# eight starter games, all UNDER 3.5 receptions... plus eight cameos with
# zero catches. ⛔ If the floor does not bite, the cameos inflate the under.
starter = [game(0.80, rec=5) for _ in range(8)]      # 5 catches: OVER 3.5
cameo = [game(0.16, rec=0) for _ in range(8)]        # blank cameo: UNDER
r = N.rate_for(starter + cameo, "player_receptions", 3.5, "under")
eq(r[2], 8, "🔴 only the 8 starter games counted, not 16")
eq(r[1], 0, "and he was never under 3.5 in them")
no_floor = sum(1 for g in starter + cameo if float(g["rec"]) < 3.5)
eq(no_floor, 8, "  (with no floor the same data says 8 unders — the bug)")

print("\n3. a rate needs a sample, and the prior never says 0% or 100%")
eq(N.rate_for([game(0.9, rec=5)] * 5, "player_receptions", 3.5, "over"), None,
   f"fewer than {N.MIN_GAMES} games is not a rate")
r = N.rate_for([game(0.9, rec=5)] * 10, "player_receptions", 3.5, "over")
eq(r[0] < 100, True, "🔴 10 for 10 is smoothed BELOW 100%")
r0 = N.rate_for([game(0.9, rec=0)] * 10, "player_receptions", 3.5, "over")
eq(r0[0] > 0, True, "and 0 for 10 is smoothed ABOVE 0%")

print("\n4. a game with NO snap field is dropped, not assumed to qualify")
eq(len(N.qualifying([{"rec": 9}, game(0.9), game(0.2)])), 1,
   "⚠️ an absence is evidence about the feed, not the player")

print("\n5. anytime TD is one-sided — 'yes' means he scored at all")
td = [game(0.9, td=1)] * 6 + [game(0.9, td=0)] * 6
r = N.rate_for(td, "player_anytime_td", None, "yes")
eq((r[1], r[2]), (6, 12), "6 of 12 games with a TD, line ignored")

print("\n6. ⛔ AN AMBIGUOUS NAME GETS NO RATE (players share names)")
idx = N.index_by_name({
    "1": {"name": "Josh Allen", "g": []},
    "2": {"name": "Josh Allen", "g": []},
    "3": {"name": "Mike Evans", "g": []},
})
eq(len(idx["josh allen"]), 2, "🔴 both Josh Allens kept — never collapsed")
eq(len(idx["mike evans"]), 1, "an unambiguous name resolves")
eq(N.norm("D'Andre Swift Jr."), "d andre swift",
   "punctuation and suffixes folded")
eq(N.norm("José Álvarez"), "jose alvarez", "accents folded")

print("\n7. 🔴 THE CARD IS DATED BY THE SLATE, IN ET — NOT THE UTC CLOCK")
# 2026-09-04T02:30:00Z is 10:30pm ET on SEPTEMBER 3.
b = {"games": [{"commence": "2026-09-04T02:30:00Z"},
               {"commence": "2026-09-06T17:00:00Z"}]}
eq(N.slate_date(b), "2026-09-03",
   "⛔ files under the ET date of the EARLIEST game, not 09-04")

print("\n8. ⛔ NO ROW MAY CLAIM MODEL, AND THE FLOOR SPLITS THE BOARD")
tmp = tempfile.mkdtemp()
cwd = os.getcwd()
try:
    os.chdir(tmp)
    os.makedirs(f"data/nfl/latest", exist_ok=True)
    import gzip
    board = {"pulled_at": "2026-09-03T22:31:00Z", "n_games": 1,
             "books_seen": ["fanduel"],
             "games": [{"id": "g1", "away": "A", "home": "H",
                        "commence": "2026-09-06T17:00:00Z",
                        "props": [
                            {"player": "Real Guy", "market": "player_receptions",
                             "line": 3.5, "sides": {
                                 "over": {"price": -110, "book": "fanduel",
                                          "n_books": 3, "link": "x"},
                                 # ⛔ below the -700 floor -> off the board
                                 "under": {"price": -900, "book": "fanduel",
                                           "n_books": 3, "link": "x"}}}]}]}
    with gzip.open("data/nfl/latest/props.json.gz", "wt") as fh:
        json.dump(board, fh)
    logs = {"season": 2025, "players": {"1": {
        "name": "Real Guy", "pos": "WR",
        "g": [game(0.9, rec=5) for _ in range(10)]}}}
    with gzip.open("data/nfl/latest/players-2025.json.gz", "wt") as fh:
        json.dump(logs, fh)
    N.main()
    out = json.load(open("picks/fb-nfl-latest.json"))
    eq([p["confidence_basis"] for p in out["picks"]], ["RECORD"],
       "🔴 the one on-board row is RECORD, never MODEL")
    eq(len(out["below_price_floor"]), 1, "the -900 side is off the board")
    eq(out["picks"][0]["raw"], "10 of 10", "carries MLB's own field names")
    eq(out["picks"][0]["break_even"], 52.4, "and its break-even")
    eq(out["kind"], "RECORD + MARKET", "the card says what it is")
    eq(os.path.exists("picks/fb-nfl-2026-09-06.json"), True,
       "the permanent dated file is written too")
finally:
    os.chdir(cwd)
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

print()
if fails:
    print(f"🔴 {len(fails)} FAILED:")
    for f in fails:
        print("   " + f)
    sys.exit(1)
print("✅ card_fb OK — college carries no rate, the snap floor bites, "
      "nothing claims MODEL")
