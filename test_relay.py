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

🔴 `[Sam, 2026-11-18]` AND FOOTBALL'S OWN CHAIN (sections 8-10). Asked "Turn the
relay on for football?", Sam: "Yes". ~~MLB only: football runs are one pass in
a queue per cron~~. ONE chain for both leagues, `collect [relay ncaaf nfl]`:
every scheduled football run and every football link ends with the relay step;
it holds relay.FB_HOLD_MIN minutes counted from the JOB's first step; only a
live football LINK keeps another from starting; the cap is derived from the
hold; the chain ends when no game is near. Section 9 replays MLB's decisions as
they were before it (research/relay_mlb_frozen.json): MLB is unchanged.

# @vacuity 🔴 a held run dispatches its successor for its OWN chain (MLB's)
#   file: docs/upload/collect.yml
#   find: -f league="$RELAY_LEAGUE" -f mode=converge -f season= -f relay=true
#   with: -f league=nfl -f mode=converge -f season= -f relay=true
#
# @vacuity 🔴 [Sam, 2026-11-18] ...and a football run dispatches the FOOTBALL chain's link
#   file: docs/upload/collect.yml
#   find: -f league="$RELAY_LEAGUE" -f mode=converge -f season= -f relay=true
#   with: -f league=mlb -f mode=converge -f season= -f relay=true
#
# @vacuity 🔴 [Sam, 2026-11-18] ...decided by the football chain's own rules
#   file: docs/upload/collect.yml
#   find:           if python relay.py "$RUNS" --league "$RELAY_LEAGUE" --run-id "${GITHUB_RUN_ID:-0}" \
#   with:           if python relay.py "$RUNS" --league mlb --run-id "${GITHUB_RUN_ID:-0}" \
#
# @vacuity 🔴 [Sam, 2026-11-18] a scheduled football run relays (the requirement Sam changed)
#   file: docs/upload/collect.yml
#   find:                && { [ "${{ github.event_name }}" = "schedule" ] || [ "$RELAY" = "true" ]; }; then
#   with:                && false; then
#
# @vacuity 🔴 [Sam, 2026-11-18] ...on the ONE football chain, whatever order its arm names the leagues
#   file: docs/upload/collect.yml
#   find:             echo "relay_league=ncaaf nfl" >> "$GITHUB_OUTPUT"
#   with:             echo "relay_league=$LEAGUE" >> "$GITHUB_OUTPUT"
#
# @vacuity 🔴 [Sam, 2026-11-18] a football link holds relay.FB_HOLD_MIN, not MLB's 320
#   file: docs/upload/collect.yml
#   find:               echo "loop_minutes=280" >> "$GITHUB_OUTPUT"
#   with:               echo "loop_minutes=320" >> "$GITHUB_OUTPUT"
#
# @vacuity 🔴 [Sam, 2026-11-18] ...counted from the JOB clock
#   file: docs/upload/collect.yml
#   find:               echo "hold_from=job" >> "$GITHUB_OUTPUT"
#   with:               echo "hold_from=pass" >> "$GITHUB_OUTPUT"
#
# @vacuity 🔴 [Sam, 2026-11-18] ...which the Converge step honours
#   file: docs/upload/collect.yml
#   find:           if [ "$HOLD_FROM" = "job" ] && [ -n "$JOB_T0" ]; then START=$JOB_T0; fi
#   with:           true
#
# @vacuity 🔴 [Sam, 2026-11-18] only a live football LINK keeps another from starting (never a cron)
#   file: relay.py
#   find:     holding = links_of(runs, me, FOOTBALL)
#   with:     holding = [r for r in runs if str(r.get("databaseId")) != str(me) and r.get("status") in LIVE]
#
# @vacuity 🔴 [Sam, 2026-11-18] ...but a live football link does
#   file: relay.py
#   find:     if holding:
#   with:     if False:
#
# @vacuity 🔴 [Sam, 2026-11-18] the football chain has its own daily cap
#   file: relay.py
#   find:     if len(started) >= FB_DAY_CAP:
#   with:     if False:
#
# @vacuity 🔴 [Sam, 2026-11-18] ...derived from the hold
#   file: relay.py
#   find: FB_DAY_CAP = 1440 // FB_HOLD_MIN + 3
#   with: FB_DAY_CAP = 7
#
# @vacuity 🔴 [Sam, 2026-11-18] no game near: the football chain ends
#   file: relay.py
#   find:     season = F.current_football_season(now)
#   with:     return True, "planted: always owed"
#
# @vacuity 🔴 [Sam, 2026-11-18] ...and a schedule that cannot be read is owed (fail closed)
#   file: relay.py
#   find:         if kicks is None:
#   with:         if False:
#
# @vacuity 🔴 [Sam, 2026-11-18] a link beats at the start of each football pass
#   file: collect.py
#   find:     if _fresh.relay_link():
#   with:     if False:
#
# @vacuity 🔴 [Sam, 2026-11-18] ...and only a link does
#   file: freshness.py
#   find:     return env.get("RELAY_LINK") == "yes" and str(env.get("LEAGUE") or "").strip().lower() in FB_TIMES
#   with:     return str(env.get("LEAGUE") or "").strip().lower() in FB_TIMES
#
# @vacuity 🔴 [Sam, 2026-11-18] a dead football chain is named
#   file: watchdog.py
#   find:     if newest <= RL.RELAY_BEAT_GRACE_MIN:
#   with:     if True:
#
# @vacuity ⛔ [Sam, 2026-11-18] ...but not with no beat at all (before the upload)
#   file: watchdog.py
#   find:     if not seen:
#   with:     if False:
#
# @vacuity ⛔ [Sam, 2026-11-18] ...nor in the off-season
#   file: watchdog.py
#   find:     owed, why = RL.football_owed(now, data)
#   with:     owed, why = True, "planted"
#
# @vacuity ⛔ [Sam, 2026-11-18] MLB's relay is unchanged: its cap
#   file: relay.py
#   find: RELAY_DAY_CAP = 5          # links a league may start in one UTC day
#   with: RELAY_DAY_CAP = 6          # links a league may start in one UTC day
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
for _tv in ("GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH"):   # no test reads the run's trigger
    os.environ.pop(_tv, None)                           # (test_trigger_cleared.py)

UTC = datetime.timezone.utc
WF = wfparse.effective_workflows(ROOT)["collect.yml"]
SRC = open(WF, encoding="utf-8").read()
# `[Sam, 2026-11-18]` ~~"Relay — hand the hold to the next MLB run"~~: both chains use it
STEP = "Relay — hand the hold to the next run of its chain"
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


def fb_schedules(root, kick):
    """`[2026-11-18]` Each football league's current-season schedule, one FBS game at
    `kick` (None: a schedule with no game)."""
    season = F.current_football_season(NOW)
    for lg in sorted(R.FOOTBALL_LEAGUES):
        games = [] if kick is None else [
            {"id": 1, "start": kick.strftime("%Y-%m-%dT%H:%M:%SZ"), "home": "Home", "away": "Away",
             "home_class": "fbs", "away_class": "fbs"}]
        put(root, "data/%s/latest/schedule-%d.json.gz" % (lg, season), {"games": games})


def relay(runs, games=2, attempt="1", relay_league=None, fb_kick=NOW + datetime.timedelta(days=1)):
    """Run the REAL relay step in a tree pinned to NOW. -> the gh calls it made.
    `relay_league`: the routing step's `relay_league` (None: unset, as the deployed
    workflow before the football relay, which MLB must still read as `mlb`)."""
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
        fb_schedules(t, fb_kick)
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
        env = dict(os.environ, GH_LOG=log, FAKE_RUNS=os.path.join(t, "runs.json"),
                   PATH=bindir + os.pathsep + os.environ["PATH"],
                   GITHUB_RUN_ID="100", GITHUB_RUN_ATTEMPT=attempt,
                   PYTHONPATH=ROOT, PYTHONUTF8="1")
        env.pop("RELAY_LEAGUE", None)
        if relay_league is not None:
            env["RELAY_LEAGUE"] = relay_league
        p = subprocess.run(["bash", "step.sh"], cwd=t, capture_output=True, text=True,
                           timeout=300, env=env)
        calls = open(log, encoding="utf-8").read().splitlines() if os.path.exists(log) else []
        return [c for c in calls if c.startswith("workflow run")], p.stdout + p.stderr
    finally:
        shutil.rmtree(t, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 A HELD RUN DISPATCHES EXACTLY ONE SUCCESSOR, FOR ITS OWN LEAGUE")
# ══════════════════════════════════════════════════════════════════════
_d, _out = relay([ME, run(90, "collect [cron 4 10 * * *]"),
                  run(91, "collect [cron 20 * * * *]", "in_progress"),      # football, running
                  run(92, "collect [relay ncaaf nfl]", "in_progress")])     # `[2026-11-18]` its link
eq(_d, ["workflow run collect.yml --ref main -f league=mlb -f mode=converge -f season= "
        "-f relay=true"],
   "🔴 one `gh workflow run` for MLB, marked a relay link, `converge` only (a football run "
   "in progress is not MLB's, nor is a football relay link)")
eq(relay([ME], relay_league="mlb")[0], _d,
   "   ...and the same with the routing step's `relay_league=mlb` (the staged workflow)")
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
# 🔴 `[Sam, 2026-11-18]` THE REQUIREMENT CHANGED, SO THE CHECK IS REWRITTEN TO IT, NOT
#    DELETED (CLAUDE.md, THE ONE RULE THAT MATTERS MOST, `[Sam, 2026-10-01]`). It read
#    ~~"a scheduled MLB run relays; a football run never does"~~. Asked "Turn the relay on
#    for football?", Sam: "Yes": a scheduled football run relays too, on the football chain.
eq({k: (route("schedule", c).get("relay"), route("schedule", c).get("relay_league"))
    for k, c in (("mlb", "4 14 * * *"), ("ncaaf nfl", "20 * * * *"))},
   {"mlb": ("yes", "mlb"), "ncaaf nfl": ("yes", R.FOOTBALL)},
   "🔴 a scheduled MLB run relays on MLB's chain, and [Sam, 2026-11-18] a scheduled football "
   "run relays on the football chain")
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

    # `[Sam, 2026-10-07]` an earlier entry first: an artifact's FIRST entry is a sighting,
    #    not a measurement, so 10-06's card is measured only once the card was seen before
    look("2026-10-05T15:00Z", "2026-10-05", "2026-10-05T14:05:00Z")
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

# ══════════════════════════════════════════════════════════════════════
section("8a. 🔴 [Sam, 2026-11-18] THE FOOTBALL CHAIN: WHO RELAYS, AND HOW A LINK HOLDS")
# ══════════════════════════════════════════════════════════════════════
# ✅ THE CLASS, DERIVED: every football arm the routing table holds (wfroutes), every
#    cron collect.yml declares, and every kind of run; never a hand list.
import runs_report as RR  # noqa: E402
import wfroutes  # noqa: E402

ARMS = wfroutes.parse_arms(SRC)
FB_ARMS = [(c, lg) for c, lg, _m in ARMS if set(lg.split()) & R.FOOTBALL_LEAGUES]
ALL_CRONS = sorted(set(RR.declared_crons(ROOT)["collect"]["crons"]))   # every cron line is byte-identical
MLB_CRONS = [c for c in ALL_CRONS if c not in {a for a, _l, _m in ARMS}]
ck("⚠️ the football arms and MLB's crons were DERIVED (rule 67: never an empty class)",
   len(FB_ARMS) >= 30 and len(MLB_CRONS) >= 4 and {"nfl ncaaf", "ncaaf nfl"} <= {lg for _c, lg in FB_ARMS},
   "%d football arms, %d MLB crons" % (len(FB_ARMS), len(MLB_CRONS)))
_bad = []
for _c, _lg in FB_ARMS:
    _o = route("schedule", _c)
    if (_o.get("relay"), _o.get("relay_league"), _o.get("loop_minutes"), _o.get("hold_from")) \
            != ("yes", R.FOOTBALL, "0", None):
        _bad.append((_c, _lg, _o))
ck("🔴 every scheduled football run (%d arms, either league order) relays on ONE chain, "
   "`relay_league` == relay.FOOTBALL (%r), and is still one pass" % (len(FB_ARMS), R.FOOTBALL),
   not _bad, "⛔ before 11-18 every one was relay=no: %s" % _bad[:3])
_fl = route("workflow_dispatch", inputs={"league": R.FOOTBALL, "mode": "converge"}, relay_flag="true")
eq((_fl.get("mode"), _fl.get("loop_minutes"), _fl.get("hold_from"), _fl.get("relay"), _fl.get("relay_league")),
   ("converge", str(R.FB_HOLD_MIN), "job", "yes", R.FOOTBALL),
   "🔴 a football link converges only, holds relay.FB_HOLD_MIN (%d) counted from the JOB clock, "
   "and hands over on the football chain" % R.FB_HOLD_MIN)
for _lg in ("nfl", "ncaaf", R.FOOTBALL):
    _h = route("workflow_dispatch", inputs={"league": _lg, "mode": "converge"})
    eq((_h.get("relay"), _h.get("loop_minutes"), _h.get("hold_from")), ("no", "0", None),
       "⛔ a plain football hand-dispatch (%s) is still a one-shot that relays nothing" % _lg)
_mbad = []
for _c in MLB_CRONS:
    _o = route("schedule", _c)
    if (_o.get("relay"), _o.get("relay_league"), _o.get("loop_minutes"), _o.get("hold_from"), _o.get("league")) \
            != ("yes", "mlb", "320", None, "mlb"):
        _mbad.append((_c, _o))
ck("⛔ MLB unchanged: each of its %d crons holds 320 from the Converge step and relays on "
   "MLB's chain" % len(MLB_CRONS), not _mbad, _mbad[:3])
eq((_link.get("hold_from"), _link.get("relay_league"), route("push").get("relay_league")), (None, "mlb", "mlb"),
   "⛔ ...and so do MLB's link (320, no job clock) and a push")

# ⛔ NO NEW PASS-CLOCK HOLD CAN APPEAR: the only runs that hold (`loop_minutes` > 0)
#    without the job clock are MLB's two, a scheduled MLB run and an MLB link.
_kinds = [("schedule " + c, route("schedule", c)) for c in ALL_CRONS] + [
    ("push", route("push"))] + [
    ("dispatch " + lg, route("workflow_dispatch", inputs={"league": lg, "mode": "converge"}))
    for lg in ("mlb", "nfl", "ncaaf", R.FOOTBALL)] + [
    ("link " + lg, route("workflow_dispatch", inputs={"league": lg, "mode": "converge"}, relay_flag="true"))
    for lg in ("mlb", R.FOOTBALL)]
_pass_clock = sorted({("link" if k.startswith("link") else k.split()[0], o.get("league"))
                      for k, o in _kinds if int(o.get("loop_minutes") or 0) > 0 and o.get("hold_from") != "job"})
eq(_pass_clock, [("link", "mlb"), ("schedule", "mlb")],
   "⛔ the only holds counted from the Converge step are MLB's (scheduled and link)")


# ══════════════════════════════════════════════════════════════════════
section("8b. 🔴 [Sam, 2026-11-18] THE RELAY STEP STARTS THE FOOTBALL CHAIN, ONCE")
# ══════════════════════════════════════════════════════════════════════
FB_ME = run(100, "collect [cron 34 11 * * *]", "in_progress")      # this run (GITHUB_RUN_ID 100)
WANT_FB = ["workflow run collect.yml --ref main -f league=%s -f mode=converge -f season= -f relay=true"
           % R.FOOTBALL]
_d, _out = relay([FB_ME], relay_league=R.FOOTBALL)
eq(_d, WANT_FB, "🔴 a football cron that ends with no link alive dispatches ONE `collect [relay %s]`, "
   "`converge` only" % R.FOOTBALL)
ck("   ...and says why", "dispatching a successor" in _out and "kicks off" in _out, _out[-300:])
for _other in (run(301, "collect [relay ncaaf nfl]", "in_progress"),
               run(302, "collect [relay ncaaf nfl]", "queued"),
               run(303, "collect [relay nfl ncaaf]", "pending")):
    eq(relay([FB_ME, _other], relay_league=R.FOOTBALL)[0], [],
       "🔴 none while `%s` is %s: that link carries on" % (_other["displayTitle"], _other["status"]))
_others = [run(310, "collect [cron 20 * * * *]", "in_progress"), run(311, "collect [cron 8 11 * * *]", "queued"),
           run(312, "collect [relay mlb]", "in_progress"), run(313, "collect [cron 9 */3 * * *]", "in_progress"),
           run(314, "collect [workflow_dispatch nfl]", "in_progress"), run(315, "collect [push]", "pending"),
           run(316, "collect [relay ncaaf nfl]", "completed")]
eq(relay([FB_ME] + _others, relay_league=R.FOOTBALL)[0], WANT_FB,
   "🔴 live football crons, MLB's holder and link, a hand run, a push and a FINISHED link do not "
   "count: only a live football link keeps another from starting")
_fl_me = run(100, "collect [relay ncaaf nfl]", "in_progress")     # this run IS the link
eq(relay([_fl_me], relay_league=R.FOOTBALL)[0], WANT_FB,
   "🔴 a football link at the end of its hold hands over (it does not count itself)")
eq(relay([FB_ME], relay_league=R.FOOTBALL, attempt="2")[0], [], "⛔ a re-run attempt starts no successor")
_d, _out = relay([FB_ME], relay_league=R.FOOTBALL, fb_kick=NOW + datetime.timedelta(days=R.FB_OWED_AFTER_D + 2))
eq(_d, [], "🔴 no football game within %d days back / %d ahead (the off-season): no link; the "
   "crons restart the chain" % (R.FB_OWED_BEFORE_D, R.FB_OWED_AFTER_D))
ck("   ...and the step says so", "the chain ends" in _out, _out[-300:])
_links = [run(330 + k, "collect [relay ncaaf nfl]", created=TODAY + "T0%d:00:00Z" % (k % 10))
          for k in range(R.FB_DAY_CAP)]
eq(len(relay([FB_ME] + _links[:-1], relay_league=R.FOOTBALL)[0]), 1,
   "   %d football links today: one more may start" % (R.FB_DAY_CAP - 1))
eq(relay([FB_ME] + _links, relay_league=R.FOOTBALL)[0], [],
   "🔴 %d football links already started today (cap %d = 1440 // FB_HOLD_MIN + 3): the chain stops"
   % (R.FB_DAY_CAP, R.FB_DAY_CAP))
eq(R.FB_DAY_CAP, 1440 // R.FB_HOLD_MIN + 3, "⚠️ the cap is DERIVED from the hold, so a hold change "
   "cannot starve the chain (every full hold a day, one across midnight, two restarts)")


# ══════════════════════════════════════════════════════════════════════
section("8c. 🔴 [Sam, 2026-11-18] relay.decide FOR FOOTBALL, ON PINNED CLOCKS")
# ══════════════════════════════════════════════════════════════════════
_P = datetime.datetime(2026, 11, 20, 18, 0, tzinfo=UTC)


def fb_owed_at(now, kicks, leagues=("ncaaf", "nfl"), unreadable=()):
    """relay.football_owed at a pinned clock on a planted tree: `kicks` per league."""
    t = tempfile.mkdtemp(prefix="relay-fbowed-")
    try:
        season = F.current_football_season(now)
        for lg in leagues:
            path = "data/%s/latest/schedule-%d.json.gz" % (lg, season)
            if lg in unreadable:
                os.makedirs(os.path.dirname(os.path.join(t, path)), exist_ok=True)
                open(os.path.join(t, path), "wb").write(b"not a gzip")
                continue
            put(t, path, {"games": [{"id": i, "start": k.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                     "home_class": "fbs", "away_class": "fbs"}
                                    for i, k in enumerate(kicks.get(lg, []))]})
        return R.football_owed(now, os.path.join(t, "data"))[0]
    finally:
        shutil.rmtree(t, ignore_errors=True)


_DAY = datetime.timedelta(days=1)
ck("🔴 a game 2 days ahead owes the chain", fb_owed_at(_P, {"nfl": [_P + 2 * _DAY]}))
ck("🔴 ...and one 2 days back (the week's late games and grading)", fb_owed_at(_P, {"ncaaf": [_P - 2 * _DAY]}))
ck("🔴 no game from 3 days back to 8 ahead in either league: the chain ends",
   not fb_owed_at(_P, {"nfl": [_P - 4 * _DAY, _P + 9 * _DAY], "ncaaf": [_P + 30 * _DAY]}))
ck("🔴 a missing schedule is owed (fail closed: no reading = owed)",
   fb_owed_at(_P, {"nfl": [_P + 30 * _DAY]}, leagues=("nfl",)))
ck("🔴 ...and so is one that cannot be read",
   fb_owed_at(_P, {"nfl": [_P + 30 * _DAY]}, unreadable=("ncaaf",)))
_jan = tempfile.mkdtemp(prefix="relay-jan-")
try:
    for _lg in ("ncaaf", "nfl"):     # the 2026 season's January game, and an empty 2027 file beside it
        put(_jan, "data/%s/latest/schedule-2026.json.gz" % _lg,
            {"games": [{"id": 1, "start": "2027-01-10T18:00:00Z", "home_class": "fbs", "away_class": "fbs"}]})
        put(_jan, "data/%s/latest/schedule-2027.json.gz" % _lg, {"games": []})
    ck("⚠️ ...it reads the season in progress (January is last year's season), never the calendar year",
       R.football_owed(datetime.datetime(2027, 1, 9, 18, 0, tzinfo=UTC), os.path.join(_jan, "data"))[0])
finally:
    shutil.rmtree(_jan, ignore_errors=True)
for _bad_lg in ("", "xfl", "mlb nfl"):
    try:
        R.chain_of(_bad_lg)
        _raised = False
    except ValueError:
        _raised = True
    ck("⛔ %r has no chain: decide raises and the relay step dispatches nothing" % _bad_lg, _raised)
eq([R.chain_of(x) for x in ("nfl", "ncaaf", "ncaaf nfl", "nfl ncaaf", "mlb")],
   [R.FOOTBALL] * 4 + ["mlb"], "   nfl, ncaaf and both (either order) are one chain; mlb its own")


# ══════════════════════════════════════════════════════════════════════
section("8d. 🔴 [Sam, 2026-11-18] THE JOB CLOCK: NO LINK PASS STARTS PAST ITS HOLD")
# ══════════════════════════════════════════════════════════════════════
# The REAL Converge step on a virtual clock: `date` and `sleep` read and move it,
# `python` records each call and spends the pass's minutes, `git` does nothing.
CONVERGE = (wfparse.step_run(WF, step_id="collect") or "").replace("\r", "")
CONVERGE_ENV = wfparse.step_env(WF, step_id="collect") or {}
CLOCK = (wfparse.step_run(WF, step_id="clock") or "").replace("\r", "")
_first = (wfparse.steps(SRC, job="collect") or [None])[0]
ck("🔴 the job clock is the job's FIRST step, and the Converge step reads it",
   _first is not None and _first.id == "clock" and "t0=$(date +%s)" in CLOCK
   and CONVERGE_ENV.get("JOB_T0") == "${{ steps.clock.outputs.t0 }}"
   and CONVERGE_ENV.get("HOLD_FROM") == "${{ steps.mode.outputs.hold_from }}",
   (_first and _first.name, CLOCK[:80], CONVERGE_ENV.get("JOB_T0")))


def clock_drive(loop_minutes, hold_from, tests_min, league_min, leagues="ncaaf nfl"):
    """-> (the virtual minute each pass started, the minute the step ended), both from
    the job's start (T0)."""
    t = tempfile.mkdtemp(prefix="relay-clock-")
    try:
        b = os.path.join(t, "bin")
        os.makedirs(b)
        t0 = 1_000_000
        vc = os.path.join(t, "vclock")
        open(vc, "w").write(str(t0 + int(tests_min * 60)))
        stubs = {
            "date": '#!/bin/bash\nn=$(cat "$VCLOCK")\nfor a in "$@"; do [ "$a" = "+%s" ] && { echo "$n"; exit 0; }; done\n'
                    'echo "2026-11-20T00:00:00Z"\n',
            "sleep": '#!/bin/bash\nn=$(cat "$VCLOCK")\necho $(( n + ${1%.*} )) > "$VCLOCK"\n',
            "python": '#!/bin/bash\nn=$(cat "$VCLOCK")\necho "$n LEAGUE=$LEAGUE $*" >> "$CALLS"\n'
                      'case "$*" in *collect.py*) echo $(( n + LEAGUE_SECS )) > "$VCLOCK" ;; esac\nexit 0\n',
            "git": '#!/bin/bash\nexit 0\n'}
        for k, v in stubs.items():
            open(os.path.join(b, k), "w", encoding="utf-8", newline="\n").write(v)
            os.chmod(os.path.join(b, k), 0o755)
        open(os.path.join(t, "step.sh"), "w", encoding="utf-8", newline="\n").write(CONVERGE)
        calls = os.path.join(t, "calls")
        env = dict(os.environ, PATH=b + os.pathsep + os.environ["PATH"], VCLOCK=vc, CALLS=calls,
                   LEAGUE_SECS=str(int(league_min * 60)), LEAGUES=leagues, MODES="converge",
                   SEASON="2026", LOOP_MINUTES=str(loop_minutes), HOLD_FROM=hold_from or "",
                   JOB_T0=str(t0), GITHUB_OUTPUT=os.path.join(t, "out"), GITHUB_RUN_NUMBER="1")
        for k in ("RELAY_HELD", "RELAY_LINK", "GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH"):
            env.pop(k, None)
        subprocess.run(["bash", os.path.join(t, "step.sh")], cwd=t, env=env, capture_output=True,
                       text=True, timeout=300)
        first = leagues.split()[0]
        starts = [(int(l.split()[0]) - t0) / 60.0 for l in open(calls, encoding="utf-8")
                  if l.split()[1:] == ["LEAGUE=" + first, "collect.py", "converge"]]             if os.path.exists(calls) else []
        return starts, (int(open(vc).read()) - t0) / 60.0
    finally:
        shutil.rmtree(t, ignore_errors=True)


_TIMEOUT = wfparse.job_timeouts(SRC).get("collect")
ck("🔴 the hold and the room a link needs after it fit the job's clock: FB_HOLD_MIN %d + "
   "ROOM_MIN %d <= timeout-minutes %s" % (R.FB_HOLD_MIN, R.ROOM_MIN, _TIMEOUT),
   isinstance(_TIMEOUT, int) and R.FB_HOLD_MIN + R.ROOM_MIN <= _TIMEOUT)
_late = []
for _tests in (5, 20.3, 31.5, 60):
    for _lm in (0.5, 18.4):             # a quiet pass, and two leagues at the longest pass measured (36.8)
        _st, _end = clock_drive(R.FB_HOLD_MIN, "job", _tests, _lm)
        if not _st or max(_st) > R.FB_HOLD_MIN or _end > R.FB_HOLD_MIN + 2 * _lm + 0.01:
            _late.append((_tests, _lm, _st[-1:] if _st else None, _end))
ck("🔴 a football link, whatever its Tests took (5 to 60 min), starts no pass after FB_HOLD_MIN "
   "(%d) minutes from the JOB's start, so its last pass ends inside the room" % R.FB_HOLD_MIN,
   not _late, "⛔ counted from the Converge step a slow Tests pushes the hold toward the kill: %s" % _late)
_st, _end = clock_drive(320, None, 31.5, 0.5, leagues="mlb")
ck("⛔ MLB (no `hold_from`) still holds 320 minutes from the Converge step, exactly as before",
   _st and max(_st) > R.FB_HOLD_MIN and 31.5 + 320 - 16 < max(_st) <= 31.5 + 320, (_st[-2:], _end))


# ══════════════════════════════════════════════════════════════════════
section("9. ⛔ MLB'S RELAY IS BYTE FOR BYTE WHAT IT WAS (research/relay_mlb_frozen.json)")
# ══════════════════════════════════════════════════════════════════════
# Every decision relay.decide(league="mlb") gave before the football relay, over a grid
# of run lists, attempts, clocks and stored schedule readings, recorded from the code at
# `_source_commit`, replayed on today's relay.py.
FROZEN = json.load(open(os.path.join(ROOT, "research", "relay_mlb_frozen.json"), encoding="utf-8"))
_diff, _go = [], 0
_t = tempfile.mkdtemp(prefix="relay-frozen-")
try:
    for _i, _c in enumerate(FROZEN["cases"]):
        _dd = os.path.join(_t, str(_i), "data")
        for _day, _n in _c["games"].items():
            put(os.path.join(_t, str(_i)), "data/%s/schedule/1200.json.gz" % _day,
                {"pulled_at": _day + "T12:00:00Z", "date": _day, "schedule": {"totalGames": _n}})
        _got = list(R.decide(FROZEN["runs_sets"][_c["clock"]][_c["runs"]], "100", _c["attempt"], "mlb",
                             now=_TT(_c["clock"]), wf_text=SRC, data=_dd))
        _go += bool(_got[0])
        if _got != _c["expect"]:
            _diff.append((_c["clock"], _c["runs"], _c["attempt"], _c["games"], _got, _c["expect"]))
finally:
    shutil.rmtree(_t, ignore_errors=True)
ck("⚠️ the record holds MLB's whole grid, both answers (%d cases, %d dispatches), from commit %s"
   % (len(FROZEN["cases"]), _go, FROZEN["_source_commit"][:9]),
   len(FROZEN["cases"]) >= 500 and 0 < _go < len(FROZEN["cases"]))
eq(_diff[:3], [], "⛔ every MLB decision (dispatch or not, and why) is the one it was: %d of %d differ"
   % (len(_diff), len(FROZEN["cases"])))


# ══════════════════════════════════════════════════════════════════════
section("10. 🔴 [Sam, 2026-11-18] A LINK BEATS, AND A DEAD CHAIN IS NAMED (watchdog)")
# ══════════════════════════════════════════════════════════════════════
import importlib  # noqa: E402


def beat_pass(env):
    """A real football converge pass with nothing due, in a planted tree pinned to NOW,
    under `env` -> the beat it wrote (None when it wrote none)."""
    t, cwd = tempfile.mkdtemp(prefix="relay-beat-"), os.getcwd()
    keys = ("LEAGUE", "RELAY_LINK", "RELAY_HELD", "GITHUB_RUN_ID", "GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH")
    saved = {k: os.environ.get(k) for k in keys}
    plan = F.plan
    try:
        os.chdir(t)
        for k in keys:
            os.environ.pop(k, None)
        os.environ.update(env, LEAGUE="ncaaf")
        importlib.reload(C)
        C.now = lambda: NOW
        C.log = lambda *a, **k: None
        F.plan = lambda **kw: ([], F.survey(kw.get("data", "data"), kw.get("picks", "picks"), NOW))
        C.converge()
        p = os.path.join("data", "ncaaf", "latest", R.BEAT_FILE)
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
    finally:
        F.plan = plan
        for k in keys:
            os.environ.pop(k, None)
            if saved[k] is not None:
                os.environ[k] = saved[k]
        os.environ["LEAGUE"] = "mlb"
        importlib.reload(C)
        os.chdir(cwd)
        shutil.rmtree(t, ignore_errors=True)


_b = beat_pass({"RELAY_LINK": "yes", "GITHUB_RUN_ID": "777"})
eq((_b or {}).get("run_id"), "777", "🔴 a football link's converge pass writes its beat, naming the run")
eq((_b or {}).get("at"), NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "   ...stamped when the pass began")
eq(beat_pass({"GITHUB_RUN_ID": "778"}), None, "⛔ a run that is not a link writes no beat")


def chain_finding(beats, kick):
    """watchdog.check_relay_chain on a planted tree at NOW: `beats` = {league: minutes old}."""
    t, root = tempfile.mkdtemp(prefix="relay-chain-"), W.ROOT
    try:
        W.ROOT = t
        fb_schedules(t, kick)
        for lg, age in beats.items():
            put(t, "data/%s/latest/%s" % (lg, R.BEAT_FILE),
                {"run_id": "1", "at": (NOW - datetime.timedelta(minutes=age)).strftime("%Y-%m-%dT%H:%M:%SZ")})
        rep = W.Report()
        W.check_relay_chain(rep, NOW)
        return [i for i in rep.items if i["key"].startswith("relay:")]
    finally:
        W.ROOT = root
        shutil.rmtree(t, ignore_errors=True)


_soon = NOW + datetime.timedelta(days=2)
_f = chain_finding({"ncaaf": R.RELAY_BEAT_GRACE_MIN + 30, "nfl": R.RELAY_BEAT_GRACE_MIN + 1}, _soon)
ck("🔴 no football link has passed for over RELAY_BEAT_GRACE_MIN (%d) while a game is near: one "
   "`relay:football` finding, DEGRADED, no repair" % R.RELAY_BEAT_GRACE_MIN,
   len(_f) == 1 and _f[0]["key"] == "relay:football" and _f[0]["severity"] == "DEGRADED"
   and _f[0]["repair"] is None and "restarts the chain" in _f[0]["why"], str(_f))
eq(chain_finding({"ncaaf": R.RELAY_BEAT_GRACE_MIN + 30, "nfl": 10}, _soon), [],
   "✅ the newer of the two beats decides: a link that passed 10 minutes ago is alive")
eq(chain_finding({}, _soon), [], "⛔ no beat file at all (before Sam's upload): silent")
eq(chain_finding({"ncaaf": 9999, "nfl": 9999}, NOW + datetime.timedelta(days=R.FB_OWED_AFTER_D + 5)), [],
   "⛔ no game within the chain's window (the off-season): silent")
ck("⚠️ RELAY_BEAT_GRACE_MIN is over the hold-free handover a link needs (HELD_BEAT_MIN %d) and "
   "under a full hold (%d)" % (R.HELD_BEAT_MIN, R.FB_HOLD_MIN),
   R.HELD_BEAT_MIN < R.RELAY_BEAT_GRACE_MIN < R.FB_HOLD_MIN)
ck("⚠️ the finding's key names the files to read first", "relay" in W.FILES_FIRST)
