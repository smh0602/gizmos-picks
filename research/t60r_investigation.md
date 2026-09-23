# T60R — why signal 6 never votes, and when the sample could reach 1,000

**Investigation only.** Nothing in `t60r.py`, `research/t60r_spec.md` or
the approved rule was changed. T60R stays frozen as Sam approved it on
2026-09-22 (bar option B). Everything below comes from the code and data
on `main`. The only outcome number used is the one already in the
committed report; nothing here recomputes a hit rate.

Reproduce every count: `python research/t60r_investigation.py` (read-only,
imports `t60r`'s own functions, computes no hit rate).

---

## In plain English (for Sam)

1. **Signal 6 never votes because I switched it off in the code, not
   because of a field name or a spelling.** No record exists of each
   team's clock share *before* each past game, so there was nothing
   honest for it to vote with. I said so in PR #130, but **the spec you
   approved still describes signal 6 voting. The code and the spec
   disagree, and I should have brought that back to you before building,
   not after.**
2. **While checking, I found a real bug of mine in signal 7 (injuries).**
   It was supposed to count players ruled **out**. It actually counts
   players who **played** while listed questionable. Out players have no
   stat row that week, so it can never see them. This exact mistake was
   already fixed once elsewhere in the repo, and I rebuilt it.
3. **Two data gaps starve the rule further.** The repo stores no 2024
   games, so signals 2 and 4 are blind for most or all of 2025. And in
   college, only two signals can ever vote on a spread. Result: **2
   college spread plays in all of 2025, out of 731 games.**
4. **The sample can never reach 1,000 under the approved test.** The spec
   covers the 2025 and 2026 seasons only. At the current pace the total
   ends the 2026 season at roughly **350 to 410** effective rows. Even if
   the test kept running into future seasons, 1,000 is about three more
   seasons away, around the 2029 season.
5. The 47.3% on 222 rows is **not a verdict**, and with the problems
   above it isn't even a fair reading of the rule you approved. The
   choices are at the bottom, as proposals for a **new** pre-registered
   test. None is implemented.

---

## 1. Signal 6 (possession) voted 0 times. Why?

**Verdict: it isn't a field-name bug, a missing join, or a spelling issue
like PR #132. It's hard-coded to 0, because no source exists that says
what a team's clock share was *before* a given past game.**

### Evidence

- **`t60r.py`, `votes()`:** `sp["6_possession"] = to["6_possession"] = 0`,
  unconditionally. `SHARE_GAP = 0.04` is defined at the top and **never
  read**. So "0 votes in 2,384 candidates" is exactly what the code does,
  not a symptom of something else.
- **What the stored possession data holds** (`data/<lg>/latest/top-2026.json.gz`):

  | | NFL | college |
  |---|---|---|
  | top-level keys | `season, kind, source, column, unit, note, drives, unparsed_drives, teams, pulled_at, written_at` | same, minus `pulled_at` |
  | rows | **32 teams, one season-to-date total each** (`share, seconds_per_game, games, drives, seconds, seconds_per_drive`) | **283 teams**, same shape |
  | per-game or per-drive rows | **none** | **none** |
  | a 2025 file | **none** | **none** |
  | dated archive (`data/<lg>/<date>/`) | **none** | **none** |
  | first commit of the file | 2026-09-20 08:53Z (6 commits since) | 2026-09-20 07:02Z (5 commits since) |

- Using that file for a game inside its own season means using games
  played **after** the kickoff being graded. That's lookahead, which the
  spec's filter list forbids. So the honest options were "abstain" or
  "stop and ask". I chose abstain and disclosed it in PR #130 and in the
  report's vote counts. **But the approved spec's section 2 still reads
  "Vote for the team with the higher share of the clock, if the gap is 4
  points of share or more."** The rule you approved and the rule that runs
  differ on this row. ⚠️ My mistake: that should have come back to you as
  a question before the build, not as a line in a PR description.

### Would it trigger if the data existed?

**Often.** As a size check only: on the current season-to-date table,
which contains lookahead and **must not be graded**, the two teams' shares
differ by at least 4 points in **21 of 32** NFL 2026 finals and **103 of
157** FBS 2026 finals, about **66%** in both leagues. Signal 6 isn't
naturally quiet; it's switched off.

**The most it could add:** it only matters where the other signals already
net ±1. Across the backtest, spread candidates stuck at exactly ±1 number:

| | 2025 | 2026 so far |
|---|---|---|
| NFL spreads at net ±1 | 120 | 14 |
| college spreads at net ±1 | 446 | 105 |

Those numbers are an upper bound. Signal 6 would turn a ±1 into a play
only when it points the same way, and it could just as easily cancel one.

---

## 2. Found during the investigation: signal 7 counts the wrong players

**Verdict: a bug in `t60r.py`, and mine.**

- **The approved rule:** "Vote against the team with at least 2 more
  players **flagged out**, as of the week before."
- **The code** (`Personnel`) counts rows with `inj > 0` in the **player
  stat logs**.
- **`nfl.py` already documents why that can't work** (its comment above
  the injuries loop, from run #194): *a player who is out has no stat row
  that week.* He didn't play, so the stats file never lists him. `nfl.py`
  keeps a separate out-set for exactly this reason. `t60r.py` rebuilt the
  broken version.
- **Measured:** NFL 2025 stat rows by injury rank are **0: 18,780 · 1
  (questionable): 620 · 2 (doubtful / out / IR): 0.** Not one of the
  rows signal 7 reads is a player who was out.
- **So signal 7's 86 spread votes on NFL 2025 counted "questionable and
  played".** That's a different quantity from the one you approved, and
  those votes helped decide which NFL rows were played.
- **College has no injury field at all.** The only related key on a
  college player row is `ahead_out_lastwk`. Signal 7 can't vote in
  college. Your rule 6 says whatever is built for one league is built
  for the other; here it can't be, because there's no college source.
- **NFL 2026 shows 0 votes for a separate, correct reason:** the logs so
  far cover weeks 1 and 2 only, with 8 and 22 flags in total. A week-2
  game reads week-1 flags, and a team needs 2 more than its opponent.

---

## 3. Also found: missing 2024 history, and college spreads that almost never play

- **The stored schedules hold only 2025 and 2026.** The 365-day
  head-to-head window and the "last 4 finals" form both reach back into
  2024 for early and mid 2025, and those games aren't stored.

  | | games | no last-4 form (signal 4 silent) | no head-to-head (signal 2 silent) |
  |---|---|---|---|
  | NFL 2025 | 284 | 32 (the first two weeks) | **232** |
  | college 2025 | 731 | 86 (the first two weeks) | **724** |
  | NFL 2026 | 32 | 0 | 17 |
  | college 2026 | 145 | 0 | 123 |

- **College spreads almost never play.** On a college spread only two
  signals can vote at all:
  - signal 2, head-to-head, missing in 724 of 731 games in 2025
  - signal 4, this season

  Signal 6 is hard-coded off and signal 7 has no college data. The others
  abstain on spreads by the rule's own design. A play needs a net of 2, so
  a college spread plays only when both vote the same way. **2025: 2
  college spread plays out of 731 games; 446 stuck at ±1.**

---

## 4. How long until effective n reaches 1,000?

**Short answer: under the approved test, never.** The spec's scope
(section 1) is **2025 and 2026 only**, and `t60r.SEASONS = (2025, 2026)`.
When the 2026 season ends, no new games qualify.

### Qualifying games per week (from the committed report, 2026-09-22 21:30Z)

Effective n here is **floored at the game count** ("floored at the 203
game(s) the rows come from"), so games per week is the effective-n
contribution per week.

| season | ISO week | rows | games |
|---|---|---|---|
| 2025 | 2025-W37 | 7 | 7 |
| 2025 | 2025-W38 | 10 | 10 |
| 2025 | 2025-W39 | 12 | 12 |
| 2025 | 2025-W40 | 10 | 10 |
| 2025 | 2025-W41 | 18 | 18 |
| 2025 | 2025-W42 | 14 | 14 |
| 2025 | 2025-W43 | 16 | 15 |
| 2025 | 2025-W44 | 8 | 8 |
| 2025 | 2025-W45 | 8 | 8 |
| 2025 | 2025-W46 | 13 | 11 |
| 2025 | 2025-W47 | 5 | 5 |
| 2025 | 2025-W48 | 20 | 18 |
| 2025 | 2025-W49 | 4 | 4 |
| 2025 | 2025-W50 | 4 | 2 |
| 2025 | 2025-W51 | 4 | 3 |
| 2025 | 2025-W52 | 6 | 4 |
| 2025 | 2026-W01 | 10 | 8 |
| 2025 | 2026-W02 | 3 | 2 |
| 2025 | 2026-W04 | 1 | 1 |
| **2025 total** | | **173** | **160** |
| 2026 | 2026-W35 | 1 | 1 |
| 2026 | 2026-W36 | 11 | 9 |
| 2026 | 2026-W37 | 18 | 16 |
| 2026 | 2026-W38 | 19 | 17 |
| **2026 so far** | | **49** | **43** |
| **combined** | | **222** | **203** |

- **2025:** about 8 games a week over 19 active weeks, with **none in the
  first two weeks** because there was no 2024 history (section 3).
- **2026:** 16 to 17 games a week lately, about twice 2025's rate for
  the same weeks, because 2026 can read 2025's games as history.

### Projection

| method | 2026 still to come | combined at end of 2026 season |
|---|---|---|
| A. 2026's recent pace (~17 a week through the college regular season, then 2025's post-season shape) | ~200 | **~400** |
| B. 2025's own games in the same calendar weeks (W39 on) | ~143 | **~350** |
| **needed** | | **1,000** |

- ⛔ **It cannot reach 1,000 before the season ends.** It can't reach it
  at all under the approved scope, which stops at 2026. The approved test
  will read **NOT YET MEASURABLE** at every weekly run until then, and
  after that it stops growing.
- **If the scope ran on into later seasons** (a change only Sam can
  make), a full season with a full year of history behind it looks like
  roughly 250 to 300 games. The remaining ~600 to 650 would take about
  three more seasons, **around the 2029 season** at the earliest. That's
  rough; it assumes 2026's rate holds.

---

## 5. Options, as proposals for a NEW pre-registered test (not implemented)

⛔ **None of these is implemented, and T60R is not edited.** Each would be
a new test with a new id, approved by Sam before it runs.

⚠️ **One caution matters more than any option:** the 47.3% has now been
seen. Changes that make the **data complete** can be judged without
reference to that number: fixing signal 7, giving signal 6 a
point-in-time source, adding 2024 history. Changes to **thresholds or
the play rule** chosen now could be chosen, even unintentionally, because
of it. The first kind is safe to pick now; the second deserves suspicion.

| # | proposal | what it fixes | cost | kind |
|---|---|---|---|---|
| P1 | **Signal 7 counts players listed OUT or DOUBTFUL**, from the injuries file that `nfl.py` already reads (it builds the out-set and discards it). `nfl.py` would need to store a per team-week "players out" count. | the bug in section 2 | free (nflverse) | data completeness |
| P2 | **Signal 6 from a point-in-time source.** NFL: per-game possession shares from nflverse play-by-play, which `possession.py` already computes. College: per-game shares from CFBD `/plays` for 2025. From now on: a dated daily copy of `top-<season>` through `daystore.py`, so a future test can read the share as it stood before kickoff. | section 1 | NFL free. College 2025 is a quota question: about one `/plays` call per week per season type (~17–20), to be derived by `cfbd_budget.py` before any pull. Dated copies are free. | data completeness |
| P3 | **Store the 2024 schedules**, so signals 2 and 4 have history for 2025. | section 3 | NFL free (nflverse). College: 2 CFBD `/games` calls. | data completeness |
| P4 | **Let the scope run on past 2026**, so weekly grading keeps adding games. | section 4: without it, 1,000 is out of reach | free | scope |
| P5 | **Re-examine the play rule or the bar.** With four or five of eight signals abstaining, "net 2" is very restrictive. A lower n floor would reach a verdict sooner, but only a bigger edge would be detectable. | reachability | free | ⚠️ **rule/bar: see the caution above** |
| P6 | **College has no injury source.** Either accept that signal 7 is NFL-only, or look for a college source. | rule 6 (build for both leagues) | unknown; only a probe would say | data completeness |

**If only one thing gets done:** P1 plus P3 are free and fix a real bug and
the largest gap. P2 gives the rule the signal it was written with. P4
decides whether the test can ever finish.

---

## Also open

- **PR #132** (the DraftKings spelling fix) isn't merged, so the committed
  report still prices some college games at a lower-ranked book. It can't
  change the verdict (NOT YET MEASURABLE either way), but the weekly run
  after it merges will use the corrected picker.

## Changelog

- **2026-09-23:** first version. Investigation only: signal 6 (hard-coded
  off, no point-in-time source), signal 7 (my bug: counts
  "questionable and played", never "out"), missing 2024 history, college
  spreads that almost never play, and the effective-n projection (can't
  reach 1,000 under the approved scope). Proposals P1–P6 for a new
  pre-registered test; none implemented.
