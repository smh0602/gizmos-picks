# UPLOAD BY HAND: `collect.yml`

## Current: the Ubuntu 26 / Node 24 update `[2026-09-24]`

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

**No schedule, cron line or step logic changes. No cost.**

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

- **2026-09-24:** first version.
