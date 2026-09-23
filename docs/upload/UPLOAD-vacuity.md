# UPLOAD BY HAND: `vacuity.yml` (the nightly "does every guard bite?" job)

**Why you and not me:** this file has a `cron:` block. GitHub credits
every scheduled run in the repo to whoever last changed a cron block. If
that became a bot, every schedule could stop firing silently. So a file
with a cron is always uploaded by you.

**What changes:** one number. The nightly job's time limit goes from
**30 minutes to 60**. The schedule, the checks and the issue it files do
not change.

**Why:** the job was **cancelled at 30 minutes on 09-22 and 09-23**. Its
sweep had grown past the limit, so for two nights nobody checked whether
the guards bite. PR #145 makes the sweep about twice as fast, but on
GitHub's slowest machines it would still come within a couple of minutes
of 30. 60 gives it room.

**Do this after merging PR #145.** Time: about 3 minutes.

---

## Step 1: download the file from GitHub

1. Go to **https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/vacuity.yml**
2. Check the breadcrumb at the top reads
   **gizmos-picks / docs / upload / vacuity.yml**.
3. Click the **Download raw file** button. It is the small
   downward-arrow icon on the right, above the file's contents.
4. It saves to your **Downloads** folder as `vacuity.yml`. If Windows
   names it `vacuity (1).yml` because an older one is there, delete the
   older one first and download again. The uploaded name must be
   exactly `vacuity.yml`.

## Step 2: upload it into the workflows folder

1. Go to **https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows**
2. Check the breadcrumb reads **gizmos-picks / .github / workflows**.
   If it doesn't, you are in the wrong folder. Go back to step 1 of this
   section.
3. Click **Add file** (top right, next to the green Code button), then
   **Upload files**.
4. Click **choose your files**, the blue link in the middle of the box.
   ⛔ Do not drag a folder in. Dragging a folder put 37 files one level
   too deep, twice, on 2026-09-22.
5. In the file picker, open your **Downloads** folder, click
   **vacuity.yml**, and click **Open**.
6. Check the page lists exactly one file: **vacuity.yml**.
7. In the **Commit changes** box, paste this as the first line:

```
vacuity: give the nightly sweep 60 minutes (it was cancelled at 30)
```

8. Leave **Commit directly to the main branch** selected.
9. Click the green **Commit changes** button. GitHub replaces the
   existing `vacuity.yml`.

## Step 3: nothing else

The cron count does not change (it is still one cron), so no follow-up
pull request is needed. The next nightly run is at 06:47 UTC (2:47am ET).
I will check it finished green and inside the new limit.

`test_vacuity_pool.py` knows this upload is pending. It reports it as a
note until the deployed file matches this one, and from then on it fails
if the nightly limit ever drops below the 2400 seconds a PR gives the
same sweep.

---

## Changelog

- **2026-09-23:** first version.
