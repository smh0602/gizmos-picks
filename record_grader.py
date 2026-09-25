#!/usr/bin/env python3
"""WHICH GRADING CODE BUILT record.json? — one fingerprint, two readers.

🔴 WHY THIS EXISTS `[2026-09-25]`. PR #166 changed the MLB grading rule (a
postponed game is a void, not a day held back). `data/latest/record.json`
on main was still the file the OLD rule wrote at 09-24 12:05Z, and
`verify_record.py` — re-grading with the NEW rule — failed collect runs
#1803, #1813 and #1816-#1819 until the 12:08Z rebuild. Nothing was wrong
but the ORDER: the verifier asked "does the record the old grader wrote
agree with the new grader?", which is the wrong question.

✅ `collect_record()` stamps this fingerprint into record.json as `grader`.
`verify_record.py` compares it with the fingerprint of the `collect.py`
beside it and, when they differ, rebuilds the record FIRST
(`collect.py record converge-off`), then verifies. A grading-rule change
can no longer turn a run red; a builder and verifier that DISAGREE still
do, because a record carrying the current fingerprint is never rebuilt.

⛔ PARSED, NEVER IMPORTED. `verify_record.py` may not import the builder it
checks, so this reads `collect.py` as TEXT.

✅ THE CLASS, NOT A LIST. The fingerprint is `collect_record` plus every
top-level name it reaches, transitively — functions and constants alike
(`VOID_STATES`, `BATTER_RESULT`, `slate_settled`, `_won`, `PICKS`, …). A
helper the grader starts calling tomorrow is covered the day it is called,
with nobody editing a list.
⚠️ Comments, docstrings and layout are NOT part of it (`ast.dump` of the
tree), so a comment edit does not force a rebuild; anything that changes
what the code DOES, does. A Python upgrade may change `ast.dump` and so
the fingerprint — that costs one free rebuild, never a red run.
"""
import ast
import hashlib

ENTRY = "collect_record"


def _strip_docstrings(tree):
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = n.body
            if (b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant)
                    and isinstance(b[0].value.value, str)):
                n.body = b[1:] or [ast.Pass()]
    return tree


def _top_level(tree):
    """{name: [statement nodes that define it at module level]}.

    ⚠️ Module-level `if`/`try` blocks are opened too: collect.py assigns
    `LEAGUE` inside `if _forced:`, and `PICKS` is derived from it."""
    out = {}

    def visit(stmts):
        for s in stmts:
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.setdefault(s.name, []).append(s)
            elif isinstance(s, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                for t in (s.targets if isinstance(s, ast.Assign) else [s.target]):
                    for n in ast.walk(t):
                        if isinstance(n, ast.Name):
                            out.setdefault(n.id, []).append(s)
            elif isinstance(s, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                for field in ("body", "orelse", "finalbody"):
                    visit(getattr(s, field, []) or [])
                for h in getattr(s, "handlers", []) or []:
                    visit(h.body)
    visit(tree.body)
    return out


def closure(path, entry=ENTRY):
    """-> {name: [ast nodes]} for `entry` and everything it reaches."""
    tree = _strip_docstrings(ast.parse(open(path, encoding="utf-8").read()))
    defs = _top_level(tree)
    if entry not in defs:
        raise LookupError("%s defines no %s — there is no grader to fingerprint"
                          % (path, entry))
    seen, todo = {}, [entry]
    while todo:
        name = todo.pop()
        if name in seen or name not in defs:
            continue
        seen[name] = defs[name]
        for node in defs[name]:
            todo.extend(n.id for n in ast.walk(node) if isinstance(n, ast.Name))
    return seen


def fingerprint(path, entry=ENTRY):
    """16 hex characters naming the grading code in `path`.

    ⛔ Raises when the file is missing or has no grader: "I could not tell
    which code built this" must never read as "it matches"."""
    parts = sorted("%s\n%s" % (name, ast.dump(node))
                   for name, nodes in closure(path, entry).items() for node in nodes)
    return hashlib.sha256("\n\n".join(parts).encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    import os
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "collect.py")
    print(fingerprint(p))
    print("covers:", ", ".join(sorted(closure(p))))
