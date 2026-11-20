#!/usr/bin/env python3
"""
A TEST'S VERDICT NEVER DEPENDS ON THE CI RUN'S OWN TRIGGER.

🔴 `[2026-11-19]` `freshness.fired_cron()` reads the run's trigger from
`os.environ` (`GITHUB_EVENT_NAME`, `GITHUB_EVENT_PATH`) when it is handed no
env, and `stand_down` asks it. ~~Only a free metered mode was asked~~: once a
paid mode stood down too (test_paid_standdown.py), `test_converge_judge.py`,
which drives the real `collect.converge(explicit=['gamelines'])` in a planted
MLB tree pinned to 17:10Z, stood its gamelines down under EVERY one of the 43
crons collect.yml declares (its board is 2 minutes old): 4 of its checks
would have gone red on every scheduled collect run and every nightly sweep,
and stayed green in pr-tests (a pull_request run names no cron). Found in
review, before it merged. The class CLAUDE.md forbids under "A TEST ASKS THE
CODE, NEVER PRODUCTION": a tree pinned to NOW, judged against the real run's
trigger.

✅ THE CLASS, DERIVED: every product function that names one of the two
variables, and every product function that calls one, transitively, through
the modules' own imports (`ambient`): today `freshness.fired_cron`,
`freshness.stand_down`, `collect.converge` and `collect.main`. A reader
added tomorrow is covered the day it is written.
✅ Every in-process call of one of them in every `test_*.py` must clear both
variables first: `os.environ.pop(...)`, `del os.environ[...]` or a set
value, each by name or through a loop over a tuple that names them, in the
calling function before the call, in an enclosing function before the nested
definition, at module level before the top-level statement that holds it, or
in a context manager defined in the same file whose `with` holds the call
(test_cron_stand_down.py's `at()`).
⛔ A call that hands the function its own env (`stand_down(rows, m, now, env)`,
`fired_cron(env)`) reads nothing ambient and is not asked.
⚠️ WHAT IT CANNOT SEE: a subprocess (it inherits the trigger; every collector
subprocess passes `converge-off`, which asks no stand-down: test_collect_subprocess.py),
a plain helper CALLED before the call to clear on its behalf, and a context
manager from another module (clear where the call is).

# @vacuity 🔴 the judge's sandbox converge without the trigger cleared is found
#   file: test_converge_judge.py
#   find:     for k in TRIGGER:
#   with:     for k in ():
#
# @vacuity 🔴 a loop that clears only one of the two is found (the planted-event driver)
#   file: test_paid_standdown.py
#   find:     keys = ("GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH", "LEAGUE", "ODDS_API_KEY",
#   with:     keys = ("GITHUB_EVENT_NAME", "LEAGUE", "ODDS_API_KEY",
#
# @vacuity 🔴 a module-level clear removed is found (a driver whose converge() names no mode)
#   file: test_credit_ledger.py
#   find: for _tv in ("GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH"):   # no test reads the run's trigger
#   with: for _tv in ():   # no test reads the run's trigger
"""
import ast
import glob
import os
import sys
import warnings

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, eq, note, section  # noqa: E402
import record_grader as RG  # noqa: E402  the one top-level/import reader

TRIGGER = ("GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH")
FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _parse(src):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)     # another file's "\w" is its own business
        return ast.parse(src)


def production(root):
    """{module: (top-level definitions, module imports)} for every product
    module beside this file (never a test)."""
    out = {}
    for f in sorted(glob.glob(os.path.join(root, "*.py"))):
        b = os.path.basename(f)
        if b.startswith("test_"):
            continue
        tree = _parse(open(f, encoding="utf-8").read())
        out[b[:-3]] = (RG._top_level(tree), RG._imports(tree.body, False))
    return out


def ambient(mods):
    """{(module, function)}: reads the run's trigger from the environment,
    itself or through a function it calls, transitively."""
    out = {(m, name) for m, (defs, _i) in mods.items() for name, nodes in defs.items()
           for node in nodes if isinstance(node, FUNCS)
           and any(isinstance(n, ast.Constant) and n.value in TRIGGER
                   for n in ast.walk(node))}
    grew = True
    while grew:
        grew = False
        for m, (defs, imps) in mods.items():
            for name, nodes in defs.items():
                if (m, name) in out:
                    continue
                for node in (n for n in nodes if isinstance(n, FUNCS)):
                    local = RG._imports([node], True)
                    if any(_reaches(n, m, local, imps, out) for n in ast.walk(node)):
                        out.add((m, name))
                        grew = True
                        break
    return out


def _reaches(n, m, local, imps, out):
    if isinstance(n, ast.Name):
        b = local.get(n.id) or imps.get(n.id)
        if b:
            return bool(b[1]) and (b[0], b[1]) in out          # `from M import f`
        return (m, n.id) in out                                  # this module's own f
    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
        b = local.get(n.value.id) or imps.get(n.value.id)
        return bool(b) and not b[1] and (b[0], n.attr) in out   # `import M as X` ... X.f
    return False


def env_slot(mods, mod, fn):
    """The position of `fn`'s `env` parameter, or None: a call that fills it
    hands the function its own trigger."""
    for node in mods[mod][0].get(fn, []):
        if isinstance(node, FUNCS):
            names = [a.arg for a in node.args.posonlyargs + node.args.args]
            if "env" in names:
                return names.index("env")
            if "env" in [a.arg for a in node.args.kwonlyargs]:
                return -1
    return None


class Scan:
    """Every in-process call of an ambient function in one test file, and
    whether the trigger is cleared before it."""

    def __init__(self, src, name, mods, amb):
        self.name, self.mods, self.amb = name, mods, amb
        self.tree = _parse(src)
        self.parent = {}
        for n in ast.walk(self.tree):
            for c in ast.iter_child_nodes(n):
                self.parent[c] = n
        self.alias, self.direct, self.environ = {}, {}, set()
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    top = a.name.split(".")[0]
                    if top in mods:
                        self.alias[a.asname or top] = top
            elif isinstance(n, ast.ImportFrom) and not n.level and n.module:
                for a in n.names:
                    if n.module in mods:
                        self.direct[a.asname or a.name] = (n.module, a.name)
                    elif n.module == "os" and a.name == "environ":
                        self.environ.add(a.asname or a.name)

    # ── the calls ───────────────────────────────────────────────────────
    def target(self, call):
        f = call.func
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in self.alias:
            return self.alias[f.value.id], f.attr
        if isinstance(f, ast.Name) and f.id in self.direct:
            return self.direct[f.id]
        return None

    def calls(self):
        for n in ast.walk(self.tree):
            if not isinstance(n, ast.Call):
                continue
            t = self.target(n)
            if t is None or t not in self.amb:
                continue
            slot = env_slot(self.mods, *t)
            if slot is not None and (any(k.arg == "env" for k in n.keywords)
                                     or (slot >= 0 and len(n.args) > slot)):
                continue                       # its own env: nothing ambient is read
            yield n, t

    # ── scopes ──────────────────────────────────────────────────────────
    def scope(self, node):
        p = self.parent.get(node)
        while p is not None and not isinstance(p, FUNCS + (ast.Lambda,)):
            p = self.parent.get(p)
        return p or self.tree

    def own(self, scope):
        stack, out = list(ast.iter_child_nodes(scope)), []
        while stack:
            n = stack.pop()
            if isinstance(n, FUNCS + (ast.Lambda, ast.ClassDef)):
                continue
            out.append(n)
            stack.extend(ast.iter_child_nodes(n))
        return out

    def strings(self, node, scope, depth=0):
        """The string constants a tuple / list / name resolves to in this file."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return {node.value}
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            return set().union(*[self.strings(e, scope, depth) for e in node.elts]) if node.elts else set()
        if isinstance(node, ast.Name) and depth < 4:
            for sc in (scope, self.tree):
                for n in self.own(sc):
                    if (isinstance(n, ast.Assign) and len(n.targets) == 1
                            and isinstance(n.targets[0], ast.Name) and n.targets[0].id == node.id):
                        return self.strings(n.value, sc, depth + 1)
        return set()

    def is_env(self, node):
        return ((isinstance(node, ast.Attribute) and node.attr == "environ"
                 and isinstance(node.value, ast.Name) and node.value.id == "os")
                or (isinstance(node, ast.Name) and node.id in self.environ))

    def touched(self, n):
        """The key node one statement clears or pins on os.environ, else None."""
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "pop" and self.is_env(n.func.value) and n.args):
            return n.args[0]
        if isinstance(n, (ast.Delete, ast.Assign)):
            for t in n.targets:
                if isinstance(t, ast.Subscript) and self.is_env(t.value):
                    return t.slice
        return None

    def clears(self, scope, line):
        """The trigger variables `scope` clears (or pins) before `line`."""
        out = set()
        for n in self.own(scope):
            if getattr(n, "lineno", line) >= line:
                continue
            key = self.touched(n)
            if isinstance(key, ast.Constant):
                out.add(key.value)
            elif isinstance(key, ast.Name):
                # through a loop (or comprehension) over a tuple that names them
                p = self.parent.get(n)
                while p is not None and p is not scope:
                    gens = ([p] if isinstance(p, ast.For) else
                            list(p.generators) if isinstance(
                                p, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp))
                            else [])
                    for g in gens:
                        if isinstance(g.target, ast.Name) and g.target.id == key.id:
                            out |= self.strings(g.iter, scope)
                    p = self.parent.get(p)
        return out & set(TRIGGER)

    def managed(self, call):
        """What the `with` blocks around `call` clear: a context manager defined
        in this file (test_cron_stand_down.py's `at()`) clears for its block."""
        got, p, child = set(), self.parent.get(call), call
        while p is not None:
            if isinstance(p, (ast.With, ast.AsyncWith)) and child in p.body:
                for item in p.items:
                    ce = item.context_expr
                    if isinstance(ce, ast.Call) and isinstance(ce.func, ast.Name):
                        for d in ast.walk(self.tree):
                            if isinstance(d, FUNCS) and d.name == ce.func.id:
                                got |= self.clears(d, 10 ** 9)
            p, child = self.parent.get(p), p
        return got

    def cleared(self, call):
        """Cleared in the calling scope before the call, by a `with` around it,
        or in any enclosing scope before the definition (or top-level
        statement) that holds it."""
        got, node = self.managed(call), call
        while True:
            sc = self.scope(node)
            got |= self.clears(sc, node.lineno)
            if sc is self.tree:
                return got
            node = sc

    def unguarded(self):
        return sorted({(n.lineno, "%s.%s" % t, tuple(sorted(set(TRIGGER) - self.cleared(n))))
                       for n, t in self.calls() if set(TRIGGER) - self.cleared(n)})


# ══════════════════════════════════════════════════════════════════════
section("1. THE FUNCTIONS THAT READ THE RUN'S TRIGGER, DERIVED FROM THE CODE")
# ══════════════════════════════════════════════════════════════════════
MODS = production(ROOT)
AMB = ambient(MODS)
note("reads the trigger, itself or through a call: %s" % ", ".join(
    "%s.%s" % t for t in sorted(AMB)))
ck("⚠️ the reader was found (rule 67: never an empty class)",
   ("freshness", "fired_cron") in AMB, sorted(AMB))
ck("🔴 ...and what reaches it: stand_down, and collect's converge and main",
   {("freshness", "stand_down"), ("collect", "converge"), ("collect", "main")} <= AMB,
   sorted(AMB))
ck("⚠️ fired_cron and stand_down take an env of their own (a call that fills it is not asked)",
   env_slot(MODS, "freshness", "fired_cron") is not None
   and env_slot(MODS, "freshness", "stand_down") is not None)


# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 EVERY TEST THAT CALLS ONE IN-PROCESS CLEARS THE TRIGGER FIRST")
# ══════════════════════════════════════════════════════════════════════
asked, bad = [], []
for f in sorted(glob.glob(os.path.join(ROOT, "test_*.py"))):
    s = Scan(open(f, encoding="utf-8").read(), os.path.basename(f), MODS, AMB)
    n = list(s.calls())
    if n:
        asked.append((s.name, len(n)))
    bad += [(s.name,) + u for u in s.unguarded()]
note("in-process callers: %s" % ", ".join("%s (%d)" % a for a in asked))
ck("⚠️ the callers were found (rule 67): the converge drivers are among them",
   {"test_converge_judge.py", "test_paid_standdown.py", "test_cron_stand_down.py"}
   <= {a for a, _n in asked}, asked)
eq(bad, [], "🔴🔴 no in-process call reads the CI run's trigger: each one clears "
   "GITHUB_EVENT_NAME and GITHUB_EVENT_PATH before it (file, line, call, not cleared)")


# ══════════════════════════════════════════════════════════════════════
section("3. THE SCAN, ON PLANTED SOURCES: IT FINDS WHAT IT MUST, AND ONLY THAT")
# ══════════════════════════════════════════════════════════════════════
def planted(src):
    return [(u[1], list(u[2])) for u in Scan(src, "planted", MODS, AMB).unguarded()]


ONE = "import collect\ndef go():\n    return collect.converge(explicit=['gamelines'])\n"
eq(planted(ONE), [("collect.converge", list(TRIGGER))],
   "🔴 a helper that converges with nothing cleared is found")
eq(planted("import collect as C\nimport os\n"
           "def go():\n    os.environ.pop('GITHUB_EVENT_NAME', None)\n    return C.main()\n"),
   [("collect.main", ["GITHUB_EVENT_PATH"])],
   "🔴 clearing one of the two is not enough (an alias is followed)")
eq(planted("import os\nimport collect\n"
           "KEYS = ('GITHUB_EVENT_NAME', 'GITHUB_EVENT_PATH', 'LEAGUE')\n"
           "def go():\n    for k in KEYS:\n        os.environ.pop(k, None)\n"
           "    return collect.converge()\n"), [],
   "✅ a loop over a module tuple that names both, before the call: cleared")
eq(planted("import os\nimport collect\n"
           "def go():\n    return collect.converge()\n"
           "for _k in ('GITHUB_EVENT_NAME', 'GITHUB_EVENT_PATH'):\n    os.environ.pop(_k, None)\n"),
   [("collect.converge", list(TRIGGER))],
   "🔴 a module-level clear AFTER the helper's definition does not count (it may run first)")
eq(planted("import os\nimport collect\n"
           "for _k in ('GITHUB_EVENT_NAME', 'GITHUB_EVENT_PATH'):\n    os.environ.pop(_k, None)\n"
           "def go():\n    return collect.converge()\n"), [],
   "✅ a module-level clear before the definition: cleared")
eq(planted("from os import environ\nimport collect\n"
           "def go():\n    del environ['GITHUB_EVENT_NAME']\n"
           "    environ['GITHUB_EVENT_PATH'] = ''\n    return collect.converge()\n"), [],
   "✅ `del` and a set value count too (`from os import environ`)")
eq(planted("import os\nimport collect\n"
           "def go():\n    r = collect.converge()\n"
           "    os.environ.pop('GITHUB_EVENT_NAME', None)\n"
           "    os.environ.pop('GITHUB_EVENT_PATH', None)\n    return r\n"),
   [("collect.converge", list(TRIGGER))], "🔴 cleared only AFTER the call: found")
WITH = ("import contextlib, os\nimport collect\n@contextlib.contextmanager\ndef blank():\n"
        "    keys = ('GITHUB_EVENT_NAME', 'GITHUB_EVENT_PATH')\n    for k in keys:\n"
        "        os.environ.pop(k, None)\n    yield\n")
eq(planted(WITH + "def go():\n    with blank():\n        return collect.converge()\n"), [],
   "✅ a context manager in this file that clears both, around the call: cleared")
eq(planted(WITH + "def go():\n    with blank():\n        pass\n    return collect.converge()\n"),
   [("collect.converge", list(TRIGGER))], "🔴 ...but not for a call after its block")
eq(planted("import freshness as F\nF.stand_down([], 'gamelines', None)\n"),
   [("freshness.stand_down", list(TRIGGER))], "🔴 stand_down with no env of its own is found")
eq(planted("import freshness as F\nF.stand_down([], 'gamelines', None, {})\n"
           "F.stand_down([], 'gamelines', None, env={})\nF.fired_cron({})\n"), [],
   "⛔ a call that hands its own env reads nothing ambient: not asked")
eq(planted("def converge(d):\n    return d\nconverge(1)\nimport json\njson.dumps(1)\n"), [],
   "⛔ a test's own `converge` helper, and a module that reads no trigger, are not asked")
