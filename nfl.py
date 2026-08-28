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

    log("\n=== schema check: EVERY file, and the join key ===")
    # 🔴 THE JOIN KEY IS THE THING THAT SILENTLY BREAKS. MLB's worst bugs
    # were joins -- shared names, cameo appearances, the wrong game. So the
    # probe does not just prove the files parse; it reports which candidate
    # ID columns each file carries, and how well they actually overlap.
    keysets, samples = {}, {}
    for tag in ("stats_player", "snap_counts", "depth_charts", "injuries",
                "weekly_rosters"):
        want = FILES[tag].format(y=2025)
        hit = [a for a in seen.get(tag, []) if a[0] == want]
        if not hit:
            log(f"🔴 {tag}: expected asset '{want}' NOT FOUND")
            ok = False
            continue
        name, size, url = hit[0]
        try:
            rows = list(csv.DictReader(
                io.StringIO(_raw(url).decode("utf-8", "replace"))))
        except Exception as e:
            log(f"🔴 {tag}: COULD NOT PARSE — {type(e).__name__}: {e}")
            ok = False
            continue
        cols = sorted(rows[0]) if rows else []
        ids = [c for c in cols if "id" in c.lower() or c in ("player", "full_name")]
        log(f"\n  {name}  {size:,}B  {len(rows):,} rows  {len(cols)} cols")
        log(f"    id-ish columns: {ids}")
        log(f"    all columns: {', '.join(cols)}")
        if rows:
            samples[tag] = rows[0]
            log(f"    sample: { {k: rows[0][k] for k in cols[:10]} }")
        for c in ("gsis_id", "player_id", "pfr_player_id", "player_display_name",
                  "player_name", "player", "full_name"):
            if c in cols:
                keysets.setdefault(c, {})[tag] = {r.get(c) for r in rows if r.get(c)}

    log("\n=== which key actually joins? ===")
    for c, per in sorted(keysets.items()):
        if len(per) < 2:
            log(f"  {c:22s} present in only {list(per)} — cannot join on it")
            continue
        tags = sorted(per)
        base = per[tags[0]]
        line = f"  {c:22s} in {len(per)} files:"
        for t in tags[1:]:
            inter = len(base & per[t])
            line += f" {tags[0]}∩{t}={inter}/{min(len(base), len(per[t]))}"
        log(line)

    log("\n✅ PROBE COMPLETE — nothing was written.")
    return ok
