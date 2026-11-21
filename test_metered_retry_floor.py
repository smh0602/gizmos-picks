#!/usr/bin/env python3
"""
A METERED MODE THAT KEEPS FAILING CANNOT DRAIN A QUOTA.

🔴 `[Sam, 2026-11-18]` The football relay (relay.py) converges both leagues every
15-35 minutes, around the clock. `fb-scores` retries its own failure on every
pass (it backs off only when CFBD refuses), and the college team-directory
rebuild runs before EVERY college mode: while one of them fails on our side, a
link would ask CFBD ~80 passes a day, 2 calls each, against ~70 calls a day of
headroom on the 3,000-call key (CFBD ran out 11-29 last month).
✅ A metered mode (freshness.STAND_DOWN: the CFBD / nflverse modes) or the team
directory that failed twice in a row is not planned again for
METERED_RETRY_MIN minutes after its last failure (freshness.retry_wait), state
in data/<lg>/latest/metered-attempts.json, cleared on a success. The first
retry is still the next pass.
⛔ The row stays stale and the gate red while it waits, exactly as before.

🔴 THE CLASS, DERIVED: every mode in STAND_DOWN, in every football league whose
contract has a row for it, and the team directory. Our own failure injected
(the mode raises), converge driven every 15 minutes for 4 hours on a pinned
clock, in planted trees, every other mode recorded and not run.

# @vacuity 🔴🔴 a metered mode that failed twice waits
#   file: freshness.py
#   find:     return max(0.0, METERED_RETRY_MIN - (now - last).total_seconds() / 60.0)
#   with:     return 0
#
# @vacuity 🔴 ...because plan() leaves it out while it waits
#   file: freshness.py
#   find:             need.discard(m)
#   with:             pass
#
# @vacuity 🔴 ...because converge records each failure
#   file: collect.py
#   find:                         _fresh.note_failure(DATA, m, now(), why)
#   with:                         pass
#
# @vacuity 🔴 the first retry is still the next pass (a one-off blip recovers at once)
#   file: freshness.py
#   find: METERED_FAILS_BEFORE_WAIT = 2
#   with: METERED_FAILS_BEFORE_WAIT = 1
#
# @vacuity 🔴 a success clears the record
#   file: freshness.py
#   find:     doc.pop(mode)
#   with:     doc.get(mode)
#
# @vacuity 🔴 the team directory's CFBD call waits behind its own failures
#   file: collect.py
#   find:     _wait = _fresh.retry_wait(DATA, _fresh.TEAM_DIRECTORY, now())
#   with:     _wait = 0
#
# @vacuity 🔴 ...which it records
#   file: collect.py
#   find:             _fresh.note_failure(DATA, _fresh.TEAM_DIRECTORY, now(), f"{type(e).__name__}: {e}")
#   with:             pass
#
# @vacuity 🔴 [2026-11-20, review] ...and a CFBD answer that leaves it still needing a rebuild is a failure too
#   file: collect.py
#   find:             _fresh.note_failure(DATA, _fresh.TEAM_DIRECTORY, now(), why2)
#   with:             pass
#
# @vacuity 🔴 [2026-11-20, review] a deadline passing mid-pass does not cut the wait short (the catch-up skips it)
#   file: collect.py
#   find:             | {m for m in _fresh.STAND_DOWN if _fresh.retry_wait(DATA, m, _at) > 0}
#   with:             | set()
"""
import contextlib
import datetime
import gzip
import importlib
import io
import json
import math
import os
import re
import shutil
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from tcheck import ck, eq, note, section  # noqa: E402

import freshness as F  # noqa: E402

UTC = datetime.timezone.utc
MIN = datetime.timedelta(minutes=1)
T0 = datetime.datetime(2026, 11, 19, 15, 7, tzinfo=UTC)          # ⚠️ a pinned in-season Thursday
PASSES = [T0 + 15 * k * MIN for k in range(17)]                   # every 15 minutes for 4 hours
SPAN = (PASSES[-1] - PASSES[0]).total_seconds() / 60.0
BOUND = 2 + math.ceil((SPAN - 15) / F.METERED_RETRY_MIN)
_TMP = tempfile.mkdtemp(prefix="retryfloor-")


@contextlib.contextmanager
def inside(d):
    cwd = os.getcwd()
    os.chdir(d)
    try:
        yield
    finally:
        os.chdir(cwd)


def _write(full, doc):
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if full.endswith(".gz"):
        with gzip.open(full, "wt", encoding="utf-8") as fh:
            json.dump(doc, fh)
    else:
        with open(full, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)


def contract_rows(lg, now):
    d = tempfile.mkdtemp(prefix="empty-", dir=_TMP)
    try:
        _write(os.path.join(d, "data", lg, "latest", "props.json.gz"), {})
        with inside(d):
            return F.contract("data/%s" % lg, "picks", now)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def tree(lg, now, missing):
    """Every row of `lg` built just after its deadline in force at `now`, except
    `missing`'s rows, never built (so the contract owes it on every pass)."""
    d = tempfile.mkdtemp(prefix="tree-", dir=_TMP)
    _write(os.path.join(d, "data", lg, "latest", "props.json.gz"), {})
    for m, (kind, path), times, paid, _w in contract_rows(lg, now):
        if m == missing:
            continue
        due = F.last_due(times, now)
        at = min(due + MIN, now) if due else now - MIN
        stamp = at.strftime("%Y-%m-%dT%H:%M:%SZ")
        doc = {"built_at": stamp, "written_at": stamp, "pulled_at": stamp}
        if re.search(r"/history/schedule-\d{4}\.json\.gz$", path):
            doc["games"] = [{"id": 1}]
        elif re.search(r"/history/lines-\d{4}\.json\.gz$", path):
            doc["games"] = {"1": {"spread": -3.5}}
        if kind == "dir":
            path = re.sub(r"\d{4}-\d{2}-\d{2}", at.strftime("%Y-%m-%d"), path, count=1)
            full = os.path.join(d, path, at.strftime("%H%M") + ".json.gz")
            if paid:
                doc.update(credits_used=12, credits_remaining=19000)
        else:
            full = os.path.join(d, path)
        _write(full, doc)
    os.makedirs(os.path.join(d, "picks"), exist_ok=True)
    return d


def _at(fn, now):
    def call(*a, **k):
        if len(a) < 3 and k.get("now") is None:
            k["now"] = now
        return fn(*a, **k)
    return call


def passes(d, lg, mode, fail_at):
    """The REAL converge, one pass at each of PASSES, in `d`. `mode` raises (our own
    failure) when `fail_at(i)` for pass i, and otherwise succeeds; every other mode is
    recorded and not run. -> the passes `mode` was attempted on."""
    keys = ("GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH", "LEAGUE", "ODDS_API_KEY", "CFBD_API_KEY",
            "RELAY_HELD", "RELAY_LINK")
    saved_env = {k: os.environ.get(k) for k in keys}
    saved = F.plan, F.survey, F.record_builds
    tried = []
    for k in keys:
        os.environ.pop(k, None)
    os.environ["LEAGUE"] = lg
    try:
        with inside(d):
            import collect
            importlib.reload(collect)
            state = {"i": None}

            def run_mode(m):
                if m == mode:
                    tried.append(state["i"])
                    if fail_at(state["i"]):
                        raise RuntimeError("planted: a defect of our own in %s" % m)

            def no_http(*a, **k):
                raise AssertionError("a test reached the network: %r" % (a,))
            collect.run_mode, collect.get = run_mode, no_http
            collect.odds_get = lambda *a, **k: ([], 0, 19000)
            collect.daily_spend = lambda *a, **k: 0
            collect.log = lambda *a, **k: None
            for i, at in enumerate(PASSES):
                state["i"] = i
                collect.now = lambda at=at: at
                F.plan, F.survey, F.record_builds = (_at(f, at) for f in saved)
                with contextlib.redirect_stdout(io.StringIO()):
                    collect.converge()
                F.plan, F.survey, F.record_builds = saved
        return tried
    finally:
        F.plan, F.survey, F.record_builds = saved
        for k in keys:
            os.environ.pop(k, None)
            if saved_env[k] is not None:
                os.environ[k] = saved_env[k]


# ══════════════════════════════════════════════════════════════════════
section("1. THE CLASS: EVERY METERED MODE IN EVERY FOOTBALL LEAGUE THAT HAS ITS ROW")
# ══════════════════════════════════════════════════════════════════════
CASES = [(m, lg) for m in sorted(F.STAND_DOWN) for lg in ("ncaaf", "nfl")
         if m in {r[0] for r in contract_rows(lg, T0)}]
ck("⚠️ the metered modes were DERIVED from STAND_DOWN and the contracts (rule 67)",
   len(CASES) >= 4 and {m for m, _lg in CASES} == set(F.STAND_DOWN), CASES)
ck("⚠️ the bound is the floor's own arithmetic: %d passes over %.0f minutes, at most 2 + ceil((%.0f - 15) "
   "/ METERED_RETRY_MIN %d) = %d attempts" % (len(PASSES), SPAN, SPAN, F.METERED_RETRY_MIN, BOUND),
   BOUND < len(PASSES) / 2)

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 A MODE THAT FAILS ON EVERY ATTEMPT IS ASKED AT MOST %d TIMES IN 4 HOURS" % BOUND)
# ══════════════════════════════════════════════════════════════════════
for m, lg in CASES:
    d = tree(lg, T0, m)
    try:
        tried = passes(d, lg, m, lambda i: True)
        ck("🔴🔴 %s (%s), failing on our side every time: %d attempts in %d passes (at most %d)"
           % (m, lg, len(tried), len(PASSES), BOUND),
           2 <= len(tried) <= BOUND, "⛔ before 11-18 it was tried on every pass: %s" % tried)
        ck("   ...the first retry is the very next pass (a one-off blip recovers at once)",
           tried[:2] == [0, 1], tried)
        gaps = [(b - a) * 15 for a, b in zip(tried[1:], tried[2:])]
        ck("   ...then each attempt waits METERED_RETRY_MIN (%d) or more" % F.METERED_RETRY_MIN,
           all(g >= F.METERED_RETRY_MIN for g in gaps), gaps)
        with inside(d):
            _rows = [r for r in F.survey("data/%s" % lg, "picks", PASSES[-1]) if r["mode"] == m]
            _rec = json.load(open(os.path.join("data", lg, "latest", F.METERED_ATTEMPTS), encoding="utf-8"))
        ck("⛔ ...its row stays out of contract while it waits (the gate still says so)",
           any(r["stale"] for r in _rows), [(r["path"], r["stale"]) for r in _rows][:2])
        ck("   ...and the record says how many and why", _rec.get(m, {}).get("fails") == len(tried)
           and "planted" in _rec.get(m, {}).get("why", ""), _rec.get(m))
    finally:
        shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("3. ✅ A SUCCESS CLEARS IT; ONE FAILURE ALONE NEVER WAITS")
# ══════════════════════════════════════════════════════════════════════
m, lg = CASES[0]
d = tree(lg, T0, m)
try:
    tried = passes(d, lg, m, lambda i: i < 2)          # fails twice, then works
    with inside(d):
        _left = F.retry_wait("data/%s" % lg, m, PASSES[-1])
        _gone = not os.path.exists(os.path.join("data", lg, "latest", F.METERED_ATTEMPTS))
    ck("✅ %s fails twice, waits, then works: tried again after the wait and on every pass after it"
       % m, tried[:2] == [0, 1] and len(tried) > BOUND and tried[2] * 15 >= F.METERED_RETRY_MIN, tried)
    ck("✅ ...and the success cleared its record (no wait, the file gone)", _left == 0 and _gone, (_left, _gone))
finally:
    shutil.rmtree(d, ignore_errors=True)
d = tree(lg, T0, m)
try:
    tried = passes(d, lg, m, lambda i: i % 2 == 0)     # fails, works, fails, works ...
    eq(tried, list(range(len(PASSES))), "⛔ failures that never come twice in a row never wait")
finally:
    shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE COLLEGE TEAM DIRECTORY'S CFBD CALL WAITS TOO")
# ══════════════════════════════════════════════════════════════════════


def directory(fail_at, still=False):
    """collect._ensure_cfb_team_directory at each of PASSES, its directory always
    needing a rebuild; `cfb.fbs_conferences` raises when `fail_at(i)`, and with `still`
    it answers but leaves the directory needing a rebuild (`[2026-11-20, review]`: a
    season rollover, CFBD holding nothing for the new season yet). -> the passes that
    called CFBD."""
    keys = ("LEAGUE", "GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH")
    saved_env = {k: os.environ.get(k) for k in keys}
    saved_cfb = sys.modules.get("cfb")
    d = tempfile.mkdtemp(prefix="teamdir-", dir=_TMP)
    calls = []
    try:
        for k in keys:
            os.environ.pop(k, None)
        os.environ["LEAGUE"] = "ncaaf"
        with inside(d):
            import collect
            importlib.reload(collect)
            state = {"i": None, "ok": False}

            def fbs(season, log):
                calls.append(state["i"])
                if fail_at(state["i"]):
                    raise RuntimeError("planted: our own defect")
                state["ok"] = not still
            sys.modules["cfb"] = types.SimpleNamespace(fbs_conferences=fbs)
            collect.cfb_team_directory_state = lambda: ((False, "ok") if state["ok"] else (True, "missing"))
            collect.log = lambda *a, **k: None
            for i, at in enumerate(PASSES):
                state["i"], state["ok"] = i, False
                collect.now = lambda at=at: at
                collect._ensure_cfb_team_directory()
        return calls
    finally:
        if saved_cfb is None:
            sys.modules.pop("cfb", None)
        else:
            sys.modules["cfb"] = saved_cfb
        for k in keys:
            os.environ.pop(k, None)
            if saved_env[k] is not None:
                os.environ[k] = saved_env[k]
        shutil.rmtree(d, ignore_errors=True)


_c = directory(lambda i: True)
ck("🔴🔴 the team directory, failing every time: CFBD asked %d times in %d passes (at most %d)"
   % (len(_c), len(PASSES), BOUND), 2 <= len(_c) <= BOUND and _c[:2] == [0, 1],
   "⛔ before 11-18 it was asked before every college mode of every pass: %s" % _c)
eq(directory(lambda i: False), list(range(len(PASSES))),
   "✅ a rebuild that works is never held back (each pass here needs one again)")
_c = directory(lambda i: False, still=True)
ck("🔴 [2026-11-20, review] ...and one CFBD ANSWERS but that leaves the directory still needing a rebuild (a "
   "season rollover, nothing for the new season yet) counts as a failure: asked %d times in %d passes (at most %d)"
   % (len(_c), len(PASSES), BOUND), 2 <= len(_c) <= BOUND and _c[:2] == [0, 1],
   "⛔ unrecorded, CFBD was asked before every college mode of every link pass: %s" % _c)

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 [2026-11-20, review] A DEADLINE THAT PASSES MID-PASS DOES NOT CUT THE WAIT SHORT")
# ══════════════════════════════════════════════════════════════════════
# The catch-up (freshness.caught_up) builds a row whose deadline passes WHILE a pass runs. A
# metered mode inside its wait is skipped there too (`_bad`), or a link pass that straddles one of
# its deadlines (a game-day fb-scores deadline, the 3:00 ET cfb-probe build) would retry it at once.
# Each class case: a pass 3 minutes before the mode's next deadline, everything inside contract,
# the mode's record planted (failed twice, the last 10 minutes ago), the hourly cron naming `news`,
# each mode taking 7 minutes of the pinned clock, so the deadline passes inside the pass.


def straddle(d, lg, at, step=7):
    """The REAL converge in `d` at `at` naming `news`, each mode recorded and not run and moving
    the pinned clock `step` minutes. -> [(mode, minute)], the log."""
    keys = ("GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH", "LEAGUE", "ODDS_API_KEY", "CFBD_API_KEY",
            "RELAY_HELD", "RELAY_LINK")
    saved_env = {k: os.environ.get(k) for k in keys}
    saved = F.plan, F.survey, F.record_builds, F.code_moves
    clk, ran = [at], []
    for k in keys:
        os.environ.pop(k, None)
    os.environ["LEAGUE"] = lg
    try:
        with inside(d):
            import collect
            importlib.reload(collect)

            def run_mode(m):
                ran.append((m, clk[0]))
                clk[0] = clk[0] + step * MIN

            def no_http(*a, **k):
                raise AssertionError("a test reached the network: %r" % (a,))

            def pin(fn):
                def call(*a, **k):
                    if len(a) < 3 and k.get("now") is None:
                        k["now"] = clk[0]
                    return fn(*a, **k)
                return call
            collect.run_mode, collect.get = run_mode, no_http
            collect.odds_get = lambda *a, **k: ([], 0, 19000)
            collect.daily_spend = lambda *a, **k: 0
            collect.now = lambda: clk[0]
            F.plan, F.survey, F.record_builds = (pin(f) for f in saved[:3])
            F.code_moves = lambda data="data", root=None: set()
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                collect.converge(explicit=["news"])
        return ran, out.getvalue()
    finally:
        F.plan, F.survey, F.record_builds, F.code_moves = saved
        for k in keys:
            os.environ.pop(k, None)
            if saved_env[k] is not None:
                os.environ[k] = saved_env[k]


_waited, _ctl, _n5 = [], [], 0
for m, lg in CASES:
    _rows = [r for r in contract_rows(lg, T0) if r[0] == m and r[2]]
    _due = min(x for x in (F.next_due(r[2], T0) for r in _rows) if x is not None)
    _at = _due - 3 * MIN
    for _planted in (True, False):
        d = tree(lg, _at, None)
        try:
            if _planted:
                with inside(d):
                    _write(os.path.join("data", lg, "latest", F.METERED_ATTEMPTS),
                           {m: {"fails": 2, "first_failed_at": (_at - 40 * MIN).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "last_failed_at": (_at - 10 * MIN).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "why": "planted: failed twice"}})
            ran, out = straddle(d, lg, _at)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        got = [x for x, _t in ran]
        if _planted:
            _n5 += 1
            if m in got:
                _waited.append((m, lg, _due.strftime("%a %H:%MZ"), [(x, t.strftime("%H:%M")) for x, t in ran]))
        elif m not in got or not any("CATCH-UP:" in l and m in l for l in out.splitlines()):
            _ctl.append((m, lg, _due.strftime("%a %H:%MZ"), got))
ck("✅ control: with no failures on record, each metered mode IS built by the catch-up when its deadline "
   "passes inside the pass (%d cases), so the case reaches caught_up" % len(CASES), not _ctl, _ctl[:3])
ck("🔴 inside its wait it is NOT: %d metered modes, failed twice 10 minutes before, a deadline passing mid-pass: "
   "none asked again before METERED_RETRY_MIN (%d)" % (_n5, F.METERED_RETRY_MIN), _n5 >= 4 and not _waited,
   "⛔ without the catch-up's skip each was retried at once: %s" % _waited[:3])

shutil.rmtree(_TMP, ignore_errors=True)
note("cfb-probe keeps its own longer back-off (3h / 6h / 20h) inside its mode, on top of this floor.")
