# HANDOFF — C8: pitcher props keep their own 25 seats on Gizmo's Picks

Read `CLAUDE.md` first. Dated; check every claim against `main`.

## What was wrong (measured, not assumed)

- Sam, 2026-09-25: the page showed 1 pitcher prop and 46 hitter props.
  The card, `picks/2026-09-25.json`, holds **1 pitcher and 49 hitters**.
- `card.py` gave each kind half the board (25) and let an unused half
  spill to the other. After C2 (#166) corrected the pitcher number
  against its price, only **1 of 57** priced pitcher props beat its
  break-even that morning, so hitters took 24 pitcher seats.

## What changed

| | |
|---|---|
| `card.select_board` | Each kind has its own 25 seats, never taken by the other. Hitters: up to 25 that beat the price (the rule as it was, capped). Pitchers: every row that beats the price first; empty seats go to the best remaining pitcher rows by the corrected number, marked `below_price`. Never both sides of one prop (keyed by **game ID**, player, market, line), in any pass. The thin-board top-up to 25 rows still runs, inside each kind's seats. Order is still strictly by confidence. |
| `board_rule` + `board_seats` | The rule text says the above and the real make-up ("25 pitcher (24 below their price) and 25 hitter"); `board_seats` carries the counts. |
| `index.html` `pickCard` | A below-price row says "Loses to its price", with the printed %, the break-even and the card's own edge. Plain sentence kept when a number is missing. Render oracle re-baselined for `pickCard` only. |
| `verify_card.py` 7c | ≤25 per kind; seat table is 25/25; never both sides; the below-price label true both ways; pitcher seats full when the card priced enough; `board_seats` and `board_rule` match the board. |
| `test_card_seats.py` | Today's real slate (anchored to the published card), synthetic slates, 300 random slates, and the page label driven in node. 8 declared mutations, all bite. |

## Before and after, on today's card

Replayed from the 14:12Z build's own inputs (data at `67ce2e4`, clock
fixed at 14:12Z). The old code reproduces the published board exactly.

| | pitcher | of which below price | hitter |
|---|---|---|---|
| before (published) | 1 | 0 | 49 |
| after | 25 | 24 | 25 |

Top 10, pairs and parlays: byte-identical before and after.

## What did NOT change

No model coefficient, no C2 correction, no `blend`, no pass bar, no
published pick (`picks/2026-09-25.json` stays 1/49). Top 10, pairs and
parlays. No cron line, no workflow, no Odds API spend.

## Mistakes, with root cause

- **Mine, caught before commit:** my first prop key was (player, market,
  line). Run against the real card, it flagged Carlos Narvaez's
  under 0.5 RBI twice. Those were game 1 and game 2 of the BAL @ NYY
  doubleheader, which are two separate wagers. Root cause: I keyed a
  wager without its game, the rule CLAUDE.md already states for parlay
  legs. The key now includes the game ID, and a declared mutation proves
  the test catches it.

## Open

- Tonight's data (evening, after first pitches) fails `verify_card` on
  one check, and `main`'s code fails it the same way: T37, Andrés
  Chaparro's RBI projection. `card_gate.py` accepts it as T37, which Sam
  accepted on 2026-09-04, so the run stays green and the card is not
  republished. Not caused by, or changed by, C8.

## Changelog

- **2026-09-25:** first version.
