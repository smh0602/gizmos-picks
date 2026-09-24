# Football props card: reading the current season, and shrinking thin samples

Status: APPROVED BY SAM 2026-09-24 — ship rule in section 2 set by Sam before any result; the formula and the scoring in section 3 fixed by Claude before any scoring

⚠️ **Written and committed before any code that scores the fix exists.**
Sections 2 and 3 are hashed by `test_prereg_gate.py`.

## In plain English (for Sam)

- Today the card rates every player on **last season only** (2025), and a
  7-game record can print 94%.
- The fix:
  - A player's **2026 games count first**, with 2025 as the starting
    point. Each new 2026 game makes 2025 count for less.
  - **Every record is pulled toward what players at his position usually
    do at that line**, so a thin sample cannot print 90% or more.
- It is scored on the props the card actually published and that have
  been graded, against the number the card printed. It goes live in this
  PR only under your ship rule (section 2).

## 1. Why the card reads 2025 only

- **The rule:** `card_fb.load_logs` takes the newest season in which the
  **median player has at least 6 games** (`MIN_GAMES`), and otherwise
  falls back to last season.
- **Why it exists:** on 2026-09-04 the college card picked the new 2026
  file (74 players, one game each), the 6-game floor refused every rate,
  and the board shipped 0 of 50 rows with a record, with no word why.
- **When it was meant to switch:** when the typical 2026 player reached 6
  games. The median is taken over **every** player in the file,
  including backups who rarely appear. Over all of 2025 the NFL median
  was only 9 games and college's exactly 6, so the switch would come
  around NFL week 11–12, and for college perhaps never. **In practice
  the card reads last season all year.**
- **Its docstring also forbids a blend** ("ONE SEASON, NEVER A BLEND").
  Sam reversed that on 2026-09-24. The reason given there — a rate
  becoming "a property of the file mix" — is answered here by weighting
  2025 **explicitly** and printing the weight.

## 2. The ship rule `[Sam, 2026-09-24, set before any result]`

> "The fixed card goes live in this PR if its log loss beats the current
> card's with one-sided p < 0.05, clustered by game."
>
> "If fewer than 500 graded props can be scored, it still goes live, but
> ONLY if it is not worse (mean log-loss difference ≥ 0). Reading the
> current season is a correction, not a new idea."
>
> "Otherwise the current card stays, and the PR says why."
>
> "Keep #155's calibration test running. Report picks from before and
> after the fix separately so they are never mixed."

## 3. The formula and the scoring, fixed by Claude before any scoring `[2026-09-24]`

⚠️ **Not approved by Sam. Frozen so nothing can be tuned after seeing a
result, and disclosed here so Sam can overrule any of it.**

**The fixed confidence** for one row (a player, market, side and line) on
card date D:

| | |
|---|---|
| His games | G25 = his 2025 games; G26 = his 2026 games dated **before D**. Each set passes the card's own `qualifying()` (the NFL snap floor). |
| The card's gates, unchanged | They are applied to G25 + G26 together: `market_rateable`, the 6-game floor (`MIN_GAMES`), college participation (`PARTICIPATED`), and the usage floor (`usage_level` on the combined, date-ordered games). A row failing any gate gets no rate, as today. |
| Hits | Exactly as today, per season: over is stat > line, under is stat < line, anytime TD is stat ≥ 1. That gives h25 of n25 and h26 of n26. |
| Season weight | Each 2025 game counts **w = 4 / (4 + n26)**. So with no 2026 games 2025 counts in full; after 4 it counts half; after 12, a quarter. |
| Weighted record | H = h26 + w·h25 and N = n26 + w·n25. |
| The position average p₀ | Across **every player at his position**, over their games that pass `qualifying()` **and in which he did this job** (a pass attempt for passing; a carry for rushing; a catch for receiving; a carry or catch for anytime TD), it is the share that clear this side at this line. It uses 2025 plus 2026 games dated before D. With fewer than 50 such games, p₀ = 0.5. |
| Shrinkage | confidence = (H + 12·p₀) / (N + 12). |
| Thin-sample cap | If N < 10, the confidence is capped at 0.89. **A thin sample never prints 90% or more.** |
| Printed | round(100 × confidence), as today. |

- **Why 12:** with it, ten perfect games against a position average of up
  to 0.8 stay under 90% ((10 + 9.6) / 22 = 89.1%). The cap makes the
  promise hold whatever p₀ is.
- **Why 4:** a new season's first four games already outweigh half of last
  season.
- **Both were chosen for those properties, before any scoring.**

**The scoring:**

| | |
|---|---|
| The props | Every row of `data/<league>/latest/record-detail.json.gz` that carries the card's printed `confidence` and a graded result (`won` true or false), **both leagues**: the props the card actually published. |
| Current | The printed confidence / 100. |
| Fixed | The formula above for the **same** player, market, side and line, as of that card's date. It uses only games before D, so it is walk-forward by construction: nothing about the prop's own game, or any later game, enters. A prop that the fixed card cannot rate (a gate) is left out of both. |
| Log loss | −[y·ln p + (1 − y)·ln(1 − p)], with p clipped to [1e-12, 1 − 1e-12] for both alike. |
| The test | d = current loss − fixed loss, so d > 0 means the fix predicted better. The mean is taken over every scored prop, **pooled over both leagues**. It is CR1 cluster-robust **by game** (league + game + kickoff date), one-sided, Student's t on G − 1 degrees of freedom, via `mlb_refit.paired_test_clustered`. |
| Ship | **LIVE** if mean d > 0 with one-sided p < 0.05. Otherwise, if n < 500, **LIVE** if mean d ≥ 0. Otherwise **STAYS**. |
| Reported beside it | Log loss and hit rate in 10-point bands for both, per league, and the n. |
| Kept apart (Sam) | Every card carries `card_method`. The graded record, its calibration buckets, the band table on the page and #155's test all report the methods **separately**. #155's registered test continues on the picks of the method it was registered on. |

## 4. What runs

- `card_fb.py` gains the fixed rating. It is live only if section 2 says
  LIVE, recorded as the card's `card_method`.
- `fb_card_fix.py` scores section 3 and writes
  `research/fb_card_fix_run_<date>.json`.
- ⛔ Nothing MLB. No cron change, no spend, and no published pick is
  edited.

## Changelog

- **2026-09-24:** written and committed before any scoring code.
