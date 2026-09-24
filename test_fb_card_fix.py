#!/usr/bin/env python3
"""test_fb_card_fix.py — the football props card's season fix keeps the
promises in `research/fb_card_fix_spec.md` (Sam, 2026-09-24).

# @vacuity 2025 counts less as 2026 games arrive: w = 4 / (4 + n26)
#   file: card_fb.py
#   find:     w = K_SEASON / (K_SEASON + n26)
#   with:     w = 1.0
#
# @vacuity every record is pulled toward the position average with weight 12
#   file: card_fb.py
#   find:     conf = (H + K_PRIOR * p0) / (N + K_PRIOR)
#   with:     conf = (H + 0.5) / (N + 1.0)
#
# @vacuity a thin sample never prints 90% or more
#   file: card_fb.py
#   find:         conf = min(conf, THIN_CAP)
#   with:         conf = conf
#
# @vacuity the fixed card applies every gate the current card applies
#   file: card_fb.py
#   find:     if gated_games(both, market, line) is None:
#   with:     if False:
#
# @vacuity the position average counts only games in which he did this job
#   file: card_fb.py
#   find:                     if any(float(g.get(f) or 0) > 0 for f in job):
#   with:                     if True:
#
# @vacuity a card never reads the game it is rating, or a later one
#   file: card_fb.py
#   find:     return [g for g in games or [] if (g.get("d") or "") < day]
#   with:     return [g for g in games or [] if (g.get("d") or "") <= day]
#
# @vacuity with fewer than 500 props the fix ships only if it is not worse
#   file: fb_card_fix.py
#   find:     elif n < MIN_N and mean is not None and mean >= 0:
#   with:     elif mean is not None and mean >= 0:
#
# @vacuity d = current loss − fixed loss, so d > 0 means the fix predicted better
#   file: fb_card_fix.py
#   find:     d = [logloss(r["current"], r["y"]) - logloss(r["fixed"], r["y"]) for r in rows]
#   with:     d = [logloss(r["fixed"], r["y"]) - logloss(r["current"], r["y"]) for r in rows]
#
# @vacuity the ship test clusters by GAME
#   file: fb_card_fix.py
#   find:     n, mean, t, p, G = mlb_refit.paired_test_clustered(d, [r["cluster"] for r in rows])
#   with:     n, mean, t, p, G = mlb_refit.paired_test_clustered(d, list(range(len(rows))))
#
# @vacuity the live switch is exactly what the recorded ship verdict says
#   file: card_fb.py
#   find: CARD_METHOD = METHOD_FIXED
#   with: CARD_METHOD = METHOD_CURRENT
#
# @vacuity the record never pools two methods' calibration
#   file: record_fb.py
#   find:         per.setdefault(r.get("card_method") or METHOD_BEFORE, {}).setdefault(
#   with:         per.setdefault(METHOD_BEFORE, {}).setdefault(
#
# @vacuity a new method with nothing graded is NOT YET MEASURABLE, never a pass
#   file: calibration.py
#   find:         return {"state": "NOT_MEASURABLE", "n": 0,
#   with:         return {"state": "OK", "n": 0,
#
# @vacuity #155's registered test reads only the method it was registered on
#   file: fb_card_calibration.py
#   find:                 if (r.get("card_method") or REGISTERED_METHOD) != method:
#   with:                 if False:
"""
import glob
import gzip
import json
import os
import shutil
import sys
import tempfile

from tcheck import ck

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "nfl")
import calibration as CAL  # noqa: E402
import card_fb as C  # noqa: E402
import fb_card_calibration as K  # noqa: E402
import fb_card_fix as X  # noqa: E402
import record_fb as R  # noqa: E402

RUSH = "player_rush_yds"


def _g(d, v, car=10):
    return {"d": d, "snap_pct": 0.7, "rush_yds": v, "car": car}


# ══════════════════════════════════════════════════════════════════════
# 1. THE FORMULA, worked by hand from the spec
# ══════════════════════════════════════════════════════════════════════
_saved = C.LEAGUE
C.LEAGUE = "nfl"
try:
    _7 = [_g("2025-10-%02d" % (i + 1), 80) for i in range(7)]
    ck(C.rate_blend(_7, [], RUSH, 50.5, "over", 0.5)[0] == round(100 * 13 / 19),
       "🔴🔴 7 of 7 against a 50% position average prints 68%, not 94%",
       "⛔ spec: (7 + 12 x 0.5) / (7 + 12). got %r" % (C.rate_blend(_7, [], RUSH, 50.5, "over", 0.5),))
    _12 = [_g("2025-10-%02d" % (i + 1), 80) for i in range(12)]
    _4 = [_g("2026-09-%02d" % (i + 1), v) for i, v in enumerate((80, 20, 90, 10))]
    _r = C.rate_blend(_12, _4, RUSH, 50.5, "over", 0.4)
    ck(_r[0] == round(100 * (8 + 12 * 0.4) / 22) and _r[4]["w25"] == 0.5,
       "🔴🔴 four 2026 games halve 2025: 12/12 + 2/4 -> H 8 of N 10 -> 58%",
       "⛔ Sam: 'the more 2026 games he has, the less 2025 counts'. got %r" % (_r,))
    _9 = [_g("2025-10-%02d" % (i + 1), 80) for i in range(9)]
    ck(C.rate_blend(_9, [], RUSH, 50.5, "over", 0.95)[0] == 89,
       "🔴 a thin sample never prints 90% or more, even with a 95% position average",
       "⛔ Sam: 'a thin sample can't print 90%% or more'. got %r" % (C.rate_blend(_9, [], RUSH, 50.5, "over", 0.95),))
    ck(C.rate_blend(_7[:5], [], RUSH, 50.5, "over", 0.5) is None,
       "🔴 the fixed card keeps every gate: 5 games is still too few for a rate")
    ck(C.rate_for(_7, RUSH, 50.5, "over")[0] == 94,
       "   ✅ ...and the current card is unchanged (7 of 7 still 94% the old way)")
    # the position average: only games he did this job in, only before the day
    _pl = {"a": {"pos": "RB", "g": [_g("2025-10-01", 100)] * 30 + [_g("2025-10-02", 0, car=0)] * 40},
           "b": {"pos": "RB", "g": [_g("2025-10-03", 20)] * 30}}
    _pools = C.position_pools([_pl])
    _p0 = C.position_prior(_pools, "RB", RUSH, "over", 50.5, "2026-09-10")
    ck(abs(_p0 - 0.5) < 1e-9,
       "🔴 the position average counts only games in which he did the job (40 no-carry games left out)",
       "30 of 60 carry games clear 50.5. got %r" % _p0)
    ck(C.position_prior(_pools, "RB", RUSH, "over", 50.5, "2025-10-02") == 0.5
       and C.position_prior(_pools, "RB", RUSH, "over", 150.5, "2026-09-10") == 0.0,
       "   ✅ ...with fewer than 50 earlier games it is 0.5, and it reads the line")
    ck([g["d"] for g in C.games_before([_g("2026-09-06", 1), _g("2026-09-13", 1), _g("2026-09-20", 1)],
                                       "2026-09-13")] == ["2026-09-06"],
       "🔴🔴 a card dated 09-13 reads only games before 09-13 — never its own game",
       "⛔ the prop's own game would be predicting itself")
finally:
    C.LEAGUE = _saved

# ══════════════════════════════════════════════════════════════════════
# 2. THE SHIP RULE, as Sam set it
# ══════════════════════════════════════════════════════════════════════


def _rows(n, cur, fix, y=1):
    return [{"current": cur, "fixed": fix, "y": y, "cluster": "g%d" % (i // 2)} for i in range(n)]


ck(X.ship(_rows(600, 0.5, 0.9))["verdict"] == "LIVE",
   "✅ a clearly better fix ships (p < 0.05)")
ck(X.ship(_rows(300, 0.6, 0.6))["verdict"] == "LIVE",
   "🔴 under 500 props, a fix that is not worse (mean difference 0) ships — Sam's correction branch")
ck(X.ship(_rows(600, 0.6, 0.6))["verdict"] == "STAYS",
   "🔴🔴 over 500 props, 'not worse' is NOT enough — it must beat the card with p < 0.05",
   "got %r" % X.ship(_rows(600, 0.6, 0.6)))
ck(X.ship(_rows(300, 0.9, 0.5))["verdict"] == "STAYS",
   "🔴 a worse fix stays out, whatever the sample")
ck(X.ship(_rows(600, 0.5, 0.9))["mean_d"] > 0 and X.ship(_rows(600, 0.5, 0.9))["clusters"] == 300,
   "🔴 d > 0 means the fix predicted better, and props are clustered by GAME (600 rows, 300 games)")

_run = sorted(glob.glob(os.path.join(ROOT, "research", "fb_card_fix_run_*.json")))
_verdict = json.load(open(_run[-1], encoding="utf-8"))["decision"]["verdict"] if _run else None
ck(_verdict is not None and (C.CARD_METHOD == C.METHOD_FIXED) == (_verdict == "LIVE"),
   "🔴🔴 the card's live method is exactly what the recorded ship verdict says",
   "⛔ Sam's rule decides, never a hand edit. verdict %r, CARD_METHOD %r" % (_verdict, C.CARD_METHOD))

# ══════════════════════════════════════════════════════════════════════
# 3. BEFORE AND AFTER, NEVER MIXED  `[Sam]`
# ══════════════════════════════════════════════════════════════════════
_mixed = ([{"confidence": 85, "won": False, "card_method": "2025-only"}] * 10
          + [{"confidence": 85, "won": True, "card_method": "season-blend"}] * 10)
_now, _by = R.calibration_by_method(_mixed, "season-blend")
ck(len(_by) == 2 and _now == _by["season-blend"] and _now[0]["n"] == 10 and _now[0]["w"] == 10
   and _by["2025-only"][0]["w"] == 0,
   "🔴🔴 the record keeps each method's calibration apart — the current table holds only its own plays",
   "got %r" % _by)
_new = CAL.judge({"calibration": [], "card_method_current": "season-blend",
                  "calibration_by_method": {"2025-only": _by["2025-only"]}})
ck(_new["state"] == "NOT_MEASURABLE",
   "🔴 a new method with nothing graded yet is NOT YET MEASURABLE — never a pass, never the old record",
   "got %r" % _new)
_tmp = tempfile.mkdtemp()
try:
    for lg in ("nfl", "ncaaf"):
        os.makedirs(os.path.join(_tmp, "data", lg, "latest"))
        rows = [{"confidence": 84, "won": True, "game": "A @ B", "commence": "2026-09-13T17:00:00Z"},
                {"confidence": 70, "won": False, "game": "C @ D", "commence": "2026-09-27T17:00:00Z",
                 "card_method": "season-blend"}]
        with gzip.open(os.path.join(_tmp, "data", lg, "latest", "record-detail.json.gz"), "wt",
                       encoding="utf-8") as fh:
            json.dump({"days": {"2026-09-13": rows[:1], "2026-09-27": rows[1:]}}, fh)
    _reg = K.load_picks(_tmp)
    _fx = K.load_picks(_tmp, method="season-blend")
    _before = K.page_bands_before("nfl", _tmp)
finally:
    shutil.rmtree(_tmp, ignore_errors=True)
ck(len(_reg) == 2 and all(p["raw"] == 0.84 for p in _reg) and len(_fx) == 2
   and all(p["raw"] == 0.70 for p in _fx),
   "🔴🔴 #155's registered test reads only the old method's plays; the fixed card's are scored apart",
   "⛔ Sam: 'report picks from before and after the fix separately'. got %r / %r" % (_reg, _fx))
ck(list(_before) == ["2025-only"],
   "   ✅ ...and the page's 'before the fix' table holds the old method, kept apart",
   "got %r" % list(_before))
