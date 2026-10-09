#!/usr/bin/env python3
"""THE FOOTBALL TABS ARE ABOUT THE NEXT GAMES, WITH ALL THREE BOOKS. `[Sam, 2026-10-09]`

Planted trees and pinned clocks only; nothing here reads the live data tree.
  1. NFL props are bought for the next slate once it is within 72 hours, and only it.
  2. A us2 refresh keeps FanDuel and DraftKings from the earlier pull, with their
     minute, and keeps a game it lacks; a started slate leaves the board.
  3. A finished slate is never the current card, and the next slate is.
  4. The name check counts players only: a team defense never counts.

# @vacuity 🔴 the pull buys ONE slate: Friday prices Sunday, never Monday too
#   file: freshness.py
#   find:     return [k for k in later if _et_day(k) == _et_day(later[0])] if later else []
#   with:     return later
#
# @vacuity 🔴 ...the next UNSTARTED slate: Thursday's played game is not it
#   file: freshness.py
#   find:     later = sorted(k for k in kickoffs if k > now)
#   with:     later = sorted(kickoffs)
#
# @vacuity 🔴 ...once it is within 72 hours, not before
#   file: collect.py
#   find:             if ks and ks[0] > now() + timedelta(hours=_fresh.FB_NEXT_SLATE_H[LEAGUE]):
#   with:             if False:
#
# @vacuity 🔴 a us2 refresh keeps FanDuel and DraftKings from the earlier pull
#   file: collect.py
#   find:         for bat, bk in (v for (e2, _b), v in latest_by.items() if e2 == eid):
#   with:         for bat, bk in (v for (e2, _b), v in latest_by.items() if e2 == eid and v[0] == newest.get("pulled_at")):
#
# @vacuity 🔴 ...and keeps a game the refresh lacks
#   file: collect.py
#   find:         if slate is None or _ko(ev) is None or _fresh._et_day(_ko(ev)) != slate:
#   with:         if slate is None or _ko(ev) is None or _fresh._et_day(_ko(ev)) != slate or _at != newest.get("pulled_at"):
#
# @vacuity 🔴 the card's day is the earliest UNSTARTED game's
#   file: card_fb.py
#   find:         return et(min([t for t in ts if t > now] or ts)).strftime("%Y-%m-%d")
#   with:         return et(min(ts)).strftime("%Y-%m-%d")
#
# @vacuity 🔴 ...and an empty board's card is the next slate with lines, not today
#   file: card_fb.py
#   find:     return (gls and next_line_slate(gls, now)) or et(now).strftime("%Y-%m-%d")
#   with:     return et(now).strftime("%Y-%m-%d")
#
# @vacuity 🔴 a board and card holding only started games are rebuilt by the next pass
#   file: freshness.py
#   find:         if (lambda ks: bool(ks) and max(ks) <= now)(_kickoffs_in(path, keys))}
#   with:         if False}
#
# @vacuity 🔴 ...only when there is a next game to move to
#   file: freshness.py
#   find:     if lg not in FB_TIMES or not any(k > now for k in _kickoffs_in(f"{data}/latest/board.json", ("games",))):
#   with:     if lg not in FB_TIMES:
#
# @vacuity 🔴 the name check counts players only, never a team defense
#   file: card_fb.py
#   find:             unit = bool(TEAM_UNIT.search(who))
#   with:             unit = False
"""
import atexit
import datetime
import gzip
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
import collect as C  # noqa: E402
import card_fb as CF  # noqa: E402
import freshness as F  # noqa: E402
from tcheck import eq, section  # noqa: E402

UTC = datetime.timezone.utc
T = lambda s: datetime.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)  # noqa: E731
TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])

# The week of 2026-10-08 (ET): Thursday TB @ DAL 8:15pm, Sunday's 13, Monday's 1.
TNF = "2026-10-09T00:15:00Z"
SUN = ["2026-10-11T17:00:00Z"] * 10 + ["2026-10-11T20:25:00Z"] * 2 + ["2026-10-12T00:20:00Z"]
MNF = "2026-10-13T00:15:00Z"
WEEK = [{"id": "g%d" % i, "home_team": "H%d" % i, "away_team": "A%d" % i, "commence_time": c}
        for i, c in enumerate([TNF] + SUN + [MNF])]


def mktree():
    t = tempfile.mkdtemp(prefix="nextslate-")
    TREES.append(t)
    return t


def put(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with (gzip.open(path, "wt") if path.endswith(".gz") else open(path, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


def priced(at, events=WEEK):
    """Drive the real NFL props pull with a stubbed API. -> how many games it priced."""
    paths, old = [], (C.LEAGUE, C.odds_get, C.now, C.write, C.props_is_fresh, C.SPORT)
    try:
        C.LEAGUE, C.SPORT, C.now = "nfl", "x", (lambda: T(at))
        C.props_is_fresh, C.write = (lambda kind: False), (lambda *a, **k: None)
        C.odds_get = lambda path, params=None: ((events, 0, 19250) if path.endswith("/events")
                                                else (paths.append(path) or ({"bookmakers": []}, 6, 19000)))
        C.collect_props("player")
    finally:
        C.LEAGUE, C.odds_get, C.now, C.write, C.props_is_fresh, C.SPORT = old
    return len(paths)


section("1. 🔴 NFL PROPS: THE NEXT SLATE, EVERY DAY ONCE IT IS WITHIN 72 HOURS")
eq(priced("2026-10-06T11:00Z"), 1, "🔴 Tuesday 7am ET buys Thursday's game (61 hours out)")
eq(priced("2026-10-09T11:00Z"), 13, "🔴 Friday 7am ET buys Sunday's 13 games, not Thursday's played one "
   "and not Monday's")
eq(priced("2026-10-11T21:00Z"), 1, "🔴 Sunday 5pm ET buys only the slate's game still to start")
eq(priced("2026-10-05T11:00Z", WEEK[:1]), 0, "⛔ Monday 7am ET: Thursday is 85 hours out, nothing bought")

section("2. 🔴 A REFRESH NEVER REMOVES A BOOK OR A GAME; A STARTED SLATE LEAVES")


def side(book_prices, who="Plant Receiver"):
    return [{"key": b, "markets": [{"key": "player_reception_yds", "outcomes": [
        {"description": who, "name": "Over", "point": 40.5, "price": p}]}]} for b, p in book_prices]


_t = mktree()
put(os.path.join(_t, "2026-10-08", "props-player", "2050.json.gz"), {
    "pulled_at": "2026-10-08T20:50:00Z", "regions": "us2", "events": [dict(WEEK[0], bookmakers=side(
        [("hardrockbet", -110)]))]})
put(os.path.join(_t, "2026-10-09", "props-player", "1425.json.gz"), {
    "pulled_at": "2026-10-09T14:25:00Z", "regions": "us,us2", "events": [
        dict(WEEK[1], bookmakers=side([("hardrockbet", -110), ("fanduel", -105), ("draftkings", -120)])),
        dict(WEEK[11], bookmakers=side([("hardrockbet", -115), ("fanduel", -110)]))]})
put(os.path.join(_t, "2026-10-09", "props-player", "1835.json.gz"), {
    "pulled_at": "2026-10-09T18:35:00Z", "regions": "us2", "events": [
        dict(WEEK[1], bookmakers=side([("hardrockbet", -125)]))]})
_old = (C.DATA, C.now, C.write)
_w = {}
try:
    C.DATA, C.now = _t, (lambda: T("2026-10-09T19:00Z"))
    C.write = lambda path, obj, compress=False: _w.update(obj=obj)
    C.collect_props_board_fb("nfl")
finally:
    C.DATA, C.now, C.write = _old
_B = _w.get("obj") or {}
_g = {g["id"]: g for g in _B.get("games") or []}
_o = (((_g.get("g1") or {}).get("props") or [{}])[0].get("sides") or {}).get("over") or {}
eq(sorted(_g), ["g1", "g11"], "🔴 the board is Sunday's slate: both games, the one the refresh lacked "
   "included, and Thursday's played game gone")
eq(_o.get("books"), {"hardrockbet": {"price": -125, "pulled_at": "2026-10-09T18:35Z"},
                     "fanduel": {"price": -105, "pulled_at": "2026-10-09T14:25Z"},
                     "draftkings": {"price": -120, "pulled_at": "2026-10-09T14:25Z"}},
   "🔴 each book keeps its latest price, with the minute it was pulled")
eq((_o.get("price"), _o.get("book"), _o.get("n_books")), (-105, "fanduel", 3),
   "🔴 ...and the side's price is the best of the three")

section("3. 🔴 A FINISHED SLATE IS NEVER THE CURRENT CARD, AND THE NEXT SLATE IS")
_fri = T("2026-10-09T03:00Z")              # Thursday 11pm ET: TB @ DAL has started
eq(CF.slate_date({"games": [{"commence": TNF}, {"commence": SUN[0]}]}, _fri), "2026-10-11",
   "🔴 a board holding Thursday's game and Sunday's: the card is Sunday's")
_t2 = mktree()
put(os.path.join(_t2, "2026-10-08", "gamelines", "2000.json.gz"),
    {"games": [{"commence": TNF}, {"commence": SUN[0]}, {"commence": MNF}]})
_old = CF.DATA
try:
    CF.DATA = _t2
    eq(CF.slate_date({"games": []}, _fri), "2026-10-11",
       "🔴 an empty board (Sunday not priced yet): the card is the next slate with lines, not today")
finally:
    CF.DATA = _old
_d, _p = _t2.replace("\\", "/") + "/data/nfl", _t2.replace("\\", "/") + "/picks"   # as collect passes it
put(os.path.join(_d, "latest", "board.json"), {"games": [{"commence": TNF}, {"commence": SUN[0]}]})
put(os.path.join(_d, "latest", "props.json.gz"), {"games": [{"commence": TNF}]})
put(os.path.join(_p, "fb-nfl-latest.json"), {"picks": [{"commence": TNF}], "game_lines": []})
eq(F.slate_moves(_d, _p, _fri), {"props-board", "card-fb"},
   "🔴 a board and card holding only started games are rebuilt by the next pass (free modes)")
put(os.path.join(_d, "latest", "props.json.gz"), {"games": [{"commence": SUN[0]}]})
eq(F.slate_moves(_d, _p, _fri), {"card-fb"}, "   ...and a board already on Sunday is left alone")
put(os.path.join(_d, "latest", "board.json"), {"games": [{"commence": TNF}]})
eq(F.slate_moves(_d, _p, _fri), set(), "⛔ ...and with no next game to move to, nothing is planned")

section("4. 🔴 THE NAME CHECK COUNTS PLAYERS ONLY `[Sam, 2026-10-09]`")
# Three logged receivers and four team defenses (FanDuel and DraftKings list
# "<Team> D/ST" and "<Team> Defense" under Anytime TD), on the real clock.
_k = (datetime.datetime.now(UTC) + datetime.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
_who = ["Rec One", "Rec Two", "Rec Three"]
_units = ["A Defense", "A D/ST", "H Defense", "H D/ST"]
_t3 = mktree()
put(os.path.join(_t3, "data", "nfl", "latest", "props.json.gz"), {"pulled_at": "2026-10-09T14:25:00Z", "games": [{
    "id": "g1", "away": "A", "home": "H", "commence": _k, "props":
        [{"player": w, "market": "player_receptions", "line": 3.5,
          "sides": {"over": {"price": -110, "book": "fanduel", "n_books": 3}}} for w in _who]
        + [{"player": w, "market": "player_anytime_td", "line": None,
            "sides": {"yes": {"price": 300, "book": "draftkings", "n_books": 2}}} for w in _units]}]})
put(os.path.join(_t3, "data", "nfl", "latest", "players-2025.json.gz"), {"season": 2025, "players": {
    str(i): {"name": w, "pos": "WR", "g": [{"d": "2025-09-%02d" % (j + 7), "snap_pct": 0.9, "rec": 5}
                                           for j in range(10)]} for i, w in enumerate(_who)}})
_cwd = os.getcwd()
try:
    os.chdir(_t3)
    CF.main()
    _card = json.load(open(os.path.join("picks", "fb-nfl-latest.json"), encoding="utf-8"))
finally:
    os.chdir(_cwd)
_rows = {r["player"]: r for r in _card.get("picks") or []}
eq((_card.get("name_match_rate"), [(_rows.get(w) or {}).get("confidence_basis") for w in _who]),
   (1.0, ["RECORD"] * 3), "🔴 the three players are rated: four team defenses never count in the check "
   "(3 of 7 would be 43%, under the 60% bar, and strip every rate)")
eq([(w in _rows, (_rows.get(w) or {}).get("confidence")) for w in _units], [(True, None)] * 4,
   "   ...and each defense row stays on the card, with no rate")
