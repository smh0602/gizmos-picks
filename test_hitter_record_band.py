#!/usr/bin/env python3
"""MLB HITTER ROWS GET THE PER-BAND "RUNS HOT" LABEL, FROM THE ONE RULE.

`[audit Proposal B, research/mlb_calibration_audit.md, approved by Sam
2026-09-25]` Hitter RECORD rows had no band warning while their 70-80 band
ran 14 points high on 220 graded picks. Pinned here:

  1. the record writes stated-vs-actual on the PRINTED number per kind
     (`calibration_printed`), so hitter rows have a table at all;
  2. a hitter row in a band that runs hot carries an actionable label, and
     a row in a band that does not, carries none;
  3. the verdict is `calibration.band_flags` itself -- tightening the
     shared rule changes the label -- so there is ONE copy of the rule;
  4. a label only: the row's number and edge do not move.

# @vacuity a hitter row in a hot band must be labelled
#   file: card.py
#   find: if not b or b.get("state") != "UNDER":
#   with: if True:
# @vacuity the record must write the hitter table on the printed number
#   file: collect.py
#   find: "calibration_printed": {k: printed_buckets(k) for k in ("pitcher", "hitter")},
#   with: "calibration_printed": {},
"""
import gzip
import json
import os
import shutil
import sys
import tempfile

from tcheck import ck, eq

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "mlb")
import calibration  # noqa: E402
import card  # noqa: E402

print("1. THE RECORD WRITES A HITTER TABLE ON THE PRINTED NUMBER")
import collect as CO  # noqa: E402
DAY = "2026-09-10"
picks, bats = [], []
for i in range(12):                      # 12 hitter rows printed 75, 3 hit
    picks.append({"pid": 100 + i, "market": "batter_hits", "side": "over",
                  "line": 0.5, "kind": "hitter", "player": "H%d" % i,
                  "confidence": 75, "confidence_basis": "RECORD"})
    bats.append({"id": 100 + i, "H": 1 if i < 3 else 0, "tb": 0, "hr": 0,
                 "r": 0, "rbi": 0})
picks.append({"pid": 900, "market": "outs", "side": "under", "line": 17.5,
              "kind": "pitcher", "pitcher": "P", "blend": 64.0,
              "confidence": 55})
t, cwd = tempfile.mkdtemp(), os.getcwd()
try:
    for d in ("picks", "data/%s/results" % DAY, "data/latest"):
        os.makedirs(os.path.join(t, d))
    json.dump({"date": DAY, "kind": "gizmos-card", "picks": picks},
              open(os.path.join(t, "picks", DAY + ".json"), "w"))
    with gzip.open(os.path.join(t, "data", DAY, "results", "final.json.gz"), "wt") as fh:
        json.dump({"slate_date": DAY, "n_games": 1, "n_final": 1, "games": [
            {"state": "Final", "batters": bats,
             "pitchers": [{"id": 900, "started": True, "k": 5, "outs": 15}]}]}, fh)
    os.chdir(t)
    CO.collect_record()
    rec = json.load(open("data/latest/record.json"))
finally:
    os.chdir(cwd)
    shutil.rmtree(t, ignore_errors=True)
cp = rec.get("calibration_printed") or {}
eq(cp.get("hitter"), [{"bucket": "70-80%", "predicted": 75.0, "w": 3, "n": 12,
                       "pct": 25.0}],
   "🔴 the hitter rows' printed number is bucketed with its result")
eq([b["bucket"] for b in cp.get("pitcher") or []], ["50-60%"],
   "  the pitcher table is on the PRINTED number (55), not blend (64)")
eq([b["bucket"] for b in rec.get("calibration") or []], ["60-70%"],
   "  ...and the permanent blend table is unchanged")

print("\n2. 🔴 A HOT BAND IS LABELLED, A HEALTHY ONE IS NOT")
HOT = [{"bucket": "70-80%", "predicted": 76.5, "n": 220, "w": 120},   # 54.5%
       {"bucket": "80-90%", "predicted": 82.6, "n": 405, "w": 326}]   # 80.5%
card.HCAL[:] = HOT
b75 = card.hitter_band(75)
f75 = card.hitter_band_flag(b75)
ck(b75 and b75["state"] == "UNDER" and f75 and f75["actionable"],
   "🔴 a 75% hitter row in a band 22 points hot carries a label the page shows",
   str(b75))
ck(f75 and "running hot" in f75["text"] and "120 of 220" in f75["text"],
   "  ...in plain words, with the numbers", f75 and f75["text"])
_jargon = ("blend", "p=", "z=", "DESCRIPTIVE", "T2", "band_flags")
ck(f75 and not any(j in f75["text"] for j in _jargon),
   "  ...and no jargon (verify_card's list)")
ck(card.hitter_band_flag(card.hitter_band(85)) is None,
   "✅ an 85% row, in a band hitting 80.5% against 82.6%, carries none")
ck(card.hitter_band(62) is None, "  a band with no graded record says nothing")
card.HCAL[:] = []
ck(card.hitter_band(75) is None, "  no record: no label, never a stale number")

print("\n3. ⛔ ONE COPY OF THE RULE: calibration.band_flags DECIDES")
card.HCAL[:] = HOT
_old = calibration.GAP_POINTS
try:
    calibration.GAP_POINTS = 30.0
    ck(card.hitter_band_flag(card.hitter_band(75)) is None,
       "🔴 raising the shared bar to 30 points removes the label: the card "
       "has no rule of its own")
finally:
    calibration.GAP_POINTS = _old
_old = calibration.BAND_MIN_N
try:
    calibration.BAND_MIN_N = 1000
    ck(card.hitter_band(75)["state"] == "NOT_MEASURABLE",
       "  ...and the shared 10-row floor is the one that applies")
finally:
    calibration.BAND_MIN_N = _old
card.HCAL[:] = []

print("\n4. ⚠️ A LABEL ONLY")
_src = open(os.path.join(ROOT, "card.py"), encoding="utf-8").read()
_i = _src.index("_hbf = hitter_band_flag(_hb)")
_block = _src[_i:_i + 200]
ck("rate" not in _block.split("flags.append(_hbf)")[0]
   and "edge" not in _block.split("flags.append(_hbf)")[0],
   "  the label is appended to flags and touches neither rate nor edge")
