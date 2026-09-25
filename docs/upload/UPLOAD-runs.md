# UPLOAD BY HAND: `runs.yml`

## Current: the run-status file `[2026-09-25]`

**Do this after you merge the pull request "Collect runs green again:
doubleheader odds, record rebuild, run-status file".** It is one file.

`runs.yml` is the hourly "did any workflow fail?" watcher. What changes in it:

1. A second job, **publish**, writes `data/latest/runs.json` every hour: the
   last 48 hours of every workflow (run number, what started it, when,
   how it ended, and for a failed run the step that failed and the error
   messages). Anyone can read it from the repo without a GitHub login.
2. The file also runs **once the moment you upload it**, so you do not wait
   for :41 past the hour.
3. The existing **watch** job (the issue that says a workflow is failing)
   is unchanged and still read-only.

**No schedule or cron line changes. No cost** (GitHub's own API, no Odds
credits).

### Click by click (Windows)

1. Open https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/runs.yml
   — the breadcrumb at the top reads **gizmos-picks / docs / upload / runs.yml**.
2. Click the **Download raw file** button (the down-arrow icon above the
   file, on the right). It saves `runs.yml` to your **Downloads** folder.
   ⚠️ If Windows saved it as `runs (1).yml`, rename it to exactly `runs.yml`.
3. Open https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
   — the breadcrumb reads **gizmos-picks / .github / workflows**.
   ⛔ Not the repo's front page: a file uploaded there lands in the top
   level, where it never runs.
4. Click **Add file** → **Upload files** → **choose your files**, pick
   `runs.yml` from Downloads.
5. In the commit box paste:

```
runs: also write data/latest/runs.json (last 48h of every workflow) - no cron change
```

6. Leave **Commit directly to the `main` branch** selected and click
   **Commit changes**.

### What you should see

- Within about 2 minutes the **Actions** tab shows a run named
  **runs [push]** with two jobs, **watch** and **publish**, both green.
- A new commit **runs: run status …** and a new file
  `data/latest/runs.json`. After that it updates every hour.
- If it goes red, the next hourly watcher run reports it like any other
  failed workflow.

---

## ~~Current:~~ Done: the Ubuntu 26 / Node 24 update `[2026-09-24]`

✅ Uploaded: on 2026-09-25 the deployed `runs.yml` matched this staged copy.

~~**This file is one of 11 uploaded together.** Follow
**`docs/upload/UPLOAD-runner-image.md`**: it has every click and the
commit message. Do it after merging the pull request "Workflows: pin
Ubuntu 24.04, move to Node 24 actions, pin Python", before 2026-10-19.~~

`runs.yml` is the hourly "did any workflow fail?" report. What changed in it then:

1. `runs-on: ubuntu-latest` → `runs-on: ubuntu-24.04`, so GitHub moving
   `ubuntu-latest` to Ubuntu 26.04 on 2026-10-19 changes nothing here.
2. `actions/checkout@v4` → `@v5`: the
   Node 24 versions (GitHub is retiring Node 20).
3. Before it runs any Python, the job now installs **Python 3.12** itself (the version it gets today) instead of using the computer's, which becomes 3.14 on Ubuntu 26.04.

**No schedule, cron line or step logic changes. No cost.**

---

## Changelog

- **2026-09-25:** the run-status file (`publish` job, runs once on upload).
  The 2026-09-24 section is marked done, not deleted.
- **2026-09-24:** first version.
