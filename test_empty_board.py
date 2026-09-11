#!/usr/bin/env python3
"""
🔴 THE EMPTY-BOARD SENTENCE WAS EXERCISED BY NOTHING ON A DAY WITH ROWS.

`[2026-09-10]` A Thursday college card with `n_priced: 0` printed **"⛔ Not
because the board is empty"** — **on a board that WAS empty.** The reader
was told the rows existed and had all been rejected for carrying no
record, when nothing had been priced at all. A false sentence on a live
page (ledger rule 179).

It was fixed. ⛔ **But look at what was guarding the fix:**

    test_drop16_fixes.py §6   if _empty:  ...  else: NOT EXERCISED
    test_top_plays.py         elif not C["picks"]:  ...

**BOTH branch on the live card.** So the day a college board prices, the
empty-board sentence is covered by **nothing at all**, and the only thing
standing between that and a repeat of the defect is which day of the week
it happens to be. `[found 2026-09-11, ledger rule 193 — and I first wrote
that `test_card_fb.py`'s fixture covered it, checked, and it does not]`

✅ **SO THE SENTENCE IS NOW A NAMED FUNCTION AND THIS FILE DRIVES BOTH
BRANCHES DIRECTLY.** No data tree, no sandbox, no card build, and
**nothing that a calendar can falsify** — which is the whole lesson of
rule 166 and its seventh instance two days ago (rule 192).

⚠️ **WHAT THIS DOES NOT REPLACE.** `test_drop16_fixes.py` still rebuilds
the real card and reads what the builder produces — that is the check
that the function is actually WIRED IN (rule 181: reading a stored
artifact tests its age, not the code). **This file tests the rule; that
one tests the plumbing.** Both are needed and neither is the other.
"""
import os
import re
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import card_fb  # noqa: E402

SLATE = "2026-09-11"
EMPTY = card_fb.empty_top_plays_sentence(SLATE, 0)
ROWS = card_fb.empty_top_plays_sentence(SLATE, 7)

print("\n═══ 1. 🔴 AN EMPTY BOARD IS NOT BLAMED ON ITS ROWS ═══")
ck("🔴 an EMPTY board never says 'Not because the board is empty'",
   "Not because the board is empty" not in EMPTY,
   "⛔ THIS IS THE 2026-09-10 DEFECT VERBATIM. It shipped to a live page "
   "and told a reader the opposite of the truth: %s" % EMPTY[:100])
ck("✅ ...it says what is actually true instead",
   "Nothing is priced for this day yet" in EMPTY,
   EMPTY[:100])
ck("⛔ ...and it does not invent a row count",
   not re.search(r"\b\d+ row\(s\) are priced", EMPTY),
   "a board with nothing on it has no rows to describe")

print("\n═══ 2. 🔴 A BOARD WITH ROWS SAYS THE OPPOSITE, AND MUST ═══")
ck("🔴 rows priced but none carrying a record DOES say it",
   "Not because the board is empty" in ROWS,
   "⛔ THE FIX FOR THE FIRST BRANCH MUST NOT DELETE THE SECOND. This "
   "sentence is TRUE here and it is the more informative of the two — "
   "the rows exist, they were judged, and they were found wanting: %s"
   % ROWS[:100])
ck("✅ ...and it names how many",
   "7 row(s) are priced" in ROWS,
   "a count the reader can check against the board in front of them")
ck("🔴 the two branches are genuinely different sentences",
   EMPTY != ROWS,
   "⛔ one message reused for two states is how the 09-10 defect read as "
   "correct for so long")

print("\n═══ 3. ✅ THE HONEST HALF SURVIVES IN BOTH ═══")
# ⛔ The 09-10 fix could have been made by deleting the awkward sentence.
#    That would have removed the REASON along with the error.
for name, text in (("empty", EMPTY), ("rows", ROWS)):
    ck("✅ the %s branch still refuses to rank by price" % name,
       "ranking by which bet pays worst" in text,
       "⛔ the reason the list is empty is a REASON, not decoration — "
       "ranking by price is ranking by which bet pays worst while "
       "calling it 'most likely to hit'")

print("\n═══ 4. ⛔ NO CALENDAR, AND NO DATA TREE ═══")
# 🔴 Rule 166, seventh instance two days ago (rule 192): a check whose
#    subject is a transient state has an expiry date and nothing expires
#    it. The slate date below is an ARGUMENT, not today.
ck("🔴 the slate date is an argument, so any date works",
   card_fb.empty_top_plays_sentence("2019-01-01", 0).startswith(
       "No top plays for 2019-01-01"),
   "⛔ this check ran identically in week 1 and will in week 15 — "
   "nothing here can be falsified by the season moving on")
src = open("card_fb.py", encoding="utf-8").read()
ck("✅ ...and the builder CALLS the function rather than inlining it",
   "empty_top_plays_sentence(slate, len(board))" in src,
   "⛔ a second copy of the sentence in the dict literal would make this "
   "whole file decorative — the exact shape of the two bugs found "
   "earlier today, where a page and a builder each held their own copy")

note("⚠️ THIS FILE TESTS THE RULE. `test_drop16_fixes.py` §6 rebuilds the "
     "real card and reads what the builder produces, which is what tests "
     "the PLUMBING (rule 181). ⛔ Neither replaces the other, and the "
     "reason this one exists is that the plumbing test can only run the "
     "branch the calendar hands it.")
