# gizmos-picks — read this before changing anything

This repo backs a live MLB betting-analysis product for one user, Sam. It
publishes probability estimates he bets real money against, and it keeps a
permanent record of how those estimates performed.

You are probably a fresh GitHub Action session with no memory of how any of
this came to be. **Almost every rule below exists because something went
wrong once.** Do not relax one because it looks over-cautious.

---

## WORKING WITH SAM — standing rules [Sam, 2026-09-22]

1. MONEY: Never buy, subscribe to, upgrade, or sign up for any paid
   service, API, plan or tool. Never enter payment details. Sam pays for
   the Odds API ($30/month, 20,000 credits) and his Claude subscription;
   the college football data service and GitHub cost him nothing today.
   Any change that adds cost, or that would push Odds API spend beyond the
   current plan (new markets, new regions, more pulls), is proposed to Sam
   first, with the exact added credits per day from budget.py, and waits
   for his yes.
2. Do not ask permission for work you can do yourself. Only stop for
   things that need Sam's hands. When a checklist task is done, move
   straight to the next one.
3. Nothing that updates site data may depend on a manual run. Everything
   data-related must be scheduled. Sam's only manual jobs are merging pull
   requests and hand-uploading workflow files that contain a cron: block.
4. Any GitHub instruction to Sam is click by click for Windows: which
   page, what the breadcrumb at the top should read, which button, which
   folder. Always give the exact file location and the exact commit
   message ready to paste. Anything he must upload by hand comes with a
   separate UPLOAD .md instruction file.
5. Every pull request description starts with a plain-English summary Sam
   can read on his phone: what changed, why, and what he should see after
   merging.
6. Whatever is built for college football is built for the NFL too, and
   vice versa.
7. Sam gets the data and decides the plays. Never hide a play because you
   dislike it; label it instead. (The one exception is his own rule:
   parlays below their payout floor are never shown.)
8. Tell Sam plainly when you got something wrong. Never defend an earlier
   claim over the evidence.
9. Every lasting doc keeps a dated changelog; strike superseded text
   instead of deleting it; record every mistake with its root cause.
10. API keys stay GitHub secrets. Never show, ask for, or commit a key.
11. Betting rules: parlays are 2 legs 1.8x or more and 3+ legs 3x or more,
    with no ceiling, ranked by the model's chance to hit. Football books
    are Hard Rock, FanDuel and DraftKings only; MLB keeps its 5. MLB is
    unfrozen and everything is kept current automatically.
12. Pitcher stat lines show only: IP, H, R, ER, BB, K, pitch count with
    strikes, decision/record, and first-pitch strikes per batters faced.
13. RESERVED FOR SAM, even though you could do them: spending money;
    deleting data or editing any published pick; changing a model
    coefficient, a test's pass bar, or a pre-registered test; and the
    backtest direction rule, which must be approved before anyone looks at
    signal-vs-outcome data. Propose these; never do them.
14. Changelogs are for docs, not code: in code, git history is the
    changelog. In docs, keep entries short and plain, strike rather than
    silently rewrite, and move finished history into docs/project-archive/.
15. One pull request per task. Never have more than 3 of your pull
    requests waiting for Sam at once; if there are 3, stop and tell him.
16. After Sam merges, verify it yourself: confirm the change is on
    origin/main by content, and check that the next scheduled run of the
    affected workflow is green. A green run alone does not prove the new
    code landed.

---

## ✅ MLB IS OPEN FOR WORK AGAIN — `[Sam, 2026-09-22]`

~~**Sam, 2026-09-12: *"we have mlb perfected we dont need to touch it."***
DO NOT CHANGE `card.py`, `verify_card.py`, the MLB model, the MLB card, or
any MLB doc. A LIVE MLB FAILURE IS REPORTED AND LEFT.~~ **SUPERSEDED.**

**Sam, 2026-09-22: *"unfreeze all mlb. anything else thats out of date
regarding any of the sports should be kept up to date right now and it
should be kept up to date from now on."***

✅ **MLB may be changed again** — under every other rule in this file:
a fix ships with a guard, a check is never weakened, and the rows in
"What must never change without Sam saying so" still need Sam.
⚠️ **The model coefficients are still fitted, not tuned** — "unfrozen"
means the code can be worked on, not that a coefficient may be nudged.
✅ **"Kept up to date" is automatic, never a manual run.** The MLB pitcher
and opponent tables are rebuilt by `mlb_tables.py` after every `pitchers`
pull and carry freshness contract rows.

---

## 🔴🔴 EVERY FIX SHIPS WITH A GUARD. A FIX ALONE IS HALF THE WORK.

**Sam, 2026-09-14: *"from now on when you notice a problem not only do we
need a fix to it now, but we also need a automated fix for said
problem."***

⛔ **DO NOT CLOSE ANYTHING WITH ONLY THE INSTANCE REPAIRED.** Every defect
leaves with two things:

1. ✅ **The fix** — the instance, corrected.
2. ✅ **The guard** — something automated that FAILS if this returns. A
   test, a check, an assertion, a watchdog question. **It must fail on the
   defect and pass after the fix**, and you must have watched it do both.

🔴 **PREFER THE GENERIC GUARD OVER THE SPECIFIC ONE.** A check naming the
one file that broke covers exactly that file — and this repo has shipped
that mistake twice (rules 246, 130). ➡️ **Ask what CLASS the defect
belongs to and guard the class** where the class is answerable; guard the
instance only when it is not, and say which you did.

⚠️ **A GUARD THAT CANNOT FAIL IS NOT A GUARD.** Prove it bites before you
call it done — an empty match, a stripped comment, a fixture missing the
file under test, and a check that asserts its own prose have all passed
green in this repo while proving nothing (rules 67, 244, 249).

⛔ **AND A GUARD THAT FIRES ON CORRECT CODE IS THE OTHER FAILURE, NOT A
SAFE ONE.** Three of mine did that in one week, each caught only by
running it. **Drive it against the real artifact, not against your
expectation of it.**

---

## 🔴🔴 IF YOU CAN PUSH TO THIS REPO, READ THIS BEFORE YOU DO

`[added 2026-09-15, the day a session could push here for the first
time — measured on the probe, not inferred]`

⚠️ **MOST OF THIS REPO WAS BUILT BY A SESSION THAT COULD NOT PUSH.** It
handed a human a folder, he dragged it into the GitHub web UI, and the
change was then verified byte-for-byte against `main`. If you can push,
that step is gone — **and so is the human who was reading every file on
its way in.**

### ⛔ 1. WORKFLOW FILES CONTAINING A `cron:` BLOCK STILL GO THROUGH SAM BY HAND

🔴 **GitHub attributes a scheduled run to the repository user who last
changed the workflow's `cron:` block.** Every one of them depends on that
user staying a human with write access.

<!-- CRON TOTAL: 57 -->
⚠️ **THE COUNT ABOVE IS DERIVED, NOT REMEMBERED.** `test_watchdog.py`
counts every `- cron:` line in `.github/workflows/` **and in files staged
under `docs/upload/`**, one per file name (`wfparse.cron_total`), and
fails if this comment disagrees. ✅ `[Sam, 2026-09-23]` Staged files count,
so the total is right before AND after Sam's upload: no red window. A
staged copy that differs from the deployed one is a PENDING upload, not a
failure, and is counted at its STAGED version (what will be live)
(`wfparse.pending_uploads`). `runs_report.py` flags a new staged cron, or
a pending update, still not uploaded 48 hours after its PR merged. ⛔ **IF IT FAILS, DO NOT JUST EDIT THE NUMBER** — ask
first whether a cron was added or lost on purpose. `[This line exists
because the prose originally said "50 crons", which was already wrong
when it was written, and a test asserting that literal string would have
reddened on anyone who corrected it. Rule 166: a number written down is a
claim about the world, and it goes stale.]`

**MEASURED 2026-09-15 on a push probe:** a commit pushed from a
repo-connected Claude session shows on GitHub as **`claude committed`**,
**not** as the repository owner.

⚠️ **WHAT IS NOT MEASURED: whether a cron-block change under that author
actually stops scheduled runs.** ⛔ **And that test is destructive** — if
it fails, every cron stops firing **silently**: no red run, no failed
check, and the watchdog cannot report it **because the watchdog is what
summons the repair agent.** The channel that would carry the alarm is the
channel that dies.

➡️ **So: change `.github/workflows/*.yml` in a PR or a hand upload, never
a direct push, until somebody measures it.** The convenience is real and
the downside is the whole product going dark; those are not comparable
quantities.

### ⛔ 2. THE REASONING BEHIND THIS PROJECT IS NOT IN THIS REPO, AND YOU CANNOT READ IT

The ledger, the pre-registered tests, the model derivations and the
architecture notes live in **Sam's Claude project docs** — `claude/...`
paths that **do not exist in this repository and never have.** A session
connected only to the repo has `CLAUDE.md` and nothing else of his.

✅ **That is not a bug to route around. Say so and ask**, exactly as the
bottom of this file already instructs. ⛔ **Do not infer what a missing
doc said**, and do not treat its absence as permission.

### ✅ 3. "PUSHED" IS NOT "LANDED", AND LOCAL IS NOT REMOTE

Verify against the remote after every push — `git show origin/main:<file>`
— not against your working tree. **This project has been burned by
treating "I wrote it" as "it is there"** more than once.

---

## ✅ HOW A CLAUDE CODE SESSION SHIPS HERE — `[Sam, 2026-09-22]`

Sam: *"when we used claude code for this it did end up causing alot of
failed recurring runs, i would like to avoid that"*. So:

1. **Branch → pull request → `pr-tests` green → Sam merges.** ⛔ Never push
   to `main`. `pr-tests.yml` runs the collector's own test loop on every PR
   (`test_pr_tests.py` fails if the two loops ever differ).
   `[2026-09-25]` It runs it as five parallel jobs per image: `rest`, and
   the vacuity sweep in four parts (`SUITE_SHARD`, `VACUITY_PART`).
   `test_pr_shards.py` fails if a file or a declared mutation falls
   between them. `collect.yml` leaves both unset and runs everything.
2. ⛔ **A workflow file with a `cron:` block is never changed in a PR.**
   Hand Sam the file; he uploads it with GitHub's "choose your files"
   button. (Dragging a folder put 37 files one level too deep, twice, on
   2026-09-22.)
3. ⛔ **One agent at a time**, and never during a `vacuity.py` sweep.
4. The current open work is in `docs/HANDOFF-2026-09-22.md`, and dated
   snapshots of Sam's project docs (rules, ledger, owed tests, model) are
   `docs/snapshot-*.md`. Read the handoff first; it says which to read.

---

## THE ONE RULE THAT MATTERS MOST

🔴 **NEVER WEAKEN A CHECK TO MAKE IT PASS.**

`verify_card.py` runs before the card is committed and fails the build on
any error. It exists to stop a wrong card reaching a page Sam bets from.
**If a check fails, the card is wrong — not the check.**

⛔ Do not loosen a tolerance, delete an assertion, or add an early return
so a run goes green. **A green tick that proves nothing is worse than a red
one, because it gets trusted.**

✅ The one legitimate reason to change a check is that it asks the WRONG
QUESTION. That happened once: a check asserted "at least one alt rung is
below −700", which tests that data EXISTS rather than that data is CORRECT,
and it failed a perfectly good card on a board that had no ladder stored
yet. It was replaced with "no rung the board holds is missing from the
card" — a strictly stronger question. **If you make that argument, make it
explicitly in the PR body, and make the new check harder to pass than the
old one, not easier.**

---

## What must never change without Sam saying so

| | |
|---|---|
| **Model coefficients in `card.py`** | Fitted, re-fit monthly. ⛔ Do not "tune" one, round one, or tier a term that ships pooled. |
| **`blend` = plain 50/50 of model and raw** | This is the number that enters the permanent calibration record. Changing how it is computed silently invalidates every historical row. `[2026-09-25]` ~~A pitcher row prints its blend~~ — it now PRINTS `confidence` = the blend corrected against the price (C2, `mlb_pitcher_cal.py`, pre-registered and passed). `blend` itself is unchanged and still stored. |
| **`carried`** | A shadow column for two PRE-REGISTERED, NOT ADOPTED tests. ⛔ It must never feed `blend`, a probability, or a pair. |
| **The 1.8x pair floor** | Sam's own instruction. A pair below it is never shown — not printed, not labelled, not listed as declined. |
| **The payout bands have FLOORS ONLY** | `[Sam, 2026-09-22]` Two-leg 1.8x and up; three- and four-leg 3x and up; **no ceiling** (~~1.8–2.2x / 3–6x~~). Every list is ranked by its chance to land, highest first — Sam: "we still have to make sure the bets we provide have a high % to hit". `PARLAY_BANDS` in `card.py` and `card_fb.py` hold `(floor, None)`; read them through `band_ok()`. |
| **The −700 price floor** | Sam's own instruction. Rungs below it are shown but never starred and never paired. |
| **The parlay candidate pool is STRATIFIED BY PRICE** | ⛔ Do not "simplify" it to the N highest-confidence legs. Confidence and price move together, so a confidence-ranked pool of 100 legs had decimal odds of 1.154–1.571 — all short favourites — and the three-leg search returned **zero** parlays on a slate with 2,396 priced legs. Measured 2026-08-26. The pool takes the best legs from each price band for exactly this reason. |
| **The top-10 price gate (−400)** | Sam's own instruction, 2026-08-26: "likely AND payable". Without it the list fills with −2000 alt rungs that always win and pay nothing. It is a floor like the other two, not a judgment call per slate. |
| **ONE projection per player per stat, the same everywhere** | ~~A projection is an INVERSION of the displayed confidence... do not print `central`~~ — **BOTH RETIRED 2026-08-27, ledger rule 66.** Inversion made the projection a property of the ROW, so every rung of one ladder implied a different number: 51 of 608 player-market combos disagreed with themselves, worst 2.1 K. Sam: *"you should have the same numbers across the entire website."* ✅ Pitchers now show the model's own `central` (E[K] / mu), hitters their own per-game mean — both line-independent by construction. `apply_projections()` is the ONLY writer of the field. ⛔ Still do not compute one in JavaScript; that is a second copy of the model. |
| **THE REGION IS THE PRICE, NOT THE BOOK LIST** | Cost is `markets × REGIONS × games` and **books are FREE inside a region** — one `us,us2` pull returned **18 books for 6 credits** (measured 2026-08-26). `BOOKS` is applied AFTER the response arrives; it is a display filter and saves nothing. ⛔ Do not try to cut credits by dropping books. Only dropping a REGION halves a pull, and `us2` is the region Hard Rock lives in. |
| **The budget is DERIVED, not written down** | `python budget.py` reads the cron schedule out of the workflow and the market lists out of `collect.py` and computes the spend. ⛔ Do not put a credit total in a comment — this project has done it three times and been wrong twice. Run the script. |
| **Every props pull is scheduled TWICE, 15 minutes apart** | The backup costs **nothing** when the first one landed: `props_is_fresh()` stands it down inside a 45-minute window. GitHub drops scheduled runs — only 29 of 70 gamelines hour-slots produced a file, measured 2026-08-26 — and with three props pulls a day one drop is a third of the board's freshness. ⛔ The guard keys on the STORAGE DIRECTORY, not the region, so a cheap `us2` backup stands down behind a full `us,us2` primary. |
| **Paid pulls are anchored to the CARDS** | The full two-region pull runs at 14:08–14:28Z, immediately before the 14:46Z card. ⛔ Do not move it later "to be fresher" — a noon pull lands AFTER the morning card, which then falls back to the 4am prices, 6¾ hours stale. |
| **Five books for MLB, THREE for football** (`BOOKS`, `FB_BOOK_KEYS` in collect.py) | MLB: Hard Rock, DraftKings, FanDuel, Caesars (`williamhill_us`), BetMGM — Sam, 2026-08-23. **Football: Hard Rock, FanDuel, DraftKings only — Sam, 2026-09-22 ("just use those three").** `league_books()` is the one filter. Hard Rock's Ohio skin is the same book and is never counted twice. ⚠️ Props still pull `us,us2`; books are free inside a region, so this changes what is shown, not what is spent. A price from a book he cannot bet is not a better price. |
| **`picks/<date>.json` already written** | Published estimates are a permanent record. ⛔ Never edit or delete one after its games have started. |

## Things that are true and easy to get wrong

- 🔴 **THE PAGE RENDERS ONLY FLAGS MARKED `actionable`.** Sam,
  2026-08-26: *"we have to advertise a clean look to the website that
  doesnt include nonsense users dont need to read and cant understand."*
  T21, T22, rule 15 and STEP 4B are notes the model writes to ITSELF.
  ⛔ **They are still computed and still stored in `picks/<date>.json`** —
  the calibration record depends on every one of them, and a clean page
  must never become a card that stopped writing its diagnostics.
  `verify_card.py` checks both halves: nothing internal is marked for
  display, and the diagnostics are still being written. A flag only earns
  `actionable` if it changes what the reader can DO — today the only one
  is "Hard Rock didn't post this", because the price on screen is then
  one they cannot bet.
- 🔴 **THE "WHY" IS WRITTEN FOR A READER, NOT FOR THE LEDGER.** Sam,
  2026-08-26: *"lose the technical wording ... all of these things that a
  casual fine wont know about has to go."* ⛔ No test IDs (T23, T24, STEP
  4B), no "measured null", no t-statistics, no "edge of N points", no
  coefficients, no "DESCRIPTIVE". The honesty those phrases carried is
  KEPT — said in English: a thin sample is "too small to read much into",
  and a number outside the model says "that isn't part of the model's
  math". ✅ **Every sentence should carry a number** — the stats are the
  argument. `verify_card.py` fails the build on a jargon list.
- 🔴 **`inningsPitched` fractions are THIRDS.** Only `.0`, `.1`, `.2` exist.
  There is no `.3`. A value outside that domain is fabricated data —
  `outs_of()` raises on it deliberately. Do not "fix" it by rounding.
- 🔴 **Two legs are in different games only if the GAME ID differs.**
  ⛔ Never compare opponent names. In every game both starters have
  different opponents and the same game, so a name check passes on exactly
  the pairs it exists to catch. A live card shipped four impossible parlays
  that way, including its top recommendation.
- 🔴 **Pitcher rates are computed over STARTS ONLY.** A reliever's two-out
  appearance is not evidence about a starter's line. Mixing them in once
  turned a true 2/3 into a false 48/49.
- 🔴 **A hitter is rated only over games he STARTED.** ~~`pa > 0`~~ —
  **tightened 2026-08-24.** Excluding zero-PA games was right but did not
  go far enough: a **1–2 plate-appearance cameo is not a start**, and
  counting it as one inflates every hitter UNDER. Measured across 37,829
  played games — under 0.5 hits: cameo **74.8%** vs start **37.4%**
  (+37.4 points); under 1.5 TB: 90.4% vs 63.5%; under 0.5 RBI: 87.8% vs
  69.4%. Cameos are 13.7% of played games and hit bench bats hardest —
  which is exactly who was topping the picks board. **Use real batting
  order from `data/latest/lineups.json.gz` where it exists; `pa >= 3` is
  the documented fallback and nothing else.**
- 🔴 **A hitter was previously rated over games he BATTED (`pa > 0`).** The hitter
  analogue of starts-only, and the same bug. A defensive sub or a pinch-run
  is not an under that won -- at the book it is usually a VOID. Measured
  2026-08-23: Tyler Tolbert's "under 0.5 total bases" read 41/58 (71%) over
  every logged game and 24/41 (59%) over games he actually batted in.
- 🔴 **Shop a price only at the EXACT SIGNED number.** Measured 2026-08-23
  on ATL@MIL: eleven books posted ATL -1.5 / MIL +1.5 while two posted the
  same game inverted. Matching on |point| paired "Milwaukee -1.5 at +130"
  against a market whose real price is "+1.5 at -182" -- opposite bets, and
  the page would have advertised a bargain that does not exist. ⛔ Never
  compare two prices without first confirming they are the same wager.
- 🔴 **A RATE BAR NEEDS A SAMPLE, AND T37's IS POOLED ACROSS CARDS.**
  Build #183 failed on **1 contradiction out of 4 priced hitter rows** — a
  2:22am board where one row is 25%. T37's bar was pre-registered on n=80
  and n=116; a percentage on n=4 is not a rate. ✅ The bar now pools every
  published card that carries the confidence field, so the denominator only
  grows and **a persistent 6% fails even when no single slate exceeds it** —
  strictly harder than the per-card form. ⚠️ Under 100 pooled rows it reports
  **NOT YET MEASURABLE**: not a pass, not a fail. ⛔ A **CANARY** still fails
  instantly with no pooling on a gross break (>25% on ≥20 rows), so a
  catastrophic regression cannot hide behind a big historical denominator.
- ⚠️ **THE MEAN IS A POOR CENTRAL ESTIMATE FOR A RIGHT-SKEWED MARKET, AND
  THAT IS NOW A PRE-REGISTERED TEST, NOT A FIX.** Amed Rosario's total bases:
  41 games, **mean 1.585 but MEDIAN 1**, under 1.5 in 30 of 41 — four games
  of 4/5/8/10 TB drag the average over the line. So "PROJ 1.6" sat beside
  "UNDER 1.5 · 75%" and both were right. ⛔ **DO NOT swap the estimator to a
  median on the strength of one row.** `research/t38_spec.md` has the bar and
  the prediction, fixed before any fit.
- 🔴 **TOTAL BASES and H+R+RBI project the player's OWN PER-GAME MEAN,
  not an inversion.** ~~"carry NO PROJECTION, deliberately"~~ — **changed
  2026-08-26** on Sam's instruction that every player have one. The bar was
  not lowered: T34/T35 asked whether an INVERTED projection could reproduce
  a player's own per-game mean to 0.25, and nothing could. Using the mean
  itself makes that question moot — it reproduces the mean exactly. What
  inversion bought was agreement with the confidence beside it, and that
  was **measured, not assumed**: across 948 real props the mean sits on the
  losing side of the line in **0.0%** of rows at 80%+ confidence and 1.9%
  at 70%+, and the board's lowest hitter is 78%. ⚠️ Below ~60% it disagrees
  often, and that is CORRECT — it is what a bad number looks like.
  `verify_card.py` RECOMPUTES the mean from the log rather than checking
  the field exists.
- ~~🔴 **Total bases and Hits+Runs+RBIs carry NO PROJECTION, deliberately.**~~
  Not an oversight and not a missing feature. T34/T34b/T35, 2026-08-26, bar
  fixed at |mean| < 0.10 and p90 < 0.25 units BEFORE any fit: plain Poisson
  missed by **0.673** at the tail on total bases, a negative binomial by
  **0.350**, a compound Poisson (hits × the player's own extra-base mix) by
  **0.287**. Projecting the observed mean directly put it on the losing side
  of the line in 5% of rows, all unders. Hits (Poisson, 0.202), home runs
  (Poisson, 0.022) and RBIs (**negative binomial**, 0.117 — Poisson failed
  at 0.299) passed and ship. ⛔ Three attempts have failed. A fourth does
  not get an easier bar; it gets a new pre-registered test at 0.25.
- 🔴 **A hitter row shows a confidence NUMBER but must never claim MODEL
  provenance.** ~~"carries NO confidence rating"~~ — **changed 2026-08-24**:
  a board with two different headline numbers is unreadable, so both kinds
  of row show one CONF number and the board sorts strictly by it. What
  rule 55 requires is that the number be **labelled**, not hidden. So:
  every row carries `confidence_basis`, which is `MODEL` for pitchers and
  **`RECORD`** for hitters, and a hitter row must never carry a `blend` or
  a calibration `band`. ⛔ Do not relabel a hitter row `MODEL` until a
  hitter model exists and has passed a pre-registered test. **T27, T28 and
  T29 all FAILED — hitter modelling is CLOSED pending lineup slot, which
  the `lineups` collector mode now gathers.**
- 🔴 **The board sorts strictly by confidence, descending.** Sam's
  instruction. ⚠️ Edge still decides which plays make the board at all; it
  just no longer decides the order. ⛔ Do not reintroduce band-first or
  edge-first ordering — it made the page look broken to anyone reading
  down the numbers.
- 🔴 **A CARD IS MATCHED TO A BOARD RECORD ON NEAREST FIRST PITCH, NEVER
  ON A DATE.** ⛔ Do not "simplify" `boardFor()` back to a date comparison.
  **A UTC date is not a game's date**: a 9:40pm ET first pitch is `01:40Z
  THE NEXT DAY`, so every night game files under tomorrow and the next
  afternoon's card inherits it. That shipped on 2026-08-26 and put six
  games' LIVE IN-PROGRESS odds onto the following day's cards — CHC at
  −4000 with a 4.5 total, Pittsburgh implied for 0 runs. ⚠️ **ET dates are
  not sufficient either**: a doubleheader is two games with the same teams
  on the same ET date. Nearest first pitch inside `BOARD_MATCH_WINDOW_MS`
  separates all three cases, and **it fails closed** — no candidate in the
  window returns null and the card renders with no odds. A card missing a
  line is a card missing a line; a card showing another game's line is
  misinformation. `test_board_match.js` is the regression test and runs
  against the real board.
- 🔴 **`run_line` is the HOME team's point, by MAJORITY across books, then
  cross-checked against the MONEYLINE.** ⛔ Never take it from one book.
  Books split on which side they show laying the runs — 11 to 6 on TB@DET,
  2026-08-26 — and `team_total` is derived from it, so one book's label
  shipped the implied runs to the wrong team on 3 of 19 games. The
  moneyline is the authority: it is a single unambiguous market and the
  favourite lays the runs. A row re-oriented against its spread label
  carries `run_line_conflicted_with_moneyline` and says so on the page.
  ⚠️ **`team_total` is owed-test T25's predictor**, so an inverted row is a
  corrupted observation in a test that has not been run yet.
- 🔴 **THE OPPONENT'S RECENT STARTER LOG IS DESCRIPTIVE AND MUST STAY THAT
  WAY UNTIL T36 PASSES.** Sam asked for it to feed the confidence score.
  It cannot yet: the v4.0 K model **already carries an opponent term**
  (`oppK`, the season-long mean), and a ten-start window is a competing
  estimator of that same quantity, not new information. Adopting it is a
  model change and this project does not make those without a
  pre-registered test. ⛔ It must never touch `confidence`, `blend`,
  `carried`, a band or a pair before T36. `verify_card.py` checks it is
  labelled DESCRIPTIVE and says so in words.
- 🔴 **IT DOES NOT NEED STATMUSE, AND MUST NOT USE IT.** Sam asked for this
  from StatMuse. **All 3,852 starts in `pitchers.json.gz` already name their
  opponent** (verified 2026-08-26), so it is a query over data the collector
  already stores: zero credits, no scraping, nothing third-party to break,
  and **point-in-time by construction** — which a scraped "last 20 games"
  table can never be. `claude/mlb-data-stack.md` also forbids letting a
  summarising fetch touch a number the card computes with.
- 🔴 **Players share names.** `resolve()` refuses to guess and returns
  `(None, None)` when a name is ambiguous and the game's own teams do not
  break the tie. ⛔ Do not make it pick the first match.
- 🔴 **The collector must FAIL LOUD.** `sys.exit(1)` on error. It used to
  exit 0, and a green check proved nothing.
- 🔴 **Every workflow runs on a PINNED image (`ubuntu-24.04`), never
  `ubuntu-latest`, with Node 24 actions and its own Python.** `[2026-09-24]`
  GitHub moves `-latest` to Ubuntu 26.04 from 2026-10-19 (image Python
  3.12 → 3.14, Node 20 → 24, apt names change). `test_runner_image.py`
  fails on a floating label, a Node 20 action major, an action not in its
  table, or a job running the image's Python. ➡️ Move a pin only after
  `pr-tests`' `ubuntu-26.04` rows are green — they run on every PR.
  Details: `docs/HANDOFF-2026-09-24-runner-image.md`.
- ⚠️ **Cron minutes are deliberately off :00 and :30.** Those are the most
  congested slots on GitHub's scheduler and runs get dropped. Six were lost
  that way, leaving a three-hour hole in the data.
- ⚠️ **`concurrency` is grouped PER MODE.** A shared group silently cancels
  queued scheduled runs when someone triggers a job by hand.
- ⚠️ **An absence in an API response is evidence about the API, never about
  the sportsbook.** This project has written down "the feed has no X" as
  "the book has no X" five times and been wrong every time.

## Data and money

- ⛔ **Never invent a price.** Every quoted number must be traceable to a
  stored raw pull. `verify_card.py` checks this.
- ⛔ **Never quote a PrizePicks price.** `−137` and `+100` are the feed's
  encodings for "goblin" and "demon" — labels, not quotes. No break-even,
  no edge, no EV may be computed from them.
- ⛔ **Do not commit secrets.** The Odds API key lives only in the
  repository secret `ODDS_API_KEY`.
- 💰 **Credits are metered.** A props pull costs `markets × regions` per
  game. Before adding a market or a region, state the new daily cost.

## How to work here

1. **Run `python verify_card.py` before proposing any change to `card.py`
   or `collect.py`.** If it does not pass locally, do not open the PR.
2. **Prefer a pull request over a push to `main`** for anything touching
   the model, the verifier, or the workflow. Data commits from the
   collector go straight to `main` and that is correct.
3. **Say what you did NOT change.** This project's docs do it, and it is
   how regressions get caught early.
4. **If you are unsure whether something is a rule or an accident, ask in
   the issue thread rather than guessing.** Sam reads them from his phone
   and would rather answer a question than unwind a change.

## What lives where

```
collect.py        the collector. modes: gamelines, schedule, results,
                  hitters, pitchers, news, props-batter, props-pitcher,
                  props-board, card, record, refresh, lineups
card.py           the v4.0 model -> picks/<date>.json. Calls nothing.
budget.py         projected Odds API spend, derived from the deployed
                  cron schedule and market lists. Run it after ANY change
                  to the schedule or the markets.
verify_record.py  re-grades EVERY published pick from the stored box
                  scores a second way and reconciles record.json against
                  it -- totals, per day, per kind, the internal sums, and
                  the drill-down detail. ⛔ Voids stay out of every
                  denominator. Runs on the record and refresh jobs.
verify_board.py   checks data/latest/board.json -- implied runs vs the
                  moneyline, run-line attribution, and whether the PAGE
                  can tell two records for one matchup apart. ⛔ Runs on
                  the GAMELINES job, which is the job that writes the
                  file. verify_card.py only runs on card/refresh, and
                  that gap is how the wrong-game bug shipped.
test_board_match.js  regression test for boardFor(), run with node
                  against the real board.json.
verify_card.py    ~90 checks (COUNT THE SOURCE, do not trust this
                  number), pitcher AND hitter, including the
                  descending-order invariant, the projection
                  round-trip, the top-10 price gate and every
                  parlay recomputed leg by leg. Runs before commit.
index.html        the dashboard, single file, no build step
.github/workflows/collect.yml   every schedule
data/             timestamped snapshots. append-only.
picks/            published cards. append-only once a slate starts.

FOOTBALL (not frozen)
card_fb.py        the football picks board -> picks/fb-<lg>-<date>.json
cfb.py            college: probe, back-fill and verify, one dispatch
nfl.py            NFL ingestion from nflverse. STDLIB ONLY.
record_fb.py      the football grader -> data/<lg>/latest/record.json
dossier_fb.py     Sam's eight per-game checks, every board game.
                  ⛔ Combines nothing, ranks nothing, scores nothing.
fb_model.py       THE FOOTBALL PICK MODEL (Sam, 2026-09-23): ridge
                  logistic per league x market on signals 1-8, walk-
                  forward weekly, graded ONLY at Hard Rock / FanDuel /
                  DraftKings prices archived before kickoff. Rides
                  `card-fb`; its own MODEL section on the page. ⛔ Never
                  touches the card. Design: research/fb_model_design.md.
                  ⛔ Its SECOND record (closing lines, college at an
                  assumed -110, labelled) is kept apart from the headline
                  and shown under it, never mixed in [Sam, 2026-09-23].
fb_props_model.py THE FOOTBALL PROPS MODEL (Sam, 2026-09-24): each player's
                  stat distribution from the stored logs 2021-26, the
                  market line folded in from EARLIER priced weeks only,
                  walk-forward at the three books' prices, and scored
                  against the props card's OWN recomputed probabilities.
                  Rides `card-fb`. ⛔ Never touches the card; the switch
                  is Sam's. Design: research/fb_props_design.md.
fb_card_calibration.py  the football props card's stated-vs-actual bands
                  and Sam's pre-registered calibration test
                  (`research/fb_card_calibration_spec.md`, frozen).
                  ⛔ Never changes what the card prints; a QUALIFIES
                  waits for Sam. Rides `card-fb`.
fb_card_fix.py    scores the football props card's season fix (reads 2026
                  first, 2025 as the start, shrunk toward the position
                  average) against the card as it was, by Sam's ship rule
                  in `research/fb_card_fix_spec.md` (frozen). The live
                  switch is `card_fb.CARD_METHOD`.
fb_ledger.py      "What the model showed, graded": both football models'
                  picks saved before kickoff via daystore, graded ONCE
                  and frozen, listed pick by pick; the verdict label per
                  market (fb_model.verdict) beside every record
                  (`research/fb_model_live_spec.md`, frozen). Rides
                  `card-fb`. ⛔ Never recalculates a graded pick.
shadow_fb.py      THE SHADOW RECORD. Grades every wager the board
                  priced -- measured 2,923 graded rows in one run
                  against the card's 222 in total -- so a selection rule
                  can be evaluated in weeks instead of seasons. ⛔ NOT
                  PUBLISHED: the page shows the card, the same way
                  `carried` is a shadow column. ⛔ Every rate carries an
                  effective n clustered by GAME and capped by the
                  complementary-pair bound, and NO p-value is ever
                  computed on the raw row count.
possession.py     ONE implementation of the possession coverage/share
                  maths, read by BOTH leagues. ⛔ Never copy it into
                  nfl.py or cfb.py (rule 117).
signal9.py        SIGNAL 9, "Opportunity change" (Sam, 2026-09-24): the
                  ONE copy of the vacated-share maths (s_adj, E_share,
                  the card scale), read by the props model, the card,
                  the game model and the dossier. Formulas frozen in
                  research/fb_signal9_spec.md. ⛔ Injured reserve counts
                  as vacated while out (Sam's rule).
fb_signal9.py     scores signal 9's three uses by Sam's keep rule (mean
                  log-loss difference >= 0, clustered by game). ⛔ The
                  per-league switches are constants set from the recorded
                  run; test_signal9.py fails if they disagree.
game_lines_fb.py  THE GAME LINES TAB (Sam, 2026-09-24): every alt spread
                  and total Hard Rock / FanDuel / DraftKings post for the
                  slate, each rung's price per book, best, break-even,
                  the game model's % and edge; frozen before kickoff
                  (daystore), graded once, its own record; alt-only
                  parlays through card_fb.build_parlays_fb's rules.
                  ⛔ Never touches the card. Data: the paid `alt-lines`
                  pull in collect.py (one pull per game, capped at
                  1,500 credits a month, bill measured per call).
fb_alt_lines.py   the pre-registered check (research/fb_alt_lines_spec.md,
                  frozen): is the game model calibrated 3/7/10 points off
                  the main line? ⛔ Decides the tab's LABEL, never whether
                  a number shows. Called by fb_model.build on its rows.
liveprobe.py      can the football scores tab ever be live?
verify_nfl.py     the football data-layer verifier

CONTRACT AND SPEND
freshness.py      THE FRESHNESS CONTRACT — what must be how current.
                  `converge` plans its work from this, not from crons.
verify_freshness.py  fails the run when the site is not current
cfbd_budget.py    projected CFBD call volume, derived from the workflow
cfbd_watch.py     ...and the watcher that asks whether it will run out
budget_watch.py   the same question for the Odds API spend
repo_watch.py     is the REPOSITORY growing in a way that will become
                  a problem, and WHAT is doing it? ⛔ Reads
                  `objectsize:disk`, never the working tree and never
                  a raw blob sum — measured 2026-09-19 they differ by
                  2.84x, because git deltas text and CANNOT delta a
                  gzip. ⚠️ Flags gzips REWRITTEN IN PLACE, measured
                  from the version count rather than guessed from the
                  path — a dated archive is written once and is the
                  correct design (rule 285). ⛔ Refuses a shallow
                  clone rather than reporting its size. Rides
                  budget.yml as a second JOB; no new cron.
calibration.py    is the product still winning? the automatic answer.
card_gate.py      did the card fail for a reason Sam already accepted?

OWED TESTS (pre-registered, not adopted)
t54.py            should a record against a line never faced be RANKED?
t58_t59.py        the two owed tests, accumulating themselves
fb_model_lambda.py  the football model with a SELF-CHOSEN ridge λ, scored
                  against today's fixed 1.0 by the rule Sam pre-registered
                  on 2026-09-24 in `research/fb_model_lambda_spec.md`
                  (frozen by `test_prereg_gate.py`). ⛔ Never switches the
                  live model and never edits `fb_model.RIDGE`; Sam decides.
t60r.py           the played-games backtest of signals 1-8, run to the
                  rule Sam APPROVED on 2026-09-22 in
                  `research/t60r_spec.md`. ⛔ That rule and its bar are
                  FROZEN and hashed by `test_prereg_gate.py` — weekly
                  grading adds games, never a new threshold. Modes:
                  `lines` (CFBD closing lines, needs the repo secret)
                  and `grade`. ⛔ The verdict is the COMBINED number;
                  2025 and 2026 are reported beside it, never as it.

SHARED HELPERS — ⛔ ONE COPY EACH. Rule 117: a helper duplicated breaks
in the file you did not edit.
tcheck.py         the one check harness every test file uses
ranking.py        the one tie-aware ranker, both leagues
wfparse.py        the one HAND parser for a workflow file -- jobs,
                  steps, `run:` bodies and `permissions:` blocks.
                  ⛔ Never `import yaml`: PyYAML is NOT on the CI
                  runner (measured 2026-09-19) and a test that cannot
                  import blocks a push. Cross-checked against PyYAML
                  in test_wfparse.py wherever PyYAML happens to exist.
wfroutes.py       the one parser for the workflow's routing table
jsblock.py        the one reader for a function's body in index.html
runs_report.py    did any workflow run fail?
daystore.py       the one dated, write-once archive writer. ⛔ Never
                  cumulative (rule 285: git cannot delta-compress a
                  gzip, 560x) and never into `picks/`.
push_retry.sh     the ONE way a workflow lands its commits: rebase
                  favouring this run's files, abort + replay on a
                  conflict, exit 1 after 5 tries. ⛔ Never hand-roll a
                  pull/push loop again — a half-done rebase lost whole
                  converge passes (and paid pulls) 09-15 → 09-21.
mlb_refit.py      MLB champion vs challenger, as Sam approved it on
                  2026-09-23 in `research/mlb_refit_spec.md`: v5.0
                  (READ from card.py) against the same model re-fitted
                  each week on earlier games only, scored by log loss.
                  ⛔ Changes no coefficient; when the challenger
                  qualifies it opens ONE "[ASK SAM]" PR. Stdlib only.
mlb_tables.py     the MLB pitcher + opponent tables, rebuilt after every
                  `pitchers` pull from the FULL starter population.
                  ⛔ card.py reads `model_pitchers()`, never the widened
                  pool, so the card's numbers do not move.
mlb_pitcher_cal.py  audit C/D, scored to `research/mlb_pitcher_cal_spec.md`
                  (frozen). C2 shipped `[2026-09-25]`: a pitcher row
                  PRINTS its blend mixed with its price, refitted each
                  card on earlier graded rows. ⛔ `blend` is unchanged;
                  card.py reads `mappings()`/`corrected()` from here and
                  never imports `fb_model` (it drags in card_fb, which
                  exits under LEAGUE=mlb). Off switch: `SHIPPED = None`.
vacuity.py        does each guard actually bite? `VACUITY_PART=k/n`
                  sweeps one share (pr-tests' parallel parts, never a
                  sample: test_pr_shards.py). ⛔ It MUTATES SOURCE
                  FILES while it runs — never edit the repo during a
                  sweep, and never run two at once.
```

⚠️ **THAT LIST IS CHECKED, NOT MAINTAINED BY HOPE.** `test_claude_md_map.py`
fails if a top-level module exists and is not named here. ⛔ If it fails
because you added a module, add the line — the list going stale is how a
fresh session ends up writing a second copy of something.

The reasoning behind all of it — the model, the ledger, the pre-registered
tests — lives in Sam's Claude project docs, not in this repo. **If a change
needs that context and you do not have it, say so instead of inferring.**
