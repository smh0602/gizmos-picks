# T36 -- does a RECENT window on opponent strikeouts beat the season rate?

Registered 2026-08-26, BEFORE any fit.

## Why this test exists at all
Sam, 2026-08-26, asking for the opponent's recent starting-pitcher logs on
the card: *"this will also be contributing to confidence score."*

⛔ It does not, yet, and it must not until this test says so.

The v4.0 strikeout model ALREADY carries an opponent term:

    E[K] = 4.939 + 0.673*(mK8 - 4.949) + K_OPP_B*(oppK - C) +/- 0.151

`oppK` is that opponent's **season-long** mean strikeouts allowed per start.
The last-10-starters block is a **recency-weighted estimator of the same
quantity**. Adding it is not new information arriving; it is a competing
measurement of a term the model already has. Swapping or blending them is
a model change, and this project does not make model changes without a
pre-registered test. T27-T30 and T31-T33 both closed on that rule.

## Specification
Point-in-time, over every carded strikeout row from 2026-08-22 forward.

  A (shipped):  oppK = opponent season mean K allowed per start
  B (recent):   oppK = mean K over the last 10 starts against that opponent
  C (blend):    0.5*A + 0.5*B

Refit `K_OPP_B` for each arm on the SAME training rows, then score on the
held-out rows. Statistic: mean absolute error on realised strikeouts, plus
Brier score on the carded probability.

## The bar, fixed now
B or C ADOPTS only if it beats A by **>= 0.05 MAE strikeouts AND >= 0.005
Brier** on held-out rows. Either one alone is not enough -- a term can look
better on the point estimate while making the probabilities worse, which is
what actually reaches the card.

## Forbidden
- Moving either half of the bar after seeing a result.
- Adopting on the training rows.
- Letting the block feed `confidence`, `blend`, `carried`, a band, or a
  pair before this test passes. It is DESCRIPTIVE on the page until then,
  and the row says so in words.
- Re-running with a different window (5, 15, 20) and reporting the best.
  The window is TEN, fixed here, because that is what Sam specified. A
  different window is a different test and needs its own registration.

## Prediction, recorded now
I expect B to LOSE to A and C to be roughly a wash. A ten-start window on
one opponent is about 40-50 innings of evidence against a full season's
~700; the variance should swamp whatever real drift exists in a lineup
over six weeks. The mechanism Sam is pointing at is real -- lineups do
change, and injuries and call-ups move a team's contact profile -- but I
do not think ten starts can measure it precisely enough to beat the season
rate. If I am wrong, the most likely reason is September roster expansion,
which changes lineups faster than a season average can track.

## What ships regardless
The block itself. It is genuinely useful to a reader deciding a bet by
eye, and it costs nothing -- it is a query over the pitcher logs the
collector already stores, so it needs no StatMuse, no scraping and no
credits. Ledger rule 55 governs how it is labelled: DESCRIPTIVE.
