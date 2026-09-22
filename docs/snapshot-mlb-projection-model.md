# MLB projection model — v5.0

**Re-fit Sept 1 2026 on the season through Aug 31 2026.** Supersedes v4.0's COEFFICIENTS. ⛔ **It does NOT supersede v4.0's structure, its strikes, or its lessons — those all replicated.**

✅ 🔴 **SHIPPED INTO `card.py` ON 2026-09-11. THE CODE-DEBT BLOCK BELOW IS CLOSED.** The card ran v4.0 for **ten days** after this page published v5.0; it now runs v5.0 and stamps `MODEL_VERSION = "v5.0"`. See the CODE-DEBT block and the Sept 11 changelog entry.

## 🔴 v5.0 IN ONE PARAGRAPH, INCLUDING THE PART THAT ARGUES AGAINST ITSELF

`[measured 2026-09-01, 17:00Z]` **Every v4.0 coefficient was re-fitted on 4,056 season starts from a DIFFERENT SOURCE than v4.0 used, and every one of them came back within a few thousandths.** ✅ **That is the headline and it is a good one: v4.0 replicates on an independently-sourced, 236-start-larger sample.** ⚠️ 🔴 **AND IT IS ALSO THE ARGUMENT FOR NOT RUSHING THE CODE UPDATE: 13 of `card.py`'s 16 model constants moved, and the largest resulting price change anywhere on a realistic board is 0.053 K and 0.133 outs.** ➡️ ~~**Ship v5.0, but ⛔ do NOT describe the shipped card as materially wrong while it still runs v4.0.**~~ ✅ **SHIPPED 2026-09-11 — and the second half of that sentence still stands: the card was never materially wrong, it was running last month's constants.** See the CODE-DEBT block.

### 🔴 WHERE THE DATA CAME FROM, AND WHY THAT IS THE MOST IMPORTANT LINE ON THIS PAGE

⛔ **THIS FIT DID NOT USE THE RECIPE.** **THE RECIPE needs Claude in Chrome; this was a scheduled headless run, and the container's Chromium reaches github but the proxy refuses `CONNECT` to `statsapi.mlb.com`** (`ERR_TUNNEL_CONNECTION_FAILED`, re-measured 2026-09-01).

✅ **IT USED `data/latest/pitchers.json.gz` FROM `github.com/smh0602/gizmos-picks`** — the collector's OWN nightly statsapi pull, reachable headless by `git clone`, **`pulled_at 2026-09-01T10:06:38Z`, `n_failed: 0`, `domain_violations: 0`**. **Every row carries `h` (isHome), `np` (`numberOfPitches`) and `bf` (`battersFaced`)** — the three fields the re-fit needs.

🔴 **THREE SCHEDULED RUNS IN A ROW WROTE "THE RE-FIT CANNOT RUN HEADLESS" WHILE THIS FILE SAT IN THE REPO THEY WERE ALREADY CLONING.** ⛔ **The blocker was never the data. It was that "the re-fit needs THE RECIPE" got read as "the re-fit needs a browser," and nobody asked what the collector had already stored.** ➡️ **STANDING RULE: before declaring a headless run blocked on data, `ls data/latest/` in the repo. It is one command and it costs nothing.**

### ⚠️ WHAT IS DIFFERENT ABOUT THIS SAMPLE — STATED BEFORE ANY COEFFICIENT

| | v4.0 | v5.0 |
|---|---|---|
| Source | THE RECIPE, in-browser statsapi, Aug 20 | the collector's stored statsapi pull, Sept 1 10:06Z |
| Season starts | 3,820 (frozen fit sample) | **4,056** (through 8/31) |
| Training rows after filters | 2,819 | **3,089** |
| Population filter | all starters with `gamesStarted > 0` | 🔴 **`min_ip ≥ 20` — 499 players, 305 with a qualifying start** |

🔴 **THAT `min_ip ≥ 20` FILTER IS A SEASON-TOTAL SELECTION CRITERION AND THEREFORE THE ONE PLACE THIS FIT IS NOT PURELY POINT-IN-TIME.** ⛔ **It is stated here rather than buried: it selects for arms that lasted, and it drops roughly 60–150 starts by low-innings pitchers that THE RECIPE would have kept.** ⚠️ **Every PREDICTOR and every GROUPING VARIABLE is strictly point-in-time; the SAMPLE MEMBERSHIP is not.** ➡️ **An interactive session running THE RECIPE should re-fit and compare — but note the direction of the evidence: v4.0's coefficients, fitted with NO such filter, reproduce here to a few thousandths, which is what a materially biasing filter would NOT do.**

⚠️ **Also recorded, because it would otherwise look like the team-assignment trap firing: 12 rows have `opponent == the pitcher's own team`. All 12 are MID-SEASON TRADES** — `team` in this file is the pitcher's CURRENT club, `o` is per-start — and every flagged start falls strictly before that pitcher's last start. ⛔ **`team` is therefore NOT a point-in-time field and is used nowhere in this fit.** ✅ **`h` and `o` are per-start and are what the model uses.**

⚠️ ~~**Refit Aug 20 2026 on the COMPLETE season.**~~ 🔴 **Qualified Aug 21 — "COMPLETE" was true on Aug 19–20 and is not a standing property.** The season keeps adding starts. **Replaced by: complete *as of Aug 20*.** The fit below is **frozen on the Aug 20 pull** and does not move as games are played — see the fit-sample vs live-population table directly below.

🔴 **Every v3.4 coefficient was fitted on a dataset that was 40% complete and heavily back-loaded (2% of April, 14% of May).** The refit below was fitted on **3,820 starts** by **340 pitchers**, pulled from `statsapi.mlb.com` game logs on **Aug 20**. Training rows after point-in-time filters: **n = 2,819**.

⚠️ ~~"uses all **3,820 starts** by all **340 pitchers** who started a game in 2026"~~ 🔴 **Struck Aug 21 — "all … who started a game in 2026" reads as a live population statement. It is not; it is the frozen fit sample.**

### ⚠️ Two different start counts on this page — do not confuse them

| Number | What it is | Does it move? |
|---|---|---|
| **3,820 starts** | the **FROZEN FIT SAMPLE** — the Aug 20 pull that **every coefficient on this page** was fitted on | **No.** Frozen. It is a historical property of the fit, not a description of the league. |
| **3,838 starts by 340 starters** | the **LIVE POPULATION**, re-verified Aug 21 (zero domain violations) — what `claude/mlb-opponent-database.md` is rebuilt on | **Yes.** It grows with the season. |

⛔ **Wherever this page says 3,820 it means the fit sample and nothing else. Never quote 3,820 as today's starter population — that is 3,838.** The 340-pitcher figure happens to be the same on both sides today; the start count is not, and will diverge further.

---

## THE MODEL

### Strikeouts

```
E[K] = 4.9292
     + 0.6653 × (mean K over his last 8 starts − 4.9454)
     + 0.5803 × (opponent mean K allowed − CENTERING CONSTANT)
                 ⚠️ DO NOT PASTE A NUMBER INTO THIS SLOT.
                    The centering constant is OWNED and STATED INTERNALLY by
                    claude/mlb-opponent-database.md. Read it from that doc, in
                    the same turn you price the play, together with the meanK.
                    (For the record only, NOT for use: the fit-sample mean of
                     this variable was 4.742 in v4.0 and 4.7710 in v5.0.
                     Neither is today's constant.)
     ± 0.1449              (+0.1449 home, −0.1449 road)
then Poisson around E[K]
```

⚠️ **The `− CENTERING CONSTANT` slot above is deliberately not a number.** ~~`− 4.742`~~ was printed there until Aug 21, three paragraphs above an instruction to centre on whatever `claude/mlb-opponent-database.md` states — so the copy-pasteable text and the instruction disagreed. **The doc owns it, states it internally, and it moves every time that table is rebuilt.** A hard-coded copy is silently wrong the moment the table moves, and it does not announce itself.

| Term | β | t | v4.0 | vs v3.4 |
|---|---|---|---|---|
| intercept | **4.9292** | **121.2** | ~~4.939~~ | was 5.21 |
| his trailing 8 | **0.6653** | **22.96** | ~~0.673~~ | was 0.564 |
| opponent K | **0.5803** | **5.69** | ~~0.575~~ | was 0.517 — holds |
| home/road ± | **0.1449** | **3.56** | ~~0.151~~ | was 0.092 |

**R² = 0.1563 · RMSE = 2.258 K · n = 3,089** *(v4.0: R² 0.156, RMSE 2.28, n 2,819)*

✅ **Every term kept its sign, its rough magnitude and its significance. The largest move is the intercept, at one hundredth of a strikeout.**

### Outs

```
mu = 15.9121
   + k      × (mean outs over his last 8 starts − 15.8988)
                 ⚠️ k IS TIERED on his own trailing outs level (table below):
                      trailing < 15.25    → k = 0.629
                      trailing 15.25–17.0 → k = 0.647
                      trailing ≥ 17.0     → k = 0.361
                    The POOLED all-tier slope is 0.5155. That is a REFERENCE
                    figure only — v5.0 does NOT ship it.
                    Do not paste 0.5155 into a price.
   + 0.0366 × (HIS PREVIOUS START's PITCH COUNT − 87.2645)
                 ⚠️ use the POOLED 0.0366 — see "Which β to use" below.
   ± 0.1994              (+0.1994 home, −0.1994 road)

then P(outs) = Normal(mu, SD = cvO × his season mean outs)
                 ✅ NO LONGER AN ASSUMPTION — owed test T3 PASSED 2026-09-01.
```

🔴 ~~`+ 0.525 × (mean outs …)` · `+ 0.037 × (… PITCH COUNT …)` · `+ 0.189 × HOME`~~ — **the block as shipped until Aug 21 is struck, and it was dangerous to copy on three counts:**

1. It printed the **pooled 0.525** while v4.0 ships a **tiered `k`** — contradicted by this doc's own tier table three lines later. **Replaced by an explicit tiered `k`, with 0.525 kept and labelled as the pooled reference figure.**
2. It printed **`0.037`** where the fitted coefficient is **`0.0371`** (as the coefficient table below has always said). **Replaced by `0.0371`.**
3. **`+ 0.189 × HOME`** reads as a one-sided home bonus with no road penalty — unlike the strikeout block, which spells out `(+0.151 home, −0.151 road)`. It is a **two-sided ±** term. **Replaced by `± 0.189 (+home, −road)`.**

**No coefficient changed. Only the printed form did — so that the form a reader copies is the form the model uses.**

| Term | β | t | v4.0 |
|---|---|---|---|
| intercept | **15.9121** | **244.6** | ~~15.899~~ |
| his trailing 8 — **POOLED, reference only, NOT SHIPPED** | 0.5155 | 14.94 | ~~0.525~~ |
| **previous start PITCH COUNT** — **POOLED, and this IS the shipped one** | **0.0366** | **6.67** | ~~0.0371~~ |
| home/road ± | **0.1994** | **3.06** | ~~0.189~~ |

**R² = 0.1614 · RMSE = 3.613 outs · n = 3,089** *(v4.0: R² 0.165, RMSE 3.65, n 2,819)*

⚠️ **`k` still varies by the pitcher's own trailing level — but the values are roughly double v3.4's:**

| His trailing outs | n | k | t | pitch-count β | t | R² | v4.0 k |
|---|---|---|---|---|---|---|---|
| **< 15.25** (short) | 1,009 | **0.629** | 9.27 | 0.0406 | 4.98 | 0.2271 | ~~0.638~~ |
| **15.25–17.0** (mid) | 1,051 | **0.647** | 2.88 | 0.0261 | 2.60 | **0.0196** | ~~0.759~~ |
| **≥ 17.0** (long) | 1,029 | **0.361** | 2.80 | 0.0190 | 1.52 | 0.0128 | ~~0.317~~ |

### ✅ 🔴 TWO THINGS THIS TABLE SETTLES THAT WERE FLAGGED FOR EXACTLY THIS RE-FIT

**1. THE MID-TIER `R² = 0.023` WAS NOT A DROPPED DIGIT.** ⚠️ v4.0 flagged it as possibly `0.23` and — correctly — **refused to change a fitted number by inference.** `[measured 2026-09-01]` **it re-fits at `0.0196`.** ✅ **The flag is CLOSED: the mid tier really does explain almost nothing, and the pattern the other two rows imply was the wrong intuition, not the number.** 🔴 **The v4.0 decision to leave it alone is vindicated and is the precedent to follow: low confidence in a printed figure is not licence to edit it.**

**2. THE TIER CUT-POINTS DID NOT MOVE, AGAINST THIS DOC'S OWN PREDICTION.** ⚠️ v4.0 said "the tier cut-points (15.25 / 17.0) will move." `[measured 2026-09-01]` **the terciles of trailing outs in the new sample sit at 15.250 / 16.875, and v4.0's own cuts split the sample 32.7% / 34.0% / 33.3% — as near an even third as makes no difference.** ✅ **The cut-points are KEPT AT 15.25 / 17.0.** ⛔ **The 16.875 tercile is a DIAGNOSTIC and was NOT adopted — moving a cut point after seeing the fit is a new model choice and needs its own pre-registration. This is recorded so nobody re-derives it as an improvement.**

### ⚠️ Which β to use — the outs model is TIERED IN `k` BUT POOLED IN PITCH COUNT

**This doc ships a per-tier `k` alongside a single pooled pitch-count β. That asymmetry is deliberate. Read it this way:**

| Term | Shipped value | The other value on this page, and why it is NOT shipped |
|---|---|---|
| **`k`** (trailing-outs slope) | **TIERED: 0.629 / 0.647 / 0.361** | The pooled **0.5155** in the coefficient table is a reference figure only. |
| **pitch count** | **POOLED: 0.0366** | The per-tier βs (0.0406 / 0.0261 / 0.0190) are **diagnostic, not for pricing** — the long tier's is still not significant (t=1.52), and the robustness sweep below was run on the pooled term. |

⛔ **Do not "tidy" this by tiering the pitch-count term. That would be a new model choice and it needs a pre-registered test in `claude/owed-tests.md` first.**

⚠️ ~~**`[flagged Aug 21 — NOT fixed]` The mid tier's `R² = 0.023` … may be a dropped digit (0.23?).**~~ ✅ 🔴 **RESOLVED 2026-09-01 AT THE SEPTEMBER RE-FIT, EXACTLY AS THIS LINE ASKED: it re-fits at `0.0196`. It was NOT a dropped digit.** ⛔ **The mid tier genuinely explains ~2% of the variance. Still do not build an argument on it — but the number was always right.**

**Direction is unchanged from v3.4 — long-outing starters regress hardest — but every magnitude roughly doubled.** Long-outing starters also have almost no explainable variance (R² 0.011): most of them go 18 outs, there is nothing to predict. **Do not expect model edge on a workhorse's outs line. The edge is on the short/erratic end.**

### ⚠️ Outs → probabilities: the distribution is ASSUMED, never fitted

The outs model above produces **`mu` and nothing else** — that is why this assumption went undocumented for weeks. Every outs probability the project quotes is computed as:

```
P(outs) = Normal(mu, SD = cvO × his season mean outs)
```

where `cvO` is the pitcher's coefficient of variation from `claude/mlb-pitcher-database.md`, computed with the **SAMPLE standard deviation (n−1)**.

🔴 ⚠️ ~~**This distribution has NEVER been fitted.** Normality of the outs distribution is an assumption, not a result.~~ ✅ 🔴 **T3 RAN 2026-09-01 AND PASSED ON ALL THREE PRE-REGISTERED CRITERIA. THE ASSUMPTION IS NOW A MEASUREMENT.**

`[measured 2026-09-01, n = 3,084 standardised residuals]` **`(actual − mu) / (cvO × his season mean outs)`, with `cvO` on the SAMPLE SD (n−1):**

| Statistic | Measured | Pre-registered bar | |
|---|---|---|---|
| mean | **+0.0543** | within ±0.10 of 0 | ✅ PASS |
| SD | **1.0772** | within ±0.15 of 1.0 | ✅ PASS |
| 10% quantile | **−1.3528** | within ±0.20 of −1.282 | ✅ PASS |
| 90% quantile | **+1.3356** | within ±0.20 of +1.282 | ✅ PASS |

✅ 🔴 **THIS IS THE SINGLE MOST LOAD-BEARING RESULT IN THE RE-FIT.** **Every outs probability this project has ever quoted rested on an untested assumption; it is now tested and it holds.** ⚠️ **Read the residual SD honestly: at 1.077 the tails are ~8% FATTER than Normal, so a quoted outs probability is very slightly over-confident at the extremes** — inside the pre-registered bar, worth nothing on a 15.5 rung, worth naming on a far alt rung.

---

# 🔴 THE PREVIOUS-START TERM WAS THE WRONG VARIABLE

`[measured]` v3.4's proudest finding was **previous start's OUTS, β=+0.188, t=4.95** — "the largest single gain in the project." On the complete sample it does not survive contact with the right variable.

| Model | prev-start OUTS β | t | prev-start PITCH COUNT β | t | R² |
|---|---|---|---|---|---|
| outs only | +0.0706 | 3.23 | — | — | 0.1560 |
| **pitch count added** | **−0.0004** | **−0.02** | **+0.0371** | **5.51** | **0.1649** |

**With pitch count in the model, previous-start outs is exactly zero.** It was never "how deep he went last time." It was **how many pitches he threw last time**, and outs was a noisy proxy for it.

Two things follow:

1. 🔴 **v3.4's +0.188 was inflated by broken data.** On a 40%-complete log, "his last 8 starts" often spanned three months, so the trailing mean was measured with large error. Classic **attenuation bias** shrinks a mis-measured predictor's coefficient and lets a correlated one absorb the slack. Repair the trailing mean (0.19–0.38 → 0.525) and the borrowed signal goes home.
2. ✅ **The direction Sam guessed is confirmed and it is PERSISTENCE, not fatigue.** More pitches last time → MORE outs this time. A high pitch count is the manager telling you he trusts this arm. It does not tire him for the next turn.

⚠️ **Pitch count is now a MANDATORY input.** It is in the statsapi game log as `numberOfPitches`, free, for every start.

---

## RE-TESTED ON THE FULL SAMPLE

| Variable | v4.0 β (t) | 🆕 v5.0 β (t), n=3,089 | Verdict |
|---|---|---|---|
| **Opponent K → OUTS** | −0.057 (−0.34) | **−0.1468 (−0.90)** | ✅ 🔴 **STILL NULL.** Struck in v4.0, stays struck. |
| **Handedness (L/R) → K** | +0.046 (0.97) | **+0.0978 (+1.09)** | ✅ **Still null.** Third consecutive sample. |
| **Days of rest → OUTS** | −0.0437 (−3.98) | **−0.0326 (−3.55)** | ⚠️ **Still significant, still NEGATIVE, still confounded** (extra rest follows short starts, injuries, skipped turns). ⛔ **Do not price it.** |
| 🆕 **Prev-start OUTS, with pitch count in** | −0.0004 (−0.02) | **+0.0089 (+0.37)** | ✅ 🔴 **STILL DEAD.** v3.4's headline stays buried. |

✅ 🔴 **ALL FOUR NULLS HELD ON A FRESH, INDEPENDENTLY-SOURCED SAMPLE. NOT ONE CAME ALIVE.** ⚠️ **And the register's warning that several were "declared on the partial log and never re-run" is now discharged for these four** — they have been re-run on 3,089 point-in-time rows drawn from a 4,056-start season log.

🔴 **The opponent splits in two.** Opponent K-rate predicts the pitcher's STRIKEOUTS (t=5.46) and has **no effect at all** on his OUTS (t=−0.34). v3.4 applied an opponent correction to both. **Apply it to K only.**

---

## What changed and why it matters

| | v3.4 | v4.0 | Why |
|---|---|---|---|
| Sample | ~1,500 partial starts | **3,820** — frozen fit sample, complete *as of Aug 20* (live population is now 3,838) | backfill |
| Pitcher trailing (K) | 0.564 | **0.673** | attenuation removed |
| Pitcher trailing (outs) | 0.19–0.38 | **0.32–0.76** | attenuation removed |
| Previous start | outs, +0.188 | **pitch count, +0.0371** | right variable found |
| Opponent → outs | +0.141 | **NULL** | was an artifact |
| Home/road | ±0.092 K | **±0.151 K** | real and bigger |

**The through-line: almost every coefficient was biased toward zero because the inputs were measured on a broken history.** The model was systematically under-confident in a pitcher's own recent form. That is the single most important correction in this project's history and it argues for keeping the game-log backfill current — a stale log silently shrinks every coefficient it feeds.

---

# ✅ RESOLVED (Aug 20) — the opponent database was rebuilt to match the fitted variable

⚠️ **THIS WHOLE SECTION IS HISTORY, NOT CURRENT STATE.** Every figure in it describes the **Aug 20** rebuild. The live opponent metric **and its centering constant** are owned and stated internally by **`claude/mlb-opponent-database.md`**, which was rebuilt again on **Aug 21 over 3,838 starts**. ⛔ **Read them there. Nothing printed in this section is usable as a constant.**

`[measured]` **Aug 20.** The refit briefly created a **new** version of the project's own documented opponent-metric bug: the 0.575 coefficient was fitted on a **rolling statsapi** opponent mean (league 4.74), while `claude/mlb-opponent-database.md` still served a **StatMuse merged-L+R** number (league 5.01). Plugging one into the other adds **+0.15 K to every projection for a perfectly average lineup.**

✅ **Fixed the same session by rebuilding the opponent table from the same statsapi pull.**

🔴 ~~"It now reads **league mean 4.735, n≈127 per team**, and `Δ E[K] = (meanK − 4.735) × 0.575` is computed on the variable the coefficient was fitted on."~~ — **struck Aug 21. It was written in the present tense under a ✅, and the present tense is now false; a skimmer reads 4.735 as the live constant. It is not.**

**What was true:** *as of Aug 20*, that rebuild read league mean 4.735 at n≈127 per team.
**Replaced by:** the table has since been rebuilt again, over 3,838 starts, and **states its own centering constant internally**. The correction to apply is

> `Δ E[K] = (meanK − [the centering constant stated in claude/mlb-opponent-database.md]) × 0.575`

computed on the variable the coefficient was fitted on. ⛔ **4.735 is retired. Read both the meanK and the constant from that doc, every time.**

⚠️ `[HISTORY — Aug 20. Neither figure below is a live constant.]` **4.742 vs 4.735 — both were correct on Aug 20 and they are not the same quantity.** 4.742 was the mean of the opponent value **across the 2,819 training rows** (each start's rolling opponent mean at the time it was thrown). ~~4.735 is the **season mean across all 3,820 starts**.~~ 🔴 **Re-worded Aug 21 — "all 3,820 starts" read as a live population statement.** **Replaced by: 4.735 was the season mean across the 3,820-start FROZEN FIT SAMPLE** — a historical figure, **not today's population (3,838) and not today's constant.** The 0.007 difference was immaterial — it moved TB by 0.01 K — **but centre on the constant that `claude/mlb-opponent-database.md` states, and read it from there every time — do not copy a constant that lives in another doc.**

`[measured 8/21]` **The opponent table was REBUILT over 3,838 starts and states its own centering constant internally — ⛔ that stated constant is the one to centre on, and it is read from `claude/mlb-opponent-database.md`, never from any number printed on this page.** ~~"…that stated constant, not the 4.735 above, is the one to centre on."~~ 🔴 **Re-worded Aug 21: an instruction should name the doc that owns the constant, not the retired number it replaced — naming the number is what gets the number copied.** The rebuild moved it by ~0.003, worth ~0.0015 K. **The drift is trivial; the copied-constant pattern is not.** A hard-coded copy is silently wrong the moment the table behind it is rebuilt, and it does not announce itself.

⛔ **NEVER mix scales.** If a future session pulls an opponent number from anywhere other than `claude/mlb-opponent-database.md`, **re-derive that source's own league mean and centre on it.** In every other case, **centre on the constant `claude/mlb-opponent-database.md` states.** ~~"…re-derive its league mean and centre on that, **not on 4.735**."~~ 🔴 **Re-worded Aug 21 — same reason as above.** ⛔ **No number printed anywhere on this page is a centering constant. 4.735 and 4.742 are both retired historical figures.** The historical StatMuse fits of this same coefficient ran **0.427–0.517** on a differently-constructed variable; **a coefficient is only valid on the variable it was fitted on.**

---

# ✅ ROBUSTNESS — the pitch-count result is not an artifact of my filters

`[measured]` The headline finding was re-run across five specifications. **Prev-start pitch count is significant in all five. Prev-start outs is significant in none.**

🆕 **RE-RUN IN FULL 2026-09-01 ON THE NEW SAMPLE. The v4.0 table is kept directly beneath it.**

| Spec (min prior / min opp / window) | n | k | prev OUTS β (t) | prev PITCH COUNT β (t) | R² |
|---|---|---|---|---|---|
| **3 / 20 / 8 — SHIPPED** | 3,089 | 0.511 | +0.0089 (**0.37**) | **0.0354 (5.51)** | 0.1614 |
| 5 / 30 / 8 — strict | 2,640 | 0.487 | +0.0230 (0.88) | **0.0273 (3.86)** | 0.1084 |
| 2 / 10 / 8 — loose | 3,463 | 0.512 | +0.0054 (0.23) | **0.0404 (6.73)** | 0.1973 |
| 3 / 20 / **5**-start window | 3,089 | 0.480 | −0.0189 (−0.76) | **0.0402 (6.34)** | 0.1585 |
| 3 / 20 / **12**-start window | 3,089 | 0.542 | +0.0153 (0.64) | **0.0335 (5.22)** | 0.1659 |

**Pitch count ranges 0.0273–0.0404 with t from 3.86 to 6.73 — SIGNIFICANT IN ALL FIVE. Previous-start outs ranges −0.019 to +0.023 with |t| never above 0.88 — SIGNIFICANT IN NONE.** ✅ **k is stable at 0.480–0.542 across every window.**

✅ 🔴 **THIS IS THE SECOND INDEPENDENT FIVE-SPEC SWEEP OF THE SAME HEADLINE, ON A DIFFERENT DATASET, AND IT AGREES SPEC-FOR-SPEC WITH v4.0's — including the ORDERING (loose > 12-window > shipped > 5-window > strict on R²).** ⚠️ **v4.0's table, below, is kept for comparison and is not superseded prose.**

<details><summary>v4.0's sweep, Aug 20, kept for comparison</summary>

| Spec | n | k | prev OUTS β (t) | prev PITCH COUNT β (t) | R² |
|---|---|---|---|---|---|
| **3 / 20 / 8 — shipped** | 2,819 | 0.525 | −0.0004 (**−0.02**) | **0.0371 (5.51)** | 0.165 |
| 5 / 30 / 8 — strict | 2,382 | 0.507 | +0.0179 (0.65) | **0.0283 (3.77)** | 0.113 |
| 2 / 10 / 8 — loose | 3,188 | 0.522 | +0.0011 (0.04) | **0.0415 (6.63)** | 0.204 |
| 3 / 20 / **5**-start window | 2,819 | 0.488 | −0.0260 (−0.99) | **0.0423 (6.35)** | 0.161 |
| 3 / 20 / **12**-start window | 2,819 | 0.550 | +0.0065 (0.26) | **0.0356 (5.29)** | 0.169 |

</details>

---

# 🔴 T1 — CLOSED-FAILED 2026-09-01. `E[outs]` DOES NOT ENTER THE STRIKEOUT MODEL.

**One specification, exactly as pre-registered in `claude/owed-tests.md`: add the v5.0 `E[outs]` projection (point-in-time) as a single extra term to the strikeout OLS. Nothing else changed.**

| | |
|---|---|
| β | **+0.1001** |
| t | **+3.39** |
| R² | 0.1563 → 0.1595 |
| **ΔR²** | **+0.00313** |
| n | 3,089 |
| **Pre-registered bar** | **\|t\| ≥ 2.5 AND ΔR² ≥ +0.005** |
| **Result** | 🔴 **FAILED — the ΔR² bar is missed by 37%.** |

🔴 **THIS IS THE ENTRY WORKING EXACTLY AS DESIGNED, AND IT IS WORTH DWELLING ON.** **`t = 3.39` on its own reads like a find** — it would have been written up as one under v3.4's standards, and the mechanism is genuinely real (a strikeout count IS bounded by how long he is on the mound). ⛔ **But the pre-registered bar was a CONJUNCTION, fixed before the data was seen, precisely because this project has been burned by a large `t` on a term that explains nothing.** ✅ **It explains 0.3% additional variance. The bar caught it.**

⛔ **DO NOT re-run this with a different functional form, an interaction, or a tier split. The entry is CLOSED-FAILED.** ⚠️ **The Lambert start that opened T1 (86.1%, pulled after 79 pitches, 3 K) remains what the entry always said it might be: a 14% outcome landing.**

🔴 **This is the check v3.4 never ran on its own headline.** The +0.188 previous-start-outs term was shipped on a single specification and celebrated as the project's biggest find. **One filter sweep would have shown how fragile it was.** Run this table on any future headline coefficient before writing it into the model.

---

# ✅ 🔴🔴 CODE-DEBT — CLOSED 2026-09-11. `card.py` NOW SHIPS v5.0.

`[opened 2026-09-01 from a fresh clone of `github.com/smh0602/gizmos-picks`, `card.py` model block · CLOSED 2026-09-11]`

⛔ ~~**THE PUBLISHED MODEL AND THE SHIPPED CARD NOW DISAGREE, AND THE CARD IS THE ONE SAM READS.** ⛔ **The re-fit is therefore NOT complete.**~~ ✅ **CLOSED 2026-09-11 — all 13 stale constants applied and `MODEL_VERSION` bumped to `"v5.0"` in the same commit.** **A headless run cannot push, cannot run the workflow and cannot test, so this block was the handover; an interactive session applied it.**

🔴 **IT TOOK TEN DAYS, AND THE ONLY THING THAT NOTICED WAS A SCHEDULED GRADING RUN RE-REPORTING IT INTO A LIST NOBODY WAS READING.** ⚠️ **And the one-line form of that report — *"model_version v4.0 nine days after v5.0 published"* — reads like a STALE LABEL, which is how it got triaged as cosmetic on 2026-09-10 and left another day.** ⛔ **It was not a label. The card GENUINELY RAN v4.0, so the stamp was CORRECT and the card was honest about itself.** ➡️ **"Fixing the label" would have been the worst available action: stamping v5.0 onto v4.0 coefficients is a FALSE PROVENANCE CLAIM on a page Sam bets real money against.** ✅ **The coefficients are the fix; the stamp follows them.**

| constant in `card.py` | v4.0 (shipped until 09-11) | **v5.0 (this page, shipped 09-11)** | delta | |
|---|---|---|---|---|
| `K_INTERCEPT` | ~~4.939~~ | **4.9292** | −0.0098 | ✅ applied |
| `K_TRAIL_B` | ~~0.673~~ | **0.6653** | −0.0077 | ✅ applied |
| `K_TRAIL_C` | ~~4.949~~ | **4.9454** | −0.0036 | ✅ applied |
| `K_OPP_B` | ~~0.575~~ | **0.5803** | +0.0053 | ✅ applied |
| `K_HOME` | ~~0.151~~ | **0.1449** | −0.0061 | ✅ applied |
| `O_INTERCEPT` | ~~15.899~~ | **15.9121** | +0.0131 | ✅ applied |
| `O_TRAIL_C` | ~~15.903~~ | **15.8988** | −0.0042 | ✅ applied |
| `O_NP_B` | ~~0.0371~~ | **0.0366** | −0.0005 | ✅ applied |
| `O_NP_C` | ~~86.6~~ | **87.2645** | **+0.6645** | ✅ applied |
| `O_HOME` | ~~0.189~~ | **0.1994** | +0.0104 | ✅ applied |
| `O_TIER_B_LO` | ~~0.638~~ | **0.629** | −0.0090 | ✅ applied |
| `O_TIER_B_MID` | ~~0.759~~ | **0.647** | **−0.1120** | ✅ applied — **the largest move in the re-fit** |
| `O_TIER_B_HI` | ~~0.317~~ | **0.361** | +0.0440 | ✅ applied |
| `O_TIER_CUT_LO` | 15.25 | 15.25 | 0 | ✅ unchanged |
| `O_TIER_CUT_HI` | 17.0 | 17.0 | 0 | ✅ unchanged |
| `TRAIL_N` | 8 | 8 | 0 | ✅ unchanged |

**13 of 16 moved. 3 unchanged.**

### ⚠️ AND NOW THE PART THAT ARGUES AGAINST URGENCY, STATED BECAUSE IT CUTS THAT WAY

🔴 **The constants moved. The PRICES barely did.** `[measured on realistic inputs, each fit centred on its own constant]`

| input | v4.0 | v5.0 | gap |
|---|---|---|---|
| trailing-8 K 3.5, easy-K lineup, home | 3.80 | 3.78 | **−0.022 K** |
| trailing-8 K 5.0, high-K lineup, home | 5.45 | 5.42 | −0.028 K |
| trailing-8 K 7.5, easy-K lineup, home | 6.50 | 6.44 | **−0.053 K** (the worst case found) |
| trailing-8 outs 13.5, prevNP 95, home | 14.87 | 14.89 | +0.019 outs |
| trailing-8 outs 19.0, prevNP 95, home | 17.38 | 17.51 | **+0.133 outs** (the worst case found) |

➡️ ✅ **SO: update `card.py`, but ⛔ do NOT tell Sam his cards have been mispriced.** **A 0.05 K shift moves a Poisson rung probability by well under a point, and the outs shift lands on the long tier — the tier this page has said for two versions has almost no explainable variance and should not be carrying model edge anyway.** ⚠️ **The honest summary is "the card is running last month's constants and it barely matters," not "the card is wrong."**

✅ 🔴 **AND THIS TABLE BECAME THE CHECK ON THE EDIT.** `[2026-09-11]` Because the expected outputs were written down BEFORE the change, they verify the application rather than the applier marking its own homework. **The two outs rows reproduced to `14.886` and `17.514` against the `14.89` / `17.51` stated here.** The strikeout side was swept across trailing-8 K 2.5–10.0 and opponent meanK 4.00–5.60, home and road: **worst move −0.056 K against the −0.053 stated here.** ⚠️ **`verify_card.py` could NOT run — every game on that day's board had started, so no card was written and it reported that rather than passing. The coefficients were driven directly instead.**

### ⛔ WHAT AN INTERACTIVE SESSION MUST NOT DO WHEN APPLYING THIS

- ⛔ **Do not paste an opponent centering constant into `card.py`.** ✅ **`card.py` already rebuilds the opponent meanK and takes its centering constant FROM THE SAME PULL** — that is correct and must stay. **`K_OPP_B = 0.5803` is the only opponent number that changes.** ✅ **Honoured 2026-09-11.**
- ⛔ **Do not tier the pitch-count β.** Still a new model choice, still needs a pre-registration. ✅ **Not done.**
- ⛔ **Do not move the tier cut-points to 16.875.** Diagnostic only — see above. ✅ **Not done; 15.25 / 17.0 kept.**
- ✅ **Bump `MODEL_VERSION` to `"v5.0"` in the same commit,** and the three `v4.0` strings in `card.py`'s prose (`confidence_note`, the `MODEL` label, the module docstring). ⚠️ **The stamp was bumped 2026-09-11; the three PROSE strings are still owed — see Still open.**
- ⚠️ ~~**Unrelated and still open in the same file, re-confirmed 2026-09-01:** `in_band` is computed against `TARGET = 2.10` while `PARLAY_BANDS[2]` is `(1.80, 2.20)` … `floor_ok` / `clears_price_floor` write `price > -700` …~~ ✅ 🔴 **BOTH FIXED 2026-09-11, the day before this block closed.** `in_band` now reads its band from `PARLAY_BANDS` in both the parlays and pairs paths, so the flag and the `parlay_rule` prose cannot disagree again (ledger rule 28 owns the bands: 2 legs 1.80–2.20). `price >= -700` in both the pitcher and hitter floors — Sam's rule is "−700, nothing shorter", and the comment above the line already said "the shortest rung he will take". ~~⚠️ **`calibration_warning` still quotes −25.9 / −18.0 and still calls 70–80% "the only band whose record supports its own number" … STILL OPEN.**~~ ✅ 🔴 **STRUCK 2026-09-14, Monday sweep — FIXED IN THE CODE AND THIS PAGE DID NOT KNOW.** `[verified 2026-09-14 from a fresh clone, in this same turn]` **`calibration_warning` now calls `calibration_sentence()`, which is built from `data/latest/record.json` and FAILS TO SILENCE — "there are not enough graded plays yet … treat every one as unproven" — rather than to a stale number. The hard-coded −25.9 / −18.0 survive only inside a dated comment explaining why they were wrong.** ⚠️ 🔴 **AND `claude/betting-project-instructions.md` v5.4 HAD ALREADY RECORDED THIS FIX AS CLOSED ON 2026-09-07 — four days before this page was written re-asserting it as open.** ➡️ **That is the failure this sweep exists for: a struck claim still stated as true in a NEWER doc. Re-read the thing itself, never the doc that describes it.**

### 🔴 THE GUARD THAT WOULD HAVE CAUGHT THIS ON DAY ONE `[added 2026-09-11]`

`test_model_version.py` fingerprints the 16 model constants and pins that fingerprint **beside the version stamp**. **Changing a coefficient without bumping the stamp now fails**, and so does the reverse — proven by flipping one digit and watching it exit 1.

⛔ **It deliberately does NOT assert the coefficient VALUES.** This page owns those, and a copy in a test would be the second-source-of-truth pattern that put v4.0's numbers into `claude/card-blueprint.md` where a card builder read them first.

➡️ **ON THE NEXT RE-FIT: update the constants, bump `MODEL_VERSION`, run that file, and paste the fingerprint it prints.** Three deliberate acts instead of one silent one.

---

## Method notes

- **Point-in-time throughout.** Every predictor at every row is computed from starts strictly BEFORE that start, including the opponent's K-allowed mean (rolling, not season-final). 🆕 🔴 **v5.0 tightened this: rows sharing a DATE cannot see each other either — a whole date is scored before any of its rows is folded into history.** ⚠️ **The one exception is SAMPLE MEMBERSHIP (`min_ip ≥ 20`), stated at the top of this page.**
- Filters: pitcher ≥3 prior starts, opponent ≥20 prior starts faced. 🆕 **v5.0: 4,056 season starts → 3,089 usable rows.** *(v4.0: 3,820 → 2,819.)*
- 🆕 **v5.0 fitted by `numpy.linalg.lstsq` with inference from `(XᵀX)⁻¹s²`.** 🔴 **CHECK 18 SATISFIED: re-solved independently by normal equations with a hand-written Gauss-Jordan inverse — the same routine shape v4.0 used in-browser — and the two agree to `1.6e−14` (K) and `3.1e−14` (outs) on every β.**
- 🆕 **FREE CONTROLS RUN BEFORE FITTING, all passed:** zero domain violations across 4,056 starts (`outs` 0–30, `k` 0–25, `np` 0–160, `bf` 0–60, `h` ∈ {0,1}); exactly **30** distinct opponents and **30** distinct teams; **home 2,029 / road 2,027** — every game produces exactly one of each, so the 2-row gap is the `min_ip` filter and nothing else.
- ⚠️ **The v5.0 start table is on disk at `/home/claude/fit/starts.json` for this session only, and is regenerable in one command from the repo.** ⛔ **Do not treat it as persistent; DO treat `data/latest/pitchers.json.gz` as the standing headless source.**
- ⚠️ *(v4.0's note, kept as history: it was fitted in-browser via THE RECIPE, and `R` lived in a browser tab.)*

## Still open

🔴 **`claude/owed-tests.md` is THE PRE-REGISTRATION REGISTER for this project and it is AUTHORITATIVE.** Its entries each carry a **pass criterion fixed BEFORE the test runs** — some written out as a full specification, some carried only as a row in its status table — and it also carries a **DOC DEBT** list. Maintain owed tests there, not here.

⛔ ~~"It holds **[a hard-coded number of]** owed tests (**T1–T[n]**), each with a written specification and a pass criterion fixed BEFORE the test runs."~~ 🔴 **Struck Aug 21 on three counts** — and the tally is **redacted even inside the strikethrough**, because the rule is that the number is never written on this page at all: the count was **stale** (the register has grown past it and is still gaining), "each with a written specification" was **inaccurate** (several entries are status-table rows, not specifications), and **writing a test count into another doc is a banned pattern in this project.** ⛔ **Name the register. Never write the tally — not here, not anywhere.** Read the current scope from `claude/owed-tests.md` itself. Where this doc and the register disagree, the register wins.

**The list this doc used to keep was already incomplete.** It was missing at least two owed tests — ✅ 🔴 **BOTH OF WHICH ARE NOW CLOSED, AND THE TWO BULLETS BELOW ARE STRUCK 2026-09-07 BY THE MONDAY SWEEP BECAUSE THEY SIT UNDER A "STILL OPEN" HEADING AND READ AS LIVE:**

- ~~**T1 — does `E[outs]` belong in the strikeout model?** `E[K]` is built from per-START rates on both sides and therefore **silently assumes an average-length outing.**~~ 🔴 **CLOSED-FAILED 2026-09-01** — β +0.1001, t +3.39, **ΔR² +0.00313 against a +0.005 bar.** ⛔ **Do not re-run it in another form.** **Full entry above.**
- ~~**T3 — is the outs distribution actually Normal?** See *Outs → probabilities* above: the `Normal(mu, cvO × season mean outs)` assumption has never been fitted.~~ ✅ **CLOSED-PASSED 2026-09-01** on all three criteria (mean +0.0543 · SD 1.0772 · q10 −1.3528 · q90 +1.3356). ⚠️ **Tails ~8% fatter than Normal.** **Full entry above.**

⚠️ 🔴 **THE HISTORICAL POINT THE TWO BULLETS WERE MAKING SURVIVES AND IS WHY THEY ARE STRUCK RATHER THAN DELETED: this page once kept its own owed-test list and that list was incomplete.** ➡️ **`claude/owed-tests.md` is the register. Read the scope there, never from this page.** ⛔ **And the sweep found FOUR OTHER DOCS still calling these two open six days after they closed — `claude/card-blueprint.md`, `claude/mlb-alt-line-protocol.md`, `claude/pitcher-reliability.md` and `claude/mlb-pitcher-database.md` — all now corrected.**

Doc-specific items still tracked here (the register remains authoritative wherever the two overlap):

- ~~🆕 ⚠️ **THREE `v4.0` PROSE STRINGS REMAIN IN `card.py` AFTER THE 2026-09-11 SHIP** — `confidence_note`, the `MODEL` parlay label, and the module docstring … ➡️ **Sweep them in the next `card.py` touch.**~~ ✅ 🔴 **STRUCK 2026-09-14, Monday sweep — ALL THREE WERE ALREADY FIXED WHEN THIS LINE WAS WRITTEN.** `[verified 2026-09-14 from a fresh clone, in this same turn]` **All three now READ `MODEL_VERSION` instead of naming a version in prose: the module docstring says "see MODEL_VERSION below", `confidence_note` is `MODEL_VERSION + " model blended 50/50 with his own rate at this line."`, and the parlay `MODEL` label is `"Every leg is a %s model estimate." % MODEL_VERSION`. Each carries a dated `~~"…v4.0…"~~ STRUCK 2026-09-11` comment beside it.** ➡️ **The generalisable part: this page recorded a to-do for work that the same commit had already done, so the doc was stale on the day it was created. ⛔ A version is a fact about the code — read it from the code, and that applies to the DOC as much as to the string.**
- 🔴 **OWED, PRE-REGISTERED: opponent P/PA → outs, GOOD tier only, single specification, decided before looking.** `[measured] Aug 20` it read **−2.78 (t=−1.68, n=468)** — worth −1.58 outs across the league spread — but ~10 specifications were run that session and at t=1.68 that is inside chance. **Do not adopt it on a re-run that shops for a spec.** Full context in `claude/backtest-results.md` RESULT 8.
- ✅ **Opponent P/PA → PITCH COUNT is REAL: +9.16, t=3.35, R²=0.226.** No pitch-count prop exists in the Odds API market list today. **If one appears, the model for it is already built.**
- Park factors — untested on the full sample; needs a venue join.
- Bullpen state — no source.
- Weather — no historical source; still unpriced by rule.
- ~~**Re-fit again once September starts land.** The tier cut-points (15.25 / 17.0 trailing outs) will move. ⚠️ **Re-check the mid-tier R² = 0.023 at that re-fit.**~~ ✅ 🔴 **BOTH DONE 2026-09-01. The cut-points did NOT move (terciles 15.250 / 16.875; kept at 15.25 / 17.0) and the mid-tier R² was NOT a dropped digit (0.0196).**
- 🆕 **Re-fit again at the OCTOBER re-fit, and run THE RECIPE that time if a browser is available** — the one open question about v5.0 is whether the `min_ip ≥ 20` sample filter matters. ⚠️ **Current evidence says it does not: v4.0's unfiltered coefficients reproduce here to a few thousandths.**
- 🆕 **T2, T12, T18's replacement, T20, T21, T22, T26 are still owed and are NOT blocked on data any more** — the start table this fit used is regenerable headless. **See the execution order in `claude/owed-tests.md`.**

---

## Changelog

- 🆕 ✅ 🔴 **Sept 11 2026 — v5.0 SHIPPED INTO `card.py`. THE CODE-DEBT BLOCK IS CLOSED.** **All 13 stale constants applied verbatim from the CODE-DEBT table and `MODEL_VERSION` bumped to `"v5.0"` in the same commit. Ten days after this page published them.**
  - 🔴 **THE ONE-LINE REPORT THAT DELAYED IT IS WORTH RECORDING.** The scheduled grading run re-reported this for sixteen days as *"model_version v4.0 nine days after v5.0 published"* — **which reads as a stale LABEL**, and was triaged as cosmetic on 2026-09-10 on exactly that reading. ⛔ **It was not a label. `card.py` genuinely ran v4.0, so the stamp was CORRECT and the card was honest.** ➡️ **Stamping v5.0 onto v4.0 coefficients would have been a FALSE PROVENANCE CLAIM. The coefficients are the fix; the stamp follows them.**
  - ✅ **VERIFIED AGAINST THIS PAGE'S OWN PRE-MEASURED IMPACT, which is what made the check real rather than self-assessment:** the two outs rows reproduced to **14.886** and **17.514** against the **14.89 / 17.51** printed here; the strikeout side swept trailing-8 K 2.5–10.0 × opponent meanK 4.00–5.60, home and road, worst move **−0.056 K** against the **−0.053** printed here.
  - ⚠️ **`verify_card.py` COULD NOT RUN** — every game on that day's board had started, so no card was written and it reported that rather than passing. **A tool that says "not exercised" is not a green light**, so the coefficients were driven directly.
  - ✅ **Every "MUST NOT DO" in the CODE-DEBT block was honoured:** no centering constant pasted into `card.py`, the pitch-count β left pooled, the tier cut-points left at 15.25 / 17.0.
  - 🆕 **`test_model_version.py` added** — fingerprints the 16 constants and pins the fingerprint beside the version stamp, so the two halves of a re-fit cannot come apart silently again. ⛔ **It does not assert the VALUES; this page owns those.**
  - ✅ **Two unrelated `card.py` defects fixed the same day, both re-reported since 2026-08-26:** the three-way band-ceiling disagreement (`in_band` now reads `PARLAY_BANDS`, so the flag and the `parlay_rule` prose cannot diverge) and `price > -700` excluding exactly −700 (now `>=`, both floors).
  - ⚠️ **STILL OPEN and newly recorded:** three `v4.0` PROSE strings in `card.py` (`confidence_note`, the `MODEL` label, the docstring) and the stale `calibration_warning` figures.

- 🆕 🔴 **Sept 1 2026 — v5.0 RE-FIT.** **Fitted on 4,056 season starts through 8/31 (3,089 training rows) from `data/latest/pitchers.json.gz` in the collector's repo — NOT from THE RECIPE, which needs a browser this scheduled run did not have.**
  - **Every coefficient re-fitted and every one moved by thousandths.** K: 4.9292 / 0.6653 / 0.5803 / ±0.1449, R² 0.1563. Outs: 15.9121 / tiered k 0.629-0.647-0.361 / 0.0366 / ±0.1994, R² 0.1614. **New centerings 4.9454 (trailing K), 15.8988 (trailing outs), 87.2645 (prev pitch count).**
  - ✅ **T3 PASSED** — the outs distribution IS Normal(mu, cvO × season mean outs) on all three pre-registered criteria. **The assumption every outs probability rests on is now a measurement.**
  - 🔴 **T1 FAILED and is CLOSED** — `E[outs]` in the K model reads t=+3.39 but ΔR²=+0.00313 against a +0.005 bar. **The conjunction bar caught a tempting t.**
  - ✅ **All four established nulls held.** Opponent→outs, handedness→K, prev-start-outs, and rest-days (still significant-negative-confounded). **None came alive.**
  - ✅ **The five-spec robustness sweep re-run in full and agrees with v4.0's spec-for-spec, including the R² ordering.**
  - ✅ **Two flagged items closed as this page asked: the tier cut-points did NOT move, and the mid-tier R² was NOT a dropped digit (0.0196).**
  - 🔴 **CODE-DEBT block added — `card.py` ships v4.0 and 13 of its 16 model constants are now stale.** ⚠️ **Recorded with the pricing impact, which is small: worst case 0.053 K and 0.133 outs.** ✅ **CLOSED 2026-09-11 — see the entry above.**
  - ⚠️ **Known deviation, stated up front: the source applies `min_ip ≥ 20`, a season-total sample filter. Every predictor and grouping variable is point-in-time; sample membership is not.**
  - ⛔ **Nothing from v4.0 was deleted. Superseded values are struck; v4.0's sweep table is kept in a collapsed block; all dated changelog prose below is untouched.**

- **Aug 21 2026 — presentation audit.** 🔴 **No fitted coefficient was changed. Only how they are presented.** Verified against a live re-run of the pull the same day: **340 starters, 3,838 starts, zero domain violations.**
  - **The outs code block was rewritten so the form a reader copies is the form the model uses.** It had shipped the **pooled 0.525** while v4.0 ships a **tiered `k`** (contradicted by this doc's own tier table three lines below it), printed **`0.037`** where the fit is **`0.0371`**, and wrote **`+ 0.189 × HOME`** as a one-sided bonus where the term is two-sided. Now: tiered `k` spelled out inline, `0.0371`, and `± 0.189 (+home, −road)` to match the strikeout block. The pooled 0.525 is retained and labelled as a reference figure.
  - **The strikeout block's `− 4.742` became `− CENTERING CONSTANT`** with an in-block warning, so the copy-pasteable text can no longer be pasted with a retired constant. `claude/mlb-opponent-database.md` owns and states the constant.
  - **Every instruction-shaped `4.735` now names that doc instead of the retired number.** ~~"not the 4.735 above"~~ and ~~"not on 4.735"~~ struck and re-worded; the genuinely historical 4.735 / 4.742 mentions are kept and marked as history.
  - **The `✅ RESOLVED` section was re-tensed.** ~~"It now reads league mean 4.735, n≈127 per team"~~ struck — present tense under a ✅, false as of Aug 21 — replaced by a dated historical statement plus a pointer, and the section is now headed as history.
  - **Fit sample and live population were disambiguated.** **3,820 = the frozen Aug 20 fit sample; 3,838 starts by 340 starters = the live Aug 21 population.** The two sentences that read 3,820 as a live population statement were struck and re-worded.
  - **"Refit on the COMPLETE season" qualified** — true on Aug 19–20, not a standing property.
  - **The owed-test count was removed** and replaced with a pointer to `claude/owed-tests.md`. **Project rule: name the register, never the tally.** The old line was stale and also wrong that every entry carries a full specification.
  - **Added:** an explicit "which β to use" note — v4.0 is **tiered in `k` but pooled in the pitch-count β**, and that asymmetry is intentional.
  - **Flagged, not fixed:** the mid-tier **R² = 0.023** may be a dropped digit. **The number was left exactly as fitted**; re-check at the September re-fit.
