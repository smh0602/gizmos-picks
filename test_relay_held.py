#!/usr/bin/env python3
"""
A HELD FOOTBALL CRON SPENDS NOTHING AND BUILDS NOTHING THE RELAY LINK OWNS.

🔴 `[Sam, 2026-11-18]` Asked "Turn the relay on for football?", Sam: "Yes". One
link, `collect [relay ncaaf nfl]`, converges both leagues every 15-35 minutes
(relay.py). GitHub starts the football crons 6-10 hours late (since 09-21), so a
late cron and the link would build, and BUY, the same deadline: on 11-14 college
props were bought 3 times for one deadline, 158 credits each.
✅ A SCHEDULED football run is HELD while a link other than itself is listed
live AND every league it routes has a beat under relay.HELD_BEAT_MIN minutes
old (`relay.py held`, the workflow's held step -> RELAY_HELD=yes). A held pass
(`freshness.relay_holds`) builds nothing the contract owes, paid, metered or
free; writes neither freshness.json nor lateness.json; and runs only its
EXTRAS (`freshness.extras`): a mode with no row (the live and halftime probes)
and a metered mode's extra build no deadline covers (the game-day fb-scores
refreshes, the Sunday cfb-probe rebuild), exactly as today. Its league's gate
is the link's, which runs it on every pass.
⛔ A hand run is never held, nor a run whose beat is over an hour old (a hung
link), nor one whose run list cannot be read.

🔴 THE CLASS, DERIVED: every football arm in collect.yml's routing table
(`wfroutes.parse_arms`), each league it names, the modes it names, against
that league's real contract. ⛔ DRIVEN, NEVER THE LIVE TREE: the real
`converge` in planted trees at pinned minutes, the cron given by a planted
GitHub event file, `odds_get` and the HTTP primitive stubbed and counted, the
real Converge and held step bodies with stub `python` / `gh` / `git`.

# @vacuity 🔴🔴 a held pass is held
#   file: freshness.py
#   find:     return env.get("RELAY_HELD") == "yes" and lg in FB_TIMES and fired_cron(env) is not None
#   with:     return False
#
# @vacuity 🔴 ...only when a cron started the run (a hand run is never held)
#   file: freshness.py
#   find:     return env.get("RELAY_HELD") == "yes" and lg in FB_TIMES and fired_cron(env) is not None
#   with:     return env.get("RELAY_HELD") == "yes" and lg in FB_TIMES
#
# @vacuity 🔴 a held pass appends none of its cron's owed modes
#   file: collect.py
#   find:     for m in (() if held else explicit):
#   with:     for m in explicit:
#
# @vacuity 🔴 a held pass writes no freshness.json
#   file: collect.py
#   find:     if held:                            # the link writes freshness.json and lateness.json
#   with:     if False:
#
# @vacuity 🔴 ...and no lateness.json when it has nothing to run
#   file: collect.py
#   find:         if not held:                    # a held run leaves lateness.json to the link
#   with:         if True:
#
# @vacuity 🔴 a mode with no row still runs as its cron named it
#   file: freshness.py
#   find:         if m not in have:
#   with:         if False:
#
# @vacuity 🔴 a metered mode's extra build (no deadline covers it) still runs
#   file: freshness.py
#   find:         if stand_down(rows, m, now, env) is not None:
#   with:         if True:
#
# @vacuity 🔴 ...but never one with an owed row: that row is the link's
#   file: freshness.py
#   find:         if not own or any(owes(r) for r in own):
#   with:         if not own:
#
# @vacuity 🔴 the beat must be fresh: an old beat (a hung link) holds nothing
#   file: relay.py
#   find:         if ages[lg] is None or not 0 <= ages[lg] < HELD_BEAT_MIN:
#   with:         if ages[lg] is None:
#
# @vacuity 🔴 ...and a link must be live (a cron, MLB's link or a finished link is not one)
#   file: relay.py
#   find:     alive = links_of(runs, me, FOOTBALL)
#   with:     alive = [r for r in runs if str(r.get("databaseId")) != str(me)]
#
# @vacuity 🔴 the held league's gate is the link's
#   file: docs/upload/collect.yml
#   find:               if [ "$RELAY_HELD" = "yes" ] && [ "$GITHUB_EVENT_NAME" = "schedule" ]; then
#   with:               if false; then
#
# @vacuity ⛔ ...only for a run a cron started
#   file: docs/upload/collect.yml
#   find:               if [ "$RELAY_HELD" = "yes" ] && [ "$GITHUB_EVENT_NAME" = "schedule" ]; then
#   with:               if [ "$RELAY_HELD" = "yes" ]; then
#
# @vacuity 🔴 the held step asks relay.py and says yes only on its exit 0
#   file: docs/upload/collect.yml
#   find:             python relay.py held "$RUNS" --leagues "$LEAGUES" --run-id "${GITHUB_RUN_ID:-0}" && HELD=yes
#   with:             HELD=yes
#
# @vacuity ⛔ ...and a run list that cannot be read holds nothing
#   file: docs/upload/collect.yml
#   find:           HELD=no
#   with:           HELD=yes
"""
import contextlib
import datetime
import gzip
import importlib
import io
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from tcheck import ck, eq, note, section, shown  # noqa: E402

import freshness as F  # noqa: E402
import relay as R  # noqa: E402
import wfparse  # noqa: E402
import wfroutes  # noqa: E402

UTC = datetime.timezone.utc
MIN = datetime.timedelta(minutes=1)
WF = wfparse.effective_workflows(ROOT)["collect.yml"]
SRC = open(WF, encoding="utf-8").read()
DAY_END = datetime.datetime(2026, 11, 14, 23, 59, tzinfo=UTC)     # ⚠️ a pinned in-season Saturday
_TMP = tempfile.mkdtemp(prefix="relayheld-")
_EVENTS = itertools.count()
NOW = datetime.datetime.now(UTC)


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


def event(cron, name="schedule"):
    p = os.path.join(_TMP, "event-%d.json" % next(_EVENTS))
    with open(p, "w", encoding="utf-8") as fh:
        json.dump({"schedule": cron}, fh)
    return {"GITHUB_EVENT_NAME": name, "GITHUB_EVENT_PATH": p}


def contract_rows(lg, now):
    """`lg`'s contract at `now`, in a tree holding only a props board (so the card rows exist)."""
    d = tempfile.mkdtemp(prefix="empty-", dir=_TMP)
    try:
        _write(os.path.join(d, "data", lg, "latest", "props.json.gz"), {})
        with inside(d):
            return F.contract("data/%s" % lg, "picks", now)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def put(d, kind, path, at, paid):
    stamp = at.strftime("%Y-%m-%dT%H:%M:%SZ")
    doc = {"built_at": stamp, "written_at": stamp, "pulled_at": stamp}
    if re.search(r"/history/schedule-\d{4}\.json\.gz$", path):      # a healthy stored season
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


def tree(lg, now, built=None):
    """A planted tree for `lg` at `now`. `built` None: only a props board, so every row
    is owed. Else {mode: when its rows were built}, every other row built just after
    its deadline in force (inside contract)."""
    d = tempfile.mkdtemp(prefix="tree-", dir=_TMP)
    _write(os.path.join(d, "data", lg, "latest", "props.json.gz"), {})
    if built is not None:
        for m, (kind, path), times, paid, _w in contract_rows(lg, now):
            due = F.last_due(times, now)
            at = built.get(m) or (min(due + MIN, now) if due else now - MIN)
            put(d, kind, path, at, paid)
    os.makedirs(os.path.join(d, "picks"), exist_ok=True)
    # what a held pass must leave alone, byte for byte
    _write(os.path.join(d, "data", lg, "latest", "freshness.json"), {"planted": "freshness"})
    _write(os.path.join(d, "data", lg, "latest", F.LATENESS_FILE), {"planted": "lateness"})
    return d


def _at_now(fn, now):
    def call(*a, **k):
        if len(a) < 3 and k.get("now") is None:
            k["now"] = now
        return fn(*a, **k)
    return call


PAID_MODES = {"gamelines", "props-player", "alt-lines"}


def converge(d, lg, now, env, explicit):
    """The REAL collect.converge in `d` at `now`, `explicit` named as its cron names it.
    A paid mode is run for real (its buy is `odds_get`, stubbed and counted); every
    other mode is recorded and not run. -> (modes run, odds_get calls, HTTP calls, log,
    freshness.json + lateness.json bytes after)."""
    keys = ("GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH", "LEAGUE", "ODDS_API_KEY", "CFBD_API_KEY",
            "RELAY_HELD", "RELAY_LINK")
    saved_env = {k: os.environ.get(k) for k in keys}
    saved_glf = sys.modules.get("game_lines_fb")
    ran, calls, http = [], [], []
    for k in keys:
        os.environ.pop(k, None)
    os.environ["LEAGUE"] = lg
    os.environ.update(env)
    saved_fresh = F.plan, F.survey, F.record_builds
    try:
        with inside(d):
            import collect
            importlib.reload(collect)
            assert collect._fresh is F
            real_run = collect.run_mode

            def run_mode(m):
                ran.append(m)
                if m in PAID_MODES:
                    real_run(m)

            def odds_get(path, params):
                calls.append(path)
                return [], 0, 19000

            def no_http(*a, **k):
                http.append(a[:1])
                raise AssertionError("a test reached the network: %r" % (a,))
            collect.run_mode, collect.odds_get, collect.get = run_mode, odds_get, no_http
            collect.ODDS_KEY = "planted-in-a-test-never-sent"
            collect.daily_spend = lambda *a, **k: 0
            collect._ensure_cfb_team_directory = lambda *a, **k: None
            collect.collect_props_board_fb = lambda *a, **k: None
            collect.collect_alt_lines = lambda *a, **k: None
            collect.build_card_fb = lambda *a, **k: None
            sys.modules["game_lines_fb"] = types.SimpleNamespace(build=lambda *a, **k: None)
            collect.now = lambda: now
            F.plan, F.survey, F.record_builds = (_at_now(f, now) for f in saved_fresh)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                collect.converge(explicit=list(explicit))
            files = tuple(open(os.path.join("data", lg, "latest", n), "rb").read()
                          if os.path.exists(os.path.join("data", lg, "latest", n)) else None
                          for n in ("freshness.json", F.LATENESS_FILE))
        return ran, calls, http, out.getvalue(), files
    finally:
        F.plan, F.survey, F.record_builds = saved_fresh
        if saved_glf is None:
            sys.modules.pop("game_lines_fb", None)
        else:
            sys.modules["game_lines_fb"] = saved_glf
        for k in keys:
            os.environ.pop(k, None)
            if saved_env[k] is not None:
                os.environ[k] = saved_env[k]


PLANTED = (json.dumps({"planted": "freshness"}).encode(), json.dumps({"planted": "lateness"}).encode())

# ══════════════════════════════════════════════════════════════════════
section("1. THE CLASS: EVERY FOOTBALL ARM IN THE ROUTING TABLE, DERIVED")
# ══════════════════════════════════════════════════════════════════════
ARMS = [(c, lg, ms) for c, lg, ms in wfroutes.parse_arms(SRC) if set(lg.split()) & R.FOOTBALL_LEAGUES]
ck("⚠️ the football arms were DERIVED (rule 67: never an empty class)", len(ARMS) >= 30,
   "%d arms" % len(ARMS))
ck("⚠️ ...and hold paid, metered, free and row-less modes in both leagues",
   {m for _c, _lg, ms in ARMS for m in ms.split()}
   >= {"gamelines", "props-player", "card-fb", "news", "cfb-probe", "fb-scores", "nfl-logs",
       "live-probe", "halftime-probe"}, sorted({m for _c, _lg, ms in ARMS for m in ms.split()}))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 HELD, A LATE CRON BUYS NOTHING AND BUILDS NOTHING THE CONTRACT OWES")
# ══════════════════════════════════════════════════════════════════════
# Every row of the league is owed (only a props board is stored), so a run that is
# NOT held buys the odds and builds everything: that is the control, and it proves
# the stubs are reachable.
_held_bad, _ctl_bad, _hand_bad, _n = [], [], [], 0
for cron, lgs, ms in ARMS:
    fire = F.cron_last_fire(cron, DAY_END)
    if fire is None:
        continue
    late = fire + 3 * 60 * MIN
    for lg in lgs.split():
        _n += 1
        modes = ms.split()
        have = {r[0] for r in contract_rows(lg, late)}
        expect = [m for m in modes if m not in have]       # no row: its cron is its only reason
        d = tree(lg, late)
        try:
            ran, calls, http, out, files = converge(d, lg, late, dict(event(cron), RELAY_HELD="yes"), modes)
            if ran != expect or calls or http or files != PLANTED or "HELD:" not in out:
                _held_bad.append((cron, lg, ran, expect, len(calls), len(http), files == PLANTED))
            ran, calls, http, out, files = converge(d, lg, late, event(cron), modes)
            if not (set(modes) <= set(ran) and calls and files[0] != PLANTED[0]):
                _ctl_bad.append((cron, lg, ran, len(calls)))
            ran, calls, _h, out, _f = converge(d, lg, late, dict(event(cron, "workflow_dispatch"),
                                                                  RELAY_HELD="yes"), modes)
            if not (set(modes) <= set(ran) and calls):
                _hand_bad.append((cron, lg, ran, len(calls)))
        finally:
            shutil.rmtree(d, ignore_errors=True)
ck("🔴🔴 held, every football cron (%d cron x league) makes 0 odds_get calls and 0 HTTP calls, "
   "runs only the modes no contract row covers, and leaves freshness.json and lateness.json "
   "byte for byte" % _n, not _held_bad,
   "⛔ before 11-18 RELAY_HELD was ignored and the pass built and bought everything owed: %s"
   % _held_bad[:3])
ck("✅ control: the same tree NOT held buys the odds (odds_get reached), runs every mode its cron "
   "names and writes freshness.json, as today", not _ctl_bad, _ctl_bad[:3])
ck("⛔ RELAY_HELD=yes on a run no cron started (a hand run) is NOT held: it converges as before",
   not _hand_bad, _hand_bad[:3])

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE EXTRAS: WHAT NO DEADLINE COVERS STILL RUNS, AS TODAY")
# ══════════════════════════════════════════════════════════════════════


def held_run(lg, cron, now, built, modes, held="yes"):
    d = tree(lg, now, built)
    try:
        env = dict(event(cron), **({"RELAY_HELD": held} if held else {}))
        ran, calls, http, out, files = converge(d, lg, now, env, modes)
        return ran, calls, files
    finally:
        shutil.rmtree(d, ignore_errors=True)


_sat = datetime.datetime(2026, 11, 14, 18, 52, tzinfo=UTC)          # Saturday, 12 min after 18:40
for _lg in ("ncaaf", "nfl"):
    _ran, _calls, _files = held_run(_lg, "40 */2 * * 6", _sat, {"fb-scores": _sat.replace(hour=8, minute=5)},
                                    ["fb-scores"])
    eq((_ran, len(_calls), _files == PLANTED), (["fb-scores"], 0, True),
       "🔴 %s, held: Saturday's `40 */2 * * 6` scores refresh still runs (its row is inside contract, "
       "built 08:05Z, before this cron's 18:40Z minute: an extra build)" % _lg)
_lt = datetime.datetime(2026, 11, 14, 12, 0, tzinfo=UTC)            # `4 8` started 4 hours late
for _b, _why in ((_lt.replace(hour=8, minute=1), "built 08:01Z, after its 08:00Z deadline: done"),
                 (_lt.replace(hour=7, minute=58), "built 07:58Z, before its 08:00Z deadline: OWED, the link's")):
    _ran, _calls, _files = held_run("ncaaf", "4 8 * * *", _lt, {"fb-scores": _b}, ["fb-scores"])
    eq(_ran, [], "🔴 ncaaf, held: the daily `4 8 * * *` cron serves the scores deadline, so it does not "
       "run fb-scores (%s)" % _why)
_sun = datetime.datetime(2026, 11, 15, 17, 35, tzinfo=UTC)          # Sunday, `35 14` 3 hours late
_ran, _calls, _files = held_run("ncaaf", "35 14 * * 0", _sun,
                                {"cfb-probe": _sun.replace(hour=7, minute=5),
                                 "cfb-teams": _sun.replace(hour=7, minute=5)}, ["cfb-probe", "cfb-teams"])
eq(_ran, ["cfb-probe"], "🔴 ncaaf, held: the Sunday `35 14 * * 0` rebuild still re-sweeps cfb-probe (built "
   "07:05Z for its 07:00Z deadline: this cron is an extra), and leaves cfb-teams, whose 14:35Z deadline "
   "it serves and which is owed, to the link")
_ran, _calls, _files = held_run("ncaaf", "50 16 * * 6", _sat, {}, ["live-probe"])
eq(_ran, ["live-probe"], "🔴 held, the live probe (no contract row) still runs as its cron named it")
_ran, _calls, _files = held_run("nfl", "7 12 * * *", _lt, {"gamelines": _lt.replace(hour=11, minute=50)},
                                ["gamelines"])
eq((_ran, len(_calls)), ([], 0), "🔴 nfl, held: the late `7 12` odds cron, its 12:00Z deadline unbought, "
   "buys NOTHING: the link buys it (one deadline, one buy)")
_ran, _calls, _files = held_run("nfl", "7 12 * * *", _lt, {"gamelines": _lt.replace(hour=11, minute=50)},
                                ["gamelines"], held=None)
eq((_ran.count("gamelines"), len(_calls)), (1, 1), "✅ control: not held, the same cron buys it once, as today")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 relay.py held: A LIVE LINK AND A FRESH BEAT, NOTHING LESS")
# ══════════════════════════════════════════════════════════════════════


def held_cli(runs, beats, leagues="ncaaf nfl", me="500", raw=None):
    """`python relay.py held` in a tree pinned to NOW -> its exit code and line.
    `beats`: {league: minutes old}."""
    t = tempfile.mkdtemp(prefix="held-cli-", dir=_TMP)
    try:
        for lg, age in beats.items():
            _write(os.path.join(t, "data", lg, "latest", R.BEAT_FILE),
                   {"run_id": "1", "at": (NOW - age * MIN).strftime("%Y-%m-%dT%H:%M:%SZ")})
        rp = os.path.join(t, "runs.json")
        if raw is not None:
            open(rp, "w").write(raw)
        else:
            _write(rp, runs)
        p = subprocess.run([sys.executable, os.path.join(ROOT, "relay.py"), "held", rp, "--leagues", leagues,
                            "--run-id", me, "--data", os.path.join(t, "data")],
                           capture_output=True, text=True, timeout=120, env=dict(os.environ, PYTHONUTF8="1"))
        return p.returncode, (p.stdout + p.stderr).strip()
    finally:
        shutil.rmtree(t, ignore_errors=True)


def run(i, title, status="in_progress"):
    return {"databaseId": i, "status": status, "displayTitle": title,
            "createdAt": NOW.strftime("%Y-%m-%dT06:00:00Z")}


LINK = run(400, "collect [relay ncaaf nfl]")
FRESH = {"ncaaf": 10, "nfl": 10}
_rc, _o = held_cli([LINK], FRESH)
eq(_rc, 0, "🔴 a live football link and both beats 10 minutes old: HELD (exit 0)")
ck("   ...and it names the link", "400" in _o and "HELD" in _o, _o)
eq(held_cli([run(400, "collect [relay nfl ncaaf]", "queued")], FRESH)[0], 0,
   "   a QUEUED link (either league order) holds too: it is the successor about to pass")
eq(held_cli([LINK], {"ncaaf": R.HELD_BEAT_MIN + 10, "nfl": R.HELD_BEAT_MIN + 10})[0], 1,
   "🔴 beats %d minutes old (a hung link): NOT held (exit 1)" % (R.HELD_BEAT_MIN + 10))
eq(held_cli([LINK], {"ncaaf": 10, "nfl": R.HELD_BEAT_MIN + 10})[0], 1,
   "🔴 one league's beat old: a two-league run is NOT held")
eq(held_cli([LINK], {"ncaaf": R.HELD_BEAT_MIN + 10, "nfl": 10}, leagues="nfl")[0], 0,
   "   ...a run routed for the NFL alone asks only the NFL's beat")
eq(held_cli([LINK], {"ncaaf": 10})[0], 1, "🔴 a league with no beat at all: NOT held")
eq(held_cli([run(401, "collect [cron 20 * * * *]"), run(402, "collect [relay mlb]"),
             run(403, "collect [relay ncaaf nfl]", "completed")], FRESH)[0], 1,
   "🔴 no LIVE football link (a cron, MLB's link and a finished link are not one): NOT held")
eq(held_cli([LINK], FRESH, me="400")[0], 1, "⛔ the link itself is never held by itself")
eq(held_cli([], FRESH, raw="{not json")[0], 1, "⛔ a run list that cannot be read: NOT held")
eq(held_cli([LINK], FRESH, leagues="mlb")[0], 1, "⛔ an MLB run is never held")
eq(held_cli([LINK], {"ncaaf": -5, "nfl": 10})[0], 1, "⛔ a beat from the future (a bad clock) holds nothing")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE HELD STEP AND THE GATE, DRIVEN (stub gh, python, git)")
# ══════════════════════════════════════════════════════════════════════
HELD_STEP = (wfparse.step_run(WF, step_id="held") or "").replace("\r", "")
HELD_ENV = wfparse.step_env(WF, step_id="held") or {}
HELD_IF = next((s.cond for s in wfparse.steps(SRC, job="collect") if s.id == "held"), "") or ""
CONVERGE = (wfparse.step_run(WF, step_id="collect") or "").replace("\r", "")
CONVERGE_ENV = wfparse.step_env(WF, step_id="collect") or {}
ck("the held step and the Converge step are read from the workflow as it will be live (%s)"
   % os.path.relpath(WF, ROOT), "relay.py held" in HELD_STEP and "verify_freshness.py" in CONVERGE
   and CONVERGE_ENV.get("RELAY_HELD") == "${{ steps.held.outputs.held }}"
   and HELD_ENV.get("LEAGUES") == "${{ steps.mode.outputs.league }}")
ck("🔴 the held step runs only for a SCHEDULED football run (never a hand run, a push or a link)",
   "github.event_name == 'schedule'" in HELD_IF and "relay_league == 'ncaaf nfl'" in HELD_IF
   and R.FOOTBALL == "ncaaf nfl", HELD_IF)


def drive_held(runs_ok, runs, beats):
    t = tempfile.mkdtemp(prefix="held-step-", dir=_TMP)
    try:
        shutil.copy(os.path.join(ROOT, "relay.py"), t)
        for lg, age in beats.items():
            _write(os.path.join(t, "data", lg, "latest", R.BEAT_FILE),
                   {"run_id": "1", "at": (NOW - age * MIN).strftime("%Y-%m-%dT%H:%M:%SZ")})
        _write(os.path.join(t, "runs.json"), runs)
        b = os.path.join(t, "bin")
        os.makedirs(b)
        for name, body in (("gh", '#!/bin/bash\n[ "$RUNS_OK" = 1 ] || exit 1\ncat "$FAKE_RUNS"\n'),
                           ("git", "#!/bin/bash\nexit 0\n")):
            open(os.path.join(b, name), "w", encoding="utf-8", newline="\n").write(body)
            os.chmod(os.path.join(b, name), 0o755)
        open(os.path.join(t, "step.sh"), "w", encoding="utf-8", newline="\n").write(HELD_STEP)
        out = os.path.join(t, "out")
        open(out, "w").close()
        subprocess.run(["bash", "step.sh"], cwd=t, capture_output=True, text=True, timeout=120,
                       env=dict(os.environ, PATH=b + os.pathsep + os.environ["PATH"], RUNS_OK="1" if runs_ok else "0",
                                FAKE_RUNS=os.path.join(t, "runs.json"), LEAGUES="ncaaf nfl", GITHUB_RUN_ID="500",
                                GITHUB_OUTPUT=out, PYTHONPATH=ROOT, PYTHONUTF8="1"))
        return [l.strip() for l in open(out, encoding="utf-8") if l.startswith("held=")]
    finally:
        shutil.rmtree(t, ignore_errors=True)


eq(drive_held(True, [LINK], FRESH), ["held=yes"], "🔴 the step says held=yes for a live link and fresh beats")
eq(drive_held(True, [LINK], {"ncaaf": 90, "nfl": 90}), ["held=no"], "🔴 ...held=no for old beats")
eq(drive_held(False, [LINK], FRESH), ["held=no"], "⛔ ...and held=no when the run list cannot be read")


def drive_gate(held, event_name, leagues="ncaaf nfl"):
    """The REAL Converge step, one pass, stub `python` (exit 0) and `git` -> the
    leagues verify_freshness.py was run for, and the step's output."""
    t = tempfile.mkdtemp(prefix="held-gate-", dir=_TMP)
    try:
        b = os.path.join(t, "bin")
        os.makedirs(b)
        open(os.path.join(b, "python"), "w", encoding="utf-8", newline="\n").write(
            '#!/bin/bash\necho "LEAGUE=$LEAGUE $*" >> "$CALLS"\nexit 0\n')
        open(os.path.join(b, "git"), "w", encoding="utf-8", newline="\n").write("#!/bin/bash\nexit 0\n")
        for n in ("python", "git"):
            os.chmod(os.path.join(b, n), 0o755)
        open(os.path.join(t, "step.sh"), "w", encoding="utf-8", newline="\n").write(CONVERGE)
        calls = os.path.join(t, "calls")
        env = dict(os.environ, PATH=b + os.pathsep + os.environ["PATH"], CALLS=calls, LEAGUES=leagues,
                   MODES="news", SEASON="2026", LOOP_MINUTES="0", GITHUB_OUTPUT=os.path.join(t, "out"),
                   GITHUB_RUN_NUMBER="1", GITHUB_EVENT_NAME=event_name)
        env.pop("RELAY_HELD", None)
        if held is not None:
            env["RELAY_HELD"] = held
        p = subprocess.run(["bash", os.path.join(t, "step.sh")], cwd=t, env=env, capture_output=True,
                           text=True, timeout=120)
        lines = open(calls, encoding="utf-8").read().splitlines() if os.path.exists(calls) else []
        return [l.split()[0][7:] for l in lines if "verify_freshness.py" in l], p.stdout
    finally:
        shutil.rmtree(t, ignore_errors=True)


_v, _o = drive_gate("yes", "schedule")
eq(_v, [], "🔴 held (a scheduled run, held=yes): verify_freshness.py is run for neither league; the link "
   "runs it on its own pass")
ck("   ...and the log says so, per league", _o.count("HELD: a football relay link converges") == 2, shown(_o[-400:]))
eq(drive_gate("no", "schedule")[0], ["ncaaf", "nfl"], "✅ held=no: the gate runs once per league, as before")
eq(drive_gate(None, "schedule")[0], ["ncaaf", "nfl"], "✅ ...and with no held step at all (MLB, a push)")
eq(drive_gate("yes", "workflow_dispatch")[0], ["ncaaf", "nfl"],
   "⛔ held=yes on a run no cron started is gated as before")

shutil.rmtree(_TMP, ignore_errors=True)
note("A held cron still pays for ITS OWN extras exactly as today: `halftime-probe` (no contract row) "
     "is a cron's own 2-credit probe that budget.py already prices; the link never runs it.")
