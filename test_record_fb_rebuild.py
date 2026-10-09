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
#
# @vacuity 🔴 rule 67 on the planted tree: its three cards really are graded (the join settles them)
#   file: record_fb.py
#   find: hits.append(g)
#   with: pass
# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# 🔴 THE PLANTED TREE. `[2026-09-28]` The three states were built only
#    from the STORED cards, so NEXT METHOD needed stored graded rows and
#    TWO GRADED needed two stored graded cards (pattern P3): after a record
#    reset (`RECORD_FROM` moved), at a new lane, or on a slim tree, the
#    rule-67 check went red on correct code — and every declared mutation
#    above, which bites only through those states, went quiet with it.
# ✅ So all three states are ALSO built from a tree this file writes:
#    three graded cards (two under the method before the split, one under
#    the fixed method) and a players log that settles them, with the floor
#    pinned below them. The stored data is rebuilt as well, as an extra.
# ══════════════════════════════════════════════════════════════════════
PLANT_DATES = ("2026-09-12", "2026-09-19", "2026-09-26")
PLANT_METHOD = {"2026-09-26": "season-blend"}
PLANT_FLOOR = "2026-09-01"
PLANT_NAMES = ("Plant Alpha", "Plant Bravo", "Plant Charlie")


def plant(lg, tmp):
    """Write the planted cards and the log that grades them into `tmp`."""
    lat = os.path.join(tmp, "data", lg, "latest")
    os.makedirs(lat)
    os.makedirs(os.path.join(tmp, "picks"))
    players = {"p%d" % k: {"name": nm, "pos": "WR", "g": [
        {"d": d, "week": i + 1, "rec": 3 + k, "rec_yds": 30 + 20 * k, "car": 1,
         "rush_yds": 5, "rec_td": 0, "rush_td": 0, "pass_yds": 0, "pass_td": 0,
         "att": 0, "snaps": 40, "snap_pct": 0.8, "team": "T%d" % k}
        for i, d in enumerate(PLANT_DATES)]} for k, nm in enumerate(PLANT_NAMES)}
    with gzip.open(os.path.join(lat, "players-2026.json.gz"), "wt") as fh:
        json.dump({"season": 2026, "players": players}, fh)
    for d in PLANT_DATES:
        picks = [{"player": nm, "market": "player_reception_yds", "side": "over",
                  "line": 40.5, "price": -110, "book": "fanduel",
                  "confidence": 60 + 5 * k, "confidence_basis": "RECORD",
                  "raw": "%d of 10" % (5 + k), "commence": d + "T17:00:00Z",
                  "game": "A%d @ H%d" % (k, k), "break_even": 52.4}
                 for k, nm in enumerate(PLANT_NAMES)]
        # ⚠️ AND ONE UNRATED ROW: graded, but in no method's buckets.
        picks.append({"player": PLANT_NAMES[0], "market": "player_receptions",
                      "side": "under", "line": 3.5, "price": -120,
                      "book": "fanduel", "confidence_basis": "MARKET",
                      "commence": d + "T17:00:00Z", "game": "A0 @ H0"})
        card = {"date": d, "league": lg, "logs_season": 2025, "picks": picks}
        if d in PLANT_METHOD:
            card["card_method"] = PLANT_METHOD[d]
        json.dump(card, open(os.path.join(tmp, "picks", "fb-%s-%s.json" % (lg, d)),
                             "w", encoding="utf-8"))


def rebuild(lg, mutate=None, planted=False):
    """Run THIS checkout's record_fb.py on a temp copy — of the stored data,
    or of the planted tree. -> (R, D, rc, log)."""
    tmp = tempfile.mkdtemp(prefix="recfb-rebuild-")
    if planted:
        plant(lg, tmp)
    else:
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
    if planted:
        # ⛔ the planted cards are graded whatever the source's floor is set to
        env["FB_RECORD_FROM"] = PLANT_FLOOR
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
    """The night a new method goes live: a card dated after every other one,
    under a method nothing has graded yet.
    ⚠️ `[2026-10-09]` BUILT, NOT BORROWED. It was a copy of the newest stored
    card, and ncaaf's 10-08 card held 0 picks (10 game lines): the copy had no
    rows, the record dropped it, the new method never became current, and
    collect went red 10-08 -> 10-09. So a games-only card is ALWAYS planted
    newest first, and the new card takes the picks of the newest card that
    has some. Nothing here reads a clock: record_fb grades on the stored logs."""
    def m(pdir):
        fs = dated_cards(pdir, lg)
        last = datetime.strptime(os.path.basename(fs[-1])[len("fb-%s-" % lg):-5], "%Y-%m-%d")

        def put(k, card):
            d = (last + timedelta(days=k)).strftime("%Y-%m-%d")
            json.dump(dict(card, date=d), open(os.path.join(pdir, "fb-%s-%s.json" % (lg, d)),
                                               "w", encoding="utf-8"))
        put(1, dict(json.load(open(fs[-1], encoding="utf-8")), picks=[]))     # games only
        src = [c for c in (json.load(open(f, encoding="utf-8")) for f in dated_cards(pdir, lg)) if c.get("picks")][-1]
        # ⚠️ Kickoffs beyond any log, so nothing on it can settle — the
        #    state of a card the night it is published.
        put(2, dict(src, card_method=PROBE_NEXT,
                    picks=[dict(p, commence="2099-12-31T00:00:00Z") for p in src["picks"]]))
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


def graded_dates_of(D):
    """Card dates holding a graded row with a confidence, from a detail file."""
    return sorted(d for d, rows in ((D or {}).get("days") or {}).items()
                  if any(r.get("won") is not None
                         and r.get("confidence") is not None for r in rows))


def three_states(lg, planted):
    """STORED, NEXT METHOD and TWO GRADED, on the planted tree or the stored data."""
    src = "PLANTED" if planted else "STORED DATA"
    R, D, rc, log = rebuild(lg, planted=planted)
    check(lg, "%s" % src, R, D, rc, log,
          expect_methods=(sorted({BEFORE, "season-blend"}) if planted else None),
          expect_current=("season-blend" if planted else None))
    graded_dates = graded_dates_of(D)
    if planted:
        # ⚠️ RULE 67, ON THE TREE THIS FILE WROTE: the case must exist.
        if not ck(graded_dates == list(PLANT_DATES),
                  "   %s PLANTED: all three planted cards hold graded rows" % lg,
                  "⛔ with fewer, TWO GRADED cannot hold two graded methods and "
                  "would prove nothing. got %s" % graded_dates):
            return
    elif len(graded_dates) < 2:
        note("⚠️ NOT EXERCISED ON THE STORED DATA (%s): %d stored card(s) hold "
             "graded rows — a record reset or a new lane. The planted tree "
             "asked every question." % (lg, len(graded_dates)))
        return
    R2, D2, rc2, log2 = rebuild(lg, add_next_method_card(lg), planted=planted)
    check(lg, "%s + NEXT METHOD" % src, R2, D2, rc2, log2, expect_current=PROBE_NEXT)
    if R2 is not None:
        ck(R2.get("calibration") == [] and any(
               v for v in (R2.get("calibration_by_method") or {}).values()),
           "   %s %s NEXT METHOD: the new method is empty while earlier ones are "
           "graded — the exact state main was in when #158 merged" % (lg, src),
           "⛔ if this is not the state, the section above did not test it")
    R3, D3, rc3, log3 = rebuild(lg, restamp_graded_card(lg, graded_dates[-1]),
                                planted=planted)
    before = sorted({(r.get("card_method") or BEFORE)
                     for d, rows in D["days"].items()
                     if d != graded_dates[-1] for r in rows
                     if r.get("won") is not None
                     and r.get("confidence") is not None})
    check(lg, "%s + TWO GRADED" % src, R3, D3, rc3, log3,
          expect_methods=sorted(set(before) | {PROBE_GRADED}))


for lg in ("nfl", "ncaaf"):
    section("%s — REBUILT FROM THIS CHECKOUT'S record_fb.py" % lg.upper())
    three_states(lg, planted=True)
    three_states(lg, planted=False)

note("⛔ WHAT THIS DOES NOT CLAIM: that the stored data is correct, or that "
     "the tab LOOKS right in a browser. It claims the record this "
     "checkout's code WOULD write — today, the night a new method goes "
     "live, and once two methods both hold graded rows — keeps every "
     "method apart, and that the tab draws each one under its own label.")
