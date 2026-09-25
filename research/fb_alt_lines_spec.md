# Alt lines — is the game model calibrated away from the main line?

Status: APPROVED BY SAM 2026-09-24 — the check in section 2 set by Sam before any result; the formulas, the bar and the label rule in section 3 fixed by Claude before any scoring code existed

⚠️ **Written and committed on its own, before any code that scores it
exists.** Sections 2 and 3 are hashed by `test_prereg_gate.py`.

## In plain English (for Sam)

- The new Game Lines tab prices every alternate spread and total with the
  game model (`fb_model.py`). The model was trained on main lines only, so
  whether its percentages hold up 3, 7 or 10 points away from the main
  line has never been tested.
- This check asks one question per league and market: **at rungs 3, 7 and
  10 points either side of the main line, does the model predict the
  outcome at least as well as a simple market baseline?**
- **The result decides the label, never whether the number shows.** Pass:
  a plain MODEL %. Fail: the same number, with a "not calibrated away from
  the main line" warning.

## 1. Scope and data

- Both leagues, spreads and totals. Moneylines have no rungs.
- Games: every final game in 2025 and 2026 that `fb_model.build_rows`
  gives a main line (`M` for the spread, `T` for the total).
- No new data and no spend: the rows, lines and scores are already stored.
- Nothing MLB.

## 2. The check `[Sam, 2026-09-24, set before any result]`

> "The model was trained on main lines only, so its accuracy away from the
> main line is untested. BEFORE any scoring code, pre-register one check
> in a new research spec, committed on its own: walk-forward on 2025 and
> 2026 finals, the model's probability at rungs of main line ±3, ±7 and
> ±10, against a market baseline (a normal distribution around the main
> line, with its spread fitted on earlier weeks only), log loss clustered
> by game, bar fixed before scoring."
>
> "The result decides the LABEL, not whether the number shows (Sam wants
> the data and decides himself). Pass: plain MODEL %. Fail: still shown,
> with a clear 'not calibrated away from the main line' warning, using the
> per-band rule already in calibration.py (do not write a second copy)."

## 3. Formulas, bar and label rule, fixed by Claude before any scoring `[2026-09-24]`

### 3a. What is scored

- **Unit:** one (game, market, δ), with δ ∈ {−10, −7, −3, +3, +7, +10}
  and market ∈ {spread, total}. Scored per league.
- **Rung line:** spread `M + δ` (the home side's line, `fb_model`'s sign),
  total `T + δ`.
- **Outcome:** spread `y = 1` if home margin > `M + δ`; total `y = 1` if
  total points > `T + δ`. A push (equal) is not scored.
- **Walk-forward:** for each game, the week is the Monday on or before its
  date (`fb_model.monday`). Everything below is fitted only on labelled
  games of the same league whose date is before that Monday.
- **Model probability:** `p_model = fb_model.predict(m, fb_model.features(
  r, market, M=M+δ))` (or `T=T+δ` for the total), where `m` is that week's
  `fb_model.fit` at the live ridge `fb_model.RIDGE`, on the live features,
  trained on main-line labels exactly as `fb_model.walk_forward` trains it.
  A week where that fit returns None is not scored.
- **Market baseline:** a normal distribution around the main line.
  `σ_w = sqrt(mean of (outcome − line)²)` over the same week's training
  games (outcome = home margin for the spread, total points for the total;
  line = that game's own `M` or `T`). `p_base = 1 − Φ(δ / σ_w)`.
- **Score:** `d = LL(p_base) − LL(p_model)`, with log loss
  `LL(p) = −[y ln p + (1 − y) ln(1 − p)]` and p clipped to [1e-12, 1 − 1e-12].
  Positive d means the model beat the baseline.
- **Clustering:** the clustered p is `mlb_refit.paired_test_clustered(d,
  game ids)`. It is **reported beside the verdict and is not part of the
  bar**.

### 3b. The bar (per league × market, 2025 and 2026 pooled)

- **NOT YET MEASURABLE** if fewer than 100 units are scored
  (`calibration.MIN_N`). Treated as FAIL for labelling.
- **PASS** if the mean d ≥ 0: the model's log loss is not worse than the
  market baseline's.
- **FAIL** if the mean d < 0.
- Reported beside the verdict, never as it: the n, the number of games, the
  clustered p, the mean d at each |δ| (3, 7, 10), and 2025 and 2026 apart.

### 3c. The per-band rule (calibration.py, not a second copy)

- Every scored unit contributes both sides: `(p_model, y)` and
  `(1 − p_model, 1 − y)`. They are grouped into 10-point bands of the stated
  probability (0–10 … 90–100) per league × market, each band carrying
  `n`, `w` (outcomes that happened) and `stated` (mean stated %).
- `calibration.band_flags` judges each band exactly as it judges the
  card's bands. A band whose state is **UNDER** marks every rung whose
  shown probability falls in it.

### 3d. The label on the tab

A rung's model probability is shown in every case. It is labelled plain
**MODEL** only when all three hold:

1. its league × market verdict is PASS;
2. the rung is within the tested range, `|rung − main line| ≤ 10`;
3. its shown probability's band is not UNDER (3c).

Otherwise it is shown with the warning **"not calibrated away from the
main line"**. The model's fair line (the line where its probability is
50%) carries its league × market verdict the same way.

## 4. What runs

- `fb_alt_lines.py` scores the check and writes
  `data/<league>/latest/alt-lines-check.json`. It rides the free `card-fb`
  run, so the verdict is re-read as games are graded; the rule above never
  changes.
- The Game Lines tab reads the verdict and the band states from that file.
- ⛔ The check never hides a rung, never changes a probability and never
  touches the card or its record.

## Changelog

- **2026-09-24:** written and committed on its own, before any scoring
  code.
