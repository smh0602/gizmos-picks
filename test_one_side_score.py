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
#   find:     return b in ("home", "away") and round(((h - a) if b == "home" else (a - h)) + point, 6) > 0
#   with:     return True
#
# @vacuity 🔴 ...an away spread is judged by the AWAY margin
#   file: one_side.py
#   find:     return b in ("home", "away") and round(((h - a) if b == "home" else (a - h)) + point, 6) > 0
#   with:     return b in ("home", "away") and round((h - a) + point, 6) > 0
#
# @vacuity 🔴 ...and a margin landing ON the number is not its side (no float error lets it through)
#   file: one_side.py
#   find:     return b in ("home", "away") and round(((h - a) if b == "home" else (a - h)) + point, 6) > 0
#   with:     return b in ("home", "away") and ((h - a) if b == "home" else (a - h)) + point > 0
#
# @vacuity 🔴 a total stays only on the predicted total's side
#   file: one_side.py
#   find:         return d > 0 if s == "over" else d < 0 if s == "under" else False
#   with:         return True
#
# @vacuity 🔴 ...an Under landing ON the number is not its side
#   file: one_side.py
#   find:         return d > 0 if s == "over" else d < 0 if s == "under" else False
#   with:         return d > 0 if s == "over" else d <= 0 if s == "under" else False
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
# @vacuity 🔴 ...and an away spread at its own point (+M)
#   file: fb_model.py
#   find:     return -v if p.get("side") == "home" else v
#   with:     return -v
#
# @vacuity 🔴 the card's game lines and alternate spreads are judged by the score
#   file: card_fb.py
#   find:     rows, _ = one_side.score_keep(rows + alt_spread_rows(rows, ladder, _score), _score)
#   with:     rows = rows + alt_spread_rows(rows, ladder, _score)
#
# @vacuity 🔴 the alternate spread is the best rung the predicted score COVERS
#   file: card_fb.py
#   find:               and (score is None or one_side.score_side_ok(
#   with:               and (True or one_side.score_side_ok(
#
# @vacuity 🔴 the why prints a predicted score only when it lands on the pick's side, never on the number
#   file: fb_why.py
#   find:         return r.get("line") is not None and round(m + float(r["line"]), 6) > 0
#   with:         return r.get("line") is not None and m + float(r["line"]) > 0
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

A = {"home": 20.0, "away": 27.0}             # the AWAY team by 7
eq([O.score_side_ok({"market": "spread", "side": "away"}, A, -6.5),
    O.score_side_ok({"market": "spread", "side": "away"}, A, -7.5),
    O.score_side_ok({"market": "spread", "side": "home"}, A, 6.5),
    O.score_side_ok({"market": "spread", "side": "home"}, A, 7.5)],
   [True, False, False, True],
   "🔴 an away favourite by 7: its -6.5 stays, its -7.5 goes; the home +6.5 goes, the home +7.5 stays")
eq([O.score_side_ok({"market": "spread", "side": "away"}, {"home": 14.1, "away": 21.1}, -7.0),
    O.score_side_ok({"market": "total", "side": "under"}, S, 46.8),
    O.score_side_ok({"market": "spread", "side": "home"}, S, None),
    O.score_side_ok({"market": "total", "side": "under"}, S, None)],
   [False, False, False, False],
   "🔴 ON the number is never its side: Tulane by 7.0 (21.1 - 14.1, a float 1.8e-15 above) on -7, an Under "
   "46.8 on a predicted 46.8; and a row with no number is never its side")


def _try(f):
    try:
        return f()
    except Exception as e:  # noqa: BLE001
        return type(e).__name__


eq([_try(lambda: O.score_side_ok({"market": "spread", "side": "home"}, None, -3.5)),
    _try(lambda: O.score_side_ok({"market": "total", "side": "over"}, {"home": None, "away": 20.0}, 40.5))],
   [False, False], "🔴 no predicted score (or half of one) is never a pick's side")
import fb_why as WY  # noqa: E402
eq([WY.score_agrees({"market": "spread", "side": "away", "line": -7.0}, {"home": 14.1, "away": 21.1}),
    WY.score_agrees({"market": "spread", "side": "away", "line": -6.5}, {"home": 14.1, "away": 21.1})],
   [False, True],
   "🔴 the why's own check agrees: no predicted score is printed under a pick it lands exactly ON")

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
     "snap": {"commence": KICK, "names": (TEX, FLA), "pulled_at": NOW}},
    # two road favourites at 25% home (the road team by about 9)
    {"id": "g3", "final": False, "T": 45.5, "sig": {"own_t": 45.0},
     "snap": {"commence": KICK, "names": ("Home Three", "Road Three"), "pulled_at": NOW}},
    {"id": "g4", "final": False, "T": 45.5, "sig": {"own_t": 45.0},
     "snap": {"commence": KICK, "names": ("Home Four", "Road Four"), "pulled_at": NOW}}]
P_FIT = {("g1", "moneyline"): 0.529, ("g1", "total"): 0.55, ("g1", "spread"): 0.6,
         ("g2", "moneyline"): 0.75, ("g2", "total"): 0.60, ("g2", "spread"): 0.6,
         ("g3", "moneyline"): 0.25, ("g3", "total"): 0.5, ("g3", "spread"): 0.4,
         ("g4", "moneyline"): 0.25, ("g4", "total"): 0.5, ("g4", "spread"): 0.4}
PICKS = {("g1", "moneyline"): ("home", None, -130, 0.529), ("g1", "spread"): ("home", 3.5, -110, 0.575),
         ("g1", "total"): ("under", 47.5, -110, 0.53),
         ("g2", "spread"): ("home", 6.5, -110, 0.56), ("g2", "total"): ("over", 44.5, -110, 0.58),
         # the stored line is M on the HOME margin: the road team -6.5 is M = -6.5, -12.5 is M = -12.5
         ("g3", "spread"): ("away", -6.5, -110, 0.56), ("g4", "spread"): ("away", -12.5, -110, 0.56)}


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
ck(SC.get("g3") and 6.5 < SC["g3"]["away"] - SC["g3"]["home"] < 12.5,
   "⚠️ ...and the road teams are predicted to win by between 6.5 and 12.5", str(SC.get("g3")))
eq(sorted((p["game_id"], p["market"]) for p in CUR),
   [("g1", "moneyline"), ("g2", "spread"), ("g2", "total"), ("g3", "spread")],
   "🔴 Purdue -3.5 on a predicted Purdue-by-1 goes, and so does Under 47.5 under a predicted total above it; "
   "Texas -6.5 (a predicted 10+) and Over 44.5 stay; the moneyline is the expected winner's and stays; a road "
   "favourite's -6.5 stays and another's -12.5 goes (each predicted to win by about 9)")
eq(sorted((p["game_id"], p["market"]) for p in CUR),
   sorted((p["game_id"], p["market"]) for p in ALL
          if O.score_side_ok(p, SC.get(p["game_id"]), FM.own_point(p)) in (None, True)),
   "🔴 exactly the picks the Game Lines tab's own printed score agrees with: the list and the tab use one score")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE CARD'S GAME LINES: THE ALTERNATE IS THE BEST RUNG THE PREDICTED MARGIN COVERS")
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
   [("Texas Longhorns", "alternate_spread", -9.5), ("Texas Longhorns", "spread", -6.5), ("Under", "total", 49.5)],
   "🔴 Purdue -3.5 goes (a predicted 1.2); Under 49.5 on a predicted 46.8 stays; Texas -6.5 stays (10.8), and "
   "its alternate is -9.5, the best rung the predicted margin covers, never the richer -12.5 it does not")
eq([O.score_side_ok(r, O.scores_by_names(WIN)(r), r["line"]) for r in GL], [True] * len(GL),
   "   ...the guard on the card's real output: every row on the predicted score's side")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 A SAME-GAME PARLAY'S LINE LEG: EACH GAME'S BEST LEG ON THE SCORE'S SIDE")
# ══════════════════════════════════════════════════════════════════════
def snap_game(gid, away, home):
    """The richest gap is the home spread -3.5 (+120 vs -110); the Over 49.5 has a smaller one and the
    Under 49.5 a smaller one still."""
    books = {}
    for bk, hp, op, up in (("fanduel", 120, -105, -102), ("draftkings", -110, -115, -110),
                           ("hardrockbet", -110, -115, -110)):
        books[bk] = {"spreads": {away: {"px": -110, "pt": 3.5}, home: {"px": hp, "pt": -3.5}},
                     "totals": {"Over": {"px": op, "pt": 49.5}, "Under": {"px": up, "pt": 49.5}}}
    return {"id": gid, "away": away, "home": home, "commence": KICK, "books": books}


_snap = {"games": [snap_game("ev1", WASH, PUR)]}
_win = O.by_names(WIN)
_free, _ = CF.build_game_lines(_snap, n=None, slate=CF.et_date(KICK), winner=_win)
_ruled, _ = CF.build_game_lines(_snap, n=None, slate=CF.et_date(KICK), winner=_win, score=O.scores_by_names(WIN))
eq(([(r["market"], r["side"], r["point"]) for r in _free], [(r["market"], r["side"], r["point"]) for r in _ruled]),
   ([("spreads", PUR, -3.5)], [("totals", "Under", 49.5)]),
   "🔴 the richest allowed leg is Purdue -3.5; on a predicted Purdue-by-1.2 it goes, the Over 49.5 (a "
   "predicted 46.8) cannot stand in, and the game's best leg ON the score's side, the Under 49.5, does")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE REAL card_fb.main HANDS THE PARLAY BUILDER THE MODEL'S SCORES")
# ══════════════════════════════════════════════════════════════════════
import datetime  # noqa: E402
import gzip  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from tcheck import shown  # noqa: E402
SEA, DEN = "Seattle Seahawks", "Denver Broncos"
_n = datetime.datetime.now(datetime.timezone.utc)
_K5 = (_n + datetime.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
_who5 = ["Rec One", "Rec Two", "Rec Three"]


def snap5(gid, away, home, at):
    """Three books. The richest price gap is DENVER -3.5 (+120 against -110); Denver's moneyline
    has a smaller one; the totals have none."""
    books = {}
    for bk, hp, hm in (("fanduel", 120, -150), ("draftkings", -110, -170), ("hardrockbet", -110, -170)):
        books[bk] = {"spreads": {away: {"px": -110, "pt": 3.5}, home: {"px": hp, "pt": -3.5}},
                     "h2h": {away: {"px": 140}, home: {"px": hm}},
                     "totals": {"Over": {"px": -110, "pt": 40.5}, "Under": {"px": -110, "pt": 40.5}}}
    return {"id": gid, "away": away, "home": home, "commence": at, "books": books}


def put(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with (gzip.open(path, "wt", encoding="utf-8") if path.endswith(".gz") else open(path, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


_T5 = tempfile.mkdtemp(prefix="scorecard-")
try:
    _L = os.path.join(_T5, "data", "nfl", "latest")
    put(os.path.join(_L, "props.json.gz"), {"pulled_at": (_n - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "games": [{"id": "ev1", "away": SEA, "home": DEN, "commence": _K5, "props": [
            {"player": w, "market": "player_receptions", "line": 3.5,
             "sides": {"over": {"price": -110, "book": "fanduel", "n_books": 3}}} for w in _who5]}]})
    put(os.path.join(_L, "players-2025.json.gz"), {"season": 2025, "players": {
        str(i): {"name": w, "pos": "WR", "g": [{"d": "2025-09-%02d" % (j + 7), "snap_pct": 0.9, "rec": 5}
                                               for j in range(10)]} for i, w in enumerate(_who5)}})
    # Denver is the expected winner, by only 2: its -3.5 is OFF the predicted score's side
    put(os.path.join(_L, "fb-model.json"), {"built_at": NOW, "picks": [],
        "win_chances": [{"game_id": "s1", "commence": _K5, "away": SEA, "home": DEN, "p_home": 55.0, "p_away": 45.0,
                         "best_ml": {}, "score": {"home": 20.0, "away": 18.0}}]})
    put(os.path.join(_T5, "data", "nfl", _n.strftime("%Y-%m-%d"), "gamelines", "0100.json.gz"),
        {"pulled_at": _n.strftime("%Y-%m-%dT%H:%M:%SZ"), "games": [snap5("ev1", SEA, DEN, _K5)]})
    _q = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, %r); import card_fb; card_fb.main()" % ROOT],
                        cwd=_T5, capture_output=True, text=True, encoding="utf-8", timeout=900,
                        env=dict(os.environ, PYTHONUTF8="1", LEAGUE="nfl"))
    try:
        CARD5 = json.load(open(os.path.join(_T5, "picks", "fb-nfl-latest.json"), encoding="utf-8"))
    except (OSError, ValueError):
        CARD5 = {}
        print(shown(_q.stdout[-1500:]), shown(_q.stderr[-1500:]))
finally:
    shutil.rmtree(_T5, ignore_errors=True)
_legs5 = [leg for size in (CARD5.get("sgp") or {}).values() for x in size if x.get("n_line_legs")
          for leg in x.get("legs") or []]
ck(any(DEN in leg for leg in _legs5),
   "⚠️ the planted card was built, with same-game parlays carrying a Denver line leg",
   "%s; rc %s" % (_legs5[:6], _q.returncode))
ck(not any("-3.5" in leg and DEN in leg for leg in _legs5),
   "🔴 the real card's same-game parlays never carry Denver -3.5 (its richest price gap) on a predicted "
   "Denver-by-2: main hands the leg builder the model's own scores", str(_legs5[:6]))
