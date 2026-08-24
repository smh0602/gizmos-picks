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

import gzip
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

ODDS_KEY = os.environ.get("ODDS_API_KEY", "").strip()
SPORT = "baseball_mlb"
API = "https://api.the-odds-api.com/v4"
STATS = "https://statsapi.mlb.com/api/v1"

# --- budget guard -----------------------------------------------------
# Stop spending when the month's allowance runs low, so a runaway loop or
# a doubleheader-heavy week can never zero us out mid-month.
RESERVE = 750

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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if compress:
        with gzip.open(path, "wt", encoding="utf-8") as f:
            json.dump(obj, f, separators=(",", ":"))
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, separators=(",", ":"))
    log(f"wrote {path} ({os.path.getsize(path)} bytes)")


def daydir(kind):
    d = now().strftime("%Y-%m-%d")
    return f"data/{d}/{kind}"


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
    write("data/latest/board.json", {
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
        rl = ((ref.get("spreads") or {}).get(home) or {}).get("pt")

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
def collect_props(kind):
    if kind == "pitcher":
        # 🔴 Hard Rock ONLY. Sam, 2026-08-22: "i onlt want to see hardrock
        # odds from now on for all props". Enforced at the REQUEST, not at
        # the write-up -- a price that never enters the working set cannot
        # reach a card. us2 still returns espnbet, fliff, betparx, ballybet
        # and hardrockbet_oh in the same response, so the distinct-price
        # check (ledger rule 47) keeps its comparison set for free.
        markets, regions = PITCHER_MARKETS, REGIONS_FULL
    else:
        # Hitter props are banked for a model we have not built yet.
        # One book is enough to backtest against; fifteen is paying for
        # precision we cannot currently interpret.
        markets, regions = BATTER_MARKETS, REGIONS_FULL

    events, used, left = odds_get(f"/sports/{SPORT}/events", {})
    log(f"{len(events)} events on the board; {left} credits before props")

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
            by.setdefault(norm_name(v["name"]), []).append((pid, v))
        dupes = {k: [x[1]["name"] + " (" + str(x[1]["team"]) + ")" for x in v]
                 for k, v in by.items() if len(v) > 1}
        log(f"  {label}: {D['n_players']} players (pulled {D['pulled_at']})")
        if dupes:
            log(f"    shared name(s), resolved by team: {dupes}")
        return D, by

    H, by_hit = load_pool("data/latest/hitters.json.gz", "hitter logs")
    PI, by_pit = load_pool("data/latest/pitchers.json.gz", "pitcher logs")
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
                        # 🔴 THE HITTER ANALOGUE OF STARTS-ONLY, and it is
                        # the same bug. A game with NO plate appearance --
                        # a defensive sub, a pinch-run -- is not an under
                        # that won. At the book it is usually a VOID.
                        # Measured 2026-08-23: Tyler Tolbert's "under 0.5
                        # total bases" reads 41/58 = 71% over every logged
                        # game and 23/40 = 58% over games he actually
                        # batted. Eighteen zero-PA appearances were being
                        # counted as wins. ⛔ Never rate a hitter on a game
                        # he did not bat in.
                        rows = [r for r in rows if (r.get("pa") or 0) > 0]
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
    write("data/latest/props.json.gz", {
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

    write("data/latest/pitchers.json.gz", {
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
NEWS_FEEDS = [
    ("MLB.com", "https://www.mlb.com/feeds/news/rss.xml"),
    ("ESPN MLB", "https://www.espn.com/espn/rss/mlb/news"),
    ("CBS Sports", "https://www.cbssports.com/rss/headlines/mlb/"),
]


def collect_news():
    import re as _re
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime

    items = []
    for source, url in NEWS_FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "gizmos-picks/0.1"})
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read()
            root = ET.fromstring(raw)
        except Exception as e:
            log(f"  {source}: {type(e).__name__}")
            continue

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

            items.append({"source": source, "title": title, "link": link,
                          "published": iso, "summary": desc,
                          **({"image": img} if img else {})})
            n += 1
            if n >= 25:
                break
        log(f"  {source}: {n} items")

    # Newest first; undated entries sink to the bottom rather than the top.
    items.sort(key=lambda x: x["published"] or "", reverse=True)
    if not items:
        raise RuntimeError("every news feed failed — nothing written")

    write("data/latest/news.json", {
        "pulled_at": stamp(),
        "kind": "DESCRIPTIVE",
        "n": len(items),
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

    write(f"data/latest/hitters.json.gz", {
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

    # Pull the finished slate and the one before it. Free, and it catches
    # suspended or resumed games that finalised late.
    for back in (0, 1):
        d = et_slate_date(back)
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
    for f in sorted(glob.glob("picks/*.json")):
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
            if w is None:
                continue
            rows.append({"kind": kind, "market": mk, "side": side,
                         "blend": p.get("blend"), "band": p.get("band"),
                         "implied": p.get("break_even") or p.get("implied"),
                         "edge": p.get("edge"), "won": bool(w), "actual": val,
                         "player": p.get("pitcher") or p.get("player")})

        pairs = []
        for q in card.get("pairs", []):
            legs = []
            for nm, ln in zip(q.get("legs", []), q.get("leg_keys", []) or []):
                legs.append(None)
            pairs.append(q)

        days.append({"date": date, "rows": rows,
                     "n": len(rows), "w": sum(1 for r in rows if r["won"])})

    def tally(rows):
        n = len(rows)
        return {"w": sum(1 for r in rows if r["won"]), "n": n,
                "pct": round(100 * sum(1 for r in rows if r["won"]) / n, 1) if n else None}

    allrows = [r for d in days for r in d["rows"]]
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
        "by_day": [{"date": d["date"], "w": d["w"], "n": d["n"]} for d in days],
        "days_graded": len(days),
        "skipped": [{"date": a, "why": b} for a, b in skipped],
    }
    write("data/latest/record.json", doc)
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
def collect_lineups():
    from datetime import date, timedelta
    path = "data/latest/lineups.json.gz"
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


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "gamelines"

    # The free modes touch statsapi or the repo only. `card` calls nothing
    # at all -- it reads what is already on disk -- so it must not be gated
    # on a key it does not use.
    FREE = ("schedule", "results", "hitters", "news", "props-board", "pitchers",
            "card", "record", "refresh", "lineups")
    if mode not in FREE and not ODDS_KEY:
        log("FATAL: ODDS_API_KEY is not set. Add it as a repository secret.")
        sys.exit(1)

    try:
        if mode == "gamelines":
            left = collect_gamelines()
        elif mode == "props-pitcher":
            left = collect_props("pitcher")
        elif mode == "props-batter":
            left = collect_props("batter")
        elif mode == "schedule":
            left = collect_schedule()
        elif mode == "results":
            left = collect_results()
        elif mode == "hitters":
            left = collect_hitters()
        elif mode == "news":
            left = collect_news()
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
        elif mode == "props-board":
            left = collect_props_board()
        else:
            log(f"unknown mode: {mode}")
            sys.exit(1)

        if left is not None and left < RESERVE:
            log(f"WARNING: {left} credits remaining, below reserve of {RESERVE}.")

    except Exception as e:
        # Fail LOUD. A missed pull is data that cannot be bought back at
        # any sane price, so a broken run has to be visible. Failed runs
        # do NOT disable a cron schedule, so there is no downside to this.
        log(f"ERROR in {mode}: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
