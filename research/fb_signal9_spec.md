# Signal 9 — "Opportunity change"

Status: APPROVED BY SAM 2026-09-24 — rules in section 2 set by Sam before any result; formulas and scoring in section 3 fixed by Claude before any scoring

⚠️ **Written and committed before any code that scores signal 9 exists.**
Sections 2 and 3 are hashed by `test_prereg_gate.py`.

## In plain English (for Sam)

- Projections lean on 2025 and miss players leaving and offenses changing.
- Signal 9 measures, for every team, **how much of last season's
  opportunity has left**: targets, air yards, carries and inside-10
  targets. That sets each player's starting point, and every 2026 game
  pulls him toward his real role.
- It is tried in three places: the props model, the card's 2025 starting
  point, and the game model. **Each stays only if it does not make that
  model's log loss worse**, clustered by game.

## 1. Scope and data

- **NFL:** from free nflverse files the collector already downloads:
  - player game logs (`players-<season>.json.gz`: targets `tgt`, air
    yards `ay`, carries `car`, team per game);
  - weekly rosters (`roster_weekly_<season>`);
  - play-by-play (inside-10 targets).
- **College:** CFBD returning production (`/player/returning`, one call
  per season) and the transfer portal (`/player/portal`, one call per
  season), priced by `cfbd_budget.py`. Each is fetched **once per season,
  only when its file is missing**: 4 calls one-time for 2025 and 2026,
  against 914 scheduled calls a month on the 1,000 free tier. Both fit.
- ⚠️ **College cannot be scored in this PR.** The CFBD key is a repository
  secret, so its data arrives with the first scheduled run after merge.
- Nothing MLB. No new spend. No cron change.

## 2. The rules `[Sam, 2026-09-24, set before any result]`

> "For each team, the 2025 regular-season targets, air yards, carries and
> inside-10 targets of players NOT on that team's Week 1 2026 roster, as a
> count and as a share of the team's 2025 total. Players on injured
> reserve count as vacated while they are out. Per player, store his 2025
> share and whether he changed teams. Rebuild it automatically when
> rosters change."
>
> "College: CFBD returning production (one call per season), plus the
> transfer portal endpoint. Price both with cfbd_budget.py first, and use
> them only if they fit the free quota."
>
> "Props model: a player's expected share starts from his 2025 share,
> adjusted for opportunity change. This season's games then pull it
> toward what he is actually getting. The card's 2025 starting point: the
> same way. Game model: the team-level vacated share as an input. The
> walk-forward decides whether each use stays. Report every record before
> and after. Keep each use only if it does not make log loss worse,
> clustered by game."
>
> "Show signal 9 as section 9 of each game's dossier panel, labelled
> DESCRIPTIVE."

## 3. Formulas and scoring, fixed by Claude before any scoring `[2026-09-24]`

⚠️ **Not approved by Sam. Frozen so nothing can be tuned after seeing a
result, and disclosed here so Sam can overrule any of it.**

**Measuring opportunity (NFL), for season S (2025 and 2026):**

| | |
|---|---|
| Prior volume | Every player-game row of season S − 1 with week ≤ 18 (the regular season), credited to that row's team T. The categories are `tgt`, `ay` and `car`, plus inside-10 targets: passes to a receiver with `yardline_100` ≤ 10 in S − 1's play-by-play, where stored. |
| Team total | TOT[T][cat] = the sum over T's rows. The **combined** category is targets + carries. |
| His old team and share | T_old = the team he had the most targets + carries for. share25[cat] = his volume for T_old / TOT[T_old][cat]. |
| Available | On team T's roster for week w of season S with status ACT or INA. **IR (RES) is not available, so it counts as vacated while out** (Sam). |
| Vacated | vacated[T][w][cat] = the prior volume for T of every player not available to T in week w, over TOT[T][cat]. A week past the roster file's last week uses its last week. |
| Off-roster only | The same at week 1 with ACT, INA and RES all counted available. This is the definition Sam's check figures match; it is stored and shown beside the main one. |
| Changed teams | His week-1 team (any status) differs from T_old. |

**Measuring opportunity (college), once CFBD data is stored:** vacated[T]
for receiving, rushing and passing = 1 − CFBD's returning usage for that
category. share25 comes from S − 1's college logs (catches, carries).
Changed teams comes from the portal (origin ≠ destination).

**The expected share (one formula, used everywhere):** for a player on
team T, in a game of week w of season S, market category cat (receiving
yards and receptions: `tgt`; rush yards: `car`; anytime TD: combined):

- v = vacated[T][w][cat] and s25 = share25[cat].
- **s_adj = min(1, s25 / (1 − v))** if he did not change teams (returning
  players absorb the vacated volume in proportion). s_adj = s25 if he
  changed teams. No value if he has no prior volume.
- obs_i = his cat volume in his i-th game of season S before this one,
  divided by his team's cat volume in that game.
- **E_share = (4·s_adj + Σ obs_i) / (4 + n)**, where n is that count of
  games. Four games already pull halfway, the same weight as the card
  fix's season weight.

**The three uses:**

| Use | Exactly what changes |
|---|---|
| Props model | One new stage-1 input: E_share × TOT[T][cat] / 17, his expected volume per game. It is 0 where there is no value, for passing markets, and for seasons without a roster file (before 2025). Everything else is as `research/fb_props_design.md`. |
| Card | Inside `card_fb.rate_blend`, for receiving yards, receptions and rush yards only, each 2025 game value is multiplied by **r = s_adj / s25** before hits are counted. r = 1 when he changed teams, has no prior, or s25 = 0. Nothing else changes. |
| Game model | One new input: spread and moneyline take V_home − V_away, totals take V_home + V_away, where V = vacated[T][w] for the combined category. It is 0 before 2025. Everything else is as `research/fb_model_design.md`. |

**The keep rule** (Sam: "only if it does not make log loss worse,
clustered by game"):

- Each use, per league, is scored walk-forward **with and without** it,
  everything else identical, on that use's own record:
  - **Props model:** its graded rungs.
  - **Card:** the graded published props, as in `research/fb_card_fix_spec.md`.
  - **Game model:** its closing-line walk-forward: every final game with a
    closing line, in every predicted week.
- d = log loss without − log loss with, per prediction, pooled over that
  use's markets. **Kept if the mean of d ≥ 0.** The cluster-robust (by
  game) one-sided p is reported beside it and is not part of the rule.
- A use with nothing to score (college, until its data is stored) **stays
  off**.
- Each use's on/off switch in the code is set from the recorded result,
  and a test fails if a switch disagrees with it.

**The dossier:** section 9 per game. For each team it shows:

- vacated share and count of targets, air yards, carries and inside-10
  targets, at the game's week;
- the off-roster-only figure;
- the departed players with the most prior targets + carries;
- how many arrivals changed teams.

It is labelled DESCRIPTIVE. College shows CFBD's returning production.

## 4. What runs

- `nfl.opportunity_from_rows` builds the NFL table inside the daily
  `nfl-logs` run, which is the run that refreshes rosters. The table is
  stored in `players-<season>.json.gz` under `opportunity`. Inside-10
  counts are added to the possession pass.
- `cfb.py` fetches returning production and the portal inside `cfb-probe`
  when a season's file is missing, after `cfbd_budget.preflight`.
- `signal9.py` is the one implementation of the expected share, read by
  all three uses and the dossier. `fb_signal9.py` scores the keep rule.
- ⛔ Nothing MLB. No cron change, no spend, and no published pick is
  edited.

## Changelog

- **2026-09-24:** written and committed before any scoring code.
