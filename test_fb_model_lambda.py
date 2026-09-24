#!/usr/bin/env python3
"""test_fb_model_lambda.py — the self-chosen λ is scored exactly as
`research/fb_model_lambda_spec.md` fixes it (Sam, 2026-09-24).

# @vacuity with fewer than 4 earlier predicted weeks, λ stays 1.0
#   file: fb_model_lambda.py
#   find:     if len(earlier) < MIN_WEEKS:
#   with:     if len(earlier) < 1:
#
# @vacuity the weekly choice reads only weeks BEFORE the week it chooses for
#   file: fb_model_lambda.py
#   find:     earlier = [e for e in fits if e[0] < week and predicted(e)]
#   with:     earlier = [e for e in fits if e[0] <= week and predicted(e)]
#
# @vacuity a tie in mean log loss goes to the LARGER λ
#   file: fb_model_lambda.py
#   find:     return max(lam for lam, v in means.items() if v <= best + TIE), means   # tie -> the LARGER λ
#   with:     return min(lam for lam, v in means.items() if v <= best + TIE), means   # tie -> the LARGER λ
#
# @vacuity a λ whose fit failed in any earlier week is dropped from the choice
#   file: fb_model_lambda.py
#   find:             continue                                  # ⛔ spec §3: a failed fit drops that λ
#   with:             pass
#
# @vacuity d is today's loss minus the self-chosen loss, so d > 0 means better
#   file: fb_model_lambda.py
#   find:     d = [logloss(s["p_fixed"], s["y"]) - logloss(s["p_self"], s["y"]) for s in pairs]
#   with:     d = [logloss(s["p_self"], s["y"]) - logloss(s["p_fixed"], s["y"]) for s in pairs]
#
# @vacuity the paired test clusters by GAME, not by prediction
#   file: fb_model_lambda.py
#   find:     n, mean, t, p, G = mlb_refit.paired_test_clustered(d, [s["game"] for s in pairs])
#   with:     n, mean, t, p, G = mlb_refit.paired_test_clustered(d, list(range(len(pairs))))
#
# @vacuity under 500 paired predictions the verdict is NOT YET MEASURABLE
#   file: fb_model_lambda.py
#   find:     if n < MIN_N:
#   with:     if n < 5:
#
# @vacuity a probability is taken and judged at the CLOSING line
#   file: fb_model_lambda.py
#   find:         return F.features(r, "spread", M=line)
#   with:         return F.features(r, "spread")
"""
import datetime
import os
import sys

from tcheck import ck

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import fb_model as F  # noqa: E402
import fb_model_lambda as L  # noqa: E402

# ══════════════════════════════════════════════════════════════════════
# 1. THE WEEKLY CHOICE
# ══════════════════════════════════════════════════════════════════════
_x1 = [1.0] + [0.0] * 6


def _entry(wk, prob_by_lam, n=10, y=1, fixed_ok=True):
    """A fake week whose λ models predict a fixed probability."""
    models = {}
    for lam in L.GRID:
        p = prob_by_lam.get(lam)
        if p is None or (lam == L.FIXED and not fixed_ok):
            models[lam] = None
            continue
        import math
        e = math.log(p / (1 - p))
        models[lam] = {"mu": [0.0] * 7, "sd": [1.0] * 7, "w": [e] + [0.0] * 7}
    return (wk, models, [(_x1, y)] * n)


_good = {lam: 0.6 for lam in L.GRID}
_good[3.0] = 0.9                                        # λ = 3 predicts the y=1 games best
_weeks = ["2025-09-%02d" % d for d in (1, 8, 15, 22, 29)] + ["2025-10-06"]
_fits = [_entry(w, _good) for w in _weeks]
ck(L.choose(_fits, "2025-09-22")[0] == 1.0,
   "🔴 with only 3 earlier predicted weeks the choice stays at today's λ = 1.0",
   "⛔ Sam: 'With fewer than 4 earlier predicted weeks, use λ = 1.0'. got %r"
   % L.choose(_fits, "2025-09-22")[0])
ck(L.choose(_fits, "2025-10-06")[0] == 3.0,
   "✅ with 5 earlier predicted weeks it takes the λ with the lowest mean log loss",
   "got %r" % (L.choose(_fits, "2025-10-06"),))
# the week being chosen for must NOT inform its own choice
_lead = [_entry(w, _good) for w in _weeks[:4]] + [_entry(_weeks[4], {lam: 0.6 for lam in L.GRID}),
                                                  _entry(_weeks[5], {**_good, 3.0: 0.6, 30.0: 0.999}, n=500)]
ck(L.choose(_lead, "2025-10-06")[0] == 3.0,
   "🔴🔴 the choice for a week reads only EARLIER weeks — never the week itself",
   "⛔ Sam: 'using only games before that week'. got %r" % L.choose(_lead, "2025-10-06")[0])
_tie = [_entry(w, {lam: 0.7 for lam in L.GRID}) for w in _weeks]
ck(L.choose(_tie, "2025-10-06")[0] == 100.0,
   "🔴 a tie goes to the LARGER λ", "⛔ Sam: 'Break ties toward the larger λ'. got %r"
   % L.choose(_tie, "2025-10-06")[0])
_fail = [_entry(w, _good) for w in _weeks[:5]] + [_entry(_weeks[5], _good)]
_fail[2][1][3.0] = None                                 # λ = 3 failed to fit in one earlier week
ck(L.choose(_fail, "2025-10-06")[0] != 3.0,
   "🔴 a λ whose fit failed in any earlier week is dropped from the choice",
   "⛔ spec §3 — otherwise it would be scored on fewer, easier weeks. got %r"
   % L.choose(_fail, "2025-10-06")[0])
_nofix = [_entry(w, _good, fixed_ok=(i != 1)) for i, w in enumerate(_weeks)]
ck(len([e for e in _nofix if e[0] < "2025-10-06" and L.predicted(e)]) == 4,
   "   ✅ ...a week where today's model did not fit does not count as a predicted week")

# ══════════════════════════════════════════════════════════════════════
# 2. THE DECISION: sign, clustering by game, the 500 floor
# ══════════════════════════════════════════════════════════════════════
_better = [{"game": "g%d" % (i // 3), "y": 1, "p_fixed": 0.5, "p_self": 0.6} for i in range(600)]
_dec = L.paired(_better)
ck(_dec["mean_d"] > 0,
   "🔴🔴 d = today's loss − the self-chosen loss, so a better self-chosen version has d > 0",
   "got mean d %r" % _dec["mean_d"])
ck(_dec["clusters"] == 200,
   "🔴🔴 the standard error is clustered by GAME — three markets of one game are one cluster",
   "⛔ Sam: 'standard errors clustered by game'. 600 predictions from 200 games gave %r clusters"
   % _dec["clusters"])
_few = L.paired(_better[:300])
ck(_few["verdict"] == "NOT YET MEASURABLE",
   "🔴 under 500 paired predictions the verdict is NOT YET MEASURABLE, never a pass",
   "got %r" % _few["verdict"])
ck(L.verdict(600, 0.01, 0.01) == "QUALIFIES" and L.verdict(600, 0.01, 0.2) == "DOES NOT QUALIFY"
   and L.verdict(600, -0.01, 0.01) == "DOES NOT QUALIFY",
   "✅ QUALIFIES needs n ≥ 500, a LOWER loss (mean d > 0) and one-sided p < 0.05")
ck(L.paired([dict(s, p_self=None) for s in _better])["n"] == 0,
   "   ✅ ...and only predictions BOTH versions made are paired")

# ══════════════════════════════════════════════════════════════════════
# 3. SCORED AT THE CLOSING LINE, NOT THE TRAINING LINE
# ══════════════════════════════════════════════════════════════════════
_r = {"id": "g", "final": True, "hs": 24, "as": 20, "M": 10.0, "T": 44.5, "pml": 0.6,
      "sig": {"h2h_m": None, "h2h_t": None, "form_m": None, "form_t": None, "def": None,
              "poss": None, "out": None, "neutral": 0.0, "dome": 0.0}}
ck(L.closing_features(_r, "spread", 3.0)[0] == 3.0 / 7.0,
   "🔴 the spread probability is taken AT the closing line (3), not the training line (10)",
   "got %r" % L.closing_features(_r, "spread", 3.0))
ck(L.closing_outcome(_r, "spread", 3.0) == 1 and L.closing_outcome(_r, "spread", 4.0) is None
   and L.closing_outcome(_r, "total", 44.5) == 0 and L.closing_outcome(_r, "total", 44.0) is None and L.closing_outcome(_r, "moneyline", None) == 1,
   "   ✅ ...and judged against that same line (a push at 4 is left out)")

# ══════════════════════════════════════════════════════════════════════
# 4. THE LIVE MODEL IS NOT TOUCHED
# ══════════════════════════════════════════════════════════════════════
_syn = []
for i in range(260):
    d = (datetime.date(2025, 9, 1) + datetime.timedelta(days=i // 3)).isoformat()
    cover = i % 5 != 0
    _syn.append({"id": "s%d" % i, "season": 2025, "day": d, "kick": d, "week": 1,
                 "home": "H", "away": "A", "final": True,
                 "hs": 30 if cover else 20, "as": 17 if cover else 23,
                 "M": 3.0, "T": 44.5, "pml": 0.6, "snap": None, "dk_ml": None,
                 "close": {"spread": [(3.0, -110, -110, False)], "total": [(44.5, -110, -110, False)],
                           "moneyline": [(None, -150, 130, False)]},
                 "sig": dict(_r["sig"])})
_res = L.score_league("nfl", _syn)
ck(F.RIDGE == 1.0 and _res["scored"] and all(s["p_self"] is not None for s in _res["scored"]),
   "✅ scoring runs end to end on synthetic weeks and leaves fb_model.RIDGE at 1.0",
   "RIDGE %r, scored %d" % (F.RIDGE, len(_res["scored"])))
_lams = [lam for _w, lam in _res["lambdas"]["spread"]]
ck(_lams[:4] == [1.0] * 4 and all(lam in L.GRID for lam in _lams),
   "   ✅ ...every week's λ is on Sam's grid, and the first weeks stay at 1.0",
   "got %r" % _lams)
