# Football pick model: design, fixed before the first walk-forward

`[Sam, 2026-09-23]` Train a model on signals 1–8 for each game (NFL and
college). It outputs the probability of each side of the spread, the total
and the moneyline. Score it walk-forward over 2025 and 2026, graded at Hard
Rock, FanDuel and DraftKings prices, with uncertainty clustered by game.
Retrain automatically each week. Show its picks as their own MODEL section,
beside the existing card. No paid tiers, no new spend.

⚠️ **Written before any result was computed**, and committed before the
code that produces one. Sam set no pass/fail bar for this model ("I'll
decide on replacing it once the record shows something"), so this is a
design record, not a pre-registration. What it prevents is the design
drifting toward whatever the first record happens to reward.

## In plain English (for Sam)

- One small model per league and market (spread, total, moneyline). Each
  one looks at what the books say, then at signals 2–8, and learns how
  much each signal has actually mattered in games already played.
- Every week of 2025 and 2026 it is retrained on earlier games only, then
  asked about that week, then graded. That weekly record is what the page
  shows.
- **It picks a side only when its probability beats the break-even of the
  best Hard Rock / FanDuel / DraftKings price.**
- **The honest limit:** we have stored prices from those three books only
  since September 2026 (our own board archive). Before that there are only
  closing lines from other sources. So the model **trains** on every 2025
  and 2026 game, but it can only be **graded** at your books from
  September 2026 on. College moneylines are the exception: CFBD kept
  DraftKings moneyline prices for 2025 and 2026.

## 1. Inputs, all known before kickoff

| § | Signal | Spread feature | Total feature | Moneyline feature |
|---|---|---|---|---|
| 1 | Market | the line M (home margin), scaled | the line T, scaled | log-odds of the home win, vig removed |
| 2 | Head to head | mean home margin in meetings within 365 days, minus M | mean combined points, minus T | mean home margin |
| 3 | Time of year | — | — | — |
| 4 | This season | last-4 margin estimate minus M | last-4 points estimate minus T | last-4 margin estimate |
| 5 | Versus position | — | both defences' allowed-yards rank fraction, minus 0.5 | — |
| 6 | Possession | home share minus away share, each from **earlier games only** (`possession.share_before`) | — | same as spread |
| 7 | Personnel (NFL only) | away players ruled out minus home, latest week before the game | — | same as spread |
| 8 | Venue | neutral site (0/1), dome or closed roof (0/1) | same | same |

- **§3 has no team-level input.** It holds player yards from this week in
  earlier seasons, and nothing about margin or points. That is the same
  reading T60R made, and it is stated rather than forced.
- **§7 is NFL-only:** no college source is permitted (Sam, 2026-09-23).
- **Point-in-time:** §2, §4 and §5 reuse `t60r.py`'s point-in-time code,
  read-only and unchanged. §6 is `possession.share_before`, and §7 reads
  `team_out` for a week before the game's own.
- **A missing input is 0**, which after scaling means "average". The model
  learns nothing from it and invents nothing.

## 2. The model

- **Form:** L2-regularised logistic regression, one per league × market.
  The strength is λ = 1.0 on standardised inputs, with the intercept not
  penalised. It is fitted by Newton's method (IRLS), stdlib only.
- **Spread label:** home margin > M. **Total label:** points > T.
  **Moneyline label:** home win. Pushes and ties are left out of training.
- **It outputs both sides:** p and 1 − p.

## 3. Lines and prices

- **Training line**, first available:
  1. the consensus (median) of Hard Rock, FanDuel and DraftKings at the
     last archived snapshot before kickoff;
  2. college: CFBD's stored line (DraftKings, then Bovada, then ESPN Bet);
  3. NFL: nflverse's closing line.

  Spread direction is checked against the moneyline, as in
  CLAUDE.md's `run_line` rule.
- **Grading price: Hard Rock, FanDuel and DraftKings only, never invented.**
  - **Spreads and totals** use each book's own line and price at the last
    snapshot before kickoff. The model is re-asked at that book's line.
  - **Moneylines** use each book's price at that snapshot. College
    additionally uses CFBD's DraftKings moneyline.
  - A game with no price at those books is **trained on but not graded**.

## 4. Walk-forward and picks

- **Weeks** run Monday to Sunday, across 2025 and 2026. For each week the
  model is trained on games that kicked off **before that Monday**, then
  asked about the week.
- **The challenger starts** only once ≥ 150 labelled games precede the week,
  per league and market.
- **Pick rule:** for each side, take the best price among the three books,
  and compute EV = p × decimal − 1. Pick the side with the higher EV if it
  is above 0. At most one pick per game per market.
- **The record** per league × market shows:
  - picks and hits (a push is void and left out);
  - hit rate, and the mean break-even of the prices taken;
  - a 95% interval on the hit rate using the **effective n clustered by
    game** (`shadow_fb.cluster`). A p-value is never taken on raw rows.

## 5. What runs when

- `fb_model.py` rides the existing `card-fb` mode, after the dossier and
  the shadow record. No cron line changes and nothing needs uploading.
- `data/<league>/latest/fb-model.json` gets a freshness row beside the
  dossier's, so `converge` rebuilds it if a run is missed.
- Every run re-scores the whole walk-forward from stored data, so a newly
  finished week is added automatically.

## Changelog

- **2026-09-23:** written, before any result.
- **2026-09-23, after the first run: three places the code did not match
  this design, all fixed without changing the design:**
  - **§3 college moneylines were never graded at CFBD's DraftKings price.**
    Root cause: `best_pick` returned early when there was no board
    snapshot, so the CFBD fallback this section promises was unreachable.
    Guard: `test_fb_model.py`.
  - **§3 "spread direction is checked against the moneyline" was not
    implemented.** Root cause: I wrote the rule here and never carried it
    into `book_lines`. It is now `spread_oriented()`, applied per book, and
    it fails closed. Guard: a mutation in `test_fb_model.py`.
  - **This week's picks read `board.json`, which has no per-book prices.**
    Root cause: I assumed the processed board kept each book's quote.
    Picks now come from the same raw snapshot archive the walk-forward
    grades against, limited to the next 7 days.
