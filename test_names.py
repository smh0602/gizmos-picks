#!/usr/bin/env python3
"""Every exception name this repo raises or catches must actually exist.

🔴 WHY THIS EXISTS, AND IT IS MY OWN DEFECT FROM TODAY.
`[2026-09-01]` I shipped a `cfb.py` containing:

    except SeasonNotStarted as e:          # line 1133
    raise RuntimeError(...)                # line 329 — still untyped

**`SeasonNotStarted` was never defined in that file.** A patch script
asserted and died AFTER modifying its in-memory copy and BEFORE writing,
so the class definition and the typed `raise` were both silently lost
while the `except` clause survived from a second script.

⛔ IT WOULD HAVE BEEN A `NameError` ON THE FIRST CFB SEASON FAILURE,
taking down the whole back-fill loop instead of skipping one season.

🔴 AND BOTH CHECKS I RAN WERE INCAPABLE OF SEEING IT:
  - `ast.parse` proves SYNTAX. An undefined name is not a syntax error.
  - `test_cfb.py` passed, because nothing in it drives a failing season,
    and Python only evaluates an `except` expression when something is
    actually raised.
⚠️ **A CHECK THAT CANNOT FAIL ON THE DEFECT IT IS MEANT TO CATCH IS NOT
A CHECK.** That is the same lesson as the CI gate that named one test
file, and the resolver comment that promised a safety the code lacked --
this time committed by me, in the fix for another one of them.

✅ SO: walk every module, collect what it actually BINDS at module level,
and confirm every name used in a `raise` or an `except` resolves.
⚠️ Deliberately narrow. It does not attempt general dead-name analysis --
it targets exception plumbing, which is the code path least likely to be
exercised by a test and most likely to run only when something is
already going wrong.
"""
import ast
import builtins
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILTINS = set(dir(builtins))
fails = []


def module_bindings(tree):
    """Names this module binds anywhere — module level or nested.

    ⚠️ Generous on purpose. The goal is ZERO FALSE POSITIVES: a check
    that cries wolf gets deleted, and this project has said so twice.
    A name bound anywhere in the file counts as defined.
    """
    names = set(BUILTINS)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            names.add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                names.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, ast.arg):
            names.add(n.arg)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            names.add(n.name)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            names.update(n.names)
    return names


def used_exception_names(tree):
    """(lineno, name, context) for every bare Name in raise/except."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ExceptHandler) and n.type is not None:
            ts = n.type.elts if isinstance(n.type, ast.Tuple) else [n.type]
            for t in ts:
                # ⚠️ `except _nfl.SeasonNotStarted` is an Attribute --
                # resolving it would mean importing the other module, and
                # a check that needs the world is a check that breaks.
                if isinstance(t, ast.Name):
                    out.append((t.lineno, t.id, "except"))
        elif isinstance(n, ast.Raise) and n.exc is not None:
            e = n.exc
            if isinstance(e, ast.Call):
                e = e.func
            if isinstance(e, ast.Name):
                out.append((n.lineno, e.id, "raise"))
    return out


PY = sorted(f for f in os.listdir(ROOT)
            if f.endswith(".py") and not f.startswith("test_"))
print(f"checking exception names in {len(PY)} module(s)\n")
checked = 0
for fn in PY:
    try:
        tree = ast.parse(open(os.path.join(ROOT, fn), encoding="utf-8").read())
    except SyntaxError as e:
        print(f"  🔴 {fn}: SYNTAX ERROR {e}")
        fails.append(f"{fn}: syntax")
        continue
    bound = module_bindings(tree)
    bad = [(ln, nm, ctx) for ln, nm, ctx in used_exception_names(tree)
           if nm not in bound]
    checked += 1
    if bad:
        for ln, nm, ctx in bad:
            print(f"  🔴 FAIL {fn}:{ln}  {ctx} {nm}  — NOT DEFINED "
                  f"ANYWHERE IN THIS MODULE")
            fails.append(f"{fn}:{ln} {nm}")
    else:
        print(f"  ok   {fn}")

# ══════════════════════════════════════════════════════════════════════
# 🔴 A CHECK THAT HAS NEVER FAILED IS A CHECK NOBODY HAS TESTED.
# ⛔ So reintroduce the exact defect and confirm it is caught. Without
# this, the whole file could be a no-op and every run would still say ✅.
print("\nSELF-TEST — reintroduce the real defect and confirm it is caught")
BUG = ("def f():\n"
       "    try:\n"
       "        pass\n"
       "    except SeasonNotStarted as e:\n"
       "        raise\n")
_t = ast.parse(BUG)
_caught = [x for x in used_exception_names(_t)
           if x[1] not in module_bindings(_t)]
print(f"  {'ok  ' if _caught else '🔴 FAIL'} undefined `except` name is "
      f"caught  ({len(_caught)} finding)")
if not _caught:
    fails.append("self-test: the checker does not catch its own case")

OK = ("class SeasonNotStarted(RuntimeError):\n    pass\n"
      "def f():\n"
      "    try:\n"
      "        pass\n"
      "    except SeasonNotStarted:\n"
      "        raise SeasonNotStarted('x')\n")
_t2 = ast.parse(OK)
_fp = [x for x in used_exception_names(_t2)
       if x[1] not in module_bindings(_t2)]
print(f"  {'ok  ' if not _fp else '🔴 FAIL'} a DEFINED name is not "
      f"flagged  ({len(_fp)} false positive)")
if _fp:
    fails.append("self-test: false positive on a defined name")

print()
if fails:
    print(f"🔴 {len(fails)} FAILED: {', '.join(fails)}")
    sys.exit(1)
print(f"✅ exception names OK across {checked} module(s)")
