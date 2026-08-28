# T39 — THE FIRST NFL MODEL: RECEIVING YARDS
Pre-registered 2026-08-28, BEFORE any fit, any correlation, any plot.
Data in hand: data/nfl/latest/players-2025.json.gz — 2,024 players, 19,400
player-weeks, 619 prop-position players, 345 with >=10 games.
⛔ NOTHING IN THIS FILE WAS WRITTEN AFTER SEEING A RESULT.

## WHY RECEIVING YARDS FIRST
Most props posted of any football market; the cleanest usage x efficiency
split; and target share is the stickiest usage signal in the sport.

## THE SPECIFICATION, FIXED NOW
Mirrors the v4.0 MLB shape deliberately -- trailing form, opponent, home:

  E[rec_yds] = a
             + b1 * (trail8_targets      - c1)
             + b2 * (trail8_yds_per_tgt  - c2)
             + b3 * (opp_rec_yds_allowed_to_pos - c3)
             + b4 * (trail8_snap_pct     - c4)
             +- HOME

⛔ EVERY INPUT IS POINT-IN-TIME: computed from games with d < the game
being predicted. No season totals, ever.
⚠️ Distribution for P(over): NORMAL, sd from the player's own residual
spread, floored at the position median so a 3-game sample cannot claim
false precision.

## THE BASELINES IT MUST BEAT
  NAIVE-1  the player's trailing-8 MEAN receiving yards
  NAIVE-2  the player's season-to-date mean, point-in-time
The comparison is against the BETTER of the two on each metric.

🔴 THE MARKET BASELINE CANNOT BE RUN ON 2025 AND THAT IS STATED, NOT HIDDEN.
We hold no historical NFL prop lines -- they were never collected and the
Odds API's history is a paid add-on. ➡️ So T39 can only establish "beats
naive". ⛔ IT CANNOT ESTABLISH "BEATS THE MARKET", WHICH IS THE ONLY THING
THAT MATTERS FOR BETTING. That test is T40, run PROSPECTIVELY on lines
collected from 2026 week 1 onward, and no confidence number ships to the
public page until T40 has passed.

## THE BAR, FIXED NOW
Temporal holdout: FIT on 2025 weeks 1-13, TEST on weeks 14-22. ⛔ Never a
random split -- this is a forecasting problem and a random split leaks the
future.
  PRIMARY   Brier score for P(over) at a line set to the player's own
            trailing-8 MEDIAN, which is approximately where a book sets it.
            Model must beat the better naive by >= 0.005 Brier.
            (Same bar the MLB hitter tests used. Chosen for consistency
            with this project's own precedent, not tuned.)
  SECONDARY MAE of the point estimate must not be WORSE than the better
            naive. A model that wins on Brier while losing on MAE is
            winning on calibration alone and must say so.
  SUBGROUP  Must not be worse than naive on WR, TE or RB taken separately.
            A model that fixes WRs by breaking TEs FAILS.
  MINIMUM   Test rows restricted to players with >= 6 prior games. Fewer
            than 200 test rows = INSUFFICIENT, not a pass.
All four must hold. ⛔ If it fails, the bar does not move and receiving
yards ships as MARKET with no confidence number.

## PREDICTION, WRITTEN BEFORE RUNNING
1. USAGE CARRIES IT. b1 (trailing targets) will be the dominant term and
   b2 (yards per target) will contribute almost nothing -- efficiency is
   noise at this sample size. Same finding as MLB, where trailing form
   carried the K model and the opponent term on OUTS was a measured null.
2. THE OPPONENT TERM b3 WILL BE WEAK OR NULL. NFL defences are less
   differentiated week to week than the "shutdown defence" narrative
   implies, and 17 games is too few to separate them.
3. THE MODEL WILL CLEAR THE BRIER BAR BUT ONLY JUST -- I expect +0.005 to
   +0.015 over naive.
4. TE WILL BE THE WEAKEST SUBGROUP, because TE usage splits between
   blocking and routes and snap share does not distinguish them.
⚠️ If (1) is wrong and efficiency matters more than usage, the whole
premise in claude/multi-league-spec.md is wrong and the CFB plan needs
rethinking before it is built.

---

# ❌ RESULT — 2026-08-28. T39 FAILS. RECEIVING YARDS SHIPS AS MARKET.

Fit 2025 wk1-13 (1,361 rows), tested wk14-22 (1,513 rows).

|          | Brier  | MAE   |
|----------|--------|-------|
| **MODEL**    | 0.2534 | 17.19 |
| naive trail-8| 0.2566 | 17.23 |
| naive season | 0.2545 | **17.10** |

- 🔴 **PRIMARY FAIL** — Brier gain **+0.0010** against a bar of **+0.0050**.
- 🔴 **SECONDARY FAIL** — MAE **17.19 vs 17.10**: the model is WORSE at the
  point estimate than the player's own season-to-date average.
- 🔴 **SUBGROUP FAIL** — WR (the largest group, n=707) is **worse than
  naive** (−0.0010). RB +0.0017 and TE +0.0042 were fine.
- ✅ Sample size passed: 1,513 test rows.

⛔ **THE BAR DOES NOT MOVE AND NOTHING IS RE-CUT TO RESCUE IT.** A second
attempt gets a NEW pre-registration at the SAME 0.005.

## COEFFICIENTS AND SIGNIFICANCE (fit set)
| term | b | t |
|---|---|---|
| trailing-8 targets | +5.94 | **+11.94** |
| trailing-8 snap %  | +9.77 | +2.03 |
| opponent yds allowed to pos | +0.28 | **+3.68** |
| trailing-8 yards per target | +0.33 | +1.39 |
| home | −0.14 | **−0.10** |

## MY PREDICTIONS: 1 OF 4 CORRECT
1. ✅ **RIGHT — usage carries it, efficiency is noise.** Targets t=+11.94,
   yards-per-target t=+1.39. Exactly as predicted, and it is the prediction
   the whole football plan rests on, so it mattered most.
2. ❌ **WRONG — the opponent term is NOT a null.** t=+3.68, clearly real. I
   predicted it would be a measured null by analogy with MLB's outs model.
   **The MLB analogy failed here and that is worth carrying forward.**
3. ❌ **WRONG — I predicted +0.005 to +0.015 Brier. Got +0.0010.**
4. ❌ **WRONG on the subgroup.** I predicted TE weakest; TE was the BEST
   and WR the worst.

## WHAT IS ACTUALLY LEARNED
- 🔴 **A PLAYER'S OWN SMOOTHED SEASON AVERAGE IS A BRUTAL BASELINE.** This
  is now the THIRD time this project has found that — MLB hitters (T27-T30)
  and MLB team totals (T31-T33) both lost to it too. **Treat it as the
  default hypothesis, not the thing to beat as an afterthought.**
- ✅ **HOME/AWAY IS A NULL for receiving yards** (t=−0.10), unlike MLB.
- ⚠️ **DESIGN NOTE FOR THE NEXT PRE-REGISTRATION, NOT AN EXCUSE FOR THIS
  ONE:** setting the test line at the player's own trailing MEDIAN forces
  the base rate to ~50%, which caps the achievable Brier gain by
  construction. Real books do not set at the median. ⛔ This does NOT
  rescue T39 — the spec was pre-registered and it failed on its own terms,
  including on MAE, which the median choice does not affect at all.

## CONSEQUENCE
➡️ **Receiving yards appears on the NFL board as 🔵 MARKET — line, price,
bet link, and the player's own usage numbers — with NO Gizmo's confidence
%.** Exactly how MLB run lines and hitter rows work today.
➡️ **T40 (beat the MARKET, prospectively on 2026 lines) is not reached.**
You cannot test whether you beat the market with a model that does not beat
a season average.
