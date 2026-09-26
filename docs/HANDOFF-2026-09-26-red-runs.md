# HANDOFF — the two failure types left after #174: self-repair turns, and red pass failures

Read `CLAUDE.md` first. Dated; check every claim against `main`.

## What was wrong (measured from runs.json and the job logs, not assumed)

`data/latest/runs.json` at 2026-09-25T23:03Z: 437 runs in 48h, 57 failed.

1. **Self-repair, 5 failures** (#45, #47, #48, #49, #52), each "Reached
   maximum number of turns (40)".
   - **All eight passes** in the window (#45-#52) were handed issue #42,
     "T58 and T59 are accumulating". Its own body says "until then this is
     a counter, not a finding". The agent was told "Something this repo
     watches is broken", found nothing, and searched until the turns ran
     out (5 passes) or stopped empty-handed (3 passes, 19-39 turns). One
     made a branch to "guard" the counter.
   - The prompt asked for the whole suite: about 26 minutes locally (the
     vacuity sweep alone 17) in a 30-minute job, and longer than one agent
     command may run.
   - The record that makes the next pass skip an issue that produced no PR
     **never saved once**. Its push failed every pass (the action's revoked
     token ×5, the agent's unstaged edits ×2, the agent's branch left
     checked out ×1), and the step printed "nothing to record or nothing
     changed". It also counted every self-repair PR in the last 20 as
     "this pass's PR".
2. **Collect, 7 runs red on "mode 'X' failed"** (#1766, #1767, #1770,
   #1781, #1786, #1816, #1835). ⚠️ **Not an outside source, in any of
   them.** Every one was football `props-board` raising
   `TypeError: '<' not supported between instances of 'dict' and 'int'`
   after writing its board. `run_mode` stored the football builder's
   board in `left`, which is a credit count, and `left < RESERVE` failed
   (introduced 6491668, 2026-09-21). The workflow's line names the mode
   the cron launched, not the mode that failed. In all seven, converge
   said "every artifact is inside contract" and the freshness gate passed.
   All seven were also red on the Tests step.

## What changed

| | fix | guard |
|---|---|---|
| 1 | `self_repair.py`: the one pick; an issue marked `COUNTER` is never a task. `t58_t59.py` marks PROGRESS and ANSWERED (SHRANK and UNREADABLE stay findings). Staged `docs/upload/self-repair.yml`: triage uses the module; the prompt asks for the tests the change touches; the record uses its own checkout and `push_retry.sh`, fails loudly, and counts only this pass's PR; the contradictory "Do not touch MLB" line is gone. The 40-turn cap is unchanged. | `test_self_repair.py` (record step driven against a bare remote), `test_watch_label.py` §7 (staged triage driven), tier 1 + 6 declared mutations. |
| 2 | `collect.py`: props-board no longer stores the board in `left`. `freshness.classify` is the gate's one hard/soft verdict (verify_freshness calls it; output identical on all three leagues). `freshness.judge_failures` + `outside_source`: a failed converge mode is a `::warning::` naming the source only when the error is evidence of an OUTSIDE source AND every artifact it writes is inside contract; everything else stays red, and converge annotates the mode that actually failed. | `test_converge_judge.py` (the real converge, 5 cases, 7 mutations), `test_run_mode_left.py` (AST over every `left =` in run_mode + football props-board driven end to end). |

## Found while testing: a news-archive check red on a correct site

At 00:44Z on 09-26, `test_news_archive.py` failed on `main`'s own code
(and turned collect #1849 red). ~~It compared a fresh `latest/news.json`
(built 23:05Z the day before, still inside its deadline) with today's UTC
archive.~~ **Wrong diagnosis, mine.** The row the check read as "latest"
was `latest/news-flags.json`, fresh all day, picked by a `{mode: row}`
lookup; `news.json` itself was stale from 00:00Z. #182 fixed that (rows by
path, `news_rows`). ✅ Merged here with #182; my `_archive_day` stays on
top at Sam's request (2026-09-26). With news due at the top of every hour,
it equals the clock's day whenever the check can fire; it matters only if
a news deadline moves off the hour. Guarded by drives and an AST pin of
the live join (a test cannot declare a mutation of its own file).

## ⚠️ Where this differs from the request, and why

Sam asked: red only when an artifact is left stale or missing, otherwise a
warning. Taken literally, that would have turned all seven failures above
into permanent warnings: the board was written before our own crash, so
the contract never saw anything stale. `freshness.py` already refuses that
(source_block: "A REFUSAL NEEDS POSITIVE EVIDENCE FROM THE SOURCE ... a
grace that can be claimed by any exception is ... a mute button"). So the
downgrade needs evidence of an outside source, as the request itself
framed it ("a failed converge pass for an outside source").

## What each fix would have prevented in that 48h

- Self-repair: 5 of 5 failures were spent on #42, which triage now never
  hands over. Issue #44 was also open, so those passes would have worked
  on it instead. Whether that finishes inside 40 turns is not in the logs.
- Collect: 7 of 7 "mode failed" gates were the props-board TypeError,
  fixed here. The new judge would have kept them RED, correctly. All 7
  runs were also red on tests fixed since, so this PR alone turns none of
  those runs green in hindsight; it removes the pass failure that was left.
  The other 37 collect failures were tests (35) and verify_record (2),
  fixed by earlier PRs.

## What Sam must do

1. Merge the PR when `pr-tests` is green.
2. Upload `docs/upload/self-repair.yml` (`docs/upload/UPLOAD-self-repair.md`
   has every click). No cron line changes. Until then the deployed
   self-repair still picks #42.

## Open

- ~~`unknown mode: news-archive` is logged as a SOFT failure on every
  football pass that plans it: the contract names a mode `run_mode` does
  not have. Soft, so not red; not fixed here.~~ ✅ **Closed by #182**
  (merged 2026-09-26): the archive row names its writer, `news`, and
  `test_contract_modes.py` fails on any contract mode `run_mode` does not
  dispatch. Checked against this PR after the merge: `classify` puts a
  stale archive row in SOFT (never hard) and `judge_failures` keeps a
  failed `news` pass a warning, on the real nfl and ncaaf contracts
  (`test_converge_judge.py` §6, declared mutation BITES).
- #171's rounding guard in `test_verify_card.py` is VACUOUS: open as #185.
- A downgraded failure is a `::warning::` on the run page only;
  `runs.json` lists annotations for failed runs only.
- `self-repair.yml` is staged: until Sam uploads it, the deployed triage
  still hands the agent issue #42.

## Mistakes, with root cause

- **Mine, caught before commit:** the prompt first said the suite "takes
  longer than this job's 30 minutes". Summed from my own run it is about
  26. Root cause: I wrote a number before measuring it.
- **Mine, caught by the staged-uploads job's check:** new triage wording
  ("open watcher issues needing a repair") no longer matched a check
  searching for "open watcher issues: 0", which would have passed
  vacuously. Kept the phrase.
- **Mine, caught by test_vacuity:** my props-board rewrite left
  `test_props_board_dispatch.py`'s declared mutation pointing at a line that
  no longer exists (1 of 412 rotted). Root cause: I did not search for
  declarations naming the lines I changed. Re-pointed, same intent, BITES.
- **Found, not fixed here:** #171's `test_verify_card.py` declaration is
  VACUOUS since the 09-25 card was published (it checks "the newest card",
  which no longer has a row on the rounding branch). Queued separately.
- **Mine, corrected after #182:** I blamed the midnight news-archive
  failure on the clock's day. It was the wrong ROW (news-flags, fresh all
  day), which #182 found. Root cause: I did not check which file the
  test's "latest" row was before explaining its verdict.
- **Mine, found after merge (fixed in the next PR,
  `HANDOFF-2026-09-26-annotations-sweep.md`):** this PR put two FALSE
  `::error::` annotations on every collect run. `test_self_repair.py`
  echoed the driven record step's error, and `test_freshness.py` prints
  converge's new `::error::` in-process. Root cause: I checked that the
  tests passed, never what their output said to GitHub.
- **Mine, found after merge (collect #1856 red):** the staged
  `self-repair.yml` dropped the line `test_workflow_python.py`'s declared
  mutation quoted from the LIVE file. It rotted the moment Sam uploaded.
  Root cause: I searched for declarations quoting the lines I changed in
  `collect.py`, not the lines my staged workflow removed.
- **Not mine, recorded:** the annotation "mode 'news' failed for ncaaf"
  pointed at the wrong mode for two days; Sam's diagnosis followed it.
  Converge now annotates the mode that failed.

## Changelog

- **2026-09-26:** first version.
- **2026-09-26 (after merge):** two mistakes of this PR recorded, found
  by collect #1856; fixed in `HANDOFF-2026-09-26-annotations-sweep.md`'s PR.
- **2026-09-26 (later):** merged main with #182; the midnight diagnosis
  corrected (struck, not deleted); Open updated: news-archive closed by
  #182, #171's vacuous guard is #185.
