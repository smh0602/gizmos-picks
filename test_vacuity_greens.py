#!/usr/bin/env python3
"""🔴🔴 A TEST'S GREEN RUN IS RUN ONCE PER SWEEP, AFTER ITS LAST RED RUN, ON A TREE THAT IS HEAD.

`[2026-11-13]` pr-tests' sweep parts used 4,158s and 4,249s of test_vacuity.py's
5,400s clock (79%), and the slowest part grew 500-800 s a week. Measured locally,
the GREEN-on-revert run was ~80% of the sweep's cost on its five costliest files:
the whole file, on the same unmutated tree, once per declaration. `vacuity.py` now
runs each test's green ONCE per sweep, at the end, for every declaration whose tree
was PRISTINE after its revert (`_pristine`: git shows no change, no untracked or
ignored file and no untracked or ignored directory), on a tree pristine then.
`[2026-11-17, the review]` ~~It ran the green after the first red run and reused
it~~: that green was the control for every later red run too, so a test that went
red mid-sweep for an outside reason read BITES; and an EMPTY directory a red run
left behind was invisible to git status (§2b, §5).

⛔ This file is that change's guard, driven on planted repos with known answers:
  · a test with three declarations runs RED three times and GREEN once, AFTER all
    three, and all three BITE;
  · a test red unmutated is RED_BOTH_WAYS for EVERY declaration it carries;
  · two tests never share a green run;
  · a red run that leaves a file behind, even an IGNORED one, or an EMPTY
    directory, is never answered for by a green on another tree: that declaration
    runs its own green and reads the leftover;
  · a dirty root (swept in place) runs every green, as before;
  · `_pristine` fails closed where git cannot answer, an owed green is a finding
    until it has run, and an owed green with no tree to run on is a finding;
  · a test that goes red unmutated mid-sweep is never BITES on a green taken
    before it went red.
This file runs no real sweep, so it carries declarations of its own.

# @vacuity 🔴🔴 a green is only ever owed by a tree that is PRISTINE after its revert
#   file: vacuity.py
#   find:     if defer and _pristine(root):
#   with:     if defer:
#
# @vacuity 🔴 an IGNORED leftover is a change too (`--ignored`)
#   file: vacuity.py
#   find:     for ask in (["git", "status", "--porcelain", "--ignored", "--untracked-files=all"],
#   with:     for ask in (["git", "status", "--porcelain", "--untracked-files=all"],
#
# @vacuity 🔴 an EMPTY directory left behind is a change too (`git clean -ndx`; git status never lists one)
#   file: vacuity.py
#   find:                 ["git", "clean", "-ndx"]):
#   with:                 ["git", "status", "--porcelain"]):
#
# @vacuity ✅ the green run really is run once per test (the headroom itself)
#   file: vacuity.py
#   find:                  lambda d, tree: _tier2_one(d, tree, defer=True), leaks, then=_owed_greens)
#   with:                  lambda d, tree: _tier2_one(d, tree, defer=False), leaks, then=_owed_greens)
#
# @vacuity 🔴🔴 the owed green is RUN, after the last red run: never assumed green
#   file: vacuity.py
#   find:     got = dict(zip(owed, again(_timed_green, owed)))
#   with:     got = {t: (0, 0.0) for t in owed}
#
# @vacuity ⛔ two tests never share one green run
#   file: vacuity.py
#   find:         t, ran = r["test"], got.get(r["test"])
#   with:         t, ran = r["test"], next(iter(got.values()))
#
# @vacuity ⛔ a git that cannot answer is NOT pristine
#   file: vacuity.py
#   find:         if p.returncode != 0:
#   with:         if False:
#
# @vacuity ⛔ a row whose green is still owed is a finding, never a pass
#   file: vacuity.py
#   find:         return {**d, "state": "RED_BOTH_WAYS", "secs": round(time.time() - t0, 1),
#   with:         return {**d, "state": "BITES", "secs": round(time.time() - t0, 1),
#
# @vacuity 🔴 the owed green runs on a tree that is pristine THEN, never on one a red run left changed
#   file: vacuity.py
#   find:         clean = [tr for tr in [root] + extra if _pristine(tr)]
#   with:         clean = [root] + extra
#
# @vacuity ⚠️ ...and on a fresh worktree of HEAD when no tree is
#   file: vacuity.py
#   find:             fresh = _extra_trees(root, 1)
#   with:             fresh = []
#
# @vacuity ⛔ an owed green with no tree to run on is a finding, never a pass
#   file: vacuity.py
#   find:             out.append({**base, "state": "RED_BOTH_WAYS", "secs": r.get("secs"),
#   with:             out.append({**base, "state": "BITES", "secs": r.get("secs"),
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

# ⚠️ Each planted test logs "<test> <red|green> <start> <end>" here, OUTSIDE the
#    planted tree, so the number of green runs and WHEN they ran are READ OFF THE
#    RUNS, never inferred.
LOG = tempfile.mkdtemp(prefix="vgreens-log-")
os.environ["VGREENS_LOG"] = LOG
TREES = []

_PROBE = ("import atexit, os, sys, tempfile, time\n"
          "def _log(name):\n"
          "    fd, path = tempfile.mkstemp(dir=os.environ['VGREENS_LOG'])\n"
          "    os.write(fd, ('%s %s %.6f' % (name, 'red' if os.environ.get('TCHECK_FAIL_FAST') == '1'"
          " else 'green', time.time())).encode()); os.close(fd)\n"
          "    atexit.register(lambda: open(path, 'a').write(' %.6f' % time.time()))\n")
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
    w("subject.py", "A = 1\nB = 2\nC = 3\nMODE = 'a'\nLEAVE = False\nEMPTY = False\nX = 1\n"
      "P = 1\nQ = 1\n")
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
    # `[2026-11-17, the review]` its 2nd mutation leaves an EMPTY directory, which git
    #    status never lists and which turns it red after; its 3rd is VACUOUS (X is never read)
    w("test_hollow.py", _DECL % ("mode", "subject.py", "MODE = 'a'", "MODE = 'y'")
      + _DECL % ("empty", "subject.py", "EMPTY = False", "EMPTY = True")
      + _DECL % ("vacuous", "subject.py", "X = 1", "X = 2")
      + _PROBE + "import subject\n_log('hollow')\n"
      "if os.path.isdir('made'):\n    sys.exit(1)\n"
      "if subject.EMPTY:\n    os.makedirs('made')\n    sys.exit(1)\n"
      "sys.exit(0 if subject.MODE == 'a' else 1)\n")
    # `[2026-11-17, the review]` an outside thing that BREAKS after this test's second
    #    run, for good (a disk that filled, a stale lock): both mutations really bite
    w("test_env.py", _DECL % ("p", "subject.py", "P = 1", "P = 2")
      + _DECL % ("q", "subject.py", "Q = 1", "Q = 2")
      + _PROBE + "import subject\n_log('env')\n"
      "_c = os.path.join(os.environ['VGREENS_LOG'], 'env-count')\n"
      "_n = int(open(_c).read()) if os.path.exists(_c) else 0\n"
      "open(_c, 'w').write(str(_n + 1))\n"
      "if _n >= 2:\n    sys.exit(1)\n"
      "sys.exit(0 if (subject.P, subject.Q) == (1, 1) else 1)\n")
    git(d, "init", "-q")
    if commit:
        git(d, "add", "-A")
        git(d, "commit", "-q", "-m", "plant")
    return d


def runs():
    """-> [(test, red|green, start, end)] logged since the last `clear()`."""
    out = []
    for p in glob.glob(os.path.join(LOG, "*")):
        if os.path.basename(p) == "env-count":
            continue
        f = open(p, encoding="utf-8").read().split()
        out.append((f[0], f[1], float(f[2]), float(f[3]) if len(f) > 3 else None))
    return out


def clear():
    for p in glob.glob(os.path.join(LOG, "*")):
        os.remove(p)


def count(rs, test, kind):
    return sum(1 for r in rs if r[:2] == (test, kind))


def worktrees(d):
    return git(d, "worktree", "list", "--porcelain").stdout.count("worktree ")


# ════════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 THREE DECLARATIONS, THREE RED RUNS, ONE GREEN RUN AFTER THEM, ALL BITE")
# ════════════════════════════════════════════════════════════════════════
_d = plant()
ck("⚠️ the planted repo is committed and PRISTINE", V._pristine(_d),
   "⛔ on a tree that is not pristine no green is owed, so every check below "
   "would be vacuous (rule 67). porcelain=%r" % V._porcelain(_d))
clear()
_leaks = []
_res = V.tier2(_d, jobs=4, leaks=_leaks, only={"test_many.py", "test_redboth.py"})
_rs = runs()
_by = {}
for _r in _res:
    _by.setdefault(_r["test"], []).append(_r)
eq([r["state"] for r in _by.get("test_many.py", [])], ["BITES"] * 3,
   "🔴🔴 every declaration of the test still BITES")
eq((count(_rs, "many", "red"), count(_rs, "many", "green")), (3, 1),
   "🔴🔴 three red runs and ONE green run for three declarations (the headroom)")
_reds = [r for r in _rs if r[:2] == ("many", "red")]
_greens = [r for r in _rs if r[:2] == ("many", "green")]
ck("🔴🔴 ...and that green STARTED after every one of its red runs had ENDED: it is the control "
   "for all three",
   len(_greens) == 1 and _reds and all(r[3] is not None for r in _reds)
   and _greens[0][2] > max(r[3] for r in _reds),
   "⛔ a green taken before a red run cannot say that red run was the mutation's doing "
   "(the review, 2026-11-17). reds=%r greens=%r" % (_reds, _greens))
eq([r.get("green_shared") for r in _by.get("test_many.py", [])], [3, 3, 3],
   "   ...and each row says one green answered for its test's three declarations")
eq([r["state"] for r in _by.get("test_redboth.py", [])], ["RED_BOTH_WAYS"] * 3,
   "🔴🔴 a test red unmutated is RED_BOTH_WAYS for EVERY declaration")
eq(count(_rs, "redboth", "green"), 1,
   "   ...and it too ran its green once: a shared RED is still red")
ck("⛔ two tests never shared a green run (each ran its own)",
   count(_rs, "many", "green") == 1 and count(_rs, "redboth", "green") == 1
   and [r["state"] for r in _by.get("test_many.py", [])] == ["BITES"] * 3
   and [r["state"] for r in _by.get("test_redboth.py", [])] == ["RED_BOTH_WAYS"] * 3,
   "🔴 a green shared across tests hands one test's verdict to another: a red test "
   "reads BITES, or a good one RED_BOTH_WAYS. runs=%r" % sorted(_rs))
ck("⚠️ no row is left owing its green", not any(r.get("green_owed") for r in _res),
   [r["why_declared"] for r in _res if r.get("green_owed")])
ck("✅ no worker tree leaked, and the root is pristine again",
   not _leaks and V._pristine(_d), "leaks=%r porcelain=%r" % (_leaks, V._porcelain(_d)))

# ════════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 A RED RUN THAT LEFT SOMETHING BEHIND RUNS ITS OWN GREEN — AN IGNORED FILE, AN EMPTY DIRECTORY")
# ════════════════════════════════════════════════════════════════════════
# ⚠️ Serial (jobs=1), so the order is the file's: `mode` first (red, revert,
#    pristine: its green is owed to the end), then `leave`, whose red run writes
#    `made.cache` (git-IGNORED) into the tree. That tree is NOT HEAD: the test now
#    reads red unmutated there, and only a green run in it can say so. A green on
#    another tree would call it BITES.
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
ck("⚠️ ...`mode` BITES on a root left changed, so its owed green ran on a fresh tree of HEAD, released after",
   worktrees(_d) == 1, "worktrees=%d" % worktrees(_d))
os.remove(os.path.join(_d, "made.cache"))

# ── 2b. `[2026-11-17, the review]` an EMPTY directory: git status never lists one ──
# `empty`'s red run makes `made/` and dies; `vacuous` changes X, which the test never
# reads, so its red run is red ONLY because of `made/`. Each must run its own green
# there and read RED_BOTH_WAYS; a green answered on a tree without `made/` reads BITES
# for a vacuous guard, the failure this harness exists to catch.
clear()
_res2b = V.tier2(_d, jobs=1, only={"test_hollow.py"})
_made = os.path.join(_d, "made")
eq([(r["why_declared"], r["state"]) for r in _res2b],
   [("mode", "BITES"), ("empty", "RED_BOTH_WAYS"), ("vacuous", "RED_BOTH_WAYS")],
   "🔴🔴 the vacuous guard after an empty directory is RED_BOTH_WAYS, never BITES")
_st = git(_d, "status", "--porcelain", "--ignored", "--untracked-files=all").stdout
ck("⚠️ ...and the leftover really was an EMPTY directory git status cannot see",
   os.path.isdir(_made) and not os.listdir(_made) and _st.strip() == "" and not V._pristine(_d),
   "⛔ a planted leftover git status shows would not test `git clean` (rule 67). "
   "isdir=%s status=%r pristine=%s" % (os.path.isdir(_made), _st, V._pristine(_d)))
if os.path.isdir(_made):
    os.rmdir(_made)
ck("   ...and once it is gone the tree is pristine again", V._pristine(_d), V._porcelain(_d))

# ════════════════════════════════════════════════════════════════════════
section("3. 🔴 A DIRTY ROOT IS SWEPT IN PLACE AND RUNS EVERY GREEN, AS BEFORE")
# ════════════════════════════════════════════════════════════════════════
_u = plant(commit=False)
clear()
_res3 = V.tier2(_u, jobs=4, only={"test_many.py"})
_rs3 = runs()
eq([r["state"] for r in _res3], ["BITES"] * 3, "   the uncommitted repo's verdicts are unchanged")
eq(count(_rs3, "many", "green"), 3,
   "🔴 three declarations on a tree that is not HEAD ran three green runs: nothing shared")
ck("   ...and no row claims a shared green", not any(r.get("green_shared") for r in _res3),
   "rows=%r" % [(r["why_declared"], r.get("green_shared")) for r in _res3])

# ════════════════════════════════════════════════════════════════════════
section("4. ⛔ FAIL CLOSED: NO GIT, A GREEN STILL OWED, NO TREE TO RUN IT ON")
# ════════════════════════════════════════════════════════════════════════
_nogit = tempfile.mkdtemp(prefix="vgreens-nogit-")
TREES.append(_nogit)
open(os.path.join(_nogit, "x.py"), "w").write("x = 1\n")
ck("⛔ a folder git cannot answer about is NOT pristine", not V._pristine(_nogit),
   "🔴 a tree nobody can vouch for must run its own green")
_decl = [x for x in V.declarations(_d) if x["test"] == "test_many.py"][0]
clear()
_owed = V._tier2_one(_decl, _d, defer=True)
eq((_owed["state"], _owed.get("green_owed"), count(runs(), "many", "green")), ("RED_BOTH_WAYS", True, 0),
   "⛔ a declaration whose green is owed is RED_BOTH_WAYS until it runs, and no green ran for it here")
eq(V.verdict([_owed], True), V.EXIT_VACUOUS,
   "🔴 ...so a sweep that never ran it is a finding, never a pass")
_none = V._owed_greens([_owed], lambda fn, items: [None] * len(items))
eq([(r["state"], "green_owed" in r) for r in _none], [("RED_BOTH_WAYS", False)],
   "⛔ an owed green with no tree that is exactly HEAD to run on is RED_BOTH_WAYS")
ck("   ...and says why", "no tree that is exactly HEAD" in _none[0]["why"], _none[0]["why"])
ck("   ...and the planted root is pristine after all of it", V._pristine(_d), V._porcelain(_d))

# ════════════════════════════════════════════════════════════════════════
section("5. 🔴🔴 A TEST THAT GOES RED UNMUTATED MID-SWEEP IS NEVER BITES ON A GREEN TAKEN BEFORE")
# ════════════════════════════════════════════════════════════════════════
# `[2026-11-17, the review]` The first version ran `test_env.py`'s green after `p`'s
# red run (its 2nd run, still fine) and reused that 0 for `q`, whose red run came
# after the break: `q` read BITES and the sweep stayed green on a broken environment.
# The harness before it read `q` RED_BOTH_WAYS. Serial, so the runs are numbered.
clear()
_res5 = V.tier2(_d, jobs=1, only={"test_env.py"})
_s5 = {r["why_declared"]: r["state"] for r in _res5}
ck("🔴🔴 the declaration whose red run came after the break is not BITES",
   _s5.get("q") not in (None, "BITES"), "states=%r" % _s5)
eq(V.verdict(_res5, True), V.EXIT_VACUOUS,
   "🔴🔴 ...and the sweep is a finding: a broken environment is never a green sweep")
eq((count(runs(), "env", "red"), count(runs(), "env", "green")), (2, 1),
   "⚠️ the drive ran both red runs, then one green (rule 67: a drive that broke nothing proves nothing)")

note("⛔ WHAT THIS DOES NOT CLAIM: that a test is deterministic, or that an outside reason "
     "that came AND WENT between a red run and the end of the sweep is seen. One that is "
     "still there at the end is seen (§5); before, the green right after each red run saw "
     "one only if it was still there then.")

for _t in TREES:
    shutil.rmtree(_t, ignore_errors=True)
shutil.rmtree(LOG, ignore_errors=True)
