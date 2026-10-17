# The football game simulation (`fb_sim.py`)

Status: APPROVED by Sam, 2026-10-17. The bar in §3 was written down before any backtest number was computed.

## In plain English (for Sam)

- **What it does:** every NFL and college game is played out 10,000 times, possession by possession.
- **What it gives:** how often each side covers each spread and total, including how often a game lands exactly on the number (a push).
- **Where it runs:** in GitHub, on every football card build. No Claude, no Odds API credits.
- **When it takes over:** in a league only if it passes the backtest in §3, which was fixed before anyone looked. Otherwise its numbers are stored and shown, but the picks keep using the smooth curve.

Sam, 2026-10-17:
- *"wed be running 1000 simulated games to get 1000 simulated outcomes, wed be doing this for every single game of the week for both nfl and cfb"*
- He chose 10,000 runs.
- He chose "Backtest, then switch": *"i dont care what my rules say you can ovverdie with my permission just ask first"*. That covers the two rule overrides: looking at results before a pre-registration, and skipping the Monday contest.

## 1. One simulated game

- **Inputs:** the model's own predicted points for each team (`fb_model.game_score`), and its own spread of results:
  - `score_sigma` for the margin;
  - `total_sigma` for the total.
  - No price, line or books' chance is an input.
- **Drives:** each team gets `drives` possessions (NFL 10, college 13).
  - Every drive but its last ends in a touchdown (6, 7 or 8 with the try), a field goal or nothing.
  - The touchdown share of scoring drives is `td_share` (NFL 0.55, college 0.70).
- **The last drive:** each team's last possession is played to the score, in a random order:
  - protect a lead;
  - kick to win a tie;
  - kick to tie or win when down 1–3;
  - only a touchdown will do when down 4–8.
- **Overtime:** a tie goes to overtime.
- **Uncertainty:** each run first moves both teams' averages by the model's own uncertainty, meaning what is left of sigma after the game's own luck.
- **Tuning:** a short pilot and a tuning run per game make sure the runs average the model's predicted margin and total, with sigma and sigma_t as their spread.

## 2. Fitted on final scores only

`PARAMS` (drives, td_share) were chosen from a grid. The criterion: how well the replayed games reproduce how often real games end by each margin from 0 to 21. The data:
- NFL: 2,307 games, 2018–2026.
- College: FBS v FBS, 2,734 games, 2023–2026.

The settings that make the most 3-point finishes also make games too swingy, so milder settings were chosen. Even then, the drives alone end NFL games by exactly 3 less often than real games, and college likewise.

`MARGIN_FIX` therefore weights each final margin's runs by its real share over its simulated share. It is computed from the same final scores, shrunk toward 1, and kept within 0.25–4.

Result on four test games:
- A close NFL game ends by exactly 3 in about 14.5% of runs, and a −3 line pushes about 7%.
- Measured on real games: NFL 3 = 14.9% of all games; pushes on 3 run 7.4–7.9% for close games.

⚠️ The margin shapes were fitted on games that include the backtest's games. That is about three numbers per league, fitted on final scores alone with no model input, so the leak is small. It is disclosed here.

## 3. THE BACKTEST BAR (fixed 2026-10-17, before any backtest number was computed)

**Setup:**
- Per league, the same walk-forward weeks as the Model picks record (`fb_model.walk_forward`).
- Each week is predicted from games before its Monday.
- Each week's sigma and sigma_t come from those training games only.

**Two numbers, the smooth curve (today) against the simulation:**
- **(a) Accuracy:** mean log loss over every final game's main closing spread and total in those weeks.
  - The question for a spread: does the home side cover? For a total: does it go over?
  - A push is left out. The simulation's chance is win / (win + loss).
- **(b) Return:** the closing-line record's spread and total picks pooled, as profit per bet. A push returns the stake.

**The rule:**
- The simulation sets a league's spread and total chances (`fb_model.SIM[lg] = True`) only if both hold in that league:
  - its log loss is at most the smooth curve's;
  - its return is at least the smooth curve's.
- The books record is reported beside it, never as it.
- Otherwise `SIM[lg]` stays False: the simulation is built, stored and shown, and the picks keep the smooth curve. Sam is told plainly.

**NFL injuries:** Sam chose "In the sim, backtest-gated". The same two numbers decide, simulation with injuries against the simulation without. Injuries go in only if both hold.

## Changelog

- **2026-10-17:** written, with §3 fixed before the backtest.
