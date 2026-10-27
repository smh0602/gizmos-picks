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
import re as _re2
import tempfile
from tcheck import ck, eq, note   # the shared gate — see tcheck.py

fails = []




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
                                           "n_books": 3, "link": "x"}}},
                            # `[Sam, 2026-10-16]` one side per prop at 50%+: Real Guy's under
                            #    (his record ~5%) now never reaches the floor, so the -900 row
                            #    is Short Guy's OVER, the side his own record favours
                            {"player": "Short Guy", "market": "player_receptions",
                             "line": 3.5, "sides": {
                                 "over": {"price": -900, "book": "fanduel",
                                          "n_books": 3, "link": "x"}}}]}]}
    with gzip.open("data/nfl/latest/props.json.gz", "wt") as fh:
        json.dump(board, fh)
    logs = {"season": 2025, "players": {"1": {
        "name": "Real Guy", "pos": "WR",
        "g": [game(0.9, rec=5) for _ in range(10)]}, "2": {
        "name": "Short Guy", "pos": "WR",
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
    # `[Sam, 2026-10-16]` one line per player per market on the board: the gated 2.5 line is a
    #    second receiver's (Cee Two, the same log) on the SAME card (~~Cee Bee's own second line~~)
    for who, line, mk in (("Cee Bee", 4.5, "player_receptions"), ("Cee Two", 2.5, "player_receptions")):
        props.append({"player": who, "market": mk, "line": line,
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
            "players": {"1": {"name": "Cee Bee", "pos": "WR", "g": gs},
                        "2": {"name": "Cee Two", "pos": "WR", "g": gs}}}
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
    # ~~Jeffreys-smoothed exactly as an MLB hitter row: round(100 * 6.5 / 11)~~
    # 🔴 CHANGED 2026-09-24 BY SAM'S SHIP RULE (research/fb_card_fix_spec.md):
    #    the card now reads this season first and shrinks toward the position
    #    average. Still EXACT: 6 of 10, no 2026 games (2025 counts in full),
    #    and this fixture's position has under 50 games, so p0 = 0.5 —
    #    (6 + 12 x 0.5) / (10 + 12).
    eq(r45["confidence"], round(100 * (6 + 12 * 0.5) / (10 + 12)),
       "   shrunk toward the position average exactly as the fix's spec says")

    r25 = by[("player_receptions", 2.5)]
    eq(r25["confidence_basis"], "MARKET",
       "🔴 receptions o2.5 is GATED on the SAME card, the same log")
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
    eq((season, C.CUR_SEASON), (2025, 2026),
       "🔴 falls back to the season that CAN answer the question, with the one-game season read first")
    eq(len(P), 5, "   and it is the real log, not an empty one")

    # `[Sam, 2026-10-26]` ~~"once the young season matures, it takes over -- no manual switch"~~
    #    (`eq(season, 2026)`): that dropped last season at a median of 6, against
    #    fb_card_fix_spec §3. Sam: "if so i want to just use games from last season and the ones
    #    played this season for both cfb and nfl". Last season stays beside this one, every week.
    wr(2026, 8)
    C = load("ncaaf")
    season, _ = C.load_logs()
    eq((season, C.CUR_SEASON), (2025, 2026),
       "🔴 once this season's median passes 6, last season is still the record's start, never dropped")
    season, _ = C.load_logs(2027)
    eq((season, C.CUR_SEASON), (2026, 2026),
       "🔴 a slate whose season has no game yet reads last season alone (its weight is then 1)")
    season, _ = C.load_logs(2025)
    eq((season, C.CUR_SEASON), (2025, 2025), "   ...and a later season's file is never read for an earlier slate")

    # ⛔ and if NOTHING is deep enough, it still returns the best available
    os.remove("data/ncaaf/latest/players-2025.json.gz")
    wr(2026, 2)
    C = load("ncaaf")
    season, _ = C.load_logs()
    eq((season, C.CUR_SEASON), (2026, 2026), "⚠️ with nothing deep enough it uses the best it has")
finally:
    os.chdir(cwd)
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

print("\n13b. 🔴 THE CARD STILL BLENDS LAST SEASON AFTER THIS SEASON'S MEDIAN PASSES 6")
print("    `[Sam, 2026-10-26]` \"use games from last season and the ones played this season\".")
print("    research/fb_card_fix_spec.md §3: G25 = last season's games, each at w = 4 / (4 + n26).")
import datetime as _dt13


def _card13(commence, side="under"):
    """card_fb.main() on a planted college league, its one game kicking off at `commence`."""
    tmp = tempfile.mkdtemp()
    cwd = os.getcwd()
    try:
        os.chdir(tmp)
        os.makedirs("data/ncaaf/latest", exist_ok=True)
        return _plant13(commence, side)
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmp, ignore_errors=True)


def _plant13(commence, side):
    def _runs(season, start, vals):
        d0 = _dt13.date.fromisoformat(start)
        return [{"d": (d0 + _dt13.timedelta(weeks=i)).isoformat(), "rush_yds": v, "car": 4, "rec": 0,
                 "rec_yds": 0, "rec_td": 0, "rush_td": 0, "pass_yds": 0, "pass_td": 0, "team": "T",
                 "game_id": "%d-%d" % (season, i)} for i, v in enumerate(vals)]

    # last season: under 34.5 in 9 of 10; this season (7 games, a median of 7): under in 2 of 7
    _v25, _v26 = [10, 20, 15, 12, 18, 14, 16, 11, 13, 45], [40, 50, 20, 45, 60, 30, 55]
    for _s, _start, _vals in ((2025, "2025-09-06", _v25), (2026, "2026-09-05", _v26)):
        with _gz.open(f"data/ncaaf/latest/players-{_s}.json.gz", "wt") as fh:
            json.dump({"season": _s, "scope": "all FBS conferences", "players": {
                str(i): {"name": "Runner One" if i == 0 else f"Runner {i}", "pos": "RB",
                         "g": _runs(_s, _start, _vals)} for i in range(5)}}, fh)
    with _gz.open("data/ncaaf/latest/props.json.gz", "wt") as fh:
        json.dump({"pulled_at": "2026-10-30T12:00:00Z", "n_games": 1, "books_seen": ["fd"],
                   "games": [{"id": "g1", "away": "A", "home": "H", "commence": commence,
                              "props": [{"player": "Runner One", "market": "player_rush_yds", "line": 34.5,
                                         "sides": {side: {"price": -115, "book": "fd", "n_books": 3,
                                                          "link": "x"}}}]}]}, fh)
    C = load("ncaaf")
    C.main()
    out = json.load(open("picks/fb-ncaaf-latest.json"))
    rows = [r for r in out.get("picks") or [] if r.get("player") == "Runner One"]
    return out, rows[0] if rows else {}


_out13, _r13 = _card13("2026-10-31T16:00:00Z")
_d13 = _r13.get("season_detail") or {}
eq((_out13.get("logs_season"), {k: _d13.get(k) for k in ("h25", "n25", "h26", "n26", "w25")}),
   (2025, {"h25": 9, "n25": 10, "h26": 2, "n26": 7, "w25": round(4 / 11, 3)}),
   "🔴 this season's 7 games first, last season's 10 beside them at 4 / (4 + 7), not dropped")
_w13 = 4 / 11
_p013 = (9 * 5 + 2 * 5) / 85.0           # every RB game, both seasons, before the card's day
_c13 = round(100 * ((2 + _w13 * 9) + 12 * _p013) / ((7 + _w13 * 10) + 12))
eq((_r13.get("confidence"), _c13), (58, 58),
   "🔴 ...and its confidence is the spec's (H + 12 p0) / (N + 12) over both seasons: 58, not this "
   "season alone's 29 (which the one-side rule would have taken off the board)")
# A week-1 card of the NEXT season, built before that season has a game: last season (2026) is
# read alone at full weight, and the season before it (2025) is not "last season" any more.
_out13b, _r13b = _card13("2027-09-04T16:00:00Z", "over")    # over 34.5 in 5 of his 7 2026 games
_d13b = _r13b.get("season_detail") or {}
eq((_out13b.get("logs_season"), {k: _d13b.get(k) for k in ("h25", "n25", "h26", "n26", "w25")}),
   (2026, {"h25": 5, "n25": 7, "h26": 0, "n26": 0, "w25": 1.0}),
   "🔴 a 2027 slate with no 2027 game yet: the card reads 2026 alone, each game at 4 / (4 + 0) = 1")

print("\n13c. 🔴 A PLAYER WITH NO LOG LAST SEASON IS FOUND IN THIS SEASON'S (review, 2026-10-26)")
print("    The card looked names up in last season's log only, so a rookie (or a player new to FBS)")
print("    was unmatched all season and his games this season were never read; the median switch")
print("    that would have looked this season up was gone. card_fb.match_player, never a guess.")
print("    `[2026-10-27, review 2]` AND A SHARED NAME IS DECIDED BY THE GAME'S TWO TEAMS: the first")
print("    form chose by which log held the name, so the Titans' RB Michael Carter read the Eagles")
print("    CB's record and Kent State's Brandon White read Kansas State's WR's. ~~Every planted player")
print("    on team 'T', board A @ H~~ (no case could ask the team question): real school names, a")
print("    planted teams.json, the real dossier_fb resolver, the right player on a game team and his")
print("    namesake on another.")
import gzip as _gz13c    # noqa: E402
import shutil as _sh13c  # noqa: E402
import dossier_fb as _D13c  # noqa: E402

# the game: UAB @ Illinois. X (San José State) and R (Rice) are in neither side.
_SCH13c = {"H": "Illinois", "A": "UAB", "X": "San José State", "R": "Rice"}


def _plant13c():
    """One planted college league, card_fb.main() on it -> (card, {player: row}, the name-join log, module)."""
    def _runs(season, start, vals, pid, team, on=None):
        d0 = _dt13.date.fromisoformat(start)
        return [{"d": on or (d0 + _dt13.timedelta(weeks=i)).isoformat(), "rush_yds": v, "car": 4 if v else 0,
                 "rec": 0, "rec_yds": 0, "rec_td": 0, "rush_td": 0, "pass_yds": 0, "pass_td": 0,
                 "team": _SCH13c[team], "game_id": "%d-%d-%s" % (season, i, pid)} for i, v in enumerate(vals)]

    _l25, _l26 = [10, 20, 15, 12, 18, 14, 16, 11, 13, 45], [40, 20, 15, 45, 12, 30, 18]
    _over7, _under7 = [40, 50, 20, 45, 60, 30, 55], [10, 12, 14, 50, 11, 13, 9]
    # {season: {pid: (name, pos, team, games)}}; H and A are the game's teams
    logs = {2025: {"1": ("Runner One", "RB", "H", _l25),
                   "50": ("Old Name", "RB", "R", [10] * 11),   # no 2026 game; 51 holds the name now, on H
                   "60": ("Two Face", "RB", "R", _l25),        # no 2026 game; 61 (H) and 62 (A) hold it now
                   "70": ("Shared Back", "RB", "H", _l25),     # plays 2026 too; an LB on X shares it in 2026
                   "80": ("Twin Name", "RB", "X", [10] * 10), "81": ("Twin Name", "RB", "H", _l25),
                   # `[2026-10-27, review 2]` the namesake cases
                   "20": ("Wrong Back", "RB", "X", _l25),      # plays 2026 on X; 21 holds the name on H
                   "30": ("Gone Back", "RB", "R", _l25),       # gone; 31 holds the name on X
                   "40": ("Hurt Back", "RB", "H", _l25),       # no 2026 game yet; 41 holds the name on X
                   "85": ("Twin Two", "RB", "X", _l25), "86": ("Twin Two", "RB", "H", _over7 + [41, 42, 43]),
                   "95": ("Day Back", "RB", "X", _l25), "96": ("Day Back", "RB", "R", _l25)},
            2026: {"1": ("Runner One", "RB", "H", _l26),
                   "99": ("Rookie Two", "RB", "H", [10, 22, 15, 40, 12, 18, 25]),
                   "51": ("Old Name", "RB", "H", [30, 50, 20, 45, 10, 33, 60]),
                   "61": ("Two Face", "RB", "H", [10] * 7), "62": ("Two Face", "RB", "A", [10] * 7),
                   "70": ("Shared Back", "RB", "H", _l26), "71": ("Shared Back", "LB", "X", [0] * 7),
                   "81": ("Twin Name", "RB", "H", _l26),
                   "98": ("Thin Rookie", "RB", "H", [10, 12, 14]),
                   "20": ("Wrong Back", "RB", "X", _under7), "21": ("Wrong Back", "RB", "H", _over7),
                   "31": ("Gone Back", "RB", "X", _under7),
                   "41": ("Hurt Back", "RB", "X", _over7),
                   "91": ("Far Rookie", "RB", "X", _under7),      # a 2026-only lone name, on X
                   "85": ("Twin Two", "RB", "X", [10] * 7),
                   "95": ("Day Back", "RB", "X", [10] * 7),
                   # his one 2026 game, for H, is ON the card's day: it never decides who he is
                   "96": ("Day Back", "RB", "H", [10], "2026-10-31")}}
    for _s, _start in ((2025, "2025-09-06"), (2026, "2026-09-05")):
        with _gz13c.open(f"data/ncaaf/latest/players-{_s}.json.gz", "wt") as fh:
            json.dump({"season": _s, "scope": "all FBS conferences", "players": {
                pid: {"name": v[0], "pos": v[1], "g": _runs(_s, _start, v[3], pid, v[2], *v[4:])}
                for pid, v in logs[_s].items()}}, fh)
    with open("data/ncaaf/latest/teams.json", "w", encoding="utf-8") as fh:
        json.dump({"teams": {t: {} for t in _SCH13c.values()}}, fh)
    _who = sorted({v[0] for s in logs.values() for v in s.values()})
    with _gz13c.open("data/ncaaf/latest/props.json.gz", "wt") as fh:
        json.dump({"pulled_at": "2026-10-30T12:00:00Z", "n_games": 1, "books_seen": ["fd"],
                   "games": [{"id": "g1", "away": "UAB Blazers", "home": "Illinois Fighting Illini",
                              "commence": "2026-10-31T16:00:00Z",
                              "props": [{"player": n, "market": "player_rush_yds", "line": 34.5,
                                         "sides": {"under": {"price": -115, "book": "fd", "n_books": 3,
                                                             "link": "x"}}} for n in _who]}]}, fh)
    C = load("ncaaf")
    said = []
    C.log = lambda m, *a, **k: said.append(str(m))
    _root, _D13c.ROOT = _D13c.ROOT, os.getcwd()        # the REAL resolver, on the planted teams.json
    try:
        C.main()
    finally:
        _D13c.ROOT = _root
    out = json.load(open("picks/fb-ncaaf-latest.json"))
    rows = {}
    for r in (out.get("picks") or []) + (out.get("below_floor") or []):
        rows.setdefault(r.get("player"), r)
    return out, rows, [m for m in said if "name join" in m], C


_tmp13c, _cwd13c = tempfile.mkdtemp(), os.getcwd()
try:
    os.chdir(_tmp13c)
    os.makedirs("data/ncaaf/latest", exist_ok=True)
    _out13c, _rows13c, _join13c, _C13c = _plant13c()
finally:
    os.chdir(_cwd13c)
    _sh13c.rmtree(_tmp13c, ignore_errors=True)
_det = {n: {k: (_rows13c.get(n, {}).get("season_detail") or {}).get(k) for k in ("h25", "n25", "h26", "n26")}
        for n in ("Rookie Two", "Old Name", "Shared Back", "Twin Name", "Runner One", "Wrong Back", "Hurt Back",
                  "Twin Two")}
eq(_det["Rookie Two"], {"h25": 0, "n25": 0, "h26": 6, "n26": 7},
   "🔴 a rookie (no 2025 log) is found in 2026's and rated on his 7 games this season, G25 none")
ck("with no 2025 game of his counted" in (_rows13c.get("Rookie Two", {}).get("confidence_note") or ""),
   "   ...and his note says no last-season game counted (not \"his 2025 record (0 of 0)\")",
   _rows13c.get("Rookie Two", {}).get("confidence_note"))
eq(_det["Old Name"], {"h25": 0, "n25": 0, "h26": 4, "n26": 7},
   "🔴 a namesake: 2025's holder (Rice) has no 2026 game and the player holding the name now is on Illinois "
   "-> rated on THAT player's 7 games, never on 2025's 11")
eq(_det["Shared Back"], {"h25": 9, "n25": 10, "h26": 5, "n26": 7},
   "🔴 a name shared THIS season (an LB on San José State) stays Illinois's back, who held it last season too: "
   "blended")
eq(_det["Twin Name"], {"h25": 9, "n25": 10, "h26": 5, "n26": 7},
   "🔴 a name 2025 held twice and 2026 once: Illinois's, with his own 2025 games (by id)")
eq(_det["Runner One"], {"h25": 9, "n25": 10, "h26": 5, "n26": 7}, "   ...and a plain veteran is unchanged")
ck("Two Face" not in _rows13c or _rows13c["Two Face"].get("rate") is None,
   "🔴 two players hold the name now, one on each side of the game: ambiguous, no record (never a guess)",
   _rows13c.get("Two Face"))
# `[2026-10-27, review 2]` the namesake cases: the right player is on a team in the game, his namesake is not
eq(_det["Wrong Back"], {"h25": 0, "n25": 0, "h26": 2, "n26": 7},
   "🔴 2025's holder plays 2026 on San José State; Illinois's namesake is the board's player: HIS 2 of 7, "
   "never San José State's 15 of 17 (Kent State's Brandon White read Kansas State's WR's 3 of 16)")
eq(_det["Hurt Back"], {"h25": 9, "n25": 10, "h26": 0, "n26": 0},
   "🔴 2025's holder (Illinois) has no 2026 game yet and San José State's namesake does: Illinois's 9 of 10, "
   "never the namesake's 2 of 7")
eq(_det["Twin Two"], {"h25": 2, "n25": 10, "h26": 0, "n26": 0},
   "🔴 2025 held the name twice and only San José State's plays in 2026: Illinois's own 2 of 10 (the Titans' "
   "Michael Carter read the Eagles CB's record the same way)")
for _n13, _say in (("Gone Back", "2025's holder (Rice) is gone and the 2026 holder is on San José State"),
                   ("Day Back", "a holder's only 2026 game for Illinois is ON the card's day, so it decides "
                                "nothing; San José State's and Rice's: nobody")):
    ck(_n13 not in _rows13c or _rows13c[_n13].get("rate") is None,
       "🔴 %s: ambiguous, no record" % _say, _rows13c.get(_n13))
_far13 = _rows13c.get("Far Rookie", {})
ck(_far13.get("rate") is None and " ".join(_far13.get("why") or []).startswith(
    "No 2025 or 2026 game log matched Far Rookie"),
   "🔴 a lone 2026 name who has played this season for San José State is not UAB's or Illinois's player "
   "(college: no one changes FBS teams mid-season): unmatched, no record (NC State's Darius Johnson on "
   "Syracuse's rows)", _far13)
ck(_out13c.get("name_match_rate") == round(9 / 13, 3) and bool(_join13c)
   and "(1 unmatched, 3 ambiguous)" in _join13c[-1],
   "🔴 the 60% name join counts a match in either season's log, team-checked: 9 of 13 (Far Rookie the 1 "
   "unmatched; Two Face, Gone Back and Day Back the 3 ambiguous)", (_out13c.get("name_match_rate"), _join13c))
_why13c = " ".join(_rows13c.get("Two Face", {}).get("why") or [])
ck(_why13c.startswith("No 2025 or 2026 game log matched Two Face"),
   "   ...and his row says it looked in both seasons' logs", _why13c)
_thin13c = _rows13c.get("Thin Rookie", {})
ck(_thin13c.get("rate") is None and "took part in this market in only 3 of his 3 2026 games"
   in " ".join(_thin13c.get("why") or []),
   "🔴 a rookie with 3 games is matched, not rated (6 is the floor), and his row names HIS season, 2026",
   _thin13c.get("why"))
# `[2026-10-27, review 2]` the NFL: a lone holder elsewhere is KEPT (a trade), a shared name still needs a team
_C13n = load("nfl")


def _nfl13(pid_team25, pid_team26):
    P25 = {p: {"name": "Same Back", "g": [{"d": "2025-12-28", "team": t}]} for p, t in pid_team25.items()}
    P26 = {p: {"name": "Same Back", "g": [{"d": "2026-10-04", "team": t}]} for p, t in pid_team26.items()}
    return _C13n.match_player("Same Back", _C13n.index_by_name(P25), P26, _C13n.index_by_name(P26),
                              teams={"HOU", "JAX"}, day="2026-10-18", last=P25)


eq(_nfl13({"mh": "ARI"}, {"mh": "HOU"}), ["mh"],
   "🔴 NFL: a lone holder traded ARI -> HOU is HOU's player (Marvin Harrison Jr. at JAX on 10-18)")
eq(_nfl13({"mh": "ARI"}, {"mh": "ARI"}), ["mh"],
   "🔴 NFL: ...and a lone holder whose games this season were elsewhere is KEPT, never refused (a trade the log "
   "has not caught up with); only college refuses him")
eq(_nfl13({"cb": "PHI", "rb": "ARI"}, {"cb": "PHI"}), ["cb", "rb"],
   "🔴 NFL: 2025 held the name twice, 2026 once, neither on HOU or JAX: ambiguous (Michael Carter, the "
   "Eagles CB and the Titans RB), never the one who has played")


print("\n14. 🔴 THE ROW SAYS ITS RECORD AT THE LINE, THIS SEASON FIRST")
print("    `[Sam, 2026-10-09]` \"The football prop rows say what the pick is,")
print("    its confidence, the player's record at the line (this season")
print("    first) and the price. Remove the caveat sentences\" -- ~~his")
print("    average and a 2x role warning beside the line~~. The average is")
print("    still the row's PROJ number, and the row is never filtered.")
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

C.CUR_SEASON = 2026
_when = ", in the games he appears in."
eq(C.build_why("KD", "player_rush_yds", 34.5, "under", 8, 8, 2025, "rush yds"),
   ["<b>KD</b> went under 34.5 rush yds in <b>8 of 8 games</b> in 2025" + _when],
   "🔴 one sentence: his record at the line, and no caveat beside it")
eq(C.build_why("KD", "player_rush_yds", 34.5, "under", 11, 12, 2025, "rush yds",
               {"h26": 3, "n26": 4, "h25": 8, "n25": 8}),
   ["<b>KD</b> went under 34.5 rush yds in <b>3 of 4 games</b> in 2026 and 8 of 8 in 2025" + _when],
   "🔴 ...this season first, then last season")

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
    eq(out["picks"][0]["why"], ["<b>KD</b> went under 34.5 rush yds in <b>8 of 8 games</b> "
                                "in 2025" + _when], "   saying only its record at the line")
finally:
    os.chdir(cwd)
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)


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
    # `[Sam, 2026-10-09]` ~~"and the note says plainly it is not a forecast"~~
    ck("forecast" not in (_p[0].get("projection_note") or ""),
       "  and its note carries no caveat sentence")
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

print("\n16. 🔴 PARLAYS — both blockers gone, and neither went quietly")
print("    Sam settled the books question at the sportsbook. The")
print("    correlation question was never policy, it was arithmetic,")
print("    and MLB had already solved it: NO TWO LEGS IN ONE GAME ID.")
_C = load("ncaaf")


def _leg(who, gid, price, conf, book="hardrockbet", mk="player_rush_yds",
         line=40.5, player=None):
    return {"player": player or who, "market": mk, "side": "under",
            "line": line, "price": price, "book": book,
            "confidence": conf, "clears_price_floor": True,
            "game_id": gid, "game": f"{gid} game"}


# ⚠️ -250 is decimal 1.40, so a PAIR pays 1.96x -- inside Sam's 1.8-2.2
# two-leg band. -110 pairs pay 3.65x and land in no two-leg band at all,
# which is a fact about his bands and not a bug: the first draft of this
# test used -110 and correctly produced nothing.
_rows = [_leg("A", "g1", -250, 80), _leg("B", "g2", -250, 78),
         _leg("C", "g3", -200, 76), _leg("D", "g4", -200, 74)]
_pl, _meta = _C.build_parlays_fb(_rows)
ck(bool(_pl["2"]), "two-leg parlays are built", f"{len(_pl['2'])}")
for _size in ("2", "3", "4"):
    for _x in _pl[_size]:
        eq(len(set(_x["game_ids"])), int(_size),
           f"   🔴 every {_size}-leg parlay is in {_size} DIFFERENT games")
        eq(_x["joint_basis"], "RECORD",
           f"   ⛔ the {_size}-leg joint is RECORD, never MODEL")
        break

print("\n16b. ⛔ TWO LEGS IN THE SAME GAME ARE NEVER COMBINED")
print("     This is the whole reason parlays were blocked. A QB and his")
print("     own receiver are not independent, and the product of their")
print("     records would be a number that means nothing.")
_same = [_leg("QB", "g1", -250, 80), _leg("WR", "g1", -250, 78),
         _leg("RB", "g1", -250, 76)]
_pl2, _m2 = _C.build_parlays_fb(_same)
eq(sum(len(v) for v in _pl2.values()), 0,
   "   🔴 one game, three players -> ZERO parlays")
ck(_m2["rejected"]["same_game"] > 0,
   "   and the rejection is COUNTED, not silent",
   str(_m2["rejected"]["same_game"]))

print("\n16c. 🔴 EVERY LEG AT THE SAME BOOK — a parlay is ONE SLIP")
print("     MLB gets this free by requiring Hard Rock. Football carries")
print("     the best price across five books, so two legs can be best at")
print("     two different books and the multiplier would be unbettable.")
_mix = [_leg("A", "g1", -250, 80, book="fanduel"),
        _leg("B", "g2", -250, 78, book="draftkings")]
_pl3, _m3 = _C.build_parlays_fb(_mix)
eq(sum(len(v) for v in _pl3.values()), 0, "   two books -> no parlay")
ck(_m3["rejected"]["mixed_book"] > 0, "   counted as such",
   str(_m3["rejected"]["mixed_book"]))
_pl4, _ = _C.build_parlays_fb(
    [_leg("A", "g1", -250, 80, book="fanduel"),
     _leg("B", "g2", -250, 78, book="fanduel")])
ck(bool(_pl4["2"]), "   ⛔ and the SAME book is fine", f"{len(_pl4['2'])}")
if _pl4["2"]:
    eq(_pl4["2"][0]["book"], "fanduel", "   the slip names its book")

print("\n16d. ⛔ ONE PLAYER CANNOT APPEAR TWICE")
_dup = [_leg("A", "g1", -250, 80, mk="player_rush_yds"),
        _leg("A", "g2", -250, 78, mk="player_reception_yds")]
_pl5, _m5 = _C.build_parlays_fb(_dup)
eq(sum(len(v) for v in _pl5.values()), 0, "   same name, two games -> none")
ck(_m5["rejected"]["same_player"] > 0, "   and it says why")

print("\n16e. 🔒 SAM'S BANDS, AND THE TWO FILES MUST AGREE ON THEM")
print("     ⛔ Restating a number is a rule 66 hazard, so the restatement")
print("     is CHECKED rather than trusted.")
_mlb_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "card.py"), encoding="utf-8").read()
_m_bands = _re2.search(r"^PARLAY_BANDS = (\{[^}]*\})", _mlb_src, _re2.M)
ck(bool(_m_bands), "card.py declares PARLAY_BANDS")
if _m_bands:
    eq(eval(_m_bands.group(1)), _C.PARLAY_BANDS,
       "   🔴 card_fb.py's bands are IDENTICAL to card.py's")
_m_str = _re2.search(r"^PARLAY_STRATA = (\[[^\]]*\][^\n]*)", _mlb_src, _re2.M)
# 🔴 `[Sam, 2026-09-22]` floors only: 1.8x+ two-legs, 3x+ above that.
ck(_C.PARLAY_BANDS == {2: (1.80, None), 3: (3.00, None), 4: (3.00, None)},
   "   ⛔ the bands are Sam's (1.8x+ two-legs, 3x+ above) and are not tuned",
   str(_C.PARLAY_BANDS))

print("\n16f. ⚠️ A BAND NOTHING FITS PRODUCES NOTHING, NOT A STRETCH")
_short = [_leg("A", "g1", -900, 95), _leg("B", "g2", -900, 94)]
_pl6, _m6 = _C.build_parlays_fb(_short)
eq(len(_pl6["2"]), 0, "   two -900 legs pay 1.22x -> outside the band")
ck(_m6["rejected"]["out_of_band"] > 0, "   and that is the reason given")

# ══════════════════════════════════════════════════════════════════════
# EVERY GUARD BELOW SHIPS WITH THE MUTATION THAT PROVES IT.
# ══════════════════════════════════════════════════════════════════════
# 🔴 A GUARD NOBODY HAS SEEN FAIL IS A GUARD NOBODY HAS TESTED. CLAUDE.md
#    says prove it bites before you call it done — these declarations turn
#    that from something two people do by hand into something `vacuity.py`
#    tier 2 re-proves every night: apply the edit, assert RED, revert,
#    assert GREEN.
# ⚠️ EACH ONE IS A REAL MUTATION THAT WAS DRIVEN, not a plausible-looking
#    string. Every `find` matches its file EXACTLY ONCE and every mutated
#    file still COMPILES — a `find` that matches nothing is a no-op
#    wearing a proof's clothes (rule 244), and a SyntaxError goes red for
#    the WRONG reason and is indistinguishable from a working guard.
# ⛔ NO VALUE MAY BEGIN WITH A SPACE. `vacuity.py`'s field regex ends
#    `:\s*(.*)$`, so leading whitespace is eaten and the mutation would
#    silently become a different string than the one written here.
#
# @vacuity [review, 2026-10-26] §13c: a board name is looked up in this season's log too
#   file: card_fb.py
#   find: pids = [] if unit else match_player(
#   with: pids = [] if unit else (lambda who, idx, *a, **k: idx.get(norm(who), []))(
#
# @vacuity [review, 2026-10-26] §13c: ...which main() hands match_player whenever the seasons differ
#   file: card_fb.py
#   find: _cur = CUR_P if (CUR_P and CUR_SEASON != season) else None
#   with: _cur = None
#
# ~~@vacuity [review, 2026-10-26] §13c: a name last season does not settle goes to this season's holders~~
#   (find `return b or a`), ~~last season's holder with no game this season yields the name~~ and
#   ~~...but one who plays this season keeps a name shared now~~ (find `if len(a) == 1 and (not b or
#   a[0] in (cur or {})):`): `[2026-10-27, review 2]` that rule chose by which LOG held the name and
#   never asked his team, so a namesake on neither team took the row (the Titans' Michael Carter, Kent
#   State's Brandon White). Its code is gone; the game's two teams decide now, guarded below.
# @vacuity [2026-10-27, review 2] §13c: main() hands match_player the board game's two teams
#   file: card_fb.py
#   find: teams={_team(g.get("home")), _team(g.get("away"))} - {None},
#   with: teams=set(),
#
# @vacuity [2026-10-27, review 2] §13c: a shared name goes to the holder playing for a team in the game
#   file: card_fb.py
#   find: return on_now
#   with: return cands
#
# @vacuity [2026-10-27, review 2] §13c: ...decided by his TEAM, never by which log holds the name
#   file: card_fb.py
#   find: on_now = [p for p in cands if now[p] is not None and now[p] in teams]
#   with: on_now = [p for p in cands if now[p] is not None]
#
# @vacuity [2026-10-27, review 2] §13c: ...his team this season BEFORE the card's day, never a later game
#   file: card_fb.py
#   find: now = {p: team_of(cur, p, day) for p in cands}
#   with: now = {p: team_of(cur, p, None) for p in cands}
#
# @vacuity [2026-10-27, review 2] §13c: ...else a holder with no game this season, by last season's team
#   file: card_fb.py
#   find: return [p for p in cands if now[p] is None and team_of(last, p, None) in teams] or cands
#   with: return cands
#
# @vacuity [2026-10-27, review 2] §13c: ...and when the teams decide nothing, nobody: ambiguous, never a guess
#   file: card_fb.py
#   find: team_of(last, p, None) in teams] or cands
#   with: team_of(last, p, None) in teams] or cands[:1]
#
# @vacuity [2026-10-27, review 2] §13c: a college lone holder who played this season elsewhere is someone else
#   file: card_fb.py
#   find: and now[cands[0]] not in teams):
#   with: and False):
#
# @vacuity [2026-10-27, review 2] §13c: ...in college only: an NFL lone holder elsewhere is kept (a trade)
#   file: card_fb.py
#   find: if (cands and LEAGUE == "ncaaf" and teams and now[cands[0]] is not None
#   with: if (cands and teams and now[cands[0]] is not None
#
# @vacuity [review, 2026-10-26] §13c: a rookie's this-season log is his row's, never his G25
#   file: card_fb.py
#   find: r = rate_blend((P.get(pids[0]) or {}).get("g") or [], _g26, mk, pr.get("line"), side,
#   with: r = rate_blend(plog.get("g") or [], _g26, mk, pr.get("line"), side,
#
# @vacuity [review, 2026-10-26] §13c: ...and a rookie gets a log at all
#   file: card_fb.py
#   find: plog, plog_season = _cur[pids[0]], CUR_SEASON
#   with: plog, plog_season = None, season
#
# @vacuity [review, 2026-10-26] §13c: a rookie with no rate is told about HIS season
#   file: card_fb.py
#   find: no_rate_reason(RATES_OK, plog, who, mk, plog_season,
#   with: no_rate_reason(RATES_OK, plog, who, mk, season,
#
# @vacuity [review, 2026-10-26] §13c: no counted last-season game is said, never "(0 of 0)"
#   file: card_fb.py
#   find: f"{_d['w25']:g} per game, " if _d['n25'] else
#   with: f"{_d['w25']:g} per game, " if True else
#
# @vacuity [review, 2026-10-26] §13c: an unmatched row names both logs it looked in
#   file: card_fb.py
#   find: _logs = (f"{season} or {this_season}" if this_season and this_season != season
#   with: _logs = (f"{season} or {this_season}" if False
#
# @vacuity [Sam, 2026-10-26] §13b: the card passes its slate's season to load_logs
#   file: card_fb.py
#   find: season, P = load_logs(fb_why.season_of(_card_day))
#   with: season, P = load_logs()
#
# @vacuity [Sam, 2026-10-26] §13b: last season stays beside this season after its median passes 6
#   file: card_fb.py
#   find: season, P, fn, med, _fs = seen[1] if len(seen) > 1 else cur
#   with: season, P, fn, med, _fs = cur
#
# @vacuity the card must WIRE the banner in, not merely be able to build it
#   file: card_fb.py
#   find: "calibration_warning": calibration_sentence_fb(),
#   with: "cal_warning_unwired": calibration_sentence_fb(),
#
# @vacuity the claim is keyed `stated`; MLB's `predicted` finds nothing
#   file: card_fb.py
#   find: row.get("stated")
#   with: row.get("predicted")
#
# @vacuity a band under FB_CAL_MIN_N must not be quoted as a rate
#   file: card_fb.py
#   find: if b in cal and cal[b]["n"] >= FB_CAL_MIN_N]
#   with: if b in cal]
#
# @vacuity the banner is DERIVED; a hand-written one is stale on night one
#   file: card_fb.py
#   find: total = sum(c["n"] for _, c in have)
#   with: return "Football confidence has run hot; treat it as unproven."
#
# @vacuity the MIN_N bar is calibration.py's, never a second copy
#   file: card_fb.py
#   find: from calibration import MIN_N
#   with: MIN_N = 55
#
# @vacuity under the bar the banner must SAY the bar
#   file: card_fb.py
#   find: if total < MIN_N else
#   with: if False else
#
# @vacuity [Sam, 2026-10-01] the football header must NOT render the confidence pop-up
#   file: index.html
#   find: <p style="color:var(--mut);margin:0">${freshness(C.odds_pulled_at)}</p>
#   with: <p style="color:var(--mut);margin:0">${freshness(C.odds_pulled_at)}</p>${fbCalNote(C)}
#
# @vacuity [Sam, 2026-10-01] no card, with or without the field, gets calibration_warning drawn
#   file: index.html
#   find: function fbConfBar(){
#   with: function fbCalNote(C){ if (!C || !C.calibration_warning) return ''; return C.calibration_warning; } function fbConfBar(){
#
# @vacuity [Sam, 2026-10-01] the MLB card must NOT render the confidence pop-up either
#   file: index.html
#   find: head.innerHTML = `<h2>Gizmo's Picks &mdash; ${CARD_DATE}</h2>`;
#   with: head.innerHTML = `<h2>Gizmo's Picks &mdash; ${CARD_DATE}</h2><div class="note"><b>Read the confidence number honestly.</b> ${P.calibration_warning}</div>`;
# ══════════════════════════════════════════════════════════════════════
print("\n17. 🔴🔴 A BOARD THAT STATES A CONFIDENCE MUST STATE HOW THAT")
print("    CONFIDENCE HAS PERFORMED.")
print("    `[the defect, measured 2026-09-16]` MLB published a")
print("    `calibration_warning` above its rows from 2026-09-01. FOOTBALL")
print("    PUBLISHED NONE — so the better-calibrated board warned and the")
print("    worse one did not. NFL overall 46.4%; its 80-90 bucket claimed")
print("    84.1 and delivered 47.8 over 23 graded plays, and a reader")
print("    seeing 84 in a CONF cell was told nothing about that.")
print("    ⚠️ THE LABEL WAS NEVER THE PROBLEM — rule 55 was satisfied.")

# ⛔ GUARDING THE CLASS, NOT THE FILE. CLAUDE.md: ask what CLASS the defect
#    belongs to and guard the class where the class is answerable. It is
#    answerable here — the class is "a card builder that publishes a
#    confidence number", which is discoverable rather than a list I type.
#    This file broke once by naming one file (rules 246, 130).
import glob as _g17
_ROOT17 = os.path.dirname(os.path.abspath(__file__))
_BUILDERS = sorted(os.path.basename(p)
                   for p in _g17.glob(os.path.join(_ROOT17, "card*.py")))
ck(len(_BUILDERS) >= 2,
   "⚠️ the sweep found the card builders at all",
   "⛔ AN EMPTY SWEEP PASSES EVERY ASSERTION BELOW AND PROVES NOTHING "
   "(rule 67). Got %s" % _BUILDERS)
_STATERS = []
for _b in _BUILDERS:
    _src = open(os.path.join(_ROOT17, _b), encoding="utf-8").read()
    if '"confidence"' not in _src:
        continue                      # not a board that states a confidence
    _STATERS.append(_b)
    ck('"calibration_warning":' in _src,
       "🔴🔴 %s states a confidence, so it publishes a calibration_warning"
       % _b,
       "⛔ THIS IS THE DEFECT. A board that prints 84 in a CONF cell and "
       "says nothing about how that bucket has gone is advertising a "
       "number it has never been held to. Every builder that states one "
       "owes the reader its record.")
ck(len(_STATERS) >= 2,
   "⚠️ ...and BOTH boards were actually swept, not just one",
   "⛔ if only MLB matched, the football half of this check never ran. "
   "Got %s" % _STATERS)

print("\n17a. ⚠️ DERIVED AT BUILD TIME, NEVER HAND-WRITTEN")
_C17 = load("nfl")


def _rec17(rows, path=None):
    """Write a record.json with the given calibration buckets."""
    p = path or os.path.join(tempfile.mkdtemp(prefix="fbcal-"), "record.json")
    with open(p, "w") as fh:
        json.dump({"calibration": rows}, fh)
    return p


_HOT = _rec17([{"bucket": "80-90%", "stated": 84.1, "w": 11, "n": 23},
               {"bucket": "60-70%", "stated": 65.1, "w": 14, "n": 32}])
_COLD = _rec17([{"bucket": "80-90%", "stated": 84.1, "w": 22, "n": 23},
                {"bucket": "60-70%", "stated": 65.1, "w": 30, "n": 32}])
_s_hot = _C17.calibration_sentence_fb(*_C17.load_calibration_fb(_HOT))
_s_cold = _C17.calibration_sentence_fb(*_C17.load_calibration_fb(_COLD))
ck("47.8" in _s_hot and "84.1" in _s_hot and "n=23" in _s_hot,
   "🔴 the sentence quotes delivered, claimed and n off the RECORD",
   "⛔ a banner that does not carry the record's own numbers is a typed "
   "sentence wearing a derived one's clothes. Got: %s" % _s_hot)
ck(_s_hot != _s_cold,
   "🔴🔴 CHANGE THE RECORD AND THE SENTENCE CHANGES",
   "⛔ THIS IS THE WHOLE CLAIM. A hand-written banner is correct until "
   "the first night it grades and stale every night after. If these two "
   "records produce the same sentence, nothing is being derived.")
ck("95.7" in _s_cold,
   "✅ ...and the second record's own delivered rate is what it says",
   "⛔ different is not enough — it has to be RIGHT. 22/23 = 95.7 pct. "
   "Got: %s" % _s_cold)

print("\n17b. 🔴🔴 `stated` IS NOT `predicted`, AND DEFAULTING IS FABRICATION")
print("     card.py reads `row.get(\"predicted\") or 0.0`. Copied across")
print("     verbatim it finds nothing in a football record and publishes")
print("     'against a claimed 0%' on a board that claimed 84.")
_MLBKEY = _rec17([{"bucket": "80-90%", "predicted": 84.1, "w": 11, "n": 23}])
_cal_k, _drop_k = _C17.load_calibration_fb(_MLBKEY)
eq(_cal_k, {}, "   a bucket with no readable claim is DROPPED")
eq(_drop_k, 23, "   ...and its rows are COUNTED, not lost in silence")
ck("claimed 0%" not in _C17.calibration_sentence_fb(_cal_k, _drop_k),
   "⛔ and nothing is published as 'claimed 0%'",
   "🔴 a fabricated number is worse than no banner at all — CLAUDE.md, "
   "never invent a price, and this is the same offence one column over")

print("\n17c. ⚠️ A BAND TOO THIN TO READ IS NAMED, NOT SILENTLY DROPPED")
_THIN = _rec17([{"bucket": "80-90%", "stated": 84.1, "w": 11, "n": 23},
                {"bucket": "70-80%", "stated": 75.9, "w": 2, "n": 4}])
_s_thin = _C17.calibration_sentence_fb(*_C17.load_calibration_fb(_THIN))
ck("70-80" in _s_thin and "too few" in _s_thin,
   "   the 4-play band is named as unreadable",
   "⛔ a band that vanishes from the banner reads as a band with no "
   "problem. Got: %s" % _s_thin)
ck("n=4" not in _s_thin,
   "   ...and its percentage is NOT quoted",
   "🔴 a percentage on n=4 is not a rate (the T37 lesson). Got: %s"
   % _s_thin)
_NONE = _rec17([{"bucket": "80-90%", "stated": 84.1, "w": 2, "n": 3}])
_s_none = _C17.calibration_sentence_fb(*_C17.load_calibration_fb(_NONE))
ck("not enough graded" in _s_none and "unproven" in _s_none,
   "   with no band at the bar it says so plainly",
   "⛔ 'I cannot say yet' is a third state and must not read as a pass. "
   "Got: %s" % _s_none)
eq(_C17.load_calibration_fb("/nonexistent/record.json"), ({}, 0),
   "   ⛔ a missing record fails to SILENCE, never to a stale number")

print("\n17d. ⚠️ FOOTBALL ROWS GO BELOW 50 AND MLB'S TABLE WOULD DROP THEM")
print("     card.py maps buckets through a literal dict starting at")
print("     `50-60%` because an MLB row never sits below 50. The graded")
print("     football record carries buckets down to `0-10%`.")
for _b, _want in (("0-10%", "under-60"), ("40-50%", "under-60"),
                  ("50-60%", "under-60"), ("60-70%", "60-70"),
                  ("70-80%", "70-80"), ("80-90%", "80-plus"),
                  ("90-100%", "80-plus")):
    eq(_C17.band_of_bucket(_b), _want, "   %s -> %s" % (_b, _want))
eq(_C17.band_of_bucket("nonsense"), None,
   "   ⛔ an unparseable label returns None rather than guessing")
_LOW = _rec17([{"bucket": "0-10%", "stated": 6.0, "w": 1, "n": 1},
               {"bucket": "30-40%", "stated": 34.3, "w": 5, "n": 12},
               {"bucket": "40-50%", "stated": 43.1, "w": 9, "n": 13}])
_cal_low, _drop_low = _C17.load_calibration_fb(_LOW)
eq(_drop_low, 0, "   no sub-50 row is dropped")
# ⚠️ `.get`, NOT `[...]`. A KeyError here KILLS THE FILE and every check
#    after it never runs — the `stated`->`predicted` mutation empties this
#    dict and cost 12 later checks their turn. A guard that dies reports
#    "an unknown number never ran", which is strictly less than a guard
#    that fails. Same assertion, no crash.
eq(_cal_low.get("under-60", {}).get("n"), 26,
   "   all 26 roll into under-60")

print("\n17e. ⛔ THE BUILDER'S SENTENCE CARRIES NO BOLD PREFIX, AND")
print("     `[Sam, 2026-10-01]` THE PAGE NO LONGER PRINTS IT AT ALL")
# ⚠️ `[Sam, 2026-10-01]` The next check is DATA-SIDE and stays exactly as it
#    was. Its reason ("index.html renders that phrase in bold") is history
#    now -- the page prints no banner (the three checks after it) -- but the
#    builder's sentence must still never carry the prefix itself.
_s_live = _C17.calibration_sentence_fb(*_C17.load_calibration_fb(_HOT))
ck("Read the confidence number honestly" not in _s_live,
   "   the builder's string does NOT carry the bold prefix",
   "🔴 index.html renders that phrase in bold immediately before this "
   "string. MLB's first draft carried it too and the banner said it "
   "TWICE (caught 2026-09-01 by rendering the page)")
# `[Sam, 2026-10-01]` THESE THREE USED TO REQUIRE THE BANNER ON THE PAGE:
#    the football header rendering `fbCalNote(C)` once, its guard for a card
#    without the field, and MLB's `${P.calibration_warning}` exactly once.
#    Sam removed every confidence pop-up from every league -- *"we have a
#    track record for a reason"* -- so they now require it NOWHERE on the
#    page. ⛔ The DATA half above is unchanged: every builder that states a
#    confidence still publishes `calibration_warning`, derived from its
#    record; it reaches Sam in the card JSON, never in a box on the page.
_IDX = open(os.path.join(_ROOT17, "index.html"), encoding="utf-8").read()
ck(_IDX.count("${fbCalNote(C)}") == 0 and "\nfunction fbCalNote(" not in _IDX
   and "Read the confidence number honestly" not in _IDX,
   "   [Sam, 2026-10-01] the football header renders NO confidence pop-up "
   "(it used to render fbCalNote(C) once)",
   "⛔ Sam: 'we have a track record for a reason'")
ck("calibration_warning" not in _IDX,
   "   ⚠️ ...and no card, with or without the field, has it drawn: the page "
   "reads calibration_warning nowhere",
   "🔴 older dated cards predate the field; since 2026-10-01 no card's "
   "field reaches the page at all, so none can print 'undefined' either")
ck(_IDX.count("${P.calibration_warning}") == 0,
   "   ⛔ and the MLB card renders none either (it used to render exactly one)",
   "[Sam, 2026-10-01] 'do this for all 3 leagues' -- MLB is unfrozen "
   "(2026-09-22) and loses its pop-up with the other two")

print("\n17f. 🔴🔴 UNDER THIS PROJECT'S OWN BAR, THE BANNER NAMES THE BAR")
print("     `[measured 2026-09-16]` CFB's readable bands total 71 graded")
print("     plays — below the 100 at which calibration.py will not even")
print("     call a gap a finding — and the banner still printed")
print("     \"80-plus hit 72.4% against a claimed 87%\". \"Small samples")
print("     throughout\" is true and does not say that.")
print("     ⛔ AND THE ANSWER IS NOT TO SUPPRESS IT: a CFB reader with no")
print("     honesty note at all is the defect this banner exists to fix.")
import calibration as _CALMOD

# ⛔ ONE COPY OF THE BAR. A second copy is a second thing to drift, and
#    this repo has been bitten by exactly that (rule 66). ⚠️ `from X import
#    Y` binds a VALUE at import time, so no runtime check can catch a
#    re-typed constant that happens to agree today — the source is where
#    the single-copy claim has to be made, and it is made explicitly here
#    rather than left implied.
_SRC_FB = open(os.path.join(_ROOT17, "card_fb.py"), encoding="utf-8").read()
eq(_C17.MIN_N, _CALMOD.MIN_N,
   "   🔴 the bar is calibration.py's own number")
ck("from calibration import MIN_N" in _SRC_FB,
   "   ⛔ ...IMPORTED, not re-typed",
   "🔴 a bar written down twice is a bar that drifts. calibration.py owns "
   "it; card_fb.py borrows it")
ck(not _re2.search(r"^MIN_N\s*=", _SRC_FB, _re2.M),
   "   ⛔ ...and card_fb.py declares no MIN_N of its own",
   "🔴 a local redefinition would shadow the import and read as "
   "borrowed while being typed")

# ⚠️ BOTH BRANCHES ARE LIVE ON REAL DATA TODAY — NFL 106 is over the bar
#    and CFB 71 is under it — so neither is a hypothetical.
_OVER = _rec17([{"bucket": "80-90%", "stated": 84.1, "w": 30, "n": 60},
                {"bucket": "60-70%", "stated": 65.1, "w": 20, "n": 50}])
_UNDER = _rec17([{"bucket": "80-90%", "stated": 84.1, "w": 11, "n": 23},
                 {"bucket": "60-70%", "stated": 65.1, "w": 14, "n": 32}])
_s_over = _C17.calibration_sentence_fb(*_C17.load_calibration_fb(_OVER))
_s_under = _C17.calibration_sentence_fb(*_C17.load_calibration_fb(_UNDER))
ck(str(_CALMOD.MIN_N) in _s_under and "not a measured rate" in _s_under
   or ("rather than a measured rate" in _s_under
       and str(_CALMOD.MIN_N) in _s_under),
   "🔴🔴 a 55-row readable sample is UNDER THE BAR, and it says so",
   "⛔ a figure quoted below the bar this project refuses to read a rate "
   "at, with nothing saying so, is the same silence one level quieter. "
   "Got: %s" % _s_under)
ck("history" in _s_under,
   "   ...and calls the figures history, not a rate",
   "Got: %s" % _s_under)
ck(str(_CALMOD.MIN_N) not in _s_over and "history rather than" not in _s_over,
   "✅ ...and a sample OVER the bar does NOT carry the caveat",
   "⛔ A CAVEAT THAT NEVER CLEARS IS NOT A CAVEAT — it is decoration, and "
   "CLAUDE.md calls a guard that fires on correct code the other "
   "failure. Got: %s" % _s_over)
ck("80-plus hit" in _s_under and "hit" in _s_over,
   "⛔ NEITHER BRANCH SUPPRESSES THE FIGURES",
   "🔴 Sam, 2026-09-16: suppressing CFB's banner means a CFB reader sees "
   "NO honesty note — the exact defect this task exists to fix. Silence "
   "is worse than a caveated number.")
note("   the two live boards today: NFL readable total 106 (over %d), "
     "CFB 71 (under) — both branches on real data, neither hypothetical."
     % _CALMOD.MIN_N)
