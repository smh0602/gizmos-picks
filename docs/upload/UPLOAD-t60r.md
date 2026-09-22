# UPLOAD BY HAND — `t60r.yml` (weekly backtest grading)

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
