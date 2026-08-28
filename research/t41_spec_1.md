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

---

# ❌ RESULT — 2026-08-28. T41 FAILS THE BAR. THE EFFECT IS REAL BUT TOO RARE.

Fit 2025 wk1-13 (1,361 rows), tested wk14-22 (1,513 rows).
`ahead_out > 0` on 137 fit rows and 112 test rows — **11% of the board.**

| | Brier | MAE |
|---|---|---|
| **MODEL** | 0.2217 | 1.268 |
| naive trailing-8 | 0.2225 | 1.254 |
| naive season-to-date | 0.2225 | **1.248** |

🔴 **PRIMARY FAIL** +0.0008 vs a +0.0050 bar · 🔴 **SECONDARY FAIL** MAE worse
· 🔴 **SUBGROUP FAIL** RB −0.0020 and WR −0.0051 both worse than naive
(TE +0.0098 was fine) · ✅ 1,513 test rows.

## ✅ BUT THE MECHANISM IS REAL, AND THAT IS THE FINDING
| term | b | t |
|---|---|---|
| trailing-8 targets | +0.481 | **+13.33** |
| trailing-8 snap %  | +1.131 | **+3.22** |
| **ahead_out**      | **+0.342** | **+2.29** |
| own_status | −0.123 | −0.49 |
| opponent receptions allowed | −0.028 | −0.30 |

📊 **DIAGNOSTIC, WITHIN PLAYER** (102 players who experienced both states):
**+0.550 receptions** in weeks a higher-usage teammate is OUT versus weeks he
is not. ✅ **THE EFFECT EXISTS AND IT IS ABOUT HALF A RECEPTION.**

## 🔴 THE PRE-REGISTERED READ, APPLIED EXACTLY AS WRITTEN
t41_spec.md said, before any fit: *"IF (1) IS SIGNIFICANT AND (3) IS STILL A
FAIL, THE HONEST READ IS THAT THE EFFECT IS REAL BUT TOO RARE TO CARRY A
MARKET — and the right response is a CONDITIONAL product ... rather than a
confidence number on every row."*

**That is exactly what happened.** `ahead_out` is significant (t=+2.29) and
worth half a reception, but it fires on 11% of rows, so it cannot move an
aggregate Brier by 0.005. ⛔ **The bar is not moved. Receptions do not ship a
Gizmo's %.** ➡️ **What ships instead is a DESCRIPTIVE FLAG on the specific
rows where a higher-usage teammate is inactive**, carrying the measured
+0.55 receptions and the sample it came from. **That was decided in advance,
so it is a finding and not a consolation prize.**

## PREDICTIONS: 2 OF 4 CORRECT (T39 was 1 of 4)
1. ✅ **RIGHT — `ahead_out` significant and positive**, t=+2.29.
2. ❌ **WRONG — `own_status` is a NULL** (t=−0.49). A Questionable tag does
   not measurably cost receptions; only a teammate's absence helps.
3. ✅ **RIGHT — it still fails.** I predicted +0.002 to +0.004; actual
   +0.0008, so the effect is even rarer in aggregate than I allowed for.
4. ~ **PARTLY RIGHT** on receptions vs yards.

## 🔴 A REFINEMENT WORTH CARRYING FORWARD
**The opponent term flipped between markets.** On receiving YARDS it was
t=+3.68; on RECEPTIONS it is t=−0.30. ➡️ **Defences differentiate on YARDS
(efficiency, explosive plays) and NOT on VOLUME.** ⛔ Do not assume an
opponent adjustment transfers between two markets on the same player.
