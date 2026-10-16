#!/usr/bin/env python3
r"""test_one_side.py — ONE TEAM PER GAME: every side pick is on the model's expected winner.

`[Sam, 2026-10-16]` "i noticed that the model picked huskies on the moneyline for college
foootbal but also picked the -3.5 spread for purdue; the huskies opponent. these two picks
go directly against one another and we can't have our model choosing both sides at once"
— "fixed as whole for all leagues so it doesn't happen again". Asked which side stays, he
chose the EXPECTED WINNER (the Game Lines tab's pick to win). Every builder of a list of
side picks is driven here on a planted both-sides game (MLB's card rows in
test_mlb_game_lines.py). Planted data only; ⛔ reads nothing live.

# @vacuity 🔴 the expected winner is the higher chance, the home team on a tie (the Game Lines tab's rule)
#   file: one_side.py
#   find:     return "home" if p_home >= 100 - p_home else "away"
#   with:     return "home" if p_home > 100 - p_home else "away"
#
# @vacuity 🔴 a side pick stays only on its game's expected winner
#   file: one_side.py
#   find:         (kept if b is None or (b != "?" and b == winner(r)) else dropped).append(r)
#   with:         (kept if True else dropped).append(r)
#
# @vacuity 🔴 a pick that names its team (the price-gap legs) is matched on the team name
#   file: one_side.py
#   find:     if side is not None and side == home:
#   with:     if False:
#
# @vacuity 🔴 the guard sees picks on both teams
#   file: one_side.py
#   find:         if len(teams) > 1:
#   with:         if False:
#
# @vacuity 🔴 the Game Lines tab names its winner with the shared rule
#   file: winners.py
#   find:     side = one_side.expected_side(p_home)
#   with:     side = "home"
#
# @vacuity 🔴 the football model's pick list keeps only the expected winner's side picks
#   file: fb_model.py
#   find:     out, _ = one_side.keep(out, lambda p: exp.get(p["game_id"]))
#   with:     pass
#
# @vacuity 🔴 ...and the expected winner is the moneyline fit's own pick to win
#   file: fb_model.py
#   find:         exp[r["id"]] = (one_side.expected_side(round(100 * predict(models["moneyline"], features(r, "moneyline")), 1))
#   with:         exp[r["id"]] = (one_side.expected_side(50.0)
#
# @vacuity 🔴 the card's game lines keep only the expected winner's side, BEFORE the alternate spreads
#   file: card_fb.py
#   find:         rows, _ = one_side.keep(rows, one_side.by_names(win_chances))
#   with:         pass
#
# @vacuity 🔴 the card is given the model file's win chances
#   file: card_fb.py
#   find:                                  win_chances=_model.get("win_chances") or [])
#   with:                                  win_chances=None)
#
# @vacuity 🔴 a same-game parlay's line leg is a total or on the expected winner
#   file: card_fb.py
#   find:     _gl_all, _ = one_side.keep(_gl_all, one_side.by_names(_model.get("win_chances") or []))
#   with:     pass
#
# @vacuity 🔴 the MLB verifier fails a card that backs both teams of a game
#   file: verify_card.py
#   find:    not _gcf, str(_gcf[:3]))
#   with:    True, str(_gcf[:3]))
"""
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "ncaaf")
import one_side as O  # noqa: E402
from tcheck import ck, eq, section, shown  # noqa: E402

WASH, PUR, FLA, TEX = "Washington Huskies", "Purdue Boilermakers", "Florida Gators", "Texas Longhorns"

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE RULE: THE EXPECTED WINNER, A TOTAL NEVER TOUCHED")
# ══════════════════════════════════════════════════════════════════════
eq([O.expected_side(x) for x in (51.2, 48.8, 50.0, None)], ["home", "away", "home", None],
   "🔴 the higher win chance; the home team on an exact tie (the Game Lines tab's own rule); no chance, none")
eq([O.backs(r) for r in (
    {"market": "moneyline", "side": "away"}, {"market": "spread", "side": "home"},
    {"market": "alternate_spread", "side": "away"}, {"market": "run_line", "side": "home"},
    {"market": "total", "side": "under"}, {"market": "totals", "side": "Over"},
    {"market": "spreads", "side": WASH, "game": "%s @ %s" % (WASH, PUR)},
    {"market": "h2h", "side": PUR, "game": "%s @ %s" % (WASH, PUR)},
    {"market": "spreads", "side": "Somebody Else", "game": "%s @ %s" % (WASH, PUR)})],
   ["away", "home", "away", "home", None, None, "away", "home", "?"],
   "🔴 every list's shape: a side, a team name (price-gap legs), a total (no team), and a team it cannot "
   "tell ('?', which is never kept)")
_k, _d = O.keep([{"market": "moneyline", "side": "away", "game_id": 1}, {"market": "spread", "side": "home", "game_id": 1},
                 {"market": "total", "side": "under", "game_id": 1}, {"market": "spread", "side": "home", "game_id": 2}],
                lambda r: {1: "home", 2: None}[r["game_id"]])
eq(([(r["game_id"], r["market"]) for r in _k], [(r["game_id"], r["market"]) for r in _d]),
   ([(1, "spread"), (1, "total")], [(1, "moneyline"), (2, "spread")]),
   "🔴 kept: the expected winner's spread and the total; dropped: the other team's moneyline, and a side "
   "pick for a game with no expected winner (the tab names none either)")
eq(O.conflicts([{"market": "moneyline", "side": "away", "game_id": 1}, {"market": "spread", "side": "home", "game_id": 1},
                {"market": "total", "side": "under", "game_id": 2}, {"market": "spread", "side": "away", "game_id": 3}],
               winner=lambda r: "home"),
   [(1, "picks on both teams"), (3, "a pick on the team the model does not expect to win")],
   "🔴 the guard names a game backing both teams, and one backing the team the model does not expect to win")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE GAME LINES TAB NAMES ITS WINNER WITH THE SAME RULE")
# ══════════════════════════════════════════════════════════════════════
import winners as WN  # noqa: E402
eq([WN.make_row("g", "2026-10-17T19:30:00Z", WASH, PUR, p, {}, {})["side"] for p in (51.2, 48.8, 50.0)],
   ["home", "away", "home"], "🔴 Purdue 51.2 home, Washington when Purdue is 48.8, the home team on a 50/50 tie")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE FOOTBALL MODEL'S PICK LIST (the Model picks table, the ledger, the card's source)")
# ══════════════════════════════════════════════════════════════════════
import fb_model as FM  # noqa: E402
NOW, KICK = "2026-10-16T08:00:00Z", "2026-10-17T19:30:00Z"
ROWS = [{"id": "g1", "final": False, "snap": {"commence": KICK, "names": (PUR, WASH), "pulled_at": NOW}},
        {"id": "g2", "final": False, "snap": {"commence": KICK, "names": (TEX, FLA), "pulled_at": NOW}}]
P_HOME = {"g1": 0.512, "g2": 0.300}            # Purdue 51.2 (expected), Texas 30.0 (Florida expected)
PICKS = {("g1", "moneyline"): ("away", None, 150, 0.488), ("g1", "spread"): ("home", 3.5, -110, 0.558),
         ("g1", "total"): ("under", 50.5, -110, 0.562),
         ("g2", "moneyline"): ("away", None, 120, 0.700), ("g2", "spread"): ("home", 6.5, -110, 0.560)}


def _bp(r, mk, model, quotes=None):
    v = PICKS.get((r["id"], mk))
    if not v:
        return None
    side, ln, px, p = v
    dec = 1 + (px / 100.0 if px > 0 else 100.0 / -px)
    return {"side": side, "book": "fanduel", "line": ln, "price": px, "p": p, "ev": p * dec - 1,
            "break_even": 1 / dec, "assumed": False}


_saved = {n: getattr(FM, n) for n in ("features", "label", "fit", "predict", "best_pick")}
try:
    FM.features = lambda r, mk, **k: (r["id"], mk)
    FM.label = lambda r, mk: 1
    FM.fit = lambda xs, ys, **k: {"n": len(xs)}
    FM.predict = lambda m, x: P_HOME[x[0]]
    FM.best_pick = _bp
    CUR = FM.current_picks("ncaaf", ROWS, now=NOW)
finally:
    for n, f in _saved.items():
        setattr(FM, n, f)
eq(sorted((p["game_id"], p["market"], p["team"]) for p in CUR),
   [("g1", "spread", PUR), ("g1", "total", "Under"), ("g2", "moneyline", FLA)],
   "🔴 Washington ML +150 beside Purdue -3.5 (Sam's game): Washington's moneyline is gone, Purdue -3.5 and "
   "the Under stay; Florida, the expected winner at 70%, keeps its moneyline and Texas -6.5 goes")
eq(O.conflicts(CUR, winner=lambda p: {"g1": "home", "g2": "away"}[p["game_id"]]), [],
   "🔴 the guard on the real builder's output: no game backs both teams or the team it does not expect to win")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE CARD'S GAME LINES, AND THE ALTERNATE SPREAD FOLLOWS THE KEPT SIDE")
# ══════════════════════════════════════════════════════════════════════
import card_fb as CF  # noqa: E402


def mp(away, home, mk, side, team, line, px, p):
    return {"game": "%s at %s" % (away, home), "commence": KICK, "market": mk, "side": side, "team": team,
            "book": "fanduel", "line": {"value": line}, "price": {"value": px},
            "model_probability": {"value": p}, "break_even": {"value": 50.0}, "priced_at": NOW}


MODEL_PICKS = [mp(WASH, PUR, "moneyline", "away", WASH, None, 150, 52.0),     # 52: clears the 50% floor
               mp(WASH, PUR, "spread", "home", PUR, 3.5, -110, 55.8),
               mp(WASH, PUR, "total", "under", "Under", 50.5, -110, 56.2),
               mp(FLA, TEX, "spread", "away", FLA, 11.5, -110, 53.0),          # Texas is the expected winner
               mp(FLA, TEX, "moneyline", "home", TEX, None, -300, 70.0)]
WIN = [{"away": WASH, "home": PUR, "p_home": 51.2}, {"away": FLA, "home": TEX, "p_home": 70.0}]
RUNG = lambda side, pt: {"side": side, "best": -150, "p": 62.0, "pt": pt, "edge": 2.0, "be": 60.0, "book": "fanduel"}  # noqa: E731
LADDER = {"games": [{"away": WASH, "home": PUR, "commence": KICK, "main_spread_home": -3.5,
                     "spread": [RUNG("home", -1.5), RUNG("away", 7.5)]},
                    {"away": FLA, "home": TEX, "commence": KICK, "main_spread_home": -11.5,
                     "spread": [RUNG("away", 17.5)]}]}
GL = CF.card_game_lines(MODEL_PICKS, [], LADDER, CF.et_date(KICK), win_chances=WIN)
eq(sorted((r["player"], r["market"], r["line"]) for r in GL),
   sorted([(PUR, "spread", -3.5), (PUR, "alternate_spread", -1.5), ("Under", "total", 50.5),
           (TEX, "moneyline", None)]),
   "🔴 Purdue -3.5 and its alternate -1.5, the Under, Texas to win; never Washington's moneyline, Florida "
   "+11.5, or Florida's alternate rung (the filter runs BEFORE the alternates are added)")
eq(O.conflicts(GL, winner=O.by_names(WIN), game=lambda r: r["game"]), [],
   "🔴 the guard on the card's real output: one team per game, the expected winner's")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 A SAME-GAME PARLAY'S LINE LEG")
# ══════════════════════════════════════════════════════════════════════
LEGS = [{"kind": "MARKET", "game": "%s @ %s" % (WASH, PUR), "market": "spreads", "side": WASH, "point": 3.5},
        {"kind": "MARKET", "game": "%s @ %s" % (WASH, PUR), "market": "h2h", "side": PUR, "point": None},
        {"kind": "MARKET", "game": "%s @ %s" % (FLA, TEX), "market": "totals", "side": "Over", "point": 55.5}]
_lk, _ld = O.keep(LEGS, O.by_names(WIN))
eq(([(r["market"], r["side"]) for r in _lk], [(r["market"], r["side"]) for r in _ld]),
   ([("h2h", PUR), ("totals", "Over")], [("spreads", WASH)]),
   "🔴 a price-gap leg on Washington +3.5 is dropped; Purdue to win and the Over stay")
_src = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
_k1 = '_gl_all, _ = one_side.keep(_gl_all, one_side.by_names(_model.get("win_chances") or []))'
ck(_k1 in _src and _src.index(_k1) < _src.index("sgp, sgp_meta = build_sgp_fb(")
   and 'win_chances=_model.get("win_chances") or [])' in _src,
   "🔴 the card filters the parlay legs before the same-game parlays are built, and hands its game lines "
   "the model file's win chances")

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 THE MLB VERIFIER FAILS A CARD THAT BACKS BOTH TEAMS")
# ══════════════════════════════════════════════════════════════════════
LINE = "one team per game: every unstarted game line is on the model's expected winner"
PLANT = r'''
import sys, json; sys.path.insert(0, %r)
import card as C
case = sys.argv[1]
FUT, PAST = "2099-10-17T23:05:00Z", "2020-10-17T23:05:00Z"
def row(mk, side, at):
    return {"kind": "mlb-line", "market": mk, "side": side, "game_pk": 1, "player": "Home" if side == "home" else "Away",
            "price": -110, "book": "fanduel", "line": None if mk == "moneyline" else (-1.5 if side == "home" else 1.5),
            "commence": at, "confidence": 60, "confidence_value": 60.0, "break_even": 52.4, "rank": 1}
rows = {"both": [row("moneyline", "home", FUT), row("run_line", "away", FUT)],
        "winner": [row("moneyline", "home", FUT)],
        "loser": [row("run_line", "away", FUT)],
        "started": [row("moneyline", "home", PAST), row("run_line", "away", PAST)]}[case]
for i, r in enumerate(rows, 1):
    r["rank"] = i
C.main = lambda *a, **k: {"date": "2026-10-17", "picks": [], "below_price_floor": [], "pairs": [],
    "projections": {}, "top10": [], "top10_excluded": {}, "parlays": {}, "hitter_record_bands": [],
    "board_rule": {}, "board_seats": {}, "pitcher_correction": {}, "game_lines": rows}
import verify_card  # noqa
''' % ROOT


def verdict(out):
    got = [ln[2:6] for ln in out.splitlines() if ln.startswith(("  PASS ", "  FAIL ")) and ln[7:].startswith(LINE)]
    return got[0] if len(got) == 1 else got or None


_T = tempfile.mkdtemp(prefix="oneside-")
_v = {}
try:
    os.makedirs(os.path.join(_T, "data", "latest"))
    for _nm, _obj in (("pitchers", {"players": {}}), ("props", {"games": []}), ("hitters", {"players": {}})):
        with gzip.open(os.path.join(_T, "data", "latest", _nm + ".json.gz"), "wt", encoding="utf-8") as _fh:
            json.dump(_obj, _fh)
    json.dump({"games": [{"game_pk": 1, "win": {"home": 60.0, "away": 40.0}}]},
              open(os.path.join(_T, "data", "latest", "mlb-game-model.json"), "w", encoding="utf-8"))
    for _c in ("both", "winner", "loser", "started"):
        _q = subprocess.run([sys.executable, "-c", PLANT, _c], cwd=_T, capture_output=True, text=True,
                            encoding="utf-8", timeout=600, env=dict(os.environ, PYTHONUTF8="1"))
        _v[_c] = verdict(_q.stdout)
        if _v[_c] not in ("PASS", "FAIL"):
            print(shown(_q.stdout[-1200:]), shown(_q.stderr[-1200:]))
finally:
    shutil.rmtree(_T, ignore_errors=True)
eq(_v, {"both": "FAIL", "winner": "PASS", "loser": "FAIL", "started": "PASS"},
   "🔴 the REAL verifier: the favourite's moneyline beside the underdog +1.5 FAILS, the expected winner alone "
   "PASSES, a lone pick on the team the model does not expect to win FAILS, and a started pair (frozen as "
   "published) is not re-judged")
