#!/usr/bin/env python3
"""test_price_words.py — the words under a number never say a price made it when the method
that made it reads none, all three leagues.

`[Sam, 2026-10-11]` *"i just want the model to pick its OWN picks by itself, nothing more nothing
less. ... only show confidence score on each pick that the model picks, BASED ON THE MODELS
CONFIDENCE SCORE NOT THE SPORTSBOOKS"*. From that switch MLB pitcher rows print C1, the blend
corrected by its own past misses with NO price (`mlb_pitcher_cal.SHIPPED`), and football's props
model's stage 2 takes no price (`fb_props_model.s2_features`).
`[2026-11-19]` Found: every C1 card from 2026-10-12 to 10-28 still said its pitcher rows were
"corrected against the price" (the note) and "Before checking it against the price it read X%"
(the why, on the page). The words now come from the method (`card.correction_words`, asked of
`mlb_pitcher_cal.reads_price`); published cards keep theirs (permanent).

Planted rows and planted cards only; nothing here reads the live data tree or the clock.
  1. ONE list (`plain_why.PRICE_INPUT`) catches every sentence that said a price or the books'
     chance made a number, and never one that only says which bet is priced and its break-even.
  2. `mlb_pitcher_cal.reads_price` is asked of the code the card prints through
     (`corrected()`), never a list: C1 no, C2 yes, D YES (`[2026-11-20]` the card prints D
     through `corrected()`, whose inputs are the blend and the price; ~~D no~~ asked
     `walk_forward`'s `smoothed`, which the card never prints), the plain blend no; a price put
     into C1's inputs turns it yes, a `corrected()` that drops the price turns C2's no, a method
     that prints nothing without a price reads it; an unscored method raises.
  3. The MLB pitcher rows card.py builds: under C1 the note and why name no price and keep the
     number before the correction; under C2 (SHIPPED patched) they say "against the price",
     which is then true; the break-even and Hard Rock sentences stay; no number moves.
     `[2026-11-20]` EVERY scored method, each at two prices: its words name the price exactly
     when its printed number moves with the price (D included: 59.8 at -120, 54.8 at +150).
  4. `card.price_claims`: every list of a card this code built, never a published one; a row
     whose method reads the price (C2, D) may say so. The walk is `plain_why.price_claims`,
     football's too (`card_fb.price_claims`, §6).
  5. verify_card.py's own lines on planted cards: the rewritten note check and the class guard,
     red on the old words under C1, green on the new, the old question on a published card,
     red on a new card that lost its stamp.
  6. Football: `fb_props_model.stage2_reads_price` is asked of s2_features (no price since
     10-11; a price input added turns it yes, and any new input stops this file until someone
     says whether it is one); fb_why's chance sentences name no price. `[2026-11-20]` The game
     model's fits are asked too (`fb_model.features_read_price`), and `card_fb.price_claims`
     walks every list of a planted football card: the board, the liked lists, the game lines,
     the alternate spreads, the top plays, `why_card` included; MARKET may name the books.

# @vacuity 🔴 a C1 note never says "corrected against the price" again
#   file: card.py
#   find: return ("then corrected by how often our pitcher plays on earlier cards actually hit; "
#   with: return ("then corrected against the price by how often our pitcher plays on earlier cards actually hit; "
#
# @vacuity 🔴 ...nor its why "Before checking it against the price"
#   file: card.py
#   find: "Before correcting it by our pitcher picks' own record")
#   with: "Before checking it against the price")
#
# @vacuity 🔴 the words follow the method, not a fixed sentence
#   file: card.py
#   find:     if pcal.reads_price(method):
#   with:     if True:
#
# @vacuity 🔴 the why is told the row's method
#   file: card.py
#   find: oppRank, central, shown=shown, method=conf_method),
#   with: oppRank, central, shown=shown),
#
# @vacuity 🔴 reads_price is asked of the code, never a typed answer
#   file: mlb_pitcher_cal.py
#   find:     return at[0] != at[1] or bare is None
#   with:     return method == "C2"
#
# @vacuity 🔴 [2026-11-20] D is answered by the path the card prints through, never walk_forward's smoothed()
#   file: mlb_pitcher_cal.py
#   find:     return at[0] != at[1] or bare is None
#   with:     return (smoothed({"model": .6, "h": 7, "n": 12, "be": .45}) != smoothed({"model": .6, "h": 7, "n": 12, "be": .58})) if method == "D" else (at[0] != at[1] or bare is None)
#
# @vacuity 🔴 [2026-11-20] ...asked of corrected() itself, not of features() beside it
#   file: mlb_pitcher_cal.py
#   find:     at = [corrected(probe, "probe", 62.0, be, method=method) for be in (45.0, 58.0)]
#   with:     at = [features({"blend": 0.62, "be": be / 100.0}, method) for be in (45.0, 58.0)]
#
# @vacuity 🔴 [2026-11-20] a method that prints nothing without a price reads the price
#   file: mlb_pitcher_cal.py
#   find:     return at[0] != at[1] or bare is None
#   with:     return at[0] != at[1]
#
# @vacuity 🔴 [2026-11-20] corrected() prints the method it is asked about
#   file: mlb_pitcher_cal.py
#   find:     method = SHIPPED if method is _AS_SHIPPED else method
#   with:     method = SHIPPED
#
# @vacuity 🔴 a card published before the change is never checked
#   file: card.py
#   find:     if not isinstance(doc, dict) or doc.get("own_number_rule") != OWN_NUMBER_RULE:
#   with:     if not isinstance(doc, dict):
#
# @vacuity 🔴 every list the card holds is walked, not only the board
#   file: plain_why.py
#   find:                 if k not in ROW_TEXT:
#   with:                 if k == "picks":
#
# @vacuity 🔴 a row whose method reads the price may say so (a guard that fires on true words fails too)
#   file: plain_why.py
#   find:             if ("confidence" in x or "confidence_note" in x) and not reads_price(x):
#   with:             if ("confidence" in x or "confidence_note" in x):
#
# @vacuity 🔴 [2026-11-20] MLB's guard asks each row's own method
#   file: card.py
#   find:     return plain_why.price_claims(doc, row_reads_price)
#   with:     return plain_why.price_claims(doc, lambda r: True)
#
# @vacuity 🔴 [2026-11-20] football's copy of the card's sentence (why_card) is read too
#   file: plain_why.py
#   find: ROW_TEXT = ("confidence_note", "why", "why_card")
#   with: ROW_TEXT = ("confidence_note", "why")
#
# @vacuity 🔴 the list catches what it lists
#   file: plain_why.py
#   find:     return [p for p in PRICE_INPUT if p in t]
#   with:     return []
#
# @vacuity 🔴 verify_card.py runs the class guard on the card main() built
#   file: verify_card.py
#   find: _pcl = C.price_claims(doc)
#   with: _pcl = []
#
# @vacuity 🔴 verify_card.py fails a new card that lost its stamp
#   file: verify_card.py
#   find:    doc.get('own_number_rule') == C.OWN_NUMBER_RULE or str(doc.get('date') or '') <= '2026-11-19',
#   with:    True,
#
# @vacuity 🔴 verify_card.py's note check: a price named only when the method reads one
#   file: verify_card.py
#   find: or bool(_pw.price_input(r.get('confidence_note'))) != _pc.reads_price(r['confidence_method'])]
#   with: or False]
#
# @vacuity 🔴 verify_card.py's note check: in the method's own words
#   file: verify_card.py
#   find: if C.correction_words(r['confidence_method'])[0] not in (r.get('confidence_note') or '')
#   with: if False
#
# @vacuity 🔴 football: stage 2's answer is asked of s2_features
#   file: fb_props_model.py
#   find:     return list(inspect.signature(s2_features).parameters) != ["market", "p1"]
#   with:     return False
#
# @vacuity 🔴 [2026-11-20] football: the game model's answer is asked of its fits' inputs
#   file: fb_model.py
#   find:     return any(features(a, mk) != features(b, mk) for mk in ("moneyline", "spread", "total"))
#   with:     return False
#
# @vacuity 🔴 [2026-11-20] football: a game-line row is answered by the game model, a props row by the props model
#   file: card_fb.py
#   find:     if row.get("kind") == "fb-line":
#   with:     if row.get("kind") == "fb-line" and False:
#
# @vacuity 🔴 [2026-11-20] football: a MARKET row may name the books
#   file: card_fb.py
#   find:     if basis == "MARKET":
#   with:     if basis == "MARKET" and False:
#
# @vacuity 🔴 [2026-11-20] football: a player's own record reads no price
#   file: card_fb.py
#   find:     if basis == "MARKET":
#   with:     if basis in ("MARKET", "RECORD"):
"""
import atexit
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "mlb"
from tcheck import ck, eq, section, shown  # noqa: E402

import card  # noqa: E402
import mlb_pitcher_cal as pcal  # noqa: E402
import plain_why  # noqa: E402

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 ONE LIST CATCHES EVERY SENTENCE THAT SAID A PRICE MADE A NUMBER")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ The sentences as the code wrote them (names and numbers planted).
SAID_PRICE = [
    # MLB pitcher note and why, C2 (true to 10-11) and every C1 card 10-12 .. 10-28 (false)
    "v5.0 model blended 50/50 with his own rate at this line (83%), then corrected against the "
    "price using graded pitcher plays from earlier cards.",
    "At <b>-120</b> this has to hit about <b>55%</b> of the time just to break even. We make it "
    "<b>60%</b>. Before checking it against the price it read 83%; our pitcher picks have hit less "
    "often than they claimed, so the number is corrected using every graded pitcher play so far.",
    # CLAUDE.md's own words for C2, and football's props stage 2 to 10-11
    "C2 shipped: a pitcher row PRINTS its blend mixed with its price.",
    "Stage 2 is stage 1 corrected by its own past misses with the books" + chr(0x2019) + " chance.",
    # the books' own chance, true where it is the method (MARKET): the alt parlays, the old alt spreads
    "The books' own chance for each leg — the two sides of that rung at that book with the vig "
    "taken out, or the break-even where the book posts only one side — multiplied together.",
    "The card's alternate spreads, each graded once from the final score: the books' own chance "
    "until 2026-10-11, the model's own after (by_basis).",
    "De-vigged sportsbook consensus. NOT a Gizmo's projection (ledger rule 55).",
]
SAYS_WHICH_BET = [
    # a price may say which bet is priced and what it needs (CLAUDE.md, THE MODEL'S OWN)
    "At <b>-120</b> this has to hit about <b>55%</b> of the time just to break even. We make it "
    "<b>60%</b>.",
    "That price is DraftKings's, not Hard Rock's.",
    "At <b>-150</b> this has to hit about <b>60%</b> of the time just to break even. His own record "
    "puts it at <b>64%</b>.",
    "The game model gives Houston Astros 61% to win. It expects 3.9 runs to 2.9, with Ace One "
    "starting against Arm Two. The price -150 needs 60.0%.",
    "The model gives it <b>51%</b>; at -110 it needs 52.4% to pay.",
    "His record at this line makes it <b>71%</b>; at -110 it needs 52.4% to pay.",
    "The game model gives Purdue 58% to cover; the price -110 needs 52.4%.",
    "Hitters: up to 25 whose record beats the price's break-even.",
    "The game model's own chance.",
]
ck(plain_why.PRICE_INPUT and all(p == p.lower() for p in plain_why.PRICE_INPUT)
   and not [p for p in plain_why.PRICE_INPUT if p.strip() in ("price", "the price", "break even",
                                                               "break-even", "line", "books")],
   "⚠️ the list is there, lower case, and no phrase is a word a which-bet sentence needs",
   str(plain_why.PRICE_INPUT[:5]))
eq([s[:50] for s in SAID_PRICE if not plain_why.price_input(s)], [],
   "🔴 every sentence that said a price or the books' chance made a number is caught "
   "(a curly apostrophe and a tag included)")
eq([(s[:50], plain_why.price_input(s)) for s in SAYS_WHICH_BET if plain_why.price_input(s)], [],
   "✅ a sentence that only says which bet is priced, its break-even or whose number it is is "
   "never caught")
eq(plain_why.price_input("<b>Corrected AGAINST the price</b>"), ["against the price"],
   "🔴 ...inside a tag, in capitals")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 mlb_pitcher_cal.reads_price IS ASKED OF THE CODE THE CARD PRINTS THROUGH")
# ══════════════════════════════════════════════════════════════════════
# `[2026-11-20]` ~~"D and the plain blend do not"~~: D was answered by walk_forward's smoothed(),
#    which the card never prints through. Under SHIPPED = "D" the card prints corrected(), whose
#    inputs (features) are the blend AND the price, so a D row's number moves with its price.
eq({m: pcal.reads_price(m) for m in ("C1", "C2", "D", "BLEND", None)},
   {"C1": False, "C2": True, "D": True, "BLEND": False, None: False},
   "🔴 C1 (shipped 2026-10-11) reads no price; C2 does, and so does D as the card prints it "
   "(corrected(): the blend and the price); the plain blend does not")
eq((pcal.corrected({"strikeouts": {"mu": [0.65, 0.22], "sd": [0.40, 0.23], "w": [0.07, 0.14, 0.08]}},
                   "strikeouts", 62, 45, method="D") is not None,
    round(pcal.corrected({"strikeouts": {"mu": [0.65, 0.22], "sd": [0.40, 0.23], "w": [0.07, 0.14, 0.08]}},
                         "strikeouts", 62, 45, method="D")
          - pcal.corrected({"strikeouts": {"mu": [0.65, 0.22], "sd": [0.40, 0.23], "w": [0.07, 0.14, 0.08]}},
                           "strikeouts", 62, 58, method="D"), 2),
    pcal.corrected({"strikeouts": {"mu": [0.65, 0.22], "sd": [0.40, 0.23], "w": [0.07, 0.14, 0.08]}},
                   "strikeouts", 62, None, method="D")),
   (True, -4.55, None),
   "⚠️ rule 67, the fact behind it: under D corrected() prints 46.69 at a 45% break-even, 51.24 at "
   "58%, and nothing with no price")
try:
    pcal.reads_price("C9")
    _raised = False
except ValueError:
    _raised = True
ck(_raised, "🔴 a method the file does not score raises: answered by its code, never assumed")
_feat, _corr = pcal.features, pcal.corrected
try:
    pcal.features = lambda r, cand: [pcal.logit(r["blend"]), pcal.logit(r["be"] if r["be"] is not None else 0.5)]
    _taught = {"price into C1's inputs": pcal.reads_price("C1")}
    pcal.features = lambda r, cand: [pcal.logit(r["blend"])] if cand == "C1" else [pcal.logit(r["blend"]), 0.0]
    _taught["C2's price weight nil, but nothing printed without one"] = pcal.reads_price("C2")
    pcal.features = _feat
    # a corrected() that stops reading the price (every row printed at a 45% break-even)
    pcal.corrected = lambda maps, market, b, be=None, method=None: _corr(maps, market, b, 45.0, method=method)
    _taught["corrected() drops the price"] = pcal.reads_price("C2")
finally:
    pcal.features, pcal.corrected = _feat, _corr
eq(_taught, {"price into C1's inputs": True, "C2's price weight nil, but nothing printed without one": True,
             "corrected() drops the price": False},
   "🔴 the answer follows the code the card prints through: a price put into C1's inputs turns it "
   "yes; a method that prints nothing without a price reads it; a corrected() that no longer reads "
   "the price turns C2's no (it is not a list, and not features() asked beside corrected())")
eq((card.row_reads_price({"confidence_method": "C1"}), card.row_reads_price({"confidence_method": "C2"}),
    card.row_reads_price({"kind": "hitter", "confidence_basis": "RECORD"}),
    card.row_reads_price({"kind": "mlb-line", "confidence_basis": "MODEL"})),
   (False, True, False, False),
   "✅ card.row_reads_price: a C1 pitcher row no, a C2 one yes, a hitter's record and a game line no")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE PITCHER ROWS card.py BUILDS: THE WORDS FOLLOW THE METHOD, NO NUMBER MOVES")
# ══════════════════════════════════════════════════════════════════════
TODAY = "2026-09-20"
GAME = {"home": "HOU", "away": "SEA", "id": "g1", "commence": "2026-09-20T20:10:00Z"}


def _starts():
    out = [{"d": "2026-08-%02d" % (2 + 4 * j), "gs": True, "k": 6 + (j % 3), "outs": 17 + (j % 3),
            "np": 92 + j, "o": "TEX"} for j in range(6)]
    return out + [{"d": "2026-09-%02d" % (3 + 5 * j), "gs": True, "k": 9, "outs": 18, "np": 95, "o": "SEA"}
                  for j in range(2)]


PITCHERS = {101: {"name": "Ace One", "team": "HOU", "era": "3.40", "whip": 1.15, "throws": "R",
                  "g": _starts()}}
# The fitted mappings' shape (fb_model.fit), by the number of inputs the method's `features`
#    gives (mappings() fits on them): C1 the blend; C2 and D the blend and the price.
_WIDE = {1: {"mu": [0.65], "sd": [0.40], "w": [0.07, 0.14], "n_train": 400, "before": TODAY},
         2: {"mu": [0.65, 0.22], "sd": [0.40, 0.23], "w": [0.07, 0.14, 0.08], "n_train": 400,
             "before": TODAY}}
MAPS = {m: _WIDE[len(pcal.features({"blend": 0.62, "be": 0.45}, m))] for m in pcal.CANDIDATES}


def pitcher_row(mk, line, method, book="draftkings", price=-120):
    """card.build_play with `method` shipped and its planted mapping (BLEND: no mapping)."""
    prop = {"market": mk, "line": line, "side": "over", "price": price, "book": book, "pid": 101}
    old = pcal.SHIPPED
    card.PCAL.clear()
    try:
        if method != "BLEND":
            pcal.SHIPPED = method
            card.PCAL.update({"strikeouts": MAPS[method], "outs": MAPS[method]})
        return card.build_play(prop, PITCHERS[101], PITCHERS, 8.0, 8.0, 6, GAME, TODAY, {"SEA": 5})
    finally:
        pcal.SHIPPED = old
        card.PCAL.clear()


K1, O1 = pitcher_row("pitcher_strikeouts", 5.5, "C1"), pitcher_row("pitcher_outs", 16.5, "C1")
K2, KB = pitcher_row("pitcher_strikeouts", 5.5, "C2"), pitcher_row("pitcher_strikeouts", 5.5, "BLEND")
KH = pitcher_row("pitcher_strikeouts", 5.5, "C1", book="hardrockbet")
ROWS = [K1, O1, K2, KB, KH]
ck(all(isinstance(r, dict) and r.get("why") for r in ROWS)
   and [r["confidence_method"] for r in ROWS] == ["C1", "C1", "C2", "BLEND", "C1"]
   and all(round(r["confidence"]) != round(r["blend"]) for r in (K1, O1, K2)),
   "⚠️ rule 67: each row is built on its method, and every corrected row prints another number "
   "than its blend (the branch the correction sentence sits on)",
   str([(r.get("confidence_method"), r.get("blend"), r.get("confidence")) for r in ROWS
        if isinstance(r, dict)]))
_last = lambda r: r["why"][-1]  # noqa: E731  the price sentence
eq([(r["pitcher"], r["market"], plain_why.price_input(r["confidence_note"]),
     [p for w in r["why"] for p in plain_why.price_input(w)]) for r in (K1, O1, KH)],
   [("Ace One", "strikeouts", [], []), ("Ace One", "outs", [], []), ("Ace One", "strikeouts", [], [])],
   "🔴 C1, both markets: neither the note nor any why line says a price made the number")


def before(text, pattern, r):
    """The number before the correction that `text` prints in `pattern`'s (\\d+) -> it, when it is
    the row's own blend (stored to one decimal, printed from the unrounded value: within 0.55),
    else None."""
    m = re.fullmatch(pattern, text or "")
    return int(m.group(1)) if m and abs(int(m.group(1)) - r["blend"]) <= 0.55 else None


_N1 = (r"v5\.0 model blended 50/50 with his own rate at this line \((\d+)%\), then corrected by how "
       r"often our pitcher plays on earlier cards actually hit; no price enters it\.")
_W1 = (r"At <b>-120</b> this has to hit about <b>55%</b> of the time just to break even\. We make it "
       r"<b>" + str(K1["confidence"]) + r"%</b>\. Before correcting it by our pitcher picks' own record "
       r"it read (\d+)%; our pitcher picks have hit less often than they claimed, so the number is "
       r"corrected using every graded pitcher play so far\. That price is DraftKings's, not Hard Rock's\.")
ck(before(K1["confidence_note"], _N1, K1) is not None,
   "🔴 C1's note: the blend's number before the correction, and what corrected it, no price",
   shown(K1["confidence_note"]))
ck(before(_last(K1), _W1, K1) is not None,
   "🔴 C1's why: the break-even stays, the number before the correction stays, the price names "
   "only the bet and its book", shown(_last(K1)))
ck(not _last(KH).endswith("not Hard Rock's.") and "Before correcting it by our pitcher picks' own record"
   in _last(KH), "✅ a Hard Rock price: no other-book sentence, the C1 opening the same",
   shown(_last(KH)))
_N2 = (r"v5\.0 model blended 50/50 with his own rate at this line \((\d+)%\), then corrected against "
       r"the price using graded pitcher plays from earlier cards\.")
ck(before(K2["confidence_note"], _N2, K2) is not None
   and before(_last(K2), r".* Before checking it against the price it read (\d+)%; our pitcher picks "
                         r"have hit less often than they claimed, .*", K2) is not None,
   "🔴 C2 (SHIPPED patched): the note and why say the price corrected it, which under C2 is true",
   shown(str((K2["confidence_note"], _last(K2)))))
eq((KB["confidence_note"], "Before" in _last(KB)),
   ("v5.0 model blended 50/50 with his own rate at this line.", False),
   "✅ the plain blend (no mapping): no correction, so no correction words")
# The words are words: the same C1 row with C2's words prints every number the same.
_real = card.correction_words
_NUM = ("confidence", "confidence_value", "confidence_method", "blend", "carried", "band", "model",
        "edge", "break_even", "price", "book", "projection", "clears_price_floor")
try:
    card.correction_words = lambda m: None if m in (None, "BLEND") else _real("C2")
    _k1c2 = pitcher_row("pitcher_strikeouts", 5.5, "C1")
finally:
    card.correction_words = _real
ck(_k1c2["confidence_note"] != K1["confidence_note"] and _last(_k1c2) != _last(K1),
   "⚠️ the two rows differ in their words")
eq({k: _k1c2.get(k) for k in _NUM}, {k: K1.get(k) for k in _NUM},
   "🔴 ...and in nothing else: no %, price, edge, band or method moves with the words")
# `[2026-11-20]` EVERY SCORED METHOD, EACH AT TWO PRICES: the words name a price exactly when the
#    printed number moves with the price. ~~D answered from smoothed()~~: under SHIPPED = "D" the
#    Ace One over 5.5 printed 59.8 at -120 and 54.8 at +150 while its note said "no price enters it",
#    and the guard required those words.
_two = {m: (pitcher_row("pitcher_strikeouts", 5.5, m), pitcher_row("pitcher_strikeouts", 5.5, m, price=150))
        for m in pcal.CANDIDATES}
_said = lambda r: bool(plain_why.price_input(r["confidence_note"])  # noqa: E731
                       or [p for w in r["why"] for p in plain_why.price_input(w)])
ck(all(a.get("confidence_method") == b.get("confidence_method") == m and a["blend"] == b["blend"]
       and round(a["confidence_value"]) != round(a["blend"]) for m, (a, b) in _two.items())
   and any(a["confidence_value"] != b["confidence_value"] for a, b in _two.values())
   and any(a["confidence_value"] == b["confidence_value"] for a, b in _two.values()),
   "⚠️ rule 67: every method's row is built on it at both prices, corrected, the same blend; some "
   "methods' numbers move with the price and some do not",
   str({m: (a.get("blend"), a.get("confidence_value"), b.get("confidence_value")) for m, (a, b) in _two.items()}))
eq({m: (a["confidence_value"] != b["confidence_value"], pcal.reads_price(m), _said(a), _said(b))
    for m, (a, b) in _two.items()},
   {"C1": (False,) * 4, "C2": (True,) * 4, "D": (True,) * 4},
   "🔴 every scored method: its number moves with the price exactly when reads_price says so, and "
   "its note and why name the price exactly then (D's 59.8 at -120 and 54.8 at +150 say so)")
eq((round(_two["D"][0]["confidence_value"], 1), round(_two["D"][1]["confidence_value"], 1)), (59.8, 54.8),
   "⚠️ ...the D row is the one the review built")
eq(card.price_claims({"own_number_rule": card.OWN_NUMBER_RULE, "date": "2027-04-01",
                      "picks": [r for ab in _two.values() for r in ab]}), [],
   "✅ ...and the class guard passes them all: each says what its own method did")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 card.price_claims: EVERY LIST OF A CARD THIS CODE BUILT, NEVER A PUBLISHED ONE")
# ══════════════════════════════════════════════════════════════════════
HIT = {"kind": "hitter", "player": "Bat Man", "confidence": 64, "confidence_basis": "RECORD",
       "confidence_note": "His own rate at this exact line, smoothed. There is no hitter model.",
       "why": ["At <b>-150</b> this has to hit about <b>60%</b> of the time just to break even. His "
               "own record puts it at <b>64%</b>."]}
GL = {"kind": "mlb-line", "player": "Houston Astros", "market": "moneyline", "confidence": 61,
      "confidence_basis": "MODEL", "confidence_note": "The game model's own chance.",
      "why": ["The game model gives Houston Astros 61% to win. It expects 3.9 runs to 2.9, with Ace "
              "One starting against Arm Two. The price -150 needs 60.0%."]}
OLD_NOTE = SAID_PRICE[0]
OLD_WHY = "Before checking it against the price it read 83%."


def planted(stamp=card.OWN_NUMBER_RULE, date="2027-04-01", rows=None):
    d = {"date": date, "picks": copy.deepcopy(rows or [K1, O1, HIT]),
         "below_price_floor": [], "top10": copy.deepcopy([K1, HIT]),
         "game_lines": [copy.deepcopy(GL)],
         "parlays": {"two_leg": [{"legs": [copy.deepcopy(O1), copy.deepcopy(HIT)]}]}}
    if stamp is not None:
        d["own_number_rule"] = stamp
    return d


eq(card.price_claims(planted()), [], "✅ a card this code built: nothing to report")
_cases = {}
for where, get in (("picks note", lambda d: d["picks"][0]), ("top10", lambda d: d["top10"][0]),
                   ("game_lines", lambda d: d["game_lines"][0]), ("a hitter", lambda d: d["picks"][2]),
                   ("a parlay leg", lambda d: d["parlays"]["two_leg"][0]["legs"][0])):
    _d = planted()
    if where == "picks note":
        get(_d)["confidence_note"] = OLD_NOTE
    else:
        get(_d)["why"].append(OLD_WHY)
    _cases[where] = [(w, p) for w, p, _l in card.price_claims(_d) or []]
eq(_cases, {"picks note": [("Ace One", "against the price")], "top10": [("Ace One", "against the price")],
            "game_lines": [("Houston Astros", "against the price")],
            "a hitter": [("Bat Man", "against the price")],
            "a parlay leg": [("Ace One", "against the price")]},
   "🔴 a price claim is found in every list the card holds, the note and the why, a hitter and a "
   "game line too, named by its row")
eq(card.price_claims(planted(rows=[K2, HIT])), [],
   "✅ a C2 row saying the price corrected it is not a claim: under C2 it is true")
_old = planted(stamp=None, date="2026-10-28")
_old["picks"][0]["confidence_note"] = OLD_NOTE
eq((card.price_claims(_old), card.price_claims(dict(_old, own_number_rule="own-number-2020-01-01"))),
   (None, None), "🔴 a card with no stamp (or another one) was published before the change: never "
   "checked, never rebuilt")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 verify_card.py's OWN LINES, ON PLANTED CARDS")
# ══════════════════════════════════════════════════════════════════════
_VSRC = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
_A = "# 🔴 `[2026-11-19]` ~~'corrected against the price' in every corrected row's note~~"
_B = "# 🔴 AUDIT PROPOSAL B."
_SLICE = (_VSRC[_VSRC.index(_A):_VSRC.index(_B)]
          if _A in _VSRC and _B in _VSRC and _VSRC.index(_A) < _VSRC.index(_B) else "")
ck("C.price_claims(doc)" in _SLICE and "C.correction_words(" in _SLICE and _SLICE.count("ck(") >= 4,
   "⚠️ rule 67: the lines were read out of verify_card.py",
   "⛔ an empty slice runs nothing, and every check below would pass on nothing")
ck(_VSRC.index("doc = C.main(dry=True)") < _VSRC.index("_pcl = C.price_claims(doc)")
   if "_pcl = C.price_claims(doc)" in _VSRC else False,
   "🔴 ...and verify_card.py runs them on the card main() built, before the card is committed")
NOTE_NEW = ("a corrected pitcher row says so in its note, in its method's own words, naming a price "
            "only when that method reads one")
NOTE_OLD, STAMP = "a corrected pitcher row says so in its note", \
    "a card dated after the 2026-11-19 change carries the own-number stamp"
CLAIMS = "no sentence on the card names a price its number's method never read"


def verify(doc):
    """verify_card.py's own lines on `doc` -> {check: ok} (a check that did not run is absent)."""
    import mlb_pitcher_cal as _pc
    got = {}

    def _ck(name, ok, detail=""):
        got[re.sub(r"\s*\(\d+ rows\)", "", name)] = bool(ok)
    pall = [r for r in (doc.get("picks") or []) + (doc.get("below_price_floor") or [])
            if r.get("kind") != "hitter" and "confidence_method" in r]
    exec(compile(_SLICE, "verify_card.py#own-number", "exec"),
         {"doc": doc, "_pall": pall, "_pc": _pc, "_pw": plain_why, "C": card, "ck": _ck,
          "print": lambda *a, **k: None})
    return got


def edited(doc, idx, **kw):
    for k, v in kw.items():
        if k == "why_add":
            doc["picks"][idx]["why"].append(v)
        else:
            doc["picks"][idx][k] = v
    return doc


eq(verify(planted()), {NOTE_NEW: True, STAMP: True, CLAIMS: True},
   "✅ a C1 card this code built passes all three")
eq(verify(planted(rows=[K2, HIT])), {NOTE_NEW: True, STAMP: True, CLAIMS: True},
   "✅ ...and so does a C2 one, its words naming the price (the old requirement, still required)")
eq(verify(planted(rows=[_two["D"][0], _two["D"][1], HIT])), {NOTE_NEW: True, STAMP: True, CLAIMS: True},
   "✅ `[2026-11-20]` ...and a D one: D reads the price as the card prints it, and its words say so")
eq(verify(edited(planted(rows=[_two["D"][0], HIT]), 0, confidence_note=K1["confidence_note"])).get(NOTE_NEW),
   False, "🔴 `[2026-11-20]` a D row saying \"no price enters it\" (the words the old answer gave it): FAIL")
eq(verify(edited(planted(), 0, confidence_note=OLD_NOTE)), {NOTE_NEW: False, STAMP: True, CLAIMS: False},
   "🔴 the old note back on a new C1 card: both the note check and the guard FAIL")
eq(verify(edited(planted(), 1, why_add=OLD_WHY)), {NOTE_NEW: True, STAMP: True, CLAIMS: False},
   "🔴 the old why opening back on a new C1 card: FAIL")
eq(verify(edited(planted(), 0, confidence_note=K1["confidence_note"] + " Checked against the price.")).get(NOTE_NEW),
   False, "🔴 a C1 note with its own words AND a price claim: FAIL (it names a price C1 never read)")
eq(verify(edited(planted(), 0, confidence_note="v5.0 model blended 50/50 with his own rate at this "
                                                "line.")).get(NOTE_NEW), False,
   "🔴 a corrected row whose note no longer says it was corrected: FAIL")
eq(verify(edited(planted(rows=[K2, HIT]), 0, confidence_note=K1["confidence_note"])).get(NOTE_NEW), False,
   "🔴 a C2 row with C1's words (no price named, though C2 reads it): FAIL")
_pub = edited(planted(stamp=None, date="2026-10-28"), 0, confidence_note=OLD_NOTE)
_pub["picks"][1]["confidence_note"] = OLD_NOTE
eq(verify(_pub), {NOTE_OLD: True, STAMP: True},
   "🔴 a card published before the change, the old words and all: the old question, nothing fails, "
   "and the guard does not run on it (published cards are permanent)")
eq(verify(planted(stamp=None)).get(STAMP), False,
   "🔴 a card dated after the change without the stamp: FAIL (the guard cannot be switched off by "
   "losing the stamp)")

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 FOOTBALL: STAGE 2 READS NO PRICE, AND THE WHYS SAY NONE")
# ══════════════════════════════════════════════════════════════════════
_EMPTY = tempfile.mkdtemp(prefix="pricewords-")          # no stored file: the chance sentence alone
atexit.register(lambda: shutil.rmtree(_EMPTY, ignore_errors=True))
_DRV = r"""
import inspect, json, sys
sys.path.insert(0, %(root)r)
import fb_props_model as M
import fb_why
out = {"params": list(inspect.signature(M.s2_features).parameters), "reads": M.stage2_reads_price()}
_real = M.s2_features
M.s2_features = lambda market, p1, p_market: [M.logit(p1), M.logit(p_market), 0.0]
out["reads_with_price"] = M.stage2_reads_price()
M.s2_features = _real
ctx = fb_why.Context(%(lg)r, %(empty)r, 2026)
row = {"player": "Model Guy", "market": "player_receptions", "line": 3.5, "side": "over",
       "confidence": 51, "confidence_basis": "MODEL", "price": -110, "break_even": 52.4,
       "home": "H", "away": "A", "commence": "2026-11-22T18:00:00Z"}
out["why"] = [fb_why.prop_why(row, ctx), fb_why.prop_why(dict(row, confidence_basis="RECORD", confidence=71), ctx)]
# `[2026-11-20]` the game model's fits, asked the same way, and football's guard on every list
import card_fb, fb_model
out["game_reads"] = fb_model.features_read_price(%(lg)r)
_f = fb_model.features
fb_model.features = lambda r, market, M=None, T=None: list(_f(r, market, M, T)) + [r["pml"]]
out["game_reads_with_price"] = fb_model.features_read_price(%(lg)r)
fb_model.features = _f
CLAIM = "Corrected against the books' chance."
PROP = {"kind": "fb", "player": "Model Guy", "market": "player_receptions", "confidence": 51,
        "confidence_basis": "MODEL", "confidence_note": "The props model's chance for this exact side "
        "and line, priced on this card's own board.", "why": ["<b>Model Guy</b> went over 3.5 rec in "
        "<b>4 of 4 games</b> in 2026, when he played at least half the snaps."]}
REC = dict(PROP, player="Record Guy", confidence=71, confidence_basis="RECORD", confidence_note=None)
MKT = dict(PROP, player="Market Guy", confidence=55, confidence_basis="MARKET",
           why=["The books' own chance for this side, with the vig taken out."])
LINE = {"kind": "fb-line", "league": %(lg)r, "player": "Purdue", "market": "spread", "confidence": 58,
        "confidence_basis": "MODEL", "why": ["The game model gives Purdue 58%% to cover +3.5; the price "
        "-110 needs 52.4%%."]}
ALT = dict(LINE, player="Alt Team", market="alternate_spread", confidence=61, why=["The game model "
           "gives Alt Team 61%% to cover +6.5; the best price, -150 at DraftKings, needs 60.0%%."])
LIKED = dict(PROP, player="Liked Guy", why=list(fb_why.prop_why(PROP, ctx)), why_card=list(PROP["why"]))
GLL = dict(LINE, player="Liked Team", why=fb_why.line_why(LINE, ctx), why_card=list(LINE["why"]))
TOP = dict(PROP, player="Top Guy")
fb_model.features = lambda r, market, M=None, T=None: list(_f(r, market, M, T)) + [r["pml"]]
out["rows_with_game_price"] = [card_fb.row_reads_price(x) for x in (LINE, ALT, PROP, REC, MKT)]
fb_model.features = _f
out["rows"] = [card_fb.row_reads_price(x) for x in (LINE, ALT, PROP, REC, MKT)]
def fbcard():
    return json.loads(json.dumps({"picks": [PROP, REC, MKT], "liked": [LIKED], "game_lines": [LINE, ALT],
                                  "game_lines_liked": [GLL], "top_plays": [TOP],
                                  "parlays": {"2": [{"legs": ["Model Guy over 3.5"], "joint": 30.0}]}}))
out["clean"] = card_fb.price_claims(fbcard())
out["planted"] = {}
for where, lst, i, key in (("a props row", "picks", 0, "why"), ("a props note", "picks", 0, "confidence_note"),
                           ("a record row", "picks", 1, "why"), ("a game line", "game_lines", 0, "why"),
                           ("an alternate spread", "game_lines", 1, "why"),
                           ("a liked game line", "game_lines_liked", 0, "why"),
                           ("a liked row's card sentence", "liked", 0, "why_card"),
                           ("a top play", "top_plays", 0, "why")):
    d = fbcard()
    row = d[lst][i]
    row[key] = (row.get(key) or "") + " " + CLAIM if key == "confidence_note" else list(row.get(key) or []) + [CLAIM]
    out["planted"][where] = [[w, ph] for w, ph, _t in card_fb.price_claims(d)]
d = fbcard()
d["picks"][2]["why"].append(CLAIM)
out["market_claim"] = card_fb.price_claims(d)
print(json.dumps(out))
"""
_fb = {}
for lg in ("nfl", "ncaaf"):
    _p = subprocess.run([sys.executable, "-c", _DRV % {"root": ROOT, "lg": lg, "empty": _EMPTY}],
                        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=300,
                        env=dict(os.environ, LEAGUE=lg, PYTHONUTF8="1"))
    try:
        _fb[lg] = json.loads(_p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        print(shown(_p.stdout[-800:]), shown(_p.stderr[-800:]))
        _fb[lg] = {}
eq([(_fb[lg].get("params"), _fb[lg].get("reads"), _fb[lg].get("reads_with_price")) for lg in _fb],
   [(["market", "p1"], False, True)] * 2,
   "🔴 stage 2 takes the market and stage 1's chance only, so it reads no price; a price input "
   "added to s2_features turns the answer yes. ⛔ A NEW INPUT STOPS HERE: say whether it is a "
   "price, then teach stage2_reads_price (an input added quietly would switch the guard off)")
_s = [s for lg in _fb for w in _fb[lg].get("why") or [] for s in w]
ck(len(_s) == 4 and all("needs 52.4% to pay" in s for s in _s),
   "⚠️ fb_why's chance sentences were built, MODEL and RECORD, both leagues", str(_s)[:300])
eq([s for s in _s if plain_why.price_input(s)], [],
   "✅ ...and neither says a price made the number (football's card rows: test_fb_props_confidence.py)")
# `[2026-11-20]` THE GAME MODEL AND EVERY LIST OF THE FOOTBALL CARD. ~~The props rows and the liked
#    list only~~: a game-line why saying "corrected against the books' chance" passed every test.
eq([(_fb[lg].get("game_reads"), _fb[lg].get("game_reads_with_price")) for lg in _fb], [(False, True)] * 2,
   "🔴 the game model's fits read no price (fb_model.features: its own ratings since 2026-10-11, the "
   "college champion's included); the books' chance put into them turns the answer yes")
eq([(_fb[lg].get("rows"), _fb[lg].get("rows_with_game_price")) for lg in _fb],
   [([False, False, False, False, True], [True, True, False, False, True])] * 2,
   "🔴 each football row is asked of its own method: a game line and an alternate spread of the game "
   "model (a price put into its fits turns them yes, and only them), a props row of the props model, "
   "a record row reads none, a MARKET row is the books' own number")
eq([_fb[lg].get("clean") for lg in _fb], [[], []],
   "✅ a planted football card whose every sentence is the code's own: nothing to report, a MARKET row "
   "naming the books' chance included (it is the books' number)")
_FB_WANT = {"a props row": [["Model Guy", "books' chance"]], "a props note": [["Model Guy", "books' chance"]],
            "a record row": [["Record Guy", "books' chance"]], "a game line": [["Purdue", "books' chance"]],
            "an alternate spread": [["Alt Team", "books' chance"]],
            "a liked game line": [["Liked Team", "books' chance"]],
            "a liked row's card sentence": [["Liked Guy", "books' chance"]],
            "a top play": [["Top Guy", "books' chance"]]}
eq([_fb[lg].get("planted") for lg in _fb], [_FB_WANT] * 2,
   "🔴 card_fb.price_claims finds a price claim in every list a football card holds: the board (the "
   "props model's row, its note, a player's record), the game lines and the alternate spreads, the "
   "liked lists (their why_card too) and the top plays, named by its row, both leagues")
eq([_fb[lg].get("market_claim") for lg in _fb], [[], []],
   "✅ ...but never on a MARKET row: the books' own number may say it is theirs")
