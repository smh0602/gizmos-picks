# PLAN — signals 1–8, and the backtest

**Rewritten 2026-09-18 06:55Z, when Phase A's buildable work finished.**
The earlier version was a build list; that list is done, so this is now a
record of what shipped and a watch-list for what the calendar owes us.
Every state below was measured on `origin/main`, not recalled.

---

## 🆕 STATE AT 2026-09-22 — read this first

**All eight signals are live on the page, in both leagues, labelled DESCRIPTIVE.** `[measured on main 2026-09-22]`

| § | NFL (17 games) | CFB (58 games) |
|---|---|---|
| 1 Market | OK 17 | OK 58 |
| 2 Head to head | OK 5 · UNAVAILABLE 12 | OK 15 · UNAVAILABLE 43 |
| 3 Time of year | OK 17 | OK 56 · UNAVAILABLE 2 |
| 4 This season | OK 17 | OK 58 |
| 5 Versus position | OK 17 | OK 58 |
| 6 Possession | **OK 17** | **OK 58** |
| 7 Personnel | OK 17 | OK 58 |
| 8 Venue | OK 17 | OK 58 |

✅ **§6 is live in both leagues** — NFL `top-2026.json.gz` first existed 2026-09-20 08:53Z, CFB 07:02Z; `possession_validated()` True for both. The H2H refusals are teams with no recent meeting.

⛔ **The model is NOT live, by design.** T60 is **NOT YET MEASURABLE**: effective n **733 (NFL, 1,168 eligible rows)** and **1,157 (CFB, 1,777)** against the pre-registered floor of **2,774**. It grows by itself as games are graded; nothing is manual. No hit rate is quoted before the floor is met.

🔴 **DECIDED BY SAM 2026-09-22: T60 COUNTS ITS ROWS AS WRITTEN.** The question was whether the 1,777 college rows — all described before §6 validated, so each carries §6 UNAVAILABLE — should be excluded. Claude recommended excluding them (see the 📌 paragraph below, which says rows before §6 passes are VOID). **Sam chose to keep the pre-registered test exactly as specified**, which gates on when a row was GRADED after validation, not on what its own §6 said. ⚠️ **Consequence, stated so it cannot be forgotten at readout: most college rows in a T60 pass will not have contained signal 6 in their write-up, so a CFB pass is weaker evidence about §6 specifically than about the dossier as a whole.** Report that sentence alongside any T60 verdict.

## 🔴 2026-09-22 FINDING — T60 AS WRITTEN CANNOT PASS, AND THE CARD DOES NOT READ THE DOSSIER

**Found while answering Sam's backtest request. Not a data look — no signal-by-outcome number was computed.**

1. ⛔ **T60 grades BOTH sides of every priced line at the best price.** A game's over and under (or both spreads) are one row each, so the pooled hit rate is pinned near 50% before any signal is involved, and a little below it once the vig is paid. **It cannot reach the 55.4% bar.** When it reaches its n floor it will read FAIL, and that FAIL will say nothing about signals 1–8. ➡️ **This is a design defect in the test, not a result.** The pre-registration is NOT re-decided here (owed-tests rule); it is flagged for Sam.
2. ⛔ **`card_fb.py` never reads the dossier.** The eight signals are shown next to the picks; they do not choose them. So "bets based on 1–8" is **not built**. This was already true (📌 section below); it is restated because Sam's request assumes otherwise.
3. ✅ **The dossier IS current.** It rebuilds on every card-fb run from current logs: NFL logs Tuesday noon, CFB 3am daily, possession 3am daily. "Keeping up with this season" already happens for the DESCRIPTIVE panel.

### T60R — the played-games backtest Sam asked for (PROPOSED, NOT RUN, NEEDS SAM)

Sam, 2026-09-22: *"the backtest should be for only the games that have been played, we can do this for thr 2025 year too… after every football game/week our model should be applying the 1-8 rules to all the new games."*

| | |
|---|---|
| Scope | NFL 2025 + 2026 to date, FBS 2025 + 2026 to date. **Game spreads and totals only.** |
| Prices | NFL: nflverse closing lines with juice (285/285 games priced in 2025). CFB: CFBD `/lines`, ~20–25 calls. |
| Not possible | **Props.** No stored 2025 prop prices; historical odds would cost ~34k–110k credits. |
| Lookahead filters | H2H `when < kick`; §4 date cut; §5 rebuilt per game; §7 one-week lag; §8 weather blank. |
| ⛔ Before any data is looked at | **A DIRECTION RULE must be pre-registered**: for each game, which ONE side the signals pick. It should be drafted by someone who has not seen signal-by-outcome data, and Sam approves it and the bar. |
| ⛔ Never | Pooled with T60. |

➡️ **Weekly refresh is the natural extension:** once the direction rule exists, the same code grades each new week as it finishes. That is automatic (a cron), never manual.

## ✅ PHASE A IS COMPLETE. Nothing buildable remains.

| PR | what shipped |
|---|---|
| **#38 #39** | the eight-section dossier, NFL · the T54 counter reaching a cron at last |
| **#40** | possession as a **share**, one implementation both leagues, floor from an error bound |
| **#45 #51** | two self-invalidating tests: they asserted an artifact's absence, and the fix created it |
| **#49** | **the dossier ported to college** — it had refused every league but NFL, silently, with `return 0` |
| **#53 #55** | the panel on the page, joined on `board_id` · the moneyline label |
| **#57 #62 #64 #68** | the shadow record · the self-disproving artifact annotated · two vacuous guards of our own |
| **#59** | §3 and §8 college — **venue 19 refusing → 2, week 21 → 5** |
| **#61** | the `/coaches` probe |
| **#65** | **`totals_h1`**, one market, one region |
| **#67** | §5 shows the declared four |

### Section state, both leagues, on current `main`

| § | signal | NFL 32 | CFB 90 | |
|---|---|---|---|---|
| 1 | Market | OK 32 | OK 90 | ✅ + first-half total. ⛔ 1H moneyline still a declared gap |
| 2 | Head to head | OK 13 | OK 15 | ✅ the refusals are correct |
| 3 | Time of year | OK 32 | OK 85 | ✅ |
| 4 | This season | OK 32 | OK 90 | ✅ |
| 5 | Versus position | OK 32 | OK 74 | ✅ QB/RB/WR/TE declared. ⚠️ moves nothing, by design |
| 6 | Possession | fills 07:14Z | ~~**~week 4**~~ | ~~🔴 the only calendar gate~~ 🔴 **`[2026-09-21 sweep]` NOT A CALENDAR GATE — `claude/possession-validation.md` (2026-09-19) found the binding constraint is CFBD play ORDERING, not coverage. Read that doc for the current state.** |
| 7 | Personnel | OK 32 | OK 90 | ⚠️ players yes, coaches a declared gap |
| 8 | Venue | OK 32 | OK 88 | ✅ |

---

## THE THREE DECISIONS — all answered 2026-09-18

**A2 · college §6 floor** → ~~lower it~~ **SHIP THE REFUSAL.**
`COVERAGE_MIN` stays **0.90**, now a decision on the record rather than an
omission. ⛔ No override, no provisional mode. A safety floor does not move
to meet a deadline.

**A3 · first-half markets** → **`totals_h1` only.** One market, one region
(`us2`, where Hard Rock lives), guarded so `us` or `us,us2` goes RED.
⛔ `team_totals_h1` not built — 6 books against `totals_h1`'s 15.
**§1 says plainly there is no best-price shopping on it.**

**A5 · per-position ranks** → **QB, RB, WR, TE.** A fixed four, declared as
`VS_POSITIONS`, not a sort — which sidesteps the judgement `audit()` exists
to refuse.

---

## 🔴 WHAT THE WORK TAUGHT US, AND IT IS MOSTLY ABOUT TRUSTING OUR OWN OUTPUT

**1. Our own error strings are queries too.** I read §8's *"the schedule
has no row for this game yet"* as a fact about the schedule. **17 of those
19 games were in `schedule-2026.json.gz` all along**, with week, venue,
roof and surface. The pair key was built from resolved codes on both sides
and an FCS away team resolves to `None`, so `(home, None, date)` never
matched. ➡️ *A fact about a query is not a fact about the world* — **and
the query can be ours.**

**2. A guard tested more harshly than it was declared looks sound.** The
strike check asserted `"~~" in verdict`; the declared mutation removed only
the opening marker, leaving a withdrawn claim reading as current. The
original drive had removed *all* markers — stronger than declared — so it
passed. **Only the sweep caught it.**

**3. A test whose precondition is "this artifact does not exist" dies the
day its feature starts working.** Shipped twice in one day, two files, two
authors.

**4. A design effect can be LESS than one.** The board prices both sides,
so each game's rate is pinned and the variance route returned **10,562
effective observations on 1,245 rows**. The brief guarded the opposite
direction. ➡️ **A variance-based effective n needs a combinatorial
ceiling**: a complementary pair resolves once.

**5. The column the name promises is not the column the value is keyed to.**
`fixed_drive` looked authoritative; `drive_time_of_possession` is keyed to
`drive`. The wrong one weakened an exact identity (269/269 at 3600) into a
92% rate bar. **The conserved quantity settled it instantly.**

**6. A written-down plan size is a claim about the world, and it goes
stale.** `cfbd_budget.py` prices against `PLAN = 1000` and reads no header.
The live header says **`X-CallLimit-Remaining: 2374`.** `budget.py:23`
hard-codes `PLAN = 20000` the same way — though the Odds *usage* half is
genuinely read and stored.

---

## WHAT IS LEFT, AND ALMOST NONE OF IT IS CODE

| # | item | blocked on |
|---|---|---|
| 1 | ⏰ Friday 12:20Z production verification | nothing — it runs itself |
| 2 | **CFBD account page: which tier are we actually on?** | 🔴 **Sam. Free. 91% may be wrong.** |
| 3 | credit-balance watcher | nothing — see below |
| 4 | §6 college clears the floor | ~~**calendar, ~week 4**~~ **blocked on CFBD play ordering — see `claude/possession-validation.md`** `[2026-09-21 sweep]` |
| 5 | T60 starts counting | #4 |
| 6 | T60 reads out | #5 + ~1 week of slates |

### 🆕 THE ONE GAP WORTH BUILDING WHILE WE WAIT

✅ **`[2026-09-21 sweep]` SUPERSEDED: `watchdog.py` now reads `credits_remaining` (the API's `x-requests-remaining`) back out of the stored snapshots — `test_credit_balance.py`, "THE CREDIT BALANCE WATCHER" — and `budget.yml` runs `budget_watch.py` daily. The paragraph below is the record of the gap as it stood 2026-09-18.** ~~⛔ **NOTHING REPORTS THE ODDS CREDIT BALANCE.**~~ `collect.py:230` reads
`x-requests-remaining` on every pull and stores it; **`watchdog.py` and
`runs_report.py` mention it zero times.** A reserve guard at **750** stops
the spend, so the site degrades rather than dies — ⚠️ **but the first
visible symptom is pulls quietly standing down, which looks like missing
data rather than a quota problem.**

📌 **And the ceiling is 235% of plan** (was 219% before `totals_h1`).
`budget.py` says in its own output that a per-game market spends against
the ceiling, not the measurement. **Measured is 13,710/month, 69%, with
6,290 headroom** — the ceiling assumes every football cron fires on a full
slate every day, which cannot happen. ⛔ But nothing watches the gap
closing.

---

## 📌 WHAT "COMPLETE" STILL DOES NOT MEAN

✅ Eight signals graded, labelled and **visible** on every game on both
boards, refusing where they cannot answer.

⛔ **The signals do not choose bets. `MODEL` count is zero and `audit()`
exits 1 rather than publish a score, rank or confidence.** Picks still come
from the existing card logic.

⛔ **Wiring 1–8 into picks is a THIRD phase that does not exist and must
not start before T60 reads out.** Rows graded before §6 passes in both
leagues are **VOID** — a signal that was wrong when the row was written is
not evidence about the signal.

📅 **Earliest honest T60 readout: early October.** Nothing shortens it but
football being played.

---

## Revision log

- **2026-09-22 (later) — T60 design finding and the T60R proposal added.** T60 grades both sides, so it cannot pass; the card does not use the dossier; the dossier itself is current. T60R (played games, 2025 + 2026, game lines only) is proposed, and waits on Sam's direction rule and bar. T60 itself is unchanged.
- **2026-09-22 — state block added at the top.** All eight sections live in both leagues; T60 not yet measurable; Sam's decision to count T60 rows as written, recorded with its consequence. The 📌 "rows graded before §6 passes are VOID" paragraph is unchanged; the eligibility gate already implements it on the GRADED date.
- **2026-09-18 06:55Z — rewritten. PHASE A COMPLETE.** #67 and #68 merged;
  tasks 31–34 all shipped; all three gates answered. Doc repurposed from a
  build list to a record plus a watch-list. 🆕 Added the credit-balance
  watcher as the one gap worth building during the calendar wait. ⚠️ **My
  "71% of plan" corrected to 37% used at day 17** — that figure was a
  projection quoted as current usage, and it appeared in a work order.
- ~~**2026-09-18 02:55Z** — A4 done (#59), #57 merged.~~ folded in above.
- ~~**2026-09-18 01:00Z** — created as a build list.~~ superseded.
