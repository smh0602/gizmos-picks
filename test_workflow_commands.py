#!/usr/bin/env python3
"""NO TEST MAY PUT A WORKFLOW COMMAND ON THE RUN BY ACCIDENT.

🔴 WHAT HAPPENED `[2026-09-26]`. GitHub reads every line a step prints,
and a line starting `::error::` (after any indentation) becomes an ERROR
annotation on the run. Every collect run, the green ones included (#1852),
carried two "test_live.py FAILED" errors: `test_pr_staged.py` drives the
pr-tests loop against a planted failing `test_live.py` and printed the
captured log in a check's detail. After #184 there were four: the same
shape in `test_self_repair.py`, and converge's own `::error::` printed
in-process by `test_freshness.py`. An annotation that is false on every
run is one nobody reads, and the day it is true it is read by nobody.

✅ THE CLASS GUARD LIVES IN `tcheck.py`, where every test file already is:
every line a test process writes to stdout or stderr is watched, a
command line is written DEFUSED (`: :`) so it cannot reach the run, and
the gate FAILS the file naming it. `tcheck.annotate()` is the one way to
annotate on purpose. This file drives that guard through every way a
planted `::error::` can be written, and statically closes the one path it
cannot see: a child process writing to the descriptor it inherited.

# @vacuity a planted command must be written DEFUSED, never as a command
#   file: tcheck.py
#   find:         return text[:i] + ": :" + text[i + 2:]
#   with:         return text
#
# @vacuity a file that printed a command must FAIL, not only defuse it
#   file: tcheck.py
#   find:         if LEAKS:
#   with:         if False:
#
# @vacuity the watcher must be on from import, in every test process
#   file: tcheck.py
#   find: _watch()   # every test process, from the moment it imports tcheck
#   with: pass
#
# @vacuity indentation must not hide a command (the runner trims it)
#   file: tcheck.py
#   find:     s = str(line).lstrip()
#   with:     s = str(line)
#
# @vacuity a deliberate annotation must not be counted as a leak
#   file: tcheck.py
#   find:         out.raw(line)
#   with:         out.write(line)
#
# @vacuity the harness's own lines are defused, so a shown detail never fails a file
#   file: tcheck.py
#   find:     print("\n".join(_defuse_start(ln) for ln in str(text).split("\n")))
#   with:     print(text)
#
# @vacuity a child that writes to the inherited stdout is caught statically
#   file: test_self_repair.py
#   find:                            capture_output=True, text=True, timeout=120)
#   with:                            text=True, timeout=120)
"""
import ast
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

import tcheck
from tcheck import ck, eq, note, section, shown

ROOT = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════════════════
section("1. WHAT THE RUNNER READS AS A COMMAND")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ The runner's own parse (actions/runner, ActionCommand.TryParseV2):
#    trim leading whitespace, require `::`, the command runs to the next `::`.
for line, want in (
        ("::error::test_live.py FAILED", "error"),
        ("   ::warning::indented still counts", "warning"),
        ("\t::notice file=a.py,line=3::with properties", "notice"),
        ("::group::a fold", "group"),
        ("::sometoken::after stop-commands, any name resumes", "sometoken"),
        (": :error: :defused", None),
        ("x ::error::mid-line is text", None),
        ("::error with no closing pair", None),
        ("  ✅ a check — ::error::inside a detail line", None)):
    eq(tcheck.command_of(line), want, "   %r -> %r" % (shown(line), want))

ck(isinstance(sys.stdout, tcheck._Watched) and isinstance(sys.stderr, tcheck._Watched),
   "🔴 this very process is watched: stdout and stderr, from tcheck's import on")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 EVERY WAY A TEST CAN WRITE A PLANTED ::error::")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ TWO KINDS OF PATH. What the HARNESS prints (a check, its detail, a
#    note, a section) is where captured output is shown on purpose, and its
#    content can depend on the machine, so tcheck defuses it and the file
#    stays GREEN. Everything that bypasses the harness is defused AND fails
#    the file: nobody meant it, and nobody would otherwise know.
HARNESS = {
    "the #1852 shape: a captured log in a check's detail":
        'from tcheck import ck\n'
        'ck("the staged job is red", True, "log:\\n::error::test_live.py FAILED\\nrc=1")\n',
    "a note":
        'from tcheck import ck, note\nck("x", True)\nnote("got:\\n::error::planted")\n',
    "eq's got/want":
        'from tcheck import eq\neq("::error::a\\n::warning::b", "::error::a\\n::warning::b", "same")\n',
    "a section title":
        'from tcheck import ck, section\nsection("x\\n::error::planted")\nck("x", True)\n',
}
PLANTS = {
    "a bare print":
        'from tcheck import ck\nck("x", True)\nprint("::error::planted")\n',
    "stderr":
        'import sys\nfrom tcheck import ck\nck("x", True)\n'
        'sys.stderr.write("::error::planted\\n")\n',
    "indented":
        'from tcheck import ck\nck("x", True)\nprint("    ::error::planted")\n',
    "split across two writes":
        'import sys\nfrom tcheck import ck\nck("x", True)\n'
        'sys.stdout.write(" :"); sys.stdout.write(":error::planted\\n")\n',
    "the last line, never finished":
        'import sys\nfrom tcheck import ck\nck("x", True)\n'
        'sys.stdout.write("::error::planted")\n',
    "product code printing in-process (the test_freshness shape)":
        'from tcheck import ck\n'
        'def converge():\n    print("::error::card failed for mlb (planted)")\n    return 1\n'
        'ck("a failed card returns 1", converge() == 1)\n',
    "a worker thread":
        'import threading\nfrom tcheck import ck\nck("x", True)\n'
        't = threading.Thread(target=print, args=("::error::planted",))\n'
        't.start(); t.join()\n',
    "a traceback":
        'from tcheck import ck\nck("x", True)\n'
        'raise RuntimeError("boom\\n::error::planted")\n',
}


def planted(src):
    """Run `src` in a throwaway dir beside a copy of tcheck. -> (rc, output)."""
    d = tempfile.mkdtemp(prefix="wfcmd-")
    try:
        shutil.copy(os.path.join(ROOT, "tcheck.py"), d)
        open(os.path.join(d, "test_p.py"), "w", encoding="utf-8").write(src)
        p = subprocess.run([sys.executable, "-B", "test_p.py"], cwd=d,
                           capture_output=True, text=True, timeout=120,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        return p.returncode, p.stdout + p.stderr
    finally:
        shutil.rmtree(d, ignore_errors=True)


def commands(out):
    return [ln for ln in out.splitlines() if tcheck.command_of(ln)]


def why_not(ok, rc, out):
    """A planted file's output, shown only when the check it explains FAILED.

    ⚠️ Printed on a pass, a planted file's own "❌ 1 of 2 checks FAILED"
    would sit in a GREEN log and read as this file's failure.
    """
    return "" if ok else "rc=%s %s" % (rc, shown(out[-400:]))


for why, src in HARNESS.items():
    rc, out = planted(src)
    ck(not commands(out),
       "🔴🔴 %s: NOTHING reaches the run as a command" % why,
       why_not(not commands(out), rc, out))
    ck(rc == 0, "   ...and the harness showed it on purpose, so the file stays green",
       why_not(rc == 0, rc, out))

for why, src in PLANTS.items():
    rc, out = planted(src)
    ck(not commands(out),
       "🔴🔴 %s: NOTHING reaches the run as a command" % why,
       why_not(not commands(out), rc, out))
    _ok = rc != 0 and "GitHub reads as a workflow command" in out
    ck(_ok, "   ...and the file FAILS, naming it", why_not(_ok, rc, out))

rc, out = planted('from tcheck import annotate, ck\nck("x", True)\n'
                  'annotate("warning", "on purpose\\nline two 100%")\n')
eq(commands(out), ["::warning::on purpose%0Aline two 100%25"],
   "✅ annotate() writes exactly ONE command, escaped onto one line")
ck(rc == 0, "   ...and a deliberate annotation is not a leak", why_not(rc == 0, rc, out))

rc, out = planted('import sys\nfrom tcheck import ck\n'
                  'print("a::b mid-line, and [::-1]")\n'
                  'sys.stdout.write("  partial "); sys.stdout.write("line\\n")\n'
                  'print(":one colon", flush=True)\n'
                  'ck("fine", True)\n')
_ok = rc == 0 and "a::b mid-line, and [::-1]\n  partial line\n:one colon\n" in out
ck(_ok, "✅ THE CONTROL: ordinary output passes through byte for byte and the file is green",
   "" if _ok else "⛔ a guard that fires on correct code is the other failure "
   "(CLAUDE.md). " + why_not(_ok, rc, out))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE PATH THE WATCHER CANNOT SEE: A CHILD'S OWN STDOUT")
# ══════════════════════════════════════════════════════════════════════
# ⛔ A child process writes to the descriptor it inherited, below Python.
#    So every child a test file starts must capture (or redirect) BOTH of
#    its streams, and nothing may shell out with os.system / os.popen.
SPAWN = {"run", "call", "check_call", "check_output", "Popen"}
_TO_LOG = {"sys.stdout", "sys.stderr", "None", "sys.__stdout__", "sys.__stderr__"}


def uncaptured(src):
    """-> [(line, call)] for every child whose output would reach the log."""
    tree = ast.parse(src)
    mods, funcs = set(), {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "subprocess":
                    mods.add(a.asname or a.name)
        elif isinstance(n, ast.ImportFrom) and n.module == "subprocess":
            for a in n.names:
                if a.name in SPAWN:
                    funcs[a.asname or a.name] = a.name
    bad = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        name = None
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            if f.value.id in mods and f.attr in SPAWN:
                name = f.attr
            elif f.value.id == "os" and (f.attr in ("system", "popen")
                                         or f.attr.startswith(("spawn", "exec"))):
                bad.append((n.lineno, "os." + f.attr))
                continue
        elif isinstance(f, ast.Name) and f.id in funcs:
            name = funcs[f.id]
        if not name:
            continue
        kw = {k.arg: ast.unparse(k.value) for k in n.keywords}
        cap = kw.get("capture_output") == "True"
        if None in kw and not cap:
            bad.append((n.lineno, "%s(**...) — cannot tell where its output goes" % name))
            continue
        out_ok = cap or name == "check_output" or kw.get("stdout", "None") not in _TO_LOG
        err_ok = cap or kw.get("stderr", "None") not in _TO_LOG
        if not (out_ok and err_ok):
            bad.append((n.lineno, "subprocess.%s without %s" % (
                name, " and ".join(s for s, ok in (("stdout", out_ok), ("stderr", err_ok))
                                   if not ok))))
    return bad


for why, src, want in (
        ("a captured run", "import subprocess\nsubprocess.run(['x'], capture_output=True)\n", 0),
        ("an uncaptured run", "import subprocess\nsubprocess.run(['x'])\n", 1),
        ("stdout captured, stderr to the log",
         "import subprocess\nsubprocess.run(['x'], stdout=subprocess.PIPE)\n", 1),
        ("both redirected", "import subprocess as sp\n"
         "sp.run(['x'], stdout=sp.PIPE, stderr=sp.STDOUT)\n", 0),
        ("an alias, uncaptured", "import subprocess as _sp\n_sp.Popen(['x'])\n", 1),
        ("a from-import, uncaptured", "from subprocess import run as r\nr(['x'])\n", 1),
        ("check_output leaves stderr to the log",
         "import subprocess\nsubprocess.check_output(['x'])\n", 1),
        ("stdout handed the log explicitly",
         "import subprocess, sys\nsubprocess.run(['x'], stdout=sys.stdout, stderr=subprocess.DEVNULL)\n", 1),
        ("os.system", "import os\nos.system('echo ::error::x')\n", 1),
        ("unpacked kwargs", "import subprocess\nsubprocess.run(['x'], **kw)\n", 1),
        ("unpacked kwargs beside an explicit capture",
         "import subprocess\nsubprocess.run(['x'], capture_output=True, **kw)\n", 0)):
    eq(len(uncaptured(src)), want, "   the static check on %s: %d finding(s)" % (why, want))

_tests = sorted(glob.glob(os.path.join(ROOT, "test_*.py")))
ck(len(_tests) >= 100, "⚠️ there are test files to check (%d)" % len(_tests),
   "⛔ a check over an empty set proves nothing (rule 67)")
_bad = {}
for _p in _tests:
    _b = uncaptured(open(_p, encoding="utf-8").read())
    if _b:
        _bad[os.path.basename(_p)] = _b
ck(not _bad, "🔴🔴 NO test file starts a child whose output reaches the run unwatched",
   "⛔ capture it (capture_output=True, or stdout= AND stderr=) and print it "
   "through tcheck.shown(). Found: %s" % _bad)


# ══════════════════════════════════════════════════════════════════════
section("4. ⚠️ THE WATCHER IS ON BEFORE A TEST CAN PRINT")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ `test_harness.py` already requires every test file to import tcheck.
#    This asks the narrower question the watcher needs: does anything PRINT
#    above that import? Output written before it is not watched.
# ⛔ NOT "any statement above it": 17 files put `sys.path.insert(0, ROOT)`
#    there, which they need in order to import tcheck at all, and a first
#    draft of this check failed all 17 (a guard firing on correct code).
def _prints(node):
    for c in ast.walk(node):
        if not isinstance(c, ast.Call):
            continue
        f = c.func
        if isinstance(f, ast.Name) and f.id == "print":
            return True
        if isinstance(f, ast.Attribute) and f.attr in ("write", "writelines") \
                and ast.unparse(f.value) in ("sys.stdout", "sys.stderr"):
            return True
    return False


def printed_before_tcheck(src):
    for n in ast.parse(src).body:
        if isinstance(n, ast.ImportFrom) and n.module == "tcheck":
            return None
        if isinstance(n, ast.Import) and any(a.name == "tcheck" for a in n.names):
            return None
        if not isinstance(n, (ast.FunctionDef, ast.ClassDef)) and _prints(n):
            return n.lineno
    return 0


eq(printed_before_tcheck('print("x")\nfrom tcheck import ck\n'), 1,
   "   a print above the import is found")
eq(printed_before_tcheck('import sys\nif True:\n    sys.stderr.write("x")\n'
                         'from tcheck import ck\n'), 2,
   "   ...and one inside a block")
eq(printed_before_tcheck('"""doc"""\nimport os, sys\nsys.path.insert(0, ".")\n'
                         'def f():\n    print(1)\nfrom tcheck import ck\nprint(1)\n'), None,
   "   a docstring, imports, sys.path and a def above it are fine")
_late = {}
for _p in _tests:
    _l = printed_before_tcheck(open(_p, encoding="utf-8").read())
    if _l is not None:
        _late[os.path.basename(_p)] = _l
ck(not _late, "🔴 every test file imports tcheck before its first top-level statement",
   "⛔ output written before the import is not watched: %s" % _late)

note("⛔ WHAT THIS DOES NOT CLAIM: that a child started by PRODUCT code "
     "during a test is watched (it writes to the descriptor it inherited), "
     "or that the node tests (test_*.js) are; neither prints a command "
     "today.")
