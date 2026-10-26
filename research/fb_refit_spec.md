# T65 — the football game model's weekly champion vs challenger

Status: Sam approved the plan 2026-10-12 (all three parts; 'go ahead') and asked for more on 2026-10-14. The definitions in sections 2, 3 and 3a are Cowork's, pre-registered (T65 2026-10-12 05:48Z, T66 2026-10-14) and disclosed for Sam to overrule.

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

## 3a. T66 — two more challengers (frozen)

Pre-registered by Cowork 2026-10-14 (claude/pro-plan-readiness-2026-10-06.md,
T66). ⚠️ Unlike T65's, these two were designed AFTER Cowork saw their history
(inputs that added noise on past games were dropped), so ONLY games played after
registration count, exactly as §2 already requires; their history is reported
for information only.

- **S (NFL):** the champion's inputs WITHOUT head-to-head and WITHOUT signal 9.
  Spread and moneyline keep: own rating term, form, possession, personnel (out),
  neutral, dome. Total keeps: own total term, form, defence, neutral, dome. All
  three markets. (Index form, today's champion lists: spread and moneyline
  [own, h2h, form, poss, out, neutral, dome, +s9 NFL] -> keep [0,2,3,4,5,6];
  total [own_t, h2h_t, form_t, def, neutral, dome, +s9 NFL] -> keep [0,2,3,4,5].)
- **TS (college):** challenger T's talent margin in place of the own margin, and
  ONLY these inputs. Spread: (T margin - line) / 10, neutral, dome. Moneyline:
  T margin / 10, neutral, dome. Total: (own total - line) / 10, neutral, dome.
  All three markets. (Index form: spread and moneyline keep [0,5,6] with T's
  margin in slot 0; total keeps [0,4,5].)
- **Registration:** the first Monday after the PR that adds them is last
  committed (2026-10-19 if before then); for TS also no earlier than the first
  Monday its talent files exist on main (§2).
- **Everything else as §2 and §3:** a prediction is one final priced game x one
  market S or TS changes (all three); fitted by `fb_model.fit(..., zmax=ZMAX)` on
  rows before that week's Monday; d, the clustered one-sided test, at least 300
  scored predictions, p < 0.01 / (challengers registered and not withdrawn in
  that league: NFL E and S = 2, college P, T and TS = 3), the WINS branch and
  Sam's merge. ⛔ No withdrawal rule for S or TS.

## 3b. T68 — Sam's averages and weather (frozen)

Sam, 2026-10-15, about his predicted-scores formula (a team's points per game
averaged with its opponent's points allowed per game, plus weather, plus about
1.5 points for the home team): *"should be just apart of the model and system we
have now, learn to implement this as well"*. Pre-registered by Cowork 2026-10-15
(claude/pro-plan-readiness-2026-10-06.md, T68 and T68b). On its own the formula
is less accurate than the model (T67) and as one more input it changes almost
nothing on past games (T68 RESULTS), so it joins as frozen challengers and the
weekly fit learns its weight. Only games after registration count (§2).

- **AV (NFL) and AVC (college):** the champion's inputs exactly as they are,
  PLUS one appended input: spread (sam_m - line) / 10, moneyline sam_m / 10,
  total (sam_t - line) / 10, each at the line being priced; no sam number -> 0.
  All three markets. They read only the stored schedules (no file of their own).
  - Per row, point in time: only games dated (start[:10]) before the row's
    Monday count. For each team, points scored (PF) and allowed (PA) per game
    over every final scored game in the stored schedules of the row's season,
    any opponent, every division stored. Fewer than 3 such games: topped up to 3
    with the team's latest games of the earlier season. No earlier game at all:
    None.
  - h = 0 at a neutral site, else 1.
    sam_m = (PF_home + PA_away - PF_away - PA_home) / 2 + 1.5 x h;
    sam_t = (PF_home + PA_away + PF_away + PA_home) / 2.
- **WX (NFL) and WXC (college):** TOTALS ONLY: the champion's total inputs PLUS
  wind / 10, wind = the "wind" (mph) of the "last" forecast stored for that game
  id in data/<lg>/latest/weather-2026.json.gz (fb_weather.py). An indoor entry,
  no entry, no "last" or no wind -> 0. Spread and moneyline unchanged. They read
  weather-2026 only (no 2025 forecasts exist), so registration looks for that
  file alone.
- **Registration:** the first Monday after the PR that adds them is last
  committed (2026-10-19 if before then); for WX and WXC also no earlier than the
  first Monday weather-2026 exists on main (§2). ⛔ No withdrawal rule.
- **Counts and bar:** NFL E, S, AV, WX = 4 -> p < 0.01 / 4 = 0.0025; college P,
  T, TS, AVC, WXC = 5 -> p < 0.01 / 5 = 0.002 (fewer if any is withdrawn, §3).
  Everything else as §2 and §3: at least 300 scored predictions, the WINS branch
  and Sam's merge.

## 3c. T69 — injuries on both sides, Sam's averages for totals, rest (frozen)

Sam, 2026-10-15, after the measured breakdown of his averages (NFL moneyline
worse, NFL totals slightly better, college margins worse; the NFL game model
trains on about 361 games): *"do all changes"*, and on injuries: *"injuries
should've always been a factor on both sides of the ball"*. Defined here before
any of these challengers' results were computed. Only games after registration
count (§2).

- **IN (NFL only), injuries on both sides of the ball.** For each team and game
  (season, week): the players its own injury report for that week lists **Out or
  Doubtful** (data/nfl/latest/injuries-<season>.json.gz; Questionable is not
  counted). Each player's weight = his mean snap share over his last 3 games
  logged for that team (data/nfl/latest/players-<season>.json.gz) dated before
  the game day: his offensive share (snap_pct) for an offensive player, his
  defensive share (def_pct, nflverse's defense_pct) for a defensive player; no
  such game -> 0.
  - qb_out = 1 when the team's starting QB in its most recent game before this
    one (most pass attempts) is listed Out or Doubtful, else 0.
  - off_out = the summed weights of listed offensive players other than QBs
    (RB, FB, WR, TE, T, G, C and their variants).
  - def_out = the summed weights of listed defensive players (DE, DT, NT, LB and
    variants, CB, S and variants, DB).
  - Inputs appended after the champion's: spread and moneyline (qb_out_away -
    qb_out_home), (off_out_away - off_out_home), (def_out_away - def_out_home);
    total (qb_out_home + qb_out_away), (off_out_home + off_out_away),
    (def_out_home + def_out_away). No report for a team-week -> 0 for that team.
  - ⚠️ College: no injury report exists in any data this repo stores (CFBD
    publishes none), so there is no college injury challenger.
- **AT (NFL) and ATC (college), Sam's averages for totals.** TOTALS ONLY: the
  champion's first total input becomes ((own total + sam_t) / 2 - line) / 10,
  sam_t as §3b defines it; when sam_t is None the champion's inputs are
  unchanged. Spread and moneyline unchanged.
- **RS (NFL) and RSC (college), rest.** Each team's rest = days from its
  previous stored game (any season, start[:10]) to this game's day, capped at
  14; no previous game -> 14. Spread and moneyline: one input appended,
  (rest_home - rest_away) / 7. Totals unchanged.
- **Registration:** the first Monday after the PR that adds them is last
  committed (2026-10-19 if before then); for IN also no earlier than the first
  Monday its injuries files exist on main (§2). ⛔ No withdrawal rule.
- **Counts and bar:** NFL E, S, AV, WX, IN, AT, RS = 7 -> p < 0.01 / 7; college
  P, T, TS, AVC, WXC, ATC, RSC = 7 -> p < 0.01 / 7 (fewer if any is withdrawn,
  §3). Everything else as §2 and §3.

## 3d. T70 — more seasons (frozen)

Sam, 2026-10-15, *"do all changes"*: the NFL game model learns from about 361
games (2025-26, the only seasons stored) and college from about 1,040. Defined
here before any result.

- **History data** (written once while missing by the daily run, never into
  `latest/`, so the champion's ratings are untouched):
  - NFL 2018-2024: `data/nfl/history/schedule-<season>.json.gz`, built by
    `nfl.build_schedule` from nflverse's games file (free); Oakland's `OAK` is
    stored as `LV`.
  - College 2023-2024: `data/ncaaf/history/schedule-<season>.json.gz`
    (`cfb.build_schedule`, CFBD /games) and `lines-<season>.json.gz` (CFBD
    /lines, regular season, one line per game chosen by t60r's PROVIDER_ORDER,
    stored in t60r's shape). Every CFBD call priced first by
    `cfbd_budget.preflight` (2 + 1 per season).
- **H (NFL) and HC (college):** inputs, every market: spread (own margin - line)
  / 10, moneyline own margin / 10, total (own total - line) / 10, then neutral and
  dome. Own margin and total by fb_model's frozen own-ratings solve
  (`own_ratings`, `own_numbers`) over every final game in `latest/` AND
  `history/` (one copy per date, home, away), dated before the row's Monday.
  Trained on the 2025-26 rows plus one row per final history game (college FBS vs
  FBS only), each labelled at its closing line by `fb_model.training_line`
  (NFL: nflverse's closing lines; college: the lines file). Only these inputs,
  because the champion's other inputs do not exist for the history seasons.
- **Registration:** the first Monday after the PR that adds them is last
  committed (2026-10-19 if before then), and no earlier than the first Monday its
  history files exist on main for every history season (§2). ⛔ No withdrawal
  rule.
- **Counts and bar:** NFL 8, college 8 -> p < 0.01 / 8 (fewer if any is
  withdrawn, §3).

## 3e. T71 — the score-first model (frozen)

Sam, 2026-10-16: *"Yes, write the registration that enters the score-first model in
the weekly contest, for me to approve"*, and the same night: *"we do need this model
to be recurring week after week on its own."* Defined here before any contest
result for these two challengers. The score model's own backtest (PR #275,
`research/fb_score_model_design.md`) was run and seen first, so ONLY games after
registration count, exactly as §2 already requires; that backtest is background,
not the test.

- **SM (NFL) and SMC (college):** each row's predicted margin m and total t from
  `fb_score_model.walk_forward` as merged in PR #275, with the design's settings
  (§1-§2 there). Both sides' points come from `fb_matchups`' opponent-adjusted points
  table (fb_model's own-ratings solver: weight 0.5 ^ (days before the Monday / 150),
  ridge 1). Add the home edge that table measures on earlier games: none at a neutral
  site, and not Sam's fixed 1.5, which is AV / AVC. Add the matchup layer, ON: pass
  gap, rush gap and combined pace, its weights fitted by ridge 100 on earlier final
  games' sides, all 0 under 200 sides. Point in time: tables and weights read only
  games dated before the row's Monday. ⛔ What SM / SMC read is frozen with them:
  `fb_score_model.py` and `fb_matchups.py` as merged in #275. A later change to what
  those compute (the props model may want one) goes into a copy or a new function,
  never into what SM / SMC read; `test_fb_refit.py` pins their numbers on a planted
  league.
- **Inputs, ONLY this one, every market:** spread (m - line) / 10, moneyline
  m / 10, total (t - line) / 10, at the line being priced; no prediction (a team
  with no earlier game) -> 0. §2's fit (`fb_model.fit(..., zmax=ZMAX)` on rows
  before the Monday) turns it into each market's chance, so the curve's centre and
  slope are re-learned from earlier games every week. ⛔ The report's own sigma, its
  k grid (1.00-3.00) and that grid's 3.0 cap are NOT used. This is neither the raw
  score curve nor the k-calibrated one; it is the predicted score fed to §2's fit.
- ⚠️ All three markets start from one predicted score, but §2 fits each market on
  its own, so SM's spread and win chances can disagree, ~~in a rare game~~ and often
  do `[2026-10-16, measured on the history after this section was first written]`:
  over games graded on both markets, the side laying points was likelier to cover
  than to win in 65 of 198 NFL games and 86 of 863 college games (today's champion:
  52 of 198 and 137 of 863). Pricing all three from one curve with no per-market fit
  would mean changing §2.
- **Training window:** the champion's: every labelled 2025-2026 row
  (`fb_model.build_rows`, `fb_model.SEASONS`) dated before the Monday. The score
  model reads the stored schedules and player logs of those seasons.
- **Registration:** the first Monday ~~on or after~~ AFTER the day this section
  reaches main (the merge day), and no earlier than 2026-10-19: a Monday merge counts
  from the next Monday, so no game that kicked off before the merge is ever scored
  (§2's own "the first Monday after"). `fb_refit.registration` reads the
  merge day from git: the first commit on main's first-parent line whose
  `fb_challengers.py` adds the entry. ⛔ No withdrawal rule.
- **Counts and bar:** NFL E, S, AV, WX, IN, AT, RS, H, SM = 9; college P, T, TS,
  AVC, WXC, ATC, RSC, HC, SMC = 9 -> p < 0.01 / 9 (fewer if any is withdrawn, §3).
  The bar gets stricter for every challenger (0.01 / 8 = 0.00125 -> 0.01 / 9 =
  0.00111), never looser. Everything else as §2 and §3: at least 300 scored
  predictions, the WINS branch and Sam's merge.

## 3f. T72 — the matchup grade: who a team has played (frozen)

Sam, 2026-10-26: *"one thing were missing is.... matchup grade. i feel like we aren't
looking at how good teams actually are just the season averages ... the premise is to
make sure the model understands bad teams and good teams."* Shown what the model
already does (every team rated against the opponents it played) and what it misses,
he said: *"let's do all of this, if any is repeating don't do it twice"*. Defined here
before any result: no history, fit or log loss of any of these challengers was
computed before this section was written. Only games after registration count (§2).

- **The ratings they read.** For a row, s = the champion's own-ratings solve for the
  row's Monday (`fb_model.own_ratings` over `fb_model.rating_games`: every final game
  of every stored `latest/` schedule, all divisions, dated before that Monday; weight
  w = 0.5 ^ (days before the Monday / 150); ridge 1): hfa, base, hpe and each team's
  R, O and D. "A team's games" below are those games, each with its w. Nothing dated
  on or after the row's Monday is read.
- **Above average**, at the row's Monday: R_t above the plain mean of R over the
  reference teams in s; likewise O_t above the mean O, and D_t above the mean D (a
  higher D holds opponents to fewer points). Reference teams: NFL, every team in s;
  college, every team in s that any stored schedule lists with class "fbs" (FCS and
  below stay in the solve and are compared against the FBS mean).
- **CL (NFL) and CLC (college), class: how a team does against good opponents beyond
  what its rating says.** For each team t, over its games against an opponent o, with
  f = +1 when t was the home side at a non-neutral site, -1 when o was, 0 at a neutral
  site, and [x] = 1 when x is above average, else 0:
  - C_t, margin class, over games where [R_o]: residual = t's margin -
    (hfa x f + R_t - R_o).
  - CO_t, offence class, over games where [D_o]: residual = t's points -
    (base + hpe x [t home, not neutral] + O_t - D_o).
  - CD_t, defence class, over games where [O_o]: residual = points t allowed -
    (base + hpe x [o home, not neutral] + O_o - D_t).
  - Each = sum(w x residual) / (sum(w) + 10); no such game -> 0. The 10 is fixed here,
    not tuned: a team's class number counts half once it has ten full-weight games
    against good opponents.
  - Row (home H, away A): cl_m = C_H x [R_A] - C_A x [R_H];
    cl_t = CO_H x [D_A] + CD_A x [O_H] + CO_A x [D_H] + CD_H x [O_A]. Either team not
    in s -> both 0.
  - Inputs appended after the champion's: spread cl_m / 10, moneyline cl_m / 10,
    total cl_t / 10. All three markets.
- **WL (NFL) and WLC (college), the resume: wins and losses, weighted by who they came
  against.** For every Monday, a Bradley-Terry fit on the same games and weights:
  P(home side wins) = 1 / (1 + exp(-(a x h + B_home - B_away))), h = 0 at a neutral
  site, else 1; y = 1 for a home win, 0 for an away win, 0.5 for a tie; the score
  margin is never read. It maximises sum(w x (y log p + (1 - y) log(1 - p))) -
  0.5 x sum(B_t ^ 2) (ridge 1 on every team term, none on a), solved until no number
  moves more than 1e-10 (the champion's tolerance), warm-started from the Monday
  before. Beating a team with a high B lifts a team's B more than beating a low one,
  and losing to a low one costs more. Row: wl = a x h + B_H - B_A; a team with no
  earlier game -> 0. Inputs appended after the champion's: spread wl, moneyline wl.
  Totals unchanged.
- **MC (NFL) and MCC (college), blowouts capped.** The champion's margin equation
  (margin = hfa x h + R_home - R_away; the same games, weights, ridge 1 on R only and
  tolerance) solved with each game's margin capped at +/-21 points (NFL) or +/-28
  (college): three and four touchdowns, fixed here, not tuned. Its margin replaces the
  champion's own margin in the first spread and moneyline input: spread (capped margin
  - line) / 10, moneyline capped margin / 10. Totals unchanged.
- **AJ (NFL) and AJC (college), the raw inputs opponent-adjusted.** The champion's
  inputs with two replaced. Head-to-head stays as it is: S and TS already test
  dropping it, and that is not repeated.
  - Form (each market's third input, index 2; the champion's is raw points for and
    against over each team's last 4 games). AJ reads the same last 4: each team's
    last 4 final games dated before the row's Monday, any stored season (fewer than 2
    -> 0, as the champion). Each game is read against s: game rating = t's margin -
    hfa x f + R_o; game offence = t's points - hpe x [t home, not neutral] + D_o -
    base; game defence = base + hpe x [o home, not neutral] + O_o - points t allowed.
    Their means over those games are Rr_t, Or_t and Dr_t. form_m = hfa x h + Rr_H -
    Rr_A; form_t = (base + hpe x h + Or_H - Dr_A) + (base + Or_A - Dr_H). Inputs:
    spread (form_m - line) / 10, moneyline form_m / 10, total (form_t - line) / 10.
  - Defence (the total's fourth input, index 3; the champion's ranks each defence's
    raw yards allowed by position). AJ uses each defence's opponent-adjusted passing
    plus rushing yards allowed per game, `fb_matchups.Tables(lg).unit_allowed` of
    "pass_yds" plus "rush_yds" as of the row's Monday, ranked among every team both
    tables carry that Monday: rank = 1 + the number of teams allowing more, fraction =
    rank / teams ranked, the mean over the two defences. Fewer than 10 ranked teams, or
    a defence not ranked -> 0. Input (fraction - 0.5) x 4, as the champion's.
  - All three markets.
- **Against another champion:** CL, CLC, WL and WLC only append, so they build against
  any champion. AJ, AJC, MC and MCC replace inputs at fixed places in today's
  champion's lists, so they build only while the league's champion is None or one
  that only appends (E, P, AV, AVC, WX, WXC, IN, RS, RSC, CL, CLC, WL, WLC); otherwise
  they are NOT APPLICABLE (§4), and how they read then is Sam's to decide.
- ⛔ **What they read is frozen with them:** C, CO, CD, the resume fit, the capped
  solve and AJ's form and defence numbers are computed in `fb_challengers.py` and a
  change to any of them is a new challenger with a new name; the champion's
  `fb_model.own_ratings` and `fb_matchups.Tables` they read are already frozen (the
  champion's settings, and SM / SMC). `test_fb_refit.py` pins their numbers on a
  planted league.
- **Registration:** the first Monday AFTER the day this section reaches main (its
  merge day), and no earlier than 2026-11-02 (`fb_refit.registration`, as §3e).
  ⛔ No withdrawal rule.
- **Counts and bar:** NFL E, S, AV, WX, IN, AT, RS, H, SM, CL, WL, MC, AJ = 13;
  college P, T, TS, AVC, WXC, ATC, RSC, HC, SMC, CLC, WLC, MCC, AJC = 13 ->
  p < 0.01 / 13 (fewer if any is withdrawn, §3). Every bar gets stricter
  (0.01 / 9 = 0.00111 -> 0.01 / 13 = 0.00077), never looser. Everything else as §2 and
  §3: at least 300 scored predictions, the WINS branch and Sam's merge.
- Not here, on purpose: pass-vs-pass and run-vs-run matchups (SM and SMC already test
  them), and the player props' opponent numbers (there is no weekly props contest, and
  earlier attempts to adjust them failed; that is its own registration, later).

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
- `[2026-10-16]` A challenger whose frozen definition cannot be built against the
  current champion is reported NOT APPLICABLE that week (still counted in §3's
  divisor, so every bar stays as strict), never a crash: S's and TS's §3a inputs are
  indexes into today's champion's lists, and H, HC, SM and SMC have shorter lists.
  How S and TS should read against another champion is Sam's to decide.
  `[2026-10-26]` AJ, AJC, MC and MCC likewise (§3f).

## Changelog

- 2026-10-12 — written from the rule as pre-registered by Cowork 05:48Z, with
  Cowork's reference numbers reproduced on commit 8581f138 before the PR.
- 2026-10-14 — §3a T66 (S, TS) added from Cowork's pre-registration; §2 and §3
  unchanged (test_prereg_gate.py hashes them on their own too).
- 2026-10-14 — Status line reworded (~~"APPROVED BY SAM 2026-10-12 — ..."~~): Sam approved the plan, not each definition; the definitions are Cowork's, pre-registered and disclosed for him to overrule. Sections 2, 3 and 3a and their hashes are unchanged.
- 2026-10-15 — §3b T68 (AV, AVC, WX, WXC) added from Cowork's pre-registration of Sam's averages and weather; §2, §3 and §3a unchanged (test_prereg_gate.py pins everything before §3a and before §3b on its own).
- 2026-10-15 — §3c T69 (IN, AT, ATC, RS, RSC) added at Sam's instruction ("do all changes"), defined before any of their results; §2 to §3b unchanged and pinned.
- 2026-10-15 — §3c corrected BEFORE any result: the stored logs held only offensive snap shares, so every defender weighed 0; defenders are weighed by their defensive share (def_pct, now stored by nfl.py; 2025 rebuilt once by the daily run).
- 2026-10-15 — §3d T70 (H, HC: more seasons) added at Sam's instruction, defined before any result; §2 to §3c unchanged and pinned.
- 2026-10-16 — §3e T71 (SM, SMC: the score-first model) added at Sam's instruction, defined before any contest result for them; §2 to §3d unchanged and pinned. Named SM / SMC, not SF: SF is the 49ers' code in this repo.
- 2026-10-16 — §3e corrected before Sam's approval, after an independent review: registration is the first Monday AFTER the merge day (a Monday-evening merge would have scored that night's game after kickoff); the coherence sentence was wrong ("a rare game") and now gives the measured numbers; SM / SMC's code is frozen with them. §4 gains the NOT APPLICABLE stopgap. §2 to §3d unchanged.
- 2026-10-26 — §3f T72 (CL, CLC, WL, WLC, MC, MCC, AJ, AJC: the matchup grade) added at Sam's instruction ("let's do all of this, if any is repeating don't do it twice"), defined before any result for them; head-to-head is not tested again (S, TS). §2 to §3e unchanged and pinned.
