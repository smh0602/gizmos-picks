#!/usr/bin/env python3
r"""🔴🔴 A JOB OR TEST FILE APPROACHING ITS OWN CLOCK IS SEEN BEFORE THE CLOCK KILLS IT.

`[2026-11-13]` pr-tests' sweep parts reached 4,249s of test_vacuity.py's 5,400s clock
(79%) on 11-12, growing 500-800 s a week. Nothing said so: the sweep's own half-clock
`::warning::` reached only the PR page, and runs_report judged a clock only after it had
killed a run. The hourly runs watcher now records every finished job's time beside its
own clock in runs.json (`runs_report.read_clocks` -> `clock_runs`), `clock_report` judges
it, the watchdog reports DEGRADED at 75%+ (`check_job_clocks`) and the Monday email lists
it (`status.clock_lines`).

`[2026-11-17, the review]` A job that HOLDS on purpose (collect's 320-minute hold inside a
350-minute clock) is judged on its time PAST the hold against the room its clock leaves, never
as a share of the clock: the first version read `clock:collect` DEGRADED every hour for good.
Measured that way collect still reads DEGRADED, rightly: its hold was counted from after its
Tests step, and 11-11's held run took 348.9 of 350 minutes (§7). Counting the hold from the
job's start is its own change, with its own hand upload of collect.yml.

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
#   find:         lim, hold, secs = _own_clock(name, mine) * 60, _own_hold(name, holds), round((b - a).total_seconds())
#   with:         lim, hold, secs = DEFAULT_CLOCK * 60, _own_hold(name, holds), round((b - a).total_seconds())
#
# @vacuity 🔴🔴 a job that holds on purpose is judged on its time PAST the hold, against the room after it
#   file: runs_report.py
#   find:                                 "secs": max(0, secs - hold * 60), "limit": lim - hold * 60})
#   with:                                 "secs": secs, "limit": lim})
#
# @vacuity 🔴 the hold is READ from the workflow, the env collect.yml's loop reads
#   file: runs_report.py
#   find: HOLD_ENV = "LOOP_MINUTES"
#   with: HOLD_ENV = "LOOP_MINUTES_X"
#
# @vacuity 🔴 ...the LONGEST hold its step can write
#   file: runs_report.py
#   find:     return max(nums) if nums else wfparse.UNREADABLE
#   with:     return min(nums) if nums else wfparse.UNREADABLE
#
# @vacuity ⚠️ ...only what the step writes to $GITHUB_OUTPUT, never a comment
#   file: runs_report.py
#   find:             if "GITHUB_OUTPUT" in ln and not ln.strip().startswith("#")
#   with:             if True
#
# @vacuity ⚠️ a hold that cannot be read is "could not look", never a whole-clock reading
#   file: runs_report.py
#   find:             rec["unread"].append("%s: its hold (%s) cannot be read" % (name, HOLD_ENV))
#   with:             pass
#
# @vacuity ⚠️ a sweep part that never reached its Tests step had no file clock running
#   file: runs_report.py
#   find:             elif not steps or (st is not None and (sa is None or st.get("conclusion") == "skipped")):
#   with:             elif False:
#
# @vacuity ⚠️ ...but one whose Tests step started and never finished could not be read
#   file: runs_report.py
#   find:                 rec["unread"].append("%s: its %s step started and never finished" % (name, sweep[0]))
#   with:                 pass
#
# @vacuity ⚠️ the advice keeps its own capitals ("a Sam upload"), never str.capitalize()
#   file: runs_report.py
#   find:     return s[:1].upper() + s[1:]
#   with:     return s.capitalize()
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
# @vacuity 🔴 a failing jobs API is asked twice a write, never once per run left
#   file: runs_report.py
#   find:                 break               # 🔴 a failing API is asked twice a write, never 40 times
#   with:                 pass
#
# @vacuity ⚠️ ...two failures IN A ROW: one bad run never holds back the runs after it
#   file: runs_report.py
#   find:         failed = 0                  # ⚠️ one bad run never holds back the runs after it
#   with:         pass
#
# @vacuity ⚠️ ...and no reading runs past its time budget
#   file: runs_report.py
#   find:         if clock() - began >= budget:
#   with:         if False:
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
# @vacuity ⚠️ a fresh run list the previous code wrote (no clocks in it) is a note, not a finding
#   file: watchdog.py
#   find:         rep.note_clocks = {"could_not_look": r["why"]}
#   with:         rep.warn("clock:unread", "how close the jobs came to their clocks could not be read", r["why"])
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
import ast
import copy
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import runs_report as R  # noqa: E402
import status as S  # noqa: E402
import watchdog as W  # noqa: E402
import wfparse  # noqa: E402

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
    # `[2026-11-17, the review]` parts that never reached their Tests step: no file clock ran
    job("tests · sweep 3/4", 380, conclusion="cancelled"),             # no steps (39007201224's shape)
    job("tests · sweep 4/4", 70, conclusion="failure", steps=[
        step("Set up job", 5), dict(step("Tests", 0), conclusion="skipped", started_at=None,
                                    completed_at=None)]),
    job("tests (ubuntu-26.04) · sweep 3/4", 90, conclusion="cancelled", steps=[
        step("Set up job", 5), dict(step("Tests", 0), conclusion="cancelled", started_at=None,
                                    completed_at=None)]),
    job("tests (ubuntu-26.04) · sweep 4/4", 4000, steps=[
        step("Set up job", 5), dict(step("Tests", 3900), completed_at=None)]),
], MINE, SWEEP, NAMES)
eq(sorted((j["job"], j.get("clock", "job"), j["secs"], j["limit"]) for j in _rec["jobs"]), sorted([
    ("tests · sweep 1/4", "job", 4400, 7200),
    ("tests · sweep 1/4", "file test_vacuity.py", 4320, 5400),
    ("render (ubuntu-26.04)", "job", 600, 1500),
    ("tests (ubuntu-26.04) · sweep 2/4", "job", 3000, 7200),
    ("tests · sweep 3/4", "job", 380, 7200),
    ("tests · sweep 4/4", "job", 70, 7200),
    ("tests (ubuntu-26.04) · sweep 3/4", "job", 90, 7200),
    ("tests (ubuntu-26.04) · sweep 4/4", "job", 4000, 7200)]),
   "🔴🔴 each job is held to ITS OWN clock (120 / 25 minutes), and a sweep part's Tests step to 5400s")
eq(sorted(_rec.get("unread") or []), sorted([
    "tests (off-season, no games): started and never finished",
    "tests (ubuntu-26.04) · sweep 2/4: its steps list no Tests step",
    "tests (ubuntu-26.04) · sweep 4/4: its Tests step started and never finished"]),
   "⚠️ a job that never finished, a sweep part whose steps list no Tests step, and a Tests step "
   "that started and never finished are named as unread; a job that never ran (queued or "
   "skipped), and a sweep part that never reached its Tests step (no steps, or the step skipped "
   "or cancelled before it started), had no clock running")
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
eq(R.clock_advice(".github/workflows/browser.yml", "render", "job"),
   "make it shorter or split it; do not raise the clock", "   ...and any other job is told to shorten")
eq(R.clock_advice(".github/workflows/collect.yml", "collect", "hold 320"),
   "count the hold from the job's start, or shorten what runs outside it (the steps before it, its "
   "last pass); do not raise the clock", "   ...and a job that holds, never to cut its hold or raise its clock")
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
_fn, _nn = watch({"generated_at": T(10), "runs": []})
eq((_fn, (_nn or {}).get("could_not_look")),
   ([], "runs.json carries no job clocks: the hourly runs watcher has not written them yet"),
   "⚠️ a FRESH run list with no clocks in it (main's runs.json the hour this merges, written by "
   "the previous code) is the note, not a finding: it clears itself on the next write "
   "(the review: ~~DEGRADED `clock:unread`~~ for hours)")
_fe, _ = watch(doc(rec(1, [_SW(1000)]), errors=[{"run_id": 9, "file": PR, "why": "RuntimeError: HTTP 502"}]))
eq([(i["key"], i["severity"]) for i in _fe], [("clock:unread", "DEGRADED")],
   "🔴 ...while a jobs call the API refused is still DEGRADED: that job really could not be read")
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

# ── `[2026-11-17, the review]` the advice keeps its own capitals ──
_VY = ".github/workflows/vacuity.yml"
_nightly = doc(rec(3, [{"job": "sweep (2)", "secs": 6000, "limit": 7200}], path=_VY, workflow="vacuity"))
_SAM = "Add parts (vacuity.yml's `part:` matrix, a Sam upload); do not raise the clock"
_fv, _ = watch(_nightly)
ck("🔴 the advice keeps its own capitals: a nightly part reads \"a Sam upload\" in the email and the "
   "finding, never \"a sam upload\" (str.capitalize() lowers every letter but the first)",
   any(ln.endswith(_SAM + ".") for ln in S.clock_lines(_nightly, None, NOW))
   and len(_fv) == 1 and _SAM in _fv[0]["why"],
   (S.clock_lines(_nightly, None, NOW), _fv and _fv[0]["why"]))
eq(R.sentence("count the hold from the job's start; ask Sam"), "Count the hold from the job's start; ask Sam",
   "   ...`sentence` raises the first letter and touches nothing else")
# ⚠️ THE CLASS: no module raises a sentence with str.capitalize(); `runs_report.sentence` does it.
#    Parsed, so a comment or a docstring that names it is not a call.


def capitalize_calls(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    return ["%s:%d" % (os.path.basename(path), n.lineno) for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "capitalize"]


_cap = [c for f in sorted(glob.glob(os.path.join(ROOT, "*.py")))
        if not os.path.basename(f).startswith("test_") for c in capitalize_calls(f)]
eq(_cap, [], "⚠️ no module calls str.capitalize(), which lowers every capital after the first "
             "(Sam, GitHub, MLB): runs_report.sentence raises the first letter only")
_cp = os.path.join(tempfile.mkdtemp(prefix="jobclocks-cap-"), "planted.py")
TREES.append(os.path.dirname(_cp))
open(_cp, "w", encoding="utf-8").write('"""str.capitalize() named in a docstring"""\nx = "a Sam".capitalize()\n')
eq(capitalize_calls(_cp), ["planted.py:2"], "   ...and the sweep finds a planted call, and not the docstring")

# ════════════════════════════════════════════════════════════════════════
section("5. 💰 EACH FINISHED RUN IS READ ONCE, AT MOST 40 A WRITE, AND A FAILED CALL IS RETRIED")
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
   "💰 at most CLOCK_READS_PER_WRITE (%d) calls a write of runs.json, the newest runs first (two "
   "writers: runs.yml's publish and collect's `runs` row)" % R.CLOCK_READS_PER_WRITE)
_old = [rec(7, [_SW(100)], ended_ago=8 * 24 * 60), rec(8, [_SW(100)], ended_ago=60)]
_recs4, _ = R.read_clocks([], NOW, NAMES, _old, Api({}), ROOT)
eq([r["run_id"] for r in _recs4], [8], "⚠️ a record older than 7 days is dropped")
# `[2026-11-17, the review]` a jobs endpoint that fails every call (a timeout is 60s a call in
#    `_gh_json`) was asked for every run left: up to 40 minutes inside runs.yml's 10-minute job
_down = Api({}, broken={1000 + k for k in range(R.CLOCK_READS_PER_WRITE + 5)})
_recs5, _errs5 = R.read_clocks(_many, NOW, NAMES, [], _down, ROOT)
eq((R.CLOCK_FAILS_IN_A_ROW, len(_down.calls), len(_recs5), [e["run_id"] for e in _errs5]),
   (2, 2, 0, [1000, 1001]),
   "🔴 a failing jobs API is asked TWICE a write: two failures in a row end the reading, the "
   "runs after them are left for the next write, never recorded")
# ...but a run whose own call keeps failing (any reason) must not hold back the older runs
#    behind it, write after write, until it leaves the run list
_bad2 = Api({}, broken={1000, 1005})
_recs5b, _errs5b = R.read_clocks(_many, NOW, NAMES, [], _bad2, ROOT)
eq((len(_bad2.calls), len(_recs5b), [e["run_id"] for e in _errs5b]),
   (R.CLOCK_READS_PER_WRITE, R.CLOCK_READS_PER_WRITE - 2, [1000, 1005]),
   "⚠️ ...while two runs whose calls fail APART are two errors, and every other run is still read")
_t = [0.0]


def _slow(path):
    _t[0] += 50                     # every call takes 50 s, and answers
    return {"jobs": [job("render", 300)]}


_recs6, _errs6 = R.read_clocks(_many, NOW, NAMES, [], _slow, ROOT, clock=lambda: _t[0])
_fit = -(-R.CLOCK_READ_BUDGET_S // 50)    # calls started before the budget ran out
eq((len(_recs6), _errs6, _t[0]), (_fit, [], 50.0 * _fit),
   "⚠️ a slow API is read for at most CLOCK_READ_BUDGET_S (%ds) a write, then left for the next"
   % R.CLOCK_READ_BUDGET_S)
ck("   ...and that budget is well inside runs.yml's publish clock (%s min)"
   % R.job_clocks(ROOT)[".github/workflows/runs.yml"].get("publish"),
   R.CLOCK_READ_BUDGET_S + 60 < 60 * (R.job_clocks(ROOT)[".github/workflows/runs.yml"].get("publish") or 0) / 2,
   "the budget plus one last 60s call must leave the job most of its clock")

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

# ════════════════════════════════════════════════════════════════════════
section("7. 🔴🔴 A JOB THAT HOLDS ON PURPOSE IS JUDGED PAST ITS HOLD, AGAINST THE ROOM ITS CLOCK LEAVES")
# ════════════════════════════════════════════════════════════════════════
# `[2026-11-17, the review]` collect's scheduled MLB runs hold LOOP_MINUTES inside their clock
# (`[Sam, 2026-10-06]` the relay): a held run is 91%+ of its clock BY DESIGN, and the first
# version read `clock:collect` DEGRADED for good, telling Sam to shorten his hold.
_DEMO = """\
name: demo
on:
  schedule:
    - cron: "17 3 * * 1"
jobs:
  hold:
    runs-on: ubuntu-24.04
    timeout-minutes: 100
    steps:
      - name: Decide
        id: mode
        run: |
          # loop_minutes=999 is a comment, never a write
          echo "loop_minutes=0" >> "$GITHUB_OUTPUT"
          echo "loop_minutes=80" >> "$GITHUB_OUTPUT"
          X="loop_minutes=500"
      - name: Hold
        env:
          LOOP_MINUTES: ${{ steps.mode.outputs.loop_minutes }}
        run: |
          echo hold
  literal:
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    steps:
      - name: Wait
        env:
          LOOP_MINUTES: 20   # a literal
        run: echo w
  lost:
    runs-on: ubuntu-24.04
    steps:
      - name: Hold
        env:
          LOOP_MINUTES: ${{ steps.gone.outputs.loop_minutes }}
        run: echo l
  plain:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - run: echo p
"""
_hd = tempfile.mkdtemp(prefix="jobclocks-holds-")
TREES.append(_hd)
os.makedirs(os.path.join(_hd, ".github", "workflows"))
open(os.path.join(_hd, ".github", "workflows", "demo.yml"), "w", encoding="utf-8").write(_DEMO)
_dh = R.job_holds(_hd).get(".github/workflows/demo.yml") or {}
eq((_dh.get("hold"), _dh.get("literal"), "plain" in _dh), (80, 20, False),
   "🔴 a hold is READ: the longest `loop_minutes=N` its step writes to $GITHUB_OUTPUT (never a "
   "comment, never another line), or the env's own number; a job that holds nothing is not listed")
ck("⚠️ a hold whose source cannot be read is UNREADABLE, never 0", _dh.get("lost") is wfparse.UNREADABLE,
   _dh.get("lost"))
_dc = R.job_clocks(_hd)[".github/workflows/demo.yml"]
_lost = R.clock_record(run(31, path=".github/workflows/demo.yml", name="demo"),
                       [job("lost", 600), job("hold", 85 * 60)], _dc, SWEEP, NAMES, _dh)
eq((_lost["jobs"], _lost.get("unread")),
   ([{"job": "hold", "clock": "hold 80", "secs": 300, "limit": 1200}],
    ["lost: its hold (LOOP_MINUTES) cannot be read"]),
   "🔴 a held job is measured PAST its hold, against the room its clock leaves; one whose hold "
   "cannot be read is \"could not look\", never a whole-clock reading")
eq(R.clock_record(run(32, path=".github/workflows/demo.yml", name="demo"), [job("literal", 600)],
                  {"literal": 20}, SWEEP, NAMES, {"literal": 20}).get("unread"),
   ["literal: its 20-minute hold leaves no room in its 20-minute clock"],
   "⚠️ a hold no shorter than its clock cannot be judged, and says so")

CO = ".github/workflows/collect.yml"
_H = (R.job_holds(ROOT).get(CO) or {}).get("collect")
_C = R.job_clocks(ROOT)[CO].get("collect")
ck("🔴 collect's hold is read from collect.yml itself, and is shorter than its clock (%r of %r minutes)"
   % (_H, _C), isinstance(_H, int) and 0 < _H < (_C or 0))
_H, _C = (_H, _C) if isinstance(_H, int) and 0 < _H < (_C or 0) else (320, 350)
_ROOM = (_C - _H) * 60


def collect_run(i, secs):
    """One collect run whose job took `secs`, read the way read_clocks reads it."""
    return R.clock_record(run(i, path=CO, name="collect"), [job("collect", secs)],
                          R.job_clocks(ROOT)[CO], SWEEP, NAMES, R.job_holds(ROOT).get(CO))


_cases = (("a healthy hold: 7 minutes of tests, the hold, a 1-minute last pass", (7 + _H + 1) * 60, []),
          ("a hold with 15 minutes to spare", (_C - 15) * 60, []),
          ("a one-pass run (a push, a football pass)", 25 * 60, []),
          ("11-11's run, about a minute (66 s) from the kill", _C * 60 - 66, ["clock:collect"]),
          ("a run 7 minutes from the kill, 77% of the room", (_C - 7) * 60, ["clock:collect"]))
for _what, _secs, _want in _cases:
    _fc, _ = watch(doc(collect_run(41, _secs)))
    eq([i["key"] for i in _fc], _want, "🔴🔴 %s (%d of %d minutes): %s" % (
        _what, _secs // 60, _C, "DEGRADED" if _want else "silent"))
_fk, _ = watch(doc(collect_run(42, _C * 60 - 66)))
ck("🔴 ...and it says what it measured and what to do: never shorten the hold, never raise the clock",
   _fk and "the room its clock leaves past its hold" in _fk[0]["what"]
   and "ran %ds past its %d-minute hold" % (_ROOM - 66, _H) in _fk[0]["why"]
   and "Count the hold from the job's start" in _fk[0]["why"] and "do not raise the clock" in _fk[0]["why"],
   _fk and (_fk[0]["what"], _fk[0]["why"]))
_sw80, _ = watch(doc(collect_run(43, (7 + _H + 1) * 60), rec(44, [_SW(4320)])))
eq([i["key"] for i in _sw80], ["clock:pr-tests"],
   "🔴 a healthy collect hold beside a sweep part at 80%: only the sweep part is DEGRADED")

note("⛔ WHAT THIS DOES NOT SEE: a file in the `rest` shard against its own 600s clock, since that "
     "step runs every file but one and a per-file time is only in the job log. The slowest was "
     "172s on 2026-11-12 (29%).")

for _t in TREES:
    shutil.rmtree(_t, ignore_errors=True)
