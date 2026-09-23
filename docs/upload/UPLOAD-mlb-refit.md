# UPLOAD BY HAND — `mlb-refit.yml` (weekly MLB champion vs challenger)

**Why you and not me:** this file has a `cron:` block. GitHub credits every
scheduled run in the repo to whoever last changed a cron block. If that
becomes a bot, every schedule can stop firing silently. So a file with a
cron is always uploaded by you.

**What it does after this:** every Monday at 11:43 UTC it does three
things:
- pulls the week's MLB games from statsapi (free);
- re-fits the challenger and scores it against v5.0 under your rule;
- updates the "Is v5.0 still the best version?" panel on the Track Record
  tab.

If the challenger ever qualifies, it opens **one** pull request titled
"[ASK SAM] MLB challenger qualified" for you to decide. It never changes
the card by itself.

**Time: about 2 minutes. Upload this only after the pull request that adds
`mlb_refit.py` is merged.** The workflow runs that file, so it has to be
on `main` first.

---

## Step 1: upload the workflow file

1. The file to upload is on your PC at:
   `C:\Users\Senor\gizmos-picks\docs\upload\mlb-refit.yml`
2. Go to **https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows**
3. Check the breadcrumb at the top of the file list reads
   **gizmos-picks / .github / workflows**. If it doesn't, go back to step 2.
4. Click **Add file** (top right, next to the green Code button), then
   **Upload files**.
5. Click **choose your files**, the blue link in the middle of the box.
   ⛔ Don't drag the folder in.
6. In the file picker, go to `C:\Users\Senor\gizmos-picks\docs\upload\`,
   click **mlb-refit.yml**, and click **Open**.
7. Check the page lists exactly one file: **mlb-refit.yml**.
8. In the **Commit changes** box, put this in the first line (paste it):

```
mlb-refit: weekly champion vs challenger, uploaded by hand (cron block)
```

9. Leave **Commit directly to the main branch** selected.
10. Click the green **Commit changes** button.

## Step 2: tell me it's uploaded

Uploading a cron makes the repo's cron count one higher than `CLAUDE.md`
says, so the test suite goes red until that number is corrected. Say
"mlb-refit is uploaded" and I'll open the one-line pull request that
corrects it.

## Step 3: run it once (optional, I can do this for you)

1. Go to **https://github.com/smh0602/gizmos-picks/actions**
2. In the left sidebar, click **mlb-refit**.
3. Click **Run workflow** on the right, then the green **Run workflow**
   button.
4. It should finish green in about 10 minutes. The Track Record tab then
   shows the new panel.

---

## Changelog

- **2026-09-23:** first version.
