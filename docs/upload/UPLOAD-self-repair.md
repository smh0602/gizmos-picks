# UPLOAD BY HAND: `self-repair.yml`

## Current: stop the repair agent running out of turns `[2026-09-26]`

**Do this after you merge the pull request "Self-repair stops running out
of turns; a failed outside source no longer turns collect red".** It is one
file.

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
4. Click **Add file** → **Upload files** → **choose your files**, pick
   `self-repair.yml` from Downloads.
5. In the commit box paste:

```
self-repair: never hand the agent a counter, run touched tests, record every pass - no cron change
```

6. Leave **Commit directly to the `main` branch** selected and click
   **Commit changes**.

### What you should see

- Nothing runs on upload (this workflow has no push trigger).
- At the next self-repair time (7:23am, 1:23pm, 7:23pm or 1:23am ET) the
  **triage** job's log says `open watcher issues needing a repair: N`. Issue
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

- **2026-09-26:** never hand the agent a counter, run touched tests, record
  every pass. The 2026-09-24 section is marked done, not deleted.
- **2026-09-24:** first version.
