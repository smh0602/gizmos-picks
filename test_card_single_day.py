#!/usr/bin/env python3
"""
THE MLB CARD IS ONE ET DAY, AND THE BOARD CAN HOLD SEVERAL.

🔴 THE FAILURE, 2026-10-01 (run 2080, pass 3): the stored board held
three games -- tonight's, and two on 10-03 (the 10-02 off day) and 10-04.
card.py built plays for EVERY game that had not started, so a card dated
2026-10-01 carried 21 `picks` rows and 6 `top10` rows from 10-03, every
projection was flagged priced (436 of 436: the verifier's "subset, not a
rubber stamp" check), and the watchdog's single-day check (rule 101) went
red. The card was withheld, correctly. The football builder had the
single-day filter; the MLB builder never did, because MLB boards had
never held a second day's games until the schedule thinned out.

✅ card.py now plays only games on the slate's own ET date. Projections
still cover the whole board (they are the Player Props tab's, and are not
rows on the card).

This file RUNS THE REAL BUILDER on a copy of the tree with kickoffs moved
RELATIVE TO THE REAL CLOCK (3h, 50h, 75h out) so the case is planted, not
waited for, and reads every dated list on the card it wrote.

# @vacuity the MLB builder skips games off the slate day
#   file: card.py
#   find:         if et_date(g["commence"]) != today:
#   with:         if False:
"""
import copy
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

from tcheck import ck, note, copy_module, shown

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp()
try:
    copy_module("card", tmp)
    shutil.copytree(os.path.join(ROOT, "data", "latest"),
                    os.path.join(tmp, "data", "latest"))
    shutil.copytree(os.path.join(ROOT, "picks"), os.path.join(tmp, "picks"))
    path = os.path.join(tmp, "data", "latest", "props.json.gz")
    B = json.load(gzip.open(path, "rt"))
    games = B["games"]
    while len(games) < 3:                     # plant, never wait for, the case
        g = copy.deepcopy(games[0])
        g["id"] = "planted%d" % len(games)
        games.append(g)
    now = datetime.now(timezone.utc)
    for g, h in zip(games, (3, 50, 75)):
        g["commence"] = (now + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    del games[3:]
    with gzip.open(path, "wt") as f:
        json.dump(B, f)

    code = ("import json,card;d=card.main(dry=True);"
            "print('@@'+json.dumps(d,default=str))")
    r = subprocess.run([sys.executable, "-c", code], cwd=tmp,
                       capture_output=True, text=True, timeout=600)
    line = [l for l in r.stdout.splitlines() if l.startswith("@@")]
    ck("the builder ran on the planted board", bool(r.returncode == 0 and line),
       "" if line else shown((r.stdout + r.stderr)[-800:]))
    doc = json.loads(line[0][2:])
    sys.path.insert(0, tmp)
    from card import et_date
    dated = {k: v for k, v in doc.items() if isinstance(v, list) and v
             and isinstance(v[0], dict) and v[0].get("commence")}
    ck("the card has dated lists to inspect", "picks" in dated and "top10" in dated,
       str(sorted(dated)))
    for k, rows in sorted(dated.items()):
        off = sorted({et_date(x["commence"]) for x in rows} - {doc["date"]})
        ck("every row of %s is on the card's own day (%s)" % (k, len(rows)),
           not off, "%s dated %s, rows on %s" % (k, doc["date"], off))
    px = doc.get("projections") or {}
    ck("the priced flag is a subset: the other days' props are projected, "
       "not priced", 0 < sum(1 for v in px.values() if v.get("p")) < len(px),
       "%d of %d" % (sum(1 for v in px.values() if v.get("p")), len(px)))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
