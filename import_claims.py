#!/usr/bin/env python3
"""import_claims.py — the sentences in this repo that say one module never imports another.

`[2026-11-20]` fix/pitcher-correction-wording gave football its price-words guard
(`card_fb.row_reads_price`), which imports the game model and the props model inside the
function, while both files' docstrings still said, as a ⛔ rule, that card_fb never imports
them. A fresh session reads a ⛔ line as a rule. ⚠️ ROOT CAUSE: an import claim is prose, and
nothing compared it with the imports. `test_import_claims.py` does, through this reader.

✅ THE CLASS: every top-level `.py` and CLAUDE.md, struck text (~~...~~) dropped and comment
lines joined; a CLAIM is "<A> [, / and / or <B> ...] <verb> <C>", the verb one of never
import(s), does / do / may / must / will not import, doesn't / don't / won't import, when every
name kept is a module in the top level (`x.py`, a backticked name, "the x"); the object "this
file", "this module" or a bare "this" before punctuation is the file that says it.
⚠️ NEVER GUESSED: "it", a subject that is not a module, or "this file" in CLAUDE.md is returned
as UNREAD (printed by the test), never resolved. A passive "parsed, never imported" names no
subject and is not a claim here.
⛔ The imports themselves are read by tcheck's ONE reader (`_imports_of`, rule 117), handed in
by the test, so this file stays stdlib only and never imports the harness.
"""
import os
import re

THIS = "import_claims.py"
TEST = "test_import_claims.py"
VERB = (r"(?:never\s+imports?|"
        r"does\s+not\s+import|do\s+not\s+import|doesn't\s+import|don't\s+import|"
        r"may\s+not\s+import|must\s+not\s+import|will\s+not\s+import|won't\s+import)")
NAME = r"(?:the\s+)?`?[A-Za-z_]\w*(?:\.py)?`?"
SEP = r"(?:\s*,\s*|\s+and\s+|\s+or\s+)"
OBJ = r"(this\s+file\b|this\s+module\b|this(?=\s*[^\w\s`])|`?[A-Za-z_]\w*(?:\.py)?`?)"
CLAIM = re.compile(r"((?:%s%s)*%s)\s+(%s)\s+%s" % (NAME, SEP, NAME, VERB, OBJ), re.I)
HAS_VERB = re.compile(VERB, re.I)
STRUCK = re.compile(r"~~.*?~~")


def flat(src):
    """`src` as one line: a comment continued on the next line joined, struck text dropped."""
    t = re.sub(r"\n[ \t]*#+[ \t]?", " ", src)
    t = re.sub(r"\s+", " ", t)
    return STRUCK.sub(" ", t)


def bare(word):
    """'the watchdog' / a backticked `x.py` / `x` -> the module name x."""
    w = re.sub(r"^the\s+", "", word.strip(), flags=re.I).strip("`")
    return w[:-3] if w.endswith(".py") else w


def claims(root, skip=(THIS, TEST)):
    """Every import claim in `root`'s top level -> (found, unread).

    found = [(file, subject, object)], both modules in `root`; unread = [(file, sentence)]
    for a sentence with the verb that this reader could not resolve (never guessed)."""
    mods = {f[:-3] for f in os.listdir(root) if f.endswith(".py")}
    found, unread = [], []
    for f in sorted(os.listdir(root)):
        if f in skip or not (f.endswith(".py") or f == "CLAUDE.md"):
            continue
        try:
            src = open(os.path.join(root, f), encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        t = flat(src)
        if not HAS_VERB.search(t):
            continue
        own = f[:-3] if f.endswith(".py") else None
        for m in CLAIM.finditer(t):
            subj = [n for n in (bare(x) for x in re.findall(NAME, m.group(1), re.I)) if n in mods]
            o = m.group(3)
            obj = own if o.lower().startswith("this") else bare(o)
            if subj and obj in mods:
                found.extend((f, s, obj) for s in subj if s != obj)
            else:
                unread.append((f, m.group(0)))
    return found, unread


def false_claims(root, found, imports_of):
    """The claims the code contradicts -> [(file, subject, object)]: the subject's own source
    imports the object. `imports_of(path)` -> module names (tcheck's `_imports_of`)."""
    def imported(mod):
        return {m.split(".")[0] for m in imports_of(os.path.join(root, mod + ".py"))}
    return [c for c in found if c[2] in imported(c[1])]
