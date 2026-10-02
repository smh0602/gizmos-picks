#!/usr/bin/env python3
"""
🔴 GAME LINES — RANKED BY PRICE, NEVER BY PROBABILITY.

`[Sam, 2026-09-11]` *"i also would like you to start adding moneyline,
team total, spread... in football betting all of these categories may be
more popular than player props."* ✅ **True — and popularity and sharpness
are the same thing.** These are the most liquid markets in sport, which is
exactly why they are the hardest to beat.

⛔ **HE ALSO SAID "you would use the same model to make these picks."
THERE IS NO SUCH MODEL, IN EITHER SPORT.** Football has none at all —
**T46, T47, T50 and now T57** each lost to a player's own season average —
and MLB's model prices pitcher strikeouts and outs, which has no opinion
about who wins a game. **A "model's best 15" here would be a number nobody
measured**, on a page bet against with real money.

✅ **SO THE LIST RANKS SOMETHING REAL INSTEAD: how much more the BEST book
pays than a TYPICAL one, on the SAME WAGER.** `[measured 2026-09-10 on the
live college board]` **276 quotes** were comparable across 3+ of Sam's
five books; the best gains ran **3–5%** and the median was **0.93%**.

⚠️ **That is arithmetic on quotes already stored. It makes no forecast, so
it cannot be wrong about a game** — which is the whole reason it is
allowed to carry a number when nothing else here is.

🔴 **THE EXACT SIGNED NUMBER, ALWAYS.** `CLAUDE.md`: eleven books posted
ATL −1.5 while two posted the same game inverted, and matching on |point|
paired **opposite bets**. Every comparison group here is keyed on
`(market, side, SIGNED point)`.

`[Sam, 2026-10-01]` The page shows each tab's content, not notes about it:
§9 and §10 asked for a model-count sentence, a MARKET badge, a glyph note
and a styled badge class on the page; they now ask for their ABSENCE, and
§10 still asks that the list itself is drawn. The card side (§1–§7, and
the builder's own sentence in §9) is unchanged.

# @vacuity the page states no model count: the FOUR went with its note boxes [Sam, 2026-10-01]
#   file: index.html
#   find: <h2>Game lines &mdash; the ${g.length} biggest price gaps</h2>
#   with: <h2>Game lines &mdash; the ${g.length} biggest price gaps</h2><p>Four pre-registered football models were tested and every one lost.</p>
#
# @vacuity the game-lines panel carries no MARKET badge [Sam, 2026-10-01]
#   file: index.html
#   find: <h2>Game lines &mdash; the ${g.length} biggest price gaps</h2>
#   with: <h2>Game lines &mdash; the ${g.length} biggest price gaps <span class="kind k-market">Market</span></h2>
#
# @vacuity ...and no note under it, in either glyph [Sam, 2026-10-01]
#   file: index.html
#   find: style="font-size:10px">${bookName(r.best_book)}</div></div>`).join('')}</div></div>`;
#   with: style="font-size:10px">${bookName(r.best_book)}</div></div>`).join('')}</div><div class="note">&#128309; <b>Market, not a model.</b></div></div>`;
#
# @vacuity ...and the stylesheet styles no badge class [Sam, 2026-10-01]
#   file: index.html
#   find: .glr.nofloor{opacity:.62}
#   with: .glr.nofloor{opacity:.62} .k-market{background:#e6eefc;color:#1a4b9c}
#
# @vacuity ...and the list itself is still drawn, every number [Sam, 2026-10-01]
#   file: index.html
#   find: <div class="p">${sgn(r.best_price)}<div class="rec"
#   with: <div class="p"><div class="rec"
"""
import gzip
import json
import os
import re
import sys

from jsblock import css_rules
from tcheck import ck, eq, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

os.environ.setdefault("LEAGUE", "ncaaf")
import card_fb as C  # noqa: E402


def snap(games):
    return {"games": games}


def game(gid, books, away="A Team", home="H Team"):
    return {"id": gid, "away": away, "home": home,
            "commence": "2026-09-11T00:00:00Z", "books": books}


print("\n═══ 1. 🔴 THE BEST PRICE IS BEST FOR A BETTOR ═══")
rows, meta = C.build_game_lines(snap([game("g1", {
    "fanduel":   {"totals": {"Over": {"pt": 50.5, "px": -110}}},
    "draftkings": {"totals": {"Over": {"pt": 50.5, "px": -105}}},
    "hardrockbet":    {"totals": {"Over": {"pt": 50.5, "px": -120}}},
})]))
eq(len(rows), 1, "one game in, one row out")
eq(rows[0]["best_price"], -105,
   "🔴 −105 beats −110 and −120 — best for a BETTOR, not numerically least")
eq(rows[0]["best_book"], "draftkings", "...and it names the book")
eq(rows[0]["n_books"], 3, "...and how many books were comparable")
ck("✅ a plus price beats every minus price",
   C.build_game_lines(snap([game("g2", {
       "fanduel": {"h2h": {"A Team": {"pt": None, "px": -105}}},
       "hardrockbet": {"h2h": {"A Team": {"pt": None, "px": 115}}},
       "draftkings": {"h2h": {"A Team": {"pt": None, "px": -110}}},
   })]))[0][0]["best_price"] == 115,
   "+115 pays more than −105 on the same wager")

print("\n═══ 2. 🔴 THE EXACT SIGNED NUMBER, OR NO COMPARISON ═══")
rows, meta = C.build_game_lines(snap([game("g3", {
    "fanduel":   {"spreads": {"A Team": {"pt": 1.5, "px": 130}}},
    "draftkings": {"spreads": {"A Team": {"pt": -1.5, "px": -182}}},
    "hardrockbet":    {"spreads": {"A Team": {"pt": -1.5, "px": -180}}},
})]))
ck("🔴 +1.5 and −1.5 are NOT the same wager and are never compared",
   not rows or rows[0]["point"] == -1.5,
   "⛔ THE LIVE MLB CASE: eleven books posted ATL −1.5 while two posted "
   "the same game inverted. Matching on |point| paired 'Milwaukee −1.5 at "
   "+130' against a market whose real price is '+1.5 at −182' — opposite "
   "bets, and the page would have advertised a bargain that does not "
   "exist. Rows: %s" % [(r["point"], r["best_price"]) for r in rows])
ck("⛔ ...and a lone quote at its own number is not a comparison at all",
   meta["comparable_quotes"] <= 1,
   "one book at +1.5 has nothing to be measured against: %d comparable"
   % meta["comparable_quotes"])

print("\n═══ 3. ⛔ ONLY SAM'S THREE FOOTBALL BOOKS COUNT ═══")
# ⛔ THE FIXTURE MUST LEAVE A REAL EDGE AMONG SAM'S BOOKS, or the row is
#    dropped for having no gap and the check passes for the wrong reason.
#    The first form priced all three identically and failed on an EMPTY
#    list — a check that cannot distinguish "excluded correctly" from
#    "nothing to rank" is not the check it claims to be.
rows, meta = C.build_game_lines(snap([game("g4", {
    "fanduel":   {"totals": {"Over": {"pt": 44.5, "px": -102}}},
    "draftkings": {"totals": {"Over": {"pt": 44.5, "px": -115}}},
    "hardrockbet":    {"totals": {"Over": {"pt": 44.5, "px": -118}}},
    "fliff":     {"totals": {"Over": {"pt": 44.5, "px": 140}}},
    # 🔴 `[2026-09-22]` BetMGM is no longer one of Sam's football books.
    "betmgm":    {"totals": {"Over": {"pt": 44.5, "px": 150}}},
})]))
eq(len(rows), 1, "the three eligible books leave a real gap to rank")
eq(rows[0]["best_price"], -102,
   "🔴 a much better price at a book he cannot bet does NOT win")
eq(rows[0]["n_books"], 3,
   "⛔ ...and the outside book is not even COUNTED — a price from a book "
   "he cannot bet is not a better price")
src = open("card_fb.py", encoding="utf-8").read()
collect = open("collect.py", encoding="utf-8").read()
# 🔴 `[2026-09-22]` football is THREE books (Sam: "just use those three"),
#    declared in `collect.FB_BOOK_KEYS`; MLB keeps the five in `BOOKS`.
_m = re.search(r"^FB_BOOK_KEYS\s*=\s*\(([^)]*)\)", collect, re.M)
_declared = set(re.findall(r'"([a-z_]+)"', _m.group(1))) if _m else set()
ck("🔒 the book list here matches collect.py's, key for key",
   C.GL_BOOKS == _declared,
   "⛔ A RESTATEMENT IS A RULE 66 HAZARD, so it is CHECKED rather than "
   "trusted — the same treatment PARLAY_BANDS gets. here=%s collect=%s"
   % (sorted(C.GL_BOOKS), sorted(_declared)))

rows, meta = C.build_game_lines(snap([game("g4b", {
    "hardrockbet":    {"totals": {"Over": {"pt": 44.5, "px": -102}}},
    "hardrockbet_oh": {"totals": {"Over": {"pt": 44.5, "px": -110}}},
    "draftkings":     {"totals": {"Over": {"pt": 44.5, "px": -115}}},
})]))
eq(len(rows), 0,
   "⛔ Hard Rock's Ohio skin is the SAME book: two skins + one other is "
   "two books, not the three a comparison needs")

print("\n═══ 4. ⚠️ A THIN MARKET IS NOT AN EDGE ═══")
rows, meta = C.build_game_lines(snap([game("g5", {
    "fanduel":   {"totals": {"Over": {"pt": 44.5, "px": 120}}},
    "draftkings": {"totals": {"Over": {"pt": 44.5, "px": -110}}},
})]))
eq(len(rows), 0,
   "⛔ two books is not a median — %d+ are required or nothing is claimed"
   % C.SHOP_MIN_BOOKS)
eq(C.SHOP_MIN_BOOKS, 3, "...and the floor is stated, not implicit")

print("\n═══ 5. 🔴 ONE ROW PER GAME ═══")
many = {"fanduel":   {"totals": {"Over": {"pt": 40.5, "px": -100}},
                      "spreads": {"A Team": {"pt": 3.5, "px": -100}}},
        "draftkings": {"totals": {"Over": {"pt": 40.5, "px": -120}},
                       "spreads": {"A Team": {"pt": 3.5, "px": -120}}},
        "hardrockbet":    {"totals": {"Over": {"pt": 40.5, "px": -120}},
                      "spreads": {"A Team": {"pt": 3.5, "px": -125}}}}
rows, _ = C.build_game_lines(snap([game("g6", many)]))
eq(len(rows), 1,
   "⛔ a game mispriced in three markets is still ONE game — fifteen rows "
   "off four games is a list about four games")

print("\n═══ 6. ⛔ NOTHING HERE PREDICTS ANYTHING ═══")
rows, meta = C.build_game_lines(snap([game("g%d" % i, {
    "fanduel":   {"totals": {"Over": {"pt": 40.5 + i, "px": -100}}},
    "draftkings": {"totals": {"Over": {"pt": 40.5 + i, "px": -120}}},
    "hardrockbet":    {"totals": {"Over": {"pt": 40.5 + i, "px": -125}}},
}) for i in range(25)]))
eq(len(rows), C.GAME_LINES_N, "🔴 the list is capped at Sam's 15")
ck("🔴 every row is labelled MARKET",
   {r["kind"] for r in rows} == {"MARKET"},
   "ledger rule 55 — and there is no MODEL to claim: T46, T47, T50 and "
   "T57 all lost to a player's own season average")
ck("⛔ no row carries a confidence, a probability or a projection",
   not any(k in r for r in rows
           for k in ("confidence", "confidence_basis", "projection",
                     "blend", "band", "edge", "win_pct")),
   "⛔ a number that looks like a chance of winning, on a list ranked by "
   "price, would be the exact misrepresentation this ranking avoids")
ck("✅ ...and the rule sentence says so in words",
   "not a prediction" in C.game_lines_rule(rows, meta),
   C.game_lines_rule(rows, meta)[:120])

print("\n═══ 7. ⚠️ AN EMPTY BOARD IS A FACT ABOUT THE BOARD ═══")
rows, meta = C.build_game_lines(snap([]))
eq(rows, [], "no games in, no rows out")
_r = C.game_lines_rule(rows, meta)
ck("⚠️ ...and it says so without implying a view about the games",
   "not enough agreement to compare prices" in _r and "fact about" in _r,
   _r[:140])

print("\n═══ 8. 🔴 THE PAGE RENDERS IT, AND ON AN EMPTY PROPS BOARD ═══")
html = open("index.html", encoding="utf-8").read()
ck("the page has a game-lines renderer",
   "function fbGameLines(C){" in html, "")
ck("🔴 ...and it is CALLED from the empty-props branch too",
   html.count("fbGameLines(C)") >= 3,
   "⛔ THE BUG THE BROWSER CAUGHT: that branch returned before reaching "
   "the section, so on a day with no player props the game lines simply "
   "never drew — invisible in the source, obvious on the page (rule 197). "
   "⚠️ A props board and a game-line board are DIFFERENT MARKETS. Found "
   "%d call site(s)" % html.count("fbGameLines(C)"))
ck("⛔ the page does not re-rank or re-compute the gap",
   "gain_pct" in html and "median_price" not in html,
   "rule 132 — the page prints what the builder computed; a second copy "
   "of the selection rule is a second thing to drift")

print("\n═══ 9. ⚠️ THE MODEL COUNT IS FOUR NOW, NOT THREE ═══")
# [Sam, 2026-10-01] ~~the page says FOUR pre-registered models were tested~~
#    The sentence lived in two note boxes (the props tab's footer and
#    fbNoModelNote), and every explanation box is gone. So the page states
#    NO count now: not the stale THREE, and not the FOUR either. The
#    builder still writes its own sentence (next check, unchanged).
ck("🔴 the page states no model count — never the stale THREE, and since 2026-10-01 not the FOUR either",
   "Three pre-registered football models" not in html
   and "Three football models were tested" not in html
   and "Four pre-registered football models" not in html
   and "Four football models were tested" not in html,
   "⛔ T57 closed FAILED on 2026-09-11, so 'three' became false the "
   "moment it did. A stale count on a page about honesty is the wrong "
   "sentence to leave standing. [Sam, 2026-10-01] the boxes that said "
   "'four' are gone with every other explanation box")
# Card side, unchanged. [Sam, 2026-10-01] "the page prints it" below is
#    history: the card still writes the sentence, the page no longer shows it.
ck("...and so does the builder's own note",
   "Three pre-registered" not in src,
   "the card writes this sentence; the page prints it")

print("\n═══ 10. \U0001f534 THE SECTION IS AS PLAIN AS THE PAGE: NO BADGE, NO NOTE ═══")
# \U0001f534 FOUND 2026-09-11 BY READING THE RENDERED DOM, NOT THE SOURCE —
#    the THIRD instance of rule 197's shape. §6 above asserts no row
#    carries a confidence and §8 asserts the section DRAWS. ⛔ Neither
#    asks whether the drawn section is LABELLED, and it was not:
#      panel.querySelectorAll('.kind')  ->  []
#    while every other section on that tab carries a badge. The only
#    badge on the picks tab read "Record", belonging to the block ABOVE
#    a numbered list of percentages. ➡️ ASSERTING A WRONG THING IS
#    ABSENT IS NOT ASSERTING THE RIGHT THING IS PRESENT.
# [Sam, 2026-10-01] ~~THE SECTION LABELS ITSELF THE WAY THE PAGE LABELS~~
#    — and it still does, because the page labels nothing now. Sam: "i
#    just want what's supposed to be in each tab to be in each tab"; asked
#    what stays, he chose: remove everything. The MARKET badge, the 🔵
#    "Market, not a model." note and the badge's stylesheet rule that were
#    REQUIRED here are now required ABSENT, and so is the builder's rule
#    sentence the panel used to print. Every row still carries kind MARKET
#    in the card (§6, unchanged). ⛔ And per the line above, three absences
#    pass on an EMPTY renderer, so the last check asks that the list
#    itself is still drawn.
_gl = html[html.index("function fbGameLines(C){"):]
_gl = _gl[:_gl.index("\nfunction ", 1)]
# ~~the panel carries the page's own MARKET badge~~
ck("\U0001f534 the panel carries no badge: its heading is the bare title",
   "<h2>Game lines &mdash; the ${g.length} biggest price gaps</h2>" in _gl
   and 'class="kind' not in _gl and "k-market" not in _gl,
   "[Sam, 2026-10-01] no MODEL / MARKET / DESCRIPTIVE tag on any tab. "
   "~~LEDGER RULE 55 — every number on the surface is labelled MODEL, "
   "MARKET or DESCRIPTIVE~~ on the page; the row's MARKET kind stays in "
   "the card")
# ~~the note uses the MARKET glyph, not the DESCRIPTIVE one~~
ck("⛔ ...and no note under it, in either glyph, and no rule sentence",
   "&#128309;" not in _gl and "&#9898;" not in _gl
   and 'class="note"' not in _gl and "game_lines_rule" not in _gl,
   "\U0001f534 THE ORIGINAL SHIPPED `&#9898;` — the glyph for "
   "'Descriptive.' — against the words 'Market, not a model.' "
   "[Sam, 2026-10-01] the note is gone with every explanation box, so "
   "neither glyph returns; the rule sentence stays in the card (§6, §7)")
# ~~the badge classes referenced here are the ones the stylesheet defines~~
_badge_css = [s for s, d in css_rules("index.html").items()
              if re.search(r"\.(?:kind|k-market)(?![\w-])", s + "{" + d)]
ck("✅ ...and the stylesheet styles neither badge class, so no tag can render as one",
   not _badge_css,
   "rule 66 — a class name invented in one place and styled in none "
   "renders as unstyled text. [Sam, 2026-10-01] the panel references "
   "neither `kind` nor `k-market` now, and a class styled with nothing "
   "drawing it is the same drift from the other side. Styled: %s"
   % (_badge_css or "none"))
ck("✅ ...and the list itself is still drawn: rank, wager, the gain, the best price and its book",
   all(s in _gl for s in ('<div class="t10">', '<div class="r">${i + 1}</div>',
                          '<div class="c">+${r.gain_pct}%</div>',
                          '${sgn(r.best_price)}', '${bookName(r.best_book)}')),
   "[Sam, 2026-10-01] kept: tables and cards with every number. Asserting "
   "a wrong thing is absent is not asserting the right thing is present")


note("⛔ WHAT THIS LIST IS NOT: a view about who wins. It ranks the gap "
     "between books on the SAME wager, which is why it is allowed a "
     "number at all. ➡️ If a team-bet model is ever wanted, the bar is "
     "not 'beat a naive average' — for game lines the MARKET is the "
     "benchmark, and the test would have to beat the CLOSING LINE.")
