# UPLOAD BY HAND: `collect.yml` (a hand-run of one mode runs that mode alone)

**Do this after you merge the pull request "collect: a hand-run named with
converge-off runs that one mode alone".** It is one file. Time: about 5
minutes.

## What this is, in plain English

When a Claude session starts a collect run by hand, the run form lets it
type a mode followed by `converge-off`, for example `card-fb converge-off`.
The form says that runs that one job **alone**. It did not: the run split
the two words into two separate jobs, so `card-fb` ran the normal way and
also rebuilt everything else that was overdue, and `converge-off` on its own
did nothing. Measured on 2026-11-11: a run asked for the college card alone
and rebuilt three things.

It only ever rebuilt things that were already overdue, so it never cost
credits. After the upload, the word stays with the job it belongs to and the
form does what it says.

**Scheduled runs do not change.** No schedule, cron line or cost changes, and
the cron count does not change: all 44 `cron:` lines are byte-identical to
the live file. Only one step differs, "Converge and hold", and only for a run
whose mode list includes `converge-off`, which no scheduled run uses.

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
   collect.yml: a hand-run named with converge-off runs that one mode alone (no cron change)
   ```

9. Leave **Commit directly to the main branch** selected and click the green
   **Commit changes** button. GitHub replaces the existing file.

## What you should see afterwards

Nothing different on the site, and scheduled runs look the same.

- The next time a session hand-runs, for example, `card-fb converge-off`, the
  run's log shows `collect.py card-fb converge-off` doing only the card, with
  no `PLAN:` line listing other jobs.
- ⚠️ If something else happens to be overdue at that moment, that run no
  longer repairs it, so its last check can report it out of date and the run
  shows red. That is the truthful answer for a run told to do one job, and the
  next scheduled run repairs it as usual.

Until you upload, the "runs" report lists `collect.yml` as waiting, and after
48 hours it says so in an issue. I (or the next session) check after your
upload that the live file matches this one and that the next collect run is
green.

---

## Changelog

- **2026-11-11:** first version.
