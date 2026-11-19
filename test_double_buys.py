#!/usr/bin/env python3
"""
ONE DEADLINE BOUGHT TWICE IS VISIBLE (watchdog.check_double_buys).

💰 `[2026-11-19]` 11-12 -> 11-19 the stored snapshots show football deadlines
bought more than once: 19 late gamelines re-buys of a deadline already on main
(194 credits, which `freshness.stand_down` now stops) and 7 buys by runs that
raced one deadline (449 credits; on 11-14 the college props pull 3 x 158).
Nothing said so. ✅ The watchdog now reports `double-buy:<kind>:<league>`,
DEGRADED with no repair, for any football deadline bought more than once in
the last 48 hours, read from the snapshots' own bills through `credits.buys`.

⛔ IT MUST NOT FIRE ON CORRECT DATA: one buy, two buys for two deadlines, a
snapshot that spent nothing, a backup that stood down (it writes nothing),
alt-lines' top-ups (each buys new games for one deadline), an MLB pull, and a
buy older than the window are all silent.

🔴 THE CLASS: every football league x every paid kind of its contract
(`freshness.paid_times`) not exempted, derived, never listed.
⛔ Planted trees only, at a pinned minute. Nothing reads production.
"""
import datetime
import gzip
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from tcheck import ck, eq, section  # noqa: E402

import freshness as F  # noqa: E402
import watchdog as W  # noqa: E402

UTC = datetime.timezone.utc
H = datetime.timedelta(hours=1)
M = datetime.timedelta(minutes=1)
NOW = datetime.datetime(2026, 11, 16, 3, 0, tzinfo=UTC)      # pinned; nothing reads today


def snap(root, lg, kind, at, used=12, half=None, n=0, balance=True):
    """One stored paid snapshot pulled at `at`, as collect.write() names it."""
    d = os.path.join(root, W.DATA[lg], at.strftime("%Y-%m-%d"), kind)
    os.makedirs(d, exist_ok=True)
    doc = {"pulled_at": at.strftime("%Y-%m-%dT%H:%M:%SZ"), "credits_used": used}
    if balance:
        doc["credits_remaining"] = 15000
    if half is not None:
        doc["half_total_credits"] = half
    name = at.strftime("%H%M") + ("-%d" % n if n else "") + ".json.gz"
    with gzip.open(os.path.join(d, name), "wt", encoding="utf-8") as fh:
        json.dump(doc, fh)


def findings(plant):
    """Plant a tree with `plant(root)`, run the check at NOW -> its findings."""
    root = tempfile.mkdtemp(prefix="doublebuy-")
    saved = W.ROOT
    try:
        plant(root)
        W.ROOT = root
        rep = W.Report()
        W.check_double_buys(rep, NOW)
        return rep.items
    finally:
        W.ROOT = saved
        shutil.rmtree(root, ignore_errors=True)


def keys(items):
    return sorted(i["key"] for i in items)


# ══════════════════════════════════════════════════════════════════════
section("1. THE CLASS, DERIVED FROM THE CONTRACT")
# ══════════════════════════════════════════════════════════════════════
FOOTBALL = [lg for lg in W.LEAGUES if lg in F.FB_TIMES]
CLASS = [(lg, k, t) for lg in FOOTBALL for k, t in sorted(F.paid_times(lg, NOW).items())
         if k not in W.DOUBLE_BUY_EXEMPT]
EXEMPT = [(lg, k, t) for lg in FOOTBALL for k, t in sorted(F.paid_times(lg, NOW).items())
          if k in W.DOUBLE_BUY_EXEMPT]
ck("⚠️ every football league's paid kinds were derived (rule 67: never empty)",
   {(lg, k) for lg, k, _t in CLASS} >= {(lg, k) for lg in ("nfl", "ncaaf")
                                        for k in ("gamelines", "props-player")},
   sorted((lg, k) for lg, k, _t in CLASS))
ck("⚠️ ...and the exemption names a real paid kind (alt-lines), nothing else",
   {k for _lg, k, _t in EXEMPT} == W.DOUBLE_BUY_EXEMPT == {"alt-lines"},
   sorted({k for _lg, k, _t in EXEMPT}))
ck("⚠️ every paid kind is a registered one (collect.PAID_KINDS)",
   {k for _lg, k, _t in CLASS + EXEMPT} <= set(W.PAID_KINDS), W.PAID_KINDS)


# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 ONE DEADLINE BOUGHT TWICE -> ONE DEGRADED FINDING, NO REPAIR")
# ══════════════════════════════════════════════════════════════════════
LO = NOW - datetime.timedelta(hours=W.DOUBLE_BUY_H)
for lg, kind, times in CLASS:
    # ⚠️ a deadline whose NEXT deadline also passed inside the window, so every
    #    buy below is one the check reads (a buy after NOW would be silent for
    #    the wrong reason: the vacuity sweep caught exactly that)
    due = F.last_due(times, NOW - 20 * H)
    nxt = F.next_due(times, due)
    second = min(due + 2 * H, nxt - M)
    key = "double-buy:%s:%s" % (kind, lg)
    tag = "%s %s (deadline %s)" % (lg, kind, due.strftime("%a %H:%MZ"))
    got = findings(lambda r: (snap(r, lg, kind, due + 5 * M, used=12),
                              snap(r, lg, kind, second, used=7)))
    # @vacuity 🔴 one deadline bought twice is reported
    #   file: watchdog.py
    #   find: if k == kind and len(g) > 1)
    #   with: if k == kind and len(g) > 99)
    eq(keys(got), [key], "🔴 %s, bought at %s and %s: one `%s`" % (
        tag, (due + 5 * M).strftime("%H:%MZ"), second.strftime("%H:%MZ"), key))
    f = (got or [{}])[0]
    ck("   ...DEGRADED, no repair, and it says how often and what it cost",
       f.get("severity") == "DEGRADED" and f.get("repair") is None
       and "bought 2 times" in f.get("what", "") and "(19 credits)" in f.get("what", "")
       and "7 credits" in f.get("why", ""), f)
    got = findings(lambda r: (snap(r, lg, kind, due + 5 * M), snap(r, lg, kind, due + 5 * M, n=1)))
    eq(keys(got), [key], "🔴 %s, two paid writes in one minute (HHMM-1): one finding" % tag)

    # ── ⛔ AND SILENT ON CORRECT DATA ────────────────────────────────────
    eq(keys(findings(lambda r: snap(r, lg, kind, due + 5 * M))), [],
       "⛔ %s bought once (a backup that stood down wrote nothing): silent" % tag)
    # @vacuity ⛔ a snapshot that spent nothing is no buy
    #   file: credits.py
    #   find:         if n <= 0:
    #   with:         if n < 0:
    eq(keys(findings(lambda r: (snap(r, lg, kind, due + 5 * M),
                                snap(r, lg, kind, second, used=0, balance=False)))), [],
       "⛔ %s, a second snapshot that spent 0 (it bought nothing): silent" % tag)
    nxt2 = F.next_due(times, nxt)
    ck("   (%s: both deadlines' buys fall inside the window it reads)" % tag,
       LO < due + 5 * M and min(nxt + 5 * M, nxt2 - M) <= NOW and second <= NOW,
       "%s .. %s" % (LO, NOW))
    # @vacuity ⛔ two deadlines are two buys, not one bought twice
    #   file: watchdog.py
    #   find: got.setdefault((kind, due), []).append((t, n))
    #   with: got.setdefault((kind, lo), []).append((t, n))
    eq(keys(findings(lambda r: (snap(r, lg, kind, due + 5 * M),
                                snap(r, lg, kind, min(nxt + 5 * M, nxt2 - M))))), [],
       "⛔ %s and the next deadline (%s), one buy each: silent" % (tag, nxt.strftime("%a %H:%MZ")))
    old = F.last_due(times, NOW - 50 * H)
    # @vacuity ⛔ only the last DOUBLE_BUY_H hours are read
    #   file: watchdog.py
    #   find: if t is not None and lo < t <= now else None
    #   with: if t is not None and t <= now else None
    eq(keys(findings(lambda r: (snap(r, lg, kind, old + 5 * M),
                                snap(r, lg, kind, old + 9 * M)))), [],
       "⛔ %s bought twice for %s, over %d hours ago: outside the window, silent" % (
           lg + " " + kind, old.strftime("%a %H:%MZ"), W.DOUBLE_BUY_H))

# 🔴 gamelines' first-half totals are a separate bill on the same snapshot.
_gl = [x for x in CLASS if x[1] == "gamelines"]
ck("⚠️ a gamelines kind exists to plant the half-totals case", _gl, CLASS)
for lg, kind, times in _gl[:1]:
    due = F.last_due(times, NOW - 3 * H)
    got = findings(lambda r: (snap(r, lg, kind, due + 5 * M),
                              snap(r, lg, kind, due + H, used=0, half=24)))
    eq(keys(got), ["double-buy:%s:%s" % (kind, lg)],
       "🔴 a second gamelines pull that billed only first-half totals (24) is a buy")


# ══════════════════════════════════════════════════════════════════════
section("3. ⛔ WHAT IS NOT ASKED: alt-lines' top-ups, and MLB")
# ══════════════════════════════════════════════════════════════════════
for lg, kind, times in EXEMPT:
    due = F.last_due(times, NOW - 3 * H)
    # @vacuity ⛔ alt-lines buys new games for one deadline: not a double buy
    #   file: watchdog.py
    #   find: DOUBLE_BUY_EXEMPT = {"alt-lines"}
    #   with: DOUBLE_BUY_EXEMPT = set()
    eq(keys(findings(lambda r: (snap(r, lg, kind, due + 5 * M, used=80),
                                snap(r, lg, kind, due + 40 * M, used=6)))), [],
       "⛔ %s %s twice for %s (new games each time): silent" % (lg, kind, due.strftime("%a %H:%MZ")))
_mlb = sorted(F.paid_times("mlb", NOW).items())
ck("⚠️ MLB's paid kinds were derived too", _mlb, _mlb)
for kind, times in _mlb:
    due = F.last_due(times, NOW - 3 * H)
    # @vacuity ⛔ MLB is not asked until its in-season pattern is measured
    #   file: watchdog.py
    #   find: for lg in [x for x in LEAGUES if x in F.FB_TIMES]:
    #   with: for lg in LEAGUES:
    eq(keys(findings(lambda r: (snap(r, "mlb", kind, due + 5 * M),
                                snap(r, "mlb", kind, due + H)))), [],
       "⛔ MLB %s twice for %s: not asked (football only)" % (kind, due.strftime("%a %H:%MZ")))

# 🔴 AND IT RUNS: the check is one of the watchdog's checks.
ck("🔴 check_double_buys is in watchdog.CHECKS", W.check_double_buys in W.CHECKS,
   [c.__name__ for c in W.CHECKS])
