# Football props card: calibrating its confidence

Status: APPROVED BY SAM 2026-09-24 — rule in section 2 set by Sam before any scoring; section 3 fixed by Claude before any scoring

⚠️ **Written and committed before any code that scores a calibration
exists.** Sections 2 and 3 are hashed by `test_prereg_gate.py`, so neither
can be edited after a result is seen.

## In plain English (for Sam)

- When the football props card has said 80–90%, those plays have hit
  about 41% (NFL) and 59% (college). Its confidence runs high.
- The fix tried here: learn, from plays **already graded**, how the
  card's printed number maps to what actually happens, and print the
  corrected number instead. Each week uses only plays graded before it.
- The corrected number replaces the printed one **only** if it predicts
  better by a margin that is unlikely to be luck, over at least 500
  graded plays. Otherwise the printed number stays, and the card carries
  a visible warning.

## 1. Scope and background

- The **football props card** (`card_fb.py`), NFL and college. Nothing MLB.
- **Found first (step 1 of Sam's request): no code bug.** Across all 113
  graded plays rated 80% or higher:
  - every side re-grades correctly;
  - every stat is the named player's own;
  - anytime TD won all 5 of its rows.

  The inflation is structural. The card rates every player on **last
  season alone** (2025), even when 93 of the 113 had already played 2026
  games. Samples of 7 games print 94%. And the board takes the most
  extreme ratings, which is exactly where the books' line disagrees with
  last season.

## 2. The rule `[Sam, 2026-09-24, set before any scoring]`

> "Map the card's raw probability to a calibrated one, using only picks
> graded before each week (walk-forward)."
>
> "The calibrated number replaces the raw one on the page only if its log
> loss is lower, one-sided p < 0.05, clustered by game, over at least 500
> predictions."
>
> "If it qualifies, apply it in this PR. The pick rule (EV > 0 at the
> best of Hard Rock, FanDuel and DraftKings, plus the existing price
> floors) then uses the calibrated number."
>
> "If it does not qualify, keep the raw number and show a visible warning
> on the card."

## 3. Definitions fixed by Claude before any scoring `[2026-09-24]`

⚠️ **Not approved by Sam. Frozen by Claude so nothing can be tuned after
seeing a result, and disclosed here so Sam can overrule any of it.**

| | |
|---|---|
| The picks | Every row of `data/<league>/latest/record-detail.json.gz` (the card's own graded record, `record_fb.py`) that carries a `confidence` and a graded result (`won` true or false), **both leagues**. A void or ungradable row is left out. |
| Raw probability | `confidence` / 100, the number the card printed. |
| Weeks | Monday to Sunday, keyed by the pick's card date. The mapping for week W is fitted on picks from card dates **before W's Monday**. |
| The mapping | Logistic recalibration: calibrated = logistic(a + b·logit(raw)), with raw clipped to [0.01, 0.99]. It is fitted by `fb_model.fit` (ridge 1.0 on the one standardised input, intercept unpenalised) on both leagues' earlier picks **pooled**: one mapping, because it is one card method. The fit needs `fb_model.MIN_TRAIN` (150) earlier picks; before that there is no mapping. |
| The scored predictions | Every pick in a week that has a mapping. Each is scored raw and calibrated against its own result. |
| Log loss | −[y·ln p + (1 − y)·ln(1 − p)], with p clipped to [1e-12, 1 − 1e-12] for both alike. |
| The test | d = raw loss − calibrated loss per scored pick, so d > 0 means the calibrated number predicted better. The mean of d is taken over every scored pick, **pooled over both leagues**. Its standard error is **cluster-robust by game** (league + game + kickoff date), CR1, with a one-sided test of mean d > 0 on Student's t with G − 1 degrees of freedom, via `mlb_refit.paired_test_clustered`. |
| Verdict | **QUALIFIES** if n ≥ 500, mean d > 0 and p < 0.05. **NOT YET MEASURABLE** if n < 500. Otherwise **DOES NOT QUALIFY**. |
| If it does not qualify | The printed number stays raw. The card's banner opens with the warning built from `calibration.band_flags`, and the page shows the test's status beside the band table. |
| After this PR | The test is re-scored every `card-fb` run and its status is shown. ⛔ **A later QUALIFIES is not applied automatically.** The page says it qualifies and is waiting for Sam, because changing what the card prints is Sam's decision; applying it is a separate PR. |
| Reported beside the verdict, not part of it | Per-league mean log loss, raw and calibrated. Stated against actual, in 10-point bands, raw and calibrated, on the scored picks. The mapping (a, b) each week. |

## 4. What runs

- `fb_card_calibration.py` scores the rule above. It rides `card-fb` and
  writes `data/<league>/latest/card-calibration.json` (with a freshness
  row), which the page reads.
- ⛔ It never edits the card, a published pick, or anything MLB. There is
  no cron change and no spend.

## Changelog

- **2026-09-24:** written and committed before any scoring code.
- **2026-09-24, first scoring: NOT YET MEASURABLE.** 157 picks were
  scored walk-forward, of the 500 needed; 345 graded picks exist in total,
  and the first week has nothing earlier to learn from. The correction
  cut log loss from 0.871 to 0.695 (NFL, 98 picks) and from 1.065 to
  0.701 (college, 59), with mean d = +0.247 and p = 0.008. But the rule
  needs 500, so **the card keeps its raw numbers** and carries the
  warning.
  - ⚠️ The fitted mapping is nearly flat (slope 0.07, then 0.01 on the
    logit scale). Every printed confidence maps to roughly 50–53%, so on
    this evidence the printed number carries almost no information about
    which props hit.
