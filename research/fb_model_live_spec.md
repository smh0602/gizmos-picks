# Football models: a frozen record of what was shown, and a plain verdict

Status: APPROVED BY SAM 2026-09-24 — rules in section 2 set by Sam before any result; section 3 fixed by Claude before any scoring

⚠️ **Written and committed before any code that snapshots, grades or
labels a pick exists.** Sections 2 and 3 are hashed by
`test_prereg_gate.py`.

## In plain English (for Sam)

- Every day, before kickoff, the picks the two football models show are
  **saved and frozen**: the game model's spreads, totals and moneylines,
  and the props model's player props. After the games they are graded
  and listed pick by pick under **"What the model showed, graded"**. It
  starts today, and no past result is ever recalculated.
- The models' own picks have **no cap**. Only the Gizmo's Picks card keeps
  its limit.
- Every record gets a plain label: **PROVEN**, **LOSING**, **NOT PROVEN** or
  **NOT YET MEASURABLE**. It is information only; nothing is hidden.

## 1. Scope

- The game model (`fb_model.py`) and the props model (`fb_props_model.py`),
  for the NFL and college. The Gizmo's Picks card is not touched.
- ⛔ No model change, nothing MLB, no new spend and no cron change.

## 2. The rules `[Sam, 2026-09-24, set before any result]`

> "Published-picks ledger. Every day, before kickoff, save the picks the
> models show (game model and props model) to the dated folder via
> daystore. They are frozen and never rewritten. Grade them after the
> games and show a new record on the page, 'What the model showed,
> graded', listing every hit and miss pick by pick. It starts today and
> never recalculates the past."
>
> "No cap on model picks (Sam). Only the Gizmo's Picks card keeps its
> limit."
>
> "Verdict label next to each record, per league and market. It is
> information only; nothing is hidden.
> - PROVEN: on the closing-line record, hit rate beats its mean
>   break-even with one-sided p < 0.05, clustered by game, over at least
>   300 picks.
> - LOSING: the top of the 95% range is below break-even.
> - NOT PROVEN: anything else with at least 300 picks.
> - NOT YET MEASURABLE: under 300 picks."

## 3. Definitions fixed by Claude before any scoring `[2026-09-24]`

⚠️ **Not approved by Sam. Frozen so nothing can be tuned after seeing a
result, and disclosed so Sam can overrule any of it.**

**The ledger**

| | |
|---|---|
| A snapshot | Every `card-fb` run, after both models build, writes the picks each model is showing for games **not yet kicked off** to `data/<league>/<UTC date>/model-picks/<HHMM>.json.gz` via `daystore.archive`, which never overwrites. It holds the game model's picks (`fb-model.json`) and every props-model pick (`fb-props-model.json`). |
| Which snapshot counts | For each game, and for each model separately, the ledger holds the picks from the **last snapshot taken before that game's kickoff in which that game had a pick**. Those are the picks the model was last seen showing. A pick seen in the morning and gone by kickoff is **not** graded, unless the game had no pick in any later snapshot. |
| Starts | Snapshots dated on or after **2026-09-24**. Nothing earlier is added, ever. |
| Grading, game model | Against the stored schedule's final score, exactly as `fb_model.grade` grades the walk-forward: the spread against the pick's line, the total against its line, the moneyline on who won. A push or tie is void. |
| Grading, props model | Exactly as its walk-forward and the card's record grade a prop: `record_fb`'s ±1-day join into the player logs, `_played` (an NFL row with 0 snaps is void), and `_val` / `_won`. |
| Never recalculated | The first time a pick is graded, its result is written to `data/<league>/<UTC date>/ledger-grades/<HHMM>.json.gz` via `daystore`. Every later run **reads that stored result** and never re-grades it, even if a stat is later corrected. A pick not yet gradable stays pending. |
| The record shown | Per league, model and market: picks graded, hits, hit rate and mean break-even of the prices taken. Then every graded pick, newest first, each marked hit or miss. |

**The verdict**

| | |
|---|---|
| The evidence record | **Game model:** its closing-line record (`closing_graded` in `fb-model.json`), as Sam's rule says, per league and market. The one label is shown next to each of that market's records: the headline, closing-line and ledger records. **Props model:** it has no closing-line record, so its walk-forward record at the three books is the evidence. That is its one graded record; the label is shown next to it and next to its ledger rows. |
| Picks | Graded picks only. Pushes and voids are left out. |
| The test | d = hit (1/0) − that pick's break-even, per pick. It is a one-sided test of mean d > 0, CR1 cluster-robust by game on Student's t with G − 1 degrees of freedom, via `mlb_refit.paired_test_clustered`. |
| The 95% range | The record's own `interval_95`, which is clustered by game (`fb_model.record`). |
| Order | Taken in Sam's order, and the first that applies wins. (1) **PROVEN**: at least 300 picks, mean d > 0 and p < 0.05. (2) **LOSING**: the range's top is below the mean break-even. This can apply under 300 picks, since the range already accounts for the sample. (3) **NOT PROVEN**: at least 300 picks. (4) **NOT YET MEASURABLE**: fewer than 300. |

## 4. What runs

- `fb_ledger.py` snapshots, grades and writes
  `data/<league>/latest/model-ledger.json`. It rides `card-fb` after both
  models, with a freshness row.
- `fb_model.verdict()` is the one implementation of the label. Both model
  builders and the ledger read it.
- The props model's page cap is removed. `fb_props_model.build` writes
  every pick.
- ⛔ It never edits a published pick, the card, or anything MLB.

## Changelog

- **2026-09-24:** written and committed before any scoring code.
