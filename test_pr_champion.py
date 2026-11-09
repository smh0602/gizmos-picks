#!/usr/bin/env python3
r"""🔴🔴 THE SUITE WITH A CHAMPION NAMED, ON EVERY PR. `[2026-11-08]`

#339, college's first champion switch (HC), was a correct one-line branch, and pr-tests went red
on it: test files whose checks were right but assumed no league names a champion
(research/fb_refit_spec.md §3j). That class shows only the day a switch merges.

✅ THE CLASS GUARD: pr-tests' `champion` job names a champion in every league that names none
(`champions_named.py`, through `fb_refit.set_champion`, the weekly job's own edit) and runs the
`tests` job's own loop. This file proves the job is wired and that it BITES: a bench repo holding a
test that leans on "no champion" is green in the `tests` loop and red in this job.

⛔ A TEST ASKS THE CODE: every verdict is on a planted tree or on fb_model.py's text, never on what
main names today (the bench's own fb_model.py names none, whatever main names).

# @vacuity 🔴🔴 the edit is never shadowed by fb_model's stale bytecode (PR #344's first run)
#   file: champions_named.py
#   find:     drop_bytecode(os.getcwd())          # ⛔ never let a stale compiled fb_model shadow the edit
#   with:     pass
#
# @vacuity 🔴 name() really names a champion
#   file: champions_named.py
#   find:             src = fb_refit.set_champion(src, lg, n)
#   with:             pass
#
# @vacuity 🔴🔴 the job really names them before the tests run
#   file: .github/workflows/pr-tests.yml
#   find:           python champions_named.py --yes
#   with:           python --version
#
# @vacuity 🔴🔴 the job really runs the suite on the named tree
#   file: .github/workflows/pr-tests.yml
#   find:           bash -e "$chloop"
#   with:           true
#
# @vacuity ⛔ a league that already names a champion keeps it
#   file: champions_named.py
#   find:         if fb_refit.names_none(src, lg):
#   with:         if True:
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import champions_named as C  # noqa: E402
import fb_challengers as FC  # noqa: E402
import wfparse as W  # noqa: E402
from tcheck import ck, eq, section, shown  # noqa: E402

PR = open(os.path.join(ROOT, ".github", "workflows", "pr-tests.yml"), encoding="utf-8").read()
SRC = open(os.path.join(ROOT, "fb_model.py"), encoding="utf-8").read()
LINE = re.compile(r'(?m)^CHAMPION = \{.*\}$')


def with_line(line):
    out, n = LINE.subn(line, SRC)
    assert n == 1, "the CHAMPION line is not in fb_model.py once"
    return out


def line_of(src):
    return LINE.search(src).group(0)


# ══════════════════════════════════════════════════════════════════════
section("1. THE JOB IS THERE, READ-ONLY, AND RUNS THE tests JOB'S OWN LOOP")
# ══════════════════════════════════════════════════════════════════════
_jobs = {j.name: j for j in W.jobs(PR)}
ck("champion" in _jobs, "pr-tests has a `champion` job", str(sorted(_jobs)))
_steps = {s.name: s for s in W.steps(PR, "champion") if s.name}
NAME = _steps.get("Name a champion in every league (locally, never pushed)")
TESTS = _steps.get("Tests, with a champion named")
TREE = _steps.get("The tests must not have modified the tree")
ck(NAME and TESTS and TREE, "   it has its three steps", str(sorted(_steps)))
ck(not any(s.cond for s in (NAME, TESTS, TREE)), "🔴 ...none behind an `if:`: it runs on every PR")
ck(W.permissions(PR) == {"contents": "read"} and not _jobs["champion"].permissions,
   "   read-only: its local commit can never be pushed")
ck(W.job_env(PR).get("champion", {}).get("SUITE_SHARD") == "rest",
   "   ...as the `rest` shard (its own env, wfparse.job_env)")

# ══════════════════════════════════════════════════════════════════════
section("2. name(): A CHAMPION IN EVERY LEAGUE THAT NAMES NONE, AND NOTHING ELSE")
# ══════════════════════════════════════════════════════════════════════
eq(sorted(C.NAMED), ["ncaaf", "nfl"], "it names one for each league")
ck(all(FC.CHALLENGERS.get(n, {}).get("league") == lg for lg, n in C.NAMED.items()),
   "🔴 each is a registered challenger of its own league (a switch could merge it)", C.NAMED)
_none = with_line('CHAMPION = {"nfl": None, "ncaaf": None}')
_out, _got = C.name(_none)
eq((line_of(_out), _got), ('CHAMPION = {"nfl": "SM", "ncaaf": "HC"}', ["nfl", "ncaaf"]),
   "🔴 from none: NFL SM and college HC")
eq(_out.replace(line_of(_out), ""), _none.replace(line_of(_none), ""), "   ...and nothing but that line changes")
_hc = with_line('CHAMPION = {"nfl": None, "ncaaf": "HC"}')
eq((line_of(C.name(_hc)[0]), C.name(_hc)[1]), ('CHAMPION = {"nfl": "SM", "ncaaf": "HC"}', ["nfl"]),
   "🔴 once college names HC (the switch merged), only the NFL is named")
_both = with_line('CHAMPION = {"nfl": "E", "ncaaf": "P"}')
eq(C.name(_both), (_both, []), "⛔ a league that already names one keeps it; both named: no change")
import fb_refit  # noqa: E402
_named = [lg for lg in C.NAMED if fb_refit.names_none(SRC, lg)]
ck(C.name(SRC)[1] == _named and all(fb_refit.set_champion(SRC, lg, C.NAMED[lg]) for lg in _named),
   "🔴 on main's real fb_model.py, name() names exactly the leagues set_champion can edit (one pattern, rule 117)",
   (_named, C.name(SRC)[1]))
_r = subprocess.run([sys.executable, os.path.join(ROOT, "champions_named.py")], capture_output=True, text=True,
                    cwd=ROOT)
ck(_r.returncode == 2, "⛔ without --yes it refuses, so it can never edit a real tree by accident",
   shown(_r.stdout[-200:]))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 IT CATCHES A TEST THAT ASSUMES NO CHAMPION, WHICH THE tests JOB CANNOT")
# ══════════════════════════════════════════════════════════════════════
PLANT = "import fb_model\nassert fb_model.CHAMPION['ncaaf'] is None, 'assumes no champion'\n"
SAFE = ("import fb_model\n"
        "fb_model.CHAMPION.update(nfl=None, ncaaf=None)   # pins the champion it tests\n"
        "assert fb_model.CHAMPION['ncaaf'] is None\n")


def repo(py):
    d = tempfile.mkdtemp(prefix="champ-repo-")
    os.makedirs(os.path.join(d, ".github", "workflows"))
    shutil.copy(os.path.join(ROOT, ".github", "workflows", "pr-tests.yml"),
                os.path.join(d, ".github", "workflows", "pr-tests.yml"))
    for f in glob.glob(os.path.join(ROOT, "*.py")):
        if not os.path.basename(f).startswith("test_"):
            shutil.copy(f, d)
    shutil.copy(os.path.join(ROOT, ".gitignore"), d)
    with open(os.path.join(d, "fb_model.py"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(with_line('CHAMPION = {"nfl": None, "ncaaf": None}'))     # whatever main names
    for n in "abcd":                       # the loop refuses a suite under 4 files
        open(os.path.join(d, "test_%s.py" % n), "w").write("pass\n")
    open(os.path.join(d, "test_live.py"), "w").write(py)
    for c in (["git", "init", "-q"], ["git", "add", "-A"],
              ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"]):
        subprocess.run(c, cwd=d, check=True, capture_output=True)
    return d


def sh(d, body):
    # ⚠️ from a file, never `bash -c` (test_pr_staged.py: Windows cuts a long -c short)
    sd = tempfile.mkdtemp(prefix="champ-sh-")
    try:
        step = os.path.join(sd, "step.sh")
        open(step, "w", encoding="utf-8", newline="\n").write(body)
        # bytecode ON, as on the runner (a machine may set PYTHONDONTWRITEBYTECODE; this one does), so
        #    the stale-bytecode case `job` sets up is real everywhere
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX")}
        p = subprocess.run(["bash", "-e", step], cwd=d, capture_output=True, text=True, timeout=600,
                           env=dict(env, SUITE_SHARD="rest", GITHUB_OUTPUT=os.devnull))
    finally:
        shutil.rmtree(sd, ignore_errors=True)
    return p.returncode, p.stdout + p.stderr


def job(d):
    """The champion job's three steps on bench `d`. ⚠️ Between naming and the tests, fb_model.py's
    mtime is set back to what it was: the edit then lands in the SAME second as the bytecode compiled
    from the old file (the size is the same too: None -> "SM"), the case that left PR #344's first
    run testing no champion. Deterministic on every OS, however fast the runner is."""
    fm = os.path.join(d, "fb_model.py")
    before = os.stat(fm)
    rc, log = sh(d, NAME.run)
    if rc:
        return rc, None, log
    os.utime(fm, ns=(before.st_atime_ns, before.st_mtime_ns))
    trc, tlog = sh(d, TESTS.run)
    krc, klog = sh(d, TREE.run)
    return trc, krc, log + tlog + klog


LOOP = W.step_run(PR, step_name="Tests", job="tests")
d = repo(PLANT)
try:
    rc_now, _log = sh(d, LOOP)
    ck(rc_now == 0, "the `tests` job's loop is GREEN while no league names a champion (how #339's reds hid)",
       shown(_log[-300:]))
    trc, krc, log = job(d)
    ck(trc != 0 and re.search(r"(?m)^failed=.*\btest_live\.py\b", log),
       "🔴🔴 the `champion` job is RED and its `failed=` line names the test that assumes no champion "
       "(the name every file prints before it runs is not enough)", shown(log[-400:]))
    ck("champions named: nfl SM, ncaaf HC" in log, "   ...after naming NFL SM and college HC", shown(log[:300]))
    ck(krc == 0, "   ...and its local commit left the tree clean", shown(log[-300:]))
finally:
    shutil.rmtree(d, ignore_errors=True)
d = repo(SAFE)
try:
    trc, krc, log = job(d)
    ck(trc == 0 and krc == 0, "✅ a test that pins the champion it tests stays green", shown(log[-400:]))
finally:
    shutil.rmtree(d, ignore_errors=True)
