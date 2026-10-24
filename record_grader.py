#!/usr/bin/env python3
"""WHICH GRADING CODE BUILT record.json (OR winners.json)? — one fingerprint,
two readers each.

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

🔴 `[2026-10-23]` THE GAME LINES TAB'S RECORD TOO (`winners.json`, every
league). PR #310 changed how winners.py grades (a void gives way to a later
real grade); the next MLB pass (collect 40040807226) ran no mode, and
verify_record checked the NEW rule against the winners.json the OLD rule had
written: red, "7/16, 0 void" vs "6/15, 1 void". The same wrong question, a
second artifact. ✅ `winners.build` stamps `winners_fingerprint` and
verify_record rebuilds a winners.json whose stamp differs, then verifies.
⚠️ That grading crosses modules (`collect.VOID_STATES`,
`fb_ledger.schedule_by_id`, `daystore.archive`), so its fingerprint FOLLOWS
them (`follow=True`): `from M import x` and `M.x` after `import M`, for any
`M.py` beside the file, keyed "M.x". ⛔ A module it reaches that is neither
beside the file nor in the standard library raises: it cannot tell which
code grades. collect_record reaches no other module's grading code, so
record.json's fingerprint is unchanged (`follow` off).
"""
import ast
import hashlib
import os
import sys

ENTRY = "collect_record"
WINNERS = "graded"          # winners.py: every frozen pick graded once, the grade that stands, the tally


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


def _imports(stmts, nested):
    """{local name: (module, attribute or None)} bound by the import statements
    in `stmts`: every one inside them (`nested`, a function's own imports) or
    only the module's own (opened like `_top_level`)."""
    out = {}
    for s in (n for st in stmts for n in (ast.walk(st) if nested else [st])):
        if isinstance(s, ast.Import):
            for a in s.names:
                out[a.asname or a.name.split(".")[0]] = (a.name if a.asname else a.name.split(".")[0], None)
        elif isinstance(s, ast.ImportFrom) and not s.level and s.module:
            for a in s.names:
                out[a.asname or a.name] = (s.module, a.name)
        elif not nested and isinstance(s, (ast.If, ast.Try, ast.With)):
            for field in ("body", "orelse", "finalbody"):
                out.update(_imports(getattr(s, field, []) or [], False))
            for h in getattr(s, "handlers", []) or []:
                out.update(_imports(h.body, False))
    return out


def _foreign(path, defs, mod_imports, seen):
    """(module file, name) for every other module's name the nodes in `seen` use."""
    here, out = os.path.dirname(os.path.abspath(path)), set()
    for nodes in seen.values():
        for node in nodes:
            local = _imports([node], True)
            for n in ast.walk(node):
                if isinstance(n, ast.Name):
                    b = local.get(n.id) or (None if n.id in defs else mod_imports.get(n.id))
                    hit = b if b and b[1] else None
                elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
                    b = local.get(n.value.id) or (None if n.value.id in defs
                                                  else mod_imports.get(n.value.id))
                    hit = (b[0], n.attr) if b and not b[1] else None
                else:
                    continue
                if not hit:
                    continue
                top = hit[0].split(".")[0]
                f = os.path.join(here, top + ".py")
                if os.path.exists(f):
                    out.add((f, hit[1]))
                elif top not in sys.stdlib_module_names:
                    raise LookupError("%s reaches %s.%s, which is neither beside it nor in the "
                                      "standard library — cannot tell which code grades"
                                      % (path, hit[0], hit[1]))
    return out


def _parse(path):
    """(top-level definitions, module-level imports) of one file, docstrings stripped."""
    tree = _strip_docstrings(ast.parse(open(path, encoding="utf-8").read()))
    return _top_level(tree), _imports(tree.body, False)


def closure(path, entry=ENTRY, follow=False):
    """-> {name: [ast nodes]} for `entry` and everything it reaches; with
    `follow`, also every other module's name it reaches, keyed "module.name"."""
    top, parsed, out, queue, done = os.path.abspath(path), {}, {}, [(os.path.abspath(path), entry)], set()
    while queue:
        p, start = queue.pop()
        if (p, start) in done:
            continue
        done.add((p, start))
        if p not in parsed:
            parsed[p] = _parse(p)
        defs, mod_imports = parsed[p]
        if start not in defs:
            if p == top:
                raise LookupError("%s defines no %s — there is no grader to fingerprint"
                                  % (path, entry))
            continue
        seen, todo = {}, [start]
        while todo:
            name = todo.pop()
            if name in seen or name not in defs:
                continue
            seen[name] = defs[name]
            for node in defs[name]:
                todo.extend(n.id for n in ast.walk(node) if isinstance(n, ast.Name))
        prefix = "" if p == top else os.path.basename(p)[:-3] + "."
        out.update((prefix + k, v) for k, v in seen.items())
        if follow:
            queue.extend(_foreign(p, defs, mod_imports, seen))
    return out


def fingerprint(path, entry=ENTRY, follow=False):
    """16 hex characters naming the grading code in `path`.

    ⛔ Raises when the file is missing or has no grader: "I could not tell
    which code built this" must never read as "it matches"."""
    parts = sorted("%s\n%s" % (name, ast.dump(node))
                   for name, nodes in closure(path, entry, follow).items() for node in nodes)
    return hashlib.sha256("\n\n".join(parts).encode("utf-8")).hexdigest()[:16]


def winners_fingerprint(path):
    """The Game Lines tab's grading code in winners.py at `path`, and every
    other module's code it reaches. Read by winners.build and verify_record."""
    return fingerprint(path, WINNERS, follow=True)


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "collect.py")
    print(fingerprint(p))
    print("covers:", ", ".join(sorted(closure(p))))
