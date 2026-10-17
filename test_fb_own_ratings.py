#!/usr/bin/env python3
"""FOOTBALL GAME LINES READ THE MODEL'S OWN TEAM RATINGS. `[Sam, 2026-10-11]`

"we can't just be a lapdog to sportsbooks our model needs to know the data and
know these teams better than they know themselves". The moneyline, spread and
total fits read the model's own margin and total (`fb_model.own_ratings`), never
the books' line or chance; a line only sets the threshold being priced. Planted
leagues and rows only; nothing here reads the live data tree.
  1. The pure-Python ratings are the direct solve, to 1e-6 (both fits).
  2. A row's ratings never read a game on or after its own week's Monday, and
     each row reads its own week's.
  3. The first input of each fit is the model's own number, whatever the price.
  4. A game the books make the underdog but the model's ratings favour lists the
     underdog, at the model's own chance.
  5. Changing every price leaves the Game Lines tab's chances and every
     alternate-spread rung's chance unchanged.
  6. The alternate-spread record keeps the books'-chance rows apart.
  7. `[2026-10-12]` Every game-market fit caps each standardised input at ±5, in
     training and in prediction; a fit made without the cap is unchanged.

# @vacuity 🔴 the Gauss-Seidel margin fit is the direct solve
#   file: fb_model.py
#   find: R[t] = num / (sum(w[i] for i in ix) + RATING_RIDGE)
#   with: R[t] = num / (sum(w[i] for i in ix) + 2 * RATING_RIDGE)
#
# @vacuity 🔴 ...and so is the points fit
#   file: fb_model.py
#   find: D[t] = num / (sum(w[i] for i in ix) + RATING_RIDGE)
#   with: D[t] = num / (sum(w[i] for i in ix) + 0.5)
#
# @vacuity 🔴 a row's ratings never read a game on or after its week's Monday
#   file: fb_model.py
#   find: while j < len(G) and G[j][0] < wk:
#   with: while j < len(G) and G[j][0] <= wk:
#
# @vacuity 🔴 each row reads its own week's ratings
#   file: fb_model.py
#   find: own.get(monday(r["day"])), r["home"], r["away"], r["sig"]["neutral"])
#   with: own.get(max(own)), r["home"], r["away"], r["sig"]["neutral"])
#
# @vacuity 🔴 the moneyline fit reads the model's own margin, never the books' chance
#   file: fb_model.py
#   find: return [z(om) / 10.0, z(s["h2h_m"]) / 10.0, z(s["form_m"]) / 10.0,
#   with: return [(math.log(r["pml"] / (1 - r["pml"])) if r.get("pml") else 0.0), z(s["h2h_m"]) / 10.0, z(s["form_m"]) / 10.0,
#
# @vacuity 🔴 the spread fit reads (own margin - line), never the line alone
#   file: fb_model.py
#   find: return [z(None if om is None or M is None else om - M) / 10.0,
#   with: return [z(M) / 7.0,
#
# @vacuity 🔴 the total fit reads (own total - line), never the line alone
#   file: fb_model.py
#   find: return [z(None if ot is None or T is None else ot - T) / 10.0,
#   with: return [(z(T) - 45.0) / 10.0,
#
# @vacuity 🔴 the alternate-spread record keeps the books'-chance rows apart
#   file: record_fb.py
#   find: "confidence_basis": r.get("confidence_basis") or "MARKET",
#   with: "confidence_basis": "MARKET",
#
# @vacuity 🔴 a prediction caps each standardised input at zmax
#   file: fb_model.py
#   find: z = [1.0] + [max(-zmax, min(zmax, v)) for v in z[1:]]
#   with: pass
#
# @vacuity 🔴 ...and so does the training
#   file: fb_model.py
#   find: Z = [[1.0] + [max(-zmax, min(zmax, v)) for v in z[1:]] for z in Z]
#   with: pass
#
# @vacuity 🔴 a fit made without zmax is unchanged
#   file: fb_model.py
#   find: def fit(X, y, ridge=RIDGE, iters=50, zmax=None):
#   with: def fit(X, y, ridge=RIDGE, iters=50, zmax=5.0):
#
# @vacuity 🔴 every game-market fit passes zmax
#   file: fb_model.py
#   find: models[mk] = fit([x for x, _ in data], [y for _, y in data], zmax=ZMAX)    # the week's fit
#   with: models[mk] = fit([x for x, _ in data], [y for _, y in data])    # the week's fit
"""
import atexit
import datetime
import gzip
import json
import math
import os
import random
import shutil
import sys
import tempfile

from tcheck import ck, eq, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
import fb_model as F  # noqa: E402
import game_lines_fb as GLF  # noqa: E402
import record_fb as R  # noqa: E402

TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])
SIG = {"h2h_m": None, "h2h_t": None, "form_m": None, "form_t": None, "def": None, "poss": None,
       "out": None, "vac_h": None, "vac_a": None, "neutral": 0.0, "dome": 0.0}

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE PURE-PYTHON RATINGS ARE THE DIRECT SOLVE")
# ══════════════════════════════════════════════════════════════════════
_rnd, G = random.Random(3), []
_teams = ["T%d" % i for i in range(9)]
for i in range(60):
    h, a = _rnd.sample(_teams, 2)
    G.append(((datetime.date(2026, 9, 1) + datetime.timedelta(days=i // 3)).isoformat(), h, a,
              0.0 if i % 7 == 0 else 1.0, float(_rnd.randint(7, 45)), float(_rnd.randint(3, 40))))
G.sort()
WK = "2026-10-05"
S = F.solve_ratings(G, WK)
_w = [0.5 ** ((datetime.date.fromisoformat(WK) - datetime.date.fromisoformat(g[0])).days / 150.0) for g in G]
_T = sorted(S["teams"])
_ix = {t: i for i, t in enumerate(_T)}


def direct(X, Y, W, pen):
    """Weighted ridge least squares by the normal equations (fb_model._solve)."""
    k = len(pen)
    A, b = [[0.0] * k for _ in range(k)], [0.0] * k
    for x, y, wt in zip(X, Y, W):
        for i in range(k):
            b[i] += wt * x[i] * y
            for j in range(k):
                A[i][j] += wt * x[i] * x[j]
    for i in range(k):
        A[i][i] += pen[i]
    return F._solve(A, b)


_n = len(_T)
_X, _Y = [], []
for g in G:
    x = [g[3]] + [0.0] * _n
    x[1 + _ix[g[1]]], x[1 + _ix[g[2]]] = 1.0, -1.0
    _X.append(x)
    _Y.append(g[4] - g[5])
_mm = direct(_X, _Y, _w, [0.0] + [1.0] * _n)
_X, _Y, _W = [], [], []
for g, wt in zip(G, _w):
    for pts, side, opp, hf in ((g[4], g[1], g[2], g[3]), (g[5], g[2], g[1], 0.0)):
        x = [1.0, hf] + [0.0] * (2 * _n)
        x[2 + _ix[side]], x[2 + _n + _ix[opp]] = 1.0, -1.0
        _X.append(x)
        _Y.append(pts)
        _W.append(wt)
_pp = direct(_X, _Y, _W, [0.0, 0.0] + [1.0] * (2 * _n))
_em = max([abs(S["hfa"] - _mm[0])] + [abs(S["R"][t] - _mm[1 + _ix[t]]) for t in _T])
_ep = max([abs(S["base"] - _pp[0]), abs(S["hpe"] - _pp[1])]
          + [abs(S["O"][t] - _pp[2 + _ix[t]]) for t in _T] + [abs(S["D"][t] - _pp[2 + _n + _ix[t]]) for t in _T])
ck(_em < 1e-6 and _ep < 1e-6, "🔴 the margin fit and the points fit match a direct solve to 1e-6",
   "margin %.2e, points %.2e" % (_em, _ep))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 A ROW'S RATINGS READ ONLY GAMES BEFORE ITS OWN WEEK'S MONDAY")
# ══════════════════════════════════════════════════════════════════════
_t = tempfile.mkdtemp(prefix="ownr-")
TREES.append(_t)
_sch = [  # (start, home, away, final, home pts, away pts)
    ("2026-09-13T17:00", "AAA", "BBB", True, 30, 10), ("2026-09-13T17:00", "CCC", "DDD", True, 20, 17),
    ("2026-09-14T00:15", "BBB", "DDD", True, 3, 41),     # ON Monday 09-14: not week 2's
    ("2026-09-17T00:15", "AAA", "CCC", True, 35, 3),     # Thursday of week 2
    ("2026-09-20T17:00", "AAA", "DDD", False, None, None), ("2026-09-27T17:00", "BBB", "CCC", False, None, None)]
os.makedirs(os.path.join(_t, "data", "nfl", "latest"))
with gzip.open(os.path.join(_t, "data", "nfl", "latest", "schedule-2026.json.gz"), "wt") as fh:
    json.dump({"games": [{"id": "s%d" % i, "start": s, "home": h, "away": a, "final": f, "week": 1 + i // 2,
                          "home_score": hs, "away_score": as_} for i, (s, h, a, f, hs, as_) in enumerate(_sch)]}, fh)


class _Allowed:
    def __init__(self, lg):
        pass

    def fraction(self, g):
        return None


_old = (F.board_prices, F.t60r.history, F.t60r.Allowed)
try:
    F.board_prices = lambda lg, resolve, root=None: {}
    F.t60r.history = lambda lg: []
    F.t60r.Allowed = _Allowed
    ROWS = {r["day"]: r for r in F.build_rows("nfl", root=_t, board={})}
finally:
    F.board_prices, F.t60r.history, F.t60r.Allowed = _old
_RG = F.rating_games("nfl", _t)
_w2 = F.own_numbers(F.solve_ratings([g for g in _RG if g[0] < "2026-09-14"], "2026-09-14"), "AAA", "DDD", 0.0)
_w3 = F.own_numbers(F.solve_ratings([g for g in _RG if g[0] < "2026-09-21"], "2026-09-21"), "BBB", "CCC", 0.0)
_r6 = lambda t: tuple(round(x, 6) for x in t)  # noqa: E731  (warm-started vs cold: 1e-6)
eq(_r6((ROWS["2026-09-20"]["sig"]["own_m"], ROWS["2026-09-20"]["sig"]["own_t"])), _r6(_w2),
   "🔴 week 2's game reads week 1's two games only: not Monday 09-14's, not Thursday's")
eq(_r6((ROWS["2026-09-27"]["sig"]["own_m"], ROWS["2026-09-27"]["sig"]["own_t"])), _r6(_w3),
   "🔴 ...and week 3's game reads all four, each row its own week's ratings")
ck(_w2 != F.own_numbers(F.solve_ratings([g for g in _RG if g[0] <= "2026-09-14"], "2026-09-14"),
                        "AAA", "DDD", 0.0),
   "⚠️ the Monday game really moves the ratings, so the cut is tested")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE FIRST INPUT OF EACH FIT IS THE MODEL'S OWN NUMBER")
# ══════════════════════════════════════════════════════════════════════
def row(own_m, own_t, pml=0.7, M=-6.5, T=44.5, **kw):
    return dict({"lg": "nfl", "M": M, "T": T, "pml": pml, "sig": dict(SIG, own_m=own_m, own_t=own_t)}, **kw)


_a, _b = row(5.0, 47.0), row(5.0, 47.0, pml=0.2, M=9.5, T=51.5)
eq([F.features(r, "moneyline")[0] for r in (_a, _b)], [0.5, 0.5],
   "🔴 moneyline: own margin / 10, whatever the books' chance")
eq([F.features(r, "spread", M=3.0)[0] for r in (_a, _b)], [0.2, 0.2],
   "🔴 spread at 3: (own margin - 3) / 10, whatever the books' line")
eq([round(F.features(r, "total", T=44.5)[0], 9) for r in (_a, _b)], [0.25, 0.25],
   "🔴 total at 44.5: (own total - 44.5) / 10")
eq([F.features(row(None, None), mk, M=3.0, T=44.5)[0] for mk in ("moneyline", "spread", "total")],
   [0.0, 0.0, 0.0], "   a team with no earlier stored game: the own terms are 0")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE MODEL'S UNDERDOG IS LISTED, AT THE MODEL'S OWN CHANCE")
# ══════════════════════════════════════════════════════════════════════
# 240 earlier games: the home side wins when the model's own margin says so,
# and the books' chance agrees with the result too (so a fit on it would follow it).
_rnd = random.Random(5)
TRAIN = []
for i in range(240):
    om = _rnd.uniform(-12, 12)
    won = om + _rnd.gauss(0, 4) > 0
    TRAIN.append(row(om, 45.0, pml=0.72 if won else 0.28, id="t%d" % i, final=True, hs=24 if won else 10,
                     **{"as": 10 if won else 24}))
_m = F.fit([F.features(r, "moneyline") for r in TRAIN], [F.label(r, "moneyline") for r in TRAIN])
_dog = row(-6.0, 45.0, pml=0.72, id="g1", final=False)      # the books favour the home side
_q = lambda r, mk: [("fanduel", None, -250, 200, False)]    # noqa: E731
_pk = F.best_pick(_dog, "moneyline", _m, _q)
ck(_pk and _pk["side"] == "away" and _pk["p"] > 0.5 and _pk["price"] == 200,
   "🔴 the books price the away side at +200; the model's ratings make it the better side, "
   "and it is the pick at the model's own chance", str(_pk))

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 A PRICE NEVER MOVES THE GAME LINES TAB OR A RUNG'S CHANCE")
# ══════════════════════════════════════════════════════════════════════
def snap(h, a):
    return {"names": ["Home Team", "Away Team"], "commence": "2026-10-12T17:00:00Z", "pulled_at": "2026-10-11T14:00:00Z",
            "books": {"fanduel": {"h2h": {"Home Team": h, "Away Team": a}}}}


_now = "2026-10-11T15:00:00Z"
_c1 = F.win_chances(TRAIN + [dict(_dog, snap=snap(-250, 200), day="2026-10-12")], _now)
_c2 = F.win_chances(TRAIN + [dict(_dog, pml=0.35, snap=snap(130, -150), day="2026-10-12")], _now)
ck(len(_c1) == len(_c2) == 1 and (_c1[0]["p_home"], _c1[0]["p_away"]) == (_c2[0]["p_home"], _c2[0]["p_away"])
   and _c1[0]["p_away"] > 50,
   "🔴 the Game Lines tab's chances are the same at -250/+200 and at +130/-150", str((_c1, _c2)))
_spm = F.fit([F.features(r, "spread", M=-3.0) for r in TRAIN], [1 if r["sig"]["own_m"] > -3 else 0 for r in TRAIN])
_lad = lambda d: {("home", -3.5): {"FanDuel": -110 + d}, ("home", 3.5): {"FanDuel": -300 + d},  # noqa: E731
                  ("away", 3.5): {"FanDuel": -110 - d}, ("away", -3.5): {"FanDuel": 160 + d}}
_r1 = GLF.rungs_for(_lad(0), "spread", -3.5, {"spread": _spm}, _dog, None)
_r2 = GLF.rungs_for(_lad(25), "spread", -3.5, {"spread": _spm}, _dog, None)
ck(len(_r1) == 4 and [(x["side"], x["pt"], x["p"]) for x in _r1] == [(x["side"], x["pt"], x["p"]) for x in _r2]
   and [x["best"] for x in _r1] != [x["best"] for x in _r2],
   "🔴 every alternate-spread rung keeps the model's chance when its price moves",
   str([(x["pt"], x["best"], x["p"]) for x in _r1 + _r2]))

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 THE ALTERNATE-SPREAD RECORD KEEPS THE BOOKS'-CHANCE ROWS APART")
# ══════════════════════════════════════════════════════════════════════
_alt = lambda s, b, c: {"market": "alternate_spread", "side": "home", "line": 7.5, "sched_id": s,  # noqa: E731
                        "confidence_basis": b, "confidence": c, "player": "H"}
_rec = R.grade_alt_spreads(
    [("f1", {"date": "2026-10-04", "game_lines": [_alt("S1", None, 77), _alt("S2", None, 75)]}),
     ("f2", {"date": "2026-10-11", "game_lines": [_alt("S3", "MODEL", 62)]})],
    {"S1": {"final": True, "home_score": 10, "away_score": 20}, "S2": {"final": True, "home_score": 30, "away_score": 3},
     "S3": {"final": True, "home_score": 3, "away_score": 30}}, GLF.grade_rung)
eq(_rec["by_basis"], {"MARKET": {"w": 1, "n": 2, "pct": 50.0}, "MODEL": {"w": 0, "n": 1, "pct": 0.0}},
   "🔴 the books'-chance rows keep their record as graded, and the model's own open theirs")

# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 THE GAME FITS CAP EACH STANDARDISED INPUT AT ±5")
# ══════════════════════════════════════════════════════════════════════
# 240 games on two inputs; then one more whose second input sits far out in training
# (head-to-head inputs 197-224 SD out on 8569375b printed 0.000000%).
_rnd = random.Random(12)
_X = [[_rnd.uniform(-12, 12), _rnd.gauss(0, 1)] for _ in range(240)] + [[2.0, 60.0]]
_Y = [1 if a + 0.1 * b + _rnd.gauss(0, 4) > 0 else 0 for a, b in _X]


def grad(m, cap):
    """The ridge-logistic gradient at m's weights, inputs standardised by m and
    capped at `cap` (None: not capped). Zero at the fit's optimum."""
    g = [0.0] * len(m["w"])
    for x, t in zip(_X, _Y):
        z = [1.0] + [(x[j] - m["mu"][j]) / m["sd"][j] for j in range(len(x))]
        z = [1.0] + [max(-cap, min(cap, v)) if cap else v for v in z[1:]]
        p = 1.0 / (1.0 + math.exp(-sum(a * b for a, b in zip(m["w"], z))))
        g = [gi + (p - t) * zi for gi, zi in zip(g, z)]
    return max(abs(gi + (F.RIDGE * wi if i else 0.0)) for i, (gi, wi) in enumerate(zip(g, m["w"])))


_pz, _p0 = F.fit(_X[:240], _Y[:240], zmax=F.ZMAX), F.fit(_X[:240], _Y[:240])
_mz, _m0 = F.fit(_X, _Y, zmax=F.ZMAX), F.fit(_X, _Y)
_at = lambda m, k: F.predict(m, [0.0, m["mu"][1] + k * m["sd"][1]])  # noqa: E731
ck(_at(_pz, 200) == _at(_pz, 5) and abs(_at(_p0, 200) - _at(_p0, 5)) > 0.2,
   "🔴 a game 200 SD out on one input gets the same chance as at 5 SD: %.4f (uncapped %.4f vs %.4f)"
   % (_at(_pz, 200), _at(_p0, 200), _at(_p0, 5)), "%.4f vs %.4f" % (_at(_pz, 200), _at(_pz, 5)))
ck(_mz["zmax"] == 5.0 and grad(_mz, 5.0) < 1e-6 and grad(_mz, None) > 1e-3,
   "🔴 the capped fit is trained on the capped inputs (it stores zmax 5)", "%.2e" % grad(_mz, 5.0))
ck(set(_m0) == {"mu", "sd", "w"} and grad(_m0, None) < 1e-6 and grad(_m0, 5.0) > 1e-3,
   "🔴 a fit made without zmax is the plain fit on the raw inputs, as before (props, MLB pitcher, "
   "MLB game model)", "%s %.2e" % (sorted(_m0), grad(_m0, None)))
_seen, _real = [], F.fit
F.fit = lambda X, y, *a, **kw: _seen.append(kw.get("zmax")) or _real(X, y, *a, **kw)
try:
    _rows = [dict(r, day="2026-10-05", snap=None) for r in TRAIN]
    F.walk_forward(_rows), F.current_picks("nfl", _rows, now=_now), F.pricing(_rows, _now), F.win_chances(_rows, _now)
finally:
    F.fit = _real
# `[Sam, 2026-10-15]` win chances also fits the total (the predicted score's total).
eq(_seen, [5.0] * 10, "🔴 every game-market fit caps at ±5: walk-forward 3, current picks 3, "
                     "the Game Lines tab and alternate rungs' pricing 2, win chances 2 (moneyline, total)")
