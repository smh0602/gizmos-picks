#!/usr/bin/env python3
r"""A RUN ITS CLOCK STOPPED IS A FAILED RUN, AND GITHUB NEVER SAYS SO.

🔴 `[2026-11-01]` The nightly sweep hit its 120-minute clock on 9 of 15 nights
and no watcher said a word. `runs_report.FAILED` listed `timed_out`, and my
R1 comment said GitHub reports a timeout that way. It does not: run, job and
step all read `cancelled` (`status=timed_out` returned 0 rows, 16 real
timeouts read `cancelled`). `test_learner_landing.py` planted the word GitHub
never sends, so it stayed green through all of it.

✅ WHAT THIS PINS, through the real `collect()`, for ANY workflow: the class is
"a job reached its own `timeout-minutes`", read from the workflow file.
  1. a clock kill reaches both readers: `analyse()` (broken, flapping) and
     `status_doc()` (n_failed, by_workflow.failed);
  2. runs.json names the step, and annotations are read only there;
  3. a concurrency cancel past the workflow's SHORTEST clock stays cancelled:
     the job's OWN clock decides (the real 40472931447: 25.3 minutes, shortest
     25, own clock 120);
  4. a run that could not be a timeout costs no API call;
  5. the shortest clock finds the candidates, and the job's name finds its clock;
  6. what cannot be read is reported, never read as fine;
  7. ⛔ `collect()` never reads an annotation: runs.yml's `watch` job holds no
     `checks: read`, so the fake here refuses them as that token would;
  8. both ways in, `--collect` (watch) and `--status-file` (publish);
  9. a job's clock is found by the name it lists under, never by its id: only
     a job that could carry that name counts, and the shortest of them decides,
     so a renamed job can never read a longer clock than its own.

⚠️ Everything is planted: workflow files, clocks, runs, jobs. Nothing here reads
a real workflow or a stored run, and the clock is the real one.

# @vacuity 🔴 the mark is what makes a clock kill a failure at all
#   file: runs_report.py
#   find:         mark_timeouts(batch, clocks, fetch_json or _gh_json)
#   with:         pass
#
# @vacuity 🔴 the mark comes BEFORE normalise(), or analyse() never sees it
#   file: runs_report.py
#   find:         runs.extend(normalise(r, names) for r in batch)
#   with:         runs.extend(normalise(dict(r or {}, conclusion="cancelled" if (r or {}).get("conclusion") == "timed_out" else (r or {}).get("conclusion")), names) for r in batch)
#
# @vacuity 🔴 the run's elapsed time finds the candidates
#   file: runs_report.py
#   find:     return (b - a).total_seconds() >= _shortest(mine) * 60
#   with:     return False
#
# @vacuity 🔴 the job's OWN clock decides, never the workflow's shortest (40472931447)
#   file: runs_report.py
#   find:                 and (b - a).total_seconds() >= _own_clock(j.get("name"), clocks) * 60:
#   with:                 and (b - a).total_seconds() >= _shortest(clocks) * 60:
#
# @vacuity 🔴 the SHORTEST clock finds the candidates, or a short job's timeout is missed
#   file: runs_report.py
#   find:     return min(clocks.values(), default=DEFAULT_CLOCK)
#   with:     return max(clocks.values(), default=DEFAULT_CLOCK)
#
# @vacuity 🔴 a jobs call that fails reports: ignorance never buys silence
#   file: runs_report.py
#   find:         return True     # the call failed: ignorance never buys silence
#   with:         return False
#
# @vacuity 🔴 a job with no conclusion counts (the stuck run)
#   file: runs_report.py
#   find:         if not j.get("conclusion") or b is None:
#   with:         if b is None:
#
# @vacuity 🔴 ...and so does a job with no end time
#   file: runs_report.py
#   find:         if not j.get("conclusion") or b is None:
#   with:         if not j.get("conclusion"):
#
# @vacuity a row with no time on it is asked about, never passed
#   file: runs_report.py
#   find:         return True     # no time on the row: ask the jobs
#   with:         return False
#
# @vacuity 🔴 a path with no clock (Pages) is never judged
#   file: runs_report.py
#   find:     if r.get("conclusion") != "cancelled" or mine is None:
#   with:     if r.get("conclusion") != "cancelled":
#
# @vacuity 🔴 only a cancelled run is a candidate: a long green run costs no call
#   file: runs_report.py
#   find:     if r.get("conclusion") != "cancelled" or mine is None:
#   with:     if mine is None:
#
# @vacuity a job with no timeout-minutes has GitHub's own limit
#   file: runs_report.py
#   find: DEFAULT_CLOCK = 360     # GitHub's limit for a job that sets no `timeout-minutes`
#   with: DEFAULT_CLOCK = 300     # GitHub's limit for a job that sets no `timeout-minutes`
#
# @vacuity only a CANCELLED job can be a clock kill
#   file: runs_report.py
#   find:         if j["conclusion"] == "cancelled" and a is not None \
#   with:         if a is not None \
#
# @vacuity a job that never started ran no clock
#   file: runs_report.py
#   find:         if j["conclusion"] == "cancelled" and a is not None \
#   with:         if j["conclusion"] == "cancelled" \
#
# @vacuity 🔴 an expression in a `name:` can expand to anything (`tests · sweep 2/4`)
#   file: runs_report.py
#   find:     return re.fullmatch(".*".join(parts) + r"( \(.*\))?", name) is not None
#   with:     return re.fullmatch("".join(parts) + r"( \(.*\))?", name) is not None
#
# @vacuity 🔴 a matrix job is listed with its values after its name
#   file: runs_report.py
#   find:     return re.fullmatch(".*".join(parts) + r"( \(.*\))?", name) is not None
#   with:     return re.fullmatch(".*".join(parts), name) is not None
#
# @vacuity 🔴 a declared name is text, never a pattern: `(staged ...)` is no regex group
#   file: runs_report.py
#   find:     parts = [re.escape(p) for p in EXPRESSION.split(declared)]
#   with:     parts = EXPRESSION.split(declared)
#
# @vacuity 🔴 the SHORTEST of every job that could carry the name, or a timeout is missed
#   file: runs_report.py
#   find:     return min((m for d, m in clocks.items() if _can_show(d, name or "")),
#   with:     return max((m for d, m in clocks.items() if _can_show(d, name or "")),
#
# @vacuity 🔴 a name no job could carry takes the shortest clock, erring toward a report
#   file: runs_report.py
#   find:                default=_shortest(clocks))
#   with:                default=DEFAULT_CLOCK)
#
# @vacuity 🔴 a job is filed under the name it lists as, never its id
#   file: runs_report.py
#   find:             key = shown.get(job) or job
#   with:             key = job
#
# @vacuity 🔴 two jobs declaring one name keep the shorter clock
#   file: runs_report.py
#   find:             mine[key] = min(mins, mine.get(key, mins))
#   with:             mine[key] = mins
#
# @vacuity 🔴 wfparse reads a job's own `name:`
#   file: wfparse.py
#   find:             if jb.start <= lineno < jb.end and indent == 4 and key == "name":
#   with:             if jb.start <= lineno < jb.end and indent == 99 and key == "name":
#
# @vacuity 🔴 ...and never a step's
#   file: wfparse.py
#   find:             if jb.start <= lineno < jb.end and indent == 4 and key == "name":
#   with:             if jb.start <= lineno < jb.end and indent >= 4 and key == "name":
#
# @vacuity 🔴 a comment after a name is not the name, or the job's own clock is lost
#   file: wfparse.py
#   find: _JOB_NAME = re.compile(r'''^("[^"]*"|'[^']*'|.*?)(?:\s+#.*)?$''')
#   with: _JOB_NAME = re.compile(r'''^("[^"]*"|'[^']*'|.*?)$''')
#
# @vacuity 🔴 ...and neither are the quotes around it
#   file: wfparse.py
#   find:                 out[jb.name] = _JOB_NAME.match(val).group(1).strip("\"'") or None
#   with:                 out[jb.name] = _JOB_NAME.match(val).group(1) or None
#
# @vacuity ⛔ collect() never asks for an annotation: `watch` holds no checks: read
#   file: runs_report.py
#   find:         got = fetch_json("actions/runs/%s/jobs?per_page=100" % run_id) or {}
#   with:         fetch_json("check-runs/1/annotations"); got = fetch_json("actions/runs/%s/jobs?per_page=100" % run_id) or {}
#
# @vacuity the status file asks the jobs through the fetcher it was given
#   file: runs_report.py
#   find:                                   window_h=window_h, raw=True, fetch_json=fetch_json)
#   with:                                   window_h=window_h, raw=True)
#
# @vacuity 🔴 a timed-out run names its cancelled step, or runs.json says nothing
#   file: runs_report.py
#   find:                         CLOCK_STOPPED if e["conclusion"] == "timed_out" else FAILED)))
#   with:                         FAILED)))
#
# @vacuity 🔴 ...but a failed run's cancelled siblings add no noise
#   file: runs_report.py
#   find:                         CLOCK_STOPPED if e["conclusion"] == "timed_out" else FAILED)))
#   with:                         CLOCK_STOPPED)))
#
# @vacuity a stuck run's job is listed too, though it has no conclusion
#   file: runs_report.py
#   find: CLOCK_STOPPED = FAILED | {"cancelled", None}
#   with: CLOCK_STOPPED = FAILED | {"cancelled"}
#
# @vacuity ...and says so in words
#   file: runs_report.py
#   find:                          % (j.get("conclusion") or "never finished"))
#   with:                          % j.get("conclusion"))
"""
import atexit
import contextlib
import copy
import datetime
import io
import itertools
import json
import os
import shutil
import sys
import tempfile

from tcheck import ck, eq, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import runs_report as R  # noqa: E402
import wfparse  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime.now(UTC).replace(microsecond=0)
_ids = itertools.count(1000)
TREE = tempfile.mkdtemp()
_HOME = os.getcwd()


def _clean():
    os.chdir(_HOME)
    shutil.rmtree(TREE, ignore_errors=True)


atexit.register(_clean)


WF_DIR = os.path.join(TREE, ".github", "workflows")


def plant(name, names=None, **jobs):
    """A workflow file: {job id: its timeout-minutes, or None for no line}.
    `names`: {job id: its `name:` value, as written}. ⚠️ Every step has a `name:`
    too, so a parser that reads one as the job's fails on every plant."""
    lines = ["name: %s" % name, "on: workflow_dispatch", "jobs:"]
    for job, mins in jobs.items():
        lines.append("  %s:" % job)
        if job in (names or {}):
            lines.append("    name: %s" % names[job])
        lines.append("    runs-on: ubuntu-24.04")
        if mins is not None:
            lines.append("    timeout-minutes: %d" % mins)
        lines += ["    steps:", "      - name: say hi", "        run: echo hi"]
    os.makedirs(WF_DIR, exist_ok=True)
    with open(os.path.join(WF_DIR, name + ".yml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ⚠️ pr-tests' own `name:` lines, word for word: GitHub lists these jobs as
#    `tests · sweep 2/4` and `render (ubuntu-26.04)`, and neither is an id.
TESTS = ("tests${{ matrix.os != 'ubuntu-24.04' && format(' ({0})', matrix.os) || '' }}"
         "${{ matrix.shard != 'rest' && format(' · sweep {0}', matrix.shard) || '' }}")
RENDER = "render${{ matrix.os != 'ubuntu-24.04' && format(' ({0})', matrix.os) || '' }}"

plant("nightly", watch=120)                     # the sweep's shape
plant("ci", names={"tests": TESTS, "render": RENDER},   # pr-tests' shape: shortest 25
      tests=120, sweep=120, render=25)
plant("pair", quick=10, slow=15)                # budget's shape: two clocks
plant("bare", work=None)                        # no timeout-minutes at all


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def run(wf, conclusion, minutes, hours_ago=3, **kw):
    """A REST workflow-run object in the shape /actions/runs returns."""
    rid, start = next(_ids), NOW - datetime.timedelta(hours=hours_ago)
    return dict({"id": rid, "run_number": rid, "run_attempt": 1, "event": "schedule",
                 "status": "completed", "conclusion": conclusion,
                 "path": ".github/workflows/%s.yml" % wf,
                 "name": wf, "display_title": wf, "html_url": "u%d" % rid,
                 "created_at": iso(start), "run_started_at": iso(start),
                 "updated_at": iso(start + datetime.timedelta(minutes=minutes))}, **kw)


def job(name, conclusion, minutes, steps=(), check=1, **kw):
    """A REST job object in the shape /actions/runs/<id>/jobs returns."""
    start = NOW - datetime.timedelta(hours=3)
    return dict({"id": check, "name": name, "conclusion": conclusion, "steps": list(steps),
                 "check_run_url": "https://api.github.com/repos/o/r/check-runs/%d" % check,
                 "started_at": iso(start),
                 "completed_at": iso(start + datetime.timedelta(minutes=minutes))}, **kw)


class Api:
    """The fake GitHub. ⛔ It refuses annotations as the `watch` token may, and
    remembers being asked, because `hit_its_clock` turns any refusal into a report."""

    def __init__(self, jobs=None, notes=None, holds_checks=False):
        self.jobs, self.notes, self.holds_checks = jobs or {}, notes or {}, holds_checks
        self.calls, self.asked_checks = [], []

    def __call__(self, path):
        self.calls.append(path)
        if path.startswith("check-runs/"):
            self.asked_checks.append(path)
            if not self.holds_checks:
                raise RuntimeError("gh api %s: HTTP 403 not accessible by integration" % path)
            return self.notes.get(path) or []
        rid = int(path.split("/")[2])
        v = self.jobs.get(rid, [])
        if isinstance(v, Exception):
            raise v
        return {"jobs": v}


def real_api_is_off(path):
    raise RuntimeError("a test reached the real API with %s" % path)


# ⛔ A mutation that loses the injected fetcher reaches this, never the network.
R._gh_json = real_api_is_off
EVERY_API = []


def collect(rows, jobs=None, raw=False):
    """The real collect() over `rows` -> (its rows, the API it used)."""
    api = Api(jobs)
    EVERY_API.append(api)
    got = R.collect(lambda _page: copy.deepcopy(rows), now=NOW, root=TREE, raw=raw,
                    fetch_json=api)[0]
    return got, api


def word(row, jobs=None):
    """-> (the conclusion collect() leaves on one row, API calls it took)."""
    got, api = collect([row], jobs)
    return got[0]["conclusion"], len(api.calls)


def analyse(rows):
    return R.analyse(rows, NOW, root=TREE)


NAMES = R.workflow_names(TREE)
STEP_KILLED = {"name": "Does every guard actually bite?", "conclusion": "cancelled"}
STEP_AFTER = {"name": "Tell Sam", "conclusion": "success"}
EXCEEDED = "The job has exceeded the maximum execution time of 2h0m0s"

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 A CLOCK KILL REACHES BOTH READERS (THE NIGHTLY OF 41313167332)")
# ══════════════════════════════════════════════════════════════════════
# `cancelled` at run, job and step level; job 120.2 minutes against a clock of 120.
_kill = run("nightly", "cancelled", 120.4)
_jobs = {_kill["id"]: [job("watch", "cancelled", 120.2, [STEP_KILLED, STEP_AFTER], 777)]}
_norm, _api = collect([_kill], _jobs)
eq(_norm[0]["conclusion"], "timed_out", "🔴 the row analyse() reads says timed_out")
eq(_api.calls, ["actions/runs/%d/jobs?per_page=100" % _kill["id"]],
   "one call decides it: the run's jobs, once")
_broken = analyse(_norm)[0]
eq([b["name"] for b in _broken], ["nightly"], "🔴 analyse() lists the workflow as broken")
eq(_broken[0]["fails_24h"], 1, "...and counts the failure")
_raw, _ = collect([_kill], _jobs, raw=True)
eq(_raw[0]["conclusion"], "timed_out", "🔴 the raw row status_doc() reads says timed_out too")
_doc_api = Api(_jobs, {"check-runs/777/annotations": [
    {"annotation_level": "failure", "message": EXCEEDED},
    {"annotation_level": "failure", "message": "The operation was canceled."}]},
    holds_checks=True)
_doc = R.status_doc(_raw, NOW, NAMES, {}, _doc_api)
eq(_doc["n_failed"], 1, "🔴 runs.json counts it failed (status.py's Failed runs reads this)")
eq((_doc["by_workflow"]["nightly"]["failed"], _doc["by_workflow"]["nightly"]["cancelled"]),
   (1, 0), "...by workflow, and no longer as cancelled")

# flapping: the latest green, three clock kills in the window behind it
_flap = [run("nightly", "success", 90, hours_ago=2)]
_fj = {}
for _h in (5, 7, 9):
    _flap.append(run("nightly", "cancelled", 121, hours_ago=_h))
    _fj[_flap[-1]["id"]] = [job("watch", "cancelled", 120.5)]
_fg, _ = collect(_flap, _fj)
_a = analyse(_fg)
eq(([b["name"] for b in _a[0]], [f["fails_24h"] for f in _a[1]]), ([], [3]),
   "🔴 a green night after three timeouts is flapping, not silence")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 runs.json NAMES WHAT STOPPED, AND ONLY THERE ARE ANNOTATIONS READ")
# ══════════════════════════════════════════════════════════════════════
_row = _doc["runs"][0]
eq(_row.get("failing_steps"), ["Does every guard actually bite?"],
   "🔴 the step the clock killed is named, and the step that ran after it is not")
ck(EXCEEDED in (_row.get("annotations") or []), "🔴 ...with GitHub's sentence beside it",
   str(_row.get("annotations")))

_failed = run("ci", "failure", 30)
_sib = {_failed["id"]: [
    job("tests", "failure", 30, [{"name": "Fail", "conclusion": "failure"},
                                 {"name": "Later", "conclusion": "cancelled"}], 1),
    job("render", "cancelled", 30, [{"name": "Draw", "conclusion": "cancelled"}], 2)]}
_sapi = Api(_sib, holds_checks=True)
_sd = R.status_doc([_failed], NOW, NAMES, {}, _sapi)
eq(_sd["runs"][0].get("failing_steps"), ["tests: Fail"],
   "🔴 a FAILED run's cancelled siblings and steps add no noise")
eq(_sapi.asked_checks, ["check-runs/1/annotations"], "...and cost no annotation call")

_stuck = dict(run("nightly", "timed_out", 1470))
_stj = {_stuck["id"]: [job("watch", None, 0, completed_at=None)]}
_std = R.status_doc([_stuck], NOW, NAMES, {}, Api(_stj, holds_checks=True))
eq(_std["runs"][0].get("failing_steps"), ["(the job never finished with no failed step)"],
   "a stuck run says its job never finished, in words")

_again = Api(_jobs, holds_checks=True)
R.status_doc(_raw, NOW, NAMES,
             {(r["run_id"], r["attempt"], r["conclusion"]): r for r in _doc["runs"]}, _again)
eq(_again.calls, [], "the next hour reuses a timed-out run's detail (0 API calls)")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 A CONCURRENCY CANCEL STAYS CANCELLED: THE JOB'S OWN CLOCK DECIDES")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ THE REAL 40472931447: past the workflow's shortest clock (25) by a whisker,
#    its job cancelled at 25.3 minutes under a clock of 120. Elapsed time against
#    the shortest clock calls this a timeout. 3 of 20 candidates since 10-16.
_con = run("ci", "cancelled", 25.6)
_cj = {_con["id"]: [job("tests · sweep 2/4", "cancelled", 25.3)]}
eq(word(_con, _cj), ("cancelled", 1), "🔴 25.3 of its own 120: stays cancelled, after one call")
_cn, _ = collect([_con], _cj)
eq(analyse(_cn)[0], [], "...and analyse() does not call it broken")
_cr, _ = collect([_con], _cj, raw=True)
_cdoc = R.status_doc(_cr, NOW, NAMES, {}, Api(holds_checks=True))
eq((_cdoc["n_failed"], _cdoc["by_workflow"]["ci"]["cancelled"]), (0, 1),
   "...and runs.json counts it cancelled")

# the queue and updated_at overshoot both inflate the RUN's time, never the job's
_over = run("nightly", "cancelled", 132.7)
eq(word(_over, {_over["id"]: [job("watch", "cancelled", 95.0)]}), ("cancelled", 1),
   "🔴 a run that overshoots its clock (39778911309's shape) with a job under it stays cancelled")
_two = run("ci", "cancelled", 40)
eq(word(_two, {_two["id"]: [job("render (ubuntu-26.04)", "cancelled", 20),
                            job("tests", "cancelled", 39)]}), ("cancelled", 1),
   "every job under its own clock: stays cancelled")
_queued = run("nightly", "cancelled", 500)
eq(word(_queued, {_queued["id"]: []}), ("cancelled", 1),
   "cancelled in the queue, no job ever ran: no clock ran either")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 A RUN THAT COULD NOT BE A TIMEOUT COSTS NO API CALL")
# ══════════════════════════════════════════════════════════════════════
eq(word(run("nightly", "cancelled", 5)), ("cancelled", 0), "🔴 cancelled at 5 minutes: no call")
eq(word(run("nightly", "cancelled", 119.9)), ("cancelled", 0), "...just under the clock: no call")
ck(word(run("nightly", "cancelled", 120))[1] == 1, "...AT the clock: it is asked about")
eq(word(run("nightly", "success", 121)), ("success", 0), "🔴 a long green run: untouched, no call")
eq(word(run("nightly", "failure", 121)), ("failure", 0), "a long red run: untouched, no call")
eq(word(run("nightly", None, 121)), (None, 0), "a run still in progress: untouched, no call")
eq(word(run("nightly", "cancelled", 9000, path="dynamic/pages/pages-build-deployment",
            name="pages build and deployment")), ("cancelled", 0),
   "🔴 Pages has no clock: never judged, whatever it took")
_many = [run("nightly", "cancelled", 3) for _i in range(40)]
ck(len(collect(_many)[1].calls) == 0, "a day of ordinary cancels costs nothing")
_nullrow, _ = collect([None, run("nightly", "success", 1)])
eq(len(_nullrow), 2, "a null row is still carried past, as normalise() always has")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE SHORTEST CLOCK FINDS CANDIDATES, THE JOB'S NAME FINDS ITS CLOCK")
# ══════════════════════════════════════════════════════════════════════
# budget's 40114244630: job `watch` at 14.0 under a clock of 10, its sibling's is 15.
_short = run("pair", "cancelled", 14.2)
eq(word(_short, {_short["id"]: [job("quick", "cancelled", 14.0)]}), ("timed_out", 1),
   "🔴 a run under the LONGEST clock is still a candidate: a job past the shortest was killed")
_slow = run("pair", "cancelled", 14.2)
eq(word(_slow, {_slow["id"]: [job("slow", "cancelled", 14.0)]}), ("cancelled", 1),
   "🔴 ...and the same 14 minutes under that job's own 15 is no timeout")

for _name, _mins, _want, _why in (
        ("tests · sweep 2/4", 119.9, "cancelled", "a suffixed name reads job `tests`, 120"),
        ("tests · sweep 2/4", 120.1, "timed_out", "...and at its own clock it is a timeout"),
        ("render (ubuntu-26.04)", 24.9, "cancelled", "a matrix name reads job `render`, 25"),
        ("render (ubuntu-26.04)", 25.1, "timed_out", "...and at its own clock it is a timeout"),
        ("sweep (2)", 119.9, "cancelled", "a matrix of a future job reads it the same way"),
        ("sweep (2)", 120.1, "timed_out", "...and at its own clock it is a timeout"),
        ("mystery", 24.9, "cancelled", "🔴 a name no job declares takes the shortest clock"),
        ("mystery", 25.1, "timed_out", "🔴 ...and errs toward a report, not toward 360"),
        (None, 25.1, "timed_out", "a job with no name is the same")):
    _r = run("ci", "cancelled", 200)
    eq(word(_r, {_r["id"]: [job(_name, "cancelled", _mins)]})[0], _want, _why)

_b1, _b2 = run("bare", "cancelled", 361), run("bare", "cancelled", 361)
eq(word(_b1, {_b1["id"]: [job("work", "cancelled", 350)]})[0], "cancelled",
   "🔴 no timeout-minutes means GitHub's own 360: a job at 350 was not stopped by it")
eq(word(_b2, {_b2["id"]: [job("work", "cancelled", 361)]})[0], "timed_out",
   "...and at 361 it was")
eq(word(run("bare", "cancelled", 340)), ("cancelled", 0), "...nor is a run under 360 asked about")

_mix = run("ci", "cancelled", 40)
eq(word(_mix, {_mix["id"]: [job("mystery", "success", 30), job("tests", "cancelled", 5)]})[0],
   "cancelled", "only a CANCELLED job can be a clock kill: a long green sibling proves nothing")
eq(R.job_clocks(TREE)[".github/workflows/ci.yml"], {TESTS: 120, "sweep": 120, RENDER: 25},
   "the clocks are read from the workflow file, every job, under the name it lists as")
plant("later", brand_new=7)
_new = run("later", "cancelled", 8)
eq(word(_new, {_new["id"]: [job("brand_new", "cancelled", 7.5)]})[0], "timed_out",
   "🔴 a workflow added today is covered today: nothing names it")

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 WHAT CANNOT BE READ IS REPORTED, NEVER READ AS FINE")
# ══════════════════════════════════════════════════════════════════════
_err = run("nightly", "cancelled", 121)
eq(word(_err, {_err["id"]: RuntimeError("gh api: HTTP 502")}), ("timed_out", 1),
   "🔴 the jobs call fails: reported")
# the real stuck run 36791843765: 1,470 minutes, job conclusion null, 0 steps
_s1, _s2 = run("nightly", "cancelled", 1470), run("nightly", "cancelled", 1470)
eq(word(_s1, {_s1["id"]: [job("watch", None, 1470)]})[0], "timed_out",
   "🔴 a job with no conclusion: reported")
eq(word(_s2, {_s2["id"]: [job("watch", "cancelled", 0, completed_at=None)]})[0], "timed_out",
   "🔴 a job with no end time: reported")
_notime = run("nightly", "cancelled", 1, updated_at=None)
eq(word(_notime, {_notime["id"]: [job("watch", "cancelled", 121)]}), ("timed_out", 1),
   "a run with no time on it is asked about, and its jobs decide")
_nostart = run("nightly", "cancelled", 121)
eq(word(_nostart, {_nostart["id"]: [job("watch", "cancelled", 121, started_at=None)]})[0],
   "cancelled", "a job that never started ran no clock")

# ══════════════════════════════════════════════════════════════════════
section("7. ⛔ collect() NEVER READS AN ANNOTATION: `watch` HOLDS NO checks: read")
# ══════════════════════════════════════════════════════════════════════
ck(len(EVERY_API) > 30, "(control: every collect() above went through this fake)",
   str(len(EVERY_API)))
ck(sum(len(a.calls) for a in EVERY_API) > 20, "(control: and they did call it)")
eq([p for a in EVERY_API for p in a.asked_checks], [],
   "🔴 no collect() above asked a check run for anything")

# ══════════════════════════════════════════════════════════════════════
section("8. BOTH WAYS IN: `--collect` (watch) AND `--status-file` (publish)")
# ══════════════════════════════════════════════════════════════════════
_kw = run("nightly", "cancelled", 121)
_cc = run("ci", "cancelled", 26)
_both = {_kw["id"]: [job("watch", "cancelled", 120.3, [STEP_KILLED], 5)],
         _cc["id"]: [job("tests", "cancelled", 26)]}


def by_id(rows, key):
    return {r[key]: r["conclusion"] for r in rows}


_page = R.gh_page
os.chdir(TREE)
try:
    # the watch job's own call: no fetcher named, its token refuses check runs
    R.gh_page = lambda _n: copy.deepcopy([_kw, _cc])
    R._gh_json = _wa = Api(_both)
    _out = io.StringIO()
    with contextlib.redirect_stdout(_out):
        _rc = R.main(["--collect"])
    eq(_rc, R.EXIT_OK, "`--collect` exits 0")
    eq(sorted(r["conclusion"] for r in json.loads(_out.getvalue())), ["cancelled", "timed_out"],
       "🔴 the watch job's list carries the mark, with no fetcher passed in")
    eq(_wa.asked_checks, [], "⛔ ...and asked for no annotation")

    # the publish job's own call: its token reads them
    _pth = os.path.join(TREE, "out", "runs.json")
    R._gh_json = _pa = Api(_both, {"check-runs/5/annotations": [
        {"annotation_level": "failure", "message": EXCEEDED}]}, holds_checks=True)
    with contextlib.redirect_stdout(io.StringIO()):
        eq(R.main(["--status-file", _pth]), R.EXIT_OK, "`--status-file` exits 0")
    _sf = json.load(open(_pth, encoding="utf-8"))
    eq(by_id(_sf["runs"], "run_id"), {_kw["id"]: "timed_out", _cc["id"]: "cancelled"},
       "🔴 the publish job's file agrees with the watch job's list, run by run")
    ck(EXCEEDED in {r["run_id"]: r for r in _sf["runs"]}[_kw["id"]].get("annotations", []),
       "...and carries the sentence", str(_sf["runs"]))
finally:
    R.gh_page, R._gh_json = _page, real_api_is_off
    os.chdir(_HOME)

_given = Api({_cc["id"]: [job("tests", "cancelled", 26)]})
_gdoc = R.write_status(os.path.join(TREE, "out", "given.json"),
                       fetch_page=lambda _n: copy.deepcopy([_cc]), fetch_json=_given,
                       now=NOW, root=TREE)
eq(by_id(_gdoc["runs"], "run_id"), {_cc["id"]: "cancelled"},
   "write_status asks the jobs through the fetcher it was given")
ck(any("/jobs" in p for p in _given.calls), "...which was called", str(_given.calls))

# ══════════════════════════════════════════════════════════════════════
section("9. 🔴 A JOB'S CLOCK IS FOUND BY THE NAME IT LISTS UNDER, NEVER BY ITS ID")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ pr-tests' `staged` lists as `tests (staged uploads applied)` and `offseason`
#    as `tests (off-season, no games)`. Read by the name's first word, both took
#    job `tests`'s clock, which was right only while all three happened to be 120.
plant("shared", names={"tests": TESTS, "staged": "tests (staged uploads applied)"},
      tests=120, staged=30)
plant("renamed", names={"long": "render everything"}, render=25, long=120)
plant("twin", names={"slow": "quick (slow pass)"}, quick=10, slow=120)
plant("same", names={"one": "one name", "two": "one name"}, one=10, two=120)
plant("open", names={"any": "${{ matrix.label }}"}, any=30, tests=120)
plant("written", names={"dq": '"tests (double)"  # why', "sq": "'tests (single)'",
                        "pl": "tests (plain)  # why"}, tests=120, dq=30, sq=30, pl=30)

for _wf, _name, _mins, _want, _why in (
        ("shared", "tests (staged uploads applied)", 30.5, "timed_out",
         "🔴 a job named after another job's id still reads its OWN clock: no timeout missed"),
        ("shared", "tests (staged uploads applied)", 29.5, "cancelled",
         "...and under that clock it was no timeout"),
        ("shared", "tests · sweep 2/4", 31, "cancelled",
         "🔴 a sibling's shorter clock never touches a name it could not carry"),
        ("shared", "tests", 31, "cancelled", "...the plain name either"),
        ("shared", "tests · sweep 2/4", 120.5, "timed_out", "...and its own clock still decides"),
        ("renamed", "render everything", 30, "cancelled",
         "🔴 a word shared with a shorter job is no timeout: that job could not carry the name"),
        ("renamed", "render everything", 120.5, "timed_out", "...and its own clock decides"),
        ("renamed", "render (ubuntu-26.04)", 25.5, "timed_out", "...and the other job keeps its own"),
        ("twin", "quick (slow pass)", 11, "timed_out",
         "🔴 two jobs that really could carry one name: the shorter clock, erring toward a report"),
        ("same", "one name", 11, "timed_out", "🔴 two jobs declaring one name: the shorter clock"),
        ("open", "tests (x)", 31, "timed_out",
         "🔴 a `name:` that is all expression could be anything, so its clock counts everywhere"),
        ("open", "tests (x)", 29, "cancelled", "...and under every clock is no timeout"),
        ("written", "tests (double)", 31, "timed_out", "🔴 a quoted name with a comment on its line"),
        ("written", "tests (single)", 31, "timed_out", "...a single-quoted one"),
        ("written", "tests (plain)", 31, "timed_out", "...and a bare one with a comment")):
    _r = run(_wf, "cancelled", _mins + 0.5)
    eq(word(_r, {_r["id"]: [job(_name, "cancelled", _mins)]})[0], _want,
       "%s (%s at %s)" % (_why, _name, _mins))

eq(R.job_clocks(TREE)[".github/workflows/same.yml"], {"one name": 10},
   "two jobs declaring one name are one clock, the shorter")
eq(wfparse.job_names(os.path.join(WF_DIR, "written.yml")),
   {"tests": None, "dq": "tests (double)", "sq": "tests (single)", "pl": "tests (plain)"},
   "🔴 job_names: a job's own `name:` without quotes or comment, None when it sets none")
eq(wfparse.job_names(os.path.join(WF_DIR, "nightly.yml")), {"watch": None},
   "🔴 ...and a step's `name:` is never the job's")
