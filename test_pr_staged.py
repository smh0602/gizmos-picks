#!/usr/bin/env python3
"""A STAGED WORKFLOW MUST NOT BE ABLE TO TURN THE SUITE RED AFTER UPLOAD.

🔴 WHAT HAPPENED `[2026-09-25, collect run #1839]`. PR #174 staged a new
`docs/upload/runs.yml`. Every pr-tests job was green. Sam uploaded it and
the next collect run went RED: `test_fb_freshness.py` pinned MLB's
freshness contract at 16 rows, and the uploaded watcher switched on a
17th. I had checked the staged file against ten tests I chose, not the
suite. pr-tests only ever tested the repo as it WAS; a staged workflow
changes what it WILL be, by Sam's hand, after the merge.

✅ THE CLASS GUARD: pr-tests' `staged` job applies every staged upload to
its own checkout and runs the `rest` shard again. This file drives that
job's REAL shell steps (read out of pr-tests.yml) in a throwaway git repo
holding a planted test that passes today and fails once the staged file
is live — and shows the `tests` job's loop cannot see it while the
`staged` job does.

# @vacuity the staged job must actually apply the staged files
#   file: .github/workflows/pr-tests.yml
#   find: .join(wfparse.apply_staged('.')))" > /tmp/staged.txt
#   with: .join([]))" > /tmp/staged.txt
#
# @vacuity an UPDATE to a live workflow is a staged change, not only a new file
#   file: wfparse.py
#   find:         if not os.path.exists(live) or not _same(root, f):
#   with:         if not os.path.exists(live):
#
# @vacuity the staged job must run the tests job's own loop, not nothing
#   file: .github/workflows/pr-tests.yml
#   find:           bash -e /tmp/loop.sh
#   with:           true
"""
import os
import shutil
import subprocess
import tempfile

import wfparse as W
from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
PR = open(os.path.join(ROOT, ".github", "workflows", "pr-tests.yml"), encoding="utf-8").read()

# ══════════════════════════════════════════════════════════════════════
section("1. THE JOB IS THERE, READ-ONLY, AND RUNS THE tests JOB'S OWN LOOP")
# ══════════════════════════════════════════════════════════════════════
_jobs = {j.name: j for j in W.jobs(PR)}
ck("staged" in _jobs, "pr-tests has a `staged` job", str(sorted(_jobs)))
_steps = {s.name: s for s in W.steps(PR, "staged") if s.name}
APPLY = _steps.get("Apply every staged upload (locally, never pushed)")
TESTS = _steps.get("Tests, as they will run after the upload")
TREE = _steps.get("The tests must not have modified the tree")
ck(bool(APPLY and TESTS and TREE), "   ...with its apply, test and tree-check steps",
   str(sorted(_steps)))
ck(W.permissions(PR) == {"contents": "read"} and not _jobs["staged"].permissions,
   "   ⛔ it can write nothing (workflow-level contents: read, no job override)")
ck(TESTS and "step_name='Tests', job='tests'" in (TESTS.run or "")
   and "for t in test_" not in "".join(s.run or "" for s in _steps.values()),
   "🔴 it runs the `tests` job's Tests step, read at run time — not a third copy "
   "of the loop (rule 117)")
eq([TESTS and TESTS.cond, TREE and TREE.cond], ["steps.apply.outputs.n != '0'"] * 2,
   "   it runs the suite whenever something staged differs from what is live")
ck("SUITE_SHARD: rest" in PR.split("  staged:")[1].split("\n  render:")[0],
   "   ...as the `rest` shard (the sweep does not read workflow files)")

# ══════════════════════════════════════════════════════════════════════
section("2. WHAT COUNTS AS A STAGED CHANGE")
# ══════════════════════════════════════════════════════════════════════
t = tempfile.mkdtemp()
try:
    for sub in (".github/workflows", "docs/upload"):
        os.makedirs(os.path.join(t, sub))
    w = lambda sub, f, s: open(os.path.join(t, sub, f), "w", newline="").write(s)
    w(".github/workflows", "same.yml", "a\nb\n")
    w("docs/upload", "same.yml", "a\r\nb\r\n")          # CRLF only: the same file
    w(".github/workflows", "upd.yml", "old\n")
    w("docs/upload", "upd.yml", "new\n")                 # an update Sam must upload
    w("docs/upload", "new.yml", "x\n")                   # a workflow not yet live
    w("docs/upload", "UPLOAD-new.md", "doc\n")           # not a workflow
    eq(W.staged_changes(t), ["new.yml", "upd.yml"],
       "new and updated workflows count; a line-ending difference and a doc do not")
    eq(W.apply_staged(t), ["new.yml", "upd.yml"], "apply_staged copies exactly those")
    eq(W.staged_changes(t), [], "   ...after which nothing staged differs from what is live")
finally:
    shutil.rmtree(t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 IT CATCHES WHAT THE tests JOB CANNOT: THE #1839 SHAPE")
# ══════════════════════════════════════════════════════════════════════
PLANT = (
    "import sys\n"
    "live = open('.github/workflows/w.yml').read()\n"
    "# passes while the old file is live, fails once the staged one is\n"
    "sys.exit(1 if 'SWITCHES_ON_A_17TH_ROW' in live else 0)\n")


def repo(staged_text):
    d = tempfile.mkdtemp(prefix="staged-")
    for sub in (".github/workflows", "docs/upload"):
        os.makedirs(os.path.join(d, sub))
    shutil.copy(os.path.join(ROOT, ".github", "workflows", "pr-tests.yml"),
                os.path.join(d, ".github", "workflows", "pr-tests.yml"))
    shutil.copy(os.path.join(ROOT, "wfparse.py"), d)
    # ⚠️ the repo's own ignore rules: importing wfparse writes __pycache__
    shutil.copy(os.path.join(ROOT, ".gitignore"), d)
    open(os.path.join(d, ".github", "workflows", "w.yml"), "w").write("on: push\n")
    open(os.path.join(d, "docs", "upload", "w.yml"), "w").write(staged_text)
    for n in "abcd":                       # the loop refuses a suite under 4 files
        open(os.path.join(d, "test_%s.py" % n), "w").write("pass\n")
    open(os.path.join(d, "test_live.py"), "w").write(PLANT)
    for c in (["git", "init", "-q"], ["git", "add", "-A"],
              ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"]):
        subprocess.run(c, cwd=d, check=True, capture_output=True)
    return d


def sh(d, body, out=None):
    env = dict(os.environ, SUITE_SHARD="rest", GITHUB_OUTPUT=out or os.devnull)
    p = subprocess.run(["bash", "-e", "-c", body], cwd=d, env=env,
                       capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr


def staged_job(d):
    """The staged job's three steps, their `if:` honoured. -> (n, rc, tree_rc, log)"""
    o = os.path.join(d, ".gh_output")
    rc, log = sh(d, APPLY.run, o)
    if rc:
        return None, rc, None, log
    n = dict(l.split("=", 1) for l in open(o).read().split() if "=" in l).get("n", "")
    os.remove(o)
    if TESTS.cond == "steps.apply.outputs.n != '0'" and n == "0":
        return n, 0, 0, log
    trc, tlog = sh(d, TESTS.run)
    krc, klog = sh(d, TREE.run)
    return n, trc, krc, log + tlog + klog


LOOP = W.step_run(PR, step_name="Tests", job="tests")
d = repo("on: push\n# SWITCHES_ON_A_17TH_ROW\n")
try:
    rc_now, _ = sh(d, LOOP)
    ck(rc_now == 0, "the `tests` job's loop is GREEN on the tree as it is "
       "(this is how #174 went green)")
    n, trc, krc, log = staged_job(d)
    ck(n == "1" and trc != 0,
       "🔴🔴 the `staged` job is RED: the planted test fails once the staged file is live",
       "n=%r rc=%r %s" % (n, trc, log[-500:]))
    ck("test_live.py" in log and krc == 0,
       "   ...it names the file, and its own local commit left the tree clean",
       log[-300:])
finally:
    shutil.rmtree(d, ignore_errors=True)

d = repo("on: push\n")                      # staged == live
try:
    n, trc, krc, log = staged_job(d)
    ck(n == "0" and trc == 0,
       "✅ with nothing staged that differs, it says so and stays green",
       "n=%r rc=%r %s" % (n, trc, log[-300:]))
finally:
    shutil.rmtree(d, ignore_errors=True)
note("⛔ WHAT THIS DOES NOT CLAIM: that an uploaded file matches its staged "
     "copy. runs_report.stale_uploads times a pending upload, and "
     "test_top_level_yaml.py catches one put in the wrong folder.")
