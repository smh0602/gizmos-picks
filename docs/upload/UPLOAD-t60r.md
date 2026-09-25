# UPLOAD BY HAND: `t60r.yml`

## Current: the Ubuntu 26 / Node 24 update `[2026-09-24]`

**This file is one of 11 uploaded together.** Follow
**`docs/upload/UPLOAD-runner-image.md`**: it has every click and the
commit message. Do it after merging the pull request "Workflows: pin
Ubuntu 24.04, move to Node 24 actions, pin Python", before 2026-10-19.

`t60r.yml` is the weekly T60R backtest grading. What changes in it:

1. `runs-on: ubuntu-latest` → `runs-on: ubuntu-24.04`, so GitHub moving
   `ubuntu-latest` to Ubuntu 26.04 on 2026-10-19 changes nothing here.
2. `actions/checkout@v4` → `@v5` and `actions/setup-python@v5` → `@v6`: the
   Node 24 versions (GitHub is retiring Node 20).
3. Its Python version does not change (it already installed its own).

**No schedule, cron line or step logic changes. No cost.**

If you upload only this one file: download
https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/t60r.yml
with **Download raw file**, then in
https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
(breadcrumb **gizmos-picks / .github / workflows**) click **Add file** →
**Upload files** → **choose your files**, pick `t60r.yml`, and commit with:

```
workflows: pin ubuntu-24.04, Node 24 actions, pinned Python (no cron change)
```

---

## Earlier upload (DONE — the deployed file matched this staged copy on 2026-09-24; kept as history)

~~UPLOAD BY HAND — `t60r.yml` (weekly backtest grading)~~

> ## ⚠️ SECOND UPLOAD NEEDED — 2026-09-22
> The first file I gave you was missing one line (the schedule "stamp"
> every cron workflow here carries), and the tests went red on `main`
> the moment it landed. **That was my mistake, not an upload problem.**
> The corrected file is at the same place. Follow the same steps below;
> GitHub will **replace** the existing `t60r.yml`. Commit message for
> this upload (paste it):
>
> ```
> t60r: add the schedule stamp to run-name (second upload)
> ```

**Why you and not me:** this file has a `cron:` block. GitHub credits
every scheduled run in the repo to whoever last changed a cron block. If
that becomes a bot, every schedule can stop firing silently. So a file
with a cron is always uploaded by you.

**What it does after this:** every Tuesday at 09:17 UTC it pulls the
college closing lines (2 CFBD calls, free tier), grades every played game
under the rule you approved, and commits the report. Nothing about it is
manual after the upload.

**Time: about 2 minutes.**

---

## Step 1 — upload the workflow file

1. The file to upload is on your PC at:
   `C:\Users\Senor\gizmos-picks\docs\upload\t60r.yml`
2. Go to **https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows**
3. Check the breadcrumb at the top of the file list reads
   **gizmos-picks / .github / workflows**. If it doesn't, you're in the
   wrong folder — go back to step 2.
4. Click the **Add file** button (top right, next to the green Code
   button) and choose **Upload files**.
5. Click **choose your files** — the blue link in the middle of the box.
   ⛔ Do not drag the folder in. Dragging a folder put 37 files one level
   too deep, twice, on 2026-09-22.
6. In the file picker, go to `C:\Users\Senor\gizmos-picks\docs\upload\`,
   click **t60r.yml**, and click **Open**.
7. Check the page now lists exactly one file: **t60r.yml**.
8. In the **Commit changes** box, put this in the first line (paste it):

```
t60r: weekly backtest grading, uploaded by hand (cron block)
```

9. Leave **Commit directly to the main branch** selected.
10. Click the green **Commit changes** button.

## Step 2 — tell me it's uploaded

Uploading a cron makes the repo's cron count 56, while `CLAUDE.md` says
55, so the test suite goes red until that number is corrected. That is
the check doing its job — it is how a cron added or lost by accident gets
noticed.

Say "t60r is uploaded" and I'll open a one-line pull request correcting
55 to 56 for you to merge. ⚠️ It has to be opened **after** the upload,
or its own check would be red for the opposite reason.

## Step 3 — check it works (optional, I can do this for you)

1. Go to **https://github.com/smh0602/gizmos-picks/actions**
2. In the left sidebar, click **t60r**.
3. Click **Run workflow** on the right, then the green **Run workflow**
   button, to run it once now rather than waiting for Tuesday.
4. It should finish green in a few minutes, and the run's log ends with
   the three numbers: 2025, 2026 and the combined verdict.

---

## Changelog

- **2026-09-23:** the "open a one-line pull request after the upload"
  step (Step 2) no longer applies to any future upload. Staged cron files
  now count toward `CRON TOTAL`, so an upload never turns the tests red.
  Kept above as history of how t60r was uploaded.
- **2026-09-22 (second upload):** ⚠️ **MISTAKE.** The first `t60r.yml`
  had no `run-name:` stamp, so `test_runs_report.py` went red on `main`
  when it landed. Root cause: the file sat in `docs/upload/`, which no
  workflow test read, so it reached Sam untested. Fixed by adding the
  stamp, and `test_runs_report.py` now checks every cron workflow staged
  in `docs/upload/` with the same reader it uses on the deployed ones.
- **2026-09-22:** first version.
- **2026-09-24:** the earlier upload was done; this file now describes the Ubuntu 26 / Node 24 update. The old steps are kept above, under "Earlier upload", as history — not deleted.
