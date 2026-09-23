# UPLOAD BY HAND — `mlb-refit.yml` (weekly MLB champion vs challenger)

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
