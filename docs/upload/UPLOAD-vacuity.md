# UPLOAD BY HAND: `vacuity.yml`

## Current: give the nightly sweep two hours `[2026-10-02]`

**This file is uploaded together with `collect.yml`.** Follow
**`docs/upload/UPLOAD-collect.md`** (the "Current" section): it has every
click and the one commit message for both files. Do it after merging the
pull request "collect/pr-tests: give the vacuity sweep 5400s".

**Why:** the nightly "does every guard bite?" job runs the whole sweep
(tier 1 and tier 2). Its limit was 60 minutes. Tier 2 alone now needs
more than the old 40-minute test clock (collect #2093 timed out after
#218 added about 140 guard checks), so the nightly would soon be cancelled
and report nothing. The limit becomes **120 minutes**.
`test_vacuity_pool.py` requires it to be at least the 5,400 seconds a
pull request gives the same sweep.

**No schedule, cron line, step or cost changes.** Only the job's time
limit and its comment differ from the live file.

If you upload only this one file: download
https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/vacuity.yml
with **Download raw file**, then in
https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
(breadcrumb **gizmos-picks / .github / workflows**) click **Add file** →
**Upload files** → **choose your files**, pick `vacuity.yml`, and commit with:

```
vacuity.yml: give the nightly sweep 120 minutes (no cron change)
```

---

## ~~Current:~~ Done: the Ubuntu 26 / Node 24 update `[2026-09-24]`

✅ Uploaded: on 2026-10-02 the deployed `vacuity.yml` matched that staged
copy byte for byte.

**This file is one of 11 uploaded together.** Follow
**`docs/upload/UPLOAD-runner-image.md`**: it has every click and the
commit message. Do it after merging the pull request "Workflows: pin
Ubuntu 24.04, move to Node 24 actions, pin Python", before 2026-10-19.

`vacuity.yml` is the nightly "does every guard bite?" sweep. What changes in it:

1. `runs-on: ubuntu-latest` → `runs-on: ubuntu-24.04`, so GitHub moving
   `ubuntu-latest` to Ubuntu 26.04 on 2026-10-19 changes nothing here.
2. `actions/checkout@v4` → `@v5`: the
   Node 24 versions (GitHub is retiring Node 20).
3. Before it runs any Python, the job now installs **Python 3.12** itself (the version it gets today) instead of using the computer's, which becomes 3.14 on Ubuntu 26.04.

**No schedule, cron line or step logic changes. No cost.**

If you upload only this one file: download
https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/vacuity.yml
with **Download raw file**, then in
https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
(breadcrumb **gizmos-picks / .github / workflows**) click **Add file** →
**Upload files** → **choose your files**, pick `vacuity.yml`, and commit with:

```
workflows: pin ubuntu-24.04, Node 24 actions, pinned Python (no cron change)
```

---

## Earlier upload (DONE — the deployed file matched this staged copy on 2026-09-24; kept as history)

~~UPLOAD BY HAND: `vacuity.yml` (the nightly "does every guard bite?" job)~~

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
- **2026-09-24:** the earlier upload was done; this file now describes the Ubuntu 26 / Node 24 update. The old steps are kept above, under "Earlier upload", as history — not deleted.
- **2026-10-02:** the Ubuntu 26 / Node 24 upload was done. New current section: the nightly's limit goes from 60 to 120 minutes, uploaded with `collect.yml`. My mistake: PR #221 first raised the pull-request sweep clock to 5,400 s without raising this limit, and pr-tests failed on `test_vacuity_pool.py`, which I had not run.
