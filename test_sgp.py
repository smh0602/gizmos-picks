#!/usr/bin/env python3
"""
SAME-GAME PARLAYS, AND THE NUMBER THEY MUST NOT PUBLISH.

Sam, 2026-09-11: *"we also need to start forming parlays in this tab,
this can include same game parlays with player props/game lines. up to
the model to decide which bets are best"*

🔴 THE WHOLE POINT OF THIS FILE IS THE ABSENCE. `build_parlays_fb`
multiplies its legs' records into an "all hit" percentage, and the ONLY
thing that licenses it is ledger rule 54 — the legs are in different
games. Inside one game that licence is gone: a quarterback's passing
yards and his receiver's receiving yards are close to the same event.
⛔ So a same-game row must carry NO joint probability, NO break-even, NO
edge and NO EV — and the temptation to add one back is exactly the kind
of thing CLAUDE.md's "never weaken a check to make it pass" exists for.
Every one of those fields is asserted ABSENT here, by name.

⚠️ AND THE PAYOUT IS AN UPPER BOUND. A book prices a correlated slip
below the product of its legs. That discount is in no pull this project
stores, so the product is published as the most the slip can pay and is
labelled so. This file asserts the label as well as the number.
"""
import glob
import itertools
import json
import os
import re
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "ncaaf")
import card_fb as C  # noqa: E402

print("═══ 1. ⛔ THE FORBIDDEN FIELDS, BY NAME ═══")

# ⛔ DRIVEN THROUGH THE REAL BUILDER on a fixture where a joint number
#    would be trivially computable. A test that asserted the SOURCE has
#    no "joint" would pass on a file that computes one under another
#    name; this asks the rows themselves.
GID = "g1"


def _leg(player, conf, price, market="player_reception_yds", line=4.5):
    return {"player": player, "confidence": conf, "price": price,
            "clears_price_floor": True, "game_id": GID, "book": "hardrockbet",
            "game": "A @ B", "market": market, "side": "over", "line": line}


rows = [_leg("P%d" % i, 90 - i, -120 - i * 10) for i in range(6)]
sgp, meta = C.build_sgp_fb(rows, [], line_quotes={})
flat = [r for v in sgp.values() for r in v]
ck("🔴 the fixture actually produced same-game rows",
   len(flat) > 0,
   "⛔ a test whose fixture builds nothing asserts nothing. Got %d rows "
   "from %d legs in one game" % (len(flat), len(rows)))

FORBIDDEN = ("break_even", "edge", "ev_30")
leaked = sorted({f for r in flat for f in FORBIDDEN if r.get(f) is not None})
ck("⛔ no same-game row carries a break-even, an edge or an EV",
   not leaked,
   "every one of those is a joint probability wearing a different unit, "
   "and the joint probability is the thing that cannot be computed here. "
   "Leaked: %s" % leaked)

ck("⛔ ...and `joint` is present but NULL, not quietly missing",
   all("joint" in r and r["joint"] is None for r in flat),
   "⚠️ ABSENT AND NULL ARE DIFFERENT CLAIMS. A missing key reads as an "
   "oversight; an explicit null beside `joint_basis: \"NOT PUBLISHED\"` "
   "says the number was considered and withheld (ledger rule 205 — "
   "asserting a wrong thing is absent is not asserting the right thing "
   "is present).")

ck("✅ every row says WHY, in its own field",
   all(r.get("joint_basis") == "NOT PUBLISHED"
       and "independent" in (r.get("joint_note") or "") for r in flat),
   "rule 55: a number's provenance travels with the number, and so does "
   "the reason a number is missing")

print("\n═══ 2. 🔴 THE PAYOUT IS AN UPPER BOUND AND SAYS SO ═══")

ck("🔴 multiplier_basis is UPPER BOUND on every row",
   all(r.get("multiplier_basis") == "UPPER BOUND" for r in flat),
   "⛔ a book discounts a correlated slip. Publishing the straight "
   "product as a price would be quoting a number no book offers, which "
   "is the same defect as matching two prices on |point|")

# 🔴 THE ARITHMETIC, RECOMPUTED. ⛔ Not "is there a multiplier" — is it
#    the product of the prices this row lists.
badmult = []
for r in flat:
    want = 1.0
    for px in r["prices"]:
        want *= C.decimal_odds(px)
    if abs(want - r["multiplier"]) > 0.005:
        badmult.append((r["legs"], round(want, 3), r["multiplier"]))
ck("✅ the multiplier IS the product of the prices on the row",
   not badmult,
   "a payout a reader cannot reproduce from the prices beside it is a "
   "number they have to take on trust. Bad: %s" % badmult[:2])

print("\n═══ 3. 🔴 THE FLOOR IS APPLIED, THE CEILING IS NOT ═══")

# ⚠️ ONE-SIDED ON PURPOSE. If even the UPPER bound misses Sam's floor the
#    slip can never reach it, so dropping it is certain. An upper bound
#    ABOVE the ceiling may sit inside it once the book discounts, so
#    excluding on that would be excluding on a number we do not have.
lo2 = C.PARLAY_BANDS[2][0]
hi2 = C.PARLAY_BANDS[2][1]
ck("🔴 no published slip's upper bound is under Sam's floor",
   all(r["multiplier"] >= C.PARLAY_BANDS[r["n_legs"]][0] - 1e-9 for r in flat),
   "the 1.8x floor is Sam's standing instruction (CLAUDE.md) and a slip "
   "whose BEST case misses it can never pay it")
over = [r["multiplier"] for r in flat if r["multiplier"] > hi2 and r["n_legs"] == 2]
ck("✅ ...and the ceiling is deliberately NOT enforced",
   meta.get("ceiling_applied") is False,
   "⛔ this is the half that looks like a bug and is not. %d two-leg "
   "slip(s) sit above the %gx ceiling as UPPER bounds; the discounted "
   "slip may well land inside it, and excluding on a number we do not "
   "hold would be inventing one." % (len(over), hi2))

print("\n═══ 4. 🔴 EVERY LEG OF ONE SLIP IS ONE GAME AND ONE BOOK ═══")

ck("🔴 every row is a single game",
   all(r.get("same_game") is True and r.get("game_id") for r in flat),
   "the tab draws these under a heading that says same game; a row from "
   "two games under that heading would be the page lying")

mixed = [_leg("X", 80, -120)]
mixed[0]["book"] = "fanduel"
sgp2, meta2 = C.build_sgp_fb(rows + mixed, [], line_quotes={})
flat2 = [r for v in sgp2.values() for r in v]
ck("🔴 a leg at another book is REJECTED, not silently priced",
   meta2["rejected"]["mixed_book"] > 0,
   "⛔ a parlay is ONE SLIP AT ONE SPORTSBOOK. A multiplier built across "
   "two books is a number nobody can bet. Rejected: %d"
   % meta2["rejected"]["mixed_book"])

print("\n═══ 5. 🔴 A GAME-LINE LEG IS PRICED AT THE PROPS' OWN BOOK ═══")

# 🔴 THE DEFECT THIS CATCHES IS ONE THIS BUILD ACTUALLY HAD.
#    `[measured on the live 2026-09-11 college card]` `build_game_lines`
#    returns each game's BEST price across books — the Rutgers spread was
#    BetMGM -102 while every rated prop in that game was Hard Rock — so
#    the first form of this builder rejected EVERY line-leg combination
#    for needing two books, and not one same-game parlay could carry a
#    line. The fix reads the props' own book's quote out of the snapshot.
gl = [{"game_id": GID, "market": "totals", "side": "Under", "point": 51.5,
       "best_price": -102, "best_book": "betmgm", "game": "A @ B"}]
quotes = {(GID, "totals", "Under", 51.5): {"betmgm": -102,
                                           "hardrockbet": -115}}
sgp3, meta3 = C.build_sgp_fb(rows, gl, line_quotes=quotes)
flat3 = [r for v in sgp3.values() for r in v]
withline = [r for r in flat3 if r.get("n_line_legs")]
ck("🔴 a line leg reaches the board at all",
   bool(withline),
   "⛔ if this is empty the feature is shipped and inert — which is what "
   "the best-price version was, and it looked identical from the source")
ck("🔴 ...priced at the PROPS' book, not the best book",
   all(r["book"] == "hardrockbet" and -115 in r["prices"] for r in withline),
   "⛔ -102 is BetMGM's price. Putting it on a Hard Rock slip advertises "
   "a price nobody can bet. Got: %s"
   % [(r["book"], r["prices"]) for r in withline[:2]])
ck("✅ and the better price elsewhere is still recorded, not hidden",
   all(r.get("line_best_book") == "betmgm"
       and r.get("line_best_price") == -102 for r in withline),
   "the reader is not told the shopped price does not exist — they are "
   "told which book has it and why this slip does not use it")

none_at_book = C.build_sgp_fb(rows, gl, line_quotes={
    (GID, "totals", "Under", 51.5): {"betmgm": -102}})[1]
ck("⛔ a book that does not quote the line yields NO line leg",
   none_at_book["rejected"]["line_not_at_book"] > 0,
   "⚠️ it is not substituted with another book's price and not with "
   "another wager. Rejected: %d"
   % none_at_book["rejected"]["line_not_at_book"])

print("\n═══ 6. 🔴 THE ORDERING IS THE WEAKEST LEG, AND IT IS A RECORD ═══")

ck("🔴 weakest_leg is the MINIMUM of the row's own leg records",
   all(r["weakest_leg"] == min(r["leg_confidences"]) for r in flat),
   "⛔ not the mean, not the product. A parlay is only as good as the "
   "leg most likely to break it, and that is a number actually measured "
   "on that player at that exact line")
ck("⛔ ...and it is labelled RECORD, never MODEL",
   all(r.get("weakest_leg_basis") == "RECORD" for r in flat),
   "there is no football model — T46, T47, T50 and T57 all lost to a "
   "player's own season average (rule 55)")
for size, rowset in sgp.items():
    ck("✅ the %s-leg list is ordered by weakest leg, descending" % size,
       all(rowset[i]["weakest_leg"] >= rowset[i + 1]["weakest_leg"]
           for i in range(len(rowset) - 1)),
       "Got: %s" % [r["weakest_leg"] for r in rowset])

ck("⛔ a slip with no rated player leg is never published",
   all(r["leg_confidences"] for r in flat),
   "a game line carries no record, so a slip of nothing but lines could "
   "not be ordered at all — it is excluded rather than ranked arbitrarily")

print("\n═══ 7. 🔴 THE PAGE SHOWS THEM SEPARATELY AND BOXES NOTHING ═══")

html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
ck("🔴 the page reads C.sgp, a separate key from C.parlays",
   "C.sgp" in html and "fbSgpTable" in html,
   "⛔ merging the two would put two different row shapes under one "
   "name, and the shape difference is the entire point")
ck("⛔ the same-game table has no 'All hit' or EV column",
   "PAYS AT MOST" in html.upper()
   and "All hit" not in html[html.index("function fbSgpTable"):
                             html.index("async function fbParlays")],
   "an empty column reads as a missing number; a filled one would be "
   "false")

# ⛔ ASKED OF THE RENDERED TAB'S OWN FUNCTION, not of the file. Sam,
#    2026-09-11: "remove all yellow boxes in the parlays tab" and
#    "remove yellow boxes in track record tab". index.html carries
#    `class="note"` in a dozen other tabs and must keep them.
for fn, label in (("fbParlays", "Parlays"), ("fbRecord", "Track Record")):
    body = html[html.index("async function %s(){" % fn):]
    body = body[:body.index("\n}\n")]
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    ck("🔴 the %s tab renders no cream .note box" % label,
       'class="note"' not in body and "fbNoModelNote" not in body,
       "⚠️ the SENTENCES survive as .fnote footnotes and .kind chips — "
       "rule 55 wants every number labelled, not boxed. What must not "
       "come back is the box.")

print("\n═══ 8. 🔴 THE LIVE CARDS ═══")

cards = sorted(glob.glob(os.path.join(ROOT, "picks", "fb-*-latest.json")))
if not cards:
    note("⚠️ NOT EXERCISED: no latest-card pointers on this machine.")
for p in cards:
    c = json.load(open(p, encoding="utf-8"))
    live = [r for v in (c.get("sgp") or {}).values() for r in v]
    nm = os.path.basename(p)
    if not live:
        note("⚠️ %s carries no same-game parlays. That is a fact about "
             "the slate, not a failure — %s"
             % (nm, (c.get("sgp_meta") or {}).get("note", "")[:90]))
        continue
    ck("🔴 %s publishes no joint probability on any same-game row" % nm,
       all(r.get("joint") is None for r in live),
       "this is the assertion that matters on the file a reader actually "
       "loads")
    ck("✅ %s: every same-game slip is one game and one book" % nm,
       all(len({r["game_id"]}) == 1 and r.get("book") for r in live),
       "")

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that a same-game parlay is a good "
     "bet, or that the weakest-leg ordering picks winners. There is no "
     "football model and nothing here was backtested. What is owned is "
     "that no number on these rows asserts more than it can — the joint "
     "probability is withheld rather than invented, and the payout is "
     "labelled as the ceiling it is.")
