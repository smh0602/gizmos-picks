# MLB champion vs challenger — the re-fit rule

Status: APPROVED BY SAM 2026-09-23 — replacement rule in section 2; section 3 fixed by Claude before any result

🔴 **Written and frozen before any walk-forward result was computed.**
Section 2 is Sam's rule, in his words. Section 3 is the arithmetic the code
needs to apply it. Claude fixed it before running anything, and it is
disclosed here for Sam to read. `test_prereg_gate.py` fingerprints sections
2 through 3, so neither can be changed after a result is seen. A different
rule is a new pre-registered test with a new id.

## In plain English (for Sam)

The strikeout and outs models on the MLB card (v5.0) were fitted once, on
games through August 31 2026, and never again. This test asks, every week,
whether the same model **re-fitted on everything played so far** would
have predicted the games better than the frozen v5.0 numbers did. It never
changes the card by itself. If the re-fitted version clears your bar, a
pull request opens for you to decide.

---

## 1. Scope

| | |
|---|---|
| Games | Every 2025 and 2026 MLB regular-season and postseason game, from `statsapi.mlb.com` (free). |
| Unit | One **start**: the starting pitcher of one game. |
| Champion | **v5.0**, the coefficients in `card.py`, read from there and never copied. |
| Challenger | The same model, re-fitted by v5.0's own recipe on games before each week. |
| Never | This test switches no model and changes no coefficient. |

## 2. The replacement rule `[Sam, 2026-09-23, approved before any result was seen]`

> "Champion vs challenger. v5.0 stays champion. Score a challenger
> walk-forward over all of 2025 and 2026: for each week, fit only on games
> before it, predict that week, grade. Score v5.0 the same way."
>
> "the challenger replaces v5.0 only if its per-prediction log loss is
> lower with one-sided p < 0.05 (paired test) over at least 500
> predictions. Report both records in the PR. Do not switch models or
> change any coefficient in this PR."

## 3. Definitions fixed by Claude before any result `[2026-09-23]`

⚠️ **Not approved by Sam. Frozen by Claude so nothing can be tuned after
seeing a result, and disclosed here so Sam can overrule any of it.**

| | |
|---|---|
| A prediction | One start in one market: **strikeouts** or **outs**. Each eligible start gives two predictions, and both markets are **pooled**, because the rule speaks of "the challenger" as one model. Each market is also reported on its own, but that per-market figure is **not** part of the decision. |
| Log loss, strikeouts | −ln P(K = observed) under Poisson(λ), with λ floored at 0.05, exactly as `card.py` does. |
| Log loss, outs | −ln P(observed − 0.5 < X ≤ observed + 0.5) under Normal(μ, s), where s is the pitcher's sample SD of outs over his earlier starts that season (the card's `cvO × season mean`). Outs are whole numbers, so the Normal is scored on the one-out bucket around the result. |
| Probability floor | Any probability below 1e-12 is scored as 1e-12, for both models alike. |
| Eligible start | The card's own point-in-time inputs exist. The pitcher has **≥ 3 earlier starts that season**, and the opponent has **≥ 20 earlier starts faced that season** (v5.0's fit filter). The previous start's pitch count is known. The SD of his earlier outs is above 0. "Earlier" means **an earlier date**: a whole date is scored before any of its starts joins the history, as in v5.0. |
| Inputs | Trailing 8 = his last 8 earlier starts **in the same season**. The opponent's mean K allowed, and the league mean K it is centred on, both come from earlier starts that season. These are the card's own definitions. |
| Weeks | Monday-to-Sunday calendar weeks, in date order across both seasons. |
| Challenger fit | Ordinary least squares on every eligible start dated **before** the week's Monday, across both seasons, in v5.0's own shape. Strikeouts: intercept, trailing K (centred on the training mean), opponent K minus that date's league mean, home ±1. Outs: intercept, pitch-count slope and home ±1 from the pooled fit, and a trailing-outs slope `k` from separate fits within v5.0's three tiers (cut-points 15.25 and 17.0, read from `card.py`). |
| When the challenger starts | Only once **≥ 1,000 eligible starts** precede the week, and only when every fit it needs solves. Before that it makes no prediction. |
| The paired set | The predictions where **both** models made one. The rule's p-value is computed on this set alone. |
| The test | d = champion loss − challenger loss for each paired prediction. One-sided paired t-test of mean d > 0, using Student's t with n − 1 degrees of freedom. |
| Verdict | **QUALIFIES** if n ≥ 500, mean d > 0 and p < 0.05. **NOT YET MEASURABLE** if n < 500. Otherwise **DOES NOT QUALIFY**. |
| Calibration table | For every prediction and every half-line from 0.5 to 12.5 strikeouts and 9.5 to 21.5 outs, the model's P(over) is recorded against what happened. The records are grouped into 10-point buckets, and each bucket shows the mean stated probability (MODEL) beside the observed hit rate (DESCRIPTIVE). ⚠️ A start contributes many correlated rows, so the bucket counts are not independent observations. |

⚠️ **Disclosed risk in the approved rule, not acted on.** A paired t-test
treats each prediction as independent. Two predictions from one start, and
many from one pitcher, are not. So p is likely **smaller than it should
be**, which makes qualifying **easier**, not harder. The rule is applied
exactly as approved. A version clustered by pitcher is Sam's call, as a
new test with a new id.

## 4. What happens each week

1. The weekly job pulls any new games, reruns the whole walk-forward, and
   writes `data/latest/mlb-refit.json`.
2. If the verdict is **QUALIFIES** and no challenger PR is already open, it
   opens one titled "[ASK SAM] MLB challenger qualified". The PR carries the
   re-fitted coefficients and both records. ⛔ It does not edit `card.py`;
   switching models is Sam's decision.
3. Otherwise it only updates the report.

## Changelog

- **2026-09-23 (first run):** **DOES NOT QUALIFY. v5.0 stays.** 13,004
  paired predictions; mean improvement from re-fitting **−0.0219** (the
  challenger was worse); one-sided p ≈ 1.0. Strikeouts were a tie
  (−0.0006). Outs were worse in every segment (−0.0431 overall), including
  2026 after v5.0's fit window, where neither model had seen the games.
  The full report is `research/mlb_refit_run_2026-09-23.json`. The code
  was committed before this run (96c73cbd), after this spec (cda92bd4).
- **2026-09-23:** written. Section 2 approved by Sam; section 3 fixed by
  Claude before any result was computed.
