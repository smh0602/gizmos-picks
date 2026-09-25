# UPLOAD BY HAND: 11 workflow files, one commit (the Ubuntu 26 / Node 24 fix)

**Do this after you merge the pull request "Workflows: pin Ubuntu 24.04,
move to Node 24 actions, pin Python". Do it before 2026-10-19.**
Time: about 10 minutes.

## What this is, in plain English

GitHub is changing the computer our scheduled jobs run on:

- From **2026-10-19** (rolling out until 11-19), `ubuntu-latest` becomes
  Ubuntu 26.04. Its built-in Python jumps from 3.12 to 3.14 and its
  system packages get renamed. Nine of our jobs used that built-in Python.
- GitHub is retiring **Node 20**, the engine two of our standard steps
  (`checkout@v4`, `setup-python@v5`) run on.

These 11 files change three things only ~~:~~ _(2026-09-25: `collect.yml` also carries a fourth, harmless one: the pr-tests split switch, left off. See `UPLOAD-collect.md`)_:

1. `runs-on: ubuntu-latest` becomes `runs-on: ubuntu-24.04`, so the 19th
   changes nothing for us.
2. `checkout@v4` becomes `@v5` and `setup-python@v5` becomes `@v6`, the
   Node 24 versions.
3. Every job that runs Python now installs Python 3.12 itself (the same
   version it gets today), instead of using the computer's.

**No schedule changes. No cron line changes. No cost.** The cron count
stays at 57.

**Why you and not me:** these files all have a `cron:` block. GitHub
credits every scheduled run to whoever last changed a file with a cron
block. If that became a bot, the schedules could stop silently.

---

## Step 1: clear old copies out of Downloads

1. Open **File Explorer** and click **Downloads** on the left.
2. If you see any file ending in **.yml** there (for example an older
   `vacuity.yml`), delete it. Otherwise Windows will save the new one as
   `vacuity (1).yml`, and the name must be exact.

## Step 2: download the 11 files

For **each** link below, do the same three things:

1. Open the link.
2. Check the breadcrumb at the top reads
   **gizmos-picks / docs / upload / <the file name>**.
3. Click **Download raw file**. It is the small downward-arrow icon on
   the right, above the file's contents.

| # | file | link |
|---|---|---|
| 1 | `browser.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/browser.yml |
| 2 | `budget.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/budget.yml |
| 3 | `calibration.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/calibration.yml |
| 4 | `cfbd.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/cfbd.yml |
| 5 | `collect.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/collect.yml |
| 6 | `mlb-refit.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/mlb-refit.yml |
| 7 | `owed_tests.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/owed_tests.yml |
| 8 | `runs.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/runs.yml |
| 9 | `self-repair.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/self-repair.yml |
| 10 | `t60r.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/t60r.yml |
| 11 | `vacuity.yml` | https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/vacuity.yml |

When you are done, **Downloads** holds exactly these 11 `.yml` files,
none with a `(1)` in its name.

## Step 3: upload all 11 into the workflows folder, in one commit

1. Go to **https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows**
2. Check the breadcrumb reads **gizmos-picks / .github / workflows**.
   If it doesn't, you are in the wrong folder; open the link again.
3. Click **Add file** (top right, next to the green **Code** button), then
   **Upload files**.
4. Click **choose your files**, the blue link in the middle of the box.
   ⛔ Do not drag a folder in. Dragging a folder put 37 files one level
   too deep, twice, on 2026-09-22.
5. In the file picker, open **Downloads**. Click the first `.yml` file,
   then hold **Ctrl** and click each of the other ten, so all 11 are
   highlighted. Click **Open**.
6. Check the page lists exactly **11 files**, all names from the table
   above, none with `(1)`.
7. In the **Commit changes** box, paste this as the first line:

```
workflows: pin ubuntu-24.04, Node 24 actions, pinned Python (no cron change)
```

8. Leave **Commit directly to the main branch** selected.
9. Click the green **Commit changes** button. GitHub replaces the 11
   existing files.

## Step 4: nothing else

No follow-up pull request is needed. Until you upload, the nightly
"runs" report lists these files as waiting; after 48 hours it says so in
an issue. Once uploaded they stop being listed, and I (or the next
session) check the next scheduled run of each is green.

**What stays for later, not now:** moving from 24.04 to 26.04. Every pull
request now also runs the test suite and the page tests on 26.04 (the
"tests (ubuntu-26.04)" and "render (ubuntu-26.04)" checks). When those
have been green for a while, a later PR stages the one-line change.

---

## Changelog

- **2026-09-25:** `collect.yml` now also carries the pr-tests split switch
  (off there). Upload it after merging "pr-tests: run the vacuity sweep as
  parallel parts" and this one upload delivers both; if you already
  uploaded, `UPLOAD-collect.md` has the one-file steps.
- **2026-09-24:** first version.
