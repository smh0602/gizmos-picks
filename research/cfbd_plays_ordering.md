# What IS the ordering in CFBD's `/plays`?

**TASK 36, FINDING 1 — a diagnosis. Nothing is rebuilt here.**
Measured 2026-09-18. Zero CFBD calls. Zero Odds calls.

---

## 0. The refusal was right, and it stays

`data/ncaaf/latest/top-probe-2026.json`, written this morning:

| | |
|---|---|
| `anomaly_pct` | **36.282** against a 2.0 bar |
| `pairs` / `negative` / `over_max` | 57,587 / 12,600 / 8,294 |
| `coverage_median` | **4.0622** — four times the game clock |
| `usable` | **False**, nothing written |

⛔ `CFB_ANOMALY_MAX_PCT` stays at 2.0. `possession.COVERAGE_MIN` stays at
0.90. Neither is touched by this work. The builder declined to publish a
plausible wrong number, which is the behaviour it was built for.

⚠️ The two symptoms are one cause. A sum of **positive** gaps of at most
300s, taken inside a single 900-second period, cannot exceed 900s per
period or 3,600s per game. Reading 4.06× that means the clock descends,
jumps back up, and descends again, repeatedly, inside one period. The
backwards pairs are dropped; the forward legs of the same oscillation are
still summed. **One broken sequence produces both numbers.**

---

## 1. 🔴 A correction to the brief, first, because everything rests on it

> *"ZERO additional CFBD calls. The failed run already stored what is needed."*

**It did not.** `poss_rows` is assembled inside `build_pace` and passed
straight to `possession_from_plays`; only the probe's aggregate counters
and — when usable — the team table are written. The rows themselves are
never persisted.

Measured over **2,376 files** under `data/` and `research/`, the only
files naming `playNumber` are:

| file | what it is |
|---|---|
| `data/ncaaf/latest/probe-report.json` | a **column list** |
| `data/ncaaf/latest/top-probe-2026.json` | a **column list** (`columns_used`) |
| `research/cfb_clock_sample_2019.json.gz` | the **cfbfastR** fixture, not CFBD |

So three of the brief's four questions — whether `playNumber` is monotonic,
whether the anomalies concentrate by game/period/**play type**, whether
`wallclock` orders correctly — **cannot be answered from stored data**, at
any price in reasoning. `playType` is not even among the six fields
`poss_rows` keeps.

⚠️ And a second correction, measured rather than recalled: the brief puts
the fixture's anomaly at **0.37 pct**. Running `possession_from_plays`
over it today gives **0.506 pct**. So the gap is **71.7×**, not 98×. Still
overwhelming; still the same conclusion. (Rule 166 — the 0.37 is a number
written down somewhere and it has gone stale against this code.)

---

## 2. ✅ So the question was asked a different way

Take real college clock sequences whose ordering is known good. Break them
in each way CFBD's rows could plausibly be broken. Ask **which break lands
on the live signature** — not on one number, on four at once: the backwards
rate, the over-300s rate, the coverage median and the coverage maximum.

`test_cfb_ordering.py` does this. It imports `cfb.CFB_REG_PERIODS`,
`cfb.CFB_MAX_PLAY_SECS` and `cfb._clock_secs` — **the real derivation's own
constants and clock parser, never a copy** — and asserts its H0 baseline
reproduces `possession_from_plays`'s own report exactly, so it is a
measurement of the shipped code rather than a parallel implementation of
it.

⚠️ **The simulation lives inside the test, and that is forced rather than
chosen.** `test_harness.py` refuses a top-level import of anything outside
this directory, so it could not sit in `research/`; `test_coaches_probe.py`
refuses to let any non-test top-level file name a probe artifact, with a
ratchet at zero, so it could not sit at top level either. ⛔ Neither check
was touched — the second names the way out itself: *"a test READING a probe
artifact is its job."*

**Live CFBD 2026 — the signature to explain:**
`neg 21.88% · over 14.40% · coverage median 4.062 · max 6.513`

| hypothesis | neg | over | cov median | cov max | mean miss |
|---|---|---|---|---|---|
| **H1b playNumber restarts per drive**, ties by drive id | 20.25% | 11.81% | 4.333 | 6.876 | **9.4%** |
| **H1 playNumber restarts per drive** | 19.89% | 11.63% | 4.347 | 6.885 | **10.3%** |
| H2 no usable order (shuffled) | 45.21% | 23.91% | 1.598 | 3.090 | 71.5% |
| H3 drives emitted out of order | 6.67% | 3.08% | 0.746 | 1.461 | 76.8% |
| H11 rows grouped by the offence | 2.33% | 2.12% | 1.234 | 1.883 | 78.8% |
| H12 drives ordered by driveId as a string | 0.58% | 0.51% | 0.858 | 1.006 | 89.3% |
| H0 true order — playNumber is the game ordinal | 0.02% | 0.48% | 0.869 | 1.006 | 89.9% |
| H4 sorted ascending by clock | 41.69% | 0.00% | 0.000 | 0.000 | 97.6% |

🔴 **One hypothesis lands in the right region on all four components, and
the next-best candidate misses by seven times as much.** That is not a
close call between two explanations; it is one explanation and a field of
rejected ones.

### Why the others fail, individually

- **H2 (no order)** overshoots the anomaly badly (45% backwards vs 22%) and
  *undershoots* coverage (1.60 vs 4.06). Pure disorder produces too many
  reversals and too little forward travel. The live data is not random —
  it is **structured, and structured wrongly**.
- **H3 (drives out of order)** and **H11 (grouped by offence)** each produce
  only a handful of reversals per period, because the sequence stays
  monotone inside long runs. Coverage barely moves.
- **H12** is nearly indistinguishable from the truth — an id-sort bug is
  *not* what is happening.
- **H4 (reversed sort)** makes every pair negative and coverage exactly
  zero. The live data still derives possession for 335 of 336 games, so
  the sort is not simply backwards.

⚠️ **What this is not.** It is a statement about which hypotheses are
consistent with four numbers *we measured*. ⛔ It is **not** a claim about
what CFBD serves. That is the exact error the fixture itself embodies, and
`claude/possession-validation.md` already carries the caveat. The fixture
is cfbfastR/ESPN 2019; CFBD 2026 is a different distributor and a different
season, which is why the residual is ~10% rather than ~0%.

---

## 3. ✅ The remedy prediction, and it is exact

CFBD's `/plays` returns **29 columns**, measured in `probe-report.json`.
Two of them order rows and **the derivation uses neither**:

```
driveNumber     ← the drive's ordinal in the game.  NOT USED TODAY
id              ← the play's own id
```

The code sorts by `playNumber` alone. If `playNumber` is drive-local, the
key that repairs it is `(driveNumber, playNumber)`.

Driven: take a bucket, **shuffle it**, sort by that key.

```
result   neg 0.02%   over 0.48%   med 0.869   max 1.006
truth    neg 0.02%   over 0.48%   med 0.869   max 1.006
✅ identical — the key recovers the true order from ANY input order
```

⛔ **This is a prediction, not a patch.** `cfb.py` is not in this PR's
diff. It should not be until the one-number test below has run against
CFBD's own rows, because the whole point of section 2 is that a fixture
cannot settle a question about a different distributor.

---

## 4. ➡️ The one-number test, at zero call cost

The next `cfbd` run already pays for the `/plays` sweep. It needs to carry
four counters out of it. Inside `possession_from_plays`, where the buckets
already exist:

```python
rep["order_distinct_ratio"]  # mean over buckets of len(set(playNumber)) / len(bucket)
rep["order_max_playnumber"]  # max playNumber seen in any (game, period) bucket
rep["order_monotonic_pct"]   # pct of buckets where playNumber ascends as the clock descends
rep["neg_by_period"]         # {1: n, 2: n, 3: n, 4: n} — concentrated, or even?
```

**What each answer means:**

| reading | verdict |
|---|---|
| `order_distinct_ratio` ≈ 1.00 and `order_max_playnumber` in the hundreds | H1 is **wrong**; `playNumber` is the game ordinal and the cause is elsewhere |
| `order_distinct_ratio` well under 1 and `order_max_playnumber` capped near 25 | **H1 confirmed** — ship `(driveNumber, playNumber)` |
| `neg_by_period` flat across all four periods | structural, the whole ordering assumption is wrong |
| `neg_by_period` concentrated in one period | a boundary bug, not an ordering bug |

For scale, the fixture under its true ordering gives
`order_distinct_ratio` **1.0000** (minimum 1.0000 across every bucket) and
a median `order_max_playnumber` of **110**, against a median longest drive
of **12 plays**. H1 would cap that second number near the first.

⛔ This costs **zero** additional CFBD calls — the rows are already in
memory when the counters would be computed. It is written here rather than
shipped because the brief says diagnose and stop, and because it is a
change to production code on a path that is currently refusing correctly.

---

## 5. 📌 Two things noticed, neither fixed here

1. **`top-probe-<season>.json` is written only to `latest/` and is never
   archived by date.** The artifact this entire report rests on is
   overwritten by the next `cfbd` run. It is snapshotted to
   `research/cfbd_top_probe_2026_20260918.json` so the evidence survives,
   and `test_cfb_ordering.py` reads the figures above out of that snapshot
   rather than trusting this prose. A dated archive for the probe is a
   separate task.
2. **`poss_rows` keeps six fields and discards `playType`.** The brief's
   "are the anomalies concentrated by play type" question is unanswerable
   even in principle until that field rides along. Adding it costs no
   calls and a little memory.

---

## 6. ✅ What I did NOT change

- **`cfb.py`** — not in the diff. No derivation change, no new column, no
  new sort key.
- **`possession.py`** — `COVERAGE_MIN` is still `0.90`.
- **`CFB_ANOMALY_MAX_PCT`** — still `2.0`.
- **MLB**, `.github/workflows/*.yml`, any `cron:` block, any
  `picks/<date>.json`.
- **Zero CFBD calls. Zero Odds calls.** Every figure above comes from one
  committed fixture and one snapshotted probe.
