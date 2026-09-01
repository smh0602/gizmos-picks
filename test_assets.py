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

print()
if fails:
    print(f"🔴 {len(fails)} FAILED:")
    for f in fails:
        print("   " + f)
    sys.exit(1)
print("✅ asset resolution OK")
