#!/usr/bin/env python3
"""A DEADLINE THAT PASSES WHILE A PASS IS RUNNING IS THAT PASS'S. `[2026-11-11]`

🔴 WHAT HAPPENED. collect 42973157780: the college pass surveyed at 06:54:57Z with
cfb-probe inside contract, planned `cfb-injuries card-fb news`, and the card took 13
minutes. cfb-probe's 07:00Z deadline passed DURING the pass; its final survey wrote
freshness.json at 07:07:54Z with cfb-probe stale, and the gate failed "cfb-probe MISSED
its 3:00 ET build ... 9m past due": a red recurring run no pass could have avoided.

✅ `collect.converge` now surveys again before it writes freshness.json and builds, in the
same pass, the FREE rows whose missed deadline passed AFTER the survey it planned from
(`freshness.caught_up`), at most `CATCH_UP_ROUNDS` times. ⛔ The gate is unchanged, a failed
mode is never retried, a paid pull is never bought by the catch-up (its own cron, in its own
concurrency group, buys it), and a free row built from that deadline's paid pull (the MLB
game model, the props board) waits for the pass that buys it.

This drives the REAL `collect.converge` in a planted MLB tree on a clock that the stubbed
modes move, the way a long mode moves the real one. Nothing reads the live tree or the real
clock (CLAUDE.md, 2026-09-28).

# @vacuity 🔴🔴 the pass builds what fell due while it ran
#   file: collect.py
#   find:         run_modes(todo)
#   with:         pass
#
# @vacuity 🔴 a mode that failed this pass is never retried, even when a later deadline passes
#   file: collect.py
#   find:         _bad = {m for m, *_ in failed} | {m for m, _w in soft_failed}
#   with:         _bad = set()
#
# @vacuity 🔴 ...a SOFT mode that failed included
#   file: collect.py
#   find:         _bad = {m for m, *_ in failed} | {m for m, _w in soft_failed}
#   with:         _bad = {m for m, *_ in failed}
#
# @vacuity 🔴 ...and a failed mode's CASCADE followers are not run behind it
#   file: freshness.py
#   find:             and r["mode"] not in held} - set(skip)
#   with:             and r["mode"] not in held}
#
# @vacuity 🔴 ...nor is a failed follower run behind a late mode
#   file: freshness.py
#   find:     need = cascaded(late) - set(skip)          # ...nor as a follower
#   with:     need = cascaded(late)
#
# @vacuity 🔴 a late mode brings its CASCADE followers
#   file: freshness.py
#   find:     need = cascaded(late) - set(skip)          # ...nor as a follower
#   with:     need = set(late) - set(skip)
#
# @vacuity 🔴 ...in the contract's order
#   file: freshness.py
#   find:     return [m for m in order if m in need]
#   with:     return [m for m in reversed(order) if m in need]
#
# @vacuity 🔴🔴 a dated path that rolls at its own deadline (the MLB card) is caught up
#   file: freshness.py
#   find:             and (not r["missing"] or r["mode"] not in ran
#   with:             and (not r["missing"]
#
# @vacuity 🔴🔴 ...also when its mode ran before the roll (results)
#   file: freshness.py
#   find:                  or (seen is not None and (r["mode"], r["path"]) not in seen))
#   with:                  )
#
# @vacuity 🔴 ...but a missing row whose mode RAN, at the same path, wrote nothing
#   file: freshness.py
#   find:             and (not r["missing"] or r["mode"] not in ran
#   with:             and (True or r["mode"] not in ran
#
# @vacuity 🔴 ...which needs the pass to record what it ran
#   file: collect.py
#   find:                 attempted.add(m)
#   with:                 pass
#
# @vacuity ⛔ the catch-up never buys a paid pull
#   file: collect.py
#   find:         todo = (_fresh.caught_up(rows2, looked, allow_paid=False, skip=_bad, ran=attempted,
#   with:         todo = (_fresh.caught_up(rows2, looked, allow_paid=allow_paid, skip=_bad, ran=attempted,
#
# @vacuity 🔴🔴 a free row built from a deadline's paid pull waits for the pass that buys it
#   file: freshness.py
#   find:             and r["mode"] not in held} - set(skip)
#   with:             } - set(skip)
#
# @vacuity 🔴🔴 ...behind a paid row owed for an EARLIER deadline too (the card, 11:00Z's pull)
#   file: freshness.py
#   find:             and any(d <= r["due_at"] and p < pos[r["mode"]] for d, p in unbought)}
#   with:             and any(d == r["due_at"] and p < pos[r["mode"]] for d, p in unbought)}
#
# @vacuity 🔴 ...only a row AFTER the paid one in the contract's (dependency) order
#   file: freshness.py
#   find:             and any(d <= r["due_at"] and p < pos[r["mode"]] for d, p in unbought)}
#   with:             and any(d <= r["due_at"] for d, p in unbought)}
#
# @vacuity 🔴 ...and only while that paid row is one this catch-up will not buy
#   file: freshness.py
#   find:                 if r["paid"] and r.get("due_at") and owes(r, True) and not owes(r, allow_paid)]
#   with:                 if r["paid"] and r.get("due_at") and owes(r, True)]
#
# @vacuity 🔴🔴 a longer pass costs a row it did not build nothing of the 10-19 rule
#   file: collect.py
#   find:     rows2 = _fresh.last_looks(rows2, end_rows, end_at, caught_now)
#   with:     pass
#
# @vacuity 🔴 ...the gate reads the row's own last look
#   file: freshness.py
#   find:         then = rec.get("stale_then", rec.get("stale")) if isinstance(rec, dict) else None
#   with:         then = rec.get("stale") if isinstance(rec, dict) else None
#
# @vacuity 🔴 ...and judges it against that survey's time
#   file: freshness.py
#   find:         at = mine if mine is not None and mine <= look else look
#   with:         at = look
#
# @vacuity 🔴 ...but a row the catch-up RAN and left stale stays strict
#   file: collect.py
#   find:         caught_now.update(todo)
#   with:         pass
#
# @vacuity 🔴 ...as last_looks itself says
#   file: freshness.py
#   find:                 and r.get("mode") not in built and _after(r.get("due_at"), at)):
#   with:                 and _after(r.get("due_at"), at)):
#
# @vacuity 🔴 ...and so does a row already stale at that survey, or due before it
#   file: freshness.py
#   find:         if (r.get("stale") and w is not None and w.get("stale") is False
#   with:         if (r.get("stale") and w is not None
#
# @vacuity 🔴 ...only a deadline after that survey
#   file: freshness.py
#   find:                 and r.get("mode") not in built and _after(r.get("due_at"), at)):
#   with:                 and r.get("mode") not in built):
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
# @vacuity 🔴 each round asks from the previous round's survey
#   file: collect.py
#   find:         looked = _at
#   with:         pass
#
# @vacuity 🔴 ...taken when that round surveyed
#   file: collect.py
#   find:         _at = now()
#   with:         _at = looked
#
# @vacuity 🔴 ONE CLOCK: the plan is asked at converge's own clock
#   file: collect.py
#   find:     modes, rows = _fresh.plan(data=DATA, picks=PICKS, now=looked, allow_paid=allow_paid)
#   with:     modes, rows = _fresh.plan(data=DATA, picks=PICKS, allow_paid=allow_paid)
#
# @vacuity 🔴 ...and so is every survey
#   file: collect.py
#   find:         rows2 = _fresh.survey(data=DATA, picks=PICKS, now=_at)
#   with:         rows2 = _fresh.survey(data=DATA, picks=PICKS)
"""
import contextlib
import datetime
import gzip
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


def at(day, h, m):
    return datetime.datetime(2026, 11, day, h, m, tzinfo=UTC)


def mins(n):
    return datetime.timedelta(minutes=n)


# The contract's fixed -4: scores, results, hitters, hitters and record are due 6:00 ET = 10:00Z
# (no paid row shares it; results' path is dated and rolls then); gamelines, props and the game
# model 7:00/16:00 ET = 11:00Z / 20:00Z; the card, lineups and weather 10:00 ET = 14:00Z; news
# 9:05/15:05/21:05 ET = 13:05Z / 19:05Z. Each case plans a few minutes before a deadline, and a
# mode the pass runs moves the clock past it.
T0, LATE = at(4, 9, 58), at(4, 10, 5)
DEADLINE = "2026-11-04T10:00Z"
HIT = "data/latest/hitters.json.gz"
SCORES = "data/latest/scores.json.gz"
RECORD = "data/latest/record.json"
NEWS = "data/latest/news.json"
GM = "data/latest/mlb-game-model.json"
BOARD = "data/latest/board.json"
PROPS = "data/latest/props.json.gz"
ODDS_1104 = {BOARD: datetime.datetime(2026, 11, 4, 11, 5, tzinfo=UTC), PROPS: datetime.datetime(2026, 11, 4, 11, 5, tzinfo=UTC),
             GM: datetime.datetime(2026, 11, 4, 11, 10, tzinfo=UTC),
             "data/2026-11-04/props-pitcher/1105.json.gz": datetime.datetime(2026, 11, 4, 11, 5, tzinfo=UTC),
             "data/2026-11-04/props-batter/1105.json.gz": datetime.datetime(2026, 11, 4, 11, 5, tzinfo=UTC)}


def ts(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def plant(d, rel, t):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    doc = {"pulled_at": ts(t), "built_at": ts(t)}
    if rel.endswith(".gz"):
        with gzip.open(p, "wt", encoding="utf-8") as fh:
            json.dump(doc, fh)
    else:
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)


def sandbox(planted):
    """An MLB tree holding only the planted artifacts ({path: built at})."""
    d = tempfile.mkdtemp(prefix="catchup-")
    os.makedirs(f"{d}/data/latest")
    os.makedirs(f"{d}/picks")
    for rel, t in planted.items():
        plant(d, rel, t)
    return d


def path_of(d, mode, t):
    """`mode`'s (first) contract path at `t`, relative to the tree: dated paths roll."""
    return next(r["path"] for r in F.survey(data=d + "/data", picks=d + "/picks", now=t)
                if r["mode"] == mode).replace(d + "/", "")


ASKED = []            # (plan|survey, the `now` converge passed, the clock then)


def converge(d, clock, run):
    """The real converge in `d` on the moving `clock` ([datetime]); `run(m)` is the stub
    run_mode (it may move the clock, plant files, raise). -> (code, stdout, survey times)."""
    cwd = os.getcwd()
    os.chdir(d)
    try:
        import collect
        importlib.reload(collect)
        fresh = collect._fresh
        calls = []
        ASKED.clear()

        def at_clock(fn, name):
            def call(*a, **k):
                # what converge itself passed, before this harness fills a gap (section 2)
                ASKED.append((name, a[2] if len(a) >= 3 else k.get("now"), clock[0]))
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


def final_rows(d):
    with open(f"{d}/data/latest/freshness.json", encoding="utf-8") as fh:
        return json.load(fh)["artifacts"]


def written(d, rel):
    """The final freshness.json's row for `rel`."""
    return next(a for a in final_rows(d) if a["path"].replace("\\", "/").endswith(rel))


def hard_modes(d, now):
    """The gate's hard rows, run as verify_freshness runs it: from inside the tree, on a
    survey taken at `now`, against the freshness.json converge wrote."""
    cwd = os.getcwd()
    os.chdir(d)
    try:
        rows = F.survey(data="data", picks="picks", now=now)
        hard, _soft = F.classify(rows, data="data", refused=False, block={"state": None}, now=now)
    finally:
        os.chdir(cwd)
    return [r["mode"] for r in hard]


def catch_up_line(out):
    return [l for l in out.splitlines() if "CATCH-UP:" in l]


def caught(out):
    """The modes each CATCH-UP line names, in order."""
    return [l.split("CATCH-UP: ", 1)[1].split(" — ", 1)[0].split() for l in catch_up_line(out)]


def caught_all(out):
    return [m for ms in caught(out) for m in ms]


def ran(log, mode):
    return [t for m, t in log if m == mode]


def stub(d, log, clock, first_to=None, writes=None, fails=(), after_each=None):
    """A run_mode stub: logs (mode, clock); the first call moves the clock to `first_to`;
    `writes` {mode: path} plants that mode's artifact at the clock (a path may be
    'DATED', meaning the mode's own contract path at that moment); `fails` raise."""
    writes = writes or {}

    def run(m):
        log.append((m, clock[0]))
        if len(log) == 1 and first_to is not None:
            clock[0] = first_to
        if m in fails:
            raise RuntimeError("%s failed" % m)
        if m in writes:
            plant(d, path_of(d, m, clock[0]) if writes[m] == "DATED" else writes[m], clock[0])
        if after_each:
            after_each(m)
    return run


# ══════════════════════════════════════════════════════════════════════
section("0. THE PLANTED TREE: hitters inside contract when the pass plans")
# ══════════════════════════════════════════════════════════════════════
d = sandbox({HIT: T0 - mins(8)})
rows0 = {r["path"].replace(d + "/", ""): r for r in F.survey(data=d + "/data", picks=d + "/picks", now=T0)}
modes0, _ = F.plan(data=d + "/data", picks=d + "/picks", now=T0)
ck(not rows0[HIT]["stale"], "hitters, built 09:50Z, is inside contract at 09:58Z", rows0[HIT])
ck("hitters" not in modes0, "...so the pass does not plan it", modes0)
rows1 = {r["path"].replace(d + "/", ""): r for r in F.survey(data=d + "/data", picks=d + "/picks", now=LATE)}
eq(rows1[HIT]["due_at"], DEADLINE, "...and at 10:05Z its 10:00Z deadline has passed: due 10:00Z")
ck(rows1[HIT]["stale"], "...stale", rows1[HIT])
ck(not [r for r in rows1.values() if r["paid"] and r["due_at"] == DEADLINE],
   "...and no paid row shares that deadline (nothing holds it)", [r["mode"] for r in rows1.values() if r["paid"]])
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 11-11's CASE: THE DEADLINE PASSES WHILE THE PASS RUNS -> BUILT IN THE SAME PASS")
# ══════════════════════════════════════════════════════════════════════
d = sandbox({HIT: T0 - mins(8)})
clock, log = [T0], []
code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=LATE, writes={"hitters": HIT}))
eq(ran(log, "hitters"), [LATE], "🔴🔴 hitters is built once, at 10:05Z, after its deadline passed")
eq(len(catch_up_line(out)), 1, "...in one catch-up round")
ck("hitters" in caught_all(out) and DEADLINE in catch_up_line(out)[0] and "09:58:00Z" in catch_up_line(out)[0],
   "...whose line names it, its deadline and the survey the pass planned from", shown(catch_up_line(out)))
ck(not written(d, HIT)["stale"], "🔴🔴 freshness.json, written after the catch-up, has it inside contract",
   written(d, HIT))
ck("hitters" not in hard_modes(d, LATE), "🔴🔴 ...so the gate has nothing to fail it on (11-11's red run)",
   hard_modes(d, LATE))
ck(not [m for m in caught_all(out) if m in ("scores", "pitchers")],
   "🔴 ...and a missing row whose mode already ran this pass, at the same path, is not run again "
   "(scores, pitchers: their stubs wrote nothing)", shown(catch_up_line(out)))
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("2. ⛔ A PASS WITH NOTHING LATE COSTS NOTHING EXTRA, AND RUNS ON ONE CLOCK")
# ══════════════════════════════════════════════════════════════════════
d = sandbox({HIT: T0 - mins(8)})
clock, log = [T0], []
code, out, surveys = converge(d, clock, stub(d, log, clock))
eq(catch_up_line(out), [], "a pass on a still clock catches nothing up")
eq(len(surveys), 2, "...and surveys exactly twice, as before: the plan's and the one freshness.json is written from")
eq(ran(log, "hitters"), [], "...and hitters, inside contract, is not run")
shutil.rmtree(d, ignore_errors=True)
d = sandbox({HIT: T0 - mins(8)})
clock, log = [T0], []
code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=LATE, writes={"hitters": HIT}))
_mine = [x for x in ASKED if x[0] == "plan"][:1] + [x for x in ASKED if x[0] == "survey"]
ck(len(_mine) >= 3 and all(now_ == clk for _n, now_, clk in _mine),
   "🔴 ONE CLOCK: converge asks the plan and every survey at its own clock, never freshness's "
   "(test_credit_ledger pins collect.now alone; a survey on the real clock beside it caught up "
   "every free mode its plan never ran)", _mine)
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 A MODE THAT FAILED THIS PASS IS NEVER RETRIED, EVEN WHEN A LATER DEADLINE PASSES")
# ══════════════════════════════════════════════════════════════════════
# hitters built 11-03 09:50Z missed that day's 10:00Z, so the plan has it. It fails; the clock
# passes 11-04's 10:00Z, so its row now reads "due 10:00Z", after the plan's survey.
d = sandbox({HIT: at(3, 9, 50)})
clock, log = [T0], []
code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=LATE, fails={"hitters"}))
eq(len(ran(log, "hitters")), 1, "🔴 the failed hitters runs once, never again in the catch-up")
ck("hitters" not in caught_all(out), "...no catch-up line names it", shown(catch_up_line(out)))
ck(written(d, HIT)["stale"] and "hitters" in hard_modes(d, LATE),
   "⛔ ...and the gate judges it exactly as before: red", hard_modes(d, LATE))
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 ...NEITHER A FAILED FOLLOWER NOR THE FOLLOWERS OF A FAILED MODE")
# ══════════════════════════════════════════════════════════════════════
# scores -> record is a CASCADE. (a) scores inside contract at 09:58Z, record (built 11-03 09:00Z)
# planned and FAILS; at 10:05Z scores is due and caught up, and CASCADE would bring record behind it.
d = sandbox({SCORES: T0 - mins(8), RECORD: at(3, 9, 0)})
clock, log = [T0], []
code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=LATE, writes={"scores": SCORES},
                                               fails={"record"}))
eq(ran(log, "scores"), [LATE], "scores, due 10:00Z mid-pass, is caught up")
eq(len(ran(log, "record")), 1, "🔴 ...but record, which failed this pass, is not run again behind it")
ck("record" not in caught_all(out), "...and no catch-up line lists it", shown(catch_up_line(out)))
shutil.rmtree(d, ignore_errors=True)
# (b) results (missing, so planned) FAILS; record runs behind it and writes nothing. At 10:05Z results'
# path has rolled to 11-04's: owed, but it failed this pass, so it is not caught up, and CASCADE
# brings record behind nothing.
d = sandbox({})
clock, log = [T0], []
code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=LATE, fails={"results"}))
eq(len(ran(log, "results")), 1, "the failed results runs once")
eq(len(ran(log, "record")), 1, "🔴 ...and its CASCADE follower record is not run again behind it")
ck(not [m for m in caught_all(out) if m in ("results", "record")], "...no catch-up line names either",
   shown(catch_up_line(out)))
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("5. ⛔ THE CATCH-UP NEVER BUYS A PAID PULL")
# ══════════════════════════════════════════════════════════════════════
# The board is inside contract at 19:58Z, so gamelines is not planned; at 20:05Z it is due. Its own
# cron buys it (own concurrency group, own checkout): a catch-up buying here could pay twice.
d = sandbox({BOARD: at(4, 19, 50)})
clock, log = [at(4, 19, 58)], []
code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=at(4, 20, 5), writes={"gamelines": BOARD}))
eq(ran(log, "gamelines"), [], "⛔ gamelines, due 20:00Z mid-pass, is never run by the catch-up")
ck(not [m for m in caught_all(out) if m in ("gamelines", "props-pitcher", "props-batter")],
   "...no catch-up line names a paid mode", shown(catch_up_line(out)))
ck(written(d, BOARD)["stale"], "...and the board is out of contract for the gate, exactly as before", written(d, BOARD))
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("6. ⛔ BOUNDED, AND THE RULE ITSELF")
# ══════════════════════════════════════════════════════════════════════
# Every hitters build moves the clock past its next deadline, so every survey finds it due again.
d = sandbox({HIT: T0 - mins(8)})
clock, log = [T0], []
NEXT = [at(5, 10, 5), at(6, 10, 5), at(7, 10, 5), at(8, 10, 5), at(9, 10, 5), at(10, 10, 5)]


def _hop(m):
    if m == "hitters":
        clock[0] = NEXT[min(len(ran(log, "hitters")) - 1, len(NEXT) - 1)]


code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=LATE, writes={"hitters": HIT}, after_each=_hop))
import collect as _C  # noqa: E402
eq(len(ran(log, "hitters")), _C.CATCH_UP_ROUNDS,
   "⛔ a pass catches up at most CATCH_UP_ROUNDS times (%d), however many deadlines pass" % _C.CATCH_UP_ROUNDS)
eq(len(catch_up_line(out)), _C.CATCH_UP_ROUNDS, "...one CATCH-UP line per round")
ck(written(d, HIT)["stale"], "...and what is still late after the last round is the gate's", written(d, HIT))
shutil.rmtree(d, ignore_errors=True)

_r = {"mode": "hitters", "stale": True, "missing": False, "paid": False, "due_at": "2026-11-04T09:00Z", "path": HIT}
_D = dict(_r, due_at=DEADLINE)
eq(F.caught_up([_r], T0), [], "🔴 a row whose missed deadline (09:00Z) came BEFORE the plan's survey is not caught up")
eq(F.caught_up([_D], T0), ["hitters"], "...one whose deadline came after it is")
eq(F.caught_up([dict(_D, missing=True)], T0), ["hitters"],
   "🔴 ...a MISSING one too, when its mode has not run this pass (a dated path rolled)")
eq(F.caught_up([dict(_D, missing=True)], T0, ran={"hitters"}, before=[_D]), [],
   "🔴 ...but not when its mode ran this pass and left the SAME path missing (it wrote nothing)")
eq(F.caught_up([dict(_D, missing=True, path="data/2026-11-04/x")], T0, ran={"hitters"}, before=[_D]),
   ["hitters"], "🔴 ...while a path that ROLLED since the plan is owed even though its mode ran")
eq(F.caught_up([_D], T0, skip={"hitters"}), [], "...nor when its mode failed this pass")
eq(F.caught_up([dict(_D, paid=True)], T0, allow_paid=False), [], "...and a paid row never, asked as converge asks")
eq(F.caught_up([dict(_r, due_at=None)], T0), [], "...and a row with no deadline never")
# CASCADE and the contract's order (scores -> record; football's injury-check -> card-fb)
_sc = {"mode": "scores", "stale": True, "missing": False, "paid": False, "due_at": DEADLINE, "path": SCORES}
_rc = {"mode": "record", "stale": False, "missing": False, "paid": False, "due_at": DEADLINE, "path": RECORD}
eq(F.caught_up([_sc, _rc], T0), ["scores", "record"],
   "🔴 a late mode brings its CASCADE followers, a fresh one included, in the contract's order")
_ic = {"mode": "injury-check", "stale": True, "missing": False, "paid": False, "due_at": "2026-11-04T16:00Z",
       "path": "data/nfl/latest/injury-check.json"}
_cf = {"mode": "card-fb", "stale": False, "missing": False, "paid": False, "due_at": "2026-11-04T15:30Z",
       "path": "picks/fb-nfl-latest.json"}
eq(F.caught_up([_ic, _cf], at(4, 15, 55)), ["injury-check", "card-fb"],
   "🔴 ...football's injury check brings the card behind it (Sam, 2026-10-26)")
# the hold, on its own
_gl = {"mode": "gamelines", "stale": True, "missing": False, "paid": True, "due_at": "2026-11-04T20:00Z", "path": BOARD}
_gm = {"mode": "game-model", "stale": True, "missing": False, "paid": False, "due_at": "2026-11-04T20:00Z", "path": GM}
eq(F.caught_up([_gl, _gm], at(4, 19, 58), allow_paid=False), [],
   "🔴🔴 a free row due with an unbought paid row, after it in the contract, waits (the game model)")
eq(F.caught_up([_gl, _gm], at(4, 19, 58), allow_paid=True), ["gamelines", "game-model"],
   "🔴 ...but only while that paid row is one this catch-up will not buy")
eq(F.caught_up([dict(_gm, mode="first"), _gl], at(4, 19, 58), allow_paid=False), ["first"],
   "🔴 ...and only a row AFTER it in the contract's (dependency) order")
_pb = {"mode": "props-batter", "stale": True, "missing": True, "paid": True, "due_at": "2026-11-04T11:00Z",
       "path": "data/2026-11-04/props-batter"}
_cd = {"mode": "card", "stale": True, "missing": True, "paid": False, "due_at": "2026-11-04T14:00Z",
       "path": "picks/2026-11-04.json"}
eq(F.caught_up([_pb, _cd], at(4, 13, 58), allow_paid=False, skip={"props-batter"}, ran={"props-batter"}, before=[]), [],
   "🔴🔴 ...and behind a paid row owed for an EARLIER deadline: the card waits for 11:00Z's pull")
# last_looks
_A = at(4, 10, 58)
_g0 = {"mode": "gamelines", "path": BOARD, "stale": False, "due_at": "2026-11-03T20:00Z"}
_g1 = dict(_g0, stale=True, due_at="2026-11-04T11:00Z")
eq(F.last_looks([_g1], [_g0], _A, set())[0].get("looked_at"), "2026-11-04T10:58:00Z",
   "🔴 last_looks: a row stale now, inside contract at the first survey after the planned modes, its "
   "deadline after it, not built by the catch-up: judged against that survey")
eq(F.last_looks([_g1], [_g0], _A, {"gamelines"})[0].get("looked_at"), None, "🔴 ...not when the catch-up ran its mode")
eq(F.last_looks([_g1], [dict(_g0, stale=True)], _A, set())[0].get("looked_at"), None,
   "🔴 ...nor when it was already stale at that survey")
eq(F.last_looks([dict(_g1, due_at="2026-11-04T10:00Z")], [_g0], _A, set())[0].get("looked_at"), None,
   "🔴 ...nor when its deadline came before that survey")
_same = [_g1]
ck(F.last_looks(_same, _same, _A, set()) is _same, "...and a pass with no catch-up changes nothing")

# ══════════════════════════════════════════════════════════════════════
section("7. 🔴🔴 A DATED PATH THAT ROLLS AT ITS OWN DEADLINE IS CAUGHT UP (THE MLB CARD, RESULTS)")
# ══════════════════════════════════════════════════════════════════════
# (a) The card is picks/<the card deadline's date>.json: at 13:58Z on 11-04 that is 11-03's file,
# built 11-03 14:10Z and inside contract, so the card is not planned. At 14:05Z the row is picks/
# 2026-11-04.json, which does not exist yet: MISSING, though the plan never saw it owed.
TC0, TC1 = at(4, 13, 58), at(4, 14, 5)
d = sandbox(dict(ODDS_1104, **{"picks/2026-11-03.json": at(3, 14, 10)}))
_c0 = [r for r in F.survey(data=d + "/data", picks=d + "/picks", now=TC0) if r["mode"] == "card"]
ck(_c0 and not _c0[0]["stale"] and _c0[0]["path"].endswith("2026-11-03.json"),
   "at 13:58Z the card row is 11-03's file, inside contract", _c0)
clock, log = [TC0], []
code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=TC1, writes={"card": "picks/2026-11-04.json"}))
eq(ran(log, "card"), [TC1], "🔴🔴 the card is built once, at 14:05Z, by the catch-up")
ck(not written(d, "picks/2026-11-04.json")["stale"], "...freshness.json has today's card inside contract",
   written(d, "picks/2026-11-04.json"))
ck("card" not in hard_modes(d, TC1), "🔴🔴 ...and the gate has no 'card MISSED its 10:00 build' to fail", hard_modes(d, TC1))
shutil.rmtree(d, ignore_errors=True)
# (b) results is data/<slate date>/results/final.json.gz: the same roll at 10:00Z, its mode not run.
d = sandbox({"data/2026-11-03/results/final.json.gz": at(3, 10, 10)})
_r0 = [r for r in F.survey(data=d + "/data", picks=d + "/picks", now=T0) if r["mode"] == "results"]
ck(_r0 and not _r0[0]["stale"], "at 09:58Z the results row (11-03's file) is inside contract", _r0)
clock, log = [T0], []
code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=LATE, writes={"results": "DATED"}))
eq(ran(log, "results"), [LATE], "🔴🔴 results, whose path rolled at 10:00Z, is built once by the catch-up")
ck("results" not in hard_modes(d, LATE), "...and the gate has nothing to fail it on", hard_modes(d, LATE))
shutil.rmtree(d, ignore_errors=True)
# (c) results RAN before the roll: owed at 09:56Z (no 11-03 file), it writes 11-03's file, and the
# pass runs past 10:00Z. Its row is now 11-04's file, missing: the path rolled, so it is owed although
# results ran this pass, and record (CASCADE) follows it, in that order.
TR0 = at(4, 9, 56)
d = sandbox({})
clock, log = [TR0], []


def _late_after_results(m):
    if m == "results" and clock[0] == TR0:
        clock[0] = LATE


code, out, surveys = converge(d, clock, stub(d, log, clock, writes={"results": "DATED"},
                                               after_each=_late_after_results))
eq(ran(log, "results"), [TR0, LATE], "🔴🔴 results runs at 09:56Z, then again at 10:05Z for the rolled path")
eq(caught(out), [["results", "record"]], "🔴 ...in one catch-up round, record following it (CASCADE)")
eq([m for m, _t in log][-2:], ["results", "record"], "🔴 ...in the contract's order: results, then record")
ck(not written(d, "data/2026-11-04/results/final.json.gz")["stale"],
   "...freshness.json has 11-04's results inside contract", written(d, "data/2026-11-04/results/final.json.gz"))
ck("results" not in hard_modes(d, LATE), "🔴🔴 ...and the gate has no 'results MISSED' to fail", hard_modes(d, LATE))
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("8. 🔴 A SOFT MODE THAT FAILED IS NOT RETRIED EITHER")
# ══════════════════════════════════════════════════════════════════════
# news (SOFT) built 12:00Z missed 13:05Z, so the plan at 19:02Z has it; it fails (a soft failure).
# At 19:10Z its row reads "due 19:05Z", after the plan's survey.
TN0, TN1 = at(4, 19, 2), at(4, 19, 10)
d = sandbox(dict(ODDS_1104, **{NEWS: at(4, 12, 0)}))
clock, log = [TN0], []
code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=TN1, fails={"news"}))
eq(len(ran(log, "news")), 1, "🔴 the failed news runs once, never again in the catch-up")
ck("news" not in caught_all(out), "...no catch-up line names it", shown(catch_up_line(out)))
ck(written(d, NEWS)["stale"], "...and it is still late in freshness.json", written(d, NEWS))
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("9. 🔴 A CAUGHT-UP MODE THAT WROTE NOTHING NEW IS NOT CAUGHT UP AGAIN FOR THE SAME DEADLINE")
# ══════════════════════════════════════════════════════════════════════
# hitters is caught up at 10:05Z, runs without raising, and leaves its file as it was: the next
# round asks from THAT round's survey, so the same 10:00Z deadline does not bring it back.
d = sandbox({HIT: T0 - mins(8)})
clock, log = [T0], []
code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=LATE))
eq(len(ran(log, "hitters")), 1, "🔴 hitters runs once in the catch-up, not once a round")
eq(len(catch_up_line(out)), 1, "...one CATCH-UP line")
ck(written(d, HIT)["stale"], "...and the row it left late is the gate's", written(d, HIT))
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("10. 🔴🔴 A FREE ROW BUILT FROM A DEADLINE'S PAID PULL WAITS FOR THE PASS THAT BUYS IT")
# ══════════════════════════════════════════════════════════════════════
# The game model and winners.json read the board; the props board joins the props snapshots. All
# share the 20:00Z deadline with the paid pulls. Pass 1 plans at 19:58Z (news is owed) and runs past
# 20:00Z: it must not build the game model from the 11:04Z board and stamp it fresh, or pass 2,
# which buys the new board, would never rebuild it (review, 11-11).
P0, P1, P2 = at(4, 19, 58), at(4, 20, 5), at(4, 20, 12)
_odds = {BOARD: at(4, 11, 4), PROPS: at(4, 11, 5), GM: at(4, 19, 50), NEWS: at(4, 12, 0),
         "data/2026-11-04/props-pitcher/1104.json.gz": at(4, 11, 4),
         "data/2026-11-04/props-batter/1104.json.gz": at(4, 11, 4)}
d = sandbox(_odds)
clock, log = [P0], []
code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=P1, writes={"game-model": GM, "props-board": PROPS}))
eq(ran(log, "game-model"), [], "🔴🔴 pass 1 does not build the game model before its odds pull")
ck(not [m for m in caught_all(out) if m in ("game-model", "props-board")],
   "...no catch-up line names it or the props board", shown(catch_up_line(out)))
ck(written(d, GM)["stale"], "...so freshness.json still has it owed, for the pass that buys the pull", written(d, GM))
clock, log2 = [P2], []
code, out2, surveys = converge(d, clock, stub(d, log2, clock, writes={
    "gamelines": BOARD, "props-pitcher": "data/2026-11-04/props-pitcher/2012.json.gz",
    "props-batter": "data/2026-11-04/props-batter/2012.json.gz", "props-board": PROPS, "game-model": GM}))
_order = [m for m, _t in log2]
ck("gamelines" in _order and "game-model" in _order and _order.index("game-model") > _order.index("gamelines"),
   "🔴🔴 pass 2 buys the board, then builds the game model from it", _order)
ck(not written(d, GM)["stale"], "...and the game model is inside contract after it", written(d, GM))
shutil.rmtree(d, ignore_errors=True)
# ══════════════════════════════════════════════════════════════════════
section("11. 🔴🔴 A LONGER PASS COSTS A ROW IT DID NOT BUILD NOTHING OF THE 10-19 RULE")
# ══════════════════════════════════════════════════════════════════════
# The board and game model are inside contract until 11:00Z. The pass plans at 09:58Z, its planned
# modes end at 10:58Z (past 10:00Z), and the catch-up of hitters runs to 11:03Z (past 11:00Z). Before
# the catch-up existed, freshness.json was written at 10:58Z with the board inside contract, so the
# gate excused it ("passed after the last survey"); written at 11:03Z it would read stale and turn
# the run red. last_looks keeps the 10:58Z verdict for rows the catch-up did not build.
_y = at(3, 20, 10)
d = sandbox({BOARD: _y, PROPS: _y, GM: _y, HIT: T0 - mins(8)})
clock, log = [T0], []


def _to_1103(m):
    if m == "hitters":
        clock[0] = at(4, 11, 3)


code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=at(4, 10, 58), writes={"hitters": HIT},
                                               after_each=_to_1103))
eq(ran(log, "hitters"), [at(4, 10, 58)], "hitters is caught up at 10:58Z")
eq((written(d, BOARD).get("looked_at"), written(d, BOARD).get("stale_then")), ("2026-11-04T10:58:00Z", False),
   "🔴🔴 freshness.json keeps the board's 10:58Z verdict: inside contract")
_h = hard_modes(d, at(4, 11, 4))
ck("gamelines" not in _h and "game-model" not in _h,
   "🔴🔴 ...so the gate at 11:04Z excuses the board and the held game model, as it did before the "
   "catch-up existed: their 11:00Z deadline passed after that survey", _h)
ck(not written(d, HIT)["stale"] and "looked_at" not in written(d, HIT), "...and hitters, built, is simply inside contract",
   written(d, HIT))
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("12. 🔴🔴 THE MLB CARD WAITS FOR A PULL STILL OWED FROM AN EARLIER DEADLINE")
# ══════════════════════════════════════════════════════════════════════
# 13:58Z, 11-04: the 11:00Z batter pull is still owed (no 11-04 snapshot). The pass plans it, it fails,
# and the pass runs past 14:00Z. The card (picks/2026-11-04.json now) must not be built from
# yesterday's batter prices and stamped fresh: no odds pull rebuilds the card, so it would stay so all
# day. It waits; the next pass buys the pull and builds the card after it (review, 11-11).
_odds = {k: v for k, v in ODDS_1104.items() if "props-batter" not in k}
d = sandbox(dict(_odds, **{"picks/2026-11-03.json": at(3, 14, 10),
                           "data/2026-11-03/props-batter/2005.json.gz": at(3, 20, 5)}))
clock, log = [TC0], []
code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=TC1, fails={"props-batter"},
                                               writes={"card": "picks/2026-11-04.json"}))
eq(ran(log, "card"), [], "🔴🔴 pass 1 does not build the card while 11:00Z's batter pull is owed")
ck("card" not in caught_all(out), "...no catch-up line names it", shown(catch_up_line(out)))
clock, log2 = [at(4, 14, 20)], []
code, out2, surveys = converge(d, clock, stub(d, log2, clock, writes={
    "props-batter": "data/2026-11-04/props-batter/1420.json.gz", "props-board": PROPS, "card": "picks/2026-11-04.json"}))
_order = [m for m, _t in log2]
ck("props-batter" in _order and "card" in _order and _order.index("card") > _order.index("props-batter"),
   "🔴🔴 pass 2 buys the batter pull, then builds the card from it", _order)
ck(not written(d, "picks/2026-11-04.json")["stale"], "...and the card is inside contract after it",
   written(d, "picks/2026-11-04.json"))
shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("13. 🔴 A ROW THE CATCH-UP RAN AND LEFT STALE STAYS STRICT")
# ══════════════════════════════════════════════════════════════════════
# 13:00Z, the day's pulls in place. News falls due at 13:05Z during the planned modes; its catch-up
# runs to 14:05Z, past lineups' 14:00Z; round 2 catches lineups up, and its stub writes nothing. That
# row was built by the catch-up, so it gets no last look: the gate judges it as it stands.
d = sandbox(dict(ODDS_1104, **{NEWS: at(4, 12, 0), "data/latest/lineups.json.gz": at(3, 14, 10)}))
clock, log = [at(4, 13, 0)], []


def _to_1405(m):
    if m == "news" and clock[0] == at(4, 13, 10):
        clock[0] = at(4, 14, 5)


code, out, surveys = converge(d, clock, stub(d, log, clock, first_to=at(4, 13, 10), writes={"news": NEWS},
                                               after_each=_to_1405))
ck(len(caught(out)) == 2 and "news" in caught(out)[0] and "lineups" in caught(out)[1],
   "news is caught up in round 1, lineups in round 2", shown(catch_up_line(out)))
ck(written(d, "data/latest/lineups.json.gz")["stale"] and "looked_at" not in written(d, "data/latest/lineups.json.gz"),
   "🔴 ...and lineups, which the catch-up ran and left stale, carries no last look", written(d, "data/latest/lineups.json.gz"))
shutil.rmtree(d, ignore_errors=True)
note("CATCH_UP_ROUNDS = %d" % _C.CATCH_UP_ROUNDS)
