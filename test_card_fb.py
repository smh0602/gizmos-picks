#!/usr/bin/env python3
"""`card_fb.py` — the football picks board.

🔴 WHAT THIS FILE IS REALLY GUARDING. This board shows a CONFIDENCE
PERCENTAGE next to a price on a page Sam bets from. Every failure below
produces a board that renders perfectly and is wrong:

  1. ~~⛔ A COLLEGE ROW MUST NEVER CARRY A RATE.~~ ⛔ **STRUCK
     2026-09-04, ledger rule 75** — the 25.8%-vs-3.5% comparison behind
     it put a SNAP-logged file beside a STAT-logged one and could never
     have supported the conclusion. ✅ **REPLACED BY A STRICTLY LARGER
     CONTRACT:** college carries a rate over a UNION denominator, and
     section 1 pins the MEASURED gate instead of a blanket ban — the
     receptions floor, the unmeasured-market rule, the union
     denominator, the page copy, and that the NFL path is untouched.
     ⚠️ Nothing about a wrong number here would look wrong.
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


def ck(cond, label, detail=""):
    print(f"  {'ok  ' if cond else '🔴 FAIL'} {label:<54} {detail}")
    if not cond:
        fails.append(label)


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


print("1. 🔴 COLLEGE RATES — THE CHECK CHANGED ON 2026-09-04, AND THE")
print("   ARGUMENT IS MADE HERE RATHER THAN LEFT IMPLICIT.")
print("   ~~`eq(C.RATES_OK, False)` — college carries no rate at all.~~")
print("   ⛔ STRUCK. That assertion encoded a CONCLUSION drawn from an")
print("   invalid comparison (ledger rule 75): NFL 25.8% vs college 3.5%")
print("   zero-catch games compared a SNAP-logged file with a STAT-logged")
print("   one. Asked the same way — share of the player's team's games —")
print("   college WR is 0.750 and NFL WR is 0.706.")
print("   ✅ THE REPLACEMENT IS STRICTLY MORE CHECKING, NOT LESS: one")
print("   boolean became four properties, each tied to a measured bar.")
C = load("ncaaf")
eq(C.LEAGUE, "ncaaf", "league read from env")
eq(C.RATES_OK, True, "college may carry a rate at all")
# (a) the gate is on the MARKET and the LINE, not on the league
eq(C.market_rateable("player_receptions", 2.5)[0], False,
   "🔴 receptions o2.5 is GATED — the one cell that failed T52b")
eq(C.market_rateable("player_receptions", 3.5)[0], True,
   "   receptions o3.5 passed its bar, so it is allowed")
eq(C.RATE_MIN_REC_LINE, 3.5,
   "⛔ the floor is pinned — do not tune it to add board rows")
# (b) a market nobody measured inherits nothing
eq(C.market_rateable("player_pass_tds", 1.5)[0], False,
   "⛔ an UNMEASURED market gets no rate, however similar it looks")
eq("player_pass_yds" in C.RATE_MEASURED, True, "   passing yards WAS measured")
eq("player_pass_tds" in C.RATE_MEASURED, False, "   passing TDs was NOT")
# (c) the gate reason reaches the reader in English
ok, why = C.market_rateable("player_receptions", 2.5)
eq("quiet games" in why or "quiet" in why, True,
   "   and the row says why, in English")
# (d) the denominator really is the union, and the NFL's really is not
eq(len(C.qualifying([{"rec": 1}, {"rec": 0}, {"rec": 0}])), 3,
   "🔴 college counts EVERY game he appears in (union denominator)")
eq("quiet" in C.COLLEGE_NOTE, True, "and the page is told the known limit")
eq("touched the ball" in C.COLLEGE_NOTE, False,
   "⛔ the struck claim is gone from the page copy")
# (e) ⛔ THE NFL IS UNTOUCHED BY ANY OF IT
_N = load("nfl")
eq(_N.market_rateable("player_receptions", 0.5)[0], True,
   "⛔ nothing is gated in the NFL — it has the TRUE denominator")
eq(len(_N.qualifying([{"rec": 1}, {"rec": 0}])), 0,
   "   and the NFL still drops games with no snap field")

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

print("\n9. 🔴 THE BOARD SAM SAW: 100% ANYTIME TD WITH +5000 ON TOP")
# ⛔ MEASURED ON THE LIVE 2026-09-03 COLLEGE CARD. With no rate to sort
# by, the fallback sorted on price DESCENDING, so the longest longshot on
# the slate led a picks board. Sam: "touchdown bets are basically long
# shots ... not every single td prop on the board should be in gizmos
# picks that makes no sense."
C = load("ncaaf")


def mkrow(market, price, conf=None):
    r = {"market": market, "price": price, "clears_price_floor": price >= -700}
    if conf is not None:
        r["confidence"] = conf
    return r


# a slate shaped like the real one: a pile of plus-money TDs and plenty
# of ordinary -110 lines in four other markets
slate = [mkrow("player_anytime_td", p) for p in
         (5000, 4000, 4000, 1500, 1500, 1300, 1100, 900, 600, 450, 300, 250, 180, 145)]
for m in ("player_receptions", "player_reception_yds",
          "player_rush_yds", "player_pass_yds"):
    slate += [mkrow(m, p) for p in (-110, -115, -120, 105, -105)]

kept = [r for r in slate if (r["price"] or 0) <= C.PRICE_CEIL]
eq(C.PRICE_CEIL, 400, "the ceiling is Sam's -400 gate, mirrored")
eq(any(r["price"] > 400 for r in kept), False,
   "🔴 nothing longer than +400 survives the ceiling")
eq(len(slate) - len(kept), 10, "  ...10 longshots dropped from this slate")

kept.sort(key=lambda r: (r.get("confidence") is None,
                         -(r.get("confidence") or 0),
                         -(r.get("price") or -10000)))
board = C.fill_board(kept, 12)
import collections as _c
mix = _c.Counter(r["market"] for r in board)
eq(len(board), 12, "the board fills to its cap")
eq(len(mix) >= 4, True, f"🔴 at least four markets represented, not one ({dict(mix)})")
top = max(mix.values()) / len(board)
eq(top <= 0.34 + 0.01, True,
   f"⛔ no market exceeds a third of the board (worst {top:.0%})")
eq(board[0]["price"] <= 400, True, "and the top row is not a longshot")

print("\n10. ⚠️ ROUND-ROBIN NEVER REORDERS WITHIN A MARKET")
one = [mkrow("player_receptions", p) for p in (-105, -110, -120)]
eq([r["price"] for r in C.fill_board(one, 3)], [-105, -110, -120],
   "a single market keeps its own order")
eq(len(C.fill_board(one, 10)), 3,
   "⛔ and a cap it cannot fill returns what exists, not padding")

print("\n11. 🔴 A RATED BOARD KEEPS STRICT CONFIDENCE ORDER (Sam's standing rule)")
# ⛔ Variety must never reshuffle a board that has something real to rank
# by. Round-robin applies ONLY where every row is unrated.
N2 = load("nfl")
eq(N2.RATES_OK, True, "the NFL board is rated")
rated_rows = [dict(mkrow("player_anytime_td", 145, conf=c)) for c in (91, 88, 85)] + \
             [dict(mkrow("player_receptions", -110, conf=c)) for c in (70, 68)]
rated_rows.sort(key=lambda r: -r["confidence"])
# the production path takes rows[:cap] when ANY row is rated
eq([r["confidence"] for r in rated_rows[:5]], [91, 88, 85, 70, 68],
   "🔴 confidence order is preserved, even though one market leads")


print("\n12. 🔴 END TO END: A COLLEGE BOARD THAT ACTUALLY CARRIES RATES,")
print("    AND THE GATE BITING ON THE SAME CARD")
tmp = tempfile.mkdtemp()
cwd = os.getcwd()
try:
    os.chdir(tmp)
    os.makedirs("data/ncaaf/latest", exist_ok=True)
    import gzip as _gz

    def cg(rec=0, rush=0, car=0):
        # ⚠️ NO snap field -- college has none, and that is the point.
        return {"rec": rec, "rec_yds": rec * 12, "rush_yds": rush,
                "car": car, "rec_td": 0, "rush_td": 0,
                "pass_yds": 0, "pass_td": 0, "team": "T", "game_id": "x"}

    props = []
    for line, mk in ((4.5, "player_receptions"), (2.5, "player_receptions")):
        props.append({"player": "Cee Bee", "market": mk, "line": line,
                      "sides": {"over": {"price": -110, "book": "fd",
                                         "n_books": 3, "link": "x"}}})
    props.append({"player": "Cee Bee", "market": "player_pass_tds",
                  "line": 1.5, "sides": {"over": {"price": -110,
                                                  "book": "fd", "n_books": 3,
                                                  "link": "x"}}})
    board = {"pulled_at": "2026-09-03T22:31:00Z", "n_games": 1,
             "books_seen": ["fd"],
             "games": [{"id": "g1", "away": "A", "home": "H",
                        "commence": "2026-09-06T17:00:00Z", "props": props}]}
    with _gz.open("data/ncaaf/latest/props.json.gz", "wt") as fh:
        json.dump(board, fh)
    # 10 games: 6 with catches, 4 appearing ONLY via a carry. ⛔ Those four
    # are the union denominator's whole contribution -- under the old
    # receiving-only denominator they would not exist.
    gs = [cg(rec=5) for _ in range(6)] + [cg(rec=0, car=3) for _ in range(4)]
    logs = {"season": 2025, "scope": "all FBS conferences",
            "players": {"1": {"name": "Cee Bee", "pos": "WR", "g": gs}}}
    with _gz.open("data/ncaaf/latest/players-2025.json.gz", "wt") as fh:
        json.dump(logs, fh)
    C = load("ncaaf")
    C.main()
    out = json.load(open("picks/fb-ncaaf-latest.json"))
    by = {(p["market"], p.get("line")): p for p in out["picks"]}

    r45 = by[("player_receptions", 4.5)]
    eq(r45["confidence_basis"], "RECORD",
       "🔴 receptions o4.5 CARRIES A RATE — this is the change")
    eq(r45["record"], "6 of 10",
       "⛔ 10 games, not 6 — the union denominator is what is counted")
    eq(r45["confidence"], round(100 * 6.5 / 11),
       "   Jeffreys-smoothed exactly as an MLB hitter row")

    r25 = by[("player_receptions", 2.5)]
    eq(r25["confidence_basis"], "MARKET",
       "🔴 receptions o2.5 is GATED on the SAME card, same player")
    eq("confidence" in r25, False, "   and carries no number at all")
    eq("quiet" in " ".join(r25["why"]), True, "   the row says why in English")

    ptd = by[("player_pass_tds", 1.5)]
    eq(ptd["confidence_basis"], "MARKET",
       "⛔ an unmeasured market is MARKET-only even with a full log")

    eq(out["denominator"], "every game he appears in (union denominator)",
       "the card states which denominator it used")
    eq(out["snap_floor"], None,
       "⛔ and does NOT advertise a snap floor college cannot have")
    eq(out["n_gated_by_measurement"], 2, "gated rows are counted separately")
finally:
    os.chdir(cwd)
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

print("\n13. 🔴 A SEASON TOO YOUNG TO RATE MUST NOT BE PICKED")
print("    `[measured 2026-09-04]` the live college run chose")
print("    players-2026.json.gz — 74 players, ONE game each — because a")
print("    week had been played, and MIN_GAMES then refused every rate.")
print("    ⛔ The board shipped 0 of 50 rows with a record and said nothing.")
tmp = tempfile.mkdtemp()
cwd = os.getcwd()
try:
    os.chdir(tmp)
    os.makedirs("data/ncaaf/latest", exist_ok=True)
    import gzip as _gz

    def wr(season, n_games, n_players=5):
        d = {"season": season, "players": {
            str(i): {"name": f"P{i}", "pos": "WR",
                     "g": [{"rec": 1} for _ in range(n_games)]}
            for i in range(n_players)}}
        with _gz.open(f"data/ncaaf/latest/players-{season}.json.gz", "wt") as fh:
            json.dump(d, fh)

    wr(2025, 10)
    wr(2026, 1)
    C = load("ncaaf")
    season, P = C.load_logs()
    eq(season, 2025, "🔴 falls back to the season that CAN answer the question")
    eq(len(P), 5, "   and it is the real log, not an empty one")

    # once the young season matures, it takes over -- no manual switch
    wr(2026, 8)
    C = load("ncaaf")
    season, _ = C.load_logs()
    eq(season, 2026, "✅ and it switches back on its own once the season is old enough")

    # ⛔ and if NOTHING is deep enough, it still returns the best available
    os.remove("data/ncaaf/latest/players-2025.json.gz")
    wr(2026, 2)
    C = load("ncaaf")
    season, _ = C.load_logs()
    eq(season, 2026, "⚠️ with nothing deep enough it uses the best it has")
finally:
    os.chdir(cwd)
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)


print("\n14. 🔴 THE ROW STATES THE PLAYER'S OWN AVERAGE BESIDE THE LINE")
print("    `[measured 2026-09-04 on the first rated college board]` the")
print("    number-two row was Alberto Mendoza, passing UNDER 204.5,")
print("    '8 of 8', 94% -- and his 2025 average was 35.8 yards a game.")
print("    The record is factually correct and tells you nothing about")
print("    this line. ⛔ The answer is MORE INFORMATION, not a filter.")
C = load("ncaaf")


def cg2(**kw):
    g = {"rec": 0, "rec_yds": 0, "rush_yds": 0, "car": 0,
         "rec_td": 0, "rush_td": 0, "pass_yds": 0, "pass_td": 0}
    g.update(kw)
    return g


# eight games at 15 rushing yards, against a line of 34.5 -> under 8 of 8
gs = [cg2(rush_yds=15, car=4) for _ in range(8)]
r = C.rate_for(gs, "player_rush_yds", 34.5, "under")
eq(len(r), 4, "rate_for now returns the mean it computed too")
eq(r[3], 15.0, "  and it is the mean over the SAME games as the rate")
eq((r[1], r[2]), (8, 8), "  record unchanged: 8 of 8")

why = C.build_why("KD", "player_rush_yds", 34.5, "under", 8, 8, 2025,
                  "rush yds", mean=r[3])
joined = " ".join(why)
ck("averaged" in joined and "15.0" in joined,
   "🔴 the average is stated on the row", "15.0 rush yds a game")
ck("34.5" in joined, "  next to the line it is being judged against")
ck("role has changed" in joined,
   "⛔ and a 2.3x gap says so plainly", "line/mean = 2.3")

# ⚠️ 2x IS A BRIGHT LINE AND IT IS PINNED, so it cannot drift to suit a board
w19 = " ".join(C.build_why("X", "player_rush_yds", 28.5, "under", 8, 8,
                           2025, "rush yds", mean=15.0))
ck("role has changed" not in w19,
   "   1.9x does NOT trip it -- the line is 2x, not 'looks far'")
w20 = " ".join(C.build_why("X", "player_rush_yds", 30.0, "under", 8, 8,
                           2025, "rush yds", mean=15.0))
ck("role has changed" in w20, "   exactly 2.0x DOES")
# the other direction too: a line far BELOW his record
wlow = " ".join(C.build_why("X", "player_rush_yds", 30.0, "over", 8, 8,
                            2025, "rush yds", mean=120.0))
ck("role has changed" in wlow, "   and 4x the other way trips it as well")

# ⛔ AND IT MUST NEVER REMOVE A ROW.
print("   ⛔ IT IS A SENTENCE, NOT A FILTER — the row still ships:")
tmp = tempfile.mkdtemp()
cwd = os.getcwd()
try:
    os.chdir(tmp)
    os.makedirs("data/ncaaf/latest", exist_ok=True)
    import gzip as _gz
    board = {"pulled_at": "2026-09-03T22:31:00Z", "n_games": 1,
             "books_seen": ["fd"],
             "games": [{"id": "g1", "away": "A", "home": "H",
                        "commence": "2026-09-06T17:00:00Z",
                        "props": [{"player": "KD", "market": "player_rush_yds",
                                   "line": 34.5, "sides": {"under": {
                                       "price": -115, "book": "fd",
                                       "n_books": 3, "link": "x"}}}]}]}
    with _gz.open("data/ncaaf/latest/props.json.gz", "wt") as fh:
        json.dump(board, fh)
    logs = {"season": 2025, "scope": "all FBS conferences",
            "players": {"1": {"name": "KD", "pos": "RB",
                              "g": [dict(g, team="T", game_id=str(i))
                                    for i, g in enumerate(gs)]}}}
    with _gz.open("data/ncaaf/latest/players-2025.json.gz", "wt") as fh:
        json.dump(logs, fh)
    C = load("ncaaf")
    C.main()
    out = json.load(open("picks/fb-ncaaf-latest.json"))
    eq(len(out["picks"]), 1, "   the stretched row is STILL on the board")
    eq(out["picks"][0]["own_mean"], 15.0, "   carrying its own mean")
    eq(out["picks"][0]["confidence_basis"], "RECORD", "   still a RECORD row")
    ck(any("role has changed" in w for w in out["picks"][0]["why"]),
       "   with the warning attached, not instead of the row")
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
print("✅ card_fb OK — the measured college gate bites, the snap floor bites, "
      "nothing claims MODEL")

print("\n15. 🔴 THE PROJECTION — Sam, 2026-09-04: \"thats what the model is")
print("    supposed to do... you predict what the outcome is which is")
print("    the projection.\" He was right, and the reason there was no")
print("    number was a misreading of our own findings: T46/T47/T50")
print("    losing to a player's own average is a LICENCE TO USE THE")
print("    AVERAGE, not a reason to show nothing. T56 then measured that")
print("    it is worth printing: +3.25 points over the constant predictor.")
import gzip as _gz2
_tmp = tempfile.mkdtemp()
_cwd = os.getcwd()
try:
    os.chdir(_tmp)
    os.makedirs("data/ncaaf/latest", exist_ok=True)

    def _cg(rush):
        return {"rec": 0, "rec_yds": 0, "rush_yds": rush, "car": 4,
                "rec_td": 0, "rush_td": 0, "pass_yds": 0, "pass_td": 0,
                "team": "T", "game_id": "x"}

    # ⚠️ TWO LINES ON ONE MARKET, so the same-number rule can be tested,
    # plus a receptions line the measured gate refuses.
    _props = [
        {"player": "Runner One", "market": "player_rush_yds", "line": 9.5,
         "sides": {"over": {"price": -140, "book": "fd", "n_books": 3,
                            "link": "x"}}},
        {"player": "Runner One", "market": "player_rush_yds", "line": 24.5,
         "sides": {"under": {"price": -180, "book": "fd", "n_books": 3,
                             "link": "x"}}},
        {"player": "Catcher One", "market": "player_receptions", "line": 2.5,
         "sides": {"over": {"price": -150, "book": "fd", "n_books": 3,
                            "link": "x"}}},
    ]
    with _gz2.open("data/ncaaf/latest/props.json.gz", "wt") as fh:
        json.dump({"pulled_at": "2026-09-03T22:31:00Z", "n_games": 1,
                   "books_seen": ["fd"],
                   "games": [{"id": "g1", "away": "A", "home": "H",
                              "commence": "2026-09-06T17:00:00Z",
                              "props": _props}]}, fh)
    _runs = [10, 20, 15, 12, 18, 14, 16, 15]            # mean exactly 15.0
    _catches = [{"rec": c, "rec_yds": c * 11, "rush_yds": 0, "car": 0,
                 "rec_td": 0, "rush_td": 0, "pass_yds": 0, "pass_td": 0,
                 "team": "T", "game_id": "x"} for c in [2, 3, 4, 2, 3, 5, 3, 4]]
    with _gz2.open("data/ncaaf/latest/players-2025.json.gz", "wt") as fh:
        json.dump({"season": 2025, "scope": "all FBS conferences",
                   "players": {"1": {"name": "Runner One", "pos": "RB",
                                     "g": [_cg(v) for v in _runs]},
                               "2": {"name": "Catcher One", "pos": "WR",
                                     "g": _catches}}}, fh)
    _C = load("ncaaf")
    _C.main()
    _doc = json.load(open("picks/fb-ncaaf-latest.json"))
finally:
    os.chdir(_cwd)
    shutil.rmtree(_tmp, ignore_errors=True)

_rows = _doc["picks"]
_p = [r for r in _rows if r.get("projection") is not None]
ck(bool(_p), "a rated row carries a projection", f"{len(_p)} of {len(_rows)}")
if _p:
    eq(_p[0]["projection_basis"], "DESCRIPTIVE",
       "  ⛔ DESCRIPTIVE, and rule 55 forbids anything else here")
    eq(_p[0]["projection_unit"], "rush yds",
       "  it carries the market's own unit")
    ck("not a forecast" in (_p[0].get("projection_note") or ""),
       "  and the note says plainly it is not a forecast")
ck(not any(r.get("projection_basis") == "MODEL" for r in _rows),
   "⛔ NOTHING on the board claims MODEL")

print("\n15b. ⛔ ONE NUMBER PER (PLAYER, MARKET), AT EVERY LINE")
print("     MLB learned this the hard way: 51 of 608 combos once carried")
print("     more than one number for the same stat.")
_vals = {r["projection"] for r in _rows
         if r["market"] == "player_rush_yds" and r.get("projection") is not None}
eq(len(_vals), 1, "   both lines report the SAME average")
eq(_vals, {15.0}, "   and it is his actual per-game mean")

print("\n15c. 🔴 THE MAP THE PLAYER PROPS TAB JOINS AGAINST")
_m = _doc.get("projections") or {}
ck(bool(_m), "the card publishes a projections map", f"{len(_m)} keys")
for _k, _v in list(_m.items())[:1]:
    eq(_k.count("|"), 3, "   keyed player|market|side|line")
    eq(_v["b"], "DESCRIPTIVE", "   every entry is DESCRIPTIVE")
_keys = {f"{r['player']}|{r['market']}|{r['side']}|{r['line']}"
         for r in _rows if r.get("projection") is not None}
ck(_keys <= set(_m), "   ⛔ every projected row is reachable from the map",
   str(sorted(_keys - set(_m))[:2]))

print("\n15d. ⛔ A GATED CELL GETS NO PROJECTION EITHER")
print("     A mean is a different statistic from a rate — but a cell we")
print("     have declared unmeasurable does not get a number by the back door.")
_g = [r for r in _rows if r["market"] == "player_receptions"]
ck(bool(_g), "   the gated row is on the board", f"{len(_g)}")
if _g:
    eq(_g[0].get("confidence_basis"), "MARKET", "   it carries no rate")
    ck(_g[0].get("projection") is None,
       "   🔴 and no projection either", str(_g[0].get("projection")))
    ck(not [k for k in _m if k.startswith("Catcher One|")],
       "   ⛔ and nothing for it in the map")
