#!/usr/bin/env python3
"""THE MLB GAME MODEL BUILDS ON ITS OWN SCHEDULE. `[Sam, 2026-10-06]`

MEASURED 2026-10-06: #235 and #236 merged at 17:09Z; at 20:40Z
`data/latest/mlb-game-model.json` did not exist, the card had no `game_lines`
and `winners.json` was empty, though MLB converge passes ran 19:02Z-20:33Z:
the model was built only inside the card, which has one deadline a day.
✅ Its own contract row (`game-model`: missing, and the Odds deadlines, on game
days only), built free by converge, then MLB's winners.json; the card is not
built and a started game keeps its frozen winner. Planted trees, pinned clock.

# @vacuity 🔴 on a game day with no model file the contract owes it
#   file: freshness.py
#   find:         ("game-model", ("file", f"{latest}/mlb-game-model.json"), ODDS, False,
#   with:         ("game-model-x", ("file", f"{latest}/mlb-game-model.json"), ODDS, False,
#
# @vacuity 🔴 ...and converge builds it without building the card
#   file: collect.py
#   find:             _gm.build(_gm.next_slate(root=".", now=now()), root=".")
#   with:             import card as _card; _card.main()
#
# @vacuity 🔴 on a no-games day it is not owed
#   file: freshness.py
#   find:     if no_games_day(due_date(ODDS, now), data):
#   with:     if False:
#
# @vacuity 🔴 the winners file is rebuilt after the model file
#   file: collect.py
#   find:             build_winners(root=".", when=now())
#   with:             pass
#
# @vacuity 🔴 a started game's winner is unchanged by a rebuild
#   file: winners.py
#   find:     rows = [fz.get(r["game_id"], r) if r["commence"] <= now else r for r in rows]
#   with:     rows = rows
#
# @vacuity 🔴 the build makes no paid call
#   file: collect.py
#   find:             _gm.build(_gm.next_slate(root=".", now=now()), root=".")
#   with:             collect_gamelines(); _gm.build(_gm.next_slate(root=".", now=now()), root=".")
"""
import datetime
import gzip
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "mlb")
import card as CA  # noqa: E402
import collect as C  # noqa: E402
import freshness as F  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

UTC = datetime.timezone.utc
T = datetime.datetime(2026, 10, 6, 18, 0, tzinfo=UTC)      # 14:00 ET, after the 07:00 Odds deadline
DAY = "2026-10-06"


def put(rel, doc):
    os.makedirs(os.path.dirname(rel), exist_ok=True)
    with gzip.open(rel, "wt") as fh:
        json.dump(doc, fh)


def game(pk, at):
    team = lambda n, i: {"team": {"name": "%s %d" % (n, pk), "id": i},  # noqa: E731
                         "probablePitcher": {"id": 1000 + i, "fullName": "P%d" % i}}
    return {"gamePk": pk, "gameDate": at, "gameType": "R", "venue": {"id": 7},
            "teams": {"home": team("Home", 2 * pk), "away": team("Away", 2 * pk + 1)}}


def schedule(n_games):
    """One reading for DAY, pulled 17:00Z: game 1 started 17:30Z, two to come."""
    gs = [game(1, DAY + "T17:30:00Z"), game(2, DAY + "T22:05:00Z"), game(3, DAY + "T23:10:00Z")]
    put("data/%s/schedule/1700.json.gz" % DAY,
        {"pulled_at": DAY + "T17:00:00Z", "date": DAY,
         "schedule": {"totalGames": n_games, "dates": [{"games": gs[:n_games]}] if n_games else []}})


class Sandbox:
    """A throwaway tree for collect.py, the clock pinned to T."""
    SAVE = ("now", "log", "odds_get", "run_mode")

    def __enter__(self):
        self.d, self.cwd = tempfile.mkdtemp(prefix="mlbmodel-"), os.getcwd()
        os.chdir(self.d)
        self.saved = {k: getattr(C, k) for k in self.SAVE}
        self.plan, self.card = F.plan, CA.main
        self.calls, self.cards, self.logs = [], [], []
        C.now = lambda: T
        C.log = lambda *a, **k: self.logs.append(" ".join(str(x) for x in a))
        C.odds_get = lambda *a, **k: self.calls.append(a) or ({}, 6, 15000)
        CA.main = lambda *a, **k: self.cards.append(a)
        C._RAN_PAID.clear()
        return self

    def __exit__(self, *a):
        for k, v in self.saved.items():
            setattr(C, k, v)
        F.plan, CA.main = self.plan, self.card
        C._RAN_PAID.clear()
        os.chdir(self.cwd)
        shutil.rmtree(self.d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 ON A GAME DAY WITH NO MODEL FILE, THE CONTRACT OWES IT AND CONVERGE BUILDS IT")
# ══════════════════════════════════════════════════════════════════════
with Sandbox() as box:
    schedule(3)
    # game 1 started 17:30Z; its winner was frozen at 15:00Z, and the rebuild must keep it
    put("data/%s/winner-picks/1500.json.gz" % DAY,
        {"league": "mlb", "taken_at": DAY + "T15:00:00Z",
         "rows": [{"game_id": "1", "commence": DAY + "T17:30:00Z", "away": "Away 1",
                   "home": "Home 1", "pick": "Home 1", "side": "home", "chance": 77,
                   "chance_value": 77.0, "price": -150, "book": "fanduel"}]})
    _modes, _rows = F.plan(data="data", picks="picks", now=T)
    _row = [r for r in _rows if r["mode"] == "game-model"]
    ck("🔴 on a game day with no model file the contract owes it, free",
       "game-model" in _modes and len(_row) == 1 and _row[0]["missing"] and not _row[0]["paid"],
       str(_row))
    F.plan = lambda **kw: (["game-model"], _rows)
    C.converge()
    _model = json.load(open("data/latest/mlb-game-model.json", encoding="utf-8"))
    _win = json.load(open("data/latest/winners.json", encoding="utf-8"))
    _picks = os.listdir("picks") if os.path.isdir("picks") else []
    ck("🔴 converge builds it for the next slate, and does not build the card",
       _model.get("slate") == DAY and len(_model.get("games") or []) == 3
       and not box.cards and _picks == [],
       "slate %s games %d card calls %d picks %s" % (_model.get("slate"),
                                                    len(_model.get("games") or []),
                                                    len(box.cards), _picks))
    eq(len(box.calls), 0, "🔴 the build makes no paid call: 0 credits")
    ck("🔴 the winners file is rebuilt right after it, from it",
       _win.get("slate") == DAY and [r["game_id"] for r in _win.get("rows") or []] == ["1", "2", "3"]
       and all(r.get("pick") for r in _win["rows"]), str(_win.get("rows"))[:300])
    _g1 = next((r for r in _win.get("rows") or [] if r["game_id"] == "1"), {})
    eq((_g1.get("pick"), _g1.get("chance")), ("Home 1", 77),
       "🔴 a started game's winner is unchanged by the rebuild: the pick frozen before it "
       "started (77%), not the model's new number")

# ══════════════════════════════════════════════════════════════════════
section("2. ⛔ ON A NO-GAMES DAY IT IS NOT OWED")
# ══════════════════════════════════════════════════════════════════════
with Sandbox():
    schedule(0)
    _modes, _rows = F.plan(data="data", picks="picks", now=T)
    ck("🔴 a no-games day (every stored reading says 0): no game-model row, nothing built",
       "game-model" not in _modes and not [r for r in _rows if r["mode"] == "game-model"],
       str(_modes))
