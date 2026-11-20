#!/usr/bin/env python3
r"""test_import_claims.py — a sentence saying one module never imports another is TRUE.

`[2026-11-20]` fix/pitcher-correction-wording gave football its price-words guard,
`card_fb.row_reads_price`, which imports `fb_model` and `fb_props_model` inside the function.
Both files' docstrings still said, as a ⛔ rule, "`card_fb.py` never imports this file". A
fresh session reads a ⛔ line as a rule: it could take the new imports for a breach and remove
them (cutting the football guard off from the code it asks), or trust a false import graph.
⚠️ ROOT CAUSE: an import claim is prose, and nothing compared it with the imports.
✅ Struck and dated in both files (rule 9). This file fails if a live claim and the code differ.

⛔ THE CLASS, NOT THE TWO FILES. `import_claims.py` reads every top-level `.py` (itself and
this file aside: they hold the planted sentences) and CLAUDE.md with struck text (~~...~~)
dropped and comment lines joined, and every sentence of the shape
"<A> [, / and / or <B>...] never imports / does not import / may not import ... <C>" is a
claim when its subjects and its object are modules in the top level (`x.py`, `` `x` ``,
"the x"); the object "this file", "this module" or a bare "this" before punctuation is the file
that says it. Each claim is asked of the subject's own source through tcheck's ONE import reader
(`_imports_of`, rule 117: every import in the file, inside a function too, `__import__` too).
⚠️ A sentence it cannot resolve ("it", a subject that is not a module, "this file" in
CLAUDE.md) is printed as a note, never guessed (vacuity.py's rule: an unclear mapping is
reported, never guessed). A passive "parsed, never imported" names no subject and is not read.

# @vacuity 🔴 fb_model's struck claim, made live again, is found false
#   file: fb_model.py
#   find: ⛔ IT DOES NOT REPLACE THE CARD. ~~`card_fb.py` never imports this file~~
#   with: ⛔ IT DOES NOT REPLACE THE CARD. `card_fb.py` never imports this file
#
# @vacuity 🔴 fb_props_model's struck claim, made live again, is found false
#   file: fb_props_model.py
#   find: ~~`card_fb.py` never imports this file~~ `[2026-11-20]` card_fb imports it only inside
#   with: `card_fb.py` never imports this file. `[2026-11-20]` card_fb imports it only inside
#
# @vacuity 🔴 struck text is history, never a claim (a guard that fires on correct text fails too)
#   file: import_claims.py
#   find:     return STRUCK.sub(" ", t)
#   with:     return t
#
# @vacuity 🔴 an import inside a function is an import
#   file: tcheck.py
#   find:         for n in ast.walk(tree) if tree is not None else ():
#   with:         for n in (tree.body if tree is not None else ()):
#
# @vacuity 🔴 a claim split across comment lines is still read
#   file: import_claims.py
#   find:     t = re.sub(r"\n[ \t]*#+[ \t]?", " ", src)
#   with:     t = src
#
# @vacuity 🔴 every subject of "A and the B never import this" is asked
#   file: import_claims.py
#   find: SEP = r"(?:\s*,\s*|\s+and\s+|\s+or\s+)"
#   with: SEP = r"(?!)"
#
# @vacuity 🔴 "this file" is the file that says it
#   file: import_claims.py
#   find:             obj = own if o.lower().startswith("this") else bare(o)
#   with:             obj = bare(o)
#
# @vacuity 🔴 CLAUDE.md's claims are read too
#   file: import_claims.py
#   find:         if f in skip or not (f.endswith(".py") or f == "CLAUDE.md"):
#   with:         if f in skip or not f.endswith(".py"):
#
# @vacuity 🔴 "does not import" is a claim, not only "never imports"
#   file: import_claims.py
#   find:         r"does\s+not\s+import|do\s+not\s+import|doesn't\s+import|don't\s+import|"
#   with:         r"do\s+not\s+import|doesn't\s+import|don't\s+import|"
#
# @vacuity 🔴 a false claim fails the file
#   file: import_claims.py
#   find:     return [c for c in found if c[2] in imported(c[1])]
#   with:     return []
"""
import os
import shutil
import sys
import tempfile

from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import tcheck  # noqa: E402  _imports_of: the ONE import reader (copy_module's)
import import_claims as IC  # noqa: E402  the claim reader


def claims(root):
    return IC.claims(root)


def false_claims(root, found):
    return IC.false_claims(root, found, tcheck._imports_of)


_trees = []


def tree(files):
    """A throwaway top level holding `files` ({name: text})."""
    d = tempfile.mkdtemp(prefix="import-claims-")
    _trees.append(d)
    for name, text in files.items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
            fh.write(text)
    return d


try:
    section("1. 🔴 A PLANTED CLAIM IS READ AND ASKED OF THE CODE")
    _lazy = tree({"b.py": '"""b.\n\n⛔ `a.py` never imports this file.\n"""\n',
                  "a.py": "def f():\n    import b\n    return b\n"})
    _f, _u = claims(_lazy)
    eq((_f, false_claims(_lazy, _f)), ([("b.py", "a", "b")], [("b.py", "a", "b")]),
       "🔴 '`a.py` never imports this file' beside an a.py importing b inside a function "
       "is false (an import inside a function is an import)")
    _true = tree({"b.py": '"""b.\n\n⛔ `a.py` never imports this file.\n"""\n',
                  "a.py": "import os\n"})
    _f, _u = claims(_true)
    eq((_f, false_claims(_true, _f)), ([("b.py", "a", "b")], []),
       "✅ the same claim beside an a.py that imports no b is read and true (silent on true words)")
    for _how, _code in (("from b import x", "from b import f\n"),
                        ("__import__('b')", "M = __import__('b')\n"),
                        ("import b as B", "import b as B\n")):
        _t = tree({"b.py": '"""⛔ `a.py` never imports this file."""\n\ndef f():\n    pass\n',
                   "a.py": _code})
        _f, _u = claims(_t)
        eq(false_claims(_t, _f), [("b.py", "a", "b")], "🔴 %s is an import of b" % _how)

    section("2. ✅ STRUCK TEXT IS HISTORY; A CLAIM SPLIT OVER COMMENT LINES IS STILL ONE")
    _struck = tree({"b.py": '"""b.\n\n⛔ ~~`a.py` never imports\nthis file~~ `[2026-11-20]` a '
                            'imports it inside f.\n"""\n',
                    "a.py": "def f():\n    import b\n"})
    eq(claims(_struck)[0], [], "✅ a struck claim (over two lines) is history, never a claim")
    _split = tree({"b.py": "X = 1\n# ⛔ `a.py` never\n#    imports this file, by design.\n",
                   "a.py": "import b\n"})
    _f, _u = claims(_split)
    eq(false_claims(_split, _f), [("b.py", "a", "b")],
       "🔴 '# ⛔ `a.py` never' / '#    imports this file' is one claim, and false")

    section("3. 🔴 EVERY SUBJECT, EVERY VERB, EVERY OBJECT FORM")
    _list = tree({"c.py": '"""⛔ status and the watchdog never import this: it drags in d."""\n',
                  "status.py": "import c\n", "watchdog.py": "import os\n"})
    _f, _u = claims(_list)
    eq((sorted(_f), false_claims(_list, _f)),
       ([("c.py", "status", "c"), ("c.py", "watchdog", "c")], [("c.py", "status", "c")]),
       "🔴 'status and the watchdog never import this': both asked, only status's import is false")
    for _verb in ("never imports", "does not import", "may not import", "must not import"):
        _t = tree({"b.py": '"""⛔ `a.py` %s this file."""\n' % _verb, "a.py": "import b\n"})
        _f, _u = claims(_t)
        eq(false_claims(_t, _f), [("b.py", "a", "b")], "🔴 '%s' is a claim" % _verb)
    _md = tree({"CLAUDE.md": "card.py never imports `fb_model` (it drags in card_fb).\n",
                "card.py": "def g():\n    import fb_model\n", "fb_model.py": "X = 1\n"})
    _f, _u = claims(_md)
    eq(false_claims(_md, _f), [("CLAUDE.md", "card", "fb_model")],
       "🔴 CLAUDE.md's 'card.py never imports `fb_model`' is read, and false here")
    _vague = tree({"b.py": '"""fb_why never imports it, and the page never imports this file."""\n',
                   "fb_why.py": "import b\n", "a.py": "X = 1\n"})
    _f, _u = claims(_vague)
    eq((_f, [s for _w, s in _u]),
       ([], ["fb_why never imports it", "the page never imports this file"]),
       "⚠️ 'it' and a subject that is not a module are reported as unread, never guessed")

    section("4. ✅ THIS REPO: EVERY LIVE IMPORT CLAIM IS TRUE")
    FOUND, UNREAD = claims(ROOT)
    for _c in sorted(FOUND):
        note("claim  %s: %s never imports %s" % _c)
    for _w, _s in UNREAD:
        note("unread %s: %s" % (_w, _s[:110]))
    ck("the reader reads this repo's own claims (dossier_fb's '`card_fb.py` does not import "
       "this file', fb_refit's 'status and the watchdog never import this')",
       ("dossier_fb.py", "card_fb", "dossier_fb") in FOUND
       and ("fb_refit.py", "watchdog", "fb_refit") in FOUND, "found %s" % sorted(FOUND))
    eq(false_claims(ROOT, FOUND), [],
       "✅ no live sentence in a top-level module or CLAUDE.md says a module never imports "
       "another that it does import (a struck claim is history: strike it, date the change)")
finally:
    for _d in _trees:
        shutil.rmtree(_d, ignore_errors=True)
