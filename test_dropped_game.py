#!/usr/bin/env python3
"""AN IF-NECESSARY GAME THE LEAGUE DROPPED IS NOT A GAME. `[2026-10-23]`

collect 39551457667 (2026-10-21 05:57Z) went red on "card MISSED its 10:00
ET build: never built" and "results ... never built", and 39730188369
(10-22 06:02Z) on "results ... the previous slate, not settled yet", both
for 2026-10-20: a day with 0 MLB games. Its first 12 schedule readings
(00:02Z-03:01Z) listed ALCS Game 7, flagged `ifNecessary` "Y"; Game 6 had
ended the series, and from 03:16Z on all 74 readings listed nothing.
`freshness.no_games_day` counted ANY reading that ever listed a game, so
the day owed a card and results nobody could build, in the contract, the
watchdog and the relay alike (all three read that one copy).
✅ A game counts as DROPPED only when every reading that lists it flags it
if-necessary and DROPPED_AFTER readings pulled after the last one that
lists it leave it out. ⛔ Everything else still fails closed: a regular
game that vanished, a game the newest readings list again, a game left out
by one reading only, a reading with no pulled_at time, one whose count
names no games, and (new) one whose game list does not add up to its own
totalGames all keep the day owed.
Measured over every stored day (63, read 2026-10-23): totalGames always
equals the game list; the five games that ever vanished were all
if-necessary (wild card, ALDS, NLCS, ALCS), and 10-20 is the only day that
lost its last game. Planted trees, the clocks of the two red runs; the
real 10-20 is printed as a note, never asserted.

# `[2026-10-27]` the first find moved with R6's gameType filter; the mutation still drops only
# the dropped-game test and keeps the filter.
# @vacuity 🔴 a dropped if-necessary game leaves its day with no games
#   file: freshness.py
#   find:     return [sum(g["gamePk"] not in gone and carded(g) for g in games) for games in lists]
#   with:     return [sum(carded(g) for g in games) for games in lists]
#
# @vacuity ⛔ a regular game that vanished still counts (only if-necessary drops)
#   file: freshness.py
#   find:             flagged[pk] = flagged.get(pk, True) and g.get("ifNecessary") == "Y"
#   with:             flagged[pk] = True
#
# @vacuity ⛔ one reading leaving it out is not enough
#   file: freshness.py
#   find: DROPPED_AFTER = 2
#   with: DROPPED_AFTER = 1
#
# @vacuity ⛔ a game the newest readings list again is not dropped
#   file: freshness.py
#   find:             last[pk] = max(last.get(pk, t), t)
#   with:             last[pk] = min(last.get(pk, t), t)
#
# @vacuity ⛔ a reading with no pulled_at time drops nothing
#   file: freshness.py
#   find:     times = [_parse(ts) for ts, _ in reads]
#   with:     times = [_parse(ts) or _parse("2000-01-01T00:00:00Z") for ts, _ in reads]
#
# @vacuity ⛔ a count that names no games drops nothing
#   file: freshness.py
#   find:     lists = [_games(sc) for _, sc in reads]
#   with:     lists = [_games(sc) or [] for _, sc in reads]
#
# @vacuity ⛔ a game list that does not add up to totalGames fails closed
#   file: freshness.py
#   find:                 return False          # a game list that does not add up: fail closed
#   with:                 continue
"""
import datetime
import gzip
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import freshness as F  # noqa: E402
import relay as R  # noqa: E402
import watchdog as W  # noqa: E402
from tcheck import ck, note, section  # noqa: E402

UTC = datetime.timezone.utc
RUN1 = datetime.datetime(2026, 10, 21, 5, 57, tzinfo=UTC)   # collect 39551457667
RUN2 = datetime.datetime(2026, 10, 22, 6, 2, tzinfo=UTC)    # collect 39730188369
DAY, BEFORE, AFTER, LATER = "2026-10-20", "2026-10-19", "2026-10-21", "2026-10-22"
G7 = 849814                                                 # ALCS Game 7


def game(pk, necessary):
    return {"gamePk": pk, "gameType": "L",
            "ifNecessary": "Y" if necessary else "N",
            "status": {"detailedState": "Scheduled"}}


def brief(rows):
    """A row list as (stale, the path's last three parts), for a failure's detail."""
    return rows and [(r["stale"], "/".join(r["path"].split("/")[-3:])) for r in rows]


def reading(day, hhmm, games=(), total=None, stamped=True, listed=True):
    """One stored schedule reading: statsapi's body as collect_schedule keeps it."""
    sc = {"totalGames": len(games) if total is None else total}
    if listed:
        sc["dates"] = [{"date": day, "games": list(games)}] if games else []
    doc = {"date": day, "schedule": sc}
    if stamped:
        doc["pulled_at"] = "%sT%s:%s:00Z" % (day, hhmm[:2], hhmm[2:])
    return day, hhmm, doc


# The real shape of 10-20: listed if-necessary, then left out from 03:16Z.
DROPPED = [reading(DAY, "0002", [game(G7, True)]), reading(DAY, "0301", [game(G7, True)]),
           reading(DAY, "0316"), reading(DAY, "0401"), reading(DAY, "1200")]
# The days around it, as they were: 10-19 played and graded, 10-21 and 10-22 empty.
AROUND = [reading(BEFORE, "1200", [game(849815, False)]),
          reading(AFTER, "0003"), reading(AFTER, "1200"),
          reading(LATER, "0010"), reading(LATER, "1200")]


class Tree:
    """A temp root holding only the planted readings (and 10-19's settled
    results); `watchdog.ROOT` is swapped in and RESTORED."""

    def __init__(self, readings):
        self.d = tempfile.mkdtemp(prefix="dropped-game-")
        self.data = self.d.replace("\\", "/") + "/data"
        for day, hhmm, doc in list(readings) + AROUND:
            self._gz("data/%s/schedule/%s.json.gz" % (day, hhmm), doc)
        self._gz("data/%s/results/final.json.gz" % BEFORE,
                 {"pulled_at": BEFORE + "T10:20:00Z", "games": [{"state": "Final"}]})
        os.makedirs(os.path.join(self.d, "picks"), exist_ok=True)

    def _gz(self, rel, doc):
        p = os.path.join(self.d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with gzip.open(p, "wt") as fh:
            json.dump(doc, fh)

    def __enter__(self):
        self._old, W.ROOT = W.ROOT, self.d
        return self

    def __exit__(self, *a):
        W.ROOT = self._old
        shutil.rmtree(self.d, ignore_errors=True)

    def owed(self, now):
        """What each reader of the one rule says about `now`'s MLB card and results."""
        rows = {}
        for r in F.survey(self.data, self.d.replace("\\", "/") + "/picks", now):
            rows.setdefault(r["mode"], []).append(r)
        rep = W.Report()
        W.check_card_present(rep, now)
        return {"card": rows.get("card"), "results": rows.get("results"),
                "watchdog": "card:mlb" in {i["key"] for i in rep.items},
                "relay": R.card_owed(now, self.data)[0],
                "no_games": F.no_games_day(DAY, self.data)}


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 10-20: THE DROPPED ALCS GAME 7 OWES NOTHING")
# ══════════════════════════════════════════════════════════════════════
ck("⚠️ the clocks are the red runs': card day and slate %s at 05:57Z, the slate "
   "before %s at 06:02Z the next day" % (DAY, DAY),
   F.due_date(F.CARD, RUN1) == DAY and F.slate_date(RUN1) == DAY
   and F.slate_date(RUN2) == AFTER and F.et_date(F.next_due(F.CARD, RUN1)) == AFTER,
   "card %s, slate %s / %s" % (F.due_date(F.CARD, RUN1), F.slate_date(RUN1), F.slate_date(RUN2)))
with Tree(DROPPED) as t:
    got, got2 = t.owed(RUN1), t.owed(RUN2)
ck("🔴 the day the league dropped its only game has no games", got["no_games"] is True,
   "no_games_day(%s) = %s" % (DAY, got["no_games"]))
ck("🔴 the contract owes no card for it (39551457667's 'card MISSED')",
   got["card"] is None, "card rows: %s" % brief(got["card"]))
ck("🔴 ...and no results (39551457667's 'results MISSED')",
   got["results"] is None, "results rows: %s" % brief(got["results"]))
ck("🔴 ...nor the next morning, as the slate before an off-day (39730188369)",
   got2["results"] is None, "results rows: %s" % brief(got2["results"]))
ck("🔴 the watchdog reports no missing MLB card", not got["watchdog"], "fired: card:mlb")
ck("🔴 the relay owes no card for %s or %s: the chain ends" % (DAY, AFTER),
   got["relay"] is False, "relay owed: %s" % got["relay"])

# ══════════════════════════════════════════════════════════════════════
section("2. ⛔ A GAME DAY WITH NO CARD IS STILL LATE")
# ══════════════════════════════════════════════════════════════════════
# Each case is 10-20 with one thing changed. Every reader must still owe
# the card, and the contract the results, judged on 10-20's own slate.
G = game(G7, True)
CASES = [
    ("the if-necessary game is listed again by the newest reading (it is on)",
     DROPPED[:4] + [reading(DAY, "1200", [G])]),
    ("a REGULAR game vanished from the later readings",
     [reading(DAY, h, [game(G7, False)]) for h in ("0002", "0301")] + DROPPED[2:]),
    ("the if-necessary game was left out by ONE later reading only",
     DROPPED[:3]),
    ("the game became necessary (flagged N) before it vanished",
     [reading(DAY, "0002", [G]), reading(DAY, "0301", [game(G7, False)])] + DROPPED[2:]),
    ("the reading that listed it has no pulled_at time",
     [reading(DAY, "0002", [G], stamped=False)] + DROPPED[2:]),
    ("a later reading counts a game but names none",
     DROPPED[:2] + [reading(DAY, "0316", total=1, listed=False)] + DROPPED[3:]),
    ("a dropped if-necessary game beside a real one still listed",
     [reading(DAY, "0002", [G, game(849899, False)])]
     + [reading(DAY, h, [game(849899, False)]) for h in ("0316", "0401", "1200")]),
    ("(new) a reading says 0 games but lists one",
     [reading(DAY, "0002", [game(849899, False)], total=0)] + DROPPED[2:]),
]
for label, readings in CASES:
    with Tree(readings) as t:
        got = t.owed(RUN1)
    ck("⛔ %s: the card is owed and stale, the watchdog fires, the relay hands over" % label,
       bool(got["card"]) and all(r["stale"] for r in got["card"])
       and got["watchdog"] and got["relay"] is True,
       "card %s / watchdog %s / relay %s" % (brief(got["card"]), got["watchdog"], got["relay"]))
    ck("   ...and its results are owed, on %s's own slate" % DAY,
       bool(got["results"]) and all(r["stale"] and r["path"].endswith(DAY + "/results/final.json.gz")
                                    for r in got["results"]),
       "results rows: %s" % brief(got["results"]))
note("the real %s (read, not asserted): no_games_day=%s"
     % (DAY, F.no_games_day(DAY, os.path.join(ROOT, "data"))))
