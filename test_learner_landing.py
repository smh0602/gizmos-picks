#!/usr/bin/env python3
"""R1 (2026-10-18): EVERY SCHEDULED LEARNER LANDS ITS FILE, AND A TIMEOUT IS A FAILURE.
Sam: "Yes, start the Monday contest watch fix (R1) now". The weekly football contest
(fb-refit) has never run, and nothing would have said so if it timed out, went green
without committing, or stopped landing; mlb-refit.json and data/t60r/ were aged by nothing.
Planted workflow folders and data trees, pinned clocks. ⛔ Reads no live data: the real
workflow FILES are code (today's learners must be in the class), never their outputs.

# @vacuity 🔴 the class is derived: a cron workflow that commits data is a learner
#   file: watchdog.py
#   find:             if (p == "data" or p.startswith("data/")) and p not in paths:
#   with:             if p == "data/never" and p not in paths:
#
# @vacuity 🔴 a learner still missing after its first scheduled run plus grace is DEGRADED
#   file: watchdog.py
#   find:             if first is not None and now > first + grace:
#   with:             if False:
#
# @vacuity 🔴 ...and not before: the grace covers GitHub's late start
#   file: watchdog.py
#   find:             if first is not None and now > first + grace:
#   with:             if first is not None and now > first:
#
# @vacuity 🔴 ...and the job's own timeout-minutes
#   file: watchdog.py
#   find:     grace = datetime.timedelta(minutes=LANDING_LATE_MIN + lr["timeout_min"])
#   with:     grace = datetime.timedelta(minutes=LANDING_LATE_MIN)
#
# @vacuity 🔴 a file older than two periods plus grace is DEGRADED
#   file: watchdog.py
#   find:         if period is not None and now - built > 2 * period + grace:
#   with:         if period is not None and now - built > 3 * period + grace:
#
# @vacuity 🔴 ...judged by its FRESHEST file, so a written-once archive beside it is not stale
#   file: watchdog.py
#   find:         built = max(stamps)
#   with:         built = min(stamps)
#
# @vacuity 🔴 a file with no stamp is said, never read as fresh
#   file: watchdog.py
#   find:         if not stamps:
#   with:         if False:
#
# @vacuity 🔴 "since" is carried from the last health report
#   file: watchdog.py
#   find:         if since is None or since.tzinfo is None or since > now:
#   with:         if True:
#
# @vacuity 🔴 ...and a changed schedule starts it again
#   file: watchdog.py
#   find:         since = _when(was.get("since")) if (was.get("crons"), was.get("paths")) == (
#   with:         since = _when(was.get("since")) if True or (was.get("crons"), was.get("paths")) == (
#
# @vacuity 🔴 ...and health.json keeps it
#   file: watchdog.py
#   find:         out["learners"] = rep.note_learners
#   with:         pass
#
# @vacuity 🔴 the landing check runs in every watchdog pass
#   file: watchdog.py
#   find:           check_learner_landing)
#   with:           )
#
# @vacuity 🔴 a landing finding is DEGRADED, never BROKEN (it never opens the watchdog's issue)
#   file: watchdog.py
#   find:             rep.warn("landing:%s" % lr["file"][:-4], "; ".join(w for w, _y in bad),
#   with:             rep.bad("landing:%s" % lr["file"][:-4], "; ".join(w for w, _y in bad),
#
# @vacuity 🔴 git_adds reads commands, not shell comments
#   file: wfparse.py
#   find:             if s.startswith("#"):
#   with:             if s.startswith("#!"):
#
# @vacuity 🔴 ...and drops a redirection
#   file: wfparse.py
#   find:                     if tok and not tok.startswith("-") and not any(ch in tok for ch in "<>$") \
#   with:                     if tok and not tok.startswith("-") \
#
# @vacuity 🔴 job_timeouts reads each job's own limit
#   file: wfparse.py
#   find:             if jb.start <= lineno < jb.end and indent == 4 and key == "timeout-minutes":
#   with:             if jb.start <= lineno < jb.end and indent == 99 and key == "timeout-minutes":
#
# @vacuity 🔴 a timed-out or never-started run is BROKEN in runs_report
#   file: runs_report.py
#   find:         if latest.get("conclusion") in FAILED:
#   with:         if latest.get("conclusion") == "failure":
#
# @vacuity 🔴 ...and counts toward flapping
#   file: runs_report.py
#   find:         fails = [r for r in recent if r.get("conclusion") in FAILED]
#   with:         fails = [r for r in recent if r.get("conclusion") == "failure"]
"""
import atexit
import datetime
import gzip
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import runs_report as RR  # noqa: E402
import watchdog as W  # noqa: E402
import wfparse  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

UTC = datetime.timezone.utc
TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])


def tree():
    t = tempfile.mkdtemp(prefix="landing-")
    TREES.append(t)
    return t


def put(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text if isinstance(text, str) else json.dumps(text))


def at(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M").replace(tzinfo=UTC)


WF = """name: zz-learn
run-name: ${{ github.event.schedule && format('zz-learn [cron {0}]', github.event.schedule) || 'zz-learn' }}
on:
  schedule:
    - cron: "5 3 * * 3"
  workflow_dispatch:
jobs:
  learn:
    runs-on: ubuntu-24.04
    timeout-minutes: 120
    steps:
      - uses: actions/checkout@v5
      - name: Ask an agent
        uses: some/action@v1
        with:
          prompt: |
            then git add data/prompt.json and push
      - name: Learn
        run: |
          # git add data/never/this.json  (a comment, not a command)
          python learn.py
      - name: Commit
        run: |
          git add data/zz/report.json data/zz/old-*.json.gz data/zzdir/ 2>/dev/null || true
          bash push_retry.sh zz
  other:
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    steps:
      - run: echo hi
"""
PLAIN = """name: plain
on:
  schedule:
    - cron: "1 1 * * *"
jobs:
  a:
    runs-on: ubuntu-24.04
    steps:
      - run: git add data/plain.json
"""
PATHS = ["data/zz/report.json", "data/zz/old-*.json.gz", "data/zzdir"]

# ══════════════════════════════════════════════════════════════════════
section("1. wfparse: WHAT A WORKFLOW COMMITS, AND ITS JOBS' TIME LIMITS")
# ══════════════════════════════════════════════════════════════════════
eq(wfparse.git_adds(WF), ["data/zz/report.json", "data/zz/old-*.json.gz", "data/zzdir/"],
   "🔴 every `git add` path in a run: body, never a shell comment, a prompt's text or a redirection")
eq((wfparse.job_timeouts(WF), wfparse.job_timeouts(PLAIN)), ({"learn": 120, "other": 5}, {"a": None}),
   "🔴 each job's own timeout-minutes, None when unset")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE CLASS IS DERIVED: TODAY'S THREE LEARNERS ARE IN IT, AND NO EXCLUSION IS DEAD")
# ══════════════════════════════════════════════════════════════════════
got = {lr["file"]: lr for lr in W.learners()}
ck({"fb-refit.yml", "mlb-refit.yml", "t60r.yml"} <= set(got),
   "🔴 fb-refit, mlb-refit and t60r are scheduled learners, read from their own workflow files", sorted(got))
eq((got.get("fb-refit.yml") or {}).get("paths"), ["data/*/latest/fb-refit.json"],
   "   ...fb-refit's path comes from its `git add` line")
eq((got.get("t60r.yml") or {}).get("paths"), ["data/t60r"], "   ...and t60r's is its whole folder")
_decl = {d["file"]: d for d in RR.declared_crons(W.LANDING_ROOT).values()}
_dead = [f for f in W.NOT_LEARNERS if f not in _decl or not any(
    p.rstrip("/") == "data" or p.startswith("data/")
    for p in wfparse.git_adds(os.path.join(W.LANDING_ROOT, ".github", "workflows", f)))]
eq(_dead, [], "🔴 every NOT_LEARNERS entry is still a cron workflow that commits data (no dead exclusion)")
ck(not set(W.NOT_LEARNERS) & set(got), "   ...and none of them is judged")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 A PLANTED LEARNER: MISSING, LANDED, STALE, UNSTAMPED")
# ══════════════════════════════════════════════════════════════════════
CODE, DATA = tree(), tree()
put(CODE, ".github/workflows/zz-learn.yml", WF)
put(CODE, ".github/workflows/plain.yml", PLAIN.replace("git add data/plain.json", "echo nothing committed"))
CODE2 = tree()
put(CODE2, ".github/workflows/plain.yml", PLAIN)
_wf, _root, _prev = W.LANDING_ROOT, W.ROOT, W._previous
SINCE = "2026-10-12T00:00:00Z"
PREV = {"learners": {"zz-learn.yml": {"crons": ["5 3 * * 3"], "paths": PATHS, "since": SINCE}}}


def judge(now, prev=PREV):
    W._previous = lambda: prev
    rep = W.Report()
    W.check_learner_landing(rep, now)
    return rep


try:
    W.LANDING_ROOT, W.ROOT = CODE, DATA
    eq(W.learners(), [{"file": "zz-learn.yml", "crons": ["5 3 * * 3"], "paths": PATHS, "timeout_min": 120}],
       "🔴 a NEW cron workflow that commits data is covered with no code change; one that commits nothing is not")
    eq([x["timeout_min"] for x in W.learners(CODE2)], [360], "   ...and a job with no limit has GitHub's 360 minutes")
    # first run since 10-12: Wed 10-14 03:05Z; grace 600 + 120 minutes -> 15:05Z
    eq([i["key"] for i in judge(at("2026-10-14T14:00")).items], [],
       "🔴 missing 11 hours after its first run is still inside 10 hours + its 2-hour job limit")
    rep = judge(at("2026-10-14T15:06"))
    eq([(i["key"], i["severity"], i["repair"]) for i in rep.items], [("landing:zz-learn", "DEGRADED", None)],
       "🔴 ...and past it, DEGRADED with no repair")
    ck(rep.items and rep.items[0]["what"].startswith("zz-learn has not landed data/zz/report.json")
       and "was due Wed 2026-10-14 03:05Z" in rep.items[0]["why"],
       "   ...naming the file and the run that was due", rep.items and rep.items[0])
    ck(not W.alerting({"findings": rep.items}), "🔴 ...which never opens the watchdog's issue (DEGRADED only)")
    eq([i["key"] for i in judge(at("2026-10-14T15:06"), prev={}).items], [],
       "🔴 a learner first seen NOW is not judged missing before its next run (fail-safe, never early)")
    put(DATA, "data/zz/report.json", {"built_at": "2026-10-14T16:00:00Z"})
    put(DATA, "data/zzdir/a.json", {"pulled_at": "2026-10-14T16:00:00Z"})
    put(DATA, "data/zzdir/b.json", {"no": "stamp"})              # a folder is judged by its stamped files
    for _n, _s in (("old-2025", "2026-01-01T00:00:00Z"), ("old-2026", "2026-10-14T16:00:00Z")):
        with gzip.open(os.path.join(DATA, "data/zz/%s.json.gz" % _n), "wt") as _fh:
            json.dump({"built_at": _s}, _fh)
    eq([i["key"] for i in judge(at("2026-10-20T12:00")).items], [],
       "🔴 landed: silent, though old-2025 (written once in January) sits beside the fresh one")
    eq([i["key"] for i in judge(at("2026-10-29T03:59")).items], [],
       "🔴 built 10-14 16:00 and weekly: still silent at 14 days 12 hours")
    rep = judge(at("2026-10-29T04:01"))
    ck([i["key"] for i in rep.items] == ["landing:zz-learn"] and rep.items[0]["what"]
       == "zz-learn's data/zz/report.json, data/zz/old-*.json.gz, data/zzdir are 14 days old",
       "🔴 ...and DEGRADED past two runs plus grace, every path that stopped", rep.items and rep.items[0]["what"])
    put(DATA, "data/zz/report.json", {"no": "time"})
    ck(any("data/zz/report.json carries no time" in i["what"] for i in judge(at("2026-10-20T12:00")).items),
       "🔴 a file with no stamp is said, never read as fresh")
    put(DATA, "data/zz/report.json", {"built_at": "2026-10-14T16:00:00Z"})
    W._previous = lambda: PREV
    out = W.run(at("2026-10-20T12:00"))
    eq((out.get("learners") or {}).get("zz-learn.yml"), {"crons": ["5 3 * * 3"], "paths": PATHS, "since": SINCE},
       "🔴 health.json carries each learner's first-seen time forward")
    put(CODE, ".github/workflows/zz-learn.yml", WF.replace('"5 3 * * 3"', '"5 3 * * 4"'))
    eq(judge(at("2026-10-20T12:00")).note_learners["zz-learn.yml"]["since"], "2026-10-20T12:00:00Z",
       "🔴 ...and a changed cron starts it again (a new schedule has no first run yet)")
finally:
    W.LANDING_ROOT, W.ROOT, W._previous = _wf, _root, _prev

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 MONDAY 2026-10-19: THE REAL fb-refit.yml AGAINST A TREE WITH NO REPORT")
# ══════════════════════════════════════════════════════════════════════
EMPTY = tree()
lr = {x["file"]: x for x in W.learners()}["fb-refit.yml"]
seen = "2026-10-18T03:00:00Z"
first = W.cron_fires(lr["crons"], at("2026-10-18T03:00"), at("2026-10-26T03:00"))[0]
grace = datetime.timedelta(minutes=W.LANDING_LATE_MIN + lr["timeout_min"])
print("  first scheduled run after %s: %s; DEGRADED from %s" % (seen, first, first + grace))
_root, _prev = W.ROOT, W._previous
try:
    W.ROOT = EMPTY
    W._previous = lambda: {"learners": {"fb-refit.yml": {"crons": lr["crons"], "paths": lr["paths"], "since": seen}}}
    _keys = lambda now: [i["key"] for i in (lambda r: (W.check_learner_landing(r, now), r)[1])(W.Report()).items]  # noqa: E731,E501
    eq(_keys(first + grace - datetime.timedelta(minutes=1)), [], "🔴 no report yet, inside the grace: silent")
    eq(_keys(first + grace + datetime.timedelta(minutes=1)), ["landing:fb-refit"],
       "🔴 no report past it: DEGRADED (the contest never landed)")
    put(EMPTY, "data/nfl/latest/fb-refit.json", {"built_at": (first + datetime.timedelta(hours=9)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")})
    eq(_keys(first + grace + datetime.timedelta(minutes=1)), [], "   ...and silent once it lands")
finally:
    W.ROOT, W._previous = _root, _prev

# ══════════════════════════════════════════════════════════════════════
section("5. cron_fires AND last_due_for")
# ══════════════════════════════════════════════════════════════════════
eq(W.cron_fires(["47 9 * * 1"], at("2026-10-12T00:00"), at("2026-10-26T23:59")),
   [at("2026-10-12T09:47"), at("2026-10-19T09:47"), at("2026-10-26T09:47")], "weekly Mondays, Sunday-0 dow")
eq(W.cron_fires(["0 0 * * 0", "0 0 * * 7"], at("2026-10-17T00:00"), at("2026-10-19T00:00")),
   [at("2026-10-18T00:00")], "   ...Sunday is 0 and 7, once")
ck(W.last_due_for("data/latest/not-a-learners-file.json", at("2026-10-19T11:17")) is None,
   "a file no learner commits has no due run")

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 runs_report: A TIMED-OUT OR NEVER-STARTED RUN IS BROKEN")
# ══════════════════════════════════════════════════════════════════════
NOW6 = at("2026-10-19T22:00")
NOWF = tree()


def runs(*conc):
    return [{"workflowName": "fb-refit", "name": "fb-refit [cron 47 9 * * 1]", "conclusion": c,
             "createdAt": (NOW6 - datetime.timedelta(hours=1 + i)).strftime("%Y-%m-%dT%H:%M:%SZ"), "url": "u%d" % i}
            for i, c in enumerate(conc)]


_b = {c: [x["name"] for x in RR.analyse(runs(c), NOW6, root=NOWF)[0]]
      for c in ("timed_out", "startup_failure", "failure", "success", "cancelled")}
eq(_b, {"timed_out": ["fb-refit"], "startup_failure": ["fb-refit"], "failure": ["fb-refit"], "success": [],
        "cancelled": []}, "🔴 timed_out and startup_failure are BROKEN like failure; success and cancelled are not")
eq([x["fails_24h"] for x in RR.analyse(runs("success", "timed_out", "timed_out", "failure"), NOW6,
                                       root=NOWF)[1]], [3],
   "🔴 ...and a green run after three timeouts and failures is FLAPPING")
