#!/usr/bin/env python3
"""test_fb_card_calibration.py — the football props card's calibration is
scored exactly as `research/fb_card_calibration_spec.md` fixes it
(Sam, 2026-09-24).

# @vacuity each week's mapping is fitted only on picks graded BEFORE that week
#   file: fb_card_calibration.py
#   find:         train = [p for p in picks if p["day"] < wk]
#   with:         train = [p for p in picks if F.monday(p["day"]) <= wk]
#
# @vacuity a void or ungradable pick is never scored
#   file: fb_card_calibration.py
#   find:                 if r.get("confidence") is None or r.get("won") not in (True, False):
#   with:                 if r.get("confidence") is None:
#
# @vacuity d = raw loss − calibrated loss, so d > 0 means the correction helped
#   file: fb_card_calibration.py
#   find:     d = [logloss(s["raw"], s["y"]) - logloss(s["cal"], s["y"]) for s in scored]
#   with:     d = [logloss(s["cal"], s["y"]) - logloss(s["raw"], s["y"]) for s in scored]
#
# @vacuity the paired test clusters by GAME
#   file: fb_card_calibration.py
#   find:     n, mean, t, p, G = mlb_refit.paired_test_clustered(d, [s["game"] for s in scored])
#   with:     n, mean, t, p, G = mlb_refit.paired_test_clustered(d, list(range(len(scored))))
#
# @vacuity under 500 scored picks the verdict is NOT YET MEASURABLE
#   file: fb_card_calibration.py
#   find:     if n < MIN_N:
#   with:     if n < 5:
#
# @vacuity the page's band flags are calibration.py's own verdicts
#   file: fb_card_calibration.py
#   find:              "actual": L(b["actual"], "DESCRIPTIVE"), "flag": b["state"]}
#   with:              "actual": L(b["actual"], "DESCRIPTIVE"), "flag": "OK"}
#
# @vacuity the page shows the band table next to the card
#   file: index.html
#   find:       ${fbCardCalHtml(CC)}
#   with:       ${''}
"""
import datetime
import gzip
import json
import os
import shutil
import sys
import tempfile

from tcheck import ck

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import fb_card_calibration as K  # noqa: E402
import jsblock  # noqa: E402


def _pk(day, raw, y, game):
    return {"league": "nfl", "day": day, "raw": raw, "y": y, "game": game}


# ══════════════════════════════════════════════════════════════════════
# 1. WALK-FORWARD: a week's mapping never sees its own week
# ══════════════════════════════════════════════════════════════════════
_p = []
for i in range(200):                       # week of 09-07: 90% printed, half hit
    _p.append(_pk("2026-09-%02d" % (7 + i % 7), 0.9, i % 2, "g%d" % i))
for i in range(300):                       # week of 09-14: 90% printed, ALL hit
    _p.append(_pk("2026-09-%02d" % (14 + i % 7), 0.9, 1, "h%d" % i))
_scored, _maps = K.walk_forward(_p)
_w2 = [s for s in _scored if s["week"] == "2026-09-14"]
ck(_w2 and max(s["cal"] for s in _w2) < 0.6,
   "🔴🔴 week 2 is corrected from week 1 ONLY (half hit -> ~50%), never from its own results",
   "⛔ Sam: 'using only picks graded before each week'. got %r" % (max(s["cal"] for s in _w2) if _w2 else None))
ck(_maps["2026-09-07"] is None and not [s for s in _scored if s["week"] == "2026-09-07"],
   "   ✅ ...and the first week, with nothing earlier, is not scored at all")

# ══════════════════════════════════════════════════════════════════════
# 2. THE PICKS: graded, rated rows of the card's own record only
# ══════════════════════════════════════════════════════════════════════
_tmp = tempfile.mkdtemp()
try:
    for lg in ("nfl", "ncaaf"):
        os.makedirs(os.path.join(_tmp, "data", lg, "latest"))
        rows = [{"confidence": 84, "won": True, "game": "A @ B", "commence": "2026-09-13T17:00:00Z"},
                {"confidence": 90, "won": None, "game": "A @ B", "commence": "2026-09-13T17:00:00Z"},
                {"confidence": None, "won": False, "game": "A @ B", "commence": "2026-09-13T17:00:00Z"}]
        with gzip.open(os.path.join(_tmp, "data", lg, "latest", "record-detail.json.gz"), "wt",
                       encoding="utf-8") as fh:
            json.dump({"days": {"2026-09-13": rows}}, fh)
    _loaded = K.load_picks(_tmp)
finally:
    shutil.rmtree(_tmp, ignore_errors=True)
ck(len(_loaded) == 2 and all(p["raw"] == 0.84 and p["y"] == 1 for p in _loaded),
   "🔴 only graded, rated picks are scored — a void and an unrated row are left out, both leagues read",
   "got %r" % _loaded)

# ══════════════════════════════════════════════════════════════════════
# 3. THE DECISION: sign, clustering by game, the 500 floor
# ══════════════════════════════════════════════════════════════════════
_s = [dict(_pk("2026-09-14", 0.9, 0, "g%d" % (i // 3)), cal=0.5) for i in range(600)]
_d = K.decision(_s)
ck(_d["mean_d"] > 0, "🔴🔴 a correction that predicts better has d > 0", "got %r" % _d["mean_d"])
ck(_d["clusters"] == 200,
   "🔴🔴 clustered by GAME — three picks of one game are one cluster",
   "⛔ Sam: 'clustered by game'. got %r" % _d["clusters"])
ck(K.decision(_s[:300])["verdict"] == "NOT YET MEASURABLE",
   "🔴 under 500 scored picks the verdict is NOT YET MEASURABLE, never a pass")
ck(K.verdict(600, 0.1, 0.01) == "QUALIFIES" and K.verdict(600, 0.1, 0.2) == "DOES NOT QUALIFY"
   and K.verdict(600, -0.1, 0.01) == "DOES NOT QUALIFY",
   "✅ QUALIFIES needs n ≥ 500, a lower loss and one-sided p < 0.05")

# ══════════════════════════════════════════════════════════════════════
# 4. THE PAGE: calibration.py's band verdicts, next to the card
# ══════════════════════════════════════════════════════════════════════
_tmp = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(_tmp, "data", "nfl", "latest"))
    json.dump({"calibration": [{"bucket": "80-90%", "stated": 84.1, "w": 20, "n": 49},
                               {"bucket": "60-70%", "stated": 65.0, "w": 30, "n": 48}]},
              open(os.path.join(_tmp, "data", "nfl", "latest", "record.json"), "w"))
    _b = {b["bucket"]: b for b in K.page_bands("nfl", _tmp)}
finally:
    shutil.rmtree(_tmp, ignore_errors=True)
ck(_b["80-90%"]["flag"] == "UNDER" and _b["60-70%"]["flag"] == "OK"
   and _b["80-90%"]["actual"] == {"value": 40.8, "basis": "DESCRIPTIVE"},
   "🔴 the page's bands carry calibration.py's own per-band verdict, labelled DESCRIPTIVE",
   "got %r" % _b)
_html = os.path.join(ROOT, "index.html")
_pk_js = jsblock.js_block("fbPicks", _html)
_cc_js = jsblock.js_block("fbCardCalHtml", _html)
ck("${fbCardCalHtml(CC)}" in _pk_js and _pk_js.index("${fbCalNote(C)}") < _pk_js.index("${fbCardCalHtml(CC)}")
   and "labN(b.stated" in _cc_js and "labN(b.actual" in _cc_js and "raw" in _cc_js,
   "🔴 the page shows stated vs actual per band next to the card, and says the numbers are raw",
   "⛔ Sam: 'next to the football props card ... labelled DESCRIPTIVE' and a visible warning")
