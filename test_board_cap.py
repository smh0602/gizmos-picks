#!/usr/bin/env python3
"""
THE BOARD IS 25 ROWS, NOT 50.

Sam, 2026-09-11: *"i only want 25 player props in the gizmos picks tab
not 50."*

🔴 WHAT THIS FILE OWNS. Not "does the constant say 25" — that is a fact
about a line of source, and this project's founding lesson is that a fact
about a query is not a fact about the world. It owns:

  1. the constant, because it is the ONE place the number may live;
  2. that the LIVE published cards honour it;
  3. that the per-market share cap is recomputed FROM the new cap, so a
     25-row board is more evenly mixed rather than a truncated 50;
  4. that the PAGE holds no copy of the number at all;
  5. that nothing else moved with it — the price floor, the price
     ceiling, MIN_GAMES and the usage floor are untouched.

⚠️ AND ONE THING IT DELIBERATELY DOES NOT ASSERT: that the 25 are the
first 25 of the 50. On a RATED board they are, because the rows are
sorted and sliced. On the COLLEGE board they are not, and that is by
design — `fill_board` derives its per-market cap from the board cap, so
int(50*0.34)=17 becomes int(25*0.34)=8 and a two-market slate comes out
differently spread. ⛔ Asserting a prefix would be asserting the wrong
thing, and it would fail on correct code.
"""
import glob
import json
import os
import re
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "ncaaf")
import card_fb  # noqa: E402  (needs LEAGUE set first)

print("═══ 1. 🔴 THE CONSTANT, AND IT IS THE ONLY COPY ═══")

ck("🔴 BOARD_MAX is 25",
   card_fb.BOARD_MAX == 25,
   "Sam, 2026-09-11: \"i only want 25 player props in the gizmos picks "
   "tab not 50.\" Got %r" % card_fb.BOARD_MAX)

src = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
# ⛔ COUNT ASSIGNMENTS, NOT OCCURRENCES. `50` appears a dozen times in
#    this file as a historical MEASUREMENT ("15 of 50 live rows", "0 of
#    50 rows with a record") and those are the record of what was
#    observed — they must not be rewritten and they are not copies of
#    the cap. What must be unique is the place the cap is DEFINED.
_assigns = re.findall(r"^BOARD_MAX\s*=\s*(\d+)", src, re.M)
ck("⛔ ...and it is assigned exactly once, nowhere else",
   _assigns == ["25"],
   "a second assignment is a second source of truth. Found: %s" % _assigns)

ck("✅ the superseded 50 is struck, not deleted",
   "~~maximum 50~~" in src,
   "Sam's standing rule for any durable file: strike superseded content "
   "visibly rather than deleting it, so the record of what changed "
   "survives")

print("\n═══ 2. 🔴 THE PAGE HOLDS NO COPY OF THE NUMBER ═══")

html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
ck("🔴 index.html prints the card's own board_max",
   "C.board_max" in html or "board_max" in html,
   "⛔ rule 66 — the page must never restate a cap the builder owns")
# ⛔ ASKED OF THE FUNCTION BODIES, NOT OF THE FILE. index.html quotes
#    Sam's 2026-09-04 instruction verbatim in a struck comment, and that
#    quote contains the words "maximum 50". A check that searched the
#    whole file for a slice-by-50 would read the documentation of the
#    change as the change failing.
_js = re.sub(r"/\*.*?\*/", "", html, flags=re.S)
ck("⛔ ...and slices no board itself",
   not re.search(r"\.slice\(\s*0\s*,\s*(25|50)\s*\)", _js),
   "a page that took its own top-N would be a second copy of the cap, "
   "and the two would disagree the first time one moved")

print("\n═══ 3. 🔴 THE LIVE CARDS HONOUR IT ═══")

# ⚠️ REPORTED AND ASSERTED SEPARATELY (ledger rule 76). Cards published
#    BEFORE this change are the permanent record of what was shown and
#    may never be rewritten, so asserting over every stored card would be
#    red forever. What is ASSERTED is the builder's own declared cap on
#    every card; what is REPORTED is how many older cards exceed 25.
cards = sorted(glob.glob(os.path.join(ROOT, "picks", "fb-*-2*.json")))
if not cards:
    note("⚠️ NOT EXERCISED: no football cards on this machine. Sections "
         "1, 2 and 4 do not need them and still ran.")
else:
    # ⛔ ONLY CARDS THAT DECLARE A CAP ARE ASSERTED. The first form of
    #    this check failed on `fb-ncaaf-2026-09-03.json`, which predates
    #    the `board_max` field entirely — so it was failing a card for
    #    not carrying a field that did not exist when it was written,
    #    which is a fact about the schema's history and not about any
    #    card being over its cap. Cards without the field are REPORTED.
    bad, undeclared = [], []
    for p in cards:
        try:
            c = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            bad.append((os.path.basename(p), "unreadable: %s" % e))
            continue
        n, cap = len(c.get("picks") or []), c.get("board_max")
        if cap is None:
            undeclared.append(os.path.basename(p))
        elif n > cap:
            bad.append((os.path.basename(p), "%d picks over a cap of %d"
                        % (n, cap)))
    ck("🔴 no published card exceeds the cap IT declares",
       not bad,
       "⛔ the card carries its own board_max so a reader can check it "
       "without the source. A card over its own stated cap is the page "
       "lying about its own rule. Bad: %s" % bad[:3])
    if undeclared:
        note("⚠️ %d card(s) predate the board_max field and are not "
             "asserted over: %s. ⛔ They are not rewritten — a published "
             "card is a permanent record (rule 76)."
             % (len(undeclared), ", ".join(undeclared[:3])))

    over = [os.path.basename(p) for p in cards
            if len(json.load(open(p, encoding="utf-8")).get("picks") or []) > 25]
    note("⚠️ %d of %d stored cards carry more than 25 picks. Those were "
         "published under the old cap of 50 and STAY AS THEY ARE — a "
         "published card is a permanent record. The next scheduled "
         "card-fb run writes the first 25-row board." % (len(over), len(cards)))

print("\n═══ 4. 🔴 THE SHARE CAP IS DERIVED FROM THE NEW NUMBER ═══")

# 🔴 THIS IS THE HALF OF THE CHANGE THAT IS EASY TO MISS. MARKET_MAX_SHARE
#    is a FRACTION, so halving the board halves the rows any one market
#    may take: int(50*0.34)=17 -> int(25*0.34)=8. ⛔ If fill_board had
#    held a row count instead of a fraction, a 25-row board could have
#    come out 17 Anytime TDs — two thirds of it — which is the exact
#    failure the share cap was added to stop.
per = max(1, int(card_fb.BOARD_MAX * card_fb.MARKET_MAX_SHARE))
ck("🔴 no market may take more than 8 of the 25",
   per == 8,
   "got %d. A third of 25 is 8; a cap that stayed at 17 would let one "
   "market take two thirds of the board" % per)


def _row(market, i):
    return {"market": market, "price": -110 - i, "confidence": None}


# ⛔ DRIVEN THROUGH THE REAL fill_board, not re-implemented. A test that
#    re-derives the round-robin checks its own arithmetic and nothing
#    that ships.
rows = ([_row("player_anytime_td", i) for i in range(40)]
        + [_row("player_rush_yds", i) for i in range(40)]
        + [_row("player_reception_yds", i) for i in range(40)]
        + [_row("player_receptions", i) for i in range(40)])
out = card_fb.fill_board(rows, card_fb.BOARD_MAX)
counts = {}
for r in out:
    counts[r["market"]] = counts.get(r["market"], 0) + 1
ck("✅ a four-market slate fills to exactly 25",
   len(out) == 25,
   "got %d" % len(out))
ck("🔴 ...and no market exceeds 8 rows",
   max(counts.values()) <= 8,
   "⛔ the board that prompted this rule was 100%% Anytime TD with a "
   "+5000 row on top. Counts: %s" % counts)

# ⚠️ THE ONE-MARKET SLATE STILL FILLS. The share cap is a mix rule, not a
#    reason to ship a 8-row board when only one market is priced —
#    fill_board falls through and takes what exists. ⛔ A board that went
#    short because of a diversity rule would be padding in reverse.
one = card_fb.fill_board([_row("player_anytime_td", i) for i in range(40)],
                         card_fb.BOARD_MAX)
ck("✅ a one-market slate still reaches 25 rather than stopping at 8",
   len(one) == 25,
   "the share cap decides the MIX when there is a mix to decide; it must "
   "not shrink a board that has nothing to mix. Got %d" % len(one))

print("\n═══ 5. ⛔ NOTHING ELSE MOVED ═══")

# 🔴 A CAP CHANGE MUST NOT BE A BAR CHANGE. CLAUDE.md's one rule that
#    matters most is that a check is never weakened to make something
#    pass, and the neighbouring temptation here is to loosen a threshold
#    so 25 "good" rows can always be found. These are the bars as they
#    stood before this change.
for name, want in (("MIN_GAMES", 6), ("PRICE_CEIL", 400),
                   ("PRICE_FLOOR", -700)):
    got = getattr(card_fb, name, None)
    ck("⛔ %s is untouched at %r" % (name, want),
       got == want,
       "⚠️ if this bar moved legitimately, it moved in a DIFFERENT change "
       "with its own reason — update this line then, not to make it "
       "green now. Got %r" % got)

ck("⛔ the usage floor is still read from the data, never restated",
   card_fb.USAGE_FLOOR is None or isinstance(card_fb.USAGE_FLOOR, float),
   "T37-CFB is FROZEN and its value belongs to the log file. A literal "
   "in this module would be a second copy of a frozen number")

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that 25 is a better number than "
     "50. It is Sam's instruction and nothing was measured about it. "
     "What is owned here is that the number is written once, that the "
     "page does not hold a second copy, and that halving the board "
     "tightened the market mix instead of quietly truncating it.")
