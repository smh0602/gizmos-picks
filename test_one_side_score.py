#!/usr/bin/env python3
"""test_one_side_score.py — a spread or total pick shows only on the predicted score's side.

`[Sam, 2026-10-16]` The football model's predicted score comes from its moneyline and total
fits, and each spread pick from a separate fit: 13 of 66 college spread and total picks sat on
the side the model's own score said loses (Purdue -3.5 beside "Purdue by 1.2"; a parlay leg on
Over 55.5 beside a predicted 52). Asked, Sam chose "Must match the score: A spread or total
pick, and a parlay's line leg, shows only when the predicted score lands on its side." Planted
rows; the real predicted_score, score_sigma and total_sigma; ⛔ reads nothing live.

# @vacuity 🔴 a spread stays only when the predicted margin covers it
#   file: one_side.py
#   find:     return b in ("home", "away") and ((h - a) if b == "home" else (a - h)) + point > 0
#   with:     return True
#
# @vacuity 🔴 a total stays only on the predicted total's side
#   file: one_side.py
#   find:         return (h + a > point) if s == "over" else (h + a < point) if s == "under" else False
#   with:         return True
#
# @vacuity 🔴 no predicted score is never a pick's side
#   file: one_side.py
#   find:     if not score or score.get("home") is None or score.get("away") is None or point is None:
#   with:     if False:
#
# @vacuity 🔴 the model's pick list keeps only picks on the predicted score's side
#   file: fb_model.py
#   find:     out, _ = one_side.score_keep(out, lambda p: sc.get(p["game_id"]), own_point)
#   with:     out = out
#
# @vacuity 🔴 ...judging a home spread at its own point (-M)
#   file: fb_model.py
#   find:     return -v if p.get("side") == "home" else v
#   with:     return v
#
# @vacuity 🔴 the card's game lines and alternate spreads are judged by the score
#   file: card_fb.py
#   find:     rows, _ = one_side.score_keep(rows + alt_spread_rows(rows, ladder), one_side.scores_by_names(win_chances))
#   with:     rows = rows + alt_spread_rows(rows, ladder)
#
# @vacuity 🔴 a same-game parlay's line leg is judged by the score
#   file: card_fb.py
#   find:             if score is not None and not one_side.score_keep([row], score, lambda r: r.get("point"))[0]:
#   with:             if False:
#
# @vacuity 🔴 the card hands the parlay builder the model's scores
#   file: card_fb.py
#   find:                                          score=one_side.scores_by_names(_model.get("win_chances") or []))
#   with:                                          score=None)
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "ncaaf")
import one_side as O  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

WASH, PUR, FLA, TEX = "Washington Huskies", "Purdue Boilermakers", "Florida Gators", "Texas Longhorns"
S = {"home": 24.0, "away": 22.8}             # Purdue (home) by 1.2, 46.8 points

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE RULE: ON THE PREDICTED SCORE'S SIDE, NEVER ON THE NUMBER")
# ══════════════════════════════════════════════════════════════════════
eq([O.score_side_ok({"market": "spread", "side": "home"}, S, -3.5),
    O.score_side_ok({"market": "spread", "side": "home"}, S, -1.0),
    O.score_side_ok({"market": "spread", "side": "away"}, S, 3.5),
    O.score_side_ok({"market": "alternate_spread", "side": "home"}, {"home": 24.0, "away": 20.5}, -3.5),
    O.score_side_ok({"market": "spreads", "side": WASH, "game": "%s @ %s" % (WASH, PUR)}, S, 1.5),
    O.score_side_ok({"market": "total", "side": "under"}, S, 49.5),
    O.score_side_ok({"market": "totals", "side": "Over"}, S, 49.5),
    O.score_side_ok({"market": "total", "side": "over"}, S, 46.8),
    O.score_side_ok({"market": "moneyline", "side": "home"}, S, None),
    O.score_side_ok({"market": "spread", "side": "home"}, None, -3.5)],
   [False, True, True, False, True, True, False, False, None, False],
   "🔴 Purdue -3.5 on a predicted 1.2 goes (Sam's game), Purdue -1 stays, Washington +3.5 stays; landing ON "
   "the number (by 3.5 on -3.5) is not its side; a price-gap leg's team is read from its name; Under 49.5 "
   "on 46.8 stays, Over 49.5 goes, Over 46.8 on 46.8 goes; a moneyline is not judged here; no score, no pick")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE MODEL'S PICK LIST IS JUDGED ON EXACTLY THE SCORE THE GAME LINES TAB PRINTS")
# ══════════════════════════════════════════════════════════════════════
import fb_model as FM  # noqa: E402
NOW, KICK = "2026-10-16T08:00:00Z", "2026-10-17T19:30:00Z"
FIN = [{"id": "f%d" % i, "final": True, "hs": hs, "as": as_, "sig": {"own_m": 0.0, "own_t": 45.0}, "snap": None}
       for i, (hs, as_) in enumerate(((31, 15), (15, 31), (35, 24), (24, 35)))]     # sigma 16 / 13.6
ROWS = FIN + [
    {"id": "g1", "final": False, "T": 47.5, "sig": {"own_t": 47.0},
     "snap": {"commence": KICK, "names": (PUR, WASH), "pulled_at": NOW}},
    {"id": "g2", "final": False, "T": 44.5, "sig": {"own_t": 46.0},
     "snap": {"commence": KICK, "names": (TEX, FLA), "pulled_at": NOW}}]
P_FIT = {("g1", "moneyline"): 0.529, ("g1", "total"): 0.55, ("g1", "spread"): 0.6,
         ("g2", "moneyline"): 0.75, ("g2", "total"): 0.60, ("g2", "spread"): 0.6}
PICKS = {("g1", "moneyline"): ("home", None, -130, 0.529), ("g1", "spread"): ("home", 3.5, -110, 0.575),
         ("g1", "total"): ("under", 47.5, -110, 0.53),
         ("g2", "spread"): ("home", 6.5, -110, 0.56), ("g2", "total"): ("over", 44.5, -110, 0.58)}


def _bp(r, mk, model, quotes=None):
    v = PICKS.get((r["id"], mk)) if model else None
    if not v:
        return None
    side, ln, px, p = v
    dec = 1 + (px / 100.0 if px > 0 else 100.0 / -px)
    return {"side": side, "book": "fanduel", "line": ln, "price": px, "p": p, "ev": p * dec - 1,
            "break_even": 1 / dec, "assumed": False}


_saved = {n: getattr(FM, n) for n in ("features", "label", "fit", "predict", "best_pick", "book_quotes")}
try:
    FM.features = lambda r, mk, **k: (r["id"], mk)
    FM.label = lambda r, mk: 1
    FM.fit = lambda xs, ys, **k: {"n": len(xs)}
    FM.predict = lambda m, x: P_FIT.get(x, 0.5)
    FM.best_pick = _bp
    FM.book_quotes = lambda r, mk: []
    CUR = FM.current_picks("ncaaf", ROWS, now=NOW)
    WCH = FM.win_chances(ROWS, now=NOW)
    ALL = [{"game_id": r["id"], "market": mk, "side": v[0], "line": {"value": v[1]}}
           for (gid, mk), v in PICKS.items() for r in ROWS if r["id"] == gid]
finally:
    for n, f in _saved.items():
        setattr(FM, n, f)
SC = {w["game_id"]: w.get("score") for w in WCH}
ck(SC.get("g1") and 0 < SC["g1"]["home"] - SC["g1"]["away"] < 3.5 and SC["g1"]["home"] + SC["g1"]["away"] > 47.5
   and SC["g2"]["home"] - SC["g2"]["away"] > 6.5 and SC["g2"]["home"] + SC["g2"]["away"] > 44.5,
   "⚠️ the case exists: the Game Lines tab's score has Purdue winning by under 3.5 with more than 47.5 points, "
   "and Texas by more than 6.5 with more than 44.5", str(SC))
eq(sorted((p["game_id"], p["market"]) for p in CUR),
   [("g1", "moneyline"), ("g2", "spread"), ("g2", "total")],
   "🔴 Purdue -3.5 on a predicted Purdue-by-1 goes, and so does Under 47.5 under a predicted total above it; "
   "Texas -6.5 (a predicted 10+) and Over 44.5 stay; the moneyline is the expected winner's and stays")
eq(sorted((p["game_id"], p["market"]) for p in CUR),
   sorted((p["game_id"], p["market"]) for p in ALL
          if O.score_side_ok(p, SC.get(p["game_id"]), FM.own_point(p)) in (None, True)),
   "🔴 exactly the picks the Game Lines tab's own printed score agrees with: the list and the tab use one score")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE CARD'S GAME LINES: AN ALTERNATE SPREAD PAST THE PREDICTED MARGIN NEVER SHOWS")
# ══════════════════════════════════════════════════════════════════════
import card_fb as CF  # noqa: E402


def mp(away, home, mk, side, team, line, px, p):
    return {"game": "%s at %s" % (away, home), "commence": KICK, "market": mk, "side": side, "team": team,
            "book": "fanduel", "line": {"value": line}, "price": {"value": px},
            "model_probability": {"value": p}, "break_even": {"value": 50.0}, "priced_at": NOW}


WIN = [{"away": WASH, "home": PUR, "p_home": 52.9, "score": {"home": 24.0, "away": 22.8}},
       {"away": FLA, "home": TEX, "p_home": 75.0, "score": {"home": 30.9, "away": 20.1}}]
RUNG = lambda side, pt, edge: {"side": side, "best": -150, "p": 62.0, "pt": pt, "edge": edge, "be": 60.0,  # noqa: E731
                               "book": "fanduel"}
LAD = {"games": [{"away": FLA, "home": TEX, "commence": KICK, "main_spread_home": -6.5,
                  "spread": [RUNG("home", -12.5, 4.0), RUNG("home", -9.5, 2.0)]}]}
_picks = [mp(WASH, PUR, "spread", "home", PUR, 3.5, -110, 57.5), mp(WASH, PUR, "total", "under", "Under", 49.5, -110, 53.0),
          mp(FLA, TEX, "spread", "home", TEX, 6.5, -110, 56.0)]
GL = CF.card_game_lines(_picks, [], LAD, CF.et_date(KICK), win_chances=WIN)
eq(sorted((r["player"], r["market"], r["line"]) for r in GL),
   [("Texas Longhorns", "spread", -6.5), ("Under", "total", 49.5)],
   "🔴 Purdue -3.5 goes (a predicted 1.2); Under 49.5 on a predicted 46.8 stays; Texas -6.5 stays (10.8), and "
   "its alternate is NOT the richer -12.5, which the predicted margin does not cover")
eq([O.score_side_ok(r, O.scores_by_names(WIN)(r), r["line"]) for r in GL], [True] * len(GL),
   "   ...the guard on the card's real output: every row on the predicted score's side")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 A SAME-GAME PARLAY'S LINE LEG: EACH GAME'S BEST LEG ON THE SCORE'S SIDE")
# ══════════════════════════════════════════════════════════════════════
def snap_game(gid, away, home):
    """The richest gap is the home spread -3.5 (+120 vs -110); the Over 49.5 has a smaller one."""
    books = {}
    for bk, hp, op in (("fanduel", 120, -105), ("draftkings", -110, -115), ("hardrockbet", -110, -115)):
        books[bk] = {"spreads": {away: {"px": -110, "pt": 3.5}, home: {"px": hp, "pt": -3.5}},
                     "totals": {"Over": {"px": op, "pt": 49.5}, "Under": {"px": -110, "pt": 49.5}}}
    return {"id": gid, "away": away, "home": home, "commence": KICK, "books": books}


_snap = {"games": [snap_game("ev1", WASH, PUR)]}
_win = O.by_names(WIN)
_free, _ = CF.build_game_lines(_snap, n=None, slate=CF.et_date(KICK), winner=_win)
_ruled, _ = CF.build_game_lines(_snap, n=None, slate=CF.et_date(KICK), winner=_win, score=O.scores_by_names(WIN))
eq(([(r["market"], r["side"], r["point"]) for r in _free], [(r["market"], r["side"], r["point"]) for r in _ruled]),
   ([("spreads", PUR, -3.5)], []),
   "🔴 the richest allowed leg is Purdue -3.5; on a predicted Purdue-by-1.2 it goes, and the Over 49.5 (a "
   "predicted 46.8) cannot stand in: no line leg for this game rather than one off the score's side")
_main = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
_main = _main[_main.index("\ndef main("):]
ck('score=one_side.scores_by_names(_model.get("win_chances") or []))' in _main,
   "🔴 card_fb.main hands the parlay builder the model's own scores")
