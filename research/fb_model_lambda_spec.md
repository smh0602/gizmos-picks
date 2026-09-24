# Football game model: a self-chosen strength setting (λ)

Status: APPROVED BY SAM 2026-09-24 — rule in section 2 pre-registered by Sam before any result under it was computed; section 3 fixed by Claude before any result

⚠️ **Written and committed before any scoring code exists.** The commit
that adds this file adds no code that computes a result under it. The
rule (section 2) and its definitions (section 3) are hashed by
`test_prereg_gate.py`, so neither can be edited after a result is seen.

## In plain English (for Sam)

- Today's game model uses one fixed strength setting, λ = 1.0. It decides
  how hard the model is pulled back toward "the market already knows".
- The new version picks its own λ **every week**, using only games already
  played. It tries seven values and keeps the one that would have
  predicted the earlier weeks best.
- It replaces today's setting **only** if it predicts better by a margin
  that is unlikely to be luck (one-sided p < 0.05). The test counts each
  game once, and needs at least 500 predictions.
- **This PR never switches the live model**, whatever the result. You
  decide.

## 1. Scope

- **Both leagues** (NFL, college) and **all three markets** (spread,
  total, moneyline) in `fb_model.py`.
- **The only thing that changes is λ.** The inputs, labels, pick rule,
  prices, weeks and the 150-game minimum stay exactly as
  `research/fb_model_design.md` fixes them.
- **Background:** `research/fb_model_closing_investigation.md` found no
  bug, and found the model worse than a coin flip on NFL spreads. Sam:
  *"Do not change anything else about the model because of that result."*

## 2. The rule `[Sam, 2026-09-24, pre-registered before any result under it was computed]`

> "The grid: λ in {0.1, 0.3, 1, 3, 10, 30, 100}. Everything else stays the
> same: inputs, labels, pick rule and prices."
>
> "The weekly choice: each week, for each league and market, choose λ
> using only games before that week. Run an inner walk-forward over the
> earlier weeks and take the λ with the lowest mean log loss. Break ties
> toward the larger λ. With fewer than 4 earlier predicted weeks, use
> λ = 1.0, today's value."
>
> "The replacement rule: the self-chosen version replaces today's fixed
> λ = 1.0 only if its per-prediction log loss is lower, with one-sided
> p < 0.05, standard errors clustered by game, and at least 500
> predictions pooled over all leagues and markets. Score it on the
> closing-line walk-forward, which has the most games."
>
> "Do not switch the live model in this PR, even if the new version
> qualifies. I decide."

## 3. Definitions fixed by Claude before any result `[2026-09-24]`

⚠️ **Not approved by Sam. Frozen by Claude so nothing can be tuned after
seeing a result, and disclosed here so Sam can overrule any of it.**

| | |
|---|---|
| λ | The ridge strength in `fb_model.fit` (`ridge=`), applied to standardised inputs with the intercept unpenalised, exactly as today. Today's value is `fb_model.RIDGE` = 1.0. |
| Weeks | Monday to Sunday, in date order across 2025 and 2026, as `fb_model.walk_forward`. The model for week W is fitted on every game that kicked off **before W's Monday**. |
| A predicted week | A week in which today's model (λ = 1.0) fits: at least 150 labelled games precede it, both outcomes occur, and the fit solves. It must also have at least one labelled game to predict. The same condition is counted per league and market. |
| The inner walk-forward (week W) | For every predicted week w **before** W, and every λ in the grid, the model is fitted on games before w's Monday. It then predicts every labelled game in w, **on the model's own training label**: home margin against the training line, points against the training total, or home win (design §2–3). The training label is used because it exists for every game and is what the model is fitted to. All these predictions are pooled over every such w, and each λ's mean log loss is taken over them. |
| The weekly choice | The λ with the lowest pooled mean log loss. Values within 1e-12 of each other count as tied, and a tie goes to the **larger** λ. A λ whose fit failed in any counted inner week is dropped from that week's choice. **With fewer than 4 predicted weeks before W, λ = 1.0.** |
| The self-chosen version, week W | `fb_model.fit` with `ridge = λ chosen for (league, market, W)`, on the same training games as today's model. If that fit fails, it makes no prediction that week. |
| The scored predictions (the decision set) | The closing-line walk-forward. For each league, market and predicted week, every final game that has a **closing line** for that market: nflverse's line for the NFL, CFBD's stored line for college. The line is exactly what `fb_model.closing_lines` returns. Where it returns none (for example an NFL spread or total whose price is not stored), that game is not scored in that market. The model's probability of the home side covering, the over, or a home win is taken **at that closing line**, and the outcome is judged against the same line. A push or a tie is left out. This is **every** such game, not only the picks: log loss scores a probability, and the pick rule would give the two versions different sets of games. The price plays no part in log loss. |
| The paired set | The scored predictions where **both** versions made one. The p-value is computed on this set alone. |
| Log loss | −[y·ln p + (1 − y)·ln(1 − p)], with p clipped to [1e-12, 1 − 1e-12] for both versions alike. |
| The test | d = today's loss − the self-chosen loss, for each paired prediction, so d > 0 means the self-chosen version predicted better. The estimand is the mean of d over every paired prediction, **pooled over both leagues and all three markets**. Its standard error is **cluster-robust by game**: every prediction from one game (league + game id, up to three markets) is one cluster. CR1: V = G/(G−1) · Σ_g (Σ_{i∈g} (d_i − mean))² / n². The test is one-sided, mean d > 0, using Student's t on **G − 1** degrees of freedom. It uses the one existing implementation, `mlb_refit.paired_test_clustered`. |
| Verdict | **QUALIFIES** if n ≥ 500, mean d > 0 and p < 0.05. **NOT YET MEASURABLE** if n < 500. Otherwise **DOES NOT QUALIFY**. |
| Reported beside the verdict, NOT part of it | Mean log loss for each version, per league and market. Both published records (your books, and closing lines), per league and market, under **each** version: picks, hit rate, break-even and 95% range, clustered by game, with the same pick rule and prices as today. The λ chosen for every week, league and market. ⚠️ Per-league and per-market p-values are not computed; the rule is the pooled one. |

## 4. What runs

- `fb_model_lambda.py` scores both versions exactly as sections 2–3
  define. It reads `fb_model.py`'s functions and changes none of them.
  ⛔ It never writes `data/<league>/latest/fb-model.json`, and it never
  changes `fb_model.RIDGE`.
- The result is recorded in `research/fb_model_lambda_run_<date>.json`,
  and reported in the PR.
- ⛔ **No switch.** If the verdict is QUALIFIES, the PR says so and Sam
  decides. Switching is a separate PR.
- No new spend and no cron changes.
- ⚠️ **Which data the recorded run reads.** College reads only stored
  data. The NFL reads nflverse's closing prices and the signal 6–7 inputs
  from files already downloaded, free, with Sam's permission. The stored
  copies gain those fields only at the next scheduled builds. These are
  the same inputs PR #150's closing record was computed from.

## Changelog

- **2026-09-24:** written and committed before any scoring code. Rule by
  Sam; definitions in section 3 by Claude.
