#!/usr/bin/env python3
r"""🔴🔴 A JOB OR TEST FILE APPROACHING ITS OWN CLOCK IS SEEN BEFORE THE CLOCK KILLS IT.

`[2026-11-13]` pr-tests' sweep parts reached 4,249s of test_vacuity.py's 5,400s clock
(79%) on 11-12, growing 500-800 s a week. Nothing said so: the sweep's own half-clock
`::warning::` reached only the PR page, and runs_report judged a clock only after it had
killed a run. The hourly runs watcher now records every finished job's time beside its
own clock in runs.json (`runs_report.read_clocks` -> `clock_runs`), `clock_report` judges
it, the watchdog reports DEGRADED at 75%+ (`check_job_clocks`) and the Monday email lists
it (`status.clock_lines`).

⛔ A TEST ASKS THE CODE, NEVER PRODUCTION: every run, job and runs.json below is planted,
and the clock is pinned. Nothing here reads data/latest/runs.json or the API.

# @vacuity 🔴🔴 the bar is 75% of the clock
#   file: runs_report.py
#   find: CLOCK_WARN = 0.75
#   with: CLOCK_WARN = 0.95
#
# @vacuity 🔴 75% itself is at the bar, not under it
#   file: runs_report.py
#   find:             "over": [x for x in rows if x["pct"] >= warn], "unread": unread, "n": n}
#   with:             "over": [x for x in rows if x["pct"] > warn], "unread": unread, "n": n}
#
# @vacuity 🔴 a job is held to ITS OWN clock, never GitHub's 360
#   file: runs_report.py
#   find:         lim = _own_clock(name, mine) * 60
#   with:         lim = DEFAULT_CLOCK * 60
#
# @vacuity 🔴🔴 a sweep part's Tests step is held to test_vacuity.py's own clock
#   file: runs_report.py
#   find:         if path.endswith("/pr-tests.yml") and SWEEP_JOB.search(name):
#   with:         if False:
#
# @vacuity 🔴 that clock is READ from the step, never assumed
#   file: runs_report.py
#   find:     alone = re.search(r'^\s*sweep\)\s*\[\s*"\$1"\s*=\s*(\S+)\s*\]', body or "", re.M)
#   with:     alone = re.search(r'^\s*sweepx\)\s*\[\s*"\$1"\s*=\s*(\S+)\s*\]', body or "", re.M)
#
# @vacuity 💰 a finished run is read ONCE, never every hour
#   file: runs_report.py
#   find:             and (r.get("path") or "") in clocks and (r.get("id"), r.get("run_attempt")) not in kept]
#   with:             and (r.get("path") or "") in clocks]
#
# @vacuity 💰 and at most CLOCK_READS_PER_WRITE an hour
#   file: runs_report.py
#   find:     for r in todo[:cap]:
#   with:     for r in todo:
#
# @vacuity ⚠️ only the last 7 days are judged
#   file: runs_report.py
#   find:         if at is None or at < floor:
#   with:         if at is None:
#
# @vacuity ⚠️ a job whose clock cannot be read is "could not look", never skipped
#   file: runs_report.py
#   find:         if lim <= 0:
#   with:         if False:
#
# @vacuity ⚠️ a job that started and never finished is "could not look"
#   file: runs_report.py
#   find:             rec["unread"].append("%s: started and never finished" % name)
#   with:             pass
#
# @vacuity ⚠️ clock_runs is one run per line, like runs
#   file: runs_report.py
#   find: LINE_LISTS = ("clock_runs", "runs")
#   with: LINE_LISTS = ("runs",)
#
# @vacuity ⛔ a test that injects a run list never reaches the API for clocks
#   file: runs_report.py
#   find:     fetch_jobs = fetch_jobs or (None if fetch_page else _gh_json)
#   with:     fetch_jobs = fetch_jobs or _gh_json
#
# @vacuity 🔴🔴 the watchdog reports a job at 75%+ of its clock
#   file: watchdog.py
#   find:     for f, rows in sorted(by.items()):
#   with:     for f, rows in []:
#
# @vacuity 🔴 ...and a job time it could not read
#   file: watchdog.py
#   find:     if r["unread"]:
#   with:     if False:
#
# @vacuity 🔴 ...and the check is registered
#   file: watchdog.py
#   find:           check_job_clocks,
#   with:           # check_job_clocks,
#
# @vacuity 🔴 the Monday email lists the clocks
#   file: status.py
#   find:     L += ["", "## Job clocks (last %d days)" % R.CLOCK_DAYS] + clock_lines(runs, stale, now)
#   with:     pass
"""
import copy
import datetime
import json
import os
import shutil
import sys
import tempfile

from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import runs_report as R  # noqa: E402
import status as S  # noqa: E402
import watchdog as W  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 11, 13, 5, 0, tzinfo=UTC)
TREES = []


def T(minutes_ago):
    return (NOW - datetime.timedelta(minutes=minutes_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def real_api_is_off(path):
    raise RuntimeError("a test reached the real API with %s" % path)


# ⛔ A mutation that loses the injected fetcher reaches this, never the network.
R._gh_json = real_api_is_off
PR = ".github/workflows/pr-tests.yml"
SWEEP = R.sweep_clock(ROOT)


def job(name, secs, ended_ago=10, steps=None, conclusion="success", started=True, ended=True):
    """A jobs-API job that ran `secs` seconds and ended `ended_ago` minutes before NOW."""
    end = NOW - datetime.timedelta(minutes=ended_ago)
    beg = end - datetime.timedelta(seconds=secs)
    return {"name": name, "conclusion": conclusion if ended else None,
            "started_at": beg.strftime("%Y-%m-%dT%H:%M:%SZ") if started else None,
            "completed_at": end.strftime("%Y-%m-%dT%H:%M:%SZ") if ended else None,
            "steps": steps or []}


def step(name, secs, ended_ago=10):
    end = NOW - datetime.timedelta(minutes=ended_ago)
    beg = end - datetime.timedelta(seconds=secs)
    return {"name": name, "conclusion": "success", "started_at": beg.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "completed_at": end.strftime("%Y-%m-%dT%H:%M:%SZ")}


def run(i, path=PR, ended_ago=10, status="completed", attempt=1, name="pr-tests"):
    return {"id": i, "run_number": i % 1000, "run_attempt": attempt, "path": path, "name": name,
            "display_title": name, "status": status, "conclusion": "success" if status == "completed" else None,
            "event": "pull_request", "created_at": T(ended_ago + 200), "run_started_at": T(ended_ago + 200),
            "updated_at": T(ended_ago), "html_url": "https://example.invalid/%d" % i}


class Api:
    """The jobs API, planted: run id -> its jobs. Every path asked is logged."""

    def __init__(self, jobs, broken=()):
        self.jobs, self.broken, self.calls = jobs, set(broken), []

    def __call__(self, path):
        self.calls.append(path)
        rid = int(path.split("/")[2])
        if rid in self.broken:
            raise RuntimeError("gh api %s: HTTP 502" % path)
        return {"jobs": copy.deepcopy(self.jobs.get(rid, []))}


MINE = R.job_clocks(ROOT)[PR]
NAMES = R.workflow_names(ROOT)

# ════════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 EACH JOB BESIDE ITS OWN CLOCK, AND A SWEEP PART'S TESTS STEP BESIDE test_vacuity.py's")
# ════════════════════════════════════════════════════════════════════════
eq(SWEEP, ("Tests", "test_vacuity.py", 5400),
   "🔴 pr-tests.yml's Tests step says a sweep part runs test_vacuity.py ALONE, with a 5400s clock")
_part = job("tests · sweep 1/4", 4400, steps=[step("Set up job", 5), step("Tests", 4320)])
_rec = R.clock_record(run(1), [
    _part,
    job("render (ubuntu-26.04)", 600),
    job("tests (staged uploads applied)", 0, started=False),           # queued, cancelled: never ran
    job("tests (a champion named)", 0, conclusion="skipped"),
    job("tests (off-season, no games)", 900, ended=False),             # started, never finished
    job("tests (ubuntu-26.04) · sweep 2/4", 3000, steps=[step("Set up job", 5)]),
], MINE, SWEEP, NAMES)
eq(sorted((j["job"], j.get("clock", "job"), j["secs"], j["limit"]) for j in _rec["jobs"]), sorted([
    ("tests · sweep 1/4", "job", 4400, 7200),
    ("tests · sweep 1/4", "file test_vacuity.py", 4320, 5400),
    ("render (ubuntu-26.04)", "job", 600, 1500),
    ("tests (ubuntu-26.04) · sweep 2/4", "job", 3000, 7200)]),
   "🔴🔴 each job is held to ITS OWN clock (120 / 25 minutes), and a sweep part's Tests step to 5400s")
eq(sorted(_rec.get("unread") or []), sorted([
    "tests (off-season, no games): started and never finished",
    "tests (ubuntu-26.04) · sweep 2/4: its Tests step has no time"]),
   "⚠️ a job that never finished, and a sweep part with no Tests time, are named as unread; a job "
   "that never ran (queued or skipped) had no clock running")
_unr = R.clock_record(run(2), [job("tests", 60)], {"tests": R.UNREADABLE_CLOCK}, SWEEP, NAMES)
eq((_unr["jobs"], _unr.get("unread")), ([], ["tests: its timeout-minutes cannot be read"]),
   "⚠️ a job whose clock cannot be read is \"could not look\", never skipped and never 360")
_gone = R.clock_record(run(3), [_part], MINE, None, NAMES)
eq(_gone.get("unread"), ["tests · sweep 1/4: pr-tests.yml no longer says which file a sweep part runs "
                          "alone, or that file's clock"],
   "⚠️ a sweep part whose file clock can no longer be read from pr-tests.yml says so")

# ── sweep_clock reads the step, and refuses when the step no longer says it ──
_d = tempfile.mkdtemp(prefix="jobclocks-")
TREES.append(_d)
os.makedirs(os.path.join(_d, ".github", "workflows"))
_src = open(os.path.join(ROOT, PR), encoding="utf-8").read()
for _what, _txt, _want in (
        ("the real step, its clock raised by hand", _src.replace("test_vacuity.py) echo 5400 ;;",
                                                                   "test_vacuity.py) echo 6000 ;;"),
         ("Tests", "test_vacuity.py", 6000)),
        ("a step whose sweep shard no longer names one file", _src.replace(
            'sweep) [ "$1" = test_vacuity.py ] ;;', "sweep) true ;;"), None)):
    open(os.path.join(_d, PR), "w", encoding="utf-8").write(_txt)
    ck("⚠️ the planted step really differs (%s)" % _what, _txt != _src)
    eq(R.sweep_clock(_d), _want, "🔴 sweep_clock reads %s" % _what)

# ════════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 THE JUDGE: 80% IS OVER, 75% IS AT THE BAR, 74% AND 50% ARE NOT, A WEEK IS THE WINDOW")
# ════════════════════════════════════════════════════════════════════════


def doc(*recs, errors=(), generated=10):
    return {"generated_at": T(generated), "runs": [], "window_hours": 48, "by_workflow": {},
            "clock_runs": list(recs), "clock_errors": list(errors)}


def rec(i, jobs, ended_ago=10, path=PR, workflow="pr-tests", unread=None):
    out = {"run_id": i, "attempt": 1, "run_number": i, "workflow": workflow, "file": path,
           "at": T(ended_ago), "jobs": jobs}
    if unread:
        out["unread"] = unread
    return out


_SW = lambda secs, part="1/4": {"job": "tests · sweep %s" % part, "clock": "file test_vacuity.py",
                                "secs": secs, "limit": 5400}
_r = R.clock_report(doc(rec(1, [_SW(4320)]), rec(2, [_SW(2700, "2/4")]), rec(3, [_SW(4050, "3/4")]),
                        rec(4, [_SW(3996, "4/4")]),
                        rec(5, [_SW(5000, "1/4")], ended_ago=8 * 24 * 60)), NOW)
eq([(x["job"], round(x["pct"], 2)) for x in _r["over"]],
   [("tests · sweep 1/4", 0.8), ("tests · sweep 3/4", 0.75)],
   "🔴🔴 80% and exactly 75% are over the bar; 74% and 50% are not; a 93% run 8 days ago is out of the week")
eq(_r["slowest"]["secs"], 4320, "   ...and the slowest of the week is the 80% part")
ck("🔴 the words say the job, the %, the clock and the run",
   R.clock_words(_r["slowest"]) == "pr-tests's tests · sweep 1/4 used 80% of test_vacuity.py's 5400s clock "
   "(4320s, run 1, " + T(10)[:16] + ")", R.clock_words(_r["slowest"]))
eq(R.clock_advice(PR, "tests · sweep 1/4", "file test_vacuity.py"),
   "add parts (pr-tests.yml's `shard:` matrix); do not raise the clock",
   "⛔ a sweep part is told to add parts, never to raise the clock")
eq(R.clock_advice(".github/workflows/vacuity.yml", "sweep (2)", "job"),
   "add parts (vacuity.yml's `part:` matrix, a Sam upload); do not raise the clock",
   "   ...and so is a nightly part")
eq(R.clock_advice(".github/workflows/collect.yml", "collect", "job"),
   "make it shorter or split it; do not raise the clock", "   ...and any other job is told to shorten")
_none = R.clock_report({"generated_at": T(10), "runs": []}, NOW)
eq((_none["looked"], _none["over"]), (False, []),
   "⚠️ a runs.json that carries no clocks is \"could not look\", never \"nothing near its clock\"")
_err = R.clock_report(doc(rec(1, [_SW(1000)], unread=["x: started and never finished"]),
                          errors=[{"run_id": 9, "file": PR, "why": "RuntimeError: HTTP 502"}]), NOW)
eq(len(_err["unread"]), 2, "⚠️ an unread job and a refused jobs call are both \"could not look\"")

# ════════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 THE WATCHDOG: DEGRADED AT 75%+, SILENT AT 50%, \"COULD NOT LOOK\" WHEN IT COULD NOT")
# ════════════════════════════════════════════════════════════════════════


def watch(d):
    """check_job_clocks over a planted runs.json (None: no file). -> (findings, note)."""
    t = tempfile.mkdtemp(prefix="jobclocks-watch-")
    TREES.append(t)
    if d is not None:
        os.makedirs(os.path.join(t, "data", "latest"))
        json.dump(d, open(os.path.join(t, "data", "latest", "runs.json"), "w", encoding="utf-8"))
    old, W.ROOT = W.ROOT, t
    try:
        rep = W.Report()
        W.check_job_clocks(rep, NOW)
        return rep.items, getattr(rep, "note_clocks", None)
    finally:
        W.ROOT = old


_f80, _n80 = watch(doc(rec(1, [_SW(4320), {"job": "render", "secs": 300, "limit": 1500}])))
eq([(i["key"], i["severity"], i["repair"]) for i in _f80], [("clock:pr-tests", "DEGRADED", None)],
   "🔴🔴 a sweep part at 80% of its clock is DEGRADED, with no repair")
ck("🔴 ...naming the job and the %%, and saying add parts, do not raise the clock",
   _f80 and "tests · sweep 1/4" in _f80[0]["what"] and "80%" in _f80[0]["what"]
   and "Add parts" in _f80[0]["why"] and "do not raise the clock" in _f80[0]["why"],
   _f80 and (_f80[0]["what"], _f80[0]["why"]))
_f50, _n50 = watch(doc(rec(1, [_SW(2700)])))
eq(_f50, [], "🔴 the same part at 50% is silent")
ck("   ...and health.json still carries the slowest, finding or not",
   (_n50 or {}).get("slowest", "").startswith("pr-tests's tests · sweep 1/4 used 50%"), _n50)
_fu, _ = watch(doc(rec(1, [_SW(1000)], unread=["tests (off-season, no games): started and never finished"])))
eq([(i["key"], i["severity"]) for i in _fu], [("clock:unread", "DEGRADED")],
   "🔴 a job time it could not read is DEGRADED: a job nobody measured could be at its clock")
_fn, _ = watch({"generated_at": T(10), "runs": []})
eq([i["key"] for i in _fn], ["clock:unread"], "⚠️ a run list with no clocks in it is \"could not look\" too")
_fs, _ns = watch(doc(rec(1, [_SW(5000)]), generated=6 * 60))
eq((_fs, (_ns or {}).get("could_not_look")), ([], "the run list is 6 hours old"),
   "⚠️ a STALE run list says nothing here (its own freshness row reports it) and the note says why")
_f0, _n0 = watch(None)
eq((_f0, (_n0 or {}).get("could_not_look")), ([], "there is no run list"),
   "⚠️ a tree with no run list is a clean tree here")
ck("🔴 the check is registered, so the real watchdog runs it", W.check_job_clocks in W.CHECKS)
_t = tempfile.mkdtemp(prefix="jobclocks-run-")
TREES.append(_t)
os.makedirs(os.path.join(_t, "data", "latest"))
json.dump(doc(rec(1, [_SW(4320)])), open(os.path.join(_t, "data", "latest", "runs.json"), "w"))
_oldroot, _oldchecks, W.ROOT, W.CHECKS = W.ROOT, W.CHECKS, _t, (W.check_job_clocks,)
try:
    _out = W.run(NOW)
finally:
    W.ROOT, W.CHECKS = _oldroot, _oldchecks
ck("   ...and health.json carries the reading (`job_clocks`) and the finding",
   (_out.get("job_clocks") or {}).get("jobs_measured") == 1 and _out["degraded"] == 1
   and _out["broken"] == 0 and not _out["repairs"], _out)

# ════════════════════════════════════════════════════════════════════════
section("4. 🔴 THE MONDAY EMAIL LISTS THEM")
# ════════════════════════════════════════════════════════════════════════
_lines = S.clock_lines(doc(rec(1, [_SW(4320)]), rec(2, [{"job": "render", "secs": 300, "limit": 1500}])),
                       None, NOW)
_W80 = "pr-tests's tests · sweep 1/4 used 80% of test_vacuity.py's 5400s clock (4320s, run 1, " + T(10)[:16] + ")"
eq(_lines, ["- The slowest: " + _W80 + ".",
            "- At 75% or more: " + _W80 + ". Add parts (pr-tests.yml's `shard:` matrix); do not raise the clock."],
   "🔴 the slowest, then each job at 75%+ with what to do")
eq(S.clock_lines(doc(rec(1, [_SW(2700)])), None, NOW)[1:], ["- None at 75% or more of its clock."],
   "   ...and a quiet week says so")
eq(S.clock_lines(None, "the run list is 5 hours old", NOW), ["- Can't say: the run list is 5 hours old."],
   "   ...and a stale run list gives no verdict")
_st = tempfile.mkdtemp(prefix="jobclocks-status-")
TREES.append(_st)
os.makedirs(os.path.join(_st, "data", "latest"))
json.dump(dict(doc(rec(1, [_SW(4320)])), generated_at=T(10)),
          open(os.path.join(_st, "data", "latest", "runs.json"), "w", encoding="utf-8"))
json.dump({"checked_at": T(20), "findings": []},
          open(os.path.join(_st, "data", "latest", "health.json"), "w", encoding="utf-8"))
_body = S.build(_st, NOW)[0]
ck("🔴 ...inside the weekly body, under its own heading",
   "## Job clocks (last 7 days)\n- The slowest: pr-tests's tests · sweep 1/4 used 80%" in _body,
   _body[_body.find("## Job clocks"):][:200])

# ════════════════════════════════════════════════════════════════════════
section("5. 💰 EACH FINISHED RUN IS READ ONCE, AT MOST 40 AN HOUR, AND A FAILED CALL IS RETRIED")
# ════════════════════════════════════════════════════════════════════════
_raw = [run(101), run(102), run(103, status="in_progress"),
        run(104, path="dynamic/pages/pages-build-deployment", name="pages build and deployment")]
_api = Api({101: [job("render", 300)], 102: [job("render", 600)]}, broken={102})
_recs, _errs = R.read_clocks(_raw, NOW, NAMES, [], _api, ROOT)
eq(sorted(_api.calls), ["actions/runs/101/jobs?per_page=100", "actions/runs/102/jobs?per_page=100"],
   "💰 one jobs call per finished run of a workflow with clocks; none for a run still going or for Pages")
eq(([r["run_id"] for r in _recs], [e["run_id"] for e in _errs]), ([101], [102]),
   "⚠️ a refused call is an error, not a record")
_api2 = Api({101: [job("render", 300)], 102: [job("render", 600)]})
_recs2, _errs2 = R.read_clocks(_raw, NOW, NAMES, _recs, _api2, ROOT)
eq((_api2.calls, sorted(r["run_id"] for r in _recs2), _errs2),
   (["actions/runs/102/jobs?per_page=100"], [101, 102], []),
   "💰 the next hour asks only for the run it could not read; the run already read costs nothing")
_many = [run(1000 + k, ended_ago=k) for k in range(R.CLOCK_READS_PER_WRITE + 5)]
_api3 = Api({})
_recs3, _ = R.read_clocks(_many, NOW, NAMES, [], _api3, ROOT)
eq((len(_api3.calls), _api3.calls[0]), (R.CLOCK_READS_PER_WRITE, "actions/runs/1000/jobs?per_page=100"),
   "💰 at most CLOCK_READS_PER_WRITE (%d) calls an hour, the newest runs first" % R.CLOCK_READS_PER_WRITE)
_old = [rec(7, [_SW(100)], ended_ago=8 * 24 * 60), rec(8, [_SW(100)], ended_ago=60)]
_recs4, _ = R.read_clocks([], NOW, NAMES, _old, Api({}), ROOT)
eq([r["run_id"] for r in _recs4], [8], "⚠️ a record older than 7 days is dropped")

# ════════════════════════════════════════════════════════════════════════
section("6. 🔴 THE FILE: WRITTEN BY write_status, ONE RUN PER LINE, AND NO TEST REACHES THE API")
# ════════════════════════════════════════════════════════════════════════
_w = tempfile.mkdtemp(prefix="jobclocks-file-")
TREES.append(_w)
_p = os.path.join(_w, "data", "latest", "runs.json")
_pages = lambda n: copy.deepcopy([run(201), run(202)]) if n == 1 else []
_wj = Api({201: [_part], 202: [job("render", 600)]})
_wd = R.write_status(_p, fetch_page=_pages, fetch_json=lambda p: {"jobs": []}, now=NOW, root=ROOT,
                     fetch_jobs=_wj)
_txt = open(_p, encoding="utf-8").read()
ck("🔴 the file is the document, and clock_runs is one run per line",
   json.loads(_txt) == _wd and len(_wd["clock_runs"]) == 2
   and len([ln for ln in _txt.splitlines() if ln.startswith('  {"run_id"')]) == 2, _txt[:400])
eq(R.clock_report(_wd, NOW)["slowest"]["secs"], 4320,
   "   ...and the judge reads the sweep part's 80% back out of it")
# ⚠️ the next write's list holds a run NOT read yet (203), so a write that went to the
#    API for it would show: `real_api_is_off` refuses, and the refusal is recorded
_pages2 = lambda n: copy.deepcopy([run(201), run(202), run(203)]) if n == 1 else []
try:
    _kept = R.write_status(_p, fetch_page=_pages2, fetch_json=lambda p: {"jobs": []}, now=NOW, root=ROOT)
    _reached = None
except RuntimeError as _e:
    _kept, _reached = None, str(_e)
ck("⛔ a test that injects its own run list and no jobs fetcher never reaches the API for clocks, "
   "and the records already in the file are kept",
   _reached is None and _kept and sorted(r["run_id"] for r in _kept["clock_runs"]) == [201, 202]
   and _kept["clock_errors"] == [],
   _reached or (_kept and ([r["run_id"] for r in _kept["clock_runs"]], _kept["clock_errors"])))

note("⛔ WHAT THIS DOES NOT SEE: a file in the `rest` shard against its own 600s clock, since that "
     "step runs every file but one and a per-file time is only in the job log. The slowest was "
     "172s on 2026-11-12 (29%).")

for _t in TREES:
    shutil.rmtree(_t, ignore_errors=True)
