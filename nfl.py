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

    log("\n=== schema check: read one file end to end ===")
    tag = "snap_counts"
    cands = [a for a in seen.get(tag, [])
             if a[0].endswith((".csv", ".csv.gz")) and "2025" in a[0]]
    if not cands:
        log(f"🔴 no 2025 csv under '{tag}' to test with")
        return False
    name, size, url = cands[0]
    log(f"  {name}  ({size:,} bytes)")
    try:
        rows = list(csv.DictReader(io.StringIO(_raw(url).decode("utf-8", "replace"))))
    except Exception as e:
        log(f"🔴 COULD NOT PARSE: {type(e).__name__}: {e}")
        return False
    log(f"  parsed {len(rows):,} rows, {len(rows[0]) if rows else 0} columns")
    if rows:
        log(f"  columns: {', '.join(sorted(rows[0])[:24])}")
        wk = collections.Counter(r.get("week") for r in rows)
        log(f"  weeks present: {sorted(k for k in wk if k)[:20]}")
        log(f"  sample row: { {k: rows[0][k] for k in list(rows[0])[:8]} }")
    log("\n✅ PROBE COMPLETE — nothing was written.")
    return ok
