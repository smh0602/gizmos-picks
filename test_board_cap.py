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

`[2026-09-28]` Item 2 is now asked of a card the BUILDER writes from a
planted board, every run; the live published cards are reported.

# @vacuity the builder's card never carries more rows than its cap (planted board)
#   file: card_fb.py
#   find: board = rows[:BOARD_MAX] if rated else fill_board(rows, BOARD_MAX)
#   with: board = rows if rated else fill_board(rows, BOARD_MAX)
#
# @vacuity the builder's card declares the cap it was built to (planted board)
#   file: card_fb.py
#   find: "board_max": BOARD_MAX,
#   with: "board_max": None,
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
# 🔴🔴 ~~ck("index.html prints the card's own board_max",
#          "C.board_max" in html or "board_max" in html, ...)~~
#    STRUCK 2026-09-14. **THAT CHECK WAS GREEN SOLELY BECAUSE OF A
#    COMMENT ASSERTING THE THING IT WAS ASSERTING.**
#
#    Measured: `C.board_max` appears in `index.html` ZERO times, and
#    `board_max` appears exactly ONCE — inside a block comment that
#    reads *"The page does not hold the number either way; it prints the
#    card's own board_max."* With comments stripped, neither needle is in
#    the file. ⛔ The `or` made the weak arm decisive, so the check
#    passed on its own documentation.
#
# ⚠️ AND THE TRAP WAS ALREADY KNOWN TO THIS FILE. The very next comment
#    below says *"ASKED OF THE FUNCTION BODIES, NOT OF THE FILE"* — the
#    author applied that fix to the following check and not to this one.
#    Sixth recorded instance of a self-matching check in this repo.
#
# 🔴🔴 AND IT WAS NOT MERELY FAKE — IT WAS BACKWARDS. It asserted the
#    page DOES hold `board_max`. Rule 66 wants the opposite: the cap
#    belongs to the builder, the page renders whatever array it is
#    handed, and a `board_max` anywhere in live JavaScript would be the
#    SECOND COPY the rule exists to forbid.
# ✅ So the correct question is the inverse of the one that was asked,
#    and it is strictly harder: a reference appearing in live code now
#    FAILS, where the old form would have called it a pass.
# ⚠️ MY OWN FIRST REPLACEMENT WAS ALSO WRONG and running it caught that:
#    it grepped for `.slice(0, NN)` and flagged six innocent lines —
#    `toISOString().slice(0,10)` taking a date, and a 30-item news list.
#    ⛔ A check that fires on correct code is the other way to be useless,
#    and the board-slicing question is already asked correctly ten lines
#    below, SCOPED TO THE FUNCTION BODIES.
_live_html = "\n".join(
    ln for ln in re.sub(r"/\*.*?\*/", "", html, flags=re.S).splitlines()
    if not ln.strip().startswith("//"))
ck("🔴 the page holds NO copy of the cap",
   "board_max" not in _live_html,
   "⛔ rule 66 — `BOARD_MAX` is the builder's. The page renders the array "
   "it is given and must not know the number at all, or the two disagree "
   "the first time one moves")
ck("⛔ ...and the comment-stripper actually removed something",
   len(_live_html) < len(html) and "board_max" in html,
   "🔴 IF THIS FAILS THE CHECK ABOVE IS VACUOUS. `board_max` occurs in "
   "index.html exactly once, inside a block comment — so it must be "
   "present in the RAW file and absent from the stripped one. Both "
   "halves are asserted, because a stripper that returned an empty "
   "string would pass the check above for the wrong reason")
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
# 🔴 `[2026-09-28]` ~~ck("no published card exceeds the cap IT declares")~~
#    over the live `picks/` asked PRODUCTION to stay silent (pattern P2):
#    one card published over its cap — a card that can never be edited —
#    would redden every run forever, and a tree with no card declaring a
#    cap passed having asked nothing. ✅ Now the scanner is driven on
#    PLANTED cards both ways, the BUILDER is shown to write a card within
#    its own declared cap from a planted board, and the live scan is a
#    note that names any over-cap card.


def over_cap(paths):
    """-> (bad, undeclared) over the given card files. ⛔ ONLY CARDS THAT
    DECLARE A CAP ARE JUDGED. The first form of this check failed on
    `fb-ncaaf-2026-09-03.json`, which predates the `board_max` field
    entirely — a fact about the schema's history, not about any card being
    over its cap. Cards without the field are REPORTED."""
    bad, undeclared = [], []
    for p in paths:
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
    return bad, undeclared


import gzip as _gz        # noqa: E402
import shutil as _sh      # noqa: E402
import subprocess as _sp  # noqa: E402
import tempfile as _tf    # noqa: E402
from tcheck import copy_module, shown  # noqa: E402

_pt = _tf.mkdtemp(prefix="boardcap-")
try:
    _pk = os.path.join(_pt, "planted-picks")
    os.makedirs(_pk)
    for _nm, _doc in (("fb-nfl-2026-09-10.json", {"board_max": 25, "picks": [{}] * 25}),
                      ("fb-nfl-2026-09-11.json", {"board_max": 25, "picks": [{}] * 26}),
                      ("fb-nfl-2026-09-12.json", {"picks": [{}] * 30})):
        json.dump(_doc, open(os.path.join(_pk, _nm), "w", encoding="utf-8"))
    open(os.path.join(_pk, "fb-nfl-2026-09-13.json"), "w").write("{ not json")
    _pb, _pu = over_cap(sorted(glob.glob(os.path.join(_pk, "fb-*-2*.json"))))
    ck("🔴 the scanner flags a planted card over its OWN cap, and an unreadable one",
       [b[0] for b in _pb] == ["fb-nfl-2026-09-11.json", "fb-nfl-2026-09-13.json"]
       and "26 picks over a cap of 25" in _pb[0][1],
       "⛔ a card at its cap passes, one row over does not. got %s" % _pb)
    ck("⚠️ ...and a card with no declared cap is REPORTED, not judged",
       _pu == ["fb-nfl-2026-09-12.json"], "got %s" % _pu)

    # ✅ THE BUILDER, ON A PLANTED BOARD WITH MORE RATED ROWS THAN THE CAP:
    #    30 players, one game each, all rated — the card must declare the
    #    cap and publish no more than it.
    # ⚠️ Letters, not digits: `norm()` strips digits, so "Player 1" and
    #    "Player 2" would be one ambiguous name and the join would refuse.
    _nm = ["Cap Player %s%s" % (chr(97 + i // 26), chr(97 + i % 26)) for i in range(30)]
    _tree = os.path.join(_pt, "tree")
    os.makedirs(os.path.join(_tree, "data/nfl/latest"))
    os.makedirs(os.path.join(_tree, "picks"))
    _kick = "2026-09-13T17:00:00Z"
    _board = {"pulled_at": "2026-09-12T22:31:00Z", "books_seen": ["fanduel"],
              "games": [{"id": "g%d" % i, "away": "A%d" % i, "home": "H%d" % i,
                         "commence": _kick,
                         "props": [{"player": _nm[i],
                                    "market": "player_receptions", "line": 3.5,
                                    "sides": {"over": {"price": -110, "book": "fanduel",
                                                       "n_books": 3, "link": "x"}}}]}
                        for i in range(30)]}
    _board["n_games"] = len(_board["games"])
    _logs = {"season": 2025, "players": {
        str(i): {"name": _nm[i], "pos": "WR",
                 "g": [{"rec": 5 if j < 3 + i % 7 else 2, "rec_yds": 30,
                        "snap_pct": 0.9, "team": "T", "game_id": "x",
                        "d": "2025-10-%02d" % (j + 1)} for j in range(10)]}
        for i in range(30)}}
    with _gz.open(os.path.join(_tree, "data/nfl/latest/props.json.gz"), "wt") as _fh:
        json.dump(_board, _fh)
    with _gz.open(os.path.join(_tree, "data/nfl/latest/players-2025.json.gz"), "wt") as _fh:
        json.dump(_logs, _fh)
    copy_module("card_fb", _tree)
    _r = _sp.run([sys.executable, "card_fb.py"], cwd=_tree,
                 env=dict(os.environ, LEAGUE="nfl"), capture_output=True, text=True)
    _lp = os.path.join(_tree, "picks", "fb-nfl-latest.json")
    _built = json.load(open(_lp, encoding="utf-8")) if os.path.exists(_lp) else None
    if _built is None:
        print(shown(_r.stdout[-1200:]), shown(_r.stderr[-1200:]))
    _rated = sum(1 for p in (_built or {}).get("picks") or []
                 if p.get("confidence") is not None)
    ck("🔴🔴 the builder, given 30 rated rows, publishes exactly its declared cap",
       _built is not None and _built.get("board_max") == card_fb.BOARD_MAX
       and len(_built.get("picks") or []) == card_fb.BOARD_MAX
       and _rated == card_fb.BOARD_MAX
       and not over_cap([_lp])[0],
       "⛔ the card carries its own board_max so a reader can check it "
       "without the source; a card over it is the page lying about its own "
       "rule. got board_max=%s, %d picks (%d rated)"
       % ((_built or {}).get("board_max"), len((_built or {}).get("picks") or []), _rated))
finally:
    _sh.rmtree(_pt, ignore_errors=True)

cards = sorted(glob.glob(os.path.join(ROOT, "picks", "fb-*-2*.json")))
if not cards:
    note("⚠️ NOT EXERCISED: no football cards on this machine. Sections "
         "1, 2 and 4 do not need them and still ran.")
else:
    bad, undeclared = over_cap(cards)
    note("%s published card(s) over the cap they declare%s — REPORTED, not "
         "asserted: a published card can never be edited (rule 76), so a hard "
         "check here would be red forever on a card nobody may fix. The "
         "builder's cap is asserted on the planted board above."
         % (len(bad), (": %s" % bad[:3]) if bad else ""))
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
# `[Sam, 2026-10-01]` PRICE_FLOOR moved legitimately, ~~-700~~ -400: "ideally
#    props/game lines at -400 is the lowest we should go" (test_price_floor.py).
for name, want in (("MIN_GAMES", 6), ("PRICE_CEIL", 400),
                   ("PRICE_FLOOR", -400)):
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
