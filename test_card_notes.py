#!/usr/bin/env python3
"""🔴 THE CARD'S OWN NOTES MUST DESCRIBE THE CARD IT SHIPS.

`[measured 2026-09-19 on picks/2026-09-18.json]` two doc-level notes in
the permanent record contradicted the 50 rows sitting beside them:

    hitter_note      "Hitter rows carry NO confidence rating and NO band."
                     …on a card whose 25 hitter rows each carry
                     `confidence` and `confidence_basis: RECORD`.
                     The card has shipped that number since 2026-08-24.

    projection_note  "…inverted through the same distribution that row
                     assumes…"
                     …describing a method RETIRED on 2026-08-27, ledger
                     rule 66, because inversion made the projection a
                     property of the ROW and 51 of 608 player-market
                     combos disagreed with themselves.

⚠️ NEITHER IS RENDERED. `index.html` uses the ROW-level notes, which are
correct and reader-facing. So this was never a falsehood on the page —
it is the permanent record describing its own columns wrongly, for 26
and 23 days respectively, in the file the calibration history is built
from. Rule 166: a sentence written down is a claim about the world, and
it goes stale.

⛔ THE RULE THIS FILE ENFORCES: a note that makes a CHECKABLE claim must
be checked against the rows in the same document. Prose that cannot be
checked is left alone; prose that can be, is.

# @vacuity 🔴 a note that contradicts its own rows is caught
#   file: card.py
#   find:             "provenance. There is no hitter model in this project, and "
#   with:             "provenance. Hitter rows carry NO confidence rating. And "
"""
import collections
import glob
import io
import json
import os
import re

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
CARDS = sorted(p for p in glob.glob(os.path.join(ROOT, "picks", "*.json"))
               if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.json", os.path.basename(p)))

ck("⚠️ there is a published MLB card to read",
   bool(CARDS),
   "⛔ rule 67 — with none of them, every check below is made about "
   "nothing. found %d" % len(CARDS))

DOC = json.load(io.open(CARDS[-1], encoding="utf-8")) if CARDS else {}
ROWS = DOC.get("picks") or []
HIT = [r for r in ROWS if r.get("confidence_basis") == "RECORD"]
PIT = [r for r in ROWS if r.get("confidence_basis") == "MODEL"]
note("newest card: %s — %d row(s), %d hitter, %d pitcher"
     % (os.path.basename(CARDS[-1]) if CARDS else "none",
        len(ROWS), len(HIT), len(PIT)))

# ════════════════════════════════════════════════════════════════════════
section("1. 🔴 WHAT THE ROWS ACTUALLY DO")
# ════════════════════════════════════════════════════════════════════════
ck("⚠️ the card has rows of both kinds to judge",
   len(HIT) >= 1 and len(PIT) >= 1,
   "⛔ rule 67. hitter=%d pitcher=%d" % (len(HIT), len(PIT)))
ck("🔴 every hitter row carries a confidence NUMBER",
   all(isinstance(r.get("confidence"), (int, float)) for r in HIT),
   "⛔ this is the fact the note denied for 26 days. missing on %d row(s)"
   % sum(1 for r in HIT if not isinstance(r.get("confidence"), (int, float))))
ck("🔴 ...and none of them carries a blend or a calibration band",
   all(r.get("blend") is None and r.get("band") is None for r in HIT),
   "⛔ ledger rule 55: a hitter row shows a number but must never claim "
   "MODEL provenance. offenders=%d"
   % sum(1 for r in HIT if r.get("blend") is not None
         or r.get("band") is not None))
proj = collections.defaultdict(set)
for r in ROWS:
    if r.get("projection") is not None:
        proj[(r.get("pid"), r.get("market"))].add(round(float(r["projection"]), 3))
    for rung in (r.get("ladder") or []):
        if isinstance(rung, dict) and rung.get("projection") is not None:
            proj[(r.get("pid"), r.get("market"))].add(
                round(float(rung["projection"]), 3))
disagree = [k for k, v in proj.items() if len(v) > 1]
ck("🔴🔴 ONE projection per player per stat, every rung of every ladder",
   not disagree,
   "⛔ this is what retired the inversion: 51 of 608 combos disagreed "
   "with themselves, worst 2.1 K. combos=%d disagreeing=%s"
   % (len(proj), disagree[:4]))

# ════════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 AND THE NOTES MAY NOT SAY OTHERWISE")
# ════════════════════════════════════════════════════════════════════════
# (field, forbidden phrase, why it is false, the measurement that says so)
CLAIMS = [
    ("hitter_note", r"carry NO confidence",
     "the card ships a hitter CONF number and has since 2026-08-24",
     lambda: len(HIT) and all(r.get("confidence") is not None for r in HIT)),
    ("hitter_note", r"NO band",
     "true of the rows, but only sayable while it stays true",
     lambda: False),          # informational: never forbidden on its own
    ("projection_note", r"invert(ed|ing|s|ion)",
     "inversion was RETIRED 2026-08-27, ledger rule 66",
     lambda: not disagree),
]
offenders = []
for field, phrase, why, contradicted in CLAIMS:
    if not contradicted():
        continue
    text = str(DOC.get(field) or "")
    if re.search(phrase, text, re.I):
        offenders.append("%s says %r — %s" % (field, phrase, why))
# ⛔ AND THIS IS A `note()`, NOT A CHECK, ON PURPOSE.
# `picks/<date>.json` is a PERMANENT RECORD and every one of these
# slates has started. `CLAUDE.md`: never edit or delete a published card
# after its games have begun. A gate on published history would be a
# gate on something nobody is allowed to fix — it could only ever be
# satisfied by breaking the rule this repo cares most about.
# ✅ THE GATE IS ON `card.py`, at the bottom of this file: the source is
# what every FUTURE card carries, and it is the only thing a correction
# can legitimately touch. The published cards are evidence of what was
# said at the time, and they stay that way.
if offenders:
    note("⚠️ the newest PUBLISHED card still carries the stale note(s): "
         "%s — left exactly as published, because it is the record"
         % "; ".join(offenders))
else:
    note("✅ the newest published card's notes agree with its rows")
ck("⚠️ ...and the notes exist at all",
   bool(DOC.get("hitter_note")) and bool(DOC.get("projection_note")),
   "⛔ deleting the note is not a way to pass this file. present: %s"
   % [k for k in ("hitter_note", "projection_note") if DOC.get(k)])
ck("⛔ the matcher would have caught the real sentences",
   bool(re.search(r"carry NO confidence",
                  "Hitter rows carry NO confidence rating and NO band.",
                  re.I))
   and bool(re.search(r"invert(ed|ing|s|ion)",
                      "inverted through the same distribution", re.I)),
   "🔴 rule 244: a matcher that does not match the defect it was written "
   "for is the emptiest kind of guard.")

# ⚠️ AND THE CURRENT TEXT IS CHECKED AGAINST THE SOURCE, not only the
#    newest card — a card is only rebuilt when a slate is open, so a
#    correction to card.py would otherwise go unverified for a day.
SRC = io.open(os.path.join(ROOT, "card.py"), encoding="utf-8").read()
_live = SRC.split('"hitter_note": (')[1].split("),")[0] if '"hitter_note": (' in SRC else ""
ck("🔴 card.py's CURRENT hitter_note does not deny the confidence number",
   bool(_live) and not re.search(r"carry NO confidence", _live, re.I),
   "⛔ the newest published card can be a day old; the source is what "
   "the next one will carry. text=%r" % _live[:120])
_lp = SRC.split('"projection_note": (')[-1].split("),")[0] if '"projection_note": (' in SRC else ""
ck("🔴 ...and its CURRENT projection_note does not claim an inversion",
   bool(_lp) and not re.search(r"invert(ed|ing|s|ion)", _lp, re.I),
   "⛔ same reason. text=%r" % _lp[:120])
