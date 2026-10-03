# UPLOAD BY HAND: `collect.yml`

## Current: collect stops running the guard sweep `[2026-10-02]`

**Do this after you merge the pull request "collect: run the tests
without the 33-minute guard sweep" (its description links to this
file).** It is one file and one change.

**Why:** your decision of 2026-10-02. collect's Tests step runs before it
pulls any data, and it ran the whole guard sweep (`test_vacuity.py`):
33 minutes in collect #2092, and it timed out at 40 minutes in #2093. So
every data pull started 35+ minutes into its run. The sweep checks the
tests, not the data, and it still runs in full on every pull request and
every night. With it out, collect's Tests step takes about 7 minutes
(measured from #2092 and #2095).

**No schedule, cron line or cost changes. The cron count does not
change.** The only difference from the live file is six added lines on
the Tests step: a comment and `SUITE_SHARD: rest`.

### Click by click (Windows)

1. Open **File Explorer**, click **Downloads**, and delete any old
   `collect.yml` there (otherwise Windows saves `collect (1).yml`).
2. Open https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/collect.yml
   and check the breadcrumb reads **gizmos-picks / docs / upload /
   collect.yml**.
3. Click **Download raw file** (the small downward-arrow icon on the
   right, above the file's contents).
4. Open https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
   and check the breadcrumb reads **gizmos-picks / .github / workflows**.
   ⛔ Not the repo's front page: a file uploaded there lands in the top
   level, where it never runs.
5. Click **Add file** (top right, next to the green **Code** button),
   then **Upload files**.
6. Click **choose your files** (the blue link in the middle of the box).
   ⛔ Do not drag a folder in. In **Downloads** pick `collect.yml` and
   click **Open**.
7. Check the page lists exactly **1 file**, `collect.yml`.
8. In the **Commit changes** box paste this as the first line:

   ```
   collect.yml: run the rest share of the tests, not the guard sweep (Sam, 2026-10-02; no cron change)
   ```

9. Leave **Commit directly to the main branch** selected and click the
   green **Commit changes** button.

**What you should see afterwards:** the next collect run's Tests step
takes about 7 minutes instead of about 40, and its log says `ran 163 of
164 test file(s) (shard rest)` (the counts grow as tests are added). The
data steps start that much sooner. The sweep keeps running on every pull
request and in the nightly vacuity run. Until you upload, the nightly
"runs" report lists `collect.yml` as waiting.

---

## ~~Current:~~ Done: give the mutation sweep enough time `[2026-10-02]`

✅ Uploaded: commit c8ba424c on 2026-10-02 made the live `collect.yml` and
`vacuity.yml` match these staged copies byte for byte.

**Do this after you merge the pull request "collect/pr-tests: give the
vacuity sweep 5400s" (its description links to this file).** It is two
files uploaded together, `collect.yml` and `vacuity.yml`, in one commit.

**Why:** every collect run since #218 merged has gone red in its Tests
step: `test_vacuity.py TIMED OUT after 2400s`. Nothing failed; the sweep
that proves every test's guards still bite simply needs longer now. It
took 33 minutes before #218 (collect #2092) and #218 added about 140
guard checks. The new limit, 5400 seconds (90 minutes), is the same
margin as the last raise. The sweep itself is not shortened or skipped.
`pr-tests.yml` already carries the same number from the merge; this
upload brings the collector in line. The nightly sweep (`vacuity.yml`)
runs the whole sweep, so its job limit goes from 60 to 120 minutes;
`test_vacuity_pool.py` requires it to be at least 5,400 seconds.

**No schedule, cron line or cost changes. The cron count does not
change.** In each file only one number and its comment differ from the
live file.

### Click by click (Windows)

1. Open **File Explorer**, click **Downloads**, and delete any old
   `collect.yml` or `vacuity.yml` there (otherwise Windows saves
   `collect (1).yml`).
2. Open https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/collect.yml
   and check the breadcrumb reads **gizmos-picks / docs / upload /
   collect.yml**.
3. Click **Download raw file** (the small downward-arrow icon on the
   right, above the file's contents). Then do the same for
   https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/vacuity.yml
   (breadcrumb **gizmos-picks / docs / upload / vacuity.yml**).
4. Open https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
   and check the breadcrumb reads **gizmos-picks / .github / workflows**.
   ⛔ Not the repo's front page: a file uploaded there lands in the top
   level, where it never runs.
5. Click **Add file** (top right, next to the green **Code** button),
   then **Upload files**.
6. Click **choose your files** (the blue link in the middle of the box).
   ⛔ Do not drag a folder in. In **Downloads** click `collect.yml`,
   hold **Ctrl** and click `vacuity.yml`, then click **Open**.
7. Check the page lists exactly **2 files**, `collect.yml` and
   `vacuity.yml`.
8. In the **Commit changes** box paste this as the first line:

   ```
   collect.yml + vacuity.yml: give the vacuity sweep 5400s and the nightly 120 min (no cron change)
   ```

9. Leave **Commit directly to the main branch** selected and click the
   green **Commit changes** button.

**What you should see afterwards:** the next collect run's Tests step
finishes instead of stopping at `test_vacuity.py TIMED OUT after 2400s`,
and collect runs go green again; the next nightly vacuity run (06:47 UTC)
finishes inside its new limit. Until you upload, the nightly "runs"
report lists both files as waiting, and after 48 hours it says so in an
issue.

---

## ~~Current:~~ Done: the watchdog's repairs stop converging `[2026-09-28]`

✅ Uploaded: on 2026-10-02 the deployed `collect.yml` matched that staged
copy byte for byte.

**Do this after you merge the pull request that changed
`docs/upload/collect.yml` on 2026-09-28 (its description links to this
file).** It is one file, and one upload carries all three changes:

1. **The watchdog's repair runs only the repair.** On 9/28, collect run
   #1953 reported "alt-lines failed for nfl — it left an artifact out of
   contract". Nothing paid had failed. The watchdog chose to rebuild the
   card, and ran the collector with the Odds key blanked. The collector
   treats every run as a chance to catch up, so it also tried every paid
   pull that was due. Each one stopped at "ODDS_API_KEY is not set" (no
   credits were spent), and each was reported as a failure. After the
   upload, each repair line says `converge-off`: it rebuilds the one free
   thing it names and nothing else. The regular converge loop, which has
   the key, still catches up everything that is late.
2. **verify_card's output goes to a temporary file of its own** instead of
   the fixed `/tmp/vc.txt`. A test runs this step. Two copies at once on
   one computer would read each other's result. On GitHub each job has
   its own computer, so the live step was never wrong.
3. **The watchdog's report is only printed.** It was also copied into two
   files in `/tmp` that nothing ever read.

The other half of the fix does **not** need this upload. `collect.py` now
makes `card` and `record` do nothing under a football league, and
`card-fb` do nothing under MLB. On 9/20 a repair of `card-fb` under MLB
wrote `data/latest/t54.json` into MLB's folder (commit 027d7215). That
works from the merge.

**No schedule, cron line or cost changes. The cron count stays at 57.**
All 43 cron lines are the same as the live file's, byte for byte.

### Click by click (Windows)

1. Open **File Explorer**, click **Downloads**, and delete any old
   `collect.yml` there (otherwise Windows saves `collect (1).yml`).
2. Open https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/collect.yml
   and check the breadcrumb reads **gizmos-picks / docs / upload /
   collect.yml**.
3. Click **Download raw file** (the small downward-arrow icon on the
   right, above the file's contents).
4. Open https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
   and check the breadcrumb reads **gizmos-picks / .github / workflows**.
   ⛔ Not the repo's front page: a file uploaded there lands in the top
   level, where it never runs.
5. Click **Add file** (top right, next to the green **Code** button),
   then **Upload files**.
6. Click **choose your files** (the blue link in the middle of the box).
   ⛔ Do not drag a folder in. In **Downloads** pick `collect.yml` and
   click **Open**.
7. Check the page lists exactly **1 file**, `collect.yml`.
8. In the **Commit changes** box paste this as the first line:

   ```
   collect.yml: watchdog repairs run converge-off; verify_card output in a per-run temp file (no cron change)
   ```

9. Leave **Commit directly to the main branch** selected and click the
   green **Commit changes** button.

**What you should see afterwards:** nothing different on the site. The
next time the watchdog repairs something, its log line
`watchdog attempting repair: card` is followed by one short run per
league. The football ones say `card is the MLB card; nfl builds its card
with card-fb. Nothing done.` There are no `PLAN:` lines and no
"ODDS_API_KEY is not set" lines, and `data/latest/runs.json` stops showing
"... failed for nfl (exit 1) — it left an artifact out of contract" from
that step. Until you upload, the nightly "runs" report lists `collect.yml`
as waiting, and after 48 hours it says so in an issue.

---

## ~~Current:~~ Done: the Ubuntu 26 / Node 24 update, plus the faster PR tests `[2026-09-25]`

✅ Uploaded: on 2026-09-25 (commit eb5bc2a4, "Add files via upload") the
deployed `collect.yml` matched that staged copy; checked again on
2026-09-28.

The staged `collect.yml` ~~now carries~~ carried **two** changes, and one
upload delivered both:

1. **The Ubuntu 26 / Node 24 update** (from the pull request "Workflows:
   pin Ubuntu 24.04, move to Node 24 actions, pin Python"), exactly as
   described under 2026-09-24 below.
2. **The faster PR tests** (from the pull request "pr-tests: run the
   vacuity sweep as parallel parts"): the Tests step gains a switch that
   lets a pull request split the test run across several machines at
   once. **In `collect.yml` the switch is never set, so the collector
   still runs every test file, one after another, exactly as it does
   today.** It is here only because a test (`test_pr_tests.py`) requires
   the PR check and the collector to run the very same test loop.

**No schedule, cron line or cost changes. The cron count stays at 57.**

### ~~Which steps to follow~~ — done on 2026-09-25; use the section at the top

- **You have NOT yet done the 11-file upload in
  `UPLOAD-runner-image.md`:** do that one, after merging the pull request
  "pr-tests: run the vacuity sweep as parallel parts". Its `collect.yml`
  link points at `main`, so it downloads the file with both changes.
  Nothing else to do.
- **You ALREADY did the 11-file upload:** upload `collect.yml` once more,
  on its own, after merging the pull request above:

  1. Open **File Explorer**, click **Downloads**, and delete any old
     `collect.yml` there (otherwise Windows saves `collect (1).yml`).
  2. Open https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/collect.yml
     and check the breadcrumb reads **gizmos-picks / docs / upload /
     collect.yml**.
  3. Click **Download raw file** (the small downward-arrow icon on the
     right, above the file's contents).
  4. Open https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
     and check the breadcrumb reads **gizmos-picks / .github / workflows**.
  5. Click **Add file** (top right, next to the green **Code** button),
     then **Upload files**.
  6. Click **choose your files** (the blue link in the middle of the box).
     ⛔ Do not drag a folder in. In **Downloads** pick `collect.yml` and
     click **Open**.
  7. Check the page lists exactly **1 file**, `collect.yml`.
  8. In the **Commit changes** box paste this as the first line:

     ```
     collect.yml: same test loop as pr-tests, split switch left off (no cron change)
     ```

  9. Leave **Commit directly to the main branch** selected and click the
     green **Commit changes** button.

**What you should see afterwards:** nothing different on the site. The
next `collect` run's "Tests" step ends with a line like
`ran 133 of 133 test file(s) (shard all)`, where it used to say
`ran 133 test file(s)`. The count grows as tests are added; what matters
is that **both numbers are the same** (the step goes red if they are not). Until you upload, the nightly "runs" report lists
`collect.yml` as waiting and after 48 hours says so in an issue.

---

## ~~Current:~~ the Ubuntu 26 / Node 24 update `[2026-09-24]`

**This file is one of 11 uploaded together.** Follow
**`docs/upload/UPLOAD-runner-image.md`**: it has every click and the
commit message. Do it after merging the pull request "Workflows: pin
Ubuntu 24.04, move to Node 24 actions, pin Python", before 2026-10-19.

`collect.yml` is the collector: every data pull, card and grading job. What changes in it:

1. `runs-on: ubuntu-latest` → `runs-on: ubuntu-24.04`, so GitHub moving
   `ubuntu-latest` to Ubuntu 26.04 on 2026-10-19 changes nothing here.
2. `actions/checkout@v4` → `@v5` and `actions/setup-python@v5` → `@v6`: the
   Node 24 versions (GitHub is retiring Node 20).
3. Its Python version does not change (it already installed its own).

**No schedule, cron line ~~or step logic~~ changes. No cost.**
_(2026-09-25: the Tests step's logic now changes too, see above. With the
switch left off it runs exactly what it ran before.)_

If you upload only this one file: download
https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/collect.yml
with **Download raw file**, then in
https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
(breadcrumb **gizmos-picks / .github / workflows**) click **Add file** →
**Upload files** → **choose your files**, pick `collect.yml`, and commit with:

```
workflows: pin ubuntu-24.04, Node 24 actions, pinned Python (no cron change)
```

---

## Changelog

- **2026-09-28:** the watchdog's repair loop runs `converge-off`;
  verify_card's output and the watchdog report no longer use fixed `/tmp`
  files. The 2026-09-25 section is marked done (uploaded in eb5bc2a4),
  not deleted.
- **2026-09-25:** the staged file also carries the pr-tests split switch
  (off in `collect.yml`); new section on top with both upload paths.
- **2026-09-24:** first version.
