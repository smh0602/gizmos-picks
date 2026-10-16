#!/usr/bin/env python3
"""test_one_per_player.py — the Gizmo's Picks board holds one row per player per market.

`[Sam, 2026-10-16]` "i dont want to see multiple of the same players in the gizmos picks, for
example i see marvin harrison jr with 3 different receiving props on gizmos picks. lets keep it
to one per player unless your using a different prop, for example, having marvin harrisions
receiving prop and reception prop is good but both receiving yards prop is a no go." That day the
NFL board held Marvin Harrison Jr. twice and Tanner McKee three times at one market, college six
such repeats, MLB two. Planted boards and rows; ⛔ reads nothing live.

# @vacuity 🔴 the football board takes one row per player per market
#   file: card_fb.py
#   find:     _brows = one_per_player_market(rows)
#   with:     _brows = rows
#
# @vacuity 🔴 ...keeping his first (best) row of each market
#   file: card_fb.py
#   find:         if k not in seen:
#   with:         if True:
#
# @vacuity 🔴 the MLB board never seats two lines of one player's market
#   file: card.py
#   find:         on_pm.add(_playermarket(x))
#   with:         pass
#
# @vacuity 🔴 the MLB guard names a repeat
#   file: card.py
#   find:             if k in held:
#   with:             if False:
#
# @vacuity 🔴 verify_card.py runs the guard on the card main() built
#   file: verify_card.py
#   find: _rep = C.player_market_repeats(doc.get('picks') or [])
#   with: _rep = []
"""
import datetime
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from tcheck import ck, eq, section, shown  # noqa: E402

UTC = datetime.timezone.utc
YDS, REC = "player_reception_yds", "player_receptions"

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE FOOTBALL BOARD (the real card_fb.main): ONE LINE PER PLAYER PER MARKET")
# ══════════════════════════════════════════════════════════════════════
_n = datetime.datetime.now(UTC)
_K = (_n + datetime.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
_P = (_n - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")


def over(px=-110):
    return {"over": {"price": px, "book": "fanduel", "n_books": 3}}


def put(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with (gzip.open(path, "wt", encoding="utf-8") if path.endswith(".gz") else open(path, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


_T = tempfile.mkdtemp(prefix="oneplayer-")
try:
    _L = os.path.join(_T, "data", "ncaaf", "latest")
    # Multi Guy: three receiving-yards lines and one receptions line; Other Guy: one line
    put(os.path.join(_L, "props.json.gz"), {"pulled_at": _P, "games": [
        {"id": "ev1", "away": "Away U", "home": "Home U", "commence": _K, "props": [
            {"player": "Multi Guy", "market": YDS, "line": ln, "sides": over()} for ln in (40.5, 45.5, 50.5)]
            + [{"player": "Multi Guy", "market": REC, "line": 3.5, "sides": over()},
               {"player": "Other Guy", "market": YDS, "line": 40.5, "sides": over()}]}]})
    put(os.path.join(_L, "players-2025.json.gz"), {"season": 2025, "players": {
        str(i): {"name": w, "pos": "WR", "team": "T",
                 "g": [{"d": "2025-09-%02d" % (j + 6), "rec": 5, "rec_yds": 60} for j in range(8)]}
        for i, w in enumerate(("Multi Guy", "Other Guy"))}})
    _q = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, %r); import card_fb; card_fb.main()" % ROOT],
                        cwd=_T, capture_output=True, text=True, encoding="utf-8", timeout=900,
                        env=dict(os.environ, PYTHONUTF8="1", LEAGUE="ncaaf"))
    try:
        CARD = json.load(open(os.path.join(_T, "picks", "fb-ncaaf-latest.json"), encoding="utf-8"))
    except (OSError, ValueError):
        CARD = {}
        print(shown(_q.stdout[-1500:]), shown(_q.stderr[-1500:]))
finally:
    shutil.rmtree(_T, ignore_errors=True)
_board = [(r.get("player"), r.get("market"), r.get("line")) for r in CARD.get("picks") or []]
ck(sum(1 for p, m, _l in _board if p == "Multi Guy") >= 2 and all(r.get("confidence") is not None
                                                                   for r in CARD.get("picks") or []),
   "⚠️ the planted card was built with rated rows, Multi Guy among them", str(_board))
eq(sorted((p, m) for p, m, _l in _board),
   sorted([("Multi Guy", REC), ("Multi Guy", YDS), ("Other Guy", YDS)]),
   "🔴 Multi Guy shows ONE receiving-yards line (of three) and his receptions line; Other Guy his one line")
os.environ["LEAGUE"] = "ncaaf"
import card_fb as CF  # noqa: E402
_rows = [{"game_id": "g", "player": "A", "market": YDS, "line": ln, "confidence": c}
         for ln, c in ((45.5, 74), (40.5, 71), (50.5, 66))] + [{"game_id": "g", "player": "A", "market": REC,
                                                               "line": 3.5, "confidence": 60}]
eq([(r["market"], r["line"]) for r in CF.one_per_player_market(_rows)], [(YDS, 45.5), (REC, 3.5)],
   "🔴 ...keeping his FIRST row of each market in the board's order (its highest confidence), and his other market")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE MLB BOARD NEVER SEATS TWO LINES OF ONE PLAYER'S MARKET")
# ══════════════════════════════════════════════════════════════════════
os.environ["LEAGUE"] = "mlb"
import card as C  # noqa: E402


def row(kind, pid, market, line, conf, side="over"):
    return {"kind": kind, "pid": pid, "player": "P%d" % pid, "market": market, "line": line, "side": side,
            "confidence": conf, "edge": 5.0, "break_even": 52.4, "clears_price_floor": True, "game_id": "g1"}


_hit = [row("hitter", 7, "batter_hits_runs_rbis", 1.5, 70), row("hitter", 7, "batter_hits_runs_rbis", 2.5, 65),
        row("hitter", 7, "batter_hits", 0.5, 68), row("hitter", 8, "batter_hits_runs_rbis", 1.5, 66)]
_pit = [row("pitcher", 1, "outs", 15.5, 72), row("pitcher", 1, "outs", 16.5, 69), row("pitcher", 1, "strikeouts", 5.5, 60)]
_b, _acct = C.select_board(_pit, _hit)
eq(sorted((x["pid"], x["market"], x["line"]) for x in _b),
   sorted([(7, "batter_hits_runs_rbis", 1.5), (7, "batter_hits", 0.5), (8, "batter_hits_runs_rbis", 1.5),
           (1, "outs", 15.5), (1, "strikeouts", 5.5)]),
   "🔴 hitter 7's H+R+RBI at 1.5 only (never also 2.5), his hits too; the pitcher's outs at 15.5 only "
   "(never also 16.5), his strikeouts too")
eq([C.player_market_repeats(_hit), C.player_market_repeats(_b)],
   [[("g1", 7, "batter_hits_runs_rbis")], []],
   "🔴 the guard names a repeated player-market, and finds none on the built board")
_v = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
ck("_rep = C.player_market_repeats(doc.get('picks') or [])" in _v and "not _rep" in _v
   and _v.index("doc = C.main(dry=True)") < _v.index("_rep = C.player_market_repeats("),
   "🔴 verify_card.py runs the guard on the card main() built, before every MLB card is committed")
