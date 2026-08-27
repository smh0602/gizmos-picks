# T37 — CAN ONE PROJECTION PER (PLAYER, MARKET) REPLACE THE PER-ROW INVERSION?
Pre-registered 2026-08-27, BEFORE any fit. Prompted by Sam: "your projections
in the gizmos picks for plays fo the day dont match your projections for the
gizmos picks and the player props ... you should have the same numbers across
the entire website if your talking about the same stat or projction."

## THE DEFECT, MEASURED FIRST
On picks/2026-08-27.json, 51 of 608 (player, market) combos carry MORE THAN
ONE projected value. Worst: pitcher_strikeouts, 9 of 11 pitchers, max gap
2.1 K. Sean Manaea reads 6.3 K on the Top-10 row (the 3.5 rung) and 5.3 K on
his carded row (4.5). Same pitcher, same stat, same page, two numbers.

CAUSE: the projection inverts EACH ROW'S OWN blend, and blend = 50% model +
50% his RAW HIT RATE AT THAT LINE. The raw rate is line-specific and thin at
extreme rungs, so every rung implies a different central value.

## CANDIDATE
- PITCHERS: the model's own central value -- E[K] (lam) for strikeouts, mu for
  outs. Line-independent by construction. Label MODEL.
- HITTERS: the player's own per-game mean. Line-independent by construction.
  Label DESCRIPTIVE. (T34 already established the inversion agrees with this
  mean to within the 0.25 bar on hits/HR/RBI.)

## WHAT IS BEING BOUGHT AND WHAT MIGHT BE LOST
Bought: coherence -- one number per player per stat, everywhere on the site.
At risk: the property inversion was chosen for -- that a confident pick can
never project against itself.

## CONTRADICTION, DEFINED
A row CONTRADICTS when it picks OVER and projection <= line, or picks UNDER
and projection >= line.

## THE BAR, FIXED NOW, BEFORE LOOKING
Measured across ALL PRICED ROWS on the board -- carded, alt rungs and
below-floor, not just the 25 carded ones:
  - contradiction rate <= 5% at confidence >= 70%
  - contradiction rate <= 2% at confidence >= 80%
Both must hold, pitchers and hitters reported SEPARATELY and both must pass.

## PREDICTION, WRITTEN BEFORE RUNNING
Pitchers will contradict MORE than hitters, because `central` is only the
MODEL HALF of a 50/50 blend and the blend is what the row displays. I expect
pitcher contradictions in the 3-8% range at 70%+, concentrated on rows where
the raw record disagrees sharply with the model. Hitters should come in near
0%, since the earlier 948-row measurement put the mean on the losing side in
0.0% at 80%+ and 1.9% at 70%+.

## IF IT FAILS
Do NOT move the bar. Fall back to: invert ONCE at the PRIMARY (non-alt) line
and reuse that single value on every rung of that market. That is still one
number per player per stat, and it keeps the inversion tie to the carded row.
