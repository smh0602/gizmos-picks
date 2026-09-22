#!/usr/bin/env python3
"""Every credit spent is counted, and the balance reconciles with the snapshots.

🔴🔴 `[measured 2026-09-19]` 1,632 of 2,750 billed credits were on no
stored snapshot — converge passes lost at push time (`push_retry.sh`).
The daily cap could not see them and the next run bought the same pull
again. Separately, `_spend_under` summed only `credits_used` and never
the first-half totals bill (`half_total_credits`, 176 that day).

# @vacuity 🔴 the daily cap counts the first-half totals bill
#   file: collect.py
#   find:                     + int(_d.get("half_total_credits") or 0)
#   with:                     + 0
#
# @vacuity 🔴🔴 unrecorded spend is reported
#   file: watchdog.py
#   find:         residue = prev[1] - cur[2] - cur[1]
#   with:         residue = 0
"""
import datetime
import gzip
import json
import os
import shutil
import tempfile

import collect as K
import watchdog as W
from tcheck import ck, section


def snap(root, day, kind, hhmm, used, left, half=None):
    d = os.path.join(root, "data", "nfl", day, kind)
    os.makedirs(d, exist_ok=True)
    doc = {"pulled_at": "%sT%s:%s:00Z" % (day, hhmm[:2], hhmm[2:]),
           "credits_used": used, "credits_remaining": left}
    if half is not None:
        doc["half_total_credits"] = half
    with gzip.open(os.path.join(d, "%s.json.gz" % hhmm), "wt") as fh:
        json.dump(doc, fh)


section("1. 🔴 THE DAILY CAP COUNTS EVERY BILL ON A SNAPSHOT")
tmp = tempfile.mkdtemp(prefix="spend-")
try:
    snap(tmp, "2026-09-23", "gamelines", "1100", 30, 5000, half=176)
    snap(tmp, "2026-09-23", "props-player", "1105", 100, 4694)
    got = K._spend_under(os.path.join(tmp, "data", "nfl", "2026-09-23"))
    ck(got == 306, "🔴 _spend_under = credits_used + half_total_credits (%d)" % got,
       "⛔ 176 first-half credits were invisible to the cap on 2026-09-19")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

section("2. 🔴🔴 THE BALANCE HEADER RECONCILES WITH THE SNAPSHOTS")
NOW = datetime.datetime(2026, 9, 23, 20, 0, tzinfo=datetime.timezone.utc)


def run(tree):
    old = W.ROOT
    W.ROOT = tree
    try:
        rep = W.Report()
        W.check_credit_reconciliation(rep, NOW)
        return rep
    finally:
        W.ROOT = old


tmp = tempfile.mkdtemp(prefix="recon-")
try:
    # complete: 5000 -> (30+176) -> 4794 -> 100 -> 4694
    snap(tmp, "2026-09-23", "gamelines", "1100", 30, 5000, half=0)
    snap(tmp, "2026-09-23", "gamelines", "1200", 30, 4794, half=176)
    snap(tmp, "2026-09-23", "props-player", "1300", 100, 4694)
    r = run(tmp)
    ck(not [i for i in r.items if i["key"] == "credits:unrecorded"],
       "✅ a complete record reconciles to zero, half-totals included",
       "%s" % r.items)
    # a lost pass: 396 spent between readings with no snapshot of it
    snap(tmp, "2026-09-23", "props-player", "1400", 100, 4198)
    r = run(tmp)
    f = [i for i in r.items if i["key"] == "credits:unrecorded"]
    ck(f and f[0]["severity"] == "BROKEN" and "396" in f[0]["what"],
       "🔴🔴 a 396-credit pull with no snapshot is reported BROKEN, with its size",
       "⛔ the exact 2026-09-19 shape (ncaaf props x4). Got %s" % f)
    # interleaved runs: written out of time order, still exact by balance
    tmp2 = tempfile.mkdtemp(prefix="recon2-")
    snap(tmp2, "2026-09-23", "gamelines", "1210", 10, 1000)
    snap(tmp2, "2026-09-23", "props-player", "1200", 20, 980)   # written earlier, spent later
    snap(tmp2, "2026-09-23", "gamelines", "1220", 5, 975)
    r = run(tmp2)
    ck(not [i for i in r.items if i["key"] == "credits:unrecorded"],
       "⛔ two runs interleaving does not raise a false alarm — ordered by balance",
       "%s" % r.items)
    shutil.rmtree(tmp2, ignore_errors=True)
    # a month rollover is a reset, not a residue
    tmp3 = tempfile.mkdtemp(prefix="recon3-")
    snap(tmp3, "2026-09-23", "gamelines", "1100", 10, 500)
    snap(tmp3, "2026-10-01", "gamelines", "1100", 10, 19990)
    r = run(tmp3)
    ck(not [i for i in r.items if i["key"] == "credits:unrecorded"],
       "⛔ a new month's balance reset is not read as spend")
    shutil.rmtree(tmp3, ignore_errors=True)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
