#!/usr/bin/env python3
"""
🔴 THE CARD NEVER PRINTED RULE 51'S GAP IN DAYS. PRE-PUBLISH CHECK 36 SAID
SO FOR WEEKS AND NOTHING ADDED IT.

`claude/card-blueprint.md` STEP 4C is not ambiguous — *"State the gap in
days on the card row."* The card printed **how many times** he had faced
them and **how many he cleared**, and never **when**. ⛔ Those are
different questions, and rule 51 is about the second one.

**WHAT RULE 51 ACTUALLY MEASURED** `[296 rematches inside 30 days, mean
gap 15.2 days]` — conditional on a first meeting of 5+ K:

    next start reaches 4+ K   vs ANYONE          1363/1826 = 74.6%
    next start reaches 4+ K   vs the SAME lineup  116/173  = 67.1%

**67.1% is just the league base rate. Whatever edge he had, they have
seen it.**

⛔ **AND IT IS A LABEL, NOT AN INPUT, AND THIS FILE ENFORCES THAT.** Rule
51's PRE-REGISTERED specification **FAILED** — it asked for a mean-K drop
≥ 0.5 with |t| ≥ 2.0 and got **0.30 with t = −1.78**. The threshold split
above was run afterwards on the same data and is **EXPLORATORY**. Folding
an exploratory result into a probability is the specification-shopping
this project has a pre-registration register to prevent. ➡️ **So the gap
is PRINTED for Sam to weigh, and it touches no number.**

⚠️ **AND THE EFFECT IS THRESHOLD-DEPENDENT, WHICH IS THE USEFUL PART:**
about **8 points** at a 4+ K bar against about **3** at 3+ K. **A rematch
is a reason to DROP A RUNG, not to drop the pitcher.**
"""
import os
import sys

from tcheck import ck, eq, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import card  # noqa: E402

print("\n═══ 1. 🔴 THE GAP IS COMPUTED, AND FROM THE MOST RECENT MEETING ═══")
eq(card.h2h_gap_days([{"d": "2026-08-30"}], "2026-09-11"), 12,
   "🔴 a single prior meeting gives the days since it")
eq(card.h2h_gap_days([{"d": "2026-07-01"}, {"d": "2026-09-05"}], "2026-09-11"),
   6,
   "🔴 ...and TWO meetings report the LATEST, not the first")
# ⛔ The order above is deliberately oldest-first. A `[0]` or a `[-1]`
#    would pass on a sorted list and lie on an unsorted one, and nothing
#    in the card guarantees this slice is sorted.
eq(card.h2h_gap_days([{"d": "2026-09-05"}, {"d": "2026-07-01"}], "2026-09-11"),
   6,
   "...and it does not depend on the list's order")

print("\n═══ 2. ⚠️ 'NEVER FACED THEM' IS A FINDING, NOT A BLANK ═══")
ck("⚠️ no prior meeting returns None rather than a number",
   card.h2h_gap_days([], "2026-09-11") is None,
   "four of the TEN ARMS CHECKED on 2026-08-21 had never faced that "
   "night's opponent — Burke, Prielipp, Manaea and Chandler. ⛔ A zero "
   "here would read as 'faced them today'")
ck("⛔ a malformed date returns None, NOT a zero-day rematch",
   card.h2h_gap_days([{"d": "not-a-date"}], "2026-09-11") is None,
   "fail to SILENT, never to a wrong number — a fabricated 0 would mark "
   "every such row as a same-day rematch and haircut it")
ck("...and a missing date field is the same",
   card.h2h_gap_days([{"o": "NYY"}], "2026-09-11") is None,
   "`.get('d')` absent must not crash the card")

print("\n═══ 3. 🔴 THE WINDOW IS THE ONE RULE 51 WAS MEASURED ON ═══")
eq(card.REMATCH_DAYS, 30,
   "🔴 30 days — 296 rematches, mean gap 15.2 days")
src = open("card.py", encoding="utf-8").read()
ck("🔴 REMATCH_DAYS is NOT in the model-constant fingerprint",
   "REMATCH_DAYS" not in open("test_model_version.py", encoding="utf-8").read(),
   "⛔ it is a LABEL threshold, not a coefficient. Adding it to that "
   "tuple would make a wording change look like a re-fit")

print("\n═══ 4. ⛔ IT IS A LABEL. IT TOUCHES NO NUMBER. ═══")
# 🔴 THE CHECK THAT MATTERS MOST IN THIS FILE. Rule 51's pre-registered
#    test FAILED; only the exploratory split survived. If a later session
#    "improves" the card by letting the gap move a probability, that is a
#    model change made without a pre-registration, and this fails.
_lines = [l for l in src.splitlines()
          if "h2h_gap" in l and not l.strip().startswith("#")]
_banned = ("blend", "model =", "confidence", "carried", "edge",
           "multiplier", "in_band", "central")
_bad = [l.strip()[:70] for l in _lines
        if any(b in l for b in _banned)]
ck("⛔ no h2h_gap value feeds blend, confidence, a band, a pair or an edge",
   not _bad,
   "rule 51's PRE-REGISTERED specification FAILED (0.30, t=-1.78) and the "
   "threshold split is EXPLORATORY — folding it into a number is fitting "
   "an exploratory result. Offending line(s): %s" % (_bad or "none"))
ck("...and the gap is stored as its own machine-readable field",
   '"h2h_gap_days": h2h_gap' in src,
   "the calibration record needs the NUMBER, not a sentence to re-parse")
ck("🔴 ...and the existing h2h sentence still leads with its old clause",
   'f"{len(h2h)} start(s) vs {ab(opp_team)} -- cleared "' in src,
   "⛔ the gap is APPENDED. No published card is re-described and nothing "
   "reading the old prefix breaks (rule 86 / the append-only record)")

print("\n═══ 5. ✅ AND THE SENTENCE READS LIKE ENGLISH ═══")
# 🔴 `CLAUDE.md`: "THE WHY IS WRITTEN FOR A READER, NOT FOR THE LEDGER" —
#    no test IDs, no t-statistics, no "rule 51". Every sentence carries a
#    number.
_sent = [l for l in src.splitlines() if "days ago" in l or "inside a month" in l]
ck("✅ the reader-facing text names the gap in plain words with a number",
   any("days ago" in l for l in _sent),
   "Sam: 'lose the technical wording' — so it says 'last one 12 days "
   "ago', not 'rule 51 rematch flag'")
ck("⛔ ...and carries no test ID, no t-statistic and no rule number",
   not any(t in " ".join(_sent) for t in ("T51", "rule 51", "t=", "STEP 4C")),
   "the jargon list in verify_card.py fails the build on these")

note("⚠️ WHAT THIS DOES NOT CLAIM: that the haircut is right. Rule 51's "
     "pre-registered test FAILED and the re-specified version is "
     "registered in `claude/owed-tests.md` for a future re-fit. ⛔ What "
     "ships today is the GAP ON THE ROW — the fact Sam asked for — and "
     "nothing that prices it.")
note("➡️ A rematch is a reason to DROP A RUNG (about 8 points at a 4+ K "
     "bar, about 3 at 3+ K), not to drop the pitcher.")
