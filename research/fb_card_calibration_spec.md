# Football props card: calibrating its confidence

Status: APPROVED BY SAM 2026-09-24 — rule in section 2 set by Sam before any scoring; section 3 fixed by Claude before any scoring

⚠️ **Written and committed before any code that scores a calibration
exists.** Sections 2 and 3 are hashed by `test_prereg_gate.py`, so neither
can be edited after a result is seen. `[Sam, 2026-11-18]` So is section
3a, which re-registers the test; the text before it is pinned on its own.

## In plain English (for Sam)

- When the football props card has said 80–90%, those plays have hit
  about 41% (NFL) and 59% (college). Its confidence runs high.
- The fix tried here: learn, from plays **already graded**, how the
  card's printed number maps to what actually happens, and print the
  corrected number instead. Each week uses only plays graded before it.
- The corrected number replaces the printed one **only** if it predicts
  better by a margin that is unlikely to be luck, over at least 500
  graded plays. Otherwise the printed number stays, and the card carries
  a visible warning.
- `[Sam, 2026-11-18]` The test counted only cards made the old way, which
  stopped in September, so it could never reach 500. Sam re-registered it
  on the way the cards are made now: the same test and the same 500-play
  bar, counting only games from Monday 2026-11-23 on (section 3a). If it
  ever qualifies, the Monday email says so under "Needs you"; nothing
  changes on the card until Sam decides.

## 1. Scope and background

- The **football props card** (`card_fb.py`), NFL and college. Nothing MLB.
- **Found first (step 1 of Sam's request): no code bug.** Across all 113
  graded plays rated 80% or higher:
  - every side re-grades correctly;
  - every stat is the named player's own;
  - anytime TD won all 5 of its rows.

  The inflation is structural. The card rates every player on **last
  season alone** (2025), even when 93 of the 113 had already played 2026
  games. Samples of 7 games print 94%. And the board takes the most
  extreme ratings, which is exactly where the books' line disagrees with
  last season.

## 2. The rule `[Sam, 2026-09-24, set before any scoring]`

> "Map the card's raw probability to a calibrated one, using only picks
> graded before each week (walk-forward)."
>
> "The calibrated number replaces the raw one on the page only if its log
> loss is lower, one-sided p < 0.05, clustered by game, over at least 500
> predictions."
>
> "If it qualifies, apply it in this PR. The pick rule (EV > 0 at the
> best of Hard Rock, FanDuel and DraftKings, plus the existing price
> floors) then uses the calibrated number."
>
> "If it does not qualify, keep the raw number and show a visible warning
> on the card."

## 3. Definitions fixed by Claude before any scoring `[2026-09-24]`

⚠️ **Not approved by Sam. Frozen by Claude so nothing can be tuned after
seeing a result, and disclosed here so Sam can overrule any of it.**

| | |
|---|---|
| The picks | Every row of `data/<league>/latest/record-detail.json.gz` (the card's own graded record, `record_fb.py`) that carries a `confidence` and a graded result (`won` true or false), **both leagues**. A void or ungradable row is left out. |
| Raw probability | `confidence` / 100, the number the card printed. |
| Weeks | Monday to Sunday, keyed by the pick's card date. The mapping for week W is fitted on picks from card dates **before W's Monday**. |
| The mapping | Logistic recalibration: calibrated = logistic(a + b·logit(raw)), with raw clipped to [0.01, 0.99]. It is fitted by `fb_model.fit` (ridge 1.0 on the one standardised input, intercept unpenalised) on both leagues' earlier picks **pooled**: one mapping, because it is one card method. The fit needs `fb_model.MIN_TRAIN` (150) earlier picks; before that there is no mapping. |
| The scored predictions | Every pick in a week that has a mapping. Each is scored raw and calibrated against its own result. |
| Log loss | −[y·ln p + (1 − y)·ln(1 − p)], with p clipped to [1e-12, 1 − 1e-12] for both alike. |
| The test | d = raw loss − calibrated loss per scored pick, so d > 0 means the calibrated number predicted better. The mean of d is taken over every scored pick, **pooled over both leagues**. Its standard error is **cluster-robust by game** (league + game + kickoff date), CR1, with a one-sided test of mean d > 0 on Student's t with G − 1 degrees of freedom, via `mlb_refit.paired_test_clustered`. |
| Verdict | **QUALIFIES** if n ≥ 500, mean d > 0 and p < 0.05. **NOT YET MEASURABLE** if n < 500. Otherwise **DOES NOT QUALIFY**. |
| If it does not qualify | The printed number stays raw. The card's banner opens with the warning built from `calibration.band_flags`, and the page shows the test's status beside the band table. |
| After this PR | The test is re-scored every `card-fb` run and its status is shown. ⛔ **A later QUALIFIES is not applied automatically.** The page says it qualifies and is waiting for Sam, because changing what the card prints is Sam's decision; applying it is a separate PR. |
| Reported beside the verdict, not part of it | Per-league mean log loss, raw and calibrated. Stated against actual, in 10-point bands, raw and calibrated, on the scored picks. The mapping (a, b) each week. |

## 3a. Re-registered on the method the cards print now `[Sam, 2026-11-18]`

**Sam's decision, 2026-11-18** (changing a pre-registered test is his, rule 13). He was
asked: *"The football props-card calibration test you pre-registered counts only cards built
with the '2025-only' method, which stopped being used on 9-21 (NFL) and 9-19 (college). It has
157 graded picks (95 after the fix) and needs 500, so it can never finish. What should happen
to it?"* He chose *"Re-register on today's method (Recommended)"*: *"Same test and same
500-pick bar, counting only picks from the new registration date on, plus a line in the Monday
email if it ever qualifies."*

Written and committed before any code that scores it existed, and before any game it counts
kicked off. Nothing above it is edited: §2 and §3 are pinned on their own by
`test_prereg_gate.py`.

| | |
|---|---|
| The method | `season-blend+props-own`: the props method every football card prints today, NFL and college alike. |
| A card's props method | The card's `card_method` without the game model's part, `card_fb.game_method`'s `+game-<name>` (the last part `card_fb` appends). That part names the game model's champion, which makes the card's game lines; this test reads only the props rows (`days`), so `season-blend+props-own+game-HC` (college today) is the same method. Any other difference is a different method, and its rows are not counted: a props-model switch (`-last2`), signal 9 (`+signal9`) or a new props model prints a different number. |
| The registration date | **2026-11-23**, a Monday. |
| The picks | §3's picks (graded, rated rows of `days`, both leagues, a void left out) whose card's props method is the method above AND whose game kicks off on or after the registration date, by the kickoff's US Eastern date (`card_fb.et_date`). A row with no readable kickoff is left out. Nothing else is read: the weekly mapping is fitted only on these picks, so the first weeks after registration train it (no mapping before 150 picks, as §3) and are not scored. |
| Everything else | Exactly §2 and §3: raw probability, weeks, the mapping, the scored predictions, log loss, the test (pooled over both leagues, clustered by game), the verdict (**QUALIFIES** needs n ≥ 500, mean d > 0 and one-sided p < 0.05; **NOT YET MEASURABLE** under 500; otherwise **DOES NOT QUALIFY**), and what is reported beside it (per-league log loss, the 10-point bands raw and calibrated, each week's mapping). Nothing is tuned. |
| When it ends | Never by a date or a count. In a league whose props method changes, the later rows stop counting; registering again is Sam's. |
| The earlier arms | §3's test (`2025-only`) and the fixed card's arm (`season-blend`, `[Sam, 2026-09-24]`) are still scored and stored as they are, labelled superseded by this section. |
| If it qualifies | §3's "After this PR" holds: nothing is applied automatically; applying it is a separate PR and Sam's decision. The page has shown none of this since 2026-10-01, so the Monday email says it under "Needs you". |

**Why 2026-11-23, and why written here.** This repo registers a section added by a merge in
one of two ways: a date written into it (T65's `REGISTERED_FROM`, 2026-10-19, and T66 in
`fb_refit_spec.md` §3a), or the first Monday AFTER the merge day, read from git (T71 to T75,
§3e onward there). This test takes the first: the first Monday after the day this section was
written and committed (2026-11-18).

1. What it scores, the confidence each card prints, is published before kickoff whether or
   not this section has merged, so the merge day decides nothing about which predictions
   exist. Pre-registration needs every counted game to kick off after the rule was fixed; a
   written date gives that and cannot move. A game between 2026-11-23 and a later merge still
   counts, for the same reason.
2. The test is scored in the collector's `card-fb` pass, whose checkout holds one commit
   (collect.yml's `actions/checkout` sets no depth). Measured 2026-11-18 on a depth-1 clone:
   git's answer for the day a line was added is the clone's own commit day (2026-11-18,
   against 2026-11-10 in full history). A date read from git would move forward every run,
   and the test would never start.
3. A Monday, because §3's weeks run Monday to Sunday.

## 4. What runs

- `fb_card_calibration.py` scores the rule above. It rides `card-fb` and
  writes `data/<league>/latest/card-calibration.json` (with a freshness
  row), ~~which the page reads~~ (the page has read none of it since
  2026-10-01).
- ⛔ It never edits the card, a published pick, or anything MLB. There is
  no cron change and no spend.
- `[2026-11-18]` §3a as built: `counts` chooses the rows, `props_method`
  removes `card_fb.game_method`'s part (`test_fb_card_calibration.py`
  fails if card_fb ever appends anything after it), and the arm is
  stored as `test_reregistered`, beside each league's newest graded day
  of its method and of any method (`newest_graded`). The two earlier
  arms carry `superseded_by`. `status.py` puts any arm whose verdict
  reads QUALIFIES under "Needs you" in the Monday email;
  `watchdog.check_calibration_arm` reports DEGRADED (no repair, no
  issue) when a league graded card rows in the last 14 days but none of
  a registered arm's method for longer. A league that graded nothing
  (the off-season) is silent.

## Changelog

- **2026-09-24:** written and committed before any scoring code.
- **2026-09-24, first scoring: NOT YET MEASURABLE.** 157 picks were
  scored walk-forward, of the 500 needed; 345 graded picks exist in total,
  and the first week has nothing earlier to learn from. The correction
  cut log loss from 0.871 to 0.695 (NFL, 98 picks) and from 1.065 to
  0.701 (college, 59), with mean d = +0.247 and p = 0.008. But the rule
  needs 500, so **the card keeps its raw numbers** and carries the
  warning.
  - ⚠️ The fitted mapping is nearly flat (slope 0.07, then 0.01 on the
    logit scale). Every printed confidence maps to roughly 50–53%, so on
    this evidence the printed number carries almost no information about
    which props hit.
- **2026-11-18:** §3a added on Sam's decision: the same test re-registered
  on `season-blend+props-own`, games from 2026-11-23, the same bar. Root
  cause: §3 counted only `2025-only` rows, and the fixed card's arm only
  rows whose whole method was `season-blend`; the cards stopped printing
  both (the second when `+props-model` was appended, 2026-10-09), so both
  sat below 500 for good, and nothing said so. Written before any code
  that scores it; §2 and §3 are unchanged and pinned on their own by
  `test_prereg_gate.py`.
