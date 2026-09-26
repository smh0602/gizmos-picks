# Card vs props model — the agreement label and its question

Status: APPROVED BY SAM 2026-09-25 — the labels and the question in section 2 set by Sam before any result; the definitions, bar, minimum sample and consequence in section 3 fixed by Claude before any scoring code existed

⚠️ **Written and committed on its own, before any code that labels or
scores a row exists.** Sections 2 and 3 are hashed by `test_prereg_gate.py`.

## In plain English (for Sam)

- The football props card (the champion) and the props model
  (`fb_props_model.py`, the challenger) each give a chance for some of the
  same props.
- Every row either of them publishes gets one label:
  - **AGREE:** both are on the same side of the row's break-even.
  - **SPLIT:** one is above the break-even and one is below.
  - **ONE SOURCE:** only one of them rates it.
- The labels are frozen when the card is built and graded after the game.
  They get their own record, clustered by game.
- One question is fixed now: **do AGREE rows beat their break-even by more
  than SPLIT rows?**
- **Nothing about picks or ranking changes because of this, whatever the
  answer.**

## 1. Scope

- NFL and college football props. Nothing MLB.
- No new data and no spend.
- The label never removes, hides, re-ranks or re-prices a row, and never
  feeds either model.

## 2. The labels and the question `[Sam, 2026-09-25, set before any result]`

> "For every props row where the card (champion) and fb_props_model
> (challenger) both give a probability for the same player, market, side and
> line, add a label. AGREE = both probabilities are on the same side of that
> row's break-even; SPLIT = one is above the break-even and one is below;
> ONE SOURCE = only one of them rates the row."
>
> "Freeze each row's label when the card is built and grade it from the
> result. Show a record by label, kept separate from every existing record
> and clustered by game."
>
> "Pre-register the question 'do AGREE rows beat their break-even by more
> than SPLIT rows?' with its bar, its minimum sample and what happens if it
> passes. Nothing about picks or ranking changes in this PR, whatever the
> answer."

## 3. Definitions, bar and consequence, fixed by Claude before any scoring `[2026-09-25]`

### 3a. Which rows, which numbers

- **Rows:** every row on the published card (`picks` in
  `picks/fb-<league>-latest.json`), plus every pick the props model
  publishes (`picks` in `fb-props-model.json`). The same row is identified
  by game id, player (the board's exact string), market, side and line;
  it is counted once.
- **The card's probability:** the card row's `confidence`, when that exact
  row is on the card.
  - ⚠️ It keeps the card's own basis. For football that is `RECORD` (the
    player's own rate), because ledger rule 55 forbids a record rate
    wearing MODEL.
- **The props model's probability:** the probability the props model gives
  that exact side of that exact rung (`rated` in `fb-props-model.json`,
  written for every rung it prices, not only its picks). Basis MODEL.
- **Break-even:** that row's own price. A card row uses the card's
  `break_even`; a row only the model publishes uses the model pick's
  `break_even`. Basis MARKET.
- **Labels:**
  - **AGREE:** both probabilities exist and are both ≥ the break-even, or
    both < it.
  - **SPLIT:** both exist and one is ≥ the break-even while the other is
    < it.
  - **ONE SOURCE:** exactly one exists.
- **Frozen:** each `card-fb` run archives every row's label, both numbers,
  the break-even, the price and the time (`daystore`, write-once). A row is
  graded on the **last copy frozen before its kickoff**.
- **Graded:** once, from the player's game log, exactly as the card's own
  record grades a prop (`record_fb`'s join and grader, via `fb_ledger`). A
  push or a player who did not play is VOID and is left out of every
  denominator. A grade is never recomputed.

### 3b. The question

- **Unit:** one graded AGREE or SPLIT row. `d = won (1/0) − break-even`.
- **Statistic:** Δ = mean d over AGREE rows − mean d over SPLIT rows.
  - Its standard error is cluster-robust by **game**: the CR1 variance of
    the slope in an ordinary least-squares fit of d on an AGREE indicator,
    with clusters = game ids.
  - One-sided p from the normal distribution, for Δ > 0.
- **Pooled:** both leagues together. Each league is reported beside the
  verdict, never as it.
- **Minimum sample:** at least 300 graded AGREE rows **and** at least 100
  graded SPLIT rows, spread over at least 3 distinct weeks. Below that:
  **NOT YET MEASURABLE**.
- **Bar:** **PASSES** if the minimum is met, Δ > 0 and p < 0.05. **FAILS**
  if the minimum is met and either does not hold.
- The rule and bar are frozen. Grading adds rows; it never changes a
  threshold.

### 3c. What happens

- **If it PASSES:** the page and the record say so, with Δ, p and the
  samples. Nothing changes on its own. Whether the label may ever touch a
  pick, a ranking or a price is Sam's decision, in a separate PR he asks
  for.
- **If it FAILS or is NOT YET MEASURABLE:** the label stays a DESCRIPTIVE
  note on the row, exactly as it ships.
- In every case no pick, ranking, price or published row changes because
  of this label.

## 4. What runs

- `fb_agreement.py` labels, freezes, grades and scores. It rides `card-fb`
  after the props model has rebuilt, and writes
  `data/<league>/latest/agreement.json`.
- `fb_props_model.py` also writes `rated`: its probability for every side
  of every rung it prices. Its picks are unchanged.

## Changelog

- **2026-09-25:** written and committed on its own, before any labelling or
  scoring code.
- **2026-09-25, first labels** (Thursday's slate as it stood before kickoff):
  - NFL: 26 rows, 14 AGREE / 11 SPLIT / 1 ONE SOURCE.
  - College: 24 rows, 14 AGREE / 9 SPLIT / 1 ONE SOURCE.
  - Every card row had a props-model probability for the same side. No row
    is graded yet, so the question is NOT YET MEASURABLE.
- **2026-09-26, a mistake in #170, fixed:** once a game kicked off, the page
  file relabelled every row of it ONE SOURCE.
  - **Measured on the live file:** 25/25 NFL and 23/23 college rows at
    2026-09-25 07:14Z; all 25 of Thursday's NFL rows still at
    2026-09-26 00:05Z.
  - **Root cause:** the props model rates only games not yet started, and
    the builder recomputed every row's label on every run.
  - **Fix:** a started game's rows show the board as last frozen before
    kickoff, marked "frozen before kickoff". A started row that was never
    frozen shows no label and says so.
  - The frozen record was always right; it grades frozen rows only.
  - ⚠️ Thursday's NFL game (2026-09-25 00:15Z) kicked off before #170
    merged, so it has **no** frozen labels. It shows "no label was frozen
    before kickoff" on every row. The 14 AGREE / 11 SPLIT quoted in #170
    were computed locally for that PR, never archived.
- **2026-09-26, a gap found, not changed:** labels are frozen on `card-fb`
  runs only, but the props pull also rebuilds the card. Rows it adds after
  the last `card-fb` run before kickoff carry no label. Freezing them at the
  props pull would use the props model's older numbers and bake wrong
  ONE SOURCE labels into the record, so the honest fix (rebuilding the
  props model there too) is proposed to Sam.
