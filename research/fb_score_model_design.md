# The score-first football game model — design, fixed before the run

Written 2026-10-15 and committed on its own, before any code that scores it
exists. `fb_score_model.py` and `fb_matchups.py` run exactly these settings;
`test_fb_score_model.py` fails if a constant in the code differs from this
page. ⛔ Nothing here is tuned on the backtest: it runs once and is reported.

## In plain English (for Sam)

- Sam, 2026-10-15: *"your goal is to predict the outcome of each game, your
  trying to predict the score of both team ... analyzing both teams average
  points scored, average points allowed, and give the home team a small +1.5
  edge ... factored afterwards should be the player stats ... how teams play
  against certain stats like passing rushing receiving"*.
- So this model predicts BOTH teams' points, and the spread, total and
  moneyline chances come from that one predicted score.
- Step 1: each team's points scored and allowed, adjusted for who it played,
  plus a home edge MEASURED from past games (Sam's fixed +1.5 already
  competes as challenger AV in the weekly contest and is not touched here).
- Step 2: the matchup layer — passing offence against passing defence,
  rushing against rushing, and both teams' pace — moves each side's points.
- ⛔ Report only. It changes no pick, chance, card row or page. Switching the
  game-line picks to it is Sam's decision after he sees the backtest.

## 1. The team-unit tables (`fb_matchups.py`, shared)

- **Points**: every final game of every stored `schedule-<season>`, all
  divisions — the list `fb_model.rating_games` already reads.
- **Every other unit**: every final scheduled game whose two offences both
  appear in the stored `players-<season>` logs (NFL: every game; college:
  FBS against FBS, the only games both sides are logged). Per team-game:
  `pass_yds` (sum of passing yards), `rush_yds`, `rec_yds_WR/TE/RB` (receiving
  yards by the player's position that game, else his listed one), `pass_att`,
  `rush_car`, `plays` = pass attempts + carries; NFL also `tgt_WR/TE/RB`.
- **One equation per side**: value(offence X against defence Y) = base + home
  edge × (X at home and not neutral) + O_X − D_Y.
- **Weighting and shrinkage — the same as fb_model's own ratings, by reusing
  its solver (`fb_model.solve_ratings`), never a copy**: weight 0.5 ^ (days
  before the as-of Monday / 150); ridge 1 on every team term, none on the
  base or the home edge — one league-average pseudo-game, so a team with n
  weighted games keeps n / (n + 1) of its difference from average. Points
  converge to 1e-10, other units to 1e-7.
- **Point in time**: a table "as of" a day reads only games dated before
  that day's Monday.
- **API**: `unit_for(team, unit, as_of)` = base + O (per game against an
  average defence, neutral site); `unit_allowed(team, unit, as_of)` = base −
  D; `expect(offence, defence, unit, as_of, home)`; `home_edge(unit, as_of)`.
- `allowed-by-position-<season>` is a season-to-date total, not point in
  time, so it is never an input; the tables' raw per-game allowed yards are
  reconciled against it and the difference is reported.

## 2. The score model (`fb_score_model.py`)

- **Games**: `fb_model.build_rows` (NFL every game, college FBS against FBS),
  each predicted as of its own week's Monday.
- **Base score**: home = base + home edge × (not neutral) + O_home − D_away;
  away = base + O_away − D_home, from the points table.
- **Matchup layer**, per side (offence X, defence Y): pass = O_X − D_Y on
  `pass_yds`; rush = the same on `rush_yds`; pace = (O_home − D_away) +
  (O_away − D_home) on `plays`, the same for both sides. A team missing from
  a unit table counts 0 (average).
- Side points = base + b_pass × pass + b_rush × rush + b_pace × pace. The b's
  are fitted each week on every earlier final game's two sides (target: real
  points − base score, both point in time), inputs scaled to unit root mean
  square, ridge 100, no intercept; under 200 earlier sides every b is 0.
- **Margin** = home − away; **total** = home + away.
- **Spread of errors**: sigma_margin and sigma_total = root mean square of
  (real − predicted) over every earlier final game's point-in-time
  prediction; under 100 such games, no chance.
- **Chances (the score curve)**: P(over the line L) = 1 − Φ((L − predicted) /
  sigma); spread: the margin against M (home covers); total: the total
  against T; moneyline: the margin against 0 (home wins).
- **Calibrated version, beside it**: the same with sigma × k, one k per
  market, chosen each week from 1.00, 1.05, …, 3.00 to minimise log loss over
  every earlier labelled game at its own line; under 100 such games, k = 1.

## 3. The backtest (run once, reported in the PR)

- Every final 2025 and 2026 game, walk-forward by week.
- **Point errors** (mean absolute and root mean square) for margin and
  total: the score model, fb_model's own ratings (own margin, own total) and
  the closing line, on games all three have.
- **Log loss** at the line fb_model labels each game against (its `M`, `T`;
  the moneyline where it has a price), for the score curve, the calibrated
  curve and fb_model's own weekly fit (the same training as
  `fb_model.walk_forward`), on games all three price; plus the books'
  de-vigged moneyline. A coin flip scores 0.693.
- **Calibration** by band of the chosen side's chance: 50–55, 55–60, 60–65,
  65–70, 70+: games, average stated chance, real hit rate.
- **ROI of picks at 50%+**: per game and market, every side whose chance at a
  quote's own line is 50% or more, at the best price among them; graded
  twice, at Sam's three books' pre-kickoff prices (archived from September
  2026) and at closing prices (college spreads and totals at an assumed
  −110, labelled); pushes out; ROI = profit / graded picks at 1 unit. The
  same rule for all three versions.

## 4. Output

`data/<lg>/latest/fb-score-model.json`, rebuilt by every `card-fb` run after
`fb_model.build` and never raising: the predicted score and chances for every
unplayed game in the next 8 days beside fb_model's chances at the same lines,
this week's settings (home edge, b's, sigmas, k's), and the backtest. A
freshness row keeps it current. ⛔ No pick, chance, card row or page reads it.

## Changelog

- 2026-10-15 — written before any code (this commit).
