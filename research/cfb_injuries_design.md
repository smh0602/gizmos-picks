# College injuries (`cfb_injuries.py`)

## In plain English (for Sam)

Sam, 2026-10-17: *"use the college injury source as long as it's accurate and up to date, we wouldn't want misinformation ruining our bets."*

- **The source.** The official conference availability reports: SEC, ACC, Big Ten, Big 12 and MAC through HD Intelligence, the vendor that runs them, plus the Sun Belt and Pac-12 feeds. All are free, with no key.
- **Stored on a schedule.** Every college run stores them. Each report is checked before it is trusted (§2).
- **Shown.** A college pick's why names the opponent's Out / Doubtful defenders who guard him, as the NFL's does. This only happens when the report is accurate and up to date.
- **Used in the model only if it passes a test fixed in advance.** College injuries move the predicted score only if they pass the same test NFL injuries took, written here before any number exists (§4). NFL injuries failed it.
- `[2026-10-26]` **It passed on 2026-10-19**, and it switches on when Sam merges it. On game days the reports are read again at 9am, 12pm and 7pm ET, and each time the model is rebuilt. A game that has not started reads the newest report at that moment (§5, Sam's "do 9am, 12pm, 7pm").

⚠️ **Terms.** The conference sites' terms limit automated reading, and HDI's own terms are unknown. Sam was told this and chose to use the source. This supersedes ~~his 2026-09-23 condition, "Build it only if it is free and allowed by those sites' terms. Otherwise signal 7 is NFL-only"~~ (`dossier_fb.PERSONNEL_COLLEGE`).

## 1. The data

### The sources, one pass each run (`run`)

- **HDI.**
  - Call: `POST https://app.hdintelligence.com/api/get-publish-public`, body `{"sport":"Football","organization":C,"conference":C}`.
  - C is SEC, ACC, B10, B12 and MAC.
  - Each call returns that conference's current reports. Every travel-roster player is listed with a status, written as `"POS #NUM Name"`.
- **Sun Belt and Pac-12.**
  - `GET https://sbcautostorage.blob.core.windows.net/availability-reports/{sunbelt,pac12}-football/prod/report.json`.
  - These list only the players who are not available, with name, position and status. They carry a real `updatedAtUTC`.
- **Past seasons, once, while missing.**
  - `get-archive-legacy-public` holds 2025 and `get-archive-public` holds the current season's completed weeks.
  - Both go to `data/ncaaf/history/injury-archive-<season>.json.gz`.
  - The current season's file is refreshed at most once a day, and rewritten only when it changes.
- **Coverage.** Power-4 reports cover conference games only. MAC covers all its games. AAC, CUSA and Mountain West have no source here.
- ⛔ **What is never stored.** Every `data:` image is stripped before anything is stored. Those images are 98% of the bytes.
- ⛔ **Separate from CFBD.** These calls never go through `cfb.get` or the CFBD budget.

### What is stored

1. **`data/ncaaf/<day>/injury-reports/<hhmm>.json.gz`** (daystore, written once).
   - A new snapshot is written only when the normalised content differs from the newest stored one.
   - It holds every accepted report: `{game_id, home, away, kickoff, source, label, posted_at, teams:{<schedule team>:[{name, number, position, position_raw, status}]}}`.
   - It also holds `fetched_at` and the refused list.
2. **`data/ncaaf/latest/injuries-probe-<season>.json`**, written on every attempt.
   - Per source: whether it answered and how many reports it gave.
   - What was refused and why.
   - Unknown names, positions and statuses.
   - The newest snapshot's age.
   - This file carries the freshness contract row, so `converge` runs the mode on every college pass. No cron changes.
3. **`data/ncaaf/history/injury-archive-<season>.json.gz`**: the archives, normalised to rows `{game_id, team, opponent, date, player, number, columns:{<report day>: status}}`.
4. **From CFBD, at no extra call** (`cfb.py`). `/roster` and `/games/players` are already fetched every build; today their jerseys and defensive stats are thrown away. Two files keep them:
   - `roster-<season>.json.gz`: `{teams:{team:[{id, name, jersey, position}]}}`.
   - `defense-<season>.json.gz`: `{players:{id:{name, team, g:[{game_id, d, week, wk_i, seasonType, tot, solo, sacks, tfl, pd, qb_hur, int}]}}}`.
   - 2025 is filled once while missing, priced by `cfbd_budget.preflight`.

## 2. Accurate and up to date: what a report must pass

### Accurate (`normalise`), or the report is refused and named in the probe

1. **Both team names are known.** A name is exact, or found in the explicit alias table (`ALIASES`, e.g. "Penn St." → "Penn State", "Miami (FL)" → "Miami", "Southern California" → "USC").
   - ⛔ Never fuzzy. ⛔ Never the display name: it writes "Miami" for both Miami schools.
   - An unknown name fails closed.
2. **The report joins exactly ONE game in the stored schedule.**
   - Same two teams, away and home in the report's own order.
   - The kickoff equals the schedule's `start` to the minute where the feed gives one (HDI publish, Sun Belt, Pac-12).
   - Archive rows join the game within the report's date + 8h to + 36h UTC.
3. **Every player row parses.** A row that does not is counted and left out, never guessed. The same player listed twice in one report (same team, jersey and name once punctuation is folded) is kept once.
4. **A status is one of the known set.** Out, Out for Season, Doubtful, Questionable, Probable, Available, Game Time Decision, Out - (1st Half), Exempt.
   - Anything else is `unknown` and counts nowhere.
   - Exempt means unknown, never healthy.

### Up to date (`report_for`)

A game's report is the last stored one fetched at or before the moment asked (and never after kickoff). It is **current** only if both hold:
- **(a)** It was published no more than `MAX_AGE_H` = 36 hours before kickoff. Published means `posted_at`, or its `fetched_at` where the feed gives no time.
- **(b)** For a live read, our newest snapshot of its source is no more than `FETCH_MAX_AGE_H` = 6 hours old.

A report that is not current is not shown and does not reach the model.

## 3. How an injury is sized (the model's input, `cfb_injuries.attach`)

These are the college versions of the NFL's measures (T69 IN), each from games BEFORE the game being predicted. Per team:
- **QB out** = 1 if the team's starting QB is Out / Doubtful. The starting QB is the most pass attempts in the team's latest stored game.
- **Offence out** = the season-to-date share of the team's rushing + receiving yards held by its Out / Doubtful players (`players-<season>`).
- **Defence out** = the season-to-date share of the team's tackles held by its Out / Doubtful defenders (`defense-<season>`).

The rules that apply to all three:
- A report player is matched to a CFBD player by team + jersey (the roster) with the same last name, else by a unique name on the team (`card_fb.norm`). ⛔ An ambiguous name is not matched.
- **Counted:** Out, Out for Season and Doubtful only.
- **No report for that game → no reading (None), never zero.** College reports cover conference games only.
- `[2026-10-17, review]` **A team with no stored game before this one (a season opener) → no reading too**: nothing is known about who matters, so a starting QB listed Out must not read 0.

**The report known at pick time:**
- For a stored snapshot: the newest report fetched before 9:00 am ET on the game's own ET day, the morning card.
- For the archives: the night-before column. 2026: "Update 2". 2025: "Friday" for SEC and Big 12, "Thursday" for ACC.
  - The 2025 Big Ten has only a game-day column, so it gives no reading.

## 4. THE BACKTEST BAR (fixed 2026-10-17, before any college injury number was computed)

It is **the same bar Sam accepted for NFL injuries** (`research/fb_sim_design.md` §3, "In the sim, backtest-gated").
- **The comparison:** the smooth curve fed the injury-moved predicted score, against the smooth curve without it.
- **The weeks:** the walk-forward weeks of the Model picks record (`fb_model.walk_forward`). Each week is fitted and sized on earlier games only.
- **The size of the move:** each team's points move by b_qb × QB out + b_off × offence out + b_def × the opponent's defence out. The b are fitted each week on that week's training games (`fb_model.injury_fit`; `INJ_RIDGE` 25 and `INJ_MIN` 200 unchanged).

Two numbers decide, on college spreads and totals:
- **(a) Log loss** over every final game's main closing spread and total. A push is left out.
- **(b) Closing-line return**, the record's spread and total picks pooled. College closings are an assumed −110, labelled.

`fb_model.INJURIES["ncaaf"]` turns on only if both hold:
- log loss with injuries is at most without;
- return with injuries is at least without.

Rules for the run:
- It is run ONCE, with the defence data stored.
- The result is recorded in `research/fb_sim_backtest.json` under `injuries.ncaaf`, by the committed runner `fb_inj_backtest.py`.
- `test_fb_sim.py` then fails if the switch disagrees with the record.
- Whatever the result, the reports are still stored and still shown in the why. Sam is told plainly.

## 5. THE LIVE READING AT EACH GAME-DAY CHECK `[Sam, 2026-10-26]` (added after §4's test passed; §3 and §4 are unchanged)

Sam asked for injuries to be checked at 12pm and 7pm on game days: *"make sure we're looking at injury status at 12pm of games starting and 7pm so we can make sure the models adjusted for injuries when deciding outcome for a vame"*.

He was then asked: "Should college's injury adjustment use the 12pm/7pm reports, or the 9am one it was tested on?" He answered: *"do 9am, 12pm, 7pm"*.

What that means:
- **When the reports are read.** The game-day injury check (`freshness.INJURY_CHECK_ET`, the `injury-check` mode) reads the reports at 9:00, 12:00 and 19:00 ET on a day with a game still to start. The card and the game model are then rebuilt in the same pass.
- **A game that has not kicked off when the model is built** reads the newest report as of that build: `cfb_injuries.read_cut`, the later of §3's cut and the build moment. Before 9:00 ET this is exactly §3's reading.
- `[2026-10-26, review]` **Every live build reads it, not only the three checks.** On a game day the live builds are the three checks, the card deadline, and any other `card-fb` rebuild. Each one reads the newest report at its own moment.
- **Everything else is §3's rule, unchanged.** That covers the §2 checks (`_eligible`, `_judge` not live, the 36-hour published rule), the archive's night-before column, both teams needed, and no report giving no reading.
- **A game that has kicked off or finished keeps §3's 9:00 cut exactly.** So does every caller that passes no build moment: the training rows~~, the walk-forward record~~ and `fb_inj_backtest`. What §4 measured does not move. ~~and what is graded~~
- `[2026-10-26, review]` **The record grades what the site showed.** That is Sam's 2026-10-16 rule for the Model picks record. A played game's 9:00 reading can differ from the one its picks were shown with: the review counted 43 of the 81 college games in 2026 with a stored report reading differently 5 minutes before kickoff (inputs only, no outcome). So the live build also reads each played game as of its last build before kickoff, into `inj_shown`. ~~That moment is~~ That build is the ledger's last snapshot before kickoff that looked at the game (`fb_ledger.looked_moments`)`[2026-10-27, review 2]`, and its moment is its model's reading (below). Only the record's replay reads `inj_shown` (`fb_model.as_shown`). Every fit, the injury fit included, still trains on the 9:00 reading. A game with no recorded build is replayed at 9:00. Guard: `test_fb_model_record.py` §5.
- `[2026-10-27, review 2]` **...read at that build's own moment, from the reports it could see.** The first version read a replayed game at `read_cut`, the later of §3's 9:00 cut and the build. Live that is harmless, because no later report exists yet. Replayed, every later report exists, so a build before 9:00 ET (the 9am and 12pm checks did not run, or the game left later builds' list), and any build for a kickoff before 9:00 ET, was read with reports it never saw. The replay now reads at the build moment itself (`cfb_injuries.shown_cut`). That moment is the game model's own reading (fb-model.json `read_at`, kept in the snapshot as `model_read_at`), not the snapshot's `taken_at`, which comes minutes later, or hours later when that pass's model build failed and the snapshot saved the earlier build's picks. The snapshot is still the one `fb_ledger.looked_moments` chooses. Guard: `test_injury_check.py` §4, the replay against the live read at 120 build moments.
- `[2026-10-27, review 2]` **Only the reports are replayed as of the build.** The archive's night-before column and the role files (rosters, defence logs) are read as they are stored now, and they are rewritten in place. The 2026 archive was first stored on 2026-10-17 and the role files on 2026-10-18. Games built before then, while college injuries were off and the site showed no injury reading, are replayed with today's copies. That is Sam's "the record is recomputed each build". An exact replay of those files as of each build would need dated copies, which are not built.
- **This is Sam's decision (rule 13), made knowing the test was scored at 9:00 only.** The 12pm and 7pm readings were not part of §4's measurement.
- Guard: `test_injury_check.py` §4.

## Changelog

- **2026-10-17:** written, with §4 fixed before any college injury number was computed.
- **2026-10-17 (review, before any number):** §3 adds the season-opener rule. §4's bar is unchanged; how it is applied is made exact: the comparison uses unrounded numbers, a measurement whose injury fit moved no scored question is not a test, and a result already on a branch is never measured again.
- **2026-10-26:** §5 added. Sam answered "do 9am, 12pm, 7pm": a game that has not started reads the newest report at each game-day build. §3 and §4 are unchanged, and so are the tested reading and the recorded result.
- **2026-10-26 (review):** §5 corrected. Its first version said the record kept the 9:00 cut. That would have graded picks the site never showed. **Root cause:** the record's rule ("grade what the site shows") was not checked against the new reading. The record now replays each played game as its last pre-kickoff build read it. §5 also now says plainly that every live build reads the newest report, not only the three checks.
- **2026-10-27 (review 2):** §5 corrected again, in three places. (1) The replay read a build made before 9:00 ET at the 9:00 cut, with reports that build never saw, so the record could grade picks the site never showed. **Root cause:** the live rule, max(9:00 cut, build), was reused for the replay; it is only safe when no later file exists. (2) The replay was dated by the ledger snapshot's minute, not by the model's reading. **Root cause:** the snapshot recorded when it was taken, not when its picks were made. (3) "The report its last build read" held for the reports only; the archive and the role files are read as stored now. **Root cause:** the claim was written about the reports and not checked against the other inputs.
