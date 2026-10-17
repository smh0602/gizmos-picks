#!/usr/bin/env python3
"""test_one_side_score.py — every football spread and total pick comes FROM the predicted score.

`[Sam, 2026-10-16]` The predicted score comes from the moneyline and total fits, and each spread
pick came from a separate fit: 13 of 66 college spread and total picks sat on the side the
model's own score said loses (Purdue -3.5 beside "Purdue by 1.2"). Sam first chose "Must match
the score", then: "we need our gizmo picks to directly correlate to what our predicted scores
are, so if your saying that purdue will win 25-23, that means gizmos picks should like the +3.5
spread for washington" -> "Yes, everywhere": the side the score covers, the chance from that same
score, replacing the spread and total fits; the moneyline stays the expected winner. Planted
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
# @vacuity 🔴 the model's spread / total pick is the side the predicted score COVERS
#   file: fb_model.py
#   find:         side, px, p = (hi, pa, p_hi) if d > 0 else (lo, pb, 1.0 - p_hi)
#   with:         side, px, p = (lo, pb, 1.0 - p_hi) if d > 0 else (hi, pa, p_hi)
#
# @vacuity 🔴 ...its chance comes from that same score
#   file: fb_model.py
#   find:         p_hi = statistics.NormalDist().cdf(d / sigma)
#   with:         p_hi = 0.6
#
# @vacuity 🔴 ...and landing ON the line is no pick (rounded, no float error)
#   file: fb_model.py
#   find:         d = round(mu - ln, 6)                     # the spread's line is M on the HOME margin
#   with:         d = mu - ln
#
# @vacuity 🔴 ...and only when its price pays (value above zero, as every model pick)
#   file: fb_model.py
#   find:     return best if best is not None and best["ev"] > 0 else None    # the value rule, as best_pick
#   with:     return best
#
# @vacuity 🔴 the live pick list takes its spreads and totals from the score, never the fits
#   file: fb_model.py
#   find:             pk = (score_pick(r, mk, sc[r["id"]], sigma if mk == "spread" else sigma_t)
#   with:             pk = (best_pick(r, mk, models[mk])
#
# @vacuity 🔴 the card's game lines and alternate spreads are judged by the score
#   file: card_fb.py
#   find:     rows, _ = one_side.score_keep(rows + alt_spread_rows(rows, ladder, _score, sigma), _score)
#   with:     rows = rows + alt_spread_rows(rows, ladder, _score, sigma)
#
# @vacuity 🔴 an alternate rung's chance comes from the predicted score
#   file: card_fb.py
#   find:         sc = score(r) if (score is not None and sigma) else None
#   with:         sc = None
#
# @vacuity 🔴 ...ranked by its VALUE at that chance (EV %, the ladder's own `edge`), never the points gap
#   file: card_fb.py
#   find:                                      edge=(round(100 * (_q(x) * decimal_odds(x["best"]) - 1.0), 1)
#   with:                                      edge=(round(100 * _q(x) - x["be"], 1)
#
# @vacuity 🔴 a same-game parlay's SPREAD leg is never judged by the expected winner (it follows the score)
#   file: card_fb.py
#   find:             if winner is not None and market == "h2h" and not one_side.keep([row], winner)[0]:
#   with:             if winner is not None and not one_side.keep([row], winner)[0]:
#
# @vacuity 🔴 the alternate spread is the best rung the predicted score COVERS
#   file: card_fb.py
#   find:               and (score is None or one_side.score_side_ok(
#   with:               and (True or one_side.score_side_ok(
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
#
# @vacuity 🔴 ...and the alternate spreads the score's spread (sigma)
#   file: card_fb.py
#   find:                                  sigma=((_model.get("pricing") or {}).get("sigma") or {}).get("spread"))
#   with:                                  sigma=None)
#
# @vacuity 🔴 the why prints a predicted score only when it lands on the pick's side, never on the number
#   file: fb_why.py
#   find:         return r.get("line") is not None and round(m + float(r["line"]), 6) > 0
#   with:         return r.get("line") is not None and m + float(r["line"]) > 0
"""
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "ncaaf")
import one_side as O  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

WASH, PUR, FLA, TEX = "Washington Huskies", "Purdue Boilermakers", "Florida Gators", "Texas Longhorns"
S = {"home": 24.0, "away": 22.8}             # Purdue (home) by 1.2, 46.8 points
N = statistics.NormalDist()

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
section("2. 🔴 THE MODEL'S SPREAD AND TOTAL PICKS COME FROM THE PREDICTED SCORE")
# ══════════════════════════════════════════════════════════════════════
import fb_model as FM  # noqa: E402
_q = lambda *qs: (lambda r, mk: list(qs))  # noqa: E731
_sam = FM.score_pick({}, "spread", {"home": 25.0, "away": 23.0}, 13.0, quotes=_q(("fanduel", 3.5, -110, -110, False)))
eq((_sam or {}).get("side"), "away",
   "🔴 Sam's game: a predicted Purdue 25-23 picks Washington +3.5 (the line is M = 3.5 on Purdue's margin)")
ck(_sam and abs(_sam["p"] - (1 - N.cdf(-1.5 / 13.0))) < 1e-9,
   "🔴 ...at the chance that same score gives it: P(Purdue wins by under 3.5) on Normal(2, 13)", str(_sam))
eq([FM.score_pick({}, "spread", {"home": 14.1, "away": 21.1}, 13.0, quotes=_q(("fd", -7.0, 110, 110, False))),
    FM.score_pick({}, "spread", {"home": 25.0, "away": 23.0}, None, quotes=_q(("fd", 3.5, -110, -110, False))),
    FM.score_pick({}, "spread", None, 13.0, quotes=_q(("fd", 3.5, -110, -110, False))),
    FM.score_pick({}, "spread", {"home": 25.0, "away": 23.0}, 13.0, quotes=_q(("fd", 3.5, -400, -400, False)))],
   [None, None, None, None],
   "🔴 no pick ON the number (Tulane by 7.0 on -7, a float 1.8e-15 off), none without a spread or a score, "
   "and none when the price does not pay (the value check, as every model pick)")
_tot = FM.score_pick({}, "total", {"home": 25.0, "away": 23.0}, 10.0, quotes=_q(("fd", 50.5, -110, -110, False)))
eq(((_tot or {}).get("side"), round((_tot or {}).get("p", 0), 6)), ("under", round(1 - N.cdf(-2.5 / 10.0), 6)),
   "🔴 a total from the predicted 48 points: the Under 50.5, at that score's chance")

NOW, KICK = "2026-10-16T08:00:00Z", "2026-10-17T19:30:00Z"
FIN = [{"id": "f%d" % i, "final": True, "hs": hs, "as": as_, "sig": {"own_m": 0.0, "own_t": 45.0}, "snap": None}
       for i, (hs, as_) in enumerate(((31, 15), (15, 31), (35, 24), (24, 35)))]
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
# each fit's own chance for the HOME side; the spread fit leans the OTHER way on purpose
P_FIT = {("g1", "moneyline"): 0.529, ("g1", "total"): 0.55, ("g1", "spread"): 0.8,
         ("g2", "moneyline"): 0.75, ("g2", "total"): 0.60, ("g2", "spread"): 0.2,
         ("g3", "moneyline"): 0.25, ("g3", "total"): 0.5, ("g3", "spread"): 0.8,
         ("g4", "moneyline"): 0.25, ("g4", "total"): 0.5, ("g4", "spread"): 0.2}
# the books' lines; a spread's line is M on the HOME margin (home -3.5 is M = 3.5)
QUOTES = {("g1", "moneyline"): [("fanduel", None, 110, -130, False)],
          ("g1", "spread"): [("fanduel", 3.5, -110, -110, False)],
          ("g1", "total"): [("fanduel", 47.5, -110, -110, False)],
          ("g2", "spread"): [("fanduel", 6.5, -110, -110, False), ("draftkings", 11.5, -110, -110, False)],
          ("g3", "spread"): [("fanduel", -6.5, -110, -110, False)],
          ("g4", "spread"): [("fanduel", -12.5, -110, -110, False)]}
_saved = {n: getattr(FM, n) for n in ("features", "label", "fit", "predict", "best_pick", "book_quotes")}
try:
    FM.features = lambda r, mk, **k: (r["id"], mk)
    FM.label = lambda r, mk: 1
    FM.fit = lambda xs, ys, **k: {"n": len(xs)}
    FM.predict = lambda m, x: P_FIT.get(x, 0.5)
    FM.book_quotes = lambda r, mk: QUOTES.get((r["id"], mk), [])
    # the real best_pick (the moneyline), at the planted quotes (its default binds the real reader)
    FM.best_pick = lambda r, mk, model, quotes=None: _saved["best_pick"](r, mk, model, quotes=quotes or FM.book_quotes)
    CUR = FM.current_picks("ncaaf", ROWS, now=NOW)
    WCH = FM.win_chances(ROWS, now=NOW)
    SIG, SIGT = FM.score_sigma(ROWS), FM.total_sigma(ROWS)
finally:
    for n, f in _saved.items():
        setattr(FM, n, f)
SC = {w["game_id"]: w.get("score") for w in WCH}
_m = {g: SC[g]["home"] - SC[g]["away"] for g in SC}
ck(0 < _m.get("g1", 9) < 3.5 and SC["g1"]["home"] + SC["g1"]["away"] > 47.5 and 6.5 < _m.get("g2", 0) < 11.5
   and -12.5 < _m.get("g3", 0) < -6.5,
   "⚠️ the case exists: the Game Lines tab's score has Purdue winning by under 3.5 with more than 47.5 points, "
   "Texas by between 6.5 and 11.5, and the road teams by between 6.5 and 12.5", str(SC))
_by = {(p["game_id"], p["market"]): p for p in CUR}
_v = lambda x: x.get("value") if isinstance(x, dict) else x  # noqa: E731
eq(sorted((g, mk, p["side"], _v(p["line"])) for (g, mk), p in _by.items()),
   sorted([("g1", "moneyline", "home", None), ("g1", "spread", "away", 3.5), ("g1", "total", "over", 47.5),
           ("g2", "spread", "home", 6.5), ("g3", "spread", "away", -6.5), ("g4", "spread", "home", -12.5)]),
   "🔴 the real pick list: Purdue to win (the expected winner), WASHINGTON +3.5 and the Over 47.5 (the "
   "predicted score), Texas -6.5 (by 9; Florida +11.5 at the other book is covered too, at a lower chance), the road "
   "favourite -6.5 (by 9), and the HOME team +12.5 against a road favourite predicted by only 9 — the spread "
   "fit, which leans the other way in every game, decides none of them")
_want = {("g1", "spread"): 1 - N.cdf(round(_m["g1"] - 3.5, 6) / SIG),
         ("g1", "total"): N.cdf(round(SC["g1"]["home"] + SC["g1"]["away"] - 47.5, 6) / SIGT),
         ("g2", "spread"): N.cdf(round(_m["g2"] - 6.5, 6) / SIG)}
eq({k: _v(_by[k]["model_probability"]) for k in _want if k in _by}, {k: round(100 * v, 1) for k, v in _want.items()},
   "🔴 each chance is the printed score's own: Normal(predicted margin or total, the model's own spread of "
   "results), the same numbers the Game Lines tab shows")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE CARD'S GAME LINES AND ALTERNATE SPREADS FOLLOW THE SCORE")
# ══════════════════════════════════════════════════════════════════════
import card_fb as CF  # noqa: E402


def mp(away, home, mk, side, team, line, px, p):
    return {"game": "%s at %s" % (away, home), "commence": KICK, "market": mk, "side": side, "team": team,
            "book": "fanduel", "line": {"value": line}, "price": {"value": px},
            "model_probability": {"value": p}, "break_even": {"value": 50.0}, "priced_at": NOW}


WIN = [{"away": WASH, "home": PUR, "p_home": 52.9, "score": {"home": 24.0, "away": 22.8}},
       {"away": FLA, "home": TEX, "p_home": 75.0, "score": {"home": 30.9, "away": 20.1}}]
RUNG = lambda side, pt, edge, p=62.0, best=-150, be=60.0: {"side": side, "best": best, "p": p, "pt": pt,  # noqa: E731
                                                           "edge": edge, "be": be, "book": "fanduel"}
LAD = {"games": [{"away": FLA, "home": TEX, "commence": KICK, "main_spread_home": -6.5,
                  "spread": [RUNG("home", -12.5, 4.0), RUNG("home", -9.5, 2.0)]}]}
# a file pick off the score (Purdue -3.5 on a predicted 1.2) never shows, one on it does
_picks = [mp(WASH, PUR, "spread", "home", PUR, 3.5, -110, 57.5), mp(WASH, PUR, "total", "under", "Under", 49.5, -110, 53.0),
          mp(FLA, TEX, "spread", "home", TEX, 6.5, -110, 56.0)]
GL = CF.card_game_lines(_picks, [], LAD, CF.et_date(KICK), win_chances=WIN)
eq(sorted((r["player"], r["market"], r["line"]) for r in GL),
   [("Texas Longhorns", "alternate_spread", -9.5), ("Texas Longhorns", "spread", -6.5), ("Under", "total", 49.5)],
   "🔴 Purdue -3.5 goes (a predicted 1.2); Under 49.5 on a predicted 46.8 stays; Texas -6.5 stays (10.8), and "
   "its alternate is -9.5, the best rung the predicted margin covers, never the richer -12.5 it does not")
# with the score's spread (sigma) each rung's chance comes FROM the score
LAD2 = {"games": [{"away": FLA, "home": TEX, "commence": KICK, "main_spread_home": -6.5,
                   "spread": [RUNG("home", -12.5, 4.0, p=62.0, best=-100, be=50.0),
                              RUNG("home", -7.5, 1.0, p=51.0, best=-100, be=50.0)]}]}
GL2 = CF.card_game_lines(_picks, [], LAD2, CF.et_date(KICK), win_chances=WIN, sigma=13.0)
_alt = [r for r in GL2 if r["market"] == "alternate_spread"]
eq([(r["line"], r["confidence"]) for r in _alt], [(-7.5, int(round(round(100 * N.cdf(round(10.8 - 7.5, 6) / 13.0), 1))))],
   "🔴 the alternate's chance is the predicted score's (Texas by 10.8 covers -7.5 about 60% of the time), "
   "never the ladder's 51%; and -12.5, which the score gives under half, never shows")
# two covered rungs where the points gap and the VALUE disagree (Texas by 10.8, sigma 13): -1.5 at
# -165 is 76.3% against 62.3 (14.0 points, value +22.5%); -7.5 at +113 is 60.0% against 46.9
# (13.1 points, value +27.8%). Sam's rule is the highest VALUE (`[Sam, 2026-10-11]`).
LAD3 = {"games": [{"away": FLA, "home": TEX, "commence": KICK, "main_spread_home": -6.5,
                   "spread": [RUNG("home", -1.5, 0.0, p=0.0, best=-165, be=62.3),
                              RUNG("home", -7.5, 0.0, p=0.0, best=113, be=46.9)]}]}
GL3 = CF.card_game_lines(_picks, [], LAD3, CF.et_date(KICK), win_chances=WIN, sigma=13.0)
eq([(r["line"], r["price"]) for r in GL3 if r["market"] == "alternate_spread"], [(-7.5, 113)],
   "🔴 the alternate is the rung with the highest VALUE at the score's chance (-7.5 at +113, +27.8%), "
   "never the bigger points gap (-1.5 at -165, +22.5%): the same value rule as the main pick")
eq([O.score_side_ok(r, O.scores_by_names(WIN)(r), r["line"]) for r in GL + GL2], [True] * len(GL + GL2),
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



def snap_dog(gid, away, home):
    """The richest gap is the AWAY spread +3.5 (+120 against -110), the expected LOSER's; the
    away moneyline has a smaller one; the home side and the totals have none."""
    books = {}
    for bk, ap in (("fanduel", 120), ("draftkings", -110), ("hardrockbet", -110)):
        books[bk] = {"spreads": {away: {"px": ap, "pt": 3.5}, home: {"px": -110, "pt": -3.5}},
                     "h2h": {away: {"px": 170 if bk == "fanduel" else 150}, home: {"px": -170}},
                     "totals": {"Over": {"px": -110, "pt": 47.5}, "Under": {"px": -110, "pt": 47.5}}}
    return {"id": gid, "away": away, "home": home, "commence": KICK, "books": books}


_WS = [{"away": WASH, "home": PUR, "p_home": 55.0, "score": {"home": 25.0, "away": 23.0}}]
_dog, _ = CF.build_game_lines({"games": [snap_dog("ev2", WASH, PUR)]}, n=None, slate=CF.et_date(KICK),
                              winner=O.by_names(_WS), score=O.scores_by_names(_WS))
eq([(r["market"], r["side"], r["point"]) for r in _dog], [("spreads", WASH, 3.5)],
   "🔴 Sam's game as a same-game parlay leg: Purdue 25-23 => Washington +3.5 (its richest gap) is the line "
   "leg; a spread leg follows the score and is never judged by the expected winner (Purdue)")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE REAL card_fb.main HANDS THE PARLAY BUILDER THE SCORES, THE ALTERNATES THE SIGMA")
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
    # Denver is the expected winner, by only 2: its -3.5 is OFF the predicted score's side and
    # Seattle +3.5, the model's pick, ON it
    put(os.path.join(_L, "fb-model.json"), {"built_at": NOW, "pricing": {"sigma": {"spread": 13.0, "total": 10.0}},
        "picks": [{"game": "%s at %s" % (SEA, DEN), "commence": _K5, "market": "spread", "side": "away", "team": SEA,
                   "book": "FanDuel", "line": {"value": 3.5}, "price": {"value": -110},
                   "model_probability": {"value": 56.0}, "break_even": {"value": 52.4}, "priced_at": NOW}],
        "win_chances": [{"game_id": "s1", "commence": _K5, "away": SEA, "home": DEN, "p_home": 55.0, "p_away": 45.0,
                         "best_ml": {}, "score": {"home": 20.0, "away": 18.0}}]})
    # the ladder: Seattle +6.5 at -150, which the old curve gives 40% (no row); a predicted
    # Denver-by-2 gives it 63.5%
    put(os.path.join(_L, "game-lines.json.gz"), {"built_at": NOW, "games": [
        {"away": SEA, "home": DEN, "commence": _K5, "main_spread_home": -3.5,
         "spread": [{"side": "away", "best": -150, "p": 40.0, "pt": 6.5, "edge": -20.0, "be": 60.0,
                     "book": "fanduel"}]}]})
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
_gl5 = sorted((r.get("market"), r.get("player"), r.get("line"), r.get("confidence")) for r in CARD5.get("game_lines") or [])
eq(_gl5, sorted([("spread", SEA, 3.5, 56),
                 ("alternate_spread", SEA, 6.5, int(round(round(100 * N.cdf(round(-2.0 + 6.5, 6) / 13.0), 1))))]),
   "🔴 the real card: Seattle +3.5 (on a predicted Denver-by-2) and its alternate +6.5 at the chance that same "
   "score gives it (main hands it fb-model.json's sigma), never the old curve's 40%")
