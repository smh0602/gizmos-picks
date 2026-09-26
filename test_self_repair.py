#!/usr/bin/env python3
"""SELF-REPAIR: HAND THE AGENT A FINDING, AND REMEMBER WHAT IT COULD NOT DO.

🔴 WHAT HAPPENED `[measured 2026-09-26 from the job logs of self-repair
#45-#52]`. runs.json showed five red self-repair runs in 48 hours (#45,
#47, #48, #49, #52), each "Reached maximum number of turns (40)".
  - ALL EIGHT passes were handed issue #42, "T58 and T59 are
    accumulating", whose body says "until then this is a counter, not a
    finding". Nothing was broken, so the agent searched for a defect until
    its 40 turns ran out (5 passes) or stopped empty-handed (3 passes, 19-39
    turns). One of them created a branch to "guard" a counter.
  - The prompt also told it to run the whole suite: about 26 minutes
    (measured locally 2026-09-25, 147 files; the vacuity sweep alone 17) in
    a 30-minute job, and longer than one agent command may run, so it can
    only be run in pieces, a turn each -- a real repair would hit the wall.
  - The step that makes the next pass skip an issue that produced no PR
    never recorded ONCE: its push failed every time (revoked token x5,
    the agent's unstaged edits x2, the agent's branch left checked out x1)
    and it said "nothing to record or nothing changed".

✅ The fix is the task, not the turn count (still 40):
  - a counter says so (`self_repair.COUNTER`, written by `t58_t59.render`)
    and triage never hands one over (driven in test_watch_label.py §7);
  - the prompt asks for the tests the change touches, not the whole suite;
  - the record is written in its own clean checkout, landed by
    push_retry.sh, fails loudly, and counts only a PR opened THIS pass.
⚠️ THE STAGED `docs/upload/self-repair.yml` IS WHAT IS CHECKED: it is the
file Sam uploads, and the deployed one is unchanged until he does.

# @vacuity the watcher marks its progress report as a counter
#   file: t58_t59.py
#   find:     o.append(COUNTER)          # PROGRESS: a counter, not a finding
#   with:     pass
#
# @vacuity 🔴🔴 the record lands through push_retry.sh, or the step fails
#   file: docs/upload/self-repair.yml
#   find:           if ! bash push_retry.sh "self-repair record"; then
#   with:           if false; then
#
# @vacuity 🔴 only a PR opened THIS pass counts as this pass's PR
#   file: docs/upload/self-repair.yml
#   find:                     and p['createdAt'] >= since))
#   with:                     ))
#
# @vacuity the prompt asks for the touched tests, not the whole suite
#   file: docs/upload/self-repair.yml
#   find:               edited. Say what you did NOT change. Do NOT run the whole
#   with:               edited. Run the full suite (`for t in test_*.py; do python $t; done`). Do NOT run the whole
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import self_repair as S  # noqa: E402
import t58_t59 as T  # noqa: E402
import wfparse as W  # noqa: E402
from tcheck import ck, eq, note, section, shown  # noqa: E402

STAGED = os.path.join(ROOT, "docs", "upload", "self-repair.yml")
SRC = W.read(STAGED)
LINES = SRC.splitlines()


def iss(n, body="b"):
    return {"number": n, "title": "t%d" % n, "body": body,
            "createdAt": "2026-09-%02dT00:00:00Z" % n}


CNT = "Two owed tests are accumulating.\n" + S.COUNTER

# ══════════════════════════════════════════════════════════════════════
section("1. THE PICK: A COUNTER IS NEVER A TASK")
# ══════════════════════════════════════════════════════════════════════
eq(S.pick([iss(42, CNT)]), None, "🔴🔴 a queue holding only #42 (a counter) picks nothing")
eq(S.pick([iss(42, CNT), iss(44)])["number"], 44,
   "🔴 a counter ahead of a finding never blocks it")
eq(S.pick([iss(3), iss(9)])["number"], 3, "the queue's own order is kept (oldest first)")
eq(S.pick([iss(7), iss(9)], last="7")["number"], 9,
   "the issue the last pass could not diagnose is skipped...")
eq(S.pick([iss(7)], last="")["number"], 7, "   ...and only when it is named")
eq([S.is_counter(iss(1, "x")), S.is_counter(iss(2, CNT))], [False, True],
   "⛔ absent the marker an issue IS actionable")
ck(S.COUNTER.startswith("<!--") and S.COUNTER.endswith("-->"),
   "   the marker is an HTML comment: invisible on the issue, readable by triage")

# ══════════════════════════════════════════════════════════════════════
section("2. THE WATCHER SAYS WHICH OF ITS REPORTS ARE COUNTERS")
# ══════════════════════════════════════════════════════════════════════
_prog = T.run()
eq(_prog.get("state") not in ("SHRANK", "UNREADABLE", "ANSWERED"), True,
   "the live T58/T59 report is still a progress count (as issue #42 is)")
ck(S.COUNTER in T.render(_prog), "🔴🔴 its progress report carries the counter marker",
   T.render(_prog)[-200:])
_ans = dict(_prog, state="ANSWERED", why="the bar is met",
            t58={"test": "T58", "verdict": "PASS", "why": "w"},
            t59={"test": "T59", "verdict": "PASS", "why": "w"})
ck(S.COUNTER in T.render(_ans), "   an ANSWERED report is not a defect either (it closes itself)")
_shr = dict(_prog, state="SHRANK", why="the sample shrank from 98 to 90 rows")
ck(S.COUNTER not in T.render(_shr),
   "⛔ a SHRANK report IS a finding (rows disappeared) and stays in the queue")
ck(S.COUNTER not in T.render({"state": "UNREADABLE", "why": "x"}),
   "⛔ ...and so is one that could not read the record")

# ══════════════════════════════════════════════════════════════════════
section("3. THE PROMPT ASKS FOR WHAT FITS THE JOB")
# ══════════════════════════════════════════════════════════════════════
_fix = [s for s in W.steps(SRC, "fix") if s.name is None and s.start]
_prompt = "\n".join(LINES[min(s.start for s in _fix):max(s.end for s in _fix)])
_flat = " ".join(_prompt.split())
ck("Something this repo watches is broken" in _flat, "the repair prompt was found")
ck("for t in test_" not in _flat and "Run the full suite" not in _flat,
   "🔴 it no longer asks for the whole suite (about 26 of the job's 30 minutes)")
ck("Run the test files your change touches" in _flat and "`pr-tests` runs all of it" in _flat,
   "   ...it asks for the tests the change touches, and says pr-tests runs the rest")
ck("Do not touch MLB" not in _flat and "MLB IS OPEN FOR REPAIR" in _flat,
   "   ...and it no longer says both 'Do not touch MLB' and 'MLB IS OPEN FOR REPAIR'")
ck(re.search(r"--max-turns 40\b", SRC) is not None,
   "⛔ the turn cap is unchanged: the task was narrowed, not the number raised")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴🔴 THE RECORD LANDS, OR THE STEP SAYS IT DID NOT")
# ══════════════════════════════════════════════════════════════════════
_steps = {s.name: s for s in W.steps(SRC, "fix") if s.name}
CO = _steps.get("A clean checkout to record into")
REC = _steps.get("Record whether this pass produced a pull request")
SINCE = _steps.get("When this pass started")
_co = "\n".join(LINES[CO.start:CO.end]) if CO else ""
_rec_hdr = "\n".join(LINES[REC.start:REC.start + 8]) if REC else ""
ck(bool(CO) and "actions/checkout@" in _co and "path: record" in _co,
   "🔴 the record gets its OWN checkout (no agent edits, no agent branch, a live token)")
ck(bool(REC) and "working-directory:" in _rec_hdr and "'record'" in _rec_hdr
   and CO.start < REC.start,
   "   ...and the record step runs in it")
ck(bool(REC) and "bash push_retry.sh" in (REC.run or "")
   and not re.search(r"\bgit (push|pull --rebase)\b", REC.run or ""),
   "🔴 it lands through push_retry.sh, never a hand-rolled pull/push")
ck(bool(REC) and "nothing to record or nothing changed" not in (REC.run or ""),
   "⛔ the message that hid eight failed pushes is gone")
ck(bool(SINCE) and SINCE.id == "since" and "steps.since.outputs.at" in _rec_hdr,
   "   the step knows when this pass started")

_BIN = None


def drive(prs, reachable=True):
    """Run the STAGED record step's own shell in a throwaway checkout whose
    origin is a local bare repo. -> (rc, output, the record on origin/main)."""
    t = tempfile.mkdtemp(prefix="sr-record-")
    try:
        g = lambda *a, **k: subprocess.run(["git", *a], check=True, capture_output=True,
                                           text=True, **k)
        remote = os.path.join(t, "remote.git")
        g("init", "-q", "--bare", "-b", "main", remote)
        seed = os.path.join(t, "seed")
        g("clone", "-q", remote, seed)
        os.makedirs(os.path.join(seed, "data", "latest"))
        open(os.path.join(seed, "data", "latest", ".keep"), "w").close()
        shutil.copy(os.path.join(ROOT, "push_retry.sh"), seed)
        for c in (["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t",
                                  "commit", "-qm", "seed"], ["push", "-q", "origin", "main"]):
            g(*c, cwd=seed)
        rec = os.path.join(t, "record")
        g("clone", "-q", remote, rec)
        if not reachable:
            g("remote", "set-url", "origin", os.path.join(t, "gone.git"), cwd=rec)
        b = os.path.join(t, "bin")
        os.makedirs(b)
        with open(os.path.join(b, "gh"), "w") as fh:
            fh.write("#!/bin/sh\ncat <<'EOF'\n%s\nEOF\n" % json.dumps(prs))
        os.chmod(os.path.join(b, "gh"), 0o755)
        body = REC.run.replace("${{ needs.triage.outputs.issue }}", "42")
        # ⚠️ PUSH_BACKOFF=0: the unreachable case still makes all five
        #    attempts; it only stops sleeping 45s between them, a run the
        #    vacuity sweep repeats 8 times (`push_retry.sh` default is 3).
        env = dict(os.environ, PATH=b + os.pathsep + os.environ["PATH"],
                   SINCE="2026-09-26T10:00:00Z", GH_TOKEN="x", PUSH_BACKOFF="0")
        p = subprocess.run(["bash", "-c", body], cwd=rec, env=env,
                           capture_output=True, text=True, timeout=120)
        got = None
        chk = os.path.join(t, "check")
        g("clone", "-q", remote, chk)
        f = os.path.join(chk, "data", "latest", "self-repair-last.json")
        if os.path.exists(f):
            got = json.load(open(f))
        return p.returncode, p.stdout + p.stderr, got
    finally:
        shutil.rmtree(t, ignore_errors=True)


if REC and REC.run:
    rc, out, got = drive([{"headRefName": "self-repair/drill",
                           "createdAt": "2026-09-22T05:20:47Z"}])
    ck(rc == 0 and got and got["issue"] == 42 and got["opened_pr"] is False,
       "🔴🔴 a pass that opened no PR is RECORDED on origin/main (opened_pr false)",
       "rc=%s got=%r %s" % (rc, got, shown(out[-300:])))
    ck(got is not None and got.get("opened_pr") is False,
       "   ⚠️ an OLD self-repair PR (the #127 drill) is not this pass's PR")
    rc, out, got = drive([{"headRefName": "self-repair/fix-x",
                           "createdAt": "2026-09-26T10:05:00Z"}])
    ck(rc == 0 and got and got["opened_pr"] is True,
       "   ✅ a PR opened during this pass is recorded as this pass's", "got=%r" % (got,))
    rc, out, got = drive([], reachable=False)
    ck(rc != 0 and "::error::could not record this pass" in out,
       "🔴 a record that cannot be pushed is an error and a red step, never 'nothing to record'",
       "rc=%s %s" % (rc, shown(out[-300:])))
else:
    ck(False, "the staged record step was found")

note("⛔ WHAT THIS DOES NOT CLAIM: that an agent finishes a REAL repair in 40 "
     "turns. It claims the agent is no longer handed a counter, is not asked "
     "to run a suite longer than its job, and that an empty pass is remembered.")
