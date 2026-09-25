# HANDOFF — Ubuntu 26 and Node 24 readiness, 2026-09-24

Read `CLAUDE.md` first. This is dated and goes stale: check every claim
against `main` before acting on it.

## Why

- GitHub moves `ubuntu-latest` from Ubuntu 24.04 to Ubuntu 26.04,
  rolling out **2026-10-19 → 2026-11-19**. `ubuntu-26.04` is already a
  generally available label, so it can be tested now.
  (https://github.blog/changelog/2026-09-17-ubuntu-26-generally-available-and-latest-migration/)
- The 26.04 image's own software, from its published readme
  (`actions/runner-images`, `images/ubuntu/Ubuntu2604-Readme.md`, read
  2026-09-24): default Python **3.14.4** (24.04: 3.12); default Node
  **24** (24.04: 20); toolcache Python 3.10–3.14 (so `setup-python` 3.11
  and 3.12 are there); git 2.55; gh 2.100; `python-is-python3` installed.
- Node 20 is being retired as an action runtime. `actions/checkout@v4`
  and `actions/setup-python@v5` are Node 20; `@v5` and `@v6` are Node 24.

## The audit — what could break, per workflow

"Image Python" = the job ran `python` with no `setup-python`, so on
26.04 it would silently become Python 3.14.

| workflow | cron? | could break on 26.04 / Node 24 | fixed how |
|---|---|---|---|
| `browser.yml` | yes | `ubuntu-latest`; checkout@v4 + setup-python@v5 (Node 20); **`playwright install --with-deps` installs apt packages by name, which change per Ubuntu release — the riskiest step**; `pip install playwright` is unpinned (floats on its own clock, not the image's) | staged: pinned 24.04, v5/v6. Render tests now also run on every PR on both images (pr-tests `render`) |
| `budget.yml` (2 jobs) | yes | `ubuntu-latest`; checkout@v4; image Python; `gh`, `git` | staged: pinned, v5, setup-python 3.12 in both jobs |
| `calibration.yml` | yes | `ubuntu-latest`; checkout@v4; image Python; `gh` | staged: same |
| `cfbd.yml` | yes | `ubuntu-latest`; checkout@v4; image Python; `gh` | staged: same |
| `collect.yml` | yes | `ubuntu-latest`; checkout@v4 + setup-python@v5; test step runs `node test_*.js` on the **image's Node** (20 → 24); `git` via `push_retry.sh`; `timeout` | staged: pinned, v5/v6. Node 24 is exercised by pr-tests on 26.04 |
| `mlb-refit.yml` | yes | `ubuntu-latest`; checkout@v4 + setup-python@v5 | staged: pinned, v5/v6 |
| `owed_tests.yml` | yes | `ubuntu-latest`; checkout@v4; image Python; `gh` | staged: pinned, v5, setup-python 3.12 |
| `runs.yml` | yes | `ubuntu-latest`; checkout@v4; image Python; `gh` | staged: same |
| `self-repair.yml` (2 jobs) | yes | `ubuntu-latest`; checkout@v4; image Python in the decide job AND for the agent (which runs the suite); `gh`, `sed`; `claude-code-action@v1` is composite (no Node runtime of its own) | staged: pinned, v5, setup-python 3.12 in both jobs |
| `t60r.yml` | yes | `ubuntu-latest`; checkout@v4 + setup-python@v5 | staged: pinned, v5/v6 |
| `vacuity.yml` | yes | `ubuntu-latest`; checkout@v4; image Python for the whole mutation sweep | staged: pinned, v5, setup-python 3.12 |
| `pr-tests.yml` | no | `ubuntu-latest`; checkout@v4 + setup-python@v5; image Node | **fixed in the PR**: v5/v6; now a matrix on `ubuntu-24.04` + `ubuntu-26.04`, plus a `render` job (browser.yml's steps) on both |
| `claude.yml` | no | `ubuntu-latest`; image Python for the agent (checkout already @v6, Node 24) | **fixed in the PR**: pinned 24.04, setup-python 3.12 |

Checked and found nothing: every module imports only the standard library
(plus `playwright`/`yaml`, both behind `ImportError` guards), and nothing
imports a module removed in Python 3.13/3.14 (`cgi`, `imp`, `distutils`,
`pipes`, `telnetlib`, …) or uses the removed `ast.Num`/`ast.Str`. No
`apt-get`, no `sudo`, no hard-coded `/usr/lib` path in any workflow.

## What was decided

1. **Pin, then move deliberately.** Every job is on `ubuntu-24.04`, so the
   19th changes nothing. GitHub's own advice for "not ready to move".
2. **Python is never the image's.** Every job that runs Python (or hands a
   shell to an agent) installs 3.12 (3.11 for `browser.yml`, unchanged).
   Moving the image later then does not also move Python.
3. **Node 24 majors**: checkout v5, setup-python v6. (`checkout@v5` rather
   than v6: v5 is v4 on Node 24 and nothing else; v6 also changes how the
   push credential is stored, and these jobs push.)
4. **The guard** (`test_runner_image.py`, reads each workflow AS IT WILL
   BE LIVE, the staged copy winning): floating labels, Node 20 majors,
   actions not in its table, image Python, pr-tests not covering a pinned
   image, and pr-tests' render job drifting from `browser.yml`. Six
   declared mutations, all bite.

## How to test on 26.04 before the 19th — no schedule touched

- **Automatic:** every pull request runs `tests (ubuntu-26.04)` _(since 2026-09-25 plus four `tests (ubuntu-26.04) · sweep k/4` jobs: the vacuity sweep in parallel parts)_ and
  `render (ubuntu-26.04)` beside the 24.04 rows. The PR that introduced
  this is the first 26.04 test of the whole suite and of the Playwright
  install. Nothing to click.
- **On demand:** `pr-tests` has a **Run workflow** button (Actions →
  pr-tests → Run workflow → branch `main`). It runs both images.
- ⚠️ What pr-tests does NOT prove on 26.04: the jobs' own steps that talk
  to GitHub (`gh issue`, `push_retry.sh`) and the paid pulls. Those use
  `gh`/`git`, present on both images; the risk is low but unmeasured.

## Moving to 26.04 later

When the 26.04 rows have been green on PRs: one PR changes `pr-tests`
and `claude.yml`, and stages the 11 cron files with
`runs-on: ubuntu-26.04` for Sam. `test_runner_image.py` needs no change
(26.04 is a pinned label and pr-tests already covers it).

## Changelog

- **2026-09-25:** pr-tests now runs each image as five jobs (`rest` plus
  the vacuity sweep in four parts); `test_pr_shards.py` holds the split.
- **2026-09-24:** first version.
