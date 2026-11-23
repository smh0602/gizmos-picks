# UPLOAD BY HAND: `browser.yml`

## Current: the render tests run once, not twice `[2026-11-21]`

Every click and the commit message are in
**`docs/upload/UPLOAD-browser-render-once.md`**. One file, no cron change.

---

## ~~Current:~~ Done: the Ubuntu 26 / Node 24 update `[2026-09-24]`

✅ Uploaded: commit eb5bc2a4 on 2026-09-25. On 2026-11-21, before the
render-once change above was staged, the live `browser.yml` matched the
staged copy byte for byte. ⚠️ The link below now serves that newer staged
copy, so follow the section above, not this one.

**This file is one of 11 uploaded together.** Follow
**`docs/upload/UPLOAD-runner-image.md`**: it has every click and the
commit message. Do it after merging the pull request "Workflows: pin
Ubuntu 24.04, move to Node 24 actions, pin Python", before 2026-10-19.

`browser.yml` is the twice-daily page (render) tests. What changes in it:

1. `runs-on: ubuntu-latest` → `runs-on: ubuntu-24.04`, so GitHub moving
   `ubuntu-latest` to Ubuntu 26.04 on 2026-10-19 changes nothing here.
2. `actions/checkout@v4` → `@v5` and `actions/setup-python@v5` → `@v6`: the
   Node 24 versions (GitHub is retiring Node 20).
3. Its Python version does not change (it already installed its own).

**No schedule, cron line or step logic changes. No cost.**

If you upload only this one file: download
https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/browser.yml
with **Download raw file**, then in
https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
(breadcrumb **gizmos-picks / .github / workflows**) click **Add file** →
**Upload files** → **choose your files**, pick `browser.yml`, and commit with:

```
workflows: pin ubuntu-24.04, Node 24 actions, pinned Python (no cron change)
```

---

## Changelog

- **2026-11-21:** new section on top pointing to
  `UPLOAD-browser-render-once.md`; the 2026-09-24 section is marked done
  (uploaded in eb5bc2a4), not deleted.
- **2026-09-24:** first version.
