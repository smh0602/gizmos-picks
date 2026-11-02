# UPLOAD BY HAND: 6 workflow files, one commit (the nightly sweep finishes)

**Do this after you merge the pull request "The nightly sweep finishes, and
the watchers stop wiping their issues".** Time: about 10 minutes.

## What this is, in plain English

Every night a job checks that the site's safety checks can actually fail
("does every guard bite?"). It had grown too big for one computer and its
two-hour limit: it ran out of time on **9 of its last 15 nights**. When it
ran out of time it had nothing to say, and the step that updates the issue
read "nothing" as a problem and **wrote a blank page over issue #249**. The
same mistake was in all six of these files.

These 6 files change two things:

1. `vacuity.yml`: the nightly check now runs on **four computers at once**,
   each with its own two hours, and a fifth job writes the one report. If
   one computer runs out of time, the other three still report, and the
   report says which one is missing.
2. All 6 files: when a job dies or crashes before it finishes, its "Tell Sam"
   step now leaves the issue alone instead of overwriting it.

**No schedule changes. No cron line changes. No cost:** these run on GitHub's
free computers and make no paid call. The cron count stays the same.

**Why you and not me:** these files all have a `cron:` block. GitHub credits
every scheduled run to whoever last changed a file with a cron block. If that
became a bot, the schedules could stop silently.

---

## Step 1: clear old copies out of Downloads

1. Open **File Explorer** and click **Downloads** on the left.
2. If you see any file ending in **.yml** there (for example an older
   `vacuity.yml`), delete it. Otherwise Windows will save the new one as
   `vacuity (1).yml`, and the name must be exact.

## Step 2: download the 6 files

For **each** link below, do the same three things:

1. Open the link.
2. Check the breadcrumb at the top reads
   **gizmos-picks / docs / upload / <the file name>**.
3. Click **Download raw file**. It is the small downward-arrow icon on the
   right, above the file's contents.

| # | file | link |
|---|---|---|
| 1 | `budget.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/budget.yml |
| 2 | `calibration.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/calibration.yml |
| 3 | `cfbd.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/cfbd.yml |
| 4 | `owed_tests.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/owed_tests.yml |
| 5 | `runs.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/runs.yml |
| 6 | `vacuity.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/vacuity.yml |

When you are done, **Downloads** holds exactly these 6 `.yml` files, none
with a `(1)` in its name.

## Step 3: upload all 6 into the workflows folder, in one commit

1. Go to **https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows**
2. Check the breadcrumb reads **gizmos-picks / .github / workflows**. If it
   doesn't, you are in the wrong folder; open the link again.
3. Click **Add file** (top right, next to the green **Code** button), then
   **Upload files**.
4. Click **choose your files**, the blue link in the middle of the box.
   ⛔ Do not drag a folder in. Dragging a folder put 37 files one level too
   deep, twice, on 2026-09-22.
5. In the file picker, open **Downloads**. Click the first `.yml` file, then
   hold **Ctrl** and click each of the other five, so all 6 are highlighted.
   Click **Open**.
6. Check the page lists exactly **6 files**, all names from the table above,
   none with `(1)`.
7. In the **Commit changes** box, paste this as the first line:

```
workflows: the nightly sweep finishes, watchers stop wiping issues (no cron change)
```

8. Leave **Commit directly to the main branch** selected.
9. Click the green **Commit changes** button. GitHub replaces the 6 existing
   files.

## Step 4: what you should see

No follow-up pull request is needed. Until you upload, the old nightly keeps
running exactly as it does today; after 48 hours the "runs" report says these
files are waiting.

After you upload, the next nightly run starts at 06:47 UTC (1:47am ET in
winter, 2:47am ET in summer), though GitHub has been starting it hours late:

- Go to **https://github.com/smh0602/gizmos-picks/actions/workflows/vacuity.yml**
  and open the newest run. It should show **sweep (1)**, **sweep (2)**,
  **sweep (3)**, **sweep (4)** and then **watch**, all green, in about an hour.
- **Issue #249 fills back in.** It is blank today because of this bug. Its
  findings were still true when last checked, so expect them back; they are
  real and are a separate job, not a sign this upload went wrong.

I (or the next session) check that first run. If **watch** shows a red X, one
of the four did not report, and nothing is lost:

- If the other three found nothing, the issue was left exactly as it was.
- If they found something, it was added to issue #249 as a comment that names
  the missing part. The issue's main text was left as it was.

Either way the next night that all four finish puts it right by itself.

---

## Changelog

- **2026-11-01:** first version.
