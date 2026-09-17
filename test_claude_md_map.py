#!/usr/bin/env python3
"""
`CLAUDE.md`'s MAP MUST NAME EVERY MODULE, BECAUSE IT IS ALL A FRESH
SESSION CAN READ.

🔴🔴 `CLAUDE.md` says it itself: *"a session connected only to the repo
has CLAUDE.md and nothing else of his."* So the "What lives where" block
is not documentation in the ordinary sense — it is the ONLY index of this
repo that an Actions session ever sees.

⛔ `[measured 2026-09-17]` **20 of the 30 top-level modules were missing
from it** — `freshness.py`, `possession.py`, `ranking.py`, `wfroutes.py`,
`tcheck.py`, both budget watchers, both owed tests, the football grader,
the dossier builder and more. Every one of them is a thing a fresh
session could not find, and four of them are explicitly SHARED HELPERS
that exist so nobody writes a second copy.

➡️ **RULE 117 IS WHAT THIS PROTECTS.** A helper duplicated breaks in the
file you did not edit, and the cheapest way to cause that is to hide the
first copy from the person about to write the second.

⚠️ AND IT IS A LIST, SO RULE 166 APPLIES: a list written down is a claim
about the world and it goes stale. This derives the modules from the repo
and compares, exactly as `test_watchdog.py` does for the cron total.
⛔ IF THIS FAILS, ADD THE LINE. The map is the thing to edit, not this.
"""
import glob
import os
import sys

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════════════
# @vacuity every top-level module must be named in CLAUDE.md's map
#   file: CLAUDE.md
#   find: possession.py     ONE implementation of the possession coverage/share
#   with: possessionXX.py   ONE implementation of the possession coverage/share
# ══════════════════════════════════════════════════════════════════════

_MD = open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8").read()
_MODS = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "*.py"))
               if not os.path.basename(p).startswith("test_"))

section("1. 🔴🔴 EVERY TOP-LEVEL MODULE IS NAMED IN THE MAP")
ck(len(_MODS) >= 20,
   "⚠️ the module list is DERIVED from the repo (%d module(s))" % len(_MODS),
   "⛔ an empty list would make the sweep below pass having checked "
   "nothing (rule 67). Got %s" % _MODS[:5])
_missing = [m for m in _MODS if m not in _MD]
ck(not _missing,
   "🔴🔴 NOTHING A FRESH SESSION COULD NOT FIND",
   "⛔ `CLAUDE.md` is the ONLY index an Actions session ever reads, and a "
   "module missing from it is a module somebody writes a second copy of "
   "(rule 117). Add the line to the map — this file is not the thing to "
   "edit. Missing: %s" % _missing)

section("2. ⚠️ AND THE SHARED HELPERS SAY THEY ARE SHARED")
# ⛔ Naming a helper is not enough. The whole reason `ranking.py`,
#    `wfroutes.py`, `jsblock.py`, `tcheck.py` and `possession.py` exist as
#    separate files is that the repo had FIVE hand-rolled copies of the
#    routing regex once. The map has to say so, or it reads like a
#    directory listing.
_block = _MD[_MD.index("## What lives where"):]
ck("Rule 117" in _block or "rule 117" in _block,
   "🔴 the map names the rule the shared helpers exist for",
   "⛔ a list of filenames does not tell a fresh session that copying "
   "one is the mistake")
for _h in ("ranking.py", "wfroutes.py", "jsblock.py", "possession.py"):
    ck(_h in _block, "   %s is in the map" % _h,
       "⛔ this is one of the ONE-COPY helpers")

section("3. ⛔ THE MAP MUST NOT NAME A FILE THAT DOES NOT EXIST")
# 🔴 THE OTHER DIRECTION, and it is the one that rots silently: a map
#    entry for a deleted module sends the next session looking for
#    something that is not there, which is worse than no entry at all.
_named = []
for _line in _block.split("\n"):
    _w = _line.strip().split()
    if _w and _w[0].endswith(".py") and "/" not in _w[0]:
        _named.append(_w[0])
_ghosts = sorted({n for n in _named
                  if not os.path.exists(os.path.join(ROOT, n))})
ck(_named, "⚠️ the map really does name modules (%d)" % len(_named),
   "⛔ a map nothing was read out of would pass this section blind")
ck(not _ghosts,
   "🔴 every module the map names actually exists",
   "⛔ an entry for a deleted file sends the next session hunting for "
   "something that is not there. Ghosts: %s" % _ghosts)
note("📌 WHAT THIS DOES NOT CLAIM: that the one-line description beside "
     "each module is accurate or current. It claims only that the module "
     "is FINDABLE — which is the half a fresh session cannot recover on "
     "its own.")
