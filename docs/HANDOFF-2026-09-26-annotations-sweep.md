# HANDOFF — false error annotations on every run, the sweep's clock, and collect #1856

Read `CLAUDE.md` first. Dated; check every claim against `main`.

## What was wrong (measured from the run logs, not assumed)

1. **Every collect run carried false ERROR annotations, the green ones
   included.**
   - GitHub reads any printed line that starts (after indentation) with
     `::error::` as an annotation on the run.
   - #1852 (green) had two, `test_live.py FAILED`. `test_pr_staged.py` drives
     the pr-tests loop against a planted failing `test_live.py` and printed
     the captured log in a check's detail.
   - #1856 had four. The other two came from **my #184**:
     - `test_self_repair.py` echoed a driven record step's
       `::error::could not record this pass`;
     - `test_freshness.py` runs `collect.converge()` in-process, and #184
       made converge print `::error::card failed for mlb …`.
2. **Collect #1856 went red on `main`, and it was mine.**
   - #184 staged a `self-repair.yml` whose triage Python moved into
     `self_repair.py`.
   - `test_workflow_python.py` declared a mutation (`@vacuity`) on the live
     file's `skip = sys.argv[1].strip()`.
   - Every pr-tests job passed, because the sweep checks declarations
     against the live file and the `staged` job runs only the `rest` shard.
   - Sam uploaded the file, the declaration matched nothing, and
     `test_vacuity.py` failed ("1 of 420 rotted"). Every collect run after
     the upload is red until this merges.
3. **The vacuity sweep's clock.**
   - #1852: 2081 s of 2400 s (13% margin), 8283 s of work over 4 trees.
     4 × 2071 s is the floor, so the packing was already as tight as it gets.
   - #1856 (main with #184): 1733 s (28% margin), 6837 s of work.
   - ⚠️ The runner, not the code, moved most of that: the same 17
     `test_dossier_fb.py` declarations cost 4309 s on #1852's runner and
     3428 s on #1856's. At #1852's speed, #1856's work is about 2150 s, a
     10% margin, so it was treated as under the 15% line.
   - Where the time goes (#1856): `test_dossier_fb.py` 3428 s (50%),
     `test_mlb_tables.py` 1094 s, `test_shadow_fb.py` 432 s,
     `test_self_repair.py` 320 s, `test_accumulators.py` 274 s.

## What changed

| | fix | guard |
|---|---|---|
| 1 | `tcheck.py` watches every line a test process writes to stdout or stderr. What the HARNESS prints (a check, its detail, a note, a section) is defused (`::` → `: :`), because showing captured output there is its job and the content can depend on the machine. Any other line GitHub would read as a command is written defused AND fails the file, naming it. `tcheck.annotate()` is the one deliberate way (`test_vacuity.py`'s clock warning uses it). The four real sources are fixed (`shown()` in `test_pr_staged.py` and `test_self_repair.py`; `test_freshness.py` captures converge's output), and four failure-branch prints of child output now go through `shown()`. | `test_workflow_commands.py`: every way a planted `::error::` can be written (detail, note, `eq`, section, bare print, stderr, indented, split across writes, unfinished last line, product code in-process, worker thread, traceback) and the control; a static check that no test starts a child without capturing both streams; tcheck imported before anything prints. 7 declared mutations, all bite. |
| 2 | `test_workflow_python.py`'s declaration is re-pointed to `since = sys.argv[1]` in the same file, with the same intent. `vacuity.rotted()` (one copy; `test_vacuity.py` §0b calls it) also checks a declaration naming a workflow with a pending upload against the STAGED copy. | `test_pr_staged.py` §4 drives `rotted()` on planted trees, and on the real tree. On the tree as #184 merged it, the new check names this exact declaration; the old one found nothing. 1 new declared mutation, bites. |
| 3 | The sweep does less work and drops nothing: all 431 declarations, each still run red and then green. **Red runs stop at the first failed check** (`TCHECK_FAIL_FAST`, set by `vacuity.run_test(red=True)` only). **`test_self_repair.py`** sets `PUSH_BACKOFF=0` on its unreachable-remote drive: all five attempts are still made, just without 45 s of sleep. **`copy_module`** parses each file once per process. | `test_fail_fast.py`: the verdict matches a full run in 8 shapes (first or last check failing, all passing, crash, no checks, a failure caught by `except BaseException`, a worker thread, a `finally`); the mode is never inherited by a child; the sweep asks for it on the red run only. 4 declared mutations, all bite. `copy_module`: all 52 modules copy exactly the same files as before. |

## Why fail-fast is not a weaker sweep

The sweep reads one bit from a red run: did it exit non-zero. A failed
check is final. Nothing in the suite un-records one (searched: no test
touches `tcheck.FAILURES`), and the gate turns any failure into exit 1.
So the first failure already decides that bit, and the rest of the run
can only confirm it. The green-on-revert run, the half that proves the
test passes on correct code, is always a full run. ⛔ Not done, because
it would be weaker: running the green check once per file instead of once
per declaration (leftover state from one mutation could make a later red
run red for the wrong reason), or sweeping only the files a PR touched
(see `HANDOFF-2026-09-23-vacuity.md`).

## Sweep measurements

| | wall | per-run total | margin |
|---|---|---|---|
| CI #1852 (before #184) | 2081 s | 8283 s | 13% |
| CI #1856 (main with #184) | 1733 s | 6837 s | 28% |
| local, main with #184 | 1140 s | 4476 s | — |
| local, this branch | _pending_ | _pending_ | — |

## What Sam must do

1. Merge the PR when `pr-tests` is green. No upload, no cron change, no cost.

## Open

- A child process started by PRODUCT code during a test writes to the
  descriptor it inherited, below Python, and the watcher cannot see it. The
  node tests (`test_*.js`) are not watched either. Neither prints a command
  today.
- The collect sweep's margin is measured on a runner whose speed varies
  about 26% between runs. `test_vacuity.py` annotates a warning past half
  the clock, and each new declaration adds to the total.

## Mistakes, with root cause

- **Mine (#184): two of the four false annotations.** Root cause: after
  adding an `::error::` print to converge and driving a step that prints
  one, I checked that the tests passed, never what their output said to
  GitHub.
- **Mine (#184): the rotted declaration that turned collect #1856 red.**
  Root cause: I searched for declarations quoting the lines I changed in
  `collect.py`, but not for the lines my STAGED `self-repair.yml` removed.
  The declaration named the deployed file, which had not changed yet.
- **Mine, caught before commit:** the first static check ("any statement
  above the tcheck import") failed 17 correct files that need
  `sys.path.insert` first. The first subprocess rule flagged
  `capture_output=True, **k`. Both fired on correct code and were narrowed
  to the real question.
- **Mine, caught before commit:** the first design failed a file for a
  command inside a check's detail. `test_accumulators.py` prints the tail of
  a collector run whose `::warning::` lines exist only where the news feeds
  fail, so that would have been a red run that comes and goes with the
  network. The harness now defuses its own lines, and only writes that
  bypass it fail.

## Changelog

- **2026-09-26:** first version.
