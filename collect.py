#!/usr/bin/env python3
"""
Gizmo's Picks — odds & schedule collector.

Runs on GitHub Actions. Pulls from The Odds API and MLB statsapi,
writes timestamped snapshots into data/, and commits them.

Historical odds cannot be bought back cheaply. Every pull we miss is a
day of line-movement and closing-line data that is gone permanently.
So this script is deliberately boring: it fails soft, never crashes the
workflow, and always records what it actually spent.

Usage:  python collect.py gamelines
        python collect.py props-pitcher
        python collect.py props-batter
        python collect.py schedule
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

    write(f"{daydir('gamelines')}/{filename()}", {
        "pulled_at": stamp(),
        "endpoint": "bulk",
        "regions": REGIONS_FULL,
        "markets": GAME_MARKETS,
        "credits_used": used,
        "credits_remaining": left,
        "n_games": len(games),
        "games": games,
    })
    log(f"gamelines: {len(games)} games, spent {used}, {left} left")
    return left


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
    write(f"{daydir('schedule')}/{filename()}", {
        "pulled_at": stamp(),
        "date": d,
        "schedule": body,
    })
    games = (body.get("dates") or [{}])[0].get("games", [])
    log(f"schedule: {len(games)} games")
    return None


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "gamelines"

    if mode != "schedule" and not ODDS_KEY:
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
        else:
            log(f"unknown mode: {mode}")
            sys.exit(1)

        if left is not None and left < RESERVE:
            log(f"WARNING: {left} credits remaining, below reserve of {RESERVE}.")

    except Exception as e:
        # Fail soft. A missed pull is bad; a red workflow that stops the
        # cron because nobody noticed the email is worse.
        log(f"ERROR in {mode}: {type(e).__name__}: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()
