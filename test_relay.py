#!/usr/bin/env python3
"""THE RELAY, AND THE RECORD OF A LATE BUILD. `[Sam, 2026-10-06]`

*"a card is on time even when GitHub starts a scheduled run hours late"*. On
10-06 the only MLB run of the morning ended its hold at 12:42Z, the next one
started 15:52Z, and the card due 14:00Z was built 16:02Z; nothing said so.
✅ An MLB run that reaches the end of its hold dispatches ONE successor that
holds like it (relay.py, the workflow's last step), and every converge pass
records how late each deadline's first build was; the watchdog reports one
more than GRACE_MIN late as DEGRADED until the next on-time build.
The REAL step bodies are driven with a stub `gh` on PATH, in a planted tree
pinned to NOW (the real clock): the workflow as it will be live (a staged
copy wins).

# @vacuity 🔴 a held run dispatches its successor for its OWN league
#   file: docs/upload/collect.yml
#   find: -f league=mlb -f mode=converge -f season= -f relay=true
#   with: -f league=nfl -f mode=converge -f season= -f relay=true
#
# @vacuity 🔴 none while another MLB run is queued or running
#   file: relay.py
#   find:     if busy:
#   with:     if False:
#
# @vacuity 🔴 the per-day cap stops the chain
#   file: relay.py
#   find:     if len(links) >= RELAY_DAY_CAP:
#   with:     if False:
#
# @vacuity 🔴 two no-games days in a row (the off-season): no successor
#   file: relay.py
#   find:     if F.no_games_day(last, data) and F.no_games_day(nxt, data):
#   with:     if False:
#
# @vacuity 🔴 the morning of a game day after a no-games day hands over
#   file: relay.py
#   find:     if F.no_games_day(last, data) and F.no_games_day(nxt, data):
#   with:     if F.no_games_day(last, data):
#
# @vacuity 🔴 the evening of a no-games day before a game day hands over
#   file: relay.py
#   find:     last, nxt = F.due_date(F.CARD, now), F.et_date(F.next_due(F.CARD, now))
#   with:     last, nxt = F.due_date(F.CARD, now), F.et_date(now)
#
# @vacuity 🔴 no reading for the next day hands over (fail closed)
#   file: freshness.py
#   find:     return bool(seen) and all(n == 0 for n in seen)
#   with:     return all(n == 0 for n in seen)
#
# @vacuity 🔴 a re-run attempt starts no successor
#   file: relay.py
#   find:     if int(attempt or 1) != 1:
#   with:     if False:
#
# @vacuity 🔴 a plain dispatch does not hold
#   file: docs/upload/collect.yml
#   find:           elif [ "${{ github.event_name }}" = "workflow_dispatch" ] && [ "$RELAY" = "true" ]; then
#   with:           elif [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
#
# @vacuity 🔴 ...and does not relay
#   file: docs/upload/collect.yml
#   find:                || [ "${{ github.event_name }}" != "workflow_dispatch" ]; }; then
#   with:                || true; }; then
#
# @vacuity 🔴 a relay link is always `converge`: with nothing due it spends nothing
#   file: docs/upload/collect.yml
#   find:             echo "mode=converge" >> "$GITHUB_OUTPUT"      # a relay link: converge only
#   with:             echo "mode=gamelines" >> "$GITHUB_OUTPUT"      # a relay link: converge only
#
# @vacuity 🔴 every converge pass writes the lateness record
#   file: collect.py
#   find:         _fresh.record_builds(rows, f"{LATEST}/{_fresh.LATENESS_FILE}")
#   with:         pass
#
# @vacuity 🔴 a build more than GRACE_MIN late is reported
#   file: watchdog.py
#   find:             if isinstance(late, (int, float)) and late > F.GRACE_MIN:
#   with:             if isinstance(late, (int, float)) and late > 10 ** 6:
#
# @vacuity 🔴 ...as DEGRADED, never BROKEN
#   file: watchdog.py
#   find:             rep.warn("late:%s:%s" % (mode, lg),
#   with:             rep.bad("late:%s:%s" % (mode, lg),
#
# @vacuity 🔴 a same-day rebuild does not hide a late build
#   file: freshness.py
#   find:             continue                       # the first build for this deadline stands
#   with:             pass
#
# @vacuity 🔴 ...and it clears after the next on-time build
#   file: freshness.py
#   find:         if old.get("due_at") == r["due_at"]:
#   with:         if old.get("due_at"):
"""
import datetime
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "mlb")
import collect as C  # noqa: E402
import freshness as F  # noqa: E402
import relay as R  # noqa: E402
import watchdog as W  # noqa: E402
import wfparse  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

UTC = datetime.timezone.utc
WF = wfparse.effective_workflows(ROOT)["collect.yml"]
SRC = open(WF, encoding="utf-8").read()
STEP = "Relay — hand the hold to the next MLB run"
BODY = (wfparse.step_run(WF, step_name=STEP) or "").replace("\r", "")
ROUTE = (wfparse.step_run(WF, step_id="mode") or "").replace("\r", "")
ROUTE_ENV = wfparse.step_env(WF, step_id="mode") or {}
NOW = datetime.datetime.now(UTC)
TODAY = NOW.strftime("%Y-%m-%d")
ck("the relay step and the routing step are read from the workflow as it will be live (%s)"
   % os.path.relpath(WF, ROOT), bool(BODY) and "relay.py" in BODY and bool(ROUTE)
   and ROUTE_ENV.get("RELAY") == "${{ github.event.inputs.relay }}")


def put(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with (gzip.open(p, "wt") if p.endswith(".gz") else open(p, "w")) as fh:
        json.dump(doc, fh)


def run(i, title, status="completed", created=None):
    return {"databaseId": i, "status": status, "displayTitle": title,
            "createdAt": created or TODAY + "T06:00:00Z"}


ME = run(100, "collect [cron 5 13,19,1 * * *]", "in_progress")


def relay(runs, games=2, attempt="1"):
    """Run the REAL relay step in a tree pinned to NOW. -> the gh calls it made."""
    t = tempfile.mkdtemp(prefix="relay-")
    try:
        shutil.copy(os.path.join(ROOT, "relay.py"), t)
        os.makedirs(os.path.join(t, ".github", "workflows"))
        shutil.copy(WF, os.path.join(t, ".github", "workflows", "collect.yml"))
        day = F.due_date(F.CARD, NOW)            # the card's governing day, and its neighbours
        for k in (-1, 0, 1):
            d = (datetime.date.fromisoformat(day) + datetime.timedelta(days=k)).isoformat()
            put(t, "data/%s/schedule/1200.json.gz" % d,
                {"pulled_at": d + "T12:00:00Z", "date": d, "schedule": {"totalGames": games}})
        os.makedirs(os.path.join(t, "picks"))
        put(t, "runs.json", runs)
        bindir = os.path.join(t, "bin")
        os.makedirs(bindir)
        gh = os.path.join(bindir, "gh")
        open(gh, "w", encoding="utf-8", newline="\n").write(
            '#!/bin/bash\nprintf "%s\\n" "$*" >> "$GH_LOG"\n'
            'if [ "$1 $2" = "run list" ]; then cat "$FAKE_RUNS"; fi\nexit 0\n')
        os.chmod(gh, 0o755)
        open(os.path.join(t, "step.sh"), "w", encoding="utf-8", newline="\n").write(BODY)
        log = os.path.join(t, "gh.log")
        p = subprocess.run(["bash", "step.sh"], cwd=t, capture_output=True, text=True,
                           timeout=300, env=dict(os.environ, GH_LOG=log, FAKE_RUNS=os.path.join(t, "runs.json"),
                                                 PATH=bindir + os.pathsep + os.environ["PATH"],
                                                 GITHUB_RUN_ID="100", GITHUB_RUN_ATTEMPT=attempt,
                                                 PYTHONPATH=ROOT, PYTHONUTF8="1"))
        calls = open(log, encoding="utf-8").read().splitlines() if os.path.exists(log) else []
        return [c for c in calls if c.startswith("workflow run")], p.stdout + p.stderr
    finally:
        shutil.rmtree(t, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 A HELD RUN DISPATCHES EXACTLY ONE SUCCESSOR, FOR ITS OWN LEAGUE")
# ══════════════════════════════════════════════════════════════════════
_d, _out = relay([ME, run(90, "collect [cron 4 10 * * *]"),
                  run(91, "collect [cron 20 * * * *]", "in_progress")])     # football, running
eq(_d, ["workflow run collect.yml --ref main -f league=mlb -f mode=converge -f season= "
        "-f relay=true"],
   "🔴 one `gh workflow run` for MLB, marked a relay link, `converge` only (a football run "
   "in progress is not MLB's)")
ck("   ...and the step says why", "dispatching a successor" in _out and "card" in _out, _out[-300:])

# ══════════════════════════════════════════════════════════════════════
section("2. ⛔ NONE WHILE ANOTHER MLB RUN IS QUEUED OR RUNNING")
# ══════════════════════════════════════════════════════════════════════
for _other in (run(101, "collect [cron 4 14 * * *]", "queued"),
               run(102, "collect [relay mlb]", "in_progress"),
               run(103, "collect [push]", "pending"),
               run(104, "collect [workflow_dispatch]", "queued")):      # an older title: no league
    _d, _out = relay([ME, _other])
    eq(_d, [], "🔴 no successor while `%s` is %s: that run carries on"
       % (_other["displayTitle"], _other["status"]))

# ══════════════════════════════════════════════════════════════════════
section("3. ⛔ THE PER-DAY CAP STOPS THE CHAIN")
# ══════════════════════════════════════════════════════════════════════
_cap = R.RELAY_DAY_CAP
_links = [run(200 + k, "collect [relay mlb]", created=TODAY + "T0%d:00:00Z" % k) for k in range(_cap)]
eq(len(relay([ME] + _links[:-1])[0]), 1, "   %d links today: one more may start" % (_cap - 1))
eq(relay([ME] + _links)[0], [], "🔴 %d relay links already started today: the chain stops" % _cap)
_old = [dict(r, createdAt="2001-01-01T00:00:00Z") for r in _links]
eq(len(relay([ME] + _old)[0]), 1, "   ...and yesterday's links do not count against today")

# ══════════════════════════════════════════════════════════════════════
section("4. ⛔ ONLY WHILE AN MLB CARD IS OWED, THE LAST OR THE NEXT [Sam, 2026-10-06]")
# ══════════════════════════════════════════════════════════════════════
_d, _out = relay([ME], games=0)
eq(_d, [], "🔴 no games on the last card's day nor the next one's (the off-season): no "
   "successor; the chain ends by itself and the crons restart it")
ck("   ...and the step says so", "no MLB games on" in _out, _out[-300:])
# `[2026-10-06]` ~~the contract's card row~~ follows the LAST deadline's day
#    until 14:00Z, so after an off-day the chain died until that morning's card
#    was due (Cowork). Planted days, pinned clocks:
_TT = lambda s: datetime.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)  # noqa: E731


def owed(at, games):
    """card_owed at a pinned clock, on a tree holding one schedule reading per day."""
    t = tempfile.mkdtemp(prefix="relay-days-")
    try:
        for d, n in games.items():
            put(t, "data/%s/schedule/1200.json.gz" % d,
                {"pulled_at": d + "T12:00:00Z", "date": d, "schedule": {"totalGames": n}})
        return R.card_owed(_TT(at), os.path.join(t, "data"))[0]
    finally:
        shutil.rmtree(t, ignore_errors=True)


ck("🔴 the evening of a no-games day before a game day hands over (10-02 19:00 ET)",
   owed("2026-10-02T23:00Z", {"2026-10-02": 0, "2026-10-03": 4}))
ck("🔴 the morning of a game day after a no-games day hands over (10-03 08:42 ET)",
   owed("2026-10-03T12:42Z", {"2026-10-02": 0, "2026-10-03": 4}))
ck("🔴 two no-games days in a row do not", not owed("2026-10-02T23:00Z",
                                                    {"2026-10-02": 0, "2026-10-03": 0}))
ck("🔴 no reading yet for the next day hands over (fail closed)",
   owed("2026-10-02T23:00Z", {"2026-10-02": 0}))
eq(relay([ME], attempt="2")[0], [], "⛔ a re-run attempt starts no successor")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 WHO HOLDS AND WHO RELAYS: THE ROUTING STEP")
# ══════════════════════════════════════════════════════════════════════


def route(event, schedule="", inputs=None, relay_flag=""):
    """The REAL routing step for one trigger -> its outputs."""
    inputs = inputs or {}
    subs = {"github.event_name": event, "github.event.schedule": schedule,
            "github.event.inputs.league": inputs.get("league", ""),
            "github.event.inputs.mode": inputs.get("mode", ""),
            "github.event.inputs.season": inputs.get("season", "")}
    body = ROUTE
    for k, v in subs.items():
        body = body.replace("${{ %s }}" % k, v)
    body = body.replace("${{ github.event.inputs.mode || 'converge' }}",
                        inputs.get("mode") or "converge")
    t = tempfile.mkdtemp(prefix="route-")
    try:
        out = os.path.join(t, "out")
        open(out, "w").close()
        open(os.path.join(t, "step.sh"), "w", encoding="utf-8", newline="\n").write(body)
        subprocess.run(["bash", "step.sh"], cwd=t, capture_output=True, text=True, timeout=60,
                       env=dict(os.environ, GITHUB_OUTPUT=out, RELAY=relay_flag))
        return dict(l.rstrip("\n").split("=", 1) for l in open(out, encoding="utf-8") if "=" in l)
    finally:
        shutil.rmtree(t, ignore_errors=True)


_plain = route("workflow_dispatch", inputs={"league": "mlb", "mode": "converge"})
eq((_plain.get("loop_minutes"), _plain.get("relay")), ("0", "no"),
   "🔴 a plain hand-dispatch neither holds nor relays, exactly as before")
_link = route("workflow_dispatch", inputs={"league": "mlb", "mode": "converge"}, relay_flag="true")
eq((_link.get("mode"), _link.get("loop_minutes"), _link.get("relay")), ("converge", "320", "yes"),
   "🔴 a relay link holds like a scheduled MLB run, converges only, and hands over at its end")
eq({k: route("schedule", c).get("relay") for k, c in (("mlb", "4 14 * * *"), ("ncaaf nfl", "20 * * * *"))},
   {"mlb": "yes", "ncaaf nfl": "no"}, "   a scheduled MLB run relays; a football run never does")
eq((route("push").get("loop_minutes"), route("push").get("relay")), ("0", "yes"),
   "   a push (your merge) does one pass and hands the hold on")
ck("🔴 a relay link waits for the run that dispatched it; every other run still cancels and "
   "carries on", "cancel-in-progress: ${{ github.event.inputs.relay != 'true' }}" in SRC
   and "actions: write" in SRC)

# ══════════════════════════════════════════════════════════════════════
section("6. ⛔ A RELAY LINK WITH NOTHING DUE SPENDS NOTHING, AND RECORDS LATENESS")
# ══════════════════════════════════════════════════════════════════════
_t, _cwd = tempfile.mkdtemp(prefix="relay-spend-"), os.getcwd()
_saved = {k: getattr(C, k) for k in ("now", "odds_get", "run_mode", "log")}
_plan, _calls, _ran = F.plan, [], []
try:
    os.chdir(_t)
    C.now = lambda: NOW
    C.log = lambda *a, **k: None
    C.odds_get = lambda *a, **k: _calls.append(a) or ({}, 6, 15000)
    C.run_mode = _ran.append
    C._RAN_PAID.clear()
    F.plan = lambda **kw: ([], F.survey(kw.get("data", "data"), kw.get("picks", "picks"), NOW))
    _args = [a for a in _link.get("mode", "").split() if a]
    _rc = C.converge() if _args in ([], ["converge"]) else C.converge(explicit=_args)
    _wrote = os.path.exists(os.path.join("data", "latest", F.LATENESS_FILE))
finally:
    F.plan = _plan
    for _k, _v in _saved.items():
        setattr(C, _k, _v)
    C._RAN_PAID.clear()
    os.chdir(_cwd)
    shutil.rmtree(_t, ignore_errors=True)
eq((_rc, _ran, len(_calls)), (0, [], 0),
   "🔴 the link runs `converge` with nothing due: no mode run, no paid call, 0 credits")
ck("🔴 ...and every converge pass writes the lateness record", _wrote)

# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 A BUILD MORE THAN GRACE_MIN LATE IS DEGRADED, AND CLEARS ON TIME")
# ══════════════════════════════════════════════════════════════════════
T = lambda s: datetime.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)  # noqa: E731
_t = tempfile.mkdtemp(prefix="late-")
_root = W.ROOT
try:
    D, Pk = os.path.join(_t, "data"), os.path.join(_t, "picks")
    LF = os.path.join(D, "latest", F.LATENESS_FILE)
    W.ROOT = _t

    def look(at, card_day, built):
        put(_t, "picks/%s.json" % card_day, {"generated_at": built})
        F.record_builds(F.survey(D, Pk, T(at)), LF, T(at))
        rep = W.Report()
        W.check_late_builds(rep, T(at))
        rec = [v for v in json.load(open(LF, encoding="utf-8"))["artifacts"].values()
               if v["mode"] == "card"][0]
        return rec, [i for i in rep.items if i["key"] == "late:card:mlb"]

    _r1, _f1 = look("2026-10-06T17:00Z", "2026-10-06", "2026-10-06T16:02:00Z")
    eq((_r1["due_at"], _r1["built_at"], _r1["late_min"]), ("2026-10-06T14:00Z", "2026-10-06T16:02Z", 122.0),
       "🔴 10-06's card: due 14:00Z, built 16:02Z, 122 minutes late, written down")
    ck("🔴 ...and the watchdog reports it DEGRADED, with no repair (GRACE_MIN %d)" % F.GRACE_MIN,
       len(_f1) == 1 and _f1[0]["severity"] == "DEGRADED" and _f1[0]["repair"] is None
       and "122 minutes after it was due" in _f1[0]["what"], str(_f1))
    _r2, _f2 = look("2026-10-06T19:00Z", "2026-10-06", "2026-10-06T18:00:00Z")
    ck("🔴 a same-day rebuild does not hide it: the first build after the deadline stands",
       _r2["built_at"] == "2026-10-06T16:02Z" and len(_f2) == 1, str(_r2))
    _r3, _f3 = look("2026-10-07T15:00Z", "2026-10-07", "2026-10-07T14:10:00Z")
    ck("🔴 the next card built on time (10 minutes) clears it",
       _r3["late_min"] == 10.0 and _f3 == [], "%s %s" % (_r3, _f3))
finally:
    W.ROOT = _root
    shutil.rmtree(_t, ignore_errors=True)
