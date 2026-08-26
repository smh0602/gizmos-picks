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
| **Batter ALTERNATE lines are never carded** | Sam's instruction, 2026-08-26. ⚠️ We never *request* a batter alt market — they arrive **inside the standard ones**: `batter_total_bases` returned 244 players at 1.5 and **17 at 3.5**. Once the −700 board gate came off, "under 3.5 total bases" at **−2200** (a 58-of-59 record that pays nothing) sorted straight to the TOP of a confidence-ranked board and buried every real play. `HITTER_PRIMARY_LINES` in `card.py` is the allowed set per market. ⛔ It is a LINE rule, not a price rule — a −300 alternate is still an alternate — and the price-floor lift is not a licence to card one. |
| **The parlay candidate pool is STRATIFIED BY PRICE** | ⛔ Do not "simplify" it to the N highest-confidence legs. Confidence and price move together, so a confidence-ranked pool of 100 legs had decimal odds of 1.154–1.571 — all short favourites — and the three-leg search returned **zero** parlays on a slate with 2,396 priced legs. Measured 2026-08-26. The pool takes the best legs from each price band for exactly this reason. |
| **The top-10 price gate (−400)** | Sam's own instruction, 2026-08-26: "likely AND payable". Without it the list fills with −2000 alt rungs that always win and pay nothing. It is a floor like the other two, not a judgment call per slate. |
| **A projection is an INVERSION of the displayed confidence** | Never a second estimate. `card.py` solves for the central value that reproduces the number already printed, under that row's own distribution, so the two can never disagree. ⛔ Do not print `central` (E[K]) instead — it is the MODEL half of a 50/50 blend and differs from the blend by design. ⛔ Do not compute one in JavaScript; that is a second copy of the model. |
| **THE REGION IS THE PRICE, NOT THE BOOK LIST** | Cost is `markets × REGIONS × games` and **books are FREE inside a region** — one `us,us2` pull returned **18 books for 6 credits** (measured 2026-08-26). `BOOKS` is applied AFTER the response arrives; it is a display filter and saves nothing. ⛔ Do not try to cut credits by dropping books. Only dropping a REGION halves a pull, and `us2` is the region Hard Rock lives in. |
| **The budget is DERIVED, not written down** | `python budget.py` reads the cron schedule out of the workflow and the market lists out of `collect.py` and computes the spend. ⛔ Do not put a credit total in a comment — this project has done it three times and been wrong twice. Run the script. |
| **Every props pull is scheduled TWICE, 15 minutes apart** | The backup costs **nothing** when the first one landed: `props_is_fresh()` stands it down inside a 45-minute window. GitHub drops scheduled runs — only 29 of 70 gamelines hour-slots produced a file, measured 2026-08-26 — and with three props pulls a day one drop is a third of the board's freshness. ⛔ The guard keys on the STORAGE DIRECTORY, not the region, so a cheap `us2` backup stands down behind a full `us,us2` primary. |
| **Paid pulls are anchored to the CARDS** | The full two-region pull runs at 14:08–14:28Z, immediately before the 14:46Z card. ⛔ Do not move it later "to be fresher" — a noon pull lands AFTER the morning card, which then falls back to the 4am prices, 6¾ hours stale. |
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
- 🔴 **A hitter is rated only over games he STARTED.** ~~`pa > 0`~~ —
  **tightened 2026-08-24.** Excluding zero-PA games was right but did not
  go far enough: a **1–2 plate-appearance cameo is not a start**, and
  counting it as one inflates every hitter UNDER. Measured across 37,829
  played games — under 0.5 hits: cameo **74.8%** vs start **37.4%**
  (+37.4 points); under 1.5 TB: 90.4% vs 63.5%; under 0.5 RBI: 87.8% vs
  69.4%. Cameos are 13.7% of played games and hit bench bats hardest —
  which is exactly who was topping the picks board. **Use real batting
  order from `data/latest/lineups.json.gz` where it exists; `pa >= 3` is
  the documented fallback and nothing else.**
- 🔴 **A hitter was previously rated over games he BATTED (`pa > 0`).** The hitter
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
- 🔴 **Total bases and Hits+Runs+RBIs carry NO PROJECTION, deliberately.**
  Not an oversight and not a missing feature. T34/T34b/T35, 2026-08-26, bar
  fixed at |mean| < 0.10 and p90 < 0.25 units BEFORE any fit: plain Poisson
  missed by **0.673** at the tail on total bases, a negative binomial by
  **0.350**, a compound Poisson (hits × the player's own extra-base mix) by
  **0.287**. Projecting the observed mean directly put it on the losing side
  of the line in 5% of rows, all unders. Hits (Poisson, 0.202), home runs
  (Poisson, 0.022) and RBIs (**negative binomial**, 0.117 — Poisson failed
  at 0.299) passed and ship. ⛔ Three attempts have failed. A fourth does
  not get an easier bar; it gets a new pre-registered test at 0.25.
- 🔴 **A hitter row shows a confidence NUMBER but must never claim MODEL
  provenance.** ~~"carries NO confidence rating"~~ — **changed 2026-08-24**:
  a board with two different headline numbers is unreadable, so both kinds
  of row show one CONF number and the board sorts strictly by it. What
  rule 55 requires is that the number be **labelled**, not hidden. So:
  every row carries `confidence_basis`, which is `MODEL` for pitchers and
  **`RECORD`** for hitters, and a hitter row must never carry a `blend` or
  a calibration `band`. ⛔ Do not relabel a hitter row `MODEL` until a
  hitter model exists and has passed a pre-registered test. **T27, T28 and
  T29 all FAILED — hitter modelling is CLOSED pending lineup slot, which
  the `lineups` collector mode now gathers.**
- 🔴 **The board sorts strictly by confidence, descending.** Sam's
  instruction. ⚠️ Edge still decides which plays make the board at all; it
  just no longer decides the order. ⛔ Do not reintroduce band-first or
  edge-first ordering — it made the page look broken to anyone reading
  down the numbers.
- 🔴 **A CARD IS MATCHED TO A BOARD RECORD ON NEAREST FIRST PITCH, NEVER
  ON A DATE.** ⛔ Do not "simplify" `boardFor()` back to a date comparison.
  **A UTC date is not a game's date**: a 9:40pm ET first pitch is `01:40Z
  THE NEXT DAY`, so every night game files under tomorrow and the next
  afternoon's card inherits it. That shipped on 2026-08-26 and put six
  games' LIVE IN-PROGRESS odds onto the following day's cards — CHC at
  −4000 with a 4.5 total, Pittsburgh implied for 0 runs. ⚠️ **ET dates are
  not sufficient either**: a doubleheader is two games with the same teams
  on the same ET date. Nearest first pitch inside `BOARD_MATCH_WINDOW_MS`
  separates all three cases, and **it fails closed** — no candidate in the
  window returns null and the card renders with no odds. A card missing a
  line is a card missing a line; a card showing another game's line is
  misinformation. `test_board_match.js` is the regression test and runs
  against the real board.
- 🔴 **`run_line` is the HOME team's point, by MAJORITY across books, then
  cross-checked against the MONEYLINE.** ⛔ Never take it from one book.
  Books split on which side they show laying the runs — 11 to 6 on TB@DET,
  2026-08-26 — and `team_total` is derived from it, so one book's label
  shipped the implied runs to the wrong team on 3 of 19 games. The
  moneyline is the authority: it is a single unambiguous market and the
  favourite lays the runs. A row re-oriented against its spread label
  carries `run_line_conflicted_with_moneyline` and says so on the page.
  ⚠️ **`team_total` is owed-test T25's predictor**, so an inverted row is a
  corrupted observation in a test that has not been run yet.
- 🔴 **THE OPPONENT'S RECENT STARTER LOG IS DESCRIPTIVE AND MUST STAY THAT
  WAY UNTIL T36 PASSES.** Sam asked for it to feed the confidence score.
  It cannot yet: the v4.0 K model **already carries an opponent term**
  (`oppK`, the season-long mean), and a ten-start window is a competing
  estimator of that same quantity, not new information. Adopting it is a
  model change and this project does not make those without a
  pre-registered test. ⛔ It must never touch `confidence`, `blend`,
  `carried`, a band or a pair before T36. `verify_card.py` checks it is
  labelled DESCRIPTIVE and says so in words.
- 🔴 **IT DOES NOT NEED STATMUSE, AND MUST NOT USE IT.** Sam asked for this
  from StatMuse. **All 3,852 starts in `pitchers.json.gz` already name their
  opponent** (verified 2026-08-26), so it is a query over data the collector
  already stores: zero credits, no scraping, nothing third-party to break,
  and **point-in-time by construction** — which a scraped "last 20 games"
  table can never be. `claude/mlb-data-stack.md` also forbids letting a
  summarising fetch touch a number the card computes with.
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
                  props-board, card, record, refresh, lineups
card.py           the v4.0 model -> picks/<date>.json. Calls nothing.
budget.py         projected Odds API spend, derived from the deployed
                  cron schedule and market lists. Run it after ANY change
                  to the schedule or the markets.
verify_record.py  re-grades EVERY published pick from the stored box
                  scores a second way and reconciles record.json against
                  it -- totals, per day, per kind, the internal sums, and
                  the drill-down detail. ⛔ Voids stay out of every
                  denominator. Runs on the record and refresh jobs.
verify_board.py   checks data/latest/board.json -- implied runs vs the
                  moneyline, run-line attribution, and whether the PAGE
                  can tell two records for one matchup apart. ⛔ Runs on
                  the GAMELINES job, which is the job that writes the
                  file. verify_card.py only runs on card/refresh, and
                  that gap is how the wrong-game bug shipped.
test_board_match.js  regression test for boardFor(), run with node
                  against the real board.json.
verify_card.py    75 checks, pitcher AND hitter, including the
                  descending-order invariant, the projection
                  round-trip, the top-10 price gate and every
                  parlay recomputed leg by leg. Runs before commit.
index.html        the dashboard, single file, no build step
.github/workflows/collect.yml   every schedule
data/             timestamped snapshots. append-only.
picks/            published cards. append-only once a slate starts.
```

The reasoning behind all of it — the model, the ledger, the pre-registered
tests — lives in Sam's Claude project docs, not in this repo. **If a change
needs that context and you do not have it, say so instead of inferring.**
