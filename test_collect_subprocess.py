#!/usr/bin/env python3
"""
🔴🔴 NO TEST MAY RUN THE COLLECTOR IN A WAY THAT CAN CONVERGE, FETCH OR SPEND.

`[2026-09-28]` `collect.py <mode>` is not "run this mode". For a league with a
freshness contract, `main()` converges EVERY overdue artifact
(`converge(explicit=[mode])`, `allow_paid=True`). Six test subprocesses ran
`collect.py card-fb` that way — test_accumulators.py (2), test_dossier_fb.py
(3), test_shadow_fb.py (1). Every run fetched news from cbssports and
profootballtalk (measured with the network blocked: 2 attempts per run), and
on 2026-09-27's tree the same call planned THREE PAID modes plus nflverse.
They were refused only because CI's Tests step carries no key; with the key
exported, a test spends Odds API credits into a temp dir it then deletes.
`test_source_block.py` documented that exact incident on 2026-09-11 — and
guarded only itself.

✅ THE CLASS, NOT THE INSTANCE. Every subprocess call in every `test_*.py`
whose argv names `collect.py` must
  1. pass `converge-off` in its argv: the mode runs ALONE; and
  2. blank ODDS_API_KEY in the env it hands the child (set to "", popped,
     or an env that does not inherit `os.environ`), so that if (1) is ever
     dropped the worst case is a failed fetch, never a bill.
  ⚪ CFBD_API_KEY is REPORTED, not failed: CFBD costs nothing (CLAUDE.md
     rule 1), and with `converge-off` only the named mode can reach it.

⚠️ WHAT IT SEES: `subprocess.run/call/check_call/check_output/Popen` (any
alias of the module, or a name imported from it) whose argv — a list, or a
name / concatenation / `-c` script it resolves in the same file — names
`collect.py`; and a call to a helper defined in the same file that runs a
subprocess from its parameters, when the call site passes `collect.py`
(`test_record_grader.py`'s `sh(t, "collect.py", ...)`).
⛔ WHAT IT CANNOT SEE: a workflow step executed through bash (the files that
do it put a stub `python` on PATH, so no real collector runs), and a product
script that runs collect.py itself (`verify_record.py`, which passes
`converge-off`).

# @vacuity 🔴 a collector call without `converge-off` is found (a real call in another file)
#   file: test_run_mode_left.py
#   find: p = subprocess.run([sys.executable, "collect.py", "props-board", "converge-off"],
#   with: p = subprocess.run([sys.executable, "collect.py", "props-board"],
#
# @vacuity 🔴 an env that keeps ODDS_API_KEY is found (a popped key put back)
#   file: test_run_mode_left.py
#   find: env.pop("ODDS_API_KEY", None)
#   with: pass
#
# @vacuity 🔴 ...through a `-c` wrapper too: section 8's card-fb run without `converge-off`
#   file: test_shadow_fb.py
#   find: "card-fb", "converge-off"], cwd=_d8,
#   with: "card-fb"], cwd=_d8,
#
# @vacuity 🔴 ...and through a helper whose env drops the blank key
#   file: test_accumulators.py
#   find: env=dict(os.environ, LEAGUE="nfl", ODDS_API_KEY="",
#   with: env=dict(os.environ, LEAGUE="nfl",
#
# @vacuity ⛔ the shared network fence refuses a LOOKUP, not only a connect
#   file: test_shadow_fb.py
#   find: "socket.getaddrinfo = _refuse\n"
#   with: "pass\n"
#   ⚠️ LOCAL EVEN UNDER THE MUTATION: the probe looks up and connects to
#      127.0.0.1 only, so an unfenced call never leaves the machine.
#
# @vacuity ⛔ the two copies of the fence cannot drift apart
#   file: test_accumulators.py
#   find: "socket.socket.connect = lambda self, *a, **k: _refuse(*a)\n"
#   with: "socket.socket.connect = lambda self, *a, **k: None\n"
"""
import ast
import glob
import os
import re
import subprocess
import sys
import warnings

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section, shown  # noqa: E402

SUBPROCESS_FNS = {"run", "call", "check_call", "check_output", "Popen"}
# ⚠️ `collect.py` as a FILE NAME, never a suffix: `test_collect.py` and
#    `verify_collect.py` are not the collector.
COLLECT = re.compile(r"(?<![\w.])collect\.py\b")
KEYS = ("ODDS_API_KEY", "CFBD_API_KEY")


class Scan:
    """Every collector subprocess call in one test file's source."""

    def __init__(self, src, name):
        self.name = name
        with warnings.catch_warnings():
            # ⚠️ another file's `"\w"` is its own business, not this scan's
            warnings.simplefilter("ignore", SyntaxWarning)
            self.tree = ast.parse(src)
        self.parent = {}
        for n in ast.walk(self.tree):
            for c in ast.iter_child_nodes(n):
                self.parent[c] = n
        self.mods, self.fns = {"subprocess"}, set()
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    if a.name == "subprocess":
                        self.mods.add(a.asname or a.name)
            elif isinstance(n, ast.ImportFrom) and n.module == "subprocess":
                for a in n.names:
                    if a.name in SUBPROCESS_FNS:
                        self.fns.add(a.asname or a.name)

    # ── scopes ──────────────────────────────────────────────────────────
    def scope(self, node):
        """The function (or module) whose body `node` executes in."""
        p = self.parent.get(node)
        while p is not None and not isinstance(
                p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            p = self.parent.get(p)
        return p or self.tree

    def own(self, scope):
        """The nodes of `scope`, nested functions excluded."""
        stack, out = list(ast.iter_child_nodes(scope)), []
        while stack:
            n = stack.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.Lambda, ast.ClassDef)):
                continue
            out.append(n)
            stack.extend(ast.iter_child_nodes(n))
        return out

    def params(self, scope):
        if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef,
                                  ast.Lambda)):
            return set()
        a = scope.args
        names = [x.arg for x in a.posonlyargs + a.args + a.kwonlyargs]
        names += [x.arg for x in (a.vararg, a.kwarg) if x]
        return set(names)

    def assignment(self, name, at):
        """The value last assigned to `name` before `at`, in `at`'s scope,
        else at module level. -> (value node, scope) or (None, None)."""
        home = self.scope(at)
        for sc in (home, self.tree):
            best = None
            for n in self.own(sc):
                if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None:
                    tg = n.targets if isinstance(n, ast.Assign) else [n.target]
                    if any(isinstance(t, ast.Name) and t.id == name for t in tg):
                        # ⚠️ in the caller's own scope, only what ran BEFORE
                        #    it; a module constant read from a function may
                        #    be defined anywhere at module level.
                        if sc is not home or n.lineno <= at.lineno:
                            if best is None or n.lineno > best.lineno:
                                best = n
            if best is not None:
                return best.value, sc
        return None, None

    def strings(self, node, depth=0):
        """Every string constant in `node`, names resolved in this file."""
        out = []
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                out.append(n.value)
            elif isinstance(n, ast.Name) and depth < 5:
                v, _ = self.assignment(n.id, n)
                if v is not None and v is not node:
                    out += self.strings(v, depth + 1)
        return out

    # ── the calls ───────────────────────────────────────────────────────
    def is_subprocess(self, call):
        f = call.func
        return ((isinstance(f, ast.Attribute) and f.attr in SUBPROCESS_FNS
                 and isinstance(f.value, ast.Name) and f.value.id in self.mods)
                or (isinstance(f, ast.Name) and f.id in self.fns))

    @staticmethod
    def argv(call):
        if call.args:
            return call.args[0]
        return next((k.value for k in call.keywords if k.arg == "args"), None)

    @staticmethod
    def kw(call, name):
        return next((k.value for k in call.keywords if k.arg == name), None)

    def blanks(self, call, key):
        """Does the env this call hands its child leave `key` empty?"""
        env = self.kw(call, "env")
        if env is None:
            return False                    # ⛔ inherits os.environ whole
        holder = None
        if isinstance(env, ast.Name):
            holder = env.id
            env, _ = self.assignment(env.id, call)
            if env is None:
                return False
        inherits, verdict = False, None
        if isinstance(env, ast.Call) and getattr(env.func, "id", "") == "dict":
            for k in env.keywords:
                if k.arg == key:
                    verdict = isinstance(k.value, ast.Constant) and k.value.value == ""
                elif k.arg is None:
                    inherits = True
            inherits = inherits or bool(env.args)
        elif isinstance(env, ast.Dict):
            for k, v in zip(env.keys, env.values):
                if k is None:
                    inherits = True
                elif isinstance(k, ast.Constant) and k.value == key:
                    verdict = isinstance(v, ast.Constant) and v.value == ""
        else:
            inherits = True                 # os.environ.copy(), a call: assume so
        if verdict is not None:
            return verdict
        if not inherits:
            return True                     # a fresh env without the key
        if holder is None:
            return False
        # ✅ AN INHERITED ENV THE FILE THEN EDITS: pop / del / set to "".
        for n in self.own(self.scope(call)):
            if getattr(n, "lineno", 10 ** 9) > call.lineno:
                continue
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr in ("pop", "update")
                    and getattr(n.func.value, "id", "") == holder):
                if n.func.attr == "pop" and n.args and getattr(n.args[0], "value", None) == key:
                    return True
                if n.func.attr == "update" and any(
                        k.arg == key and getattr(k.value, "value", None) == ""
                        for k in n.keywords):
                    return True
            if isinstance(n, (ast.Delete, ast.Assign)):
                tg = n.targets
                for t in tg:
                    if (isinstance(t, ast.Subscript)
                            and getattr(t.value, "id", "") == holder
                            and getattr(t.slice, "value", None) == key
                            and (isinstance(n, ast.Delete)
                                 or getattr(n.value, "value", None) == "")):
                        return True
        return False

    def finding(self, call, where, args_strings):
        return {"file": self.name, "line": where.lineno,
                "call": " ".join(ast.unparse(where).split())[:140],
                "converge_off": any("converge-off" in s for s in args_strings),
                **{k: self.blanks(call, k) for k in KEYS}}

    def calls(self):
        """-> [finding] for every collector subprocess call in the file."""
        out, deferred = [], {}
        for n in ast.walk(self.tree):
            if not (isinstance(n, ast.Call) and self.is_subprocess(n)):
                continue
            av = self.argv(n)
            if av is None:
                continue
            ss = self.strings(av)
            sc = self.scope(n)
            uses = {x.id for x in ast.walk(av) if isinstance(x, ast.Name)}
            from_params = uses & self.params(sc)
            if any(COLLECT.search(s) for s in ss):
                f = self.finding(n, n, ss)
                if f["converge_off"] or not from_params:
                    out.append(f)
                    continue
            if from_params and isinstance(sc, (ast.FunctionDef,
                                               ast.AsyncFunctionDef)):
                # ⚠️ A HELPER: its argv is built from what its CALLERS pass.
                deferred[sc.name] = (n, ss)
        for n in ast.walk(self.tree):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id in deferred):
                sub, inner = deferred[n.func.id]
                site = [s for a in list(n.args) + [k.value for k in n.keywords]
                        for s in self.strings(a)]
                if any(COLLECT.search(s) for s in site + inner):
                    out.append(self.finding(sub, n, site + inner))
        return out


def scan(src, name="<planted>"):
    return Scan(src, name).calls()


def bad(f):
    return not (f["converge_off"] and f["ODDS_API_KEY"])


# ══════════════════════════════════════════════════════════════════════
section("1. ⚠️ THE SCANNER TELLS A BAD CALL FROM A GOOD ONE (planted)")
# ══════════════════════════════════════════════════════════════════════
# ⛔ PROVED ON A FIXTURE FIRST, every shape the real files use, because a
#    scanner that finds nothing passes forever (rule 67).
PLANTED = r'''
import os, subprocess, sys
import subprocess as sp
from subprocess import run as _run
ROOT = "."
OFF = "import runpy; runpy.run_path('collect.py', run_name='__main__')"
subprocess.run([sys.executable, "collect.py", "card-fb"], env=dict(os.environ, LEAGUE="nfl"))                  # BAD-1 converges, keeps key
subprocess.run([sys.executable, "collect.py", "card-fb", "converge-off"], env=dict(os.environ, LEAGUE="nfl"))  # BAD-2 keeps key
subprocess.run([sys.executable, "collect.py", "card-fb"], env=dict(os.environ, ODDS_API_KEY=""))               # BAD-3 converges
sp.check_output([sys.executable, os.path.join(ROOT, "collect.py"), "news"])                                   # BAD-4 alias, no env
_run([sys.executable, "-c", OFF, "card-fb"], env={**os.environ, "ODDS_API_KEY": ""})                          # BAD-5 -c wrapper, converges
def sh(t, *argv):
    return subprocess.run([sys.executable, "-B"] + list(argv), cwd=t, env=dict(os.environ, LEAGUE="mlb"))
sh(".", "collect.py", "record", "converge-off")                                                                # BAD-6 helper keeps key
subprocess.run([sys.executable, "collect.py", "card-fb", "converge-off"], env=dict(os.environ, ODDS_API_KEY=""))  # GOOD-1
env = dict(os.environ, LEAGUE="nfl")
env.pop("ODDS_API_KEY", None)
subprocess.run([sys.executable, "collect.py", "props-board", "converge-off"], env=env)                        # GOOD-2 popped
_run([sys.executable, "-c", OFF, "card-fb", "converge-off"], env={**os.environ, "ODDS_API_KEY": ""})          # GOOD-3 -c wrapper
subprocess.run([sys.executable, "collect.py", "x", "converge-off"], env={"PATH": "/bin"})                     # GOOD-4 fresh env
def sh2(t, *argv):
    return subprocess.run([sys.executable, "-B"] + list(argv), cwd=t, env=dict(os.environ, ODDS_API_KEY=""))
sh2(".", "collect.py", "record", "converge-off")                                                               # GOOD-5 helper
open(os.path.join(ROOT, "collect.py")).read()                                                                  # NOT A CALL
subprocess.run(["git", "log", "-1"])                                                                           # NOT THE COLLECTOR
subprocess.run([sys.executable, "test_collect.py"])                                                            # NOT THE COLLECTOR
'''
_P = scan(PLANTED)
_lines = PLANTED.splitlines()
_tag = {f["line"]: re.search(r"#\s*(\S+)", _lines[f["line"] - 1]).group(1)
        if "#" in _lines[f["line"] - 1] else "?" for f in _P}
_bad = sorted(_tag[f["line"]] for f in _P if bad(f))
_good = sorted(_tag[f["line"]] for f in _P if not bad(f))
ck(_bad == ["BAD-%d" % i for i in range(1, 7)],
   "🔴 every planted BAD call is flagged — no converge-off, a kept key, an "
   "alias, a `-c` wrapper, a helper (%s)" % _bad,
   "Got bad=%s good=%s" % (_bad, _good))
ck(_good == ["GOOD-%d" % i for i in range(1, 6)],
   "   ✅ ...and every planted GOOD call passes — a blank key, a popped key, "
   "a wrapper, a fresh env, a helper (%s)" % _good,
   "⛔ a guard that fires on correct code is the other failure, not a safe "
   "one. Got good=%s bad=%s" % (_good, _bad))
ck(len(_P) == 11,
   "   ⚠️ ...and nothing that is not a collector call is counted (%d found)"
   % len(_P),
   "⛔ `open('collect.py')`, `git log` and `test_collect.py` are not the "
   "collector. Found: %s" % [f["call"][:50] for f in _P])

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 EVERY COLLECTOR CALL IN EVERY TEST FILE RUNS ALONE, KEYLESS")
# ══════════════════════════════════════════════════════════════════════
_FILES = sorted(glob.glob(os.path.join(ROOT, "test_*.py")))
_ALL, _unparsed = [], []
for _f in _FILES:
    try:
        _ALL += scan(open(_f, encoding="utf-8").read(), os.path.basename(_f))
    except SyntaxError as _e:
        _unparsed.append("%s: %s" % (os.path.basename(_f), _e))
ck(not _unparsed, "⚠️ every test file parsed (%d)" % len(_FILES),
   "⛔ a file this cannot read is a file it cannot vouch for: %s"
   % _unparsed)
_byfile = sorted({f["file"] for f in _ALL})
ck(len(_ALL) >= 10 and len(_byfile) >= 5,
   "⚠️ the scan found %d collector call(s) in %d file(s)"
   % (len(_ALL), len(_byfile)),
   "⛔ rule 67: a scan that finds none passes forever. Files: %s" % _byfile)
_nooff = ["%s:%d" % (f["file"], f["line"]) for f in _ALL if not f["converge_off"]]
ck(not _nooff,
   "🔴🔴 EVERY COLLECTOR CALL PASSES `converge-off` — the mode runs ALONE",
   "⛔ `collect.py <mode>` converges every overdue artifact: news from two "
   "outside hosts on every run, and the PAID modes whenever they are due. "
   "Missing: %s" % _nooff)
_keyed = ["%s:%d" % (f["file"], f["line"]) for f in _ALL if not f["ODDS_API_KEY"]]
ck(not _keyed,
   "🔴🔴 ...AND EVERY ONE BLANKS ODDS_API_KEY — a test can never spend",
   "⛔ defence in depth: if `converge-off` is ever dropped, the worst case "
   "must be a failed fetch, never a bill. Inherits the key: %s" % _keyed)
note("   collector calls: %s" % ["%s:%d%s" % (f["file"], f["line"],
                                            "" if not bad(f) else " ✗")
                                for f in _ALL])
note("   ⚪ not blanking CFBD_API_KEY (free, and only the named mode runs): %s"
     % (["%s:%d" % (f["file"], f["line"]) for f in _ALL if not f["CFBD_API_KEY"]]
        or "none"))

# ══════════════════════════════════════════════════════════════════════
section("3. ⛔ THE NETWORK FENCE THE CARD-FB RUNS SHARE REFUSES, AND IS ONE FENCE")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ `test_shadow_fb.py` and `test_accumulators.py` each carry `OFFLINE`, a
#    `-c` prelude that refuses every lookup and connect and counts them.
#    Two copies are only safe if they cannot drift (rule 117), and a fence
#    is only a fence if it refuses — so both are asked here, read by AST,
#    never by importing a test file (that would run it).
def offline_of(path):
    for n in ast.parse(open(path, encoding="utf-8").read()).body:
        if (isinstance(n, ast.Assign) and len(n.targets) == 1
                and getattr(n.targets[0], "id", "") == "OFFLINE"):
            return ast.literal_eval(n.value)
    return None


_FENCES = {f: offline_of(os.path.join(ROOT, f))
           for f in ("test_shadow_fb.py", "test_accumulators.py")}
ck(all(_FENCES.values()) and len(set(_FENCES.values())) == 1,
   "⛔ both card-fb test files carry the SAME fence",
   "🔴 rule 117: a helper duplicated breaks in the file you did not edit. "
   "%s" % {k: (v or "")[:60] for k, v in _FENCES.items()})
_prelude = (_FENCES.get("test_shadow_fb.py") or "").split("#PIN\n")[0]
# ✅ LOCAL ONLY, EVEN IF THE FENCE IS BROKEN: a numeric loopback lookup and
#    a connect to 127.0.0.1's discard port never leave the machine.
_probe = _prelude + (
    "for _try in (lambda: socket.getaddrinfo('127.0.0.1', 9),\n"
    "             lambda: socket.socket().connect(('127.0.0.1', 9))):\n"
    "    try:\n"
    "        _try()\n"
    "    except OSError:\n"
    "        pass\n")
_r3 = subprocess.run([sys.executable, "-c", _probe], capture_output=True,
                     text=True, timeout=120, cwd=ROOT)
_o3 = (_r3.stdout or "") + (_r3.stderr or "")
ck(bool(_prelude) and "OFFLINE FENCE: 2 network attempt(s) refused" in _o3,
   "🔴 ...and it REFUSES AND COUNTS both a lookup and a connect",
   "⛔ a fence that lets either through is a test that can reach the "
   "network. %s" % shown(_o3[-300:]))

note("➡️ WHAT THIS DOES NOT CLAIM: that a test cannot reach the network by "
     "some other route. It closes the one route that fetched and could "
     "spend — the collector converging — in every test file at once, and "
     "the fence proves the two card-fb files reach nothing at all.")
