#!/usr/bin/env python3
"""T48 — split-half reliability of NFL defensive EPA per play.

⛔ SPECIFICATION FIXED IN `claude/owed-tests.md` BEFORE THIS FILE EXISTED
AND BEFORE THE COLLECTOR THAT FEEDS IT EXISTED. Nothing here is a choice
made after seeing data:
  - per (defence, season), games ordered by week, ALL games
  - first k vs the rest, k = 1..6, Pearson r across (defence, season)
  - pooled 2021-2025
  - THREE measures, each passing or failing ALONE
  - PASS = r >= 0.35 at some k <= 6
  - ONE RUN. No variants.

✅ THE RULER IS CHECKED BEFORE THE RESULT IS BELIEVED. T39 recorded a
positive control (a WR's own snap_pct, r = 0.80) on the same instrument
in the same run, which is the only reason its failure was credible. The
same is done here: a defence's own PLAY COUNT is a stable team property
and should score high; if the instrument cannot find that, it cannot be
trusted to report a null.
"""
import glob
import gzip
import json
import math
import os
import statistics

D = "/home/claude/rp2/data/nfl/latest"
SEASONS = [2021, 2022, 2023, 2024, 2025]
MEASURES = ["epa_per_play", "pass_epa_per_play", "rush_epa_per_play"]


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    dy = math.sqrt(sum((b - my) ** 2 for b in ys))
    return num / (dx * dy) if dx and dy else float("nan")


# ── load ──────────────────────────────────────────────────────────────
# unit = (defence, season) -> [(week, row), ...] ordered by week
units = {}
for s in SEASONS:
    p = f"{D}/def-epa-{s}.json.gz"
    doc = json.load(gzip.open(p, "rt"))
    assert doc["season"] == s, (p, doc["season"])
    for team, games in doc["by_team"].items():
        rows = sorted(games.values(), key=lambda r: (r["week"] is None,
                                                     r["week"]))
        units[(team, s)] = rows

print(f"units (defence-season): {len(units)}")
gl = sorted(len(v) for v in units.values())
print(f"games per unit: min {gl[0]}  median {statistics.median(gl)}  "
      f"max {gl[-1]}")

# ══════════════════════════════════════════════════════════════════════
# ✅ POSITIVE CONTROL FIRST. If this fails, nothing below is reportable.
# A defence's plays-faced per game is a real, stable team property
# (a team whose own offence is fast/pass-heavy puts its defence on the
# field more, every week of the season).
print("\n── POSITIVE CONTROL: plays faced per game ──")
for k in (3, 5):
    xs, ys = [], []
    for rows in units.values():
        if len(rows) < k + 3:
            continue
        a = [r["plays"] for r in rows[:k]]
        b = [r["plays"] for r in rows[k:]]
        xs.append(statistics.fmean(a))
        ys.append(statistics.fmean(b))
    print(f"  k={k}  n={len(xs):>3}  r = {pearson(xs, ys):+.4f}")

# ⚠️ AND A NEGATIVE CONTROL, so a high r is not just "this code returns
# high numbers". A defence's WEEK NUMBER halves cannot correlate.
print("\n── NEGATIVE CONTROL: shuffled pairing (should be ~0) ──")
import random
random.seed(48)
for k in (3,):
    xs, ys = [], []
    for rows in units.values():
        if len(rows) < k + 3:
            continue
        xs.append(statistics.fmean([r["plays"] for r in rows[:k]]))
        ys.append(statistics.fmean([r["plays"] for r in rows[k:]]))
    ys2 = ys[:]
    random.shuffle(ys2)
    print(f"  k={k}  n={len(xs):>3}  r = {pearson(xs, ys2):+.4f}")

# ── sanity: does the measure name real defences? ──────────────────────
print("\n── SANITY: 2024 season means (LOWER = BETTER DEFENCE) ──")
season_mean = {}
for (t, s), rows in units.items():
    if s != 2024:
        continue
    season_mean[t] = statistics.fmean([r["epa_per_play"] for r in rows])
best = sorted(season_mean.items(), key=lambda kv: kv[1])
print("  best 5 :", "  ".join(f"{t} {v:+.3f}" for t, v in best[:5]))
print("  worst 5:", "  ".join(f"{t} {v:+.3f}" for t, v in best[-5:]))
print(f"  league mean {statistics.fmean(season_mean.values()):+.4f}  "
      f"sd {statistics.stdev(season_mean.values()):.4f}")

# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 66)
print("T48 — SPLIT-HALF r,  BAR = 0.35 AT SOME k <= 6")
print("=" * 66)
print(f"{'measure':<24} " + " ".join(f"k={k:<6}" for k in range(1, 7)))
verdicts = {}
for m in MEASURES:
    cells, peak = [], -9
    for k in range(1, 7):
        xs, ys = [], []
        for rows in units.values():
            if len(rows) < k + 3:
                continue
            a = [r[m] for r in rows[:k] if r[m] is not None]
            b = [r[m] for r in rows[k:] if r[m] is not None]
            if not a or not b:
                continue
            xs.append(statistics.fmean(a))
            ys.append(statistics.fmean(b))
        r = pearson(xs, ys)
        cells.append(r)
        peak = max(peak, r)
    verdicts[m] = peak
    row = " ".join(f"{c:+.4f}" + ("*" if c >= 0.35 else " ") for c in cells)
    print(f"{m:<24} {row}   peak {peak:+.4f}  "
          f"{'PASS' if peak >= 0.35 else 'FAIL'}")

print("\n" + "-" * 66)
for m in MEASURES:
    v = verdicts[m]
    print(f"  {m:<24} peak {v:+.4f}  vs bar 0.35  ->  "
          f"{'PASS' if v >= 0.35 else 'FAIL'}")
print("-" * 66)
print("\nFor comparison, the measures this replaces (same sample, same k):")
print("  T42 all scrimmage yards allowed   peak 0.2923  FAIL")
print("  T43 pass_allowed                  peak 0.3060  FAIL")
print("  T41 WR1 yards allowed, adjusted   peak 0.1782  FAIL")
