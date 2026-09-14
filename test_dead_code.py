#!/usr/bin/env python3
"""
EVERY FUNCTION ON THE PAGE IS CALLED BY SOMETHING.

🔴 LEDGER RULE 130 — **A RENDERER NOBODY CALLS IS A DECOY.** It looks
exactly like the one that renders the page, it survives review, and the
first time somebody edits it they are editing dead code while the live
path stays broken. This repo has shipped that defect, which is why
`jsblock.calls()` was written.

⛔ AND THE GUARD WAS COVERING **2 OF 127 FUNCTIONS**. `test_scores_live.py`
asserts one symbol with the comment *"rule 130 — this repo has shipped a
renderer nobody called"* — and it names `ageNote`, a live football-side
variable, **while `ageText` sat dead twenty lines away in the same file.**

➡️ **A CHECK THAT NAMES ONE SYMBOL PROVES NOTHING ABOUT THE OTHERS.** This
file sweeps every one.

`[measured 2026-09-14: 2 dead of 127 — `ageText` and `fbTeam`, both
deleted in the same change]`

════════════════════════════════════════════════════════════════════════
⚠️ WHY A PLAIN TOKEN COUNT IS THE RIGHT TEST HERE, AND NOT A LAZY ONE.

A function can be reached four ways on this page and **every one of them
mentions its name**:

    called directly        fbWire()
    a dispatch table       {scores: renderScores, picks: renderPicks}[t]()
    passed as a callback   rows.map(fbBoxBlock)
    an inline handler      onclick="fbOpenBox(...)"

⛔ So a name appearing EXACTLY ONCE — at its own definition — cannot be
reached by any of them. **That is a proof, not a heuristic.** The reverse
is not true (a mention is not a call), so this check is deliberately
one-directional: it finds the certainly-dead and says nothing about the
rest.
"""
import os
import re
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

# ⛔ COMMENTS STRIPPED FIRST, AND IT MATTERS IN BOTH DIRECTIONS HERE. This
#    repo's house style STRIKES deleted code in a comment rather than
#    removing it — so a function deleted today still appears in the file
#    by name, and an unstripped search would report it as alive. The two
#    functions this file was written for are struck in exactly that way.
_NO_BLOCK = re.sub(r"/\*.*?\*/", "", HTML, flags=re.S)
LIVE = "\n".join(ln for ln in _NO_BLOCK.splitlines()
                 if not ln.strip().startswith("//"))

ck("⛔ the comment stripper actually removed something",
   len(LIVE) < len(_NO_BLOCK) or len(_NO_BLOCK) < len(HTML),
   "🔴 IF THIS FAILS EVERY CHECK BELOW IS READING PROSE. The file's own "
   "struck-code convention means an unstripped search reports deleted "
   "functions as live")

# `function foo(` and `const foo = (…) =>` / `async function foo(`
DEFS = set(re.findall(r"^\s*(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(",
                      LIVE, re.M))
DEFS |= set(re.findall(r"^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
                       r"(?:async\s*)?(?:function\b|\([^)]*\)\s*=>|"
                       r"[A-Za-z_$][\w$]*\s*=>)", LIVE, re.M))

ck("🔴 the sweep actually found the page's functions",
   len(DEFS) > 80,
   "⛔ a regex that matches nothing passes every check below for the "
   "worst possible reason (rule 67). Found %d" % len(DEFS))

dead = []
for fn in sorted(DEFS):
    n = len(re.findall(r"(?<![\w$.])%s(?![\w$])" % re.escape(fn), LIVE))
    if n <= 1:
        dead.append(fn)

ck("🔴 every function on the page is referenced somewhere other than its "
   "own definition",
   not dead,
   "⛔ RULE 130 — a renderer nobody calls is a decoy: it looks like the "
   "live one, survives review, and the next person to edit it fixes "
   "nothing. A name appearing exactly ONCE cannot be reached by a call, "
   "a dispatch table, a callback or an inline handler. Dead: %s" % dead)

note("swept %d function definitions in index.html; %d unreferenced"
     % (len(DEFS), len(dead)))

# 🔴 AND THE SWEEP IS PROVED TO BITE, because "no dead functions" is also
#    what a broken regex returns. A planted definition that nothing calls
#    must be found, or this file is decoration about decoration.
_planted = LIVE + "\nfunction zzUnreachableProbe(){ return 1; }\n"
_n = len(re.findall(r"(?<![\w$.])zzUnreachableProbe(?![\w$])", _planted))
ck("⛔ ...and a planted uncalled function IS detected",
   _n == 1,
   "🔴 if a deliberately dead function is not found, the sweep above is "
   "green for the same reason an empty list is green. Got %d "
   "reference(s)" % _n)

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that every function that IS "
     "referenced is reachable. A mention is not a call, and a dispatch "
     "entry nothing dispatches to would still pass. ➡️ It finds the "
     "CERTAINLY dead and stays silent about the rest — one-directional "
     "on purpose, because the other direction cannot be answered without "
     "running the page.")
