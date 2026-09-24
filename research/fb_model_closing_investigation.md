# Why is the NFL closing-line spread record 38.8%? — investigation

`[Sam, 2026-09-24]` *"Investigation only. Change no model settings. PR
#150's closing-line record shows NFL spreads at 38.8% on 98 picks (95%
range 29–48%), entirely below 50%. A model with no skill should land near
50% at closing lines, so this is more likely a bug than bad luck. Find out
which."*

## Verdict, in plain English

**I found no bug.** Every link from nflverse's raw row to the graded pick
was checked, for all 319 NFL closing-line picks, not just a sample. The
line, the side, the price and the result all match a by-hand re-grade.
The two records pick the same side on every game they share. Every
feature I rebuilt by hand matches what the model stored.

What is left is the model itself. On NFL spreads it has so far been
**worse than a coin flip**, and its probabilities score worse than
guessing 50% every time. **Nothing was changed and nothing was retuned.**

## 1. Spreads, side mapping end to end

**The chain, as the code does it:**

| Step | What it is | Checked |
|---|---|---|
| nflverse `spread_line` | positive = the HOME team is favoured by that many | `t60r.market` refuses any row whose sign disagrees with the moneyline favourite |
| `M` (the model's line) | the home team's expected margin = `spread_line` | the "line" column below equals nflverse's `spread_line` on every pick |
| a HOME pick | home must win by MORE than `M`, at `home_spread_odds` | price column below |
| an AWAY pick | home must win by LESS than `M`, at `away_spread_odds` | price column below |
| grade | `margin − M`: above 0 = home covers, 0 = push (void) | hand column below |

**Ten real 2025 picks, worked by hand from nflverse's own row.** "Line" is
how much the home team was favoured by.

| Date | Game | Line | Pick | Price | Final (home first) | Margin | By hand | Code |
|---|---|---|---|---|---|---|---|---|
| 11-17 | DAL@LV | −3.5 | DAL −3.5 | −115 | LV 16–33 DAL | −17 | win | win |
| 11-20 | BUF@HOU | −5.5 | BUF −5.5 | −108 | HOU 23–19 BUF | +4 | loss | loss |
| 11-23 | NYJ@BAL | +14 | BAL −14 | −110 | BAL 23–10 NYJ | +13 | loss | loss |
| 11-23 | PIT@CHI | +3 | CHI −3 | −105 | CHI 31–28 PIT | +3 | push | push |
| 11-23 | NYG@DET | +14 | DET −14 | −105 | DET 34–27 NYG | +7 | loss | loss |
| 11-23 | SEA@TEN | −12.5 | TEN +12.5 | −105 | TEN 24–30 SEA | −6 | win | win |
| 11-23 | JAX@ARI | −2.5 | ARI +2.5 | −112 | ARI 24–27 JAX | −3 | loss | loss |
| 11-23 | CLE@LV | +3 | LV −3 | −115 | LV 10–24 CLE | −14 | loss | loss |
| 11-23 | PHI@DAL | −3 | PHI −3 | −105 | DAL 24–21 PHI | +3 | loss | loss |
| 11-23 | TB@LA | +7 | TB +7 | −110 | LA 34–7 TB | +27 | loss | loss |

**All 100 spread picks** (98 graded plus 2 pushes) were then re-graded the
same way from the raw row: **0 mismatches** in line, price or result.

## 2. Totals and moneylines, the same way

**Totals** (45.8% on 120): `total_line`, `over_odds` / `under_odds`, and
points against the line.

| Date | Game | Total | Pick | Price | Final | Points | By hand | Code |
|---|---|---|---|---|---|---|---|---|
| 11-17 | DAL@LV | 48.5 | under | −115 | 16–33 | 49 | loss | loss |
| 11-20 | BUF@HOU | 43.5 | under | −105 | 23–19 | 42 | win | win |
| 11-23 | NYJ@BAL | 44.5 | over | −118 | 23–10 | 33 | loss | loss |
| 11-23 | NE@CIN | 50.5 | under | −102 | 20–26 | 46 | win | win |
| 11-23 | NYG@DET | 50.5 | under | +100 | 34–27 | 61 | loss | loss |
| 11-23 | MIN@GB | 41.5 | over | −108 | 23–6 | 29 | loss | loss |
| 11-23 | SEA@TEN | 41.5 | over | −110 | 24–30 | 54 | win | win |
| 11-23 | JAX@ARI | 47.5 | under | −115 | 24–27 | 51 | loss | loss |
| 11-23 | CLE@LV | 35.5 | over | −118 | 10–24 | 34 | loss | loss |
| 11-23 | PHI@DAL | 47.5 | under | +100 | 24–21 | 45 | win | win |

**Moneylines** (48.5% on 99, against a 54.4% break-even):
`home_moneyline` / `away_moneyline`, and who won.

| Date | Game | Home / away price | Pick | Price | Final (home first) | By hand | Code |
|---|---|---|---|---|---|---|---|
| 11-17 | DAL@LV | +164 / −198 | DAL | −198 | LV 16–33 DAL | win | win |
| 11-20 | BUF@HOU | +210 / −258 | BUF | −258 | HOU 23–19 BUF | loss | loss |
| 11-23 | PIT@CHI | −155 / +130 | CHI | −155 | CHI 31–28 PIT | win | win |
| 11-23 | NYG@DET | −1050 / +675 | NYG | +675 | DET 34–27 NYG | loss | loss |
| 11-23 | MIN@GB | −290 / +235 | GB | −290 | GB 23–6 MIN | win | win |
| 11-23 | IND@KC | −218 / +180 | KC | −218 | KC 23–20 IND | win | win |
| 11-23 | SEA@TEN | +625 / −950 | TEN | +625 | TEN 24–30 SEA | loss | loss |
| 11-23 | JAX@ARI | +114 / −135 | JAX | −135 | ARI 24–27 JAX | win | win |
| 11-23 | PHI@DAL | +136 / −162 | PHI | −162 | DAL 24–21 PHI | loss | loss |
| 11-23 | ATL@NO | −122 / +102 | ATL | +102 | NO 10–24 ATL | win | win |

**All 120 totals and all 99 moneylines** re-graded from the raw row:
**0 mismatches.**

## 3. Do the two records pick the same side?

For every game graded in both the headline (your books) and the
closing-line record:

| Market | Games in both | Same side | Different side |
|---|---|---|---|
| Spread | 20 | 20 | 0 |
| Total | 21 | 21 | 0 |
| Moneyline | 19 | 19 | 0 |

## 4. The spread weights at the last training week

These come from the fit made for the week of Monday 2026-09-21, trained on
the 314 labelled games before it. Weights are per standard deviation,
because inputs are standardised (design §2).

| Input | Weight | What the design expects | Flag |
|---|---|---|---|
| intercept | +0.013 | — | |
| line (M) | +0.046 | no direction stated (the market is the baseline) | |
| h2h (mean margin in meetings, minus M) | **−0.048** | + | ⚠️ opposite |
| form (last-4 margin estimate, minus M) | +0.123 | + | |
| possession (home share minus away) | **−0.096** | + | ⚠️ opposite |
| personnel (away out minus home) | +0.010 | + | |
| neutral site | −0.042 | no direction stated | |
| dome / closed roof | −0.134 | no direction stated | |

⚠️ **Two signs are opposite to the design, so I rebuilt both features by
hand, to rule out a feature built backwards.** A backwards feature is the
one kind of bug that could make a model worse than a coin flip.

- **Possession:** the stored value matches the hand calculation to 4
  decimals on 4 real games (e.g. CAR@ATL: ATL 0.4908 over 9 earlier games,
  CAR 0.5154 over 10, giving −0.0245 by hand and −0.0246 stored). In all
  285 games the two teams' shares sum to 1. Every team code is on the
  schedule. **It is built correctly.**
- **H2H:** it reads each past meeting from **this** game's home side, and
  flips the margin when that team was away. The stored values match a
  hand calculation that uses only 2025-season meetings. My first hand
  pass disagreed because it included January 2025 games, which belong to
  the 2024 season. You set the history window to 2025–26 only
  (2026-09-23), so those meetings are correctly absent. **It is built
  correctly**, but early-2025 head-to-head is thin by that choice.
- **Form** (not flagged, checked anyway): WAS@MIA works out by hand to
  +10.375 and CAR@ATL to −1.25, both exactly as stored.

**So the two opposite signs are what the data taught the model, not a
wiring error.** Both are small (under 0.1 standard deviation). I did not
change either one.

## 5. Is it luck?

- **The whole model, not just its picks:** across all 153 NFL games the
  walk-forward predicted, the model's side covered **71 (46.4%)**. Its
  probabilities scored a Brier of 0.2613, against 0.2500 for guessing 50%
  every time. **It is currently worse than knowing nothing.** For 2025
  alone it is 51 of 121 (42.1%); for 2026 so far, 20 of 32 (62.5%).
- **How unlikely under pure luck** (exact binomial, fair coin):

  | Record | Result | Chance of this few or fewer |
  |---|---|---|
  | Spread picks | 38 of 98 | 1.7% (3.3% two-sided) |
  | Totals picks | 55 of 120 | 21% |
  | All predicted spread games | 71 of 153 | 21% |

  With six closing-line records, the chance that at least one looks as
  bad as the spread record by luck alone is about **18%**. ⚠️ The
  2025-only slice (18 of 61) looks far worse, but I found that slice by
  looking at the results, so its odds are not a fair test and I do not
  quote them as one.
- **Why "no skill = 50%" does not guarantee 50%.** A model can do worse
  than a coin flip without a bug, if what it learned from earlier games
  pushes it toward the side the closing line has already moved against.
  With 150–300 training games and seven inputs, that is plausible.
  Whether the ridge strength is right for that sample size is a model
  setting. You said not to retune after seeing this result, so this
  report does not test it. If you want it tested, it needs a
  pre-registered question first.

## What I did not change

- Any model setting, weight, input or pick rule.
- Either record.
- The page, and anything MLB.

Nothing was re-run with a different setting to see if it "fixed" the
number.

## Found in passing — a separate PR

While confirming #149 landed, I found the 2026 NFL quarter scores flipping
between 32 and 0 on `main`. The `fb-scores` job rebuilds the current
season's schedule without passing quarter scores. #149 guarded only the
other call site. That fix is its own PR, not this one.

## Changelog

- **2026-09-24:** written. Verdict: no bug.
