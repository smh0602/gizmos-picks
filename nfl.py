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
    "stats_player":   "stats_player_reg_{y}.csv.gz",     # + _post_, _regpost_
    "snap_counts":    "snap_counts_{y}.csv.gz",
    "depth_charts":   "depth_charts_{y}.csv.gz",
    "injuries":       "injuries_{y}.csv.gz",
    "weekly_rosters": "roster_weekly_{y}.csv.gz",
    "pbp":            "play_by_play_{y}.csv.gz",
}
# ⚠️ `schedules` is NOT year-partitioned — it publishes 2 assets covering
# every season at once. The probe's year filter reported "NONE" for it,
# which was the FILTER being wrong, not the data being absent.
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
