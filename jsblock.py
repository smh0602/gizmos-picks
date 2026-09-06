#!/usr/bin/env python3
"""jsblock.py — THE ONE READER FOR A FUNCTION'S BODY IN `index.html`.

    from jsblock import js_block, calls

⚠️ WHY IT IS A MODULE AND NOT A COPY. `test_conf_filter.py` grew its own
brace-matcher, `test_live_scores.py` needed the same thing, and this repo
has just paid twice for duplicated parsers:
  · **five** copies of the workflow routing regex, all of which silently
    stopped matching the day an arm named two leagues (→ `wfroutes.py`)
  · **fifteen** byte-identical copies of `eq()` (→ `tcheck.py`)
⛔ A helper duplicated is a helper that breaks in the files you did not
edit. Ledger rule 117.

🔴 AND IT MATTERS MORE HERE THAN USUAL, because the thing being checked
is *whether a function is actually reached*. `[2026-09-06]` `fbScores`
carried a complete `<tr>` builder that was **defined and never called**;
the live-score wiring went into it and the tab rendered no live game
while the join worked perfectly. **Reading source is how you get fooled
by that — so the question has to be "who CALLS it", not "does it exist".**
"""
import re

_CACHE = {}


def source(path):
    if path not in _CACHE:
        _CACHE[path] = open(path, encoding="utf-8").read()
    return _CACHE[path]


def js_block(name, path):
    """The text of `function <name>(…)` through its matching close brace.

    ⛔ BRACE-MATCHED, NEVER LENGTH-GUESSED. Deleting a span by eye cost
    this project `FBTEAMS`, `NFL_LOGOS` and `nflDirectory` once, and the
    whole `fbOdds` tab a second time (rules 110 and 131)."""
    src = source(path)
    m = re.search(r"\n(?:async )?function " + re.escape(name) + r"\s*\(", src)
    assert m, "no function " + name
    i = src.index("{", m.end() - 1)
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[m.start() + 1:j + 1]
    raise AssertionError("unbalanced braces in " + name)


def calls(name, path):
    """How many times `<name>(` appears OUTSIDE its own definition.

    ⚠️ THE POINT OF THE WHOLE MODULE. A renderer nobody calls looks
    exactly like the one that renders the page (rule 130), so "is it
    defined" is the wrong question and this is the right one."""
    src = source(path)
    try:
        body = js_block(name, path)
    except AssertionError:
        body = ""
    outside = src.replace(body, "") if body else src
    return len(re.findall(r"\b" + re.escape(name) + r"\s*\(", outside))
