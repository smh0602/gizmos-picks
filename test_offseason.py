#!/usr/bin/env python3
"""🔴🔴 THE SUITE WITH NO GAME ANYWHERE, ON EVERY PR. `[Sam, 2026-10-30]`

*"we need to fix it for the long term as well not just the short term"*.
`test_board_match.js` read the live MLB board. The season ended, board.json
emptied, the test died on `BOARD.games[0]` and every collect run went red
(#329). #298 and #301 were the same class. Football goes dark in February.

✅ THE CLASS GUARD: pr-tests' `offseason` job empties every league's live
boards on its own checkout (`offseason.py`) and runs the `tests` job's own
loop. This file proves the job is wired and that it BITES: a bench repo
holding the #329 shape is green in the `tests` loop and red in this job.

⛔ A TEST ASKS THE CODE: every verdict here is on a planted tree, except that
§3 asks the real tree's FILE SHAPE (a renamed key would disarm the job
silently). An empty list is still the key, so §3 holds in any season.

# @vacuity 🔴 blank() really empties the lists
#   file: offseason.py
#   find:                     doc[k] = []
#   with:                     pass
#
# @vacuity 🔴🔴 the job really empties the boards before the tests run
#   file: .github/workflows/pr-tests.yml
#   find:           python offseason.py --yes
#   with:           python --version
#
# @vacuity ⛔ a published card is never emptied: it stays when a season ends
#   file: offseason.py
#   find: LATEST = ("data/latest", "data/nfl/latest", "data/ncaaf/latest")
#   with: LATEST = ("data/latest", "data/nfl/latest", "data/ncaaf/latest", "picks")
"""
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

import offseason as O
import wfparse as W
from tcheck import ck, eq, section, shown

ROOT = os.path.dirname(os.path.abspath(__file__))
PR = open(os.path.join(ROOT, ".github", "workflows", "pr-tests.yml"), encoding="utf-8").read()


def put(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with (gzip.open(p, "wt", encoding="utf-8") if p.endswith(".gz") else open(p, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


def read(root, rel):
    p = os.path.join(root, rel)
    with (gzip.open(p, "rt", encoding="utf-8") if p.endswith(".gz") else open(p, encoding="utf-8")) as fh:
        return json.load(fh)


# ══════════════════════════════════════════════════════════════════════
section("1. THE JOB IS THERE, READ-ONLY, AND RUNS THE tests JOB'S OWN LOOP")
# ══════════════════════════════════════════════════════════════════════
_jobs = {j.name: j for j in W.jobs(PR)}
ck("offseason" in _jobs, "pr-tests has an `offseason` job", str(sorted(_jobs)))
_steps = {s.name: s for s in W.steps(PR, "offseason") if s.name}
EMPTY = _steps.get("Empty every league's live boards (locally, never pushed)")
TESTS = _steps.get("Tests, with no game anywhere")
TREE = _steps.get("The tests must not have modified the tree")
ck(EMPTY and TESTS and TREE, "   it has its three steps", str(sorted(_steps)))
ck(not any(s.cond for s in (EMPTY, TESTS, TREE)),
   "🔴 ...none behind an `if:`: it runs in every season, on every PR")
ck(W.permissions(PR) == {"contents": "read"} and not _jobs["offseason"].permissions,
   "   read-only: its local commit can never be pushed")
ck("SUITE_SHARD: rest" in PR.split("  offseason:")[1].split("\n  render:")[0],
   "   ...as the `rest` shard")

# ══════════════════════════════════════════════════════════════════════
section("2. blank(): WHAT A REAL OFF-SEASON EMPTIES, AND NOTHING ELSE")
# ══════════════════════════════════════════════════════════════════════
t = tempfile.mkdtemp(prefix="off-")
try:
    put(t, "data/latest/board.json", {"pulled_at": "x", "games": [1, 2]})
    put(t, "data/nfl/latest/props.json.gz", {"games": [1], "note": "kept"})
    put(t, "data/ncaaf/latest/fb-model.json", {"picks": [1], "win_chances": [2], "record": [3]})
    put(t, "data/nfl/latest/winners.json", {"week": [1], "rows": [2], "record": {"n": 2}})
    put(t, "data/latest/record.json", {"games": [1]})
    put(t, "picks/fb-nfl-latest.json", {"games": [1]})
    got = O.blank(t)
    eq(sorted(got), ["data/latest/board.json:games", "data/ncaaf/latest/fb-model.json:picks",
                     "data/ncaaf/latest/fb-model.json:win_chances", "data/nfl/latest/props.json.gz:games",
                     "data/nfl/latest/winners.json:week"],
       "every dark list present is emptied, in all three leagues; a missing file is no error")
    eq(read(t, "data/latest/board.json"), {"pulled_at": "x", "games": []}, "   the rest of a file is kept")
    eq(read(t, "data/nfl/latest/props.json.gz"), {"games": [], "note": "kept"}, "   a gzip stays a gzip")
    eq(read(t, "data/ncaaf/latest/fb-model.json")["record"], [3], "   the graded record is kept")
    eq(read(t, "data/nfl/latest/winners.json")["rows"], [2], "   so are the graded winners")
    eq((read(t, "data/latest/record.json"), read(t, "picks/fb-nfl-latest.json")),
       ({"games": [1]}, {"games": [1]}),
       "⛔ a graded record and a published card are untouched: nothing rewrites them at a season's end")
finally:
    shutil.rmtree(t, ignore_errors=True)
_r = subprocess.run([sys.executable, os.path.join(ROOT, "offseason.py")], capture_output=True, text=True, cwd=ROOT)
ck(_r.returncode == 2, "⛔ without --yes it refuses, so it can never empty a real tree by accident",
   shown(_r.stdout[-200:]))

# ══════════════════════════════════════════════════════════════════════
section("3. EVERY DARK FILE AND KEY STILL EXISTS, OR THE JOB IS QUIETLY DISARMED")
# ══════════════════════════════════════════════════════════════════════
_missing = []
for _name, _keys in O.DARK.items():
    _docs = [read(ROOT, l + "/" + _name) for l in O.LATEST if os.path.exists(os.path.join(ROOT, l, _name))]
    _missing += ["%s:%s" % (_name, k) for k in _keys if not any(k in d for d in _docs)]
eq(_missing, [], "🔴 no DARK file or key has been renamed out from under the job")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴🔴 IT CATCHES THE #329 SHAPE, WHICH THE tests JOB CANNOT")
# ══════════════════════════════════════════════════════════════════════
PLANT = ("const fs=require('fs');\n"
         "const B=JSON.parse(fs.readFileSync('data/latest/board.json','utf8'));\n"
         "console.log(B.games[0].commence);\n")
SAFE = ("const fs=require('fs');\n"
        "const B=JSON.parse(fs.readFileSync('data/latest/board.json','utf8'));\n"
        "console.log((B.games[0]||{}).commence);\n")


def repo(js):
    d = tempfile.mkdtemp(prefix="off-repo-")
    os.makedirs(os.path.join(d, ".github", "workflows"))
    shutil.copy(os.path.join(ROOT, ".github", "workflows", "pr-tests.yml"),
                os.path.join(d, ".github", "workflows", "pr-tests.yml"))
    for f in ("wfparse.py", "offseason.py", ".gitignore"):
        shutil.copy(os.path.join(ROOT, f), d)
    put(d, "data/latest/board.json", {"games": [{"commence": "soon"}]})
    for n in "abcd":                       # the loop refuses a suite under 4 files
        open(os.path.join(d, "test_%s.py" % n), "w").write("pass\n")
    open(os.path.join(d, "test_live.js"), "w").write(js)
    for c in (["git", "init", "-q"], ["git", "add", "-A"],
              ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"]):
        subprocess.run(c, cwd=d, check=True, capture_output=True)
    return d


def sh(d, body):
    # ⚠️ from a file, never `bash -c` (test_pr_staged.py: Windows cuts a long -c short)
    sd = tempfile.mkdtemp(prefix="off-sh-")
    try:
        step = os.path.join(sd, "step.sh")
        open(step, "w", encoding="utf-8", newline="\n").write(body)
        p = subprocess.run(["bash", "-e", step], cwd=d, capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, SUITE_SHARD="rest", GITHUB_OUTPUT=os.devnull))
    finally:
        shutil.rmtree(sd, ignore_errors=True)
    return p.returncode, p.stdout + p.stderr


def job(d):
    rc, log = sh(d, EMPTY.run)
    if rc:
        return rc, None, log
    trc, tlog = sh(d, TESTS.run)
    krc, klog = sh(d, TREE.run)
    return trc, krc, log + tlog + klog


LOOP = W.step_run(PR, step_name="Tests", job="tests")
d = repo(PLANT)
try:
    rc_now, _log = sh(d, LOOP)
    ck(rc_now == 0, "the `tests` job's loop is GREEN while the board has a game (how it passed all season)",
       shown(_log[-300:]))
    trc, krc, log = job(d)
    ck(trc != 0 and "test_live.js" in log,
       "🔴🔴 the `offseason` job is RED and names the test that needs a game", shown(log[-400:]))
    ck(krc == 0, "   ...and its local commit left the tree clean", shown(log[-300:]))
finally:
    shutil.rmtree(d, ignore_errors=True)
d = repo(SAFE)
try:
    trc, krc, log = job(d)
    ck(trc == 0 and krc == 0, "✅ a test that copes with an empty board stays green", shown(log[-400:]))
finally:
    shutil.rmtree(d, ignore_errors=True)
