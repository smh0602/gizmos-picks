# UPLOAD BY HAND: `collect.yml` (the football relay)

**Do this after you merge the pull request "The football relay: one run keeps
football alive at every deadline, late crons step back, injuries every 2
hours" (its description links to this file).** It is one file. Time: about 5
minutes.

## What this is, in plain English

Your decision of 2026-11-18: "Turn the relay on for football?" You said yes.

Since 21 September GitHub has started this repo's scheduled runs 6 to 10 hours
late. MLB already copes with that: an MLB run that reaches the end of its hold
starts the next one (your 10-06 relay). Football was left out, so in the week
to 11-20, 101 football deadlines were first built more than an hour late
(median 130 minutes, worst 477), and the college card was on time at only 2
of the 7 deadlines that were recorded at all.

After this upload:

- One extra run, titled **collect [relay ncaaf nfl]**, keeps football alive for
  both leagues. It checks both every 15 to 35 minutes, builds whatever is due,
  and after about 4 hours 40 minutes starts its own replacement.
- While it is alive, the late football crons step back: they build and buy
  nothing a deadline owes, so two runs can no longer buy the same odds. They
  still run the things no deadline covers (the live and halftime probes, the
  game-day score refreshes, the Sunday rebuild).
- Any football cron that finishes and finds no relay run alive starts one.
- The chain stops by itself when no game in either league is within 3 days
  back or 8 days ahead, and the crons start it again when the season resumes.

**No schedule, cron line or cost changes, and the cron count does not change.**
All 43 `cron:` lines are byte-identical to the live file. `budget.py` gives
the same Odds API numbers before and after (+0 credits a day), and
`cfbd_budget.py` the same CFBD numbers (+0 calls). The extra run uses free
GitHub minutes (this repo is public).

What differs from the live file:

- a new first step, **Start the job clock**;
- the routing step lets every scheduled football run and a football relay run
  hand over at the end, and gives a football relay run its 280-minute hold;
- a new step, **Is a football relay link alive?**, before the Converge step;
- the Converge step counts a football relay run's hold from the job clock, and
  skips the freshness check for a league a relay run is checking itself;
- the last step is renamed **Relay — hand the hold to the next run of its
  chain** and starts the right chain (MLB or football).

MLB is unchanged: its relay, its 320-minute hold, its cap of 5 a day.

**Why you and not me:** this file has `cron:` lines. GitHub credits every
scheduled run to whoever last changed a file with a cron block. If that became
a bot, the schedules could stop silently.

---

## Click by click (Windows)

1. Open **File Explorer**, click **Downloads**, and delete any old
   `collect.yml` there (otherwise Windows saves `collect (1).yml`, and the name
   must be exact).
2. Open https://github.com/smh0602/gizmos-picks/blob/main/docs/upload/collect.yml
   and check the breadcrumb at the top reads **gizmos-picks / docs / upload /
   collect.yml**.
3. Click **Raw** (the button above the file's contents, on the right). The page
   now shows only the file's text.
4. Press **Ctrl+S**. In the Save window click **Downloads** on the left, make
   the **File name** exactly `collect.yml`, set **Save as type** to **All
   Files** if your browser offers it (so it does not become `collect.yml.txt`),
   and click **Save**.
5. Open https://github.com/smh0602/gizmos-picks/tree/main/.github/workflows
   and check the breadcrumb reads **gizmos-picks / .github / workflows**.
   ⛔ Not the repo's front page: a file uploaded there lands in the top level,
   where it never runs.
6. Click **Add file** (top right, next to the green **Code** button), then
   **Upload files**.
7. Click **choose your files** (the blue link in the middle of the box).
   ⛔ Do not drag a folder in. In **Downloads** pick `collect.yml` and click
   **Open**.
8. Check the page lists exactly **1 file**, `collect.yml`, with no `(1)` and no
   `.txt` in its name.
9. In the **Commit changes** box paste this as the first line:

   ```
   collect.yml: one football relay link keeps a run alive at every football deadline (upload of docs/upload/collect.yml)
   ```

10. Leave **Commit directly to the main branch** selected and click the green
    **Commit changes** button. GitHub replaces the existing file.

## What you should see afterwards

- On the **Actions** page, after the next football cron finishes (crons run
  late, so this can take a few hours), a run titled **collect [relay ncaaf
  nfl]** starts. Its last step's log says `relay: dispatching a successor`
  when it hands over, about every 5 hours. There is always at most one of them
  running, plus at most one waiting.
- Football crons that run while a relay run is alive finish quickly. Their
  log says `HELD: a football relay link converges ncaaf ...` and they turn
  green without rebuilding anything a deadline owes.
- In `data/latest/health.json` the `late:...` findings for football clear as
  each deadline is next built on time (within an hour), usually within a day.
- Football cards built within about 20 to 40 minutes of their time instead of
  hours late. Nothing else on the site changes: every pick, price and number
  is built the same way.

## How to tell it worked

- Open https://github.com/smh0602/gizmos-picks/blob/main/data/ncaaf/latest/relay-beat.json
  (and the same under `data/nfl/latest/`). It exists once a relay run has made
  its first check, and its `at` time moves forward every 15 to 35 minutes.
- In `health.json` there is no `relay:football` finding. If one appears, it
  says no relay run has checked football for over 2.5 hours while a game is
  near; the next football cron to finish restarts the chain by itself.

## If a hand run is ever needed

Start it with league `mlb`, `nfl` or `ncaaf`. ⛔ Never type exactly
`ncaaf nfl`: that is the relay's own name, and a hand run with it would
cancel the relay run that is holding.

Until you upload, the "runs" report lists `collect.yml` as waiting, and after
48 hours it says so in an issue: that is expected. I (or the next session)
check after your upload that the live file matches this one byte for byte and
that the first **collect [relay ncaaf nfl]** run is green.
