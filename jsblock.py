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

# ══════════════════════════════════════════════════════════════════════
# 🔴 THE WHOLE-PAGE READERS, for the questions that are about EVERY
# function or EVERY rule rather than one named thing.
# ⛔ THEY LIVE HERE FOR THE REASON THE MODULE EXISTS. `test_mlb_untouched.py`
# needs a brace matcher over the whole script and a rule splitter over the
# style block; growing its own would be the sixth copy of a parser this
# repo has paid for (rule 117).
# ══════════════════════════════════════════════════════════════════════
def top_level_blocks(path):
    """{name: body} for every top-level `function name(...)` on the page.

    ⛔ BRACE-MATCHED like `js_block`, never length-guessed."""
    src = source(path)
    out = {}
    for m in re.finditer(r"\n(?:async )?function ([A-Za-z_$][\w$]*)\s*\(", src):
        i = src.index("{", m.end() - 1)
        depth = 0
        for j in range(i, len(src)):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    out[m.group(1)] = src[m.start() + 1:j + 1]
                    break
    return out


def css_rules(path):
    """{selector: declarations} for every rule in every `<style>` block.

    ⚠️ NESTING-AWARE, because `@media` wraps rules in another brace pair
    and a naive split would return the media query as one enormous
    "selector" — which would make a comparison over it useless rather
    than wrong, and useless is harder to notice.
    ⛔ COMMENTS ARE STRIPPED. A comment is not a rendered rule, and a
    check that reddened on a reworded comment would be the stripped-comment
    failure in reverse (rule 244)."""
    src = source(path)
    out = {}
    for st in re.findall(r"<style>(.*?)</style>", src, re.S):
        st = re.sub(r"/\*.*?\*/", "", st, flags=re.S)
        depth, buf, sel = 0, [], None
        for c in st:
            if c == "{":
                depth += 1
                if depth == 1:
                    sel, buf = "".join(buf).strip(), []
                else:
                    buf.append(c)
            elif c == "}":
                depth -= 1
                if depth == 0:
                    if sel:
                        out.setdefault(sel, []).append("".join(buf).strip())
                    buf, sel = [], None
                else:
                    buf.append(c)
            else:
                buf.append(c)
    return {k: "\n".join(v) for k, v in out.items()}


# ══════════════════════════════════════════════════════════════════════
# 🔴 THE PAGE'S CODE WITHOUT ITS COMMENTS, AND EVERY CALL OF ONE NAME.
# ⛔ `strip_js` was test_page_plain.py's own until `[2026-10-17]`, when
# test_fetch_fresh.py needed the same question asked of every fetch on the
# page; a second copy of a parser is rule 117 again.
# ══════════════════════════════════════════════════════════════════════
def strip_js(js):
    """JavaScript with every comment removed. Strings, template literals and
    regex literals are kept as code; an HTML comment inside a template
    literal (emitted into innerHTML, never seen) is removed too."""
    out, i, n = [], 0, len(js)
    frames = [["code", 0]]
    prev = ""
    while i < n:
        kind, c = frames[-1][0], js[i]
        if kind == "code":
            if js.startswith("/*", i):
                j = js.find("*/", i + 2)
                i = n if j < 0 else j + 2
                out.append(" ")
                continue
            if js.startswith("//", i):
                j = js.find("\n", i)
                i = n if j < 0 else j
                continue
            if c == "/" and (prev == "" or prev in "(,=:[!&|?{};+-*%<>~^"):
                j, cls = i + 1, False                     # a regex literal
                while j < n and js[j] != "\n":
                    if js[j] == "\\":
                        j += 2
                        continue
                    if js[j] == "[":
                        cls = True
                    elif js[j] == "]":
                        cls = False
                    elif js[j] == "/" and not cls:
                        break
                    j += 1
                out.append(js[i:j + 1])
                i, prev = j + 1, "/"
                continue
            if c in "\"'":
                j = i + 1
                while j < n and js[j] != c and js[j] != "\n":
                    j += 2 if js[j] == "\\" else 1
                out.append(js[i:j + 1])
                i, prev = j + 1, c
                continue
            if c == "`":
                frames.append(["tpl", 0])
                out.append(c)
                i += 1
                continue
            if c == "{":
                frames[-1][1] += 1
            elif c == "}":
                if frames[-1][1] == 0 and len(frames) > 1:
                    frames.pop()
                    out.append(c)
                    i += 1
                    prev = "}"
                    continue
                frames[-1][1] -= 1
            out.append(c)
            if not c.isspace():
                prev = c
            i += 1
            continue
        if c == "\\":
            out.append(js[i:i + 2])
            i += 2
            continue
        if js.startswith("<!--", i):
            j = js.find("-->", i + 4)
            i = n if j < 0 else j + 3
            continue
        if c == "`":
            frames.pop()
            out.append(c)
            i, prev = i + 1, "`"
            continue
        if js.startswith("${", i):
            frames.append(["code", 0])
            out.append("${")
            i += 2
            prev = "{"
            continue
        out.append(c)
        i += 1
    return "".join(out)


def script_code(path):
    """The code of every `<script>` block on the page, comments removed.

    ⚠️ This repo strikes deleted code in a comment rather than removing it,
    so a whole-page question about CODE reads this, never the raw file: a
    struck `fetch(u)` in a comment is not a fetch the page makes."""
    src = source(path)
    blocks = re.findall(r"<script\b[^>]*>(.*?)</script>", src, re.S)
    return "\n".join(strip_js(b) for b in blocks)


def _skip_quoted(code, i):
    """Index just past the '...' or "..." string that starts at `i`."""
    q, j, n = code[i], i + 1, len(code)
    while j < n and code[j] != q:
        j += 2 if code[j] == "\\" else 1
    return j + 1


def _skip_template(code, i):
    """Index just past the `...` template literal that starts at `i`, its
    `${...}` substitutions included (they may hold strings and templates)."""
    j, n = i + 1, len(code)
    while j < n:
        c = code[j]
        if c == "\\":
            j += 2
            continue
        if c == "`":
            return j + 1
        if code.startswith("${", j):
            j = _skip_code(code, j + 2)
            continue
        j += 1
    raise AssertionError("unterminated template literal at %d" % i)


def _skip_code(code, j):
    """Index just past the bracket that closes the code starting at `j`."""
    depth, n = 0, len(code)
    while j < n:
        c = code[j]
        if c in "\"'":
            j = _skip_quoted(code, j)
            continue
        if c == "`":
            j = _skip_template(code, j)
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                return j + 1
            depth -= 1
        j += 1
    raise AssertionError("nothing closes the code at %d" % j)


def call_sites(code, name):
    """[(the call's text, [its top-level arguments])] for every `name(` in
    `code`, which should already be comment-free (`script_code`).

    ⛔ ARGUMENTS SPLIT ON TOP-LEVEL COMMAS ONLY: strings, template literals
    and nested brackets are skipped, so `fetch(u, {method: 'HEAD', cache:
    'no-cache'})` is two arguments, not three. `window.fetch(` is a call of
    `fetch`; `prefetch(` and `fbFetch(` are not."""
    out = []
    for m in re.finditer(r"(?<![\w$])" + re.escape(name) + r"\s*\(", code):
        end = _skip_code(code, m.end())
        inner = code[m.end():end - 1]
        args, start, j = [], 0, 0
        depth = 0
        while j < len(inner):
            c = inner[j]
            if c in "\"'":
                j = _skip_quoted(inner, j)
                continue
            if c == "`":
                j = _skip_template(inner, j)
                continue
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
            elif c == "," and depth == 0:
                args.append(inner[start:j].strip())
                start = j + 1
            j += 1
        args.append(inner[start:].strip())
        out.append((code[m.start():end], [a for a in args if a]))
    return out
