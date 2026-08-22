# Gizmo's Picks — data collector

Pulls MLB odds and schedule data on a schedule and commits timestamped
snapshots to `data/`.

## Why this exists

Historical odds are a separate and expensive product. Line movement,
closing-line value, and the implied-team-total test (T25) all need odds
recorded *as they were at the time*. None of it can be reconstructed
later. Every slate that passes uncollected is gone permanently.

So the collector runs first, before any dashboard. The store is the
valuable part; the site is just a view of it.

## Setup

1. Add your Odds API key as a repository secret named `ODDS_API_KEY`
   (Settings → Secrets and variables → Actions → New repository secret).
2. Enable Actions if prompted.
3. That's it. The first scheduled run collects within the hour.

To test immediately: Actions → `collect` → Run workflow → `gamelines`.

## Budget

The Odds API bills `markets × regions`, but the two endpoints differ:

| Endpoint | Billing | Note |
|---|---|---|
| `/sports/{sport}/odds` | per **call** | 3 markets × 2 regions = 6 credits for the whole slate |
| `/sports/{sport}/events/{id}/odds` | per **game** | player props — this is where the money goes |

Daily spend at the current schedule:

| Pull | Frequency | Credits/day |
|---|---|---|
| Game lines (15 books) | every 30 min, ~14 hrs | ~168 |
| Pitcher props (15 books) | 2× daily | ~180 |
| Hitter props (Hard Rock only) | 1× daily | ~75 |
| **Total** | | **~423** |

≈12,700/month against a 20,000 allowance. `RESERVE` in `collect.py`
stops prop sweeps before they can zero the month out.

MLB statsapi is free and unmetered.

## Layout

```
data/2026-08-23/
  gamelines/1530.json      compact extract, one per pull
  props-pitcher/1410.json.gz   raw, gzipped
  props-batter/1420.json.gz    raw, gzipped
  schedule/1530.json           probables, records, linescores
```

Game lines are stored as a normalised extract — at 28 pulls a day the raw
payloads would run to gigabytes a year. Prop sweeps are stored raw
because they happen a few times a day and we cannot yet model most of
those markets, so we keep everything and decide later.

## Adding a market

Add the key to the relevant list at the top of `collect.py`. Cost scales
linearly, so check the budget table first.
