# gizmos-picks — read this before changing anything

This repo backs a live MLB betting-analysis product for one user, Sam. It
publishes probability estimates he bets real money against, and it keeps a
permanent record of how those estimates performed.

You are probably a fresh GitHub Action session with no memory of how any of
this came to be. **Almost every rule below exists because something went
wrong once.** Do not relax one because it looks over-cautious.

---

## THE ONE RULE THAT MATTERS MOST

🔴 **NEVER WEAKEN A CHECK TO MAKE IT PASS.**

`verify_card.py` runs before the card is committed and fails the build on
any error. It exists to stop a wrong card reaching a page Sam bets from.
**If a check fails, the card is wrong — not the check.**

⛔ Do not loosen a tolerance, delete an assertion, or add an early return
so a run goes green. **A green tick that proves nothing is worse than a red
one, because it gets trusted.**

✅ The one legitimate reason to change a check is that it asks the WRONG
QUESTION. That happened once: a check asserted "at least one alt rung is
below −700", which tests that data EXISTS rather than that data is CORRECT,
and it failed a perfectly good card on a board that had no ladder stored
yet. It was replaced with "no rung the board holds is missing from the
card" — a strictly stronger question. **If you make that argument, make it
explicitly in the PR body, and make the new check harder to pass than the
old one, not easier.**

---

## What must never change without Sam saying so

| | |
|---|---|
| **Model coefficients in `card.py`** | Fitted, re-fit monthly. ⛔ Do not "tune" one, round one, or tier a term that ships pooled. |
| **`blend` = plain 50/50 of model and raw** | This is the number that enters the permanent calibration record. Changing how it is computed silently invalidates every historical row. |
| **`carried`** | A shadow column for two PRE-REGISTERED, NOT ADOPTED tests. ⛔ It must never feed `blend`, a probability, or a pair. |
| **The 1.8x pair floor** | Sam's own instruction. A pair below it is never shown — not printed, not labelled, not listed as declined. |
| **The −700 price floor** | Sam's own instruction. Rungs below it are shown but never starred and never paired. |
| **Five books only** (`BOOKS` in collect.py) | Hard Rock, DraftKings, FanDuel, Caesars (`williamhill_us`), BetMGM. Sam's instruction, 2026-08-23. ⚠️ This SUPERSEDED the earlier "Hard Rock only / `regions=us2`" rule for props — four of the five live in `us`, so props pull `us,us2` and cost double. A price from a book he cannot bet is not a better price. |
| **`picks/<date>.json` already written** | Published estimates are a permanent record. ⛔ Never edit or delete one after its games have started. |

## Things that are true and easy to get wrong

- 🔴 **`inningsPitched` fractions are THIRDS.** Only `.0`, `.1`, `.2` exist.
  There is no `.3`. A value outside that domain is fabricated data —
  `outs_of()` raises on it deliberately. Do not "fix" it by rounding.
- 🔴 **Two legs are in different games only if the GAME ID differs.**
  ⛔ Never compare opponent names. In every game both starters have
  different opponents and the same game, so a name check passes on exactly
  the pairs it exists to catch. A live card shipped four impossible parlays
  that way, including its top recommendation.
- 🔴 **Pitcher rates are computed over STARTS ONLY.** A reliever's two-out
  appearance is not evidence about a starter's line. Mixing them in once
  turned a true 2/3 into a false 48/49.
- 🔴 **A hitter is rated only over games he BATTED (`pa > 0`).** The hitter
  analogue of starts-only, and the same bug. A defensive sub or a pinch-run
  is not an under that won -- at the book it is usually a VOID. Measured
  2026-08-23: Tyler Tolbert's "under 0.5 total bases" read 41/58 (71%) over
  every logged game and 24/41 (59%) over games he actually batted in.
- 🔴 **Shop a price only at the EXACT SIGNED number.** Measured 2026-08-23
  on ATL@MIL: eleven books posted ATL -1.5 / MIL +1.5 while two posted the
  same game inverted. Matching on |point| paired "Milwaukee -1.5 at +130"
  against a market whose real price is "+1.5 at -182" -- opposite bets, and
  the page would have advertised a bargain that does not exist. ⛔ Never
  compare two prices without first confirming they are the same wager.
- 🔴 **A hitter row carries NO confidence rating and NO band.** There is no
  hitter model. Ledger rule 55 forbids a MARKET number from wearing a
  Gizmo's %. ⛔ Do not add one until a hitter model exists, is backtested,
  and has beaten the raw rate on a pre-registered test.
- 🔴 **Players share names.** `resolve()` refuses to guess and returns
  `(None, None)` when a name is ambiguous and the game's own teams do not
  break the tie. ⛔ Do not make it pick the first match.
- 🔴 **The collector must FAIL LOUD.** `sys.exit(1)` on error. It used to
  exit 0, and a green check proved nothing.
- ⚠️ **Cron minutes are deliberately off :00 and :30.** Those are the most
  congested slots on GitHub's scheduler and runs get dropped. Six were lost
  that way, leaving a three-hour hole in the data.
- ⚠️ **`concurrency` is grouped PER MODE.** A shared group silently cancels
  queued scheduled runs when someone triggers a job by hand.
- ⚠️ **An absence in an API response is evidence about the API, never about
  the sportsbook.** This project has written down "the feed has no X" as
  "the book has no X" five times and been wrong every time.

## Data and money

- ⛔ **Never invent a price.** Every quoted number must be traceable to a
  stored raw pull. `verify_card.py` checks this.
- ⛔ **Never quote a PrizePicks price.** `−137` and `+100` are the feed's
  encodings for "goblin" and "demon" — labels, not quotes. No break-even,
  no edge, no EV may be computed from them.
- ⛔ **Do not commit secrets.** The Odds API key lives only in the
  repository secret `ODDS_API_KEY`.
- 💰 **Credits are metered.** A props pull costs `markets × regions` per
  game. Before adding a market or a region, state the new daily cost.

## How to work here

1. **Run `python verify_card.py` before proposing any change to `card.py`
   or `collect.py`.** If it does not pass locally, do not open the PR.
2. **Prefer a pull request over a push to `main`** for anything touching
   the model, the verifier, or the workflow. Data commits from the
   collector go straight to `main` and that is correct.
3. **Say what you did NOT change.** This project's docs do it, and it is
   how regressions get caught early.
4. **If you are unsure whether something is a rule or an accident, ask in
   the issue thread rather than guessing.** Sam reads them from his phone
   and would rather answer a question than unwind a change.

## What lives where

```
collect.py        the collector. modes: gamelines, schedule, results,
                  hitters, pitchers, news, props-batter, props-pitcher,
                  props-board, card, record
card.py           the v4.0 model -> picks/<date>.json. Calls nothing.
verify_card.py    26 checks, pitcher AND hitter. Runs before commit.
index.html        the dashboard, single file, no build step
.github/workflows/collect.yml   every schedule
data/             timestamped snapshots. append-only.
picks/            published cards. append-only once a slate starts.
```

The reasoning behind all of it — the model, the ledger, the pre-registered
tests — lives in Sam's Claude project docs, not in this repo. **If a change
needs that context and you do not have it, say so instead of inferring.**
