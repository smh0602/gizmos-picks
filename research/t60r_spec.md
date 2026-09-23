# T60R — the played-games backtest: direction rule and bar

Status: APPROVED BY SAM 2026-09-22 — bar option B — FROZEN

🔴 **APPROVED AND FROZEN.** `[Sam, 2026-09-22: "I approve the T60R
direction rule as written, and bar option B … The rule is frozen once
approved; weekly grading adds new games but never changes the rule."]`
⛔ **No part of section 2 or section 3 may be changed from here on.**
Weekly grading adds games; it never re-decides the rule, the thresholds
or the bar. A different rule is a NEW pre-registered test with a new id.

⚠️ Everything in this file was written and approved **before any
signal-vs-outcome number was computed.** `test_prereg_gate.py` enforced
that: it blocked every `t60r*.py` until the line above carried Sam's
dated approval.

## In plain English (for Sam)

You asked for a backtest of signals 1–8 on games already played, 2025 and
2026. To grade a signal against the spread or total, it first has to
**pick a side**. Today the dossier only displays the signals, so no side
exists yet. This file is the rule that picks the side, written before
anyone has compared a signal with a result.

~~Two things for you to decide, both below: the direction rule (section
2) and the bar (section 3).~~ **DECIDED 2026-09-22: rule as written, bar
option B.** Both are frozen.

The code now gets built, it runs once over 2025 and 2026, and then it
grades each new week by itself on a schedule. Because only a big edge is
detectable on this much history, a FAIL means "no big edge", not "no
edge".

---

## 1. What it grades

| | |
|---|---|
| Games | NFL 2025 + 2026 to date; FBS vs FBS 2025 + 2026 to date |
| Markets | **Full-game spread and total only.** No props: we hold no 2025 prop prices. |
| One row | One game, one market, **one side**. Never both sides. That is exactly the fault that stops T60 passing. |
| Price | The closing line. NFL: nflverse (`closing_spread`, `closing_total`, already stored for 285/285 games in 2025 and 32/32 finals in 2026). FBS: CFBD `/lines`, about 20–25 calls, free tier. |
| FBS line source | CFBD returns several providers per game. ⛔ The provider order is fixed **from the provider LIST the first call returns** (names only, no scores read) and written here before any grading. ~~(order not yet written)~~ **Observed on the first pull, 2026-09-22: ESPN Bet 1,542 lines · DraftKings 1,268 · Bovada 1,200 · "Draft Kings" 423** (one book, two spellings). **Order, as committed in code before any grading: DraftKings → Bovada → ESPN Bet.** "consensus", "teamrankings" and "numberfire" were in the typed order and never appear; they change nothing. ⚠️ See the changelog: this was written into the code, not here, and the spelling split was missed. |
| Spread sign | ⛔ Not assumed. The favourite by closing moneyline lays the points (CLAUDE.md, `run_line`). A game where the spread's sign disagrees with the moneyline is VOID, and counted. |
| Push | VOID. Out of every denominator. |
| Break-even | −110 (52.38%) for every row, the same as T60. |
| Never | Pooled with T60. |

**Games available, counted 2026-09-22** (presence of fields only, no
result compared with anything):

| | finals | with closing spread + total stored |
|---|---|---|
| NFL 2025 | 285 | 285 |
| NFL 2026 | 32 | 32 |
| FBS v FBS 2025 | 808 | 0 (needs CFBD `/lines`) |
| FBS v FBS 2026 | 157 | 0 (needs CFBD `/lines`) |

➡️ **The ceiling is about 1,282 games × 2 markets = 2,564 rows, before
any signal abstains.** The real count will be lower, because a game with
no clear vote is not played.

## 2. The direction rule

Each signal casts **+1** (home covers / over), **−1** (away covers /
under), or **0** (abstains). Everything uses only what was known before
kickoff: the lookahead filters from the plan (H2H `when < kick`; §4 date
cut; §5 rebuilt per game; §7 one-week lag; §8 weather blank).

**`M` = the home team's expected margin implied by the closing spread.
`T` = the closing total.**

| § | Spread vote | Total vote |
|---|---|---|
| 1 Market | 0. It is the price being tested. | 0 |
| 2 Head to head | Mean home margin in meetings inside 365 days (from THIS game's home side). Vote its sign vs `M` if at least 3 points away from `M`. | Mean combined points in those meetings vs `T`, same 3-point gap. |
| 3 Time of year | 0. It holds player yards from this week in past seasons, with nothing about margin or points. | 0 |
| 4 This season | Each team's last 4 finals before kickoff (any opponent): estimate = ((home PF − PA) − (away PF − PA)) ÷ 2. Vote vs `M` if at least 3 points away. Fewer than 2 prior finals for either team: 0. | (home PF + PA + away PF + PA) ÷ 2 over the same games, vs `T`, 3-point gap. |
| 5 Versus position | 0. Opponent yards allowed says little about which side wins. | Both defences' allowed-yards rank across QB/RB/WR/TE, as a fraction of the league (rank 1 = allows the most). Mean of the 8 ≤ 1/3: over. ≥ 2/3: under. Otherwise 0. |
| 6 Possession | Vote for the team with the higher share of the clock, if the gap is 4 points of share or more. | 0. Shares add to 100%, so they say nothing about points. |
| 7 Personnel | Vote against the team with at least 2 more players flagged out, as of the week before. | 0 |
| 8 Venue | 0. Home field is already in the line, and past weather is blank. | 0 |

**Play rule:** add the votes. **Play the side when the total is +2 or
more, or −2 or less.** Otherwise the game has no row in that market.

⚠️ **The thresholds (3 points, 4 points of share, 2 players, one third, a
net of 2) were chosen without looking at any data.** They are round
numbers, not fitted ones. ~~Sam may change any of them before
approving~~ — **APPROVED AS WRITTEN 2026-09-22 AND NOW FROZEN.** ⛔ A
threshold may not be moved to make a result look better; that is a new
test with a new id.

⚠️ **Four of the eight signals abstain on spreads, and five on totals.**
That is a statement about what each signal measures, not a verdict on
it. ~~If you want a signal to vote where it abstains, say how it should
vote.~~ **Sam approved the abstentions as written.**

## 3. The bar — the choice that matters most

The same maths as T60 (one-sided test against 52.38%, 80% power). What
it shows: **with at most ~2,500 rows, this backtest can only detect a
large edge.**

| effective n | smallest edge it can detect (α = 0.01) | (α = 0.05) |
|---|---|---|
| 600 | +6.4 pts (58.8%) | +5.1 pts (57.4%) |
| 1,000 | +5.0 pts (57.4%) | +3.9 pts (56.3%) |
| 1,500 | +4.1 pts (56.5%) | +3.2 pts (55.6%) |
| 2,000 | +3.5 pts (55.9%) | +2.8 pts (55.2%) |

Options:

- **A. T60's own bar** (55.4%, α = 0.01, n ≥ 2,774 as registered). ⛔ The backtest
  cannot reach that n. It would read **NOT YET MEASURABLE** until the
  weekly grading adds enough new rows, which is roughly 2027.
- **B. Recommended: α = 0.01 and effective n ≥ 1,000, PASS at
  hit rate ≥ 57.4% with one-sided p < 0.01** (+5 points). It keeps T60's strictness about luck,
  and it can pass on the history that exists. The catch: a real but
  smaller edge, say 2 points, reads FAIL here. So a FAIL means "no big
  edge", not "no edge".
- **C. α = 0.05, effective n ≥ 1,708, PASS at ≥ 55.4% with one-sided
  p < 0.05.** Can detect T60's 3-point
  edge, but 1 in 20 signal sets with no edge at all would pass by luck.

✅ **APPROVED: OPTION B.** `[Sam, 2026-09-22]` PASS at hit rate **≥
57.4%** with one-sided **p < 0.01** on an **effective n ≥ 1,000**.

### 3a. How the verdict is reported `[Sam, 2026-09-22, part of the approval]`

⛔ **Three numbers, always, in this order: 2025 alone, 2026 alone, and
combined.** Each carries its own hit rate, effective n and p-value.

- 🔴 **The PASS/FAIL verdict is the COMBINED number and only that.** The
  bar above is applied to it. ⛔ A season may not be dropped, swapped or
  read as the verdict because it looks better.
- ✅ **The per-season pair is reported beside it** so Sam can see whether
  the edge holds across the offseason.
- ⚠️ **Each season alone will usually sit under the n floor**, so it
  reports NOT YET MEASURABLE rather than a verdict. That is expected and
  is not a second test.
- ⛔ **No per-season split is ever promoted to a decision rule** — "it
  worked in 2025 so use 2025's version" is exactly the re-deciding this
  pre-registration forbids.

Under the n floor: **NOT YET MEASURABLE**, not a pass and not a fail (the
T37/T60 three-state rule). The n floor and the p-value both use an
**effective n clustered by game**, the way `shadow_fb.py` already does:
if a game's spread and total results move together, that game counts for
less than two rows. ⚠️ How many rows actually play is **not known
yet**: counting them means computing the votes, and that code is blocked
until approval.

## 4. After approval

⛔ Every step below runs the rule EXACTLY as section 2 and 3 state it.

1. Pull CFBD `/lines` for FBS 2025 + 2026 (~20–25 calls, free tier, no
   Odds API credits).
2. Build `t60r.py`: signals rebuilt point-in-time per game, votes, rows.
3. Run once over the history and report the verdict with its n.
4. Grade each new week automatically. This needs a cron, so Sam uploads
   that workflow file by hand (CLAUDE.md rule 3).
5. ⛔ A PASS does not change the card by itself. Wiring the signals into
   `card_fb.py` is its own proposal.

## Changelog

- **2026-09-22 (first run):** ⚠️ **MISTAKE, and its root cause.** The
  provider order was typed from memory into `t60r.py` instead of being
  read off the first pull and written into section 1, as section 1
  required. CFBD spells one book two ways ("DraftKings" / "Draft Kings"),
  and an exact-string match ranked the 423 "Draft Kings" lines last, so
  some games were priced from ESPN Bet or Bovada when a DraftKings line
  existed. Root cause: two labels compared as raw strings without first
  confirming they name the same thing. Fixed by comparing names
  spelling-insensitively; `test_t60r.py` now fails if the stored pull
  holds any provider the order does not recognise. The ORDER itself is
  unchanged. No hit rate was looked at before or during the fix, and the
  first run's verdict (NOT YET MEASURABLE) cannot have been affected in
  kind.
- **2026-09-22 (later):** ✅ **APPROVED BY SAM** — direction rule as
  written, bar option B, and the three-way reporting rule in section 3a
  added as part of the approval. Frozen from this point: weekly grading
  adds games and never changes the rule. Still nothing run at the moment
  of approval.
- **2026-09-22:** drafted. Proposed, not approved, not run. No
  signal-vs-outcome number was computed while writing it; the only data
  read was the count of finished games and whether their lines are
  stored.
