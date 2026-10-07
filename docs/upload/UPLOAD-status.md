# UPLOAD BY HAND: `status.yml` (a new workflow)

## Current: the weekly status email `[2026-10-07]`

**Do this after you merge the pull request "status: one plain weekly email,
and every alert says what to do".** It is one new file.

**Why:** your decision of 2026-10-07. With the scheduled Claude tasks off,
the repo writes to you itself: every Monday at 7:17am (6:17am in winter) it
updates the issue **Gizmo's Picks - weekly status**, assigned to you, and
posts the week as a comment, so GitHub emails you. Free. **One new cron
line (`17 11 * * 1`): the cron count goes from 57 to 58. No existing
workflow changes.**

### Click by click (Windows)

1. Open **File Explorer**, click **Downloads**, and delete any old
   `status.yml` there (otherwise Windows saves `status (1).yml`).
2. Open https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/status.yml
   and check the breadcrumb reads **gizmos-picks / docs / upload /
   status.yml**.
3. Click **Download raw file** (the small downward-arrow icon on the
   right, above the file's contents).
4. Open https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
   and check the breadcrumb reads **gizmos-picks / .github / workflows**.
   ⛔ Not the repo's front page: a file uploaded there never runs.
5. Click **Add file** (top right, next to the green **Code** button),
   then **Upload files**.
6. Click **choose your files** (the blue link in the middle of the box).
   ⛔ Do not drag a folder in. In **Downloads** pick `status.yml` and
   click **Open**.
7. Check the page lists exactly **1 file**, `status.yml`.
8. In the **Commit changes** box paste this as the first line:

   ```
   status.yml: the weekly status email (Sam, 2026-10-07; one new cron, Monday 11:17Z)
   ```

9. Leave **Commit directly to the main branch** selected and click the
   green **Commit changes** button.

**Afterwards:** for the first email now instead of Monday, open
**Actions**, click **status** on the left, then **Run workflow** (right)
and the green **Run workflow** button. Within a minute the issue exists,
starting "Nothing needs you this week." or "Needs you: ...". Not uploaded
within 48 hours of the merge, the runs report flags it.
