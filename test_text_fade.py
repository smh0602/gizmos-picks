#!/usr/bin/env python3
"""
🔴 TEXT IS DIMMED BY COLOUR, NEVER FADED. `[2026-10-24]`

Design I's rule (Sam, 2026-10-17): every word on every tab reads at 4.5:1 or
better (3:1 for large text). test_league_switch.py §5 measures that in a real
browser, but only on whatever rows the day's data happens to hold. On 2026-10-24
the MLB playoff card held Hard Rock ladder rungs below the -400 floor. CLAUDE.md
draws those "dimmed, never starred", and `.rung.dim{opacity:.45}` put their price
and % at 1.99:1, so browser.yml and every PR's render job went red. Nothing in the
code had changed; the data had finally shown the faint style.

⛔ THE CLASS: a style that fades text (opacity below 1, a see-through text colour, an
opacity() filter) passes every day the data happens not to show it. ✅ So this file
asks the CODE: nothing in index.html fades text. A dimmed row uses a colour token
(`--mut`, 6.21:1 on white) instead. The one exemption is a blinking mark with no text
in it: an @keyframes block named in BLINKS, whose only users are ::before/::after
boxes with `content:''`.

# @vacuity a dimmed rung faded by opacity again goes red
#   file: index.html
#   find: .rung.dim{border-style:dashed}
#   with: .rung.dim{border-style:dashed;opacity:.45}
#
# @vacuity ...and so does an inline fade on a label
#   file: index.html
#   find: <span style="font-size:11px;color:var(--mut);margin-right:2px">Conference</span>
#   with: <span style="font-size:11px;color:var(--mut);opacity:.6;margin-right:2px">Conference</span>
#
# @vacuity ...and a see-through text colour
#   file: index.html
#   find:   color:var(--mut);white-space:nowrap}
#   with:   color:rgba(15,27,45,.5);white-space:nowrap}
#
# @vacuity ...and the blink exemption stops the moment the blinking mark carries text
#   file: index.html
#   find:   border-radius:50%;background:#b3261e;margin-right:5px;vertical-align:1px;
#   with:   border-radius:50%;background:#b3261e;margin-right:5px;vertical-align:1px;content:'LIVE';
"""
import os
import re

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

# A blink on a mark with no text in it. ⛔ Never add a keyframes block here for an element
# that holds words: fade it by colour instead.
BLINKS = {"fblive": "the red live dot before a football score's time (a ::before, no text)"}


def block_end(s, i):
    """Index just past the '}' that closes the '{' at or after i."""
    j = s.index("{", i)
    depth = 0
    for k in range(j, len(s)):
        depth += {"{": 1, "}": -1}.get(s[k], 0)
        if depth == 0:
            return k + 1
    raise ValueError("unclosed block at %d" % i)


def keyframes(s):
    return {m.group(1): (m.start(), block_end(s, m.start()))
            for m in re.finditer(r"@keyframes\s+([\w-]+)\s*\{", s)}


def fades(s, allowed):
    """Every text fade in s, outside the allowed keyframes spans: (what, context)."""
    spans = [allowed[n] for n in allowed]
    inside = lambda i: any(a <= i < b for a, b in spans)
    out = []
    for m in re.finditer(r"opacity\s*:\s*([0-9]*\.?[0-9]+)", s):
        if float(m.group(1)) < 1 and not inside(m.start()):
            out.append(("opacity:" + m.group(1), s[max(0, m.start() - 50):m.end()].replace("\n", " ")))
    for m in re.finditer(r"filter\s*:\s*opacity\(\s*([0-9]*\.?[0-9]+)(%?)", s):
        v = float(m.group(1)) / (100 if m.group(2) else 1)
        if v < 1:
            out.append(("filter:opacity", s[max(0, m.start() - 50):m.end()].replace("\n", " ")))
    for m in re.finditer(r"(?<![\w-])color\s*:\s*(rgba\(([^)]*)\)|hsla\(([^)]*)\)|#[0-9a-fA-F]{8}\b|transparent)", s):
        val = m.group(1)
        alpha = 1.0
        if val.startswith(("rgba", "hsla")):
            parts = [p.strip() for p in (m.group(2) or m.group(3)).replace("/", ",").split(",")]
            if len(parts) >= 4:
                a = parts[3]
                alpha = float(a[:-1]) / 100 if a.endswith("%") else float(a)
        elif val.startswith("#"):
            alpha = int(val[7:9], 16) / 255
        else:
            alpha = 0.0
        if alpha < 1:
            out.append(("color:" + val, s[max(0, m.start() - 50):m.end()].replace("\n", " ")))
    return out


section("1. 🔴 NOTHING ON THE PAGE FADES TEXT")
kf = keyframes(PAGE)
allowed = {n: kf[n] for n in BLINKS if n in kf}
found = fades(PAGE, allowed)
ck(not found,
   "🔴 no opacity below 1, see-through text colour or opacity() filter outside a text-free blink",
   "⛔ dim a row with a colour token (--mut), never a fade: a fade passes every day the data "
   "does not show it, and fails Sam's 4.5:1 rule the day it does. Found %s" % found[:6])

section("2. ⛔ THE BLINK EXEMPTION IS REAL AND STAYS TEXT-FREE")
ck(set(allowed) == set(BLINKS),
   "   every exempted blink still exists (a dead exemption is a hole waiting to be used)",
   "missing: %s" % sorted(set(BLINKS) - set(allowed)))
for name in BLINKS:
    users = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*animation(?:-name)?\s*:[^;{}]*\b%s\b[^{}]*)\}" % re.escape(name), PAGE):
        users.append((m.group(1).strip(), m.group(2)))
    ck(users, "   %s is used by at least one rule" % name, "a blink nothing uses")
    bad = [sel for sel, body in users
           if not re.search(r"::?(before|after)\s*$", sel)
           or not re.search(r"content\s*:\s*(''|\"\")\s*;", body)
           or len(re.findall(r"content\s*:", body)) != 1]
    ck(not bad,
       "🔴 every rule that runs %s is a ::before/::after with content:'' and nothing else for content (no words to fade)" % name,
       "⛔ a blink that fades words is a text fade. Offending: %s" % bad)

section("3. ✅ THE CHECK ITSELF BITES")
_planted = ".x{opacity:.45} .y{color:rgba(0,0,0,.5)} .z{filter:opacity(50%)} .ok{opacity:1}"
ck(len(fades(_planted, {})) == 3,
   "   a planted page with three fades is caught three times, and opacity:1 is not",
   str(fades(_planted, {})))
note("exempted blinks: %s" % BLINKS)
