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
"""
import gzip
import json
import os
import re
import sys

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
    "betmgm":    {"totals": {"Over": {"pt": 50.5, "px": -120}}},
})]))
eq(len(rows), 1, "one game in, one row out")
eq(rows[0]["best_price"], -105,
   "🔴 −105 beats −110 and −120 — best for a BETTOR, not numerically least")
eq(rows[0]["best_book"], "draftkings", "...and it names the book")
eq(rows[0]["n_books"], 3, "...and how many books were comparable")
ck("✅ a plus price beats every minus price",
   C.build_game_lines(snap([game("g2", {
       "fanduel": {"h2h": {"A Team": {"pt": None, "px": -105}}},
       "betmgm": {"h2h": {"A Team": {"pt": None, "px": 115}}},
       "draftkings": {"h2h": {"A Team": {"pt": None, "px": -110}}},
   })]))[0][0]["best_price"] == 115,
   "+115 pays more than −105 on the same wager")

print("\n═══ 2. 🔴 THE EXACT SIGNED NUMBER, OR NO COMPARISON ═══")
rows, meta = C.build_game_lines(snap([game("g3", {
    "fanduel":   {"spreads": {"A Team": {"pt": 1.5, "px": 130}}},
    "draftkings": {"spreads": {"A Team": {"pt": -1.5, "px": -182}}},
    "betmgm":    {"spreads": {"A Team": {"pt": -1.5, "px": -180}}},
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

print("\n═══ 3. ⛔ ONLY SAM'S FIVE BOOKS COUNT ═══")
# ⛔ THE FIXTURE MUST LEAVE A REAL EDGE AMONG SAM'S BOOKS, or the row is
#    dropped for having no gap and the check passes for the wrong reason.
#    The first form priced all three identically and failed on an EMPTY
#    list — a check that cannot distinguish "excluded correctly" from
#    "nothing to rank" is not the check it claims to be.
rows, meta = C.build_game_lines(snap([game("g4", {
    "fanduel":   {"totals": {"Over": {"pt": 44.5, "px": -102}}},
    "draftkings": {"totals": {"Over": {"pt": 44.5, "px": -115}}},
    "betmgm":    {"totals": {"Over": {"pt": 44.5, "px": -118}}},
    "fliff":     {"totals": {"Over": {"pt": 44.5, "px": 140}}},
})]))
eq(len(rows), 1, "the three eligible books leave a real gap to rank")
eq(rows[0]["best_price"], -102,
   "🔴 a much better price at a book he cannot bet does NOT win")
eq(rows[0]["n_books"], 3,
   "⛔ ...and the outside book is not even COUNTED — a price from a book "
   "he cannot bet is not a better price")
src = open("card_fb.py", encoding="utf-8").read()
collect = open("collect.py", encoding="utf-8").read()
_declared = set(re.findall(r'"([a-z_]+)":\s*"(?:Hard Rock|DraftKings|FanDuel'
                           r'|Caesars|BetMGM)"', collect))
ck("🔒 the book list here matches collect.py's, key for key",
   C.GL_BOOKS == _declared,
   "⛔ A RESTATEMENT IS A RULE 66 HAZARD, so it is CHECKED rather than "
   "trusted — the same treatment PARLAY_BANDS gets. here=%s collect=%s"
   % (sorted(C.GL_BOOKS), sorted(_declared)))

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
        "betmgm":    {"totals": {"Over": {"pt": 40.5, "px": -120}},
                      "spreads": {"A Team": {"pt": 3.5, "px": -125}}}}
rows, _ = C.build_game_lines(snap([game("g6", many)]))
eq(len(rows), 1,
   "⛔ a game mispriced in three markets is still ONE game — fifteen rows "
   "off four games is a list about four games")

print("\n═══ 6. ⛔ NOTHING HERE PREDICTS ANYTHING ═══")
rows, meta = C.build_game_lines(snap([game("g%d" % i, {
    "fanduel":   {"totals": {"Over": {"pt": 40.5 + i, "px": -100}}},
    "draftkings": {"totals": {"Over": {"pt": 40.5 + i, "px": -120}}},
    "betmgm":    {"totals": {"Over": {"pt": 40.5 + i, "px": -125}}},
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
ck("🔴 the page says FOUR pre-registered models were tested",
   "Three pre-registered football models" not in html
   and "Three football models were tested" not in html,
   "⛔ T57 closed FAILED on 2026-09-11, so 'three' became false the "
   "moment it did. A stale count on a page about honesty is the wrong "
   "sentence to leave standing")
ck("...and so does the builder's own note",
   "Three pre-registered" not in src,
   "the card writes this sentence; the page prints it")

note("⛔ WHAT THIS LIST IS NOT: a view about who wins. It ranks the gap "
     "between books on the SAME wager, which is why it is allowed a "
     "number at all. ➡️ If a team-bet model is ever wanted, the bar is "
     "not 'beat a naive average' — for game lines the MARKET is the "
     "benchmark, and the test would have to beat the CLOSING LINE.")
