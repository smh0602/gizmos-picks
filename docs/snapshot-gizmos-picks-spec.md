# Gizmo's Picks — product spec

**v0.3 · 2026-08-23.** ✅ 🔴 **STATUS: THE COLLECTOR, THE DASHBOARD AND THE DAILY CARD ARE ALL BUILT AND RUNNING. THE MODELS BEHIND THEM ARE STILL TWO MARKETS FOR ONE POSITION.**

~~**v0.2 · 2026-08-22.** ✅ **STATUS: THE DATA LAYER IS BUILT AND RUNNING. EVERYTHING ABOVE IT IS STILL SPEC.** 🔴 **The old status line "SPEC ONLY, NOTHING IS BUILT" NO LONGER APPLIES TO THE COLLECTOR — see PHASE 0 immediately below.** ⛔ **It still applies to every model, every tab and the dashboard itself: outside Phase 0, every "Status" below is a claim about what is BUILDABLE, not about what runs.**~~ 🔴 **SUPERSEDED 2026-08-23 — "the dashboard itself" is no longer unbuilt. SEVEN TABS ARE LIVE. See PHASE 1 below.**

⛔ **WHAT IS STILL SPEC IS THE MODELLING, NOT THE SURFACE: there is NO hitter model and NO team run-scoring model, so every hitter market and every game projection on the page is 🔵 MARKET or ⚪ DESCRIPTIVE and carries NO Gizmo's confidence %.** ➡️ **The three-kinds discipline below is now load-bearing on a page real people can open, not a note about a page that might exist.**

**What it is:** a live MLB dashboard and picks product, modelled on covers.com's MLB section, **named by Sam**. It replaces the manual every-morning card build with a page that is always up.

---

# ✅ PHASE 0 — THE COLLECTOR — BUILT, DEPLOYED AND RUNNING AS OF 2026-08-22

✅ **THIS IS THE FIRST PART OF THIS DOCUMENT THAT DESCRIBES A THING THAT ACTUALLY EXISTS AND IS RUNNING RIGHT NOW.**

- **Repository: `github.com/smh0602/gizmos-picks`** ~~(private)~~ 🔴 **PUBLIC — CORRECTED 2026-08-31.** **Flagged as suspect on 2026-08-24 and left unverified for a week; it is now VERIFIED: an unauthenticated `git clone` from a scheduled cloud run succeeds, and `.github/workflows/collect.yml`'s own header says *"The repo is public, so Actions minutes are free."* **Owner: Sam.**
- **It runs on GITHUB ACTIONS, not in any Claude session.** ⛔ **THIS IS THE POINT: THIS CONTAINER CANNOT REACH EITHER API.** **A direct-fetch probe on 2026-08-22 returned `Tunnel connection failed: 403 Forbidden` for BOTH `api.the-odds-api.com` AND `statsapi.mlb.com`.** **github.com IS reachable — `git ls-remote` succeeds.**
  ✅ **THAT MEASUREMENT CONFIRMS LEDGER RULE 38 RATHER THAN INHERITING IT AS AN ASSUMPTION: a scheduled task in this environment can NEVER collect odds,** ~~**because it has neither a browser nor network access.**~~ `[2026-09-21 Monday sweep]` **because it has no API key and its direct egress to both APIs is refused — NOT for lack of a browser or of all network (`claude/betting-project-instructions.md` v5.3: Chromium launches headless; github is reachable) — and the one route it does have, `WebFetch`, is banned for odds.**
- **Files:** `collect.py` · `.github/workflows/collect.yml` · `README.md`.
- **The API key lives in a GitHub repository secret named `ODDS_API_KEY`.** ✅ 🔴 **THIS CLOSES THE PROJECT'S OLDEST OPEN SECURITY ITEM.** **The key is no longer pasted into conversations; Actions injects it at runtime.**
  ⚠️ **The OLD key was exposed in session transcripts for days and Sam TWICE declined to rotate it — he rotated it when the paid subscription was attached.** ⛔ **THE OLD KEY MUST BE TREATED AS COMPROMISED AND MUST NEVER BE REUSED.**
- **Subscription: $30/month, 20,000 credits.**

## 💰 MEASURED IN PRODUCTION 2026-08-22 — first two live runs, 19:56Z and 20:07Z

- ✅ **A `gamelines` pull returns 25 GAMES FOR EXACTLY 6 CREDITS**, confirming the bulk endpoint bills **PER CALL**. **Matches the pre-build estimate exactly.**
- ✅ **Uncompressed snapshot 85,627 bytes; gzipped 7,396 bytes — 11.6×**, inside the **8–12×** band predicted and **far below the 96× a synthetic test had suggested** (that test was rejected as unrealistic before being quoted).
- 🔴 **A REAL DEFECT WAS CAUGHT BY THE FIRST LIVE RUN AND FIXED THE SAME HOUR: the spec had budgeted ~20KB per gamelines pull and the true figure is 85KB.** **Uncompressed that is ~1.5 GB/year**, past what a git repo should carry, and **it would have surfaced as a problem around March rather than on day one.** **ALL SNAPSHOTS ARE NOW GZIPPED** (~180 MB/year including prop sweeps). ⚠️ **Recorded because an estimate made before measurement was wrong by 4×, and only shipping it revealed that.**
- ⚠️ **A SECOND DESIGN DECISION WAS REVERSED THE SAME HOUR: the collector originally FAILED SOFT (`sys.exit(0)` on any exception) so that broken runs would not email Sam. That was wrong for this job and is now FAIL LOUD (`sys.exit(1)`).** 🔴 **A MISSED PULL IS DATA THAT CANNOT BE BOUGHT BACK AT ANY SANE PRICE, SO A BROKEN RUN MUST BE VISIBLE.** **Failed runs do not disable a cron schedule, so there was never a real downside.** ⛔ **A GREEN CHECK ON A FAIL-SOFT COLLECTOR PROVES NOTHING — that is exactly why the first run's log had to be read line by line rather than trusted.**

## ⏰ LIVE SCHEDULE (UTC)

🔴 **THE TABLE BELOW IS STRUCK 2026-08-24: IT WAS COSTED AT ONE REGION FOR PROPS AND ITS TIMES ARE STALE.**

| Sweep | Cadence | Credits/day |
|---|---|---|
| ~~**Game lines**~~ | ~~**every 30 min, 15:00Z → 04:30Z (~28 pulls)**~~ | ~~**~168**~~ |
| ~~**Pitcher props**~~ | ~~**14:10Z and 21:40Z**~~ | ~~**~180**~~ |
| ~~**Hitter props**~~ | ~~**14:20Z**~~ | ~~**~75**~~ |
| | ~~✅ **TOTAL**~~ | ~~**≈ 423/day · ≈ 12,700/month against 20,000**~~ |

✅ **REPLACED BY THE BUDGET AS ACTUALLY DEPLOYED.** `[measured 2026-08-24 from `.github/workflows/collect.yml`]` 🔴 **THESE FIGURES ARE READ OFF THE WORKFLOW, NOT ASSUMED — which is the whole reason the row above was wrong.**

| Sweep | Cadence (UTC) | Per pull | Credits/day |
|---|---|---|---|
| **Game lines** | **28 runs/day** | **6** | **168** |
| ~~**Batter props**~~ | ~~**14:20Z and 20:20Z**~~ 🔴 **TIMES STRUCK 2026-08-27** | **150** *(both regions)* · **75** *(us2 only)* | **300** |
| ~~**Pitcher props**~~ | ~~**14:10Z and 20:10Z**~~ 🔴 **TIMES STRUCK 2026-08-27** | **90** *(both regions)* · **45** *(us2 only)* | **180** |
| | | 🔴 **TOTAL** | ~~🔴 **≈ 648/day · ≈ 19,400 of a 20,000-credit monthly plan**~~ 🔴 **STRUCK 2026-08-31 — SUPERSEDED. See the note directly below.** |

⚠️ 🔴 **THAT IS TIGHT, AND IT IS A DELIBERATE TRADE: MORE BOOKS AND FRESHER PROPS ARE NOT BOTH AFFORDABLE AT THIS PLAN.** **Three prop pulls a day at two regions is ~26,600/month and would run out before month end.** 🛟 **The 750-credit `RESERVE` guards the tail of the month, and its behaviour is the point: PROPS STOP AND GAMELINES KEEP RUNNING, rather than the whole month zeroing out.** ⚠️ **The prop pulls are TIMED, not merely spaced — so nothing on the board is much more than three hours old at first pitch.**

🔴 🆕 **THE WHOLE BUDGET BLOCK ABOVE AND THE 2026-08-27 RESTATEMENT BELOW ARE BOTH SUPERSEDED — 2026-08-31.** ⛔ **THIS PAGE NO LONGER OWNS THE SCHEDULE OR ITS COST.** ➡️ **`claude/update-schedule.md` (written 2026-08-28, newer than both) OWNS SAM'S TIMES AND THE DERIVED CREDIT COST; `freshness.py` OWNS THE DUE TIMES; `.github/workflows/collect.yml` OWNS THE CRONS. READ THEM THERE.**
🔴 **WHY BOTH FIGURES ARE WRONG, STATED SO NOBODY RE-DERIVES THEM: THERE IS NO 4am PROPS BLOCK ANY MORE AND THERE ARE NOT THREE PROP BLOCKS.** `[measured 2026-08-31 from `.github/workflows/collect.yml` and `collect.py`]` **Sam's 2026-08-28 schedule is Odds + Player Props at 7:00am and 4:00pm ET — TWO blocks — with the 7:00am one the full two-region pull and the 4:00pm one Hard Rock only, and the card at 10:00am.** **The derived worst case is 372/day at a 15-game slate, and `claude/update-schedule.md`'s MEASURED actuals are 317 / 287 / ~330 a day — roughly HALF the 606–648 this page asserts.** ⚠️ **The BILLING FORMULA is untouched and still correct: `markets × regions × games` on the per-event endpoint, `per call` on the bulk one.** ⛔ **Only the cadence and the totals moved.**

~~🔴 **RESTATED 2026-08-27 — THERE ARE NOW THREE PROP BLOCKS, NOT TWO, AND THE COST IS THE SAME BECAUSE THE REGION IS THE PRICE.** `[measured 2026-08-26]` **Cost is markets × REGIONS × games and BOOKS ARE FREE INSIDE A REGION — one `us,us2` pull returned EIGHTEEN BOOKS for 6 credits. Narrowing the BOOK list saves nothing.** ➡️ **4am ET Hard Rock only (`us2`) = 120 · 10am ET BOTH regions = 240 · 4pm ET Hard Rock only = 120 → 480/day, plus 126 gamelines = 606/day ≈ 18,786 a month.** 🔴 **THE FULL PULL SITS BEFORE THE MORNING CARD ON PURPOSE.** ⚠️ **The trade, stated: the 4am and evening cards carry Hard Rock prices only and lose cross-book comparison.** **Sam, 2026-08-26:** *"i want the lines to start being posted at around 4am"*.~~ 🔴 **STRUCK 2026-08-31 — the 4am block is gone; see the note above. Sam's 8/26 words are kept as the record of why it existed.**

**A `RESERVE` of 750 credits in `collect.py` REFUSES TO START a prop sweep that would drop below it.** ~~**GitHub Actions minutes ≈ 930/month against 2,000 free on a private repo.**~~ 🔴 **STRUCK 2026-08-31 — THE REPO IS PUBLIC, SO ACTIONS MINUTES ARE FREE AND UNMETERED AND THERE IS NO 2,000-MINUTE BUDGET TO SPEND.** ⚠️ **The heartbeat loop holds a job open for hours, so a minutes figure computed from a run count was never going to be right either. Minutes are not a constraint on this repo; the CREDIT plan is.**

## 🔴 WHAT IS NOW ACCUMULATING AND COULD NOT BE BOUGHT BACK

- **Line movement across 15 books.**
- **Closing lines** — the last snapshot before first pitch, **the only basis for real closing-line-value measurement.**
- **The de-vigged implied team totals that owed-test T25 needs, and which CANNOT BE BACKFILLED.**

✅ **T25's COLLECTION REQUIREMENT IS NOW SATISFIED GOING FORWARD, FROM 2026-08-22 ONWARD.** ⛔ **IT REMAINS UNSATISFIABLE FOR EVERY DATE BEFORE THAT.**

## ⛔ STILL NOT BUILT — *as of 2026-08-22*

~~**Every model beyond starting-pitcher strikeouts and outs, and the dashboard itself.** 🔴 **THE COLLECTOR IS THE DATA LAYER ONLY.** **Phases 1–4 below are UNCHANGED.**~~ 🔴 **HALF STRUCK 2026-08-23: THE DASHBOARD IS BUILT AND SO IS THE DAILY CARD.** ✅ **What survives unchanged is the MODEL half — every model beyond starting-pitcher strikeouts and outs is still unbuilt. See "WHAT IS STILL NOT BUILT" at the end of PHASE 1.**

---

# ✅ PHASE 1 — THE DASHBOARD AND THE AUTOMATED CARD — BUILT AND RUNNING AS OF 2026-08-23

✅ **SEVEN TABS ARE LIVE: Scores & Matchups · Gizmo's Picks · Odds · Player Props · Track Record · Trends · News.**

- **Same repository, `github.com/smh0602/gizmos-picks`.** **The page is `index.html`; the collector is `collect.py`; the card generator is `card.py`; the verifier is `verify_card.py`.**
- ✅ **THE COLLECTOR RUNS ITSELF.** **Nothing on the page needs a Claude session to be open, and nothing on it needs the browser extension.**
- ✅ **CLICKABLE BOX SCORES** off the free statsapi live feed — ⚪ **DESCRIPTIVE**, zero credits.
- ✅ **PITCHER PROPS ARE ON THE PAGE WITH THEIR MODEL NUMBERS** — 🟢 **MODEL**, and the only 🟢 numbers on the surface.
- ✅ **BET-SLIP DEEP LINKS.** **Each priced outcome carries the book's own link with a `{state}` placeholder substituted from the viewer's selected jurisdiction.**
- ✅ **FINISHED GAMES DROP OFF EVERY TAB AND THE BOARD ROLLS TO THE NEXT DAY BY ITSELF** — see THE SLATE DATE below, which is what makes the roll work.

## ✅ THE BET-STATE SELECTOR IS NOW ALL 51 JURISDICTIONS

🔴 **IT HELD 29 ENTRIES AND WAS MISSING 22.** **Sam: *"for the bet state. there are about 20 missing states"* — he said ~20; the true count was 22.**

- ✅ **NOW ALL 50 STATES PLUS DC = 51**, grouped into **"Sportsbooks operate here"** and **"Other states"**.
- 🔴 **THE BOOK, NOT THE PAGE, IS THE AUTHORITY ON WHERE IT OPERATES.** **A missing option was a DEAD BET LINK WITH NO WAY OUT — the viewer could not even select their state to find out.** ➡️ **Listing a state is not a claim that a book takes action there; it is a claim that the viewer is allowed to say where they are.**
- ⚠️ **The grouping is a convenience label and it will go stale as legalisation moves. ⛔ Do not treat the grouping as legal advice or as a market map.**

## ✅ THE DAILY CARD IS GENERATED UNATTENDED — `card.py`, run as `python collect.py card`

🔴 **IT SPENDS ZERO ODDS API CREDITS. IT CALLS NOTHING AT ALL.** **It reads `data/latest/pitchers.json.gz` and `data/latest/props.json.gz`, which the collector has already stored, and writes `picks/<date>.json`.**

**What it computes per prop:**

- 🟢 **STRIKEOUTS: the K equation EXACTLY AS PUBLISHED IN `claude/mlb-projection-model.md`, WHICH OWNS IT.** 🔴 **~~v4.0~~ — STRUCK 2026-09-14: `card.py` has stamped `MODEL_VERSION = "v5.0"` since 2026-09-11 and this page still said v4.0 three days later.** ⛔ **A VERSION IS A FACT ABOUT THE CODE — read it from `MODEL_VERSION`, never from a version typed into a doc. That is the same rule that kept the coefficients off this page.** **Poisson.** ⚠️ **The equation was inlined on this page until 2026-08-24 and now sits behind the pointer. ⛔ NO COEFFICIENT VALUE WAS ALTERED — ONLY RELOCATED.**
- 🟢 **OUTS: the outs equation EXACTLY AS PUBLISHED IN `claude/mlb-projection-model.md`, WHICH OWNS IT** *(~~v4.0~~ — struck 2026-09-14, same reason as the line above)* — including the TIERED shrinkage `k` and the previous-start PITCH-COUNT term. **Normal with SD = cvO × season mean outs.** ⚠️ **Same treatment, same date, same guarantee: relocated behind the pointer, no value altered.**
- 🔴 **WHY THE RELOCATION: A COEFFICIENT COPIED INTO A SECOND DOC IS A COEFFICIENT THAT WILL GO STALE IN ONE OF THEM, AND NOTHING WILL SAY WHICH.** ⛔ **Never quote a MODEL coefficient from this page — of any version. Read it from the model doc.** *(~~"a v4.0 coefficient"~~ struck 2026-09-14: naming the version made the prohibition look version-specific, and the doc then went stale on the version rather than on the rule.)*
- ⚪ **RAW HIT RATE at the exact threshold — STARTS ONLY, ALL starts, NO 4+IP filter**, because **T23 proved that filter is biased** (it can only delete winners on an outs under at `T ≥ 12`).
- **`blend` = plain 50/50 model + raw.**
- ⚪ **MATCHED CLASS (STEP 4B), axis chosen by market: the K axis (±1.5 season K/9) for strikeout props, the DURABILITY axis (trailing mean outs band, POINT-IN-TIME) for outs props — this is owed-test T24's finding, now applied in code.** **BOTH the all-starts and the 4+IP figure are reported with `n`, and the reference figure used for the ≥15-point flag is the ALL-STARTS one (unbiased per T23), NEVER the flattering 4+IP one.**
- ⚪ **HEAD-TO-HEAD (STEP 4C), reported INCLUDING when `n=0`** — ledger rule 50 requires the zero to be printed.
- 🔴 **EVERY CHECK IS A LABEL ON THE ROW, NEVER A GATE (ledger rule 53).** **The ONLY thing withheld is a PAIR below 1.8x, which is Sam's own instruction (ledger rule 28).**
- **PAIRS: two legs, ONE book (Hard Rock only — it is the only one that multiplies), TWO DIFFERENT GAMES CHECKED ON GAME ID (ledger rule 54), product ≥ 1.80, ranked by joint probability, labelled IN BAND / ABOVE BAND.** `[2026-09-21 Monday sweep]` **AND 3- AND 4-LEG PARLAYS, same one-book / different-games rules, on their own band — every band is owned by `claude/pick-ledger.md` rule 28 (`card.py` `PARLAY_BANDS`).**

### 🔴 T21 AND T22 ARE STILL NOT ADOPTED, AND THE CODE ENFORCES THAT

- ✅ **`blend` IS THE PLAIN 50/50 AND IS THE ONLY COLUMN THAT ENTERS CALIBRATION.**
- **`carried` is the blend after the T21 flag (perfect-record shrinkage — 88.8% on 9+ prior starts, 78.0% on 3–8) and the T22 flag (shuttled starter, −14.4 points, point-in-time), and it enters NO DENOMINATOR.**
- ✅ **This mirrors exactly what the hand-built 8/22 card did.**
- ⚠️ 🔴 **ONE DELIBERATE DIFFERENCE FROM THE 8/22 HAND-BUILT CARD, STATED PLAINLY: THE AUTOMATED `carried` APPLIES NO DISCRETIONARY NUDGE TOWARD THE MATCHED CLASS.** **The 8/22 card nudged some rows by hand; the automated one does not — because STEP 4B is a FLAG, and folding it into a number, even a third of the way, would be a NEW MODEL CHOICE WITH NO PRE-REGISTERED TEST.**

## 🔴 `verify_card.py` — ~~**46 CHECKS** `[counted 2026-08-26 from the source]`~~ **COUNT THE SOURCE** — RUN BEFORE THE COMMIT STEP, EXITS NON-ZERO ON ANY FAILURE

🔴 ⛔ **THE NUMBER IS REMOVED RATHER THAN UPDATED, 2026-08-31, BECAUSE THIS DOC HAS NOW CARRIED FIVE DIFFERENT ONES — 21 → 27 → 33 → 46 → 90 — AND EVERY ONE OF THEM WAS RIGHT ON THE DAY IT WAS WRITTEN AND WRONG WITHIN DAYS.** `[counted 2026-08-31: 90 `ck(` calls at line start]` ➡️ **The project's own standing rule is NEVER PUT A COUNT ANYWHERE YOU CANNOT AUTO-UPDATE. Writing a sixth number here would be making the same mistake a fifth time.** ✅ **To get the live figure, count `ck(` in `verify_card.py`. What matters is not the count but that the verifier runs BEFORE the commit and that a card failing it is never published.**

~~**33 CHECKS** `[counted 2026-08-25]`~~ 🔴 **STRUCK 2026-08-26 — the count moved again, +13 for the projection block.** `[counted 2026-08-26]` **46 `ck(...)` calls.** ⚠️ **THIS IS THE FOURTH DIFFERENT FIGURE THIS DOC HAS CARRIED (21 → 27 → 33 → 46) AND THE LESSON IS THE PROJECT'S OWN: NEVER PUT A COUNT ANYWHERE YOU CANNOT AUTO-UPDATE.** ➡️ **Treat this number as a snapshot and COUNT THE SOURCE.**

✅ 🔴 **THE 2026-08-26 ADDITIONS WERE FAULT-INJECTED BEFORE BEING TRUSTED.** **Six deliberate defects were written into a real card — a projection nudged 1.5 K, a confident pick flipped to the wrong side of its line, a hitter row relabelled `MODEL`, a projection added to a BARRED market, a stripped unit, and a nudged hitter projection — and ALL SIX WERE CAUGHT.** ⚠️ **A check that has never been shown to fail is a check nobody has tested.**

~~**27 CHECKS** `[counted 2026-08-24]`~~ 🔴 **STRUCK 2026-08-25 — the count moved again.** `[counted 2026-08-25]` **33 `ck(...)` calls.** ⚠️ **THIS IS THE THIRD DIFFERENT FIGURE THIS DOC HAS CARRIED (21 → 27 → 33) AND THE LESSON IS THE PROJECT'S OWN: NEVER PUT A COUNT ANYWHERE YOU CANNOT AUTO-UPDATE.** ➡️ **Treat this number as a snapshot and COUNT THE SOURCE.**

~~## ✅ `verify_card.py` — 21 CHECKS~~ 🔴 **STRUCK 2026-08-24 — THE COUNT DOES NOT RECONCILE, AND NEITHER PUBLISHED FIGURE WAS RIGHT.** `[counted 2026-08-24 from the source]` **`verify_card.py` contains 27 `ck(...)` calls.** ⚠️ **The repo's own `CLAUDE.md` says 26 — IT IS ITSELF STALE.** ⛔ **REPORT ONLY: a headless run MAY NOT PUSH A CODE CHANGE, so `CLAUDE.md` still says 26 and someone with push rights must correct it there. This doc is not the fix; it is the flag.**

🔴 **A CARD THAT FAILS VERIFICATION IS NEVER PUBLISHED — the verifier runs BEFORE the commit, not after.** ~~✅ **All 21 passed on the first real run.**~~ ✅ **All checks passed on the first real run — the COUNT quoted in that sentence was 21 and is struck above; the pass result is not in doubt.**

- **Poisson CDF vs 200,000 simulations — max gap 0.307 points.**
- **Normal outs probability RE-DERIVED from the raw game log (`mu` and SD both rebuilt, not read back) — max gap 0.0400 points.**
- **Raw hit rates re-counted by hand off the game log — 32/32 rows exact.**
- **POINT-IN-TIME: no start dated on or after the slate date appears in any denominator.**
- **model over + under = 100% on all 32 two-sided numbers.**
- **No same-game parlay, checked on GAME ID.**
- **No pair below 1.8x.**
- **Multiplier re-derived from the two American prices.**
- **Joint = product of the two blends.**
- **Every pair leg priced at Hard Rock; no pair reuses a pitcher.**
- **Every quoted price traced back to a raw stored pull — 0 invented.**
- 🔴 **`blend` is the plain 50/50 — this check is what PROVES T21/T22 were not silently adopted.**
- **Every row carries a calibration band label.**
- **No `picks` row shorter than −700; below-floor rungs are KEPT AND SHOWN, not deleted (118 rungs, 23 below −700).**
- **A higher over rung is never more likely than a lower one (monotonicity).**
- **Every over rung carries its "To Record N+" app-label form (rule 49's off-by-one).**

## 🔴 THE PITCHER-PROPS PULL IS `regions=us,us2` — AND THE SAME FAILURE HAS NOW HAPPENED IN BOTH DIRECTIONS

~~## ✅ THE PITCHER-PROPS PULL IS NOW `us2` — A RULE THAT NEVER REACHED THE CODE~~ 🔴 **HEADING STRUCK 2026-08-24 — it asserted a deployed state that is no longer the deployed state.**

~~🔴 **LEDGER RULE 48 / STEP 5 HAS SAID HARD ROCK ONLY (`us2`) SINCE 2026-08-22 AND THE COLLECTOR WAS STILL ON `regions=us,us2`.**~~ 🔴 **STRUCK 2026-08-24 — RULE 48 NO LONGER SAYS HARD ROCK ONLY.** **On the evening of 2026-08-23 Sam widened the odds source to FIVE BOOKS, and rule 48 now specifies those five books at `regions=us,us2`.** ⛔ **`claude/pick-ledger.md` RULE 48 OWNS THE CURRENT SET — read the book list there. It is deliberately NOT restated on this page, because a second copy of a set that moves is the thing that goes stale.**

~~✅ **Fixed 2026-08-23 to `REGIONS_CHEAP` (`us2`).**~~ 🔴 **STRUCK — that was true for one day.** ✅ **REPLACED: the pitcher-props pull is `REGIONS_FULL`, i.e. `regions=us,us2`** — **four of the five books live in `us`, so a `us2`-only pull cannot see them.** `[verified 2026-08-24 in `collect.py`]`

~~💰 **It also halves that pull: 3 markets × 1 region × ~16 games = 48 credits per pull instead of 96.**~~ 🔴 **STRUCK — the halving was REVERSED by the widening.** 💰 **At two regions that pull is 3 markets × 2 REGIONS × games = 6 CREDITS PER GAME** — **~90 on a 15-game slate.** 🔴 **~~96~~ STRUCK 2026-09-14: the arithmetic contradicted itself — 3 × 2 × 15 is 90, and the deployed budget table in PHASE 0 says 90 in the same document.** ⚠️ **Which is the case for writing the RATE and not the total: a per-game rate cannot go stale with the slate size, and a total can be wrong without looking wrong.** ➡️ **See the deployed budget table in PHASE 0, which is costed at two regions.**

⚠️ **`us_dfs` REMAINS BANNED and PrizePicks is NEVER the source of a NUMBER.** **The widening changed the BOOK SET; it did not touch that rule.**

✅ 🔴 **THE LESSON OF THIS SECTION IS UNCHANGED, AND IS WHY IT IS STRUCK RATHER THAN DELETED: A RULE WRITTEN IN A DOC IS NOT A RULE IN THE CODE.** 🔴 **AND ON 2026-08-24 THE SAME FAILURE INVERTED. This time the rule was LIVE IN THE CODE — the five-book widening shipped 8/23 evening — and had NOT REACHED THE DOCS, so this page went on asserting a `us2`-only pull for a day. ⛔ THE GAP RUNS BOTH WAYS AND NEITHER DIRECTION ANNOUNCES ITSELF: doc-ahead-of-code and code-ahead-of-doc are the same defect, and only reading the deployed source settles which one you have.**

## ✅ THE ALT LADDER IS NOW STORED — IT WAS BEING PULLED AND THEN DROPPED

🔴 **`pitcher_strikeouts_alternate` WAS IN THE REQUEST AND NEVER SURVIVED INTO `props.json.gz`, so a rung-walk into the 1.8x band had nothing to walk.**

- ✅ **Ladders are stored per pitcher, Hard Rock only, DEDUPED ACROSS `hardrockbet` AND `hardrockbet_oh`** — they post the same rung and it was producing duplicate plays.
- ✅ **Each rung carries BOTH forms — the feed's `o2.5` and the app's `To Record 3+` — per ledger rule 49.**
- ✅ **Every rung is priced through the same model and hangs under its pitcher; the card STARS the safest rung that still clears Sam's −700 floor.**
- ⛔ **`pitcher_outs_alternate` is DELIBERATELY NOT REQUESTED: Hard Rock posts no alt outs market at all, Sam-confirmed at the book (ledger rule 31).**

## ✅ "BEST PRICE ACROSS BOOKS" AND "WHAT DOES SAM'S BOOK SAY" ARE NO LONGER THE SAME FIELD

🔴 **THEY WERE ONE FIELD, AND THAT IS A RULE-55 HAZARD AS WELL AS A BETTING ONE.**

- ✅ **Each prop now also keeps HARD ROCK'S OWN price and link in an `hr` field, and the card quotes Hard Rock's number.**
- ✅ **When Hard Rock did not post a market in that pull, THE PLAY IS STILL PRINTED (ledger rule 53), with the fact stated on the row and the other book named.**
- ⛔ **Such a play is BARRED FROM PAIRS, because only Hard Rock multiplies.**

## 🔴 THE CARD IS DATED BY THE SLATE, NOT BY THE WALL CLOCK

**The date is the ET date of the EARLIEST GAME THAT HAS NOT STARTED.**

⚠️ **At 11pm ET the board already holds tomorrow's games and none of today's. Dating off the clock would file tomorrow's card under today and the page would never find it.** ✅ **This is what makes the board roll to the next day by itself.**

## ✅ THE OPPONENT TABLE IS REBUILT NIGHTLY ON THE RUNNER, FROM THE SAME PULL THE MODEL READS

🔴 **THIS MATTERS BECAUSE `claude/mlb-opponent-database.md` CAN ONLY BE REBUILT IN AN INTERACTIVE BROWSER SESSION (THE RECIPE needs Claude in Chrome), so the published copy goes stale a slate at a time — it was already one slate short on 8/22.** ✅ **The runner's rebuild is self-healing.**

`[measured 2026-08-23, against the published table]` **The pool holds 3,802 starts (IP-filtered, ~99% of the season). Mean |ΔE[K]| difference 0.021 K, max 0.064 K — inside the ~0.045 K the opponent doc itself quotes as the cost of a one-slate lag.**

✅ 🔴 **THE PROPERTY THAT ACTUALLY MATTERS IS NOT THE SIZE OF THE GAP: IT IS THAT THE VARIABLE AND ITS CENTERING CONSTANT COME FROM THE SAME PULL.** **A meanK on one scale centred on a constant from another is this project's oldest documented bug.**

⛔ **THIS DOES NOT RETIRE THE PUBLISHED TABLE AND DOES NOT CHANGE THE CENTERING CONSTANT RECORDED THERE — that constant is stated in `claude/mlb-opponent-database.md`, WHICH OWNS IT.** **The runner computes its OWN constant, on its own nightly pull, on a slightly different population.** ⛔ 🔴 **THE TWO MUST NEVER BE MIXED, AND THE VARIABLE AND ITS CENTERING CONSTANT MUST COME FROM THE SAME PULL — THAT RULE IS UNCHANGED AND IS THE WHOLE POINT OF THIS PARAGRAPH.** ⚠️ **Both figures were inlined here until 2026-08-24 and are now behind the pointer. ⛔ NEITHER VALUE WAS ALTERED — only relocated, precisely so that this page cannot become the place somebody copies a centering constant from.** *(The Aug 23 changelog entry below still quotes both numbers; it is dated history and is left exactly as written.)*

~~## ⏰ TWO NEW CRON ENTRIES, PLUS AN EVENING PROPS REBUILD~~ 🔴 **STRUCK 2026-08-27 — EVERY TIME IN THE TABLE BELOW IS DEAD. The schedule has been rewritten twice since (4am props on 8/26; 29 cron entries collapsed to 16 on 8/27).**

| ~~New entry (UTC)~~ | ~~What~~ |
|---|---|
| ~~**`45 14 * * *`**~~ | ~~**card**~~ |
| ~~**`45 21 * * *`**~~ | ~~**props-board rebuild**~~ |
| ~~**`50 21 * * *`**~~ | ~~**card**~~ |

✅ **THE REASON THE REBUILD EXISTS SURVIVES AND IS THE PART WORTH KEEPING: A CARD BUILT AT 10AM MAY NOT ASSERT A 6PM PRICE (ledger rule 49).** **Every props block therefore still ends with a `props-board` rebuild before its card.** ⚠️ **Minutes are still deliberately off `:00` and `:30`.**

## ⏰ THE SCHEDULE LIVES IN `.github/workflows/collect.yml` AND IS NOT RESTATED HERE

🔴 **THIS PAGE HAS NOW CARRIED A STALE CRON TABLE TWICE, AND THE PROJECT ALREADY HAS THE RULE FOR IT: NEVER PUT A FIGURE ANYWHERE YOU CANNOT AUTO-UPDATE.** ➡️ **READ THE WORKFLOW.** **`claude/pick-ledger.md` RULE 63 owns the SHAPE of the schedule; the workflow owns the times.**

**The shape, as of 2026-08-27:** **A MODE IS A LIST — one cron runs a whole time block (`props-pitcher-hr props-batter-hr props-board`), and the CARD keeps its own cron so a `verify_card.py` failure can never discard the props pull that paid for it.** ~~**Three props blocks a day (4am / 10am / 4pm ET), each with a backup 30 minutes later that costs nothing when the first one worked, each followed by a card.**~~ `[2026-09-21 Monday sweep]` **STRUCK — stale; the schedule is owned by `claude/update-schedule.md` and `.github/workflows/collect.yml`.** ~~📊 **16 cron entries, down from 29. Credit cost UNCHANGED at 606/day — batching changes the number of RUNS, never the number of PULLS.**~~ 🔴 **STRUCK 2026-08-31 — BOTH HALVES ARE STALE.** ~~`[counted 2026-08-31 from the workflow]` **SIX cron entries, not 16** … ⚠️ 🔴 **AND THE WORKFLOW'S OWN HEADER COMMENT STILL SAYS "the count is 16" — REPORTED, NOT FIXED.**~~ 🔴 **BOTH HALVES STRUCK 2026-09-14 — AND THIS IS THE SIXTH COUNT THIS DOC HAS CARRIED AND GONE STALE ON.** `[verified 2026-09-14 from a fresh clone, in this same turn]` **The workflow's header no longer says 16 — it carries a `CRON COUNT` line, its own strike recording that 16 was right when written, and an explicit ban on hand-editing the number to silence a red run; and the count is now ASSERTED BY `test_cron_wiring.py` rather than remembered.** ✅ **So the header and the file agree, and a machine checks it.** ⛔ **NO NUMBER IS WRITTEN HERE THIS TIME — that is the whole lesson of the five struck counts above, applied instead of restated. `.github/workflows/collect.yml` owns the count and the test asserts it.** ➡️ **The count was never the point anyway: since the 2026-08-28 converge rewrite the crons are CHANCES TO LAND, not the mechanism.** ➡️ **The count is not the point any more: since the 2026-08-28 converge rewrite the crons are CHANCES TO LAND, not the mechanism. `claude/freshness-architecture.md` explains why, and `freshness.py` holds the deadlines.**

🔴 **WHY IT WAS COLLAPSED: GITHUB STOPPED FIRING EVERY SCHEDULED RUN FOR 21 HOURS ON 2026-08-26/27 while manual dispatch kept working.** ⛔ **CAUSE NEVER CONFIRMED — see ledger rule 62, which also carries the four-step diagnostic. The 29-entry cron list is a SUSPICION, labelled as one.**

## ✅ THE FIRST AUTOMATED CARD

**2026-08-23 slate · 32 plays across 10 games · 8 pairs, all inside 1.8x–2.1x · 118 alt rungs.** **Generated 2026-08-23T03:15Z from odds pulled 02:55:33Z and game logs pulled 02:37:45Z.**

~~⚠️ 🔴 **IT IS NOT YET IN THE REPO — the container could not push, so Sam is uploading the files by hand and will trigger the first run himself.** ⛔ **Until he does, this section describes code that exists and has been run, not code that is deployed.**~~ ✅ 🔴 **STRUCK 2026-08-24 — HE DID, AND IT IS DEPLOYED.** `[verified 2026-08-24]` **`github.com/smh0602/gizmos-picks` IS LIVE AND PUBLIC, THE COLLECTOR HAS BEEN COMMITTING DATA SINCE 2026-08-22, and `data/` holds dated snapshots through today.** ~~⚠️ **NOTE, NOT CHANGED: PHASE 0 above still describes the repository as *(private)*.** …~~ ✅ `[2026-09-21 Monday sweep]` **Resolved — PHASE 0's *(private)* was struck and corrected to PUBLIC on 2026-08-31.**

## ⛔ WHAT IS STILL NOT BUILT

1. 🔴 **THE HITTER MODEL — Phase 2. ATTEMPTED AND CLOSED-FAILED 2026-08-24/25.** **FOUR pre-registered specifications — T27, T28, T29, T30 — all lost to a smoothed season average. Every hitter market on the page is 🔵 MARKET prices with a ⚪ DESCRIPTIVE own-rate number and carries no Gizmo's confidence %.** ⚠️ **This is no longer "not built yet"; it is "built, tested and did not clear."** **See `claude/owed-tests.md`.**
2. 🔴 **TEAM RUNS → PREDICTED SCORE → MONEYLINE → RUN LINE → TOTALS — Phase 3. ATTEMPTED AND CLOSED-FAILED 2026-08-25.** **FIVE arms across THREE pre-registered specifications — T31a, T31b, T32a, T32b, T33 — and not one cleared a bar against a NAIVE baseline, never mind a sportsbook. The posted numbers stay 🔵 MARKET; none of them is ours.** ⚠️ **Same correction: tested, not merely unbuilt.**
3. ⛔ **ATS RECORDS AND LAST-10 O/U.** **These need ACCUMULATED CLOSING-LINE HISTORY, which began 2026-08-22 and cannot be backfilled.**
4. ~~⛔ **THE TRACK RECORD TAB IS STILL HARDCODED.** 🔴 **It does not read the ledger as data.**~~ ✅ 🔴 **STRUCK 2026-08-25 — IT IS NO LONGER HARDCODED AND THIS DOC WAS A DAY BEHIND THE CODE.** `[verified 2026-08-25 in the deployed `index.html`]` **The tab reads `data/latest/record.json`, which `collect.py record` regenerates nightly from stored results; the file is stamped `"kind": "DESCRIPTIVE"` and carries overall, by-kind, by-market, by-side, by-band and a calibration table.** ✅ **PHASE 1'S LAST STATED DEBT IS THEREFORE CLOSED.** ⚠️ **What it grades is the MACHINE card only — hand-built cards and Sam's own slips were removed on 2026-08-24 at his instruction, so this record and the ledger's are DIFFERENT POPULATIONS and must never share a denominator.**

---

# 🔴 THE CENTRAL DISCIPLINE — READ THIS BEFORE ANY OTHER SECTION

**EVERY NUMBER ON THE SITE IS EXACTLY ONE OF THREE KINDS, AND IT MUST BE LABELLED AS SUCH ON THE PAGE.**

- 🟢 **MODEL** — produced by a **fitted, backtested, calibrated** model of ours. **May carry a Gizmo's confidence %.**
- 🔵 **MARKET** — derived from sportsbook prices: **de-vigged implied probability, posted run lines, posted totals.** **Honest and useful — but it is the BOOK'S opinion, not ours.** ⛔ **NEVER carries a Gizmo's confidence % and is never described as a projection.**
- ⚪ **DESCRIPTIVE** — raw facts: records, live game state, standings, a player's own game log. **No modelling claim at all.**

⛔ 🔴 **A PAGE THAT BLURS MODEL AND MARKET IS CLAIMING CREDIT FOR THE BOOK'S WORK. THIS IS THE SINGLE LARGEST INTEGRITY RISK IN THE PRODUCT.**

➡️ **See ledger rule 55**, which is this discipline written into the standing rules.

---

# 🔴 THE DE-VIG REQUIREMENT

**Raw implied probabilities from a two-way market sum to MORE than 100%. The excess is the book's margin.** ⛔ **Always normalise proportionally before display.**

**Worked example, measured 2026-08-22 from the live feed:**

| Side | Price | Raw implied | ✅ De-vigged |
|---|---|---|---|
| **Yankees** | **−550** | **84.6%** | **79.2%** |
| **Blue Jays** | **+350** | **22.2%** | **20.8%** |
| | | 🔴 **sum 106.8%** | **100.0%** |

🔴 **POSTING THE RAW FIGURE INFLATES THE FAVOURITE BY 5.4 POINTS.**

✅ **Sam's own example is exactly right and is recorded because it is the cleanest statement of the mechanism: −115 on both sides sums to 107% and de-vigs to precisely 50/50.**

---

# 🔴 CURRENT MODEL COVERAGE — STATED BLUNTLY

**WE MODEL TWO MARKETS, FOR ONE POSITION: starting-pitcher STRIKEOUTS and starting-pitcher OUTS.** ~~**v4.0.**~~ 🔴 **STRUCK 2026-09-14 — `card.py`'s `MODEL_VERSION` OWNS THE VERSION AND IT READS v5.0 (shipped 2026-09-11). ⛔ It is not restated here.** ⛔ **EVERYTHING ELSE ON THE TARGET SITE IS UNMODELLED.**

**Calibration status as of 2026-08-22 — n = 40 graded plays total:**

| Band | n | Status |
|---|---|---|
| **70–80%** | **20** | ✅ **WELL CALIBRATED — +4.8** |
| 🔴 **60–70%** | **13** | 🔴 **BROKEN — −25.9** |
| 🔴 **80%+** | **6** | 🔴 **BROKEN — −18.0** |
| 50–60% | 1 | ⚠️ **n=1. Nothing.** |

⛔ 🔴 **ONLY THE 70–80% BAND IS CURRENTLY FIT TO CARRY A PUBLIC CONFIDENCE NUMBER.** **Live figures live in `claude/pick-ledger.md`; this table is a snapshot and goes stale.**

---

# TAB-BY-TAB BUILD STATUS

⚠️ **"BUILDABLE NOW" means the data exists and the work is engineering. It does NOT mean it is built.**

| Tab | What Sam wants | Data kind | Status |
|---|---|---|---|
| **Live scoreboard** | in-game pitcher, batter, count, inning, live pitcher line | ⚪ **DESCRIPTIVE** | 🆕 ✅ **BUILT 2026-08-23 — the Scores & Matchups tab, with CLICKABLE BOX SCORES.** statsapi live feed, zero credits |
| **Date picker + filters** | any date, filter the board | ⚪ **DESCRIPTIVE** | 🆕 ✅ **BUILT 2026-08-23.** **Finished games drop off every tab and the board rolls to the next day by itself** |
| **Team records** | incl. home/road and last-10 | ⚪ **DESCRIPTIVE** | 🆕 ✅ **BUILT 2026-08-23** — statsapi standings, `date=` works. ⛔ **ATS and last-10 O/U are NOT built — they need accumulated closing-line history** |
| **Game projections** | predicted score, win %, total, run line | 🟢 **MODEL** *(if ours)* | ⛔ **BLOCKED ON MODEL — no team run-scoring model exists** |
| **Top-3 player props per matchup** | the three best props in each game | 🟢 **MODEL** | ⚠️ **PITCHERS ONLY.** ⛔ **Hitters BLOCKED ON MODEL** |
| **Trends** | streaks and recent form | ⚪ **DESCRIPTIVE** | 🆕 ✅ **BUILT 2026-08-23 — the Trends tab.** Game logs are free |
| **Gizmo's Picks** | 4–5 per matchup with a why and a confidence % | 🟢 **MODEL** | 🆕 ✅ **BUILT 2026-08-23 — generated unattended by `card.py`, verified by `verify_card.py` before publish.** ⚠️ **STILL PITCHER MARKETS ONLY, and only the 70–80% band is fit to carry a public confidence number** |
| **Prop projections** | a projected number per prop | 🟢 **MODEL** *(pitchers)* · ⚪ **DESCRIPTIVE** *(hitters)* | 🆕 ✅ **REBUILT 2026-08-26 — a `PROJ` chip beside the line in BOTH Gizmo's Picks and Player Props, covers-style.** **It is the row's own confidence READ BACKWARDS, so the two can never disagree.** ⚠️ **HITTERS: hits · home runs · RBIs only, and ⚪ DESCRIPTIVE.** ⛔ **TOTAL BASES and H+R+RBI carry NO projection — T34/T34b/T35** |
| **Parlays / SGPs** | one pair per matchup (3 legs), plus 1–2 SGPs per slate | 🟢 **MODEL** + 🔵 **MARKET** *(price)* | 🆕 ✅ **PAIRS BUILT 2026-08-23 — two legs, Hard Rock only, two different games CHECKED ON GAME ID, product ≥ 1.80, labelled IN BAND / ABOVE BAND.** ⚠️ **PITCHER LEGS ONLY.** ⛔ **NO SGPs — legs are CORRELATED and books reprice them (ledger rule 54)** |
| **Odds tab** | all books, start times, starter + ERA | 🔵 **MARKET** | 🆕 ✅ **BUILT 2026-08-23 — the Odds tab, with BET-SLIP DEEP LINKS carrying the `{state}` substitution.** ⛔ **MARKET-DATA ONLY — ships as 🔵, NO confidence % (ledger rule 55)** |
| **Line movement** | how a number moved | 🔵 **MARKET** | ✅ **UNBLOCKED 2026-08-22 — the Phase 0 collector now stores snapshots every 30 min.** ⛔ **NO HISTORY EXISTS BEFORE 2026-08-22** |
| **Consensus** | % of tickets on each side | 🔵 **MARKET** | ⛔ **DROPPED — it is a measure of USERS and we have none** |
| **Best-odds button** | best price across books | 🔵 **MARKET** | ✅ **MARKET-DATA ONLY.** ⛔ **Shopping only — a best-of-each-side pair CANNOT be de-vigged** |
| **Player props tab** | hits · HR · RBI · total bases · H+R+RBI · outs recorded | 🔵 **MARKET** *(prices)* · 🟢 **MODEL** *(pitcher K and outs only)* | 🆕 ✅ **TAB BUILT 2026-08-23 — pitcher props carry their MODEL numbers; every HITTER market is 🔵 PRICES ONLY and still BLOCKED ON MODEL** |
| **News headlines** | injuries, lineups, scratches | ⚪ **DESCRIPTIVE** | 🆕 ✅ **BUILT 2026-08-23 — the News tab** |
| 🆕 **Track Record** | our hit rate, our calibration table, every graded pick | ⚪ **DESCRIPTIVE** | ✅ 🔴 **BUILT AND NO LONGER HARDCODED — ~~STILL HARDCODED~~ STRUCK 2026-08-31.** `[verified 2026-08-25 in the deployed `index.html`; this ROW was missed and stayed wrong for six days]` **It reads `data/latest/record.json`, regenerated nightly by `collect.py record`.** ⚠️ **It grades the MACHINE card only — never a shared denominator with the ledger** |
| ⛔ **Sportsbook ads** | — | — | ⛔ **DROPPED — Sam explicitly does not want them** |

---

# 💰 THE BILLING MODEL — MEASURED 2026-08-22 WITH `x-requests-last` PROBES

🔴 **THE TWO ENDPOINTS DO NOT BILL THE SAME WAY, AND THE DIFFERENCE IS UP TO 40× ON A SLATE.**

- ✅ **BULK — `/v4/sports/baseball_mlb/odds`** — **cost = markets × regions, PER CALL, NOT PER GAME.** `[measured]` **A probe with `markets=h2h,spreads,totals` and `regions=us,us2` returned 25 GAMES and billed 6.**
  **It returned 15 books:** `fanduel` · `draftkings` · `betmgm` · `betrivers` · `bovada` · `hardrockbet` · `espnbet` · `betparx` · `ballybet` · `fliff` · `betonlineag` · `mybookieag` · `lowvig` · `betus` · `betanysports`.
- ⚠️ **PER-EVENT — `/v4/sports/baseball_mlb/events/{id}/odds`** — **cost = markets × regions, PER GAME.** `[measured]` **A probe with `markets=batter_hits,batter_total_bases,batter_home_runs` and `regions=us,us2` on ONE event billed 6.**
- ✅ **HITTER PROP MARKETS — FIVE, NOT THREE.** ~~`batter_hits` · `batter_home_runs` · `batter_total_bases`~~ 🔴 **The three-market list is STRUCK 2026-08-24.** `[measured 2026-08-24 from `collect.py`]` **The collector requests FIVE batter markets — `batter_hits` · `batter_total_bases` · `batter_home_runs` · `batter_rbis` · `batter_hits_runs_rbis` — at `regions=us,us2`.** ✅ **The original three were confirmed present on `hardrockbet`, `draftkings`, `betmgm`, `espnbet`, `betparx`, `ballybet`, `fliff`, `betonlineag`; that availability finding is unchanged.** ⚠️ **FIVE markets × TWO regions is what makes a batter pull 150 credits — see the deployed budget in PHASE 0.**

| Pull | 2 regions | 1 region |
|---|---|---|
| **Game lines, WHOLE SLATE** | **6** | **3** |
| **All player props, 15 games** | **240** | **120** |
| **One full pull** | **246** | **123** |
| One pull a day | **≈ 7,400 / month** | — |
| Line movement 4×/day | 🔴 **≈ 29,500 / month** | — |

✅ 🔴 **THE CHEAP ARCHITECTURE, AND IT FALLS STRAIGHT OUT OF THE MEASUREMENT: LINE MOVEMENT MATTERS MOST ON MONEYLINE / RUN LINE / TOTAL, AND THOSE ARE 6 CREDITS FOR THE WHOLE SLATE.**
- **Pull them every 30 minutes, all day = ~8,600 / month.**
- **Take player props TWICE daily (open + pregame) = ~14,400 / month.**
- ➡️ **TARGET ≈ 25,000 CREDITS / MONTH FOR THE FULL PRODUCT.**

✅ **RESOLVED 2026-08-22 — THE $30 TIER IS 20,000 CREDITS/MONTH, CONFIRMED ON PURCHASE.** ~~⚠️ 🔴 THE $30 TIER'S CREDIT ALLOWANCE WAS NOT VERIFIED — the pricing pages did not return a trustworthy figure. Sam must check the credit count before buying.~~ **The Hard Rock-only fallback is no longer needed.** ~~✅ **The live schedule actually deployed spends ≈ 12,700/month — see PHASE 0.**~~ 🔴 **STRUCK 2026-08-24 — SAME DEFECT AS THE PHASE 0 TABLE: that figure was costed at ONE region for props.** ~~✅ **The schedule actually deployed spends ≈ 648/day · ≈ 19,400/month against 20,000** `[measured 2026-08-24 from `.github/workflows/collect.yml`]` — **see the deployed budget table in PHASE 0.**~~ 🔴 **STRUCK 2026-08-31 — SUPERSEDED BY THE 2026-08-28 SCHEDULE. `claude/update-schedule.md` OWNS THE COST: ≤372/day derived at a 15-game slate, ~330/day measured. Read it there and never off this page.**

---

# ✅ FREE DATA — statsapi, ZERO CREDITS

**Live game feed verified 2026-08-22:** `/api/v1.1/game/{gamePk}/feed/live` returns **inning state, score, current pitcher, current batter, count, outs, and the pitcher's live stat line.**

**Example capture:** **TOR@NYY, End 4th, 2-0. Cease pitching to Spencer Jones. Cease line: 4.0 IP / 0 H / 7 K / 65 P.**

`/api/v1/schedule?hydrate=probablePitcher,linescore,team` gives **records, probables and linescores.** ✅ **All team and hitter game logs for the future models come from here too.**

⚠️ **The whole free stack still inherits `claude/mlb-data-stack.md`'s rules — domain-check every fetched value, and never let a summarising fetch touch a number you will compute with.**

---

# PHASE PLAN

- ✅ **PHASE 0 — THE COLLECTOR. DONE. BUILT, DEPLOYED AND RUNNING SINCE 2026-08-22 — see the PHASE 0 section at the top of this document.**
- ✅ 🆕 **PHASE 1 — LARGELY DONE 2026-08-23. SEVEN TABS LIVE, THE CARD AUTOMATED, THE VERIFIER GATING THE PUBLISH — see the PHASE 1 section above.** ⚠️ ~~**What Phase 1 still owes: the track-record page reading the LEDGER AS DATA rather than being hardcoded.**~~ ✅ `[2026-09-21 Monday sweep]` **closed 2026-08-25 (reads `data/latest/record.json`) per this doc's own Phase 1 section.** ⛔ **SGPs are not owed — they are dropped on ledger rule 54.**
  *(original scope, kept as written)* **live scoreboard + pitcher props with a real confidence % + pairs/SGPs + the reasoning + the track-record page.** **Unmodelled tabs are PRESENT BUT MARKED.** **Market-data tabs (odds, best odds, line movement) ship as 🔵 MARKET.**
- ✅ 🔴 **PHASE 1'S LAST DEBT IS CLOSED 2026-08-25 — the track-record page now reads `data/latest/record.json` AS DATA. PHASE 1 IS DONE.**
- 🔴 **PHASE 2 — hitter props. CLOSED-FAILED 2026-08-24/25.** ~~**HITS and TOTAL BASES first** — the two with the cleanest game-log history.~~ **Both were attempted. FOUR pre-registered specifications lost to a smoothed season average: T27 (P(1+ hit), flat) +0.00236, T28 (two-stage) +0.00127, T29 (P(TB>=2)) +0.00119, T30 (+ real batting order) +0.00266/+0.00295 — every one against a +0.00500 bar.** ➡️ **The through-line: PLATE APPEARANCES dominate every hitter target and are themselves nearly unforecastable.** ⛔ **Hitter rows stay ⚪ DESCRIPTIVE. Reopening needs a NEW INPUT, not a new specification — and lineup slot, the input named in advance, has been spent.**
- 🔴 **PHASE 3 — team runs → predicted score → moneyline % → run line → totals. CLOSED-FAILED FOR THE SEASON 2026-08-25.** **FIVE arms across THREE specifications: T31a −0.0054, T31b +0.0403, T32a −0.0618, T32b +0.0302, T33 −0.0363. NOT ONE cleared a bar against a NAIVE baseline.** ➡️ **A game total is mostly same-day noise — the best correlation any arm reached between prediction and outcome was +0.1559, about 2% of variance, against real games running 1 to 27 runs.** ✅ **What it established: PARK and TEMPERATURE are real (corr +0.1363, +0.0913); WIND SPEED ALONE and DAY/NIGHT are not (−0.0010, −0.0113); park factor DOUBLE-COUNTS with a home club's runs allowed (+0.4773); and elevation does NOT (VIF 1.12).** ⛔ **Reopening needs a NUMERIC park-orientation table making wind direction usable, or captured market history reaching T31c's 400 games — NOT another specification.**
- ✅ 🆕 **PART 2 ITEM 1 — PROJECTIONS BESIDE THE LINES. DONE 2026-08-26.** **Sam: _"i want to include our projections as well in the player props section and the gizmos picks section, it shouldnt be a huge section but fit in next to their actual normal lines. similar to how covers does it"_ and _"it should go hand in hand with the confidence score."** 🔴 ⛔ **RETIRED 2026-08-27 BY LEDGER RULE 66, AND STRUCK HERE 2026-08-31 — THIS PARAGRAPH DESCRIBED THE SHIPPED DESIGN AND HAS DESCRIBED THE WRONG ONE FOR FOUR DAYS.** ~~**THE DESIGN FOLLOWS FROM THAT SECOND SENTENCE AND NOTHING ELSE: a projection computed independently could contradict the row it sits beside, so it is NOT computed independently. `card.py` takes the probability the row already displays and SOLVES FOR the central value that would produce it, under the SAME distribution that row already assumes. One number in, one number out.**~~ ➡️ **INVERSION MADE THE PROJECTION A PROPERTY OF THE ROW, so every rung of one ladder implied a different number and 51 of 608 player-market combos disagreed with themselves, worst 2.1 K.** **Sam: *"you should have the same numbers across the entire website."*** ✅ **THE SHIPPED DESIGN IS NOW ONE PROJECTION PER PLAYER PER STAT, LINE-INDEPENDENT BY CONSTRUCTION — pitchers show the model's own central value (`E[K]` / `mu`), hitters their own per-game mean — and `apply_projections()` is the ONLY writer of the field.** `[verified 2026-08-31 in `card.py`]` ✅ **Round-trip exact to 1e-10; validated on the four published cards at a mean gap of +0.073 K to the model's own `E[K]` (max 1.04, none ≥ 2) and +0.355 outs (max 3.99).** 🔴 ⛔ **THIS PROHIBITION IS NOW INVERTED AND IS STRUCK 2026-08-31 — IT INSTRUCTED A READER TO AVOID EXACTLY WHAT THE CODE SHIPS.** ~~**DO NOT print `central` (`E[K]`) instead — it is the MODEL half of a 50/50 blend and differs from the displayed `blend` BY DESIGN.**~~ ✅ **`central` IS what a pitcher row prints, deliberately, under ledger rule 66.** ⚠️ **The observation underneath it survives and is worth keeping: `central` is the MODEL half of a 50/50 blend, so a projection and its row's confidence are NOT two views of one number and may point different ways. That is correct and is not a contradiction to "fix".** ⛔ **DO NOT compute a projection in JavaScript — that is a second copy of the model, and this project has a documented history of two copies of one number drifting apart. The card publishes a `projections` index (~6 KB gzipped) and the Player Props tab JOINS against it.** ~~⚠️ **A row displaying exactly 50% gets NO projection: there is no direction to project, and Poisson discreteness would make an UNDER 2.5 at 50% print a projection of 2.67 — ABOVE its own line.**~~ 🔴 **NARROWED 2026-08-27 — IT WAS TOO BROAD AND IT COST 52 PITCHER ROWS THEIR PROJECTION ON ONE BOARD.** **The artifact is a property of the POISSON'S LUMPINESS, not of the probability: the NORMAL is continuous, and inverting it at 50% returns the LINE ITSELF, which contradicts nothing.** ✅ **The guard now applies to `poisson` and `negbin` only, and those fall back to the MODEL'S OWN CENTRAL VALUE (`lam` / `mu`) — not an inversion, so no artifact.** **See ledger rule 64.** ✅ **Rows BELOW 50% still project, and still project onto the losing side of the line — that is CORRECT. It is what "we like the over at +180 even though we project under the line" looks like, and hiding it would flatter the card.**
- ⚠️ **PHASE 4 — "whatever the API tier then supports" — THIS IS A PLACEHOLDER, NOT A PLAN, and it should be read as one.** 🔴 **With Phases 2 and 3 both closed-failed, the honest statement of what remains is NOT a fifth phase: it is (a) ~~the SEPTEMBER 1 RE-FIT, which is where roughly a dozen pre-registered tests are already owed~~ `[2026-09-21 Monday sweep]` the owed tests still OPEN after the 2026-09-01 re-fit (v5.0; T1 closed-failed, T3 closed-passed — read the rest in `claude/owed-tests.md`), (b) the ACCUMULATING COUNTERS that decide those tests, and (c) ATS / last-10 O/U once closing-line history is deep enough.** ➡️ **Anything beyond that is a new proposal and should be written down as one before it is built.**

---

# 🔴 THE TRACK-RECORD PAGE IS A REQUIREMENT, NOT A FEATURE

**Our hit rate, our calibration table, and EVERY graded pick — published.**

🔴 **IT IS THE ONLY THING THAT DISTINGUISHES THIS FROM EVERY OTHER PICKS SITE.** **Sam's own stated standard is that a pick without data-driven evidence behind it makes us unreliable** — a site that shows picks and hides the record is exactly that.

⛔ **It ships in Phase 1. It is not deferred, and it is not softened by goodwill** — the ledger already records the one time that was offered and declined (rule 34).

---

# 🔴 KNOWN BLOCKERS — STATED PLAINLY

1. ✅ **RESOLVED 2026-08-22.** ~~🔴 THE ODDS API KEY HAS BEEN IN PLAINTEXT IN SESSION TRANSCRIPTS FOR DAYS, AND SAM HAS TWICE DECLINED TO ROTATE IT. ⛔ IT MUST BE ROTATED BEFORE ANY PAYMENT METHOD IS ATTACHED OR ANYTHING SHIPS PUBLICLY.~~ **The key was rotated when the paid subscription was attached, and now lives ONLY in the GitHub repository secret `ODDS_API_KEY`.** ⛔ **THE OLD KEY IS COMPROMISED AND MUST NEVER BE REUSED.** ⚠️ **The blocker is kept here rather than deleted because it stood open for days across two refusals — that is the part worth remembering.**
2. ⛔ **THIS PROJECT'S DATA PULLS CURRENTLY RUN THROUGH A BROWSER EXTENSION, because the sandbox blocks direct fetching.** **A hosted product needs a real server, and no session can host anything itself.** ⚠️ **STILL OPEN.** **Phase 0 moved the SCHEDULED COLLECTION off the browser and onto GitHub Actions, but ANY AD-HOC PULL FROM A SESSION STILL NEEDS THE BROWSER EXTENSION** — the 2026-08-22 probe measured `403 Forbidden` to both APIs from this container. **And Actions is a collector, not a host: the dashboard still has no server.**
3. ⚠️ **SESSIONS ARE EPHEMERAL.** **"Live" means either a page REGENERATED ON A SCHEDULE or a REAL HOSTED APP Sam runs.** ⛔ **It does not mean a session sitting there watching.** ✅ 🆕 **2026-08-23: THE FIRST HALF IS NOW THE ANSWER — the page is REGENERATED ON A SCHEDULE by GitHub Actions and needs no session at all.**

---

# 🆕 THE FOOTBALL SURFACE — GIZMO'S DEFENSE BOARD, BUILT 2026-08-30

⚠️ **THIS DOCUMENT IS MLB. THE FIRST FOOTBALL SURFACE NOW EXISTS AND IS RECORDED HERE SO IT IS NOT LOST** — the NFL and CFB layers otherwise live in `claude/nfl-checklist.md` and `claude/cfb-checklist.md`.

**Sam, 2026-08-30:** *"i want you to track this data … touchdowns allowed vs certain positions, yards allowed vs certain positions, etc"* and *"do the trends first"*.

✅ **BUILT: a defensive trends board covering NFL (32 teams) and Power 4 college (188 defences faced), 2021–2025.** Per defence, per game, by position faced (QB / RB / WR / TE): **receptions · receiving yards · receiving TDs · carries · rushing yards · rushing TDs · attempts · completions · passing yards · passing TDs · interceptions**, each with a league rank, a range bar, and a **five-season trend line on a shared scale** so a rising line means a defence getting softer.

- ⚪ **DESCRIPTIVE, AND LABELLED AS SUCH ON THE PAGE — ledger rule 55.** ⛔ **No confidence number, no projection.**
- ⛔ **RANK 1 = ALLOWS THE MOST**, because the question asked of the board is *"how soft is this defence"*, not *"how good"*.
- ⚠️ **Ranks are WITHHELD below 8 games** and those rows are listed unranked rather than dropped.
- 🔴 **THE PAGE CARRIES ITS OWN CAVEATS RATHER THAN RELYING ON A READER KNOWING THEM:** college charges **sack yardage to rushing** (CFB QB rushing reaches −73, 23.5% of rows negative; the NFL bottoms at −10, 11.6%), so **CFB "rushing yards allowed to QBs" is largely a PASS-RUSH measure and is NOT comparable to the NFL column**; and the CFB rows describe **what Power 4 offences did to that defence**, which for a non-P4 defence may be one or two games.

🔴 **AND THE PAGE STATES THE THING IT WOULD BE EASIEST TO LEAVE OUT: a spread this wide is NOT evidence that the measure predicts.** `[measured 2026-08-30]` **T45 tested exactly that and it failed 8 arms of 8** — strength-of-schedule adjustment made player projections **worse** in both sports, both positions, both held-out seasons. ➡️ **The board is a trends surface. The moment one of its numbers drives a 🟢 MODEL number, that use needs its own pre-registered value test with a minimum effect size.** **See `claude/owed-tests.md` T36–T45.**

⚠️ **The board is published as an ARTIFACT, not as a tab in `index.html`.** ⛔ **It is therefore NOT refreshed by the collector yet** — `cfb.py` writes `allowed-by-position-YYYY.json.gz` on every run, but nothing joins that file to a page. **`nfl.py` does not write the file at all yet.** ➡️ **Two owed items, stated rather than implied.**

---

# Changelog

- 🆕 **2026-09-21, Monday sweep (text-only, headless)** — six live lines corrected: the stale "PHASE 0 still says private" note (fixed 08-31); "Phase 1 still owes the record page" (closed 08-25); "the SEPTEMBER 1 RE-FIT … owed" (it ran — T1 failed, T3 passed); the live "three props blocks a day (4am/10am/4pm)" struck in favour of `claude/update-schedule.md`; "neither a browser nor network access" corrected to the real reasons (no key, egress refused, WebFetch banned); PAIRS now notes 3- and 4-leg parlays on rule 28's bands.
- **Aug 27 2026 (GitHub stopped firing the schedule, the card failed its own verifier on a live board, and one of those three failures was the verifier's fault)** — 🔴 **THE COLLECTOR WENT SILENT FOR 21 HOURS AND THE REPO COULD NOT SAY WHY. The Actions page could: the workflow was NOT disabled, Actions permissions were on "Allow all", the repo is Public so minutes are free and unmetered, and the last scheduled runs were GREEN — and a `workflow_dispatch` fired and succeeded on the first try.** ➡️ **So the failure is the SCHEDULE EVENT ALONE.** ⛔ **CAUSE NEVER CONFIRMED, AND IT IS RECORDED AS UNCONFIRMED — ledger rule 62 carries the four-step diagnostic so the next session does not re-derive it.** ✅ **Ten modes were dispatched by hand to bring the 8/27 slate current.** 🔴 **THE `card` RUN FAILED, AND `verify_card.py` WAS RIGHT TWICE AND WRONG ONCE — which is the entry worth reading.** **(1) 52 PITCHER ROWS HAD NO PROJECTION because the coin-flip guard suppressed the NORMAL as well as the Poisson; the Normal is continuous and inverting it at 50% returns the line, which contradicts nothing. Landen Roupp's `outs 16.5` at a blend of 49.6/50.4 went from blank to 16.46.** **(2) A TOTAL-BASES MEAN OF 1.469 PRINTED AS "1.5" BESIDE "under 1.5" and read as the card arguing with itself — a ROUNDING artifact, not a disagreement, so the DISPLAY is what changed: the second decimal is kept in exactly that case and nowhere else.** 🔴 **(3) THE THIRD FAILURE WAS THE CHECK'S OWN: it traced every top-10 row to `picks[] + below_price_floor[]`, which are the board AFTER `BOARD_MAX` truncation — so two correct plays failed a check they should have passed.** ✅ **The projection index now carries a one-byte `"p"` flag meaning "card.py priced this exact row", and the check traces against that — PINNED FROM BOTH ENDS so it cannot become a rubber stamp: every carded row must carry it AND it must cover strictly fewer entries than the index (1,185 of 1,400).** ⛔ **Publishing the pool's 2,196 keys was REJECTED at ~48KB on a file the PAGE DOWNLOADS.** ⚠️ 🔴 **THE LESSON, BECAUSE THIS PROJECT HAS NOW HIT IT TWICE: A FALSE FAIL COSTS A MORNING AND TRAINS THE READER TO IGNORE THE VERIFIER, WHICH IS THE MORE EXPENSIVE FAILURE OF THE TWO.** ✅ **Per `CLAUDE.md`, the old check was REPLACED, not deleted.** 🔴 **AND THE SCHEDULE WAS CUT FROM 29 CRON ENTRIES TO 16: a mode is now a LIST, one cron does a time block, a failed pull fails the job AFTER the commit so paid data still reaches the repo, and the card keeps its own cron.** 🆕 **A CARD NOW BUILDS AT 4:42am ET** — Sam: *"i thought we changed all of the upload times from later in the day to 4am"*; **the PROPS pulls had moved on 8/26 and the CARD had not, so at 4am the lines were fresh and the picks were still yesterday's.** ⚠️ **The trade, stated: that card is built BEFORE lineups post, and the 10:46am build replaces it.** 📊 **Projections index 1,316 → 1,400; every row `card.py` prices now reaches it, alternate rungs included.** ⛔ **WHAT DID NOT CHANGE: no model coefficient, no `blend` definition, no calibration figure, no billing measurement, no de-vig example, no dropped-feature decision; the three-kinds discipline and ledger rule 55 are untouched; the 1.8x pair floor and the −700 price floor are untouched; Phases 2 and 3 remain CLOSED-FAILED; credit cost is UNCHANGED at 606/day; and every dated changelog entry below is history and is left exactly as written.** ⚠️ **Rules 62–65 written to `claude/pick-ledger.md`.** ⛔ **DELIVERED AS `gizmos-p2r.zip` + `collect.yml` FOR MANUAL UPLOAD — push is still proxy-blocked and `.github/workflows/` still cannot be written by the app.** ⚠️ **Merged, not rewritten, per ledger rule 43: `project_read` → tool result extracted VERBATIM from the session transcript JSONL → programmatic patch with `assert count == 1` on every anchor → `collections.Counter` line-loss check → upload with `local_path`.**

- **Aug 26 2026 (PROJECTIONS SHIP — and the hitter half needed three pre-registered tests to decide what a hitter projection may even be)** — ✅ 🔴 **PART 2 ITEM 1 IS DONE: a small `PROJ` chip now sits beside the line in BOTH Gizmo's Picks and Player Props, covers-style, exactly as Sam specified.** 🔴 **THE ONE DESIGN DECISION THAT MATTERS: A PROJECTION IS AN INVERSION OF THE DISPLAYED CONFIDENCE, NEVER A SECOND ESTIMATE.** **Sam's brief already settled it — _"it should go hand in hand with the confidence score"_ — and only inversion GUARANTEES that. `card.py` solves for the central value that reproduces the probability the row already shows, under the same distribution that row already assumes; round-trip is exact to 1e-10 and a confident pick can never project against itself.** ✅ **Validated on the four published cards: pitcher strikeouts mean gap to the model's own `E[K]` **+0.073 K** (max 1.04, NONE ≥ 2); outs **+0.355 outs** (max 3.99, one ≥ 1 inning).** ⚠️ 🔴 **MY SYNTHETIC EXAMPLE HAD LOOKED WRONG AND THE REAL DATA SETTLED IT: an 85% confidence on a 5.5 line implies 8.5 K, which reads absurd — but that COMBINATION NEVER OCCURS on a real card. Actual 85%+ confidences sit on LOW lines (`o2.5` at 95% implies 6.3 K). Sam's instinct and the arithmetic agree once the input is real, which is why it was checked against published cards rather than argued about.** 🔴 **THE HITTER HALF COULD NOT BE SHIPPED THE SAME WAY, BECAUSE A HITTER ROW HAS NO MODEL AND THEREFORE NO DISTRIBUTION — so T34, T34b and T35 were pre-registered, WITH THE BAR FIXED BEFORE ANY FIT, and they decided it.** ✅ **PASSED AND SHIPPING: hits (Poisson, p90 0.202), home runs (Poisson, 0.022), RBIs (NEGATIVE BINOMIAL holding the player's own game-to-game variance, 0.117 — plain Poisson FAILED at 0.299).** ⛔ **FAILED AND SHIPPING NOTHING: total bases and Hits+Runs+RBIs. On total bases, plain Poisson missed by **0.673** at the tail, a negative binomial by **0.350**, a compound Poisson (hits × the player's own extra-base mix) by **0.287** — against a bar of **0.25** fixed before any of them were fitted. Projecting the observed mean directly landed on the LOSING side of the line in 5% of rows, ALL of them unders.** ➡️ **THOSE TWO MARKETS CARRY NO PROJECTION AT ALL AND THE PAGE STATES THE ABSENCE AND THE REASON. A precise-looking number that is wrong by two-thirds of a base is worse than no number on a page whose entire pitch is accuracy.** 🔴 **MY OWN PRE-REGISTERED PREDICTION WAS WRONG AND IS RECORDED AS SUCH: I predicted total bases would fail BIASED HIGH by +0.2 to +0.4. It is not biased at all — its mean error is −0.016, the second-smallest of the five markets — it fails on SPREAD, which is the WORSE failure, because a bias can be subtracted and an unbiased-but-wide estimator cannot.** ⛔ **THREE ATTEMPTS HAVE NOW FAILED ON TOTAL BASES AND A FOURTH DOES NOT GET AN EASIER BAR — it gets a new pre-registration at the same 0.25. Same pre-commitment shape as T29 for hitters and T33 for Phase 3, made for the same reason: so the decision is not taken while disappointed.** 🔴 **ALL THREE SHIPPED HITTER PROJECTIONS ARE LABELLED ⚪ DESCRIPTIVE, NEVER 🟢 MODEL — ledger rule 55 binds hardest here, because what they invert is the player's own RECORD.** ✅ **The verifier went 33 → 46 checks, and the new block was FAULT-INJECTED before being trusted: six deliberate defects written into a real card, all six caught. The point-in-time check is written as a DIFFERENCE — recompute each RBI projection with the date filter and without it, and the card must match the filtered one — because asserting "the filter exists" would prove nothing; it reported 0 separable rows on the test slate and SAYS SO IN ITS OWN NAME.** ⛔ **WHAT DID NOT CHANGE: no model coefficient, no `blend` definition, no calibration figure, no billing measurement, no de-vig example and no dropped-feature decision was altered; the three-kinds discipline and ledger rule 55 are untouched; the 1.8x pair floor and the −700 price floor are untouched; Phases 2 and 3 remain CLOSED-FAILED; and every dated changelog entry below is history and is left exactly as written.** ⚠️ **Merged, not rewritten, per ledger rule 43: `project_read` → tool result extracted VERBATIM from the session transcript JSONL → programmatic patch with `assert count == 1` on every anchor → `collections.Counter` line-loss check → upload with `local_path`.**

- **Aug 25 2026 (PHASES 2 AND 3 ARE BOTH CLOSED-FAILED, PHASE 1'S LAST DEBT IS CLOSED, AND THIS DOC WAS A DAY BEHIND THE CODE ON ALL THREE)** — 🔴 **THE HEADLINE CORRECTION: THIS PAGE DESCRIBED THE HITTER MODEL AND THE TEAM-RUNS FAMILY AS "NOT BUILT". BOTH WERE BUILT, TESTED AND FAILED, AND "NOT BUILT YET" AND "TESTED AND DID NOT CLEAR" ARE DIFFERENT CLAIMS.** **PHASE 2 — FOUR pre-registered specifications lost to a smoothed season average (T27 +0.00236, T28 +0.00127, T29 +0.00119, T30 +0.00266/+0.00295, all against +0.00500), and the through-line is that PLATE APPEARANCES dominate every hitter target and are themselves nearly unforecastable. PHASE 3 — FIVE arms across THREE specifications (T31a −0.0054, T31b +0.0403, T32a −0.0618, T32b +0.0302, T33 −0.0363) and NOT ONE cleared a bar against a NAIVE baseline; a game total is mostly same-day noise, the best correlation any arm reached being +0.1559.** ✅ **What Phase 3 established even in failing: PARK and TEMPERATURE are real (+0.1363, +0.0913), WIND SPEED ALONE and DAY/NIGHT are not (−0.0010, −0.0113), park factor DOUBLE-COUNTS with a home club's runs allowed (+0.4773), and elevation does NOT (VIF 1.12) — the last of which CONTRADICTED the pre-registration's own prediction, which is why the prediction was written down.** ✅ 🔴 **PHASE 1'S LAST STATED DEBT IS CLOSED AND THIS DOC WAS WRONG ABOUT IT: "THE TRACK RECORD TAB IS STILL HARDCODED" is STRUCK.** `[verified 2026-08-25 in the deployed `index.html`]` **The tab reads `data/latest/record.json`, regenerated nightly by `collect.py record` from stored results and stamped `"kind": "DESCRIPTIVE"`.** ⚠️ **It grades the MACHINE card only — hand-built cards and Sam's slips were removed 2026-08-24 at his instruction — so it and the ledger's record are DIFFERENT POPULATIONS and must never share a denominator.** 🔴 **THE VERIFIER CHECK COUNT MOVED AGAIN: 21 → 27 → 33 `[counted 2026-08-25 from the source]`. THIS IS THE THIRD FIGURE THIS DOC HAS CARRIED, and the lesson is the project's own standing rule — NEVER PUT A COUNT ANYWHERE YOU CANNOT AUTO-UPDATE. Count the source.** ⚠️ **PHASE 4 IS RELABELLED AS WHAT IT IS — A PLACEHOLDER, NOT A PLAN. With Phases 2 and 3 both closed-failed, what actually remains is the SEPTEMBER 1 RE-FIT and its roughly dozen owed tests, the ACCUMULATING COUNTERS that decide them, and ATS / last-10 O/U once closing-line history is deep enough. Anything beyond that is a NEW PROPOSAL and should be written down as one before it is built.** ⛔ **WHAT DID NOT CHANGE: no measured figure, billing probe, calibration snapshot, de-vig example or dropped-feature decision was altered; the three-kinds discipline and ledger rule 55 are untouched; the tab-by-tab table, the track-record REQUIREMENT section and the three known blockers are untouched; and every dated changelog entry below is history and is left exactly as written, including its now-superseded counts.** ⚠️ **Merged, not rewritten, per ledger rule 43: `project_read` → tool result extracted VERBATIM from the session transcript JSONL → programmatic patch with `assert count == 1` on every anchor → `collections.Counter` line-loss check → upload with `local_path`.**

- **Aug 24 2026, Monday sweep (the five-book widening reached the CODE on 8/23 and never reached THIS DOC)** — 🔴 **THE HEADLINE DEFECT: on the evening of 2026-08-23 Sam widened the odds source to FIVE BOOKS and the props pull went back to `regions=us,us2`. That shipped in `collect.py` and `.github/workflows/collect.yml` the same night. THIS PAGE WENT ON ASSERTING A `us2`-ONLY PITCHER-PROPS PULL FOR A DAY.** ⚠️ **The 8/23 entry below recorded the OPPOSITE failure — a rule live in a DOC that had not reached the CODE. On 8/24 the same gap ran the other way. Both are recorded, because the moral is that neither direction announces itself.** ✅ **EDIT 1 — the section headed "THE PITCHER-PROPS PULL IS NOW `us2`" is STRUCK, heading and body: the pull is `REGIONS_FULL` (`regions=us,us2`), widened 8/23 evening under ledger rule 48's five-book set, and `claude/pick-ledger.md` RULE 48 IS NAMED AS THE OWNER OF THAT SET RATHER THAN THE SET BEING RESTATED HERE.** ✅ **The section's original lesson — a rule written in a doc is not a rule in the code — is KEPT INTACT, which is why the section is struck and not deleted.** ✅ **EDIT 2 — "it also halves that pull … 48 credits instead of 96" is STRUCK; at two regions that pull is 96 CREDITS PER PULL.** ✅ **EDIT 3 — "LEDGER RULE 48 / STEP 5 HAS SAID HARD ROCK ONLY (`us2`) SINCE 2026-08-22" is STRUCK; rule 48 now specifies five books at `regions=us,us2`. `us_dfs` STAYS BANNED and PrizePicks is still never the source of a NUMBER.** 💰 **EDIT 4 — THE PHASE 0 CREDIT BUDGET WAS COSTED AT ONE REGION AND ITS TIMES WERE STALE. Struck and replaced with the budget AS DEPLOYED, `[measured 2026-08-24 from `.github/workflows/collect.yml`]`: gamelines 6 × 28 = 168/day; batter props 150 per pull × 2 = 300/day (5 markets × 2 regions × 15 games); pitcher props 90 per pull × 2 = 180/day (3 markets × 2 regions × 15 games); TOTAL ≈ 648/day ≈ 19,400 of a 20,000-credit plan.** ⚠️ **That is TIGHT and it is a DELIBERATE TRADE — more books AND fresher props are not both affordable at this plan — with a 750-credit reserve guarding the tail of the month (props stop, gamelines keep running). The two prop pulls are 14:20Z / 20:20Z (batter) and 14:10Z / 20:10Z (pitcher), i.e. 10:20am and 4:20pm ET.** 🔴 **These figures are READ FROM THE WORKFLOW, NOT ASSUMED.** ✅ **EDIT 5 — the hitter prop market list went from THREE to FIVE: `batter_rbis` and `batter_hits_runs_rbis` added, `[measured 2026-08-24 from `collect.py`]`. Five markets × two regions is what makes a batter pull 150 credits.** 🔴 **EDIT 6 — THE VERIFIER CHECK COUNT DOES NOT RECONCILE AND NEITHER PUBLISHED FIGURE WAS RIGHT: this doc said 21, the repo's `CLAUDE.md` says 26, and `[counted 2026-08-24 from the source]` `verify_card.py` contains 27 `ck(...)` calls. Restated here as 27.** ⛔ **`CLAUDE.md` IS REPORTED, NOT FIXED — a headless run may not push a code change.** ✅ **EDIT 7 — "IT IS NOT YET IN THE REPO" is STRUCK: `[verified 2026-08-24]` `github.com/smh0602/gizmos-picks` is live and public, the collector has been committing data since 2026-08-22, and `data/` holds dated snapshots through today.** ⚠️ **Flagged but NOT edited: PHASE 0 still calls the repo *(private)*.** ✅ **EDIT 8 — THE INLINE MODEL COEFFICIENTS ARE NOW POINTERS: the v4.0 K and outs equations point at `claude/mlb-projection-model.md`, which owns them, and the two centering constants point at `claude/mlb-opponent-database.md`, which owns them.** ⛔ **NO COEFFICIENT VALUE AND NO CONSTANT VALUE WAS ALTERED — ONLY RELOCATED. The rule that the two constants must never be mixed, and that a variable and its constant must come from the same pull, is KEPT VERBATIM IN FORCE.** 🧹 **SWEEP — the doc was swept, not spot-checked, for further live `us2`-only instructions and further one-region credit figures. ONE more was found and struck: "The live schedule actually deployed spends ≈ 12,700/month" in THE BILLING MODEL, the same one-region costing, now ≈ 19,400/month.** ✅ **NOT A DEFECT, LEFT ALONE: the 2-regions/1-regions comparison table in THE BILLING MODEL is a `[measured 2026-08-22]` PRICE REFERENCE showing both costings, not an instruction to pull one region; and "Hard Rock only" on PAIRS and on the ALT LADDER is ledger rules 31/54 about which book MULTIPLIES, not a region instruction.** ⛔ **WHAT DID NOT CHANGE: no graded row, money row or dated card table was touched; the Aug 23 changelog entry is dated history and is left EXACTLY as written, including the coefficient and constant figures it quotes and its now-superseded `us2` and 48-credit claims; the three-kinds discipline and ledger rule 55 are untouched; the de-vig requirement and its worked example are untouched; the calibration snapshot, the model coverage (still TWO MARKETS FOR ONE POSITION), the phase plan, the tab-by-tab table, the track-record requirement and the three known blockers are all untouched; the `[measured 2026-08-22]` billing probes are untouched; and no coefficient, constant or credit MEASUREMENT was altered — only relocated or restated against the deployed source.** ⚠️ **Merged, not rewritten, per ledger rule 43: `project_read` → tool result extracted VERBATIM from the session transcript JSONL → byte count verified → programmatic patch with `assert count == 1` on every anchor → `collections.Counter` line-loss check → re-read and `created_at` compared immediately before upload → upload with `local_path`.**
- **Aug 23 2026 (v0.3 — the dashboard, the automated card and its verifier; and the bet-state selector was missing 22 jurisdictions)** — ✅ 🔴 **THE STATUS LINE CHANGES FOR THE SECOND TIME: v0.1 was SPEC ONLY, v0.2 was DATA LAYER RUNNING, AND v0.3 IS SEVEN LIVE TABS — Scores & Matchups, Gizmo's Picks, Odds, Player Props, Track Record, Trends, News — plus clickable box scores, pitcher props with their model numbers, bet-slip deep links with a `{state}` substitution, and finished games dropping off every tab so the board rolls to the next day by itself.** 🆕 **`card.py` GENERATES THE DAILY CARD UNATTENDED ON THE RUNNER (`python collect.py card`) AND SPENDS ZERO ODDS API CREDITS — it calls nothing, reading `data/latest/pitchers.json.gz` and `data/latest/props.json.gz` and writing `picks/<date>.json`.** 🆕 **`verify_card.py` RUNS BEFORE THE COMMIT STEP AND EXITS NON-ZERO ON ANY FAILURE, SO A BAD CARD IS NEVER PUBLISHED — 21 checks, all passing on the first real run, including a Poisson CDF against 200,000 simulations (max gap 0.307 points), the Normal outs probability re-derived from the raw game log rather than read back (max gap 0.0400 points), 32/32 raw hit rates re-counted by hand, a point-in-time check that no start on or after the slate date enters a denominator, no same-game parlay checked on GAME ID, no pair below 1.8x, every price traced to a raw stored pull (0 invented), and a check that `blend` is the plain 50/50.** 🔴 **THAT LAST CHECK IS THE POINT: T21 AND T22 REMAIN NOT ADOPTED AND THE CODE ENFORCES IT — `blend` is the only column entering calibration, `carried` carries the T21/T22 flags and enters NO denominator.** ⚠️ 🔴 **ONE DELIBERATE DIFFERENCE FROM THE 8/22 HAND-BUILT CARD IS STATED RATHER THAN LEFT TO BE NOTICED: the automated `carried` applies NO discretionary nudge toward the matched class, because STEP 4B is a FLAG and folding it in — even a third of the way — would be a new model choice with no pre-registered test.** ✅ **T23 AND T24 ARE APPLIED IN CODE: the raw rate is ALL starts with NO 4+IP filter (T23), and the matched class is selected on the DURABILITY axis for outs props and the K axis for strikeout props (T24), with both the all-starts and 4+IP figures reported and the ALL-STARTS one used as the reference for the ≥15-point flag.** 🔴 **TWO COLLECTOR DEFECTS FIXED, BOTH OF THE SAME SHAPE — A RULE WRITTEN IN A DOC THAT NEVER REACHED THE CODE: the pitcher-props pull was still on `regions=us,us2` although ledger rule 48 narrowed it to `us2` on 8/22 (now `REGIONS_CHEAP`, and that pull is halved to 48 credits from 96), and the alt strikeout ladder was being PULLED AND THEN DROPPED at the board stage, so a rung-walk into the 1.8x band had nothing to walk.** ✅ **Ladders are now stored per pitcher, Hard Rock only, deduped across `hardrockbet` and `hardrockbet_oh`, each rung carrying BOTH the feed's `o2.5` and the app's `To Record 3+` form (rule 49), priced through the same model, with the card starring the safest rung that still clears the −700 floor.** ⛔ **`pitcher_outs_alternate` is deliberately NOT requested — Hard Rock posts no alt outs market at all, Sam-confirmed.** ✅ **"Best price across books" and "what does Sam's book say" were ONE FIELD and are now two: each prop keeps Hard Rock's own price and link in an `hr` field, the card quotes Hard Rock, and a play Hard Rock did not post is STILL PRINTED (rule 53) with the fact stated and the other book named — and barred from pairs, because only Hard Rock multiplies.** 🔴 **THE CARD IS DATED BY THE SLATE, NOT THE CLOCK — the ET date of the earliest game that has not started — because at 11pm ET the board holds tomorrow's games and none of today's, and dating off the clock would file tomorrow's card under today.** ✅ **The opponent table is rebuilt nightly on the runner from the same pull the model reads, with its centering constant taken from that same rebuild; measured 2026-08-23 against the published table across 3,802 IP-filtered starts, mean |ΔE[K]| 0.021 K and max 0.064 K.** ⛔ **THAT DOES NOT RETIRE THE PUBLISHED TABLE AND DOES NOT CHANGE ITS CONSTANT (4.7376); the runner computes its own (4.7756) on a slightly different population AND THE TWO MUST NEVER BE MIXED.** ⏰ **Two new cron entries — `45 14 * * *` and `50 21 * * *` (card) — plus `45 21 * * *` as a props-board rebuild so the evening card joins the 21:40Z odds pull, because a card built at 10am may not assert a 6pm price (rule 49); minutes deliberately off `:00` and `:30`.** 🔴 **THE BET-STATE SELECTOR HELD 29 ENTRIES AND IS NOW ALL 50 STATES PLUS DC (51), grouped into "Sportsbooks operate here" and "Other states". Sam reported ~20 missing; the true count was 22. The BOOK, not the page, is the authority on where it operates, and a missing option was a dead bet link with no way out.** 📌 **FIRST AUTOMATED CARD: 2026-08-23 slate, 32 plays across 10 games, 8 pairs all inside 1.8x–2.1x, 118 alt rungs; generated 2026-08-23T03:15Z from odds pulled 02:55:33Z and game logs pulled 02:37:45Z.** ⚠️ **IT IS NOT YET IN THE REPO — the container could not push, so Sam is uploading by hand and will trigger the first run himself.** ⛔ **WHAT DID NOT CHANGE: the three-kinds discipline (🟢 MODEL / 🔵 MARKET / ⚪ DESCRIPTIVE) and ledger rule 55 are untouched and are now load-bearing on a public surface; the de-vig requirement is untouched; the model coverage is STILL TWO MARKETS FOR ONE POSITION and the calibration snapshot is unchanged; the hitter model (Phase 2) and the team-runs family (Phase 3) are still unbuilt; ATS and last-10 O/U still need accumulated closing-line history; the Track Record tab is built but STILL HARDCODED and does not read the ledger as data; blocker 2 (no host) and blocker 3 (ephemeral sessions) both stand, though the scheduled half of blocker 3 is now answered; and NO calibration figure, phase definition, billing measurement or dropped-feature decision was altered.** ⚠️ **Merged, not rewritten: `project_read` → local file in a PRIVATE scratch directory → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check → re-read and `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.**
