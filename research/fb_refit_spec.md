# T65 — the football game model's weekly champion vs challenger

Status: APPROVED BY SAM 2026-10-12 — pre-registered by Cowork 2026-10-12 05:48Z, before any challenger result; sections 2 and 3 copied unchanged

## 1. What it asks

Sam, 2026-10-12: *"how can we make sure the model learns each week and analyzes
all data efficiently and accurately ... how do we make sure the model knows these
teams better than they do or in the least is learning how to do so or working
towards doing so."* He chose all three: a weekly scoreboard against the books,
better data, and a weekly champion-vs-challenger contest. And: *"we can't have any
recurring tasks or weekly checks or anything in Claude ... What we can do is set
something up in GitHub."* So it runs on GitHub Actions (`fb-refit.yml`), reads
only the repo's own files and never calls Claude. Code: `fb_challengers.py`,
`fb_refit.py`.

## 2. The rule (frozen)

- **Champion:** the live football game model (fb_model on main), named per league
  in ONE place: `fb_model.CHAMPION = {"nfl": None, "ncaaf": None}`. None is
  today's model, unchanged.
- **Challengers** (frozen; any change is a new challenger with a new name):
  - **E (NFL):** one more input, the opponent-adjusted EPA margin. Entries from
    `data/nfl/latest/def-epa-<season>.json.gz`: each `by_team[defence][game_id]`
    is what that offence (`opp`) did against that defence (`epa_per_play`,
    `plays`). Game date, home and neutral come from the schedule by game_id. For
    every Monday, solve on the entries whose game kicked off (UTC date) before
    that Monday: epa = base + home edge x (offence at home and not neutral) +
    Off_offence - Def_defence; weight 0.5 ^ (days before the Monday / 150); ridge
    1 on every Off and Def term, none on base or home edge; pure-Python
    Gauss-Seidel warm-started from the week before, as `fb_model.solve_ratings`
    does. EPA margin in points = (home edge x home + Off_home - Def_away -
    Off_away + Def_home) x the mean `plays` of the entries in that solve. Inputs
    appended after the champion's: spread (EPA margin - line) / 10, moneyline
    EPA margin / 10. Totals unchanged. A team with no earlier entry gives 0.
  - **P (college):** the same as E, from CFBD /plays `ppa`: per offence per game,
    the mean ppa over that game's plays that carry one. All games in the file,
    FBS and FCS alike.
  - **T (college):** CFBD /talent for each season, z-scored within that season's
    file; a team missing from it gets 0. The champion's margin solve gains one
    unpenalised term: margin = home edge x home + beta x (z_home - z_away) +
    R_home - R_away, each game's z from its own season, beta solved in the same
    weighted Gauss-Seidel (ridge 1 on R only, same weights). A row's own margin
    uses its own season's z. Own total unchanged. Spread and moneyline.
  - ⛔ **R (college returning production)** was pre-registered and then
    WITHDRAWN before registration: on the 2025+2026 history it was worse (2026
    moneyline log loss 0.551 -> 0.572). Do not build it.
- **A prediction:** one final game the model prices (`fb_model.schedule_games`)
  x one market the challenger changes (E, P, T: spread and moneyline), at the
  line the champion is labelled against (`fb_model.label`). Champion and
  challenger are each fitted by `fb_model.fit(..., zmax=ZMAX)` on rows before
  that week's Monday, exactly walk_forward's cut. Log loss with p clipped to
  1e-12.
- **d** = champion log loss - challenger log loss, mean over predictions,
  cluster-robust by game, one-sided (`mlb_refit.paired_test_clustered`).
- **Scored weeks:** ONLY from the challenger's registration Monday on. That is
  the first Monday after this PR's last commit (2026-10-19 if finished before
  then), or the first Monday on or after the day its data first exists on main
  for every season it reads, whichever is later. Earlier weeks are its HISTORY,
  reported for information only.
- **Withdrawal** (P and T only; fixed before their data exists): if the
  history's mean d < 0 with one-sided p < 0.05 in the wrong direction (the same
  test on -d), the challenger is WITHDRAWN: reported, never scored.

## 3. The verdict (frozen)

- Every Monday: **WINS** if at least 300 scored predictions, mean d > 0 and
  p < 0.01 / (the number of challengers registered, not withdrawn, in that
  league). **NOT YET MEASURABLE** below 300. Otherwise **NOT YET**.
  (Why 0.01: it is checked weekly. Cowork simulated seasons with no real
  difference: a weekly p < 0.05 lets a fluke win 10% (NFL) / 16% (college) of
  seasons; p < 0.01, 2% / 4.5%.)
- **When one WINS:** the weekly job pushes ONE branch
  `fb/champion-<lg>-<name>-<date>` whose only change is that league's CHAMPION
  entry (skip if any `fb/champion-<lg>-*` branch already exists on origin). It
  never opens a PR and never touches main. The Monday email tells Sam. When Sam
  merges it, the card uses the challenger: card_method gains "+game-<name>", so
  the Track Record and T64 open a new method, and every remaining challenger's
  scored weeks restart at the next Monday against the new champion.

## 4. How it is built (not frozen)

- `fb_refit.py weekly`, Mondays 09:47 UTC (`docs/upload/fb-refit.yml`): builds
  each league's rows once (`fb_model.build_rows`), attaches every challenger's
  number (`fb_challengers.attach`), runs the contest and the scoreboard, writes
  `data/<lg>/latest/fb-refit.json`, and pushes the WINS branch.
- "The day its data first exists on main" is the first commit that added each
  file (`git log --diff-filter=A`; the workflow checks out full history).
- A champion switch is noticed by the first weekly run after the merge (the
  report's stored `champion` differs); `champion_since` is the first Monday on
  or after that run, and scored weeks restart there.
- The scoreboard (a report, it decides nothing), 2026 season, the champion's
  walk-forward predictions: the gap to the books per market (moneyline: the
  row's pml; spread and total: 0.5) with a 90% interval and a 4-week trend; the
  average miss in points; lines moved toward the model (only snapshots pulled on
  or after the row's Monday 00:00Z, at least two; first vs last); said vs hit.
- T's talent z uses each season file's population SD.

## Changelog

- 2026-10-12 — written from the rule as pre-registered by Cowork 05:48Z, with
  Cowork's reference numbers reproduced on commit 8581f138 before the PR.
