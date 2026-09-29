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
#   find: .join(wfparse.apply_staged('.')))" > "$staged"
#   with: .join([]))" > "$staged"
#
# @vacuity an UPDATE to a live workflow is a staged change, not only a new file
#   file: wfparse.py
#   find:         if not os.path.exists(live) or not _same(root, f):
#   with:         if not os.path.exists(live):
#
# @vacuity the staged job must run the tests job's own loop, not nothing
#   file: .github/workflows/pr-tests.yml
#   find:           bash -e "$loop"
#   with:           true
#
# @vacuity 🔴 two copies must not share the apply step's answer file
#   file: .github/workflows/pr-tests.yml
#   find: staged=$(mktemp "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/staged.XXXXXX")
#   with: staged=/tmp/staged.txt
#
# @vacuity 🔴 two copies must not share the loop they run
#   file: .github/workflows/pr-tests.yml
#   find: loop=$(mktemp "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/loop.XXXXXX")
#   with: loop=/tmp/loop.sh
#
# @vacuity a declaration must also resolve in a pending upload's staged copy
#   file: vacuity.py
#   find:             copies.append("docs/upload/" + base)
#   with:             pass

🔴 AND THE SAME CLASS, ONE LEVEL DOWN `[2026-09-26, collect #1856]`. A
declared mutation (`@vacuity`) quoted a line of the LIVE `self-repair.yml`
that #184's staged copy no longer had. Every pr-tests job passed: the
sweep checks declarations against the live file, and the `staged` job runs
the `rest` shard, which has no sweep. Sam uploaded; the declaration rotted;
collect went red. `vacuity.rotted` now checks a declaration naming a
workflow with a pending upload against the staged copy too. Section 4.

🔴 AND TWO COPIES AT ONCE `[2026-09-28]`. The job's two shell steps wrote
FIXED files in /tmp. Two copies on one machine (two suites, or the vacuity
sweep's parallel trees) read each other's answer and a correct case
failed; alone it passed. Section 5 replays that collision step by step,
not by timing. The class (any step a test runs) is test_step_tmp.py.
⚠️ Section 4's real-tree rot line is a note(): test_vacuity.py asks it as
a hard check, and asked here it turned every mutation declared above red
by construction, so the sweep could never call one of them VACUOUS.
"""
import os
import shutil
import subprocess
import tempfile

import wfparse as W
from tcheck import ck, eq, note, section, shown

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
    # ⚠️ from a file, never `bash -c`: on Windows a -c script past about 8K
    #    characters is cut short with no error, and the tests job's loop is
    #    already 6K. The file sits outside the repo the tree check reads.
    sd = tempfile.mkdtemp(prefix="staged-sh-")
    try:
        step = os.path.join(sd, "step.sh")
        open(step, "w", encoding="utf-8", newline="\n").write(body)
        p = subprocess.run(["bash", "-e", step], cwd=d, env=env,
                           capture_output=True, text=True, timeout=600)
    finally:
        shutil.rmtree(sd, ignore_errors=True)
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
       "n=%r rc=%r %s" % (n, trc, shown(log[-500:])))
    ck("test_live.py" in log and krc == 0,
       "   ...it names the file, and its own local commit left the tree clean",
       shown(log[-300:]))
finally:
    shutil.rmtree(d, ignore_errors=True)

d = repo("on: push\n")                      # staged == live
try:
    n, trc, krc, log = staged_job(d)
    ck(n == "0" and trc == 0,
       "✅ with nothing staged that differs, it says so and stays green",
       "n=%r rc=%r %s" % (n, trc, shown(log[-300:])))
finally:
    shutil.rmtree(d, ignore_errors=True)
# ══════════════════════════════════════════════════════════════════════
section("4. 🔴🔴 A DECLARED MUTATION MUST SURVIVE THE UPLOAD IT WAITS FOR")
# ══════════════════════════════════════════════════════════════════════
import vacuity as V  # noqa: E402


def decl_tree(staged_text):
    d = tempfile.mkdtemp(prefix="staged-decl-")
    for sub in (".github/workflows", "docs/upload"):
        os.makedirs(os.path.join(d, sub))
    open(os.path.join(d, ".github", "workflows", "w.yml"), "w").write(
        "on: push\n# keep = sys.argv[1]\n")
    open(os.path.join(d, "docs", "upload", "w.yml"), "w").write(staged_text)
    open(os.path.join(d, "test_w.py"), "w").write(
        "# @vacuity planted\n#   file: .github/workflows/w.yml\n"
        "#   find: keep = sys.argv[1]\n#   with: keep = $X\n")
    return d


for why, staged, want in (
        ("the staged copy drops the declared line (the #1856 shape)", "on: push\n", 1),
        ("the staged copy still has it", "on: push\n# keep = sys.argv[1]\n# more\n", 0),
        ("nothing is pending (staged == live)", "on: push\n# keep = sys.argv[1]\n", 0)):
    d = decl_tree(staged)
    try:
        _r = V.rotted(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    eq(len(_r), want, "%s: %d finding(s)" % (why, want))
    if want:
        ck(_r and _r[0][1] == "docs/upload/w.yml" and "STAGED" in _r[0][2],
           "   ...and it names the STAGED copy, so the fix is made before the upload",
           "%r" % (_r,))
_real = V.rotted(ROOT)
# ⚠️ A NOTE, NOT A CHECK `[2026-09-28]`. The question is unchanged and is
#    still asked as a hard check, in the file that owns it:
#    test_vacuity.py ("NO DECLARED MUTATION HAS ROTTED AWAY"), through the
#    same V.rotted, pending uploads included. The three planted trees
#    above ask it here every run. Asked of the real tree HERE, it failed
#    under every mutation this file declares (each one removes its own
#    `find`), so all of them went red whatever the check they name did.
note("real tree: %d rotted declaration(s)%s (the hard check is test_vacuity.py)"
     % (len(_real), (": %r" % (_real,)) if _real else ""))

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴🔴 TWO COPIES AT ONCE MUST NOT READ EACH OTHER'S FILES")
# ══════════════════════════════════════════════════════════════════════
# `[2026-09-28]` Both staged steps wrote a FIXED path in /tmp. Two copies
# on one machine read each other's answer and a correct case failed.
# ✅ REPLAYED, NOT RACED: copy A runs its REAL step up to the line that
# writes its file and WAITS; copy B runs its whole step; A is released.
# The only line added is the wait. ⛔ A race left to timing would pass most
# runs and prove nothing.
import time  # noqa: E402

PAUSE = 'while [ ! -e "$PAUSE_GO" ]; do sleep 0.05; done'


def replay(dA, bodyA, after, dB, bodyB):
    """A runs to the one live line containing `after` and waits, B runs
    whole, then A finishes. -> ((rcA, logA, outA), (rcB, logB, outB))"""
    lines = bodyA.split("\n")
    k = [i for i, l in enumerate(lines)
         if after in l and not l.lstrip().startswith("#")]
    if len(k) != 1:
        return ((None, "pause point %r found %d times" % (after, len(k)), {}),
                (None, "", {}))
    # ⛔ control files in their own dir, never in the repo: the tree check
    #    would see them.
    ctl = tempfile.mkdtemp(prefix="staged-ctl-")
    pA = None
    try:
        at, go, oA, oB = (os.path.join(ctl, x).replace(os.sep, "/")
                          for x in ("at", "go", "oA", "oB"))
        for o in (oA, oB):
            open(o, "w").close()
        # ⚠️ from a file, never `bash -c` (Windows cuts a long -c script short)
        sA, sB = os.path.join(ctl, "a.sh"), os.path.join(ctl, "b.sh")
        open(sA, "w", newline="\n").write("\n".join(
            lines[:k[0] + 1] + [': > "$PAUSE_AT"', PAUSE] + lines[k[0] + 1:]))
        open(sB, "w", newline="\n").write(bodyB)
        env = dict(os.environ, SUITE_SHARD="rest", PAUSE_AT=at, PAUSE_GO=go)
        pA = subprocess.Popen(["bash", "-e", sA], cwd=dA, text=True,
                              env=dict(env, GITHUB_OUTPUT=oA),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        t0 = time.time()
        while not os.path.exists(at) and pA.poll() is None and time.time() - t0 < 120:
            time.sleep(0.05)
        reached = os.path.exists(at)
        pB = subprocess.run(["bash", "-e", sB], cwd=dB, text=True, timeout=600,
                            env=dict(env, GITHUB_OUTPUT=oB), capture_output=True)
        open(go, "w").close()
        logA = pA.communicate(timeout=600)[0]

        def out(o):
            return dict(l.split("=", 1) for l in open(o).read().split() if "=" in l)
        return ((pA.returncode if reached else None, logA, out(oA)),
                (pB.returncode, pB.stdout + pB.stderr, out(oB)))
    finally:
        # ⛔ never leave copy A waiting on a file that will not come
        if pA is not None and pA.poll() is None:
            pA.kill()
            pA.wait()
        shutil.rmtree(ctl, ignore_errors=True)


# 5a. the apply step: A has a staged change, B has none
dA, dB = repo("on: push\n# SWITCHES_ON_A_17TH_ROW\n"), repo("on: push\n")
try:
    (rA, lA, oA), (rB, lB, oB) = replay(dA, APPLY.run, "apply_staged(", dB, APPLY.run)
    ck(rA == 0 and oA.get("n") == "1",
       "🔴🔴 copy A still sees ITS staged change while copy B ran beside it",
       "rc=%r n=%r %s" % (rA, oA.get("n"), shown(lA[-300:])))
    ck(rB == 0 and oB.get("n") == "0",
       "   ...and copy B still sees nothing staged, and stays green",
       "rc=%r n=%r %s" % (rB, oB.get("n"), shown(lB[-300:])))
finally:
    shutil.rmtree(dA, ignore_errors=True)
    shutil.rmtree(dB, ignore_errors=True)

# 5b. the tests step: A's planted test fails once applied; B's loop is green
dA, dB = repo("on: push\n# SWITCHES_ON_A_17TH_ROW\n"), repo("on: push\n")
try:
    OTHER = "THE OTHER COPY'S LOOP"
    open(os.path.join(dB, ".github", "workflows", "pr-tests.yml"), "w").write(
        "jobs:\n  tests:\n    steps:\n      - name: Tests\n        run: |\n"
        "          run_one() { :; }\n          echo \"%s\"\n" % OTHER)
    _o0 = tempfile.mkdtemp(prefix="staged-o-")
    try:
        rc0, log0 = sh(dA, APPLY.run, os.path.join(_o0, "o"))
    finally:
        shutil.rmtree(_o0, ignore_errors=True)
    (rA, lA, _oA), (rB, lB, _oB) = replay(dA, TESTS.run, "step_run(", dB, TESTS.run)
    ck(rc0 == 0 and rA not in (0, None) and "test_live.py" in lA and OTHER not in lA,
       "🔴🔴 copy A runs ITS OWN loop, and is red on its planted test, while "
       "copy B ran a green one beside it",
       "apply rc=%r tests rc=%r other_loop_ran_in_A=%s %s"
       % (rc0, rA, OTHER in lA, shown(lA[-300:])))
    ck(rB == 0 and OTHER in lB,
       "   ...and copy B ran its own green loop", "rc=%r %s" % (rB, shown(lB[-200:])))
finally:
    shutil.rmtree(dA, ignore_errors=True)
    shutil.rmtree(dB, ignore_errors=True)

note("⛔ WHAT THIS DOES NOT CLAIM: that an uploaded file matches its staged "
     "copy. runs_report.stale_uploads times a pending upload, and "
     "test_top_level_yaml.py catches one put in the wrong folder.")
