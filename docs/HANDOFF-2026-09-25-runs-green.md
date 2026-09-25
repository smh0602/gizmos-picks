# HANDOFF — collect runs red since 2026-09-25 06:44Z: two causes, one blind spot

Read `CLAUDE.md` first. Dated; check every claim against `main`.

## What was wrong (measured, not assumed)

1. **`test_board_match.js` failed on every collect run.** The board held two
   doubleheaders (CHC @ BOS 17:06Z / 22:06Z, BAL @ NYY 20:05Z / 23:06Z);
   the BAL @ NYY pair was 3.0h apart against a 4h `BOARD_MATCH_WINDOW_MS`.
   ⚠️ **Worse than the test said: the page was already wrong.** MLB lists
   BAL @ NYY game 2 at a **20:10Z placeholder** (`startTimeTBD`), so
   nearest-first-pitch gave game 2's card **game 1's odds** — and a
   narrower window alone does not fix that (measured: the old matcher with
   a 90-minute window still hands game 2 the 20:05Z record).
2. **`verify_record.py` failed** on #1803, #1813, #1816–#1819. PR #166
   changed the grading rule (postponed = void); `record.json` was still the
   one the old rule wrote at 09-24 12:05Z. Reproduced: that exact file,
   verified by today's code, fails 5 checks; rebuilt, it reconciles.
3. **Run status was unreadable outside GitHub.** The runs watcher files an
   issue only when something is broken; nothing in the repo listed runs.

## What changed

| | fix | guard |
|---|---|---|
| 1 | `boardFor()` matches MLB's `gameNumber` against the board's first-pitch order first; fallback is a 90-min window that refuses a tie and never matches a placeholder time. `gameCard` passes the game. `verify_board.py`'s copy of the rule refuses a tie too. | `test_board_doubleheader.py` (the 2026-09-25 board + two schedule snapshots, 6 declared mutations incl. the old 4h window). `test_board_match.js` keeps its window invariant and now also replays the newest stored schedule: no record may go to two games. |
| 2 | `record.json` carries `grader` (`record_grader.py`: collect_record's AST closure). `verify_record.py` rebuilds a record whose stamp differs, then verifies. | `test_record_grader.py` builds the record with the pre-#166 rule and verifies it with today's code; control: the same content under the current stamp stays red and is not touched. 5 declared mutations. |
| 3 | `collect.py runs` → `data/latest/runs.json` (48h, every workflow, failing step + annotations). Staged `docs/upload/runs.yml` adds a `publish` job (the `watch` job stays read-only); freshness row `runs`, SOFT, off the page, stale after two missed hourly runs, present only once the watcher is deployed. | `test_runs_status.py`, 7 declared mutations. |

The MLB render oracle (`research/mlb_render_frozen.json`) was re-baselined
for `boardFor`, `gameCard` and `renderStaleBanner` only, with the reason in
its `_why`.

## What Sam must do

1. Merge the PR when `pr-tests` is green.
2. Upload `docs/upload/runs.yml` — `docs/upload/UPLOAD-runs.md` has every
   click. No cron line changes.

## What did NOT change

No cron line. No model coefficient, no pass bar, no published pick. The
grading rule itself (`slate_settled`, `VOID_STATES`) and verify_record's
re-grade are untouched. `collect.yml` is untouched.

## Mistakes, with root cause

- **Mine: the runs.json grace.** I first set 150 minutes; driving it
  against real landing times (44–58 past the hour) showed it only fires
  after THREE missed runs. Derived bound for "two in a row": 76–122 → 100.
  Root cause: I picked a number before deriving it.
- **The board-match invariant tested the board against itself.** Every
  probe passed a record's own commence back in, so it could never see
  MLB's placeholder time. Root cause: the test asked with the board's
  clock, the page asks with MLB's.
- **verify_record asked the wrong question after a rule change**: old
  grader's output vs new grader's re-grade. Root cause: nothing recorded
  which code built the file.

- **Mine again, after merge: the upload turned the suite red.** Sam
  uploaded the staged `runs.yml` at 20:33Z and collect run #1839 went red
  on `test_fb_freshness.py`: it pins MLB's contract at 16 rows and the
  live watcher switched on the 17th (`runs`). I had "simulated the
  upload" with ten tests I picked, not the suite. Root cause: pr-tests
  only ever tested the repo as it IS, never as it will be after a staged
  upload. Fix: the pin now holds in both states and admits exactly the
  `runs` row. Class guard: pr-tests' new `staged` job applies every
  staged upload to its own checkout and runs the suite again
  (`test_pr_staged.py`). Replayed on PR #174's head it goes red on
  exactly this test.
- **Not mine, same run:** `test_mlb_tables.py` required pitcher rows on
  the board; after C2 (#166) tonight's card has 0 (today's published card
  has 1 of 50). Pre-merge code fails identically on the same data. PR #171
  (another session) already fixes it; its hunk is ported byte-for-byte
  into the follow-up PR so the two merge cleanly in either order.

## Open

- `checks: read` for annotations is granted but unmeasured in production;
  a refusal lands as `detail_error` on the row, never fails the file.
- `collect.yml`'s token has no `actions: read`, so converge's own attempt
  to rebuild a stale runs.json may be refused; the row is SOFT, so that is
  a logged soft failure, not a red run.

## Changelog

- **2026-09-25:** first version.
- **2026-09-25 (later):** the post-upload red run (#1839), its root
  cause, the pin fix and the `staged` pr-tests job.
