#!/usr/bin/env python3
"""THE PRINTED PITCHER NUMBER IS FITTED BY THE CODE THE TEST SCORED.

`[2026-09-25]` research/mlb_pitcher_cal_spec.md was committed and hashed
before any scoring. C2 (the printed number mixed with the price) qualified
and shipped. This file pins what that means:

  1. the card's mapping for card date D is EXACTLY the scorer's walk-forward
     mapping for D: same rows (earlier card dates only), same fit;
  2. a market below 150 graded rows has no mapping and prints its blend;
  3. Sam's off switch (`SHIPPED = None`) puts the plain blend back;
  4. the corrected number is really used: a mapping that says "the price
     is right" moves a row's number toward the price.

Everything is built in a temp tree; the repo's record is never read.

# @vacuity a card mapping fitted on the card's OWN day would be look-ahead
#   file: mlb_pitcher_cal.py
#   find: if before is not None and date >= before:
#   with: if before is not None and date > before:
# @vacuity the off switch must actually switch the correction off
#   file: mlb_pitcher_cal.py
#   find: m = (maps or {}).get(market) if SHIPPED else None
#   with: m = (maps or {}).get(market)
# @vacuity importing fb_model would drag card_fb (which exits on mlb) into the card
#   file: mlb_pitcher_cal.py
#   find: fb_model = _load_fb_fit()   # the one ridge-logistic fit (spec §3)
#   with: import fb_model  # noqa
"""
import datetime
import gzip
import json
import os
import random
import shutil
import sys
import tempfile

from tcheck import ck, eq

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import mlb_pitcher_cal as M  # noqa: E402


def fixture(root, n_days=30, per_day=12, markets=M.MARKETS):
    """A record-detail with a known truth: the price is right, the card
    runs ~12 points hot."""
    rnd = random.Random(7)
    days = {}
    d0 = datetime.date(2026, 8, 23)
    for i in range(n_days):
        date = (d0 + datetime.timedelta(days=i)).isoformat()
        rows = []
        for mk in markets:
            for _ in range(per_day):
                be = rnd.uniform(0.45, 0.75)
                y = rnd.random() < be - 0.03
                rows.append({"kind": "pitcher", "market": mk, "won": y,
                             "blend": round(100 * min(0.97, be + 0.12), 1),
                             "implied": round(100 * be, 1)})
            rows.append({"kind": "pitcher", "market": mk, "won": None,
                         "blend": 70.0, "implied": 55.0})     # a void
            rows.append({"kind": "hitter", "market": "batter_hits",
                         "won": True, "blend": None, "implied": 70.0})
        days[date] = rows
    os.makedirs(os.path.join(root, "data", "latest"), exist_ok=True)
    with gzip.open(os.path.join(root, "data", "latest",
                                "record-detail.json.gz"), "wt") as fh:
        json.dump({"days": days}, fh)
    return sorted(days)


t = tempfile.mkdtemp()
try:
    dates = fixture(t)
    D = dates[20]

    print("1. 🔴 THE CARD'S MAPPING IS THE SCORER'S WALK-FORWARD MAPPING")
    rows = M.graded_rows(t)
    ck(all(r["date"] < D for r in M.graded_rows(t, D)) and M.graded_rows(t, D),
       "⛔ only card dates BEFORE the card's own date are read (no look-ahead)")
    eq(len(M.graded_rows(t, D)), 20 * 12 * 2,
       "  voids and hitter rows are left out; 20 earlier days x 12 x 2 markets")
    for r in rows:
        r.update(model=0.6, h=3, n=5, cluster=r["date"])
    _wf, _ = M.walk_forward([r for r in rows if r["date"] <= D])
    card_maps = M.mappings(D, t)
    for mk in M.MARKETS:
        test_rows = [r for r in rows if r["date"] == D and r["market"] == mk]
        sc = {id(r): p for r, p in _wf["C2"] if r["date"] == D and r["market"] == mk}
        live = [M.corrected(card_maps, mk, 100 * r["blend"], 100 * r["be"]) / 100
                for r in test_rows]
        ck(len(sc) == len(test_rows) and
           max(abs(a - sc[id(r)]) for a, r in zip(live, test_rows)) < 1e-9,
           "🔴 %s: the card prints exactly what the test scored" % mk)

    print("\n2. ⚠️ THE TRUTH IN THE FIXTURE IS RECOVERED")
    r0 = [r for r in rows if r["date"] == D][0]
    p_card = r0["blend"]
    p_fix = M.corrected(card_maps, r0["market"], 100 * r0["blend"], 100 * r0["be"]) / 100
    ck(abs(p_fix - r0["be"]) < abs(p_card - r0["be"]),
       "  a card running 12 points hot is pulled toward the price",
       "blend %.3f  corrected %.3f  price %.3f" % (p_card, p_fix, r0["be"]))

    print("\n3. ⏳ BELOW 150 GRADED ROWS A MARKET HAS NO MAPPING")
    few = M.mappings(dates[5], t)          # 5 days x 12 = 60 per market
    ck(all(v is None for v in few.values()),
       "  no mapping on 60 rows", str({k: bool(v) for k, v in few.items()}))
    ck(M.corrected(few, "outs", 70.0, 55.0) is None,
       "  ...so the card prints its blend unchanged")

    print("\n4. ⛔ SAM'S OFF SWITCH")
    _old = M.SHIPPED
    try:
        M.SHIPPED = None
        ck(M.corrected(card_maps, "outs", 70.0, 55.0) is None,
           "  SHIPPED = None puts the plain blend back on every row")
    finally:
        M.SHIPPED = _old
    ck(M.corrected(card_maps, "outs", 70.0, 55.0) is not None,
       "  ...and with C2 shipped the row is corrected")
    eq(M.SHIPPED, "C2", "  the shipped candidate is the one the spec's run chose")
finally:
    shutil.rmtree(t, ignore_errors=True)

print("\n5. THE COMMITTED RUN RECORDS THE VERDICT THAT SHIPPED")
_runs = sorted(f for f in os.listdir(os.path.join(ROOT, "research"))
               if f.startswith("mlb_pitcher_cal_run_") and f.endswith(".json"))
ck(bool(_runs), "  a scored run is committed beside the spec")
if _runs:
    _r = json.load(open(os.path.join(ROOT, "research", _runs[0])))
    eq(_r.get("ships"), M.SHIPPED,
       "🔴 what the card applies is what the FIRST committed run chose")
    ck(_r["candidates"][M.SHIPPED]["verdict"] == "QUALIFIES",
       "  ...and that candidate QUALIFIED under the frozen bar")

print("\n6. 🔴 THE MLB CARD NEVER IMPORTS THE FOOTBALL STACK")
# `[measured 2026-09-25]` `import fb_model` pulls in card_fb.py, which
# EXITS under LEAGUE=mlb -- the MLB card would have died on import.
import subprocess  # noqa: E402
_p = subprocess.run(
    [sys.executable, "-c",
     "import sys, card; bad = sorted(m for m in ('fb_model', 'card_fb', "
     "'dossier_fb', 'shadow_fb', 't60r') if m in sys.modules); "
     "print('FOOTBALL', bad); sys.exit(1 if bad else 0)"],
    cwd=ROOT, capture_output=True, text=True, env=dict(os.environ, LEAGUE="mlb"))
ck(_p.returncode == 0,
   "🔴 `import card` under LEAGUE=mlb loads no football module",
   (_p.stdout + _p.stderr)[-300:])

print("\n7. ⛔ ...AND THE FIT IT READS IS fb_model.fit, NOT A SECOND COPY")
_p = subprocess.run(
    [sys.executable, "-c",
     "import json, random, fb_model, mlb_pitcher_cal as M\n"
     "r = random.Random(3)\n"
     "X = [[r.gauss(0, 1), r.gauss(0, 1)] for _ in range(300)]\n"
     "y = [1 if r.random() < 0.5 + 0.2 * x[0] else 0 for x in X]\n"
     "a, b = fb_model.fit(X, y), M.fb_model.fit(X, y)\n"
     "print(json.dumps([a == b, fb_model.MIN_TRAIN == M.fb_model.MIN_TRAIN,"
     " fb_model.RIDGE == M.fb_model.RIDGE,"
     " fb_model.predict(a, [0.3, -1]) == M.fb_model.predict(b, [0.3, -1])]))"],
    cwd=ROOT, capture_output=True, text=True, env=dict(os.environ, LEAGUE="nfl"))
try:
    _same = json.loads(_p.stdout.strip().splitlines()[-1])
except (ValueError, IndexError):
    _same = None
eq(_same, [True, True, True, True],
   "🔴 the source-loaded fit, predict, MIN_TRAIN and RIDGE equal fb_model's own")
