#!/usr/bin/env python3
"""THE WEEKLY STATUS EMAIL, AND EVERY ALERT SAYS WHAT TO DO. `[Sam, 2026-10-07]`
Planted trees and a pinned clock; the real workflow steps driven with a stub gh.

# @vacuity 🔴 the weekly body states each number it was given: the week is 7 days
#   file: status.py
#   find:     rows = [r for r in rows or [] if str(r.get("date") or "") >= since]
#   with:     rows = list(rows or [])
#
# @vacuity 🔴 ...and the week's late builds are kept, not only each artifact's latest
#   file: freshness.py
#   find:             late.append(arts[key])
#   with:             pass
#
# @vacuity 🔴 a clean week reads "Nothing needs you this week."
#   file: status.py
#   find:     L = ["Needs you: %s." % "; ".join(needs) if needs else "Nothing needs you this week.",
#   with:     L = ["Needs you: %s." % "; ".join(needs) if True else "Nothing needs you this week.",
#
# @vacuity 🔴 a BROKEN finding puts it under "Needs you"
#   file: status.py
#   find:         f for f in findings if f.get("severity") == "BROKEN"]
#   with:         f for f in findings if False]
#
# @vacuity 🔴 ...and a health check too old to read, which gives no "right now"
#   file: status.py
#   find:     if seen and now - seen <= datetime.timedelta(hours=HEALTH_MAX_H):
#   with:     if seen:
#
# @vacuity 🔴 the issue is updated in place, never opened twice: a closed one is found too
#   file: docs/upload/status.yml
#   find:           NUM=$(gh issue list --state all --limit 1000 --json number,title \
#   with:           NUM=$(gh issue list --state open --limit 1000 --json number,title \
#
# @vacuity 🔴 ...and the week is posted as a comment, which is what GitHub emails
#   file: docs/upload/status.yml
#   find:             gh issue comment "$NUM" --body-file "$BODY"
#   with:             true
#
# @vacuity 🔴 the watchdog's alert ends with what to do
#   file: watchdog.py
#   find:     L.append(what_to_do(broken or out["findings"], site_updating(out["findings"])))
#   with:     pass
#
# @vacuity 🔴 ...for its own (first BROKEN) finding
#   file: watchdog.py
#   find:     broken = [i for i in out["findings"] if i["severity"] == "BROKEN"]
#   with:     broken = []
"""
import atexit
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
import self_repair  # noqa: E402
import status as S  # noqa: E402
import watchdog as W  # noqa: E402
import wfparse  # noqa: E402
from tcheck import ck, copy_module, eq, section  # noqa: E402

T = lambda s: datetime.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=datetime.timezone.utc)  # noqa: E731
NOW, TITLE, TREES = T("2026-10-12T11:17Z"), "Gizmo's Picks - weekly status", []    # a Monday, at the cron
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])


def put(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with (gzip.open(p, "wt") if p.endswith(".gz") else open(p, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


def tree(findings=(), health_at="2026-10-12T10:41:00Z", runs_at="2026-10-12T11:06:00Z"):
    """One week planted for the three leagues (college has nothing graded)."""
    t = tempfile.mkdtemp(prefix="status-")
    TREES.append(t)
    put(t, "data/latest/record.json", {"overall": {"w": 1108, "n": 1824}, "by_day": [
        {"date": "2026-10-04", "w": 5, "n": 9}, {"date": "2026-10-08", "w": 30, "n": 50}],
        "game_lines": {"w": 7, "n": 12, "by_day": [{"date": "2026-10-09", "w": 3, "n": 5}]}})
    put(t, "data/nfl/latest/record.json", {"overall": {"w": 170, "n": 329},
                                           "by_day": [{"date": "2026-10-11", "w": 12, "n": 25}]})
    put(t, "data/nfl/latest/model-ledger.json", {"picks": [
        {"model": "game_model", "state": "graded", "won": True, "commence": "2026-10-11T17:00:00Z"},
        {"model": "game_model", "state": "graded", "won": False, "commence": "2026-09-28T17:00:00Z"},
        {"model": "game_model", "state": "pending", "commence": "2026-10-18T17:00:00Z"},
        {"model": "props_model", "state": "graded", "won": True, "commence": "2026-10-11T17:00:00Z"}]})
    put(t, "data/nfl/2026-10-11/winner-grades/2300.json.gz", {"grades": [
        {"game_id": "a", "state": "graded", "won": True, "graded_at": "2026-10-11T23:00:00Z"},
        {"game_id": "b", "state": "void", "won": None, "graded_at": "2026-10-11T23:00:00Z"}]})
    # MLB's card 122 minutes late on 10-06 and on time on 10-07, written by the real recorder
    for at, day, age in (("2026-10-05T15:00Z", "2026-10-05", 55), ("2026-10-06T17:00Z", "2026-10-06", 58),
                         ("2026-10-07T15:00Z", "2026-10-07", 50)):    # 10-05 first: a sighting, not measured
        F.record_builds([{"mode": "card", "path": "picks/%s.json" % day, "due_at": day + "T14:00Z",
                          "stale": False, "age_min": age}], os.path.join(t, "data", "latest", F.LATENESS_FILE), T(at))
    put(t, "data/nfl/latest/lateness.json", {"late": [
        {"mode": "card-fb", "path": "picks/fb-nfl-latest.json", "due_at": "2026-10-09T13:30Z", "late_min": 75.0,
         "measured": True},
        {"mode": "card-fb", "path": "picks/fb-nfl-latest.json", "due_at": "2026-10-03T13:30Z", "late_min": 300.0,
         "measured": True}]})
    put(t, "data/latest/health.json", {"checked_at": health_at, "findings": list(findings),
                                       "credits": {"balance": 14568, "pulled_at": "2026-10-12T04:08:00Z"}})
    put(t, "data/latest/runs.json", {"generated_at": runs_at, "window_hours": 48, "by_workflow": {
        "collect": {"failed": 2, "latest": {"conclusion": "failure"}},
        "vacuity": {"failed": 1, "latest": {"conclusion": "success"}}}})
    return t


DEG = {"key": "late:card:mlb", "severity": "DEGRADED", "what": "mlb card was built 122 minutes after it was due"}
BRK = {"key": "card:mlb", "severity": "BROKEN", "what": "the MLB card is missing"}

section("1. 🔴 THE WEEKLY BODY STATES EACH NUMBER IT WAS GIVEN")
_b, _n = S.build(tree([DEG]), NOW)
for _want in ("**MLB**\n- Props: 30-20 (60%) / 1108-716 (61%)\n- Game-line picks: 3-2 (60%) / 7-5 (58%)\n"
              "- Pick to win: nothing graded / nothing graded",
              "**NFL**\n- Props: 12-13 (48%) / 170-159 (52%)\n- Game-line picks: 1-0 (100%) / 1-1 (50%)\n"
              "- Pick to win: 1-0 (100%) / 1-0 (100%)",
              "**College**\n- Props: nothing graded / nothing graded",
              "- {:,} used this month, 14,568 left (read 2026-10-12T04:08:00Z).".format(C.MONTHLY_PLAN - 14568),
              "- 2 built more than 60 minutes after they were due. The worst: MLB card, 122 minutes late "
              "(due 2026-10-06T14:00Z).",
              "- 3 in the last 48 hours: collect 2, vacuity 1.",
              "## Right now\n- DEGRADED: mlb card was built 122 minutes after it was due"):
    ck("🔴 the body says: %s" % _want.splitlines()[-1][:70], _want in _b, "" if _want in _b else _b)

section("2. 🔴 A CLEAN WEEK, AND WHAT NEEDS SAM")
eq((_b.splitlines()[0], _n), ("Nothing needs you this week.", []),
   "🔴 a clean week (a DEGRADED finding is listed, not a need) reads \"Nothing needs you this week.\"")
ck("   ...with no prompt to paste, and it is a report, never a self-repair task",
   "paste this into Claude Code" not in _b and self_repair.is_counter({"body": _b}))
_b3, _n3 = S.build(tree([DEG, BRK]), NOW)
eq(_b3.splitlines()[0], "Needs you: the MLB card is missing.", "🔴 a BROKEN finding puts it under \"Needs you\"")
ck("🔴 ...and the email ENDS with the prompt naming that finding, with Sam's usage check",
   _b3.endswith("```\n") and "check `card:mlb`" in _b3[_b3.rfind("\n---\n"):] and W.USAGE_CHECK in _b3,
   _b3[_b3.rfind("\n---\n"):][:160])
_b5, _n5 = S.build(tree(runs_at="2026-10-12T06:00:00Z"), NOW)
ck("🔴 a stale run list is named as stale and gives no verdict",
   "## Failed runs\n- Can't say: the run list is 5 hours old." in _b5, _b5[_b5.find("## Failed"):][:80])
_b6, _n6 = S.build(tree([BRK], health_at="2026-10-11T09:00:00Z"), NOW)
ck("🔴 a health check 26 hours old needs Sam, says nothing about \"right now\", and says the site "
   "is not updating", _n6 == ["the health check has not run for 26 hours"]
   and "## Right now\n- Can't say: the health check has not run for 26 hours." in _b6
   and "**Is the site still updating?** No: the health check has not run for 26 hours" in _b6, _n6)

section("3. 🔴 ONE ISSUE, UPDATED IN PLACE (the real steps, a stub gh)")
WF = wfparse.effective_workflows(ROOT)["status.yml"]
WRITE, SEND = "Write the weekly status", "Send Sam the weekly status"
STEPS = [(wfparse.step_run(WF, step_name=n) or "").replace("\r", "") for n in (WRITE, SEND)]
_ids = {s.name: s.id for s in wfparse.steps(WF)}
ck("the two steps are read from the workflow as it will be live (%s)" % os.path.relpath(WF, ROOT),
   'python status.py "$BODY"' in STEPS[0] and "gh issue create" in STEPS[1]
   and (wfparse.step_env(WF, step_name=SEND) or {}).get("BODY") == "${{ steps.%s.outputs.body }}" % _ids.get(WRITE))


def drive(issues, closed=()):
    """Both steps, run as GitHub runs them, in a planted tree. -> the gh calls made."""
    t = tree(health_at="2020-01-01T00:00:00Z")      # too old to read: something is posted on any day
    copy_module("status", t, ROOT)
    put(t, "all.json", [{"number": n, "title": s} for n, s in issues])
    put(t, "open.json", [{"number": n, "title": s} for n, s in issues if n not in closed])
    os.makedirs(os.path.join(t, "bin"))
    with open(os.path.join(t, "bin", "gh"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write('#!/bin/bash\nprintf "%s\\n" "$*" >> gh.log\nif [ "$1 $2" = "issue list" ]; then\n'
                 '  case "$*" in *"--state all"*) cat all.json;; *) cat open.json;; esac\nfi\n')
    os.chmod(os.path.join(t, "bin", "gh"), 0o755)
    out = os.path.join(t, "out.txt").replace("\\", "/")
    env = dict(os.environ, GITHUB_OUTPUT=out, TMPDIR=t.replace("\\", "/"), PYTHONUTF8="1",
               PATH=os.path.join(t, "bin") + os.pathsep + os.environ["PATH"])
    env.pop("RUNNER_TEMP", None)
    for i, body in enumerate(STEPS):
        if i:
            env["BODY"] = open(out, encoding="utf-8").read().split("body=", 1)[1].strip()
        with open(os.path.join(t, "step.sh"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        subprocess.run(["bash", "-eo", "pipefail", "step.sh"], cwd=t, env=env, capture_output=True, timeout=300)
    log = os.path.join(t, "gh.log")
    return open(log, encoding="utf-8").read().splitlines() if os.path.exists(log) else []


_c = drive([(7, "Gizmo's Picks - the site is broken")])
_new = [c for c in _c if c.startswith("issue create")]
ck("🔴 the first week opens ONE issue, labelled and assigned to Sam", len(_new) == 1
   and "--label gizmo-watch --title %s --body-file" % TITLE in _new[0] and "--assignee smh0602" in _new[0], _c)
for _closed in ((), (31,)):
    _c = drive([(7, "Gizmo's Picks - the site is broken"), (31, TITLE)], _closed)
    ck("🔴 %s weekly issue is updated in place and the week posted as a comment, never opened twice"
       % ("a CLOSED" if _closed else "the open"), not [c for c in _c if c.startswith("issue create")]
       and any(c.startswith("issue edit 31 --add-label gizmo-watch --add-assignee smh0602") for c in _c)
       and any(c.startswith("issue comment 31 --body-file") for c in _c)
       and (not _closed or "issue reopen 31" in _c), _c)

section("4. 🔴 THE WATCHDOG'S ALERT ENDS WITH WHAT TO DO")
_out = {"healthy": False, "checked_at": "2026-10-12T10:41Z", "repairs": [], "unrepairable": ["record-verify:mlb"],
        "findings": [dict(DEG, why="w", repair=None), {"key": "record-verify:mlb", "severity": "BROKEN",
                     "what": "the MLB Track Record does not add up", "why": "w", "repair": None}]}
_body = W.render(_out)
_tail = _body[_body.rfind("\n---\n"):]
ck("🔴 the alert ENDS with what is wrong, whether the site is updating and the prompt, for its "
   "first BROKEN finding", _body.endswith("```")
   and "**What is wrong:** the MLB Track Record does not add up." in _tail    # BROKEN only
   and "**Is the site still updating?** Yes" in _tail and "check `record-verify:mlb`" in _tail
   and "verify_record.py" in _tail and W.USAGE_CHECK in _tail, _tail[:160])
eq(W.site_updating([{"key": "stopped:mlb", "severity": "BROKEN", "what": "mlb has not updated since Tue 11:11Z"}]),
   "No: mlb has not updated since Tue 11:11Z.", "🔴 ...and it says the site is NOT updating while a league has stopped")
