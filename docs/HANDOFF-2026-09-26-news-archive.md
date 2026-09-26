# HANDOFF — the news archive's freshness row named a mode nobody runs

Read `CLAUDE.md` first. Dated; check every claim against `main`.

## What was wrong (measured, not assumed)

1. **Converge planned a mode it cannot run.** Every football converge pass
   that found the dated news archive stale printed
   `unknown mode: news-archive` and then
   `WARNING: news-archive failed (exit 1). It is a SOFT artifact`
   (collect runs #1766, #1767, #1770, #1781, #1786, #1816, #1835).
   `freshness._football_contract`'s archive row named the mode
   `news-archive`; `collect.run_mode` has no such arm. The archive is
   written by `news`. The row is SOFT, so no run went red, and a stale
   archive could never rebuild itself through converge.
2. **`test_news_archive.py` was red on `main` after UTC midnight.** Its
   divergence check read `{mode: row}["news"]`, which since 2026-09-25 is
   the news-*flags* row (fresh all day), not `latest/news.json`. Between
   00:00Z and the first news pull today's archive is empty, so it fired on
   a healthy tree (measured 00:38Z, 2026-09-26: `news.json` 98 min stale,
   read as fresh).

## What changed

| | fix | guard |
|---|---|---|
| 1 | The archive row names its writer, `news`. `plan()` runs a mode once however many rows it owns, so a late archive costs one news pull. The dead `news-archive` entry left `SOFT`; the row is still soft through `news`. No deadline changed. | `test_contract_modes.py`: every mode named by `freshness.contract()` (mlb, nfl, ncaaf), by any row-shaped tuple in `freshness.py`'s source, and by `SOFT`/`OFF_PAGE`/`LATE_GRACE_MIN`/`CASCADE`/`SOURCE_BACKED`/`FREE` must be an arm of `run_mode`, read from `collect.py` with `ast`. Red on unchanged `main` (named `news-archive` four times), green after. 3 declared mutations, all BITE. |
| 2 | `test_news_archive.py` finds rows by PATH (`news_rows()`), and asks softness of the archive ROW. | A driven check that the right rows are picked in any order (hand-mutated back to the by-mode lookup: red, and it reproduced the false fire); a live check that both rows were found. |

## What Sam must do

Merge the PR when `pr-tests` is green. Nothing to upload.

## What did NOT change

No deadline, no softness decision, no workflow file, no cron, no spend.
`collect.py`, `index.html`, MLB's contract, the card and every model are
untouched.

## Mistakes, with root cause

- **A check asked the right question against a hand-typed answer.**
  `test_page_contract.py` already failed on "a contract row naming a mode
  the collector does not have" — against a `_KNOWN` set typed by hand,
  which listed `news-archive`. Root cause: the list of runnable modes was
  written down instead of read from `run_mode`. The new guard reads it.
- **A "driven by" entry excused the name.** `test_fb_freshness.py` and
  `test_parity.py` mapped `news-archive → news`. True of the FILE; says
  nothing about whether converge can run the MODE. Both entries removed.
- **Rows keyed by mode collapse.** A mode that writes several files owns
  several rows; `{mode: row}` keeps the last. That is how the divergence
  check read the flags row.

## Open

- `collect.converge()` still builds `still` (the `STILL OUT OF CONTRACT`
  log line and `freshness.json`'s `ok`) from `{mode: row}`, so for a
  multi-row mode only its last row decides. Nothing reads `ok`; the gate,
  the watchdog and the page banner read rows one by one. Suggested as its
  own task.
- Not guarded: a mode that is dispatched but refuses the league it is
  asked for (`props-player` under `LEAGUE=mlb`).

## Changelog

- 2026-09-26 — written with the fix.
