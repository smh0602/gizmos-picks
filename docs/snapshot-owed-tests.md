# OWED TESTS — the pre-registration register

**Created Aug 21 2026.** Every test this project owes itself, in one place, **written down BEFORE it is run.**

## Why this exists

🔴 **The project's two worst errors were both specification-shopping.** v3.4's headline coefficient (previous-start outs, +0.188, t=4.95) was shipped on **one** specification and died at **t=−0.02** the moment a filter sweep ran. The GOOD-tier P/PA result read **t=−1.68 after ~10 specifications** — inside chance, and it was only caught because someone counted the specs.

➡️ **A test decided after looking at the data is not evidence.** Each entry below states **the exact specification** and **what counts as a pass**, *before* it runs. **Log the result whichever way it falls. An entry may be marked FAILED and closed — it may never be quietly rewritten.**

---

# 🔴🔴 2026-09-01, 17:00Z — **CORRECTION: THE RE-FIT DID RUN.** THE BRIEF BELOW WAS WRITTEN ON A FALSE PREMISE.

⛔ **THE SECTION IMMEDIATELY BELOW SAYS THE RE-FIT COULD NOT RUN HEADLESS. THAT WAS WRONG, AND IT HAD BEEN WRONG FOR THREE CONSECUTIVE SCHEDULED RUNS.** ⚠️ **It is NOT deleted — the strike is the record, and the reasoning error is the most useful thing on this page.**

🔴 **THE ERROR, PRECISELY: "the re-fit needs THE RECIPE" was read as "the re-fit needs a browser."** ✅ **What the re-fit actually needs is a full-season start table carrying `isHome`, `numberOfPitches` and `battersFaced` — and the collector has been storing exactly that, every night, in `data/latest/pitchers.json.gz`, in the repo these runs were ALREADY CLONING for other reasons.**

➡️ ⛔ **STANDING RULE, ADDED BECAUSE THIS COST A MONTH: BEFORE DECLARING A HEADLESS RUN BLOCKED ON DATA, `ls data/latest/` AND READ WHAT IS THERE. One command, zero credits.** ⚠️ **And the browser half was checked too and is a genuine block: the container's Chromium launches and tunnels to github, but the proxy refuses `CONNECT` to `statsapi.mlb.com` and `baseballsavant.mlb.com` (`ERR_TUNNEL_CONNECTION_FAILED`). THE RECIPE really cannot run here. The data can.**

✅ **WHAT RAN 2026-09-01 17:00Z, on 4,056 season starts / 3,089 training rows:**
- **The full re-fit** — published as **v5.0** in `claude/mlb-projection-model.md`, with its own CODE-DEBT block.
- **T1 — CLOSED-FAILED** (t=+3.39, ΔR²=+0.00313 against a +0.005 bar). See the entry.
- **T3 — CLOSED-PASSED** on all three criteria. See the entry.
- **All four established nulls re-run — all held.** Opponent→outs (t=−0.90), handedness→K (t=+1.09), prev-start-outs with pitch count in (t=+0.37), rest-days (t=−3.55, still negative and confounded).
- **The five-spec robustness sweep, re-run in full** — pitch count significant in all five, prev-start outs in none, `k` stable 0.480–0.542.
- **Tier cut-points re-checked — they did NOT move.** **Mid-tier R² re-checked — 0.0196, NOT a dropped digit.**
- **Check 18 satisfied** — numpy vs an independent Gauss-Jordan solve agree to 1.6e−14.

⛔ **STILL NOT RUN, AND STILL CORRECTLY BLOCKED: everything needing an ODDS PULL (T17), a browser-only source (T8's collection), or a source that does not exist (T13b weather).** ⚠️ **Everything else in the execution order below is NO LONGER BLOCKED ON DATA and can be run headless from the same file.**

---

# 🗓️ ~~2026-09-01 — THE SEPTEMBER RE-FIT DID NOT RUN. READY-TO-RUN BRIEF FOR THE NEXT INTERACTIVE SESSION.~~ 🔴 **SUPERSEDED 17:00Z — SEE THE CORRECTION ABOVE. The execution order below is still the right order; only its "interactive session" premise is struck.**

`[written 2026-09-01, 4am ET scheduled monthly re-fit firing]`

🔴 **THE RE-FIT NEEDS THE FULL SEASON START TABLE AND THAT COMES ONLY FROM THE RECIPE (`claude/mlb-data-stack.md`), WHICH NEEDS CLAUDE IN CHROME. A SCHEDULED RUN HAS NO BROWSER, SO NOTHING WAS FITTED.** ⛔ **No substitute dataset was improvised: no StatMuse rebuild (retired, row-capped, wrong scale), no `claude/data-starts-h.csv.md` restore (forbidden — the 40% log cost a model version), no repo-log patchwork.** ✅ **That is the correct outcome for a headless firing, not a failure to conceal.** ⛔ **NO ENTRY WAS CLOSED, NO SPECIFICATION WAS ALTERED, AND NO COUNTER WAS MOVED BY THIS RUN.**

## What this firing DID verify, dated 2026-09-01

- ✅ **Every open entry above was re-read against its own wording. No quiet re-specification was found**: each open Tier-1/Tier-2 entry still carries the specification and pass criterion it was registered with, and every closed entry's verdict matches its own registered bar (T18's mean-K spec is still CLOSED-FAILED with the threshold cut still labelled EXPLORATORY; T27–T33's fail verdicts all cite their own pre-registered margins).
- ✅ **Every sample-size trigger was checked against `claude/pick-ledger.md` and `claude/calibration-accumulators.md`. NONE has been met**, because no TABLE A card has been built since 8/22:
  - **T4** — 60–70% bucket **n = 17 / 30**. NOT met. Leave open.
  - **T6** — **1 / 10** instances. NOT met.
  - **T11** — **25 / 40** distinct carded starts. NOT met. (The machine card would clear it in one slate; merging it is a population change and stays forbidden without its own pre-registration.)
  - **T15** — **31 / 100** carded plays. NOT met; argmin sits on the `w = 1.00` boundary, which its own entry marks as a warning. **The 50/50 stands.**
  - **T19** — **1 / 10** instances. NOT met — and with `us_dfs` banned from every pull, new instances can only come from Sam's app, not from the feed.
  - **T17** — **1 / 40** captured lines. ⛔ **BLOCKED** — price capture is interactive-only (ledger rule 38).
  - **T23 / T24** — **5 / 30** outs plays on their shared counter. **Their own decision clause requires n ≥ 30 — if the counter still reads under 30 when the interactive re-fit sits down, the three-way comparisons CANNOT be decided; report them as open-for-lack-of-n rather than deciding on 5.**
  - **T25** — **0 joined team totals.** Storage exists from 8/22 forward; the JOIN has never been done. See execution step 13.
- 🔴 **BLOCKED entries, reported as blocked:** **T13b** (weather) — no historical temperature/wind source exists in the stack; ⛔ never mark it confirmed and never substitute the roof proxy. **T17** — needs captured prices (LINE VALUE n = 0). **T10** — needs a live Odds API market-list read; a Claude scheduled run has no key.
- ⚠️ **T8 and T9 carry STATUS ROWS, not written specifications.** ➡️ **Before running either, write its one-specification pre-registration into this register — spec and pass bar BEFORE the data is touched.**
- ✅ **`card.py`'s model block was compared against `claude/mlb-projection-model.md` constant by constant** (the block at `card.py` ~lines 48–70: both intercepts, both trailing slopes and centering constants, the opponent slope, both home/road terms written as ±, the pitch-count term and its centering, the tier cut-points and all three tiered `k` values, the 8-start trailing window, the 50/50 blend, and sample-SD `cvO`). 🔴 **EVERY ONE MATCHES v4.0 EXACTLY, the tiered `k` is applied per tier, and home/road is two-sided.** ➡️ ~~**So on the day the re-fit publishes new values, `card.py` is stale ON EVERY CONSTANT THAT MOVED — see execution step 14.**~~ ✅ **AND THAT IS EXACTLY WHAT HAPPENED, FOR TEN DAYS.** v5.0 published 2026-09-01; `card.py` ran v4.0 until **2026-09-11**, when all 13 moved constants were applied and `MODEL_VERSION` bumped in the same commit. **The prediction in this line was correct and nothing acted on it** — see ledger rules 183–184.

## Execution order for the interactive session

⛔ **The entries above OWN their specifications and pass bars. Run each ONCE, exactly as its entry states, and close it whichever way it falls — including FAILED. Nothing here restates a bar, so nothing here can drift from one.**

1. **Rebuild the data.** THE RECIPE (`claude/mlb-data-stack.md`) — full season start table with `isHome`, `numberOfPitches`, `battersFaced`; domain-check every row; rebuild `claude/mlb-pitcher-database.md` (must reproduce the two named acceptance-test pitchers to four decimals; `cv` on the SAMPLE SD, n−1) and `claude/mlb-opponent-database.md` (verify all 30 `n` against standings; the new centering constant is stated internally there and nowhere else). **Every predictor AND every grouping variable point-in-time.**
2. **T20** — count vs rate form for the strikeout model. Run FIRST: it decides the form everything downstream is interpreted on.
3. **T1** — `E[outs]` in the strikeout model.
4. **T2** — opponent P/PA → outs, GOOD tier only.
5. **T3** — the outs distribution's Normality. Run BEFORE T26, per T26's own note.
6. **T26** — outs under/over calibration asymmetry.
7. **T22** — the shuttled-starter term.
8. **T21** — small-sample shrinkage of the raw rate.
9. **T18's replacement specification** — the rematch threshold form, ≥ 400 pairs.
10. **T12** — the tails-only opponent rule's quintiles.
11. **T13a** — parks · roof/dome PROXY · team record, one specification each; report the roof result as the PROXY, never as "weather".
12. **The re-fit proper.** Same construction as v4.0 (its Method notes state the filters); publish ONE canonical specification with its filters and n in `claude/mlb-projection-model.md`, strike superseded values, BUMP THE VERSION STAMP; re-check the tier cut-points and the flagged mid-tier R² = 0.023; run the five-specification robustness sweep on any coefficient that changed; verify any hand-rolled OLS against a reference implementation (check 18).
13. **T25** — JOIN the stored `board.json` de-vigged team totals (2026-08-22 forward only — earlier is permanently unreachable) to the start table, report the joined n on the counter, then run once as specified.
14. **The code-debt pass.** Compare every constant in `card.py`'s model block against the new fit, name each one that moved and by how much, and write the comparison into `claude/mlb-projection-model.md` as an explicit CODE-DEBT block. 🔴 **A re-fit that updates the doc and stops has shipped nothing — the card is the surface Sam reads.** ⛔ **Do not describe the re-fit as complete while the published model and the shipped card disagree.** 
    ✅ **v5.0's code-debt pass CLOSED 2026-09-11** — 13 of 16 constants applied verbatim from the CODE-DEBT block, the other three (both tier cut-points, the 8-start window) unmoved. ~~`card.py` hard-codes v4.0~~ — it ships **v5.0**. ⚠️ **IT TOOK TEN DAYS, AND THIS STEP EXISTED THE WHOLE TIME.** Having the rule written down is not the rule firing (ledger 183). 
    ➡️ **STEP 14 NOW HAS A GUARD.** `test_model_version.py` fingerprints the 16 constants and pins that fingerprint beside `MODEL_VERSION`, so a coefficient that moves without the stamp moving is a red CI run. **The next re-fit is three deliberate acts: update the constants, bump the stamp, paste the fingerprint.** ⛔ The test must never assert the VALUES — `claude/mlb-projection-model.md` owns those, and a copy is the second-source-of-truth pattern that once put v4.0's numbers into `card-blueprint.md`.
15. **T15** — restate the Brier accumulator; at n = 31 the weight is not adoptable, and a machine-population version needs its own pre-registration first.
16. **T8** — the full-season times-through-order collection (browser), after pre-registering its specification per the note above.

⚠️ **Tier 1's "(Sept 1)" date is now history: the 2026-09-01 scheduled firing was headless and could not run these. The Tier-1 entries are owed to the next interactive session, in the order above.**

---

# 🔴 TIER 1 — pre-registered, run at the monthly re-fit (Sept 1)

## T1. ✅ 🔴 **CLOSED — FAILED 2026-09-01.** Does `E[outs]` belong in the strikeout model? **NO.**

`[opened Aug 21 2026 — Lambert]`

**The observation.** Lambert o3.5 K was carded at **86.1%**, the highest-confidence play on the 8/20 board, because the Angels are the **2nd-easiest lineup in baseball to strike out** (5.56 meanK, +0.47). They scored **18 runs**, he was pulled after **79 pitches in 3.2 innings**, and he struck out **3**.

**The mechanism.** `E[K] = 4.939 + 0.673×(his mean K per start) + 0.575×(opponent meanK per start) ± 0.151`. **Both predictors are per-START, so both silently embed an AVERAGE outing length.** A strikeout count is bounded by how long he is on the mound, and **nothing in the K equation knows how long that will be.** The outs model exists, is fitted, and is never consulted when pricing a strikeout line.

**⚠️ The counter-argument, which is measured and strong.** Opponent → outs is a **measured null, t=−0.34 on 2,819 rows.** A tough lineup does **not** shorten a start on average. **So this may be nothing but a 14% outcome landing.** ⛔ **Do not patch the model off one start.**

| | |
|---|---|
| **Specification** | Add `E[outs]` (the v4.0 outs projection, computed point-in-time) as a single additional term to the v4.0 strikeout OLS. **Nothing else changes.** |
| **Sample** | The same 2,819 training rows |
| **Pass** | **\|t\| ≥ 2.5 AND ΔR² ≥ +0.005** |
| **Fail** | Anything less. **Record it as FAILED and close the entry.** |
| ⛔ **Forbidden** | Trying a second functional form, a tier split, or an interaction **after** seeing the first result. **One specification.** |

### 🔴 RESULT — RAN ONCE, EXACTLY AS SPECIFIED. **FAILED.** `[measured 2026-09-01, v5.0 re-fit]`

| | Measured | Pre-registered bar | |
|---|---|---|---|
| β | **+0.1001** | — | |
| t | **+3.39** | \|t\| ≥ 2.5 | ✅ met |
| **ΔR²** | **+0.00313** (0.1563 → 0.1595) | **≥ +0.005** | 🔴 **MISSED by 37%** |
| n | 3,089 | | |

🔴 **VERDICT: FAILED. The bar was a CONJUNCTION and both halves were required. THE ENTRY IS CLOSED.**

⚠️ 🔴 **THIS IS THE ENTRY DOING ITS JOB AND IT DESERVES THE SENTENCE: `t = 3.39` ON ITS OWN LOOKS LIKE A FIND.** **Under v3.4's standards it would have been shipped — the mechanism is real, a strikeout count IS bounded by how long he is on the mound, and the entry itself called that mechanism plausible.** ✅ **It explains three tenths of one percent of additional variance, and the conjunction bar — written down before the data was touched — is the only thing that separates it from v3.4's `+0.188`.**

⛔ **DO NOT re-run with a different functional form, an interaction, a tier split or a filter sweep. That is specification shopping and this register exists to stop it.** ⚠️ **The Lambert start that opened T1 stands as what the entry always allowed it might be: a 14% outcome landing.**

## T2. Opponent P/PA → outs, GOOD tier only

`[carried from claude/backtest-results.md RESULT 8 — opened Aug 20]`

**Read −2.78 (t=−1.68, n=468)** — worth −1.58 outs across the league spread. **~10 specifications were run that session.** At t=1.68 that is inside chance.

| | |
|---|---|
| **Specification** | Opponent P/PA (`numberOfPitches ÷ battersFaced`, rolling, point-in-time) added to the v4.0 outs model, **GOOD tier only** |
| **Pass** | **\|t\| ≥ 2.5**, single specification |
| ⛔ **Forbidden** | Re-running across tiers and reporting the best one. **That is exactly how it got to −1.68.** |

## T3. ✅ 🔴 **CLOSED — PASSED 2026-09-01.** Is the outs distribution actually Normal(mu, cvO × season mean outs)? **YES.**

`[opened Aug 20 — it was never fitted at all]`

🔴 **Every outs probability this project has ever quoted rests on an assumption nobody tested.** The outs model produces `mu` and **no distribution.** The card assumes **Normal with SD = cvO × his season mean outs.**

| | |
|---|---|
| **Specification** | Compute the standardised residual `(actual − mu) / (cvO × mO)` across all 2,819 rows |
| **Pass** | Mean within ±0.10 of 0, SD within ±0.15 of 1.0, and the 10%/90% empirical quantiles within ±0.20 of ±1.282 |
| **If it fails** | **Every quoted outs probability in the ledger is miscalibrated by a known amount. Re-derive them before quoting calibration on outs plays again.** |

### ✅ RESULT — RAN ONCE, EXACTLY AS SPECIFIED. **PASSED ON ALL THREE CRITERIA.** `[measured 2026-09-01, n = 3,084]`

| Statistic | Measured | Pre-registered bar | |
|---|---|---|---|
| mean | **+0.0543** | within ±0.10 of 0 | ✅ **PASS** |
| SD | **1.0772** | within ±0.15 of 1.0 | ✅ **PASS** |
| 10% quantile | **−1.3528** | within ±0.20 of −1.282 | ✅ **PASS** |
| 90% quantile | **+1.3356** | within ±0.20 of +1.282 | ✅ **PASS** |

✅ 🔴 **VERDICT: PASSED. THE ENTRY IS CLOSED. `cvO` computed on the SAMPLE SD (n−1), as the entry requires.**

✅ 🔴 **THIS IS THE MOST LOAD-BEARING RESULT THE RE-FIT PRODUCED. Every outs probability this project has ever quoted rested on an assumption nobody had tested; it is now tested and it holds.** ⛔ **No ledger figure needs re-deriving — the "if it fails" clause does not trigger.**

⚠️ **ONE HONEST QUALIFICATION, INSIDE THE BAR BUT WORTH NAMING: the residual SD is 1.077, so the real tails are ~8% FATTER than Normal.** ➡️ **A quoted outs probability is very slightly OVER-confident at the extremes — negligible on a 15.5 rung, worth stating on a far alt rung.** ⛔ **This does NOT reopen the entry and is not a licence to fit a t-distribution; that would be a new model choice needing its own pre-registration.**

---

# ⚠️ TIER 2 — decide at a stated sample size, on principle

## T4. Raise the carding floor to ~70%?

`[opened Aug 21 — two days of agreeing evidence]`

| Bucket | n | Predicted | Actual | Gap |
|---|---|---|---|---|
| **60–70%** | 12 | 64.2% | **41.7%** | **−22.5** |
| **70–80%** | 14 | 75.4% | **78.6%** | **+3.2** ✅ |

**The 8/20 card carded nothing below 71.2% and went 8/10.** ➡️ `[hypothesis]` **the model earns its money above ~70% and gives it back below.**

**DECIDE AT n ≥ 30 IN THE 60–70% BUCKET. Currently 12** *(re-verified 8/21 — unchanged; the 8/20 card added nothing to this bucket)*. ⛔ **Do not adopt on 12. Do not haircut every estimate instead — that would also fix the number and would be fixing the wrong thing.**

⚠️ 🆕 **COUNTER UPDATED 2026-08-22 — n = 13, NOT 12.** **T5 closed the same day and admitted G. Rodriguez u15.5 outs (66.6%, a LOSS) to this bucket.** 🔴 **It now reads 5/13 — 38.5% actual against 64.4% predicted, gap −25.9. The bucket got WORSE, not better.** ⛔ **The n ≥ 30 bar is UNCHANGED and T4 is still NOT adopted at 13.** ⚠️ **The snapshot table above is the 8/21 state and is left as written; the live figures are in `claude/pick-ledger.md`.**

⚠️ 🔴 **COUNTER UPDATED AGAIN 2026-08-23 — n = 17, AND THE BUCKET GOT WORSE FOR THE SECOND CONSECUTIVE RUN.** **The 8/22 card carded FOUR plays in this bucket — Skubal u18.5 outs 66.4 ❌, Skubal u8.5 K 69.7 ❌, Hunter Brown u17.5 outs 62.2 ✅, Martín Pérez o14.5 outs 67.3 ❌ — and they went 1/4.** 🔴 **The bucket now reads 6/17 — 35.3% actual against 64.9% predicted, gap −29.6, from −25.9 and −22.5 before it.** ⛔ **The n ≥ 30 bar is UNCHANGED and T4 is still NOT adopted at 17.**

⚠️ 🔴 **BUT THE 8/22 CARD IS THE FIRST DIRECT EVIDENCE THAT THE PROPOSED FIX WOULD NOT HAVE BEEN ENOUGH, AND THAT BELONGS IN THIS ENTRY BEFORE IT IS DECIDED.** **T4's hypothesis is that the model earns above ~70% and gives it back below.** **On 8/22 the plays carded AT OR ABOVE 70% went 5/9 (55.6%) against a mean estimate of 79.5%.** ➡️ **A carding floor at 70% would have removed four plays and left a 5/9 card.** ⛔ **This does NOT alter the specification, the n ≥ 30 bar, or the decision date. It is one slate, and it is recorded because it cuts against the fix rather than for it.**

## T5. ✅ 🔴 **CLOSED — DECIDED 2026-08-22.** Do conversational picks join calibration? **YES.**

🔴 **This must be decided on principle, and it must be decided BEFORE the next look at the numbers.**

The CALIBRATION table is carded-only by rule. **G. Rodriguez u15.5 at 66.6% lost and is excluded** — it would make the suspect bucket **5/13** instead of 5/12. **The rule is now actively withholding evidence about the one bucket under suspicion.**

⛔ **Deciding this after seeing which way it moves the number is the same error as specification shopping.** **Decide by n=30 or leave the rule alone permanently.**

⚠️ `[8/21]` **The count of excluded plays is now stated explicitly in the ledger: 5 — all conversational, zero `[pre-correction]`, zero from any other table.** **Knowing the size of the excluded set does not license deciding T5 early.**

---

### ✅ 🔴 DECIDED 2026-08-22 — **SAM: *"include them"*.** THE ENTRY IS CLOSED AS **DECIDED**, NOT PASSED AND NOT FAILED.

🔴 **PASS/FAIL WAS NEVER THE RIGHT VERDICT HERE.** **T5 asked a question about a RULE — which population the calibration table measures — not a hypothesis about the world.** ✅ **So it closes as DECIDED.**

✅ 🔴 **IT WAS DECIDED ON PRINCIPLE AND BEFORE THE BUCKET FILLED — WHICH IS EXACTLY WHAT THIS ENTRY DEMANDED, IN ITS OWN WORDS: *"decide it on PRINCIPLE, by n=30, and not after seeing which way it cuts."*** **The 60–70% bucket stood at n=12 against a stated bar of 30 when the decision was taken, and the decision was taken anyway, on the principle rather than on the count.** ⛔ **Nothing was looked at first and nothing was chosen to move the number.**

⚠️ 🔴 **AND THE DECISION CUTS AGAINST THE MODEL'S CURRENT RECORD. STATED FIRST, BECAUSE IT CUTS THAT WAY.** **The plays it admits include G. Rodriguez u15.5 outs — a 66.6% LOSS that lands squarely in the one bucket already under suspicion.** 🔴 **Applied in `claude/pick-ledger.md` the same day, the 60–70% bucket went 5/12 → 5/13, actual 41.7% → 38.5%, gap −22.5 → −25.9. IT GOT WORSE.**

**HOW IT WAS APPLIED — two of the five conversational picks entered, three did not, each for a separately named reason:**

| Conversational pick | Logged PREGAME estimate? | Verdict |
|---|---|---|
| 8/20 — G. Williams o5.5 K | ✅ 76.8%, in a column headed *"Pregame estimate"* | ✅ **IN — 70–80%, W** |
| 8/20 — G. Rodriguez u15.5 outs | ✅ 66.6%, same column | ✅ **IN — 60–70%, L** |
| 8/19 — Skenes u15.5 outs | ⛔ none anywhere | ⛔ **OUT — `[estimate unlogged]`** |
| 8/19 — Messick o4.5 K | ⚠️ 66.6% exists, but only in the POST-MORTEM ladder; the ledger says slips 0 and 1 were never logged pregame | ⛔ **OUT — `[no PREGAME estimate]`, not back-filled** |
| 8/19 — Sasaki o4.5 K | ✅ 72.5% — **but the SAME rung as 8/19 TABLE A row 3** | ⛔ **OUT — 🔴 DUPLICATE, already in calibration** |

⛔ **NO ESTIMATE WAS INVENTED OR BACK-FILLED FOR ANY EXCLUDED PLAY.** ✅ **Calibration total n = 38 → 40; exclusions 5 → 3; every figure reconciles as 43 settled − 40 in calibration = 3.**

⚠️ **SCOPE OF THE CHANGE, PRECISELY:** ✅ **CALIBRATION only.** ⛔ **The ledger's HIT RATE table is UNCHANGED and stays carded-only, and ledger rule 6 still keeps Sam's SLIPS out of both.** **Every newly included play is tagged `[conversational]` on its row so the two populations stay separable.**

## T6. The market-fade signal

`[opened Aug 20 — 1-for-1]`

**When a book moves BOTH of a pitcher's markets against his recent form, treat it as a FADE, not value.** Alcantara, 8/19: books moved him to 4.5 K and 18.5 outs against averages of 5.75 and 20.6. He was carded #4 anyway and threw **1 K in 6 innings**.

**LOG EVERY INSTANCE. DO NOT ACT ON IT.** Revisit at **n ≥ 10 instances.** ⚠️ **Still at 1. The 7:30am run cannot add to it — it needs odds, and a scheduled run may not pull them.**

---

# ⚠️ TIER 3 — untested, and known to be untested

| # | What | Status |
|---|---|---|
| T7 | ~~**Parks · weather · hits allowed · team record**~~ 🔴 **SUPERSEDED — HISTORICAL ONLY.** | ⚠️ ~~"all four were tested on the 40%-complete log and have NEVER been re-run on the full sample"~~ 🔴 **CORRECTED 8/21 evening — HITS ALLOWED *HAS* BEEN RE-RUN ON THE FULL SAMPLE.** `claude/backtest-hits-allowed.md` **RESULT 6, n=2,819**: his own prior **H/BF persists at +0.2422, t=5.34** (real, and still unbettable at R²=0.010), and **the opponent side is measured dead at t=0.61.** ✅ **Hits allowed is NOT outstanding and must not be listed as such.** ➡️ **The three genuinely outstanding nulls are PARKS · WEATHER · TEAM RECORD.** 🔴 **AND THE AMBIGUITY IS RESOLVED HERE, UNAMBIGUOUSLY: T13 IS THE LIVE ENTRY. T7 IS DEAD.** ⛔ **Do not run anything off T7's wording, and do not cite T7 as an open test.** ⚠️ **Four sibling docs still point at "T7" by number.** ⛔ **CITE THE DOC AND THE LIVE ENTRY, NEVER A BARE T-NUMBER** — this register is the only current index, and a number quoted out of another doc has already been stale here more than once. |
| T8 | **Times through the order** | `claude/times-through-order.md` rests on **~5% of the season.** Needs a full-season collection |
| T9 | **Pitcher-quality-adjusted opponent** | Real mechanism, **t=0.0.** Most likely null to revive on the full sample |
| T10 | **Opponent P/PA → PITCH COUNT** | ✅ **REAL: +9.16, t=3.35, R²=0.226.** **No pitch-count prop exists in the Odds API market list. The model is built and waiting** — check the market list monthly |

## T11. Is the model under-confident in the 20–60% range?

`[opened Aug 21 2026 — first shadow-ladder pass]`

**The carded record only ever samples 71–86%, because on a flat price the lowest rung that clears is always the best bet.** Grading every rung instead of the carded one costs nothing and covers the whole range.

### 🔴 THE FIRST PASS WAS SUPERSEDED ON 8/21. HERE IS WHY, AND IT IS A PROCESS FINDING.

~~First pass, 8/20's six evening arms — 40 gradeable probabilities, buckets: 0–20% n=6 · 20–40% n=10 · 40–60% n=6 · 60–70% n=4 · 70–80% n=4 · 80–90% n=4 · 90–100% n=6.~~

⛔ **STRUCK — not because it was wrong, but because it recorded BUCKET COUNTS AND NO LIST OF WHICH SIX ARMS.** An accumulator that cannot be deduplicated cannot be accumulated into: the next pass over the same slate would silently double-count starts already in it, and **rungs within a start are perfectly correlated, so a double-counted start does real damage.**

✅ **REPLACED by a fully itemised pass over ALL 12 of 8/20's graded arms — 83 rungs across 12 NAMED starts.** Table, per-pitcher rungs, and both the pure-model and blend bucket breakdowns live in **`claude/calibration-accumulators.md`**.

➡️ 🔴 **STANDING REQUIREMENT, added to the specification below: every shadow pass names its starts.**

**Current accumulator state — pure model, n = 12 STARTS:**

| Model bucket | rungs | **starts** | Predicted | Actual |
|---|---|---|---|---|
| 0–20% | 15 | 12 | 13.6% | 13.3% |
| **20–40%** | 19 | 12 | **29.6%** | **47.4%** |
| 40–60% | 13 | 12 | 50.9% | 53.8% |
| **60–70%** | 7 | 7 | **64.8%** | **85.7%** |
| 70–80% | 9 | 9 | 76.8% | 77.8% |
| 80–90% | 8 | 8 | 86.3% | 87.5% |
| 90–100% | 12 | 12 | 93.8% | 100.0% |

⚠️ 🔴 **THIS IS TWELVE STARTS, NOT EIGHTY-THREE OBSERVATIONS.** ⛔ **Do not read the 20–60% rows as a finding.** **8/20 was an 8/10 slate — every bucket is lifted by the same good day.**

⚠️ **It still points the OPPOSITE way to the carded 60–70% bucket** (41.7% actual vs 64.2% predicted, i.e. over-confident). **Both cannot be right.** 🔴 **The reconciliation offered when this test was opened — "carded is blended, shadow is pure model" — IS NOT SUPPORTED by the new pass: the blend table shows the same under-confidence** (40–60% bucket: 50.0% predicted, 76.9% actual). **The contradiction is unresolved and must stay unresolved until n is real.**

| | |
|---|---|
| **Specification** | Accumulate shadow ladders on every carded slate. At **≥ 40 distinct STARTS**, bin pure-model probabilities in deciles and compare to realised frequency |
| **Pass for "under-confident below 60%"** | Actual exceeds predicted by **≥ 8 points** in the 20–60% range across ≥ 40 starts |
| **Also report** | The same table computed on the **blend** rather than the pure model, so the two can be told apart |
| ⛔ **Forbidden** | Quoting rung-count as n. **Count starts.** |
| 🆕 ⛔ **Forbidden** | **Merging a pass that does not name its starts.** Discard it instead. *(Added 8/21 — the pass criterion above is UNCHANGED.)* |

⚠️ 🔴 **UPDATED 2026-08-23 — n = 25 STARTS, AND THE HYPOTHESIS HAS TURNED OVER.** **The merged pure-model accumulator in `claude/calibration-accumulators.md` now stands at 185 rungs across 25 distinct named starts (8/20 + 8/21 + 8/22).** 🔴 **The 20–40% bucket that read 29.6% predicted against 47.4% actual on 8/20 — the entire basis of this entry — read 29.5 / 30.0 at 18 starts and now reads 29.5 / 25.6 at 25.** **60–70% reads 64.3 / 60.0 and 70–80% reads 76.0 / 70.0: both now slightly OVER-confident, which is the direction the carded calibration table has said all along.** ⛔ **T11 IS NOT RE-DECIDED HERE AND ITS PASS CRITERION IS UNTOUCHED — the bar is still "actual exceeds predicted by ≥ 8 points in the 20–60% range across ≥ 40 starts", and on current evidence it is heading for a FAIL rather than a pass.** ✅ **The snapshot table above is the n=12 state and is left exactly as written.**

⚠️ **The 8/22 pass is 54 rungs across 7 named starts, with `E[K]` inverted from each play's logged `model` probability and the inversion validated SIX ways against `E[K]` figures the ledger prints independently, plus an internal two-rung cross-check on Jared Jones (5.308 vs 5.303).**

**Progress: 25 / 40 starts.**

---

# 🔴 NOT A TEST — the structural blocker

**Every data path in this project runs through the Chrome extension.**

`[measured] Aug 20–21` — with the laptop closed, all four routes to a box score shut at once: statsapi `WebFetch`-proxy **403** (transient, recovered), Chrome **disconnected**, ESPN **robots-blocked**, B-Ref **had not posted the slate**. **A scheduled task has no browser. Neither will the website.**

🔴 **This is why LINE VALUE still reads n=0, and it is why the 7:30am task cannot rebuild the databases.** **It is the largest structural risk on the board and it is an engineering problem, not a modelling one.**

⚠️ **Partial workaround:** the flat `gameLog` endpoint survives a summarising fetch where the **boxscore does not.**
🔴 🆕 **QUALIFIED 8/21 — AND THE QUALIFICATION MATTERS.** The flat game log survives *block merging*. **It does NOT survive scalar corruption.** A pull on 8/21 returned **`1.3` innings pitched — a value that cannot exist** — and it was caught only because the full-season sum came up short by exactly the 2 outs it implied. ➡️ **The headless path is usable ONLY with a control. "It is a safe shape" is not true, and was one row away from being written down as a finding.** Ledger rule 40.

## T12. The tails-only opponent rule has lost its support. Re-derive it.

`[opened Aug 21 2026 — found by the doc sweep]`

🔴 **`claude/mlb-opponent-database.md` instructs: "apply the opponent adjustment only at the tails" — quintiles 2, 3 and 4 are identical to two decimal places.** That instruction is live and it is on every card.

⚠️ **Its only support was Finding 6 in `claude/pitcher-reliability.md`, whose quintile cut-points were computed on the RETIRED StatMuse scale (league mean 5.01) over the 40%-complete log.** Those cut-points were struck on 8/21; applied to the current statsapi table they would flag almost nobody as tough and almost the whole bottom half as easy.

➡️ **The rule may well be right. It currently has no derivation behind it.** ⛔ **No replacement cut-points were invented; the gap is flagged in-doc instead** ✅ *(re-verified in place 8/21 — the flag is present in the opponent doc)*.

| | |
|---|---|
| **Specification** | Split the current opponent metric into quintiles over the full start table. Compare **mean actual K allowed** across quintiles 2, 3 and 4. |
| **Pass — the tails-only rule stands** | Quintiles 2–4 differ by **< 0.15 K** end to end |
| **Fail** | They separate. **Then the adjustment is linear across the range and the tails-only instruction must be struck from every doc that carries it.** |

## T13. Are the parks / weather / team-record nulls real, or artifacts of the 40% log?

`[carried forward — flagged independently by two sweep passes]`

⚠️ **Parks, domes, weather and team record are quoted as settled nulls throughout the project, and all four were measured on the 40%-complete log.** `claude/backtest-weather-homeaway.md` itself hedges that they are "under-powered, not settled."

🔴 **Attenuation bias is exactly the mechanism that would have produced false nulls there** — the same mechanism that hid the pitch-count term and shrank every own-form coefficient. **A null measured on a broken sample is not a null.**

### 🔴 THE ENTRY IS SPLIT. ONE HALF IS RUNNABLE; THE OTHER HALF IS BLOCKED ON A DATA SOURCE THAT DOES NOT EXIST.

🔴 **CORRECTED 8/21 evening.** ~~"Re-run each of the four against the full start table, one specification each, **same form as originally tested**."~~ ⛔ **STRUCK AS WRITTEN, AND THIS MATTERS.** **The "form as originally tested" for weather is a ROOF/DOME PROXY, static per venue.** `claude/backtest-weather-homeaway.md` states plainly that **actual temperature and wind were NEVER TESTED and there is no historical weather source anywhere in the stack.** ➡️ **Run as written, T13 would re-measure the roof proxy, find it null again, and be written up as "weather confirmed null on the full season" — a CONFIRMATION OF SOMETHING IT CANNOT TEST.** **A test that can only return the answer it already has is not a test.**

## T13a. Parks · domes · team record — ✅ RUNNABLE

| | |
|---|---|
| **Specification** | Re-run **parks**, the **roof/dome proxy** and **team record** against the full start table — one specification each, same form as originally tested. **Nothing else changes.** |
| **Pass — the null holds** | \|t\| < 2.0 |
| **If one comes alive** | 🔴 **Revision-log entry in bold. A resurrected variable is a bigger finding than a new one**, because it means the banned-arguments list has been wrong on the card for weeks |
| ⚠️ **Report the roof result as what it is** | **"the roof/dome PROXY is null on the full season"** — ⛔ **never as "weather is null."** **Retractable roofs open and close; the proxy is noisy even where it is measurable.** |

## T13b. Weather — ⛔ **BLOCKED. NOT RUNNABLE. DO NOT MARK IT CONFIRMED.**

| | |
|---|---|
| ⛔ ~~**Blocked by**~~ 🔴 **BLOCKER PARTLY DISCHARGED 2026-09-14 — THE SOURCE EXISTS NOW** | ~~🔴 **NO HISTORICAL WEATHER SOURCE EXISTS IN THIS PROJECT'S STACK.**~~ 🔴 **STRUCK BY THE MONDAY SWEEP — TRUE WHEN WRITTEN, FALSE SINCE 2026-08-25, AND THIS ENTRY CONTRADICTED T32 IN THIS SAME REGISTER FOR THREE WEEKS.** `[verified 2026-09-14 from a fresh clone of `github.com/smh0602/gizmos-picks`]` **`collect.py` has a `weather` mode — venue coordinates from statsapi, history from the Open-Meteo free archive — and `data/latest/weather.json.gz` is a live artifact. T32 records the coverage measured at the time: temperature and wind at game hour on 1,971 of 1,973 regular-season games, plus venue elevation.** ✅ **WHAT IS STILL TRUE, AND IT IS THE HALF THAT MATTERS HERE: temperature and wind have NEVER been tested against a STARTER'S STRIKEOUTS OR OUTS — the markets THIS entry is about.** ⛔ **The T31/T32/T33 weather work is on GAME TOTALS, a different target with a different sample; it does not discharge T13b and must never be cited as if it did.** ➡️ **So the standing wording below is UNCHANGED and still governs: weather is UNTESTED on this project's two modelled markets.** |
| **What would unblock it** | ~~A per-game historical temperature and wind source joinable to the start table by (date, venue).~~ ✅ **THAT SOURCE NOW EXISTS (above). WHAT REMAINS IS THE JOIN AND THE SPECIFICATION.** **Join the stored weather series to the start table by (date, venue) — the venue field is on the schedule response — and REGISTER THE SPECIFICATION AND THE PASS BAR IN THIS ENTRY BEFORE RUNNING ANYTHING.** ⛔ **THE STATUS OF THIS ENTRY IS NOT CHANGED BY THIS SWEEP: it stays OPEN AND UNSPECIFIED. A sweep corrects a factual blocker claim; it does not write a specification, run a test, or decide an entry.** |
| ⛔ **Forbidden** | **Substituting the roof/dome proxy and reporting the result as a weather finding.** **That is what the original specification would have done.** |
| ➡️ **Standing wording until then** | **"Weather is UNTESTED — carried forward as an operational default, not a measured null."** ⛔ **Not "weather is null," which the docs have said for weeks and cannot support.** |

## T14 — ✅ CLOSED Aug 21 2026, same day it was opened. **RESULT: permanent feed limitation. Ask Sam.**

**Question:** are Hard Rock's alternate UNDER prices reachable through the API?

**Answer: no, and stop looking.** Two credits spent. A clean single-book, two-market pull returned Hard Rock's full alternate ladder with **every outcome `Over`, zero `Under`** — while the same rungs are two-way in the app.

✅ **What the test bought, beyond the answer:**
1. **The API's over prices match the app EXACTLY.** **The feed is not sloppy; it is incomplete in exactly one way.**
2. 🔴 **The mirror shortcut was tested and FAILS.** `Under(R) = Over(2×pivot − R)` is exact at the pivot and one rung out, then decays **25 points at two rungs and 50 at three — always against the bettor.** ⛔ **Never quote a mirrored price.**
3. ✅ **First real de-vig of a Hard Rock ladder:** 7.0% at the pivot widening to 8.5% at the tails.

➡️ **STANDING PROCEDURE: name the rung, say the feed does not carry its price, ask Sam to read it off the app.** ⛔ **Do not re-open this test.**

## T15. 🆕 Can the blend weight be fitted at all at realistic sample sizes?

`[opened Aug 21 2026 — 7:30am run, pre-registered before the September re-fit]`

**Rule 15 exists to replace the hand-set 50/50 with a fitted number. The 8/21 run tried, and found the parameter is not identifiable at current n.**

`[measured 8/21]` Brier score over the blend weight `w`, on the 12 graded plays of 8/20:

| w (model) | 0.0 | 0.2 | 0.4 | **0.5** | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|---|
| Brier | .1852 | .1847 | .1843 | **.1842** | .1841 | .1841 | .1842 |

🔴 **The entire range from pure-raw to pure-model spans 0.0011 of Brier.** The argmin lands at 0.7 and is noise.

⚠️ **Two prior errors are the reason this is being pre-registered rather than acted on:** the "which was closer" tally the rule originally specified is **win-rate-biased** (on an 8/10 day it just rewards the higher number), and this project has already shipped one headline coefficient off a single specification.

| | |
|---|---|
| **Specification** | Accumulate per-play Brier for the model, the raw rate, and the blend. Fit `w` by minimising Brier over all carded plays. |
| **Pass — adopt a fitted `w`** | The Brier difference between the fitted `w` and 0.5 exceeds **0.005**, at **n ≥ 100 carded plays** |
| **Fail** | Anything less. **Keep the 50/50 and record that the weight is not identifiable.** |
| ⛔ **Forbidden** | Adopting an argmin without the 0.005 margin. **A flat surface has an argmin too.** |

⚠️ 🔴 **UPDATED 2026-08-23 — n = 31 CARDED PLAYS, AND ONE LEG OF THE PASS CRITERION HAS CLEARED FOR THE FIRST TIME.** **Brier over `w` on the 31 carded plays of 8/20 + 8/21 + 8/22: argmin at 🔴 `w = 1.00` (PURE MODEL), Brier .2245, against .2338 at the shipped 0.5 — a MARGIN of 0.0094 against a bar of 0.005.** ✅ **The MARGIN leg clears. ⛔ The `n` leg does not: 31 against 100.** ⛔ **THE 50/50 IS NOT TOUCHED, AND THIS ENTRY IS NOT RE-SPECIFIED.**

🔴 **TWO REASONS THE CLEARED MARGIN MUST NOT BE READ AS A RESULT, BOTH RECORDED BEFORE ANYONE IS TEMPTED:** **(1) the argmin has moved 0.7 → 0.74 → 1.00 across three slates and has now landed ON THE BOUNDARY of the parameter space, which means the optimiser is pushing as hard as it can in one direction and has nowhere further to go; (2) the mechanism is a single bad slate — on 8/22 the RAW rate was the more optimistic of the two estimates on 10 of the 13 plays and the card went 6/13, so pure model wins this Brier for being the LOWER number on a losing night, not for being better calibrated.** ➡️ **This is exactly the failure mode the `n ≥ 100` leg exists to absorb, and it is why the criterion has two legs rather than one.**

⚠️ **PROVENANCE, carried forward: 10 of the 31 plays (the 8/20 third) use RECONSTRUCTED model and raw values, including the two flagged residuals. 8/21 and 8/22 are LOGGED.**

**Progress: 31 carded plays accumulated / 100.**

⚠️ 🔴 **THE PARAGRAPH BELOW IS THE 8/21 STATE AND IS KEPT AS HISTORY — the numerator/denominator mismatch it describes was RESOLVED on 2026-08-22 when the accumulator was restated on carded plays only, exactly as this entry pre-registered.** ⛔ **Do not act on its `12 accumulated` figure.**

⚠️ 🔴 **THE NUMERATOR AND THE DENOMINATOR COUNT DIFFERENT POPULATIONS, AND UNTIL THIS IS RESOLVED BOTH ARE STATED PLAINLY RATHER THAN RECONCILED BY ARITHMETIC (ledger rule 45).**

- **The DENOMINATOR — 100 — is CARDED PLAYS**, which is what the specification says. **The ledger's carded record currently stands at 30 graded carded plays** (HIT RATE, TABLE A only).
- **The NUMERATOR — 12 — is the 12 GRADED PLAYS OF 8/20, and TWO OF THEM ARE CONVERSATIONAL** (G. Williams o5.5 K, G. Rodriguez u15.5 outs). **Only 10 of those 12 are carded.** **So the numerator is not drawn from the population the denominator names.**

➡️ 🔴 **THE RESOLUTION IS PRE-REGISTERED HERE AND IS NOT DECIDED BY WHICH WAY IT MOVES THE FIT.** **The Brier accumulator counts CARDED PLAYS, matching the specification.** ➡️ **At the next grading run, RE-STATE the accumulator on the 10 carded plays of 8/20 and report the count as `10 / 100`, saying that two conversational plays were removed.** ⛔ **Do not instead widen the denominator to "all graded plays" — that is T5's question, T5 must be decided on principle, and answering it here as a side effect of a progress counter is exactly the error T5 exists to prevent.** ⚠️ **Until that restatement happens this counter reads `12 accumulated (10 carded + 2 conversational) / 100 carded`.**

⚠️ 🆕 🔴 **T5 WAS DECIDED 2026-08-22 — AND THIS ENTRY'S SPECIFICATION IS UNCHANGED BY IT.** **T5 admitted conversational picks to the CALIBRATION table. T15's specification says CARDED PLAYS and it still says carded plays.** ⛔ **Do not widen this denominator now on the strength of T5.** 🔴 **T15 pre-registered its own resolution before any of this — restate the accumulator on the 10 CARDED plays of 8/20 — and quietly re-specifying it after a neighbouring entry closed would be exactly the drift this register exists to stop.** ➡️ **If the Brier accumulator should follow calibration's new population, that is a NEW pre-registration, written down BEFORE the numbers are recomputed. It is not a side effect.**

## T16. 🆕 ✅ **PASSED** — does a BAD-tier arm against a strong offense go under 15.5 outs more often?

`[opened AND run Aug 21 2026 — Sam's hypothesis, spec written before the query]`

**Sam raised it in his own words:** *"finding these bad pitchers going against really good teams can give us some really good odds when betting the under on outs."*

| | |
|---|---|
| **Specification** | 2026 starts. **BAD tier = season K/9 < 9.0 AND ERA > 3.50** (the project's existing tier definition, not a new one), pitcher with **≥8 starts**. **Strong offense = opponent in the top 10 by runs per game.** Metric: **P(outs < 15.5)**. |
| **Pass** | BAD-vs-top-10 exceeds BAD-vs-rest by **≥5 points** with **\|z\| ≥ 2.0** |
| ⛔ **Forbidden** | Trying other cut-points (top-8, top-12), other thresholds (14.5, 16.5) or other tier definitions after seeing the first result |

### `[measured 2026-08-21]` RESULT — **PASSES**

| Cell | Rate | n |
|---|---|---|
| **BAD tier vs a top-10 offense** | **54.1%** | 304/562 |
| **BAD tier vs everyone else** | **47.5%** | 539/1134 |
| **Difference** | **+6.6 points** | **z = 2.54** · total n = 1,696 |

✅ **One specification, one run, no cut-point shopping.** The tier definition and the 15.5 threshold were both taken from existing project documents rather than chosen for this test, which is most of what keeps it honest.

🔴 **WHAT THIS DOES *NOT* SAY, AND THE DISTINCTION IS THE WHOLE POINT.** Sam's claim has two halves — **(a)** the under hits more often, and **(b)** the price is good. **Only (a) is measured.** **(b) is a claim about what the BOOKS do, and LINE VALUE is still n=0** — this project has never captured a closing line. ⛔ **Do not quote T16 as evidence of an edge against a price.**

⚠️ **AND THE FIRST LIVE APPLICATION ARGUES THE BOOK ALREADY KNOWS.** Bubba Chandler is the exact cell — **8.03 K/9, 4.23 ERA, facing LAD (5th, 5.00 rpg)** — and Hard Rock priced **u15.5 outs at −160, a 61.5% break-even against a 54.1% base rate.** **model 48.3% · his own log 60.9% (14/23) · matched class 54.8% (40/73), 45.9% on 4+IP · blend 54.6% → edge −6.9.** **No bet.**

✅ **WHERE IT IS STILL USEFUL, AND THIS IS SAM'S OTHER OBSERVATION:** *"it is still worth noting because it has a lot of potential to be a great pair for some alt lines that can be priced at −1000."* 🔴 **The 1.8x–2.1x band REQUIRES a short favourite, and almost every edge-bearing leg prices near even.** **A mid-priced under-outs leg at 1.60–1.75 is the scarce ingredient that lets a −700-to−1000 anchor reach the band at all.** ➡️ **T16 identifies WHERE to look for that leg. It does not certify the price when one is found.**

➡️ 🆕 **OPENS T17 (below), which is the half T16 cannot answer.**

## T17. 🆕 Do the books UNDER-price the T16 cell?

`[opened Aug 21 2026 — the untestable half of T16, written down now so it cannot be answered by argument later]`

| | |
|---|---|
| **Specification** | On every card, when a starter falls in the T16 cell, record the book's outs line, its price, and the realised outs. Compare the **implied probability of the under** to the **realised rate** in that cell. |
| **Pass** | Realised exceeds mean implied by **≥4 points** over **≥40 captured lines** |
| ⛔ **Blocked by** | **LINE VALUE, n=0.** This needs captured prices, and price capture is interactive-only (ledger rule 38). **It will accumulate slowly or not at all — say so rather than substituting the T16 base rate for it.** |

**Progress: 1 / 40 captured lines** *(Chandler u15.5 outs at −160, 8/21 — outcome pending)*.

⚠️ 🔴 **IS A "CAPTURED LINE" THE SAME UNIT AS A "PAIRED OBSERVATION"? ANSWERED EXPLICITLY, BECAUSE THE TWO COUNTERS DISAGREE ON THE PAGE.** **The ledger's LINE VALUE section reads `n = 0 paired observations` while this entry reads `1 / 40 captured lines`. Both are correct, and they are NOT the same unit.**

- **A CAPTURED LINE** — this entry's unit — is **one T16-cell starter, with the book's outs line, its price and the realised outs, recorded on the card.** **One start, one line, one price.** **Chandler 8/21 is that, and it is 1.**
- **A PAIRED OBSERVATION** — the ledger's unit — is **an OPENING price and a CLOSING price for the same rung**, which is what a CLV measurement requires. ⛔ **This project has never captured a closing line, so that counter is correctly `n=0` and the two are not in conflict.**

➡️ 🔴 **T17 NEEDS THE CAPTURED LINE, NOT THE PAIR.** **It compares implied probability at capture to the realised rate; it does not need a close.** ⚠️ **But it inherits the same blocker for the same reason** — price capture is interactive-only (ledger rule 38), so it accumulates one card at a time or not at all. ⛔ **Never report the two counters as one number, and never substitute the T16 base rate for either.**

## T18. 🆕 ⛔ **CLOSED-FAILED** — does a rematch inside 30 days cost a pitcher strikeouts?

`[opened AND closed Aug 21 2026 — prompted by Sam: "your not worried about dobbins facing the phillies 2 starts ago"]`

🔴 **REGISTERED HERE BECAUSE `claude/pick-ledger.md` RULE 51 CLAIMED ITS SPECIFICATION WAS "written into `claude/owed-tests.md`" AND IT WAS NOT.** **A doc asserting a fix is not a fix (check 25 / ledger rule 37).** **The entry exists so that claim resolves, and so the failure below cannot be quietly re-specified later.**

**Population.** 2026 starts in which the same pitcher faced the same opponent **within the previous 30 days.** **n = 296 pairs, mean gap 15.2 days.**

| | |
|---|---|
| **Specification — PRE-REGISTERED** | Mean strikeout drop from the first meeting to the rematch |
| **Pass** | **drop ≥ 0.5 K with \|t\| ≥ 2.0** |
| 🔴 **RESULT** | **5.04 → 4.74 — a drop of 0.30, t = −1.78** |
| ⛔ **VERDICT** | 🔴 **FAILED. MARKED CLOSED-FAILED.** **It did not clear, it is recorded as failed, and it is NOT rewritten.** |

### 🔴 A SECOND CUT WAS THEN RUN ON THE SAME DATA. IT IS SIGNIFICANT. IT IS EXPLORATORY, NOT REGISTERED.

`[measured 2026-08-21 — run AFTER the primary specification had already failed]`

- **4+ K fell 221/296 → 182/296.** Paired **McNemar χ² = 12.78** — **76 hit-then-miss** against **37 miss-then-hit.**
- **Conditional on a strong (≥5 K) first meeting, the next start reaches 4+ K:**

| Next start reaches 4+ K | Rate |
|---|---|
| vs **anyone** | **1363/1826 = 74.6%** |
| vs the **same team** again, ≤30 days | **116/173 = 67.1%** |

- **At a 3+ K bar the same split is 87.5% → 84.4%** — about **3 points**, against about **8 points** at the 4+ bar. ➡️ **The effect is THRESHOLD-DEPENDENT: the lower the bar, the less a second look costs. A rematch is a reason to DROP A RUNG, not to drop the pitcher.**

⚠️ 🔴 **SAID PLAINLY, BECAUSE IT IS THE POINT OF THIS ENTRY: LOOKING A SECOND WAY AFTER THE PRIMARY SPECIFICATION FAILED *IS* SPECIFICATION SHOPPING.** **It is this project's own documented worst error, twice over** — v3.4's headline coefficient was shipped on one specification and died at **t=−0.02** on a filter sweep, and the GOOD-tier P/PA result read **t=−1.68 after ~10 specifications.** **This is the same shape, caught and labelled while it was happening rather than a week later.**

⛔ **THE EXPLORATORY RESULT MAY NEVER BE SILENTLY PROMOTED TO THE REGISTERED ONE.** ➡️ **Every citation of the threshold numbers — on a card, in a doc, in a task prompt — states that the PRE-REGISTERED mean-K specification FAILED at t=−1.78 and that the threshold version is EXPLORATORY.** **Quote it with the failure attached, or do not quote it.** ⚠️ **`claude/mlb-alt-line-protocol.md` and `claude/pick-ledger.md` rule 51 both carry it correctly labelled — keep it that way.**

### 🆕 THE REPLACEMENT SPECIFICATION — pre-registered NOW, for the September re-fit

**One specification, the threshold form, decided before the data is touched again.**

| | |
|---|---|
| **Specification** | Compare the **4+ K rate in rematches inside 30 days** against **the SAME pitchers' 4+ K rate in their non-rematch starts**, paired within pitcher. **Same season, same 30-day window, no other cut.** |
| **Pass** | The rematch rate is **at least 5 POINTS BELOW** the same-pitcher non-rematch rate, with a **paired \|z\| ≥ 2.5**, on **≥ 400 pairs** |
| **Fail** | Anything less — **including a significant result on fewer than 400 pairs.** **Record as FAILED and close.** |
| ⛔ **Forbidden** | A second threshold (3+, 5+), a second window (14 days, 45 days), a conditional on the first meeting's result, or any functional form tried **after** seeing the outcome. **One specification. This one.** |

## T19. 🆕 Does PrizePicks' DEMON/GOBLIN tag beat this project when the two disagree?

`[opened Aug 21 2026 — registered here because it was living ONLY inside a card write-up in `claude/pick-ledger.md`, which is precisely the failure this register exists to prevent]`

🔴 **IT ALREADY HAD A SPECIFICATION, A PASS CRITERION AND AN INSTANCE 1 — AND NO ENTRY.** A test that lives in a card write-up is a test nobody will find at the re-fit, and one that can be quietly re-specified because there is nothing to compare it against.

**The tag is a market signal.** **DEMON marks the HARDER side of a rung** — PrizePicks saying its own baseline for that player sits on the other side of the number. **GOBLIN marks the easier side.**

| | |
|---|---|
| **Specification** | Track **every** play where PrizePicks' **DEMON/GOBLIN tag disagrees with this project's read by more than 15 points** |
| **Pass** | **The books are right in ≥ 7 of the first 10** |
| ⛔ **Forbidden** | **Acting on it as a rule before then.** **Log instances. Do not fade the tag, do not follow it, and do not let it move a blend.** |
| ⚠️ **Note** | The tag is **not a price** (ledger rule 46) — ⛔ **no break-even, edge or EV is ever derived from it.** It is used here **only** as a direction. |

**Instance 1 — Hunter Dobbins OVER 3.5 K, 2026-08-21.** ⏳ **UNGRADED.**

| Source | P(Dobbins reaches 4+ K) |
|---|---|
| **PrizePicks — tagged DEMON** | **below 50% by their baseline** |
| **Hard Rock — priced −135 at the 4:05pm ET pull, −130 at the 4:41pm ET re-pull** | **57.4% → 56.5% implied.** ⏱️ **Both are real — line movement between two stamped pulls, not a discrepancy (ledger rule 49).** |
| **This project, after every correction** | **~76%** |

🔴 **TWO BOOKS, INDEPENDENTLY, PUT IT ~19 POINTS BELOW THE MODEL.** ⚠️ **And the edge only got that big off a thin sample — 7/7 on n=7 career starts dragged the blend far above both the model (72.3%) and the matched class.**

**Progress: 1 instance logged / 10.**

## T20. 🆕 Count form vs rate form for the STRIKEOUT model — a full-season re-test

`[opened Aug 21 2026 — `claude/backtest-hits-allowed.md` RESULT 5 records in its own text that no entry for this existed here. It does now.]`

🔴 **THE STRIKEOUT MODEL IS FITTED IN COUNT FORM BECAUSE OF ONE TABLE, AND THAT TABLE IS 699 ROWS OF THE 40%-COMPLETE LOG.** RESULT 5 reads **count R² 0.1106 / RMSE 2.2980** against **rate R² 0.0942 / RMSE 2.3191.** ⚠️ **This is not a historical note. It is the SHAPE OF THE LIVE MODEL, on every card, and it sat in no register entry at all.**

- 🔴 **Attenuation bias is exactly the mechanism that would decide a count-versus-rate contest wrongly.** Both forms were measured on the same broken history, where **every own-form coefficient was shrunk toward zero** — that doc's own control check reads **pitcher +0.519** where the full season reads **+0.673.** **The margin being relied on is 0.1106 against 0.0942. Nothing establishes that it survives the refit, and nothing establishes that it does not.**
- ⚠️ **And the same question FLIPPED for hits the moment a denominator arrived** — RESULT 6's rate form carries **10× the t-statistic of the count form.** **"Test both forms before declaring either null" is that doc's own lesson, and the strikeout side has never been re-run.**
- ⛔ **NOT RE-DECIDED HERE. The model form stays exactly as it is until this runs.** **Re-deciding it now, having looked at the table, is the specification-shopping error this register exists to prevent.**

| | |
|---|---|
| **Specification** | Re-fit the v4.0 strikeout model **twice on the COMPLETE start table** — once in **COUNT** form (both predictors per start, exactly as shipped) and once in **RATE** form (both predictors as K/9). **Same rows, same filters, same point-in-time construction. Nothing else changes.** Report **R² and RMSE** for each, the same two statistics RESULT 5 used. |
| **Pass — switch the model to RATE form** | Rate beats count on **BOTH**: **ΔR² ≥ +0.005** AND **RMSE lower by ≥ 0.02 K** |
| **Fail** | Anything less. 🔴 **The COUNT form stands — and its justification is then a full-season measurement rather than one inherited from the broken log, which is most of the value of running this at all.** |
| ⛔ **Forbidden** | A third form, a tier split, an interaction, or a subsample, tried **after** seeing the first result. **One comparison. Two forms. Decided here.** |

## T21. 🆕 Small-sample shrinkage of the raw hit rate — the blend takes 7-for-7 at face value

`[opened Aug 22 2026 — measured the same day on 2,984 point-in-time observations from the full 2026 start table: 340 starters, 3,868 starts after the 8/21 slate]` ⚠️ **PROMPTED BY SAM'S OWN READ, NOT BY THE MODEL.** ⛔ **NOT ADOPTED. The model is NOT changed until the September re-fit.**

**THE DEFECT.** The card blends **50% model + 50% raw hit rate with NO adjustment for the raw rate's sample size.** **A 7-for-7 record enters the blend at exactly the same weight as 26-for-26.**

`[measured]` **Actual next-start rate at 4+ K, by the pitcher's PRIOR record at that threshold (prior starts only, ≥3):**

| Prior raw rate | n | Raw claims | ACTUAL | Gap |
|---|---|---|---|---|
| **100%** | 343 | 100.0% | **81.3%** | **−18.7** |
| 85–99% | 484 | 89.2% | 80.4% | −8.8 |
| 70–84% | 891 | 77.8% | 74.2% | −3.6 |
| 50–69% | 868 | 60.6% | 64.5% | **+3.9** |
| <50% | 398 | 30.8% | 48.5% | **+17.7** |

**Base rate 69.8%.** **At the 5+ K threshold the 100% row reads 74.4% actual against 100% claimed — −25.6.**

🔴 **THE SHARPEST RESULT — A PERFECT *SHORT* RECORD CARRIES NO INFORMATION OVER A MERELY GOOD ONE:**

| Prior record at 4+ K | 3–8 prior starts | 9+ prior starts |
|---|---|---|
| **100%** | **78.0%** (184/236) | **88.8%** (95/107) |
| 70–84% | **77.9%** (215/276) | 72.5% (446/615) |

➡️ **78.0% and 77.9% — identical.** **Over a short sample, perfect is worth exactly the same as good. Over a long one it is worth 16 points more.**

**LIVE CONSEQUENCE, STATED:** **Hunter Dobbins was 7-for-7 and carded at a blend of 86.1%; his measured cell says 78.0%, and the model alone (72.3%) was closer than the blend.**

| | |
|---|---|
| **Specification** | Replace the raw rate in the blend with an **empirically shrunk rate** estimated from the (prior rate × prior n) grid above, fitted point-in-time on the full season. **One specification.** |
| **Pass** | The shrunk blend beats the current 50/50 blend on **Brier score by ≥ 0.005** on held-out starts |
| **Fail** | Anything less. **Record it FAILED and keep the 50/50.** |
| ⛔ **Forbidden** | **Tuning the bucket boundaries after seeing the first result.** |

## T22. 🆕 The shuttled-starter penalty — an arm moved in and out of the bullpen is a different bet

`[opened Aug 22 2026 — measured the same day on the same 2,984 point-in-time observations]` ⚠️ **PROMPTED BY SAM'S OWN READ, NOT BY THE MODEL.** ⛔ **NOT ADOPTED. The model is NOT changed until the September re-fit.**

**SAM'S READ:** *"guys like him who have been moved in and out of a bullpen are hard to rely on."* **He said it about Sean Manaea, who has 13 starts and 14 relief appearances in 2026 — a reliever until June 13.**

`[measured, POINT-IN-TIME — the role label is built ONLY from appearances STRICTLY BEFORE each start, so it carries no lookahead]`

| At 4+ K | Record |
|---|---|
| **Pure starters** | **1719/2362 = 72.8%** |
| **Had already relieved** | **363/622 = 58.4%** |
| | **−14.4 points · z = 6.97** |

**At 5+ K: 57.5% vs 40.8% · −16.7 · z = 7.44.**

✅ **IT SURVIVES CONTROLLING FOR STRIKEOUT ABILITY** (season K/9 terciles, point-in-time):

| K/9 tier | Pure | Shuttled | Gap | z |
|---|---|---|---|---|
| Low | 56.2% (n=683) | 45.8% (n=262) | −10.4 | 2.87 |
| Mid | 71.9% (n=800) | 64.9% (n=282) | −7.0 | 2.20 |
| **High** | **86.5% (n=879)** | **76.9% (n=78)** | **−9.5** | **2.31** |

➡️ **Even among power arms a shuttled starter is ~9 points worse.** **It also survives splitting by mean start length.**

⚠️ 🔴 **AN EARLIER CUT USING A SEASON-LONG ROLE LABEL READ −17.7. THAT VERSION WAS LOOKAHEAD — a grouping variable built from season totals — AND IS STRUCK.** **The point-in-time figure of −14.4 is the one to carry.** ✅ **Recorded because catching it is the point.**

**LIVE CONSEQUENCE:** **Manaea is a shuttled, high-K arm — his cell says ~77%, and he was carded at 86.9%.** **Dobbins is shuttled too (3 relief appearances), so he was carrying both this penalty and the small-sample one at once.**

| | |
|---|---|
| **Specification** | Add a **point-in-time binary "has relieved this season"** term to the strikeout model. **One specification, nothing else changes.** |
| **Pass** | **\|t\| ≥ 2.5 AND ΔR² ≥ +0.005** |
| **Fail** | **Record FAILED and close it.** |
| ⛔ **Forbidden** | Trying relief-appearance counts, recency weights or interactions **after** seeing the first result. |

### ⚠️ APPLIES TO BOTH T21 AND T22

**These are the largest un-modelled effects found in this project to date.** 🔴 **Both were surfaced by SAM rather than by the model.** ⛔ **AND BOTH MUST WAIT FOR THE SEPTEMBER RE-FIT — this project has explicit rules against changing the model the moment a result looks good, and a result this large is exactly when that rule matters.**

## T23. 🆕 The matched-class `outs ≥ 12` filter is provably biased on OUTS markets — replace it with one that cannot touch the outcome

`[opened Aug 22 2026 — DERIVED, not measured. Prompted by Sam asking about a SECOND u15.5 outs play, which put two of them side by side and made the pattern visible]` ⛔ **STATUS: PRE-REGISTERED, NOT ADOPTED. STEP 4B is NOT changed until the September re-fit.**

**THE DEFECT.** STEP 4B reports the matched class two ways — **ALL starts**, and starts where the pitcher recorded **`outs ≥ 12` ("4+IP")**. The 4+IP split exists to strip out starts abandoned early for reasons unrelated to the bet. 🔴 **On an OUTS market it does not do that. The filter is a function of the very quantity being graded, so it can only ever delete one side of the ledger.**

**THE PROOF, for an under at threshold `T`:**
- **A WIN is `outs ≤ T`. A LOSS is `outs > T`. The filter keeps `outs ≥ 12`.**
- ➡️ **Whenever `T ≥ 12`, EVERY loss already satisfies `outs > T ≥ 12` and is KEPT with certainty, while the winners with `outs < 12` are ALL REMOVED.**
- ⛔ **The filtered rate is a STRICT LOWER BOUND on the true rate — guaranteed by arithmetic, on every slate, for every pitcher.**
- **MIRROR IMAGE ON AN OVER: for `T ≥ 12` every WIN (`outs > T`) survives and only LOSERS are removed, so the 4+IP figure is biased HIGH.**

⚠️ **SEVERITY SCALES WITH HOW FAR `T` SITS ABOVE 12.** At **`u18.5`** the winning region is 0–18 and only the 0–11 slice is removed — modest, which is why 8/21's Sale row read a healthy **90.5%**. 🔴 At **`u15.5`** the winning region is 0–15 and 0–11 is removed — a large share of it — and **`u15.5` is the most common outs rung on the board.**

🔴 **THIS IS A DERIVATION, NOT A MEASUREMENT, AND THAT MAKES IT STRONGER: it is a property of the FILTER, so it has been corrupting every outs-under class figure this project has ever printed, on every card, since STEP 4B was introduced.**

⛔ **IT DOES NOT APPLY TO STRIKEOUT MARKETS.** A short outing is a plausible LOSS for a K over and a plausible WIN for a K under, so the filter is not provably biased in either direction there. ✅ **4+IP stays informative on strikeouts and STEP 4B is unchanged for them.**

**THE TWO PLAYS IT MISREPRESENTED ON 2026-08-22 — both against the bet** *(cross-reference: the 2026-08-22 entry in `claude/pick-ledger.md`)*:

| Play | Biased 4+IP figure — quoted as the headline | Unbiased ALL figure |
|---|---|---|
| **Jake Irvin u15.5 outs vs MIA** (8/22 TABLE A row 9) | 🔴 **46.9% (23/49)** — delivered as *"under half"* | ✅ **55.2% (32/58)** |
| **Ryan Johnson u15.5 outs vs TEX** *(not carded — asked about in conversation)* | 🔴 **38.5% (20/52)** | ✅ **50.0% (32/64)** |

⚠️ **The Irvin flag SURVIVES either way — 55.2% is still well below his carded 70.9% blend — but 46.9% and 55.2% are different claims and the card led with the one that could not have been anything else.**

| | |
|---|---|
| **Specification** | On the full 2026 start table, compute the outs-market matched class **three ways** and compare each against realised outcomes: **(a)** the current **`outs ≥ 12`** filter, **(b)** **NO filter at all** — ALL starts, **(c)** a filter that removes **ONLY starts ended by injury or ejection**, i.e. one that cannot be caused by the outcome being measured. **Same rows, same peer definition, same thresholds. Nothing else changes.** |
| **Pass — adopt a replacement** | Adopt whichever variant has the **smallest mean absolute calibration gap** against realised outcomes across the accumulated outs plays. **Requires n ≥ 30 outs plays before deciding.** |
| **Decided at** | **The September re-fit.** ⛔ **Written down BEFORE the data is touched again.** |
| ⛔ **Forbidden** | A fourth variant, a different outs cut-point (`≥ 9`, `≥ 15`), or a threshold split tried **after** seeing the first result. **Three variants. One decision.** |
| ⛔ **Scope** | **OUTS markets only.** **STRIKEOUT markets are out of scope and STEP 4B is unchanged for them.** |

✅ **INTERIM — WHAT CHANGED ON 2026-08-22 AND WHAT DID NOT.** **ONLY THE REPORTING ORDER CHANGED:** on an OUTS bet at **`T ≥ 12`** the **ALL-STARTS figure is the headline**, and the 4+IP figure is reported only with the words **"biased low on unders / high on overs by construction"** attached. ⛔ **NO probability was recomputed and NO carded estimate moved — Irvin's carded blend stays 70.9% and enters calibration at 70.9%.**

### ✅ 🆕 **APPLIED IN CODE 2026-08-23 — AND THIS IS NOT AN ADOPTION.** `card.py` COMPUTES THE RAW HIT RATE ON **ALL STARTS, WITH NO 4+IP FILTER.**

🔴 **SAY PRECISELY WHAT THAT DOES AND DOES NOT MEAN, BECAUSE THE DISTINCTION IS THE WHOLE POINT OF THIS REGISTER.**

- ✅ **T23 IS A FINDING ABOUT HOW TO *MEASURE*, NOT A NEW MODEL TERM.** **The filter it removes was never fitted, never carried a coefficient and never entered a probability — it only ever decided which starts got COUNTED in a descriptive rate.** **Removing a provably biased filter from a descriptive count is a correction, not an adoption.**
- ⛔ **NOTHING IN THE MODEL CHANGED. `E[K]`, `mu`, the distributions and the 50/50 blend weight are all exactly as fitted.**
- ✅ **BOTH FIGURES ARE STILL REPORTED WITH `n` — the all-starts rate AND the 4+IP rate — and the ALL-STARTS one is the REFERENCE used for the ≥15-point matched-class flag, never the flattering 4+IP one.**
- 🔴 **CONTRAST, STATED SO IT CANNOT BE BLURRED: T21 AND T22 REMAIN NOT ADOPTED, AND `verify_card.py` HAS A CHECK THAT FAILS THE BUILD IF `blend` IS EVER ANYTHING BUT THE PLAIN 50/50.** **Those two are new model terms. T23 and T24 are not.**
- ⛔ **THE PRE-REGISTERED SPECIFICATION ABOVE IS UNCHANGED AND IS STILL OWED.** **Applying the unbiased rate on the card does NOT decide between variants (a), (b) and (c); that decision is still the September re-fit's, still needs n ≥ 30 outs plays, and this entry is NOT closed.**

⚠️ 🆕 **COUNTER OPENED 2026-08-23 — 5 OUTS PLAYS ACCUMULATED, AND THE COUNTING CONVENTION IS STATED SO A FUTURE RUN DOES NOT RE-BASE IT.** **This entry was opened on 2026-08-22 with the counter at zero, so it accumulates from the 8/22 card forward. That card's FIVE outs plays are the first five and they are named here:** **Skubal u18.5 outs (blend 66.4) ❌ 21 outs · Irvin u15.5 outs (70.9) ❌ 18 outs · Hunter Brown u17.5 outs (62.2) ✅ 17 outs · Martín Pérez o14.5 outs (67.3) ❌ 12 outs · Cease u17.5 outs (47.4) ❌ 20 outs.** 🔴 **1 of 5, against a mean carded estimate of 62.8%.** ⛔ **FIVE PLAYS DECIDE NOTHING and no variant is chosen; the three-way comparison, the n ≥ 30 bar and the September decision date are all untouched.**

**Progress: 5 / 30 outs plays accumulated.**

## T24. 🆕 The matched-class SELECTION AXIS is wrong for OUTS markets — comparables are picked by K/9, which says nothing about start length

`[opened Aug 22 2026 — MEASURED the same day, point-in-time. Prompted by Sam asking what TIER the comparables were, not by the model]` ⛔ **STATUS: PRE-REGISTERED, NOT ADOPTED. STEP 4B's selection axis is NOT changed until the September re-fit.**

**THE PROBLEM.** STEP 4B selects comparables by **`±1.5 K/9`**. 🔴 **For OUTS markets that is the wrong axis — K/9 is near-orthogonal to start length, so the pool mixes durability tiers.** **A `±1.5 K/9` band puts a workhorse ace beside a short-leash arm, because strikeout rate says almost nothing about how long a start lasts.**

**SAM'S WORDS, which are the whole finding:** *"look at pitchers of ryan johnsons caliber against texas… in all of those 64 texas games half of them may have gone over or under, but how many of those pitchers are tiers above ryan johnson, this is an important thing to catch for trying to snipe these types of pitchers for an under"*

**EVIDENCE** `[measured 2026-08-22, point-in-time]` — across **88 starts vs Texas**, the u15.5 outs hit rate split by the starter's **trailing-8 mean outs going in**:

| Starter's trailing-8 mean outs | u15.5 hit rate |
|---|---|
| **under 14** | **5/9 = 55.6%** |
| 14–16 | 12/27 = 44.4% |
| 🔴 **16–18** | 🔴 **12/39 = 30.8%** |
| 🔴 **18+** | 🔴 **4/13 = 30.8%** |

🔴 **52 OF THE 88 CAME FROM PITCHERS AVERAGING 16+ OUTS AND THEY HIT THE UNDER ONLY 31% OF THE TIME — that is what dragged the pooled figure to 50%.**

**EFFECT ON LIVE PLAYS** *(cross-reference: the 2026-08-22 2:00pm ET entry in `claude/pick-ledger.md`)*:

| Play | K/9-matched (4+IP / ALL) | ✅ Durability-matched, point-in-time |
|---|---|---|
| **Irvin u15.5 vs MIA** | 46.9% / **50.0%–55.2%** | ✅ **66.7% (18/27)** |
| **Johnson u15.5 vs TEX** | 38.5% / **50.0%** | **56.5% (13/23)** |
| **Skubal u18.5 vs PIT** | 75.9% / **82.1%** | **77.5% (31/40)** |

| | |
|---|---|
| **Specification — written BEFORE further data is touched** | Compare **three selection axes** for OUTS markets: **(a)** the current **`±1.5 K/9`**, **(b)** **`±1.5` trailing mean outs (point-in-time)**, **(c)** **both bands jointly.** **Same rows, same thresholds, same peer construction. Nothing else changes.** |
| **Pass — adopt a replacement axis** | Adopt whichever **minimises mean absolute calibration gap** on accumulated outs plays. **Requires n ≥ 30 outs plays before deciding.** |
| ⛔ **Explicitly** | **KEEP `±1.5 K/9` for STRIKEOUT markets unless (c) wins there too.** |
| 🔴 **Grouping variable** | **MUST be POINT-IN-TIME.** **A season-long durability label is LOOKAHEAD — the same error already recorded and struck for T22's role label.** |
| ⚠️ **Interacts with T23** | **T23 (the `outs ≥ 12` filter bias) and T24 MUST BE RESOLVED TOGETHER** — both affect the same outs-market figure and **both bias the same direction, against outs unders.** |
| **Decided at** | **The September re-fit.** |
| ⛔ **Forbidden** | A fourth axis, a different band width, or a threshold split tried **after** seeing the first result. **Three axes. One decision.** |

✅ **INTERIM — WHAT CHANGED ON 2026-08-22 AND WHAT DID NOT. REPORTING ORDER ONLY:** on an OUTS market the **durability-matched, point-in-time figure is the headline** and the K/9-matched figure is reported beside it as the legacy number. ⛔ **NO carded estimate moved — Irvin's blend stays 70.9% and enters calibration at 70.9%, Skubal's stays 66.4% (ledger rule 34).**

### ✅ 🆕 **APPLIED IN CODE 2026-08-23 — AND, LIKE T23, THIS IS NOT AN ADOPTION.** `card.py` SELECTS THE MATCHED CLASS ON THE **DURABILITY AXIS FOR OUTS PROPS** (trailing mean outs band, **POINT-IN-TIME**) AND ON THE **K AXIS FOR STRIKEOUT PROPS** (±1.5 season K/9).

- ✅ **T24 IS A FINDING ABOUT WHICH PITCHERS THE COMPARABLE POOL SHOULD CONTAIN — a measurement question, not a model term.** **No coefficient was added, no probability was refit, and the class figure remains a LABEL on the row (ledger rule 53), never a gate and never folded into the blend.**
- 🔴 **THE GROUPING VARIABLE IS POINT-IN-TIME IN THE CODE, exactly as this entry requires — a season-long durability label would be LOOKAHEAD, the error already struck for T22's role label.**
- ✅ **BOTH the all-starts and the 4+IP figures are reported with `n`, and the ALL-STARTS figure is the reference for the ≥15-point flag (T23).**
- ⛔ **THE THREE-AXIS COMPARISON ABOVE — (a) K/9, (b) trailing mean outs, (c) both jointly — IS STILL OWED AND STILL DECIDED AT THE SEPTEMBER RE-FIT, at n ≥ 30 outs plays. THIS ENTRY IS NOT CLOSED.**
- ⚠️ 🔴 **AND ONE THING THE CARD DELIBERATELY DOES NOT DO: THE AUTOMATED `carried` COLUMN APPLIES NO DISCRETIONARY NUDGE TOWARD THE MATCHED CLASS.** **The 8/22 hand-built card nudged some rows by hand; the code does not, because folding a FLAG into a NUMBER — even a third of the way — WOULD be a new model choice, and it has no pre-registered test.**

**Progress: 5 / 30 outs plays accumulated.** ⚠️ **Shares its counter's population with T23 — the five 8/22 outs plays are named in that entry.** ⛔ **Five plays decide nothing; the three-axis comparison and the September decision date are untouched.**

## T25. 🆕 THE MARKET'S IMPLIED TEAM TOTAL AS A MODEL INPUT

`[opened 2026-08-22 — PROPOSED BY SAM, not by the model]` ⛔ **STATUS: PRE-REGISTERED, NOT ADOPTED.**

**Sam's words, 2026-08-22:** *"if a book puts a run total on a team at 2.5 at -150 odds that means the opposing pitcher will probably pitch a good game"*

**WHY IT IS PROMISING.** 🔴 **The model's ONLY current view of an opponent is that lineup's mean strikeouts.** **The opponent→outs channel was already MEASURED NULL (t = −0.34), so the model has NO working opponent term for outs at all.** ➡️ **A book's posted team total embeds the starter, the bullpen, the park, the weather, that day's lineup and the umpire — every input this project does not have — priced by better-informed participants and compressed into ONE number.** ✅ **AND IT COSTS 6 CREDITS FOR AN ENTIRE SLATE** (the bulk endpoint, measured 2026-08-22 — see `claude/mlb-data-stack.md`).

| | |
|---|---|
| **Specification — written BEFORE the data is touched** | Collect the OPPOSING team's implied total (from `totals` + `spreads`, **de-vigged**) for every start going forward. Test whether adding it as a term improves **(a)** the OUTS model and **(b)** the STRIKEOUT model, **over and above the existing terms.** |
| **Pass** | **A coefficient with \|t\| ≥ 2.0 AND an out-of-sample improvement in mean absolute error** |
| **Decided at** | **The September re-fit.** **Single specification, no second look.** |
| ⛔ **Forbidden** | A second functional form, a tier split, or an interaction tried **after** seeing the first result. |

⚠️ 🔴 **THE HAZARD, STATED UP FRONT: THIS IS A MARKET-DERIVED PREDICTOR.** **If it works, the model is partly REPRODUCING the book's opinion rather than beating it, and the edge it produces will be SMALLER than the coefficient makes it look.** ➡️ **REPORT THE MODEL'S PERFORMANCE WITH AND WITHOUT THE TERM SEPARATELY, ALWAYS.** ⛔ **And it can never appear on the product surface as a 🟢 MODEL input without that caveat (ledger rule 55).**

🔴 **RETROSPECTIVE COLLECTION IS NOT POSSIBLE — HISTORICAL ODDS ARE A SEPARATE, MORE EXPENSIVE API PRODUCT. THIS TEST STARTS ACCUMULATING FROM THE DAY COLLECTION BEGINS AND CANNOT BE BACKFILLED.** ➡️ **START COLLECTING IMMEDIATELY, EVEN BEFORE THE MODEL WORK — every day not collected is a day the test cannot reach `n`.**

⚠️ **It requires STORING ODDS OVER TIME, which this project does not do at all.** **That storage is a Phase-1 build item in `claude/gizmos-picks-spec.md`.**

✅ 🆕 **COLLECTABLE FROM 2026-08-22 ONWARD — RECORDED 2026-08-23.** **The Phase-0 collector stores `board.json` every 30 minutes, and it carries the DE-VIGGED IMPLIED TEAM TOTALS this entry needs.** ➡️ **The blocking half of this entry — "it requires storing odds over time, which this project does not do at all" — IS RESOLVED GOING FORWARD.** ⛔ **IT IS STILL UNBACKFILLABLE: every date before 2026-08-22 is permanently out of reach, because historical odds are a separate, more expensive API product.** ⛔ **AND NOTHING ELSE ABOUT T25 CHANGES — the specification, the pass criterion, the September decision date, the single-specification rule and the market-derived-predictor hazard all stand exactly as written, and the term is NOT in any model.**

**Progress: 0 captured team totals.** ⚠️ **The counter starts at zero on the day collection starts, and not before.** ⚠️ 🆕 **The counter stays at 0 until someone actually JOINS the stored `board.json` totals to the start table — storage is not collection for this test's purposes, and saying otherwise would be counting a capability as a sample.**

## T26. 🆕 The outs market's error is asymmetric — do outs UNDERS lose more than outs OVERS?

`[opened 2026-08-23 — prompted by the 8/22 outs half going 1/5, and by Sam's read that it was variance]` `[stated 2026-08-23 — the specification below is written BEFORE the data is touched]` ⛔ **STATUS: PRE-REGISTERED, NOT RUN, NOT ADOPTED. NOTHING IS RE-PRICED ON IT.**

**Why it is opened.** `[measured 2026-08-23]` **The project's carded record splits hard by market: strikeouts 26/38 (68.4%), outs 8/17 (47.1%) — a 21-point gap.** On the 8/22 slate the outs half went 1/5. **Sam's read, in his own words, was that it was variance:** *"skubal finished the 6th inning with 92 pitches and went back out for the 7th... irving did the same, finished the 5th with 90+ pitches, and he went back in for the 6th. this isnt gonna be a norm just bad luck."*

**What was already checked, and it SUPPORTS his read on outs.** `[measured 2026-08-23, one specification, stated before it was run]` Residual `r = actual outs − his own trailing-8 mean outs`, point-in-time, starts only, minimum 5 prior starts, grouped by calendar date; 2,531 starts across 115 dates with 8+ starters each.

| | |
|---|---|
| Season mean residual | **−0.07 outs** — the trailing mean is essentially unbiased |
| Within-day SD of residuals | 3.76 outs |
| SD of daily MEAN residuals, observed | 0.894 |
| Expected under INDEPENDENCE | 0.828 |
| Ratio | **1.079** |
| **Implied intraclass correlation** | **0.008 — effectively no night-level clustering** |
| **8/22's daily mean outs residual** | **+0.046 outs — RANK 57 OF 115. Dead average.** |

➡️ **The league's starters went their normal length on 8/22. The two arms Sam bet did not. That is the shape of variance, not of model bias, and it is recorded because it cuts in Sam's favour.**

✅ **AND A SECOND, FREE RESULT THAT MATTERS FOR PAIRS: at an ICC of 0.008 the outs residuals of two starters on the same night are effectively INDEPENDENT.** ➡️ **STEP 6's joint probability, which multiplies two blends, is NOT overstating on cross-game outs legs. The independence assumption survives its first check.** ⚠️ **One season, one specification. It is a check passed, not a law.**

⚠️ 🔴 **THE PITCH-COUNT SIDE IS DIFFERENT AND THE POST-HOC RISK MUST BE STATED WITH IT.** Same specification on `numberOfPitches`: **8/22 ranked 5TH OF 115 dates at +4.97 pitches per starter, with 21 of 26 starters exceeding their own trailing mean (sign test one-sided p = 0.0012).** ⛔ **BUT THE DATE WAS CHOSEN AFTER THE LOSS. With 115 dates available, roughly 0.3 are expected this extreme by chance, so this is suggestive and NOT a finding.** ⚠️ **Night-level ICC on pitch counts is 0.013 — still tiny.** ➡️ **Recorded as an observation. ⛔ Nothing is re-priced on it.**

**THE TEST ITSELF:**

| | |
|---|---|
| **Specification** | On the full season, point-in-time, split every carded-style outs threshold into UNDERS and OVERS and compute the model's calibration gap (predicted − actual) SEPARATELY for each side. **One specification. The threshold set is every half-integer outs line from 11.5 to 20.5; the model is v4.0's `mu` with the `Normal(mu, cvO × season mean outs)` assumption exactly as shipped.** |
| **Pass** | The under-side gap and the over-side gap differ by **≥ 8 percentage points**, in a consistent direction, on **≥ 300 starts per side** |
| **Fail** | Anything less. **Record it FAILED and change nothing.** The outs record is then a small-sample story and the 50/50 blend stands. |
| ⛔ **Forbidden** | **Re-cutting by threshold band, by pitcher tier, or by home/road after seeing the first result.** **Specification shopping produced both of this project's worst errors.** |

⚠️ **IF IT PASSES, THE FIX IS IN THE DISTRIBUTION, NOT IN A NEW TERM.** The outs probability rests on `T3`'s never-fitted Normality assumption. **An asymmetric error is exactly what a wrong tail shape looks like.** ➡️ **Run T3 before proposing any coefficient change.**

🔴 **DO NOT RUN THIS EARLY. It belongs to the September re-fit.** ⛔ **And do not treat the 8/22 slate as evidence for or against it — that slate is the reason the question was asked, so it cannot also be the answer.**

## T27. 🆕 The first HITTER model — does a fitted `P(1+ hit)` beat the raw rate?

`[opened 2026-08-24 — PRE-REGISTERED BEFORE ANY FITTING. The data reconnaissance below was measured first; not one regression has been run]` 🔴 ⛔ **STATUS: CLOSED-FAILED 2026-08-24 — FITTED, MEASURED, AND IT DID NOT CLEAR ITS PRE-REGISTERED BAR. Held-out Brier improvement +0.00236 against a declared +0.00500. NOTHING SHIPPED.** ⛔ **THE SPECIFICATION, THE PASS BAR AND THE FORBIDDEN LIST BELOW ARE UNCHANGED AND WERE NOT MOVED — the result is recorded BENEATH them.**

**Why it is opened.** `[stated 2026-08-23]` **Sam asked for hitter props on the Gizmo's Picks board.** **They shipped the same night carrying NO confidence rating and NO calibration band**, because **there is no hitter model** and **ledger rule 55 forbids a MARKET number from wearing a Gizmo's %.** **Their number is the player's own season rate at the exact line with a Jeffreys prior — 🔵 DESCRIPTIVE, explicitly not a projection.** 🔴 **THIS TEST IS WHAT WOULD LET A HITTER ROW CARRY A REAL NUMBER.** **Sam chose the target himself: `P(1+ hit)`, the over-0.5-hits line** — **the most-bet hitter prop and a clean binary outcome directly comparable to the pitcher model's Brier score.**

**THE DATA** `[measured 2026-08-24 — BEFORE ANY FITTING]`:

| | |
|---|---|
| Hitters in the pool | 453 |
| Game rows | 38,691 |
| Rows with at least one plate appearance | **37,541** |
| Hitters with 80+ played games | 242 |
| League `P(1+ hit)` | **57.4%** |
| Plate appearances per played game | mean **3.77**, sd **1.13**, range 1–7 |
| Total bases per played game | mean 1.35 |

🔴 **THE OPPOSING-STARTER JOIN IS THE REASON THIS IS WORTH DOING, AND IT WAS VERIFIED FIRST.** **The hitter log records only the opposing TEAM.** **The pitcher logs can be reversed onto it — a starter's row names his date and his opponent — and `[measured 2026-08-24]` 95.7% of hitter rows (35,935) resolve to EXACTLY ONE opposing starter, 1.5% are ambiguous, 2.8% do not match.** ➡️ **Without that join this would be a dressed-up season average.**

⚠️ **A KNOWN DEFECT IN THAT JOIN, STATED BEFORE IT IS USED.** **It currently keys on each hitter's CURRENT team for every historical row, so a TRADED hitter's pre-trade games are matched against the WRONG pitching staff, silently.** **Jo Adell is the live example — Cleveland now, 127 games.** **PART OF THE UNMATCHED 2.8% IS EXACTLY THIS.** ⛔ **A consistency check must be built and must PASS BEFORE the fit, and rows that fail it are DROPPED, not guessed at.**

⚠️ **TWO INPUTS DO NOT EXIST, AND THEIR ABSENCE IS RECORDED RATHER THAN WORKED AROUND: PARK FACTORS** (no venue in the hitter log) **and LINEUP SLOT.** 🔴 **SLOT IS THE DOMINANT DRIVER OF PLATE APPEARANCES** — batting second versus eighth — **and PA is the largest source of game-to-game variance the current estimator ignores entirely.** ⚠️ **Trailing mean PA is used as a proxy and is NOT the same thing.**

**THE SPECIFICATION — FIXED NOW, BEFORE ANY REGRESSION IS RUN:**

| | |
|---|---|
| **Target** | `P(H >= 1)` on a game in which the hitter recorded at least one plate appearance |
| **Sample** | Hitter game rows with `pa > 0`; hitter has **>= 20 prior played games**; opposing starter resolved **unambiguously** and passing the trade-consistency check; that starter has **>= 5 prior starts**. **Point-in-time throughout — every predictor computed from games strictly BEFORE the row** |
| **Features (EXACTLY FOUR, no others, no interactions)** | **1.** his hits-per-plate-appearance over his last **20** played games · **2.** his mean plate appearances over the same 20 · **3.** the opposing starter's **hits allowed per batter faced** over his prior starts · **4.** home/road |
| **Model** | Logistic regression. **ONE SPECIFICATION.** |
| **Split** | **CHRONOLOGICAL, NOT RANDOM.** Train on games before **2026-07-15**, test on **2026-07-15 onward**. 🔴 **A random split leaks the future into the past through the trailing windows** |
| **Incumbent to beat** | **The estimator SHIPPING TODAY:** the Jeffreys-smoothed rate `(h + 0.5) / (n + 1)`, where `h` is his prior played games with 1+ hit, computed point-in-time |
| **Pass** | The fitted model beats the incumbent on **Brier score by >= 0.005** on the held-out set, **AND is not worse on log loss** |
| **Fail** | Anything less. **Record it FAILED and ship nothing.** **Hitter rows keep the smoothed season rate and keep carrying no confidence number** |
| ⛔ **Forbidden** | Adding a feature, changing the 20-game window, moving the split date, or re-cutting the sample **after seeing the first result.** **Specification shopping produced both of this project's worst errors** |

🔴 **IF IT PASSES, THAT IS NOT PERMISSION TO PRINT A CONFIDENCE %.** **A passing Brier score earns the model a place in the pipeline.** **Whether a hitter row DISPLAYS a Gizmo's rating is a SEPARATE decision under ledger rule 55, and it needs its own calibration table with its own bands** — **the pitcher bands do not transfer.** ⛔ **Do not reuse them.**

⚠️ **THE LEAGUE BASE RATE IS 57.4%, SO A MODEL THAT PREDICTS THE BASE RATE FOR EVERYONE ALREADY SCORES A BRIER OF ABOUT 0.245.** ➡️ **State the base-rate Brier alongside BOTH results, or the comparison is unreadable.**

### 🔴 `[measured 2026-08-24]` RESULT — **FAILED**

🔴 **T27 FAILED ITS PRE-REGISTERED BAR. NOTHING SHIPS. Hitter rows keep the smoothed season rate and keep carrying no confidence number.**

**The sample, after the filters the specification fixed in advance:**

| | |
|---|---|
| Usable rows | **21,323** |
| Train (before 2026-07-15) | 13,444 — base rate 0.5861 |
| Test (2026-07-15 onward) | **7,879** — base rate 0.5752 |
| Dropped: fewer than 20 prior played games | 9,060 |
| Dropped: opposing starter had under 5 prior starts | 4,786 |
| Dropped: **failed the trade-consistency check** | 1,379 |
| Dropped: starter ambiguous or missing | 993 |

✅ **THE TRADE-CONSISTENCY CHECK VALIDATED ITSELF.** The schedule was rebuilt from the hitter logs — a (date, team, opponent) triple supported by 3+ different players is a real game, one supported by fewer is a player in the wrong place. It kept **3,862 directed team-days**. Thirty teams over roughly 128 dates should produce about **3,840**. **The reconstruction landed within half a percent of the true schedule size, which is what licenses using it as a filter.**

**THE FIT** (inputs standardised, so betas are per standard deviation and directly comparable):

| Term | β | z |
|---|---|---|
| intercept | 0.3537 | 19.98 |
| **his mean PLATE APPEARANCES, last 20** | **0.2580** | **14.24** |
| his hits per PA, last 20 | 0.0732 | 4.04 |
| opposing starter's hits allowed per batter faced | 0.0540 | 3.04 |
| home | −0.0260 | **−1.47 — NULL** |

**HELD-OUT RESULT, 7,879 rows:**

| Estimator | Brier | LogLoss |
|---|---|---|
| base rate (predict 58.6% for everyone) | 0.24446 | 0.68204 |
| **INCUMBENT — the smoothed rate that ships today** | **0.24248** | **0.67828** |
| T27 model | **0.24013** | 0.67321 |

**Brier improvement over the incumbent: +0.00236, against a pre-registered bar of +0.00500.** LogLoss improved by +0.00508, which clears its half of the criterion. **The criterion required BOTH. It FAILS.**

⛔ **THE BAR WAS NOT MOVED, AND THE TEMPTATION TO MOVE IT IS THE WHOLE REASON IT WAS WRITTEN DOWN FIRST.** The model IS better than the incumbent — just not by the margin declared in advance. **A margin chosen after seeing +0.00236 would not be a margin.**

✅ **IT IS NOT A BROKEN FIT, AND THAT WAS CHECKED BEFORE THE FAILURE WAS RECORDED:**

- **In-sample gain +0.00351 against out-of-sample +0.00236.** Similar magnitudes, so it is not overfitting — **the predictable signal in P(1+ hit) really is this small.**
- **Calibration on held-out data is excellent:** predicted 45–50% → actual 48.0% (n=818) · 55–60% → 57.8% (n=1,713) · 60–65% → 61.8% (n=2,440) · 65–70% → 66.1% (n=1,214).
- The incumbent was hand-recomputed on a sampled row and matched to 12 decimal places, confirming it is genuinely point-in-time.
- A 400-row recount of the outcome column found 2 apparent mismatches; **both were doubleheaders on 2026-08-17 and were the CHECK's naive indexing, not the data.** 276 player-dates in the pool carry two games.

🔴 **THE HEADLINE FINDING IS NOT THE FAILURE. IT IS THAT PLATE APPEARANCES DOMINATE.** At 0.258 per SD against 0.073, **how often a hitter comes to the plate carries roughly three and a half times the weight of how well he hits.** That is the largest single driver in the model and the current shipped estimator ignores it completely. ➡️ **It is also exactly what went wrong on the board on 2026-08-23**, when bench bats with high under-rates topped the picks list until a lineup-share flag was added.

⚠️ **HOME/ROAD IS NULL FOR HITTERS (z = −1.47), AND NEGATIVE.** Worth recording because it is **significant for pitchers** in the v4.0 model (±0.151 K, t=3.52). ⛔ **Do not assume a term transfers across sides of the ball.**

➡️ 🆕 **OPENS T28 (below) — prompted by T27's own coefficient table, not by shopping T27's leftovers.**

---

## T28. 🆕 Model expected PLATE APPEARANCES first, then hits-per-PA on top

`[opened 2026-08-24, pre-registered BEFORE any fitting]` 🔴 ⛔ **STATUS: CLOSED-FAILED 2026-08-24 — FITTED, MEASURED, AND IT FAILED BOTH LEGS OF ITS PRE-REGISTERED BAR. Held-out Brier −0.00108 against T27 (bar +0.00200) and +0.00127 against the INCUMBENT smoothed rate (bar +0.00500). IT FAILED WORSE THAN T27. NOTHING SHIPPED.** ⛔ **THE SPECIFICATION, THE PASS BAR AND THE FORBIDDEN LIST BELOW ARE UNCHANGED AND WERE NOT MOVED — the result is recorded BENEATH them.** **Prompted by T27's own coefficient table, not by shopping T27's leftovers.**

**Why:** T27 put trailing PA in as a flat feature and it came back as the dominant term. **The right structure may be a two-stage one — predict how many times he bats, then how likely each trip produces a hit — rather than one flat logistic that has to learn both at once.**

| | |
|---|---|
| **Target** | Stage 1: `E[PA]` for the game. Stage 2: `P(hit per PA)`. Combined: `P(H >= 1) = 1 − (1 − p)^E[PA]` |
| **Sample** | Identical filters to T27, including the trade-consistency check. **Same chronological split at 2026-07-15.** ⛔ Deliberately the same sample so the two are comparable |
| **Stage 1 inputs** | his trailing-20 mean PA · his team's trailing-20 mean runs-per-game if derivable, else omitted and said so · home/road |
| **Stage 2 inputs** | his trailing-20 hits per PA · the opposing starter's hits allowed per batter faced |
| **Model** | OLS for stage 1, logistic for stage 2. **ONE specification.** |
| **Pass** | Beats the T27 model on held-out **Brier by >= 0.002** AND beats the INCUMBENT smoothed rate by **>= 0.005** — the same bar T27 had to clear |
| **Fail** | Anything less. **Record FAILED and ship nothing.** |
| ⛔ **Forbidden** | Re-using T27's held-out set to choose anything. Changing the window, the split, or the filters. **Adding lineup slot** — it is not in the data, and inventing a proxy after seeing T27's result is shopping |

⚠️ **LINEUP SLOT IS THE REAL MISSING VARIABLE AND IT IS NOT IN THE STACK.** Batting second versus eighth is most of the PA gap. **Trailing mean PA is a proxy and must never be described as the slot.** ➡️ **If a lineup source is ever added, that is a new test, not an amendment to this one.**

### 🔴 `[measured 2026-08-24]` RESULT — **FAILED**

🔴 **T28 FAILED, AND IT FAILED WORSE THAN T27. NOTHING SHIPS.**

**Identical sample to T27 by design — 21,323 rows, 13,444 train / 7,879 test — so the two are directly comparable.**

**STAGE 1 — E[PA] by OLS.** RMSE **0.985 train / 1.009 test**, against a plate-appearance standard deviation of **1.13**. ⚠️ **It barely predicts anything.**

| Term | coefficient |
|---|---|
| intercept | +3.8124 |
| his trailing-20 PA | +0.4866 |
| team runs/game, trailing 20 | **−0.0473 — near null, and the WRONG SIGN** |
| home | **−0.0882** |

**STAGE 2 — P(hit per PA), logistic, PA-weighted.** League rate ≈ 0.2208.

| Term | coefficient |
|---|---|
| intercept | −1.2640 |
| his trailing-20 hits/PA | **+0.0387** |
| opposing starter's H/BF | **+0.0359** |

⚠️ **Both stage-2 terms are tiny. Hits-per-plate-appearance is very close to unpredictable at this resolution.**

**HELD-OUT RESULT, 7,879 rows, base rate 0.5752:**

| Estimator | Brier | LogLoss |
|---|---|---|
| INCUMBENT smoothed rate | 0.24248 | 0.67828 |
| T27 model | **0.24013** | 0.67321 |
| **T28 two-stage** | **0.24121** | 0.67541 |

**T28 vs T27: −0.00108** against a bar of **+0.00200**. **T28 vs incumbent: +0.00127** against a bar of **+0.00500**. **FAILS BOTH.**

🔴 **THE TWO-STAGE STRUCTURE IS WORSE THAN THE FLAT LOGISTIC, AND THE REASON IS INSTRUCTIVE.** Splitting the problem forced two things on the model that the flat version never had to accept: a stage-1 estimate of `E[PA]` that is barely better than the mean, and the combination form `P(H >= 1) = 1 - (1-p)^E[PA]`, which **assumes plate appearances are independent trials at a constant rate**. The flat logistic was free to learn the relationship instead of being told it. ⛔ **A better-motivated structure is not automatically a better model.**

### 🔴 STOP WORKING ON THIS TARGET

**Two pre-registered specifications have now failed on `P(1+ hit)`, and the incumbent smoothed season rate has beaten both by the bar that was set in advance.** ➡️ **The honest reading is that this market has very little predictable structure left once a player's own smoothed rate is known.** ⛔ **A third specification would be specification shopping** — this project has recorded two headline coefficients that died exactly that way. **Do not open T29 on P(1+ hit).** If hitters are revisited, it must be on a DIFFERENT target (total bases, or a market with more spread) or with a genuinely NEW input — lineup slot being the obvious one, and it is not in the stack.

### ✅ WHAT THE TWO FAILURES BOUGHT

**Plate appearances are the dominant term (T27, β 0.258/SD vs 0.073 for hitting rate) and they are ALSO nearly unpredictable (T28, RMSE 0.985 against sd 1.13).** ➡️ **The biggest driver of a hitter's night is the thing we can least forecast.** That is a real ceiling on hitter props, not a failure of either specification, and it should temper any future claim about this market.

---

## T29. 🆕 The second half of Phase 2: TOTAL BASES — does a fitted `P(TB >= 2)` beat the raw rate?

`[opened 2026-08-24, pre-registered BEFORE any fitting]` 🔴 ⛔ **STATUS: CLOSED-FAILED 2026-08-24 — FITTED, MEASURED, AND IT DID NOT CLEAR ITS PRE-REGISTERED BAR. Held-out Brier improvement over the INCUMBENT +0.00119 against a declared +0.00500 — A WIDER MISS THAN T27's. NOTHING SHIPPED, AND THE PRE-COMMITTED CONSEQUENCE IS TRIGGERED: HITTER MODELLING ON THIS DATA SET IS CLOSED.** ⛔ **THE SPECIFICATION, THE PASS BAR AND THE FORBIDDEN LIST BELOW ARE UNCHANGED AND WERE NOT MOVED — the result is recorded BENEATH them.**

**Why this is not a re-run of a closed question.** **T27 and T28 both failed on `P(1+ hit)` and that target is CLOSED.** 🔴 **TOTAL BASES WAS ALWAYS THE OTHER HALF OF PHASE 2 AND HAS NEVER BEEN ATTEMPTED.** **It is a different problem: hits is a near coin-flip at 57.4%, which is precisely why a player's own smoothed rate was so hard to beat — the incumbent already contained most of the signal.** ⛔ **This is not specification shopping on a closed target; it is the SECOND TARGET, on a DIFFERENT OUTCOME, with its own bar.**

**Reconnaissance, measured 2026-08-24 BEFORE the specification was fixed:**

🔴 **THE MARKET POSTS ONE LINE.** **Of 240 total-bases quotes on the live board, 236 are over/under 1.5 and 4 are 3.5.** ➡️ **The target is therefore `P(TB >= 2)`, the over-1.5 line, because that is the bet that actually exists.** ⛔ **Modelling a line the books do not post would be an academic exercise.**

| Total bases in a played game | share |
|---|---|
| 0 | 42.6% |
| 1 | 24.6% |
| 2 | 13.6% |
| 3 | 5.8% |
| 4 | 7.2% |
| 5+ | 6.3% |
| **mean** | **1.352** |

| Threshold | base rate |
|---|---|
| TB >= 1 (over 0.5) | 57.4% |
| **TB >= 2 (over 1.5) — THE TARGET** | **32.8%** |
| TB >= 3 (over 2.5) | 19.2% |

⚠️ **A base rate of 32.8% sits FURTHER FROM A COIN FLIP than hits did, so there is more separation available in principle.** **Base-rate Brier is about 0.2204, against 0.2445 for the hits target.** ➡️ **STATE IT ALONGSIDE THE RESULTS OR THE COMPARISON IS UNREADABLE.**

⚠️ 🔴 **AN INPUT WE WANTED DOES NOT EXIST AND IS NOT BEING FAKED.** **The pitcher game log carries `hit`, `bb`, `k`, `bf`, `outs`, `er`, `np` — NO EXTRA-BASE DETAIL AT ALL — so a starter's TOTAL BASES ALLOWED CANNOT BE COMPUTED.** ➡️ **Two available PROXIES are used instead and are LABELLED as proxies: hits allowed per batter faced (contact allowed) and strikeouts per batter faced (balls never put in play).** ⛔ **Do not describe either as a total-bases-allowed rate.**

**THE SPECIFICATION — FIXED NOW, BEFORE ANY REGRESSION IS RUN:**

| | |
|---|---|
| **Target** | `P(TB >= 2)` — the over-1.5 total-bases line — in a game where the hitter recorded at least one plate appearance |
| **Sample** | **IDENTICAL filters to T27 and T28**, deliberately, so all three are comparable: `pa > 0`; hitter has **>= 20 prior played games**; opposing starter resolved unambiguously and passing the **trade-consistency check**; that starter has **>= 5 prior starts**. **Point-in-time throughout** |
| **Features (EXACTLY FIVE, no others, no interactions)** | **1.** his **total bases per plate appearance** over his last **20** played games · **2.** his mean plate appearances over the same 20 · **3.** the opposing starter's **hits allowed per batter faced** (PROXY) · **4.** the opposing starter's **strikeouts per batter faced** (PROXY) · **5.** home/road |
| **Model** | Logistic regression. **ONE SPECIFICATION.** |
| **Split** | **CHRONOLOGICAL**, train before **2026-07-15**, test **2026-07-15 onward** — the same split as T27 and T28 |
| **Incumbent to beat** | **The same estimator that ships today, at this line:** the Jeffreys-smoothed rate `(h + 0.5) / (n + 1)` where `h` is his prior played games with `TB >= 2`, computed point-in-time |
| **Pass** | Beats the incumbent on **Brier by >= 0.005** on the held-out set **AND is not worse on log loss**. ⚠️ **The same ABSOLUTE bar as T27, which on a 0.2204 baseline is a slightly HARDER relative bar than it was on 0.2445. That is deliberate — a bar that moves with the target is not a bar** |
| **Fail** | Anything less. **Record FAILED and ship nothing.** |
| ⛔ **Forbidden** | Adding a feature, changing the 20-game window, moving the split, re-cutting the sample, or switching to a different TB threshold **after seeing the result** |

🔴 **PRE-COMMITTED CONSEQUENCE OF FAILURE, STATED BEFORE THE RESULT IS KNOWN.** **If T29 fails, HITTER MODELLING ON THIS DATA SET IS CLOSED — not just this target.** **Three pre-registered specifications across two outcomes would have lost to a smoothed season average, and the honest conclusion is that the available inputs do not support a hitter model.** ➡️ **Hitter rows stay 🔵 DESCRIPTIVE indefinitely, and the reopening condition is a NEW INPUT — LINEUP SLOT above all — not a new specification.**

🔴 **AND IF IT PASSES, THAT IS STILL NOT PERMISSION TO PRINT A CONFIDENCE %.** **Ledger rule 55 needs its own calibration table with its own bands for hitters.** ⛔ **The pitcher bands do not transfer.**

### 🔴 `[measured 2026-08-24]` RESULT — **FAILED**

🔴 **T29 FAILED. NOTHING SHIPS.**

**Same sample as T27 and T28 by design — 21,323 rows, 13,444 train / 7,879 test, held-out base rate 0.3242.**

| Term | β (per SD) | z |
|---|---|---|
| intercept | −0.6635 | −36.02 |
| **his mean PLATE APPEARANCES, last 20** | **0.2499** | **12.62** |
| **opposing starter's K/BF (proxy)** | **−0.0746** | **−3.44** |
| his total bases per PA, last 20 | 0.0608 | 3.19 |
| opposing starter's H/BF (proxy) | 0.0352 | **1.64 — not significant** |
| home | −0.0119 | **−0.65 — NULL, for the third time** |

| Estimator | Brier | LogLoss |
|---|---|---|
| base rate (predict 32.4%) | 0.21943 | 0.63076 |
| **INCUMBENT smoothed rate** | **0.21695** | 0.62496 |
| T29 model | 0.21576 | 0.62223 |

**Brier improvement +0.00119 against a bar of +0.00500.** LogLoss improved by +0.00274. **The criterion required both. It FAILS, and by a wider margin than T27 did.**

✅ **CHECKED BEFORE RECORDING, as with T27:**

- **In-sample gain +0.00379 against out-of-sample +0.00119.** ⚠️ **A 3x shrinkage — more than T27's 1.5x, which is what five features on 13,444 rows will do.** **The out-of-sample gain is the real one and it is tiny.**
- **Calibration on held-out data is good:** predicted 20–25% → actual 20.5% (n=667) · 25–30% → 26.8% (n=1,516) · 30–35% → 31.2% (n=1,840) · 35–40% → 36.2% (n=2,332) · 40–45% → 41.2% (n=1,215). Only the 45–50% bucket (n=173) misses. **The model is honest. It is simply not better by the bar.**

### 🔴 THE PRE-COMMITTED CONSEQUENCE IS NOW TRIGGERED: HITTER MODELLING ON THIS DATA IS CLOSED

**T29's own pre-registration, written before the result was known, said: if it fails, hitter modelling on this data set is CLOSED — not just this target.** **That condition is met.**

**Three pre-registered specifications, across two different outcomes, have now lost to a smoothed season average:**

| Test | Target | Brier gain over the incumbent | Bar |
|---|---|---|---|
| T27 | P(1+ hit), flat logistic | +0.00236 | +0.00500 |
| T28 | P(1+ hit), two-stage | +0.00127 | +0.00500 |
| T29 | P(TB >= 2), flat logistic | +0.00119 | +0.00500 |

⛔ **DO NOT OPEN A FOURTH SPECIFICATION ON HITTER PROPS.** ➡️ **The reopening condition is a NEW INPUT, not a new specification — LINEUP SLOT above all, and it is not in the stack.** **Hitter rows on the Picks tab stay 🔵 DESCRIPTIVE indefinitely: the player's own smoothed rate, no confidence number, no band.**

### ✅ THE THROUGH-LINE ACROSS ALL THREE, WHICH IS WORTH MORE THAN A MARGINAL MODEL

🔴 **PLATE APPEARANCES ARE THE DOMINANT TERM IN EVERY HITTER TARGET TRIED, AND THEY ARE THE THING WE CAN LEAST FORECAST.**

| | |
|---|---|
| T27, P(1+ hit) | PA β **0.258**/SD, z **14.24** — dominant |
| T29, P(TB >= 2) | PA β **0.250**/SD, z **12.62** — dominant again |
| T28, predicting PA itself | **RMSE 0.985 against a standard deviation of 1.13** |

➡️ **The biggest driver of a hitter's night is barely forecastable from what we hold. That is a ceiling on hitter props, not a failure of any one specification, and it should temper every future claim about this market.** ⚠️ **It is also, independently, what put bench bats at the top of the live board on 2026-08-23 until a lineup-share flag was added.**

---

## T30. 🆕 Hitter modelling REOPENS on the input T29 named: BATTING ORDER

`[opened 2026-08-25, pre-registered BEFORE any fitting]` 🔴 ⛔ **STATUS: CLOSED-FAILED 2026-08-25 — FITTED, MEASURED, AND BOTH ARMS FAILED BOTH BRIER LEGS OF THE PRE-REGISTERED BAR. ARM A: +0.00266 over the INCUMBENT (bar +0.00500) and +0.00003 over T27-REFITTED (bar +0.00200). ARM B: +0.00295 and +0.00033 against the same two bars. NOTHING SHIPPED.** ⛔ **THE SPECIFICATION, THE PASS BARS AND THE FORBIDDEN LIST BELOW ARE UNCHANGED AND WERE NOT MOVED — the result is recorded BENEATH them.**

🔴 **THIS IS THE REOPENING T29 AUTHORISED, AND IT IS AUTHORISED BECAUSE THE INPUT IS NEW, NOT BECAUSE THE SPECIFICATION IS.** **T29 closed hitter modelling and wrote the condition in advance:** *"the reopening condition is a NEW INPUT — lineup slot above all — not a new specification."* ✅ **That input now exists.**

**THE BACKFILL, measured 2026-08-25 BEFORE the specification was written:**

| | |
|---|---|
| Dates covered | **176** (2026-03-01 → 2026-08-23) |
| Batter-games recovered | **53,424** |
| With a real batting slot | **53,424 — all of them** |
| Genuine starters (`sub == 0`) | **41,472** |
| Distinct players | 1,989 |
| Slot distribution | near-uniform 1–9, from 5,755 to 6,341 per slot |

✅ **AND THE SIGNAL IS THERE, MONOTONIC ACROSS ALL NINE SLOTS:**

| Slot | P(1+ hit) | PA/game | n |
|---|---|---|---|
| 1 | **65.7%** | 4.50 | 3,894 |
| 2 | 66.2% | 4.41 | 3,892 |
| 3 | 64.8% | 4.30 | 3,917 |
| 4 | 62.4% | 4.20 | 3,881 |
| 5 | 61.2% | 4.06 | 3,829 |
| 6 | 60.6% | 3.91 | 3,751 |
| 7 | 58.6% | 3.79 | 3,618 |
| 8 | 55.9% | 3.62 | 3,601 |
| 9 | **53.6%** | 3.48 | 3,439 |

**A 12-POINT SPREAD ON THE OUTCOME, DRIVEN BY A FULL PLATE APPEARANCE OF DIFFERENCE.** ➡️ **This is precisely the mechanism T27, T28 and T29 all identified and none could see.**

### 🔴 THE OPERATIONAL CATCH, STATED BEFORE FITTING RATHER THAN DISCOVERED AFTER

⚠️ **THE LINEUP CARD IS POSTED ROUGHLY 2–3 HOURS BEFORE FIRST PITCH. THE 10:45am ET CARD CANNOT KNOW A 7pm GAME'S BATTING ORDER.** ⛔ **So today's ACTUAL slot is NOT a shippable feature on the morning card, and a test that used it and then claimed a live edge would be lying about what the model can see.**

`[measured]` **How well a player's recent slot predicts today's slot**, over 34,266 starts with 10+ prior starts: **mean absolute error 1.04 slots**, median 0.70; the rounded prediction is exactly right **39.9%** of the time and within one slot **63.3%**.

➡️ **THE TEST THEREFORE HAS TWO ARMS, AND ONLY ONE OF THEM CAN SHIP ON THE MORNING CARD:**

| Arm | Feature | Where it could ship |
|---|---|---|
| **A — SHIPPABLE** | his **trailing-20 mean batting slot** (known at any time) | the 10:45am and 4:50pm cards, as they run today |
| **B — UPPER BOUND** | **today's ACTUAL slot** | ⛔ **nowhere today.** Only a card generated AFTER lineups post could use it |

⚠️ **A LIKELY REASON ARM A FAILS, WRITTEN DOWN NOW SO IT CANNOT BE CLAIMED AS A DISCOVERY LATER: THE INCUMBENT ALREADY CONTAINS MOST OF THE SLOT INFORMATION.** **A leadoff hitter's own smoothed hit rate is already the rate of a man getting 4.5 plate appearances a night.** ➡️ **Slot adds value mainly when it CHANGES — and a change is exactly what the trailing mean cannot predict.**

**THE SPECIFICATION — FIXED NOW, BEFORE ANY REGRESSION IS RUN:**

| | |
|---|---|
| **Target** | `P(H >= 1)`, the over-0.5-hits line — **the same target as T27**, deliberately, so the marginal value of the new input is isolated rather than confounded with a target change |
| **Sample** | Games the hitter **STARTED**, by real batting order (`sub == 0`) — **not** the `pa > 0` sample T27 used, and **not** the `pa >= 3` proxy. Hitter has **>= 20 prior started games**; opposing starter resolved unambiguously and passing the trade-consistency check, with **>= 5 prior starts**. **Point-in-time throughout** |
| **THREE estimators, ONE sample** | ⛔ **All three must be scored on the SAME held-out rows or the comparison is meaningless:** **(1)** the **INCUMBENT** smoothed rate, recomputed on this sample · **(2)** **T27's four features** refitted on this sample · **(3)** **T27's features PLUS the new slot feature** |
| **Model** | Logistic regression. **ONE SPECIFICATION PER ARM.** |
| **Split** | **CHRONOLOGICAL**, train before **2026-07-15**, test **2026-07-15 onward** — the same split as T27/T28/T29 |
| **Pass (Arm A)** | Arm A beats the **INCUMBENT** on **Brier by >= 0.005** **AND** beats **T27-refitted by >= 0.002** **AND** is not worse on log loss. ⛔ **BOTH MARGINS, OR IT FAILS** — beating the incumbent while adding nothing over T27 would mean the SAMPLE changed, not that slot helped |
| **Pass (Arm B)** | The same two margins. **REPORTED AS AN UPPER BOUND ONLY.** ⛔ **Arm B passing does NOT license shipping anything on the morning card** |
| **Fail** | Anything less. **Record FAILED and ship nothing.** |
| ⛔ **Forbidden** | Adding a feature beyond the one slot term, changing the 20-game window, moving the split, re-cutting the sample, or reporting Arm B as if it were live-usable |

🔴 **IF ARM B PASSES AND ARM A FAILS, THAT IS A PRODUCT FINDING, NOT A MODEL FINDING.** **It would mean the information is real and arrives too late for the card we currently publish.** ➡️ **The response would be a LATE CARD generated after lineups post — an OPERATIONAL change — and that would need its own pre-registration before anything ships.** ⛔ **Do not quietly start using Arm B on the existing card.**

🔴 **AND IF ARM A PASSES, THAT IS STILL NOT PERMISSION TO PRINT A CONFIDENCE %.** **Ledger rule 55 needs hitters to have their own calibration table with their own bands.** ⛔ **The pitcher bands do not transfer.**

### 🔴 `[measured 2026-08-25]` RESULT — **BOTH ARMS FAILED**

🔴 **T30 FAILED. NOTHING SHIPS. Hitter rows keep the smoothed season rate and keep carrying no confidence number.**

**THE SAMPLE, built on the filters the specification fixed in advance — games he STARTED by real batting order, not `pa > 0` and not a `pa >= 3` proxy:**

| | |
|---|---|
| Usable rows | **18,578** — 444 distinct hitters over 121 dates |
| Train (before 2026-07-15) | 11,500 — base rate **0.6272** |
| Test (2026-07-15 onward) | **7,078** — base rate **0.6140** |
| Dropped: fewer than 20 prior STARTED games | 9,072 |
| Dropped: opposing starter had under 5 prior starts | 4,092 |
| Dropped: **failed the trade-consistency check** | 1,073 |
| Dropped: starter ambiguous or missing | 707 |
| Dropped from the started log: **lineup join not unambiguous** | 369 — 320 doubleheaders whose lineup entries disagree, 14 with two lineup entries against one log row |

✅ **THE DOUBLEHEADER AMBIGUITY WAS DROPPED, NOT GUESSED AT.** **A hitter's log carries one row per game keyed only by DATE, so on a doubleheader there is no way to say which lineup card belongs to which row unless every game that day was a start at the same slot.** ⛔ **Where they disagree the whole date leaves the started log rather than being assigned by position.**

✅ **The trade-consistency check was rebuilt exactly as T27 built it and again validated itself: 3,892 directed team-days kept, against the ~3,900 that thirty teams over roughly 130 dates should produce.**

**THE FITS** (inputs standardised, so betas are per standard deviation and directly comparable):

| Term | T27-REFITTED β (z) | ARM A β (z) | ARM B β (z) |
|---|---|---|---|
| intercept | 0.5244 (27.06) | 0.5245 (27.06) | 0.5247 (27.07) |
| **his mean PLATE APPEARANCES, last 20** | **0.1498 (7.59)** | **0.1175 (3.59)** | **0.1049 (3.95)** |
| opposing starter's H/BF | 0.0574 (2.95) | 0.0581 (2.99) | 0.0582 (2.99) |
| his hits per PA, last 20 | 0.0557 (2.81) | 0.0557 (2.80) | 0.0486 (2.42) |
| home | −0.0308 (**−1.59**) | −0.0305 (**−1.58**) | −0.0304 (**−1.57**) |
| **his TRAILING-20 MEAN SLOT** (Arm A) | — | **−0.0403 (−1.24 — NOT SIGNIFICANT)** | — |
| **TODAY'S ACTUAL SLOT** (Arm B) | — | — | **−0.0681 (−2.54 — REAL)** |

**HELD-OUT RESULT, 7,078 rows, base rate 0.6140 — all five estimators scored on the SAME rows:**

| Estimator | Brier | LogLoss |
|---|---|---|
| base rate (predict 62.7% for everyone) | **0.23717** | 0.66729 |
| 🔴 **INCUMBENT — the smoothed rate that ships today** | 🔴 **0.23819** | 0.66966 |
| T27's four features, refitted on this sample | 0.23557 | 0.66390 |
| **ARM A — plus his trailing-20 mean slot** | **0.23553** | 0.66384 |
| **ARM B — plus today's actual slot** | **0.23524** | 0.66322 |

| | vs INCUMBENT (bar +0.00500) | vs T27-REFITTED (bar +0.00200) | LogLoss (must be ≥ 0) | **VERDICT** |
|---|---|---|---|---|
| **ARM A** | **+0.00266 ❌** | **+0.00003 ❌** | +0.00582 ✅ | 🔴 **FAIL** |
| **ARM B** | **+0.00295 ❌** | **+0.00033 ❌** | +0.00644 ✅ | 🔴 **FAIL** |

⛔ **NEITHER BAR WAS MOVED, AND THE TWO-MARGIN STRUCTURE IS WHAT MADE THE RESULT READABLE.** **The entry pre-registered both margins with a stated reason — *"beating the incumbent while adding nothing over T27 would mean the SAMPLE changed, not that slot helped."*** ➡️ 🔴 **THAT IS EXACTLY WHAT HAPPENED. Arm A's entire +0.00266 over the incumbent is T27's four features, which are worth +0.00262 on this sample by themselves. THE SLOT TERM IS WORTH +0.00003.** ⚠️ **A single-margin criterion would have reported a 0.0027 gain and invited a shipping decision. It would have been measuring the sample change.**

### ✅ IT IS NOT A BROKEN FIT, AND THAT WAS CHECKED BEFORE THE FAILURE WAS RECORDED

- **In-sample against out-of-sample gain over the incumbent: T27-refitted +0.00444 / +0.00262 · Arm A +0.00447 / +0.00266 · Arm B +0.00457 / +0.00295.** **Similar magnitudes — it is not overfitting.**
- 🔴 **THE SLOT VARIABLE ITSELF IS SOUND, WHICH IS THE CHECK THAT MATTERS MOST HERE.** **On the T30 sample the raw `P(1+ hit)` by today's actual slot runs 66.2% · 66.5% · 65.5% · 63.1% · 62.9% · 60.0% · 59.8% · 56.6% · 55.0% from slot 1 to slot 9** — **monotonic, an 11-point spread, reproducing the reconnaissance on a different sample.** **A slot-only model beats the base rate by +0.00155 Brier held out.** ➡️ **The variable carries real information. It simply carries almost none that the model did not already have.**
- **Held-out calibration of Arm B, the better arm, is excellent:** 50–55% → 51.6% (n=473) · 55–60% → 57.4% (n=1,639) · 60–65% → 61.2% (n=2,652) · 65–70% → 66.5% (n=2,146). Only the 70–75% bucket (n=145) misses.
- **The incumbent was hand-re-derived from the raw hitter log on sampled rows and matched to 12 decimal places**, confirming it is genuinely point-in-time on this sample too.
- **Sample shape agrees with the pre-registration's reconnaissance:** `P(1+ hit)` on started games reads **62.2%** here against the **61.24%** measured before the specification was written.

### 🔴 WHY IT FAILED, MEASURED RATHER THAN ARGUED — AND THE PRE-REGISTRATION CALLED IT

**The entry wrote the reason down in advance so it could not be claimed as a discovery later:** *"THE INCUMBENT ALREADY CONTAINS MOST OF THE SLOT INFORMATION — a leadoff hitter's own smoothed hit rate is already the rate of a man getting 4.5 plate appearances a night."* ✅ **That is now measured:**

| Correlation, on all 18,578 rows | |
|---|---|
| today's slot ↔ his trailing-20 mean slot | **+0.827** |
| today's slot ↔ his trailing-20 mean PA | **−0.675** |
| today's slot ↔ the INCUMBENT smoothed rate | **−0.455** |
| his trailing-20 mean slot ↔ the INCUMBENT rate | **−0.491** |

➡️ **And the collinearity is visible inside the fit: the trailing-PA coefficient collapses from 0.1498 (z 7.59) to 0.1175 (z 3.59) the moment slot enters. The two terms are carrying the same fact.**

⚠️ 🔴 **ARM B'S SLOT TERM IS SIGNIFICANT AND ARM A'S IS NOT — z = −2.54 against z = −1.24 — WHICH IS PRECISELY THE PRE-REGISTERED PREDICTION: slot adds value mainly when it CHANGES, and a change is exactly what the trailing mean cannot see.** ➡️ **The mechanism was right. The magnitude is still too small to clear anything.**

### ⛔ THE "PRODUCT FINDING" BRANCH IS **NOT** TRIGGERED — DO NOT BUILD A LATE CARD ON THIS

🔴 **T30 pre-registered what to do if Arm B passed while Arm A failed: treat it as a PRODUCT finding and consider a LATE CARD generated after lineups post.** ⛔ **THAT BRANCH IS NOT OPEN, BECAUSE ARM B FAILED TOO.** **Today's actual batting order — the information a late card would exist to capture — is worth +0.00033 Brier over T27's features, against a bar of +0.00200.** ➡️ **A late card may still be worth building for other reasons (scratches, rest days, a bat out of the lineup entirely), but T30 provides NO evidence for it and must not be cited as if it did.**

### ⚠️ 🆕 A SECOND RESULT, RECORDED BECAUSE IT CUTS AGAINST THE SHIPPED ESTIMATOR

🔴 **ON THE STARTED-GAMES SAMPLE THE INCUMBENT IS WORSE THAN PREDICTING THE LEAGUE AVERAGE FOR EVERYONE — Brier 0.23819 against 0.23717.** ⚠️ **On T27's `pa > 0` sample it was BETTER than the base rate (0.24248 against 0.24446). The ordering flips.**

➡️ 🔴 **THE READING, AND IT IS A READING AND NOT A TEST: most of what the player's own smoothed rate was buying on the old sample was the difference between a STARTER and a CAMEO, not the difference between one starter and another.** **Strip the cameos out — which is what a real batting-order filter does — and the individual differentiation is worth less than nothing on Brier.** ⚠️ **This is consistent with the cameo measurements already recorded elsewhere in the project (under 0.5 hits: 74.8% on cameos against 37.4% on starts).**

⛔ **THIS IS NOT PRE-REGISTERED AND IS NOT A FINDING. IT DOES NOT LICENSE CHANGING THE SHIPPED ESTIMATOR.** ➡️ **It is written here because it is the kind of thing that gets discovered later and mistaken for new.** **If the shipped hitter estimator is ever revisited, THIS is the question to pre-register: does a hitter's own smoothed rate beat the league base rate at all, once the sample is restricted to games he started?**

### 🔴 WHAT THIS MEANS FOR HITTER MODELLING — STATED AS A READING, NOT AS A PRE-COMMITTED CONSEQUENCE

⚠️ **T30 did NOT pre-register a consequence of failure, and one is NOT being invented after the fact.** ➡️ **What follows is a reading, labelled as one:**

**Four pre-registered specifications have now lost to a smoothed season average, across two targets and two samples:**

| Test | Target | Sample | Gain over the incumbent | Bar |
|---|---|---|---|---|
| T27 | P(1+ hit), flat logistic | `pa > 0` | +0.00236 | +0.00500 |
| T28 | P(1+ hit), two-stage | `pa > 0` | +0.00127 | +0.00500 |
| T29 | P(TB >= 2), flat logistic | `pa > 0` | +0.00119 | +0.00500 |
| **T30 Arm A** | P(1+ hit), + trailing slot | **STARTED** | **+0.00266** | +0.00500 |
| **T30 Arm B** | P(1+ hit), + actual slot | **STARTED** | **+0.00295** | +0.00500 |

🔴 **T29's reopening condition was a NEW INPUT, and it named LINEUP SLOT. That input has now been built, joined, verified and fitted — and it did not clear.** ➡️ **The condition has been spent on the input it named.** ⛔ **Another cut of slot — a slot-change flag, a slot interaction, a nine-way dummy, a different window — IS A NEW SPECIFICATION ON A SPENT INPUT, and this register's whole purpose is to forbid that.**

✅ **Hitter rows on the Picks tab stay 🔵 DESCRIPTIVE: the player's own smoothed rate, no confidence number, no band.**

✅ **WHAT THE BACKFILL BOUGHT ANYWAY, AND IT IS NOT NOTHING:** **the project now holds real batting order for 176 dates and 53,424 batter-games, which is what makes a STARTED-GAMES sample possible at all.** **That sample already corrected the board once — bench bats no longer top the picks list — and it is the correct population for every future hitter question, model or not.**

---

## T31. 🆕 PHASE 3 — the first GAME-LEVEL model. Does a fitted total beat a naive one?

`[opened 2026-08-25, pre-registered BEFORE any fitting]` 🔴 ⛔ **STATUS: T31a AND T31b CLOSED-FAILED 2026-08-25 — FITTED, MEASURED, AND NEITHER CLEARED ITS BAR. T31a came in +0.0054 MAE WORSE than the naive baseline (bar +0.10000). T31b gained +0.0403 over T31a on the same rows (bar +0.05000). NOTHING SHIPPED.** ⏳ **T31c REMAINS PRE-REGISTERED AND UNRUNNABLE — 55 of 400 games.** ⛔ **THE SPECIFICATION, THE PASS BARS AND THE FORBIDDEN LISTS BELOW ARE UNCHANGED AND WERE NOT MOVED — the result is recorded BENEATH them.**

🔴 **THIS IS THE FIRST TEST IN THIS PROJECT THAT IS NOT ABOUT A PLAYER.** Phase 1 models a pitcher, Phase 2 tried and failed to model a hitter. **T31 models the GAME.** ✅ **Sam chose the target himself, as he chose `P(1+ hit)` for T27: the GAME TOTAL, over/under combined runs** — the highest-volume market in baseball, and one his Odds tab already displays with **no model view whatsoever**.

### ✅ THE INPUT THAT UNBLOCKED IT — built 2026-08-25, and it did not exist that morning

**`collect.py` mode `scores`, backfilled on the Actions runner:** **177 dates walked, 2,314 games, validated 90/90 EXACT against every game where a real final was already on disk.**

⚠️ 🔴 **AND THE RAW BACKFILL IS NOT THE SAMPLE. `sportId=1` RETURNS THREE POPULATIONS THAT ARE NOT REGULAR-SEASON MLB, AND POOLING THEM SHIFTS THE RUN ENVIRONMENT.** `[measured 2026-08-25 BEFORE the specification was written]`

| Population | Games | Mean runs per team-game |
|---|---|---|
| ✅ **REGULAR SEASON** | **1,973** | **4.47** |
| ⛔ spring training (before opening day) | 311 | **5.02** |
| ⛔ non-MLB opponent | 30 | 4.17 |
| ⚠️ *everything pooled* | *2,314* | *4.54* |

🔴 **The 20 extra "teams" are 14 WORLD BASEBALL CLASSIC national sides (Mar 3–4), 4 MINOR-LEAGUE / MEXICAN LEAGUE clubs (Mar 22–24) and 2 ALL-STAR squads (Jul 14).** **Spring training scores half a run per team HIGHER** — minor leaguers, pitchers on limited counts, split squads. ➡️ **Pooled, the run environment reads +0.070 too high, and 15% of games are not regular-season baseball.** ⛔ **A model fitted on the pooled table projects high in a way that looks like signal.**

✅ **THE SAMPLE FILTER IS THEREFORE PART OF THE SPECIFICATION, NOT A LATER CLEANUP:** both clubs must be one of the **30 MLB teams taken from the hitter DB's own `team` field** (⛔ never a hand-typed list), and the date must be **on or after OPENING DAY, derived as the first date present in the hitter game logs** (⛔ never a hand-typed date). `[measured]` **that resolves to 2026-03-25.**

**THE SAMPLE, measured before the specification was fixed:**

| | |
|---|---|
| Clean regular-season games | **1,973** |
| Train (before 2026-07-15) | **1,444** |
| Test (2026-07-15 onward) | **529** |
| Combined runs | mean **8.94**, sd **4.52** |

⚠️ **`P(combined runs > 8.5)` reads 48.4% on this sample.** ⛔ **THAT IS NOT EVIDENCE ABOUT MARKET CALIBRATION and must not be quoted as such** — 8.5 is a fixed number chosen for the reconnaissance, **not** each game's posted line. **It says only that 8.5 sits near the median total.**

### 🔴 THE TEST SPLITS IN TWO, AND ONLY ONE HALF IS RUNNABLE. THIS IS STATED BEFORE FITTING, NOT DISCOVERED AFTER.

⛔ **THE MARKET BENCHMARK CANNOT BE BACKFILLED.** `[measured 2026-08-25]` **the gameline archive holds a posted total for 55 DISTINCT GAMES, spanning 2026-08-22 to 2026-08-25.** **Historical odds are a separate, more expensive API product — the same wall T25 hit.** ➡️ **So "does the model beat the book" is NOT decidable now and will not be decidable in September either.**

| Arm | What it asks | Sample | Runnable |
|---|---|---|---|
| **T31a** | Does a fitted model beat a NAIVE baseline? | 1,973 games | ✅ **NOW** |
| **T31b** | Do the STARTING PITCHERS add anything over team form? | the same 1,973 | ✅ **NOW** |
| **T31c** | Does the model beat the MARKET's posted total? | **55 games** | ⛔ **NO — accumulating** |

🔴 **T31a AND T31b ARE SANITY GATES, NOT SHIPPING GATES.** ⛔ **Passing them does NOT license putting a total on the board.** **Only T31c can do that, because only T31c compares against the number a bettor would actually have to beat.** ⚠️ **Beating a naive baseline is easy and means nothing at a sportsbook.**

**THE SPECIFICATION — FIXED NOW, BEFORE ANY REGRESSION IS RUN:**

| | |
|---|---|
| **Target** | **Combined runs** scored in a regular-season game, as a continuous quantity |
| **Sample** | The clean filter above. **Both starters resolved unambiguously via the existing opposing-starter join, each with >= 5 prior starts, for the T31b arm only.** **POINT-IN-TIME throughout** — every predictor computed from games strictly BEFORE the row |
| **T31a features (EXACTLY FOUR, no others, no interactions)** | **1.** away club's trailing-20 runs SCORED per game · **2.** away club's trailing-20 runs ALLOWED per game · **3.** home club's trailing-20 runs SCORED per game · **4.** home club's trailing-20 runs ALLOWED per game |
| **T31b features** | **T31a's four PLUS EXACTLY TWO:** **5.** away starter's trailing-8 EARNED RUNS per start · **6.** home starter's trailing-8 earned runs per start. ⛔ **Nothing else.** |
| **Model** | OLS. **ONE SPECIFICATION PER ARM.** |
| **Split** | **CHRONOLOGICAL**, train before **2026-07-15**, test **2026-07-15 onward** — deliberately the SAME split date as T27/T28/T29/T30, so nothing about the split is a new choice |
| **Baselines to beat, BOTH reported** | **(i)** the **LEAGUE MEAN** total computed point-in-time on training games only · **(ii)** **TEAM TRAILING**, i.e. away trailing-20 runs scored + home trailing-20 runs scored |
| **Metric** | **MAE and RMSE on held-out games. Report both.** |
| **Pass (T31a)** | Beats the BETTER of the two baselines on held-out **MAE by >= 0.10 runs** |
| **Pass (T31b)** | Beats **T31a** on held-out **MAE by >= 0.05 runs.** ⛔ **BOTH margins are absolute and were chosen before any result was seen** |
| **Fail** | Anything less. **Record FAILED and ship nothing.** |
| ⛔ **Forbidden** | Adding a feature, changing the 20-game or 8-start window, moving the split, re-cutting the sample, or switching from OLS **after seeing the first result.** **Specification shopping produced both of this project's worst errors.** |
| ⛔ **Forbidden, and this one is specific to Phase 3** | 🔴 **USING THE MARKET'S POSTED TOTAL, OR ANY MARKET-DERIVED QUANTITY, AS A FEATURE.** **T31c tests the model AGAINST the book; a model that has read the book's number and is then scored against it is measuring nothing.** ⚠️ **This is the mirror image of T25's hazard and it is FORBIDDEN here rather than merely flagged.** |

### 🔴 T31c — pre-registered NOW so it cannot be softened later

| | |
|---|---|
| **Specification** | For every game carrying a posted total, de-vig the over/under **INSIDE A SINGLE BOOK** and compare the model's `P(over)` against the book's implied `P(over)`, scored by **BRIER** against the realised outcome |
| **Pass** | The model beats the de-vigged market on Brier by **>= 0.010** over **>= 400 games** |
| **Fail** | Anything less — **including a better Brier on fewer than 400 games.** **Record FAILED and ship nothing.** |
| ⛔ **Blocked by** | **55 games captured.** ⚠️ **At roughly 15 games a day this reaches 400 around late October, i.e. AFTER the regular season ends.** ➡️ **SAY SO rather than deciding it early on 55.** |
| ⛔ **Forbidden** | De-vigging ACROSS books. **A single book, both sides, every time.** |

**Progress: 55 / 400 games with a captured total.**

🔴 **THE PRIOR, WRITTEN DOWN BEFORE THE RESULT SO IT CANNOT BE CLAIMED AS A DISCOVERY: GAME TOTALS ARE THE MOST HEAVILY MODELLED MARKET IN BASEBALL, AND THE HONEST EXPECTATION IS THAT T31c FAILS.** ➡️ **If T31a and T31b pass while T31c fails, that is the correct and most likely outcome, and it means the model is real but not sharper than the book.** ⛔ **That is NOT permission to ship a total with a Gizmo's confidence % on it (ledger rule 55).**

⚠️ **AND IF T31a PASSES, THE PITCHER MODEL'S BANDS DO NOT TRANSFER — game totals would need their own calibration table, exactly as hitters would have.**

### 🔴 `[measured 2026-08-25]` RESULT — **T31a FAILED. T31b FAILED.**

🔴 **NOTHING SHIPS. No total appears on the board, and the Odds tab's totals stay 🔵 MARKET-only.**

**THE SAMPLE, on the filters fixed in advance.** Clean regular-season games **1,973**; after requiring **20 prior games for BOTH clubs**, T31a holds **1,667 rows — 1,138 train / 529 test**. T31b additionally requires **both starters resolved with >= 5 prior starts**, leaving **1,028 rows — 648 train / 380 test**. Dropped: 306 for a club under 20 prior games, 538 for a starter under 5 prior starts, 101 for an ambiguous or missing starter, 340 spring-training games, 1 non-MLB club.

**HELD-OUT RESULT, 529 games:**

| Estimator | MAE | RMSE |
|---|---|---|
| baseline (i) league mean 9.08 | 3.6430 | 4.4578 |
| ✅ **baseline (ii) team trailing** | 🔴 **3.6227** | 4.5259 |
| **T31a — four team-form features** | **3.6281** | **4.4399** |

🔴 **T31a is +0.0054 MAE WORSE than simply adding the two clubs' trailing runs scored, against a bar of +0.10000. It FAILS, and it fails on the wrong side of zero.**

**T31b, scored on the SAME 380 held-out rows as T31a — because T31b's sample is a SUBSET, and comparing it against T31a's figure from the full set would measure the SAMPLE CHANGE rather than the starters. That is precisely the trap T30's second margin was written to catch, and it is avoided here by construction.**

| Estimator, same 380 rows | MAE | RMSE |
|---|---|---|
| baseline (ii) team trailing | 3.5750 | 4.5425 |
| T31a re-scored here | **3.5711** | 4.3991 |
| **T31b — plus both starters** | **3.5309** | **4.3706** |

**Gain from adding both starting pitchers: +0.0403 MAE, against a bar of +0.05000. It FAILS — but it is the closest thing to a real effect in this entry, and it fails narrowly.**

⛔ **NEITHER BAR WAS MOVED. A margin chosen after seeing +0.0403 would not be a margin.**

### 🔴 THE HEADLINE IS NOT THE FAILURE. IT IS HOW LITTLE OF A GAME TOTAL IS PREDICTABLE AT ALL.

| | |
|---|---|
| Actual combined runs, held out | **1 to 27**, sd **4.51** |
| The model's PREDICTED range | 🔴 **7.79 to 10.80** |
| **corr(predicted, actual)** | 🔴 **+0.0799** |

➡️ **The best linear predictor available from team form moves inside a THREE-RUN window while real games range from 1 to 27, and it correlates with the outcome at 0.08 — under 1% of variance.** 🔴 **A baseball game's run total is overwhelmingly same-day noise that season-long team form cannot see.**

⚠️ **This is the Phase 3 analogue of Phase 2's ceiling finding** — there, plate appearances dominated and were themselves unforecastable. **Here, almost nothing about the total is forecastable from what we hold.**

### ✅ CHECKED BEFORE RECORDING, as with T27 and T30

- 🔴 **T31a IS OVERFITTING AND THAT IS WHY IT FAILS: in-sample gain over the naive baseline +0.1211, out-of-sample −0.0054.** **The four team-form features fit the training set and carry nothing out of it.** **T31b shrinks too but survives: +0.1494 in-sample against +0.0441 out.**
- ✅ **POINT-IN-TIME INTEGRITY CONFIRMED BY HAND: sampled rows had their trailing-20 windows re-derived directly from the raw score file, walking each club's game sequence and stopping at the row's own `gamePk`. Zero mismatches.** **A mismatch would have meant a window saw a game it should not have.**
- ✅ **The fit is sane, not broken** — predictions centre on 8.99 against an actual mean of 8.70.

### 🔴 THE COEFFICIENT FINDING, AND IT IS THE MOST USEFUL THING THIS TEST PRODUCED

**Per standard deviation of the input, in runs of predicted total:**

| Feature | β × sd (runs) |
|---|---|
| 🔴 **home club's trailing-20 runs ALLOWED** | **+0.511** |
| 🔴 **away STARTER's trailing-8 earned runs** | **+0.313** |
| away club's trailing-20 runs ALLOWED | +0.238 |
| home STARTER's trailing-8 earned runs | +0.121 |
| home club's trailing-20 runs SCORED | +0.056 |
| ⚠️ **away club's trailing-20 runs SCORED** | ⚠️ **+0.028 — effectively nothing** |

➡️ 🔴 **RUNS ALLOWED AND STARTER QUALITY CARRY ESSENTIALLY ALL OF IT. RUNS SCORED CARRIES ALMOST NOTHING — the two offence terms together are worth less than the weakest pitching term.** **Mechanically that is sensible: runs allowed proxies a pitching staff, which persists, while offensive output is noisier and more opponent-dependent.** ⚠️ **It is also a COEFFICIENT READING off a model that FAILED, so it is a description of this fit and NOT a pre-registered finding.** ⛔ **Do not promote it to one.**

### ⛔ WHAT THIS SAYS ABOUT T31c, STATED NOW SO IT IS NOT A SURPRISE LATER

🔴 **A model that cannot beat "add the two clubs' trailing runs scored" has no realistic prospect of beating a sportsbook's posted total.** ➡️ **The pre-registered expectation that T31c FAILS is now considerably stronger than when it was written.** ⛔ **T31c is NOT decided here and its counter is untouched — it needs 400 games and holds 55.** ⚠️ **But nobody should build toward it expecting a win.**

✅ **WHAT WOULD ACTUALLY BE WORTH TRYING, recorded as a DIRECTION and NOT as a specification** — ⛔ **it is not pre-registered, and writing a spec now, having seen these coefficients, would be shopping: the two terms that carried weight were PITCHING terms, and this project already has a FITTED PITCHER MODEL that was not used here at all. T31b used a crude trailing-8 earned-run average rather than `E[outs]` or `E[K]`.** ➡️ **Any successor must be pre-registered BEFORE it is fitted, on that basis, and it must beat T31b's 3.5309 on the same rows.**

---

## T32. 🆕 Phase 3, second attempt — does the ENVIRONMENT rescue a game-total model?

`[opened 2026-08-25, pre-registered BEFORE any fitting]` 🔴 ⛔ **STATUS: CLOSED-FAILED 2026-08-25 — BOTH ARMS FITTED, MEASURED, AND NEITHER CLEARED ITS BAR. T32a came in 0.0618 MAE WORSE than T31b (bar +0.05000). T32b gained +0.0302 over T32a (bar +0.05000). NOTHING SHIPPED.** ✅ **BUT THE TEST SUCCEEDED AT WHAT A TEST IS FOR: it separated the two new inputs that carry real signal from the two that carry none.** ⛔ **THE SPECIFICATION, THE PASS BARS AND THE FORBIDDEN LISTS BELOW ARE UNCHANGED — the result is recorded BENEATH them.**

🔴 **THIS IS A REOPENING ON NEW INPUTS, NOT A NEW SPECIFICATION ON THE OLD ONES — the same standard T30 had to meet after T27/T28/T29.** **T31 failed at `corr(predicted, actual) = +0.0799` on trailing team runs and a crude trailing-8 earned-run average.** ➡️ **The honest diagnosis was never that the model was wrong; it is that the inputs were the weakest set available, and the things that physically move a run total were not in the stack.** ✅ **Three of them now are.**

### ✅ WHAT ARRIVED 2026-08-25, AFTER T31 CLOSED

| Input | How | Why it should matter |
|---|---|---|
| **PARK** | `venue` was in the schedule response all along; the `scores` backfill requested a narrow field list and dropped it. Schema 2 captures it. | **Coors against Petco is worth roughly two runs on a total** — the largest cheap input a total model can have |
| **TEMPERATURE and WIND** | 🆕 `collect.py` mode `weather` — venue coordinates from statsapi, history from Open-Meteo's free archive | **Air density and wind are the classical drivers of run scoring** |
| **DAY / NIGHT** | `dayNight`, same dropped field list | A real and long-documented run-environment split |

**COVERAGE, measured before this specification was written:** **4,578 readings across 57 venues; temperature 27–112°F (mean 75.4), wind 0.1–22.2 mph (mean 6.8), direction spanning the full compass; 1,971 of 1,973 regular-season games — 99.9% — carry a reading at their game hour.** ✅ **Validity check passed: monthly mean temperature runs 63.5°F in April to 82.7°F in July, with March reading warm because spring training is in Arizona and Florida.** ✅ **And `gameType == 'R'` returns EXACTLY 1,973 games, matching the opening-day filter T31 derived independently from the hitter logs — two different methods agreeing on the same population.**

### ⛔ WIND DIRECTION IS DELIBERATELY EXCLUDED, AND THE REASON IS RECORDED BEFORE FITTING

🔴 **Wind direction is stored but is NOT a feature.** **A bearing is meaningless without the park's orientation — 90° at Wrigley is blowing out; 90° at Fenway is not — and this project holds NO park-orientation table.** ⛔ **Inventing one, or letting a model learn 34 park-specific direction interactions from 1,973 games, would be fabrication dressed as a feature.** ➡️ **WIND SPEED enters; DIRECTION does not.** ⚠️ **If an orientation source is ever added, that is a NEW test, not an amendment to this one.**

### ⚠️ THE PARK FACTOR MUST BE POINT-IN-TIME, AND THAT IS THE EASIEST THING HERE TO GET WRONG

🔴 **A park factor computed over the whole season and then used to predict games inside that season is LOOKAHEAD** — the same error already struck twice in this register, for T22's season-long role label and T24's durability label. ✅ **The factor is therefore the mean total at that venue over games played STRICTLY BEFORE the row, minus the league mean to that point, and a venue with fewer than 10 prior games contributes 0.0 rather than a noisy estimate.**

**THE SPECIFICATION — FIXED NOW, BEFORE ANY REGRESSION IS RUN:**

| | |
|---|---|
| **Target** | **Combined runs**, exactly as T31 — deliberately unchanged so the marginal value of the new inputs is isolated rather than confounded with a target change |
| **Sample** | `gameType == 'R'`, both clubs among the 30 derived MLB teams, 20+ prior games for both clubs, **both starters resolved with 5+ prior starts** — i.e. **T31b's sample exactly**, so the comparison is like-for-like |
| **T32a features (T31b's SIX plus EXACTLY FOUR)** | away/home trailing-20 runs scored and allowed · both starters' trailing-8 earned runs · 🆕 **point-in-time park factor** · 🆕 **temperature °F** · 🆕 **wind speed mph** · 🆕 **night (binary)** |
| **T32b features** | T32a's ten **plus EXACTLY FOUR:** each starter's **trailing-8 mean OUTS** and **trailing-8 mean K** — the v4.0 pitcher model's own two predictors, which Phase 3 has never used |
| **Model** | OLS. **ONE SPECIFICATION PER ARM.** |
| **Split** | **CHRONOLOGICAL**, train before **2026-07-15** — the same split as T27–T31 |
| **Pass (T32a)** | Beats **T31b's held-out MAE by >= 0.05 runs, scored on the SAME rows** |
| **Pass (T32b)** | Beats **T32a by >= 0.05 runs, on the SAME rows** |
| **Fail** | Anything less. **Record FAILED and ship nothing.** |
| ⛔ **Forbidden** | Adding a feature, changing a window, moving the split, re-cutting the sample, adding wind direction, or switching from OLS **after seeing a result** |
| ⛔ **Forbidden** | 🔴 **Using the market's posted total, or any market-derived quantity, as a feature — carried forward from T31 and unchanged.** |

🔴 **AND THE BAR THAT ACTUALLY MATTERS IS STILL T31c, WHICH IS STILL 55 / 400 GAMES.** ⛔ **T32a and T32b are SANITY GATES exactly as T31a and T31b were. Passing them does NOT put a total on the board.** ⚠️ **A model that beats a naive baseline is not a model that beats a sportsbook.**

⚠️ **THE HONEST PRIOR, WRITTEN DOWN BEFORE THE RESULT: park and weather are large, real, physically-grounded effects and SHOULD move MAE — but T31 showed the outcome is dominated by same-day variance, and no amount of environmental context changes how much of a single game is simply noise.** ➡️ **Expect a real improvement and a still-unbettable model. If that is what happens, it is a finding and not a disappointment.**

### 🔴 `[measured 2026-08-25]` RESULT — **T32a FAILED. T32b FAILED. And the test earned its keep anyway.**

**Sample: 1,027 rows — 647 train / 380 test — T31b's sample less one game with no weather reading. All arms scored on the SAME 380 held-out rows.**

| Estimator | MAE | RMSE |
|---|---|---|
| baseline — team trailing | 3.5750 | 4.5425 |
| baseline — league mean | 3.5888 | 4.4159 |
| ✅ **T31b — six features (the reference)** | 🔴 **3.5269** | **4.3680** |
| **T32a — plus park, temp, wind, night** | **3.5886** | 4.3929 |
| **T32b — plus starter outs and K** | **3.5585** | 4.3769 |

**T32a vs T31b: −0.0618 MAE.** **T32b vs T32a: +0.0302.** ⛔ **Both FAIL, and T32a is WORSE than the model it was meant to improve.**

### ✅ 🔴 THE RESULT WORTH KEEPING: TWO OF THE FOUR NEW INPUTS ARE REAL AND TWO ARE NOTHING

**Correlation with the outcome, measured independently of any fit:**

| New input | corr with combined runs | verdict |
|---|---|---|
| 🔴 **PARK factor** (point-in-time) | **+0.1363** | ✅ **REAL — and larger than anything T31 had** |
| 🔴 **TEMPERATURE** | **+0.0913** | ✅ **REAL** |
| ⚠️ **WIND SPEED** | **−0.0010** | ⛔ **NOTHING** |
| ⚠️ **DAY / NIGHT** | **−0.0113** | ⛔ **NOTHING** |

➡️ 🔴 **THE PHYSICAL PRIOR WAS HALF RIGHT, AND THE HALF THAT WAS WRONG IS WHY THE ARM FAILED.** **Park and temperature carry genuine signal — in T32a's fit they are the two LARGEST terms at +0.597 and +0.455 runs per standard deviation, bigger than any pitching or team-form term.** **Wind speed and day/night carry none.** ⛔ **Adding two pure-noise features to a 647-row fit costs more than the two real ones gain, and that is the whole failure in one sentence.**

⚠️ **AND WIND'S NULL IS NOT EVIDENCE THAT WIND DOES NOT MATTER.** **What was tested is wind SPEED with DIRECTION deliberately excluded, because this project holds no park-orientation table.** ➡️ **A 15 mph wind blowing out and a 15 mph wind blowing in are the same number here and physically opposite.** ⛔ **Report this as "wind SPEED alone is null", never as "wind is null."**

### ✅ THE MODEL SEES MORE THAN T31 DID, EVEN THOUGH IT SCORES WORSE

| | T31 | **T32a** |
|---|---|---|
| corr(predicted, actual) | +0.0799 | 🔴 **+0.1559** |
| predicted range | 7.79 – 10.80 | **7.33 – 12.51** |

➡️ **Correlation nearly DOUBLED and the model makes bolder predictions across a five-run span instead of three.** ⚠️ **MAE still got worse, because a bolder model that is not perfectly calibrated is punished by an error metric even while it tracks the outcome better.** ⛔ **This does NOT rescue the arm — the pre-registered bar was MAE and MAE says fail — but it is why the inputs are worth keeping.**

### ⚠️ CHECKED BEFORE RECORDING

- 🔴 **T32a IS OVERFITTING: in-sample MAE 3.5813 against T31b's 3.6296 — it fits the training set BETTER — while out-of-sample it is worse, 3.5886 against 3.5269.** **Ten features on 647 training rows.**
- 🔴 **A NONSENSE SIGN CONFIRMS THE INSTABILITY: `h_rs` reads −0.2497, meaning a home club that has been scoring MORE lately predicts FEWER total runs.** **That is physically impossible and is the classic signature of collinear features in a thin fit.**
- ✅ **THE PARK FACTOR IS GENUINELY POINT-IN-TIME, verified by HAND rather than asserted: one row's stored factor (+0.524796 on gamePk 823444, from 42 prior games at that venue) was re-derived directly from the raw score file and matched to six decimal places.** **The append happens after the computation, so a game can never contribute to its own park factor.**
- ⚠️ **The first attempt at this check was WEAK and is recorded as such: it looked for zero-valued factors among the earliest rows, but the sample starts a month into the season — by which point every park already has 10+ games — so it could not have discriminated. It was replaced with the hand recomputation above.**

### ➡️ A DIRECTION, EXPLICITLY NOT A SPECIFICATION

🔴 **The obvious next move is visible and must NOT be run without pre-registering it first: park and temperature ONLY, dropping wind and night, on the LARGER sample.** **T32 inherited T31b's starter requirement and paid 639 games for it — 1,027 rows instead of the 1,667 available without it.** ➡️ **Park and temperature need no starter join at all.** ⛔ **Writing that specification now, having seen which two inputs survived, is exactly the shopping this register exists to forbid.** ✅ **It must be registered BEFORE it is fitted, and it must beat T31b's 3.5269 on comparable rows.**

---

## T33. 🆕 Phase 3, third and final attempt — ELEVATION and a NON-LINEAR temperature term

`[opened 2026-08-25, pre-registered BEFORE any fitting]` 🔴 ⛔ **STATUS: CLOSED-FAILED 2026-08-25 — FITTED, MEASURED, AND IT FAILED BOTH MARGINS. Margin 1: −0.0363 MAE against the better baseline (bar +0.10000). Margin 2: −0.0322 against T31a on the same rows (bar +0.05000). IT IS WORSE THAN THE MODEL IT WAS MEANT TO IMPROVE. NOTHING SHIPPED.** 🔴 **THE PRE-COMMITTED CONSEQUENCE IS TRIGGERED: PHASE 3 IS CLOSED FOR THE SEASON.** ⛔ **THE SPECIFICATION, THE PASS BARS AND THE FORBIDDEN LIST BELOW ARE UNCHANGED — the result is recorded BENEATH them.**

🔴 **THE NEW CONTENT CAME FROM OUTSIDE THIS PROJECT'S DATA, WHICH IS WHAT MAKES IT A LEGITIMATE REOPENING.** **Sam supplied published sources on how weather affects hitting, and two mechanisms in them are inputs Phase 3 has never had.** ➡️ **They are THEORY-DRIVEN — derived from physics and outside measurement, NOT from staring at T32's residuals — and that distinction is the whole basis for opening this entry.**

**WHAT THE SOURCES ACTUALLY SAY** *(read 2026-08-25; a third link returned 403 and was not read)*:

| Claim | Source |
|---|---|
| The pathway is **AIR DENSITY** — warm air is less dense, the ball carries further | Scientific American |
| **A game 18°F above average has ~20% more home runs** | Scientific American, quoting a published study |
| The effect is **BROAD, not home-run-only** — runs, batting average and slugging all rise (HR 29–46%, hits/BA 5–11%) | AMS Headlines |
| 🔴 **A cold BALL has a lower coefficient of restitution** — it is not only the air | AMS Headlines |
| 🔴 **Fly balls travel 16 FEET LESS at ≤50°F than at ≥90°F** | AMS Headlines, quoting a study |
| Denver's humidor exists because of **altitude-driven air density** | Scientific American |

➡️ 🔴 **TWO CONSEQUENCES, AND BOTH ARE NEW MODEL CONTENT:**
1. **THE TEMPERATURE EFFECT IS PLAUSIBLY NON-LINEAR.** **A 50°F-versus-90°F framing with a cold-ball COR mechanism describes a COLD PENALTY, not a smooth slope.** **T31 and T32 both fitted temperature as a straight line.**
2. **ELEVATION IS THE PUREST AIR-DENSITY VARIABLE AND THE PROJECT NEVER STORED IT.** ✅ **Open-Meteo returns it on every response; a top-up pass added it 2026-08-25.**

✅ **AND THE BROAD-EFFECT FINDING SUPPORTS KEEPING THE TARGET AS COMBINED RUNS** rather than switching to home runs — the effect shows up across the whole offensive line, so the existing target is the right one and is NOT changed.

### ⚠️ WHAT IS DROPPED, AND THE HONEST ACCOUNTING FOR IT

🔴 **WIND SPEED AND DAY/NIGHT ARE DROPPED, AND THIS IS THE ONE PART OF T33 THAT IS DATA-DRIVEN RATHER THAN THEORY-DRIVEN. SAYING SO IS THE POINT.** **T32 measured them at corr −0.0010 and −0.0113 — nothing — and dropping them is a decision informed by that result.** ⛔ **THAT MAKES T33 A WEAKER PRE-REGISTRATION THAN T31 OR T32 IN EXACTLY THAT ONE RESPECT, and the weakness is recorded here rather than glossed.** ✅ **What is NOT weakened: elevation and the cold term were chosen from published physics before any T33 fit, and the bars below are carried over UNCHANGED from T31a rather than softened after a failure.**

⚠️ **WIND'S NULL REMAINS "WIND SPEED ALONE IS NULL."** **Direction is still stored and still unusable — Sam's orientation source turned out to be COMPASS-ROSE DIAGRAMS rather than bearings, so there is still no numeric park-orientation table.** ⛔ **Do not restate this as "wind is null."**

### ⚠️ ELEVATION AND PARK FACTOR ARE CORRELATED BY CONSTRUCTION — STATED BEFORE FITTING

🔴 **A point-in-time park factor ALREADY encodes most of what elevation does: Coors reads high because it IS high.** ➡️ **Elevation's marginal value is NOT that it adds a new effect — it is that it is EXACT AND KNOWN FROM DAY ONE, where the park factor is a noisy estimate that needs 10 games before it says anything at all.** ⚠️ **So the honest expectation is a SMALL elevation coefficient, mattering most where park history is thin.** ⛔ **If elevation comes back large, suspect collinearity before celebrating.**

**THE SPECIFICATION — FIXED NOW, BEFORE ANY REGRESSION IS RUN:**

| | |
|---|---|
| **Target** | **Combined runs** — unchanged from T31 and T32, deliberately |
| 🔴 **Sample — THE LARGER ONE** | `gameType == 'R'`, both clubs among the 30 derived MLB teams, **20+ prior games for both clubs**, weather present. ⛔ **NO STARTER REQUIREMENT** — T32 inherited it and paid 639 games for it, and none of T33's new inputs need a starter join |
| **Features (EXACTLY EIGHT, no others, no interactions)** | away/home trailing-20 runs **scored** and **allowed** (four) · 🆕 **point-in-time park factor** · 🆕 **temperature °F** · 🆕 **COLD indicator, `temp < 60°F`** · 🆕 **venue elevation, metres** |
| **The cold cut-point** | **60°F, fixed in advance.** ⛔ **NOT tuned.** ⚠️ **It is not the sources' 50°F either — 50°F is nearly absent from a regular MLB season, so a 50°F indicator would fire on almost nothing.** ➡️ **60°F is chosen to be a usable frequency, stated before it is counted, and NOT moved afterwards** |
| **Model** | OLS. **ONE SPECIFICATION.** |
| **Split** | **CHRONOLOGICAL**, train before **2026-07-15** — unchanged from T27–T32 |
| **Baselines, both reported** | league mean (point-in-time on training games) · team trailing (away runs scored + home runs scored) |
| **Pass — margin 1** | Beats the BETTER baseline on held-out **MAE by >= 0.10 runs** — 🔴 **the SAME bar T31a had and failed. It is NOT lowered after a failure** |
| **Pass — margin 2** | Beats **T31a's four team-form features, refitted and scored on these exact rows, by >= 0.05 MAE** — this isolates the FOUR NEW TERMS from the sample change |
| **Both margins, or it FAILS** | ⛔ **The T30 structure, for the T30 reason: beating a baseline while adding nothing over team form would mean the SAMPLE changed, not that the environment helped** |
| **Fail** | Anything less. **Record FAILED and ship nothing.** |
| ⛔ **Forbidden** | Adding a feature, moving the 60°F cut-point, changing a window, moving the split, re-adding wind or day/night, or switching from OLS **after seeing a result** |
| ⛔ **Forbidden** | **The market's posted total as a feature — carried forward from T31 and T32, unchanged** |

🔴 **AND THE BAR THAT MATTERS IS STILL T31c AT 55 / 400 GAMES. T33 IS A SANITY GATE, NOT A SHIPPING GATE.**

### 🔴 THE PRE-COMMITTED CONSEQUENCE, STATED BEFORE THE RESULT

⛔ **IF T33 FAILS, PHASE 3 CLOSES FOR THE SEASON.** **Three pre-registered specifications — team form, environment, and now physics-derived environment on the larger sample — would have failed to clear a bar against a NAIVE baseline, never mind against a sportsbook.** ➡️ **The Odds tab's totals stay 🔵 MARKET-only, and the reopening condition is a genuinely NEW INPUT — a numeric park-orientation table making wind direction usable, or captured market history reaching T31c's 400 games — NOT another specification.** ⚠️ **This is the same pre-commitment T29 made for hitters, and it is made here for the same reason: so the decision is not taken while disappointed.**

⚠️ **THE HONEST PRIOR: T32 already showed park and temperature carry real signal (corr +0.1363 and +0.0913) and that a game total is still dominated by same-day noise (corr(predicted, actual) +0.1559 at best). Expect the larger sample and the cleaner feature set to HELP, and still expect the +0.10 margin to be out of reach.**

### 🔴 `[measured 2026-08-25]` RESULT — **FAILED BOTH MARGINS**

**Sample 1,665 rows — 1,136 train / 529 test. Only 2 games lost to missing weather; the starter requirement is gone, so this is 638 games larger than T32's.**

| Estimator | MAE | RMSE |
|---|---|---|
| baseline — league mean 9.07 | 3.6406 | 4.4570 |
| ✅ **baseline — team trailing** | 🔴 **3.6227** | 4.5259 |
| T31a — four team-form features | 3.6268 | 4.4396 |
| **T33 — plus park, temp, cold, elevation** | **3.6590** | 4.4451 |

**Margin 1 vs the better baseline: −0.0363 (bar +0.10000). Margin 2 vs T31a on the same rows: −0.0322 (bar +0.05000).** ⛔ **BOTH FAIL, and T33 is WORSE than the four-feature model it was built to improve.**

### 🔴 MY OWN PRE-REGISTERED PREDICTION WAS WRONG, AND THE REAL PROBLEM WAS SOMEWHERE ELSE

**This entry predicted, before fitting:** *"elevation and park factor are correlated by construction… expect a SMALL elevation coefficient… if elevation comes back large, suspect collinearity before celebrating."*

⚠️ **ELEVATION CAME BACK LARGE — +0.501 runs per standard deviation — SO THE PREDICTION SAID TO SUSPECT COLLINEARITY. IT WAS CHECKED, AND THE PREDICTION WAS WRONG:**

| | |
|---|---|
| corr(park factor, elevation) | **+0.2414 — modest** |
| **VIF, elevation** | 🔴 **1.12 — essentially none** |

➡️ **Elevation is NOT redundant with the park factor and its coefficient is not an artifact.** ✅ **Recorded because the prediction was mine, it was specific, and it was wrong.**

🔴 **THE COLLINEARITY IS REAL BUT IT IS BETWEEN TWO OTHER TERMS, AND IT IS WHY THE ARM FAILED:**

| | |
|---|---|
| **corr(home club's runs ALLOWED, park factor)** | 🔴 **+0.4773** |
| corr(home club's runs SCORED, park factor) | +0.3330 |

**A club's runs-allowed average is INFLATED OR DEFLATED BY ITS OWN HOME PARK — half its games are played there. So an explicit park factor and a home club's runs allowed are substantially THE SAME FACT COUNTED TWICE.**

**What that did to the fit, per standard deviation:**

| Term | T31a | **T33** |
|---|---|---|
| home club's runs ALLOWED | **+0.445 — T31's LARGEST term** | 🔴 **+0.015 — annihilated** |
| home club's runs SCORED | +0.024 | 🔴 **−0.278 — nonsense sign** |

➡️ **Adding the park factor did not ADD information. It REDISTRIBUTED information the team-form terms already carried, destabilised the coefficients — a home club scoring more now predicts FEWER total runs — and cost accuracy out of sample.**

### ⛔ AND THE COLD TERM WAS NEVER ACTUALLY TESTED — A FLAW IN THE TEST DESIGN, NOT IN THE IDEA

| | |
|---|---|
| Cold games (`temp < 60°F`) in TRAIN | **165 of 1,136 — 14.5%** |
| 🔴 **Cold games in the HELD-OUT set** | 🔴 **2 of 529 — 0.4%** |

🔴 **A CHRONOLOGICAL SPLIT AT MID-JULY PUTS ALMOST EVERY COLD GAME IN THE TRAINING SET, BECAUSE COLD BASEBALL IS AN APRIL PHENOMENON.** **The cold term was fitted on 165 games and evaluated on TWO.** ⛔ **Its held-out contribution is not measurable, so this test says NOTHING about whether a cold penalty is real.**

⚠️ **THE SPLIT DATE IS NOT MOVED — it is shared with T27 through T32 and changing it after a failure is exactly what this register forbids.** ➡️ **But the limitation is recorded so nobody reads T33 as evidence against the cold-ball mechanism. It is evidence about nothing on that point.** ✅ **If a cold term is ever tested properly it needs a split that puts cold games on BOTH sides — a seasonally stratified or multi-year design — and that is a NEW pre-registration.**

### ⚠️ CHECKED BEFORE RECORDING

- 🔴 **T33 OVERFITS MORE THAN T31a: in-sample gain over the naive baseline +0.1891 against T31a's +0.1233, while out-of-sample it is −0.0363 against T31a's −0.0041.** **Eight features on 1,136 rows, and the extra four buy training fit and nothing else.**
- ⚠️ **corr(predicted, actual) = +0.1456, against T32a's +0.1559 and T31's +0.0799.** **The larger sample did not restore what T32a's ten features reached.**
- ✅ **The park factor's point-in-time construction is unchanged from T32, where it was verified by hand against the raw score file to six decimal places.**

### 🔴 THE PRE-COMMITTED CONSEQUENCE IS TRIGGERED — PHASE 3 IS CLOSED FOR THE SEASON

**T33's own pre-registration, written before the result was known, said: if it fails, Phase 3 closes.** **That condition is met.**

| Test | What it added | Margin vs its bar |
|---|---|---|
| **T31a** | four team-form features | −0.0054 vs +0.10 |
| **T31b** | + both starters | +0.0403 vs +0.05 |
| **T32a** | + park, temp, wind, night | −0.0618 vs +0.05 |
| **T32b** | + starter outs and K | +0.0302 vs +0.05 |
| **T33** | + park, temp, cold, elevation, larger sample | −0.0363 vs +0.10 |

🔴 **FIVE ARMS ACROSS THREE PRE-REGISTERED SPECIFICATIONS. NOT ONE CLEARED A BAR AGAINST A NAIVE BASELINE — never mind against a sportsbook.** ✅ **The Odds tab's totals stay 🔵 MARKET-only.** ⛔ **THE REOPENING CONDITION IS A GENUINELY NEW INPUT — a NUMERIC park-orientation table making wind direction usable, or captured market history reaching T31c's 400 games — NOT another specification.** ⚠️ **Sam's orientation source was checked on 2026-08-25 and turned out to be COMPASS-ROSE DIAGRAMS rather than bearings, so that door is still shut.**

### ✅ WHAT THE THREE FAILURES BOUGHT, WHICH IS NOT NOTHING

1. 🔴 **A GAME TOTAL IS MOSTLY NOISE.** **The best correlation any arm reached between prediction and outcome was +0.1559 — about 2% of variance — while real games run 1 to 27 runs.**
2. ✅ **PARK AND TEMPERATURE ARE REAL** (corr +0.1363 and +0.0913) **and WIND SPEED ALONE AND DAY/NIGHT ARE NOT** (−0.0010, −0.0113).
3. 🔴 **PARK FACTOR AND A HOME CLUB'S RUNS ALLOWED ARE SUBSTANTIALLY THE SAME VARIABLE** (+0.4773). **Anyone adding a park term to a team-form model is double-counting and should expect the coefficients to move, not improve.**
4. ✅ **ELEVATION IS NOT REDUNDANT WITH PARK FACTOR** (VIF 1.12) — **contradicting this entry's own prediction, which is why the prediction was written down.**
5. ⚠️ **A CHRONOLOGICAL MID-SEASON SPLIT CANNOT TEST A COLD-WEATHER TERM.** **A design lesson that applies to any future seasonal variable.**
6. ✅ **PERMANENT DATA THAT DID NOT EXIST ON THE MORNING OF 2026-08-25:** **1,973 clean regular-season games with real scores, park, day/night; 4,578 weather readings covering 99.9% of them; and elevations for 57 venues.** **None of it depends on Phase 3 succeeding, and all of it is the correct foundation for any future game-level question.**

---

## 🆕 `[measured 2026-08-24]` MEASURED FINDING — **NOT A TEST.** Home field is a PLAYING-TIME term for hitters, not a hitting term — and it runs against the OVER

⚠️ **THIS IS NOT A PRE-REGISTERED TEST AND IT DOES NOT GET A T-NUMBER.** **Nothing here was pre-registered: it is a DECOMPOSITION of a term that was already fitted inside T27, run to explain a coefficient that had already been recorded.** ⛔ **Do not cite it as a passed test, and do not let it become one retrospectively.**

**T27 read `home` as null-to-negative (z = −1.47), which is surprising when the same term is significant for pitchers in v4.0 (±0.151 K, t = 3.52).** Decomposed over all 37,541 played rows:

| | home | road | difference |
|---|---|---|---|
| **Plate appearances per game** | 3.693 | 3.840 | **−0.147, z = −12.6** |
| **Hits per plate appearance** | 0.21986 | 0.21576 | +0.0041, **z = +1.87** |
| P(1+ hit) | 57.30% | 57.60% | −0.30 pts, z = −0.6 |

➡️ **Per plate appearance a home hitter is, at most, marginally better — z = 1.87 is not significant. But he gets 0.147 FEWER plate appearances at overwhelming significance, because the home team does not bat in the ninth when it is winning.** **The playing-time effect is roughly seven times larger in z than the hitting effect and points the other way.** ⛔ **Never treat "home" as a hitting bonus on a hitter prop. On an over it is a mild NEGATIVE.**

⚠️ **This is why a term cannot be assumed to transfer across sides of the ball.** **It is real and large for pitchers and effectively absent — and inverted in mechanism — for hitters.**

---

## 🆕 `[measured 2026-08-24]` MEASURED FINDING — **NOT A TEST.** For TOTAL BASES, the opposing starter's STRIKEOUT rate matters more than his HITS-ALLOWED rate

⚠️ **THIS IS NOT A PRE-REGISTERED TEST AND IT DOES NOT GET A T-NUMBER.** **It is a COEFFICIENT READING off a model that was already fitted inside T29 — not a pre-registration.** ⛔ **Do not cite it as a passed test, and do not let it become one retrospectively.**

**In T29 the opposing starter's strikeout rate reads β −0.0746 at z = −3.44, while his hits-allowed rate reads β +0.0352 at z = 1.64 and is NOT significant.**

| The opposing starter's… | β (per SD) | z | verdict |
|---|---|---|---|
| **strikeouts per batter faced (PROXY)** | **−0.0746** | **−3.44** | ✅ **real, and the larger of the two** |
| hits allowed per batter faced (PROXY) | +0.0352 | 1.64 | ⚠️ **NOT SIGNIFICANT** |

➡️ **A ball that is never put in play cannot become a total base**, and the strikeout term is both larger and the only one of the two that clears significance.

⚠️ **BOTH ARE PROXIES — the pitcher log carries `hit`, `bb`, `k`, `bf`, `outs`, `er`, `np` and NO extra-base detail, so a true total-bases-allowed rate CANNOT be computed.** ⛔ **Do not describe either as one.**

➡️ **PRACTICAL READ: on a hitter's over-1.5 total bases, WHO IS PITCHING matters mainly through his STRIKEOUT RATE, not through how many hits he gives up.**

---

## T34 / T34b / T35. 🆕 ⛔ **CLOSED-FAILED (T34b, T35) and CLOSED-PASSED (T34, three markets)** — what distribution may turn a hitter's RATE into a PROJECTION?

**Opened and closed 2026-08-26.** **Sam asked for projections beside the lines, covers-style, and said the requirement in his own words: _"it need to be an accurate projection of what the model thinks the players outcome will be, it should go hand in hand with the confidence score."_**

🔴 **THE PITCHER SIDE NEEDED NO TEST AND DID NOT GET ONE.** **A pitcher row already assumes a distribution — Poisson on strikeouts, Normal(mu, cvO × season mean outs) on outs — so the projection is obtained by INVERSION: solve for the central value that reproduces the probability the row already displays. It is the same estimate in different units, exact to 1e-10, and it CANNOT contradict the pick.** ✅ **Validated on the four published cards: mean gap to the model's own `E[K]` +0.073 K (max 1.04, none ≥ 2); on outs, +0.355 outs (max 3.99, one ≥ 1 inning).**

⚠️ **A HITTER ROW HAS NO MODEL, SO NOTHING SUPPLIES A DISTRIBUTION.** **That is what T34 tested, and it is the only reason a test was needed at all.**

### The bar, fixed BEFORE any fit
**Per market, the implied central value must reproduce the player's own observed per-game mean:** **|mean(implied − observed)| < 0.10 units AND p90 |implied − observed| < 0.25 units.** **Sample: every hitter with ≥ 25 STARTED games (`pa ≥ 3` fallback, per `CLAUDE.md`), at every line the book posts.**

### 🔴 `[measured 2026-08-26]` RESULT

| market | n | Poisson mean / p90 | NegBin mean / p90 | ships |
|---|---|---|---|---|
| hits | 1058 | +0.0142 / **0.202** | +0.0146 / 0.198 | ✅ **Poisson** |
| home runs | 377 | +0.0056 / **0.022** | +0.0055 / 0.016 | ✅ **Poisson** |
| RBIs | 977 | +0.0547 / 0.299 ⛔ | +0.0174 / **0.117** | ✅ **NegBin** |
| total bases | 1628 | −0.0162 / 0.673 ⛔ | +0.0329 / 0.350 ⛔ | ⛔ **NOTHING** |
| H+R+RBI | 1654 | −0.1192 / 0.696 ⛔ | +0.0138 / 0.356 ⛔ | ⛔ **NOTHING** |

**T34b — project the OBSERVED MEAN directly, for the two markets with nothing.** **Bar fixed before the run: the mean lands on the picked side of the line in ≥ 97% of rows whose displayed rate is ≥ 60%.** ⛔ **total bases 1318/1386 = 95.09% FAIL · H+R+RBI 1239/1278 = 96.95% FAIL.** 🔴 **All 107 misses were UNDERS, as predicted.** ⚠️ **H+R+RBI missed by 0.05 points and the bar did not move — that is the entire reason for fixing it first.**

**T35 — compound Poisson for total bases**, registered before running: TB is not a count but a SUM, `1B + 2×2B + 3×3B + 4×HR`, and the count underneath it (HITS) passed T34 cleanly. So: hits ~ Poisson, each hit drawing its base value from the player's OWN observed extra-base mix. ⛔ **n=1628, mean +0.0335, p90 0.287 — FAIL.**

➡️ **PROGRESSION ON ONE STATISTIC: plain Poisson 0.673 → negative binomial 0.350 → compound Poisson 0.287, against a bar of 0.25.** ✅ **The mechanism was right — modelling TB as a sum over hits more than halved the error — and it still did not clear.**

### 🔴 MY PRE-REGISTERED PREDICTION WAS WRONG, AND IN THE MORE USEFUL DIRECTION
**This entry predicted, before fitting:** *"Total bases FAILS, biased HIGH, by roughly +0.2 to +0.4 bases."* ⛔ **IT IS NOT BIASED AT ALL — Poisson's mean error on TB is −0.016, the second-smallest of the five markets. It fails on SPREAD.** ➡️ **That is the WORSE of the two failures: a consistent bias can be subtracted; an unbiased estimator that is wrong by two-thirds of a base on one row in ten cannot be, and it would print a precise-looking wrong number.** ⚠️ **I also predicted RBIs would pass under Poisson. They failed at 0.299 and needed the negative binomial — RBI is lumpier than its mean suggests, because a three-run homer is one swing.**

### What ships, and the pre-commitment
✅ **Hits and home runs invert a Poisson; RBIs invert a negative binomial holding the player's own game-to-game variance, computed POINT-IN-TIME from the hitter log.** 🔴 **All three are labelled `DESCRIPTIVE`, never `MODEL` — ledger rule 55 binds, because the rate they invert is the player's own record and T27/T28/T29 all failed.** ⛔ **Total bases and Hits+Runs+RBIs carry NO PROJECTION AT ALL, and the page states the absence and the reason.** ⛔ **THREE ATTEMPTS HAVE FAILED ON TOTAL BASES. A FOURTH DOES NOT GET AN EASIER BAR — it gets a NEW pre-registration at the SAME 0.25.** ⚠️ **This is the same pre-commitment T29 made for hitter modelling and T33 made for Phase 3, made here for the same reason: so the decision is not taken while disappointed.**

### Enforcement in code
✅ **`verify_card.py` grew from 33 to 46 checks.** **The one that matters is a ROUND TRIP: push the printed projection back through the row's own distribution with a SECOND implementation (`math.factorial` series / `lgamma`, never `card.project()`) and the row's own confidence must come back out — worst observed 0.70 pts on pitchers, 3.13 on hitters, both pure one-decimal rounding.** ✅ **Six faults were INJECTED into a real card and all six were caught: a projection nudged 1.5 K, a confident pick flipped to the wrong side, a hitter row relabelled `MODEL`, a projection added to a BARRED market, a stripped unit, and a nudged hitter projection.** ⚠️ **The point-in-time check is written as a DIFFERENCE — recompute each RBI projection with the date filter and without it, and the card must match the filtered one — because asserting "the filter exists" would prove nothing. It reported **0 separable rows** on the test slate and says so in its own name.**

---

# 📋 DOC DEBT — specific edits owed, with the exact change named

**Not tests. Known-stale lines in docs.** ⛔ **Do not mark one done without re-reading the doc in the same turn (rule 37).**

| Doc | The stale line | The edit owed |
|---|---|---|
| ✅ `claude/mlb-projection-model.md` | all three edits | ✅ **DONE 8/21.** 🔴 **VERIFIED: all 247 numeric tokens checked against an independent copy.** ⚠️ Two hard-coded `4.735`s remain by deliberate choice — history, not instructions. |
| ✅ `claude/today-shortlist.md` | the 8/20 card, results pending, a **2.45x** pair described as *"clears 1.8x"* | ✅ **Rewritten 8/21** — closed, graded, pair marked outside the band. |
| ✅ `claude/mlb-data-stack.md` | timing, count, ten missing findings | ✅ **DONE 8/21.** ✅ 🆕 **AND THE 7:30am ITEM IS CLOSED TOO — VERIFIED AT THE SOURCE 8/21 late, in the same turn (rule 37).** ~~⏳ ONE NEW ITEM OWED: the scalar-corruption qualification, the `1.3 IP` case and the `people?personIds=...&hydrate=stats(...)` 403~~ — **all three are in the doc**: the flat-game-log claim is marked **QUALIFIED** in the headless-grading section, the **`1.3 IP`** case has its own banner, and the control-endpoint **403 is lie mode 4**. 🆕 **A further correction landed the same turn: the archived `starts_h.csv` count was STRUCK from 1,517 to 1,499** — 60 team-hand blocks, 59×25 plus `COL,L` at 24, span 2026-04-03 → 2026-08-18, **39.1% of the 3,838-start table**; see `claude/data-starts-h.csv.md`. |
| ✅ `claude/card-blueprint.md` · `claude/mlb-alt-line-protocol.md` · `claude/mlb-data-stack.md` | all three asserted **"Hard Rock alt ladders are OVERS ONLY"** | 🔴 **FALSE — struck 8/21.** ✅ **"No alternate OUTS market on Hard Rock" survives, marked Sam-confirmed.** |
| ✅ `claude/card-blueprint.md` | the card template logged **only the blend** | ✅ **DONE — verified in place 8/21 evening (rule 37).** STEP 7 carries *"LOG `model` AND `raw` AS THEIR OWN COLUMNS IN THE LEDGER, NOT JUST THE BLEND"*, and the 8/21 card is the first logged under it. **Ledger rule 41 / this DOC DEBT item is CLOSED.** |
| ✅ `claude/mlb-alt-line-protocol.md` | **seven** contradictions | ✅ **DONE 8/21 — the worst doc in the project.** ~~⚠️ 🆕 **Note: it uses its own rules 40 and 41, which now collide with ledger rules 40 and 41.**~~ 🔴 **STRUCK 8/21 evening — THE COLLISION NO LONGER EXISTS.** ✅ **Re-read at the source in the same turn (rule 37): `claude/mlb-alt-line-protocol.md` NUMBERS NO RULES OF ITS OWN.** **It uses `CORRECTION 1`–`CORRECTION 4` for its own material and cites ledger rules by name and number — "ledger rule 46", "ledger rule 47", "ledger rule 48", "LEDGER RULE 51".** **The rival numbering was removed when that doc was rewritten clean.** ✅ **THE HABIT IS KEPT AND IS THE PART THAT WAS ALWAYS RIGHT: cite the DOC when citing a rule, never a bare number.** |
| ✅ `claude/v4-refit-supersessions.md` | itself stale, and now **DELETED** | ✅ **CLOSED 8/21.** The file is gone from the project — verified against the doc list. **Its two irreplaceable pieces were rescued into `claude/backtest-results.md` FIRST**: the `🧭 WHERE TO LOOK` authority table (with the last row's missing `claude/` prefix corrected on the way in) and the `JUDGMENT CALLS THE REFIT LATER CONFIRMED` section. ⚠️ **Nothing was lost.** ⛔ **Do not recreate it** — it was scaffolding for the v4.0 sweep, that sweep is finished, and a "what is still stale" doc that outlives its list becomes the staleness. |
| ⏳ 🔴 **RE-OPENED** — `claude/mlb-team-advanced.md` · `claude/times-through-order.md` · `claude/backtest-weather-homeaway.md` · `claude/backtest-results.md` · `claude/pitcher-reliability.md` · `claude/pitcher-tier-finding.md` · `claude/opponent-metric-bug.md` | ~~swept 8/21 — ✅ **DONE**~~ | 🔴 **THE "DONE" IS STALE AND IS STRUCK. A SECOND SWEEP ON 2026-08-21 EVENING FOUND FOUR MORE CLASSES OF DEFECT IN THOSE SAME DOCS:** **(a)** 🔴 **A FALSE CLAIM OF FULL-SEASON VERIFICATION** — `claude/pitcher-tier-finding.md` asserted *"still the verdict on the full season: sub-.500 opponent is null"* when **team record has NEVER been re-run on the full sample.** **Struck and restated as an UNCONFIRMED NULL carried forward from the 40% log**; the "never substitute record for meanK" prohibition was kept and made independent of the null. **(b)** 🔴 **TWO LIVE CARD INSTRUCTIONS WHOSE DERIVATIONS HAD BEEN STRUCK** — `claude/times-through-order.md`'s *"do not target LAA or TOR on their season number alone"* reads off the `season meanK` column **that same page retires** (now **SUSPENDED**, re-anchored to rank off `claude/mlb-opponent-database.md`), and `claude/pitcher-tier-finding.md`'s "Sam's spot" filter runs on a cut-point struck as retired-scale. **(c)** ⚠️ **A DOC WHOSE HEADER DISCLAIMS BEING LIVE WHILE ISSUING A LIVE VERDICT** — `claude/mlb-team-advanced.md` says *"This table is `[descriptive]`. None of it is a model input"* and then flips a lineup from "neutral K environment" to "a K-over FADE" and reverses an ordering. **(d)** 🔴 **FIVE COUNT ERRORS** across those docs, each corrected against the rows beneath it (ledger rule 45). ➡️ 🔴 **THE LESSON, AND IT IS WHY THIS ROW IS RE-OPENED RATHER THAN AMENDED: `✅ DONE` ON A SWEEP ROW MEANS "SWEPT ON THAT DATE." IT NEVER MEANS "VERIFIED CORRECT."** ⛔ **Do not close this row again with a bare ✅.** |
| ✅ 🔴 **CLOSED 2026-08-22** — `claude/pick-ledger.md` | *"Table B's 4-1 is tracked separately"* — the referent was missing from the ledger | ✅ 🔴 **THE IDENTIFICATION HAPPENED. IT WAS NOT GUESSED — IT CAME FROM PRIMARY EVIDENCE.** ~~"The likeliest referent is Sam's own **4/5**, now TABLE C."~~ ⛔ **That guess is STRUCK and was wrong.** **The superseded 7:30am task prompt — read out of `list_triggers` before it was rewritten — specifies** *"TABLE A = 9 live plays, TABLE B = 5 midday plays tagged `[pre-correction]`. Expect 14 rows graded, 9 entering calibration."* ➡️ **TABLE B was the 8/19 MIDDAY card: 5 plays, `[pre-correction]`, graded 4/5, excluded from calibration by design.** ✅ **It now carries a 📇 TABLE INDEX row marked LOST, and the HIT RATE section records it as a data-loss event with what it was and what is gone.** 🔴 **The five play rows themselves are GONE and ⛔ will NOT be reconstructed from memory.** ✅ 🔴 🆕 **CLOSED 2026-08-22 — SAM CLOSED IT EXPLICITLY: *"close it"*.** ~~⏳ **WHAT REMAINS OPEN IS ONLY WHETHER TO CLOSE THE ITEM FORMALLY, AND THAT IS SAM'S CALL**~~ — **he has now made it.** **WHAT IS RECORDED AT CLOSURE, ALL FOUR FACTS:** **(1)** the referent was identified from **PRIMARY EVIDENCE** — the superseded 7:30am task prompt — as the **8/19 MIDDAY card: 5 plays, `[pre-correction]`, graded 4/5, excluded from calibration by design**; **(2)** 🔴 **the five play rows are PERMANENTLY LOST and WILL NOT be reconstructed**; **(3)** ✅ **every total in the ledger reconciles WITHOUT them**; **(4)** **Sam closed it explicitly on 2026-08-22.** ⛔ **THE DATA-LOSS RECORD ITSELF IS NOT DELETED** — it stays in the ledger's HIT RATE section permanently, because it is the evidence behind ledger rules 42, 43 and 44. ⛔ **CLOSED MEANS CLOSED: this is not to be re-opened, re-derived or re-litigated by a future session.** ⚠️ **The ledger's own TABLE B blocks and its 📇 TABLE INDEX row were checked in the same turn and now read CLOSED rather than open; the wording that invited re-litigation was removed from each.** |
| ✅ Sam's Project Instructions box | said *"the standing rules, currently 36"* | ✅ **FIXED BY SAM 8/21 — verified in `project_info`.** The count is gone; the line now reads "the standing rules." ⛔ **NEVER PUT A COUNT ANYWHERE YOU CANNOT EDIT.** It was written as `36`, was wrong within hours, and only Sam could repair it. **The same mistake was made twice in one day — the other copy was in a scheduled-task prompt.** ➡️ **Applies to rule counts, doc counts, start counts and test counts alike: name the doc, never the tally.** |

| ⏳ 🆕 `claude/backtest-weather-homeaway.md` | the Method line's **`481 usable point-in-time observations`** | 🔴 **UNRECONCILABLE AGAINST ITS OWN ROWS. ⛔ IT MUST NOT BE RE-ADOPTED AS A SAMPLE SIZE.** **RESULT 2's roof/open split reads `ROOF (n=313)` + `OPEN (n=932)` = 1,245** — **two and a half times the stated 481.** ⛔ **Neither figure is adopted and neither is deleted; `481` is marked UNVERIFIED in the doc.** ⚠️ **It CANNOT be repaired by re-running:** the join ran on `claude/data-starts-h.csv.md`, **restoring that file is forbidden**, and the two figures may simply come from different filter passes — **but that is a guess and is not written down as a finding.** ➡️ **The only real repair is T13a's full-sample re-run.** ⛔ **Until then, quote RESULT 2's own row counts and never the prose `481`.** |
| ⏳ 🆕 `claude/times-through-order.md` | the **`season meanK` column**, and card instruction 2 | 🔴 **THE COLUMN IS ON THE RETIRED StatMuse SCALE THROUGHOUT (league mean 5.01), every value an Aug 19–20 copy.** **The live statsapi metric has a materially lower league mean and RE-ORDERS teams — it is not a shift, so a read taken off that column must be RE-DERIVED, NOT RE-VALUED.** 🔴 **CONSEQUENCE: THE LAA/TOR CARD INSTRUCTION THAT DEPENDED ON IT IS *SUSPENDED*.** *"Do not target LAA or TOR for strikeouts on their season number alone"* rests on LAA's **5.91**, a retired-scale number, so the entire premise of the trap may not survive re-derivation. ⛔ **A live card instruction may not read off a column its own page says not to read.** ✅ **THE ONLY FORM THAT MAY BE USED: read the lineup's CURRENT rank off `claude/mlb-opponent-database.md`, then use this doc's LATE K% column as a flag to look harder — never as an adjustment.** ⛔ **The two-name list is not restored until the full-season TTO collection lands (T8).** |
| ⏳ 🆕 `claude/pitcher-tier-finding.md` | **"Sam's spot"** — a MIXED arm vs a sub-.500 team with opponent meanK **≥ 5.20** | 🔴 **IT HAS A DESCRIPTION AND NO EXECUTABLE DEFINITION.** `[measured]` **the spot averages 5.90 K against 4.97 for other MIXED starts** — but **the 5.20 cut-point is on the RETIRED StatMuse scale**, the live metric **re-orders** lineups so 5.20 does not select the same teams, and **NO replacement cut-point has been derived on the live metric.** ⛔ **Do not filter on 5.20 and DO NOT TRANSLATE IT** — the translation that used to sit under it (`4.93` / `4.86`) was struck for exactly that, having been built from a centering constant copied out of another doc that then moved. ⚠️ **The "sub-.500" half of the filter is the unconfirmed team-record null (T13a).** ➡️ **Take the tough-lineup tail by RANK off `claude/mlb-opponent-database.md`, and re-derive the cut-point empirically at the monthly re-fit.** ⛔ **Until a live cut-point exists the spot may not be filtered on at all.** |
| ⏳ 🆕 `claude/backtest-hits-allowed.md` | **`16.18`** — mean outs per start, inside the shipped Poisson hits recipe | 🔴 **A RETIRED 40%-LOG CONSTANT STILL SITTING IN A LIVE FORMULA.** Its sibling `4.97` was struck the same day and replaced with full-season constants — **`E[H] = 0.2232 × E[BF]`, `E[BF] = 22.4 × (expected outs / mean outs)`, both from RESULT 6 on n=2,819** — but **`16.18` was flagged rather than guessed at and is STILL un-replaced.** ➡️ **RE-DERIVE IT ON THE FULL SEASON OR RETIRE IT.** ⛔ **Do not invent a replacement.** ✅ **Interim rule, already on the page and repeated here so it is not lost: scale off the mean outs of whatever start table is actually in hand, and SAY WHICH TABLE IT WAS.** ⚠️ **And the recipe is UNTESTED in either form — flag any hits play that uses it.** |
| ⏳ 🆕 `claude/mlb-data-stack.md` — **THE RECIPE's working dataset** | **`pitchHand` is not a field in the pull at all** | 🔴 **HANDEDNESS IS NOT IN THE WORKING DATASET.** `[measured 2026-08-22]` **It had to be fetched LIVE from `people?personIds=…&fields=people,id,fullName,pitchHand,code` to answer one handedness question, which is a second round-trip for a field that costs nothing to carry.** ➡️ **ADD `pitchHand` TO THE PULL** so handedness splits are available without an extra fetch. ⚠️ 🔴 **THE 2026-08-22 FINDING IT PRODUCED IS RECORDED HERE WITH ITS LABEL ATTACHED, NOT AS A RESULT: comparable RIGHT-handers vs the White Sox went 13/13 at 4+ K while LEFT-handers went 6/9 — every miss in the pool was a lefty.** ⛔ **POST-HOC, NOT PRE-REGISTERED — the split was made after Sam named the axis, which is specification shopping unless it is labelled.** ⚠️ **n=13.** ⚠️ **And T21's shrinkage applies exactly: a perfect record on 9+ prior observations delivers ~89%, not 100%.** ⛔ **Do not cite 13/13 as 100%, and do not promote this cut to a finding.** |
| ⏳ 🆕 **ODDS ARE NOT STORED ANYWHERE — no schema, no file, no table** | there is no odds store of any kind in this project | 🔴 **LINE MOVEMENT, T25 AND ANY CLOSING-LINE-VALUE WORK ALL DEPEND ON A STORE THAT DOES NOT EXIST.** **Every pull this project has ever made was read, used once and discarded.** ⛔ **This is why LINE VALUE reads `n = 0` and why T25 cannot be backfilled — historical odds are a separate, more expensive API product.** ➡️ **The edit owed is a decision and a build, not a wording fix: a per-pull store keyed by (date, event id, book, market, outcome, pulled-at minute), written on every pull. It is a Phase-1 item in `claude/gizmos-picks-spec.md`.** ⚠️ **Until it exists, say `n=0` rather than substituting a base rate for a captured price.** |
| ⏳ 🆕 `claude/mlb-opponent-database.md` — **THERE ARE NOW TWO COPIES OF THIS METRIC AND THEY HAVE DIFFERENT CENTERING CONSTANTS** | the published table is the only copy the docs describe | 🔴 **AS OF 2026-08-23 A SECOND, NIGHTLY, MACHINE-REBUILT COPY OF THE OPPONENT METRIC LIVES IN THE GITHUB ACTIONS RUNNER, rebuilt from the same pull the model reads, with its centering constant taken from that same rebuild.** **Why it exists: the published table can only be rebuilt in an INTERACTIVE BROWSER SESSION (THE RECIPE needs Claude in Chrome), so it goes stale a slate at a time — it was already one slate short on 8/22 — and the runner's rebuild is self-healing.** `[measured 2026-08-23 against the published table]` **pool of 3,802 IP-filtered starts (~99% of the season); mean \|ΔE[K]\| difference 0.021 K, max 0.064 K — inside the ~0.045 K the opponent doc itself quotes as the cost of a one-slate lag.** ⛔ 🔴 **THE TWO CONSTANTS MUST NEVER BE MIXED: the published table records 4.7376 and the runner computed 4.7756 on the 8/23 pull, on a slightly different population.** **A meanK on one scale centred on a constant from another is this project's OLDEST DOCUMENTED BUG** (`claude/opponent-metric-bug.md`). ✅ **The property that actually matters is not the size of the gap — it is that the VARIABLE AND ITS CONSTANT COME FROM THE SAME PULL.** ⛔ **THIS DOES NOT RETIRE THE PUBLISHED TABLE and does not change the constant recorded there.** ➡️ **The edit owed: state in `claude/mlb-opponent-database.md` that a second machine-rebuilt copy exists, name both constants, and forbid mixing them.** ✅ 🔴 **DONE 2026-08-23, 7:30am run — VERIFIED IN PLACE IN THE SAME TURN (ledger rule 37).** **That doc now carries a section naming BOTH constants (4.7376 published / 4.7756 on the runner's 8/23 pull), both populations (3,838 starts complete through 8/20 / 3,802 IP-filtered), the measured agreement (mean \|Δ E[K]\| 0.021 K, max 0.064 K), and an explicit prohibition on computing across them.** ⛔ **It also states that this does NOT retire the published table and is NOT a reason to skip the daily verification. ROW CLOSED.** |
| ⏳ 🆕 🔴🔴 **`claude/pick-ledger.md` LOSES WHOLE GRADING RUNS TO CONCURRENT WRITES — FOURTH OCCURRENCE, AND THE FIRST REPEAT** | the standing divergence check reads `project_info`'s `created_at` and treats a NEWER ledger as a ledger that carries the newer RECORD | 🔴 **IT DOES NOT, AND 2026-09-18 IS THE PROOF.** `[measured 2026-09-18]` **The ledger's `created_at` was `2026-09-17T12:19:36Z` against `claude/calibration-accumulators.md`'s `2026-09-17T11:50:58Z` — NEWER by half an hour — and it was missing the 2026-09-15 AND 2026-09-16 grading blocks that the accumulators page recorded as written.** **Its newest Changelog entry is an INTERACTIVE football/dossier entry dated `Sep 17 2026, midday`, so a session wrote it last from a base that predated the grading run's write.** ⛔ **The 9/15 block had ALREADY been restored once, on 9/17, and was lost AGAIN — the first repeat in four occurrences (9/11, 9/12, 9/15, 9/15+9/16).** ➡️ **THE EDIT OWED IS NOT A WORDING FIX. An INTERACTIVE session must decide how a concurrent write is prevented rather than detected** — candidates named and NOT chosen here: a grading-run write that appends to a DATED, WRITE-ONCE companion doc rather than rewriting the ledger (ledger rule 285's shape, one level up); or a mandatory pre-write check that the base contains the previous slate's dated block BY NAME, which this run performed manually and which detects the loss without preventing it. ⛔ **A grading run can re-derive the lost blocks from source and does, every time — that is recovery, not a fix.** |

### 🔴 A SCHEDULED TASK CANNOT REPAIR A SCHEDULED TASK — WHICH CHANGES WHAT THIS REGISTER IS FOR

🔴 **`update_trigger` REQUIRES HUMAN APPROVAL (`MCP tool call requires approval`) AND AN UNATTENDED RUN HAS NOBODY TO GIVE IT.** **Measured 2026-08-24, Monday sweep: the call was made, it was refused, and both stored prompts were afterwards re-read and byte-compared against their originals — UNCHANGED.** ➡️ **EVERY “check every trigger” TRIPWIRE IN THIS PROJECT IS REPORT-ONLY FROM AN UNATTENDED RUN.** ⛔ **A scheduled run may NEVER record a task-prompt fix as done — it cannot make one.** ➡️ **TASK-PROMPT DEBT LANDS HERE, IN DOC DEBT, WHERE AN UNATTENDED RUN *CAN* WRITE, AND IS CLEARED INTERACTIVELY.** **The two rows below are the first entries filed under that rule.**

| Doc | The stale line | The edit owed |
|---|---|---|
| ✅ 🔴 **CLOSED 2026-08-31** — **SCHEDULED-TASK PROMPT** — `trig_01Pgu7WoEsuipfVVQ41cff7S`, *“Weekly sweep — pitcher DB verify + doc consistency (Mondays, 6am ET)”* `[filed 2026-08-24]` | the v4.0-tripwire bullet beginning 🆕 🔴 **“Does any doc instruct pulling ANY REGION OTHER THAN `us2`?”** — it asserts the standing pull is `regions=us2` **and nothing else** | 🔴 **INVERTED SINCE 2026-08-23 — the standing set is FIVE BOOKS on `regions=us,us2` (ledger rule 48), so as written the tripwire instructs the run to FLAG every doc that says `regions=us,us2` and would RE-NARROW THE ENTIRE PROJECT back to Hard Rock only — the exact opposite of Sam’s 8/23 instruction, applied to the docs the 8/24 sweep just repaired.** ➡️ **THE EDIT OWED: replace that whole bullet with one that NAMES NO REGION SET AT ALL.** It must say instead that **the region/book set is OWNED by `claude/pick-ledger.md` rule 48 and must be READ THERE at the start of every run** — because the set has changed **three times in three days** and **each inline copy was wrong within hours**; that the hunt is for docs disagreeing with rule 48 **in EITHER direction, too narrow OR too wide**; that **a struck historical reference stays as history — the hunt is for LIVE INSTRUCTIONS**; that the **`us_dfs` ban is confirmed against rule 48**, never against the bullet; and that the credit figure is stated **only as the formula `unique markets × regions`**, with the **region count read from rule 48** and the **MARKET LIST read from `collect.py`**. ➕ **ADD THE LESSON: an enumerated list of instances is not a sweep — after any region or market change, GREP EVERY DOC FOR THE OLD STRING.** ⚠️ **ALSO OWED ON THE SAME PROMPT:** **(a)** JOB 1 step 2 must record that **`statsapi.mlb.com` is UNREACHABLE from a scheduled cloud run** (`CONNECT tunnel failed, 403`, measured 2026-08-24) and that the gap must instead be **bounded from the repo’s own enumerated `data/<date>/results/final.json.gz` game counts** — **completed games × 2 = starts added**, and **a `results` file with `n_final: 0` is an unplayed slate** — ⛔ **never from `WebFetch`**; **(b)** the code-sweep section’s **“THREE TIMES” must become FOUR**, adding the **2026-08-24 INVERTED case — a rule live in the CODE that never reached the DOCS —** with the lesson that **the drift runs BOTH ways**; **(c)** the Method section must require **verifying the instructions doc’s scheduled-task table against `list_triggers` every run.** 🔴 **DEADLINE: BEFORE THE NEXT FIRING, 2026-08-31.** ⛔ **An unattended run cannot make this edit — see the note above.** ✅ 🔴 **CLOSED 2026-08-31 — DONE, AND VERIFIED AT THE SOURCE IN THE SAME TURN (rule 37).** **The stored prompt was read back out of `list_triggers` by the 2026-08-31 firing and every one of the four owed edits is in it:** **it now states in bold that it deliberately carries NO region set and that rule 48 OWNS it and must be read there;** **it hunts disagreement in EITHER direction and says a struck historical reference is history, not a finding;** **it confirms the `us_dfs` ban against rule 48 rather than against itself;** **it states the credit figure only as `unique markets × regions` and sends the reader to `collect.py` for the market list;** **it carries the "an enumerated list of instances is not a sweep — grep every doc for the old string" lesson;** **JOB 1 records that statsapi is unreachable from a scheduled run and that the gap is bounded from the repo's own enumerated game counts;** **the code-sweep section reads FOUR TIMES with the inverted case; and the Method section requires `list_triggers` every run.** ✅ **The 2026-08-31 run then USED all of it — and the `list_triggers` requirement immediately earned its place by catching a FOURTH scheduled task no doc knew existed.** ➡️ 🔴 **AND THE PART WORTH KEEPING: THE DEADLINE WAS MET WITH NOTHING TO SPARE, AND THE MECHANISM THAT MET IT WAS THIS ROW.** **An unattended run could not fix the prompt; it could only write the exact edit down here, where an interactive session found it. That is the whole design and it worked once.** |
| ✅ 🔴 **CLOSED 2026-08-31** — **SCHEDULED-TASK PROMPT** — `trig_0115e9hbeLDiKToXgiUuyUFU`, the **7:30am grading task** `[filed 2026-08-24]` | JOB 1B’s **“The card is now written unattended by `card.py` … at 14:45Z and 21:50Z.”** | ⚠️ **THE EVENING TIME IS WRONG.** `[measured 2026-08-24 from `.github/workflows/collect.yml`]` **the card crons are `45 14` and `50 20` — i.e. 14:45Z and 20:50Z, not 21:50Z; the whole evening cycle moved.** ➡️ **THE EDIT OWED: DELETE THE INLINE TIMES and point at `.github/workflows/collect.yml` as the source.** ⛔ **Do NOT restate a new fixed pair — that is how this line went stale in the first place, and it is this project’s own standing rule: delete the number, name the doc.** ⚠️ **ALSO ADD: if `picks/<yesterday>.json` DOES NOT EXIST, THAT IS A FINDING** — **name the date and say the card did not run.** ⛔ **NEVER grade a different date’s file in its place.**  ✅ 🔴 **CLOSED 2026-08-31 — DONE, AND VERIFIED AT THE SOURCE IN THE SAME TURN (rule 37).** **The stored prompt now reads: *"THE SCHEDULE IS READ FROM `.github/workflows/collect.yml` IN THE REPO, NEVER FROM THIS PROMPT — an inline time here has already gone stale once. ⛔ Do not restate the times as a fixed pair either."*** **No inline card times remain anywhere in it.** |

| ⏳ 🆕 **SCHEDULED-TASK PROMPT** — `trig_01Pgu7WoEsuipfVVQ41cff7S`, the **Monday sweep** `[filed 2026-08-31]` | the v4.0-tripwire bullet **“Does any doc state a pair target other than the 1.8x–2.1x band?”** | 🔴 **INVERTED SINCE 2026-08-26, AND IT IS THE SAME SHAPE AS THE REGION TRIPWIRE THIS REGISTER JUST CLOSED — WHICH IS WHY IT IS FILED THE MOMENT IT WAS FOUND RATHER THAN LEFT FOR THE NEXT RUN TO REDISCOVER.** **Sam widened the bands on 2026-08-26: two-mans 1.8x–2.2x, three- and four-mans 3x–6x** (`card.py`'s `PARLAY_BANDS`; now recorded in `claude/pick-ledger.md` rule 28). ⛔ **As written the bullet instructs the run to FLAG every doc that correctly states the 2.2x two-leg ceiling or the 3x–6x multi-leg band — i.e. to strike the correction out of the docs the 2026-08-31 sweep just wrote into them.** ➡️ **THE EDIT OWED: replace the bullet with one that NAMES NO BAND AT ALL.** It must say that **the parlay bands are OWNED by `claude/pick-ledger.md` rule 28 and must be READ THERE at the start of every run**; that the hunt is for docs disagreeing with rule 28 **in EITHER direction**; that **the 1.80x HARD FLOOR is the one number that has never moved** and a doc contradicting *that* is always a finding; and that **a struck historical 2.1x reference stays as history.** ⚠️ **ALSO OWED ON THE SAME PROMPT:** the JOB 1 population-bound instruction should name **`claude/pick-ledger.md`'s own standings-authority figure** as the preferred bound (the grading run computes it daily and controls it with the W=L identity) with the repo's enumerated `final.json.gz` game counts as the top-up, because the 2026-08-31 run had to assemble that itself. ~~🔴 **DEADLINE: BEFORE THE NEXT FIRING, 2026-09-07.**~~ 🔴🔴 **DEADLINE MISSED — RECORDED 2026-09-07 BY THE FIRING ITSELF. THE PROMPT STILL CARRIES THE 1.8x–2.1x TRIPWIRE VERBATIM.** ✅ 🔴 **NOTHING WAS RE-NARROWED: the 2026-09-07 run read `claude/pick-ledger.md` rule 28 FIRST, confirmed the standing bands at 2 LEGS 1.80–2.20 and 3–4 LEGS 3.00–6.00, and DELIBERATELY DID NOT ENFORCE ITS OWN PROMPT'S BULLET.** **`claude/card-blueprint.md` STEP 6's 2026-08-26 widening note and rule 28 itself were read and LEFT EXACTLY AS WRITTEN.** ⚠️ 🔴 **BUT THAT IS A RUN-BY-RUN RESCUE, NOT A FIX, AND IT DEPENDS ENTIRELY ON THE RUN READING THIS ROW BEFORE IT ACTS. THE ROW IS NOW THE ONLY THING STANDING BETWEEN THE STORED PROMPT AND SAM'S 8/26 INSTRUCTION.** ➡️ **THIS IS THE FIRST ITEM FOR THE NEXT INTERACTIVE SESSION.** ⛔ **An unattended run cannot make this edit — `update_trigger` requires human approval.** ⚠️ 🆕 **AND A SECOND, SEPARATE COPY OF THE SAME STALE BAND SITS WHERE ONLY SAM CAN REACH IT: the Project Instructions settings box still reads *"`claude/card-blueprint.md` — the process, and the 1.8x-2.1x band."*** ➡️ **Ask him to change it to name no band and point at ledger rule 28 — the same mistake he already fixed once in that box, when it carried a rule COUNT.** ✅ **The JOB 1 half of this row is DISCHARGED IN PRACTICE: the 2026-09-07 run did bound the population from `claude/mlb-opponent-database.md`'s daily standings-authority figure plus the repo's enumerated `final.json.gz` counts, exactly as this row asks — but the PROMPT still does not say to, so the edit is still owed.** |
| ⏳ 🆕 **SCHEDULED-TASK PROMPT** — `trig_0115e9hbeLDiKToXgiUuyUFU`, the **7:30am grading task** `[filed 2026-08-31]` | JOB 1's item 8, **“If a TABLE C slip is marked OUT OF BAND (outside 1.8x–2.1x) …”** | ⚠️ **SAME CAUSE, SMALLER BLAST RADIUS: the two-leg band ceiling is 2.2x since 2026-08-26 and three- and four-leg tickets have their own 3x–6x band, so a slip at 2.15x is now IN band and this line would exclude it from the very hit rate the band is measured on.** ➡️ **THE EDIT OWED: DELETE THE INLINE BAND and point at `claude/pick-ledger.md` rule 28**, keeping the instruction itself — an out-of-band slip is graded normally and excluded only from the INSIDE-BAND subtotal, with the exclusions named. ⛔ **Do not restate a new fixed pair of numbers.** ⚠️ **Note it is genuinely inert today: no TABLE C row has been logged since 8/22, because Sam has reported no slips.** |
| ✅ 🔴 **CLOSED — VERIFIED 2026-09-21 by the Monday sweep, read from `list_triggers` in the same turn (the fix was made by an interactive session; this run only confirms it)** — ~~⏳~~ 🆕 **SCHEDULED-TASK PROMPT** — `trig_01CzM8fkqXnLqBxw1DYu2aFx`, *“Gizmo's Picks — daily automation audit”* `[filed 2026-08-31]` **(prompt rewritten 2026-09-16; now named "…daily audit (only what the watchdog CANNOT see)". It no longer restates the deadline schedule or any artifact count.)** | it **restates Sam's deadline schedule inline** (*“Trends + Track Record 6:00am ET, Odds + Player Props 7:00am and 4:00pm ET, Gizmo's Picks + Parlays 10:00am ET”*) and asserts **“It prints all 13 artifacts”** | ⚠️ 🔴 **A COUNT AND A SCHEDULE IN A PROMPT NOBODY RE-READS — EXACTLY THE PATTERN THIS REGISTER EXISTS FOR, AND THE FOURTH TASK PROMPT TO CARRY IT.** **The schedule is owned by `claude/update-schedule.md` and the DUE TIMES by `freshness.py`; the artifact count is whatever `verify_freshness.py` currently prints and moves the moment a row is added — and `claude/tomorrow-checklist.md` has an OPEN item to add football rows, which will move it.** ➡️ **THE EDIT OWED: delete the inline schedule and the `13`, and point at `claude/update-schedule.md` and `freshness.py`.** ✅ **The DATED BASELINE FIGURES in the same prompt (the 7 / 4 / 1 / 2 runs on 8/25–8/28, the 9-games / 359-props broken state) are FINE AS WRITTEN and must be KEPT — they are measurements with dates attached, not live counts.** ⚠️ **Lower priority than the two rows above: this prompt reports rather than edits, so a stale count there costs a confusing sentence, not a corrupted doc.** |
| ⏳ 🆕 **SCHEDULED-TASK PROMPT** — `trig_01CzM8fkqXnLqBxw1DYu2aFx`, the **daily audit** `[filed 2026-09-21 by the Monday sweep]` | its check 2 carries **“Expected ~250/day, hard cap 600/day, plan 20,000/month.”** | ⚠️ **THE REWRITE THAT CLOSED THE ROW ABOVE PUT NEW INLINE NUMBERS IN.** `[measured 2026-09-21: `python3 budget.py` in a fresh clone]` **the 7-day measured mean is ~475/day (MLB ~323 + football ~152), so an audit judging against “~250/day” will read a normal day as nearly double.** ➡️ **THE EDIT OWED: delete the three figures and say “compare yesterday's actual against `budget.py`'s own measured rate and the caps in `collect.py` (`FLAT_DAILY_CAP`, `HARD_DAY_CEIL`)” — the same name-the-owner-never-the-number rule as every row in this table.** ⛔ **An unattended run cannot edit a prompt; an interactive session must.** |
| ⏳ 🆕 **POINTER — tests registered OUTSIDE this register** `[filed 2026-09-21 by the Monday sweep]` | `claude/audit-2026-09-20.md` § **PRE-REGISTERED TESTS** holds **T-A, T-B, T-C, T-D**, registered there on 2026-09-20 because this file was too large to rewrite safely from that session | ➡️ **Read them there. ⛔ They are NOT copied here, NOT renumbered into the T-series, and NOT re-decided — this row exists only so a session that reads the register alone does not miss them.** ⚠️ **Their letter IDs can collide with nothing in the T-number series, but an interactive session should decide whether to fold them in (verbatim) or leave them where they are.** |


## Closed entries

- **T18** — opened and closed Aug 21 2026, 🔴 **FAILED on its pre-registered specification** (mean K **5.04 → 4.74**, drop 0.30, **t = −1.78**, against a bar of ≥0.5 and |t| ≥ 2.0). ⚠️ **The significant threshold cut of the same data is EXPLORATORY and is NOT the registered result.** ✅ **A replacement specification is pre-registered inside the entry for the September re-fit.** ⛔ **Do not promote the exploratory number.**
- **T14** — closed Aug 21 2026. Hard Rock alt unders are not reachable through the API; the standing procedure is to ask Sam. ⛔ Do not re-open.
- **DOC DEBT** — `v4-refit-supersessions.md` (deleted, contents rescued) and the Project Instructions box (count removed by Sam) both closed Aug 21 2026.
- **T16** — opened and closed Aug 21 2026, **PASSED** (+6.6 points, z=2.54, n=1,696). ⚠️ It measures the BASE RATE only; the price half is **T17** and is blocked on LINE VALUE.
- **DOC DEBT — `claude/card-blueprint.md` model/raw columns** — closed Aug 21 2026, verified in place.
- **T5** — 🔴 **CLOSED 2026-08-22 as DECIDED** (not passed, not failed — it was a question about a RULE, not a hypothesis). **Sam: *"include them"*.** ✅ **Decided ON PRINCIPLE and BEFORE the bucket filled, exactly as the entry demanded.** ⚠️ **It cuts AGAINST the model: the 60–70% bucket went 5/12 → 5/13, gap −22.5 → −25.9.** **Two of five conversational picks entered; three were excluded and named — `[estimate unlogged]`, `[no PREGAME estimate]`, and one DUPLICATE of a carded row.** ⛔ **No estimate was back-filled.**
- **DOC DEBT — `claude/pick-ledger.md` "Table B"** — 🔴 **CLOSED 2026-08-22 by Sam: *"close it"*.** **Referent identified from primary evidence as the 8/19 midday card (5 plays, `[pre-correction]`, 4/5, excluded from calibration by design); the five play rows are permanently lost and will not be reconstructed; every ledger total reconciles without them.** ⛔ **The data-loss record itself stays — it is the evidence behind ledger rules 42–44. Do not re-open.**
- **T27** — opened AND closed Aug 24 2026, 🔴 **FAILED on its pre-registered specification.** **Held-out Brier improvement over the shipping incumbent was +0.00236 against a bar of +0.00500** (incumbent 0.24248 → model 0.24013 on 7,879 rows; LogLoss 0.67828 → 0.67321, which clears its half — **the criterion required BOTH**). ⛔ **THE BAR WAS NOT MOVED. NOTHING SHIPPED — hitter rows keep the smoothed season rate and keep carrying no confidence number.** ✅ **Not a broken fit: in-sample +0.00351 against out-of-sample +0.00236, and held-out calibration is excellent.** 🔴 **The headline finding is that PLATE APPEARANCES DOMINATE — 0.258 per SD against 0.073 for hitting rate, ~3.5×.** ⚠️ **Home/road is NULL for hitters (z = −1.47) though significant for pitchers.** ➡️ **Successor T28 is pre-registered.**
- **T28** — opened AND closed Aug 24 2026, 🔴 **FAILED on its pre-registered specification, and FAILED WORSE THAN T27.** **Held-out Brier: T28 two-stage 0.24121 against the T27 model's 0.24013 and the incumbent's 0.24248 on the same 7,879 rows — −0.00108 vs T27 against a bar of +0.00200, and +0.00127 vs the incumbent against a bar of +0.00500. IT FAILS BOTH LEGS.** 🔴 **The two-stage structure is WORSE than the flat logistic: stage 1 barely predicts `E[PA]` at all (RMSE 0.985 against a plate-appearance sd of 1.13) and the combination form `P(H >= 1) = 1 - (1-p)^E[PA]` FORCES an independent-trials-at-a-constant-rate assumption the flat logistic never had to accept.** ⛔ **A better-motivated structure is not automatically a better model.** ⛔ **NOTHING SHIPPED — hitter rows still carry no confidence rating.** 🔴 **AND THE TARGET IS CLOSED: two pre-registered specifications have now lost to the incumbent smoothed rate, so a third would be specification shopping. DO NOT OPEN T29 ON `P(1+ hit)`** — revisit hitters only on a DIFFERENT target or with a genuinely NEW input (lineup slot, which is not in the stack). ✅ **What the two failures bought: plate appearances are the dominant term AND are nearly unpredictable — the biggest driver of a hitter's night is the thing we can least forecast. That is a real ceiling on hitter props.**
- **T29** — opened AND closed Aug 24 2026, 🔴 **FAILED on its pre-registered specification, and by a WIDER MARGIN THAN T27.** **Held-out Brier on the same 7,879 rows: base rate 0.21943 → INCUMBENT smoothed rate 0.21695 → T29 model 0.21576 — an improvement of +0.00119 against a bar of +0.00500 (LogLoss 0.62496 → 0.62223, +0.00274, which clears its half — the criterion required BOTH).** ⛔ **THE BAR WAS NOT MOVED. NOTHING SHIPPED.** ✅ **Not a broken fit: in-sample +0.00379 against out-of-sample +0.00119 — a 3x shrinkage, which is what five features on 13,444 rows will do — and held-out calibration is good from 20% to 45%, missing only the n=173 45–50% bucket. The model is honest; it is simply not better by the bar.** 🔴 **AND THE PRE-COMMITTED CONSEQUENCE, WRITTEN BEFORE THE RESULT WAS KNOWN, IS NOW TRIGGERED: HITTER MODELLING ON THIS DATA SET IS CLOSED — not just this target. Three pre-registered specifications across TWO different outcomes have now lost to a smoothed season average: T27 +0.00236, T28 +0.00127, T29 +0.00119, all against +0.00500.** ⛔ **DO NOT OPEN A FOURTH SPECIFICATION ON HITTER PROPS. The reopening condition is a NEW INPUT — LINEUP SLOT above all — NOT a new specification, and hitter rows stay 🔵 DESCRIPTIVE indefinitely: the player's own smoothed rate, no confidence number, no band.** ⚠️ **Home/road is NULL for hitters for the THIRD CONSECUTIVE TEST (z = −0.65).** ✅ **The through-line, worth more than a marginal model: plate appearances DOMINATE every hitter target tried (T27 β 0.258/SD z 14.24; T29 β 0.250/SD z 12.62) and are THEMSELVES nearly unforecastable (T28, RMSE 0.985 against an sd of 1.13) — a ceiling on hitter props, not a failure of any one specification.**
- **T30** — opened Aug 25 2026 and closed the same day, 🔴 **FAILED — BOTH ARMS, BOTH BRIER LEGS.** **Held-out Brier on 7,078 started-game rows: base rate 0.23717 → INCUMBENT smoothed rate 0.23819 → T27's four features refitted 0.23557 → ARM A (plus trailing-20 mean slot) 0.23553 → ARM B (plus today's actual slot) 0.23524.** **ARM A beat the incumbent by +0.00266 (bar +0.00500) and T27-refitted by +0.00003 (bar +0.00200); ARM B by +0.00295 and +0.00033 against the same bars. Log loss cleared for both; the criterion required all three.** ⛔ **NEITHER BAR WAS MOVED. NOTHING SHIPPED.** 🔴 **THE TWO-MARGIN STRUCTURE IS WHAT MADE IT READABLE: Arm A's entire gain over the incumbent IS T27's four features (+0.00262 alone) — THE SLOT TERM IS WORTH +0.00003 — and a single-margin criterion would have reported a 0.0027 gain and invited a shipping decision it had not earned.** ✅ **NOT A BROKEN FIT AND NOT A BROKEN VARIABLE: in-sample gains track out-of-sample; Arm B's held-out calibration is excellent; and raw `P(1+ hit)` by today's actual slot runs 66.2% down to 55.0% across slots 1–9 on this very sample, with a slot-only model beating the base rate by +0.00155.** 🔴 **IT FAILED FOR THE REASON THE ENTRY PRE-REGISTERED: the incumbent already holds the slot information — corr(today's slot, trailing-20 PA) −0.675, corr(today's slot, incumbent rate) −0.455 — and the trailing-PA coefficient collapses from z 7.59 to z 3.59 the moment slot enters.** ⚠️ **Arm B's slot term IS significant (z −2.54) where Arm A's is not (z −1.24), exactly as predicted: slot pays only when it CHANGES, and the trailing mean cannot see a change.** ⛔ **THE PRODUCT-FINDING BRANCH IS NOT TRIGGERED — Arm B failed too, so T30 provides NO evidence for a late card and must not be cited as if it did.** ⚠️ 🔴 **AND A SECOND RESULT THAT CUTS AGAINST THE SHIPPED ESTIMATOR: on the STARTED-GAMES sample the INCUMBENT IS WORSE THAN THE LEAGUE BASE RATE (0.23819 against 0.23717), where on T27's `pa > 0` sample it was better (0.24248 against 0.24446) — most of what the smoothed rate was buying was starter-versus-cameo, not one starter versus another.** ⛔ **A reading, not a finding; it does not license changing the shipped estimator, and if that estimator is revisited THAT is the question to pre-register.** ➡️ **T29's reopening condition named LINEUP SLOT; that input has now been built, joined, verified and fitted, and it did not clear. The condition is spent on the input it named, and another cut of slot would be a new specification on a spent input.**

- **T31** — opened Aug 25 2026, ⏳ **PRE-REGISTERED, NOT RUN.** **Phase 3's first entry and the first test in this project that is not about a player.** **Sam chose the target himself, as he did for T27: the GAME TOTAL, over/under combined runs.** ✅ **Unblocked by the `scores` backfill built the same day — 177 dates, 2,314 games, validated 90/90 EXACT against every final already on disk.** 🔴 **The raw backfill is NOT the sample: `sportId=1` also returns 14 World Baseball Classic sides, 4 minor-league/Mexican clubs, 2 All-Star squads and 311 spring-training games, and spring training scores 5.02 runs per team-game against the regular season's 4.47 — pooled, the run environment reads +0.070 too high and 15% of games are not regular-season baseball.** ✅ **So the filter is part of the specification: both clubs among the 30 MLB teams taken from the hitter DB's own field, and the date on or after opening day derived as the first date in the hitter game logs (2026-03-25) — never hand-typed. Clean sample 1,973 games, 1,444 train / 529 test, combined runs mean 8.94 sd 4.52.** 🔴 **THE TEST SPLITS IN THREE AND ONLY TWO ARMS ARE RUNNABLE: T31a (four team-form features vs a naive baseline) and T31b (plus both starters' trailing-8 earned runs) can run now; T31c — does the model beat the BOOK's posted total — has 55 GAMES and cannot be backfilled, the same wall T25 hit.** ⛔ **T31a and T31b are SANITY GATES, NOT SHIPPING GATES — beating a naive baseline means nothing at a sportsbook, and only T31c can license a total on the board.** ⛔ **Using the market's posted total as a FEATURE is forbidden outright, not merely flagged: a model that has read the book's number and is then scored against it measures nothing.** 🔴 **The prior is written down in advance: totals are the most heavily modelled market in baseball and the honest expectation is that T31c FAILS, with T31a/T31b passing — meaning the model is real but not sharper than the book.**

- **Aug 25 2026 (T31a AND T31b FITTED AND FAILED — and a game total turns out to be almost entirely unforecastable from team form)** — 🔴 **BOTH RUNNABLE ARMS OF PHASE 3'S FIRST TEST CLOSED-FAILED THE DAY THEY WERE REGISTERED.** **T31a, four point-in-time team-form features on 1,138 train / 529 held-out games, came in at MAE 3.6281 against the naive team-trailing baseline's 3.6227 — +0.0054 WORSE, against a bar of +0.10000.** **T31b, adding both starters' trailing-8 earned runs, was scored on the SAME 380 held-out rows as T31a — because T31b's sample is a SUBSET and comparing against T31a's full-set figure would measure the SAMPLE CHANGE rather than the starters, exactly the trap T30's second margin was written to catch — and gained +0.0403 MAE against a bar of +0.05000. It FAILS, narrowly.** ⛔ **NEITHER BAR WAS MOVED AND NOTHING SHIPPED; the Odds tab's totals stay 🔵 MARKET-only.** 🔴 **THE HEADLINE IS NOT THE FAILURE BUT THE CEILING: the model's predictions span 7.79 to 10.80 while real games range from 1 to 27 at sd 4.51, and corr(predicted, actual) is +0.0799 — under 1% of variance. A baseball game's run total is overwhelmingly same-day noise that season-long team form cannot see.** ⚠️ **That is the Phase 3 analogue of Phase 2's ceiling: there, plate appearances dominated and were themselves unforecastable.** ✅ **CHECKED BEFORE RECORDING: T31a is plainly OVERFITTING (in-sample gain +0.1211 against out-of-sample −0.0054) while T31b survives its shrinkage (+0.1494 in, +0.0441 out); point-in-time integrity was confirmed by re-deriving sampled trailing-20 windows directly from the raw score file with ZERO mismatches; and the fit centres sanely on 8.99 against an actual 8.70.** 🔴 **THE MOST USEFUL OUTPUT IS A COEFFICIENT READING, LABELLED AS ONE AND NOT PROMOTED: per standard deviation, home runs ALLOWED +0.511 and the away STARTER +0.313 dominate, while away runs SCORED is +0.028 — the two offence terms together are worth less than the weakest pitching term. Runs allowed proxies a pitching staff, which persists; offence is noisier.** ⛔ **IT IS A DESCRIPTION OF A MODEL THAT FAILED, not a finding.** ⛔ **AND WHAT IT SAYS ABOUT T31c IS STATED NOW RATHER THAN AS A LATER SURPRISE: a model that cannot beat 'add the two clubs' trailing runs scored' has no realistic prospect of beating a sportsbook, so the pre-registered expectation that T31c fails is considerably stronger than when written. T31c is NOT decided and its counter is untouched at 55 / 400 games.** ✅ **A DIRECTION is recorded and explicitly NOT a specification — the terms that carried weight were PITCHING terms, and this project has a FITTED PITCHER MODEL that T31b did not use, reaching instead for a crude trailing-8 earned-run average. Any successor must be pre-registered BEFORE fitting and must beat T31b's 3.5309 on the same rows.** ⛔ **Writing that spec now, having seen these coefficients, would be shopping.** ⛔ **NO EXISTING ENTRY, PASS CRITERION, SPECIFICATION, PROGRESS COUNTER, MEASURED RESULT, CLOSED VERDICT OR DOC DEBT ITEM WAS ALTERED, RENUMBERED OR REMOVED — T31's specification, its three pass bars and both forbidden lists stand byte-for-byte and the result was ADDED BENEATH THEM; T1–T30 are byte-identical. The only line replaced is T31's STATUS line.**

- **T32** — opened Aug 25 2026, ⏳ **PRE-REGISTERED, NOT RUN.** **Phase 3's second attempt, and a REOPENING ON NEW INPUTS rather than a new specification on the old ones — the same standard T30 had to meet after T27/T28/T29.** **T31 failed at corr +0.0799 on trailing team runs and a crude earned-run average; the diagnosis was that the inputs were the weakest set available, not that the model was wrong.** ✅ **Three physically-grounded inputs arrived the same day: PARK (`venue` was in the schedule response all along and the backfill's narrow field list dropped it — Coors against Petco is worth ~2 runs), TEMPERATURE and WIND (new `collect.py` mode `weather`, venue coordinates from statsapi and history from Open-Meteo's free archive), and DAY/NIGHT.** **Coverage measured before the spec was written: 4,578 readings across 57 venues, temperature 27–112°F, wind 0.1–22.2 mph, and 1,971 of 1,973 regular-season games — 99.9% — carrying a reading at game hour. Validity confirmed by the seasonal curve (63.5°F April to 82.7°F July) and by `gameType=='R'` returning EXACTLY 1,973, matching the opening-day filter T31 derived independently.** ⛔ **WIND DIRECTION IS STORED BUT DELIBERATELY EXCLUDED AS A FEATURE: a bearing is meaningless without park orientation — 90° at Wrigley blows out, 90° at Fenway does not — and this project holds no orientation table. Inventing one, or letting a model learn 34 park-specific interactions from 1,973 games, would be fabrication dressed as a feature.** ⚠️ **The PARK FACTOR is required to be POINT-IN-TIME — the mean total at that venue over games strictly BEFORE the row, minus the league mean to that point, with under 10 prior games contributing 0.0 — because a season-long factor used inside its own season is LOOKAHEAD, the error already struck twice here for T22's role label and T24's durability label.** **Two arms, both on T31b's exact sample so the comparison is like-for-like: T32a adds the four environment terms to T31b's six and must beat T31b by >= 0.05 MAE on the SAME rows; T32b adds each starter's trailing-8 mean OUTS and mean K — the v4.0 model's own predictors, which Phase 3 has never used — and must beat T32a by >= 0.05 on the same rows.** 🔴 **BOTH ARE SANITY GATES, NOT SHIPPING GATES. The bar that matters is still T31c at 55/400 games.** ⚠️ **The honest prior is recorded in advance: park and weather are large real effects and SHOULD move MAE, but T31 showed the outcome is dominated by same-day variance — expect a real improvement and a still-unbettable model, and treat that as a finding rather than a disappointment.**

- **Aug 25 2026 (T32 FITTED AND FAILED — but it separated the real environmental inputs from the fake ones, which is what a test is for)** — 🔴 **BOTH ARMS CLOSED-FAILED. T32a came in at MAE 3.5886 against T31b's 3.5269 on the same 380 held-out rows — 0.0618 WORSE than the model it was meant to improve, against a bar of +0.05000 — and T32b gained +0.0302 over T32a against the same bar.** ⛔ **Neither bar was moved and nothing shipped.** ✅ 🔴 **THE RESULT WORTH KEEPING IS THAT TWO OF THE FOUR NEW INPUTS ARE REAL AND TWO ARE NOTHING: corr with combined runs reads PARK +0.1363 and TEMPERATURE +0.0913 — both genuine, and in T32a's fit they are the two LARGEST terms at +0.597 and +0.455 runs per standard deviation, bigger than any pitching or team-form term — against WIND SPEED −0.0010 and DAY/NIGHT −0.0113, which are nothing. The physical prior was half right, and adding two pure-noise features to a 647-row fit cost more than the two real ones gained. That is the whole failure in one sentence.** ⚠️ **WIND'S NULL MUST BE REPORTED AS 'WIND SPEED ALONE IS NULL', NEVER AS 'WIND IS NULL' — direction was deliberately excluded because this project holds no park-orientation table, so a 15 mph wind blowing out and one blowing in are the same number here and physically opposite.** ✅ **AND THE MODEL SEES MORE THAN T31 DID EVEN WHILE SCORING WORSE: corr(predicted, actual) nearly DOUBLED from +0.0799 to +0.1559 and the predicted range widened from 7.79–10.80 to 7.33–12.51. A bolder model that is not perfectly calibrated is punished by an error metric even while tracking the outcome better. That does NOT rescue the arm — the bar was MAE — but it is why the inputs are worth keeping.** 🔴 **CHECKED BEFORE RECORDING: T32a is OVERFITTING (in-sample 3.5813, better than T31b's 3.6296, while out-of-sample is worse) on ten features and 647 training rows; and a NONSENSE SIGN confirms it — `h_rs` reads −0.2497, meaning a home club scoring MORE lately predicts FEWER total runs, which is physically impossible and is the classic signature of collinear features in a thin fit.** ✅ **The PARK FACTOR was verified POINT-IN-TIME BY HAND rather than asserted: one row's stored value (+0.524796, gamePk 823444, 42 prior games at that venue) was re-derived from the raw score file and matched to six decimal places.** ⚠️ **The FIRST attempt at that check was WEAK and is recorded as such — it looked for zero-valued factors among the earliest rows, but the sample starts a month into the season by which point every park has 10+ games, so it could not have discriminated.** ➡️ **A DIRECTION is recorded and explicitly NOT a specification: park and temperature ONLY, dropping wind and night, on the LARGER sample — T32 inherited T31b's starter requirement and paid 639 games for it, 1,027 rows against the 1,667 available, and park and temperature need no starter join at all.** ⛔ **Writing that spec now, having seen which two inputs survived, is exactly the shopping this register exists to forbid; it must be registered BEFORE fitting and must beat T31b's 3.5269.**

- **T33** — opened Aug 25 2026, ⏳ **PRE-REGISTERED, NOT RUN.** **Phase 3's third and final attempt, and a REOPENING ON NEW INPUTS THAT CAME FROM OUTSIDE THIS PROJECT'S DATA — Sam supplied published sources on weather and hitting, and two mechanisms in them are inputs Phase 3 has never had.** **The sources give: the pathway is AIR DENSITY; a game 18°F above average has ~20% more home runs; the effect is BROAD rather than home-run-only (HR 29–46%, hits/BA 5–11%), which SUPPORTS keeping combined runs as the target; a COLD BALL has a lower coefficient of restitution, so it is not only the air; and fly balls travel 16 FEET LESS at ≤50°F than at ≥90°F.** ➡️ **Two consequences, both new model content: the temperature effect is plausibly NON-LINEAR — a cold penalty rather than a smooth slope, where T31 and T32 both fitted a straight line — and ELEVATION is the purest air-density variable and was never stored, though Open-Meteo returns it on every response and a top-up pass added it the same day.** ⚠️ 🔴 **THE HONEST ACCOUNTING IS RECORDED IN THE ENTRY: WIND SPEED AND DAY/NIGHT ARE DROPPED, AND THAT ONE DECISION IS DATA-DRIVEN RATHER THAN THEORY-DRIVEN — T32 measured them at corr −0.0010 and −0.0113. That makes T33 a WEAKER pre-registration than T31 or T32 in exactly that respect, and the weakness is stated rather than glossed. What is NOT weakened: elevation and the cold term were chosen from published physics before any fit, and the bars are carried over UNCHANGED from T31a rather than softened after a failure.** ⚠️ **ELEVATION AND PARK FACTOR ARE CORRELATED BY CONSTRUCTION and that is stated before fitting — a park factor already encodes most of what elevation does, since Coors reads high because it IS high. Elevation's marginal value is that it is EXACT AND KNOWN FROM DAY ONE where the park factor needs 10 games before it says anything. Expect a SMALL coefficient; if it comes back large, suspect collinearity before celebrating.** ✅ **THE SAMPLE IS THE LARGER ONE — no starter requirement, which T32 inherited and paid 639 games for, and none of T33's new inputs need a starter join.** **EXACTLY EIGHT features: four team-form terms, point-in-time park factor, temperature, a COLD indicator at `temp < 60°F` fixed in advance and explicitly NOT the sources' 50°F because 50°F is nearly absent from a regular MLB season, and venue elevation.** **TWO MARGINS, the T30 structure for the T30 reason: beat the better naive baseline by >= 0.10 MAE — the SAME bar T31a had and failed, NOT lowered after a failure — AND beat T31a's four team-form features refitted on these exact rows by >= 0.05, which isolates the four new terms from the sample change. Both, or it fails.** 🔴 **PRE-COMMITTED CONSEQUENCE, STATED BEFORE THE RESULT: IF T33 FAILS, PHASE 3 CLOSES FOR THE SEASON. The Odds tab's totals stay 🔵 MARKET-only and the reopening condition is a genuinely new input — a numeric park-orientation table, or captured market history reaching T31c's 400 games — NOT another specification. Same pre-commitment T29 made for hitters, for the same reason: so the decision is not taken while disappointed.**

- **Aug 25 2026 (T33 FITTED AND FAILED — PHASE 3 CLOSES FOR THE SEASON on a pre-commitment made before the result)** — 🔴 **T33 CLOSED-FAILED BOTH MARGINS: −0.0363 MAE against the better naive baseline (bar +0.10000) and −0.0322 against T31a on the same 529 held-out rows (bar +0.05000), on a sample 638 games LARGER than T32's. IT IS WORSE THAN THE FOUR-FEATURE MODEL IT WAS BUILT TO IMPROVE.** ⛔ **Neither bar was moved and nothing shipped.** 🔴 **MY OWN PRE-REGISTERED PREDICTION WAS WRONG AND THAT IS RECORDED FIRST: the entry predicted elevation would be collinear with the park factor and therefore SMALL, and instructed that if it came back large the right response was to suspect collinearity before celebrating. It came back LARGE (+0.501 runs per sd), the collinearity was checked, and there is NONE — corr(park, elevation) +0.2414 and VIF 1.12. Elevation is NOT redundant and its coefficient is not an artifact. The prediction was specific, it was mine, and it was wrong.** 🔴 **THE REAL COLLINEARITY IS BETWEEN TWO OTHER TERMS AND IT IS WHY THE ARM FAILED: corr(home club's runs ALLOWED, park factor) = +0.4773, because half a club's games are played in its own park, so its runs-allowed average and an explicit park factor are substantially THE SAME FACT COUNTED TWICE. The consequence is visible in the coefficients — home runs ALLOWED was T31's single LARGEST term at +0.445 per sd and collapses to +0.015 in T33, while home runs SCORED flips to −0.278, a nonsense sign. Adding the park factor did not ADD information; it REDISTRIBUTED information the team-form terms already carried, destabilised the fit and cost out-of-sample accuracy.** ⛔ 🔴 **AND THE COLD TERM WAS NEVER ACTUALLY TESTED — A FLAW IN THE TEST DESIGN, NOT IN THE IDEA: cold games (`temp < 60°F`) are 165 of 1,136 in TRAIN and TWO of 529 in the held-out set, because a chronological split at mid-July puts almost every cold game in training. Cold baseball is an April phenomenon. The term was fitted on 165 games and evaluated on two, so T33 says NOTHING about whether a cold penalty is real.** ⚠️ **The split date is NOT moved — it is shared with T27–T32 and changing it after a failure is what this register forbids — but the limitation is recorded so nobody reads T33 as evidence against the cold-ball mechanism. Testing it properly needs a split with cold games on BOTH sides, and that is a NEW pre-registration.** ⚠️ **CHECKED BEFORE RECORDING: T33 overfits more than T31a (in-sample +0.1891 against +0.1233, out-of-sample −0.0363 against −0.0041) — eight features on 1,136 rows buying training fit and nothing else; and corr(predicted, actual) reads +0.1456 against T32a's +0.1559, so the larger sample did not restore what T32a's ten features reached.** 🔴 **THE PRE-COMMITTED CONSEQUENCE IS TRIGGERED: PHASE 3 IS CLOSED FOR THE SEASON. Five arms across three pre-registered specifications — T31a −0.0054, T31b +0.0403, T32a −0.0618, T32b +0.0302, T33 −0.0363 — and NOT ONE cleared a bar against a NAIVE baseline, never mind a sportsbook. The Odds tab's totals stay 🔵 MARKET-only.** ⛔ **The reopening condition is a genuinely NEW INPUT — a NUMERIC park-orientation table, or captured market history reaching T31c's 400 games — NOT another specification. Sam's orientation source was checked the same day and turned out to be COMPASS-ROSE DIAGRAMS rather than bearings, so that door is still shut.** ✅ **WHAT THE THREE FAILURES BOUGHT: a game total is mostly noise (best correlation any arm reached was +0.1559, about 2% of variance, against real games running 1 to 27 runs); PARK and TEMPERATURE are real (+0.1363, +0.0913) while WIND SPEED ALONE and DAY/NIGHT are not (−0.0010, −0.0113); PARK FACTOR AND A HOME CLUB'S RUNS ALLOWED ARE SUBSTANTIALLY THE SAME VARIABLE, so anyone adding a park term to a team-form model is double-counting; ELEVATION IS NOT redundant with park factor, contradicting this entry's own prediction; A CHRONOLOGICAL MID-SEASON SPLIT CANNOT TEST A SEASONAL VARIABLE; and PERMANENT DATA THAT DID NOT EXIST THAT MORNING — 1,973 clean regular-season games with real scores, park and day/night, 4,578 weather readings covering 99.9% of them, and elevations for 57 venues — none of which depends on Phase 3 succeeding.**


---

## Changelog

- **2026-09-21 (Monday sweep — DOC DEBT ONLY, NOTHING ELSE TOUCHED)** — ⛔ **NO TEST ENTRY, SPECIFICATION, PASS CRITERION, PROGRESS COUNTER, MEASURED RESULT OR CLOSED VERDICT WAS ALTERED, RENUMBERED OR REMOVED; no owed test was run.** ✅ **The 2026-08-31 daily-audit prompt row is CLOSED — verified against `list_triggers` in this turn (rewritten 2026-09-16).** 🆕 **Two rows filed: the same prompt's new inline spend figures ("~250/day" against a measured ~475/day), and a POINTER to T-A–T-D, which live in `claude/audit-2026-09-20.md`.** ⚠️ **The Monday-sweep and grading-prompt band rows (filed 2026-08-31) are RE-CONFIRMED STILL OWED — both stored prompts still carry `1.8x–2.1x`.** T-entry header count 54 before and 54 after. Method: file-returned `project_read` → `cp` → uniqueness-asserted patch → `collections.Counter` line-loss check → `local_path` upload.
- **2026-09-18 (7:30am grading run — ONE DOC DEBT ROW FILED, NOTHING ELSE TOUCHED)** — ⛔ **NO TEST ENTRY, SPECIFICATION, PASS CRITERION, PROGRESS COUNTER, MEASURED RESULT OR CLOSED VERDICT WAS ALTERED, RENUMBERED OR REMOVED. No owed test was run — the owed tests belong to the monthly firing and running one early destroys its pre-registration.** ✅ **T15's sample trigger was READ, not restated from any prompt, and it is STILL NOT MET: the machine board is not T15's population and no TABLE A play has been carded since 2026-08-22, so T15 stands at 31 carded plays against its own pre-registered `n` bar.** 🆕 🔴 **ONE NEW DOC DEBT ROW: `claude/pick-ledger.md` lost the 2026-09-15 and 2026-09-16 grading blocks to a concurrent write — the FOURTH occurrence and the FIRST time an already-restored block was lost a second time — and the standing divergence check is now measured to be insufficient, because a NEWER `created_at` on the ledger does not mean it carries the newer RECORD.** ⛔ **The row names candidate fixes and CHOOSES NONE: preventing a concurrent write is an INTERACTIVE decision and a grading run does not make it.** ⚠️ **Method: `project_read` (returned as a FILE — `cp`'d, no retype) → programmatic patch with the anchor ASSERTED to occur EXACTLY ONCE → `collections.Counter` line-loss check (zero original lines lost) → fresh `project_read` compared immediately before upload → upload with `local_path`, per ledger rule 43.**

- **Sept 1 2026, 4am ET scheduled monthly re-fit firing (headless — the re-fit did NOT run, and the register was verified instead)** — 🔴 **NO BROWSER, SO NO DATA: nothing was fitted, no entry was closed, no specification was altered, no counter moved, and no substitute dataset was improvised.** ✅ **Every open entry was re-read against its own wording and no quiet re-specification was found; every sample-size trigger was checked against `claude/pick-ledger.md` and `claude/calibration-accumulators.md` and NONE is met (T4 17/30 · T6 1/10 · T11 25/40 · T15 31/100 · T17 1/40 blocked · T19 1/10 · T23/T24 5/30 · T25 0 joined); blocked entries reported as blocked (T13b — no weather source; T17 — no captured prices; T10 — no key headless).** ✅ **`card.py`'s model block was compared against `claude/mlb-projection-model.md` constant by constant and EVERY ONE matches v4.0 exactly** — so the CODE-DEBT comparison in the brief is armed for the day new values publish. 🆕 **A READY-TO-RUN BRIEF for the interactive re-fit was inserted ahead of Tier 1**, stating execution order by pointer to each entry (no bar and no coefficient is restated in it). ⛔ **NO TEST ENTRY, SPECIFICATION, PASS CRITERION, PROGRESS COUNTER, MEASURED RESULT, CLOSED VERDICT OR DOC DEBT ROW WAS ALTERED, RENUMBERED OR REMOVED — this write is a PURE INSERTION of the brief and this entry.** ⚠️ **Merged, not rewritten: `project_read` (returned as a FILE — `cp`'d, no retype) → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE → `collections.Counter` line-loss check → fresh `project_read` compared immediately before upload → upload with `local_path`, per ledger rule 43.**

- **Aug 31 2026, Monday sweep (both 2026-08-24 task-prompt debts CLOSED — the mechanism worked exactly once and it worked — and three more filed the day they were found)** — ✅ 🔴 **THE TWO ROWS FILED ON 2026-08-24 ARE BOTH DONE AND BOTH WERE VERIFIED AT THE SOURCE IN THIS SAME TURN (rule 37), NOT ASSUMED.** **The stored prompts were read back out of `list_triggers` and checked edit by edit.** **The Monday sweep prompt now names no region set and points at ledger rule 48; the 7:30am grading prompt now points at `.github/workflows/collect.yml` and carries no card times.** 🔴 **THE DESIGN POINT, RECORDED BECAUSE IT IS THE FIRST TIME IT HAS BEEN TESTED END TO END: an unattended run could not repair either prompt, so it wrote the exact edit into this register, an interactive session picked it up, and the 2026-08-31 firing then RAN under the corrected prompt and immediately used all four of its edits.** ⚠️ **The region tripwire's deadline was met with nothing to spare — had it slipped one week, the sweep would have re-narrowed the whole project to Hard Rock only.** 🆕 🔴 **THREE NEW TASK-PROMPT ROWS FILED, and the first two are the SAME FAILURE ONE RULE OVER: Sam widened the parlay bands on 2026-08-26 (two-mans 1.8x–2.2x, three- and four-mans 3x–6x) and BOTH the Monday sweep prompt and the 7:30am grading prompt still hard-code `1.8x–2.1x`.** ⛔ **Left as written, next Monday's sweep would strike the 2.2x correction back out of the docs this sweep just wrote it into — the exact failure the region row was filed to prevent, reproduced on a different number.** ➡️ **Both edits owed are the same shape and it is the shape this project keeps re-learning: NAME NO NUMBER, POINT AT THE DOC THAT OWNS IT — here `claude/pick-ledger.md` rule 28.** **The third row is the newly-discovered fourth scheduled task, which restates the deadline schedule and an artifact count inline instead of pointing at `claude/update-schedule.md` and `freshness.py`.** ⛔ **NO TEST ENTRY, SPECIFICATION, PASS CRITERION, PROGRESS COUNTER, MEASURED RESULT, CLOSED VERDICT OR PRE-EXISTING DOC DEBT ROW WAS ALTERED, RENUMBERED OR REMOVED — T1–T45 are byte-identical, every Tier-3 row is untouched, both un-numbered MEASURED FINDINGS are untouched, and the Closed-entries list is untouched. The only two lines replaced are the two 2026-08-24 DOC DEBT rows, each amended IN PLACE to carry its closure; everything else in this write is a PURE INSERTION.** ⚠️ **Merged, not rewritten: `project_read` (which returned this doc as a FILE PATH, so there was no transcription and no retype) → `cp` to a local file → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → `project_info` `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.**

- **Aug 25 2026 (T30 FITTED AND FAILED — BOTH ARMS. The input T29 named is in the stack, is real, and is already inside the incumbent. The reopening condition is spent.)** — 🔴 **T30 CLOSED-FAILED. THE SLOT MODEL WAS FITTED, MEASURED, AND BOTH ARMS MISSED BOTH BRIER LEGS OF THE PRE-REGISTERED BAR.** **Held-out on 7,078 started-game rows (base rate 0.6140), all five estimators scored on the SAME rows: base rate 0.23717 / LogLoss 0.66729 → INCUMBENT smoothed rate 0.23819 / 0.66966 → T27's four features refitted on this sample 0.23557 / 0.66390 → ARM A, plus his trailing-20 mean slot, 0.23553 / 0.66384 → ARM B, plus today's actual slot, 0.23524 / 0.66322.** **ARM A beats the INCUMBENT by +0.00266 against a bar of +0.00500 and T27-REFITTED by +0.00003 against a bar of +0.00200; ARM B by +0.00295 and +0.00033 against the same two bars. Log loss improved for both (+0.00582 and +0.00644) and clears its leg — THE CRITERION REQUIRED ALL THREE.** ⛔ **NEITHER BAR WAS MOVED AND NOTHING SHIPPED — hitter rows keep the smoothed season rate and keep carrying no confidence number.** 🔴 **THE TWO-MARGIN STRUCTURE IS WHAT MADE THE RESULT READABLE, AND IT WAS PRE-REGISTERED WITH ITS REASON ATTACHED — *"beating the incumbent while adding nothing over T27 would mean the SAMPLE changed, not that slot helped."* THAT IS EXACTLY WHAT HAPPENED: Arm A's ENTIRE +0.00266 over the incumbent is T27's four features, which are worth +0.00262 on this sample by themselves, so THE SLOT TERM IS WORTH +0.00003.** ⚠️ **A single-margin criterion would have reported a 0.0027 gain and invited a shipping decision it had not earned.** **THE SAMPLE, on the filters fixed in advance — games he STARTED by real batting order, not `pa > 0` and not a `pa >= 3` proxy: 18,578 usable rows across 444 hitters and 121 dates, 11,500 train (base 0.6272) / 7,078 test (base 0.6140); dropped 9,072 for fewer than 20 prior STARTED games, 4,092 for a starter with under 5 prior starts, 1,073 for FAILING THE TRADE-CONSISTENCY CHECK, 707 for an ambiguous or missing starter, and 369 rows whose LINEUP JOIN WAS NOT UNAMBIGUOUS — 320 doubleheaders whose lineup entries disagree and 14 with two lineup entries against one log row.** ✅ **THE DOUBLEHEADER AMBIGUITY WAS DROPPED, NOT GUESSED AT: a hitter's log is keyed only by DATE, so unless every game that day was a start at the same slot there is no way to say which card belongs to which row, and the whole date leaves the started log rather than being assigned by position.** ✅ **The trade-consistency check was rebuilt exactly as T27 built it and again validated itself — 3,892 directed team-days kept against the ~3,900 that thirty teams over roughly 130 dates should produce.** ✅ **IT IS NOT A BROKEN FIT AND — the check that matters most here — NOT A BROKEN VARIABLE: in-sample gains track out-of-sample (T27-refitted +0.00444/+0.00262, Arm A +0.00447/+0.00266, Arm B +0.00457/+0.00295); Arm B's held-out calibration is excellent (50–55% → 51.6% n=473 · 55–60% → 57.4% n=1,639 · 60–65% → 61.2% n=2,652 · 65–70% → 66.5% n=2,146, only the n=145 70–75% bucket missing); the incumbent was hand-re-derived from the raw log on sampled rows and matched to 12 decimal places; and RAW `P(1+ hit)` BY TODAY'S ACTUAL SLOT RUNS 66.2% · 66.5% · 65.5% · 63.1% · 62.9% · 60.0% · 59.8% · 56.6% · 55.0% ACROSS SLOTS 1–9 ON THIS VERY SAMPLE — monotonic, an 11-point spread, with a slot-only model beating the base rate by +0.00155. THE VARIABLE CARRIES REAL INFORMATION. IT CARRIES ALMOST NONE THE MODEL DID NOT ALREADY HAVE.** 🔴 **AND IT FAILED FOR THE REASON THE ENTRY WROTE DOWN IN ADVANCE SO IT COULD NOT BE CLAIMED AS A DISCOVERY LATER — *"the incumbent already contains most of the slot information"* — WHICH IS NOW MEASURED: corr(today's slot, his trailing-20 mean slot) +0.827, corr(today's slot, his trailing-20 mean PA) −0.675, corr(today's slot, the INCUMBENT rate) −0.455, corr(trailing mean slot, the INCUMBENT rate) −0.491 — and the collinearity is visible inside the fit, the trailing-PA coefficient collapsing from 0.1498 (z 7.59) to 0.1175 (z 3.59) the moment slot enters.** ⚠️ 🔴 **ARM B'S SLOT TERM IS SIGNIFICANT AND ARM A'S IS NOT — z = −2.54 against z = −1.24 — WHICH IS PRECISELY THE PRE-REGISTERED PREDICTION: slot pays mainly when it CHANGES, and a change is exactly what the trailing mean cannot see. The mechanism was right; the magnitude is still too small to clear anything.** ⛔ 🔴 **THE "PRODUCT FINDING" BRANCH IS NOT TRIGGERED AND A LATE CARD IS NOT JUSTIFIED BY THIS TEST: T30 pre-registered that if Arm B passed while Arm A failed the response would be a LATE CARD generated after lineups post — BUT ARM B FAILED TOO, and today's actual batting order, the very information such a card would exist to capture, is worth +0.00033 Brier over T27's features against a bar of +0.00200. A late card may still be worth building for other reasons — scratches, rest days, a bat out of the lineup entirely — but T30 provides NO evidence for it and must not be cited as if it did.** ⚠️ 🆕 🔴 **A SECOND RESULT IS RECORDED BECAUSE IT CUTS AGAINST THE SHIPPED ESTIMATOR: ON THE STARTED-GAMES SAMPLE THE INCUMBENT IS WORSE THAN PREDICTING THE LEAGUE AVERAGE FOR EVERYONE — Brier 0.23819 against 0.23717 — WHERE ON T27's `pa > 0` SAMPLE IT WAS BETTER (0.24248 against 0.24446). THE ORDERING FLIPS.** ➡️ **The reading, labelled as a reading: most of what the player's own smoothed rate was buying on the old sample was the difference between a STARTER and a CAMEO, not between one starter and another — consistent with the cameo measurements already in the project (under 0.5 hits: 74.8% on cameos against 37.4% on starts).** ⛔ **NOT PRE-REGISTERED, NOT A FINDING, AND IT DOES NOT LICENSE CHANGING THE SHIPPED ESTIMATOR — it is written down because it is the kind of thing that gets rediscovered later and mistaken for new. If the shipped hitter estimator is ever revisited, THAT is the question to pre-register.** 🔴 **WHAT IT MEANS FOR HITTER MODELLING IS STATED AS A READING AND NOT AS A PRE-COMMITTED CONSEQUENCE, BECAUSE T30 DID NOT PRE-REGISTER ONE AND ONE IS NOT BEING INVENTED AFTER THE FACT: four pre-registered specifications have now lost to a smoothed season average across two targets and two samples — T27 +0.00236, T28 +0.00127, T29 +0.00119, T30 Arm A +0.00266 and Arm B +0.00295, every one against +0.00500. T29's reopening condition was a NEW INPUT and it named LINEUP SLOT; that input has now been built, joined, verified and fitted, and it did not clear. THE CONDITION IS SPENT ON THE INPUT IT NAMED.** ⛔ **Another cut of slot — a slot-change flag, a slot interaction, a nine-way dummy, a different window — IS A NEW SPECIFICATION ON A SPENT INPUT, and forbidding exactly that is this register's whole purpose.** ✅ **Hitter rows on the Picks tab stay 🔵 DESCRIPTIVE.** ✅ **WHAT THE BACKFILL BOUGHT ANYWAY, AND IT IS NOT NOTHING: the project now holds real batting order for 176 dates and 53,424 batter-games, which is what makes a STARTED-GAMES sample possible at all — that sample already corrected the board once, bench bats no longer top the picks list, and it is the correct population for every future hitter question, model or not.** ⛔ **NO EXISTING ENTRY, PASS CRITERION, SPECIFICATION, PROGRESS COUNTER, MEASURED RESULT, CLOSED VERDICT OR DOC DEBT ITEM WAS ALTERED, RENUMBERED OR REMOVED — T30's SPECIFICATION, its PASS BARS and its FORBIDDEN LIST stand byte-for-byte as pre-registered and the result was ADDED BENEATH THEM; T1–T29 are byte-identical, every Tier-3 row is untouched, EVERY DOC DEBT ROW IS UNTOUCHED, and both un-numbered MEASURED FINDINGS are untouched. The only line replaced in this write is T30's byline, which gains a STATUS line moving it from PRE-REGISTERED to CLOSED-FAILED.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session's transcript JSONL with a JSON walker rather than retyped → local file inside the working directory → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → full `project_read` AGAIN immediately before upload, rebasing if it had moved → upload with `local_path`, per ledger rule 43.** ⛔ **One doc touched this write — this one.**

- **Aug 25 2026 (THE LINEUP BACKFILL LANDED, AND T30 IS PRE-REGISTERED ON IT BEFORE ANY FITTING — the reopening T29 authorised, on a NEW INPUT rather than a new specification)** — ✅ 🔴 **THE LINEUP BACKFILL IS COMPLETE: 176 DATES (2026-03-01 → 2026-08-23), 53,424 BATTER-GAMES, AND EVERY ONE OF THEM CARRIES A REAL BATTING SLOT — 41,472 of them genuine starters (`sub == 0`), 1,989 distinct players, and the slot distribution is near-uniform across 1–9, from 5,755 to 6,341 per slot.** 🔴 **LINEUP SLOT — the input T27, T28 and T29 all named as the missing variable and none of them had — IS NOW IN THE STACK.** ✅ **AND THE SIGNAL IS THERE, MONOTONIC ACROSS ALL NINE SLOTS: `P(1+ hit)` runs 65.7% · 66.2% · 64.8% · 62.4% · 61.2% · 60.6% · 58.6% · 55.9% · 53.6% from slot 1 to slot 9, on plate appearances of 4.50 down to 3.48 — A 12-POINT SPREAD ON THE OUTCOME, DRIVEN BY A FULL PLATE APPEARANCE OF DIFFERENCE.** ➡️ **That is precisely the mechanism the three failed hitter tests identified and could not see.** 🆕 🔴 **T30 OPENED AND PRE-REGISTERED BEFORE ANY FITTING — NOT ONE REGRESSION HAS BEEN RUN.** ✅ **IT IS THE REOPENING T29 AUTHORISED, AND IT IS AUTHORISED BECAUSE THE INPUT IS NEW, NOT BECAUSE THE SPECIFICATION IS: T29 closed hitter modelling and wrote the condition in advance — *"the reopening condition is a NEW INPUT — lineup slot above all — not a new specification."* That input now exists, and the backfill above was measured BEFORE the specification was written.** ⚠️ 🔴 **THE OPERATIONAL CATCH IS STATED BEFORE FITTING RATHER THAN DISCOVERED AFTER: THE LINEUP CARD IS POSTED ROUGHLY 2–3 HOURS BEFORE FIRST PITCH, SO THE 10:45am ET CARD CANNOT KNOW A 7pm GAME'S BATTING ORDER. Today's ACTUAL slot is therefore NOT a shippable feature on the morning card, and a test that used it and then claimed a live edge would be lying about what the model can see.** `[measured]` **A player's recent slot predicts today's slot with mean absolute error 1.04 slots (median 0.70) over 34,266 starts with 10+ prior starts; the rounded prediction is exactly right 39.9% of the time and within one slot 63.3%.** ➡️ **SO THE TEST HAS TWO ARMS AND ONLY ONE CAN SHIP: ARM A uses his TRAILING-20 MEAN BATTING SLOT, known at any hour, and could run on the 10:45am and 4:50pm cards as they stand; ARM B uses TODAY'S ACTUAL SLOT and can ship NOWHERE TODAY — only a card generated AFTER lineups post could use it, and Arm B is reported as an UPPER BOUND ONLY.** ⚠️ 🔴 **A LIKELY REASON ARM A FAILS IS WRITTEN DOWN NOW SO IT CANNOT BE CLAIMED AS A DISCOVERY LATER: THE INCUMBENT ALREADY CONTAINS MOST OF THE SLOT INFORMATION — a leadoff hitter's own smoothed hit rate is already the rate of a man getting 4.5 plate appearances a night, so slot adds value mainly when it CHANGES, and a change is exactly what the trailing mean cannot predict.** ✅ **THE SPECIFICATION IS FIXED NOW: target `P(H >= 1)`, THE SAME TARGET AS T27 deliberately, so the marginal value of the new input is isolated rather than confounded with a target change; sample = games the hitter STARTED by real batting order (`sub == 0`) — not T27's `pa > 0` sample and not a `pa >= 3` proxy — with >= 20 prior started games, the opposing starter resolved unambiguously and passing the trade-consistency check with >= 5 prior starts, POINT-IN-TIME throughout; THREE ESTIMATORS SCORED ON THE SAME HELD-OUT ROWS or the comparison is meaningless — the INCUMBENT smoothed rate recomputed on this sample, T27's four features refitted on this sample, and T27's features PLUS the new slot feature; logistic regression, ONE specification per arm; CHRONOLOGICAL split, train before 2026-07-15 and test from 2026-07-15 onward, the same split as T27/T28/T29.** **PASS (ARM A) = beats the INCUMBENT on Brier by >= 0.005 AND beats T27-refitted by >= 0.002 AND is not worse on log loss — BOTH MARGINS OR IT FAILS, because beating the incumbent while adding nothing over T27 would mean the SAMPLE changed, not that slot helped. PASS (ARM B) = the same two margins, REPORTED AS AN UPPER BOUND ONLY. FAIL = anything less, recorded FAILED, ship nothing.** ⛔ **FORBIDDEN: adding a feature beyond the one slot term, changing the 20-game window, moving the split, re-cutting the sample, or reporting Arm B as if it were live-usable.** 🔴 **IF ARM B PASSES AND ARM A FAILS, THAT IS A PRODUCT FINDING AND NOT A MODEL FINDING — it would mean the information is real and arrives too late for the card we currently publish, and the response would be a LATE CARD generated after lineups post, an OPERATIONAL change needing its own pre-registration before anything ships.** ⛔ **Do not quietly start using Arm B on the existing card.** 🔴 **AND IF ARM A PASSES, THAT IS STILL NOT PERMISSION TO PRINT A CONFIDENCE % — ledger rule 55 needs hitters to have their own calibration table with their own bands, and the pitcher bands do not transfer.** ⛔ **NO EXISTING ENTRY, PASS CRITERION, SPECIFICATION, STATUS ROW, PROGRESS COUNTER, MEASURED RESULT, CLOSED VERDICT OR DOC DEBT ITEM WAS ALTERED, RENUMBERED OR REMOVED — T1–T29 are byte-identical (T27's, T28's and T29's specifications, pass bars, forbidden lists and CLOSED-FAILED results all stand exactly as written), every Tier-3 row is untouched, EVERY DOC DEBT ROW IS UNTOUCHED, both un-numbered MEASURED FINDINGS are untouched, and the Closed-entries list is untouched. THIS WRITE IS A PURE INSERTION of T30 and this changelog entry, with ZERO lines lost.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session's transcript JSONL with a JSON walker rather than retyped → local file inside the working directory → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check, ZERO lines lost → full `project_read` AGAIN immediately before upload, rebasing if it had moved → upload with `local_path`, per ledger rule 43.** ⛔ **One doc touched this write — this one.**

- **Aug 24 2026, Monday sweep (TWO SCHEDULED-TASK PROMPTS RECORDED AS DEBT, BECAUSE AN UNATTENDED RUN CANNOT REPAIR ONE — a PURE INSERTION)** — 🔴 **TWO DOC DEBT ROWS ADDED, BOTH ⏳ AND DATED 2026-08-24, BOTH AGAINST SCHEDULED-TASK PROMPTS RATHER THAN DOCS.** **ROW 1 — the Monday sweep prompt (`trig_01Pgu7WoEsuipfVVQ41cff7S`): its v4.0 region tripwire still asserts the standing pull is `regions=us2` and nothing else, which has been INVERTED since 2026-08-23 when the standing set became FIVE BOOKS on `regions=us,us2` (ledger rule 48). Left as written, the sweep firing 2026-08-31 would FLAG every doc reading `regions=us,us2` and RE-NARROW THE WHOLE PROJECT back to Hard Rock only — the exact opposite of Sam’s instruction, done to the docs the 8/24 sweep just repaired. The edit owed is recorded in full: name NO region set, point at rule 48 as the OWNER, hunt disagreement in EITHER direction, keep struck history as history, confirm the `us_dfs` ban against rule 48, state the credit figure only as the formula `unique markets × regions`, and add the lesson that an enumerated list of instances is not a sweep. Three further items on the same prompt are recorded with it — statsapi is unreachable from a scheduled cloud run and the gap must be bounded from the repo’s own enumerated `final.json.gz` game counts and never from `WebFetch`; the code-sweep “THREE TIMES” becomes FOUR with the 2026-08-24 inverted case; and the Method section must verify the scheduled-task table against `list_triggers` every run. DEADLINE: before the next firing, 2026-08-31.** **ROW 2 — the 7:30am grading prompt (`trig_0115e9hbeLDiKToXgiUuyUFU`): JOB 1B hard-codes the machine card’s write times as 14:45Z and 21:50Z, where the crons in `.github/workflows/collect.yml` read `45 14` and `50 20` — 20:50Z, the whole evening cycle having moved. The edit owed is to DELETE the inline times and point at the workflow file, WITHOUT restating a new fixed pair, and to add that a missing `picks/<yesterday>.json` is a FINDING to be named by date rather than replaced with another date’s file.** 🔴 **AND THE STRUCTURAL FACT THAT PUTS THEM HERE AT ALL IS RECORDED ABOVE THE TWO ROWS, BECAUSE IT CHANGES WHAT THIS REGISTER IS FOR: A SCHEDULED TASK CANNOT REPAIR A SCHEDULED TASK. `update_trigger` returns `MCP tool call requires approval` and an unattended run has nobody to give it — measured 2026-08-24, the call made, refused, and both stored prompts afterwards re-read and byte-compared against their originals as UNCHANGED.** ➡️ **Every “check every trigger” tripwire in this project is therefore REPORT-ONLY from an unattended run, task-prompt debt lands in DOC DEBT where an unattended run CAN write, and it is cleared INTERACTIVELY.** ⛔ **NO TEST ENTRY, SPECIFICATION, PASS CRITERION, PROGRESS COUNTER, MEASURED RESULT OR CLOSED VERDICT WAS ALTERED, RENUMBERED OR REMOVED — T1–T29 ARE BYTE-IDENTICAL, every Tier-3 row is untouched, every PRE-EXISTING DOC DEBT row is untouched, both un-numbered MEASURED FINDINGS are untouched, and the Closed-entries list is untouched. THIS WRITE IS A PURE INSERTION of one note, two DOC DEBT rows and this changelog entry, with ZERO lines lost.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session’s transcript JSONL with a JSON walker rather than retyped → local file inside the working directory → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check, ZERO lines lost → `project_info` `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **Two docs touched this write — this one and `claude/betting-project-instructions.md`, whose v4.9 entry carried the FALSE claim that these two prompts had been corrected; it is struck and restated in the same turn (check 25).**

- **Aug 24 2026 (T29 FITTED AND FAILED — the third hitter specification to lose to a smoothed season average, and the PRE-COMMITTED CONSEQUENCE is triggered: HITTER MODELLING IS CLOSED)** — 🔴 **T29 CLOSED-FAILED. THE TOTAL-BASES MODEL WAS FITTED, MEASURED, AND DID NOT CLEAR ITS PRE-REGISTERED BAR: held-out Brier improvement over the shipping incumbent was +0.00119 against a declared +0.00500** (base rate 0.21943 → INCUMBENT smoothed rate 0.21695 → T29 model 0.21576 on 7,879 held-out rows; LogLoss 0.63076 → 0.62496 → 0.62223). **LogLoss improved by +0.00274 and clears its half of the criterion — THE CRITERION REQUIRED BOTH, so it FAILS, and by a WIDER MARGIN THAN T27 DID.** ⛔ **THE BAR WAS LEFT EXACTLY AS WRITTEN AND WAS NOT MOVED.** ⛔ **NOTHING SHIPPED — HITTER ROWS STILL CARRY NO CONFIDENCE RATING and keep the smoothed season rate, exactly as the FAIL branch of the specification says.** **THE SAMPLE WAS THE SAME AS T27 AND T28 BY DESIGN — 21,323 rows, 13,444 train / 7,879 test, held-out base rate 0.3242 — so all three are directly comparable.** **THE FIT, on standardised inputs: intercept −0.6635 (z −36.02); his mean PLATE APPEARANCES over the last 20, β 0.2499 (z 12.62) — DOMINANT AGAIN; the opposing starter's strikeouts per batter faced (PROXY), β −0.0746 (z −3.44); his own total bases per plate appearance over the last 20, β 0.0608 (z 3.19); the opposing starter's hits allowed per batter faced (PROXY), β 0.0352 (z 1.64 — NOT SIGNIFICANT); and home, β −0.0119 (z −0.65 — NULL, FOR THE THIRD CONSECUTIVE TEST).** ✅ **IT IS NOT A BROKEN FIT, AND THAT WAS CHECKED BEFORE THE FAILURE WAS RECORDED, AS WITH T27: in-sample gain +0.00379 against out-of-sample +0.00119 — a 3x shrinkage, more than T27's 1.5x, which is what five features on 13,444 rows will do, so THE OUT-OF-SAMPLE GAIN IS THE REAL ONE AND IT IS TINY; and held-out calibration is good — 20–25% → 20.5% (n=667) · 25–30% → 26.8% (n=1,516) · 30–35% → 31.2% (n=1,840) · 35–40% → 36.2% (n=2,332) · 40–45% → 41.2% (n=1,215), with only the 45–50% bucket (n=173) missing. THE MODEL IS HONEST. IT IS SIMPLY NOT BETTER BY THE BAR.** 🔴 **THE PRE-COMMITTED CONSEQUENCE — WRITTEN INTO T29 BEFORE THE RESULT WAS KNOWN — IS NOW TRIGGERED: HITTER MODELLING ON THIS DATA SET IS CLOSED, NOT JUST THIS TARGET. THREE PRE-REGISTERED SPECIFICATIONS ACROSS TWO DIFFERENT OUTCOMES HAVE NOW LOST TO A SMOOTHED SEASON AVERAGE: T27 (P(1+ hit), flat logistic) +0.00236, T28 (P(1+ hit), two-stage) +0.00127, T29 (P(TB >= 2), flat logistic) +0.00119 — every one of them against a +0.00500 bar.** ⛔ **DO NOT OPEN A FOURTH SPECIFICATION ON HITTER PROPS.** ➡️ **THE REOPENING CONDITION IS A NEW INPUT, NOT A NEW SPECIFICATION — LINEUP SLOT ABOVE ALL, AND IT IS NOT IN THE STACK. Hitter rows on the Picks tab stay 🔵 DESCRIPTIVE indefinitely: the player's own smoothed rate, no confidence number, no band.** ✅ **THE THROUGH-LINE ACROSS ALL THREE IS WORTH MORE THAN A MARGINAL MODEL WOULD HAVE BEEN: PLATE APPEARANCES ARE THE DOMINANT TERM IN EVERY HITTER TARGET TRIED — T27's P(1+ hit) put PA at β 0.258 per SD (z 14.24) and T29's P(TB >= 2) puts it at β 0.250 per SD (z 12.62) — AND THEY ARE THE THING WE CAN LEAST FORECAST, because T28, which tried to predict PA itself, returned RMSE 0.985 against a plate-appearance standard deviation of 1.13.** ➡️ **The biggest driver of a hitter's night is barely forecastable from what we hold. That is a CEILING on hitter props, not a failure of any one specification, and it should temper every future claim about this market.** ⚠️ **It is also, independently, what put bench bats at the top of the live board on 2026-08-23 until a lineup-share flag was added.** 🆕 🔴 **NEW MEASURED FINDING ADDED — AND IT IS EXPLICITLY NOT A TEST AND CARRIES NO T-NUMBER, because it is a COEFFICIENT READING off a model already fitted inside T29 rather than a pre-registration: FOR TOTAL BASES, THE OPPOSING STARTER'S STRIKEOUT RATE MATTERS MORE THAN HIS HITS-ALLOWED RATE. K/BF reads β −0.0746 at z = −3.44 while H/BF reads β +0.0352 at z = 1.64 and is NOT significant — a ball that is never put in play cannot become a total base, and the strikeout term is both larger and the only one of the two that clears significance.** ⚠️ **BOTH ARE PROXIES — the pitcher log carries no extra-base detail at all, so a true total-bases-allowed rate CANNOT be computed.** ⛔ **Do not describe either as one.** ➡️ **Practical read: on a hitter's over-1.5 total bases, WHO IS PITCHING matters mainly through his STRIKEOUT RATE, not through how many hits he gives up.** ⚠️ **HOME/ROAD IS NULL FOR HITTERS FOR THE THIRD CONSECUTIVE TEST (T27 z = −1.47, T28 home coefficient −0.0882, T29 z = −0.65), while the same term is SIGNIFICANT FOR PITCHERS in v4.0 (±0.151 K, t = 3.52).** ⛔ **Do not assume a term transfers across sides of the ball.** ⛔ **NO EXISTING ENTRY, PASS CRITERION, SPECIFICATION, PROGRESS COUNTER, MEASURED RESULT, CLOSED VERDICT OR DOC DEBT ITEM WAS ALTERED, RENUMBERED OR REMOVED — T29's SPECIFICATION, its PASS BAR and its FORBIDDEN LIST stand byte-for-byte as pre-registered and the result was ADDED BENEATH THEM; T27's and T28's entries, including their own specifications, bars, forbidden lists and CLOSED-FAILED results, are untouched; T1–T26 are untouched, every Tier-3 row is untouched, every DOC DEBT row is untouched, and the un-numbered home-field MEASURED FINDING is untouched. The only line replaced in this write is T29's STATUS line, which moves from PRE-REGISTERED/NOT RUN to CLOSED-FAILED.** ⚠️ **Merged, not rewritten: `project_read` → local file in a PRIVATE scratch directory inside the working directory → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check, the single dropped line being that intended STATUS replacement → `project_read` again in full immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **One doc touched this write — this one.**

- **Aug 24 2026 (T29 pre-registered — TOTAL BASES, the second half of Phase 2, written before a single regression was run)** — 🆕 🔴 **T29 OPENED: DOES A FITTED `P(TB >= 2)` BEAT THE RAW RATE?** ⛔ **PRE-REGISTERED BEFORE ANY FITTING — NOTHING HAS BEEN FITTED AND NOT ONE REGRESSION HAS BEEN RUN.** 🔴 **IT IS NOT A RE-RUN OF A CLOSED QUESTION: T27 and T28 both failed on `P(1+ hit)` and THAT TARGET IS CLOSED, but TOTAL BASES WAS ALWAYS THE OTHER HALF OF PHASE 2 AND HAS NEVER BEEN ATTEMPTED. It is a different problem — hits is a near coin-flip at 57.4%, which is precisely why a player's own smoothed rate was so hard to beat, because the incumbent already contained most of the signal.** ⛔ **This is not specification shopping on a closed target; it is the SECOND TARGET, on a DIFFERENT OUTCOME, with its own bar.** 🔴 **THE MARKET SET THE TARGET, NOT THE MODELLER: of 240 total-bases quotes on the live board, 236 ARE OVER/UNDER 1.5 and 4 are 3.5, so the target is `P(TB >= 2)` — the over-1.5 line — because that is the bet that actually exists.** ⛔ **Modelling a line the books do not post would be an academic exercise.** **THE RECONNAISSANCE, `[measured 2026-08-24 BEFORE the specification was fixed]`: total bases in a played game distribute 0 → 42.6%, 1 → 24.6%, 2 → 13.6%, 3 → 5.8%, 4 → 7.2%, 5+ → 6.3%, mean 1.352; thresholds read TB >= 1 (over 0.5) 57.4%, TB >= 2 (over 1.5) 32.8% — THE TARGET — and TB >= 3 (over 2.5) 19.2%.** ⚠️ **A base rate of 32.8% sits FURTHER FROM A COIN FLIP than hits did, so there is more separation available in principle: base-rate Brier is about 0.2204 against 0.2445 for the hits target.** ➡️ **State it alongside the results or the comparison is unreadable.** ⚠️ 🔴 **AN INPUT WE WANTED DOES NOT EXIST AND IS NOT BEING FAKED: the pitcher game log carries `hit`, `bb`, `k`, `bf`, `outs`, `er`, `np` and NO EXTRA-BASE DETAIL AT ALL, so a starter's TOTAL BASES ALLOWED CANNOT BE COMPUTED. Two available PROXIES are used in its place and are LABELLED as proxies — hits allowed per batter faced (contact allowed) and strikeouts per batter faced (balls never put in play).** ⛔ **Neither may be described as a total-bases-allowed rate.** ✅ **THE SPECIFICATION IS FIXED NOW: target `P(TB >= 2)` in a game where the hitter recorded at least one plate appearance; sample IDENTICAL to T27 and T28 by design so all three are comparable — `pa > 0`, hitter with >= 20 prior played games, opposing starter resolved unambiguously and passing the TRADE-CONSISTENCY CHECK, that starter with >= 5 prior starts, POINT-IN-TIME throughout; EXACTLY FIVE features and no interactions — his total bases per plate appearance over his last 20 played games, his mean plate appearances over the same 20, the opposing starter's hits allowed per batter faced (proxy), the opposing starter's strikeouts per batter faced (proxy), and home/road; logistic regression, ONE specification; CHRONOLOGICAL split, train before 2026-07-15 and test from 2026-07-15 onward, the same split as T27 and T28; incumbent = the same estimator that ships today at this line, the Jeffreys-smoothed `(h + 0.5) / (n + 1)` where `h` is his prior played games with `TB >= 2`, computed point-in-time. PASS = beats the incumbent on Brier by >= 0.005 on the held-out set AND is not worse on log loss. FAIL = anything less, recorded FAILED, ship nothing.** ⚠️ **THE SAME ABSOLUTE BAR AS T27, WHICH ON A 0.2204 BASELINE IS A SLIGHTLY HARDER RELATIVE BAR THAN IT WAS ON 0.2445 — DELIBERATE, because a bar that moves with the target is not a bar.** ⛔ **FORBIDDEN: adding a feature, changing the 20-game window, moving the split, re-cutting the sample, or switching to a different TB threshold after seeing the result.** 🔴 **PRE-COMMITTED CONSEQUENCE OF FAILURE, STATED BEFORE THE RESULT IS KNOWN: IF T29 FAILS, HITTER MODELLING ON THIS DATA SET IS CLOSED — not just this target. Three pre-registered specifications across two outcomes would have lost to a smoothed season average, and the honest conclusion is that the available inputs do not support a hitter model.** ➡️ **Hitter rows then stay 🔵 DESCRIPTIVE INDEFINITELY, and the reopening condition is a NEW INPUT — LINEUP SLOT above all — not a new specification.** 🔴 **AND IF IT PASSES, THAT IS STILL NOT PERMISSION TO PRINT A CONFIDENCE %: ledger rule 55 needs its own calibration table with its own bands for hitters, and the pitcher bands DO NOT TRANSFER.** ⛔ **NO EXISTING ENTRY, PASS CRITERION, SPECIFICATION, STATUS ROW, PROGRESS COUNTER, MEASURED RESULT, CLOSED VERDICT OR DOC DEBT ITEM WAS ALTERED, RENUMBERED OR REMOVED — T1–T28 are untouched (T27's and T28's specifications, pass bars, forbidden lists and CLOSED-FAILED results stand byte-for-byte), every Tier-3 row is untouched, every DOC DEBT row is untouched, the un-numbered home-field MEASURED FINDING is untouched, and the Closed-entries list is untouched. This write is a PURE INSERTION of T29 and this changelog entry, with ZERO lines lost.** ⚠️ **Merged, not rewritten: `project_read` → local file in a PRIVATE scratch directory inside the working directory → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → `project_read` again in full immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **One doc touched this write — this one.**

- **Aug 24 2026 (T28 FITTED AND FAILED — worse than T27; work on `P(1+ hit)` is STOPPED; and a new measured finding on home field for hitters)** — 🔴 **T28 CLOSED-FAILED. THE TWO-STAGE HITTER MODEL WAS FITTED, MEASURED, AND FAILED BOTH LEGS OF ITS PRE-REGISTERED BAR: held-out Brier 0.24121 against the T27 model's 0.24013 and the incumbent smoothed rate's 0.24248 on the SAME 7,879 held-out rows — −0.00108 against T27 (bar +0.00200) and +0.00127 against the incumbent (bar +0.00500).** 🔴 **IT FAILED WORSE THAN T27.** **The sample was IDENTICAL to T27 by design — 21,323 rows, 13,444 train / 7,879 test, base rate 0.5752 — so the two are directly comparable.** **STAGE 1, `E[PA]` by OLS: RMSE 0.985 train / 1.009 test against a plate-appearance sd of 1.13 — it barely predicts anything; intercept +3.8124, his trailing-20 PA +0.4866, team runs/game trailing 20 −0.0473 (near null AND the wrong sign), home −0.0882. STAGE 2, `P(hit per PA)` logistic and PA-weighted, league rate ≈ 0.2208: intercept −1.2640, his trailing-20 hits/PA +0.0387, opposing starter's H/BF +0.0359 — both terms tiny, so hits-per-plate-appearance is very close to unpredictable at this resolution.** 🔴 **WHY THE BETTER-MOTIVATED STRUCTURE LOST, RECORDED BECAUSE IT IS THE INSTRUCTIVE PART: splitting the problem forced two things on the model that the flat version never had to accept — a stage-1 `E[PA]` barely better than the mean, and the combination form `P(H >= 1) = 1 - (1-p)^E[PA]`, which ASSUMES plate appearances are independent trials at a constant rate. The flat logistic was free to learn the relationship instead of being told it.** ⛔ **A better-motivated structure is not automatically a better model.** 🔴 **THE EXPLICIT DECISION: STOP WORKING ON `P(1+ hit)`. Two pre-registered specifications have now failed and the incumbent smoothed season rate has beaten both by bars set in advance, so the honest reading is that this market has very little predictable structure left once a player's own smoothed rate is known. A THIRD SPECIFICATION WOULD BE SPECIFICATION SHOPPING — this project has recorded two headline coefficients that died exactly that way.** ⛔ **DO NOT OPEN T29 ON `P(1+ hit)`.** ➡️ **If hitters are revisited it must be on a DIFFERENT target (total bases, or a market with more spread) or with a genuinely NEW input — lineup slot being the obvious one, and it is not in the stack.** ✅ **WHAT THE TWO FAILURES BOUGHT: plate appearances are the DOMINANT term (T27, β 0.258/SD against 0.073 for hitting rate) and are ALSO nearly unpredictable (T28, RMSE 0.985 against sd 1.13) — the biggest driver of a hitter's night is the thing we can least forecast. That is a real ceiling on hitter props, not a failure of either specification, and it should temper any future claim about this market.** 🆕 🔴 **NEW MEASURED FINDING ADDED — AND IT IS EXPLICITLY NOT A TEST AND CARRIES NO T-NUMBER, because nothing in it was pre-registered: it is a DECOMPOSITION of a term already fitted inside T27. HOME FIELD IS A PLAYING-TIME TERM FOR HITTERS, NOT A HITTING TERM, AND IT RUNS AGAINST THE OVER.** **Decomposed over all 37,541 played rows: plate appearances per game 3.693 home against 3.840 road, −0.147 at z = −12.6; hits per plate appearance 0.21986 home against 0.21576 road, +0.0041 at z = +1.87; P(1+ hit) 57.30% home against 57.60% road, −0.30 points at z = −0.6.** ➡️ **Per plate appearance a home hitter is at most marginally better and z = 1.87 is NOT significant, but he gets 0.147 FEWER plate appearances at overwhelming significance, because the home team does not bat in the ninth when it is winning. The playing-time effect is roughly SEVEN TIMES LARGER IN z than the hitting effect and points the OTHER WAY.** ⛔ **Never treat "home" as a hitting bonus on a hitter prop — on an over it is a mild NEGATIVE.** ⚠️ **This is why a term cannot be assumed to transfer across sides of the ball: it is real and large for PITCHERS (v4.0, ±0.151 K, t = 3.52) and effectively absent — and inverted in mechanism — for hitters.** ⛔ **NOTHING SHIPPED. HITTER ROWS STILL CARRY NO CONFIDENCE RATING and keep the smoothed season rate, exactly as the FAIL branch of T28's specification says.** ⛔ **NO EXISTING ENTRY, PASS CRITERION, SPECIFICATION, PROGRESS COUNTER, MEASURED RESULT, CLOSED VERDICT OR DOC DEBT ITEM WAS ALTERED, RENUMBERED OR REMOVED — T28's SPECIFICATION, its PASS BAR and its FORBIDDEN LIST stand byte-for-byte as pre-registered and the result was ADDED BENEATH THEM; T27's entry, including its own specification, bar and forbidden list, is untouched; T1–T26 are untouched, every Tier-3 row is untouched, every DOC DEBT row is untouched. The only line replaced in this write is T28's STATUS line, which moves from PRE-REGISTERED/NOT RUN to CLOSED-FAILED.** ⚠️ **Merged, not rewritten: `project_read` → local file in a PRIVATE scratch directory inside the working directory → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check, the single dropped line being that intended STATUS replacement → `project_read` again immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **One doc touched this write — this one.**

- **Aug 24 2026 (T27 FITTED AND FAILED — the bar was not moved; T28 opened and pre-registered)** — 🔴 **T27 CLOSED-FAILED. THE FIRST HITTER MODEL WAS FITTED, MEASURED, AND DID NOT CLEAR ITS PRE-REGISTERED BAR: held-out Brier improvement over the shipping incumbent was +0.00236 against a declared +0.00500** (base rate 0.24446 → incumbent 0.24248 → T27 model 0.24013 on 7,879 held-out rows; LogLoss 0.68204 → 0.67828 → 0.67321). **LogLoss improved by +0.00508 and clears its half of the criterion — THE CRITERION REQUIRED BOTH, so it FAILS.** ⛔ **THE BAR WAS LEFT EXACTLY AS WRITTEN AND WAS NOT MOVED; the model IS better than the incumbent, just not by the margin declared in advance, and a margin chosen after seeing +0.00236 would not be a margin.** ⛔ **NOTHING SHIPPED — HITTER ROWS STILL CARRY NO CONFIDENCE RATING and keep the smoothed season rate, exactly as the FAIL branch of the specification says.** **THE SAMPLE, after the filters the specification fixed in advance: 21,323 usable rows — train 13,444 (base rate 0.5861) before 2026-07-15, test 7,879 (base rate 0.5752) from 2026-07-15 onward; dropped 9,060 for fewer than 20 prior played games, 4,786 for an opposing starter with under 5 prior starts, 1,379 for FAILING THE TRADE-CONSISTENCY CHECK and 993 for an ambiguous or missing starter.** ✅ 🔴 **THE TRADE-CONSISTENCY CHECK — the blocker T27 required to be built and to PASS BEFORE the fit — VALIDATED ITSELF: the schedule was rebuilt from the hitter logs (a (date, team, opponent) triple supported by 3+ different players is a real game; fewer is a player in the wrong place) and kept 3,862 DIRECTED TEAM-DAYS against the ~3,840 that thirty teams over roughly 128 dates should produce — WITHIN HALF A PERCENT OF THE TRUE SCHEDULE SIZE, which is what licenses using it as a filter.** 🔴 **THE HEADLINE FINDING IS NOT THE FAILURE — IT IS THAT PLATE APPEARANCES DOMINATE. On standardised inputs the trailing-20 mean PA carries β = 0.2580 (z = 14.24) against 0.0732 (z = 4.04) for his own hits-per-PA — roughly THREE AND A HALF TIMES the weight of how well he hits — and the currently shipped estimator ignores it completely.** ➡️ **It is also exactly what went wrong on the board on 2026-08-23, when bench bats with high under-rates topped the picks list until a lineup-share flag was added.** ⚠️ **HOME/ROAD IS NULL FOR HITTERS (β = −0.0260, z = −1.47) AND NEGATIVE — recorded because it is SIGNIFICANT FOR PITCHERS in the v4.0 model (±0.151 K, t = 3.52).** ⛔ **Do not assume a term transfers across sides of the ball.** ✅ **IT IS NOT A BROKEN FIT, AND THAT WAS CHECKED BEFORE THE FAILURE WAS RECORDED: in-sample gain +0.00351 against out-of-sample +0.00236 (similar magnitudes, so not overfitting — the predictable signal in `P(1+ hit)` really is this small); held-out calibration is excellent (45–50% → 48.0%, n=818 · 55–60% → 57.8%, n=1,713 · 60–65% → 61.8%, n=2,440 · 65–70% → 66.1%, n=1,214); the incumbent was hand-recomputed on a sampled row and matched to 12 decimal places, confirming it is genuinely point-in-time; and a 400-row recount of the outcome column found 2 apparent mismatches that were BOTH doubleheaders on 2026-08-17 and were the CHECK's naive indexing rather than the data — 276 player-dates in the pool carry two games.** 🆕 **T28 OPENED AND PRE-REGISTERED BEFORE ANY FITTING — model expected PLATE APPEARANCES first, then hits-per-PA on top: stage 1 `E[PA]` by OLS, stage 2 `P(hit per PA)` by logistic, combined as `P(H >= 1) = 1 − (1 − p)^E[PA]`; IDENTICAL filters to T27 including the trade-consistency check and the SAME chronological split at 2026-07-15, deliberately so the two are comparable; PASS = beats the T27 model on held-out Brier by >= 0.002 AND beats the INCUMBENT smoothed rate by >= 0.005, the same bar T27 had to clear; FAIL = anything less, recorded FAILED, ship nothing.** ⛔ **FORBIDDEN: re-using T27's held-out set to choose anything, changing the window, the split or the filters, and ADDING LINEUP SLOT — it is not in the data, and inventing a proxy after seeing T27's result is shopping.** ⚠️ 🔴 **PROMPTED BY T27'S OWN COEFFICIENT TABLE, NOT BY SHOPPING T27'S LEFTOVERS — and lineup slot remains the real missing variable, absent from the stack; trailing mean PA is a PROXY and must never be described as the slot. If a lineup source is ever added, that is a NEW test, not an amendment to T28.** ⛔ **NO EXISTING ENTRY, PASS CRITERION, SPECIFICATION, STATUS ROW, PROGRESS COUNTER, MEASURED RESULT, CLOSED VERDICT OR DOC DEBT ITEM WAS ALTERED, RENUMBERED OR REMOVED — T27's SPECIFICATION, its PASS BAR and its FORBIDDEN LIST stand byte-for-byte as pre-registered, and the result was ADDED BENEATH THEM; T1–T26 are untouched, every Tier-3 row is untouched, every DOC DEBT row is untouched. The only line replaced in this write is T27's STATUS line, which moves from PRE-REGISTERED/NOT RUN to CLOSED-FAILED.** ⚠️ **Merged, not rewritten: `project_read` → local file in a PRIVATE scratch directory inside the working directory → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check, the single dropped line being that intended STATUS replacement → `project_read` again immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **One doc touched this write — this one.**
- **Aug 24 2026 (T27 pre-registered — the FIRST HITTER TEST, written before a single regression was run)** — 🆕 🔴 **T27 OPENED: DOES A FITTED `P(1+ hit)` BEAT THE RAW RATE?** **Sam asked for hitter props on the Gizmo's Picks board on 2026-08-23; they shipped that night with NO confidence rating and NO calibration band, because there is no hitter model and ledger rule 55 forbids a MARKET number from wearing a Gizmo's %. Their number is the player's own season rate at the exact line with a Jeffreys prior — DESCRIPTIVE, explicitly not a projection.** ➡️ **T27 is what would let a hitter row carry a real number, and Sam chose the target himself: `P(1+ hit)`, the over-0.5-hits line — the most-bet hitter prop and a clean binary outcome directly comparable to the pitcher model's Brier score.** ✅ 🔴 **PRE-REGISTERED BEFORE ANY FITTING — NOTHING HAS BEEN FITTED, NOT ONE REGRESSION HAS BEEN RUN, AND THE SPECIFICATION IS FIXED: target `P(H >= 1)` on games with `pa > 0`; sample = hitter has >= 20 prior played games, opposing starter resolved UNAMBIGUOUSLY and passing the trade-consistency check, that starter has >= 5 prior starts, POINT-IN-TIME throughout; EXACTLY FOUR features and no interactions — his H/PA over his last 20 played games, his mean PA over the same 20, the opposing starter's hits allowed per batter faced over his prior starts, and home/road; logistic regression, ONE specification; CHRONOLOGICAL split, train before 2026-07-15 and test from 2026-07-15 onward, because a random split leaks the future into the past through the trailing windows; incumbent = the estimator SHIPPING TODAY, the Jeffreys-smoothed `(h + 0.5) / (n + 1)` computed point-in-time. PASS = beats the incumbent on Brier by >= 0.005 on the held-out set AND is not worse on log loss. FAIL = anything less, recorded FAILED, ship nothing, hitter rows keep the smoothed season rate and keep carrying no confidence number.** ⛔ **Adding a feature, changing the 20-game window, moving the split date or re-cutting the sample after seeing the first result is FORBIDDEN — specification shopping produced both of this project's worst errors.** **THE DATA RECONNAISSANCE, `[measured 2026-08-24 before any fitting]`: 453 hitters, 38,691 game rows, 37,541 with at least one plate appearance, 242 hitters with 80+ played games, league `P(1+ hit)` 57.4%, plate appearances per played game mean 3.77 / sd 1.13 / range 1–7, total bases per played game mean 1.35.** ✅ 🔴 **THE OPPOSING-STARTER JOIN WAS VERIFIED BEFORE THE SPECIFICATION WAS WRITTEN, AND IT IS THE REASON THIS IS WORTH DOING: the hitter log records only the opposing TEAM, the pitcher logs reverse onto it, and 95.7% of hitter rows (35,935) resolve to EXACTLY ONE opposing starter — 1.5% ambiguous, 2.8% unmatched. Without that join this would be a dressed-up season average.** ⚠️ 🔴 **THE TRADE-ATTRIBUTION DEFECT IS STATED UP FRONT AS A BLOCKER TO CLEAR RATHER THAN DISCOVERED LATER: the join keys on each hitter's CURRENT team for every historical row, so a TRADED hitter's pre-trade games are matched against the WRONG pitching staff, silently — Jo Adell is the live example, Cleveland now, 127 games — and part of the unmatched 2.8% is exactly this.** ⛔ **A consistency check must be built and must PASS BEFORE the fit, and rows that fail it are DROPPED, not guessed at.** ⚠️ **TWO INPUTS DO NOT EXIST AND THEIR ABSENCE IS RECORDED RATHER THAN WORKED AROUND — park factors (no venue in the hitter log) and LINEUP SLOT, which is the dominant driver of plate appearances and therefore the largest source of game-to-game variance the current estimator ignores entirely. Trailing mean PA is a proxy and is NOT the same thing.** 🔴 **AND IF IT PASSES THAT IS NOT PERMISSION TO PRINT A CONFIDENCE %: a passing Brier score earns the model a place in the pipeline, but whether a hitter row DISPLAYS a Gizmo's rating is a SEPARATE decision under ledger rule 55 and needs its own calibration table with its own bands — the pitcher bands DO NOT TRANSFER and may not be reused.** ⚠️ **The league base rate is 57.4%, so a model predicting the base rate for everyone already scores a Brier of about 0.245 — state the base-rate Brier alongside BOTH results or the comparison is unreadable.** ⛔ **NO EXISTING TEST ENTRY, PASS CRITERION, SPECIFICATION, STATUS ROW, PROGRESS COUNTER, MEASURED RESULT, CLOSED VERDICT OR DOC DEBT ITEM WAS ALTERED, RENUMBERED OR REMOVED — T1–T26 are untouched, every Tier-3 row is untouched, every DOC DEBT row is untouched, and the Closed-entries list is untouched. This write is a PURE INSERTION of T27 and this changelog entry, with ZERO lines lost.** ⚠️ **Merged, not rewritten: `project_read` → local file in a PRIVATE scratch directory inside the working directory → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → `project_read` again and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **One doc touched this write — this one.**
- **Aug 23 2026 (T26 pre-registered — is the outs market's error ASYMMETRIC? — and a night-clustering check run once, which cuts in Sam's favour)** — 🆕 🔴 **T26 OPENED: DO OUTS UNDERS LOSE MORE THAN OUTS OVERS?** **The carded record splits hard by market — strikeouts 26/38 (68.4%) against outs 8/17 (47.1%), a 21-point gap — and on 8/22 the outs half went 1/5.** ✅ **SPECIFICATION WRITTEN BEFORE THE DATA IS TOUCHED: on the full season, point-in-time, split every carded-style outs threshold into UNDERS and OVERS and compute the calibration gap SEPARATELY for each side; threshold set every half-integer outs line 11.5–20.5; the model is v4.0's `mu` with the shipped `Normal(mu, cvO × season mean outs)` assumption. PASS = the two gaps differ by ≥ 8 percentage points, in a consistent direction, on ≥ 300 starts per side. FAIL = anything less, recorded FAILED, nothing changed.** ⛔ **NOT RUN, NOT ADOPTED, AND NOT TO BE RUN EARLY — it belongs to the September re-fit, and the 8/22 slate may NOT be used as evidence either way because that slate is the reason the question was asked.** ⚠️ **If it passes, the fix is in the DISTRIBUTION and not in a new term: run T3 first, because an asymmetric error is what a wrong tail shape looks like.** ✅ 🔴 **THE NIGHT-CLUSTERING CHECK WAS RUN ONCE, ON ONE SPECIFICATION STATED BEFORE IT RAN, AND IT SUPPORTS SAM'S READ RATHER THAN THE MODEL'S — RECORDED FIRST BECAUSE IT CUTS THAT WAY.** `[measured 2026-08-23]` **residual `r = actual outs − his own trailing-8 mean outs`, point-in-time, starts only, ≥5 prior starts, grouped by calendar date: 2,531 starts across 115 dates with 8+ starters each; season mean residual −0.07 outs, within-day SD 3.76, SD of daily MEAN residuals 0.894 against 0.828 expected under INDEPENDENCE, ratio 1.079, implied INTRACLASS CORRELATION 0.008 — effectively no night-level clustering — and 8/22's daily mean outs residual was +0.046, RANK 57 OF 115, dead average.** ➡️ **The league's starters went their normal length on 8/22; the two arms Sam bet did not. That is the shape of variance, not of model bias.** ✅ **AND A SECOND, FREE RESULT THAT MATTERS FOR PAIRS: at an ICC of 0.008 two starters' outs residuals on the same night are effectively INDEPENDENT, so STEP 6's joint probability — which multiplies two blends — is NOT overstating on cross-game outs legs. The independence assumption survives its first check.** ⚠️ **One season, one specification: a check passed, not a law.** ⚠️ 🔴 **THE PITCH-COUNT OBSERVATION IS CARRIED WITH ITS POST-HOC CAVEAT ATTACHED, NOT AS A FINDING: the same specification on `numberOfPitches` puts 8/22 5TH OF 115 dates at +4.97 pitches per starter, 21 of 26 starters above their own trailing mean, sign test one-sided p = 0.0012 — BUT THE DATE WAS CHOSEN AFTER THE LOSS, roughly 0.3 of 115 dates are expected this extreme by chance, and night-level ICC on pitch counts is 0.013.** ⛔ **Suggestive, NOT a finding, and NOTHING IS RE-PRICED ON IT.** ⛔ **NO EXISTING TEST ENTRY, PASS CRITERION, SPECIFICATION, STATUS ROW, PROGRESS COUNTER, MEASURED RESULT, CLOSED VERDICT OR DOC DEBT ITEM WAS ALTERED, RENUMBERED OR REMOVED — T1–T25 are untouched, every Tier-3 row is untouched, every DOC DEBT row is untouched, and the Closed-entries list is untouched. This write is a PURE INSERTION of T26 and this changelog entry, with ZERO lines lost.** ⚠️ **Merged, not rewritten: `project_read` → local file in a PRIVATE scratch directory inside the working directory → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → `project_read` again and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **One doc touched this write — this one.**
- **Aug 23 2026, 7:30am scheduled run (four counters advanced, one DOC DEBT row closed, and T15's margin leg clears for the first time)** — ⛔ **NO OPEN TEST, PASS CRITERION, SPECIFICATION, MEASURED RESULT OR CLOSED VERDICT WAS ALTERED, REORDERED OR DROPPED. This write advances progress counters, appends update blocks inside four entries, closes one DOC DEBT row and adds this entry. T1–T3, T6–T10, T12–T14, T16–T22 and T25 are untouched, and every snapshot table is left exactly as written.** 🔴 **T15 — n = 31 CARDED PLAYS AND THE MARGIN LEG CLEARS FOR THE FIRST TIME: argmin `w = 1.00` (PURE MODEL) at Brier .2245 against .2338 at the shipped 0.5, a margin of 0.0094 against a bar of 0.005.** ⛔ **THE `n` LEG FAILS (31 against 100) AND THE 50/50 IS NOT TOUCHED.** ⚠️ **Both reasons the cleared margin must not be read as a result are recorded in the entry: the argmin has moved 0.7 → 0.74 → 1.00 across three slates and has landed ON THE BOUNDARY of the parameter space, and the mechanism is one bad slate — on 8/22 raw was the more optimistic estimate on 10 of 13 plays and the card went 6/13, so pure model wins for being the LOWER number on a losing night.** ➡️ **This is precisely the failure the `n ≥ 100` leg exists to absorb.** 🔴 **T11 — n = 25 STARTS AND THE HYPOTHESIS HAS TURNED OVER. The 20–40% bucket that read 29.6 / 47.4 on 8/20 alone, which was this entry's entire basis, reads 29.5 / 25.6 merged across 25 named starts; 60–70% reads 64.3 / 60.0 and 70–80% reads 76.0 / 70.0 — both now slightly OVER-confident, the direction the carded calibration table has always pointed.** ⛔ **NOT re-decided; the pass criterion is untouched and on current evidence heads for a FAIL.** ⚠️ **T4 — n = 17 and the bucket got WORSE for a second consecutive run: 6/17, 35.3% actual against 64.9% predicted, gap −29.6 from −25.9 and −22.5.** 🔴 **AND THE FIRST DIRECT EVIDENCE THAT THE PROPOSED FIX WOULD NOT HAVE BEEN ENOUGH IS RECORDED IN THE ENTRY BEFORE IT IS DECIDED: on 8/22 the plays carded AT OR ABOVE 70% went 5/9 against a mean estimate of 79.5%, so a 70% carding floor would have left a 5/9 card.** ⛔ **One slate; the specification, the n ≥ 30 bar and the decision date are unchanged.** 🆕 **T23 / T24 — THE SHARED OUTS-PLAY COUNTER IS OPENED AT 5 / 30, with the counting convention stated so a future run does not re-base it: the entries opened on 2026-08-22 with the counter at zero, so the 8/22 card's five outs plays are the first five and they are NAMED — Skubal u18.5 ❌, Irvin u15.5 ❌, H. Brown u17.5 ✅, M. Pérez o14.5 ❌, Cease u17.5 ❌, 1 of 5 against a mean carded estimate of 62.8%.** ⛔ **No variant and no axis is chosen; both three-way comparisons and the September decision date stand.** ✅ 🔴 **DOC DEBT CLOSED — `claude/mlb-opponent-database.md` now records that a SECOND, machine-rebuilt copy of the opponent metric lives on the GitHub Actions runner, names BOTH centering constants (4.7376 published / 4.7756 on the runner's 8/23 pull), both populations, the measured agreement (mean |Δ E[K]| 0.021 K, max 0.064 K) and an explicit prohibition on computing across them — and states that this does NOT retire the published table.** ✅ **Verified in place in the same turn (ledger rule 37).** ⚠️ 🔴 **ONE FINDING FROM THIS RUN IS RECORDED IN `claude/pick-ledger.md` AND `claude/calibration-accumulators.md` RATHER THAN HERE, BECAUSE IT IS A CARD-BUILD FAILURE AND NOT A REGISTER ITEM: TWO OF THE THIRTEEN 8/22 PLAYS WERE REMATCHES SIX DAYS OLD (Weathers vs TOR and Cease vs NYY, both last faced 2026-08-16) AND NEITHER ROW STATED THE GAP — a pre-publish check 36 failure.** ⛔ **T18's pre-registered specification stays FAILED and closed, its replacement specification is untouched, and the two new instances are logged in the rule-51 accumulator as EXPLORATORY observations that point in OPPOSITE directions.** ⚠️ **Merged, not rewritten: `project_read` → local file in a PRIVATE scratch directory → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check → `project_info` `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⚠️ 🆕 **The local copy was verified before any patch: TWO INDEPENDENT transcriptions of the `project_read` result were written to separate files and diffed byte-for-byte (90,743 bytes, 657 lines, identical).** ⛔ **Four docs touched this run — `claude/pick-ledger.md`, `claude/calibration-accumulators.md`, `claude/mlb-opponent-database.md` and this one.**
- **Aug 23 2026 (T23 and T24 are APPLIED IN CODE — and that is not the same thing as adopting them; T25 becomes collectable)** — ✅ 🔴 **T23 AND T24 ARE NOW APPLIED IN `card.py`, WHICH GENERATES THE DAILY CARD UNATTENDED ON THE GITHUB ACTIONS RUNNER: the raw hit rate is computed on ALL STARTS with NO 4+IP FILTER (T23), and the matched class is selected on the DURABILITY axis for outs props and the K axis for strikeout props, with the grouping variable POINT-IN-TIME (T24).** 🔴 **WHAT THAT MEANS AND DOES NOT MEAN IS STATED IN BOTH ENTRIES RATHER THAN LEFT TO BE INFERRED: T23 AND T24 WERE FINDINGS ABOUT HOW TO *MEASURE*, NOT NEW MODEL TERMS.** **Neither ever carried a coefficient; both only ever decided which starts got COUNTED in a descriptive rate or which pitchers sat in a comparable pool.** ✅ **Removing a provably biased filter, and pooling the right pitchers, is a CORRECTION — so applying them is NOT adopting an unadopted test.** 🔴 **BY CONTRAST T21 AND T22 REMAIN NOT ADOPTED, AND THE CODE ENFORCES IT: `blend` is the plain 50/50 and is the only column entering calibration, `carried` carries the T21/T22 flags and enters NO denominator, and `verify_card.py` has a check that FAILS THE BUILD if `blend` is ever anything but the plain 50/50.** ⛔ **NEITHER T23 NOR T24 IS CLOSED: their three-variant and three-axis comparisons are still owed, still decided at the September re-fit, and still need n ≥ 30 outs plays. Both progress counters stay at 0/30.** ⚠️ 🔴 **ONE DELIBERATE RESTRAINT RECORDED IN T24: the automated `carried` applies NO discretionary nudge toward the matched class, although the 8/22 hand-built card nudged some rows by hand — because folding a FLAG into a NUMBER, even a third of the way, WOULD be a new model choice with no pre-registered test.** ✅ **T25 IS NOW COLLECTABLE GOING FORWARD: the Phase-0 collector stores `board.json` every 30 minutes with de-vigged implied team totals, which resolves this entry's "there is no odds store" blocker from 2026-08-22 onward.** ⛔ **IT STILL CANNOT BE BACKFILLED, its specification and pass criterion are untouched, the term is in NO model, and its progress counter stays at 0 — storage is not collection, and counting a capability as a sample would be exactly the drift this register exists to stop.** 🆕 **DOC DEBT ADDED: `claude/mlb-opponent-database.md` NOW HAS A SECOND, NIGHTLY, MACHINE-REBUILT COPY OF ITS OWN METRIC LIVING IN THE RUNNER — rebuilt from the same pull the model reads, with its constant taken from that same rebuild, because the published table can only be rebuilt in an interactive browser session and goes stale a slate at a time.** `[measured 2026-08-23]` **3,802 IP-filtered starts, mean \|ΔE[K]\| 0.021 K, max 0.064 K.** ⛔ **THE TWO CONSTANTS MUST NEVER BE MIXED — 4.7376 published, 4.7756 on the runner's 8/23 pull — and this does NOT retire the published table.** ⛔ **NO OPEN TEST, PASS CRITERION, SPECIFICATION, MEASURED RESULT, PROGRESS COUNTER OR CLOSED VERDICT WAS ALTERED, REORDERED OR DROPPED — T1–T22 are untouched, every Tier-3 row is untouched, every existing DOC DEBT row is untouched, and the Closed-entries list is untouched. This write is a PURE INSERTION of three in-entry blocks, one DOC DEBT row and this changelog entry.** ⚠️ **Merged, not rewritten: `project_read` → local file in a PRIVATE scratch directory → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check → `project_info` `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **Four docs touched this write — this one, `claude/pick-ledger.md`, `claude/gizmos-picks-spec.md` and `claude/mlb-data-stack.md`.**
- **Aug 22 2026 (T25 pre-registered — Sam's team-total insight, and the first pre-registered test whose predictor comes from the MARKET)** — 🆕 🔴 **T25 OPENED: THE MARKET'S IMPLIED TEAM TOTAL AS A MODEL INPUT. Sam: *"if a book puts a run total on a team at 2.5 at -150 odds that means the opposing pitcher will probably pitch a good game"*.** 🔴 **THE ARGUMENT IS THAT THE MODEL HAS ALMOST NO OPPONENT VIEW AT ALL — its only one is that lineup's mean strikeouts, and the opponent→outs channel is a MEASURED NULL at t = −0.34, so the outs model has no working opponent term whatsoever.** ➡️ **A posted team total embeds the starter, the bullpen, the park, the weather, that day's lineup and the umpire — every input this project lacks — priced by better-informed participants and compressed into one number, AND IT COSTS 6 CREDITS FOR A WHOLE SLATE off the bulk endpoint.** ✅ **SPECIFICATION WRITTEN BEFORE THE DATA IS TOUCHED: collect the opposing team's DE-VIGGED implied total (from `totals` + `spreads`) for every start going forward; test it as one added term against (a) the outs model and (b) the strikeout model; pass = \|t\| ≥ 2.0 AND an out-of-sample improvement in mean absolute error; decided at the September re-fit; single specification, no second look.** ⚠️ 🔴 **THE HAZARD IS STATED IN THE ENTRY ITSELF RATHER THAN DISCOVERED LATER: this is a MARKET-DERIVED predictor, so if it works the model is partly reproducing the book rather than beating it, and the edge will be smaller than the coefficient looks. REPORT PERFORMANCE WITH AND WITHOUT THE TERM, ALWAYS.** ⛔ **It may never reach the product surface as a 🟢 MODEL input without that caveat — ledger rule 55, added the same day.** 🔴 **AND IT CANNOT BE BACKFILLED: historical odds are a separate, more expensive API product, so the test accumulates only from the day collection begins.** ➡️ **START COLLECTING IMMEDIATELY, BEFORE ANY MODEL WORK — every uncollected day is a day the test cannot reach `n`.** 🆕 **DOC DEBT ADDED: ODDS ARE NOT STORED ANYWHERE. Line movement, T25 and any closing-line-value work all depend on a store that does not exist; every pull this project has made was read once and discarded, which is why LINE VALUE still reads n=0. The store is a Phase-1 item in the new `claude/gizmos-picks-spec.md`.** 🆕 **`claude/gizmos-picks-spec.md` CREATED the same day (v0.1, SPEC ONLY, NOTHING BUILT) and 🔴 LEDGER RULE 55 ADDED — a MARKET-derived number is never presented as a MODEL projection.** ⛔ **NO OPEN TEST, PASS CRITERION, SPECIFICATION, MEASURED RESULT OR CLOSED VERDICT WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of T25, one DOC DEBT row and this entry.** ⚠️ **Merged, not rewritten: `project_read` → local file in a PRIVATE scratch directory → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check → re-read and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **Four docs touched this write — this one, `claude/gizmos-picks-spec.md`, `claude/pick-ledger.md` and `claude/mlb-data-stack.md`.**
- **Aug 22 2026 (T24 pre-registered — the SECOND structural defect found in STEP 4B in one day, and again it was Sam who found it)** — 🆕 🔴 **T24 OPENED: STEP 4B SELECTS COMPARABLES BY `±1.5 K/9`, AND FOR AN OUTS MARKET THAT IS THE WRONG AXIS.** **K/9 is near-orthogonal to start length, so a `±1.5 K/9` band mixes workhorse aces with short-leash arms and the resulting "matched class" was never a number about pitchers like the one being priced.** **Sam: *"how many of those pitchers are tiers above ryan johnson, this is an important thing to catch for trying to snipe these types of pitchers for an under"*.** ✅ **REBUILT ON TRAILING MEAN OUTS, POINT-IN-TIME — each comparable's own prior-8 mean as of that start, so the GROUPING VARIABLE CARRIES NO LOOKAHEAD, which is the discipline T22's struck season-long role label already taught this register.** 🔴 **THE GRADIENT IS THE ARGUMENT, across 88 starts vs Texas: trailing mean outs under 14 → u15.5 hits 55.6%; 14–16 → 44.4%; 16–18 → 30.8%; 18+ → 30.8%. FIFTY-TWO OF THE 88 (59%) CAME FROM 16+ OUTS PITCHERS HITTING ONLY 31%, and that is what dragged the pooled figure to 50%.** 🔴 **IT MOVED A PLAY SAM HAD ALREADY BET: Irvin u15.5 vs MIA goes 50.0%/55.2% → 66.7% (18/27), which AGREES with the model's 61.8% instead of contradicting it — the "the class kills this bet" verdict delivered to him was an artifact of the wrong comparison group read through T23's subtract-only filter.** **Johnson u15.5 vs TEX 50.0% → 56.5% (13/23); Skubal u18.5 vs PIT 82.1% → 77.5% (31/40).** ⚠️ **The opponent effect SURVIVES the fix and is real — 66.7% vs Miami against 56.5% vs Texas at near-identical durability.** ✅ **SPECIFICATION WRITTEN BEFORE FURTHER DATA IS TOUCHED: compare three selection axes for OUTS markets — (a) `±1.5 K/9`, (b) `±1.5` trailing mean outs point-in-time, (c) both jointly — adopt whichever minimises mean absolute calibration gap, at n ≥ 30 outs plays, decided at the September re-fit. KEEP `±1.5 K/9` for STRIKEOUT markets unless (c) wins there too.** 🔴 **T23 AND T24 MUST BE RESOLVED TOGETHER — both affect the same outs-market figure and BOTH BIAS THE SAME DIRECTION, against outs unders.** ⛔ **NOT ADOPTED NOW. Only the REPORTING ORDER changed on 2026-08-22 — the durability-matched point-in-time figure is the headline on outs markets, the K/9-matched figure sits beside it as the legacy number — and NO carded estimate moved (Irvin stays 70.9%, Skubal 66.4%; ledger rule 34).** 🆕 **DOC DEBT ADDED: `pitchHand` IS NOT A FIELD IN THE WORKING DATASET and had to be fetched live from `people?personIds=…&fields=people,id,fullName,pitchHand,code`; adding it to THE RECIPE's pull is now owed.** ⚠️ **The exploratory cut that fetch produced is recorded WITH ITS LABEL ATTACHED, not as a result: comparable RHP vs CWS 13/13 at 4+ K against LHP 6/9, every miss a lefty. ⛔ Post-hoc, not pre-registered, n=13, and T21 says 13/13 delivers ~89% not 100%.** 🔴 **RECORDED BECAUSE IT CUTS AGAINST THE PROCESS: this is the SECOND structural defect found in STEP 4B in a single day and NEITHER WAS FOUND BY A CHECK — T23 surfaced because Sam asked about a second u15.5 play, T24 because he asked what tier the comparables were.** ⛔ **NO OPEN TEST, PASS CRITERION, SPECIFICATION, MEASURED RESULT OR CLOSED VERDICT WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION.** ⚠️ **Merged, not rewritten: `project_read` → local file → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check → upload with `local_path`, per ledger rule 43.** ⛔ **Two docs touched this write — this one and `claude/pick-ledger.md`.**
- **Aug 22 2026 (T23 pre-registered — the matched-class outs filter is provably biased, and it is a derivation rather than a measurement)** — 🆕 🔴 **T23 OPENED: STEP 4B's `outs ≥ 12` ("4+IP") split CAN ONLY DELETE WINNERS AND NEVER A SINGLE LOSER ON ANY OUTS UNDER AT A THRESHOLD OF 12 OR HIGHER.** **For an under at `T`, a loss is `outs > T`; if `T ≥ 12` every loss already clears the filter with certainty while winners below 12 outs are all removed, so the filtered rate is a STRICT LOWER BOUND — guaranteed by arithmetic, on every slate, for every pitcher. Mirror-image upward bias on overs.** 🔴 **DERIVED, NOT MEASURED — it is a property of the FILTER, so it has been corrupting every outs-under class figure this project has printed since STEP 4B was introduced.** ⚠️ **Severity scales with how far `T` sits above 12 — modest at `u18.5` (why 8/21's Sale row read 90.5%), large at `u15.5`, the most common outs rung on the board.** 🔴 **TWO PLAYS WERE MISREPRESENTED TO SAM ON 2026-08-22 AND BOTH AGAINST THE BET: Irvin u15.5 delivered as 46.9% (23/49) against an unbiased 55.2% (32/58), and Ryan Johnson u15.5 read at 38.5% (20/52) against an unbiased 50.0% (32/64).** ⚠️ **The Irvin flag SURVIVES either way — 55.2% is still well below his carded 70.9% blend.** ⛔ **IT DOES NOT APPLY TO STRIKEOUT MARKETS — a short outing is a plausible loss for a K over and a plausible win for a K under, so the filter is not provably biased there and STEP 4B is UNCHANGED for strikeouts.** ✅ **SPECIFICATION WRITTEN BEFORE THE DATA IS TOUCHED AGAIN: compare three variants of the outs-market matched class — (a) the current `outs ≥ 12` filter, (b) no filter at all, (c) a filter removing only starts ended by injury or ejection — and adopt whichever has the smallest mean absolute calibration gap, at n ≥ 30 outs plays, decided at the September re-fit.** ⛔ **NOT ADOPTED NOW. Only the REPORTING ORDER changed on 2026-08-22 — ALL-STARTS is the headline on outs bets at `T ≥ 12` and the 4+IP figure carries "biased by construction" — and NO probability was recomputed, NO carded estimate moved.** ⚠️ **Cross-referenced to the 2026-08-22 entry in `claude/pick-ledger.md`.** ⛔ **NO OPEN TEST, PASS CRITERION, SPECIFICATION, MEASURED RESULT OR CLOSED VERDICT WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION.** ⚠️ **Merged, not rewritten: `project_read` → local file → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check → upload with `local_path`, per ledger rule 43.** ⛔ **Two docs touched this write — this one and `claude/pick-ledger.md`.**
- **Aug 22 2026 (two entries closed on Sam's explicit decisions)** — ✅ 🔴 **T5 CLOSED AS DECIDED — conversational picks now enter calibration. Sam: *"include them"*.** **Closed as DECIDED rather than passed or failed, because T5 asked a question about a RULE and not a hypothesis about the world.** ✅ **Decided ON PRINCIPLE and BEFORE the bucket filled — the bar this entry set itself, in its own words.** ⚠️ 🔴 **It cuts AGAINST the model and that is recorded first: applied in `claude/pick-ledger.md` the same day, the 60–70% bucket went 5/12 → 5/13, actual 41.7% → 38.5%, gap −22.5 → −25.9, and the 70–80% bucket went 15/19 → 16/20, +3.8 → +4.8. Calibration total n = 38 → 40; exclusions 5 → 3.** **Two of the five conversational picks entered (G. Williams 76.8% W, G. Rodriguez 66.6% L, both carrying a logged PREGAME estimate); three did not — Skenes `[estimate unlogged]`, Messick o4.5 `[no PREGAME estimate]`, Sasaki o4.5 a 🔴 DUPLICATE of a carded row.** ⛔ **No estimate was invented or back-filled.** ⚠️ **T4's 60–70% counter updated 12 → 13, its n ≥ 30 bar UNCHANGED and still not adopted.** ⚠️ **T15's specification is explicitly UNCHANGED by T5 — its denominator stays CARDED PLAYS, and widening it would need its own pre-registration.** ✅ 🔴 **DOC DEBT — the `claude/pick-ledger.md` "Table B" row CLOSED. Sam: *"close it"*.** **Recorded at closure: the referent was identified from primary evidence (the superseded 7:30am task prompt) as the 8/19 midday card — 5 plays, `[pre-correction]`, graded 4/5, excluded from calibration by design; the five play rows are permanently lost and will not be reconstructed; every total in the ledger reconciles without them; and Sam closed it explicitly on 2026-08-22.** ⛔ **The data-loss record itself is NOT deleted — it stays in the ledger as the evidence behind rules 42–44.** ⛔ **NO OPEN TEST, PASS CRITERION, SPECIFICATION, MEASURED RESULT OR CLOSED VERDICT WAS ALTERED, REORDERED OR DROPPED.** ⚠️ **Merged, not rewritten: `project_read` → local file → programmatic patch with uniqueness-asserted anchors (7 anchors, every one verified to occur EXACTLY ONCE before any write) → `collections.Counter` line-loss check, every dropped line an intended replacement → upload with `local_path`, per ledger rule 43.** ⛔ **Only three docs were touched this session — this one, `claude/pick-ledger.md` and `claude/card-blueprint.md`.**

---

## T36. 🆕 CFB — does `ahead_out_lastwk` earn its place, given it is a LAGGED and imperfect injury signal?

`[opened Aug 30 2026 — from Sam's own week-to-week point]`

**The observation.** Sam: *"as the season goes on you will see more players get involved especially if there are injuries to anybody up on the depth chart in front of said players."* ✅ Correct — and the NFL layer already prices it as `ahead_out` off the Wednesday injury report. ⛔ **College publishes no injury report at all: `/player/injuries` returns HTTP 404.**

⛔ **MECHANISM STRUCK AND REPLACED 2026-08-30, BEFORE ANY FITTING — see the amendment at the foot of this entry.** ~~**The mechanism.** Absence is observable *after the fact*. A player who averaged a high snap share and took **zero snaps last week** was out last week~~, and that is a fact about a COMPLETED game — so it is knowable before this week's kickoff and is point-in-time legal. `ahead_out_lastwk` = the count of players ranked ahead of this one at his position who were absent in the most recent completed week.

⛔ **IT IS NOT THE NFL FEATURE.** NFL `ahead_out` knows **today's** status. This one knows **last week's**, so it is wrong every time a player returns this week or goes down on game day. **It must not share the NFL name and must not be compared to NFL results.**

**THE SPECIFICATION, FIXED NOW, BEFORE ANY CFB DATA IS FITTED:**
- Population: Power 4 only (67 teams), seasons 2021–2025, **weeks 4+ only** (weeks 1–3 have too little trailing history to rank depth).
- Positions: RB, WR, TE. **QB excluded** — a backup QB is a different offence, not a depth promotion, and mixing them would hide the effect being tested.
- Target: the same per-game production targets the NFL layer uses.
- Comparison: the identical model **with** and **without** `ahead_out_lastwk`, everything else held constant.
- Validation: **held-out by SEASON, not by row.** Fit on 2021–2023, test on 2024–2025. ⛔ Row-wise splitting leaks a team's own season into its own test set.
- **PASS = out-of-sample improvement on the held-out seasons, on a pre-declared error metric, in BOTH held-out seasons independently.** ⛔ **One season improving and the other not is a FAIL, not a partial pass.**
- ⚠️ **ONE SPECIFICATION. NO SWEEP.** If it fails it is logged FAILED and closed. **The project has already lost a headline coefficient (v3.4 outs, +0.188 → t=−0.02) to exactly the temptation to try another cut.**

**What a pass would mean.** That the injury cascade survives the 404 in lagged form. **What a fail would mean:** that college role change is too fast, or too invisible without a status report, for last week's absence to carry it — in which case CFB simply does not get the feature and the docs say so plainly.

### 🔴 AMENDMENT, 2026-08-30 — THE MECHANISM DOES NOT EXIST. THE TEST IS RE-SPECIFIED **BEFORE** ANY DATA IS FITTED.

`[measured 2026-08-30 04:47Z, probe report read from the repo]` **`/plays` returns 29 keys and NOT ONE OF THEM NAMES A PLAYER** — no `player`, `athlete`, `participant`, `personnel` field of any kind. The only player reference anywhere in a play record is inside **`playText`, free prose.**

⛔ **THEREFORE THERE IS NO SNAP COUNT FOR COLLEGE FOOTBALL AT ALL.** Not a weak one, not a proxy — none. `playText` names only the players **involved in the play**, so it yields **TOUCHES, never SNAPS**, and a receiver who ran a route and was not thrown to is invisible in it.

➡️ **RE-SPECIFIED:** `ahead_out_lastwk` = the count of players who ranked ahead of this one **by trailing per-game TOUCHES** and who **recorded no box-score line at all last week.**
⚠️ ⛔ **THIS IS A STRICTLY WEAKER SIGNAL AND THE WEAKNESS MUST BE STATED WHEREVER THE FEATURE IS USED:** a healthy WR who simply drew zero targets is **indistinguishable from a WR who did not dress.** For RBs and QBs the signal is far cleaner than for WRs and TEs.
✅ **EVERYTHING ELSE IN THE SPECIFICATION ABOVE IS UNCHANGED** — same population, same positions, same season-held-out validation, same both-seasons-must-improve pass bar, same one-specification rule.
✅ **LEGITIMACY OF THIS EDIT:** the test **has not been run and no CFB data has been fitted.** The revision is forced by what the API does not publish, **not by a result.** ⛔ **After the first fit, this entry is frozen.**

### 🔒 THE LAST UNDECLARED PIECE, DECLARED 2026-08-30 05:36Z — **BEFORE THE FIRST FIT**

The spec above said *"a pre-declared error metric"* and never named one. ⛔ **An unnamed metric is a metric chosen after the fact.** Naming it now, with **no model yet run on CFB data of any kind:**

- **Rows:** seasons 2021–2025, **regular season only, weeks 4–15.** Postseason excluded (bowl opt-outs make absence mean something entirely different).
- **Filters, all declared now:** `depth_rank` present · `opp_elo` present · **`trailing_usage` ≥ 3.0** (the frozen T37-CFB floor). ⚠️ 2021 loses ~7.35% of rows to missing Elo; that is **stated, not silently absorbed.**
- **Positions fitted SEPARATELY:** RB, WR, TE. **QB excluded** per the original spec.
- **Target:** RB → `rush_yds`; WR and TE → `rec_yds`. A missing target on a row that exists is **0**, not a dropped row.
- **Baseline features:** `trailing_usage`, `depth_rank`, `opp_elo`, `home`.
- **Test model:** the baseline **plus `ahead_out_lastwk`. Nothing else changes.**
- **Estimator:** ordinary least squares. No regularisation, no transforms.
- **Metric: MEAN ABSOLUTE ERROR** on held-out rows.
- **Fit:** 2021–2023 pooled. **Test: 2024 and 2025 SCORED SEPARATELY.**
- **PASS for a position = MAE strictly lower WITH the feature, in BOTH 2024 and 2025.** ⛔ **One season improving and the other not is a FAIL for that position, not a partial pass.**

⛔ **ONE RUN. NO VARIANTS.** If it fails it is logged FAILED and closed. **The project lost v3.4's headline coefficient (+0.188, t=4.95 → t=−0.02) to exactly the urge to try one more cut, and the GOOD-tier P/PA result to ~10 specifications.**

### ⛔ CLOSED — RUN ONCE, 2026-08-30 05:38Z. **RB FAILED · TE FAILED · WR PASSED THE LETTER AND NOTHING ELSE.**

| pos | fit n | 2024 base → +f | 2025 base → +f | verdict |
|---|---|---|---|---|
| RB | 3,694 | 26.3568 → **26.3734** | 28.3905 → **28.4078** | ⛔ **FAIL — worse in both** |
| WR | 3,034 | 29.7672 → 29.7627 | 29.8941 → 29.8810 | ✅ **PASS by the criterion** |
| TE | 480 | 23.1123 → **23.1319** | 22.1977 → **22.2175** | ⛔ **FAIL — worse in both** |

🔴 **THE WR "PASS" IS WORTH NOTHING, AND SAYING SO IS NOT RE-DECIDING THE TEST.**
1. ⛔ **The effect is 0.0045 and 0.0131 YARDS of MAE.** On a ~30-yard error that is **four ten-thousandths of the error.** It is not a betting edge; it is not distinguishable from noise.
2. 🔴 **AND THE SIGN IS BACKWARDS.** `coef = −1.1389`. The hypothesis was *a receiver ahead of you is out, so you get more*. **The fitted coefficient says a receiver ahead of you being out is associated with FEWER receiving yards.** ⛔ **A wrong-signed coefficient that improves MAE by a hundredth of a yard is noise wearing a result's clothes.** (RB's coefficient is `+0.6203` — the *right* sign — and it made both held-out seasons **worse**.)

➡️ **DECISION: `ahead_out_lastwk` IS NOT CARRIED INTO THE CFB MODEL.**
⚠️ **This is a decision to be MORE conservative than the pre-registration required, not a rescue of a failure**, and the distinction matters: the register may never be used to promote a loser, and declining to bank a meaningless winner costs nothing. **The number that passed is recorded above exactly as it fell.**

📌 **THE LESSON, AND IT IS A DEFECT IN MY OWN PRE-REGISTRATION:** the pass criterion had **NO MINIMUM EFFECT SIZE.** "Strictly lower in both held-out seasons" is satisfiable by four ten-thousandths of a yard. ⛔ **A bar that any coin-flip-sized improvement clears is not a bar.** ➡️ **EVERY FUTURE ENTRY IN THIS REGISTER MUST DECLARE A MINIMUM EFFECT SIZE ALONGSIDE ITS DIRECTION TEST.** ⛔ This applies to entries opened from now on; **it does NOT retroactively change T36's recorded verdict.**

📌 **WHAT IT MEANS FOR THE SPORT, NOT FOR THE FEATURE.** Sam's mechanism — *"injuries to anybody up on the depth chart in front of said players"* — is real in the NFL, where `ahead_out` is read off a **same-week injury report**. ⛔ **The college version could only ever see LAST WEEK, and could not tell a player who did not dress from one who played and was never thrown to.** That ambiguity is not a modelling weakness that a better fit would overcome; **it is the signal being absent from the data.**

⛔ **NOTHING ABOUT THIS TEST MAY BE RE-DECIDED AFTER THE DATA IS SEEN.**

## T37-CFB. 🆕 Are the NFL snap floors valid on college?

`[opened Aug 30 2026]`
⚠️ Not to be confused with verify_card check **T37**, a different namespace.

**The observation.** The depth-rank build inherits QB .60 / RB .30 / WR .50 / TE .40. **Those floors were fit on the NFL.** ⛔ **Inheriting a bar is not the same as pre-registering one** — and college rosters are deeper, blowouts are more common, and starters sit earlier.

~~**THE SPECIFICATION, FIXED NOW:** before any CFB model is fitted, plot the snap-share distribution by position for Power 4, 2021–2025, weeks 4+. **PASS = the NFL floor sits in the same relative position of the college distribution (within 10 percentage points of the same quantile).** Otherwise the floor is **re-set from the college distribution ONCE, at the matching quantile, and that value is then frozen.**
⛔ **The floor is set from the DISTRIBUTION ONLY. It may never be tuned against model performance** — that is specification shopping wearing a different hat.~~

### 🔴 AMENDMENT, 2026-08-30 — THE TEST AS WRITTEN IS UNANSWERABLE. RE-SPECIFIED **BEFORE** ANY FIT.

`[measured 2026-08-30 05:04Z, five seasons built and audited]` The entry above asks whether **the NFL snap floor sits at the same quantile of the college snap distribution.** ⛔ **THERE IS NO COLLEGE SNAP DISTRIBUTION.** `/plays` carries no player field at all, so no snap share exists to compare against. **The question is not hard; it is undefined.**

⚠️ **This is a data-availability fact, not a result** — the same standing as T36's amendment. **No CFB model has been fitted.**

➡️ **RE-SPECIFIED, AND THE VALUE IS NOT YET COMPUTED:**
- The floor applies to **`trailing_usage`** (trailing TOUCHES per game), the only usage quantity college publishes.
- **It is set at the 25th percentile of `trailing_usage` among rows that ALREADY pass the depth-rank cap** (`VS_DEPTH`: QB 1, RB 2, WR 3, TE 2), **computed on the FITTING SEASONS ONLY — 2021, 2022, 2023 — then FROZEN and applied unchanged to 2024 and 2025.**
- ⛔ **Computing it on all five seasons would let the held-out seasons set their own admission bar.** That is leakage, and it is subtle enough to survive a code review.
- **Reason for p25, declared now:** the floor exists to remove cameos, not to trim the sample. A player who has already earned a top-2 or top-3 trailing rank at his position and still sits in the bottom quarter of that group's usage is a rotational body, not a starter.
- ⛔ **ONE VALUE. It may never be re-set against model performance, and it may never be re-derived after a fit.**

### 🔒 FROZEN, 2026-08-30 05:27Z — THE FLOOR IS **3.0 TOUCHES PER GAME**

`[measured from the v6 run, `data/ncaaf/latest/probe-report.json`]`
**`trailing_usage` p25 among rows already passing the depth-rank cap, fitting seasons 2021–2023 only: n = 11,380 · p10 2.0 · p25 3.0 · p50 5.0 · p75 13.5 · p90 32.3 · max 62.0.**

⛔ **THE FLOOR IS 3.0 AND IT IS NOW CLOSED.** It was computed exactly as specified above, on 2021–2023 alone, **before a single model was fitted**, and it may never be re-derived, re-tuned, or re-argued against model performance.

✅ **Confirmed unaffected by the coverage defect found in the same run:** the ~300 `' Team'` pseudo-rows per season carry no position, so they never entered the player set and never entered this pool. **Fixing that defect does not move this number.**

⚠️ **APPLIED AS METADATA, NOT AS A DELETION.** The floor travels on the file as `usage_floor: 3.0`; the rows below it are **kept**. ⛔ A build that silently dropped them would make the bar unauditable and would destroy the only sample on which it could ever be re-examined — and re-examining it is forbidden anyway, so the data must survive for anyone checking that the rule was followed.

📌 **`[measured, for the record, BEFORE the floor is chosen]`** all-rows `trailing_usage`-adjacent distribution of per-game touches, 2025: **p10 1 · p25 2 · p50 4 · p75 8 · p90 24 · max 69.** ⚠️ **This is the ALL-ROWS distribution and is NOT the number the floor is taken from** — the floor comes from the post-depth-rank subset, which has not been computed.

---

## T38. 🆕 CFB — how many games before a defence's `vs-position` row means anything?

`[opened AND specified 2026-08-30 05:42Z, BEFORE the measurement was run]`

**The observation.** `vs-position-2025` holds **159 defences** for a 67-team scope, because Power 4 offences play G5 and FCS opponents. ⛔ **Every row in that table is a POWER 4 OFFENCE'S performance**, so a non-P4 defence can be described by **a single game** — and *"what this defence allows a WR1"* built from one night against Alabama is a fact about **Alabama**.

**THE SPECIFICATION, FIXED NOW:**
- Data: `vs-position-2021…2025`, **WR depth-slot 1** (the highest-volume slot), metric **`rec_yds` allowed**.
- For each (defence, season) with at least `2k` rows: mean over the **first k games by week** vs mean over **the remaining games**. Pooled across all five seasons.
- **Pearson r between the two halves, as a function of k, for k = 1…6.**
- **MINIMUM GAMES = the smallest k whose r ≥ 0.35.**
- ⛔ **PRE-COMMITTED NEGATIVE ANSWER:** if **no k up to 6 reaches 0.35**, the finding is that **a defence-level `vs-position` row is not reliable at all** and the table must be **pooled** (by conference, or by opponent-Elo band) rather than read per-defence. **That outcome is logged as the result, not treated as a failed run to be retried with a different metric.**
- ⛔ **ONE RUN. NO SWEEP OVER METRICS, POSITIONS OR SLOTS.**

📌 **Why a threshold and not a model test:** this is a **reliability property of the data**, in the same class as T37-CFB's usage floor. ⛔ **It may never be tuned against model performance** — that would be specification shopping in a lab coat.

---

## T39. 🆕 🔴 THE SAME QUESTION, ASKED OF THE **NFL** LAYER — because T38 says the college version carries no per-defence signal at all

`[opened AND specified 2026-08-30 05:44Z, BEFORE the measurement was run]`

**Why this must be asked.** T38 returned its **pre-committed negative answer**: across k = 1…5 the split-half correlation of a college defence's WR1 receiving yards allowed is **0.03, 0.06, 0.05, −0.02, −0.07** — indistinguishable from zero at every game count. ⛔ **`vs-position` is the SAME CONSTRUCT the NFL layer is built on.** If it is noise there too, then a core component of the NFL model is noise, and **we would rather find that out from a reliability check than from losing money.**

⚠️ **I would rather this come back positive.** ⛔ **That is exactly why the bar is written down before the run.**

**THE SPECIFICATION — IDENTICAL TO T38, DELIBERATELY:**
- Data: `data/nfl/latest/vs-position-2021…2025`, **WR depth-slot 1**, metric **`rec_yds` allowed**.
- For each (defence, season) with at least `2k` rows: mean over the **first k games by week** vs mean over **the remaining games**. Pooled across the five seasons.
- **Pearson r as a function of k, k = 1…6.**
- **PASS = some k ≤ 6 reaches r ≥ 0.35** — the same bar as T38, unchanged.
- ⛔ **PRE-COMMITTED NEGATIVE ANSWER:** if no k reaches it, **the NFL `vs-position` table is also unreliable read per-defence**, and that is logged as the result. ⛔ **No re-cut to a different metric, position, slot or season set to find a friendlier number.**
- ⛔ **ONE RUN.**

📌 **Whatever this returns, the interpretation of BOTH tests is bounded in advance:** a raw per-game total allowed is heavily driven by **which offence turned up**. An unreliable raw table therefore points at **opponent adjustment**, not at abandoning the construct — but ⛔ **any adjusted version is a NEW pre-registered test, never a re-cut of T38 or T39.**

---

## ⛔ T38 AND T39 — BOTH CLOSED, BOTH NEGATIVE, RUN ONCE EACH ON 2026-08-30

### THE RESULT

**Split-half r of a defence's WR1 `rec_yds` allowed — first k games vs the rest:**

| k | CFB r | NFL r |
|---|---|---|
| 1 | 0.0315 | 0.0004 |
| 2 | 0.0622 | 0.1109 |
| 3 | 0.0456 | 0.0930 |
| 4 | −0.0243 | 0.0955 |
| 5 | −0.0670 | −0.0053 |
| 6 | *too few* | 0.0090 |

⛔ **NEITHER REACHES 0.35 AT ANY GAME COUNT. BOTH PRE-COMMITTED NEGATIVE ANSWERS STAND.**
🔴 **AND THE NFL RESULT IS THE SERIOUS ONE.** The NFL sample is *clean* — 160 defence-seasons, 12–14 games each, no G5/FCS contamination, real snap-share depth ranking. **It is the strongest version of this test that exists in the project, and it returns zero.**

### ✅ THE POSITIVE CONTROL — because a null this large has two explanations, and one of them is a broken ruler

Same instrument, same code, applied to quantities whose stability nobody disputes:

| series | k=1 | k=3 | k=5 |
|---|---|---|---|
| CFB — a WR's own `rec_yds` | 0.4251 | 0.5678 | 0.5549 |
| CFB — a WR's own `rec` | 0.5614 | 0.6551 | 0.6357 |
| NFL — a WR's own `rec_yds` | 0.6121 | 0.7622 | 0.7705 |
| **NFL — a WR's own `snap_pct`** | **0.8001** | **0.8054** | **0.8149** |

✅ **THE RULER WORKS.** It finds **r = 0.80** on NFL snap share. ⛔ **So the defence-level zero is the world, not the method.**

### 📌 WHAT THIS DOES AND DOES NOT SAY

⛔ **It does NOT say defences are all the same.** It says **a defence's RAW per-game total allowed to a WR1 in one half of a season does not predict the other half.** That is a statement about the **measure**, not about defensive quality.
➡️ **The obvious culprit was named before the run and is not a rescue: a raw total allowed is dominated by WHICH OFFENCE TURNED UP.** Alabama's WR1 and Purdue's WR1 are not the same test.
⛔ **Any opponent-adjusted version is a NEW pre-registered test. It is NOT a re-cut of T38 or T39.**

### 🔴 THE CONSEQUENCE FOR BOTH MODELS, STATED PLAINLY

1. ⛔ **A raw `vs-position` row must not be read as a per-defence property — in EITHER sport.** The minimum-games question T38 was opened to answer is **moot: no game count fixes it**, and shipping a "minimum 4 games" rule would have been **false comfort**, the exact failure mode of probe v1.
2. ✅ **Player-level trailing form is where the predictable signal lives** — r 0.43–0.78 across both sports, on the same instrument, in the same run.
3. 🔴 **AND IT QUANTIFIES THE CFB HANDICAP EXACTLY.** The single most reliable input in the entire project is **NFL snap share, r = 0.80** — and **college publishes no snap data at all.** Its best available substitute, receptions, sits at **0.56–0.66.** ⛔ **That gap is not a modelling problem to be engineered away. It is the difference between the two datasets.**

---

## 📌 CORRECTION LOGGED 2026-08-30 05:49Z — I REPORTED THE WRONG ELO COLUMN

⛔ **What I told Sam:** *"2021 Elo is 7.35% missing (513 rows), every other season is 0.0%."*
🔴 **That measured `elo` — the player's OWN team rating.** The column that goes into a model is **`opp_elo`, the opponent-strength control**, and it is missing on:

| season | own `elo` missing | **`opp_elo` missing** |
|---|---|---|
| 2021 | 7.3% | **7.8%** |
| 2022 | 0.2% | **8.6%** |
| 2023 | 0.0% | **8.6%** |
| 2024 | 0.0% | **9.2%** |
| 2025 | 0.0% | **10.0%** |

⛔ **NOT "one bad season." EVERY season, and RISING.** Every missing row is an FCS opponent (Southern, MVFC, Coastal Athletic, OVC-Big South, Southland).

📌 **THIS IS THE SAME FAILURE FAMILY AS THE PARITY PROBES THAT SAID 20 AND THEN 7:** a number was measured about something **adjacent to the question** and reported as the answer. ➡️ ⛔ **BEFORE REPORTING A COLUMN'S COMPLETENESS, CHECK THAT IT IS THE COLUMN THE MODEL WILL READ.**

✅ **It does not change any verdict.** T36 required `opp_elo` present, so those rows were already excluded from the fit; T38/T39 do not use Elo at all. **The correction is to the reporting, not to a result.**

---

## T40. 🆕 IS CFBD'S PAID WEATHER TIER WORTH BUYING? — asked of the NFL, where weather is FREE

`[opened AND specified 2026-08-30 05:56Z, BEFORE the measurement was run]`

**The decision.** `/games/weather` returns **HTTP 401 — paid tier.** ⛔ **Buying a feed to find out whether it helps is the wrong order.** The NFL layer already carries weather on **100% of rows** (`roof`, `surface`, `temp`, `wind`; temp and wind present on 12,175 of 18,961 rows — the rest are domes). **Measure it there, for free, and let that decide the purchase.**

⚠️ **THIS IS EVIDENCE, NOT PROOF.** College is not the NFL: more outdoor stadiums, wider geography, and a run-heavier average offence. ⛔ **A null in the NFL does not prove weather is worthless in college — it proves we should not PAY for it on a hunch.** That distinction is the whole finding either way.

**THE SPECIFICATION, FIXED NOW:**
- Data: `data/nfl/latest/players-2021…2025`, **outdoor games only** (`roof == "outdoors"`), rows with `temp` and `wind` both present.
- Positions fitted **separately**: QB (`pass_yds`), RB (`rush_yds`), WR (`rec_yds`).
- Rows: weeks 4+, `snap_pct` ≥ the existing NFL floor for the position, `depth_rank` present.
- **Baseline features:** `tgt_share` (or `snap_pct` for QB/RB), `depth_rank`, `home`.
- **Test model:** baseline **plus `temp` and `wind`. Nothing else changes.**
- Estimator: ordinary least squares. Metric: **MAE.**
- **Fit 2021–2023, test 2024 and 2025 SCORED SEPARATELY.**
- 🔴 **PASS = MAE lower in BOTH held-out seasons AND the improvement is at least 1.0% of the baseline MAE**, in at least one position.

⛔ **THE 1% MINIMUM EFFECT SIZE IS THE T36 LESSON APPLIED.** T36's WR arm "passed" on **0.0045 yards** — four ten-thousandths of the error — because the criterion had no floor. **A bar that any coin-flip clears is not a bar.** This is the first entry written under the new rule.

### ⚠️ AMENDMENT 2026-08-30 05:57Z — `depth_rank` IS NOT ON NFL PLAYER ROWS. AMENDED **BEFORE ANY NUMBER WAS SEEN.**

`[measured from `data/nfl/latest/players-2024.json.gz`]` The row schema is `d · week · team · o · home · game_id · ol_out · opp_dl_out · wx · inj · tgt · rec · rec_yds · rec_td · tgt_share · ay_share · ay · car · rush_yds · rush_td · att · cmp · pass_yds · pass_td · int · snaps · snap_pct · ahead_out · tgt_per_snap`. ⛔ **There is no `depth_rank`** — `nfl.py` computes rank inside `build_vs_position` and never writes it back to the player file. **The filter as written was unsatisfiable and the run died on an empty array before printing a single figure.**

➡️ **AMENDED: `depth_rank` is dropped from the filter and from the feature set.** ✅ **The snap floor already does the job `depth_rank` was there for** — establishing that the player was a starter that week. **Everything else — positions, targets, seasons, estimator, metric, the 1% minimum gain — is unchanged.**
✅ **Legitimacy: no result had been produced.** The script raised a `ValueError` on a zero-row matrix; **no MAE, no coefficient, and no verdict existed to be influenced by.**

- ⛔ **ONE RUN. NO SWEEP.** If it fails, the recommendation is **do not buy CFBD's weather tier**, and `wx` is **dropped from the CFB feature set and documented as dropped** rather than left as a column that is silently always null.

### ⛔ T40 CLOSED — FAILED. **DO NOT BUY CFBD'S WEATHER TIER.** Run once, 2026-08-30 05:57Z.

| pos | fit n | 2024 base → +wx | Δ% | 2025 base → +wx | Δ% | verdict |
|---|---|---|---|---|---|---|
| QB | 753 | 54.201 → 53.938 | **+0.49%** | 58.951 → 57.754 | **+2.03%** | ⛔ **FAIL — 2024 under the 1% floor** |
| RB | 1,250 | 26.265 → 26.237 | +0.11% | 26.553 → 26.578 | **−0.09%** | ⛔ FAIL |
| WR | 2,069 | 20.870 → 20.872 | **−0.01%** | 21.398 → 21.223 | +0.82% | ⛔ FAIL |

🔴 **THE QB ARM IS THE CLOSE ONE AND IT IS NOT BEING RESCUED.** It improved in **both** seasons and the wind coefficient is **−1.5675 yards per mph** — the right sign and a sensible size. ⛔ **It still fails, because 2024's gain was 0.49% against a declared 1.0% floor.** **That floor is the T36 lesson and it exists precisely for results that look like this one.**

⚠️ **Two reasons to believe the FAIL rather than the near-miss:**
1. **The 2025 test set is 305 rows.** A 2% MAE difference on 305 rows is comfortably inside noise, and the 2024 arm — 300 rows — gave 0.49%. **The two held-out seasons disagree by a factor of four on the same effect.**
2. ⛔ **The baseline here is deliberately thin** (snap share + home). **Adding a variable to a weak baseline flatters it**, so the real gain against our actual model would be **smaller than 0.49%, not larger.**

➡️ **DECISION: `wx` IS DROPPED FROM THE CFB FEATURE SET AND DOCUMENTED AS DROPPED** — not left as a column that is silently always null.
📌 **What this does NOT say:** it does not say weather is irrelevant to football. It says **we will not pay for a feed on the strength of an effect this size.** ⚠️ College has more outdoor stadiums, wider geography and a run-heavier average offence, so **the NFL is evidence here, not proof** — that was written down before the run and it holds now that the answer is inconvenient.

---

## T41. 🆕 🔴 THE QUESTION T38/T39 FORCED — does OPPONENT ADJUSTMENT rescue `vs-position`, in either sport?

`[opened AND specified 2026-08-30 05:58Z, BEFORE the measurement was run]`

**Why it must be asked.** T38 and T39 showed a defence's **raw** WR1 yards allowed has **no** split-half reliability (r ≈ 0 at every k, both sports), while the same instrument found **r = 0.80** on NFL snap share. The named culprit — written down *before* those runs — is that **a raw total is dominated by WHICH OFFENCE TURNED UP.** ⛔ **This is the test of that explanation, and it is a NEW test, not a re-cut.**

**THE SPECIFICATION, FIXED NOW:**
- For every `vs-position` **WR slot-1** row, compute a **residual**: the receiver's `rec_yds` in that game **minus his own mean `rec_yds` across his OTHER games that season** (leave-one-out, so a player cannot be correlated with himself).
- Per (defence, season): the **mean residual**. Split-half exactly as T38/T39 — first k games by week vs the rest, k = 1…6, pooled across 2021–2025.
- **Run on BOTH `data/ncaaf/latest` and `data/nfl/latest`.**
- **PASS = r ≥ 0.35 at some k ≤ 6**, the same bar as T38/T39, unchanged.
- ⛔ **PRE-COMMITTED NEGATIVE ANSWER: if adjustment does not rescue it, `vs-position` is DROPPED as a per-defence input in BOTH sports**, and the NFL model is changed accordingly. **That is logged as the result — not retried with a third adjustment.**
- ⛔ **ONE RUN.**

⚠️ **This is a DIAGNOSTIC, not a forecast.** The leave-one-out mean uses the whole season and is therefore **not point-in-time** — that is legitimate for measuring whether a defence-level signal *exists at all*, and ⛔ **it would be illegal in a model.** If T41 passes, the model version must be rebuilt **point-in-time** and re-tested separately.

### ⛔ T41 CLOSED — FAILED IN BOTH SPORTS. `vs-position` IS DROPPED AS A PER-DEFENCE INPUT. Run once, 2026-08-30 05:58Z.

Split-half r of a defence's **opponent-adjusted** WR1 yards allowed, with the raw number carried alongside as a control:

| k | CFB adj | CFB raw | **NFL adj** | NFL raw |
|---|---|---|---|---|
| 1 | 0.0411 | 0.0523 | 0.1393 | −0.0096 |
| 2 | 0.0357 | 0.0614 | 0.1454 | 0.0852 |
| 3 | 0.0357 | 0.0973 | **0.1782** | 0.1268 |
| 4 | −0.0188 | 0.0149 | 0.1172 | 0.1185 |
| 5 | −0.0919 | −0.1733 | 0.0374 | −0.0006 |

⛔ **NOTHING REACHES 0.35. THE PRE-COMMITTED NEGATIVE ANSWER STANDS.**

✅ **THE DIAGNOSIS WAS RIGHT AND IT STILL DID NOT SAVE IT.** Adjustment roughly **doubles** the NFL signal (0.13→0.18 at k=3 against 0.09 raw), which confirms that *which offence turned up* really was contaminating the raw table. **It is simply not enough.** ⛔ **CFB does not move at all** (~0.04), which is what a sport with no snap data and receptions-as-usage should look like.

🔴 **AND 0.18 IS AN UPPER BOUND, NOT AN ESTIMATE.** The leave-one-out mean **uses the whole season, including the future.** ⛔ **A legitimate point-in-time version can only score LOWER than 0.18.** The honest ceiling on this construct is worse than the number in the table.

### ➡️ THE CONSEQUENCE, AND IT CHANGES A LIVE MODEL
1. ⛔ **`vs-position` is no longer a per-defence input in EITHER sport.** The NFL model must be changed; **leaving it in, now that this is known, is the one option that is not available.**
2. ✅ **The data is NOT deleted.** It stays built, stamped with this verdict, and remains the sample anyone would need to re-examine the claim.
3. ➡️ **Opponent quality must come from TEAM-LEVEL measures, not position-slot allowed tables** — points and yards allowed, or a rating. 🟢 **CFB already carries exactly that: `opp_elo`, pregame and point-in-time legal.** ⚠️ **The NFL layer has no equivalent and now needs one.**
4. ⛔ **Any team-level opponent measure is a NEW pre-registered test.** ⚠️ **Three constructs have now failed in a row — `ahead_out_lastwk`, raw `vs-position`, adjusted `vs-position`. That is not bad luck; it is what an unfalsifiable pipeline looks like when it finally gets tested.** ➡️ **Test the next one BEFORE building on it, not after.**

---

## T42. 🆕 IS A **TEAM-LEVEL** DEFENSIVE MEASURE RELIABLE, WHERE THE POSITION-SLOT ONE WAS NOT?

`[opened AND specified 2026-08-30 06:02Z, BEFORE the measurement was run]`

**Why this is the right next question.** T41 left a hole: opponent quality has to come from **somewhere**, and it cannot come from `vs-position`. The obvious candidate is a **team-level total** — every yard a defence allowed, not just the slot-1 receiver's. ⚠️ **And there is a real reason to expect it to behave differently: pooling a whole team's production per game averages away far more noise than one receiver's line does.** ⛔ **That is a hypothesis, not a reason to skip the test.**

📌 **RELIABILITY FIRST, VALUE SECOND — and that ordering is the point.** Three constructs have now failed consecutively because they were **built first and tested later.** ⛔ **Nothing is built on this until it clears a reliability bar.**

**THE SPECIFICATION, FIXED NOW:**
- Measure: **total yards from scrimmage allowed per game** = Σ(`rush_yds` + `rec_yds`) over every opposing player in that game. ⚠️ `pass_yds` is **excluded on purpose** — it double-counts receiving yards.
- Per (defence, season), ordered by week. **Split-half exactly as T38/T39/T41**: first k games vs the rest, k = 1…6, pooled 2021–2025.
- **Run on BOTH sports.**
- ⚠️ **CFB CAVEAT, DECLARED NOW:** our CFB file holds **Power 4 offences only**, so a defence's total is computable **only for games against a Power 4 offence** (~8–9 a season) and the CFB arm is restricted to **Power 4 defences**. **The NFL arm is complete and is the cleaner test.**
- **PASS = r ≥ 0.35 at some k ≤ 6** — the same bar as T38, T39 and T41, unchanged.
- ⛔ **PRE-COMMITTED NEGATIVE ANSWER, AND IT IS A BIG ONE:** if a team-level total is **also** unreliable, then **defensive identity is not measurable from box scores at all**, and the architecture becomes **player-form-only with no opponent term derived from our own data.** ⛔ **That conclusion is logged and acted on — not retried with a fifth construct.**
- ⛔ **ONE RUN.**

⚠️ **A PASS HERE IS NOT A LICENCE TO USE IT.** Reliability means the measure is *stable*, not that it *predicts player production*. **Incremental value is a separate pre-registered test, with a minimum effect size, per the T36 lesson.**

### ⛔ T42 CLOSED — **CFB PASSES. NFL FAILS.** Run 2026-08-30 06:02Z.

⚠️ **DISCLOSURE FIRST, BECAUSE IT MATTERS MORE THAN THE RESULT.** The **first execution did not implement the declared specification.** The spec said *"the CFB arm is restricted to Power 4 defences"*; the code filtered only the **offence**, leaving **860 defence-seasons at a median of 2 games** — every G5 and FCS team a Power 4 offence happened to play. ⛔ **I had already seen that output before noticing.** The conforming run is below and **both are reported**, because a re-run after seeing a number is exactly the move this register exists to police.
✅ **The verdict did not move:** k=3 went **0.3793 → 0.3831**, k=4 **0.4350 → 0.4377**. **The fix did not manufacture the result.**

**Split-half r of team scrimmage yards allowed per game (conforming run):**

| k | **CFB** (294 defence-seasons, median 10 games) | **NFL** (160, median 17) |
|---|---|---|
| 1 | 0.3065 | 0.1261 |
| 2 | 0.3353 | 0.2716 |
| 3 | **0.3831 ✅** | 0.2675 |
| 4 | **0.4377 ✅** | 0.2923 |
| 5 | **0.4263 ✅** | 0.2455 |

➡️ **CFB PASSES at k = 3.** ⛔ **NFL FAILS — peak 0.2923, against a 0.35 bar declared before the run.**

### 📌 WHY THE TWO SPORTS SPLIT — and it is the same reason everything else has split
🟢 **College has enormous talent dispersion.** Alabama's defence and a bottom-tier Power 4 defence are genuinely far apart; **the NFL is parity-engineered on purpose.** So a team-level defensive number carries **real between-team variance in college that barely exists in the NFL.** ✅ This is consistent with every other finding in this register, which is why it is believable rather than convenient.
⚠️ **And note the ordering in the NFL:** slot-level `vs-position` ≈ **0.10** → team-level total ≈ **0.29** → bar **0.35**. **Pooling helped a lot and still was not enough.** ⛔ It fails. **0.29 is not 0.35.**

### 🔴 A RELIABLE MEASURE OF **WHAT**? — the next question, flagged now, not after building
⛔ **Reliability is not validity.** Total yards allowed per game is **partly a fact about PACE** — how many plays the game had — and **college tempo varies enormously.** A team whose own offence plays fast puts its defence on the field more. ➡️ **Some of that r = 0.44 may be a stable measure of TEMPO wearing a defence's name.** **The value test must use a PER-PLAY rate, and must say which of the two it is measuring.**

### ➡️ CONSEQUENCES
1. ✅ **CFB gets a candidate opponent term.** ⛔ **It is not used until it passes a value test with a minimum effect size** — reliability only means it is stable.
2. 🔴 **NFL: the pre-committed negative answer applies.** Defensive identity is **not measurable from our box scores at slot level OR team level.** ➡️ **The NFL layer needs an EXTERNAL rating** (an EPA- or DVOA-style measure), **not another aggregate of the data we already hold.** ⛔ **Building a fifth box-score construct is the thing this register was created to prevent.**

---

## T43. 🆕 SAM'S PROPOSAL, TESTED DIRECTLY — do the SIMPLE split defensive stats clear the bar?

`[opened AND specified 2026-08-30 06:06Z, BEFORE the measurement was run]`

> Sam, 2026-08-30: *"i think you might be overcomplicating the defensive side of things … simple passing yards allowed, rushing yards, yards allowed to tight ends, rushing yards allowed to qbs and etc, are enough to measure how offenses pair up vs these defenses … all of those stats are easily accessible and are available for every team in both the cfb and nfl."*

🔴 **HE IS POINTING AT A GAP I LEFT, AND THERE IS A MECHANICAL REASON HE MAY BE RIGHT.** I tested the **thinnest** slice (T38/T39/T41: WR **slot-1** yards allowed) and the **fattest** (T42: **all** scrimmage yards) and never tested the middle. ⛔ **Summing rush and pass into one total CANCELS the distinction that matters** — a defence stout against the run and porous against the pass reads as average. **Splitting them is not a smaller version of T42; it is a different measure.**

**THE SPECIFICATION, FIXED NOW.** Per (defence, game):
- **`pass_allowed`** = Σ `rec_yds` over opposing players ⚠️ (receiving, **not** `pass_yds`, which double-counts)
- **`rush_allowed`** = Σ `rush_yds` over opposing players
- **`te_allowed`** = Σ `rec_yds` over opposing **TE** only
- **`qb_rush_allowed`** = Σ `rush_yds` over opposing **QB** only
- Split-half **exactly as T38/T39/T41/T42**: first k games by week vs the rest, k = 1…6, pooled 2021–2025. **Both sports.** CFB restricted to **Power 4 defences AND Power 4 offences**, as T42's conforming run.
- **PASS = r ≥ 0.35 at some k ≤ 6.** Same bar, unchanged, fifth time.
- ➡️ **EACH MEASURE PASSES OR FAILS ON ITS OWN.** ⛔ **Only the ones that clear the bar become opponent terms.** A measure that fails is **not** used because its siblings passed.
- ⛔ **ONE RUN. NO SWEEP OVER VARIANTS.**

📌 **AND THE SIMPLIFICATION IS THE POINT, NOT A CONSOLATION.** If these clear the bar, the architecture becomes **four plain team-level defensive rates** instead of a depth-slot allowed table that has now failed three separate reliability tests. ✅ **Sam's standing instruction recorded: go above and beyond for an edge, but when the exotic version does not work, the simple accessible stats are good enough. Do not keep building complexity that has not earned its place.**

⚠️ **ONE THING TO VERIFY SEPARATELY, NOT ASSUMED:** Sam is right that these are published for every team in both sports. ⛔ **Our CFB file holds Power 4 OFFENCES only**, so it cannot produce a full-season defensive total for a non-P4 defence. **CFBD very likely exposes a per-game team box endpoint — I HAVE NOT CHECKED, and I am not going to state that it does until I have.**

### ⛔ T43 CLOSED — **ONE OF FOUR PASSES, AND IT IS THE RUN.** Run once, 2026-08-30 06:06Z.

| measure | k=1 | k=2 | k=3 | k=4 | k=5 | verdict |
|---|---|---|---|---|---|---|
| **NFL** pass_allowed | 0.120 | 0.251 | 0.306 | 0.298 | 0.308 | ⛔ FAIL |
| **NFL** rush_allowed | 0.068 | 0.116 | 0.192 | 0.264 | 0.222 | ⛔ FAIL |
| **NFL** te_allowed | 0.132 | 0.104 | 0.165 | 0.173 | 0.189 | ⛔ FAIL |
| **NFL** qb_rush_allowed | 0.088 | 0.191 | 0.172 | 0.092 | 0.068 | ⛔ FAIL |
| **CFB** pass_allowed | 0.163 | 0.167 | 0.205 | 0.177 | 0.131 | ⛔ FAIL |
| **CFB** rush_allowed | 0.305 | **0.383** | **0.388** | **0.411** | **0.378** | ✅ **PASS k=2** |
| **CFB** te_allowed | 0.074 | 0.083 | 0.027 | 0.058 | 0.082 | ⛔ FAIL |
| **CFB** qb_rush_allowed | 0.120 | 0.104 | 0.197 | 0.246 | 0.176 | ⛔ FAIL |

### ✅ SAM'S MECHANICAL POINT WAS RIGHT, AND IT FOUND SOMETHING THE TOTAL WAS HIDING
**Splitting is not a smaller T42 — it is a different measure, and the split reveals that CFB's team-total reliability (r ≈ 0.38–0.44) came ALMOST ENTIRELY FROM RUN DEFENCE.** ✅ **`rush_allowed` alone matches or beats the combined total at every k.** ⛔ **`pass_allowed` fails on its own (0.13–0.21).** **Summing them was diluting a real signal with a null one** — exactly the cancellation he predicted, though not in the direction either of us assumed.

### ⛔ AND THREE OF THE FOUR DO NOT SURVIVE. THAT IS THE APPROACH WORKING, NOT FAILING.
📌 **"Simple and universally available" is not the same as "carries signal."** These stats **are** published for every team in both sports, exactly as Sam said — ⛔ **and three of the four have no season-to-season stability at the team level.** ➡️ **Cheap tests on simple measures are precisely how you find that out before building on them.**

⚠️ **Why `pass_allowed` probably fails while `rush_allowed` passes — a hypothesis, NOT a finding:** passing volume is **game-script dependent**. Trailing teams throw; a good defence protects leads and therefore faces fewer, more desperate passes. **So pass yards allowed is partly a measure of a team's OWN offence.** Rushing is far less script-driven. ⛔ **Untested. Do not repeat it as established.**
⚠️ **`te_allowed` and `qb_rush_allowed` are near zero in BOTH sports** — thin per-game samples, and a defence's QB-rush-allowed largely records **whether it happened to face running quarterbacks.**
⚠️ **CFB `rush_allowed` at k=6 reads 0.634 on a very small n. Do not quote that figure** — the honest range is **0.38–0.41**.

### ➡️ CONSEQUENCES — AND THE ARCHITECTURE GETS SIMPLER, WHICH WAS THE INSTRUCTION
1. ✅ **CFB opponent term = `rush_allowed`, per-game, point-in-time trailing.** ⛔ **Still needs a VALUE test with a minimum effect size before it is used** — stable is not useful. ⚠️ **And the pace confound from T42 applies: the value test uses a PER-PLAY rate.**
2. ⛔ **`pass_allowed`, `te_allowed`, `qb_rush_allowed` are NOT used in either sport.** A measure is not adopted because its sibling passed.
3. 🔴 **NFL still has NOTHING from its own box scores** — four constructs and five measures, all below the bar. ➡️ **It needs an EXTERNAL rating (EPA/DVOA-style). That is now the single largest open item in the NFL layer.**
4. ✅ **DROP the depth-slot `vs-position` table from the model in both sports.** It has failed three separate reliability tests. **The data stays on disk; it stops being an input.**

📌 **SAM'S STANDING INSTRUCTION, RECORDED:** *"its always good to go above and beyond to capture an edge but if we arent able to do so, those simple stats i mentioned are good enough."* ➡️ **Reach for the exotic version once; if it does not clear the bar, take the simple one and stop building.** ⛔ **Complexity that has not earned its place is removed, not parked.**

---

## T44 & T45. 🆕 SAM'S REBUTTAL, OPERATIONALISED — **stability ≠ predictability**

`[opened AND specified 2026-08-30 06:12Z, BEFORE either measurement was run]`

> Sam, 2026-08-30: *"we are predicting games before they happen. if you see a top offense in the league go against one of the worst defenses in the league you can make a pretty good estimated guess on what the game script/tempo will be like … if a wide reciever averages 85 yards per game across multiple games, some of these games being against top 10-15 defenses, and that reciever is facing a bottom 10 team in recieving yards allowed chances are that reciever will have a good game."*

🔴 **HE IS RIGHT THAT MY TEST ANSWERED A NARROWER QUESTION THAN I IMPLIED.** T43's split-half asks whether **a raw number is a stable property of a team in isolation.** ⛔ **It does NOT ask whether that number is PREDICTABLE GIVEN CONTEXT** — and the context he names (both teams' season profiles) is **fully available before kickoff.** A measure can be unstable alone and still be forecastable in a matchup. **My phrasing let a narrow null sound like a wide one.**

### T44 — does controlling for the OPPOSING OFFENCE reveal a stable pass-defence signal?
- Per (defence, game): `pass_allowed` = Σ `rec_yds` by opposing players.
- **Residual** = `pass_allowed` − the opposing **offence's** leave-one-out season mean of its own receiving yards. ⚠️ LOO so a team cannot correlate with itself.
- Split-half exactly as T38–T43, k = 1…6, 2021–2025, **both sports**, CFB restricted to Power 4 both sides.
- **PASS = r ≥ 0.35 at some k ≤ 6.** Same bar, sixth time.
- ⚠️ **DIAGNOSTIC ONLY** — the LOO mean sees the whole season and would be illegal in a model.

### T45 — SAM'S ACTUAL EXAMPLE: does strength-of-schedule adjustment on the PLAYER side beat raw trailing form?
🔴 **This is the one that matters**, because it is a **VALUE** test, not a reliability test, and it implements his 85-yards-versus-top-10-defences case directly.
- Positions: **WR → `rec_yds`** and **RB → `rush_yds`**. Both sports.
- **Predictor A (baseline):** the player's **raw trailing mean** of the target, strictly weeks < w.
- **Predictor B (SoS-adjusted):** each past game is scaled by `league_mean_allowed / defence_faced_trailing_allowed`, the trailing mean of those adjusted values is taken, and the result is scaled back up by `this_week_defence_trailing_allowed / league_mean_allowed`. **Every input strictly point-in-time.**
- Rows: weeks 4+ (so a trailing history exists), target present, both defences having a trailing history.
- Metric **MAE**. **Test 2024 and 2025 SCORED SEPARATELY.** No fitting — both are direct point predictions, so there is nothing to overfit.
- 🔴 **PASS = MAE lower in BOTH held-out seasons AND the gain ≥ 1.0% of baseline MAE**, per position per sport. **The minimum effect size is the T36 lesson.**
- ⛔ **ONE RUN EACH. NO SWEEP.**

📌 **PRE-COMMITTED READING OF EVERY OUTCOME:** if **T45 passes**, matchup adjustment earns its place and Sam's argument is vindicated on the evidence, **whatever T43 said about raw stability.** If **T45 fails while T44 passes**, the defence signal is real but too small to move a forecast. If **BOTH fail**, then the matchup effect is **already inside the player's own trailing form** and adding a defensive term is double-counting. ⛔ **All three are results. None is a reason for a fourth variant.**

### ⛔ T44 CLOSED — FAILED BOTH SPORTS. Run 2026-08-30 06:12Z.

Split-half r of pass yards allowed **after removing the opposing offence's own level** (raw carried alongside):

| k | NFL adj | NFL raw | CFB adj | CFB raw |
|---|---|---|---|---|
| 3 | 0.2932 | 0.3062 | 0.2189 | 0.2051 |
| 4 | 0.2862 | 0.2977 | 0.1726 | 0.1770 |
| 5 | **0.3333** | 0.3076 | 0.1306 | 0.1306 |

⛔ **Nothing reaches 0.35.** ⚠️ **NFL k=5 comes within 0.017 of the bar and is NOT rescued** — the bar was fixed six tests ago and a near-miss is a miss.
📌 **Adjusting for the offence barely moved the NFL at all** (0.31 → 0.33), which is itself informative: **the instability of pass-yards-allowed is not mostly caused by opponent identity.**

### ⛔ T45 CLOSED — **FAILED 8 ARMS OUT OF 8, AND NOT NARROWLY.** Run 2026-08-30 06:12Z.

| sport · pos | 2024 raw → SoS | Δ | 2025 raw → SoS | Δ |
|---|---|---|---|---|
| NFL WR | 21.916 → 22.398 | **−2.20%** | 21.528 → 21.915 | **−1.80%** |
| NFL RB | 20.651 → 20.974 | **−1.57%** | 20.302 → 20.808 | **−2.49%** |
| CFB WR | 26.977 → 27.935 | **−3.55%** | 27.107 → 27.756 | **−2.39%** |
| CFB RB | 27.908 → 31.437 | **−12.65%** | 29.729 → 30.678 | **−3.19%** |

🔴 **SoS adjustment did not merely fail to help — it made every single arm WORSE, in both sports, both positions, both held-out seasons.** ⛔ **This is not a knife-edge result and there is no reading of it that favours the adjustment.**

### 📌 THE PRE-COMMITTED INTERPRETATION, APPLIED
Both failed, so the declared reading stands: **the matchup effect is ALREADY INSIDE the player's own trailing form, and adding a defensive term double-counts it.** ➡️ **A receiver who averaged 85 yards against hard defences — that 85 IS the estimate.** Inflating it for a soft upcoming matchup **adds variance without adding signal**, because the defensive measure (r ≈ 0.13–0.31) is far noisier than the player measure (r ≈ 0.61–0.80). ⛔ **Multiplying a stable quantity by a noisy one produces a noisier quantity. That is arithmetic, and T43/T44 predicted it.**

### ⚠️ WHERE I WOULD TEMPER MY OWN RESULT
1. **CFB RB's −12.65% is probably overstated.** The adjustment is **multiplicative and uncapped**, and college rushing defence has the widest spread of any measure here, so extreme ratios are possible. ⛔ **The other three arms, −1.57% to −3.55%, are not outlier-driven and carry the verdict on their own.**
2. **One operationalisation was tested.** A regression that *learns* a small weight on the defensive term is a different thing from assuming a full multiplicative adjustment. ⛔ **It would be a NEW pre-registration — and after six consecutive failures the honest prior on it is low.**
3. ✅ **Sam's reasoning is not what failed.** Conditioning on matchup is how everyone thinks about this, and it is right in principle. **What failed is that these particular defensive measures are too noisy to carry it.**

### 🔴 THE STRONGEST SINGLE FINDING IN THIS WHOLE PASS
⛔ **Even the ONE defensive measure that passed a reliability bar — CFB `rush_allowed`, r = 0.38–0.41 (T43) — made RB predictions WORSE when used.** ➡️ **Reliability did not translate into value, in the one case where we finally had reliability to spend.** 📌 **That is the clearest possible demonstration that a stable measure and a useful one are different things, and it is why value tests are separate from reliability tests in this register.**

### ➡️ DIRECTION, STATED PLAINLY
**Six constructs, eleven measures, one reliability pass, zero value passes.** ⛔ **The honest conclusion is that the DEFENSIVE side has very little to give us, in either sport, from box-score data.** ➡️ **The edge, if there is one, lives in PLAYER FORM and in MARKET PRICING — not in defensive modelling.** ⚠️ **Stop adding defensive constructs until something outside this data source is available.**

---

## 📌 DIRECTION SET BY SAM, 2026-08-30 06:30Z — DEFENSIVE TRACKING IS BUILT AND SHIPPED

> *"i dont care if you think that it offers little value, i think it adds a lot of value … i want you to track this data, i want you to use this data to predict offensive outcomes … touchdowns allowed vs certain positions, yards allowed vs certain positions, etc"*

✅ **BUILT AND SHIPPED THE SAME SESSION.** `allowed-by-position-YYYY.json.gz`, both leagues, 2021–2025, refreshed on every run: **receptions · receiving yards · receiving TDs · carries · rushing yards · rushing TDs · attempts · completions · passing yards · passing TDs · interceptions**, per game, for **QB / RB / WR / TE**, each with a league rank and percentile.
⛔ **RANK 1 = ALLOWS THE MOST**, because the question asked of the table is *"how soft is this defence"*, not *"how good"*.

### 🔴 NO NEW SOURCE WAS NEEDED, AND I SHOULD HAVE SAID SO SOONER
Sam asked me to find a website. ⛔ **The data was already on disk** — it is the same player-week rows the whole layer is built from, aggregated by opponent instead of by player. **I had built "yards allowed by position" and never thought to also aggregate touchdowns.** ➡️ **Before proposing an external source, check what the existing data can already answer.**

### ✅ WHY THIS SHIPS WITHOUT PASSING A VALUE TEST, AND IT IS NOT AN EXCEPTION
📌 **Ledger rule 55 settles it.** Every number on the surface is **MODEL**, **MARKET**, or **DESCRIPTIVE**, and **a market number never carries a Gizmo's confidence %.** ✅ **This table is DESCRIPTIVE** — it reports what happened. **Descriptive numbers do not need a value test; they need to be TRUE, and these are measured directly.**
⛔ **The line is drawn at the confidence number.** The moment an allowed-by-position figure drives a **MODEL** number — a projection, a confidence %, an edge — **that use needs its own pre-registered value test with a minimum effect size.** ➡️ **Track freely. Label honestly. Test before it prices anything.**

### ⚠️ TWO CAVEATS THAT TRAVEL ON THE FILE
1. 🔴 **CFB `qb_rush_yds` allowed IS NOT THE NFL COLUMN.** `[measured 2026-08-30]` college charges **sack yardage to rushing**: CFB QB rushing reaches **−73 with 23.5% of rows negative**; the NFL bottoms at **−10 with 11.6%**. ➡️ **CFB "rushing yards allowed to QBs" is largely a PASS-RUSH measure** — Ohio State's **−3.2** is a sack rate, not run defence. ⛔ **Never compare the leagues on this column.** 🟢 **And it is arguably the most useful CFB defensive column we have, because it is the pass-rush signal we otherwise lack.**
2. ⚠️ **CFB scope: Power 4 offences only.** A defence's row describes **what Power 4 offences did to it**, which for a non-P4 defence may be **one or two games.** `games` is carried on every row and **ranks are withheld below 8 games.**

### 📌 WHAT THE 2025 TABLE ALREADY SHOWS — the spread is not small
- **CFB WR receiving yards allowed:** Duke **220.1** · West Virginia **220.0** → Ohio State **90.4**. **A 130-yard range.**
- **NFL WR receiving yards allowed:** DAL **171.0** → CLE **109.5**. **A 62-yard range.**
- **CFB WR receiving TDs allowed:** Maryland **2.0** → Ohio State/Nebraska **~0.2**.
⛔ **A spread that wide is not evidence the measure PREDICTS** — T45 tested that and it failed. ✅ **But it is exactly what a trends surface exists to show, and it is real.**

---

## T48. 🆕 DOES AN **EPA-PER-PLAY** DEFENSIVE RATING CLEAR THE BAR IN THE NFL, WHERE FIVE BOX-SCORE MEASURES DID NOT?

🔴 ⛔ **STATUS: CLOSED-FAILED 2026-09-01 — ALL THREE ARMS. Peak 0.268 against a 0.35 bar declared before the run, and BELOW the yards-allowed measure it was meant to beat. THE SPECIFICATION, THE BAR AND THE FORBIDDEN LIST BELOW ARE UNCHANGED AND WERE NOT MOVED — the result is recorded BENEATH them.**

`[opened AND specified 2026-09-01 03:2xZ, BEFORE any code touched the data — the collector for it had not been written when this was fixed]`

**WHY THIS AND NOT A SIXTH BOX-SCORE CONSTRUCT.** T42's pre-committed consequence was explicit: *"the NFL layer needs an EXTERNAL rating (an EPA- or DVOA-style measure), not another aggregate of the data we already hold."* T43 repeated it: *"NFL still has NOTHING from its own box scores — four constructs and five measures, all below the bar."* ⛔ **Building a sixth box-score aggregate is the thing this register exists to prevent.** ✅ **EPA is the measure T42 named**, and it is **already inside a file the collector already downloads and already pays nothing for** — nflverse `play_by_play_{y}`, which `build_routes` fetches for its pass flag. ⚠️ **No new source, no new cost, no new vendor.**

⚠️ **WHY IT IS A GENUINELY DIFFERENT MEASURE, NOT A RESKIN.** Yards allowed is a raw count. **EPA conditions each play on down, distance, field position and game state** — a 4-yard gain on 3rd-and-3 and on 3rd-and-8 are opposite outcomes and yardage cannot tell them apart. ⛔ **That is a reason to test it, not a reason to expect it to pass.**

**THE SPECIFICATION, FIXED NOW:**
- Source: nflverse `play_by_play_{y}`. Per (defence, game), over plays where `defteam` is that team and the play is a pass or a rush:
  - **`def_epa_per_play`** = mean `epa` ⚠️ **EPA is signed from the OFFENCE's perspective, so LOWER IS BETTER for the defence.** The sign convention is stated here so it cannot be flipped later to suit a result.
  - **`def_pass_epa_per_play`** — pass plays only
  - **`def_rush_epa_per_play`** — rush plays only
- ⚠️ **A PER-PLAY RATE BY CONSTRUCTION.** T42 flagged that a team total is partly a measure of PACE. ✅ **Dividing by plays is exactly the fix T42 demanded of any value test, and it is built into the measure here rather than bolted on.**
- Sample: per (defence, season), ordered by week, **ALL games**, pooled **2021–2025**. 🔴 **IDENTICAL population and ordering to T42 and T43 — deliberately — so the comparison against their 0.29 peak is apples-to-apples.** ⛔ **No regular-season-only variant, no garbage-time filter, no early-down cut. One arm per measure.**
- Split-half: **first k games vs the rest, k = 1…6**, Pearson r across (defence, season) units. **Exactly as T38 / T39 / T41 / T42 / T43.**
- **PASS = r ≥ 0.35 at some k ≤ 6.** ⛔ **Same bar, sixth time, unchanged.**
- ➡️ **EACH OF THE THREE PASSES OR FAILS ON ITS OWN** (T43's lesson: a measure is not adopted because its sibling passed).
- ⛔ **ONE RUN. NO SWEEP OVER EPA VARIANTS** — no success rate, no WPA, no CPOE, no explosive-play rate. **Choosing a variant after seeing r is shopping, and this project has two headline coefficients that died exactly that way.**
- ⛔ **FAIL-CLOSED COLLECTION.** The collector must **NAME** the columns it used and **write nothing** if `defteam`, `epa` or the play-type flag is absent or populated on under 80% of rows. **A probe report is written either way.** ⚠️ Same discipline as `build_routes`, which is why routes could be trusted.

**PRE-COMMITTED CONSEQUENCES, FIXED BEFORE THE RUN:**
1. ✅ **IF A MEASURE PASSES** — the NFL gets a **candidate** opponent term. ⛔ **Reliability is not validity and it is NOT used until it passes a value test.**
2. 🔴 **AND THAT VALUE TEST'S MINIMUM EFFECT SIZE IS DECLARED NOW, NOT AFTER THE RELIABILITY RESULT IS SEEN: ≥ +0.005 held-out Brier over the incumbent T46 used** (the player's own trailing form, no opponent term), **on a chronological split.** ⛔ **The bar does not move.** ⚠️ **This is the T36 lesson applied in advance — an effect size declared late is an effect size chosen to fit.**
3. 🔴 **IF ALL THREE FAIL** — T42's pre-committed negative **hardens into a final one: NFL defensive identity is not measurable from ANY aggregate we can compute, per-play or box-score.** ➡️ **The NFL layer becomes PLAYER-FORM-ONLY with no opponent term, and that is written on the page.** ⛔ **NO SEVENTH CONSTRUCT.** ➡️ **The only remaining legitimate move is a genuinely external PUBLISHED rating (DVOA-style), which is PAID — and that is a purchasing decision for Sam, not a test I run.**

⚠️ **PREDICTION, WRITTEN DOWN BEFORE THE RUN SO IT CAN BE WRONG ON THE RECORD:** **I expect EPA/play to beat every box-score measure and to land between 0.30 and 0.40 — genuinely uncertain against the bar.** Reasoning: EPA conditions on game state, which should strip out much of the game-script contamination T43 hypothesised for `pass_allowed`. ⚠️ **A hypothesis. The bar decides, not the reasoning.**

### ⛔ T48 CLOSED — **ALL THREE FAIL. AND EPA CAME IN BELOW THE MEASURES IT WAS SUPPOSED TO BEAT.** Run once, 2026-09-01.

| measure | k=1 | k=2 | k=3 | k=4 | k=5 | k=6 | peak | verdict |
|---|---|---|---|---|---|---|---|---|
| **`def_epa_per_play`** | +0.040 | +0.183 | +0.197 | +0.218 | +0.225 | **+0.268** | 0.268 | ⛔ **FAIL** |
| **`def_pass_epa_per_play`** | −0.044 | +0.090 | +0.110 | +0.185 | **+0.189** | +0.178 | 0.189 | ⛔ **FAIL** |
| **`def_rush_epa_per_play`** | +0.020 | +0.032 | +0.016 | −0.004 | +0.058 | **+0.146** | 0.146 | ⛔ **FAIL** |

**Sample: 160 defence-seasons, 2021–2025, median 17 games — the SAME 160 units as T41, T42 and T43.**

🔴 **MY WRITTEN PREDICTION WAS WRONG, AND WRONG IN THE DIRECTION THAT MATTERS.** I predicted **0.30–0.40** and said EPA *"should beat every box-score measure."* ⛔ **It came in at 0.268 — BELOW T42's yards-allowed (0.292) and BELOW T43's `pass_allowed` (0.306).** ✅ **The prediction was written down precisely so it could be wrong on the record. Conditioning on down, distance and field position did not help; it slightly hurt.**

### 🔴 THE CONTROL FAILED FIRST, AND THAT IS THE MOST IMPORTANT PARAGRAPH HERE
⛔ **The pre-planned positive control — a defence's PLAYS FACED per game — scored r = 0.03 at k=3, while a deliberately SHUFFLED negative control scored 0.06.** ⚠️ **On those two numbers the instrument was not trustworthy and the FAIL above was not reportable.**
✅ **DIAGNOSED RATHER THAN WAVED AWAY.** Plays faced has a **between-unit sd of 2.41 against a within-unit sd of 8.67** — a k=3 mean carries ~5.0 of noise against 2.4 of signal. ⛔ **It is a BAD CONTROL, not evidence of a broken ruler.** 🔴 **I chose it badly; T39 chose `snap_pct` and got 0.80.**
✅ **THE CONTROL DONE PROPERLY — IDENTICAL ROWS, IDENTICAL CODE, GROUPED BY `posteam` INSTEAD OF `defteam`:**

| grouping | k=1 | k=2 | k=3 | k=4 | k=5 | k=6 | peak |
|---|---|---|---|---|---|---|---|
| **DEFENCE** (T48) | +0.040 | +0.183 | +0.197 | +0.218 | +0.225 | +0.268 | **0.268** |
| **OFFENCE** (control) | +0.277 | +0.438 | +0.470 | +0.539 | +0.541 | +0.534 | **0.541 ✅** |

✅ **THE INSTRUMENT WORKS. It clears the bar comfortably on the same plays, the same seasons and the same code — the grouping key is the only thing that changed.**
✅ **AND THREE MORE CHECKS PASSED BEFORE THE NULL WAS BELIEVED:** week ordering is real (PHI 2024 reads weeks 1–4, 6–22 — the bye is missing, as it should be); the measure **names real defences** (2024 best: PHI −0.109, MIN, DEN, GB, LAC; worst: JAX +0.131, CAR +0.154 ✅ correct, and **DEN's presence proves the grouping is the DEFENCE — Denver's 2024 defence was elite and its offence was not**); and the shuffled control sits inside noise for n=160 (se ≈ 0.079).

### 🔴 MEASURED FINDING — **NOT A TEST, NO T-NUMBER.** NFL OFFENCE IS RELIABLY MEASURABLE. NFL DEFENCE IS NOT. SAME INSTRUMENT, SAME PLAYS.
⚠️ **THIS WAS NOT PRE-REGISTERED. It is a CONTROL that was run to validate the ruler, and it is labelled as one.** ⛔ **Do not cite it as a passed test and do not let it become one retrospectively.**
**0.54 against 0.27, on identical data, with the grouping key the only difference.**
📌 **THIS SHARPENS T42'S EXPLANATION AND PARTLY CONTRADICTS IT.** T42 attributed the NFL's failure to **parity** — small between-team variance. ⛔ **Parity would depress BOTH sides. It does not: NFL offences are twice as self-similar as NFL defences.** ➡️ **The honest reading is that a defence's per-play outcome is dominated by WHICH OFFENCE IT FACED, which is exactly the game-script mechanism T43 hypothesised for `pass_allowed` — now visible on the other side of the ball.** ⚠️ **Still a reading, not a finding.**

### ➡️ CONSEQUENCES — THE PRE-COMMITTED ONE, APPLIED WITHOUT AMENDMENT
1. 🔴 **T42's pre-committed negative HARDENS INTO A FINAL ONE: NFL defensive identity is NOT measurable from ANY aggregate we can compute — slot-level, team-level, box-score or per-play.** **Six measures, five constructs, 2021–2025, every one below 0.35.**
2. ✅ **THE NFL LAYER IS PLAYER-FORM-ONLY, WITH NO OPPONENT TERM, AND THE PAGE SAYS SO.**
3. ⛔ **NO SEVENTH CONSTRUCT.** **Not success rate, not WPA, not CPOE, not early-down EPA, not a garbage-time filter.** ⚠️ **T48 forbade exactly these by name before the run, and the failure does not unlock them.**
4. ➡️ **The only remaining legitimate move is a PAID external published rating (DVOA-style).** 🔴 **That is a purchasing decision for Sam, not a test I run** — and it should be made knowing that **six free measures found nothing**, so a paid one is a bet, not a fix.
5. ✅ **`def-epa-*.json.gz` STAYS ON DISK, ⚪ DESCRIPTIVE.** It is the sample anyone would need to re-examine this, and it is the correct instrument for the **offensive** side, where r = 0.54.
6. 🟢 ➡️ **AND THE CONTROL POINTS SOMEWHERE REAL: an OFFENCE-quality term is reliable in the NFL where a defence-quality term is not.** ⛔ **Reliability is not validity — that is a NEW pre-registered test with its own minimum effect size, not an input.**

⚠️ **AND THE NFL'S STRUCTURAL PROBLEM DOES NOT GO AWAY:** T42's explanation for why college passes and the NFL fails — **the NFL is parity-engineered, so between-team variance is genuinely small** — applies to EPA exactly as it applied to yards. ⛔ **A better instrument cannot manufacture variance that is not there.**

---

## T49. 🆕 THE VALUE TEST FOR CFB `rush_allowed` — **THE LAST SURVIVING OPPONENT TERM IN EITHER SPORT**

🔴 ⛔ **STATUS: CLOSED-FAILED 2026-09-01. C vs B came in −0.94% / +0.24% against a +1.00% bar declared before the run. THE SPECIFICATION, THE BAR AND THE FORBIDDEN LIST BELOW ARE UNCHANGED AND WERE NOT MOVED — the result is recorded BENEATH them.**

`[opened AND specified 2026-09-01, BEFORE any fitting. Nothing has been regressed.]`

🔴 **THIS IS THE WHOLE OPPONENT-SIDE ARCHITECTURE, DECIDED BY ONE TEST.** Across T36–T48, **seven measures in two sports** have been put against a reliability bar and **exactly one survived: CFB `rush_allowed`, r = 0.38–0.41 (T43).** ⛔ **And T43 said it plainly: *"Still needs a VALUE test with a minimum effect size before it is used — stable is not useful."*** ➡️ **If this fails, NEITHER SPORT HAS AN OPPONENT TERM and the football model is player-form-only, full stop.**

📌 **AND THE RISK IS INCREMENTAL VALUE, NOT VALUE.** ⚠️ **CFB already carries `opp_elo` — pregame, free, point-in-time legal, and the talent gap in college is enormous.** ⛔ **A rushing-defence term that merely rediscovers "Alabama is good" has added NOTHING.** ✅ **So `rush_allowed` must beat a model that ALREADY KNOWS the opponent's Elo. That is the honest question and it is the harder one.**

**THE SPECIFICATION, FIXED NOW:**
- **Target: a running back's RUSHING YARDS in a game.** ⚠️ **The outcome the measure is supposed to predict.** ⛔ Testing a rushing-defence term against receiving yards would be a category error.
- **Sample:** `pos == "RB"`, seasons **2021–2025**, games where **the opposing defence is Power 4** (⚠️ our file holds P4 offences only, so `rush_allowed` is computable only there — T42's restriction, inherited deliberately), the player has **≥ 4 prior games that season**, and the opposing defence has **≥ 3 prior games that season** (T43 cleared the bar from k=2; 3 is the floor and it is declared here, not chosen later).
- **Point-in-time throughout, `w < week` strictly.** ⛔ A season total joined to a week-3 game has seen the future.
- **`rush_allowed` is a PER-PLAY RATE:** opposing rushing yards allowed **per opposing carry**, trailing, point-in-time. ⚠️ **T42 warned that a per-game total is partly a measure of PACE. This is that fix, declared in the spec rather than discovered in the result.**
- **THREE ARMS, ALL DECLARED NOW, OLS, one specification each, no interactions:**
  - **A (incumbent)** — the player's trailing mean `rush_yds` this season
  - **B** — A **+ `opp_elo`**
  - **C** — B **+ `rush_allowed` per-play**
- 🔴 **`rush_allowed`'s VALUE IS C vs B, NOT C vs A.** ⛔ **Beating a model that does not know who the opponent is proves nothing.**
- ⚠️ **B vs A is a SECOND DECLARED QUESTION, not a sweep** — does `opp_elo` earn its place at all? **Both are fixed before the run.**
- **Split: CHRONOLOGICAL BY SEASON. Fit 2021–2023. Hold out 2024 AND 2025.**
- **PASS = C beats B on held-out MAE by ≥ 1.0%, IN BOTH HELD-OUT SEASONS.**
  🔴 **The both-seasons clause is not decoration. T40's weather term improved in one held-out season and failed in the other, and it was recorded FAILED rather than rescued.** ⛔ **Same treatment here.**
- ⛔ **ONE RUN. FORBIDDEN BY NAME:** a trailing-window sweep, switching `rush_allowed` back to a per-game total after seeing C, adding carries/game or `usage` to rescue it, dropping 2024 or 2025 for being "unrepresentative", and re-running on a different position group.

**PRE-COMMITTED CONSEQUENCES:**
1. ✅ **IF C PASSES** — CFB gets its first tested opponent term. ⚠️ 🔵 **It is MODEL and labelled MODEL (rule 55).**
2. 🔴 **IF C FAILS** — ⛔ **`rush_allowed` is NOT used, and NEITHER SPORT HAS AN OPPONENT TERM.** ➡️ **The football model becomes PLAYER FORM plus, if B passed, PREGAME ELO — and nothing else. That is written on the page.** ✅ **This is the simplification Sam asked for, arrived at by measurement rather than by preference:** *"if we arent able to do so, those simple stats i mentioned are good enough."*
3. ⛔ **A FAILURE DOES NOT REOPEN THE DEFENSIVE BOX SCORE.** **Eight measures will have been tested. The reopening condition is a genuinely NEW INPUT, not a new cut of the same data.**


### ⛔ T49 CLOSED — **FAILED. AND SO DID `opp_elo`.** Run once, 2026-09-01.

**4,931 RB-games (2,706 fit 2021–23 · 2,225 held out 2024–25), 67 Power 4 teams, 860 defence-seasons.**

**Held-out MAE (rushing yards):**

| arm | 2024 | 2025 |
|---|---|---|
| **A** trailing form only | 26.511 | 28.190 |
| **B** + `opp_elo` | 26.530 | 27.657 |
| **C** + `rush_allowed` | 26.780 | 27.590 |

🔴 **THE TEST — `rush_allowed`'s incremental value, C vs B: −0.94% in 2024, +0.24% in 2025, against a +1.00% bar declared before the run. FAIL, and 2024 is actively WORSE.**
⚠️ **THE VERDICT IS ROBUST TO THE BAR.** ⛔ A 0.5% bar would not save it and neither would 0.25% — **2024 is negative.** ✅ **So no one need wonder whether the bar was set too high.**

### ⚠️ AND THE SECOND ARM, WITH AN HONESTY CAVEAT I HAVE TO STATE FIRST
🔴 **I DECLARED B vs A AS A QUESTION AND DID NOT DECLARE ITS BAR.** The script applied C's bar to it, which is consistent, ⛔ **but it was NOT pre-registered and I will not call it a passed or failed test.** ➡️ **It is reported as a MEASURED READING:** `opp_elo` gains **−0.07% in 2024 and +1.89% in 2025.** ⚠️ **It helps in one held-out season and does nothing in the other** — the same shape as T40's weather.

### ✅ BOTH CONTROLS PASSED — CHECKED BEFORE THE RESULT WAS BELIEVED
| control | result | |
|---|---|---|
| trailing form vs a constant | **+24.8% / +19.3%** | ✅ the frame works |
| corr(`opp_elo`, `rush_allowed`) | **−0.4855** | ✅ better defences allow fewer yds/carry — **the measure is not inverted** |

⚠️ **T48's planned control FAILED and nearly let an unreportable null through. These were chosen better and both cleared.**

### 🔴 THE REASON IT FAILS, AND IT IS NOT A BROKEN FIT — **EVERY SIGN AND SIZE IS RIGHT**
| term | coefficient | 1-sd swing |
|---|---|---|
| `rush_allowed` | **+5.17** yds per yd/carry | **±4.41 rushing yards** |
| `opp_elo` | **−0.0171** | **±3.77 rushing yards** |

✅ **Both signs are correct** — a leakier run defence means more yards, a stronger opponent means fewer. ⛔ **AND THE HELD-OUT MAE IS ~27 YARDS.** 🔴 **A full standard deviation of DEFENSIVE QUALITY moves the projection about 4 yards against 27 yards of error, on an outcome whose own sd is 46.** ➡️ **The effect is REAL AND SWAMPED.** ⚠️ **Exactly T40's weather story: right sign, sensible magnitude, still does not earn its place.**

### ⚠️ MY PREDICTION WAS HALF RIGHT, AND THE HALF I GOT WRONG IS THE INTERESTING ONE
✅ **"C fails against B" — correct.** ⛔ **"B beats A comfortably" — WRONG.** `opp_elo` is not comfortable; it is one season of nothing and one season of 1.9%.

### ➡️ CONSEQUENCES — THE PRE-COMMITTED ONE, APPLIED
1. ⛔ **`rush_allowed` IS NOT USED.** 🔴 **NEITHER SPORT HAS A TESTED OPPONENT TERM.** **Eight measures across two sports have now been tested and the one that survived reliability died on value.**
2. ✅ **THE FOOTBALL MODEL IS PLAYER FORM. THAT IS THE ARCHITECTURE, AND THE PAGE SAYS SO.** ⚠️ `opp_elo` may stay as a ⚪ DESCRIPTIVE context field — ⛔ **it is NOT a fitted input on this evidence.**
3. ⛔ **NO NINTH CONSTRUCT.** **T49 forbade a window sweep, a per-game switch, a usage rescue and a different position group BY NAME. The failure does not unlock them.**
4. ✅ **THE DATA STAYS ON DISK.** It is the sample anyone would need to re-examine this.
5. 📌 **AND THIS IS SAM'S OWN INSTRUCTION ARRIVING BY MEASUREMENT:** *"if we arent able to do so, those simple stats i mentioned are good enough."* ➡️ **The opponent side is not simplified — it is EMPTY, and that was found by testing rather than assumed by either of us.**

⚠️ **WHAT WOULD REOPEN THIS: a genuinely NEW INPUT, not a new cut.** ⛔ Not another aggregate of carries and yards. ➡️ **The honest candidates are charted data we do not have (pressure rate, box counts, personnel) or a paid external rating — and T48 already showed a paid rating would be a bet, not a fix.**

⚠️ **PREDICTION, ON THE RECORD SO IT CAN BE WRONG:** **I expect B to beat A comfortably and C to FAIL against B — a gain under 1%.** Reasoning: `opp_elo` already encodes most of "how good is this defence" in a sport with enormous talent dispersion, and T43's reliability (0.38) is stability, not orthogonality. ⚠️ **A hypothesis. The bar decides.** 🔴 **My last written prediction (T48, 0.30–0.40) was wrong and below its own range.**

---

## T47. 🆕 **THE FULL SPECIFICATION** — can a football model we are ALLOWED TO SHIP beat a season average?

🔴 ⛔ **STATUS: CLOSED-FAILED 2026-09-01. Brier −0.0041 against a +0.0050 bar — WORSE than T46's +0.0010. MAE worse. RB subgroup worse. THE SPECIFICATION, THE BAR AND THE FORBIDDEN LIST BELOW ARE UNCHANGED AND WERE NOT MOVED — the result is recorded BENEATH them.**

`[opened AND specified 2026-09-01, BEFORE any fit. T47 has existed as a one-line reservation since 2026-08-30; this is its specification, and nothing has been regressed.]`

🔴 **THIS IS THE ONLY OPEN PATH TO FOOTBALL HAVING A MODEL AT ALL.** T46 failed. T48 and T49 closed the opponent side in both sports. **Everything football currently ships is ⚪ DESCRIPTIVE or 🔵 MARKET.** ➡️ **T47 is the question of whether that changes.**

📌 **WHY THESE INPUTS AND NOT OTHERS.** T46's own result named them: *"T39 USED NEITHER INJURIES NOR DEPTH CHARTS, AND THOSE ARE THE ONLY COLLECTED INPUTS A SEASON AVERAGE CANNOT CONTAIN."* ➡️ **A WR2 becomes a WR1 the moment WR1 sits. A season average cannot know that. A model can.** ⚠️ **And a player's own smoothed season average has now beaten this project FOUR separate times (T27–T30, T31–T33, T46) — it is the DEFAULT HYPOTHESIS, not the afterthought.**

### 🔴 THE ONE DELIBERATE DEVIATION FROM T46, DECLARED BEFORE THE RUN
⛔ **T46's specification contained an OPPONENT TERM (`opp_rec_yds_allowed_to_pos`, which read t = +3.68 and was "clearly real"). IT IS REMOVED.**
**Because T43's consequence #4 is binding — *"DROP the depth-slot `vs-position` table from the model in BOTH sports"*** — and T48/T49 have since closed the opponent side entirely. ⛔ **A model that cannot ship is not worth testing.**
⚠️ 🔴 **THE COST OF THAT IS STATED PLAINLY: T47 IS THEREFORE *NOT* A CLEAN ISOLATION OF INJURIES AND DEPTH.** Two things change at once. ➡️ **It is a test of THE BEST MODEL WE ARE ALLOWED TO SHIP, which is the decision-relevant question — but it cannot attribute its result to the new inputs alone, and no such attribution will be claimed.**
✅ **THE OPPONENT-HISTORY ROW FILTER IS RETAINED ANYWAY** (opponent needs ≥ 8 prior games), **even though the term is gone, SO THE SAMPLE IS IDENTICAL TO T46's.** ⛔ **Dropping the filter with the feature would have quietly changed the population and made the two incomparable.**

**THE SPECIFICATION, FIXED NOW:**

    E[rec_yds] = a + b1*trail8_targets + b2*trail8_yds_per_tgt
                   + b3*trail8_snap_pct + b4*home
                   + b5*inj + b6*ahead_out + b7*ol_out + b8*opp_dl_out

**The four NEW inputs, named now so none can be dropped after seeing a t-stat:**
| field | what it is | base rate (2025 WR) |
|---|---|---|
| `inj` | **he himself** is on the injury report | 4.1% |
| `ahead_out` | **how many players AHEAD of him are OUT** — the WR2→WR1 cascade | 15.3% non-zero |
| `ol_out` | his own blockers missing | 36.6% non-zero |
| `opp_dl_out` | opposing pass rushers missing | 31.1% non-zero |

✅ **POINT-IN-TIME VERIFIED, NOT ASSUMED.** `out_set` is built from nflverse's **published injury report** (`report_status` OUT/DOUBTFUL) — **known pregame.** ⛔ It is NOT "who failed to record a stat", which would be post-hoc. And `ahead_out`'s depth ranking uses **snap share from games STRICTLY BEFORE this one.**

**EVERYTHING ELSE IS T46, UNCHANGED:** 2025 only · trailing 8 · ≥ 6 prior games · **fit weeks 1–13, test weeks 14–22** · line = the player's own trailing-8 **median** · Normal with sd floored at the position residual sd · positions WR/TE/RB.

**THE BAR — ALL FOUR MUST HOLD, SAME AS T46, NOT MOVED:**
1. **PRIMARY** — Brier beats the better naive by **≥ +0.0050**
2. **SECONDARY** — MAE **not worse** than the better naive
3. **SUBGROUP** — not worse than naive on **WR, TE or RB separately**
4. **MINIMUM** — **≥ 200 test rows**

⛔ **ONE RUN. FORBIDDEN BY NAME:** adding routes / `pass_snaps` (that is a **separate** test and it is not this one); re-adding any opponent term; expanding the sample to 2021–2025; changing the line rule (⚠️ **T46's own design note that a median line caps the achievable Brier gain is ACKNOWLEDGED and DELIBERATELY NOT ACTED ON — changing it would make T47 incomparable, and MAE is unaffected by it anyway**); dropping any of the four new features after seeing its t-statistic; a second trailing window.

**PRE-COMMITTED CONSEQUENCES:**
1. ✅ **IF IT PASSES** — football gets its first 🟢 MODEL number. ⚠️ **And it STILL does not ship a confidence % to the public page**, because T46's successor test — **beat the MARKET, prospectively, on 2026 lines** — has not been run. **Beating a season average is not beating a book.**
2. 🔴 **IF IT FAILS** — ⛔ **the football layer ships as ⚪ DESCRIPTIVE and 🔵 MARKET with NO Gizmo's %, and that is written on the page as a statement rather than an omission.** ➡️ **The reopening condition is a genuinely NEW INPUT — and the one candidate we hold and have never tested is ROUTE PARTICIPATION**, which T46's own prediction #4 pointed at: *"TE usage splits between blocking and routes and snap share does not distinguish them."* ⛔ **That is a NEW pre-registration, not a rescue of this one.**


### ⛔ T47 CLOSED — **FAILED, AND FAILED WORSE THAN T46.** Run once, 2026-09-01.

**Identical sample to T46: 2,874 rows, 1,361 fit (wk 1–13), 1,513 held out (wk 14–22).**

| | Brier | MAE |
|---|---|---|
| **T47 MODEL** | **0.2586** | **17.35** |
| T46 model *(for reference)* | 0.2534 | 17.19 |
| naive trailing-8 | 0.2566 | 17.23 |
| naive season-to-date | **0.2544** | **17.10** |

- 🔴 **PRIMARY FAIL — Brier −0.0041 against a +0.0050 bar.** ⛔ **T46 was +0.0010. This is WORSE, not closer.**
- 🔴 **SECONDARY FAIL — MAE 17.35 vs 17.10.**
- 🔴 **SUBGROUP FAIL — RB −0.0204, badly worse than naive.** ✅ TE +0.0018 and WR +0.0033 were fine.
- ✅ 1,513 test rows.

⛔ **THE BAR DOES NOT MOVE AND NOTHING IS RE-CUT.**

### 🔴 THE NEW INPUTS ARE NEARLY ALL NULL — AND ONLY ONE CLEARED
| term | b | t | |
|---|---|---|---|
| trailing-8 targets | +6.43 | **+13.28** | 🟢 usage carries it, **fifth confirmation** |
| trailing-8 yds/target | +0.49 | +2.14 | ⚠️ weak |
| trailing-8 snap % | +8.57 | +1.77 | ⚠️ null |
| home | +0.19 | +0.14 | ⛔ dead null, **as T46 also found** |
| **`inj`** | −3.24 | **−0.94** | ⛔ **NULL** |
| **`ahead_out`** | **+4.11** | **+2.01** | ✅ **real, and it is the only one** |
| **`ol_out`** | +0.99 | +0.85 | ⛔ **NULL** |
| **`opp_dl_out`** | +1.44 | +1.39 | ⛔ **NULL** |

📌 **`ahead_out` IS REAL AND IT IS NOT ENOUGH.** **+4.1 receiving yards when a man ahead of him sits** — the right sign, a sensible size, t = 2.01. ⛔ **And it is non-zero on ~15% of rows, so a real effect moves few predictions.** ⚠️ **This is the third time in two days a term has been correct in sign and magnitude and still failed to earn its place** — T40's weather, T49's `rush_allowed`, now this.

### ⚠️ THE CONFOUND WAS DECLARED IN ADVANCE, AND IT IS WHY THE MODEL GOT WORSE
⛔ **T47 removed T46's opponent term (t = +3.68) and added four weak ones. TWO THINGS CHANGED, exactly as the spec warned, so NO PER-INPUT ATTRIBUTION IS CLAIMED.** ➡️ **The plain reading is that dropping `oa` cost more than injuries and depth gained.**
🔴 **AND THAT TENSION IS THE INTERESTING PART, NOT AN ARGUMENT TO PUT `oa` BACK.** **T39/T41/T43/T48/T49 proved `vs-position` is NOT a reliable property of a defence** (r = 0.0004–0.31 across five tests). ➡️ **So a term can be SIGNIFICANT IN-SAMPLE while not measuring the thing it is named after** — most likely `oa` was picking up game environment or the opposing offence. ⛔ **Statistical significance in a fit is not evidence that a construct is real. This register has now demonstrated that on the same variable from both directions.**

### ✅ AND THE CONCLUSION IS ROBUST TO THE CONFOUND, WHICH IS WHAT MATTERS
**T46 WITH the opponent term: FAIL (+0.0010).** **T47 WITHOUT it: FAIL (−0.0041).** ➡️ 🔴 **NO SHIPPABLE RECEIVING-YARDS MODEL BEATS A PLAYER'S OWN SEASON AVERAGE. Both specifications fail, so the confound does not rescue either.**
📌 **FIFTH INDEPENDENT CONFIRMATION** that a player's own smoothed season average is a brutal baseline — MLB hitters (T27–T30), MLB team totals (T31–T33), T46, now T47.

### ⚠️ MY PREDICTION: 2 OF 3, AND WRONG ON THE NUMBER FOR THE THIRD TIME RUNNING
✅ **"`ahead_out` will be significant (t > 2)" — RIGHT**, t = +2.01.
✅ **"the model will still FAIL" — RIGHT.**
⛔ **"+0.001 to +0.003" — WRONG, and wrong in SIGN: −0.0041.** 🔴 **T48 (0.30–0.40 → 0.268), T49's second half, now this. My magnitude estimates are not reliable and should be read as commitments to be graded, not as forecasts.**

### ➡️ CONSEQUENCES — THE PRE-COMMITTED ONE, APPLIED
1. ⛔ **THE FOOTBALL LAYER SHIPS ⚪ DESCRIPTIVE AND 🔵 MARKET WITH NO GIZMO'S %.** ✅ **And the page STATES it rather than omitting it.**
2. ✅ **THE REOPENING CONDITION WAS NAMED IN ADVANCE AND IT IS NOW LIVE: ROUTE PARTICIPATION.** 🔴 **T46's own prediction #4 pointed straight at it — *"TE usage splits between blocking and routes and snap share does not distinguish them."*** ⚠️ **AND THIS RUN IS CONSISTENT WITH THAT: `snap_pct` is a NULL here (t = +1.77), and RB — the position whose snaps include the most pass-blocking — is the subgroup that FAILED.** ➡️ **`pass_snaps` is a strictly better usage denominator than `snap_pct`, and it is the one input we hold and have never tested.**
3. ⛔ **THAT IS A NEW PRE-REGISTRATION, NOT A RESCUE OF T47**, and it needs **2025 only** — the same season T46 and T47 used. ✅ **So `routes-2023` is still not worth building; the withdrawal stands.**
4. ⛔ **`inj`, `ol_out` and `opp_dl_out` ARE SPENT.** **They were named, tested and came back null. They do not return in a different window or a different interaction.**

⚠️ **PREDICTION, ON THE RECORD SO IT CAN BE WRONG:** **`ahead_out` will be significant (t > 2) and the model will STILL FAIL the Brier bar — I expect +0.001 to +0.003.** Reasoning: T46 missed by 0.004, and these inputs are non-zero on only ~15% of rows for the cascade that matters, so even a real effect moves few predictions. ⚠️ **A hypothesis; the bar decides.** 🔴 **My last two written predictions were both wrong — T48 (0.30–0.40, actual 0.268) and T49's second half.**

---

## T50. 🆕 **IS PASS-SNAP SHARE A BETTER USAGE DENOMINATOR THAN SNAP SHARE?**

🔴 ⛔ **STATUS: CLOSED-FAILED 2026-09-01. Brier −0.0036 against +0.0050. The two snap measures correlate at 0.9647 — they are almost the same variable. THE SPECIFICATION, THE BAR AND THE FORBIDDEN LIST BELOW ARE UNCHANGED AND WERE NOT MOVED.**

`[opened AND specified 2026-09-01, BEFORE any fit. The reopening condition T47 named, taken up as a NEW pre-registration rather than a rescue.]`

🔴 **THIS WAS PREDICTED IN WRITING BEFORE T46 EVER RAN.** T46's prediction #4: *"TE usage splits between blocking and routes and **snap share does not distinguish them**."*
✅ **AND T47 IS CONSISTENT WITH IT, WHICH IS WHY THIS TEST IS OWED RATHER THAN INVENTED:** `snap_pct` came back a **NULL (t = +1.77)**, and **RB — the position whose snaps contain the most pass-blocking — is the subgroup that FAILED (−0.0204).**
➡️ **`pass_snaps` is the one input we hold and have NEVER tested.** ⛔ A receiver who was on the field for 60 snaps of which 20 were passes had 20 chances, not 60. **`snap_pct` cannot see that. `pass_snap_share` can.**

### ✅ THE FIX FOR T47'S OWN CONFOUND: **EXACTLY ONE THING CHANGES**
⛔ **T47 changed TWO things at once and could not attribute its result. That is not repeated.** ✅ **T50 is T47's specification with `trail8_snap_pct` REPLACED by `trail8_pass_snap_share` and NOTHING ELSE TOUCHED** — same rows, same split, same bars, and **the three inputs T47 declared SPENT (`inj`, `ol_out`, `opp_dl_out`) are CARRIED UNCHANGED rather than dropped.** ⚠️ **Dropping them would be a second change and would forfeit the attribution this test exists to get.**

**THE SPECIFICATION, FIXED NOW:**

    E[rec_yds] = a + b1*trail8_targets + b2*trail8_yds_per_tgt
                   + b3*trail8_PASS_SNAP_SHARE          <-- the ONLY change
                   + b4*home + b5*inj + b6*ahead_out
                   + b7*ol_out + b8*opp_dl_out

**`pass_snap_share` = his pass snaps ÷ his team's pass plays that game**, from `routes-2025.json.gz`, trailing 8, point-in-time.

⚠️ **THE DENOMINATOR IS A PROXY AND IS DECLARED AS ONE BEFORE THE RUN.** Team pass plays are taken as the **maximum `pass_snaps` among that team's WR/TE/RB in that game.** ⛔ **Linemen are not in the player database, so the true count is not available.** ➡️ **A near-every-down receiver plays ~90–95% of pass snaps, so this UNDERSTATES the denominator slightly and OVERSTATES every share by a roughly constant factor.** ✅ **A near-constant scaling is absorbed by the coefficient; the per-game noise is not, and that is a real limitation of this test, stated up front.**

**SAMPLE:** T47's rows **∩** a successful route join. ✅ **Measured before writing this: the join covers 99.66% (5,610 of 5,629 WR/TE/RB player-games; 19 misses).** ⛔ **If the fit or test row counts fall more than 5% below T47's 1,361 / 1,513, that is REPORTED and the two are declared not-quite-comparable.**

**THE BAR — ALL FOUR, IDENTICAL TO T46 AND T47, NOT MOVED:** Brier ≥ **+0.0050** over the better naive · MAE not worse · no subgroup worse · ≥ 200 test rows.

⛔ **ONE RUN. FORBIDDEN BY NAME:** reverting to `snap_pct` after seeing the result; using `pass_snaps` as a **count** instead of a share; including **both** snap measures; a different trailing window; expanding to 2021–2025; re-adding an opponent term; dropping `inj` / `ol_out` / `opp_dl_out`.

**PRE-COMMITTED CONSEQUENCES:**
1. ✅ **IF IT PASSES** — football gets its first 🟢 MODEL number, ⚠️ **and still no public confidence %** until a prospective beat-the-market test on 2026 lines. **Beating a season average is not beating a book.**
2. 🔴 **IF IT FAILS** — ⛔ **THE FOOTBALL MODELLING PROGRAMME IS CLOSED.** **Three pre-registered specifications (T46, T47, T50) will have lost to a player's own season average, and every input we hold will have been tested.** ➡️ **Football ships ⚪ DESCRIPTIVE and 🔵 MARKET, the page SAYS SO, and the reopening condition is CHARTED DATA WE DO NOT OWN — not another cut of what we have.**


### ⛔ T50 CLOSED — **FAILED. AND THE TWO SNAP MEASURES ARE ALMOST THE SAME VARIABLE.** Run once, 2026-09-01.

✅ **ROUTE JOIN: 2,874 of 2,874 T47 rows — 100.00%.** ⛔ **So the samples ARE identical and the attribution IS clean. Exactly one thing changed.**

| | Brier | MAE |
|---|---|---|
| **T50 (`pass_snap_share`)** | **0.2580** | **17.36** |
| T47 (`snap_pct`) | 0.2586 | 17.35 |
| naive season-to-date | **0.2544** | **17.10** |

- 🔴 **PRIMARY FAIL — Brier −0.0036 against +0.0050.** ⚠️ **T47 was −0.0041. The swap bought +0.0005. That is nothing.**
- 🔴 **SECONDARY FAIL — MAE 17.36 vs 17.10.**
- 🔴 **SUBGROUP FAIL — RB −0.0183** (T47: −0.0204). ✅ TE +0.0025, WR +0.0028.

| term | T47 t | **T50 t** |
|---|---|---|
| `snap_pct` → **`pass_snap_share`** | +1.77 | **+1.96** |
| trailing-8 targets | +13.28 | **+11.48** |

### 🔴 THE REASON, AND IT IS MEASURED RATHER THAN ASSERTED
| pair | r |
|---|---|
| **`pass_snap_share` vs `snap_pct`** | **+0.9647** |
| `trail8_targets` vs `pass_snap_share` | +0.8686 |
| `trail8_targets` vs `snap_pct` | +0.8364 |

🔴 **THE TWO SNAP MEASURES CORRELATE AT 0.96. THEY ARE ALMOST THE SAME VARIABLE.**
➡️ **T46's prediction #4 — *"TE usage splits between blocking and routes and snap share does not distinguish them"* — is TRUE PER PLAY AND WASHES OUT IN AN 8-GAME AVERAGE.** **A player who is on the field a lot is on the field for a lot of pass plays.** ⛔ **The distinction the whole hypothesis rested on barely exists at the resolution the model works at.**
✅ **AND THE REDUNDANCY WITH TARGETS IS VISIBLE IN THE FIT:** targets' t fell **13.28 → 11.48** when `pass_snap_share` replaced `snap_pct`, which is the collinearity signature. ⚠️ **Consistent with the prediction, not proof of it.**

### ⚠️ MY PREDICTION: 1 OF 2 ON THE VERDICT, AND THE MECHANISM HELD
⛔ **"t > 2.5" — WRONG.** It reached **+1.96** — higher than `snap_pct`'s +1.77, and still a null.
✅ **"the model will still FAIL" — RIGHT.**
✅ **"it will fail for being REDUNDANT, because targets are already pass-game usage" — SUPPORTED** by r = 0.87 with targets and the drop in targets' t. **I wrote the mechanism down in advance and it is the part that held.**
🔴 **FOUR CONSECUTIVE WRONG MAGNITUDE CALLS (T48, T49, T47, T50). The pattern is now established and stated: my point estimates are unreliable; my directional and mechanistic calls have been better.**

### ➡️ CONSEQUENCE — PRE-COMMITTED, AND IT IS THE BIG ONE
🔴 ⛔ **THE FOOTBALL MODELLING PROGRAMME IS CLOSED.**
**THREE pre-registered specifications — T46, T47, T50 — have now lost to a player's own season average on the same held-out weeks, and EVERY INPUT WE HOLD HAS BEEN TESTED:** trailing targets ✅ *(the only thing that works)*, yards per target, snap share, **pass-snap share**, home, opponent yards allowed, `inj`, `ahead_out`, `ol_out`, `opp_dl_out`, plus eight opponent constructs across T36–T49.

1. ✅ **FOOTBALL SHIPS ⚪ DESCRIPTIVE AND 🔵 MARKET, AND THE PAGE SAYS SO AS A STATEMENT RATHER THAN AN OMISSION.**
2. ⛔ **THE REOPENING CONDITION IS CHARTED DATA WE DO NOT OWN** — separation, box counts, personnel groupings, pressure rate. **NOT another cut of what we have.**
3. 🟢 **WHAT SURVIVED IS WORTH SAYING PLAINLY: TRAILING TARGETS, t = +11 TO +13 ACROSS THREE INDEPENDENT SPECIFICATIONS.** ➡️ **Usage is the signal and it belongs ON THE PAGE as a descriptive number, which is exactly what the trends surface already does.**
4. 📌 **SIXTH CONFIRMATION** that a player's own smoothed season average is a brutal baseline — MLB hitters, MLB team totals, T46, T47, T50.

⚠️ **PREDICTION, ON THE RECORD:** **`pass_snap_share` will be MORE significant than `snap_pct` was (t > 2.5) and the model will STILL FAIL.**
🔴 **AND THE REASON IS THE INTERESTING PART: TARGETS ARE ALREADY PASS-GAME USAGE.** A player only draws a target on a pass play, so `trail8_targets` (t = +13.28) and `pass_snap_share` are **substantially the same variable**, and the second one cannot add much once the first is in. ⛔ **`snap_pct` failed for being too BROAD; `pass_snap_share` will fail for being REDUNDANT.**
⚠️ 🔴 **MY LAST THREE MAGNITUDE PREDICTIONS WERE ALL WRONG (T48, T49, T47). Read this as a commitment to be graded, not a forecast.**

---

## 🔴 TEST-NUMBER COLLISION — LOGGED 2026-08-30 06:50Z, AND IT IS MINE

⛔ **I OPENED T36–T45 IN THIS REGISTER WITHOUT CHECKING WHETHER ANY OF THOSE NUMBERS WERE ALREADY IN USE ELSEWHERE.** `claude/multi-league-spec.md` had claimed **T39** on 2026-08-28 (the first NFL receiving-yards model, failed) and reserved **T41** (its owed follow-up adding injuries and depth charts). ➡️ **For two days two different tests answered to each name across two documents.**

✅ **RESOLUTION: THIS REGISTER IS AUTHORITATIVE AND ITS T36–T45 STAND UNCHANGED.** The multi-league page's tests were never entered here, so they take the next free numbers and are entered now:
- **T46** *(was "T39" in `multi-league-spec.md`)* — **CLOSED-FAILED 2026-08-28.** NFL receiving yards, fit 2025 wk1–13 (1,361 rows), tested wk14–22 (1,513 held out). **Brier 0.2534 vs 0.2545 season-to-date — +0.0010 against a +0.0050 bar. MAE 17.19 vs 17.10, WORSE than a season average. WR, the largest subgroup, worse than naive.** ⛔ **The bar was not moved.** ✅ **What survived: trailing targets t=+11.94, yards-per-target t=+1.39 — usage carries it, efficiency is noise, exactly as pre-registered.**
- **T47** *(was "T41")* — **OPEN.** Add **injuries and depth charts** to T46's specification at the same 0.005 bar. ⚠️ **They are the only collected inputs a season average cannot contain.**

📌 **THE LESSON, AND IT IS THE PROJECT'S OWN, POINTED AT ME:** ⛔ **A REGISTER IS ONLY A SINGLE SOURCE OF TRUTH IF YOU READ IT BEFORE WRITING TO IT.** I checked the register for the highest number in use and never grepped the other docs. ➡️ **BEFORE OPENING A TEST NUMBER, SEARCH EVERY PROJECT DOC FOR IT — not just this file.**

⚠️ **AND NOTE WHAT T46 MEANS FOR T47:** the register's own T41 found that opponent-adjusted `vs-position` carries no reliable per-defence signal, and T45 found SoS adjustment makes player projections **worse in 8 arms of 8**. ⛔ **T47 must therefore NOT reach for a defensive opponent term as its new input.** ✅ **Injuries and depth charts are a different thing entirely — they describe WHO IS PLAYING, which is the one input a season average genuinely cannot contain, and nothing measured this week bears on them.**


---

# 🔴 T51 — THE NFL SNAP FLOOR. PRE-REGISTERED 2026-09-03, BEFORE THE FIRST BOARD SHIPPED.

⚠️ **THIS IS NOT A MODEL TEST. IT IS A DENOMINATOR TEST**, and the denominator is now load-bearing on a live page.

**THE CLAIM UNDER TEST:** a player's own hit rate, computed over games where he played **at least 50% of his team's offensive snaps**, is a better guide to the next game than the same rate computed over **every logged game**.

🔴 **WHY IT CANNOT WAIT AND WHY IT CANNOT BE SKIPPED.** Measured on 2025 NFL WR/TE, the floor is worth **23.9 points**:

| snap floor | games | under 2.5 rec | under 39.5 rec yds |
|---|---|---|---|
| none | 3,979 | **62.2%** | 73.4% |
| 0.25 | 3,088 | 51.7% | 66.4% |
| **0.50** | 2,147 | **38.3%** | 56.1% |

⛔ **THIS IS MLB's CAMEO BUG IN ANOTHER SPORT.** A WR3 on **16% of snaps** who catches nothing is not evidence about a WR1's line — and with no floor those blanks put short unders on top of the board, exactly as `pa > 0` did to MLB hitters before it became `pa >= 3` (+37.4 points, measured over 37,829 games).

✅ **THE FLOOR SHIPPED AT 0.50 AS A BRIGHT LINE** — *a majority of his team's offensive snaps is a starter's role* — ⛔ **NOT read off the table above for the friendliest number.** ⚠️ **That distinction is the whole point of pre-registering it:** the table was computed first, so choosing from it would have been fitting.

📌 **THE BAR, FIXED NOW:** over the 2026 season, on rows the board actually published, the 0.50-floor rate must beat the no-floor rate on **Brier score** by **≥ 0.005**, on **≥ 200 graded rows**. ⚠️ **Under 200 rows it reports NOT YET MEASURABLE — not a pass, not a fail.**
⛔ **FORBIDDEN VARIANTS, NAMED NOW:** no sweep over floors, no per-position floor, no "0.45 was better" after the fact. **One run.** If 0.50 loses, the finding is recorded and a NEW test is pre-registered — the floor does not get nudged.

⚠️ **PREDICTION, ON THE RECORD:** the floor **holds** (0.50 beats no-floor) but by **less than the 23.9-point in-sample gap suggests** — most of that gap is the market already pricing the cameo games out.
🔴 **AND THE STANDING CAVEAT: MY LAST FOUR MAGNITUDE PREDICTIONS WERE ALL WRONG (T48, T49, T47, T50). The DIRECTION is the part worth grading.**

---

# 🔴 T52 — CAN A COLLEGE DENOMINATOR BE RECOVERED AT ALL? OPENED 2026-09-03.

⛔ **THIS ONE IS BLOCKED ON DATA, NOT ON ANALYSIS, AND IT IS WHY THE COLLEGE BOARD SHIPS WITH NO RATE.**

**THE MEASUREMENT, 2026-09-03:**

| | games with ZERO catches |
|---|---|
| **NFL receivers** | **25.8%** |
| **College receivers** | **3.5%** |

🔴 **THE MECHANISM, CONFIRMED NOT ASSUMED:** nflverse carries **snap counts**, so an NFL receiver is logged for every game he was **on the field** — **79.1%** of his zero-catch games have `snaps > 0`. CFBD carries **none**, and `players-<yr>.json.gz` says so in its own `consumer_contract`: *"NO SNAP DATA EXISTS FOR COLLEGE FOOTBALL."* A college player is therefore logged **only when he touched the ball**.

⛔ **THE COST: the median college receiver is missing SIX of his team's THIRTEEN games, and 69.6% are missing three or more.** Roughly **half the denominator is absent, and the absent half is systematically the quiet half.** A rate built on it reads **too high on every over**.

⚠️ **AND THE TWO CAUSES CANNOT BE SEPARATED.** A missing college game is either *"played and did not touch the ball"* or *"did not play"*. **Assuming the first inflates unders; assuming the second inflates overs.** ⛔ **There is no third option in this data** — the file's own contract warns of exactly this ambiguity for `ahead_out_lastwk`.

📌 **WHAT WOULD CLOSE IT:** a participation source — a snap count, a depth chart with game-by-game actives, or a play-by-play feed from which appearances can be counted. ⚠️ **PROBE IT BEFORE PROMISING IT.** ⛔ **Until then the college board carries a price and no rate, and the page says why in one sentence.**

🔴 **THE PRINCIPLE THIS IS AN INSTANCE OF, AND IT IS THE PROJECT'S MOST-REPEATED FAILURE — now roughly the eleventh:** ⛔ **A FACT ABOUT A QUERY IS NOT A FACT ABOUT THE WORLD.** The college log answers *"games in which he recorded a stat"*. It was about to be read as *"games he played"*. **Those are different questions and only one of them is a denominator.**

---

# 🔴 T53 — CAN THE NFL's SCORE BY QUARTER BE RECOVERED FROM PLAY-BY-PLAY? PRE-REGISTERED 2026-09-04, **BEFORE THE DERIVATION WAS RUN AGAINST A SINGLE REAL ROW.**

⚠️ **NOT A MODEL TEST. A DATA-RECOVERY TEST**, in the same class as T51's snap floor and T52's denominator question — it asks whether a source can support a claim, not whether a claim predicts anything.

## The gap

**The college box score shows quarters; the NFL one did not.** CFBD returns `homeLineScores`/`awayLineScores` free on a call the collector already makes. ⛔ **nflverse's `games.csv.gz` has no per-quarter column at all** — measured by `nfl.py`'s own probe, which lists every column, not inferred from a failed lookup.

## Why the answer was NOT "add a source"

✅ The quarters are recoverable from **`play_by_play_{y}`, a file the collector already downloads twice** (`build_routes` for its pass flag, `build_def_epa` for T48). **No new vendor, no new key, no credit — the Odds API is not involved at any point.** ⚠️ It is a third download of a large file on a weekly job; **a shared cache was deliberately NOT added** — one mutable copy of 200MB of rows passed between three builders is a worse risk than a repeated download.

## The method

**The per-quarter increase in the cumulative score**, taking the **MAXIMUM** cumulative score reached within each quarter. ⛔ **NOT the last row.** A cumulative score is monotone, so a maximum is order-independent; reading "the last play of the quarter" would make our numbers depend on how the vendor happened to sort their file.

## 🔴 THE BARS, FIXED IN THE CODE BEFORE ANY OF THIS DATA WAS SEEN

⚠️ **THE BUILD CONTAINER HAS NO OUTBOUND NETWORK, so the derivation could not be run against real nflverse data before shipping.** ⛔ **That is stated rather than hidden, and it is precisely why the bars live in the code and the report is written pass or fail.**

| # | bar | consequence of failing |
|---|---|---|
| 1 | a quarter column, a cumulative home score, a cumulative away score and a game id are all present | write **NOTHING**; the report lists what *was* available |
| 2 | 🔴 **the quarters sum to the final, EXACTLY, per game** | the game is **DROPPED and counted**, never displayed |
| 3 | coverage **≥ 95%** of games the schedule marks final | write **NOTHING** |
| 4 | **overtime agreement ≥ 99%** | write **NOTHING** |
| 5 | the play-by-play's home team **is** the schedule's home team | the game is dropped |

### ⚠️ Bar 2 exists to test the ONE assumption that could not be verified from here

**Is the cumulative score the score AFTER the play, or BEFORE it?** If it is *before*, the last score of every quarter is missing and **every quarter comes out short by a score.** ✅ **Under bar 2 that fails on EVERY game and nothing ships** — so a wrong assumption fails loudly instead of putting a plausible-looking, uniformly wrong line score on a page Sam bets from. `test_line_scores.py` §2 constructs a before-the-play feed on purpose and proves it writes nothing.

### ⚠️ Bar 4 is genuinely independent, which is the whole reason it is worth having

`overtime` comes from **`games.csv.gz`**; the period count comes from **the play-by-play**. **Two different FILES agreeing is evidence. One file agreeing with itself is not.**

### Bar 5 is the run-line attribution bug in another sport

Quarters attached to the wrong side is exactly the failure that put implied runs on the wrong MLB team on 3 of 19 games (2026-08-26).

## 📊 THE STATE AT PRE-REGISTRATION, MEASURED ON THE LIVE PAGE

```
NFL 2026 schedule:  272 games,  0 final
```

🔴 **So the scheduled path can derive NOTHING until week 1 is played (2026-09-09), and the first real chance is the Tuesday rebuild on 2026-09-15.** ⚠️ **This is why the code also derives any season a run asks for by name:** a hand-dispatched `SEASON=2025` is how T53 gets measured against real football **before it has to work**, rather than discovering the answer on a live page in the middle of week 2.

## 📌 WHAT WOULD CLOSE IT

**`data/nfl/latest/linescore-probe-2025.json` from a hand-dispatched `nfl-logs` run.** Three outcomes, all useful:
- `"usable": true`, coverage near 100% → **adopted**, and 2026 fills in automatically after week 1.
- an error naming a **sum mismatch on every game** → the cumulative score is "before the play"; a one-line change, and the report says so exactly.
- an error naming **missing columns** → the schema differs from what the code names, and the report lists what is actually there.

⚠️ **⛔ THE BARS ARE NOT TO BE MOVED AFTER THAT FILE IS READ.** If coverage lands at 94% the answer is that it did not clear, not that 94 was always fine.

## Scope, stated so it is not mistaken for an oversight

⛔ **Not every season.** The current season always, plus any season when the run asked for exactly one. A `SEASON=2021-2025` back-fill does **not** pull five play-by-play files to produce quarters nobody can click into — the Scores tab renders the current season only.

⚠️ **The renderer was already correct and needed no change.** It draws whatever length of line score it is given; verified by driving it, regulation (`1 2 3 4 T`) and overtime (`1 2 3 4 OT T`), totals matching. ✅ **One renderer, one shape, two leagues that reach it by different routes — the page must never learn the difference.**

---

# 🔴 T52 — **SUBSTANTIALLY REVISED 2026-09-04. THE ORIGINAL COMPARISON ASKED TWO DIFFERENT QUESTIONS, AND THE GAP LARGELY DISAPPEARS WHEN THEY ARE MADE THE SAME.**

⚠️ **NOTHING BELOW COST A CREDIT OR A FETCH.** Every number is a query over `players-2025.json.gz` for both leagues, already in the repo.

## ⛔ What the original finding compared

| | logged when… |
|---|---|
| **nflverse** | the player took **a snap** |
| **CFBD** | the player **recorded a stat** |

**"NFL receivers 25.8% zero-catch games vs college 3.5%" is a comparison between those two definitions.** A file that logs snap-only games *necessarily* shows more zero-catch games than one that does not. 🔴 **That gap is produced by the two file formats. It is not a measurement of how much college data is missing.**

📌 **TWELFTH INSTANCE OF THE PROJECT'S MOST-REPEATED FAILURE — and this time it was one of our own headline findings.** ⛔ *A fact about a query is not a fact about the world.*

## ✅ The like-for-like measurement — **share of the player's TEAM's games**, both leagues, same filter (≥3 games in the stat, team with ≥8 games)

| | college WR | NFL WR | college TE | NFL TE | college RB | NFL RB |
|---|---|---|---|---|---|---|
| games with a **receiving** row | 0.733 | 0.706 | 0.583 | 0.647 | 0.500 | 0.588 |
| games with **any** of rec/car/att | **0.750** | **0.706** | **0.615** | **0.657** | **0.857** | **0.882** |
| **games he ACTUALLY PLAYED** | *unknown* | **0.842** | *unknown* | **0.756** | *unknown* | **0.941** |

🔴 **COLLEGE IS NOT MEANINGFULLY WORSE THAN THE NFL ON THE SAME CONSTRUCT.** College WR is *higher* than NFL WR. The three union figures sit within **2.5 points** of each other across both leagues.
⚠️ **The doc's "median college receiver is missing SIX of THIRTEEN games" is not contradicted — it is a different population.** For players who could actually be **carded** (≥3 receiving games) the shortfall is **27%**, and the NFL's, measured identically, is **29%**.

## ✅ The union denominator is a large win for RBs and a rounding error for WR/TE — **replicated in BOTH leagues**

| | college gain | NFL gain |
|---|---|---|
| WR | +1.7 pts | +0.0 pts |
| TE | +3.2 pts | +1.0 pts |
| **RB** | **+35.7 pts** | **+29.4 pts** |

⛔ **A receiver genuinely only appears when he catches something.** A back appears because he carried it. **Two leagues, same shape — that is a replication, not a one-season artifact.**

---

# 🔴 T52b — HOW WRONG IS A UNION DENOMINATOR? **RUN 2026-09-04 IN THE NFL, WHERE THE TRUTH IS KNOWN.**

## The design

✅ **Measure the error where it can be measured.** In the NFL the true denominator exists (**snaps > 0**). So: compute each player's over-rate at real lines **twice** — once over the union denominator (what college would have) and once over the true one — and take the difference. **The NFL is the laboratory; college is where the answer gets used.**

## 🔴 THE BAR, FIXED BEFORE THE NUMBERS WERE PRINTED

> The card buckets confidence into **10-point calibration bands** (under-60 / 60-70 / 70-80 / 80+). A denominator error that can move a row **across a band** changes what the page says about a bet.
> ⛔ **median |bias| ≤ 3.0 points AND p90 |bias| ≤ 8.0 points.**
> 3 is comfortably inside a 10-point band; 8 is where a row near a band edge starts crossing it.

⚠️ **Jeffreys-smoothed exactly as the card smooths, so the comparison is against the number the page would really print.**

## 📊 RESULT — **PASS, pooled**

```
POOLED   n=2,142 player-market-lines
         median |bias| 0.21 pts      p90 |bias| 3.79 pts
BAR      median <= 3.0               p90 <= 8.0
```

**The bias is systematically POSITIVE on overs** — the union denominator is too small, and the games it misses are the quiet ones. ⚠️ **Small, but one-directional, which this project treats as more dangerous than noise.**

### ⛔ AND ONE CELL FAILS ITS SUB-BAR. IT IS REPORTED, NOT BURIED.

| cell | median | p90 | max |
|---|---|---|---|
| **WR receptions o2.5** | +2.19 | **8.58** 🔴 | 19.44 |
| WR receiving yds o39.5 | +1.92 | 7.93 | 16.48 |
| WR receptions o3.5 | +1.32 | 5.00 | 12.50 |
| TE receptions o2.5 | +2.05 | 6.25 | 11.11 |
| RB carries / receptions, every line | +0.00 | ≤1.61 | ≤9.64 |

🔴 **The damage concentrates exactly where theory says it must: the LOW receiving lines, where a missing zero-catch game is the difference between a hit and a miss.** ✅ **RB markets are clean at every line tested.**

## 📌 WHAT THIS LICENSES, AND WHAT IT DOES NOT

✅ **A college rate over a UNION denominator is defensible for RB markets at every line tested, and for receiving lines of 3.5 and above.**
⛔ **It is NOT defensible at WR/TE receptions 2.5 or receiving yards 39.5**, where p90 bias reaches or exceeds the 8-point sub-bar.
⚠️ **THE TRANSFER IS AN ASSUMPTION, AND IT IS NAMED:** the bias was measured in the NFL and applied to college. The supporting evidence is that the union/team-game ratios sit within 2.5 points across both leagues. **That is support, not proof.**
⚠️ **POPULATION:** the 2025 college logs were built under the old **Power-4** scope — 67 teams, 12–16 games each. These are the teams whose players get carded, so it is the right population, but it is not all of FBS.

## ⏳ THE DECISION IS SAM'S, AND IT IS THE ONE HE ALREADY HAS OPEN

> *"ship college rates anyway with a warning, or keep them off?"*

**This is the measurement that decision was waiting on.** ⛔ **The bars above must not be moved after the fact whichever way he calls it.**

---

# ✅ 🔴 T53 — **CLOSED 2026-09-04. PASSED ON EVERY BAR, WITH NOTHING TO ROUND.**

**Run:** `nfl-logs`, `SEASON=2025`, dispatched by Sam. Report:
`data/nfl/latest/linescore-probe-2025.json`, written 04:52:32Z.

```
games_final_in_schedule  285          play-by-play rows   48,771
games_derived            285          coverage_pct        100.0
dropped_sum_mismatch       0          dropped_home_side     0
overtime_checked         285          overtime_agreement  100.0
columns_used   qtr · total_home_score · total_away_score · game_id · home_team
```

## 🔴 THE ONE THING I COULD NOT VERIFY BEFORE SHIPPING IS NOW ANSWERED

**The cumulative score is the score AFTER the play.** ⚠️ That was the
single assumption the build container could not check — no network — and
bar 2 existed precisely to catch it being wrong. **`dropped_sum_mismatch`
is 0 across all 285 games**, which is only possible if the reading was
right; had it been "before the play", *every* game would have come up
short and nothing would have shipped.

✅ **The fail-loud design did its job by not needing to.**

## ✅ RE-DERIVED INDEPENDENTLY FROM THE SHIPPED ARTIFACT, NOT FROM THE REPORT

⛔ A probe that grades itself is not evidence. `schedule-2025.json.gz` was
re-checked from scratch:

| | |
|---|---|
| games with quarters | **285 of 285** |
| quarters summing to the final | **285 of 285**, 0 mismatches |
| period counts | **269 four-period, 16 five-period** |
| five-period games the SCHEDULE also flags `overtime` | **16 of 16** |
| games flagged `overtime` with only four periods | **0** |

🔴 **THE OVERTIME CROSS-CHECK IS THE STRONGEST RESULT HERE, AND IT IS
GENUINELY INDEPENDENT:** `overtime` comes from `games.csv.gz`, the period
count from `play_by_play`. **Two different files, 285 games, perfect
agreement in both directions.**

⚠️ **A TIE SURVIVED IT.** `GB [7,6,7,17,3] = 40 @ DAL [0,16,7,14,3] = 40`,
overtime, both sides scoring 3 in the fifth period — **the exact shape
that breaks a naive derivation**, and it reconciles.

## 📌 WHAT HAPPENS NEXT WITHOUT ANYONE DOING ANYTHING

The Tuesday `nfl-logs` cron runs `SEASON=CUR`, which is one season, so
2026 derives on the same path. ⚠️ **2026 has 272 scheduled games and zero
finals as of 2026-09-04**, so the first real quarters appear on the
**Tuesday 2026-09-15 rebuild**, after week 1.

## ⚠️ WHAT THIS DOES NOT CLOSE

⛔ **Only seasons the run asks for by name, plus the current one.** A
`SEASON=2021-2025` back-fill still skips the derivation, deliberately —
five large play-by-play downloads to produce quarters no surface renders.
**If a historical box score is ever wanted on the page, that is a new
decision, not an oversight.**

---

# 🔴 T54 — **SHOULD A RECORD AGAINST A LINE THE PLAYER NEVER FACED BE *RANKED* AT ALL?** OPENED AND SPECIFIED 2026-09-04, **BEFORE ANY CUTOFF WAS TRIED.**

## The observation, from the first rated college board

`[measured 2026-09-04, the first college card to carry rates]`

| conf | row | record | his own 2025 mean | line ÷ mean |
|---|---|---|---|---|
| 94 | KD Daniels under 34.5 rush yds | 8 of 8 | 15.0 | 2.30 |
| **94** | **Alberto Mendoza under 204.5 pass yds** | **8 of 8** | **35.8** | **5.72** |
| 88 | Ty Clark III under 86.5 rush yds | 11 of 12 | 26.9 | 3.21 |

🔴 **Mendoza was a BACKUP QB in 2025 and the book has priced him as a
starter.** His record is **factually correct** and **carries no
information about this line** — he never faced anything like it.

⚠️ **THIS IS MLB's CAMEO BUG IN A THIRD SPORT.** The NFL board is
protected by `SNAP_FLOOR = 0.50`; ⛔ **college publishes no snap data at
all**, so the same protection cannot be built.

## 📊 THE SIZE OF IT, MEASURED BEFORE ANY REMEDY WAS CHOSEN

```
UNDER rows: median line ÷ own mean = 1.32     (30 rows)
OVER  rows: median line ÷ own mean = 0.77     (13 rows)
rows with line >= 2x own mean:  3 of 43, all unders
```

✅ **The skew is mostly rational** — a record board *should* take unders
where the line sits above a player's history. **Three rows, not fifty.**

## ✅ WHAT WAS SHIPPED IMMEDIATELY, AND WHY IT IS NOT THIS TEST

Every rated row now states the player's **own per-game average beside the
line**, over the same games the rate used, plus a plain-English warning
when the line is **2x or more** away from it. ⚠️ **That 2x IS a threshold**
— but it governs whether a **sentence** appears, never whether a **row**
ships. ⛔ **Adding information is always safe; removing rows is not.**

## 🔴 THE QUESTION THIS TEST ASKS

> **Does a row whose line sits far outside the player's own historical
> range perform worse than the rest of the board?**

⛔ **NOT "does the board look better without them".** That is the question
that gets answered by deleting rows until a page pleases, and it is
forbidden.

## 🔒 THE SPECIFICATION, FIXED NOW, BEFORE ANY OUTCOME IS GRADED

- **Population:** every published football pick carrying `confidence` and
  `own_mean`, both leagues, graded W/L by the normal record path.
  ⛔ Voids excluded from every denominator, as always.
- **The split, declared now:** `stretch = line / own_mean` (and its
  reciprocal for OVER rows, so the measure is symmetric). **STRETCHED =
  `stretch >= 2.0`; NORMAL = everything else.** ⚠️ **The 2.0 is inherited
  from the sentence threshold already shipped — it is NOT re-chosen here**,
  because re-choosing it after seeing outcomes is the whole failure mode.
- **Metric:** hit rate minus mean stated confidence — **the calibration
  gap** — computed separately for STRETCHED and NORMAL.
- **MINIMUM SAMPLE: 40 graded STRETCHED rows.** ⚠️ Under that it reports
  **NOT YET MEASURABLE** — not a pass, not a fail. On the current board
  stretched rows are ~7% of the card, so this is **months** of slates.
- **PASS (they are fine as they are):** the STRETCHED calibration gap is
  no worse than the NORMAL gap by more than **5 percentage points.**
- **FAIL:** worse by more than 5 points → **stretched rows stop being
  RANKED.** ⚠️ They are still **shown**, still labelled, still carrying
  their warning — they are removed from the *ordering*, exactly as the
  unrated college rows were before today.
- ⛔ **ONE SPECIFICATION. NO SWEEP over the stretch cutoff, the metric or
  the position.** If it fails it is logged and the consequence above is
  applied; if it passes it is logged and nothing changes.

## 🔴🔴 2026-09-12 — IT COULD NEVER HAVE BECOME MEASURABLE, AND NOTHING SAID SO

`[measured 2026-09-12, eight days after this test was opened]`

```
published football picks carrying own_mean    339 of 339
GRADED rows carrying own_mean                   0 of 200
```

⛔ **`record_fb.py` BUILT ITS GRADED ROWS WITHOUT `own_mean`**, so the
predictor this test splits on was **discarded at grading time**. The
sample was not small — it was **structurally stuck at zero**, and no
number of slates could ever have moved it.

⛔ **THAT IS NOT "NOT YET MEASURABLE FOR LACK OF SAMPLE", AND COLLAPSING
THE TWO IS THE DEFECT.** One is a thin slate and waits. The other is a
broken pipeline and waits forever — **while this register says the test
is in progress.** ➡️ **An owed test that cannot accumulate is worse than
one nobody opened** (ledger rule 225).

✅ **FIXED BY CARRYING ONE FIELD. NOTHING IS COMPUTED DIFFERENTLY** —
`stretch = line / own_mean` is still derived by the consumer exactly as
specified below. ⚠️ **The history is recoverable**: every stored card
still holds the field, so a re-grade replays it.

✅ **AND IT NOW READS ITSELF.** `t54.py` runs on the `fb-record` job —
the job that writes the file it reads — so the count can never be staler
than the record. ⛔ **A pre-registered test that depends on being
REMEMBERED is checked when it is convenient to like the answer** (rule
226). It is a **MEASUREMENT, NOT A GATE**: only the new **BLOCKED**
verdict exits non-zero, because BLOCKED means the test cannot run at all.

### ⚪ WHERE IT STANDS

```
graded rows          135
...carrying own_mean 110
STRETCHED  n=5  of the 40 required     →  NOT YET MEASURABLE
```

⛔ **THE EARLY SPLIT LEANS HARD AND IS PRINTED AND MUST NOT BE ACTED ON.**
Reading a lean off five rows is exactly what a pre-registered minimum
exists to stop — **including, and especially, when the lean points the
way you expected.** ⛔ **The cutoff, the minimum and the tolerance are
asserted by `test_t54.py` against the values fixed on 2026-09-04**, so
running this test cannot quietly become re-choosing it.

## ⚠️ WHY THIS IS NOT ANSWERED BY BORROWING `usage_floor: 3.0`

The college logs carry `usage_floor: 3.0` and the file says *"applied by
the consumer, not by this build"*. ⛔ **That floor is not available for
this.** T37-CFB froze it on **`trailing_usage`**, among rows **already
passing a depth-rank cap**, for a **model-fitting population** (2021–23,
regular season weeks 4–15). 🔴 **Using a bar frozen for one purpose as a
filter for a different estimator is specification shopping with extra
steps** — and T37-CFB's own entry forbids re-deriving or re-arguing it.
**If a usage floor belongs in the rate denominator, it gets its own
pre-registered derivation.**

---

## T55. ⛔ 🔴 **CLOSED VOID, 2026-09-04, SAME DAY IT WAS OPENED — THE SPECIFICATION WAS INVALID, AND IT WAS INVALID BEFORE ANY DATA WAS SEEN.** ~~THE RIGHT-SKEW ARTIFACT IN T37~~ — is a MEAN projection the wrong number to publish against a 0.5 line?

**Opened 2026-09-04.** ⛔ **THIS IS NOT A RE-DECISION OF T37.** T37's bar
(≤5.0% contradictions at 70%+) stays exactly where it was pre-registered,
is not moved, and is not re-argued. This is a **separate question about
which statistic we publish**, and it gets its own bar, fixed below, before
anything is measured against it.

## 📊 WHAT WAS OBSERVED, AND WHY IT IS ONLY A MOTIVATION

`[measured 2026-09-04 on the live pooled population]` T37's hitter half sat
**exactly on its bar** — 63 of 1252 pooled rows = **5.03%** against ≤5.0%
counted from the live board, and **4.99%** counted from the published card.
🔴 **A check that flips red and green as the odds move is an unstable
alarm, and an unstable alarm is the failure mode `card_gate` exists for.**

```
batter_rbis           under 0.5   53   ← 84% of every contradiction
batter_total_bases    under 1.5    8
batter_hits_runs_rbis under 1.5    2

median |projection - line| = 0.03      max = 0.20
36 of 63 sit within 0.05 of the line
```

⚠️ **BOTH NUMBERS ARE CORRECT AND THEY ARE DIFFERENT STATISTICS.** A hitter
who records zero RBI in 70% of his games can average 0.53 RBI/game — the
occasional 2- and 3-RBI night drags the mean up. The confidence is a
**frequency** fact (`P(X < 0.5)`); the projection is a **mean** fact
(`E[X]`). ⛔ **On a right-skewed count at a 0.5 line, `E[X] > 0.5` and
`P(X < 0.5) > 70%` are simultaneously true, so "the projection contradicts
the row" is measuring an artifact of comparing two different statistics —
not a defect in either.**

## 🔴 THE QUESTION

> **Does publishing the MEDIAN (or the modal outcome) instead of the MEAN,
> on markets whose line is 0.5, remove the contradiction WITHOUT making the
> published number less accurate?**

⛔ **NOT "does it make T37 go green".** That is the question answered by
choosing whichever statistic flatters the check, and it is forbidden.

## 🔒 THE SPECIFICATION, FIXED NOW, BEFORE ANY OUTCOME IS SEEN

- **Population:** every published MLB hitter row carrying `projection` and
  `confidence`, on a market whose `line` is `0.5`, graded W/L by the normal
  record path. ⛔ Voids excluded, as always.
- **The two candidates, declared now:** `MEAN` (what ships today —
  `hitter_mean`) and `MEDIAN` (the player's median outcome over the same
  games the rate used). ⛔ **NO third candidate, no sweep over trimming,
  smoothing or shrinkage.** If both fail, both fail.
- **Metric — accuracy, and it is the PRIMARY one:** mean absolute error of
  the published number against the player's ACTUAL outcome that night.
- **Metric — the artifact, and it is SECONDARY:** the share of rows where
  the published number sits on the losing side of the line at 70%+
  confidence.
- **MINIMUM SAMPLE: 250 graded 0.5-line rows.** ⚠️ Under that it reports
  **NOT YET MEASURABLE** — not a pass, not a fail.
- **PASS (switch to MEDIAN):** MEDIAN's MAE is **no worse than MEAN's by
  more than 0.05** AND its contradiction share is **at least 3 points
  lower**. ⛔ **Both conditions, or no change.** A number that agrees with
  the confidence by being less accurate is a worse number, not a better one.
- **FAIL (keep MEAN):** anything else. The projection keeps shipping the
  mean and T37's hitter half is understood to be measuring the artifact —
  ⚠️ **which is a finding to record, NOT a licence to move T37's bar.**
- ⛔ **ONE SPECIFICATION. The bars above were written before the first
  measurement and are not re-chosen after it.**

## ⚠️ WHAT IS OWED TO SAM IN THE MEANTIME

**T37 is failing now and `card-accepted.txt` is his file alone.** He was
given three options on 2026-09-04 — accept it, leave it red (and lose the
next card), or wait for this test — with the exact line to paste if he
accepts. ⛔ **Claude does not write that file, and the card stays refused
either way.**


---

# ⛔ T55 — THE RESULT, AND WHY IT IS **VOID** RATHER THAN **PASSED**

`[run 2026-09-04, about four hours after the spec was written, on 6,337
graded 0.5-line hitter rows across 8 stored slates]`

## 🔴 IT "PASSED", AND THE PASS IS WORTHLESS

```
                      MEAN      MEDIAN     the registered bar
  MAE                 0.6147    0.5119     median <= mean + 0.05   -> PASS
  contradictions@70%  6.87%     0.00%      drop >= 3.0 points      -> PASS
                                            verdict: "switch to MEDIAN"
```

⛔ **BOTH BARS CLEARED AND THE TEST STILL PROVES NOTHING, BECAUSE MEAN
ABSOLUTE ERROR IS MINIMISED BY THE MEDIAN AS A MATTER OF ARITHMETIC.**
Scoring two candidates with a loss function that one of them minimises by
construction is not a comparison. 🔴 **I chose that metric, and its flaw
needed no data to see. Registering it was the error, not running it.**

## 📊 THE DIAGNOSTIC THAT MAKES IT UNARGUABLE

```
  RMSE       MEAN 0.8523   MEDIAN 0.9088    <- minimised by the MEAN, by construction
  BIAS       MEAN +0.0467  MEDIAN -0.1767    (published minus actual)
```

⚠️ **EACH METRIC ELECTS ITS OWN ESTIMATOR.** MAE picks the median, RMSE
picks the mean, and neither is evidence about which number belongs on the
page. ⛔ **A test that could not have come out any other way is decoration.**

## ✅ WHAT THE DATA DOES SAY, ON MEASURES NO BAR WAS SET FOR

- 🔴 **The published MEAN is very nearly unbiased: +0.047 over 6,337
  rows.** It is a good number.
- 🔴 **The MEDIAN is badly biased low (−0.177)** and **would print `0.0`
  on 3,761 of 6,337 rows — 59% of the board.** A projection column reading
  zero on three rows in five is not a projection anyone can use.
- ➡️ **THE MEAN KEEPS SHIPPING.** ⛔ Not because T55 failed — it is void,
  it neither passed nor failed — but because **nothing has displaced the
  status quo**, and two measures nobody set a bar for both point the same
  way.

## ⚠️ AND SO T37 KEEPS FIRING, WHICH IS THE HONEST END STATE

T37's contradiction count is measuring **`E[X] > 0.5` and `P(X < 0.5) >
70%` being simultaneously true for a right-skewed count** — an artifact of
comparing a mean against a frequency, not a defect in either number.
⛔ **The bar is not moved, and `card-accepted.txt` is Sam's file alone.**
What this run adds to his decision: **there is no better number available
to publish**, so T37 will keep firing until T56 says otherwise.

---

## T56. ✅ 🔴 **CLOSED — RUN 2026-09-04. BOTH CANDIDATES PASS; THE REGISTERED CONSEQUENCE IS *KEEP THE MEAN*.** THE NON-CIRCULAR REPLACEMENT — IS THE PUBLISHED PROJECTION ANY USE AS A PREDICTION OF THE LINE?**

**Opened 2026-09-04. The specification below was written before the metric
was computed on a single row.** ⛔ **This is not T55 re-run with friendlier
bars.** T55's metrics were *estimation* losses, and an estimation loss is
minimised by a particular estimator. **This asks a decision question**, and
neither candidate minimises it by construction.

## 🔴 THE QUESTION

> **When the published number sits on one side of the line, does the
> ACTUAL outcome land on that side more often than the constant
> predictor?**

That is the only thing the number on the page does: a reader sees `0.53`
beside a `0.5` line and takes it as a nudge toward the over. ⛔ **If it
carries no signal about the side, it should not be printed beside the line
at all — and that is a real possible outcome of this test.**

## 🔒 THE SPECIFICATION, FIXED NOW

- **Population:** identical to T55's and to T37's — **every priced MLB
  hitter row** carrying `projection` and `confidence`, on a market whose
  `line` is `0.5`, from a stored card whose slate is settled, with the
  actual outcome recoverable from the stored box score. ⛔ Voids excluded.
- **The two candidates:** `MEAN` (shipping today) and `MEDIAN`. ⛔ No
  third candidate, no sweep.
- **The classifier:** `sign(published − line)` — **PREDICTED OVER** when
  `published > line`, **PREDICTED UNDER** otherwise.
- **METRIC:** the share of rows where
  `sign(published − line) == sign(actual − line)`. ⚠️ **Reported
  separately for predicted-over and predicted-under rows**, because a
  candidate that almost always predicts one side can score well on the mix
  while being useless.
- **THE BASELINE, DECLARED NOW:** the **majority-class rate** — always
  predicting whichever side is more common in the population. ⛔ **Beating
  a coin flip is not the bar. Beating the constant predictor is.**
- **MINIMUM SAMPLE: 1,000 rows, AND at least 200 rows in each predicted
  class.** ⚠️ Under either, **NOT YET MEASURABLE** — not a pass, not a
  fail. 🔴 **The second condition is the one that matters:** T55 showed the
  median predicts UNDER on 59% of rows, so a candidate can starve its own
  minority class and be scored on almost nothing.
- **PASS for a candidate:** overall sign accuracy beats the majority-class
  baseline **by at least 3 percentage points**, AND accuracy within
  **each** predicted class is at least **50%**.
- **THE CONSEQUENCES, FIXED NOW:**
  - **MEAN passes, MEDIAN does not** → nothing changes; the mean keeps
    shipping and **T37's failure is recorded as measuring an artifact.**
  - **MEDIAN passes and beats MEAN by ≥ 3 points** → the 0.5-line
    projection switches to the median. ⚠️ **And the 59%-print-zero problem
    must be solved in the same drop, or it does not ship.**
  - **NEITHER passes** → 🔴 **the projection stops being printed beside a
    0.5 line at all.** ⛔ A number with no signal about the side is worse
    than a blank, because a reader will use it.
  - **BOTH pass** → keep the mean; it is unbiased and already shipping.
- ⛔ **ONE SPECIFICATION. The bars are not re-chosen after the
  measurement, and an inconvenient result is logged inconvenient.**


---

# ✅ T56 — THE RESULT

`[run 2026-09-04, immediately after the specification above was written
and before the metric was computed on any row. n = 6,337.]`

```
  actual OVER 2,479 of 6,337 = 39.1%
  MAJORITY-CLASS BASELINE (always predict UNDER) = 60.88%

           predicted OVER          predicted UNDER        overall   vs baseline
  MEAN     3,630  acc 52.84%       2,707  acc 79.28%      64.13%     +3.25  ✅ PASS
  MEDIAN   2,556  acc 59.86%       3,781  acc 74.90%      68.83%     +7.95  ✅ PASS
```

## 🔴 THE FIRST EVIDENCE THE HITTER PROJECTION IS WORTH PRINTING AT ALL

⚠️ **This is the thing T37 could never tell us.** T37 asks whether the
projection *agrees with our own confidence*; **T56 asks whether it agrees
with what actually happened.** The mean beats the constant predictor by
**+3.25 points**, clearing a bar fixed in advance, with **both** predicted
classes above 50%. ✅ **The number on the page carries signal. It stays.**

## ⛔ AND THE CONSEQUENCE IS THE ONE THAT WAS WRITTEN DOWN: KEEP THE MEAN

**BOTH pass → keep the mean.** That clause was fixed before the numbers
were seen and it is applied as written.

🔴 **I RECORD, LOUDLY, THAT IT LOOKS WRONG IN HINDSIGHT.** The median beat
the mean by **4.7 points** on a metric neither of them minimises by
construction — and my "both pass" clause set no margin, so it cannot see
that. ⛔ **That is a defect in the specification and it is logged as one.
It is NOT grounds to switch now** — running tests until one licenses a
change already wanted is the failure this whole register exists to stop.

⚠️ **AND THE MEDIAN IS NOT SHIPPABLE ANYWAY, ON T55's OWN DIAGNOSTIC:** it
would print **`0.0` on 3,761 of 6,337 rows — 59% of the board.** So
keeping the mean is right on the merits, not only by the letter of the
clause. ➡️ **Any future switch needs a test registered with BOTH a margin
bar AND a solved zeros problem, before it is run.**

## ⚠️ WHAT THIS DOES NOT DO

⛔ **It does not clear T37.** T37 measures agreement between a mean and a
frequency at a 0.5 line, which is an artifact, and no result here moves
that bar. **T37 keeps firing, and accepting it remains Sam's decision
alone.**

---

# 🔴 T37 — SAM ACCEPTED IT, 2026-09-04

**Sam, asked directly what the decision was, answered: "yes i accept it."**

⛔ **WHAT HE ACCEPTED, AND WHAT HE DID NOT.** He accepted that the run
stops going red for a decision already taken. ⚠️ **He did NOT accept a
published card**: `card_gate` makes the RUN green and **the card is still
reverted either way** (ledger rule 73). The page still says the card was
refused.

## THE STATE OF THE MEASUREMENT AT THE MOMENT OF THE DECISION

```
63 of 1215 pooled priced rows = 5.2%   against a pre-registered 5.0%
   batter_rbis    under 0.5    53      <- 84% of every contradiction
   batter_total_bases 1.5       8
   batter_hits_runs_rbis 1.5    2
median |projection - line| = 0.03      36 of 63 within 0.05
```

⚠️ **THE RATE DRIFTS RUN TO RUN** — 4.99%, 5.03%, 5.1%, 5.2% — because the
pooled population includes **today's live board**, which moves with the
odds. 🔴 **A check sitting exactly on its bar is an unstable alarm** (rule
82); that instability is part of what was accepted.

## ⛔ THE BAR WAS NOT MOVED, AND NOTHING WAS RE-DECIDED

- **T37's own pre-registered fallback was already spent** in August —
  `hitter_primary_projection`, which took it 5.43% → 4.9%. It has since
  drifted back. **There is no second fallback.**
- **T55 was VOIDED**, not passed: its primary metric (MAE) is minimised by
  one of its two candidates by construction.
- **T56 PASSED for the mean** on a non-circular metric: sign accuracy
  64.13% against a 60.88% majority-class baseline, **+3.25 points**, both
  predicted classes above 50%. ✅ **The published number carries signal.**
- ➡️ **So no better number is available to publish**, and T37 will keep
  firing until something changes that is not a re-decision of T37.

## 🔴 THE OPEN PROBLEM THIS DOES NOT SOLVE

**Tomorrow's 10am card is refused if the rate is still over the bar**, and
the page freezes on the previous day's card. ⛔ **Accepting does not fix
that**, and there is currently **no legitimate fix available**:

- moving the bar is forbidden;
- swapping T37's population (e.g. excluding 0.5 lines) after seeing it fail
  is population-shopping — `verify_card`'s own comment forbids exactly
  that, *"the same error as moving the bar"*;
- re-writing T37 is forbidden by this register's first rule.

➡️ **THE ONLY CLEAN ROUTE IS A NEW, PRE-REGISTERED TEST** whose question is
*"is a mean the right statistic to publish beside a 0.5 line at all"*, with
its bars and its consequence fixed before it is run — and **its consequence
must be allowed to be "stop printing a projection at 0.5 lines."** T56 was
the first half of that argument; it answered whether the number is
informative (yes) and not whether it belongs beside that particular line.

## ⛔ WHEN TO REMOVE THE ACCEPTANCE

**The line comes out of `card-accepted.txt` the day the underlying problem
is fixed.** A stale entry there is a check that has quietly stopped
mattering — the file's own header says so.

---

# 🆕 🔴 T57 — **DOES THE GAME'S OWN MARKET LINE CARRY WHAT THREE FAILED MODELS LACKED?**
`[pre-registered 2026-09-11, BEFORE any fit. Sam's proposal, his words below.]`

> *"i would like you to factor in spread and team implied total from
> sportsbooks... if a team has a -9.5 spread against the other, with a
> 23.5 point total while the other team has a 13.5 point total, this says
> a lot about the matchup... you will more than likely see more running of
> the football if a team is up by a large margin, resulting in poorer
> output for the receiver."*

## 🔴 WHY THIS IS NOT ANOTHER CUT OF WHAT WE HAVE

⛔ **The football modelling programme was CLOSED on 2026-09-01** with a
stated reopening condition: **charted data we do not own — NOT another cut
of the player log.** T46/T47/T50 exhausted our own inputs: trailing form,
opponent, snap share, pass-snap share, injuries, depth charts.

✅ **THE MARKET LINE WAS NEVER TESTED, AND IT IS NOT OUR DATA.** It is a
third party's forecast of the game, produced by people with information we
do not hold. **That is a different source, not a different slice**, which
is why this reopens rather than re-litigates.

⚠️ **THE BAR IS NOT MOVED FOR IT.** Identical to T46, T47 and T50.

## 📊 THE SAMPLE — MEASURED BEFORE WRITING THIS, NOT ASSUMED

`[measured 2026-09-11 against the stored files]`

```
2025 schedule            285 games
  closing_spread         285  = 100.0%
  closing_total          285  = 100.0%
  closing moneyline      285  = 100.0%
player-game rows (2025)  19,400
  joined to a game line  19,400 = 100.0%
  skill positions, >=50% snaps   3,259
```

✅ **The join is 100%, not "mostly".** ⛔ **If the fit or test row counts
come in more than 5% below these figures, that is REPORTED and the
comparison to T46/T47/T50 is declared not-quite-comparable.**

⚠️ 🔴 **SEASONS — CORRECTED 2026-09-11, BEFORE ANY FIT.**
~~2021–2025, the same range T46/T47/T50 used.~~ ⛔ **THAT WAS WRONG AND I
CHECKED RATHER THAN ASSUMED.** `research/t47_fit.py` is in the repo and
reads **`players-2025.json.gz` ALONE**, `FIT_MAX_WK, TEST_MIN_WK = 13, 14`,
`POS = {"WR","TE","RB"}`. The 2021–2025 range belongs to the OPPONENT
reliability work (T39–T48), not to the three model tests.
✅ **SO T57 RUNS ON 2025, WEEKS ≤13 FIT / ≥14 TEST — WHICH IS BETTER, NOT
WORSE: the sample is now IDENTICAL to T46/T47/T50 rather than merely
similar**, and `research/t47_fit.py` is reused verbatim with three
predictors added and nothing else touched. ⛔ **Corrected before a single
row was fitted; a correction after a result would be specification
shopping.**

## 🔴 THE PREDICTORS — THREE, AND THE THIRD IS SAM'S

1. **`spread`** — signed from the player's OWN team's perspective
   (negative = favoured).
2. **`team_implied`** = `total / 2 − spread / 2`, the player's own team's
   implied points. ⛔ **This formula is fixed here and may not be
   re-derived after seeing a result.**
3. 🔴 **`spread × position` — THE GAME-SCRIPT INTERACTION, IN THE PRIMARY
   SPECIFICATION AT SAM'S EXPLICIT INSTRUCTION** (*"put it in the
   primary"*). ⚠️ **This makes the test HARDER to pass than the main
   effects alone, and that was his call knowingly made** — it is the
   honest form of his hypothesis: a big favourite runs more late, so the
   RB gains and the WR loses.

## ⛔ THE OUTCOME, AND WHY IT IS THE SAME ONE THAT FAILED THREE TIMES

**PRIMARY: receiving yards**, identical in construction to T46/T47/T50 —
same positions, same snap floor, same held-out weeks. ✅ **That is the
whole point: only ONE thing changes, so a pass is attributable to the
market line and nothing else.**

**SECONDARY, pre-registered, NOT primary: RB rushing yards.** Sam's
mechanism should bite hardest here, but it is a different outcome
variable and must not be able to ride on the primary.

## 🔒 THE BAR — ALL FOUR, IDENTICAL TO T46/T47/T50, NOT MOVED

```
Brier  >= +0.0050 over the better naive
MAE    not worse
no subgroup worse
>= 200 test rows
```

⚠️ **The naive is the player's own season-to-date average**, as before.
**T47's specification is the SECOND baseline**, so the report says whether
the market line beat a season average AND whether it beat our best failed
model.

## 🔴🔴 THE TRAP THIS TEST EXISTS TO AVOID, NAMED BEFORE IT RUNS

⛔ **A PROP LINE ALREADY CONTAINS THE GAME TOTAL.** If Miami is implied
for 30 points, the book has already moved every Miami player's line up.
**"Players on big favourites produce more yards" is TRUE, PRICED, and
worth nothing.**

➡️ **So this test predicts PRODUCTION against a season-average naive —
which is a claim about information, not about profit — and a pass earns
NO public confidence number.** See the consequences below.

## ⚠️ AND A SECOND TRAP: A CLOSING LINE IS NOT THE LINE WE WOULD HAVE

🔴 **`closing_spread` and `closing_total` are CLOSING numbers.** They
contain everything known at kickoff — late injury news, weather, sharp
money — **which we would NOT have when the 9:00am card is built.**

⛔ **A pass on closing lines is an UPPER BOUND, not a result.** So, in the
SAME RUN and pre-registered here:

- the primary is fit and tested on the **closing** line, and
- **the identical specification is re-run on the line we actually store
  at card-build time**, and **both are reported side by side**.

⚠️ **If the closing line passes and the card-time line does not, the test
is recorded as FAILED for shipping purposes** and the gap is the finding.
**➡️ We cannot bet a number we do not have when we bet.**

## ⛔ ONE RUN. FORBIDDEN BY NAME.

- swapping closing for opening (or the reverse) **after** seeing a result
- **dropping the interaction** if the main effects pass without it
- re-deriving `team_implied` any other way
- adding ANY player-log input — trailing targets, snap share, injuries,
  depth charts are **SPENT** (T46/T47/T50)
- widening or narrowing the season range
- **running college to look for a pass after the NFL fails** — college is
  the REPLICATION, and it runs only if the NFL passes
- re-cutting by position, weather, home/road or favourite/underdog after
  the fact

## ✅ PRE-COMMITTED CONSEQUENCES

1. ✅ **IF IT PASSES ON BOTH LINES** — football gets its first 🟢 MODEL
   number, ⚠️ **and STILL no public confidence %** until a prospective
   beat-the-market test on real 2026 prop lines. **Beating a season
   average is not beating a book** — that sentence is T50's and it still
   governs. ➡️ **Then, and only then, replicate on college.**
2. ⚠️ **IF IT PASSES ON CLOSING AND FAILS AT CARD TIME** — recorded as a
   FINDING about line timing, not as a model. Nothing ships.
3. 🔴 **IF IT FAILS** — ⛔ **the market-line route is closed too.** Four
   pre-registered specifications will have lost to a player's own season
   average, and the reopening condition returns to **charted data we do
   not own.** ➡️ Football continues to ship ⚪ DESCRIPTIVE and 🔵 MARKET,
   and the page keeps saying so.

⚠️ **WHAT SAM ASKED FOR THAT IS ALREADY ANSWERED, AND IS NOT IN THIS
TEST:** *"use data from the past year to pick up on trends in an offense
or a defence."* **Offensive carryover is REAL (r = 0.541 grouped by
offence); DEFENSIVE carryover is a measured NULL** — six measures, five
constructs, 2021–2025, nothing above 0.31, and `def_epa_per_play` came in
at **0.268, below plain yards allowed** (T39/T41/T42/T43/T48). ⛔ **A
defensive trend term may not enter this specification.**

⚠️ **AND ROUTES / SNAP SHARE ARE SPENT:** T46, T47, and T50 — where
`pass_snap_share` correlated **0.9647** with `snap_pct`. **They are
nearly the same variable and the distinction washes out in an 8-game
average.**

### ⛔ T57 CLOSED — **FAILED, BOTH ARMS. Run once, 2026-09-11.**

✅ **SAMPLE IDENTICAL TO T47's, NOT MERELY SIMILAR:** `2,874 rows · 1,361
fit · 1,513 test`, and **100.0% of T47's rows carried a game line** — the
5%-loss clause never triggered, so the comparison below is exact.

| | Brier | MAE |
|---|---|---|
| **T57 (T47 + spread + implied + game script)** | **0.2555** | **17.20** |
| naive trailing-8 | 0.2566 | 17.23 |
| **naive season-to-date** | **0.2545** | **17.10** |

- 🔴 **PRIMARY FAIL — Brier −0.0010 against +0.0050.**
- 🔴 **SECONDARY FAIL — MAE 17.20 vs 17.10.**
- 🔴 **SUBGROUP FAIL — RB −0.0174** (TE +0.0074, WR +0.0052 were fine).
- ✅ 1,513 test rows, minimum met.

**WHERE IT SITS AMONG THE FOUR:** T46 **+0.0010** · T47 **−0.0041** · T50
**−0.0036** · **T57 −0.0010.** Second-best of four, and still **six
Brier points short of the bar.**

### 🔴 THE ONE REAL FINDING, AND IT IS NOT A MODEL

| term | coefficient | t |
|---|---|---|
| **`own_implied`** | **+0.8355 rec yds per implied point** | **+2.73** |
| `own_spread` | −0.1159 | −0.43 |
| **`spread_x_RB`** | −0.3074 | **−1.08** |
| **`spread_x_WR`** | −0.1761 | **−0.66** |

✅ **THE IMPLIED TOTAL IS REAL: t = +2.73, about +0.84 receiving yards per
implied point.** Sam's intuition that the market line says something about
the matchup is **correct and measurable.**

⛔ **AND IT STILL DOES NOT HELP OUT OF SAMPLE.** In-sample significance
with no held-out gain is the classic pattern: the information is already
inside trailing form, or it is too small to beat a player's own season
average. **A t-statistic is not a prediction.**

🔴 **SAM'S GAME-SCRIPT MECHANISM IS NULL, AND IT WAS TESTED TWICE.**
`spread × RB` t = **−1.08**, `spread × WR` t = **−0.66** — neither
reaches significance, and the interaction was in the PRIMARY at his own
instruction. ⚠️ **The pre-registered SECONDARY tested it head-on — RB
RUSHING yards, where "the favourite runs more late" should bite hardest:**

```
RB rushing yards   MODEL 0.2599 / 21.79   naive 0.2512 / 19.88
Brier −0.0087   MAE worse by 1.91   449 test rows   FAIL
```

**It failed harder than the primary.** ⛔ The mechanism is plausible, was
stated in advance, and does not survive contact with held-out weeks.

### ⚠️ THE LINE-TIMING ARM COULD NOT RUN, AND THAT IS REPORTED NOT SKIPPED

The spec required the identical fit on **the line we would actually hold
at card-build time**, beside the closing line. ⛔ **Only `closing_spread`
and `closing_total` are stored for 2025 — card-time lines were never
archived**, and `raw.githubusercontent.com` is blocked from this
container. ✅ **Moot in this instance — the CLOSING line, which is the
FRIENDLIER of the two, already failed** — but the requirement stands for
any future attempt. ➡️ **To make it answerable later, the collector would
have to archive the line at pull time.**

### ✅ PRE-COMMITTED CONSEQUENCE, APPLIED

🔴 **CONSEQUENCE 3 FIRES: THE MARKET-LINE ROUTE IS CLOSED.** **Four
pre-registered specifications — T46, T47, T50, T57 — have now lost to a
player's own season average**, and the reopening condition returns to what
it was: ⛔ **CHARTED DATA WE DO NOT OWN** (separation, box counts,
personnel, pressure rate). **Not another cut of what we have, and not the
market's own numbers either.**

➡️ **Football continues to ship ⚪ DESCRIPTIVE and 🔵 MARKET, and the page
keeps saying so.** ⛔ **No college replication** — the spec forbids it by
name unless the NFL passes.

⚠️ **WHAT SURVIVED, AND IT IS THE SAME THING THAT SURVIVED THREE TIMES
BEFORE: trailing targets, t = +13.25.** Usage is the signal. It is
already on the page as a descriptive number.


---

# 🆕 T58 — **THE NFL OVER/UNDER ASYMMETRY.** OPEN, PRE-REGISTERED 2026-09-15.

⛔ **THIS WAS FOUND BY LOOKING AT THE DATA. IT IS THEREFORE NOT EVIDENCE — IT IS A HYPOTHESIS.** `[Sam, 2026-09-15, asked where to go next; nobody had read the football record in two days]` **Everything below the observation is fixed BEFORE another row is graded.**

## 📊 THE OBSERVATION (post-hoc, n=100 NFL / 97 CFB, 3 slates each)

```
NFL   over    n=62   stated 70.8%   actual 38.7%   gap -32.1   mean edge +17.3
      under   n=30   stated 56.2%   actual 73.3%   gap +17.1   mean edge  +2.2
      yes     n=8    stated 47.2%   actual 25.0%   gap -22.2

CFB   over    n=33   stated 59.5%   actual 54.5%   gap  -5.0   mean edge  +6.0
      under   n=44   stated 67.2%   actual 54.5%   gap -12.7   mean edge +14.0
      yes     n=20   stated 52.7%   actual 65.0%   gap +12.3
```

**NFL over vs under: z = −3.11, p = 0.0018, a 34.6-point gap.**
✅ **CFB CONTROL: z = 0.00, p = 1.0000 — the two sides are identical to the decimal.**
⚠️ NFL overs against a coin flip ALONE are only z = −1.78, p = 0.075. **The signal is in the SPLIT, not in the over rate.**

## ✅ THE OBVIOUS CONFOUND IS RULED OUT, AND IT RUNS BACKWARDS

**"Unders only get published when the board is very confident"** would explain the gap as selection, not skill. ⛔ **It is the opposite: NFL overs carry the HIGHER stated confidence (70.8 vs 56.2) and the far bigger claimed edge (+17.3 vs +2.2) — and they are the side that loses.** ➡️ **The board is most confident exactly where it is most wrong.**

## 🔬 THE PRE-REGISTRATION — fixed now, before any more data

| | |
|---|---|
| **Predictor** | `side ∈ {over, under}` on NFL player props |
| **Outcome** | win rate, voids and unresolved rows excluded from both denominators |
| **Sample** | **FRESH rows only — published after 2026-09-15.** ⛔ The 100 above may never be reused; they generated the hypothesis. |
| **Minimum** | **n ≥ 120 fresh graded NFL rows spanning ≥ 3 distinct NFL WEEKS.** ⚠️ Not 3 days — the current sample is 3 days inside 2 weeks, which is far less independent than it looks. |
| **PASS** | the over-minus-under gap is **≤ −15 points** AND **p < 0.01** two-sided |
| **FAIL** | gap narrower than 15 points, **or** p ≥ 0.01 |
| **⛔ VOID** | **if CFB develops the same gap beyond ±10 points.** Then the finding is about the GRADING or the PIPELINE, not about NFL, and this test answers the wrong question. |

⛔ **NOTHING CHANGES UNTIL IT PASSES.** No side filter, no confidence reweighting, no suppression of overs, no change to what the board publishes. ⚠️ **Reading a lean off a sample this size is exactly what a pre-registered minimum exists to stop — including when the lean is this large and this clean.**

## 🧭 THE MECHANISM TO TEST IF IT PASSES — named now so it cannot be invented later

### 🔴🔴 AMENDMENT, 2026-09-15 (same day, hours later) — **THE MECHANISM NAMED BELOW IS MEASURABLY FALSE. STRUCK.**

⛔ **THE PRE-REGISTRATION ABOVE IS UNTOUCHED.** Predictor, outcome, sample, minimum, PASS, FAIL and VOID all stand exactly as fixed. **What is struck is a STORY about why, which was flagged as untested when written and has now been measured — and it is wrong.** ✅ Striking a mechanism is not re-deciding a test.

~~🔴 **Football has NO MODEL** (`no_model_note`): the "confidence" is **the player's own historical rate**, and **NFL is two weeks into its season.** ➡️ **A receiver with one good game reads as a near-certain OVER on a one-game denominator**, and `edge = confidence − implied` then reports a huge edge on what is essentially one observation.~~

~~⚠️ **CFB not showing the gap is CONSISTENT with this** — college teams have played more games by week 3, and the CFB board leans UNDER (34% overs vs NFL's 62%).~~

⛔ **THERE IS NO ONE-GAME DENOMINATOR, AND THE SEASON IS NOT 2026.** `[measured 2026-09-15 from the published cards themselves, `picks/fb-nfl-*.json` and `picks/fb-ncaaf-*.json`, not from the code and not from memory]`

```
                    NFL                          CFB
logs_season         2025                         2025
min_games           6                            6
denominator         games at >= 50% of           every game he appears in
                    team snaps                   (union denominator)
snap_floor          0.5                          none
observed `raw`      "8 of 8", "13 of 15"         "11 of 11", "12 of 12", "10 of 12"
```

🔴 **SO THE DENOMINATOR IS 6–15 GAMES, GATED, AND IT IS LAST SEASON'S.** The struck paragraph asserts the opposite on both counts. ⛔ **"NFL is two weeks into its season" is true of the CALENDAR and irrelevant to the CARD** — the card never reads 2026 games at all.

📌 **THE CLASS, AND IT IS THIS PROJECT'S OLDEST ONE.** I described a mechanism from what I knew about the sport instead of reading the artifact the card writes down. **The denominator was printed on every row, in `raw`, the whole time.** ➡️ *A fact about a query is not a fact about the world* — and a fact about the calendar is not a fact about the pipeline.

✅ **WHAT THE HEDGE BOUGHT.** The original entry said in its own words: *"BUT THIS IS A STORY, NOT A RESULT... must not be repeated as though it were established."* **That hedge is the only reason this correction costs a paragraph instead of a feature.** Keep writing them.

### ➡️ THE REPLACEMENT CANDIDATE — **A 2025 RATE AGAINST A 2026 LINE.** NOT ASSERTED.

⚠️ The book prices the 2026 line with 2026 information — new team, new role, new quarterback, an offseason of change. **The confidence is the same player's 2025 rate at that new line.** ⛔ **This is a hypothesis with one measurement behind it (`logs_season: 2025`) and no test. It is written here so it cannot be invented later, and it may not be repeated as established.**

⛔ **AND IT DOES NOT BY ITSELF EXPLAIN THE LEAGUE SPLIT: CFB IS EQUALLY STALE AND DOES NOT SHOW THE GAP.** Anything that claims to explain NFL must also explain why CFB, on the same stale season, reads `z = 0.00`.

### 🔴 WHAT THE FOLLOW-UP ACTUALLY NEEDS, AND WHY IT CANNOT WAIT FOR T58 TO PASS

~~➡️ **If T58 passes, the first follow-up is to add the denominator to the row and test it directly.**~~ **STRUCK — the ORDERING was the error, not the action.**

⛔ **T57 ALREADY TAUGHT THIS AND IT COST AN ENTIRE PRE-REGISTERED ARM.** The line-timing arm could not run because *"card-time lines were never archived."* **Waiting to record a field until a test needs it means the test's own history does not exist when it arrives.**

✅ **SO THE DENOMINATOR IS CARRIED NOW, BEFORE ANY VERDICT.** `record_fb.py` already carries `own_mean` for exactly this reason (T54 was unanswerable without it). **Carrying `n` and `logs_season` alongside it is the same act, for the same reason, and it decides nothing.**

---

# 🆕 T59 — **DOES THE FOOTBALL CONFIDENCE NUMBER CARRY ANY INFORMATION?** OPEN, PRE-REGISTERED 2026-09-15.

⛔ **FOUND BY LOOKING AT THE DATA. IT IS A HYPOTHESIS, NOT EVIDENCE.** Everything below the observation is fixed BEFORE another row is graded.

## 📊 THE OBSERVATION (post-hoc; NFL n=125, CFB n=88 carrying a bucket, from `data/<league>/latest/record.json`)

```
            n-weighted corr(stated, actual) across buckets
NFL                       +0.135
CFB                       +0.146

                  n     stated    actual     gap
NFL  stated <60   46      47.7      41.3     -6.4
     stated >=60  79      75.0      49.4    -25.7
CFB  stated <60   42      40.5      54.8    +14.2
     stated >=60  46      80.8      60.9    -19.9
```

🔴 **THE STATED NUMBER MOVES AND THE OUTCOME DOES NOT.** NFL by slate: stated 52.4 → actual 52.0; stated 68.8 → 44.0; stated 84.4 → 44.0; stated 66.8 → 40.0. **Stated swings 32 points across slates; actual sits between 40 and 52 in all four.**

⚠️ **THE WORST-CALIBRATED BUCKET IS THE MOST CONFIDENT ONE, IN BOTH LEAGUES.** NFL 90-100% stated goes 2 of 5. NFL 80-90% goes 11 of 23 against 84.1 stated (z = −4.76).

✅ **BUT CFB'S HIGH-CONFIDENCE SLATE DELIVERED**: 2026-09-12, stated 87.4, actual 80.0 on n=25. ⛔ **So this is not a grading bug and not a pipeline bug** — which is the same thing the T58 CFB control says, arrived at independently.

## 🔬 THE PRE-REGISTRATION — fixed now, before any more data

| | |
|---|---|
| **Predictor** | stated `confidence`, split at **60** |
| **Outcome** | win rate; voids and unresolved excluded from both denominators |
| **Sample** | **FRESH rows only — published after 2026-09-15.** ⛔ The rows above generated the hypothesis and may never be reused. |
| **Minimum** | **n ≥ 120 fresh graded NFL rows across ≥ 3 distinct NFL WEEKS, with ≥ 40 rows in EACH band.** |
| **MINIMUM EFFECT SIZE** | **≥ 10 points**, declared per the T36 lesson — a bar any coin-flip-sized improvement clears is not a bar. |
| **PASS** | the `>=60` band beats the `<60` band by **≥ 10 points** AND **p < 0.01** two-sided. ➡️ The number carries information. |
| **FAIL** | gap under 10 points, **or** p ≥ 0.01. ➡️ **The number is decoration and the page must stop implying otherwise.** |
| **⛔ VOID** | if either band holds fewer than 40 fresh rows. |

⛔ **NOTHING CHANGES UNTIL IT RESOLVES.** No reweighting, no suppression, no confidence floor, no change to what the board publishes or how rule 55 labels it.

⚠️ **T59 IS NOT T58 AND NEITHER ANSWERS THE OTHER.** T58 asks about SIDE; T59 asks about CONFIDENCE. A row can be in both samples; the tests are independent and must be reported separately.

## 📌 THE T58 CONTROL, RE-READ 2026-09-15 — **AND WHY "UNCHANGED" IS NOT "RE-TESTED"**

```
                 pre-registration (n=100/97)      now (n=125/97)
NFL  over/under        -34.6                          -36.2   z=-3.56  p=0.0004
CFB  over/under          0.0                           +0.0   z=+0.00  p=1.0000
```

⛔ **THE CFB CONTROL DID NOT HOLD — IT DID NOT MOVE, BECAUSE CFB GAINED NO NEW GRADED ROWS.** n is 97 in both columns. **Reading "the control is stable" off an unchanged n is reading a fact about the query as a fact about the world.** ➡️ The VOID condition is untested, not passed.

⚠️ **AND THE NFL COLUMN IS NOT T58 EVIDENCE EITHER** — those 125 rows include the 100 that generated the hypothesis. T58 needs FRESH rows published after 2026-09-15. **Nothing here advances it by a single row.**

---

## 🆕 T-CRON-22 — IS `4 14 * * *` DEAD, OR IS IT STARTING AND DYING?
**Pre-registered 2026-09-16 by the narrowed audit, BEFORE any further data
exists. `update-schedule.md` item 22 carries the measurement.**

### What was measured today, and its limit

```
"4 14 * * *"  (10:04am ET, the MLB card cron)  landed 5 of 7, 09-09 → 09-15
  09-09 ✅  09-10 ✅  09-11 ✅  09-12 ✅  09-13 ✅
  09-14 ❌  09-15 ❌  09-16 ❌ (today)

MLB schedule-snapshot series — a per-pass liveness record:
  09-13  ...1407 1410 1426 1441 1456 1511 1519...   no gap
  09-14  ...1326 1341 1356 ─── 89 min ─── 1525
  09-15  ...1339 1354 1411 ─── 70 min ─── 1521
  09-16  ...1339 1354 1411 ─── 71 min ─── 1522
```

⛔ **The commit log cannot separate two hypotheses**, and the run list —
which can — is **HTTP 403 from a scheduled Claude session (item 21)**.

| | |
|---|---|
| **H1 — THE CRON NEVER FIRES** | GitHub simply drops it, three days running. |
| **H2 — IT FIRES AND DIES BEFORE ITS FIRST COMMIT** | It starts, `cancel-in-progress` on group `collect-mlb` kills the incumbent heartbeat loop, and the new job then fails or produces nothing. |

⚠️ **H2 IS THE ONE THE EVIDENCE LEANS TOWARD AND IT IS NOT PROVEN.** The
incumbent died with ~270 of its 320 `LOOP_MINUTES` unspent, on all three
days, within minutes of when a 14:04 run would land — and **only another
MLB `collect` run can cancel it** (verified: every other workflow uses its
own concurrency group). ⛔ **"Leans toward" is not a finding. Do not write
H2 down as the cause.**

### 📌 THE PRE-REGISTRATION — decided now, before the next day's data

| | |
|---|---|
| **H1 CONFIRMED** | the run list shows **no run** for schedule `4 14 * * *` on a day the snapshot hole is present. |
| **H2 CONFIRMED** | the run list shows a run stamped `collect [cron 4 14 * * *]` that is **cancelled, failed, or completed with no commit**, on a day the hole is present. |
| **⛔ VOID** | if the hole is absent that day — the condition did not occur and **nothing may be concluded from the run list either way.** |
| **⛔ NOT EVIDENCE** | the card being on the page. It was on time all three days — twice from the incumbent's last pass at 14:11, **once built by the watchdog at 14:14**. The product is the thing that cannot answer this. |

➡️ **THE TEST CANNOT BE RUN UNTIL ITEM 21 IS CLOSED.** Option (a) —
`runs.yml` committing `data/latest/runs.json` — makes it answerable for
free and permanently. **Build the instrument first; do not re-derive the
answer from the commit log a fourth time.**

⚠️ **AND THE STANDING CHECK EITHER WAY:** the snapshot hole is measurable
from the clone alone. **`ls data/<date>/schedule/` and look for a gap
wider than ~20 minutes.** A hole that closes on its own is the outage
ending; a hole still present is day N of it. **That much needs no API.**

## 📌 THE METHOD RULE 2026-09-16 EARNED, AND IT VOIDED A PRIOR CONCLUSION

🔴 **A PAID SNAPSHOT'S FILENAME IS A TIME, NOT AN ATTRIBUTION.** The 09-15
audit struck the standing claim *"the dedicated CFB props cron has bought
ZERO props"* by matching the 09-10/11/12 college props purchases to
`34 12 * * *` **on clock proximity alone.** ⛔ **All three were committed
by `collect[ncaaf nfl]` runs; `34 12` routes `LEAGUE=ncaaf` alone and
appears as the `collect[ncaaf]` run that lands at 12:44–12:50 every day
and buys nothing.** ➡️ **The strike is RETRACTED and the claim REINSTATED.**

✅ **THE RULE: trace every paid snapshot to the commit that ADDED it and
read the league label** —
`git log --diff-filter=A --format='%aI %s' -- <snapshot>`. **The label is
the only field that separates two crons firing into the same window.**

---

## 🆕🆕 T60 — DOES THE EIGHT-SIGNAL DOSSIER BEAT THE BOOK'S PRICE?
**Pre-registered 2026-09-17, BEFORE the dossier has produced a single
archived row and BEFORE signal #6 exists in either league.**
`[Sam: "the goal is for the model to grade every game in that 1-8 order
and then choose player props/gamelines based on that data, as well as
depict which player props/gamelines are the bets to bet on"]`

### 🔴 THE TARGET IS THE PRICE, NOT THE YARDS. THIS IS NOT NEGOTIABLE.

⛔ **T46, T47, T50 AND T57 ALL SCORED AGAINST A LINE WE INVENTED** — the
player's own trailing-8 **median** — and not one of them ever faced the
book. `[T46 +0.0010 · T47 −0.0041 · T50 −0.0036 · T57 −0.0010, against a
Brier bar of +0.0050]` ➡️ **T60 scores against the ARCHIVED BOOK LINE at
the archived price or it does not run.** A dossier that predicts yards
well and cannot beat −110 is worth nothing to Sam.

### 📌 THE BAR — FIXED NOW, WHILE NO DATA EXISTS

| | |
|---|---|
| **Break-even at −110** | **52.38%** |
| **PASS** | hit rate **≥ 55.4%** (break-even **+3.0 points**) on **fresh rows only**, one-sided **p < 0.01** |
| **REQUIRED n** | **2,774 graded plays** `[computed, α=0.01 one-sided, power 0.80]` |
| **⛔ NOT MEASURABLE** | under the required n. **Not a pass, not a fail** — the same three-state rule T37 uses. |
| **⛔ VOID** | any row whose line or price was not archived BEFORE first snap. A reconstructed line is not a line. |

⚠️ **THE BAR MAY BE MOVED BY SAM UNTIL THE FIRST ROW IS GRADED. AFTER
THAT IT IS FROZEN.** `[This is the standing rule: never re-decide a test
after seeing the data.]`

### 🔴🔴 THE BLOCKER IS NOT TASK 20. IT IS THE LINE ARCHIVE, AND IT IS MEASURED.

⛔ **Task 20 (CFB possession) unblocks SIGNAL #6. It does not unblock the
backtest, and believing otherwise would waste weeks.** `[measured on
origin/main 2026-09-17]`

```
archived football market snapshots, ENTIRE HISTORY
  NFL  gamelines 31   props-player  8    earliest 2026-09-03
  CFB  gamelines 34   props-player 14    earliest 2026-09-01

graded football plays on record   222   (NFL 125 + CFB 97)
required for a 3-point edge      2774
```

🔴 **EVERYTHING BEFORE 2026-09-01 DOES NOT EXIST FOR US.** We hold roughly
**two weeks** of prices and **222 of the 2,774 rows** the bar needs — **8%.**

### ⚠️ AND TWO OF THE EIGHT SIGNALS CANNOT BE RECONSTRUCTED BACKWARDS AT ALL

| signal | reconstructable point-in-time from a past season? |
|---|---|
| **#2** head to head | ✅ yes — schedule + results history |
| **#3** time of year | ✅ yes |
| **#4** this season | ✅ yes — game logs |
| **#5** versus position | ✅ yes — box scores |
| **#6** possession | ✅ yes — nflverse play-by-play back years; CFBD `/plays` past seasons |
| **#1 market** | 🔴 **NO.** We never stored it. The Odds API sells historical snapshots as a **paid add-on** — a real option, but it is a spend decision, and the Odds quota is already at **71%**. |
| **#7 personnel** | 🔴 **NO.** Who was out before a game played last year is not in anything we store. ⛔ Reconstructing it from today's rosters is **LOOKAHEAD** — the exact defect that struck T22's season-long-role cut. |
| **#8 venue/weather** | 🟡 venue yes; **weather no** — CFBD `/games/weather` is **401, paid tier**. |

➡️ **SO A DEEP HISTORICAL BACKTEST OF ALL EIGHT IS NOT AVAILABLE AT ANY
EFFORT.** A backtest of **#2–#6 only**, scored against outcomes rather
than prices, IS available over many past seasons — ⛔ **but it answers the
question that already failed four times** (does the number predict the
stat), not Sam's question (does it beat the price).

### ✅ THEREFORE: T60 IS A FORWARD TEST, AND THE CLOCK IS THE BINDING CONSTRAINT

🔴 **EVERY DAY THE DOSSIER IS NOT ARCHIVING ITS OUTPUT IS A DAY OF ROWS
THAT CAN NEVER BE RECOVERED.** ➡️ **THE HIGHEST-VALUE ACTION AVAILABLE ON
THIS WORKSTREAM IS NOT MODELLING — IT IS TURNING ON THE ARCHIVE.**

⛔ **`dossier_fb.py` WRITES TO `data/<league>/latest/dossiers.json.gz`,
WHICH IS OVERWRITTEN EVERY RUN.** ✅ **It must also write a DATED copy**,
exactly as `picks/fb-<league>-<date>.json` already does, or T60 has no
observations even after the signals all work.

📌 **PROJECTED, at the current ~157 graded plays/week:**

| edge sought | n needed | weeks |
|---|---|---|
| 2 points | 6,249 | ~40 |
| **3 points (the bar)** | **2,774** | **~18** |
| 4 points | 1,559 | ~10 |
| 5 points | 996 | ~6 |

⚠️ **~18 weeks from a start date that has not happened yet.** ⛔ The
projection assumes the current rate holds; **CFB's season ends first and
the rate will fall.** Do not quote the date as a promise.

### 📌 THE ORDER, AND STEP 0 IS THE ONE PEOPLE SKIP


---

## 🆕🆕 T61 — DOES SIGNAL #6 SURVIVE, OR IS IT RETIRED? **PRE-REGISTERED 2026-09-19, BEFORE THE COUNTERS LAND.**

🔴 **SAM, 2026-09-19:** *"lets finish the prs, if those dont fix number 6 lets just drop it form the rules."*

⛔ **THIS ENTRY EXISTS SO THAT DECISION IS MADE BY A READING AND NOT BY A
MOOD.** The counters land in `top-probe-<season>.json` on the next
already-paid CFBD run. **The rule below is written before they arrive and
is not to be re-decided after seeing them** — that is this register's whole
purpose.

### 🔴 FIRST: #6 IS TWO DIFFERENT PROBLEMS AND THEY MUST BE DECIDED SEPARATELY

⛔ **"Drop #6" on a CFB reading would retire a signal whose NFL half has
never been tried.** They share a section number and nothing else:

| | source | shape | state |
|---|---|---|---|
| **CFB §6** | CFBD `/plays` clock | **DERIVED** by arithmetic | refuses — 36.282% ordering anomaly against a 2.0 bar |
| **NFL §6** | nflverse `drive_time_of_possession` | **READ** off a field | **never run.** No `top-*` artifact has ever existed |

✅ **AND THE NFL SOURCE IS THE BEST-VALIDATED INPUT IN THE PROJECT:** 269
of 269 regulation games summed to **exactly 3600s** — an identity, not a
tolerance — and the per-team cross-check passed at **r = +0.98979, max
|diff| 35.0s**. ⛔ **Nothing about CFBD's play ordering says anything about
a field nflverse records directly.**

➡️ **SO: TWO VERDICTS, TWO SPECIFICATIONS.**

---

### T61a — CFB §6. **Decided by the counters, from ONE reading.**

**Specification:** the first `data/ncaaf/latest/top-probe-2026.json` written
by a CFBD run carrying PR #84's counters.

| reading | verdict |
|---|---|
| `negative_games_share` ≥ 0.5 **AND** `dn_pn_anomaly_pct` ≤ 2.0 | ✅ **SHIP THE SORT.** H1 confirmed; `(driveNumber, playNumber)` is the fix and CFB §6 lives. |
| `negative_games_share` ≥ 0.5 **AND** `dn_pn_anomaly_pct` > 2.0 | 🔴 **RETIRE.** The ordering is broken and the remedy does not fix it. |
| `negative_games_share` < 0.5 | 🔴 **RETIRE.** H1 is wrong — the 36% is outlier-driven, and the diagnosis that justified further work does not hold. |
| no counters present after **two** CFBD runs | ⚠️ **ONE** wiring fix, then re-read. Still absent → 🔴 **RETIRE.** |

⚠️ **THE BARS ARE NOT INVENTED.** `2.0` is `CFB_ANOMALY_MAX_PCT`, already
deployed. `0.5` separates a feed-wide shape from a handful of games and was
measured against a known-good feed, which reads **0.0327** — ⛔ **and an
earlier version of this counter would have read 0.498 on that same good
feed, sitting on its own bar. That is why the counter was split.**

✅ **THE REMEDY FIGURE IS PROVEN TO MEASURE WHAT IT CLAIMS:** driven on the
2019 fixture, `dn_pn_anomaly_pct` recovers **0.506** from a deliberately
H1-broken feed — **exactly the true rate** — against **33.134** under the
current sort.

---

### T61b — NFL §6. **Decided by ONE run, and it is not blocked on CFBD.**

**Specification:** one `nfl-logs` run that reaches `build_possession`.

| reading | verdict |
|---|---|
| a `top-2026.json.gz` is written and layer 1 holds (regulation games sum to exactly 3600) | ✅ **NFL §6 LIVES.** |
| the build runs and **refuses** on its own guard | 🔴 **RETIRE NFL §6**, and record the refusal reason — that is a fact about the season's data, not about the design. |
| the build cannot be made to run at all | ⚠️ **ONE** fix to the arm, then re-read. Still nothing → 🔴 **RETIRE.** |

⛔ **DO NOT RETIRE NFL §6 ON A CFB READING.** Different source, different
shape, different failure.

---

### ⛔ WHAT "RETIRE" MEANS — DEFINED NOW, SO IT CANNOT DRIFT

✅ **RETIRE THE SECTION. KEEP THE MACHINERY.**

1. **`dossier_fb.py` stops emitting §6** for the retired league. The dossier
   states **seven** sections and says on the page that possession was
   retired and why. ⛔ **Do not silently renumber** — a reader who saw eight
   is owed the sentence.
2. **The freshness row goes with it** (PR #76's `"possession"` entry, that
   league only). ⛔ A contract row for a section nobody publishes is the
   `t54.json` shape again.
3. ⛔ **DO NOT DELETE `possession.py`, `nfl.py`'s builder, `cfb.py`'s
   derivation, or `claude/possession-validation.md`.** Measured blast
   radius: **6 production files, 73 mentions, 8 test files.** They cost
   nothing dormant, the NFL half is validated to an identity, and **if CFBD
   fixes its feed this is a one-line revival instead of a rebuild.**
4. **`claude/possession-validation.md` gets the verdict and the reading that
   produced it**, struck rather than deleted.

⚠️ **AND THE HONEST FRAMING FOR THE PAGE:** *a signal we could not compute
to a standard we would stand behind was removed rather than published
weakly.* ⛔ **That is the product's existing voice — the §6 refusal text
already says exactly this — and it is a better story than a section that
reads UNAVAILABLE on 119 games.**

---


---

## ✅ T61 — RESULT, LOGGED 2026-09-19 08:10Z. **BOTH HALVES RAN.**

⛔ **The register's standing rule: log the result whichever way it falls.**

### ✅ T61b — NFL §6: **PASSED. NOT RETIRED.**

`[run by the Cowork session on REAL 2026 nflverse play-by-play, fetched
free and without a key — not a fixture, not a simulation]`

```
regulation games exact 3600     16 of 16      <- the identity, exactly
teams with a row                32 of 32
coverage min / median           1.0 / 1.0
league mean share               0.5010        (0.5 is the identity)
overtime games                  1, correctly over 3600
unparsed                        0
usable                          True
```

📌 **NFL §6 HAS NEVER BEEN BROKEN. IT HAS NEVER BEEN RUN.** ➡️ **The
remaining NFL work is to schedule the build, not to fix it.** The freshness
row PR #76 added already reports it: `nfl-logs … MISSING`.

⚠️ **One miscount on the way, caught before reporting:** the returned table
was read as "9 team rows" — those are 9 metadata keys; the `teams` dict
holds all 32.

### ⚠️ T61a — CFB §6: **THE RULE SAYS SHIP. THE ARTIFACT SAYS INCONCLUSIVE. THE RULE WAS MIS-SPECIFIED.**

`[data/ncaaf/latest/top-probe-2026.json, written 2026-09-19T07:53:52Z,
 339 games, 58,106 pairs]`

```
negative_games_share        1.0        ✅ >= 0.5
dn_pn_anomaly_pct           1.585      ✅ <= 2.0      -> T61a row 1 = SHIP

pn_monotonic_game_pct       0.0
pn_monotonic_drive_pct      22.9       <- H1 predicts this near 100
dn_pn_monotonic_game_pct    68.73      <- remedy fixes 2 games in 3, not all
dn_pn_buckets_skipped_no_drivenumber  0
artifact's own verdict      INCONCLUSIVE
```

🔴 **BOTH READINGS ARE CORRECT AND THE FAULT IS IN MY SPECIFICATION.** I
wrote T61a's two conditions as a **proxy for "H1 confirmed"**, assuming a
feed-wide anomaly plus a remedy under the bar could only mean `playNumber`
restarts per drive. ⛔ **It does not.** H1 predicts monotonicity **within a
drive**; the live feed reads **22.9%**. The ordering is broken in some way
that is **not H1**, and `(driveNumber, playNumber)` pulls the anomaly under
the bar **without restoring the ordering.**

📌 **THE LESSON, AND IT IS ABOUT PRE-REGISTRATION ITSELF: A MECHANISM CLAIM
MUST NOT BE SMUGGLED INTO A THRESHOLD PAIR.** ➡️ **If the verdict depends on
*why*, then a counter measuring *why* belongs in the rule — not two
counters that would usually coincide with it.**

### 🔴 AND THE DECIDING NUMBER WAS NEVER MEASURED

The derivation has **two** bars. Only one was tested under the remedy:

```
anomaly     1.585 under the remedy        ✅ would pass CFB_ANOMALY_MAX_PCT
coverage    median still 4.06             ⛔ >1.0 is impossible
            dn_pn coverage fields          NONE — not measured
```

⛔ **Shipping the sort on the anomaly bar alone could produce a table that
passes and is still garbage.**

### ➡️ T61a IS NOT CLOSED. IT IS EXTENDED, ONCE, AT ZERO COST.

**T61a-ii, pre-registered 2026-09-19 before the counter exists:** add
`dn_pn_coverage_median` — the same one-line shape as the five counters
already shipped, zero API calls, written by the next CFBD run.

| reading | verdict |
|---|---|
| `dn_pn_coverage_median` ≤ 1.0 **and** `dn_pn_anomaly_pct` ≤ 2.0 | ✅ **SHIP THE SORT — CFB §6 LIVES** |
| `dn_pn_coverage_median` > 1.0 | 🔴 **RETIRE CFB §6.** The remedy fixes the anomaly and not the quantity, which means we do not understand the feed. |

⛔ **ONE extension only. If T61a-ii is also ambiguous, CFB §6 RETIRES** —
per §"what RETIRE means" above, keeping the machinery. ⚠️ **A test extended
twice is a test being shopped, and that is the failure this whole register
exists to prevent.**


### 📌 WHAT THIS DECISION DOES **NOT** TURN ON

⛔ **Retiring #6 does not change a single published pick**, and nobody
should expect it to. `card_fb.py` reads four files — `gamelines`,
`players-*`, `props`, `record` — and **has never read `dossiers.json.gz`.**
The dossier describes; the card ranks on a player's own hit rate. ➡️ **Seven
signals or eight, the card ranks identically.**

✅ **The signal that matters for the PRODUCT is T60** — does the dossier
combination beat the book — **and T60 is a separate question that a retired
#6 makes cheaper to answer, not harder**, because a signal that reads
UNAVAILABLE on 119 of 119 games contributes nothing to it either way.


---

0. ⬜ **ARCHIVE THE DOSSIER TO A DATED PATH.** Cheap, and it is the only
   step that loses value every single day it waits.
1. ⬜ Task 19 (`claude/reachable-accumulators`) reviewed and merged.
2. ⬜ Task 20 — CFB possession. Signal #6 leaves `UNAVAILABLE`.
3. ⬜ `claude/possession-validation.md` layers 1 and 2 pass for **both** leagues.
4. ⬜ Only now does T60 start counting. **Rows graded before step 3 are VOID** — a signal that was wrong when the row was written is not evidence about the signal.
