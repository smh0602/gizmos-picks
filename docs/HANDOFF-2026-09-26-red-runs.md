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

- `unknown mode: news-archive` is logged as a SOFT failure on every
  football pass that plans it: the contract names a mode `run_mode` does
  not have. Soft, so not red; not fixed here.
- A downgraded failure is a `::warning::` on the run page only;
  `runs.json` lists annotations for failed runs only.

## Mistakes, with root cause

- **Mine, caught before commit:** the prompt first said the suite "takes
  longer than this job's 30 minutes". Summed from my own run it is about
  26. Root cause: I wrote a number before measuring it.
- **Mine, caught by the staged-uploads job's check:** new triage wording
  ("open watcher issues needing a repair") no longer matched a check
  searching for "open watcher issues: 0", which would have passed
  vacuously. Kept the phrase.
- **Not mine, recorded:** the annotation "mode 'news' failed for ncaaf"
  pointed at the wrong mode for two days; Sam's diagnosis followed it.
  Converge now annotates the mode that failed.

## Changelog

- **2026-09-26:** first version.
