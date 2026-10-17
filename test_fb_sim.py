#!/usr/bin/env python3
"""test_fb_sim.py — every football game simulated 10,000 times, and the switches the backtest set.

`[Sam, 2026-10-17]` *"we shoudl be setting up the 10000 game simulations for each game every
week"*; 10,000 runs, "Backtest, then switch". `fb_sim.simulate` plays a game possession by
possession from the model's own predicted score; `fb_model.SIM` lets it set a league's spread and
total chances only when the recorded backtest (research/fb_sim_backtest.json) passed the bar fixed
before the run (research/fb_sim_design.md §3): log loss at most the smooth curve's AND closing-
line return at least its. NFL injuries: the same bar, `fb_model.INJURIES`. Planted games only,
plus the recorded run; ⛔ reads nothing live.

# @vacuity 🔴 every game's runs average the model's own predicted margin and total
#   file: fb_sim.py
#   find:     bh, ba = bh - (dt + dm) / 2.0, ba - (dt - dm) / 2.0
#   with:     bh, ba = bh, ba
#
# @vacuity 🔴 ...with the model's own spread of results
#   file: fb_sim.py
#   find:     v_m, v_t = max(0.0, v_m - (vm - sigma * sigma)), max(0.0, v_t - (vt - sigma_t * sigma_t))
#   with:     v_m, v_t = v_m + 60.0, v_t + 60.0
#
# @vacuity 🔴 games land on 3 as real games do (the margin correction)
#   file: fb_sim.py
#   find:     fix = MARGIN_FIX.get(lg) or {}
#   with:     fix = {}
#
# @vacuity 🔴 a push is counted on a whole-number line
#   file: fb_sim.py
#   find:     push = sum(c for k, c in hist.items() if k == line) / n
#   with:     push = 0.0
#
# @vacuity 🔴 the same game gives the same 10,000 runs every build
#   file: fb_sim.py
#   find:     rng = random.Random(_seed(lg, key, round(home, 2), round(away, 2), round(sigma, 4), round(sigma_t, 4), runs))
#   with:     rng = random.Random()
#
# @vacuity 🔴 a sim pick sits on the predicted score's side
#   file: fb_model.py
#   find:         side, px, p = (hi, pa, win_hi) if d > 0 else (lo, pb, 1.0 - win_hi - push)
#   with:         side, px, p = (lo, pb, 1.0 - win_hi - push) if d > 0 else (hi, pa, win_hi)
#
# @vacuity 🔴 ...and a push returns the stake in its value
#   file: fb_model.py
#   find:         ev = p * decimal(px) + push - 1.0
#   with:         ev = p * decimal(px) - 1.0
#
# @vacuity 🔴 a league's picks use the simulation only when its switch is on
#   file: fb_model.py
#   find:         if SIM.get(r.get("lg")):                  # `[Sam, 2026-10-17]` once its backtest passed
#   with:         if True:
#
# @vacuity 🔴 the Game Lines tab gets every game's simulated win share
#   file: winners.py
#   find:     w = sim["home_win"] if row["side"] == "home" else 1.0 - sim["home_win"] - (sim.get("tie") or 0.0)
#   with:     w = sim["home_win"]
#
# @vacuity 🔴 injuries move each team's points by the week's fitted sizes
#   file: fb_model.py
#   find:         sc = {"home": round(sc["home"] + dh, 1), "away": round(sc["away"] + da, 1)}
#   with:         sc = {"home": round(sc["home"], 1), "away": round(sc["away"], 1)}
"""
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "nfl")
import fb_sim as S  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 ONE GAME, 10,000 TIMES: THE MODEL'S SCORE, ITS SPREAD, FOOTBALL'S SHAPE")
# ══════════════════════════════════════════════════════════════════════
GAMES = [("nfl", 24.9, 23.9, 13.39, 14.25), ("nfl", 31.0, 14.0, 13.39, 14.25),
         ("ncaaf", 30.6, 21.0, 16.57, 16.40), ("ncaaf", 45.0, 10.0, 16.57, 16.40)]
for lg, h, a, sg, st in GAMES:
    sim = S.simulate(lg, h, a, sg, st, key="g")
    mm, vm = S._moments(sim["margin"])
    mt, vt = S._moments(sim["total"])
    ck(sim["runs"] == 10000 and abs(mm - (h - a)) < 0.8 and abs(mt - (h + a)) < 0.8
       and abs(vm ** 0.5 - sg) < 1.0 and abs(vt ** 0.5 - st) < 1.0,
       "🔴 %s %.1f-%.1f: 10,000 runs averaging the model's margin and total, with its spread of results"
       % (lg, h, a), "margin %.2f sd %.2f, total %.2f sd %.2f" % (mm, vm ** 0.5, mt, vt ** 0.5))
close = S.simulate("nfl", 24.9, 23.9, 13.39, 14.25, key="g")
n = close["runs"]
p3 = (close["margin"].get(3, 0) + close["margin"].get(-3, 0)) / n
ck(p3 > 0.12 and 0.05 < S.cover(close, 3, "spread")[1] < 0.10 and S.cover(close, 3.5, "spread")[1] == 0,
   "🔴 a close NFL game ends by exactly 3 in more than 12% of its runs (real games: 14.9% of ALL games; "
   "a smooth curve: about 6%), and a -3 line pushes 5-10% of the time; a -3.5 never pushes",
   "%.3f, push %.3f" % (p3, S.cover(close, 3, "spread")[1]))
cc = S.simulate("ncaaf", 28.0, 27.0, 16.57, 16.40, key="c")
ck(cc["ties"] == 0 and (cc["margin"].get(3, 0) + cc["margin"].get(-3, 0)) / cc["runs"] > 0.08,
   "🔴 college: no ties (overtime until someone leads), and a close game lands on 3 in more than 8% of runs")
eq(S.simulate("nfl", 24.9, 23.9, 13.39, 14.25, key="g"), close,
   "🔴 the same game and inputs give the same 10,000 runs every build (seeded by the game)")
_r = S.from_summary(S.summary(close))
ck(all(abs(S.cover(_r, x, "spread")[0] - S.cover(close, x, "spread")[0]) < 1e-3 for x in (-7, -3, 0.5, 3, 6.5)),
   "🔴 the stored form (fb-model.json win_chances[].sim) gives back the same chances")
eq([round(v, 6) for v in S.team_cover(close, "home", -3)], [round(v, 6) for v in S.cover(close, 3, "spread")],
   "   ...and a team's own point reads the same (home -3 = margin above 3)")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 A SIM PICK: THE SCORE'S SIDE, THE SIM'S CHANCE, A PUSH RETURNS THE STAKE")
# ══════════════════════════════════════════════════════════════════════
import fb_model as FM  # noqa: E402
_q = lambda *qs: (lambda r, mk: list(qs))  # noqa: E731
SC = {"home": 24.9, "away": 23.9}
pk = FM.sim_pick({}, "spread", SC, close, quotes=_q(("fd", 3.0, 110, 110, False)))
w, push = S.cover(close, 3.0, "spread")
eq((pk or {}).get("side"), "away",
   "🔴 a predicted 1-point home win takes the away +3 (the score's side), never the home -3")
ck(pk and abs(pk["p"] - (1 - w - push)) < 1e-9 and abs(pk["push"] - push) < 1e-9
   and abs(pk["ev"] - ((1 - w - push) * FM.decimal(110) + push - 1)) < 1e-9,
   "🔴 its chance and push chance are the simulation's, and a push returns the stake in its value", str(pk))
_saved = (dict(FM.SIM), FM.score_pick, FM.sim_pick)
_gs = FM.game_score
try:
    FM.score_pick = lambda *a, **k: "SMOOTH"
    FM.sim_pick = lambda *a, **k: "SIM"
    _r0 = {"lg": "nfl", "id": "x", "sig": {}}
    _m = {"moneyline": None}
    FM.game_score = lambda r, models, sigma, sigma_t: (52.0, SC)
    FM.SIM["nfl"] = False
    off = FM.shown_pick(_r0, "spread", _m, 13.39, 14.25, quotes=_q())
    FM.SIM["nfl"] = True
    on = FM.shown_pick(_r0, "spread", _m, 13.39, 14.25, quotes=_q())
finally:
    FM.SIM.clear()
    FM.SIM.update(_saved[0])
    FM.score_pick, FM.sim_pick = _saved[1], _saved[2]
    FM.game_score = _gs
eq((off, on), ("SMOOTH", "SIM"), "🔴 a league's picks use the simulation only when its switch is on")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE SWITCHES ARE THE RECORDED BACKTEST'S VERDICT, BY THE BAR FIXED BEFORE IT")
# ══════════════════════════════════════════════════════════════════════
REC = json.load(open(os.path.join(ROOT, "research", "fb_sim_backtest.json"), encoding="utf-8"))
_sim_pass = {lg: v["logloss"]["sim"] <= v["logloss"]["smooth"]
             and v["closing_return"]["sim"] >= v["closing_return"]["smooth"] for lg, v in REC["simulation"].items()}
eq({lg: FM.SIM.get(lg) for lg in ("nfl", "ncaaf")}, {lg: _sim_pass.get(lg, False) for lg in ("nfl", "ncaaf")},
   "🔴 fb_model.SIM is exactly what the recorded run earned (both numbers, per league): %s" % _sim_pass)
# `[2026-10-17, review]` read through the runner's own bar (exact numbers where recorded), so the
#    switch check and fb_inj_backtest can never disagree. ~~the comparison retyped on the rounded fields~~
import fb_inj_backtest as _IB  # noqa: E402
_inj_pass = {lg: _IB.passes(v) for lg, v in REC["injuries"].items()}
_inj_retyped = {lg: v["logloss"]["with"] <= v["logloss"]["without"]
             and v["closing_return"]["with"] >= v["closing_return"]["without"] for lg, v in REC["injuries"].items()}
eq({lg: FM.INJURIES.get(lg) for lg in ("nfl", "ncaaf")}, {lg: _inj_pass.get(lg, False) for lg in ("nfl", "ncaaf")},
   "🔴 fb_model.INJURIES is exactly what the recorded injury run earned: %s" % _inj_pass)
_old = [lg for lg, v in REC["injuries"].items() if "exact" not in v]
eq({lg: _inj_pass[lg] for lg in _old}, {lg: _inj_retyped[lg] for lg in _old},
   "✅ ...and an entry recorded without exact numbers reads exactly as the rounded comparison did")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 EVERY GAME'S RUNS REACH THE GAME LINES TAB")
# ══════════════════════════════════════════════════════════════════════
import winners as W  # noqa: E402
FBM = {"win_chances": [
    {"game_id": "g1", "commence": "2026-10-18T17:00:00Z", "away": "Seattle Seahawks", "home": "Denver Broncos",
     "p_home": 42.0, "best_ml": {}, "score": {"home": 20.6, "away": 23.9},
     "sim": {"runs": 10000, "home_win": 0.41, "tie": 0.004}},
    {"game_id": "g2", "commence": "2026-10-18T17:00:00Z", "away": "A", "home": "B", "p_home": 61.0,
     "best_ml": {}, "score": None, "sim": None}]}
_wk = {r["game_id"]: (r["sim_win"], r["sim_runs"]) for r in W.fb_rows(FBM, None, lambda c: c[:10])}
eq(_wk, {"g1": (59, 10000), "g2": (None, None)},
   "🔴 the tab gets how often the PICK wins in the runs: Seattle 1 - 0.41 - 0.004 = 59%; no sim: none")
PAGE = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
ck("<th class=\"n\">Wins in 10,000 sims</th>" in PAGE and "r.sim_win + '%'" in PAGE,
   "   ...and prints it in its own column")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 NFL INJURIES: SIZED ON EARLIER GAMES, MOVING THE SCORE AND THE CHANCE")
# ══════════════════════════════════════════════════════════════════════
rng = random.Random(3)
TRAIN = []
for i in range(400):
    qh, qa = (1.0 if rng.random() < 0.1 else 0.0), (1.0 if rng.random() < 0.1 else 0.0)
    oh, oa, dh, da = rng.random() * 2, rng.random() * 2, rng.random() * 2, rng.random() * 2
    # the planted truth: a QB out costs his team 6 points, each offensive starter 1, each
    #    defensive starter out gives the opponent 1
    hs = 24 - 6 * qh - oh + da + rng.gauss(0, 3)
    as_ = 20 - 6 * qa - oa + dh + rng.gauss(0, 3)
    TRAIN.append({"final": True, "hs": hs, "as": as_,
                  "sig": {"own_m": 4.0, "own_t": 44.0, "inj": {"qb": (qh, qa), "off": (oh, oa), "def": (dh, da)}}})
b = FM.injury_fit(TRAIN)
ck(b and -7.0 < b[0] < -3.0 and -1.6 < b[1] < -0.4 and 0.4 < b[2] < 1.6,
   "🔴 the injury fit finds the planted sizes (QB out -6, offensive starter -1, opponent's defender +1; "
   "ridge pulls them a little toward 0)", str(b))
_saved = dict(FM.INJURIES)
_gs_models = {"moneyline": {"mu": [0.0], "sd": [1.0], "w": [0.2, 0.0]}, "injury": [-6.0, -1.0, 1.0]}
_row = {"lg": "nfl", "T": None, "sig": {"own_t": 44.0, "own_m": 0.0, "inj": {"qb": (1.0, 0.0), "off": (0.0, 0.0), "def": (0.0, 0.0)}}}
_fs = FM.features
try:
    FM.features = lambda r, mk, **k: [0.0]
    FM.INJURIES["nfl"] = False
    p0, s0 = FM.game_score(_row, _gs_models, 13.4, 14.3)
    FM.INJURIES["nfl"] = True
    p1, s1 = FM.game_score(_row, _gs_models, 13.4, 14.3)
finally:
    FM.features = _fs
    FM.INJURIES.clear()
    FM.INJURIES.update(_saved)
ck(s0 and s1 and abs((s1["home"] - s0["home"]) + 6.0) < 0.11 and s1["away"] == s0["away"] and p1 < p0,
   "🔴 on: the home QB out takes 6 points off the home score and the home win chance falls with it; off: "
   "nothing moves", (p0, s0, p1, s1))
