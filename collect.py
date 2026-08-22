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

Usage:  python collect.py props-board
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


def odds_get(path, params):
    params = dict(params)
    params["apiKey"] = ODDS_KEY
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

    log(f"gamelines: {len(games)} games, spent {used}, {left} left")
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
        markets, regions = PITCHER_MARKETS, REGIONS_FULL
    else:
        # Hitter props are banked for a model we have not built yet.
        # One book is enough to backtest against; fifteen is paying for
        # precision we cannot currently interpret.
        markets, regions = BATTER_MARKETS, REGIONS_CHEAP

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
    import glob

    # --- hitter game logs
    hp = "data/latest/hitters.json.gz"
    if not os.path.exists(hp):
        raise RuntimeError("data/latest/hitters.json.gz missing — run the hitters job first")
    H = json.load(gzip.open(hp, "rt"))
    players = H["players"]
    # A normalised name is NOT a unique key. In 2026 there are two players
    # called Max Muncy -- a Dodgers lefty and an Athletics righty, both with
    # enough plate appearances to qualify. A setdefault here would silently
    # attach one man's props to the other man's game log, which is exactly
    # the kind of wrong-but-plausible number this project exists to catch.
    # So names map to a LIST, and the game's own teams break the tie.
    by_name = {}
    for pid, v in players.items():
        by_name.setdefault(norm_name(v["name"]), []).append((pid, v))
    dupes = {k: [x[1]["name"] + " (" + str(x[1]["team"]) + ")" for x in v]
             for k, v in by_name.items() if len(v) > 1}
    log(f"hitter logs: {len(players)} players (pulled {H['pulled_at']})")
    if dupes:
        log(f"  {len(dupes)} shared name(s), resolved by team: {dupes}")


    def resolve(who, away, home):
        """Return (pid, record) or (None, None). Never guesses."""
        cands = by_name.get(norm_name(who))
        if not cands:
            return (None, None)
        if len(cands) == 1:
            return cands[0]
        inplay = [c for c in cands if c[1].get("team") in (away, home)]
        return inplay[0] if len(inplay) == 1 else (None, None)

    # --- newest batter-prop snapshot
    d = now().strftime("%Y-%m-%d")
    snaps = sorted(glob.glob(f"data/{d}/props-batter/*.json.gz"))
    if not snaps:
        raise RuntimeError(f"no batter props stored for {d} — run props-batter first")
    B = json.load(gzip.open(snaps[-1], "rt"))
    log(f"batter props: {B['n_events']} events (pulled {B['pulled_at']})")

    games, unmatched = [], set()
    for ev in B.get("events", []):
        away, home = ev.get("away_team"), ev.get("home_team")

        # collapse every book into one row per (player, market, line, side),
        # keeping the best price and remembering who offered it
        best = {}
        for bk in ev.get("bookmakers", []):
            for m in bk.get("markets", []):
                if m.get("key") not in PROP_STATS:
                    continue
                for o in m.get("outcomes", []):
                    who, pt, px = o.get("description"), o.get("point"), o.get("price")
                    side = (o.get("name") or "").lower()
                    if not who or pt is None or px is None or side not in ("over", "under"):
                        continue
                    k = (who, m["key"], pt, side)
                    if k not in best or px > best[k]["price"]:
                        best[k] = {"price": px, "book": bk["key"]}

        # de-vig each line using the pair of sides where both exist
        pair = {}
        for (who, mk, pt, side), v in best.items():
            pair.setdefault((who, mk, pt), {})[side] = v["price"]

        props = []
        for (who, mk, pt, side), v in sorted(best.items()):
            _label, fn = PROP_STATS[mk]
            pid, rec = resolve(who, away, home)
            if rec is None:
                unmatched.add(who)

            implied = None
            two = pair.get((who, mk, pt), {})
            if "over" in two and "under" in two:
                ro, ru = implied_p(two["over"]), implied_p(two["under"])
                if ro and ru and (ro + ru) > 0:
                    implied = round(100 * (ro if side == "over" else ru) / (ro + ru), 1)

            ev_block = {}
            if rec:
                rows = rec["g"]
                opp = away if rec.get("team") == home else home
                season = _rate(rows, fn, pt, side)
                last15 = _rate(rows[-15:], fn, pt, side)
                homes = _rate([r for r in rows if r.get("h")], fn, pt, side)
                roads = _rate([r for r in rows if not r.get("h")], fn, pt, side)
                vsopp = _rate([r for r in rows if r.get("o") == opp], fn, pt, side)
                ev_block = {"season": _fmt(*season), "last15": _fmt(*last15),
                            "home": _fmt(*homes), "road": _fmt(*roads),
                            "vs_opp": _fmt(*vsopp), "opp": opp, "bats": rec.get("bats")}
                # The prose lives in the page, not here. Writing it twice --
                # once as sentences, once as the numbers behind them -- made
                # the payload a third larger for nothing, and left two copies
                # of the same claim that could drift apart.

            props.append({
                "player": who, "pid": int(pid) if pid else None,
                "team": (rec or {}).get("team"), "market": mk,
                "line": pt, "side": side, "price": v["price"], "book": v["book"],
                "implied": implied, "evidence": ev_block,
            })

        if props:
            games.append({"id": ev.get("id"), "commence": ev.get("commence_time"),
                          "away": away, "home": home, "props": props})

    games.sort(key=lambda g: g["commence"])
    total = sum(len(g["props"]) for g in games)
    # Gzipped: a full slate is ~2.5MB of JSON and roughly 250KB compressed,
    # and every viewer pays that on load. Browsers gunzip it natively.
    write("data/latest/props.json.gz", {
        "pulled_at": stamp(),
        "odds_pulled_at": B["pulled_at"],
        "hitters_pulled_at": H["pulled_at"],
        "kind": "MARKET + DESCRIPTIVE",
        "note": "Market prices and each player's own record. No hitter model exists; "
                "nothing here carries a Gizmo's confidence rating (ledger rule 55).",
        "n_games": len(games), "n_props": total,
        "unmatched": sorted(unmatched)[:40],
        "games": games,
    }, compress=True)
    log(f"props board: {len(games)} games, {total} props, {len(unmatched)} unmatched names")
    if unmatched:
        log(f"  unmatched sample: {sorted(unmatched)[:6]}")
    return None


def implied_p(american):
    return implied(american)


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
            desc = _re.sub(r"<[^>]+>", "", txt("description"))[:220]
            items.append({"source": source, "title": title, "link": link,
                          "published": iso, "summary": desc})
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


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "gamelines"

    if mode not in ("schedule", "results", "hitters", "news", "props-board") and not ODDS_KEY:
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
