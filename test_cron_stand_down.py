#!/usr/bin/env python3
"""
A CRON THAT STARTS LATE MUST NOT BUY AGAIN WHAT AN EARLIER PASS BOUGHT.

🔴🔴 `[2026-11-11]` `converge(explicit=...)` appended every mode its cron
named, inside contract or not. GitHub started the `4 7 * * *` college cron
5-10 hours late on every one of the 25 days measured (10-18 -> 11-11), after
an hourly pass had already rebuilt cfb-probe for its 07:00Z deadline, so the
cron swept CFBD again: 922 of the 2,391 calls those 25 days made (39%), and
November's 3,000-call key was on course to run out around the 29th.

✅ `freshness.STAND_DOWN`: a free metered mode a cron names is not run when
every row it builds is inside contract and each dated row was built at or
after THIS cron's own minute. ⛔ Everything else runs exactly as before: a
row the contract owes, a mode with no dated row, a run no cron started, an
unreadable event file, every paid mode, and the Sunday `35 14 * * 0` rebuild.

⛔ DRIVEN, NEVER THE LIVE TREE: the real `converge`, in a planted college
tree pinned to the same NOW its clocks read, with `run_mode` recording what
it was asked to run, and the cron given by a planted GitHub event file.
"""
import ast
import contextlib
import datetime
import importlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from tcheck import ck, eq, note, section  # noqa: E402

import freshness as F  # noqa: E402

UTC = datetime.timezone.utc


def T(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


# ══════════════════════════════════════════════════════════════════════
section("1. THE CRON'S OWN MINUTE (cron_last_fire), GITHUB'S UTC CRONS")
# ══════════════════════════════════════════════════════════════════════
for cron, now, want in [
        ("4 7 * * *", "2026-11-11 15:25", "2026-11-11 07:04"),   # 11-11, 8h late
        ("4 7 * * *", "2026-11-11 07:04", "2026-11-11 07:04"),   # on the minute
        ("4 7 * * *", "2026-11-11 06:59", "2026-11-10 07:04"),   # before: yesterday's
        ("35 14 * * 0", "2026-11-08 19:03", "2026-11-08 14:35"),  # Sunday, 4.5h late
        ("35 14 * * 0", "2026-11-10 09:00", "2026-11-08 14:35"),  # Tuesday: last Sunday's
        ("40 */2 * * 6", "2026-11-07 18:45", "2026-11-07 18:40"),  # a Saturday refresh
        ("40 */2 * * 6", "2026-11-08 00:10", "2026-11-07 22:40"),  # past midnight
        ("45 1,3,23 * * 2", "2026-11-10 02:00", "2026-11-10 01:45"),
        ("45 1,3,5 * * 1", "2026-11-10 00:30", "2026-11-09 05:45"),
        ("5 13,19,1 * * *", "2026-11-11 12:00", "2026-11-11 01:05"),
        ("40 1,3,5,13 * * 0", "2026-11-08 13:39", "2026-11-08 05:40"),
        ("12 16 * * 7", "2026-11-08 17:00", "2026-11-08 16:12"),  # 7 is Sunday too
]:
    eq(F.cron_last_fire(cron, T(now)), T(want), "%-18s at %s -> %s" % (cron, now, want))
for bad in ("", "not a cron", "4 7 * *", None, "61-x 7 * * *"):
    eq(F.cron_last_fire(bad, T("2026-11-11 15:25")), None,
       "⛔ an unreadable cron %r has no minute (so the mode runs)" % (bad,))


# ══════════════════════════════════════════════════════════════════════
section("2. THE RUN'S OWN CRON (fired_cron), FROM GITHUB'S EVENT FILE")
# ══════════════════════════════════════════════════════════════════════
_tmp = tempfile.mkdtemp(prefix="standdown-ev-")


def event(cron, name="schedule"):
    """A GitHub event file for a run `cron` started -> its env."""
    p = os.path.join(_tmp, "event-%d.json" % len(os.listdir(_tmp)))
    with open(p, "w", encoding="utf-8") as fh:
        json.dump({"schedule": cron} if cron is not None else {}, fh)
    return {"GITHUB_EVENT_NAME": name, "GITHUB_EVENT_PATH": p}


eq(F.fired_cron(event("4 7 * * *")), "4 7 * * *", "a scheduled run names its cron")
# @vacuity only a run a cron started has a cron's minute to stand down for
#   file: freshness.py
#   find:     if env.get("GITHUB_EVENT_NAME") != "schedule":
#   with:     if not env.get("GITHUB_EVENT_PATH"):
eq(F.fired_cron(event("4 7 * * *", name="workflow_dispatch")), None,
   "⛔ a dispatch is no cron, whatever its event file holds")
eq(F.fired_cron(event("4 7 * * *", name="push")), None, "⛔ nor is a push")
eq(F.fired_cron({"GITHUB_EVENT_NAME": "schedule",
                 "GITHUB_EVENT_PATH": os.path.join(_tmp, "missing.json")}), None,
   "⛔ an event file that is not there names no cron")
_garbled = os.path.join(_tmp, "garbled.json")
open(_garbled, "w").write("{not json")
eq(F.fired_cron({"GITHUB_EVENT_NAME": "schedule", "GITHUB_EVENT_PATH": _garbled}), None,
   "⛔ nor does one that is not JSON")
eq(F.fired_cron(event(None)), None, "⛔ nor one with no schedule in it")
eq(F.fired_cron({}), None, "⛔ nor a run outside GitHub")


# ══════════════════════════════════════════════════════════════════════
# THE HARNESS: the real converge on a planted college tree, at NOW.
# ══════════════════════════════════════════════════════════════════════
def plant(now, built, mode="cfb-probe", stale_one=False, others=None):
    """A college tree whose `mode` rows were all built at `built`
    (one dated row a day older when `stale_one`), plus `others`
    {mode: built}. -> the sandbox directory."""
    d = tempfile.mkdtemp(prefix="standdown-")
    want = dict(others or {})
    want[mode] = built
    first = True
    for m, (kind, path), times, _paid, _why in F.contract("data/ncaaf", "picks", now):
        if m not in want:
            continue
        at = want[m]
        if stale_one and m == mode and times and first:
            at, first = at - datetime.timedelta(days=1), False
        full = os.path.join(d, path)
        stamp = at.strftime("%Y-%m-%dT%H:%M:%SZ")
        if kind == "dir":
            os.makedirs(full, exist_ok=True)
            full = os.path.join(full, at.strftime("%H%M") + ".json")
        os.makedirs(os.path.dirname(full), exist_ok=True)
        doc = {"built_at": stamp, "written_at": stamp}
        if full.endswith(".gz"):
            import gzip
            with gzip.open(full, "wt", encoding="utf-8") as fh:
                json.dump(doc, fh)
        else:
            with open(full, "w", encoding="utf-8") as fh:
                json.dump(doc, fh)
    os.makedirs(os.path.join(d, "picks"), exist_ok=True)
    return d


@contextlib.contextmanager
def at(collect, now, env):
    """converge's clocks (`collect.now`, freshness's `plan` / `survey`) pinned
    to `now`, and the run's GitHub env set to `env`, both restored after."""
    fresh = collect._fresh

    def at_now(fn):
        def call(*a, **k):
            if len(a) < 3 and k.get("now") is None:
                k["now"] = now
            return fn(*a, **k)
        return call
    keys = ("GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH")
    saved_env = {k: os.environ.get(k) for k in keys}
    saved = collect.now, fresh.plan, fresh.survey
    collect.now = lambda: now
    fresh.plan, fresh.survey = at_now(fresh.plan), at_now(fresh.survey)
    for k in keys:
        os.environ.pop(k, None)
        if env.get(k) is not None:
            os.environ[k] = env[k]
    try:
        yield
    finally:
        collect.now, fresh.plan, fresh.survey = saved
        for k in keys:
            os.environ.pop(k, None)
            if saved_env[k] is not None:
                os.environ[k] = saved_env[k]


def converge(d, now, env, explicit):
    """The real converge in `d` at `now` -> (modes run, exit code, stdout)."""
    cwd, lg = os.getcwd(), os.environ.get("LEAGUE")
    os.chdir(d)
    os.environ["LEAGUE"] = "ncaaf"
    ran = []
    try:
        import collect
        importlib.reload(collect)
        collect.run_mode = ran.append
        collect.daily_spend = lambda *a, **k: 0
        out = io.StringIO()
        with at(collect, now, env), contextlib.redirect_stdout(out):
            code = collect.converge(explicit=list(explicit))
        return ran, code, out.getvalue()
    finally:
        os.chdir(cwd)
        if lg is None:
            os.environ.pop("LEAGUE", None)
        else:
            os.environ["LEAGUE"] = lg


def rows_of(d, now, mode):
    return [r for r in F.survey(data=os.path.join(d, "data", "ncaaf"),
                                picks=os.path.join(d, "picks"), now=now)
            if r["mode"] == mode]


def precondition(d, now, mode, label):
    """Every row of `mode` inside contract, and the contract plans no `mode`
    by itself: otherwise the case asks nothing about a stand-down."""
    cwd = os.getcwd()
    os.chdir(d)
    try:
        rs = [r for r in F.survey(data="data/ncaaf", picks="picks", now=now)
              if r["mode"] == mode]
        planned, _ = F.plan(data="data/ncaaf", picks="picks", now=now)
    finally:
        os.chdir(cwd)
    ck("   (%s: the planted %s has %d rows, %d dated, all inside contract, "
       "and the contract alone plans no %s)" % (label, mode, len(rs),
                                                sum(1 for r in rs if r["due_at"]), mode),
       rs and any(r["due_at"] for r in rs) and not any(r["stale"] for r in rs)
       and mode not in planned,
       "⛔ otherwise this case is vacuous. stale: %s planned: %s"
       % ([(r["path"], r["age_min"], r["due_at"], r.get("unhealthy"))
           for r in rs if r["stale"]], planned))


# ══════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 11-11: THE `4 7` CRON STARTED 8 HOURS LATE, CFB-PROBE ALREADY BUILT")
# ══════════════════════════════════════════════════════════════════════
NOW = T("2026-11-11 15:25")            # 43044581018 started 15:04Z, planned 15:25Z
d = plant(NOW, T("2026-11-11 07:25"))  # the hourly pass that built it at 07:25Z
try:
    precondition(d, NOW, "cfb-probe", "11-11")
    ran, code, out = converge(d, NOW, event("4 7 * * *"), ["cfb-probe"])
    # @vacuity a cron whose work an earlier pass already did must not re-run a metered mode
    #   file: collect.py
    #   find:         if _since is not None:
    #   with:         if False:
    ck("🔴🔴 cfb-probe is NOT run again: its ~40 CFBD calls are not spent twice",
       "cfb-probe" not in ran,
       "⛔ THE DEFECT. ~~`for m in explicit: if m not in modes: modes.append(m)`~~ "
       "ran it: 1,973 -> 1,932 at 07:26Z, then 1,930 -> 1,890 at 15:40Z. ran=%s" % ran)
    ck("✅ ...and the log says so, naming the cron's minute",
       re.search(r"STAND DOWN: cfb-probe — .*2026-11-11 07:04Z", out), out[-600:])
    eq(code, 0, "   ...and the pass is green")
finally:
    shutil.rmtree(d, ignore_errors=True)

# 🔴 `[2026-11-12]` #349'S CATCH-UP. A pass that straddles 07:00Z builds
#    cfb-probe in its catch-up round, often before the cron's 07:04Z: the
#    stand-down reads only the rows' stamps, so that build counts like any
#    other. ~~"built after the cron's own minute"~~ re-swept it: a build after
#    07:00Z is the one `4 7` fires for (SERVES_MIN).
d = plant(NOW, T("2026-11-11 07:02"))
try:
    precondition(d, NOW, "cfb-probe", "catch-up at 07:02Z")
    ran, code, out = converge(d, NOW, event("4 7 * * *"), ["cfb-probe"])
    # @vacuity a build after the deadline the cron fires for did the cron's work
    #   file: freshness.py
    #   find: SERVES_MIN = 30
    #   with: SERVES_MIN = 0
    ck("🔴 a catch-up build at 07:02Z, after the 07:00Z deadline `4 7` fires for, "
       "is not swept again", "cfb-probe" not in ran and "STAND DOWN: cfb-probe" in out,
       "ran=%s" % ran)
finally:
    shutil.rmtree(d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("4. ⛔ EVERYTHING ELSE RUNS EXACTLY AS BEFORE")
# ══════════════════════════════════════════════════════════════════════
def runs(label, now, built, env, explicit=("cfb-probe",), mode="cfb-probe",
         stale_one=False, others=None, need_pre=True):
    d = plant(now, built, mode=mode, stale_one=stale_one, others=others)
    try:
        if need_pre:
            precondition(d, now, mode, label)
        ran, _code, out = converge(d, now, env, explicit)
        ck("⛔ %s -> %s runs" % (label, mode), mode in ran,
           "ran=%s %s" % (ran, [l for l in out.splitlines() if "STAND DOWN" in l]))
    finally:
        shutil.rmtree(d, ignore_errors=True)


# 🔴 THE SUNDAY REBUILD. Sam's `35 14 * * 0`, after Saturday's games, fires
#    7h35m after cfb-probe's 07:00Z deadline: an extra build, judged by its own
#    minute, and the day's build (07:07Z) is before it, so it sweeps.
# @vacuity an extra cron is judged by its own minute, never by the deadline before it
#   file: freshness.py
#   find:         return built >= (due if fires_for else since)
#   with:         return built >= due
# @vacuity only a cron within SERVES_MIN of a deadline fires for it
#   file: freshness.py
#   find: SERVES_MIN = 30
#   with: SERVES_MIN = 600
runs("Sunday 11-08: the `35 14 * * 0` rebuild, the day's build at 07:07Z",
     T("2026-11-08 19:03"), T("2026-11-08 07:07"), event("35 14 * * 0"),
     explicit=("cfb-probe",))
# A row the contract owes is planned by the contract, whatever the cron.
runs("one dated row a day old", NOW, T("2026-11-11 07:25"), event("4 7 * * *"),
     stale_one=True, need_pre=False)
runs("a run no cron started (a dispatch)", NOW, T("2026-11-11 07:25"),
     event("4 7 * * *", name="workflow_dispatch"))
runs("an event file nobody can read", NOW, T("2026-11-11 07:25"),
     {"GITHUB_EVENT_NAME": "schedule", "GITHUB_EVENT_PATH": _garbled})
runs("no GitHub env at all", NOW, T("2026-11-11 07:25"), {})
# 🔴 A GAME-DAY SCORES REFRESH: each is due after the one before it.
_SAT = T("2026-11-07 18:45")
runs("Saturday's 18:40Z fb-scores refresh, the last at 16:41Z", _SAT,
     T("2026-11-07 16:41"), event("40 */2 * * 6"), explicit=("fb-scores",),
     mode="fb-scores")
# ⚠️ The nearest extra refresh to a deadline: Saturday's 08:40Z, 40 minutes after
#    fb-scores' 08:00Z (over SERVES_MIN), after the 08:04Z cron built it.
runs("Saturday's 08:40Z fb-scores refresh, 40 minutes after its 08:00Z deadline",
     T("2026-11-07 08:45"), T("2026-11-07 08:05"), event("40 */2 * * 6"),
     explicit=("fb-scores",), mode="fb-scores")

# ...and the same refresh when a pass already built it after 18:40Z stands down.
d = plant(_SAT, T("2026-11-07 18:42"), mode="fb-scores")
try:
    precondition(d, _SAT, "fb-scores", "Saturday 18:42Z")
    ran, _c, out = converge(d, _SAT, event("40 */2 * * 6"), ["fb-scores"])
    ck("✅ ...while a refresh another pass made after 18:40Z is not asked twice",
       "fb-scores" not in ran and "STAND DOWN: fb-scores" in out, "ran=%s" % ran)
finally:
    shutil.rmtree(d, ignore_errors=True)

# cfb-teams: due Sun 10:35 ET (14:35Z); an hourly pass at 15:20Z built it.
_SUN = T("2026-11-08 19:03")
d = plant(_SUN, T("2026-11-08 15:20"), mode="cfb-teams",
          others={"cfb-probe": T("2026-11-08 07:07")})
try:
    precondition(d, _SUN, "cfb-teams", "Sunday cfb-teams")
    ran, _c, out = converge(d, _SUN, event("35 14 * * 0"), ["cfb-teams"])
    ck("✅ Sunday's cfb-teams, rebuilt at 15:20Z after its 14:35Z deadline, is not "
       "asked twice", "cfb-teams" not in ran and "STAND DOWN: cfb-teams" in out,
       "ran=%s" % ran)
    ran, _c, out = converge(d, _SUN, event("35 14 * * 0"), ["cfb-probe"])
    ck("🔴 ...while the same cron's cfb-probe, built at 07:07Z, still sweeps",
       "cfb-probe" in ran, "ran=%s" % ran)
finally:
    shutil.rmtree(d, ignore_errors=True)

# A mode outside STAND_DOWN is run as named, however fresh.
d = plant(NOW, T("2026-11-11 07:25"))
try:
    ran, _c, _o = converge(d, NOW, event("4 7 * * *"), ["news"])
    ck("⛔ a mode outside STAND_DOWN (news) runs as its cron named it",
       "news" in ran, "ran=%s" % ran)
finally:
    shutil.rmtree(d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE CLASS: EVERY METERED MODE A CRON NAMES, AND NO PAID ONE")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ DERIVED, NOT LISTED: the arms of `run_mode` that import `cfb` (CFBD) or
#    reach nflverse, among the modes a cron in collect.yml names.
_src = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
_run = [n for n in ast.walk(ast.parse(_src))
        if isinstance(n, ast.FunctionDef) and n.name == "run_mode"][0]
_arms, _free = {}, set()
for _n in ast.walk(_run):
    if isinstance(_n, ast.If) and ast.unparse(_n.test).startswith("mode == "):
        _m = ast.unparse(_n.test).split("==")[1].strip().strip("'\"")
        _arms[_m] = " ".join(ast.unparse(x) for x in _n.body)
    if isinstance(_n, ast.Assign) and any(getattr(t, "id", None) == "FREE" for t in _n.targets):
        _free = set(ast.literal_eval(_n.value))
import wfroutes  # noqa: E402
_wf = open(os.path.join(ROOT, ".github", "workflows", "collect.yml"), encoding="utf-8").read()
_named = {m for _c, _lg, ms in wfroutes.parse_routes(_wf) for m in ms.split()}
_metered = {m for m in _named if m in _arms and (
    re.search(r"\bimport cfb\b(?!_)", _arms[m]) or "import nfl " in _arms[m] + " "
    or re.search(r"\bimport nfl\b(?!_)", _arms[m]))}
ck("⚠️ the metered modes a cron names were derived (rule 67: never an empty set)",
   {"cfb-probe", "fb-scores"} <= _metered, sorted(_metered))
# @vacuity every metered mode a cron names is in STAND_DOWN, cfb-teams included
#   file: freshness.py
#   find: STAND_DOWN = SOURCE_BACKED | {"cfb-teams"}
#   with: STAND_DOWN = set(SOURCE_BACKED)
ck("🔴 every one of them is in STAND_DOWN",
   _metered <= F.STAND_DOWN,
   "⛔ a metered mode left out re-buys its source on every late cron. missing: %s"
   % sorted(_metered - F.STAND_DOWN))
ck("⛔ and STAND_DOWN holds no paid mode: the Odds pulls keep pull_owed alone",
   _free and F.STAND_DOWN <= _free,
   "not on run_mode's FREE list: %s" % sorted(F.STAND_DOWN - _free))
ck("⚠️ SOURCE_BACKED is inside it (one list grows the other)",
   F.SOURCE_BACKED <= F.STAND_DOWN)

shutil.rmtree(_tmp, ignore_errors=True)

note("💰 WHAT IT SAVES, MEASURED 10-18 -> 11-11 from the key's own readings and "
     "the collect run list: the `4 7` cron re-swept CFBD on 24 of 25 days, "
     "922 calls, ~37 a day, ~1,100 a month. Sunday's rebuild (~40 a week) and "
     "the game-day score refreshes are unchanged.")
