#!/usr/bin/env python3
"""🔴🔴 THE SWEEP RUNS IN PARALLEL TREES — AND STILL ASKS EVERY QUESTION.

`[measured 2026-09-23]` `vacuity.tier2` applied 188 declared mutations ONE
AT A TIME, each run red and then green, so `test_vacuity.py` cost the
serial sum of all of them: 1448s, 2240s, then **2401s = TIMEOUT** against
its 2400s clock in pr-tests, on the same code. `vacuity.yml` was
CANCELLED at its 30-minute limit two nights running. A PR went red on
runner speed alone.

✅ THE FIX RUNS THE SAME DECLARATIONS IN SEVERAL DETACHED WORKTREES AT
ONCE. This file is its guard, driven against a planted repo with known
answers, and it fails if the sweep goes back to a serial sum:
  · runs really OVERLAP in time — a serial sweep never does
  · no two overlapping runs ever share a tree — two mutations in one tree
    is the 2026-09-17 corruption
  · every verdict is still the right one: BITES, VACUOUS, MALFORMED,
    RED_BOTH_WAYS
  · a DIRTY root is swept serially in place, never from HEAD worktrees
  · a worker tree left modified is a LEAK, reported or raised
  · nothing is left behind: no worktree, no temp tree

⛔ This file runs NO real sweep, so unlike `test_vacuity.py` it can carry
declarations of its own — the nightly sweep proves each check here bites.

# @vacuity 🔴🔴 the sweep must actually run in parallel
#   file: vacuity.py
#   find: if jobs > 1 and len(tasks) > 1 and _porcelain(root) == set():
#   with: if False:
#
# @vacuity 🔴 a dirty root is never swept from HEAD worktrees
#   file: vacuity.py
#   find: if jobs > 1 and len(tasks) > 1 and _porcelain(root) == set():
#   with: if jobs > 1 and len(tasks) > 1:
#
# @vacuity ⛔ a worker tree left modified is reported, not swallowed
#   file: vacuity.py
#   find:             leaks.extend(dirty)
#   with:             pass
#
# @vacuity ⛔ one tree is never handed to two workers at once
#   file: vacuity.py
#   find:         tr = free.get()
#   with:         tr = root
#
# @vacuity 🔴 the nightly job's clock may not fall below the PR's sweep clock
#   file: docs/upload/vacuity.yml
#   find:     timeout-minutes: 60
#   with:     timeout-minutes: 30
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import vacuity as V  # noqa: E402

# ⚠️ Each planted test logs "<tree> <start> <end>" to this directory, so
#    concurrency is READ OFF THE RUNS rather than inferred from a clock.
LOG = tempfile.mkdtemp(prefix="vpool-log-")
os.environ["VPOOL_LOG"] = LOG
NAP = 0.7

_PROBE = ("import os, sys, time, tempfile\n"
          "t0 = time.time(); time.sleep(%s)\n"
          "def _log():\n"
          "    fd, _ = tempfile.mkstemp(dir=os.environ['VPOOL_LOG'])\n"
          "    os.write(fd, ('%%s %%r %%r' %% (os.path.realpath(os.getcwd()),"
          " t0, time.time())).encode()); os.close(fd)\n" % NAP)


def git(d, *a):
    return subprocess.run(["git", "-c", "user.name=vpool",
                           "-c", "user.email=vpool@example.invalid", *a],
                          cwd=d, capture_output=True, text=True, timeout=120)


def plant():
    """A committed repo with one declaration of each verdict."""
    d = tempfile.mkdtemp(prefix="vpool-")
    w = lambda n, s: open(os.path.join(d, n), "w", encoding="utf-8").write(s)
    w("pretend.py", "def answer():\n    return 42\n")
    w("pretend2.py", "def answer():\n    return 42\n")
    decl = "# @vacuity %s\n#   file: %s\n#   find: %s\n#   with: %s\n"
    w("test_a_bites.py", decl % ("bites", "pretend.py", "return 42", "return 43")
      + _PROBE + "import pretend\n_log()\n"
      "sys.exit(0 if pretend.answer() == 42 else 1)\n")
    w("test_b_bites.py", decl % ("bites", "pretend2.py", "return 42", "return 44")
      + _PROBE + "import pretend2\n_log()\n"
      "sys.exit(0 if pretend2.answer() == 42 else 1)\n")
    w("test_c_vacuous.py", decl % ("vacuous", "pretend.py", "return 42", "return 43")
      + _PROBE + "_log()\nsys.exit(0)\n")
    w("test_d_redboth.py", decl % ("red both", "pretend2.py", "return 42", "return 43")
      + _PROBE + "_log()\nsys.exit(1)\n")
    w("test_e_bad.py", decl % ("bad", "pretend.py", "not in the file", "x")
      + "import sys\nsys.exit(0)\n")
    # ── tier 1: name-mapped, one depends on its subject and one does not ──
    w("test_pretend.py", _PROBE + "import pretend\n_log()\n"
      "sys.exit(0 if pretend.answer() == 42 else 1)\n")
    w("test_pretend2.py", _PROBE + "_log()\nsys.exit(0)\n")
    git(d, "init", "-q")
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "plant")
    return d


def runs():
    """-> [(tree, start, end)] logged since the last `clear()`."""
    out = []
    for p in glob.glob(os.path.join(LOG, "*")):
        tree, a, b = open(p, encoding="utf-8").read().rsplit(" ", 2)
        out.append((tree, float(a), float(b)))
    return out


def clear():
    for p in glob.glob(os.path.join(LOG, "*")):
        os.remove(p)


def overlaps(rs):
    return [(x, y) for i, x in enumerate(rs) for y in rs[i + 1:]
            if x[1] < y[2] and y[1] < x[2]]


def leftovers():
    return glob.glob(os.path.join(tempfile.gettempdir(),
                                  "vacuity-sweep-%d-w*" % os.getpid()))


WANT = {"test_a_bites.py": "BITES", "test_b_bites.py": "BITES",
        "test_c_vacuous.py": "VACUOUS", "test_d_redboth.py": "RED_BOTH_WAYS",
        "test_e_bad.py": "MALFORMED"}

# ════════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 THE SWEEP RUNS IN PARALLEL, AND ASKS EVERY QUESTION")
# ════════════════════════════════════════════════════════════════════════
_d = plant()
ck("⚠️ the planted repo is committed and clean",
   V._porcelain(_d) == set(),
   "⛔ a dirty root is swept serially by design, so every parallel check "
   "below would be vacuous (rule 67). porcelain=%r" % V._porcelain(_d))
clear()
_leaks = []
_res = V.tier2(_d, jobs=4, leaks=_leaks)
_got = {r["test"]: r["state"] for r in _res}
_rs = runs()
ck("⚠️ every planted declaration came back",
   list(_got) == sorted(WANT),
   "⛔ a declaration the pool drops is a guard silently skipped. got %s"
   % list(_got))
ck("🔴🔴 every verdict is still the RIGHT one",
   _got == WANT,
   "⛔ running in parallel may change the wall clock and NOTHING else. "
   "got %r" % _got)
ck("⚠️ the planted runs were all logged (%d)" % len(_rs),
   len(_rs) == 7,
   "⛔ BITES 2x2 + VACUOUS 1 + RED_BOTH_WAYS 2 (red, then the green that "
   "stays red) = 7; without them "
   "the overlap checks below read nothing (rule 67). got %d" % len(_rs))
_ov = overlaps(_rs)
ck("🔴🔴 the runs really OVERLAPPED — the sweep is not a serial sum",
   len(_ov) >= 1 and len({r[0] for r in _rs}) >= 2,
   "⛔ THIS IS THE DEFECT: a serial sweep costs the sum of every "
   "declaration and outgrew its 2400s clock. %d overlap(s) across %d "
   "tree(s)" % (len(_ov), len({r[0] for r in _rs})))
ck("⛔🔴 no two overlapping runs ever shared a tree",
   all(x[0] != y[0] for x, y in _ov),
   "🔴 two mutations live in ONE tree at once is how `blind()` was baked "
   "to `return []` on 2026-09-17. clashes: %s"
   % [(x[0], y[0]) for x, y in _ov if x[0] == y[0]][:3])
ck("✅ no worker tree leaked", not _leaks, "leaks: %s" % _leaks)
ck("✅ ...the root is clean again", V._porcelain(_d) == set(),
   "porcelain=%r" % V._porcelain(_d))
_wt = git(_d, "worktree", "list", "--porcelain").stdout
ck("✅ ...and every worker tree was released",
   _wt.count("worktree ") == 1 and not leftovers(),
   "⛔ each is a full checkout; a leak per run fills the disk. "
   "worktrees=%d leftovers=%s" % (_wt.count("worktree "), leftovers()))

clear()
_t1 = {r["test"]: r["state"] for r in V.tier1(_d, jobs=4)}
_rs1 = runs()
ck("🔴 tier 1 through the same pool gives the same verdicts",
   _t1 == {"test_pretend.py": "BITES", "test_pretend2.py": "VACUOUS"},
   "⛔ tier 1 shares the pool, so it shares the hazard. got %r" % _t1)
ck("🔴 ...and its runs overlapped too, in different trees",
   len(_rs1) == 2 and len(overlaps(_rs1)) == 1
   and _rs1[0][0] != _rs1[1][0],
   "⛔ the nightly job runs tier 1 AND tier 2 inside a 30-minute limit. "
   "runs=%s" % [r[0][-24:] for r in _rs1])

# ════════════════════════════════════════════════════════════════════════
section("2. 🔴 A DIRTY ROOT IS SWEPT IN PLACE, NEVER FROM HEAD")
# ════════════════════════════════════════════════════════════════════════
# ⛔ A worktree is HEAD. If `root` has uncommitted edits, HEAD trees would
#    answer about code nobody asked about — so the pool must go serial.
open(os.path.join(_d, "scratch.txt"), "w").write("uncommitted\n")
clear()
_res2 = V.tier2(_d, jobs=4, only={"test_a_bites.py", "test_c_vacuous.py"})
_rs2 = runs()
ck("⚠️ the dirty-root runs were logged (%d)" % len(_rs2), len(_rs2) == 3,
   "⛔ BITES x2 + VACUOUS x1 = 3 (rule 67). got %d" % len(_rs2))
ck("🔴 ...all in the root itself, one at a time",
   {r[0] for r in _rs2} == {os.path.realpath(_d)} and not overlaps(_rs2),
   "⛔ a dirty root swept from HEAD worktrees gives a verdict about "
   "different code. trees=%s overlaps=%d"
   % (sorted({r[0] for r in _rs2}), len(overlaps(_rs2))))
ck("✅ ...with the same verdicts",
   {r["test"]: r["state"] for r in _res2}
   == {"test_a_bites.py": "BITES", "test_c_vacuous.py": "VACUOUS"},
   "got %r" % [(r["test"], r["state"]) for r in _res2])
os.remove(os.path.join(_d, "scratch.txt"))

# ════════════════════════════════════════════════════════════════════════
section("3. ⛔ A WORKER TREE LEFT MODIFIED FAILS CLOSED")
# ════════════════════════════════════════════════════════════════════════
# ⚠️ Three tasks, three trees, each held for a moment: the queue must hand
#    each thread a DIFFERENT tree, so at least two land in worker trees.
def _dirty(task, tree):
    import time
    time.sleep(0.3)
    if os.path.realpath(tree) != os.path.realpath(_d):
        open(os.path.join(tree, "left-behind.txt"), "w").write("x")
    return task


_l3 = []
_out3 = V._pool(_d, 3, [1, 2, 3], _dirty, _l3)
ck("⚠️ the pool returned every task in order", _out3 == [1, 2, 3],
   "got %r" % _out3)
ck("🔴🔴 a worker tree left modified is REPORTED as a leak",
   len(_l3) >= 1 and all("left-behind.txt" in x for x in _l3),
   "⛔ a mutation left in a worker tree is read by every later mutation "
   "in that tree. leaks=%r" % _l3)
try:
    V._pool(_d, 3, [1, 2, 3], _dirty)
    _raised = False
except RuntimeError:
    _raised = True
ck("🔴 ...and with nowhere to report it, it RAISES rather than passes",
   _raised, "⛔ a leak nobody hears is no leak check at all")
ck("✅ ...and even then, nothing is left behind",
   not leftovers()
   and git(_d, "worktree", "list", "--porcelain").stdout.count("worktree ") == 1,
   "leftovers=%s" % leftovers())

# ════════════════════════════════════════════════════════════════════════
section("4. ⚠️ AND THE REAL SWEEP GETS MORE THAN ONE TREE")
# ════════════════════════════════════════════════════════════════════════
ck("🔴 JOBS is more than 1 on any machine with more than one core",
   V.JOBS >= 2 or (os.cpu_count() or 1) < 2,
   "⛔ JOBS=1 is the serial sweep that timed out. cpu=%s JOBS=%s"
   % (os.cpu_count(), V.JOBS))
note("JOBS=%d on this machine (%s cores); GitHub's runner has 4."
     % (V.JOBS, os.cpu_count()))

# ════════════════════════════════════════════════════════════════════════
section("5. 🔴 THE NIGHTLY JOB GETS AT LEAST THE CLOCK A PR GIVES THE SWEEP")
# ════════════════════════════════════════════════════════════════════════
# ⛔ `[2026-09-23]` `vacuity.yml` ran tier 1 AND tier 2 under a 30-minute
#    job limit while pr-tests gave tier 2 ALONE 2400s. It was cancelled on
#    09-22 and 09-23 and reported nothing either night.
# ⚠️ `vacuity.yml` has a cron block, so the fix is uploaded by Sam, never
#    merged. Until he does, a DIFFERENT copy staged in `docs/upload/` is the
#    fix in flight and the deployed file is reported, not failed. Once the
#    two match, the deployed file is held to the bar like any other.
_WF = os.path.join(ROOT, ".github", "workflows")
_m = re.search(r"test_vacuity\.py\)\s*echo (\d+)",
               open(os.path.join(_WF, "pr-tests.yml"), encoding="utf-8").read())
_pr_clock = int(_m.group(1)) if _m else 0
ck("⚠️ the PR clock for test_vacuity.py was read (%ds)" % _pr_clock,
   _pr_clock >= 600,
   "⛔ every comparison below is against this number (rule 67)")


def _job_secs(path):
    m = re.search(r"^\s*timeout-minutes:\s*(\d+)",
                  open(path, encoding="utf-8").read(), re.M)
    return int(m.group(1)) * 60 if m else None


def _text(path):
    return open(path, encoding="utf-8").read().replace("\r\n", "\n")


_dep = os.path.join(_WF, "vacuity.yml")
_stg = os.path.join(ROOT, "docs", "upload", "vacuity.yml")
_pending = os.path.exists(_stg) and _text(_stg) != _text(_dep)
if os.path.exists(_stg):
    ck("🔴 the STAGED vacuity.yml gives the nightly at least %ds" % _pr_clock,
       (_job_secs(_stg) or 0) >= _pr_clock,
       "⛔ this is the file Sam will upload; it has to be right. got %ss"
       % _job_secs(_stg))
if _pending and (_job_secs(_dep) or 0) < _pr_clock:
    note("⚠️ deployed vacuity.yml still allows %ss; the fix is staged in "
         "docs/upload/vacuity.yml and waiting for Sam's upload."
         % _job_secs(_dep))
else:
    ck("🔴🔴 the DEPLOYED nightly gets at least the PR's sweep clock",
       (_job_secs(_dep) or 0) >= _pr_clock,
       "⛔ the nightly runs tier 1 AND tier 2; a job limit below what a PR "
       "gives tier 2 alone is cancelled before it can report. deployed=%ss "
       "pr=%ss" % (_job_secs(_dep), _pr_clock))

shutil.rmtree(_d, ignore_errors=True)
shutil.rmtree(LOG, ignore_errors=True)
