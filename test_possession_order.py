#!/usr/bin/env python3
"""
🔴🔴 `playNumber` ALONE WAS NOT THE PLAY ORDER, AND THE COLLEGE POSSESSION
SIGNAL REFUSED TO PUBLISH FOR IT ON EVERY RUN.

`[live 2026-09-19T07:53:52Z — data/ncaaf/latest/top-probe-2026.json]`

    anomaly_pct                           36.339   ordering by playNumber
    dn_pn_anomaly_pct                      1.585   ordering by (driveNumber, playNumber)
    dn_present_pct                         100.0   on all 59,462 rows
    dn_pn_buckets_skipped_no_drivenumber       0
    CFB_ANOMALY_MAX_PCT                      2.0   the floor

⛔ Both numbers come from the SAME RUN over the SAME ROWS, and the counter
that produced the second one shipped in PR #75 **before anyone saw the
data**. The sort key changed on a measurement, not on a hunch.

⚠️ WHAT IS NOT CLAIMED, AND IT MATTERS: the pre-registered `order_reading`
verdict came back **INCONCLUSIVE** — *"the counters do not match any
pre-registered reading … read the numbers directly rather than the
verdict"*. So WHY `playNumber` is scrambled is still unknown, and
`dn_pn_monotonic_game_pct` is **68.73**, not 100. ⛔ This file pins that
the remedy RECOVERS ORDER. It does not pin an explanation of the feed.

⛔ AND THE ANOMALY GATE IS NOT THE ONLY GATE. `COVERAGE_MIN` is untested
under this key on live CFBD bytes — the probe only ever reported coverage
for the old order. If coverage still refuses, nothing is written, and that
is the correct outcome rather than a regression.

══════════════════════════════════════════════════════════════════════
DRIVEN, NEVER READ. Every check below calls the real
`cfb.possession_from_plays` on real college clock sequences.
══════════════════════════════════════════════════════════════════════

# @vacuity 🔴🔴 the sort key is (driveNumber, playNumber)
#   file: cfb.py
#   find:         rows.sort(key=lambda r: (r[4] is None, r[4], r[0] is None, r[0]))
#   with:         rows.sort(key=lambda r: (r[0] is None, r[0]))
"""
import collections
import gzip
import json
import os
import random
import sys

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import cfb  # noqa: E402

FIXTURE = "research/cfb_clock_sample_2019.json.gz"


def quiet(*a, **k):
    pass


def load():
    with gzip.open(FIXTURE, "rt") as fh:
        return json.load(fh)["plays"]


PLAYS = load()
BY_G = collections.defaultdict(list)
for _p in PLAYS:
    BY_G[_p["gameId"]].append(_p)
GIDS = sorted(BY_G)[:60]
SUB = [p for g in GIDS for p in BY_G[g]]


def run(rows):
    return cfb.possession_from_plays(rows, 2019, quiet)[1]


def h1_shape(gids):
    """`playNumber` restarting per drive, `driveNumber` present, rows shuffled.

    ⚠️ THE SHUFFLE IS THE POINT. Arrival order must carry no information,
    or the check passes on list order rather than on the sort key.
    """
    out = []
    for g in gids:
        rows = sorted(BY_G[g],
                      key=lambda r: (r.get("playNumber") is None,
                                     r.get("playNumber")))
        dn_of, ctr = {}, collections.Counter()
        for r in rows:
            d = r.get("driveId")
            if d not in dn_of:
                dn_of[d] = len(dn_of) + 1
            ctr[d] += 1
            q = dict(r)
            q["driveNumber"] = dn_of[d]
            q["playNumber"] = ctr[d]
            out.append(q)
    random.Random(7).shuffle(out)
    return out


# ══════════════════════════════════════════════════════════════════════
section("0. ⚠️ THE FIXTURE IS REAL AND CARRIES NO driveNumber")
# ══════════════════════════════════════════════════════════════════════
ck("the fixture loaded and is a real season of plays",
   len(PLAYS) > 100000 and len(BY_G) > 500,
   "⛔ rule 67: every check below is vacuous over a thin fixture. "
   "rows=%d games=%d" % (len(PLAYS), len(BY_G)))
ck("⚠️ ...and NOT ONE of its rows carries `driveNumber`",
   not any("driveNumber" in p for p in PLAYS),
   "🔴 THIS IS WHY THE FIXTURE CANNOT SETTLE THE LIVE QUESTION and why "
   "§2 below synthesises the shape instead. It also makes §1 a genuine "
   "no-op test rather than a coincidence.")

# ══════════════════════════════════════════════════════════════════════
section("1. ⛔ ON DATA WITH NO driveNumber THE CHANGE IS A NO-OP")
# ══════════════════════════════════════════════════════════════════════
FULL = run(PLAYS)
ck("🔴 the known-good fixture still scores 0.506",
   FULL["anomaly_pct"] == 0.506,
   "⛔ the recorded value for this fixture through the OLD key. A new "
   "sort key that moved it would be changing a correct answer. got %s"
   % FULL["anomaly_pct"])
ck("✅ ...and it still publishes",
   FULL["usable"] is True and FULL.get("error") is None,
   "the whole-fixture run is the regression case: %s" % FULL.get("error"))
ck("⚠️ ...and the report names the key it used",
   FULL.get("order_key") == "(driveNumber, playNumber)",
   "⛔ an anomaly rate with no ordering key beside it cannot be compared "
   "to the next run's. got %r" % FULL.get("order_key"))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 ON THE LIVE SHAPE, THE NEW KEY RECOVERS THE TRUE ORDER")
# ══════════════════════════════════════════════════════════════════════
TRUTH = run(SUB)
H1 = h1_shape(GIDS)
NEWK = run(H1)
OLDK = run([{k: v for k, v in r.items() if k != "driveNumber"} for r in H1])

ck("⚠️ the truth case is a real, ordered derivation to compare against",
   TRUTH["anomaly_pct"] < 1.0 and TRUTH["pairs"] > 5000,
   "⛔ rule 67 again — if the baseline is already broken the comparison "
   "below says nothing. anomaly=%s pairs=%s"
   % (TRUTH["anomaly_pct"], TRUTH["pairs"]))

ck("🔴🔴 the scrambled feed sorted by (driveNumber, playNumber) "
   "reproduces the TRUE anomaly rate EXACTLY",
   NEWK["anomaly_pct"] == TRUTH["anomaly_pct"],
   "⛔ THIS IS THE WHOLE FIX. truth=%s recovered=%s"
   % (TRUTH["anomaly_pct"], NEWK["anomaly_pct"]))
ck("🔴 ...and the coverage distribution too, not just the headline",
   NEWK.get("coverage_median") == TRUTH.get("coverage_median"),
   "⛔ a matching anomaly rate with a different coverage median would "
   "mean the pairs were re-ordered but the seconds landed elsewhere. "
   "truth=%s recovered=%s"
   % (TRUTH.get("coverage_median"), NEWK.get("coverage_median")))
ck("🔴 ...and the same teams derive a possession at all",
   NEWK.get("teams") == TRUTH.get("teams"),
   "truth=%s recovered=%s" % (TRUTH.get("teams"), NEWK.get("teams")))

ck("⛔ while the SAME rows without `driveNumber` are wrecked",
   OLDK["anomaly_pct"] > 20.0,
   "🔴 IF THIS PASSES QUIETLY THE TEST ABOVE PROVES NOTHING — the "
   "scramble has to actually break the old key. got %s"
   % OLDK["anomaly_pct"])
ck("⛔ ...and its coverage median goes ABOVE 1.0, which is impossible",
   (OLDK.get("coverage_median") or 0) > 1.0,
   "🔴 the live tell: coverage is a fraction of 3600, so a median over "
   "1.0 is four times the game clock. This is the signature the real "
   "feed showed at 4.06. got %s" % OLDK.get("coverage_median"))

# ══════════════════════════════════════════════════════════════════════
section("3. ⚠️ A MISSING OR ODD driveNumber MUST NOT CRASH THE BUILD")
# ══════════════════════════════════════════════════════════════════════
# 🔴 AN ABSENT `driveNumber` IS NOT A ZERO and must not collide with one.
MIXED = [dict(r) for r in H1]
for i, r in enumerate(MIXED):
    if i % 97 == 0:
        r.pop("driveNumber", None)
try:
    MREP = run(MIXED)
    _crash = None
except Exception as e:          # noqa: BLE001
    MREP, _crash = None, "%s: %s" % (type(e).__name__, e)
ck("🔴 rows with a MISSING driveNumber sort last instead of crashing",
   _crash is None,
   "⛔ a feed that omits the column on some rows must degrade, not take "
   "the whole college build down: %s" % _crash)
ck("⚠️ ...and the run still produces a report rather than silence",
   bool(MREP) and MREP.get("anomaly_pct") is not None,
   "a build that neither writes nor reports is the worst outcome")

note("⚠️ WHAT THIS FILE DOES NOT PROVE. The recovery above is measured on "
     "a cfbfastR fixture re-keyed into CFBD's shape — ⛔ a fact about one "
     "distributor is not a fact about the other, which is exactly the "
     "caveat that paid off when the live run came back at 36% against "
     "the fixture's 0.5%. ✅ What settles the LIVE question is the "
     "already-paid counter `dn_pn_anomaly_pct = 1.585` against a 2.0 "
     "floor, measured on real CFBD bytes on 2026-09-19. ⛔ And the "
     "coverage gate is still unmeasured under this key — the first live "
     "run under it is what says whether §6 publishes.")
