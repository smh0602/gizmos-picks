# UPLOAD BY HAND: `collect.yml` (the 320-minute hold counts from the start of the run)

**Do this after you merge the pull request "Sweep clock headroom".** It is one
file. Time: about 5 minutes. Please do it soon: a held run is now within
minutes of being stopped by its own clock.

## What this is, in plain English

The scheduled MLB runs stay open for 320 minutes, checking the site every
15 minutes, and then hand over to the next run (the relay you asked for on
2026-10-06). GitHub stops any run at 350 minutes, so 30 minutes are meant to be
spare.

They are not spare any more. The 320 minutes were counted from **after** the
tests that run at the start of every collect run, and those tests now take
10 to 30 minutes (29.9 on 11-11, and growing as tests are added). So a held run
lasted tests + 320 + its last check. Measured from GitHub: on 11-11 a run took
**348.9 of its 350 minutes, 11 seconds from being stopped**, and most held runs
this week took 340 to 344 minutes.

A run stopped at 350 minutes is marked "cancelled": its last check may not be
saved, and it never starts the next run in the relay, so the site waits for the
next scheduled start.

After the upload the 320 minutes are counted from the **start** of the run,
whatever the tests take. Each held run ends about 320 to 330 minutes in, with
the 30 spare minutes left for its last check alone. The relay still hands over
at the end, as before.

**Nothing else changes.** No schedule, cron line or cost changes, and the cron
count does not change: all 43 `cron:` lines are byte-identical to the live
file. One new first step, "Start the hold's clock", writes down the time the
run started, and one line of "Converge and hold" counts from it. A one-pass run
(a push, a football run, a hand-run) does exactly what it does today.

**Why you and not me:** this file has a `cron:` block. GitHub credits every
scheduled run to whoever last changed a file with a cron block. If that
became a bot, the schedules could stop silently.

---

## Click by click (Windows)

1. Open **File Explorer**, click **Downloads**, and delete any old
   `collect.yml` there (otherwise Windows saves `collect (1).yml`, and the
   name must be exact).
2. Open https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/collect.yml
   and check the breadcrumb at the top reads **gizmos-picks / docs / upload /
   collect.yml**.
3. Click **Download raw file** (the small downward-arrow icon on the right,
   above the file's contents).
4. Open https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
   and check the breadcrumb reads **gizmos-picks / .github / workflows**.
   ⛔ Not the repo's front page: a file uploaded there lands in the top
   level, where it never runs.
5. Click **Add file** (top right, next to the green **Code** button), then
   **Upload files**.
6. Click **choose your files** (the blue link in the middle of the box).
   ⛔ Do not drag a folder in. In **Downloads** pick `collect.yml` and click
   **Open**.
7. Check the page lists exactly **1 file**, `collect.yml`, with no `(1)` in
   its name.
8. In the **Commit changes** box paste this as the first line:

   ```
   collect.yml: the 320-minute hold counts from the start of the run, not after the tests (no cron change)
   ```

9. Leave **Commit directly to the main branch** selected and click the green
   **Commit changes** button. GitHub replaces the existing file.

## What you should see afterwards

Nothing different on the site.

- On the **Actions** page, a scheduled MLB collect run now lists a first step
  called **Start the hold's clock**, and a held run finishes about 320 to 330
  minutes after it started instead of 340 to 349.
- The Monday status email's "Job clocks" section, and health.json, read collect
  by how long it ran past its hold. Until the upload that reads 75% or more
  (DEGRADED, "Count the hold from the job's start"); about a week after the
  upload, once the older runs leave the 7-day window, it should go quiet.

Until you upload, the "runs" report lists `collect.yml` as waiting, and after
48 hours it says so in an issue. I (or the next session) check after your
upload that the live file matches this one and that the next held collect run
is green and ends before 330 minutes.

---

## Changelog

- **2026-11-17:** first version.
