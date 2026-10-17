#!/usr/bin/env python3
r"""test_one_side.py — ONE TEAM PER GAME: every side pick is on the model's expected winner.

`[Sam, 2026-10-16]` "i noticed that the model picked huskies on the moneyline for college
foootbal but also picked the -3.5 spread for purdue; the huskies opponent. these two picks
go directly against one another and we can't have our model choosing both sides at once"
— "fixed as whole for all leagues so it doesn't happen again". Asked which side stays, he
chose the EXPECTED WINNER (the Game Lines tab's pick to win). Every builder of a list of
side picks is driven here on a planted both-sides game, and §8 builds a WHOLE football
card and checks every list on it (MLB's card rows: test_mlb_game_lines.py). Planted data
only; ⛔ reads nothing live.

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
# @vacuity 🔴 a side pick whose team cannot be told is dropped (fail closed)
#   file: one_side.py
#   find:         (kept if b is None or (b != "?" and b == winner(r)) else dropped).append(r)
#   with:         (kept if b is None or b == "?" or b == winner(r) else dropped).append(r)
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
# @vacuity 🔴 the guard names a game whose pick's team cannot be told
#   file: one_side.py
#   find:         elif winner is not None and any(b == "?" or b != winner(r) for b, r in picks):
#   with:         elif winner is not None and any(b != "?" and b != winner(r) for b, r in picks):
#
# @vacuity 🔴 the Game Lines tab names its winner with the shared rule
#   file: winners.py
#   find:     side = one_side.expected_side(p_home)
#   with:     side = "home"
#
# @vacuity 🔴 the football model's pick list keeps only the expected winner's moneyline
#   file: fb_model.py
#   find:     return pk if pk and pk["side"] == one_side.expected_side(ph) else None
#   with:     return pk
#
# @vacuity 🔴 ...and a game with no win chance keeps no side pick
#   file: card_fb.py
#   find:     rows = one_side.keep(_ml, one_side.by_names(win_chances))[0] + [r for r in rows if r.get("market") != "moneyline"]
#   with:     rows = one_side.keep(_ml, lambda r: one_side.by_names(win_chances)(r) or r.get("side"))[0] + [r for r in rows if r.get("market") != "moneyline"]
#
# @vacuity 🔴 ...and the expected winner is the MONEYLINE fit's pick to win, as win_chances'
#   file: fb_model.py
#   find:     ph = round(100 * predict(m, features(r, "moneyline")), 1) if m else None
#   with:     ph = round(100 * predict(models["spread"], features(r, "spread")), 1) if models.get("spread") else None
#
# @vacuity 🔴 the card's game lines keep only the expected winner's moneyline
#   file: card_fb.py
#   find:     rows = one_side.keep(_ml, one_side.by_names(win_chances))[0] + [r for r in rows if r.get("market") != "moneyline"]
#   with:     rows = _ml + [r for r in rows if r.get("market") != "moneyline"]
#
# @vacuity 🔴 ...an empty win-chance list (no expected winner) keeps no side row
#   file: card_fb.py
#   find:     if win_chances is None:
#   with:     if not win_chances:
#
# @vacuity 🔴 ...and the filter runs before the 25-row cap and the ranks
#   file: card_fb.py
#   find:     return order_game_lines(rows)
#   with:     return one_side.score_keep(order_game_lines(model_game_rows(model_picks, games, slate)), one_side.scores_by_names(win_chances))[0]
#
# @vacuity 🔴 the card is given the model file's win chances
#   file: card_fb.py
#   find:                                  win_chances=_model.get("win_chances") or [],
#   with:                                  win_chances=None,
#
# @vacuity 🔴 a same-game parlay's line leg is each game's best ALLOWED row
#   file: card_fb.py
#   find:             if winner is not None and market == "h2h" and not one_side.keep([row], winner)[0]:
#   with:             if False:
#
# @vacuity 🔴 ...and the card hands the leg builder the expected winners
#   file: card_fb.py
#   find:                                          winner=one_side.by_names(_model.get("win_chances") or []),
#   with:                                          winner=None,
#
# @vacuity 🔴 the MLB verifier fails a card that backs both teams of a game
#   file: verify_card.py
#   find:    not _gcf, str(_gcf[:3]))
#   with:    True, str(_gcf[:3]))
#
# @vacuity 🔴 a published MLB row is re-judged after a game-model rebuild
#   file: card.py
#   find:     kept, gone = one_side.keep(judged, lambda r: win.get(r.get("game_pk")))
#   with:     kept, gone = judged, []
#
# @vacuity 🔴 ...but a started row stays exactly as published
#   file: card.py
#   find:     started = [r for r in rows if r.get("commence") and _iso(r["commence"]) <= now]
#   with:     started = []
#
# @vacuity 🔴 ...and a game the rebuilt model does not hold is left alone
#   file: card.py
#   find:     judged = [r for r in rows if r not in started and r.get("game_pk") in win]
#   with:     judged = [r for r in rows if r not in started]
#
# @vacuity 🔴 the collector's game-model rebuild re-judges the published card
#   file: collect.py
#   find:             _gone = _card.refilter_game_lines(os.path.join(PICKS, "%s.json" % _slate), _gmod, now())
#   with:             _gone = 0
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
os.environ.setdefault("LEAGUE", "ncaaf")
import one_side as O  # noqa: E402
from tcheck import ck, eq, section, shown  # noqa: E402

WASH, PUR, FLA, TEX = "Washington Huskies", "Purdue Boilermakers", "Florida Gators", "Texas Longhorns"
UTC = datetime.timezone.utc

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
   "tell ('?')")
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
_unk = {"market": "spreads", "side": "Somebody Else", "game": "%s @ %s" % (WASH, PUR)}
eq((O.keep([_unk], lambda r: "away"), O.conflicts([_unk], winner=lambda r: "away")),
   (([], [_unk]), [("%s @ %s" % (WASH, PUR), "a pick on the team the model does not expect to win")]),
   "🔴 a side pick whose team cannot be told is dropped even when its game has an expected winner (fail "
   "closed), and the guard names its game")

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
ROWS = [{"id": "g1", "final": False, "sig": {}, "snap": {"commence": KICK, "names": (PUR, WASH), "pulled_at": NOW}},
        {"id": "g2", "final": False, "sig": {}, "snap": {"commence": KICK, "names": (TEX, FLA), "pulled_at": NOW}}]
# `[Sam, 2026-10-16]` "Must match the score": each game's predicted score, on the side of
#    the picks that should stay (Purdue by 5, 49 points; Florida by 7)
SCORE = {"g1": {"home": 27.0, "away": 22.0}, "g2": {"home": 20.0, "away": 27.0}}
# each fit's own chance for the HOME side; the spread and total fits lean the other way on
# purpose, so an expected winner taken from any fit but the moneyline's is caught
P_FIT = {("g1", "moneyline"): 0.512, ("g1", "spread"): 0.400, ("g1", "total"): 0.300,
         ("g2", "moneyline"): 0.300, ("g2", "spread"): 0.650, ("g2", "total"): 0.700}
PICKS = {("g1", "moneyline"): ("away", None, 150, 0.488), ("g1", "spread"): ("home", 3.5, -110, 0.558),
         ("g1", "total"): ("under", 50.5, -110, 0.562),
         ("g2", "moneyline"): ("away", None, 120, 0.700), ("g2", "spread"): ("home", 6.5, -110, 0.560)}


def _bp(r, mk, model, quotes=None):
    if not model:
        return None
    v = PICKS.get((r["id"], mk))
    if not v:
        return None
    side, ln, px, p = v
    dec = 1 + (px / 100.0 if px > 0 else 100.0 / -px)
    return {"side": side, "book": "fanduel", "line": ln, "price": px, "p": p, "ev": p * dec - 1,
            "break_even": 1 / dec, "assumed": False}


# `[Sam, 2026-10-16]` the spread and total picks come FROM the predicted score at these quotes
QUOTES = {("g1", "spread"): [("fanduel", 3.5, -110, -110, False)], ("g1", "total"): [("fanduel", 50.5, -110, -110, False)],
          ("g2", "spread"): [("fanduel", -6.5, -110, 100, False)]}
_saved = {n: getattr(FM, n) for n in ("features", "label", "fit", "predict", "best_pick", "book_quotes",
                                      "predicted_score", "score_sigma", "total_sigma")}
try:
    FM.features = lambda r, mk, **k: (r["id"], mk)
    FM.label = lambda r, mk: 1
    FM.fit = lambda xs, ys, **k: {"n": len(xs)}
    FM.predict = lambda m, x: P_FIT[x]
    FM.best_pick = _bp
    FM.book_quotes = lambda r, mk: QUOTES.get((r["id"], mk), [])
    FM.predicted_score = lambda r, p, sigma, p_over=None, sigma_t=None: SCORE[r["id"]]
    FM.score_sigma = FM.total_sigma = lambda rows: 13.0
    CUR = FM.current_picks("ncaaf", ROWS, now=NOW)
    WCH = FM.win_chances(ROWS, now=NOW, scores=False)
    FM.fit = lambda xs, ys, **k: None if xs and xs[0][1] == "moneyline" else {"n": len(xs)}
    CUR0 = FM.current_picks("ncaaf", ROWS, now=NOW)
finally:
    for n, f in _saved.items():
        setattr(FM, n, f)
_tab = {w["game_id"]: O.expected_side(w["p_home"]) for w in WCH}
eq(_tab, {"g1": "home", "g2": "away"}, "⚠️ the Game Lines tab's numbers (win_chances): Purdue, and Florida at 70%")
eq(sorted((p["game_id"], p["market"], p["team"]) for p in CUR),
   [("g1", "spread", PUR), ("g1", "total", "Under"), ("g2", "moneyline", FLA), ("g2", "spread", FLA)],
   "🔴 Washington ML +150 beside Purdue -3.5 (Sam's game): Washington's moneyline is gone (Purdue is the "
   "expected winner); Purdue -3.5 and the Under come from the predicted score (Purdue by 5, 49 points); "
   "Florida keeps its moneyline, and its -6.5 comes from the score too (Florida by 7)")
_v3 = lambda x: x.get("value") if isinstance(x, dict) else x  # noqa: E731
_pt3 = lambda p: ((-_v3(p["line"]) if p["side"] == "home" else _v3(p["line"]))  # noqa: E731
                  if p["market"] == "spread" else _v3(p["line"]))
eq([p for p in CUR if (p["market"] == "moneyline" and p["side"] != _tab.get(p["game_id"]))
    or O.score_side_ok(p, SCORE[p["game_id"]], _pt3(p)) is False], [],
   "🔴 the guard on the real builder's output, against the tab's own win chances and score: every "
   "moneyline on the expected winner, every spread and total on the predicted score's side "
   "(`[Sam, 2026-10-16]` ~~no game backs both teams~~: Purdue 25-23 => Washington +3.5)")
eq(sorted(p["market"] for p in CUR0), [],
   "🔴 with no moneyline fit there is no expected winner, so no side pick at all; and no predicted "
   "score either, so `[Sam, 2026-10-16]` ~~a total stays~~ the total goes too")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE CARD'S GAME LINES, THE ALTERNATE SPREAD, THE 25-ROW CAP")
# ══════════════════════════════════════════════════════════════════════
import card_fb as CF  # noqa: E402


def mp(away, home, mk, side, team, line, px, p, at=KICK):
    return {"game": "%s at %s" % (away, home), "commence": at, "market": mk, "side": side, "team": team,
            "book": "fanduel", "line": {"value": line}, "price": {"value": px},
            "model_probability": {"value": p}, "break_even": {"value": 50.0}, "priced_at": NOW}


MODEL_PICKS = [mp(WASH, PUR, "moneyline", "away", WASH, None, 150, 52.0),     # 52: clears the 50% floor
               mp(WASH, PUR, "spread", "home", PUR, 3.5, -110, 55.8),
               mp(WASH, PUR, "total", "under", "Under", 50.5, -110, 56.2),
               mp(FLA, TEX, "spread", "away", FLA, 11.5, -110, 53.0),          # Texas is the expected winner
               mp(FLA, TEX, "moneyline", "home", TEX, None, -300, 70.0)]
WIN = [{"away": WASH, "home": PUR, "p_home": 51.2, "score": {"home": 27.0, "away": 22.0}},
       {"away": FLA, "home": TEX, "p_home": 70.0, "score": {"home": 31.0, "away": 20.0}}]
RUNG = lambda side, pt: {"side": side, "best": -150, "p": 62.0, "pt": pt, "edge": 2.0, "be": 60.0, "book": "fanduel"}  # noqa: E731
LADDER = {"games": [{"away": WASH, "home": PUR, "commence": KICK, "main_spread_home": -3.5,
                     "spread": [RUNG("home", -1.5), RUNG("away", 7.5)]},
                    {"away": FLA, "home": TEX, "commence": KICK, "main_spread_home": -11.5,
                     "spread": [RUNG("away", 17.5)]}]}
GL = CF.card_game_lines(MODEL_PICKS, [], LADDER, CF.et_date(KICK), win_chances=WIN)
eq(sorted((r["player"], r["market"], r["line"]) for r in GL),
   sorted([(PUR, "spread", -3.5), (PUR, "alternate_spread", -1.5), ("Under", "total", 50.5),
           (TEX, "moneyline", None), (FLA, "spread", 11.5), (FLA, "alternate_spread", 17.5)]),
   "🔴 Purdue -3.5 and its alternate -1.5, the Under, Texas to win, never Washington's moneyline; and "
   "`[Sam, 2026-10-16]` 'Yes, everywhere': a spread follows the predicted score (Purdue 25-23 => Washington "
   "+3.5): Texas is predicted by 11, so Florida +11.5 (and its +17.5) STAYS (~~Florida +11.5 goes~~)")
_bad = [r for r in GL if O.score_side_ok(r, O.scores_by_names(WIN)(r), r["line"]) is False
        or (r["market"] == "moneyline" and O.backs(r) != O.by_names(WIN)(r))]
eq(_bad, [], "🔴 the guard on the card's real output: every moneyline on the expected winner, every spread "
   "and total on the predicted score's side (~~one team per game~~: a Texas win and Florida +11.5 both land)")
eq(sorted(r["market"] for r in CF.card_game_lines(MODEL_PICKS, [], LADDER, CF.et_date(KICK), win_chances=[])),
   [], "🔴 an empty win-chance list names no expected winner and no predicted score: `[Sam, 2026-10-16]` "
   "~~only the total stays~~ nothing stays")
# 40 games, the home team expected in each; every 4th spread pick (the highest-confidence ones
# among them) is on the away team. 30 survive: the cap must be filled from those, ranked 1..25.
#    `[2026-10-16]` home by 2: every away +1.5 is OFF the predicted score's side (the score filter
#    removes it; ~~the one-team filter~~ no longer judges a spread), every home -1.5 on it.
_many = [mp("A%02d" % i, "H%02d" % i, "spread", "away" if i % 4 == 0 else "home",
            ("A%02d" % i) if i % 4 == 0 else ("H%02d" % i), 1.5, -110, 90.0 - i * 0.5)
         for i in range(40)]
_mwin = [{"away": "A%02d" % i, "home": "H%02d" % i, "p_home": 60.0, "score": {"home": 22.0, "away": 20.0}}
         for i in range(40)]
_cap = CF.card_game_lines(_many, [], {}, CF.et_date(KICK), win_chances=_mwin)
eq((len(_cap), [r["rank"] for r in _cap], sorted({r["side"] for r in _cap})),
   (min(CF.GAME_LINES_MAX, 30), list(range(1, min(CF.GAME_LINES_MAX, 30) + 1)), ["home"]),
   "🔴 the filter runs BEFORE the 25-row cap and the ranks: 25 home rows ranked 1..25, never fewer with gaps")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 A SAME-GAME PARLAY'S LINE LEG: EACH GAME'S BEST ALLOWED ROW")
# ══════════════════════════════════════════════════════════════════════
def snap_game(gid, away, home, at):
    """Three books. The richest price gap is AWAY +3.5 (+120 against -110), then the away
    moneyline (+170 against +150), then home's moneyline; the totals have none."""
    books = {}
    for bk, ap in (("fanduel", 120), ("draftkings", -110), ("hardrockbet", -110)):
        books[bk] = {"spreads": {away: {"px": ap, "pt": 3.5}, home: {"px": -110, "pt": -3.5}},
                     "h2h": {away: {"px": 170 if bk == "fanduel" else 150},
                             home: {"px": -160 if bk == "fanduel" else -170}},
                     "totals": {"Over": {"px": -110, "pt": 40.5}, "Under": {"px": -110, "pt": 40.5}}}
    return {"id": gid, "away": away, "home": home, "commence": at, "books": books}


_snap = {"games": [snap_game("ev1", WASH, PUR, KICK)]}
_free, _ = CF.build_game_lines(_snap, n=None, slate=CF.et_date(KICK))
_ruled, _ = CF.build_game_lines(_snap, n=None, slate=CF.et_date(KICK), winner=O.by_names(WIN),
                                score=O.scores_by_names(WIN))
eq(([(r["market"], r["side"]) for r in _free], [(r["market"], r["side"]) for r in _ruled]),
   ([("spreads", WASH)], [("h2h", PUR)]),
   "🔴 the richest leg is Washington +3.5, which a predicted Purdue-by-5 does not cover; the next, "
   "Washington to win, is not the expected winner; so the game keeps its best ALLOWED leg, Purdue to win")

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
win, rows = {"both": (60.0, [row("moneyline", "home", FUT), row("run_line", "away", FUT)]),
             "winner": (60.0, [row("moneyline", "home", FUT)]),
             "loser": (60.0, [row("run_line", "away", FUT)]),
             "road": (40.0, [row("moneyline", "away", FUT), row("run_line", "away", FUT)]),
             "road_home": (40.0, [row("moneyline", "home", FUT)]),
             "started": (60.0, [row("moneyline", "home", PAST), row("run_line", "away", PAST)])}[case]
for i, r in enumerate(rows, 1):
    r["rank"] = i
def main(*a, **k):
    C.LAST_GAME_MODEL.clear()
    C.LAST_GAME_MODEL.update({"games": [{"game_pk": 1, "win": {"home": win, "away": 100 - win}}]})
    return {"date": "2026-10-17", "picks": [], "below_price_floor": [], "pairs": [],
            "projections": {}, "top10": [], "top10_excluded": {}, "parlays": {}, "hitter_record_bands": [],
            "board_rule": {}, "board_seats": {}, "pitcher_correction": {}, "game_lines": rows}
C.main = main
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
    # ⛔ a STALE model on disk that names the OTHER team: the verifier must judge the model main() used
    json.dump({"games": [{"game_pk": 1, "win": {"home": 10.0, "away": 90.0}}]},
              open(os.path.join(_T, "data", "latest", "mlb-game-model.json"), "w", encoding="utf-8"))
    for _c in ("both", "winner", "loser", "road", "road_home", "started"):
        _q = subprocess.run([sys.executable, "-c", PLANT, _c], cwd=_T, capture_output=True, text=True,
                            encoding="utf-8", timeout=600, env=dict(os.environ, PYTHONUTF8="1"))
        _v[_c] = verdict(_q.stdout)
        if _v[_c] not in ("PASS", "FAIL"):
            print(shown(_q.stdout[-1200:]), shown(_q.stderr[-1200:]))
finally:
    shutil.rmtree(_T, ignore_errors=True)
eq(_v, {"both": "FAIL", "winner": "PASS", "loser": "FAIL", "road": "PASS", "road_home": "FAIL", "started": "PASS"},
   "🔴 the REAL verifier, on the model main() built the card from (never the stale file on disk): the "
   "favourite's moneyline beside the underdog +1.5 FAILS, the expected winner alone PASSES, a lone pick on "
   "the other team FAILS, a road favourite's rows PASS and its home team's FAIL, and a started pair (frozen "
   "as published) is not re-judged")

# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 THE PUBLISHED MLB CARD AFTER THE GAME MODEL IS REBUILT ON ITS OWN")
# ══════════════════════════════════════════════════════════════════════
import card as CA  # noqa: E402
_NOWDT = datetime.datetime(2026, 10, 17, 18, 0, tzinfo=UTC)


def pr(pk, side, at, mk="moneyline", conf=60.0):
    return {"kind": "mlb-line", "market": mk, "side": side, "game_pk": pk, "player": "%s %d" % (side, pk),
            "commence": at, "confidence": int(conf), "confidence_value": conf}


_LATE, _EARLY = "2026-10-17T23:05:00Z", "2026-10-17T17:05:00Z"
_pubrows = [pr(1, "home", _LATE, conf=70.0), pr(2, "away", _LATE, conf=65.0), pr(3, "home", _EARLY, conf=64.0),
            pr(4, "home", _LATE, conf=62.0)]
_T7 = tempfile.mkdtemp(prefix="refilter-")
try:
    _pp = os.path.join(_T7, "2026-10-17.json")
    json.dump({"date": "2026-10-17", "game_lines": _pubrows, "picks": []}, open(_pp, "w", encoding="utf-8"))
    # the rebuilt model now expects the AWAY team in games 1, 2 and 3; game 4 is not in it
    _rebuilt = {"games": [{"game_pk": pk, "win": {"home": 40.0, "away": 60.0}} for pk in (1, 2, 3)]}
    _gone = CA.refilter_game_lines(_pp, _rebuilt, _NOWDT)
    _after = json.load(open(_pp, encoding="utf-8"))["game_lines"]
    _again = CA.refilter_game_lines(_pp, _rebuilt, _NOWDT)
finally:
    shutil.rmtree(_T7, ignore_errors=True)
eq((_gone, sorted((r["game_pk"], r["side"]) for r in _after), [r["rank"] for r in _after], _again),
   (1, [(2, "away"), (3, "home"), (4, "home")], [1, 2, 3], 0),
   "🔴 game 1's home moneyline (no longer the expected winner, not started) leaves; game 2 (now on the "
   "winner) stays; game 3 has STARTED and stays as published; game 4 is not in the rebuilt model and is "
   "left alone; the rest re-ranked; a second pass changes nothing")
_csrc = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
_gm_branch = _csrc[_csrc.index('elif mode == "game-model":'):_csrc.index('elif mode == "card":')]
ck("_card.refilter_game_lines(" in _gm_branch and _gm_branch.index("_gm.build(") < _gm_branch.index("refilter_game_lines(")
   < _gm_branch.index("build_winners("),
   "🔴 the collector's own game-model rebuild re-judges the published card, after the model and before the tab")

# ══════════════════════════════════════════════════════════════════════
section("8. 🔴 A WHOLE FOOTBALL CARD: EVERY LIST ON IT, ONE TEAM PER GAME")
# ══════════════════════════════════════════════════════════════════════
SEA, DEN = "Seattle Seahawks", "Denver Broncos"
_n = datetime.datetime.now(UTC)
_K = (_n + datetime.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
_who = ["Rec One", "Rec Two", "Rec Three"]
_T8 = tempfile.mkdtemp(prefix="onecard-")


def put(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with (gzip.open(path, "wt", encoding="utf-8") if path.endswith(".gz") else open(path, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


try:
    _L = os.path.join(_T8, "data", "nfl", "latest")
    put(os.path.join(_L, "props.json.gz"), {"pulled_at": (_n - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "games": [{"id": "ev1", "away": SEA, "home": DEN, "commence": _K, "props": [
            {"player": w, "market": "player_receptions", "line": 3.5,
             "sides": {"over": {"price": -110, "book": "fanduel", "n_books": 3}}} for w in _who]}]})
    put(os.path.join(_L, "players-2025.json.gz"), {"season": 2025, "players": {
        str(i): {"name": w, "pos": "WR", "g": [{"d": "2025-09-%02d" % (j + 7), "snap_pct": 0.9, "rec": 5}
                                               for j in range(10)]} for i, w in enumerate(_who)}})
    put(os.path.join(_L, "fb-model.json"), {"built_at": NOW, "picks": [
        mp(SEA, DEN, "moneyline", "away", SEA, None, 150, 52.0, at=_K),        # the model's both-sides pair
        mp(SEA, DEN, "spread", "home", DEN, 3.5, -110, 55.8, at=_K),
        mp(SEA, DEN, "total", "under", "Under", 40.5, -110, 56.2, at=_K)],
        "win_chances": [{"game_id": "s1", "commence": _K, "away": SEA, "home": DEN, "p_home": 51.2, "p_away": 48.8,
                         # `[2026-10-16]` Denver by 5, 40 points: Seattle +3.5 is OFF the predicted
                         # score's side, Seattle's moneyline off the expected winner; the Under stays
                         "best_ml": {}, "score": {"home": 22.5, "away": 17.5}}]})
    put(os.path.join(_T8, "data", "nfl", _n.strftime("%Y-%m-%d"), "gamelines", "0100.json.gz"),
        {"pulled_at": _n.strftime("%Y-%m-%dT%H:%M:%SZ"), "games": [snap_game("ev1", SEA, DEN, _K)]})
    _q = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, %r); import card_fb; card_fb.main()" % ROOT],
                        cwd=_T8, capture_output=True, text=True, encoding="utf-8", timeout=900,
                        env=dict(os.environ, PYTHONUTF8="1", LEAGUE="nfl"))
    try:
        CARD = json.load(open(os.path.join(_T8, "picks", "fb-nfl-latest.json"), encoding="utf-8"))
    except (OSError, ValueError):
        CARD = {}
        print(shown(_q.stdout[-1500:]), shown(_q.stderr[-1500:]))
finally:
    shutil.rmtree(_T8, ignore_errors=True)
_lines = CARD.get("game_lines") or []
_sgp_line_legs = [x for size in (CARD.get("sgp") or {}).values() for x in size if x.get("n_line_legs")]
ck(bool(_lines) and bool(_sgp_line_legs),
   "⚠️ the planted card really was built, with game lines and same-game parlays that carry a line leg",
   "%d line rows, %d parlays with a line leg; rc %s" % (len(_lines), len(_sgp_line_legs), _q.returncode))
_sides = O.by_names([{"away": SEA, "home": DEN, "p_home": 51.2}])
_sc8 = O.scores_by_names([{"away": SEA, "home": DEN, "score": {"home": 22.5, "away": 17.5}}])
_all = _lines + list(CARD.get("game_lines_liked") or [])
eq([r for r in _all if O.score_side_ok(r, _sc8(r), r.get("line")) is False
    or (r.get("market") == "moneyline" and O.backs(r) != _sides(r))], [],
   "🔴 the built card's game lines and liked lines: every moneyline on Denver (the expected winner), every "
   "spread and total on the predicted score's side; never Seattle's moneyline")
ck(not any(SEA in leg for x in _sgp_line_legs for leg in x.get("legs") or []),
   "🔴 ...and no same-game parlay's line leg is on Seattle: its +3.5 (the richest gap) is off a predicted "
   "Denver-by-5, its moneyline (the next) off the expected winner",
   str([x.get("legs") for x in _sgp_line_legs][:3]))
