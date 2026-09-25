# UPLOAD BY HAND: `collect.yml`

## Current: the Ubuntu 26 / Node 24 update, plus the faster PR tests `[2026-09-25]`

The staged `collect.yml` now carries **two** changes, and one upload
delivers both:

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

### Which steps to follow

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
`ran 132 of 132 test file(s) (shard all)`, where it used to say
`ran 132 test file(s)`. Until you upload, the nightly "runs" report lists
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

- **2026-09-25:** the staged file also carries the pr-tests split switch
  (off in `collect.yml`); new section on top with both upload paths.
- **2026-09-24:** first version.
