#!/usr/bin/env python3
"""card_fb.py — the football picks board.

    python card_fb.py            # LEAGUE from env, default nfl
    LEAGUE=ncaaf python card_fb.py

🔴 THIS IS NOT A MODEL AND MUST NEVER BECOME ONE WITHOUT A PRE-REGISTERED
TEST. Three football specifications have already been tested and all three
LOST to a player's own season average — T46 (+0.0010), T47 (−0.0041),
T50 (−0.0036) against a +0.0050 bar — plus eight opponent constructs
across T36–T49. ⛔ **Ledger rule 55: a MARKET number never wears a Gizmo's
confidence %.**

✅ SO EVERY NUMBER HERE IS `RECORD` — the player's own rate at that exact
line, smoothed with a Jeffreys prior. Exactly what an MLB HITTER row is,
and it renders through the same `pickCard` component. That is what "the
same layout as MLB" means for a sport with no model: the same board, the
same columns, the same sort — with the number's PROVENANCE labelled
honestly on the row.

════════════════════════════════════════════════════════════════════════
~~🔴 THE FINDING THAT SHAPES THIS WHOLE FILE — measured 2026-09-03~~
⛔ **STRUCK 2026-09-04. THE COMPARISON WAS NOT VALID.** Ledger rule 75.
════════════════════════════════════════════════════════════════════════
~~**NFL AND COLLEGE LOGS ANSWER DIFFERENT QUESTIONS, AND ONLY ONE OF THEM
SUPPORTS A HIT RATE.** Measured on 2025: NFL WR games with ZERO receptions
25.8%, CFB WR 3.5% — so blank games are MISSING from college. The median
CFB receiver is missing 6 of his team's 13 games. **THEREFORE: NFL rows
carry a RECORD confidence. COLLEGE ROWS DO NOT.**~~

🔴 **WHY THAT WAS WRONG, AND IT WAS WRONG IN THE PREMISE, NOT THE
ARITHMETIC.** Both percentages are correct. They are not comparable:
**nflverse logs a game when a player took a SNAP; CFBD logs a game when he
RECORDED A STAT.** A file that logs snap-only games *necessarily* shows
more zero-catch games. ⛔ **The 25.8-vs-3.5 gap is produced by the two
file formats, and says nothing about how much college data is missing.**

✅ **ASKED THE SAME WAY — share of the player's TEAM's games, one filter,
both leagues** `[measured 2026-09-04]`:

    games with ANY of rec/car/att     college    NFL    NFL TRUTH (snaps)
      WR                                0.750   0.706        0.842
      TE                                0.615   0.657        0.756
      RB                                0.857   0.882        0.941

**College is not meaningfully worse than the NFL — on receivers it is
better.**

════════════════════════════════════════════════════════════════════════
✅ SO COLLEGE ROWS NOW CARRY A RATE, OVER A **UNION** DENOMINATOR
════════════════════════════════════════════════════════════════════════
The denominator is **every game he appears in for any reason** — a carry,
a catch, an attempt — not only the games he recorded the stat the market
is about. ⚠️ Worth **+35.7 points** for a college RB and a rounding error
for a WR, **replicated in the NFL (+29.4 / +0.0)**.

🔴 **THE RESIDUAL ERROR IS REAL, KNOWN, AND ONE-DIRECTIONAL** — a game he
played and did nothing in is still missing, so an OVER reads high. **T52b
measured exactly that, in the NFL, where the true denominator exists:**
the same Jeffreys-smoothed rate computed both ways and differenced.

    BAR, fixed before the numbers printed:  median |bias| <= 3.0 points
                                            AND p90 <= 8.0
    (the card buckets confidence in 10-point calibration bands; an error
     that can move a row ACROSS a band changes what the page says)

    RESULT   pooled n=2,142   median 0.21   p90 3.79      PASS

⛔ **ONE CELL FAILED AND IS GATED, NOT ROUNDED AWAY:** WR receptions
over 2.5 — p90 **8.58**, max 19.44. See `RATE_MIN_REC_LINE`.
⚠️ **THE TRANSFER IS AN ASSUMPTION AND IS NAMED AS ONE.** The bias was
measured in the NFL and applied to college; the support is that the union
ratios above sit within 2.5 points across both leagues. **Support, not
proof.** T52b/T52c in `claude/owed-tests.md` carry the bars, and ⛔ **they
do not move now that the numbers have been seen.**

════════════════════════════════════════════════════════════════════════
🔴 THE SNAP FLOOR IS LOAD-BEARING AND IS PRE-REGISTERED, NOT FITTED
════════════════════════════════════════════════════════════════════════
This is MLB's cameo bug in a different sport. Measured on 2025 NFL WR/TE:

    snap floor      games   under 2.5 rec   under 39.5 rec yds
        none         3979        62.2%            73.4%
        0.25         3088        51.7%            66.4%
        0.50         2147        38.3%            56.1%

**A 23.9-POINT SWING ON THE SAME PLAYERS.** With no floor, a WR3 playing
16% of snaps and catching nothing counts as evidence about a WR1's line —
and short unders would top the board, which is precisely how MLB's hitter
half went wrong before `pa >= 3` replaced `pa > 0`.

⛔ `SNAP_FLOOR = 0.50` IS CHOSEN AS A BRIGHT LINE — *a majority of his
team's offensive snaps is a starter's role* — NOT by reading the table
above for the friendliest number. ⚠️ It is written here before any board
was built with it, and **T51 in `claude/owed-tests.md` is the test that
will check it against real outcomes** once 2026 games accumulate.
⛔ Do not tune it. If it is wrong, it gets a test, not an adjustment.
"""
import glob
import gzip
import itertools
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone

LEAGUE = os.environ.get("LEAGUE", "nfl")
if LEAGUE not in ("nfl", "ncaaf"):
    print(f"FATAL: card_fb.py is football only, got LEAGUE={LEAGUE!r}")
    sys.exit(1)
DATA = f"data/{LEAGUE}"
LG_NAME = {"nfl": "NFL", "ncaaf": "College Football"}[LEAGUE]

# ~~🔴 NFL ONLY. the college denominator is contaminated and no amount of
# care here fixes it.~~ ⛔ **STRUCK 2026-09-04. THE COMPARISON THAT
# JUSTIFIED IT WAS NOT VALID** -- see the docstring and ledger rule 75.
# ✅ BOTH LEAGUES MAY CARRY A RATE. Which MARKETS may is a separate
# question, answered by `market_rateable()` from a measured bias.
RATES_OK = True

SNAP_FLOOR = 0.50        # pre-registered, see docstring. ⛔ do not tune
MIN_GAMES = 6            # a rate on fewer games is not a rate

# 🔴 THE ONE CELL THAT FAILED T52b, AND THE ONLY THING GATED BECAUSE OF IT.
# `[measured 2026-09-04 in the NFL, where the true denominator EXISTS]`
# Using a union denominator instead of the true one biases an OVER rate
# upward, and the bias grows as the line falls, because a missing game is
# always a quiet one:
#
#     WR receptions o2.5    median +2.19   p90 8.58 🔴   max 19.44
#     WR receptions o3.5    median +1.32   p90 5.00      max 12.50
#     WR receptions o4.5    median +0.82   p90 3.21      max  6.94
#
# ⛔ THE BAR WAS FIXED BEFORE THOSE NUMBERS PRINTED: median <= 3.0 and
# p90 <= 8.0, derived from the card's own 10-point calibration bands --
# an error that can move a row ACROSS a band changes what the page says
# about a bet. o2.5 breaches it; o3.5 does not.
# ⚠️ APPLIED TO ALL POSITIONS, not just WR. Lines below 2.5 were never
# tested and the MECHANISM says they are worse, so the floor is set at
# the lowest line that passed rather than at the lowest that failed.
# ⛔ Do not lower it to put more rows on the board. If it is wrong it
# gets a test, not an adjustment.
RATE_MIN_REC_LINE = 3.5

# ⚠️ EVERY OTHER CARDED MARKET WAS MEASURED AGAINST THE SAME BAR, and a
# market that was never measured does NOT inherit a pass from one that
# was (T52c, 2026-09-04, pooled median 0.00 / p90 2.24 over 1,058
# player-lines):
#   passing yards  o199.5/o249.5   median +0.00  p90 0.00
#   rushing yards  o29.5/49.5/69.5 median +0.00  p90 <= 2.11
#   receiving yds  o39.5/o49.5     median +1.92  p90 <= 7.93  (marginal)
#   carries        o8.5/o12.5      median +0.00  p90 <= 1.61
#   anytime TD                     median +1.14  p90 <= 6.25  max 25.00
# ⛔ `player_pass_tds` IS DELIBERATELY ABSENT. It was not in either test,
# so on college it carries a price and no rate -- exactly the treatment
# every college market had yesterday. Adding it needs a measurement, not
# an assumption that it resembles passing yards.
RATE_MEASURED = frozenset({
    "player_pass_yds", "player_rush_yds", "player_reception_yds",
    "player_receptions", "player_anytime_td",
})
PRICE_FLOOR = -700       # Sam's standing floor, same as MLB

# 🔴 A CEILING, BECAUSE "LIKELY AND PAYABLE" HAS TWO ENDS.
# ⛔ MEASURED ON THE LIVE 2026-09-03 COLLEGE BOARD: the card was 100%
# Anytime TD and its TOP ROW WAS +5000 -- a ~2% shot leading a picks
# board. With no rate to sort by, the fallback sorted on price DESCENDING,
# so the longest longshot on the slate won every time.
# ⚠️ Sam's own MLB gate is -400: "likely AND payable". -400 is ~80%
# implied; +400 is its MIRROR at ~20%. ⛔ This is Sam's number reflected,
# NOT a value picked by looking at which cutoff produced a nicer board.
PRICE_CEIL = 400

# 🔴 NO SINGLE MARKET MAY OWN THE BOARD. Sam, 2026-09-04: *"touchdown bets
# are basically long shots, td props the model likes are good to bet on
# but not every single td prop on the board should be in gizmos picks."*
# ⚠️ The board is built ROUND-ROBIN across markets, so receptions, rushing,
# receiving and passing all appear rather than one market crowding out the
# rest. ⛔ Within a market the order is unchanged -- this decides the MIX,
# never the ranking inside a market.
MARKET_MAX_SHARE = 0.34   # no market may exceed a third of the board
BOARD_MAX = 50           # same as MLB's board

# ══════════════════════════════════════════════════════════════════════
# 🔴 THE BOARD IS ONE DAY. Sam, 2026-09-04: *"only games on the day the
# run happens. minimum 5 picks, maximum 50. a day with no games means an
# EMPTY tab, and that is correct."*
#
# ⛔ THIS IS NOT A HYPOTHETICAL. `[measured 2026-09-05 across all 18
# published cards with picks]` exactly one card mixes days --
# `picks/fb-ncaaf-2026-09-03.json` is HEADED `2026-09-03` and **19 of its
# 50 picks are 09-04 games**. The header said Wednesday and 38% of the
# board was Thursday. Every other card is clean, so this reads as rare
# rather than harmless: it is what a 14-hour props window does whenever
# it happens to straddle midnight ET.
#
# 🔴 WHICH DAY, AND WHY IT IS NOT THE WALL CLOCK. Sam's words are "the day
# the run happens", and read literally off the clock that is DANGEROUS at
# the boundary: a converge pass at 01:00 ET Sunday would decide the day is
# Sunday, find no Sunday games, and OVERWRITE a good Saturday card with an
# empty one. ✅ So the day is `slate_date(B)` -- the ET date of the
# earliest game on the board, which is ALREADY the card's own `date` field
# under ledger rule 60. The change is that the date now describes every
# row on the card, which today it does not. That is rule 66: one number
# per fact.
#
# ⚠️ FIVE IS A FLOOR TO REACH FOR, NOT A GATE THAT EMPTIES THE BOARD. The
# only way to force a minimum is to lower a bar, and every other rule here
# forbids that. ➡️ So a short day ships what it has AND SAYS SO on the
# page, with the count. ⛔ Never padded, never hidden.
BOARD_MIN = 5

# ══════════════════════════════════════════════════════════════════════
# 🔴 TOP PLAYS OF THE DAY. Sam: *"top plays of the day, at the bottom of
# Gizmo's Picks, same single-day rule, capped at 20."*
#
# ⛔ AND THE HONEST FINDING FIRST, BECAUSE IT CHANGES WHAT THIS LIST IS.
# MLB's `build_top10` is a genuinely DIFFERENT list from its board: its
# pool is wider (every alt ladder rung, which never reaches the board) and
# its gate is narrower (nothing priced worse than -400). ⛔ **NEITHER OF
# THOSE BITES ON FOOTBALL**, and it was measured rather than assumed:
#
#   `[measured 2026-09-05 on the live college board]`
#     alternate markets in the football props feed            NONE
#       (player_anytime_td, pass_yds, rush_yds, reception_yds,
#        receptions -- no `_alternate` key exists at all)
#     rows dropped by a -400 payable gate                     0 of 50
#       (football props price near even; the SHORTEST on the
#        whole board is -160)
#     players shared between a payable/deduped top-20 and
#       the board's first 20 rows                             18 of 20
#
# ➡️ **SO ON FOOTBALL THIS IS A HIGHLIGHTS LIST, NOT A SECOND OPINION**, and
# the card says so in `top_plays_rule` and the page prints it. ⛔ It must
# never be quoted as independent evidence about a play -- it is drawn from
# the same rows, ranked by the same number.
#
# ✅ WHAT IT DOES ADD, AND THE ONLY THING IT ADDS TODAY: **one row per
# player.** `[measured]` the 50-row board carries only **39 distinct
# players**, so eleven of its rows are a second line on somebody already
# listed. A top-20 that repeats a player is a top-13 wearing a bigger
# number.
#
# ⚠️ THE PRICE FLOOR IS SAM'S AND IT IS SHARED WITH `card.py`, NOT RETYPED
# AS A COINCIDENCE. `test_top_plays.py` asserts the two files agree, the
# same way the parlay bands are cross-checked -- restating a number in two
# files is the rule 66 hazard, whether or not it currently matches.
TOP_N = 20
TOP_PRICE_FLOOR = -400

# market -> (how to read it out of a game row, unit, higher-is-a-hit)
def _td(g):
    return (float(g.get("rec_td") or 0) + float(g.get("rush_td") or 0)
            + float(g.get("pass_td") or 0) * 0)   # a passing TD is not "anytime"


MARKETS = {
    "player_pass_yds":      (lambda g: float(g.get("pass_yds") or 0), "pass yds"),
    "player_pass_tds":      (lambda g: float(g.get("pass_td") or 0),  "pass TD"),
    "player_rush_yds":      (lambda g: float(g.get("rush_yds") or 0), "rush yds"),
    "player_reception_yds": (lambda g: float(g.get("rec_yds") or 0),  "rec yds"),
    "player_receptions":    (lambda g: float(g.get("rec") or 0),      "rec"),
    "player_anytime_td":    (_td,                                     "TD"),
}
LABEL = {
    "player_pass_yds": "Passing yards", "player_pass_tds": "Passing TDs",
    "player_rush_yds": "Rushing yards", "player_reception_yds": "Receiving yards",
    "player_receptions": "Receptions",  "player_anytime_td": "Anytime TD",
}


def log(m):
    print(f"[{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}] {m}", flush=True)


def norm(n):
    """Fold a name to something two sources can agree on.

    ⚠️ Accents, punctuation, and Jr/Sr/III all differ between the Odds API
    and the stats feed. ⛔ This does NOT try to be clever about nicknames --
    a name that does not match is reported as unmatched, never guessed at.
    """
    n = unicodedata.normalize("NFKD", n or "")
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower().replace("&", "and")
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", " ", n)
    n = re.sub(r"[^a-z ]", " ", n)
    return " ".join(n.split())


SCOPES = {}
LOG_SCOPE = None


def load_logs():
    """Newest season with enough games to READ A RATE. (season, {pid: player}).

    🔴 ~~"Newest season that actually has games."~~ ⛔ **THAT WAS WRONG AND
    IT WOULD HAVE EMPTIED THE BOARD FOR THE FIRST SIX WEEKS OF EVERY
    SEASON, SILENTLY.** `[measured 2026-09-04]` the live college run picked
    `players-2026.json.gz` — **74 players, one game each** — because one
    week had been played, and `MIN_GAMES = 6` then refused every rate. The
    board shipped 0 of 50 rows with a record and nothing said why. ⚠️ The
    NFL would have done the same thing on the Tuesday after week 1.

    ✅ **A SEASON IS USABLE WHEN A TYPICAL PLAYER IN IT COULD CLEAR THE
    FLOOR** — median games per player >= `MIN_GAMES`. Below that the file
    exists but cannot answer the question being asked of it.
    ⚠️ Falling back to last season is the DESIGNED behaviour, not a
    workaround: every row already says "this is his own record from last
    season", and roster churn is a stated, accepted limit.
    ⛔ ONE SEASON, NEVER A BLEND. Mixing two seasons' games into one
    denominator would make the rate a property of the file mix rather than
    of the player.
    """
    usable, thinner = None, None
    for f in sorted(glob.glob(f"{DATA}/latest/players-*.json.gz"), reverse=True):
        try:
            d = json.load(gzip.open(f, "rt"))
        except Exception:
            continue
        P = d.get("players") or {}
        SCOPES[os.path.basename(f)] = d.get("scope")
        counts = sorted(len(p.get("g") or []) for p in P.values())
        if not counts or counts[-1] == 0:
            log(f"  {os.path.basename(f)}: no games yet, skipping")
            continue
        med = counts[len(counts) // 2]
        row = (d.get("season"), P, os.path.basename(f), med)
        if thinner is None:
            thinner = row
        if med >= MIN_GAMES:
            usable = row
            break
        log(f"  {os.path.basename(f)}: median {med} game(s) per player, "
            f"under the {MIN_GAMES} needed for a rate — looking further back")
    best = usable or thinner
    if not best:
        log("FATAL: no player log with any games")
        sys.exit(1)
    season, P, fn, med = best
    global LOG_SCOPE
    LOG_SCOPE = SCOPES.get(fn)
    log(f"logs: {fn} — {len(P)} players, season {season}, "
        f"median {med} games/player"
        + (f", scope: {LOG_SCOPE}" if LOG_SCOPE else ""))
    if usable is None:
        # ⛔ SAID OUT LOUD. A board with no rates because the season is
        # young is a legitimate state; a board with no rates and no
        # explanation is the failure.
        log(f"  ⚠️ NO season has a median of {MIN_GAMES}+ games yet — this "
            f"board will carry prices and few or no records, and the card "
            f"says so.")
    return season, P


def index_by_name(P):
    """name -> [pid]. ⛔ AMBIGUOUS NAMES ARE KEPT AS LISTS, NOT COLLAPSED.

    🔴 Players share names, and `resolve()` in the MLB collector refuses to
    guess for exactly this reason. A silent first-match here would attach
    one player's record to another player's price.
    """
    idx = {}
    for pid, p in P.items():
        idx.setdefault(norm(p.get("name")), []).append(pid)
    return idx


def qualifying(games):
    """The games a rate may be computed over.

    🔴 NFL: a majority of snaps. See the docstring -- with no floor a WR3's
    blank games are counted as evidence about a WR1's line and every under
    is overstated by up to 23.9 points.
    ⚠️ Rows with no snap field at all are DROPPED rather than assumed to
    qualify. An absence is evidence about the feed, not about the player.

    🔴 COLLEGE: EVERY GAME IN HIS LOG -- the UNION denominator, added
    2026-09-04. ⛔ CFBD publishes no snap counts, so there is no floor to
    apply and pretending otherwise would be inventing a field. What the
    union buys is the games he appears in for ANY reason -- a carry, a
    catch, an attempt -- rather than only the games he recorded the stat
    the market is about.
    📊 THE SIZE OF THAT, MEASURED IN BOTH LEAGUES: it is worth **+35.7
    points** for a college RB (+29.4 in the NFL) and a rounding error for
    a WR (+1.7 / +0.0). ⚠️ Replicated across two leagues, so it is a
    property of how backs and receivers are used, not a season artifact.
    ⚠️ THE RESIDUAL ERROR IS REAL, KNOWN AND ONE-DIRECTIONAL: a game he
    played and did nothing in is still missing, so an OVER rate reads
    high. T52b measured that against the truth in the NFL -- pooled
    median 0.21 points, p90 3.79, against a 3.0/8.0 bar -- and
    `market_rateable()` gates the one cell that failed.
    """
    if LEAGUE != "nfl":
        return list(games)
    out = []
    for g in games:
        sp = g.get("snap_pct")
        if sp is None:
            continue
        if float(sp) >= SNAP_FLOOR:
            out.append(g)
    return out


def market_rateable(market, line):
    """May THIS market at THIS line carry a rate? (ok, reason-if-not)

    🔴 THE GATE IS ON THE MARKET AND THE LINE, NOT ON THE LEAGUE. The NFL
    has the true denominator (snaps), so nothing is gated there. College
    has the union denominator, whose error was measured in the NFL and is
    acceptable everywhere except the low receptions lines.
    ⛔ A market nobody measured gets no rate on college. It does not
    inherit a pass from a market that resembles it.
    """
    if LEAGUE == "nfl":
        return True, None
    if market not in RATE_MEASURED:
        return False, (
            "This market has not been checked for how much college box "
            "scores understate a player's games played, so it shows the "
            "price and no record.")
    if market == "player_receptions" and (line is None
                                          or float(line) < RATE_MIN_REC_LINE):
        return False, (
            f"Reception lines under {RATE_MIN_REC_LINE:g} are left without a "
            f"record on purpose. College box scores list a player only when "
            f"he did something, so his quiet games go missing — and at a "
            f"short line a missing quiet game is exactly the difference "
            f"between a hit and a miss.")
    return True, None


def jeffreys(hits, n):
    """The same smoothing MLB hitter rows use. Never 0% and never 100%."""
    return (hits + 0.5) / (n + 1.0)


def rate_for(games, market, line, side):
    """(confidence 0-100, hits, n) over his qualifying games, or None."""
    getter = MARKETS.get(market)
    if not getter:
        return None
    # ⛔ THE MEASURED GATE COMES FIRST. A row that is not allowed a rate
    # must not get one by any other route.
    ok, _why = market_rateable(market, line)
    if not ok:
        return None
    read = getter[0]
    q = qualifying(games)
    if len(q) < MIN_GAMES:
        return None
    vals = [read(g) for g in q]
    if market == "player_anytime_td":
        # ⚠️ A one-sided market. "Yes" is scoring at all; there is no line.
        hits = sum(1 for v in vals if v >= 1)
    elif side == "over":
        hits = sum(1 for v in vals if v > line)
    else:
        hits = sum(1 for v in vals if v < line)
    mean = (sum(vals) / len(vals)) if vals else None
    return round(100 * jeffreys(hits, len(vals))), hits, len(vals), mean


def american_break_even(price):
    return (-price) / ((-price) + 100) if price < 0 else 100 / (price + 100)


def fill_board(rows, cap):
    """Take the best rows, ROUND-ROBIN ACROSS MARKETS.

    🔴 WHY THIS EXISTS. `[measured on the live 2026-09-03 college board]`
    the card came out **100% Anytime TD with a +5000 row on top**. Sam:
    *"not every single td prop on the board should be in gizmos picks
    that makes no sense."*
    ⛔ Sorting alone cannot fix that. Whatever the sort key, one market
    whose prices happen to sit where the key looks will crowd out every
    other market. The MIX has to be decided separately from the RANKING --
    the same reason the MLB parlay pool is stratified by price rather than
    taking the N highest-confidence legs.

    ✅ Rows arrive already sorted. This walks the markets in turn, taking
    each one's next-best row, so the board reflects the whole slate.
    ⚠️ ORDER INSIDE A MARKET IS NEVER CHANGED, and if only one market has
    rows the cap cannot be met -- in that case it fills from what exists
    rather than returning a short board.
    """
    if not rows:
        return []
    buckets = {}
    for r in rows:
        buckets.setdefault(r.get("market"), []).append(r)
    # ⚠️ Start with the market holding the single best row, so the board's
    # top pick is still the best available row overall.
    order = sorted(buckets, key=lambda m: rows.index(buckets[m][0]))
    per_market_cap = max(1, int(cap * MARKET_MAX_SHARE))
    out, taken = [], {m: 0 for m in order}
    while len(out) < cap:
        progressed = False
        for m in order:
            if len(out) >= cap:
                break
            if taken[m] >= per_market_cap or taken[m] >= len(buckets[m]):
                continue
            out.append(buckets[m][taken[m]])
            taken[m] += 1
            progressed = True
        if not progressed:
            break
    # ⛔ If the caps left the board short -- a slate with only one or two
    # markets priced -- fill from what is left rather than shipping a
    # half-empty board.
    if len(out) < cap:
        seen = {id(r) for r in out}
        out += [r for r in rows if id(r) not in seen][:cap - len(out)]
    return out


def empty_top_plays_sentence(slate, n_board):
    """The sentence an EMPTY top-plays list shows, and there are TWO.

    🔴 **THE CARD ONCE GAVE THE WRONG ONE ON A LIVE PAGE.**
    `[2026-09-10]` On a Thursday college card with `n_priced: 0` it
    printed *"⛔ Not because the board is empty"* — **on a board that WAS
    empty.** The reader was told the rows existed and had all been
    rejected for carrying no record, when nothing had been priced at all.

    ⛔ **EXTRACTED TO A NAMED FUNCTION 2026-09-11, AND THAT IS THE POINT
    OF THIS CHANGE.** Both branches were only reachable by running the
    whole builder against a real data tree, so the two checks that
    covered them — `test_drop16_fixes.py` §6 and `test_top_plays.py` —
    **BOTH BRANCHED ON THE LIVE CARD.** On a day with rows priced, the
    empty-board sentence was exercised by **nothing at all**, and the
    only thing standing between that and a repeat of the 09-10 defect
    was which day of the week it happened to be.
    ➡️ **A rule the card PRINTS should be a rule a test can DRIVE** — no
    data tree, no sandbox, no calendar. Same reason `h2h_gap_days()` and
    `nfl.check_ahead_out()` were pulled out of their builders.

    ✅ **THE HONEST HALF IS KEPT IN BOTH BRANCHES:** we did not rank by
    price, because ranking by price is ranking by which bet pays worst
    while calling it *"most likely to hit"*.

    ⚠️ `n_board` is a COUNT, not the board. The sentence needs to know
    how many rows are priced and nothing else about them.
    """
    if not n_board:
        return (f"No top plays for {slate}. Nothing is priced for this "
                f"day yet, so there was nothing to rank. ⚠️ When rows do "
                f"arrive, only those carrying a record are ranked — "
                f"ranking by price would be ranking by which bet pays "
                f"worst while calling it 'most likely to hit'.")
    return (f"No top plays for {slate}. ⛔ Not because the board is "
            f"empty — {n_board} row(s) are priced, but none carries a "
            f"record, and ranking those by price would be ranking by "
            f"which bet pays worst while calling it 'most likely to "
            f"hit'.")


def build_top_plays(rows, board, n=TOP_N):
    """Most likely to hit, among rows a person is actually paid on.

    ⛔ CONFIDENCE IS REQUIRED, NOT PREFERRED. On a board whose player-name
    join failed its gate, no row carries a record at all -- and ranking
    THOSE by price would be ranking by which bet pays worst while calling
    it "most likely to hit". ✅ The correct output there is an EMPTY list
    with a stated reason, which is what the caller gets.

    ⚠️ DEDUP IS BY PLAYER NAME, because football has no player ids. Both
    sides of this comparison are ours -- the card and `props.json.gz` come
    from the same snapshot -- so the strings match by construction rather
    than by matching. ⛔ If a third source is ever joined here it needs its
    own gate, exactly as the projections map does.

    🔴 AND ONE PLAY PER GAME. `[Sam's decision, 2026-09-06]` Asked whether
    this should be forced to diversify, he chose ONE PER GAME.
    ⛔ THE MEASUREMENT THAT PUT THE QUESTION TO HIM: a payable, deduped
    top-20 shared **18 of its 20 players** with the board's own first 20
    rows -- it was very nearly a second copy of the head of the board.
    ✅ One per game makes it a genuinely different list. ⚠️ AND IT COSTS
    ROWS, WHICH IS THE HONEST TRADE: today's 20 came from 12 games, so a
    one-per-game list is TWELVE plays, not twenty. The cap becomes a
    ceiling the slate rarely reaches rather than a number always hit.
    ⛔ Nothing is padded to get back to 20. Fewer, more independent rows
    is what was chosen.
    """
    pool, dropped_price, dropped_dupe, dropped_game = [], 0, 0, 0
    for x in rows:
        if x.get("price") is None or x.get("confidence") is None:
            continue
        if x["price"] <= TOP_PRICE_FLOOR:
            dropped_price += 1
            continue
        pool.append(x)
    pool.sort(key=lambda x: -x["confidence"])

    seen, seen_games, out = set(), set(), []
    for x in pool:
        who = x.get("player")
        gid = x.get("game_id")
        if who in seen:
            dropped_dupe += 1
            continue
        # ⛔ COUNTED SEPARATELY FROM THE PLAYER DEDUP. "his team-mate is
        # already listed" and "he is already listed" are different facts,
        # and a report that merges them cannot tell you which rule is
        # shaping the list.
        if gid is not None and gid in seen_games:
            dropped_game += 1
            continue
        seen.add(who)
        if gid is not None:
            seen_games.add(gid)
        out.append(x)
        if len(out) >= n:
            break

    # 🔴 THE OVERLAP IS MEASURED AND PUBLISHED, NOT ASSUMED EITHER WAY.
    # This list is only worth reading as a HIGHLIGHT of the board unless
    # the numbers say otherwise, and the numbers are on the card so a
    # reader -- or a future session -- can check rather than trust.
    head = {r.get("player") for r in board[:n]}
    shared = len({r.get("player") for r in out} & head)
    meta = {
        "below_payable_floor": dropped_price,
        "same_player_already_listed": dropped_dupe,
        "same_game_already_listed": dropped_game,
        "one_per_game": True,
        "price_floor": TOP_PRICE_FLOOR,
        "pool_after_price_gate": len(pool),
        "cap": n,
        "distinct_games": len({r.get("game_id") for r in out}),
        "shared_with_board_head": shared,
        "board_head_size": min(n, len(board)),
    }
    return out, meta


def slate_date(B):
    """The ET date of the earliest game on the board (ledger rule 60).

    ⚠️ Falls back to today in ET -- never UTC -- so the page's `todayET()`
    lookup and this writer can never disagree about which day it is.
    """
    ts = [g.get("commence") for g in B.get("games", []) if g.get("commence")]
    if ts:
        try:
            t = min(datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc) for x in ts)
            return et(t).strftime("%Y-%m-%d")
        except Exception:
            pass
    return et(datetime.now(timezone.utc)).strftime("%Y-%m-%d")


def et_date(commence):
    """The ET calendar date a kickoff belongs to, or None.

    🔴 ET, NEVER UTC, AND THE REASON IS THE WHOLE POINT OF THIS FILTER. A
    Saturday 8pm ET kickoff is 00:00Z SUNDAY. Slicing the UTC string files
    it under the wrong day and would put half a college Saturday on
    Sunday's card -- the same defect ledger rule 60 exists for, arriving
    through a different door.
    """
    if not commence:
        return None
    try:
        t = datetime.strptime(commence, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc)
    except Exception:
        return None
    return et(t).strftime("%Y-%m-%d")


def et(dt):
    """UTC -> US Eastern. ⚠️ zoneinfo, not a hardcoded offset -- a fixed -5
    is wrong for seven months of a football season."""
    try:
        from zoneinfo import ZoneInfo
        return dt.astimezone(ZoneInfo("America/New_York"))
    except Exception:
        return dt


def main():
    try:
        B = json.load(gzip.open(f"{DATA}/latest/props.json.gz", "rt"))
    except Exception as e:
        log(f"no props board for {LEAGUE} yet ({type(e).__name__}) — nothing to card")
        return 0

    season, P = load_logs()
    idx = index_by_name(P)

    rows, unmatched, ambiguous, thin, gated = [], set(), set(), 0, 0
    seen_players = set()

    for g in B.get("games", []):
        for pr in g.get("props", []):
            mk = pr.get("market")
            if mk not in MARKETS:
                continue
            who = pr.get("player") or ""
            seen_players.add(who)
            pids = idx.get(norm(who), [])
            plog = None
            if RATES_OK:
                if len(pids) > 1:
                    ambiguous.add(who)
                elif not pids:
                    unmatched.add(who)
                else:
                    plog = P[pids[0]]

            for side, sd in (pr.get("sides") or {}).items():
                price = sd.get("price")
                if price is None:
                    continue
                r = None
                gate_ok, gate_why = market_rateable(mk, pr.get("line"))
                if plog is not None and gate_ok:
                    r = rate_for(plog.get("g") or [], mk, pr.get("line"), side)
                    if r is None:
                        thin += 1
                elif plog is not None and not gate_ok:
                    # ⛔ COUNTED SEPARATELY. "gated by a measurement" and
                    # "too few games" are different facts and a report that
                    # merges them cannot tell you which one is happening.
                    gated += 1
                conf = r[0] if r else None
                unit = MARKETS[mk][1]
                sideword = {"over": "over", "under": "under", "yes": "yes"}[side]
                row = {
                    "kind": "fb",
                    "league": LEAGUE,
                    # 🔴 rule 55, said on the row itself
                    "basis": ("RECORD + MARKET — his own rate, no model"
                              if conf is not None
                              else "MARKET — price only, no rate available"),
                    "player": who,
                    "market": mk,
                    "market_label": LABEL[mk],
                    "side": sideword,
                    "line": pr.get("line"),
                    "game": f"{g.get('away')} @ {g.get('home')}",
                    "game_id": g.get("id"),
                    "away": g.get("away"), "home": g.get("home"),
                    "commence": g.get("commence"),
                    "book": sd.get("book"), "price": price,
                    "link": sd.get("link"),
                    "n_books": sd.get("n_books"),
                    "clears_price_floor": price >= PRICE_FLOOR,
                    "confidence_basis": "RECORD" if conf is not None else "MARKET",
                }
                if conf is not None:
                    hits, n = r[1], r[2]
                    row["confidence"] = conf
                    # ⚠️ SAME FIELD NAMES THE MLB CARD USES, so the shared
                    # pickCard detail line renders football with no special
                    # case. `raw` is the unsmoothed count, `rate` the
                    # smoothed percentage -- exactly as a hitter row.
                    row["raw"] = f"{hits} of {n}"
                    row["record"] = f"{hits} of {n}"
                    row["rate"] = conf
                    row["break_even"] = round(100 * american_break_even(price), 1)
                    row["edge"] = round(
                        100 * (conf / 100.0 - american_break_even(price)), 1)
                    # ⚠️ THE NOTE MUST DESCRIBE THE DENOMINATOR THAT WAS
                    # ACTUALLY USED. ⛔ Claiming a snap floor on a league
                    # that publishes no snap counts would be stating
                    # something the data cannot support.
                    row["confidence_note"] = (
                        f"His own rate at this exact line over {n} games in "
                        f"{season} where he played at least half his team's "
                        f"snaps, smoothed. There is no football model in this "
                        f"project, so this is DESCRIPTIVE — not a projection."
                        if LEAGUE == "nfl" else
                        f"His own rate at this exact line over the {n} games "
                        f"in {season} he appears in, smoothed. College box "
                        f"scores list a player only when he did something, so "
                        f"a game he played quietly can be missing — which "
                        f"nudges an over slightly high. There is no football "
                        f"model in this project, so this is DESCRIPTIVE — not "
                        f"a projection.")
                    row["own_mean"] = (None if r[3] is None
                                       else round(r[3], 2))
                    # ══════════════════════════════════════════════════
                    # 🔴 THE PROJECTION. Sam, 2026-09-04: *"thats what the
                    # model is supposed to do... you predict what the
                    # outcome is which is the projection."* He is right,
                    # and the reason there was no number here was a
                    # misreading of our own findings.
                    # ⛔ T46 (+0.0010), T47 (-0.0041) and T50 (-0.0036) all
                    # LOST to a player's own season average. **That is a
                    # licence to use the average, not a reason to show
                    # nothing** -- a test saying "nothing beats the simple
                    # thing" is a test saying ship the simple thing.
                    # ✅ AND T56 MEASURED WHETHER IT IS WORTH PRINTING, on
                    # a metric neither candidate minimises by construction:
                    # the mean's sign predicts the side of the line 64.13%
                    # against a 60.88% majority-class baseline -- **+3.25
                    # points, both predicted classes above 50%.** The
                    # number carries signal.
                    # ⛔ IT IS DESCRIPTIVE AND NEVER MODEL. Rule 55 governs
                    # the LABEL, not whether a number appears. This is his
                    # own per-game average over the same games the rate
                    # used -- it is not opponent-adjusted and it is not
                    # role-adjusted, because every attempt at that lost.
                    # ⚠️ AND IT FOLLOWS THE RATE'S GATE. `rate_for` returns
                    # None for a market/line the measurement never cleared,
                    # so a gated cell gets no projection either. A mean is
                    # a different statistic from a rate, but a cell we have
                    # declared unmeasurable does not get a number by the
                    # back door.
                    if r[3] is not None:
                        row["projection"] = round(r[3], 1)
                        row["projection_unit"] = unit
                        row["projection_basis"] = "DESCRIPTIVE"
                        row["projection_note"] = (
                            f"His own average over the {r[2]} games this "
                            f"record is built from — {r[3]:.1f} {unit} a "
                            f"game. That is what he has actually been doing, "
                            f"not a forecast.")
                    row["why"] = build_why(who, mk, pr.get("line"), sideword,
                                           hits, n, season, unit,
                                           mean=r[3])
                else:
                    row["why"] = [gate_why] if (plog is not None
                                                 and not gate_ok) else [
                        no_rate_reason(RATES_OK, plog, who)]
                rows.append(row)

    # 🔴 A NAME GATE THAT FAILS CLOSED, exactly like the Power 4 gate.
    # ⛔ If the join is unproven, ship the board with NO rates rather than a
    # board whose rates belong to the wrong people.
    # ⛔ EVERY PRICED ROW, NOT JUST THE 50 THAT MADE THE BOARD. The Player
    # Props tab renders the whole slate and joins against this map; a map
    # built from the card alone would light up 50 rows and leave the rest
    # blank for no reason a reader could see.
    #
    # 🔴 THE PARLAYS ARE NOT BUILT HERE ANY MORE, AND THAT WAS A REAL BUG.
    # `build_parlays_fb(rows)` used to run at THIS point -- ABOVE the name
    # gate below, which strips every `confidence` when the join is too
    # weak. ⛔ So a board that correctly shipped MARKET-ONLY could still
    # ship parlays whose joint probability was built from the RECORD
    # numbers the same run had just decided it did not trust. That is
    # ledger rule 55 defeated by ordering rather than by argument.
    # ✅ Parlays are now built AFTER the gate, AFTER the price floor, AFTER
    # the price ceiling and AFTER the single-day filter -- from the same
    # rows the board is drawn from, which is the only defensible pool.
    projections = {}
    for _r in rows:
        _v = _r.get("projection")
        if _v is None:
            continue
        projections[f"{_r['player']}|{_r['market']}|{_r['side']}|{_r['line']}"] = {
            "v": _v, "u": _r.get("projection_unit"),
            "b": "DESCRIPTIVE", "n": _r.get("projection_note")}

    match_rate = None
    if RATES_OK and seen_players:
        matched = len(seen_players) - len(unmatched) - len(ambiguous)
        match_rate = matched / len(seen_players)
        log(f"name join: {matched}/{len(seen_players)} = {match_rate:.1%} "
            f"({len(unmatched)} unmatched, {len(ambiguous)} ambiguous)")
        if match_rate < 0.60:
            log(f"🔴 JOIN TOO WEAK ({match_rate:.1%} < 60%) — stripping every "
                f"rate and shipping a MARKET-only board.")
            # 🔴 SAY *WHY* IT IS WEAK, NOT JUST THAT IT IS.
            # `[measured 2026-09-04]` the college join read 58.2% and the
            # matcher was fine: `players-2025.json.gz` still declares
            # "Power 4 only (ACC, Big 12, Big Ten, SEC)" and covers 67
            # teams, while the odds board is ALL FBS. Every unmatched name
            # was a Group of Five player who has no log to match against.
            # ⛔ A gate that fails without naming its cause invites the
            # wrong fix -- and the wrong fix here is lowering the gate.
            covered = {gg.get("team") for pl in P.values()
                       for gg in (pl.get("g") or []) if gg.get("team")}
            log(f"  the log covers {len(covered)} team(s); "
                f"{len(unmatched)} board name(s) matched nothing")
            scope_note = None
            try:
                scope_note = LOG_SCOPE
            except NameError:
                pass
            if scope_note:
                log(f"  the log declares its scope as: {scope_note}")
                if "power 4" in str(scope_note).lower():
                    log("  ⚠️ THE STORED LOG IS POWER-4 AND THE BOARD IS "
                        "ALL FBS. This is a SCOPE gap, not a broken "
                        "matcher. Re-run the college back-fill (free) to "
                        "rebuild the logs at FBS scope; ⛔ do NOT lower "
                        "the gate.")
            for r in rows:
                r.pop("confidence", None)
                r.pop("edge", None)
                r["confidence_basis"] = "MARKET"
                r["basis"] = "MARKET — price only, the name join did not clear its gate"
                r["why"] = ["The player name join did not clear its gate on "
                            "this slate, so no record is shown rather than a "
                            "record that might belong to someone else."]

    # ══════════════════════════════════════════════════════════════════
    # 🔴 THE SINGLE-DAY FILTER, AND IT COMES FIRST. See BOARD_MIN above for
    # the measurement and for why the day is the SLATE's, not the clock's.
    # ⛔ It runs BEFORE the price rules and BEFORE the parlays so that one
    # filter governs every surface. Applying it at the board alone is how
    # the parlays would keep pairing a Saturday leg with a Sunday one.
    # ⚠️ `projections` above is deliberately built from EVERY priced row,
    # day filter or not -- the Player Props tab renders the whole slate and
    # joins against that map, so filtering it would blank tomorrow's rows
    # for no reason a reader could see. The BOARD is one day; the
    # PROJECTIONS are the slate. Different questions, different scopes.
    slate = slate_date(B)
    off_day = [r for r in rows if et_date(r.get("commence")) not in (slate, None)]
    rows = [r for r in rows if et_date(r.get("commence")) in (slate, None)]
    off_dates = sorted({d for d in (et_date(r.get("commence")) for r in off_day) if d})
    if off_day:
        log(f"  single-day board: {len(off_day)} priced row(s) dropped for "
            f"{', '.join(off_dates)} — this card is {slate} only")

    # 🔴 THE -700 FLOOR IS SAM'S STANDING INSTRUCTION AND IT APPLIES HERE
    # TOO. Rows below it are kept and reported, but they are NOT the board.
    # ⛔ Without this the board fills with prices that always win and pay
    # nothing -- the exact failure the MLB top-10 price gate exists to stop.
    below = [r for r in rows if not r["clears_price_floor"]]
    rows = [r for r in rows if r["clears_price_floor"]]

    # ⛔ AND THE CEILING. A price longer than +400 is a longshot, not a
    # pick, whatever else is true about it.
    longshots = [r for r in rows if (r.get("price") or 0) > PRICE_CEIL]
    rows = [r for r in rows if (r.get("price") or 0) <= PRICE_CEIL]
    for r in longshots:
        r["excluded"] = f"longer than +{PRICE_CEIL}"

    # Sort: rated rows by confidence descending (Sam's standing rule), then
    # the unrated ones by price. ⛔ An unrated row must never outrank a
    # rated one just because its price is short.
    rows.sort(key=lambda r: (r.get("confidence") is None,
                             -(r.get("confidence") or 0),
                             -(r.get("price") or -10000)))

    # 🔴 ROUND-ROBIN ONLY WHEN THERE IS NOTHING TO RANK BY.
    # ⚠️ Sam's standing rule is that the board sorts STRICTLY by
    # confidence, descending. Where rows carry a rate that order is
    # meaningful and must not be reshuffled for the sake of variety.
    # ⛔ Where they do NOT -- the college board -- price ordering is
    # meaningless in both directions, and leaving it alone is what put
    # fifty Anytime TDs and a +5000 top row on the card. Diversity is the
    # only honest arrangement of an unranked board.
    # ➡️ If a RATED board ever comes out market-heavy, that is a finding
    # to measure, not a reason to override the ranking here.
    rated = any(r.get("confidence") is not None for r in rows)
    board = rows[:BOARD_MAX] if rated else fill_board(rows, BOARD_MAX)
    for i, r in enumerate(board, 1):
        r["rank"] = i

    # 🔴 PARLAYS FROM THE SAME POOL THE BOARD IS DRAWN FROM -- one day, past
    # the floor, under the ceiling, and past the name gate. ⛔ Built any
    # earlier and they inherit rows the board itself refused; see the note
    # where this call used to sit.
    parlays, parlay_meta = build_parlays_fb(rows)

    # 🔴 SAME POOL AS THE BOARD AND THE PARLAYS -- one day, past the floor,
    # under the ceiling, past the name gate. ⛔ Built any earlier and it
    # inherits rows the board itself refused (ledger rule 102).
    top_plays, top_meta = build_top_plays(rows, board)
    if top_plays:
        log(f"  top plays: {len(top_plays)} of {top_meta['pool_after_price_gate']} "
            f"payable rows, ONE PER GAME across {top_meta['distinct_games']} "
            f"game(s); {top_meta['same_player_already_listed']} skipped as a "
            f"repeat player and {top_meta['same_game_already_listed']} as a "
            f"repeat game; {top_meta['shared_with_board_head']} of "
            f"{top_meta['board_head_size']} players shared with the board's head")
    else:
        log("  top plays: none — no row on this board carries a record, and "
            "ranking by price would rank by which bet pays worst.")

    # ⚠️ A SHORT BOARD IS REPORTED, NEVER PADDED AND NEVER SUPPRESSED. Five
    # is Sam's floor; the only way to hit it on a thin day is to lower a
    # bar, which every other rule here forbids.
    short_of_min = 0 < len(board) < BOARD_MIN
    if short_of_min:
        log(f"  ⚠️ {len(board)} pick(s) on the {slate} board, below the "
            f"minimum of {BOARD_MIN} — shipped as-is and stated on the "
            f"page. ⛔ NOT padded.")
    if not board:
        log(f"  no picks for {slate}: {len(rows)} priced rows survived the "
            f"day filter, {len(below)} below the floor, {len(off_day)} on "
            f"another day. An empty board on a gameless day is CORRECT.")

    # 🔴 LEDGER RULE 60: THE CARD IS DATED BY THE SLATE, NOT THE WALL
    # CLOCK -- the ET date of the earliest game that has not kicked off.
    # ⛔ A UTC date is not a game's date. Written UTC and read ET, a card
    # built at 9pm ET files under TOMORROW and the page never finds it.
    # This is the same defect that put six games' live odds on the wrong
    # MLB cards on 2026-08-26.
    out = {
        "date": slate,
        "league": LEAGUE,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "card_fb.py",
        "kind": "RECORD + MARKET" if RATES_OK else "MARKET",
        "odds_pulled_at": B.get("pulled_at"),
        "logs_season": season,
        "rates_available": RATES_OK,
        # ⚠️ THE SNAP FLOOR IS AN NFL FACT. ⛔ Reporting it on a college
        # card would advertise a filter that cannot exist there.
        "snap_floor": SNAP_FLOOR if LEAGUE == "nfl" else None,
        "denominator": ("games at >= 50% of team snaps"
                        if LEAGUE == "nfl" else
                        "every game he appears in (union denominator)"),
        "min_games": MIN_GAMES,
        "n_gated_by_measurement": gated,
        "rate_gates": (None if LEAGUE == "nfl" else {
            "min_reception_line": RATE_MIN_REC_LINE,
            "measured_markets": sorted(RATE_MEASURED),
            "why": ("A college rate is computed over the games he appears "
                    "in, which can miss a game he played quietly. That error "
                    "was measured in the NFL, where the true figure is "
                    "known: median 0.2 points, 90th percentile 3.8. It is "
                    "largest at short reception lines, so those carry no "
                    "rate, and a market that was never measured carries "
                    "none either.")}),
        # ══════════════════════════════════════════════════════════════
        # 🔴 ONE NUMBER PER (PLAYER, MARKET), REPEATED AT EVERY LINE.
        # Sam, 2026-08-27: *"you should have the same numbers across the
        # entire website if your talking about the same stat or
        # projction."* MLB learned this the hard way -- 51 of 608 combos
        # once carried more than one number and Sean Manaea read 6.3 K on
        # one row and 5.3 K on another.
        # ✅ THE MEAN IS LINE-INDEPENDENT BY CONSTRUCTION: `rate_for`
        # averages over `qualifying(games)`, which does not depend on the
        # line or the side. So one value is computed and written at every
        # key it belongs to.
        # ⚠️ KEYED BY NAME, AND THAT IS SAFE HERE ONLY BECAUSE BOTH SIDES
        # ARE OURS. The card and `props.json.gz` are built by this repo
        # from the SAME snapshot, so the strings are identical by
        # construction rather than by matching -- measured 50 of 50 on the
        # live board. ⛔ Football has no player ids; if a third source is
        # ever joined here it needs its own gate.
        # 🔴 PARLAYS. Sam settled the books question on 2026-09-04; the
        # correlation blocker is handled by MLB's own rule -- no two legs
        # in the same GAME ID -- and football adds one MLB does not need:
        # every leg at the SAME BOOK, because a parlay is one slip.
        # ══════════════════════════════════════════════════════════════
        # 🔴 TOP PLAYS OF THE DAY, AND THE SENTENCE THAT KEEPS IT HONEST.
        # See `build_top_plays` for the measurement: on football this is a
        # HIGHLIGHTS list, not a second opinion, because the two things
        # that make MLB's version an independent list -- alt ladder rungs
        # and a biting price gate -- do not exist here.
        "top_plays": top_plays,
        "top_plays_excluded": top_meta,
        "top_plays_rule": (
            f"The {len(top_plays)} most likely to hit for {slate} — "
            f"ONE PLAY PER GAME and one per player, among rows priced "
            f"better than {TOP_PRICE_FLOOR}. Sam's rule for the MLB list "
            f"is likely AND payable; he added one-per-game on 2026-09-06 "
            f"after the list was measured at 18 of 20 players shared with "
            f"the board's own first rows. "
            f"⚠️ It is now {top_meta['shared_with_board_head']} of "
            f"{top_meta['board_head_size']}, over "
            f"{top_meta['distinct_games']} game(s). "
            + (f"{top_meta['same_game_already_listed']} row(s) were held "
               f"back because their game was already represented"
               if top_meta["same_game_already_listed"] else
               "No row was held back for a repeat game")
            + (f" and {top_meta['same_player_already_listed']} because the "
               f"player was. " if top_meta["same_player_already_listed"]
               else ". ")
            + f"⛔ Nothing is padded back to {TOP_N}: fewer, more "
              f"independent rows is the point."
            # 🔴 THE TWO EMPTY-LIST SENTENCES LIVE IN A NAMED FUNCTION
            #    so a test can drive BOTH without a data tree — see
            #    `empty_top_plays_sentence` for why that matters.
            if top_plays else empty_top_plays_sentence(slate, len(board))),
        "parlays": parlays,
        "parlay_meta": parlay_meta,
        "parlay_rule": (
            "Legs are in DIFFERENT GAMES and at the SAME BOOK. ⛔ Every "
            "number is the player's own record — nothing here is a model "
            "output, and the combined figure is those records multiplied, "
            "which assumes the games are unrelated."),
        "projections": projections,
        "name_match_rate": round(match_rate, 3) if match_rate is not None else None,
        "n_priced": len(rows),
        # ══════════════════════════════════════════════════════════════
        # 🔴 THE SINGLE-DAY CONTRACT, WRITTEN ON THE CARD SO THE PAGE DOES
        # NOT HAVE TO RE-DERIVE IT. ⛔ A second copy of the rule in
        # JavaScript is a second thing to drift (the same reason the page
        # prints `confidence_basis` rather than deciding it).
        "single_day": True,
        "slate_date": slate,
        "board_min": BOARD_MIN,
        "board_max": BOARD_MAX,
        "n_on_slate_day": len(rows),
        "n_off_slate_day": len(off_day),
        "off_slate_dates": off_dates,
        "short_of_min": short_of_min,
        "single_day_rule": (
            f"This board is {slate} only. Priced rows for another day are "
            f"not shown here and neither are parlays that would cross days "
            f"— a card dated one day and half-filled with the next is two "
            f"facts under one label. "
            + (f"{len(off_day)} row(s) were held back for "
               f"{', '.join(off_dates)}. " if off_day else "")
            + f"Minimum {BOARD_MIN}, maximum {BOARD_MAX}; a day with no "
              f"games is an empty board, and that is correct."),
        "empty_reason": (None if board else (
            f"No {LG_NAME} picks for {slate}. "
            + (f"{len(below)} priced row(s) sat below the {PRICE_FLOOR} "
               f"floor and {len(longshots)} above +{PRICE_CEIL}. "
               if (below or longshots) else "")
            + (f"The board's own games are on {', '.join(off_dates)}, "
               f"which is a different day's card. "
               if off_day else
               "Nothing is priced for this day yet. ")
            + "An empty board on a day with no games is the correct "
              "result, not a failure — the card was built and it found "
              "nothing to show.")),
        "short_reason": (None if not short_of_min else (
            f"Only {len(board)} pick(s) cleared for {slate}, below the "
            f"minimum of {BOARD_MIN}. ⛔ The board is NOT padded to reach "
            f"the minimum — the only way to do that is to lower a bar. "
            f"What is here is everything that qualified.")),
        "coverage": (
            f"{len(rows):,} priced football rows for {slate} across "
            f"{B.get('n_games', 0)} board games; {len(board)} shown"
            + (f" — {len(off_day)} row(s) on another day are not on this "
               f"card." if off_day else ".")),
        "board_rule": (
            "Sorted by the player's own record at that exact line, highest "
            "first — the same order the MLB board uses. Rows with no record "
            "sit below every row that has one."
            if RATES_OK else
            "Sorted by price. No row carries a rate — see the note."),
        "no_model_note": (
            "🔴 No row on this board carries a Gizmo's confidence rating and "
            "none ever will on today's evidence. Three pre-registered "
            "football models were tested and every one lost to a player's "
            "own season average. What is shown is his OWN RECORD and the "
            "market's price — both labelled."),
        "college_note": None if LEAGUE == "nfl" else COLLEGE_NOTE,
        "picks": board,
        "n_longshots_excluded": len(longshots),
        "price_ceiling": PRICE_CEIL,
        "market_max_share": MARKET_MAX_SHARE if not rated else None,
        "board_mixed": not rated,
        "below_price_floor": [
            {k: r[k] for k in ("player", "market_label", "side", "line",
                               "price", "book") if k in r} for r in below],
        "price_floor": PRICE_FLOOR,
        "schema_note": ("Renders through the same pickCard component as the "
                        "MLB board. confidence_basis is RECORD or MARKET, "
                        "never MODEL."),
    }
    # 🔴 TWO FILES, AND THE REASON IS THAT FOOTBALL IS WEEKLY.
    #   fb-<lg>-<date>.json  the PERMANENT record of what was published,
    #                        append-only, exactly like MLB's picks/.
    #   fb-<lg>-latest.json  what the PAGE reads.
    # ⛔ The page must NOT look up "today's" card the way MLB does. Most
    # days in a football week have no games at all, so a date lookup finds
    # nothing on a Tuesday and the tab reads as broken. A pointer file
    # answers "the next slate" with no date arithmetic in JavaScript --
    # and date arithmetic split across two languages is how the MLB
    # wrong-game bug happened.
    os.makedirs("picks", exist_ok=True)
    path = f"picks/fb-{LEAGUE}-{out['date']}.json"
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    with open(f"picks/fb-{LEAGUE}-latest.json", "w") as fh:
        json.dump(out, fh, indent=1)
    rated = sum(1 for r in board if r.get("confidence") is not None)
    log(f"card_fb[{LEAGUE}]: {len(rows) + len(below)} priced, "
        f"{len(below)} below the {PRICE_FLOOR} floor, {len(board)} on the "
        f"board, {rated} with a record, {thin} too thin -> {path}")
    return 0


# ~~"College rows carry a price and no rate, on purpose..."~~
# ⛔ STRUCK 2026-09-04 — the comparison behind it was not valid. Rule 75.
COLLEGE_NOTE = (
    "College records are counted over the games a player appears in. "
    "College box scores list him only when he did something, so a game he "
    "played quietly can be missing — which nudges an over slightly high. "
    "That gap was measured against the NFL, where the true figure is "
    "known: a median of 0.2 percentage points and 3.8 at the 90th "
    "percentile. Short reception lines, where the gap is biggest, carry no "
    "record at all.")


def no_rate_reason(rates_ok, plog, who):
    if not rates_ok:
        return COLLEGE_NOTE
    if plog is None:
        return (f"No 2025 game log matched {who} — he is new, changed his "
                f"listed name, or shares one. No record is shown rather than "
                f"a guess.")
    if LEAGUE == "nfl":
        return (f"{who} has too few games at a starter's snap share to read "
                f"a rate from. Fewer than {MIN_GAMES} is not a rate.")
    return (f"{who} appears in too few games last season to read a rate "
            f"from. Fewer than {MIN_GAMES} is not a rate.")


# ══════════════════════════════════════════════════════════════════════
# PARLAYS. Sam unblocked this on 2026-09-04: *"you can combine player
# props ill verify that for you right now. you can. there done."*
#
# 🔴 THE OTHER BLOCKER WAS NEVER POLICY, IT WAS ARITHMETIC: multiplying
# two players' own records asserts they are INDEPENDENT, and two players
# in the same game are not. ✅ MLB already solved it -- **no parlay puts
# two legs in the same GAME ID** (ledger rule 54) -- and that rule is
# reused here verbatim. ⛔ It is checked on game IDENTITY, never on
# opponent name: in one game both sides have different opponents and the
# same game, so a name test passes on exactly the pairs it exists to
# catch. A live MLB card once shipped four impossible parlays that way.
#
# 🔴 AND ONE CONSTRAINT FOOTBALL HAS THAT MLB DOES NOT: **EVERY LEG MUST
# BE AT THE SAME BOOK.** A parlay is one slip at one sportsbook. The
# football board carries the BEST price across five books, so two legs
# can easily be best at two different books -- and a multiplier built
# from those is a number nobody can actually bet. MLB sidesteps this by
# requiring `on_hardrock`, because Hard Rock is the only one of the five
# that combines props. Here it is enforced directly and the rejects are
# COUNTED, so a thin parlay list is explained rather than mysterious.
#
# ⚠️ THE BANDS ARE SAM'S AND THEY ARE THE SAME NUMBERS AS `card.py`'s.
# ⛔ Restating them is a rule 66 hazard, so `test_card_fb.py` asserts the
# two files agree rather than trusting that they do.
PARLAY_BANDS = {2: (1.80, 2.20), 3: (3.00, 6.00), 4: (3.00, 6.00)}
PARLAY_STRATA = [(1.00, 1.30), (1.30, 1.60), (1.60, 2.00),
                 (2.00, 3.00), (3.00, 99.0)]
PARLAY_PER_STRATUM = 12
PARLAY_PER_SIZE = 8


def decimal_odds(american):
    return 1 + (100.0 / -american if american < 0 else american / 100.0)


def build_parlays_fb(rows, per_size=PARLAY_PER_SIZE):
    """Combinations of 2, 3 and 4 legs from RATED football rows.

    ⛔ EVERY NUMBER HERE IS DESCRIPTIVE. A leg's confidence is the
    player's own record, so their product is a product of records --
    never a model output, and the note says so on the card.
    """
    legs = [r for r in rows
            if r.get("confidence") is not None
            and r.get("price") is not None
            and r.get("clears_price_floor")
            and r.get("game_id") and r.get("book")]
    legs.sort(key=lambda r: -r["confidence"])

    # ⛔ STRATIFIED BY PRICE, for MLB's reason: confidence and price move
    # together, so the N most confident legs are all short favourites and
    # no combination of them ever reaches a 3x band.
    pool, strata = [], []
    for lo_d, hi_d in PARLAY_STRATA:
        band = [r for r in legs if lo_d <= decimal_odds(r["price"]) < hi_d]
        pool.extend(band[:PARLAY_PER_STRATUM])
        strata.append({"decimal": f"{lo_d:g}-{hi_d:g}",
                       "available": len(band),
                       "taken": len(band[:PARLAY_PER_STRATUM])})

    def leg_text(r):
        side = {"over": "o", "under": "u", "yes": ""}.get(r["side"], r["side"])
        ln = "" if r.get("line") is None else f"{side}{r['line']}"
        return f"{r['player']} {ln} {MARKETS[r['market']][1]}".replace("  ", " ")

    out, rejects = {}, {"same_game": 0, "same_player": 0, "mixed_book": 0,
                        "out_of_band": 0}
    for size, (lo, hi) in PARLAY_BANDS.items():
        found = []
        for combo in itertools.combinations(pool, size):
            if len({c["game_id"] for c in combo}) != size:
                rejects["same_game"] += 1
                continue
            if len({c["player"] for c in combo}) != size:
                rejects["same_player"] += 1
                continue
            if len({c["book"] for c in combo}) != 1:
                rejects["mixed_book"] += 1
                continue
            mult = 1.0
            for c in combo:
                mult *= decimal_odds(c["price"])
            if not (lo <= mult <= hi):
                rejects["out_of_band"] += 1
                continue
            joint = 1.0
            for c in combo:
                joint *= c["confidence"] / 100.0
            be = 100.0 / mult
            found.append({
                "legs": [leg_text(c) for c in combo],
                "games": [c["game"] for c in combo],
                "game_ids": [c["game_id"] for c in combo],
                "book": combo[0]["book"],
                "prices": [c["price"] for c in combo],
                "multiplier": round(mult, 3),
                "n_legs": size,
                "band": f"{lo:g}x-{hi:g}x",
                "joint": round(100 * joint, 1),
                "joint_basis": "RECORD",
                "joint_note": (
                    "The legs' own records multiplied together. ⛔ Every leg "
                    "is the player's OWN RATE at that exact line — "
                    "DESCRIPTIVE, never a model output, because this project "
                    "has no football model. Legs are in different games, so "
                    "they are treated as independent; that assumption is not "
                    "free and has never been tested here."),
                "leg_confidences": [c["confidence"] for c in combo],
                "break_even": round(be, 1),
                "edge": round(100 * joint - be, 1),
                "ev_30": round(30 * (joint * mult - 1), 2),
            })
        found.sort(key=lambda x: -x["joint"])
        out[str(size)] = found[:per_size]
    return out, {"pool": len(pool), "rated_legs": len(legs),
                 "strata": strata, "rejected": rejects,
                 "note": (f"{len(legs)} rated legs, {len(pool)} in the "
                          f"stratified pool. Rejected: "
                          f"{rejects['same_game']} same game, "
                          f"{rejects['same_player']} same player, "
                          f"{rejects['mixed_book']} would need two books, "
                          f"{rejects['out_of_band']} outside Sam's bands.")}


def build_why(who, mk, line, side, hits, n, season, unit, mean=None):
    """Plain English, with the numbers in it. ⛔ No test IDs, no jargon.

    Sam, 2026-08-26: "lose the technical wording ... all of these things
    that a casual [fan] wont know about has to go."

    🔴 THE ROW NOW STATES THE PLAYER'S OWN PER-GAME AVERAGE BESIDE THE
    LINE, AND THAT IS NOT COSMETIC. `[measured 2026-09-04 on the first
    rated college board]` the number two row was **Alberto Mendoza,
    passing UNDER 204.5, "8 of 8", 94%** -- and his 2025 average was
    **35.8 yards a game.** He was a backup; the book has priced him as a
    starter. **The record is factually correct and tells you nothing
    about this line.**
    ⛔ NOTHING HERE FILTERS A ROW. A cutoff at which a row is SUPPRESSED
    would be picking a number to make a board look better, and this
    project does not do that -- that question is pre-registered as T54 in
    `claude/owed-tests.md` instead of being decided at the keyboard.
    ✅ **ADDING INFORMATION IS ALWAYS SAFE. REMOVING ROWS IS NOT.** The
    reader sees "he averaged 35.8 a game" next to "under 204.5" and can
    judge the gap themselves.
    ⚠️ Mean over the SAME games the rate was computed over, so the two
    numbers can never describe different samples.
    """
    pct = round(100 * hits / n) if n else 0
    # ⚠️ THE SENTENCE MUST DESCRIBE THE DENOMINATOR THAT WAS ACTUALLY
    # USED. ⛔ The snap-share clause is TRUE OF THE NFL ONLY -- CFBD
    # publishes no snap counts, and saying it anyway would put a claim on
    # the page the data cannot support (rule 55's plain-English half).
    when = ("when he played at least half the snaps" if LEAGUE == "nfl"
            else "across the games he appears in")
    if mk == "player_anytime_td":
        head = (f"<b>{who}</b> scored in <b>{hits} of {n} games</b> in "
                f"{season} ({pct}%) {when}.")
    else:
        word = "over" if side == "over" else "under"
        head = (f"<b>{who}</b> went {word} {line} {unit} in "
                f"<b>{hits} of {n} games</b> in {season} ({pct}%) {when}.")
    out = [head]
    # 🔴 THE KNOWN LIMIT, SAID ON THE ROW, IN ENGLISH, EVERY TIME.
    # ⚠️ It is one-directional and the reader is entitled to know which
    # way: college box scores drop a player's quiet games, so an OVER
    # reads slightly high. Measured at a median of 0.2 points and a 90th
    # percentile of 3.8 -- small, but never hidden.
    if LEAGUE != "nfl":
        out.append("College box scores list a player only when he did "
                   "something, so a game he played quietly can be missing "
                   "from that count — which nudges an over slightly high.")
    # 🔴 HIS OWN AVERAGE, BESIDE THE LINE. ⛔ Over the same games the
    # rate used -- two numbers from one sample, never two samples.
    if mean is not None and mk != "player_anytime_td" and line is not None:
        out.append(f"He averaged <b>{mean:.1f} {unit} a game</b> over those "
                   f"{n} games, against a line of {line}.")
        # ⚠️ THIS IS A THRESHOLD AND CALLING IT ANYTHING ELSE WOULD BE
        # DISHONEST -- but it is a threshold for SHOWING A SENTENCE, never
        # for removing a row, and those carry very different risk.
        # ⛔ 2x IS A BRIGHT LINE -- "double, or half" -- chosen because it
        # is the point at which a line stops being a variation on what the
        # player did and becomes a different question. It was NOT found by
        # trying values until the right number of rows lit up.
        # 📊 On the first rated college board it marks 3 of 43 rows.
        # ⚠️ IF IT IS WRONG IT GETS A TEST, NOT AN ADJUSTMENT -- and the
        # real question, whether such a row should be RANKED at all, is
        # pre-registered as T54 rather than decided here.
        if mean > 0 and (line / mean >= 2.0 or mean / max(line, 0.5) >= 2.0):
            out.append("⚠️ That line is a long way from what he actually "
                       "did last season, which usually means his role has "
                       "changed. His record is history; it is not evidence "
                       "about a line he never faced.")
    if n < 10:
        out.append("That is a small sample — too few games to read much "
                   "into on its own.")
    out.append(f"This is his own record from last season, not a forecast. "
               f"Rosters and roles change between seasons, so read it as "
               f"history rather than a prediction.")
    return out


if __name__ == "__main__":
    sys.exit(main())
