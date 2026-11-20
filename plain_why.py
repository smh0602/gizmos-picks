#!/usr/bin/env python3
"""plain_why.py — THE CAVEAT PHRASES NO PICK'S "WHY" CARRIES, ALL THREE LEAGUES.

`[Sam, 2026-10-09]` football: "Remove the caveat sentences" (card_fb.build_why).
`[Sam, 2026-11-18]` MLB, asked whether its whys drop theirs the same way, from the
first 2027 card, he chose "Drop them like football": "The 'One thing to know' line and
the 'not part of the model's math' endings go."

A why gives the stats; it does not hedge them. The pick's own numbers (%, price, book,
break-even, edge) sit beside it, and every label, basis and count stays in the DATA
(`confidence_basis`, `confidence_note`, `basis`, `opp_recent.note`, the record fields).

⛔ ONE LIST, READ BY BOTH LEAGUES' CHECKS (rule 117): `verify_card.py`, through
`card.why_caveats`, on every MLB card this code builds, `test_fb_props_confidence.py`
on the football card's rows and their notes, and `test_card_fb.py` §15 on the football
projection note. A phrase is the distinctive part of a caveat sentence one
of the two removed, never a word a stat sentence needs ("model", "averaged", "never
faced" are football's own extras, for its one-sentence row only).
⚠️ Matched case-insensitively, HTML tags stripped and curly apostrophes made straight,
so "<b>Too small</b> a sample" is still caught. Stdlib only; imports nothing from the
repo.

`[2026-11-19]` AND A SECOND LIST, `PRICE_INPUT`, BY THE SAME MATCHER (`price_input()`):
the words that say a price, the books' chance or a de-vigged chance MADE a number. Sam,
2026-10-11: "only show confidence score on each pick that the model picks, BASED ON THE
MODELS CONFIDENCE SCORE NOT THE SPORTSBOOKS". A price may still say which bet is priced
and what it needs to break even ("At +120 this has to hit about 45% ... to break even",
"That price is FanDuel's"), so a phrase here is never "price" or "break even" alone.
⛔ A sentence on a row whose method reads NO price never carries one: `card.price_claims`
(verify_card.py, on every MLB card this code builds) and the football card's rows
(`test_fb_props_confidence.py`, `test_price_words.py`). A method that does read the books'
number (MLB's C2 to 2026-10-11, the football alt parlays, MARKET) may say so: it is true.
"""
import re

PHRASES = (
    # "not a forecast" and its kin (football to 10-09, the MLB hitter line to 11-18)
    "not a forecast",
    "rather than a forecast",
    "rather than a prediction",
    "history rather than",
    "not a projection",
    "one thing to know",
    "hitter model",
    "no football model",
    # "not part of the model's math" (the MLB pitcher rows' opponent log, to 11-18)
    "part of the model's math",
    "recent history",
    # the small-sample warnings (both leagues)
    "small sample",
    "small a sample",
    "read much into",
    "read anything into",
    "nothing to read",
    "to mean anything",
    # the MLB rows' ledger-era hedges (to 08-26), the same family
    "never been tested",
    # football's far-line warning and college box-score note (to 10-09)
    "a long way from what he",
    "not evidence about",
    "box scores list a player",
)

# `[2026-11-19]` the words that say a price or the books' number MADE a number (see the top).
PRICE_INPUT = (
    # MLB pitcher rows: C2, the blend with its price (2026-09-25 to 10-11), and every C1 card
    # from 10-12 to 10-28, which no price entered ("corrected against the price", "Before
    # checking it against the price it read 62%")
    "against the price",
    "against its price",
    "with the price",
    "with its price",
    "using the price",
    # the books' own chance or a de-vigged one as the number (football's alternate spreads and
    # its props model's stage 2 to 10-11; the alt parlays, MARKET, still)
    "books' chance",
    "book's chance",
    "books' own chance",
    "books' number",
    "market's chance",
    "market chance",
    "de-vig",
    "devig",
    "no-vig",
    "vig taken out",
)

_TAG = re.compile(r"<[^>]*>")


def _plain(text):
    return _TAG.sub("", str(text or "")).replace(chr(0x2019), "'").replace(chr(0x2018), "'").lower()


def found(text):
    """Every listed phrase in `text`, in list order ([] = a plain sentence)."""
    t = _plain(text)
    return [p for p in PHRASES if p in t]


def price_input(text):
    """Every `PRICE_INPUT` phrase in `text`, in list order ([] = it names no price as an
    input). The same matcher as `found()`: tags stripped, apostrophes straight, lower case."""
    t = _plain(text)
    return [p for p in PRICE_INPUT if p in t]
