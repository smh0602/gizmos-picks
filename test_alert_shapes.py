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
⚠️ AND MY FIRST FIX DROPPED A REAL ONE (found in review, 2026-11-04). It gave a
verdict only from the LAST pass, so a fresh first-pass BROKEN was thrown away
when the re-check after repairing raised, or the run was killed while repairing.
§3 now drives both passes: the first verdict lands before the repairs.

✅ THE CLASS, NOT THE INSTANCE. Every step in every workflow as it will be live
(`wfparse.effective_workflows`: a staged copy wins) whose live lines can close
or overwrite an issue (`gh issue close`, `edit`, `create` or `reopen`, or a
`comment --edit-last`; a plain comment adds and loses nothing) is either a
three-state watcher, swept by `test_budget_watch.py` §2, or a shape in `SHAPES`
below, which says how to give that step no result and a real one. ⛔ A step in
neither FAILS, so a new alert cannot slip past by having a new shape. Steps are
keyed by workflow, job and id (else name), and two steps sharing a key FAIL,
so one cannot hide behind another's name. Each shape is RUN with a fake `gh`.
With no result it touches no issue, with an issue open and with none. A real
result closes or writes, which proves the harness can see it (rule 67).

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
#   find:           if [ "$LOOKED" = "0" ]; then
#   with:           if true; then
#
# @vacuity 🔴🔴 ...and the first pass's verdict lands before the repairs, so a failed re-check keeps it
#   file: docs/upload/collect.yml
#   find:             echo "healthy=$FIRST" >> "$GITHUB_OUTPUT"
#   with:             true
#
# @vacuity 🔴 ...a re-check that raised does not replace it with the stale file's
#   file: docs/upload/collect.yml
#   find:             if [ "$RECHECK" = "0" ]; then
#   with:             if true; then
#
# @vacuity 🔴 ...and a re-check that finished does replace it
#   file: docs/upload/collect.yml
#   find:               echo "healthy=$HEALTHY" >> "$GITHUB_OUTPUT"
#   with:               true
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
WRITES = re.compile(r"\bgh issue (?:close|edit|create|reopen)\b"
                    r"|\bgh issue comment\b[^\n]*--edit-last")
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
    """-> (three-state [key], other {key: Step}, keys held by more than one step)
    for every step that can close or overwrite an issue, the staged copy of a
    workflow winning. A key is (workflow, job, the step's id, else its name)."""
    swept, other, seen, dupes = [], {}, set(), []
    for f, p in sorted(W.effective_workflows(root).items()):
        for j in W.jobs(p):
            for s in W.steps(p, j.name):
                if not s.run or not WRITES.search(live(s.run)):
                    continue
                key = (f, j.name, s.id or s.name)
                if key in seen:
                    dupes.append(key)
                seen.add(key)
                if three_state(s.run):
                    swept.append(key)
                else:
                    other[key] = s
    return swept, other, dupes


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


def drive(step, num, title="", exprs=None, files=None, env=None, keep=None):
    """Run a step's REAL shell in a folder of its own, with a fake `gh` first on
    PATH. -> (every `gh` call, one per line; what it wrote to GITHUB_OUTPUT;
    the text of the file `keep` names in the folder afterwards, or "").

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

        def text(p):
            return open(p, encoding="utf-8").read() if os.path.exists(p) else ""
        return text(log), text(out), text(os.path.join(d, keep)) if keep else ""
    finally:
        shutil.rmtree(d, ignore_errors=True)


def touched(log):
    return [l for l in log.splitlines() if TOUCH.match(l)]


def verdict(output):
    """The `healthy` a step's GITHUB_OUTPUT gives the steps after it: GitHub keeps
    the LAST value written for a name. '' when none was written."""
    return (re.findall(r"^healthy=(.*)$", output, re.M) or [""])[-1]


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
TELL = ("collect.yml", "collect", "tell")

SHAPES = {
    ("collect.yml", "collect", "Tell Sam the tests are failing"): {
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
    TELL: {
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
    ("status.yml", "status", "Send Sam the weekly status"): {
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
          "          [ \"$STATE\" = ok ] && gh issue close 1\n"
        + "      - name: Rewrites the last comment\n        run: |\n"
          "          gh issue comment 1 --edit-last --body-file b\n"
        + "      - name: Reopens\n        run: |\n          gh issue reopen 1\n"
        + "      - name: Twin\n        run: |\n          gh issue close 2\n"
        # ⚠️ A SECOND JOB with a step of the same name is a different step (budget.yml
        #    has two "Tell Sam" steps); one job holding two steps of one name is a
        #    key two steps share, and fails.
        + "  k:\n    runs-on: x\n    steps:\n"
        + "      - name: Twin\n        run: |\n          gh issue close 3\n"
        + "      - name: Dup\n        run: |\n          gh issue close 4\n"
        + "      - name: Dup\n        run: |\n          gh issue edit 4 --body-file b\n")
    # ⚠️ the STAGED copy wins: live, `v.yml` writes no issue; staged, it does.
    open(os.path.join(_t, ".github/workflows/v.yml"), "w").write(
        _head + "      - name: Staged\n        run: |\n          echo\n")
    open(os.path.join(_t, "docs/upload/v.yml"), "w").write(
        _head + "      - name: Staged\n        run: |\n          gh issue edit 1 --body-file b\n")
    _sw, _ot, _du = discover(_t)
    eq(_sw, [("w.yml", "j", "Three")],
       "a three-state step is left to test_budget_watch.py, exactly as it selects them")
    eq(sorted(_ot), [("v.yml", "j", "Staged"), ("w.yml", "j", "Reopens"),
                     ("w.yml", "j", "Rewrites the last comment"),
                     ("w.yml", "j", "State but no create"), ("w.yml", "j", "Twin"),
                     ("w.yml", "j", "fresh"), ("w.yml", "k", "Dup"),
                     ("w.yml", "k", "Twin")],
       "🔴 every other step that can close or overwrite an issue is found, keyed by "
       "workflow, job and id then name, the staged copy read; a reopen and a "
       "`comment --edit-last` count, a plain comment and a commented-out call do not")
    eq(_du, [("w.yml", "k", "Dup")],
       "🔴 ...and two steps of one name in one job are reported, never folded into one")
finally:
    shutil.rmtree(_t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 EVERY ISSUE-WRITING STEP IS A KNOWN SHAPE (the workflows as they will be live)")
# ══════════════════════════════════════════════════════════════════════
SWEPT, OTHER, DUPES = discover(ROOT)
note("three-state, swept by test_budget_watch.py §2: %s" % sorted(SWEPT))
note("other shapes, swept here: %s" % sorted(OTHER))
ck(len(SWEPT) >= 3 and TELL in OTHER
   and ("collect.yml", "collect", "Tell Sam the tests are failing") in OTHER,
   "⚠️ the sweep holds the steps known to write issues (rule 67)")
ck(not DUPES, "⛔ no two issue-writing steps share a key",
   "🔴 a step whose workflow, job and name another step also has is a step this "
   "file would never ask. Give one an `id:`. Shared: %s" % DUPES)
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
        _log = drive(_step, _num, _shape["title"], **_kw)[0]
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
section("3. 🔴🔴 THE WATCHDOG'S VERDICT COMES FROM A PASS THAT FINISHED THIS RUN, OR THERE IS NONE")
# ══════════════════════════════════════════════════════════════════════
# ⛔ The alert acts on `steps.watchdog.outputs.healthy`, so that output must come
#    from a pass of watchdog.py that FINISHED this run. One that raised wrote no
#    report, and the health.json beside it is the last pass's. ⛔ And a finished
#    first pass's verdict must survive what follows it: a re-check that raises, or
#    a run killed while repairing (found in review: the first fix dropped a fresh
#    BROKEN that way). Driven: the Watchdog step with a stand-in watchdog.py that
#    does one thing per call, and a stand-in collect.py that records what the
#    step had already written when the repairs ran. Then the verdict into the alert.
_wf = W.effective_workflows(ROOT).get("collect.yml")
_wd = next((s for s in W.steps(_wf) if s.id == "watchdog"), None) if _wf else None
ck(_wd is not None and "python watchdog.py" in live(_wd.run or ""),
   "⚠️ the Watchdog step was found, and it runs watchdog.py (rule 67)")
_REPORTS = {"clean": json.loads(_CLEAN),
            "broken": dict(json.loads(_BROKEN), repairs=["card"])}


def standin(*acts):
    """A watchdog.py whose n-th run does acts[n]: write the 'clean' or 'broken'
    (one repair listed) report and exit 0, or 'raise' before writing anything."""
    return ("import json, os\n"
            "n = int(open('calls.txt').read()) if os.path.exists('calls.txt') else 0\n"
            "open('calls.txt', 'w').write(str(n + 1))\n"
            "act = %r[min(n, %d)]\n"
            "if act == 'raise':\n"
            "    raise RuntimeError('a check raised')\n"
            "os.makedirs('data/latest', exist_ok=True)\n"
            "json.dump(%r[act], open('data/latest/health.json', 'w'))\n"
            ) % (list(acts), len(acts) - 1, _REPORTS)


_AT_REPAIR = ("import os\n"
              "o = os.environ.get('GITHUB_OUTPUT', '')\n"
              "open('at_repair.txt', 'a').write(open(o).read() if os.path.exists(o) else '')\n")
_tell = OTHER.get(TELL)
if _wd is not None:
    # (what each pass does, the health.json left from the last run, the verdict
    #  wanted, why)
    _CASES = [
        (("clean",), _BROKEN, "True", "a pass that finished gives its verdict"),
        (("raise",), _CLEAN, "", "🔴🔴 a pass that raised gives none, not the last run's"),
        (("broken", "raise"), _CLEAN, "False",
         "🔴🔴 a fresh BROKEN survives a re-check that raised"),
        (("broken", "clean"), _CLEAN, "True", "a re-check that finished replaces it"),
        (("raise", "raise"), json.dumps(_REPORTS["broken"]), "",
         "🔴 no pass finished, though the last run's report listed a repair: none"),
    ]
    _got = {}
    for _acts, _stale, _want, _why in _CASES:
        _, _out, _seen = drive(_wd, "", files={"watchdog.py": standin(*_acts),
                                               "collect.py": _AT_REPAIR, _HEALTH: _stale},
                               keep="at_repair.txt")
        _got[_acts] = (verdict(_out), _seen)
        ck(verdict(_out) == _want, "%s (%s)" % (_why, " then ".join(_acts)),
           "⛔ the alert would act on `healthy=%s`, wanted %r. GITHUB_OUTPUT: %r"
           % (verdict(_out), _want, _out))
    _seen = _got.get(("broken", "raise"), ("", ""))[1]
    ck(bool(_seen) and verdict(_seen) == "False",
       "🔴🔴 ...and the first verdict had landed BEFORE the repairs ran",
       "⛔ a run killed while repairing (each repair may take 15 minutes) would "
       "leave no verdict, and a real BROKEN would reach nobody. GITHUB_OUTPUT as "
       "the repair saw it: %r" % _seen)
    if _tell is not None:
        _title = SHAPES[TELL]["title"]
        _t = touched(drive(_tell, "", _title, exprs={_WD: _got[("broken", "raise")][0]},
                           files={_HEALTH: json.dumps(_REPORTS["broken"])})[0])
        ck(any(l.startswith("issue create") for l in _t),
           "🔴 ...so the alert still opens the issue on that fresh BROKEN",
           "⛔ the regression the review found: %s" % _t)
        for _acts, _stale in ((("raise",), _CLEAN), (("raise", "raise"), json.dumps(_REPORTS["broken"]))):
            for _num in ("77", ""):
                _t = touched(drive(_tell, _num, _title, exprs={_WD: _got[_acts][0]},
                                   files={_HEALTH: _stale})[0])
                ck(not _t, "🔴 ...and with no verdict (%s, %s) the alert touches no issue"
                   % (" then ".join(_acts), "issue open" if _num else "none open"),
                   "⛔ the last run's report closed or opened it: %s" % _t)
