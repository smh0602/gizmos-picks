# TONIGHT'S FIXES — every finding on `AUDIT-2026-09-19.md`, and nine more

**Nothing is merged. Thirteen branches are pushed, each one its own cause,
each with a guard I drove RED against the real defect and watched go
green on the fix.** Two of them are parked because they touch things you
said not to touch — MLB, and a sort key a check of yours pins.

⛔ **I did not close anything with only the instance repaired**, and I did
not loosen a bar, a tolerance or a floor anywhere. **Two checks in the
fix set were REPLACED** (one more in the parked CFB branch); every
replacement is harder to pass and every argument is made in the commit
and in the PR body, in the open.

---

## 1 · Merge order

Only one ordering rule matters: **merge PR #87
(`fix/self-repair-can-read-the-queue`) first.** It introduces
`wfparse.py`, and four later branches read the workflows with it.
Everything else is independent.

| # | PR | branch | fixes |
|---|---|---|---|
| 1 | **#87** | `fix/self-repair-can-read-the-queue` | **F33** — triage had no `issues:` scope and swallowed the refusal |
| 2 | #88 | `fix/watcher-issues-carry-the-label` | **F34** — 10 `gh issue edit` sites never labelled, so 5 of 6 issues were invisible |
| 3 | #89 | `fix/watchdog-reads-the-key-the-writer-emits` | **F23** — the staleness check read `rows`; the writer emits `artifacts` (+ the guard that fix made vacuous) |
| 4 | #90 | `fix/football-card-frozen-after-kickoff` | **F18** — a published card was rewritten 15h after kickoff |
| 5 | #91 | `fix/nflverse-403-auth-and-backoff` | **F24/F20** — 47 hours of `403 rate limit exceeded` |
| 6 | #92 | `fix/strengthen-the-two-vacuous-guards` | **F11** — issue #69, both guards now BITE |
| 7 | #93 | `fix/watch-label-runs-without-pyyaml` | **F3** — red in CI since it merged: PyYAML is not on the runner |
| 8 | #94 | `fix/both-collect-gates-report` | **F2b** — the first gate skipped the second |
| 9 | #96 | `fix/watchers-stop-claiming-green` | **F35** — three watchers said "every job is green" while CI was red |
| 10 | #97 | `fix/verify-nfl-actually-runs` | **F36** — the football verifier nothing ever ran |
| 11 | **#98** | `fix/vacuity-gets-a-clock-it-can-finish` | **F5** — an 18m16s sweep against a 600s clock |

⚠️ **Merge 5 before 10.** #97 wires in the verifier that reports NFL being
a week behind; #91 is what lets that week land.

✅ **`all-fixes-2026-09-20`** is all eleven merged together, **zero
conflicts**, if you would rather take them as one. Measured on it:

```
full suite       109 files    FAILED: none   TIMEOUT: none
vacuity sweep    1,124s       42/42 checks, tree clean, no leaked worktree
  tier 2         158 of 158   BITES — 0 VACUOUS, 0 MALFORMED, 0 RED_BOTH_WAYS
declarations     158          0 rotted (static pre-flight)
CRON TOTAL       55           unchanged
blind set        56 of 108    ceiling 56 — the ratchet holds
python budget.py              13,710/month of 20,000 (69%), unchanged
```

---

## 2 · The two that need your word, and are NOT in that list

### `mlb/ask-sam-first` — **PR #95, draft.** Two commits, take either, both or neither.

**It does not merge into a green suite, and that is the point.**
`test_calibration.py` §1 goes red on the second commit:

```
🔴 the league list is football only
⛔ ...and no MLB path exists anywhere in the file
   "a disabled MLB branch is one edit away from being a live one.
    The absence is the guard"
```

That guard is yours and it is right — the freeze names *"no scheduled
checks that read MLB state"*. **I did not touch it.** Relaxing a check to
let my own change through is the one thing `CLAUDE.md` forbids above
everything else. If you want this, the argument gets made in that file,
in your name.

| commit | what | measured |
|---|---|---|
| `card.py`: two notes | `hitter_note` says hitter rows carry NO confidence — they have carried one since 2026-08-24. `projection_note` describes the inversion RETIRED 2026-08-27. | false for 26 and 23 days, in the permanent record. Neither is rendered; the page uses the row-level notes, which are correct. |
| `calibration.py`: an MLB arm | the pitcher board is **290/580 = 50.0%** advertising 58–93% | wired in it reads **−14.2 points against a −15.0 bar — it does not even alarm.** ⛔ I did not move the bar. |

### `cfb/ask-sam-first-ordering` — **PR #99, draft.** CFB possession ordering.

Task 44 built counters to measure whether `playNumber` orders a period.
**It does not**, and the counters say so on the live probe:

```
[measured 2026-09-19, 2026 probe, 339 games, 59,462 rows, 1,356 buckets]
  pn_monotonic_game_pct        0.00    <- never, in any game
  pn_monotonic_drive_pct      22.9
  dn_pn_monotonic_game_pct    68.73
  anomaly_pct                 36.339   <- refuses; the bar is 2.0
  dn_pn_anomaly_pct            1.585   <- under the bar
```

`playNumber` is a **drive-local** ordinal, so sorting a whole period by it
interleaves drives and the clock runs backwards. §6 has therefore been
UNAVAILABLE.

⛔ **Your own check said this was your call, not a diff's** —
*"shipping the remedy is Sam's decision"* — so it is parked here rather
than in the fix set. The pin is **not removed**; it now names the new
expression, so the next unannounced re-sort is caught the same way this
one was made deliberate.

✅ **It fails safe.** If the reading is wrong the anomaly stays over the
bar and the derivation refuses exactly as today; it cannot ship a wrong
table. Driven on the committed fixture, offline, no CFBD call:

```
H0 (well ordered)      anomaly 0.506%   usable True
H1 (drive-local pn)    anomaly 33.134%  usable False   <- before
H1 under (dn, pn)      anomaly 0.506%   usable True    <- after
H1 with no driveNumber                  usable False   <- still refuses
```

0.506% is the CONTROL's own rate. The remedy does not merely get under
the bar — it lands on the well-ordered feed's number to the digit.

---

## 3 · Nine things I found that were not on the page

1. **The coverage matrix was certifying the watchdog against a shape
   nobody writes.** `test_watchdog_coverage.py` typed its freshness
   fixture as `{"rows": [{"key": …}]}` — the reader's *mistaken* shape —
   and scored the row CAUGHT while the check had never run. The fixture
   is now built from a real contract. *(#89)*
2. **`verify_nfl.py` was firing on correct code.** Three of its five
   failures were a constancy test read in week 2 of a season —
   `ahead_out` is 0 across ALL of 2025's week-1 rows too. They became a
   third verdict, **NOT YET MEASURABLE**, and a harder question replaced
   them: *do the logs cover every week the schedule calls final?* It is
   red today, for the real reason. *(#97)*
3. **A third "every job is green"**, in `cfbd_watch.py`, split across
   source lines so my grep missed it. The AST scan in the new guard
   found it. *(#96)*
4. **`calibration.py` would have silently misread MLB** — football
   buckets carry `stated`, MLB's carry `predicted`, and
   `b.get("stated") or 0.0` returns **0.0, not None**. The board would
   have read as beating its claim by sixty points. *(#95, parked)*
5. **The `run:`-block extractor existed twice**, byte for byte, in
   `test_multileague.py` and `test_season_default.py` with a different
   `id:` hardcoded in each — rule 117, and the reason the third copy
   went its own way and imported PyYAML. Both now call `wfparse`. *(#87)*
6. **A proximity check pretending to be a relationship.**
   `test_multileague.py` asked whether `exit 1` appeared within 400
   CHARACTERS of a reference. It now binds the `exit 1` to the body of
   the step whose condition reads the verdict. *(#94)*
7. **Three `@vacuity` declarations rotted in one night — mine.** Each was
   broken by a *correct* fix to the file it names: `--add-label` added to
   a line a `find:` quoted, a comment that repeated `issues: read` so the
   literal occurred twice, and a trailing `\` written **doubled** inside a
   Python docstring. ⛔ A `find` that matches zero times mutates nothing,
   so the test passes having been asked nothing — rule 244. Each is fixed
   on the branch that broke it, and **the class is now guarded**: a new
   static pre-flight in `test_vacuity.py` checks every declaration
   resolves to exactly one occurrence, in milliseconds, **before** the
   18-minute sweep. *(#88, #87, #97, guard in #98)*
8. **Fixing the watchdog made a sibling guard VACUOUS — and only the
   sweep could see it.** `test_credit_balance.py` declares a mutation
   that drops the credit reading from the report *when the report has no
   findings*. It turned the file red only because it was measuring a
   LIVE REPO that happened to be finding-free — and the reason it was
   finding-free is the freshness key defect in #89. The moment that was
   fixed, the live tree carried a real DEGRADED row and the mutation
   stopped changing anything. 🔴 **The guard's bite depended on the state
   of production data**; it would have gone vacuous the first time
   anything went stale, with no code change at all. The condition is now
   BUILT — a synthetic tree with `CHECKS` narrowed so the report has zero
   findings by construction — which asks the question every day instead
   of only on clean ones. *(#89)*
9. **The clock fix broke its own guard, loudly.** `test_test_harness.py`
   §4 extracted the runner with *"everything up to the first line that is
   exactly `}`"* — a shape assumption. Adding a second shell helper made
   that brace close the wrong function and §4 ran a shell where
   `run_one` did not exist. Replaced with *"everything up to the
   discovery loop"*, which drives **more** of the step, not less. *(#98)*

**And one thing I reported as a finding and then withdrew:** the NFL card
carrying Sunday's game lines under a Thursday date is **DELIBERATE**
(`card_fb.py:1065-1092`, your 2026-09-14 request — the tab sat empty for
four days between slates). I checked before writing it up.

---

## 4 · What is still broken after all of this

- **NFL is a week behind and will stay so until #91 runs.**
  `players-2026.json.gz` holds week 1; the schedule records finals for
  weeks 1 and 2. #97 makes the job say so out loud — measured just now on
  its branch:

  ```
  python verify_nfl.py --current
  13 passed, 3 not yet measurable, 1 warnings, 1 FAILED
  ::error::2026: the logs cover every week the schedule calls final
  exit 1
  ```

- **2022's snap coverage is 78.3%** — a real historical gap. Reported by a
  bare `python verify_nfl.py` (104 passed, 7 NYM, 5 warnings, 2 FAILED),
  deliberately **not** gating today's job.
- **The MLB pitcher board is a coin flip.** Nothing I can fix; the model
  is frozen and it needs the ledger, not a PR.
- **56 of 108 test files have never had anything try to break them.** The
  ratchet holds — every file I added tonight carries a `@vacuity`
  declaration — but the backlog is the backlog.

---

## 5 · What I did NOT change

- **MLB** — `card.py`, `verify_card.py`, the model, the card, the MLB
  docs: untouched on every branch except `mlb/ask-sam-first`, which is
  parked and marked DO NOT MERGE WITHOUT READING.
- **`CRON TOTAL` = 55** before and after, on every branch. No cron was
  added, retimed, repriced or disabled. Every workflow change went
  through a PR, never a push.
- **`python budget.py` is unchanged**: MLB 322/day, football 135/day,
  13,710/month of 20,000 (69%). **Zero API calls were made all night.**
- **No bar, threshold or floor was loosened anywhere.** Two checks in the
  fix set were REPLACED, one more in the parked CFB branch, and every
  replacement is harder to pass than what it replaced.
- **`vacuity.py` itself was not touched**, and neither was the sweep, the
  blind-set ceiling, or any declared mutation's question.
- **No `picks/` or `data/` file was written.**
- **The ten already-corrupted rows in `picks/fb-nfl-2026-09-17.json` are
  not repaired.** That would be a second edit to a published record.
