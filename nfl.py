#!/usr/bin/env python3
"""NFL ingestion — nflverse.

🔴 STDLIB ONLY. The Actions runner installs Python and nothing else; there
is no pip step in the workflow and adding one costs a minute on every run.
That rules out pandas and pyarrow, so every file here is read as CSV with
the `csv` module. ⛔ Do not introduce a dependency without also adding the
install step and re-costing the schedule.

⚠️ NOTHING IN THIS FILE HAS BEEN RUN AGAINST THE REAL SOURCE YET. The Claude
container is barred from fetching URLs, so the file layout below is written
from documentation and MUST be confirmed by `probe()` on the runner before
any collector is scheduled. That is the same discipline the NBA source gets,
and it exists because this project has twice written down "the feed has X"
and been wrong.
"""
import collections
import csv
import gzip
import io
import json
import urllib.error
import urllib.request

GH_API = "https://api.github.com/repos/nflverse/nflverse-data/releases"
UA = {"User-Agent": "gizmos-picks/0.1"}

# What the model needs, and why. See claude/multi-league-spec.md.
#   usage  -> forecastable, carries the model
#   effic. -> high variance, regressed hard toward position baselines
WANT = {
    "stats_player":   "weekly player stats — the TARGET and the trailing-form input",
    "snap_counts":    "USAGE. the best single predictor of next week's usage",
    "depth_charts":   "the lineup-slot analogue MLB's hitter model never had",
    "injuries":       "a WR2 becomes a WR1 the moment WR1 sits",
    "weekly_rosters": "who was actually active, point-in-time",
    "schedules":      "opponent, home/away, game id, kickoff",
    "pbp":            "target share, air yards, red-zone usage",
}


# ✅ CONFIRMED ON THE RUNNER 2026-08-28, collect run #187 — these are the
# real asset names, not a pattern anyone inferred. ⛔ Do not "tidy" them
# into an f-string template: nflverse names are irregular on purpose
# (`stats_player_reg_YYYY` but `roster_weekly_YYYY`), and a template is how
# a collector silently fetches nothing.
FILES = {
    # ✅ WEEKLY, CONFIRMED run #189: 19,422 rows for 2025. ⛔ NOT
    # `stats_player_reg_{y}` -- that is 2,020 rows of SEASON TOTALS and
    # carries a `games` column. Using it would feed one season aggregate
    # in as every week's trailing form and the model would look fitted.
    "stats_player":   "stats_player_week_{y}.csv.gz",
    "snap_counts":    "snap_counts_{y}.csv.gz",
    "depth_charts":   "depth_charts_{y}.csv.gz",
    "injuries":       "injuries_{y}.csv.gz",
    "weekly_rosters": "roster_weekly_{y}.csv.gz",
    "pbp":            "play_by_play_{y}.csv.gz",
}
# ✅ `schedules` is NOT year-partitioned: one `games.csv.gz` (512KB) covers
# every season. The probe's "NONE" was the FILTER being wrong, not the data
# being absent -- which is exactly the "an absence in a response is evidence
# about the response" rule this project already has.
SCHEDULE_FILE = "games.csv.gz"

# ✅ THE JOIN, MEASURED run #189 -- not assumed:
#   stats_player.player_id IS gsis_id      overlap 2,024 / 2,024  (100%)
#   depth_charts / injuries               keyed on gsis_id
#   snap_counts                           keyed on pfr_player_id ONLY
#   weekly_rosters                        carries BOTH -> it is the bridge
# ⚠️ 1,783 of snap_counts' 2,189 pfr ids bridge to a gsis_id (81.5%). The
# collector reports the gap BY POSITION and fails loud if a prop-relevant
# position is thin -- an unbridged left guard costs us nothing, an
# unbridged WR1 is a silent hole in the model.
# ⛔ NEVER JOIN ON NAME. depth_charts x stats_player on `player_name`
# matched 0 of 1,848 rows. A name join here returns an empty model that
# reads as "football does not model" rather than "the plumbing is broken".
#
# ⚠️ 2026 FILES ALREADY EXIST for depth_charts and weekly_rosters; the
# stat and snap files appear once week 1 has been played.
#
# 🔴 `player_stats` (1,822 assets) IS A DIFFERENT, OLDER TAG from
# `stats_player` (542). nflverse migrated. Use `stats_player`.


def _raw(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        blob = r.read()
    if url.endswith(".gz") or blob[:2] == b"\x1f\x8b":
        blob = gzip.decompress(blob)
    return blob


def _json(url, timeout=60):
    return json.loads(_raw(url, timeout).decode())


def probe(log=print):
    """Ask the source what it actually publishes. Writes nothing.

    🔴 RUN THIS BEFORE WRITING A SINGLE COLLECTOR AGAINST A GUESSED URL.
    The GitHub releases API returns every tag with its exact asset names,
    so there is no need to guess a filename pattern at all -- and guessing
    one is how a collector ends up silently fetching nothing.
    """
    log("=== nflverse: what is actually published ===")
    try:
        rels = _json(GH_API + "?per_page=100")
    except Exception as e:
        log(f"🔴 CANNOT REACH THE RELEASES API: {type(e).__name__}: {e}")
        log("   If this fails on the RUNNER, the whole NFL plan changes shape.")
        return False

    log(f"{len(rels)} release tags\n")
    seen = {}
    for r in rels:
        tag = r.get("tag_name")
        assets = [(a["name"], a["size"], a["browser_download_url"])
                  for a in (r.get("assets") or [])]
        seen[tag] = assets
        mark = "  <-- WANTED" if tag in WANT else ""
        log(f"  {tag:22s} {len(assets):>4} assets{mark}")

    log("\n=== the tags this model needs ===")
    ok = True
    for tag, why in WANT.items():
        if tag not in seen:
            log(f"🔴 MISSING TAG '{tag}' — {why}")
            ok = False
            continue
        csvs = [a for a in seen[tag] if a[0].endswith((".csv", ".csv.gz"))]
        recent = sorted(a[0] for a in csvs if "2025" in a[0] or "2026" in a[0])
        log(f"\n  {tag}  ({why})")
        log(f"    {len(csvs)} csv asset(s); 2025/2026: {recent[:6] or 'NONE'}")
        if not csvs:
            log(f"    🔴 NO CSV FORM — stdlib cannot read this tag's format.")
            ok = False

    # 🔴 TWO THINGS RUN #188 EXPOSED, BOTH FATAL IF UNCHECKED:
    #   1. `stats_player_reg_2025` is 2,020 rows. A season has ~18 weeks x
    #      ~1,700 active players ~= 30,000 player-WEEKS, and the file
    #      carries a `games` column -- so it is SEASON TOTALS, not weekly.
    #      Building trailing form off it would have silently used a single
    #      season aggregate as every week's input.
    #   2. `player_name` joins depth_charts to stats_player 0 of 1,848
    #      times. ZERO. The name formats differ, and a name join would have
    #      produced an empty model that looked like a modelling failure
    #      rather than a plumbing one. This is MLB's shared-name bug with a
    #      new face.
    log("\n=== 1. is there a WEEKLY stats file? ===")
    allsp = sorted(a[0] for a in seen.get("stats_player", [])
                   if a[0].endswith(".csv.gz"))
    log(f"  {len(allsp)} gz assets under stats_player")
    for pat in ("week", "reg", "post", "2025", "2026"):
        hit = [n for n in allsp if pat in n]
        log(f"    contains '{pat}': {len(hit)} -> {hit[:8]}")

    log("\n=== 2. is stats_player.player_id the same namespace as gsis_id? ===")
    ids = {}
    for tag, fname, col in (("stats_player", None, "player_id"),
                            ("weekly_rosters", FILES["weekly_rosters"].format(y=2025), "gsis_id")):
        if fname is None:
            cand = [n for n in allsp if "week" in n and "2025" in n] or \
                   [n for n in allsp if "reg_2025" in n]
            fname = cand[0] if cand else None
        hit = [a for a in seen.get(tag, []) if a[0] == fname]
        if not hit:
            log(f"  🔴 {tag}: '{fname}' not found")
            continue
        rows = list(csv.DictReader(
            io.StringIO(_raw(hit[0][2]).decode("utf-8", "replace"))))
        vals = [r[col] for r in rows if r.get(col)]
        ids[tag] = set(vals)
        log(f"  {fname}: {len(rows):,} rows, {col} sample {vals[:3]}")
    if len(ids) == 2:
        a, b = ids["stats_player"], ids["weekly_rosters"]
        log(f"  OVERLAP stats_player.player_id n weekly_rosters.gsis_id = "
            f"{len(a & b):,} / {min(len(a), len(b)):,}")

    log("\n=== 3. does weekly_rosters bridge pfr -> gsis? ===")
    hit = [a for a in seen["weekly_rosters"]
           if a[0] == FILES["weekly_rosters"].format(y=2025)]
    rows = list(csv.DictReader(
        io.StringIO(_raw(hit[0][2]).decode("utf-8", "replace"))))
    both = [r for r in rows if r.get("gsis_id") and r.get("pfr_id")]
    log(f"  {len(rows):,} roster rows; {len(both):,} carry BOTH gsis_id and pfr_id")
    snap = [a for a in seen["snap_counts"]
            if a[0] == FILES["snap_counts"].format(y=2025)]
    srows = list(csv.DictReader(
        io.StringIO(_raw(snap[0][2]).decode("utf-8", "replace"))))
    spfr = {r["pfr_player_id"] for r in srows if r.get("pfr_player_id")}
    bridge = {r["pfr_id"] for r in both}
    log(f"  snap_counts has {len(spfr):,} distinct pfr ids; "
        f"{len(spfr & bridge):,} of them bridge to a gsis_id "
        f"({100.0 * len(spfr & bridge) / max(1, len(spfr)):.1f}%)")

    log("\n=== 4. what is actually under `schedules`? ===")
    for n, sz, _ in seen.get("schedules", []):
        log(f"  {n}  {sz:,}B")

    log("\n✅ PROBE COMPLETE — nothing was written.")
    return ok


# ======================================================================
# THE COLLECTOR
# ======================================================================
# 🔴 EVERY ROW IS POINT-IN-TIME BY CONSTRUCTION. Each game log entry
# carries the KICKOFF DATE from the schedule, so the model filters
# `d < slate_date` exactly the way the MLB pitcher log does. ⛔ Never join
# a season-total column onto a week-3 game: that is a model that has seen
# the future, and it is the single easiest way to fake a good backtest.

# What the model actually reads off a player-week. Usage first, because
# usage is what forecasts; efficiency is regressed toward baselines.
STAT_COLS = {
    "targets": "tgt", "receptions": "rec", "receiving_yards": "rec_yds",
    "receiving_tds": "rec_td", "target_share": "tgt_share",
    "air_yards_share": "ay_share", "receiving_air_yards": "ay",
    "carries": "car", "rushing_yards": "rush_yds", "rushing_tds": "rush_td",
    "attempts": "att", "completions": "cmp", "passing_yards": "pass_yds",
    "passing_tds": "pass_td", "passing_interceptions": "int",
}
# Positions whose props we will actually card. The bridge-coverage check
# below is enforced ON THESE ONLY -- an unbridged offensive lineman is
# irrelevant, an unbridged WR1 is a hole.
PROP_POS = {"QB", "RB", "WR", "TE", "FB"}
BRIDGE_MIN = 95.0          # % of prop-position snap rows that must bridge


def _rows(seen, tag, fname, log):
    hit = [a for a in seen.get(tag, []) if a[0] == fname]
    if not hit:
        raise RuntimeError(f"{tag}: asset '{fname}' not published")
    blob = _raw(hit[0][2]).decode("utf-8", "replace")
    out = list(csv.DictReader(io.StringIO(blob)))
    log(f"  {fname}: {len(out):,} rows")
    return out


def _num(v):
    if v in (None, "", "NA"):
        return 0.0
    try:
        return float(v)
    except ValueError:
        return 0.0


def build_logs(season, log=print):
    """Per-player point-in-time game logs for one season."""
    log(f"=== nfl: building {season} player logs ===")
    rels = _json(GH_API + "?per_page=100")
    seen = {r["tag_name"]: [(a["name"], a["size"], a["browser_download_url"])
                            for a in (r.get("assets") or [])] for r in rels}

    sched = _rows(seen, "schedules", SCHEDULE_FILE, log)
    stats = _rows(seen, "stats_player", FILES["stats_player"].format(y=season), log)
    snaps = _rows(seen, "snap_counts", FILES["snap_counts"].format(y=season), log)
    rost = _rows(seen, "weekly_rosters", FILES["weekly_rosters"].format(y=season), log)

    # -- the bridge. pfr_id -> gsis_id, from the roster that carries both.
    bridge = {r["pfr_id"]: r["gsis_id"] for r in rost
              if r.get("pfr_id") and r.get("gsis_id")}
    log(f"  bridge: {len(bridge):,} pfr->gsis pairs")

    # -- kickoff date and home/away, per (season, week, team).
    when = {}
    for g in sched:
        if str(g.get("season")) != str(season):
            continue
        wk, day, gid = g.get("week"), g.get("gameday"), g.get("game_id")
        for side, opp, home in (("home_team", "away_team", 1),
                                ("away_team", "home_team", 0)):
            if g.get(side):
                when[(str(wk), g[side])] = (day, g.get(opp), home, gid)
    log(f"  schedule: {len(when):,} team-weeks in {season}")

    # -- snap counts, bridged onto gsis, keyed by (gsis, week).
    snap_by = {}
    miss = collections.Counter()
    have = collections.Counter()
    for r in snaps:
        pos = (r.get("position") or "").upper()
        gid = bridge.get(r.get("pfr_player_id"))
        (have if gid else miss)[pos] += 1
        if gid:
            snap_by[(gid, str(r.get("week")))] = r

    thin = []
    for pos in sorted(PROP_POS):
        h, m = have[pos], miss[pos]
        pct = 100.0 * h / (h + m) if (h + m) else 100.0
        log(f"  bridge coverage {pos:3s}: {h:>6,} of {h + m:>6,}  {pct:5.1f}%")
        if (h + m) and pct < BRIDGE_MIN:
            thin.append(f"{pos} {pct:.1f}%")
    if thin:
        # 🔴 FAIL LOUD. A thin bridge on a prop position is a silent hole in
        # the model, and a silent hole looks like a modelling result.
        raise RuntimeError(f"bridge below {BRIDGE_MIN}% on: {', '.join(thin)}")

    players = {}
    for r in stats:
        pid = r.get("player_id")
        if not pid:
            continue
        wk, team = str(r.get("week")), r.get("recent_team") or r.get("team")
        day, opp, home, gid = when.get((wk, team), (None, None, None, None))
        p = players.setdefault(pid, {
            "name": r.get("player_display_name") or r.get("player_name"),
            "pos": (r.get("position") or "").upper(), "team": team, "g": [],
        })
        row = {"d": day, "week": int(wk) if str(wk).isdigit() else wk,
               "team": team, "o": opp, "home": home, "game_id": gid}
        sn = snap_by.get((pid, wk))
        if sn:
            row["snaps"] = int(_num(sn.get("offense_snaps")))
            row["snap_pct"] = round(_num(sn.get("offense_pct")), 3)
        for src, dst in STAT_COLS.items():
            row[dst] = _num(r.get(src))
        p["g"].append(row)

    for p in players.values():
        p["g"].sort(key=lambda x: (x["d"] or "", x["week"]))

    undated = sum(1 for p in players.values() for x in p["g"] if not x["d"])
    withsnap = sum(1 for p in players.values() for x in p["g"] if "snaps" in x)
    total = sum(len(p["g"]) for p in players.values())
    log(f"  {len(players):,} players, {total:,} player-weeks")
    log(f"  {withsnap:,} carry snap counts ({100.0 * withsnap / max(1, total):.1f}%)")
    if undated:
        # ⛔ A row with no kickoff date cannot be filtered point-in-time, so
        # it can never be used safely. Refuse rather than silently include.
        raise RuntimeError(f"{undated} player-weeks have no kickoff date")
    return {"season": season, "source": "nflverse", "players": players}
