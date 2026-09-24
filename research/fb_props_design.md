# Football props model: design, fixed before any scoring

`[Sam, 2026-09-24]` Step 5 of the machine-learning plan. A player-props
model for the NFL and college, trained on stored player logs from 2021
through 2026. It predicts each player's stat distribution, and so
P(over) and P(under) at any line. It is scored walk-forward at the best
Hard Rock / FanDuel / DraftKings price from the stored prop snapshots,
and compared, champion against challenger, with the existing props card.
It retrains inside `card-fb`, with no new spend and no cron changes.

⚠️ **Written and committed before any code that scores a prop exists.**
Everything that decides a result is fixed below: the inputs, the model,
the pick rule and the replacement rule. The replacement rule (§6) is Sam's
own; the rest is Claude's, disclosed so Sam can overrule it.

## In plain English (for Sam)

- For every prop the books post in the markets we already pull, the model
  estimates the player's likely stat line. That gives a chance for the
  over and the under at any line.
- **It learns from the player logs we already store (2021–2026), which
  cost nothing.** Every input it uses is known before kickoff.
- Each week of the prop snapshots (from 2026-09-03), it is retrained on
  earlier games only, then asked about that week, then graded at the best
  of your three books.
- **The honest limit:** books' prop lines exist only in our snapshots from
  September 2026, so the model cannot learn how much to trust the line
  from the 2021–2025 logs. It learns that from the priced weeks as they
  accumulate (§3, stage 2).
- It replaces the current props card **only** if its predictions are
  better by a margin that is unlikely to be luck (§6). **This PR never
  switches.** You decide.

## 1. Scope and data

- **Markets:** only the prop markets `collect.py` already pulls. That is
  pass yards, pass TDs, rush yards, receiving yards, receptions and
  anytime TD for the NFL, and the same without pass TDs for college
  (`PROP_MARKETS`). No market, region or book is added.
- **Books:** Hard Rock (`hardrockbet`, `hardrockbet_oh`), FanDuel and
  DraftKings, which is `collect.league_books()`.
- **Training data:** `data/<league>/latest/players-<season>.json.gz`, 2021
  through 2026.
- **Prices:** `data/<league>/<date>/props-player/*.json.gz`, from
  2026-09-03 (college) and 2026-09-09 (NFL).
- **Outcomes:** the same player logs, graded by `record_fb`'s own helpers
  (`_val`, `_won`, `_played`) and its ±1-day join. The card's record is
  graded the same way.

## 2. Inputs — every one known before kickoff

For a player's game on date D, "history" is his played games dated
**before D**. NFL: a game with `snaps` > 0, or no snap field but a stat.
College: every log row. Each market reads one stat **s** and one usage
figure **u**:

| Market | s (the stat) | u (usage) | Positions trained on |
|---|---|---|---|
| Pass yards | `pass_yds` | `att` | QB |
| Pass TDs (NFL) | `pass_td` | `att` | QB |
| Rush yards | `rush_yds` | `car` | QB, RB, WR |
| Receiving yards | `rec_yds` | NFL `tgt`, college `rec` | WR, TE, RB |
| Receptions | `rec` | NFL `tgt`, college `rec` | WR, TE, RB |
| Anytime TD | `rush_td + rec_td` (the card's `_td`) | NFL `car + tgt`, college `car + rec` | QB, RB, WR, TE |

**The inputs** (§ = Sam's signal number):

| # | Input | Source, point-in-time |
|---|---|---|
| 1 | season-to-date mean of s | his games this season before D; 0 if none |
| 2 | has a game this season (0/1) | |
| 3 | mean of s over his last 3 games | any season |
| 4 | mean of s last season | 0 if none |
| 5 | season-to-date mean of u | |
| 6 | mean of u over his last 3 games | |
| 7 | mean `snap_pct`, last 3 games | NFL; 0 for college, which stores no snaps |
| 8 | log(1 + games this season) | |
| 9 | **§5** opponent's defence: s allowed per game to this position so far this season, minus the league's per-game mean so far | accumulated from the logs, games before D only; 0 if the opponent has fewer than 2 games |
| 10 | **§6** team pace: the team's (attempts + carries) per game so far this season, minus the league mean so far | from the logs |
| 11 | **§6** opponent pace, the same | |
| 12 | **§6** possession: team share minus opponent share, from earlier games only | `possession.share_before`; 0 while the per-game rows are not stored |
| 13 | **§8** home (1/0) | log row |
| 14 | **§8** neutral site (college) | log row |
| 15 | **§8** dome or closed roof (NFL) | `wx.roof` |
| 16 | **§8** temperature − 60°F (NFL, where stored; else 0) | `wx.temp` |
| 17 | **§8** wind mph (NFL, where stored; else 0) | `wx.wind` |
| 18 | **§7** teammates ahead of him ruled out (NFL only) | `ahead_out`: same-team, same-position players with a higher earlier snap share who are OUT this week, from the injury report |
| 19 | **§7** his offensive linemen out (NFL) | `ol_out` |
| 20 | **§7** opponent's defensive linemen out (NFL) | `opp_dl_out` |
| — | **the market line itself** | stage 2 (§3), because the logs carry no lines |

- **§7 is NFL-only** (Sam, 2026-09-23). College gets 0 on inputs 18–20.
- **A missing input is 0.**
- ⛔ **No input reads the game itself.** A per-game field such as
  `tgt_share` is only ever averaged over earlier games.

## 3. The model

**Stage 1: the stat distribution.** One ridge regression per league ×
market, on the 20 standardised inputs, with λ = 1.0 and the intercept
unpenalised. It is solved exactly, from running sums, stdlib only. It is
trained on every played game of a trained position that has at least one
earlier game in the logs.

| Market | Regression target | Distribution | P(over L) |
|---|---|---|---|
| Pass, rush, receiving yards | √max(s, 0) | Normal on the square-root scale: mean from the regression, σ = the training residual RMS | 1 − Φ((√L − mean)/σ) |
| Receptions, pass TDs | s | Poisson(μ), μ = max(0.05, prediction) | 1 − F(⌊L⌋; μ) |
| Anytime TD | rush_td + rec_td | Poisson(μ) | P(yes) = 1 − e^(−μ) |

- P(under L) = P(s < L), so a push is neither.
- ⚠️ **Changed after the first run:** for the yardage markets, the stat,
  usage and opponent inputs are averaged on the **same √ scale** as the
  target (first written with raw yards). See the changelog: a design
  mistake, recorded with its root cause.

**Stage 2: the market line.** The final probability is

  logistic(a + b·logit(p₁) + c·logit(p_mkt) + d·[anytime TD]).

- p₁ is stage 1's probability.
- p_mkt is the market's own probability at **that exact line**: each of
  the three books quoting both sides there is de-vigged, and the average
  is taken. For anytime TD, which is posted "Yes" only, it is the average
  implied probability of "Yes"; its vig is absorbed by the fit.
- The logistic fit is `fb_model.fit` (ridge 1.0, standardised), pooled
  over the league's markets. It is trained on every graded rung from
  **earlier** prop weeks, each carrying its own walk-forward p₁.
- **Until that fit exists** (fewer than 150 earlier graded rungs in the
  league, `fb_model.MIN_TRAIN`), the final probability is p₁. So is it
  for a rung with no two-sided quote at the three books.

## 4. Walk-forward

- **Weeks** run Monday to Sunday, in date order. Only weeks that have a
  prop snapshot are scored.
- **Stage 1** for week W is fitted on every played game dated before W's
  Monday, 2021 onwards. **Stage 2** for week W is fitted on graded rungs
  from weeks before W.
- **The prices for a game** come from the last snapshot pulled **before
  its kickoff**. A **rung** is one (game, player, market, line). Its price
  on each side is the best among the three books **at that exact line**.
- **The player:** the name is matched with the card's own matcher
  (`card_fb.norm`), over the 2025 and 2026 logs. A name that matches no
  one, or more than one player, is skipped, exactly as the card does.
- **The outcome:** `record_fb`'s ±1-day join, `_played` (an NFL row with
  0 snaps is void) and `_val` / `_won`. With no log row, or no game, the
  rung is not graded.

## 5. The pick rule and the record

- **For each side of a rung:** EV = p × decimal(price) − 1, at the best
  three-book price. **The card's own price floors apply:** a side is
  eligible only if its price is between `card_fb.PRICE_FLOOR` (−700) and
  `card_fb.PRICE_CEIL` (+400).
- **One pick per player and market per game:** the eligible side with the
  highest EV, if that EV is above 0.
- **The record, per league and market:**
  - picks and hit rate (a push or a void is left out);
  - the mean break-even of the prices taken;
  - a 95% range on the effective n clustered by game (`fb_model.record`).
- **Calibration:** every graded rung, in 10-point buckets of the model's
  stated P(over) or P(yes). Each bucket shows the mean stated probability
  (MODEL) beside the observed rate (DESCRIPTIVE). The champion's
  calibration is shown the same way. ⚠️ Rungs of one game are correlated,
  so bucket counts are not independent.
- **The page** shows this week's picks, top 25 by model probability. That
  is the card's own `BOARD_MAX`; the file keeps them all. The record per
  market sits next to them, in its own section labelled MODEL, below the
  existing card, which stays.

## 6. Champion vs challenger — the replacement rule `[Sam, 2026-09-24]`

> "Champion vs challenger: the existing football props card is the
> champion. Score its probabilities on the same props. The new model
> replaces it only if its log loss is lower, with one-sided p < 0.05,
> clustered by game, over at least 500 predictions. Do not switch in this
> PR. I decide."

**Definitions, fixed by Claude before any result:**

| | |
|---|---|
| The champion's probability | The card's own published confidence for that rung: `card_fb.rate_for(...)` / 100. It is computed on the logs season the card used on that date (the card file's `logs_season`, 2025 on every card so far), with the card's own gates (snap floor, six games, participation, usage floor, measured markets). ⚠️ The card saves its confidence for only about 25 rows per day, so it is recomputed with the card's own function, not read from the file. |
| A prediction | One graded rung. It is P(over) for over/under markets and P(yes) for anytime TD, scored against the outcome. |
| The paired set | Rungs where **both** give a probability and the outcome is graded. |
| Log loss | −[y·ln p + (1 − y)·ln(1 − p)], with p clipped to [1e-12, 1 − 1e-12] for both alike. |
| The test | d = champion loss − model loss per paired prediction, **pooled over both leagues and all markets**. It is CR1 cluster-robust **by game** (league + event id), one-sided mean d > 0, Student's t on G − 1 degrees of freedom. It uses the one existing implementation, `mlb_refit.paired_test_clustered`. |
| Verdict | **QUALIFIES** if n ≥ 500, mean d > 0 and p < 0.05. **NOT YET MEASURABLE** if n < 500. Otherwise **DOES NOT QUALIFY**. Per-league and per-market figures are reported beside it, never as it. |

## 7. What runs when

- `fb_props_model.py` rides the existing `card-fb` mode, after
  `fb_model`. It writes `data/<league>/latest/fb-props-model.json`, which
  gets a freshness row, so `converge` rebuilds it after a missed run.
- Every run re-scores the whole walk-forward from stored data, so a newly
  finished week is added automatically.
- ⛔ It never edits the card, `card_fb.py`, or a published pick.

## Changelog

- **2026-09-24:** written and committed before any scoring code.
- **2026-09-24, first run: a mistake in this design, fixed.** §3
  regressed √yards on inputs averaged in **raw** yards. A straight line
  from raw yards to √yards extrapolates wildly for high-volume players:
  Derrick Henry's recent 144 and 162 projected 218 yards on a 96.5 line,
  at P = 0.996. **Root cause:** I fixed the target's scale in §3 and never
  put the inputs on the same scale. **Fix:** for the yardage markets, the
  stat and usage averages (inputs 1, 3–6) and the opponent input (9) are
  taken on the same √ scale as the target. Counts are unchanged.
  - Both runs are reported. The first did **not** qualify (n = 2,556,
    one-sided p = 0.088); nor does the fixed one (p = 0.069).
  - Guard: a mutation in `test_fb_props_model.py`.
- **2026-09-24: a labelling mistake in the build, fixed.** When the other
  league's file was missing, `build()` reported one league's figure as
  "the pooled verdict", and college alone read QUALIFIES while the true
  pooled answer did not. One league is now never a verdict ("INCOMPLETE —
  needs both leagues"). Guard: a mutation.
- **Seen, and deliberately NOT acted on** (changing it now would be tuning
  after seeing results):
  - Stage 1 predicts overs too rarely in every over/under market (NFL
    passing yards: 0.31 stated against 0.48 observed).
  - On its own, stage 1 does worse than a coin flip on most markets. The
    market's own de-vigged probability beats both models everywhere.
  - Anytime TD is well calibrated (0.19 against 0.19 in the NFL).
- ⚠️ **A limit of the live picks:** the §7 inputs (18–20) sit on a game's
  own log row, which exists only after the game. The graded record has
  them; this week's live picks carry 0 for them.
