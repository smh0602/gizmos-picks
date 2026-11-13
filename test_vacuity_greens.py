#!/usr/bin/env python3
"""🔴🔴 A TEST'S GREEN RUN IS RUN ONCE PER SWEEP — AND ONLY REUSED ON THE TREE IT SAW.

`[2026-11-13]` pr-tests' sweep parts used 4,158s and 4,249s of test_vacuity.py's
5,400s clock (79%), and the slowest part grew 500-800 s a week. Measured locally,
the GREEN-on-revert run was ~80% of the sweep's cost on its five costliest files:
the whole file, on the same unmutated tree, once per declaration. `vacuity.py` now
runs each test's green once per sweep and reuses it (`_Greens`), but only when the
tree is PRISTINE after the revert (`_pristine`: git lists no change, no untracked
and no ignored file).

⛔ This file is that change's guard, driven on planted repos with known answers:
  · a test with three declarations runs RED three times and GREEN once, and all
    three BITE (two of them on the reused green);
  · a test red unmutated is RED_BOTH_WAYS for EVERY declaration it carries;
  · two tests never share a green run;
  · a red run that leaves a file behind, even an IGNORED one, is not reused over:
    the next declaration runs its own green and reads the leftover;
  · a dirty root (swept in place) runs every green, as before;
  · `_pristine` fails closed where git cannot answer;
  · a green run that raised is not handed to the trees waiting on it.
This file runs no real sweep, so it carries declarations of its own.

# @vacuity 🔴🔴 a reused green is only ever reused on a PRISTINE tree
#   file: vacuity.py
#   find:     if greens is not None and _pristine(root):
#   with:     if greens is not None:
#
# @vacuity 🔴 an IGNORED leftover is a change too (`--ignored`)
#   file: vacuity.py
#   find:         p = subprocess.run(["git", "status", "--porcelain", "--ignored",
#   with:         p = subprocess.run(["git", "status", "--porcelain",
#
# @vacuity ✅ the green run really is run once per test (the headroom itself)
#   file: vacuity.py
#   find:     greens = _Greens()
#   with:     greens = None
#
# @vacuity ⛔ two tests never share one green run
#   file: vacuity.py
#   find:         green, reused = greens.get(t, _green_run)
#   with:         green, reused = greens.get("", _green_run)
#
# @vacuity ⛔ a git that cannot answer is NOT pristine
#   file: vacuity.py
#   find:     if p.returncode != 0:
#   with:     if False:
#
# @vacuity ⚠️ a green run that raised is not handed to the trees waiting on it
#   file: vacuity.py
#   find:         if not box:
#   with:         if False:
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import vacuity as V  # noqa: E402

# ⚠️ Each planted test logs "<test> <red|green>" here, OUTSIDE the planted tree,
#    so the number of green runs is READ OFF THE RUNS, never inferred.
LOG = tempfile.mkdtemp(prefix="vgreens-log-")
os.environ["VGREENS_LOG"] = LOG
TREES = []

_PROBE = ("import os, sys, tempfile\n"
          "def _log(name):\n"
          "    fd, _ = tempfile.mkstemp(dir=os.environ['VGREENS_LOG'])\n"
          "    os.write(fd, ('%s %s' % (name, 'red' if os.environ.get('TCHECK_FAIL_FAST') == '1'"
          " else 'green')).encode()); os.close(fd)\n")
_DECL = "# @vacuity %s\n#   file: %s\n#   find: %s\n#   with: %s\n"


def git(d, *a):
    return subprocess.run(["git", "-c", "user.name=vgreens",
                           "-c", "user.email=vgreens@example.invalid", *a],
                          cwd=d, capture_output=True, text=True, timeout=120)


def plant(commit=True):
    """A repo with known answers. `commit=False` leaves it uncommitted (dirty)."""
    d = tempfile.mkdtemp(prefix="vgreens-")
    TREES.append(d)
    w = lambda n, s: open(os.path.join(d, n), "w", encoding="utf-8").write(s)
    w("subject.py", "A = 1\nB = 2\nC = 3\nMODE = 'a'\nLEAVE = False\n")
    w(".gitignore", "*.cache\n")
    # three declarations, one test: every one must BITE, with ONE green run
    w("test_many.py", "".join(_DECL % (w_, "subject.py", f, r) for w_, f, r in (
        ("a", "A = 1", "A = 9"), ("b", "B = 2", "B = 9"), ("c", "C = 3", "C = 9")))
      + _PROBE + "import subject\n_log('many')\n"
      "sys.exit(0 if (subject.A, subject.B, subject.C) == (1, 2, 3) else 1)\n")
    # red whatever it is given: every declaration must read RED_BOTH_WAYS
    w("test_redboth.py", "".join(_DECL % (w_, "subject.py", f, r) for w_, f, r in (
        ("a", "A = 1", "A = 8"), ("b", "B = 2", "B = 8"), ("c", "C = 3", "C = 8")))
      + _PROBE + "_log('redboth')\nsys.exit(1)\n")
    # its 2nd mutation leaves an IGNORED file in the tree, which turns it red after
    w("test_leaves.py", _DECL % ("mode", "subject.py", "MODE = 'a'", "MODE = 'x'")
      + _DECL % ("leave", "subject.py", "LEAVE = False", "LEAVE = True")
      + _PROBE + "import subject\n_log('leaves')\n"
      "if os.path.exists('made.cache'):\n    sys.exit(1)\n"
      "if subject.LEAVE:\n    open('made.cache', 'w').write('left behind')\n    sys.exit(1)\n"
      "sys.exit(0 if subject.MODE == 'a' else 1)\n")
    git(d, "init", "-q")
    if commit:
        git(d, "add", "-A")
        git(d, "commit", "-q", "-m", "plant")
    return d


def runs():
    """-> [(test, red|green)] logged since the last `clear()`."""
    return [tuple(open(p, encoding="utf-8").read().split()) for p in glob.glob(os.path.join(LOG, "*"))]


def clear():
    for p in glob.glob(os.path.join(LOG, "*")):
        os.remove(p)


def count(rs, test, kind):
    return sum(1 for r in rs if r == (test, kind))


# ════════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 THREE DECLARATIONS, THREE RED RUNS, ONE GREEN RUN, ALL BITE")
# ════════════════════════════════════════════════════════════════════════
_d = plant()
ck("⚠️ the planted repo is committed and PRISTINE", V._pristine(_d),
   "⛔ on a tree that is not pristine nothing is reused, so every check below "
   "would be vacuous (rule 67). porcelain=%r" % V._porcelain(_d))
clear()
_leaks = []
_res = V.tier2(_d, jobs=4, leaks=_leaks, only={"test_many.py", "test_redboth.py"})
_rs = runs()
_by = {}
for _r in _res:
    _by.setdefault(_r["test"], []).append(_r)
eq([r["state"] for r in _by.get("test_many.py", [])], ["BITES"] * 3,
   "🔴🔴 every declaration of the reused test still BITES")
eq((count(_rs, "many", "red"), count(_rs, "many", "green")), (3, 1),
   "🔴🔴 three red runs and ONE green run for three declarations (the headroom)")
eq(sorted(bool(r.get("green_reused")) for r in _by.get("test_many.py", [])), [False, True, True],
   "   ...one declaration ran the green, two reused it, and each row says which")
eq([r["state"] for r in _by.get("test_redboth.py", [])], ["RED_BOTH_WAYS"] * 3,
   "🔴🔴 a test red unmutated is RED_BOTH_WAYS for EVERY declaration, reused or not")
eq(count(_rs, "redboth", "green"), 1,
   "   ...and it too ran its green once: a reused RED is still red")
ck("⛔ two tests never shared a green run (each ran its own)",
   count(_rs, "many", "green") == 1 and count(_rs, "redboth", "green") == 1
   and [r["state"] for r in _by.get("test_many.py", [])] == ["BITES"] * 3
   and [r["state"] for r in _by.get("test_redboth.py", [])] == ["RED_BOTH_WAYS"] * 3,
   "🔴 a green shared across tests hands one test's verdict to another: a red test "
   "reads BITES, or a good one RED_BOTH_WAYS. runs=%r" % sorted(_rs))
ck("✅ no worker tree leaked, and the root is pristine again",
   not _leaks and V._pristine(_d), "leaks=%r porcelain=%r" % (_leaks, V._porcelain(_d)))

# ════════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 A RED RUN THAT LEFT A FILE BEHIND IS NEVER REUSED OVER — EVEN AN IGNORED ONE")
# ════════════════════════════════════════════════════════════════════════
# ⚠️ Serial (jobs=1), so the order is the file's: `mode` first (red, revert,
#    pristine: its green runs and is kept), then `leave`, whose red run writes
#    `made.cache` (git-IGNORED) into the tree. That tree is NOT the tree the kept
#    green saw: the test now reads red unmutated there, and only a green run of
#    its own can say so. Reusing the kept 0 would call it BITES.
clear()
_res2 = V.tier2(_d, jobs=1, only={"test_leaves.py"})
_rs2 = runs()
eq([(r["why_declared"], r["state"]) for r in _res2], [("mode", "BITES"), ("leave", "RED_BOTH_WAYS")],
   "🔴🔴 the declaration after the leftover reads the tree it was given: RED_BOTH_WAYS")
eq(count(_rs2, "leaves", "green"), 2,
   "   ...because it ran a green of its own: the leftover tree was not pristine")
ck("⚠️ ...and the leftover really was an IGNORED file, invisible to the leak check",
   os.path.exists(os.path.join(_d, "made.cache")) and V._porcelain(_d) == set()
   and not V._pristine(_d),
   "⛔ without `--ignored` the pristine check is the leak check, and this case is "
   "the one it cannot see. porcelain=%r" % V._porcelain(_d))
os.remove(os.path.join(_d, "made.cache"))

# ════════════════════════════════════════════════════════════════════════
section("3. 🔴 A DIRTY ROOT IS SWEPT IN PLACE AND RUNS EVERY GREEN, AS BEFORE")
# ════════════════════════════════════════════════════════════════════════
_u = plant(commit=False)
clear()
_res3 = V.tier2(_u, jobs=4, only={"test_many.py"})
_rs3 = runs()
eq([r["state"] for r in _res3], ["BITES"] * 3, "   the uncommitted repo's verdicts are unchanged")
eq(count(_rs3, "many", "green"), 3,
   "🔴 three declarations on a tree that is not HEAD ran three green runs: nothing reused")
ck("   ...and no row claims a reused green", not any(r.get("green_reused") for r in _res3),
   "rows=%r" % [(r["why_declared"], r.get("green_reused")) for r in _res3])

# ════════════════════════════════════════════════════════════════════════
section("4. ⛔ `_pristine` FAILS CLOSED, AND A GREEN THAT RAISED IS NOT HANDED ON")
# ════════════════════════════════════════════════════════════════════════
_nogit = tempfile.mkdtemp(prefix="vgreens-nogit-")
TREES.append(_nogit)
open(os.path.join(_nogit, "x.py"), "w").write("x = 1\n")
ck("⛔ a folder git cannot answer about is NOT pristine", not V._pristine(_nogit),
   "🔴 a tree nobody can vouch for must run its own green")
_g = V._Greens()


def _boom():
    raise RuntimeError("the green run could not start")


try:
    _g.get("test_x.py", _boom)
    _raised = False
except RuntimeError:
    _raised = True
ck("   the run that owns a test's green passes its error up", _raised)
try:
    _again = _g.get("test_x.py", lambda: 0)
except Exception as _e:  # noqa: BLE001 - the failure under test
    _again = repr(_e)
eq(_again, (0, False),
   "⚠️ the next tree asking for that test runs its own green, never a result that does not exist")
eq(V._Greens().get("t", lambda: 5), (5, False), "   a first ask runs the green and says it was not reused")

note("⛔ WHAT THIS DOES NOT CLAIM: that a test is deterministic. A test whose result "
     "changes between runs of the same tree was sampled once per declaration before "
     "and is sampled once per sweep now; the harness never claimed to measure that.")

for _t in TREES:
    shutil.rmtree(_t, ignore_errors=True)
shutil.rmtree(LOG, ignore_errors=True)
