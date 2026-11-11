#!/usr/bin/env python3
"""A DEADLINE THAT PASSES WHILE A PASS IS RUNNING IS THAT PASS'S. `[2026-11-11]`

🔴 WHAT HAPPENED. collect 42973157780: the college pass surveyed at 06:54:57Z with
cfb-probe inside contract, planned `cfb-injuries card-fb news`, and the card took 13
minutes. cfb-probe's 07:00Z deadline passed DURING the pass; its final survey wrote
freshness.json at 07:07:54Z with cfb-probe stale, and the gate failed "cfb-probe MISSED
its 3:00 ET build ... 9m past due": a red recurring run no pass could have avoided.

✅ `collect.converge` now surveys again before it writes freshness.json and builds, in the
same pass, the rows whose missed deadline passed AFTER the survey it planned from
(`freshness.caught_up`), at most `CATCH_UP_ROUNDS` times. ⛔ The gate is unchanged.

This drives the REAL `collect.converge` in a planted MLB tree on a clock that the stubbed
modes move, the way a long mode moves the real one. Nothing reads the live tree or the real
clock (CLAUDE.md, 2026-09-28).

# @vacuity 🔴🔴 the pass builds what fell due while it ran
#   file: collect.py
#   find:         run_modes(todo)
#   with:         pass
#
# @vacuity 🔴 a mode that failed this pass is never retried, even when a later deadline passes
#   file: freshness.py
#   find:             and _after(r.get("due_at"), since)} - set(skip)
#   with:             and _after(r.get("due_at"), since)}
#
# @vacuity 🔴 ...the skip set is this pass's failures
#   file: collect.py
#   find:         _bad = {m for m, *_ in failed} | {m for m, _w in soft_failed} | set(skipped)
#   with:         _bad = set()
#
# @vacuity 🔴 ...nor as a CASCADE follower
#   file: freshness.py
#   find:     need = cascaded(late) - set(skip)          # ...nor as a follower
#   with:     need = cascaded(late)
#
# @vacuity 🔴 a missing row was planned already and is never caught up
#   file: freshness.py
#   find:     late = {r["mode"] for r in rows if owes(r, allow_paid) and not r["missing"]
#   with:     late = {r["mode"] for r in rows if owes(r, allow_paid)
#
# @vacuity 🔴 only a deadline AFTER the plan's survey counts
#   file: freshness.py
#   find:     return due > since
#   with:     return True
#
# @vacuity ⛔ bounded: at most CATCH_UP_ROUNDS rounds
#   file: collect.py
#   find:                 if _round < CATCH_UP_ROUNDS else [])
#   with:                 if True else [])
#
# @vacuity ⛔ a paid mode still runs at most once a pass
#   file: collect.py
#   find:             if m in paid and m in _RAN_PAID:
#   with:             if False:
"""
import contextlib
import datetime
import importlib
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, eq, note, section, shown  # noqa: E402

os.environ["LEAGUE"] = "mlb"
os.environ.setdefault("ODDS_API_KEY", "test")
import freshness as F  # noqa: E402

UTC = datetime.timezone.utc
# MLB's game-model, gamelines and props rows are due at 7:00/16:00 ET = 11:00Z / 20:00Z (the
# contract's fixed -4). The pass plans at 19:58Z; the first mode it runs moves the clock to 20:05Z.
T0 = datetime.datetime(2026, 11, 4, 19, 58, tzinfo=UTC)
LATE = datetime.datetime(2026, 11, 4, 20, 5, tzinfo=UTC)
DEADLINE = "2026-11-04T20:00Z"
GM = "data/latest/mlb-game-model.json"
BOARD = "data/latest/board.json"
PROPS = "data/latest/props.json.gz"


def ts(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def plant(d, rel, t):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if rel.endswith(".gz"):
        import gzip
        with gzip.open(p, "wt", encoding="utf-8") as fh:
            json.dump({"pulled_at": ts(t), "built_at": ts(t)}, fh)
    else:
        with open(p, "w", encoding="utf-8") as fh:
            json.dump({"pulled_at": ts(t), "built_at": ts(t)}, fh)


def sandbox(planted):
    """An MLB tree holding only the planted artifacts ({path: built at})."""
    d = tempfile.mkdtemp(prefix="catchup-")
    os.makedirs(f"{d}/data/latest")
    os.makedirs(f"{d}/picks")
    for rel, t in planted.items():
        plant(d, rel, t)
    return d


def converge(d, clock, run):
    """The real converge in `d` on the moving `clock` ([datetime]); `run(m)` is the stub
    run_mode (it may move the clock, plant files, raise). -> (code, stdout, survey calls)."""
    cwd = os.getcwd()
    os.chdir(d)
    try:
        import collect
        importlib.reload(collect)
        fresh = collect._fresh
        calls = []

        def at_clock(fn, name):
            def call(*a, **k):
                if len(a) < 3 and k.get("now") is None:
                    k["now"] = clock[0]
                if name == "survey":
                    calls.append(clock[0])
                return fn(*a, **k)
            return call
        saved = collect.now, fresh.plan, fresh.survey
        collect.now = lambda: clock[0]
        fresh.plan, fresh.survey = at_clock(fresh.plan, "plan"), at_clock(fresh.survey, "survey")
        collect.run_mode = run
        collect.daily_spend = lambda: 0
        collect.daily_allowance = lambda: 10 ** 6
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                code = collect.converge()
        finally:
            collect.now, fresh.plan, fresh.survey = saved
        return code, out.getvalue(), calls
    finally:
        os.chdir(cwd)


def written(d, rel):
    """The final freshness.json's row for `rel`."""
    with open(f"{d}/data/latest/freshness.json", encoding="utf-8") as fh:
        doc = json.load(fh)
    return next(a for a in doc["artifacts"] if a["path"].endswith(rel))


def catch_up_line(out):
    return [l for l in out.splitlines() if "CATCH-UP:" in l]


def ran(log, mode):
    return [t for m, t in log if m == mode]


# ══════════════════════════════════════════════════════════════════════
section("0. THE PLANTED TREE: game-model inside contract when the pass plans")
# ══════════════════════════════════════════════════════════════════════
d = sandbox({GM: T0 - datetime.timedelta(minutes=8)})
rows0 = {r["path"].replace(d + "/", ""): r for r in F.survey(data=d + "/data", picks=d + "/picks", now=T0)}
modes0, _ = F.plan(data=d + "/data", picks=d + "/picks", now=T0)
ck(not rows0[GM]["stale"], "game-model, built 19:50Z, is inside contract at 19:58Z", rows0[GM])
ck("game-model" not in modes0, "...so the pass does not plan it", modes0)
rows1 = {r["path"].replace(d + "/", ""): r for r in F.survey(data=d + "/data", picks=d + "/picks", now=LATE)}
eq(rows1[GM]["due_at"], DEADLINE, "...and at 20:05Z its 20:00Z deadline has passed: stale, due 20:00Z")
ck(rows1[GM]["stale"], "...stale", rows1[GM])
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 11-11's CASE: THE DEADLINE PASSES WHILE THE PASS RUNS -> BUILT IN THE SAME PASS")
# ══════════════════════════════════════════════════════════════════════
d = sandbox({GM: T0 - datetime.timedelta(minutes=8)})
clock, log = [T0], []


def run1(m):
    log.append((m, clock[0]))
    if len(log) == 1:
        clock[0] = LATE                         # the first mode takes 7 minutes
    if m == "game-model":
        plant(d, GM, clock[0])


code, out, surveys = converge(d, clock, run1)
eq(ran(log, "game-model"), [LATE], "🔴🔴 game-model is built once, at 20:05Z, after its deadline passed")
ck(len(catch_up_line(out)) == 1 and "CATCH-UP: game-model " in catch_up_line(out)[0]
   and DEADLINE in catch_up_line(out)[0] and "19:58:00Z" in catch_up_line(out)[0],
   "...and the log says so: the mode, its deadline, the survey it planned from", shown(catch_up_line(out)))
ck(not written(d, GM)["stale"], "🔴🔴 freshness.json, written after the catch-up, has it inside contract",
   written(d, GM))
_rows = json.load(open(f"{d}/data/latest/freshness.json", encoding="utf-8"))["artifacts"]
hard, _soft = F.classify(_rows, data=d + "/data", refused=False, block={"state": None}, now=LATE)
ck(not [r for r in hard if r["mode"] == "game-model"],
   "🔴🔴 ...so the gate has nothing to fail it on (this was 11-11's red run)", [r["mode"] for r in hard])
eq(F.caught_up([dict(r, path=r["path"]) for r in _rows], T0), [],
   "...and nothing else that fell due mid-pass is left (every other planted-late row is missing)")
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("2. ⛔ A PASS WITH NOTHING LATE COSTS NOTHING EXTRA")
# ══════════════════════════════════════════════════════════════════════
d = sandbox({GM: T0 - datetime.timedelta(minutes=8)})
clock, log = [T0], []
code, out, surveys = converge(d, clock, lambda m: log.append((m, clock[0])))
eq(catch_up_line(out), [], "a pass on a still clock catches nothing up")
eq(len(surveys), 2, "...and surveys exactly twice, as before: the plan's and the one freshness.json is written from")
eq(ran(log, "game-model"), [], "...and game-model, inside contract, is not run")
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 A MODE THAT FAILED THIS PASS IS NEVER RETRIED, EVEN WHEN A LATER DEADLINE PASSES")
# ══════════════════════════════════════════════════════════════════════
# game-model built 10:50Z: it missed 11:00Z, so the plan has it. It fails; the clock passes 20:00Z,
# so its row now reads "due 20:00Z", after the plan's survey: the shape an hourly row has.
d = sandbox({GM: T0.replace(hour=10, minute=50)})
clock, log = [T0], []


def run3(m):
    log.append((m, clock[0]))
    if len(log) == 1:
        clock[0] = LATE
    if m == "game-model":
        raise RuntimeError("the game model failed")


code, out, surveys = converge(d, clock, run3)
eq(len(ran(log, "game-model")), 1, "🔴 the failed game-model runs once, never again in the catch-up")
eq(catch_up_line(out), [], "...so there is no catch-up at all")
ck(written(d, GM)["stale"], "⛔ ...and it stays out of contract: the gate judges it exactly as before", written(d, GM))
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 ...NOR AS A CASCADE FOLLOWER")
# ══════════════════════════════════════════════════════════════════════
# The board (gamelines) is inside contract at 19:58Z; props-board (built 10:50Z) is planned and fails.
# At 20:05Z the board is due: gamelines is caught up, and CASCADE would bring props-board with it.
d = sandbox({BOARD: T0 - datetime.timedelta(minutes=8), PROPS: T0.replace(hour=10, minute=50)})
clock, log = [T0], []


def run4(m):
    log.append((m, clock[0]))
    if len(log) == 1:
        clock[0] = LATE
    if m == "props-board":
        raise RuntimeError("the props board failed")
    if m == "gamelines":
        plant(d, BOARD, clock[0])


code, out, surveys = converge(d, clock, run4)
eq(ran(log, "gamelines"), [LATE], "the board that fell due mid-pass is caught up")
eq(len(ran(log, "props-board")), 1, "🔴 ...but props-board, which failed this pass, is not run again behind it")
ck(catch_up_line(out) and "props-board" not in catch_up_line(out)[0].split("—")[0],
   "...and the catch-up line does not list it", shown(catch_up_line(out)))
shutil.rmtree(d, ignore_errors=True)

# The board missed 11:00Z, so gamelines is planned and FAILS; props-board (no file yet) is planned
# behind it, runs and writes nothing. At 20:05Z the board's row reads "due 20:00Z", after the plan's
# survey: gamelines failed this pass, so nothing is caught up, and CASCADE brings no follower either.
d = sandbox({BOARD: T0.replace(hour=10, minute=50)})
clock, log = [T0], []


def run4b(m):
    log.append((m, clock[0]))
    if len(log) == 1:
        clock[0] = LATE
    if m == "gamelines":
        raise RuntimeError("the gamelines pull failed")


code, out, surveys = converge(d, clock, run4b)
eq(len(ran(log, "props-board")), 1, "🔴 a failed mode's CASCADE followers are not run again behind it")
eq(catch_up_line(out), [], "...so there is no catch-up at all")
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("5. ⛔ A PAID MODE STILL RUNS AT MOST ONCE A PASS")
# ══════════════════════════════════════════════════════════════════════
# The board missed 11:00Z, so gamelines is planned and bought at 19:59Z; the 20:00Z deadline then
# passes, so the board is due again, after the plan's survey. The catch-up asks for it; the
# once-a-pass rule refuses it, and the board is the gate's to judge, as before.
d = sandbox({BOARD: T0.replace(hour=10, minute=50)})
clock, log = [T0], []


def run5(m):
    log.append((m, clock[0]))
    if m == "gamelines":
        plant(d, BOARD, clock[0] + datetime.timedelta(minutes=1))
        clock[0] = LATE


code, out, surveys = converge(d, clock, run5)
eq(len(ran(log, "gamelines")), 1, "⛔ gamelines is bought once in the pass")
ck(any("gamelines already ran this pass" in l for l in out.splitlines()),
   "...the catch-up asked for it and the once-a-pass rule said no, out loud", shown(catch_up_line(out)))
ck(written(d, BOARD)["stale"], "...so the board is out of contract for the gate, exactly as before", written(d, BOARD))
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("6. ⛔ BOUNDED, AND ONLY A DEADLINE AFTER THE PLAN'S SURVEY COUNTS")
# ══════════════════════════════════════════════════════════════════════
# Every game-model build moves the clock past its next deadline, so every survey finds it due again.
d = sandbox({GM: T0 - datetime.timedelta(minutes=8)})
clock, log = [T0], []
NEXT = [LATE, datetime.datetime(2026, 11, 5, 11, 5, tzinfo=UTC), datetime.datetime(2026, 11, 5, 20, 5, tzinfo=UTC),
        datetime.datetime(2026, 11, 6, 11, 5, tzinfo=UTC), datetime.datetime(2026, 11, 6, 20, 5, tzinfo=UTC)]


def run6(m):
    log.append((m, clock[0]))
    if len(log) == 1:
        clock[0] = NEXT[0]
    elif m == "game-model":
        plant(d, GM, clock[0])
        clock[0] = NEXT[min(len(ran(log, "game-model")), len(NEXT) - 1)]


code, out, surveys = converge(d, clock, run6)
import collect as _C  # noqa: E402
eq(len(ran(log, "game-model")), _C.CATCH_UP_ROUNDS,
   "⛔ a pass catches up at most CATCH_UP_ROUNDS times (%d), however many deadlines pass" % _C.CATCH_UP_ROUNDS)
eq(len(catch_up_line(out)), _C.CATCH_UP_ROUNDS, "...one CATCH-UP line per round")
ck(written(d, GM)["stale"], "...and what is still late after the last round is the gate's", written(d, GM))
shutil.rmtree(d, ignore_errors=True)

_r = {"mode": "game-model", "stale": True, "missing": False, "paid": False, "due_at": "2026-11-04T19:00Z",
      "path": GM}
eq(F.caught_up([_r], T0), [], "🔴 a row whose missed deadline (19:00Z) came BEFORE the plan's survey is not caught up")
eq(F.caught_up([dict(_r, due_at=DEADLINE)], T0), ["game-model"], "...one whose deadline came after it is")
eq(F.caught_up([dict(_r, due_at=DEADLINE, missing=True)], T0), [], "🔴 ...unless the artifact is missing")
eq(F.caught_up([dict(_r, due_at=DEADLINE)], T0, skip={"game-model"}), [], "...or its mode failed this pass")
eq(F.caught_up([dict(_r, due_at=DEADLINE, paid=True)], T0, allow_paid=False), [],
   "...and a paid row only when paid modes are allowed (the plan's own rule)")
eq(F.caught_up([dict(_r, due_at=None)], T0), [], "...and a row with no deadline never")
note("CATCH_UP_ROUNDS = %d" % _C.CATCH_UP_ROUNDS)
