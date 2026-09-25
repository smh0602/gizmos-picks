#!/usr/bin/env python3
"""
THE FOOTBALL RECORD, REBUILT FROM THIS CHECKOUT'S OWN CODE — THEN CHECKED.

🔴🔴 THE GAP THIS CLOSES. `[2026-09-24]` PR #158 split the football
record's calibration by card method. It passed pr-tests, merged, and main
went red at the 21:50Z rebuild: `calibration` was now the NEW method's
buckets, empty until its first slate is graded, and the Track Record tab
drew no football bands at all.
⛔ pr-tests could not see it because every record check read the
COMMITTED `data/<lg>/latest/record.json` — a file written by the code on
`main`, not by the PR. A PR that changes the record's shape is tested
against the old shape, and the new shape first meets a check after merge.

✅ SO THIS FILE NEVER READS THE COMMITTED RECORD. It runs this checkout's
`record_fb.py` over a throwaway copy of the stored cards and player logs,
for BOTH leagues, and asks the record and the page's own renderer the
questions `test_record_fb.py` and `test_fb_record.py` ask:
  1. every graded row with a confidence is in exactly one method's buckets
  2. `calibration` is the current method's buckets, never a pool
  3. the tab draws one labelled table per method, current first
  4. no band on any table says "we said"
  5. a method with nothing graded is REPORTED and says so on the page —
     never a failure, never a blank

⚠️ THREE STATES OF THE STORED DATA, because the defect lived in a state
the stored data was not in when the PR was tested:
  STORED       — the cards exactly as they are on disk
  NEXT METHOD  — plus tomorrow's card under a method nothing has graded:
                 the state main was in the night #158 merged
  TWO GRADED   — one graded card re-stamped with a second method, so two
                 methods BOTH hold graded rows and a pool would show
⛔ The re-stamped cards are FIXTURES in a temp directory. Nothing under
`data/` or `picks/` is written.
"""
import glob
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

from tcheck import ck, eq, note, section

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsblock import js_block  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(ROOT, "index.html")
BEFORE = "2025-only"
PROBE_NEXT = "probe-next-method"
PROBE_GRADED = "probe-second-method"


# ══════════════════════════════════════════════════════════════════════
# @vacuity two methods' graded rows must never be pooled into one
#   file: record_fb.py
#   find: per.setdefault(r.get("card_method") or METHOD_BEFORE, {}).setdefault(
#   with: per.setdefault(METHOD_BEFORE, {}).setdefault(
#
# @vacuity a method that is not current must keep its buckets
#   file: record_fb.py
#   find: for m, bk in per.items()}
#   with: for m, bk in per.items() if m == current}
#
# @vacuity the current method is the NEWEST card's, not the first one's
#   file: record_fb.py
#   find: _current = next((r.get("card_method") for d in reversed(days) for r in d["rows"]
#   with: _current = next((r.get("card_method") for d in days for r in d["rows"]
#
# @vacuity the page must draw every method, not `calibration` alone
#   file: index.html
#   find: const order = [cur, ...Object.keys(by).filter(m => m !== cur)];
#   with: const order = [cur];
#
# @vacuity an empty method says so on the page
#   file: index.html
#   find: return label ? `${head}<div class="fb-cal-empty" style="margin:0 0 8px;font-size:12.5px;color:var(--mut)">No graded
#   with: return label ? `${head}<div class="fb-cal-empty" style="margin:0 0 8px;font-size:12.5px;color:var(--mut)">
# ══════════════════════════════════════════════════════════════════════


def rebuild(lg, mutate=None):
    """Run THIS checkout's record_fb.py on a temp copy. -> (R, D, rc, log)."""
    tmp = tempfile.mkdtemp(prefix="recfb-rebuild-")
    shutil.copytree(os.path.join(ROOT, "data", lg),
                    os.path.join(tmp, "data", lg))
    os.makedirs(os.path.join(tmp, "picks"))
    for f in glob.glob(os.path.join(ROOT, "picks", "fb-%s-*.json" % lg)):
        shutil.copy(f, os.path.join(tmp, "picks"))
    # ⛔ THE COMMITTED OUTPUT IS REMOVED FIRST, so a run that writes
    #    nothing cannot be read as a run that wrote the old file.
    for f in ("record.json", "record-detail.json.gz"):
        p = os.path.join(tmp, "data", lg, "latest", f)
        if os.path.exists(p):
            os.remove(p)
    if mutate:
        mutate(os.path.join(tmp, "picks"))
    env = dict(os.environ, LEAGUE=lg)
    p = subprocess.run([sys.executable, os.path.join(ROOT, "record_fb.py")],
                       cwd=tmp, env=env, capture_output=True, text=True,
                       timeout=900)
    R = D = None
    rp = os.path.join(tmp, "data", lg, "latest", "record.json")
    dp = os.path.join(tmp, "data", lg, "latest", "record-detail.json.gz")
    if os.path.exists(rp):
        R = json.load(open(rp, encoding="utf-8"))
    if os.path.exists(dp):
        D = json.load(gzip.open(dp, "rt"))
    shutil.rmtree(tmp, ignore_errors=True)
    return R, D, p.returncode, (p.stdout or "") + (p.stderr or "")


def dated_cards(pdir, lg):
    return sorted(f for f in glob.glob(os.path.join(pdir, "fb-%s-*.json" % lg))
                  if not f.endswith("-latest.json"))


def add_next_method_card(lg):
    """Tomorrow's card, under a method nothing has graded yet."""
    def m(pdir):
        newest = dated_cards(pdir, lg)[-1]
        card = json.load(open(newest, encoding="utf-8"))
        d = card.get("date") or os.path.basename(newest)[len("fb-%s-" % lg):-5]
        nxt = (datetime.strptime(d, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        card["date"] = nxt
        card["card_method"] = PROBE_NEXT
        # ⚠️ Kickoffs beyond any log, so nothing on it can settle — the
        #    state of a card the night it is published.
        for p in card.get("picks") or []:
            p["commence"] = "2099-12-31T00:00:00Z"
        json.dump(card, open(os.path.join(pdir, "fb-%s-%s.json" % (lg, nxt)),
                             "w", encoding="utf-8"))
    return m


def restamp_graded_card(lg, date):
    """One card that HAS graded rows, re-stamped with a second method."""
    def m(pdir):
        f = os.path.join(pdir, "fb-%s-%s.json" % (lg, date))
        card = json.load(open(f, encoding="utf-8"))
        card["card_method"] = PROBE_GRADED
        json.dump(card, open(f, "w", encoding="utf-8"))
    return m


def page(R):
    """The tab's own `fbCalMethods`, run under node on record `R`."""
    src = "\n".join(js_block(n, IDX) for n in ("bandRow", "fbCalBlock",
                                               "fbCalMethods"))
    decl = re.search(r"^const FB_METHOD_BEFORE = '[^']*';",
                     open(IDX, encoding="utf-8").read(), re.M)
    assert decl, "index.html no longer declares FB_METHOD_BEFORE"
    prog = (decl.group(0) + "\n"
            "const sgn = v => v == null ? '-' : (v > 0 ? '+' + v : '' + v);\n"
            + src + "\nconst REC = " + json.dumps(R) + ";\n"
            "const h = fbCalMethods(REC);"
            "const heads=[...h.matchAll(/Was the record right\\? <span[^>]*>&mdash; ([^<]*)</g)].map(m=>m[1]);"
            "const parts=h.split('Was the record right?').slice(1).map(x=>(x.match(/class=\"band\"/g)||[]).length);"
            "const empties=[...h.matchAll(/No graded\\s+picks under the ([^<]*?) yet/g)].map(m=>m[1]);"
            "console.log(JSON.stringify({heads, parts, empties,"
            " weSaid:(h.match(/we said/g)||[]).length,"
            " claimed:(h.match(/title=\"the record claimed/g)||[]).length}));")
    d = tempfile.mkdtemp(prefix="recfb-page-")
    f = os.path.join(d, "probe.js")
    open(f, "w", encoding="utf-8").write(prog)
    p = subprocess.run(["node", f], capture_output=True, text=True, timeout=120)
    shutil.rmtree(d, ignore_errors=True)
    for line in (p.stdout or "").splitlines():
        if line.startswith("{"):
            return json.loads(line)
    return {"__rc": p.returncode, "__out": ((p.stdout or "") + (p.stderr or ""))[-400:]}


def check(lg, tag, R, D, rc, log, expect_methods=None, expect_current=None):
    """The record and the page questions, asked of one rebuilt record."""
    ok = rc == 0 and R is not None and D is not None
    ck(ok, "%s %s: this checkout's record_fb.py rebuilt both files" % (lg, tag),
       "rc=%s %s" % (rc, log[-300:]))
    if not ok:
        return
    by = R.get("calibration_by_method")
    cur = R.get("card_method_current")
    ck(isinstance(by, dict) and isinstance(cur, str),
       "   %s: the record carries `calibration_by_method` and its current method" % tag,
       "current=%r" % cur)
    by = by or {}
    graded = [r for rows in (D.get("days") or {}).values() for r in rows
              if r.get("won") is not None and r.get("confidence") is not None]
    want = {}
    for r in graded:
        m = r.get("card_method") or BEFORE
        want[m] = want.get(m, 0) + 1
    got = {m: sum(c["n"] for c in v) for m, v in by.items()}
    ck(got == want and sum(got.values()) == len(graded),
       "🔴🔴 %s %s: every graded row with a confidence is in exactly one "
       "method's buckets" % (lg, tag),
       "buckets %s vs detail rows %s (of %d)" % (got, want, len(graded)))
    ck(R.get("calibration") == by.get(cur, []),
       "   %s: `calibration` is the current method's buckets, never a pool" % tag,
       "current=%r" % cur)
    if expect_current is not None:
        eq(cur, expect_current,
           "   %s: the current method is the NEWEST card's" % tag)
    if expect_methods is not None:
        eq(sorted(got), sorted(expect_methods),
           "   %s: the methods holding graded rows are the ones stamped" % tag)

    P = page(R)
    order = [cur] + [m for m in by if m != cur]
    label = {m: ("current method" if m == cur else
                 "2025-only method" if m == BEFORE else
                 "earlier method (%s)" % m) for m in order}
    eq(P.get("heads"), [label[m] for m in order],
       "🔴 %s %s: the tab draws one labelled table per method, current first"
       % (lg, tag))
    eq(P.get("parts"), [len(by.get(m) or []) for m in order],
       "   %s: each table holds exactly its own method's bands" % tag)
    eq(P.get("claimed"), sum(len(v) for v in by.values()),
       "   %s: every band names the record as the claimant" % tag)
    eq(P.get("weSaid"), 0,
       "🔴🔴 %s %s: NO band on any table says \"we said\"" % (lg, tag))
    empty = [label[m] for m in order if not by.get(m)]
    eq(P.get("empties"), empty,
       "🔴 %s %s: a method with nothing graded says so — and only that one"
       % (lg, tag))
    for m in order:
        if not by.get(m):
            note("⚠️ %s %s: method %r has no graded picks yet — reported, "
                 "not failed" % (lg, tag, m))


for lg in ("nfl", "ncaaf"):
    section("%s — REBUILT FROM THIS CHECKOUT'S record_fb.py" % lg.upper())

    R, D, rc, log = rebuild(lg)
    check(lg, "STORED", R, D, rc, log)

    R2, D2, rc2, log2 = rebuild(lg, add_next_method_card(lg))
    check(lg, "NEXT METHOD", R2, D2, rc2, log2, expect_current=PROBE_NEXT)
    if R2 is not None:
        ck(R2.get("calibration") == [] and any(
               v for v in (R2.get("calibration_by_method") or {}).values()),
           "   NEXT METHOD: the new method is empty while earlier ones are "
           "graded — the exact state main was in when #158 merged",
           "⛔ if this is not the state, the section above did not test it")

    # ⚠️ A card with graded rows, taken from the rebuild's own detail file.
    graded_dates = sorted(d for d, rows in ((D or {}).get("days") or {}).items()
                          if any(r.get("won") is not None
                                 and r.get("confidence") is not None
                                 for r in rows))
    ck(len(graded_dates) >= 2,
       "   %s: at least two stored cards hold graded rows (%d)"
       % (lg, len(graded_dates)),
       "⛔ with fewer, TWO GRADED cannot hold two graded methods and "
       "would prove nothing")
    if len(graded_dates) >= 2:
        R3, D3, rc3, log3 = rebuild(lg, restamp_graded_card(lg, graded_dates[-1]))
        before = sorted({(r.get("card_method") or BEFORE)
                         for d, rows in D["days"].items()
                         if d != graded_dates[-1] for r in rows
                         if r.get("won") is not None
                         and r.get("confidence") is not None})
        check(lg, "TWO GRADED", R3, D3, rc3, log3,
              expect_methods=sorted(set(before) | {PROBE_GRADED}))

note("⛔ WHAT THIS DOES NOT CLAIM: that the stored data is correct, or that "
     "the tab LOOKS right in a browser. It claims the record this "
     "checkout's code WOULD write — today, the night a new method goes "
     "live, and once two methods both hold graded rows — keeps every "
     "method apart, and that the tab draws each one under its own label.")
