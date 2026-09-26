#!/usr/bin/env python3
"""🔴🔴 A WORKFLOW'S EMBEDDED PYTHON MUST STILL BE PYTHON WHEN THE SHELL
IS DONE WITH IT.

⛔ `[measured 2026-09-18, on my own unshipped work]` `self-repair.yml`
spliced a shell variable straight into a `python -c` program:

    skip = $LAST.strip()

`$LAST` is empty on the very first pass and on every pass after one that
opened a pull request — the overwhelmingly common case. An empty
expansion leaves `skip = .strip()`, which is a **SyntaxError**.

🔴 AND IT DOES NOT FAIL LOUDLY. The snippet dies, its `$(...)` capture
comes back empty, and the very next line reads that emptiness as "there
is nothing to do" and stands down. The widening it was part of would
have shipped green, passed review, and fired **never**.

➡️ **THE CLASS, NOT THE INSTANCE.** The defect is not "one line in
self-repair.yml". It is *a shell expansion standing where Python source
is expected*, and every `python -c` in every workflow can carry it. So
this derives the snippets from the workflow files and asks the question
of all of them. `[CLAUDE.md: "Ask what CLASS the defect belongs to and
guard the class where the class is answerable."]`

**THE QUESTION**, asked twice, because the two halves catch different
things:

  1. with every expansion replaced by the EMPTY string — an expansion
     that is unset, or set to "", must not change the program's shape.
     ⛔ This is the half that reddens on the real defect.
  2. with every expansion replaced by a plain VALUE — an expansion
     carrying an ordinary token must not change it either.

✅ An expansion inside a Python string literal survives both, which is
the correct way to pass one in, and the one this repo now uses in the
same file: `sys.argv[1]`.

⚠️ AND THE HEREDOCS. `python - <<PY` expands shell variables inside the
program body; `python - <<'PY'` does not. The quoted form is the only
safe one, so it is the only one allowed.

⚠️ No network, no credits, no subprocess. It reads the workflow files off
disk and calls `ast.parse`.
"""
import ast
import glob
import os
import re
import sys
import textwrap

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(ROOT, ".github", "workflows")


# ══════════════════════════════════════════════════════════════════════
# @vacuity a shell expansion spliced into embedded python source is caught
#   file: .github/workflows/self-repair.yml
#   find: since = sys.argv[1]
#   with: since = $SINCE
# ⚠️ Re-pointed 2026-09-26: `skip = sys.argv[1].strip()` left this file
#    when #184's triage moved into self_repair.py, and the declaration
#    rotted the moment Sam uploaded it (collect #1856). Same intent: a
#    shell variable standing where the snippet reads sys.argv[1].
# ══════════════════════════════════════════════════════════════════════

# ⚠️ `${{ ... }}` FIRST. GitHub's own expression syntax is substituted
#    before the shell ever sees the line, and it is a superset spelling
#    of `${...}` — matched first so it is never half-eaten.
_SH = re.compile(r"\$\{\{[^}]*\}\}|\$\{[A-Za-z_][A-Za-z0-9_]*\}"
                 r"|\$[A-Za-z_][A-Za-z0-9_]*")
_OPEN = re.compile(r'python3?\s+-c\s+"')
_HEREDOC = re.compile(r"python3?\s+-\s*<<(-?)\s*(\S+)")


def _snippets(path):
    """Every `python -c "…"` program in one workflow file, as (line, source).

    ⛔ Both spellings, because both are in use: the one-liner that closes
    its quote on the same line, and the block whose body runs down the
    YAML until a line that opens with the closing quote.
    """
    lines = open(path, encoding="utf-8").read().split("\n")
    out, i = [], 0
    while i < len(lines):
        m = _OPEN.search(lines[i])
        if not m:
            i += 1
            continue
        rest = lines[i][m.end():]
        if '"' in rest:
            out.append((i + 1, rest[:rest.index('"')]))
            i += 1
            continue
        body, j = [], i + 1
        while j < len(lines) and not lines[j].lstrip().startswith('"'):
            body.append(lines[j])
            j += 1
        out.append((i + 1, textwrap.dedent("\n".join(body))))
        i = j + 1
    return out


_FILES = sorted(glob.glob(os.path.join(WF, "*.yml")))
_ALL = [(os.path.basename(p), ln, src)
        for p in _FILES for ln, src in _snippets(p)]

section("1. ⚠️ THE SNIPPETS ARE DERIVED FROM THE WORKFLOWS, NOT LISTED")

ck(len(_FILES) >= 5,
   "⚠️ the workflow files were found (%d)" % len(_FILES),
   "⛔ an empty directory would make every sweep below pass having "
   "checked nothing — rule 67. Got %s"
   % [os.path.basename(p) for p in _FILES][:6])

# ⛔ RULE 67 AGAIN, ONE LEVEL DOWN: the files can exist and the extractor
#    still find nothing, if its pattern drifts from how the YAML is
#    written. A sweep over zero snippets is a green tick over no question.
ck(len(_ALL) >= 8,
   "🔴 the extractor actually FINDS embedded python (%d snippet(s))"
   % len(_ALL),
   "⛔ if this falls to zero the checks below are vacuous — the pattern "
   "has drifted from the YAML, and that is a bug in THIS file. Got %s"
   % sorted({f for f, _, _ in _ALL}))

# ⚠️ AND THE EXTRACTOR AGREES WITH A DUMB COUNT OF THE OPENINGS, so it
#    cannot quietly skip one. A snippet it never returns is a snippet
#    nothing asks about.
_RAW = sum(len(_OPEN.findall(open(p, encoding="utf-8").read())) for p in _FILES)
ck(_RAW == len(_ALL),
   "⚠️ every `python -c` opening in the workflows became a snippet",
   "⛔ a snippet the extractor drops is one this file silently exempts. "
   "openings=%d extracted=%d" % (_RAW, len(_ALL)))

section("2. 🔴🔴 AN EMPTY EXPANSION MUST NOT BREAK THE PROGRAM")

_broke_empty = []
for fname, ln, src in _ALL:
    try:
        ast.parse(_SH.sub("", src))
    except SyntaxError as e:
        _broke_empty.append("%s:%d (%s)" % (fname, ln, e.msg))

ck(not _broke_empty,
   "🔴🔴 NO SHELL EXPANSION STANDS WHERE PYTHON SOURCE IS EXPECTED",
   "⛔ an unset or empty variable turns this program into a SyntaxError, "
   "and a dead `$(...)` returns the empty string rather than failing — "
   "so the step around it reads 'nothing to do' and carries on green. "
   "✅ Pass the value as an ARGUMENT (`sys.argv[1]`) or put it inside a "
   "string literal. Broken: %s" % _broke_empty)

section("3. ⚠️ ...AND NEITHER MAY AN ORDINARY VALUE")

_broke_value = []
for fname, ln, src in _ALL:
    try:
        ast.parse(_SH.sub("gizmo", src))
    except SyntaxError as e:
        _broke_value.append("%s:%d (%s)" % (fname, ln, e.msg))

ck(not _broke_value,
   "⚠️ a plain token in every expansion still leaves valid python",
   "⛔ the other half of the same defect: the program parses when the "
   "variable is empty but not when it is set, or vice versa. Either way "
   "the shape of the program depends on a runtime value. Broken: %s"
   % _broke_value)

section("4. ⚠️ AND A HEREDOC BODY IS QUOTED, SO THE SHELL KEEPS OUT")

_unquoted = []
for p in _FILES:
    for m in _HEREDOC.finditer(open(p, encoding="utf-8").read()):
        delim = m.group(2)
        if not (delim.startswith("'") or delim.startswith('"')):
            _unquoted.append("%s: <<%s" % (os.path.basename(p), delim))

ck(not _unquoted,
   "⚠️ every `python - <<X` heredoc quotes its delimiter",
   "⛔ an UNQUOTED delimiter expands `$VAR` inside the program body — the "
   "same defect as section 2, in the spelling where it is invisible. "
   "✅ Write `<<'PY'`, and pass values as arguments. Unquoted: %s"
   % _unquoted)

note("swept %d embedded python snippet(s) across %d workflow file(s)"
     % (len(_ALL), len(_FILES)))
