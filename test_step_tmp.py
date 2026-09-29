#!/usr/bin/env python3
"""A WORKFLOW STEP THAT A TEST RUNS MUST NOT WRITE A FIXED TEMP PATH.

🔴 WHAT HAPPENED `[2026-09-28]`. test_pr_staged.py drives pr-tests.yml's
`staged` job, whose two steps wrote `/tmp/staged.txt` and `/tmp/loop.sh`.
Two copies on one machine (two suites, or the vacuity sweep's parallel
worker trees) overwrote each other and a correct case failed; alone it
passed. The same shape sat in three more steps a test runs: self-repair's
`decide` (its "403" reached the log only through `/tmp/ghqueue.err`, and a
second copy emptied it; replayed), its record step, and collect's converge
step (`/tmp/vc.txt`). ⚠️ The sweep gives every run its own TMPDIR; an
absolute /tmp path walks straight past it. On a runner each job has its
own machine, which is why this only ever shows when a TEST runs the step.

✅ THE CLASS, NOT THE INSTANCE: every step, in every workflow as it will be
live (`wfparse.effective_workflows`: a staged copy wins), whose `name:` or
`id:` a test that starts bash quotes exactly. A write is a redirect
(`>`, `>>`, `2>`, `&>`), a `tee`, or a Python `open(..., 'w')`, into a
FIXED name under a shared temp dir: `/tmp`, `$TMPDIR`, `$TEMP`, `$TMP` or
`$RUNNER_TEMP` (unset when a test drives a step, so it falls through to
the shared dir), spelled directly or through a variable assigned that
fixed path. `mktemp` is the fix: a name no other copy can hold.
test_pr_staged.py section 5 replays the original collision itself.

⚠️ WHAT THIS CANNOT SEE: a test that picks its step by BODY TEXT rather
than by name or id (test_budget_watch.py, test_cfbd_watch.py and
test_runs_report.py select the three-state watchers' "Tell Sam" steps on
`gh issue create`; test_card_revert.py and test_test_harness.py run a
block inside a step). None of those writes a fixed temp path today: their
/tmp paths are `--body-file` arguments, which only read.

# @vacuity 🔴 a new fixed /tmp write in a driven step is caught
#   file: .github/workflows/pr-tests.yml
#   find: echo "applied $n staged upload(s):"; cat "$staged"
#   with: echo "applied $n staged upload(s):"; tee /tmp/staged.log < "$staged"
#
# @vacuity 🔴 ...and a fixed path reached through a variable, in a STAGED copy
#   file: docs/upload/self-repair.yml
#   find: GHERR=$(mktemp "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/gh.XXXXXX")
#   with: GHERR="${RUNNER_TEMP:-/tmp}/ghqueue.err"
"""
import ast
import glob
import os
import re
import shutil
import tempfile
import warnings

import wfparse as W
from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))

# A fixed name under a shared temp dir. ⚠️ The name must END in literal
# characters: `/tmp/x.$$` (the process id) and `/tmp/$f` are not fixed.
_DIRS = r"(?:/tmp|\$(?:TMPDIR|TEMP|TMP|RUNNER_TEMP)\b|\$\{(?:TMPDIR|TEMP|TMP|RUNNER_TEMP)\b[^}]*\}+)"
_TARGET = r"[\"']?(" + _DIRS + r"/[\w.\-]+(?:/[\w.\-]+)*)(?![\w.\-$])"
_OP = r"(?:(?<![<\w])(?:\d|&)?>>?\|?\s*|\btee\b(?:\s+(?:-a|--append))?\s+)"
WRITE = re.compile(_OP + _TARGET)
PYOPEN = re.compile(r"open\(\s*[\"'](/tmp/[\w.\-/]+)[\"']\s*,\s*[\"'][wax]")
ASSIGN = re.compile(r"(?:^|[\s;&|(])([A-Za-z_]\w*)=" + _TARGET, re.M)
VARWRITE = re.compile(_OP + r"[\"']?\$\{?([A-Za-z_]\w*)\}?")


def _consts(path):
    """-> (every string constant in the file, does it start bash)."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(open(path, encoding="utf-8").read())
    except (OSError, SyntaxError, ValueError):
        return set(), False
    consts = {n.value for n in ast.walk(tree)
              if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    bash = any(isinstance(n, (ast.List, ast.Tuple)) and n.elts
               and isinstance(n.elts[0], ast.Constant) and n.elts[0].value == "bash"
               for n in ast.walk(tree))
    return consts, bash


def drivers(root):
    """{test file: its string constants} for every test that starts bash."""
    out = {}
    for p in sorted(glob.glob(os.path.join(root, "test_*.py"))):
        consts, bash = _consts(p)
        if bash:
            out[os.path.basename(p)] = consts
    return out


def fixed_writes(run):
    """Every fixed temp path a step body writes. Comment lines are skipped."""
    live = "\n".join(l for l in (run or "").splitlines()
                     if not l.lstrip().startswith("#"))
    found = set(WRITE.findall(live)) | set(PYOPEN.findall(live))
    fixed_vars = {}
    for name, path in ASSIGN.findall(live):
        fixed_vars.setdefault(name, path)
    for name in VARWRITE.findall(live):
        if name in fixed_vars:
            found.add("$%s=%s" % (name, fixed_vars[name]))
    return sorted(found)


def scan(root):
    """-> (driven [(wf, job, name, id, [drivers])],
           findings [(wf, step, paths, [drivers])])"""
    drv = drivers(root)
    driven, bad = [], []
    for f, p in sorted(W.effective_workflows(root).items()):
        for j in W.jobs(p):
            for s in W.steps(p, j.name):
                if not s.run:
                    continue
                by = sorted(t for t, c in drv.items()
                            if (s.name and s.name in c) or (s.id and s.id in c))
                if not by:
                    continue
                driven.append((f, j.name, s.name, s.id, by))
                w = fixed_writes(s.run)
                if w:
                    bad.append((f, s.name or s.id, w, by))
    return driven, bad


# ══════════════════════════════════════════════════════════════════════
section("1. THE SCANNER, ON A PLANTED TREE (every case, every run)")
# ══════════════════════════════════════════════════════════════════════
t = tempfile.mkdtemp(prefix="steptmp-")
try:
    os.makedirs(os.path.join(t, ".github", "workflows"))
    os.makedirs(os.path.join(t, "docs", "upload"))
    open(os.path.join(t, ".github", "workflows", "w.yml"), "w").write(
        "on: push\njobs:\n  j:\n    runs-on: x\n    steps:\n"
        "      - name: Shared\n        run: |\n"
        "          # a comment is not a write > /tmp/in-a-comment.txt\n"
        "          echo hi > /tmp/shared.txt\n          cat /tmp/shared.txt\n"
        "      - name: Errors\n        id: errs\n        run: |\n"
        "          x 2>/tmp/err.txt\n"
        "      - name: Spellings\n        run: |\n"
        "          echo a >> \"$TMPDIR/app.log\"\n"
        "          echo b | tee -a \"${RUNNER_TEMP:-/tmp}/t.txt\"\n"
        "          python -c \"open('/tmp/p.txt', 'w').write('x')\"\n"
        "      - name: Through a variable\n        run: |\n"
        "          f=/tmp/v.txt\n          echo hi > \"$f\"\n"
        "      - name: Own\n        id: own\n        run: |\n"
        "          f=$(mktemp \"${RUNNER_TEMP:-${TMPDIR:-/tmp}}/x.XXXXXX\")\n"
        "          echo hi > \"$f\"; echo pid > /tmp/run.$$\n"
        "          gh issue create --body-file /tmp/body.md; cat < /tmp/in.txt\n"
        "          RESULT=\"$RUNNER_TEMP/out.json\"; python r.py \"$RESULT\"\n"
        "      - name: Nobody runs me\n        run: |\n          echo hi > /tmp/unrun.txt\n")
    # ⚠️ a STAGED copy wins: the live one above has the fixed write in
    #    `Staged fix`, the staged one does not.
    for sub, body in ((".github/workflows", "echo hi > /tmp/old.txt"),
                      ("docs/upload", "o=$(mktemp); echo hi > \"$o\"")):
        open(os.path.join(t, sub, "v.yml"), "w").write(
            "on: push\njobs:\n  j:\n    runs-on: x\n    steps:\n"
            "      - name: Staged fix\n        run: |\n          %s\n" % body)
    open(os.path.join(t, "test_drive.py"), "w").write(
        "import subprocess\n"
        "S = ['Shared', 'errs', 'Spellings', 'Through a variable', 'own', 'Staged fix']\n"
        "subprocess.run(['bash', 'step.sh'])\n")
    open(os.path.join(t, "test_reads.py"), "w").write(
        "S = ['Nobody runs me']\n")          # quotes it, never starts bash
    _d, _b = scan(t)
    eq(sorted(n or i for _f, _j, n, i, _by in _d),
       ["Errors", "Own", "Shared", "Spellings", "Staged fix", "Through a variable"],
       "a step is driven when a test that starts bash names it (name or id); "
       "one a test only quotes is not")
    eq(sorted((s, w) for _f, s, w, _by in _b),
       [("Errors", ["/tmp/err.txt"]), ("Shared", ["/tmp/shared.txt"]),
        ("Spellings", ["$TMPDIR/app.log", "${RUNNER_TEMP:-/tmp}/t.txt", "/tmp/p.txt"]),
        ("Through a variable", ["$f=/tmp/v.txt"])],
       "🔴 every spelling of a fixed temp write is found; a mktemp file, a "
       "per-process name, a comment, a read and a fixed path never written "
       "are not; the staged copy is the one read")
finally:
    shutil.rmtree(t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 NO STEP A TEST RUNS WRITES A FIXED TEMP PATH")
# ══════════════════════════════════════════════════════════════════════
DRIVEN, BAD = scan(ROOT)
_ids = {(f, i) for f, _j, _n, i, _by in DRIVEN if i}
_names = {(f, n) for f, _j, n, _i, _by in DRIVEN if n}
_known = {("pr-tests.yml", "apply"), ("self-repair.yml", "decide"),
          ("collect.yml", "collect"), ("collect.yml", "watchdog")}
ck(_known <= _ids
   and ("pr-tests.yml", "Tests, as they will run after the upload") in _names
   and len(DRIVEN) >= 10,
   "⚠️ the driven set holds the steps known to be driven (rule 67)",
   "%d driven; missing %s" % (len(DRIVEN), sorted(_known - _ids)))
ck(not BAD, "🔴🔴 every driven step writes only a file of its own",
   "\n".join("       %s :: %s writes %s (driven by %s)" % (f, s, w, ", ".join(by))
             for f, s, w, by in BAD))
note("%d driven step(s) scanned across %d workflow(s), staged copies winning"
     % (len(DRIVEN), len({f for f, _j, _n, _i, _b in DRIVEN})))
