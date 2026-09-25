# MLB pitcher rows: correcting the printed confidence

Status: APPROVED BY SAM 2026-09-25 — rule in section 2 set by Sam (audit proposals C and D, approved 2026-09-25) before any scoring; section 3 fixed by Claude before any scoring

⚠️ **Written and committed on its own, before any code that scores it
exists.** Sections 2 and 3 are hashed by `test_prereg_gate.py`, so neither
can be edited after a result is seen.

## In plain English (for Sam)

- The MLB pitcher rows (strikeouts and outs) have printed about 65% and
  hit about 50%. On both markets the price alone predicted the result
  better than the card did (`research/mlb_calibration_audit.md` §1c).
- Three fixes are tried here, each against the card as it is today:
  1. **Correct** the printed number, learning from pitcher plays already
     graded how the printed number maps to what actually happened.
  2. **Mix in the price**: learn the same way how much weight the
     printed number and the price's own break-even each deserve.
  3. **Smooth the pitcher's own record**, so 3 of 3 reads 87.5%, not
     100%.
- A fix ships only if it predicts better than today's card by a margin
  that is unlikely to be luck. Otherwise nothing changes, and the result
  is written down here.

## 1. Scope and background

- MLB pitcher props only: `strikeouts` and `outs`. Hitter rows, football,
  the T21 shadow flag and the `carried` column are **not** part of this
  test and are not touched by it (`carried` and T21 belong to their own
  registered tests).
- Background: `research/mlb_calibration_audit.md` (PR #162). Pitcher rows
  run 10 to 18 points high in every band with enough games; the own-record
  half is unsmoothed, so a 3-for-3 reads 100% (§3a).

## 2. The rule `[Sam, 2026-09-25, set before any scoring]`

> **C:** "a walk-forward correction of the printed pitcher confidence (or
> a blend with the price), for strikeouts and outs."
>
> **D:** "smoothing the pitcher's own-record half, so that 3 of 3 cannot
> read 100%."
>
> "Pre-register ONE test before any scoring code ... Fix the bar before
> scoring: log loss clustered by game, walk-forward, and a change ships
> only if it beats the current card by the bar."
>
> "A change that passes ships in this PR. A change that fails stays off,
> with its result written in the spec's changelog."
>
> "Leave the T21 shadow column and 'carried' alone; they belong to a
> registered test."

## 3. Definitions fixed by Claude before any scoring `[2026-09-25]`

⚠️ **Not individually approved by Sam. Frozen by Claude so nothing can be
tuned after seeing a result, and disclosed here so Sam can overrule any of
it.** The row counts below (391 strikeout, 318 outs graded rows) were read
before this was written, to check the test can reach its sample floor.
No candidate had been scored against any result.

| | |
|---|---|
| The rows | Every graded pitcher row (`market` = `strikeouts` or `outs`, `won` true or false) of `data/latest/record-detail.json.gz`, joined to the row it grades on `picks/<date>.json` (same player, market, side and line, in card order). A void is left out. A row that does not join is left out and counted. |
| The current card | `blend` / 100, the number the row printed. |
| The game | Cluster = (card date, `game_id` of the card row). A pitcher's strikeout and outs rows in one start share a cluster. |
| Walk-forward | Card dates, day by day. A fitted candidate's mapping for card date D is fitted only on rows whose card date is **before D**, of **the same market**. It needs `fb_model.MIN_TRAIN` (150) earlier rows of that market; before that the candidate has no mapping on that market and those rows are not scored for it. |
| **C1 — correction** | calibrated = logistic(a + b·logit(blend)), per market, fitted by `fb_model.fit` (ridge 1.0 on the standardised input, intercept unpenalised). Inputs clipped to [0.01, 0.99] before the logit. |
| **C2 — blend with the price** | calibrated = logistic(a + b·logit(blend) + c·logit(break_even)), per market, same fit. `break_even` is the row's own `implied` (the printed price's break-even, book margin still in it). |
| **D — smoothed own record** | blend_D = ½·model + ½·(h + ½)/(n + 1), where `model` and `h/n` are the card row's `model` and `raw`. (h + ½)/(n + 1) is the smoothing the card already applies to hitter records. No fit, so every row is scored. |
| Log loss | −[y·ln p + (1 − y)·ln(1 − p)], p clipped to [1e-12, 1 − 1e-12], the same for every number. |
| The test, per candidate | d = (current card's loss) − (candidate's loss), per scored row, so d > 0 means the candidate predicted better. Mean d over the candidate's scored rows, **both markets pooled**. Standard error **cluster-robust by game** (CR1), one-sided test of mean d > 0 on Student's t with G − 1 degrees of freedom, via `mlb_refit.paired_test_clustered`. |
| The bar | A candidate **QUALIFIES** only if all hold: (1) n ≥ 300 scored rows; (2) mean d > 0; (3) p < 0.05 / 3 = 0.0167 (Bonferroni: three candidates are tried); (4) mean d is not below zero on either market alone. **NOT YET MEASURABLE** if n < 300. Otherwise **DOES NOT QUALIFY**. |
| More than one qualifies | The one with the lowest mean log loss on the rows **every** qualifier scored ships. Only one ships. |
| What ships, C1 or C2 | The row's printed `confidence` (and so `edge`, the board, top 10, pairs and parlays) becomes the corrected number, refitted at every card build on every graded row of that market with an earlier card date (no mapping, and no change, below 150). `blend` keeps its definition and is still written, so the permanent record is not rewritten. The record adds stated-vs-actual on `confidence` beside the `blend` table. |
| What ships, D | The own-record half becomes (h + ½)/(n + 1) from the first card built after the merge. Every row carries a field naming which own-record rule built its `blend`, so the record can keep the two apart. `carried` and T21 are unchanged. |
| If nothing qualifies | Nothing on the card changes. The result is recorded in the changelog below. |
| Reported beside the verdict, not part of it | Per-market n and mean log loss for the card and each candidate; stated-vs-actual in 10-point bands on the scored rows; the fitted coefficients on the last card date. |

## 4. What runs

- `mlb_pitcher_cal.py` scores section 3 from the stored record and cards.
  Stdlib only, no API call, no spend. It writes
  `research/mlb_pitcher_cal_run_<date>.json`.
- ⛔ It never edits the card, `blend`, `carried`, a coefficient or a
  published pick.

## Changelog

- **2026-09-25:** written and committed before any scoring code.
- **2026-09-25, first scoring (`mlb_pitcher_cal_run_2026-09-25.json`).**
  Scored on the record rebuilt with proposal A (so 2026-09-22 is in):
  709 graded pitcher rows (391 strikeouts, 318 outs), card dates
  2026-08-23 to 2026-09-23, 0 rows that failed to join. All three
  candidates **QUALIFY**:

  | | Scored rows | Games | Mean d | p (one-sided, by game) | Log loss, card → candidate (K / outs) |
  |---|---|---|---|---|---|
  | C1 correction | 397 | 205 | +0.0441 | 0.0097 | 0.727 → 0.688 / 0.750 → 0.699 |
  | **C2 with the price** | 397 | 205 | **+0.0451** | 0.0102 | 0.727 → 0.691 / 0.750 → 0.691 |
  | D smoothed record | 709 | 334 | +0.0045 | 0.00002 | 0.722 → 0.719 / 0.763 → 0.756 |

  - Only one ships. On the 397 rows every qualifier scored, mean log loss
    was card 0.736, D 0.732, C1 0.692, **C2 0.691**. **C2 ships.**
  - **D qualified and does NOT ship** (the one-ships rule). Its gain is
    real but small (+0.0045 per row); it fixes rows like Gordon's 6/6,
    as the audit predicted, and not the gap.
  - ⚠️ What C2 learned, in words: on **outs** the printed number carries
    almost no information once the price is known (its weight is
    slightly negative, the price's is +0.28 on the standardised scale),
    so a corrected outs row sits a little under its own break-even and
    never has an edge. On **strikeouts** the printed number keeps real
    weight, so a very high rating can still beat its price.
  - ⚠️ **Consequence on the page:** pitcher rows only reach Gizmo's Picks
    with a positive edge, so far fewer will. On the 2026-09-24 slate,
    rebuilt at 16:00Z, `main` put 15 pitcher rows on the board and C2 put
    none. The board fills its other half with hitters, as it always has.
    Pairs and parlays still build, on the corrected number.
  - `blend`, `carried` and the T21 flag are unchanged. The off switch is
    `mlb_pitcher_cal.SHIPPED = None`, which is Sam's call.

- **2026-09-25, two mistakes of mine after the merge (PR #166).**
  - `verify_card.py`'s new check asked `confidence == round(blend)` on
    a row with no correction. `blend` is stored to one decimal, so a true
    69.45 is stored 69.5 and prints 69: **the check failed a correct
    card** (2026-09-24, Dobnak and Painter). Today's rows are all
    corrected, so no live card was refused, but a market below 150 rows
    or `SHIPPED = None` would have hit it. Root cause: I compared against
    a rounded copy of the number. Fixed to the exact relationship (within
    0.5 of the true blend, stored within 0.05). Guard:
    `test_verify_card.py` fails if this check ever fails a real published
    card, and still catches a row printed 2 points off.
  - Collector run 1813 (07:25Z) went red: the new `verify_record.py`
    grades 2026-09-22, and `record.json` was still the pre-merge build
    until the scheduled rebuild at 12:08Z. Root cause: a grading-rule
    change reaches the verifier at merge and the record only at its next
    rebuild. It reconciled at 12:08Z (923/1,499).
