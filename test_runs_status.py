#!/usr/bin/env python3
"""RUN STATUS, READABLE WITHOUT A GITHUB LOGIN — `data/latest/runs.json`.

🔴 WHY `[Sam, 2026-09-25]`: "Nobody can read run status reliably from
outside GitHub." Collect runs had failed since 06:44Z and the only way to
see which, and why, was the Actions page. The hourly runs watcher now also
writes the last 48 hours of every workflow into the repo.

✅ WHAT THIS PINS:
  1. the file's rows carry what was asked for — run number, trigger,
     start, conclusion — and a FAILED run its failing step and its error
     annotations (collect.yml fails a LATE step, "Fail if the tests
     failed", so the annotations are what name the broken file);
  2. it covers 48 hours, not the watcher's 24, by the same paging rule;
  3. `collect.py runs` is the one writer, free of Odds credits;
  4. its freshness row: stale only when TWO hourly runs are missing, SOFT,
     off the reader's banner — and absent until the watcher is deployed;
  5. the staged runs.yml writes it from its OWN job, so the watcher job
     stays read-only, and changes no cron line.

⚠️ The REST fixtures are copied from this repo's own runs on 2026-09-25
(collect #1832, #1830, #1814; job 108186680616's steps). No network.

# @vacuity a failed run must name the step that failed
#   file: runs_report.py
#   find: steps.extend(pre + (s or "?") for s in bad)
#   with: pass
#
# @vacuity ...and its error annotations, which name the failing file
#   file: runs_report.py
#   find: if a.get("annotation_level") == "failure" and a.get("message"):
#   with: if False:
#
# @vacuity the file covers 48 hours, not the watcher's 24
#   file: runs_report.py
#   find: STATUS_WINDOW_H = 48
#   with: STATUS_WINDOW_H = 24
#
# @vacuity a finished run's detail is reused, not re-bought every hour
#   file: runs_report.py
#   find: if old and "failing_steps" in old and not old.get("detail_error"):
#   with: if False:
#
# @vacuity one missed hourly run must not flap the watchdog
#   file: freshness.py
#   find: LATE_GRACE_MIN = {"runs": 100}
#   with: LATE_GRACE_MIN = {}
#
# @vacuity a monitoring file stays off the reader's stale banner
#   file: index.html
#   find: const bad = FRESH.artifacts.filter(a => a.stale && a.page !== false);
#   with: const bad = FRESH.artifacts.filter(a => a.stale);
#
# @vacuity the row must not exist before the watcher that writes it
#   file: freshness.py
#   find:     if not runs_writer_deployed(root):
#   with:     if False:
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from jsblock import js_block
from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "mlb")
import freshness as F  # noqa: E402
import runs_report as R  # noqa: E402
import wfparse  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 9, 25, 18, 45, tzinfo=UTC)
NAMES = R.workflow_names(ROOT)


def run(i, n, when, conclusion, event="schedule", title=None,
        path=".github/workflows/collect.yml", name=None, attempt=1):
    """A REST workflow-run object in the shape /actions/runs returns."""
    return {"id": i, "run_number": n, "run_attempt": attempt, "event": event,
            "status": "completed" if conclusion else "in_progress",
            "conclusion": conclusion, "path": path,
            "name": name or title or "collect", "display_title": title or "collect",
            "created_at": when, "run_started_at": when,
            "html_url": "https://github.com/smh0602/gizmos-picks/actions/runs/%d" % i}


RAW = [
    run(36169924938, 1832, "2026-09-25T17:53:13Z", "failure",
        title="collect [cron 6 13 * * *]"),
    run(36169403672, 1830, "2026-09-25T17:48:14Z", "cancelled",
        title="collect [cron 5 13,19,1 * * *]"),
    run(36109962481, 1814, "2026-09-25T07:53:20Z", "success",
        title="collect [cron 20 * * * *]"),
    run(36104224611, 1813, "2026-09-25T06:44:17Z", "failure", event="push",
        title="collect [push]"),
    run(1, 900, "2026-09-25T18:40:00Z", None, title="runs [cron 41 * * * *]",
        path=".github/workflows/runs.yml"),
    run(2, 5000, "2026-09-25T18:34:00Z", "success", event="dynamic",
        title="pages build and deployment", name="pages build and deployment",
        path="dynamic/pages/pages-build-deployment"),
    run(3, 42, "2026-09-25T10:00:00Z", "startup_failure", event="push",
        title="runs [push]", path=".github/workflows/runs.yml"),
    # the same run again (a page boundary moved between calls) ...
    run(36169924938, 1832, "2026-09-25T17:53:13Z", "failure",
        title="collect [cron 6 13 * * *]"),
    # ... and one outside the 48h window
    run(4, 1700, "2026-09-23T17:00:00Z", "failure", title="collect [cron 6 13 * * *]"),
]
# job 108186680616 of run #1832, as the jobs API returned it
JOB_1832 = {"id": 108186680616, "name": "collect", "conclusion": "failure",
            "check_run_url": "https://api.github.com/repos/smh0602/gizmos-picks/check-runs/108186680616",
            "steps": [{"name": "Tests", "conclusion": "success"},
                      {"name": "Converge and hold", "conclusion": "success"},
                      {"name": "Fail if the tests failed", "conclusion": "failure"},
                      {"name": "Fail if any pass failed", "conclusion": "skipped"}]}
ANN_1832 = [{"annotation_level": "failure", "message": "test_board_match.js FAILED"},
            {"annotation_level": "failure",
             "message": "the test suite failed — see the Tests step"},
            {"annotation_level": "warning", "message": "Node.js 20 is deprecated"}]
JOB_1813 = {"id": 107973154906, "name": "collect", "conclusion": "failure",
            "steps": [{"name": "Fail if the tests failed", "conclusion": "skipped"},
                      {"name": "Fail if any pass failed", "conclusion": "failure"}]}
ANN_1813 = [{"annotation_level": "failure", "message": "verify_record failed"}]


class Api:
    def __init__(self, broken=()):
        self.calls, self.broken = [], set(broken)

    def __call__(self, path):
        self.calls.append(path)
        for rid in self.broken:
            if str(rid) in path:
                raise RuntimeError("gh api %s: HTTP 502" % path)
        if path.startswith("actions/runs/36169924938/jobs"):
            return {"jobs": [JOB_1832]}
        if path.startswith("actions/runs/36104224611/jobs"):
            return {"jobs": [JOB_1813]}
        if path.startswith("actions/runs/3/jobs"):
            return {"jobs": []}
        if path == "check-runs/108186680616/annotations":
            return ANN_1832
        if path == "check-runs/107973154906/annotations":
            return ANN_1813
        raise AssertionError("unexpected API call " + path)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 EVERY RUN, WITH WHAT SAM ASKED FOR, AND WHY A FAILURE FAILED")
# ══════════════════════════════════════════════════════════════════════
api = Api()
doc = R.status_doc(RAW, NOW, NAMES, {}, api, pages=1, covered=True)
rows = {(r["run_id"]): r for r in doc["runs"]}
eq(len(doc["runs"]), 7, "7 runs in the window: the duplicate once, the 09-23 run dropped")
ck(all(all(k in r for k in ("run_number", "trigger", "started", "conclusion"))
       for r in doc["runs"]),
   "every row carries run number, trigger, start and conclusion")
ck([r["started"] for r in doc["runs"]] == sorted((r["started"] for r in doc["runs"]),
                                                 reverse=True), "newest first")
r1832 = rows[36169924938]
eq((r1832["run_number"], r1832["trigger"], r1832.get("cron"), r1832["workflow"]),
   (1832, "schedule", "6 13 * * *", "collect"),
   "#1832: which cron fired it is read from the run's own stamp")
eq(r1832.get("failing_steps"), ["Fail if the tests failed"], "🔴 #1832 names its failing step")
ck(r1832.get("annotations") == ["test_board_match.js FAILED",
                                "the test suite failed — see the Tests step"],
   "🔴 ...and its error annotations — the step alone says nothing; these name the file",
   "got %s (a warning must not be listed)" % r1832.get("annotations"))
eq(rows[36104224611].get("annotations"), ["verify_record failed"],
   "#1813 (push) says verify_record failed")
ck(all("failing_steps" not in rows[i] for i in (36169403672, 36109962481, 1, 2)),
   "success, cancelled and in-progress runs carry no failure detail")
eq(rows[3].get("note"), "no job ran", "a startup failure says no job ran")
ck(doc["by_workflow"]["collect"]["runs"] == 4 and doc["by_workflow"]["collect"]["failed"] == 2
   and doc["by_workflow"]["collect"]["latest"]["run_number"] == 1832,
   "the per-workflow summary counts and names the latest run",
   str(doc["by_workflow"].get("collect")))
ck("pages build and deployment" in doc["by_workflow"] and "runs" in doc["by_workflow"],
   "every workflow is listed, the Pages build included")

# ⚠️ detail is bought once: a finished run never changes
api2 = Api()
R.status_doc(RAW, NOW, NAMES, {(r["run_id"], r["attempt"], r["conclusion"]): r
                               for r in doc["runs"]}, api2)
ck(api2.calls == [], "the next hour reuses a finished run's detail (0 API calls)",
   str(api2.calls))
_rerun = [dict(RAW[0], run_attempt=2)] + RAW[1:]
api3 = Api()
R.status_doc(_rerun, NOW, NAMES, {(r["run_id"], r["attempt"], r["conclusion"]): r
                                  for r in doc["runs"]}, api3)
ck(any("36169924938" in c for c in api3.calls),
   "  ...but a RE-RUN (attempt 2) is asked about again")
api4 = Api(broken=[36104224611])
d4 = R.status_doc(RAW, NOW, NAMES, {}, api4)
ck("HTTP 502" in ({r["run_id"]: r for r in d4["runs"]}[36104224611].get("detail_error") or "")
   and {r["run_id"]: r for r in d4["runs"]}[36169924938].get("failing_steps"),
   "a detail call that fails is RECORDED on that row, and the rest still lands")

# ══════════════════════════════════════════════════════════════════════
section("2. 48 HOURS, BY THE SAME PAGING RULE — AND THE FILE ITSELF")
# ══════════════════════════════════════════════════════════════════════
def pages(n_pages, step_h):
    """n full pages, one run every `step_h` hours going back from NOW."""
    out, k = [], 0
    for p in range(n_pages):
        pg = []
        for _ in range(R.REST_PER_PAGE):
            t = NOW - datetime.timedelta(hours=k * step_h)
            pg.append(run(10_000 + k, k, t.strftime("%Y-%m-%dT%H:%M:%SZ"), "success"))
            k += 1
        out.append(pg)
    return lambda i: out[i - 1] if i <= len(out) else []


tmp = tempfile.mkdtemp()
try:
    path = os.path.join(tmp, "data", "latest", "runs.json")
    d = R.write_status(path, fetch_page=pages(5, 0.2), fetch_json=Api(), now=NOW, root=ROOT)
    eq(d["pages_read"], 3, "🔴 the 48h file pages past the watcher's 24h (3 pages, not 2)")
    ck(d["covered"] and d["window_hours"] == 48, "and says the window is covered")
    txt = open(path, encoding="utf-8").read()
    ck(json.loads(txt) == d, "the file on disk is valid JSON and is the document")
    ck(len([l for l in txt.splitlines() if l.startswith('  {"workflow"')]) == d["n_runs"],
       "one run per line (a reader can scan it; git stores each hour as a delta)")
    eq(F.stamp_of(path), NOW, "the freshness contract reads its age from `generated_at`")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("3. ONE WRITER: `collect.py runs`, AND IT SPENDS NO ODDS CREDIT")
# ══════════════════════════════════════════════════════════════════════
import collect as C  # noqa: E402
_src = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
_free = _src.split("FREE = (")[1].split(")")[0]
ck('"runs"' in _free, "`runs` is a FREE mode (no ODDS_API_KEY needed)")
_seen = []
_orig = R.write_status
R.write_status = lambda p, *a, **k: _seen.append(p)
_key, C.ODDS_KEY = C.ODDS_KEY, ""
try:
    C.run_mode("runs")
finally:
    R.write_status, C.ODDS_KEY = _orig, _key
eq(_seen, ["data/latest/runs.json"], "run_mode('runs') writes the one repo-wide file")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 ITS FRESHNESS ROW")
# ══════════════════════════════════════════════════════════════════════
_deployed = F.runs_writer_deployed
ck(_deployed() == (F.RUNS_WRITER in "\n".join(
    l for l in open(os.path.join(ROOT, ".github/workflows/runs.yml"), encoding="utf-8")
    if not l.lstrip().startswith("#"))),
   "the row follows the DEPLOYED runs.yml (today: %s)" % _deployed())
_stage = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(_stage, ".github", "workflows"))
    shutil.copy(os.path.join(ROOT, "docs/upload/runs.yml"),
                os.path.join(_stage, ".github", "workflows", "runs.yml"))
    ck(F.runs_writer_deployed(_stage), "✅ ...and the STAGED runs.yml switches it on")
    ck(F.runs_rows("data/latest", _stage) and not F.runs_rows("data/latest", tempfile.gettempdir()),
       "  no watcher, no row — never a red row on a correct system before the upload")
finally:
    shutil.rmtree(_stage, ignore_errors=True)


def survey_at(age_min, now):
    t = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(t, "data", "latest"))
        if age_min is not None:
            json.dump({"generated_at": (now - datetime.timedelta(minutes=age_min))
                       .strftime("%Y-%m-%dT%H:%M:%SZ")},
                      open(os.path.join(t, "data", "latest", "runs.json"), "w"))
        F.runs_writer_deployed = lambda root=None: True
        return [r for r in F.survey(os.path.join(t, "data"), os.path.join(t, "picks"), now)
                if r["mode"] == "runs"]
    finally:
        F.runs_writer_deployed = _deployed
        shutil.rmtree(t, ignore_errors=True)


_at = datetime.datetime(2026, 9, 25, 18, 50, tzinfo=UTC)   # 50 past, UTC
_one = survey_at(70, _at)          # last hour's run landed, this hour's has not
_two = survey_at(185, _at)         # two hourly runs in a row missing
ck(len(_one) == 1 and not _one[0]["stale"],
   "🔴 one missed hourly run is NOT stale (GitHub drops scheduled runs)",
   "" if _one and not _one[0]["stale"] else str(_one))
ck(_two and _two[0]["stale"], "🔴 two missed in a row IS stale",
   "" if _two and _two[0]["stale"] else str(_two))
# ⚠️ AT THE EDGES THE GRACE WAS DERIVED FROM (a run lands 44-58 past the hour)
_early = survey_at(119, datetime.datetime(2026, 9, 25, 18, 43, tzinfo=UTC))  # landed 16:44
_late = survey_at(123, datetime.datetime(2026, 9, 25, 18, 1, tzinfo=UTC))    # landed 15:58
ck(_early and not _early[0]["stale"],
   "  edge: last landing at :44, next one missed, checked at 18:43 -> NOT stale")
ck(_late and _late[0]["stale"],
   "  edge: last landing at :58, two missed, checked at 18:01 -> stale")
ck(survey_at(None, _at) and survey_at(None, _at)[0]["missing"], "never written is stale")
ck(_one and _one[0]["page"] is False and "runs" in F.SOFT,
   "it is SOFT and marked off the page (a late run list misleads no bettor)")
ck(all(r["page"] for r in F.survey() if r["mode"] != "runs"),
   "  ...and every other row still reaches the banner")

# the banner itself, run in node with the page's own code
_banner = js_block("renderStaleBanner", os.path.join(ROOT, "index.html"))


def banner(rows):
    js = ("const el={className:'',innerHTML:''};"
          "const document={getElementById:()=>el};"
          "let FRESH=%s;%s;renderStaleBanner();"
          "process.stdout.write(el.innerHTML);" % (json.dumps({"artifacts": rows}), _banner))
    p = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    if p.returncode:
        raise SystemExit("renderStaleBanner did not run: " + p.stderr[-400:])
    return p.stdout


_runs_row = dict(_two[0]) if _two else {}
ck(banner([_runs_row]) == "", "🔴 a stale run list alone shows the reader NOTHING")
_card = {"mode": "card", "stale": True, "missing": False, "late_min": 90,
         "due_et": "10:00", "page": True}
ck("Gizmo" in banner([_runs_row, _card]) and "runs" not in banner([_runs_row, _card]),
   "  ...while a stale card beside it still shows, without the run list")

# ══════════════════════════════════════════════════════════════════════
section("5. ⛔ THE STAGED runs.yml: ITS OWN JOB WRITES, THE WATCHER STAYS READ-ONLY")
# ══════════════════════════════════════════════════════════════════════
_st = open(os.path.join(ROOT, "docs/upload/runs.yml"), encoding="utf-8").read()
_dp = open(os.path.join(ROOT, ".github/workflows/runs.yml"), encoding="utf-8").read()
_jobs = {j.name: j for j in wfparse.jobs(_st)}
ck(set(_jobs) == {"watch", "publish"}, "two jobs: watch and publish", str(sorted(_jobs)))
eq(_jobs["watch"].permissions, {"contents": "read", "actions": "read", "issues": "write"},
   "🔴 the watcher's permissions are unchanged — read-only on the repo")
eq(_jobs["publish"].permissions, {"contents": "write", "actions": "read", "checks": "read"},
   "publish may write the repo and read runs and their annotations — nothing else")
_pub = "\n".join(s.run or "" for s in wfparse.steps(_st, "publish"))
ck(F.RUNS_WRITER + " converge-off" in _pub and "bash push_retry.sh" in _pub
   and re.findall(r"git add (\S+)", _pub) == ["data/latest/runs.json"],
   "publish runs the one writer, stages ONLY runs.json, lands it with push_retry.sh")
_cron = lambda t: sorted(re.findall(r"^\s*-\s*cron:.*$", t, re.M))
ck(_cron(_st) == _cron(_dp) and _cron(_st),
   "⛔ NO CRON LINE CHANGES (CLAUDE.md: Sam uploads it, the schedule is untouched)",
   "%s vs %s" % (_cron(_st), _cron(_dp)))
_paths = re.search(r"push:\s*\n\s*branches:.*\n\s*paths:\s*\[([^\]]*)\]", _st)
ck(_paths and "data/" not in _paths.group(1) and "runs.yml" in _paths.group(1),
   "the on-upload push trigger cannot loop (runs.json is not in its path filter)",
   _paths and _paths.group(1))
note("⛔ WHAT THIS DOES NOT CLAIM: that GITHUB_TOKEN may read annotations "
     "in production. `checks: read` is granted for it; the first run after "
     "the upload is the measurement, and a refusal lands on the row as "
     "`detail_error` rather than failing the file.")
