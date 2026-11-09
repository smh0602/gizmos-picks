# UPLOAD BY HAND: `collect.yml` (the two alerts stop closing issues they could not check)

**Do this after you merge the pull request "collect: the two alerts leave
their issue alone when they could not look".** It is one file. Time: about
5 minutes.

## What this is, in plain English

`collect.yml` has two steps that write to an issue for you:

1. **"the test suite is failing".** GitHub stops an older MLB run whenever a
   newer one starts. When that happened while the tests were still running,
   this step had no answer, read that as "the tests are green", posted
   "✅ Resolved" and **closed the issue**, even though the tests were still
   failing.
2. **"the watchdog says the site is wrong".** If the watchdog crashed, or its
   report could not be read, this step posted "✅ Resolved — the watchdog now
   reports the site healthy" and **closed the issue**. If the report could not
   be written out, it **replaced the issue's text with a blank page**. And if
   the watchdog crashed partway through, the step acted on the report left
   over from the run before.

After the upload, in every one of those cases the step **leaves the issue
exactly as it was** and says so in the run's log. Real results work as
before: green tests or a healthy site close the issue, and a real failure
opens or updates it. A real problem the watchdog found still reaches you even
if its second look, after trying a repair, crashes or the run is stopped
while repairing.

**No schedule, cron line or cost changes. The cron count does not change.**
All 44 `cron:` lines are byte-identical to the live file. Only three steps
differ: "Watchdog — check the product, repair what is repairable", "Tell
Sam" and "Tell Sam the tests are failing".

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
   collect.yml: the alerts leave their issue alone when they could not look (no cron change)
   ```

9. Leave **Commit directly to the main branch** selected and click the green
   **Commit changes** button. GitHub replaces the existing file.

## What you should see afterwards

Nothing different on the site, and normal runs look the same.

- When a run is stopped during its tests, the log of **Tell Sam the tests are
  failing** says `the Tests step never reported — leaving any open issue
  alone`, and the issue stays open.
- If the watchdog ever crashes, the run's page shows a yellow warning,
  `watchdog.py exited 1, so health.json is the last pass's — no verdict this
  run`, and the watchdog's issue is left as it was.

Until you upload, the "runs" report lists `collect.yml` as waiting, and after
48 hours it says so in an issue. I (or the next session) check after your
upload that the live file matches this one and that the next collect run is
green.

---

## Changelog

- **2026-11-04:** first version.
