# MLB pitcher database — 2026

## ✅ REFRESHED Aug 21 2026, 12:30am ET — complete through the 8/20 slate

> # 🔴 STALE — ~~TEN COMPLETED SLATES BEHIND AS OF 2026-08-31~~ ~~**SEVENTEEN COMPLETED SLATES BEHIND AS OF 2026-09-07.**~~ **THIRTY-ONE COMPLETED SLATES AND ~840 STARTS BEHIND AS OF 2026-09-21.** AN INTERACTIVE SESSION MUST RUN THE RECIPE.
>
> 🆕 🔴 **RE-MEASURED 2026-09-21, Monday sweep. Built through the 8/20 slate on 3,838 starts; 31 slates (8/21–9/20) have been played since — 32 days. Season population through 9/20 ≈ 4,678 starts, so the table is SHORT BY ~840.** ✅ **BOUNDED FROM ENUMERATED ROWS, NOT FETCHED, TWO WAYS: (1) the 2026-09-14 anchor of 4,460 through 9/12 + 109 games enumerated slate by slate from the repo's `data/<date>/results/final.json.gz` for 9/13–9/20 (15 · 10 · 15 · 15 · 9 · 15 · 15 · 15, every `n_final` = `n_games`, zero domain violations) × 2 = 4,678. (2) `data/latest/pitchers.json.gz` (`pulled_at 2026-09-21T10:02:56Z`, `n_failed: 0`, `domain_violations: 0`) enumerates 4,601 started rows through 9/20 under `min_ip >= 20` — home 2,300 / road 2,301 — and its per-player `gs` fields sum to the same 4,601; a 77-row filter gap against route 1, against 78 at 9/12.** ✅ **Plausibility bound: 840 starts / 31 slates = 27.1 a slate ≈ 13.5 games, inside the 9–15-game slates enumerated. It exceeds this table's 3,838 and not implausibly.** ⛔ **No statsapi population call was made and no fetched figure is asserted. 9/21 is unplayed and not counted.**
>
> ✅ 🆕 **THE ACCEPTANCE TEST, RE-DRIVEN RATHER THAN RE-READ: recomputing from the repo's own per-start log through 8/20 with the SAMPLE SD (n−1) reproduces Misiorowski `0.2522 / 0.1739` (n 23) and Gilbert `0.2890 / 0.1324` (n 25) — the published `0.252 / 0.174` and `0.289 / 0.132`. The population SD gives Misiorowski `cvO 0.1700`, which is the √(n/(n−1)) failure this doc warns about.** ➡️ **So a headless rebuild from that file would pass the gate — but a Monday sweep verifies, it does not rebuild, and the `min_ip` caveat below still applies.** ✅ **Published table re-verified: 185 rows · `sum(n)` 3,403 · min n 8 · no duplicate names · 10 pipes on every row.** ⚠️ 🆕 **AND SEE THE HEADLESS QUALIFICATION BELOW — "a scheduled run cannot fix this" is TOO BROAD as written.**
>
> 🆕 🔴 **RE-MEASURED 2026-09-07, Monday sweep. THE GAP HAS NEARLY DOUBLED SINCE 8/31.** **This table is built through the 8/20 slate on 3,838 starts. SEVENTEEN slates have been played since — 8/21 through 9/6 — and the season population through 9/6 is 4,308 starts, so it is SHORT BY 470 STARTS.**
>
> ✅ 🔴 **AND THE POPULATION IS NOW *VERIFIED*, NOT MERELY BOUNDED — THREE INDEPENDENT ENUMERATED ROUTES AGREE.** **(1) `claude/mlb-opponent-database.md`'s 2026-09-06 verification puts the true season population through 9/5 at 4,278, closed three ways with no residue and confirmed member-for-member across 30 enumerated standings rows; the 9/6 slate is 15 games, every one `Final`, enumerated from `data/2026-09-06/results/final.json.gz`, so 4,278 + 30 = 4,308.** **(2) `data/latest/pitchers.json.gz` in `github.com/smh0602/gizmos-picks` (`pulled_at 2026-09-07T10:07:51Z`, `n_failed: 0`, `domain_violations: 0`) enumerates 4,221 started rows through 9/6 under its `min_ip >= 20` filter — and the same file enumerates 3,775 through 8/20 against this table's unfiltered 3,838, so the filter drops 63 there and 87 here, which is the right direction and the right magnitude for September call-ups.** **(3) home 2,112 / road 2,109 across those rows — every game produces exactly one of each, so the 3-row gap is the filter and nothing else.**
>
> ✅ **SANITY BOUND, RUN BEFORE THE FIGURE WAS BELIEVED: it must exceed this table's 3,838 and must not exceed it implausibly. 470 starts over 17 slates is 27.6 starts a slate ≈ 13.8 games a slate, inside the 9–16 game slates the repo actually recorded (9/3 was 9 games, 9/4 was 16).** ⛔ **8/31's 12 games ARE counted — `n_final: 12`; 9/7's 11 games read `n_final: 0` and are NOT.**
>
> ⚠️ 🔴 **WHAT THAT COSTS, STATED RATHER THAN WAVED AT: the model inputs are `mK8` and `mO8` — the TRAILING EIGHT starts. ~~Ten~~ **SEVENTEEN** missed slates means a regular starter has made roughly ~~TWO~~ **THREE TO FOUR** turns that are not in his trailing eight, so for many arms the eight-start window this table publishes is not the eight-start window the model is supposed to read.** ⛔ **That is a bigger error than a stale season mean, and it is invisible on the page.**
>
> ✅ **THE PUBLISHED TABLE ITSELF IS INTERNALLY SOUND AND WAS RE-VERIFIED THIS RUN: 185 rows · `sum(n)` = 3,403 · ZERO rows below n≥8 · no duplicate names · and BOTH acceptance-test pitchers reproduce to four decimals (Misiorowski `0.252 / 0.174`, Gilbert `0.289 / 0.132`), so the sample-SD (n−1) convention is intact.** ⛔ **It is not corrupt. It is OLD, which is a different problem and is not fixable by a scheduled run.**
>
> 🔴 ~~**HOW THE POPULATION WAS BOUNDED, BECAUSE IT WAS NOT FETCHED:** `statsapi.mlb.com` **is unreachable from a scheduled cloud run** (`connect_rejected` at the egress proxy), so no season-population call was made and **no fetched figure is asserted.**~~ 🔴 **STRUCK 2026-09-07 — THE BLANKET UNREACHABILITY CLAIM WAS STRUCK PROJECT-WIDE ON 2026-09-01 AND THIS COPY SURVIVED IT.** **`claude/betting-project-instructions.md` v5.3 records that `WebFetch` DOES reach `statsapi.mlb.com` from a scheduled run; what is closed is the CONTAINER'S OWN direct egress.** ✅ **The CONCLUSION is unchanged and the figure above is still not a fetched one — the one route a scheduled run has to statsapi is the route this project BANS for data — but the REASON matters, because "unreachable" invites a future session to declare the blocker gone the day the egress opens.** ✅ **The bound is built from ENUMERATED ROWS only: 4,086 starts through 8/29 — the 8/30 grading run's standings-authority figure, W=L control 2,043/2,043, independently reproduced by 834 enumerated season values across 347 starters — plus 28 started pitchers enumerated one by one out of `data/2026-08-30/results/final.json.gz` in the collector's repo (14 games, `n_final: 14`).** **8/31's 12 games read `n_final: 0` and are NOT counted.**
> **Sanity bound: 276 starts over 10 slates is 27.6 starts a slate ≈ 13.8 games a slate, inside the 12–17 game slates the repo actually recorded. The gap exceeds this table's own count and does not exceed it implausibly.**
>
> ⛔ ~~**A SCHEDULED RUN CANNOT FIX THIS.**~~ 🔴 **TOO BROAD — QUALIFIED 2026-09-07, AND THIS IS THE SAME ERROR SHAPE THAT COST THIS PROJECT A MONTH OF RE-FITS.** **`claude/mlb-projection-model.md` v5.0 established the standing rule — before declaring a headless run blocked on data, `ls data/latest/` in the repo — after THREE consecutive scheduled runs wrote "the re-fit cannot run headless" while the file it needed sat in the repo they were already cloning.** `[measured 2026-09-07]` **`data/latest/pitchers.json.gz` carries the full per-start game log — `d`, `o` (opponent), `h` (isHome), `gs`, `outs`, `k`, `np`, `bf` — for every arm, and 4,221 started rows were enumerated from it headless in this run. THAT IS THIS TABLE'S INPUT.**
>
> ⚠️ 🔴 **BUT IT IS NOT THE SAME POPULATION AS THE RECIPE, AND THE DIFFERENCE IS STATED RATHER THAN GLOSSED: the repo file applies `min_ip >= 20`, a SEASON-TOTAL sample filter.** **At n≥8 that drops almost nobody — the arms it would drop are the OPENERS this doc already says to exclude (Braydon Fisher at `mO` 3.38 over 8 starts is ~9 IP; PJ Poulin at 4.09 over 11 is ~15 IP) — but it is a real difference and a rebuild from it must SAY SO on the page.** ⛔ **It is emphatically NOT a substitute for THE RECIPE where a POPULATION-SCALED quantity is involved: `claude/mlb-opponent-database.md`'s centering constant is defined on the UNFILTERED population, the runner already computes a different one (4.756 on 4,164 IP-filtered) from this very file, and that doc is right to say its own rebuild needs THE RECIPE. ⛔ NEVER MIX THE TWO SCALES.**
>
> ➡️ ⛔ **NOT DONE THIS RUN, AND DELIBERATELY: a Monday sweep verifies and reports, it does not rebuild a data table, and its own prompt forbids it.** **THE HANDOVER: run THE RECIPE at the top of the next interactive session, and reproduce Misiorowski `0.252 / 0.174` and Gilbert `0.289 / 0.132` to four decimals BEFORE trusting the rebuild.** ✅ **If a future session rebuilds from the repo file instead, the same two acceptance rows still gate it, and the `min_ip` caveat above goes on the page.**

**Source:** `statsapi.mlb.com` game logs for all **340 pitchers** who started a 2026 game — **3,838 starts, zero failed fetches, 6.5 seconds.** Free, no API credits. Recipe in `claude/mlb-data-stack.md`.

✅ **Reconciles exactly:** 3,820 starts through 8/19 **+ 18** (9 games × 2 starters on 8/20) = **3,838**, and the summed `gamesStarted` across all 340 starters equals 3,838 independently.

**185 starters at n≥8, median n = 19.** Unchanged in count from the Aug 20 build; **17 rows moved** (the 8/20 starters who clear n≥8 — Dobnak is still below it at n<8).

⚠️ 🔴 **THE HEADLINE 3,838 IS THE BUILD POPULATION, NOT THE PUBLISHED TABLE. THEY DO NOT MATCH AND ARE NOT SUPPOSED TO.** The build covers **340 starters / 3,838 starts**; the table below **publishes only the 185 arms at n≥8**, whose `n` column sums to **3,403**. The missing **435 starts** belong to the **155 starters under n≥8** who are computed but not printed. ➡️ **Verifying this doc against the table means checking `sum(n) = 3,403` over 185 rows. Verifying it against the SEASON means re-running the pull and checking 3,838 over 340 starters** (`claude/mlb-opponent-database.md` cross-checks the same 3,838 by two further routes). ⛔ **A run that sums the printed `n` and reports a 435-start shortfall has found the n≥8 cutoff, not a bug.**

## 🔴 METHODS — `cv` USES THE SAMPLE SD (n−1). DO NOT CHANGE IT SILENTLY.

`[measured] Aug 21` **A refresh built on the POPULATION SD (÷n) reproduced a table that looked right and was wrong in every row.** Misiorowski came out `cvK 0.247 / cvO 0.170` against the published `0.252 / 0.174`; the whole table shifted by a factor of `√(n/(n−1))`.

**This matters because `cvO` is not decorative — it IS the outs distribution.** The card prices outs as `Normal(mu, SD = cvO × season mean outs)`, so a 2% shift in `cvO` moves every outs probability on every card.

✅ 🔴 **CAVEAT DISCHARGED 2026-09-01 — T3 RAN ONCE, EXACTLY AS PRE-REGISTERED, AND PASSED ON ALL THREE CRITERIA.** ~~**CAVEAT, AND IT IS A BIG ONE: THE `Normal(mu, cvO × mO)` ASSUMPTION HAS NEVER BEEN FITTED.**~~ `[measured 2026-09-01, n = 3,084 standardised residuals]` **mean +0.0543 · SD 1.0772 · q10 −1.3528 · q90 +1.3356 — every one inside its pre-registered bar.** **The assumption every outs probability this project has ever quoted rested on is now a MEASUREMENT. Full result in `claude/mlb-projection-model.md`; the register entry is CLOSED-PASSED.** ⚠️ **Read the residual SD honestly: at 1.077 the tails are ~8% FATTER than Normal, so a quoted outs probability is very slightly over-confident at the extremes — worth nothing on a 15.5 rung, worth naming on a far alt rung.** ⛔ **The paragraph below is kept as the RECORD of what was believed before the test, and its narrow point still stands: the ✅ reproduction checks validate the SD CONVENTION and nothing else.** ⛔ **The ✅ checks above validate the SD *convention* — that `cv` is computed with the sample SD (n−1) — and NOTHING ELSE.** They say the number is computed the way we said we would compute it. **They do not say the outs distribution is Normal, that its SD is `cvO × mO`, or that the resulting probabilities are calibrated.** ➡️ ~~**The distributional form is an OWED TEST — see `claude/owed-tests.md`.**~~ 🔴 **STRUCK 2026-09-07 — T3 is CLOSED-PASSED (2026-09-01). See the block above.** Outs are bounded below at 0, censored by the hook, and visibly left-skewed (that is exactly what the `tail` column measures), **none of which a Normal has.** ⛔ **Do not cite the reproduction checks as evidence that outs pricing is validated. A correct input to an unfitted model is still an unfitted model.**

✅ **Convention confirmed by spot-check against the published Aug 20 values:** sample SD reproduces Misiorowski `0.252 / 0.174` and Gilbert `0.289 / 0.132` **exactly.** ⛔ **Any future rebuild must reproduce those two rows before the table is trusted.**

✅ **This build was verified against the browser's authoritative computation on 12 aggregate checksums** — character count, row count, and the summed `n · mK · mK8 · mO · mO8 · cvK · cvO · mNP · tail`, plus the left-hander count. **All 12 matched.**

## Columns

`name | hand | n | mK | mK8 | mO | mO8 | cvK | cvO | mNP | tail`

| | |
|---|---|
| `n` | full-season starts |
| `mK` / `mO` | season mean strikeouts / mean OUTS (not innings) |
| `mK8` / `mO8` | mean over his **last 8 starts** — **this is the model input** |
| `cvK` / `cvO` | coefficient of variation, **sample SD ÷ mean** |
| `mNP` | mean pitches per start — feeds the previous-start term, β=+0.037, t=5.51 |
| `tail` | share of starts more than 2 sample-SD BELOW his own mean outs — the blow-up rate |

## How to read it

🔴 **`mK8` and `mO8`, not `mK` and `mO`, are the model inputs.**

🔴 **Low `cvO` at low `n` is still fake consistency.** Two corrections from the full-season rebuild stand:

- **Max Scherzer** was written up at **CV 0.10 on n=4** as the canonical fake-consistency case. On the full season (**n=11**) his `cvO` is **0.398** — among the highest on the board. ✅ The warning was right; the example was upside down.
- **Aaron Nola** was flagged as the CV blind spot — "0.13 CV but an 11.1% tail rate." On the full season (**n=26**): `cvO` **0.156**, `tail` **0.000**. **No 2σ collapses all year.**

⚠️ **Sandy Alcantara** holds up as *mid-pack*, not extreme: `cvK` 0.419 against a board median around 0.44. His **outs** are the steadiest thing about him (`cvO` 0.156, `mO` 19.63 — ~~deepest workload on the board~~ 🔴 **SECOND-deepest on the board, behind Yoshinobu Yamamoto at `mO` 19.82**; then Logan Webb 18.95, Michael Wacha 18.68). **Bet his outs, not his Ks.**

🔴 **`[corrected 8/21]` "Deepest workload on the board" was FALSE against this doc's own table** — Yamamoto's 19.82 is printed 70 rows above it. ⚠️ **The point being made survives: what makes Alcantara the outs bet is the LOW `cvO` (0.156) at a high `mO`, not a depth record he does not hold** — and Yamamoto's `cvO` is 0.158, essentially the same, on a deeper mean. ⛔ **Check every superlative in this doc against the column it claims to top before repeating it.**

⚠️ **The bottom two rows are openers, not starters.** Braydon Fisher (`mO` 3.38) and PJ Poulin (4.09) cleared n≥8 on one-inning "starts." **Exclude anything with `mO` under ~9 before modelling.** Griffin Jax (`mO` 13.78, `mNP` 68) and Ryan Gusto (`mNP` 66) are borderline piggyback arms.

⚠️ `cvO` board median is **0.204**. Above ~0.28 is genuinely volatile.

## 🔴 Biggest movers on the 8/20 refresh

| Pitcher | Was | Now | Why it matters |
|---|---|---|---|
| **Gavin Williams** | mK8 **9.13** | **9.75** | 11 K on 8/20. **The highest trailing-8 on the board** — at β=0.673 that is +0.42 K on every projection |
| **Gerrit Cole** | mK8 7.25 · mO8 18.38 | **7.38 · 18.75** | 8 K in 6.0. Still the deepest-trending arm carded this week |
| **Kyle Bradish** | mK8 **3.75** | **4.13** | 5 K. ⚠️ **The u5.5 edge that read +19.3 points narrows as his trailing 8 rises. Re-price before carding it again.** |
| **Peter Lambert** | mK8 6.13 · mO8 16.63 | **5.75 · 15.88** | 3 K in 3.2 IP, 9 ER. **`tail` went 0 → 0.045 — his first 2σ collapse of the season** |
| **Grayson Rodriguez** | mK8 4.00 · mO8 13.38 | **4.63 · 15.13** | 7.0 IP shutout. **mO8 up 1.75 outs — the u15.5 that lost is now priced very differently** |
| **Landen Roupp** | mK8 4.13 | **3.88** | still falling |

---

```
Jacob Misiorowski|R|23|9.13|9|18.13|17.25|0.252|0.174|91|0
Dylan Cease|R|23|8.74|9.13|17.96|20.38|0.237|0.195|102|0
Gavin Williams|R|26|7.73|9.75|17.85|18.13|0.346|0.165|95|0
Jesús Luzardo|L|25|7.4|8.63|18.04|19.88|0.378|0.173|98|0.04
Chris Sale|L|22|7.27|7.63|17.59|16.88|0.295|0.166|94|0.045
Cam Schlittler|R|26|7.27|8.25|17.54|18|0.315|0.202|92|0.038
Cristopher Sánchez|L|26|7.19|6.38|18.65|16.75|0.352|0.187|95|0.038
Tarik Skubal|L|19|7.11|7.5|17.95|18|0.311|0.138|91|0
Zack Wheeler|R|21|6.86|7.5|17.19|15.13|0.381|0.233|93|0.095
Shohei Ohtani|R|14|6.79|6.63|18.36|18.25|0.318|0.082|95|0.071
Reid Detmers|L|25|6.68|6.88|17.16|16.25|0.388|0.203|92|0
Chase Burns|R|24|6.63|5.88|17|16.63|0.364|0.106|93|0
Paul Skenes|R|26|6.58|6.5|16.04|15.75|0.363|0.271|91|0.038
Jacob deGrom|R|24|6.54|6.38|15.83|14.25|0.369|0.232|88|0.042
Nolan McLean|R|25|6.48|6.13|17.12|17.75|0.325|0.165|94|0.04
Ian Seymour|L|11|6.45|7.5|14.09|15.25|0.477|0.3|77|0
Payton Tolle|L|21|6.38|7.5|17.14|17.13|0.445|0.214|86|0.048
Braxton Ashcraft|R|25|6.36|5.5|17.92|17.5|0.357|0.209|87|0.04
Taj Bradley|R|25|6.32|5.75|16.88|16.88|0.395|0.18|97|0
Logan Gilbert|R|25|6.28|6.25|18.04|18.88|0.289|0.132|94|0.04
Logan Henderson|R|12|6.25|6.5|15.83|17|0.298|0.231|79|0.083
Gerrit Cole|R|16|6.25|7.38|17.38|18.75|0.411|0.145|89|0.063
Nathan Eovaldi|R|22|6.23|6.75|18.09|17|0.384|0.182|91|0
Yoshinobu Yamamoto|R|22|6.18|6.25|19.82|20.13|0.359|0.158|98|0
Sean Burke|R|21|6.1|7.38|16.43|17.75|0.44|0.187|91|0
Kyle Harrison|L|20|6.1|5.63|14.75|14.5|0.57|0.253|85|0.05
Parker Messick|L|25|6.08|5.75|17.88|18|0.364|0.16|92|0
Max Meyer|R|20|6.05|5.88|16.65|16.63|0.254|0.179|89|0.05
Eury Pérez|R|22|6.05|6.5|16.73|18.75|0.377|0.174|91|0
Joe Ryan|R|23|6|5.75|16.39|16.25|0.379|0.265|91|0.043
Cade Cavalli|R|27|6|7.13|15.85|18.75|0.547|0.283|87|0.037
MacKenzie Gore|L|26|5.92|6.25|16.12|16.38|0.363|0.245|91|0.038
Ryan Weathers|L|24|5.83|5.25|16.75|17.13|0.37|0.251|92|0.042
Christian Scott|R|18|5.83|6.5|14.11|14.88|0.295|0.239|85|0.056
Drew Rasmussen|R|24|5.75|5.5|16.79|15.88|0.49|0.212|87|0.042
Spencer Strider|R|8|5.75|5.75|14.63|14.63|0.413|0.239|86|0
Bryan Woo|R|24|5.71|5.63|17.29|17|0.427|0.183|88|0.042
Sean Manaea|L|12|5.67|6.13|17|18|0.386|0.193|93|0.083
Kris Bubic|L|9|5.67|5.88|16.78|16.63|0.467|0.183|90|0
Cole Ragans|L|8|5.63|5.63|13.25|13.25|0.593|0.425|80|0
Aaron Nola|R|26|5.62|6.5|15.81|16.88|0.338|0.156|91|0
Carlos Rodón|L|10|5.6|5.75|15.1|15.88|0.269|0.167|89|0
Shota Imanaga|L|25|5.6|6|17.2|16.88|0.458|0.14|90|0
Hunter Brown|R|13|5.54|5|15.85|16.25|0.358|0.198|92|0.077
Bryce Miller|R|15|5.53|4.13|16.93|16.5|0.511|0.154|85|0
Jack Leiter|R|15|5.53|5|16|15.75|0.468|0.174|93|0
Connor Prielipp|L|17|5.53|5.63|15.47|16.5|0.384|0.137|89|0
Gage Jump|L|16|5.5|5.88|15.38|14.63|0.492|0.23|90|0
Kevin Gausman|R|26|5.5|5.38|16.54|15.88|0.437|0.2|93|0.038
Connelly Early|L|17|5.47|6|16.18|16.5|0.304|0.191|90|0
Peter Lambert|R|22|5.45|5.75|16.68|15.88|0.361|0.155|94|0.045
José Soriano|R|25|5.44|4.25|16.72|16.63|0.454|0.2|93|0.04
Luis Severino|R|12|5.42|5.13|15.67|16.25|0.488|0.322|91|0.083
Emmet Sheehan|R|20|5.4|5.5|14.3|13.5|0.414|0.273|85|0.05
Lance McCullers Jr.|R|8|5.38|5.38|14.75|14.75|0.444|0.266|87|0
Jack Flaherty|R|19|5.37|5.88|13.63|14.75|0.466|0.259|86|0.053
Jack Perkins|R|11|5.36|5.38|13.82|14.13|0.419|0.177|83|0
Joey Cantillo|L|26|5.35|6.25|14.5|13|0.446|0.277|84|0.077
Dean Kremer|R|10|5.3|4.63|16|15.88|0.378|0.177|86|0
Shane Baz|R|25|5.28|5.63|17.48|16.75|0.459|0.185|95|0.04
Max Fried|L|15|5.27|5.25|17.27|14.63|0.348|0.255|86|0
Foster Griffin|L|25|5.24|4.13|17.32|17.25|0.468|0.162|93|0
Brandon Woodruff|R|9|5.22|5.13|15.11|15.13|0.447|0.33|71|0.111
Troy Melton|R|14|5.21|6|18.07|17.5|0.406|0.163|89|0
Landen Roupp|R|25|5.2|3.88|16.16|17.13|0.364|0.223|95|0.04
Michael Soroka|R|17|5.18|4.13|16.24|16.13|0.526|0.283|85|0.059
Roki Sasaki|R|22|5.18|5.25|15.82|16.5|0.411|0.199|90|0.045
Emerson Hancock|R|23|5.17|4.75|16.7|16.13|0.514|0.207|87|0.043
Kyle Bradish|R|25|5.16|4.13|16.64|17.13|0.467|0.24|92|0
Ranger Suarez|L|22|5.14|4.75|15.45|13.75|0.504|0.264|83|0
Tyler Mahle|R|21|5.14|5.5|16.19|17.5|0.37|0.162|88|0
Shane Drohan|L|14|5.14|5.75|15.79|17.38|0.395|0.197|84|0.071
Jared Jones|R|14|5.14|5.88|13.71|14.63|0.357|0.219|75|0
Ben Brown|R|8|5.13|5.13|15.88|15.88|0.32|0.195|75|0
Noah Cameron|L|23|5.13|5.38|17.13|19.25|0.503|0.238|94|0
Spencer Arrighetti|R|17|5.12|5.13|15.53|13.88|0.498|0.295|88|0.059
Walbert Ureña|R|21|5.1|5|15.86|15.38|0.316|0.199|89|0.048
Sonny Gray|R|23|5.09|5.25|17.3|18.38|0.523|0.202|84|0.043
Trey Yesavage|R|18|5.06|4.75|15.61|14.5|0.491|0.299|86|0.111
Will Warren|R|24|5.04|4.63|15.17|14|0.501|0.207|87|0
Griffin Jax|R|18|5|6.75|13.78|16|0.513|0.253|68|0.056
Logan Webb|R|22|5|4.25|18.95|18.25|0.349|0.21|94|0.045
Casey Mize|R|19|5|4.63|16.11|16.5|0.442|0.246|82|0.053
J.T. Ginn|R|22|5|5.13|16.41|16.75|0.419|0.244|87|0.045
Matthew Liberatore|L|25|5|5.75|15|15.88|0.486|0.198|84|0.04
Freddy Peralta|R|25|4.92|4.38|15.36|13.75|0.415|0.184|94|0.04
Michael King|R|26|4.92|5|17.19|17.5|0.34|0.141|93|0.038
Dustin May|R|24|4.92|5|15.5|14.88|0.505|0.349|83|0.042
Justin Wrobleski|L|20|4.9|6.25|18.35|17.63|0.584|0.204|92|0.05
Brandon Sproat|R|19|4.89|5.38|13.95|13.38|0.379|0.236|83|0
George Kirby|R|24|4.88|4.13|17.5|16.5|0.398|0.202|91|0.042
Sandy Alcantara|R|27|4.85|4.88|19.63|19.88|0.419|0.156|99|0.037
Robert Gasser|L|15|4.8|4.5|15.4|15.5|0.297|0.226|86|0
Michael Wacha|R|25|4.8|4.5|18.68|17.63|0.39|0.141|94|0
Jake Irvin|R|15|4.8|4.13|14.27|13.75|0.426|0.173|85|0.067
Tatsuya Imai|R|15|4.8|5.5|11.73|11|0.744|0.567|77|0
Zebby Matthews|R|17|4.76|4.38|17.06|15.13|0.436|0.192|92|0.059
Kodai Senga|R|8|4.75|4.75|11.88|11.88|0.537|0.329|75|0
Bryce Elder|R|24|4.71|4.25|17.21|16.13|0.458|0.197|86|0.042
Trevor Rogers|L|23|4.7|5.88|16.39|17.38|0.403|0.23|89|0.043
Griffin Canning|R|11|4.64|4.63|13.73|14.75|0.324|0.265|78|0.091
Davis Martin|R|24|4.63|2.63|15.63|12|0.555|0.291|85|0.083
Kyle Leahy|R|24|4.63|5.5|15.29|15.38|0.497|0.149|84|0.042
Brandon Young|R|21|4.57|4.88|16.81|17|0.357|0.186|90|0
Luis Castillo|R|20|4.55|4.13|15.6|16.75|0.437|0.199|93|0
Robbie Ray|L|24|4.54|4.38|16.42|15.75|0.395|0.203|93|0
Matthew Boyd|L|15|4.53|3.88|17|19.25|0.471|0.191|89|0
Tanner Bibee|R|26|4.5|4.25|17.35|18|0.492|0.215|90|0.038
JR Ritchie|R|8|4.5|4.5|14.88|14.88|0.376|0.195|90|0
Kyle Freeland|L|23|4.48|4.38|16.22|17.75|0.471|0.245|87|0
Shane McClanahan|L|21|4.48|3.5|14.62|14.38|0.321|0.184|76|0.048
Edward Cabrera|R|15|4.47|3.75|15.2|13|0.405|0.211|85|0
Framber Valdez|L|25|4.44|4.25|16.64|16.13|0.516|0.25|89|0.04
Jameson Taillon|R|17|4.41|4.13|14.82|12.5|0.432|0.272|83|0.059
Bubba Chandler|R|23|4.39|4.38|15.13|15.75|0.494|0.167|86|0.043
Jake Bennett|L|14|4.36|4.5|17.29|17.88|0.428|0.158|82|0
Grayson Rodriguez|R|14|4.36|4.63|14.14|15.13|0.498|0.277|86|0
Mike Burrows|R|17|4.35|3.5|16.53|16.25|0.414|0.137|92|0
David Peterson|L|16|4.31|3.88|15.06|16.13|0.412|0.167|84|0
Kai-Wei Teng|R|10|4.3|5|13.2|14.25|0.685|0.262|76|0
Jacob Lopez|L|17|4.29|5.25|14|13.63|0.581|0.28|83|0.118
Anthony Kay|L|24|4.29|4.63|15.04|16.25|0.415|0.168|87|0
Brady Singer|R|25|4.28|4.5|15.8|18.5|0.424|0.234|91|0.04
Seth Lugo|R|26|4.27|3.88|16.77|16.75|0.422|0.172|90|0.038
Reynaldo López|R|11|4.27|4.25|13.55|12.75|0.503|0.309|78|0.091
Eduardo Rodriguez|L|25|4.24|4.38|17.92|17.75|0.393|0.225|95|0.08
Kumar Rocker|R|22|4.23|4.88|14.77|15.38|0.334|0.228|84|0.045
Andrew Alvarez|L|11|4.18|4|14.55|15.25|0.318|0.167|78|0
Clay Holmes|R|12|4.17|4.25|17.17|17.13|0.51|0.174|89|0
Walker Buehler|R|25|4.16|3.5|14.44|14.38|0.426|0.227|82|0.04
Rhett Lowder|R|19|4.16|4.63|14.84|15.63|0.455|0.299|84|0.053
Andrew Abbott|L|26|4.15|4.38|16.08|16.63|0.407|0.158|93|0.038
Ryne Nelson|R|15|4.13|4.25|16.67|19.5|0.474|0.331|86|0.067
Nick Lodolo|L|14|4.07|4|15.36|14.63|0.391|0.157|88|0
Trevor McDonald|R|14|4.07|3.25|15.07|13.63|0.496|0.3|81|0
Mitch Keller|R|22|4.05|3.88|15.77|14.5|0.354|0.234|86|0.045
Andre Pallante|R|24|4.04|3.63|17|17.5|0.47|0.151|92|0.042
Grant Holmes|R|24|4|3.63|14.96|15.5|0.43|0.208|80|0.042
Slade Cecconi|R|21|4|3.75|15.33|14.88|0.387|0.18|85|0
Zac Thornton|L|9|4|4.13|16.78|17.25|0.515|0.157|82|0
Shane Bieber|R|11|4|4.38|15.18|16|0.5|0.357|85|0.091
Colin Rea|R|19|3.95|4.25|15.89|16.38|0.418|0.155|87|0.053
Noah Schultz|L|14|3.93|3.63|12.93|11.63|0.56|0.327|77|0.071
Jeffrey Springs|L|23|3.87|2.63|14.83|13|0.501|0.255|85|0.043
Andrew Painter|R|16|3.81|3.88|14.13|13.75|0.535|0.244|82|0.063
Michael McGreevy|R|25|3.8|4.38|16.48|15.75|0.515|0.185|89|0.04
Cal Quantrill|R|9|3.78|4.13|14.78|15.88|0.574|0.296|72|0.111
Brandon Pfaadt|R|13|3.77|3.75|17.77|18.75|0.595|0.134|86|0
Luinder Avila|R|12|3.75|4.13|12.92|14.25|0.51|0.358|79|0.083
Bailey Ober|R|19|3.74|3.5|16.32|15.5|0.673|0.213|86|0
Carmen Mlodzinski|R|12|3.67|2.88|13.08|12.63|0.825|0.264|80|0
Janson Junk|R|18|3.67|3.25|15.44|14.13|0.408|0.178|82|0.056
Ryan Johnson|R|12|3.67|3.63|13.83|13.5|0.574|0.171|83|0
Merrill Kelly|R|23|3.65|3.88|16.83|15.88|0.434|0.196|90|0
Ryan Gusto|R|11|3.64|4.25|12.09|12.63|0.481|0.27|66|0
Jack Kochanowicz|R|13|3.62|3.5|14.77|13.13|0.683|0.39|85|0.077
Martín Pérez|L|20|3.6|2.88|15.3|14.75|0.594|0.17|80|0.05
Aaron Civale|R|15|3.6|3.38|14.47|13.38|0.443|0.15|84|0.067
Adrian Houser|R|15|3.53|4.25|14.4|13.38|0.384|0.275|79|0.067
Erick Fedde|R|12|3.5|3.13|14.42|13.5|0.48|0.19|80|0
Javier Assad|R|10|3.5|3.63|15.6|15.75|0.431|0.118|84|0
Keider Montero|R|21|3.48|3.13|17.05|17.63|0.614|0.139|81|0
Patrick Corbin|L|15|3.47|3.75|13.8|13|0.498|0.182|81|0
Eric Lauer|L|17|3.47|3.88|15.41|16.75|0.661|0.208|85|0.059
Nick Martinez|R|24|3.46|3.13|17.71|17.63|0.475|0.194|83|0
Steven Matz|L|11|3.45|2.63|12.82|11.63|0.689|0.447|73|0
Chris Paddack|R|9|3.44|3.13|13.67|13.88|0.698|0.204|83|0.111
Stephen Kolek|R|10|3.4|3.13|16.2|16.25|0.736|0.422|84|0
Ryan Feltner|R|19|3.37|3.63|14.53|14.63|0.604|0.259|80|0.105
Germán Márquez|R|10|3.3|3.5|13.2|13.5|0.43|0.283|76|0
Tyler Phillips|R|14|3.29|3.25|13.71|12.38|0.469|0.315|71|0.071
Michael Lorenzen|R|25|3.28|2|13.76|12.75|0.574|0.226|87|0
Zac Gallen|R|19|3.21|2.63|15.47|16.38|0.493|0.185|87|0.053
Randy Vásquez|R|19|3.21|1.75|14.89|12.75|0.795|0.232|81|0
Tomoyuki Sugano|R|22|3.14|3.5|16.18|17|0.409|0.127|86|0.045
Mitch Bratt|L|8|3.13|3.13|13.75|13.75|0.912|0.327|76|0
Chris Bassitt|R|12|3|3.63|14.25|15.38|0.651|0.271|84|0.083
Zack Littell|R|14|2.93|2.88|14.36|14.38|0.56|0.234|79|0.071
Max Scherzer|R|11|2.91|2.88|12.27|13|0.564|0.398|76|0
Brayan Bello|R|8|2.75|2.75|13.38|13.38|0.505|0.253|89|0
Miles Mikolas|R|11|2.73|2.38|14.45|15.25|0.37|0.254|83|0
Simeon Woods Richardson|R|10|2.4|2.25|13.4|12.38|0.403|0.252|81|0
Jose Quintana|L|9|2.22|2.25|13.67|13.75|0.704|0.319|76|0.111
Braydon Fisher|R|8|1.13|1.13|3.38|3.38|1.206|0.153|17|0
PJ Poulin|L|11|1|1.13|4.09|4.63|0.894|0.37|21|0
```

## Changelog

- 🆕 **Sept 21 2026, Monday sweep — text-only. 🔴 NOT ONE DATA ROW WAS TOUCHED** (185 rows, `sum(n) = 3,403`). **Staleness re-measured: 31 slates / ~840 starts behind (population ≈ 4,678 through 9/20, bounded two enumerated ways). Acceptance-test rows re-driven from the repo's per-start log through 8/20 with the sample SD and reproduced.** ⚠️ **Method:** `project_read` → verbatim local copy → uniqueness-asserted programmatic patch → `collections.Counter` line-loss check → `local_path` upload.
- 🆕 **Sept 7 2026, Monday sweep — text-only. 🔴 NOT ONE DATA ROW WAS TOUCHED** (185 rows, `sum(n) = 3,403`, byte-identical before and after). ✅ **THE PUBLISHED TABLE WAS RE-VERIFIED THIS RUN AND IS INTERNALLY SOUND: 185 rows · `sum(n)` 3,403 · ZERO rows below n≥8 (min n = 8, max 27) · no duplicate names · exactly 10 pipes on every row · and both acceptance-test rows present at their stated values (Misiorowski `0.252 / 0.174`, Gilbert `0.289 / 0.132`), so the sample-SD (n−1) convention is intact.** ⛔ **It is not corrupt. It is OLD.**
- 🔴 **STALENESS RE-MEASURED: SEVENTEEN completed slates and 470 starts behind, through the 8/20 slate against a season population of 4,308 through 9/6 — VERIFIED three independent enumerated ways rather than bounded.** **The 8/31 banner's "ten slates / ~276 starts" is struck and dated.**
- 🔴 **TWO CLAIMS IN THE BANNER WERE FALSE AGAINST NEWER PROJECT DOCS AND ARE STRUCK WITH THEIR REPLACEMENTS STATED:** **(a)** *"`statsapi.mlb.com` is unreachable from a scheduled cloud run"* — struck project-wide on 2026-09-01 (`claude/betting-project-instructions.md` v5.3) and this copy survived it; the conclusion is unchanged, the reason is corrected. **(b)** *"A SCHEDULED RUN CANNOT FIX THIS"* — TOO BROAD: `data/latest/pitchers.json.gz` in the collector's repo carries the full per-start log this table is built from and 4,221 started rows were enumerated from it headless this run, on an `min_ip >= 20` population that at n≥8 drops only the openers this doc already excludes. ⛔ **Still not a substitute for THE RECIPE where a population-scaled constant is involved, and the rebuild was NOT run — a sweep verifies, it does not rebuild.**
- ✅ **THE `Normal(mu, cvO × mO)` CAVEAT IS DISCHARGED. T3 ran 2026-09-01 and PASSED on all three pre-registered criteria** (mean +0.0543 · SD 1.0772 · q10 −1.3528 · q90 +1.3356). **This doc had carried it as an open owed test for six days after it closed.** ⚠️ **The tails are ~8% fatter than Normal — inside the bar, worth naming on a far alt rung.**
- ⚠️ **Method:** `project_read` → verbatim local copy (no retype) → programmatic patch with every anchor ASSERTED to occur exactly once → `collections.Counter` line-loss check → fresh `project_read` and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.

- **Aug 21 2026, evening — text-only audit. 🔴 NOT ONE DATA ROW WAS TOUCHED** (185 rows, `sum(n) = 3,403`, byte-identical before and after). 🔴 **Struck a superlative that was false against this doc's own table:** Sandy Alcantara was written up as the **"deepest workload on the board"** at `mO` 19.63 when **Yoshinobu Yamamoto is deeper at 19.82** — corrected to *second-deepest*, struck rather than deleted, with the surrounding argument (low `cvO`, not record depth) left intact. ⚠️ **Added the missing caveat on the outs model:** `cvO` **is** the outs distribution, but the **`Normal(mu, cvO × mO)` form has NEVER been fitted** — the ✅ marks nearby validate only the **sample-SD convention**, and the distributional assumption is an **owed test** in `claude/owed-tests.md`. ⚠️ **Reconciled the headline against the table:** the build is **340 starters / 3,838 starts**, the printed table is **185 arms at n≥8 summing to 3,403**, and the **435-start gap is the cutoff, not a defect** — stated in place so the headline is verifiable. 🆕 **Changelog section created; this doc previously had none.**
