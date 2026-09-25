# MLB props card — calibration audit (investigation only)

**Kind: DESCRIPTIVE.** Nothing here changes the card, the model, a
coefficient, `blend`, a band, the board, or any published pick. Every fix
below is a **proposal for Sam**. None is implemented.

Reproduce: `python research/mlb_calibration_audit.py` (stdlib only). It
writes the numbers to `research/mlb_calibration_audit_run_2026-09-24.json`.

## Changelog

- **2026-09-25** — Sam approved proposals A to D; built in one PR.
  A: postponed games are settled-void and 2026-09-22 is graded (the
  audit's "48 gradeable picks" was 44: four more players did not play).
  B: hitter rows carry the shared per-band label (no band trips it yet;
  70–80 is −14.4 against the 15-point bar). C and D: pre-registered in
  `research/mlb_pitcher_cal_spec.md`; C2 qualified and ships, D qualified
  and does not (one ships). E and F are untouched.
- **2026-09-24** — First version. Graded record as built at
  2026-09-24T12:05Z: 31 machine cards (2026-08-23 → 2026-09-23), 1,411
  graded picks, 109 voids.

---

## The short version

1. **The MLB card's printed confidence runs high almost everywhere.**
   Stated 71.7% on average, delivered 61.7%, a gap of **−9.9 points**
   (95% range −12.5 to −7.3, clustered by game, 363 games).
2. **Pitcher rows are the problem.** Strikeouts: said 64.9%, hit 52.4%.
   Outs: said 64.6%, hit 49.8%. **On both markets, the price's own
   break-even predicts the result better than the card does** (details in
   §1c). The card's pitcher confidence is worse than just reading the odds.
3. **Hitter rows are much closer.** The 80–90% band, where 405 of the 726
   hitter picks sit (mostly "under 0.5 RBIs"), said 82.6% and hit 80.5%.
   That is within noise. The 70–80% hitter band runs 14 points high.
4. **None of the ten highest-confidence misses is a code bug.** Every one
   re-derives exactly from the stored logs and box scores: the right
   player, side, line and result. They lost for three reasons the card
   cannot see: a pitch limit, a first start back from a two-month layoff,
   and a 6-start perfect record read as near-certain. (Plus plain bad
   luck on 90% RBI unders, which should lose about 1 time in 10.)
5. **I found one real bug, in the GRADER, not the card.** A game postponed
   on 2026-09-22 means that whole day is **never graded**: 48 gradeable
   picks are missing from the record for good (§4, Proposal A).
6. **Football's three structural issues, asked of MLB:**
   - **Thin sample printed as near-certain:** yes, but only on pitchers
     (3 starts is enough to get rated). It is **not** what drives the
     overconfidence. Pitchers with 10–19 starts run further off than
     those with fewer than 10.
   - **Stale season:** **no.** MLB reads the 2026 logs only, refreshed
     every morning before the card. The MLB version of the problem is
     **stale form**: a pitcher back from a long layoff is rated on his
     pre-injury starts (§3b).
   - **The board picking the most extreme ratings:** **yes, on pitcher
     outs and on hitters where the card disagrees most with the market.**
     The more the card disagrees with the price, the worse it does (§3c).

---

## How this was measured

- **Source:** `data/latest/record-detail.json.gz`, the card's own graded
  record. Each graded row is joined back to the card that published it
  (`picks/<date>.json`). The grader writes the rows in card order, so the
  join is exact: **0 mismatches** out of 1,520 rows.
- **"Stated"** is the confidence number printed on the row. For pitchers
  it is `blend`, a 50/50 mix of the v4.0/v5.0 model and his own record at
  that line. For hitters it is his own smoothed record (`RECORD`, no model).
- **Voids** (the player never took the field) are left out of every
  number, as the record does.
- **Clustered by game.** Two props from one game share its weather,
  bullpen and score, so they are not independent. Every interval below
  adds the misses up within each game before measuring spread (a
  cluster-robust standard error, with the usual G/(G−1) correction).
  "Games" is the number of clusters. "Eff. n" is the independent-sample
  size those games are worth. Bands from fewer than 10 games get no
  interval; the number would mean nothing.
- **p** is one-sided: how likely a gap this negative would be if the
  card's numbers were honest (normal approximation on the clustered
  error).
- **Period:** every machine card graded so far in 2026, 2026-08-23 →
  2026-09-23. 2026-08-22 was hand-built and graded in the ledger, not
  here. 2026-09-22 is missing because of the grader bug in §4.

---

## 1. Stated vs actual, 10-point bands, per market

Columns: band · graded picks · games · **stated %** · **hit %** · gap
(hit − stated) · 95% range of the gap · eff. n · p.

### 1a. Pitcher strikeouts (380 graded, 282 games)

| Band | Picks | Games | Stated | Hit | Gap | 95% range | Eff. n | p |
|---|---|---|---|---|---|---|---|---|
| 50–60 | 76 | 71 | 56.1 | 39.5 | −16.6 | −27.5 to −5.8 | 78 | 0.001 |
| 60–70 | 214 | 183 | 63.6 | 53.7 | −9.9 | −16.6 to −3.2 | 214 | 0.002 |
| 70–80 | 72 | 70 | 73.1 | 59.7 | −13.3 | −25.2 to −1.5 | 66 | 0.014 |
| 80–90 | 18 | 18 | 84.3 | 61.1 | −23.2 | −46.1 to −0.4 | 17 | 0.023 |
| **All** | **380** | **282** | **64.9** | **52.4** | **−12.5** | **−17.6 to −7.5** | 386 | <0.001 |

### 1b. Pitcher outs (305 graded, 245 games)

| Band | Picks | Games | Stated | Hit | Gap | 95% range | Eff. n | p |
|---|---|---|---|---|---|---|---|---|
| 50–60 | 93 | 79 | 56.1 | 50.5 | −5.5 | −15.5 to +4.4 | 98 | 0.14 |
| 60–70 | 144 | 124 | 64.2 | 45.8 | −18.3 | −26.4 to −10.3 | 147 | <0.001 |
| 70–80 | 53 | 52 | 73.5 | 58.5 | −15.0 | −28.9 to −1.1 | 49 | 0.017 |
| 80–90 | 8 | 8 | 86.8 | 62.5 | −24.3 | too few games | — | — |
| 90–100 | 7 | 7 | 94.7 | 42.9 | −51.9 | too few games | — | — |
| **All** | **305** | **245** | **64.6** | **49.8** | **−14.8** | **−20.6 to −9.0** | 296 | <0.001 |

**An outs row the card rated 60–70% hit less often than a coin.** Every
pitcher band with enough games runs 10 to 18 points high.

### 1c. Pitchers: is the card better than the price?

Log loss: lower is better, 0.693 is a coin flip. "Break-even" is the
chance the price itself implies, **with the book's margin still in it**,
so it is a deliberately handicapped stand-in for the market.

| | Picks | Hit | Card said | Price break-even | Log loss, card | Log loss, break-even |
|---|---|---|---|---|---|---|
| Strikeouts | 380 | 52.4 | 64.9 | 55.9 | 0.721 | **0.693** |
| Outs | 305 | 49.8 | 64.6 | 55.1 | 0.768 | **0.689** |

Splitting the card's number into its two halves (strikeouts / outs):

| | Model half | Own-record half | Blend (printed) | Break-even |
|---|---|---|---|---|
| Mean stated | 62.6 / 62.2 | 67.2 / 67.0 | 64.9 / 64.6 | 55.9 / 55.1 |
| Log loss | 0.720 / 0.765 | 0.757 / 0.815 | 0.721 / 0.766 | **0.693 / 0.689** |

- **Both halves run high.** The own-record half is worse, but the model
  alone does not beat the price either.
- **It is not a v5.0 regression.** v4.0 cards: strikeouts −11.8, outs
  −15.0. v5.0 cards (from 2026-09-11): −13.6 and −14.5. Same story.
- **Overs are worse than unders** on both markets (strikeout overs −16.0,
  unders −8.3; outs overs −18.2, unders −12.5).
- **Flat 1-unit stakes at the printed price:** strikeouts −6.0% (±4.7),
  outs −10.0% (±5.3). Both are about what the book's margin alone costs,
  or worse. Said plainly: **the pitcher rows have not beaten the price.**

### 1d. Hitters (726 graded, 289 games)

| Band | Picks | Games | Stated | Hit | Gap | 95% range | Eff. n | p |
|---|---|---|---|---|---|---|---|---|
| under 60 | 30 | two cards only | — | — | — | too few games | — | — |
| 60–70 | 48 | 11 | 65.6 | 54.2 | −11.5 | −23.4 to +0.5 | 79 | 0.030 |
| 70–80 | 220 | 123 | 76.5 | 62.3 | **−14.3** | −20.5 to −8.0 | 233 | <0.001 |
| 80–90 | 405 | 235 | 82.6 | 80.5 | −2.1 | −6.1 to +2.0 | 360 | 0.16 |
| 90–100 | 23 | 22 | 90.6 | 87.0 | −3.7 | −17.9 to +10.6 | 22 | 0.31 |
| **All** | **726** | **289** | **78.2** | **71.6** | **−6.5** | **−9.8 to −3.3** | 479 | <0.001 |

The under-60 rows all come from two thin early boards (2026-08-27 and
08-29) that were topped up to reach the minimum board size. They are
listed in the JSON and left out here.

**By market** (only bands with ≥10 games):

| Market | Picks | Stated | Hit | Gap (95% range) | Worst band |
|---|---|---|---|---|---|
| RBIs (almost all "under 0.5") | 443 | 81.1 | 76.1 | −5.1 (−9.2 to −1.0) | 70–80: 77.5 → 64.6 (113) |
| Total bases | 132 | 77.4 | 72.7 | −4.7 (−11.7 to +2.3) | 70–80: 76.4 → 68.0 (50) |
| Hits | 105 | 73.6 | 60.0 | −13.6 (−21.7 to −5.5) | 70–80: 75.1 → 57.1 (42) |
| Hits+Runs+RBIs | 41 | 68.5 | 56.1 | −12.4 (−29.5 to +4.8) | 70–80: 73.9 → 40.0 (15) |
| Home runs | 5 | 11.2 | 20.0 | one game only | — |

- **Hitter rows are close to the price.** Log loss 0.577 printed against
  0.570 for the de-vigged market number the card itself stores (721 rows).
  A little worse than the market, not badly.
- Flat stakes at the printed price: **−1.1% (±2.6)**, about break-even.
- Rows from 2026-09-11 onward run closer (−4.3) than earlier ones (−7.8).
  Hitter rows have no model, so that is a time split, not a version
  effect.

---

## 2. The ten highest-confidence misses, traced end to end

For each one I re-derived, from the stored files and not from the card:
the record the card quoted (from `pitchers.json.gz` / `hitters.json.gz`,
games strictly before the card date, using the collector's own "did he
start" rule), the blend from its two halves, and the result from
`data/<date>/results/final.json.gz`.

| # | Date | Player, game | Bet | Price | Printed | Used | Result |
|---|---|---|---|---|---|---|---|
| 1 | 09-07 | Chase Burns, CIN @ LAD | **over 11.5 outs** | −130 HR | **98%** | model 98.9 (expected 16.3 outs, spread ±2.0); record 25/26 | **9 outs** on 44 pitches |
| 2 | 09-13 | Chase Burns, CIN @ MIL | over 9.5 outs | **+189** DK | 96% | model 95.2 (expected 13.7); record 26/27 | **9 outs** on 56 pitches |
| 3 | 09-09 | Zac Gallen, AZ @ KC | over 11.5 outs | −140 HR | 93% | model 95.7 (expected 16.4); record 17/19; **last start 07-07** | **10 outs** on 68 pitches |
| 4 | 08-28 | Christian Koss, AZ @ SF | under 0.5 RBI | −375 HR | 92% | record 29/31 started games; in lineup 23% | **2 RBI** (HR) |
| 5 | 09-19 | Ke'Bryan Hayes, CHC @ CIN | under 0.5 RBI | −450 BetMGM | 91% | record 62/68; in lineup 44% | **1 RBI** |
| 6 | 08-26 | Tanner Gordon, COL @ WSH | under 16.5 outs | −115 HR | 90% | model 79.0; record **6/6** | **21 outs** |
| 7 | 09-01 | Christian Koss, SF @ PIT | under 0.5 RBI | −525 HR | 90% | record 32/35 | **1 RBI** |
| 8 | 08-23 | Kyle Leahy, STL @ PHI | over 12.5 outs | −130 **Fliff** | 89% | model 90.2; record 21/24 | **12 outs** (missed by one) |
| 9 | 09-05 | Christian Koss, SF @ NYM | under 0.5 RBI | −450 HR | 89% | record 35/39 | **3 RBI** (2 HR) |
| 10 | 08-25 | Drew Cavanaugh, CIN @ SF | under 0.5 RBI | −350 HR | 88% | record 25/28; in lineup 21% | **2 RBI** |

**Checks, all ten:**

| Check | Result |
|---|---|
| Right player and team | ✅ All ten. The logged team matches the printed team. |
| Right side and line | ✅ All ten grade exactly as the record says. The box-score value equals the graded `actual`, and every game is `Final`. |
| Record reproduces | ✅ All ten reproduce exactly from the logs, point in time. |
| Blend reproduces | ✅ Printed model + recomputed record gives the printed blend to within rounding (e.g. Burns 97.5 vs 98; the model is stored to one decimal). |
| Look-ahead | ✅ None. Every record stops the day before the card. |

**Verdict: no code bug in any of the ten.** What they show instead:

- **#1–2, Chase Burns: a pitch limit the card cannot see.** His starts
  went 100 pitches (08-30), then 44 (09-07), 56 (09-13), 67 (09-18). On
  09-13 the market priced over 9.5 outs at **+189** (a 35% chance) and
  the card said **96%**, a 61-point disagreement. The model does read the
  previous start's pitch count, but only as a small linear nudge. It moved
  his expectation from 16.3 to 13.7 outs, with a spread of about ±2 outs,
  so it still put 9.5 far in the tail. **The market knew; the card did
  not.**
- **#3, Zac Gallen: stale form.** His previous start was **2026-07-07**,
  64 days before the card. The model's last-8 average (16.4 outs) and his
  17/19 record are all from before the layoff. First start back: 68
  pitches, 10 outs. This is the MLB version of football's stale season.
- **#6, Tanner Gordon: a thin perfect record.** 6 starts, all under 16.5
  outs. The own-record half read 100%, which pulled a 79% model up to
  90%. He also had five bulk-relief outings of up to 18 outs that the
  starts-only rule (correctly) leaves out. The shadow flags T21 (perfect
  short record) and T22 (shuttled arm) both apply here. They are
  pre-registered and not adopted, so they did not touch the printed
  number, as designed.
- **#4, 5, 7, 9, 10: 90% RBI unders that lost.** At 88–92% about one in
  ten should lose, and the 80–90 RBI band as a whole is on target (82.9
  said, 81.0 hit, 305 picks). Christian Koss is three of the ten: he was
  carded 25 times and won 18. Each row printed "in the lineup 23–27% of
  games" as a risk note. Nothing is wrong here beyond variance, though
  five of the ten biggest misses being one market is worth knowing.
- **#8, Kyle Leahy, 2026-08-23: priced at Fliff**, a book that is not one
  of Sam's five. **9 of the 32 picks on that first machine card were
  priced at Fliff.** No card after 2026-08-23 carries a Fliff price, so
  this was fixed at the time. It is noted here as history, not as a live
  defect. (The loss itself was by one out.)

---

## 3. Football's structural issues, asked of MLB

### 3a. A thin sample printed as near-certain — **present on pitchers, not the driver**

- **Hitters:** a row needs **25 started games**, and the smoothing
  ((hits + ½) / (games + 1)) is mild. The smallest sample behind any 80%+
  hitter row was 25 games; the median was 63. Calibration does not get
  worse on thinner records:

  | Hitter sample | Picks | Stated | Hit | Gap (95% range) |
  |---|---|---|---|---|
  | 25–49 games | 231 | 81.3 | 75.3 | −6.0 (−12.2 to +0.2) |
  | 50–89 | 222 | 77.7 | 72.5 | −5.2 (−10.1 to −0.2) |
  | 90+ | 273 | 75.9 | 67.8 | −8.1 (−13.7 to −2.6) |

- **Pitchers:** a row needs only **3 prior starts**, and the own-record
  half is **not smoothed at all**. A 3-for-3 reads 100% and adds 50
  points to the blend by itself. The smallest sample behind an 80%+
  pitcher row was **3 starts** (median 18). Gordon's 6/6 → 90% (#6) is
  the football "7 of 7 → 94%" in MLB form.

  | Pitcher starts | Picks | Stated | Hit | Gap (95% range) |
  |---|---|---|---|---|
  | 3–9 | 101 | 68.8 | 55.4 | −13.4 (−23.8 to −3.0) |
  | 10–19 | 183 | 65.2 | 47.0 | −18.2 (−26.1 to −10.2) |
  | 20+ | 401 | 63.6 | 52.1 | −11.5 (−16.4 to −6.5) |
  | perfect record (h = n) | 9 | 87.4 | 77.8 | too few games |

  **Thin samples happen, but they do not explain the gap.** The 10–19
  start group runs further off than the 3–9 group, and 20+ starts is
  still 11.5 points high. So shrinking thin records (what #158 did for
  football) would fix rows like Gordon's but **would not close most of
  the MLB pitcher gap.**

### 3b. A stale season — **no; stale FORM — yes, on a small, exploratory sample**

- **Season:** both logs are the 2026 regular season only
  (`pitchers.json.gz` and `hitters.json.gz` both say `season: 2026`).
  Every one of the 31 cards read logs pulled **the same day**, between 12
  minutes and about 9½ hours before the card was built (most cards: about
  4 hours). Football's bug, rating everyone on last season, **does not
  exist in MLB.**
- **Stale form:** the card rates a pitcher on his last 8 starts and his
  season record, however long ago those starts were.

  | Pitcher rows | Picks | Games | Stated | Hit | Gap (95% range) |
  |---|---|---|---|---|---|
  | last start **> 20 days** before the card | 24 | 13 | 72.2 | **41.7** | −30.5 (−53.4 to −7.7) |
  | last start ≤ 20 days | 661 | 318 | 64.5 | 51.6 | −12.9 (−16.8 to −9.0) |

  ⚠️ **The 20-day cut is mine, chosen while looking at this data.** 24
  picks from 13 games is thin. Treat it as a lead worth a pre-registered
  test, not as a finding. The same goes for hitters whose last 15 games
  run 15+ points below their season rate (46 picks, 73.2 said → 60.9
  hit, −12.3, range −23.9 to −0.7). They run worse than the rest (−6.0),
  but the sample is small.

### 3c. The board picking the most extreme ratings — **yes**

The board takes rows where the card beats the price (edge > 0), then the
highest confidence first. So it favours rows where **the card disagrees
most with the book**. If the book is usually right, those are exactly the
rows that run hottest.

Split each market into thirds by edge (card % − price break-even %):

| Market | Edge third | Picks | Mean edge | Stated | Hit | Break-even | Gap (95% range) |
|---|---|---|---|---|---|---|---|
| Outs | low | 101 | 2.2 | 59.3 | 54.5 | 57.1 | −4.8 (−14.1 to +4.4) |
| Outs | middle | 101 | 7.8 | 62.7 | 49.5 | 54.9 | −13.1 (−22.8 to −3.5) |
| Outs | **high** | 103 | **18.4** | 71.8 | **45.6** | 53.4 | **−26.2 (−36.0 to −16.4)** |
| Strikeouts | low | 126 | 2.2 | 60.3 | 52.4 | 58.1 | −7.9 (−16.2 to +0.3) |
| Strikeouts | middle | 126 | 7.6 | 63.5 | 45.2 | 55.9 | −18.2 (−27.5 to −8.9) |
| Strikeouts | high | 128 | 17.0 | 70.8 | 59.4 | 53.9 | −11.5 (−20.6 to −2.3) |
| Hitters | low | 242 | 1.4 | 75.4 | 71.9 | 73.9 | −3.5 (−8.9 to +1.9) |
| Hitters | middle | 242 | 4.5 | 78.4 | 70.2 | 73.8 | −8.1 (−14.1 to −2.2) |
| Hitters | high | 242 | 10.0 | 80.8 | 72.7 | 70.8 | −8.1 (−13.9 to −2.2) |

And for hitters, against the de-vigged market number the card stores:

| Card minus market | Picks | Stated | Market | Hit | Gap (95% range) |
|---|---|---|---|---|---|
| under 5 points | 28 | 61.4 | 57.3 | 53.6 | −7.8 (−21.7 to +6.1) |
| 5–15 points | 605 | 79.1 | 69.8 | 73.7 | −5.3 (−8.9 to −1.8) |
| **15+ points** | 88 | 81.3 | **63.4** | **65.9** | **−15.4 (−25.1 to −5.7)** |

- **Outs:** the more the card disagrees with the price, the worse it
  does. The top third claimed a 72% average and hit **45.6%**, below its
  own 53.4% break-even.
- **Hitters:** where the card is 15+ points above the market, the market
  (63.4%) was close to the truth (65.9%) and the card (81.3%) was not.
- **Strikeouts** do not follow a clean pattern: the high-edge third
  actually hit above its break-even. So this is clear on outs and
  hitters, and not proven on strikeouts.
- This is the same thing PR #155 found in football ("the board takes the
  most extreme ratings, and those are exactly the props where the books'
  line disagrees").

---

## 4. Proposals for Sam — none implemented

Each would ship with a guard that fails on the defect, as CLAUDE.md
requires. The ones that touch a number are **reserved for Sam** (rule 13):
they change `blend`, a coefficient or the board, and need a
pre-registered test first.

**A. Grader: a postponed game blocks its whole day forever. (A BUG.)**
`collect.py` grades a card only when `n_final == n_games`, counting only
`Final` games. On 2026-09-22, TOR @ BAL was **Postponed**, so the day
reads "15/16 games final — not settled" on every rebuild. **48 gradeable
picks** are permanently missing from the record; the 2 picks on the
postponed game should be voids. *Fix:* treat Postponed / Cancelled games
as settled-void. *Guard:* a `test_record_*` fixture day with one
postponed game must grade the other games and void that game's picks.
Better still, guard the class: any card older than 3 days that is still
ungraded should turn the watchdog red. This touches the permanent record's
denominator, so it is Sam's call even though it is a bug fix.

**B. Warn per band on MLB hitter rows too.** The pitcher rows already
print a per-band "runs hot" note. Hitter RECORD rows have no band and no
warning, yet their 70–80 band runs 14 points high on 220 picks. *Label
only*: no number changes. Reuse the per-band rule PR #155 put in
`calibration.py` (15+ points under, p < 0.01, ≥ 10 graded), so there
stays one copy of it.

**C. A pre-registered calibration test for MLB pitcher rows**, like #155's
football test: a walk-forward correction of the printed number (or a
blend with the price), scored by log loss clustered by game, with the
bar fixed before scoring. Today the price beats the card on both pitcher
markets. ⛔ Changing what `blend` is or how it prints is reserved for
Sam, and `blend` is the permanent calibration column.

**D. Smooth the pitcher own-record half** (a 3/3 must not read 100%), in
the spirit of #158. ⚠️ Section 3a says this fixes rows like Gordon's but
**not most of the gap**. It changes `blend`, so it needs a pre-registered
test. The T21 shadow column is already collecting the "perfect record"
half of this question, and I have **deliberately not scored `carried`
here**: it belongs to a registered test.

**E. Label stale form and pitch limits on the row** (descriptive, no
number changes): "first start in N days" when the last start was more
than a set number of days ago, and "last start was N pitches" when it was
well under his norm. Both change what a bettor can do, so they could
earn `actionable`. Whether either should *move* the number is a
pre-registered test, and the 20-day cut in §3b must not be reused as its
bar, because I chose it after seeing the data.

**F. Flag big disagreements with the price.** When the card is 15+
points above the de-vigged market (or 15+ over the break-even on outs),
say so on the row, e.g. "the books make this about 63%". It is the
honest label for §3c. Whether to cap edge or drop such rows from the
board is Sam's decision (the board filter is his instruction).

## What I did NOT change

`card.py`, `verify_card.py`, `collect.py`, every model coefficient,
`blend`, `carried`, the bands, the board, the parlays, any
`picks/<date>.json`, any workflow or cron, and any spend. No API call
was made. The only new files are this doc, its script and its JSON.
