# UPLOAD BY HAND: `browser.yml` (the render tests run once, not twice)

**Do this after you merge the pull request "browser: run the render tests
once, not twice".** It is one file. Time: about 5 minutes.

## What this is, in plain English

`browser.yml` is the twice-daily page check: it opens the site in a real
browser and runs the five page ("render") test files. Its last step, "A
skipped render check is a failure in THIS workflow", ran all five files
**a second time**, only to look for the words "NO BROWSER HERE" in what they
printed. So every run did the page tests twice: about 400 seconds each time,
on all 20 runs up to 11-21. On a day GitHub's install step is slow (446
seconds on 11-19), the job reached 1273 of its 1500 seconds (85%), and the
watchdog reported `clock:browser` as DEGRADED.

After the upload, the "Render tests" step runs each file once and keeps what
they print in a log of its own, and the last step reads that log instead of
running them again. It still fails on any "NO BROWSER HERE" line, as before.
It also fails if it has no log to read (for example when an earlier step
failed and "Render tests" never ran), and if the log is missing any of the
five files: a check that cannot see what it checks fails, it never passes.

**No schedule, cron line, trigger or cost changes. The cron count does not
change.** Both `cron:` lines, the triggers and paths, the 25-minute clock,
the image and the action versions are byte-identical to the live file. Only
the two steps "Render tests" and "A skipped render check is a failure in
THIS workflow" differ. Every render check still runs, once.

**Why you and not me:** this file has a `cron:` block. GitHub credits every
scheduled run to whoever last changed a file with a cron block. If that
became a bot, the schedules could stop silently.

---

## Click by click (Windows)

1. Open **File Explorer**, click **Downloads**, and delete any old
   `browser.yml` there (otherwise Windows saves `browser (1).yml`, and the
   name must be exact).
2. Open https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/browser.yml
   and check the breadcrumb at the top reads **gizmos-picks / docs / upload /
   browser.yml**.
3. Click **Download raw file** (the small downward-arrow icon on the right,
   above the file's contents).
   If you cannot see that icon: click **Raw** instead, press **Ctrl+S**, and
   in the Save box pick **Downloads**, set **Save as type** to **All Files
   (\*.\*)**, set **File name** to exactly `browser.yml` (not
   `browser.yml.txt`), and click **Save**.
4. Open https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
   and check the breadcrumb reads **gizmos-picks / .github / workflows**.
   ⛔ Not the repo's front page: a file uploaded there lands in the top
   level, where it never runs.
5. Click **Add file** (top right, next to the green **Code** button), then
   **Upload files**.
6. Click **choose your files** (the blue link in the middle of the box).
   ⛔ Do not drag a folder in. In **Downloads** pick `browser.yml` and click
   **Open**.
7. Check the page lists exactly **1 file**, `browser.yml`, with no `(1)` in
   its name.
8. In the **Commit changes** box paste this as the first line:

   ```
   browser.yml: run the render tests once; the skip check reads their log (no cron change)
   ```

9. Leave **Commit directly to the main branch** selected and click the green
   **Commit changes** button. GitHub replaces the existing file.

## What you should see afterwards

Nothing different on the site: the page and what it is tested on are
unchanged.

- Your upload itself starts a browser run within a minute or two (a change
  to `browser.yml` is one of its triggers). On the **Actions** page, click
  **browser** on the left; the new run is called **browser [push]**.
- Its **render** job takes about 7-8 minutes instead of about 14-15 (about
  14 instead of 21 on a day the install is slow).
- **How to tell it worked:** open that run, click **render**, and look at the
  last step, **A skipped render check is a failure in THIS workflow**. It now
  takes about a second (it took about 400 seconds) and its last line says
  `every render file had a browser`. The step above it, **Render tests**,
  still lists the five files and ends with `ran 5 render test file(s)`.
- The watchdog's `clock:browser` warning looks back 7 days, so it goes away
  about a week after the last slow run before your upload (the last run
  over 75% was on 11-20), as long as no new run passes 75% of the clock.

Until you upload, the "runs" report lists `browser.yml` as waiting, and after
48 hours it says so in an issue. I (or the next session) check after your
upload that the live file matches this one and that the next browser run is
green.

## If you need to undo it

This puts back the file that was live before your upload.

1. Open **File Explorer**, click **Downloads**, and delete any old
   `browser.yml` there.
2. Open
   https://github.com/smh0602/gizmos-picks/blob/85c434f01b14146062e2fb4ac753ccbc7ef8013a/.github/workflows/browser.yml
   Its breadcrumb reads **gizmos-picks / .github / workflows / browser.yml**
   (not docs / upload): that is correct for this link, because it is the old
   live file. The branch button above the file shows `85c434f` instead of
   `main`; that is expected too.
3. Download it exactly as in step 3 above (**Download raw file**, or **Raw**,
   **Ctrl+S**, **All Files (\*.\*)**, file name exactly `browser.yml`).
4. Do steps 4 to 7 above unchanged: the **.github / workflows** page, **Add
   file**, **Upload files**, **choose your files**, exactly **1 file**.
5. In the **Commit changes** box paste this as the first line:

   ```
   browser.yml: back to the previous version (render tests run twice; no cron change)
   ```

6. Leave **Commit directly to the main branch** selected and click the green
   **Commit changes** button.

The render job is then about 7 minutes longer again, as it was before. Tell
me too, so the staged copy in `docs/upload/` is put back to match (until it
is, the "runs" report lists `browser.yml` as waiting again).

---

## Changelog

- **2026-11-21:** first version.
- **2026-11-21 (review, before merge):** the undo is its own numbered list.
  The first version sent you to step 2, whose breadcrumb check
  (docs / upload) the undo link cannot pass: that link is the old live file,
  under .github / workflows.
