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
🔴 THE FINDING THAT SHAPES THIS WHOLE FILE — measured 2026-09-03
════════════════════════════════════════════════════════════════════════
**NFL AND COLLEGE LOGS ANSWER DIFFERENT QUESTIONS, AND ONLY ONE OF THEM
SUPPORTS A HIT RATE.**

A rate needs a DENOMINATOR: the games he played. Measured on 2025:

    NFL WR games with ZERO receptions   25.8%   <- blank games ARE logged
    CFB WR games with ZERO receptions    3.5%   <- blank games are MISSING

⚠️ THE MECHANISM, CONFIRMED NOT ASSUMED: nflverse carries SNAP COUNTS, so
a receiver appears in the log for every game he was **on the field** —
79.1% of his zero-catch games have snaps > 0. CFBD has **no snap data at
all**, and `players-<yr>.json.gz` says so in its own consumer_contract:
*"NO SNAP DATA EXISTS FOR COLLEGE FOOTBALL."* A college player therefore
appears only in games where he **touched the ball**.

⛔ SO A COLLEGE HIT RATE IS COMPUTED OVER HIS PRODUCTIVE GAMES ONLY. The
median CFB receiver is missing **6 of his team's 13 games** and 69.6% are
missing three or more — roughly half the denominator is absent, and the
absent half is systematically the low-production half. **The rate would be
inflated on every OVER by an unknown margin.**

⚠️ AND THE TWO CAUSES CANNOT BE SEPARATED. A missing college game is
either "played and did not touch the ball" or "did not play" — the file's
own contract warns of exactly this. **Assuming the first inflates unders;
assuming the second inflates overs.** There is no third option in this
data.

➡️ **THEREFORE: NFL rows carry a RECORD confidence. COLLEGE ROWS DO NOT.**
College still gets the identical board, the identical columns and the
identical sort — sorted by price — with the confidence column reading
"no rate" and the page saying why in one sentence. ⛔ A number that is
wrong in a known direction is worse than no number, because it gets bet.

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

# 🔴 NFL ONLY. See the module docstring -- the college denominator is
# contaminated and no amount of care here fixes it.
RATES_OK = LEAGUE == "nfl"

SNAP_FLOOR = 0.50        # pre-registered, see docstring. ⛔ do not tune
MIN_GAMES = 6            # a rate on fewer games is not a rate
PRICE_FLOOR = -700       # Sam's standing floor, same as MLB
BOARD_MAX = 50           # same as MLB's board

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


def load_logs():
    """Newest season that actually has games. Returns (season, {pid: player})."""
    best = None
    for f in sorted(glob.glob(f"{DATA}/latest/players-*.json.gz"), reverse=True):
        try:
            d = json.load(gzip.open(f, "rt"))
        except Exception:
            continue
        P = d.get("players") or {}
        if sum(len(p.get("g") or []) for p in P.values()) == 0:
            log(f"  {os.path.basename(f)}: no games yet, skipping")
            continue
        best = (d.get("season"), P, os.path.basename(f))
        break
    if not best:
        log("FATAL: no player log with any games")
        sys.exit(1)
    season, P, fn = best
    log(f"logs: {fn} — {len(P)} players, season {season}")
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
    """
    out = []
    for g in games:
        sp = g.get("snap_pct")
        if sp is None:
            continue
        if float(sp) >= SNAP_FLOOR:
            out.append(g)
    return out


def jeffreys(hits, n):
    """The same smoothing MLB hitter rows use. Never 0% and never 100%."""
    return (hits + 0.5) / (n + 1.0)


def rate_for(games, market, line, side):
    """(confidence 0-100, hits, n) over his qualifying games, or None."""
    getter = MARKETS.get(market)
    if not getter:
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
    return round(100 * jeffreys(hits, len(vals))), hits, len(vals)


def american_break_even(price):
    return (-price) / ((-price) + 100) if price < 0 else 100 / (price + 100)


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

    rows, unmatched, ambiguous, thin = [], set(), set(), 0
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
                if plog is not None:
                    r = rate_for(plog.get("g") or [], mk, pr.get("line"), side)
                    if r is None:
                        thin += 1
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
                    row["confidence_note"] = (
                        f"His own rate at this exact line over {n} games in "
                        f"{season} where he played at least half his team's "
                        f"snaps, smoothed. There is no football model in this "
                        f"project, so this is DESCRIPTIVE — not a projection.")
                    row["why"] = build_why(who, mk, pr.get("line"), sideword,
                                           hits, n, season, unit)
                else:
                    row["why"] = [no_rate_reason(RATES_OK, plog, who)]
                rows.append(row)

    # 🔴 A NAME GATE THAT FAILS CLOSED, exactly like the Power 4 gate.
    # ⛔ If the join is unproven, ship the board with NO rates rather than a
    # board whose rates belong to the wrong people.
    match_rate = None
    if RATES_OK and seen_players:
        matched = len(seen_players) - len(unmatched) - len(ambiguous)
        match_rate = matched / len(seen_players)
        log(f"name join: {matched}/{len(seen_players)} = {match_rate:.1%} "
            f"({len(unmatched)} unmatched, {len(ambiguous)} ambiguous)")
        if match_rate < 0.60:
            log(f"🔴 JOIN TOO WEAK ({match_rate:.1%} < 60%) — stripping every "
                f"rate and shipping a MARKET-only board.")
            for r in rows:
                r.pop("confidence", None)
                r.pop("edge", None)
                r["confidence_basis"] = "MARKET"
                r["basis"] = "MARKET — price only, the name join did not clear its gate"
                r["why"] = ["The player name join did not clear its gate on "
                            "this slate, so no record is shown rather than a "
                            "record that might belong to someone else."]

    # 🔴 THE -700 FLOOR IS SAM'S STANDING INSTRUCTION AND IT APPLIES HERE
    # TOO. Rows below it are kept and reported, but they are NOT the board.
    # ⛔ Without this the board fills with prices that always win and pay
    # nothing -- the exact failure the MLB top-10 price gate exists to stop.
    below = [r for r in rows if not r["clears_price_floor"]]
    rows = [r for r in rows if r["clears_price_floor"]]

    # Sort: rated rows by confidence descending (Sam's standing rule), then
    # the unrated ones by price. ⛔ An unrated row must never outrank a
    # rated one just because its price is short.
    rows.sort(key=lambda r: (r.get("confidence") is None,
                             -(r.get("confidence") or 0),
                             -(r.get("price") or -10000)))
    board = rows[:BOARD_MAX]
    for i, r in enumerate(board, 1):
        r["rank"] = i

    # 🔴 LEDGER RULE 60: THE CARD IS DATED BY THE SLATE, NOT THE WALL
    # CLOCK -- the ET date of the earliest game that has not kicked off.
    # ⛔ A UTC date is not a game's date. Written UTC and read ET, a card
    # built at 9pm ET files under TOMORROW and the page never finds it.
    # This is the same defect that put six games' live odds on the wrong
    # MLB cards on 2026-08-26.
    out = {
        "date": slate_date(B),
        "league": LEAGUE,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "card_fb.py",
        "kind": "RECORD + MARKET" if RATES_OK else "MARKET",
        "odds_pulled_at": B.get("pulled_at"),
        "logs_season": season,
        "rates_available": RATES_OK,
        "snap_floor": SNAP_FLOOR if RATES_OK else None,
        "min_games": MIN_GAMES,
        "name_match_rate": round(match_rate, 3) if match_rate is not None else None,
        "n_priced": len(rows),
        "coverage": (
            f"{len(rows):,} priced football rows across {B.get('n_games', 0)} "
            f"games; {len(board)} shown."),
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
        "college_note": None if RATES_OK else COLLEGE_NOTE,
        "picks": board,
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


COLLEGE_NOTE = (
    "College rows carry a price and no rate, on purpose. A hit rate needs "
    "the games a player actually played, and college box-score data lists "
    "him only in games where he touched the ball — the median receiver is "
    "missing six of his team's thirteen games, and the missing ones are the "
    "quiet ones. A rate built on that would read too high on every over. "
    "The NFL board has snap counts, so it does not have this problem.")


def no_rate_reason(rates_ok, plog, who):
    if not rates_ok:
        return COLLEGE_NOTE
    if plog is None:
        return (f"No 2025 game log matched {who} — he is new, changed his "
                f"listed name, or shares one. No record is shown rather than "
                f"a guess.")
    return (f"{who} has too few games at a starter's snap share to read a "
            f"rate from. Fewer than {MIN_GAMES} is not a rate.")


def build_why(who, mk, line, side, hits, n, season, unit):
    """Plain English, with the numbers in it. ⛔ No test IDs, no jargon.

    Sam, 2026-08-26: "lose the technical wording ... all of these things
    that a casual [fan] wont know about has to go."
    """
    pct = round(100 * hits / n) if n else 0
    if mk == "player_anytime_td":
        head = (f"<b>{who}</b> scored in <b>{hits} of {n} games</b> in "
                f"{season} ({pct}%) when he played at least half the snaps.")
    else:
        word = "over" if side == "over" else "under"
        head = (f"<b>{who}</b> went {word} {line} {unit} in "
                f"<b>{hits} of {n} games</b> in {season} ({pct}%) when he "
                f"played at least half the snaps.")
    out = [head]
    if n < 10:
        out.append("That is a small sample — too few games to read much "
                   "into on its own.")
    out.append(f"This is his own record from last season, not a forecast. "
               f"Rosters and roles change between seasons, so read it as "
               f"history rather than a prediction.")
    return out


if __name__ == "__main__":
    sys.exit(main())
