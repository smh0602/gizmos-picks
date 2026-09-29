# HANDOFF 2026-09-29 — tests that asked production instead of the code

## Why this exists

Collect was red from 2026-09-26 16:16Z. The product still committed, since the
test gate is the last step, but nothing was checked before it shipped.

Some failures depended on the day's data, not the code:
- **Every run:** `test_credit_balance.py` and `test_shadow_fb.py` failed.
- **Thin days only:** `test_dossier_fb.py` and `test_dossier_page.py` failed
  whenever the live board was thin (Monday 09-28: 7 games).

Sam's instruction was: *"Fix the tests' questions; never lower a bar."* Then
search every test file for the same patterns and fix them all.

## The patterns

- **P1: a frozen clock against a live tree.** Code that reads the live repo
  is handed a fixed `NOW`, so every window it computes from "now" drifts as
  the calendar moves. (The reverse is the same defect: a real clock against a
  pinned tree.) **Fix:** use the real clock against the live tree, or pin the
  tree to NOW. Never one of each.
- **P2: asserting that another guard is silent on production data.** The
  verdict becomes a fact about production that day. **Fix:** build the
  silence case synthetically, and make the live line a `note()`.
- **P3: a rule-67 guard that needs live data to show a case.** It passes or
  fails depending on what the latest board, the newest window or the current
  season holds. It also covers a fixture that real data written later can
  shadow. **Fix:** plant the case every run, as #156 (commit e4b04844) did.
  The live check stays as an extra when the live data holds the case.
- **P4: network.** Most of it came from tests running `collect.py <mode>`
  without `converge-off`. The collector then converges every overdue mode:
  news from two outside hosts, and the PAID modes whenever a key is present.
  **Fix:** `converge-off`, blank keys, and recorded fixtures.

**Not a finding:**
- a check over repo SOURCE;
- a check over append-only history that already holds its case (a dated
  archive, a published `picks/<date>.json`);
- a live check that is already a note, or that has an always-present planted
  twin.

## How the sweep was run

1. **Finding candidates.** 14 readers each read about 11 test files end to
   end. A search-driven sweeper covered all 151 files from a second angle.
   Together they produced 147 candidates in 57 files.
2. **Judging and fixing.** Seven agents each took a disjoint set of files and
   worked in their own git worktree. They judged every candidate, fixed the
   real ones, and declared a red `@vacuity` mutation for every new or changed
   check.
3. **Merging.** The orchestrator reviewed and merged the work, and reversed
   one call (below).

## Guards added for the classes

- **`test_collect_subprocess.py` (new):** AST-scans every test for collector
  subprocesses. Each must pass `converge-off` and blank `ODDS_API_KEY`.
- **`test_step_tmp.py` (new):** no workflow step a test runs writes a fixed
  `/tmp` path. It reads staged copies where an upload is pending.
- **`test_repair_loop.py` (new):** the watchdog's free-repair loop never
  converges. Every `SAFE_REPAIRS` mode, run under a league that does not own
  it, exits 0 and changes none of that league's files.
- **`test_credit_balance.py` §8:** the file re-runs itself with a credits
  finding planted on the live tree only, and must stay green and show the
  plant. (`vacuity.py` only has "must go red" mutations, so the file asks the
  stay-green question itself, on every run.)

## Per-file results

**FIXED** means the check now has its case every run (planted, pinned or
recorded). Where the live data holds the case, the live check still runs as an
extra; otherwise it prints a `note()`. **NOT A FINDING** gives the reason.
Every new or changed check carries its own `@vacuity` declaration.

### The four named items

| File | Pattern | What changed |
|---|---|---|
| `test_credit_balance.py` | P1 + P2 | The live tree is now judged at the real clock (this machine's clock brackets the run). Silence is built on a synthetic tree pinned to its own now, with both credits checks running. What the live tree finds is a note. §8 plants a live finding and must stay green. 72 checks. |
| `test_dossier_fb.py` | P3 + P4 | 12 real week-2 games are planted in every tree. §8/§9 run `card-fb converge-off` with keys blank, behind a socket fence (0 network attempts, down from 6). The temp-tree leak is fixed (it was about 9 trees per run). The week-1 §6 refusal now names a remedy. Found: the §3 "without dossier_fb" tree never lacked the file; fixed. It passes on empty, 1-game, 7-game, week-1 and rollover boards. |
| `test_dossier_page.py` | P3 | A 12-game planted board with one side no table holds, so the real builder refuses sections by name. Sections 4 and 5 take their frames from the planted build. No IndexError on an empty board. |
| `test_shadow_fb.py` | P3 + P4 | §7's fixture is always the file read. A later "real" archive is planted to prove the shadowing check bites. It adds a day with 14 games, decoys and unique patterns, and wipes every other day, only inside a verified mkdtemp copy. §4 and §7 run on the densest committed window, and the newest window is a note. §8 runs `converge-off`, offline, clock pinned. The Windows path separator is fixed. |
| `test_pr_staged.py` + `pr-tests.yml` | fixed /tmp path | `mktemp` files for the apply and Tests steps, plus a deterministic two-copy replay. `V.rotted(ROOT)` is now a note here; the same hard check stays in `test_vacuity.py`. |

### The sweep: fixed

| File | Line(s) | Pattern | Fix |
|---|---|---|---|
| test_dossier_coverage.py | 184, 193, 266, 279, 293, 384 | P3 | A five-game planted board covers each join kind, the week source, the unplaced date, the neither-side skip and the venue. Section 3 reuses it. |
| test_vs_position.py | 345, 389 | P3 | A 7-game planted board per league with a synthetic allowed file. It covers every refusal path, and exact counts are asserted. |
| test_accumulators.py | 201, 227 (P4), 222/231 (P3) | P3/P4 | `card-fb converge-off`, offline. The card check now requires a card this run wrote. |
| test_page_contract.py | 341 (P1), 349 (P2) | P1/P2 | §4 now runs on a tree planted at 35 instants across a week, with two planted late twins that must be caught. The live result is a note. |
| test_top_plays.py | 127, 168, 199, 266, 324 | P3 | A planted board runs through the real card_fb (exact plays, order, sentence), plus MARKET-only, join-under-60% and empty boards. |
| test_verify_card.py | 205 (P2), 230, 253, 347 | P1/P3 | Section 39 runs on planted rows. Each fault class runs on its own fair card. Found: the projection injection was dead; fixed. |
| test_verifiers_run.py | 258 | P3 | `verify_nfl --current` runs on trees pinned to now: clean, failing and empty. |
| test_trends_schedule.py | 137 | P3 | Measured on planted schedules. Found: a fixed −4h offset was misfiling November days; fixed. |
| test_p4.py | 28 | P3 | A declared 67-team map is planted beside a newer partial season. |
| test_news_archive.py | 434 | P2 | The whole chain is one `_verdict`, asserted on planted trees pinned to now. The live result is a note. |
| test_record_fb.py | 214, 328, 394, 680, 741, 747 | P3 | New §3b plants cards, pointer and log per league with known answers. |
| test_record_fb_rebuild.py | 246, 257 | P3 | The three states also run on a planted tree. |
| test_record_reset.py | 50 | P3 | "MLB untouched" is asserted on a planted MLB record. Found: the sandbox was reading production's record; fixed. |
| test_fb_record.py | 193, 224, 346, 451, 499 | P2/P3 | Planted bands and a planted grader run. |
| test_calibration.py | 228 | P2 | `read_all` is checked on a planted root both ways. The live verdict is a note. |
| test_board_cap.py | 156 | P2 | The scanner runs on planted cards. The builder publishes exactly 25 from a planted 30-row board. |
| test_cfb_possession.py | 92 | P3 | The recorded column list (`research/cfbd_plays_columns_20260928.json`). Before, one refused /plays call crashed the whole file. |
| test_cfb_source.py | 63, 109 | P3 | A planted tree, and `run_probe` driven offline with a planted 429. The old :63 check could never fail. |
| test_conf_filter.py | 332, 386 | P3 | Recorded names and directory (`research/conf_filter_names_20260928.json`), and a planted 3-conference directory. |
| test_contract_modes.py | 271 | P1 | Each of the 7 fixed instants gets its own tree pinned to it. |
| test_fb_freshness.py | 130, 281, 324, 508 | P3 | A planted tree pinned to 2026-09-19 20:00Z. Found: a dead call that always raised; removed. |
| test_fb_props_model.py | 274 | P3 | A planted league whose shares change. |
| test_freshness.py | 124 (P1), 144 | P1/P3 | Trees pinned. Found: six verdicts sat in a list nothing checked, and a converge case could never fail. All are checks now. |
| test_game_lines_day.py | 182 | P2 | Built every run from a planted snapshot across a slate change. The live card is a note (the watchdog asks it of production). |
| test_league_switch.py | 127 (P4), 140 (partial) | P4/P3 | A catch-all route aborts every off-machine request. It notes the day when both leagues sit on the same week. |
| test_live_scores.py | 209 (P4), 271 §3 | P4/P3 | Catch-all route, plus the page's `fbMerge` run in node on planted games. |
| test_box_live.py / test_box_score.py / test_nfl_opener.py | browser | P4 | Catch-all route. test_box_score pins season 2026. test_nfl_opener:161 re-checked its own filter; it is replaced by planted season files. |
| test_drop16_fixes.py | 415 | P2 | The four other files' verdicts on the live tree are notes; each runs directly in the suite, and the empty-card case is planted in three files. |
| test_fbs_gate.py | 124 (hardened) | P3 | §6b: a planted part-built file, and an empty tree. |
| test_parity.py | 111, 225, 257 | P3 | A planted schedule and tree. |
| test_props_window.py | 171 | P3 | The coverage walk uses `runs_report`'s cron parser (one copy), shown on a planted cron. The season follows the clock. |
| test_mlb_refit.py | 266 | P1 | Reads the refit's own season-stamped file. |
| test_mlb_tables.py | 133 (P1), 315, 321, 327 | P1/P3 | Pinned pull `research/mlb_pitchers_0820.json.gz` (byte-for-byte the published table), and a planted three-game props snapshot. |
| test_price_floor.py | 136 | P3 | A synthetic card goes through the real verify_card: a leg at −700 passes, one at −701 fails. Before, it printed NOT EXERCISED today. |
| test_repo_watch.py | 213 (P2), 288 | P2/P3 | Asked of the dated 2026-09-19 baseline. Live figures are a note. ⚠️ On a full clone, live packed growth is 10.71 MB/day, and the old check would already be red. |
| test_signal9.py | 146 | P3 | A planted three-week schedule. |
| test_signals_67.py | 112 | P3 | Schedule dates are stubbed from the sample's own ids, with a no-schedule twin. |
| test_single_day.py | 269, 375 | P3 | Planted logs and board across two ET days, and a planted 2-row board. |
| test_source_block.py | 162 (P1), 210, 227 (P2), 333 (P4) | P1-P4 | A `_nonet.py` wrapper (the network refuses; `build_schedule` records), cfb-probe artifacts derived from the survey, and an MLB sandbox for the silence case. 61s → 7s. |
| test_t58_t59.py | 116 | P3 | A planted record with 119 rows over 3 weeks. (The real one is at 115 of 120.) |
| test_t60r.py | 274 | P2 | Recorded provider spellings from the 2026-09-22 pull. The live pull is a note. |
| test_watchdog_coverage.py | 139 | P3 | The freshness fixture is written by this checkout's writer, pinned to NOW. Found: the record-age check could never fire; fixed. |
| test_artifact_keys.py | 205, 209 | P3 | A planted twin (this checkout's reader and writer). ⚠️ The live class sweep STAYS a check: the orchestrator reversed the agent's demotion to a note, because it asks this file's own question of every module against append-only artifacts. |
| test_self_repair.py | 197, 199 | P2/P3 | A planted PROGRESS record feeds `render()`. The live state is a note. |
| test_budget_watch.py | 431, 441 | P2/P3 | A synthetic report plus a planted copy of the ceiling line. The live report is an extra. |
| test_runs_report.py | 682 | P4 | Runs with no token or repository in the env. It asserts the offline branch was taken. |
| test_multileague.py | Windows `bash -c` | — | The step is driven from a file (it was 16 of 21 red on Windows). |
| test_record_grader.py | 169, 180 | P4 (defence) | Keys blanked on its collector calls. |
| test_gh_permissions.py / test_watch_label.py | "403" drive | fixed /tmp path | Declarations re-pointed so they resolve in the deployed and staged copies. The staged self-repair.yml uses a mktemp file. |

### The sweep: not a finding (with the reason)

| File | Line(s) | Why |
|---|---|---|
| test_dossier_coverage.py | 535, 538 | A union over committed append-only dossier archives (171 files); it only grows. |
| test_shadow_fb.py | 415, 420 | `picks/` is append-only; the card at the cap is permanent. (Lowering TOP_N would be a deliberate change.) |
| test_accumulators.py | 213 | t54 counts rows rebuilt from every append-only card against a log that only grows. |
| test_page_contract.py | 178/209/224, 255 | A frozen NOW, but everything read is permanent (schedule-2026 kickoffs, the append-only card glob, and constants). The real clock would go red every off-season. |
| test_verify_card.py | 214 | The case lives in append-only `picks/2026-09-24.json` (and 29 others). |
| test_news_archive.py | 622 | `data/latest/news.json` is tracked and never deleted. |
| test_record_fb.py | 113, 348 | Cumulative and finished season logs; the hand fold is coarser by design. |
| test_record_reset.py | 84 | Append-only cards plus the permanent players-2026 log. |
| test_ranking.py | 149, 160 | A season-stamped committed matched pair, with 536 tie groups present. |
| test_schedule.py | 92 | No check reads the live-dependent fields. |
| test_single_day.py | 82 | Reads append-only published cards (51 with mixed days). |
| test_line_scores.py | 205 | Section 9's planted store already catches both declared mutations. |
| test_news_flags_fb.py | 64, 92 | The frozen date pins the window to write-once dated archives. The real clock would make it worse. |
| test_box_live.py / test_box_score.py | 131, 298 / 66, 154 | Whole-season, hard-coded season files that only accumulate; no other guard is involved. |
| test_live_scores.py | 271 §1/§5 | The whole-season schedule, and the page always lands on a week with games. |
| test_drop16_fixes.py | 116 | Every path writes the header first; the file is committed and never deleted. |
| test_nfl_opener.py | 145 | The finished 2025 log holds the case. |
| test_conf_filter.py | 332 (live coverage) | Kept as a check on purpose: a name the page's own resolver cannot place really vanishes from the tab. A new odds-feed spelling can turn it red; see "decisions for Sam". |

## The 2026-09-28 "alt-lines exit 1" (collect run #1953): diagnosed, and it is ours

**What happened**
- The watchdog chose repair `card`.
- Its free-repair loop (`collect.yml`, watchdog step) ran
  `LEAGUE=$lg ODDS_API_KEY= python collect.py "$m"` with no `converge-off`.
- So the key-less NFL run converged the whole contract. It planned gamelines,
  props-player, props-board and alt-lines, and each died at "FATAL:
  ODDS_API_KEY is not set" before any request was made.
- Converge then reported each of them as "failed … left an artifact out of
  contract".
- Nothing was spent. The real alt-lines pulls landed at 16:00, 19:03 and 21:40Z.

**The same loop also:**
- ran the MLB `card` mode under football ("no game logs at all");
- would have let a `record` repair overwrite football's `record.json` with an
  MLB-shaped one (reproduced in a temp tree; never seen in production);
- wrote a stray `data/latest/t54.json` on 2026-09-20 through an MLB `card-fb`
  repair (commit 027d7215).

**Fixed**
- The staged `docs/upload/collect.yml` adds `converge-off` to the repair line.
- `collect.py`'s run_mode refuses `card` and `record` under football, and
  `card-fb` under MLB. The guards sit in run_mode, so record_grader's
  fingerprint is unchanged.
- The new guard is `test_repair_loop.py`.

## Proof that the guards bite

**The full declared-mutation sweep**, run locally (Windows, 8 parallel trees,
910 s) on the merged branch:
- 618 declarations in total, up from 449 on main.
- 585 BITES: red under their mutation, green on revert.
- The other 33 are RED_BOTH_WAYS. They are all in files that are already red
  on this machine for time-zone or path reasons: test_card_fb,
  test_card_frozen, test_converge_judge, test_game_lines_day,
  test_possession_freshness, test_record_fb.
  - The two of those this PR touches (test_game_lines_day, test_record_fb)
    were swept with a time-zone shim by the agents that changed them, and
    their declarations bite.

**The sweep also found one of this PR's own live extras running without its
case:** test_mlb_tables (c2) used the board's stamp as its clock just after
00:00Z. Fixed; all 13 of its declarations bite.

**The blind set** (test files with no proof of any kind) went from 53 to 37.
`vacuity.BLIND_CEILING` came down from 56 to 37: the ratchet only comes down.

⚠️ pr-tests' sweep parts do not fail on a declaration that does not bite, so
CI alone would not have shown the above. It is offered as its own task.

## Needs Sam's hands

1. **Upload two staged workflow files**, one upload each. Both carry
   byte-identical cron lines.
   - `docs/upload/collect.yml`: `docs/upload/UPLOAD-collect.md`.
   - `docs/upload/self-repair.yml`: `docs/upload/UPLOAD-self-repair.md`.
   - Until you upload, a key-less repair can still converge and print false
     paid-mode errors. pr-tests' `staged` job runs the suite with both files
     applied.
2. **A stray `data/latest/t54.json`**, written by the MLB `card-fb` repair on
   2026-09-20 (commit 027d7215). Deleting data is your call; nothing reads it.
3. **About 82 GB of leaked `dossier-*` temp trees** in
   `C:\Users\Senor\AppData\Local\Temp`, left by the old `test_dossier_fb.py`
   (it no longer leaks). They are throwaway copies of `data/`, so deleting them
   is safe, but it's your machine.

## Decisions for Sam (not changed)

- **`test_conf_filter.py` live name coverage stays a check.** A new odds-feed
  spelling the page cannot place really does drop a team from the Conference
  tab. It can turn the suite red on a data change. If you'd rather it alarm in
  production, it belongs in `watchdog.py`.
- **A hard production alarm for news divergence** (latest fresh, archive
  empty) would be a contract change. Today it is watched only by the soft
  dated-archive row.
- **`test_props_window.py`'s 99% bar** lets 1-2 NFL misses through. The bar is
  yours.

## Found, not changed (their own task)

- pr-tests' vacuity sweep parts pass even when a declared mutation does not
  bite; only the nightly job catches it (issue #188). Offered as its own task.
- `t60r.py:496-497` picks a game's provider with an exact-string index, not
  `provider_rank`, so "Draft Kings" (423 lines) still ranks last at selection.
  `t60r.py lines` should also warn on an unknown provider.
- `shadow_fb.py:561` uses `int(day[:4])` as the season, so January playoff
  boards will look for next year's players file.
- `dossier_fb` head-to-head counts a finished game as its own "prior meeting"
  (35 archived rows).
- `refresh` mode runs the MLB card and grader with no league guard. It is not
  a SAFE_REPAIR, and no football route to it was found.
- Two checks that can never fail were reported and not changed:
  - `test_conf_filter.py` "no name resolves by MISTAKE" (`_wrong` is
    hard-coded `[]`);
  - `test_nfl_opener.py` "the first ET slate day holds at least one game".
- On a full clone, live packed repo growth is 10.71 MB/day against the
  2026-09-19 baseline of 5.34 MB/day, which `repo_watch.py` may start
  reporting.

## What did NOT change

- **No bar was lowered, and no assertion was deleted.**
  - Every check that became a `note()` has a planted or synthetic twin that
    asks the same question every run.
  - Two new floors in this PR's own new checks were set with headroom
    (`test_collect_subprocess.py`: 7 calls in 5 files, found 9 in 7).
- **No cron line.** No deployed workflow file with a cron block was edited.
  `pr-tests.yml` has no cron block and was edited directly.
- **No model, coefficient, card output, published pick, or API spend.**
- **Product code, in total:**
  - the `collect.py` run_mode league guards;
  - `dossier_fb.nfl_table()` (one parse of `NFL_TEAMS`, no behaviour change);
  - a `remedy` sentence on the §6 refusal (the page does not print it);
  - a comment in `freshness.py`.

## Changelog

- **2026-09-29:** first version.
