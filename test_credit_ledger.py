#!/usr/bin/env python3
"""THE CREDIT LEDGER: every paid snapshot counted, none overwritten, the room
read off the API's own balance, the newest balance taken by the chain.

`[2026-09-29]` Four defects, one ledger:
  1. watchdog's paid pattern matched `gamelines|props-*` only, so alt-lines
     spend (#168) was invisible to the reconciliation. ✅ ONE registry,
     `collect.PAID_KINDS`; every paid writer goes through `paid_path`, and
     watchdog, `daily_spend()` and `alt_month_spend()` all read it.
  2. Lost alt-line snapshots. The job logs show the mechanism: props-player
     buys the alt lines on its deadline, converge had ALSO planned
     `alt-lines`, ran it seconds later, found nothing left to buy and wrote
     the same HHMM file over the paid one -- 36 credits / 18 games at 13:19Z
     on 09-26 (collect #1866), 94 / 47 at 19:14Z (#1886), 2 / PHI@CHI at
     16:00Z on 09-28 (#1954), bought again at 19:03Z. ✅ A paid mode runs at
     most once per pass, and a paid snapshot is never overwritten.
  3. `daily_allowance()` summed our snapshots, 2,918 credits light of the
     API's balance by 09-26. ✅ The month's spend is MONTHLY_PLAN minus the
     newest `credits_remaining` read THIS month; the 1st starts clean.
  4. health.json took props-pitcher/1113 (3,848) over props-batter/1113
     (3,808) by file name. ✅ The newest reading by the chain.
Every case is planted in a throwaway tree; nothing reads production data.

# @vacuity 🔴 alt-lines is a registered paid kind
#   file: collect.py
#   find:               "alt-lines")     # alt-lines: paid per game since #168
#   with:               )
#
# @vacuity 🔴 every write that records credits goes through the registry
#   file: collect.py
#   find:     write(f"{paid_path('alt-lines')}/{filename()}.gz", {
#   with:     write(f"{daydir('alt-lines')}/{filename()}.gz", {
#
# @vacuity 🔴 daily_spend reads only the registered paid kinds
#   file: collect.py
#   find:     for kind in PAID_KINDS:
#   with:     for kind in os.listdir(root):
#
# @vacuity alt_month_spend reads the registry
#   file: collect.py
#   find:         for p in glob.glob(f"{LEAGUES[lg]['data']}/{month}-*/{paid_kind('alt-lines')}/*.json.gz"):
#   with:         for p in glob.glob(f"{LEAGUES[lg]['data']}/{month}-*/alt-lines/*.json.gz"):
#
# @vacuity 🔴 watchdog reads collect's registry, so alt-lines spend is reconciled
#   file: watchdog.py
#   find: PAID_KINDS = _paid_kinds() or ()
#   with: PAID_KINDS = ("gamelines", "props-pitcher", "props-batter")
#
# @vacuity 🔴🔴 a paid snapshot is never overwritten
#   file: collect.py
#   find:     path = _paid_free_name(path)
#   with:     pass
#
# @vacuity 🔴 ...and the reading written beside it is still read
#   file: credits.py
#   find:     return re.compile(r"(\d{4}-\d{2}-\d{2})/(%s)/(\d{4})((?:-\d+)?)\.json\.gz$"
#   with:     return re.compile(r"(\d{4}-\d{2}-\d{2})/(%s)/(\d{4})()\.json\.gz$"
#
# @vacuity 🔴🔴 a paid mode runs at most once per pass
#   file: collect.py
#   find:         if m in paid and m in _RAN_PAID:
#   with:         if False:
#
# @vacuity 🔴 the chained alt-lines run counts as this pass's
#   file: collect.py
#   find:     _RAN_PAID.add("alt-lines")
#   with:     pass
#
# @vacuity 🔴 the allowance's room comes off the API's balance
#   file: collect.py
#   find:     spent_month = billed if billed is not None else sum(month_spend().values())
#   with:     spent_month = sum(month_spend().values())
#
# @vacuity 🔴 on the 1st, last month's balance is not this month's
#   file: collect.py
#   find:     if not nb or str(nb[0])[:7] != t.strftime("%Y-%m"):
#   with:     if not nb:
#
# @vacuity 🔴 within a minute the LOWER balance is the newer one
#   file: credits.py
#   find:     return max(have, key=lambda r: (str(r[0])[:16], -r[1]))
#   with:     return max(have, key=lambda r: (str(r[0])[:16], r[1]))
#
# @vacuity 🔴 health.json's balance is picked by the chain
#   file: watchdog.py
#   find:     _nb = C.newest(readings)
#   with:     _nb = readings[0] if readings else None
"""
import ast
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
import credits as K  # noqa: E402
import watchdog as W  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

UTC = datetime.timezone.utc


def at(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def put(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with gzip.open(p, "wt") as fh:
        json.dump(doc, fh)
    return p


def reading(root, rel, pulled, left, used=0):
    return put(root, rel, {"pulled_at": pulled, "credits_remaining": left,
                           "credits_used": used})


class Sandbox:
    """A throwaway working tree for collect.py, pinned to `when`."""
    SAVE = ("now", "LEAGUE", "DATA", "odds_get", "alt_plan", "log", "run_mode")

    def __init__(self, when, league="mlb"):
        self.when, self.league, self.logs = at(when), league, []

    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="ledger-")
        self.cwd = os.getcwd()
        os.chdir(self.d)
        self.saved = {k: getattr(C, k) for k in self.SAVE}
        self.plan = C._fresh.plan
        C.now = lambda: self.when
        C.log = lambda *a, **k: self.logs.append(" ".join(str(x) for x in a))
        if self.league != "mlb":
            C.LEAGUE, C.DATA = self.league, "data/%s" % self.league
        C._RAN_PAID.clear()
        return self

    def __exit__(self, *a):
        for k, v in self.saved.items():
            setattr(C, k, v)
        C._fresh.plan = self.plan
        C._RAN_PAID.clear()
        os.chdir(self.cwd)
        shutil.rmtree(self.d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 ONE REGISTRY OF PAID KINDS, READ BY EVERY SPEND READER")
# ══════════════════════════════════════════════════════════════════════
ck("the registry names every paid writer's kind",
   set(C.PAID_KINDS) >= {"gamelines", "props-pitcher", "props-batter",
                         "props-player", "alt-lines"}, "PAID_KINDS=%s" % (C.PAID_KINDS,))
eq(W.PAID_KINDS, C.PAID_KINDS, "   watchdog reads the same list (parsed from collect.py)")
_writes = []
for _n in ast.walk(ast.parse(open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read())):
    if (isinstance(_n, ast.Call) and getattr(_n.func, "id", "") == "write"
            and len(_n.args) >= 2 and isinstance(_n.args[1], ast.Dict)
            and "credits_used" in {getattr(k, "value", None) for k in _n.args[1].keys}):
        _calls = {getattr(c.func, "id", "") for c in ast.walk(_n.args[0])
                  if isinstance(c, ast.Call)}
        _writes.append((_n.lineno, "paid_path" in _calls and "daydir" not in _calls))
ck("🔴 every write that records credits_used goes through paid_path (%d)" % len(_writes),
   len(_writes) >= 3 and all(ok for _l, ok in _writes),
   "rule 67 floor 3; not through the registry: %s" % [l for l, ok in _writes if not ok])
try:
    C.paid_kind("props-board")
    _refused = False
except ValueError:
    _refused = True
ck("   ...and an unregistered kind is refused, never silently billed", _refused)
_amd = next(n for n in ast.walk(ast.parse(open(os.path.join(ROOT, "collect.py"),
                                               encoding="utf-8").read()))
            if isinstance(n, ast.FunctionDef) and n.name == "alt_month_spend")
ck("   alt_month_spend reads the registry",
   any(getattr(c.func, "id", "") == "paid_kind" for c in ast.walk(_amd)
       if isinstance(c, ast.Call)))

_t = tempfile.mkdtemp(prefix="ledger-rec-")
try:
    reading(_t, "data/2026-09-26/gamelines/1000.json.gz", "2026-09-26T10:00:00Z", 5000, 6)
    reading(_t, "data/nfl/2026-09-26/alt-lines/1100.json.gz", "2026-09-26T11:00:00Z", 4960, 40)
    reading(_t, "data/2026-09-26/gamelines/1200.json.gz", "2026-09-26T12:00:00Z", 4954, 6)
    _steps = W._balance_steps(root=_t)
    ck("🔴 the reconciliation SEES alt-lines spend: 2 steps, 0 unrecorded",
       len(_steps) == 2 and sum(r[4] for r in _steps if r[4] > 0) == 0,
       "steps=%s" % [(r[0], r[4]) for r in _steps])
finally:
    shutil.rmtree(_t, ignore_errors=True)

with Sandbox("2026-09-26T20:00:00Z"):
    put(".", "data/nfl/2026-09-26/alt-lines/1100.json.gz", {"credits_used": 10})
    put(".", "data/nfl/2026-09-26/not-a-paid-kind/1100.json.gz", {"credits_used": 99})
    put(".", "data/nfl/2026-09-20/alt-lines/1600.json.gz", {"credits_used": 28})
    eq(C.daily_spend("2026-09-26"), 10,
       "🔴 daily_spend counts the registered paid kinds, nothing else")
    eq(C.alt_month_spend(), 38, "   alt_month_spend sums both leagues' alt-lines this month")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 A PAID SNAPSHOT IS NEVER OVERWRITTEN, A PAID MODE NEVER RUN TWICE")
# ══════════════════════════════════════════════════════════════════════
with Sandbox("2026-09-26T13:19:20Z"):
    _p = "data/ncaaf/2026-09-26/alt-lines/1319.json.gz"
    C.write(_p, {"credits_used": 36, "bought": ["g%d" % i for i in range(18)]}, compress=True)
    C.write(_p, {"credits_used": 0, "bought": []}, compress=True)
    _a = json.load(gzip.open(_p, "rt"))
    _b = json.load(gzip.open(_p.replace("1319.", "1319-1."), "rt"))
    ck("🔴🔴 a second write in the same minute lands BESIDE the paid one, never over it",
       _a["credits_used"] == 36 and len(_a["bought"]) == 18 and _b["credits_used"] == 0,
       "first=%s second=%s" % (_a.get("credits_used"), _b.get("credits_used")))
    ck("   ...and both are read as paid snapshots",
       len(K.readings("data", C.PAID_KINDS)) == 2 and C.daily_spend("2026-09-26") == 36,
       "readings=%d" % len(K.readings("data", C.PAID_KINDS)))
    C.write("data/latest/plain.json", {"v": 1})
    C.write("data/latest/plain.json", {"v": 2})
    ck("   ...while a non-paid file is still replaced in place",
       json.load(open("data/latest/plain.json"))["v"] == 2
       and not os.path.exists("data/latest/plain-1.json"))

# The 09-26 13:19Z sequence, replayed through the REAL collect_alt_lines:
# props-player's chained buy, then converge's own alt-lines in the same
# minute. Stubbed: the Odds API call, and the planner (the real rule it
# keeps: a game in an earlier snapshot's `bought` is held, never re-bought).
_GAMES = [{"id": "e%02d" % i, "commence": "2026-09-26T20:00:00Z",
           "home": "H%d" % i, "away": "A%d" % i} for i in range(18)]


def _planner(events, at_, times, window_h, bought):
    return ([e for e in events if e[0] not in bought],
            [(e[0], "already bought") for e in events if e[0] in bought])


def _replay(box):
    box.calls = []

    def _odds(path, params):
        box.calls.append(path)
        return {"bookmakers": [{"key": "draftkings", "markets": []}]}, 2, 6000 - 2 * len(box.calls)
    C.odds_get, C.alt_plan = _odds, _planner
    put(".", "data/nfl/2026-09-26/gamelines/1200.json.gz", {"games": _GAMES})


with Sandbox("2026-09-26T13:19:10Z", league="nfl") as box:
    _replay(box)
    C.collect_alt_lines()
    C.collect_alt_lines()
    _f = sorted(os.listdir("data/nfl/2026-09-26/alt-lines"))
    _d = [json.load(gzip.open(os.path.join("data/nfl/2026-09-26/alt-lines", f), "rt")) for f in _f]
    ck("🔴🔴 the 13:19Z replay keeps the paid record: 18 games bought ONCE, 36 credits on disk",
       len(box.calls) == 18 and _f == ["1319-1.json.gz", "1319.json.gz"]
       and _d[1]["credits_used"] == 36 and len(_d[1]["bought"]) == 18
       and _d[0]["bought"] == [],
       "calls=%d files=%s" % (len(box.calls), _f))
    ck("   ...and the chained run counts as this pass's alt-lines run",
       "alt-lines" in C._RAN_PAID, "ran=%s" % sorted(C._RAN_PAID))

with Sandbox("2026-09-26T13:19:10Z", league="nfl") as box:
    _replay(box)
    _rows = [{"mode": m, "paid": True, "stale": True, "missing": True, "age_min": None,
              "due_et": "8:30/15:00", "late_min": 49} for m in ("props-player", "alt-lines")]
    C._fresh.plan = lambda **kw: (["props-player", "alt-lines"], _rows)
    _ran = []

    def _run_mode(m):
        _ran.append(m)
        if m == "props-player":
            C.collect_alt_lines()        # the chain run_mode('props-player') makes
    C.run_mode = _run_mode
    C.converge()
    ck("🔴🔴 converge runs a paid mode at most once per pass: alt-lines not run again",
       _ran == ["props-player"] and len(box.calls) == 18
       and os.listdir("data/nfl/2026-09-26/alt-lines") == ["1319.json.gz"],
       "ran=%s calls=%d" % (_ran, len(box.calls)))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE ROOM COMES OFF THE API'S BALANCE, ON BOTH SIDES OF THE 1st")
# ══════════════════════════════════════════════════════════════════════
FLAT, HARD, PLAN = C.FLAT_DAILY_CAP, C.HARD_DAY_CEIL, C.MONTHLY_PLAN
with Sandbox("2026-09-26T20:00:00Z"):
    # the API says 16,000 spent; our snapshots only record 1,000 of it
    reading(".", "data/2026-09-26/gamelines/1900.json.gz", "2026-09-26T19:00:00Z",
            PLAN - 16000, 1000)
    eq(C.month_billed(), 16000, "the month's spend is MONTHLY_PLAN minus the newest balance")
    eq(C.daily_allowance(), max(FLAT, min(HARD, FLAT * 26 - 16000)),
       "🔴 the allowance's room uses the API's spend, not the 1,000 our snapshots hold")
with Sandbox("2026-09-30T23:50:00Z"):
    reading(".", "data/2026-09-30/gamelines/2300.json.gz", "2026-09-30T23:00:00Z", 1500, 50)
    eq(C.month_billed(), PLAN - 1500, "   09-30: September's own balance counts")
with Sandbox("2026-10-01T00:05:00Z"):
    reading(".", "data/2026-09-30/gamelines/2300.json.gz", "2026-09-30T23:00:00Z", 1500, 50)
    eq(C.month_billed(), None,
       "🔴 10-01 before the first pull: September's low balance is NOT October's")
    eq(C.daily_allowance(), max(FLAT, min(HARD, FLAT * 1)),
       "   ...so the 1st starts from the stored sum, which is 0")
with Sandbox("2026-10-01T12:00:00Z"):
    reading(".", "data/2026-09-30/gamelines/2300.json.gz", "2026-09-30T23:00:00Z", 1500, 50)
    reading(".", "data/2026-10-01/gamelines/0030.json.gz", "2026-10-01T00:30:00Z", 1490, 10)
    reading(".", "data/2026-10-01/gamelines/1100.json.gz", "2026-10-01T11:00:00Z", PLAN - 60, 6)
    eq(C.month_billed(), 60,
       "   10-01 after the API's reset: the newest reading (a later minute) wins, "
       "not the pre-reset low")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE NEWEST BALANCE BY THE CHAIN, NOT THE FILE NAME")
# ══════════════════════════════════════════════════════════════════════
_R = [("2026-09-28T11:13:05Z", 3848, "data/2026-09-28/props-pitcher/1113.json.gz"),
      ("2026-09-28T11:13:41Z", 3808, "data/2026-09-28/props-batter/1113.json.gz")]
eq(K.newest(_R)[1], 3808, "🔴 two paid pulls in one minute: the LOWER balance is the newer")
eq(K.newest(list(reversed(_R)))[1], 3808, "   ...whatever order they arrive in")
_t = tempfile.mkdtemp(prefix="ledger-wd-")
_saved = (W.ROOT, W.SRCDIR)
try:
    open(os.path.join(_t, "collect.py"), "w").write("RESERVE = 750\n")
    reading(_t, "data/2026-09-28/props-pitcher/1113.json.gz", "2026-09-28T11:13:05Z", 3848, 40)
    reading(_t, "data/2026-09-28/props-batter/1113.json.gz", "2026-09-28T11:13:05Z", 3808, 40)
    W.ROOT, W.SRCDIR = _t, _t
    _rep = W.Report()
    W.check_credit_balance(_rep, at("2026-09-28T12:00:00Z"))
    _cr = getattr(_rep, "note_credits", None) or {}
    ck("🔴 health.json's balance is 3,808 (props-batter), not props-pitcher's 3,848",
       _cr.get("balance") == 3808, "credits=%s" % (_cr,))
finally:
    W.ROOT, W.SRCDIR = _saved
    shutil.rmtree(_t, ignore_errors=True)
