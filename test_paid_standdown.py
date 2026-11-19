#!/usr/bin/env python3
"""
ONE DEADLINE, ONE BUY: A LATE CRON DOES NOT BUY AGAIN WHAT ITS DEADLINE ALREADY HAS.

🔴🔴 `[2026-11-19]` Since 09-21 GitHub starts scheduled runs 6-10 hours late.
`freshness.stand_down` answered None for every mode outside STAND_DOWN (the
free metered list), so a late football `gamelines` cron (`2 11`, `4 19`,
`7 12`, `6 18`) bought again a deadline another pass had already bought and
landed on main: 19 such re-buys, 194 credits, 11-12 -> 11-19, counted from
the stored snapshots.

✅ A mode with a PAID contract row now stands down exactly as a metered one
does, by the same `served()` / SERVES_MIN rule: every row it builds is inside
contract and was built for the deadline this cron fires for.
⛔ A pull the contract owes is still bought; a hand run and `converge-off`
buy as before; a mode with no row (`halftime-probe`, `live-probe`) runs as
named.

🔴 THE CLASS, NOT FOUR CRONS: every (cron, league, mode) route in collect.yml
(`wfroutes.parse_routes`) whose mode has a PAID row in that league's contract.
A future paid cron is covered the day it is routed, whatever its league.

⛔ DRIVEN, NEVER THE LIVE TREE: the real `converge` in a planted tree, at a
pinned minute its clocks all read, the cron given by a planted GitHub event
file, `odds_get` stubbed and counted, every free mode recorded and not run,
and the HTTP primitive made to raise. No key is read; nothing is spent.
"""
import contextlib
import datetime
import gzip
import importlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from tcheck import ck, eq, note, section, shown  # noqa: E402

import freshness as F  # noqa: E402
import runs_report as RR  # noqa: E402
import wfroutes  # noqa: E402

UTC = datetime.timezone.utc
MIN = datetime.timedelta(minutes=1)
WF = open(os.path.join(ROOT, ".github", "workflows", "collect.yml"), encoding="utf-8").read()
# ⚠️ A PINNED IN-SEASON SATURDAY. Every daily cron fires on it; nothing reads today.
DAY_END = datetime.datetime(2026, 11, 14, 23, 59, tzinfo=UTC)
_TMP = tempfile.mkdtemp(prefix="paidstand-")


def _data(lg):
    return "data" if lg == "mlb" else "data/%s" % lg


@contextlib.contextmanager
def inside(d):
    cwd = os.getcwd()
    os.chdir(d)
    try:
        yield
    finally:
        os.chdir(cwd)


def contract_rows(lg, now, board=True):
    """The league's contract at `now`, asked in a tree that holds nothing but
    (`board`) a football props board, so the card rows a board brings are in
    it. Nothing from the repo's own data/ reaches it, and with no schedule
    stored every props row stays ("cannot tell" keeps it governed)."""
    d = tempfile.mkdtemp(prefix="empty-", dir=_TMP)
    try:
        if board and lg != "mlb":
            _write(os.path.join(d, _data(lg), "latest", "props.json.gz"), {})
        with inside(d):
            return F.contract(_data(lg), "picks", now)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def event(cron, name="schedule"):
    """A GitHub event file for a run `cron` started -> its env."""
    p = os.path.join(_TMP, "event-%d.json" % len(os.listdir(_TMP)))
    with open(p, "w", encoding="utf-8") as fh:
        json.dump({"schedule": cron}, fh)
    return {"GITHUB_EVENT_NAME": name, "GITHUB_EVENT_PATH": p}


def _write(full, doc):
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if full.endswith(".gz"):
        with gzip.open(full, "wt", encoding="utf-8") as fh:
            json.dump(doc, fh)
    else:
        with open(full, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)


def put(d, kind, path, at, paid, kickoff=None):
    """One artifact built at `at`: a file stamped `at`, or a snapshot named
    for `at` in its own UTC day's directory (a paid one with a real bill).
    A football schedule holds one FBS game at `kickoff`, so the props rows are
    warranted the way a real slate makes them (`_props_warranted`)."""
    stamp = at.strftime("%Y-%m-%dT%H:%M:%SZ")
    doc = {"built_at": stamp, "written_at": stamp, "pulled_at": stamp}
    if kickoff is not None and re.search(r"/latest/schedule-\d{4}\.json\.gz$", path):
        doc["games"] = [{"id": 1, "start": kickoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
                         "home": "Home", "away": "Away", "home_class": "fbs",
                         "away_class": "fbs"}]
    if kind == "dir":
        path = re.sub(r"\d{4}-\d{2}-\d{2}", at.strftime("%Y-%m-%d"), path, count=1)
        full = os.path.join(d, path, at.strftime("%H%M") + ".json.gz")
        if paid:
            doc.update(credits_used=12, credits_remaining=19000)
    else:
        full = os.path.join(d, path)
    _write(full, doc)


def plant(lg, now, mode, built):
    """A tree where every row of `lg`'s contract was built just after its
    deadline in force at `now`, except `mode`'s rows, built at `built`
    (None: never). -> its directory."""
    d = tempfile.mkdtemp(prefix="tree-", dir=_TMP)
    for m, (kind, path), times, paid, _why in contract_rows(lg, now):
        due = F.last_due(times, now)
        at = built if m == mode else (min(due + MIN, now) if due else now - MIN)
        if at is not None:
            put(d, kind, path, at, paid, kickoff=now + datetime.timedelta(hours=2))
    os.makedirs(os.path.join(d, "picks"), exist_ok=True)
    return d


def _at_now(fn, now):
    def call(*a, **k):
        if len(a) < 3 and k.get("now") is None:
            k["now"] = now
        return fn(*a, **k)
    return call


def converge(d, lg, now, env, mode, argv=None, real=True):
    """The real collect.py in `d` at `now`, `mode` named the way its cron names
    it (or `argv` through main()). Only `mode` is run for real (`real`); every
    other mode is recorded. -> (modes run, odds_get calls, stdout)."""
    keys = ("GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH", "LEAGUE", "ODDS_API_KEY",
            "CFBD_API_KEY")
    saved_env = {k: os.environ.get(k) for k in keys}
    saved_glf = sys.modules.get("game_lines_fb")
    ran, calls = [], []
    for k in keys:
        os.environ.pop(k, None)
    os.environ["LEAGUE"] = lg
    for k, v in env.items():
        os.environ[k] = v
    fresh = F                               # collect's `_fresh` is this module
    saved_fresh = fresh.plan, fresh.survey, fresh.record_builds
    try:
        with inside(d):
            import collect
            importlib.reload(collect)
            assert collect._fresh is F
            real_run = collect.run_mode

            def run_mode(m):
                ran.append(m)
                if m == mode and real:
                    real_run(m)

            def odds_get(path, params):
                calls.append(path)
                return [], 0, 19000

            def no_http(*a, **k):
                raise AssertionError("a test reached the network: %r" % (a,))
            collect.run_mode, collect.odds_get, collect.get = run_mode, odds_get, no_http
            collect.ODDS_KEY = "planted-in-a-test-never-sent"   # run_mode's gate only
            collect.daily_spend = lambda *a, **k: 0
            collect._ensure_cfb_team_directory = lambda *a, **k: None
            # after the buy, not the buy: the join, the alt-line top-up, the card
            collect.collect_props_board_fb = lambda *a, **k: None
            collect.collect_alt_lines = lambda *a, **k: None
            collect.build_card_fb = lambda *a, **k: None
            sys.modules["game_lines_fb"] = types.SimpleNamespace(build=lambda *a, **k: None)
            collect.now = lambda: now
            fresh.plan, fresh.survey, fresh.record_builds = (
                _at_now(f, now) for f in saved_fresh)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                if argv is None:
                    collect.converge(explicit=[mode])
                else:
                    saved_argv = sys.argv
                    sys.argv = ["collect.py"] + list(argv)
                    try:
                        collect.main()
                    except SystemExit:
                        pass
                    finally:
                        sys.argv = saved_argv
        return ran, calls, out.getvalue()
    finally:
        fresh.plan, fresh.survey, fresh.record_builds = saved_fresh
        if saved_glf is None:
            sys.modules.pop("game_lines_fb", None)
        else:
            sys.modules["game_lines_fb"] = saved_glf
        for k in keys:
            os.environ.pop(k, None)
            if saved_env[k] is not None:
                os.environ[k] = saved_env[k]


def rows_of(d, lg, now, mode):
    with inside(d):
        rs = [r for r in F.survey(data=_data(lg), picks="picks", now=now) if r["mode"] == mode]
        planned, _ = F.plan(data=_data(lg), picks="picks", now=now)
    return rs, planned


# ══════════════════════════════════════════════════════════════════════
section("1. THE CLASS: EVERY ROUTED CRON THAT NAMES A PAID MODE, DERIVED")
# ══════════════════════════════════════════════════════════════════════
ROUTES = wfroutes.parse_routes(WF)
CASES = []
for cron, lg, ms in ROUTES:
    fire = F.cron_last_fire(cron, DAY_END)
    if fire is None or not F.has_contract(lg):
        continue
    paid = {m: t for m, _p, t, p, _w in contract_rows(lg, fire) if p}
    for m in ms.split():
        if m in paid:
            CASES.append((cron, lg, m, paid[m], fire))
ck("⚠️ the paid routes were DERIVED (rule 67: never an empty class)", len(CASES) >= 8,
   "%d: %s" % (len(CASES), sorted((c, lg, m) for c, lg, m, _t, _f in CASES)))
ck("⚠️ ...and hold the gamelines and props crons of both football leagues",
   {(lg, m) for _c, lg, m, _t, _f in CASES}
   >= {("ncaaf", "gamelines"), ("nfl", "gamelines"), ("ncaaf", "props-player"),
       ("nfl", "props-player")}, sorted({(lg, m) for _c, lg, m, _t, _f in CASES}))
for cron, lg, m, times, fire in CASES:
    due = F.last_due(times, fire)
    note("%-5s %-12s %-12s fires %s, %d min after its %s deadline (SERVES_MIN %d)" % (
        lg, m, cron, fire.strftime("%H:%MZ"), (fire - due).total_seconds() // 60,
        due.strftime("%H:%MZ"), F.SERVES_MIN))
note("MLB arms in the routing table: %d (MLB's crons fall through to `converge`, naming "
     "no mode, so no MLB run asks a stand-down; an MLB arm that named a paid mode would "
     "join the class above)" % sum(1 for _c, lg, _m in ROUTES if lg == "mlb"))


# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 A LATE CRON WHOSE DEADLINE IS ALREADY BOUGHT BUYS NOTHING")
# ══════════════════════════════════════════════════════════════════════
for cron, lg, m, times, fire in CASES:
    due = F.last_due(times, fire)
    nxt = F.next_due(times, fire)
    late = min(fire + datetime.timedelta(hours=4), nxt - MIN)   # its deadline still in force
    tag = "%s %s `%s`" % (lg, m, cron)
    # 🔴 THE DEFECT: an earlier pass bought it 3 minutes after the deadline.
    d = plant(lg, late, m, due + 3 * MIN)
    try:
        rs, planned = rows_of(d, lg, late, m)
        ck("   (%s: the planted %s rows are inside contract and the contract alone "
           "plans no %s)" % (tag, m, m),
           rs and not any(r["stale"] for r in rs) and m not in planned,
           "⛔ otherwise the case is vacuous: %s planned=%s" % (
               [(r["path"], r["age_min"], r["due_at"]) for r in rs], planned))
        ran, calls, out = converge(d, lg, late, event(cron), m)
        # @vacuity 🔴🔴 a mode with a paid row stands down like a metered one
        #   file: freshness.py
        #   find:     if mode not in STAND_DOWN and not any(r.get("paid") for r in mine):
        #   with:     if mode not in STAND_DOWN:
        # @vacuity 🔴 a pull after the deadline, before the cron's own minute, did its work
        #   file: freshness.py
        #   find: SERVES_MIN = 30
        #   with: SERVES_MIN = 0
        ck("🔴🔴 %s, started %s late (%s), bought for its %s deadline at %s: NO buy" % (
            tag, str(late - fire)[:-3], late.strftime("%H:%MZ"), due.strftime("%H:%MZ"),
            (due + 3 * MIN).strftime("%H:%MZ")),
           not calls and m not in ran,
           "⛔ THE DEFECT: odds_get calls %s, ran %s" % (calls, ran))
        ck("✅ ...and the log says why, naming the cron's minute",
           re.search(r"STAND DOWN: %s — .*%s.*NOTHING SPENT" % (
               re.escape(m), fire.strftime("%Y-%m-%d %H:%MZ")), out), shown(out[-300:]))
        # ⛔ A HAND RUN (no cron) AND `converge-off` BUY AS BEFORE.
        ran, _c, out = converge(d, lg, late, {}, m)
        ck("⛔ %s: the same tree, run by hand (no cron), still runs %s" % (tag, m), m in ran,
           "ran=%s" % ran)
        ran, _c, out = converge(d, lg, late, event(cron), m, argv=[m, "converge-off"])
        ck("⛔ %s: `%s converge-off` still runs it" % (tag, m), m in ran, "ran=%s" % ran)
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # ⛔ A PULL THE CONTRACT OWES IS BOUGHT: built a minute BEFORE the deadline.
    d = plant(lg, late, m, due - MIN)
    try:
        ran, calls, out = converge(d, lg, late, event(cron), m)
        ck("⛔ %s: the last pull was a minute before the %s deadline, so the contract "
           "owes one: exactly one buy" % (tag, due.strftime("%H:%MZ")),
           len(calls) == 1 and ran.count(m) == 1,
           "odds_get calls %s, ran %s" % (calls, ran))
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # 🔴 OVERTAKEN: the cron started after the NEXT deadline, which a pass
    #    already bought. Built after this cron's own minute -> nothing owed.
    over = nxt + 20 * MIN
    d = plant(lg, over, m, nxt + 4 * MIN)
    try:
        ran, calls, out = converge(d, lg, over, event(cron), m)
        ck("🔴 %s, started after the next (%s) deadline, already bought at %s: no buy" % (
            tag, nxt.strftime("%a %H:%MZ"), (nxt + 4 * MIN).strftime("%H:%MZ")),
           not calls and m not in ran, "odds_get calls %s, ran %s" % (calls, ran))
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("3. ⛔ A MODE WITH NO CONTRACT ROW RUNS AS ITS CRON NAMED IT")
# ══════════════════════════════════════════════════════════════════════
_seen = set()
for cron, lg, ms in ROUTES:
    fire = F.cron_last_fire(cron, DAY_END)
    if fire is None or not F.has_contract(lg):
        continue
    have = {r[0] for r in contract_rows(lg, fire)}
    for m in ms.split():
        if m in have or (lg, m) in _seen:
            continue
        _seen.add((lg, m))
        late = fire + datetime.timedelta(hours=4)
        d = plant(lg, late, m, None)
        try:
            ran, _c, _o = converge(d, lg, late, event(cron), m, real=False)
            ck("⛔ %s %s (`%s`, no row): still run as its cron named it" % (lg, m, cron),
               m in ran, "ran=%s" % ran)
        finally:
            shutil.rmtree(d, ignore_errors=True)
ck("⚠️ the modes with no row were derived too (halftime-probe, live-probe)",
   {m for _lg, m in _seen} >= {"halftime-probe", "live-probe"}, sorted(_seen))


# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE SAFETY PROPERTY, EVERY LEAGUE (MLB TOO), EVERY CRON collect.yml DECLARES")
# ══════════════════════════════════════════════════════════════════════
# For every league's PAID rows, at minutes across three days, with the pull made
# never / a minute before / a minute after the deadline in force / at that
# minute, and asked as if EACH declared cron had started the run:
# ⛔ `stand_down` may answer only when every row of the mode has a pull at or
#    after its deadline in force, i.e. that exact deadline's pull has landed.
# ⚠️ MLB's props rows are the STORAGE DIRECTORY (the us2 backup and the us,us2
#    primary write to one), the same rows `pull_owed` judges.
CRONS = sorted(set(RR.declared_crons(ROOT)["collect"]["crons"]))
ck("⚠️ the crons were read from collect.yml (never a hand list)", len(CRONS) >= 40, len(CRONS))
ENVS = {c: event(c) for c in CRONS}
answered = owed = broke = 0
bad = []
START = datetime.datetime(2026, 11, 12, 0, 7, tzinfo=UTC)
for lg in ("mlb", "nfl", "ncaaf"):
    box = tempfile.mkdtemp(prefix="prop-%s-" % lg, dir=_TMP)
    for step in range(0, 3 * 24 * 60, 313):
        now = START + datetime.timedelta(minutes=step)
        rows_c = [r for r in contract_rows(lg, now) if r[3]]
        for m in sorted({r[0] for r in rows_c}):
            mine = [r for r in rows_c if r[0] == m]
            due = F.last_due(mine[0][2], now)
            for built in (None, due - MIN, due + MIN, now):
                shutil.rmtree(os.path.join(box, "data"), ignore_errors=True)
                for _m, (kind, path), _t, paid, _w in mine:
                    if built is not None:
                        put(box, kind, path, built, paid)
                with inside(box):
                    rows = F.survey(data=_data(lg), picks="picks", now=now)
                landed = built is not None and all(
                    built >= F.last_due(t, now) for _m, _p, t, _pd, _w in mine)
                owed += not landed
                for c in CRONS:
                    if F.stand_down(rows, m, now, ENVS[c]) is not None:
                        answered += 1
                        if not landed:
                            broke += 1
                            if len(bad) < 5:
                                bad.append((lg, m, c, now.isoformat(), built and built.isoformat()))
    shutil.rmtree(box, ignore_errors=True)
ck("⚠️ the property was asked of owed pulls too (else it asks nothing)", owed > 100, owed)
# @vacuity 🔴🔴 a row the contract owes is never stood down, whatever the cron
#   file: freshness.py
#   find:     if since is None or not mine or any(r["stale"] or r["missing"] for r in mine):
#   with:     if since is None or not mine:
ck("✅ a paid pull whose deadline already has one is stood down for some cron", answered > 0,
   "⛔ on the code before 11-19 every paid mode answered None: %d" % answered)
eq(broke, 0, "🔴🔴 NEVER a stand-down without that deadline's pull: %d of %d answers%s" % (
    broke, answered, (" e.g. %s" % bad) if bad else ""))

shutil.rmtree(_TMP, ignore_errors=True)

note("💰 WHAT IT SAVES, MEASURED 11-12 -> 11-19 from the stored snapshots: 19 late "
     "re-buys of a football gamelines deadline already on main, 194 credits (~28 a "
     "day). Two runs RACING one deadline (7 buys, 449 credits) are not stopped here: "
     "neither could see the other's pull (watchdog `double-buy:*` names them).")
