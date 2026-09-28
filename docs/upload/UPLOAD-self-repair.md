# UPLOAD BY HAND: `self-repair.yml`

## Current: stop starting an agent that cannot finish `[2026-09-28]`

**Do this after you merge the pull request "Self-repair stands down after
two passes it could not finish; #44 and #192 never go to the agent".** It
is one file.

`self-repair.yml` failed 8 of 8 runs between 9/26 14:58Z and 9/28 11:48Z.
Every one stopped at "Reached maximum number of turns (40)" and opened no
pull request. What changes in it:

1. **It stands down.** After two passes in a row that end at the turn cap
   (or run to the end and open no pull request), it stops starting the
   agent. Each issue those passes worked on gets one comment: "self-repair
   could not fix this in 40 turns; it needs a person." It starts again
   when a pull request merges to main, or when an issue it could work on
   opens or closes.
2. **Every pass is recorded**, with how it ended (the turn cap, finished
   without a PR, a PR, or an error), in `data/latest/self-repair-last.json`.
   It lands the same way every data commit does.

The other half of the fix does **not** need this upload. Late crons (#44)
and the calibration monitor (#192) never go to the agent. The live
workflow already asks `self_repair.py` which issue to pick, so that works
from the merge.

**No schedule or cron line changes. No cost.** The turn limit stays 40.

### Click by click (Windows)

1. Open https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/self-repair.yml
   — the breadcrumb at the top reads **gizmos-picks / docs / upload / self-repair.yml**.
2. Click the **Download raw file** button (the down-arrow icon above the
   file, on the right). It saves `self-repair.yml` to your **Downloads**
   folder. ⚠️ If Windows saved it as `self-repair (1).yml`, rename it to
   exactly `self-repair.yml`.
3. Open https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
   — the breadcrumb reads **gizmos-picks / .github / workflows**.
   ⛔ Not the repo's front page: a file uploaded there lands in the top
   level, where it never runs.
4. Click **Add file** → **Upload files** → **choose your files**, and pick
   `self-repair.yml` from Downloads.
5. In the commit box paste:

```
self-repair: stand down after two passes that could not finish - no cron change
```

6. Leave **Commit directly to the `main` branch** selected and click
   **Commit changes**.

### What you should see

- Nothing runs on upload (this workflow has no push trigger).
- **The first two passes after the upload still start the agent.** The
  record kept today has no count in it yet.
- **If both of those end at the turn cap:**
  - the second one comments on the issues the two passes worked on;
  - a commit **self-repair: issue #N, opened_pr=0, turn_cap** appears;
  - from the next pass on, the **triage** job's log says
    `standing down since …` and the agent does not start.
- **It starts again on its own:** on the first pass after you merge any
  pull request, or after a watcher issue it could work on opens or closes.
- **#44 and #192 are never picked.** The triage log's count leaves them
  out. Each picks up the marker the next time its watcher rewrites it:
  hourly for #44, daily for #192.

---

## ~~Current:~~ Done: stop the repair agent running out of turns `[2026-09-26]`

✅ Uploaded: on 2026-09-28 the deployed `self-repair.yml` matched that staged copy.

~~**Do this after you merge the pull request "Self-repair stops running out
of turns; a failed outside source no longer turns collect red".** It is one
file.~~

`self-repair.yml` is the watchdog's repair agent. It failed 5 times in 48
hours with "Reached maximum number of turns (40)". Every pass was given
issue #42, which only counts up two pre-registered tests and has nothing
to fix. What changes in it:

1. **Triage never hands the agent a counter.** Issue #42 now says it is a
   counter (an invisible marker the watcher writes), and triage skips it.
   If only counters are open, the agent does not start.
2. **The agent is asked to run the tests its change touches**, not the whole
   suite (about 26 minutes of a 30-minute job). `pr-tests` still runs the
   whole suite on any pull request it opens.
3. **The "skip this issue next time" record now actually saves.** It never
   saved once before: the push failed every time and the step said
   "nothing to record". It now saves from its own clean copy of the repo,
   and says so in red if it cannot. It also counts only a pull request
   opened by *this* pass.
4. The prompt no longer says both "Do not touch MLB" and "MLB IS OPEN FOR
   REPAIR"; it keeps the second, which matches CLAUDE.md.

**No schedule or cron line changes. No cost.** The turn limit stays 40.

### ~~Click by click (Windows)~~ — done on 2026-09-26; use the section at the top

1. Open https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/self-repair.yml
   — the breadcrumb at the top reads **gizmos-picks / docs / upload / self-repair.yml**.
2. Click the **Download raw file** button (the down-arrow icon above the
   file, on the right). It saves `self-repair.yml` to your **Downloads**
   folder. ⚠️ If Windows saved it as `self-repair (1).yml`, rename it to
   exactly `self-repair.yml`.
3. Open https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
   — the breadcrumb reads **gizmos-picks / .github / workflows**.
   ⛔ Not the repo's front page: a file uploaded there lands in the top
   level, where it never runs.
4. Click **Add file** → **Upload files** → **choose your files**, pick
   `self-repair.yml` from Downloads.
5. In the commit box paste:

```
self-repair: never hand the agent a counter, run touched tests, record every pass - no cron change
```

6. Leave **Commit directly to the `main` branch** selected and click
   **Commit changes**.

### ~~What you should see~~ — then

- Nothing runs on upload (this workflow has no push trigger).
- At the next self-repair time (7:23am, 1:23pm, 7:23pm or 1:23am ET) the
  **triage** job's log says `open watcher issues: N (counters left out)`. Issue
  #42 is not counted once the owed-tests watcher has rewritten it with the
  marker (its next daily run).
- If the agent runs and opens no pull request, a commit
  **self-repair: issue #N, opened_pr=0** appears, and the next pass skips
  that issue once.

---

## ~~Current:~~ Done: the Ubuntu 26 / Node 24 update `[2026-09-24]`

✅ Uploaded: on 2026-09-26 the deployed `self-repair.yml` matched that staged copy.

~~**This file is one of 11 uploaded together.** Follow
**`docs/upload/UPLOAD-runner-image.md`**: it has every click and the
commit message. Do it after merging the pull request "Workflows: pin
Ubuntu 24.04, move to Node 24 actions, pin Python", before 2026-10-19.~~

`self-repair.yml` is the watchdog's repair agent. What changed in it then:

1. `runs-on: ubuntu-latest` → `runs-on: ubuntu-24.04`, so GitHub moving
   `ubuntu-latest` to Ubuntu 26.04 on 2026-10-19 changes nothing here.
2. `actions/checkout@v4` → `@v5`: the
   Node 24 versions (GitHub is retiring Node 20).
3. Before it runs any Python, the job now installs **Python 3.12** itself (the version it gets today) instead of using the computer's, which becomes 3.14 on Ubuntu 26.04.

**No schedule, cron line or step logic changes. No cost.**

~~If you upload only this one file: download
https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/self-repair.yml
with **Download raw file**, then in
https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
(breadcrumb **gizmos-picks / .github / workflows**) click **Add file** →
**Upload files** → **choose your files**, pick `self-repair.yml`, and commit with:~~

~~`workflows: pin ubuntu-24.04, Node 24 actions, pinned Python (no cron change)`~~

---

## Changelog

- **2026-09-28:** stand down after two passes that could not finish; the
  runs watcher's and calibration monitor's issues never go to the agent.
  The 2026-09-26 section is marked done, not deleted.
- **2026-09-26:** never hand the agent a counter, run touched tests, record
  every pass. The 2026-09-24 section is marked done, not deleted.
- **2026-09-24:** first version.
