#!/usr/bin/env python3
"""EVERY STEP THAT CAN CLOSE OR OVERWRITE AN ISSUE, WHATEVER ITS SHAPE: NO RESULT,
NO ISSUE TOUCHED. `[2026-11-04]`

🔴 WHAT HAPPENED. PR #334 made every three-state watcher (a `look` step's
`state` read into `$STATE`) leave its issue alone on an empty state or an empty
report, and `test_budget_watch.py` §2 sweeps them. It left out the steps of
another shape. Driven on 2026-11-04, the deployed `collect.yml`:
  - "Tell Sam the tests are failing" read an EMPTY rc as green. A run killed or
    cancelled during Tests commented "✅ Resolved" and CLOSED the open issue.
  - the watchdog's alert (id `tell`) closed on any ALERT that was not "True". A
    health.json cut short, or a watchdog.py that does not import, commented
    "✅ Resolved — the watchdog now reports the site healthy" and closed the
    issue. A report that does not RENDER (a finding with no `why`) edited the
    open issue with a 0-byte body, or opened one with none.
  - and a watchdog.py that raised mid-run left the LAST pass's health.json in
    place. The Watchdog step still wrote that verdict as this run's
    (`healthy=True`), and the alert acted on it.

✅ THE CLASS, NOT THE INSTANCE. Every step in every workflow as it will be live
(`wfparse.effective_workflows`: a staged copy wins) whose live lines can close
or overwrite an issue (`gh issue close`, `edit` or `create`; a comment adds and
loses nothing) is either a three-state watcher, swept by `test_budget_watch.py`
§2, or a shape in `SHAPES` below, which says how to give that step no result
and a real one. ⛔ A step in neither FAILS, so a new alert cannot slip past by
having a new shape. Each shape is RUN with a fake `gh`. With no result it
touches no issue, with an issue open and with none. A real result closes or
writes, which proves the harness can see it (rule 67).

⚠️ WHAT THIS CANNOT SEE: an issue written some other way than the `gh issue`
CLI (curl to the API, an action), and a step that writes one only through a
script it calls.

# @vacuity 🔴🔴 an empty rc (Tests never reported) is caught: it closed the issue
#   file: docs/upload/collect.yml
#   find:           if [ -z "$RC" ]; then
#   with:           if false; then
#
# @vacuity 🔴🔴 a Watchdog step that gave no verdict is caught: the stale report closed it
#   file: docs/upload/collect.yml
#   find:           if [ "$HEALTHY" != "True" ] && [ "$HEALTHY" != "False" ]; then
#   with:           if false; then
#
# @vacuity 🔴 ...and an alert that could not be read is not "nothing is broken"
#   file: docs/upload/collect.yml
#   find:           if [ "$ALERT" != "True" ] && [ "$ALERT" != "False" ]; then
#   with:           if false; then
#
# @vacuity 🔴 ...and an alert body nobody wrote goes over no issue
#   file: docs/upload/collect.yml
#   find:           if [ ! -s "$BODY" ]; then
#   with:           if false; then
#
# @vacuity 🔴🔴 a watchdog.py that raised gives no verdict (its health.json is the last pass's)
#   file: docs/upload/collect.yml
#   find:           if [ "$LOOKED" != "0" ]; then
#   with:           if false; then
#
# @vacuity 🔴 ...and the weekly status, the class's third shape, posts no empty body
#   file: docs/upload/status.yml
#   find:           if [ ! -s "$BODY" ]; then
#   with:           if false; then
"""
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile

import wfparse as W
from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
WRITES = re.compile(r"\bgh issue (close|edit|create)\b")
TOUCH = re.compile(r"^issue (create|edit|comment|close|reopen)\b", re.M)


def live(text):
    """Drop whole-line comments (YAML and shell alike)."""
    return "\n".join(l for l in (text or "").splitlines()
                     if not l.lstrip().startswith("#"))


def three_state(run):
    """`test_budget_watch.py` §2's own selection: it sweeps exactly these."""
    return ("gh issue create" in live(run) and "steps.look.outputs.state" in run
            and "$STATE" in run)


def discover(root):
    """-> (three-state [(file, key)], other {(file, key): Step}) for every step
    that can close or overwrite an issue, the staged copy of a workflow winning.
    A step's key is its `id:`, else its `name:`."""
    swept, other = [], {}
    for f, p in sorted(W.effective_workflows(root).items()):
        for s in W.steps(p):
            if not s.run or not WRITES.search(live(s.run)):
                continue
            key = (f, s.id or s.name)
            if three_state(s.run):
                swept.append(key)
            else:
                other[key] = s
    return swept, other


_GH = r'''#!/bin/bash
line="$*"
prev=""
for a in "$@"; do
  if [ "$prev" = "--body-file" ]; then
    if [ -s "$a" ]; then line="$line [body ok]"; else line="$line [body EMPTY]"; fi
  fi
  prev="$a"
done
printf '%s\n' "$line" >> "$GH_LOG"
if [ "$1 $2" = "issue list" ]; then
  case " $* " in
    *" --jq "*) echo "$FAKE_NUM" ;;
    *) if [ -n "$FAKE_NUM" ]; then
         printf '[{"number": %s, "title": "%s"}]\n' "$FAKE_NUM" "$FAKE_TITLE"
       else echo "[]"; fi ;;
  esac
fi
exit 0
'''


def drive(step, num, title="", exprs=None, files=None, env=None):
    """Run a step's REAL shell in a folder of its own, with a fake `gh` first on
    PATH. -> (every `gh` call, one per line; what it wrote to GITHUB_OUTPUT).

    ⚠️ The only substitutions are the expressions GitHub itself would expand:
    `exprs` gives a value to `${{ <expr> }}`, and any other one expands to ''
    (an output nobody wrote). `files` are planted in the folder (the step's
    working directory), and `{d}` in an `env` value is that folder. /tmp is
    pointed at the folder too, so two copies never share a file."""
    d = tempfile.mkdtemp(prefix="alertshape-")
    try:
        here = d.replace(os.sep, "/")
        tmp = os.path.join(d, "tmp")
        os.makedirs(os.path.join(d, "bin"))
        os.makedirs(tmp)
        gh = os.path.join(d, "bin", "gh")
        with open(gh, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(_GH)
        os.chmod(gh, os.stat(gh).st_mode | stat.S_IEXEC)
        body = step.run
        for k, v in (exprs or {}).items():
            body = re.sub(r"\$\{\{\s*%s\s*\}\}" % re.escape(k), lambda _m: v, body)
        body = re.sub(r"\$\{\{[^}]*\}\}", "", body).replace("/tmp/", here + "/tmp/")
        with open(os.path.join(d, "step.sh"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        for rel, txt in (files or {}).items():
            p = os.path.join(d, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(txt)
        log, out = os.path.join(d, "gh.log"), os.path.join(d, "out.txt")
        e = dict(os.environ)
        e.update({k: v.replace("{d}", here) for k, v in (env or {}).items()})
        e.update(PATH=os.pathsep.join([os.path.join(d, "bin"),
                                       os.path.dirname(sys.executable), e["PATH"]]),
                 GH_LOG=log, FAKE_NUM=num, FAKE_TITLE=title, GITHUB_OUTPUT=out,
                 RUNNER_TEMP=tmp, TMPDIR=tmp, PYTHONPATH=ROOT, PYTHONUTF8="1")
        subprocess.run(["bash", "step.sh"], cwd=d, env=e, capture_output=True,
                       text=True, timeout=120)
        got = open(log, encoding="utf-8").read() if os.path.exists(log) else ""
        wrote = open(out, encoding="utf-8").read() if os.path.exists(out) else ""
        return got, wrote
    finally:
        shutil.rmtree(d, ignore_errors=True)


def touched(log):
    return [l for l in log.splitlines() if TOUCH.match(l)]


# ══════════════════════════════════════════════════════════════════════
# THE SHAPES. Each says how to give its step NO result (every case must touch
# no issue, open or not) and REAL ones (each must do what it names: proof the
# harness sees a close or a write at all). ⛔ An issue-writing step outside the
# three-state contract that is not here FAILS section 2.
# ══════════════════════════════════════════════════════════════════════
_CLEAN = json.dumps({"healthy": True, "findings": [], "repairs": [],
                     "checked_at": "2026-11-04T12:00:00Z", "et_date": "2026-11-04"})
_BROKEN = json.dumps({"healthy": False, "repairs": [],
                      "checked_at": "2026-11-04T12:00:00Z", "et_date": "2026-11-04",
                      "findings": [{"severity": "BROKEN", "what": "the card is missing",
                                    "why": "no picks file for today"}]})
_HEALTH = "data/latest/health.json"
_WD = "steps.watchdog.outputs.healthy"
_RC, _NAMES = "steps.tests.outputs.rc", "steps.tests.outputs.failed"

SHAPES = {
    ("collect.yml", "Tell Sam the tests are failing"): {
        "title": "Gizmo's Picks - the test suite is failing",
        "real": [
            ("a green suite closes the open issue", "77",
             {"exprs": {_RC: "0", _NAMES: ""}}, r"^issue close 77\b"),
            ("a red suite writes the open issue", "77",
             {"exprs": {_RC: "1", _NAMES: "test_x.py"}}, r"^issue edit 77 .*\[body ok\]"),
            ("...and opens one when none is open", "",
             {"exprs": {_RC: "1", _NAMES: "test_x.py"}}, r"^issue create .*\[body ok\]"),
        ],
        "none": [
            # 🔴 THE DEFECT, DRIVEN. The run was killed or cancelled in Tests, so
            #    the step never wrote `rc`: it closed the issue as "green again".
            ("the Tests step never reported (rc empty)", {"exprs": {_RC: "", _NAMES: ""}}),
        ],
    },
    ("collect.yml", "tell"): {
        "title": "Gizmo's Picks - the watchdog says the site is wrong",
        "real": [
            ("a clean report closes the open issue", "77",
             {"exprs": {_WD: "True"}, "files": {_HEALTH: _CLEAN}}, r"^issue close 77\b"),
            ("a BROKEN report writes the open issue", "77",
             {"exprs": {_WD: "False"}, "files": {_HEALTH: _BROKEN}},
             r"^issue edit 77 .*\[body ok\]"),
            ("...and opens one when none is open", "",
             {"exprs": {_WD: "False"}, "files": {_HEALTH: _BROKEN}},
             r"^issue create .*\[body ok\]"),
        ],
        "none": [
            # 🔴 THE WATCHDOG STEP GAVE NO VERDICT: killed, or watchdog.py raised
            #    (section 3), so health.json is the LAST pass's. Stale, it closed
            #    the issue when it read clean, and opened one when it read BROKEN.
            ("the Watchdog step gave no verdict, a stale clean report",
             {"exprs": {_WD: ""}, "files": {_HEALTH: _CLEAN}}),
            ("the Watchdog step gave no verdict, a stale BROKEN report",
             {"exprs": {_WD: ""}, "files": {_HEALTH: _BROKEN}}),
            ("watchdog.py was not in the repo (verdict 'skipped')",
             {"exprs": {_WD: "skipped"}, "files": {_HEALTH: _CLEAN}}),
            # 🔴 THE ALERT'S OWN READ FAILED: each one closed the issue.
            ("health.json is cut short",
             {"exprs": {_WD: "False"}, "files": {_HEALTH: _BROKEN[:40]}}),
            ("watchdog.py does not import",
             {"exprs": {_WD: "False"},
              "files": {_HEALTH: _BROKEN, "watchdog.py": "raise ImportError('a bad merge')\n"}}),
            ("a finding that is not a finding (alerting() raises)",
             {"exprs": {_WD: "False"},
              "files": {_HEALTH: json.dumps({"healthy": False, "findings": ["x"],
                                             "repairs": []})}}),
            # 🔴 THE ALERT DOES NOT RENDER: it wrote a 0-byte body over the issue.
            ("the alert does not render (a finding with no why)",
             {"exprs": {_WD: "False"},
              "files": {_HEALTH: json.dumps({"healthy": False, "repairs": [],
                                             "checked_at": "2026-11-04T12:00:00Z",
                                             "findings": [{"severity": "BROKEN",
                                                           "what": "x"}]})}}),
        ],
    },
    ("status.yml", "Send Sam the weekly status"): {
        "title": "Gizmo's Picks - weekly status",
        "real": [
            ("the week's body is posted on the issue", "77",
             {"env": {"BODY": "{d}/week.md"}, "files": {"week.md": "the week\n"}},
             r"^issue comment 77 .*\[body ok\]"),
            ("...and opens it when there is none", "",
             {"env": {"BODY": "{d}/week.md"}, "files": {"week.md": "the week\n"}},
             r"^issue create .*\[body ok\]"),
        ],
        "none": [
            ("the write step never reported its file", {"env": {"BODY": ""}}),
            ("status.py wrote nothing", {"env": {"BODY": "{d}/week.md"},
                                         "files": {"week.md": ""}}),
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════
section("1. THE DISCOVERY, ON A PLANTED TREE (every case, every run)")
# ══════════════════════════════════════════════════════════════════════
_t = tempfile.mkdtemp(prefix="alertshape-tree-")
try:
    for _sub in (".github/workflows", "docs/upload"):
        os.makedirs(os.path.join(_t, _sub))
    _head = "on: push\njobs:\n  j:\n    runs-on: x\n    steps:\n"
    open(os.path.join(_t, ".github/workflows/w.yml"), "w").write(
        _head
        + "      - name: Three\n        run: |\n"
          "          STATE='${{ steps.look.outputs.state }}'\n"
          "          [ \"$STATE\" = bad ] && gh issue create --title t --body-file b\n"
        + "      - name: Says only\n        run: |\n          gh issue comment 1 --body hi\n"
        + "      - name: Commented\n        run: |\n          # gh issue close 1\n          echo\n"
        + "      - name: New shape\n        id: fresh\n        run: |\n"
          "          [ \"$X\" = 0 ] && gh issue close 1\n"
        + "      - name: State but no create\n        run: |\n"
          "          STATE='${{ steps.look.outputs.state }}'\n"
          "          [ \"$STATE\" = ok ] && gh issue close 1\n")
    # ⚠️ the STAGED copy wins: live, `v.yml` writes no issue; staged, it does.
    open(os.path.join(_t, ".github/workflows/v.yml"), "w").write(
        _head + "      - name: Staged\n        run: |\n          echo\n")
    open(os.path.join(_t, "docs/upload/v.yml"), "w").write(
        _head + "      - name: Staged\n        run: |\n          gh issue edit 1 --body-file b\n")
    _sw, _ot = discover(_t)
    eq(_sw, [("w.yml", "Three")],
       "a three-state step is left to test_budget_watch.py, exactly as it selects them")
    eq(sorted(_ot), [("v.yml", "Staged"), ("w.yml", "State but no create"),
                     ("w.yml", "fresh")],
       "🔴 every other step that can close or overwrite an issue is found, keyed by id "
       "then name, the staged copy read; a comment and a commented-out call are not")
finally:
    shutil.rmtree(_t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 EVERY ISSUE-WRITING STEP IS A KNOWN SHAPE (the workflows as they will be live)")
# ══════════════════════════════════════════════════════════════════════
SWEPT, OTHER = discover(ROOT)
note("three-state, swept by test_budget_watch.py §2: %s" % sorted(SWEPT))
note("other shapes, swept here: %s" % sorted(OTHER))
ck(len(SWEPT) >= 3 and ("collect.yml", "tell") in OTHER
   and ("collect.yml", "Tell Sam the tests are failing") in OTHER,
   "⚠️ the sweep holds the steps known to write issues (rule 67)")
_unmapped = sorted(set(OTHER) - set(SHAPES))
ck(not _unmapped,
   "⛔ every issue-writing step outside the three-state contract is a shape here",
   "🔴 a step that is neither is a step nobody asks what it does with no "
   "result. Unmapped: %s. Give it a shape below (no result, and a real one)."
   % _unmapped)
_gone = sorted(set(SHAPES) - set(OTHER))
ck(not _gone, "⛔ ...and every shape here is still a step that writes an issue",
   "a shape whose step moved or was renamed asks nothing. Not found: %s" % _gone)

_blind, _wiped = [], []
for _key in sorted(set(SHAPES) & set(OTHER)):
    _shape, _step = SHAPES[_key], OTHER[_key]
    for _label, _num, _kw, _want in _shape["real"]:
        _log, _ = drive(_step, _num, _shape["title"], **_kw)
        if not re.search(_want, _log, re.M):
            _blind.append((_key, _label, touched(_log)))
    for _label, _kw in _shape["none"]:
        for _num in ("77", ""):
            _t = touched(drive(_step, _num, _shape["title"], **_kw)[0])
            if _t:
                _wiped.append((_key, _label, "issue open" if _num else "none open", _t))
ck(not _blind, "🔴🔴 the harness CAN see a close and a write, on each shape's real result",
   "⛔ otherwise 'touched no issue' is true of a step that did nothing at all "
   "(rule 67). Not seen: %s" % _blind)
ck(not _wiped, "🔴🔴 a step with no result touches no issue, open or not",
   "⛔ THIS IS THE DEFECT. 'I could not look' closed an open issue as resolved, "
   "or wrote an empty body over it. Offenders:\n%s"
   % "\n".join("       %s :: %s (%s): %s" % w for w in _wiped))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 THE WATCHDOG'S VERDICT IS THIS RUN'S, OR THERE IS NONE")
# ══════════════════════════════════════════════════════════════════════
# ⛔ The alert acts on `steps.watchdog.outputs.healthy`, so that output must
#    come from a report THIS run wrote. A watchdog.py that raised wrote none,
#    and the health.json beside it is the last pass's. Driven: the Watchdog step
#    with a stand-in watchdog.py, then its output into the alert.
_wf = W.effective_workflows(ROOT).get("collect.yml")
_wd = next((s for s in W.steps(_wf) if s.id == "watchdog"), None) if _wf else None
ck(_wd is not None and "python watchdog.py" in live(_wd.run or ""),
   "⚠️ the Watchdog step was found, and it runs watchdog.py (rule 67)")
if _wd is not None:
    _writes = ("import json, os, sys\n"
               "os.makedirs('data/latest', exist_ok=True)\n"
               "json.dump(%s, open('data/latest/health.json', 'w'))\n")
    _ok = _writes % repr(json.loads(_CLEAN)) + "sys.exit(0)\n"
    _raise = "raise RuntimeError('a check raised')\n"
    _, _out = drive(_wd, "", files={"watchdog.py": _ok, _HEALTH: _BROKEN})
    ck(re.search(r"^healthy=True$", _out, re.M),
       "✅ a watchdog that wrote its report gives that report's verdict",
       "⛔ the other half: a step that never says True would make the alert "
       "leave every issue alone for ever. GITHUB_OUTPUT: %r" % _out)
    _, _out = drive(_wd, "", files={"watchdog.py": _raise, _HEALTH: _CLEAN})
    _verdict = (re.findall(r"^healthy=(.*)$", _out, re.M) or [""])[-1]
    ck(_verdict not in ("True", "False"),
       "🔴🔴 a watchdog.py that raised gives NO verdict, not the last pass's",
       "⛔ its health.json is the last pass's, so `healthy=%s` reported an old "
       "report as this run's. GITHUB_OUTPUT: %r" % (_verdict, _out))
    _tell = OTHER.get(("collect.yml", "tell"))
    if _tell is not None:
        _t = touched(drive(_tell, "77", SHAPES[("collect.yml", "tell")]["title"],
                           exprs={_WD: _verdict}, files={_HEALTH: _CLEAN})[0])
        ck(not _t, "🔴 ...so the alert leaves the open issue alone",
           "⛔ the stale clean report closed it as resolved: %s" % _t)
