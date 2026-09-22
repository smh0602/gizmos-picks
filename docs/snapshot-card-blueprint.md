# THE CARD BLUEPRINT — Sam's definitive process

**Stated by Sam, Aug 20 2026. Amended the same evening with the PAYOUT BAND.** Follow it in order. **Do not skip to the odds.**

> *"your job is to find the best bets while also looking for the best combos that allow me to 1.8x or more my money, whether or not your using alt lines or arent."*
> *"the normal bets we want to make are goint to be in the 1.8 to 2.1x range… we need to move lines around when pairing to find this so we can maximize our odss of winning."*

---

# 🔴 🆕 THE DIVISION OF LABOUR — READ THIS BEFORE STEP 1. **ledger rule 53.**

**Sam, Aug 22 2026:** *"i do agree, i dont want you to stop doing this tho, it should be up to me to decide whcih i feel comfortable with your job is to provide me the data"*

| | |
|---|---|
| **CLAUDE PROVIDES** | the data **and the read** — model, raw, blend, matched class, head-to-head, the price, and a stated recommendation |
| **SAM DECIDES** | which of it he is comfortable betting |
| ⛔ **NEVER** | **a play absent from the board because Claude did not like it** |

🔴 **A PLAY THAT FAILS A CHECK IS PRINTED WITH THE FAILING NUMBER ATTACHED. IT IS NOT DELETED.** **"Cut", "declined", "below the floor" and "flagged by rule 15" are LABELS ON A VISIBLE ROW — never a reason a row is missing.** ➡️ **Every check in this blueprint — STEP 4B's matched class, STEP 4's raw-rate gap, STEP 4C's head-to-head, the price rules — is a LABEL, NOT A GATE.**

✅ **THIS IS NOT A LICENCE TO WITHHOLD JUDGMENT.** Sam asked for the data **and** the read. **Flagging a bad price is still the job, and the recommendation is still stated.** ⛔ **What is not Claude's call is whether Sam sees the play at all.**

⚠️ **THE EVIDENCE, STATED BECAUSE IT CUTS AGAINST CLAUDE:** on **8/21 Sam named six plays and five won**, and **Claude argued against four of them on PRICE grounds** — the full row-by-row table is in `claude/pick-ledger.md`, ledger rule 53 and the 8/21 TABLE C section. **The price logic was defensible; delivering it as a REMOVAL was not.** ⚠️ **n=6, one slate. This changes WHOSE DECISION IT IS. It does not lower the bar on price and it re-tunes nothing.**

⛔ **ONE THING THIS DOES NOT OVERTURN, AND IT IS SAM'S OWN INSTRUCTION: STEP 6's "below 1.8x — do not show it."** **That is a rule Sam stated himself about PAIRS, in his own words, and rule 53 is about plays Claude removed on Claude's judgment.** ➡️ **A sub-1.8x pair still goes unshown; a play Claude dislikes does not.** ~~⚠️ **If Sam ever wants the sub-band pairs printed too, that is his call to make and it is not assumed here.**~~

✅ 🔴 🆕 **ASKED AND ANSWERED, 2026-08-22 — HE DOES NOT WANT THEM.** **Sam, asked directly whether sub-band pairs should be printed with a "below band" label: *"i dont want to see them at all"*.** ➡️ **1.8x is a HARD FLOOR. A pair below it is NEVER SHOWN — not printed, not labelled, not listed as declined.** ⛔ **THIS IS AN EXPLICIT, DELIBERATE EXCEPTION TO LEDGER RULE 53, SET BY SAM HIMSELF AFTER RULE 53 ALREADY EXISTED. A future session must NOT "fix" it back to rule 53's default — it is not an oversight and it is not a contradiction.** ⚠️ **Rule 53 governs plays CLAUDE dislikes. The 1.8x floor governs pairs SAM does not want to see. Different authorities, and only the second one removes anything.**

✅ **AND THE OTHER HALF, ANSWERED THE SAME DAY: 2.1x IS A SOFT TARGET, NOT A CAP.** **Asked whether an above-band slip should be excluded: *"if its a good bet its a good bet still show it, i mostly dont want anything belo 1.8"*.** ➡️ **An above-band pair IS shown, labelled with its multiplier.** **See STEP 6, and `claude/pick-ledger.md` ledger rule 28.**

---

# STEP 1 — Split the board into two groups BEFORE looking at a single price

## Group 1 — the bet candidates

**A) GOOD pitcher in a GOOD matchup → target STRIKEOUT OVERS and OUTS OVERS**

- **GOOD** = `K/9 ≥ 9.0` **AND** `ERA ≤ 3.50`, assigned **from prior starts only**.
- **GOOD matchup** = a lineup that **strikes out a lot**.

**B) BAD pitcher → target OUTS UNDERS, and possibly STRIKEOUT UNDERS**

- **BAD** = `K/9 < 9.0` **AND** `ERA > 3.50`.

⚠️ **MIXED** = meets exactly one criterion, and it is ~36% of starters. **MIXED changes WHICH MARKET you bet, never the weights.** High-K/high-ERA → strikeout overs only. Low-K/low-ERA → outs overs only. **Read the raw K/9 and ERA for anyone near a cut point** — Lambert at 8.87 / 3.11 is nominally "outs only" and is one hundredth of a K/9 from GOOD.

## Group 2 — every other starter on the board

**Study them exactly as thoroughly.** Group 1 is who Sam bets; Group 2 is mostly **data for another day** — though a Group 2 arm can still make the card if the number is wrong enough.

⛔ **Do not silently skip Group 2.**

---

# STEP 2 — Which stats matter. This is measured, not guessed.

## ✅ IN THE MODEL — use these

🔴 🆕 **THE WEIGHT COLUMN IS STRUCK — 2026-09-07, Monday sweep. EVERY NUMBER IN IT WAS v4.0's AND THE MODEL HAS BEEN v5.0 SINCE 2026-09-01.** ⛔ **This is the project's own banned pattern — a coefficient copied outside the doc that owns it — reproduced in the table a card builder reads first.** ➡️ 🔴 **READ EVERY COEFFICIENT FROM `claude/mlb-projection-model.md`, IN THE SAME TURN YOU PRICE THE PLAY. This page names the INPUTS and their SOURCES and deliberately states no weight.** ⚠️ **What the struck numbers cost in practice was small — the re-fit moved 13 of 16 constants by thousandths and the worst pricing gap anywhere on a realistic board is 0.053 K and 0.133 outs — but "small" is not "right", and a hard-coded copy is silently wrong the moment the model moves and does not announce itself.**

| Input | ~~Weight~~ 🔴 **READ IT FROM `claude/mlb-projection-model.md`** | Market | Source |
|---|---|---|---|
| **His mean K over last 8 starts** | ~~0.673~~ **v5.0 trailing-K slope** | strikeouts | statsapi game log |
| **Opponent meanK** | ~~0.575~~ **v5.0 opponent slope** ⚠️ **centred on the constant `claude/mlb-opponent-database.md` states internally — never on a number copied from anywhere else** | 🔴 **strikeouts ONLY** | `claude/mlb-opponent-database.md` |
| **Home / road** | ~~±0.151 K · ±0.189 outs~~ **v5.0 ± terms, both markets** ⛔ **two-sided: +home AND −road, never a one-sided bonus** | both | `isHome` in the game log |
| **His mean OUTS over last 8** | ~~0.638 / 0.759 / 0.317~~ **v5.0 TIERED `k` on his own trailing level** ⛔ **the pooled slope is a reference figure and is NOT shipped — pasting it prices every pitcher wrong** | outs | game log |
| **His PREVIOUS START's pitch count** | ~~+0.0371~~ **v5.0 POOLED pitch-count slope** ⛔ **do NOT tier it — that is a new model choice and needs a pre-registration** | outs | `numberOfPitches` |
| **Raw hit rate at the exact threshold** | mandatory cross-check | both | game log |
| **cvK · cvO · tail rate** | shape, not level | both | `claude/mlb-pitcher-database.md` |
| **corr(outs, K)** | is length a K argument for THIS arm? | pairing | `claude/pitcher-reliability.md` |
| **Times through the order** | late-game K decay | strikeouts | `claude/times-through-order.md` |

## 🆕 THE BLEND — write it down, it was never defined

`[stated as method, Aug 20]` The card quotes **model / raw / blend**. The blend is **50% Poisson-or-Normal model, 50% his RAW SEASON hit rate at that exact threshold.**

- **Strikeouts:** Poisson around `E[K]`.
- **Outs:** Normal around `mu` with **`SD = cvO × his season mean outs`**. ~~There is no fitted outs distribution; this is the working assumption and it should be tested at the monthly re-fit.~~ ✅ 🔴 **STRUCK 2026-09-07 — IT WAS TESTED, AND IT PASSED. T3 ran once at the 2026-09-01 re-fit, exactly as pre-registered, and CLEARED ALL THREE CRITERIA** `[n = 3,084 standardised residuals: mean +0.0543 · SD 1.0772 · q10 −1.3528 · q90 +1.3356]`**. The distribution is no longer an assumption; it is a measurement.** ⚠️ **Read the SD honestly: at 1.077 the tails are ~8% FATTER than Normal, so an outs probability is very slightly over-confident at the extremes — worth nothing on a 15.5 rung, worth naming on a far alt rung.** **Result in `claude/mlb-projection-model.md`; the register entry is CLOSED-PASSED.**
- 🔴 **Flag any play where model and raw differ by more than 10 points.** The model is a smoother and smoothers fail worst on metronomes.

## ⛔ BANNED — tested and dead

| Claim | Result |
|---|---|
| "Good stuff, so he'll go deep" | R² = 0.0008 |
| "This lineup racks up hits" / "he's been getting hit" | R² ≈ 0.000 both directions |
| "This lineup gets to starters early, fade the outs" | 🔴 **opponent → outs is t = −0.34, NULL** |
| "He went short last time" (previous-start OUTS) | t = −0.02 — **use pitch count instead** |
| "Extra rest, he'll go deeper" | −0.044, t = −3.98, confounded |
| Handedness / platoon splits | t = 0.97. Dead twice |
| Park, dome (the **roof/dome PROXY**) | null once opponent is controlled — ⚠️ **measured on the 40%-complete log and NOT confirmed on the full season; owed test T13a re-runs it** |
| ~~Weather~~ 🔴 **UNTESTED, NOT NULL** | ⛔ **Temperature and wind have NEVER been tested against a starter's K or outs, on any sample** ~~**, and no historical weather source exists in the stack.**~~ **— a historical source DOES exist since 2026-08-25 (`collect.py` mode `weather`; struck 2026-09-21).** **Carried forward as an operational default, not a measured null** — `claude/owed-tests.md` **T13b,** ~~**which is BLOCKED**~~ **OPEN AND UNSPECIFIED (no join, no pre-registered bar yet).** ⛔ **Never write "weather is null," and never substitute the roof proxy for it** |
| Sub-.500 opponent | ΔR² +0.0017 — meanK already contains it |
| Opponent adjusted for pitcher quality faced | real mechanism, t = 0.0 |

## 🔴 THE OUTS HALF OF THE BLUEPRINT — TESTED Aug 20, AND IT DOES NOT CONVERT

`[measured]` Full chain in `claude/backtest-results.md` RESULT 8.

| Sam's chain | Verdict |
|---|---|
| Grinding lineup → pitcher's P/PA rises | ✅ **+0.502, t=5.42 REAL** |
| → his pitch count rises | ✅ **+9.16, t=3.35 REAL — +5.2 pitches across the league spread** |
| → **outs fall** | ❌ **−0.60, t=−0.80 NULL — only −0.34 outs across the full spread** |
| Conditional on leash | ❌ **interaction t=0.79 NULL, tier direction runs BACKWARDS** |

🔴 **"Teams that get hits" and "teams that grind at-bats" are OPPOSITE lineup types.** `corr(opponent P/PA, opponent hits allowed) = −0.401`. **Do not bundle them.**

➡️ **STEP 1B selects the PITCHER, not the matchup.** A bad arm is a bad-outs bet because he is a bad arm. **Do not add an opponent argument to an outs play.**

⚠️ **One number is parked, not adopted:** GOOD-tier arms read **−2.78 (t=−1.68)**. ~10 specifications were run; that is inside chance. **A pre-registered single-specification test is owed at the monthly re-fit.**

---

# STEP 3 — Sources, and what each is actually for

| Source | Use it for | Warnings |
|---|---|---|
| **statsapi.mlb.com** | ⭐ **The spine.** Game logs, schedule, probables, boxscores | Free. CORS-open. **Full rebuild in 6.5 s** `[measured 8/21]` — RECIPE in `claude/mlb-data-stack.md`. ~~~2 min~~ **struck 8/21 late: the old estimate was off by ~20×** |
| **statsapi schedule `hydrate=probablePitcher`** | 🔴 **THE ONLY authority on WHICH TEAM a pitcher is on** | ⛔ **The odds feed groups both starters under one event and does NOT tell you which is home.** See the Aug 20 failure below |
| **baseballsavant.mlb.com** | Process stats — whiff%, chase%, barrel%, xERA, pitch mix | Read `window.data` in Chrome. ⚠️ Season aggregates — good for tonight, useless for backtesting |
| **fangraphs.com** | Advanced, batted-ball, plate-discipline, team batting splits | JS-rendered; same `window` trick. Export is members-only |
| **The Odds API** | 🔴 **The only source of** ~~**PrizePicks and**~~ **Hard Rock (and the other ledger-rule-48 books') prices, including ALT LADDERS** `[2026-09-21 Monday sweep]` **— PrizePicks values in the feed are goblin/demon LABELS, never prices (rule 46)** | ⛔ **NEVER through `WebFetch` — it fabricates.** Same-origin JSON in Chrome only. 🔴 **And it is a PARTIAL view of both books — see STEP 5.** |
| **scoresandodds.com/mlb/props** | Free sharp thresholds when credits are tight | Best-of-each-side — **shopping only, cannot de-vig.** No outs market |
| **baseball-reference.com** | Team advanced batting, one call for all 30 | Count the rows — a pull once dropped SEA silently |
| **statmuse.com** | Last-resort fallback only | 🔴 Stale windows, wrong players, truncates populations by ~83% |
| **rotowire.com/baseball/weather.php** | Conditions for the card's field 4 | Record it, **do not price it** |

## 🔴 NEW, Aug 20 — THE TEAM-ASSIGNMENT TRAP

`[measured]` The Odds API returns both starters inside one event object with **no team field on the player.** On Aug 20 the LAA@HOU event was read as *G. Rodriguez = HOU, Lambert = LAA*. **It is the reverse.** That single flip inverts **two** mandatory inputs at once — the opponent meanK **and** home/road — and it moved Lambert's `E[K]` by **+0.79** (5.57 → 6.36).

⛔ **Every card must resolve each starter's team from `hydrate=probablePitcher` and cross-check it against the opponents in his own game log** (a pitcher never faces his own team). **Two independent confirmations, every slate.**

---

# STEP 4 — Choose the props

**Good arms:** strikeout overs, outs overs. **Bad arms:** outs unders, sometimes strikeout unders.

⛔ **Never card an over on a BAD arm without saying explicitly why the rule is being broken.**
⛔ **Never fade an elite arm on a strikeout under.** Fade workload instead.
⛔ **One leg per pitcher.**

🔴 **Cross-check every play against his raw hit rate at that exact threshold.** A gap over ~10 points means the model is the suspect.

🔴 🆕 **AND THE GAP IS PRINTED ON THE ROW, NEVER A REASON TO DROP THE ROW (ledger rule 53).** **A rule-15 flag makes the play a SUSPECT and says so on the card, with the model number and the raw rate both visible.** ⛔ **It does not remove the play from Sam's board.** ⚠️ *(This is the same treatment the 8/21 card already gave its three rule-15 flags — Misiorowski +22.3, Yamamoto +32.4, Sale +10.6 were all CARDED WITH THE FLAG, not killed. Rule 53 makes that the standing behaviour rather than a one-slate choice.)*

---

# 🔴 STEP 4B — THE MATCHED-CLASS CHECK. **THE THIRD OPINION. MANDATORY ON EVERY CARDED PLAY.**

`[added Aug 21 2026 at Sam's explicit instruction]`

> *"i want you to show me notable game logs from other pitchers vs the same teams your favorite pitchers are playing today… backing up your reasoning"*
> — and then, when it was done for one pitcher only: *"don't just be doing this for sale in the future i want you to do this for every pitcher in your top 10."*

⛔ **This is not decoration.** On its first full run it **contradicted three of the TEN PLAYS IT WAS RUN ON and strongly confirmed a fourth that Sam had objected to.** ⚠️ 🆕 ~~"ten carded plays"~~ **corrected 8/21 late: the 8/21 card was EIGHT plays, and Luzardo — in the worked example below — was CHECKED but never carded. See the reconciliation note above the example.**

**After the model number and the raw hit rate, compute a THIRD independent number: how often comparable arms have cleared THIS EXACT THRESHOLD against THIS EXACT LINEUP this season.**

## 🔴 THE COMPARISON CLASS IS FIXED IN ADVANCE AND APPLIED IDENTICALLY TO EVERY PLAY — NEVER TUNED PER PITCHER

- **Comparable = starters whose season K/9 is within ±1.5 of the carded pitcher's.** ⚠️ `[2026-09-21 Monday sweep]` **THAT IS THE STRIKEOUT AXIS. `card.py` has, since 2026-08-23, selected OUTS comparables on the DURABILITY axis instead — trailing mean outs bucket `<14 / 14–16 / 16–18 / 18+`, point-in-time — labelled T24. `claude/owed-tests.md` records this as APPLIED IN CODE, NOT ADOPTED; the three-axis comparison is still owed. A hand card that uses K/9 for an outs prop disagrees with the machine card.**
- Report **both** the all-starts rate **and** the rate excluding sub-4-inning outings (`outs ≥ 12`), because openers and injury exits sit in the denominator. **Quote both; do not pick the flattering one.**
- **Report `n`.** 🔴 **If `n < 8`, the check is UNINFORMATIVE — say so and do not use it.**

⚠️ **WHY THE CLASS MUST BE MATCHED, NOT JUST "ELITE."** A first pass using `K/9 ≥ 9.0` as the class made **Misiorowski (13.60 K/9) look contradicted at 43%**, when he was simply being compared to arms **four strikeouts per nine below him.** 🔴 **A too-broad class MANUFACTURES A FALSE CONTRADICTION.** ⚠️ **And a too-narrow one manufactures nothing at all** — the matched band left Misiorowski at **n=1**, which is the honest answer: **nobody in baseball is comparable to him, so the check cannot speak.**

## HOW TO USE IT — the same way as the raw-rate check

| Reading | What it means |
|---|---|
| **Class agrees with the blend** | ✅ **The play is confirmed by three independent sources. Say so.** |
| 🔴 **Class disagrees by more than ~15 points** | **Treat it exactly like a model/raw gap: the play is a SUSPECT, and the disagreement MUST be stated on the card.** |

⛔ **IT DOES NOT RE-PRICE ANYTHING. It is a FLAG, not an INPUT.** The model already carries the opponent term. 🔴 **NEVER fold the class rate into the blend.**

🔴 🆕 **AND IT IS A LABEL, NOT A GATE — ledger rule 53.** **A play the class contradicts is SHOWN WITH THE CLASS RATE AND ITS `n` PRINTED BESIDE THE BLEND.** ⛔ **A ≥15-point disagreement is never on its own a reason the play is absent from the board.** ➡️ **Write `🔴 class 38% (24/64) vs blend 70.2% — 32 pts below` on the row and let Sam weigh it.** ⚠️ **The worked example below is exactly this: Yamamoto is marked `cut` in the teaching table and the ledger CARDED him with the flag attached — the ledger's behaviour is the correct one and is now the rule.**

⚠️ **STATE THE POST-HOC RISK EVERY TIME.** This is a subgroup chosen **after the board is known**, which is the exact shape of the specification-shopping that produced this project's two worst errors. **The fixed ±1.5 rule exists so the class cannot be tuned to the answer. ⛔ Do not add filters to it mid-card.**

## ⚠️ 🔴 THE WORKED EXAMPLE BELOW IS A TEACHING RUN, NOT THE CARD THAT SHIPPED — READ THIS FIRST

`[reconciled 8/21 evening against `claude/pick-ledger.md`]` **Two rows of the 8/21 example do not correspond to plays on the card that was actually logged:**

- **Luzardo o5.5 K appears with a class rate — but Luzardo had NO pitcher props in the feed on any book that afternoon**, and the ledger states explicitly that no price was asserted for him anywhere on that card. **He was checked, not carded.** ⚠️ **His markets DID appear in a later pull the same evening; the class figure is real, the carded status is not.**
- **Yamamoto o17.5 outs is marked `cut` here — and the ledger CARDED it as TABLE A row 8**, with the class disagreement stated on the page. **The check flagged it; the play shipped anyway with the flag attached.** 🔴 **That is the honest history and it is the more useful lesson: STEP 4B is a FLAG, and a flag can be overridden as long as the override is written down.**

✅ **Nothing in the example is deleted — it teaches the check correctly. It simply is not a record of what was bet.** ➡️ **The ledger is the record. This is the lesson.**

## SHOW THE LOGS, NOT JUST THE RATE

Under each carded play, list **2–3 notable individual lines** from the comparison class against that lineup — **the best, and at least one poor one.** **Sam asked for the logs themselves, not only the summary percentage.** 🔴 **A rate with no visible starts behind it is not evidence he can check.**

## 🔴 THE FIRST FULL RUN — 8/21. THE WORKED EXAMPLE.

| Play | blend | matched class (4+IP) | verdict |
|---|---|---|---|
| Manaea o3.5 K vs CWS | 86.9% | **92%** (59/64) | ✅ confirmed |
| Burke o3.5 K vs NYM | 85.4% | **93%** (42/45) | ✅ confirmed |
| Gore o4.5 K vs LAA | 76.9% | **90%** (35/39) | ✅ confirmed |
| Detmers o4.5 K vs TEX | 76.0% | **74%** (23/31) | ✅ near-exact |
| **Sale u18.5 outs vs MIL** | 72.0% | ~~**90%** (18/20)~~ → **90.5% (19/21)** on 4+IP starts, **92.0% (23/25)** all starts | ✅ **confirmed — and Sam had objected to this play.** 🔴 **Figures RE-MEASURED 8/21 evening; the ledger's numbers were right and these were stale** |
| Schlittler o4.5 K vs TOR | 87.8% | ~~**68%** (21/31)~~ → **62.1% (18/29)** on 4+IP starts, **54.5% (18/33)** all starts | 🔴 **26 pts below — re-measured 8/21 evening, and it is WORSE than this table said.** ⚠️ **But see STEP 4C: his own head-to-head is 7 K, 7 K, 7 K vs Toronto in 2026** |
| Luzardo o5.5 K vs STL | 74.6% | **52%** (14/27) | 🔴 23 pts below |
| Peralta u5.5 K vs BAL | 61.9% | **47%** (33/70) | 🔴 15 pts below |
| **Yamamoto o17.5 outs vs PIT** | 70.2% | **38%** (24/64) | 🔴🔴 **32 pts below — cut** |
| Misiorowski o6.5 K vs ATL | 75.9% | **n=1** | ⚠️ no comparison exists |

🔴 **THE YAMAMOTO CASE IS THE REASON THIS CHECK EXISTS.** His model number was **54.0%** and his raw rate **86.4%** — a **32-point gap.** Ledger rule 15 says the model is the suspect, so the play was carded **leaning on the raw rate.** **The matched class came in at 38% — on the MODEL's side.**

➡️ 🔴 **WHEN MODEL AND RAW DISAGREE, THE CLASS RATE IS A TIE-BREAKER — and here it said THE RAW RATE WAS THE LIAR.**

⚠️ **One instance. LOG EVERY FUTURE CASE BEFORE TREATING IT AS A RULE.**

---

# 🔴 🆕 STEP 4C — THE HEAD-TO-HEAD TIEBREAKER. **RUN IT ONLY WHEN THE INPUTS CONTRADICT.**

**Sam, Aug 21 2026:** *"when you see 2 contradictions, a pitcher who doesn't strike out batters and a lineup who strikes out a ton, i want you to look at the matchups between the two. so in this case in recent starts vs cinci has he gone over this line or under? remember when we check these we only look at this season and the last season to get the most recent stats on the matter."*

## The trigger

**Run STEP 4C when the pitcher's profile and the opponent's profile point OPPOSITE ways at the carded number.** The two live cases:

| Contradiction | Example |
|---|---|
| **Low-K arm vs a high-K lineup**, and the play is an UNDER | E. Rodríguez (6.4 K/9) vs Cincinnati (most strikeout-prone lineup in baseball) |
| **High-K arm vs a low-K lineup**, and the play is an OVER | Schlittler (11.2 K/9) vs Toronto (5th-hardest to strike out) |

⛔ **Do NOT run it on every play.** When the pitcher and the matchup agree, there is no contradiction to break and the head-to-head is just a second small sample pretending to be evidence.

## The window is TWO SEASONS. This season and last. Nothing older.

```
/api/v1/people/<id>/stats?stats=gameLog&season=<yr>&group=pitching&gameType=R
  &fields=stats,splits,date,isHome,opponent,name,stat,gamesStarted,inningsPitched,strikeOuts,numberOfPitches
   → run for BOTH years, filter splits to the scheduled opponent, gamesStarted only
```
⛔ **Never widen the window to rescue a thin sample.** A 2023 meeting describes a different pitcher and a different lineup.

## How to use it — and how NOT to

- ✅ **TIEBREAKER ONLY.** It breaks a tie between the pitcher's own rate and the matched class. ⛔ **It is NEVER folded into the blend** — same standing as STEP 4B.
- ⚠️ ✅ **PRINT `n` ON EVERY ROW, AND PRINT "NONE" WHEN THERE IS NONE.** `[measured 8/21]` **Four of the TEN ARMS CHECKED had never faced that night's opponent in 2025–26 — Burke, Prielipp, Manaea and Chandler.** ⚠️ 🆕 ~~"four of ten CARDED arms"~~ **corrected 8/21 late against `claude/pick-ledger.md` rule 50: TABLE A is eight plays, contains no Prielipp, and Chandler was a DECLINED play — so no set of ten CARDED arms holds all four names (rule 45).** **"No head-to-head" is a finding, not a blank to be skipped.**
- ✅ **Report the SHAPE, not just the count.** Rodríguez's 2026 meeting with Cincinnati — **3 K while being knocked out in the third on 85 pitches** — is worth more than the bare result, because it shows the strikeouts did not come even when everything else went wrong.
- 🔴 **REPORT IT WHEN IT ARGUES AGAINST THE CARD.** On its first run it contradicted two published verdicts (Schlittler, Gray) and confirmed one (Yamamoto). ⛔ **A tiebreaker that only ever gets quoted when it agrees is not a tiebreaker.**
- 🔴 ⚠️ **DO NOT RE-RANK A PUBLISHED CARD ON IT MID-SLATE.** Log the disagreement, carry it to the next card. **Re-weighting evidence the moment it says something more exciting is the documented failure this project has the pre-registration register for.**

## 🔴 🆕 AND IF HE FACED THEM INSIDE 30 DAYS, HAIRCUT THE HIGH THRESHOLDS — ledger rule 51

`[measured 2026-08-21 — 296 rematches inside 30 days, mean gap 15.2 days]`

**A strong first meeting buys NOTHING the second time.** Conditional on a first meeting of **5+ K**:

| Next start reaches 4+ K | |
|---|---|
| vs **anyone** | **1363/1826 = 74.6%** |
| vs the **same lineup**, ≤30 days | **116/173 = 67.1%** |

➡️ **67.1% is just the league base rate. Whatever edge he had, they have seen it.**

✅ **THE EFFECT IS THRESHOLD-DEPENDENT, AND THAT IS THE USEFUL PART.** At a **3+ K** bar the same split is **87.5% → 84.4%, about three points**, against roughly **eight** at 4+ K. ➡️ 🔴 **A REMATCH IS A REASON TO DROP A RUNG, NOT TO DROP THE PITCHER.**

⚠️ 🔴 **THE EPISTEMICS MUST BE QUOTED EVERY TIME THIS IS USED.** **The PRE-REGISTERED specification FAILED** — it asked for a mean-K drop ≥ 0.5 with |t| ≥ 2.0 and got **0.30 with t = −1.78.** **The threshold analysis above was run afterwards, on the same data, and is EXPLORATORY — looking a second way after the primary fails is specification shopping, which is this project's own documented worst error.** ⛔ **Do not fit it. Do not present it as established.** **The re-specified version is registered in `claude/owed-tests.md` for the September re-fit.**

**How to detect it:** the two-season game log you already pulled for the head-to-head answers it — same pitcher, same opponent, date gap ≤ 30 days. **State the gap in days on the card row.**

# STEP 5 — Odds. **ALT LADDERS ARE MANDATORY.**

🔴 **Pull the markets the collector requests — `collect.py`'s `PITCHER_MARKETS` owns the list.** `[verified 2026-09-14 from a fresh clone]` **Today that is THREE: `pitcher_strikeouts`, `pitcher_outs`, `pitcher_strikeouts_alternate` — so `3 markets × 2 regions = 6 credits per game.`** **Separate market keys, extra credits. Budget for them.**

⚠️ 🔴 **~~"…`pitcher_outs_alternate` on every card"~~ STRUCK 2026-09-14 — THIS LINE CONTRADICTED THIS DOC'S OWN STEP 5 TWO SCREENS BELOW IT.** **The collector has NOT requested `pitcher_outs_alternate` since ledger rule 61, because Hard Rock posts no alternate outs market at all (Sam-confirmed AT THE BOOK), and the same section already says so.** ⛔ **A four-market mandate at the top of STEP 5 and a three-market reality at the bottom of STEP 5 is a doc arguing with itself in one section.** ⏳ ⛔ **WHETHER THE FIVE-BOOK PULL SHOULD RE-REQUEST IT IS STILL SAM'S INTERACTIVE CALL — unchanged, and not decided here.** ✅ **THE ALT LADDER ITSELF IS STILL MANDATORY: `pitcher_strikeouts_alternate` is in the pull and is stored.**

## 🔴 MEASURED Aug 20 — WHAT EACH BOOK ACTUALLY POSTS

⚠️ **Read this table as a description of THE FEED, not of the books.** Every "only" below is an observation about an Odds API response.

| | Hard Rock | PrizePicks |
|---|---|---|
| `pitcher_strikeouts_alternate` | **9–11 rungs — ~~⚠️ OVERS ONLY~~ 🔴 OVERS ONLY *IN THE FEED*. The book itself offers BOTH SIDES — Sam bets there and confirms it.** | 5–7 rungs, **OVERS ONLY in the feed** |
| `pitcher_outs_alternate` | 🔴 **NONE AT ALL. Zero rungs, all six arms, 8/20 — and Sam confirms this independently AT THE BOOK, not just in the feed. Outs on Hard Rock is one two-way standard line.** | ✅ **2–4 rungs** (e.g. Cole 14.5 / 17.5 / 20.5) |
| `pitcher_outs` (standard) | ✅ one two-way line | sometimes |
| Pricing | real odds that multiply honestly | 🔴 **NO PER-LEG PRICE. ~~flat −137 on goblins, +100 on demons~~ — STRUCK Aug 21: those are the feed's LABELS for goblin/demon, not quotes. The SLIP is priced by pick-count and multiplier. ASK SAM.** |

➡️ ~~🔴 **THE ONLY UNDER YOU CAN BET ON HARD ROCK IS THE STANDARD LINE'S UNDER SIDE.** There is no alternate under rung, for strikeouts or for outs. **When the band math asks for a different under number, say the rung does not exist — do not name one.**~~ 🔴 **STRUCK Aug 21 — FALSE. Sam bets Hard Rock and confirms you CAN bet the under on an alt strikeout rung there.**

🔴 **CORRECTED, Aug 21:** **THE ODDS API FEED CARRIES ONLY THE OVER SIDE OF HARD ROCK'S ALTERNATE STRIKEOUT LADDER. THE BOOK ITSELF OFFERS BOTH SIDES.** What was measured was real and reproducible — `pitcher_strikeouts_alternate` came back with only `Over` outcomes. The error was the inference: **"the feed has no under side" was written down as "the book has no under side."**

⚠️ **The Hard Rock OUTS finding is NOT affected and stands:** `pitcher_outs_alternate` genuinely does not exist on Hard Rock — no alt outs ladder at the book, only the one two-way standard line. Sam confirms that one independently.

➡️ 🔴 **STANDING PROCEDURE — when the band math wants an alternate UNDER rung on Hard Rock:** **do NOT say the rung does not exist.** Say **the feed does not carry its price**, **name the rung**, and **ASK SAM to read the price off the app.** This is exactly the procedure already in place for PrizePicks in-app multipliers. *(The claim that "the requested Bradish u4.5 does not exist on Hard Rock" was wrong — it exists; the FEED just does not price it.)*

⛔ **Reconcile this with the phantom-rung rule — both hold at once: NEVER ASSERT A PRICE YOU HAVE NOT SEEN.** Naming a rung the book plausibly offers and asking Sam for its price is fine. **Quoting a number you invented is not.**

⚠️ **THE HISTORY ON THIS EXACT QUESTION, both directions:** ~~"Hard Rock posts one point per pitcher"~~ was false and cost two days; ~~**"Hard Rock alt ladders are two-way" is the opposite error. Both are wrong.**~~ 🔴 **That parenthetical is itself struck Aug 21 — the ladders ARE two-way at the book. This doc set has now been wrong in BOTH directions on Hard Rock's ladders, so state the provenance of every claim about them.**

🔴 **THE FEED IS NOT THE BOOK — generalise it.** ⚠️ ~~**PrizePicks' feed is not the app.**~~ 🔴 **Widened Aug 21: this is not a PrizePicks quirk.** Sam has found lines in the PrizePicks app three times the feed did not have, **and it has now happened on Hard Rock too.** ➡️ **AN ABSENCE IN AN API RESPONSE IS EVIDENCE ABOUT THE API, NEVER ABOUT THE SPORTSBOOK.** **Report what the feed shows and ask him to check the app.** *(~~Third time~~ 🔴 **FIFTH time, updated Aug 21 evening — count reconciled against the list, ledger rule 45.** The five: "Hard Rock posts no alt ladders at all" · "Hard Rock's alt ladders are overs-only" · WebFetch's 27 fabricated events · the feed omitting Luzardo's entire pitcher market while carrying his game · **and the worst, "PrizePicks charges a flat −137" — the feed's goblin ENUM read as a price.**)*

## 🔴 STRUCK Aug 21 — `−137` IS NOT A PRIZEPICKS PRICE. IT IS THE FEED'S ENCODING FOR "GOBLIN."

`[measured 2026-08-21]` **Across 7 games × 4 markets, PrizePicks returned exactly TWO distinct values in 145 outcomes: `−137` (×77) and `+100` (×68).** The same pull returned **80 distinct prices from hardrockbet, 73 from espnbet, 28 betparx, 27 underdog, 23 fliff, 18 ballybet, 1 pick6.** **No sportsbook prices 145 props at two numbers.** **`−137` = goblin (easier rung), `+100` = demon (harder rung). A LABEL, NOT A QUOTE.**

**Sam caught it from the app:** *"some of your odds are wrong still, your giving me a lot of alt lines that are priced wrong, for example sean burkes 3.5 is not priced at −137… you can't keep giving me false info."*

⛔ **CONSEQUENCE: every "break-even 57.8%", every "edge +X" and every EV figure ever computed on a PrizePicks play is arithmetic performed on a constant. Those numbers are MEANINGLESS — not merely imprecise.** On the 8/21 card that voids the quoted edges of **+27.6, +19.1, +18.2, +18.1 and +12.4 — five of the ~~seven~~ EIGHT carded plays.** *(🆕 denominator corrected 8/21 late against `claude/pick-ledger.md`, which is authoritative: the 8/21 card is **EIGHT plays, five of them PrizePicks rows**. The five voided edges are unchanged.)*

⚠️ **PrizePicks does not price rungs at all.** It is a DFS product: **the SLIP is priced by pick-count and multiplier, and a goblin reduces the multiplier.** **There is no per-leg American price to break even against.**

### 🔴 THE STANDING RULE — ledger rule 46 / pre-publish check 31

**A PRIZEPICKS PLAY MAY BE RANKED BY PROBABILITY BUT MUST NEVER CARRY A BREAK-EVEN, AN EDGE, OR AN EV FIGURE.** Quote **`model / raw / blend / matched class`**, then **ASK SAM FOR THE IN-APP MULTIPLIER.** ⛔ **Do not derive one from the feed.**

### 🔴 THE OTHER STANDING RULE — ledger rule 47 / pre-publish check 32

**BEFORE TREATING ANY BOOK'S PRICES AS REAL, COUNT ITS DISTINCT VALUES IN THE PULL.** A book returning **1–2 distinct prices across dozens of outcomes is emitting LABELS, NOT QUOTES.** **One line of code, and it would have caught this on day one.**

⚠️ **FIFTH INSTANCE of a fact about a QUERY written down as a fact about the WORLD** — after ~~"Hard Rock posts no alt ladders"~~, ~~"Hard Rock's alt ladders are overs-only"~~, WebFetch's 27 fabricated events, and the feed omitting Luzardo's entire market while carrying his game. 🔴 **The worst of the five: it was load-bearing for the project's stated premise and it survived every audit for days.**

✅ **WHAT SURVIVES, PRECISELY — do not over-correct:**
- ✅ **The model probabilities are UNTOUCHED.** Nothing about `E[K]`, `mu`, the raw rates or the matched-class check depends on this.
- ✅ **Hard Rock prices are REAL** — 80 distinct values in the same pull. **Every Hard Rock edge, break-even, de-vig and pair multiplier STANDS.**
- ✅ **"At a flat payout, take the lowest rung that clears" SURVIVES with a new justification:** not that PrizePicks charges −137 everywhere, but that **the 2-pick multiplier barely moves with rung difficulty** — Sam's real slips returned **1.8x, 1.9x and 2.0x.** **A harder rung for a near-identical multiplier is still a donation.**
- ✅ **The DFS thesis survives in WEAKENED form:** PrizePicks' payout structure is insensitive to rung difficulty in a way a sportsbook's is not. ⚠️ **It can no longer be quantified from the feed, and it was never measured — it was inferred from an encoding.**

⚠️ **STILL OPEN, DO NOT RESOLVE BY GUESSING:** Sam says Burke's 3.5 rung *"is not priced at −137."* **That confirms the price is fake; it does NOT establish whether the 3.5 rung exists in the app at all.** The feed has shown rungs that did not exist (three phantom rungs) and hidden rungs that did. ⛔ **An open question for Sam. Assert the rung in neither direction.**

## 🔴 🆕 THE ODDS SOURCE IS FIXED: ~~SPORTSBOOKS ONLY. **PULL `us,us2`**~~ ~~**HARD ROCK ONLY. PULL `us2` — NOTHING ELSE.**~~ 🔴 🆕 **WIDENED 2026-08-23 — FIVE BOOKS, AND `regions=us,us2` AGAIN.**

🔴 🆕 **WIDENED 2026-08-23, IN SAM'S OWN WORDS** — recorded in `github.com/smh0602/gizmos-picks` `CLAUDE.md` and commit `91b0290`: *"lets just only use the top 5 sportsbooks in the USA, hardrock, draftkings, fanduel, ceasars, and bet MGM"*. ➡️ **THE STANDING SET IS FIVE BOOKS — Hard Rock (`hardrockbet` / `hardrockbet_oh`), DraftKings, FanDuel, Caesars (`williamhill_us`), BetMGM — and the props pull is `regions=us,us2` AGAIN, because FOUR OF THE FIVE LIVE IN `us`.** ⛔ **`us_dfs` STAYS BANNED, and PrizePicks is still NEVER a source of a NUMBER (ledger rule 46).**

⚠️ 🔴 **A STRIKE THAT REVERSED — SAID OUT LOUD SO A FUTURE READER IS NOT CONFUSED BY IT.** **The ~~`us,us2`~~ struck in the heading above was struck on 2026-08-22, and it is CORRECT AGAIN as of 2026-08-23.** **The strike is kept because the strike is the RECORD of what was believed; it is NOT the instruction.**

🔴 ⛔ **DO NOT READ THE CURRENT REGION/BOOK SET OFF THIS LINE. THE OWNER OF IT IS `claude/pick-ledger.md` RULE 48 — READ IT THERE, EVERY PULL.** ⚠️ **THE SET HAS MOVED THREE TIMES IN THREE DAYS** — `us,us2` (8/21) → `us2` only (8/22) → five books on `us,us2` (8/23) — **so any bare restatement in this doc goes stale inside a day. This doc POINTS AT rule 48; it never restates the set bare.**

**Sam, Aug 22 2026 — this SUPERSEDES AND TIGHTENS the instruction below:** *"i onlt want to see hardrock odds from now on for all props"*

**Sam, Aug 21 2026:** *"from now on i want you to pull all odds from sportsbooks not prizepicks, i see the pattern of you messing up is when you are pulling odds from alt lines on prizepicks. to avoid this let's just pull our odds from hardrock and other sports books."*

🔴 **This is enforced at the REQUEST, not at the write-up.** `us_dfs` is the region carrying PrizePicks and pick6 — **the two books that returned 2 and 1 distinct values in the 8/21 pull.** Omit the region and a fake price cannot reach a Price column, because it never enters the working set. ~~🆕 **The same logic now drops `us`: Hard Rock lives in `us2` ONLY, so `regions=us2` alone is correct and sufficient for every prop on every card.**~~ 🔴 **STRUCK 2026-08-24 — REVERSED BY THE 8/23 FIVE-BOOK WIDENING. The standing props pull is `regions=us,us2`; read the current set from `claude/pick-ledger.md` rule 48.**

```
regions=us          ✅  PULLED. draftkings · fanduel · williamhill_us (Caesars) · betmgm  — four of the five books
regions=us2         ✅  PULLED. hardrockbet · hardrockbet_oh (Hard Rock)  — espnbet · fliff · betparx · ballybet ride along free
regions=us_dfs      ⛔  prizepicks, pick6  — NEVER for a number
```

💰 ~~**AND IT HALVES THE BILL — BUDGET FOR IT AT THE NEW NUMBER.**~~ 🔴 **STRUCK 2026-08-24 — THE HALVING IS REVERSED. Two regions are live again under the five-book widening, so the per-game cost is back to `markets × 2`.** ✅ **THE BILLING FORMULA ITSELF STANDS, UNCHANGED AND STILL MEASURED:** `[measured 2026-08-22]` **The Odds API bills `cost = unique markets × regions, per game`, confirmed by a probe returning `x-requests-last: 1` for one market on one region.** ~~**OLD: 4 markets × 2 regions = 8 credits per game. NEW: 4 markets × 1 region = 4 CREDITS PER GAME.**~~ 🔴 **STRUCK — the one-region figure died with the `us2`-only pull.**

🔴 ⛔ **AND READ THE LIVE MARKET COUNT FROM THE COLLECTOR RATHER THAN ASSUMING FOUR.** `[measured 2026-08-24 from `collect.py`]` **`PITCHER_MARKETS` is THREE markets — `pitcher_strikeouts`, `pitcher_outs`, `pitcher_strikeouts_alternate` — so a PITCHER PULL IS `3 × 2 = 6 CREDITS PER GAME`, not 8 and not 4.** ⚠️ **The collector does NOT request `pitcher_outs_alternate` at all (ledger rule 61).** ⏳ ⛔ **WHETHER THE FIVE-BOOK PULL SHOULD RE-REQUEST `pitcher_outs_alternate` IS AN INTERACTIVE DECISION FOR SAM — NOT ONE A SWEEP MAKES.**

✅ **AND THE CROSS-BOOK SANITY CHECK SURVIVES FOR FREE — which is why this costs nothing in safety.** `[measured 2026-08-22]` **A `us2` pull still returns several books in the same response at no extra cost: a probe returned `hardrockbet`, `espnbet` and `fliff` on one market, and `hardrockbet_oh`, `ballybet` and `betparx` also live in that region.** ➡️ **STEP 5's distinct-price count (ledger rule 47 / check 32) still has a comparison set in every pull.**

⚠️ ~~**WHAT IS GIVEN UP, SAID HONESTLY: price shopping against DraftKings, FanDuel, BetMGM, BetRivers, Bovada and BetOnline.** ✅ **It was never actionable — Sam bets Hard Rock and PrizePicks only, so a better DraftKings price was information he could not use.** ⛔ 🔴 **RESIDUAL RISK, RECORDED: a Hard Rock price offside versus the wider market is no longer visible against the `us` books. The `us2` siblings are the remaining check.**~~ 🔴 **STRUCK 2026-08-24 — THAT PARAGRAPH DESCRIBES THE 8/22 NARROWING, AND SAM REVERSED IT ON 8/23.** ➡️ **DraftKings, FanDuel, Caesars and BetMGM ARE BACK IN THE PULL, so NOTHING IS GIVEN UP — and the RESIDUAL RISK IT RECORDED NO LONGER EXISTS: a Hard Rock price offside versus the wider market is VISIBLE AGAIN against the `us` books.**

⏳ 🔴 **THE ONE QUESTION THE WIDENING LEAVES OPEN, AND NOTHING RECORDS SAM ANSWERING IT: does "CARD ONLY PRIZEPICKS AND HARD ROCK" (ledger rule 19) WIDEN WITH THE FIVE-BOOK SET?** ⛔ **DO NOT GUESS IT AND DO NOT RESOLVE IT IN A SWEEP.** ➡️ **UNTIL HE ANSWERS: CARD THE TWO; PAIRS STAY HARD ROCK-ONLY (the code enforces it, and only Hard Rock multiplies); and A PLAY PRICED ONLY AT DRAFTKINGS / FANDUEL / CAESARS / BETMGM IS SHOWN WITH ITS BOOK NAMED** (ledger rules 53 and 59 — a play is never absent because of where it is priced).

⚠️ **PrizePicks is NOT banned as a place to BET.** Sam bets there. **It is banned as a source of a NUMBER.** A PrizePicks play is still cardable on `model / raw / blend / matched class` with the multiplier ASKED FOR (ledger rule 46).

✅ **Hard Rock is the default book: it is where Sam bets, it multiplies exactly, and its feed prices are now confirmed against his app end to end.**

## 🔴 🆕 HARD ROCK'S APP SAYS "TO RECORD N+ STRIKEOUTS". THE FEED SAYS "OVER N−0.5". SAME BET.

`[measured 2026-08-21 — Sam's Sean Burke screenshot against the raw pull, ALL NINE RUNGS MATCHED TO THE DOLLAR]`

| App label | Feed outcome | Price |
|---|---|---|
| To Record 3+ | Over 2.5 | −4000 |
| **To Record 4+** | **Over 3.5** | **−1000** |
| To Record 5+ | Over 4.5 | −400 |
| To Record 6+ | Over 5.5 | −185 |
| To Record 7+ | Over 6.5 | +115 |
| To Record 8+ | Over 7.5 | +220 |
| To Record 9+ | Over 8.5 | +425 |
| To Record 10+ | Over 9.5 | +800 |
| To Record 11+ | Over 10.5 | +2000 |

🔴 **THIS IS THE PROJECT'S FIRST END-TO-END CONFIRMATION THAT A HARD ROCK FEED PRICE EQUALS THE APP PRICE** — and it is the direct evidence behind the rule above: **Hard Rock's numbers in the feed are real; PrizePicks' never were prices at all.**

⚠️ **THE OFF-BY-ONE IS A LIVE HAZARD.** Reading "4+" as "over 4.5" turns **−1000 into −400** and moves the break-even **10.9 points.** ➡️ **QUOTE BOTH FORMS BACK TO SAM** — *"o3.5 (the app's **4+ strikeouts**) at −1000"* — so a mismatch shows on the page instead of after the bet.

⏱️ 🆕 **STAMP EVERY PRICE WITH THE MINUTE IT WAS PULLED.** `[measured 8/21]` Misiorowski o6.5 read **−550** at ~3:00pm and **−850** in Sam's app at 3:32pm; the next day's pull read **−850**. **The feed was right when it was read and the market moved 300 points underneath it.** ⛔ **A card built at 3pm may not assert an 8pm price.**

## ⚠️ 🆕 WHAT RULE 48 DID TO THE ALT-OUTS PULL — SAY IT, DO NOT PAPER OVER IT

~~**The four-market pull stays mandatory.**~~ `[2026-09-21 Monday sweep]` **The pull of the markets `collect.py`'s `PITCHER_MARKETS` requests stays mandatory — three, with `pitcher_outs_alternate` NOT requested (ledger rule 61; STEP 5 above says the same).** But two facts now collide:
1. ✅ **Hard Rock posts NO alternate outs market at all** — Sam-confirmed at the book, not a feed artifact.
2. 🔴 **`us_dfs` is no longer pulled** (rule 48), and PrizePicks was the only source of alt-outs rungs on the 8/21 board.

➡️ **So `pitcher_outs_alternate` under ~~`regions=us,us2`~~ ~~`regions=us2`~~ 🔴 `regions=us,us2` (RESTORED 2026-08-24, ledger rule 48) may come back EMPTY, and that is a FINDING to report, not a gap to fill.** ⚠️ ~~**MORE SO AFTER Aug 22, not less — `us2` alone means the only book that could carry an alt-outs rung is the one Sam confirmed has none.**~~ 🔴 **STRUCK 2026-08-24 — THE ESCALATION NO LONGER HOLDS: four more books (DraftKings, FanDuel, Caesars, BetMGM) are back in the response under the five-book widening.** ✅ **THE CORE FINDING SURVIVES INTACT AND IS NOT WEAKENED: HARD ROCK POSTS NO ALTERNATE OUTS MARKET AT ALL — Sam-confirmed AT THE BOOK, not a feed artifact — and `us_dfs` STAYS BANNED.** ✅ **AN EMPTY RESULT IS A FINDING AND IS REPORTED, with the MARKET KEY, the REGIONS REQUESTED and the ROW COUNT** — *"`pitcher_outs_alternate` returned 0 rows across `us,us2` on N games."* ⚠️ 🆕 **AND THE COLLECTOR DOES NOT CURRENTLY REQUEST THE MARKET AT ALL (ledger rule 61) — so today its absence is a REQUEST decision, not a feed finding, and must be reported as one.** ⏳ ⛔ **Whether the five-book pull should RE-REQUEST it is SAM'S INTERACTIVE CALL, not a sweep's.** ⛔ **Never substitute a DFS rung for a missing sportsbook one.** ⚠️ `[measured 8/21]` **The card's only alt-outs play — Yamamoto o17.5 outs — was a PrizePicks rung with no sportsbook equivalent anywhere in the pull. Hard Rock's line for him is 18.5, two-way, and that is the whole outs market there.**

## Sam's price rules

| Rule | |
|---|---|
| **−700 floor** | The shortest alt rung he will take. Williams o4.5 at −1000 is out; o5.5 at −450 is in. 🔴 **HARD ROCK ONLY — a PrizePicks rung carries no price, so the floor cannot be applied there. Do not pretend it has been** |
| **Avoid lines too high to be worth even odds** | A rung near even that the model has at 50% is not a bet |
| **At a FLAT PAYOUT, take the lowest rung that clears** | 🔴 **RULE STANDS, JUSTIFICATION REPLACED Aug 21.** ~~PrizePicks charges the same at every rung~~ — struck, that was an encoding. **The real reason: the 2-pick MULTIPLIER barely moves with rung difficulty — Sam's real slips paid 1.8x, 1.9x, 2.0x — so climbing is still a pure donation** |
| ⛔ **Every rung must appear in a raw pull** | Three phantom rungs have shipped. Sam caught all three. 🔴 **Aug 21 nuance: this bans inventing a PRICE. It does not ban NAMING a rung the feed omits and asking Sam to price it — say which you are doing** |

---

# 🔴 STEP 6 — THE PAYOUT BAND. **FLOOR ONLY SINCE 2026-09-22: 2 LEGS ≥ 1.80x, 3+ LEGS ≥ 3.00x, NO CEILING. OWNED BY `claude/pick-ledger.md` RULE 28.** THIS IS THE HARD PART.

🔴🔴 **READ THIS FIRST — SAM, 2026-09-22:** *"we can make it 1.8- unlimited, but we still have to make sure the bets we provide have a high % to hit based on data from our model"*, then *"i want the minimum for 2 mans to be 1.8 for anything over 2man parlays i want the minimum to be 3x"*. ➡️ **There is no ceiling any more, so every "ceiling", "above band", "2.2x" and "3x–6x" figure below is HISTORY, not an instruction.** ✅ **What still binds: the floors (below them a ticket is never shown), one book per pair, different games by game identity (rule 54), and ranking by JOINT MODEL PROBABILITY** — that ranking is how "a high % to hit" is kept now that the ceiling is gone. ⚠️ **Walking a leg to a safer rung is still the right move whenever the ticket still clears its floor afterwards: it raises the hit %, which is what Sam asked to protect.**

🔴 **~~"1.8x to 2.1x"~~ STRUCK FROM THIS HEADING 2026-09-14, Monday sweep.** **The 2026-09-12 sweep struck the 2.1x out of this section's TABLE CELLS and left it in the HEADING — which is the line a card builder reads first, and the one a skimmer takes as the rule.** ⚠️ **That is the enumerated-instances failure again: fixing the places you listed is not sweeping the section.**

🔴 🆕 **WIDENED 2026-08-26 BY SAM — AND THIS SECTION DESCRIBES TWO-LEG TICKETS ONLY. FOUND IN THE CODE BY THE 2026-08-31 SWEEP, FIVE DAYS AFTER IT SHIPPED, WITH NO PROJECT DOC CARRYING IT.** `[measured 2026-08-31 from `card.py`'s `PARLAY_BANDS` and the `parlay_rule` string on the published cards]` **Sam, 2026-08-26: two-mans in 1.8x–2.2x, three- and four-mans in 3x–6x.** ➡️ **2 LEGS → 1.80x–2.20x · 3 LEGS → 3.00x–6.00x · 4 LEGS → 3.00x–6.00x.** ⛔ **THE 1.80 HARD FLOOR IS UNCHANGED AND IS STILL NEVER CROSSED.** 🔴 **`claude/pick-ledger.md` RULE 28 OWNS THE CURRENT BANDS — read them there, never off this page.** ✅ 🔴 **THE CODE NO LONGER CONTRADICTS ITSELF — CLOSED 2026-09-11, ledger rule 185.** ~~*AND THE CODE CONTRADICTS ITSELF, REPORTED BY EVERY GRADING RUN SINCE 8/26 AND STILL NOT FIXED: `parlay_rule` says 1.8x–2.2x while the `in_band` FLAG is computed against 2.1x, so a pair at 2.15x is ABOVE BAND to the flag and INSIDE BAND to the prose. AN INTERACTIVE SESSION MUST PICK ONE CEILING.*~~ ➡️ **The `in_band` flag is now COMPUTED FROM THE BAND IT PRINTS**, so the prose and the flag cannot disagree by construction. ⚠️ **The contradiction was real and stood on the page for sixteen days** — 2026-08-26 to 2026-09-11 — which is why the strike is kept rather than the sentence deleted. ⛔ **The bands themselves are STILL OWNED BY `claude/pick-ledger.md` RULE 28 and are still never read off this page.**

> Sam, Aug 20: *"dont give me any pairs that arent 1.8x or more… the normal bets we want to make are goint to be in the 1.8 to 2.1x range… we should be droppig bradish to 4.5 then to see if we can still get a 1.8x at least, that boosts our odds of hitting. this should always be done."*

🔴 🆕 **THE BAND IS ASYMMETRIC — AMENDED 2026-08-22 IN SAM'S OWN WORDS. THE ASYMMETRY IS THE POINT, NOT AN INCONSISTENCY.**

| | |
|---|---|
| 🔴 **Below 1.8x** | ⛔ **A HARD FLOOR. Not a bet. NEVER SHOWN — not printed, not labelled "below band", not listed as declined.** ✅ **CONFIRMED BY SAM 2026-08-22, in his own words, when asked directly whether a "below band" label would do: *"i dont want to see them at all"*.** ⛔ **This is an EXPLICIT, DELIBERATE EXCEPTION TO LEDGER RULE 53** — which otherwise says a failing play is SHOWN with its failing number rather than removed. 🔴 **Sam set it himself, AFTER rule 53 existed. ⛔ DO NOT "FIX" IT BACK.** ⚠️ **Rule 53 is about plays CLAUDE dislikes; this is about pairs SAM does not want to see** |
| ~~**1.8x – 2.1x**~~ 🔴 **1.8x – 2.2x ON A TWO-LEG TICKET** | ✅ **The normal card.** ⚠️ **The 2.1 in the struck cell is the pre-2026-08-26 ceiling** — Sam widened two-mans to 2.2x that day and added 3x–6x bands for three- and four-leg tickets. ⛔ **READ THE LIVE BANDS FROM `claude/pick-ledger.md` RULE 28, never off this row.** |
| ✅ ~~**Above 2.1x**~~ 🔴 **Above the ticket's own ceiling** | ⚠️ **A SOFT TARGET, NOT A CAP.** **The legs are riskier than they need to be, so WALK THE RUNGS first and try to land it in the band.** ✅ **But if it is a good bet, IT IS SHOWN — labelled with its multiplier and marked ABOVE BAND.** **Sam, 2026-08-22: *"if its a good bet its a good bet still show it, i mostly dont want anything belo 1.8"*.** ➡️ **Say why no walk was possible; ⛔ do NOT suppress it** |

⚠️ 🔴 **CONSEQUENCE FOR GRADING, RECORDED SO IT IS NOT DISCOVERED LATE.** **Sam's 8/21 slip 2 was 2.20x — ABOVE BAND AND LEGITIMATELY PLAYED.** **Above-band plays are graded normally and stay IN THE RECORD.** ➡️ **When the band's own hit rate is eventually measured, REPORT INSIDE-BAND AND ABOVE-BAND SEPARATELY AND SAY WHICH IS WHICH — otherwise "does** ~~**1.8–2.1**~~ **the band** **work" measures nothing.** `[2026-09-21 Monday sweep]` **(the 8/21 slip at 2.20x was above the 2.1x ceiling in force THAT day; under rule 28's 2026-08-26 bands it would sit inside)** ⛔ **Excluding an above-band play from the RECORD is forbidden. It is excluded only from the INSIDE-BAND SUBTOTAL.**

🔴 **Aug 21 — an UNDER CAN be walked UP the Hard Rock ladder to fit the band after all.** ~~"walked down"~~ **corrected: UP is the safer direction on an under (u5.5 → u6.5), and the safer number is the shorter price, which is what pulls a pair back inside** ~~**1.8x–2.1x**~~ **the ticket's band (`claude/pick-ledger.md` rule 28 — corrected by the 2026-09-21 sweep).** The overs-only reading had removed that whole move; it is back. **The rung exists; the feed just does not price it. Name it and ask Sam for the number.**

## 🔴 WHICH WAY IS "DOWN THE LADDER" — GET THIS RIGHT

**An OVER gets safer as the number goes DOWN. An UNDER gets safer as the number goes UP.**

| Play | To raise hit probability | Pays |
|---|---|---|
| o5.5 K | **→ o4.5** | less |
| **u5.5 K** | **→ u6.5** | **less** |

⛔ **"Drop Bradish to 4.5" on an UNDER moves the wrong way.** u4.5 needs *four or fewer* where u5.5 needs *five or fewer* — **harder, and it pays more.** On an under, the safety direction is **up**. **Say this out loud when it comes up; the instruction as phrased is a trap on half the board.**

## 🔴 BAND ARITHMETIC — run this BEFORE building, it kills pairs on sight

~~Two legs, product ≤ 2.10, so the two decimals average **≤ 1.449 (≈ −222 each)**.~~ 🔴 **RE-SOLVED AT THE LIVE CEILING 2026-09-14: two legs, product ≤ 2.20 on a two-leg ticket, so the two decimals average ≤ 1.483.**

⚠️ 🔴 **THE 2026-09-12 SWEEP LEFT THIS ARITHMETIC ALONE ON THE GROUND THAT IT IS "arithmetic about a decimal, not a statement of the live ceiling." THAT REASONING WAS WRONG AND IS RECORDED AS WRONG.** **The block does not merely describe a decimal — it ends in an instruction to CHECK EACH LEG AGAINST 2.10 BEFORE PAIRING IT, so at Sam's live 2.20 ceiling it REJECTS LEGAL PAIRS.** ➡️ **An instruction that computes with a retired constant is a retired instruction, however arithmetical it looks.**

- With the **−700 floor** (decimal **1.143**) as the short leg, the partner can be as long as `2.20 / 1.143 =` **1.925 (≈ −108)**. That is the widest legal spread. *(~~`2.10 / 1.143 =` **1.837 (≈ −119)**~~ — the same arithmetic at the retired 2.10 ceiling, struck 2026-09-14.)*
- 🔴 **ANY SINGLE LEG AT DECIMAL ≥ 2.20 (+120 OR LONGER) CANNOT SIT INSIDE A TWO-LEG BAND AT ALL.** No second leg is short enough. *(~~+110 or longer, decimal ≥ 2.10~~ — struck 2026-09-14; at the live ceiling a +115 leg at 2.15 now FITS, and the old rule would have thrown it away.)* ⚠️ **The historical example is unchanged and still instructive: Bradish u5.5 at +110 was 2.10x by itself under the ceiling in force that night, which is why every Bradish pair came out at 2.42x–2.94x.** **Check each leg's decimal against the CEILING FOR THAT TICKET SIZE — `claude/pick-ledger.md` rule 28 — before you try to pair it.**
  - ➡️ 🔴 **THE REMEDY, ADDED Aug 21 — WALK THE UNDER *UP* THE LADDER.** ~~"No fix exists on Hard Rock, because the alt under rung is unavailable there."~~ **STRUCK — that conclusion was wrong.** **Hard Rock's alternate unders exist and are bettable (Sam-confirmed); only their PRICES are missing from the feed.** **u5.5 → u6.5 is an easier number, so it prices shorter, the leg's decimal falls under** ~~**2.10**~~ **the ticket's ceiling (2.20 on two legs, ledger rule 28 — corrected 2026-09-21), and the pair drops into the band.** ⛔ **Name the rung, say the feed does not carry its price, and ASK SAM for the app number — never invent it.** ⚠️ **On OUTS there is still no walk available on Hard Rock: no alt outs market exists at the book at all.**
- A pair of two near-even legs (both ~1.9) lands at **3.6x** — far outside. **The band REQUIRES at least one short favourite.**

⚠️ **The band is a HIT-RATE preference, not an EV preference, and Sam knows it.** Short legs are usually priced above fair value, so the anchor leg is often a small −EV drag carried by the live leg. **State the trade once per card. Do not lecture.**

## AND AT LEAST FIVE PAIRS

> *"you should give me at least 5 pairs of bets out of the 10 props you give me."*

Every pair must:

1. 🔴 **CLEAR THE 1.8x HARD FLOOR.** **State the multiplier and the two decimals it came from.** ✅ **Landing inside THE TICKET SIZE'S OWN BAND is the TARGET and is what the rung-walking is for** — 🔴 **`claude/pick-ledger.md` RULE 28 OWNS IT: two legs 1.80x–2.20x, three and four legs 3.00x–6.00x.** *(~~1.8x–2.1x~~ struck 2026-09-14 — the pre-2026-08-26 two-leg band, still live in the item a card builder writes the pairs from.)* — ⚠️ **and the ceiling is SOFT (amended 2026-08-22): an above-band pair that is a good bet is SHOWN, labelled with its multiplier and marked ABOVE BAND.** ⛔ **A pair BELOW 1.8x is never shown at all — not as a labelled row, not as a declined one.**
2. **Sit on ONE book.** ⚠️ Only **Hard Rock** multiplies. On PrizePicks quote probabilities and **ASK for the in-app number.** 🔴 **And on a Hard Rock alt UNDER, ask for the price too — the feed does not carry it.**
3. **Use two different games.**
    🔴🔴 **CHECK GAME IDENTITY, NEVER OPPONENT NAME (ledger rule 54).** `[measured 2026-08-22 — a live card shipped FOUR IMPOSSIBLE PAIRS, including the #1 recommendation]`
    **Jared Jones' opponent read `Los Angeles Dodgers`; Tarik Skubal's read `Pittsburgh Pirates`. Two opponent strings that differ were read as two games that differ. They are the two halves of ONE game.**
    ⛔ **In EVERY game on EVERY slate the two starters have DIFFERENT opponents and the SAME game, so a name-comparison check could never have worked on any card.**
    ➡️ **Compare the event id, or the ordered `(away_team, home_team)` pair. Print the game on every pair row so a collision is visible on the page.**
    ⛔ **Hard Rock CORRELATION-REPRICES same-game parlays — the quoted multiplier does not exist — and the joint probability is invalid regardless of price, because opposing starters are not independent.**
    ⚠️ **Rule 32 is NOT the fix and is not the gap: it resolves a starter's TEAM, which was correct here. This defect is DOWNSTREAM, in the PAIRING step.**
4. Show **joint probability · break-even · edge · EV in dollars at $30.** 🔴 **HARD ROCK PAIRS ONLY.** ⛔ **A PrizePicks pair gets joint probability and nothing else — no break-even, no edge, no EV — until Sam reports the in-app multiplier (ledger rule 46).** ✅ 🆕 **AMENDED 8/21 late, mirroring ledger rule 46 exactly: PER-LEG break-even/edge/EV on a PrizePicks play is banned ALWAYS; SLIP-LEVEL EV becomes legal the moment Sam supplies the multiplier** — `EV = stake × (joint × multiplier − 1)`, break-even `1 / multiplier` — **because that multiplier is a real quoted payout.** ⛔ **Never a multiplier derived from the feed.**
5. ~~🔴 **Be checked against Sam's OPEN slips.** A pair that reuses a leg he already has live is concentration, not diversification. **Name the overlap.**~~ 🔴 **RETIRED Aug 21 at Sam's request** — *"this isnt nesssecary, if you like a leg that much to put it into multiple pairs thats fine you dont need to explain yourself, i understand."* **Reusing a strong leg across pairs is deliberate and he already reads it that way. Price legs on their merits and stop narrating the overlap.** ⚠️ *(The 8/20 observation — both top pairs shared the G. Rodriguez leg and it lost — stands as history in `claude/pick-ledger.md`. It is a fact about that night, not a live rule.)*
6. 🔴 **Carry BOTH leg probabilities as `model` AND `raw` AND `blend`, not just the blend** — the same three numbers STEP 7 requires, written into the ledger as their own columns. **The joint probability is quoted off the blends; the model and raw halves still have to be logged, per leg, or ledger rule 15 stays unfittable.** See the logging rule under STEP 7.

🔴 **If the band cannot be filled with plays you believe in, say so and hand over fewer.** *"a forced card is worse than an empty one."* On a 3-game remainder with 6 arms, **only 3 of 20 in-band pairs were +EV.** That is the honest answer, and it is the answer.

---

# STEP 7 — OUTPUT FORMAT

```
#N  PITCHER — MARKET                        [GOOD / BAD / MIXED]  ·  Game  ·  First pitch
    Standard:  <line>  <book>  <price>
    → model <m>%  ·  raw <r>% (<hits>/<starts> at this exact number)  ·  blend <b>%
    → matched class: <p>% (<hits>/<n>, K/9 ±1.5, 4+IP) vs <OPP> this season
       best:  <pitcher> <date> <line>  ·  <pitcher> <date> <line>
       worst: <pitcher> <date> <line>
    Alt ladder: <rung> <price> ★  ·  <rung> <price>  ·  <rung> <price>
    ★ = the rung I'd take, and why
    Four mandatory inputs: own form · opponent · home/road · raw hit rate at that number
    Matched class (STEP 4B): all-starts % AND 4+IP % · n · agree / ≥15-pt gap · post-hoc caveat
    Matchup: opponent, first pitch, moneyline, conditions
```

## 🔴 A PRIZEPICKS PLAY'S ODDS LINE IS THE RUNG AND THE BOOK. NOTHING ELSE.

⛔ **On a PrizePicks play the template's `Standard: <line> <book> <price>` line carries NO price and NO payout**, and the play carries **no PER-LEG break-even, no PER-LEG edge and no PER-LEG EV** — those require a per-leg price and PrizePicks does not publish one (**ledger rule 46**). ✅ 🆕 **THE SLIP IS DIFFERENT: once Sam reports the in-app multiplier, SLIP-level EV and break-even ARE quotable, because that multiplier is a real payout** (amended 8/21 late; ledger rule 46 / pre-publish check 31). **Write `Standard: o3.5 PrizePicks — multiplier TBC, ask Sam`, quote `model / raw / blend / matched class`, and stop.** ✅ **Hard Rock plays keep the full line: real price, real payout, real edge.**

## ⏱️ 🆕 EVERY PRICE CARRIES THE MINUTE IT WAS PULLED — ledger rule 49

**Add a `pulled` column to the card table.** `[measured]` **Misiorowski's o6.5 read −550 at ~3:00pm and −850 in Sam's app at 3:32pm.** **The feed was right when it was read and the market moved 300 points underneath it.** ⛔ **A card built at 3pm may not assert an 8pm price.**

⚠️ **The same thing shows inside the 8/21 ledger: Schlittler o4.5 is −525 on TABLE A (pulled ~3:00–3:20pm) and −550 on TABLE A2 (pulled 4:05pm).** **Without the stamps that reads as a transcription error. With them it reads as what it is.**

✅ **And quote a Hard Rock alt rung in BOTH forms** — the feed's `o3.5` and the app's `4+ strikeouts` — so an off-by-one is visible on the page instead of after the bet.

## 🔴 LOG `model` AND `raw` AS THEIR OWN COLUMNS IN THE LEDGER, NOT JUST THE BLEND

`[measured 8/21 by the 7:30am run]` **All three numbers are mandatory and separately logged. The blend alone is unfittable.**

- **Ledger rule 15 exists to replace the hand-set 50/50 with a MEASURED weight** — and it **has never once been executable from the ledger as written**, because **every card since the start has logged only the blend.** No card has ever logged a model probability or a raw hit rate.
- 🔴 **The raw rate must state its denominator** — `raw 50% (4/8 at this exact number)`. **A rate without a denominator cannot be weighted.** An 0/1 and a 4/8 are not the same evidence and a bare "50%" hides which one it is.
- ⚠️ **The 8/21 reconstruction is not a precedent.** To run rule 15's scoreboard even once, model and raw had to be rebuilt from scratch for all 12 plays of 8/20 — trailing-8 from the statsapi game log, opponent meanK from the opponent table, home/road from the schedule. **Nine of eleven reconstructions landed within ±0.2 of the published blend, so the method works** — but **a reconstruction is not a log**, it only worked because that whole slate was rebuildable from free endpoints, and **it will not always be possible.** **Do not rely on it.**
- 🔴 **The MATCHED-CLASS rate is logged too, as its own column** — `class % (hits/n)`, both the all-starts and the 4+IP figure, plus the 2–3 notable lines behind it. ⚠️ **It is logged, never blended.** STEP 4B is a flag; the blend stays **model + raw only.** Logging it is what makes the tie-breaker claim testable instead of a single anecdote.
- ➡️ ⚠️ 🔴 **CORRECTED 8/21 evening — THIS IS A BLUEPRINT REQUIREMENT THAT LEDGER RULE 41 DOES NOT CARRY.** **Ledger rule 41 names only `model` and `raw` beside the blend, and pre-publish check 26 names only those three columns.** **The 8/21 card that closed the rule-41 DOC DEBT item has NO class column.** ➡️ **So the debt is only PARTLY closed: the model/raw/blend half shipped, the class column did not.** ⛔ **Do not cite ledger rule 41 as the authority for the class column — it is this doc's requirement until the ledger adopts it.**

Then the pairs, **ranked by joint probability**, each with its multiplier, break-even, edge and dollar EV.

---

## Where this came from

Sam, Aug 20 2026, after a card shipped with two phantom goblin rungs and fabricated Hard Rock prices; amended the same evening after every pair on the follow-up card missed the payout band.

> *"a good format i would like you to follow is, looking at the board, focusing on good matchups for good pitchers against teams that striekout alot… after you figure out which props are the absolute best to target, you look at the odds on the bets, you find good bets that correlate with the stats you found."*

---

## Changelog

- 🆕 **2026-09-22 — Sam made the band floor-only** (2 legs ≥1.8x, 3+ legs ≥3x, no ceiling). STEP 6's heading now says so, and a read-first note marks every ceiling figure below as history. The ranking by joint model probability, the floors, one-book pairs and game-identity checks are unchanged. The figures below were left in place as the record. Football uses three books (rule 48); this MLB page's five-book set is unchanged.
- 🆕 **2026-09-21, Monday sweep (text-only, headless)** — three live 1.8x–2.1x / 2.10 band references re-pointed at ledger rule 28 (2 legs 1.80–2.20); the "four-market pull" corrected to `collect.py`'s three `PITCHER_MARKETS`; the weather row's "no historical source / T13b BLOCKED" corrected (source exists since 2026-08-25; T13b OPEN and UNSPECIFIED, still untested — not null); the STEP 3 sources row no longer calls the Odds API a source of PrizePicks PRICES; STEP 4B flags that `card.py` applies the T24 durability axis to OUTS (applied in code, not adopted). No step number, band arithmetic value, model figure or dated example changed.
- 🆕 **Sept 7 2026, Monday sweep (STEP 2's input table was still handing a card builder v4.0's coefficients six days after v5.0 published, and an owed test this page called open had closed)** — 🔴 **STEP 2's `IN THE MODEL — use these` WEIGHT COLUMN IS STRUCK. All five entries were v4.0 values** — the trailing-K slope, the opponent slope, both ± home/road terms, all three tiered outs `k`s and the pitch-count slope — **and `claude/mlb-projection-model.md` has shipped v5.0 since 2026-09-01, in which 13 of 16 constants moved.** ⛔ **This is this project's own banned pattern reproduced in the table a card builder reads FIRST: a coefficient copied outside the doc that owns it.** ✅ **The INPUTS and their SOURCES are kept; every weight now points at the model doc, with three traps named inline — the opponent slope must be centred on the constant `claude/mlb-opponent-database.md` states, home/road is TWO-SIDED, and the outs `k` is TIERED (the pooled slope is a reference figure and is not shipped).** ⚠️ **Stated honestly rather than alarmingly: the re-fit moved every constant by thousandths and the worst pricing gap on a realistic board is 0.053 K and 0.133 outs. The card is running last month's constants and it barely matters — but "small" is not "right".**
- 🆕 **Sept 12 2026 (STEP 6's open instruction had been carried out and the page still asked for it)** — 🔴 **STEP 6's *"AN INTERACTIVE SESSION MUST PICK ONE CEILING"* IS STRUCK. IT WAS PICKED ON 2026-09-11** (ledger rule 185): the `in_band` flag is now computed from the band it prints, so the prose and the flag cannot disagree by construction. ⚠️ **The contradiction was real and stood for SIXTEEN DAYS** — 2026-08-26 to 2026-09-11 — **so the sentence is struck rather than deleted**, and the closure is stated beside it. 🔴 **AND THE ASYMMETRY TABLE'S OWN 2.1x CEILING IS STRUCK IN BOTH ROWS** — it is the pre-2026-08-26 number, five days older than the widening note printed directly above it, and a reader who skipped the note would have taken it as live. ⛔ **Neither row now states a live ceiling: both point at `claude/pick-ledger.md` rule 28**, which is what the rest of this page already does for the bands and for the region set, and for the same reason — a number restated in two places goes stale in one of them. ✅ **THE HARD 1.8x FLOOR IS UNTOUCHED IN EVERY PLACE IT APPEARS**, and so is the floor/ceiling ASYMMETRY, which is the part of STEP 6 that carries Sam's own words. ⛔ **WHAT WAS NOT CHANGED, ITEMISED: no model coefficient, no blend, no band ARITHMETIC (the "+110 is 2.10x by itself" worked example is deliberately left alone — it is arithmetic about a decimal, not a statement of the live ceiling), no ladder-direction rule, no Sam price rule, no odds-source rule, no region set, no credit figure, no step numbering, no worked-example figure, no matched-class figure and no output template.** ⚠️ **Method:** `project_read` → the tool result recovered VERBATIM from the session transcript JSONL rather than retyped → programmatic patch with every anchor ASSERTED to occur exactly once → `collections.Counter` line-loss check → upload with `local_path`, per ledger rule 43. ⚠️ **The first attempt at the verbatim recovery FAILED — the transcript had not flushed the read yet — and the doc was NOT rewritten from context while that was true.**
- ✅ **STEP 2's BLEND NOTE CORRECTED: *"There is no fitted outs distribution … it should be tested at the monthly re-fit"* is STRUCK.** **It WAS tested at that re-fit. T3 ran once on 2026-09-01, exactly as pre-registered, and PASSED all three criteria** (mean +0.0543 · SD 1.0772 · q10 −1.3528 · q90 +1.3356). ⚠️ **Tails ~8% fatter than Normal — inside the bar, worth naming on a far alt rung.**
- ⛔ **WHAT WAS NOT CHANGED, ITEMISED: no band rule, no band arithmetic, no ladder-direction rule, no Sam price rule, no odds-source rule, no region set, no credit figure, no step numbering, no worked-example figure, no matched-class figure and no output template.** **STEP 5's region/book pointer at ledger rule 48 was re-checked against rule 48 this run and is CORRECT (five books, `regions=us,us2`, `us_dfs` banned); the `3 markets × 2 regions = 6 credits per game` figure was re-checked against `collect.py`'s `PITCHER_MARKETS` and is CORRECT.** ⛔ **STEP 6's 2026-08-26 widening note (two-mans 1.8x–2.2x, three- and four-mans 3x–6x, pointing at ledger rule 28) was left EXACTLY as written — it is correct and the sweep prompt's own 1.8x–2.1x tripwire is the stale side of that disagreement.**
- ⚠️ **Method:** `project_read` → verbatim local copy (no retype) → programmatic patch with every anchor ASSERTED to occur exactly once → `collections.Counter` line-loss check → `project_info` `created_at` compared immediately before upload → upload with `local_path`, per ledger rule 43.
- **Aug 24 2026, Monday sweep (the 8/23 five-book widening reached the CODE and the LEDGER but never reached this doc — STEP 5 carried a LIVE `regions=us2` instruction for a day)** — 🔴🔴 **SAM WIDENED THE ODDS SOURCE ON 2026-08-23, IN HIS OWN WORDS, RECORDED IN `github.com/smh0602/gizmos-picks` `CLAUDE.md` AND COMMIT `91b0290`:** *"lets just only use the top 5 sportsbooks in the USA, hardrock, draftkings, fanduel, ceasars, and bet MGM"* ➡️ **THE STANDING SET IS FIVE BOOKS — Hard Rock (`hardrockbet` / `hardrockbet_oh`), DraftKings, FanDuel, Caesars (`williamhill_us`), BetMGM — AND THE PROPS PULL IS `regions=us,us2` AGAIN, because four of the five live in `us`.** ⛔ **`us_dfs` STAYS BANNED; PrizePicks is still never a source of a NUMBER (rule 46).** ⚠️ 🔴 **THE FAILURE BEING FIXED, STATED PLAINLY: the widening reached `collect.py` and `claude/pick-ledger.md` rule 48 on 8/23, and the v4.8 Monday sweep of 2026-08-24 applied it to `claude/betting-project-instructions.md` and `claude/pick-ledger.md` — BUT THIS DOC WAS MISSED, so STEP 5 stood for a full day telling a card builder to pull `regions=us2` and Hard Rock only. That is ledger rule 61's failure mode INVERTED: the rule was live in the code and STALE in the doc.** 🆕 **FIVE THINGS SWEPT IN STEP 5, EVERY ONE BY STRIKETHROUGH WITH ITS REPLACEMENT STATED BESIDE IT — nothing was silently deleted:** **(1) THE ODDS-SOURCE HEADING** — the `us2`-only half struck and restated as five books on `regions=us,us2`, with the note that the previously-struck `us,us2` IS CORRECT AGAIN so a future reader is not confused by a strike that reversed; **(2) THE REGION CODE BLOCK** — `us` and `us2` now BOTH marked PULLED, with DraftKings, FanDuel, `williamhill_us` (Caesars) and BetMGM named on the `us` row, and the `us_dfs` line kept word-for-word as NEVER for a number; **(3) THE CREDIT FIGURE** — the "halves the bill" claim and the one-region figure struck, the BILLING FORMULA `cost = unique markets × regions, per game` KEPT because it is still correct and still measured, and the per-game cost restated as `markets × 2`, with `[measured 2026-08-24 from `collect.py`]` that `PITCHER_MARKETS` is THREE markets — `pitcher_strikeouts`, `pitcher_outs`, `pitcher_strikeouts_alternate` — so a pitcher pull is **6 credits per game**, and that the collector does NOT request `pitcher_outs_alternate` at all (rule 61); **(4) THE "WHAT IS GIVEN UP" PARAGRAPH** — struck, because it describes the 8/22 narrowing: DraftKings, FanDuel, Caesars and BetMGM are back in the pull, so nothing is given up and the recorded residual risk no longer exists; **(5) THE ALT-OUTS CONSEQUENCE** — `regions=us,us2` restored as the live region set and the "MORE SO AFTER Aug 22" escalation struck, while the CORE FINDING SURVIVES UNCHANGED (Hard Rock posts NO alternate outs market at all, Sam-confirmed at the book; `us_dfs` banned; an empty result is a FINDING reported with market key / regions / row count; a DFS rung may NEVER be substituted), plus the new note that the collector does not request the market at all and that re-requesting it is Sam's interactive call. ⚠️ **ONE FURTHER SENTENCE IN THE SAME SECTION WAS STRUCK RATHER THAN LEFT LIVE AND WRONG:** *"The same logic now drops `us`: Hard Rock lives in `us2` ONLY, so `regions=us2` alone is correct and sufficient for every prop on every card"* — **it is the same reversed instruction in a second place, and leaving it would have defeated the sweep.** 🔴 ⛔ **AND THE REGION SET IS NOW READ FROM `claude/pick-ledger.md` RULE 48 AND NEVER RESTATED BARE HERE, because it has moved THREE TIMES IN THREE DAYS** — `us,us2` (8/21) → `us2` only (8/22) → five books on `us,us2` (8/23). ⏳ **LEFT OPEN FOR SAM, NOT GUESSED: whether ledger rule 19's "card only PrizePicks and Hard Rock" widens with the five-book set. Until he answers: card the two, pairs stay Hard Rock-only (the code enforces it), and a play priced only at DraftKings / FanDuel / Caesars / BetMGM is SHOWN with its book named.** ⛔ **WHAT WAS NOT CHANGED, ITEMISED: NO MODEL COEFFICIENT, NO BLEND, NO BAND RULE, NO BAND ARITHMETIC, NO LADDER-DIRECTION RULE, NO SAM PRICE RULE, NO STEP NUMBERING, NO WORKED-EXAMPLE FIGURE, NO OUTPUT TEMPLATE AND NO GRADED FIGURE.** ⛔ **No graded row, money row or dated card table was touched; STEP 6 item 4 / STEP 7's SLIP-LEVEL EV carve-out, STEP 4B's "three of the TEN PLAYS IT WAS RUN ON", STEP 4C's "Four of the TEN ARMS CHECKED" and the 1.8x-hard-floor / 2.1x-soft-ceiling asymmetry were ALL LEFT EXACTLY AS WRITTEN — they are correct and a previous auditor got them wrong.** ⚠️ **Merged, not rewritten, per ledger rule 43: `project_read` → verbatim local copy → programmatic patch in python with SIX uniqueness-asserted anchors (`content.count(anchor) == 1` verified for every one BEFORE any replacement) → `collections.Counter` line-loss check, SEVEN lines dropped and every one of them an INTENDED replacement → fresh `project_read` and `created_at` comparison immediately before upload → upload with `local_path`.** ⛔ **One doc touched by this edit — this one.**
- **Aug 22 2026, 12:55pm ET (the different-games check was never a different-games check — it compared opponent names)** — 🔴🔴 **STEP 6'S "USE TWO DIFFERENT GAMES" REQUIREMENT NOW SPECIFIES *HOW* TO CHECK IT: ON GAME IDENTITY — THE EVENT ID, OR THE ORDERED `(away_team, home_team)` PAIR — AND NEVER ON THE OPPONENT NAME.** ➡️ **And the GAME IS NOW PRINTED ON EVERY PAIR ROW, so a collision is visible on the page instead of being discovered after delivery.** 🔴 **THE CAUSE, AND IT REACHED SAM: the live 8/22 card shipped FOUR SAME-GAME PARLAYS, INCLUDING THE #1 RECOMMENDATION. Jared Jones (PIT) and Tarik Skubal (LAD) are the OPPOSING STARTERS in PIT@LAD.** **Jones' opponent read `Los Angeles Dodgers`, Skubal's read `Pittsburgh Pirates`, and two opponent strings that differ were read as two games that differ — they are the two halves of ONE game.** ⚠️ **CAUGHT BY SAM, NOT BY ANY CHECK IN THIS PROJECT: *"skubal is on the dodgers"*.** ⛔ **AND THE NAME COMPARISON COULD NEVER HAVE WORKED ON ANY CARD, EVER — in every game on every slate the two starters have DIFFERENT opponents and the SAME game, so the test as written was guaranteed to pass on precisely the pairs it existed to catch.** ⛔ **THE CONSEQUENCE IS TWO-FOLD: Hard Rock CORRELATION-REPRICES same-game parlays, so the quoted multiplier DOES NOT EXIST AT THE BOOK; and the joint probability is invalid REGARDLESS OF PRICE, because two opposing starters' lines are not independent events.** ⚠️ 🔴 **STEP 3's TEAM-ASSIGNMENT TRAP / ledger rule 32 IS NOT THE GAP AND IS NOT AMENDED: the team assignments were CORRECT, confirmed from `schedule?hydrate=probablePitcher` and independently by Sam. The defect was DOWNSTREAM, in the PAIRING step, which had no check at all — resolving a starter's TEAM is not the same as resolving his GAME.** ➡️ **Mirrored in `claude/pick-ledger.md` as LEDGER RULE 54, added the same day, with the four voided pairs named on the card rather than quietly dropped.** ⛔ **NOTHING ELSE IN THIS DOC CHANGED — no model coefficient, no blend, no band rule, no band ARITHMETIC, no ladder-direction rule, no Sam price rule, no odds-source rule, no step numbering, no worked-example figure and no output template; the insertion sits inside STEP 6's "AT LEAST FIVE PAIRS" item 3 and items 4–6 are untouched.** ⚠️ **Merged, not rewritten: `project_read` → verbatim local copy → programmatic patch with a uniqueness-asserted anchor (verified to occur EXACTLY ONCE before any write) → `collections.Counter` line-loss check, ZERO lines lost → upload with `local_path`, per ledger rule 43.** ⛔ **Two docs touched by this correction — this one and `claude/pick-ledger.md`.**
- **Aug 22 2026 (the band has a hard floor and a soft ceiling — Sam decided both halves)** — 🔴 🆕 **STEP 6'S BAND IS NOW EXPLICITLY ASYMMETRIC, IN SAM'S OWN WORDS, AND THE ASYMMETRY IS THE POINT.** 🔴 **1.8x IS A HARD FLOOR: a pair below it is NEVER SHOWN — not printed, not labelled "below band", not listed as declined.** Asked directly whether sub-band pairs should carry a "below band" label, Sam said: *"i dont want to see them at all"*. ⛔ **This is an EXPLICIT, DELIBERATE EXCEPTION TO LEDGER RULE 53 — which otherwise says a failing play is SHOWN with its failing number rather than removed — and Sam set it himself, in his own words, AFTER rule 53 already existed.** ⛔ **Both STEP 6 and the DIVISION OF LABOUR section now say so on the page, so a future session does not "fix" it back to rule 53's default.** ✅ **2.1x IS A SOFT TARGET, NOT A CAP: an above-band pair IS shown, labelled with its multiplier, whenever it is a good bet** — *"if its a good bet its a good bet still show it, i mostly dont want anything belo 1.8"*. ➡️ **Rung-walking to pull a pair inside the band is still tried first and is still preferred; what changed is that failing to manage it is no longer a reason to suppress the pair.** ⚠️ 🔴 **CONSEQUENCE RECORDED FOR GRADING: Sam's 8/21 slip 2 was 2.20x — ABOVE BAND AND LEGITIMATELY PLAYED. Above-band plays are graded normally and stay IN THE RECORD; when the band's own hit rate is finally measured, INSIDE-BAND and ABOVE-BAND must be reported SEPARATELY, or "does 1.8–2.1 work" measures nothing.** 🆕 **THE DIVISION OF LABOUR section's open question — *"If Sam ever wants the sub-band pairs printed too, that is his call to make and it is not assumed here"* — is STRUCK, because he has now made it, and the answer is recorded beside it.** 🆕 **STEP 6's "AT LEAST FIVE PAIRS" item 1 amended to match: clear the 1.8x HARD FLOOR; the band is the target; above-band is shown and labelled; below-band is never shown.** ➡️ **Mirrored in `claude/pick-ledger.md` ledger rules 28 and 30, amended the same day.** ⛔ **No model coefficient, no blend, no ladder-direction rule, no band ARITHMETIC, no price rule, no odds-source rule, no step numbering and no worked-example figure changed** — the "+110 is 2.10x by itself" arithmetic is untouched, and so is STEP 5's `us2` narrowing; only what the arithmetic IMPLIES about SHOWING the pair changed. ⚠️ **Merged, not rewritten: `project_read` → local file → programmatic patch with uniqueness-asserted anchors (4 anchors, every one verified to occur EXACTLY ONCE before any write) → `collections.Counter` line-loss check, every dropped line an intended replacement → upload with `local_path`, per ledger rule 43.** ⛔ **Only three docs were touched this session — this one, `claude/pick-ledger.md` and `claude/owed-tests.md`.**
  ⚠️ 🔴 **CONCURRENCY HAZARD, RECORDED BECAUSE IT NEARLY DESTROYED THIS WRITE: A SECOND AGENT WAS EDITING THIS PROJECT AT THE SAME TIME AND PUBLISHED THE `us2` NARROWING TO THIS DOC AND TO `claude/pick-ledger.md` WHILE THIS WORK WAS IN FLIGHT.** **It was caught by re-reading both docs at the source before uploading (ledger rule 37) and comparing `project_info`'s per-doc `created_at` against the version each edit was built on.** ➡️ **This write was REBASED onto the newer version — STEP 5's `us2` narrowing, its credit figure, its cross-book note and its changelog entry are ALL PRESENT and were not clobbered; the rebuilt base was verified BYTE-IDENTICAL to the published version before a single patch was applied.** ⛔ **`project_write` has NO conflict detection and NO diff: a stale local copy uploaded over a newer one deletes it silently — ledger rule 43's failure with a second AUTHOR instead of a second session.** ➡️ 🆕 **STANDING PROCEDURE: `project_read` the doc AGAIN immediately before uploading and check `project_info`'s `created_at` for that path. If it moved, REBASE — never upload.**
- **Aug 22 2026 (Hard Rock only — STEP 5's odds source narrowed to `us2`, and the card is now half price)** — 🔴 **SAM NARROWED THE ODDS SOURCE, IN HIS OWN WORDS:** *"i onlt want to see hardrock odds from now on for all props"* ➡️ **STEP 5's odds-source instruction is amended: ~~`regions=us,us2`~~ is struck and the standing pull is `regions=us2` — HARD ROCK ONLY, EVERY PROP, EVERY CARD.** **Hard Rock lives in `us2` only, so one region is correct and sufficient; `us_dfs` was already banned and stays banned; the region code block now marks `us` as NO LONGER PULLED.** 💰 **PER-GAME CREDIT FIGURE ADDED TO STEP 5 AT THE NEW NUMBER — 4 CREDITS PER GAME.** `[measured 2026-08-22]` **The Odds API bills `cost = unique markets × regions, per game`, confirmed by a probe returning `x-requests-last: 1` for one market on one region: 4 markets × 1 region = 4, against the old 4 × 2 = 8.** ⚠️ **This doc previously carried NO per-game credit figure at all — only "extra credits, budget for them" — so the figure is an ADDITION, not a correction of a wrong number, and nothing was invented to replace a stale one.** ✅ **THE CROSS-BOOK CHECK SURVIVES FOR FREE and STEP 5 now says so: a `us2` pull still returns `hardrockbet`, `espnbet` and `fliff` in the same response at no extra cost, with `hardrockbet_oh`, `ballybet` and `betparx` in the same region — so ledger rule 47 / check 32 still has a comparison set in every pull.** ⚠️ **WHAT IS GIVEN UP: price shopping against DraftKings, FanDuel, BetMGM, BetRivers, Bovada and BetOnline — never actionable, because Sam bets Hard Rock and PrizePicks only.** ⛔ **Residual risk recorded on the page: a Hard Rock price offside versus the wider market is no longer visible against the `us` books.** ✅ **The alt-outs consequence line was updated to `us2` in the same pass, because it reads MORE strongly at one region, not less.** ⚠️ **PrizePicks is unchanged: still a place Sam BETS, still never a source of a NUMBER (ledger rule 46).** ⛔ **No model coefficient, no blend, no band rule, no ladder-direction rule, no Sam price rule, no step numbering, no worked-example figure and no output template changed.** ⚠️ **Merged, not rewritten: `project_read` → local file → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check → upload with `local_path`, per ledger rule 43.**
- **Aug 22 2026 (the division of labour — a failing check is a label, not a gate)** — 🆕 🔴 **NEW SECTION ADDED ABOVE STEP 1 — THE DIVISION OF LABOUR, mirroring `claude/pick-ledger.md` LEDGER RULE 53, in Sam's own words:** *"i do agree, i dont want you to stop doing this tho, it should be up to me to decide whcih i feel comfortable with your job is to provide me the data"* ➡️ **Claude provides the data AND the read; Sam decides what he is comfortable betting; a play is never absent from the board because Claude did not like it.** 🔴 **STEP 4's raw-rate cross-check (rule 15) and STEP 4B's matched-class check each gained a line saying the same thing where the check actually lives: the failing number is PRINTED ON THE ROW and the play stays visible.** ✅ **This is not a licence to withhold judgment — flagging a bad price is still the job.** ⚠️ **TWO OF THE THREE PLACES THE INSTRUCTION NAMED DO NOT EXIST IN THIS DOC AND NOTHING WAS INVENTED TO FILL THEM: there is NO "carding floor" instruction anywhere in this blueprint** (the only floor here is Sam's **−700 PRICE floor**, which is his rule and is untouched), **and rule 15 has never been written as a KILL here** — STEP 2 and STEP 4 already said "flag", so the amendment strengthens flag language rather than replacing a removal instruction. ⛔ **STEP 6's "below 1.8x — do not show it" was deliberately NOT amended: that is SAM'S OWN instruction about pairs, not a Claude judgment call, and the new section says so explicitly.** ⛔ **No model coefficient, no blend, no band rule, no ladder-direction rule, no price rule, no step numbering and no worked-example figure changed.** ⚠️ **Merged, not rewritten: `project_read` → local file → programmatic patch with uniqueness-asserted anchors → `collections.Counter` line-loss check (zero lines lost) → upload with `local_path`, per ledger rule 43.**
- **Aug 21 2026 (evening — the audit)** — 🆕 **STEP 4C ADDED — the head-to-head tiebreaker (ledger rule 50), in Sam's words**, and **ledger rule 51's rematch haircut added beneath it**, with the failed-pre-registration / exploratory epistemics stated on the page. 🔴 **STEP 5 gained the sportsbooks-only rule (ledger rule 48 — pull `regions=us,us2`, never `us_dfs`), the Hard Rock "To Record N+" label map (rule 49, verified 9/9 against Sam's screenshot), and a price pull-time requirement.** 🆕 **A section was added saying plainly what rule 48 did to the alt-outs pull: Hard Rock has no alt-outs market and PrizePicks is no longer a source, so `pitcher_outs_alternate` may return nothing — a finding, not a gap to fill.** 🔴 **A DANGLING REFERENCE WAS CORRECTED: STEP 7 claimed the matched-class column was tracked as ledger rule 41, and rule 41 names only `model` and `raw`.** **The debt is only partly closed and the doc now says so.** ✅ **Two matched-class figures were re-measured and were stale here** — Sale u18.5 vs MIL is **19/21 (90.5%)** not 18/20, and Schlittler o4.5 vs TOR is **18/29 (62.1%)** not 21/31, i.e. worse than this doc claimed. ⚠️ **A note was added reconciling the STEP 4B worked example with the card that actually shipped: Luzardo was checked but never carded (no props in the feed), and Yamamoto was carded WITH the flag rather than cut.** 🔴 **The changelog's claim that "PrizePicks flat −137/+100" was "still true" is struck — the flat-price half is false.** ⛔ **No model coefficient, no band rule, no ladder-direction rule and no step numbering changed.**

- **Aug 21 2026 (evening — the −137 was never a price)** — 🔴 **STRUCK THE FLAT-`−137` CLAIM EVERYWHERE IN THIS DOC.** `[measured 2026-08-21]` **PrizePicks returned exactly two distinct values across 145 outcomes in 7 games × 4 markets — `−137` (×77) and `+100` (×68) — while hardrockbet returned 80 distinct prices, espnbet 73, betparx 28, underdog 27, fliff 23, ballybet 18, pick6 1.** **`−137` is the Odds API's ENCODING for a goblin rung and `+100` for a demon. It is a label, not a quote.** Sam caught it from the app: *"sean burkes 3.5 is not priced at −137… you can't keep giving me false info."* ⛔ **Every break-even, edge and EV ever computed on a PrizePicks play is arithmetic on a constant and is meaningless** — on the 8/21 card that voids **+27.6, +19.1, +18.2, +18.1 and +12.4**, five of ~~seven~~ **EIGHT** carded plays *(denominator corrected 8/21 late)*. **Changed in STEP 5:** the WHAT EACH BOOK POSTS pricing row now reads *no per-leg price exists*; a full correction block was inserted above **Sam's price rules** carrying both new standing rules. **Changed in Sam's price rules:** the **−700 floor** is marked **Hard Rock-only** (a PrizePicks rung has no price to filter), and **"At a FLAT price, take the lowest rung that clears" is RETAINED with its justification REPLACED** — not *"PrizePicks charges the same at every rung"* but *"the 2-pick multiplier barely moves with rung difficulty"*, measured from Sam's own slips at **1.8x, 1.9x and 2.0x.** **Changed in STEP 6:** pairs item 4 (**joint · break-even · edge · EV**) is now **Hard Rock only.** **Changed in STEP 7:** a PrizePicks play's odds line carries the rung and the book and nothing else. ✅ **UNTOUCHED AND STILL TRUE: every model coefficient, the blend, the 1.8x–2.1x band, the ladder-direction rule, STEP 4B's matched-class check, the two-group split, the banned-arguments table, the Hard Rock feed-vs-book language, and every Hard Rock price, de-vig and pair multiplier — Hard Rock's prices are real.** ⚠️ **FIFTH instance of a fact about a query written down as a fact about the world, and the worst: it was the project's stated premise.** ⚠️ **Left OPEN, deliberately: whether Burke's 3.5 rung exists in the app at all. Sam's message proves the price is fake and proves nothing about the rung.**
- **Aug 21 2026 (matched-class check)** — 🔴 **ADDED STEP 4B — THE MATCHED-CLASS CHECK, mandatory on every carded play**, inserted between STEP 4's raw-hit-rate cross-check and STEP 5's odds pull. **Existing step numbers were NOT changed** — the new step is 4B so every reference to STEPS 1–7 elsewhere in this doc set still resolves. Sam asked for it in his own words on 8/21: *"i want you to show me notable game logs from other pitchers vs the same teams your favorite pitchers are playing today… backing up your reasoning"*, then *"don't just be doing this for sale in the future i want you to do this for every pitcher in your top 10."* **The check computes a THIRD independent number beside model and raw: how often starters within ±1.5 K/9 of the carded arm have cleared that exact threshold against that exact lineup this season**, quoted both all-starts and excluding sub-4-inning outings (`outs ≥ 12`), always with `n`, and **uninformative below n=8.** **The ±1.5 band is fixed in advance precisely so it cannot be tuned to the answer** — a first pass at `K/9 ≥ 9.0` manufactured a false contradiction on Misiorowski (13.60 K/9 read as 43% against arms four K/9 below him), and the matched band honestly returns **n=1** for him. ⛔ **It is a FLAG, NOT AN INPUT — never folded into the blend**, which stays model + raw; a **>15-point disagreement makes the play a suspect and must be stated on the card**, and the **post-hoc/subgroup risk is stated every time.** **STEP 7's per-play template now carries the class line plus 2–3 notable individual logs (best, and at least one poor one)** — Sam asked for the logs, not only the percentage — and the class rate is **logged as its own ledger column** alongside model and raw. **First full run (8/21) added as the worked example:** it **confirmed four plays, near-matched a fifth, contradicted three, and confirmed Sale u18.5 outs at 90% — a play Sam had objected to.** 🔴 **The Yamamoto case is why the step exists:** model 54.0% vs raw 86.4%, a 32-point gap; rule 15 called the model the suspect so the play was carded off the raw rate, and **the matched class came in at 38%, on the model's side — the raw rate was the liar.** ⚠️ **One instance; every future case is to be logged before this is treated as a rule.** **Nothing else changed** — model, coefficients, 1.8x–2.1x band, ladder-direction rule, two-group split, banned-arguments table, Hard Rock feed-vs-book language and the model/raw/blend logging requirement are all untouched.
- **Aug 21 2026 (model/raw logging)** — 🔴 **FIXED the STEP 7 template, which had been quietly logging ONLY THE BLEND.** The line read `Standard: <line> <book> <price> → model / raw / blend`, which *reads* as though all three are recorded but in practice only the blend ever survived into the ledger. **Split into two lines with all three numbers explicit, mandatory and separately logged**, and the raw rate now **must carry its denominator** (`raw 50% (4/8 at this exact number)`) — a rate without one cannot be weighted. **Added a prominent logging rule under STEP 7** and a **matching item 6 to the AT LEAST FIVE PAIRS list**, so the requirement appears where a card is actually written up. **Discovered when ledger rule 15's scoreboard was attempted for the first time on 8/21:** rule 15 requires both numbers so the hand-set 50/50 blend weight can be fitted, and it turned out **no card had ever logged either one.** The 8/20 slate had to be reconstructed from scratch (trailing-8, opponent meanK, home/road) to run the scoreboard once; 9 of 11 reconstructions landed within ±0.2 of the published blend, **but a reconstruction is not a log and will not always be possible.** Tracked as **ledger rule 41** / owed DOC DEBT.
- **Aug 21 2026 (consistency sweep)** — 🔴 **RETIRED the pair/slip-overlap check in STEP 6** (*"Be checked against Sam's OPEN slips… name the overlap"*) — Sam retired it the same day: *"this isnt nesssecary, if you like a leg that much to put it into multiple pairs thats fine you dont need to explain yourself, i understand."* The 8/20 shared-leg observation stays in the ledger **as history, not as a rule.** 🔴 **Corrected the band-remedy DIRECTION:** STEP 6 and the changelog said an under could be *"walked down"* the ladder, which contradicts this doc's own ladder-direction table — **an under is walked UP (u5.5 → u6.5)** to get safer and shorter. **Wrote the remedy into the band-arithmetic bullet itself**, beside the *+110 is 2.10x alone* line, so the arithmetic and its fix sit together; noted that **no such walk exists on Hard Rock OUTS**, because no alt outs market exists there.
- **Aug 21 2026** — 🔴 **STRUCK the false claim that Hard Rock's alternate strikeout ladders are overs-only AT THE BOOK.** Sam bets Hard Rock and confirms **you can bet the under on an alt line there.** What was measured is real — the Odds API returned `pitcher_strikeouts_alternate` with only `Over` outcomes — but **"the feed has no under side" was written down as "the book has no under side."** Struck in STEP 5: *"THE ONLY UNDER YOU CAN BET ON HARD ROCK IS THE STANDARD LINE'S UNDER SIDE… say the rung does not exist — do not name one"*, and the parenthetical calling *"Hard Rock alt ladders are two-way"* the opposite error. **Replaced with the standing procedure: name the rung, say the feed does not price it, ASK SAM for the app price** — the PrizePicks in-app-multiplier procedure, applied to Hard Rock. Consequence written into STEP 6: **an under CAN be walked into the band after all.** **Generalised the feed-is-not-the-app rule beyond PrizePicks: an absence in an API response is evidence about the API, never about the sportsbook** (third instance in this project). **UNCHANGED and still true: Hard Rock posts NO alternate outs market at all** (Sam-confirmed at the book); 9–11 real multiplying strikeout rungs. 🔴 ~~PrizePicks flat −137/+100 with non-multiplying multipliers~~ **STRUCK 8/21 evening — the "flat −137/+100" half is FALSE: those two values are the feed's ENCODING for goblin and demon, not prices.** ✅ **The non-multiplying half survives: PrizePicks multipliers do not come from leg prices and must be asked of Sam.** **Phantom-rung rule kept and reconciled: never assert a PRICE you have not seen.**
- **Aug 20 2026** — Written, then amended the same evening with the payout band.
