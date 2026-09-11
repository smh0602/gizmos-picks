#!/usr/bin/env python3
"""
🔴 ONE CEILING, AND THE CODE SAYS IT ONCE.

`card.py` contradicted itself from **2026-08-26 until 2026-09-11**, and
every scheduled grading run re-reported it for sixteen days:

    parlay_rule prose   1.8x - 2.2x      (from PARLAY_BANDS)
    in_band flag        mult <= 2.10     (from TARGET)

**A pair at 2.15x was ABOVE BAND to the flag and INSIDE BAND to the same
card's own sentence.** `claude/pick-ledger.md` rule 28 says plainly that
an interactive session must pick one, because a headless run can neither
test nor push.

✅ **IT IS PICKED, AND IT IS NOT A JUDGMENT CALL.** Rule 28 OWNS the
bands and records Sam's own instruction of 2026-08-26 — *"two-mans in
1.8x-2.2x, three- and four-mans in 3x-6x"*:

    2 LEGS -> 1.80x - 2.20x
    3 LEGS -> 3.00x - 6.00x
    4 LEGS -> 3.00x - 6.00x

`PARLAY_BANDS` already matched that. **Only the flag was stale**, so the
fix is to compute the flag FROM the band it prints — after which the two
cannot drift apart again.

⛔ **WHAT DID NOT CHANGE, AND MUST NOT:**
  - **1.80 is a HARD FLOOR.** A pair below it is never shown — not
    printed, not labelled, not listed as declined. Sam: *"i dont want to
    see them at all"*. That gate is `mult < FLOOR` and is untouched.
  - **2.10 is a SOFT TARGET, never a cap** (rule 28). An above-band pair
    that is a good bet is still SHOWN and labelled ABOVE BAND. This
    changes a LABEL, not what reaches the page.
  - **NO HISTORY IS RE-GRADED.** Every INSIDE-BAND / ABOVE-BAND subtotal
    in `pick-ledger.md` was computed on the 2.1x flag and stays that way;
    the ledger says so on its own rows.

⚠️ AND A SECOND, QUIETER BUG WENT WITH IT: the three- and four-leg flag
read `(size != 2)`, which is UNCONDITIONALLY TRUE — so a 3-leg at 2.5x,
below its own 3.00 floor, was labelled IN BAND. Every size is now judged
against its own band.
"""
import os
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import card  # noqa: E402

print("\n═══ 1. 🔴 THE BANDS ARE RULE 28'S, IN ONE PLACE ═══")
ck("🔴 the two-leg band is Sam's 2026-08-26 instruction",
   card.PARLAY_BANDS[2] == (1.80, 2.20),
   "1.80-2.20 — ledger rule 28 owns this and the code must not hold a "
   "second opinion")
ck("...and the multi-leg bands are his too",
   card.PARLAY_BANDS[3] == (3.00, 6.00)
   and card.PARLAY_BANDS[4] == (3.00, 6.00),
   "3x-6x for three- and four-mans")
ck("⛔ the 1.80 HARD FLOOR is unchanged",
   card.FLOOR == 1.80,
   "a pair below it is never shown — Sam: 'i dont want to see them at "
   "all'")
src = open("card.py", encoding="utf-8").read()
# ⛔ ASSERT ON THE ASSIGNMENT, NOT ON THE WHOLE FILE. The first form of
#    this read `"<= TARGET" not in src` and FAILED — on the "do not
#    reintroduce `mult <= TARGET`" warning in the comment four lines
#    above the fix. A bare substring search over a source file reads the
#    PROSE as if it were code, which is the trap this repo has three
#    dead comment-strippers to show for.
# ✅ `test_scores_live.py` already owns the one stripper that works — a
#    FOURTH attempt after three wrong ones — and a fifth copy here would
#    be worse than the check it serves. So this asks the exact question
#    instead: does any `in_band` ASSIGNMENT mention TARGET?
import re  # noqa: E402
_in_band_lines = [l for l in src.splitlines()
                  if re.search(r'"in_band"\s*:', l)]
ck("🔴 no in_band ASSIGNMENT is computed against TARGET any more",
   _in_band_lines and not any("TARGET" in l for l in _in_band_lines),
   "⛔ TARGET is the SOFT TARGET (2.10, the 47.6%% break-even landmark), "
   "not a band edge — using it as one WAS the bug. Found %d in_band "
   "assignment(s): %s" % (len(_in_band_lines),
                          [l.strip()[:46] for l in _in_band_lines]))
ck("...and the pairs path reads the band rather than copying it",
   "_P2_LO, _P2_HI = PARLAY_BANDS[2]" in src,
   "a third copy of the numbers is a third thing to drift")


def leg(name, price, gid, pid):
    return {"pitcher": name, "side": "over", "line": 5.5,
            "market": "strikeouts", "price": price, "blend": 80.0,
            "model": 80.0, "raw": 80.0, "carried": 80.0, "band": "70-80",
            "game": "A@B", "game_id": gid, "book": "hardrockbet",
            "edge": 5.0, "kind": "pitcher", "on_hardrock": True,
            "pid": pid, "clears_price_floor": True}


def pair_at(target):
    """Two real prices whose decimals multiply nearest `target`."""
    best = None
    for p1 in range(-400, 300, 5):
        for p2 in range(-400, 300, 5):
            if not p1 or not p2:
                continue
            m = card.decimal(p1) * card.decimal(p2)
            if best is None or abs(m - target) < abs(best[2] - target):
                best = (p1, p2, m)
    p1, p2, _ = best
    return card.build_pairs([leg("A", p1, "g1", 1), leg("B", p2, "g2", 2)],
                            limit=4)


print("\n═══ 2. 🔴 DRIVEN THROUGH THE REAL build_pairs() ═══")
# ⛔ The documented case, verbatim from rule 28: "a pair at 2.15x is
#    ABOVE BAND to the flag and INSIDE BAND to the same file's prose".
rows = pair_at(2.15)
ck("🔴 THE CONTRADICTION CASE — 2.15x is now IN BAND",
   bool(rows) and rows[0]["in_band"] and rows[0]["label"] == "IN BAND",
   "%s — the flag and the prose finally agree"
   % (rows[0]["multiplier"] if rows else "no pair built"))

rows = pair_at(2.05)
ck("✅ ...and a pair that was always in band still is",
   bool(rows) and rows[0]["in_band"],
   "%s — the fix widens the label, it does not invert it"
   % (rows[0]["multiplier"] if rows else "no pair built"))

rows = pair_at(2.25)
ck("⛔ ...while ABOVE the band is still ABOVE BAND",
   bool(rows) and not rows[0]["in_band"]
   and rows[0]["label"] == "ABOVE BAND",
   "%s — 2.20 is the edge, so this is not a licence to relabel "
   "everything" % (rows[0]["multiplier"] if rows else "no pair built"))

rows = pair_at(1.79)
ck("🔴 ...and BELOW 1.80 is still NOT SHOWN AT ALL",
   rows == [],
   "⛔ the hard floor is the one thing that suppresses, and it is "
   "untouched — not printed, not labelled, not declined")

print("\n═══ 3. ⚠️ AND EVERY SIZE IS JUDGED AGAINST ITS OWN BAND ═══")
# 🔴 `(size != 2)` made in_band unconditionally TRUE for 3- and 4-leg
#    tickets, so a 3-leg BELOW its own 3.00 floor was labelled IN BAND.
ck("🔴 the multi-leg flag is no longer unconditionally true",
   "(size != 2) or" not in src,
   "a 3-leg at 2.5x is below its own 3.00 floor and was called IN BAND")
ck("...it is computed from that size's own band",
   "lo <= mult <= hi" in src,
   "one expression, every size, read off PARLAY_BANDS")

note("⛔ THIS CHANGES A LABEL, NOT WHAT REACHES THE PAGE. The 1.80 hard "
     "floor still suppresses, an above-band pair that is a good bet is "
     "still shown (rule 28: 2.10 is a SOFT TARGET, never a cap), and NO "
     "graded row or published INSIDE/ABOVE subtotal is recomputed — "
     "history was graded on the 2.1x flag and stays that way.")
