#!/usr/bin/env python3
"""MLB: EVERY NUMBER THE CARD SHOWS IS THE MODEL'S OWN. `[Sam, 2026-10-11]`

"only show confidence score on each pick that the model picks, BASED ON THE
MODELS CONFIDENCE SCORE NOT THE SPORTSBOOKS." A price only says which bet is
priced, its break-even and whether it pays. Planted rows and trees only;
nothing here reads the live data tree.
  1. Changing every price (each kept on its side of -400 and +400) leaves every
     pitcher and hitter row's confidence unchanged, and a thin board seats the
     same rows in the same order.
  2. ...and every MLB game-line row's confidence and order.
  3. The Track Record keeps C2's pitcher bands as they were graded and opens C1's.

# @vacuity 🔴 a pitcher row's number takes no price
#   file: mlb_pitcher_cal.py
#   find: SHIPPED = "C1"
#   with: SHIPPED = "C2"
#
# @vacuity 🔴 a thin board's top-up is ranked by the model's number, never by edge
#   file: card.py
#   find: rest.sort(key=by_conf)
#   with: rest.sort(key=lambda x: -x["edge"])
#
# @vacuity 🔴 two game lines at one confidence are never ordered by a price
#   file: card.py
#   find: str(r.get("game_id")), r.get("market") or ""))
#   with: -(r.get("edge") or 0)))
#
# @vacuity 🔴 the record keeps each method's pitcher bands apart
#   file: collect.py
#   find: "confidence_method": p.get("confidence_method"),
#   with: "confidence_method": None,
"""
import atexit
import datetime
import gzip
import json
import os
import random
import shutil
import sys
import tempfile

from tcheck import ck, eq, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "mlb"
import card  # noqa: E402
import mlb_pitcher_cal as pcal  # noqa: E402

TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])
TODAY = "2026-10-12"
GAME = {"home": "HOU", "away": "SEA", "id": "g1", "commence": "2026-10-12T20:10:00Z"}


def tree():
    t = tempfile.mkdtemp(prefix="mlbown-")
    TREES.append(t)
    return t


def american(be):
    """The American price whose break-even is `be` (0-1)."""
    return int(round(-100 * be / (1 - be))) if be >= 0.5 else int(round(100 * (1 - be) / be))


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 A PRICE NEVER MOVES A PITCHER OR HITTER ROW'S NUMBER")
# ══════════════════════════════════════════════════════════════════════
# The walk-forward correction, fitted on a planted record: 30 days, the card
# running about 15 points hot.
_t = tree()
_rnd, _days = random.Random(11), {}
for i in range(30):
    _rows = []
    for mk in pcal.MARKETS:
        for _ in range(12):
            be = _rnd.uniform(0.45, 0.75)
            _rows.append({"kind": "pitcher", "market": mk, "won": _rnd.random() < be - 0.03,
                          "blend": round(100 * min(0.97, be + 0.12), 1), "implied": round(100 * be, 1)})
    _days[(datetime.date(2026, 9, 1) + datetime.timedelta(days=i)).isoformat()] = _rows
os.makedirs(os.path.join(_t, "data", "latest"))
with gzip.open(os.path.join(_t, "data", "latest", "record-detail.json.gz"), "wt") as fh:
    json.dump({"days": _days}, fh)
card.PCAL.clear()
card.PCAL.update(pcal.mappings(TODAY, _t))
ck(all(card.PCAL.get(mk) for mk in pcal.MARKETS), "⚠️ both markets have a correction to apply",
   "⛔ without one every row prints its blend and the check below asks nothing")


def pitcher(pid, k):
    starts = [{"d": "2026-09-%02d" % (2 + 5 * j), "gs": True, "k": k + (j % 3) - 1, "outs": 17 + (j % 3),
               "np": 92 + j, "o": "TEX"} for j in range(6)]
    return {"name": "P%d" % pid, "team": "HOU", "era": "3.40", "whip": 1.15, "throws": "R", "g": starts}


PITCHERS = {101: pitcher(101, 5), 102: pitcher(102, 7), 103: pitcher(103, 9)}


def plays(prices):
    out = []
    for (pid, p), px in zip(sorted(PITCHERS.items()), prices):
        prop = {"market": "pitcher_strikeouts", "line": 5.5, "side": "over", "price": px,
                "book": "draftkings", "pid": pid}
        out.append(card.build_play(prop, p, PITCHERS, 8.0, 8.0, 6, GAME, TODAY))
    return out


def hitters(prices):
    """30 hitters, every one below its price (a thin board), records 30-70%."""
    out = []
    for i, px in enumerate(prices):
        prop = {"market": "batter_hits", "line": 0.5, "side": "over", "price": px, "book": "fanduel",
                "player": "H%02d" % i, "pid": 200 + i, "team": "HOU",
                "evidence": {"season": "%d/60" % (18 + i)}}
        out.append(card.hitter_play(prop, GAME, {}, {"HOU": 70}, None, TODAY))
    return out


_rate = [100.0 * (18 + i + 0.5) / 61 for i in range(30)]
_P0 = [american(min(0.8, (r + 2 + i % 5) / 100)) for i, r in enumerate(_rate)]
_P1 = [american(min(0.8, (r + 8 - i % 5) / 100)) for i, r in enumerate(_rate)]
_pa, _pb = plays([-120, 105, -150]), plays([-150, 135, -115])
_ha, _hb = hitters(_P0), hitters(_P1)
ck(all(isinstance(r, dict) for r in _pa + _pb + _ha + _hb), "⚠️ every planted row is built",
   str([r for r in _pa + _ha if not isinstance(r, dict)][:3]))
eq([r.get("confidence_method") for r in _pa], ["C1"] * 3, "   the pitcher rows are corrected (C1)")
eq([r["confidence"] for r in _pb], [r["confidence"] for r in _pa],
   "🔴 every pitcher row prints the same number at different prices")
eq([r["confidence"] for r in _hb], [r["confidence"] for r in _ha],
   "🔴 ...and every hitter row")
_ba, _bb = card.select_board([], _ha)[0], card.select_board([], _hb)[0]
ck(len(_ba) == card.BOARD_MIN < len(_ha) and all(r["edge"] < 0 for r in _ha + _hb),
   "⚠️ a thin board: no row beats its price and 25 of the 30 are topped up", str(len(_ba)))
eq([r["player"] for r in _bb], [r["player"] for r in _ba],
   "🔴 the topped-up board holds the same rows in the same order at both prices")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 ...AND NEVER MOVES OR REORDERS A GAME-LINE ROW")
# ══════════════════════════════════════════════════════════════════════
def gl_rows(prices):
    games, board = [], []
    for i, (team, px) in enumerate(zip(("NYY", "BOS"), prices)):
        c = "2026-10-12T%02d:05:00Z" % (17 + 3 * i)
        games.append({"home": team, "away": "TOR%d" % i, "commence": c, "home_id": i, "away_id": 9 + i,
                      "starters": {"home": {"id": 1, "name": "A"}, "away": {"id": 2, "name": "B"}},
                      "card": {"moneyline": {"home": 58.0, "away": 42.0}},
                      "expected_runs": {"home": 4.6, "away": 3.9}})
        board.append({"home": team, "away": "TOR%d" % i, "commence": c, "id": "b%d" % i,
                      "best_ml": {team: {"price": px, "book": "fanduel"}}})
    rows = card.game_line_rows({"games": games}, {"games": board}, card.et_date(games[0]["commence"]))
    return card.order_game_lines(rows)


_ga, _gb = gl_rows([-105, -140]), gl_rows([-145, -110])
ck(len(_ga) == len(_gb) == 2, "⚠️ both planted games are listed at both prices", str(len(_ga)))
eq([(r["player"], r["confidence_value"]) for r in _gb], [(r["player"], r["confidence_value"]) for r in _ga],
   "🔴 two games at one confidence keep their numbers and their order when the prices swap")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE TRACK RECORD KEEPS C2'S PITCHER BANDS AND OPENS C1'S")
# ══════════════════════════════════════════════════════════════════════
import collect as CO  # noqa: E402
_t2, _cwd = tree(), os.getcwd()
for day, method, conf, ks in (("2026-09-10", "C2", 65, (7, 7, 3, 3)), ("2026-10-12", "C1", 52, (7, 3, 3, 3))):
    os.makedirs(os.path.join(_t2, "data", day, "results"))
    os.makedirs(os.path.join(_t2, "picks"), exist_ok=True)
    picks = [{"pid": 900 + j, "market": "strikeouts", "side": "over", "line": 5.5, "kind": "pitcher",
              "pitcher": "P%d" % j, "blend": 66.0, "confidence": conf, "confidence_method": method}
             for j in range(4)]
    json.dump({"date": day, "kind": "gizmos-card", "picks": picks},
              open(os.path.join(_t2, "picks", day + ".json"), "w"))
    with gzip.open(os.path.join(_t2, "data", day, "results", "final.json.gz"), "wt") as fh:
        json.dump({"slate_date": day, "n_games": 1, "n_final": 1, "games": [
            {"state": "Final", "batters": [],
             "pitchers": [{"id": 900 + j, "started": True, "k": k, "outs": 18} for j, k in enumerate(ks)]}]}, fh)
try:
    os.makedirs(os.path.join(_t2, "data", "latest"), exist_ok=True)
    os.chdir(_t2)
    CO.collect_record()
    _rec = json.load(open(os.path.join("data", "latest", "record.json")))
finally:
    os.chdir(_cwd)
eq(_rec.get("calibration_printed_by_method"),
   {"C1": [{"bucket": "50-60%", "predicted": 52.0, "w": 1, "n": 4, "pct": 25.0}],
    "C2": [{"bucket": "60-70%", "predicted": 65.0, "w": 2, "n": 4, "pct": 50.0}]},
   "🔴 C2's band is exactly its own graded rows, and C1 opens its own")
