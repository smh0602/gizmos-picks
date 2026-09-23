# HANDOFF: the guard sweep's clock, 2026-09-23

Dated and it goes stale. Check it against `main` before acting on it.

## What happened

- `test_vacuity.py` runs the whole declared-mutation sweep inside the
  pr-tests / collect Tests loop, with a 2400s per-file clock. Measured
  CI times: 1448s, 2240s, then **2401s = TIMEOUT** (PR #138, run
  35832540827, attempt 1) on the same code. Runner speed alone.
- The nightly `vacuity.yml` (30-minute job limit, tier 1 + tier 2) was
  **cancelled on 09-22 and 09-23**.
- Where the time went (serial sweep, measured locally, 2140s, 376 runs):
  `test_dossier_fb.py` 46% (17 declarations × ~29s dossier builds),
  `test_mlb_tables.py` 19%, everything else ≤5% each.

## What was done (PR #145)

- `vacuity.py` runs tier 1 and tier 2 across `JOBS` detached worktrees
  at once. Same declarations, same red-then-green runs, one mutation per
  tree. A dirty root still runs serially in place.
- On the same slow runner class: **2240s → 1054s**. Not 4×: a 4-vCPU
  runner gave about 2×.
- Guard: `test_vacuity_pool.py` (5 declared mutations, all proven to
  bite).
- `docs/upload/vacuity.yml` staged: nightly limit 30 → 60 min. Sam
  uploads it (`UPLOAD-vacuity.md`).

## Still open, for Sam to decide

- **Headroom is about 1.6× on the slowest runner seen** and shrinks with
  every new declaration. Next options, in order: (C) make
  `test_dossier_fb.py` / `test_mlb_tables.py` cheaper without changing
  what they check; (D) raise the 2400s clock, which is a `collect.yml`
  hand upload plus a matching pr-tests PR.
- ⛔ Sweeping only the declarations whose `file:` a PR touched is
  **weaker**, not equivalent: a guard's verdict also depends on
  everything its test reads (e.g. `tcheck.py`, fixtures under `data/`).
  Not done.

## Changelog

- **2026-09-23:** first version.
