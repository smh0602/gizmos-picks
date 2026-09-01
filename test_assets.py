#!/usr/bin/env python3
"""`_rows` asset-name resolution — the layer that has silently swapped
one KIND of file for another and nearly did it again.

🔴 THIS FUNCTION'S HISTORY IS THE ARGUMENT FOR THIS FILE.
  1. `[run #206]` an `any()` word match let `rosters_2021.csv.gz` (SEASON
     rosters, one row per player) stand in for `roster_weekly_2021.csv.gz`
     (one row per player PER WEEK). The build "succeeded" and the bridge
     collapsed to RB 75.0% / TE 70.8% / WR 77.2%. ⛔ INVISIBLE IN THE
     OUTPUT -- it surfaced only as a coverage number nobody questioned.
  2. `[2026-09-01]` routes 2023 refused to build: two candidates matched,
     `pbp_participation_2023.csv` and `pbp_participation_old_2023.csv`,
     and the schema of the `old` one is DIFFERENT.
     🔴 A COMMENT IN nfl.py ASSERTED THAT COULD NOT HAPPEN -- "will not
     take the `old` one, because 'old' is a word the requested name does
     not carry." **THE REASONING WAS BACKWARDS**: the rule requires every
     word of the REQUESTED name to appear in the CANDIDATE, so an EXTRA
     word does not disqualify anything.
     ⚠️ The guard held. **A comment claiming a safety the code does not
     have is the more dangerous half of that defect.**

✅ SO THE RESOLUTION ORDER IS PINNED HERE, BY HAND:
     exact name  ->  exact stem ignoring .gz  ->  same-year word match
                 ->  refuse, naming the candidates
⛔ AND THE REFUSALS ARE TESTED AS HARD AS THE MATCHES. A resolver that
never refuses is the bug, not the feature.

⚠️ No network, no data files, no clock.
"""
import sys

import nfl

fails = []
LOG = lambda *a, **k: None


def resolve(fname, names, tag="t"):
    """Return the asset name `_rows` would fetch, or an Exception."""
    assets = [(n, 1, "http://x/" + n) for n in names]
    got = {}
    # ⚠️ Stub the DOWNLOAD, not the resolver. The thing under test is
    # WHICH asset gets chosen; the bytes are irrelevant and the network
    # must never be touched by a test.
    nfl._raw = lambda url: got.setdefault("u", url) and b"" or b""
    try:
        nfl._rows({tag: assets}, tag, fname, LOG)
    except Exception as e:
        return e
    return got.get("u", "").rsplit("/", 1)[-1]


def eq(got, want, label):
    ok = (got == want)
    shown = f"{type(got).__name__}" if isinstance(got, Exception) else repr(got)
    print(f"  {'ok  ' if ok else '🔴 FAIL'} {label:<46} {shown}")
    if not ok:
        fails.append(f"{label} (got {got!r} want {want!r})")


def raises(fname, names, must_contain, label):
    r = resolve(fname, names)
    ok = isinstance(r, Exception) and all(m in str(r) for m in must_contain)
    print(f"  {'ok  ' if ok else '🔴 FAIL'} {label:<46} "
          f"{type(r).__name__ if isinstance(r, Exception) else repr(r)}")
    if not ok:
        fails.append(label)


P23 = "pbp_participation_2023.csv"
POLD = "pbp_participation_old_2023.csv"

print("1. exact name wins outright")
eq(resolve("pbp_participation_2023.csv.gz",
           ["pbp_participation_2023.csv.gz", P23, POLD]),
   "pbp_participation_2023.csv.gz", "exact beats every other candidate")

print("\n2. 🔴 THE 2023 BUG — .gz asked for, uncompressed published")
eq(resolve("pbp_participation_2023.csv.gz", [P23, POLD]), P23,
   "resolves to the real 2023 file, NOT the `old` one")
eq(resolve("pbp_participation_2024.csv.gz",
           ["pbp_participation_2024.csv"]), "pbp_participation_2024.csv",
   "2024 now resolves BY NAME, not by word fallback")
# ⛔ and the reverse: uncompressed asked for, gzipped published
eq(resolve("roster_weekly_2025.csv",
           ["roster_weekly_2025.csv.gz"]), "roster_weekly_2025.csv.gz",
   "works in the other direction too")

print("\n3. ⛔ THE SUBSTITUTION THAT COLLAPSED THE 2022 BRIDGE")
raises("roster_weekly_2021.csv.gz", ["rosters_2021.csv.gz"],
       ["not published"],
       "season rosters must NOT satisfy roster_weekly")
eq(resolve("roster_weekly_2021.csv.gz",
           ["roster_weekly_2021.csv.gz"]), "roster_weekly_2021.csv.gz",
   "the real weekly roster still resolves")

print("\n4. ⛔ IT REFUSES TO GUESS, AND NAMES WHAT IT REFUSED")
# 🔴 THE ONE THIS FILE WAS WRITTEN FOR. With ONLY the `old` file
# published, the old rule resolved to it SILENTLY -- one candidate is
# not an ambiguity, so the guard never fired. ⛔ A DIFFERENT SCHEMA,
# ingested as if it were the right one.
raises("pbp_participation_2023.csv.gz", [POLD],
       ["not published"],
       "🔴 `old` file ALONE -> refuse, never substitute")
raises("pbp_participation_2023.csv.gz",
       ["pbp_participation_2023.parquet", POLD, "pbp_participation_2023.qs"],
       ["not published"],
       "`old` beside non-csv formats -> still refuse")
raises("pbp_participation_2023.csv.gz",
       ["pbp_participation_2022.csv", "pbp_participation_2025.csv"],
       ["not published", "2023"],
       "wrong year only -> refuse, naming the year")
raises("pbp_participation_2023.csv.gz", [],
       ["0 assets"], "empty release -> says the release is empty")

print("\n5. ⚠️ non-csv formats are never fetched as csv")
eq(resolve("pbp_participation_2023.csv.gz",
           ["pbp_participation_2023.parquet",
            "pbp_participation_2023.rds", P23]), P23,
   "parquet and rds present, csv still chosen")

# ══════════════════════════════════════════════════════════════════════
print("\n6. 🔴 A SEASON THAT HAS NOT STARTED IS NOT A FAILURE")
# `[run #307, 2026-09-01]` the Tuesday NFL rebuild fired with SEASON=CUR
# -> 2026, nflverse held 542 assets and NONE mentioned 2026, and the job
# went red. ⛔ Nothing was broken; the season had not kicked off. It
# would have gone red every Tuesday until mid-September.
# ⚠️ THE RULE IS NARROW AND BOTH HALVES ARE TESTED: only the CURRENT
# season may be forgiven. A missing 2019 must still be fatal.
import freshness

r = resolve("stats_player_week_2026.csv.gz",
            ["stats_player_week_2024.csv.gz", "stats_player_week_2025.csv.gz"])
eq(isinstance(r, nfl.SeasonNotStarted), True,
   "no asset mentions the year -> SeasonNotStarted")
eq("NONE" in str(r), True, "  ...and it still says what it DID see")

# ⛔ A WRONG NAME IS NOT A MISSING SEASON. The year IS published here,
# so this must stay an ordinary failure that turns a run red.
r = resolve("stats_player_week_2025.csv.gz",
            ["rosters_2025.csv.gz", "snap_counts_2025.csv.gz"])
eq(isinstance(r, Exception) and not isinstance(r, nfl.SeasonNotStarted),
   True, "🔴 year present, name wrong -> ORDINARY failure, still red")

print("\n7. the current-season rule, and it matches the workflow")
import datetime as _dt
_UTC = _dt.timezone.utc
for _d, _want in (("2026-09-01", 2026), ("2026-08-01", 2026),
                  ("2026-07-31", 2025), ("2026-01-15", 2025),
                  ("2025-12-31", 2025)):
    _y, _m, _dd = map(int, _d.split("-"))
    eq(freshness.current_football_season(_dt.datetime(_y, _m, _dd, tzinfo=_UTC)),
       _want, f"{_d} -> season {_want}")

# 🔴 THE SAME RULE LIVES IN THE WORKFLOW, IN BASH. TWO COPIES DRIFT.
# ⛔ So parse the workflow and check they agree, rather than trusting a
# comment that says they do.
import os as _os
import re as _re
_wf = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                    ".github/workflows/collect.yml")
if _os.path.exists(_wf):
    _txt = open(_wf, encoding="utf-8").read()
    _has = ('Y=$(date -u +%Y)' in _txt
            and '[ "$M" -lt 8 ] && Y=$((Y - 1))' in _txt)
    eq(_has, True,
       "workflow still resolves CUR as year, minus 1 before August")
else:
    print("  ⚠️  workflow not found beside this test — pairing UNCHECKED")

print()
if fails:
    print(f"🔴 {len(fails)} FAILED:")
    for f in fails:
        print("   " + f)
    sys.exit(1)
print("✅ asset resolution OK")
