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
   parlays below their payout floor are never shown.) `[Sam, 2026-10-01]`
   On the page a play's label is its own numbers (%, price, book,
   break-even, edge), never a chip, flag or note box; the labels stay in
   the data files.
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

⛔ **A TEST ASKS THE CODE, NEVER PRODUCTION.** `[Sam, 2026-09-28]` Collect
was red 09-26 → 09-28 on tests whose verdict was a fact about that day's
data. No frozen clock against the live tree (the real clock, or a tree
pinned to NOW — never one of each). No assertion that another guard is
silent on production data (build the case; the live line is a `note()`).
No rule-67 case waited for from the live board (plant it, as #156 did; the
live check is an extra). A `collect.py` run from a test passes
`converge-off` with the keys blank (`test_collect_subprocess.py`). Every
instance found: `docs/HANDOFF-2026-09-29-live-tree-tests.md`.

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

<!-- CRON TOTAL: 59 -->
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
   between them. ~~`collect.yml` leaves both unset and runs everything.~~
   `[Sam, 2026-10-02]` `collect.yml` runs the `rest` share
   (`SUITE_SHARD: rest` on its Tests step): the sweep checks the TESTS, not
   the data, and took 33 minutes before every pull. It still runs in full
   on every PR (four parts) and every night (`vacuity.yml`).
   `test_pr_shards.py` fails if collect runs it again or the nightly stops
   sweeping everything (the nightly step itself: `test_vacuity_pool.py`).
   `[2026-09-25]` One more job, `staged`, applies every workflow staged in
   `docs/upload/` to its own checkout and runs the `rest` shard again:
   the suite as it will be AFTER Sam's upload. Sam's upload of PR #174's
   runs.yml turned collect #1839 red on a row-count pin that every
   pr-tests job had passed (`test_pr_staged.py`).
2. ⛔ **A workflow file with a `cron:` block is never changed in a PR.**
   Hand Sam the file; he uploads it with GitHub's "choose your files"
   button. (Dragging a folder put 37 files one level too deep, twice, on
   2026-09-22.) `[2026-09-25]` Uploading from the repo's front page put 11
   workflow copies in the TOP LEVEL (103c7ac), where they never run;
   `test_top_level_yaml.py` now fails on any top-level `.yml`/`.yaml`.
3. ⛔ **One agent at a time**, and never during a `vacuity.py` sweep.
4. The current open work is in ~~`docs/HANDOFF-2026-09-22.md`~~
   `docs/HANDOFF-2026-10-18.md` `[2026-10-18]`, and dated
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

✅ `[Sam, 2026-10-01]` The other legitimate reason: **Sam changes the
requirement itself.** The check is rewritten to the NEW requirement in the
same PR, never deleted; the PR body quotes him; the new form still goes red
under its own `@vacuity` mutation. First use: the page tests that required
note boxes, tags and the stale bar now require their absence.

---

## What must never change without Sam saying so

| | |
|---|---|
| **Model coefficients in `card.py`** | Fitted, re-fit monthly. ⛔ Do not "tune" one, round one, or tier a term that ships pooled. |
| **`blend` = plain 50/50 of model and raw** | This is the number that enters the permanent calibration record. Changing how it is computed silently invalidates every historical row. `[2026-09-25]` ~~A pitcher row prints its blend~~ — it now PRINTS `confidence` = the blend corrected ~~against the price (C2, `mlb_pitcher_cal.py`, pre-registered and passed)~~ `[Sam, 2026-10-11]` by its own past misses, no price (C1, the same pre-registered run, also passed). `blend` itself is unchanged and still stored. |
| **`carried`** | A shadow column for two PRE-REGISTERED, NOT ADOPTED tests. ⛔ It must never feed `blend`, a probability, or a pair. |
| **The 1.8x pair floor** | Sam's own instruction. A pair below it is never shown — not printed, not labelled, not listed as declined. |
| **The payout bands have FLOORS ONLY** | `[Sam, 2026-09-22]` Two-leg 1.8x and up; three- and four-leg 3x and up; **no ceiling** (~~1.8–2.2x / 3–6x~~). Every list is ranked by its chance to land, highest first — Sam: "we still have to make sure the bets we provide have a high % to hit". `PARLAY_BANDS` in `card.py` and `card_fb.py` hold `(floor, None)`; read them through `band_ok()`. |
| **The −400 price floor** ~~(−700)~~ | `[Sam, 2026-10-01]` "ideally props/game lines at -400 is the lowest we should go": the floor for EVERY Gizmo's Picks row in all three leagues — board picks, top plays, game-line rows, parlay and same-game legs; −400 itself clears. ~~Rungs below −700 are shown but never starred and never paired~~; a ladder rung below −400 is still drawn, dimmed, never starred. One constant per league file (`card.PRICE_FLOOR`, `card_fb.PRICE_FLOOR`), read by `verify_card.py`; `test_price_floor.py`. Published cards and graded records are not rebuilt. |
| **The parlay candidate pool is STRATIFIED BY PRICE** | ⛔ Do not "simplify" it to the N highest-confidence legs. Confidence and price move together, so a confidence-ranked pool of 100 legs had decimal odds of 1.154–1.571 — all short favourites — and the three-leg search returned **zero** parlays on a slate with 2,396 priced legs. Measured 2026-08-26. The pool takes the best legs from each price band for exactly this reason. |
| **The top-10 price gate (−400)** | Sam's own instruction, 2026-08-26: "likely AND payable". Without it the list fills with −2000 alt rungs that always win and pay nothing. It is a floor like the other two, not a judgment call per slate. `[2026-10-01]` It IS `PRICE_FLOOR` now, the one constant, and −400 itself clears (~~`TOP10_PRICE_FLOOR`, `<= −400` dropped~~). |
| **ONE projection per player per stat, the same everywhere** | ~~A projection is an INVERSION of the displayed confidence... do not print `central`~~ — **BOTH RETIRED 2026-08-27, ledger rule 66.** Inversion made the projection a property of the ROW, so every rung of one ladder implied a different number: 51 of 608 player-market combos disagreed with themselves, worst 2.1 K. Sam: *"you should have the same numbers across the entire website."* ✅ Pitchers now show the model's own `central` (E[K] / mu), hitters their own per-game mean — both line-independent by construction. `apply_projections()` is the ONLY writer of the field. ⛔ Still do not compute one in JavaScript; that is a second copy of the model. |
| **THE REGION IS THE PRICE, NOT THE BOOK LIST** | Cost is `markets × REGIONS × games` and **books are FREE inside a region** — one `us,us2` pull returned **18 books for 6 credits** (measured 2026-08-26). `BOOKS` is applied AFTER the response arrives; it is a display filter and saves nothing. ⛔ Do not try to cut credits by dropping books. Only dropping a REGION halves a pull, and `us2` is the region Hard Rock lives in. |
| **The budget is DERIVED, not written down** | `python budget.py` reads the cron schedule out of the workflow and the market lists out of `collect.py` and computes the spend. ⛔ Do not put a credit total in a comment — this project has done it three times and been wrong twice. Run the script. |
| **Every props pull is scheduled TWICE, 15 minutes apart** | The backup costs **nothing** when the first one landed: `props_is_fresh()` stands it down ~~inside a 45-minute window~~ `[2026-10-24]` once a pull has landed for the deadline in force, which is the contract's own answer (`freshness.pull_owed`). A pull the contract owes is never stood down: the 45-minute window refused the owed pull because one had landed 23 minutes before the deadline, and turned collect red (10-18, 10-24). GitHub drops scheduled runs — only 29 of 70 gamelines hour-slots produced a file, measured 2026-08-26 — and with three props pulls a day one drop is a third of the board's freshness. ⛔ The guard keys on the STORAGE DIRECTORY, not the region, so a cheap `us2` backup stands down behind a full `us,us2` primary. |
| **Paid pulls are anchored to the CARDS** | The full two-region pull runs at 14:08–14:28Z, immediately before the 14:46Z card. ⛔ Do not move it later "to be fresher" — a noon pull lands AFTER the morning card, which then falls back to the 4am prices, 6¾ hours stale. |
| **Five books for MLB, THREE for football** (`BOOKS`, `FB_BOOK_KEYS` in collect.py) | MLB: Hard Rock, DraftKings, FanDuel, Caesars (`williamhill_us`), BetMGM — Sam, 2026-08-23. **Football: Hard Rock, FanDuel, DraftKings only — Sam, 2026-09-22 ("just use those three").** `league_books()` is the one filter. Hard Rock's Ohio skin is the same book and is never counted twice. ⚠️ Props still pull `us,us2`; books are free inside a region, so this changes what is shown, not what is spent. A price from a book he cannot bet is not a better price. |
| **`picks/<date>.json` already written** | Published estimates are a permanent record. ⛔ Never edit or delete one after its games have started. |

## Things that are true and easy to get wrong

- 🔴🔴 **NOTHING RECURRING RUNS IN CLAUDE.** `[Sam, 2026-10-12]` *"we can't have
  any recurring tasks or weekly checks or anything in Claude ... What we can do is
  set something up in GitHub ... we can't have anything running in Claude
  anymore."* ⛔ Every recurring job is a GitHub Actions workflow that reads only the
  repo's own files and never calls Claude.
- 🔴 **THE FOOTBALL GAME MODEL LEARNS EVERY WEEK, BY A FROZEN CONTEST.** `[Sam,
  2026-10-12]` *"how do we make sure the model knows these teams better than they
  do or in the least is learning how to do so"*; he chose all three: a weekly
  scoreboard against the books, better data, and a weekly champion-vs-challenger
  contest. T65 (`research/fb_refit_spec.md`, frozen by `test_prereg_gate.py`):
  `fb_model.CHAMPION` names each league's champion in ONE place (None = today's
  model); challengers E (NFL EPA), P (college PPA) and T (college talent) live in
  `fb_challengers.py` (⛔ R, returning production, was withdrawn: never build
  it). `[Sam, 2026-10-14]` T66 (§3a, Cowork's pre-registration) adds S (NFL: the
  champion without head-to-head and signal 9) and TS (college: T's talent margin,
  the line, neutral and dome only), all three markets, registered 2026-10-19, no
  withdrawal; only games after registration count (`[Sam, 2026-10-26]` still true for these
  two: see T73 below). `[Sam, 2026-10-15]` T68 (§3b) adds AV/AVC
  (Sam's averages) and WX/WXC (wind); T69 (§3c, "do all changes") adds IN (NFL injuries on BOTH
  sides of the ball: Out/Doubtful weighted by offensive or DEFENSIVE snap share, starting QB
  out), AT/ATC (Sam's averages blended into totals) and RS/RSC (rest); T70 (§3d) adds H/HC
  (own ratings, neutral, dome, trained on NFL 2018-2024 / college 2023-2024 too, stored in
  `data/<lg>/history/` by `fb_history.py`, never in `latest/`): ~~8 challengers a league, so
  p < 0.01/8~~. `[Sam, 2026-10-16]` T71 (§3e) adds SM/SMC, the score-first model
  (`fb_score_model.py`'s predicted margin and total, the only input; registered from the
  first Monday ~~on or after~~ AFTER its merge day (a Monday merge counts from the next
  Monday), no earlier than 2026-10-19, read from git): ~~9 challengers a league, so
  p < 0.01/9~~. `[Sam, 2026-10-26]` T72 (§3f, the matchup grade) adds CL/CLC (class: how a
  team does against above-average opponents beyond its rating), WL/WLC (a win-loss resume),
  MC/MCC (the margin with blowouts capped at 21 / 28) and AJ/AJC (form and the defence rank,
  opponent-adjusted; head-to-head is not retested), registered from the first Monday AFTER
  its merge day, no earlier than 2026-11-02: 13 challengers a league, so p < 0.01/13
  (`test_fb_matchup_grade.py`). ~~College has no injury data stored.~~ (`[Sam, 2026-10-17]` it is now: see COLLEGE
  INJURIES.) `fb_refit.py weekly` (staged `fb-refit.yml`, Mondays 09:47Z) writes
  `data/<lg>/latest/fb-refit.json`; a WINS pushes ONE branch
  `fb/champion-<lg>-<name>-<date>` (only the CHAMPION line), never a PR, never
  main; the Monday email's "Is the football model learning?" section and "Needs
  you" tell Sam. ⛔ Merging is Sam's; a champion adds "+game-<name>" to the card's
  method. A report over 8 days old is DEGRADED. `[R1, 2026-10-18]` A report that never lands
  is DEGRADED too (`watchdog.check_learner_landing`). While the league already names a
  CHAMPION, a WINS pushes nothing and its report carries NEEDS SAM; a second switch (an
  ordered CHAMPION list) is Sam's, §3 unchanged. `test_fb_refit.py`. `[Sam, 2026-10-26]` T73
  (§3g): *"instead of having it need 300 scored prediction can we just use games from last
  season and the ones played this season for both cfb and nfl"*. The verdict reads each
  challenger's `counted` predictions: ~~only games after registration count~~ EVERY 2025-2026
  walk-forward prediction for the eighteen defined before any of their results existed, and
  only games after registration for the eight shaped on those games (`fb_refit.SCORED_ONLY`:
  S, TS, AV, AVC, AT, ATC, SM, SMC). The 300 floor counts only predictions that differ from
  the champion's (WX before stored weather equals it); p < 0.01/k, k and registration are
  unchanged, and nothing is counted before a challenger's registration Monday. P and T's
  withdrawal window stays the weeks before 2026-10-19; `[Sam, 2026-10-27]` *"Yes: keep 'differs'
  exact, and make P and T's withdrawal permanent."* (§3h): once withdrawn, withdrawn in every
  later report, outside k (`withdrawn_since`, carried by `fb_refit.carried_withdrawals` from the
  previous fb-refit.json), and "differs" has no minimum size. Several WINS: all reported, ONE branch,
  to the largest mean d (`fb_refit.branch_order`; `[2026-10-27, review 2]` the UNROUNDED one,
  `mean_d_exact`, never the 6 printed decimals). After a switch the eighteen do not
  restart; the eight do. `history` / `scored` stay in the report for information. The email
  reads the floor from the report (`floor`), never a 300 of its own. `test_fb_refit_counted.py`.
- 🔴🔴 **EVERY CONFIDENCE THE SITE SHOWS IS THE MODEL'S OWN.** `[Sam, 2026-10-11]`
  *"i just want the model to pick its OWN picks by itself, nothing more nothing less.
  ... only show confidence score on each pick that the model picks, BASED ON THE
  MODELS CONFIDENCE SCORE NOT THE SPORTSBOOKS"*; *"we can't just be a lapdog to
  sportsbooks"*. ⛔ Every % or chance shown, and every ranking or pick built on it,
  comes only from the data the model was built to read and its own record of past
  misses. A price, a de-vigged chance, a break-even or a line is NEVER an input. A
  price or line only says WHICH bet is priced: the side, the threshold, the
  break-even printed beside the row, and the value check (chance above what the
  price needs). Everything else stays: tabs, layout, lists, the top 25, the 50%+
  rule for game lines, the −400 floor, the parlays (their price strata are the
  payout bands), the Track Record. Each league's Track Record opens a new method at
  the switch, so old bands stay as graded. It supersedes ~~2026-09-25's C2 for
  pitcher rows~~ (now C1, `mlb_pitcher_cal.SHIPPED`), ~~2026-10-09's props-model
  stage 2 with the price~~ and ~~2026-10-01's alternate spreads at the books'
  chance~~. MLB: a thin board's top-up and a game-line tie are ordered by the
  model's number, never by edge; hitter rows (his own record) and the game model's
  moneyline and run line never read a price (`CORRECTED` is totals only, and totals
  are not on the card); pitcher rows' printed bands are kept per
  `confidence_method` in record.json (`calibration_printed_by_method`).
  `test_mlb_own_number.py`.
- 🔴 **THE PAGE SHOWS EACH TAB'S CONTENT, NOT NOTES ABOUT IT.** `[Sam,
  2026-10-01]` *"i just want what's supposed to be in each tab to be in
  each tab. do this for all 3 leagues"*; asked what stays, he chose:
  remove everything. ⛔ On every MLB, NFL and college tab: no explanation,
  caveat or warning box (`note`, `fnote`, `fbnotes`, `glwarn`, `domnote`
  or anything like them), no confidence pop-up (*"we have a track record
  for a reason"*), no badge legend, no MODEL / MARKET / DESCRIPTIVE /
  RECORD / LIVE tag (`span.kind`), no per-row flag, no stale-data bar or
  "out of date" note, nothing yellow. ✅ Kept: tables and cards with every
  number, headings, controls, the last-updated time where a tab shows one,
  and a one-line plain empty state. Two Trends headers carry their own
  meaning ("Rank (1 = most allowed)", "Per game vs FBS"). ⚠️ The DATA keeps
  every `kind`, `basis`, flag and note field, and every server-side check
  on them stays; staleness reaches Sam through the watchdog, health.json
  and the GitHub issue. `test_page_plain.py` fails if any of it returns.
- 🔴 **ONE TAB BAR FOR ALL THREE LEAGUES.** `[Sam, 2026-10-01]` *"lets have
  the colors of the tabs and the layout be the same for each league ... same
  order of tab from left to right, same colors"*. The header's `.subnav` is
  the only tab bar (`drawTabs`); one list, `TABS`, gives every league the
  order Scores, Gizmo's Picks, Odds, Player Props, Game Lines, Parlays,
  Trends, Track Record, News; a league without a tab leaves its slot out
  (`TABS_OFF`; ~~MLB has no Game Lines yet~~ `[Sam, 2026-10-01]` every league
  has Game Lines now, so it is empty). Every league opens on Scores and
  a league switch keeps the tab (`nextTab`). ⛔ Never draw a league's own bar
  again. `test_tab_bar.py`; the computed style is measured in a browser by
  `test_league_switch.py`.
- 🔴 **ONE LOOK FOR ALL THREE LEAGUES: DESIGN I.** `[Sam, 2026-10-17]` *"i like the
  light blue on i think that oone is good"*, choosing design I of the layouts he was
  shown: a white page; the ONE `<header>` is a navy side panel (logo, league switch,
  the one `.subnav`) from 1024 px and a top header below 1024 px (tabs five over four,
  every tab visible); royal blue #2449B8 the second colour; IBM Plex. ⛔ Green only for
  what is green on purpose (a positive edge, a hit, the projection chip, Sam 2026-08-26);
  no amber or yellow anywhere. A Gizmo's Picks row (pickCard, every league): the
  confidence as a number and a bar; the player, then the bet in blue; the game and its
  time (football's kickoff from `commence`) in their own column; the price with the book
  as the bet link (SET STATE kept); and every row not marked `below_price` prints
  "Break-even x%" and "Edge ±y" (the card's own edge, never recomputed, green only above
  zero; an MLB game line has no edge gate, so it can read "Edge -8" in plain ink; ~~football
  only, by `fbEdgeLine`~~); a row below its price keeps its C8 line. ⚠️ A row lays out by
  ITS OWN width (`@container`, about 840 px), never the screen's: keyed to the screen, the
  first build squeezed the player to 10 px at 601-690 and 821-960 px
  (`test_league_switch.py` §4). A Top 10 row is one element: name, % and price on line
  one of a phone. ⛔ MLB changed with it on purpose: `research/mlb_render_frozen.json`'s
  2026-10-17 `_why` lists every digest. ✅ Guarded: every word on every tab of every
  league reads at 4.5:1 (`test_league_switch.py` §5); nothing yellow or amber, by hue
  (`test_page_plain.py`); a pick row never squeezes its player from 601 to 1280 px and no
  tab is wider than the screen beside the panel (§4) or at 390 px, MLB included (§3); a
  NEW @media block that restyles a frozen rule fails `test_mlb_untouched.py`.
- 🔴 ~~**THE PAGE RENDERS ONLY FLAGS MARKED `actionable`.**~~ **THE PAGE
  RENDERS NO FLAGS** `[Sam, 2026-10-01]`, not even actionable ones. Sam,
  2026-08-26: *"we have to advertise a clean look to the website that
  doesnt include nonsense users dont need to read and cant understand."*
  T21, T22, rule 15 and STEP 4B are notes the model writes to ITSELF.
  ⛔ **They are still computed and still stored in `picks/<date>.json`** —
  the calibration record depends on every one of them, and a clean page
  must never become a card that stopped writing its diagnostics.
  `verify_card.py` checks both halves: nothing internal is marked for
  display, and the diagnostics are still being written. A flag only earns
  `actionable` if it changes what the reader can DO ~~— today the only one
  is "Hard Rock didn't post this", because the price on screen is then
  one they cannot bet~~. `actionable` is still written and checked; since
  2026-10-01 it decides nothing on the page.
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
  rule 55 requires is that the number be **labelled**, not hidden —
  `[Sam, 2026-10-01]` in the DATA only: the page prints no MODEL / RECORD /
  MARKET chip any more. So: every row carries `confidence_basis`, which is `MODEL` for pitchers and
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
- 🔴 **THE FOOTBALL CARD'S GAME LINES ARE THE GAME MODEL'S PICKS.** `[Sam,
  2026-10-01]` *"make the models gizmo picks game line picks the same format
  as the player prop picks"*. `card_fb.card_game_lines`: fb-model.json's
  picks for ONE day, the next slate with an unstarted game (`next_line_slate`,
  ~~the card's own slate day~~ `[2026-10-03]`: that props day had started),
  one row per pick in the prop row's fields (team or Over/Under where a prop
  has the player), drawn by `pickCard`; ~~the N biggest price gaps~~
  (`build_game_lines` is now only the same-game parlays' line legs).
  `[Sam, 2026-10-03]` only picks at 50% or more (`GL_MIN_CONF`), the 25
  highest (`GAME_LINES_MAX` = the props board's `BOARD_MAX`), whole-number
  confidence; a row that is not `kind` fb-line never stays in `game_lines`
  (archived) and is never drawn. Each spread pick is followed directly by
  ONE alternate spread when the books' ladder is pulled: the model's side,
  ~~the highest books' chance (`mkt`)~~ `[Sam, 2026-10-11]` the rung with the
  highest value above zero where ~~the spread fit, priced at that rung's own
  line,~~ `[Sam, 2026-10-16]` the predicted score, Normal(the team's predicted margin,
  fb-model.json `pricing.sigma.spread`) at that rung's own line, covers the rung and
  gives 50% or more, at −400 or longer, off the main line; it shows only
  under a listed pick. ~~⛔ Its confidence is the books' chance and its basis
  stays MARKET~~: its confidence is the model's own and its basis MODEL; a rung
  the model cannot price gets no row. `card-fb` builds `fb_model` and
  `game_lines_fb` BEFORE the card. `record_fb` grades the alternate spreads in
  their own line (`alt_spreads`, `by_basis` keeps the books'-chance rows apart);
  the model's picks keep fb-model.json's record. `test_fb_game_picks.py`.
  `[Sam, 2026-10-16]` ~~Only on the game's expected winner~~ A moneyline only on the
  expected winner (see ONE TEAM PER GAME); a spread and its alternate follow the
  predicted score (see A FOOTBALL SPREAD OR TOTAL PICK COMES FROM THE PREDICTED SCORE).
- 🔴 **A FOOTBALL SPREAD OR TOTAL PICK COMES FROM THE PREDICTED SCORE** (~~SITS ON THE
  PREDICTED SCORE'S SIDE~~). `[Sam, 2026-10-16]` The predicted score comes from the moneyline and
  total fits, each spread pick came from a separate fit: 13 of 66 college spread and total picks
  sat on the side the model's own score said loses (Purdue -3.5 beside "Purdue by 1.2"). Sam chose
  *"Must match the score"*, then: *"if your saying that purdue will win 25-23, that means gizmos
  picks should like the +3.5 spread for washington"* and *"Yes, everywhere"*.
  `fb_model.score_pick` makes `current_picks`' spread and total picks (the Model picks table, the
  ledger's snapshots, the card's source) through `fb_model.shown_pick`: at each quote, the side the predicted margin or total
  covers, its chance Normal(that margin or total, `score_sigma` / `total_sigma`), the best value
  above zero (~~the spread and total fits' `best_pick`, then `one_side.score_keep` after the
  one-team filter~~). The card's alternate spread is priced from the same score with fb-model.json's
  `pricing.sigma.spread` and is the best rung the score COVERS; `one_side.score_keep` still runs in
  `card_fb.card_game_lines` and `build_game_lines` (each game's best same-game-parlay line leg on
  the score's side). Landing ON the number is not its side, compared after rounding (21.1 - 14.1 -
  7 is 1.8e-15 in binary); `fb_why.score_agrees` does the same; no score, no pick. ⛔ Never inside
  `best_pick`: ~~`walk_forward`'s graded record and verdict still grade the spread and total fits
  (changing what they grade is Sam's call)~~ `[Sam, 2026-10-16]` *"lets do both"*: the graded
  record and verdict replay the shown rule too (see THE MODEL PICKS RECORD GRADES WHAT THE SITE
  SHOWS). ~~The Game Lines tab prints the score to one decimal (~~whole numbers~~), the
  precision picks are judged on.~~ `[Sam, 2026-10-17]` *"we need to not have decimal places in the
  predicted scores and make them only whole numbers"*, rounded so they never contradict a pick
  ("Round, stay consistent"): `one_side.shown_score`, the nearest whole score the expected winner
  leads and every pick the model's score agrees with still agrees with; `card_fb.shown_scores`
  applies it to every game of the week (the model's picks, the card's game lines and alternates,
  the parlay legs), writes `scores_shown` on the card, and the why and winners.json's `score_shown`
  (the Game Lines tab) print it; no agreeing whole score: one decimal. Picks are still judged on
  the model's own 0.1 score. `test_one_side_score.py`, `test_whole_scores.py`.
- 🔴 **NEW FOOTBALL DATA IS STORED ONLY UNTIL COWORK TESTS IT.** `[Sam, 2026-10-14]`
  NWS kickoff forecasts (`fb_weather.py`), CFBD venues / advanced stats (garbage
  time excluded) / pregame Elo / weather if the key's tier allows (`cfb.py`
  `store_new_data`), NFL injuries + starting QBs (`nfl.store_injuries`). ⛔ No fit,
  input, pick or chance reads them until a challenger is registered. Every CFBD
  call is priced by `cfbd_budget.preflight`. Their freshness rows are
  `freshness.STORED_ONLY`: stale is a warning, ⛔ never a red run and never a
  planned rebuild of a CFBD mode. `test_fb_new_data.py`. `[Sam, 2026-10-17]` The college
  injury reports, archives, rosters and defensive logs are stored the same way; the why reads a
  CURRENT report, and the model reads them only once its test passes (COLLEGE INJURIES).
  `[2026-10-26]` So are the game-day injury check's NFL snapshots (data/nfl/<day>/injury-reports/,
  written only on a change); ~~`injuries-<season>` is now rewritten only when its content changes, so
  its row has no clock deadline (`freshness.ON_CHANGE`; GAME-DAY INJURY CHECK)~~ `[2026-10-26,
  review]` ⛔ nfl-logs still rewrites `injuries-<season>` every day and its 3am deadline stays: that
  rewrite is how an nflverse outage is seen. Only the check skips an unchanged rewrite. The first
  build took the deadline off, and a 10-day outage read stale nowhere: a check weakened to let a
  change pass, caught in review.
- 🔴 **THE GAME-DAY INJURY CHECK: 9AM, 12PM AND 7PM ET, BOTH FOOTBALL LEAGUES.** `[Sam,
  2026-10-26]` *"make sure we're looking at injury status at 12pm of games starting and 7pm so we
  can make sure the models adjusted for injuries when deciding outcome for a vame"*; asked "Should
  college's injury adjustment use the 12pm/7pm reports, or the 9am one it was tested on?": *"do 9am,
  12pm, 7pm"*. ✅ The `injury-check` mode, one contract row per league on its probe
  (`latest/injury-check.json`, written on every attempt): due at 9:00, 12:00 and 19:00 REAL
  Eastern time (`freshness.INJURY_CHECK_ET`, `et_wall_utc`, the one DST rule `_us_eastern_offset`, moved here from fb_weather; 12:00 is 16:00Z
  under daylight time and 17:00Z from 11-01) on an ET day with a game still to kick off AFTER the
  slot; a slot whose later games have all started is owed nothing. ⛔ NO CRON CHANGE: the hourly
  news cron's pass plans it (a `Moments` deadline). NFL: this season's nflverse report into
  injuries-<season> (this call rewrites it only on a change, `only_on_change`; nfl-logs' daily one
  always does) and the week's statuses and game-day INACTIVES
  (roster_weekly INA) into a dated snapshot only on a change, STORED ONLY (`nfl.check_injuries`;
  it honours nfl-logs' back-off; an answer with no rows is a failed source, never every player
  cleared); college: the conference reports, once per slot
  (`cfb_injuries.run`, reused when this pass's reader already ran after the slot). Then `CASCADE`
  runs `card-fb` in the same pass: the game model, Game Lines, the card and its whys are rebuilt
  with the status as of the check (⛔ never after a plain `cfb-injuries` pass). SOFT; never in
  lateness.json (`UNTIMED`: GitHub's start delay would be a `late:` finding most game-day
  evenings). `[2026-10-26, review]` A check that read nothing is retried ONCE in its slot
  (`INJURY_RETRIES`; `[2026-10-27, review 2]` PLANNED on the next pass, `freshness.injury_retry`,
  never a deadline: ~~a retry moment a second after the failure~~ made the row stale at the end of
  the failed pass, a `fresh:` finding over one failed attempt); an NFL source down at 2 slots in a
  row is a `health` warning (a `fresh:` finding) that is ⛔ never replanned (`REPORT_ONLY_HEALTH`:
  each run would rebuild the card); `[2026-10-27, review 2]` so is the check ITSELF reading nothing
  at its last 2 slots, either league, whatever the cause (our own code raising included: the
  probe's slot log), until an attempt reads again; a run that serves no slot (the first pass after
  a merge, a manual run) counts toward neither; a season with no stored schedule owes nothing; the probe logs every slot's attempts for 8 days and
  the Monday status says how many checks ran before their games (`status.injury_checks`). ⚠️ WHAT
  IT DOES NOT DO: it changes a pick only through a model that reads injuries.
  College's does, once Sam merges the switch (its test passed 2026-10-19): a game still to start
  reads the newest report as of each build (`cfb_injuries.read_cut`; design §5). ⚠️ EACH LIVE
  BUILD, not only the three checks: on a game day those are the checks, the card deadline and any
  other `card-fb` rebuild. ~~a started or final game and every training, record and backtest
  caller keep §3's tested 9:00 cut~~ `[2026-10-26, review]` Training and `fb_inj_backtest` keep
  §3's tested 9:00 cut; the RECORD replays each played game with the report its last pre-kickoff
  build read (`fb_ledger.looked_moments` -> `inj_shown`, `fb_model.as_shown`), so it still grades
  what the site showed (`test_fb_model_record.py` §5). `[2026-10-27, review 2]` Read AT that build's
  own moment (`cfb_injuries.shown_cut`): `read_cut`'s max(9:00 cut, build), used at first, read a
  build before 9:00 ET, or any build for a kickoff before 9:00 ET, with reports it never saw. The moment is the
  game model's own reading (fb-model.json `read_at`, the snapshot's `model_read_at`), never the
  snapshot's later minute (a failed model build's pass snapshots the earlier build's picks).
  `test_injury_check.py` §4: the replay equals the live read at 120 build moments. ⚠️ ONLY THE
  REPORTS are replayed as of the build: the archive's night-before column and the role files
  (roster, defence) are read as stored now and are rewritten in place, so games built before they
  were stored (10-17 / 10-18, while college injuries were off) are replayed with today's copies,
  under Sam's "the record is recomputed each build"; an exact replay of them needs dated copies
  (not built). The NFL's
  adjustment FAILED its test (10-17) and stays off; signal 7 still reads the week before. ⚠️ The
  rest of the contract still reads a fixed UTC-4 (`ET_OFFSET`), an hour off from 11-01: a
  separate change. `test_injury_check.py`.
- 🔴 **THE FOOTBALL GAME MODEL READS ITS OWN TEAM RATINGS, NEVER THE BOOKS'.** `[Sam,
  2026-10-11]` *"our model needs to know the data and know these teams better than
  they know themselves"*. `fb_model.own_ratings`: per row, every final game of every
  stored `schedule-<season>.json.gz` (all divisions, FCS and below too) dated
  before the row's own week's Monday. Margin = home edge × (0 neutral, else 1) +
  R_home − R_away; points (one equation per side) = base + home-points edge × (at
  home, not neutral) + O_team − D_opponent. ⛔ FROZEN SETTINGS (Cowork chose them
  from five tried on the same games; the Track Record from the switch is the test,
  so never re-tuned on this data): weight 0.5 ^ (days before that Monday / 150),
  ridge 1 on every team term, none on the base or a home edge; pure-Python
  Gauss-Seidel, warm-started each week (matches a direct solve to 1e-6). The fits'
  first input: moneyline own margin / 10 (~~logit of the books' chance~~), spread
  (own margin − line) / 10 (~~line / 7~~), total (own total − line) / 10
  (~~(line − 45) / 10~~); every other input unchanged; no earlier game → 0.
  `[2026-10-12]` Every game-market fit caps each standardised input at ±5, in training
  and prediction (`fb_model.ZMAX`; head-to-head inputs 197–224 SD out printed
  0.000000%); a fit without `zmax` (props, MLB) is unchanged. `pml`,
  `M` and `T` stay for labels, grading, the break-even and the value check. Cowork's
  walk-forward at closing prices (2026-10-11): NFL moneyline +1.1% → +15.8%
  (12 → 39 underdogs); college moneyline +4.6% → −0.5% (it says 66% on picks that
  win 54.5%); spreads NFL −12.4% → −8.0%, college −1.1% → +2.7%.
  `test_fb_own_ratings.py`.
- 🔴 **THE FOOTBALL TABS ARE ABOUT THE NEXT GAMES, WITH ALL THREE BOOKS.** `[Sam,
  2026-10-09]` NFL props for the next slate with an unstarted game are bought every
  day once it is within 72 hours (`freshness.FB_NEXT_SLATE_H`, `next_slate`; college
  keeps its 14-hour window): about +540 credits a week, measured from the stored
  pulls. The props board keeps each book's latest price per game with the minute it
  was pulled, so a us2 refresh never drops FanDuel, DraftKings or a game, and holds
  only the next slate. The card's day is the earliest unstarted game's
  (`card_fb.slate_date`); once every game a board or card holds has started, the
  hourly pass rebuilds both (`freshness.slate_moves`: planned, never marked stale).
  The card's name check counts PLAYERS ONLY (Sam's choice): a team defense
  (`card_fb.TEAM_UNIT`, "<Team> D/ST" / "Defense") never counts; the 60% bar is
  unchanged. Once a slate's card is published, a started game takes no new seat
  (board, parlays, top plays): `freeze_published` keeps what was published for it.
  `test_fb_next_slate.py`.
- 🔴 **ONE SIDE PER PROP: ONLY THE SIDE THE MODEL GIVES 50% OR MORE, ALL LEAGUES.** `[Sam,
  2026-10-16]` A sweep after one-team-per-game found the same props model on both sides of 5 props
  (the card's Hunter Tipton Under 3.5 at 55%, its pick list's Over 3.5 at 45% because +162 paid).
  Sam chose *"Model's 50%+ side only: Every list shows only the side the model gives 50% or
  more."* `one_side.keep_props`: per over/under wager (one game, player, market and line), only
  the side whose number is 50+ AND above the other side's; an exact tie keeps neither; an anytime
  TD "yes" needs 50% too (~~a one-sided market is never touched~~: a 22% TD at +400 is the value
  side Sam declined); a wager with no number on either side never shows both ways
  (`one_per_wager`, MLB's rule). Where: `fb_props_model.current_picks` (live picks only; its walk-forward record is
  unchanged), the football card's pool before the price rules (`card_fb.prop_value`: the model's
  unrounded chance on a MODEL row, so 49.8 never ties 50.2), and MLB's `card.one_side_pools` (the
  PRINTED number; the board keeps blend's side only when it agrees, e.g. Nick Martinez outs, blend
  86% Over, printed Over 51 / Under 53: no pick). The starred ladder rung needs 50%+ too.
  `verify_card.py` runs `card.one_side_problems` on every MLB card. `test_one_side_props.py`.
- 🔴 **ONE ROW PER PLAYER PER MARKET ON THE GIZMO'S PICKS BOARD, ALL LEAGUES.** `[Sam,
  2026-10-16]` *"i dont want to see multiple of the same players in the gizmos picks ... marvin
  harrison jr with 3 different receiving props ... receiving prop and reception prop is good but
  both receiving yards prop is a no go."* That day: NFL MHJ x2, McKee x3; college six repeats;
  MLB two. Football: `card_fb.one_per_player_market` (his first row of each market in the board's
  order, before the 25-row cap). MLB: `card.select_board` never seats one player's market twice
  (`_playermarket`, which also keeps out a seated prop's other side). The liked list and top
  plays were already one per player; the parlays are unchanged. `verify_card.py` runs
  `card.player_market_repeats`. `test_one_per_player.py`.
- 🔴 **THE PROPS MODEL SETS THE FOOTBALL CARD'S CONFIDENCE.** `[Sam, 2026-10-09]`
  *"Where fb_props_model prices a prop on the card ... the row's confidence is the
  model's probability and the card ranks by it. A prop it does not price keeps the
  player's own rate."* A priced row is `confidence_basis` MODEL (`model_p`, whole-number
  `confidence`), an unpriced one RECORD; the record stays in `rate` / `record`.
  `[Sam, 2026-10-26]` The record blends THIS season's games and LAST season's at
  4 / (4 + this season's games) (`research/fb_card_fix_spec.md` §3) every week, the same
  rule Sam asked of the contest (*"use games from last season and the ones played this
  season"*): ~~once this season's median player reached 6 games, `card_fb.load_logs` took
  that season alone and dropped last season~~ (not reached by either league before the fix:
  NFL median 5, college 4). A slate whose season has no game yet reads last season alone
  (its weight is then 1). `test_card_fb.py` §13, `test_nfl_opener.py` §2. `[review,
  2026-10-26]` A board name is looked up in BOTH seasons' logs (`card_fb.match_player`;
  ~~last season's only~~, which left a rookie or a player new to FBS unrated all season): a
  rookie is rated on his games this season (G25 none); ~~last season's one holder keeps a name
  he still plays under (a name shared this season stays his); a holder with no game this
  season yields it to this season's one holder; anything else is ambiguous, never a guess~~
  `[2026-10-27, review 2]` (that chose by which LOG held a name and never asked his team: the
  Titans' RB Michael Carter read the Eagles CB's record, Kent State's Brandon White Kansas
  State's WR's) a name two players hold is decided by the BOARD GAME'S TWO TEAMS
  (`teamkeys.team_codes`): the holder whose latest game this season was for one of them,
  else a holder with no game this season whose last-season team is one, else nobody
  (ambiguous, never a guess). A lone holder keeps his name, except in college, where one who
  has played this season for another team is someone else; an NFL lone holder elsewhere is
  kept (a trade). The row's role and role sentence read only that matched id, never a
  namesake's by name (`current_role`, `role_change_note`). The
  60% name join counts a match in either log. `test_card_fb.py` §13c, `test_fb_role_season.py`.
  `collect.build_card_fb` builds the props model first on BOTH card paths (the props
  pull and `card-fb`); it prices the props board itself and stamps `board_pulled_at`,
  and a model that priced another board leaves the whole build on the record
  (`card_fb.props_model_rated`). Every card from the switch is method ~~`…+props-model`~~
  `[Sam, 2026-10-11]` `…+props-own` (record-only builds too), so the old bands stay
  as graded. `[Sam, 2026-10-11]` The model's chance is its OWN: stage 2 is stage 1
  corrected by its own past misses (`fb_props_model.s2_features` = [logit(p1), TD],
  ~~with the books' chance~~), trained on every graded rung and applied priced or
  not; `[2026-10-12]` trained on BOTH sides of every two-sided rung (`s2_rows`) and
  applied per side (~~the under as 1 − the corrected over~~), the pair rescaled to
  sum to 1; `p_market` stays in the data for the record only. Expect the low 50s and few
  −200 favourites: that is the model being honest. `test_fb_props_own.py`. When the name check
  fails, only the records are withheld: a MODEL row keeps its % (Sam's choice; the
  model matched the player itself). A board row's one sentence is
  its record at the line, this season first (~~the average, the far-line warning, the
  small sample, the college note, "not a forecast", "no football model"~~).
  `fb_agreement` still compares the RECORD with the model (Sam's choice).
  `test_fb_props_confidence.py`.
- 🔴 **A LIKED NFL OVER NEEDS A REAL ROLE THIS SEASON.** `[Sam, 2026-10-15]` *"we can't be
  betting on guys like tory horton because he's had 2 good games ... he's a wr4"*: an over or
  anytime TD is liked only at 40%+ of snaps over his last 3 games, 12%+ of targets on a
  receiving prop, 8+ carries on a rushing prop (`card_fb.role_ok`); an under is never blocked.
  `[2026-10-16]` The role is `card_fb.current_role`: THIS season's log, by id ~~or a unique name~~
  (`[2026-10-27, review 2]` the matched id only; an ambiguous or unmatched name has none).
  ~~A rookie had none (the check skipped him); a player with no game this season used last
  season's~~. A player with no game this season now has a zero role (n 0), so his over fails.
  Shares are stored at 4 decimals and rounded once on the page. `test_fb_best_plays.py`,
  `test_fb_role_season.py`.
- 🔴 **EVERY FOOTBALL GIZMO'S PICKS PICK CARRIES ITS WHY.** `[Sam, 2026-10-15]`
  *"i also want a "why" behind the picks underneath each gizmo picks pick"*.
  `fb_why.explain` writes `why` on the liked lists only (`liked`,
  `game_lines_liked`, copies of board rows): a prop gets his role (NFL: snaps,
  targets or carries over his last ~~3~~ games, saying how many), ~~his record at
  the line this season~~ the card's OWN record sentence (its half-the-snaps and
  6-game gates; none when the card shows none), what the opponent allows his
  position and its rank (ties read from the right end), the opponent's Out /
  Doubtful defenders who guard him (NFL, ~~latest report~~ THIS game's week's
  report; `[Sam, 2026-10-17]` college, this game's CURRENT conference report), and the chance against the break-even ("the model's" on a MODEL row,
  "his record's" on a RECORD row); a game line keeps its sentence and adds the
  model's predicted score (`[2026-10-16]` only when it lands on the pick's side:
  the score comes from the moneyline and total fits, ~~the spread fit is separate~~
  and every football spread and total pick now comes from it)
  and each team's points for and against. `[Sam, 2026-10-26]` *"let's do all of this"*, approving
  the proposal "add one plain line to each game pick's why, like 'Washington is 2–3
  against teams rated above average'. That's information only and moves no %.": a game line also gives each
  team's record this season (W-L, W-L-T with a tie) against the teams the model
  rates above average at THIS game's Monday (`fb_model.above_average`, T72 §3f's
  definition, stored in fb-model.json `above_average` by the game's schedule day,
  from the solve the rows already read; every other field byte for byte the same).
  The season is the kickoff's, never the
  newest file. ⛔ It explains and changes no pick, chance, rank or price. A fact
  it cannot find (an ambiguous name, a team it cannot resolve, a season or week
  with no stored file) is left out, never guessed; a row whose why fails keeps
  its old one; the card's sentence is kept in `why_card`. `[2026-10-16]` Its
  first version was checked sentence by sentence against the raw files (225) and
  six defects were fixed. `test_fb_why.py`.
- 🔴 **FOOTBALL GIZMO'S PICKS IS AS SIMPLE AS MLB'S.** `[Sam, 2026-10-17]` *"no above their
  price only button in gizmos pikcs not needed"*; *"i dont want to have past picks to show
  outcomes it just makes the page way to long ... in the mlb gizmos picks we have the picks the
  why underneath each pick, and then the top 10 plays of the day, we should do the same for both
  football leagues"*; *"lose everything in the gizmos picks tab after the model picks gameliones
  tab ... it should be as simple as the mlb gizmos picks"*. ✅ The tab draws the Player props /
  Game lines switch, the card's liked list (`fbView`: `liked`, `game_lines_liked` whenever the card
  has them; `[Sam, 2026-10-17]` *"we need to sort our gizmos picks by confidence score, the highest at
  the top and working down"*: each list SHOWN by confidence, a tie by edge, the same rows CHOSEN as
  before (`card_fb.best_liked`, one per player or game, by edge; the freeze trims by edge, then shows
  by confidence); `test_top_plays.py` holds every list the card shows to it) with the why under each pick, and `fbTopPlays`, the top 10 (`card_fb.TOP_N` = 10, as
  MLB's `card.TOP10_N`; ~~20~~), each play filtered on its OWN game (started, conference), ~~only
  in a game the liked list covers~~ (that hid 2026-10-18's 10th NFL play). ⛔ No "Above their price only" button (~~`FBABOVE`,
  `fbAbovePass`~~), no Model picks / Prop model picks / "What the model showed, graded" panels
  (~~`fbModelAppend`, `fbModelHtml`, `fbPropModelHtml`, `fbLedgerHtml`, `fbPointText`~~) and no
  "Card vs props model" record (~~`fbAgRecordHtml`~~); fb-model.json, fb-props-model.json,
  model-ledger.json and agreement.json are still built and graded, and past picks with their
  outcomes live in the Track Record. `research/fb_model_live_spec.md` (frozen) still says the
  ledger is shown: Sam changed that requirement here. `test_fb_phone_page.py`, `test_fb_line_sign.py`,
  `test_fb_ledger.py`, `test_agree_flags_page.py`, `test_top_plays.py`.
- 🔴🔴 **ONE TEAM PER GAME: ~~EVERY SIDE PICK~~ EVERY MONEYLINE AND RUN-LINE PICK IS ON THE
  MODEL'S EXPECTED WINNER, ALL THREE LEAGUES** (`[Sam, 2026-10-16]` a football spread follows
  the predicted score). `[Sam, 2026-10-16]` *"the model picked huskies on the moneyline for college
  foootbal but also picked the -3.5 spread for purdue; the huskies opponent ... we can't
  have our model choosing both sides at once"*; asked which side stays, he chose the
  expected winner. `one_side.py` holds the ONE rule (`expected_side`, which winners.py
  reads, so the Game Lines tab and every list agree) and keeps a moneyline, ~~spread,
  alternate spread~~ or run-line pick only on the team the tab picks to win; a total is
  never touched; no win chance, no side pick. `[Sam, 2026-10-16]` A football spread and its
  alternate follow the predicted score instead, which can back the expected loser (Purdue
  25-23 => Washington +3.5): see A FOOTBALL SPREAD OR TOTAL PICK COMES FROM THE PREDICTED SCORE. It runs AFTER each market's own pick in
  `fb_model.current_picks` (the Model picks table, the ledger's snapshots, the card's
  source; `[2026-10-16]` inside `fb_model.shown_pick`, which the graded record replays too), `card_fb.card_game_lines` (~~before the alternate spreads, so they follow~~
  moneylines only), the same-game parlays' line legs (`build_game_lines`: each game's best
  ALLOWED leg; a moneyline leg on the winner, a spread leg on the score's side), and
  `card.game_line_rows` (MLB, by `win`); when the MLB game model is rebuilt on its own
  (`game-model`), `card.refilter_game_lines` removes a published, unstarted row no longer
  on the new expected winner (~~the card's game lines stay as built~~). ⛔ Never inside
  `fb_model.best_pick` (the pre-registered lambda test reads it): ~~`walk_forward`'s graded
  record replays it per market and stays as it was~~ `[Sam, 2026-10-16]` the graded record
  replays `shown_pick`. ⛔ It only removes; a published or frozen row is never edited (the ledger keeps
  what it showed). `verify_card.py` fails an MLB card whose unstarted game lines back both
  teams or the other team (judged on the model main() built them from, `LAST_GAME_MODEL`).
  ~~⚠️ The Model picks panel's record tables and verdict (`walk_forward`) still grade the old
  per-market rule, both sides included: changing what they grade is Sam's call.~~ `[Sam,
  2026-10-16]` They grade the shown rule now: see THE MODEL PICKS RECORD GRADES WHAT THE SITE
  SHOWS. Measured that day: 18 of 55 college and 5 of 13 NFL games in the
  model's list, 6 of 11 MLB games with game lines. `test_one_side.py`,
  `test_mlb_game_lines.py`.
- 🔴 **THE MODEL PICKS RECORD GRADES WHAT THE SITE SHOWS.** `[Sam, 2026-10-16]` Offered a
  switch of the record from the old fits to the score-based picks and a backtest of them, he
  said *"lets do both"* and *"i want whatever the models score predictions are to directly
  correlate with any gameline picks the model chooses"*. `fb_model.shown_pick` is the ONE pick
  rule: a spread or total FROM the predicted score (`score_pick`), a moneyline only on the
  expected winner. `current_picks` (the live list) and `walk_forward` (the Model picks record,
  its closing-line record and the verdict, `fb_model_live_spec.md`'s rule unchanged) both call
  it; each week's score uses that week's fits and a spread of results (`score_sigma`,
  `total_sigma`) from its TRAINING games only; a week's picks start once the MONEYLINE fit
  exists (a spread pick never needs the spread fit). `fb_model.game_score` is the one place
  the predicted score is made (the Game Lines tab, the list, the record), from the same
  rounded win chance the tab prints. ⛔ `walk_forward(rows,
  rule="fits")` (each fit's own `best_pick`, both sides) stays ONLY for the pre-registered
  signal-9 report (`fb_signal9`), which must score what it scored; `best_pick` is unchanged
  (the lambda test). The record is recomputed each build, so its past numbers changed with the
  switch (Sam's choice). `test_fb_model_record.py` builds the same games once upcoming and once
  played and fails if the record and the list ever pick differently.
- 🔴 **EVERY FOOTBALL GAME IS SIMULATED 10,000 TIMES, EVERY BUILD.** `[Sam, 2026-10-17]`
  *"we shoudl be setting up the 10000 game simulations for each game every week"*; he chose
  "Backtest, then switch" and overrode two rules for it (looking at results first; skipping the
  Monday contest). `fb_sim.py` plays every game in `win_chances` 10,000 times; the Game Lines tab
  shows how often the pick wins. The bar (research/fb_sim_design.md §3, committed before the run):
  log loss at most the smooth curve's AND closing-line return at least its. Result (§4): NFL
  0.70221 v 0.70259 but +1.23% v +1.85%; college 0.72217 v 0.72074; so `fb_model.SIM` is off in
  both and the picks keep the smooth curve. NFL injuries (T69 IN's measures, sized weekly by
  `injury_fit`, the win chance moving with the margin): 0.70281 v 0.70259, so `INJURIES` is off
  too (its fitted QB-out size pointed the wrong way). ⛔ A switch moves only with a new recorded
  run in research/fb_sim_backtest.json that passes the bar; test_fb_sim.py fails otherwise.
  ~~College has no injury data stored.~~ `[Sam, 2026-10-17]` College injuries: see COLLEGE INJURIES.
- 🔴 **COLLEGE INJURIES COME FROM THE CONFERENCE REPORTS: CHECKED, STORED, SHOWN WHEN CURRENT,
  TEST-GATED FOR THE MODEL.** `[Sam, 2026-10-17]` *"use the college injury source as long as it's
  accurate and up to date, we wouldn't want misinformation ruining our bets."* He was told the
  conference sites' terms limit automated reading; this supersedes ~~his 2026-09-23 "Build it only
  if it is free and allowed by those sites' terms"~~ (`dossier_fb.PERSONNEL_COLLEGE`; its signal 7
  stays NFL-only). `cfb_injuries.py` (`cfb-injuries` mode, planned by its probe row on every college
  pass, no cron change): HD Intelligence's public reports for SEC, ACC, Big Ten, Big 12 and MAC and
  the Sun Belt / Pac-12 feeds, images stripped, written once per change (daystore
  `injury-reports`), the past seasons' archives once (`data/ncaaf/history/injury-archive-<s>`).
  ⛔ ACCURATE: both teams known (an explicit alias table, never fuzzy, never the display names),
  exactly one stored schedule game, the kickoff equal to the minute, parsed rows only, known
  statuses only (Exempt is unknown, never healthy); anything else is refused and named in the
  probe. ⛔ UP TO DATE: a report is current only when published at most 36 hours before kickoff
  and our snapshot of it is at most 6 hours old; only a current report is shown (the why) or read.
  `cfb.py` keeps the jerseys and defensive stats CFBD already sends (`roster-<s>`, `defense-<s>`,
  zero extra calls; 2025 once, priced). The model (`fb_model.injury_readings` ->
  `cfb_injuries.attach`, design §3: QB out, offence share, defence share; no report = no reading)
  moves only if `research/cfb_injuries_design.md` §4 passes, the NFL's bar, fixed before any
  number: `fb_inj_backtest.py` runs it ONCE, by itself, in the Monday fb-refit job once the data
  is stored, and pushes one `fb/injuries-ncaaf-<date>` branch for Sam (the switch only on a PASS);
  the Monday email names it. ⛔ Merging is Sam's. `test_cfb_injuries.py`, `test_fb_inj_backtest.py`.
  `[Sam, 2026-10-26]` ✅ IT PASSED 2026-10-19 (log loss 0.7205076 v 0.7205148, closing return
  −3.91% v −4.12%, recorded in research/fb_sim_backtest.json `injuries.ncaaf`, branch
  `fb/injuries-ncaaf-2026-10-19`), and the game-day injury check's PR carries that switch:
  `INJURIES["ncaaf"]` is ON from Sam's merge, after he asked for the models to adjust for injuries
  (*"make sure we're looking at injury status at 12pm of games starting and 7pm so we can make sure
  the models adjusted for injuries when deciding outcome for a vame"*) and answered *"do 9am, 12pm,
  7pm"*: ~~the newest snapshot fetched before 9:00 ET on game day, for every game~~ a game still to
  start reads the newest report as of each build (`cfb_injuries.read_cut`, design §5); a started or
  final game, the training rows~~, the record~~ and `fb_inj_backtest` keep §3's 9:00 cut
  (`[2026-10-26, review]` the record replays each played game as its last pre-kickoff build read
  it: it grades what the site showed; `[2026-10-27, review 2]` its reports at that build's own
  moment, the archive and role files as stored now). The Monday
  email stops listing the branch once main holds the entry (`status.injury_recorded`).
- 🔴 **THE GAME LINES TAB IS THE MODEL'S PICK TO WIN EACH GAME, IN ALL THREE
  LEAGUES, ONE LAYOUT.** `[Sam, 2026-10-01]` *"remove the game lines standalone
  tab with moneyline predictions, in this tab you will simply just give the
  models pick on whos going to win the game outright. do this for all
  leagues"*. `winners.py`: one row per slate game (the teams, the start, the
  side with the higher chance, that chance as a whole number, the best
  moneyline at the league's books), by start time; ⛔ no price floor and no
  edge rule. MLB reads `win` in mlb-game-model.json (no pick until both
  starters are named); football reads fb-model.json `win_chances` for
  `card_fb.next_line_slate`'s day. Frozen at the start, graded once, ONE
  record per league in winners.json (top of the tab ~~and the league's Track
  Record~~; `[Sam, 2026-10-17]` the Track Record shows only its three hit rates and the
  by-date lists), never mixed into another; verify_record.py re-grades it.
  ~~The alt ladders, fair lines, rung tables and alt parlays~~ left the page;
  their files are still built (the card's alternate spreads read the ladder).
  `test_game_lines_page.py`.
- 🔴 **FOOTBALL ON A PHONE, BELOW ITS PRICE, AND THE WEEK.** `[Sam, 2026-10-14]`
  *"look at every aspect ... and your only goal is to do anything to make it
  better"*; *"the way i want you to predict outcomes of football games is by
  predicted scores"*. C8's rule now covers football props and game-line rows
  (`card_fb.mark_below_price`: the card's own `edge` <= 0, before the freeze); a
  row above its price prints ~~"Break-even 53.7% · edge +1.3"~~ `[Sam, 2026-10-17]`
  "Break-even 53.7%" and "Edge +1.3", in every league (DESIGN I). ~~"Above their price
  only" (kind bar, OFF by default, localStorage) hides exactly edge <= 0.~~ `[Sam,
  2026-10-17]` "no above their price only button in gizmos pikcs not needed": gone; the
  page always shows the card's liked lists. Under
  600 px the tab bar is two rows, a prop row stacks its price under the player and
  a table scrolls in its own box. Football Game Lines shows winners.json's `week`
  (every game in `win_chances`, by ET day, "ET" times) with the model's predicted
  score (`fb_model.predicted_score`, ~~output only~~ `[Sam, 2026-10-16]` the source of
  every football spread and total pick); `rows` stays the graded record.
  `test_fb_phone_page.py`; 390 px measured by `test_league_switch.py` §3.
- 🔴 **THE MLB CARD'S GAME LINES ARE THE GAME MODEL'S MONEYLINE AND RUN LINE
  PICKS, AND ⛔ NEVER ITS TOTALS.** `[Sam, 2026-10-03]` *"go on with moneyline
  and run line only. Totals stay in mlb-game-model.json with both records
  (uncorrected and corrected) and keep being graded there, but they never
  appear on the card, the page or the record's game-line line."* (The total's
  50%+ sides won under half in the model's check.) ⛔ **Totals come onto the
  card only by Sam's decision**, never because a later check looks better.
  `card.game_line_rows`: one row per market in `GL_MARKETS`, the side at 50%
  or more (`GL_MIN_CONF`) and −400 or longer at board.json's best of the five
  books (a run line only at its exact signed point), both starters named,
  the card's own day, at most 25 (`GAME_LINES_MAX`), whole-number confidence
  that is the model's OWN chance on both markets `[2026-10-03]`, `kind` mlb-line, drawn by `pickCard` under Gizmo's Picks' Player props /
  Game lines switch, frozen at first pitch (`freeze_game_lines`). Graded in
  their own line (record.json `game_lines`, `collect.GAME_LINE_MARKETS`),
  re-graded by verify_record.py, never in a props count (`[Sam, 2026-10-17]` the
  Track Record's Board is props + game lines, `board`, beside both, never in `overall`).
  `test_mlb_game_lines.py`. `[Sam, 2026-10-16]` And only on the expected winner
  (`win`): see ONE TEAM PER GAME.
- 🔴 **THE TRACK RECORD: THREE HIT RATES, THEN THE DAYS, ALL THREE LEAGUES.** `[Sam, 2026-10-17]`
  *"in track record we should have a game lines tracker ... lose the was the record right?
  section of it. i only want the board hit % to be shown(this is the 25 player props and all the
  game lines hit %) and i want both hit % to be shown ... board(all picks), player props(only
  player props), and game line(only game lines)"*; for MLB he chose "Remove both" and, below the
  three, "Just the by-date lists". ✅ Every league's Track Record draws three `trBox` boxes:
  Board (record.json `board` = every graded pick the card showed, props + game lines), Player
  props (`overall`, the props alone, unchanged) and Game lines (`game_lines`); then "Player props
  by day" and "Game lines by day", each day opening its rows (record-detail `days` /
  `game_lines`, `lineDetailHtml`). ⛔ ~~Four boxes, the winners' line, the market table, "Was the
  record right?" (football), "Does the confidence number mean anything?" and "Is v5.0 still the
  best version?" (MLB)~~: gone (`bandRow`, `refitPanel`, `fbCalBlock` deleted; their data is still
  built). Football's game lines are graded by `record_fb.grade_game_lines`: every fb-line row a
  card SHOWED (its liked list, else its list plus `card_fb.GL_EARLIER`'s archive: 5 NFL and 35
  college archived rows had never been graded), the LAST card that showed a game decides (a game
  is its schedule id, whatever kickoff minute a card printed: 2026-10-04's 1pm NFL games at 17:00Z
  on one card and 17:05Z on the next were graded twice, keyed on the minute), a push
  or tie is void, joined to the schedule by `sched_id` or the snapshots' names (`line_ids`); its
  record.json `game_lines` carries the tally at the TOP, MLB's shape, which the box reads, and the
  grader reads the schedule from its working tree like every other file it reads (beside
  game_lines_fb.py, tests' planted cards were graded on the live schedule). MLB's
  `board` is collect_record's, checked by verify_record (board = overall + game lines); each MLB
  game-line row keeps its final score, as football's does. Football's
  by-day detail prints an anytime TD as "Yes" (~~"Under null"~~). `test_track_record.py`.
- 🔴 **EACH KIND KEEPS ITS OWN 25 SEATS.** `[Sam, 2026-09-25, C8]` The
  card showed 1 pitcher and 49 hitters: ~~an unused half spills to the
  other kind~~, and after C2 (#166) few pitcher rows beat their price.
  ✅ `card.select_board`: hitters up to 25 that beat the price; pitchers
  that beat it first, then the best remaining pitcher rows by the
  corrected number, marked `below_price` (the page prints the %, the
  break-even and the edge — `[Sam, 2026-10-01]` as plain numbers on the
  row, no sentence). Never both sides of one prop, keyed by GAME
  ID. ⛔ Do not let one kind take the other's seats again.
  `test_card_seats.py`, `verify_card.py` section 7c.
- 🔴 **A CARD IS MATCHED TO A BOARD RECORD ON NEAREST FIRST PITCH, NEVER
  ON A DATE.** ⛔ Do not "simplify" `boardFor()` back to a date comparison.
  **A UTC date is not a game's date**: a 9:40pm ET first pitch is `01:40Z
  THE NEXT DAY`, so every night game files under tomorrow and the next
  afternoon's card inherits it. That shipped on 2026-08-26 and put six
  games' LIVE IN-PROGRESS odds onto the following day's cards — CHC at
  −4000 with a 4.5 total, Pittsburgh implied for 0 runs. ⚠️ **ET dates are
  not sufficient either**: a doubleheader is two games with the same teams
  on the same ET date. ~~Nearest first pitch inside `BOARD_MATCH_WINDOW_MS`
  separates all three cases~~ — **false for a doubleheader, and it was live
  `[2026-09-25]`**: MLB lists game 2 of a traditional doubleheader at a
  PLACEHOLDER time (`startTimeTBD`, BAL @ NYY 20:10Z beside game 1's
  20:05Z; odds feed 23:06Z), so game 2's card showed game 1's odds.
  ✅ **The game decides first**: MLB's `gameNumber` against the board's
  first-pitch order, when both list the same number of games for the pair
  that ET date. Only otherwise does a FIRM first pitch decide, inside a
  90-minute window (narrower than every same-pair gap ever stored), never
  between two records, never on a placeholder. **It fails closed** — no
  candidate returns null and the card renders with no odds. A card missing
  a line is a card missing a line; a card showing another game's line is
  misinformation. `test_board_match.js` runs against the real board and
  the newest stored schedule; `test_board_doubleheader.py` replays the
  2026-09-25 doubleheaders.
- 🔴 **`run_line` is the HOME team's point, by MAJORITY across books, then
  cross-checked against the MONEYLINE.** ⛔ Never take it from one book.
  Books split on which side they show laying the runs — 11 to 6 on TB@DET,
  2026-08-26 — and `team_total` is derived from it, so one book's label
  shipped the implied runs to the wrong team on 3 of 19 games. The
  moneyline is the authority: it is a single unambiguous market and the
  favourite lays the runs. A row re-oriented against its spread label
  carries `run_line_conflicted_with_moneyline` ~~and says so on the page~~
  (`[Sam, 2026-10-01]` no RE-ORIENTED chip on the page; the line shown is
  already the corrected one, and `verify_board.py` still checks it).
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
  exit 0, and a green check proved nothing. `[Sam, 2026-09-26]` One
  refinement, judged by the freshness contract (`freshness.judge_failures`):
  a converge mode that failed on an OUTSIDE SOURCE (HTTP, network, timeout,
  `SourceUnavailable`) while every artifact it writes is still inside its
  deadline is a `::warning::` naming the source, not a red run. ⛔ Our own
  exception stays red whatever the contract says: the seven "outside
  source" failures that prompted this were football `props-board` raising a
  `TypeError` after it had written its file (fixed; `test_run_mode_left.py`).
- 🔴 **Every workflow runs on a PINNED image (`ubuntu-24.04`), never
  `ubuntu-latest`, with Node 24 actions and its own Python.** `[2026-09-24]`
  GitHub moves `-latest` to Ubuntu 26.04 from 2026-10-19 (image Python
  3.12 → 3.14, Node 20 → 24, apt names change). `test_runner_image.py`
  fails on a floating label, a Node 20 action major, an action not in its
  table, or a job running the image's Python. ➡️ Move a pin only after
  `pr-tests`' `ubuntu-26.04` rows are green — they run on every PR.
  Details: `docs/HANDOFF-2026-09-24-runner-image.md`.
- 🔴 **A SEASON COMES FROM THE GAMES, NEVER FROM THE CALENDAR YEAR.** `[2026-10-27]` R6:
  everything was written inside one season, where the two agree. A football DATE's season
  is `fb_why.season_of` (January and February are the season before: the Track Record
  skipped every January card), the season in progress NOW is
  `freshness.current_football_season`, and an NFL game's week is its own schedule row
  (`fb_why.game_week`). The MLB pulls ask for the newest season with a stored final of a
  game the product cards (`collect.mlb_pull_season`; ~~`now().year`~~ turned every MLB run
  red from 01-01 to mid-April); while that season is older than the calendar's, statsapi
  is asked whether the calendar's is under way (a scores store that stopped adding
  finals). For 45 days after a season's first final, a CLEAN pool nobody has cleared
  pulls the season before, with a `::warning::`; a broken pool (a domain violation, the
  bar's field missing) still raises, and the pull's own stored file is a floor on every
  path, so a season never steps backwards (`collect.season_pool`). Every MLB game owes a card except a code in
  `mlb_game_model.NOT_CARDED` (spring training, exhibition, All-Star, intrasquad; parsed,
  and an exclusion list, so a code nobody has seen still owes one). `test_year_turn.py` §1
  fails on a year sliced off a date (under int(), of str(), in a %-format of one value or
  a tuple, a `+` or an f-string), a `.year` outside a date constructor, or a
  `strftime("%Y")`, unless it is named with its reason. ⚠️ It does not see a slice handed
  straight to a call or a variable, `.format()`, or a LITERAL year: of those only the
  `data/2026-*` odds glob is guarded (§7); `players-2026`, `(2025, 2026)` and the like are
  the season lists in Sam's decisions or the August 2027 follow-up. ⚠️ Left, with the
  decisions that are Sam's: the handoff's R6.
- 🔴 **AN MLB RUN THAT REACHES THE END OF ITS HOLD STARTS ITS SUCCESSOR (THE
  RELAY).** `[Sam, 2026-10-06]` *"a card is on time even when GitHub starts a
  scheduled run hours late"*: on 10-06 the card due 14:00Z was built 16:02Z,
  because the only morning MLB run ended its hold at 12:42Z and the next
  cron landed at 15:52Z. ✅ collect.yml's last step runs `relay.py`; a
  scheduled MLB run, a push and a relay link each dispatch ONE successor
  (`workflow_dispatch`, `relay=true`) that holds 320 minutes and only ever
  `converge`s. ⛔ None when another MLB run is queued or running, past
  `RELAY_DAY_CAP` (5) links a UTC day, on a re-run, or when every stored
  schedule says neither the last card deadline's day nor the next one's has
  MLB games (the off-season; fail closed, so one off-day between game days
  does not stop it): the chain ends and the crons, unchanged, restart it. A relay link WAITS for the run that started
  it (`cancel-in-progress` is false only for it), so a red run stays red.
  MLB only: football runs are one pass in a queue per cron. And LATENESS
  LEAVES A RECORD: every converge pass writes `latest/lateness.json`
  (`freshness.record_builds`, the first build after each deadline); the
  watchdog reports DEGRADED, no repair, while a last build was more than
  `GRACE_MIN` (60) late, until the next on-time build. `test_relay.py`.
  `[Sam, 2026-10-07]` Only a `measured` entry counts: an artifact's first entry
  is a sighting (NFL record.json read 9100 minutes late), not a measurement.
- 🔴 **THE REPO NOTICES ITS OWN PROBLEMS; NO CLAUDE AUDIT DOES.** `[Sam, 2026-10-07]`
  *"the website should do all of them themselves"* (scheduled Claude tasks and
  self-repair are switched off). ✅ `watchdog.check_stopped_league`: a row whose
  deadline fell after its league's freshness.json was written, past due with no
  pass for over `STOPPED_GRACE_MIN` (~~90~~ 240 `[Cowork replay, 2026-10-07]`:
  90 raised 44 findings in a week, none a real stop; the grace is on the ROW,
  never the file's age; a row another workflow builds, `runs`, is skipped)
  -> BROKEN for a card, DEGRADED otherwise, no repair. ✅ runs.json
  is read only through `runs_report.run_list`, age first ("the run list is N
  hours old", no verdict). ✅ verify_record writes `record-verify-failure.txt`
  on a failure (removed on a pass) and the watchdog reports it. ✅ A workflow
  GitHub reports switched off (`runs_report.DISABLED`) is not expected to fire,
  ⛔ never collect, runs or status (`ALWAYS_ON`). `test_watchdog_stopped.py`.
  ✅ Every Monday `status.py` (staged `status.yml`, daily) posts ONE fixed-title
  issue to smh0602; other days only a health check over 12 hours old. ✅ Only a
  BROKEN finding opens the watchdog's issue (`watchdog.alerting`); DEGRADED stays
  in health.json and the weekly. Every alert ends with `watchdog.what_to_do`
  (what is wrong, is the site updating, a prompt ready to paste). lateness.json
  keeps 8 days of measured `late`. `test_status.py`. ✅ `[R1, 2026-10-18]`
  `watchdog.check_learner_landing`: every cron workflow that `git add`s a data/ path must
  land it; missing after its first run since first seen + 600 min + its timeout, or older
  than 2 periods + grace -> DEGRADED, no repair; first-seen is carried in health.json
  `learners`. `test_learner_landing.py`. ✅ `[2026-10-23]` A REFUSED ODDS API KEY IS
  BROKEN: 10-22 21:42Z -> 10-23 17:10Z every call was a 401 (the plan lapsed and was
  bought again) and health.json called it staleness that repairs itself. Every 401/403
  writes `data/latest/odds-refused.json` (the API's own reason, the key scrubbed);
  `watchdog.check_odds_refused` is BROKEN until a paid pull lands after it, and its alert
  gives Sam the steps in `docs/FIX-ODDS-KEY.md` (`SAM_DOES`), never a prompt for Claude
  and never the self-repair list. ⛔ The run's own colour is unchanged (Sam's 09-26
  rule). `test_odds_refused.py`. ✅ `[2026-10-27]` A finding names only a repair that acts
  in its own league (`watchdog.REBUILDS`: MLB `card`/`record`, football `card-fb`, checked
  against each league's contract by `test_repair_loop.py` §4; `Report` drops any other and
  says so): football's Track Record findings had named `record`, a no-op under football.
  The football ungraded-card alarm fires only while a row is still OWED a grade
  (record_fb's `owed`: every unresolved state but `SETTLED_UNRESOLVED`, the player-side
  ones, an exclusion list), never on a card whose rows are graded as they will stay; a
  final game the log does not hold stays owed.
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
                  `[Sam, 2026-10-26]` injury-check, football: the game-day
                  injury check (`collect_injury_check`, 9am/12pm/7pm ET),
                  planned by converge, card-fb after it (no cron).
card.py           the v4.0 model -> picks/<date>.json. Calls nothing.
winners.py        THE GAME LINES TAB, ALL THREE LEAGUES (Sam, 2026-10-01):
                  the model's pick to win each slate game, the best
                  moneyline at the league's books; frozen at the start
                  (daystore), graded once, ONE record per league ->
                  winners.json; verify_record.py re-grades it. Rides the
                  MLB card / record runs and football's `card-fb`.
                  `[2026-10-23]` A VOID gives way to a later real grade
                  (`superseded`): 849817 was postponed 10-16, graded void,
                  played 10-18 under the same id. ⛔ A real grade is never
                  replaced. verify_record reads the box scores oldest first
                  and re-checks the grade that stands.
                  `test_winners_postponed.py`. `[2026-10-23]` Stamps
                  `grader` (its grading code), so a grading change is
                  rebuilt before verify_record checks it.
mlb_game_model.py THE MLB GAME MODEL (Sam, 2026-10-02): each side's runs
                  from the opposing starter (start logs), its bullpen (scores
                  minus starters), the side's usual nine (hitter logs), park
                  and home field; negative-binomial runs -> win, run-line and
                  total chances. Starters from the schedule saved BEFORE first
                  pitch; ⛔ nothing dated at or after first pitch is read (no
                  stored file holds a posted lineup, so `confirmed` is false).
                  Built in the card run (free) -> data/latest/mlb-game-model.json
                  with its walk-forward check, AND `[Sam, 2026-10-06]` on its
                  own contract row (`game-model`, free): when missing and at
                  the Odds deadlines, on game days, for the next slate, then
                  MLB winners.json. ⛔ That build never builds the card. The total carries C2's
                  correction in the file only (~~run line and total~~):
                  `[2026-10-03]` the run line's fit weighted the model's own
                  chance NEGATIVELY (the books' number tilted against it), so
                  it is MEASURED in the check and never applied. ⛔ Totals
                  never reach the card (see MLB GAME LINES below).
budget.py         projected Odds API spend, derived from the deployed
                  cron schedule and market lists. Run it after ANY change
                  to the schedule or the markets.
verify_record.py  re-grades EVERY published pick from the stored box
                  scores a second way and reconciles record.json against
                  it -- totals, per day, per kind, the internal sums, and
                  the drill-down detail. ⛔ Voids stay out of every
                  denominator. Runs on the record and refresh jobs.
                  `[2026-09-25]` A record.json whose `grader` stamp is
                  not the collect.py beside it is REBUILT first (it
                  runs `collect.py record converge-off`), so a grading-rule
                  change cannot turn runs red; a current-stamped record
                  that disagrees still fails.
                  `[2026-10-23]` Each league's winners.json too: a `grader`
                  stamp that is not the winners.py beside it is rebuilt
                  first (`winners.py`, LEAGUE=<lg>, free), then checked.
                  #310's grading change sat red on collect 40040807226
                  until a mode rebuilt the file. `test_winners_grader.py`.
                  `[Sam, 2026-10-01]` ONE named exception, `DH_EXCEPTION`:
                  the three 9/25 doubleheader picks count as published
                  (29/45 stays). ⛔ Never widen it; the graders cannot
                  tell doubleheader games apart (open, next season).
record_grader.py  the fingerprint of the MLB grading code: collect_record
                  and every top-level name it reaches, parsed with ast,
                  comments ignored. collect.py stamps it, verify_record
                  compares it. ⛔ Parsed, never imported.
                  `[2026-10-23]` Also the winners' grading (`winners.graded`,
                  `winners_fingerprint`), FOLLOWED into the other modules it
                  reads (collect.VOID_STATES, fb_ledger, daystore); a module
                  it reaches that it cannot find raises, never "matches".
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
                  `[Sam, 2026-10-12]` T65's college data: ppa-<season>
                  (per offence per game, from the /plays sweep it already
                  makes; 2025 swept once while missing) and talent-<season>
                  (CFBD /talent once a season; a refusal writes a DIAGNOSTIC
                  talent-probe and never raises). test_cfb_ppa.py.
                  `[Sam, 2026-10-17]` also roster-<season> (jerseys) and
                  defense-<season> (tackles, sacks, ...), from the calls it
                  already makes; 2025 once while missing. test_cfb_defense.py.
cfb_injuries.py   COLLEGE INJURIES (Sam, 2026-10-17): the conference
                  availability reports (HD Intelligence: SEC, ACC, Big Ten,
                  Big 12, MAC; Sun Belt; Pac-12), checked (one game, known
                  teams and statuses) and dated (current = published <=36h
                  before kickoff, snapshot <=6h old), stored by the
                  `cfb-injuries` mode; `report_for` (the why), `attach` (the
                  model, only once its test passes). Stdlib only, never
                  raises. Design: research/cfb_injuries_design.md.
                  `[Sam, 2026-10-26]` `read_cut`: a game still to start at a
                  build reads the newest report as of it ("do 9am, 12pm,
                  7pm", design §5); started games and `now` None keep §3.
                  `[2026-10-26, review]` `attach(shown_at=)`: a played game
                  also gets `inj_shown`, as its last pre-kickoff build read
                  it, for the record's replay only. `[2026-10-27, review 2]`
                  at `shown_cut` (the build's own moment, never a later
                  cut); the archive and role files as stored now.
fb_inj_backtest.py THE INJURY TEST'S RUNNER, both leagues: the bar fixed
                  before it ran (fb_sim_design.md §3, cfb_injuries_design.md
                  §4), recorded ONCE in research/fb_sim_backtest.json; `auto`
                  runs it by itself in the Monday fb-refit job and pushes one
                  fb/injuries-<lg>-* branch. test_fb_inj_backtest.py.
nfl.py            NFL ingestion from nflverse. STDLIB ONLY.
                  `[2026-10-26]` `store_injuries(only_on_change=True)`, the
                  check's call, skips an unchanged rewrite (nfl-logs' daily
                  call always rewrites); `check_injuries`: the game-day injury check's
                  NFL half (the week's statuses + roster_weekly INA inactives,
                  a daystore snapshot only on a change, STORED ONLY).
record_fb.py      the football grader -> data/<lg>/latest/record.json
                  `[Sam, 2026-10-17]` also the game lines every card showed
                  (`grade_game_lines`) and the Board (props + game lines).
                  `[2026-10-27]` A card's log is its football season's
                  (`fb_why.season_of`), never its calendar year's.
dossier_fb.py     Sam's eight per-game checks, every board game.
                  ⛔ Combines nothing, ranks nothing, scores nothing.
fb_model.py       THE FOOTBALL PICK MODEL (Sam, 2026-09-23): ridge
                  logistic per league x market on signals 1-8, walk-
                  forward weekly, graded ONLY at Hard Rock / FanDuel /
                  DraftKings prices archived before kickoff. Rides
                  `card-fb`; ~~its own model section on the page (no
                  chip since 2026-10-01)~~ `[Sam, 2026-10-17]` no section on
                  the page (Gizmo's Picks is as simple as MLB's). `[2026-10-01]` `win_chances`:
                  both teams' chance for every priced game, the Game
                  Lines tab's input (winners.py). ⛔ Never
                  touches the card. Design: research/fb_model_design.md.
                  `[Sam, 2026-10-11]` Its fits read the model's OWN team
                  ratings (`own_ratings`), never the books' line or chance.
                  ⛔ Its SECOND record (closing lines, college at an
                  assumed -110, labelled) is kept apart from the headline
                  and shown under it, never mixed in [Sam, 2026-09-23].
                  ⚠️ `[2026-10-16]` A spread pick's `line` is M, the
                  threshold on the HOME margin (= -home point), so a HOME
                  pick's own point is -M. ~~The page prints every model
                  line through `fbPointText` (Cleveland +3.5 had shown
                  "-3.5")~~ `[2026-10-17]` the page prints no model line;
                  `test_fb_line_sign.py` fails if one returns.
                  `[Sam, 2026-10-26]` `above_average`: who it rates above
                  average at each Game Lines game's Monday, for the why only.
                  `[2026-10-26, review]` `as_shown`: the record's replay reads
                  a played college game's `inj_shown` (the report its last
                  pre-kickoff build read); every fit trains on `inj` (§3).
                  `[2026-10-27, review 2]` `read_at`: when the rows read the
                  injury reports (the build's `now`); the ledger dates the
                  replay by it.
fb_props_model.py THE FOOTBALL PROPS MODEL (Sam, 2026-09-24): each player's
                  stat distribution from the stored logs 2021-26, the
                  market line folded in from EARLIER priced weeks only,
                  walk-forward at the three books' prices, and scored
                  against the props card's OWN recomputed probabilities.
                  Rides `card-fb`. ~~⛔ Never touches the card; the switch
                  is Sam's.~~ `[Sam, 2026-10-09]` Sets the card's
                  confidence where it prices a prop; built first in
                  `build_card_fb`, from the props board. `[Sam, 2026-10-11]`
                  Its stage 2 takes no price. Design:
                  research/fb_props_design.md.
fb_card_calibration.py  the football props card's stated-vs-actual bands
                  and Sam's pre-registered calibration test
                  (`research/fb_card_calibration_spec.md`, frozen).
                  ⛔ Never changes what the card prints; a QUALIFIES
                  waits for Sam. Rides `card-fb`. `[Sam, 2026-10-01]`
                  Not shown on the page, nor either league's "Read the
                  confidence number honestly" note; still built and
                  scored.
fb_card_fix.py    scores the football props card's season fix (reads 2026
                  first, 2025 as the start, shrunk toward the position
                  average) against the card as it was, by Sam's ship rule
                  in `research/fb_card_fix_spec.md` (frozen). The live
                  switch is `card_fb.CARD_METHOD`.
fb_ledger.py      "What the model showed, graded": both football models'
                  picks saved before kickoff via daystore, graded ONCE
                  and frozen, ~~listed pick by pick~~ (`[Sam, 2026-10-17]`
                  not on the page any more); the verdict label per
                  market (fb_model.verdict) beside every record
                  (`research/fb_model_live_spec.md`, frozen). Rides
                  `card-fb`. ⛔ Never recalculates a graded pick.
                  `[Sam, 2026-10-16]` spec §3a: a pick the model withdrew
                  before kickoff is NOT graded. Each snapshot lists the
                  games each model looked at (`looked_at`), and the last
                  snapshot before kickoff that looked at a game decides,
                  even with no pick (~~kept "unless the game had no pick in
                  any later snapshot"~~). `test_fb_ledger_withdrawn.py`.
                  `[2026-10-26, review]` That rule is ONE function, `chosen`;
                  `looked_moments` dates each game's last pre-kickoff build
                  from it for the game model's record (reads only).
                  `[2026-10-27, review 2]` A snapshot keeps fb-model.json's
                  `read_at` (`model_read_at`); `looked_moments` returns it
                  (`taken_at` without one, never a moment after it).
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
fb_challengers.py T65's frozen challengers to the football game model
                  (Sam, 2026-10-12): E (NFL opponent-adjusted EPA margin), P
                  (college PPA, the same solve), T (college talent in the
                  margin solve); T66 adds S (NFL, fewer inputs) and TS (college,
                  talent, few inputs); T68 AV/AVC, WX/WXC; T69 IN (NFL injuries both
                  sides), AT/ATC, RS/RSC; T70 H/HC; `[2026-10-16]` T71 SM/SMC (the
                  score-first model's margin and total, the only input);
                  `[Sam, 2026-10-26]` T72 CL/CLC (class vs above-average teams),
                  WL/WLC (win-loss resume), MC/MCC (blowouts capped), AJ/AJC (form
                  and defence opponent-adjusted). fb_model reads it only for a
                  named CHAMPION.
fb_refit.py       T65 weekly (staged fb-refit.yml): champion vs challengers,
                  the scoreboard against the books -> data/<lg>/latest/
                  fb-refit.json; a WINS pushes one fb/champion-* branch. ⛔ No
                  PR, never main. status.py and the watchdog never import it.
                  `[2026-10-17]` also the injury test, once (fb_inj_backtest.auto),
                  through the one branch pusher, `push_change`.
                  `[R1, 2026-10-18]` while CHAMPION is set, a WINS pushes no
                  branch (NEEDS SAM); each league's `elapsed_seconds` is stored.
                  `[Sam, 2026-10-26]` T73 (§3g): the verdict reads `counted`
                  (every 2025-2026 week, or only scored weeks for SCORED_ONLY);
                  several WINS -> one branch, `branch_order`; `floor` stored.
fb_history.py     T70's OLDER SEASONS (Sam, 2026-10-15): NFL 2018-2024 schedules
                  (nflverse, free; OAK stored as LV) and college 2023-2024 schedules
                  + lines (CFBD, priced) -> data/<lg>/history/, once while missing, by
                  `nfl-logs` / `cfb-probe`. ⛔ Never in latest/; never raises.
                  `[2026-10-27]` Every file is stamped (`written_at`); an unstamped
                  stored one is stamped in place once, its games untouched.
fb_weather.py     NWS KICKOFF FORECASTS, STORED ONLY (Sam, 2026-10-14): NFL
                  and FBS-vs-FBS college games within 7 days at outdoor US
                  venues -> data/<lg>/latest/weather-<season>.json.gz ("first"
                  never overwritten, "last" only before kickoff). Rides
                  `nfl-logs` / `cfb-probe`. ⛔ No model reads it yet; never raises.
fb_matchups.py    THE SHARED TEAM-UNIT TABLES (Sam, 2026-10-15): points,
                  pass / rush / receiving yards by position, plays, NFL
                  targets, FOR and ALLOWED per team and Monday, opponent-
                  adjusted by fb_model.solve_ratings (reused). ⛔ Games
                  before the Monday only. The props model's weaknesses.
fb_sim.py         THE GAME SIMULATION (Sam, 2026-10-17): every NFL and college
                  game played out 10,000 times, possession by possession (TD,
                  FG, nothing; the last drive played to the score; overtime),
                  from the model's own predicted score and spread of results,
                  with each margin's share corrected to the stored final
                  scores (`MARGIN_FIX`). Stdlib only, seeded per game. Every
                  game's runs are in fb-model.json `win_chances[].sim` and the
                  Game Lines tab ("Wins in 10,000 sims"). ⛔ It sets no chance
                  while `fb_model.SIM` is off: its backtest failed the bar
                  fixed before the run (research/fb_sim_design.md §3-§4,
                  research/fb_sim_backtest.json); so did NFL injuries
                  (`fb_model.INJURIES`). test_fb_sim.py.
fb_score_model.py THE SCORE-FIRST GAME MODEL, ⛔ REPORT ONLY (Sam,
                  2026-10-15): both teams' points + a measured home edge + a
                  pass / rush / pace layer, chances from the score curve;
                  backtest -> data/<lg>/latest/fb-score-model.json after the
                  card in `card-fb`. ⛔ Nothing reads it; the switch is Sam's.
                  Design: research/fb_score_model_design.md.
fb_why.py         THE WHY UNDER EACH FOOTBALL GIZMO'S PICKS PICK (Sam,
                  2026-10-15): reader sentences from the stored logs,
                  opponent tables, injury reports, schedule and
                  fb-model.json, on the liked lists only. ⛔ Changes no
                  pick, chance, rank or price; never raises.
                  `[2026-10-27]` Also the ONE date-to-season rule (`season_of`)
                  and THIS game's week (`game_week`, read by the news flags).
game_lines_fb.py  THE ALT LADDERS (~~THE GAME LINES TAB~~: `[Sam, 2026-10-01]`
                  no longer drawn; the tab is winners.py, and the card's
                  alternate spreads still read this file) (Sam, 2026-09-24): every alt spread
                  and total Hard Rock / FanDuel / DraftKings post for the
                  slate, each rung's price per book, best, break-even,
                  the game model's % and edge; frozen before kickoff
                  (daystore), graded once, its own record; alt-only
                  parlays through card_fb.build_parlays_fb's rules,
                  built and RANKED ON THE BOOKS' OWN CHANCE (stored
                  basis MARKET; no chip, box or ⚠ on the page since
                  2026-10-01) (de-vigged
                  per book, MARKET) — ⛔ never the model's % [Sam,
                  2026-09-25: the check failed; NFL points the wrong way].
                  ⛔ Never touches the card. Data: the paid `alt-lines`
                  pull in collect.py (one pull per game, capped at
                  1,500 credits a month, bill measured per call).
fb_agreement.py   card vs props model (Sam, 2026-09-25): every card row and
                  props-model pick labelled AGREE / SPLIT / ONE SOURCE
                  against its break-even, frozen per card run, graded
                  once, its own record; scores the pre-registered
                  question in research/fb_agreement_spec.md (frozen).
                  ⛔ ~~A note on the row~~ Not printed on the row since
                  2026-10-01 (still labelled, frozen and graded; ~~the
                  record table stays~~ `[Sam, 2026-10-17]` the record table
                  left the page too) — changes no pick, rank or price.
                  `[Sam, 2026-10-09]` Where the model set a row's
                  confidence, the card's side is the row's record (`rate`).
news_flags_fb.py  the free news-flag reviewer (Sam, 2026-09-25): once a
                  day on the news run, NFL injury-report status (the
                  injury rows nfl.py stores for signal 7) and stored
                  headlines naming a board player/team with a status
                  word. Exact full names only. ⛔ FLAGS, NEVER PICKS:
                  hides, re-ranks, re-prices nothing; feeds no model.
                  College is headlines only (~~no injury reports~~ `[Sam, 2026-10-17]` the conference reports are read by cfb_injuries, not here).
                  `[Sam, 2026-10-01]` Not printed on board rows or
                  parlay legs; the file and its record are still kept.
                  `[2026-10-27]` A game's week is its own schedule row
                  (`fb_why.game_week`): ~~`signal9.week_of`~~ lost January
                  and read Monday night as the next week.
fb_alt_lines.py   the pre-registered check (research/fb_alt_lines_spec.md,
                  frozen): is the game model calibrated 3/7/10 points off
                  the main line? ⛔ Decides the tab's LABEL (stored in
                  game-lines.json; no box or ⚠ on the page since
                  2026-10-01), never whether a number shows. Called by fb_model.build on its rows.
liveprobe.py      can the football scores tab ever be live?
verify_nfl.py     the football data-layer verifier

CONTRACT AND SPEND
freshness.py      THE FRESHNESS CONTRACT — what must be how current.
                  `converge` plans its work from this, not from crons.
                  `[2026-09-26]` `classify` is the gate's one hard/soft
                  verdict; `judge_failures` decides whether a failed
                  converge mode turns the run red (see FAIL LOUD above).
                  `[2026-10-24]` `pull_owed`: the props stand-down judged
                  by the contract's own survey, on its own row (`props_rows`).
                  `after_last_survey`: a deadline that passed after the
                  league's last survey is the next pass's (10-19's 1.9 s).
                  `[Sam, 2026-10-26]` the `injury-check` row: `INJURY_CHECK_ET`
                  (9:00/12:00/19:00), `injury_check_slots` (real Eastern time,
                  `et_wall_utc`, game days only), a `Moments` deadline (real
                  UTC moments; every other row keeps its ET tuples), CASCADE
                  to card-fb, SOFT, `UNTIMED` (not in lateness.json);
                  ~~`ON_CHANGE`: a file rewritten only on a change has no clock
                  deadline~~ (withdrawn in review: it weakened a check);
                  `[2026-10-26, review]` one retry (`INJURY_RETRIES`), the NFL
                  probe's `health` (`INJURY_FAILED_SLOTS`, never replanned:
                  `REPORT_ONLY_HEALTH`), `injury_check_history` (the weekly).
                  `[2026-10-27, review 2]` the retry is PLANNED
                  (`injury_retry`, like `slate_moves`), never a deadline;
                  `health` also judges both leagues' slot logs (the last 2
                  slots read nothing, any cause).
                  ⛔ It imports no other repo module (sandboxes copy it alone):
                  the US DST rule `_us_eastern_offset` lives here, fb_weather
                  reads it from here `[2026-10-26]`.
                  `[2026-10-27]` ✅ Every other deadline stays at a FIXED UTC-4
                  all year, on purpose: it is the minute its cron fires, and a
                  GitHub cron is UTC. From 11-01 each is the same UTC minute, an
                  hour earlier by the wall clock (the card's "10:00" is 9:00
                  EST). ⛔ Moving them means moving the crons (Sam's upload).
                  The page reads Eastern time by the zone everywhere
                  (`etWallDate`, `fbStartDate`, `fbEspnDay`); a fixed offset on
                  the page, or a new one in the Python not named with its reason,
                  fails `test_et_clock_change.py`.
verify_freshness.py  fails the run when the site is not current.
                  `[Sam, 2026-10-01]` The page shows no stale-data bar
                  and no "out of date" note; staleness reaches Sam
                  through this, the watchdog, health.json and the issue.
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
credits.py        THE CREDIT BALANCE CHAIN: the one reader of stored
                  `credits_remaining` readings and the one rule for the
                  newest (by minute, then the LOWER balance). Read by
                  collect.py (the daily room) and watchdog.py. The paid
                  kinds come from ONE registry, `collect.PAID_KINDS`.
                  `[2026-10-23]` Also the QUOTA PERIODS (`periods`): a rise
                  in the balance starts one (the 1st, or a plan bought again
                  mid-month, as on 10-23); the watchdog reconciles inside
                  each, never across one.
calibration.py    is the product still winning? the automatic answer.
relay.py          THE RELAY (Sam, 2026-10-06): at the end of an MLB run's
                  hold, may it dispatch one successor? ⛔ Not while another
                  MLB run is queued or running, past 5 links a UTC day, on a
                  re-run, or when no MLB card is owed for the last or the
                  next card deadline's day. Run by
                  collect.yml's last step; exit 0 = dispatch.
status.py         THE WEEKLY STATUS EMAIL (Sam, 2026-10-07): one issue, updated
                  and commented each Monday, and any day the health check is
                  too old (status.yml, daily), from the repo's own files.
                  ⛔ A report, never a task (`self_repair.COUNTER`).
                  `[2026-10-26]` an injury branch whose entry main already
                  holds is no longer "Needs you" (`injury_recorded`); the
                  game-day injury checks that ran, failed or never ran
                  (`injury_checks`).
card_gate.py      did the card fail for a reason Sam already accepted?
                  ⚠️ `[2026-10-01]` the page no longer says a card was
                  published past an accepted check (the stale bar went).

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
tcheck.py         the one check harness every test file uses.
                  `[2026-09-26]` It watches every line a test prints:
                  one GitHub reads as a workflow command (`::error::`)
                  is written defused and FAILS the file. Print captured
                  output through `shown()`; annotate on purpose only
                  with `annotate()` (test_workflow_commands.py).
ranking.py        the one tie-aware ranker, both leagues
teamkeys.py       THE ONE TEAM-NAME RESOLVER `[2026-10-27, review 2]`: a book's team
                  name -> the key the league's files use (NFL_TEAMS parsed out of
                  collect.py; college teams.json, folded, longest prefix, three
                  aliases), moved unchanged out of dossier_fb.py, which re-exports
                  it. The card reads it (`card_fb.match_player`) and so never
                  reaches the dossier (`test_dossier_fb.py` §3). ⛔ Never a guess.
one_side.py       ONE TEAM PER GAME (Sam, 2026-10-16): the expected winner
                  (the Game Lines tab's rule, read by winners.py), the filter
                  every list of side picks runs, and the guard verify_card.py
                  runs. ⛔ Only removes; stdlib only. `[Sam, 2026-10-17]` also
                  `shown_score`: whole-number scores that never contradict a pick.
wfparse.py        the one HAND parser for a workflow file -- jobs,
                  steps, `run:` bodies and `permissions:` blocks.
                  ⛔ Never `import yaml`: PyYAML is NOT on the CI
                  runner (measured 2026-09-19) and a test that cannot
                  import blocks a push. Cross-checked against PyYAML
                  in test_wfparse.py wherever PyYAML happens to exist.
wfroutes.py       the one parser for the workflow's routing table
jsblock.py        the one reader for a function's body in index.html
self_repair.py    self-repair triage: which watcher issue the repair agent
                  gets, and whether it is started at all. ⛔ An issue whose
                  watcher marks it a counter (`COUNTER`, e.g. T58/T59's
                  progress) or not agent-repairable (`NOT_REPAIRABLE`: the
                  runs watcher's late crons, the calibration monitor) is
                  never a task. `[2026-09-28]` After two passes in a row
                  that end at the turn cap or open no PR it STANDS DOWN
                  until a PR merges to main or a new watcher issue opens (#55-#62:
                  8 of 8 at the turn cap). Read by self-repair.yml's
                  triage and record steps.
runs_report.py    did any workflow run fail? `[2026-09-25]` also writes
                  data/latest/runs.json (`collect.py runs`, hourly from
                  runs.yml's own `publish` job): the last 48h of every
                  workflow, and each failure's step and annotations.
daystore.py       the one dated, write-once archive writer. ⛔ Never
                  cumulative (rule 285: git cannot delta-compress a
                  gzip, 560x) and never into `picks/`.
push_retry.sh     the ONE way a workflow lands its commits: rebase
                  favouring this run's files, abort + replay on a
                  conflict, exit 1 after 5 tries. ⛔ Never hand-roll a
                  pull/push loop again — a half-done rebase lost whole
                  converge passes (and paid pulls) 09-15 → 09-21.
                  `[2026-10-23]` A PAID snapshot the remote already holds
                  under the same name keeps it; this run's copy lands
                  beside it as `HHMM-n` (`credits.keep_both`): two runs
                  buying the same minute lost a receipt three times
                  (08-23, 10-11, 10-23: 221 credits off the record).
                  test_push_retry.py §4.
mlb_refit.py      MLB champion vs challenger, as Sam approved it on
                  2026-09-23 in `research/mlb_refit_spec.md`: v5.0
                  (READ from card.py) against the same model re-fitted
                  each week on earlier games only, scored by log loss.
                  ⛔ Changes no coefficient; when the challenger
                  qualifies it opens ONE "[ASK SAM]" PR. Stdlib only.
mlb_tables.py     the MLB pitcher + opponent tables, rebuilt after every
                  `pitchers` pull from the FULL starter population.
                  ⛔ card.py reads `model_pitchers()`, never the widened
                  pool, so the card's ~~numbers~~ PROP numbers do not move.
                  `[2026-10-09]` Its game lines come from mlb_game_model,
                  which counts every start by design (test_mlb_tables.py).
mlb_pitcher_cal.py  audit C/D, scored to `research/mlb_pitcher_cal_spec.md`
                  (frozen). ~~C2 shipped `[2026-09-25]`: a pitcher row
                  PRINTS its blend mixed with its price~~ `[Sam, 2026-10-11]`
                  C1 ships: the blend corrected by its own past misses, no
                  price, refitted each card on earlier graded rows. ⛔ `blend` is unchanged;
                  card.py reads `mappings()`/`corrected()` from here and
                  never imports `fb_model` (it drags in card_fb, which
                  exits under LEAGUE=mlb). Off switch: `SHIPPED = None`.
vacuity.py        does each guard actually bite? `VACUITY_PART=k/n`
                  sweeps one share (pr-tests' parallel parts, never a
                  sample: test_pr_shards.py). ⛔ It MUTATES SOURCE
                  FILES while it runs — never edit the repo during a
                  sweep, and never run two at once. `[2026-09-26]` A
                  RED run stops at the first failed check
                  (`TCHECK_FAIL_FAST`); the green-on-revert run is
                  always a full run (test_fail_fast.py).
```

⚠️ **THAT LIST IS CHECKED, NOT MAINTAINED BY HOPE.** `test_claude_md_map.py`
fails if a top-level module exists and is not named here. ⛔ If it fails
because you added a module, add the line — the list going stale is how a
fresh session ends up writing a second copy of something.

The reasoning behind all of it — the model, the ledger, the pre-registered
tests — lives in Sam's Claude project docs, not in this repo. **If a change
needs that context and you do not have it, say so instead of inferring.**
