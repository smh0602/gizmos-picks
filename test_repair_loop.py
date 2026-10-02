#!/usr/bin/env python3
"""A FREE REPAIR NEVER CONVERGES, AND NEVER RUNS A MODE OUTSIDE ITS LEAGUE.

🔴 WHAT HAPPENED `[2026-09-28, collect run #1953]`. runs.json reported
"alt-lines/props-player/gamelines failed for nfl (exit 1) -- it left an
artifact out of contract" and "card failed for nfl (RuntimeError: no game
logs at all)". Nothing paid had failed. The WATCHDOG step chose the repair
`card` and ran `LEAGUE=$lg ODDS_API_KEY= ... collect.py card` for all three
leagues. Every explicit mode also converges, so the key-less NFL run
planned every paid pull due, and each died on "ODDS_API_KEY is not set";
and the MLB `card` mode, run under nfl and ncaaf, raised on football data.
⚠️ The same loop, two more ways (both measured):
  - `LEAGUE=nfl ... record` ran the MLB grader and replaced the football
    record.json with an empty MLB-shaped one (4,964 -> 783 bytes, in a
    copy; not seen in production);
  - `LEAGUE=mlb ... card-fb` ran T54 after build_card_fb refused MLB and
    wrote data/latest/t54.json -- in production, commit 027d7215.

✅ THE CLASS, NOT THE INSTANCE:
  1. every `collect.py` call in any workflow as it will be live (a staged
     copy wins) that blanks ODDS_API_KEY carries `converge-off`, and so
     does every `collect.py` call in the watchdog step;
  2. the watchdog step, run WHOLE from the staged copy in a planted tree,
     once per `watchdog.SAFE_REPAIRS` mode: a league whose freshness
     contract does not name the mode exits 0 and leaves every one of its
     files byte-identical; no run converges; nothing reaches the network
     (sockets refused and logged in every Python the step starts).
⚠️ A league that OWNS the mode is only held to its own files here: in a
planted tree its real rebuild has no data to build from, so its exit code
is reported, not judged. Its rebuild is the product's own job and is
tested by the files that own it.

# @vacuity 🔴🔴 a key-less repair that converges is caught
#   file: docs/upload/collect.yml
#   find: LEAGUE=$lg ODDS_API_KEY= timeout 900 python collect.py "$m" converge-off || true
#   with: LEAGUE=$lg ODDS_API_KEY= timeout 900 python collect.py "$m" || true
#
# @vacuity 🔴🔴 the MLB grader under a football league is caught
#   file: collect.py
#   find: return log(f"record is the MLB grader; {LEAGUE} is graded by card-fb. Nothing done.")
#   with: log("the record guard is gone")
#
# @vacuity 🔴 the MLB card under a football league is caught
#   file: collect.py
#   find: return log(f"card is the MLB card; {LEAGUE} builds its card with card-fb. Nothing done.")
#   with: log("the card guard is gone")
#
# @vacuity 🔴 a football mode under MLB is caught
#   file: collect.py
#   find: return log("card-fb is football only; under mlb its card, T54, dossier and shadow record are skipped. Nothing done.")
#   with: log("the card-fb guard is gone")
"""
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import freshness
import watchdog
import wfparse as W
from tcheck import ck, eq, note, section, shown

ROOT = os.path.dirname(os.path.abspath(__file__))
UTC = datetime.timezone.utc

COLLECT = re.compile(r"\bcollect\.py\b")
BLANK_KEY = re.compile(r"(?:^|\s)ODDS_API_KEY=(?:\s|$|\"\"|'')")


def repair_lines(run):
    """Live lines of a step that run collect.py."""
    return [l.strip() for l in (run or "").splitlines()
            if COLLECT.search(l) and not l.lstrip().startswith("#")]


def converging(lines, all_calls=False):
    """collect.py calls that would converge: every one when `all_calls`,
    otherwise only those that blank the Odds key."""
    return [l for l in lines
            if (all_calls or BLANK_KEY.search(l)) and "converge-off" not in l]


# ══════════════════════════════════════════════════════════════════════
section("1. THE SCANNER, ON PLANTED LINES (every case, every run)")
# ══════════════════════════════════════════════════════════════════════
_plant = "\n".join([
    'LEAGUE=$lg ODDS_API_KEY= timeout 900 python collect.py "$m" || true',
    'ODDS_API_KEY="" python collect.py card',
    'LEAGUE=nfl ODDS_API_KEY= python collect.py card-fb converge-off',
    'if ! python collect.py "$m"; then',          # keyed: converging is its job
    '# ODDS_API_KEY= python collect.py card     (a comment runs nothing)',
])
eq(converging(repair_lines(_plant)),
   ['LEAGUE=$lg ODDS_API_KEY= timeout 900 python collect.py "$m" || true',
    'ODDS_API_KEY="" python collect.py card'],
   "🔴 a key-less collect.py call without converge-off is found; one with "
   "it, a keyed call and a comment are not")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 NO KEY-LESS collect.py CALL CONVERGES (the workflows as they will be live)")
# ══════════════════════════════════════════════════════════════════════
_bad, _keyless = [], 0
for _f, _p in sorted(W.effective_workflows(ROOT).items()):
    for _s in W.steps(_p):
        _ls = repair_lines(_s.run)
        _keyless += sum(1 for l in _ls if BLANK_KEY.search(l))
        _bad += ["%s :: %s :: %s" % (_f, _s.name or _s.id, l) for l in converging(_ls)]
WF = W.effective_workflows(ROOT).get("collect.yml")
STEP = W.step_run(WF, step_id="watchdog") if WF else None
STEP = re.sub(r"\$\{\{[^}]*\}\}", "", STEP) if STEP else ""
_wd = repair_lines(STEP)
ck(_keyless >= 1 and any(BLANK_KEY.search(l) for l in _wd)
   and "health.json" in STEP,
   "⚠️ the watchdog step was read from %s, and it holds a key-less repair "
   "(rule 67)" % os.path.relpath(WF or "?", ROOT).replace(os.sep, "/"),
   "%d key-less call(s) found; watchdog step %d chars" % (_keyless, len(STEP)))
ck(not _bad, "🔴🔴 every key-less collect.py call carries converge-off",
   "\n".join("       " + b for b in _bad))
ck(_wd and not converging(_wd, all_calls=True),
   "   ...and so does every collect.py call in the watchdog step", "%r" % _wd)

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 THE WATCHDOG STEP, RUN WHOLE, ONCE PER FREE REPAIR")
# ══════════════════════════════════════════════════════════════════════
_now = datetime.datetime.now(UTC)
# 🔴 `[2026-10-02]` MLB IS ASKED OF AN EMPTY TREE, NOT THE REPO. `no_games_day`
#    reads stored schedules, so in the off-season the live tree dropped MLB's
#    `card` row and "mlb owns card" went false. No reading fails closed: every
#    row is owed, which is the contract this test is about.
_cwd, _empty = os.getcwd(), tempfile.mkdtemp(prefix="repair-owns-")
OWNS = {lg: {r[0] for r in freshness.contract(data=watchdog.DATA[lg], picks="picks", now=_now)}
        for lg in watchdog.LEAGUES if lg != "mlb"}
os.chdir(_empty)
try:
    OWNS["mlb"] = {r[0] for r in freshness.contract(data=watchdog.DATA["mlb"], picks="picks", now=_now)}
finally:
    os.chdir(_cwd)
    shutil.rmtree(_empty, ignore_errors=True)
ck(all(any(m in OWNS[lg] for lg in watchdog.LEAGUES)
       and not all(m in OWNS[lg] for lg in watchdog.LEAGUES)
       for m in watchdog.SAFE_REPAIRS),
   "⚠️ every free repair is owned by some league's contract and not by "
   "every league, so each one has a league it must leave alone (rule 67)",
   "%r" % {m: [lg for lg in watchdog.LEAGUES if m in OWNS[lg]]
           for m in watchdog.SAFE_REPAIRS})

# ⚠️ A NETWORK ATTEMPT IS REFUSED AND WRITTEN DOWN, in every Python the
#    step starts (PYTHONPATH -> this sitecustomize).
SITE = r'''
import os, socket
def _refuse(*a, **k):
    with open(os.environ["REPAIR_NET_LOG"], "a") as fh:
        fh.write("network attempt: %s\n" % repr(a[:3])[:160])
    raise OSError("network refused by test_repair_loop.py")
socket.socket.connect = _refuse
socket.socket.connect_ex = _refuse
socket.create_connection = _refuse
socket.getaddrinfo = _refuse
'''
# ⚠️ `timeout` is the repair line's own first word: this one runs the
#    command and records its league, whether a key reached it, and its
#    exit code. A line that stops calling it records nothing, and the
#    checks below fail rather than pass on silence.
TIMEOUT = '''#!/bin/sh
shift
"$@"; rc=$?
printf '%s|%s|%s|%s\\n' "$LEAGUE" "${ODDS_API_KEY:+KEY}" "$rc" "$*" >> "$REPAIR_RC_LOG"
exit $rc
'''


def owner_of(rel):
    """Which league a data/ or picks/ path belongs to."""
    for lg in ("nfl", "ncaaf"):
        if rel.startswith(("data/%s/" % lg, "picks/%s/" % lg, "picks/fb-%s-" % lg)):
            return lg
    return "mlb"


def snap(d):
    out = {}
    for base in ("data", "picks"):
        for dp, _dirs, fs in os.walk(os.path.join(d, base)):
            for f in fs:
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, d).replace(os.sep, "/")
                out[rel] = hashlib.sha1(open(p, "rb").read()).hexdigest()
    return out


def tree(mode):
    """The product's modules and a planted data tree: one sentinel record
    per league, a college team directory current for today (so nothing
    rebuilds it from the network), and a health report asking for `mode`."""
    d = tempfile.mkdtemp(prefix="repair-loop-")
    for f in os.listdir(ROOT):
        if f.endswith(".py") and not f.startswith("test_") and os.path.isfile(os.path.join(ROOT, f)):
            shutil.copy(os.path.join(ROOT, f), d)
    for lg in watchdog.LEAGUES:
        lat = os.path.join(d, watchdog.DATA[lg], "latest")
        os.makedirs(lat, exist_ok=True)
        json.dump({"planted": lg, "by_book": {}}, open(os.path.join(lat, "record.json"), "w"))
    json.dump({"season": freshness.current_football_season(), "teams": {"x": {}}, "n": 1},
              open(os.path.join(d, "data", "ncaaf", "latest", "teams.json"), "w"))
    os.makedirs(os.path.join(d, "picks"))
    for f in ("2026-01-01.json", "fb-nfl-2026-01-01.json", "fb-ncaaf-2026-01-01.json"):
        json.dump({"planted": f}, open(os.path.join(d, "picks", f), "w"))
    json.dump({"repairs": [mode], "healthy": False, "findings": [], "unrepairable": []},
              open(os.path.join(d, "data", "latest", "health.json"), "w"))
    # the watchdog's JUDGEMENT is not under test here, its repair loop is
    open(os.path.join(d, "watchdog.py"), "w").write("print('stub watchdog')\n")
    return d


def drive(mode):
    """Run the staged watchdog step in a planted tree. -> dict"""
    d = tree(mode)
    ctl = tempfile.mkdtemp(prefix="repair-ctl-")
    try:
        b = os.path.join(ctl, "bin")
        site = os.path.join(ctl, "site")
        os.makedirs(b)
        os.makedirs(site)
        open(os.path.join(site, "sitecustomize.py"), "w").write(SITE)
        py = sys.executable.replace(os.sep, "/")
        for name, body in (("python", '#!/bin/sh\nexec "%s" "$@"\n' % py),
                           ("timeout", TIMEOUT)):
            with open(os.path.join(b, name), "w", newline="\n") as fh:
                fh.write(body)
            os.chmod(os.path.join(b, name), 0o755)
        rc_log, net_log, out = (os.path.join(ctl, x) for x in ("rc.log", "net.log", "out"))
        open(out, "w").close()
        step = os.path.join(ctl, "step.sh")
        open(step, "w", encoding="utf-8", newline="\n").write(STEP)
        before = snap(d)
        env = dict(os.environ, PATH=b + os.pathsep + os.environ["PATH"],
                   PYTHONPATH=site, REPAIR_RC_LOG=rc_log, REPAIR_NET_LOG=net_log,
                   GITHUB_OUTPUT=out, ODDS_API_KEY="", CFBD_API_KEY="")
        env.pop("LEAGUE", None)
        p = subprocess.run(["bash", step], cwd=d, env=env, capture_output=True,
                           text=True, timeout=900)
        after = snap(d)
        calls = [l.split("|", 3) for l in open(rc_log).read().splitlines()] \
            if os.path.exists(rc_log) else []
        return {"rc": p.returncode, "log": p.stdout + p.stderr, "calls": calls,
                "net": open(net_log).read() if os.path.exists(net_log) else "",
                "changed": sorted(k for k in set(before) | set(after)
                                  if before.get(k) != after.get(k)),
                "files": before}
    finally:
        shutil.rmtree(d, ignore_errors=True)
        shutil.rmtree(ctl, ignore_errors=True)


if not STEP:
    ck(False, "the staged watchdog step could not be read, so nothing below can run")
for _m in watchdog.SAFE_REPAIRS if STEP else ():
    _r = drive(_m)
    _by = {c[0]: c for c in _r["calls"]}
    ck(sorted(c[0] for c in _r["calls"]) == sorted(watchdog.LEAGUES)
       and all(c[3].split()[:2] == ["python", "collect.py"] and _m in c[3].split()
               for c in _r["calls"]),
       "⚠️ `%s`: the step ran it once for each of %s" % (_m, ", ".join(watchdog.LEAGUES)),
       "calls %r %s" % (_r["calls"], shown(_r["log"][-300:])))
    ck(all(c[1] == "" for c in _r["calls"]) and "PLAN:" not in _r["log"]
       and not _r["net"],
       "🔴🔴 `%s`: no key, no converge, no network" % _m,
       "keys %r net %r %s" % ([c[1] for c in _r["calls"]], _r["net"][:200],
                              shown(_r["log"][-400:])))
    for _lg in watchdog.LEAGUES:
        if _m in OWNS[_lg]:
            note("`%s` under %s (its owner): exit %s in a planted tree with no data, "
                 "not judged here" % (_m, _lg, (_by.get(_lg) or [None, None, "?"])[2]))
            continue
        _mine = [k for k in _r["changed"] if owner_of(k) == _lg]
        _held = [k for k in _r["files"] if owner_of(k) == _lg]
        ck(_by.get(_lg, [None, None, None])[2] == "0" and not _mine and _held,
           "🔴🔴 `%s` under %s does nothing: exit 0, and all %d of %s's files "
           "byte-identical" % (_m, _lg, len(_held), _lg),
           "rc %r changed %r %s" % ((_by.get(_lg) or [None, None, None])[2], _mine,
                                    shown(_r["log"][-400:])))
