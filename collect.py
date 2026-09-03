#!/usr/bin/env python3
"""
Gizmo's Picks — odds & schedule collector.

Runs on GitHub Actions. Pulls from The Odds API and MLB statsapi,
writes timestamped snapshots into data/, and commits them.

Historical odds cannot be bought back cheaply. Every pull we miss is a
day of line-movement and closing-line data that is gone permanently.
So this script is deliberately boring: it fails soft, never crashes the
workflow, and always records what it actually spent.

All snapshots are gzipped. Measured 2026-08-22: an uncompressed gamelines
pull is ~85KB and a schedule pull ~61KB, which at 28 pulls a day is ~1.5GB
a year -- past what a git repo should carry. Gzipped it is ~180MB a year.

Usage:  python collect.py card
        python collect.py pitchers
        python collect.py props-board
        python collect.py news
        python collect.py hitters
        python collect.py gamelines
        python collect.py props-pitcher
        python collect.py props-batter
        python collect.py schedule
        python collect.py results
"""

import collections
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

ODDS_KEY = os.environ.get("ODDS_API_KEY", "").strip()
API = "https://api.the-odds-api.com/v4"
STATS = "https://statsapi.mlb.com/api/v1"

# ---------------------------------------------------------------- LEAGUES
# 🔴 MLB'S PATHS DO NOT MOVE. `data/` and `picks/` stay exactly where they
# are, because every published card, every stored snapshot and every
# verifier already points at them -- and `picks/<date>.json` is an
# append-only permanent record that must never be relocated.
# ⛔ NEW LEAGUES NEST UNDERNEATH. A future league is a new row here and
# nothing else; if you find yourself editing a path string somewhere else
# in this file, the refactor has leaked and should be fixed here instead.
LEAGUES = {
    "mlb":   {"sport": "baseball_mlb",            "data": "data",       "picks": "picks"},
    "nfl":   {"sport": "americanfootball_nfl",    "data": "data/nfl",   "picks": "picks/nfl"},
    "ncaaf": {"sport": "americanfootball_ncaaf",  "data": "data/ncaaf", "picks": "picks/ncaaf"},
}
# 🔴 A MODE THAT IS INHERENTLY ONE LEAGUE'S PINS THAT LEAGUE ITSELF.
# ⛔ It must NOT depend on the operator remembering the dropdown. Run #191
# built a perfectly good 2025 NFL back-fill and wrote it to
# `data/latest/players-2025.json.gz` -- MLB's directory -- because the
# league input defaulted to `mlb`. The run went GREEN. Nothing detected it.
# ✅ Forcing is chosen over failing loud on purpose: a fail-loud check is
# still a thing a tired operator has to read at 4am, whereas a forced path
# CANNOT be wrong.
MODE_LEAGUE = {"nfl-probe": "nfl", "nfl-logs": "nfl",
               "cfb-probe": "ncaaf"}
LEAGUE = os.environ.get("LEAGUE", "mlb").strip().lower() or "mlb"
_forced = {MODE_LEAGUE[m] for m in MODE_LEAGUE
           if m in " ".join(sys.argv[1:]).split()}
if len(_forced) > 1:
    print(f"FATAL: modes from more than one league in one run: {_forced}")
    sys.exit(1)
if _forced:
    _want = _forced.pop()
    if _want != LEAGUE:
        print(f"NOTE: league forced to '{_want}' by the mode "
              f"(input said '{LEAGUE}'). League-specific modes own their paths.")
    LEAGUE = _want
if LEAGUE not in LEAGUES:
    print(f"FATAL: unknown LEAGUE '{LEAGUE}'. Known: {sorted(LEAGUES)}")
    sys.exit(1)
_L = LEAGUES[LEAGUE]
SPORT = _L["sport"]
DATA = _L["data"]
PICKS = _L["picks"]
LATEST = f"{DATA}/latest"

# --- budget guard -----------------------------------------------------
# Stop spending when the month's allowance runs low, so a runaway loop or
# a doubleheader-heavy week can never zero us out mid-month.
RESERVE = 750

# 🔴 FOOTBALL PROPS ONLY PRICE THE SLATE ABOUT TO BE PLAYED. See the gate
# in `collect_props`. ⛔ Every football props cron fires within two days of
# its slate, so this keeps that slate and nothing else. Widening it costs
# `markets x regions` PER EXTRA GAME -- 12 credits a game for the NFL.
# ⚠️ 36h, not 48h. 36 is the smallest window that still catches MONDAY
# NIGHT FOOTBALL from the Sunday 11:25am pull (kickoff is ~32h later);
# 24h and 30h both miss it. Dropping 48 -> 36 also removes the overlap
# where Thursday's pull bought Saturday's games only for Saturday's pull
# to buy them again. Measured on the real 2026 schedules.
FB_PROPS_WINDOW_H = 36

# --- market definitions -----------------------------------------------
GAME_MARKETS = ["h2h", "spreads", "totals"]
PITCHER_MARKETS = ["pitcher_strikeouts", "pitcher_outs", "pitcher_strikeouts_alternate"]
# Alternate rungs, kept as a ladder the card can walk. Hard Rock posts NO
# alternate OUTS market at all -- Sam-confirmed at the book, not a feed
# artifact -- so pitcher_outs_alternate is not requested and its absence
# here is a finding, never a gap to fill from somewhere else.
ALT_MARKETS = {"pitcher_strikeouts_alternate": "strikeouts"}
BATTER_MARKETS = [
    "batter_hits",
    "batter_total_bases",
    "batter_home_runs",
    "batter_rbis",
    "batter_hits_runs_rbis",
]

# ---------------------------------------------------------------- PROPS
# 🔴 MLB SPLITS ITS PROPS IN TWO because pitchers and batters are different
# populations on different schedules. FOOTBALL HAS NO SUCH SPLIT -- every
# prop is a player prop -- so football uses ONE `player` kind. ⛔ Do not
# invent a fake pitcher/batter split for a sport that lacks one just to
# reuse the mode names.
# ✅ Market keys CONFIRMED against the Odds API's published list 2026-08-27.
# ⚠️ COST IS `markets x REGIONS x GAMES`. Run `python budget.py` after any
# edit here -- never estimate.
PROP_MARKETS = {
    "nfl": ["player_pass_yds", "player_pass_tds", "player_rush_yds",
            "player_reception_yds", "player_receptions", "player_anytime_td"],
    # ⚠️ CFB is a THINNER board -- deep markets on marquee games, little
    # else. Five markets: pass TDs are sparse outside the top games and
    # would mostly buy empty responses.
    "ncaaf": ["player_pass_yds", "player_rush_yds", "player_reception_yds",
              "player_receptions", "player_anytime_td"],
}

# Two regions gives us best-odds shopping across ~15 books.
# One region (us2) is Hard Rock only and costs half.
REGIONS_FULL = "us,us2"
REGIONS_CHEAP = "us2"

# 🔴 THE FIVE BOOKS, AND ONLY THESE FIVE.
# Sam, 2026-08-23: "lets just only use the top 5 sportsbooks in the USA,
# hardrock, draftkings, fanduel, ceasars, and bet MGM".
# ⚠️ THIS SUPERSEDES the 2026-08-22 "Hard Rock only / regions=us2"
# instruction for PROPS. Four of the five live in `us`, so props go back
# to a two-region pull -- which DOUBLES the per-game cost, and the pull
# schedule below was cut from three a day to two to pay for it.
# ⚠️ Caesars trades as `williamhill_us` in this feed. `hardrockbet_oh` is
# Hard Rock's Ohio skin and is the same book.
BOOKS = {
    "hardrockbet": "Hard Rock", "hardrockbet_oh": "Hard Rock",
    "draftkings": "DraftKings", "fanduel": "FanDuel",
    "williamhill_us": "Caesars", "betmgm": "BetMGM",
}


def now():
    return datetime.now(timezone.utc)


import freshness as _fresh


def stamp():
    return now().strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg):
    print(f"[{stamp()}] {msg}", flush=True)


def get(url, timeout=30):
    """GET returning (parsed_json, headers). Raises on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": "gizmos-picks/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode()), dict(r.headers)


# Bet-slip deep links. Documented as `includeLinks` on /odds and
# /events/odds, returning a `link` on bookmakers, markets and outcomes.
# ⚠️ Whether THIS plan tier serves them is undocumented and unconfirmed, so
# the pulls ask and then REPORT what came back. The page shows a bet button
# only where a link actually exists -- never a guessed URL.
INCLUDE_LINKS = True


def odds_get(path, params):
    params = dict(params)
    params["apiKey"] = ODDS_KEY
    if INCLUDE_LINKS and path.endswith("/odds"):
        params["includeLinks"] = "true"
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    body, hdr = get(f"{API}{path}?{qs}")
    used = int(hdr.get("x-requests-last", 0) or 0)
    left = int(hdr.get("x-requests-remaining", 0) or 0)
    return body, used, left


def write(path, obj, compress=False):
    """Write JSON so a reader NEVER sees a half-written file — and STAMP IT.

    🔴 EVERY ARTIFACT IS STAMPED HERE, NOT AT THE CALL SITE. `freshness.py`
    can only age an artifact that carries its own timestamp, and three of
    them (`scores`, `lineups`, `weather`) carried none — so the contract
    could not tell a fresh one from a four-day-old one. Stamping at the
    single choke point means a NEW artifact added later cannot be born
    un-ageable, which is the whole failure this rewrite exists to end.
    ⚠️ An explicit `pulled_at` / `built_at` / `generated_at` still wins:
    `written_at` is last in `freshness.STAMP_FIELDS`.

    🔴 WHY THIS IS ATOMIC. `open(path, "w")` TRUNCATES TO ZERO the instant
    it is called, and everything between that and the final flush is a
    window in which any other process reading the path gets an empty file.
    On 2026-08-26 a run died with `JSONDecodeError: Expecting value: line 1
    column 1 (char 0)` on data/latest/record.json -- exactly that window.

    ⚠️ AND IT IS NOT RARE, BECAUSE THE JOBS OVERLAP BY DESIGN. The
    workflow's concurrency group is per-MODE, so a push-triggered
    `refresh` (group `collect-push`) and a scheduled `record` (group
    `collect-2 6 * * *`) are in DIFFERENT groups and run at the same time.
    Both call collect_record() and both write this one path. GitHub also
    delays scheduled runs by hours -- measured 2026-08-26, an 08:05Z job
    landed at 10:06Z -- so "they are hours apart in the cron" guarantees
    nothing about when they actually execute.

    os.replace() is atomic on POSIX: a reader sees the OLD file or the NEW
    one, never a torn one. ⛔ Do not "simplify" this back to a direct open.
    """
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    # 🔴 `written_at` IS ALWAYS REFRESHED. IT MEANS "WHEN THIS FILE WAS
    # WRITTEN", SO IT CHANGES ON EVERY WRITE, BY DEFINITION.
    # ⛔ THE BUG THIS FIXES, AND IT IS THE MTIME BUG'S COUSIN. The first
    # version only stamped when NO stamp field was present. `scores`,
    # `lineups` and `weather` are RESUMABLE CACHES -- they load the old
    # document and write it back -- so the old `written_at` came along for
    # the ride and the condition was never true again.
    # `[measured 2026-08-29]` `scores.json.gz` was rewritten every 15
    # minutes for 22 hours while reporting a `written_at` of
    # **2026-08-28T18:07:43Z**. The freshness gate called it 1,333 minutes
    # stale and the page showed a red bar, on a file that was being
    # rebuilt constantly.
    # ➡️ SAME CLASS AS THE MTIME BUG: the freshness signal did not track
    # the actual write. ⚠️ An explicit `pulled_at` / `built_at` /
    # `generated_at` still WINS AT READ TIME -- they mean "when the DATA
    # is from", which is a different question and must not be overwritten.
    if isinstance(obj, dict):
        obj = dict(obj, written_at=stamp())

    try:
        if compress:
            with gzip.open(tmp, "wt", encoding="utf-8") as f:
                json.dump(obj, f, separators=(",", ":"))
        else:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(obj, f, separators=(",", ":"))
                f.flush()
                os.fsync(f.fileno())
        os.replace(tmp, path)              # atomic
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    log(f"wrote {path} ({os.path.getsize(path)} bytes)")


def daydir(kind):
    d = now().strftime("%Y-%m-%d")
    return f"{DATA}/{d}/{kind}"


def filename():
    return now().strftime("%H%M") + ".json"


# ----------------------------------------------------------------------
# Game lines — the cheap, high-value pull.
#
# 3 markets x 2 regions = 6 credits for the ENTIRE slate, regardless of
# how many games there are. This single call feeds three separate things:
#   * line movement
#   * best-odds shopping across books
#   * the implied team totals that owed-test T25 needs
#
# Stored as a compact normalised extract rather than raw JSON. At 28 pulls
# a day the raw payloads would run to gigabytes a year; the extract keeps
# every number we can actually use and drops the packaging.
# ----------------------------------------------------------------------
def collect_gamelines():
    body, used, left = odds_get(
        f"/sports/{SPORT}/odds",
        {"regions": REGIONS_FULL, "markets": ",".join(GAME_MARKETS),
         "oddsFormat": "american"},
    )

    games = []
    for g in body:
        books = {}
        for bk in g.get("bookmakers", []):
            entry = {}
            for m in bk.get("markets", []):
                key, outs = m.get("key"), m.get("outcomes", [])
                if key == "h2h":
                    entry["h2h"] = {
                        o["name"]: o["price"] for o in outs
                    }
                elif key == "spreads":
                    entry["spreads"] = {
                        o["name"]: {"pt": o.get("point"), "px": o["price"]} for o in outs
                    }
                elif key == "totals":
                    entry["totals"] = {
                        o["name"]: {"pt": o.get("point"), "px": o["price"]} for o in outs
                    }
            if entry:
                if bk.get("link"):
                    entry["link"] = bk["link"]
                books[bk["key"]] = entry
        games.append({
            "id": g.get("id"),
            "commence": g.get("commence_time"),
            "away": g.get("away_team"),
            "home": g.get("home_team"),
            "books": books,
        })

    write(f"{daydir('gamelines')}/{filename()}.gz", {
        "pulled_at": stamp(),
        "endpoint": "bulk",
        "regions": REGIONS_FULL,
        "markets": GAME_MARKETS,
        "credits_used": used,
        "credits_remaining": left,
        "n_games": len(games),
        "games": games,
    }, compress=True)
    # One known URL for the dashboard, overwritten every run.
    write(f"{LATEST}/board.json", {
        "pulled_at": stamp(),
        "kind": "MARKET",
        "note": "De-vigged sportsbook consensus. NOT a Gizmo's projection (ledger rule 55).",
        "n_books_seen": len({b for g in games for b in g["books"]}),
        "games": build_board(games),
    })

    linked = sum(1 for g in body for b in g.get("bookmakers", []) if b.get("link"))
    log(f"gamelines: {len(games)} games, spent {used}, {left} left")
    log(f"  bet links: {linked} bookmaker blocks carried one"
        + ("" if linked else "   <- this plan tier does NOT appear to serve deep links"))
    return left


# ----------------------------------------------------------------------
# The dashboard board file.
#
# GitHub Pages has no directory listing, so the page cannot discover which
# snapshot is newest. The collector therefore writes ONE known URL —
# data/latest/board.json — overwritten every run.
#
# It is also pre-computed. De-vigging in the page would mean shipping the
# same arithmetic to every viewer and risking a version of it that drifts
# from what the ledger uses. Doing it here means one implementation.
#
# Everything in this file is 🔵 MARKET data (ledger rule 55): the book's
# opinion, de-vigged. Nothing here is a Gizmo's projection and the page
# must never label it as one.
# ----------------------------------------------------------------------
def implied(american):
    """American odds -> raw implied probability (still contains the vig)."""
    if american is None:
        return None
    return (-american) / ((-american) + 100) if american < 0 else 100 / (american + 100)


def build_board(games):
    """Compact, de-vigged, dashboard-ready view of one gamelines pull."""
    board = []
    for g in games:
        away, home = g["away"], g["home"]
        # Same five-book rule as the props board. The raw snapshot keeps
        # every book -- that is the historical record and it is not
        # touched -- but the DASHBOARD only shows books Sam can bet at.
        g = dict(g, books={k: v for k, v in g["books"].items() if k in BOOKS})

        # Best price for each side across every book, and the book offering it.
        best = {}
        for side in (away, home):
            top_book, top_px = None, None
            for bk, mk in g["books"].items():
                px = (mk.get("h2h") or {}).get(side)
                if px is None:
                    continue
                # Higher American odds always pays more: +150 > +120 > -110 > -200
                if top_px is None or px > top_px:
                    top_book, top_px = bk, px
            if top_px is not None:
                best[side] = {"book": top_book, "price": top_px}
                lk = (g["books"].get(top_book) or {}).get("link")
                if lk:
                    best[side]["link"] = lk

        # Consensus de-vigged win probability, averaged across books that
        # posted BOTH sides. A one-sided quote cannot be de-vigged.
        probs, vigs = {away: [], home: []}, []
        for bk, mk in g["books"].items():
            h2h = mk.get("h2h") or {}
            ra, rh = implied(h2h.get(away)), implied(h2h.get(home))
            if ra is None or rh is None:
                continue
            s = ra + rh
            if s <= 0:
                continue
            probs[away].append(ra / s)
            probs[home].append(rh / s)
            vigs.append(s - 1)

        avg = lambda xs: round(100 * sum(xs) / len(xs), 1) if xs else None

        # Hard Rock is the reference book for the posted line (ledger rule 48).
        ref = g["books"].get("hardrockbet") or next(iter(g["books"].values()), {})
        total = ((ref.get("totals") or {}).get("Over") or {}).get("pt")

        # 🔴 THE RUN LINE IS THE HOME TEAM'S POINT, BY MAJORITY, AND THEN
        # CROSS-CHECKED AGAINST THE MONEYLINE.
        #
        # ~~rl = ref.spreads[home].pt~~ -- ONE book's label, and it shipped
        # the implied runs to the WRONG TEAM. Measured 2026-08-26 on the
        # live board: 3 of 19 games had the moneyline FAVOURITE credited
        # with FEWER implied runs than the underdog. On TB @ DET the books
        # split 11-6 on which side they show laying the 1.5, Hard Rock was
        # in the group that labels the AWAY team as laying it, and the card
        # published "Implied runs TB 4.5, DET 3.0" -- with Detroit the
        # -115 favourite.
        #
        # ⛔ This is not cosmetic. `team_total` is the predictor owed-test
        # T25 was pre-registered on, so an inverted row is a corrupted
        # observation in a test that has not been run yet.
        #
        # The moneyline is the authority: it is a single unambiguous market
        # and all 17 books agreed on it in the case above. The favourite is
        # the side LAYING runs. Where the majority spread label contradicts
        # that, the moneyline wins and the row is FLAGGED rather than
        # silently corrected.
        _pts = [(bk.get("spreads") or {}).get(home, {}).get("pt")
                for bk in g["books"].values()]
        _pts = [x for x in _pts if x is not None]
        rl, rl_basis, rl_conflict = None, None, False
        if _pts:
            rl, _agree = collections.Counter(_pts).most_common(1)[0]
            rl_basis = f"home team's point, majority of {len(_pts)} books ({_agree} agree)"
            _pa, _ph = avg(probs[away]), avg(probs[home])
            if _pa is not None and _ph is not None and abs(_ph - _pa) >= 2.0:
                _home_fav = _ph > _pa
                if (rl < 0) != _home_fav:
                    rl_conflict = True
                    rl = -abs(rl) if _home_fav else abs(rl)
                    rl_basis += (" -- INVERTED relative to the moneyline and "
                                 "re-oriented to it; the favourite lays the runs")

        # 🔴 The spread and total were being stored as bare NUMBERS while the
        # prices and bet links sat in the same pull, unused. A line you cannot
        # click is a line you cannot bet. Same shopping rule as the moneyline:
        # best price wins, and the link comes from the book offering it.
        # 🔴 SHOP ONLY AT THE EXACT SIGNED NUMBER, PER OUTCOME.
        # Measured 2026-08-23 on ATL@MIL: eleven books posted ATL -1.5 /
        # MIL +1.5, while mybookieag and williamhill_us posted the SAME game
        # inverted -- ATL +1.5 / MIL -1.5. Matching on |point| paired
        # "Milwaukee -1.5 at +130" against a market whose real price is
        # "Milwaukee +1.5 at -182". Those are OPPOSITE BETS, and the page
        # would have advertised a 300-point bargain that does not exist.
        # betrivers posts a 1.0 line in the same pull, which is a different
        # bet again. ⛔ Same failure family as the phantom alt rungs: never
        # compare a price without first confirming it is the same wager.
        def ref_points(market):
            return {name: v.get("pt") for name, v in (ref.get(market) or {}).items()}

        def shop(market):
            """Best price per outcome, only among books quoting the SAME
            signed number the reference book posts for that outcome."""
            want = ref_points(market)
            out, rejected = {}, 0
            for bk, mk in g["books"].items():
                for name, v in (mk.get(market) or {}).items():
                    if v.get("px") is None:
                        continue
                    tgt = want.get(name)
                    if tgt is None or v.get("pt") is None or abs(v["pt"] - tgt) > 1e-9:
                        rejected += 1
                        continue
                    cur = out.get(name)
                    if cur is None or v["px"] > cur["price"]:
                        out[name] = {"price": v["px"], "book": bk, "pt": v["pt"]}
                        lk = (g["books"].get(bk) or {}).get("link")
                        if lk:
                            out[name]["link"] = lk
            return out, rejected

        best_total, rej_t = shop("totals")
        best_spread, rej_s = shop("spreads")

        # Implied team totals: split the total by the run line. This is the
        # input owed-test T25 needs -- the market's read on each starter,
        # bullpen, park and lineup compressed into one number.
        tt_home = tt_away = None
        if total is not None and rl is not None:
            tt_home, tt_away = round(total / 2 - rl / 2, 2), round(total / 2 + rl / 2, 2)

        board.append({
            "id": g["id"], "commence": g["commence"], "away": away, "home": home,
            "win_pct": {away: avg(probs[away]), home: avg(probs[home])},
            "vig_pct": round(100 * sum(vigs) / len(vigs), 2) if vigs else None,
            "n_books": len(vigs),
            "best_ml": best,
            "total": total, "run_line": rl,
            # `run_line` is the HOME team's point. Stated, because a bare
            # signed float with no team attached is what caused the bug.
            "run_line_team": home,
            "run_line_basis": rl_basis,
            "run_line_conflicted_with_moneyline": rl_conflict,
            "best_total": best_total,     # {"Over": {...}, "Under": {...}}
            "best_spread": best_spread,   # {"<team>": {...}, "<team>": {...}}
            "team_total": {away: tt_away, home: tt_home},
        })
    return board


# ----------------------------------------------------------------------
# Player props — the per-event endpoint, billed markets x regions PER GAME.
# This is where the money goes, so it runs on a schedule, not a loop.
#
# Raw payloads are kept gzipped. These pulls happen 2-3 times a day, not
# 28, and we cannot yet model most of these markets — so we store
# everything and decide what mattered later.
# ----------------------------------------------------------------------
# 🔴 THE FRESHNESS GUARD, AND WHY A BACKUP CRON IS FREE.
# GitHub drops scheduled runs under load -- measured 2026-08-26 across the
# archive, only 29 of 70 scheduled gamelines hour-slots produced a file.
# Gamelines survives that: losing some of 21 hourly pulls costs resolution,
# not the board. PROPS DO NOT: there are three pulls a day, so one dropped
# run is a third of the day's freshness.
#
# So every props pull is scheduled TWICE, fifteen minutes apart, and this
# guard makes the second one free. If a pull for the same STORAGE DIR
# already landed inside the window, the backup exits without spending a
# credit. It only costs anything on the days the primary was dropped --
# which is the only day you wanted it.
#
# ⛔ The guard keys on the storage directory, NOT on the region. A cheap
# `us2` backup must see a full `us,us2` primary and stand down; otherwise
# the backup would re-buy a board we already have.
# ======================================================================
# THE DAILY CREDIT CAP — the guard converge cannot run without
# ======================================================================
# 🔴 CONVERGE CHANGED THE COST MODEL AND THE FIRST DRAFT DID NOT PRICE IT.
# The old schedule spent a FIXED amount: three props pulls a day at named
# times, ~606 credits/day, ~18,800/month against a 20,000 plan. Converge
# spends whatever the CONTRACT implies, and a contract is not a budget:
# at a 240-minute props contract on a 15-game slate it would have spent
# **1,512/day = ~46,000/month.** ⛔ That is 2.3x the plan, and it would
# have drained the month in under two weeks.
#
# ✅ So freshness is now bounded by MONEY as well as by time, and the two
# are allowed to disagree. On a small slate the cap never binds and props
# stay as fresh as the contract says. On a big slate the cap throttles the
# pulls and the artifacts go out of contract -- which the freshness banner
# then says out loud on the page.
#
# 🔴 THAT DEGRADATION IS THE POINT. The alternative is a silent overrun
# that ends with a dead API key mid-month and a board with no prices at
# all. ⛔ Visibly late beats invisibly broken.
#
# ⚠️ MEASURED, not assumed (from the repo's own stored `credits_used`):
#   gamelines  6 credits per CALL, flat -- the bulk endpoint does not
#              bill per game
#   pitcher    3 markets x regions x games
#   batter     5 markets x regions x games
#   regions    us2 = 1, "us,us2" = 2
MONTHLY_PLAN = int(os.environ.get("ODDS_MONTHLY_PLAN", "20000"))
# 31 days, with ~7% held back for hand-dispatched pulls and month-end
# slates. ⛔ Do not raise this to make a stale artifact go green.
DAILY_CAP = int(os.environ.get("ODDS_DAILY_CAP", str(int(MONTHLY_PLAN / 31 * 0.93))))


def daily_spend():
    """Credits spent TODAY, summed from the snapshots' own credits_used.

    🔴 DERIVED, NEVER WRITTEN DOWN -- the project's own rule. The stored
    files record what the API actually billed, so this is a measurement
    and not a model that can drift away from the invoice.
    """
    total = 0
    root = f"{DATA}/{now().strftime('%Y-%m-%d')}"
    if not os.path.isdir(root):
        return 0
    for kind in os.listdir(root):
        d = os.path.join(root, kind)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            p = os.path.join(d, f)
            try:
                op = gzip.open if p.endswith(".gz") else open
                with op(p, "rt") as fh:
                    total += int(json.load(fh).get("credits_used") or 0)
            except Exception:
                continue
    return total


def props_regions(kind):
    """Hard Rock only, EXCEPT one full cross-book pull a day.

    🔴 `kind` IS NOT OPTIONAL, AND THAT IS THE WHOLE FIX. This function
    took no argument and scanned BOTH prop directories. Converge builds
    pitcher first; it writes a snapshot stamped `us,us2`; the batter side
    asked ONE SECOND LATER, saw the PITCHER's full pull, and downgraded
    itself to Hard Rock alone.
    ⛔ NOT A FLAKY MISS -- THE BATTER SIDE COULD NEVER TAKE THE FIVE-BOOK
    PULL ON ANY DAY, BY CONSTRUCTION.
    `[measured 2026-08-31 from the stored snapshots]`
        11:07:56Z  props-pitcher  us,us2  72 credits  = 3 x 2 x 12
        11:07:57Z  props-batter   us2     60 credits  = 5 x 1 x 12
    A full 12-game batter pull is 120. **60 is exactly half.**
    ➡️ FIVE CONSECUTIVE CARDS -- 8/27 through 8/31 -- priced every hitter
    row off ONE BOOK while `claude/update-schedule.md` said the card is
    priced from the five-book pull.
    ⚠️ IT WAS WRITTEN UP AS FIXED ON 8/29 AND WAS NEVER ON MAIN. The
    acceptance test for a fix to a PAID pull is the NEXT SNAPSHOT'S OWN
    `regions` AND `credits_used` -- never the diff, never the write-up.

    ⚠️ The five-book set (ledger rule 48) doubles the per-game price, so
    it cannot be what every routine pull uses. It runs ONCE, in the
    morning window, before the day's first real card -- which is where
    cross-book comparison is worth most, because early lines are softer
    and the books disagree more. Sam, 2026-08-23: the five books stand;
    this is about WHEN they are pulled, not WHETHER.
    """
    # 🔴 THE 7:00am ET PULL IS THE FULL ONE (11:00Z), because it is the
    # pull the 10:00am card is priced from -- cross-book comparison is
    # worth most before the day's card, and early lines disagree more.
    # The 4:00pm pull is Hard Rock only. ⚠️ Window is generous so a run
    # that lands late still gets the full pull rather than silently
    # downgrading the card's prices to one book.
    hh = int(now().strftime("%H"))
    if not (10 <= hh < 14):            # 6am-10am ET
        return REGIONS_CHEAP
    root = f"{DATA}/{now().strftime('%Y-%m-%d')}"
    # ⛔ THIS KIND'S DIRECTORY ONLY. Reading the sibling's is what made
    # the pitcher pull answer a question the batter side had asked.
    sub = kind if kind.startswith("props-") else f"props-{kind}"
    d = os.path.join(root, sub)
    if os.path.isdir(d):
        for f in os.listdir(d):
            try:
                with gzip.open(os.path.join(d, f), "rt") as fh:
                    if "," in (json.load(fh).get("regions") or ""):
                        return REGIONS_CHEAP      # already had the full pull
            except Exception:
                continue
    return REGIONS_FULL


PROPS_FRESH_MIN = 45


def props_is_fresh(kind, minutes=PROPS_FRESH_MIN):
    """True when a pull for this kind already landed inside the window.

    🔴 THIS FUNCTION USED `os.path.getmtime` AND WAS THEREFORE A PERMANENT
    LOCK, NOT A GUARD. Every CI run is a fresh `git checkout`, which sets
    every file's mtime to the checkout time -- so the second props pull of
    any day measured an age of ~0 minutes, declared the morning's file
    fresh, and stood down "NOTHING SPENT" for the rest of the day.
    `[measured 2026-08-28]` `props-pitcher/0220.json.gz` was written at
    02:20Z and carried an mtime of 16:47Z in a clean clone; the props on
    the live board were 15 hours old and half the slate had no line at all.

    ⛔ AGE NOW COMES FROM THE SNAPSHOT'S OWN FILENAME (`HHMM.json.gz`),
    which a checkout cannot alter. `getmtime` is banned for freshness
    anywhere in this project -- see `freshness.py`.
    """
    age = _fresh.newest_age_minutes(daydir("props-" + kind))
    if age >= _fresh.MISSING:
        return False
    if age <= minutes:
        log(f"props-{kind}: a pull landed {age:.0f} min ago (window "
            f"{minutes} min). Standing down, NOTHING SPENT.")
        return True
    return False


# ══════════════════════════════════════════════════════════════════════
# 🔴 THE POWER 4 GATE — THE ONE THING THAT MAKES CFB AFFORDABLE
# Props bill `markets x regions x GAMES`, PER GAME. A Saturday NCAAF board
# is ~70 events, so an unfiltered pull is 5 x 2 x 70 = 700 CREDITS FOR ONE
# PULL, against roughly 390/day of headroom on the whole plan.
# ✅ Sam's scope has always been POWER 4 ONLY -- "G5 games carry almost no
# player props, so a wider board means paying to collect empty boards".
# This is that rule enforced at the REQUEST, where it saves money, rather
# than at the write-up, where it saves nothing.
#
# ⚠️ THE TEAM NAMES COME FROM TWO DIFFERENT SOURCES AND I HAVE NOT SEEN
# THE ODDS API'S SPELLING OF THEM. `[unverified 2026-08-31]` Our list is
# CFBD's ("Ohio State"); the Odds API may say "Ohio State Buckeyes". ⛔ A
# NAME JOIN I HAVE NOT MEASURED IS EXACTLY THIS PROJECT'S OLDEST FAILURE.
# ➡️ SO THE GATE FAILS CLOSED AND CHEAP: `/events` is free, the match is
# reported team by team, and if too few events match, THE RUN SPENDS
# NOTHING and writes the unmatched names into the repo to be read.
# ⛔ Better a first run that collects nothing and tells us the names than
# one that quietly pulls 70 events or quietly pulls none.
# ══════════════════════════════════════════════════════════════════════
def _norm_team(x):
    # 🔴 STRIP ACCENTS FIRST. ⛔ CFBD writes "San José State"; the Odds API
    # writes "San Jose State Spartans". Dropping non-alphanumerics without
    # folding the accent turns the first into "sanjosstate" and the second
    # into "sanjosestate", so they never match and an FBS school is
    # silently dropped from the board. Measured 2026-09-03.
    import unicodedata as _ud
    x = _ud.normalize("NFKD", str(x or ""))
    x = "".join(c for c in x if not _ud.combining(c))
    return "".join(c for c in x.lower() if c.isalnum())


# ⛔ CFBD AND THE ODDS API DISAGREE ON SOME SCHOOL NAMES, and the
# difference is not a mascot suffix so prefix-matching cannot bridge it.
# ⚠️ THESE WERE MEASURED, NOT GUESSED: every unmatched name on a real
# 155-game board was listed and checked against the schedule's own
# classification. Only these needed an alias.
# 🔴 KEEP THIS LIST SHORT AND EVIDENCE-BASED. It is a pin for known feed
# disagreements, NOT a general mapping -- a long list here means the
# matcher is wrong and should be fixed instead.
FEED_ALIASES = {
    "appalachianstate": "App State",
    "southernmississippi": "Southern Miss",
    "samhoustonstate": "Sam Houston",
}


# ══════════════════════════════════════════════════════════════════════
# 🔴 THE MAX MUNCY RULE, APPLIED TO TEAM NAMES.
# Sam, 2026-09-01: *"just make sure your talking about the right team,
# just like the max muncy situation for the batters"* -- MLB has TWO Max
# Muncys, and a name-only join silently credits one with the other's
# line.
# ⛔ COLLEGE FOOTBALL HAS THE SAME TRAP AND IT IS WORSE, because the
# collisions are PREFIXES, not duplicates:
#     "Washington State Cougars"  starts with  "Washington"  (Big Ten)
#     "Miami RedHawks" (MAC)      starts with  "Miami"       (ACC)
#     "Michigan State Spartans"   starts with  "Michigan"    (Big Ten)
# ➡️ Tolerating a mascot suffix is what makes the join WORK; the two
# guards below are what stop it pulling a Group of 5 game onto a Power 4
# board and paying per game for it.
# ══════════════════════════════════════════════════════════════════════

# ⛔ A WORD THAT CONTINUES A SCHOOL NAME. If the leftover after our name
# begins with one of these, the feed is naming a DIFFERENT school.
_CONTINUES = {"state", "a&m", "am", "tech", "southern", "northern",
              "eastern", "western", "central", "international",
              "atlantic", "christian", "poly", "dominion", "carolina",
              "illinois", "michigan", "florida", "texas", "kentucky",
              "methodist", "chicago", "st", "saint"}

# ⛔ STEMS THAT NAME TWO REAL SCHOOLS. For these the mascot is REQUIRED --
# exactly the disambiguation the Max Muncy case needs. ⚠️ Keep this list
# SHORT and only for genuine collisions; it is a pin, not a mapping.
_AMBIGUOUS = {"miami": "hurricanes"}


def _match_team(feed_name, by_norm):
    """Our Power 4 team, or None. ⛔ REFUSES rather than guessing."""
    if not feed_name:
        return None
    n = _norm_team(feed_name)
    if n in by_norm:                       # exact -- the common case
        return by_norm[n]
    # ⚠️ A KNOWN FEED DISAGREEMENT, applied to the name AND to the name
    # with its mascot stripped. ⛔ Checked BEFORE the prefix walk so an
    # alias can never be beaten by a coincidental prefix.
    for k, v in FEED_ALIASES.items():
        if n == k or n.startswith(k):
            cand = _norm_team(v)
            if cand in by_norm:
                return by_norm[cand]
    words = str(feed_name).replace("(", " ").replace(")", " ").split()
    # longest candidate first, so "Ohio State" is tried before "Ohio"
    for cand in sorted(by_norm, key=len, reverse=True):
        acc, taken = "", 0
        for i, w in enumerate(words):
            acc += _norm_team(w)
            taken = i + 1
            if acc == cand:
                break
            if len(acc) > len(cand):
                taken = 0
                break
        if not taken or acc != cand:
            continue
        rest = words[taken:]
        if not rest:
            return by_norm[cand]
        # ⛔ GUARD A -- a leftover this long is a DIFFERENT SCHOOL, not a
        # mascot. `[measured 2026-09-01 on the real 103-game board]` our
        # "Arkansas" matched inside "Arkansas Pine Bluff Golden Lions",
        # an FCS SWAC school, and would have put it on the Power 4 board
        # and paid for it. Every legitimate mascot on that board is ONE
        # or TWO words -- "Buckeyes", "Yellow Jackets", "Demon Deacons".
        # ⚠️ Measured, not guessed: 51 one-word and 35 two-word leftovers
        # were legitimate; every 3+ was a different school.
        if len(rest) > 2:
            continue
        # ⛔ GUARD B -- a mascot never carries an ampersand; a school
        # qualifier does. "North Carolina A&T Aggies" would otherwise
        # match our "North Carolina" on a two-word leftover.
        # ⚠️ "Texas A&M Aggies" is unaffected: longest-match consumes the
        # A&M into the school name and the leftover is just "Aggies".
        if any("&" in w for w in rest):
            continue
        if _norm_team(rest[0]) in {_norm_team(x) for x in _CONTINUES}:
            continue                       # "Washington" + "State ..."
        need = _AMBIGUOUS.get(cand)
        if need and not any(_norm_team(w) == _norm_team(need) for w in rest):
            continue                       # "Miami" without "Hurricanes"
        return by_norm[cand]
    return None


def power4_teams():
    """The Power 4 set, READ FROM OUR OWN COLLECTED DATA, not hardcoded.
    ⛔ Hardcoding 67 names guarantees they go stale at the next
    realignment -- the set was 52 teams in 2021 and is 67 now."""
    # 🔴 THE NEWEST FILE IS NOT THE RIGHT FILE IN SEPTEMBER.
    # `[measured 2026-09-02]` a 2026 back-fill wrote a LEGITIMATE
    # `players-2026.json.gz` holding 74 players across SEVEN teams --
    # correct, because only Week 0 had been played. This function took
    # the newest file, so the Power 4 set became SEVEN TEAMS.
    # ⛔ AND THE GATE FAILS CLOSED AT `P4_MIN_MATCH = 8`, so the next
    # college props pull would have MATCHED NOTHING AND COLLECTED
    # NOTHING. Odds history cannot be re-bought: a missed Thursday is
    # missed permanently.
    # ✅ SO WALK NEWEST-FIRST AND TAKE THE FIRST SEASON THAT LOOKS LIKE A
    # REAL CONFERENCE MAP. ⚠️ The floor is 40, comfortably under the 52
    # of 2021 and far above a part-played season -- it asks "is this a
    # season?", not "is this the current season?".
    # ⛔ AND IT SAYS WHICH FILE IT USED. A silently-chosen input is how
    # this went wrong in the first place.
    import glob as _glob
    P4_MIN_TEAMS = 40
    teams = set()
    files = sorted(_glob.glob(
        f"{LEAGUES['ncaaf']['data']}/latest/players-*.json.gz"), reverse=True)
    for p in files:
        got = set()
        try:
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                doc = json.load(fh)
            for pl in doc.get("players", {}).values():
                for g in pl.get("g", []):
                    if g.get("conf") in ("ACC", "Big 12", "Big Ten", "SEC"):
                        got.add(g["team"])
        except Exception as e:
            log(f"  could not read {p}: {type(e).__name__}: {e}")
            continue
        if len(got) >= P4_MIN_TEAMS:
            log(f"  Power 4 list: {len(got)} teams from {p.split('/')[-1]}")
            return got
        log(f"  skipping {p.split('/')[-1]} -- only {len(got)} Power 4 "
            f"teams, below the {P4_MIN_TEAMS} floor (part-played season)")
        teams = got if len(got) > len(teams) else teams
    # ⛔ NOTHING CLEARED THE FLOOR. Return what was found so the caller's
    # own fail-closed gate reports it, rather than pretending to a set.
    log(f"  ⛔ no players file has {P4_MIN_TEAMS}+ Power 4 teams "
        f"(best was {len(teams)}) -- the name gate will refuse to spend")
    return teams


P4_MIN_MATCH = 8          # below this, assume the name join is broken


# 🔴 EVERY FBS SCHOOL, READ FROM OUR OWN SCHEDULE -- NOT HARDCODED and not
# a conference list. Sam, 2026-09-03: *"if a fbs team is playing a fcs team
# i woudl want that included, for example usf, ucf vs a fcs team."*
# ⛔ USF is American Athletic and UCF is Big 12 -- a Power 4 conference
# list gets one and not the other, which is exactly the wrong answer.
# FBS is a DIVISION, so it covers both and survives realignment.
FBS_MIN_TEAMS = 100      # there are ~138; a part-built file must not gate
FBS_MIN_MATCH_PCT = 0.30  # on a real board ~97% of games have an FBS side


def fbs_teams():
    """The FBS set, from the schedule we already collect."""
    import glob as _glob
    files = sorted(_glob.glob(
        f"{LEAGUES['ncaaf']['data']}/latest/schedule-*.json.gz"), reverse=True)
    for p in files:
        got = set()
        try:
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                doc = json.load(fh)
            for g in doc.get("games", []):
                for side, klass in (("home", "home_class"), ("away", "away_class")):
                    if g.get(klass) == "fbs" and g.get(side):
                        got.add(g[side])
        except Exception as e:
            log(f"  could not read {p}: {type(e).__name__}: {e}")
            continue
        if len(got) >= FBS_MIN_TEAMS:
            log(f"  FBS list: {len(got)} schools from {p.split('/')[-1]}")
            return got
        log(f"  skipping {p.split('/')[-1]} -- only {len(got)} FBS schools, "
            f"below the {FBS_MIN_TEAMS} floor")
    return set()


def filter_fbs(events, log=log):
    """Keep an event if AT LEAST ONE side is FBS.

    🔴 *AT LEAST ONE*, NOT BOTH. ⛔ THE BOTH-SIDES VERSION THREW AWAY 122
    OF THE 189 POWER 4 GAMES IN SEPTEMBER -- Alabama, USC, Oklahoma,
    Michigan State, Utah, and tonight's Rutgers, UCF and Wake Forest --
    because each was playing a smaller school. Sam caught this same
    both-sides mistake twice before on the Scores division filter. **It is
    the third instance, so it now has a test that fails on the both-sides
    form by name.**

    ⚠️ What is deliberately EXCLUDED is FCS-vs-FCS, which is what Sam
    asked for and what the books barely price anyway.
    """
    fbs = fbs_teams()
    if not fbs:
        log("  ⛔ no FBS list on disk -- run the schedule build first. "
            "NOTHING SPENT.")
        return [], "no FBS team list on disk"
    norm = {_norm_team(t): t for t in fbs}
    kept, dropped = [], []
    for ev in events:
        h, a_ = ev.get("home_team"), ev.get("away_team")
        # ⛔ ONE SIDE IS ENOUGH.
        if _match_team(h, norm) or _match_team(a_, norm):
            kept.append(ev)
        else:
            dropped.append((a_, h))
    log(f"  FBS gate: {len(kept)} of {len(events)} events kept "
        f"({len(dropped)} with no FBS side)")
    for a_, h in dropped[:8]:
        log(f"    dropped  {a_} @ {h}")
    # 🔴 FAIL CLOSED ON A BROKEN JOIN. On a real college board ~97% of
    # games have an FBS side, so matching under 30% means the NAMES are
    # not joining, not that the slate is small. ⛔ Spending on that case
    # is how a silent join failure becomes a bill.
    if events and (len(kept) / len(events)) < FBS_MIN_MATCH_PCT:
        return [], (f"only {len(kept)} of {len(events)} events matched an "
                    f"FBS school -- the name join looks broken, not the slate")
    return kept, None


def filter_power4(events, log=log):
    """Keep only events where BOTH sides are Power 4. Report everything."""
    p4 = power4_teams()
    if not p4:
        log("  ⛔ no Power 4 list on disk -- run the cfb back-fill first. "
            "NOTHING SPENT.")
        return [], "no Power 4 team list on disk"
    norm = {_norm_team(t): t for t in p4}
    kept, dropped = [], []
    for ev in events:
        h, a_ = ev.get("home_team"), ev.get("away_team")
        hm, am = _match_team(h, norm), _match_team(a_, norm)
        if hm and am:
            kept.append(ev)
        else:
            dropped.append((a_, h))
    log(f"  Power 4 gate: {len(kept)} of {len(events)} events kept")
    for a_, h in dropped[:12]:
        log(f"    dropped  {a_} @ {h}")
    if len(events) and len(kept) < P4_MIN_MATCH:
        # 🔴 FAIL CLOSED. Either it really is a light slate, or the names
        # do not join -- and those look identical from here. ⛔ Spending
        # on the second case is how a silent join failure becomes a bill.
        names = sorted({n for ev in events
                        for n in (ev.get("home_team"), ev.get("away_team"))})
        try:
            os.makedirs(f"{LEAGUES['ncaaf']['data']}/latest", exist_ok=True)
            with open(f"{LEAGUES['ncaaf']['data']}/latest/event-names.txt",
                      "w", encoding="utf-8") as fh:
                fh.write(f"{stamp()}\nEvents on the board: {len(events)}\n"
                         f"Matched as Power 4: {len(kept)}\n\n"
                         "--- the Odds API's own team names ---\n"
                         + "\n".join(names)
                         + "\n\n--- our Power 4 list (from CFBD) ---\n"
                         + "\n".join(sorted(p4)))
            log("  wrote data/ncaaf/latest/event-names.txt -- compare the "
                "two name lists before spending anything")
        except Exception:
            pass
        return [], (f"only {len(kept)} of {len(events)} events matched the "
                    f"Power 4 list; the name join is unproven, so nothing "
                    f"was spent")
    return kept, None


def collect_props(kind, regions=None):
    if kind == "player":
        markets = PROP_MARKETS[LEAGUE]          # 🔴 the football pull
    elif kind == "pitcher":
        # 🔴 Hard Rock ONLY. Sam, 2026-08-22: "i onlt want to see hardrock
        # odds from now on for all props". Enforced at the REQUEST, not at
        # the write-up -- a price that never enters the working set cannot
        # reach a card. us2 still returns espnbet, fliff, betparx, ballybet
        # and hardrockbet_oh in the same response, so the distinct-price
        # check (ledger rule 47) keeps its comparison set for free.
        markets = PITCHER_MARKETS
    else:
        # Hitter props are banked for a model we have not built yet.
        # One book is enough to backtest against; fifteen is paying for
        # precision we cannot currently interpret.
        markets = BATTER_MARKETS

    # 🔴 THE REGION IS THE PRICE. Cost is markets x REGIONS x games, and
    # BOOKS ARE FREE INSIDE A REGION -- one `us,us2` pull returned 18 books
    # for 6 credits (measured 2026-08-26). So narrowing the BOOK list saves
    # nothing; only dropping a region does. `us2` is Hard Rock's region and
    # halves the pull; `us,us2` adds DraftKings, FanDuel, BetMGM and
    # Caesars, which is what best-price shopping needs.
    regions = regions or REGIONS_FULL

    if props_is_fresh(kind):
        return None

    events, used, left = odds_get(f"/sports/{SPORT}/events", {})
    log(f"{len(events)} events on the board; {left} credits before props")

    # 🔴 FOOTBALL: ONLY THE SLATE ABOUT TO BE PLAYED.
    # ⛔ THE ODDS API POSTS THE WHOLE SEASON. The 2026-09-03 gamelines pull
    # returned **272 NFL games** and **155 college games** -- the full
    # schedule, not this week's. Props are charged PER GAME, so an
    # unbounded NFL pull is 6 markets x 2 regions x 272 = **3,264 credits
    # in one call**, against a 20,000 monthly cap and a budget that models
    # it at 16 games (192). Three NFL pulls a week would be 9,792/wk.
    # ⚠️ THE EXISTING RESERVE GUARD WOULD NOT HAVE STOPPED IT: 19,250
    # available minus 3,264 is far above RESERVE, so it would have spent.
    # ✅ The window is what makes the budget's game counts TRUE rather than
    # hoped-for. Every football props cron fires within two days of the
    # slate it is meant to price, so 48h keeps exactly that slate.
    # ⛔ The Power 4 filter is a TEAM filter, not a time filter -- it does
    # not bound this on its own.
    if LEAGUE in ("nfl", "ncaaf"):
        before = len(events)
        cutoff = now() + timedelta(hours=FB_PROPS_WINDOW_H)
        kept = []
        for e in events:
            t = e.get("commence_time")
            if not t:
                continue          # ⚠️ no kickoff time -> cannot bound it -> drop
            try:
                when = datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc)
            except Exception:
                continue
            if when <= cutoff:
                kept.append(e)
        events = kept
        log(f"  slate window: {before} events on the board -> {len(events)} "
            f"within {FB_PROPS_WINDOW_H}h. Saved "
            f"{(before - len(events)) * len(markets) * len(regions.split(','))} "
            f"credits.")
        if not events:
            log(f"SKIPPING {kind} props: no game kicks off within "
                f"{FB_PROPS_WINDOW_H}h. Nothing spent.")
            return left

    # ⛔ CFB ONLY. MLB and NFL are untouched by this branch.
    if LEAGUE == "ncaaf":
        events, why = filter_fbs(events, log)
        if why:
            log(f"SKIPPING {kind} props: {why}")
            return left

    per_game = len(markets) * len(regions.split(","))
    need = per_game * len(events)
    if left - need < RESERVE:
        log(f"SKIPPING {kind} props: would need {need}, only {left} left "
            f"(reserve {RESERVE}). Nothing spent.")
        return left

    out, spent = [], 0
    for ev in events:
        try:
            body, u, left = odds_get(
                f"/sports/{SPORT}/events/{ev['id']}/odds",
                {"regions": regions, "markets": ",".join(markets),
                 "oddsFormat": "american"},
            )
            spent += u
            out.append(body)
        except urllib.error.HTTPError as e:
            # A game with no props posted yet is normal, not an error.
            log(f"  {ev.get('away_team')}@{ev.get('home_team')}: HTTP {e.code}")
        except Exception as e:
            log(f"  {ev.get('away_team')}@{ev.get('home_team')}: {type(e).__name__}")

    write(f"{daydir('props-' + kind)}/{filename()}.gz", {
        "pulled_at": stamp(),
        "endpoint": "per-event",
        "regions": regions,
        "markets": markets,
        "credits_used": spent,
        "credits_remaining": left,
        "n_events": len(out),
        "events": out,
    }, compress=True)
    log(f"props-{kind}: {len(out)} events, spent {spent}, {left} left")
    return left


# ----------------------------------------------------------------------
# Schedule + probables + records. statsapi is free and unmetered.
# ----------------------------------------------------------------------
def collect_schedule():
    d = now().strftime("%Y-%m-%d")
    body, _ = get(
        f"{STATS}/schedule?sportId=1&date={d}"
        "&hydrate=probablePitcher,linescore,team"
    )
    write(f"{daydir('schedule')}/{filename()}.gz", {
        "pulled_at": stamp(),
        "date": d,
        "schedule": body,
    }, compress=True)
    games = (body.get("dates") or [{}])[0].get("games", [])
    log(f"schedule: {len(games)} games")
    return None


# ----------------------------------------------------------------------
# The player-props board.
#
# Joins three things the page cannot join for itself:
#   * batter prop odds (which name players in a free-text field)
#   * hitter game logs (keyed by MLB player id)
#   * the schedule (for who is playing whom, and when)
#
# ⛔ WHAT THIS IS NOT: a model. Every number it emits is either the
# market's (de-vigged price) or the player's own record. There is no
# fitted hitter model in this project, so nothing here carries a Gizmo's
# confidence rating (ledger rule 55). The "why" is assembled from the
# player's actual game log and says only what that log says.
# ----------------------------------------------------------------------
import unicodedata

# market key -> (label, function of a game row -> the stat being bet)
# Pitcher markets are counted over STARTS only. A reliever's two-out
# appearance is not evidence about a starter's strikeout line, and mixing
# them in silently deflates every rate.
PITCHER_PROP_STATS = {
    "pitcher_strikeouts": ("Strikeouts", lambda r: r.get("k")),
    "pitcher_outs":       ("Outs recorded", lambda r: r.get("outs")),
}

PROP_STATS = {
    "batter_hits":            ("Hits",            lambda r: r.get("H")),
    "batter_total_bases":     ("Total bases",     lambda r: r.get("tb")),
    "batter_home_runs":       ("Home runs",       lambda r: r.get("hr")),
    "batter_rbis":            ("RBIs",            lambda r: r.get("rbi")),
    "batter_hits_runs_rbis":  ("Hits+Runs+RBIs",  lambda r: None if r.get("H") is None
                                                   else (r.get("H") or 0) + (r.get("r") or 0) + (r.get("rbi") or 0)),
}


def norm_name(n):
    """Fold accents and punctuation so 'Eury Pérez' matches 'Eury Perez'."""
    if not n:
        return ""
    n = unicodedata.normalize("NFKD", n)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower().replace(".", "").replace("'", "").replace("-", " ")
    n = n.replace(" jr", "").replace(" sr", "").replace(" iii", "").replace(" ii", "")
    return " ".join(n.split())


def _rate(rows, fn, line, side):
    """How often this player has landed this exact bet. Returns (hits, n)."""
    vals = [fn(r) for r in rows]
    vals = [v for v in vals if v is not None]
    if not vals:
        return (0, 0)
    if side == "over":
        return (sum(1 for v in vals if v > line), len(vals))
    return (sum(1 for v in vals if v < line), len(vals))


def _fmt(h, n):
    return f"{h}/{n}" if n else None


_LINEUPS = None


def _lineup_index():
    """(pid, date) -> started?  Built once from data/latest/lineups.json.gz."""
    global _LINEUPS
    if _LINEUPS is None:
        _LINEUPS = {}
        p = f"{LATEST}/lineups.json.gz"
        if os.path.exists(p):
            try:
                D = json.load(gzip.open(p, "rt"))
                for d, rws in (D.get("days") or {}).items():
                    for r in rws:
                        _LINEUPS[(int(r["pid"]), d)] = bool(r.get("started"))
                log(f"  lineups: {len(_LINEUPS)} batter-games with a real batting order")
            except Exception as e:
                log(f"  lineups: unreadable ({type(e).__name__}) -- using the PA proxy")
    return _LINEUPS


def started_game(rec, row):
    """Did he START? Real batting order wins; PA >= 3 is the fallback."""
    pid = rec.get("_pid")
    if pid is not None:
        hit = _lineup_index().get((int(pid), row.get("d")))
        if hit is not None:
            return hit
    return (row.get("pa") or 0) >= 3


FB_MARKET_LABEL = {
    "player_pass_yds":      ("Passing yards",   "pass yds"),
    "player_pass_tds":      ("Passing TDs",     "pass TD"),
    "player_rush_yds":      ("Rushing yards",   "rush yds"),
    "player_reception_yds": ("Receiving yards", "rec yds"),
    "player_receptions":    ("Receptions",      "rec"),
    "player_anytime_td":    ("Anytime TD",      "TD"),
}


def collect_props_board_fb(league=None):
    """Join the day's football prop snapshot into a board the page reads.

    🔴 WHY THIS EXISTS SEPARATELY FROM `collect_props_board`. That
    function is MLB to the bone: it loads `pitchers.json.gz` and
    `hitters.json.gz` and RAISES without them. `[measured 2026-09-02]`
    Thursday's football pull would have stored raw snapshots that
    NOTHING joined, so the Player Props tab would have stayed empty on a
    day the data actually arrived. ⛔ Odds history cannot be re-bought;
    a board that is never built is a pull that was wasted.

    ⚠️ EVERY NUMBER HERE IS 🔵 MARKET AND CARRIES NO PROJECTION.
    ⛔ AND THAT IS NOT A TEMPORARY STATE ON FOOTBALL: three
    pre-registered specifications (T46, T47, T50) each lost to a
    player's own season average, so there is no football MODEL number to
    attach. A line, a price and where to get it is the honest product.

    ⛔ NO PLAYER GAME-LOG JOIN, ON PURPOSE. Attaching a player's own
    trailing numbers means matching a sportsbook's spelling to our
    database -- the Max Muncy problem, and worse in college where a
    roster turns over 45% a year. ⚠️ And 2026 logs do not exist yet.
    ➡️ It is added when there are logs to join AND the match is proven
    by a gate, not before.
    """
    import glob as _g
    lg = league or LEAGUE
    base = LEAGUES[lg]["data"] + "/latest"
    # 🔴 THE SAME DATE CONVENTION AS THE WRITER, NOT A SECOND ONE.
    # `daydir()` files a snapshot under the UTC date; a first draft of
    # this read `et_date()` instead. ⛔ Between 00:00 and 05:00 UTC those
    # differ, so a Thursday-night college pull -- 22:30 ET, which is
    # 02:30 UTC Friday -- would have been looked for under the wrong day
    # and the board would have come back empty on a night the data
    # arrived. ⚠️ Two date conventions for one path is the same class of
    # defect as two copies of a coefficient.
    day = now().strftime("%Y-%m-%d")
    src = sorted(_g.glob(f"{DATA}/{day}/props-player/*.json.gz"))
    if not src:
        # ⚠️ A pull just before midnight UTC lands under yesterday.
        # Looking back one day is cheap and cannot pick up a stale board:
        # the file records its own `pulled_at` and the page shows the age.
        prev = (now() - timedelta(days=1)).strftime("%Y-%m-%d")
        src = sorted(_g.glob(f"{DATA}/{prev}/props-player/*.json.gz"))
        if src:
            day = prev
            log(f"  using the {prev} snapshot (pull landed before midnight UTC)")
    if not src:
        log(f"  no props-player snapshot for {day} -- nothing to join")
        return None
    # ⚠️ NEWEST SNAPSHOT WINS. Several pulls a day land in the same
    # directory; the board describes the most recent one and says when.
    doc = None
    for f in src:
        try:
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                d = json.load(fh)
            if doc is None or (d.get("pulled_at") or "") > (doc.get("pulled_at") or ""):
                doc = d
        except Exception as e:
            log(f"  skipping {f}: {type(e).__name__}: {e}")
    if not doc:
        return None

    books_seen, games = set(), []
    for ev in doc.get("events") or []:
        # rung -> the best price on each side, plus how many books have it
        rungs = {}
        for bk in ev.get("bookmakers") or []:
            key = bk.get("key")
            books_seen.add(key)
            # ⛔ Sam's five books only, same filter as every other pull.
            if key not in BOOKS:
                continue
            for mk in bk.get("markets") or []:
                m = mk.get("key")
                if m not in FB_MARKET_LABEL:
                    continue
                for o in mk.get("outcomes") or []:
                    who = o.get("description")
                    side = (o.get("name") or "").lower()
                    pt = o.get("point")
                    price = o.get("price")
                    if not who or price is None:
                        continue
                    k = (who, m, pt)
                    r = rungs.setdefault(k, {
                        "player": who, "market": m,
                        "label": FB_MARKET_LABEL[m][0],
                        "unit": FB_MARKET_LABEL[m][1],
                        "line": pt, "sides": {}})
                    sd = r["sides"].setdefault(side, {"n_books": 0, "price": None,
                                                      "book": None, "link": None})
                    sd["n_books"] += 1
                    # ⚠️ BEST = LEAST NEGATIVE / MOST POSITIVE. American
                    # odds do not order numerically for a bettor.
                    if sd["price"] is None or price > sd["price"]:
                        sd["price"] = price
                        sd["book"] = key
                        sd["link"] = o.get("link") or mk.get("link") or bk.get("link")
        props = sorted(rungs.values(),
                       key=lambda r: (r["market"], r["player"], r["line"] or 0))
        if not props:
            continue
        games.append({
            "id": ev.get("id"),
            "home": ev.get("home_team"), "away": ev.get("away_team"),
            "commence": ev.get("commence_time"),
            "n_props": len(props),
            "props": props,
        })
    games.sort(key=lambda g: g["commence"] or "")
    out = {
        "kind": "MARKET",
        "note": ("Player prop lines and the best available price across "
                 "Sam's five books. NOT a Gizmo's projection (rule 55) -- "
                 "football has no model, so no row carries a confidence %."),
        "league": lg,
        "pulled_at": doc.get("pulled_at"),
        "regions": doc.get("regions"),
        "books_seen": sorted(books_seen),
        "n_games": len(games),
        "n_props": sum(g["n_props"] for g in games),
        "games": games,
    }
    write(f"{base}/props.json.gz", out, compress=True)
    log(f"  props board: {out['n_games']} games, {out['n_props']} rungs, "
        f"books {sorted(b for b in books_seen if b in BOOKS)}")
    return out


def collect_props_board():
    """Join prop odds to game logs. Batters and pitchers, one board."""
    import glob

    def load_pool(path, label):
        if not os.path.exists(path):
            log(f"  {label}: {path} missing — those markets will be skipped")
            return None, {}
        D = json.load(gzip.open(path, "rt"))
        by = {}
        for pid, v in D["players"].items():
            v["_pid"] = pid
            by.setdefault(norm_name(v["name"]), []).append((pid, v))
        dupes = {k: [x[1]["name"] + " (" + str(x[1]["team"]) + ")" for x in v]
                 for k, v in by.items() if len(v) > 1}
        log(f"  {label}: {D['n_players']} players (pulled {D['pulled_at']})")
        if dupes:
            log(f"    shared name(s), resolved by team: {dupes}")
        return D, by

    H, by_hit = load_pool(f"{LATEST}/hitters.json.gz", "hitter logs")
    PI, by_pit = load_pool(f"{LATEST}/pitchers.json.gz", "pitcher logs")
    if H is None and PI is None:
        raise RuntimeError("no game logs at all — run the hitters and pitchers jobs first")

    def resolve(table, who, away, home):
        """(pid, record) or (None, None). Never guesses on a shared name."""
        c = table.get(norm_name(who))
        if not c:
            return (None, None)
        if len(c) == 1:
            return c[0]
        inplay = [x for x in c if x[1].get("team") in (away, home)]
        return inplay[0] if len(inplay) == 1 else (None, None)

    d = now().strftime("%Y-%m-%d")
    merged, unmatched, links_seen = {}, set(), 0

    def ingest(kind, stat_map, table, starts_only):
        nonlocal links_seen
        # ⚠️ Fall back to the most recent day that HAS a snapshot. The
        # UTC date rolls at 8pm ET, mid-slate, so a run just after
        # midnight UTC would otherwise find nothing and report an empty
        # board as though no props existed. Report which day was used.
        snaps = sorted(glob.glob(f"data/{d}/props-{kind}/*.json.gz"))
        if not snaps:
            older = sorted(glob.glob(f"data/*/props-{kind}/*.json.gz"))
            if not older:
                log(f"  props-{kind}: nothing stored for {d} and no older snapshot")
                return None
            snaps = [older[-1]]
            log(f"  props-{kind}: nothing for {d}, falling back to {snaps[-1]}")
        B = json.load(gzip.open(snaps[-1], "rt"))
        log(f"  props-{kind}: {B['n_events']} events (pulled {B['pulled_at']})")

        for ev in B.get("events", []):
            away, home = ev.get("away_team"), ev.get("home_team")

            # Best price is a shopping question. Fair probability is a
            # pricing question and may only be asked of one book at a time.
            best, per_book, hr, ladder = {}, {}, {}, {}
            dropped = set()
            for bk in ev.get("bookmakers", []):
                # ⛔ Anything outside the five is not shown at all. A price
                # Sam cannot bet is not a better price -- and it was
                # winning the "best price" comparison and taking the bet
                # link with it, which is why links kept landing on books
                # he has never heard of.
                if bk.get("key") not in BOOKS:
                    dropped.add(bk.get("key"))
                    continue
                for m in bk.get("markets", []):
                    # 🔴 STEP 5: alt ladders are mandatory on every card. They
                    # were being pulled and then dropped here, which is what a
                    # rung-walk into the 1.8x band needs and could not find.
                    # Hard Rock only -- it is the book that multiplies, and the
                    # feed carries only the OVER side of its ladder (the book
                    # itself offers both; ask Sam for an under rung's price).
                    if m.get("key") in ALT_MARKETS and bk["key"] in ("hardrockbet", "hardrockbet_oh"):
                        for o in m.get("outcomes", []):
                            who, pt, px = o.get("description"), o.get("point"), o.get("price")
                            sd_ = (o.get("name") or "").lower()
                            if not who or pt is None or px is None:
                                continue
                            ladder.setdefault(norm_name(who), []).append({
                                "market": ALT_MARKETS[m["key"]], "line": pt, "side": sd_,
                                "price": px, "book": bk["key"],
                                "app_label": (f"To Record {int(pt + 0.5)}+"
                                              if sd_ == "over" and ALT_MARKETS[m["key"]] == "strikeouts"
                                              else None),
                                **({"link": o.get("link") or m.get("link") or bk.get("link")}
                                   if (o.get("link") or m.get("link") or bk.get("link")) else {}),
                            })
                    if m.get("key") not in stat_map:
                        continue
                    for o in m.get("outcomes", []):
                        who, pt, px = o.get("description"), o.get("point"), o.get("price")
                        side = (o.get("name") or "").lower()
                        if not who or pt is None or px is None or side not in ("over", "under"):
                            continue
                        k = (who, m["key"], pt, side)
                        if k not in best or px > best[k]["price"]:
                            best[k] = {"price": px, "book": bk["key"]}
                            lk = o.get("link") or m.get("link") or bk.get("link")
                            if lk:
                                best[k]["link"] = lk
                                links_seen += 1
                        per_book.setdefault((who, m["key"], pt), {})\
                                .setdefault(bk["key"], {})[side] = px
                        # Hard Rock's own number, kept separately. The card
                        # may only quote the book Sam bets at, and "best
                        # across books" is a different question from "what
                        # does his book say".
                        if bk["key"] in ("hardrockbet", "hardrockbet_oh"):
                            e = hr.setdefault(k, {})
                            if "price" not in e or bk["key"] == "hardrockbet":
                                e["price"] = px
                                e["book"] = bk["key"]
                                lk2 = o.get("link") or m.get("link") or bk.get("link")
                                if lk2:
                                    e["link"] = lk2

            fair = {}
            for key, books_here in per_book.items():
                vals = []
                for px in books_here.values():
                    if "over" not in px or "under" not in px:
                        continue
                    ro, ru = implied(px["over"]), implied(px["under"])
                    if ro is None or ru is None or (ro + ru) <= 0:
                        continue
                    vals.append(ro / (ro + ru))
                if vals:
                    fair[key] = (sum(vals) / len(vals), len(vals))

            props = []
            for (who, mk, pt, side), v in sorted(best.items()):
                _lbl, fn = stat_map[mk]
                pid, rec = resolve(table, who, away, home)
                if rec is None:
                    unmatched.add(who)

                imp_pct = n_books = None
                if (who, mk, pt) in fair:
                    p_over, n_books = fair[(who, mk, pt)]
                    imp_pct = round(100 * (p_over if side == "over" else 1 - p_over), 1)

                ev_block = {}
                if rec:
                    rows = rec["g"]
                    if starts_only:
                        rows = [r for r in rows if r.get("gs")]
                    else:
                        # 🔴 THE HITTER ANALOGUE OF STARTS-ONLY -- and the
                        # first version of it did not go far enough.
                        #
                        # A game with NO plate appearance is obviously not
                        # an under that won; at the book it is a VOID. But
                        # a ONE- OR TWO-PLATE-APPEARANCE CAMEO is not a
                        # start either, and counting it as one biases every
                        # hitter UNDER upward. Measured 2026-08-24 across
                        # 37,829 played games:
                        #
                        #   under 0.5 hits : cameo 74.8%  start 37.4%  +37.4
                        #   under 1.5 TB   : cameo 90.4%  start 63.5%  +27.0
                        #   under 0.5 RBI  : cameo 87.8%  start 69.4%  +18.4
                        #
                        # Cameos are 13.7% of played games and land hardest
                        # on bench bats -- exactly who was topping the board.
                        #
                        # ⚠️ PA >= 3 IS A PROXY FOR "HE STARTED" and it is a
                        # stopgap. The `lineups` collector recovers real
                        # batting order; `started` (sub == 0) SUPERSEDES this
                        # the moment that file exists.
                        rows = [r for r in rows if started_game(rec, r)]
                    opp = away if rec.get("team") == home else home
                    season = _rate(rows, fn, pt, side)
                    ev_block = {
                        "season": _fmt(*season),
                        "last15": _fmt(*_rate(rows[-15:], fn, pt, side)),
                        "home": _fmt(*_rate([r for r in rows if r.get("h")], fn, pt, side)),
                        "road": _fmt(*_rate([r for r in rows if not r.get("h")], fn, pt, side)),
                        "vs_opp": _fmt(*_rate([r for r in rows if r.get("o") == opp], fn, pt, side)),
                        "opp": opp,
                        "bats": rec.get("bats") or rec.get("throws"),
                    }

                props.append({
                    "player": who, "pid": int(pid) if pid else None,
                    "team": (rec or {}).get("team"), "market": mk, "kind": kind,
                    "line": pt, "side": side, "price": v["price"], "book": v["book"],
                    "implied": imp_pct, "n_books": n_books, "evidence": ev_block,
                    **({"link": v["link"]} if v.get("link") else {}),
                    **({"hr": hr[(who, mk, pt, side)]} if (who, mk, pt, side) in hr else {}),
                })

            if props:
                g = merged.setdefault(ev.get("id"), {
                    "id": ev.get("id"), "commence": ev.get("commence_time"),
                    "away": away, "home": home, "props": []})
                g["props"].extend(props)
                if ladder:
                    for kk, v2 in ladder.items():
                        # hardrockbet and hardrockbet_oh post the same rung.
                        # One rung, one row -- a duplicate here becomes a
                        # duplicate play on the card.
                        seen_r = {}
                        for r in v2:
                            kx = (r["market"], r["line"], r["side"])
                            if kx not in seen_r or r["book"] == "hardrockbet":
                                seen_r[kx] = r
                        v2[:] = sorted(seen_r.values(), key=lambda r: (r["market"], r["line"]))
                    g.setdefault("ladders", {}).update(ladder)
        return B["pulled_at"]

    bat_at = ingest("batter", PROP_STATS, by_hit, starts_only=False) if H else None
    pit_at = ingest("pitcher", PITCHER_PROP_STATS, by_pit, starts_only=True) if PI else None
    if bat_at is None and pit_at is None:
        raise RuntimeError(f"no prop snapshots stored for {d}")

    games = sorted(merged.values(), key=lambda g: g["commence"])
    total = sum(len(g["props"]) for g in games)
    write(f"{LATEST}/props.json.gz", {
        "pulled_at": stamp(),
        "batter_odds_at": bat_at, "pitcher_odds_at": pit_at,
        "hitters_pulled_at": (H or {}).get("pulled_at"),
        "pitchers_pulled_at": (PI or {}).get("pulled_at"),
        "kind": "MARKET + DESCRIPTIVE",
        "note": "Market prices and each player's own record. No hitter model exists; "
                "nothing here carries a Gizmo's confidence rating (ledger rule 55).",
        "bet_links": links_seen,
        "n_games": len(games), "n_props": total,
        "unmatched": sorted(unmatched)[:60],
        "games": games,
    }, compress=True)
    log(f"props board: {len(games)} games, {total} props, "
        f"{len(unmatched)} unmatched names, {links_seen} bet links")
    if unmatched:
        log(f"  unmatched sample: {sorted(unmatched)[:6]}")
    return None


# ----------------------------------------------------------------------
# Pitcher game logs — the mirror of the hitter pull, and what lets the
# props tab cover strikeouts and outs alongside the batter markets. Free.
#
# ⛔ This is the raw log only. The project's fitted strikeout/outs model
# lives elsewhere; a model number never comes from this file (rule 55).
# ----------------------------------------------------------------------
PITCHER_MIN_IP = 20


def collect_pitchers():
    yr = now().year
    pool, _ = get(f"{STATS}/stats?stats=season&group=pitching&season={yr}&gameType=R"
                  f"&limit=900&sortStat=inningsPitched")
    splits = (pool.get("stats") or [{}])[0].get("splits", []) if pool.get("stats") else []
    people, skipped = [], 0
    for sp in splits:
        st, pl = sp.get("stat") or {}, sp.get("player") or {}
        try:
            outs = outs_of(st.get("inningsPitched"))
        except ValueError as e:
            log(f"  DOMAIN VIOLATION in season pool: {e}")
            skipped += 1
            continue
        if outs is not None and outs >= PITCHER_MIN_IP * 3 and pl.get("id"):
            people.append({"id": pl["id"], "name": pl.get("fullName"),
                           "team": (sp.get("team") or {}).get("name"),
                           "era": st.get("era"), "whip": st.get("whip"),
                           "w": st.get("wins"), "l": st.get("losses"),
                           "gs": st.get("gamesStarted"), "outs": outs})
    log(f"pitcher pool: {len(splits)} returned, {len(people)} with >= {PITCHER_MIN_IP} IP")
    if not people:
        raise RuntimeError("pitcher pool came back empty")

    hand = {}
    ids = [p["id"] for p in people]
    for i in range(0, len(ids), 100):
        try:
            d, _ = get(f"{STATS}/people?personIds={','.join(str(x) for x in ids[i:i+100])}"
                       "&fields=people,id,pitchHand,code")
            for pp in d.get("people", []):
                hand[pp["id"]] = (pp.get("pitchHand") or {}).get("code")
        except Exception as e:
            log(f"  handedness chunk {i}: {type(e).__name__}")

    logs, bad, viol = {}, 0, skipped
    for p in people:
        try:
            d, _ = get(f"{STATS}/people/{p['id']}/stats?stats=gameLog&group=pitching"
                       f"&season={yr}&gameType=R"
                       "&fields=stats,splits,date,isHome,opponent,name,stat,gamesStarted,"
                       "inningsPitched,strikeOuts,earnedRuns,hits,baseOnBalls,numberOfPitches,battersFaced")
            sp = (d.get("stats") or [{}])[0].get("splits", []) if d.get("stats") else []
        except Exception as e:
            log(f"  {p['name']}: {type(e).__name__}")
            bad += 1
            continue
        rows = []
        for g in sp:
            st = g.get("stat") or {}
            try:
                o = outs_of(st.get("inningsPitched"))
            except ValueError as e:
                log(f"  DOMAIN VIOLATION {p['name']} {g.get('date')}: {e}")
                viol += 1
                continue
            rows.append({"d": g.get("date"), "o": (g.get("opponent") or {}).get("name"),
                         "h": 1 if g.get("isHome") else 0,
                         "gs": 1 if (st.get("gamesStarted") or 0) > 0 else 0,
                         "outs": o, "k": st.get("strikeOuts"), "er": st.get("earnedRuns"),
                         "hit": st.get("hits"), "bb": st.get("baseOnBalls"),
                         "np": st.get("numberOfPitches"), "bf": st.get("battersFaced")})
        if rows:
            logs[p["id"]] = {"name": p["name"], "team": p["team"], "throws": hand.get(p["id"]),
                             "era": p["era"], "whip": p["whip"], "w": p["w"], "l": p["l"],
                             "gs": p["gs"], "g": rows}

    write(f"{LATEST}/pitchers.json.gz", {
        "pulled_at": stamp(), "season": yr, "min_ip": PITCHER_MIN_IP,
        "n_players": len(logs), "n_failed": bad, "domain_violations": viol,
        "players": logs}, compress=True)
    log(f"pitchers: {len(logs)} arms, {sum(len(v['g']) for v in logs.values())} rows, "
        f"{bad} failed, {viol} domain violations")
    return None


# ----------------------------------------------------------------------
# News.
#
# Fetched here rather than in the page because RSS hosts do not send CORS
# headers, so a browser cannot read them directly. Pulled on the runner,
# normalised, and committed as plain JSON the page can load same-origin.
#
# ⚠️ Headlines and links only, with attribution to the source. No article
# text is copied.
# ----------------------------------------------------------------------
# 🔴 KEYED BY LEAGUE, AND `mlb`'s LIST IS THE ONE THAT HAS ALWAYS SHIPPED.
# ⛔ Do not reorder or edit the mlb entry -- it is a live feed on a live
# page and it works.
#
# ⚠️ THE FOOTBALL LISTS ARE EMPTY ON PURPOSE. They are filled from the
# PROBE REPORT, not from a guess. `news-probe` fetches NEWS_CANDIDATES,
# parses each one exactly the way `collect_news` will, and writes what it
# found. A feed URL that looks obviously right is still a guess: ESPN's
# college path is `ncf`, not `ncaaf` or `college-football`, and there is
# no way to know that from the outside. ⛔ Ship nothing here until a probe
# report says the feed parsed and the headlines are the right sport.
NEWS_FEEDS = {
    "mlb": [
        ("MLB.com", "https://www.mlb.com/feeds/news/rss.xml"),
        # 🔴 DEAD AS OF 2026-09-03 and kept deliberately. It returns an
        # EMPTY BODY, exactly as ESPN's college and NFL feeds do, so it
        # contributes nothing -- the live news.json that day held 25
        # MLB.com and 25 CBS items and ZERO from ESPN. ⛔ Left in place so
        # it resumes automatically if ESPN restores RSS, and the new
        # per-feed health block makes its silence visible instead of
        # invisible. ⚠️ Removing it would hide the fact that it broke.
        ("ESPN MLB", "https://www.espn.com/espn/rss/mlb/news"),
        ("CBS Sports", "https://www.cbssports.com/rss/headlines/mlb/"),
    ],
    # ✅ ADOPTED 2026-09-03 FROM THE PROBE REPORT, after reading the
    # sample headlines. ⛔ Not from a guess -- see NEWS_CANDIDATES below
    # and `data/<lg>/latest/news-probe.json` for what was rejected.
    #
    # 🔴 EVERY ESPN FEED IS DEAD. All three ESPN URLs returned an EMPTY
    # BODY ("no element found: line 1, column 0"), college and NFL alike.
    # ⚠️ That is a fact about ESPN, not about our parser -- the same
    # parser read 25 clean items from every other feed in the same run.
    # NFL.com returned a hard 404.
    #
    # ⛔ YAHOO NFL IS PROFOOTBALLTALK SYNDICATED and is deliberately NOT
    # adopted: "Mike Hall moves past training camp incident with Quinshon
    # Judkins" appeared VERBATIM in both samples. PFT is the original and
    # carries images on all 25 items; Yahoo carried none.
    "nfl": [
        ("CBS Sports", "https://www.cbssports.com/rss/headlines/nfl/"),
        ("ProFootballTalk", "https://profootballtalk.nbcsports.com/feed/"),
    ],
    "ncaaf": [
        ("CBS Sports", "https://www.cbssports.com/rss/headlines/college-football/"),
        ("Yahoo CFB", "https://sports.yahoo.com/college-football/rss.xml"),
    ],
}

# ⚠️ CANDIDATES ARE NOT FEEDS. Nothing here is believed until probed --
# every one of these URLs is my guess at a pattern, and the point of the
# probe is that a guess and a fact are different things.
NEWS_CANDIDATES = {
    "nfl": [
        ("ESPN NFL", "https://www.espn.com/espn/rss/nfl/news"),
        ("CBS Sports", "https://www.cbssports.com/rss/headlines/nfl/"),
        ("NFL.com", "https://www.nfl.com/feeds/rss/news"),
        ("Yahoo NFL", "https://sports.yahoo.com/nfl/rss.xml"),
        ("ProFootballTalk", "https://profootballtalk.nbcsports.com/feed/"),
    ],
    "ncaaf": [
        # ⚠️ ESPN's college-football path is `ncf`. Both spellings are
        # probed BECAUSE I am not certain which one answers.
        ("ESPN CFB", "https://www.espn.com/espn/rss/ncf/news"),
        ("ESPN CFB alt", "https://www.espn.com/espn/rss/ncaaf/news"),
        ("CBS Sports", "https://www.cbssports.com/rss/headlines/college-football/"),
        ("Yahoo CFB", "https://sports.yahoo.com/college-football/rss.xml"),
    ],
}

# 🔴 THE BARS, FIXED BEFORE THE PROBE RUNS. A feed that misses one is
# reported and NOT adopted. ⛔ Do not relax one after seeing the report --
# that is the whole reason they are written down here first.
NEWS_MIN_ITEMS = 8      # fewer than this is not a news feed
NEWS_MIN_DATED = 0.90   # undated items sink to the bottom and read as stale
NEWS_MIN_LINKED = 1.00  # a headline with no link is not usable at all


def probe_news(league):
    """Fetch every candidate, parse it the way collect_news would, report.

    🔴 WRITES NO news.json. ⛔ A probe that ships its own findings is not a
    probe -- it is an unreviewed deploy. This writes a report and stops,
    and a human reads the sample headlines to confirm the feed is the
    RIGHT SPORT. A feed can parse perfectly and still be the wrong thing:
    a 404 page is valid XML, and a network's general sports feed returns
    real, dated, linked headlines about basketball.
    """
    cands = NEWS_CANDIDATES.get(league, [])
    if not cands:
        log(f"news-probe: no candidates for {league}")
        return None

    report = []
    for source, url in cands:
        row = {"source": source, "url": url}
        try:
            items = _news_items(source, url)
        except Exception as e:
            row.update(ok=False, error=f"{type(e).__name__}: {e}")
            report.append(row)
            log(f"  🔴 {source}: {row['error']}")
            continue

        n = len(items)
        dated = sum(1 for i in items if i.get("published"))
        linked = sum(1 for i in items if i.get("link"))
        imaged = sum(1 for i in items if i.get("image"))
        summed = sum(1 for i in items if i.get("summary"))
        row.update(
            n=n,
            dated=dated, linked=linked, imaged=imaged, summarised=summed,
            pct_dated=round(dated / n, 3) if n else 0.0,
            pct_linked=round(linked / n, 3) if n else 0.0,
            # 🔴 THE SAMPLE IS THE POINT. Every number above can pass on a
            # feed about the wrong sport. A human reads these.
            sample=[i["title"] for i in items[:5]],
        )
        row["ok"] = bool(
            n >= NEWS_MIN_ITEMS
            and row["pct_dated"] >= NEWS_MIN_DATED
            and row["pct_linked"] >= NEWS_MIN_LINKED
        )
        report.append(row)
        log(f"  {'✅' if row['ok'] else '🔴'} {source}: {n} items, "
            f"{dated} dated, {linked} linked, {imaged} with art")
        for t in row["sample"][:3]:
            log(f"       · {t[:90]}")

    passed = [r for r in report if r.get("ok")]
    write(f"{LATEST}/news-probe.json", {
        "pulled_at": stamp(),
        "league": league,
        "kind": "DESCRIPTIVE",
        "bars": {"min_items": NEWS_MIN_ITEMS,
                 "min_pct_dated": NEWS_MIN_DATED,
                 "min_pct_linked": NEWS_MIN_LINKED},
        "n_candidates": len(cands),
        "n_passed": len(passed),
        # ⚠️ NOT a recommendation to ship. The headlines still have to be
        # read by a person to confirm the sport.
        "passed": [r["source"] for r in passed],
        "candidates": report,
    })
    log(f"news-probe[{league}]: {len(passed)}/{len(cands)} candidates cleared the bars")
    log("  ⚠️ READ THE SAMPLE HEADLINES before adding any of these to NEWS_FEEDS.")
    return None


def _news_items(source, url):
    """Fetch ONE feed and return its normalised items.

    🔴 THIS IS THE ONE PARSER. `collect_news` and `probe_news` both call
    it, so the probe measures the code that will actually run. ⛔ A probe
    with its own copy of the parser is a check that cannot fail on the
    defect it exists to catch -- it would pass on a feed the real
    collector chokes on, and vice versa.

    ⚠️ Raises on a fetch or XML failure. The CALLER decides whether that
    is fatal: the collector skips the source, the probe records it.
    """
    import re as _re
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime

    req = urllib.request.Request(url, headers={"User-Agent": "gizmos-picks/0.1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    root = ET.fromstring(raw)

    out = []
    n = 0
    for it in root.iter("item"):
        def txt(tag):
            e = it.find(tag)
            return (e.text or "").strip() if e is not None and e.text else ""
        title, link = txt("title"), txt("link")
        if not title or not link:
            continue
        when = txt("pubDate")
        iso = None
        if when:
            try:
                iso = parsedate_to_datetime(when).astimezone(timezone.utc)\
                    .strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                iso = None
        # 🔴 Summary AND image. Feeds disagree on where both live, so
        # try every shape in turn rather than assuming one. Measured
        # 2026-08-23: the previous parser read only <description> and
        # every stored item came back with an EMPTY summary and no
        # image at all. A missing image is fine -- the page falls back
        # to a plain tile -- but silently producing nothing is not.
        MRSS = "{http://search.yahoo.com/mrss/}"
        CONTENT = "{http://purl.org/rss/1.0/modules/content/}"

        body = txt("description") or txt(CONTENT + "encoded") or txt("summary")
        desc = _re.sub(r"<[^>]+>", " ", body)
        desc = _re.sub(r"&[a-z]+;|&#\d+;", " ", desc)
        desc = " ".join(desc.split())[:240]

        # 🔴 SWEEP EVERY DESCENDANT rather than guessing the tag.
        # Measured 2026-08-24: CBS returned an image on 25/25 items and
        # MLB.com on 0/25, because MLB nests its art somewhere the
        # fixed find() list did not look. Feeds disagree about where an
        # image lives and they are entitled to; the parser is what has
        # to be flexible. Any element whose tag mentions thumbnail,
        # image, content or enclosure is a candidate, and the first one
        # that looks like an image URL wins.
        img = None
        for e in it.iter():
            tag = e.tag.rsplit("}", 1)[-1].lower()
            if not any(k in tag for k in ("thumbnail", "image", "content", "enclosure")):
                continue
            typ = (e.get("type") or e.get("medium") or "").lower()
            if typ and "image" not in typ and tag != "thumbnail":
                continue          # audio/video enclosure -- not art
            # 🔴 DO NOT REQUIRE A FILE EXTENSION. Measured 2026-08-24:
            # CBS returned an image on 25/25 items and MLB.com on 0/25,
            # because MLB serves Cloudinary-style URLs with NO
            # extension at all (".../image/upload/t_16x9/w_1024/mlb/xy").
            # The extension test was the bug, not the feed. A media
            # element that hands back a url IS the image -- trust the
            # element, not the filename.
            for cand in (e.get("url"), e.get("href"), e.get("src"),
                         (e.text or "").strip()):
                if cand and _re.match(r"https?://", cand):
                    img = cand
                    break
            if img:
                break
        if not img:
            # last resort: the first <img src> inside the body html
            m = _re.search(r'<img[^>]+src=["\']([^"\']+)', body)
            if m:
                img = m.group(1)
        if img and img.startswith("http://"):
            img = "https://" + img[7:]      # the page is https; http images are blocked

        out.append({"source": source, "title": title, "link": link,
                    "published": iso, "summary": desc,
                    **({"image": img} if img else {})})
        n += 1
        if n >= 25:
            break
    return out


# ══════════════════════════════════════════════════════════════════════
# NFL TEAM DIRECTORY — name, abbreviation, logo.
#
# 🔴 WHY THIS IS A LIST AND THE COLLEGE ONE IS NOT. CFBD ships logos with
# `/teams/fbs`, so college is read live and survives realignment. The NFL
# has no equivalent free endpoint we already call, and it is **32 teams
# whose abbreviations have not changed in years** -- a relocation is rare
# and newsworthy, not silent drift.
# ⚠️ THE ABBREVIATIONS ARE NOT INVENTED: they are the ones nflverse
# already uses in `schedule-<yr>.json.gz`, so the schedule tab and the
# odds tab resolve to the SAME logo. ⛔ If you edit one side, edit both.
# ⚠️ Logos come from ESPN's public CDN by abbreviation. A URL that 404s
# degrades to the text abbreviation on the page -- `fbMark` has an
# onerror fallback -- so a bad entry is cosmetic, never a broken tab.
# ══════════════════════════════════════════════════════════════════════
NFL_TEAMS = {
    "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL",
    "Baltimore Ravens": "BAL", "Buffalo Bills": "BUF",
    "Carolina Panthers": "CAR", "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE",
    "Dallas Cowboys": "DAL", "Denver Broncos": "DEN",
    "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND",
    "Jacksonville Jaguars": "JAX", "Kansas City Chiefs": "KC",
    "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LA", "Miami Dolphins": "MIA",
    "Minnesota Vikings": "MIN", "New England Patriots": "NE",
    "New Orleans Saints": "NO", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI",
    "Pittsburgh Steelers": "PIT", "San Francisco 49ers": "SF",
    "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN", "Washington Commanders": "WAS",
}
NFL_LOGO = "https://a.espncdn.com/i/teamlogos/nfl/500/{}.png"


def build_nfl_teams():
    """Write the NFL team directory the page reads for logos.

    ⚠️ Keyed BOTH ways -- by full name (what the odds board uses) and by
    abbreviation (what the schedule uses) -- so one lookup serves every
    tab. ⛔ Two lookup paths would be two things to drift.
    """
    directory = {}
    for full, ab_ in NFL_TEAMS.items():
        entry = {"abbr": ab_, "logo": NFL_LOGO.format(ab_.lower()),
                 "name": full}
        directory[full] = entry
        directory[ab_] = entry
    write(f"{LEAGUES['nfl']['data']}/latest/teams.json", {
        "kind": "DESCRIPTIVE",
        "built_at": stamp(),
        "n": len(NFL_TEAMS),
        "source": "static name/abbr map + ESPN CDN logos",
        "teams": directory})
    log(f"nfl teams: {len(NFL_TEAMS)} teams written")
    return None


def build_card_fb():
    """Run `card_fb.py` for this league.

    🔴 A SUBPROCESS, NOT AN IMPORT. `card_fb` reads LEAGUE at import time
    and the collector may already have imported it for a different league
    in the same process. ⛔ Re-importing a module to change a constant is
    how a college board would get NFL rates attached to it.

    ⚠️ Football only. MLB has `card.py` and this must never touch it.
    """
    if LEAGUE == "mlb":
        log("card-fb is a FOOTBALL mode; MLB uses card.py. Nothing done.")
        return None
    import subprocess
    env = dict(os.environ, LEAGUE=LEAGUE)
    r = subprocess.run([sys.executable, "card_fb.py"], env=env,
                       capture_output=True, text=True)
    for line in (r.stdout or "").splitlines():
        log(f"  {line}")
    if r.returncode != 0:
        raise RuntimeError(f"card_fb.py exited {r.returncode}: "
                           f"{(r.stderr or '')[-400:]}")
    return None


def collect_news():
    # 🔴 THE LEAGUE PICKS THE LIST. ⛔ An empty list is NOT an error and
    # must NOT write an empty news.json over a good one -- football has no
    # adopted feed until a probe report is read. It is a clean no-op.
    feeds = NEWS_FEEDS.get(LEAGUE, [])
    if not feeds:
        log(f"news: no feeds adopted for {LEAGUE} yet — run `news-probe` "
            f"and read the sample headlines. Nothing written.")
        return None

    items, health = [], []
    for source, url in feeds:
        try:
            got = _news_items(source, url)
        except Exception as e:
            log(f"  🔴 {source}: {type(e).__name__}: {e}")
            health.append({"source": source, "n": 0,
                           "error": f"{type(e).__name__}: {e}"})
            continue
        items.extend(got)
        health.append({"source": source, "n": len(got)})
        # 🔴 A FEED THAT RETURNS NOTHING MUST SAY SO. ⛔ MEASURED
        # 2026-09-03: ESPN's RSS is dead across every sport, and MLB's
        # news tab had been running on TWO of its THREE feeds for an
        # unknown length of time WITHOUT ANYONE KNOWING -- because
        # `collect_news` only raises when EVERY feed fails, and a feed
        # that parses cleanly to zero items looked like a quiet day.
        # ⚠️ This is the project's own rule: a stale page that looks
        # fresh is worse than an outage.
        if not got:
            log(f"  🔴 {source}: PARSED BUT RETURNED ZERO ITEMS -- "
                f"the feed is probably dead. It is NOT being counted.")
        else:
            log(f"  {source}: {len(got)} items")

    # Newest first; undated entries sink to the bottom rather than the top.
    items.sort(key=lambda x: x["published"] or "", reverse=True)

    # 🔴 DEDUPE BY HEADLINE ACROSS FEEDS. ⛔ SYNDICATION IS REAL AND WAS
    # MEASURED, NOT IMAGINED: the 2026-09-03 probe found Yahoo NFL
    # republishing ProFootballTalk verbatim. Two feeds that share a wire
    # would otherwise print the same story twice on the page, which reads
    # as a broken site. ⚠️ Sorted newest-first already, so the FIRST copy
    # kept is the freshest; ties keep whichever feed was listed first.
    seen, deduped = set(), []
    for it in items:
        k = "".join(c for c in (it["title"] or "").lower() if c.isalnum())
        if k and k in seen:
            continue
        seen.add(k)
        deduped.append(it)
    if len(deduped) != len(items):
        log(f"  deduped {len(items) - len(deduped)} syndicated duplicate(s)")
    items = deduped

    if not items:
        raise RuntimeError("every news feed failed — nothing written")

    write(f"{LATEST}/news.json", {
        "pulled_at": stamp(),
        "kind": "DESCRIPTIVE",
        "n": len(items),
        # ⚠️ PER-FEED HEALTH, so a dead source is visible in the artifact
        # rather than only in a log nobody reads. Additive -- the page
        # ignores it.
        "feeds": health,
        "n_dead": sum(1 for h in health if not h["n"]),
        "items": items[:60],
    })
    log(f"news: {len(items)} items from {len({i['source'] for i in items})} sources")
    return None


# ----------------------------------------------------------------------
# Hitter game logs — the foundation for hitter props.
#
# Free (statsapi) and pulled here rather than in a session because a
# Claude container cannot reach statsapi at all. ~500 hitters, one call
# each, a couple of minutes.
#
# Overwritten daily rather than appended: it is a full-season snapshot,
# not a time series, so there is nothing to accumulate.
#
# ⛔ Nothing here is a model. These are raw game logs. What gets built on
# top of them is DESCRIPTIVE evidence (a player's own record at a line)
# until a fitted, calibrated hitter model exists -- and only then may
# anything on this data carry a Gizmo's confidence number (ledger rule 55).
# ----------------------------------------------------------------------
HITTER_MIN_PA = 80


def collect_hitters():
    yr = now().year

    # One call gets the whole hitter pool ranked by plate appearances,
    # which is far cheaper than walking 30 rosters.
    pool, _ = get(
        f"{STATS}/stats?stats=season&group=hitting&season={yr}&gameType=R"
        f"&limit=700&sortStat=plateAppearances"
    )
    splits = (pool.get("stats") or [{}])[0].get("splits", []) if pool.get("stats") else []
    people = []
    for sp in splits:
        st, pl = sp.get("stat") or {}, sp.get("player") or {}
        pa = st.get("plateAppearances") or 0
        if pa >= HITTER_MIN_PA and pl.get("id"):
            people.append({"id": pl["id"], "name": pl.get("fullName"),
                           "pa": pa, "team": (sp.get("team") or {}).get("name")})
    log(f"hitter pool: {len(splits)} returned, {len(people)} with >= {HITTER_MIN_PA} PA")
    if not people:
        raise RuntimeError("hitter pool came back empty — endpoint or season wrong")

    # Handedness, in bulk. Needed for the platoon splits that make a
    # descriptive 'why' worth reading.
    hand = {}
    ids = [p["id"] for p in people]
    for i in range(0, len(ids), 100):
        chunk = ",".join(str(x) for x in ids[i:i + 100])
        try:
            d, _ = get(f"{STATS}/people?personIds={chunk}&fields=people,id,batSide,code")
            for pp in d.get("people", []):
                hand[pp["id"]] = (pp.get("batSide") or {}).get("code")
        except Exception as e:
            log(f"  handedness chunk {i}: {type(e).__name__}")

    logs, bad, empty = {}, 0, 0
    for p in people:
        try:
            d, _ = get(
                f"{STATS}/people/{p['id']}/stats?stats=gameLog&group=hitting"
                f"&season={yr}&gameType=R"
                "&fields=stats,splits,date,isHome,opponent,name,stat,"
                "atBats,hits,homeRuns,rbi,totalBases,runs,baseOnBalls,strikeOuts,plateAppearances"
            )
            sp = (d.get("stats") or [{}])[0].get("splits", []) if d.get("stats") else []
        except Exception as e:
            log(f"  {p['name']}: {type(e).__name__}")
            bad += 1
            continue
        if not sp:
            empty += 1
            continue
        rows = []
        for g in sp:
            st = g.get("stat") or {}
            rows.append({
                "d": g.get("date"),
                "o": (g.get("opponent") or {}).get("name"),
                "h": 1 if g.get("isHome") else 0,
                "ab": st.get("atBats"), "pa": st.get("plateAppearances"),
                "H": st.get("hits"), "hr": st.get("homeRuns"), "rbi": st.get("rbi"),
                "tb": st.get("totalBases"), "r": st.get("runs"),
                "bb": st.get("baseOnBalls"), "k": st.get("strikeOuts"),
            })
        logs[p["id"]] = {"name": p["name"], "team": p["team"],
                         "bats": hand.get(p["id"]), "pa": p["pa"], "g": rows}

    write(f"{LATEST}/hitters.json.gz", {
        "pulled_at": stamp(),
        "season": yr,
        "min_pa": HITTER_MIN_PA,
        "n_players": len(logs),
        "n_failed": bad,
        "n_empty": empty,
        "players": logs,
    }, compress=True)
    total = sum(len(v["g"]) for v in logs.values())
    log(f"hitters: {len(logs)} players, {total} game rows, {bad} failed, {empty} empty")
    return None


# ----------------------------------------------------------------------
# Final results — the grading feed. Free (statsapi) and the most important
# thing this collector does after the odds themselves.
#
# Grading is what makes the pick ledger worth anything, and a session
# cannot be relied on to reach statsapi itself: a direct probe from a
# Claude container on 2026-08-22 returned 403 for statsapi AND for the
# odds API. GitHub reachability is not in doubt. So results are pulled
# here, on a runner that definitely has network, and the grading session
# reads them out of the repo instead of fetching anything.
#
# Stored as a compact extract. The raw live feed is 1-3MB per game; what
# grading actually needs is a few dozen numbers.
#
# Includes each starter's SEASON line alongside his game line, because
# ledger rule 10's strong control is to sum a pitcher's whole game log
# against his season total -- that is what caught a fabricated "1.3 IP"
# on 2026-08-21. Storing both makes the control runnable offline.
# ----------------------------------------------------------------------
def outs_of(ip):
    """IP -> outs. Fractions are THIRDS: only .0, .1, .2 exist (rule 40)."""
    if ip is None:
        return None
    whole, _, frac = str(ip).partition(".")
    f = int(frac) if frac else 0
    if f not in (0, 1, 2):
        raise ValueError(f"impossible innings-pitched value: {ip!r}")
    return int(whole) * 3 + f


def et_slate_date(back=0):
    """The ET date of the slate that has finished.

    Run at 08:00Z that is 04:00 ET; the night's last games ended around
    02:00 ET, so stepping back 6 more hours lands on the right ET date.
    """
    from datetime import timedelta
    et = now() - timedelta(hours=4)
    return (et - timedelta(hours=6 + 24 * back)).strftime("%Y-%m-%d")


def collect_results():
    from datetime import timedelta

    # 🔴 THIS USED TO BE `for back in (0, 1)` — A FIXED TWO-DAY LOOKBACK,
    # AND IT MADE EVERY OUTAGE PERMANENT. When the scheduler dropped this
    # mode for three days (8/25–8/27, measured), those slates fell out of
    # the window and could never be graded by any later run: the track
    # record was not merely stale, it had a hole that would not close.
    #
    # ✅ It now walks FORWARD FROM THE LAST SLATE ON DISK, so any gap —
    # from a dropped cron, a failed run, or a week the repo sat idle —
    # heals itself on the next run. The 0/1 slates are always re-pulled on
    # top of that, because finals arrive late and suspended games resume.
    # ⚠️ Capped so a cold start cannot walk the whole season in one job.
    from datetime import datetime as _dt
    GAP_CAP = 14
    want, d0 = [], _dt.strptime(et_slate_date(0), "%Y-%m-%d")
    for back in range(GAP_CAP, -1, -1):
        day = et_slate_date(back)
        if back <= 1 or not os.path.exists(f"data/{day}/results/final.json.gz"):
            want.append(day)
    want = sorted(set(want))
    missing = [x for x in want if not os.path.exists(f"data/{x}/results/final.json.gz")]
    if missing:
        log(f"results: BACK-FILLING {len(missing)} missing slate(s): "
            f"{' '.join(missing)}")
    for d in want:
        sched, _ = get(
            f"{STATS}/schedule?sportId=1&date={d}&hydrate=linescore,team"
        )
        games = (sched.get("dates") or [{}])[0].get("games", []) if sched.get("dates") else []
        if not games:
            log(f"results {d}: no games")
            continue

        out, bad = [], 0
        for g in games:
            pk = g.get("gamePk")
            try:
                box, _ = get(f"{STATS}/game/{pk}/boxscore")
            except Exception as e:
                log(f"  gamePk {pk}: {type(e).__name__}")
                continue

            pitchers = []
            for side in ("away", "home"):
                team = box["teams"][side]
                for key, p in team.get("players", {}).items():
                    st = (p.get("stats") or {}).get("pitching") or {}
                    if not st:
                        continue
                    season = (p.get("seasonStats") or {}).get("pitching") or {}
                    try:
                        game_outs = outs_of(st.get("inningsPitched"))
                        season_outs = outs_of(season.get("inningsPitched"))
                    except ValueError as e:
                        # Domain violation = fabricated value until proven
                        # otherwise (ledger rule 40). Record it, do not drop it.
                        log(f"  DOMAIN VIOLATION gamePk {pk}: {e}")
                        bad += 1
                        game_outs = season_outs = None
                    pitchers.append({
                        "id": p["person"]["id"],
                        "name": p["person"]["fullName"],
                        "side": side,
                        "team": team["team"]["name"],
                        "started": (st.get("gamesStarted") or 0) > 0,
                        "ip": st.get("inningsPitched"),
                        "outs": game_outs,
                        "k": st.get("strikeOuts"),
                        "bb": st.get("baseOnBalls"),
                        "er": st.get("earnedRuns"),
                        "h": st.get("hits"),
                        "bf": st.get("battersFaced"),
                        "pitches": st.get("numberOfPitches") or st.get("pitchesThrown"),
                        # season line as of AFTER this game -- the rule-10 control
                        "season": {
                            "gs": season.get("gamesStarted"),
                            "ip": season.get("inningsPitched"),
                            "outs": season_outs,
                            "k": season.get("strikeOuts"),
                        },
                    })

            # Batters, from the SAME boxscore call -- free, and it is what
            # lets a hitter play be graded and a hitter model be backtested
            # later. Stored as the raw line; nothing here is derived.
            batters = []
            for side in ("away", "home"):
                team = box["teams"][side]
                for key, p in team.get("players", {}).items():
                    st = (p.get("stats") or {}).get("batting") or {}
                    if not st or st.get("atBats") is None:
                        continue
                    h = st.get("hits")
                    d2, t3, hr = st.get("doubles"), st.get("triples"), st.get("homeRuns")
                    tb = None
                    if None not in (h, d2, t3, hr):
                        tb = (h - d2 - t3 - hr) + 2 * d2 + 3 * t3 + 4 * hr
                    # 🔴 BATTING ORDER -- the input T29 named as the ONLY
                    # condition for reopening hitter modelling. statsapi
                    # gives it as "100", "200" ... for slots 1-9, with a
                    # trailing digit for substitutes who inherited the spot.
                    # Slot determines plate appearances, and plate
                    # appearances were the dominant, unforecastable term in
                    # every one of T27/T28/T29.
                    bo = p.get("battingOrder")
                    slot = sub = None
                    if bo:
                        try:
                            slot, sub = int(str(bo)[0]), int(str(bo)[1:] or 0)
                        except ValueError:
                            slot = sub = None
                    batters.append({
                        "id": p["person"]["id"],
                        "name": p["person"]["fullName"],
                        "side": side,
                        "team": team["team"]["name"],
                        "slot": slot, "sub": sub, "started": sub == 0,
                        "ab": st.get("atBats"), "H": h, "r": st.get("runs"),
                        "rbi": st.get("rbi"), "hr": hr, "d": d2, "t": t3,
                        "bb": st.get("baseOnBalls"), "k": st.get("strikeOuts"),
                        "tb": tb, "sb": st.get("stolenBases"),
                    })

            ls = g.get("linescore") or {}
            out.append({
                "gamePk": pk,
                "state": (g.get("status") or {}).get("detailedState"),
                "away": g["teams"]["away"]["team"]["name"],
                "home": g["teams"]["home"]["team"]["name"],
                "score": {
                    "away": (ls.get("teams", {}).get("away") or {}).get("runs"),
                    "home": (ls.get("teams", {}).get("home") or {}).get("runs"),
                },
                "innings": ls.get("currentInning"),
                "pitchers": pitchers,
                "batters": batters,
            })

        final = sum(1 for g in out if g["state"] == "Final")
        write(f"data/{d}/results/final.json.gz", {
            "pulled_at": stamp(),
            "slate_date": d,
            "n_games": len(out),
            "n_final": final,
            "domain_violations": bad,
            "games": out,
        }, compress=True)
        log(f"results {d}: {len(out)} games, {final} final, "
            f"{bad} domain violations")

    return None


# ----------------------------------------------------------------------
# The track record.
#
# Grades every published card against the stored results and writes one
# file the page reads. Free, no API call, and it runs nightly -- which is
# the whole point: the Track Record tab was hardcoded and went stale the
# day it shipped.
#
# 🔴 ONLY MACHINE CARDS ARE COUNTED. `picks/2026-08-22.json` is a JSON
# republication of that day's HAND-BUILT card, which is already graded in
# the ledger as TABLE A. Counting it here would double-count all 13 plays
# and mix a curated board in with an uncurated one -- two different
# populations that must never share a denominator. The machine card is
# identified by `kind == "gizmos-card"`, and TABLE M begins with 8/23.
# ----------------------------------------------------------------------
BATTER_RESULT = {
    "batter_hits":           lambda b: b.get("H"),
    "batter_total_bases":    lambda b: b.get("tb"),
    "batter_home_runs":      lambda b: b.get("hr"),
    "batter_rbis":           lambda b: b.get("rbi"),
    "batter_hits_runs_rbis": lambda b: None if b.get("H") is None else
                                       (b.get("H") or 0) + (b.get("r") or 0) + (b.get("rbi") or 0),
}


def _won(val, line, side):
    if val is None:
        return None
    return (val > line) if side == "over" else (val < line)


def collect_record():
    import glob

    days, skipped = [], []
    for f in sorted(glob.glob(f"{PICKS}/*.json")):
        try:
            card = json.load(open(f))
        except Exception as e:
            skipped.append((os.path.basename(f), f"unreadable: {type(e).__name__}"))
            continue
        date = card.get("date") or os.path.basename(f)[:-5]
        if card.get("kind") != "gizmos-card":
            skipped.append((date, "hand-built card, graded in the ledger as TABLE A"))
            continue
        rf = f"data/{date}/results/final.json.gz"
        if not os.path.exists(rf):
            skipped.append((date, "no results stored yet"))
            continue
        R = json.load(gzip.open(rf, "rt"))
        if R.get("n_final", 0) < R.get("n_games", 1):
            skipped.append((date, f"{R.get('n_final')}/{R.get('n_games')} games final -- not settled"))
            continue

        pit, bat = {}, {}
        for g in R["games"]:
            for p in g.get("pitchers") or []:
                if p.get("started"):
                    pit[p["id"]] = p
            for b in g.get("batters") or []:
                bat[b["id"]] = b

        rows = []
        for p in card.get("picks", []):
            mk, side, line = p.get("market"), p.get("side"), p.get("line")
            if mk in ("strikeouts", "outs"):
                a = pit.get(p.get("pid"))
                val = None if not a else (a["k"] if mk == "strikeouts" else a["outs"])
                kind = "pitcher"
            elif mk in BATTER_RESULT:
                a = bat.get(p.get("pid"))
                val = None if not a else BATTER_RESULT[mk](a)
                kind = "hitter"
            else:
                continue
            w = _won(val, line, side)
            # 🔴 A VOID IS NOT A LOSS AND IT IS NOT NOTHING.
            # ~~`if w is None: continue`~~ -- a player who never took the
            # field was dropped from the file entirely, so a reader
            # comparing the card to the record found a pick that had simply
            # vanished. At the book that is a VOID (usually a refund), and
            # on 2026-08-24 Ke'Bryan Hayes was exactly this. It is now
            # RECORDED with won=None and EXCLUDED FROM EVERY TALLY, so the
            # published percentages do not move by a hundredth.
            rows.append({"kind": kind, "market": mk, "side": side,
                         "line": line, "price": p.get("price"),
                         "blend": p.get("blend"), "band": p.get("band"),
                         "confidence": p.get("confidence"),
                         "confidence_basis": p.get("confidence_basis"),
                         "implied": p.get("break_even") or p.get("implied"),
                         "edge": p.get("edge"),
                         "won": None if w is None else bool(w),
                         "void": w is None,
                         "actual": val, "game": p.get("game"),
                         "market_label": p.get("market_label"),
                         "player": p.get("pitcher") or p.get("player")})

        pairs = []
        for q in card.get("pairs", []):
            legs = []
            for nm, ln in zip(q.get("legs", []), q.get("leg_keys", []) or []):
                legs.append(None)
            pairs.append(q)

        graded = [r for r in rows if r["won"] is not None]
        days.append({"date": date, "rows": rows, "graded": graded,
                     "n": len(graded), "w": sum(1 for r in graded if r["won"]),
                     "voids": sum(1 for r in rows if r["won"] is None)})

    def tally(rows):
        n = len(rows)
        return {"w": sum(1 for r in rows if r["won"]), "n": n,
                "pct": round(100 * sum(1 for r in rows if r["won"]) / n, 1) if n else None}

    # ⛔ TALLIES SEE GRADED ROWS ONLY. `rows` now carries voids too.
    allrows = [r for d in days for r in d["graded"]]
    buckets = {}
    for r in allrows:
        if r["kind"] != "pitcher" or r["blend"] is None:
            continue
        b = int(r["blend"] // 10) * 10
        buckets.setdefault(b, []).append(r)

    # 🔴 THE HAND-BUILT RECORD AND SAM'S BANKROLL WERE REMOVED FROM THE
    # DASHBOARD ON 2026-08-24, at Sam's instruction: the site tracks the
    # MODEL's record and nothing else.
    # ⚠️ THIS IS A DISPLAY CHANGE, NOT A DELETION. Both still live in
    # claude/pick-ledger.md and the 7:30am grading run still maintains
    # them. ⛔ Do not read this as permission to stop grading them.

    doc = {
        "built_at": stamp(),
        "kind": "DESCRIPTIVE",
        "note": ("Graded from stored results, not from anyone's memory. Machine cards "
                 "only -- the hand-built cards live in the ledger and are a different, "
                 "CURATED population that must never share a denominator with this one."),
        "overall": tally(allrows),
        "by_kind": {k: tally([r for r in allrows if r["kind"] == k])
                    for k in ("pitcher", "hitter")},
        "by_market": {m: tally([r for r in allrows if r["market"] == m])
                      for m in sorted({r["market"] for r in allrows})},
        "by_side": {sd: tally([r for r in allrows if r["side"] == sd])
                    for sd in ("over", "under")},
        "by_band": {b: tally([r for r in allrows if r["band"] == b])
                    for b in sorted({r["band"] for r in allrows if r.get("band")})},
        "calibration": [{"bucket": f"{b}-{b+10}%",
                         "predicted": round(sum(r["blend"] for r in v) / len(v), 1),
                         **tally(v)} for b, v in sorted(buckets.items())],
        "by_day": [{"date": d["date"], "w": d["w"], "n": d["n"],
                     "voids": d["voids"]} for d in days],
        # 🔴 THE PER-PICK DETAIL LIVES IN ITS OWN GZIPPED FILE.
        # Sam, 2026-08-26: he wants to click a day and see what hit and what
        # missed. Inlining ~50 rows a day here would push record.json past
        # 400KB by season's end, UNCOMPRESSED, on a tab that only needs the
        # totals to draw. So the totals stay here and the page fetches the
        # detail once, on demand, the first time somebody expands a day.
        "detail_file": f"{LATEST}/record-detail.json.gz",
        "days_graded": len(days),
        "skipped": [{"date": a, "why": b} for a, b in skipped],
    }
    write(f"{LATEST}/record.json", doc)
    write(f"{LATEST}/record-detail.json.gz",
          {"built_at": doc["built_at"], "kind": "DESCRIPTIVE",
           "note": ("Every published pick, graded from the stored box score. "
                    "`won` is null on a VOID -- a player who never took the "
                    "field -- and those are excluded from every percentage in "
                    "record.json."),
           "days": {d["date"]: d["rows"] for d in days}},
          compress=True)
    log(f"record: {len(days)} card(s) graded, {doc['overall']['w']}/{doc['overall']['n']} plays")
    for a, b in skipped:
        log(f"  skipped {a}: {b}")
    return None


# ----------------------------------------------------------------------
# LINEUP SLOT — the backfill.
#
# 🔴 This exists for one reason: T27, T28 and T29 all failed, and all three
# said the same thing — PLATE APPEARANCES dominate every hitter target and
# are themselves barely forecastable. Batting order is what determines
# plate appearances. T29's pre-registration named a NEW INPUT as the only
# condition for reopening hitter modelling, and this is that input.
#
# Free (statsapi), and RESUMABLE: it records which dates it has already
# done and skips them, so a run that times out loses nothing. The daily
# `results` job captures slot going forward; this recovers the season
# already played.
# ----------------------------------------------------------------------
def collect_weather():
    """Per-game TEMPERATURE and WIND -- the input T13b calls permanently blocked.

    🔴 T13b IN `claude/owed-tests.md` STATES: "NO HISTORICAL WEATHER SOURCE
    EXISTS IN THIS PROJECT'S STACK. Temperature and wind have never been
    tested, on any sample." It names exactly what would unblock it: "a
    per-game historical temperature and wind source joinable to the start
    table by (date, venue)." THIS IS AN ATTEMPT AT THAT SOURCE.

    ⛔ IT DOES NOT UNBLOCK T13b BY ITSELF. T13b requires a specification to
    be registered BEFORE anything is run, and it explicitly forbids
    substituting the roof/dome proxy and calling the result a weather
    finding. This mode only makes the DATA exist. The test stays blocked
    until a spec is written against it.

    Two sources, both free and keyless:
      venue coordinates  statsapi /venues?hydrate=location
      historical weather Open-Meteo archive (archive-api.open-meteo.com)

    🔴 THE PARTIAL-FILE CONTRACT, CORRECTED 2026-08-25 AFTER THE FIRST REAL
    RUN. This mode originally claimed it would "write NO partial file" on
    failure -- and then its own periodic checkpoint wrote one anyway, 8,288
    bytes, immediately before raising an error that said not to. The claim
    and the code disagreed, which is the exact failure this project has
    rules about.

    The contract is now the honest one: a partial file IS written, because
    it is RESUMABLE and the 8 venues already fetched are perfectly good.
    What must never happen is a MODEL silently fitting on incomplete
    weather. So the file carries `complete: true|false`, and any consumer
    MUST refuse to fit while it reads false. The guard moved from collect
    time to model time, which is where it always belonged.

    ⚠️ AND THE FIRST RUN DID NOT SHOW "UNREACHABLE". It showed 8 calls
    SUCCEEDING and then an SSL handshake timing out -- that is rate
    limiting, not a block. Retries with backoff and a polite delay between
    venues are therefore the fix, not a different data source.

    ⚠️ GAME TIME IS APPROXIMATED. The scores feed carries dayNight, not a
    first-pitch timestamp, so night games are read at 19:00 and day games
    at 13:00 LOCAL. That is an approximation and every consumer must be
    told so; it is recorded on the row as `hour_local` and `approx: true`.
    """
    import urllib.request, urllib.parse, collections, time

    spath = f"{LATEST}/scores.json.gz"
    if not os.path.exists(spath):
        raise RuntimeError("run `scores` before `weather` -- it names the venues and dates")
    S = json.load(gzip.open(spath, "rt"))
    if S.get("schema", 1) < 2:
        raise RuntimeError("scores.json.gz is schema 1 and carries no venue -- "
                           "re-run `scores` first")
    need = collections.defaultdict(set)          # venue_id -> {dates}
    vname = {}
    for d, rows in S["days"].items():
        for r in rows:
            if r.get("venue_id"):
                need[r["venue_id"]].add(d)
                vname[r["venue_id"]] = r.get("venue")
    if not need:
        raise RuntimeError("no venue ids in scores.json.gz -- nothing to fetch")
    log(f"weather: {len(need)} venues, "
        f"{sum(len(v) for v in need.values())} venue-days needed")

    # ---- venue coordinates, one batched call
    ids = ",".join(str(i) for i in sorted(need))
    coords = {}
    v, _ = get(f"{STATS}/venues?venueIds={ids}&hydrate=location")
    for x in v.get("venues", []):
        c = ((x.get("location") or {}).get("defaultCoordinates") or {})
        if c.get("latitude") is not None and c.get("longitude") is not None:
            coords[x["id"]] = (c["latitude"], c["longitude"])
    log(f"weather: {len(coords)}/{len(need)} venues have coordinates")
    missing = [vname.get(i, i) for i in need if i not in coords]
    if missing:
        log(f"weather: NO COORDINATES for {missing[:6]}")

    path = f"{LATEST}/weather.json.gz"
    store = {"schema": 1, "complete": False,
             "note": "hour is APPROXIMATE -- 19:00 local night, "
                     "13:00 local day; no first-pitch time in the feed",
             "consumer_contract": "REFUSE TO FIT A MODEL WHILE complete IS false. "
                                  "A half-populated weather column silently fits on "
                                  "whichever games happened to resolve.",
             "venues": {}}
    if os.path.exists(path):
        store = json.load(gzip.open(path, "rt"))
    done = fetched = 0
    for vid, dates in sorted(need.items()):
        if vid not in coords:
            continue
        key = str(vid)
        have = store["venues"].setdefault(key, {})
        want = sorted(d for d in dates if d not in have)
        if not want:
            continue
        lat, lon = coords[vid]
        q = urllib.parse.urlencode({
            "latitude": lat, "longitude": lon,
            "start_date": want[0], "end_date": want[-1],
            "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m",
            "temperature_unit": "fahrenheit", "wind_speed_unit": "mph",
            "timezone": "auto"})
        url = f"https://archive-api.open-meteo.com/v1/archive?{q}"
        # RETRY WITH BACKOFF. The first real run made 8 calls successfully and
        # then timed out on the SSL handshake -- the signature of rate
        # limiting, not of an unreachable host. A single-attempt fetch turned
        # a throttle into a fatal error and a wrong diagnosis.
        w = None
        for attempt, wait in enumerate((0, 3, 10, 30), start=1):
            if wait:
                log(f"  retry {attempt-1} for venue {vid} after {wait}s")
                time.sleep(wait)
            try:
                with urllib.request.urlopen(url, timeout=30) as resp:
                    w = json.loads(resp.read().decode())
                break
            except Exception as e:
                last = e
        if w is None:
            write(path, store, compress=True)     # keep what DID resolve -- it resumes
            raise RuntimeError(
                f"Open-Meteo failed for venue {vid} after 4 attempts "
                f"({type(last).__name__}: {last}). "
                f"{fetched} venue(s) DID fetch successfully this run, so the host is "
                f"reachable and this is most likely RATE LIMITING -- do not conclude "
                f"the source is unusable. The partial file is RESUMABLE and is marked "
                f"complete:false; re-run this mode to continue from where it stopped.")
        fetched += 1
        time.sleep(1.5)          # be a good citizen; the archive is free
        if w.get("elevation") is not None:
            store.setdefault("elevations", {})[str(vid)] = w["elevation"]
        H = w.get("hourly") or {}
        times = H.get("time") or []
        idx = {t: i for i, t in enumerate(times)}
        for d in want:
            for hh in ("19:00", "13:00"):
                i = idx.get(f"{d}T{hh}")
                if i is None:
                    continue
                have.setdefault(d, {})[hh[:2]] = {
                    "temp_f": (H.get("temperature_2m") or [None])[i],
                    "wind_mph": (H.get("wind_speed_10m") or [None])[i],
                    "wind_dir": (H.get("wind_direction_10m") or [None])[i]}
        done += 1
        if done % 8 == 0:
            write(path, store, compress=True)
            log(f"  ... {done} venues, {fetched} calls")

    # ---- ELEVATION TOP-UP.
    # Elevation is the PUREST air-density variable there is -- Coors sits a
    # mile up, and that is why the Rockies keep game balls in a humidor. It
    # comes back on every Open-Meteo response and the first version of this
    # mode simply did not store it. Venues whose weather is already complete
    # never re-enter the loop above, so they are topped up here with a
    # minimal one-day query rather than by refetching a season of hours.
    store.setdefault("elevations", {})
    todo_el = [v for v in coords if str(v) not in store["elevations"]]
    if todo_el:
        log(f"weather: {len(todo_el)} venue(s) need an elevation top-up")
    for vid in todo_el:
        lat, lon = coords[vid]
        d0 = sorted(need[vid])[0]
        q = urllib.parse.urlencode({"latitude": lat, "longitude": lon,
                                    "start_date": d0, "end_date": d0,
                                    "daily": "temperature_2m_max", "timezone": "auto"})
        got = None
        for attempt, wait in enumerate((0, 3, 10, 30), start=1):
            if wait:
                log(f"  elevation retry {attempt-1} for venue {vid} after {wait}s")
                time.sleep(wait)
            try:
                with urllib.request.urlopen(
                        f"https://archive-api.open-meteo.com/v1/archive?{q}", timeout=30) as r:
                    got = json.loads(r.read().decode())
                break
            except Exception as e:
                last = e
        if got is None:
            write(path, store, compress=True)
            raise RuntimeError(
                f"Open-Meteo failed on the elevation top-up for venue {vid} "
                f"({type(last).__name__}: {last}). The weather HISTORY is unaffected "
                f"and still stored; re-run this mode to finish the elevations.")
        if got.get("elevation") is not None:
            store["elevations"][str(vid)] = got["elevation"]
        time.sleep(1.5)
    if store["elevations"]:
        els = list(store["elevations"].values())
        log(f"weather: elevations for {len(els)} venues, "
            f"{min(els):.0f}m to {max(els):.0f}m "
            f"(Coors Field should be the high one, ~1580m)")

    outstanding = sum(1 for vid, dates in need.items() if vid in coords
                      for d in dates if d not in store["venues"].get(str(vid), {}))
    outstanding += sum(1 for v in coords if str(v) not in store["elevations"])
    store["complete"] = (outstanding == 0)
    write(path, store, compress=True)
    nd = sum(len(v) for v in store["venues"].values())
    log(f"weather: {len(store['venues'])} venues, {nd} venue-days, {fetched} API calls")
    log(f"weather: complete={store['complete']}"
        + ("" if store["complete"] else f" -- {outstanding} venue-days still missing, RE-RUN this mode"))
    if nd == 0:
        raise RuntimeError("no weather rows written -- do NOT proceed to a model")
    temps = [h["temp_f"] for v in store["venues"].values() for d in v.values()
             for h in d.values() if h.get("temp_f") is not None]
    if temps:
        log(f"weather: mean temperature {sum(temps)/len(temps):.1f}F "
            f"(a sane MLB season reads roughly 65-80F)")
    return None


def collect_scores():
    """Season-long per-game TEAM RUNS -- the foundation Phase 3 needs.

    WHY THIS EXISTS. Team runs were reconstructable from the hitter logs by
    summing each player's `r`, and it looked usable. Measured against 90
    team-games with a real final: it captures 91.0% of runs, mean error
    -0.378 per team-game, and IT NEVER OVERCOUNTS. That is the signature of
    a hitter pool that does not contain every batter who scored -- bench
    bats and callups fall out. A run model fitted on it would sit low, and
    the bias tracks how much a team uses its bench, which is a slope you
    would mistake for a finding. So the real scores are pulled instead.

    One call per DATE, not per game: the schedule endpoint carries the score
    already. That makes this far cheaper than the lineups backfill was.
    Resumable, like lineups -- a stored date is never re-fetched.
    """
    from datetime import date, timedelta
    path = f"{LATEST}/scores.json.gz"
    # SCHEMA VERSION. v1 stored scores only. v2 adds venue, gameType and
    # dayNight -- park is the biggest single input a total model can have and
    # it was in the same response all along. A cache written by an older
    # schema is DISCARDED and refetched, because a resumable collector that
    # skips stored dates would otherwise keep the thin rows forever and the
    # gap would be discovered later as "why is venue null before August".
    SCHEMA = 2
    store = {"season": now().year, "schema": SCHEMA, "days": {}}
    if os.path.exists(path):
        old = json.load(gzip.open(path, "rt"))
        if old.get("schema") == SCHEMA:
            store = old
        else:
            log(f"scores: cache is schema {old.get('schema', 1)}, need {SCHEMA}"
                f" -- refetching all {len(old.get('days', {}))} dates")
    days = store["days"]

    yr = now().year
    start = date(yr, 3, 1)
    end = (now() - timedelta(hours=4)).date() - timedelta(days=1)
    todo = []
    d = start
    while d <= end:
        k = d.isoformat()
        if k not in days:
            todo.append(k)
        d += timedelta(days=1)
    log(f"scores: {len(days)} dates already stored, {len(todo)} to fetch")

    done = viol = 0
    for k in todo:
        try:
            sched, _ = get(f"{STATS}/schedule?sportId=1&date={k}"
                           "&fields=dates,games,gamePk,status,detailedState,"
                           "teams,away,home,team,name,score,isTie,doubleHeader,"
                           "venue,id,gameType,dayNight,officialDate")
        except Exception as e:
            log(f"  {k}: schedule {type(e).__name__} -- stopping, will resume")
            break
        blocks = sched.get("dates") or []
        games = blocks[0].get("games", []) if blocks else []
        rows = []
        for g in games:
            if (g.get("status") or {}).get("detailedState") != "Final":
                continue
            t = g.get("teams") or {}
            a, h = t.get("away") or {}, t.get("home") or {}
            ar, hr = a.get("score"), h.get("score")
            an = ((a.get("team") or {}).get("name"))
            hn = ((h.get("team") or {}).get("name"))
            # DOMAIN CHECK. A Final game has two integer scores, both >= 0.
            # Anything else is fabricated data and is DROPPED, not coerced.
            # (`1.3 innings pitched` taught this project that a plausible
            # shape is not the same thing as a valid value.)
            if not (isinstance(ar, int) and isinstance(hr, int)
                    and ar >= 0 and hr >= 0 and an and hn):
                viol += 1
                continue
            v = g.get("venue") or {}
            rows.append({"gamePk": g.get("gamePk"), "away": an, "home": hn,
                         "away_r": ar, "home_r": hr,
                         # PARK is the single largest cheap input a total
                         # model can have -- Coors against Petco is worth
                         # about two runs -- and it was sitting in this same
                         # response all along. gameType filters spring
                         # training ('S') from the regular season ('R')
                         # DIRECTLY, which is stronger than deriving opening
                         # day from another file. dayNight is a real run
                         # environment split.
                         "venue_id": v.get("id"), "venue": v.get("name"),
                         "gameType": g.get("gameType"),
                         "dayNight": g.get("dayNight")})
        days[k] = rows
        done += 1
        if done % 15 == 0:
            write(path, store, compress=True)
            log(f"  ... {done}/{len(todo)} dates")

    write(path, store, compress=True)
    tot = sum(len(v) for v in days.values())
    runs = sum(r["away_r"] + r["home_r"] for v in days.values() for r in v)
    log(f"scores: {len(days)} dates, {tot} games, {runs} total runs stored")
    if viol:
        log(f"scores: {viol} Final game(s) DROPPED for failing the domain check")
    if tot:
        log(f"scores: mean {runs/tot/2:.2f} runs per team-game")
    # Fail LOUD if the backfill recovered nothing, exactly as lineups does.
    # A silent empty file would be discovered later as "Phase 3 has no data",
    # which is the expensive way to learn it.
    if len(days) > 5 and tot == 0:
        raise RuntimeError("no finals recovered across many dates -- the schedule "
                           "endpoint may not expose `score` in this field set; "
                           "do NOT proceed to a model")
    return None


def collect_lineups():
    from datetime import date, timedelta
    path = f"{LATEST}/lineups.json.gz"
    store = {"season": now().year, "days": {}}
    if os.path.exists(path):
        store = json.load(gzip.open(path, "rt"))
    days = store["days"]

    yr = now().year
    start = date(yr, 3, 1)
    end = (now() - timedelta(hours=4)).date() - timedelta(days=1)
    todo = []
    d = start
    while d <= end:
        k = d.isoformat()
        if k not in days:
            todo.append(k)
        d += timedelta(days=1)
    log(f"lineups: {len(days)} dates already stored, {len(todo)} to fetch")

    done = fetched = 0
    for k in todo:
        try:
            sched, _ = get(f"{STATS}/schedule?sportId=1&date={k}"
                           "&fields=dates,games,gamePk,status,detailedState,teams,away,home,team,name")
        except Exception as e:
            log(f"  {k}: schedule {type(e).__name__}"); break
        games = (sched.get("dates") or [{}])[0].get("games", []) if sched.get("dates") else []
        rows = []
        for g in games:
            if (g.get("status") or {}).get("detailedState") != "Final":
                continue
            try:
                box, _ = get(f"{STATS}/game/{g['gamePk']}/boxscore")
            except Exception as e:
                log(f"  gamePk {g['gamePk']}: {type(e).__name__}")
                continue
            fetched += 1
            for side in ("away", "home"):
                t = box["teams"][side]
                opp = box["teams"]["home" if side == "away" else "away"]["team"]["name"]
                for _pk, pl in t.get("players", {}).items():
                    bo = pl.get("battingOrder")
                    if not bo:
                        continue
                    try:
                        slot, sub = int(str(bo)[0]), int(str(bo)[1:] or 0)
                    except ValueError:
                        continue
                    rows.append({"pid": pl["person"]["id"], "team": t["team"]["name"],
                                 "opp": opp, "slot": slot, "sub": sub,
                                 "started": 1 if sub == 0 else 0})
        days[k] = rows
        done += 1
        if done % 15 == 0:
            write(path, store, compress=True)
            log(f"  ...{done}/{len(todo)} dates, {fetched} boxscores")

    write(path, store, compress=True)
    n = sum(len(v) for v in days.values())
    withslot = sum(1 for v in days.values() for r in v if r["slot"])
    log(f"lineups: {len(days)} dates, {n} batter-games, {withslot} with a slot")
    if n == 0:
        raise RuntimeError("no batting orders recovered -- statsapi may not expose "
                           "battingOrder on this endpoint; do NOT proceed to a model")
    return None


def run_mode(mode):
    """Run ONE mode. Raises on failure; `main` decides what that means."""

    # The free modes touch statsapi or the repo only. `card` calls nothing
    # at all -- it reads what is already on disk -- so it must not be gated
    # on a key it does not use.
    FREE = ("schedule", "results", "hitters", "news", "props-board", "pitchers",
            "card", "record", "refresh", "lineups", "scores", "weather",
            "nfl-probe", "nfl-logs", "freshness", "cfb-probe", "news-probe",
            "card-fb", "nfl-teams", "cfb-teams")
    if mode not in FREE and not ODDS_KEY:
        log("FATAL: ODDS_API_KEY is not set. Add it as a repository secret.")
        sys.exit(1)

    try:
        if mode == "gamelines":
            left = collect_gamelines()
        elif mode == "props-pitcher":
            # ⚠️ NOT REGIONS_FULL unconditionally any more -- see
            # props_regions(kind). Both regions once a day, Hard Rock the
            # rest. ⛔ THE ARGUMENT IS LOAD-BEARING -- see the docstring.
            left = collect_props("pitcher", props_regions("pitcher"))
        elif mode == "props-batter":
            left = collect_props("batter", props_regions("batter"))
        elif mode == "props-player":
            # 🔴 FOOTBALL. One `player` kind -- football has no
            # pitcher/batter split and inventing one would be a fake
            # distinction for the sake of reusing a mode name.
            if LEAGUE == "mlb":
                log("FATAL: props-player is a FOOTBALL mode. Set LEAGUE.")
                sys.exit(1)
            left = collect_props("player", props_regions("player"))
            # 🔴 JOIN IT IMMEDIATELY. A pull that is never joined is a
            # pull that was wasted, and odds history cannot be re-bought.
            # ⛔ A join failure must NOT lose the snapshot that was just
            # paid for -- it is already on disk and committed.
            try:
                collect_props_board_fb()
            except Exception as _pe:
                log(f"  props board FAILED: {type(_pe).__name__}: {_pe}")
                log("  ⚠️ the snapshot is safe on disk; the board can be rebuilt")
            # 🔴 AND CARD IT, in its own try for the same reason. ⛔ A card
            # failure must not lose the paid snapshot OR the board built
            # from it -- both are already on disk by this point.
            try:
                build_card_fb()
            except Exception as _ce:
                log(f"  football card FAILED: {type(_ce).__name__}: {_ce}")
                log("  ⚠️ the board is safe; the card can be rebuilt")
        # The cheap refreshes. Hard Rock's region only, half the price.
        # Same storage directory as the full pull -- the stored file
        # records which regions it used, so the two never get confused.
        elif mode == "props-pitcher-hr":
            left = collect_props("pitcher", REGIONS_CHEAP)
        elif mode == "props-batter-hr":
            left = collect_props("batter", REGIONS_CHEAP)
        elif mode == "schedule":
            left = collect_schedule()
        elif mode == "results":
            left = collect_results()
        elif mode == "hitters":
            left = collect_hitters()
        elif mode == "news":
            left = collect_news()
        elif mode == "nfl-teams":
            # ⛔ FREE -- no API call at all, it writes a static directory.
            # ⚠️ The PAGE no longer depends on this file (the NFL map is
            # embedded in index.html), so this is a convenience artifact
            # only. Kept so the data is inspectable on disk.
            left = build_nfl_teams()
        elif mode == "cfb-teams":
            # 🔴 FREE (CFBD), and it is what puts college logos on the
            # page. ⛔ It used to run ONLY inside a full season rebuild,
            # so the file never existed and every college logo fell back
            # to text. It is its own mode now, and converge calls it.
            import cfb as _cfb
            _cfb.fbs_conferences(_fresh.current_football_season(), log)
            left = None
        elif mode == "card-fb":
            # ⛔ FREE -- it reads the board already on disk and computes.
            left = build_card_fb()
        elif mode == "news-probe":
            # 🔴 FREE, and it WRITES NO news.json. It writes a report for a
            # human to read. ⛔ Do not chain it into `news`.
            left = probe_news(LEAGUE)
        elif mode == "pitchers":
            left = collect_pitchers()
        elif mode == "refresh":
            # Fired automatically after any push that changes the code.
            # 🔴 FREE MODES ONLY -- no API call, no credits. A push must
            # never be able to spend money, or a busy evening of small
            # fixes could quietly drain the month's allowance.
            # ⛔ It cannot loop: the push trigger is filtered to the three
            # source files, and this job only ever commits data/ and
            # picks/, which are not in that filter.
            collect_props_board()
            import card as _card
            _card.main()
            collect_record()
            left = None
        elif mode == "lineups":
            collect_lineups()
            left = None
        elif mode == "scores":
            collect_scores()
            left = None
        elif mode == "weather":
            collect_weather()
            left = None
        elif mode == "record":
            collect_record()
            left = None
        elif mode == "card":
            # Rebuild the board FIRST, from the snapshots already on disk.
            # Free -- no API call. The card is only ever as current as the
            # join it reads, and the committed board may have been built by
            # an older revision of this file. Making the card mode
            # self-sufficient means it can never silently price off a stale
            # or differently-shaped join.
            collect_props_board()
            import card as _card
            _card.main()
            left = None
        elif mode == "props":
            # 🔴 THE FOOTBALL PROPS PULL. ⛔ MLB must not use this -- it has
            # its own two-mode split and a props-board join that assumes it.
            if LEAGUE not in PROP_MARKETS:
                log(f"FATAL: no prop market list for league '{LEAGUE}'. "
                    f"Known: {sorted(PROP_MARKETS)}")
                sys.exit(1)
            left = collect_props("player")
        elif mode == "freshness":
            # 🔴 REPUBLISH THE REPORT AGAINST WHAT IS ON DISK RIGHT NOW.
            # Called by the workflow AFTER verify_card has had its say, so
            # a reverted card is described as reverted.
            write_freshness()
            left = None
        elif mode == "props-board":
            left = collect_props_board()
        elif mode == "nfl-logs":
            # 🔴 FREE. nflverse publishes flat files on GitHub; no key, no
            # credits. ⚠️ 2026 stat files appear only once week 1 is played,
            # so a season with nothing yet is NOT an error -- it is skipped
            # and said out loud.
            import nfl as _nfl
            # 🔴 SEASON TAKES A RANGE OR A LIST. The point of this mode is a
            # HISTORY, and dispatching once per year by hand is how a
            # back-fill ends up missing a season nobody notices.
            #   SEASON=2025  ·  SEASON=2021-2025  ·  SEASON=2019,2021
            raw = os.environ.get("SEASON", "2025").strip()
            if "-" in raw:
                _a, _b = raw.split("-", 1)
                seasons = list(range(int(_a), int(_b) + 1))
            else:
                seasons = [int(x) for x in raw.replace(" ", "").split(",") if x]
            log(f"back-filling seasons: {seasons}")
            # ⛔ LEAGUES["nfl"] EXPLICITLY, not the ambient LATEST. Belt and
            # braces with the MODE_LEAGUE forcing above.
            base = LEAGUES["nfl"]["data"] + "/latest"
            # 🔴 ONE BAD SEASON MUST NOT DESTROY THE WHOLE BACK-FILL.
            # `[measured 2026-08-28, run #204]` `SEASON=2021-2025` failed and
            # wrote NOTHING AT ALL -- not even the seasons that had already
            # succeeded -- because this loop had no error handling.
            # ⛔ nflverse's file naming is irregular across years, so an
            # older season failing while a recent one works is the EXPECTED
            # case, not a surprise.
            # ✅ Same deferred-failure rule as the paid props pull:
            # everything that CAN land, lands; the failures are named; the
            # run still goes red at the end.
            done, failed, not_yet = [], [], []
            for season in seasons:
                try:
                    doc = _nfl.build_logs(season, log)
                    doc["pulled_at"] = stamp()
                    write(f"{base}/players-{season}.json.gz", doc,
                          compress=True)
                    # 🔴 THE MATCHUP TABLES COME FROM THE SAME PULL that made
                    # the logs, so the two can never disagree about a depth
                    # slot. ⛔ Do not split this into a second mode that
                    # reads the file back -- that is how two copies of one
                    # number drift apart.
                    vs = _nfl.build_vs_position(doc, log)
                    vs["pulled_at"] = stamp()
                    write(f"{base}/vs-position-{season}.json.gz", vs,
                          compress=True)
                    # 🔴 SAME PULL AGAIN, SAME REASON. The defensive
                    # tracking table Sam asked for on 2026-08-30 is built
                    # from the doc already in memory, never by reading a
                    # file back -- that is how two copies of one number
                    # drift apart.
                    al = _nfl.build_side(doc, "def", log)
                    al["pulled_at"] = stamp()
                    write(f"{base}/allowed-by-position-{season}.json.gz", al,
                          compress=True)
                    # 🔴 THE OFFENSIVE BOARD, FROM THE SAME DOC. Sam,
                    # 2026-09-01: "an offensive side of trends ... is a
                    # necessity just like the defensive one we have".
                    # ⛔ Same function, different grouping key -- never a
                    # second aggregator.
                    off = _nfl.build_side(doc, "off", log)
                    off["pulled_at"] = stamp()
                    write(f"{base}/offense-by-position-{season}.json.gz", off,
                          compress=True)
                    # 🔴 ROUTE PARTICIPATION — Sam's item 2. PROBE-FIRST:
                    # it writes the table ONLY if the columns are what we
                    # expect AND the join clears 80%. ⚠️ Tonight's CFB
                    # target parse scored 53% against the same style of
                    # bar and was killed by a format nobody had read; the
                    # identical risk lives here.
                    # ⛔ THE REPORT IS ALWAYS WRITTEN, pass or fail --
                    # a diagnosis that only exists in an Actions log is a
                    # diagnosis you do not have.
                    try:
                        _rt, _rrep = _nfl.build_routes(season, None, log)
                    except Exception as _re_:
                        _rt, _rrep = None, {"season": season,
                                            "kind": "DIAGNOSTIC",
                                            "usable": False,
                                            "error": f"{type(_re_).__name__}: {_re_}"}
                    write(f"{base}/routes-probe-{season}.json", _rrep)
                    if _rt:
                        _rt["pulled_at"] = stamp()
                        write(f"{base}/routes-{season}.json.gz", _rt,
                              compress=True)

                    # ── T48: DEFENSIVE EPA PER PLAY ──────────────────
                    # 🔴 THIS IS THE MEASURE T42 NAMED, NOT A SIXTH
                    # BOX-SCORE CONSTRUCT. T42 and T43 between them put
                    # five NFL defensive measures below the 0.35 bar and
                    # pre-committed the consequence: the NFL layer needs
                    # an EPA- or DVOA-style rating, "not another
                    # aggregate of the data we already hold."
                    # ✅ It is FREE and it is already downloaded -- the
                    # same `play_by_play_{y}` build_routes just used for
                    # its pass flag. ⚠️ No new source, no new cost.
                    # ⛔ THE REPORT IS ALWAYS WRITTEN, pass or fail.
                    try:
                        _ep, _erep = _nfl.build_def_epa(season, None, log)
                    except Exception as _ee_:
                        _ep, _erep = None, {"season": season,
                                            "kind": "DIAGNOSTIC",
                                            "usable": False, "test": "T48",
                                            "error": f"{type(_ee_).__name__}: {_ee_}"}
                    write(f"{base}/def-epa-probe-{season}.json", _erep)
                    if _ep:
                        _ep["pulled_at"] = stamp()
                        write(f"{base}/def-epa-{season}.json.gz", _ep,
                              compress=True)

                    done.append(season)
                except _nfl.SeasonNotStarted as _e:
                    # 🔴 THE SOURCE HAS NOTHING FOR THIS YEAR. If it is the
                    # CURRENT season, the season simply has not happened
                    # yet and there is nothing to collect -- that is a
                    # STATUS, not a failure. ⛔ Any OTHER year is still
                    # fatal: somebody asked for a season that should
                    # exist, and forgiving that would hide a real break.
                    if season == _fresh.current_football_season():
                        not_yet.append((season, f"{_e}"))
                        log(f"SEASON {season} NOT YET PUBLISHED — the "
                            f"season has not started. Not a failure.")
                    else:
                        failed.append((season, f"SeasonNotStarted: {_e}"))
                        log(f"SEASON {season} FAILED: the source has "
                            f"nothing for a season that is NOT current")
                    log("  continuing with the remaining seasons")
                except Exception as _e:
                    failed.append((season, f"{type(_e).__name__}: {_e}"))
                    log(f"SEASON {season} FAILED: {type(_e).__name__}: {_e}")
                    log("  continuing with the remaining seasons")

            # ══════════════════════════════════════════════════════
            # 🔴 THE SCHEDULE IS BUILT SEPARATELY, AND THAT IS THE WHOLE
            # POINT. `[measured 2026-09-02]` it was first written INSIDE
            # the per-season try above -- the one that begins with
            # `build_logs`. For 2026 `build_logs` raises SeasonNotStarted
            # on its FIRST LINE, so the schedule was never attempted, and
            # the run produced NO schedule for the one season we need it
            # for. ⛔ THE COLLEGE RUN SUCCEEDED AND THE NFL RUN DID NOT,
            # for no reason other than where the call sat.
            # ✅ THE SCHEDULE HAS NO DEPENDENCY ON PLAYER LOGS. It comes
            # from `games.csv.gz`, a DIFFERENT file that is not
            # year-partitioned -- which is exactly why a 2026 schedule
            # can exist months before a 2026 stat line does.
            # ⚠️ Coupling two independent things because they happened to
            # want the same loop is the defect; the fix is the loop.
            # ══════════════════════════════════════════════════════
            for season in seasons:
                try:
                    _sc, _srep = _nfl.build_schedule(season, None, log)
                except Exception as _se_:
                    _sc, _srep = None, {"season": season,
                                        "kind": "DIAGNOSTIC",
                                        "usable": False,
                                        "error": f"{type(_se_).__name__}: {_se_}"}
                # ⛔ REPORT ALWAYS WRITTEN, pass or fail.
                write(f"{base}/schedule-probe-{season}.json", _srep)
                if _sc:
                    _sc["pulled_at"] = stamp()
                    write(f"{base}/schedule-{season}.json.gz", _sc,
                          compress=True)
                    log(f"  schedule {season}: {_srep.get('games')} games, "
                        f"{_srep.get('final')} final")

            log("=" * 60)
            log(f"BACK-FILL RESULT: {len(done)} season(s) written "
                f"{done or '(none)'}")
            for _yr, _why in not_yet:
                log(f"  NOT YET PUBLISHED {_yr}: {_why}")
            for _yr, _why in failed:
                log(f"  FAILED {_yr}: {_why}")
            log("=" * 60)

            # 🔴 THE REASON LANDS IN THE REPO, NOT ONLY IN A LOG.
            # An Actions log cannot be read from outside the runner and
            # GitHub deletes it. A diagnosis you cannot retrieve is a
            # diagnosis you do not have -- same rule as
            # card-verify-failure.txt.
            os.makedirs(base, exist_ok=True)
            _rp = f"{base}/backfill-report.txt"
            with open(_rp, "w", encoding="utf-8") as _fh:
                _fh.write(f"nfl-logs back-fill at {stamp()}\n")
                _fh.write(f"requested: {seasons}\n")
                _fh.write(f"written  : {done}\n")
                _fh.write(f"failed   : {[y for y, _ in failed]}\n")
                # ⚠️ REPORTED, NOT SUPPRESSED. A season the source has no
                # data for yet gets its own STATUS line, so the artifact
                # says why it is empty instead of just being empty.
                _fh.write(f"not yet  : {[y for y, _ in not_yet]}"
                          f"   (season not started — not a failure)\n\n")
                for _yr, _why in not_yet:
                    _fh.write(f"--- {_yr} NOT YET PUBLISHED ---\n{_why}\n\n")
                for _yr, _why in failed:
                    _fh.write(f"--- {_yr} ---\n{_why}\n\n")
            log(f"wrote {_rp}")

            if failed:
                raise RuntimeError(
                    f"{len(failed)} season(s) failed: "
                    f"{[y for y, _ in failed]} -- see {_rp}")
            left = None
        elif mode == "cfb-probe":
            # 🔴 A PARITY CHECK, NOT A SURVEY. Sam, 2026-08-30: "i want the
            # SAME EXACT stats and data pulled for cfb as we did for the
            # nfl." So it asks, field by field, whether CFBD can supply
            # each of the 29 the NFL layer produces -- and NAMES THE GAPS.
            # 🔴 THE NAME IS STALE AND THE COMMENT WAS FALSE.
            # `[corrected 2026-09-01]` this said "Writes nothing. No CFB
            # collector exists yet, on purpose." ⛔ `cfb.probe()` HAS
            # back-filled and written the whole CFB board set since
            # 2026-08-30 — probe, back-fill and verify in one dispatch,
            # reading SEASON from the environment.
            # ⚠️ A comment claiming behaviour the code does not have is
            # the same defect that let `_rows` promise it would never
            # take the `old` participation file. Fixed in place rather
            # than renamed, because the mode name is in the workflow.
            import cfb as _cfb
            if not _cfb.probe(log):
                sys.exit(1)
            left = None
        elif mode == "nfl-probe":
            # 🔴 ASKS THE SOURCE WHAT IT PUBLISHES AND WRITES NOTHING.
            # The Claude container may not fetch URLs, so every nflverse
            # path was written from documentation. This confirms them on
            # the runner BEFORE a collector is scheduled against a guess.
            import nfl as _nfl
            if not _nfl.probe(log):
                log("PROBE FOUND PROBLEMS -- see above. Nothing scheduled yet.")
                sys.exit(1)
            left = None
        else:
            log(f"unknown mode: {mode}")
            sys.exit(1)

        if left is not None and left < RESERVE:
            log(f"WARNING: {left} credits remaining, below reserve of {RESERVE}.")

    except Exception as e:
        log(f"ERROR in {mode}: {type(e).__name__}: {e}")
        raise


# ======================================================================
# CONVERGE — the thing that replaced "one cron owns one artifact"
# ======================================================================
# 🔴 READ `freshness.py` FIRST. The short version: GitHub drops most
# scheduled runs, so a design where a dropped cron means a missing
# artifact will keep producing a stale site forever. Under converge, a
# dropped cron costs LATENCY AND NOTHING ELSE, because the NEXT run of
# ANY kind rebuilds whatever is late.
#
# ⛔ THIS IS WHY EVERY MODE NOW CONVERGES FIRST. A `gamelines` run that
# also rebuilds the card is not a bug, it is the entire mechanism.

def _record_failure(failed, soft_failed, mode, why):
    """A SOFT mode's failure is reported and survived; everything else
    turns the run red. ⛔ See freshness.SOFT for what may be lost."""
    if mode in _fresh.SOFT:
        log(f"WARNING: {mode} failed ({why}). It is a SOFT artifact — the "
            f"run continues and the page will show it as late.")
        soft_failed.append((mode, why))
    else:
        failed.append((mode, why))


def write_freshness(rows=None, still=None):
    """Publish the freshness report the PAGE reads.

    🔴 THIS MUST RUN AFTER THE CARD REVERT, NOT BEFORE, AND THAT IS THE
    WHOLE REASON IT IS A SEPARATE FUNCTION.
    `[measured 2026-08-29]` converge wrote this report while the freshly
    built card was still on disk, and only afterwards did `verify_card`
    fail and `git checkout -- picks/` throw that card away. So the report
    said **card age 0.0m, stale=false** while the PUBLISHED card was five
    hours old.
    ⛔ THAT IS THE SILENT-STALENESS FAILURE THIS ENTIRE SYSTEM EXISTS TO
    PREVENT, REINTRODUCED BY MY OWN REVERT MECHANISM. The page looked
    perfectly healthy while serving a card nobody had published.
    ➡️ The workflow now calls this again after the revert, so the report
    describes what is ACTUALLY on disk rather than what was there a
    moment earlier.
    """
    rows = rows if rows is not None else _fresh.survey(data=DATA, picks=PICKS)
    still = still if still is not None else [r["mode"] for r in rows
                                             if r["stale"]]
    # 🔴 "LATE" AND "REFUSED TO PUBLISH" ARE DIFFERENT THINGS AND THE PAGE
    # MUST NOT CONFLATE THEM. `[measured 2026-08-29]` the card sat 140
    # minutes past its 10:00 deadline because `verify_card` was FAILING it
    # every pass -- and the banner said only "has not updated on
    # schedule", which reads like slowness. ⛔ A reader who is told the
    # machine is slow behaves differently from one told the card did not
    # pass its own checks. The second is the more important fact.
    # 🔴 A CARD THAT IS CURRENT WAS NOT BLOCKED, WHATEVER THE FILE SAYS.
    # `[measured 2026-08-29 23:27Z]` verify_card started PASSING again, the
    # card published, and `freshness.json` still carried a `card_blocked`
    # message read a moment earlier — so the page told readers it was
    # "showing an earlier version" while showing the current one.
    # ⛔ A FALSE ALARM IS THE ONE THING THIS BANNER CANNOT AFFORD. It is
    # the only channel the site has for admitting it is wrong; if it cries
    # wolf it stops being read, and then a REAL stale card goes unnoticed.
    # ✅ The failure file is now evidence, not proof: it only counts when
    # the card is ALSO actually past due.
    _card_stale = any(r["mode"] == "card" and r["stale"] for r in rows)
    _blocked = None
    _bp = f"{LATEST}/card-verify-failure.txt"
    if _card_stale and os.path.exists(_bp):
        try:
            with open(_bp, encoding="utf-8") as _fh:
                _txt = _fh.read()
            _fails = [l.strip() for l in _txt.splitlines()
                      if l.strip().startswith("FAILURES:")]
            _blocked = (_fails[0][9:].strip() if _fails
                        else _txt.splitlines()[0])
        except Exception:
            _blocked = "the card did not pass its own checks"

    write(f"{LATEST}/freshness.json", {
        "built_at": stamp(),
        "kind": "DESCRIPTIVE",
        "card_blocked": _blocked,
        "note": "How old every artifact on this site is, and how old it is "
                "allowed to be. Published by the converge pass.",
        "ok": not still,
        "artifacts": rows,
    })


def converge(explicit=(), allow_paid=True):
    """Bring every artifact back inside its contract. Returns exit code."""
    modes, rows = _fresh.plan(data=DATA, picks=PICKS, allow_paid=allow_paid)

    log("=" * 66)
    log("FRESHNESS SURVEY")
    for r in rows:
        age = "never built" if r["missing"] else f"{r['age_min']:.0f}m ago"
        mark = "DUE  " if r["stale"] else " ok  "
        late = f"  {r['late_min']:.0f}m LATE" if r["late_min"] else ""
        log(f"  {mark}  {r['mode']:<14} built {age:>12}  "
            f"due {r['due_et']:<20} {'PAID' if r['paid'] else 'free'}{late}")

    for m in explicit:
        if m not in modes:
            modes.append(m)
    if not modes:
        log("everything inside contract — nothing to do")
        log("=" * 66)
        return 0

    log(f"PLAN: {' '.join(modes)}")
    log("=" * 66)

    # 🔴 ONE FAILING MODE MUST NOT ABORT THE REST. That is the same
    # deferred-failure rule the workflow already applies to paid pulls:
    # a run that dies on `news` must still rebuild the card. Failures are
    # collected and reported at the end, and the exit code is non-zero so
    # the run goes red -- but everything that CAN land, lands.
    paid = {r["mode"] for r in rows if r["paid"]}
    spent = daily_spend()
    log(f"credits spent today: {spent} of a {DAILY_CAP} daily cap "
        f"({MONTHLY_PLAN}/month)")

    failed, soft_failed, skipped = [], [], []
    for m in modes:
        # 🔴 THE CAP IS CHECKED BEFORE EVERY PAID MODE, NOT ONCE PER RUN.
        # A single props cycle on a 15-game slate is ~120-240 credits, so
        # a check made only at the top of the pass could overshoot by a
        # whole cycle. Re-measuring each time costs a directory walk.
        if m in paid:
            spent = daily_spend()
            if spent >= DAILY_CAP:
                # ⛔ REPORTED, NEVER SILENT. A skipped paid pull leaves an
                # artifact out of contract, the freshness banner says so
                # on the page, and the run goes red. That is the intended
                # behaviour, not a failure to hide.
                log(f"SKIPPING {m}: {spent} credits spent today, cap is "
                    f"{DAILY_CAP}. NOTHING SPENT. It will stay out of "
                    f"contract and the page will say so.")
                skipped.append(m)
                continue
        try:
            log(f"--- converge: {m}")
            run_mode(m)
        except SystemExit as e:
            if e.code:
                _record_failure(failed, soft_failed, m, f"exit {e.code}")
        except Exception as e:
            _record_failure(failed, soft_failed, m, f"{type(e).__name__}: {e}")

    rows2 = _fresh.survey(data=DATA, picks=PICKS)
    after = {r["mode"]: r for r in rows2}
    still = [m for m, r in after.items() if r["stale"]]
    write_freshness(rows2, still)

    # 🔴 THE PAGE MUST BE ABLE TO SAY HOW OLD IT IS. Sam had to ask why
    # the board looked wrong; the site itself said nothing, because
    # nothing on it knew. This publishes the SAME survey the gate uses --
    # ⛔ the contract is defined in freshness.py and NOWHERE ELSE, so the
    # page cannot drift out of agreement with the checker the way two
    # copies of a number in this project always have.

    log("=" * 66)
    if skipped:
        log(f"SKIPPED ON BUDGET: {' '.join(skipped)} "
            f"(spent {daily_spend()} of {DAILY_CAP})")
    for m, why in soft_failed:
        log(f"SOFT FAILURE (run stays green): {m} — {why}")
    if failed:
        for m, why in failed:
            log(f"FAILED: {m} — {why}")
    if still:
        log(f"STILL OUT OF CONTRACT: {' '.join(sorted(still))}")
    else:
        log("every artifact is inside contract")
    log("=" * 66)
    return 1 if failed else 0


def main():
    args = [a for a in sys.argv[1:] if a]
    # ⛔ NO SILENT DEFAULT MODE. An unnamed run converges, which is always
    # a safe and useful thing to do, and never a wrong-file write.
    if not args or args == ["converge"]:
        sys.exit(converge())

    # 🔴 EVERY EXPLICIT MODE STILL CONVERGES. The mode is a HINT about
    # what the caller cared about, not a licence to leave the rest of the
    # site stale. `converge-off` is the escape hatch for a one-shot job
    # (an NFL back-fill, a probe) that must not touch MLB at all.
    if "converge-off" in args or LEAGUE != "mlb":
        code = 0
        for m in args:
            if m == "converge-off":
                continue
            try:
                run_mode(m)
            except SystemExit as e:
                code = code or (e.code or 0)
            except Exception:
                code = 1
        sys.exit(code)

    sys.exit(converge(explicit=args))


if __name__ == "__main__":
    main()
