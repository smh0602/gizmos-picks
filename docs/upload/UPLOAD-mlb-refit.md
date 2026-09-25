# UPLOAD BY HAND: `mlb-refit.yml`

## Current: the Ubuntu 26 / Node 24 update `[2026-09-24]`

**This file is one of 11 uploaded together.** Follow
**`docs/upload/UPLOAD-runner-image.md`**: it has every click and the
commit message. Do it after merging the pull request "Workflows: pin
Ubuntu 24.04, move to Node 24 actions, pin Python", before 2026-10-19.

`mlb-refit.yml` is the weekly MLB champion-vs-challenger refit. What changes in it:

1. `runs-on: ubuntu-latest` → `runs-on: ubuntu-24.04`, so GitHub moving
   `ubuntu-latest` to Ubuntu 26.04 on 2026-10-19 changes nothing here.
2. `actions/checkout@v4` → `@v5` and `actions/setup-python@v5` → `@v6`: the
   Node 24 versions (GitHub is retiring Node 20).
3. Its Python version does not change (it already installed its own).

**No schedule, cron line or step logic changes. No cost.**

If you upload only this one file: download
https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/mlb-refit.yml
with **Download raw file**, then in
https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
(breadcrumb **gizmos-picks / .github / workflows**) click **Add file** →
**Upload files** → **choose your files**, pick `mlb-refit.yml`, and commit with:

```
workflows: pin ubuntu-24.04, Node 24 actions, pinned Python (no cron change)
```

---

## Earlier upload (DONE — the deployed file matched this staged copy on 2026-09-24; kept as history)

~~UPLOAD BY HAND — `mlb-refit.yml` (weekly MLB champion vs challenger)~~

**Do this after the pull request that adds `mlb_refit.py` is merged.**
It takes about 2 minutes, and nothing else is needed afterwards: the job
runs every Monday at 11:43 UTC by itself.

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

That's all.

---

## Changelog

- **2026-09-23 (later):** ~~step 2, "tell me it's uploaded" for a
  cron-count pull request~~ and ~~step 3, a manual first run~~ removed.
  Sam: staged files now count toward `CRON TOTAL`, so the upload no longer
  turns the tests red, and the job runs on its own schedule.
- **2026-09-23:** first version.
- **2026-09-24:** the earlier upload was done; this file now describes the Ubuntu 26 / Node 24 update. The old steps are kept above, under "Earlier upload", as history — not deleted.
