#!/usr/bin/env python3
"""
🔴 A PLAYED MLB SLATE IS NEVER LEFT UNGRADED. `[Sam, 2026-10-02]`

2026-10-02 had no MLB games, so the contract dropped its `results` row and
converge never ran `results`. 10-01's stored results had been pulled at
10:14Z on 10-01, 14 hours before first pitch (1 game, 0 final), and
record.json skipped 10-01 as "not settled": 29 picks and 10 top-10 rows off
the Track Record. `collect_results` re-pulled only the two newest slates or
a MISSING file, so once 10-01 was two slates back the hole was permanent.

✅ The contract judges `results` on the slate it grades: on a no-games day
it is owed while the previous slate had games (fail closed) and is not
settled, probing THAT slate's file. `collect_results` re-pulls every stored
slate inside its 14-slate cap that is not settled; a settled one is left
alone. "Settled" is the grader's rule: every game Final, or Postponed /
Cancelled (they grade as voids, Sam's 2026-09-24 approval).

Driven on planted trees with a pinned clock, never on the live tree.

# @vacuity 🔴 a no-games day after a game day still owes results
#   file: freshness.py
#   find: if no_games_day(prev, data) or results_settled(prev, data):
#   with: if True:
#
# @vacuity 🔴 a no-games day after a settled slate owes none
#   file: freshness.py
#   find: return bool(games) and all(isinstance(g, dict) and (g.get("state") == "Final"
#   with: return False and all(isinstance(g, dict) and (g.get("state") == "Final"
#
# @vacuity 🔴 ...nor after another no-games day
#   file: freshness.py
#   find: if no_games_day(prev, data) or results_settled(prev, data):
#   with: if results_settled(prev, data):
#
# @vacuity ⛔ no reading for the slate before still counts as played
#   file: freshness.py
#   find: return bool(seen) and all(n == 0 for n in seen)
#   with: return all(n == 0 for n in seen)
#
# @vacuity ⛔ the contract's settled rule is the grader's
#   file: freshness.py
#   find: VOID_STATES = frozenset({"Postponed", "Cancelled"})
#   with: VOID_STATES = frozenset({"Postponed"})
#
# @vacuity 🔴 a stored not-final file two or more slates back is re-pulled
#   file: collect.py
#   find: if back <= 1 or not os.path.exists(p) or not _stored_settled(p):
#   with: if back <= 1 or not os.path.exists(p):
#
# @vacuity 🔴 ...and a settled one is not
#   file: collect.py
#   find: return bool(slate_settled(json.load(gzip.open(path, "rt")))[0])
#   with: return False
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

import collect as C  # noqa: E402
import freshness as F  # noqa: E402
from tcheck import ck, section  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 10, 3, 1, 0, tzinfo=UTC)    # slate 10-02, past its 06:00 ET deadline
PREV, DAY = "2026-10-01", "2026-10-02"


def gz(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt") as fh:
        json.dump(doc, fh)


def plant(t, sched=(), results=()):
    """sched: {day: totalGames}; results: {day: (pulled_at, [game states])}."""
    for day, n in dict(sched).items():
        gz(os.path.join(t, "data", day, "schedule", "1200.json.gz"),
           {"date": day, "schedule": {"totalGames": n}})
    for day, (at, states) in dict(results).items():
        gz(os.path.join(t, "data", day, "results", "final.json.gz"),
           {"pulled_at": at, "slate_date": day, "n_games": len(states),
            "n_final": states.count("Final"), "games": [{"state": s} for s in states]})


def owed(sched=(), results=()):
    """-> [(path, stale)] of the contract's `results` rows on a planted tree."""
    t = tempfile.mkdtemp(prefix="slate-graded-")
    try:
        plant(t, sched, results)
        base = t.replace("\\", "/")
        return [(r["path"][len(base) + 1:], r["stale"])
                for r in F.survey(base + "/data", base + "/picks", NOW) if r["mode"] == "results"]
    finally:
        shutil.rmtree(t, ignore_errors=True)


EARLY = ("2026-10-01T10:14:39Z", ["Scheduled"])      # what 10-01 really stored
PREV_FILE = "data/%s/results/final.json.gz" % PREV

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE CONTRACT JUDGES `results` ON THE SLATE IT GRADES")
# ══════════════════════════════════════════════════════════════════════
ck("⚠️ the pinned clock reads slate %s, past its 06:00 ET deadline" % DAY,
   F.slate_date(NOW) == DAY and F.last_due(F.GRADING, NOW) < NOW, F.slate_date(NOW))
_a = owed({PREV: 1, DAY: 0}, {PREV: EARLY})
_a2 = owed({PREV: 1, DAY: 0})
ck("🔴 a no-games day after a game day still owes results until that slate is settled",
   _a == [(PREV_FILE, True)] and _a2 == [(PREV_FILE, True)],
   "⛔ 10-02 dropped the row and 10-01 never graded. stored-early %s, missing %s" % (_a, _a2))
_b = owed({PREV: 1, DAY: 0}, {PREV: ("2026-10-02T03:00:00Z", ["Final", "Postponed"])})
ck("🔴 a no-games day after a settled slate owes none (a postponed game is settled-void)",
   _b == [], "rows %s" % _b)
_c = owed({PREV: 0, DAY: 0})
ck("🔴 ...nor after another no-games day", _c == [], "rows %s" % _c)
_d = owed({DAY: 0})
ck("⛔ no reading for the slate before still counts as played (fail closed)",
   _d == [(PREV_FILE, True)], "rows %s" % _d)

_cases = [["Final"], ["Final", "Postponed"], ["Cancelled"], ["Scheduled"],
          ["Final", "Suspended"], ["In Progress"], []]
_t = tempfile.mkdtemp(prefix="slate-rule-")
try:
    _diff = []
    for _i, _st in enumerate(_cases):
        _day = "2026-09-%02d" % (_i + 1)
        plant(_t, results={_day: ("2026-09-30T12:00:00Z", _st)})
        _g = C.slate_settled({"games": [{"state": s} for s in _st]})[0]
        if F.results_settled(_day, os.path.join(_t, "data")) != _g:
            _diff.append((_st, _g))
finally:
    shutil.rmtree(_t, ignore_errors=True)
ck("⛔ the contract's settled rule is the grader's: the same void states, the same verdicts",
   F.VOID_STATES == C.VOID_STATES and not _diff,
   "⛔ a contract that calls a slate settled the grader skips leaves it ungraded. %s %s"
   % (sorted(F.VOID_STATES), _diff))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 `collect_results` RE-PULLS A STORED SLATE THAT NEVER SETTLED")
# ══════════════════════════════════════════════════════════════════════
NOW2 = datetime.datetime(2026, 10, 3, 12, 0, tzinfo=UTC)  # slate 10-03; 10-01 is two back
_t, _cwd, _now = tempfile.mkdtemp(prefix="slate-repull-"), os.getcwd(), C.now
try:
    C.now = lambda: NOW2
    _res = {C.et_slate_date(b): ("2026-10-03T11:00:00Z", ["Final"]) for b in range(2, 15)}
    _res[PREV] = EARLY
    _res[C.et_slate_date(4)] = ("2026-10-03T11:00:00Z", ["Final", "Postponed"])
    plant(_t, results=_res)
    os.chdir(_t)
    _want = C.results_slates(14)
finally:
    os.chdir(_cwd)
    C.now = _now
    shutil.rmtree(_t, ignore_errors=True)
ck("🔴 a stored not-final file two or more slates back is re-pulled",
   PREV in _want, "⛔ only a MISSING file was fetched again. want %s" % _want)
ck("🔴 ...and a settled one is not (the two newest are always pulled)",
   _want == [PREV, DAY, "2026-10-03"], "want %s" % _want)
