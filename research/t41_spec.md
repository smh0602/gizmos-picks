# T41 — RECEPTIONS, WITH THE INFORMATION A SEASON AVERAGE CANNOT HAVE
Pre-registered 2026-08-28, BEFORE any fit, correlation or plot.
⛔ T39 FAILED FIRST. This is a SECOND attempt and it gets the SAME BAR.
`research/t39_spec.md` holds that failure in full.

## THE HYPOTHESIS, STATED AS A MECHANISM
T39 lost to a player's own season average, and every input it used —
trailing targets, snap share, yards per target — is something a season
average ALREADY HALF-CONTAINS. That is why it could not pull away.

🔴 **INJURY AND DEPTH STATE IS THE ONE COLLECTED INPUT A SEASON AVERAGE
STRUCTURALLY CANNOT KNOW.** A player whose WR1 is inactive this week is a
different player this week, and no smoothed average of his past can say so.
➡️ **IF THIS DOES NOT BEAT THE BASELINE, THE MECHANISM IS WRONG, NOT THE
FUNCTIONAL FORM — and receiving markets should be abandoned, not re-fitted.**

## TWO CHANGES FROM T39, AND ONLY TWO
1. **TARGET IS RECEPTIONS, NOT YARDS.** Receptions sit closer to the usage
   signal that measurably worked (targets t=+11.94) and further from the
   efficiency noise that did not (yards-per-target t=+1.39).
2. **TWO NEW INPUTS, both point-in-time:**
   - `ahead_out` — count of same-team, same-position players with a HIGHER
     trailing-8 snap share who are OUT or DOUBTFUL this week.
   - `own_status` — the player's own injury report status this week
     (0 healthy, 1 questionable, 2 doubtful/out).

⚠️ **DEVIATION FROM WHAT WAS DESCRIBED, DECLARED UP FRONT:** the depth
"rank" is derived from TRAILING SNAP SHARE, not from the published
`depth_charts` file. Two reasons, both stated before seeing any result:
(a) that file is 554,215 timestamped snapshots and joining it point-in-time
is a large surface for a silent bug; (b) published depth charts are
notoriously gamed by teams, whereas snap share is what actually happened.
⛔ If T41 fails, "we should have used the published depth chart" is a
LEGITIMATE follow-up and is pre-registered here as T42's premise.

## THE SPECIFICATION
  E[rec] = a + b1*(trail8_targets - c1) + b2*(trail8_snap_pct - c2)
             + b3*(opp_rec_allowed_to_pos - c3)
             + b4*ahead_out + b5*own_status
⚠️ `home` is DROPPED — T39 measured it at t=−0.10, a dead null. Carrying a
null term forward would be noise with a coefficient attached.
⚠️ Distribution for P(over): POISSON on receptions (a count), unlike T39's
Normal on yards.

## BASELINES, BAR AND SPLIT — IDENTICAL TO T39. NOTHING RELAXED.
  NAIVE-1 trailing-8 mean receptions · NAIVE-2 season-to-date mean
  FIT 2025 wk1-13 · TEST wk14-22 · line = player's own trailing-8 median
  PRIMARY   Brier gain >= +0.0050 vs the better naive
  SECONDARY MAE not worse than the better naive
  SUBGROUP  not worse than naive on WR, TE or RB separately
  MINIMUM   >= 200 test rows, players with >= 6 prior games
All four must hold. ⛔ THE BAR DOES NOT MOVE.

## PREDICTION, WRITTEN BEFORE RUNNING
1. `ahead_out` WILL BE SIGNIFICANT (|t| > 2) and POSITIVE. This is the whole
   hypothesis; if it is null the mechanism is dead.
2. `own_status` WILL BE SIGNIFICANT AND NEGATIVE — questionable players play
   fewer snaps.
3. **I PREDICT T41 STILL FAILS THE 0.005 BAR**, landing +0.002 to +0.004.
   Reason: `ahead_out` will be significant but RARE — a WR1 is inactive in a
   small minority of weeks, so a real effect on few rows moves an
   aggregate Brier very little.
4. Receptions will beat yards on MAE-relative terms but the Brier gap to
   naive will stay similar, because the line-at-median design caps it.
⚠️ **IF (1) IS SIGNIFICANT AND (3) IS STILL A FAIL, THE HONEST READ IS THAT
THE EFFECT IS REAL BUT TOO RARE TO CARRY A MARKET** — and the right response
is a CONDITIONAL product (flag the specific games where a WR1 is out) rather
than a confidence number on every row. That is pre-registered here so it
cannot be invented afterwards as a consolation.
