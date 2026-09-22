# Calibration accumulators — rule 15 and rule 35

**Created Aug 21 2026, 7:30am run.** These two tables grow on **every** grading run. They are **diagnostics, not the record** — `claude/pick-ledger.md` holds the record and is authoritative on every W/L.

🔴 **Why they live here and not in the ledger:** both are accumulators that get one block longer per slate. The ledger is already the longest doc in the project and its job is to be readable. **Prune the ledger, grow this.**

## ⛔ 🔴 RECOUNT EVERY BUCKET FROM THE ITEMISED ROWS. NEVER CITE A PRINTED `n`.

**The project's most-repeated defect is a count stated beside a table that does not reconcile against the table.** It has now happened inside this doc. ➡️ **Before quoting ANY count in this doc — a W/L tally, a `rungs` cell, a `starts` cell, a `predicted`, an `actual` — re-derive it from the itemised rows underneath it.** A tally is not evidence; the rows are.

⚠️ **Two rules for re-deriving the bucket tables, both learned the hard way on 8/21:**

1. **The rung percentages are PRINTED AS INTEGERS but were BUCKETED UNROUNDED.** A rung printed `40` may be 39.85 or 40.33. **Bucketing on the printed integer will disagree with the table and the table will be right.** Recover the unrounded value first — for the pure-model column, `P(K > rung)` under `Poisson(E[K])` reproduces **82 of 83** printed rungs exactly.
2. **Buckets are half-open `[lo, hi)`.** Resolve every rung that prints exactly on an edge (20, 40, 60, 70, 80, 90) before counting it.

✅ **BOTH BUCKET TABLES BELOW WERE FULLY RE-DERIVED ON 8/21 AND RECONCILE, 83/83 RUNGS, ON ALL 14 ROWS.** ⛔ **They were audited under suspicion of a miscount and they are CORRECT. Do not "fix" them.** See the audit notes filed beneath each table.

---

# 🔴 RULE 15 SCOREBOARD — model vs raw, which was closer

**What the monthly re-fit needs from this: a number to replace the hand-set 50/50 blend weight.**

## 🔴 THE CARD DOES NOT LOG THE INPUTS RULE 15 NEEDS

`[measured 8/21]` **Rule 15 says "every play logs both a model number and a raw hit rate." The 8/20 card logged NEITHER — it logged only the blend.** So did the 8/19 card. **Rule 15 has never been executable from the ledger as written.**

➡️ ✅ **The 8/20 numbers below were RECONSTRUCTED from first principles** — trailing-8 K from the statsapi game log, opponent meanK from `claude/mlb-opponent-database.md`, home/road from `schedule?hydrate=probablePitcher`, then the v4.0 formula and Poisson.

✅ **The reconstruction validates.** Recomputed `0.5×model + 0.5×raw` reproduces the **published blend** to **≤0.2 points on 9 of the 11 strikeout plays** and **1.2 points on the one outs play**. Two exceptions are flagged below.

➡️ 🔴 **FIX, AND IT IS A ONE-COLUMN FIX: the card template must carry `model` and `raw` as their own columns, beside the blend.** Reconstruction worked here because the whole slate was rebuildable from free endpoints. **It will not always be, and a reconstruction is not a log.**

## 8/20 — 12 graded plays

| Play | Line | model | raw | blend | pub. blend | W/L | **closer** |
|---|---|---|---|---|---|---|---|
| Peter Lambert | o3.5 K | 87.8% | 81.0% | 84.4% | 86.1% ⚠️ | L | **raw** |
| Randy Dobnak | o2.5 K | 79.8% | 83.3% | 81.6% | 81.6% ✅ | W | **raw** |
| Anthony Kay | o2.5 K | 81.6% | 78.3% | 79.9% | 79.9% ✅ | W | **model** |
| Gerrit Cole | o4.5 K | 78.5% | 80.0% | 79.3% | 79.2% ✅ | W | **raw** |
| Andrew Alvarez | o2.5 K | 77.7% | 80.0% | 78.8% | 78.9% ✅ | W | **raw** |
| Gage Jump | o3.5 K | 75.0% | 80.0% | 77.5% | 77.6% ✅ | L | **model** |
| Grant Holmes | o2.5 K | 75.5% | 78.3% | 76.9% | 76.9% ✅ | W | **raw** |
| Kyle Bradish | u6.0 K | 77.6% | 72.7% | 75.2% | 76.4% ⚠️ | W | **model** |
| Robert Gasser | o3.5 K | 72.8% | 78.6% | 75.7% | 75.7% ✅ | W | **raw** |
| Jacob deGrom | o4.5 K | 68.8% | 73.9% | 71.4% | 71.2% ✅ | W | **raw** |
| *G. Williams* | o5.5 K | 78.0% | 76.0% | 77.0% | 76.8% ✅ | W | **model** |
| *G. Rodriguez* | u15.5 outs | 61.5% | 69.2% | 65.4% | 66.6% ⚠️ | L | **model** |

*(italic rows are conversational / TABLE C — they do NOT enter the carded record)*

### Running scoreboard

| Scope | model closer | raw closer |
|---|---|---|
| **TABLE A only (carded)** | **3/10** | **7/10** |
| All 12 graded plays | 5/12 | 7/12 |

## ⚠️ 🔴 THE "CLOSER" TALLY IS A BIASED STATISTIC. DO NOT FIT A WEIGHT TO IT.

`[measured 8/21]` **On a slate that goes ~~10/12~~ 🔴 9/12, "closer to the outcome" mechanically rewards whichever estimate was HIGHER**, because for a win the target is 1.0. The raw rate happened to be the higher number on ~~7~~ 🔴 **8** of 12 plays. **The tally is measuring the day's win rate, not the estimator.**

🔴 **`[corrected 8/21]` BOTH COUNTS IN THE SENTENCE ABOVE WERE WRONG AGAINST THE TABLE DIRECTLY ABOVE THEM.** The W/L column reads **L,W,W,W,W,L,W,W,W,W,W,L — 9 W and 3 L, so 9/12**, not 10/12. And `raw > model` on **8** of the 12 rows (Dobnak, Cole, Alvarez, Jump, Holmes, Gasser, deGrom, G. Rodriguez), not 7 — the 7 belongs to the **closer** column, which is a different question and is correct at 7/12. ⚠️ **The 8/10 carded figure quoted later in this doc is right** (TABLE A only: 8 W, 2 L). ✅ **The argument survives both corrections unchanged, and is in fact slightly stronger: the higher estimate was raw on 8 of 12, and raw took the "closer" column on 7.**

✅ **THE CORRECT ACCUMULATOR IS A PROPER SCORING RULE.** Brier score over the blend weight `w`, on the same 12 plays:

| w (model) | 0.0 | 0.2 | 0.4 | **0.5** | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|---|
| Brier | .1852 | .1847 | .1843 | **.1842** | .1841 | .1841 | .1842 |

🔴 **THE SURFACE IS FLAT TO FOUR DECIMAL PLACES. At n=12 the blend weight is UNIDENTIFIABLE.** The argmin lands at 0.7 and it is noise — the whole range from 0 to 1 spans **0.0011 of Brier.**

➡️ **This is the useful finding, and it is a negative one: one slate cannot fit this parameter and neither can ten.** ⛔ **Do not touch the 50/50.** **Keep accumulating Brier per play; revisit when the carded n is in the hundreds, not the dozens.**

## ⚠️ Two reconstruction residuals, unexplained

| Play | reconstructed | published | gap |
|---|---|---|---|
| **Lambert o3.5 K** | 84.4% | **86.1%** | **−1.7** |
| **Bradish u6.0 K** | 75.2% | **76.4%** | **−1.2** |

**Nine of eleven land inside ±0.2, so the method is right and these two have a specific cause that was not found.** Candidates: a different raw-rate window, or a trailing-8 that included a relief appearance. ⛔ **Not chased, not patched, and the published numbers were left alone** — the ledger's blend is what was bet and it stays the record.

## 🆕 8/21 — 8 carded plays. 🔴 **THE FIRST SLATE WHERE RULE 15 IS A READ, NOT A RECONSTRUCTION.**

✅ **Ledger rule 41 / pre-publish check 26 landed: the 8/21 card logged `model` and `raw` as their own columns.** **Every number in the table below was copied off `claude/pick-ledger.md` TABLE A. Nothing was rebuilt from the formula.** ⛔ **That is the whole difference from the 8/20 block above, and it is why this block carries no "reconstruction residuals" section.**

✅ 🔴 **INDEPENDENTLY AUDITED THE SAME MORNING, AND THE AUDIT IS THE POINT.** `[measured 2026-08-22]` **Every pitcher's full statsapi game log was re-pulled and each raw denominator recomputed from PRIOR STARTS ONLY. All 8 reproduce the card exactly — 24/26, 11/12, 17/21, 20/26, 20/25, 20/23, 17/22, 19/22.** **And `0.5×model + 0.5×raw` reproduces every published blend to ≤0.05 points, 8 of 8.** ⛔ **The card's raw column is not taken on trust; it is now measured.**

| Play | Line | model | raw | blend | pub. blend | W/L | **closer** |
|---|---|---|---|---|---|---|---|
| Cam Schlittler | o4.5 K | 83.4% | 92.3% (24/26) | 87.85% | 87.8% ✅ | L | **model** |
| Sean Manaea | o3.5 K | 82.2% | 91.7% (11/12) | 86.95% | 86.9% ✅ | W | **raw** |
| Sean Burke | o3.5 K | 89.9% | 81.0% (17/21) | 85.45% | 85.4% ✅ | W | **model** |
| MacKenzie Gore | o4.5 K | 76.9% | 76.9% (20/26) | 76.90% | 76.9% ✅ | W | **tie** |
| Reid Detmers | o4.5 K | 72.0% | 80.0% (20/25) | 76.00% | 76.0% ✅ | W | **raw** |
| Jacob Misiorowski | o6.5 K | 64.7% | 87.0% (20/23) | 75.85% | 75.9% ✅ | L | **model** |
| Chris Sale | u18.5 outs | 66.7% | 77.3% (17/22) | 72.00% | 72.0% ✅ | W | **raw** |
| Yoshinobu Yamamoto | o17.5 outs | 54.0% | 86.4% (19/22) | 70.20% | 70.2% ✅ | W | **raw** |

**8 rows. W/L: 6 W + 2 L = 8 ✅** (counted against the rows, not against another number — ledger rule 45).

### Running scoreboard — 🔴 **CARDED PLAYS ONLY**

| Scope | model closer | raw closer | tie |
|---|---|---|---|
| 8/20 carded | 3/10 | 7/10 | 0 |
| **8/21 carded** | **3/8** | **4/8** | **1/8** |
| **Both slates, carded** | **6/18** | **11/18** | **1/18** |

⚠️ 🔴 **THE "CLOSER" COLUMN IS STILL THE BIASED STATISTIC THE SECTION ABOVE CONDEMNS, AND IT IS PRINTED ONLY FOR CONTINUITY.** **8/21 went 6/8, so "closer" again mostly rewards whichever estimate was higher.** ⛔ **Do not fit anything to it.** **The Brier table below is the accumulator that counts.**

⚠️ **AND ON THIS SLATE IT POINTS THE OTHER WAY FROM 8/20, WHICH IS ITSELF THE WARNING:** model took the column on **both losses** (Schlittler, Misiorowski) because it was the lower number, and raw took it on three of six wins because it was the higher one. **Two slates, opposite tilts, same mechanism. It is measuring the day.**

## 🆕 8/22 — 13 carded plays. 🔴 **THE WORST CARD IN THE PROJECT'S HISTORY, AND THE SCOREBOARD IS A READ.**

✅ **Every `model` and `raw` figure below was copied off `claude/pick-ledger.md` 8/22 TABLE A. Nothing was rebuilt from the formula.**

✅ 🔴 **AND EVERY RAW DENOMINATOR WAS RE-DERIVED FROM PRIOR STARTS ONLY AND ALL 13 REPRODUCE THE CARD EXACTLY** `[measured 2026-08-23]` — 14/14, 22/24, 16/18, 12/14, 20/23, 13/19, 15/19, 13/19, 12/15, 8/13, 16/20, 8/13, 11/23 — **and `0.5×model + 0.5×raw` reproduces every published blend to ≤0.06 points, 13 of 13.** ⛔ **The card's raw column is measured, not trusted.**

| Play | Line | model | raw | blend | pub. blend | W/L | **closer** |
|---|---|---|---|---|---|---|---|
| Jared Jones | o2.5 K | 89.9% | 100% (14/14) | 94.95% | 94.9% ✅ | W | **raw** |
| Ryan Weathers | o3.5 K | 74.3% | 91.7% (22/24) | 83.00% | 83.0% ✅ | L | **model** |
| Christian Scott | o4.5 K | 71.0% | 88.9% (16/18) | 79.94% | 80.0% ✅ | W | **raw** |
| Jared Jones | o3.5 K | 77.5% | 85.7% (12/14) | 81.60% | 81.6% ✅ | W | **raw** |
| Dylan Cease | o6.5 K | 68.3% | 87.0% (20/23) | 77.65% | 77.6% ✅ | W | **raw** |
| Tarik Skubal | u18.5 outs | 64.4% | 68.4% (13/19) | 66.40% | 66.4% ✅ | L | **model** |
| Rhett Lowder | o2.5 K | 78.9% | 78.9% (15/19) | 78.90% | 78.9% ✅ | L | **model** |
| Tarik Skubal | u8.5 K | 70.9% | 68.4% (13/19) | 69.65% | 69.7% ✅ | L | **raw** |
| Jake Irvin | u15.5 outs | 61.8% | 80.0% (12/15) | 70.90% | 70.9% ✅ | L | **model** |
| Hunter Brown | u17.5 outs | 62.8% | 61.5% (8/13) | 62.15% | 62.2% ✅ | W | **model** |
| Martín Pérez | o14.5 outs | 54.7% | 80.0% (16/20) | 67.35% | 67.3% ✅ | L | **model** |
| Hunter Brown | u5.5 K | 56.9% | 61.5% (8/13) | 59.20% | 59.2% ✅ | W | **raw** |
| Dylan Cease | u17.5 outs | 46.9% | 47.8% (11/23) | 47.35% | 47.4% ✅ | L | **model** |

**13 rows. W/L: 6 W + 7 L = 13 ✅** (counted against the rows, not against another number — ledger rule 45).

### Running scoreboard — 🔴 **CARDED PLAYS ONLY**

| Scope | model closer | raw closer | tie |
|---|---|---|---|
| 8/20 carded | 3/10 | 7/10 | 0 |
| 8/21 carded | 3/8 | 4/8 | 1/8 |
| **8/22 carded** | **7/13** | **6/13** | **0/13** |
| **All three slates, carded** | **13/31** | **17/31** | **1/31** |

⚠️ 🔴 **AND 8/22 IS THE CLEANEST DEMONSTRATION YET THAT THIS COLUMN IS THE BIASED STATISTIC THIS DOC CONDEMNS.** **The card went 6/13, so for the first time the slate's win rate is BELOW half — and for the first time `model` takes the column, 7 to 6, purely because it was the LOWER number on a losing night.** ⛔ **8/20 (9/12) favoured raw, 8/21 (6/8) favoured raw, 8/22 (6/13) favours model. Three slates, and the column has tracked the day's win rate every single time.** ➡️ **It is measuring the day. The Brier accumulator below is the one that counts.**

## 🔴 T15 BRIER ACCUMULATOR — RESTATED ON CARDED PLAYS ONLY, EXACTLY AS PRE-REGISTERED

🔴 **`claude/owed-tests.md` T15 pre-registered this restatement BEFORE today, in its own words: *"At the next grading run, RE-STATE the accumulator on the 10 carded plays of 8/20 and report the count as `10 / 100`, saying that two conversational plays were removed."*** ✅ **Done here, and the two removed plays are named: G. Williams o5.5 K and G. Rodriguez u15.5 outs.**

⛔ **T5 closing on 2026-08-22 does NOT widen this denominator.** **T5 admitted conversational picks to the CALIBRATION table; T15's specification says CARDED PLAYS and still says carded plays.** **Widening it now would need its own pre-registration.**

**Brier over the blend weight `w`, on 18 CARDED plays (10 from 8/20 + 8 from 8/21):**

| w (model) | 0.0 | 0.2 | 0.4 | **0.5** | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|---|
| Brier | .1945 | .1914 | .1893 | **.1886** | .1881 | .1879 | .1887 |

| | |
|---|---|
| **argmin** | **w = 0.74, Brier .1879** |
| **Brier at the shipped w = 0.5** | **.1886** |
| **Margin, argmin vs 0.5** | **0.0007** |
| **T15's bar** | **margin ≥ 0.005 AND n ≥ 100 carded plays** |

🔴 **FAILS BOTH LEGS, AND NOT NARROWLY: the margin is one seventh of the bar and n is 18 against 100.** ⛔ **The 50/50 is not touched.** ⚠️ **The surface is no longer flat to four decimals — it spans 0.0059 from w=0 to w=1, against 0.0011 at n=12 — so it is beginning to have a shape.** ⛔ **A shape is not an identification. The argmin has moved 0.7 → 0.74 on six added plays, which is exactly how much a 6-play sample can move it.**

⚠️ 🔴 **`[noted 2026-08-24]` ARITHMETIC NOTE, AND IT APPLIES TO EVERY SPAN, SPREAD AND MARGIN ON THIS PAGE: they are computed on the UNROUNDED Brier values and will therefore differ in the LAST DIGIT from the 4-dp tables printed above them — the `0.0059` span here against a printed `.1945 − .1887 = .0058`, and the `0.0094` margin in the 31-play block below against a printed `.2338 − .2245 = .0093`.** ⛔ **This is display rounding, not a discrepancy: no Brier figure on this page is altered and none may be recomputed from the printed 4-dp cells** (the same trap as this doc's own header rule 1 on printed rung integers).

⚠️ 🔴 **A PROVENANCE CAVEAT THAT MUST TRAVEL WITH THIS NUMBER: the 8/20 half of the accumulator uses RECONSTRUCTED model and raw values; only the 8/21 half is LOGGED.** **The two reconstruction residuals flagged above (Lambert −1.7, Bradish −1.2) sit inside these 18 plays.** ➡️ **From 8/21 forward every slate is a log, so the reconstructed fraction shrinks every run — but it is not zero and the doc says so.**

## 🆕 🔴 T15 BRIER — RESTATED 2026-08-23 ON 31 CARDED PLAYS. **THE MARGIN LEG CLEARS FOR THE FIRST TIME. THE `n` LEG DOES NOT. THE 50/50 IS NOT TOUCHED.**

**Brier over the blend weight `w`, on 31 CARDED plays (10 from 8/20 + 8 from 8/21 + 13 from 8/22):**

| w (model) | 0.0 | 0.2 | 0.4 | **0.5** | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|---|
| Brier | .2502 | .2428 | .2366 | **.2338** | .2314 | .2274 | **.2245** |

| | |
|---|---|
| **argmin** | 🔴 **w = 1.00 (PURE MODEL), Brier .2245** |
| **Brier at the shipped w = 0.5** | **.2338** |
| **Margin, argmin vs 0.5** | 🔴 **0.0094** |
| **T15's bar** | **margin ≥ 0.005 AND n ≥ 100 carded plays** |
| **Verdict** | ⛔ **FAILS — n = 31 against 100.** ⚠️ **But the MARGIN leg is now cleared, for the first time.** |

🔴 **THE ARGMIN HAS MOVED 0.7 → 0.74 → 1.00 ON THREE SLATES, AND IT LANDED ON A BOUNDARY.** ⛔ **An argmin at the edge of the parameter space is a warning, not a finding: it means the data are pulling as hard as they can in one direction and the optimiser has nowhere further to go.** ⚠️ **The spread from w=0 to w=1 is now .0257, against .0059 at n=18 and .0011 at n=12 — the surface has real shape now.**

⚠️ 🔴 **SAY WHY IT MOVED, BECAUSE THE MECHANISM MATTERS MORE THAN THE NUMBER: on 8/22 the raw rate was the MORE OPTIMISTIC of the two estimates on 10 of the 13 plays, and the card went 6/13. Pure model wins this Brier because it was lower on a losing night, not because it is better calibrated.** ⛔ **That is the same day-tracking artifact the "closer" column above is condemned for — it is simply harder to see in a proper scoring rule.** ➡️ **This is exactly why T15 has TWO legs and why `n ≥ 100` is the binding one.**

⛔ **DO NOT TOUCH THE 50/50. DO NOT ADOPT A FITTED `w`.** **Adoption needs both legs, and it needs a September re-fit decision — not a grading run that has just watched one bad slate move the argmin to a boundary.**

⚠️ 🔴 **PROVENANCE CAVEAT, CARRIED FORWARD: the 8/20 third of this accumulator uses RECONSTRUCTED model and raw values (including the two flagged residuals, Lambert −1.7 and Bradish −1.2). The 8/21 and 8/22 thirds are LOGGED.** ➡️ **The reconstructed fraction is now 10 of 31 and shrinks every run.**

**Progress: 31 carded plays / 100.**

---

# 🔴 RULE 35 SHADOW LADDER — every rung, not just the carded one

## ⛔ COUNT STARTS. NEVER QUOTE A RUNG COUNT AS SAMPLE SIZE.

**Rungs inside one start are perfectly correlated** — deGrom's 10 K wins every rung up to 8.5 simultaneously. **Shadow grading buys SPREAD, not sample size.**

## 🔴 THE FIRST PASS WAS NEVER ITEMISED, SO IT COULD NOT BE ADDED TO

`[measured 8/21]` `claude/owed-tests.md` T11 recorded a first pass of **"40 gradeable probabilities across 8/20's six evening arms"** — with **bucket counts only and no list of which six arms.** ⛔ **An accumulator you cannot deduplicate cannot be accumulated into.** A second pass over the same slate would have silently double-counted starts that are already in it.

✅ **THE PASS BELOW IS ITEMISED, COVERS ALL 12 OF 8/20's GRADED ARMS, AND SUPERSEDES THE UN-ITEMISED 40.** ➡️ **Standing requirement: every shadow pass names its starts.**

## 8/20 — 83 rungs across **12 distinct starts** (n = 12)

Pure-model `P(K > rung)`, rungs retained where the model probability falls in **[8%, 97%]**. `H` = hit.

| Pitcher | E[K] | actual K | rungs — `line: model% / blend% → hit` |
|---|---|---|---|
| Lambert | 6.35 | **3** | 2.5:95/98→H · 3.5:88/84 · 4.5:76/71 · 5.5:61/59 · 6.5:45/34 · 7.5:31/25 · 8.5:19/12 · 9.5:11/8 |
| Dobnak | 4.27 | **4** | 1.5:93/88→H · 2.5:80/82→H · 3.5:62/56→H · 4.5:42/29 · 5.5:26/21 · 6.5:14/7 |
| Kay | 4.41 | **6** | 1.5:93/95→H · 2.5:82/80→H · 3.5:64/67→H · 4.5:45/44→H · 5.5:28/23→H · 6.5:16/14 |
| Cole | 6.58 | **8** | 2.5:96/91→H · 3.5:89/88→H · 4.5:79/79→H · 5.5:64/59→H · 6.5:49/44→H · 7.5:34/30→H · 8.5:22/21 · 9.5:13/13 |
| Alvarez | 4.10 | **5** | 1.5:92/96→H · 2.5:78/79→H · 3.5:59/64→H · 4.5:39/45→H · 5.5:23/17 · 6.5:12/6 |
| Jump | 5.11 | **3** | 1.5:96/91→H · 2.5:88/88→H · 3.5:75/77 · 4.5:58/69 · 5.5:40/43 · 6.5:25/33 · 7.5:14/17 |
| Holmes | 3.95 | **3** | 1.5:90/95→H · 2.5:75/77→H · 3.5:56/63 · 4.5:36/33 · 5.5:21/15 · 6.5:11/7 |
| Bradish | 4.69 | **5** | 1.5:95/97→H · 2.5:85/90→H · 3.5:69/72→H · 4.5:50/48→H · 5.5:33/33 · 6.5:19/22 · 7.5:10/11 |
| Gasser | 4.95 | **4** | 1.5:96/98→H · 2.5:87/94→H · 3.5:73/76→H · 4.5:55/56 · 5.5:38/33 · 6.5:23/22 · 7.5:13/6 |
| deGrom | 5.81 | **10** | 2.5:93/96→H · 3.5:83/83→H · 4.5:69/71→H · 5.5:52/59→H · 6.5:36/42→H · 7.5:23/29→H · 8.5:13/20→H |
| G. Williams | 7.70 | **11** | 3.5:95/97→H · 4.5:88/86→H · 5.5:78/77→H · 6.5:65/62→H · 7.5:50/47→H · 8.5:37/36→H · 9.5:25/28→H · 10.5:16/20→H · 11.5:9/7 |
| G. Rodriguez | 4.14 | **6** | 1.5:92/88→H · 2.5:78/81→H · 3.5:59/60→H · 4.5:40/47→H · 5.5:24/27→H · 6.5:13/10 |

### PURE MODEL

| Bucket | rungs | **starts** | predicted | actual |
|---|---|---|---|---|
| 0–20% | 15 | 12 | 13.6% | 13.3% |
| **20–40%** | 19 | 12 | **29.6%** | **47.4%** |
| 40–60% | 13 | 12 | 50.9% | 53.8% |
| **60–70%** | 7 | 7 | **64.8%** | **85.7%** |
| 70–80% | 9 | 9 | 76.8% | 77.8% |
| 80–90% | 8 | 8 | 86.3% | 87.5% |
| 90–100% | 12 | 12 | 93.8% | 100.0% |

✅ **`[audited 8/21]` RE-DERIVED FROM THE ITEMISED RUNGS — THIS TABLE IS CORRECT AS PRINTED.** All 83 rungs re-bucketed from `Poisson(E[K])`; **`rungs`, `starts` and `actual` reproduce on 7/7 rows, `predicted` to within 0.1 point** (the residual is the display rounding of the printed rung integers).

⚠️ **A reported "misfiling across the 20–40 / 40–60 boundary — should be 20/12, not 19/13" was CHECKED AND REFUTED.** Two rungs print as `40`: **Jump 5.5** and **G. Rodriguez 4.5**. Unrounded they are **40.33%** and **39.85%**, so under `[lo, hi)` they belong in **different** buckets, exactly as the table has them. The published cells are forced by the rows: **20–40% is 9 hits / 19 rungs = 47.4%** ✅ and **40–60% is 7 hits / 13 rungs = 53.8%** ✅. The proposed 20/12 split would give **45.0%** and **58.3%**, which match nothing on the page.

⛔ **This is why rule 1 in the header exists.** Bucketing on the PRINTED integers gives **18/14** — and also breaks the 70–80% and 80–90% rows, which nobody had flagged. **The printed-integer recount is the broken instrument, not the table.**

### BLEND (50/50)

| Bucket | rungs | **starts** | predicted | actual |
|---|---|---|---|---|
| 0–20% | 16 | 12 | 11.9% | 12.5% |
| 20–40% | 17 | 11 | 28.3% | 35.3% |
| **40–60%** | 13 | 11 | **50.0%** | **76.9%** |
| 60–70% | 6 | 6 | 64.3% | 66.7% |
| 70–80% | 10 | 10 | 76.0% | 80.0% |
| 80–90% | 9 | 7 | 85.3% | 88.9% |
| 90–100% | 12 | 10 | 94.9% | 100.0% |

✅ **`[audited 8/21]` RE-DERIVED FROM THE ITEMISED RUNGS — THIS TABLE IS CORRECT AS PRINTED.** **`rungs`, `starts` and `actual` reproduce on 7/7 rows, `predicted` to within 0.1 point.** Three blend rungs print exactly on an edge — **Kay 2.5 (`80`), deGrom 8.5 (`20`), G. Williams 10.5 (`20`)** — and all three sit just BELOW their printed integer. Resolving them that way is not a free choice: it is the ONLY assignment that reproduces the page.

⚠️ **A reported error in the 80–90% row — "the 9 rungs come from 8 distinct starts, not 7" — was CHECKED AND REFUTED.** The 9 rungs are **Lambert 3.5 · Dobnak 1.5, 2.5 · Cole 3.5 · Jump 2.5 · deGrom 3.5 · G. Williams 4.5 · G. Rodriguez 1.5, 2.5** — **7 distinct (pitcher, date) pairs**, with Dobnak and G. Rodriguez each contributing two. **The published `predicted` proves it arithmetically:** those 9 blends mean to **85.33%**, the printed **85.3%**. Adding Kay's 2.5 as a 10th rung (the only candidate 8th start) drops the mean to **84.8%** and the actual to 9/10 = **90.0%**, neither of which is on the page. ✅ **7 starts, 8 hits of 9 = 88.9%. Correct as printed.**

🔴 **Both refutations are logged rather than silently dropped, because the next run will be tempted to "find" them again.**

🔴 **n = 12 STARTS. NOT 83.** ⛔ **Do not read the 20–60% rows as a finding.** They point the same way as the first pass — under-confident below ~70% — **and 8/20 was an 8/10 slate, so every bucket is lifted by the same good day.** **T11 needs ≥ 40 distinct starts. It is at 12.**

⚠️ **It still contradicts the carded 60–70% bucket, which reads OVER-confident at −22.5.** The reconciliation offered in T11 — carded is blended, shadow is pure model — **is not supported here either: the blend table shows the same under-confidence.** **The contradiction is unresolved and should stay unresolved until n is real.**

## 🆕 8/21 — 48 rungs across **6 distinct starts** (n = 6)

🔴 **METHOD, AND IT IS DIFFERENT FROM 8/20's IN THE WAY THAT MATTERS.** `E[K]` was **not** rebuilt from the formula. It was **inverted from the card's own logged `model` probability** at the carded rung under `Poisson`, so the ladder is anchored to the number that was actually bet.

✅ **THE INVERSION IS VALIDATED AGAINST AN INDEPENDENTLY PUBLISHED FIGURE.** `claude/pick-ledger.md` states Misiorowski's `E[K]` as **7.69** in prose. **Inverting his logged 64.7% at o6.5 returns 7.69.** ⛔ **That is the only `E[K]` printed anywhere for this slate, and it matches to two decimals.**

✅ **The blend column uses the raw rate at each rung computed from PRIOR STARTS ONLY** — the same denominators the card used, all 6 re-verified against re-pulled game logs on 8/22.

🔴 **TWO OF THE EIGHT CARDED PLAYS ARE NOT IN THIS PASS, AND THE REASON IS STATED RATHER THAN THE `n` BEING PADDED.** **Chris Sale u18.5 outs and Yoshinobu Yamamoto o17.5 outs are OUTS plays: their logged `model` number is an outs probability, so there is no `E[K]` to invert.** ⛔ **Building K ladders for them would mean reconstructing `E[K]` from the formula — a reconstruction inside a pass whose whole method is a read.** ➡️ **`n = 6 distinct starts`, not 8. Their K results are recorded in the rule-15 table above and can be added by a future interactive pass that has the model inputs in hand.**

| Pitcher | E[K] | actual K | rungs — `line: model% / blend% → hit` |
|---|---|---|---|
| Schlittler | 7.08 | **4** | 3.5:92/94→H · 4.5:83/88 · 5.5:71/76 · 6.5:56/59 · 7.5:41/42 · 8.5:28/24 · 9.5:18/15 · 10.5:10/11 |
| Manaea | 5.72 | **4** | 2.5:92/96→H · 3.5:82/87→H · 4.5:68/63 · 5.5:51/50 · 6.5:35/34 · 7.5:22/15 · 8.5:13/10 |
| Burke | 6.66 | **4** | 2.5:96/93→H · 3.5:90/85→H · 4.5:79/75 · 5.5:65/59 · 6.5:50/44 · 7.5:35/37 · 8.5:23/21 · 9.5:14/14 |
| Gore | 6.44 | **7** | 2.5:95/96→H · 3.5:88/86→H · 4.5:77/77→H · 5.5:62/56→H · 6.5:46/44→H · 7.5:32/26 · 8.5:20/20 · 9.5:12/8 |
| Detmers | 6.04 | **5** | 2.5:94/97→H · 3.5:85/89→H · 4.5:72/76→H · 5.5:56/60 · 6.5:40/42 · 7.5:26/31 · 8.5:16/20 · 9.5:9/8 |
| Misiorowski | 7.69 | **6** | 3.5:95/97→H · 4.5:88/94→H · 5.5:78/87→H · 6.5:65/76 · 7.5:50/64 · 8.5:36/46 · 9.5:25/34 · 10.5:15/21 · 11.5:9/11 |

**Starts named, per the accumulation protocol: Schlittler 2026-08-21 (4 K) · Manaea 2026-08-21 (4 K) · Burke 2026-08-21 (4 K) · Gore 2026-08-21 (7 K) · Detmers 2026-08-21 (5 K) · Misiorowski 2026-08-21 (6 K).** **No (pitcher, date) pair here appears in the 8/20 pass.**

### 8/21 PURE MODEL

| Bucket | rungs | **starts** | predicted | actual |
|---|---|---|---|---|
| 0–20% | 9 | 6 | 12.8% | 0.0% (0/9) |
| 20–40% | 11 | 6 | 29.2% | 0.0% (0/11) |
| **40–60%** | 7 | 6 | **50.1%** | **14.3% (1/7)** |
| **60–70%** | 4 | 4 | **65.0%** | **25.0% (1/4)** |
| 70–80% | 5 | 5 | 75.4% | 60.0% (3/5) |
| 80–90% | 6 | 6 | 86.2% | 83.3% (5/6) |
| 90–100% | 6 | 6 | 94.2% | 100.0% (6/6) |

### 8/21 BLEND (50/50)

| Bucket | rungs | **starts** | predicted | actual |
|---|---|---|---|---|
| 0–20% | 10 | 6 | 13.2% | 0.0% (0/10) |
| 20–40% | 8 | 6 | 28.3% | 0.0% (0/8) |
| **40–60%** | 9 | 6 | **49.2%** | **22.2% (2/9)** |
| 60–70% | 3 | 3 | 62.4% | 0.0% (0/3) |
| 70–80% | 5 | 5 | 76.0% | 40.0% (2/5) |
| 80–90% | 6 | 6 | 87.0% | 83.3% (5/6) |
| 90–100% | 7 | 6 | 95.4% | 100.0% (7/7) |

🔴 **8/21 POINTS THE OPPOSITE WAY TO 8/20 IN EVERY MIDDLE BUCKET, AND THAT IS THE FINDING.** **8/20 read badly UNDER-confident from 20–70%. 8/21 reads badly OVER-confident across the same range.** ⚠️ **The mechanism is obvious and is the same one the 8/20 block warned about in reverse: four of the six arms struck out exactly 4, so every rung above 4.5 missed on four different pitchers at once. One slate lifts or sinks every bucket together.** ⛔ **Neither slate is evidence about the model. This is precisely why T11's bar is 40 distinct starts.**

## 🆕 8/22 — 54 rungs across **7 distinct starts** (n = 7)

🔴 **METHOD: same as 8/21 — `E[K]` was INVERTED from each play's own logged `model` probability at the carded rung under `Poisson`, not rebuilt from the formula.** ✅ **The ladder is anchored to the number that was actually carded.**

✅ 🔴 **THE INVERSION IS VALIDATED SIX WAYS THIS TIME, NOT ONCE.** `claude/pick-ledger.md`'s 8/22 TOP PROJECTIONS block prints `E[K]` independently for six of these arms, and the inversion reproduces every one:

| Pitcher | inverted from the logged `model` | printed independently in the ledger |
|---|---|---|
| **Dylan Cease** | **7.97** | **7.97** ✅ |
| **Tarik Skubal** | **7.15** | **7.15** ✅ |
| **Christian Scott** | **5.96** | 5.97 ✅ |
| **Jared Jones** | **5.31** | **5.31** ✅ |
| **Ryan Weathers** | **5.06** | 5.05 ✅ |
| **Hunter Brown** | **5.27** | **5.27** ✅ |

✅ **AND AN INTERNAL CROSS-CHECK THE PREVIOUS PASSES COULD NOT RUN: Jared Jones was carded at TWO rungs (o2.5 at 89.9% and o3.5 at 77.5%), so his `E[K]` can be inverted twice, independently. The two inversions give 5.308 and 5.303 — a gap of 0.005.** ⛔ **Had they disagreed, the whole pass would have been discarded.**

🔴 **TWO OF THE THIRTEEN CARDED PLAYS ARE NOT IN THIS PASS, AND THE REASON IS STATED RATHER THAN THE `n` BEING PADDED. Jake Irvin u15.5 outs and Martín Pérez o14.5 outs are OUTS-ONLY plays: their logged `model` is an outs probability, so there is no `E[K]` to invert.** ⚠️ **Cease, Skubal and Hunter Brown each carded BOTH a K play and an outs play, and enter through their K play — one start each, counted once.** ➡️ **`n = 7 distinct starts`, not 13 and not 9.**

✅ **The blend column uses the raw rate at each rung computed from PRIOR STARTS ONLY, re-derived from the game logs on 2026-08-23.**

| Pitcher | E[K] | actual K | rungs — `line: model% / blend% → hit` |
|---|---|---|---|
| Jared Jones | 5.31 | **5** | 1.5:97/98→H · 2.5:90/95→H · 3.5:78/82→H · 4.5:61/56→H · 5.5:44/40 · 6.5:28/25 · 7.5:17/16 · 8.5:9/8 |
| Ryan Weathers | 5.06 | **3** | 1.5:96/98→H · 2.5:88/92→H · 3.5:74/83 · 4.5:57/60 · 5.5:39/47 · 6.5:25/31 · 7.5:14/17 |
| Christian Scott | 5.96 | **6** | 2.5:94/94→H · 3.5:85/87→H · 4.5:71/80→H · 5.5:55/61→H · 6.5:39/39 · 7.5:25/18 · 8.5:15/7 · 9.5:8/4 |
| Dylan Cease | 7.97 | **8** | 3.5:96/98→H · 4.5:90/95→H · 5.5:81/88→H · 6.5:68/78→H · 7.5:54/60→H · 8.5:40/46 · 9.5:28/34 · 10.5:18/20 · 11.5:11/12 |
| Rhett Lowder | 4.19 | **1** | 1.5:92/91 · 2.5:79/79 · 3.5:60/64 · 4.5:41/42 · 5.5:25/23 · 6.5:13/12 |
| Tarik Skubal | 7.15 | **11** | 3.5:93/94→H · 4.5:84/87→H · 5.5:72/75→H · 6.5:57/58→H · 7.5:42/40→H · 8.5:29/30→H · 9.5:19/15→H · 10.5:11/8→H |
| Hunter Brown | 5.27 | **4** | 1.5:97/98→H · 2.5:90/95→H · 3.5:77/85→H · 4.5:61/57 · 5.5:43/41 · 6.5:28/33 · 7.5:16/20 · 8.5:9/8 |

**Starts named, per the accumulation protocol: Jared Jones 2026-08-22 (5 K) · Ryan Weathers 2026-08-22 (3 K) · Christian Scott 2026-08-22 (6 K) · Dylan Cease 2026-08-22 (8 K) · Rhett Lowder 2026-08-22 (1 K) · Tarik Skubal 2026-08-22 (11 K) · Hunter Brown 2026-08-22 (4 K).** **No (pitcher, date) pair here appears in the 8/20 or 8/21 pass.**

### 8/22 PURE MODEL

| Bucket | rungs | **starts** | predicted | actual |
|---|---|---|---|---|
| 0–20% | 12 | 7 | 13.3% | 16.7% (2/12) |
| 20–40% | 9 | 7 | 29.5% | 11.1% (1/9) |
| 40–60% | 9 | 7 | 48.2% | 44.4% (4/9) |
| 60–70% | 4 | 4 | 62.6% | 50.0% (2/4) |
| 70–80% | 6 | 6 | 75.1% | 66.7% (4/6) |
| 80–90% | 7 | 6 | 86.7% | 100.0% (7/7) |
| 90–100% | 7 | 7 | 94.8% | 85.7% (6/7) |

### 8/22 BLEND (50/50)

| Bucket | rungs | **starts** | predicted | actual |
|---|---|---|---|---|
| 0–20% | 13 | 7 | 12.7% | 15.4% (2/13) |
| 20–40% | 9 | 7 | 32.7% | 22.2% (2/9) |
| 40–60% | 9 | 6 | 51.7% | 33.3% (3/9) |
| 60–70% | 2 | 2 | 62.6% | 50.0% (1/2) |
| 70–80% | 4 | 4 | 78.0% | 75.0% (3/4) |
| 80–90% | 6 | 6 | 85.1% | 83.3% (5/6) |
| 90–100% | 11 | 7 | 95.3% | 90.9% (10/11) |

⚠️ **8/22's middle buckets sit BELOW their predictions, like 8/21 and unlike 8/20 — but nowhere near as violently as 8/21, and the 80–90% row went 7/7.** ⛔ **Seven correlated starts. Read nothing off this table alone.**

## 🔴 MERGED PURE-MODEL ACCUMULATOR — 8/20 + 8/21, **18 distinct starts, 131 rungs**

> ⚠️ 🔴 **SUPERSEDED 2026-08-23 by the 25-start merge further down this page. KEPT, NOT DELETED — it is the state of the accumulator at n=18 and the rows behind it are unchanged.** ⛔ **Quote the 25-start table, not this one.**

✅ 🔴 **THE MERGE IS LICENSED BY A REGENERATION, NOT BY TRUST.** **8/20's pure-model rungs were regenerated from the `E[K]` values printed in its own table and re-bucketed unrounded; the result reproduces the published 8/20 PURE MODEL table on all 7 rows — `rungs`, `starts`, `predicted` and `actual` — for all 83 rungs.** ⛔ **Had it not reproduced, the merge would not have been made.**

| Bucket | rungs | **starts** | predicted | actual |
|---|---|---|---|---|
| 0–20% | 24 | 18 | 13.3% | 8.3% (2/24) |
| **20–40%** | 30 | 18 | **29.5%** | **30.0% (9/30)** |
| 40–60% | 20 | 18 | 50.6% | 40.0% (8/20) |
| 60–70% | 11 | 11 | 64.9% | 63.6% (7/11) |
| 70–80% | 14 | 14 | 76.3% | 71.4% (10/14) |
| 80–90% | 14 | 14 | 86.2% | 85.7% (12/14) |
| 90–100% | 18 | 18 | 93.9% | 100.0% (18/18) |

**131 rungs, 66 hits, 18 distinct starts.** ⛔ **`n = 18 STARTS. NOT 131.**

🔴 **ONE ADDED SLATE ERASED T11's HEADLINE.** **The 20–40% bucket read 29.6% predicted against 47.4% actual on 8/20 — a 17.8-point under-confidence that was the entire basis of T11's hypothesis. Merged, it reads 29.5% against 30.0%. Dead on.** **The 60–70% bucket went 64.8/85.7 to 64.9/63.6.** ⛔ **T11 is NOT re-decided here and its pass criterion is untouched** — but **the honest state of the evidence is that the under-confidence signal did not survive contact with a second slate**, and that must be on the page before it is quoted again.

⚠️ **The 90–100% bucket is 18/18 across both slates against a 93.9% prediction.** ⛔ **Do not read that as under-confidence either — 18 near-certain rungs concentrated in 18 starts is the most correlated cell in the table.**

⛔ **THE BLEND TABLES ARE NOT MERGED THIS RUN, AND THE REASON IS RECORDED SO NOBODY THINKS IT WAS AN OVERSIGHT.** **Merging the blend needs 8/20's per-rung RAW rates, which are not on this page — only the finished blend integers are, and the header's own rule 1 forbids re-deriving from printed integers.** ➡️ **Recovering them means re-pulling 12 game logs. Cheap in an interactive session, and NOT done headless on a run whose job was verification.** **The two blend tables stay side by side until then.**

**T11 progress: 18 / 40 distinct starts.**

## 🔴 🆕 MERGED PURE-MODEL ACCUMULATOR — 8/20 + 8/21 + 8/22, **25 distinct starts, 185 rungs**

✅ 🔴 **THE MERGE IS AGAIN LICENSED BY A REGENERATION, NOT BY TRUST.** **8/20's and 8/21's pure-model rungs were regenerated from the `E[K]` values printed in their own tables and re-bucketed unrounded.** **8/20 reproduces its published table on ALL 7 ROWS — `rungs`, `starts`, `predicted` and `actual`, 83 rungs.** **8/21 reproduces its published table on 7 of 7 rows once ONE boundary rung is placed as published.**

⚠️ 🔴 **THAT ONE RUNG IS WORTH RECORDING, BECAUSE IT IS THIS PAGE'S OWN HEADER RULE 1 FIRING IN PRACTICE.** **Regenerating from Detmers' printed 2-dp `E[K]` of 6.04 puts his 6.5 rung at 40.012% — just ABOVE the 40% boundary — while the published 8/21 table has it just BELOW, in the 20–40% bucket.** **The published pass used the unrounded inverted value; the regeneration used the printed one.** ✅ **The published bucketing is correct and was kept; the rung is a MISS either way, so no `actual` figure moves — only two `rungs` counts and two `predicted` means.** ⛔ **Had the merge been built on the regeneration without checking, it would have silently disagreed with the page above it.**

| Bucket | rungs | **starts** | predicted | actual |
|---|---|---|---|---|
| 0–20% | 36 | 25 | 13.3% | 11.1% (4/36) |
| **20–40%** | 39 | 25 | **29.5%** | **25.6% (10/39)** |
| 40–60% | 29 | 25 | 49.9% | 41.4% (12/29) |
| 60–70% | 15 | 15 | 64.3% | 60.0% (9/15) |
| 70–80% | 20 | 20 | 76.0% | 70.0% (14/20) |
| 80–90% | 21 | 20 | 86.4% | 90.5% (19/21) |
| 90–100% | 25 | 25 | 94.2% | 96.0% (24/25) |

**185 rungs, 92 hits, 25 distinct starts.** ⛔ **`n = 25 STARTS. NOT 185.**

🔴 **T11's HYPOTHESIS IS NOW DEAD ON THREE SLATES AND HAS TURNED OVER.** **The 20–40% bucket that read 29.6% predicted against 47.4% actual on 8/20 alone — the entire basis of T11 — read 29.5 / 30.0 at 18 starts and now reads 29.5 / 25.6 at 25.** ➡️ **The under-confidence signal did not survive a second slate and has gone mildly the OTHER way on a third.** **60–70% reads 64.3 / 60.0 and 70–80% reads 76.0 / 70.0 — both now slightly OVER-confident, which is the direction the carded calibration table has said all along.** ⛔ **T11 is NOT re-decided here and its pass criterion is untouched. The evidence is recorded as it stands.**

⚠️ **The 90–100% bucket is 24/25 and the 80–90% bucket 19/21.** ⛔ **Still the most correlated cells in the table — near-certain rungs concentrated in the same starts. Do not read them as under-confidence.**

⛔ **THE BLEND TABLES ARE STILL NOT MERGED, FOR THE SAME REASON AS 8/22's RUN: it needs 8/20's per-rung RAW rates, which are not on this page, and re-deriving them from the printed blend integers is forbidden by this doc's own header rule 1.** ⚠️ 🆕 **The 8/21 and 8/22 blend tables COULD now be merged with each other — both were computed from re-derived prior-starts-only raw rates — but a two-thirds merge sitting beside a three-thirds pure-model merge is an invitation to quote the wrong `n`. ⛔ Left unmerged deliberately.**

**T11 progress: 25 / 40 distinct starts.**

## Accumulation protocol

1. **Name every start.** Pitcher, date, actual K. A pass without an itemised start list cannot be merged and must be discarded.
2. **Deduplicate on (pitcher, date)** before adding.
3. **Report `n` as distinct starts.** Rungs are a column width, not a sample size.
4. **Carry the pure-model AND blend tables side by side** so they can be told apart.
5. ⛔ **Never re-decide T11's pass criterion.** It is fixed in `claude/owed-tests.md`.
6. 🔴 **Recount the buckets from the rungs before citing them.** See the header. **The printed `n` is a claim, not a source.**

---

# 🔴 RULE 50 ACCUMULATOR — the head-to-head tiebreaker

**Rule 50 fires when the class evidence and the season/rate evidence CONTRADICT each other, and the head-to-head record is used to break the tie.** This table exists so we can eventually answer the only question that matters about it: **when head-to-head overrode a class rate, was it right?**

⚠️ **`n` here is the number of prior head-to-head starts, and it is usually TINY — two or three, sometimes zero.** ⛔ **Log `n=0` cases too.** A tiebreaker that gets invoked on n=0 is a tiebreaker being used as a vibe, and that is precisely what this accumulator is for catching.

⛔ **UNGRADED UNTIL THE RESULT COLUMN IS FILLED.** ⛔ **Never quote a hit rate off this table until it has been graded; and when it has, report `n` as distinct plays.**

**Columns:** `date | play | the contradiction that triggered rule 50 | head-to-head record (n) | what H2H argued | W/L | was H2H right?`

| date | play | contradiction | head-to-head (n) | H2H argued | W/L | H2H right? |
|---|---|---|---|---|---|---|
| 2026-08-21 | **E. Rodríguez u5.5 K vs CIN** | CIN is the **easiest lineup in baseball to strike out** (meanK 5.58, Δ +0.48) pulling the projection UP, against his own low season rate | **3 K and 3 K** (n=2) | **FOR the under** — both prior meetings landed well under 5.5, **confirming** his own 21/25 and a matched class of 30/41 | **W** — **4 K** (5.2 IP), under 5.5 | ✅ **RIGHT** — *confirm*, not override |
| 2026-08-21 | **Cam Schlittler o4.5 K vs TOR** | a matched class read **18/29** and was being used to DOUBT the play | **7 K, 7 K, 7 K (2026) and 3 K, 2 K (2025)** (n=5) | **AGAINST the 18/29 class** — the three 2026 meetings all cleared 4.5 comfortably; the two 2025 meetings did not | **L** — **4 K** (6.0 IP), missed 4.5 | ❌ **WRONG** — *override*, and the class it overrode was right |
| 2026-08-21 | **Yamamoto o5.5 K vs PIT** | ⚠️ **NOT IN THE 8/21 SEED TABLE — added at grading, and logged as such.** Here the head-to-head was the *dissenting* evidence: the projection and the rate case supported the over, the lone meeting did not | **5 K** (n=1, 2025) | **AGAINST the over** — 5 K is a **LOSS** at 5.5 | **W** — **9 K** (6.1 IP), cleared 5.5 by three | ❌ **WRONG** — *override attempt on n=1* |
| 2026-08-21 | **Sonny Gray o4.5 K vs SF** | a **12/23** season rate and a **30/60** class both argued against the over | **6 K and 7 K (Sept 2025)** (n=2) | **AGAINST both the 12/23 season rate and the 30/60 class** — both meetings cleared | **W** — **6 K** (6.0 IP), cleared 4.5 | ✅ **RIGHT** — *override* |
| 2026-08-22 | **Dylan Cease o6.5 K vs NYY** | elite arm (13.19 K/9) against the **28th-hardest lineup to strike out** (5.38 meanK), but a matched class of **1/4** | **9 K, 9 K, 10 K** (n=3, 2025–26) | **FOR the over** — and it was the ONLY real evidence, because the class was n=4 and UNINFORMATIVE | **W** — **8 K** (6.2 IP), cleared 6.5 | ✅ **RIGHT** — *override of an uninformative class* |
| 2026-08-22 | **Jared Jones o2.5 K vs LAD** | a **14/14** perfect raw record (T21 flag) against a merely-average matchup | **4 K in 12 outs** (n=1, 2026-06-10) | **FOR the over** — the one meeting cleared | **W** — **5 K** (4.0 IP), cleared 2.5 | ✅ **RIGHT** — *confirm* |
| 2026-08-22 | **Tarik Skubal u8.5 K vs PIT** | elite arm against a **high-K lineup** (PIT 5.34 meanK, 27th-hardest) | **6 K** (n=1) | **FOR the under** — the one meeting cleared | 🔴 **L** — **11 K** (7.0 IP), his season high | ❌ **WRONG** — *override attempt on n=1.* ⚠️ **Not followed: the carried figure was nudged DOWN toward the class (69.7 → 67.0)** |
| 2026-08-22 | **Jake Irvin u15.5 outs vs MIA** | the model's **biggest edge on the board (+17.4)** against a matched class quoted at 46.9% on 4+IP starts | **15 outs** (n=1) | **FOR the under** — the one meeting cleared | 🔴 **L** — **18 outs** (6.0 IP) | ❌ **WRONG** — *override attempt on n=1.* 🔴 **Not followed: the carried figure followed the CLASS (70.9 → 62.0), and the class was right again** |
| 2026-08-22 | **Martín Pérez o14.5 outs vs MIL** | shuttled arm (T22 flag) with a 9-out start in his last five, against a class that liked the over | **18 outs** (n=1) | **FOR the over** — the one meeting cleared | 🔴 **L** — **12 outs** (4.0 IP) | ❌ **WRONG** — *confirm* |
| 2026-08-22 | Rhett Lowder o2.5 K vs ARI | shuttled arm (T22) vs the 2nd-hardest K lineup in baseball | 🔴 **n=0 — never faced them** | **nothing — printed as a finding, per rule 50** | L — **1 K** (6.0 IP) | ⛔ **NO CALL — n=0, not in any tally** |
| 2026-08-22 | Christian Scott o4.5 K vs CWS | — | 🔴 **n=0 — never faced them** | **nothing — printed as a finding, per rule 50** | W — **6 K** (4.2 IP) | ⛔ **NO CALL — n=0, not in any tally** |

⚠️ **Read the seed honestly: one of the three (E. Rodríguez) CONFIRMED the other evidence rather than overriding it.** **Tag confirm-vs-override when grading** — an overrule that is right is a real finding; a confirmation that is right tells us nothing.
⚠️ **Schlittler's n=5 splits 3–2 by season.** ⛔ **Do not let a same-season subset be quoted as the whole head-to-head record.**

## 🔴 GRADED — 8/21 DEBUT: **2/4**. `n = 4 distinct plays.`

`[graded 8/22]` **Re-derive this from the four rows above, never from this heading.** The `H2H right?` column reads **✅ ❌ ❌ ✅** — **2 right, 2 wrong.**

| | H2H right | H2H wrong |
|---|---|---|
| **confirm** (H2H agreed with the other evidence) | 1 (E. Rodríguez) | 0 |
| **override** (H2H contradicted a class or season rate) | 1 (Gray) | 2 (Schlittler, Yamamoto) |

⚠️ **The confirm/override split matters more than the 2/4.** Stripping the one confirmation — which tells us nothing, exactly as the seed note warned — the **overrides are 1/3.**

## 🔴 THE FIRST DIRECT HEAD-TO-HEAD-vs-CLASS CONFLICT IN THE PROJECT, AND THE CLASS WON

🔴 **On Schlittler the head-to-head and the matched class FLATLY DISAGREED. The head-to-head read 7 K, 7 K, 7 K across three 2026 meetings — three straight clears of 4.5, no ambiguity. The matched class read 18/29. Rule 50 sided with the head-to-head. He struck out 4.**

⚠️ **THAT IS ONE START. IT MUST NOT RE-ORDER ANYTHING.** ⛔ **Do not demote head-to-head beneath class evidence off this. Do not re-weight rule 50. Do not rewrite the tiebreaker.** A 7/7/7 head-to-head losing once is entirely ordinary noise; 18/29 is 62%, so the class *expected* the play to win too, just less confidently.

➡️ **It is recorded because it is the first time the two sources of evidence pointed in opposite directions on a carded play and we can say which one was right.** That is the exact question this accumulator was built to answer, and this is instance one of it. **Log every future conflict the same way, with the class number and the H2H record both written down BEFORE the result.**

⚠️ **PARALLEL, AND IT IS A WARNING ABOUT THIS PAGE, NOT ABOUT RULE 50: rule 15 also debuted at 1/4.** ⛔ **Neither was re-tuned off its debut slate and neither may be.** **A four-play debut is a sample of four.** The doc's whole thesis — the flat Brier surface, `n = 12 STARTS. NOT 83.` — is that this project's failure mode is fitting to one slate. **Rule 50 is at 4 plays. Accumulate.**

## 🔴 🆕 GRADED — 8/22 ADDS FIVE CALLS. RUNNING: **4/9.** `n = 9 distinct plays.`

`[graded 2026-08-23]` **Re-derive this from the rows above, never from this heading.** **The `H2H right?` column now reads ✅ ❌ ❌ ✅ · ✅ ✅ ❌ ❌ ❌ — 4 right, 5 wrong, plus 2 rows marked NO CALL (n=0) that are in no tally.**

| | H2H right | H2H wrong |
|---|---|---|
| **confirm** (H2H agreed with the other evidence) | **2** (E. Rodríguez, Jones) | **1** (M. Pérez) |
| **override** (H2H contradicted a class or season rate) | **2** (Gray, Cease) | **4** (Schlittler, Yamamoto, Skubal, Irvin) |

⚠️ **Confirms 2/3. 🔴 OVERRIDES 2/6 — a coin flip at best, and that is the only half of this table that could ever be worth anything.**

🔴 **AND THE STRONGEST PATTERN IN NINE PLAYS IS NOT ABOUT RULE 50 AT ALL — IT IS THAT THE MATCHED CLASS HAS NOW BEATEN THE HEAD-TO-HEAD THREE TIMES OUT OF THREE WHEN THEY FLATLY DISAGREED.** **Schlittler (H2H 7/7/7 vs class 18/29 — class right), Skubal u8.5 K (H2H 1/1 vs a 62.1% class — class right), Irvin u15.5 outs (H2H 1/1 vs a class quoted at 46.9% — class right).** ⚠️ **Every one of those H2H samples was n≤5 and two were n=1.** ⛔ **THREE INSTANCES. DO NOT DEMOTE RULE 50, DO NOT RE-WEIGHT IT, DO NOT REWRITE THE TIEBREAKER.** ➡️ **But this is now the specific question the accumulator exists to answer, and it has a direction. Keep logging the class number and the H2H record BEFORE the result, every time.**

⚠️ 🔴 **ONE HONEST QUALIFIER ON THE IRVIN ROW, BECAUSE IT CUTS BOTH WAYS: `claude/pick-ledger.md` records that the 46.9% class figure Irvin was judged against was itself biased by construction (T23) and matched on the wrong axis (T24), and that the corrected figure is 66.7%, which AGREES with the model.** **So on that row "the class was right" is true about the OUTCOME and false about the REASONING that was published.** ✅ **Both halves are recorded; neither is allowed to stand alone.**

~~**Progress: 9 instances (7 gradeable calls + 2 logged n=0 rows with no call).**~~ 🔴 **`[corrected 2026-08-24]` THAT LINE DID NOT RECONCILE AGAINST THE TABLE IT SITS UNDER, AND IT IS STRUCK RATHER THAN DELETED.** **Enumerated programmatically from the rows above: the table holds ELEVEN rows — NINE gradeable calls and TWO `n=0` NO-CALL rows.** **Progress: 11 logged instances = 9 gradeable calls + 2 logged `n=0` rows with no call.** ✅ **The 9 is forced twice over by this section's own evidence: the `H2H right?` column reads ✅ ❌ ❌ ✅ · ✅ ✅ ❌ ❌ ❌ — nine marks, 4 right and 5 wrong — and the heading above reads `4/9`.** ⛔ **The gradeable count must reconcile against the RESULT STRING and the `x/y` HEADING, never against another prose number** (ledger rule 45 / pre-publish check 28). ⛔ **The struck `7` was prose reconciled to nothing; no tally, no bucket and no row moved when it was corrected — 4/9 was right all along.**

---

# 🔴 RULE 51 ACCUMULATOR — the rematch haircut

**Rule 51 fires when a carded pitcher faces the SAME lineup he has already faced within 30 days.** Every such carded play is logged here, hit or miss, so the haircut can eventually be measured instead of assumed.

## ⛔ 🔴 THE PRE-REGISTERED SPECIFICATION FAILED. WHAT IS LEFT IS EXPLORATORY.

⛔ **The pre-registered test was on MEAN K and it is a NULL: drop of 0.30 K, `t = −1.78`.** ⛔ **That is the version that was owed, that is the version that was run, and it FAILED. It does not get quietly replaced by a version that worked.**

⚠️ **A THRESHOLD version does separate, and it is `[exploratory]`, not a finding:**

| threshold | after a strong first meeting | baseline | gap |
|---|---|---|---|
| **4+ K** | **74.6%** | 67.1% | +7.5 |
| **3+ K** | **87.5%** | 84.4% | +3.1 |

⛔ **This specification was chosen AFTER seeing the mean-K null.** ⛔ **It carries no pre-registration and must not be carded off, quoted as measured, or written into the model.** ➡️ **To promote it, pre-register the threshold version in `claude/owed-tests.md` and test it forward on plays logged BELOW this line.**

**Columns:** `date | play | threshold | opponent | first meeting (date, K) | days since | W/L | actual K`

| date | play | threshold | opponent | first meeting | days since | W/L | actual K |
|---|---|---|---|---|---|---|---|
| 2026-08-21 | **Hunter Dobbins o3.5 K** | 3.5 | PHI | **8/10 — 6 K** | **11** | **MISS** — ⛔ **CONFOUNDED, EXCLUDED FROM THE TALLY** | **3 K** (4.0 IP, 78 pitches, 3 ER) |
| 2026-08-22 | **Ryan Weathers o3.5 K** | 3.5 (a **4+ K** bar) | TOR | **2026-08-16 — 4 K** in 7.1 IP | 🔴 **6** | ❌ **MISS** | **3 K** (3.1 IP, 72 pitches, 8 H) |
| 2026-08-22 | **Dylan Cease o6.5 K** | 6.5 (a **7+ K** bar) | NYY | **2026-08-16 — 10 K** in 6.1 IP 🔴 **STRONG first meeting (≥5 K)** | 🔴 **6** | ✅ **HIT** | **8 K** (6.2 IP, 111 pitches) |
| 2026-08-22 | *Dylan Cease u17.5 outs* | *17.5 outs* | *NYY* | *2026-08-16 — 19 outs* | *6* | ⛔ **CONTEXT ROW — OUTS MARKET, OUTSIDE RULE 51'S SCOPE, NOT IN THE TALLY** | *20 outs (6.2 IP)* |

⚠️ **Log EVERY qualifying carded play, including the ones where the haircut was not applied.** ⛔ **A log of only the plays where the rule fired cannot measure the rule.**

## ⛔ 🔴 THE ONE INSTANCE IS CONFOUNDED. IT IS NOT EVIDENCE FOR RULE 51.

`[graded 8/22]` **Dobbins missed — and the miss does not count, in either direction.** **Sam reported he left injured on the first pitch of the 5th inning.**

⛔ **EXCLUDED FROM THE TALLY.** **Rule 51 predicts a haircut for a specific reason: a lineup that has seen a pitcher recently hits him better. A pitcher leaving injured is a different failure entirely.** ⚠️ **Counting an injury exit as confirmation of the rematch haircut would be motivated reasoning** — it would let rule 51 bank a win it did not earn, on the one play that would otherwise have started its record at 0/1.

⚠️ **THE HONEST COUNTER-NOTE, AND IT CUTS THE OTHER WAY: through four innings he was NOT cruising.** **78 pitches, 19 batters faced, 3 earned runs**, and a 3-K pace of **6.75 K/9 against his 8.82 season rate.** ➡️ **The injury cost real equity; it did not cost a won ticket.** At 78 pitches through 4, a 5th inning was likely and a 6th was not — so the extra strikeout was live but never favoured. **Both facts are recorded so that neither side of this can be quoted alone.**

⛔ **Do not re-classify this row later to make an `n` bigger.** The exclusion was decided on the mechanism, not on the result.

### 🔴 🆕 THE 8/22 CARD DID NOT RUN THIS CHECK. THAT IS A PRE-PUBLISH CHECK 36 FAILURE AND IT IS RECORDED AS ONE.

`[found 2026-08-23 by the grading run, not by any pre-publish check]`

🔴 **TWO OF THE THIRTEEN PLAYS ON THE 8/22 CARD WERE REMATCHES SIX DAYS OLD, AND NEITHER ROW STATED THE GAP.** **Ryan Weathers had faced Toronto on 2026-08-16; Dylan Cease had faced the Yankees on 2026-08-16. Both are inside the 30-day window by a wide margin.**

⚠️ 🔴 **RULE 50 WAS RUN AND PRINTED ON BOTH — the card's head-to-head table names Weathers' three meetings and Cease's three. RULE 51 WAS NOT.** ➡️ **Running the head-to-head is not the same as running the rematch check, even though both read the same game log.** **Pre-publish check 36 requires the GAP IN DAYS on the row, and neither row carried one.**

⛔ **NOTHING ABOUT THE CARD IS RESTATED OR RE-GRADED FOR THIS.** **The plays were carded on their blends, the blends are unchanged, and rule 51 is EXPLORATORY and was never entitled to move a number** (its pre-registered mean-K specification FAILED at t=−1.78). ✅ **What changes is that the two instances are now LOGGED, which is all the accumulator ever wanted.**

## ⚠️ 🔴 TWO CLEAN INSTANCES NOW EXIST — AND THEY POINT IN OPPOSITE DIRECTIONS. **LOG, DO NOT CONCLUDE.**

`[graded 2026-08-23]`

- ❌ **Weathers MISSED at a 4+ K bar** six days after a 4-K meeting — the direction the exploratory haircut predicts.
- ✅ **Cease HIT at a 7+ K bar** six days after a **10-K** meeting — which is the exact conditional the exploratory finding is about (*"conditional on a strong ≥5 K first meeting, the next start reaches 4+ K only 67.1% against the same team"*), **and it cleared a bar two strikeouts higher than the one that conditional was measured at.**

⛔ **n = 2. ONE SLATE. THIS IS NOT EVIDENCE IN EITHER DIRECTION** and it must never be quoted as a rate. ⛔ **And the pre-registered specification is still FAILED and still closed; the replacement specification for the September re-fit is untouched.**

**Progress: 2 clean instances / 1 logged and confounded.**

---

# 🔴 RULE 53 ACCUMULATOR — plays SHOWN-BUT-FLAGGED rather than removed

**Standing instruction from Sam, 2026-08-22:** *"it should be up to me to decide whcih i feel comfortable with your job is to provide me the data"*

➡️ **A play that fails a check is now PRINTED WITH THE FAILING NUMBER ATTACHED, not cut from the board.** The check still runs and still says what it says; it no longer gets to delete the row.

## 🔴 PURPOSE: MEASURE WHETHER THE CHECKS THAT USED TO REMOVE PLAYS WERE ACTUALLY RIGHT TO.

**Every removal was an unfalsifiable claim** — the play vanished, so the check was never scored. **Flagging instead of removing makes the check gradeable.**

**Track, per flagged play:** `date | play | which check flagged it | the flagging number | did Sam bet it? | result`

| date | play | check that flagged it | flagging number | Sam bet it? | result |
|---|---|---|---|---|---|
| 2026-08-21 | **Yamamoto o5.5 K** | price / break-even | **−300 → needs 75.0%** | ✅ yes | ✅ **WIN — 9 K** |
| 2026-08-21 | **Sonny Gray o4.5 K** | price / break-even | **−230 → needs 69.7%** | ✅ yes | ✅ **WIN — 6 K** |
| 2026-08-21 | **Burke o3.5 K** | price / break-even | **−1000 → needs 90.9%** | ✅ yes | ✅ **WIN — 4 K** |
| 2026-08-21 | **Chandler u15.5 outs** | price / break-even | **−160 → needs 61.5%** | ✅ yes | ✅ **WIN — 12 outs** |
| **2026-08-22** | **Jake Irvin u15.5 outs** | **matched class (STEP 4B)** | 🔴 **46.9% (23/49) on 4+IP — delivered as the headline; 55.2% (32/58) on ALL starts; 66.7% (18/27) durability-matched** | ✅ yes — **$25 straight, Hard Rock −115** | ❌ **LOSS — 18 outs** |
| **2026-08-22** | **Tarik Skubal u95.5 pitches** *(Sam's slip 2 leg)* | **price disagreement + UNMODELLED market** | 🔴 **−115 implies ~53.5% against this project's 82% — a ~29-point gap, the largest in the project's history, with NO model cross-check because no fitted pitch-count equation exists** | ✅ yes — **leg of a $29 two-pick** | ❌ **LOSS — 106 pitches** |

## 🔴 THE SEED IS THE REASON THE RULE EXISTS

`[8/21]` **Sam named six plays. FIVE WON. Claude argued against four of them — every one on price grounds, and all four of those won.** **That is the slate that produced the standing instruction above, so it is written down here rather than referred to.**

⚠️ **STATE BOTH SIDES, AND THE ACCUMULATOR ONLY WORKS IF BOTH STAY ON THE PAGE:**

1. ⚠️ **The price logic is DEFENSIBLE. A bet can win and still be bad value.** −300 needs 75.0% and −1000 needs 90.9% *regardless of what happened on 8/21*. Four wins at those prices is exactly what those prices predict most of the time — **the break-even objection was never a prediction that they would lose.** ⛔ **Do not read 4/4 as the price check being refuted.**
2. ⚠️ **`n = 6` on one slate is NOT A FINDING.** It is the same error this doc catalogues everywhere else — rule 15's flat Brier surface at n=12, `n = 12 STARTS. NOT 83.` **One slate cannot settle this and neither can ten.**

➡️ **The accumulator exists so that in fifty plays' time this is a MEASUREMENT instead of an ARGUMENT.** ⛔ **Until then: log, do not conclude.** ⛔ **Do not quote a hit rate off four rows.**

## 🔴 🆕 8/22 — THE FIRST TWO FLAGS THAT WERE RIGHT, AND THEY WERE THE TWO BIGGEST FLAGS EVER RAISED

`[graded 2026-08-23]` **The seed was 4/4 against the checks. 8/22 adds two flagged plays Sam bet and BOTH LOST.** **Running: the flag predicted the outcome in 2 of 6.**

⚠️ 🔴 **AND THE IRVIN ROW IS THE MOST INSTRUCTIVE ENTRY IN THIS DOCUMENT, BECAUSE THE FLAG WAS RIGHT FOR A REASON THAT HAD ALREADY BEEN SHOWN TO BE WRONG.** **The 46.9% headline was biased low by construction (T23) and matched on the wrong axis (T24); the corrected figure, 66.7%, AGREES with the model's 61.8% instead of contradicting it. The bet lost anyway.** ⛔ **A flag that lands for the wrong reason is not a vindication of the flag. Score the CHECK, not the play** — and on the corrected figure this check did not fire at all.

🔴 **THE SKUBAL PITCH-COUNT ROW IS THE CLEANEST ONE AND IT IS THE ONE TO WATCH.** **The flag was raised pregame, in writing, in these terms: the largest-ever disagreement with a quoted price, on the only carded number on the board with no model behind it. The book said ~53.5%, this project said 82%, and he threw 106 pitches — over the line by more than ten.** ✅ **Sam was shown the failing number and took it anyway. That is ledger rule 53 working exactly as designed, on both sides.**

⛔ **n = 6. STILL NOT A FINDING.** **Four wins at prices needing 61.5%–90.9% and two losses at flagged numbers is what the first six rows of a table like this look like.** ➡️ **Item 4 of the logging protocol is now the binding one: the real test is realised ROI against the break-even, not W/L — and at n=6 neither is measurable.**

## Logging protocol

1. **Log every flagged play, whether or not Sam bet it.** ⛔ **A log of only the flagged plays that were bet cannot measure the check** — same defect as rule 51's.
2. **Record the flagging number as a number** (the price, the break-even, the class rate), not as "failed the check."
3. **Score the CHECK, not the play.** The right question is whether the flag predicted the loss, not whether the play won.
4. **For price flags, the eventual test is realised ROI against the break-even**, not W/L. **Four wins at −300 and −1000 can still be a loss over a long run; W/L alone will never show that.**
5. ⛔ **Never re-decide a flag after seeing the result.**

---

# 🤖 TABLE M ACCUMULATORS — THE MACHINE CARD. ⛔ A SEPARATE POPULATION. NEVER MERGED WITH ANYTHING ABOVE THIS LINE.

`[created 2026-08-24, the first run on which a machine card existed to grade]`

🔴 **`card.py` writes `picks/<date>.json` unattended. Its rows are NOT carded plays: nobody chose them, and there are several times as many per slate.** ⛔ **They must never enter T15's Brier accumulator (whose specification says CARDED PLAYS), the rule-35 merged shadow ladder (whose `n` is carded arms), or the rule-50 / rule-51 tallies above.** ➡️ **Everything about the machine card lives under this heading and is counted here only.**

⚠️ **AND THE COMPARISON IS NOT AVAILABLE EITHER. An uncurated board will have a worse hit rate than a curated one; that is a different question, not a worse model.**

## 🔴 T15 — NOT RESTATED THIS RUN, AND THE REASON IS THE SPECIFICATION

**No TABLE A play was carded on 8/23, so the carded denominator did not move.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Adding TABLE M's 32 rows would take it past 60 in one night and would be a silent re-specification of a pre-registered test. It is not done.**

## 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING, AND THAT IS DELIBERATE

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

⛔ **The 8/23 machine card carries a full Hard Rock alt ladder per pitcher and 17 distinct starts — enough to move T11 from 25 to 42 in a single night.** 🔴 **IT IS NOT MERGED, AND THE REASON IS WRITTEN DOWN SO THE NEXT RUN DOES NOT DO IT ABSENT-MINDEDLY:** T11's `n` is **carded arms** — arms a session selected — and the machine board is every qualifying starter on the slate. **Merging them would change the population under a live pass criterion, which is the specification shopping this register exists to prevent.** ➡️ **If a machine shadow ladder is wanted, PRE-REGISTER IT as its own entry in `claude/owed-tests.md`, with its own `n` and its own bar, in an interactive session.** ⛔ **Do not merge first and register afterwards.**

## 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 8/23. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**`card.py` prints a matched class and a head-to-head figure on EVERY row, not only where they contradict.** ⛔ **That is not rule 50 firing — rule 50 is a TIEBREAKER triggered by a contradiction — so these observations are logged here, separately, and the hand-carded rule-50 accumulator above is untouched at 4/9.**

**Scoring convention, fixed here before it is used: the matched class ARGUED FOR the play when its all-starts rate is ≥50%, and AGAINST below 50%. The head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **32** | **15/32** | 🔴 **worse than a coin flip on this slate** |
| **Head-to-head** (prior meetings) | **14** | **4/14** | 🔴 **and it is the ONLY thing on the page pointing hard in one direction** |
| **Head-to-head, NO CALL** | **18** | — | ⛔ **n=0 rows, logged and in no tally** (14 + 18 = 32 ✅) |

### 🔴 FIVE ROWS WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED

| play | class (all) | head-to-head | result | which was right |
|---|---|---|---|---|
| Janson Junk u16.5 outs vs WSH | 19/30 (63.3%) FOR | 0/1 AGAINST | **W** (14 outs) | ✅ **CLASS** |
| Tyler Mahle o4.5 K vs MIL | 40/72 (55.6%) FOR | 0/1 AGAINST | **L** (4 K) | ✅ **H2H** |
| Carlos Rodón o5.5 K vs TOR | 26/64 (40.6%) AGAINST | 1/1 FOR | **L** (2 K) | ✅ **CLASS** |
| Andrew Abbott o16.5 outs vs AZ | 20/40 (**exactly 50.0%**) | 0/1 AGAINST | **W** (18 outs) | ⚠️ **CLASS — but on a 50.0% class, which argued NOTHING** |
| Cristopher Sánchez u6.5 K vs STL | 26/39 (66.7%) FOR | 0/1 AGAINST | **L** (7 K) | ✅ **H2H** |

⚠️ **Strip the Abbott row, whose class sits exactly on the boundary and is therefore uninformative by construction, and the conflicts split 2–2.** ⛔ **FOUR ROWS. This says nothing, and it must not be quoted beside the hand-carded "the class has beaten the head-to-head 3/3" note above — different population, different trigger, and that note is about a tiebreaker being INVOKED, not about a column being PRINTED.**

⚠️ 🔴 **THIRTEEN of the fourteen head-to-head samples are n=1 and one is n=2.** ⛔ **A 4/14 off samples of one is a coin flip landing badly, not a finding about head-to-head.**

## 🆕 🔴 A PRE-PUBLISH CHECK 36 DEFECT IN THE MACHINE CARD — REPORTED, NOT FIXED

`[found 2026-08-24 by the grading run]`

🔴 **`card.py` prints rule 50's head-to-head on every row and NEVER prints rule 51's GAP IN DAYS.** **Nine of the 32 rows carry at least one prior meeting with that opponent and not one of them states how long ago it was**, so **pre-publish check 36 cannot pass on a machine card by construction.**

⚠️ **This is the SAME failure the 8/22 hand-built card made, now baked into code: reading the game log for the head-to-head is not the same as running the ≤30-day rematch check.**

⛔ **NOTHING IS RE-GRADED AND THE RULE 51 ACCUMULATOR ABOVE GAINS NO ROWS — the gap in days is not recoverable from the card, and rule 51 is EXPLORATORY with its pre-registered specification FAILED and closed.** ⛔ **A grading run does not edit `card.py`, and a headless session can neither test nor push a change.** ➡️ **Interactive fix: emit the gap in days on every row that has a prior meeting.**

## 🟡 THE `carried` SHADOW — TABLE M's OWN T21/T22 LADDER

**`carried` is the blend after the T21/T22 flags, both PRE-REGISTERED AND NOT ADOPTED (ledger rule 57).** ⛔ **It enters NO denominator here either.**

**It differed from `blend` on 3 of the 32 rows on 8/23, all three from the `T22` shuttled-starter warning:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Shane Drohan o14.5 outs | 76.2% | 61.8% | **W** | **blend** |
| Shane Drohan o4.5 K | 64.2% | 49.8% | **W** | **blend** |
| Daniel Lynch IV u11.5 outs | 68.8% | 54.4% | **L** | **carried** |

| | Brier over all 32 rows | Brier over the 3 rows that differ |
|---|---|---|
| `blend` | **.2752** | **.2194** |
| `carried` | **.2763** | **.2313** |
| Verdict | 🔴 **`carried` is WORSE by .0011** | 🔴 **`carried` is WORSE** |

⛔ **THREE ROWS, TWO OF THEM THE SAME PITCHER ON THE SAME NIGHT. T22 is neither adopted nor rejected by this and nothing is re-specified.** ➡️ **Accumulate. The whole point of logging `carried` is that at the September re-fit this is a measurement instead of an argument.**

**Progress: TABLE M — 1 slate, 32 plays, 8 pairs.** ⚠️ 🔴 **SUPERSEDED 2026-08-25 by the 8/24 block immediately below — the counter now reads 2 slates / 55 pitcher plays / 16 pairs, plus a separate hitter denominator. KEPT, NOT DELETED: this is the state of the accumulator after one slate.**

---

## 🆕 2026-08-24 — THE SECOND MACHINE SLATE, AND THE CARD CHANGED POPULATION UNDER THE ACCUMULATOR

`[graded 2026-08-25]` 🔴 **`picks/2026-08-24.json` IS 50 PLAYS — 23 PITCHER AND 27 HITTER — AGAINST 8/23's 32 PITCHER-ONLY.** **`50 = 23 + 27` ✅.**

⛔ **THE HITTER ROWS ARE NOT IN TABLE M AND ARE NOT IN ANY ACCUMULATOR ON THIS PAGE.** **They carry NO `blend`, NO `band` and NO model — `basis: "MARKET + DESCRIPTIVE — no model, no confidence rating (rule 55)"` — and `claude/owed-tests.md` records FOUR pre-registered hitter specifications (T27, T28, T29, T30) that all FAILED to beat the smoothed season rate those rows carry.** ➡️ **A row with no carded estimate cannot be bucketed against one.** ✅ **They are graded into their own denominator, TABLE M-H, in `claude/pick-ledger.md` — 19/26 — and nothing on this page counts them.**

⚠️ 🔴 **THE SPLIT IS THE GRADING RUN'S JUDGEMENT AND IS FLAGGED AS SUCH RATHER THAN PRESENTED AS SETTLED PRACTICE. An interactive session should ratify or overrule it.** ⛔ **What is not a judgement call: the two populations must stay separably logged from today, because a merged rate would measure neither.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER, AND THE REASON IS STILL THE SPECIFICATION

**No TABLE A play was carded on 8/23 or on 8/24, so the CARDED denominator has not moved for two consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Adding the machine card's 23 pitcher rows would take the counter past 50 without a single carded play being carded, and that is a silent re-specification of a pre-registered test. It is not done.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

⛔ **The 8/24 machine card carries a full Hard Rock alt ladder per pitcher across 14 distinct starts — enough to move T11 from 25 to 39 in one night, and past the bar of 40 with one more machine slate.** 🔴 **IT IS NOT MERGED, for the same reason as 8/23: T11's `n` is CARDED arms, and the machine board is every qualifying starter.** ➡️ **A machine shadow ladder must be PRE-REGISTERED as its own entry in `claude/owed-tests.md`, with its own `n` and its own bar, in an interactive session.** ⛔ **Do not merge first and register afterwards — and note that the temptation is now concrete rather than hypothetical, because two machine slates would clear T11's bar outright.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 8/24. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 block, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **23** | **16/23** | ✅ **better than a coin flip on this slate, unlike 8/23's 15/32** |
| **Head-to-head** (prior meetings) | **9** | **4/9** | ⚠️ **and every single sample is n=1** |
| **Head-to-head, NO CALL** | **14** | — | ⛔ **n=0 rows, logged and in no tally** (9 + 14 = 23 ✅) |

**Running across the two machine slates, reported as a sum of two enumerated tallies and NOT as a finding: matched class 31/55, head-to-head 8/23, NO CALL 32.** ⛔ **`23 + 32 = 55` ✅.**

#### 🔴 FIVE ROWS WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED — AND THE CLASS TOOK FOUR

| play | class (all) | head-to-head | result | which was right |
|---|---|---|---|---|
| Parker Messick u6.5 K vs LAA | 41/68 (60.3%) FOR | 0/1 AGAINST | **W** | ✅ **CLASS** |
| Robbie Ray u5.5 K vs PIT | 47/75 (62.7%) FOR | 0/1 AGAINST | **W** | ✅ **CLASS** |
| Kevin Gausman o4.5 K vs AZ | 34/66 (51.5%) FOR | 0/1 AGAINST | **W** | ✅ **CLASS** |
| Robbie Ray u16.5 outs vs PIT | 23/38 (60.5%) FOR | 0/1 AGAINST | **W** | ✅ **CLASS** |
| Zebby Matthews u17.5 outs vs ATH | 20/34 (58.8%) FOR | 0/1 AGAINST | **L** | ✅ **H2H** |

⚠️ 🔴 **ALL FIVE CONFLICTS HAVE THE SAME SHAPE — a class in the 51–63% range against a head-to-head of 0-for-1 — SO THIS IS FIVE ROWS TESTING ONE PATTERN, NOT FIVE INDEPENDENT TESTS.** ⛔ **And a 0/1 head-to-head "arguing against" is a sample of one. Four-one to the class says nothing.** ⚠️ **It does point the same way as the hand-carded note that the class has beaten the head-to-head 3/3 when they flatly disagreed — but that note is about a TIEBREAKER being INVOKED and this is about a COLUMN being PRINTED on every row.** ⛔ **Different population, different trigger. Do not add them together.**

### 🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — SECOND CONSECUTIVE RUN

`[re-checked 2026-08-25]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** **Nine of the 23 pitcher rows carry at least one prior meeting and not one of them states how long ago it was**, so **pre-publish check 36 still cannot pass on a machine card by construction.**

⛔ **REPORTED, NOT FIXED, AGAIN — a grading run does not touch the code and a headless session can neither test nor push a change.** ⛔ **The rule 51 accumulator above gains NO rows: the gap in days is not recoverable from the card, and rule 51 is EXPLORATORY with its pre-registered specification FAILED and closed.** ➡️ **Interactive fix, unchanged: emit the gap in days on every row that has a prior meeting.**

### 🟡 THE `carried` SHADOW — 8/24. ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 2 of the 23 rows — BOTH THE SAME PITCHER, both from the `T22` shuttled-starter warning (`1 relief appearance this season`):**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Robbie Ray u5.5 K | 61.2% | 46.8% | **W** | **blend** |
| Robbie Ray u16.5 outs | 54.3% | 39.9% | **W** | **blend** |

| | Brier over all 23 rows | Brier over the 2 rows that differ |
|---|---|---|
| `blend` | **.2099** | **.1797** |
| `carried` | **.2223** | **.3221** |
| Verdict | 🔴 **`carried` is WORSE by .0124** | 🔴 **`carried` is WORSE** |

⛔ **TWO ROWS, ONE PITCHER, ONE NIGHT.** ⚠️ **Across both machine slates `carried` has now been worse on both, over FIVE differing rows total (three on 8/23, two on 8/24) — and on each night the differing rows were concentrated in ONE OR TWO pitchers.** ⛔ **T22 is neither adopted nor rejected by this and nothing is re-specified. Five correlated rows is not a measurement; it is the beginning of one.**

### ⚠️ ONE MACHINE ROW COULD NOT BE GRADED, AND IT IS LOGGED HERE BECAUSE IT IS A GRADING-RULE GAP

🔴 **A TABLE M-H row — Ke'Bryan Hayes u0.5 RBIs — WAS NOT IN THE LINEUP, and the standing rule "W OR L — THERE IS NO VOID" does not reach it.** **That rule was written for pitcher props, where a scratch is a pitcher who did not throw. A bench bat who did not bat is a bet every book voids and returns.** ✅ **Recorded UNGRADED, in no tally, with the row saying so.** ➡️ **If hitter rows keep being carded, the grading-mechanics section in `claude/pick-ledger.md` needs a hitter clause. ⛔ A grading run is not the place to write one — flagged for an interactive session.**

~~**Progress: TABLE M — 2 slates, 55 pitcher plays, 16 pairs. TABLE M-H — 1 slate, 26 graded hitter rows.**~~ ⚠️ 🔴 **SUPERSEDED 2026-08-26 by the 8/25 block immediately below — the counter now reads TABLE M 3 slates / 80 pitcher plays / 24 pairs, and TABLE M-H 2 slates / 51 graded hitter rows. KEPT, NOT DELETED: this is the state of the accumulator after two slates.**
---

## 🆕 2026-08-26 — THE THIRD MACHINE SLATE (2026-08-25), AND THE FIRST ON WHICH `carried` BEAT THE BLEND

`[graded 2026-08-26]` 🔴 **`picks/2026-08-25.json` IS 50 PLAYS — 25 PITCHER AND 25 HITTER.** **`50 = 25 + 25` ✅.**

⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in `claude/pick-ledger.md` — 14/25, a gap of −26.3 against their mean stated rate — and nothing here counts them.** ⚠️ **That gap is the largest this project has recorded on any table and it is recorded in the ledger with its caveats; it changes nothing on this page.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **THIRD CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23, 8/24 or 8/25, so the CARDED denominator has not moved for three consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Folding in the machine card's 25 pitcher rows would take the counter past 55 without a single carded play, which is a silent re-specification of a pre-registered test. It is not done.**

⚠️ 🔴 **AND THE THREE-RUN DROUGHT IS ITSELF WORTH SAYING OUT LOUD: T15's `n ≥ 100` leg can now only advance when a human sits down and builds a card, and no card has been hand-built since 8/22.** ⛔ **That is an observation, not a licence to widen the denominator.** ➡️ **If the project intends T15 to ever close, either an interactive card has to be built or a MACHINE-population version has to be pre-registered as its own entry with its own bar. ⛔ A grading run may do neither.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

⛔ **The 8/25 machine card again carries a full Hard Rock alt ladder per pitcher across 18 distinct starts.** 🔴 **IT IS NOT MERGED, for the third time and for the same reason: T11's `n` is CARDED arms and the machine board is every qualifying starter.** ➡️ **A machine shadow ladder must be PRE-REGISTERED as its own entry in `claude/owed-tests.md`, in an interactive session.** ⛔ **Do not merge first and register afterwards.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 8/25. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 and 8/24 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **23** *(2 rows excluded — see below)* | **11/23** | 🔴 **a coin flip, between 8/23's 15/32 and 8/24's 16/23** |
| **Head-to-head** (prior meetings) | **10** | **8/10** | ⚠️ **and EVERY SINGLE SAMPLE IS n=1** |
| **Head-to-head, NO CALL** | **15** | — | ⛔ **n=0 rows, logged and in no tally** (10 + 15 = 25 ✅) |

⚠️ 🔴 **TWO ROWS ARE EXCLUDED FROM THE CLASS TALLY AND THEY ARE NAMED RATHER THAN QUIETLY DROPPED: Seth Lugo o3.5 K (class 26/52 = 50.0%) and Jacob deGrom u6.5 K (class 11/22 = 50.0%).** **A class sitting EXACTLY on the boundary argues nothing by construction.** ⛔ 🆕 **AND THE CONVENTION HAS NOT BEEN APPLIED CONSISTENTLY ACROSS THE THREE BLOCKS — 8/23 carried an identical boundary row (Andrew Abbott, 20/40 = 50.0%) INSIDE its 32-row denominator while flagging it in the conflict table.** ➡️ **So the three class tallies are NOT summable as published. They are reported as three separate enumerated tallies and NOT added together, and the inconsistency is flagged for an interactive session to settle rather than harmonised by a grading run after the fact.**

#### 🔴 THREE ROWS WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED — AND THE HEAD-TO-HEAD TOOK ALL THREE

| play | class (all) | head-to-head | result | which was right |
|---|---|---|---|---|
| Paul Skenes u16.5 outs vs SD | 18/33 (54.5%) FOR | 0/1 AGAINST | **L** | ✅ **H2H** |
| Walbert Ureña o4.5 K vs CLE | 38/72 (52.8%) FOR | 0/1 AGAINST | **L** | ✅ **H2H** |
| Anthony Kay u16.5 outs vs TEX | 15/39 (38.5%) AGAINST | 1/1 FOR | **W** | ✅ **H2H** |

⚠️ 🔴 **THREE ROWS, EVERY HEAD-TO-HEAD SAMPLE A SINGLE START, AND A CLEAN SWEEP. ⛔ THAT IS WHAT A COIN LANDING THE SAME WAY THREE TIMES LOOKS LIKE.** **On 8/24 the class took four of five conflicts and on 8/23 they split 2–2; today the head-to-head takes three of three.** ⛔ **Do not read a direction into this and do not set it beside the hand-carded note that the class has beaten the head-to-head 3/3 when they FLATLY DISAGREED — that note is about a TIEBREAKER being INVOKED and this is about a COLUMN being PRINTED on every row.** ⛔ **Different population, different trigger. Do not add them together.**

### 🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **THIRD CONSECUTIVE RUN**

`[re-checked 2026-08-26]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** **Ten of the 25 pitcher rows carry at least one prior meeting and not one states how long ago**, so **pre-publish check 36 still cannot pass on a machine card by construction.** ✅ **Verified mechanically this run: the string `days` appears ZERO times anywhere in `picks/2026-08-25.json`.**

⛔ **REPORTED, NOT FIXED, AGAIN — a grading run does not touch the code and a headless session can neither test nor push a change.** ⛔ **The rule 51 accumulator above gains NO rows.** ➡️ **Interactive fix, unchanged: emit the gap in days on every row that has a prior meeting.**

### 🟡 THE `carried` SHADOW — 8/25. 🔴 **IT BEAT THE BLEND FOR THE FIRST TIME.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 8 of the 25 rows — EVERY ONE the `T22` shuttled-starter warning, across SIX pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Chris Bassitt u4.5 K | 76.3% | 61.9% | **L** | **carried** |
| Chris Bassitt u16.5 outs | 67.0% | 52.6% | **L** | **carried** |
| Chris Bassitt u3.5 K | 62.5% | 48.1% | **L** | **carried** |
| Brandon Pfaadt u4.5 K | 62.7% | 48.3% | **W** | **blend** |
| Will Warren o4.5 K | 60.5% | 46.1% | **L** | **carried** |
| Walbert Ureña o4.5 K | 59.9% | 45.5% | **L** | **carried** |
| Adrian Houser o3.5 K | 60.4% | 46.0% | **L** | **carried** |
| Anthony Kay u16.5 outs | 59.4% | 45.0% | **W** | **blend** |

| | Brier over all 25 rows | Brier over the 8 rows that differ |
|---|---|---|
| `blend` | **.2654** | **.3519** |
| `carried` | 🔴 **.2365** | 🔴 **.2615** |
| Verdict | 🔴 **`carried` is BETTER by .0289** | 🔴 **`carried` is BETTER by .0904** |

⛔ **EIGHT ROWS FROM SIX PITCHERS, THREE OF THEM ONE MAN ON ONE NIGHT. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **AND SAY WHY IT WON, BECAUSE THE MECHANISM MATTERS MORE THAN THE NUMBER: six of the eight rows LOST, and `carried` is always the LOWER number.** **It wins this Brier for being pessimistic on a bad set of rows — the identical day-tracking artifact this page condemns the \"closer\" column for, and the identical mechanism that moved T15's argmin to a boundary on 8/22.** ⛔ **A proper scoring rule does not immunise a one-slate result against it.**

➡️ **RUNNING ACROSS THE THREE MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 13 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25 — and the verdict is WORSE, WORSE, BETTER.** ⚠️ **On every one of the three nights the differing rows were concentrated in one or two pitchers. Thirteen correlated rows is not a measurement; it is the beginning of one.**

~~**Progress: TABLE M — 3 slates, 80 pitcher plays, 24 pairs. TABLE M-H — 2 slates, 51 graded hitter rows.**~~ ⚠️ 🔴 **SUPERSEDED 2026-08-27 by the 8/26 block immediately below — the counter now reads TABLE M 4 slates / 103 GRADED pitcher plays / 32 pairs, and TABLE M-H 3 slates / 76 graded hitter rows. KEPT, NOT DELETED: this is the state of the accumulator after three slates.** ⚠️ **The 8/26 pitcher count is 23 of 25 carded — two rows were UNGRADEABLE because the named starter did not pitch, and they are in no denominator.**

---

## 🆕 2026-08-27 — THE FOURTH MACHINE SLATE (2026-08-26), A SCRATCHED STARTER THE GRADING RULES DO NOT REACH, AND A COLLECTOR THAT STOPPED COMMITTING

`[graded 2026-08-27]` 🔴 **`picks/2026-08-26.json` IS 50 PLAYS — 25 PITCHER AND 25 HITTER.** **`50 = 25 + 25` ✅.**

🔴 **ONLY 23 OF THE 25 PITCHER ROWS ARE GRADED. Landen Roupp was carded twice and DID NOT PITCH.** ✅ **Both rows are UNGRADED and in no tally here or in `claude/pick-ledger.md`; the full reasoning, the historical control that established the absence, and the alternative reading that would have made both unders WIN, are in the ledger's dated 8/26 block.** ⛔ **A grading run does not settle a grading-mechanics question the standing rule does not reach.**

⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24 and 8/25: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in `claude/pick-ledger.md` — 14/25, a gap of −25.1 against their mean stated rate — and nothing here counts them.** ⚠️ 🔴 **THAT IS THE SECOND CONSECUTIVE ~25-POINT GAP ON THAT TABLE (−26.3 then −25.1, after −7.2), which is recorded in the ledger with its caveats and changes nothing on this page.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **FOURTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23, 8/24, 8/25 or 8/26, so the CARDED denominator has not moved for four consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Folding in the machine card's 23 graded pitcher rows would take the counter past 54 without a single carded play, which is a silent re-specification of a pre-registered test. It is not done.**

⚠️ 🔴 **AND THE DROUGHT IS NOW FOUR SLATES LONG, WHICH IS WORTH SAYING AGAIN RATHER THAN LETTING IT BECOME BACKGROUND: T15's `n ≥ 100` leg can advance ONLY when a human sits down and builds a card, and none has been hand-built since 8/22 — five days.** ⛔ **An observation, not a licence to widen the denominator.** ➡️ **Closing T15 needs either an interactive card or a MACHINE-population version pre-registered as its own entry with its own bar. ⛔ A grading run may create neither.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

⛔ **The 8/26 machine card again carries Hard Rock alt ladders — 91 rungs across the carded rows.** 🔴 **IT IS NOT MERGED, for the fourth time and for the same reason: T11's `n` is CARDED arms and the machine board is every qualifying starter.** ➡️ **A machine shadow ladder must be PRE-REGISTERED as its own entry in `claude/owed-tests.md`, in an interactive session.** ⛔ **Do not merge first and register afterwards.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 8/26. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23, 8/24 and 8/25 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **23** *(no row sits exactly on 50.0%, so nothing is excluded this slate)* | **13/23** | ⚠️ **a coin flip again — 15/32, 16/23, 11/23, 13/23 across four slates** |
| **Head-to-head** (prior meetings) | 🔴 **3** | **2/3** | ⛔ **THREE ROWS. Every sample n=1.** |
| **Head-to-head, NO CALL** | **20** | — | ⛔ **n=0 rows, logged and in no tally** (3 + 20 = 23 ✅) |

⚠️ 🔴 **TWENTY OF THE TWENTY-THREE GRADED ROWS HAVE NO HEAD-TO-HEAD AT ALL, WHICH IS THE HIGHEST NO-CALL SHARE OF ANY MACHINE SLATE (18/32, 14/23, 15/25, now 20/23).** ⛔ **A 2/3 off three samples of one start each says nothing whatever, and it is printed only so the tally is complete.**

⛔ 🆕 **THE BOUNDARY-ROW CONVENTION INCONSISTENCY FLAGGED ON 8/25 IS UNCHANGED AND UNRESOLVED — 8/23 kept its 50.0% row inside its denominator while 8/25 excluded two.** ➡️ **The four class tallies are therefore still NOT summable as published and are still reported as four separate enumerated tallies. An interactive session should settle the convention; a grading run does not re-cut a published tally after the fact.**

#### 🔴 ONE ROW WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED

| play | class (all) | head-to-head | result | which was right |
|---|---|---|---|---|
| Joey Cantillo u15.5 outs vs LAA | 11/17 (64.7%) FOR | 0/1 AGAINST | **L** (18 outs) | ✅ **H2H** |

⚠️ 🔴 **ONE ROW. ⛔ IT IS NOT A DATA POINT ABOUT ANYTHING.** **Across the four machine slates the conflicts run 2–2, then four-of-five to the CLASS, then three-of-three to the H2H, now one-of-one to the H2H.** ⛔ **Do not read a direction into that and do not set it beside the hand-carded note that the class has beaten the head-to-head 3/3 when they FLATLY DISAGREED — that note is about a TIEBREAKER being INVOKED and this is about a COLUMN being PRINTED on every row.** ⛔ **Different population, different trigger. Do not add them together.**

### 🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **FOURTH CONSECUTIVE RUN**

`[re-checked 2026-08-27]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** **Five of the 25 pitcher rows carry at least one prior meeting and not one states how long ago**, so **pre-publish check 36 still cannot pass on a machine card by construction.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-08-26.json`.**

⛔ **REPORTED, NOT FIXED, AGAIN — a grading run does not touch the code and a headless session can neither test nor push a change.** ⛔ **The rule 51 accumulator above gains NO rows.** ➡️ **Interactive fix, unchanged: emit the gap in days on every row that has a prior meeting.**

### 🟡 THE `carried` SHADOW — 8/26. 🔴 **IT BEAT THE BLEND FOR A SECOND CONSECUTIVE SLATE — BY THE SAME MECHANISM.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 8 of the 23 graded rows — EVERY ONE the `T22` shuttled-starter warning, across FIVE pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Tanner Gordon u16.5 outs | 89.5% | 64.1% | **L** | **carried** |
| Randy Dobnak o2.5 K | 77.8% | 63.4% | **W** | **blend** |
| Ryan Gusto u14.5 outs | 75.9% | 61.5% | **L** | **carried** |
| J.T. Ginn o3.5 K | 75.0% | 60.6% | **L** | **carried** |
| Randy Dobnak u16.5 outs | 66.1% | 51.7% | **L** | **carried** |
| Randy Vásquez u3.5 K | 61.1% | 46.7% | **W** | **blend** |
| Ryan Gusto o3.5 K | 60.2% | 45.8% | **L** | **carried** |
| Tanner Gordon u3.5 K | 59.9% | 45.5% | **L** | **carried** |

| | Brier over all 23 graded rows | Brier over the 8 rows that differ |
|---|---|---|
| `blend` | **.3123** | **.4123** |
| `carried` | 🔴 **.2671** | 🔴 **.2823** |
| Verdict | 🔴 **`carried` is BETTER by .0452** | 🔴 **`carried` is BETTER by .1300** |

⛔ **EIGHT ROWS FROM FIVE PITCHERS, TWO OF THEM ONE MAN ON ONE NIGHT. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **AND THE MECHANISM IS IDENTICAL TO 8/25's, WHICH IS THE POINT: six of the eight rows LOST, and `carried` is ALWAYS the LOWER number.** **It wins this Brier for being pessimistic on a bad set of rows — the same day-tracking artifact this page condemns the "closer" column for, on the same flag, two nights running.** ⛔ **TWO CONSECUTIVE WINS BY THE SAME MECHANISM IS NOT TWO PIECES OF EVIDENCE; IT IS THE SAME PIECE TWICE.** ⚠️ **On a night when the T22-flagged rows happen to WIN, `carried` will lose by exactly as much — that is what 8/23 and 8/24 were.**

➡️ **RUNNING ACROSS THE FOUR MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 21 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26 — and the verdict is WORSE, WORSE, BETTER, BETTER.** ⚠️ **On every one of the four nights the differing rows were concentrated in one or two pitchers. Twenty-one correlated rows is not a measurement; it is still the beginning of one.**

### ⚠️ 🆕 AND THE GRADING RUN COULD NOT USE THE REPO ROUTE AT ALL, WHICH IS LOGGED HERE BECAUSE IT AFFECTS EVERY FUTURE PASS

🔴 **THE COLLECTOR HAS NOT COMMITTED SINCE `2026-08-26T19:30:22Z`.** **`data/2026-08-26/results/` does not exist and `data/latest/record.json` names the gap itself.** ➡️ **The whole slate was graded from statsapi through `WebFetch`, controlled two independent ways on 19/19 pitchers and 21/21 hitters with zero domain violations — detail in `claude/pick-ledger.md`.** ⛔ **REPORTED, NOT FIXED: a headless session cannot see the Actions run history, re-run a workflow or push. AN INTERACTIVE SESSION MUST CHECK IT.** ⚠️ **The convenience route this project adopted on 8/24 is exactly that — a convenience — and this is the first run on which it was unavailable. The domain check and the season-total control are what made its absence survivable, and that is the argument for never letting them lapse.**

~~**Progress: TABLE M — 4 slates, 103 graded pitcher plays, 32 pairs. TABLE M-H — 3 slates, 76 graded hitter rows.**~~ ⚠️ 🔴 **SUPERSEDED 2026-08-28 by the 8/27 block immediately below — the counter now reads TABLE M 5 slates / 104 GRADED pitcher plays / 32 pairs, and TABLE M-H 4 slates / 111 graded hitter rows. KEPT, NOT DELETED: this is the state of the accumulator after four slates.** ⚠️ **The 8/27 slate adds ONE pitcher row and ZERO pairs, and the reason is in the ledger: the card file was overwritten after the slate began.**

---

## 🆕 2026-08-28 — THE FIFTH MACHINE SLATE (2026-08-27), AND THERE IS ALMOST NOTHING OF IT: THE CARD FILE WAS OVERWRITTEN AFTER THE SLATE BEGAN

`[graded 2026-08-28]` 🔴🔴 **`picks/2026-08-27.json` AS COMMITTED IS 38 PLAYS — 1 PITCHER AND 37 HITTER — ACROSS ONE GAME.** **`38 = 1 + 37` ✅.**

🔴 **IT IS NOT A ONE-GAME SLATE. IT IS A DESTROYED CARD.** **The file was written three times and each write replaced it: `4044f600` at `2026-08-27T17:08:34Z` held 50 plays across 6 games (12 pitcher, 8 pairs); the surviving `5bd789ce` was generated `2026-08-28T00:59:58Z` — 8:59pm ET — by which time six of the seven games had started and `card.py`'s own guard dropped them.** ✅ **The full provenance, the commit hashes, the twelve lost pitcher rows and the reasoning for grading the surviving file (the literal rule AND reversibility) are in `claude/pick-ledger.md`'s dated 8/27 block.** ⛔ **A grading run does not touch the code and cannot fix the overwrite; it is REPORTED there.**

⛔ **THE 37 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24, 8/25 and 8/26: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in `claude/pick-ledger.md` — 18/35, with 2 rows ungraded because Nolan Arenado did not play — and nothing here counts them.** ⚠️ 🔴 **THE ~25-POINT M-H GAP DID NOT RECUR (+0.5 this slate, after −7.2, −26.3, −25.1) AND THAT IS NOT THE GAP CLOSING: this slate's mean stated rate is 50.9 against 80.3, 82.3 and 81.1, because the collapsed board filled its slots with long-shot overs.** ⛔ **Different population. The four gaps are not comparable and are not averaged.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **FIFTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23, 8/24, 8/25, 8/26 or 8/27, so the CARDED denominator has not moved for five consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Folding in the machine card's rows — one, this time — would still be a silent re-specification of a pre-registered test, and the smallness of the number is not a licence. It is not done.**

⚠️ 🔴 **THE DROUGHT IS NOW SIX DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.** ➡️ **Closing T15 needs either an interactive card or a MACHINE-population version pre-registered as its own entry with its own bar. ⛔ A grading run may create neither.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 8/27 card carries ONE Hard Rock alt ladder — Landen Roupp's, seven rungs from 1.5 to 8.5.** 🔴 **IT IS NOT MERGED, for the fifth time and for the same reason: T11's `n` is CARDED arms and the machine board is every qualifying starter.** ➡️ **A machine shadow ladder must be PRE-REGISTERED as its own entry in `claude/owed-tests.md`, in an interactive session.** ⛔ **Do not merge first and register afterwards.**

⚠️ **The start is NAMED anyway, per the accumulation protocol, so that a future registered pass can deduplicate against it without re-deriving anything: Landen Roupp 2026-08-27 (3 K).** ⛔ **Naming it is not merging it, and it is in no bucket table.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 8/27. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23, 8/24, 8/25 and 8/26 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | 🔴 **1** | **0/1** | ⛔ **ONE ROW. It is not a data point about anything.** |
| **Head-to-head** (prior meetings) | 🔴 **1** | **1/1** | ⛔ **ONE ROW, and n=3.** |
| **Head-to-head, NO CALL** | **0** | — | ⛔ **no n=0 rows this slate** (1 + 0 = 1 ✅) |

⛔ 🔴 **THE BOUNDARY-ROW CONVENTION INCONSISTENCY FLAGGED ON 8/25 IS STILL UNCHANGED AND UNRESOLVED — 8/23 kept its 50.0% row inside its denominator while 8/25 excluded two.** ➡️ **The five class tallies are therefore still NOT summable as published and are still reported as five separate enumerated tallies. An interactive session should settle the convention; a grading run does not re-cut a published tally after the fact.** ⚠️ **The 8/27 row sits at 51.4%, close to but not on the boundary, so the convention did not have to be applied here.**

#### 🔴 THE ONE ROW WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED — AND IT IS THE WHOLE SLATE

| play | class (all) | head-to-head | result | which was right |
|---|---|---|---|---|
| Landen Roupp o4.5 K vs AZ | 38/74 (51.4%) FOR | 1/3 AGAINST (2026-05-19 3 K · 2026-05-25 7 K · 2026-06-30 4 K) | **L** (3 K) | ✅ **H2H** |

⚠️ 🔴 **ONE ROW. ⛔ IT IS NOT A DATA POINT ABOUT ANYTHING.** **Across the five machine slates the conflicts run 2–2, then four-of-five to the CLASS, then three-of-three to the H2H, then one-of-one to the H2H, now one-of-one to the H2H again.** ⛔ **Do not read a direction into that and do not set it beside the hand-carded note that the class has beaten the head-to-head 3/3 when they FLATLY DISAGREED — that note is about a TIEBREAKER being INVOKED and this is about a COLUMN being PRINTED on every row.** ⛔ **Different population, different trigger. Do not add them together.**

⚠️ **Worth one line because it is unusually informative for a single row: this head-to-head is n=3 rather than the n=1 that has dominated every prior machine slate, and the card printed it as `3 start(s) vs AZ -- cleared 1/3`.** ✅ **The three meetings were re-derived from the repo's own pre-slate log and reproduce exactly.**

### 🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **FIFTH CONSECUTIVE RUN** — ⚠️ **BUT IT COST NOTHING THIS SLATE, AND SAYING SO IS PART OF SCORING THE CHECK HONESTLY**

`[re-checked 2026-08-28]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-08-27.json`.**

✅ 🆕 **AND THE GAP WAS COMPUTED HERE INSTEAD, WHICH NO PRIOR RUN COULD DO BECAUSE THE CARD CARRIED TOO MANY ROWS: Roupp's most recent prior meeting with Arizona is 2026-06-30 — FIFTY-EIGHT DAYS — comfortably outside rule 51's 30-day window.** ➡️ **So no rule-51 instance was owed on this slate and the accumulator below correctly gains NO rows.** ⛔ **That is not the defect being fixed; it is the defect not biting. It is still REPORTED, NOT FIXED — a grading run does not touch the code and a headless session can neither test nor push a change.**

### 🟡 THE `carried` SHADOW — 8/27. 🔴 **IT DIFFERED ON ZERO ROWS.** ⛔ **STILL IN NO DENOMINATOR.**

**`carried` equals `blend` at 52.8 on the single row, so there is nothing to score.**

➡️ **RUNNING ACROSS THE FIVE MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 21 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27 — and the verdict is WORSE, WORSE, BETTER, BETTER, and NO CALL.** ⛔ **T22 is neither adopted nor rejected, and twenty-one correlated rows is still only the beginning of a measurement.**

### ⚠️ 🆕 A RUN-LEVEL FACT, LOGGED BECAUSE IT AFFECTS EVERY FUTURE PASS AND IT IS **NOT** YESTERDAY'S FACT

🔴 **THE COLLECTOR IS COMMITTING AGAIN — the last commit is `2026-08-28T07:16Z` — BUT ITS `results` MODE HAS NOT RUN SINCE `2026-08-27T16:39Z`.** **`data/2026-08-27/results/final.json.gz` exists and is a PRE-SLATE snapshot: `n_final: 0`, every game `Pre-Game` or `Scheduled`, `started: true` on ZERO pitchers across all seven games.** ✅ **`data/latest/record.json` names the gap itself, listing `2026-08-27` under `skipped` with the reason `"0/7 games final -- not settled"`.** ⛔ **So the repo grading route was unavailable for a SECOND consecutive run, for a DIFFERENT reason — yesterday the collector had stopped entirely; today it runs and the results pull specifically does not.** ✅ **The slate was graded from statsapi instead, controlled four independent ways with zero domain violations — detail in `claude/pick-ledger.md`.** ⛔ **REPORTED, NOT FIXED. AN INTERACTIVE SESSION MUST CHECK IT.**

✅ 🆕 **ONE GENUINELY NEW CONTROL IS RECORDED HERE BECAUSE IT GENERALISES BEYOND THIS SLATE: every `raw` string the card printed — all 37 hitter rows and the pitcher's 17/25 — was RECOMPUTED from the repo's own pre-slate logs plus `lineups.json.gz`, under `card.py`'s documented started-games filter, and reproduces 38/38 EXACTLY.** ➡️ **That checks the card's own evidence column against the data it claims to have read, which no prior grading run had done on the hitter half.** ⚠️ **It also explains a residual that would otherwise look like a defect: the card's denominators are smaller than the stored game logs because they count games the player STARTED, not games he appeared in.**

~~**Progress: TABLE M — 5 slates, 104 graded pitcher plays, 32 pairs. TABLE M-H — 4 slates, 111 graded hitter rows.**~~ ⚠️ 🔴 **SUPERSEDED 2026-08-29 by the 8/28 block immediately below — the counter now reads TABLE M 6 slates / 129 GRADED pitcher plays / 40 pairs, and TABLE M-H 5 slates / 134 graded hitter rows. KEPT, NOT DELETED: this is the state of the accumulator after five slates.**

---

## 🆕 2026-08-29 — THE SIXTH MACHINE SLATE (2026-08-28), THE FULL BOARD BACK, AND `carried` WORSE AGAIN BY THE SAME MECHANISM INVERTED

`[graded 2026-08-29]` 🔴 **`picks/2026-08-28.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 15 GAMES.** **`50 = 25 + 25` ✅.**

⚠️ 🔴 **THE FILE WAS WRITTEN SEVEN TIMES AND EACH WRITE REPLACED IT, EXACTLY AS ON 8/27 — BUT THIS TIME THE LAST WRITE WAS THE PRE-SLATE ONE AND THE BEST ONE.** **The six overnight writes held FIVE pitcher rows across EIGHT games; the surviving `069707d` at `2026-08-28T18:20:40Z` holds TWENTY-FIVE across FIFTEEN, four hours before first pitch.** ⛔ **The code is unchanged and so is the hazard. A mechanism that happens to help has not been fixed.** ✅ **Full provenance, commit by commit, is in `claude/pick-ledger.md`.**

⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24, 8/25, 8/26 and 8/27: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in `claude/pick-ledger.md` — 16/23, with 2 rows ungraded because Jakob Marsee and Amed Rosario did not play — and nothing here counts them.** ⚠️ 🔴 **THE ~25-POINT M-H GAP DID NOT RECUR ON A COMPARABLE BOARD (−11.3 this slate, against −7.2, −26.3, −25.1 and 8/27's non-comparable +0.5) — and four gaps of −7, −26, −25 and −11 are a scattered set, not a converging one.** ⛔ **They are not averaged and change nothing on this page.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **SIXTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23, 8/24, 8/25, 8/26, 8/27 or 8/28, so the CARDED denominator has not moved for six consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Folding in the machine card's 25 pitcher rows would take the counter past 56 without a single carded play, which is a silent re-specification of a pre-registered test. It is not done.**

⚠️ 🔴 **THE DROUGHT IS NOW SEVEN DAYS SINCE THE LAST HAND-BUILT CARD, AND AN INTERACTIVE SESSION DID SIT DOWN ON 8/28 EVENING WITHOUT BUILDING ONE** — it created four new project docs and logged neither a TABLE A nor a TABLE C. ⛔ **An observation, not a licence to widen the denominator.** ➡️ **Closing T15 needs either an interactive card or a MACHINE-population version pre-registered as its own entry with its own bar. ⛔ A grading run may create neither.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 8/28 card carries Hard Rock alt ladders across 17 distinct starts — enough to take T11 from 25 past its bar of 40 in one night.** 🔴 **IT IS NOT MERGED, for the sixth time and for the same reason: T11's `n` is CARDED arms and the machine board is every qualifying starter.** ➡️ **A machine shadow ladder must be PRE-REGISTERED as its own entry in `claude/owed-tests.md`, in an interactive session.** ⛔ **Do not merge first and register afterwards — and note that the temptation is now larger than it has ever been, because this one slate alone would clear the bar.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so that a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket table:**

**Patrick Sandoval 2026-08-28 (7 K) · Jacob Lopez 2026-08-28 (6 K) · Andrew Painter 2026-08-28 (6 K) · Emerson Hancock 2026-08-28 (1 K) · Drew Anderson 2026-08-28 (5 K) · Tarik Skubal 2026-08-28 (7 K) · Hunter Brown 2026-08-28 (10 K) · Michael Wacha 2026-08-28 (10 K) · Rhett Lowder 2026-08-28 (5 K) · Christian Scott 2026-08-28 (2 K) · Grant Holmes 2026-08-28 (3 K) · Reid Detmers 2026-08-28 (2 K) · Tomoyuki Sugano 2026-08-28 (4 K) · Dean Kremer 2026-08-28 (3 K) · Dylan Cease 2026-08-28 (8 K) · David Peterson 2026-08-28 (6 K) · Logan Henderson 2026-08-28 (7 K)** — **17 distinct (pitcher, date) pairs, none of which appears in the 8/20, 8/21 or 8/22 passes.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 8/28. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23, 8/24, 8/25, 8/26 and 8/27 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **25** *(no row sits exactly on 50.0%, so nothing is excluded this slate)* | **10/25** | 🔴 **worse than a coin flip — 15/32, 16/23, 11/23, 13/23, 0/1, now 10/25 across six slates** |
| **Head-to-head** (prior meetings) | **11** | **7/11** | ⚠️ **ten of the eleven are n=1 and one is n=2** |
| **Head-to-head, NO CALL** | **14** | — | ⛔ **n=0 rows, logged and in no tally** (11 + 14 = 25 ✅) |

⛔ 🔴 **THE BOUNDARY-ROW CONVENTION INCONSISTENCY FLAGGED ON 8/25 IS STILL UNCHANGED AND UNRESOLVED — 8/23 kept its 50.0% row inside its denominator while 8/25 excluded two.** ➡️ **The six class tallies are therefore still NOT summable as published and are still reported as six separate enumerated tallies. An interactive session should settle the convention; a grading run does not re-cut a published tally after the fact.** ⚠️ **The closest row this slate is Patrick Sandoval u5.5 K at 50.7%, near the boundary but not on it, so the convention did not have to be applied.**

#### 🔴 FOUR ROWS WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED — AND THEY SPLIT TWO–TWO

| play | class (all) | head-to-head | result | which was right |
|---|---|---|---|---|
| Rhett Lowder o3.5 K vs CHC | 43/64 (67.2%) FOR | 0/1 AGAINST | **W** (5 K) | ✅ **CLASS** |
| Dylan Cease o7.5 K vs SEA | 1/5 (20.0%) AGAINST | 1/1 FOR | **W** (8 K) | ✅ **H2H** |
| Dean Kremer o15.5 outs vs CWS | 11/30 (36.7%) AGAINST | 1/1 FOR | **L** (12 outs) | ✅ **CLASS** |
| David Peterson u16.5 outs vs CIN | 16/44 (36.4%) AGAINST | 1/1 FOR | **W** (15 outs) | ✅ **H2H** |

⚠️ 🔴 **FOUR ROWS, EVERY HEAD-TO-HEAD SAMPLE A SINGLE START, AND A TWO–TWO SPLIT.** **Across the six machine slates the conflicts run 2–2, four-of-five to the CLASS, three-of-three to the H2H, one-of-one to the H2H, one-of-one to the H2H, now 2–2 again.** ⛔ **Do not read a direction into that and do not set it beside the hand-carded note that the class has beaten the head-to-head 3/3 when they FLATLY DISAGREED — that note is about a TIEBREAKER being INVOKED and this is about a COLUMN being PRINTED on every row.** ⛔ **Different population, different trigger. Do not add them together.**

⚠️ 🔴 **THE CEASE ROW IS THE ONE WORTH A SENTENCE, BECAUSE THE CLASS FIGURE IS UNINFORMATIVE BY CONSTRUCTION AND SAYING SO IS THE HONEST READ: 1/5 is a sample of FIVE STARTS.** **A 20.0% class on n=5 is not evidence against a play; it is noise wearing a percentage.** ⛔ **Scoring it as "the H2H was right" is arithmetically correct and epistemically empty — the same defect the 8/23 Abbott row and the 8/25 boundary rows were flagged for.**

### 🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **SIXTH CONSECUTIVE RUN** — ⚠️ **AND AGAIN IT COST NOTHING, WHICH WAS MEASURED RATHER THAN ASSUMED**

`[re-checked 2026-08-29]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-08-28.json`.**

✅ **THE GAP WAS COMPUTED HERE INSTEAD, FOR ALL EIGHT ARMS THAT CARRY A PRIOR MEETING, by re-deriving each meeting from the repo's own pre-slate log (`data/latest/pitchers.json.gz` at `2026-08-28T18:08:13Z`, the same pull the card read):**

| Pitcher | Opponent | Most recent prior meeting | Gap |
|---|---|---|---|
| Jacob Lopez | BAL | 2026-05-08 | **112 days** |
| Emerson Hancock | TOR | 2026-07-05 | **54 days** |
| Michael Wacha | CLE | 2026-05-04 | **116 days** |
| Rhett Lowder | CHC | 2026-05-07 | **113 days** |
| Grant Holmes | COL | 2026-05-01 | **119 days** |
| Dean Kremer | CWS | 2026-07-01 | **58 days** |
| Dylan Cease | SEA | 2026-07-03 | **56 days** |
| David Peterson | CIN | 2026-05-26 | **94 days** |

➡️ **Every one is far outside rule 51's 30-day window, so NO rule-51 instance was owed on this slate and the accumulator below correctly gains NO rows.** ⛔ **That is the defect not biting, not the defect being fixed. It is still REPORTED, NOT FIXED — a grading run does not touch the code and a headless session can neither test nor push a change.**

✅ **The re-derivation is also a control on the card: every head-to-head count the card printed reproduces exactly from the same log.**

### 🟡 THE `carried` SHADOW — 8/28. 🔴 **WORSE AGAIN, ON THE LARGEST DIFFERING SET YET — AND BY THE SAME MECHANISM RUNNING THE OTHER WAY.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 9 of the 25 rows — EVERY ONE the `T22` shuttled-starter warning, across SIX pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Jacob Lopez u6.5 K | 71.8% | 57.4% | **W** | **blend** |
| Jacob Lopez u16.5 outs | 70.4% | 56.0% | **W** | **blend** |
| Andrew Painter u16.5 outs | 67.6% | 53.2% | **L** | **carried** |
| Andrew Painter u5.5 K | 66.9% | 52.5% | **L** | **carried** |
| Drew Anderson u14.5 outs | 65.6% | 51.2% | **W** | **blend** |
| Grant Holmes u4.5 K | 63.4% | 49.0% | **W** | **blend** |
| Rhett Lowder o3.5 K | 62.9% | 48.5% | **W** | **blend** |
| David Peterson u16.5 outs | 58.1% | 43.7% | **W** | **blend** |
| Rhett Lowder o15.5 outs | 56.3% | 41.9% | **L** | **carried** |

| | Brier over all 25 rows | Brier over the 9 rows that differ |
|---|---|---|
| `blend` | 🔴 **.2602** | 🔴 **.2171** |
| `carried` | **.2696** | **.2433** |
| Verdict | 🔴 **`carried` is WORSE by .0094** | 🔴 **`carried` is WORSE by .0262** |

⛔ **NINE ROWS FROM SIX PITCHERS, TWO OF THEM ONE MAN TWICE. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **AND THE MECHANISM IS THE 8/25 AND 8/26 MECHANISM INVERTED, WHICH IS THE POINT AND IS WHY NEITHER RESULT IS EVIDENCE: six of the nine rows WON, and `carried` is ALWAYS the LOWER number.** **It loses this Brier for being pessimistic on a good set of rows exactly as it won the last two for being pessimistic on bad ones.** ⛔ **Six slates, four verdicts, and every single one is explained by whether that night's T22-flagged rows happened to win. That is the day-tracking artifact this page condemns the "closer" column for, measured in a proper scoring rule.**

➡️ **RUNNING ACROSS THE SIX MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 30 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27, 9 on 8/28 — and the verdict is WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE.** ⚠️ **On every one of the six nights the differing rows were concentrated in one or two pitchers. Thirty correlated rows is not a measurement; it is still the beginning of one.**

### ✅ 🆕 A RUN-LEVEL FACT, LOGGED BECAUSE IT REVERSES THE LAST TWO ENTRIES: THE COLLECTOR'S RESULTS MODE IS BACK

🔴 **The last two runs recorded the repo grading route as unavailable, for two different reasons.** ✅ **It worked this run: `data/2026-08-28/results/final.json.gz` was pulled `2026-08-29T10:07:00Z` and reads `n_games: 15, n_final: 15, domain_violations: 0`, and the collector has BACK-FILLED 8/26 and 8/27 as well.** ✅ **`data/latest/record.json` now carries `by_day` rows for all three and every one matches what this project graded — including `2026-08-27: 18/36, voids 2`, which is the destroyed-card slate the ledger graded as TABLE M 0/1 plus TABLE M-H 18/35.** ⛔ **It is still a CONVENIENCE and it was still not trusted alone: the slate was controlled five independent ways, one of them an INDEPENDENT statsapi pull on a different host for all 19 pitchers, 19/19 exact. Detail in `claude/pick-ledger.md`.**

~~**Progress: TABLE M — 6 slates, 129 graded pitcher plays, 40 pairs. TABLE M-H — 5 slates, 134 graded hitter rows.**~~ ⚠️ 🔴 **SUPERSEDED 2026-08-30 by the 8/29 block immediately below — the counter now reads TABLE M 7 slates / 135 GRADED pitcher plays / 48 pairs, and TABLE M-H 6 slates / 175 graded hitter rows. KEPT, NOT DELETED: this is the state of the accumulator after six slates.** ⚠️ **The 8/29 slate adds only SIX pitcher rows, and the reason is in the ledger: the card file was overwritten after the slate began, for the second time in four days.**

---

## 🆕 2026-08-30 — THE SEVENTH MACHINE SLATE (2026-08-29), A CARD DESTROYED FOR THE SECOND TIME, AND A DOUBLEHEADER THE GRADING RULES DO NOT REACH

`[graded 2026-08-30]` 🔴🔴 **`picks/2026-08-29.json` AS COMMITTED IS 50 PLAYS — 6 PITCHER AND 44 HITTER — ACROSS THREE GAMES.** **`50 = 6 + 44` ✅.**

🔴 **IT IS NOT A THREE-GAME SLATE. 2026-08-29 WAS A SEVENTEEN-GAME SLATE, AND THIS IS THE SECOND DESTROYED CARD IN FOUR DAYS.** **The pre-slate `20b154f2` at `2026-08-29T11:08:08Z` (7:08am ET) held 50 plays across 13 games with TWENTY-FIVE pitcher rows; the surviving `49ec278a` at `23:27:52Z` (7:27pm ET) holds 6, because `card.py`'s own guard dropped thirteen games as `"already started"`.** ✅ **Full provenance, the commit hashes and the reasoning for grading the surviving file are in `claude/pick-ledger.md`.** ⛔ **A grading run does not touch the code; it is REPORTED there.**

⛔ **THE 44 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24 through 8/28: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in `claude/pick-ledger.md` — 25/41, with THREE rows ungraded — and nothing here counts them.**

⚠️ 🔴 **ONE OF THOSE THREE UNGRADED ROWS IS A NEW KIND OF GAP AND IT IS NAMED HERE BECAUSE IT WILL RECUR: 2026-08-29 CARRIED TWO DOUBLEHEADERS, AND A DATE IS NOT A GAME.** **Jose Fernandez was carded on the 02:06Z AZ @ SF event (`gamePk 823176`, game 2) and appeared only in game 1, so his date-level game log carries an `8/29` row belonging to a different game at a different price against a different pitcher.** ⛔ **Left UNGRADED on the 8/24 Hayes / 8/26 Roupp precedent, with both readings printed in the ledger, and flagged for an interactive session.** ➡️ **Every accumulator on this page that ever reads a game log by DATE inherits this hazard. Resolve to a `gamePk`, not to a date.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **SEVENTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23, 8/24, 8/25, 8/26, 8/27, 8/28 or 8/29, so the CARDED denominator has not moved for seven consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Folding in the machine card's rows — six, this time — would still be a silent re-specification of a pre-registered test, and the smallness of the number is not a licence. It is not done.**

⚠️ 🔴 **THE DROUGHT IS NOW EIGHT DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.** ➡️ **Closing T15 needs either an interactive card or a MACHINE-population version pre-registered as its own entry with its own bar. ⛔ A grading run may create neither.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The surviving 8/29 card carries Hard Rock alt ladders on its pitcher rows across 5 distinct starts.** 🔴 **IT IS NOT MERGED, for the seventh time and for the same reason: T11's `n` is CARDED arms and the machine board is every qualifying starter.** ➡️ **A machine shadow ladder must be PRE-REGISTERED as its own entry in `claude/owed-tests.md`, in an interactive session.** ⛔ **Do not merge first and register afterwards.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket table:**

**Ryan Johnson 2026-08-29 (2 K) · Cristopher Sánchez 2026-08-29 (8 K) · Mitch Bratt 2026-08-29 (2 K) · Shane Baz 2026-08-29 (4 K) · Jack Perkins 2026-08-29 (5 K)** — **5 distinct (pitcher, date) pairs, none of which appears in the 8/20, 8/21 or 8/22 passes.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 8/29. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 8/28 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **6** *(no row sits exactly on 50.0%, so nothing is excluded this slate)* | **2/6** | 🔴 **worse than a coin flip — 15/32, 16/23, 11/23, 13/23, 0/1, 10/25, now 2/6 across seven slates** |
| **Head-to-head** (prior meetings) | 🔴 **1** | **1/1** | ⛔ **ONE ROW, and n=1.** |
| **Head-to-head, NO CALL** | **5** | — | ⛔ **n=0 rows, logged and in no tally** (1 + 5 = 6 ✅) |

⛔ 🔴 **THE BOUNDARY-ROW CONVENTION INCONSISTENCY FLAGGED ON 8/25 IS STILL UNCHANGED AND UNRESOLVED — 8/23 kept its 50.0% row inside its denominator while 8/25 excluded two.** ➡️ **The seven class tallies are therefore still NOT summable as published and are still reported as seven separate enumerated tallies. An interactive session should settle the convention; a grading run does not re-cut a published tally after the fact.**

#### ⛔ NO ROW WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED

**The single row carrying a head-to-head — Shane Baz u17.5 outs vs ATH, class 22/41 (53.7%) FOR and h2h 1/1 FOR — has both sources pointing the SAME way, so there is no conflict to score.** ⚠️ **Across the seven machine slates the conflicts run 2–2, four-of-five to the CLASS, three-of-three to the H2H, one-of-one to the H2H, one-of-one to the H2H, 2–2, and now NONE.** ⛔ **Do not read a direction into that and do not set it beside the hand-carded note that the class has beaten the head-to-head 3/3 when they FLATLY DISAGREED — that note is about a TIEBREAKER being INVOKED and this is about a COLUMN being PRINTED on every row.**

⚠️ 🔴 **AND SAY THE OBVIOUS THING ABOUT THE 2/6: it is SIX ROWS, five of them from three pitchers, on the wreckage of a seventeen-game slate.** ⛔ **It is not a data point about the matched class.**

### 🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **SEVENTH CONSECUTIVE RUN** — ⚠️ **AND AGAIN IT COST NOTHING, WHICH WAS MEASURED RATHER THAN ASSUMED**

`[re-checked 2026-08-30]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-08-29.json`.**

✅ **THE GAP WAS COMPUTED HERE INSTEAD, FOR THE ONE ARM THAT CARRIES A PRIOR MEETING, by re-deriving it from the repo's own stored log:**

| Pitcher | Opponent | Most recent prior meeting | Gap |
|---|---|---|---|
| Shane Baz | ATH | 2026-05-09 | **112 days** |

➡️ **Far outside rule 51's 30-day window, so NO rule-51 instance was owed on this slate and the accumulator below correctly gains NO rows.** ⛔ **That is the defect not biting, not the defect being fixed. It is still REPORTED, NOT FIXED — a grading run does not touch the code and a headless session can neither test nor push a change.**

✅ **The re-derivation is also a control on the card: the head-to-head string it printed — `1 start(s) vs ATH -- cleared 1/1` — reproduces exactly from the same log (14 outs, 5 K on 2026-05-09, which clears both an o3.5 K and a u17.5 outs).**

### 🟡 THE `carried` SHADOW — 8/29. 🔴 **WORSE AGAIN, ON TWO ROWS.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 2 of the 6 rows — BOTH the `T22` shuttled-starter warning, across two pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Ryan Johnson u15.5 outs | 64.6% | 50.2% | **W** | **blend** |
| Jack Perkins u5.5 K | 52.8% | 38.4% | **W** | **blend** |

| | Brier over all 6 rows | Brier over the 2 rows that differ |
|---|---|---|
| `blend` | 🔴 **.2500** | 🔴 **.1741** |
| `carried` | **.2965** | **.3137** |
| Verdict | 🔴 **`carried` is WORSE by .0466** | 🔴 **`carried` is WORSE by .1397** |

⛔ **TWO ROWS FROM TWO PITCHERS ON A WRECKED CARD. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **AND THE MECHANISM IS THE SAME ONE, FOR THE SEVENTH TIME: BOTH differing rows WON, and `carried` is ALWAYS the LOWER number, so it loses for being pessimistic on a good set exactly as it won on 8/25 and 8/26 for being pessimistic on bad ones.** ⛔ **Seven slates, five verdicts, and every single one is explained by whether that night's T22-flagged rows happened to win. That is the day-tracking artifact this page condemns the "closer" column for, measured in a proper scoring rule.**

➡️ **RUNNING ACROSS THE SEVEN MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 32 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27, 9 on 8/28, 2 on 8/29 — and the verdict is WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE, WORSE.** ⚠️ **On every one of the seven nights the differing rows were concentrated in one or two pitchers. Thirty-two correlated rows is not a measurement; it is still the beginning of one.**

### ⚠️ 🆕 A RUN-LEVEL FACT, LOGGED BECAUSE IT IS THE FIRST TIME THE RUNNER AND THIS PROJECT HAVE DISAGREED

✅ **The repo grading route worked for a second consecutive run: `data/2026-08-29/results/final.json.gz` was pulled `2026-08-30T10:06:25Z` and reads `n_games: 17, n_final: 17, domain_violations: 0`.**

🔴 **BUT `data/latest/record.json` NO LONGER REPRODUCES THIS PROJECT'S HITTER TOTAL. It reads `by_kind.pitcher: 71/135` — EXACT — and `by_kind.hitter: 107/176` against this project's 106/175, with `by_day 2026-08-29: 30/48, voids 2` against 29/47, voids 3.** ✅ **The entire difference is the ONE Jose Fernandez doubleheader row: the runner grades hitter rows by DATE and this project grades them by EVENT.** ⛔ **Neither is a bug. It is the mechanics question above, and it is put in front of an interactive session rather than settled here.** ⚠️ **The pitcher half reproducing exactly is a genuine independent control and it is worth more than the disagreement is worth worrying about.**

~~**Progress: TABLE M — 7 slates, 135 graded pitcher plays, 48 pairs. TABLE M-H — 6 slates, 175 graded hitter rows.**~~ ⚠️ 🔴 **SUPERSEDED 2026-08-31 by the 8/30 block immediately below — the counter now reads TABLE M 8 slates / 160 GRADED pitcher plays / 56 pairs, and TABLE M-H 7 slates / 198 graded hitter rows. KEPT, NOT DELETED: this is the state of the accumulator after seven slates.**

---

## 🆕 2026-08-31 — THE EIGHTH MACHINE SLATE (2026-08-30): A FULL UNDAMAGED CARD, THE WORST GAP A FULL MACHINE BOARD HAS RECORDED, AND THE FIRST TIME CHECK 36's DEFECT ACTUALLY COST SOMETHING

`[graded 2026-08-31]` ✅ **`picks/2026-08-30.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 14 GAMES.** **`50 = 25 + 25` ✅.**

✅ **THE FILE WAS WRITTEN TWICE AND FOR THE FIRST TIME IN FOUR DAYS THE OVERWRITE COST NOTHING: `1855d53` at `11:09:53Z` and the surviving `bbc364e` at `14:08:23Z` are BOTH pre-slate and identical on every axis, and `coverage_detail.skipped` carries no `"already started"` key at all.** ⛔ **The code is unchanged and so is the hazard. A mechanism that happens not to bite has not been fixed, and the interactive decision owed since 8/27 is now owed a THIRD time.** ✅ **Full provenance in `claude/pick-ledger.md`.**

⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24 through 8/29: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in the ledger — 17/23, two rows ungraded because Tyler Heineman did not play — and nothing here counts them.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **EIGHTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23 through 8/30, so the CARDED denominator has not moved for eight consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Folding in the machine card's 25 pitcher rows would take the counter past 56 without a single carded play, which is a silent re-specification of a pre-registered test. It is not done.**

⚠️ 🔴 **THE DROUGHT IS NOW NINE DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.** ➡️ **Closing T15 needs either an interactive card or a MACHINE-population version pre-registered as its own entry with its own bar. ⛔ A grading run may create neither.**

⚠️ **What the machine slate DID show, recorded here and NOT folded into T15: over its 25 rows the mean `model` is 60.2, the mean `raw` 71.8 and the actual 44.0, with Brier `model` .2511 · `blend` .2822 · `raw` .3335.** 🔴 **Pure model "wins" for the same reason it won on 8/22 — it was the LOWER of the two estimates on 21 of the 25 rows and the slate lost.** ⛔ **That is the day-tracking artifact this page condemns, in a proper scoring rule, on a different population. It is not evidence about the blend weight.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 8/30 card carries Hard Rock alt ladders across 17 distinct starts — enough on its own to take T11 from 25 past its bar of 40.** 🔴 **IT IS NOT MERGED, for the eighth time and for the same reason: T11's `n` is CARDED arms and the machine board is every qualifying starter.** ➡️ **A machine shadow ladder must be PRE-REGISTERED as its own entry in `claude/owed-tests.md`, in an interactive session.** ⛔ **Do not merge first and register afterwards.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket table:**

**Max Scherzer 2026-08-30 (10 K) · Chase Burns (7 K) · Logan Gilbert (4 K) · Janson Junk (2 K) · Ranger Suarez (2 K) · Chris Bassitt (4 K) · Parker Messick (5 K) · Jeffrey Springs (6 K) · Yusei Kikuchi (6 K) · Zack Wheeler (6 K) · Shota Imanaga (4 K) · Robbie Ray (4 K) · Tyler Mahle (9 K) · Matthew Liberatore (9 K) · Braxton Ashcraft (3 K) · Tyler Glasnow (6 K) · Will Warren (7 K)** — **17 distinct (pitcher, date) pairs, all 2026-08-30, none of which appears in the 8/20, 8/21 or 8/22 passes.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 8/30. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 8/29 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **23** *(2 rows excluded — see below)* | **13/23** | ⚠️ **a coin flip again — 15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, now 13/23 across eight slates** |
| **Head-to-head** (prior meetings) | **8** | 🔴 **2/8** | ⛔ **six of the eight are n=1 and two are n=2** |
| **Head-to-head, NO CALL — n=0** | **11** | — | ⛔ **logged and in no tally** |
| 🆕 🔴 **Head-to-head, NO CALL — the published convention DOES NOT REACH THEM** | 🔴 **6** | — | ⛔ **see below** (8 + 11 + 6 = 25 ✅) |

🔴 🆕 **A CASE THE CONVENTION HAS NEVER MET, AND IT IS REPORTED RATHER THAN RESOLVED BY INVENTION. The convention says the head-to-head argues FOR on a MAJORITY and AGAINST when NONE cleared. Six rows on this card read `cleared 1/2` — neither a majority nor none — and the convention is silent.** **They are: Janson Junk vs WSH (twice), Ranger Suarez vs NYY (twice), Shota Imanaga vs CIN, Tyler Mahle vs COL.** ⛔ **They are recorded as NO CALL, which is the literal reading of the published rule and the choice that invents nothing.** ➡️ **An interactive session should settle it; a grading run does not write a new convention mid-tally.** ⚠️ **It matters: reading `1/2` as FOR would make the head-to-head tally 4/14 instead of 2/8.**

⛔ 🔴 **AND THE BOUNDARY-ROW CONVENTION INCONSISTENCY FLAGGED ON 8/25 IS STILL UNCHANGED AND UNRESOLVED — 8/23 kept its 50.0% row inside its denominator while 8/25 excluded two.** **Two rows are excluded here on the 8/25 practice and NAMED rather than quietly dropped: Logan Gilbert o4.5 K (class 37/74 = 50.0%, result L) and Tyler Glasnow o6.5 K (class 12/24 = 50.0%, result L).** ➡️ **The eight class tallies are therefore still NOT summable as published and are still reported as eight separate enumerated tallies.**

#### 🔴 TWO ROWS WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED — AND THEY SPLIT ONE–ONE

| play | class (all) | head-to-head | result | which was right |
|---|---|---|---|---|
| Logan Gilbert u18.5 outs vs TOR | 15/21 (71.4%) FOR | 0/1 AGAINST | **W** (15 outs) | ✅ **CLASS** |
| Robbie Ray u16.5 outs vs TB | 20/30 (66.7%) FOR | 0/1 AGAINST | **L** (18 outs) | ✅ **H2H** |

⚠️ 🔴 **TWO ROWS, BOTH HEAD-TO-HEADS A SINGLE START, A ONE–ONE SPLIT.** **Across the eight machine slates the conflicts run 2–2, four-of-five to the CLASS, three-of-three to the H2H, one-of-one to the H2H, one-of-one to the H2H, 2–2, NONE, now 1–1.** ⛔ **Do not read a direction into that and do not set it beside the hand-carded note that the class has beaten the head-to-head 3/3 when they FLATLY DISAGREED — that note is about a TIEBREAKER being INVOKED and this is about a COLUMN being PRINTED on every row.** ⛔ **Different population, different trigger. Do not add them together.**

### 🔴🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **EIGHTH CONSECUTIVE RUN** — 🆕 **AND FOR THE FIRST TIME IT COST SOMETHING**

`[re-checked 2026-08-31]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-08-30.json`.**

🔴 **EVERY PRIOR RUN SINCE 8/24 HAS BEEN ABLE TO ADD "AND IT COST NOTHING", BECAUSE EVERY PRIOR MEETING WAS 50+ DAYS OLD. THIS SLATE IS THE EXCEPTION.** ✅ **The gap was computed here, for all nine arms carrying a prior meeting, by re-deriving each meeting from the repo's own stored log:**

| Pitcher | Opponent | Most recent prior meeting | Gap |
|---|---|---|---|
| 🔴 **Janson Junk** | 🔴 **WSH** | 🔴 **2026-08-23** | 🔴 **7 days — INSIDE the 30-day window** |
| Tyler Mahle | COL | 2026-07-11 | 50 days |
| Shota Imanaga | CIN | 2026-07-10 | 51 days |
| Logan Gilbert | TOR | 2026-07-04 | 57 days |
| Will Warren | BOS | 2026-06-26 | 65 days |
| Ranger Suarez | NYY | 2026-06-07 | 84 days |
| Braxton Ashcraft | STL | 2026-05-21 | 101 days |
| Matthew Liberatore | PIT | 2026-05-19 | 103 days |
| Robbie Ray | TB | 2026-05-01 | 121 days |

✅ **The re-derivation doubles as a control on the card: every head-to-head COUNT the card printed reproduces exactly from the same log, 14/14 rows.**

⛔ **REPORTED, NOT FIXED — a grading run does not touch the code and a headless session can neither test nor push a change.** ➡️ **Interactive fix, unchanged and now urgent rather than cosmetic: emit the gap in days on every row that has a prior meeting.**

### 🆕 🔴 A MACHINE-POPULATION RULE 51 LOG — CREATED HERE BECAUSE AN INSTANCE FINALLY EXISTS. ⛔ **NOT ADDED TO THE HAND-CARDED RULE 51 ACCUMULATOR ABOVE.**

**The hand-carded rule-51 table above is CARDED plays and stays at 2 clean instances / 1 confounded.** ⛔ **A machine row may not be dropped into it — that is the population merge this whole page exists to prevent.** ✅ **So the instance is logged here, separately, and an interactive session should decide whether a machine rule-51 accumulator is worth pre-registering.**

| date | play | threshold | opponent | first meeting | days since | W/L | actual K |
|---|---|---|---|---|---|---|---|
| 2026-08-30 | **Janson Junk o2.5 K** *(TABLE M, machine card)* | 2.5 (a **3+ K** bar) | WSH | **2026-08-23 — 2 K** in 4.2 IP | 🔴 **7** | ❌ **MISS** | **2 K** (4.2 IP, 65 pitches, 18 BF) |

⚠️ **The direction is the one the EXPLORATORY threshold haircut predicts — a rematch inside 30 days, and the play missed.** ⛔ **It is ONE ROW, on a different population from the pre-registered test, and the first meeting was WEAK (2 K), so it does not even test the "conditional on a strong ≥5 K first meeting" version the exploratory finding is about.** ⛔ **The pre-registered mean-K specification is still FAILED and still CLOSED, and nothing here promotes the threshold version.**

⚠️ **He also carded an OUTS row against the same lineup on the same day (o14.5 outs, MISS at 14 outs).** ⛔ **Outs are outside rule 51's scope — the 8/22 Cease context row set that precedent — so it is named and is in no tally.**

### 🟡 THE `carried` SHADOW — 8/30. 🔴 **WORSE AGAIN, ON SEVEN ROWS.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 7 of the 25 rows — every one the `T22` shuttled-starter warning, across FOUR pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Janson Junk o2.5 K | 70.6% | 56.2% | **L** | **carried** |
| Chris Bassitt u17.5 outs | 70.0% | 55.6% | **W** | **blend** |
| Chris Bassitt u4.5 K | 67.6% | 53.2% | **W** | **blend** |
| Robbie Ray o3.5 K | 67.0% | 52.6% | **W** | **blend** |
| Janson Junk o14.5 outs | 57.0% | 42.6% | **L** | **carried** |
| Robbie Ray u16.5 outs | 56.9% | 42.5% | **L** | **carried** |
| Will Warren o4.5 K | 56.6% | 42.2% | **W** | **blend** |

| | Brier over all 25 rows | Brier over the 7 rows that differ |
|---|---|---|
| `blend` | 🔴 **.2822** | 🔴 **.2342** |
| `carried` | **.2827** | **.2361** |
| Verdict | 🔴 **`carried` is WORSE by .0005** | 🔴 **`carried` is WORSE by .0019** |

⛔ **SEVEN ROWS FROM FOUR PITCHERS, TWO PITCHERS CONTRIBUTING TWO EACH. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **THE MECHANISM IS THE SAME ONE FOR THE EIGHTH TIME: four of the seven differing rows WON, and `carried` is ALWAYS the LOWER number, so it loses for being pessimistic on a mildly good subset.** ⚠️ **And this is the sharpest illustration yet of why the sign of this verdict says nothing about T22: the card as a whole missed its own mean by TWENTY-TWO POINTS — the most pessimism-friendly slate in the machine card's history — and the pessimistic shadow was STILL worse, because the seven rows it touched were not the rows that lost.**

➡️ **RUNNING ACROSS THE EIGHT MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 39 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27, 9 on 8/28, 2 on 8/29, 7 on 8/30 — and the verdict is WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE, WORSE, WORSE.** ⚠️ **On every one of the eight nights the differing rows were concentrated in a handful of pitchers. Thirty-nine correlated rows is not a measurement; it is still the beginning of one.**

### 🆕 🔴 TWO SURFACES HAVE BEEN LIVE ON THE CARD SINCE 2026-08-26 AND NEITHER HAS EVER BEEN NAMED IN THIS PROJECT

`[measured 2026-08-31, enumerated across `picks/2026-08-22.json` through `picks/2026-08-31.json`]` **A `parlays` object (2-, 3- and 4-leg tickets mixing pitcher and hitter legs, under Sam's 8/26 bands) and a `top10` list (his −400 payable floor) are absent on 8/22–8/25 and present on 8/26 and EVERY card since.** ⛔ **No grading run has recorded either — five days of them.**

✅ **Both are now graded and recorded in `claude/pick-ledger.md`, and BOTH ARE IN NO DENOMINATOR ON THIS PAGE AND IN NO ACCUMULATOR HERE.** ⛔ **The parlays are not merged with TABLE M PAIRS; the `top10` rows are all already TABLE M-H rows this slate (10/10, checked on (player, market, side, line)) so it opens nothing.** ➡️ **Whether either becomes a denominator is an interactive decision.**

⚠️ 🔴 **AND A CARD DEFECT FOUND BY COUNTING RATHER THAN READING, RECORDED HERE BECAUSE IT AFFECTS ANY FUTURE PAIR OR PARLAY ACCUMULATOR: THE POOL EMITS BYTE-IDENTICAL DUPLICATE TICKETS.** **Two of the eight pairs on 8/30 duplicate two others, and one ticket in each of the three parlay leg-counts does the same — zero such duplicates on 8/26, 8/28 or 8/29, two on 8/30 and two again on the live 8/31 card.** ⛔ **An accumulator that counts printed tickets would silently double-weight one ticket. REPORTED, NOT FIXED.**

~~**Progress: TABLE M — 8 slates, 160 graded pitcher plays, 56 pairs. TABLE M-H — 7 slates, 198 graded hitter rows.**~~ ⚠️ 🔴 **SUPERSEDED 2026-09-01 by the 8/31 block immediately below — the counter now reads TABLE M 9 slates / 185 GRADED pitcher plays / 64 pairs, and TABLE M-H 8 slates / 221 graded hitter rows. KEPT, NOT DELETED: this is the state of the accumulator after eight slates.**

---

---

## 🆕 2026-09-01 — THE NINTH MACHINE SLATE (2026-08-31): A SECOND CONSECUTIVE UNDAMAGED CARD, `carried` WORSE A FOURTH TIME RUNNING, AND CHECK 36's DEFECT BITING ON CONSECUTIVE SLATES

`[graded 2026-09-01]` ✅ **`picks/2026-08-31.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 12 GAMES.** **`50 = 25 + 25` ✅.**

✅ **THE FILE WAS WRITTEN TWICE AND FOR THE SECOND CONSECUTIVE DAY THE OVERWRITE COST NOTHING: `05ba1e4` at `11:08:12Z` and the surviving `8495399` at `14:09:01Z` are BOTH pre-slate and identical on every axis, and `coverage_detail.skipped` carries no `"already started"` key at all.** ⛔ **The code is unchanged and so is the hazard. A mechanism that happens not to bite has not been fixed, and the interactive decision owed since 8/27 is now owed a FOURTH time.** ✅ **Full provenance in `claude/pick-ledger.md`.**

⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24 through 8/30: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in the ledger — 20/23, two rows ungraded because Drew Cavanaugh and Drew Romo did not play — and nothing here counts them.** 🆕 **Their gap is **+5.1**, the FIRST POSITIVE gap that table has recorded on a comparable board.** ⛔ **Seven scattered gaps from −26 to +5 are not a converging set and are not averaged; nothing on this page moves for it.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **NINTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23 through 8/31, so the CARDED denominator has not moved for nine consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Folding in the machine card's 25 pitcher rows would take the counter past 56 without a single carded play, which is a silent re-specification of a pre-registered test. It is not done.**

⚠️ 🔴 **THE DROUGHT IS NOW TEN DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.** ➡️ **Closing T15 needs either an interactive card or a MACHINE-population version pre-registered as its own entry with its own bar. ⛔ A grading run may create neither.**

⚠️ 🔴 **WHAT THE MACHINE SLATE DID SHOW IS RECORDED HERE AND NOT FOLDED IN — AND IT POINTS THE OPPOSITE WAY TO YESTERDAY'S, WHICH IS THE POINT.** **Over its 25 rows the mean `model` is 59.4, the mean `raw` 67.8, the mean `blend` 63.6 and the actual 56.0, with Brier `model` .2631 · `blend` .2491 · `raw` .2482.** 🔴 **RAW "wins" today for the mirror of the reason MODEL won on 8/30: raw was the HIGHER of the two estimates on most rows and the slate went 14/25, where on 8/30 model was the LOWER estimate on 21 of 25 and the slate went 11/25.** ⛔ **Two consecutive slates, opposite winners, one mechanism — the day-tracking artifact this page condemns the "closer" column for, measured in a proper scoring rule on a population T15's specification does not cover.** ⛔ **It is not evidence about the blend weight.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 8/31 card carries Hard Rock alt ladders on 13 of its 25 pitcher rows — 150 rungs across 12 distinct starts.** 🔴 **IT IS NOT MERGED, for the ninth time and for the same reason: T11's `n` is CARDED arms and the machine board is every qualifying starter.** ➡️ **A machine shadow ladder must be PRE-REGISTERED as its own entry in `claude/owed-tests.md`, in an interactive session.** ⛔ **Do not merge first and register afterwards.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket table:**

**Clay Holmes (8 K) · Elmer Rodríguez (5 K) · Anthony Kay (5 K) · Payton Tolle (6 K) · Aaron Nola (4 K) · Robert Stock (4 K) · Brady Singer (5 K) · Jacob deGrom (8 K) · Ian Seymour (10 K) · Ryan Gusto (4 K) · Tanner Gordon (3 K) · Kyle Harrison (3 K) · Walbert Ureña (8 K) · Michael King (6 K) · Taj Bradley (9 K) · George Kirby (2 K)** — **16 distinct (pitcher, date) pairs, all 2026-08-31, none of which appears in the 8/20, 8/21 or 8/22 passes.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 8/31. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 8/30 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **24** *(1 row excluded — see below)* | **13/24** | ⚠️ **a coin flip again — 15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, now 13/24 across nine slates** |
| **Head-to-head** (prior meetings) | **7** | **4/7** | ⛔ **five of the seven are n=1 and two are n=2** |
| **Head-to-head, NO CALL — n=0** | **16** | — | ⛔ **logged and in no tally** |
| 🔴 **Head-to-head, NO CALL — the published convention DOES NOT REACH IT** | 🔴 **1** | — | ⛔ **see below** (7 + 16 + 1 + 1 = 25 ✅) |

🔴 **THE `cleared 1/2` CASE THE 8/30 RUN MET FOR THE FIRST TIME RECURS, AND IT IS TREATED IDENTICALLY RATHER THAN RE-DECIDED. One row — Taj Bradley vs DET, `2 start(s) -- cleared 1/2` — is neither a MAJORITY nor NONE, and the convention is silent.** ⛔ **Recorded as NO CALL, the literal reading of the published rule and the choice that invents nothing.** ➡️ **An interactive session should settle it; a grading run does not write a new convention mid-tally, and it does not write one on the second sighting either.**

⛔ 🔴 **AND THE BOUNDARY-ROW CONVENTION INCONSISTENCY FLAGGED ON 8/25 IS STILL UNCHANGED AND UNRESOLVED — 8/23 kept its 50.0% row inside its denominator while 8/25 excluded two.** **One row is excluded here on the 8/25 practice and NAMED rather than quietly dropped: Jacob deGrom u6.5 K (class 11/22 = 50.0%, result L).** ➡️ **The nine class tallies are therefore still NOT summable as published and are still reported as nine separate enumerated tallies.**

#### 🔴 ONE ROW WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED

| play | class (all) | head-to-head | result | which was right |
|---|---|---|---|---|
| Brady Singer o4.5 K vs SD | 35/79 (44.3%) AGAINST | 1/1 FOR | **W** (5 K) | ✅ **H2H** |

⚠️ 🔴 **ONE ROW, AND ITS HEAD-TO-HEAD IS A SINGLE START. ⛔ IT IS NOT A DATA POINT ABOUT ANYTHING.** **Across the nine machine slates the conflicts run 2–2, four-of-five to the CLASS, three-of-three to the H2H, one-of-one to the H2H, one-of-one to the H2H, 2–2, NONE, 1–1, now one-of-one to the H2H.** ⛔ **Do not read a direction into that and do not set it beside the hand-carded note that the class has beaten the head-to-head 3/3 when they FLATLY DISAGREED — that note is about a TIEBREAKER being INVOKED and this is about a COLUMN being PRINTED on every row.** ⛔ **Different population, different trigger. Do not add them together.**

### 🔴🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **NINTH CONSECUTIVE RUN** — 🆕 **AND IT HAS NOW BITTEN ON CONSECUTIVE SLATES**

`[re-checked 2026-09-01]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-08-31.json`.**

✅ **The gap was computed here instead, for all six arms carrying a prior meeting, by re-deriving each meeting from the repo's own stored log:**

| Pitcher | Opponent | Most recent prior START | Gap |
|---|---|---|---|
| 🔴 **Ryan Gusto** | 🔴 **WSH** | 🔴 **2026-08-21** | 🔴 **10 days — INSIDE the 30-day window** |
| Kyle Harrison | CHC | 2026-06-27 | 65 days |
| Payton Tolle | SEA | 2026-06-21 | 71 days |
| Brady Singer | SD | 2026-06-10 | 82 days |
| Michael King | CIN | 2026-06-10 | 82 days |
| Taj Bradley | DET | 2026-06-09 | 83 days |

🔴 **UNTIL 8/30 EVERY PRIOR MEETING ON EVERY MACHINE SLATE WAS 50+ DAYS OLD AND EVERY RUN COULD ADD "AND IT COST NOTHING". JANSON JUNK WAS THE FIRST EXCEPTION; RYAN GUSTO IS THE SECOND, ON THE VERY NEXT SLATE.** ⛔ **REPORTED, NOT FIXED — a grading run does not touch the code and a headless session can neither test nor push a change.** ➡️ **Interactive fix, unchanged and now twice-demonstrated: emit the gap in days on every row that has a prior meeting.**

✅ **The re-derivation doubles as a control on the card: every head-to-head string it printed reproduces exactly from the same log, 8/8 — once the filter is applied to STARTS (`gs == 1`) rather than to appearances.** ⚠️ 🔴 **THAT QUALIFIER IS NOT COSMETIC AND IT IS RECORDED BECAUSE IT ALMOST PRODUCED A FALSE FINDING: an appearance-based check reads Gusto's card string `1 start(s) vs WSH` as a MISMATCH against two Washington rows in the log. The second is a RELIEF appearance on 2026-06-02. The card counts starts and the card is right; the check was wrong.** ➡️ **A control that disagrees with the thing it is checking is a claim about the CONTROL until the disagreement is enumerated.**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS NO GRADEABLE ROW, AND THE REASON IS SCOPE

⛔ **The hand-carded rule-51 table above is CARDED plays and stays at 2 clean instances / 1 confounded. A machine row may not be dropped into it.**

**Gusto's rematch is a genuine ≤30-day instance and it is NAMED — but his only 8/31 carded row is an OUTS row (u14.5 outs, W at 13 outs), and OUTS ARE OUTSIDE RULE 51'S SCOPE.** **The 8/22 Dylan Cease context row set that precedent and it is followed here rather than quietly widened.** ⛔ **So the machine rule-51 log created on 2026-08-31 stays at its single Janson Junk row.**

⚠️ **For the record and in no tally: Gusto's 2026-08-21 meeting with Washington was 12 outs and 2 K; on 8/31 he went 13 outs and 4 K.** ⛔ **One row, outside scope, on a population the pre-registered test does not cover. Nothing is promoted and the mean-K specification is still FAILED and CLOSED.**

### 🟡 THE `carried` SHADOW — 8/31. 🔴 **WORSE AGAIN, ON EIGHT ROWS — A FOURTH CONSECUTIVE "WORSE".** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 8 of the 25 rows — every one the `T22` shuttled-starter warning, across FIVE pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Anthony Kay o3.5 K | 69.7% | 55.3% | **W** | **blend** |
| Ryan Gusto u14.5 outs | 65.4% | 51.0% | **W** | **blend** |
| Ian Seymour u17.5 outs | 65.0% | 50.6% | **L** | **carried** |
| Tanner Gordon u4.5 K | 64.2% | 49.8% | **W** | **blend** |
| Walbert Ureña o4.5 K | 62.1% | 47.7% | **W** | **blend** |
| Ian Seymour u16.5 outs | 60.5% | 46.1% | **L** | **carried** |
| Walbert Ureña u5.5 K | 60.3% | 45.9% | **L** | **carried** |
| Tanner Gordon u15.5 outs | 59.4% | 45.0% | **W** | **blend** |

| | Brier over all 25 rows | Brier over the 8 rows that differ |
|---|---|---|
| `blend` | 🔴 **.2491** | 🔴 **.2250** |
| `carried` | **.2550** | **.2434** |
| Verdict | 🔴 **`carried` is WORSE by .0059** | 🔴 **`carried` is WORSE by .0184** |

⛔ **EIGHT ROWS FROM FIVE PITCHERS, THREE OF THEM CONTRIBUTING TWO EACH. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **THE MECHANISM IS THE SAME ONE FOR THE NINTH TIME: five of the eight differing rows WON, and `carried` is ALWAYS the LOWER number, so it loses for being pessimistic on a good subset exactly as it won on 8/25 and 8/26 for being pessimistic on bad ones.** ⛔ **Nine slates, six verdicts, and every single one is explained by whether that night's T22-flagged rows happened to win.**

➡️ **RUNNING ACROSS THE NINE MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 47 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27, 9 on 8/28, 2 on 8/29, 7 on 8/30, 8 on 8/31 — and the verdict is WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE, WORSE, WORSE, WORSE.** ⚠️ **On every one of the nine nights the differing rows were concentrated in a handful of pitchers. Forty-seven correlated rows is not a measurement; it is still the beginning of one.**

### ⚠️ 🆕 TWO CARD DEFECTS RE-OBSERVED, AND ONE `[hypothesis]` REFUTED RATHER THAN CARRIED FORWARD

🔴 **THE BYTE-IDENTICAL DUPLICATE TICKETS RECUR: two of the eight pairs duplicate two others, and two parlay tickets do the same.** ⚠️ **The 8/30 block guessed the cause was a Logan Gilbert strikeout ladder entering the pool once per carded row.** 🔴 **TODAY'S DUPLICATES CARRY NO GILBERT LEG AT ALL — the repeated leg is Aaron Nola's.** ✅ **What survives is the SHAPE and not the name: on both days the repeated leg belongs to a pitcher carded on TWO rows.** ⛔ **STILL A `[hypothesis]`, and any future pair or parlay accumulator that counts printed tickets will silently double-weight one ticket. REPORTED, NOT FIXED.**

⚠️ **Also re-reported and unchanged: `card.py`'s `parlay_rule` prose (1.8x–2.2x) still contradicts its pair `in_band` flag (computed against 2.10). It did NOT bite this slate — no pair lands between 2.10 and 2.20 — which is the defect not biting, not the defect being fixed. Open since 2026-08-26.**

~~**Progress: TABLE M — 9 slates, 185 graded pitcher plays, 64 pairs. TABLE M-H — 8 slates, 221 graded hitter rows.**~~ ⚠️ 🔴 **SUPERSEDED 2026-09-02 by the 9/1 block immediately below — the counter now reads TABLE M 10 slates / 209 GRADED pitcher plays / 70 graded pairs, and TABLE M-H 9 slates / 242 graded hitter rows. KEPT, NOT DELETED: this is the state of the accumulator after nine slates.**

---

## 🆕 2026-09-02 — THE TENTH MACHINE SLATE (2026-09-01): A THIRD CONSECUTIVE UNDAMAGED CARD, THE BEST-CALIBRATED MACHINE SLATE ON RECORD, `carried` WORSE A FIFTH TIME RUNNING, AND THE DUPLICATE-TICKET DEFECT SHOWN TO BE NON-DETERMINISTIC

`[graded 2026-09-02]` ✅ **`picks/2026-09-01.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 15 GAMES.** **`50 = 25 + 25` ✅.**

✅ **THE FILE WAS WRITTEN TWICE AND FOR THE THIRD CONSECUTIVE DAY THE OVERWRITE COST NOTHING: `580f1c7` at `14:08:23Z` and the surviving `c59f47c` at `18:41:09Z` are BOTH pre-slate — the earliest `commence` on the card is `22:41:00Z`, checked row by row — and `coverage_detail.skipped` carries no `"already started"` key at all.** ⛔ **The code is unchanged and so is the hazard; the interactive decision owed since 8/27 is owed a FIFTH time.** ✅ **Full provenance in `claude/pick-ledger.md`.**

⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24 through 8/31: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in the ledger — 17/21, four rows ungraded because Colt Keith, Zach McKinstry, Mike Yastrzemski and Leo Jimenez did not play — and nothing here counts them.** **Their gap is −1.3 against a mean stated rate of 82.3.** ⛔ **Eight comparable gaps now run −7.2, −26.3, −25.1, −11.3, +5.1 and −1.3. A scattered set from −26 to +5 is not a converging one and is not averaged.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **TENTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23 through 9/1, so the CARDED denominator has not moved for ten consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Folding in the machine card's 24 graded pitcher rows would take the counter past 55 without a single carded play, which is a silent re-specification of a pre-registered test. It is not done.**

⚠️ 🔴 **THE DROUGHT IS NOW ELEVEN DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.**

⚠️ 🔴 **AND WHAT THE MACHINE SLATE SHOWED IS RECORDED HERE AND NOT FOLDED IN — IT IS THE BEST-CALIBRATED MACHINE SLATE THE PROJECT HAS RECORDED AND THAT IS EXACTLY WHY IT MUST NOT BE.** **Over its 24 graded rows the mean `model` is 59.3, the mean `raw` 65.2, the mean `blend` 62.2 and the actual 62.5%, with Brier `model` .2442 · `blend` .2260 · `raw` .2229 · `carried` .2353.** **The blend missed its own mean by −0.3.** ⛔ **On 8/30 the same measurement read −22 and on 8/31 it read +0.4 on the hitter half; three consecutive slates have produced three different verdicts from the same instrument.** ⛔ **A −0.3 gap on 24 correlated rows is not evidence the model is calibrated, on a population T15's specification does not cover.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 9/1 card carries Hard Rock alt ladders across its pitcher rows.** 🔴 **IT IS NOT MERGED, for the tenth time and for the same reason: T11's `n` is CARDED arms and the machine board is every qualifying starter.** ➡️ **A machine shadow ladder must be PRE-REGISTERED as its own entry in `claude/owed-tests.md`, in an interactive session.** ⛔ **Do not merge first and register afterwards.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket table:**

**Sean Manaea 2026-09-01 (2 K) · Gabriel Hughes (4 K) · Robert Gasser (4 K) · Jesús Luzardo (6 K) · Randy Vásquez (3 K) · Bryan Woo (7 K) · Jake Irvin (5 K) · Matthew Boyd (3 K) · Randy Dobnak (6 K) · Gavin Williams (13 K) · MacKenzie Gore (4 K) · Ronel Blanco (3 K) · Eric Lauer (2 K) · Nick Lodolo (5 K) · Paul Skenes (4 K) · Michael McGreevy (4 K) · Troy Melton (4 K)** — **17 distinct (pitcher, date) pairs, all 2026-09-01, none of which appears in the 8/20, 8/21 or 8/22 passes.**

🔴 **SPENCER ARRIGHETTI IS DELIBERATELY NOT IN THAT LIST. He was carded as Toronto's starter, Toronto opened with Spencer Miles, and he entered as the bulk arm — `started: false`, confirmed on a second host by statsapi `gamesStarted: 0`.** ⛔ **He threw 3.2 innings and struck out 2; a future registered pass that wants relief appearances must say so in its own specification rather than inherit one silently.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/1. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 8/31 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **22** *(2 rows excluded — see below)* | **15/22** | ⚠️ **the best class tally of any machine slate — 15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, now 15/22 across ten slates** |
| **Head-to-head** (prior meetings) | **11** | **7/11** | ⚠️ **eight of the eleven are n=1, two are n=3 and one is n=2** |
| **Head-to-head, NO CALL — n=0** | **13** | — | ⛔ **logged and in no tally** (11 + 13 = 24 ✅) |

⛔ 🔴 **THE BOUNDARY-ROW CONVENTION INCONSISTENCY FLAGGED ON 8/25 IS STILL UNCHANGED AND UNRESOLVED — 8/23 kept its 50.0% row inside its denominator while 8/25 excluded two.** **Two rows are excluded here on the 8/25 practice and NAMED rather than quietly dropped: Jesús Luzardo o5.5 K (class 11/22 = 50.0%, result W) and Randy Vásquez u3.5 K (class 17/34 = 50.0%, result W).** ➡️ **The ten class tallies are therefore still NOT summable as published and are still reported as ten separate enumerated tallies.**

✅ **AND THE `cleared 1/2` CASE THE CONVENTION DOES NOT REACH — met on 8/30 and again on 8/31 — DID NOT ARISE AMONG THE GRADED ROWS THIS SLATE. The only `1/2` row on the card is Spencer Arrighetti's, and it is ungraded.** ⛔ **The convention is still owed an interactive decision; it simply had nothing to decide today.**

#### 🔴 FOUR ROWS WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED — AND THE CLASS TOOK THREE

| play | class (all) | head-to-head | result | which was right |
|---|---|---|---|---|
| Gavin Williams u17.5 outs vs TOR | 24/40 (60.0%) FOR | 0/1 AGAINST | **L** (21 outs) | ✅ **H2H** |
| Jesús Luzardo o6.5 K vs AZ | 6/22 (27.3%) AGAINST | 1/1 FOR | **L** (6 K) | ✅ **CLASS** |
| Michael McGreevy o15.5 outs vs LAD | 13/31 (41.9%) AGAINST | 1/1 FOR | **L** (15 outs) | ✅ **CLASS** |
| Ronel Blanco u14.5 outs vs CWS | 17/33 (51.5%) FOR | 0/1 AGAINST | **W** (12 outs) | ✅ **CLASS** |

⚠️ 🔴 **FOUR ROWS, EVERY HEAD-TO-HEAD SAMPLE A SINGLE START, AND THREE OF FOUR TO THE CLASS.** **Across the ten machine slates the conflicts run 2–2, four-of-five to the CLASS, three-of-three to the H2H, one-of-one to the H2H, one-of-one to the H2H, 2–2, NONE, 1–1, one-of-one to the H2H, now three-of-four to the CLASS.** ⛔ **Do not read a direction into that and do not set it beside the hand-carded note that the class has beaten the head-to-head 3/3 when they FLATLY DISAGREED — that note is about a TIEBREAKER being INVOKED and this is about a COLUMN being PRINTED on every row.** ⛔ **Different population, different trigger. Do not add them together.**

### 🔴🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **TENTH CONSECUTIVE RUN** — 🆕 **AND IT HAS NOW BITTEN ON THREE CONSECUTIVE SLATES**

`[re-checked 2026-09-02]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-09-01.json`.**

✅ **The gap was computed here instead, for all EIGHT arms carrying a prior meeting, by re-deriving each meeting from the repo's own stored log under a STARTS filter:**

| Pitcher | Opponent | Most recent prior START | Gap |
|---|---|---|---|
| 🔴 **MacKenzie Gore** | 🔴 **ATH** | 🔴 **2026-08-15** | 🔴 **17 days — INSIDE the 30-day window** |
| Jake Irvin | ATL | 2026-07-30 | 33 days |
| Ronel Blanco | CWS | 2026-07-26 | 37 days |
| Spencer Arrighetti | CLE | 2026-06-20 | 73 days |
| Troy Melton | MIN | 2026-06-09 | 84 days |
| Michael McGreevy | LAD | 2026-05-02 | 122 days |
| Gavin Williams | TOR | 2026-04-24 | 130 days |
| Jesús Luzardo | AZ | 2026-04-10 | 144 days |

🔴 **UNTIL 8/30 EVERY PRIOR MEETING ON EVERY MACHINE SLATE WAS 50+ DAYS OLD AND EVERY RUN COULD ADD "AND IT COST NOTHING". JANSON JUNK WAS THE FIRST EXCEPTION, RYAN GUSTO THE SECOND, AND MACKENZIE GORE IS THE THIRD — ON THREE CONSECUTIVE SLATES.** ⚠️ **And Jake Irvin at 33 days is three days outside a window nothing on the card measures.** ⛔ **REPORTED, NOT FIXED — a grading run does not touch the code and a headless session can neither test nor push a change.** ➡️ **Interactive fix, unchanged and now three-times-demonstrated: emit the gap in days on every row that has a prior meeting.**

✅ **The re-derivation doubles as a control on the card: every head-to-head string it printed reproduces exactly from the same log, 12/12 — again only once the filter is applied to STARTS (`gs == 1`) rather than to appearances, exactly as the 8/31 run recorded.**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS ITS SECOND ROW

⛔ **The hand-carded rule-51 table above is CARDED plays and stays at 2 clean instances / 1 confounded. A machine row may not be dropped into it.**

**Gore's rematch is a genuine ≤30-day instance and — unlike Gusto's on 8/31 — it is IN SCOPE, because he carded a STRIKEOUT row against the same lineup.** ⚠️ **It is an UNDER, which is the MIRROR of every instance logged so far, and that is stated on the row rather than absorbed.**

| date | play | threshold | opponent | first meeting | days since | W/L | actual K |
|---|---|---|---|---|---|---|---|
| 2026-09-01 | **MacKenzie Gore u6.5 K** *(TABLE M, machine card)* ⚠️ **an UNDER — the mirror of every prior instance** | 6.5 (a **7+ K** bar to lose) | ATH | **2026-08-15 — 5 K** in 17 outs | 🔴 **17** | ✅ **HIT** (the under cashed) | **4 K** (5.1 IP, 95 pitches, 25 BF) |

⚠️ **The exploratory threshold haircut predicts a rematch makes a HIGH bar HARDER to clear, which on an UNDER means the under is MORE likely — and it cashed.** ⛔ **ONE ROW, on a different population from the pre-registered test, in the opposite direction from every row logged before it, and the pre-registered mean-K specification is still FAILED and still CLOSED. Nothing is promoted.**

⚠️ **For the record and in no tally: his same-day OUTS row against the same lineup (u17.5 outs, W at 16 outs) is OUTSIDE rule 51's scope on the 8/22 Cease precedent.**

### 🟡 THE `carried` SHADOW — 9/1. 🔴 **WORSE AGAIN, ON NINE ROWS — A FIFTH CONSECUTIVE "WORSE".** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 9 of the 24 graded rows — every one the `T22` shuttled-starter warning, across SEVEN pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Sean Manaea u18.5 outs | 75.8% | 61.4% | **W** | **blend** |
| Gabriel Hughes o14.5 outs | 74.0% | 59.6% | **L** | **carried** |
| Robert Gasser o3.5 K | 73.3% | 58.9% | **W** | **blend** |
| Randy Vásquez u3.5 K | 66.1% | 51.7% | **W** | **blend** |
| Randy Dobnak o3.5 K | 62.6% | 48.2% | **W** | **blend** |
| Eric Lauer o15.5 outs | 62.0% | 47.6% | **L** | **carried** |
| Ronel Blanco u4.5 K | 61.8% | 47.4% | **W** | **blend** |
| Randy Vásquez o14.5 outs | 56.4% | 42.0% | **L** | **carried** |
| Ronel Blanco u14.5 outs | 55.2% | 40.8% | **W** | **blend** |

| | Brier over all 24 graded rows | Brier over the 9 rows that differ |
|---|---|---|
| `blend` | 🔴 **.2260** | 🔴 **.2202** |
| `carried` | **.2353** | **.2450** |
| Verdict | 🔴 **`carried` is WORSE by .0093** | 🔴 **`carried` is WORSE by .0248** |

⛔ **NINE ROWS FROM SEVEN PITCHERS, TWO OF THEM CONTRIBUTING TWO EACH. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **THE MECHANISM IS THE SAME ONE FOR THE TENTH TIME: six of the nine differing rows WON, and `carried` is ALWAYS the LOWER number, so it loses for being pessimistic on a good subset exactly as it won on 8/25 and 8/26 for being pessimistic on bad ones.** ⛔ **Ten slates, seven verdicts, and every single one is explained by whether that night's T22-flagged rows happened to win.**

➡️ **RUNNING ACROSS THE TEN MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 56 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27, 9 on 8/28, 2 on 8/29, 7 on 8/30, 8 on 8/31, 9 on 9/1 — and the verdict is WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE, WORSE, WORSE, WORSE, WORSE.** ⚠️ **On every one of the ten nights the differing rows were concentrated in a handful of pitchers. Fifty-six correlated rows is not a measurement; it is still the beginning of one.**

### 🔴🔴 🆕 THE DUPLICATE-TICKET DEFECT IS NON-DETERMINISTIC, AND THAT IS WORSE THAN A STABLE DEFECT

`[measured 2026-09-02 by diffing the two writes of the SAME card]` **The 14:08 write emitted 8 pairs that are only FIVE distinct tickets and 24 parlays that are only SEVENTEEN distinct (6 two-leg, 5 three-leg, 4 four-leg). The surviving 18:41 write — built from BYTE-IDENTICAL `picks[]`, zero rows differing on `blend`, `carried`, `price` or `book` — emitted 8 DISTINCT pairs and 24 DISTINCT parlays.**

🔴 **SAME BOARD, FOUR HOURS APART, DIFFERENT TICKET POOLS.** ⛔ **The 8/30 block guessed the cause was a pitcher carded on two rows entering the pool twice, and the 8/31 block refuted the Logan Gilbert half of that while keeping the SHAPE. Today's evidence says the shape is not sufficient either: the 18:41 board has the same double-carded pitchers and no duplicates at all.** ➡️ **Whatever the cause, it is not a function of the board alone.** ⛔ **REPORTED, NOT FIXED. An accumulator that counts printed tickets would double-weight a ticket on some runs and not others.**

### ✅ 🆕 ONE LONG-STANDING CODE DEFECT IS GONE, AND IT IS RECORDED BECAUSE EVERY GRADING RUN SINCE 8/24 HAS RE-REPORTED IT

🔴 **`card.py`'s `calibration_warning` NO LONGER QUOTES HARD-CODED FIGURES.** **`calibration_sentence()` now builds the banner from `data/latest/record.json` and FAILS TO SILENCE rather than to a stale number — its own docstring says so — and the 9/1 card carries the live figures (under-60 47.9% n=71; 60-70 51.7% n=87; 70-80 68% n=25) with an explicit small-sample hedge.** ⛔ **The struck −25.9 / −18.0 constants and the false claim that "only the 70-80% band has a record that supports its own number" are gone from the surface.** ⚠️ **Still open and re-reported: `in_band` is computed against `TARGET = 2.10` while `PARLAY_BANDS[2]` is `(1.80, 2.20)` and `parlay_rule` prose says 1.8x–2.2x — a THREE-way disagreement inside one file, open since 8/26; and `floor_ok` / `clears_price_floor` still write `price > -700`, excluding exactly −700.** ✅ **Neither bit this slate: the highest pair multiplier is 1.941x and the highest two-leg parlay 1.951x, so nothing lands between 2.10 and 2.20.**

~~**Progress: TABLE M — 10 slates, 209 graded pitcher plays, 70 graded pairs. TABLE M-H — 9 slates, 242 graded hitter rows.**~~ ⚠️ 🔴 **SUPERSEDED 2026-09-03 by the 9/2 block immediately below — the counter now reads TABLE M 11 slates / 234 GRADED pitcher plays / 78 graded pairs, and TABLE M-H 10 slates / 264 graded hitter rows. KEPT, NOT DELETED: this is the state of the accumulator after ten slates.**

---

## 🆕 2026-09-03 — THE ELEVENTH MACHINE SLATE (2026-09-02): THE FIRST CARD EVER WRITTEN EXACTLY ONCE, `carried` BETTER FOR THE FIRST TIME IN SIX SLATES, CHECK 36's DEFECT BITING ON FOUR CONSECUTIVE SLATES AND ON TWO ARMS AT ONCE, AND A TICKET POOL THAT WENT 0-FOR-EVERYTHING OFF ONE LEG

`[graded 2026-09-03]` ✅ **`picks/2026-09-02.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 14 GAMES.** **`50 = 25 + 25` ✅.**

✅ 🆕 **AND FOR THE FIRST TIME IN THE PROJECT'S HISTORY THE FILE WAS WRITTEN EXACTLY ONCE: `git log` on a FULLY UNSHALLOWED clone names ONE commit, `90c2142` at `2026-09-02T14:09:54Z` (`generated_at 14:09:41Z`), pre-slate against an earliest `commence` of `16:41:00Z`, with `coverage_detail.skipped` carrying no `"already started"` key at all.** ⛔ **THE CODE IS UNCHANGED AND SO IS THE HAZARD — a mechanism that had no second run to fire has not been fixed, and the interactive decision owed since 8/27 is owed a SIXTH time.** ✅ **Full provenance in `claude/pick-ledger.md`.**

⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24 through 9/1: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in the ledger — 16/22, three rows ungraded because Freddy Fermin, Tommy White and Ryan Waldschmidt did not play — and nothing here counts them.** **Their gap is −10.3.** ⚠️ 🔴 **AND A CHECK-28 DEFECT IN THAT TABLE'S RUNNING GAP LINE WAS FOUND BY THIS RUN AND REPORTED RATHER THAN PROPAGATED — it has said "eight comparable gaps" for two runs while ENUMERATING SIX, because the 8/29 and 8/30 figures were never added to the list.** ⛔ **No figure was invented to close it. The ledger now states the ENUMERATED set without a count.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **ELEVENTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23 through 9/2, so the CARDED denominator has not moved for eleven consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Folding in the machine card's 25 pitcher rows would take the counter past 56 without a single carded play, which is a silent re-specification of a pre-registered test. It is not done.**

⚠️ 🔴 **THE DROUGHT IS NOW TWELVE DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.**

⚠️ 🔴 **AND WHAT THE MACHINE SLATE SHOWED IS RECORDED HERE AND NOT FOLDED IN — IT IS THE MIRROR OF YESTERDAY'S, WHICH IS THE POINT.** **Over its 25 graded rows the mean `model` is 59.4, the mean `raw` 67.1, the mean `blend` 63.2 and the actual 48.0%, with Brier `model` .2674 · `blend` .2885 · `raw` .3264 · `carried` .2679.** 🔴 **MODEL "wins" today for exactly the reason it won on 8/22 and 8/30 and lost on 8/31: it was the LOWER of the two estimates on 18 of the 25 rows and the slate went 12/25.** ⛔ **Yesterday's board read a blend gap of −0.3 and today's reads -15.2 from the same instrument on the same population. Two consecutive slates, opposite verdicts, one day-tracking artifact — and it is not evidence about the blend weight.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 9/2 card carries Hard Rock alt ladders on 13 of its 25 pitcher rows — 103 rungs across 19 distinct starts.** 🔴 **IT IS NOT MERGED, for the eleventh time and for the same reason: T11's `n` is CARDED arms and the machine board is every qualifying starter.** ➡️ **A machine shadow ladder must be PRE-REGISTERED as its own entry in `claude/owed-tests.md`, in an interactive session.** ⛔ **Do not merge first and register afterwards.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket table:**

**Griffin Jax (1 K) · Cody Bradford (3 K) · Grant Holmes (1 K) · Dylan Cease (4 K) · Eury Pérez (3 K) · Jacob Lopez (7 K) · Drew Anderson (5 K) · Joey Cantillo (6 K) · Landen Roupp (4 K) · Andrew Painter (6 K) · Bryce Miller (3 K) · Casey Mize (4 K) · Jacob Misiorowski (5 K) · Hayden Wesneski (5 K) · Noah Cameron (7 K) · Cam Schlittler (9 K) · Reid Detmers (8 K) · Dean Kremer (5 K) · Davis Martin (3 K)** — **19 distinct (pitcher, date) pairs, all 2026-09-02, none of which appears in the 8/20, 8/21 or 8/22 passes.** ✅ **And unlike 9/1 there is no exclusion to declare: every one of the 19 carded arms STARTED.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/2. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/1 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **24** *(1 row excluded — see below)* | **15/24** | ⚠️ **a coin flip again — 15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, 15/22, now 15/24 across eleven slates** |
| **Head-to-head** (prior meetings) | **11** | **7/11** | ⚠️ **nine of the eleven are n=1 and two are n=2** |
| **Head-to-head, NO CALL — n=0** | **11** | — | ⛔ **logged and in no tally** |
| 🔴 **Head-to-head, NO CALL — the published convention DOES NOT REACH THEM** | 🔴 **3** | — | ⛔ **see below** (`11 + 11 + 3 = 25` ✅) |

🔴 **THE `cleared 1/2` CASE FIRST MET ON 8/30 AND SEEN AGAIN ON 8/31 RECURS, AND ON THE LARGEST SET YET — 3 ROWS, none of them a MAJORITY and none of them NONE, and the convention is silent on all three: Grant Holmes vs Washington Nationals (u4.5 K) · Jacob Lopez vs Texas Rangers (u16.5 outs) · Jacob Lopez vs Texas Rangers (u5.5 K).** ⛔ **Recorded as NO CALL, the literal reading of the published rule and the choice that invents nothing.** ➡️ **An interactive session should settle it; a grading run does not write a new convention mid-tally, and it does not write one on the third sighting either.** ⚠️ **It matters more than it did: reading `1/2` as FOR would make the head-to-head tally 8/14 instead of 7/11.**

⛔ 🔴 **AND A SECOND CASE THE PUBLISHED CONVENTION DOES NOT REACH, MET FOR THE FIRST TIME ON A GRADED MACHINE ROW: Dylan Cease o6.5 K CARRIES `class n=0` — NO RATE AT ALL, not a rate sitting on the boundary.** **A class with no observations cannot argue FOR or AGAINST by construction.** ✅ **EXCLUDED and NAMED rather than quietly dropped or counted as a boundary row (his result was L).** ⚠️ **The 8/25 boundary-row inconsistency is STILL unchanged and unresolved — 8/23 kept its 50.0% row inside its denominator while 8/25 excluded two — so the eleven class tallies are still NOT summable as published and are still reported as eleven separate enumerated tallies.**

#### 🔴 5 ROWS WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED — AND THE CLASS TOOK 3

| play | class (all) | head-to-head | result | which was right |
|---|---|---|---|---|
| Joey Cantillo u15.5 outs vs Toronto Blue Jays | 3/9 (33.3%) AGAINST | 1 start(s) vs TOR -- cleared 1/1 FOR | **L** | ✅ **CLASS** |
| Landen Roupp u5.5 K vs Pittsburgh Pirates | 43/76 (56.6%) FOR | 1 start(s) vs PIT -- cleared 0/1 AGAINST | **W** | ✅ **CLASS** |
| Landen Roupp o15.5 outs vs Pittsburgh Pirates | 23/40 (57.5%) FOR | 1 start(s) vs PIT -- cleared 0/1 AGAINST | **L** | ✅ **H2H** |
| Reid Detmers u6.5 K vs New York Yankees | 31/57 (54.4%) FOR | 1 start(s) vs NYY -- cleared 0/1 AGAINST | **L** | ✅ **H2H** |
| Dean Kremer o4.5 K vs Detroit Tigers | 40/78 (51.3%) FOR | 1 start(s) vs DET -- cleared 0/1 AGAINST | **W** | ✅ **CLASS** |

⚠️ 🔴 **5 ROWS, EVERY HEAD-TO-HEAD SAMPLE A SINGLE START, AND 3 OF 5 TO THE CLASS.** **Across the eleven machine slates the conflicts run 2–2, four-of-five to the CLASS, three-of-three to the H2H, one-of-one to the H2H, one-of-one to the H2H, 2–2, NONE, 1–1, one-of-one to the H2H, three-of-four to the CLASS, now three-of-five to the CLASS.** ⛔ **Do not read a direction into that and do not set it beside the hand-carded note that the class has beaten the head-to-head 3/3 when they FLATLY DISAGREED — that note is about a TIEBREAKER being INVOKED and this is about a COLUMN being PRINTED on every row.** ⛔ **Different population, different trigger. Do not add them together.**
### 🔴🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **ELEVENTH CONSECUTIVE RUN** — 🆕 **AND IT HAS NOW BITTEN ON FOUR CONSECUTIVE SLATES, THIS TIME ON TWO ARMS AT ONCE**

`[re-checked 2026-09-03]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-09-02.json`.**

✅ **The gap was computed here instead, for every arm carrying a prior meeting, by re-deriving each meeting from the repo's own stored log under a STARTS (`gs == 1`) filter:**

| Pitcher | Opponent | Most recent prior START | Gap |
|---|---|---|---|
| 🔴 **Cody Bradford** | 🔴 **Athletics** | 🔴 **2026-08-16** | 🔴 **17 days — INSIDE the 30-day window** |
| 🔴 **Jacob Lopez** | 🔴 **Texas Rangers** | 🔴 **2026-08-16** | 🔴 **17 days — INSIDE the 30-day window** |
| Grant Holmes | Washington Nationals | 2026-07-30 | 34 days |
| Dean Kremer | Detroit Tigers | 2026-07-28 | 36 days |
| Davis Martin | Houston Astros | 2026-07-24 | 40 days |
| Jacob Misiorowski | Chicago Cubs | 2026-06-26 | 68 days |
| Bryce Miller | Boston Red Sox | 2026-06-19 | 75 days |
| Landen Roupp | Pittsburgh Pirates | 2026-05-09 | 116 days |
| Joey Cantillo | Toronto Blue Jays | 2026-04-25 | 130 days |
| Reid Detmers | New York Yankees | 2026-04-14 | 141 days |

🔴 **UNTIL 8/30 EVERY PRIOR MEETING ON EVERY MACHINE SLATE WAS 50+ DAYS OLD AND EVERY RUN COULD ADD "AND IT COST NOTHING". JANSON JUNK WAS THE FIRST EXCEPTION, RYAN GUSTO THE SECOND, MACKENZIE GORE THE THIRD — AND TODAY THERE ARE TWO IN ONE SLATE: Cody Bradford vs Athletics AT 17 DAYS AND Jacob Lopez vs Texas Rangers AT 17 DAYS.** ⛔ **FOUR CONSECUTIVE SLATES, and the card said nothing on any of them.** ⛔ **REPORTED, NOT FIXED — a grading run does not touch the code and a headless session can neither test nor push a change.** ➡️ **Interactive fix, unchanged and now four-times-demonstrated: emit the gap in days on every row that has a prior meeting.**

✅ **The re-derivation doubles as a control on the card: every head-to-head string it printed reproduces EXACTLY from the same log, 25/25 — again only once the filter is applied to STARTS (`gs == 1`) rather than to appearances, exactly as the 8/31 and 9/1 runs recorded.**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS ITS THIRD AND FOURTH ROWS — AND THEY POINT OPPOSITE WAYS

⛔ **The hand-carded rule-51 table above is CARDED plays and stays at 2 clean instances / 1 confounded. A machine row may not be dropped into it.**

**Both rematches are IN SCOPE, because each arm carded a STRIKEOUT row against the same lineup.** ⚠️ **Both are UNDERS, like the 9/1 Gore row and unlike the 8/30 Junk row, and that is stated rather than absorbed.**

| date | play | threshold | opponent | first meeting | days since | W/L | actual K |
|---|---|---|---|---|---|---|---|
| 2026-09-02 | **Cody Bradford u4.5 K** *(TABLE M, machine card)* ⚠️ **an UNDER** | 4.5 (a **5+ K** bar to lose) | Athletics | **2026-08-16 — 4 K** in 12 outs ⚠️ **WEAK first meeting (<5 K)** | 🔴 **17** | ✅ **HIT** (the under cashed) | **3 K** (4.0 IP, 86 P, 20 BF) |
| 2026-09-02 | **Jacob Lopez u5.5 K** *(TABLE M, machine card)* ⚠️ **an UNDER** | 5.5 (a **6+ K** bar to lose) | Texas Rangers | **2026-08-16 — 6 K** in 18 outs 🔴 **STRONG first meeting (≥5 K)** | 🔴 **17** | ❌ **MISS** (the under lost) | **7 K** (6.0 IP, 102 P, 25 BF) |

⚠️ 🔴 **AND THEY SPLIT, WHICH IS THE MOST USEFUL THING ABOUT THEM.** **The exploratory threshold haircut says a rematch makes a HIGH bar HARDER to clear, which on an UNDER means the under is MORE likely.** **Bradford's under cashed — the predicted direction — off a WEAK 4-K first meeting that does not even test the "strong ≥5 K first meeting" conditional. Lopez's under LOST off a STRONG 6-K first meeting, which is the conditional the exploratory finding is actually about, and it went the wrong way.** ⛔ **TWO ROWS, on a population the pre-registered test does not cover, pointing in opposite directions. The pre-registered mean-K specification is still FAILED and still CLOSED. Nothing is promoted.**

⚠️ **For the record and in no tally: both men also carded an OUTS row against the same lineup on the same day — Bradford u17.5 outs (W at 12 outs) and Lopez u16.5 outs (L at 18 outs). OUTS ARE OUTSIDE RULE 51'S SCOPE on the 8/22 Cease precedent, so they are named and counted nowhere.**
### 🟡 THE `carried` SHADOW — 9/2. 🔴 **BETTER FOR THE FIRST TIME IN SIX SLATES — AND BY THE SAME MECHANISM THAT MADE IT WORSE FIVE TIMES RUNNING.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 10 of the 25 graded rows — the largest differing set this table has recorded — every one the `T22` shuttled-starter warning, across 7 pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Griffin Jax o11.5 outs | 86.7% | 72.3% | **L** | **carried** |
| Grant Holmes u4.5 K | 71.0% | 56.6% | **W** | **blend** |
| Griffin Jax o4.5 K | 67.9% | 53.5% | **L** | **carried** |
| Jacob Lopez u16.5 outs | 66.8% | 52.4% | **L** | **carried** |
| Drew Anderson u14.5 outs | 66.4% | 52.0% | **L** | **carried** |
| Grant Holmes u15.5 outs | 60.3% | 45.9% | **W** | **blend** |
| Andrew Painter o3.5 K | 59.8% | 45.4% | **W** | **blend** |
| Bryce Miller o15.5 outs | 60.3% | 45.9% | **L** | **carried** |
| Noah Cameron u17.5 outs | 56.4% | 42.0% | **W** | **blend** |
| Jacob Lopez u5.5 K | 55.1% | 40.7% | **L** | **carried** |

| | Brier over all 25 graded rows | Brier over the 10 rows that differ |
|---|---|---|
| `blend` | **.2885** | **.3360** |
| `carried` | 🔴 **.2679** | 🔴 **.2846** |
| Verdict | 🔴 **`carried` is BETTER by .0206** | 🔴 **`carried` is BETTER by .0515** |

⛔ **10 ROWS FROM 7 PITCHERS, THREE OF THEM CONTRIBUTING TWO EACH. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **AND THE MECHANISM IS THE SAME ONE FOR THE ELEVENTH TIME, WHICH IS PRECISELY WHY THE SIGN FLIPPING TODAY IS NOT NEWS: 6 of the 10 differing rows LOST, and `carried` is ALWAYS the LOWER number, so it wins for being pessimistic on a bad subset exactly as it lost the last five times for being pessimistic on good ones.** ⛔ **Eleven slates, eight verdicts, and every single one is explained by whether that night's T22-flagged rows happened to win.** ⛔ **A proper scoring rule does not immunise a one-slate result against a day-tracking artifact — this page has said so since 8/25 and today is the cleanest confirmation of it, because the flip required no change in T22 at all.**

➡️ **RUNNING ACROSS THE ELEVEN MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 66 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27, 9 on 8/28, 2 on 8/29, 7 on 8/30, 8 on 8/31, 9 on 9/1, 10 on 9/2 — and the verdict is WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE, WORSE, WORSE, WORSE, WORSE, BETTER.** ⚠️ **On every one of the eleven nights the differing rows were concentrated in a handful of pitchers. 66 correlated rows is not a measurement; it is still the beginning of one.**

### 🔴🔴 🆕 A TICKET-POOL DEFECT THAT NO ACCUMULATOR ON THIS PAGE WOULD HAVE CAUGHT, AND IT IS THE REASON TO NAME IT HERE

🔴 **THE 9/2 PAIRS WENT 0/8 AND THE PARLAYS 0/24 — the first total wipeout on either surface — AND BOTH HAVE ONE CAUSE: 7 of the 8 pairs and 23 of the 24 parlays carry the SAME LEG, Griffin Jax o11.5 outs, the board's highest-confidence pitcher row at blend 86.7, who recorded 8 OUTS.** **The single ticket without him carries Dylan Cease o5.5 K, which also lost.**

➡️ 🔴 **THE STRUCTURAL POINT: `parlay_meta` says the pool takes the 12 highest-confidence legs from each of five PRICE BANDS, so the board's top row enters nearly every ticket in the pool.** **A pool built that way cannot diversify, and its aggregate record measures one leg's luck rather than the pool's.** ⛔ **So 0/24 is ONE failed leg reported twenty-four times.** ⚠️ **Any future pair or parlay accumulator that reads printed tickets as independent observations will be badly wrong, and this is a SECOND, INDEPENDENT reason for that beyond the byte-identical-duplicate defect logged on 8/30, 8/31 and 9/1.** ⛔ **REPORTED, NOT FIXED — a grading run does not touch the code.** ✅ **The duplicate defect itself did NOT bite this slate: 8 pairs and 24 parlays, all distinct.**

⚠️ **Also re-reported and unchanged: `card.py`'s `in_band` flag is still computed against 2.10 while `PARLAY_BANDS[2]` is `(1.80, 2.20)` and `parlay_rule` prose says 1.8x–2.2x.** 🔴 **IT BIT THIS SLATE, for the first time in three runs: two pairs at 2.107x and five two-leg parlays between 2.10x and 2.20x are ABOVE BAND by the flag and INSIDE BAND by the same file's prose.** ⛔ **The ledger reports the FLAG, as every prior slate has. An interactive session must pick one ceiling — open since 2026-08-26.**

~~**Progress: TABLE M — 11 slates, 234 graded pitcher plays, 78 graded pairs. TABLE M-H — 10 slates, 264 graded hitter rows.**~~ ⚠️ 🔴 **SUPERSEDED 2026-09-04 by the 9/3 block immediately below — the counter now reads TABLE M 12 slates / 259 GRADED pitcher plays / 86 graded pairs, and TABLE M-H 11 slates / 289 graded hitter rows. KEPT, NOT DELETED: this is the state of the accumulator after eleven slates.**


## 🆕 2026-09-04 — THE TWELFTH MACHINE SLATE (2026-09-03): A SECOND CONSECUTIVE CARD WRITTEN EXACTLY ONCE, THE BEST-CALIBRATED MACHINE BOARD ON RECORD, `carried` WORSE AGAIN BY THE SAME MECHANISM THAT MADE IT BETTER YESTERDAY, AND CHECK 36's DEFECT PRESENT BUT COSTING NOTHING FOR THE FIRST TIME IN FIVE SLATES

`[graded 2026-09-04]` ✅ **`picks/2026-09-03.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 9 GAMES.** **`50 = 25 + 25` ✅.**

✅ **AND FOR A SECOND CONSECUTIVE DAY THE FILE WAS WRITTEN EXACTLY ONCE: `git log` on a FULLY UNSHALLOWED clone (999 commits, no `.git/shallow`) names ONE commit, `59447b1` at `2026-09-03T14:08:47Z` (`generated_at 14:08:36Z`), pre-slate against an earliest `commence` of `16:35:00Z`, with `coverage_detail.skipped` carrying no `"already started"` key at all.** ⛔ **THE CODE IS UNCHANGED AND SO IS THE HAZARD — two runs that had no second write to collide with is not a fix, and the interactive decision owed since 8/27 is owed a SEVENTH time.** ✅ **Full provenance in `claude/pick-ledger.md`.**

⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24 through 9/2: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in the ledger — 17/25, with ZERO rows ungraded because every carded hitter batted — and nothing here counts them.** **Their gap is −9.6.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **TWELFTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23 through 9/3, so the CARDED denominator has not moved for twelve consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Folding in the machine card's 25 pitcher rows would take the counter past 56 without a single carded play, which is a silent re-specification of a pre-registered test. It is not done.**

⚠️ 🔴 **THE DROUGHT IS NOW THIRTEEN DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.**

⚠️ 🔴 **AND WHAT THE MACHINE SLATE SHOWED IS RECORDED HERE AND NOT FOLDED IN.** **Over its 25 graded rows the mean `model` is 65.2, the mean `raw` 63.0, the mean `blend` 64.1 and the actual 64.0%, with Brier `model` .2003 · `blend` .2170 · `raw` .2381 · `carried` .2409.** 🔴 **MODEL "wins" AGAIN — its fourth consecutive win on this board — but for a different reason than yesterday's, and that is exactly why it is not evidence: on 9/2 model won by being the LOWER estimate on a slate that went 12/25, and today it wins on a slate that went 16/25 while being HIGHER than raw on average.** ⛔ **A one-slate Brier ordering on 25 correlated rows is a day-tracking artifact in both directions and it says nothing about the blend weight.** ⚠️ **Four consecutive full boards read a blend gap of −22.0, −0.3, −15.2 and now −0.1 — a sequence that ALTERNATES rather than converges.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 9/3 card carries Hard Rock alt ladders on 15 of its 25 pitcher rows — 115 rungs across 14 distinct starts.** 🔴 **IT IS NOT MERGED, for the twelfth time and for the same reason: T11's `n` is CARDED arms and the machine board is every qualifying starter.** ➡️ **A machine shadow ladder must be PRE-REGISTERED as its own entry in `claude/owed-tests.md`, in an interactive session.** ⛔ **Do not merge first and register afterwards.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket table:**

**Lake Bachar (3 K) · José Soriano (2 K) · Tarik Skubal (6 K) · Tanner Bibee (4 K) · Cal Quantrill (5 K) · Sandy Alcantara (2 K) · Hunter Brown (7 K) · Luis Castillo (3 K) · Michael Wacha (7 K) · Shane McClanahan (3 K) · Jack Perkins (7 K) · Kevin Gausman (9 K) · Logan Henderson (7 K) · Brandon Young (7 K)** — **14 distinct (pitcher, date) pairs, all 2026-09-03, none of which appears in the 8/20, 8/21 or 8/22 passes.** ⚠️ **15 carded ROWS carry a ladder but only 14 distinct ARMS do, because Tarik Skubal carries two laddered rows.** 📐 **`n` IS DISTINCT STARTS — 14 — NEVER THE RUNG COUNT.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/3. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/2 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **25** | **14/25** | ⚠️ **a coin flip again — 15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, 15/22, 15/24, now 14/25 across twelve slates** |
| **Head-to-head** (prior meetings) | **10** | **6/10** | ⚠️ **eight of the ten are n=1 and two are n=2** |
| **Head-to-head, NO CALL — n=0** | **13** | — | ⛔ **logged and in no tally** |
| 🔴 **Head-to-head, NO CALL — the published convention DOES NOT REACH THEM** | 🔴 **2** | — | ⛔ **see below** (`10 + 13 + 2 = 25` ✅) |

🔴 **THE `cleared 1/2` CASE FIRST MET ON 8/30 RECURS FOR A FOURTH TIME, on both of Luis Castillo's rows against Houston (u4.5 K and u15.5 outs) — neither a MAJORITY nor NONE, and the convention is silent on both.** ⛔ **Recorded as NO CALL, the literal reading of the published rule and the choice that invents nothing.** ➡️ **An interactive session should settle it; a grading run does not write a new convention mid-tally, and it does not write one on the fourth sighting either.** ⚠️ **Reading `1/2` as FOR would make the head-to-head tally 8/12 instead of 6/10 — both Castillo unders cashed.**

#### 🔴 FIVE ROWS WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED — AND THEY SPLIT THREE–TWO TO THE HEAD-TO-HEAD

| Play | Matched class | Head-to-head | Result | Which was right |
|---|---|---|---|---|
| **Lake Bachar o5.5 outs** | **19/22 = 86.4% → FOR** | **0/1 → AGAINST** | **W** ✅ | **the class** |
| **Lake Bachar o1.5 K** | **43/45 = 95.6% → FOR** | **0/1 → AGAINST** | **W** ✅ | **the class** |
| **Hunter Brown u6.5 K** | **40/67 = 59.7% → FOR** | **0/1 → AGAINST** | **L** ❌ | **the head-to-head** |
| **Hunter Brown u17.5 outs** | **25/49 = 51.0% → FOR** | **0/1 → AGAINST** | **L** ❌ | **the head-to-head** |
| **Brandon Young o4.5 K** | **24/60 = 40.0% → AGAINST** | **1/1 → FOR** | **W** ✅ | **the head-to-head** |

**FIVE disagreeing rows: the class right on 2, the head-to-head right on 3** — `2 + 3 = 5` ✅, counted against the rows above (ledger rule 45). ⚠️ **AND THE FIVE ARE NOT FIVE INDEPENDENT CALLS: both Bachar rows rest on the same arm and the same single n=1 meeting, and both Brown rows likewise, so this is really THREE independent disagreements — Bachar (class right), Brown (head-to-head right) and Young (head-to-head right).** ⛔ **Stated rather than averaged or weighted.**

### 🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **TWELFTH CONSECUTIVE RUN** — ✅ 🆕 **AND FOR THE FIRST TIME IN FIVE SLATES IT COST NOTHING, WHICH WAS MEASURED RATHER THAN ASSUMED**

`[re-checked 2026-09-04]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-09-03.json`.**

✅ **The gap was computed here instead, for every arm carrying a prior meeting, by re-deriving each meeting from the repo's own stored log under a STARTS (`gs == 1`) filter:**

| Pitcher | Opponent | Most recent prior START | Gap |
|---|---|---|---|
| Shane McClanahan | Texas Rangers | 2026-07-30 | **35 days** — the closest on the board |
| Cal Quantrill | Tampa Bay Rays | 2026-07-28 | 37 days |
| Hunter Brown | Chicago White Sox | 2026-07-25 | 40 days |
| Lake Bachar | San Francisco Giants | 2026-06-19 | 76 days |
| Luis Castillo | Houston Astros | 2026-05-14 | 112 days |
| Brandon Young | Boston Red Sox | 2026-04-24 | 132 days |
| Kevin Gausman | Milwaukee Brewers | 2026-04-14 | 142 days |

✅ 🔴 **NOT ONE PRIOR MEETING ON THIS BOARD IS INSIDE THIRTY DAYS — the closest is 35 — so the four-consecutive-slate biting streak (Junk, Gusto, Gore, then Bradford and Lopez together) ENDS HERE.** ⛔ **THE DEFECT IS UNCHANGED AND IS STILL REPORTED: a card that would say nothing on a 17-day rematch says nothing today only because there wasn't one.** ➡️ **Interactive fix, unchanged and now five-times-demonstrated: emit the gap in days on every row that has a prior meeting.**

✅ **The re-derivation doubles as a control on the card: every head-to-head string it printed reproduces EXACTLY from the same log, 25/25 — again only once the filter is applied to STARTS (`gs == 1`) rather than to appearances, exactly as the 8/31, 9/1 and 9/2 runs recorded.** ⚠️ **Jack Perkins is the row that proves the filter matters: he has a 2026-05-25 RELIEF appearance against Seattle and no prior START, and the card correctly prints "never faced SEA this season."**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS NO ROW, AND THE REASON IS THE GAP

⛔ **The hand-carded rule-51 table above is CARDED plays and stays at 2 clean instances / 1 confounded. A machine row may not be dropped into it.**

**The machine-population log stays at FOUR rows (8/30 Junk, 9/1 Gore, 9/2 Bradford and Lopez).** ✅ **No 9/3 row qualifies: rule 51's window is 30 days and the closest prior meeting on this board is 35.** ⛔ **A near-miss is not an instance and is not logged as one.**

### 🟡 THE `carried` SHADOW — 9/3. 🔴 **WORSE AGAIN — AND BY EXACTLY THE MECHANISM THAT MADE IT BETTER YESTERDAY.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 8 of the 25 graded rows, every one the `T22` shuttled-starter warning, across 5 pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Lake Bachar o5.5 outs | 89.5% | 75.1% | **W** | **blend** |
| Blade Tidwell o14.5 outs | 79.3% | 64.9% | **W** | **blend** |
| Lake Bachar o1.5 K | 77.8% | 63.4% | **W** | **blend** |
| Cal Quantrill o3.5 K | 66.3% | 51.9% | **W** | **blend** |
| Luis Castillo u4.5 K | 61.9% | 47.5% | **W** | **blend** |
| Jack Perkins u5.5 K | 60.4% | 46.0% | **L** | **carried** |
| Luis Castillo u15.5 outs | 57.8% | 43.4% | **W** | **blend** |
| Cal Quantrill o15.5 outs | 57.0% | 42.6% | **W** | **blend** |

| | Brier over all 25 graded rows | Brier over the 8 rows that differ |
|---|---|---|
| `blend` | 🔴 **.2170** | 🔴 **.1362** |
| `carried` | **.2409** | **.2109** |
| Verdict | 🔴 **`carried` is WORSE by .0239** | 🔴 **`carried` is WORSE by .0747** |

⛔ **8 ROWS FROM 5 PITCHERS, THREE OF THEM CONTRIBUTING TWO EACH. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **AND THE MECHANISM IS THE SAME ONE FOR THE TWELFTH TIME, WHICH IS WHY YESTERDAY'S FLIP WAS NOT NEWS EITHER: 7 of the 8 differing rows WON, and `carried` is ALWAYS the LOWER number, so it loses for being pessimistic on a good subset exactly as it won yesterday for being pessimistic on a bad one.** ⛔ **Twelve slates, nine verdicts, and every single one is explained by whether that night's T22-flagged rows happened to win.**

➡️ **RUNNING ACROSS THE TWELVE MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 74 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27, 9 on 8/28, 2 on 8/29, 7 on 8/30, 8 on 8/31, 9 on 9/1, 10 on 9/2, 8 on 9/3 — and the verdict is WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE, WORSE, WORSE, WORSE, WORSE, BETTER, WORSE.** ⚠️ **On every one of the twelve nights the differing rows were concentrated in a handful of pitchers. 74 correlated rows is not a measurement; it is still the beginning of one.**

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT NAMED YESTERDAY RECURS WITH THE SIGN FLIPPED, WHICH IS THE STRONGEST FORM OF THE ARGUMENT

🔴 **THE 9/3 PAIRS WENT 6/8 AND THE PARLAYS 14/24 — the best either surface has recorded — AND BOTH HAVE ONE CAUSE: 6 of the 8 pairs and ALL 24 of the parlays carry the SAME LEG, Lake Bachar o5.5 outs, the board's highest-confidence pitcher row at blend 89.5, who cleared with 7 outs on 38 pitches.**

➡️ 🔴 **YESTERDAY THIS PAGE WROTE THAT SUCH A POOL "CANNOT DIVERSIFY, AND ITS AGGREGATE RECORD MEASURES ONE LEG'S LUCK RATHER THAN THE POOL'S." TODAY THE SAME STRUCTURE PRODUCED THE OPPOSITE HEADLINE FROM THE SAME DEFECT.** ⛔ **14/24 is ONE winning leg reported twenty-four times, exactly as 9/2's 0/24 was one losing leg reported twenty-four times.** ⚠️ **A defect that only gets named on losing nights becomes an excuse; naming it on a winning night is the whole point of the accumulation protocol.** ⛔ **REPORTED, NOT FIXED — a grading run does not touch the code.** ✅ **The duplicate-ticket defect did NOT bite: 8 pairs and 24 parlays, all distinct — a third clean slate, which on 9/1's evidence is the defect not biting rather than the defect being fixed.**

⚠️ **Also re-reported and unchanged: `card.py`'s `in_band` flag is still computed against `TARGET = 2.10` while `PARLAY_BANDS[2]` is `(1.80, 2.20)` and `parlay_rule` prose says 1.8x–2.2x.** 🔴 **IT BIT ON CONSECUTIVE SLATES: pair 6 at 2.143x is ABOVE BAND by the flag and INSIDE BAND by the same file's prose.** ⛔ **The ledger reports the FLAG, as every prior slate has. An interactive session must pick one ceiling — open since 2026-08-26.**

✅ 🆕 **AND ONE DEFECT THIS PAGE HAS RE-REPORTED SINCE 8/24 IS GONE: `card.py`'s `calibration_warning` no longer hard-codes `−25.9 / −18.0`. It calls `calibration_sentence()`, and the 9/3 card carries computed machine-card band figures — correctly scoped to the MACHINE card and not to this project's TABLE A calibration.** ⚠️ **Recorded because a defect that stops being true and keeps being reported is its own error.**

**Progress: TABLE M — 12 slates, 259 graded pitcher plays, 86 graded pairs. TABLE M-H — 11 slates, 289 graded hitter rows.**


## 🆕 2026-09-05 — THE THIRTEENTH MACHINE SLATE (2026-09-04): A THIRD CONSECUTIVE CARD WRITTEN EXACTLY ONCE, THE WORST-CALIBRATED MACHINE BOARD ON RECORD, `carried` BETTER FOR THE SECOND TIME IN THIRTEEN SLATES BY THE SAME MECHANISM THAT MADE IT WORSE ELEVEN TIMES, AND CHECK 36's DEFECT BITING HARDER THAN IT EVER HAS

`[graded 2026-09-05]` ✅ **`picks/2026-09-04.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 15 GAMES.** **`50 = 25 + 25` ✅.**

✅ **AND FOR A THIRD CONSECUTIVE DAY THE FILE WAS WRITTEN EXACTLY ONCE: `git log` on a FULLY UNSHALLOWED clone (1,114 commits, no `.git/shallow`) names ONE commit, `91eac80` at `2026-09-04T14:07:27Z` (`generated_at 14:07:14Z`), pre-slate against an earliest `commence` of `18:11:00Z`, with `coverage_detail.skipped` carrying no `"already started"` key at all.** ⛔ **The overwrite mechanism is unchanged and simply had no second run to fire.**

🔴 **ONE OF THE 25 PITCHER ROWS IS UNGRADED AND IS THEREFORE IN NO ACCUMULATOR ON THIS PAGE: KUMAR ROCKER o3.5 K — he pitched in the carded game and WAS NOT THE STARTER (Texas opened with Trevor Williams; Rocker followed for 5.0 IP on 73 pitches).** ⛔ **Every tally in this block has a denominator of 24, and it says so.** ➡️ **The grading-mechanics question is set out in full in `claude/pick-ledger.md` and is NOT decided here.**

⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24 through 9/3: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in the ledger — 15/21, with 4 rows ungraded because those hitters did not play — and nothing here counts them.** **Their gap is −11.1.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **THIRTEENTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23 through 9/4, so the CARDED denominator has not moved for thirteen consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it: 31 carded plays / 100, argmin `w = 1.00` at Brier .2245 against .2338 at the shipped 0.5, margin 0.0094 — MARGIN leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.**

⚠️ 🔴 **THE DROUGHT IS NOW FOURTEEN DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.**

⚠️ 🔴 **AND WHAT THE MACHINE SLATE SHOWED IS RECORDED HERE AND NOT FOLDED IN.** **Over its 24 graded rows the mean `model` is 67.7, the mean `raw` 71.3, the mean `blend` 69.5 and the actual 41.7%, with Brier `carried` .2717 · `model` .2968 · `blend` .3158 · `raw` .3447.** 🔴 **MODEL beats BLEND beats RAW again — a fifth consecutive slate in which the pure model outscores the shipped 50/50 on the MACHINE population.** ⛔ **THAT IS NOT T15's DENOMINATOR AND MAY NOT BE MERGED INTO IT.** ⚠️ **On this slate every estimator is badly over-confident — the best Brier on the page belongs to `carried` purely for being the lowest number on a board that lost — so this is weak evidence about ordering and no evidence at all about level.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 9/4 card carries Hard Rock alt ladders on 12 of its 25 pitcher rows — 92 rungs across 12 distinct starts.** 🔴 **IT IS NOT MERGED, for the thirteenth time and for the same reason: T11's `n` is CARDED arms and the machine board is every qualifying starter.** ➡️ **A machine shadow ladder must be PRE-REGISTERED as its own test before it can accumulate anywhere.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket table:**

**Blake Snell (7 K) · Cristian Javier (8 K) · Erick Fedde (2 K) · Jared Jones (9 K) · Keider Montero (4 K) · Kumar Rocker (3 K) · Logan Gilbert (10 K) · Max Fried (4 K) · Merrill Kelly (4 K) · Nolan McLean (7 K) · Ranger Suarez (3 K) · Rhett Lowder (2 K)** — **12 NAMED STARTS, deduplicated on (pitcher, date).** ⚠️ **Kumar Rocker is named here because rule 35 counts STARTS SEEN, and his appearance is recorded with the caveat that HE DID NOT START; a registered pass must decide whether a relief outing belongs in a starter shadow ladder at all.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/4. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/3 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared, AGAINST when none did, and makes NO CALL at n=0.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **24** | 🔴 **10/24** | ⚠️ **a coin flip again, and its worst reading yet — 15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, 15/22, 15/24, 14/25, now 10/24 across thirteen slates** |
| **Head-to-head** (prior meetings) | **6** | **2/6** | ⚠️ **two are n=1 and four are n=2** |
| **Head-to-head, NO CALL — n=0** | **15** | — | ⛔ **logged and in no tally** |
| 🔴 **Head-to-head, NO CALL — the published convention DOES NOT REACH THEM** | 🔴 **3** | — | ⛔ **see below** (`6 + 15 + 3 = 24` ✅) |

🔴 **THE `cleared 1/2` CASE FIRST MET ON 8/30 RECURS FOR A FIFTH TIME, on three rows — Erick Fedde o2.5 K vs MIN, Keider Montero o2.5 K and o15.5 outs vs CLE — neither a MAJORITY nor NONE, and the convention is silent on all three.** ⛔ **Recorded as NO CALL, the literal reading of the published rule and the choice that invents nothing.** ➡️ **An interactive session should extend the convention; a grading run may not.**

#### 🔴 ONE ROW WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED, AND THE HEAD-TO-HEAD WON

| Play | Matched class | Head-to-head | Result | Which was right |
|---|---|---|---|---|
| **Cristopher Sánchez u18.5 outs** | **6/13 = 46.2% → AGAINST** | **1/1 → FOR** | **W** ✅ | **the head-to-head** |

**ONE disagreeing row: the class right on 0, the head-to-head right on 1** — `0 + 1 = 1` ✅, counted against the row above (ledger rule 45). ⚠️ **It rests on a single n=1 meeting and is worth almost nothing on its own.**

### 🔴🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **THIRTEENTH CONSECUTIVE RUN** — 🔴 **AND IT HAS NEVER BITTEN HARDER: THE BOARD CARRIED A SIX-DAY REMATCH**

`[re-checked 2026-09-05]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the substring `days` appears ZERO times anywhere in `picks/2026-09-04.json`.**

✅ **The gap was computed here instead, for every arm carrying a prior meeting, by re-deriving each meeting from the repo's own stored log under a STARTS (`gs == 1`) filter:**

| Pitcher | Opponent | Most recent prior START | Gap |
|---|---|---|---|
| 🔴 **Erick Fedde** | **Minnesota Twins** | **2026-08-29** | 🔴 **6 days — THE SHORTEST GAP THIS PROJECT HAS EVER RECORDED** |
| 🔴 **Keider Montero** | **Cleveland Guardians** | **2026-08-13** | 🔴 **22 days** |
| Rhett Lowder | Milwaukee Brewers | 2026-06-30 | 66 days |
| Shane Drohan | Cincinnati Reds | 2026-07-01 | 65 days |
| Logan Gilbert | Athletics | 2026-05-27 | 100 days |
| Cristopher Sánchez | Atlanta Braves | 2026-04-18 | 139 days |
| Nolan McLean | San Francisco Giants | 2026-04-03 | 154 days |

🔴🔴 **TWO ROWS ARE INSIDE RULE 51's THIRTY-DAY WINDOW AND THE CARD SAID NOTHING ABOUT EITHER.** ⛔ **Six days is not a near-miss; it is the tightest rematch the project has seen, and the card printed `2 start(s) vs MIN -- cleared 1/2` with no indication that one of those two was LAST WEEK.**

✅ **The re-derivation doubles as a control on the card: every head-to-head string it printed reproduces EXACTLY from the same log, 18/18 distinct (pitcher, opponent) pairs — again only once the filter is applied to STARTS (`gs == 1`) rather than to appearances, exactly as the 8/31 through 9/4 runs recorded.**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS ITS FIFTH AND SIXTH ROWS — AND BOTH FAIL THE REGISTERED CONDITIONAL, WHICH IS SAID BEFORE THE OUTCOMES ARE

⛔ **The hand-carded rule-51 table above is CARDED plays and stays at 2 clean instances / 1 confounded. A machine row may not be dropped into it.**

⚠️ 🔴 **STATED FIRST, SO NEITHER ROW CAN BE READ AS SUPPORT FOR A SPECIFICATION IT DOES NOT MEET: the registered rule-51 finding is conditional on a STRONG (≥5 K) FIRST MEETING, and NEITHER of these first meetings clears it.** ⛔ **And the registered mean-K specification FAILED at t=−1.78; the threshold version is a SECOND CUT OF THE SAME DATA and is EXPLORATORY — owed test T18.**

| # | Pitcher | Opponent | First meeting | Gap | Carded row | Result |
|---|---|---|---|---|---|---|
| 5 | **Erick Fedde** | **MIN** | 2026-08-29 — **4 K**, 15 outs, 88 P *(below the ≥5 K conditional)* | **6 days** | o2.5 K at blend 66.9 | **2 K — L** ❌ |
| 6 | **Keider Montero** | **CLE** | 2026-08-13 — **0 K**, 19 outs, 88 P *(far below the ≥5 K conditional)* | **22 days** | o2.5 K at blend 65.8 · o15.5 outs at blend 59.5 | **4 K — W** ✅ · **12 outs — L** ❌ |

⛔ **LOG, DO NOT CONCLUDE. Two rows, three graded outcomes, both first meetings outside the registered conditional, and they point opposite ways on the K bar.** **The machine-population log now holds SIX rows (8/30 Junk, 9/1 Gore, 9/2 Bradford and Lopez, 9/4 Fedde and Montero).**

### 🟡 THE `carried` SHADOW — 9/4. ✅ **BETTER — ONLY THE SECOND TIME IN THIRTEEN SLATES, AND BY EXACTLY THE MECHANISM THAT MADE IT WORSE ELEVEN TIMES.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 8 of the 24 graded rows, every one the `T22` shuttled-starter warning, across 6 pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Cristian Javier u4.5 K | 73.5% | 59.1% | **L** | **carried** |
| Daniel Lynch IV u12.5 outs | 71.8% | 57.4% | **L** | **carried** |
| Erick Fedde o2.5 K | 66.9% | 52.5% | **L** | **carried** |
| Cristian Javier u14.5 outs | 66.6% | 52.2% | **L** | **carried** |
| Keider Montero o2.5 K | 65.8% | 51.4% | **W** | **blend** |
| Rhett Lowder o3.5 K | 62.6% | 48.2% | **L** | **carried** |
| Keider Montero o15.5 outs | 59.5% | 45.1% | **L** | **carried** |
| Shane Drohan o15.5 outs | 58.7% | 44.3% | **L** | **carried** |

| | Brier over all 24 graded rows | Brier over the 8 rows that differ |
|---|---|---|
| `blend` | 🔴 **.3158** | 🔴 **.3943** |
| `carried` | ✅ **.2717** | ✅ **.2619** |
| Verdict | ✅ **`carried` is BETTER by .0441** | ✅ **`carried` is BETTER by .1324** |

⛔ **8 ROWS FROM 6 PITCHERS, TWO OF THEM CONTRIBUTING TWO EACH. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **AND THE MECHANISM IS THE SAME ONE FOR THE THIRTEENTH TIME, WHICH IS WHY TODAY'S FLIP IS NOT NEWS EITHER: 7 of the 8 differing rows LOST, and `carried` is ALWAYS the LOWER number, so it wins for being pessimistic on a bad subset exactly as it lost on 9/3 for being pessimistic on a good one.** ⛔ **Thirteen slates of the same arithmetic is not thirteen pieces of evidence about T22. It is one piece of evidence about the sign of a shift, sampled thirteen times.**

➡️ **RUNNING ACROSS THE THIRTEEN MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 82 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27, 9 on 8/28, 2 on 8/29, 7 on 8/30, 8 on 8/31, 9 on 9/1, 10 on 9/2, 8 on 9/3, 8 on 9/4** *(`3+2+8+8+0+9+2+7+8+9+10+8+8 = 82` ✅, counted against the thirteen enumerated slate figures and not against another number)*.

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS THIRD FORM IN THREE SLATES, AND THE THIRD FORM IS THE ONE THAT SETTLES THE ARGUMENT

🔴 **THE 9/4 PARLAYS WENT 1/23 AND THE PAIRS 3/7 — AND THE CAUSE IS A SINGLE LEG THAT NEVER RESOLVED: KUMAR ROCKER o2.5 K SITS IN 18 OF THE 24 PARLAYS AND 2 OF THE 8 PAIRS, AND HE DID NOT START.**

➡️ 🔴 **THREE CONSECUTIVE SLATES, THREE DIFFERENT HEADLINES, ONE DEFECT: 9/2's 0/24 was one losing leg reported twenty-four times · 9/3's 14/24 was one winning leg reported twenty-four times · 9/4's 1/23 is one SCRATCHED leg reported eighteen times.** ⛔ **A pool that can be destroyed, carried or voided wholesale by one row is not twenty-four observations of anything, and the aggregate number it produces should never be quoted as a rate.** ✅ **This is the strongest available form of the argument, because it now holds across a good night, a bad night and a null one.**

⚠️ **Also re-reported and unchanged: `card.py`'s `in_band` flag is still computed against `TARGET = 2.10` while `PARLAY_BANDS[2]` is `(1.80, 2.20)` and `parlay_rule` prose says 1.8x–2.2x.** ✅ **IT DID NOT BITE THIS SLATE — the only above-band pair is 2.308x, above the ceiling on BOTH readings — so the split is the same either way.** ⛔ **An interactive session must still pick one ceiling; open since 8/26.**

⚠️ 🔴 **AND ONE NEW CODE-DEBT LINE, REPORTED NOT FIXED: `picks/2026-09-04.json` still carries `model_version: "v4.0"`, four days after the September re-fit published v5.0.** ⛔ **The model doc's own CODE-DEBT block puts the worst realistic pricing impact at 0.053 K and 0.133 outs, so this is "last month's constants, and it barely matters" — not "the card is wrong."**

**Progress: TABLE M — 13 slates, 283 graded pitcher plays, 93 graded pairs. TABLE M-H — 12 slates, 310 graded hitter rows.**


## 🆕 2026-09-06 — THE FOURTEENTH MACHINE SLATE (2026-09-05): A FOURTH CONSECUTIVE CARD WRITTEN EXACTLY ONCE, `carried` BETTER FOR THE THIRD TIME IN FOURTEEN SLATES BY THE SAME MECHANISM THAT MADE IT WORSE ELEVEN TIMES, CHECK 36's DEFECT ON ITS WORST BOARD YET AT **THREE** ROWS INSIDE THE WINDOW, AND A TICKET SURFACE THAT WENT 0-FOR-EVERYTHING OFF TWO LEGS

`[graded 2026-09-06]` ✅ **`picks/2026-09-05.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 15 GAMES.** **`50 = 25 + 25` ✅.**

✅ **AND FOR A FOURTH CONSECUTIVE DAY THE FILE WAS WRITTEN EXACTLY ONCE: `git log` on a FULLY UNSHALLOWED clone (1,237 commits, no `.git/shallow`) names ONE commit, `8e17703` at `2026-09-05T14:11:55Z` (`generated_at 14:11:41Z`), pre-slate against an earliest `commence` of `20:11:00Z`, with `coverage_detail.skipped` carrying no `"already started"` key at all.** ⛔ **The overwrite mechanism is unchanged and simply had no second run to fire; four clean days is not a fix.**

✅ **ALL 25 PITCHER ROWS ARE GRADED — every carded starter started, so nothing on this slate is excluded from the accumulators below for a scratch.**

⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24 through 9/4: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in the ledger — 15/20, with 5 rows ungraded because those players did not appear.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **FOURTEENTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23 through 9/5, so the CARDED denominator has not moved for fourteen consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it. The machine population is NOT T15's denominator and may not be substituted into it.**

⚠️ 🔴 **THE DROUGHT IS NOW FIFTEEN DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.**

⚠️ 🔴 **AND WHAT THE MACHINE SLATE SHOWED IS RECORDED HERE AND NOT FOLDED IN.** **Over its 25 graded rows the mean `model` is 65.2, the mean `raw` 69.0, the mean `blend` 67.1 and the mean `carried` 61.9, against an actual 44.0%.** **Brier: `carried` .2875 · `model` .3031 · `blend` .3043 · `raw` .3116.** ⚠️ **On a board this badly calibrated the ordering is close to meaningless — every estimator is far too high, so the LOWEST one wins by being lowest.** ⛔ **Log, do not conclude.**

⚠️ **The "which was closer" tally on this population reads model 11, raw 14, tie 0.** ⛔ **It is recorded for completeness and it is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no fit.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 9/5 card carries Hard Rock alt ladders on 15 of its 25 pitcher rows — 123 rungs across 14 distinct starts.** 🔴 **IT IS NOT MERGED, for the fourteenth time and for the same reason: T11's `n` is CARDED arms and the machine board is a different population.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket tally on this page.**

**Andrew Abbott (5 K) · Anthony Kay (3 K) · Brandon Pfaadt (4 K) · Braxton Ashcraft (9 K) · Carlos Rodón (7 K) · Chris Bassitt (6 K) · Dustin May (5 K) · George Kirby (5 K) · Max Scherzer (2 K) · Parker Messick (12 K) · Robbie Ray (1 K) · Tyler Glasnow (8 K) · Yusei Kikuchi (6 K) · Zack Wheeler (9 K)** — **14 DISTINCT STARTS**, deduplicated on (pitcher, date). ⛔ **`n` is 14 STARTS, not 123 rungs.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/5. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/4 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared the number and AGAINST when none did; `n=0` is a NO CALL and enters no tally.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **25** | 🔴 **9/25** | ⚠️ **its worst reading yet — 15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, 15/22, 15/24, 14/25, 10/24, now 9/25 across fourteen slates** |
| **Head-to-head** (prior meetings) | **15** | **4/15** | ⚠️ **thirteen are n=1 and two are n=2** |
| **Head-to-head, NO CALL — n=0** | **10** | — | ⛔ **logged and in no tally** (`15 + 10 = 25` ✅) |

✅ 🆕 **AND FOR THE FIRST TIME SINCE 8/30 THE `cleared 1/2` CASE DID NOT ARISE AT ALL — every head-to-head on this board is either a clean majority or a clean none, so the published convention reaches all 15 of them.**

⚠️ 🔴 **BOTH READ BELOW A COIN FLIP THIS SLATE, AND THE REASON IS THE BOARD, NOT THE TIEBREAKER: the slate went 11/25, so an estimator that says FOR on almost everything is punished mechanically.** ⛔ **Log, do not conclude.**

#### 🔴 THREE ROWS WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED — AND THE CLASS TOOK TWO

| Play | Matched class | Head-to-head | Result | Which was right |
|---|---|---|---|---|
| **Tyler Glasnow u7.5 K** | **29/35 = 82.9% → FOR** | **0/1 vs WSH → AGAINST** | **L** ❌ | **the head-to-head** |
| **Chris Bassitt o14.5 outs** | **23/35 = 65.7% → FOR** | **0/1 vs BOS → AGAINST** | **W** ✅ | **the class** |
| **Andrew Abbott o3.5 K** | **46/73 = 63.0% → FOR** | **0/1 vs MIL → AGAINST** | **W** ✅ | **the class** |

**THREE disagreeing rows: the class right on 2, the head-to-head right on 1** — `2 + 1 = 3` ✅, counted against the rows above (ledger rule 45). ⚠️ **All three head-to-heads rest on a single prior meeting and are worth almost nothing individually.**

### 🔴🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **FOURTEENTH CONSECUTIVE RUN** — 🔴 **AND THE BOARD CARRIED THREE ROWS INSIDE THE WINDOW, MORE THAN ANY SLATE BEFORE IT**

`[re-checked 2026-09-06]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the substring `days` appears ZERO times anywhere in `picks/2026-09-05.json`.**

✅ **The gap was computed here instead, for every arm carrying a prior meeting, by re-deriving each meeting from the repo's own stored log under a STARTS (`gs == 1`) filter:**

| Pitcher | Opponent | Most recent prior START | Gap |
|---|---|---|---|
| 🔴 **Max Scherzer** | **Kansas City Royals** | **2026-08-25** | 🔴 **11 days** |
| 🔴 **Parker Messick** | **Detroit Tigers** | **2026-08-13** | 🔴 **23 days** |
| 🔴 **Matthew Liberatore** | **Colorado Rockies** | **2026-08-08** | 🔴 **28 days** |
| Dustin May | Cincinnati Reds | 2026-07-24 | 43 days |
| Andrew Abbott | Milwaukee Brewers | 2026-07-01 | 66 days |
| Chris Bassitt | Boston Red Sox | 2026-06-03 | 94 days |
| Anthony Kay | Minnesota Twins | 2026-05-25 | 103 days |
| Zack Wheeler | Atlanta Braves | 2026-04-25 | 133 days |
| Martín Pérez | Philadelphia Phillies | 2026-04-17 | 141 days |
| Tyler Glasnow | Washington Nationals | 2026-04-04 | 154 days |
| Robbie Ray | New York Yankees | 2026-03-27 | 162 days |

🔴🔴 **THREE ROWS ARE INSIDE RULE 51's THIRTY-DAY WINDOW AND THE CARD SAID NOTHING ABOUT ANY OF THEM — the first slate on which more than two have been inside at once.** ⛔ **The card printed `1 start(s) vs KC -- cleared 1/1` for Scherzer and `2 start(s) vs DET -- cleared 2/2` for Messick with no indication that either meeting was recent.**

✅ **The re-derivation doubles as a control on the card: every head-to-head string it printed reproduces EXACTLY from the same log, 25/25 rows, again only once the filter is applied to STARTS (`gs == 1`) rather than to appearances.**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS ITS SEVENTH, EIGHTH AND NINTH ROWS — AND ONE OF THEM IS THE FIRST TO CLEAR THE REGISTERED CONDITIONAL

⛔ **The hand-carded rule-51 table above is CARDED plays and stays at 2 clean instances / 1 confounded. A machine row may not be dropped into it.**

⚠️ 🔴 **STATED FIRST, SO NO ROW CAN BE READ AS SUPPORT FOR A SPECIFICATION IT DOES NOT MEET: the registered rule-51 finding is conditional on a STRONG (≥5 K) FIRST MEETING.** ⛔ **And the registered mean-K specification FAILED at t=−1.78; the threshold version is EXPLORATORY. Nothing below promotes it.**

| # | Pitcher | Opponent | Prior meeting | Gap | Carded row | Result |
|---|---|---|---|---|---|---|
| 7 | **Max Scherzer** | **KC** | 2026-08-25 — **4 K**, 15 outs, 92 P *(below the ≥5 K conditional)* | **11 days** | o3.5 K at blend 61.9 | **2 K — L** ❌ |
| 8 | 🆕 **Parker Messick** | **DET** | 2026-08-13 — **6 K**, 17 outs, 102 P 🔴 *(**CLEARS** the ≥5 K conditional — the FIRST machine-population row that does)* | **23 days** | u18.5 outs at blend 66.9 · u6.5 K at blend 65.7 | **18 outs — W** ✅ · **12 K — L** ❌ |
| 9 | **Matthew Liberatore** | **COL** | 2026-08-08 — **3 K**, 15 outs, 94 P *(below the ≥5 K conditional)* | **28 days** | u17.5 outs at blend 73.2 | **13 outs — W** ✅ |

🔴 **ROW 8 IS THE ONE THAT MATTERS AND IT POINTS AGAINST THE HAIRCUT: the exploratory finding says a strong first meeting makes the REMATCH LESS likely to reach 4+ K. Messick reached TWELVE.** ⛔ **ONE observation. It does not move the specification, it does not refute it, and it is not folded into any tally.** **The machine-population log now holds NINE rows (8/30 Junk, 9/1 Gore, 9/2 Bradford and Lopez, 9/4 Fedde and Montero, 9/5 Scherzer, Messick and Liberatore).**

### 🟡 THE `carried` SHADOW — 9/5. ✅ **BETTER — THE THIRD TIME IN FOURTEEN SLATES, AND BY EXACTLY THE MECHANISM THAT MADE IT WORSE ELEVEN TIMES.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 9 of the 25 graded rows, every one the `T22` shuttled-starter warning, across 7 pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Javier Assad o14.5 outs | 71.7% | 57.3% | **L** | **carried** |
| Anthony Kay o14.5 outs | 70.1% | 55.7% | **L** | **carried** |
| Anthony Kay o3.5 K | 70.1% | 55.7% | **L** | **carried** |
| Chris Bassitt u4.5 K | 69.4% | 55.0% | **L** | **carried** |
| Brandon Pfaadt u4.5 K | 69.2% | 54.8% | **W** | **blend** |
| Ryan Gusto u14.5 outs | 66.5% | 52.1% | **W** | **blend** |
| Martín Pérez o14.5 outs | 66.9% | 52.5% | **L** | **carried** |
| Chris Bassitt o14.5 outs | 65.7% | 51.3% | **W** | **blend** |
| Robbie Ray u5.5 K | 61.6% | 47.2% | **W** | **blend** |

| | Brier over all 25 graded rows | Brier over the 9 rows that differ |
|---|---|---|
| `blend` | 🔴 **.3043** | 🔴 **.3220** |
| `carried` | ✅ **.2875** | ✅ **.2752** |
| Verdict | ✅ **`carried` is BETTER by .0168** | ✅ **`carried` is BETTER by .0468** |

⛔ **9 ROWS FROM 7 PITCHERS, TWO OF THEM CONTRIBUTING TWO EACH. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **AND THE MECHANISM IS THE SAME ONE FOR THE FOURTEENTH TIME, WHICH IS WHY TODAY'S RESULT IS NOT NEWS EITHER: `carried` is ALWAYS the LOWER number, and 5 of the 9 differing rows LOST, so it wins for being pessimistic on a board that came in low.** ⛔ **The differing set went 4/9 = 44.4%, which is the slate rate. `carried` is not identifying anything about these arms; it is subtracting a constant on a board where every estimate was too high.**

➡️ **RUNNING ACROSS THE FOURTEEN MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 91 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27, 9 on 8/28, 2 on 8/29, 7 on 8/30, 8 on 8/31, 9 on 9/1, 10 on 9/2, 8 on 9/3, 8 on 9/4, 9 on 9/5** *(`3+2+8+8+0+9+2+7+8+9+10+8+8+9 = 91` ✅, counted against the fourteen enumerated slate figures and not against another number)*.

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS FOURTH FORM IN FOUR SLATES, AND THE FOURTH FORM IS THE PUREST ONE YET

🔴 **THE 9/5 PAIRS WENT 0/8 AND THE PARLAYS 0/23 — AND SETH LUGO IS A LEG IN **ALL EIGHT** PAIRS AND IN **19 OF THE 24** PARLAYS. He went 5.0 IP for ONE strikeout, and both of his carded rungs (`o1.5 K` and `o2.5 K`) lost.** **Christian Koss u0.5 RBI covers 13 more parlays and also lost; between them the two legs touch 22 of the 24 tickets.**

➡️ 🔴 **FOUR CONSECUTIVE SLATES, FOUR DIFFERENT HEADLINES, ONE DEFECT: 9/2's 0/24 was one losing leg reported twenty-four times · 9/3's 14/24 was one winning leg reported twenty-four times · 9/4's 1/23 was one SCRATCHED leg reported eighteen times · 9/5's 0/8 and 0/23 are one losing leg in EVERY SINGLE PAIR.** ⛔ **A ticket surface built by combining a small pool does not produce independent observations, and no accumulator on this page should ever treat its counts as sample size.**

⚠️ 🔴 **AND ONE THING THIS SLATE ADDS THAT NONE OF THE OTHER THREE DID: SETH LUGO IS ON NO ROW OF THE 50-PLAY CARD AT ALL.** **Both his rungs come off his Hard Rock alt ladder, which never reaches `picks[]`.** ➡️ **So the pair pool's whole result turns on an arm the card itself did not card — the pair surface and TABLE M are not the same population even on the same day.**

🔴🔴 **AND THE BAND-CEILING CONTRADICTION BIT FOR THE FIRST TIME: pairs 5 (2.157x) and 7 (2.115x) are ABOVE BAND under `card.py`'s `in_band` (`TARGET = 2.10`) and INSIDE BAND under the same file's `PARLAY_BANDS[2] = (1.80, 2.20)` and its `parlay_rule` prose.** ➡️ **INSIDE 0/6 · ABOVE 0/2 by the flag; INSIDE 0/8 · ABOVE 0/0 by the prose.** ✅ **It cost nothing in the numerator because every pair lost — but the split is now demonstrably reader-dependent.** ⛔ **REPORTED, NOT FIXED, open since 2026-08-26. An interactive session must pick one ceiling.**

⚠️ 🔴 **Also re-reported and unchanged: `picks/2026-09-05.json` still carries `model_version: "v4.0"` and `card.py`'s model block still holds the v4.0 constants verbatim, five days after the September re-fit published v5.0.** ⛔ **A headless run cannot test or push.** ✅ 🆕 **One long-standing defect IS gone, and it is recorded because every grading run from 8/24 to 9/2 re-reported it: `card.py`'s `calibration_warning` no longer quotes the stale −25.9 / −18.0 ledger figures — it is built by `calibration_sentence()` from the runner's own band record and carries an explicit small-sample hedge.**

**Progress: TABLE M — 14 slates, 308 graded pitcher plays, 101 graded pairs. TABLE M-H — 13 slates, 330 graded hitter rows.**


## 🆕 2026-09-07 — THE FIFTEENTH MACHINE SLATE (2026-09-06): A FIFTH CONSECUTIVE CARD WRITTEN EXACTLY ONCE, THE SMALLEST GAP SINCE 9/3, `carried` BETTER FOR THE FOURTH TIME IN FIFTEEN SLATES BY THE SAME MECHANISM THAT MADE IT WORSE ELEVEN, CHECK 36's DEFECT AGAIN AT **THREE** ROWS IN THE WINDOW, AND A TICKET SURFACE WHOSE ENTIRE RESULT IS ONE ARM

`[graded 2026-09-07]` ✅ **`picks/2026-09-06.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 14 GAMES.** **`50 = 25 + 25` ✅.**

✅ **AND FOR A FIFTH CONSECUTIVE DAY THE FILE WAS WRITTEN EXACTLY ONCE: `git log` on a FULLY UNSHALLOWED clone (1,384 commits, no `.git/shallow`) names ONE commit, `68764a3` at `2026-09-06T14:06:52Z` (`generated_at 14:06:37Z`), pre-slate against an earliest `commence` of `16:10:00Z`, with `coverage_detail.skipped` carrying no `"already started"` key at all.** ⛔ **The overwrite mechanism is unchanged and simply had no second run to fire; five clean days is not a fix.**

⚠️ **The slate held FIFTEEN games and the card covers FOURTEEN. MIN @ CWS was in the props pull (`n_events: 15`) and produced no top-50 row — an absence in a RANKING, not a dropped game. Stated here because "14 games" would otherwise read like the 8/27 and 8/29 damage.**

✅ **ALL 25 PITCHER ROWS ARE GRADED — every carded starter started, so nothing on this slate is excluded from the accumulators below for a scratch.**

⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24 through 9/5: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in the ledger — 21/21 with 4 rows ungraded because those players did not appear.** ⚠️ **That is a 100% slate and the ledger says plainly why it is structural rather than predictive; nothing on this page counts it.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **FIFTEENTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23 through 9/6, so the CARDED denominator has not moved for fifteen consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it. The machine population is NOT T15's denominator and may not be substituted into it.**

⚠️ 🔴 **THE DROUGHT IS NOW SIXTEEN DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.**

⚠️ 🔴 **AND WHAT THE MACHINE SLATE SHOWED IS RECORDED HERE AND NOT FOLDED IN.** **Over its 25 graded rows the mean `model` is 66.5, the mean `raw` 67.8, the mean `blend` 67.1 and the mean `carried` 61.4, against an actual 60.0%.** **Brier: `carried` .2214 · `raw` .2375 · `blend` .2458 · `model` .2627.** ⚠️ **The ordering is the same shape as 9/5's — every estimator sits above the outcome, so the LOWEST one wins by being lowest — but the board is far better calibrated (−7.1 against −23.1), which makes the ordering weaker evidence, not stronger.** ⛔ **Log, do not conclude.**

⚠️ **The "which was closer" tally on this population reads model 10, raw 15, tie 0.** ⛔ **It is recorded for completeness and it is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no fit.** ⚠️ **It has now tracked the day's win rate on every slate it has been computed on, which is the bias, not a finding.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 9/6 card carries Hard Rock alt ladders on 15 of its 25 pitcher rows — 111 rungs across 14 distinct starts.** 🔴 **IT IS NOT MERGED, for the fifteenth time and for the same reason: T11's `n` is CARDED arms and the machine board is a different population.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket tally on this page.**

**Andrew Alvarez (5 K) · Bryan Woo (9 K) · Ian Seymour (2 K) · Jackson Jobe (7 K) · Justin Wrobleski (6 K) · Kyle Harrison (4 K) · Kyle Leahy (6 K) · Paul Skenes (2 K) · Peter Lambert (6 K) · Randy Dobnak (3 K) · Spencer Arrighetti (3 K) · Tyler Mahle (3 K) · Tyler Phillips (3 K) · Walbert Ureña (4 K)** — **14 DISTINCT STARTS**, deduplicated on (pitcher, date). ⛔ **`n` is 14 STARTS, not 111 rungs.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/6. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/5 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared the number and AGAINST when none did; `n=0` is a NO CALL and enters no tally.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **25** | **10/25** | ⚠️ **15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, 15/22, 15/24, 14/25, 10/24, 9/25, now 10/25 across fifteen slates** |
| **Head-to-head** (prior meetings) | **7** | **4/7** | ⚠️ **five are n=1 and two are n=2** |
| **Head-to-head, NO CALL** | **18** | — | ⛔ **logged and in no tally** (`7 + 18 = 25` ✅) |

⚠️ **THE NO-CALL GROUP IS 17 `n=0` ROWS PLUS ONE `cleared 1/2` — Tyler Mahle o4.5 K vs PHI, 2 prior starts, one clearing.** 🔴 **The published convention reaches a clean majority and a clean none and does NOT reach a 1-of-2 split, so it is a NO CALL, exactly as the 8/30 block ruled it.** ⛔ **The convention was not re-decided after seeing the outcome.**

⚠️ 🔴 **SEVENTEEN OF TWENTY-FIVE ROWS HAVE NO PRIOR MEETING AT ALL. That is the highest `n=0` share this tally has recorded, and it is the honest headline: on a September board the tiebreaker mostly has nothing to say.**

#### 🔴 ONE ROW WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED — AND THE CLASS TOOK IT

| Play | Matched class | Head-to-head | Result | Which was right |
|---|---|---|---|---|
| **Aaron Nola u17.5 outs** | **17/42 = 40.5% → AGAINST** | **1/1 vs ATL → FOR** | **L** *(21 outs)* ❌ | ✅ **the class** |

**ONE disagreeing row: the class right on 1, the head-to-head right on 0** — `1 + 0 = 1` ✅, counted against the row above (ledger rule 45). ⚠️ **The head-to-head rests on a single prior meeting and is worth almost nothing on its own.**

### 🔴🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **FIFTEENTH CONSECUTIVE RUN** — 🔴 **AND THE BOARD AGAIN CARRIED THREE ROWS IN THE WINDOW**

`[re-checked 2026-09-07]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the substring `days` appears ZERO times anywhere in `picks/2026-09-06.json`.**

✅ **The gap was computed here instead, for every arm carrying a prior meeting, by re-deriving each meeting from the repo's own stored log under a STARTS (`gs == 1`) filter:**

| Pitcher | Opponent | Most recent prior START | Gap |
|---|---|---|---|
| 🔴 **Spencer Arrighetti** | **Kansas City Royals** | **2026-08-27** | 🔴 **10 days** |
| 🔴 **Randy Dobnak** | **Toronto Blue Jays** | **2026-08-26** | 🔴 **11 days** |
| 🔴 **Kyle Leahy** | **Colorado Rockies** | **2026-08-07** | 🔴 **30 days — EXACTLY ON THE BOUNDARY** |
| MacKenzie Gore | Tampa Bay Rays | 2026-07-29 | 39 days |
| Gage Jump | Seattle Mariners | 2026-05-26 | 103 days |
| Tyler Mahle | Philadelphia Phillies | 2026-04-28 | 131 days |
| Aaron Nola | Atlanta Braves | 2026-04-26 | 133 days |

🔴 **THREE ROWS ARE INSIDE OR ON RULE 51's THIRTY-DAY WINDOW AND THE CARD SAID NOTHING ABOUT ANY OF THEM — equalling the 9/5 board.** ⚠️ 🔴 **AND KYLE LEAHY IS AT EXACTLY 30 DAYS, WHICH THE RULE'S WORDING ("inside 30 days") DOES NOT CLEANLY RESOLVE.** ⛔ **It is reported as a boundary case and is NOT decided here; the machine rule-51 log below records it with the boundary stated on its row.**

✅ **The re-derivation doubles as a control on the card: every head-to-head string it printed reproduces EXACTLY from the same log, 25/25 rows, again only once the filter is applied to STARTS (`gs == 1`) rather than to appearances.**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS ITS TENTH, ELEVENTH AND TWELFTH ROWS — AND TWO OF THEM CLEAR THE REGISTERED CONDITIONAL

⛔ **The hand-carded rule-51 table above is CARDED plays and stays at 2 clean instances / 1 confounded. A machine row may not be dropped into it.**

⚠️ 🔴 **STATED FIRST, SO NO ROW CAN BE READ AS SUPPORT FOR A SPECIFICATION IT DOES NOT MEET: the registered rule-51 finding is conditional on a STRONG (≥5 K) FIRST MEETING.** ⛔ **And the registered mean-K specification FAILED at t=−1.78; the threshold version is EXPLORATORY. Nothing below promotes it.**

| # | Pitcher | Opponent | Prior meeting | Gap | Carded row | Result |
|---|---|---|---|---|---|---|
| 10 | **Spencer Arrighetti** | **KC** | 2026-08-27 — **4 K**, 12 outs, 79 P *(below the ≥5 K conditional)* | **10 days** | o3.5 K at blend 68.6 | **3 K — L** ❌ |
| 11 | 🆕 **Randy Dobnak** | **TOR** | 2026-08-26 — **5 K**, 18 outs, 92 P 🔴 *(**CLEARS** the ≥5 K conditional)* | **11 days** | o2.5 K at blend 84.4 | **3 K — W** ✅ |
| 12 | 🆕 **Kyle Leahy** | **COL** | 2026-08-07 — **8 K**, 15 outs, 82 P 🔴 *(**CLEARS** the ≥5 K conditional)* | ⚠️ **30 days — ON THE BOUNDARY, not inside it** | o2.5 K at blend 83.1 · o3.5 K at blend 71.0 | **6 K — W** ✅ · **6 K — W** ✅ |

🔴 **ROWS 11 AND 12 BOTH POINT AGAINST THE HAIRCUT AT A LOW BAR AND SAY NOTHING ABOUT THE HIGH ONE: the exploratory finding is about reaching **4+ K** in the rematch, and Dobnak reached three while Leahy reached six.** ⚠️ **So on the registered threshold Dobnak's rematch FAILED to reach 4+ (consistent with the haircut) while Leahy's cleared it comfortably (against it) — and BOTH of the carded rows they settled were WINS, because the carded bars were 2.5 and 3.5, not 4.5.** ⛔ **That distinction is the whole reason a rematch is "a reason to DROP A RUNG, not to drop the pitcher." THREE observations. Nothing is folded into any tally, nothing is re-specified.** **The machine-population log now holds TWELVE rows (8/30 Junk, 9/1 Gore, 9/2 Bradford and Lopez, 9/4 Fedde and Montero, 9/5 Scherzer, Messick and Liberatore, 9/6 Arrighetti, Dobnak and Leahy).**

### 🟡 THE `carried` SHADOW — 9/6. ✅ **BETTER — THE FOURTH TIME IN FIFTEEN SLATES, AND BY EXACTLY THE MECHANISM THAT MADE IT WORSE ELEVEN TIMES.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 10 of the 25 graded rows, every one the `T22` shuttled-starter warning, across 8 pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Justin Wrobleski o13.5 outs | 87.5% | 73.1% | **L** | **carried** |
| Randy Dobnak o2.5 K | 84.4% | 70.0% | **W** | **blend** |
| Spencer Arrighetti o3.5 K | 68.6% | 54.2% | **L** | **carried** |
| Tanner Gordon u15.5 outs | 68.0% | 53.6% | **W** | **blend** |
| Andrew Alvarez o3.5 K | 68.1% | 53.7% | **W** | **blend** |
| Walbert Ureña o4.5 K | 63.6% | 49.2% | **L** | **carried** |
| Ian Seymour o5.5 K | 61.5% | 47.1% | **L** | **carried** |
| Tyler Phillips o3.5 K | 61.2% | 46.8% | **L** | **carried** |
| Andrew Alvarez o14.5 outs | 61.4% | 47.0% | **L** | **carried** |
| Justin Wrobleski o4.5 K | 59.9% | 45.5% | **W** | **blend** |

| | Brier over all 25 graded rows | Brier over the 10 rows that differ |
|---|---|---|
| `blend` | 🔴 **.2458** | 🔴 **.3160** |
| `carried` | ✅ **.2214** | ✅ **.2549** |
| Verdict | ✅ **`carried` is BETTER by .0244** | ✅ **`carried` is BETTER by .0611** |

⛔ **10 ROWS FROM 8 PITCHERS, TWO OF THEM CONTRIBUTING TWO EACH. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **AND THE MECHANISM IS THE SAME ONE FOR THE FIFTEENTH TIME, WHICH IS WHY TODAY'S RESULT IS NOT NEWS EITHER: `carried` is ALWAYS the LOWER number, and 6 of the 10 differing rows LOST.** 🔴 **THE SHARPEST FORM OF IT YET: the differing set went 4/10 = 40.0% against a SLATE rate of 60.0% — a twenty-point split — so on a board that was otherwise WELL calibrated, `carried` still won purely by being pessimistic on the subset that happened to lose.** ⛔ **It is not identifying anything about these arms; it is subtracting a constant.**

➡️ **RUNNING ACROSS THE FIFTEEN MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 101 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27, 9 on 8/28, 2 on 8/29, 7 on 8/30, 8 on 8/31, 9 on 9/1, 10 on 9/2, 8 on 9/3, 8 on 9/4, 9 on 9/5, 10 on 9/6** *(`3+2+8+8+0+9+2+7+8+9+10+8+8+9+10 = 101` ✅, counted against the fifteen enumerated slate figures and not against another number)*.

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS FIFTH FORM IN FIVE SLATES, AND THIS ONE IS THE CLEANEST DEMONSTRATION SO FAR

🔴 **THE 9/6 PAIRS WENT 4/8 AND THE PARLAYS 6/23 — AND JUSTIN WROBLESKI o13.5 OUTS IS A LEG IN 4 OF THE 8 PAIRS, 17 OF THE 24 PARLAYS AND **ALL EIGHT** FOUR-MANS. He went 3.0 IP for NINE outs.** ✅ 🔴 **HE IS THE ONLY LOSING LEG IN ANY PAIR ON THE BOARD — every other pair leg won — so the pairs' 4/8 is one arm reported four times against four tickets that avoided him, and the four-mans' 0/8 is one arm reported eight times.**

➡️ 🔴 **FIVE CONSECUTIVE SLATES, FIVE DIFFERENT HEADLINES, ONE DEFECT: 9/2's 0/24 was one losing leg reported twenty-four times · 9/3's 14/24 was one winning leg reported twenty-four times · 9/4's 1/23 was one SCRATCHED leg reported eighteen times · 9/5's 0/8 and 0/23 were one losing leg in EVERY pair · 9/6's 4/8 and 0/8-on-four-mans are one losing leg partitioning the surface exactly in half.** ⛔ **A ticket surface built by combining a small pool does not produce independent observations, and no accumulator on this page should ever treat its counts as sample size.**

⚠️ 🔴 **AND THE 9/5 OBSERVATION HOLDS AGAIN, LARGER: ELEVEN of the FOURTEEN distinct legs across the pair and parlay surfaces are on NO ROW OF THE 50-PLAY CARD** — they are alt-ladder rungs or hitter rows that never reach `picks[]`. ➡️ **The ticket surfaces and TABLE M are not the same population even on the same day.**

🔴🔴 **AND THE BAND-CEILING CONTRADICTION BIT AGAIN, HARDER THAN ON 9/5: pair 7 at 2.14x is ABOVE BAND under `card.py`'s `in_band` (`TARGET = 2.10`) and INSIDE BAND under the same file's `PARLAY_BANDS[2] = (1.80, 2.20)` and its `parlay_rule` prose — and it LOST, so it moves the NUMERATOR-BEARING denominators of both cuts.** ➡️ **INSIDE 2/3 · ABOVE 2/5 by the flag; INSIDE 2/4 · ABOVE 2/4 by the prose.** ⚠️ **On 9/5 it cost nothing because every pair lost. This slate it makes the two readings genuinely different measurements.** ⛔ **REPORTED, NOT FIXED, open since 2026-08-26. An interactive session must pick one ceiling.**

⚠️ 🔴 **Also re-reported and unchanged: `picks/2026-09-06.json` still carries `model_version: "v4.0"` and `card.py`'s model block still holds the v4.0 constants verbatim, six days after the September re-fit published v5.0.** ⛔ **A headless run cannot test or push.**

## 🆕 2026-09-08 — THE SIXTEENTH MACHINE SLATE (2026-09-07): A SIXTH CONSECUTIVE CARD WRITTEN EXACTLY ONCE, THE FIRST CARD SINCE 8/24 THAT IS NOT 25 PITCHER + 25 HITTER, THE WORST-CALIBRATED PITCHER BOARD SINCE 9/4, `carried` BETTER A FIFTH TIME IN SIXTEEN SLATES — AND A TICKET SURFACE IN WHICH **ONE ARM IS A LEG IN ALL EIGHT PAIRS AND ALL TWENTY-FOUR PARLAYS**

`[graded 2026-09-08]` ✅ **`picks/2026-09-07.json` AS COMMITTED IS 50 PLAYS — 22 PITCHER AND 28 HITTER — ACROSS 11 GAMES.** **`50 = 22 + 28` ✅.**

⚠️ 🆕 **THE SPLIT IS NOT 25/25, AND THAT IS THE FIRST TIME SINCE 8/24.** **Every card from 8/25 through 9/6 carried exactly 25 pitcher and 25 hitter rows; this one carries 22 and 28.** ✅ **It is not damage: `board_rule` says 31 pitcher and 1,599 hitter rows were PRICED and 50 are SHOWN, so the split is what the ranking produced on an 11-game board, not a truncation.** ⛔ **Stated here because a changed denominator that nobody names is how a population silently drifts under an accumulator — and it drifted under this one on 8/24.**

✅ **AND FOR A SIXTH CONSECUTIVE DAY THE FILE WAS WRITTEN EXACTLY ONCE: `git log` on a clone deepened to 400 commits names ONE commit touching `picks/2026-09-07.json` — `9458027` at `2026-09-07T14:09:38Z` (`generated_at 14:09:31Z`), pre-slate by roughly three hours against an earliest `commence` of `17:06:00Z`, with `coverage_detail.skipped` carrying no `"already started"` key at all.** ⛔ **The overwrite mechanism is unchanged and simply had no second run to fire; six clean days is not a fix.**

✅ **The slate held ELEVEN games and the card covers ELEVEN — ZERO games dropped, the first exact cover since 9/3.**

✅ **ALL 22 PITCHER ROWS ARE GRADED — every carded starter started, so nothing on this slate is excluded from the accumulators below for a scratch.**

⛔ **THE 28 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE**, for the same reason as 8/24 through 9/6: no `blend`, no `band`, no model. ✅ **They are graded into TABLE M-H in the ledger — 19/25 with 3 rows ungraded because those players did not appear.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **SIXTEENTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23 through 9/7, so the CARDED denominator has not moved for sixteen consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it — argmin on the `w = 1.00` boundary, margin leg cleared, `n` leg at 31 against 100, and the 50/50 UNTOUCHED. The machine population is NOT T15's denominator and may not be substituted into it.**

⚠️ 🔴 **THE DROUGHT IS NOW SEVENTEEN DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.**

⚠️ 🔴 **AND WHAT THE MACHINE SLATE SHOWED IS RECORDED HERE AND NOT FOLDED IN.** **Over its 22 graded rows the mean `model` is 62.0, the mean `raw` 62.9, the mean `blend` 62.5 and the mean `carried` 57.2, against an actual 40.9%.** **Brier: `carried` .3062 · `model` .3072 · `blend` .3230 · `raw` .3496.** ⚠️ **Same shape as 9/5 and 9/6 — every estimator sits above the outcome, so the LOWEST one wins by being lowest — and on a board this badly calibrated (−21.6) the ordering is close to uninformative.** ⚠️ 🆕 **What is different is that `model` and `carried` are separated by .0010, which is inside any margin this project would act on.** ⛔ **Log, do not conclude.**

⚠️ **The "which was closer" tally on this population reads model 12, raw 10, tie 0** *(`12 + 10 + 0 = 22` ✅, counted against the 22 graded rows)*. ⛔ **It is recorded for completeness and it is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no fit.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 9/7 card carries Hard Rock alt ladders on 13 of its 22 pitcher rows — 96 rungs across 13 distinct starts.** 🔴 **IT IS NOT MERGED, for the sixteenth time and for the same reason: T11's `n` is CARDED arms and the machine board is a different population.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket tally on this page.**

**Brayan Bello (7 K) · Chase Burns (5 K) · Dylan Cease (6 K) · Grant Holmes (6 K) · Grayson Rodriguez (3 K) · Jacob Lopez (1 K) · Jake Irvin (3 K) · Joey Cantillo (3 K) · Matthew Boyd (7 K) · Noah Cameron (7 K) · Robert Gasser (5 K) · Trevor Rogers (6 K) · Troy Melton (3 K)** — **13 DISTINCT STARTS**, deduplicated on (pitcher, date). ⛔ **`n` is 13 STARTS, not 96 rungs.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/7. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/6 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared the number and AGAINST when none did; `n=0` is a NO CALL and enters no tally.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **22** | **13/22** | ⚠️ **15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, 15/22, 15/24, 14/25, 10/24, 9/25, 10/25, now 13/22 across sixteen slates** |
| **Head-to-head** (prior meetings) | **10** | **5/10** | ⚠️ **eight are n=1 and two are n=2** |
| **Head-to-head, NO CALL** | **12** | — | ⛔ **logged and in no tally** (`10 + 12 = 22` ✅) |

⚠️ **THE NO-CALL GROUP IS 11 `n=0` ROWS PLUS ONE `cleared 1/2` — Grant Holmes u14.5 outs vs PHI, 2 prior starts, one clearing.** 🔴 **The published convention reaches a clean majority and a clean none and does NOT reach a 1-of-2 split, so it is a NO CALL, exactly as the 8/30 and 9/7 blocks ruled it.** ⛔ **The convention was not re-decided after seeing the outcome.**

#### 🔴 FOUR ROWS WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED — AND THEY SPLIT TWO–TWO

| Play | Matched class | Head-to-head | Result | Which was right |
|---|---|---|---|---|
| **Troy Melton o3.5 K** | **47.0% → AGAINST** | **2/2 vs MIN → FOR** | **L** *(3 K)* ❌ | ✅ **the class** |
| **Trevor Rogers o4.5 K** | **40.7% → AGAINST** | **1/1 vs CLE → FOR** | **W** *(6 K)* ✅ | ✅ **the head-to-head** |
| **Robert Gasser o4.5 K** | **57.1% → FOR** | **0/1 vs CHC → AGAINST** | **W** *(5 K)* ✅ | ✅ **the class** |
| **Dylan Cease u17.5 outs** | **41.2% → AGAINST** | **1/1 vs ATH → FOR** | **W** *(15 outs)* ✅ | ✅ **the head-to-head** |

**FOUR disagreeing rows: the class right on 2, the head-to-head right on 2** — `2 + 2 = 4` ✅, counted against the four rows above (ledger rule 45). ⚠️ **Three of the four head-to-heads rest on a single prior meeting and are worth almost nothing on their own.**

### 🔴🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **SIXTEENTH CONSECUTIVE RUN** — 🔴 **AND THE THREE ROWS IN THE WINDOW ARE ALL AT SIX DAYS, THE TIGHTEST SET IT HAS EVER CARRIED**

`[re-checked 2026-09-08]` **`card.py` prints rule 50's head-to-head on every row and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the substring `days` appears ZERO times anywhere in `picks/2026-09-07.json`.**

✅ **The gap was computed here instead, for every arm carrying a prior meeting, by re-deriving each meeting from the repo's own stored log under a STARTS (`gs == 1`) filter:**

| Pitcher | Opponent | Most recent prior START | Gap |
|---|---|---|---|
| 🔴 **Troy Melton** | **Minnesota Twins** | **2026-09-01** | 🔴 **6 days** |
| 🔴 **Matthew Boyd** | **Milwaukee Brewers** | **2026-09-01** | 🔴 **6 days** |
| 🔴 **Robert Gasser** | **Chicago Cubs** | **2026-09-01** | 🔴 **6 days** |
| Grant Holmes | Philadelphia Phillies | 2026-04-24 | 136 days |
| Trevor Rogers | Cleveland Guardians | 2026-04-19 | 141 days |
| Joey Cantillo | Baltimore Orioles | 2026-04-19 | 141 days |
| Dylan Cease | Athletics | 2026-03-28 | 163 days |

🔴 **THREE ROWS ARE INSIDE RULE 51's THIRTY-DAY WINDOW AND THE CARD SAID NOTHING ABOUT ANY OF THEM — equalling 9/5 and 9/6 on count and beating both on tightness: all three prior meetings fall on the SAME DATE, 2026-09-01, six days out.** ⚠️ **There is no boundary case this slate; the distribution is starkly bimodal — three at 6 days and four at 136 days or more, with nothing in between.**

✅ **The re-derivation doubles as a control on the card: every head-to-head string it printed reproduces EXACTLY from the same log, 22/22 rows, again only once the filter is applied to STARTS (`gs == 1`) rather than to appearances.**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS ITS THIRTEENTH, FOURTEENTH AND FIFTEENTH ROWS — AND NOT ONE OF THEM CLEARS THE REGISTERED CONDITIONAL

⛔ **The hand-carded rule-51 table above is CARDED plays and stays at 2 clean instances / 1 confounded. A machine row may not be dropped into it.**

⚠️ 🔴 **STATED FIRST, SO NO ROW CAN BE READ AS SUPPORT FOR A SPECIFICATION IT DOES NOT MEET: the registered rule-51 finding is conditional on a STRONG (≥5 K) FIRST MEETING.** ⛔ **And the registered mean-K specification FAILED at t=−1.78; the threshold version is EXPLORATORY. Nothing below promotes it.**

| # | Pitcher | Opponent | Prior meeting | Gap | Carded row | Result |
|---|---|---|---|---|---|---|
| 13 | **Troy Melton** | **MIN** | 2026-09-01 — **4 K**, 16 outs, 96 P *(below the ≥5 K conditional)* | **6 days** | o3.5 K at blend 72.4 · u17.5 outs at blend 51.9 | **3 K — L** ❌ · **17 outs — W** ✅ |
| 14 | **Matthew Boyd** | **MIL** | 2026-09-01 — **3 K**, 16 outs, 97 P *(below the ≥5 K conditional)* | **6 days** | u4.5 K at blend 65.0 | **7 K — L** ❌ |
| 15 | **Robert Gasser** | **CHC** | 2026-09-01 — **4 K**, 13 outs, 76 P *(below the ≥5 K conditional)* | **6 days** | o4.5 K at blend 51.6 | **5 K — W** ✅ |

🔴 **ALL THREE FAIL THE ≥5 K CONDITIONAL, SO NONE OF THEM SPEAKS TO THE REGISTERED FINDING AT ALL — and that is worth saying plainly rather than quietly counting them.** ⚠️ **What they do show, descriptively, is the opposite of a haircut where it can be seen: Boyd's rematch produced SEVEN strikeouts after three, and Gasser's five after four; only Melton went down, from four to three.** ⛔ **THREE observations, none eligible. Nothing is folded into any tally, nothing is re-specified.** **The machine-population log now holds FIFTEEN rows.**

### 🟡 THE `carried` SHADOW — 9/7. ✅ **BETTER — THE FIFTH TIME IN SIXTEEN SLATES — BUT BY A WEAKER FORM OF THE USUAL MECHANISM, AND THAT IS THE INTERESTING PART.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 8 of the 22 graded rows, every one the `T22` shuttled-starter warning, across 5 pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Brayan Bello u4.5 K | 74.4% | 60.0% | **L** | **carried** |
| Noah Cameron o3.5 K | 71.3% | 56.9% | **W** | **blend** |
| Jacob Lopez o4.5 K | 68.5% | 54.1% | **L** | **carried** |
| Noah Cameron u17.5 outs | 57.5% | 43.1% | **L** | **carried** |
| Grant Holmes o3.5 K | 56.2% | 41.8% | **W** | **blend** |
| Grant Holmes u14.5 outs | 54.7% | 40.3% | **L** | **carried** |
| Brayan Bello u14.5 outs | 51.7% | 37.3% | **L** | **carried** |
| Robert Gasser o4.5 K | 51.6% | 37.2% | **W** | **blend** |

| | Brier over all 22 graded rows | Brier over the 8 rows that differ |
|---|---|---|
| `blend` | 🔴 **.3230** | 🔴 **.3035** |
| `carried` | ✅ **.3062** | ✅ **.2574** |
| Verdict | ✅ **`carried` is BETTER by .0168** | ✅ **`carried` is BETTER by .0461** |

⛔ **8 ROWS FROM 5 PITCHERS, THREE OF THEM CONTRIBUTING TWO EACH. T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **AND THE MECHANISM IS THE SAME ONE FOR THE SIXTEENTH TIME — `carried` is ALWAYS the LOWER number and 5 of the 8 differing rows LOST — BUT THIS SLATE IS THE WEAKEST FORM OF IT SO FAR AND THE DIFFERENCE MATTERS.** 🔴 **The differing set went 3/8 = 37.5% against a SLATE rate of 40.9% — a gap of THREE POINTS, against twenty on 9/6 and larger still on earlier slates.** ➡️ **So on this board `carried` did NOT win by being pessimistic on a subset that happened to lose; it won because THE WHOLE BOARD was over-confident by 21.6 points and `carried` is simply 14.4 points lower everywhere it differs.** ⛔ **That is still subtracting a constant rather than identifying anything about these arms — it is just a different route to the same verdict, and it is the route that will keep making `carried` look good for as long as the board is over-confident.**

➡️ **RUNNING ACROSS THE SIXTEEN MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 109 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27, 9 on 8/28, 2 on 8/29, 7 on 8/30, 8 on 8/31, 9 on 9/1, 10 on 9/2, 8 on 9/3, 8 on 9/4, 9 on 9/5, 10 on 9/6, 8 on 9/7** *(`3+2+8+8+0+9+2+7+8+9+10+8+8+9+10+8 = 109` ✅, counted against the sixteen enumerated slate figures and not against another number)*.

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS SIXTH FORM IN SIX SLATES — AND THIS ONE IS THE LIMIT CASE. **ONE ARM IS A LEG IN 8 OF 8 PAIRS AND 24 OF 24 PARLAYS.**

🔴 **THE 9/7 PAIRS WENT 0/8 AND THE PARLAYS 0/18 (6 ungraded) — AND `Chase Burns o11.5 outs` IS A LEG IN EVERY SINGLE PAIR AND EVERY SINGLE PARLAY ON THE BOARD. He went 3.0 IP for NINE outs.**

⛔ **THERE IS NOTHING LEFT TO PARTITION. Every prior form of this defect left at least one ticket that avoided the arm — 9/2's 0/24, 9/3's 14/24, 9/4's 1/23, 9/5's 0/8-and-0/23, 9/6's 4/8. This board had none.** ➡️ 🔴 **THE ENTIRE 32-TICKET SURFACE WAS DECIDED BY ONE PITCHER BEFORE ANY OTHER LEG WAS SETTLED, AND THE OTHER LEGS MOSTLY WON: Burns is the ONLY losing leg in 6 of the 8 pairs.**

⚠️ 🔴 **SO THE HONEST READING OF "PAIRS 0/8, PARLAYS 0/18" IS THAT IT IS ONE OBSERVATION REPORTED TWENTY-SIX TIMES, NOT TWENTY-SIX OBSERVATIONS.** ⛔ **No accumulator on this page or in the ledger treats it as twenty-six, and the pair record should not be read as evidence about pair construction on a day like this.**

⚠️ 🔴 **AND THE ROW THAT DID IT WAS THE CARD'S MOST CONFIDENT PLAY: Chase Burns o11.5 outs carried `blend` 97.5, the only `80-plus` row on the board, off a raw record of 25/26.** ➡️ **The 80-plus band therefore went 0/1 at a stated 97.5%. ⛔ n=1; it is reported because it is the whole ticket surface, not because one row measures a band.**

🔴🔴 **AND THE BAND-CEILING CONTRADICTION IS LIVE ON THREE TICKETS AGAIN, THOUGH IT COST NOTHING THIS SLATE BECAUSE EVERY PAIR LOST: pairs at 2.123x, 2.142x and 2.186x are ABOVE BAND under `card.py`'s `in_band` (`TARGET = 2.10`) and INSIDE BAND under the same file's `PARLAY_BANDS[2] = (1.80, 2.20)` and its `parlay_rule` prose.** ➡️ **INSIDE 0/3 · ABOVE 0/5 by the flag; INSIDE 0/6 · ABOVE 0/2 by the prose. Both cuts are reported in the ledger and neither is chosen here.** ⛔ **Open since 8/26; an interactive session must pick one ceiling.**

⚠️ 🔴 **Also re-reported and unchanged: `picks/2026-09-07.json` still carries `model_version: "v4.0"` and `card.py`'s model block still holds the v4.0 constants verbatim, seven days after the September re-fit published v5.0; `card.py`'s `floor_ok` and `clears_price_floor` still write `price > -700`, excluding EXACTLY −700 where Sam's rule is "−700, nothing shorter"; and `.github/workflows/collect.yml`'s header still says "count is 16" where the file enumerates THIRTY-NINE `- cron:` entries.** ⛔ **A headless run cannot test or push.**

**Progress: TABLE M — 16 slates, 355 graded pitcher plays, 117 graded pairs. TABLE M-H — 15 slates, 376 graded hitter rows.**

---

## 🆕 2026-09-09 — THE SEVENTEENTH MACHINE SLATE (2026-09-08): A SEVENTH CONSECUTIVE CARD WRITTEN EXACTLY ONCE, THE **BEST-CALIBRATED BAND CELL THIS TABLE HAS EVER PRODUCED** SITTING INSIDE A BOARD THAT MISSED BY 13.7, `carried` WORSE AGAIN — AND A TICKET SURFACE WHERE **ONE PITCHER IS A LEG IN ALL 8 PAIRS AND ALL 24 PARLAYS, ON TWO DIFFERENT RUNGS THAT SETTLED OPPOSITE WAYS**

`[graded 2026-09-09]` ✅ **`picks/2026-09-08.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 14 GAMES.** **`50 = 25 + 25` ✅.** ✅ **The 25/25 split is back after 9/7's 22/28.**

✅ **AND FOR A SEVENTH CONSECUTIVE DAY THE FILE WAS WRITTEN EXACTLY ONCE: `git log` on a clone deepened to 400 commits names ONE commit touching `picks/2026-09-08.json` — `8c3c75d` at `2026-09-08T14:11:02Z` (`generated_at 14:10:48Z`), pre-slate by roughly EIGHT AND A HALF HOURS against an earliest `commence` of `22:36:00Z`, with `coverage_detail.skipped` carrying no `"already started"` key at all.** ⛔ **The overwrite mechanism is unchanged and simply had no second run to fire; seven clean days is not a fix.**

⚠️ **The slate held FIFTEEN games and the card covers FOURTEEN. The missing one is TEX @ SEA, and it is an absence in a RANKING rather than a dropped game: `props-pitcher/1114.json.gz` — the same snapshot the card's own `odds_pulled_at` names — carries `n_events: 15`, so the game was priced and simply produced no top-50 row.** ⛔ **Same shape as MIN @ CWS on 9/6; named rather than absorbed.**

✅ **ALL 25 PITCHER ROWS ARE GRADED — every carded starter started, so nothing on this slate is excluded from the accumulators below for a scratch.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **SEVENTEENTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23 through 9/8, so the CARDED denominator has not moved for seventeen consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it — argmin on the `w = 1.00` boundary, margin leg cleared, `n` leg at 31 against 100, and the 50/50 UNTOUCHED. The machine population is NOT T15's denominator and may not be substituted into it.**

⚠️ 🔴 **THE DROUGHT IS NOW EIGHTEEN DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.**

⚠️ 🔴 **AND WHAT THE MACHINE SLATE SHOWED IS RECORDED HERE AND NOT FOLDED IN.** **Over its 25 graded rows the mean `model` is 63.3, the mean `raw` 68.2, the mean `blend` 65.7 and the mean `carried` 61.2, against an actual 52.0%.** **Brier: `model` .2712 · `blend` .2924 · `carried` .2937 · `raw` .3246.** ⚠️ 🆕 **THIS IS THE FIRST MACHINE SLATE IN FOUR ON WHICH `model` WINS OUTRIGHT AND `carried` DOES NOT — and the mechanism is the same one the 9/5–9/7 blocks named, running in the other direction: every estimator still sits above the outcome, but the board missed by only 13.7 rather than 21.6, so the LOWEST number is no longer automatically the best one.** ⛔ **Log, do not conclude.**

⚠️ **The "which was closer" tally on this population reads model 17, raw 8, tie 0** *(`17 + 8 + 0 = 25` ✅, counted against the 25 graded rows)*. ⛔ **It is recorded for completeness and it is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no fit.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 9/8 card carries Hard Rock alt ladders on 14 of its 25 pitcher rows — 108 rungs across 14 distinct starts.** 🔴 **IT IS NOT MERGED, for the seventeenth time and for the same reason: T11's `n` is CARDED arms and the machine board is a different population.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket tally on this page.**

**Brandon Young (2 K) · Casey Mize (7 K) · Dean Kremer (3 K) · Hayden Wesneski (3 K) · Jack Perkins (3 K) · Jacob Misiorowski (9 K) · Landen Roupp (2 K) · Michael Wacha (4 K) · Patrick Sandoval (7 K) · Quinn Mathews (4 K) · Sean Burke (2 K) · Sean Manaea (4 K) · Tanner Bibee (1 K) · Tarik Skubal (5 K)** — **14 DISTINCT STARTS**, deduplicated on (pitcher, date). ⛔ **`n` is 14 STARTS, not 108 rungs.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/8. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/7 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared the number and AGAINST when none did; `n=0` is a NO CALL and enters no tally.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **25** | **16/25** | ⚠️ **15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, 15/22, 15/24, 14/25, 10/24, 9/25, 10/25, 13/22, now 16/25 across seventeen slates** |
| **Head-to-head** (prior meetings) | **4** | **3/4** | ⚠️ **three are n=1 and one is n=3** |
| **Head-to-head, NO CALL** | **21** | — | ⛔ **logged and in no tally** (`4 + 21 = 25` ✅) |

⚠️ 🔴 **THE NO-CALL GROUP IS THE LARGEST THIS TABLE HAS EVER CARRIED — 19 `n=0` ROWS PLUS TWO `cleared 1/2` SPLITS (Freddy Peralta o14.5 outs vs ATL, 2 prior starts; Dean Kremer o4.5 K vs DET, 2 prior starts).** 🔴 **The published convention reaches a clean majority and a clean none and does NOT reach a 1-of-2 split, so both are NO CALLS, exactly as the 8/30, 9/7 and 9/8 blocks ruled it.** ⛔ **The convention was not re-decided after seeing the outcome.**

#### ⚠️ ONLY ONE ROW HAD THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREE — THE FEWEST THIS TABLE HAS RECORDED

| Play | Matched class | Head-to-head | Result | Which was right |
|---|---|---|---|---|
| **Drew Anderson u15.5 outs** | **61.1% → FOR** | **0/1 vs MIN → AGAINST** | **L** *(16 outs)* ❌ | ✅ **the head-to-head** |

**ONE disagreeing row: the class right on 0, the head-to-head right on 1** — `0 + 1 = 1` ✅, counted against the single row above (ledger rule 45). ⚠️ **It rests on a single prior meeting and is worth almost nothing on its own.** ⛔ **A one-row disagreement set is not a measurement of either instrument.**

### 🔴🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **SEVENTEENTH CONSECUTIVE RUN** — 🔴 **AND FOR THE SECOND SLATE RUNNING THE THREE ROWS IN THE WINDOW ALL SHARE ONE PRIOR-MEETING DATE**

`[re-checked 2026-09-09]` **`card.py` prints rule 50's head-to-head on all 25 rows and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the substring `days` appears ZERO times anywhere in `picks/2026-09-08.json`.**

✅ **The gap was computed here instead, for every arm carrying a prior meeting, by re-deriving each meeting from the repo's own stored log under a STARTS (`gs == 1`) filter:**

| Pitcher | Opponent | Most recent prior START | Gap |
|---|---|---|---|
| 🔴 **Drew Anderson** | **Minnesota Twins** | **2026-09-02** | 🔴 **6 days** |
| 🔴 **Jacob Misiorowski** | **Chicago Cubs** | **2026-09-02** | 🔴 **6 days** |
| 🔴 **Dean Kremer** | **Detroit Tigers** | **2026-09-02** | 🔴 **6 days** |
| Sandy Alcantara | New York Mets | 2026-08-02 | 37 days |
| Freddy Peralta | Atlanta Braves | 2026-07-06 | 64 days |
| Tanner Bibee | Baltimore Orioles | 2026-04-17 | 144 days |

🔴 **THREE ROWS ARE INSIDE RULE 51's THIRTY-DAY WINDOW AND THE CARD SAID NOTHING ABOUT ANY OF THEM — a third consecutive slate at three, and for the second consecutive slate all three prior meetings fall on the SAME DATE, this time 2026-09-02.** ⚠️ **The nearest row outside the window is Alcantara at 37 days, so the boundary is not close and nothing turns on where the line is drawn.**

✅ **The re-derivation doubles as a control on the card: every head-to-head string it printed reproduces EXACTLY from the same log, 25/25 rows, again only once the filter is applied to STARTS (`gs == 1`) rather than to appearances.**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS ITS SIXTEENTH, SEVENTEENTH AND EIGHTEENTH ROWS — 🔴 **AND FOR THE FIRST TIME ALL THREE CLEAR THE ≥5 K CONDITIONAL**

⛔ **The hand-carded rule-51 table above is CARDED plays and stays at 2 clean instances / 1 confounded. A machine row may not be dropped into it.**

⚠️ 🔴 **STATED FIRST, SO NO ROW CAN BE READ AS SUPPORT FOR A SPECIFICATION IT DOES NOT MEET: the registered rule-51 finding is conditional on a STRONG (≥5 K) FIRST MEETING.** ⛔ **And the registered mean-K specification FAILED at t=−1.78; the threshold version is EXPLORATORY. Nothing below promotes it.**

| # | Pitcher | Opponent | Prior meeting | Gap | Carded row | Result |
|---|---|---|---|---|---|---|
| 16 | **Drew Anderson** | **MIN** | 2026-09-02 — **5 K**, 17 outs, 90 P *(meets the ≥5 K conditional)* | **6 days** | u15.5 outs at blend 75.5 | **16 outs — L** ❌ *(he struck out 4)* |
| 17 | **Jacob Misiorowski** | **CHC** | 2026-09-02 — **5 K**, 12 outs, 92 P *(meets)* | **6 days** | u8.5 K at blend 62.3 | **9 K — L** ❌ |
| 18 | **Dean Kremer** | **DET** | 2026-09-02 — **5 K**, 12 outs, 79 P *(meets)* | **6 days** | o4.5 K at blend 54.6 | **3 K — L** ❌ |

🔴 **THIS IS THE FIRST TIME ANY OF THESE ROWS HAS MET THE CONDITIONAL — the previous three (9/7's Melton, Boyd and Gasser) all failed it at 4, 3 and 4 K — and it is said plainly rather than quietly counted.** ⚠️ **Descriptively, on the exploratory 4+ K bar: Anderson went 5 K → 4 K (cleared), Misiorowski 5 K → 9 K (cleared), Kremer 5 K → 3 K (missed). TWO of three cleared.** ⛔ **n = 3. That is not evidence for or against a 74.6%-vs-67.1% split and it is not folded into anything.** ⚠️ 🔴 **What IS worth recording separately is that ALL THREE CARDED ROWS LOST, on three different markets and three different sides — which is a fact about this board's calibration, not about rule 51.** ⛔ **THREE observations. Nothing is re-specified.** **The machine-population log now holds EIGHTEEN rows.**

### 🟡 THE `carried` SHADOW — 9/8. 🔴 **WORSE — THE TWELFTH TIME IN SEVENTEEN SLATES — AND THE MECHANISM IS THE USUAL ONE RUNNING BACKWARDS.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 8 of the 25 graded rows, across 6 pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Hayden Wesneski o3.5 K | 84.5% | 73.5% | **L** | **carried** |
| Jack Perkins o3.5 K | 79.2% | 64.8% | **L** | **carried** |
| Drew Anderson u15.5 outs | 75.5% | 61.1% | **L** | **carried** |
| Jack Perkins u15.5 outs | 75.0% | 60.6% | **W** | **blend** |
| Bubba Chandler o14.5 outs | 67.8% | 53.4% | **W** | **blend** |
| Sean Burke u6.5 K | 63.0% | 48.6% | **W** | **blend** |
| Sean Manaea u5.5 K | 61.3% | 46.9% | **W** | **blend** |
| Sean Burke u17.5 outs | 56.8% | 42.4% | **W** | **blend** |

| | Brier over all 25 graded rows | Brier over the 8 rows that differ |
|---|---|---|
| `blend` | ✅ **.2924** | ✅ **.3188** |
| `carried` | 🔴 **.2937** | 🔴 **.3230** |
| Verdict | 🔴 **`carried` is WORSE by .0013** | 🔴 **`carried` is WORSE by .0042** |

⛔ **8 ROWS FROM 6 PITCHERS, TWO OF THEM CONTRIBUTING TWO EACH. T21/T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

⚠️ 🔴 **THE MECHANISM IS THE SAME ONE FOR THE SEVENTEENTH TIME AND IT IS WHY THE VERDICT FLIPPED: `carried` is ALWAYS the LOWER number — 14.0 points lower on average here — so it wins when the differing rows lose and loses when they win.** 🔴 **This slate the differing set went 5/8 = 62.5% against a SLATE rate of 52.0%, so the subset BEAT the board by ten points and the pessimistic column was punished for it.** ⛔ **That is the exact converse of 9/7, where the subset went 3/8 against a board of 40.9% and `carried` looked good.** ➡️ **Neither result identifies anything about these arms. It is a constant subtraction being scored against whichever way a small subset happened to fall, and it will keep alternating for as long as that is all it is.**

➡️ **RUNNING ACROSS THE SEVENTEEN MACHINE SLATES, as a sum of enumerated tallies and NOT as a finding: `carried` has differed on 117 rows total — 3 on 8/23, 2 on 8/24, 8 on 8/25, 8 on 8/26, 0 on 8/27, 9 on 8/28, 2 on 8/29, 7 on 8/30, 8 on 8/31, 9 on 9/1, 10 on 9/2, 8 on 9/3, 8 on 9/4, 9 on 9/5, 10 on 9/6, 8 on 9/7, 8 on 9/8** *(`3+2+8+8+0+9+2+7+8+9+10+8+8+9+10+8+8 = 117` ✅, counted against the seventeen enumerated slate figures and not against another number)*.

### 🔴 THE BAND SHAPE — AND THE ONE CELL THAT LANDED DEAD ON ITS OWN NUMBER

| Band | Record | Mean claim | Gap |
|---|---|---|---|
| **80-plus** | **0/1** | 84.5 | 🔴 **−84.5** |
| **70-80** | **1/5** | 75.2 | 🔴 **−55.2** |
| **60-70** | **9/14** | 64.31 | ✅ 🆕 **−0.0** |
| **under-60** | **3/5** | 56.42 | ✅ **+3.6** |

`1 + 5 + 14 + 5 = 25` ✅, `0 + 1 + 9 + 3 = 13` ✅.

✅ 🆕 **THE 60–70 CELL IS THE CLOSEST ANY BAND HAS EVER COME ON THIS TABLE: 14 rows claiming a mean 64.31% and delivering 64.3%.** ⚠️ 🔴 **AND IT IS REPORTED AS A COINCIDENCE, NOT AS CALIBRATION.** **n = 14. One row flipping moves it 7 points.** ⛔ **The band's own cumulative record in the runner's `record.json` is 94/177 = 53.1%, which is where the evidence actually is; a single cell landing on its number is what a small sample does sometimes.**

🔴 **THE SHAPE ABOVE THAT CELL IS THE FAMILIAR ONE AND IT IS THE SAME DIRECTION AS EVERY PRIOR SLATE: the two most confident bands missed by 84.5 and 55.2 points on n = 1 and n = 5.** ⛔ **NOT ONE OF THOSE IS A MEASUREMENT OF A BAND. Log, do not conclude.**

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS SEVENTH FORM IN SEVEN SLATES — 🆕 **AND THIS ONE IS NEW: ONE PITCHER IS A LEG IN 8 OF 8 PAIRS AND 24 OF 24 PARLAYS, ON TWO RUNGS THAT SETTLED OPPOSITE WAYS**

🔴 **`Hayden Wesneski` IS A LEG IN EVERY SINGLE TICKET ON THE BOARD — but not as one leg.** **`o3.5 K` appears in 7 of 8 pairs and 20 of 24 parlays; `o2.5 K` appears in the remaining 1 pair and the remaining 4 parlays.** `7 + 1 = 8` ✅ and `20 + 4 = 24` ✅, counted against the enumerated tickets; **no ticket carries both rungs.**

🔴 **HE STRUCK OUT THREE. `o2.5 K` WON AND `o3.5 K` LOST — THE SAME START, ONE RUNG APART, SETTLING IN OPPOSITE DIRECTIONS.** ➡️ 🔴 **SO THE ENTIRE 32-TICKET SURFACE TURNED ON WHICH RUNG THE POOL HAPPENED TO PICK, AND FOR THE FIVE TICKETS THAT PICKED THE WINNING RUNG IT DID NOT MATTER ANYWAY — every one of them lost on a different leg (Jack Perkins o3.5 K ×2, Kaelen Culpepper o0.5 H, and Quinn Mathews u16.5 outs ×2).**

⚠️ **This is a sharper form of the 9/7 limit case rather than a softer one.** **On 9/7 one leg was on all 32 tickets and lost, so there was nothing to partition. Here one ARM is on all 32 tickets, the pool DID diversify across two of his rungs — and the diversification bought nothing, because the alternative rung's tickets lost elsewhere.** ➡️ 🔴 **"PAIRS 0/8, PARLAYS 0/24" IS ONE START REPORTED THIRTY-TWO TIMES, NOT THIRTY-TWO JUDGEMENTS.** ⛔ **It is not evidence about ticket construction and must not be read as any.**

✅ **All 8 pairs and all 24 parlays are DISTINCT — the duplicate-ticket defect did not recur, for a ninth consecutive slate.**

🔴🔴 **AND THE BAND-CEILING CONTRADICTION IS LIVE ON TWO TICKETS, though it cost nothing this slate because every pair lost: pairs at 2.140x and 2.171x are ABOVE BAND under `card.py`'s `in_band` (`TARGET = 2.10`) and INSIDE BAND under the same file's `PARLAY_BANDS[2] = (1.80, 2.20)` and its own `parlay_rule` prose.** **By the flag the split is INSIDE 0/5 · ABOVE 0/3; by the prose it is INSIDE 0/7 · ABOVE 0/1.** ⛔ **Open since 8/26 and re-reported by every grading run since. An interactive session must pick one ceiling; a grading run does not.**

⚠️ 🔴 **Also re-reported and unchanged: `picks/2026-09-08.json` still carries `model_version: "v4.0"` and `card.py` still declares `MODEL_VERSION = "v4.0"` with its model block holding the v4.0 constants verbatim, EIGHT days after the September re-fit published v5.0; `card.py`'s `floor_ok` and `clears_price_floor` still write `price > -700`, excluding exactly −700 where Sam's rule is "−700, nothing shorter"; and `.github/workflows/collect.yml`'s header still says "the count is 16" where the file now enumerates FORTY `- cron:` entries, one more than the thirty-nine counted on 9/7.** ⛔ **REPORTED, NOT FIXED — a headless run cannot test a change and cannot push one.**

~~**Progress: TABLE M — 17 slates, 380 graded pitcher plays, 125 graded pairs. TABLE M-H — 16 slates, 399 graded hitter rows.**~~ ⚠️ 🔴 **STRUCK 2026-09-13 — CORRECT WHEN WRITTEN (2026-09-09) AND NEVER UPDATED BY THE 9/10, 9/11 OR 9/12 RUNS. The live figure is at the foot of the 2026-09-13 block below.**

## 🆕 2026-09-10 — THE EIGHTEENTH MACHINE SLATE (2026-09-09): AN EIGHTH CONSECUTIVE CARD WRITTEN EXACTLY ONCE, THE **NARROWEST BRIER SPREAD BETWEEN THE FOUR ESTIMATORS THIS TABLE HAS EVER PRODUCED**, `carried` BETTER AGAIN BY AN AMOUNT THAT ORDERS NOTHING — AND A TICKET SURFACE WHERE **ONE ARM IS A LEG IN ALL 32 TICKETS ON TWO RUNGS THAT BOTH LOST**

`[graded 2026-09-10]` ✅ **`picks/2026-09-09.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 14 GAMES.** **`50 = 25 + 25` ✅.**

✅ **AND FOR AN EIGHTH CONSECUTIVE DAY THE FILE WAS WRITTEN EXACTLY ONCE: `git log` on a clone deepened to 403 commits names ONE commit touching `picks/2026-09-09.json` — `ff7f920` at `2026-09-09T14:13:41Z` (`generated_at 14:13:27Z`), with `coverage_detail.skipped` carrying no `"already started"` key at all.** ⚠️ 🔴 **THE PRE-SLATE MARGIN IS THE NARROWEST ON AN UNDAMAGED CARD SO FAR — 2h 57m against the earliest `commence` of `2026-09-09T17:11:00Z`, checked row by row across all 50 rows, where 9/8 had eight and a half hours.** ⛔ **Still pre-slate, still zero games dropped, and the overwrite mechanism is unchanged — eight clean days is not a fix.**

⚠️ **The slate held FIFTEEN games and the card covers FOURTEEN. The missing one is CHC @ MIL, and it is an absence in a RANKING rather than a dropped game: `props-pitcher/1113.json.gz` — the same snapshot the card's own `odds_pulled_at` names — carries `n_events: 15` and enumerates Chicago Cubs @ Milwaukee Brewers among them.** ⛔ **Same shape as TEX @ SEA on 9/8; named rather than absorbed.**

✅ **ALL 25 PITCHER ROWS ARE GRADED — every carded starter started, so nothing on this slate is excluded from the accumulators below for a scratch.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **EIGHTEENTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play was carded on 8/23 through 9/9, so the CARDED denominator has not moved for eighteen consecutive slates.** ⛔ **T15 stands exactly where 2026-08-23 left it — argmin on the `w = 1.00` boundary, margin leg cleared, `n` leg at 31 against 100, and the 50/50 UNTOUCHED. The machine population is NOT T15's denominator and may not be substituted into it.**

⚠️ 🔴 **THE DROUGHT IS NOW NINETEEN DAYS SINCE THE LAST HAND-BUILT CARD.** ⛔ **An observation, not a licence to widen the denominator.**

⚠️ 🔴 **AND WHAT THE MACHINE SLATE SHOWED IS RECORDED HERE AND NOT FOLDED IN.** **Over its 25 graded rows the mean `model` is 65.4, the mean `raw` 66.9, the mean `blend` 66.1 and the mean `carried` 59.2, against an actual 52.0%.** **Brier: `carried` .2896 · `blend` .2902 · `raw` .2937 · `model` .2939.** ⚠️ 🆕 **THE FOUR ESTIMATORS SPAN 0.0043 OF BRIER — the narrowest spread in eighteen slates, against gaps of .05 to .12 on comparable boards.** ⛔ **At n=25 a 0.0043 spread orders nothing at all, and the ranking above is printed only so it cannot be quietly reported as a result later. Log, do not conclude.**

⚠️ **The "which was closer" tally on this population reads model 12, raw 13, tie 0** *(`12 + 13 + 0 = 25` ✅, counted against the 25 graded rows)*. ⛔ **It is recorded for completeness and it is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no fit.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 9/9 card carries Hard Rock alt ladders on 11 of its 25 pitcher rows — 77 rungs across 11 distinct starts.** 🔴 **IT IS NOT MERGED, for the eighteenth time and for the same reason: T11's `n` is CARDED arms and the machine board is a different population.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket tally on this page.**

**Cody Bradford (1 K) · Foster Griffin (4 K) · Griffin Jax (2 K) · Hunter Brown (7 K) · Jackson Kent (2 K) · Keider Montero (2 K) · Lake Bachar (3 K) · Robert Stock (4 K) · Walker Buehler (4 K) · Yoshinobu Yamamoto (10 K) · Zac Gallen (1 K)** — **11 DISTINCT STARTS**, deduplicated on (pitcher, date). ⛔ **`n` is 11 STARTS, not 77 rungs.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/9. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/8 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared the number and AGAINST when none did; `n=0` is a NO CALL and enters no tally.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **25** | 🔴 **11/25** | ⚠️ **15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, 15/22, 15/24, 14/25, 10/24, 9/25, 10/25, 13/22, 16/25, now 11/25 across eighteen slates** |
| **Head-to-head** (prior meetings) | **8** | 🔴 **2/8** | ⚠️ **all eight rest on a SINGLE prior meeting, and this is the instrument's worst reading yet** |
| **Head-to-head, NO CALL** | **17** | — | ⛔ **logged and in no tally** (`8 + 17 = 25` ✅) |

⚠️ 🔴 **EVERY ONE OF THE EIGHT HEAD-TO-HEAD CALLS IS `n=1`.** ⛔ **A 2/8 on eight single-start samples is not a measurement of the head-to-head and is not evidence against rule 50; it is eight coin flips reported as a fraction because the convention requires them to be.**

#### ⚠️ FIVE ROWS HAD THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREE — AND THE CLASS TOOK THREE

| Play | Matched class | Head-to-head | Result | Which was right |
|---|---|---|---|---|
| **Foster Griffin u5.5 K** | **57.1% → FOR** | **0/1 vs BAL → AGAINST** | **W** *(4 K)* ✅ | ✅ **the class** |
| **Keider Montero u17.5 outs** | **60.6% → FOR** | **0/1 vs MIN → AGAINST** | **W** *(12 outs)* ✅ | ✅ **the class** |
| **Ryan Johnson o14.5 outs** | **64.9% → FOR** | **0/1 vs BOS → AGAINST** | **W** *(18 outs)* ✅ | ✅ **the class** |
| **Shane Baz o16.5 outs** | **47.6% → AGAINST** | **1/1 vs CLE → FOR** | **W** *(17 outs)* ✅ | ✅ **the head-to-head** |
| **Robert Stock u4.5 K** | **47.4% → AGAINST** | **1/1 vs MIA → FOR** | **W** *(4 K)* ✅ | ✅ **the head-to-head** |

**FIVE disagreeing rows: the class right on 3, the head-to-head right on 2** — `3 + 2 = 5` ✅, counted against the rows above (ledger rule 45). ⚠️ 🆕 **AND ALL FIVE WON, which is why the split is exactly the split of which instrument said FOR: on a slate where every disagreeing row cleared, "who was right" collapses into "who was bullish".** ⛔ **That is a property of this five-row sample, not of either instrument.**

### 🔴🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **EIGHTEENTH CONSECUTIVE RUN** — ✅ **BUT FOR THE FIRST TIME SINCE IT WAS FOUND IT COST NOTHING, BECAUSE NO ROW WAS IN THE WINDOW**

`[re-checked 2026-09-10]` **`card.py` prints rule 50's head-to-head on all 25 rows and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the substring `days` appears ZERO times anywhere in `picks/2026-09-09.json`.**

✅ **The gap was computed here instead, for every arm carrying a prior meeting, by re-deriving each meeting from the repo's own stored log under a STARTS (`gs == 1`) filter:**

| Pitcher | Opponent | Most recent prior START | Gap |
|---|---|---|---|
| Robert Stock | Miami Marlins | 2026-08-02 | 38 days |
| Janson Junk | New York Mets | 2026-07-31 | 40 days |
| Ryan Johnson | Boston Red Sox | 2026-07-05 | 66 days |
| Foster Griffin | Baltimore Orioles | 2026-06-27 | 74 days |
| Keider Montero | Minnesota Twins | 2026-06-11 | 90 days |
| Shane Baz | Cleveland Guardians | 2026-04-16 | 146 days |

✅ 🆕 **ZERO ROWS ARE INSIDE RULE 51's THIRTY-DAY WINDOW — the first slate since the defect was found on which the missing field could not have changed a single line, the nearest row being Stock at 38 days.** ⛔ **A check that could not have fired is not a check that works, and the defect is re-reported at full strength rather than downgraded.** **Three consecutive slates carried three in-window rows each; this one carries none, which is slate composition and nothing else.**

✅ **The re-derivation doubles as a control on the card: every head-to-head string it printed reproduces EXACTLY from the same log, 25/25 rows, again only once the filter is applied to STARTS (`gs == 1`) rather than to appearances.**

### 🆕 🔴 AND THAT FILTER IS ALSO A WORDING DEFECT, FOUND BY THE SAME CONTROL AND REPORTED NOT FIXED

`[measured 2026-09-10]` **`card.py` prints `never faced <TEAM> this season` when what it computes is `never STARTED against <TEAM> this season`.** **Lake Bachar's two carded rows both print `never faced CWS this season`; his own stored log carries a 2026-03-30 RELIEF appearance against Chicago — 9 outs, 3 K, 42 pitches, a third of a game against that lineup.**

✅ **The COMPUTATION is what rule 50 specifies and it is right — the tiebreaker is about prior STARTS.** ⛔ **The STRING overclaims, and it overclaims hardest on exactly the profile where it matters: Bachar was carded at `o6.5 outs`, an opener/bulk line, and a prior nine-out relief outing against that lineup is the most relevant thing the log holds about him.** ➡️ **Reported to an interactive session; a grading run does not touch the code.**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS NO ROWS THIS SLATE, AND THAT IS RECORDED RATHER THAN LEFT BLANK

⛔ **The hand-carded rule-51 table above is CARDED plays and stays at 2 clean instances / 1 confounded. A machine row may not be dropped into it.**

**No carded arm faced its opponent inside the thirty-day window, so the machine-population log stays at EIGHTEEN rows.** ⚠️ **This is the first slate in five that adds none.** ⛔ **An empty increment is an observation about the schedule, not about rule 51, and nothing is re-specified.**

### 🟡 THE `carried` SHADOW — 9/9. ✅ **BETTER — THE SIXTH TIME IN EIGHTEEN SLATES — BY .0006, WHICH ORDERS NOTHING.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 12 of the 25 graded rows, across 8 pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Daniel Lynch IV u14.5 outs | 79.3% | 64.9% | **L** | **carried** |
| Lake Bachar o6.5 outs | 73.6% | 59.2% | **L** | **carried** |
| Reynaldo López u15.5 outs | 72.2% | 57.8% | **W** | **blend** |
| Keider Montero o2.5 K | 69.9% | 55.5% | **L** | **carried** |
| Robert Stock u14.5 outs | 67.6% | 53.2% | **W** | **blend** |
| Lake Bachar o2.5 K | 63.9% | 49.5% | **W** | **blend** |
| Keider Montero u17.5 outs | 63.0% | 48.6% | **W** | **blend** |
| Janson Junk o14.5 outs | 61.5% | 47.1% | **L** | **carried** |
| Robert Stock u4.5 K | 61.9% | 47.5% | **W** | **blend** |
| Ryan Johnson o14.5 outs | 59.8% | 45.4% | **W** | **blend** |
| Griffin Jax o4.5 K | 60.5% | 46.1% | **L** | **carried** |
| Griffin Jax o14.5 outs | 58.3% | 43.9% | **W** | **blend** |

| | Brier over all 25 graded rows | Brier over the 12 rows that differ |
|---|---|---|
| `blend` | 🔴 **.2902** | 🔴 **.2778** |
| `carried` | ✅ **.2896** | ✅ **.2766** |
| Verdict | ✅ **`carried` is BETTER by .0006** | ✅ **`carried` is BETTER by .0012** |

⚠️ 🔴 **AND THE MECHANISM RAN BACKWARDS FOR THE FIRST TIME IN EIGHTEEN SLATES, WHICH IS THE ONLY PART WORTH RECORDING.** **On every prior slate `carried` won by being LOWER on a subset that LOST: here the differing subset went 7/12 = 58.3%, BETTER than the slate's own 52.0%, and `carried` still won — because the whole board sat 14.1 points over the outcome, so the lower number was closer even on rows that cleared.** ⛔ **A .0006 margin at n=25 is noise however it arose. T21/T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

**Running total 129 differing rows across eighteen slates** *(109 through sixteen + 8 on 9/8 + 12 on 9/9)*. ⚠️ **The "closer" tally on the differing rows alone reads blend 7, carried 5 — the OPPOSITE ordering to the Brier, on the same twelve rows, because one row can be closer more often and worse on average.** ⛔ **Both are printed; neither is a verdict.**

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS EIGHTH FORM IN EIGHT SLATES — 🆕 **ONE ARM ON ALL 32 TICKETS, ON TWO RUNGS THAT BOTH LOST**

🔴 **`Zac Gallen` IS A LEG IN ALL 8 PAIRS AND ALL 24 PARLAYS.** **`o11.5 outs` in 7 of 8 pairs and all 24 parlays; `o1.5 K` in the remaining 1 pair** — `7 + 1 = 8` ✅, `24 + 0 = 24` ✅, counted against the enumerated tickets. **He recorded 10 outs and 1 K in 3.1 IP on 68 pitches, and BOTH rungs lost.**

⚠️ 🔴 **THIS IS THE HARD FORM OF 9/8's CASE, NOT A REPEAT: on 9/8 Wesneski's two rungs settled in OPPOSITE directions, so the pool's diversification at least produced a split. Here it produced nothing — both rungs went the same way and all 32 tickets died on one start.** **He was the board's #1 row at a blend of 92.6, the single most confident number on the card.** ➡️ 🔴 **"PAIRS 0/8, PARLAYS 0/24" IS ONE START REPORTED THIRTY-TWO TIMES.** ⛔ **It is not evidence about ticket construction and its aggregate must never be quoted as a rate.**

⚠️ **The band-ceiling contradiction is re-reported and did not bite: by `in_band` (`TARGET = 2.10`) the pairs are INSIDE 0/5 · ABOVE 0/3; under the same file's `PARLAY_BANDS[2] = (1.80, 2.20)` and its `parlay_rule` prose they are INSIDE 0/6 · ABOVE 0/2. ONE ticket (2.143x) moves, and every pair lost, so the disagreement cost nothing this slate — exactly as on 9/8.** ⛔ **Open since 8/26. An interactive session must pick one ceiling.**

---

## 🆕 2026-09-11 — THE NINETEENTH MACHINE SLATE (2026-09-10): A NINTH CONSECUTIVE CARD WRITTEN EXACTLY ONCE, THE **NARROWEST PRE-SLATE MARGIN EVER RECORDED**, A THIRTEEN-ROW PITCHER BOARD THAT LANDED **45.1 POINTS UNDER ITSELF**, `carried` BETTER ON THREE ROWS THAT SETTLE NOTHING — AND A SEASON-TOTAL CONTROL THAT **FABRICATED TWICE AND TRUNCATED TWICE IN ONE RUN**

`[graded 2026-09-11]` ✅ **`picks/2026-09-10.json` AS COMMITTED IS 50 PLAYS — 13 PITCHER AND 37 HITTER — ACROSS 5 GAMES.** **`50 = 13 + 37` ✅.** ⚠️ 🆕 **THE FIRST CARD SINCE TABLE M OPENED THAT IS NOT ROUGHLY 25 + 25, AND THE CAUSE IS THE SLATE: 2026-09-10 WAS A FIVE-GAME THURSDAY AND ONLY 19 PITCHER ROWS PRICED AT ALL.**

✅ **Written EXACTLY ONCE for a ninth consecutive day — `8f3ddaf` at `2026-09-10T14:08:58Z`, `generated_at 14:08:53Z`, no `"already started"` key in `coverage_detail.skipped`, zero games dropped.** ⚠️ 🔴 **THE PRE-SLATE MARGIN IS THE NARROWEST THIS TABLE HAS RECORDED — 2h 06m against the earliest `commence` of `2026-09-10T16:15:00Z`, checked across all 50 rows, after 2h 57m on 9/9 and eight and a half hours on 9/8.** ⛔ **Three consecutive slates of shortening margin is the mechanism that destroyed the 8/27 and 8/29 cards, and it is reported for that reason and not because anything went wrong today.**

✅ **ALL 13 PITCHER ROWS ARE GRADED — every carded starter started.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **NINETEENTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play has been carded since 8/22. T15's denominator is CARDED plays and the machine board is a different population, so nothing was substituted into it.** ⚠️ **The drought is now twenty days.**

⚠️ **Brier on the machine population, for the record and in NO T15 denominator:** `raw` **.3096** · `carried` **.3113** · `blend` **.3271** · `model` **.3597** — **means `model` 63.2 · `raw` 57.7 · `blend` 60.4 · `carried` 57.1 against an actual 15.4%.** ⛔ **On a board that missed by 45 points the Brier ordering is just "lower was better", which is arithmetic and not evidence. LOG, DO NOT CONCLUDE.**

⚠️ **The "which was closer" tally on this population reads model 6, raw 7, tie 0** *(`6 + 7 + 0 = 13` ✅, counted against the 13 graded rows)*. ⛔ **It is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no fit.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 9/10 card carries Hard Rock alt ladders on 7 of its 13 pitcher rows — 57 rungs across 7 distinct starts.** 🔴 **IT IS NOT MERGED, for the nineteenth time and for the same reason: T11's `n` is CARDED arms and the machine board is a different population.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket tally on this page.**

**Jacob deGrom (12 K) · Jared Jones (8 K) · Logan Gilbert (11 K) · Max Fried (7 K) · Nick Martinez (3 K) · Ryan Feltner (2 K) · Zack Wheeler (9 K)** — **7 DISTINCT STARTS**, deduplicated on (pitcher, date). ⛔ **`n` is 7 STARTS, not 57 rungs.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/10. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/9 blocks, fixed before it was used: the matched class ARGUED FOR the play when its all-starts rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared the number and AGAINST when none did; `n=0` is a NO CALL and enters no tally.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **13** | 🔴 **4/13** | ⚠️ **15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, 15/22, 15/24, 14/25, 10/24, 9/25, 10/25, 13/22, 16/25, 11/25, now 4/13 across nineteen slates** |
| **Head-to-head** (prior meetings) | **3** | 🔴 **0/3** | ⚠️ **two arms, three rows: Logan Gilbert (2/3 vs TEX → FOR) and Jacob deGrom on BOTH his rows (3/3 vs SEA → FOR). All three lost** |
| **Head-to-head, NO CALL** | **10** | — | ⛔ **logged and in no tally** (`3 + 10 = 13` ✅) |

⚠️ 🔴 **THE TWO INSTRUMENTS DISAGREED ON ZERO ROWS THIS SLATE — the first time that has happened since this tally opened.** **On all three head-to-head calls the class also said FOR, and all three lost, so there is nothing to separate them.** ⛔ **A 0/3 on two arms is not a measurement of the head-to-head; it is one bad night for two pitchers reported three times.**

⚠️ **And the class's 4/13 is its worst-looking reading, which is a property of the SLATE and not of the instrument: eleven of the thirteen rows lost, so any instrument that said FOR on eight of them was going to look bad. The class said FOR on 8 and AGAINST on 5; it was right on 1 of the 8 FORs and 3 of the 5 AGAINSTs** — `1 + 3 = 4` ✅ and `8 + 5 = 13` ✅.

> ⚠️ 🔴 **CORRECTION APPENDED 2026-09-12 BY THE NEXT GRADING RUN — PRE-PUBLISH CHECK 28. THE TOTAL IS RIGHT AND THE SPLIT IS NOT, WHICH IS THE EXACT SHAPE THE CHECK EXISTS FOR.** ⛔ **THE 4/13 IS NOT ALTERED AND NO GRADED ROW, BRIER VALUE OR BUCKET COUNT IS TOUCHED.** `[measured 2026-09-12 by re-reading `class.all_pct` off all 13 rows of `picks/2026-09-10.json`]` **Under the convention THIS BLOCK declares — "the matched class ARGUED FOR the play when its all-starts rate is ≥50%" — the split is NINE FORs and FOUR AGAINSTs, right on 1 of 9 and 3 of 4.** **The single row that moves is Martín Pérez u15.5 outs, whose all-starts rate is 53.1% (FOR) against a 4+IP rate of 48.3% (AGAINST).** ⚠️ **And under the 4+IP reading the AGAINST-right count becomes 4 of 5, not 3 — so the published split reconciles to its own total under NEITHER axis.** ➡️ **The all-starts axis is the right one here for a second reason: the 8/22 finding is that the 4+IP split is BIASED on outs bets at a threshold of 12 or higher, and Pérez's row is an outs bet at 15.5.**

> ⚠️ 🔴 **AND A SECOND PROSE COUNT IN THIS SAME BLOCK, CORRECTED THE SAME WAY: the Changelog entry below says "five of ten starters went seven innings" on 9/10.** `[measured 2026-09-12 by enumerating all ten `started: true` rows in `data/2026-09-10/results/final.json.gz`]` 🔴 **FOUR did — Martín Pérez, Zack Wheeler, Logan Gilbert and Jared Jones, every one at exactly 7.0 IP.** ✅ **The other half of the sentence is right: four struck out eight or more (deGrom 12, Gilbert 11, Wheeler 9, Jones 8).** ⛔ **Neither correction changes a graded outcome; both are recorded because a count stated in prose must reconcile against the rows beneath it.**

### 🔴🔴 THE PRE-PUBLISH CHECK 36 DEFECT IN `card.py` IS STILL THERE — **NINETEENTH CONSECUTIVE RUN** — ⚠️ **AND IT COST NOTHING, BECAUSE NO ROW IS IN THE WINDOW**

`[re-checked 2026-09-11]` **`card.py` prints rule 50's head-to-head on all 13 rows and STILL NEVER PRINTS RULE 51's GAP IN DAYS.** ✅ **Verified mechanically again: the substring `days` appears ZERO times anywhere in `picks/2026-09-10.json`.**

⚠️ 🔴 **AND THIS IS NOW A CONTRADICTION WORTH NAMING RATHER THAN A PLAIN DEFECT: `claude/pick-ledger.md` rule 189, written 2026-09-11, records the gap-in-days omission as CLOSED in the code.** ⛔ **The 9/10 card was generated at `14:08:53Z` on 2026-09-10 and the fix (`d64540f`) landed at `2026-09-11T04:04Z`, so this card PREDATES it.** ➡️ **The defect is real on THIS card and is expected to be absent from the next one. The next grading run should check, and should record a CLOSE rather than a twentieth consecutive report if the field is present.**

✅ **The gap was computed here instead, for every arm carrying a prior meeting, by re-deriving each meeting from the repo's own stored log under a STARTS (`gs == 1`) filter:**

| Pitcher | Opponent | Most recent prior START | Gap |
|---|---|---|---|
| Logan Gilbert | Texas Rangers | 2026-07-26 | 46 days |
| Jacob deGrom | Seattle Mariners | 2026-07-26 | 46 days |

✅ 🆕 **ZERO ROWS ARE INSIDE RULE 51's THIRTY-DAY WINDOW — the second such slate since the defect was found — so the missing field could not have changed a single line, the nearest row being 46 days.** ⛔ **A check that could not have fired is not a check that works, and the defect is re-reported at full strength rather than downgraded.**

✅ **The re-derivation doubles as a control on the card: every head-to-head string it printed reproduces EXACTLY from the same log, 13/13, again only once the filter is applied to STARTS (`gs == 1`) rather than to appearances — and the `never faced` wording defect recorded on 9/10 is therefore re-confirmed, not fixed.**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS NO ROWS THIS SLATE, AND THAT IS RECORDED RATHER THAN LEFT BLANK

⛔ **The hand-carded rule-51 table above is CARDED plays and stays at 2 clean instances / 1 confounded. A machine row may not be dropped into it.**

**No carded arm faced its opponent inside the thirty-day window, so the machine-population log stays at EIGHTEEN rows.** ⛔ **An empty increment is an observation about the schedule, not about rule 51, and nothing is re-specified.**

### 🟡 THE `carried` SHADOW — 9/10. ✅ **BETTER — THE SEVENTH TIME IN NINETEEN SLATES — ON A DIFFERING SET OF THREE.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 3 of the 13 graded rows, across 3 pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Ryan Feltner u4.5 K | 67.5% | 53.1% | **W** | **blend** |
| Cristian Javier u14.5 outs | 65.7% | 51.3% | **L** | **carried** |
| Martín Pérez u15.5 outs | 59.4% | 45.0% | **L** | **carried** |

| | Brier over all 13 graded rows | Brier over the 3 rows that differ |
|---|---|---|
| `blend` | 🔴 **.3271** | 🔴 **.2967** |
| `carried` | ✅ **.3113** | ✅ **.2285** |
| Verdict | ✅ **`carried` is BETTER by .0158** | ✅ **`carried` is BETTER by .0682** |

⚠️ 🔴 **THE MECHANISM IS THE ORDINARY ONE AND THE MARGIN IS MEANINGLESS: `carried` is simply LOWER, the board sat 45 points over the outcome, and the differing subset went 1/3.** ⛔ **A .0158 margin at n=13 on a board that missed by 45 points measures the direction of the miss, not the estimator. T21/T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

**Running total 132 differing rows across nineteen slates** *(129 through eighteen + 3 on 9/10)*. ⚠️ **The "closer" tally on the differing rows alone reads blend 1, carried 2 — the SAME ordering as the Brier this time, on three rows, which settles nothing either.** ⛔ **Both are printed; neither is a verdict.**

### 🔴🔴 🆕 THE FINDING THAT MATTERS MOST THIS RUN IS ABOUT THE CONTROL, NOT THE CARD

`[measured 2026-09-11 — five failures of the live `statsapi` route in a single run, full detail in `claude/pick-ledger.md`'s 2026-09-11 control block]`

**Two `stats=season` calls returned DOMAIN-VALID BUT WRONG season totals (Ryan Feltner `20 · 97.2 · 70` against a true `22 · 111.2 · 83`; Logan Gilbert `27 · 160.1 · 166` against a true `29 · 172.0 · 187`), two `stats=gameLog` calls returned SILENTLY TRUNCATED logs missing the carded start (Nick Martinez ending 8/23, Jacob deGrom ending 8/20), and one enumerated 23 splits correctly while STATING that there were 22.**

🔴 **THE CONSEQUENCE FOR THIS PAGE: the season-total delta is the control every accumulator on this page ultimately rests on, and in its SUMMARISED form it would have FALSELY FAILED two correct lines this run.** ✅ **In its ENUMERATED form — list every split, sum locally — it was right on all nine carded starters, 9/9 exact on outs, strikeouts and games started.** ➡️ 🔴 **A fetched TOTAL is a summary. Enumerate and sum, always.**


---

## 🆕 2026-09-12 — THE TWENTIETH MACHINE SLATE (2026-09-11): A TENTH CONSECUTIVE CARD WRITTEN EXACTLY ONCE, **THE FIRST CARD IN THIS TABLE PRICED BY MODEL v5.0**, **RULE 51's INSTRUMENT FIRING FOR THE FIRST TIME SINCE IT WAS BUILT**, AND A `carried` COLUMN THAT WAS BETTER AGAIN ON FIVE ROWS THAT SETTLE NOTHING

`[graded 2026-09-12]` ✅ **`picks/2026-09-11.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 14 GAMES.** **`25 + 25 = 50` ✅.**

✅ **Written EXACTLY ONCE for a tenth consecutive day — `9ab382f` at `2026-09-11T14:07:25Z`, `generated_at 14:07:11Z`, no `"already started"` key in `coverage_detail.skipped`, zero games dropped.** ✅ **The pre-slate margin recovered to 4h 13m against the earliest `commence` of `2026-09-11T18:21:00Z`, after 2h 06m on 9/10 and 2h 57m on 9/9 — the shortening trend reported for three slates did not continue.**

⚠️ 🔴 **A COVERAGE GAP, NAMED: the slate was FIFTEEN games and the card covers FOURTEEN. `TEX @ AZ` carries no row of any kind.** **`coverage_detail.skipped` reads `no game log: 23` and `insufficient inputs: 8`.** ⛔ **That says what the card's OWN INPUTS contained, not that the game had no priced props.**

🔴 🆕 **AND THE POPULATION CHANGED UNDER THIS PAGE'S ACCUMULATORS, WHICH IS RECORDED BEFORE ANY NUMBER IS QUOTED: this is the FIRST TABLE M card carrying `MODEL_VERSION v5.0`.** **Every slate from 8/23 to 9/10 was priced by v4.0.** ⛔ **Nothing on this page is split, re-bucketed or re-specified off it — `claude/mlb-projection-model.md`'s own code-debt arithmetic puts the worst realistic pricing impact at 0.053 K and 0.133 outs — but every Brier and bucket figure from here forward is computed on a mixed-version population and must say so.**

✅ **ALL 25 PITCHER ROWS ARE GRADED — every carded starter started. TABLE M 12/25 (48.0%).**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **TWENTIETH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play has been carded since 8/22. T15's denominator is CARDED plays and the machine board is a different population, so nothing was substituted into it.** ⚠️ **The drought is now twenty-one days.**

⚠️ **Brier on the machine population, for the record and in NO T15 denominator:** `carried` **.2437** · `model` **.2485** · `blend` **.2531** · `raw` **.2682** — **means `model` 61.7 · `raw` 64.3 · `blend` 63.0 · `carried` 60.1 against an actual 48.0%.** ⛔ **The whole spread is .0245 at n=25 and the board sat 15 points over the outcome, so "lower was better" is again arithmetic rather than evidence. LOG, DO NOT CONCLUDE.**

⚠️ **The "which was closer" tally on this population reads model 12, raw 13, tie 0** *(`12 + 13 + 0 = 25` ✅, counted against the 25 graded rows)*. ⛔ **It is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no fit.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 9/11 card carries Hard Rock alt ladders on 14 of its 25 pitcher rows — 119 rungs across 13 DISTINCT starts** *(14 carded rows, 13 distinct pitchers: Taj Bradley appears on two rows and is ONE start)*. 🔴 **IT IS NOT MERGED, for the twentieth time and for the same reason: T11's `n` is CARDED arms and the machine board is a different population.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket tally on this page.**

**Anthony Kay (2 K) · Drew Rasmussen (4 K) · Dustin May (6 K) · Jeffrey Springs (1 K) · Max Scherzer (3 K) · Nolan McLean (5 K) · Parker Messick (5 K) · Robbie Ray (5 K) · Ryan Gusto (3 K) · Seth Lugo (7 K) · Shota Imanaga (4 K) · Taj Bradley (6 K) · Yusei Kikuchi (5 K)** — **13 DISTINCT STARTS**, deduplicated on (pitcher, date). ⛔ **`n` is 13 STARTS, not 119 rungs.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/11. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/10 blocks: the matched class ARGUED FOR the play when its ALL-STARTS rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a majority of prior meetings cleared the number and AGAINST when none or a minority did; `n=0` is a NO CALL and enters no tally.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **25** | **16/25** | ⚠️ **right on 11 of its 19 FORs and 5 of its 6 AGAINSTs** *(`11 + 5 = 16` ✅, `19 + 6 = 25` ✅)*. **15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, 15/22, 15/24, 14/25, 10/24, 9/25, 10/25, 13/22, 16/25, 11/25, 4/13, now 16/25 across twenty slates** |
| **Head-to-head** (prior meetings) | **9** | **4/9** | ⚠️ **right on 1 of 4 FORs and 3 of 5 AGAINSTs** *(`1 + 3 = 4` ✅, `4 + 5 = 9` ✅)* |
| **Head-to-head, NO CALL** | **16** | — | ⛔ **logged and in no tally** (`9 + 16 = 25` ✅) |

⚠️ **The two instruments DISAGREED on 4 of the 25 rows, after zero on 9/10.** ⛔ **Four rows is not a comparison of two instruments and nothing is concluded from it.**

### ✅ 🆕 PRE-PUBLISH CHECK 36 IS **CLOSED ON THE CARD** — AFTER NINETEEN CONSECUTIVE REPORTS — AND THE INSTRUMENT FIRED ON ITS FIRST LIVE SLATE

`[verified 2026-09-12]` 🔴 **THE 9/10 BLOCK ABOVE ASKED THE NEXT RUN TO CHECK FOR A CLOSE RATHER THAN A TWENTIETH REPORT. IT IS A CLOSE.** ✅ **`picks/2026-09-11.json` carries `h2h_gap_days` on all 14 rows with a prior meeting and `h2h_rematch` on every one of the 25, and the head-to-head string now ends `-- last one N days ago` and, inside the window, `, and they have seen him inside a month`.** ✅ **`card.py` carries an `h2h_gap_days()` function at line 80 and writes the field at line 984.**

🔴 **AND FIVE ROWS ARE INSIDE RULE 51's THIRTY-DAY WINDOW — the first slate on which the check could fire at all, after nineteen slates in which it was either absent or moot.**

| Pitcher | Opponent | Most recent prior START | Gap | Carded row | Result |
|---|---|---|---|---|---|
| Aaron Nola | Atlanta Braves | 2026-09-06 — **5 K**, 21 outs, 93 P | **5 days** | u17.5 outs at blend 65.4 | **19 outs — L** ❌ |
| Aaron Nola | Atlanta Braves | 2026-09-06 — **5 K**, 21 outs, 93 P | **5 days** | u16.5 outs at blend 56.0 | **19 outs — L** ❌ |
| Dustin May | Cincinnati Reds | 2026-09-05 — **5 K**, 11 outs, 56 P | **6 days** | u5.5 K at blend 63.3 | **6 K — L** ❌ |
| Jeffrey Springs | Seattle Mariners | 2026-09-05 — **6 K**, 21 outs, 81 P | **6 days** | u4.5 K at blend 62.9 | **1 K — W** ✅ |
| Chris Sale | Philadelphia Phillies | 2026-09-04 — **7 K**, 18 outs, 103 P | **7 days** | u18.5 outs at blend 66.1 | **21 outs — L** ❌ |

🔴 **THE FIVE CARDED ROWS WENT 1/5, AND THAT IS A FACT ABOUT THIS BOARD, NOT ABOUT RULE 51** — four of the five are UNDERS on a night the pitcher board's unders went 9/17 overall.

🔴 **ALL FOUR ARMS CLEAR THE ≥5 K CONDITIONAL — the first slate on which every eligible row does.** ⚠️ **Descriptively, on the exploratory 4+ K bar the rematch: Sale 7 K → 6 K (cleared), Nola 5 K → 3 K (missed), May 5 K → 6 K (cleared), Springs 6 K → 1 K (missed). TWO of four cleared.** ⛔ **n = 4 arms. That is not evidence for or against the 74.6%-vs-67.1% split, it is not folded into any tally, and NOTHING IS RE-SPECIFIED.** **The machine-population log now holds TWENTY-THREE rows** *(eighteen through 9/10, plus these five carded rows across four arms)*. ⛔ **It is a DIFFERENT population from the hand-carded rule 51 table, which stays at 2 clean instances / 1 confounded and may never receive a machine row.**

### 🟡 THE `carried` SHADOW — 9/11. ✅ **BETTER — THE EIGHTH TIME IN TWENTY SLATES — ON A DIFFERING SET OF FIVE.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed from `blend` on 5 of the 25 graded rows, across 4 pitchers:**

| Play | blend | carried | Result | closer |
|---|---|---|---|---|
| Chris Bassitt u17.5 outs | 72.7% | 58.3% | **W** | **blend** |
| Anthony Kay o3.5 K | 66.1% | 51.7% | **L** | **carried** |
| Ryan Gusto o3.5 K | 60.8% | 46.4% | **L** | **carried** |
| Robbie Ray u4.5 K | 60.1% | 45.7% | **L** | **carried** |
| Ryan Gusto o13.5 outs | 57.8% | 43.4% | **W** | **blend** |

| | Brier over all 25 graded rows | Brier over the 5 rows that differ |
|---|---|---|
| `blend` | **.2531** | **.2841** |
| `carried` | ✅ **.2437** | ✅ **.2371** |
| Verdict | ✅ **`carried` is BETTER by .0094** | ✅ **`carried` is BETTER by .0470** |

⚠️ 🔴 **THE MECHANISM IS THE ORDINARY ONE AND THE MARGIN IS MEANINGLESS: `carried` is simply LOWER, the board sat 15 points over the outcome, and the differing subset went 2/5.** ⛔ **T21/T22 IS NEITHER ADOPTED NOR REJECTED AND NOTHING IS RE-SPECIFIED.**

**Running total 137 differing rows across twenty slates** *(132 through nineteen + 5 on 9/11)*. ⚠️ **The "closer" tally on the differing rows alone reads blend 2, carried 3 — the same ordering as the Brier, on five rows, which settles nothing.** ⛔ **Both are printed; neither is a verdict.**

### ✅ 🆕 THE CONTROL REVERSED YESTERDAY'S FIVE FAILURES, AND THAT IS REPORTED AS A REVERSAL RATHER THAN A CLEARANCE

`[measured 2026-09-12 — full detail in `claude/pick-ledger.md`'s 2026-09-12 control block]`

**The ENUMERATED full-season sum was 28/28 EXACT on carded starters across BOTH slates, from two files written a day apart. The LIVE `statsapi` game log, asked to list one split per line, was 3/3 EXACT — Scherzer 15 starts / 203 outs / 51 K, Sale 26 / 471 / 190, Nola 30 / 484 / 165 — with zero domain violations anywhere.**

⛔ **THIS DOES NOT RETIRE YESTERDAY'S FINDING AND MUST NOT BE READ AS ONE.** **Every clean reading here came from the ENUMERATED form. No `stats=season` TOTAL was asked for and none was believed.** ➡️ **A fetched TOTAL is still a summary; the discipline that produced 3/3 today is the same one that produced 9/9 yesterday after two totals fabricated.**

### 🔴🔴 🆕 AND THE FINDING THAT MATTERS MOST THIS RUN IS NOT ON THIS PAGE AT ALL

**`claude/pick-ledger.md` had NO record of the 9/10 slate when this run started — no dated table, no TABLE-INDEX rows, no by-day rows, no Changelog entry — while THIS page carried the complete 2026-09-11 block above.** 🔴 **The two docs are written by the same run and they diverged.** ⛔ **Whether the ledger write failed at upload or landed and was overwritten by a later interactive session is NOT established headless and is NOT guessed at.** ✅ **The 9/10 slate was re-derived from scratch on 2026-09-12 and REPRODUCED every figure on this page exactly — 2/13, all four means, all four Brier values, the −45.1 gap, and 57 rungs across 7 distinct starts — so nothing here needed correcting, and the ledger now carries the record.** ➡️ **Standing check proposed: `project_info`'s `created_at` for the ledger and this page should never be more than one grading run apart, and when they are, the ledger is the one behind.**


---

## 🆕 2026-09-13 — THE TWENTY-FIRST MACHINE SLATE (2026-09-12): AN ELEVENTH CARD WRITTEN EXACTLY ONCE, 🔴🔴 **AND THE FIRST SINCE 8/29 TO LOSE A GAME — A 3h30m VERIFY OUTAGE PUSHED IT PAST A FIRST PITCH AND LEFT IT SEVENTEEN MINUTES OF MARGIN**, A BOARD THAT INVERTED YESTERDAY'S SIDE SPLIT AND MISSED BY THE SAME SIGN, AND THE **MILDEST TICKET-POOL CONCENTRATION THIS TABLE HAS RECORDED**

`[graded 2026-09-13]` ✅ **`picks/2026-09-12.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 12 GAMES.** **`25 + 25 = 50` ✅.**

✅ **Written EXACTLY ONCE for an eleventh consecutive day — `9bd1688` at `2026-09-12T17:19:36Z`, `generated_at 17:19:27Z`.**

🔴🔴 **BUT NOT UNDAMAGED, AND THE DAMAGE IS A NEW SHAPE: `coverage_detail.skipped` CARRIES `"already started": 1` — the first time since 8/29 that key has appeared — AND THE PRE-SLATE MARGIN IS SEVENTEEN MINUTES.** **The earliest `commence` the card DID cover is `2026-09-12T17:36:00Z`; the game it did NOT is COL @ DET at `17:10:00Z`, which was nine minutes into play when the file was written.** ⛔ **This is not a scheduling drift. `claude/pick-ledger.md`'s 2026-09-12 entries record `verify_card` failing from 13:49Z to 17:19Z on a parlay leg priced at EXACTLY −700 — a check rule 187 had already fixed in the BUILDER and not in the VERIFIER — with drop 44B clearing it.** ➡️ **THE OUTAGE COST THE CARD ONE WHOLE GAME AND ALL BUT SEVENTEEN MINUTES OF ITS MARGIN.** ⚠️ **The previous narrowest margin this table has recorded is 9/10's 2h 06m. This is seven times narrower.**

✅ **The other two absent games are NOT drops and are named rather than counted: PIT @ CHC (`18:20Z`) and CIN @ MIL (`23:10Z`) were both still ahead of the card, so they are absences in a RANKING.** ⛔ **Which of the three was the started one is not guessed — it is read off the first-pitch times.**

✅ **ALL 25 PITCHER ROWS ARE GRADED — every carded starter started. TABLE M 10/25 (40.0%).**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **TWENTY-FIRST CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play has been carded since 8/22. T15's denominator is CARDED plays and the machine board is a different population, so nothing was substituted into it.** ⚠️ **The drought is now twenty-two days.**

⚠️ **Brier on the machine population, for the record and in NO T15 denominator:** `carried` **.2918** · `model` **.3035** · `blend` **.3218** · `raw` **.3482** — **means `model` 65.6 · `raw` 66.0 · `blend` 65.8 · `carried` 58.3 against an actual 40.0%.** ⛔ **The board sat 25.8 points over the outcome, so "lower was better" is once again arithmetic rather than evidence. LOG, DO NOT CONCLUDE.**

⚠️ **The "which was closer" tally on this population reads model 16, raw 9, tie 0** *(`16 + 9 + 0 = 25` ✅, counted against the 25 graded rows)*. ⛔ **It is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no fit.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The merged pure-model accumulator stays at 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The 9/12 card carries Hard Rock alt ladders on 16 of its 25 pitcher rows — 119 rungs across 14 DISTINCT starts** *(16 carded rows, 14 distinct pitchers: Connor Prielipp and Peter Lambert each carry TWO laddered rows and each is ONE start)*. 🔴 **IT IS NOT MERGED, for the twenty-first time and for the same reason: T11's `n` is CARDED arms and the machine board is a different population.**

⚠️ **The starts are NAMED anyway, per the accumulation protocol, so a future registered pass can deduplicate against them without re-deriving anything.** ⛔ **Naming is not merging, and none of these appears in any bucket tally on this page.**

**Andrew Alvarez (8 K) · Brandon Pfaadt (7 K) · Connor Prielipp (1 K) · Kumar Rocker (5 K) · Kyle Bradish (2 K) · Kyle Leahy (4 K) · Michael King (4 K) · Peter Lambert (4 K) · Randy Dobnak (4 K) · Ranger Suarez (8 K) · Tyler Glasnow (7 K) · Tyler Mahle (3 K) · Tyler Phillips (3 K) · Walbert Ureña (7 K)** — **14 DISTINCT STARTS**, deduplicated on (pitcher, date). ⛔ **`n` is 14 STARTS, not 119 rungs.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/12. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/11 blocks, and stated in the form the tallies are actually COMPUTED under: the matched class ARGUED FOR the play when its ALL-STARTS rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a MAJORITY of prior meetings cleared the number and AGAINST when NONE did; `n=0` is a NO CALL, and so is any split that is neither a majority nor none.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **24** | **12/24** | ⚠️ **right on 8 of its 19 FORs and 4 of its 5 AGAINSTs** *(`8 + 4 = 12` ✅, `19 + 5 = 24` ✅)*. **15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, 15/22, 15/24, 14/25, 10/24, 9/25, 10/25, 13/22, 16/25, 11/25, 4/13, 16/25, now 12/24 across twenty-one slates** |
| **Head-to-head** (prior meetings) | **10** | 🔴 **3/10** | ⚠️ **right on 3 of 8 FORs and 0 of 2 AGAINSTs** *(`3 + 0 = 3` ✅, `8 + 2 = 10` ✅)* |
| **Head-to-head, NO CALL** | **15** | — | ⛔ **logged and in no tally** — **12 at `n=0` plus THREE split-cleared rows the convention does not reach (Kyle Bradish vs TOR `cleared 1/2`, on two carded rows; Tyler Mahle vs PHI `cleared 1/3`)** (`10 + 15 = 25` ✅) |

⚠️ 🔴 **ONE ROW IS EXCLUDED FROM THE CLASS TALLY AND IT IS NAMED RATHER THAN QUIETLY DROPPED, on the 8/25 practice: Tyler Glasnow `u7.5 K`, class `17/34 = 50.0%`, result W.** **A class sitting EXACTLY on the boundary argues nothing by construction.** ⛔ **The boundary-row convention inconsistency flagged on 8/25 is STILL unresolved — 8/23 kept its 50.0% row inside its denominator while 8/25 excluded two — so the twenty-one class tallies are still NOT summable as published and are still reported as twenty-one separate enumerated tallies.**

⚠️ **The two instruments DISAGREED on 2 of the 25 rows and the CLASS was right on both** — Kumar Rocker `o3.5 K` (class FOR, h2h AGAINST, result W) and Peter Lambert `o4.5 K` (class AGAINST, h2h FOR, result L). ⛔ **Two rows is not a comparison of two instruments and nothing is concluded from it.**

### ⚠️ 🔴 A DATED CORRECTION TO THE 2026-09-12 BLOCK ABOVE — PRE-PUBLISH CHECK 28, AND IT IS A PROSE-vs-ROWS MISMATCH, NOT A NUMBER ERROR

**That block states the head-to-head convention as *"ARGUED FOR when a majority of prior meetings cleared the number and AGAINST when none OR A MINORITY did."*** 🔴 **Its own numbers were NOT computed that way.** `[measured 2026-09-13 by re-deriving that slate from source]` **Under a rule where a MINORITY counts as AGAINST, the six `cleared 1/2`-shaped rows on that card would enter the tally and its denominator could not be 9. Re-deriving it under the ORIGINAL rule — majority FOR, none AGAINST, everything else NO CALL — reproduces `4/9` with `16` no-calls EXACTLY.**

⛔ **THE TALLY IS CORRECT AND IS NOT ALTERED. THE SENTENCE DESCRIBING IT IS THE THING THAT DRIFTED, and it is corrected here rather than in place so nothing above this line moves.** ➡️ **Every block from 8/23 forward is computed under the original rule; the convention stated at the head of THIS block is the operative one.**

### ✅ PRE-PUBLISH CHECK 36 STAYS CLOSED — SECOND CONSECUTIVE SLATE

**`h2h_gap_days` is present on 13 of the 25 pitcher rows (every row with a prior meeting) and `h2h_rematch` on all 25; the substring `days` appears 44 times in the file.** ✅ **The close recorded on 9/12 holds.**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS ROWS 24 AND 25 — AND NEITHER CLEARS THE ≥5 K CONDITIONAL

**TWO carded rows sit inside rule 51's thirty-day window, and they are the SAME ARM: Tyler Mahle vs PHI at SIX DAYS** (`o4.5 K` → **L**, and `o16.5 outs` → **W**; the two rows print different `cleared` fractions because they measure different numbers). ⚠️ **The nearest row outside the window is far clear of it, so there is no boundary case.**

🔴 **The prior meeting was 2026-09-06 and Mahle struck out THREE — so this pair does NOT clear the ≥5 K conditional and speaks to the REGISTERED finding not at all.** **Descriptively, the rematch produced THREE again: identical strikeout output six days apart, which is neither the haircut the exploratory version predicts nor a contradiction of it at n=1.**

**The machine-population log now holds TWENTY-FIVE rows.** ⛔ **Nothing eligible is folded in, nothing is re-specified, and the registered mean-K specification is still CLOSED-FAILED with the threshold version EXPLORATORY.**

### 🟡 THE `carried` SHADOW — 9/12. ✅ **BETTER — THE NINTH TIME IN TWENTY-ONE SLATES — ON A DIFFERING SET OF THIRTEEN.** ⛔ **STILL IN NO DENOMINATOR.**

| | `blend` | `carried` |
|---|---|---|
| Brier, all 25 graded rows | **.3218** | ✅ **.2918** |
| Brier, the 13 rows where they DIFFER | **.3355** | ✅ **.2778** |
| Hit rate on those 13 rows | **5/13 = 38.5%** | *(same rows — the column does not change the outcome)* |
| Slate hit rate | **10/25 = 40.0%** | |

⚠️ **The mechanism is the ORDINARY one and it is stated so nobody reads a finding into it: the differing subset went 38.5% against a slate rate of 40.0% — a 1.5-point gap — so `carried` did not win because it identified a worse subset. It won because it is simply LOWER and the whole board sat 25.8 points over.**

**Running total: 150 differing rows across twenty-one slates.** ⛔ **Nothing is adopted, rejected or re-specified. `carried` enters NO denominator.**

### 🔴 THE BAND SHAPE — AND THE ONE CELL THAT IS ONE ROW

| Band | Record | Mean `blend` | Gap |
|---|---|---|---|
| 80-plus | 🔴 **0/1 = 0.0%** | 86.0 | 🔴 **−86.0** |
| 70-80 | **3/6 = 50.0%** | 75.3 | 🔴 **−25.3** |
| 60-70 | 🔴 **4/11 = 36.4%** | 64.4 | 🔴 **−28.0** |
| under-60 | **3/7 = 42.9%** | 57.0 | **−14.1** |

✅ `1 + 6 + 11 + 7 = 25` ✅ · `0 + 3 + 4 + 3 = 10` ✅.

⚠️ 🔴 **THE 80-plus CELL IS ONE ROW — Connor Prielipp `o3.5 K` at blend 86.0, one strikeout in 5.1 innings — AND ITS −86.0 MEANS NOTHING ALONE.** ✅ **The card's own `band_note` on that row already said so: *"only 12 graded plays in this range — too few to say anything."***

🔴 **AND THE SIDE SPLIT INVERTED FROM YESTERDAY WITHOUT CHANGING THE SIGN OF THE ERROR: the 9/10 board was twelve-thirteenths UNDERS and missed by 45.1; this board was sixteen-twenty-fifths OVERS (overs 8/16, unders 2/9) and missed by 25.8.** ⛔ **Two opposite board shapes, the same direction of over-confidence. That is the observation. It is NOT a finding about sides, and three slates do not make a trend.**

### ✅ 🆕 THE TICKET-POOL CONCENTRATION DEFECT IS AT ITS MILDEST SINCE IT WAS FIRST RECORDED — AND THAT IS A MEASUREMENT, NOT A FIX

`[measured 2026-09-13 by enumerating every leg of all 32 tickets]` **No single leg appears in more than 13 of the 32 tickets and no single ARM in more than 14** (Kyle Leahy 14, Peter Lambert 13, Kumar Rocker 13; in the eight PAIRS the most-used arms are Lambert and Leahy at four each).

⛔ **Compare the eight preceding slates: ONE ARM IN ALL 32 TICKETS on 9/7, 9/8 and 9/9; 23 of 32 on 9/10 (Austin Wells) and 23 of 32 on 9/11 (Kaelen Culpepper).**

⚠️ 🔴 **STATED AS A PROPERTY OF THIS BOARD, NOT AS A REPAIR: nothing in `card.py` changed that anyone has recorded, and a fifteen-game slate simply offers more distinct legs than a five- or eleven-game one.** ➡️ **The honest reading is that the defect is DRIVEN BY BOARD SIZE, which is testable and has never been tested.** ✅ **PAIRS 3/8 and PARLAYS 8/18 are therefore, for once, several observations rather than one start reported thirty-two times.**

### ✅ THE CONTROL — SIX ROUTES, ZERO DOMAIN VIOLATIONS, AND THE LIVE ENUMERATED ROUTE CLEAN FOR A SECOND CONSECUTIVE RUN

`[measured 2026-09-13 — full detail in `claude/pick-ledger.md`'s 2026-09-13 control block]`

**Every stored result line across all three slates domain-checked and recomputed (zero violations); the ENTIRE stored pitcher corpus checked — 17,153 game-log rows across 519 players, `pulled_at 2026-09-13T10:16:03Z`, `n_failed: 0` — zero there too; enumerated full-season sums 15/15 EXACT against the season block stored beside each carded starter's game line; the LIVE `statsapi` game log, asked to ENUMERATE one split per line, 2/2 EXACT (Michael King 30 splits / 525 outs / 148 K, Tyler Glasnow 11 / 185 / 77); and the runner's own `record.json` reproducing this page's grading of all three slates row for row.**

⛔ **No `stats=season` TOTAL was requested and none was believed. Every clean reading came from the ENUMERATED form.**

### 🔴🔴 🆕 AND THE FINDING THAT MATTERS MOST THIS RUN IS AGAIN NOT ON THIS PAGE — IT IS THAT THE LEDGER LOST TWO CONSECUTIVE GRADING RUNS

**The 2026-09-12 block above ends by recording that `claude/pick-ledger.md` had no 9/10 record and saying "the ledger now carries the record."** 🔴 **IT DID NOT. When THIS run started, that document's newest graded block was still the 9/9 slate — no 9/10 block, no 9/11 block, no TABLE-INDEX rows, no by-day rows — so the 9/12 run's ledger write is gone as well as the 9/11 run's.**

✅ **BOTH SLATES WERE RE-DERIVED FROM SCRATCH THIS RUN, from the committed card files and the collector's stored results, WITHOUT reading this page first — and every figure published here for them reproduced EXACTLY: 9/10's 2/13, its four means, its four Brier values, its −45.1 gap, its 4/13 class and 0/3 head-to-head, its 57 rungs across 7 named starts; 9/11's 12/25, its four means, its four Brier values, its −15.0 gap, its 16/25 class and 4/9 head-to-head, its 119 rungs across 13 named starts.** ⛔ **NOTHING ON THIS PAGE NEEDED CORRECTING AND NOTHING ON IT WAS ALTERED. The ledger now carries all three slates, and the divergence is written up there.**

➡️ 🔴 **THE STANDING CHECK IS ADOPTED AND SHARPENED: `project_info`'s `created_at` for the ledger and for this page should never be more than one grading run apart, and when they are, THE LEDGER IS THE ONE BEHIND. An unattended run cannot prevent a stale upload of a 6,800-line file; it CAN detect the loss the next morning and restore from source — but only while the source data is still in the repo.**

⚠️ **ONE SMALLER HOUSEKEEPING DEFECT, FOUND WHILE WRITING THIS BLOCK: the `Progress:` footer on this page had not been updated by the 9/10, 9/11 or 9/12 runs and still read the state as of the 9/8 slate.** ✅ **The stale line is STRUCK IN PLACE where it stands — not deleted — and the current value is here.**

~~**Progress: TABLE M — 21 slates, 468 graded pitcher plays, 157 graded pairs. TABLE M-H — 20 slates, 501 graded hitter rows.**~~ ⚠️ **SUPERSEDED 2026-09-14 by the block below — kept, not deleted: this is the state of the accumulator after twenty-one slates.** *(`380 + 25 + 13 + 25 + 25 = 468` ✅ · `125 + 8 + 8 + 8 + 8 = 157` ✅ · `399 + 22 + 35 + 23 + 22 = 501` ✅ — counted against the four dated slate blocks added since, not against another number.)*


---

## 🆕 2026-09-14 — THE TWENTY-SECOND MACHINE SLATE (2026-09-13): A TWELFTH CARD WRITTEN EXACTLY ONCE AND THE PRE-SLATE MARGIN BACK TO **2h 02m**, THE **NARROWEST FOUR-ESTIMATOR BRIER SPREAD THIS TABLE HAS EVER PRODUCED**, `carried` BETTER FOR ONCE **NOT** BY THE USUAL MECHANISM — AND A TICKET SURFACE WHERE THE SAME CONCENTRATION DEFECT PRODUCED A **7/8** AND A **0/8** ON ONE NIGHT

✅ **ALL BUT ONE PITCHER ROW GRADED. TABLE M 12/24 (50.0%), ONE UNGRADED — Jake Irvin DID NOT START.** `[measured 2026-09-14 by enumerating every pitcher in LAA @ WSH from `data/2026-09-13/results/final.json.gz`: Riley Cornelio carries `started: true` for Washington and Irvin appears in the SAME game with `started: false`]` ⛔ **Nothing was inferred from an empty response — the row is present and it says he relieved.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **TWENTY-SECOND CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play has been carded since 8/22. T15's denominator is CARDED plays and the machine board is a different population, so nothing was substituted into it. T15 stays at 31/100.** ⚠️ **The last TABLE A card is 8/22 — twenty-two days before the slate this run grades, twenty-three before the run itself.**

⚠️ **Brier on the machine population, for the record and in NO T15 denominator:** `carried` **.2839** · `model` **.2849** · `blend` **.2856** · `raw` **.2997** — **means `model` 63.8 · `raw` 70.5 · `blend` 67.1 · `carried` 61.7 against an actual 50.0%.** 🔴 **The whole spread is .0158 at n=24 — the narrowest this table has recorded, beating 9/9's .0043-on-25 only on the count of estimators it fails to separate.** ⛔ **It orders nothing. LOG, DO NOT CONCLUDE.**

⚠️ **The "which was closer" tally on this population reads model 10, raw 14, tie 0** *(`10 + 14 + 0 = 24` ✅, counted against the 24 graded rows)*. ⛔ **It is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no fit.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The 9/13 card carries alt ladders on 14 of 25 pitcher rows — 111 rungs across THIRTEEN NAMED distinct starts — and none of it is merged, because T11's `n` is CARDED arms.** **The merge stays 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The thirteen starts, NAMED with the actual strikeout count, so this pass can be deduplicated on `(pitcher, date)` if it is ever merged:**

| Pitcher | Date | Rungs | Actual K |
|---|---|---|---|
| Andrew Painter | 2026-09-13 | 8 | 3 |
| Cal Quantrill | 2026-09-13 | 8 | 4 |
| Chase Burns | 2026-09-13 | 7 | 5 |
| Christian Scott | 2026-09-13 | 8 | 7 |
| Dylan Cease | 2026-09-13 | 7 | 9 |
| Freddy Peralta | 2026-09-13 | 9 | 4 |
| Grant Holmes | 2026-09-13 | 6 | 0 |
| Hayden Wesneski | 2026-09-13 | 6 | 2 |
| Jackson Jobe | 2026-09-13 | 16 | 8 |
| Jacob Lopez | 2026-09-13 | 9 | 3 |
| Matthew Boyd | 2026-09-13 | 9 | 3 |
| Robert Gasser | 2026-09-13 | 9 | 5 |
| Trevor Rogers | 2026-09-13 | 9 | 5 |

✅ `8+8+7+8+7+9+6+6+16+9+9+9+9 = 111` ✅, counted against the thirteen rows above and not against another number. ⚠️ **THIRTEEN DISTINCT STARTS, not fourteen rows — Jackson Jobe carries ladders on two carded rows and is ONE start.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/13. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/12 blocks, stated in the form the tallies are actually COMPUTED under: the matched class ARGUED FOR the play when its ALL-STARTS rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a MAJORITY of prior meetings cleared the number and AGAINST when NONE did; `n=0` is a NO CALL, and so is any split that is neither a majority nor none.**

| | Rows | Right | Verdict |
|---|---|---|---|
| **Matched class** (all-starts %) | **23** | 🔴 **10/23** | ⚠️ **right on 8 of its 17 FORs and 2 of its 6 AGAINSTs** *(`8 + 2 = 10` ✅, `17 + 6 = 23` ✅)*. **15/32, 16/23, 11/23, 13/23, 0/1, 10/25, 2/6, 13/23, 13/24, 15/22, 15/24, 14/25, 10/24, 9/25, 10/25, 13/22, 16/25, 11/25, 4/13, 16/25, 12/24, now 10/23 across twenty-two slates** |
| **Head-to-head** (prior meetings) | **11** | ✅ **7/11** | ⚠️ **right on 6 of 9 FORs and 1 of 2 AGAINSTs** *(`6 + 1 = 7` ✅, `9 + 2 = 11` ✅)* |
| **Head-to-head, NO CALL** | **13** | — | ⛔ **logged and in no tally** — **11 at `n=0` plus TWO split-cleared rows the convention does not reach (Andrew Painter vs ATL `cleared 1/2`, on two carded rows)** (`11 + 13 = 24` ✅) |

⚠️ 🔴 **ONE ROW IS EXCLUDED FROM THE CLASS TALLY AND IT IS NAMED RATHER THAN QUIETLY DROPPED, on the 8/25 practice: Jackson Jobe `u4.5 K`, class `40/80 = 50.0%`, result L.** **A class sitting EXACTLY on the boundary argues nothing by construction.** ⛔ **The boundary-row convention inconsistency flagged on 8/25 is STILL unresolved — 8/23 kept its 50.0% row inside its denominator while 8/25 excluded two — so the twenty-two class tallies are still NOT summable as published and are still reported as twenty-two separate enumerated tallies.**

⚠️ 🔴 **THE TWO INSTRUMENTS DISAGREED ON THREE ROWS AND THE HEAD-TO-HEAD WAS RIGHT ON ALL THREE** — Jacob Lopez `o4.5 K` (class FOR, h2h AGAINST, result L), Robert Gasser `u5.5 K` (class AGAINST, h2h FOR, result W) and Jacob Lopez `u16.5 outs` (class AGAINST, h2h FOR, result W). ⛔ **Three rows is not a comparison of two instruments, TWO of the three are the same arm, and nothing is concluded from it.** ⚠️ **Recorded because on 9/12 the CLASS was right on both disagreements and on 9/9 the split was 3–2; the instrument that "wins" flips slate to slate, which is what n=2-to-5 looks like.**

### ✅ PRE-PUBLISH CHECK 36 STAYS CLOSED — THIRD CONSECUTIVE SLATE

**`h2h_gap_days` is present on 13 of the 25 pitcher rows (every row with a prior meeting) and `h2h_rematch` on all 25; the substring `days` appears 41 times in the file.** ✅ **The close recorded on 9/12 holds.**

### 🔴 THE MACHINE-POPULATION RULE 51 LOG GAINS ROWS 26 AND 27 — AND FOR THE SECOND TIME SINCE THE INSTRUMENT WAS BUILT, THE PRIOR MEETING **DOES** CLEAR THE ≥5 K CONDITIONAL

**TWO carded rows sit inside rule 51's thirty-day window and they are the SAME ARM: Grant Holmes vs PHI at SIX DAYS** (`o14.5 outs` → **L**, and `o3.5 K` → **L**; the two rows print different `cleared` fractions because they measure different numbers). ⚠️ **The nearest row outside the window is Matthew Boyd at 51 days, so there is no boundary case.**

✅ 🔴 **THE PRIOR MEETING WAS 2026-09-07 AND HOLMES STRUCK OUT SIX — so this pair DOES clear the ≥5 K conditional, and it is only the second slate on which any eligible row has.** 🔴 **The rematch produced ZERO strikeouts in 4.0 innings on 71 pitches.** **On the exploratory 4+ K bar the prior meeting cleared and the rematch did not, which is the DIRECTION the exploratory version predicts** — ⛔ **at n=1 arm that is an anecdote, not evidence, and the registered mean-K specification is still CLOSED-FAILED with the threshold version EXPLORATORY.**

**The machine-population log now holds TWENTY-SEVEN rows.** ⛔ **Nothing eligible is folded in and nothing is re-specified.**

### 🟡 THE `carried` SHADOW — 9/13. ✅ **BETTER — THE TENTH TIME IN TWENTY-TWO SLATES — BUT NOT BY THE USUAL MECHANISM, AND THAT IS THE INTERESTING PART.** ⛔ **STILL IN NO DENOMINATOR.**

| | `blend` | `carried` |
|---|---|---|
| Brier, all 24 graded rows | **.2856** | ✅ **.2839** |
| Brier, the 9 rows where they DIFFER | **.2609** | ✅ **.2564** |
| Hit rate on those 9 rows | **5/9 = 55.6%** | *(same rows — the column does not change the outcome)* |
| Slate hit rate | **12/24 = 50.0%** | |

🔴 **THE MECHANISM RAN BACKWARDS AND IT IS STATED SO NOBODY READS A FINDING INTO IT.** **On nine of the previous ten occasions `carried` won because it is simply LOWER and the board sat far over its own number. Here the differing subset went 55.6% — BETTER than the slate's 50.0% — so being lower on that subset should have HURT it, and the margin is .0017 overall.** ⚠️ **The honest reading is that at n=9 differing rows and a .0158 total spread across four estimators, nothing separates them.** ⛔ **Nothing is adopted, rejected or re-specified. `carried` enters NO denominator.**

**Running total: 159 differing rows across twenty-two slates** *(`150 + 9 = 159`)*.

### 🔴 THE BAND SHAPE — AND THE CELL THAT IS ONE PITCHER ON TWO MARKETS

| Band | Record | Mean `blend` | Gap |
|---|---|---|---|
| 80-plus | **1/2 = 50.0%** | 90.6 | 🔴 **−40.6** |
| 70-80 | ✅ **3/4 = 75.0%** | 73.4 | ✅ **+1.6** |
| 60-70 | 🔴 **6/14 = 42.9%** | 64.4 | 🔴 **−21.6** |
| under-60 | **2/4 = 50.0%** | 58.6 | **−8.6** |

✅ `2 + 4 + 14 + 4 = 24` ✅ · `1 + 3 + 6 + 2 = 12` ✅.

🔴 **BOTH 80-plus ROWS ARE CHASE BURNS IN THE SAME 3.0-INNING START, AND THEY SPLIT: `o9.5 outs` at blend 95.7 LOST on EXACTLY 9 outs; `o3.5 K` at 85.4 WON with 5 K.** ⛔ **Two rows, one outing — not two observations — and the −40.6 on that cell is one out.** ✅ **The card's own `band_note` already said "only 13 graded plays in this range — too few to say anything."**

⚠️ **The 60-70 cell is the one carrying the slate at 6/14 and −21.6, and it is the same cell that has been under its number on every slate this month.**

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT IS BACK AT ITS WORST END AFTER TWO MILD SLATES — AND FOR THE FIRST TIME IT PRODUCED **TWO OPPOSITE "RECORDS" ON ONE NIGHT**

`[measured 2026-09-14 by enumerating every leg of all 32 tickets]` **Chase Burns is a leg in 29 of the 32 tickets — 8 of 8 PAIRS and 21 of 24 PARLAYS — on two rungs (`o3.5 K` in 27 tickets, `o2.5 K` in 2), and BOTH won. Hayden Wesneski is in 17 of 32, including SEVEN of the eight three-leg tickets, and his `o2.5 K` LOST on 2 K in 3.0 IP.**

➡️ 🔴 **THE CONSEQUENCE IS THE CLEAREST DEMONSTRATION THIS DEFECT HAS PRODUCED: PAIRS read 7/8 and THREE-LEG PARLAYS read 0/8, on the same board, on the same night, and both numbers are determined by TWO STARTS.** ⛔ **Neither is several observations. A surface that can print a 7/8 and a 0/8 out of two outcomes is not measuring the model.**

⛔ **AND THE 9/13 HYPOTHESIS IS CONTRADICTED RATHER THAN CONFIRMED: that block proposed the defect is "DRIVEN BY BOARD SIZE," on the ground that a fifteen-game slate offers more distinct legs. THIS WAS ALSO A FIFTEEN-GAME SLATE and it produced 29-of-32.** ➡️ **The hypothesis stays UNTESTED, and it is now untested with a counterexample attached. Nothing in `card.py` changed that anyone has recorded.**

### ✅ THE CONTROL — FIVE ROUTES, ZERO DOMAIN VIOLATIONS, AND THE LIVE ENUMERATED ROUTE CLEAN FOR A THIRD CONSECUTIVE RUN

`[measured 2026-09-14 — full detail in `claude/pick-ledger.md`'s 2026-09-14 control block]`

**Every stored result line of the 9/13 slate domain-checked and recomputed (zero violations, 15 games, all `Final`); the ENTIRE stored pitcher corpus checked — 17,272 game-log rows across 520 players, `pulled_at 2026-09-14T10:09:19Z`, `n_failed: 0` — zero there too; enumerated full-season sums 16/16 EXACT against the season block stored beside each carded starter's game line; the LIVE `statsapi` game log, asked to ENUMERATE one split per line, 2/2 EXACT and agreeing THREE ways (Chase Burns 28 splits / 454 outs / 181 K, Jackson Jobe 7 / 104 / 34); and the runner's own `record.json`, built `2026-09-14T10:10:27Z`, reproducing `2026-09-13 w:28 n:47 voids:3` and `by_kind.pitcher: 246/492` EXACTLY.**

⛔ **No `stats=season` TOTAL was requested and none was believed. Every clean reading came from the ENUMERATED form.**

✅ 🆕 **AND THE DIVERGENCE THE LAST TWO RUNS FOUND DID NOT RECUR: `project_info` gives `claude/pick-ledger.md` a `created_at` of `2026-09-14T08:01:04Z` and this page `2026-09-13T11:53:24Z` — one grading run apart, which is the standing check's pass condition. The ledger carried the complete 9/12 record when this run started.**

~~**Progress: TABLE M — 22 slates, 492 graded pitcher plays, 165 graded pairs. TABLE M-H — 21 slates, 524 graded hitter rows.**~~ ⚠️ **SUPERSEDED 2026-09-15 by the block below — kept, not deleted: this is the state of the accumulator after twenty-two slates.** *(`468 + 24 = 492` ✅ · `157 + 8 = 165` ✅ · `501 + 23 = 524` ✅ — counted against the dated slate block added since, not against another number.)*


---

## 🆕 2026-09-15 — THE TWENTY-THIRD MACHINE SLATE (2026-09-14): A THIRTEENTH CARD WRITTEN EXACTLY ONCE, THE **WIDEST PRE-SLATE MARGIN OF ANY SEPTEMBER CARD**, `model` BEATING `blend` BY .0224 OF BRIER ON A BOARD THAT MISSED BY 18.0 — AND **RULE 51's INSTRUMENT FIRING ON FIVE ROWS THAT ALL LOST, WHICH IS THREE STARTS AND NOT FIVE**

`[graded 2026-09-15]` ✅ **`picks/2026-09-14.json` AS COMMITTED IS 50 PLAYS — 23 PITCHER AND 27 HITTER — ACROSS 10 GAMES.** **`23 + 27 = 50` ✅.**

✅ **TABLE M 10/23 (43.5%), ZERO UNGRADED — every one of the fifteen distinct carded arms started.** **Full rows, the summary and every reconciliation are in `claude/pick-ledger.md`'s dated 2026-09-14 blocks; this page carries only the diagnostics.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **TWENTY-THIRD CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play has been carded since 8/22. T15's denominator is CARDED plays and the machine board is a different population, so nothing was substituted into it. T15 stays at 31/100.** ⚠️ **The last TABLE A card is 8/22 — twenty-three days before the slate this run grades, twenty-four before the run itself.**

⚠️ **Brier on the machine population, for the record and in NO T15 denominator:** ✅ `model` **.2706** · `blend` **.2930** · `carried` **.3084** · 🔴 `raw` **.3306** — **means `model` 58.7 · `raw` 64.3 · `blend` 61.5 · `carried` 58.5 against an actual 43.5%.** 🔴 **The spread is .0600 at n=23, against 9/13's .0158 — the four estimators separated this time, and the ORDER is `model` first and `raw` last.** ⛔ **It orders nothing across slates. LOG, DO NOT CONCLUDE.**

⚠️ **The "which was closer" tally on this population reads model 14, raw 9, tie 0** *(`14 + 9 + 0 = 23` ✅, counted against the 23 graded rows)*. ⛔ **It is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no fit.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The 9/14 card carries alt ladders on 11 of 23 pitcher rows — 85 rungs across ELEVEN NAMED distinct starts — and none of it is merged, because T11's `n` is CARDED arms.** **The merge stays 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

**The eleven starts, NAMED with the actual strikeout count, so this pass can be deduplicated on `(pitcher, date)` if it is ever merged:**

| Pitcher | Date | Rungs | Actual K |
|---|---|---|---|
| Brandon Young | 2026-09-14 | 8 | 6 |
| David Peterson | 2026-09-14 | 7 | 7 |
| José Soriano | 2026-09-14 | 9 | 5 |
| Kade Anderson | 2026-09-14 | 9 | 5 |
| Quinn Mathews | 2026-09-14 | 8 | 8 |
| Reid Detmers | 2026-09-14 | 8 | 8 |
| Sandy Alcantara | 2026-09-14 | 7 | 6 |
| Tarik Skubal | 2026-09-14 | 8 | 9 |
| Tomoyuki Sugano | 2026-09-14 | 7 | 2 |
| Troy Melton | 2026-09-14 | 7 | 3 |
| Will Warren | 2026-09-14 | 7 | 6 |

✅ **`8 + 7 + 9 + 9 + 8 + 8 + 7 + 8 + 7 + 7 + 7 = 85` ✅ — counted against the eleven rows above, not against another number.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/14. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**The matched class — the card's `class` block, every start by a pitcher within ±1.5 season K/9 — called 11 of 23 right.** **The DIRECT head-to-head, on the 11 rows that carry one, called 4 of 11.**

⚠️ **Twelve of the twenty-three rows carry `"never faced ... this season"`, which is printed and is a finding in itself (check 35).** ⛔ **Neither number is added to rule 50's carded tally — different population.**

### 🔴 4 ROWS WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED

| Pitcher | Play | head-to-head says | class says | actual | which was right |
|---|---|---|---|---|---|
| Tarik Skubal | u7.5 K | W | L | **L** | **class** |
| José Soriano | u5.5 K | W | L | **W** | **head-to-head** |
| Gavin Williams | u17.5 outs | W | L | **W** | **head-to-head** |
| Reid Detmers | u6.5 K | W | L | **L** | **class** |

⚠️ **Two each. The class and the head-to-head split the disagreements down the middle and settled nothing.** ⛔ **Four rows. LOG, DO NOT CONCLUDE.**

### 🔴🔴 🆕 RULE 51's INSTRUMENT FIRED ON FIVE ROWS AND ALL FIVE LOST — **AND THAT IS THREE STARTS, NOT FIVE OBSERVATIONS**

`[measured 2026-09-15 from the card's own `h2h_rematch` and `h2h_gap_days` fields]` ✅ **PRE-PUBLISH CHECK 36 IS SATISFIED ON THE CARD: every one of the five rows states the gap in days on the row, exactly as the 9/12 fix intended. The defect this page reported for nineteen consecutive runs is still closed.**

| Pitcher | Play | opponent | gap | W/L | actual |
|---|---|---|---|---|---|
| Tarik Skubal | u18.5 outs | Cincinnati Reds | **6 days** | **MISS ❌** | 7.0 IP · 9 K · 21 outs |
| Tarik Skubal | u7.5 K | Cincinnati Reds | **6 days** | **MISS ❌** | 7.0 IP · 9 K · 21 outs |
| Landen Roupp | o14.5 outs | St. Louis Cardinals | **6 days** | **MISS ❌** | 4.1 IP · 4 K · 13 outs |
| Quinn Mathews | u16.5 outs | San Francisco Giants | **6 days** | **MISS ❌** | 6.2 IP · 8 K · 20 outs |
| Quinn Mathews | u4.5 K | San Francisco Giants | **6 days** | **MISS ❌** | 6.2 IP · 8 K · 20 outs |

🔴 **FIVE FOR FIVE IN THE DIRECTION THE EXPLORATORY HAIRCUT PREDICTS — AND THE HONEST DENOMINATOR IS THREE.** **The five rows are THREE starts: Tarik Skubal (two markets), Landen Roupp (one) and Quinn Mathews (two).** ⛔ **Two markets on one arm is not two observations, and this page has recorded that mistake being made on the pair surface for nine consecutive slates.**

⛔ **AND THE THREE STARTS DO NOT POINT ONE WAY EITHER: Skubal and Mathews both went LONGER and struck out MORE than their unders allowed (9 K in 7.0 IP, 8 K in 6.2 IP) — the OPPOSITE of a haircut — while Roupp went shorter than his over needed.** ➡️ **The rows lost because the card was on the wrong side, not because a lineup had seen the arm recently.** ⛔ **THE PRE-REGISTERED MEAN-K SPECIFICATION IS STILL FAILED AND STILL CLOSED. Nothing here promotes the threshold version, and none of it is added to rule 51's carded tally.**

### 🟡 THE `carried` SHADOW — 9/14. 🔴 **WORSE, AND FOR THE CLEAREST REASON IT HAS EVER BEEN WORSE.** ⛔ **STILL IN NO DENOMINATOR.**

| | `blend` | `carried` |
|---|---|---|
| Brier, all 23 graded rows | ✅ **.2930** | 🔴 **.3084** |
| Brier, the 5 rows where they DIFFER | ✅ **.2007** | 🔴 **.2715** |
| Hit rate on those 5 rows | **4/5 = 80.0%** | *(same rows — the column does not change the outcome)* |
| Slate hit rate | **10/23 = 43.5%** | |

🔴 **THE MECHANISM IS THE MIRROR OF THE ONE THAT USUALLY MAKES `carried` LOOK GOOD, AND IT IS WORTH NAMING BECAUSE IT IS THE FIRST CLEAN COUNTER-CASE: `carried` is simply LOWER, and on this slate the differing subset went 4/5 = 80.0% against a slate rate of 43.5%.** **Shading five rows DOWN by 11–14 points when four of them won is exactly the cost of a flag that only ever subtracts.**

**The five differing rows across four pitchers: Kade Anderson `u5.5 K` (84.0 → 73.0, WON), Will Warren `o4.5 K` (59.9 → 45.5, WON), David Peterson `u15.5 outs` (59.1 → 44.7, LOST), David Peterson `o4.5 K` (52.0 → 37.6, WON), Reynaldo López `u14.5 outs` (51.3 → 36.9, WON).**

**Running total: 164 differing rows across twenty-three slates** *(`159 + 5 = 164`)*. ⛔ **Nothing is adopted, rejected or re-specified. `carried` enters NO denominator.**


### 🔴 THE BAND SHAPE — AND TWO CELLS THAT ARE ONE ROW EACH

| Band | Record | Mean `blend` | Gap |
|---|---|---|---|
| 80-plus | ✅ **1/1 = 100.0%** | 84.0 | ✅ **+16.0** |
| 70-80 | 🔴 **0/1 = 0.0%** | 73.7 | 🔴 **−73.7** |
| 60-70 | 🔴 **3/9 = 33.3%** | 64.6 | 🔴 **−31.3** |
| under-60 | **6/12 = 50.0%** | 56.3 | **−6.3** |

✅ `1 + 1 + 9 + 12 = 23` ✅ · `1 + 0 + 3 + 6 = 10` ✅.

⚠️ 🔴 **THE TWO TOP CELLS ARE ONE ROW EACH AND BOTH TURNED ON A SINGLE STRIKEOUT: Kade Anderson `u5.5 K` at blend 84.0 recorded exactly 5 and WON; Tomoyuki Sugano `o2.5 K` at 73.7 recorded exactly 2 and LOST.** ⛔ **±1 K in either game inverts both cells. Neither means anything alone and the card's own `band_note` says so.**

⚠️ **The cell carrying the slate is 60-70 at 3/9 and −31.3 — under its own number again, as it was on 9/13 (6/14, −21.6) and 9/12.** ⚠️ **And `under-60` was the closest cell for the second consecutive slate, which is what the card's own `calibration_warning` already tells readers.**

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS NINTH FORM IN NINE SLATES — 🆕 **AND THIS IS THE FIRST TIME IT PRODUCED AN 8/8**

`[measured 2026-09-15 by enumerating every leg of all 32 tickets]` **Kade Anderson `u5.5 K` is a leg in 24 of the 32 tickets — 8 of 8 PAIRS and 16 of 24 PARLAYS — and it is in ALL EIGHT four-leg tickets. Ha-Seong Kim `u1.5 TB` is in 15 of 32. By NAME: Anderson 24/32, Kim 16/32, Ke'Bryan Hayes 11/32.**

➡️ 🔴 **BOTH dominant legs won, so the surface printed PAIRS 7/8 and PARLAYS 21/23 — its best numbers ever — off a 4.1-inning, 5-strikeout start and one hitter who recorded zero total bases.** ⛔ **Anderson needed exactly 5 K to stay under 5.5. One more strikeout and the same board prints 1/8 and 2/23.** ⛔ **A surface whose entire record flips on one at-bat is not measuring the model, and neither number may be quoted as a hit rate.**

⚠️ **It is the exact mirror of 9/7, 9/8 and 9/9, where the identical structure printed 0/24.** ⛔ **And the 9/13 "DRIVEN BY BOARD SIZE" hypothesis is neither confirmed nor refuted here — 9/14 was a TEN-game slate, the smallest full board since 9/10 — so the hypothesis is still UNTESTED and is not advanced by this run.**

### ✅ THE CONTROL — FIVE ROUTES, ZERO DOMAIN VIOLATIONS, AND THE LIVE ENUMERATED ROUTE CLEAN FOR A FOURTH CONSECUTIVE RUN

`[measured 2026-09-15 — full detail in `claude/pick-ledger.md`'s 2026-09-15 control block]`

**Every stored result line of the 9/14 slate domain-checked and recomputed (298 lines, zero violations, 10 games, all `Final`); the ENTIRE stored pitcher corpus checked — 17,352 game-log rows across 521 players, `pulled_at 2026-09-15T10:09:19Z`, `n_failed: 0` — zero there too; enumerated full-season sums 19/19 EXACT against the season block stored beside each starter's game line; the LIVE `statsapi` game log, asked to ENUMERATE one split per line, 2/2 EXACT and agreeing THREE ways (Tarik Skubal 24 splits / 440 outs / 173 K, Troy Melton 19 / 332 / 90, Melton's 2.2 IP fraction included); and the runner's own `record.json` reproducing `by_day 2026-09-14 w:26 n:45 voids:5` and `by_kind.pitcher 256/515` EXACTLY.**

⛔ **No `stats=season` TOTAL was requested and none was believed. Every clean reading came from the ENUMERATED form.**

✅ **AND THE DIVERGENCE CHECK PASSED FOR A SECOND CONSECUTIVE RUN: `project_info` gives `claude/pick-ledger.md` a `created_at` of `2026-09-15T06:32:01Z` and this page `2026-09-14T11:49:19Z` — one grading run apart, the standing check's pass condition. The ledger carried the complete 9/13 record when this run started.**

~~**Progress: TABLE M — 23 slates, 515 graded pitcher plays, 173 graded pairs. TABLE M-H — 22 slates, 546 graded hitter rows.**~~ **SUPERSEDED 2026-09-16 — see the block below.** *(`492 + 23 = 515` ✅ · `165 + 8 = 173` ✅ · `524 + 22 = 546` ✅ — counted against the dated slate block added since, not against another number.)*


## 🆕 2026-09-16 — THE TWENTY-FOURTH MACHINE SLATE (2026-09-15): A FOURTEENTH CARD WRITTEN EXACTLY ONCE, A NEW **WIDEST PRE-SLATE MARGIN**, THE FOUR-ESTIMATOR BRIER ORDERING **EXACTLY REVERSED FROM YESTERDAY**, **RULE 51's INSTRUMENT FIRING ON FOUR ROWS THAT ALL WON — THE MIRROR OF 9/14 — AND A PRE-STATED HITTER TEST THAT FAILED ON ITS FIRST SLATE**

`[graded 2026-09-16]` ✅ **`picks/2026-09-15.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 14 OF THE SLATE'S 15 GAMES.** **`25 + 25 = 50` ✅.**

✅ **TABLE M 14/24 (58.3%), ONE UNGRADED — Davis Martin relieved an opener.** **Full rows, the summary and every reconciliation are in `claude/pick-ledger.md`'s dated 2026-09-15 blocks; this page carries only the diagnostics.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **TWENTY-FOURTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play has been carded since 8/22. T15's denominator is CARDED plays and the machine board is a different population, so nothing was substituted into it. T15 stays at 31/100.** ⚠️ **The last TABLE A card is 8/22 — twenty-four days before the slate this run grades, twenty-five before the run itself.**

⚠️ **Brier on the machine population, for the record and in NO T15 denominator:** ✅ `raw` **.2506** · `blend` **.2573** · `carried` **.2581** · 🔴 `model` **.2765** — **means `model` 64.4 · `raw` 71.9 · `blend` 68.1 · `carried` 59.7 against an actual 58.3%.** 🔴🔴 **THE ORDERING IS THE EXACT REVERSE OF YESTERDAY'S, WHICH IS THE POINT OF WRITING IT DOWN: on 9/14 it was `model` .2706 first and `raw` .3306 last; tonight it is `raw` first and `model` last.** **The spread is .0259 at n=24 against 9/14's .0600.** ⛔ **Two consecutive slates cannot order four estimators in opposite directions and also be evidence about them. LOG, DO NOT CONCLUDE.**

⚠️ **The "which was closer" tally on this population reads model 8, raw 16, tie 0** *(`8 + 16 + 0 = 24` ✅, counted against the 24 graded rows)*. ⛔ **It is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no fit.**

### 🔴 RULE 35 — THE SHADOW LADDER GAINED NOTHING AGAIN, AND AGAIN DELIBERATELY

**The 9/15 card carries alt ladders on TWELVE of 25 pitcher rows — 77 rungs across ELEVEN NAMED pitchers — and none of it is merged, because T11's `n` is CARDED arms.** **The merge stays 185 rungs / 25 distinct starts. T11 progress: 25 / 40 distinct starts, unchanged.**

⚠️ **TWELVE ROWS, ELEVEN NAMES: Lake Bachar carries a ladder on BOTH of his strikeout rows and it is the same five-rung ladder, counted ONCE.** ⚠️ **And one of the eleven is NOT A START — Davis Martin relieved an opener — so a merge would have to drop him, which is why he is flagged on his row rather than silently included.**

**The eleven, NAMED with the actual strikeout count, so this pass can be deduplicated on `(pitcher, date)` if it is ever merged:**

| Pitcher | Date | Rungs | Actual K |
|---|---|---|---|
| Bailey Ober | 2026-09-15 | 7 | 3 |
| Davis Martin | 2026-09-15 | 5 | 0 ⛔ **NOT A START — relieved an opener** |
| Drew Anderson | 2026-09-15 | 7 | 4 |
| Foster Griffin | 2026-09-15 | 9 | 5 |
| Jack Perkins | 2026-09-15 | 8 | 8 |
| Lake Bachar | 2026-09-15 | 5 | 1 |
| Michael Wacha | 2026-09-15 | 8 | 2 |
| Rhett Lowder | 2026-09-15 | 6 | 4 |
| Sean Manaea | 2026-09-15 | 8 | 6 |
| Walker Buehler | 2026-09-15 | 6 | 1 |
| Yoshinobu Yamamoto | 2026-09-15 | 8 | 7 |

✅ **`7 + 5 + 7 + 9 + 8 + 5 + 8 + 6 + 8 + 6 + 8 = 77` ✅ — counted against the eleven rows above, not against another number.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/15. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**The matched class — the card's `class` block, every start by a pitcher within ±1.5 season K/9 or inside the trailing-outs band — called 13 of 24 right.** **The DIRECT head-to-head, on the 8 graded rows that carry one, called 1 of 8.**

⚠️ **Sixteen of the twenty-four graded rows carry `"never faced ... this season"`, which is printed and is a finding in itself (check 35).** ⛔ **Neither number is added to rule 50's carded tally — different population.**

### 🔴🔴 5 ROWS WHERE THE CLASS AND THE HEAD-TO-HEAD FLATLY DISAGREED — **AND THE CLASS WON ALL FIVE**

| Pitcher | Play | head-to-head says | class says | actual | which was right |
|---|---|---|---|---|---|
| Jack Perkins | o3.5 K | L | W | **W** | **class** |
| Rhett Lowder | o14.5 outs | L | W | **W** | **class** |
| Foster Griffin | u5.5 K | L | W | **W** | **class** |
| Blade Tidwell | o14.5 outs | L | W | **W** | **class** |
| Yoshinobu Yamamoto | u7.5 K | L | W | **W** | **class** |

🔴 **FIVE FOR FIVE TO THE CLASS — and every one of the five head-to-heads is a `cleared 0/1` or `0/2`, i.e. a sample of ONE OR TWO STARTS being asked to overrule a class of dozens.** ⚠️ **That is exactly what rule 50 says a head-to-head is: a TIEBREAKER on a tiny `n`, never an input.** ⛔ **Five rows across five arms. It agrees in direction with the 8/21 finding that the class beat the head-to-head, and it is STILL five rows. LOG, DO NOT CONCLUDE.** ⛔ **Nothing is added to rule 50's carded 4/9.**

### 🔴🔴 🆕 RULE 51's INSTRUMENT FIRED ON FOUR ROWS AND ALL FOUR **WON** — **THE EXACT MIRROR OF YESTERDAY, AND THAT IS THREE STARTS, NOT FOUR**

`[measured 2026-09-16 from the card's own `h2h_rematch` and `h2h_gap_days` fields]` ✅ **PRE-PUBLISH CHECK 36 IS SATISFIED ON THE CARD: every one of the four rows states the gap in days on the row. The defect this page reported for nineteen consecutive runs is still closed.**

| Pitcher | Play | opponent | gap | W/L | actual |
|---|---|---|---|---|---|
| Rhett Lowder | o14.5 outs | Los Angeles Dodgers | **6 days** | **HIT ✅** | 5.0 IP · 4 K · 15 outs |
| Rhett Lowder | o3.5 K | Los Angeles Dodgers | **6 days** | **HIT ✅** | 5.0 IP · 4 K · 15 outs |
| Blade Tidwell | o14.5 outs | St. Louis Cardinals | **6 days** | **HIT ✅** | 6.2 IP · 4 K · 20 outs |
| Yoshinobu Yamamoto | u7.5 K | Cincinnati Reds | **6 days** | **HIT ✅** | 7.0 IP · 7 K · 21 outs |

🔴🔴 **YESTERDAY THE INSTRUMENT FIRED ON FIVE ROWS AND ALL FIVE MISSED. TONIGHT IT FIRED ON FOUR AND ALL FOUR HIT. BOTH AT A SIX-DAY GAP.** ⛔ **The honest denominator tonight is THREE STARTS — Rhett Lowder on two markets, Blade Tidwell, Yoshinobu Yamamoto — exactly as yesterday's five rows were three starts.** ➡️ **Two slates, opposite results, three starts each. That is not a signal reversing; it is a reminder that four rows off three outings measures nothing.**

⛔ **THE PRE-REGISTERED MEAN-K SPECIFICATION IS STILL FAILED AND STILL CLOSED (t = −1.78). Nothing here promotes the threshold version, nothing is re-specified, and none of it is added to rule 51's carded tally.**

### 🟡 THE `carried` SHADOW — 9/15. **WORSE, BY THE NARROWEST MARGIN IT HAS EVER BEEN EITHER WAY.** ⛔ **STILL IN NO DENOMINATOR.**

| | `blend` | `carried` |
|---|---|---|
| Brier, all 24 graded rows | ✅ **.2573** | 🔴 **.2581** |
| Brier, the 14 rows where they DIFFER | ✅ **.2511** | 🔴 **.2524** |
| Hit rate on those 14 rows | **9/14 = 64.3%** | *(same rows — the column does not change the outcome)* |
| Slate hit rate | **14/24 = 58.3%** | |

⚠️ **The gap is .0008 on the full board and .0013 on the differing subset. It is noise and is reported as noise.** 🔴 **FOURTEEN of 24 rows differ — the largest differing share this page has recorded — and they still separate the two columns by less than a thousandth of Brier, because the differing subset went 9/14 = 64.3% against a slate rate of 58.3%: shading rows DOWN by ~14 points when they win slightly more often than the board costs almost exactly what it saves.**

**Running total: 178 differing rows across twenty-four slates** *(`164 + 14 = 178`)*. ⛔ **Nothing is adopted, rejected or re-specified. `carried` enters NO denominator.**

### 🔴 THE BAND SHAPE — AND THE FIRST BOARD WITH NO `under-60` ROW AT ALL

| Band | Record | Mean `blend` | Gap |
|---|---|---|---|
| 80-plus | 🔴 **1/3 = 33.3%** | 84.1 | 🔴 **−50.8** |
| 70-80 | ✅ **3/3 = 100.0%** | 72.1 | ✅ **+27.9** |
| 60-70 | **10/18 = 55.6%** | 64.8 | **−9.2** |
| under-60 | **— NO ROWS** | — | — |

✅ `3 + 3 + 18 = 24` ✅ · `1 + 3 + 10 = 14` ✅.

🔴 🆕 **EVERY CARDED PITCHER ROW SITS AT `blend` ≥ 60.0, WHICH THIS TABLE HAS NEVER RECORDED BEFORE** — against 12 of 23 under 60 one night earlier. ⛔ **A property of what the board found, not a change to the selection rule. No cause is asserted.** ⚠️ **It removes the cell that had been best-calibrated on each of the two previous slates, so that comparison cannot be made at all tonight.**

⚠️ **The 80-plus cell is THREE rows across TWO arms and all three are off-Hard-Rock: Kyle Freeland `o11.5 outs` (89.2, WON by exactly one out), Kyle Freeland `o2.5 K` (81.6, LOST with 1 K) and Lake Bachar `o1.5 K` (81.6, LOST with 1 K in a 2.0-inning start).** ⛔ **The card's own `band_note` on those rows says "only 16 graded plays in this range -- too few to say anything."**

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS TENTH FORM IN TEN SLATES — 🆕 **AND THIS ONE DOES NOT SWEEP OR WIPE OUT. IT VOIDS.**

`[measured 2026-09-16 by enumerating every leg of all 32 tickets]` **Ke'Bryan Hayes appears by NAME on 14 of the 32 tickets — `u0.5 RBI` on 12 and `u1.5 TB` on 2, ALL FOURTEEN OF THEM PARLAYS — and HE DID NOT PLAY.** ➡️ **All 14 are UNGRADEABLE. The parlay surface lost 58% of its own denominator to one absent hitter and printed 6/10.** **By ticket-LEG: Hayes `u0.5 RBI` 12/32, Carlos Narváez `u0.5 RBI` 12/32, Jahmai Jones `u0.5 RBI` 10/32.**

🔴 **THE NINE PREVIOUS FORMS WERE ALL ABOUT A DOMINANT LEG WINNING OR LOSING FOR EVERYBODY. THIS ONE NEVER SETTLED, WHICH IS WORSE: a voided pool cannot even be scored against itself.** 🔴 **AND THE CARD'S OWN `lineup_risk` FLAG WAS SET ON HAYES — the surface knew he might not play and built fourteen tickets on him.** ⛔ **A grading run does not touch `card.py`; this is for an interactive session.**

✅ **THE PAIR POOL IS THE OPPOSITE STORY AND IS WORTH THE SAME SENTENCE: all eight pairs IN BAND at 1.815x–2.009x, so the arithmetic complaint the 9/14 block filed — a leg priced so long that no partner can keep the ticket under 2.20 — is simply not present tonight.** ⚠️ **Still one arm: Drew Anderson is a leg in four of the eight and Michael Wacha in three, and Wacha's exactly-2 strikeouts killed all three of his.** ⛔ **4/8 is two arms, not eight observations.**

### ✅ THE CONTROL — FIVE ROUTES, ZERO DOMAIN VIOLATIONS, AND THE LIVE ENUMERATED ROUTE TRUNCATED AND WAS CAUGHT

`[measured 2026-09-16 — full detail in `claude/pick-ledger.md`'s 2026-09-16 control block]`

**Every stored result line of the 9/15 slate domain-checked and recomputed (464 lines — 132 pitcher, 332 batter — zero violations, 15 games, all `Final`); the ENTIRE stored pitcher corpus checked — 17,470 game-log rows across 521 players, `pulled_at 2026-09-16T10:07:58Z`, `n_failed: 0` — zero there too; enumerated full-season sums 19/19 EXACT against the season block stored beside each starter's game line; and the runner's own `record.json` reproducing `by_day 2026-09-15 w:33 n:45 voids:5` and `by_kind.pitcher 270/539` EXACTLY, including the Davis Martin void, which it reached independently by the same `started` test.**

🔴🔴 **THE LIVE ENUMERATED `statsapi` ROUTE FAILED AND WAS CAUGHT BY THE SUM.** **Cristopher Sánchez's game log came back as 27 perfectly-formed splits ending `2026-08-23` — 505 outs / 194 K against a true 581 / 215, FOUR STARTS SHORT — with every IP fraction legal.** ✅ **Re-asked at the same endpoint with an explicit terminal anchor (`LAST=` and `N=`), it returned all 31 and reconciled EXACTLY three ways.** ✅ **Yoshinobu Yamamoto was clean first time: 27 splits / 537 outs / 178 K, agreeing three ways.** ➡️ **Ledger rule 285 — always demand a terminal marker from an enumerating fetch.** ⛔ **No `stats=season` TOTAL was requested and none was believed.**

🔴 **AND A SECOND NEAR-MISS, INSIDE THIS RUN'S OWN GRADING: the parlay legs carry NO player id and the card writes `Narvaez` / `Acuna` where the box score writes `Narváez` / `Acuña`. An exact-string join read two men who batted as absent and would have shipped 22 of 24 parlays UNGRADED instead of 14.** ✅ **Caught before anything was written, by folding the names to ASCII and re-joining.** ➡️ **Ledger rule 284.**

✅ **AND THE DIVERGENCE CHECK PASSED FOR A THIRD CONSECUTIVE RUN: `project_info` gives `claude/pick-ledger.md` a `created_at` of `2026-09-16T06:57:16Z` and this page `2026-09-15T11:50:05Z` — the ledger newer, the standing check's pass condition. The ledger carried the complete 9/14 record when this run started.**

~~**Progress: TABLE M — 24 slates, 539 graded pitcher plays, 181 graded pairs. TABLE M-H — 23 slates, 567 graded hitter rows.**~~ ⚠️ **SUPERSEDED 2026-09-17 by the block below — kept, not deleted: this is the state of the accumulator after twenty-four slates.** *(`515 + 24 = 539` ✅ · `173 + 8 = 181` ✅ · `546 + 21 = 567` ✅ — counted against the dated slate block added since, not against another number.)*



---

## 🆕 2026-09-17 — THE TWENTY-FIFTH MACHINE SLATE (2026-09-16): A FIFTEENTH CARD WRITTEN EXACTLY ONCE, **A THIRD CONSECUTIVE SLATE WITH A DIFFERENT FOUR-ESTIMATOR ORDERING**, **RULE 51's INSTRUMENT NOT FIRING AT ALL FOR THE FIRST TIME SINCE IT WAS BUILT** — AND THE TICKET-POOL CONCENTRATION DEFECT IN ITS MOST EXTREME FORM YET, ONE LEG IN 31 OF 32 TICKETS

`[graded 2026-09-17]` ✅ **`picks/2026-09-16.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 14 OF THE SLATE'S 15 GAMES.** **`25 + 25 = 50` ✅.**

✅ **TABLE M 14/23 (60.9%), TWO UNGRADED — Robert Stock ×2 did not start (Xzavion Curry started for Baltimore).** **Full rows, the summary and every reconciliation are in `claude/pick-ledger.md`'s dated 2026-09-16 blocks; this page carries only the diagnostics.**

🔴🔴 **AND THE RUN'S BIGGEST FINDING IS NOT ABOUT THIS CARD: `claude/pick-ledger.md` HAD NO 2026-09-15 RECORD AT ALL WHEN THIS RUN STARTED**, while THIS page carried the complete `2026-09-16` block grading that slate. **Third occurrence of the divergence (9/11, 9/12, now 9/15).** ✅ **The 9/15 slate was re-derived from source WITHOUT reading this page first and reproduced EVERY figure published here EXACTLY — 14/24, all four Brier values, the means, the 8h 28m margin, pairs 4/8 all in band, parlays 6/10 with 14 ungraded.** ⛔ **Nothing on this page needed correcting; the ledger now carries both slates and the divergence is written up there.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **TWENTY-FIFTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play has been carded since 8/22. T15's denominator is CARDED plays and the machine board is a different population, so nothing was substituted into it. T15 stays at 31/100.** ⚠️ **The drought is twenty-five days.**

⚠️ **Brier on the machine population, for the record and in NO T15 denominator:** ✅ `carried` **.2171** · `blend` **.2235** · `model` **.2246** · 🔴 `raw` **.2385** — **means `carried` 62.3 · `blend` 69.3 · `model` 63.8 · `raw` 74.8 against an actual 60.9%.**

🔴🔴 **THREE CONSECUTIVE SLATES HAVE ORDERED THESE FOUR ESTIMATORS THREE DIFFERENT WAYS, AND THAT IS THE ENTIRE FINDING.** **9/14: `model` .2706 first, `raw` .3306 last, spread .0600. 9/15: `raw` .2506 first, `model` .2765 last, spread .0259. 9/16: `carried` .2171 first, `raw` .2385 last, spread .0214.** ⛔ **Four estimators that reorder every night at n≈24 are not being measured. LOG, DO NOT CONCLUDE.** ⚠️ **The spread has narrowed on each of the last two slates; that is a small-sample fact, not a trend, and it is recorded so nobody reads the narrowing as convergence.**

### 🟡 THE `carried` SHADOW — 9/16. ✅ **BETTER — THE ELEVENTH TIME IN TWENTY-FIVE SLATES — BY THE ORDINARY MECHANISM.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed on 9 of 23 rows across SIX arms.** **On the differing set `carried` scores .2020 against `blend`'s .2184, and that set went 5/9 = 55.6% against a slate rate of 60.9%.** ➡️ **The differing subset UNDER-performed the board while `carried` was the LOWER number on it — the same mechanism that has made it WORSE fourteen times, running the other way.** **Running total 187 differing rows across twenty-five slates.** *(`178 + 9 = 187` — counted against the dated slate block added since, not against another number.)* ⛔ **Nothing adopted, rejected or re-specified.**

### 🔴 RULE 35 / T11 — THE SHADOW LADDER, EVERY START NAMED, AND DELIBERATELY NOT MERGED

**The 9/16 card carries Hard Rock alt ladders on 16 of its 25 pitcher rows.** ✅ **Deduplicated on (pitcher, date): JR Ritchie and Nick Martinez each carry TWO carded rows sharing ONE ladder and ONE start, and Robert Stock's 9 rungs are EXCLUDED because he did not start.** ➡️ **103 rungs across THIRTEEN DISTINCT STARTS. `n` is reported as DISTINCT STARTS, never as rung count.**

| Pitcher | Date | Rungs | Actual K |
|---|---|---|---|
| Anthony Kay | 2026-09-16 | 6 | 3 |
| Anthony Molina | 2026-09-16 | 6 | 6 |
| Blake Snell | 2026-09-16 | 8 | 1 |
| Carlos Rodón | 2026-09-16 | 9 | 5 |
| Chris Bassitt | 2026-09-16 | 8 | 6 |
| Daniel Lynch IV | 2026-09-16 | 6 | 3 |
| George Kirby | 2026-09-16 | 9 | 5 |
| JR Ritchie | 2026-09-16 | 8 | 5 |
| Jake Bennett | 2026-09-16 | 8 | 7 |
| Max Scherzer | 2026-09-16 | 9 | 3 |
| Nick Martinez | 2026-09-16 | 9 | 3 |
| Yusei Kikuchi | 2026-09-16 | 9 | 4 |
| Zack Wheeler | 2026-09-16 | 8 | 5 |

*(`6+6+8+9+8+6+9+8+8+9+9+9+8 = 103` ✅ over THIRTEEN named rows ✅ — counted against the rows above, not against another number.)*

⛔ **NOT MERGED, for the twenty-fifth time and for the same reason: T11's `n` is CARDED arms and the machine board is a different population.** **The merged pure-model accumulator stays at 185 rungs / 25 distinct starts; T11 progress 25 / 40 distinct starts, unchanged.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/16. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/15 blocks, stated in the form the tallies are actually COMPUTED under: the matched class ARGUED FOR the play when its ALL-STARTS rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a MAJORITY of prior meetings cleared the number and AGAINST when NONE did; `n=0` is a NO CALL, and so is any split that is neither a majority nor none.**

| Instrument | Right | Detail |
|---|---|---|
| **Matched class** | **15/22** | **13 of 19 FORs · 2 of 3 AGAINSTs** — `19 + 3 = 22` ✅, `13 + 2 = 15` ✅ |
| **Direct head-to-head** | 🔴 **2/8** | **2 of 5 FORs · 0 of 3 AGAINSTs**, **15 NO CALLS** — `8 + 15 = 23` ✅ |

⚠️ 🔴 **ONE BOUNDARY ROW EXCLUDED AND NAMED rather than silently bucketed — Carlos Rodón `u15.5 outs`, class `all_pct` exactly 50.0%, result L.** **`22 + 1 = 23` ✅.**

🔴 **THE TWO INSTRUMENTS DISAGREED ON FOUR ROWS AND THE CLASS WAS RIGHT ON ALL FOUR** — Zebby Matthews `o14.5 outs` (class FOR, h2h AGAINST on `cleared 0/1`, W), George Kirby `u5.5 K` (class FOR, h2h AGAINST on `cleared 0/1`, W), Nick Martinez `u4.5 K` (class FOR, h2h AGAINST on `cleared 0/1`, W), JR Ritchie `u4.5 K` (class AGAINST, h2h FOR on `cleared 1/1`, L). ⛔ **Four rows is not a comparison of two instruments and every one of those head-to-heads is a SINGLE prior start.** ⚠️ **On 9/15 the class also won all five disagreements; on 9/13 the head-to-head won all three. The instrument that "wins" flips slate to slate, which is what n=3-to-5 looks like.**

### ✅ PRE-PUBLISH CHECK 36 — STILL CLOSED · 🔴 **RULE 51's INSTRUMENT DID NOT FIRE AT ALL, FOR THE FIRST TIME SINCE IT WAS BUILT**

✅ **`h2h_gap_days` present on all 8 rows with a prior meeting, `h2h_rematch` on all 25, the substring `days` appearing 36 times.**

🔴 **NOT ONE ROW SITS INSIDE THE 30-DAY WINDOW. The nearest is 36 days; the full gap set is 36, 39, 74, 79, 126.** ⛔ **The machine-population rule-51 log gains NO rows. The pre-registered mean-K specification is still CLOSED-FAILED and the threshold version is still EXPLORATORY (T18). Nothing re-specified.** ⚠️ **Worth stating after 9/14 (five rows, all missed, three starts) and 9/15 (four rows, all hit, three starts): the instrument's `n` is a property of the night's schedule, not of the model, and two opposite slates followed by an empty one is exactly what that looks like.**

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS ELEVENTH FORM IN ELEVEN SLATES — **AND IT IS THE MOST EXTREME YET**

`[measured 2026-09-17 by enumerating every leg of all 32 tickets]` **`Brady Basso u14.5 outs` is a leg in 31 of the 32 tickets — 7 of 8 PAIRS and ALL 24 PARLAYS. He was pulled after 2.2 innings for EIGHT outs, so the leg cleared by more than six outs and every ticket holding it survived to be decided by its partner. By NAME: Basso 31/32, Anthony Molina 18/32, Anthony Kay 11/32.**

➡️ **The surface printed PAIRS 8/8 and PARLAYS 18/18.** ⛔ **That is ONE OUTING reported thirty-one times, not thirty-one judgements, and it must be read that way before the number is read.**

⛔ **AND THE COMPARISON THAT MATTERS IS WITH THE SLATE IMMEDIATELY BEFORE IT: on 9/15 the dominant leg (Ke'Bryan Hayes, 14 of 32) DID NOT PLAY and voided 58% of the parlay pool. Same defect, opposite sign, consecutive nights.** ➡️ **A pool set by one arm yields an 8/8 and a 0/8 with equal ease. Nothing in `card.py` changed that anyone has recorded, and a grading run does not touch it.**

✅ **All 32 tickets DISTINCT.** ✅ **The `in_band` flag and the `parlay_rule` prose AGREE on all 32 tickets — the 2026-09-11 ceiling fix has now held for six consecutive grading runs and is NOT re-reported as open.**

### ✅ THE CONTROL — SIX ROUTES, ZERO DOMAIN VIOLATIONS

`[measured 2026-09-17 — full detail in `claude/pick-ledger.md`'s 2026-09-17 control block]`

**Both the 9/16 and 9/15 stored result files domain-checked and recomputed (15 games each, all `Final`, zero violations); the ENTIRE stored pitcher corpus checked — 17,602 game-log rows across 523 players, `pulled_at 2026-09-17T10:21:23Z`, `n_failed: 0` — zero there too; FULL-SEASON SUMS 16/16 EXACT on outs, K and `gamesStarted` against the season block stored beside each carded starter's game line; each game line 16/16 EXACT against the corpus log; the LIVE `statsapi` game log 2/2 EXACT and agreeing THREE ways with a terminal date anchor (Zebby Matthews 22 splits / 376 outs / 107 K, Max Scherzer 16 / 218 / 54); and the runner's own `record.json`, built `2026-09-17T10:22:34Z`, reproducing `2026-09-16 w:30 n:42 voids:8`, `2026-09-15 w:33 n:45 voids:5` and `by_kind.pitcher: 284/562` EXACTLY.**

🔴 **THE DIVERGENCE CHECK FAILED ITS PASS CONDITION: `project_info` gives `claude/pick-ledger.md` a `created_at` of `2026-09-17T08:27:55Z` and this page `2026-09-16T11:51:22Z` — nominally one grading run apart, the standing pass condition — AND THE LEDGER WAS STILL THE DOCUMENT BEHIND.** ➡️ **The check as written is not sufficient: a NEWER `created_at` on the ledger does not mean the ledger carries the newer RECORD, because an interactive session can rewrite it from an older base. ⛔ The only reliable test is to look for the previous slate's dated block by name, which is what this run did.**

**Progress: TABLE M — 25 slates, 562 graded pitcher plays, 189 graded pairs. TABLE M-H — 24 slates, 586 graded hitter rows.** *(`539 + 23 = 562` ✅ · `181 + 8 = 189` ✅ · `567 + 19 = 586` ✅ — counted against the dated slate block added since, not against another number.)*

---

## 🆕 2026-09-18 — THE TWENTY-SIXTH MACHINE SLATE (2026-09-17): A SIXTEENTH CARD WRITTEN EXACTLY ONCE, **THE WORST EIGHTEEN-ROW-OR-LARGER MACHINE BOARD THIS PROJECT HAS GRADED**, `carried` LEADING THE FOUR ESTIMATORS FOR A SECOND CONSECUTIVE SLATE ON A DIFFERENT FULL ORDERING — AND 🔴🔴 **THIS PAGE WAS ONCE AGAIN THE DOCUMENT THAT SURVIVED, WHILE THE LEDGER LOST TWO GRADING RUNS**

`[graded 2026-09-18]` ✅ **`picks/2026-09-17.json` AS COMMITTED IS 50 PLAYS — 18 PITCHER AND 32 HITTER — ACROSS ALL 9 OF THE SLATE'S 9 GAMES.** **`18 + 32 = 50` ✅.**

🔴 **TABLE M 6/18 (33.3%), ZERO UNGRADED — every carded arm started.** **Full rows, the summary and every reconciliation are in `claude/pick-ledger.md`'s dated 2026-09-17 blocks; this page carries only the diagnostics.**

🔴🔴 **AND THE RUN'S BIGGEST FINDING IS AGAIN NOT ABOUT THIS CARD: `claude/pick-ledger.md` HAD NO 2026-09-15 AND NO 2026-09-16 RECORD WHEN THIS RUN STARTED**, while THIS page carried complete `2026-09-16` and `2026-09-17` blocks grading both of them. **FOURTH occurrence of the divergence (9/11, 9/12, 9/15, and now 9/15 AGAIN plus 9/16) — and the FIRST time a block that had ALREADY been restored once was lost a SECOND time.** ✅ **Both slates were re-derived from source WITHOUT reading this page first and reproduced EVERY figure published here EXACTLY — 14/24 and 14/23, all four Brier values on each, every mean, every band cell, pairs 4/8 and 8/8, parlays 6/10 with 14 ungraded and 18/18 with 6 ungraded.** ⛔ **Nothing on this page needed correcting; the ledger now carries all three slates and the divergence is written up there.** ⚠️ 🔴 **THE STANDING DIVERGENCE CHECK IS NOW KNOWN TO BE INSUFFICIENT IN BOTH DIRECTIONS: the 9/17 run recorded that a NEWER `created_at` on the ledger does not mean the ledger carries the newer RECORD, and this run is the instance that proves it — the ledger's `created_at` was `2026-09-17T12:19:36Z` against this page's `2026-09-17T11:50:58Z`, newer by half an hour and missing two slates.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **TWENTY-SIXTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play has been carded since 8/22. T15's denominator is CARDED plays and the machine board is a different population, so nothing was substituted into it. T15 stays at 31/100 against its own pre-registered `n` bar.** ⚠️ **The drought is twenty-six days.**

⚠️ **Brier on the machine population, for the record and in NO T15 denominator:** ✅ `carried` **.2737** · `raw` **.2920** · `blend` **.2945** · 🔴 `model` **.3122** — **means `carried` 53.9 · `raw` 61.4 · `blend` 58.7 · `model` 55.9 against an actual 33.3%.**

🔴 **THE LEADER REPEATS FOR THE FIRST TIME IN FOUR SLATES — `carried` again — AND THE FULL ORDERING IS DIFFERENT AGAIN.** **9/14: `model` first, `raw` last, spread .0600. 9/15: `raw` first, `model` last, spread .0259. 9/16: `carried` first, `raw` last, spread .0214. 9/17: `carried` first, `model` last, spread .0385.** ⛔ **Four slates, four full orderings, at n≈18–24. LOG, DO NOT CONCLUDE.** ⚠️ **And the reason `carried` leads is the ordinary one and is stated so it is not mistaken for skill: it is the LOWEST of the four estimators on a night the board went 33.3%.**

⚠️ **The "which was closer" tally on this population reads model 7, raw 11, tie 0** *(`7 + 11 + 0 = 18` ✅, counted against the 18 graded rows)*. ⛔ **It is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no fit.**

### 🟡 THE `carried` SHADOW — 9/17. ✅ **BETTER — THE TWELFTH TIME IN TWENTY-SIX SLATES — BY THE ORDINARY MECHANISM.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed on 6 of 18 rows across FOUR arms — Justin Wrobleski, Tanner Gordon, Walbert Ureña and Taj Bradley.** **On the differing set `carried` scores .2502 against `blend`'s .3124, and that set went 2/6 = 33.3% against a slate rate of 33.3%.** ➡️ **`carried` was the LOWER number on a subset that performed exactly at the slate rate, on a slate that missed its own estimate by 25.4 — which is the mechanism that has made it better on every losing night and worse on every winning one.** **Running total 193 differing rows across twenty-six slates.** *(`187 + 6 = 193` — counted against the dated slate block added since, not against another number.)* ⛔ **Nothing adopted, rejected or re-specified.**

### 🔴 RULE 35 / T11 — THE SHADOW LADDER, EVERY START NAMED, AND DELIBERATELY NOT MERGED

**The 9/17 card carries Hard Rock alt ladders on 9 of its 18 pitcher rows.** ✅ **Deduplicated on (pitcher, date): Brady Singer carries TWO carded rows sharing ONE ladder and ONE start.** ➡️ **64 rungs across EIGHT DISTINCT STARTS. `n` is reported as DISTINCT STARTS, never as rung count.**

**THE EIGHT STARTS, NAMED, WITH THE ACTUAL STRIKEOUT COUNT EACH LADDER RESOLVES AGAINST:**

| Pitcher | Date | Rungs | Actual K |
|---|---|---|---|
| Brady Singer | 2026-09-17 | 8 | **0** |
| Justin Wrobleski | 2026-09-17 | 9 | 3 |
| Walbert Ureña | 2026-09-17 | 8 | **9** |
| Michael King | 2026-09-17 | 7 | 6 |
| Tanner Gordon | 2026-09-17 | 6 | 3 |
| Nolan McLean | 2026-09-17 | 9 | 5 |
| Sonny Gray | 2026-09-17 | 9 | 6 |
| Taj Bradley | 2026-09-17 | 8 | **9** |

✅ `8 + 9 + 8 + 7 + 6 + 9 + 9 + 8 = 64` ✅ across `n = 8` DISTINCT STARTS.

⛔ **NOT MERGED INTO THE 8/20–8/22 ACCUMULATOR, AND THE REASON IS UNCHANGED: that accumulator is the CARDED population and this is the MACHINE population.** **The two are never pooled, and a pass that does not name its starts cannot be merged at all.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/17. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/16 blocks: the matched class ARGUED FOR the play when its ALL-STARTS rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a MAJORITY of prior meetings cleared the number and AGAINST when NONE did; `n=0` is a NO CALL, and so is any split that is neither a majority nor none.**

| Instrument | Right | Detail |
|---|---|---|
| **Matched class** | 🔴 **4/17** | **2 of 11 FORs · 2 of 6 AGAINSTs** — `11 + 6 = 17` ✅, `2 + 2 = 4` ✅ |
| **Direct head-to-head** | **5/9** | **3 of 7 FORs · 2 of 2 AGAINSTs**, **9 NO CALLS** — `9 + 9 = 18` ✅ |

⚠️ 🔴 **ONE BOUNDARY ROW EXCLUDED AND NAMED rather than silently bucketed — Framber Valdez `o17.5 outs`, class `all_pct` exactly 50.0%, result L.** **`17 + 1 = 18` ✅.**

🔴🔴 **THE TWO INSTRUMENTS DISAGREED ON FIVE ROWS AND THE HEAD-TO-HEAD WAS RIGHT ON FOUR OF THE FIVE — REVERSING TWO CONSECUTIVE SLATES ON WHICH THE CLASS WON EVERY DISAGREEMENT.** Michael King `o4.5 K` (class AGAINST, h2h FOR on `cleared 1/1`, **W**), Sonny Gray `u5.5 K` (class FOR, h2h AGAINST on `cleared 0/1`, **L**), Nolan McLean `o17.5 outs` (class AGAINST, h2h FOR on `cleared 1/1`, **W**), Taj Bradley `u17.5 outs` (class FOR, h2h AGAINST on `cleared 0/1`, **L**) — and the one it got wrong, Taj Bradley `u6.5 K` (class AGAINST, h2h FOR on `cleared 1/1`, **L**). ⛔ **Five rows is not a comparison of two instruments and every one of those head-to-heads is a SINGLE prior start.** ⚠️ 🔴 **AND THE REVERSAL IS THE POINT: on 9/15 the class won all five disagreements, on 9/16 all four, and tonight it lost four of five. The instrument that "wins" flips slate to slate, which is what n=4-to-5 looks like.** ⛔ **LOG, DO NOT CONCLUDE. Rule 50's own tally is unmoved at 4/9.**

### ✅ PRE-PUBLISH CHECK 36 — STILL CLOSED · 🔴 **RULE 51's INSTRUMENT DID NOT FIRE, FOR A SECOND CONSECUTIVE SLATE**

✅ **`h2h` present on all 18 pitcher rows, `h2h_gap_days` present on all 9 rows with a prior meeting, `h2h_rematch` on all 18.**

🔴 **NOT ONE ROW SITS INSIDE THE 30-DAY WINDOW. The nearest is 43 days; the full gap set is 43, 51, 51, 60, 60, 67, 67, 97, 110.** ⛔ **The machine-population rule-51 log gains NO rows. The pre-registered mean-K specification is still CLOSED-FAILED and the threshold version is still EXPLORATORY (T18). Nothing re-specified.** ⚠️ **Two consecutive empty slates after 9/14 (five rows, all missed) and 9/15 (four rows, all hit) is the same point as before: the instrument's `n` is a property of the night's schedule, not of the model.**

### 🔴 THE BAND SHAPE — **AND EVERY BAND MISSED, WITH TWO-THIRDS OF THE BOARD UNDER 60**

| Band | Record | Mean `blend` | Gap |
|---|---|---|---|
| 80-plus | **— NO ROWS** | — | — |
| 70-80 | 🔴 **0/1 = 0.0%** | 76.3 | 🔴 **−76.3** |
| 60-70 | 🔴 **2/5 = 40.0%** | 64.1 | 🔴 **−24.1** |
| under-60 | 🔴 **4/12 = 33.3%** | 54.9 | 🔴 **−21.6** |

✅ `1 + 5 + 12 = 18` ✅ · `0 + 2 + 4 = 6` ✅.

⚠️ **The 70-80 cell is ONE ROW — Justin Wrobleski `o13.5 outs` at 76.3, who recorded NINE outs on 32 pitches — and means nothing alone.** 🔴 **What carries the slate is that BOTH multi-row cells missed by more than twenty points in the same direction, on a board where two-thirds of the rows sat under 60 to begin with.** ⛔ **One slate of eighteen rows. No cause is asserted and nothing is re-specified.**

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS TWELFTH FORM IN TWELVE SLATES — **AND THIS ONE IS A HITTER, NOT AN ARM, AND IT LOST**

`[measured 2026-09-18 by enumerating every leg of all 32 tickets]` **`Jahmai Jones u0.5 RBI` is a leg in 17 of the 32 tickets. He drove in a run, so the leg LOST and every ticket holding it was dead before its partner mattered.** **By NAME: Jones 17/32, Xander Bogaerts 14/32, Michael King 10/32, Luisangel Acuña 9/32.**

➡️ **The surface printed PAIRS 5/8 and PARLAYS 5/24, with the three-leg row at 0/8.** ⛔ **That is ONE PLATE APPEARANCE reported seventeen times, not seventeen judgements.** ⚠️ **It is the mirror of 9/16, where one arm's `u14.5 outs` cleared by six outs and printed 8/8 and 18/18 — same defect, opposite sign, two nights apart.** ⛔ **A grading run does not touch `card.py`; this is for an interactive session.**

✅ **All 32 tickets DISTINCT.** ✅ **The `in_band` flag and the `parlay_rule` prose AGREE on all 32 tickets — the 2026-09-11 ceiling fix has now held for nine consecutive grading runs and is NOT re-reported as open.**

### ✅ THE CONTROL — SIX ROUTES, ZERO DOMAIN VIOLATIONS

`[measured 2026-09-18 — full detail in `claude/pick-ledger.md`'s 2026-09-18 control block]`

**All THREE slates' stored result files domain-checked and recomputed (1,210 lines — 354 pitcher and 856 batter — across 39 games, every one `Final`, zero violations, and the IP↔outs identity re-derived on every pitcher line); the ENTIRE stored pitcher corpus checked — 17,690 game-log rows across 524 players, `pulled_at 2026-09-18T10:02:50Z`, `n_failed: 0`, `domain_violations: 0` — zero there too, with started home 2,256 = started road 2,256 exactly; FULL-SEASON SUMS 45/45 EXACT on outs, K AND `gamesStarted` against the season block stored beside each carded starter's game line; the LIVE `statsapi` enumerated game log 2/2 EXACT and agreeing THREE ways WITH a terminal anchor (Michael King `N=31 LAST=2026-09-17`, 543 outs / 154 K; Tanner Gordon `N=23 LAST=2026-09-17`, 301 outs / 84 K); the runner's own `record.json`, built `2026-09-18T10:03:17Z`, reproducing `2026-09-15 w:33 n:45 voids:5`, `2026-09-16 w:30 n:42 voids:8`, `2026-09-17 w:26 n:46 voids:4` and `by_kind.pitcher: 290/580` EXACTLY; and the standings identity W 2,294 = L 2,294 across 30 enumerated rows.**

⚠️ **The one open divergence is the historical hitter row — the runner's `by_kind.hitter` at `439/615` against the ledger's `438/614`, still EXACTLY one apart in both terms and not from any of these three slates.**

**Progress: TABLE M — 26 slates, 580 graded pitcher plays, 197 graded pairs. TABLE M-H — 25 slates, 614 graded hitter rows.** *(`562 + 18 = 580` ✅ · `189 + 8 = 197` ✅ · `586 + 28 = 614` ✅ — counted against the dated slate blocks added since, not against another number.)*

---

## 🆕 2026-09-19 — THE TWENTY-SEVENTH MACHINE SLATE (2026-09-18): A SEVENTEENTH CARD WRITTEN EXACTLY ONCE, THE **WIDEST PRE-SLATE MARGIN OF ANY SEPTEMBER CARD**, `carried` LEADING THE FOUR ESTIMATORS FOR A THIRD CONSECUTIVE SLATE — AND 🔴 **THE HITTER BOARD LOSING EIGHT OF TWENTY-FIVE ROWS TO PLAYERS WHO NEVER BATTED, THE MOST IT HAS EVER LOST**

`[graded 2026-09-19]` ✅ **`picks/2026-09-18.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 14 OF THE SLATE'S 15 GAMES.** **`25 + 25 = 50` ✅.**

✅ **WRITTEN EXACTLY ONCE: commit `0827784`, `2026-09-18T14:04:18Z`, 14 seconds after the file's own `generated_at` of `14:04:04Z`, on a full history (`git fetch --unshallow`, 3,407 commits, one entry in the path log).** ✅ **Earliest `commence` on any row is `2026-09-18T22:41:00Z`, a pre-slate margin of **8h 36m 56s** — `[measured 2026-09-19 by computing the same margin for ALL TWENTY-EIGHT dated cards in `picks/`]` **the widest of any SEPTEMBER card, ahead of 9/15's 8h 28m 38s, and second only to 8/23's 13h 01m 01s in the whole record.** ⚠️ **Stated as arithmetic, not as an improvement — the cron did not change; a card written at 14:04Z is early or late depending only on when the slate starts.**

⚠️ **THE ONE GAME WITH NO CARDED ROW IS `PHI @ NYM`, AND IT IS SELECTION, NOT A DROPPED EVENT — SAID THAT WAY ROUND BECAUSE THE TWO LOOK IDENTICAL ON THE CARD.** `[measured 2026-09-19]` **The event IS in the odds pull (`data/2026-09-18/props-pitcher/1110.json.gz`, `n_events: 15`, PHI @ NYM carrying 9 bookmakers) and IS in the results (15 games, `n_final: 15`).** **The card's own `board_rule` says 54 pitcher and 2,280 hitter rows were priced and 50 are shown, so a game simply having no row in the top 25 of either half is the selection rule operating.** ⛔ **Pre-publish check 3 is NOT failing here, and it would be wrong to log it as failing.**

🔴 **TABLE M 14/25 (56.0%), ZERO UNGRADED, ZERO PUSH — every carded arm started.** **Full rows, the summary and every reconciliation are in `claude/pick-ledger-2.md`'s dated 2026-09-18 block** — 🔴 **NOT in `claude/pick-ledger.md`, which could not be written to this run either; see that page's cap banner.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **TWENTY-SEVENTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play has been carded since 8/22. T15's denominator is CARDED plays and the machine board is a different population, so nothing was substituted into it. T15 stays at 31/100 against its own pre-registered `n` bar.** ⚠️ **The drought is now TWENTY-SEVEN DAYS.**

⚠️ **Brier on the machine population, for the record and in NO T15 denominator:** ✅ `carried` **.2328** · `raw` **.2445** · `blend` **.2495** · 🔴 `model` **.2669** — **means `carried` 65.7 · `raw` 73.2 · `blend` 70.0 · `model` 66.8 against an actual 56.0%.** **Gap on the carded estimate: 🔴 −14.0.**

🔴 **`carried` LEADS FOR A THIRD CONSECUTIVE SLATE — the first time any estimator has led three running — AND THE FULL ORDERING IS DIFFERENT AGAIN.** **9/16: `carried` first, `raw` last. 9/17: `carried` first, `model` last, spread .0385. 9/18: `carried` first, `model` last, spread .0341.** ⚠️ **Four estimators and twenty-seven slates: a repeat is what chance produces, and this page has said the same thing every time the leader changed.** ⛔ **Nothing is adopted.**

⚠️ **The "which was closer" tally on this population reads model 7, raw 18, tie 0** *(`7 + 18 + 0 = 25` ✅, counted against the 25 graded rows)*. ⛔ **It is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no denominator.**

### 🟡 THE `carried` SHADOW — 9/18. ✅ **BETTER — THE THIRTEENTH TIME IN TWENTY-SEVEN SLATES — BY THE ORDINARY MECHANISM.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed on 7 of 25 rows across SIX arms — Connor Prielipp, David Sandlin, Ian Seymour, Kumar Rocker, Nick Pivetta and Randy Dobnak.** **On the differing set `carried` scores .2098 against `blend`'s .2692, and that set went 3/7 = 42.9% against a slate rate of 56.0%.** ➡️ **The mechanism is the ordinary one and is stated so it is not read as a finding: `carried` is the blend after the T21/T22 haircuts, the haircut rows underperformed the board, and a lower number on a worse-performing subset scores better. ⛔ That is not evidence the haircut predicts.**

### 🔴 RULE 35 / T11 — THE SHADOW LADDER, EVERY START NAMED, AND DELIBERATELY NOT MERGED

**The 9/18 card carries Hard Rock alt ladders on 12 of its 25 pitcher rows.** ✅ **Deduplicated on (pitcher, date): NO pitcher carries two laddered rows this slate, so 12 rows resolve to 12 distinct starts.** ➡️ **95 rungs across TWELVE DISTINCT STARTS. `n` is reported as DISTINCT STARTS, never as a rung count.**

**THE TWELVE STARTS, NAMED, WITH THE ACTUAL STRIKEOUT COUNT EACH LADDER RESOLVES AGAINST:**

| Pitcher | Date | Rungs | Actual K |
|---|---|---|---|
| Chase Burns | 2026-09-18 | 7 | 4 |
| David Sandlin | 2026-09-18 | 8 | 4 |
| Kyle Leahy | 2026-09-18 | 6 | **1** |
| Bryan Woo | 2026-09-18 | 9 | 4 |
| Kumar Rocker | 2026-09-18 | 8 | **2** |
| Dylan Cease | 2026-09-18 | 9 | 3 |
| Randy Dobnak | 2026-09-18 | 6 | **1** |
| Ranger Suarez | 2026-09-18 | 7 | 5 |
| Gerrit Cole | 2026-09-18 | 9 | 6 |
| Ian Seymour | 2026-09-18 | 9 | 5 |
| Peter Lambert | 2026-09-18 | 8 | 6 |
| Nick Pivetta | 2026-09-18 | 9 | 4 |

✅ `7 + 8 + 6 + 9 + 8 + 9 + 6 + 7 + 9 + 9 + 8 + 9 = 95` ✅ across `n = 12` DISTINCT STARTS.

⛔ **NOT MERGED INTO THE 8/20–8/22 ACCUMULATOR, AND THE REASON IS UNCHANGED: that accumulator is the CARDED population and this is the MACHINE population.** **The two are never pooled, and a pass that does not name its starts cannot be merged at all.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/18. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/17 blocks: the matched class ARGUED FOR the play when its ALL-STARTS rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a MAJORITY of prior meetings cleared the number and AGAINST when a minority did.**

| Instrument | Right | Detail |
|---|---|---|
| **Matched class** | **14/23** | **12 of 19 FORs · 2 of 4 AGAINSTs** — `19 + 4 = 23` ✅, `12 + 2 = 14` ✅ |
| **Direct head-to-head** | 🔴 **3/6** | **2 of 5 FORs · 1 of 1 AGAINST**, **19 NO CALLS** — `6 + 19 = 25` ✅ |

⚠️ 🔴 **TWO BOUNDARY ROWS EXCLUDED AND NAMED rather than silently bucketed — Dylan Cease `o6.5 K` and Ian Seymour `o5.5 K`, class `all_pct` exactly 50.0% on both, BOTH L.** **`23 + 2 = 25` ✅.**

⚠️ **THE TWO INSTRUMENTS DISAGREED ON EXACTLY ONE ROW AND THE CLASS WON IT** — Grayson Rodriguez `u16.5 outs` (class AGAINST at 48.8, h2h FOR on `cleared 1/1`), who recorded 20 outs: **L, so the class was right and the head-to-head wrong.** ⛔ **`n = 1`. That is not a result and is logged only so the running disagreement tally stays honest.**

🔴 **AND THE SHAPE OF THE HEAD-TO-HEAD FIELD IS ITSELF THE FINDING THIS SLATE: 19 of 25 rows read "never faced X this season."** **Every one of the six that had a meeting had exactly one or two of them — `cleared 1/1` five times and `cleared 0/2` once.** ⛔ **A tiebreaker built on a sample of one is a coin with a name on it, which is why ledger rule 50 makes it a TIEBREAKER and never an input.**

### ✅ PRE-PUBLISH CHECK 36 — STILL CLOSED · 🔴 **RULE 51's INSTRUMENT FIRED ON EXACTLY ONE ROW, THE FIRST FIRING SINCE 9/14**

✅ **`h2h` present on all 25 pitcher rows, `h2h_gap_days` present on all 6 rows with a prior meeting, `h2h_rematch` on all 25 (one true).**

🔴 **ONE ROW SITS INSIDE THE 30-DAY WINDOW — Chase Burns `o3.5 K` vs CHC, gap 19 days — AND IT WON (4 K).** **The full gap set is 19, 62, 70, 82, 83, 148.** ⚠️ **Rule 51's EXPLORATORY threshold result says a rematch inside 30 days is worth roughly 8 points at a 4+ K bar, i.e. it argued for dropping a rung; the row cleared anyway.** ⛔ **`n = 1`, the pre-registered mean-K specification is still CLOSED-FAILED at t = −1.78, and one winning row is not evidence in either direction. LOGGED, NOT CONCLUDED.**

### 🔴 THE BAND SHAPE — **THE 70-80 CELL IS THE WORST ON THE BOARD, AND IT IS THREE ROWS**

| Band | Record | Mean `blend` | Gap |
|---|---|---|---|
| 80-plus | ✅ **4/5 = 80.0%** | 87.8 | **−7.8** |
| 70-80 | 🔴 **1/3 = 33.3%** | 71.9 | 🔴 **−38.6** |
| 60-70 | 🔴 **9/17 = 52.9%** | 64.5 | 🔴 **−11.5** |
| under-60 | **— NO ROWS** | — | — |

✅ `5 + 3 + 17 = 25` ✅ · `4 + 1 + 9 = 14` ✅.

⚠️ **The 80-plus cell at −7.8 is the closest that band has come to its own claim in this table's history, and it is FIVE ROWS.** 🔴 **The card's own `calibration_warning` put 80-plus at −42.4 over n=22 when it was written; one five-row night does not move that, and the two numbers must not be read as a trend.** ⚠️ **The 70-80 cell is THREE ROWS and means nothing alone.** **What carries the slate is the 60-70 cell — seventeen rows, −11.5, and the shape the machine board has printed for a month.**

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS THIRTEENTH FORM IN THIRTEEN SLATES — **AND THIS TIME EVERY CONCENTRATED LEG WON, WHICH IS WHY THE NUMBER LOOKS GOOD**

`[measured 2026-09-19 by enumerating every leg of all 32 tickets — 8 pairs plus 24 parlays]` **THREE legs each appear in 17 of the 32 tickets — `Kyle Leahy o8.5 outs`, `Chase Burns o3.5 K` and `Nick Pivetta u15.5 outs` — and ALL THREE WON.** **By NAME: Chase Burns 23/32 · Kyle Leahy 22/32 · Nick Pivetta 17/32 · Tyler Mahle 8/32 · David Sandlin 8/32.**

➡️ **The surface printed PAIRS 6/8 and PARLAYS 11/20.** ⛔ **That is THREE OUTINGS reported thirty-two times, not thirty-two judgements — and it is the mirror of 9/17, where one leg in 17 tickets LOST and dragged the same surface down.** 🔴 **THE POINT IS THAT THE DEFECT IS INVISIBLE ON A GOOD NIGHT.** **A pool set by two or three legs prints a number that is those legs repeated; read it that way before reading the number, in both directions.**

⚠️ **AND THE PAIRS ARE BUILT FROM LADDER RUNGS, NOT FROM `picks[]` — SAID PLAINLY BECAUSE A GRADER WHO INDEXES ON `picks[]` SILENTLY LOSES SIX OF THE EIGHT.** `[measured 2026-09-19]` **`Chase Burns o2.5 K`, `Kyle Leahy o1.5 K`, `David Sandlin o2.5 K` and `Tyler Mahle o2.5 K` are ladder rungs and appear nowhere in `picks[]`; the card's own `schema_note` says `pairs[] may use any rung`.** ➡️ **Legs are parsed and graded against the game log directly. ⛔ A rung is still never a PLAY and never enters TABLE M.**

✅ **All 32 tickets DISTINCT.** ✅ **The `in_band` flag and the `parlay_rule` prose AGREE on all 32 tickets against Sam's live bands (1.80–2.20 two-leg, 3.00–6.00 three- and four-leg) — the 2026-09-11 ceiling fix has now held for ten consecutive grading runs and is NOT re-reported as open.**

### 🔴🔴 THE HITTER BOARD'S WORST NON-APPEARANCE RATE ON RECORD — **8 OF 25 ROWS NEVER BATTED, AND EVERY ONE WAS FLAGGED IN ADVANCE**

`[measured 2026-09-19, both by `pid` and independently by NAME against every batter line in all 15 games]` **TABLE M-H is 15/17 with EIGHT UNGRADED of 25 carded — 32.0%, against a previous high of 6 of 25 on 9/16.** **The eight rows are six distinct players: Ha-Seong Kim (×2), Luisangel Acuna (×2), Tyler Heineman, Angel Genao, Jake Rogers, Esteury Ruiz.**

🔴 **AND THE CARD HAD ALREADY SAID SO.** **Every one of the eight carries `lineup_risk: true`, and the split on `lineup_share` is clean on this slate: every ungraded row sits at 43.8% or below, and NO row at 50% or above failed to appear.** ⚠️ ⛔ **`n = 25` on one slate, this is a DESCRIPTIVE observation and NOT a test — pre-registering a `lineup_share` gate belongs to the monthly task, and running it here would destroy its pre-registration.** ➡️ **What is recorded is the measurement and nothing else.**

### ✅ THE CONTROL — ZERO DOMAIN VIOLATIONS, AND THE RUNNER'S OWN RECORD REPRODUCES THIS GRADING EXACTLY

`[measured 2026-09-19 — full detail in `claude/pick-ledger-2.md`'s 2026-09-18 control block]`

**The stored result file domain-checked and recomputed (15 games, every one `Final`, the IP↔outs identity re-derived on every pitcher line, zero violations); the ENTIRE stored pitcher corpus domain-checked at 17,813 rows across 525 players with zero violations; the SEASON-TOTAL SUM run on all 19 distinct carded starters on `outs`, `strikeOuts` AND `gamesStarted` with the game line matched row-for-row — 19/19 EXACT; and the standings identity `W == L` at 2,309 each across 30 enumerated teams.**

✅ **AND THE STRONGEST OF THEM: the runner's own `record.json` (built `2026-09-19T10:07:28Z`) carries `2026-09-18 w:29 n:42 voids:8`, and this page's independent grading is 14/25 pitcher + 15/17 hitter = **29/42 with 8 voids** — EXACT.** ✅ **Its cumulative `by_kind.pitcher: 304/605` reproduces TABLE M's new total EXACTLY (`290 + 14 = 304` ✅, `580 + 25 = 605` ✅).**

⚠️ **The one open divergence is unchanged and is NOT from this slate — the runner's `by_kind.hitter` at `454/632` against this project's `453/631`, still EXACTLY one apart in both terms, as it has been since it was first noticed.**

**Progress: TABLE M — 27 slates, 605 graded pitcher plays, 205 graded pairs. TABLE M-H — 26 slates, 631 graded hitter rows.** *(`580 + 25 = 605` ✅ · `197 + 8 = 205` ✅ · `614 + 17 = 631` ✅ — counted against the dated slate blocks.)*

---

## 🆕 2026-09-20 — THE TWENTY-EIGHTH MACHINE SLATE (2026-09-19): AN EIGHTEENTH CARD WRITTEN EXACTLY ONCE, 🆕 **THE BEST PITCHER BOARD THIS TABLE HAS GRADED — 19/25, above every rate in its own by-day table — ON A GAP OF +10.1**, `carried` FALLING TO LAST AFTER LEADING THREE RUNNING — AND 🔴🔴 **THE TICKET-POOL CONCENTRATION DEFECT IN ITS MOST DESTRUCTIVE FORM YET: THE CONCENTRATED LEG DID NOT LOSE, IT NEVER PLAYED**

`[graded 2026-09-20]` ✅ **`picks/2026-09-19.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS ALL FIFTEEN OF THE SLATE'S FIFTEEN GAMES.** **`25 + 25 = 50` ✅.**

✅ **WRITTEN EXACTLY ONCE: commit `5165496e`, `2026-09-19T14:09:44Z`, 6 seconds after the file's own `generated_at` of `14:09:38Z`, on a full history (`git fetch --unshallow`, 3,590 commits, one entry in the path log).** ✅ **Earliest `commence` on any row is `2026-09-19T18:11:00Z`, a pre-slate margin of **4h 01m 22s**, and every row's first pitch is after the write.** ⚠️ **An ordinary Saturday margin, not a wide one. 9/18's 8h 36m was a late-starting Friday; the cron did not move.**

✅ 🆕 **FULL SLATE COVERAGE — every one of the fifteen `(away, home)` pairs in the results file carries at least one carded row.** **Among the four cards this run examined it is the first FIFTEEN-game slate covered in full (9/16 and 9/18 each missed one; 9/17 was nine of nine).**

🆕 **TABLE M 19/25 (76.0%), ZERO UNGRADED, ZERO PUSH — every carded arm started.** **Full rows, the summary and every reconciliation are in `claude/pick-ledger.md`'s dated 2026-09-19 block.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **TWENTY-EIGHTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play has been carded since 8/22. T15's denominator is CARDED plays and the machine board is a different population, so nothing was substituted into it. T15 stays at 31/100 against its own pre-registered `n` bar.** ⚠️ **The drought is now TWENTY-EIGHT DAYS.**

⚠️ **Brier on the machine population, for the record and in NO T15 denominator:** ✅ `blend` **0.2012** · `raw` **0.2029** · `model` **0.2096** · 🔴 `carried` **0.2160** — **means `blend` 65.9 · `raw` 65.8 · `model` 66.1 · `carried` 59.6 against an actual 76.0%.** **Gap on the carded estimate: ✅ +10.1.**

🆕 🔴 **`blend` LEADS THIS SLATE AND `carried` FALLS FROM FIRST TO LAST, AFTER LEADING THREE CONSECUTIVE SLATES.** **9/16: `carried` first, `raw` last. 9/17: `carried` first, `model` last, spread .0385. 9/18: `carried` first, `model` last, spread .0341. 9/19: `blend` first, `carried` last, spread .0148 — the NARROWEST spread of the four.** ⚠️ **Four estimators, twenty-eight slates, and a leader that changes almost every time the board does. ⛔ Nothing is adopted, and a .0148 spread orders nothing at n=25.**

⚠️ **The "which was closer" tally on this population reads model 13, raw 12, tie 0** *(`13 + 12 + 0 = 25` ✅, counted against the 25 graded rows)*. ⛔ **It is the biased statistic rule 15's own banner warns against; it is NOT T15 evidence and enters no denominator.**

### 🟡 THE `carried` SHADOW — 9/19. 🔴 **WORSE — THE FIFTEENTH TIME IN TWENTY-EIGHT SLATES — AND BY THE ORDINARY MECHANISM RUNNING BACKWARDS.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed on 11 of 25 rows across 8 arms — Andrew Alvarez, Brandon Pfaadt, Bryce Miller, Bubba Chandler, Cal Quantrill, Grant Holmes, Noah Cameron, Robert Gasser.** **On the differing set `carried` scores 0.2591 against `blend`'s 0.2254, and that set went 8/11 = 72.7% against a slate rate of 76.0%.** ➡️ **The mechanism is the usual one inverted and is stated so it is not read as a finding: `carried` is the blend after the T21/T22 haircuts, the haircut rows very nearly matched the board rather than underperforming it, and a lower number on a subset that WON scores worse. ⛔ That is not evidence the haircut fails, any more than the last three slates were evidence it predicts.**

### 🔴 RULE 35 / T11 — THE SHADOW LADDER, EVERY START NAMED, AND DELIBERATELY NOT MERGED

**The 9/19 card carries Hard Rock alt ladders on 17 of its 25 pitcher rows.** 🔴 **Deduplicated on (pitcher, date): THREE pitchers carry TWO laddered rows each — Andrew Alvarez, Cal Quantrill, Christian Scott — and in every case the two rows carry the IDENTICAL ladder (asserted rung-for-rung on line, side and price, not assumed).** ➡️ **17 rows resolve to 14 DISTINCT STARTS and 112 rungs. `n` is reported as DISTINCT STARTS, never as a rung count** — **a rung count over all 17 rows would read 136 and would be wrong.**

**THE FOURTEEN STARTS, NAMED, WITH THE ACTUAL STRIKEOUT COUNT EACH LADDER RESOLVES AGAINST:**

| Pitcher | Date | Rungs | Actual K |
|---|---|---|---|
| Cal Quantrill | 2026-09-19 | 7 | **0** |
| Christian Scott | 2026-09-19 | 9 | 7 |
| Andrew Alvarez | 2026-09-19 | 8 | 8 |
| Grant Holmes | 2026-09-19 | 8 | 4 |
| Robert Gasser | 2026-09-19 | 9 | **2** |
| Cam Schlittler | 2026-09-19 | 10 | 6 |
| Bubba Chandler | 2026-09-19 | 8 | 6 |
| Tarik Skubal | 2026-09-19 | 8 | 3 |
| José Soriano | 2026-09-19 | 9 | 8 |
| Joe Ryan | 2026-09-19 | 8 | 5 |
| Michael McGreevy | 2026-09-19 | 6 | **1** |
| Casey Mize | 2026-09-19 | 7 | **2** |
| Jackson Jobe | 2026-09-19 | 8 | 9 |
| Hayden Wesneski | 2026-09-19 | 7 | 3 |

✅ `7 + 9 + 8 + 8 + 9 + 10 + 8 + 8 + 9 + 8 + 6 + 7 + 8 + 7 = 112` ✅ across `n = 14` DISTINCT STARTS.

⛔ **NOT MERGED INTO THE 8/20–8/22 ACCUMULATOR, AND THE REASON IS UNCHANGED: that accumulator is the CARDED population and this is the MACHINE population.** **The two are never pooled, and a pass that does not name its starts cannot be merged at all.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/19. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as the 8/23 through 9/18 blocks: the matched class ARGUED FOR the play when its ALL-STARTS rate is ≥50% and AGAINST below 50%; the head-to-head ARGUED FOR when a MAJORITY of prior meetings cleared the number and AGAINST when a minority did.**

| Instrument | Right | Detail |
|---|---|---|
| **Matched class** | ✅ **17/25** | **16 of 21 FORs · 1 of 4 AGAINSTs** — `21 + 4 = 25` ✅, `16 + 1 = 17` ✅ |
| **Direct head-to-head** | 🔴 **4/12** | **3 of 7 FORs · 1 of 5 AGAINSTs**, **13 NO CALLS** — `12 + 13 = 25` ✅ |

✅ **NO BOUNDARY ROW THIS SLATE — no `class.all_pct` sits at exactly 50.0, so nothing was excluded and `25 + 0 = 25` ✅.**

🔴 **THE TWO INSTRUMENTS DISAGREED ON FIVE ROWS — the most they ever have — AND THE CLASS WON FOUR OF THE FIVE.** **Michael McGreevy `o3.5 K` (class FOR at 54.0, h2h AGAINST on `cleared 0/1`) — **L**, h2h right. Casey Mize `u4.5 K` (FOR 52.2 vs AGAINST 0/1) — **W**, class right. José Soriano `u5.5 K` (FOR 51.0 vs AGAINST 0/1) — **W**, class right. Jackson Jobe `u4.5 K` (class AGAINST at 40.0 vs h2h FOR on `cleared 1/1`) — **L**, class right. Freddy Peralta `o15.5 outs` (FOR 61.8 vs AGAINST 0/1) — **W**, class right.** ⛔ **`n = 5`, and every one of the five head-to-heads is a sample of ONE start. That is not a result; it is logged so the running disagreement tally stays honest.**

🔴 **AND THE SHAPE OF THE HEAD-TO-HEAD FIELD AGAIN: 13 of 25 rows read "never faced X this season."** **Of the twelve that had a meeting, TEN had exactly one — `cleared 1/1` five times and `cleared 0/1` five times — and two had `cleared 2/2`.** ⛔ **A tiebreaker built on a sample of one is a coin with a name on it, which is why ledger rule 50 makes it a TIEBREAKER and never an input.**

### ✅ PRE-PUBLISH CHECK 36 — STILL CLOSED · ⚠️ **RULE 51's INSTRUMENT DID NOT FIRE AT ALL**

✅ **`h2h` present on all 25 pitcher rows, `h2h_gap_days` present on all 12 rows with a prior meeting, `h2h_rematch` on all 25 (zero true).**

⚠️ **NO ROW SITS INSIDE THE 30-DAY WINDOW. The full gap set is 36, 36, 65, 65, 70, 70, 74, 74, 84, 84, 161, 164 — the shortest is 36 days, six clear of the threshold.** ⛔ **The machine-population rule 51 log gains NO row this slate, and that is recorded rather than left blank.** **The pre-registered mean-K specification remains CLOSED-FAILED at t = −1.78 and the threshold version remains EXPLORATORY.**

### 🔴 THE BAND SHAPE — **THREE CELLS ABOVE THEIR OWN CLAIM, AND AN 80-PLUS CELL THAT IS ONE ROW**

| Band | Record | Mean `blend` | Gap |
|---|---|---|---|
| 80-plus | 🔴 **0/1 = 0.0%** | 82.9 | **-82.9** |
| 70-80 | ✅ **5/6 = 83.3%** | 73.3 | **+10.0** |
| 60-70 | ✅ **11/14 = 78.6%** | 63.6 | **+15.0** |
| under-60 | ✅ **3/4 = 75.0%** | 58.9 | **+16.1** |

✅ `1 + 6 + 14 + 4 = 25` ✅ · `0 + 5 + 11 + 3 = 19` ✅.

🔴 **THE 80-PLUS CELL IS ONE ROW — Cal Quantrill `o2.5 K` at a stated 82.9, who recorded ZERO strikeouts in 1.1 IP on 12 pitches.** ⛔ **A one-row cell at −82.9 is not a calibration reading and must not be quoted as one; it is printed so the table reconciles.** ✅ **The other three cells all landed ABOVE their own claim, and the fourteen-row 60-70 cell at +15.0 is the only one with enough rows to mean anything.** ⚠️ 🔴 **IT IS ALSO THE EXACT MIRROR OF 9/17, WHICH WENT 6/18 AND IS THIS TABLE'S WORST BOARD, THREE DAYS EARLIER.** ⛔ **Two ~25-row slates in opposite directions inside three days is what that sample size does. Report the fraction; do not narrate a trend — in either direction.**

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS FOURTEENTH FORM IN FOURTEEN SLATES — 🆕 **AND THIS ONE IS THE WORST: THE CONCENTRATED LEG DID NOT LOSE, IT NEVER PLAYED**

`[measured 2026-09-20 by enumerating every leg of all 32 tickets — 8 pairs plus 24 parlays]` **`Brayan Bello o1.5 K` appears in 17 of 32 tickets, `Jackson Jobe o2.5 K` in 16 of 32 and `Ha-Seong Kim u1.5 TB` in 13 of 32. By NAME: Jackson Jobe 17/32 · Brayan Bello 17/32 · Ha-Seong Kim 14/32 · Samad Taylor 12/32 · Christian Scott 7/32 · Carlos Narvaez 7/32.**

🔴 **Ha-Seong Kim was in 14 of the 32 tickets and Carlos Narvaez in 7 — AND NEITHER BATTED. Between them they VOIDED 18 of the 24 parlays.** ➡️ **The surface printed PAIRS 6/8 and PARLAYS 6/6, and that 6/6 is TWO PITCHERS — Jobe and Bello, both of whom won — reported six times.** ⛔ **Read the concentration before the number, and it has now shown all three faces inside three slates: a losing leg (9/17) dragging the surface down, a winning leg (9/18) flattering it, and an absent leg (9/19) deleting it.**

🔴 🆕 **AND ALL EIGHT PAIRS USE AT LEAST ONE LADDER RUNG THAT IS NOT IN `picks[]` — eight of eight, against six of eight yesterday, plus 22 of the 24 parlays.** **A grader that indexes pair legs on `picks[]` loses the ENTIRE pair surface this slate.** ⛔ **Legs are parsed and graded against the game log directly, and a rung is still never a PLAY.**

⚠️ 🆕 **`Brayan Bello` IS A LEG IN 17 OF 32 TICKETS AND HAS NO `picks[]` ROW AT ALL — he threw 8.0 IP and 11 K, the largest strikeout line on the slate.** ⛔ **Recorded as a measurement of two selection rules, not as a miss: `picks[]` ranks by blend against a price, the ticket pool draws from every rung.**

✅ **All 32 tickets DISTINCT.** ✅ **The `in_band` flag and the `parlay_rule` prose AGREE on all 32 against Sam's live bands (1.80–2.20 two-leg, 3.00–6.00 three- and four-leg) — the 2026-09-11 ceiling fix has now held for ELEVEN consecutive grading runs and is NOT re-reported as open.**

### 🔴 THE HITTER BOARD — **12/20 WITH FIVE UNGRADED, AND 9/18's CLEAN `lineup_share` SPLIT BREAKS**

`[measured 2026-09-20, both by `pid` and independently by ACCENT-FOLDED NAME against every batter line in all 15 games]` 🔴 **TABLE M-H is 12/20 with FIVE UNGRADED of 25 carded — 60.0%, the lowest since 9/10 — against a mean stated rate of 81.8, a gap of −21.8.**

**The five rows are three distinct players: Ha-Seong Kim (×2), Carlos Narvaez (×2), Jose Trevino.** ⚠️ **All five carry `lineup_risk: true`.** 🔴 **BUT THE 9/18 GLOSS — "no row at 50% or above failed to appear" — IS STRUCK AS A RULE AND KEPT AS A 9/18 FACT: Carlos Narvaez at `lineup_share` 52.3% did NOT appear, and Angel Genao at 20.5% DID.** ⛔ **`n = 25` on one slate, DESCRIPTIVE, not a test. Pre-registering a `lineup_share` gate belongs to the monthly task and running it here would destroy its pre-registration.**

⚠️ 🔴 **AND A GRADING-MECHANICS QUESTION IS FLAGGED RATHER THAN RE-DECIDED, BECAUSE TWO ROWS TURN ON IT.** **Zach McKinstry `u0.5 RBI` and Henry Davis `u1.5 TB` appear in the boxscore batter list with `0 AB` and `0 BB` — they entered the game and never came to the plate.** **This run graded them W on the precedent already in the ledger: the 9/16 block's 16/19 with six ungraded is reproduced ONLY by the appears-in-the-list rule (a plate-appearance rule gives 15/18 there, and 10/18 here).** ⚠️ **A book would VOID a prop on a player with no plate appearance, so the precedent disagrees with the book and not merely with an alternative.** ➡️ **FOR AN INTERACTIVE SESSION. ⛔ A grading run does not re-decide a mechanics question after seeing the data.**

### ✅ THE CONTROL — ZERO DOMAIN VIOLATIONS, AND THE RUNNER'S OWN RECORD REPRODUCES THIS GRADING EXACTLY

`[measured 2026-09-20 — full detail in `claude/pick-ledger.md`'s 2026-09-19 control block]`

**The stored result file domain-checked and recomputed (15 games, every one `Final`, the IP↔outs identity re-derived on all 140 pitcher lines, `tb ≥ H` and `hr ≤ H` on all 337 batter lines, zero violations); the ENTIRE stored pitcher corpus domain-checked at 17,964 rows across 527 players with zero violations; the SEASON-TOTAL SUM run on all 18 distinct carded starters on `outs`, `strikeOuts` AND `gamesStarted` with the game line matched row-for-row — 18/18 EXACT; and the standings identity `W == L` at 2,324 each across 30 enumerated teams.**

✅ **AND THE STRONGEST OF THEM: the runner's own `record.json` (built `2026-09-20T10:37:56Z`) carries `2026-09-19 w:31 n:45 voids:5`, and this page's independent grading is 19/25 pitcher + 12/20 hitter = **31/45 with 5 voids** — EXACT.** ✅ **Its cumulative `by_kind.pitcher: 323/630` reproduces TABLE M's new total EXACTLY (`304 + 19 = 323` ✅, `605 + 25 = 630` ✅).**

⚠️ **The one open divergence is unchanged and is NOT from this slate — the runner's `by_kind.hitter` at `466/652` against this project's `465/651`, still EXACTLY one apart in both terms.**

⚠️ 🔴 **ONE FALSE POSITIVE FROM THIS RUN'S OWN DOMAIN CHECK IS RECORDED SO IT IS NOT RE-RAISED NEXT RUN: `outs > bf` fired on two relief lines — Kody Funderburk (2 outs, 1 BF) and Ben Joyce (3 outs, 2 BF) — and BOTH ARE LEGAL.** **A double play retires two runners on one batter faced; a pickoff or caught stealing is an out with no batter faced at all.** ➡️ **`outs ≤ bf` is NOT a domain identity and was dropped. `k ≤ bf` IS one and held on all 140 lines.**

**Progress: TABLE M — 28 slates, 630 graded pitcher plays, 213 graded pairs. TABLE M-H — 27 slates, 651 graded hitter rows.** *(`605 + 25 = 630` ✅ · `205 + 8 = 213` ✅ · `631 + 20 = 651` ✅ — counted against the dated slate blocks.)*

---
## 🆕 2026-09-21 — THE TWENTY-NINTH MACHINE SLATE (2026-09-20): A NINETEENTH CARD WRITTEN EXACTLY ONCE, 🔴 **A −14.1 BOARD TWO DAYS AFTER THE BEST ONE, CARRIED ALMOST ENTIRELY BY ONE 60-70 CELL**, `model` FIRST AND `raw` LAST, AND RULE 51's INSTRUMENT FIRING ON ONE ARM THAT LOST BOTH ROWS

`[graded 2026-09-21]` ✅ **`picks/2026-09-20.json` AS COMMITTED IS 50 PLAYS — 25 PITCHER AND 25 HITTER — ACROSS 13 OF THE SLATE'S 15 GAMES.** **`25 + 25 = 50` ✅.** ✅ **WRITTEN EXACTLY ONCE: commit `1919c02`, `2026-09-20T14:38:48Z`, 13 s after `generated_at` `14:38:35Z`; earliest `commence` `17:36:00Z`, a pre-slate margin of 2h 57m 25s.** ⚠️ **No carded row on `PHI @ NYM` or `SF @ LAD` — detail in the ledger block; reported, not diagnosed.**

🔴 **TABLE M 13/25 (52.0%), ZERO UNGRADED, ZERO PUSH.** **Full rows and every reconciliation are in `claude/pick-ledger.md`'s dated 2026-09-20 block.**

### 🔴 T15 — NOT RESTATED THIS RUN EITHER. **TWENTY-NINTH CONSECUTIVE RUN, AND THE REASON IS STILL THE SPECIFICATION.**

**No TABLE A play has been carded since 8/22; T15's denominator is CARDED plays, so nothing was substituted. T15 stays at 31/100 against its own pre-registered `n` bar (read from `claude/owed-tests.md`, not restated).** ⛔ **The blend weight is not fitted.**

⚠️ **Brier on the machine population, for the record and in NO T15 denominator:** ✅ `model` **0.2331** · `carried` **0.2506** · `blend` **0.2561** · 🔴 `raw` **0.2940** — **means `model` 60.1 · `raw` 72.0 · `blend` 66.1 · `carried` 59.7 against an actual 52.0%.** **Gap on the carded estimate: 🔴 −14.1.** **Rule 15's raw rate is logged as its own value on every row with its denominator (the `raw` column of the ledger rows, e.g. `28/32`).**

⚠️ **The "which was closer" tally reads model 13, raw 12, tie 0** *(`13 + 12 + 0 = 25` ✅)*. ⛔ **The biased statistic rule 15's own banner warns against; NOT T15 evidence.**

### 🟡 THE `carried` SHADOW — 9/20. ✅ **BETTER THAN `blend`.** ⛔ **STILL IN NO DENOMINATOR.**

**It differed on 11 of 25 rows across 7 arms — Davis Martin, Griffin Jax, Jack Perkins, Jake Irvin, Rhett Lowder, Sandy Alcantara, Will Warren.** **On the differing set `carried` scores 0.2209 against `blend`'s 0.2333; that set went 6/11 = 54.5% against a slate rate of 52.0%.** ➡️ **The ordinary mechanism: on a board that landed well under its claim, the haircut number is closer.** ⛔ **Not evidence the haircut predicts. Nothing adopted.**

### 🔴 RULE 35 / T11 — THE SHADOW LADDER, EVERY START NAMED, AND DELIBERATELY NOT MERGED

**The 9/20 card carries Hard Rock alt ladders on 12 of its 25 pitcher rows.** 🔴 **Deduplicated on (pitcher, date): ONE pitcher — Patrick Sandoval — carries two laddered rows, and the two ladders are IDENTICAL (asserted rung-for-rung on line, side and price).** ➡️ **12 rows resolve to 11 DISTINCT STARTS and 86 rungs. `n` is DISTINCT STARTS.**

| Pitcher | Date | Rungs | Actual K |
|---|---|---|---|
| Patrick Sandoval | 2026-09-20 | 8 | 5 |
| Jack Perkins | 2026-09-20 | 8 | 4 |
| Jake Irvin | 2026-09-20 | 6 | 8 |
| Dean Kremer | 2026-09-20 | 9 | 8 |
| Jacob deGrom | 2026-09-20 | 9 | **2** |
| Walker Buehler | 2026-09-20 | 8 | 6 |
| Jacob Misiorowski | 2026-09-20 | 9 | 4 |
| Rhett Lowder | 2026-09-20 | 6 | 3 |
| Sandy Alcantara | 2026-09-20 | 6 | 3 |
| Michael Wacha | 2026-09-20 | 9 | 5 |
| Will Warren | 2026-09-20 | 8 | 4 |

✅ `8 + 8 + 6 + 9 + 9 + 8 + 9 + 6 + 6 + 9 + 8 = 86` ✅ across `n = 11` DISTINCT STARTS.

⛔ **NOT MERGED INTO THE 8/20–8/22 ACCUMULATOR — that is the CARDED population and this is the MACHINE population.**

### 🆕 TABLE M — MATCHED CLASS vs HEAD-TO-HEAD, 9/20. ⛔ **ITS OWN TALLY. NOT ADDED TO RULE 50's 4/9.**

**Same scoring convention as every prior block: class FOR at `all_pct` > 50, AGAINST below; head-to-head FOR when a majority of prior meetings cleared, AGAINST when a minority did; an even split is NO CALL.**

| Instrument | Right | Detail |
|---|---|---|
| **Matched class** | **14/24** | **11 of 19 FORs · 3 of 5 AGAINSTs** — `19 + 5 = 24` ✅, `11 + 3 = 14` ✅ · **1 BOUNDARY row excluded** (Patrick Sandoval `u15.5 outs`, class `18/36` = 50.0; L) — `24 + 1 = 25` ✅ |
| **Direct head-to-head** | **3/6** | **3 of 6 FORs · 0 AGAINSTs**, **19 NO CALLS** (16 "never faced" + 3 even splits at `cleared 1/2`) — `6 + 19 = 25` ✅ |

⚠️ **THE TWO DISAGREED ON ONE ROW AND THE CLASS WON IT — Davis Martin `o14.5 outs` (class AGAINST at 36.8, h2h FOR on `cleared 1/1`), 13 outs: L.** ⛔ **`n = 1`, a head-to-head of one start. Logged so the running disagreement tally stays honest.**

### ✅ PRE-PUBLISH CHECK 36 — STILL CLOSED · 🔴 **RULE 51's INSTRUMENT FIRED ON ONE ARM, TWO ROWS, AND BOTH LOST**

✅ **`h2h` present on all 25 pitcher rows, `h2h_gap_days` on all 9 rows with a prior meeting, `h2h_rematch` on all 25 (two true).** **Full gap set: 23, 23, 36, 56, 64, 64, 64, 65, 91.**

🔴 **Rhett Lowder vs CHC, gap 23 days — `o3.5 K` (L, 3 K) and `o14.5 outs` (L, 9 outs), 3.0 IP on 60 pitches.** ⚠️ **Rule 51's EXPLORATORY threshold result says a rematch inside 30 days costs roughly 8 points at a 4+ K bar — the `o3.5 K` row is exactly that bar and it missed.** ⚠️ **The outs row is NOT the quantity rule 51 measured and is logged as context only.** ⛔ **One start. The pre-registered mean-K specification remains CLOSED-FAILED at t = −1.78; the threshold version stays EXPLORATORY. LOGGED, NOT CONCLUDED** — **the machine rule-51 log now reads, by start: Chase Burns (W), Rhett Lowder (L).**

### 🔴 THE BAND SHAPE — **ONE CELL CARRIES THE SLATE**

| Band | Record | Mean `blend` | Gap |
|---|---|---|---|
| 80-plus | — 0 rows | — | — |
| 70-80 | ✅ **4/4 = 100.0%** | 75.1 | **+24.9** |
| 60-70 | 🔴 **8/20 = 40.0%** | 64.6 | **−24.6** |
| under-60 | ✅ **1/1 = 100.0%** | 59.5 | **+40.5** |

✅ `4 + 20 + 1 = 25` ✅ · `4 + 8 + 1 = 13` ✅. ⛔ **Two slates ago the 60-70 cell went 11/14; today 8/20. That is what ~20-row cells do.**

### 🔴🔴 THE TICKET-POOL CONCENTRATION DEFECT — THE WINNING-LEG DIRECTION AGAIN

`[measured 2026-09-21, all 32 tickets]` **`Sandy Alcantara o15.5 outs` in 18/32 · `Ha-Seong Kim u1.5 TB` in 15/32 · `Kade Anderson o2.5 K` in 12/32; by name Alcantara 19 · Kim 15 · Anderson 12 · Samad Taylor 12.** **All four won, so pairs 7/8 and parlays 23/23 (1 ungraded) are a few outings reported many times.** ⚠️ **Ticket #3 duplicates pair #1 across surfaces (31 distinct leg-sets in 32 tickets); within each surface every ticket is distinct.** ⚠️ **Kade Anderson again: a pair/parlay leg with NO `picks[]` row.**

### ✅ THE HITTER BOARD — **19/21 WITH FOUR UNGRADED**

**Mean graded `rate` 82.4 against 90.5% (+8.1).** **Ungraded: McKinstry (67.8%, risk), Keith (68.5%, risk), Trevino (27.3%, risk), 🔴 Karros (79.9%, `lineup_risk: false`).** ⚠️ **Kyle Isbel graded W with 0 AB / 0 BB on precedent; 18/20 on a plate-appearance rule.** ⛔ **DESCRIPTIVE; a gate is the monthly task's to pre-register.**

### ✅ THE CONTROL — ZERO DOMAIN VIOLATIONS, AND THE RUNNER'S OWN RECORD REPRODUCES THIS GRADING EXACTLY

**Five routes, detailed in the ledger's 2026-09-20 control block: result file (129 pitcher / 325 batter lines, 0 violations), full corpus (18,112 rows, 0 violations), season-total sum 18/18 exact on every distinct carded starter, runner `record.json` `2026-09-20 w:32 n:46 voids:4` exact, standings W = L = 2,339.** ✅ **The grading script reproduced the 9/19 block exactly before it was trusted on 9/20.**

## Changelog

- **2026-09-21 (7:30am grading run — the 9/20 slate)** — 🔴 **TABLE M 13/25 (52.0%), gap −14.1; one 60-70 cell of twenty rows went 8/20.** **Brier: `model` .2331 first, `raw` .2940 last; `carried` beat `blend` (.2209 vs .2333 on the 11 differing rows).** **Shadow ladder: 11 DISTINCT STARTS named, 86 rungs, one duplicate ladder (Sandoval) deduped; not merged.** **Class 14/24 (1 boundary), head-to-head 3/6 (19 no-calls), one disagreement, class right.** **Rule 51 fired on Rhett Lowder (23 days) — both rows lost; logged, not concluded.** **T15 untouched at 31/100; blend weight not fitted.** ⚠️ **Method: `project_read` → FILE path `cp`'d → PURE INSERTION of one block and one changelog line, anchor asserted once → `collections.Counter` line-loss check (zero lines lost) → `created_at` re-checked → `local_path` upload.**

- **2026-09-20 (7:30am grading run — the 9/19 slate)** — 🆕 **TABLE M 19/25 (76.0%), zero ungraded, zero push: the HIGHEST rate any machine board of eighteen rows or more has recorded, and the exact mirror of 9/17's record-low 6/18 three days earlier.** ⛔ **Two ~25-row slates in opposite directions inside three days is what that sample size does — the fraction is reported and no trend is narrated, in either direction.** ✅ **An eighteenth card written EXACTLY ONCE (`5165496e`, six seconds after its own `generated_at`), covering all fifteen of the slate's fifteen games, on a 4h 01m 22s pre-slate margin.** 🔴 **`blend` led the four estimators and `carried` fell from first to LAST after leading three running, on a .0148 spread that orders nothing.** 🔴🔴 **The ticket-pool concentration defect took its most destructive form yet — the concentrated leg did not lose, it never played: Ha-Seong Kim in 14 of 32 tickets and Carlos Narvaez in 7 VOIDED 18 of the 24 parlays, and the surviving "6/6" is two pitchers reported six times.** ⚠️ **Rule 51's instrument did not fire (shortest gap 36 days); the matched class went 17/25 and the head-to-head 4/12 with 13 no-calls, disagreeing on five rows — the most ever — with the class right on four.** 🔴 **9/18's clean `lineup_share` split is STRUCK as a rule and kept as a 9/18 fact: Narvaez at 52.3% did not appear and Genao at 20.5% did.** ⚠️ **A grading-mechanics question is FLAGGED not re-decided: two rows with `0 AB` and `0 BB` were graded W on the 9/16 precedent; a plate-appearance rule gives 10/18 instead of 12/20.** ✅ **Control: 18/18 exact season-total sums, zero domain violations across 17,964 corpus rows, and the runner's `record.json` reproducing 31/45 with 5 voids EXACTLY.** ⚠️ **One false positive from this run's own check recorded so it is not re-raised: `outs ≤ bf` is NOT a domain identity.** ⛔ **No graded row, bucket count, rung count, Brier value, specification or pass criterion above this entry was altered.**

- **2026-09-19 (7:30am grading run — the 9/18 slate, and the LEDGER IS NOW UNWRITABLE, not merely large)** — 🔴🔴 **`claude/pick-ledger.md` COULD NOT BE WRITTEN TO FOR A SECOND DAY: the project knowledge store is at ~1.59M of 2.00M and the cap check adds a doc's new size WITHOUT subtracting its old, so replacing the 1.72 MB ledger is treated as adding one.** **No write was attempted against it — a refused `project_write` on a delete-then-create API is not a risk worth taking with the only copy of every graded row.** ➡️ **The 2026-09-18 grading record is in `claude/pick-ledger-2.md`, which its own banner already declares to be the same document; the fix is Sam's call and is stated there.** ✅ **TABLE M 14/25 (56.0%), zero ungraded, zero push, from a seventeenth card written EXACTLY ONCE with the widest pre-slate margin of any September card (8h 36m 56s).** ✅ **`carried` leads the four estimators a THIRD consecutive slate — the first time any estimator has led three running — and is explicitly NOT adopted.** 🔴 **TABLE M-H lost EIGHT of 25 rows to players who never batted, the most on record, and every one of the eight was flagged `lineup_risk: true` in advance with `lineup_share` ≤ 43.8%; recorded as DESCRIPTIVE, with the pre-registration of any `lineup_share` gate left to the monthly task.** ⚠️ **The ticket pool was set by three legs in 17 of 32 tickets each and all three WON — the defect is invisible on a good night, which is the finding.** ✅ **Control: 19/19 exact season-total sums, zero domain violations across 17,813 corpus rows, and the runner's `record.json` reproducing 29/42 with 8 voids EXACTLY.** ⛔ **No graded row, bucket count, rung count, Brier value, specification or pass criterion above this entry was altered.**

- **2026-09-18 (7:30am grading run — the 9/17 slate, and this page was AGAIN the surviving document)** — 🔴🔴 **`claude/pick-ledger.md` HELD NO 2026-09-15 AND NO 2026-09-16 RECORD WHEN THIS RUN STARTED, while this page held complete blocks grading both.** **FOURTH occurrence of the divergence, and the FIRST time an already-restored block was lost a SECOND time.** ✅ **Both slates were re-derived from primary source WITHOUT reading this page first, reproduced every figure published here EXACTLY, and are now written back into the ledger; NOTHING ON THIS PAGE WAS CORRECTED.** ✅ **One block appended for the twenty-sixth machine slate (2026-09-17): TABLE M 6/18, zero ungraded; Brier `carried` .2737 / `raw` .2920 / `blend` .2945 / `model` .3122; the `carried` shadow BETTER for the twelfth time in twenty-six slates on 6 differing rows across 4 arms; the rule-35/T11 shadow ladder at 64 rungs across EIGHT NAMED DISTINCT STARTS; matched class 4/17 against head-to-head 5/9 with the head-to-head right on four of five disagreements, REVERSING two slates; rule 51's instrument not firing for a second consecutive slate (nearest gap 43 days); and the ticket-pool concentration defect in its twelfth form — one HITTER leg on 17 of 32 tickets, and it lost.** ⛔ **T15 NOT restated — twenty-sixth consecutive run, still 31/100, still no TABLE A card since 8/22.** ⛔ **NO pre-registered specification, pass criterion, closed verdict, counter base or dated block was altered; this write is an APPEND plus this entry.** ⚠️ **Method: `project_read` → the returned FILE copied verbatim (no retype) → programmatic patch with the anchor ASSERTED to occur EXACTLY ONCE → `collections.Counter` line-loss check (zero original lines lost) → fresh `project_read` compared immediately before upload → upload with `local_path`, per ledger rule 43.**

- **Sep 17 2026, 7:30am scheduled run — the twenty-fifth machine slate (2026-09-16): a fifteenth card written exactly once, a THIRD consecutive slate with a DIFFERENT four-estimator ordering, rule 51's instrument NOT FIRING AT ALL for the first time since it was built, and the ticket-pool concentration defect in its most extreme form yet — one leg in 31 of 32 tickets.** ✅ **TABLE M graded 14/23 (60.9%) with TWO UNGRADED (Robert Stock ×2 did not start; Xzavion Curry started for Baltimore, enumerated not inferred). Mean `blend` 69.3 against an actual 60.9%, gap −8.5.** ✅ **Brier `carried` .2171 · `blend` .2235 · `model` .2246 · `raw` .2385 — spread .0214 at n=23, against 9/15's .0259 and 9/14's .0600, and a THIRD distinct ordering in three nights. LOG, DO NOT CONCLUDE.** 🔴 **T15 NOT RESTATED for a TWENTY-FIFTH consecutive run: no TABLE A play since 8/22, drought twenty-five days, T15 stays at 31/100.** 🔴 **RULE 35 gained nothing again and deliberately — 103 rungs across THIRTEEN NAMED starts, itemised with actual K so it can be deduplicated on (pitcher, date); merge unchanged at 185 rungs / 25 distinct starts, T11 still 25/40.** 🆕 **MATCHED CLASS 15/22 with ONE boundary row EXCLUDED AND NAMED (Carlos Rodón `u15.5 outs`, exactly 50.0%, L); DIRECT head-to-head 2/8 with FIFTEEN no calls. They disagreed on FOUR rows and THE CLASS WON ALL FOUR. ⛔ Its own tally, not added to rule 50's 4/9.** ✅ **PRE-PUBLISH CHECK 36 STILL CLOSED.** 🔴 **Rule 51: NOT ONE row inside the 30-day window — nearest 36 days — so the log gains nothing, after 9/14's five-all-missed and 9/15's four-all-hit. The registered mean-K spec is still CLOSED-FAILED.** 🟡 **`carried` BETTER — the ELEVENTH time in twenty-five slates — differing on 9 of 23 rows across 6 arms, .2020 vs .2184 on the differing set, which went 5/9 = 55.6% against a slate rate of 60.9%; running total 187. In NO denominator.** 🔴 **Bands: 80-plus 3/3 (+11.1) on three rows, two of them resting on a `raw` of 5/5 and 3/3; 70-80 4/6 (−5.9); 60-70 7/12 (−6.0); under-60 0/2 (−59.8).** 🔴🔴 **THE CONCENTRATION DEFECT'S ELEVENTH FORM AND ITS MOST EXTREME: `Brady Basso u14.5 outs` in 31 of 32 tickets, pulled after 2.2 innings for EIGHT outs, printing PAIRS 8/8 and PARLAYS 18/18 — one outing reported thirty-one times, and the exact mirror of 9/15, where the dominant leg DID NOT PLAY and voided 58% of the pool.** ✅ **All 32 tickets distinct; the `in_band` flag and the `parlay_rule` prose agree on all 32 for a sixth consecutive run.** 🔴🔴 **AND THE FINDING THAT MATTERS MOST IS AGAIN NOT ON THIS PAGE: `claude/pick-ledger.md` had NO 2026-09-15 record when this run started, while this page carried the complete 2026-09-16 block grading it — the THIRD occurrence (9/11, 9/12, 9/15). The slate was re-derived from source WITHOUT reading this page first and reproduced every figure here EXACTLY. ⛔ Nothing here needed correcting; the ledger now carries both slates.** ⚠️ 🔴 **AND THE STANDING DIVERGENCE CHECK IS RECORDED AS INSUFFICIENT: the ledger's `created_at` (2026-09-17T08:27:55Z) is NEWER than this page's (2026-09-16T11:51:22Z) and it was STILL the document behind, because an interactive session can rewrite it from an older base. The reliable test is to look for the previous slate's dated block BY NAME.** ✅ **CONTROL: six routes, zero domain violations on both slates' result files and on 17,602 corpus rows; full-season sums 16/16 EXACT; the live enumerated statsapi route clean for a sixth consecutive run with a terminal date anchor; the runner's `record.json` reproducing `by_kind.pitcher: 284/562` and both `by_day` rows exactly.** ⛔ **NOTHING ABOVE THE NEW BLOCK WAS TOUCHED except the superseded Progress line, which is STRUCK IN PLACE rather than deleted. No existing bucket count, rung count, Brier value, graded row or specification was altered.**

- **Sep 16 2026, 7:30am scheduled run — the twenty-fourth machine slate (2026-09-15): a fourteenth card written exactly once, a NEW widest pre-slate margin at 8h 28m, the four-estimator Brier ordering EXACTLY REVERSED from 9/14, rule 51's instrument firing on FOUR rows that ALL WON — the mirror of yesterday — and a pre-stated hitter test that FAILED on its first slate.** ✅ **TABLE M graded 14/24 (58.3%) with ONE ungraded (Davis Martin relieved an opener; third instance of that shape, confirmed two ways, and grading him would have moved the headline DOWN to 14/25).** ✅ **Brier `raw` .2506 · `blend` .2573 · `carried` .2581 · `model` .2765 — spread .0259 at n=24, against 9/14's .0600 with `model` first and `raw` last. Opposite orderings on consecutive slates. LOG, DO NOT CONCLUDE.** 🔴 **T15 NOT RESTATED for a TWENTY-FOURTH consecutive run: no TABLE A play since 8/22, drought twenty-four days, T15 stays at 31/100.** 🔴 **RULE 35 gained nothing again and deliberately — 77 rungs across ELEVEN NAMED pitchers (twelve carded rows; Lake Bachar's two strikeout rows share one ladder, counted once; Davis Martin flagged NOT A START), merge unchanged at 185 rungs / 25 distinct starts, T11 still 25/40.** 🆕 **MATCHED CLASS 13/24 and the DIRECT head-to-head 1/8; they disagreed on FIVE rows and THE CLASS WON ALL FIVE, every one of those head-to-heads a `cleared 0/1` or `0/2`. ⛔ Its own tally, not added to rule 50's 4/9.** ✅ **PRE-PUBLISH CHECK 36 STILL CLOSED — all four rematch rows state the gap in days.** 🔴🔴 **Rule 51: four rows, ALL HIT, all at a six-day gap — three starts, and the exact mirror of 9/14's five-rows-all-missed over three starts. The pre-registered mean-K specification is still FAILED and still closed.** 🟡 **`carried` WORSE by .0008 — the narrowest margin either way this page has recorded — on FOURTEEN differing rows, the largest differing share yet; running total 178 across twenty-four slates. In NO denominator.** 🔴 **FIRST BOARD WITH NO `under-60` ROW AT ALL; 80-plus went 1/3 at −50.8 on three off-book rows across two arms; 60-70 carried the slate at 10/18 and −9.2.** 🔴🔴 **The ticket-pool concentration defect takes its TENTH form in ten slates and a form it has never taken: Ke'Bryan Hayes on 14 of 32 tickets DID NOT PLAY, so the parlay surface lost 58% of its own denominator — it did not sweep or wipe out, it VOIDED. The card's own `lineup_risk` flag was SET on him.** ✅ **PAIRS 4/8, all eight IN BAND at 1.815x–2.009x — the 9/14 arithmetic complaint is not present tonight.** 🔴 **CONTROL: five routes, zero domain violations on 464 result lines and 17,470 corpus rows — but the live enumerated statsapi route TRUNCATED four starts short on Cristopher Sánchez, caught only by the season-total sum, and came back EXACT on re-asking with a terminal anchor (ledger rule 285); and this run's own name-join near-miss on `Narváez`/`Acuña` (ledger rule 284).** ⛔ **NOTHING ABOVE THE NEW BLOCK WAS TOUCHED except the superseded Progress line, which is STRUCK IN PLACE rather than deleted.**
- **Sep 15 2026, 7:30am scheduled run — the twenty-third machine slate (2026-09-14): a thirteenth card written exactly once, the widest pre-slate margin of any September card, the four estimators separating for the first time in weeks with `model` first and `raw` last, `carried` WORSE for the clearest reason it has ever been worse — and RULE 51's instrument firing on FIVE ROWS THAT ALL LOST, which is THREE STARTS and not five.** ✅ **TABLE M graded 10/23 (43.5%) with ZERO ungraded — mean `model` 58.7, `raw` 64.3, `blend` 61.5, `carried` 58.5 against an actual 43.5%, a gap of −18.0 on the carded estimate.** ✅ **Brier `model` .2706 · `blend` .2930 · `carried` .3084 · `raw` .3306 — a spread of .0600 at n=23 against 9/13's .0158.** 🔴 **T15 NOT RESTATED for a TWENTY-THIRD consecutive run: no TABLE A play since 8/22, the drought is twenty-three days, T15 stays at 31/100 and the machine population is NOT its denominator.** 🔴 **RULE 35 gained nothing again and deliberately — 85 rungs across ELEVEN NAMED distinct starts, itemised so it can be deduplicated, merge unchanged at 185 rungs / 25 distinct starts, T11 still 25/40.** 🆕 **MATCHED CLASS 11/23 and the DIRECT head-to-head 4/11 on the eleven rows that carry one; they disagreed on FOUR rows and split them two apiece. ⛔ Its own tally, not added to rule 50's 4/9.** ✅ **PRE-PUBLISH CHECK 36 STILL CLOSED — all five rematch rows state the gap in days on the row.** 🔴 **Rule 51: five rows, all MISS, all at a six-day gap — but three starts, and Skubal and Mathews both went LONGER and struck out MORE than their unders allowed, which is the OPPOSITE of a haircut. The pre-registered mean-K specification is still FAILED and still closed; nothing is promoted and nothing is added to the carded tally.** 🟡 **`carried` WORSE — .3084 against `blend`'s .2930, differing on 5 of 23 rows across 4 pitchers, four of which WON; running total 164 differing rows across twenty-three slates. In NO denominator.** 🔴🔴 **The ticket-pool concentration defect takes its NINTH form in nine slates and produced its first 8/8: Kade Anderson `u5.5 K` in 24 of 32 tickets and in ALL EIGHT four-leg tickets, winning on EXACTLY five strikeouts — one more and the same board prints 1/8 and 2/23.** ✅ **CONTROL: five routes, zero domain violations, the live enumerated statsapi route clean for a fourth consecutive run.** ⛔ **NOTHING ABOVE THE NEW BLOCK WAS TOUCHED except the superseded Progress line, which is STRUCK IN PLACE rather than deleted.**

- **Sep 14 2026, 7:30am scheduled run — the twenty-second machine slate (2026-09-13): a twelfth card written exactly once with the pre-slate margin back to 2h 02m, the NARROWEST FOUR-ESTIMATOR BRIER SPREAD this table has produced, `carried` better for once NOT by the usual mechanism, rule 51's conditional cleared for only the second time — and a ticket surface where ONE concentration defect produced a 7/8 and a 0/8 on the same night.** ✅ **TABLE M graded 12/24 (50.0%) with ONE UNGRADED — Jake Irvin DID NOT START (Riley Cornelio started for WSH; Irvin is in the same game with `started: false`, i.e. he relieved), graded out on the 9/4 Kumar Rocker rule. Mean `model` 63.8, `raw` 70.5, `blend` 67.1, `carried` 61.7 against an actual 50.0%; Brier `carried` .2839 · `model` .2849 · `blend` .2856 · `raw` .2997 — a spread of .0158 at n=24 that orders nothing; gap −17.1.** ⛔ **T15 NOT restated for a TWENTY-SECOND consecutive run — no TABLE A play since 8/22 and the machine population is not T15's denominator. T15 stays 31/100.** ⛔ **RULE 35 gained nothing again and deliberately: 111 rungs across THIRTEEN NAMED distinct starts (fourteen carded rows — Jackson Jobe carries two and is ONE start), not merged. The merge stays 185 rungs / 25 starts, T11 25/40.** 🆕 **MATCHED CLASS vs HEAD-TO-HEAD, 9/13: class 10/23 — right on 8 of its 17 FORs and 2 of its 6 AGAINSTs — with ONE boundary row EXCLUDED AND NAMED (Jackson Jobe `u4.5 K`, 40/80 = 50.0%, result L); head-to-head 7/11 with THIRTEEN no calls (11 at `n=0` plus two Andrew Painter `cleared 1/2` rows the convention does not reach). The two instruments disagreed on THREE rows and the HEAD-TO-HEAD was right on all three — but two of the three are the same arm, and the instrument that "wins" has now flipped on three consecutive slates.** ✅ **CHECK 36 STAYS CLOSED for a THIRD slate — `h2h_gap_days` on all 13 rows with a prior meeting, `h2h_rematch` on all 25, `days` appearing 41 times.** 🔴 **THE RULE 51 LOG GAINS ROWS 26 AND 27 — Grant Holmes vs PHI at SIX days, on two carded rows that both LOST. The prior meeting (2026-09-07) produced SIX K, so for only the second time since the instrument was built the pair DOES clear the ≥5 K conditional; the rematch produced ZERO K in 4.0 IP, which is the direction the exploratory version predicts and an anecdote at n=1 arm. The registered mean-K spec is still CLOSED-FAILED with the threshold version EXPLORATORY; nothing re-specified.** 🟡 **`carried` BETTER — the TENTH time in twenty-two slates — but the mechanism RAN BACKWARDS: it differed on 9 of 24 rows across 6 pitchers, Brier .2839 vs .2856 overall and .2564 vs .2609 on the differing set, and that differing set went 5/9 = 55.6% against a slate rate of 50.0%, so being lower should have hurt it. At a .0017 overall margin nothing separates them. Running total 159 differing rows across twenty-two slates. Nothing adopted, rejected or re-specified.** 🔴 **THE BAND SHAPE: 80-plus 1/2 (mean 90.6, −40.6), 70-80 3/4 (73.4, +1.6), 60-70 6/14 (64.4, −21.6), under-60 2/4 (58.6, −8.6). BOTH 80-plus rows are Chase Burns in the SAME 3.0-inning start and they split — `o9.5 outs` at 95.7 lost on exactly 9 outs, `o3.5 K` at 85.4 won with 5 K. Two rows, one outing.** 🔴🔴 **THE TICKET-POOL CONCENTRATION DEFECT IS BACK AT ITS WORST END: Chase Burns in 29 of 32 tickets (8 of 8 pairs, 21 of 24 parlays) on two winning rungs; Hayden Wesneski in 17 of 32 including SEVEN of the eight three-leg tickets, losing on 2 K. PAIRS therefore read 7/8 and THREE-LEG PARLAYS 0/8 on the same board — two opposite "records" out of two starts. ⛔ And the 9/13 "driven by board size" hypothesis is CONTRADICTED: this was ALSO a fifteen-game slate. It stays untested, now with a counterexample attached.** ✅ **THE CONTROL: five routes, zero domain violations — the 9/13 result file recomputed in full; the entire stored pitcher corpus (17,272 rows / 520 players / `n_failed: 0`) clean; enumerated full-season sums 16/16 EXACT; the LIVE `statsapi` game log 2/2 EXACT and agreeing THREE ways; the runner's `record.json` reproducing `w:28 n:47 voids:3` and `by_kind.pitcher: 246/492` exactly. No `stats=season` TOTAL requested or believed.** ✅ **AND THE LEDGER DIVERGENCE DID NOT RECUR — `created_at` for the ledger (`2026-09-14T08:01:04Z`) and this page (`2026-09-13T11:53:24Z`) are one grading run apart, which is the standing check's pass condition.** ⛔ **NOT ONE EXISTING BUCKET COUNT, RUNG COUNT, BRIER VALUE, GRADED ROW OR SPECIFICATION ON THIS PAGE WAS ALTERED — the 2026-09-14 block is a PURE INSERTION immediately above this Changelog, plus ONE struck-in-place Progress line.** ⚠️ **Method:** `project_read` → the returned content taken VERBATIM (file result copied, never retyped) → programmatic patch with TWO anchors each ASSERTED to occur EXACTLY ONCE → `collections.Counter` line-loss check → `project_info` `created_at` re-read immediately before upload → upload with `local_path`, per ledger rule 43.

- **Sep 13 2026, 7:30am scheduled run — the twenty-first machine slate (2026-09-12): an eleventh card written exactly once and the FIRST SINCE 8/29 TO LOSE A GAME, a board that inverted yesterday's side split without changing the sign of the error, the mildest ticket-pool concentration this table has recorded, rule 51's log gaining two rows that clear nothing, and a dated correction to the 9/12 block's statement of its own convention.** ✅ **TABLE M graded 10/25 (40.0%) with ZERO ungraded — mean `model` 65.6, `raw` 66.0, `blend` 65.8, `carried` 58.3 against an actual 40.0%; Brier `carried` .2918 · `model` .3035 · `blend` .3218 · `raw` .3482; gap −25.8.** 🔴🔴 **THE PROVENANCE IS THE FINDING: `9bd1688` at `2026-09-12T17:19:36Z` carries `skipped."already started": 1` and a pre-slate margin of SEVENTEEN MINUTES. COL @ DET first pitch `17:10:00Z` was nine minutes into play when the card was written; `verify_card` had been failing since 13:49Z on a leg priced at EXACTLY −700 (rule 187 fixed the builder and not the verifier; drop 44B cleared it). The outage cost one whole game and all but seventeen minutes of margin — the previous narrowest on record is 9/10's 2h 06m.** ✅ **PIT @ CHC (18:20Z) and CIN @ MIL (23:10Z) were still ahead of the card and are ranking absences, not drops — identified from first-pitch times, not guessed.** ⛔ **T15 NOT restated for a TWENTY-FIRST consecutive run — no TABLE A play since 8/22, drought twenty-two days, and the machine population is not T15's denominator.** ⛔ **RULE 35 gained nothing again and deliberately: 119 rungs across 14 NAMED distinct starts, not merged. The merge stays 185 rungs / 25 starts, T11 25/40.** 🆕 **MATCHED CLASS vs HEAD-TO-HEAD, 9/12: class 12/24 — right on 8 of its 19 FORs and 4 of its 5 AGAINSTs — with ONE boundary row EXCLUDED AND NAMED (Tyler Glasnow `u7.5 K`, 17/34 = 50.0%, result W); head-to-head 3/10 with FIFTEEN no calls (12 at n=0 plus three split-cleared rows the convention does not reach), and the two instruments disagreed on 2 rows with the class right on both.** ⚠️🔴 **A DATED CORRECTION, CHECK 28: the 2026-09-12 block states its head-to-head convention as "AGAINST when none OR A MINORITY did," and its own 4/9-with-16-no-calls could not have been computed that way — re-deriving that slate under the ORIGINAL rule (majority FOR, none AGAINST, everything else NO CALL) reproduces it EXACTLY. ⛔ THE TALLY IS CORRECT AND IS NOT ALTERED; the sentence describing it is what drifted, and it is corrected in the new block rather than in place.** ✅ **CHECK 36 STAYS CLOSED for a second slate — `h2h_gap_days` on all 13 rows with a prior meeting, `h2h_rematch` on all 25.** 🔴 **THE RULE 51 LOG GAINS ROWS 24 AND 25 — Tyler Mahle vs PHI at SIX days, on two carded rows that went 1/2. The prior meeting produced THREE K, so NEITHER clears the ≥5 K conditional and neither speaks to the registered finding; descriptively the rematch produced three again. Nothing re-specified; the registered mean-K spec is still CLOSED-FAILED with the threshold version EXPLORATORY.** 🟡 **`carried` BETTER — the NINTH time in twenty-one slates: differed on 13 of 25 rows across 8 pitchers, Brier .2918 vs .3218 overall and .2778 vs .3355 on the differing set, which went 5/13 = 38.5% against a slate rate of 40.0% — a 1.5-point gap, so it won by the ordinary mechanism (simply lower, board 25.8 over). Running total 150 differing rows across twenty-one slates. Nothing adopted, rejected or re-specified.** ✅ 🆕 **THE TICKET-POOL CONCENTRATION DEFECT IS AT ITS MILDEST EVER — no leg in more than 13 of 32 tickets and no arm in more than 14, against ONE ARM IN ALL 32 on 9/7, 9/8 and 9/9 and 23 of 32 on 9/10 and 9/11. ⚠️ Reported as a property of a fifteen-game board, NOT as a repair: nothing in `card.py` changed that anyone has recorded, and "the defect is driven by board size" is testable and untested.** 🔴🔴 **AND THE FINDING THAT MATTERS MOST IS AGAIN NOT ON THIS PAGE: the 9/12 block's closing claim that "the ledger now carries the record" was FALSE — `claude/pick-ledger.md` still had no 9/10 AND no 9/11 record when this run started, so the 9/12 run's ledger write was lost as well as the 9/11 run's. Both slates were re-derived from scratch WITHOUT reading this page first and reproduced EVERY figure published here EXACTLY. ⛔ Nothing on this page needed correcting; the ledger now carries all three slates and the divergence is written up there.** ⚠️ **Also fixed: this page's `Progress:` footer had not been updated by the 9/10, 9/11 or 9/12 runs and still read the 9/8 state. STRUCK IN PLACE, not deleted; the live figure closes the new block and reconciles three ways.** ⛔ **NOT ONE EXISTING BUCKET COUNT, RUNG COUNT, BRIER VALUE, GRADED ROW OR SPECIFICATION ON THIS PAGE WAS ALTERED — the 2026-09-13 block is a PURE INSERTION immediately above this Changelog, plus ONE struck-in-place Progress line.** ⚠️ **Method:** `project_read` → the returned content taken VERBATIM (no retype) → programmatic patch with THREE anchors each ASSERTED to occur EXACTLY ONCE → `collections.Counter` line-loss check → `project_info` `created_at` re-read immediately before upload → upload with `local_path`, per ledger rule 43.

- **Sep 12 2026, 7:30am scheduled run — the twentieth machine slate (2026-09-11): a tenth consecutive card written exactly once, THE FIRST TABLE M CARD PRICED BY MODEL v5.0, pre-publish check 36 CLOSED on the card after nineteen consecutive reports, rule 51's instrument firing on its first live slate, and a `carried` column better again on five rows that settle nothing.** ✅ **TABLE M graded 12/25 (48.0%) with ZERO ungraded — mean `model` 61.7, `raw` 64.3, `blend` 63.0, `carried` 60.1 against an actual 48.0%; Brier `carried` .2437 · `model` .2485 · `blend` .2531 · `raw` .2682; gap −15.0.** ⚠️ **The whole Brier spread is .0245 at n=25 — LOG, DO NOT CONCLUDE.** 🔴 **A POPULATION CHANGE IS RECORDED BEFORE ANY RATE IS QUOTED: `picks/2026-09-11.json` is the first card carrying `MODEL_VERSION v5.0`; 8/23 through 9/10 are all v4.0, so every figure from here forward sits on a mixed-version population.** ⛔ **T15 NOT restated for a TWENTIETH consecutive run — no TABLE A play since 8/22, the drought is twenty-one days, and the machine population is not T15's denominator.** ⛔ **RULE 35 gained nothing again and deliberately: the 9/11 card carries alt ladders on 14 of 25 pitcher rows — 119 rungs across 13 NAMED distinct starts — and none of it is merged. The merge stays 185 rungs / 25 starts, T11 25/40.** 🆕 **MATCHED CLASS vs HEAD-TO-HEAD, 9/11: class 16/25 — right on 11 of its 19 FORs and 5 of its 6 AGAINSTs (`11 + 5 = 16` ✅, `19 + 6 = 25` ✅) — head-to-head 4/9 with SIXTEEN NO CALLS (`9 + 16 = 25` ✅), and the two instruments disagreed on 4 rows.** ✅🔴 **CHECK 36 IS CLOSED: `h2h_gap_days` and `h2h_rematch` are on the card, and FIVE rows sit inside the thirty-day window — Nola ×2 at 5 days, May and Springs at 6, Sale at 7. Those five carded rows went 1/5; all four arms CLEAR the ≥5 K conditional, the first slate on which every eligible row does, and on the exploratory 4+ K bar two of four cleared in the rematch. The machine-population log now holds TWENTY-THREE rows. n = 4 arms; nothing is re-specified.** 🟡 **`carried` differed on 5 of 25 rows across 4 pitchers and was BETTER by .0094 overall and .0470 on the differing set — the EIGHTH time in twenty slates — by the ordinary mechanism. Running total 137 differing rows across twenty slates. Nothing is adopted, rejected or re-specified.** ✅ **The control REVERSED yesterday's five failures — enumerated full-season sums 28/28 exact across both slates, the live `statsapi` game log 3/3 exact, zero domain violations — and it is reported as a reversal, not a clearance: every clean reading came from the ENUMERATED form and no `stats=season` total was believed.** ⚠️🔴 **TWO PROSE COUNTS IN THE 2026-09-11 BLOCK ABOVE DO NOT RECONCILE AGAINST THEIR OWN ROWS and are CORRECTED IN PLACE AS DATED NOTES, with no graded row, Brier value or bucket count altered: its matched-class split ("FOR on 8 and AGAINST on 5 … right on 1 of the 8 and 3 of the 5") reconciles to its correct 4/13 total under NEITHER axis — the all-starts convention it declares gives 9 FORs and 4 AGAINSTs, right on 1 of 9 and 3 of 4 — and "five of ten starters went seven innings" is FOUR.** 🔴🔴 **AND THE FINDING OF THE RUN IS NOT ON THIS PAGE: `claude/pick-ledger.md` had NO record of the 9/10 slate when this run started while this page carried the full block. The 9/10 slate was re-derived from scratch and reproduced every figure here EXACTLY, so nothing on this page needed correcting; the ledger now carries the record and the divergence is written up there.** ⛔ **NOT ONE EXISTING BUCKET COUNT, RUNG COUNT, BRIER VALUE, GRADED ROW OR SPECIFICATION ON THIS PAGE WAS ALTERED — the 9/11 block is a PURE INSERTION immediately above this Changelog, and the two corrections are APPENDED notes that strike nothing.**

- **Sep 11 2026, 7:30am scheduled run — the nineteenth machine slate (2026-09-10): a ninth consecutive card written exactly once, the NARROWEST pre-slate margin this table has recorded, a thirteen-row pitcher board that landed 45.1 points under itself, the first slate on which the class and the head-to-head disagreed on ZERO rows, `carried` better on a differing set of three, and a season-total control that fabricated twice and truncated twice in one run.** ✅ **TABLE M graded 2/13 (15.4%) with ZERO ungraded — mean `model` 63.2, `raw` 57.7, `blend` 60.4, `carried` 57.1 against an actual 15.4%; Brier `raw` .3096 · `carried` .3113 · `blend` .3271 · `model` .3597; gap −45.1, the worst this table has recorded by a factor of three.** 🔴 **STATED BEFORE IT IS EXPLAINED: the board was TWELVE-THIRTEENTHS UNDERS on a five-game night when five of ten starters went seven innings and four struck out eight or more. It is not evidence the model got worse and must not be averaged into a trend sentence.** ⛔ **T15 NOT restated for a NINETEENTH consecutive run — no TABLE A play has been carded since 8/22, the drought is twenty days, and the machine population is not T15's denominator.** ⛔ **RULE 35 gained nothing again and deliberately: the 9/10 card carries alt ladders on 7 of 13 pitcher rows — 57 rungs across 7 NAMED distinct starts — and none of it is merged. The merge stays 185 rungs / 25 starts, T11 25/40.** 🆕 **MATCHED CLASS vs HEAD-TO-HEAD, 9/10: class 4/13 — right on 1 of its 8 FORs and 3 of its 5 AGAINSTs (`1 + 3 = 4` ✅, `8 + 5 = 13` ✅) — head-to-head 0/3 with TEN NO CALLS (`3 + 10 = 13` ✅), and the two instruments disagreed on ZERO rows for the first time since the tally opened.** 🔴 **CHECK 36's DEFECT PRESENT FOR A NINETEENTH RUN: `days` appears ZERO times in the card — ⚠️ but the card PREDATES the 2026-09-11 fix (`d64540f`) that ledger rule 189 records as closing it, so the next run should check for a CLOSE rather than a twentieth report.** ✅ **ZERO rows are inside the thirty-day window (nearest 46 days, Gilbert vs TEX and deGrom vs SEA), so it could not have changed a line; the machine-population rule 51 log gains NO rows and stays at eighteen.** ✅ **All 13 head-to-head strings reproduce EXACTLY from the repo log under a STARTS (`gs == 1`) filter, re-confirming the `never faced` wording defect recorded on 9/10.** 🟡 **`carried` differed on 3 of 13 rows across 3 pitchers and was BETTER by .0158 overall and .0682 on the differing set — the SEVENTH time in nineteen slates — by the ordinary mechanism (it is simply lower, and the board sat 45 points over). Running total 132 differing rows across nineteen slates. Nothing is adopted, rejected or re-specified.** 🔴🔴 🆕 **THE FINDING OF THE RUN IS ABOUT THE CONTROL: the live `statsapi` route FAILED FIVE TIMES — two DOMAIN-VALID BUT WRONG season totals (Feltner `20 · 97.2 · 70` vs a true `22 · 111.2 · 83`; Gilbert `27 · 160.1 · 166` vs a true `29 · 172.0 · 187`), two SILENTLY TRUNCATED game logs missing the carded start (Martinez, deGrom), and one that enumerated 23 splits while stating 22. In its SUMMARISED form the season-total control would have FALSELY FAILED two correct lines; in its ENUMERATED form it was 9/9 exact. A fetched TOTAL is a summary — enumerate and sum, always.** ⛔ **NOT ONE EXISTING BUCKET COUNT, RUNG COUNT, BRIER VALUE, GRADED ROW OR SPECIFICATION ON THIS PAGE WAS ALTERED — the 9/10 block is a PURE INSERTION immediately above this Changelog.**

- **Sep 10 2026, 7:30am scheduled run — the eighteenth machine slate (2026-09-09): an eighth consecutive card written exactly once, the NARROWEST Brier spread between the four estimators this table has produced, the matched class's worst reading in eighteen slates, check 36's defect present but for the first time COSTLESS, a new WORDING defect in the head-to-head string, and a ticket surface killed by one start.** ✅ **TABLE M graded 13/25 (52.0%) with ZERO ungraded — mean `model` 65.4, `raw` 66.9, `blend` 66.1, `carried` 59.2 against an actual 52.0%; Brier `carried` .2896 · `blend` .2902 · `raw` .2937 · `model` .2939, a spread of 0.0043 that orders nothing at n=25; gap −14.1.** ⛔ **T15 NOT restated for an EIGHTEENTH consecutive run — no TABLE A play has been carded since 8/22 and the machine population is not T15's denominator; the drought is nineteen days.** ⛔ **RULE 35 gained nothing again and deliberately: the 9/9 card carries alt ladders on 11 of 25 pitcher rows — 77 rungs across 11 NAMED distinct starts — and none of it is merged, because T11's `n` is CARDED arms. The merge stays 185 rungs / 25 starts, T11 25/40.** 🆕 **MATCHED CLASS vs HEAD-TO-HEAD, 9/9: class 11/25 — its worst reading in eighteen slates — head-to-head 2/8 with SEVENTEEN NO CALLS (`8 + 17 = 25` ✅), and EVERY ONE of the eight head-to-head calls rests on a single prior meeting.** ✅ **FIVE flat disagreements, the class right on 3 and the head-to-head on 2 — and ALL FIVE ROWS WON, so the split is simply which instrument was bullish.** 🔴 **CHECK 36's DEFECT PRESENT FOR AN EIGHTEENTH RUN: `days` appears ZERO times in the card.** ✅ **But ZERO rows are inside the thirty-day window — the first such slate since the defect was found — so it could not have changed a line; the nearest prior START is Robert Stock vs MIA at 38 days. The machine-population rule 51 log therefore gains NO rows and stays at eighteen.** 🆕 🔴 **A NEW DEFECT, REPORTED NOT FIXED: `card.py` prints `never faced <TEAM>` where it computes `never STARTED against <TEAM>`. Lake Bachar's two rows print `never faced CWS` against a 2026-03-30 RELIEF appearance of 9 outs and 3 K on 42 pitches. The computation is right; the string overclaims, and it overclaims hardest on an opener line like his `o6.5 outs`.** ✅ **The h2h re-derivation doubles as a control and reproduces all 25 printed strings EXACTLY under the STARTS (`gs == 1`) filter.** 🟡 **`carried` differed on 12 of 25 rows across 8 pitchers and was BETTER by .0006 overall and .0012 on the differing set — the SIXTH time in eighteen slates — and the mechanism RAN BACKWARDS for the first time: the differing subset went 7/12 = 58.3%, better than the slate's 52.0%, and `carried` still won because the whole board sat 14.1 points over. Running total 129 differing rows across eighteen slates. The 'closer' tally on the same twelve rows reads blend 7, carried 5 — the opposite ordering, and neither is a verdict.** 🔴 **The ticket-pool concentration defect takes its EIGHTH form in eight slates and its hardest: Zac Gallen is a leg in ALL 8 pairs and ALL 24 parlays, on `o11.5 outs` (7 pairs + 24 parlays) and `o1.5 K` (1 pair), and BOTH rungs lost — 10 outs and 1 K in 3.1 IP. Where 9/8's two rungs at least split, these did not. 0/8 and 0/24 is ONE START reported thirty-two times.** ⚠️ **Re-reported, not fixed: the `in_band` / `PARLAY_BANDS` / `parlay_rule` three-way ceiling disagreement (it moves ONE ticket, the 2.143x, and cost nothing because every pair lost), and `picks/2026-09-09.json` still carrying `model_version: "v4.0"` nine days after v5.0 published.** ⛔ **NOT ONE EXISTING BUCKET COUNT, RUNG COUNT, BRIER VALUE, GRADED ROW OR SPECIFICATION ON THIS PAGE WAS ALTERED — the 9/9 block is a PURE INSERTION immediately above the Changelog.**

- **Sep 9 2026, 7:30am scheduled run — the seventeenth machine slate (2026-09-08): a seventh consecutive card written exactly once, the best-calibrated single band cell this table has ever produced sitting inside a board that missed by 13.7, `carried` worse for the twelfth time in seventeen slates, check 36's defect at THREE rows in the window for a third consecutive slate — and a ticket surface where one PITCHER is a leg in all 32 tickets on TWO rungs that settled opposite ways)** — 🤖 🆕 **A 9/8 TABLE M BLOCK WAS APPENDED. ⛔ NOTHING ABOVE THE TABLE M SECTION WAS TOUCHED.** ✅ **`picks/2026-09-08.json` is 50 plays — 25 pitcher + 25 hitter — across 14 games, written EXACTLY ONCE (`8c3c75d`, `2026-09-08T14:11:02Z`, `generated_at 14:10:48Z`), pre-slate by ~8.5 hours, zero games dropped; the missing 15th game (TEX @ SEA) was in the props pull at `n_events: 15` and is an absence in a RANKING, not a dropped game.** ✅ **All 25 pitcher rows graded — 13/25 (52.0%) against a mean `blend` of 65.7, a gap of −13.7.** 🔴 **T15 NOT RESTATED for a SEVENTEENTH consecutive run — no TABLE A play has been carded since 8/22 and the drought is now eighteen days; the machine population is not T15's denominator and was not substituted into it.** ⚠️ **Brier on the machine population: `model` .2712 · `blend` .2924 · `carried` .2937 · `raw` .3246 — the first slate in four where `model` wins outright and `carried` does not, by the same over-confidence mechanism running in the other direction.** 🔴 **RULE 35 gained NOTHING again and deliberately: the 9/8 card carries 108 rungs across 14 NAMED distinct starts and they are NOT merged, because T11's `n` is CARDED arms. The merged accumulator stays at 185 rungs / 25 distinct starts; T11 progress 25/40, unchanged.** 🆕 **MATCHED CLASS vs HEAD-TO-HEAD, 9/8, in its OWN tally and NOT added to rule 50's 4/9: class 16/25, head-to-head 3/4, with 21 NO CALLS (19 `n=0` plus TWO `cleared 1/2` splits) — the largest no-call group this table has carried, and `4 + 21 = 25` ✅. ONLY ONE row had the two instruments disagree (Drew Anderson u15.5 outs: class 61.1% FOR, h2h 0/1 AGAINST, result L) and the head-to-head was right — the fewest disagreements ever recorded here, and n=1 either way.** 🔴 **PRE-PUBLISH CHECK 36's DEFECT IS PRESENT FOR A SEVENTEENTH CONSECUTIVE RUN — the substring `days` appears ZERO times in the card — and THREE rows sit inside rule 51's 30-day window, all three at SIX days off the SAME prior date (2026-09-02), the second consecutive slate with that shape. The nearest row outside is 37 days, so no boundary case.** 🔴 **THE MACHINE-POPULATION RULE 51 LOG GAINS ROWS 16, 17 AND 18 — Drew Anderson (MIN), Jacob Misiorowski (CHC) and Dean Kremer (DET) — and FOR THE FIRST TIME ALL THREE CLEAR THE ≥5 K CONDITIONAL, each having struck out exactly 5 in the prior meeting. Descriptively two of three cleared 4+ K on the rematch; ALL THREE CARDED ROWS LOST. n=3, nothing eligible is folded in, nothing re-specified, and the registered mean-K spec is still CLOSED-FAILED with the threshold version EXPLORATORY.** 🟡 **`carried` WORSE — the twelfth time in seventeen slates: it differed on 8 of 25 rows across 6 pitchers, Brier .2937 vs `blend`'s .2924 overall and .3230 vs .3188 on the differing rows. The differing set went 5/8 = 62.5% against a slate rate of 52.0%, so the pessimistic column was punished for a subset that beat the board — the exact converse of 9/7. Still in NO denominator.** ✅ 🆕 **THE 60–70 BAND CELL LANDED DEAD ON ITS OWN NUMBER — 9/14 = 64.3% against a mean claim of 64.31 — the closest any band has come on this table, and it is reported as a COINCIDENCE at n=14, not as calibration; the two most confident bands missed by 84.5 and 55.2 points on n=1 and n=5.** 🔴🔴 **THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS SEVENTH FORM IN SEVEN SLATES AND THIS ONE IS NEW: Hayden Wesneski is a leg in ALL 8 pairs and ALL 24 parlays, on TWO rungs — `o3.5 K` on 7 pairs and 20 parlays, `o2.5 K` on 1 pair and 4 parlays, no ticket carrying both. He struck out THREE, so `o2.5` WON and `o3.5` LOST from the same start; the five tickets holding the winning rung lost on other legs anyway. PAIRS 0/8 and PARLAYS 0/24 is ONE START reported thirty-two times, not thirty-two judgements.** ✅ **All 32 tickets DISTINCT — the duplicate defect did not recur, ninth consecutive slate.** 🔴 **BAND-CEILING CONTRADICTION live on TWO tickets (2.140x, 2.171x): by the `in_band` flag pairs are 0/5 inside · 0/3 above, by the same file's prose 0/7 inside · 0/1 above; it cost nothing only because every pair lost.** ⚠️ **Re-reported and unchanged: `model_version: "v4.0"` eight days after v5.0 published; `price > -700` still excluding exactly −700; `collect.yml`'s header still saying "the count is 16" against FORTY enumerated cron entries, one more than yesterday.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY OR CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION plus ONE replaced line, the Progress line, whose prior value is preserved verbatim at the head of the new block.** ⚠️ **Merged, not rewritten: `project_read` → local file taken VERBATIM from the tool result → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE → `collections.Counter` line-loss check → `project_info` `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.**

- **Sep 8 2026, 7:30am scheduled run — the sixteenth machine slate (2026-09-07): a sixth consecutive card written exactly once, the first card since 8/24 that is not 25 pitcher + 25 hitter, `carried` better a fifth time in sixteen slates but by a weaker mechanism than usual, check 36's defect on its tightest window yet, and a ticket surface in which ONE ARM is a leg in ALL 8 PAIRS and ALL 24 PARLAYS** — ⛔ **NO OPEN TEST, PASS CRITERION, SPECIFICATION, MEASURED RESULT, CLOSED VERDICT OR EARLIER SLATE BLOCK WAS ALTERED, REORDERED OR DROPPED. This write is a PURE INSERTION of the 2026-09-08 block plus this entry, and a one-line update to the Progress footer.** ✅ **`picks/2026-09-07.json` is 50 plays — **22 pitcher + 28 hitter**, `50 = 22 + 28` — across 11 games, ALL 22 pitcher rows graded, ZERO games dropped against an 11-game slate.** ⚠️ 🆕 **The 22/28 split is the first departure from 25/25 since 8/24 and is NAMED rather than absorbed: `board_rule` records 31 pitcher and 1,599 hitter rows priced with 50 shown, so it is the ranking on a small board, not truncation.** 🔴 **T15 NOT restated — SIXTEENTH consecutive run; no TABLE A play has been carded since 8/22 and the drought is seventeen days. The machine population is not T15's denominator.** 🔴 **RULE 35 gained nothing again: the merged pure-model accumulator stays 185 rungs / 25 distinct starts and T11 stays 25/40. The 9/7 card's 96 rungs across 13 NAMED distinct starts are logged and NOT merged.** ⚠️ **Matched class 13/22 · head-to-head 5/10 · NO CALL 12 (`10 + 12 = 22`), the no-calls being 11 `n=0` rows plus one 1-of-2 split (Grant Holmes vs PHI) that the published convention does not reach. FOUR rows disagreed outright and split TWO–TWO.** 🔴 **CHECK 36's DEFECT IS PRESENT FOR A SIXTEENTH CONSECUTIVE RUN — the substring `days` appears ZERO times in the file — and the board carried THREE rows inside the 30-day window whose prior meetings ALL fall on the SAME DATE, 2026-09-01, six days out; the gap distribution is starkly bimodal at three-at-6-days and four-at-136-days-or-more.** ✅ **The re-derivation doubles as a control: all 22 head-to-head strings reproduce EXACTLY from the stored log under a STARTS (`gs == 1`) filter.** 🔴 **The machine-population rule-51 log gains rows 13, 14 and 15 (Melton/MIN, Boyd/MIL, Gasser/CHC) and NOT ONE clears the ≥5 K conditional, so none speaks to the registered finding; descriptively two of the three rematches produced MORE strikeouts, not fewer.** ✅ **`carried` differed on 8 of 22 rows across 5 pitchers and was BETTER — Brier .3062 vs .3230 overall and .2574 vs .3035 on the differing rows — but the differing set went 3/8 = 37.5% against a slate rate of 40.9%, a THREE-point gap against twenty on 9/6, so it won because the WHOLE board was 21.6 points over-confident rather than because the subset was worse. Running total 109 differing rows across sixteen slates.** 🔴🔴 **THE TICKET-POOL CONCENTRATION DEFECT REACHED ITS LIMIT CASE: `Chase Burns o11.5 outs` — the card's most confident row at blend 97.5, its only `80-plus` play — is a leg in 8 of 8 pairs and 24 of 24 parlays, went 3.0 IP for NINE outs, and is the ONLY losing leg in 6 of the 8 pairs. Pairs 0/8 and parlays 0/18 are ONE observation reported twenty-six times.** 🔴 **The band-ceiling contradiction is live on three tickets (2.123x, 2.142x, 2.186x) and cost nothing only because every pair lost.** ⚠️ **Re-reported and unchanged: `model_version: "v4.0"` seven days after v5.0 published, `price > -700` excluding exactly −700, and `collect.yml`'s header claiming 16 crons where 39 are enumerated. A headless run cannot test or push.** ⚠️ **Merged, not rewritten: `project_read` (returned as a FILE — `cp`'d, no retype) → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE → `collections.Counter` line-loss check (ONE line replaced, the Progress footer) → `project_info`'s `created_at` for this path re-read immediately before upload and found UNMOVED → upload with `local_path`, per ledger rule 43.**

- **Sep 7 2026, 7:30am scheduled run — the fifteenth machine slate (2026-09-06): a fifth consecutive card written exactly once, the smallest gap since 9/3, `carried` better a fourth time in fifteen slates, check 36's defect again at THREE rows in the window, and a ticket surface whose entire result is one arm.** ✅ **TABLE M graded 15/25 (60.0%) with ZERO ungraded — mean `model` 66.5, `raw` 67.8, `blend` 67.1, `carried` 61.4 against an actual 60.0%; Brier `carried` .2214 · `raw` .2375 · `blend` .2458 · `model` .2627; gap −7.1, against −27.8 on 9/4 and −23.1 on 9/5.** ⛔ **T15 NOT restated for a FIFTEENTH consecutive run — no TABLE A play has been carded since 8/22 and the machine population is not T15's denominator; the drought is sixteen days.** ⛔ **RULE 35 gained nothing again and deliberately: the 9/6 card carries alt ladders on 15 of 25 pitcher rows — 111 rungs across 14 NAMED distinct starts — and none of it is merged, because T11's `n` is CARDED arms.** 🆕 **MATCHED CLASS vs HEAD-TO-HEAD, 9/6: class 10/25, head-to-head 4/7, with EIGHTEEN NO CALLS (17 at `n=0` plus one `cleared 1/2`) — `7 + 18 = 25` ✅. Seventeen `n=0` rows is the highest share this tally has recorded.** ✅ **ONE flat disagreement — Aaron Nola u17.5 outs, class 40.5% AGAINST versus a 1/1 head-to-head FOR — and the CLASS was right (21 outs, L).** 🔴 **CHECK 36's DEFECT PRESENT FOR A FIFTEENTH RUN: `days` appears ZERO times in the card, and THREE rows sit inside or on the 30-day window — Arrighetti 10 days, Dobnak 11 days and Leahy at EXACTLY 30, which is reported as a BOUNDARY CASE and deliberately not decided.** ✅ **The gap re-derivation doubles as a control: all 25 head-to-head strings reproduce EXACTLY from the stored log under a STARTS (`gs == 1`) filter.** 🔴 **The machine-population rule 51 log gains rows 10, 11 and 12 (Arrighetti, Dobnak, Leahy); two CLEAR the ≥5 K conditional and they point opposite ways on the registered 4+ K threshold. Nothing promoted, nothing folded in.** 🟡 **`carried` differed on 10 of 25 rows across 8 pitchers and was BETTER — .2214 against .2458 overall, .2549 against .3160 on the differing set — and the mechanism is the same for the fifteenth time: it is always LOWER, and the differing set went 4/10 = 40.0% against a SLATE rate of 60.0%. Running total 101 differing rows across fifteen slates.** 🔴 **The ticket-pool concentration defect takes its fifth form in five slates: Justin Wrobleski o13.5 outs is a leg in 4 of 8 pairs, 17 of 24 parlays and ALL EIGHT four-mans, and he is the ONLY losing leg in any pair on the board.** 🔴 **The band-ceiling contradiction bit again and this time it moves both cuts' denominators: INSIDE 2/3 · ABOVE 2/5 by `in_band`, INSIDE 2/4 · ABOVE 2/4 by the same file's prose. Open since 8/26; an interactive session must pick one ceiling.** ⛔ **NOT ONE EXISTING BUCKET COUNT, RUNG COUNT, BRIER VALUE, GRADED ROW OR SPECIFICATION ON THIS PAGE WAS ALTERED — the 9/6 block is a PURE INSERTION immediately above the Changelog.**

- **Sep 6 2026, 7:30am scheduled run — the fourteenth machine slate (2026-09-05): a fourth consecutive card written exactly once, `carried` better a third time in fourteen slates, check 36's defect on its worst board yet, and a ticket surface that went 0-for-everything off two legs.** ✅ **TABLE M graded 11/25 with ZERO ungraded — mean `model` 65.2, `raw` 69.0, `blend` 67.1, `carried` 61.9 against an actual 44.0%; Brier `carried` .2875 · `model` .3031 · `blend` .3043 · `raw` .3116.** ⛔ **T15 NOT restated for a FOURTEENTH consecutive run — no TABLE A play has been carded since 8/22 and the machine population is not T15's denominator; the drought is fifteen days.** ⛔ **RULE 35 gained nothing again: the merged accumulator stays at 185 rungs / 25 distinct starts and T11 stays 25/40. The 9/5 card's 123 rungs across 14 DISTINCT NAMED STARTS are recorded with each start's actual K and NOT merged.** ⚠️ **Matched class 9/25 — its worst reading yet — head-to-head 4/15, ten n=0 NO CALLs (`15 + 10 = 25` ✅); three rows disagreed and the class took two.** ✅ **For the first time since 8/30 the `cleared 1/2` case did not arise at all.** 🔴 **CHECK 36's DEFECT IS THERE FOR A FOURTEENTH CONSECUTIVE RUN — `days` appears ZERO times in the card — and the board carried THREE rows inside rule 51's thirty-day window (Scherzer 11 days, Messick 23, Liberatore 28), more than any slate before it.** ✅ **All 25 printed head-to-head strings reproduce EXACTLY from the stored log under a STARTS filter.** 🔴 **The machine-population rule-51 log gains rows 7, 8 and 9, and row 8 (Messick) is the FIRST to CLEAR the registered ≥5 K conditional — and it points AGAINST the haircut: he took 12 K in the rematch. LOG, DO NOT CONCLUDE.** ✅ **`carried` differed on 9 of 25 rows across 7 pitchers and was BETTER (.2875 vs .3043 overall, .2752 vs .3220 on the differing set) — the third time in fourteen slates, by the same mechanism: it is always the lower number and the board came in low. Running total 91 differing rows over fourteen slates.** 🔴 **THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS FOURTH FORM IN FOUR SLATES AND ITS PUREST: Seth Lugo is a leg in ALL EIGHT pairs and 19 of 24 parlays, and he is on NO ROW OF THE 50-PLAY CARD.** 🔴 **The `in_band` / `PARLAY_BANDS` / `parlay_rule` ceiling contradiction BIT for the first time (pairs at 2.157x and 2.115x), making the printed split reader-dependent. REPORTED, NOT FIXED.** ⚠️ **`model_version` still `v4.0` five days after v5.0.** ✅ 🆕 **`card.py`'s `calibration_warning` no longer quotes the stale −25.9 / −18.0 figures — that defect is CLOSED.** ⛔ **NO EXISTING BUCKET, TALLY, SPECIFICATION OR GRADED ROW WAS ALTERED. Graded W/L verdict tokens in this doc: 6 before, 9 after — the three added are the Result column of the matched-class-vs-head-to-head DISAGREEMENT table, which re-cites three TABLE M rows already graded in the ledger and opens no denominator here.** ⚠️ **Method: `project_read` → verbatim local copy → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check → fresh `project_read` and `created_at` compared immediately before upload → upload with `local_path`.**

- **Sep 5 2026, 7:30am scheduled run — the thirteenth machine slate (2026-09-04), the worst-calibrated machine board on record, a named starter who pitched in RELIEF, and check 36's defect biting harder than it ever has.** ✅ **T15 NOT RESTATED for a THIRTEENTH consecutive run — no TABLE A play has been carded since 8/22 and the drought is now FOURTEEN DAYS, so the carded denominator stands at 31/100 with the 50/50 untouched.** ⚠️ **The machine slate's own figures are recorded and NOT folded in: mean `model` 67.7, `raw` 71.3, `blend` 69.5 against an actual 41.7% over 24 graded rows, Brier `carried` .2717 · `model` .2968 · `blend` .3158 · `raw` .3447 — MODEL beats BLEND for a fifth consecutive slate on the MACHINE population, which is NOT T15's denominator.** ⚠️ **On a board this over-confident the best Brier belongs to whichever estimator is lowest, so it is weak evidence about ordering and none about level.** 🔴 **ONE PITCHER ROW IS UNGRADED AND IS IN NO ACCUMULATOR HERE: Kumar Rocker o3.5 K — he pitched in the carded game and WAS NOT THE STARTER. Every tally in the new block has a denominator of 24 and says so.** ✅ **RULE 35 gained nothing again, deliberately: the merged pure-model accumulator stays at 185 rungs / 25 distinct starts and T11 stays 25/40. The 9/4 board's 92 rungs across 12 NAMED starts are listed but NOT merged, because T11's `n` is CARDED arms.** 🆕 **MATCHED CLASS vs HEAD-TO-HEAD, its own tally and never added to rule 50's 4/9: class 10/24 — its worst reading in thirteen slates — head-to-head 2/6, NO CALL at n=0 on 15 rows, and THREE rows the published convention does not reach (`cleared 1/2`, a fifth recurrence).** **ONE row disagreed outright and the head-to-head won it (Cristopher Sánchez u18.5 outs, class 46.2% AGAINST vs h2h 1/1 FOR, W).** 🔴🔴 **CHECK 36's DEFECT IS PRESENT FOR A THIRTEENTH CONSECUTIVE RUN AND HAS NEVER BITTEN HARDER: the substring `days` appears ZERO times in the card, and the board carried a SIX-DAY REMATCH — Erick Fedde vs Minnesota, whose prior start was 2026-08-29 — plus Keider Montero vs Cleveland at 22 days.** ⛔ **Both are inside rule 51's thirty-day window and the card said nothing about either.** ✅ **The h2h re-derivation doubles as a control and reproduces every printed string, 18/18 distinct (pitcher, opponent) pairs, under the STARTS (`gs == 1`) filter.** 🔴 **THE MACHINE-POPULATION RULE 51 LOG GAINS ITS FIFTH AND SIXTH ROWS (Fedde, Montero), with the disqualifier stated BEFORE the outcomes: NEITHER first meeting clears the registered ≥5 K conditional (4 K and 0 K), and the registered mean-K specification FAILED at t=−1.78 — the threshold version is EXPLORATORY, owed test T18.** ⛔ **Log, do not conclude; the hand-carded rule-51 table is untouched at 2 clean / 1 confounded.** 🟡 **THE `carried` SHADOW WAS BETTER — only the second time in thirteen slates: it differed on 8 of 24 rows across 6 pitchers, Brier .2717 vs blend's .3158 overall and .2619 vs .3943 on the differing rows.** ⚠️ 🔴 **SAME MECHANISM FOR THE THIRTEENTH TIME: 7 of the 8 differing rows LOST and `carried` is always the LOWER number, so it wins for pessimism on a bad subset exactly as it lost on 9/3 for pessimism on a good one. Thirteen slates of the same arithmetic is one piece of evidence sampled thirteen times.** **Running differing-row count 82** *(`3+2+8+8+0+9+2+7+8+9+10+8+8 = 82` ✅, counted against the thirteen enumerated slate figures)*. 🔴🔴 **THE TICKET-POOL CONCENTRATION DEFECT TAKES ITS THIRD FORM IN THREE SLATES AND THAT SETTLES THE ARGUMENT: 9/2's 0/24 was one LOSING leg reported twenty-four times, 9/3's 14/24 one WINNING leg reported twenty-four times, and 9/4's 1/23 one SCRATCHED leg (Rocker, in 18 of 24 parlays and 2 of 8 pairs) reported eighteen times.** ⛔ **A pool that can be destroyed, carried or voided wholesale by one row is not twenty-four observations, and its aggregate must never be quoted as a rate.** ⚠️ **Re-reported, not fixed: the `in_band` / `PARLAY_BANDS` / `parlay_rule` three-way ceiling disagreement (it did NOT bite — the only above-band pair is 2.308x, above on both readings), and 🆕 `picks/2026-09-04.json` still carrying `model_version: "v4.0"` four days after v5.0 published.** ⛔ **NO EARLIER BLOCK, BUCKET TABLE, TALLY OR TEST SPECIFICATION WAS ALTERED; the new block is a PURE INSERTION ahead of the Changelog.** ⚠️ **Merged, not rewritten: `project_read` → the tool result written verbatim to a local file → programmatic patch with the anchor ASSERTED to occur EXACTLY ONCE → `collections.Counter` line-loss check (ZERO lines lost) → `project_info` `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.**

- **Sep 4 2026, 7:30am scheduled run — the twelfth machine slate (2026-09-03), the best-calibrated machine board on record, and check 36's defect present but costing nothing for the first time in five slates.** ✅ **THE 9/3 TABLE M BLOCK APPENDED AS A PURE INSERTION.** **25 pitcher rows, ALL 25 graded, 16/25 (64.0%) against a mean `blend` of 64.1 — a gap of −0.1, the smallest this board has recorded — with Brier `model` .2003 · `blend` .2170 · `raw` .2381 · `carried` .2409.** ⛔ **Four consecutive full boards now read −22.0, −0.3, −15.2 and −0.1: a sequence that ALTERNATES rather than converges, reported as a fraction and not as a trend.** 🔴 **T15 NOT RESTATED — TWELFTH CONSECUTIVE RUN, and the reason is still the specification: no TABLE A play has been carded since 8/22, the drought is thirteen days, and folding in 25 machine rows would take a pre-registered counter past its bar without a single carded play. It stands at 31 / 100, argmin w = 1.00, margin 0.0094 — margin leg cleared, `n` leg failed, THE 50/50 UNTOUCHED.** 🔴 **RULE 35 GAINED NOTHING, DELIBERATELY: the merged pure-model accumulator stays at 185 rungs / 25 distinct starts and T11 stays at 25 / 40. The 9/3 card's 115 alt rungs across 14 NAMED distinct starts are recorded and NOT merged — a machine shadow ladder must be pre-registered in `claude/owed-tests.md` first.** 📐 **`n` is DISTINCT STARTS (14), never the rung count; 15 carded ROWS carry a ladder because Skubal carries two.** 🆕 **MATCHED CLASS vs HEAD-TO-HEAD, 9/3: class 14/25, head-to-head 6/10, 13 NO CALL at n=0 and 2 NO CALL because the published convention does not reach `cleared 1/2` — `10 + 13 + 2 = 25` ✅.** **The `1/2` case recurs for a FOURTH time, on both Luis Castillo rows; recorded as NO CALL, the literal reading, and flagged for an interactive session rather than re-written mid-tally.** **FIVE rows where the two flatly disagreed, splitting THREE–TWO to the head-to-head — and stated honestly as really THREE independent calls, because both Bachar rows share one n=1 meeting and both Brown rows share another.** 🔴 **CHECK 36's DEFECT IS STILL THERE — TWELFTH CONSECUTIVE RUN, `days` appears ZERO times in `picks/2026-09-03.json`** — ✅ 🆕 **BUT FOR THE FIRST TIME IN FIVE SLATES IT COST NOTHING, AND THAT WAS MEASURED RATHER THAN ASSUMED: every prior meeting was re-derived under a STARTS (`gs == 1`) filter and the CLOSEST is 35 days (McClanahan vs Texas). No rematch is inside thirty, so the Junk/Gusto/Gore/Bradford+Lopez biting streak ENDS — the card says nothing today only because there was nothing to say.** ✅ **The re-derivation doubles as a control: all 25 head-to-head strings reproduce EXACTLY, again only under the STARTS filter, and Jack Perkins is the row that proves the filter matters (a relief appearance vs Seattle, no prior start, and the card correctly prints "never faced SEA").** 🔴 **THE MACHINE-POPULATION RULE 51 LOG GAINS NO ROW and stays at four — a 35-day near-miss is not an instance.** 🟡 **THE `carried` SHADOW WENT WORSE AGAIN, BY EXACTLY THE MECHANISM THAT MADE IT BETTER YESTERDAY: it differed on 8 of 25 rows across 5 pitchers, 7 of the 8 WON, and `carried` is always the LOWER number — Brier worse by .0239 over all 25 and by .0747 over the 8 that differ.** ➡️ **Running as a sum of enumerated tallies and NOT as a finding: 74 differing rows over twelve slates (3, 2, 8, 8, 0, 9, 2, 7, 8, 9, 10, 8) with verdicts WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE, WORSE, WORSE, WORSE, WORSE, BETTER, WORSE. Twelve slates, nine verdicts, every one explained by whether that night's T22-flagged rows happened to win.** 🔴 **THE TICKET-POOL CONCENTRATION DEFECT RECURS WITH THE SIGN FLIPPED, AND THAT IS THE STRONGEST FORM OF THE ARGUMENT: 6 of 8 pairs and ALL 24 parlays carry Lake Bachar o5.5 outs, who cleared, so 14/24 is one winning leg reported twenty-four times exactly as 9/2's 0/24 was one losing leg reported twenty-four times.** ⚠️ **A defect named only on losing nights becomes an excuse.** ⛔ **REPORTED, NOT FIXED.** ⚠️ **The `in_band` / `PARLAY_BANDS` / `parlay_rule` ceiling disagreement bit on consecutive slates (pair 6 at 2.143x); the duplicate-ticket defect did not bite for a third slate, which on 9/1's evidence is it not biting rather than it being fixed.** ✅ 🆕 **AND ONE DEFECT THIS PAGE HAS RE-REPORTED SINCE 8/24 IS GONE: `card.py`'s `calibration_warning` no longer hard-codes −25.9 / −18.0 — it calls `calibration_sentence()` and the 9/3 card carries computed machine-card band figures, correctly scoped.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY OR CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of one dated block plus this entry, and the ONLY line replaced is the superseded progress counter, which is kept in place under a SUPERSEDED banner.** ⚠️ **Merged, not rewritten: `project_read` → the returned local file copied VERBATIM, never retyped → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE → `collections.Counter` line-loss check → fresh `project_read` and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.**

- **Sep 3 2026, 7:30am scheduled run (the eleventh machine slate, the FIRST card ever written exactly once, `carried` BETTER for the first time in six slates, check 36's defect biting on FOUR consecutive slates and on TWO arms at once, and a ticket pool that went 0-for-everything off ONE leg)** — 🤖 🆕 **A 9/2 BLOCK WAS ADDED TO THE TABLE M ACCUMULATOR SECTION for `picks/2026-09-02.json` — 50 plays, 25 PITCHER and 25 HITTER (`50 = 25 + 25` ✅), across 14 games.** ✅ 🆕 **AND FOR THE FIRST TIME IN THE PROJECT'S HISTORY THE FILE WAS WRITTEN EXACTLY ONCE: `git log` on a FULLY UNSHALLOWED clone names one commit, `90c2142` at `2026-09-02T14:09:54Z`, pre-slate, with no `"already started"` key.** ⛔ **The overwrite mechanism is unchanged and simply had no second run to fire; the interactive decision owed since 8/27 is owed a SIXTH time.** ⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE — no `blend`, no `band`, no model. They are graded into TABLE M-H in the ledger (16/22, three rows ungraded because Freddy Fermin, Tommy White and Ryan Waldschmidt did not play) and nothing here counts them; their gap is −10.3.** ⚠️ 🔴 **A CHECK-28 DEFECT IN THAT TABLE'S RUNNING GAP LINE WAS FOUND AND REPORTED RATHER THAN PROPAGATED — it has said "eight comparable gaps" for two runs while ENUMERATING SIX, because the 8/29 and 8/30 figures were never added. No figure was invented to close it.** 🔴 **T15 WAS NOT RESTATED, FOR THE ELEVENTH CONSECUTIVE RUN — no TABLE A play has been carded on 8/23 through 9/2: it stands at 31 / 100, argmin `w = 1.00`, margin 0.0094, MARGIN leg cleared and `n` leg failed, THE 50/50 UNTOUCHED.** ⚠️ **The drought is now TWELVE DAYS.** ⚠️ 🔴 **What the machine slate showed is recorded and NOT folded in, and it is the MIRROR of yesterday's: mean `model` 59.4, mean `raw` 67.1, mean `blend` 63.2, actual 48.0%, Brier model .2674 / blend .2885 / raw .3264 / carried .2679, a blend gap of −15.2 against yesterday's −0.3 from the same instrument on the same population.** ⛔ **Two consecutive slates, opposite verdicts, one day-tracking artifact. Not evidence about the blend weight.** 🔴 **RULE 35 GAINED NOTHING AND THAT IS DELIBERATE FOR AN ELEVENTH TIME — the merge stays at 185 rungs / 25 distinct starts, T11 progress 25 / 40 — even though this card carries 103 alt rungs across 19 distinct starts.** ✅ **All 19 arms are NAMED anyway so a future REGISTERED pass can deduplicate against them, and unlike 9/1 there is no exclusion to declare: every carded arm STARTED.** 🆕 **RULE 50 / RULE 51 OBSERVATIONS FROM THE 9/2 MACHINE CARD LOGGED IN THEIR OWN TALLY — matched class 15/24, head-to-head 7/11, with 11 n=0 NO-CALL rows and THREE further rows the published convention does not reach (`11 + 11 + 3 = 25` ✅).** 🔴 **THE `cleared 1/2` CASE recurs on its LARGEST set yet — three rows — and is treated identically rather than re-decided: recorded as NO CALL, the literal reading of the published rule. Reading `1/2` as FOR would make the tally 8/14 instead of 7/11.** ⛔ 🆕 **AND A SECOND CASE THE CONVENTION DOES NOT REACH WAS MET FOR THE FIRST TIME ON A GRADED MACHINE ROW: Dylan Cease o6.5 K carries `class n=0` — NO RATE AT ALL, not a boundary rate — so it is EXCLUDED and NAMED rather than counted as a boundary row.** ⛔ **The 8/25 boundary-row inconsistency is still unresolved, so the eleven class tallies are still NOT summable.** **FIVE rows had the class and the head-to-head flatly disagree and the CLASS took three.** ⛔ **The hand-carded rule-50 accumulator is UNTOUCHED at 4/9.** 🔴🔴 **THE PRE-PUBLISH CHECK 36 DEFECT IS RE-RECORDED AGAINST THE CODE FOR AN ELEVENTH CONSECUTIVE RUN — `days` appears ZERO times in `picks/2026-09-02.json` — 🆕 AND IT HAS NOW BITTEN ON FOUR CONSECUTIVE SLATES, THIS TIME ON TWO ARMS AT ONCE: CODY BRADFORD vs THE ATHLETICS AND JACOB LOPEZ vs TEXAS, BOTH SEVENTEEN DAYS, and the card said nothing on either.** 🆕 **THE MACHINE RULE-51 LOG GAINS ITS THIRD AND FOURTH ROWS AND THEY SPLIT: Bradford u4.5 K HIT off a WEAK 4-K first meeting (the predicted direction, but not the conditional the exploratory finding is about) and Lopez u5.5 K MISSED off a STRONG 6-K first meeting (which IS that conditional, and it went the wrong way).** ⛔ **NOT added to the hand-carded rule 51 accumulator, which stays at 2 clean / 1 confounded; both men's same-day OUTS rows are outside scope on the 8/22 Cease precedent.** ✅ **The card's own evidence column was re-derived rather than trusted: all 25 `h2h` strings reproduce EXACTLY, again only under a STARTS (`gs == 1`) filter.** 🟡 🔴 **THE `carried` SHADOW WAS BETTER FOR THE FIRST TIME IN SIX SLATES — Brier .2679 against .2885 over all 25 graded rows and .2846 against .3360 over the 10 rows that differ, all ten the T22 shuttled-starter flag across seven pitchers, the largest differing set this table has recorded.** ⚠️ **Same mechanism an eleventh time, which is exactly why the flip is not news: six of the ten differing rows LOST and `carried` is always the LOWER number, so it wins for pessimism on a bad subset as it lost five times running for pessimism on good ones.** ⛔ **Across eleven machine slates `carried` has differed on 66 rows (3 + 2 + 8 + 8 + 0 + 9 + 2 + 7 + 8 + 9 + 10) and stands WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE, WORSE, WORSE, WORSE, WORSE, BETTER.** 🔴🔴 🆕 **A TICKET-POOL DEFECT IS NAMED HERE BECAUSE NO ACCUMULATOR ON THIS PAGE WOULD HAVE CAUGHT IT: the 9/2 pairs went 0/8 and the parlays 0/24 — the first total wipeout on either surface — and BOTH have ONE cause, 7 of 8 pairs and 23 of 24 parlays carrying the same leg, Griffin Jax o11.5 outs, the board's highest-confidence pitcher row at blend 86.7, who recorded 8 OUTS.** ➡️ **`parlay_meta` builds the pool from the highest-confidence legs per PRICE BAND, so the top row enters nearly every ticket and the pool cannot diversify — 0/24 is ONE failed leg reported twenty-four times.** ⛔ **A SECOND, INDEPENDENT reason never to read printed tickets as independent observations, beyond the byte-identical-duplicate defect. REPORTED, NOT FIXED.** ✅ **The duplicate defect itself did NOT bite: 8 pairs and 24 parlays, all distinct.** ⚠️ 🔴 **And the `in_band` / `parlay_rule` contradiction open since 2026-08-26 BIT for the first time in three runs: two pairs at 2.107x and five two-leg parlays between 2.10x and 2.20x are ABOVE BAND by the flag and INSIDE BAND by the same file's prose.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY, REFUTATION, PROGRESS COUNTER OR EARLIER CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of one new section and this entry, plus a SUPERSEDED marker appended in place to the ten-slate TABLE M progress counter, which is kept rather than replaced. T15 stands at 31 carded plays / 100; T11 at 25 / 40 distinct starts; rule 50 at 4/9; rule 51 at 2 clean / 1 confounded; rule 53 at 2 of 6. The `collections.Counter` line-loss check reports exactly ONE line replaced — that progress counter — and nothing else lost. Graded rows 91 before, 106 after.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session's transcript JSONL with a JSON walker rather than retyped (two recorded occurrences, identical at 243,653 characters) → local file → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → `project_info` `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.**

- **Sep 2 2026, 7:30am scheduled run (the tenth machine slate, a third consecutive undamaged card, the best-calibrated machine slate on record, `carried` worse a FIFTH time running, a carded arm who PITCHED BUT DID NOT START, and the duplicate-ticket defect shown to be NON-DETERMINISTIC)** — 🤖 🆕 **A 9/1 BLOCK WAS ADDED TO THE TABLE M ACCUMULATOR SECTION for `picks/2026-09-01.json` — 50 plays, 25 PITCHER and 25 HITTER (`50 = 25 + 25` ✅), across 15 games.** ✅ **THE FILE WAS WRITTEN TWICE AND FOR THE THIRD CONSECUTIVE DAY THE OVERWRITE COST NOTHING — both writes pre-slate, no `"already started"` key.** ⛔ **A mechanism that happens not to bite has not been fixed; the interactive decision owed since 8/27 is owed a FIFTH time.** ⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE — no `blend`, no `band`, no model. They are graded into TABLE M-H in the ledger (17/21, four rows ungraded because Colt Keith, Zach McKinstry, Mike Yastrzemski and Leo Jimenez did not play) and nothing here counts them; their gap is −1.3, and eight comparable gaps from −26 to +5 are not a converging set.** 🔴 **T15 WAS NOT RESTATED, FOR THE TENTH CONSECUTIVE RUN — no TABLE A play has been carded on 8/23 through 9/1: it stands at 31 / 100, argmin `w = 1.00`, margin 0.0094, MARGIN leg cleared and `n` leg failed, THE 50/50 UNTOUCHED.** ⚠️ **The drought is now ELEVEN DAYS.** ⚠️ 🔴 **What the machine slate showed is recorded and NOT folded in, and it is the BEST-CALIBRATED machine slate on record — mean `model` 59.3, mean `raw` 65.2, mean `blend` 62.2, actual 62.5%, Brier model .2442 / blend .2260 / raw .2229 / carried .2353, a blend gap of −0.3 — which is exactly why it must not be folded in: the same instrument read −22 on 8/30 and +0.4 on 8/31's hitter half.** 🔴 **RULE 35 GAINED NOTHING AND THAT IS DELIBERATE FOR A TENTH TIME — the merge stays at 185 rungs / 25 distinct starts, T11 progress 25 / 40.** ✅ **All 17 STARTED arms are NAMED anyway so a future REGISTERED pass can deduplicate against them, and SPENCER ARRIGHETTI IS DELIBERATELY EXCLUDED FROM THAT LIST because he did not start.** 🆕 **RULE 50 / RULE 51 OBSERVATIONS FROM THE 9/1 MACHINE CARD LOGGED IN THEIR OWN TALLY — matched class 15/22 (TWO 50.0% boundary rows excluded on the 8/25 practice and NAMED: Jesús Luzardo o5.5 K and Randy Vásquez u3.5 K), head-to-head 7/11, with 13 n=0 NO-CALL rows (11 + 13 = 24 ✅).** ✅ **The `cleared 1/2` case the convention does not reach did NOT arise among the graded rows — the only such row is Arrighetti's, which is ungraded — so the convention is still owed a decision and simply had nothing to decide.** ⛔ **The 8/25 boundary-row inconsistency is still unresolved, so the ten class tallies are still NOT summable.** **FOUR rows had the class and the head-to-head flatly disagree and the CLASS took three.** ⛔ **The hand-carded rule-50 accumulator is UNTOUCHED at 4/9.** 🔴🔴 **THE PRE-PUBLISH CHECK 36 DEFECT IS RE-RECORDED AGAINST THE CODE FOR A TENTH CONSECUTIVE RUN — `days` appears ZERO times in `picks/2026-09-01.json` — 🆕 AND IT HAS NOW BITTEN ON THREE CONSECUTIVE SLATES: MACKENZIE GORE FACED THE ATHLETICS ON 2026-08-15 AND WAS CARDED AGAINST THEM AGAIN ON 9/1, SEVENTEEN DAYS, and the card said nothing.** ⚠️ **Jake Irvin at 33 days is three days outside a window nothing on the card measures.** 🆕 **THE MACHINE RULE-51 LOG GAINS ITS SECOND ROW — Gore u6.5 K, a 7+ K bar to lose, 17 days after a 5-K meeting, the UNDER cashed at 4 K.** ⚠️ **It is an UNDER, the MIRROR of every prior instance, and that is stated on the row.** ⛔ **NOT added to the hand-carded rule 51 accumulator, which stays at 2 clean / 1 confounded; his same-day OUTS row is outside scope on the 8/22 Cease precedent.** ✅ **The card's own evidence column was re-derived rather than trusted: all 12 `h2h` strings reproduce EXACTLY, again only under a STARTS (`gs == 1`) filter.** 🟡 🔴 **THE `carried` SHADOW WAS WORSE AGAIN, A FIFTH CONSECUTIVE TIME — Brier .2353 against .2260 over all 24 graded rows and .2450 against .2202 over the 9 rows that differ, all nine the T22 shuttled-starter flag across seven pitchers.** ⚠️ **Same mechanism a tenth time: six of the nine differing rows WON and `carried` is always the LOWER number.** ⛔ **Across ten machine slates `carried` has differed on 56 rows (3 + 2 + 8 + 8 + 0 + 9 + 2 + 7 + 8 + 9) and stands WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE, WORSE, WORSE, WORSE, WORSE.** 🔴🔴 🆕 **THE DUPLICATE-TICKET DEFECT IS NON-DETERMINISTIC: the 14:08 write emitted 5 distinct pairs of 8 and 17 distinct parlays of 24; the 18:41 write, from BYTE-IDENTICAL `picks[]`, emitted 8 distinct pairs and 24 distinct parlays.** ⛔ **The 8/30 `[hypothesis]` that a double-carded pitcher causes it is not sufficient either — the clean board has the same double-carded pitchers. Whatever the cause, it is not a function of the board alone. REPORTED, NOT FIXED.** ✅ 🆕 **AND ONE LONG-STANDING CODE DEFECT IS GONE: `card.py`'s `calibration_warning` no longer quotes hard-coded figures. `calibration_sentence()` builds the banner from `data/latest/record.json` and FAILS TO SILENCE rather than to a stale number; the struck −25.9 / −18.0 constants and the false "only the 70-80% band supports its own number" claim are off the surface.** ⚠️ **Still open and re-reported: the three-way `in_band` / `PARLAY_BANDS` / `parlay_rule` disagreement (open since 8/26) and `price > -700` excluding exactly −700. Neither bit this slate.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY, REFUTATION, PROGRESS COUNTER OR EARLIER CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of one new section and this entry, plus a SUPERSEDED marker appended in place to the nine-slate TABLE M progress counter, which is kept rather than replaced. T15 stands at 31 carded plays / 100; T11 at 25 / 40 distinct starts; rule 50 at 4/9; rule 51 at 2 clean / 1 confounded; rule 53 at 2 of 6. The `collections.Counter` line-loss check reports exactly ONE line replaced — that progress counter — and nothing else lost. Graded rows 78 before, 91 after.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session's transcript JSONL with a JSON walker rather than retyped (two recorded occurrences, identical at 221,306 characters) → local file → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → fresh `project_read` and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.**

- **Sep 1 2026, 7:30am scheduled run (the ninth machine slate, a second consecutive undamaged full card, check 36's defect biting on CONSECUTIVE slates, and an 8/30 `[hypothesis]` refuted rather than carried forward)** — 🤖 🆕 **AN 8/31 BLOCK WAS ADDED TO THE TABLE M ACCUMULATOR SECTION for `picks/2026-08-31.json` — 50 plays, 25 PITCHER and 25 HITTER (`50 = 25 + 25` ✅), across 12 games.** ✅ **THE FILE WAS WRITTEN TWICE AND FOR THE SECOND CONSECUTIVE DAY THE OVERWRITE COST NOTHING — both writes are pre-slate, identical on every axis, and `coverage_detail.skipped` carries no `"already started"` key.** ⛔ **A mechanism that happens not to bite has not been fixed; the interactive decision owed since 8/27 is owed a FOURTH time.** ⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE — no `blend`, no `band`, no model. They are graded into TABLE M-H in the ledger (20/23, two rows ungraded because Drew Cavanaugh and Drew Romo did not play) and nothing here counts them; their gap is +5.1, the FIRST POSITIVE gap that table has recorded on a comparable board, and seven scattered gaps from −26 to +5 are not a converging set.** 🔴 **T15 WAS NOT RESTATED, FOR THE NINTH CONSECUTIVE RUN — no TABLE A play has been carded on 8/23 through 8/31, so the CARDED denominator has not moved for nine slates: it stands at 31 / 100, argmin `w = 1.00`, margin 0.0094, MARGIN leg cleared and `n` leg failed, THE 50/50 UNTOUCHED.** ⚠️ **The drought is now TEN DAYS since the last hand-built card.** ⚠️ 🔴 **What the machine slate showed is recorded and NOT folded in, and it points the OPPOSITE way to yesterday's: mean `model` 59.4, mean `raw` 67.8, mean `blend` 63.6, actual 56.0, Brier model .2631 / blend .2491 / raw .2482 — RAW "wins" today for the mirror of the reason MODEL won on 8/30, because it was the HIGHER estimate on a slate that went 14/25 where model was the LOWER estimate on one that went 11/25.** ⛔ **Two consecutive slates, opposite winners, one day-tracking artifact. Not evidence about the blend weight.** 🔴 **RULE 35 GAINED NOTHING AND THAT IS DELIBERATE FOR A NINTH TIME — the merge stays at 185 rungs / 25 distinct starts, T11 progress 25 / 40, even though this card carries 150 alt rungs across 12 distinct starts.** ✅ **All 16 carded starts are NAMED anyway so a future REGISTERED pass can deduplicate against them, and naming is not merging.** 🆕 **RULE 50 / RULE 51 OBSERVATIONS FROM THE 8/31 MACHINE CARD LOGGED IN THEIR OWN TALLY — matched class 13/24 (ONE 50.0% boundary row excluded on the 8/25 practice and NAMED: Jacob deGrom u6.5 K), head-to-head 4/7, with 16 n=0 NO-CALL rows and ONE further row the published convention does not reach (7 + 16 + 1 + 1 = 25 ✅).** 🔴 **THAT `cleared 1/2` CASE — first met on 8/30 — RECURS (Taj Bradley vs DET) and is treated IDENTICALLY rather than re-decided: recorded as NO CALL, the literal reading of the published rule.** ⛔ **A grading run does not write a new convention mid-tally, and it does not write one on the second sighting either.** ⛔ **The 8/25 boundary-row inconsistency is still unresolved, so the nine class tallies are still NOT summable and are still reported separately.** **ONE row had the class and the head-to-head flatly disagree — Brady Singer o4.5 K vs SD, class 35/79 (44.3%) AGAINST against a 1/1 head-to-head FOR, result W, H2H right — and its head-to-head is a single start.** ⛔ **The hand-carded rule-50 accumulator is UNTOUCHED at 4/9.** 🔴🔴 **THE PRE-PUBLISH CHECK 36 DEFECT IS RE-RECORDED AGAINST THE CODE FOR A NINTH CONSECUTIVE RUN — `card.py` prints the head-to-head on every row and NEVER prints rule 51's GAP IN DAYS, verified mechanically (`days` appears ZERO times in `picks/2026-08-31.json`) — 🆕 AND IT HAS NOW BITTEN ON CONSECUTIVE SLATES.** **The gap was computed here for all SIX arms carrying a prior meeting: five are 65–83 days out, and RYAN GUSTO STARTED AGAINST WASHINGTON ON 2026-08-21 AND WAS CARDED AGAINST THEM AGAIN ON 8/31 — TEN DAYS, well inside rule 51's window — and the card said nothing.** ⛔ **THE MACHINE RULE-51 LOG GAINS NO GRADEABLE ROW, AND THE REASON IS SCOPE: his only carded row is an OUTS row, and outs are outside rule 51's scope on the 8/22 Cease precedent. The instance is NAMED and is in no tally; the log stays at its single Janson Junk row and the hand-carded accumulator stays at 2 clean / 1 confounded.** ✅ **The re-derivation doubles as a control: every head-to-head string the card printed reproduces exactly, 8/8 — once the filter is applied to STARTS (`gs == 1`) rather than to appearances.** ⚠️ 🔴 **THAT QUALIFIER ALMOST PRODUCED A FALSE FINDING and is recorded as one: an appearance-based check reads Gusto's `1 start(s) vs WSH` as a MISMATCH against two Washington rows, the second of which is a RELIEF appearance. The card counts starts and the card is right; the check was wrong.** ➡️ **A control that disagrees with the thing it is checking is a claim about the CONTROL until the disagreement is enumerated.** 🟡 🔴 **THE `carried` SHADOW WAS WORSE AGAIN, A FOURTH CONSECUTIVE TIME — Brier .2550 against .2491 over all 25 rows and .2434 against .2250 over the 8 rows that differ, all eight the T22 shuttled-starter flag across five pitchers.** ⚠️ **Same mechanism a ninth time: five of the eight differing rows WON and `carried` is always the LOWER number.** ⛔ **T22 is neither adopted nor rejected. Across nine machine slates `carried` has differed on 47 rows (3 + 2 + 8 + 8 + 0 + 9 + 2 + 7 + 8) and stands WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE, WORSE, WORSE, WORSE.** 🔴 🆕 **THE DUPLICATE-TICKET DEFECT RECURS AND THE 8/30 `[hypothesis]` IS REFUTED RATHER THAN CARRIED FORWARD: two of eight pairs and two parlay tickets are byte-identical duplicates again, but TODAY'S DUPLICATES CARRY NO LOGAN GILBERT LEG AT ALL — the repeated leg is Aaron Nola's.** ✅ **What survives is the SHAPE and not the name: on both days the repeated leg belongs to a pitcher carded on TWO rows.** ⛔ **STILL A `[hypothesis]`, REPORTED AND NOT FIXED, and any accumulator that counts printed tickets would double-weight one.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY, REFUTATION, PROGRESS COUNTER OR EARLIER CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of one new section and this entry, plus a SUPERSEDED marker appended in place to the eight-slate TABLE M progress counter, which is kept rather than replaced. T15 stands at 31 carded plays / 100; T11 at 25 / 40 distinct starts; rule 50 at 4/9; rule 51 at 2 clean / 1 confounded; rule 53 at 2 of 6. The `collections.Counter` line-loss check reports exactly ONE line replaced — that progress counter — and nothing else lost.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session's transcript JSONL with a JSON walker rather than retyped (two recorded occurrences, compared and byte-identical at 205,878 bytes) → local file → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → fresh `project_read` and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **Three docs touched this run — `claude/pick-ledger.md`, this one and `claude/mlb-opponent-database.md`.**

- **Aug 31 2026, 7:30am scheduled run (the eighth machine slate, the first undamaged full card in four days, check 36's defect biting for the first time, and two card surfaces found that have been live for five days with nothing on this page or in the ledger)** — 🤖 🆕 **AN 8/30 BLOCK WAS ADDED TO THE TABLE M ACCUMULATOR SECTION for `picks/2026-08-30.json` — 50 plays, 25 PITCHER and 25 HITTER (`50 = 25 + 25` ✅), across 14 games.** ✅ **THE FILE WAS WRITTEN TWICE AND FOR THE FIRST TIME IN FOUR DAYS THE OVERWRITE COST NOTHING — both writes are pre-slate, identical on every axis, and `coverage_detail.skipped` carries no `"already started"` key at all.** ⛔ **A mechanism that happens not to bite has not been fixed; the interactive decision owed since 8/27 is owed a THIRD time.** ⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE — no `blend`, no `band`, no model. They are graded into TABLE M-H in the ledger (17/23, two rows ungraded because Tyler Heineman did not play) and nothing here counts them.** 🔴 **T15 WAS NOT RESTATED, FOR THE EIGHTH CONSECUTIVE RUN — no TABLE A play has been carded on 8/23 through 8/30, so the CARDED denominator has not moved for eight slates: it stands at 31 / 100, argmin `w = 1.00`, margin 0.0094, MARGIN leg cleared and `n` leg failed, THE 50/50 UNTOUCHED.** ⚠️ **The drought is now NINE DAYS since the last hand-built card.** ⚠️ **What the machine slate showed is recorded and NOT folded in: mean `model` 60.2, mean `raw` 71.8, actual 44.0, Brier model .2511 / blend .2822 / raw .3335 — and pure model "wins" only because it was the LOWER estimate on 21 of 25 rows on a losing night, which is the day-tracking artifact this page condemns.** 🔴 **RULE 35 GAINED NOTHING AND THAT IS DELIBERATE FOR AN EIGHTH TIME — the merge stays at 185 rungs / 25 distinct starts, T11 progress 25 / 40, even though this one card carries alt ladders across 17 distinct starts and would clear the bar outright.** ✅ **All 17 starts are NAMED anyway so a future REGISTERED pass can deduplicate against them, and naming is not merging.** 🆕 **RULE 50 / RULE 51 OBSERVATIONS FROM THE 8/30 MACHINE CARD LOGGED IN THEIR OWN TALLY — matched class 13/23 (two 50.0% boundary rows excluded on the 8/25 practice and NAMED: Logan Gilbert o4.5 K and Tyler Glasnow o6.5 K), head-to-head 2/8, with 11 n=0 NO-CALL rows and 🔴 SIX further rows the published convention DOES NOT REACH (8 + 11 + 6 = 25 ✅).** 🔴 🆕 **THAT SIX IS A CASE THE CONVENTION HAS NEVER MET AND IT IS REPORTED RATHER THAN RESOLVED BY INVENTION: six rows read `cleared 1/2` — neither a MAJORITY nor NONE — so they are recorded as NO CALL, the literal reading of the published rule. Reading `1/2` as FOR would make the tally 4/14 instead of 2/8. An interactive session should settle it; a grading run does not write a new convention mid-tally.** ⛔ **The 8/25 boundary-row inconsistency is still unresolved, so the eight class tallies are still NOT summable and are still reported separately.** **TWO rows had the class and the head-to-head flatly disagree and they split ONE–ONE (Logan Gilbert u18.5 outs — CLASS right; Robbie Ray u16.5 outs — H2H right), both head-to-heads a single start.** ⛔ **The hand-carded rule-50 accumulator is UNTOUCHED at 4/9.** 🔴🔴 **THE PRE-PUBLISH CHECK 36 DEFECT IS RE-RECORDED AGAINST THE CODE FOR AN EIGHTH CONSECUTIVE RUN — `card.py` prints the head-to-head on every row and NEVER prints rule 51's GAP IN DAYS, verified mechanically (`days` appears ZERO times in `picks/2026-08-30.json`) — 🆕 AND FOR THE FIRST TIME IT COST SOMETHING.** **The gap was computed here for all NINE arms carrying a prior meeting, and eight are 50–121 days out, but JANSON JUNK FACED WASHINGTON ON 2026-08-23 AND WAS CARDED AGAINST THEM AGAIN ON 8/30 — SEVEN DAYS, well inside rule 51's window — and the card said nothing.** ✅ **The re-derivation doubles as a control: every head-to-head count the card printed reproduces exactly from the stored log, 14/14.** 🆕 **A MACHINE-POPULATION RULE 51 LOG WAS CREATED for that instance (Junk o2.5 K, a 3+ K bar, 7 days after a 2-K meeting, MISS at 2 K).** ⛔ **IT IS NOT ADDED TO THE HAND-CARDED RULE 51 ACCUMULATOR, which stays at 2 clean instances / 1 confounded — dropping a machine row into it is the population merge this page exists to prevent.** ⚠️ **The first meeting was WEAK (2 K), so it does not even test the exploratory "strong ≥5 K first meeting" conditional; the pre-registered mean-K specification is still FAILED and CLOSED and nothing is promoted.** **His same-day OUTS row against the same lineup is named and is in no tally — outs are outside rule 51's scope.** 🟡 🔴 **THE `carried` SHADOW WAS WORSE AGAIN — Brier .2827 against .2822 over all 25 rows and .2361 against .2342 over the 7 rows that differ, all seven the T22 shuttled-starter flag across four pitchers.** ⚠️ **Same mechanism an eighth time: four of the seven differing rows WON and `carried` is always the LOWER number. And this is the sharpest illustration yet that the sign says nothing about T22 — the card missed its own mean by TWENTY-TWO POINTS, the most pessimism-friendly slate in the machine card's history, and the pessimistic shadow was STILL worse, because the rows it touched were not the rows that lost.** ⛔ **T22 is neither adopted nor rejected. Across eight machine slates `carried` has differed on 39 rows (3 + 2 + 8 + 8 + 0 + 9 + 2 + 7) and stands WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE, WORSE, WORSE.** 🆕 🔴 **TWO CARD SURFACES HAVE BEEN LIVE SINCE 2026-08-26 AND NEITHER HAS EVER BEEN NAMED IN THIS PROJECT — a `parlays` object (2-, 3- and 4-leg tickets mixing pitcher and hitter legs) and a `top10` list.** ✅ **Both are graded and recorded in `claude/pick-ledger.md`, both in NO denominator here and in NO accumulator on this page; the `top10` rows are all already TABLE M-H rows this slate (10/10) so it opens nothing.** ⚠️ 🔴 **AND A CARD DEFECT FOUND BY COUNTING RATHER THAN READING, RECORDED BECAUSE IT WOULD CORRUPT ANY FUTURE PAIR OR PARLAY ACCUMULATOR: THE POOL EMITS BYTE-IDENTICAL DUPLICATE TICKETS — two of eight pairs on 8/30 and one ticket in each parlay leg-count, against ZERO on 8/26, 8/28 and 8/29, and two again on the live 8/31 card.** ⛔ **REPORTED, NOT FIXED.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY, REFUTATION, PROGRESS COUNTER OR EARLIER CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of one new section and this entry, plus a SUPERSEDED marker appended in place to the seven-slate TABLE M progress counter, which is kept rather than replaced. T15 stands at 31 carded plays / 100; T11 at 25 / 40 distinct starts; rule 50 at 4/9; rule 51 at 2 clean / 1 confounded; rule 53 at 2 of 6. The `collections.Counter` line-loss check reports exactly ONE line replaced — that progress counter — and nothing else lost.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session's transcript JSONL with a JSON walker rather than retyped (two recorded occurrences, compared and byte-identical at 183,587 bytes) → local file → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → fresh `project_read` and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **Three docs touched this run — `claude/pick-ledger.md`, this one and `claude/mlb-opponent-database.md`.**

- **Aug 30 2026, 7:30am scheduled run (the seventh machine slate, a card destroyed for the second time in four days, a doubleheader hazard the grading rules do not reach, and a seventh consecutive run with no carded play to advance T15)** — 🤖 🆕 **AN 8/29 BLOCK WAS ADDED TO THE TABLE M ACCUMULATOR SECTION for `picks/2026-08-29.json` AS COMMITTED — 50 plays, 6 PITCHER and 44 HITTER (`50 = 6 + 44` ✅), across THREE games.** 🔴🔴 **THAT IS NOT A THREE-GAME SLATE: 2026-08-29 WAS A SEVENTEEN-GAME SLATE AND THIS IS THE SECOND DESTROYED CARD IN FOUR DAYS.** **The pre-slate `20b154f2` at `2026-08-29T11:08:08Z` (7:08am ET) held 50 plays across 13 games with TWENTY-FIVE pitcher rows; the surviving `49ec278a` at `23:27:52Z` (7:27pm ET) holds six, because `card.py`'s own guard dropped thirteen games as `"already started"`.** ✅ **Full provenance, the commit hashes and the reasoning for grading the surviving file are in `claude/pick-ledger.md`.** ⛔ **REPORTED, NOT FIXED — a grading run does not touch the code.** 🔴 🆕 **A GRADING HAZARD THIS PROJECT HAS NEVER MET IS NAMED HERE BECAUSE IT WILL RECUR: 2026-08-29 CARRIED TWO DOUBLEHEADERS (BOS @ NYY and AZ @ SF), SO A DATE IS NOT A GAME.** **Jose Fernandez was carded on the 02:06Z AZ @ SF event (`gamePk 823176`, game 2) and appeared only in game 1, so his date-level game log carries an `8/29` row belonging to a different game at a different price against a different pitcher.** ⛔ **Left UNGRADED on the 8/24 Hayes / 8/26 Roupp precedent, with both readings printed in the ledger.** ➡️ **Every accumulator on this page that ever reads a game log BY DATE inherits this hazard: resolve to a `gamePk`, not to a date.** ⛔ **THE 44 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE — no `blend`, no `band`, no model. They are graded into TABLE M-H in the ledger (25/41, three rows ungraded) and nothing here counts them.** 🔴 **T15 WAS NOT RESTATED, FOR THE SEVENTH CONSECUTIVE RUN — no TABLE A play has been carded on 8/23 through 8/29, so the CARDED denominator has not moved for seven slates: it stands at 31 / 100, argmin `w = 1.00`, margin 0.0094, MARGIN leg cleared and `n` leg failed, THE 50/50 UNTOUCHED.** ⚠️ **The drought is now EIGHT DAYS since the last hand-built card.** ⛔ **An observation, not a licence to widen the denominator.** 🔴 **RULE 35 GAINED NOTHING AND THAT IS DELIBERATE FOR A SEVENTH TIME — the merge stays at 185 rungs / 25 distinct starts, T11 progress 25 / 40.** ✅ **All five starts are NAMED anyway so a future REGISTERED pass can deduplicate against them — Ryan Johnson (2 K), Cristopher Sánchez (8 K), Mitch Bratt (2 K), Shane Baz (4 K), Jack Perkins (5 K), all 2026-08-29 — and naming is not merging.** 🆕 **RULE 50 / RULE 51 OBSERVATIONS FROM THE 8/29 MACHINE CARD LOGGED IN THEIR OWN TALLY — matched class 2/6 (no row sits exactly on 50.0%, so nothing is excluded), head-to-head 1/1 with 5 n=0 NO-CALL rows (1 + 5 = 6 ✅), and ZERO rows where the two flatly disagreed: the single row carrying a head-to-head has both sources pointing the same way.** ⛔ **SIX ROWS, five of them from three pitchers, on the wreckage of a seventeen-game slate — the 2/6 is not a data point about the matched class.** ⛔ **The boundary-row convention inconsistency flagged on 8/25 is UNCHANGED and UNRESOLVED, so the seven class tallies are still NOT summable and are still reported separately.** ⛔ **The hand-carded rule-50 accumulator is UNTOUCHED at 4/9 and rule 51 gains NO rows.** 🔴 **THE PRE-PUBLISH CHECK 36 DEFECT IS RE-RECORDED AGAINST THE CODE FOR A SEVENTH CONSECUTIVE RUN: `card.py` prints the head-to-head on every row and NEVER prints rule 51's GAP IN DAYS.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-08-29.json`.** ✅ **AND THE GAP WAS COMPUTED HERE INSTEAD, FOR THE ONE ARM THAT CARRIES A PRIOR MEETING: Shane Baz last faced the Athletics on 2026-05-09 — 112 days — far outside the 30-day window, so no rule-51 instance was owed and none is added. The re-derivation doubles as a control: the card's `1 start(s) vs ATH -- cleared 1/1` reproduces exactly from the stored log.** ⛔ **That is the defect not biting, not the defect being fixed. REPORTED, NOT FIXED.** 🟡 🔴 **THE `carried` SHADOW WAS WORSE AGAIN — Brier .2965 against .2500 over all 6 rows and .3137 against .1741 over the 2 rows that differ, BOTH the T22 shuttled-starter flag, across two pitchers.** ⚠️ **The mechanism is the same one for the seventh time: BOTH differing rows WON and `carried` is always the LOWER number, so it loses for being pessimistic on a good set exactly as it won twice for being pessimistic on bad ones. Seven slates, five verdicts, every one explained by whether that night's flagged rows happened to win.** ⛔ **T22 is neither adopted nor rejected. Across seven machine slates `carried` has differed on 32 rows (3 + 2 + 8 + 8 + 0 + 9 + 2) and stands WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE, WORSE.** 🔴 🆕 **A RUN-LEVEL FACT LOGGED BECAUSE IT IS THE FIRST TIME THE RUNNER AND THIS PROJECT HAVE DISAGREED: `data/latest/record.json`, built `2026-08-30T10:09:14Z`, reads `by_kind.pitcher: 71/135` — EXACT — and `by_kind.hitter: 107/176` against this project's 106/175, with `by_day 2026-08-29: 30/48, voids 2` against 29/47, voids 3.** ✅ **The entire difference is the ONE Jose Fernandez doubleheader row: the runner grades hitter rows by DATE and this project by EVENT.** ⛔ **Neither is a bug; it is the mechanics question above, put in front of an interactive session rather than settled here.** ⚠️ **The pitcher half reproducing exactly is a genuine independent control.** ✅ **The repo grading route worked for a second consecutive run: `data/2026-08-29/results/final.json.gz` pulled `2026-08-30T10:06:25Z`, `n_games: 17, n_final: 17, domain_violations: 0`.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY, REFUTATION, PROGRESS COUNTER OR EARLIER CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of one new section and this entry, plus a SUPERSEDED marker appended in place to the six-slate TABLE M progress counter, which is kept rather than replaced. T15 stands at 31 carded plays / 100; T11 at 25 / 40 distinct starts; rule 50 at 4/9; rule 51 at 2 clean / 1 confounded; rule 53 at 2 of 6. The `collections.Counter` line-loss check reports exactly ONE line replaced — that progress counter — and nothing else lost.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session's transcript JSONL with a JSON walker rather than retyped (FOUR recorded occurrences, compared and byte-identical at 165,515 bytes) → local file → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → fresh `project_read` and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **Three docs touched this run — `claude/pick-ledger.md`, this one and `claude/mlb-opponent-database.md`.**

- **Aug 29 2026, 7:30am scheduled run (the sixth machine slate, the full board back after 8/27's destroyed card, and a sixth consecutive run with no carded play to advance T15)** — 🤖 🆕 **AN 8/28 BLOCK WAS ADDED TO THE TABLE M ACCUMULATOR SECTION for `picks/2026-08-28.json` — 50 plays, 25 PITCHER and 25 HITTER (`50 = 25 + 25` ✅), across 15 games.** ⚠️ 🔴 **THE FILE WAS WRITTEN SEVEN TIMES AND EACH WRITE REPLACED IT, EXACTLY AS ON 8/27 — BUT THIS TIME THE LAST WRITE WAS THE PRE-SLATE ONE AND THE BEST ONE: six overnight writes held 5 pitcher rows across 8 games, and the surviving `069707d` at `2026-08-28T18:20:40Z` holds 25 across 15, four hours before first pitch.** ⛔ **The code is unchanged and so is the hazard; a mechanism that happens to help has not been fixed. Full provenance in `claude/pick-ledger.md`.** ⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE — no `blend`, no `band`, no model. They are graded into TABLE M-H in the ledger (16/23, 2 rows ungraded because Jakob Marsee and Amed Rosario did not play) and nothing here counts them.** ⚠️ 🔴 **The ~25-point M-H gap did NOT recur on a comparable board (−11.3, against −7.2, −26.3, −25.1 and 8/27's non-comparable +0.5) — but four gaps of −7, −26, −25 and −11 are a scattered set, not a converging one, and they are not averaged.** 🔴 **T15 WAS NOT RESTATED, FOR THE SIXTH CONSECUTIVE RUN — no TABLE A play has been carded on 8/23 through 8/28, so the CARDED denominator has not moved for six slates: it stands at 31 / 100, argmin `w = 1.00`, margin 0.0094, MARGIN leg cleared and `n` leg failed, THE 50/50 UNTOUCHED.** ⚠️ **The drought is now seven days, and an interactive session DID sit down on 8/28 evening without building a card — it created four new project docs and logged neither a TABLE A nor a TABLE C.** ⛔ **An observation, not a licence to widen the denominator.** 🔴 **RULE 35 GAINED NOTHING AND THAT IS DELIBERATE FOR A SIXTH TIME — the merge stays at 185 rungs / 25 distinct starts, T11 progress 25 / 40, even though this ONE slate carries 17 distinct starts with Hard Rock ladders and would clear T11's bar of 40 outright.** ✅ **All 17 starts are NAMED anyway so a future REGISTERED pass can deduplicate against them, and naming is not merging.** 🆕 **RULE 50 / RULE 51 OBSERVATIONS FROM THE 8/28 MACHINE CARD LOGGED IN THEIR OWN TALLY — matched class 10/25 (no row sits exactly on 50.0%, so nothing is excluded), head-to-head 7/11 with 14 n=0 NO-CALL rows (11 + 14 = 25 ✅), and the FOUR rows where the two flatly disagreed itemised, splitting TWO–TWO.** ⚠️ 🔴 **Ten of the eleven head-to-head samples are n=1 and one is n=2, and the Dylan Cease conflict is flagged as uninformative BY CONSTRUCTION — a 20.0% matched class on FIVE starts is noise wearing a percentage, so scoring it as an H2H win is arithmetically correct and epistemically empty.** ⛔ **The boundary-row convention inconsistency flagged on 8/25 is UNCHANGED and UNRESOLVED, so the six class tallies are still NOT summable and are still reported separately.** ⛔ **The hand-carded rule-50 accumulator is UNTOUCHED at 4/9 and rule 51 gains NO rows.** 🔴 **THE PRE-PUBLISH CHECK 36 DEFECT IS RE-RECORDED AGAINST THE CODE FOR A SIXTH CONSECUTIVE RUN: `card.py` prints the head-to-head on every row and NEVER prints rule 51's GAP IN DAYS.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-08-28.json`.** ✅ 🆕 **AND THE GAP WAS COMPUTED HERE INSTEAD, FOR ALL EIGHT ARMS THAT CARRY A PRIOR MEETING, by re-deriving every meeting from the repo's own pre-slate log — 54, 56, 58, 94, 112, 113, 116 and 119 days, every one far outside the 30-day window. No rule-51 instance was owed and none is added, and the re-derivation doubles as a control: every head-to-head count the card printed reproduces exactly.** ⛔ **That is the defect not biting, not the defect being fixed. REPORTED, NOT FIXED.** 🟡 🔴 **THE `carried` SHADOW WAS WORSE AGAIN, ON THE LARGEST DIFFERING SET YET — Brier .2696 against .2602 over all 25 rows and .2433 against .2171 over the 9 rows that differ, ALL NINE the T22 shuttled-starter flag, across six pitchers.** ⚠️ **The mechanism is 8/25's and 8/26's INVERTED, which is why neither result is evidence: six of the nine rows WON and `carried` is always the LOWER number, so it loses for being pessimistic on a good set exactly as it won twice for being pessimistic on bad ones. Six slates, four verdicts, every one explained by whether that night's flagged rows happened to win.** ⛔ **T22 is neither adopted nor rejected. Across six machine slates `carried` has differed on 30 rows (3 + 2 + 8 + 8 + 0 + 9) and stands WORSE, WORSE, BETTER, BETTER, NO CALL, WORSE.** ✅ 🆕 **A RUN-LEVEL FACT THAT REVERSES THE LAST TWO ENTRIES: THE COLLECTOR'S RESULTS MODE IS BACK.** **`data/2026-08-28/results/final.json.gz` was pulled `2026-08-29T10:07:00Z` and reads `n_games: 15, n_final: 15, domain_violations: 0`, and 8/26 and 8/27 have been BACK-FILLED.** ✅ **`data/latest/record.json` now reproduces every one of this project's machine denominators exactly, including `2026-08-27: 18/36, voids 2` on the destroyed-card slate.** ⛔ **It is still a CONVENIENCE and was not trusted alone — the slate was controlled five independent ways, one of them an INDEPENDENT statsapi pull on a different host for all 19 pitchers, 19/19 exact, with zero domain violations.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY, REFUTATION, PROGRESS COUNTER OR EARLIER CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of one new section and this entry, plus a SUPERSEDED marker appended in place to the five-slate TABLE M progress counter, which is kept rather than replaced. T15 stands at 31 carded plays / 100; T11 at 25 / 40 distinct starts; rule 50 at 4/9; rule 51 at 2 clean / 1 confounded; rule 53 at 2 of 6. The `collections.Counter` line-loss check reports exactly ONE line replaced — that progress counter — and nothing else lost.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session's transcript JSONL with a JSON walker rather than retyped (two recorded occurrences, compared and byte-identical at 145,940 bytes) → local file → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → fresh `project_read` and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **Three docs touched this run — `claude/pick-ledger.md`, this one and `claude/mlb-opponent-database.md`.**

- **Aug 28 2026, 7:30am scheduled run (the fifth machine slate, and there is almost nothing of it — the card file was overwritten after the slate began; a fifth consecutive run with no carded play to advance T15)** — 🤖 🆕 **AN 8/27 BLOCK WAS ADDED TO THE TABLE M ACCUMULATOR SECTION for `picks/2026-08-27.json` AS COMMITTED — 38 plays, 1 PITCHER and 37 HITTER (`38 = 1 + 37` ✅), all from ONE game.** 🔴🔴 **THAT IS NOT A ONE-GAME SLATE, IT IS A DESTROYED CARD: the file was written three times and each write replaced it, and the surviving version was generated `2026-08-28T00:59:58Z` (8:59pm ET) with six of the seven games already started. The genuine pre-slate card, commit `4044f600` at `17:08:34Z`, held 50 plays across 6 games — 12 pitcher rows and 8 pairs.** ✅ **Full provenance, commit hashes, the twelve lost pitcher rows and the reasoning for grading the surviving file (the literal rule AND reversibility) are in `claude/pick-ledger.md`.** ⛔ **REPORTED, NOT FIXED — a grading run does not touch the code.** ⛔ **THE 37 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE — no `blend`, no `band`, no model. They are graded into TABLE M-H in the ledger (18/35, 2 rows ungraded because Nolan Arenado did not play) and nothing here counts them.** ⚠️ 🔴 **The ~25-point M-H gap did NOT recur (+0.5 after −7.2, −26.3, −25.1) and that is NOT the gap closing: this slate's mean stated rate is 50.9 against 80.3, 82.3 and 81.1, because the collapsed board filled its slots with long-shot overs. Different population; the four gaps are not comparable and are not averaged.** 🔴 **T15 WAS NOT RESTATED, FOR THE FIFTH CONSECUTIVE RUN — no TABLE A play has been carded on 8/23, 8/24, 8/25, 8/26 or 8/27, so the CARDED denominator has not moved for five slates: it stands at 31 / 100, argmin `w = 1.00`, margin 0.0094, MARGIN leg cleared and `n` leg failed, THE 50/50 UNTOUCHED.** ⚠️ **The drought is now six days since the last hand-built card, and the smallness of the machine slate is not a licence to fold it in.** 🔴 **RULE 35 GAINED NOTHING AND THAT IS DELIBERATE FOR A FIFTH TIME — the merge stays at 185 rungs / 25 distinct starts, T11 progress 25 / 40, even though the card carries a seven-rung Hard Rock ladder.** ✅ **The start is NAMED anyway so a future REGISTERED pass can deduplicate against it — Landen Roupp 2026-08-27 (3 K) — and naming is not merging.** 🆕 **RULE 50 / RULE 51 OBSERVATIONS FROM THE 8/27 MACHINE CARD LOGGED IN THEIR OWN TALLY — matched class 0/1, head-to-head 1/1 with ZERO n=0 NO-CALL rows (1 + 0 = 1 ✅), and the ONE row where the two flatly disagreed itemised (Landen Roupp o4.5 K vs AZ — class 38/74 = 51.4% FOR, h2h 1/3 AGAINST across three enumerated meetings, result L, H2H right).** ⚠️ **This head-to-head is n=3 rather than the n=1 that has dominated every prior machine slate, and the three meetings were re-derived from the repo's own pre-slate log and reproduce exactly.** ⛔ **ONE ROW IS NOT A DATA POINT. The boundary-row convention inconsistency flagged on 8/25 is UNCHANGED and UNRESOLVED, so the five class tallies are still NOT summable and are still reported separately.** ⛔ **The hand-carded rule-50 accumulator is UNTOUCHED at 4/9 and rule 51 gains NO rows.** 🔴 **THE PRE-PUBLISH CHECK 36 DEFECT IS RE-RECORDED AGAINST THE CODE FOR A FIFTH CONSECUTIVE RUN: `card.py` prints the head-to-head on every row and NEVER prints rule 51's GAP IN DAYS.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-08-27.json`.** ✅ 🆕 **AND THE GAP WAS COMPUTED HERE INSTEAD, WHICH NO PRIOR RUN COULD DO BECAUSE THE CARD CARRIED TOO MANY ROWS: Roupp's most recent prior meeting with Arizona is 2026-06-30, FIFTY-EIGHT days, comfortably outside the 30-day window — so no rule-51 instance was owed and none is added.** ⛔ **That is the defect not biting, not the defect being fixed. REPORTED, NOT FIXED.** 🟡 **THE `carried` SHADOW DIFFERED ON ZERO ROWS (`carried` = `blend` = 52.8), so there was nothing to score. Across five machine slates `carried` has differed on 21 rows (3 + 2 + 8 + 8 + 0) and stands WORSE, WORSE, BETTER, BETTER, NO CALL. T22 is neither adopted nor rejected.** ⚠️ 🆕 **A RUN-LEVEL FACT LOGGED BECAUSE IT IS NOT YESTERDAY'S: THE COLLECTOR IS COMMITTING AGAIN (last commit `2026-08-28T07:16Z`) BUT ITS `results` MODE HAS NOT RUN SINCE `2026-08-27T16:39Z` — `data/2026-08-27/results/final.json.gz` is a PRE-SLATE snapshot with `n_final: 0`, every game `Pre-Game` or `Scheduled` and `started: true` on ZERO pitchers, and `data/latest/record.json` lists `2026-08-27` under `skipped` with the reason `"0/7 games final -- not settled"`.** ⛔ **So the repo grading route was unavailable for a SECOND consecutive run, for a DIFFERENT reason.** ✅ **The slate was graded from statsapi instead, controlled four independent ways with zero domain violations.** ✅ 🆕 **ONE GENUINELY NEW CONTROL IS RECORDED BECAUSE IT GENERALISES: every `raw` string the card printed — all 37 hitter rows and the pitcher's 17/25 — was RECOMPUTED from the repo's own pre-slate logs plus `lineups.json.gz` under `card.py`'s documented started-games filter and reproduces 38/38 EXACTLY, which checks the card's evidence column against the data it claims to have read.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY, REFUTATION, PROGRESS COUNTER OR EARLIER CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of one new section and this entry, plus a SUPERSEDED marker appended in place to the four-slate TABLE M progress counter, which is kept rather than replaced. T15 stands at 31 carded plays / 100; T11 at 25 / 40 distinct starts; rule 50 at 4/9; rule 51 at 2 clean / 1 confounded; rule 53 at 2 of 6. The `collections.Counter` line-loss check reports exactly ONE line replaced — that progress counter — and nothing else lost.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session's transcript JSONL with a JSON walker rather than retyped (two recorded occurrences, compared and byte-identical at 129,342 bytes) → local file → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → fresh `project_read` and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **Three docs touched this run — `claude/pick-ledger.md`, this one and `claude/mlb-opponent-database.md`.**

- **Aug 27 2026, 7:30am scheduled run (the fourth machine slate, a scratched starter the grading rules do not reach, a fourth consecutive run with no carded play to advance T15 — and the first run on which the repo grading route was unavailable)** — 🤖 🆕 **AN 8/26 BLOCK WAS ADDED TO THE TABLE M ACCUMULATOR SECTION for `picks/2026-08-26.json` — 50 plays, 25 PITCHER and 25 HITTER (`50 = 25 + 25` ✅).** 🔴 **ONLY 23 OF THE 25 PITCHER ROWS ARE GRADED: Landen Roupp was carded twice as San Francisco's starter and DID NOT PITCH.** ✅ **Both rows are UNGRADED and in no tally here or in `claude/pick-ledger.md`, with the historical control run BEFORE the absence was believed (his fetched game log ends 2026-08-20 with no 8/26 row; his season block reads 25 GS / 404 outs / 130 K; the repo's pre-slate snapshot reads the same; the game itself is `Final`).** ⛔ **The standing rule "W OR L — THERE IS NO VOID" does not reach a starter who never threw, the two readings give opposite answers (11/23 vs 13/25), and a grading run does not decide it — flagged for an interactive session, with both numbers printed in the ledger.** ⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE — no `blend`, no `band`, no model. They are graded into TABLE M-H in the ledger (14/25, gap −25.1) and nothing here counts them.** ⚠️ 🔴 **That is the SECOND CONSECUTIVE ~25-point gap on M-H (−26.3 then −25.1, after −7.2); the RATE is still not a measurement but the GAP is no longer a one-off, and it is put in front of an interactive session in the ledger rather than acted on here.** 🔴 **T15 WAS NOT RESTATED, FOR THE FOURTH CONSECUTIVE RUN — no TABLE A play has been carded on 8/23, 8/24, 8/25 or 8/26, so the CARDED denominator has not moved for four slates: it stands at 31 / 100, argmin `w = 1.00`, margin 0.0094, MARGIN leg cleared and `n` leg failed, THE 50/50 UNTOUCHED.** ⚠️ **The drought is now five days since the last hand-built card, and closing T15 needs either an interactive card or a separately pre-registered machine-population entry. ⛔ A grading run may create neither.** 🔴 **RULE 35 GAINED NOTHING AND THAT IS DELIBERATE FOR A FOURTH TIME — the merge stays at 185 rungs / 25 distinct starts, T11 progress 25 / 40, even though the 8/26 board carries 91 Hard Rock alt rungs.** 🆕 **RULE 50 / RULE 51 OBSERVATIONS FROM THE 8/26 MACHINE CARD LOGGED IN THEIR OWN TALLY — matched class 13/23 (no row sits exactly on 50.0%, so nothing is excluded this slate), head-to-head 2/3 with 20 n=0 NO-CALL rows (3 + 20 = 23 ✅), and the ONE row where the two flatly disagreed itemised (Joey Cantillo u15.5 outs vs LAA — class 11/17 FOR, h2h 0/1 AGAINST, result L, H2H right).** ⚠️ 🔴 **TWENTY OF TWENTY-THREE ROWS HAVE NO HEAD-TO-HEAD AT ALL — the highest no-call share of any machine slate — and all three that do are n=1, so the 2/3 says nothing and is printed only for completeness.** ⛔ **The boundary-row convention inconsistency flagged on 8/25 is UNCHANGED and UNRESOLVED, so the four class tallies are still NOT summable and are still reported separately.** ⛔ **The hand-carded rule-50 accumulator is UNTOUCHED at 4/9 and rule 51 gains NO rows.** 🔴 **THE PRE-PUBLISH CHECK 36 DEFECT IS RE-RECORDED AGAINST THE CODE FOR A FOURTH CONSECUTIVE RUN: `card.py` prints the head-to-head on every row and NEVER prints rule 51's GAP IN DAYS — five of the 25 pitcher rows carry a prior meeting and not one says how long ago.** ✅ **Verified mechanically again: the string `days` appears ZERO times anywhere in `picks/2026-08-26.json`.** ⛔ **REPORTED, NOT FIXED.** 🟡 🔴 **THE `carried` SHADOW BEAT THE BLEND FOR A SECOND CONSECUTIVE SLATE — Brier .2671 against .3123 over all 23 graded rows and .2823 against .4123 over the 8 rows that differ, ALL EIGHT the T22 shuttled-starter flag, across five pitchers.** ⚠️ **The mechanism is IDENTICAL to 8/25's and is recorded so the number is not misread: six of the eight rows LOST and `carried` is always the LOWER number, so it wins for being pessimistic on a bad set — the same day-tracking artifact this page condemns the "closer" column for, on the same flag, two nights running.** ⛔ **TWO CONSECUTIVE WINS BY THE SAME MECHANISM IS THE SAME PIECE OF EVIDENCE TWICE. T22 is neither adopted nor rejected. Across four machine slates `carried` has differed on 21 rows (3 + 2 + 8 + 8) and stands WORSE, WORSE, BETTER, BETTER, concentrated each night in one or two pitchers.** ⚠️ 🆕 **AND A RUN-LEVEL FACT IS LOGGED BECAUSE IT AFFECTS EVERY FUTURE PASS: THE COLLECTOR HAS NOT COMMITTED SINCE `2026-08-26T19:30:22Z`, `data/2026-08-26/results/` DOES NOT EXIST, and the repo grading route — adopted as the cheap path on 8/24 — was UNAVAILABLE for the first time.** ✅ **The slate was graded from statsapi through `WebFetch` instead, controlled two independent ways on 19/19 pitchers and 21/21 hitters with ZERO domain violations, and the control caught a real fabricated row (Nathan Lukes) and rejected it.** ⛔ **REPORTED, NOT FIXED — a headless session cannot see the Actions run history, re-run a workflow or push.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY, REFUTATION, PROGRESS COUNTER OR EARLIER CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of one new section and this entry, plus a SUPERSEDED marker appended in place to the three-slate TABLE M progress counter, which is kept rather than replaced. T15 stands at 31 carded plays / 100; T11 at 25 / 40 distinct starts; rule 50 at 4/9; rule 51 at 2 clean / 1 confounded; rule 53 at 2 of 6. The `collections.Counter` line-loss check reports exactly ONE line replaced — that progress counter — and nothing else lost.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session's transcript JSONL with a JSON walker rather than retyped (two recorded occurrences, compared and byte-identical at 109,635 bytes) → local file → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → fresh `project_read` and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **Three docs touched this run — `claude/pick-ledger.md`, this one and `claude/mlb-opponent-database.md`.**

- **Aug 26 2026, 7:30am scheduled run (the third machine slate, the first on which `carried` beat the blend, and a third consecutive run with no carded play to advance T15)** — 🤖 🆕 **AN 8/25 BLOCK WAS ADDED TO THE TABLE M ACCUMULATOR SECTION for `picks/2026-08-25.json` — 50 plays, 25 PITCHER and 25 HITTER (`50 = 25 + 25` ✅), against 8/24's 23 + 27 and 8/23's 32 pitcher-only.** ⛔ **THE 25 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE — same reason as 8/24: no `blend`, no `band`, no model. They are graded into TABLE M-H in `claude/pick-ledger.md` (14/25) and nothing here counts them.** 🔴 **T15 WAS NOT RESTATED, FOR THE THIRD CONSECUTIVE RUN — no TABLE A play has been carded on 8/23, 8/24 or 8/25, so the CARDED denominator has not moved for three slates: it stands at 31 / 100, argmin `w = 1.00`, margin 0.0094, MARGIN leg cleared and `n` leg failed, THE 50/50 UNTOUCHED.** ⚠️ 🆕 **AND THE DROUGHT IS NAMED RATHER THAN LEFT IMPLICIT: T15's `n` leg can now only advance if a human builds a card, and none has been hand-built since 8/22.** ⛔ **An observation, not a licence to widen the denominator — closing T15 needs either an interactive card or a separately pre-registered machine-population entry, and a grading run may create neither.** 🔴 **RULE 35 GAINED NOTHING AND THAT IS DELIBERATE FOR A THIRD TIME — the merge stays at 185 rungs / 25 distinct starts, T11 progress 25 / 40, even though the 8/25 board carries full Hard Rock ladders across 18 distinct starts.** 🆕 **RULE 50 / RULE 51 OBSERVATIONS FROM THE 8/25 MACHINE CARD LOGGED IN THEIR OWN TALLY — matched class 11/23, head-to-head 8/10 with 15 n=0 NO-CALL rows (10 + 15 = 25 ✅), and the THREE rows where the two flatly disagreed itemised, the HEAD-TO-HEAD taking all three.** ⚠️ 🔴 **THREE CONFLICTS, EVERY HEAD-TO-HEAD SAMPLE A SINGLE START, AND A CLEAN SWEEP — which is what a coin landing the same way three times looks like. 8/23 split 2–2, 8/24 went four-of-five to the CLASS, 8/25 goes three-of-three to the H2H.** ⛔ **No direction is read into it and it is not set beside the hand-carded 3/3 note, which is about a TIEBREAKER being INVOKED rather than a COLUMN being PRINTED.** ⛔ 🆕 **AND A CONVENTION INCONSISTENCY IS FLAGGED RATHER THAN SILENTLY HARMONISED: today's class tally EXCLUDES two rows whose class sits exactly on 50.0% (Seth Lugo o3.5 K, Jacob deGrom u6.5 K) because a boundary class argues nothing, while the 8/23 block kept its own identical boundary row (Andrew Abbott, 20/40) INSIDE its 32-row denominator.** ➡️ **The three tallies are therefore NOT summable as published and are reported separately. An interactive session should settle the convention; a grading run does not re-cut a published tally after the fact.** 🔴 **THE PRE-PUBLISH CHECK 36 DEFECT IS RE-RECORDED AGAINST THE CODE FOR A THIRD CONSECUTIVE RUN: `card.py` prints the head-to-head on every row and NEVER prints rule 51's GAP IN DAYS — ten of the 25 pitcher rows carry a prior meeting and not one says how long ago.** ✅ **Verified mechanically this time: the string `days` appears ZERO times anywhere in `picks/2026-08-25.json`.** ⛔ **REPORTED, NOT FIXED — a grading run does not touch the code and a headless session can neither test nor push one. Rule 51 gains NO rows.** 🟡 🔴 **THE `carried` SHADOW BEAT THE BLEND FOR THE FIRST TIME: Brier .2365 against .2654 over all 25 rows and .2615 against .3519 over the 8 rows that differ — ALL EIGHT the T22 shuttled-starter flag, across six pitchers, three of them Chris Bassitt on one start.** ⚠️ **The mechanism is recorded so the number is not misread: six of the eight rows LOST and `carried` is always the LOWER number, so it wins for being pessimistic on a bad set — the same day-tracking artifact this page condemns the "closer" column for.** ⛔ **T22 is neither adopted nor rejected. Across three machine slates `carried` has differed on 13 rows (3 + 2 + 8) and stands at WORSE, WORSE, BETTER, concentrated each night in one or two pitchers.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY, REFUTATION, PROGRESS COUNTER OR EARLIER CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of one new section and this entry, plus a SUPERSEDED marker appended in place to the two-slate TABLE M progress counter, which is kept rather than replaced. T15 stands at 31 carded plays / 100; T11 at 25 / 40 distinct starts; rule 50 at 4/9; rule 51 at 2 clean / 1 confounded; rule 53 at 2 of 6. The `collections.Counter` line-loss check reports exactly ONE line replaced — that progress counter — and nothing else lost.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session's transcript JSONL with a JSON walker (two recorded occurrences, compared and identical) rather than retyped → local file → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → fresh `project_read` and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **Three docs touched this run — `claude/pick-ledger.md`, this one and `claude/mlb-opponent-database.md`.**

- **Aug 25 2026, 7:30am scheduled run (the machine card grew a hitter half, and the disciplined answer was a FOURTH denominator plus two accumulators that were deliberately NOT advanced)** — 🤖 🆕 **AN 8/24 BLOCK WAS ADDED TO THE TABLE M ACCUMULATOR SECTION for `picks/2026-08-24.json` — 50 plays, 23 PITCHER and 27 HITTER, against 8/23's 32 pitcher-only.** 🔴 **THE 27 HITTER ROWS ARE IN NO ACCUMULATOR ON THIS PAGE: they carry no `blend`, no `band` and no model (`basis: "MARKET + DESCRIPTIVE — no model, no confidence rating (rule 55)"`), and a row with no carded estimate cannot be bucketed against one.** ✅ **They are graded into a separate fourth denominator, TABLE M-H (19/26), in `claude/pick-ledger.md`, and nothing here counts them.** ⚠️ **The split is the grading run's judgement, is flagged as such, and an interactive session should ratify or overrule it.** 🔴 **T15 WAS NOT RESTATED, FOR THE SECOND CONSECUTIVE RUN — no TABLE A play was carded on 8/23 or 8/24, so the CARDED denominator has not moved: it stands at 31 / 100, argmin `w = 1.00`, margin 0.0094, MARGIN leg cleared and `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Folding the machine card's 23 pitcher rows in would push the counter past 50 without a single carded play, which is a silent re-specification.** 🔴 **RULE 35 GAINED NOTHING AND THAT IS DELIBERATE AGAIN — the merge stays at 185 rungs / 25 distinct starts, T11 progress 25 / 40.** ⚠️ 🆕 **AND THE TEMPTATION IS NOW CONCRETE RATHER THAN HYPOTHETICAL: the 8/24 board carries 14 distinct starts with full Hard Rock ladders, which would take T11 to 39 — and ONE MORE MACHINE SLATE WOULD CLEAR ITS BAR OUTRIGHT.** ⛔ **It is still not merged: T11's `n` is CARDED arms and the machine board is every qualifying starter. A machine shadow ladder must be PRE-REGISTERED first, interactively.** 🆕 **RULE 50 / RULE 51 OBSERVATIONS FROM THE 8/24 MACHINE CARD LOGGED IN THEIR OWN TALLY — matched class 16/23, head-to-head 4/9 with 14 n=0 NO-CALL rows (9 + 14 = 23 ✅), and the FIVE rows where the two flatly disagreed itemised, the class taking four of them.** ⚠️ 🔴 **ALL FIVE CONFLICTS HAVE THE IDENTICAL SHAPE — a 51–63% class against a 0-for-1 head-to-head — so they are five rows testing ONE pattern, not five independent tests, and every head-to-head sample on the whole card is n=1.** ⛔ **The hand-carded rule-50 accumulator is UNTOUCHED at 4/9 and rule 51 gains NO rows: `card.py` prints these columns on every row, which is not rule 50 FIRING, and the gap in days is still not recoverable from the card.** 🔴 **THE PRE-PUBLISH CHECK 36 DEFECT IS RE-RECORDED AGAINST THE CODE FOR A SECOND CONSECUTIVE RUN: `card.py` prints the head-to-head on every row and NEVER prints rule 51's GAP IN DAYS — nine of the 23 pitcher rows carry a prior meeting and not one says how long ago.** ⛔ **REPORTED, NOT FIXED — a grading run does not touch the code and a headless session can neither test nor push one.** 🟡 **THE `carried` SHADOW LOGGED FOR 8/24: it differed on 2 of 23 rows, BOTH the same pitcher (Robbie Ray, T22 flag), and was WORSE again — Brier .2223 against the blend's .2099 overall and .3221 against .1797 on the two.** ⚠️ **Across both machine slates `carried` has been worse on both, over five differing rows, concentrated each night in one or two pitchers.** ⛔ **T22 is neither adopted nor rejected.** 🆕 ⚠️ **A GRADING-RULE GAP IS LOGGED: one hitter row (Ke'Bryan Hayes u0.5 RBIs) could not be graded because HE WAS NOT IN THE LINEUP, and the standing "W OR L — THERE IS NO VOID" rule was written for pitcher props and does not reach a bench bat who never batted.** ✅ **Recorded UNGRADED, in no tally.** ➡️ **A hitter clause is owed in the ledger's grading-mechanics section; ⛔ a grading run is not the place to write one.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY, REFUTATION, PROGRESS COUNTER OR EARLIER CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of one new section and this entry, plus a SUPERSEDED marker appended in place to the one-slate TABLE M progress counter, which is kept rather than replaced. T15 stands at 31 carded plays / 100; T11 at 25 / 40 distinct starts; rule 50 at 4/9; rule 51 at 2 clean / 1 confounded; rule 53 at 2 of 6. The `collections.Counter` line-loss check reports exactly ONE line replaced — that progress counter, which is extended in place with its SUPERSEDED marker rather than removed — and nothing else lost.** ⚠️ **Merged, not rewritten: `project_read` → the tool result extracted VERBATIM from this session's transcript JSONL with a JSON walker rather than retyped → local file → programmatic patch with anchors ASSERTED to occur EXACTLY ONCE before any write → `collections.Counter` line-loss check → fresh `project_read` and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.** ⛔ **Three docs touched this run — `claude/pick-ledger.md`, this one and `claude/mlb-opponent-database.md`.**

- **Aug 24 2026, Monday sweep — a two-line text-only reconciliation. 🔴 NOT ONE GRADED ROW, BUCKET COUNT, RUNG COUNT OR BRIER VALUE WAS TOUCHED.** 🔴 **RULE 50's progress line was STRUCK AND RESTATED: it read `9 instances (7 gradeable calls + 2 logged n=0 rows)`, which reconciles against nothing.** **Enumerated programmatically from the rows: ELEVEN rows — NINE gradeable calls plus TWO `n=0` NO-CALL rows.** ✅ **The 9 is confirmed twice by the section's own evidence — the `H2H right?` string ✅ ❌ ❌ ✅ · ✅ ✅ ❌ ❌ ❌ carries nine marks (4 right, 5 wrong) and the heading reads `4/9`.** ⛔ **The `4/9` tally, the confirm/override split (2/3 and 2/6) and every row were left exactly as published — only the prose counter moved.** ⚠️ **Rule restated in place: a gradeable count reconciles against the RESULT STRING and the `x/y` HEADING, never against another prose number (ledger rule 45 / pre-publish check 28).** ⚠️ 🆕 **An ARITHMETIC NOTE was added beside the n=18 Brier block: every span, spread and margin on this page is computed on UNROUNDED Brier values and differs in the last digit from the 4-dp tables above them — `0.0059` against a printed `.1945 − .1887 = .0058`, and `0.0094` against a printed `.2338 − .2245 = .0093`.** ⛔ **That is display rounding, not a defect: NO BRIER FIGURE WAS CHANGED, and none may be recomputed from the printed 4-dp cells.** ⛔ **NO ROW, TABLE, BUCKET, TALLY, REFUTATION, PROGRESS COUNTER OR EARLIER CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED apart from the one struck progress line, which is struck and restated in place. T15 stands at 31 carded plays / 100, argmin `w = 1.00`, margin 0.0094, THE 50/50 UNTOUCHED; T11 stands at 25 / 40 distinct starts; rule 50 at 4/9; rule 51 at 2 clean / 1 confounded; rule 53 at 2 of 6; TABLE M at 1 slate / 32 plays.** ⚠️ **Merged, not rewritten: `project_read` → verbatim transcript extraction → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check (ZERO lines lost) → `project_info` `created_at` compared immediately before upload → upload with `local_path`.**
- **Aug 24 2026, 7:30am scheduled run — the machine card arrives, and the discipline of the run is what it did NOT do.** 🤖 🆕 **A TABLE M ACCUMULATOR SECTION WAS CREATED for `picks/2026-08-23.json` (32 plays, 15/32; 8 pairs, 4/8 all inside band).** ⛔ **NOTHING ABOVE THAT HEADING WAS TOUCHED.** 🔴 **T15 WAS NOT RESTATED — no TABLE A play was carded on 8/23, so the carded denominator did not move: it stands at 31 / 100, argmin `w = 1.00`, margin 0.0094, MARGIN leg cleared and `n` leg failed, THE 50/50 UNTOUCHED.** ⛔ **Folding TABLE M's 32 rows in would have taken it past 60 in one night and silently re-specified a pre-registered test.** 🔴 **RULE 35 GAINED NOTHING AND THAT IS DELIBERATE — the merge stays at 185 rungs / 25 distinct starts, T11 progress 25 / 40.** ⛔ **The 8/23 board carries 17 distinct starts with full Hard Rock ladders and would have moved T11 to 42 overnight; it is NOT merged, because T11's `n` is CARDED arms and the machine board is every qualifying starter. Changing the population under a live pass criterion is the specification shopping this register exists to prevent.** ➡️ **A machine shadow ladder must be PRE-REGISTERED in `claude/owed-tests.md` first, interactively.** 🆕 **RULE 50 / RULE 51 OBSERVATIONS FROM THE MACHINE CARD LOGGED IN THEIR OWN TALLY — matched class 15/32, head-to-head 4/14 with 18 n=0 NO-CALL rows (14 + 18 = 32 ✅), and the FIVE rows where the two flatly disagreed itemised.** ⛔ **The hand-carded rule-50 accumulator is UNTOUCHED at 4/9: `card.py` prints these columns on every row, which is not rule 50 FIRING — rule 50 is a tiebreaker triggered by a contradiction.** ⚠️ **Strip the one row whose class sits exactly on 50.0% and the conflicts split 2–2; thirteen of the fourteen head-to-head samples are n=1.** 🔴 🆕 **A PRE-PUBLISH CHECK 36 DEFECT IS RECORDED AGAINST THE CODE: `card.py` prints rule 50's head-to-head on every row and NEVER prints rule 51's GAP IN DAYS, so check 36 cannot pass on a machine card by construction. Nine of the 32 rows carry a prior meeting and not one states how long ago.** ⛔ **REPORTED, NOT FIXED — a grading run does not touch the code and a headless session can neither test nor push a change. The rule 51 accumulator gains NO rows: the gap is not recoverable from the card.** 🟡 **THE `carried` SHADOW LOGGED FOR TABLE M: it differed on 3 of 32 rows (all T22) and was WORSE — Brier .2763 against the blend's .2752 overall, and .2313 against .2194 on the three rows that differ.** ⛔ **Three rows, two of them the same pitcher on the same night. T22 is neither adopted nor rejected.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY, REFUTATION, PROGRESS COUNTER OR CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of one new section and this entry, and the `collections.Counter` line-loss check reports ZERO lines lost.** ⚠️ **Merged, not rewritten: `project_read` → local file → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check → `project_info` `created_at` compared immediately before upload → upload with `local_path`.** ⚠️ **The local copy was verified before patching: TWO INDEPENDENT `project_read` transcriptions, each made by a separate agent from its own fresh read, written to separate files and diffed byte-for-byte (72,165 bytes, 626 lines, IDENTICAL).**
- **Aug 23 2026, 7:30am scheduled run — the 8/22 slate, and every accumulator on this page moved.** ✅ **RULE 15: the 8/22 block is a READ, appended from `claude/pick-ledger.md` 8/22 TABLE A — and audited anyway.** 🔴 **All 13 raw denominators were RE-DERIVED FROM PRIOR STARTS ONLY off freshly pulled game logs and all 13 reproduce the card exactly (14/14, 22/24, 16/18, 12/14, 20/23, 13/19, 15/19, 13/19, 12/15, 8/13, 16/20, 8/13, 11/23), with `0.5×model + 0.5×raw` reproducing every published blend to ≤0.06 points.** ⚠️ 🔴 **The "closer" column is now demonstrated to be the biased statistic this page condemns: three slates, and it has tracked the day's win rate every time — raw on 8/20 (9/12), raw on 8/21 (6/8), and MODEL on 8/22 (6/13), purely because model was the LOWER number on a losing night.** 🔴 **T15 BRIER RESTATED ON 31 CARDED PLAYS: the argmin has moved 0.7 → 0.74 → 1.00 and landed on the BOUNDARY of the parameter space, at Brier .2245 against .2338 at the shipped 0.5 — a margin of 0.0094.** ⚠️ 🆕 **THE MARGIN LEG (≥0.005) CLEARS FOR THE FIRST TIME. THE `n` LEG DOES NOT (31 against 100).** ⛔ **THE 50/50 IS NOT TOUCHED** — and the mechanism is recorded so the number is not misread: raw was the more optimistic estimate on 10 of 13 plays and the card went 6/13, so pure model wins this Brier for being lower on a bad night, not for being better calibrated. **An argmin at the edge of the space is a warning, not a finding.** 🆕 **RULE 35: 8/22 pass added — 54 rungs across 7 NAMED distinct starts, `E[K]` INVERTED from each play's logged `model` probability.** ✅ 🔴 **THE INVERSION IS VALIDATED SIX WAYS, not once as on 8/21: Cease 7.97, Skubal 7.15, Scott 5.96, Jones 5.31, Weathers 5.06 and Brown 5.27 all reproduce the `E[K]` figures the ledger prints independently — plus an internal cross-check no earlier pass could run, Jared Jones inverted from TWO carded rungs giving 5.308 and 5.303.** ⛔ **Irvin and M. Pérez are EXCLUDED and named: outs-only plays have no `E[K]` to invert. `n = 7`, not 13 and not 9.** 🔴 **MERGED PURE-MODEL ACCUMULATOR REBUILT AT 185 RUNGS / 25 DISTINCT STARTS, again licensed by regenerating the earlier slates first** — 8/20 reproduces its published table on all 7 rows, and 8/21 reproduces on all 7 **once ONE boundary rung is placed as published**: Detmers' 6.5 regenerates at 40.012% from his printed 2-dp `E[K]`, while the published pass had it just below 40. ⚠️ **That is this page's own header rule 1 firing in practice, and it is recorded rather than silently absorbed; the rung is a MISS either way so no `actual` moves.** 🔴 **AND T11's HYPOTHESIS HAS NOW TURNED OVER: the 20–40% bucket that read 29.6 / 47.4 on 8/20 alone reads 29.5 / 25.6 at 25 starts, and 60–70% and 70–80% are both now slightly OVER-confident — the direction the carded calibration table has said all along.** ⛔ **T11 is NOT re-decided and its pass criterion is untouched. T11 progress: 25 / 40 distinct starts.** 🆕 **RULE 50 ACCUMULATOR: five gradeable calls added plus two n=0 rows logged with NO CALL. Running 4/9 — confirms 2/3, 🔴 OVERRIDES 2/6.** 🔴 **The strongest pattern in nine plays is not about rule 50 at all: THE MATCHED CLASS HAS NOW BEATEN THE HEAD-TO-HEAD THREE TIMES OUT OF THREE when they flatly disagreed (Schlittler, Skubal u8.5 K, Irvin u15.5 outs), every one of those H2H samples being n≤5 and two of them n=1.** ⛔ **Three instances. Nothing is demoted, re-weighted or rewritten.** ⚠️ **One honest qualifier is attached to the Irvin row: the class figure he was judged against was itself biased (T23) and matched on the wrong axis (T24), so "the class was right" is true about the outcome and false about the published reasoning.** 🆕 🔴 **RULE 51 GETS ITS FIRST TWO CLEAN INSTANCES — AND THE WAY THEY WERE FOUND IS A PRE-PUBLISH CHECK 36 FAILURE ON THE 8/22 CARD.** **Ryan Weathers and Dylan Cease had BOTH faced their 8/22 opponent on 2026-08-16 — six days — and NEITHER CARD ROW STATED THE GAP.** ⚠️ **Rule 50's head-to-head was run and printed on both; rule 51's ≤30-day check was not. Reading the same game log for one is not running the other.** ⛔ **Nothing about the card is re-graded for it — rule 51 is EXPLORATORY and was never entitled to move a number.** ⚠️ **The two instances POINT OPPOSITE WAYS: Weathers MISSED at a 4+ K bar after a 4-K meeting, Cease HIT at a 7+ K bar after a 10-K meeting — the exact "strong first meeting" conditional the exploratory finding is about, cleared at a bar two strikeouts higher.** ⛔ **n = 2. Log, do not conclude; the pre-registered specification stays FAILED and closed.** 🆕 **RULE 53 ACCUMULATOR: the first two flags that were RIGHT — Irvin's matched-class flag and Skubal's pitch-count price flag — both bet by Sam, both LOST. Running: the flag predicted the outcome in 2 of 6.** ⚠️ 🔴 **The Irvin row is recorded as the most instructive entry on the page BECAUSE THE FLAG LANDED FOR A REASON ALREADY SHOWN TO BE WRONG: on the corrected T23/T24 figure of 66.7% the check would not have fired at all. Score the CHECK, not the play.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY, REFUTATION OR CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — the 18-start merged table is KEPT and marked superseded rather than replaced, and this write is otherwise a PURE INSERTION apart from three progress counters (`18 carded plays / 100`, `4 instances`, `0 clean instances / 1 confounded`), each replaced by its own successor block.** ⚠️ **Merged, not rewritten: `project_read` → local file → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check → `project_info` `created_at` compared immediately before upload → upload with `local_path`.** ⚠️ 🆕 **The local copy was verified before any patch: TWO INDEPENDENT transcriptions of the `project_read` result were written to separate files and diffed byte-for-byte (43,963 bytes, 423 lines, identical).**
- **Aug 21 2026, 7:30am run** — 🆕 **Doc created.** First itemised rule-35 pass: **83 rungs across 12 named starts**, superseding the un-itemised "40 across six evening arms." First rule-15 scoreboard ever built — **and it required reconstructing model and raw from scratch, because the card logs only the blend.** 🔴 **Brier surface over the blend weight is flat to 4 dp at n=12: the weight is unidentifiable and the 50/50 must not be touched.** 🔴 **Flagged that the "closer to outcome" tally is win-rate-biased and is the wrong statistic to fit a weight to.**
- **Aug 21 2026, evening — audit + two new accumulators.** 🔴 **Corrected two counts in the rule-15 "biased statistic" paragraph that did not reconcile against the table immediately above them:** the slate is **9/12, not 10/12** (W/L column reads 9 W, 3 L), and raw was the higher estimate on **8 of 12, not 7** (the 7 is the *closer* column). **Both corrections are struck through, not deleted, and the argument is unaffected.** ✅ **Re-derived BOTH rule-35 bucket tables from the itemised rungs, 83/83, and they are CORRECT AS PRINTED** — two reported errors (**pure model 20–40/40–60 "should be 20/12"** and **blend 80–90% "should be 8 starts"**) were **checked and REFUTED**, with the refutations filed in place so the next run does not re-find them. 🔴 **Root cause of both false alarms: bucketing on the PRINTED integer rung values, which were bucketed UNROUNDED.** 🔴 **Added a header rule: recount every bucket from the itemised rows, recover the unrounded value first, and treat a printed `n` as a claim rather than a source.** 🆕 **Created the RULE 50 accumulator (head-to-head tiebreaker), seeded with the three 8/21 calls — E. Rodríguez u5.5 K vs CIN, Cam Schlittler o4.5 K vs TOR, Sonny Gray o4.5 K vs SF — all ungraded.** 🆕 **Created the RULE 51 accumulator (rematch haircut), seeded with Hunter Dobbins o3.5 K vs PHI, 11 days after a 6 K meeting on 8/10, ungraded** — **with the pre-registered mean-K specification recorded as FAILED (drop 0.30 K, t=−1.78) and the threshold version marked EXPLORATORY.**
- **Aug 22 2026 — 8/21 slate graded; rule 50 graded, rule 51 confounded, rule 53 created.** 🔴 **RULE 50 DEBUTS AT 2/4** (`n = 4 distinct plays`) — E. Rodríguez ✅ (4 K, under 5.5, a *confirmation*), Sonny Gray ✅ (6 K, an *override* that was right), Schlittler ❌ (4 K), Yamamoto ❌ (9 K). **Overrides alone are 1/3.** ⚠️ **Yamamoto was NOT in the 8/21 seed table and was added at grading; the row says so.** 🔴 **Recorded the project's FIRST direct head-to-head-vs-class conflict: on Schlittler the H2H (7/7/7) and the matched class (18/29) flatly disagreed and THE CLASS WON.** ⛔ **One start — nothing re-ordered, nothing re-weighted; noted only that rule 15 also debuted at 1/4 and neither may be re-tuned off one slate.** ⛔ **RULE 51's single instance (Dobbins o3.5 K vs PHI) LOGGED AS CONFOUNDED AND EXCLUDED FROM THE TALLY** — he left injured on the first pitch of the 5th, which is a different failure than the rematch haircut; **counter-note recorded that he was not cruising either (78 pitches, 19 BF, 3 ER, 6.75 K/9 vs an 8.82 season rate), so the injury cost equity, not a won ticket.** **Rule 51 stands at 0 clean instances / 1 confounded.** 🆕 **Created the RULE 53 accumulator — plays SHOWN-BUT-FLAGGED rather than removed**, per Sam's standing instruction of 8/22 that his job is to decide and Claude's is to provide the data; **seeded with the four 8/21 plays Claude argued against on price (Yamamoto −300, Gray −230, Burke −1000, Chandler −160) — all four won, five of Sam's six won** — **with both sides stated: the break-even logic is defensible and n=6 on one slate is not a finding.**
- **Aug 22 2026, 7:30am scheduled run — the first rule-15 block that is a READ, and one added slate erased T11's headline.** ✅ **8/21's rule-15 scoreboard APPENDED FROM THE LEDGER, not reconstructed** — ledger rule 41 / check 26 landed and the card logged `model` and `raw` as their own columns. 🔴 **AUDITED ANYWAY: all nine relevant pitchers' full statsapi game logs re-pulled, and all 8 raw denominators reproduce the card exactly (24/26, 11/12, 17/21, 20/26, 20/25, 20/23, 17/22, 19/22), with `0.5×model + 0.5×raw` reproducing every published blend to ≤0.05 points.** ✅ **T15's Brier accumulator RESTATED ON CARDED PLAYS ONLY, exactly as that entry pre-registered before today** — the two 8/20 conversational plays (G. Williams, G. Rodriguez) are named and removed, and the counter reads **18 carded / 100**. 🔴 **The weight is still unidentifiable: argmin w = 0.74 at Brier .1879 against .1886 at the shipped 0.5 — a margin of 0.0007 against a bar of 0.005, at n=18 against a bar of 100. FAILS BOTH LEGS. The 50/50 is not touched.** ⚠️ **The surface is no longer flat to four decimals (spread 0.0059 vs 0.0011 at n=12) — it has a shape, which is not an identification.** ⚠️ **Provenance caveat recorded: the 8/20 half of the Brier accumulator is RECONSTRUCTED and only the 8/21 half is LOGGED.** 🆕 **RULE 35: 8/21 pass added — 48 rungs across 6 NAMED distinct starts, `E[K]` INVERTED from each play's logged `model` probability rather than rebuilt from the formula, and the inversion validated by reproducing Misiorowski's independently published `E[K]` of 7.69 exactly.** ⛔ **Sale and Yamamoto are EXCLUDED and named: their carded `model` is an OUTS probability, so there is no `E[K]` to invert, and reconstructing one would put a rebuild inside a read. `n = 6`, not 8.** 🔴 **MERGED PURE-MODEL TABLE BUILT — 131 rungs, 18 distinct starts — after regenerating 8/20's pure-model rungs from its own printed `E[K]` values and reproducing the published table on all 7 rows / 83 rungs. The merge was conditional on that check passing.** 🔴 **AND THE RESULT CUTS AGAINST T11: the 20–40% bucket that read 29.6% predicted vs 47.4% actual on 8/20 now reads 29.5% vs 30.0% merged, and 60–70% went 64.8/85.7 to 64.9/63.6. The under-confidence signal did not survive a second slate.** ⛔ **T11 is NOT re-decided and its pass criterion is untouched — the evidence is simply recorded as it now stands.** ⚠️ **8/21 alone reads badly OVER-confident from 20–70%, the exact mirror of 8/20, because four of six arms struck out exactly 4 and every rung above 4.5 missed at once.** ⛔ **THE BLEND TABLES ARE DELIBERATELY NOT MERGED** — it needs 8/20's per-rung RAW rates, which are not on this page, and re-deriving them from the printed blend integers is forbidden by this doc's own header rule 1. **T11 progress: 18 / 40 distinct starts.** ⛔ **NO EXISTING ROW, TABLE, BUCKET, TALLY OR CHANGELOG ENTRY WAS ALTERED, REORDERED OR DROPPED — this write is a PURE INSERTION of three blocks.** ⚠️ **Merged, not rewritten: `project_read` → local file → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check (zero lines lost) → upload with `local_path`.** ⛔ **Rule 50, rule 51 and rule 53 gained NOTHING this run and were not touched: no new play was graded on 8/22, so there was no observation to add.**
