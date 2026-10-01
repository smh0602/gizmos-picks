#!/usr/bin/env python3
"""
🔴 THE PRICED FLAG SITS ON EXACTLY THE ROWS THE CARD PRICED.

`[Sam, 2026-10-01]` From 20:11Z on 10/01 every MLB card rebuild was
reverted: `verify_card.py` asked ~~"is the priced flag a subset of the
index, not a rubber stamp (0 < flagged < whole index)"~~, and that night
the board held only games that had not started, every prop on it was
priced, and 436 of 436 entries were CORRECTLY flagged. The check asked
about the board's makeup, not the card.

✅ The question now: the flag (`"p"` on a projection entry) sits on exactly
the rows `card.main()` priced (`card.LAST_PRICED_ROWS`, in memory) -- no
stray flag, no missing one, at least one priced row.

THE RULE IS RUN FROM `verify_card.py` ITSELF: its own lines, between the
`_MKT_FEED` line and the next check, are executed on planted cards (the
way test_verify_card.py runs section 39). One copy of the rule, no data
tree, no clock. ⛔ If the markers move, the block is empty and the first
check says so -- it can never pass on nothing.

# @vacuity 🔴 a correct ALL-PRICED card passes (the question is the card, not the board)
#   file: verify_card.py
#   find:    bool(_pexp) and not _stray and not _missed,
#   with:    0 < len(_pkeys) < len(_pxall),
#
# @vacuity a flag on a row that was never priced fails
#   file: verify_card.py
#   find: _stray, _missed = sorted(_pkeys - _pexp), sorted(_pexp - _pkeys)
#   with: _stray, _missed = [], sorted(_pexp - _pkeys)
#
# @vacuity a priced row that lost its flag fails
#   file: verify_card.py
#   find: _stray, _missed = sorted(_pkeys - _pexp), sorted(_pexp - _pkeys)
#   with: _stray, _missed = sorted(_pkeys - _pexp), []
#
# @vacuity a card that priced nothing does not pass on an empty match
#   file: verify_card.py
#   find:    bool(_pexp) and not _stray and not _missed,
#   with:    not _stray and not _missed,
"""
import copy
import os
import sys
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section  # noqa: E402

import card  # noqa: E402

NAME = "the priced flag sits on exactly the rows the card priced"
SRC = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
_A, _B = "_MKT_FEED = {", 'ck("the price gate actually excluded something'
BLOCK = (SRC[SRC.index(_A):SRC.index(_B)]
         if _A in SRC and _B in SRC and SRC.index(_A) < SRC.index(_B) else "")


def verdict(doc, priced, t10=(), carded=()):
    """verify_card.py's own priced-flag lines on a planted card -> ok?"""
    got = {}

    def _ck(name, ok, detail=""):
        if name.startswith(NAME):
            got["ok"] = bool(ok)
    exec(compile(BLOCK, "verify_card.py#priced-flag", "exec"),
         {"doc": doc, "_t10": list(t10), "allrows": list(carded), "ck": _ck,
          "print": lambda *a, **k: None,
          "C": types.SimpleNamespace(LAST_PRICED_ROWS=list(priced))})
    return got.get("ok")


def row(pid, market, side="over", line=0.5, kind="hitter"):
    return {"pid": pid, "market": market, "side": side, "line": line, "kind": kind,
            "projection": 1.0, "projection_unit": "u", "projection_basis": "MODEL",
            "confidence": 70, "player": "P%d" % pid}


# Priced rows, indexed the way card.main() indexes them (its own function);
# DESCRIPTIVE entries, the way the board pass writes them (no "p").
PRICED = [row(1, "batter_hits"), row(2, "batter_rbis", "under"),
          row(3, "strikeouts", "over", 5.5, "pitcher")]
DESCR = {"8|batter_hits|over|0.5": {"v": 0.9, "u": "H", "b": "D"},
         "9|batter_total_bases|under|1.5": {"v": 1.2, "u": "TB", "b": "D"}}
BOTH = {"projections": {**DESCR, **card.projection_index(PRICED, priced=True)}}
ALL = {"projections": card.projection_index(PRICED, priced=True)}

section("0. THE RULE IS verify_card.py's OWN, AND IT WAS FOUND")
ck("the block was cut out of verify_card.py and holds the check",
   NAME in BLOCK and "LAST_PRICED_ROWS" in BLOCK,
   "%d characters between the markers" % len(BLOCK))

section("1. ✅ A CORRECT CARD PASSES, WHATEVER THE BOARD HOLDS")
ck("a card with both kinds (priced and descriptive entries) passes",
   verdict(BOTH, PRICED) is True)
_pk = sum(1 for v in ALL["projections"].values() if v.get("p"))
note("all-priced card: %d of %d entries flagged -- the old form "
     "(0 < flagged < index) called this a failure" % (_pk, len(ALL["projections"])))
ck("🔴 a card where EVERY projection is priced passes (10/01 20:11Z)",
   verdict(ALL, PRICED) is True and _pk == len(ALL["projections"]))

section("2. 🔴 A MIS-FLAGGED ROW FAILS, EITHER WAY ROUND")
stray = copy.deepcopy(BOTH)
stray["projections"]["8|batter_hits|over|0.5"]["p"] = 1
ck("🔴 a flag on a row the card never priced fails", verdict(stray, PRICED) is False)
lost = copy.deepcopy(ALL)
lost["projections"]["2|batter_rbis|under|0.5"].pop("p")
ck("🔴 a priced row that lost its flag fails", verdict(lost, PRICED) is False)
ck("a card that priced nothing fails, even with nothing flagged",
   verdict({"projections": copy.deepcopy(DESCR)}, []) is False)
