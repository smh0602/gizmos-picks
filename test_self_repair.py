#!/usr/bin/env python3
"""SELF-REPAIR: HAND THE AGENT A FINDING, REMEMBER WHAT IT COULD NOT DO,
AND STOP STARTING IT WHEN IT CANNOT FINISH.

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

🔴🔴 AND AGAIN, ON REAL FINDINGS `[measured 2026-09-28 from the job logs of
self-repair #55-#62]`. Eight passes in 48 hours (9/26 14:58Z to 9/28
11:48Z), every one `"subtype": "error_max_turns"` after 41 turns, 0 PRs,
nothing merged to main in the window. The one-pass skip worked, so the
agent alternated #44 (crons that did not fire) and #188 (a guard red even
unmutated). ✅ The class:
  - STAND DOWN (§5, driven through the staged record and triage steps):
    two passes in a row that end at the turn cap, or run to the end with
    no PR, and the third pass does not start the agent; each issue tried
    gets one comment; a PR merged to main, or a new watcher issue opening,
    re-arms it -- an issue closing keeps it down [Sam's review, PR #195];
  - NOT AGENT-REPAIRABLE (§6): a watcher whose issue no code change can
    clear writes `self_repair.NOT_REPAIRABLE` (the runs watcher, the
    calibration monitor) and triage never hands it over;
  - §7 replays #55-#62 through the staged triage step.

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
#
# @vacuity 🔴🔴 the second pass in a row that could not finish sets the stand-down
#   file: self_repair.py
#   find:     if streak >= STAND_DOWN_AFTER:
#   with:     if False:
#
# @vacuity 🔴🔴 a stood-down triage does not start the agent
#   file: docs/upload/self-repair.yml
#   find:             if [ -n "$WHY" ]; then
#   with:             if false; then
#
# @vacuity 🔴 a pass that ended at the turn cap is counted as one
#   file: self_repair.py
#   find:     if sub == "error_max_turns":
#   with:     if False:
#
# @vacuity a pass that ran to the end and opened no PR counts too
#   file: self_repair.py
#   find:     if sub == "success" or (not sub and agent == "success"):
#   with:     if False:
#
# @vacuity 🔴 each issue the stand-down tried is told it needs a person
#   file: docs/upload/self-repair.yml
#   find:             if gh issue comment "$N" --body-file "$TELL_MD"; then
#   with:             if true; then
#
# @vacuity ...and never told twice
#   file: self_repair.py
#   find:         tell = [n for n in tried if n not in told]
#   with:         tell = list(tried)
#
# @vacuity 🔴 a PR merged to main after the stand-down re-arms it
#   file: self_repair.py
#   find:     if any((m or {}).get("mergedAt") and m["mergedAt"] > since for m in (merged or [])):
#   with:     if False:
#
# @vacuity 🔴 a new watcher issue re-arms it
#   file: self_repair.py
#   find:     if set(key(queue)) - set(int(n) for n in state.get("queue") or []):
#   with:     if False:
#
# @vacuity 🔴🔴 an issue CLOSING keeps it down (the loose rule re-armed #60 and #61)
#   file: self_repair.py
#   find:     if set(key(queue)) - set(int(n) for n in state.get("queue") or []):
#   with:     if set(key(queue)) != set(int(n) for n in state.get("queue") or []):
#
# @vacuity a re-armed agent gets two passes again, not one
#   file: self_repair.py
#   find:         prev.update(streak=0, tried=[], down_since=None)
#   with:         prev.update(down_since=None)
#
# @vacuity ⛔ a refused merged-PR query is not "nothing merged"
#   file: docs/upload/self-repair.yml
#   find:             if [ "$MRC" != "0" ]; then
#   with:             if false; then
#
# @vacuity 🔴🔴 a not-agent-repairable issue is never handed to the agent
#   file: self_repair.py
#   find:             if not is_counter(it) and not is_not_repairable(it)]
#   with:             if not is_counter(it)]
#
# @vacuity 🔴 the runs watcher's issue says it is not agent-repairable
#   file: runs_report.py
#   find:     out.append(PERSON_ONLY)
#   with:     pass
#
# @vacuity ...and so does its waiting-upload body
#   file: runs_report.py
#   find:     lines += ["", PERSON_ONLY]
#   with:     pass
#
# @vacuity 🔴 the calibration monitor's issue says it is not agent-repairable
#   file: calibration.py
#   find:     out.append(NOT_REPAIRABLE)
#   with:     pass
#
# @vacuity the comment's turn count is the workflow's
#   file: self_repair.py
#   find: TURNS = 40
#   with: TURNS = 41
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

import calibration as C  # noqa: E402
import runs_report as RR  # noqa: E402
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
NR = "These crons were DUE and no run carries their stamp.\n" + S.NOT_REPAIRABLE

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
_rec_hdr = "\n".join(LINES[REC.start:REC.start + 12]) if REC else ""
ck(bool(CO) and "actions/checkout@" in _co and "path: record" in _co,
   "🔴 the record gets its OWN checkout (no agent edits, no agent branch, a live token)")
ck(bool(REC) and "working-directory: record" in _rec_hdr and CO.start < REC.start,
   "   ...and the record step runs in it")
ck(bool(REC) and "bash push_retry.sh" in (REC.run or "")
   and not re.search(r"\bgit (push|pull --rebase)\b", REC.run or ""),
   "🔴 it lands through push_retry.sh, never a hand-rolled pull/push")
ck(bool(REC) and "nothing to record or nothing changed" not in (REC.run or ""),
   "⛔ the message that hid eight failed pushes is gone")
ck(bool(SINCE) and SINCE.id == "since" and "steps.since.outputs.at" in _rec_hdr,
   "   the step knows when this pass started")
ck(bool(REC) and "${{" not in (REC.run or "")
   and "AGENT: ${{ steps.agent.outcome }}" in _rec_hdr
   and "RESULT: ${{ steps.agent.outputs.execution_file }}" in _rec_hdr,
   "   ...and how the agent ended, all through env: (nothing spliced into the script)")


def _git(*a, **k):
    return subprocess.run(["git", *a], check=True, capture_output=True, text=True, **k)


def origin(t, state=None):
    """A bare repo standing in for origin/main: push_retry.sh, self_repair.py
    and, when given, the record an earlier pass left there."""
    remote = os.path.join(t, "remote.git")
    _git("init", "-q", "--bare", "-b", "main", remote)
    seed = os.path.join(t, "seed")
    _git("clone", "-q", remote, seed)
    os.makedirs(os.path.join(seed, "data", "latest"))
    open(os.path.join(seed, "data", "latest", ".keep"), "w").close()
    for f in ("push_retry.sh", "self_repair.py"):
        shutil.copy(os.path.join(ROOT, f), seed)
    if state is not None:
        json.dump(state, open(os.path.join(seed, S.STATE), "w"))
    for c in (["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t",
                              "commit", "-qm", "seed"], ["push", "-q", "origin", "main"]):
        _git(*c, cwd=seed)
    return remote


def record_pass(t, remote, prs, issue="42", agent="failure", result=None,
                queue="[42]", reachable=True, result_at="env"):
    """Run the STAGED record step's own shell in a fresh clone of `remote`,
    as one pass of the fix job. -> (rc, output, the comments it posted)."""
    n = sum(1 for x in os.listdir(t) if x.startswith("rec"))
    rec = os.path.join(t, "rec%d" % n)
    _git("clone", "-q", remote, rec)
    if not reachable:
        _git("remote", "set-url", "origin", os.path.join(t, "gone.git"), cwd=rec)
    b = os.path.join(t, "bin%d" % n)
    os.makedirs(b)
    log = os.path.join(t, "comments%d.log" % n)
    prs_f = os.path.join(t, "prs%d.json" % n)
    json.dump(prs, open(prs_f, "w"))
    with open(os.path.join(b, "gh"), "w", newline="\n") as fh:
        fh.write("#!/bin/sh\ncase \"$*\" in\n"
                 "  *'issue comment'*) echo \"COMMENT $3\" >> %s; cat \"$5\" >> %s ;;\n"
                 "  *) cat %s ;;\nesac\n" % (json.dumps(log), json.dumps(log), json.dumps(prs_f)))
    os.chmod(os.path.join(b, "gh"), 0o755)
    tmp = os.path.join(t, "runner%d" % n)
    os.makedirs(tmp)
    res = ""
    if result is not None:
        # ⚠️ the action's `execution_file` output, or -- if that is empty on
        #    a failed step -- the file it logs as saved in RUNNER_TEMP.
        res = os.path.join(tmp, "claude-execution-output.json")
        json.dump(result, open(res, "w"))
        if result_at == "runner_temp":
            res = ""
    # ⚠️ PUSH_BACKOFF=0: the unreachable case still makes all five
    #    attempts; it only stops sleeping between them (`push_retry.sh`).
    env = dict(os.environ, PATH=b + os.pathsep + os.environ["PATH"],
               SINCE="2026-09-26T10:00:00Z", GH_TOKEN="x", PUSH_BACKOFF="0",
               ISSUE=issue, QUEUE=queue, AGENT=agent, RESULT=res, RUNNER_TEMP=tmp)
    step = os.path.join(t, "step%d.sh" % n)
    open(step, "w", encoding="utf-8", newline="\n").write(REC.run)
    p = subprocess.run(["bash", step], cwd=rec, env=env,
                       capture_output=True, text=True, timeout=120)
    said = open(log, encoding="utf-8").read() if os.path.exists(log) else ""
    return p.returncode, p.stdout + p.stderr, said


def on_origin(t, remote):
    """The record as origin/main holds it now, or None."""
    chk = os.path.join(t, "check%d" % len(os.listdir(t)))
    _git("clone", "-q", remote, chk)
    f = os.path.join(chk, S.STATE)
    return json.load(open(f, encoding="utf-8")) if os.path.exists(f) else None


OLD_PR = [{"headRefName": "self-repair/drill", "createdAt": "2026-09-22T05:20:47Z"}]
CAP = [{"type": "system", "subtype": "init"},
       {"type": "result", "subtype": "error_max_turns", "is_error": True, "num_turns": 41}]
DONE = [{"type": "system", "subtype": "init"},
        {"type": "result", "subtype": "success", "is_error": False, "num_turns": 22}]


def one_pass(prs, **kw):
    t = tempfile.mkdtemp(prefix="sr-record-")
    try:
        remote = origin(t)
        rc, out, _said = record_pass(t, remote, prs, **kw)
        return rc, out, on_origin(t, remote)
    finally:
        shutil.rmtree(t, ignore_errors=True)


if REC and REC.run:
    rc, out, got = one_pass(OLD_PR)
    ck(rc == 0 and got and got["issue"] == 42 and got["opened_pr"] is False,
       "🔴🔴 a pass that opened no PR is RECORDED on origin/main (opened_pr false)",
       "rc=%s got=%r %s" % (rc, got, shown(out[-300:])))
    ck(got is not None and got.get("opened_pr") is False,
       "   ⚠️ an OLD self-repair PR (the #127 drill) is not this pass's PR")
    rc, out, got = one_pass([{"headRefName": "self-repair/fix-x",
                              "createdAt": "2026-09-26T10:05:00Z"}])
    ck(rc == 0 and got and got["opened_pr"] is True and got["outcome"] == S.OPENED_PR,
       "   ✅ a PR opened during this pass is recorded as this pass's", "got=%r" % (got,))
    rc, out, got = one_pass([], reachable=False)
    ck(rc != 0 and "::error::could not record this pass" in out,
       "🔴 a record that cannot be pushed is an error and a red step, never 'nothing to record'",
       "rc=%s %s" % (rc, shown(out[-300:])))
else:
    ck(False, "the staged record step was found")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴🔴 TWO PASSES THAT COULD NOT FINISH, AND THE THIRD DOES NOT START")
# ══════════════════════════════════════════════════════════════════════
_DEC = W.step_run(STAGED, step_id="decide")
_DEC = re.sub(r"\$\{\{[^}]*\}\}", "", _DEC) if _DEC else ""
ck("self_repair.py still-down" in _DEC and "self_repair.py down-since" in _DEC,
   "the staged `decide` step was extracted, with its stand-down",
   "rule 67: an unread step is a drive that checks nothing")
CLEAN = {"unrepairable": [], "findings": []}
BROKEN = {"unrepairable": ["x"],
          "findings": [{"severity": "BROKEN", "repair": None, "what": "the board is stale",
                        "why": "gamelines have not landed since 04:00Z"}]}


def triage(state, queue, merged=(), merged_rc=0, health=None):
    """Run the STAGED `decide` step against a stub `gh`. -> its outputs,
    plus `rc` and `log`."""
    d = tempfile.mkdtemp(prefix="sr-triage-")
    try:
        os.makedirs(os.path.join(d, "data", "latest"))
        json.dump(health or CLEAN, open(os.path.join(d, "data", "latest", "health.json"), "w"))
        if state is not None:
            json.dump(state, open(os.path.join(d, S.STATE), "w"))
        json.dump(queue, open(os.path.join(d, "queue.json"), "w"))
        json.dump(list(merged), open(os.path.join(d, "merged.json"), "w"))
        shutil.copy(os.path.join(ROOT, "self_repair.py"), d)
        b = os.path.join(d, "bin")
        os.makedirs(b)
        with open(os.path.join(b, "gh"), "w", newline="\n") as fh:
            fh.write("#!/bin/sh\ncase \"$*\" in\n"
                     "  *'issue list'*) cat queue.json ;;\n"
                     "  *'--state merged'*) cat merged.json; exit %d ;;\n"
                     "  *'pr list'*) echo 0 ;;\n"
                     "  *) echo '[]' ;;\nesac\n" % merged_rc)
        os.chmod(os.path.join(b, "gh"), 0o755)
        out = os.path.join(d, "out")
        open(out, "w").close()
        # ⚠️ from a file: on Windows a `bash -c` script past ~8K characters
        #    is cut short with no error, and this step is past it.
        open(os.path.join(d, "step.sh"), "w", encoding="utf-8", newline="\n").write(_DEC)
        env = dict(os.environ, PATH=b + os.pathsep + os.environ["PATH"], GITHUB_OUTPUT=out)
        p = subprocess.run(["bash", "step.sh"], cwd=d, env=env,
                           capture_output=True, text=True, timeout=90)
        got = {}
        for ln in open(out, encoding="utf-8").read().split("\n"):
            if "=" in ln and not ln.startswith(" "):
                k, v = ln.split("=", 1)
                if k in ("go", "issue", "queue"):
                    got[k] = v
        got["rc"], got["log"] = p.returncode, p.stdout + p.stderr
        return got
    finally:
        shutil.rmtree(d, ignore_errors=True)


# The queue as it stands on 2026-09-28: #44 and #192 marked by their
# watchers, three issues the agent could be handed.
NOW_Q = [iss(4, NR), iss(18), iss(21), iss(22, NR), iss(24)]
NOW_KEY = "[18, 21, 24]"
T5 = tempfile.mkdtemp(prefix="sr-standdown-")
try:
    # ⚠️ origin/main starts from the record on main today (the old format:
    #    no streak), so this is exactly the first two passes after the upload.
    R5 = origin(T5, state={"issue": 188, "opened_pr": False, "at": "2026-09-28T11:54:01Z"})
    rc1, out1, said1 = record_pass(T5, R5, OLD_PR, issue="21", result=CAP, queue=NOW_KEY)
    s1 = on_origin(T5, R5) or {}
    ck(rc1 == 0 and s1.get("outcome") == S.TURN_CAP and s1.get("streak") == 1
       and not s1.get("down_since") and said1 == "",
       "   one pass at the turn cap is counted, read from the agent's own result; "
       "nothing stands down yet", "rc=%s s1=%r %s" % (rc1, s1, shown(out1[-300:])))
    rc2, out2, said2 = record_pass(T5, R5, OLD_PR, issue="18", result=CAP, queue=NOW_KEY,
                                   result_at="runner_temp")
    s2 = on_origin(T5, R5) or {}
    ck(rc2 == 0 and s2.get("streak") == 2 and bool(s2.get("down_since"))
       and s2.get("tried") == [21, 18] and s2.get("queue") == [18, 21, 24],
       "🔴🔴 the SECOND pass in a row at the turn cap sets the stand-down on origin/main "
       "(read from RUNNER_TEMP when the action gives no path)",
       "rc=%s s2=%r %s" % (rc2, s2, shown(out2[-300:])))
    ck(said2.count("COMMENT ") == 2 and "COMMENT 21\n" in said2 and "COMMENT 18\n" in said2
       and said2.count(S.NEEDS_PERSON) == 2 and s2.get("told") == [21, 18],
       "🔴 each issue those passes tried gets ONE comment: \"%s\"" % S.NEEDS_PERSON,
       shown(said2[:300]))

    g3 = triage(s2, NOW_Q)
    ck(g3.get("go") == "no" and g3["rc"] == 0 and "standing down since" in g3["log"],
       "🔴🔴 ...and the THIRD pass does not start the agent", shown(g3["log"][-300:]))
    ck(triage(s2, NOW_Q, health=BROKEN).get("go") == "no",
       "   ...nor for a health.json finding: the stand-down is ahead of both")

    _after = [{"number": 999, "mergedAt": "2099-01-01T00:00:00Z"}]
    _before = [{"number": 187, "mergedAt": "2026-09-26T06:34:11Z"}]
    g = triage(s2, NOW_Q, merged=_after)
    ck(g.get("go") == "yes" and g.get("issue") == "21" and "re-armed" in g["log"],
       "🔴 a pull request merged to main AFTER the stand-down re-arms it",
       "got go=%r issue=%r" % (g.get("go"), g.get("issue")))
    ck(triage(s2, NOW_Q, merged=_before).get("go") == "no",
       "   ...one merged before it does not")
    ck(triage(s2, NOW_Q + [iss(25)]).get("go") == "yes"
       and triage(s2, [q for q in NOW_Q if q["number"] != 24] + [iss(25)]).get("go") == "yes",
       "🔴 a new watcher issue re-arms it -- also when another closed the same pass")
    g = triage(s2, [q for q in NOW_Q if q["number"] != 24])
    ck(g.get("go") == "no" and "standing down since" in g["log"],
       "🔴🔴 an issue CLOSING keeps it down: every issue left was in the queue that just "
       "failed twice [Sam's review, PR #195]", shown(g["log"][-200:]))
    ck(triage(s2, NOW_Q + [iss(26, NR)]).get("go") == "no"
       and triage(s2, NOW_Q + [iss(27, CNT)]).get("go") == "no",
       "   ...but not a not-agent-repairable issue or a counter: the agent would never get either")
    g = triage(s2, NOW_Q, merged=[{"number": 1, "mergedAt": "2026-01-01T00:00:00Z"}], merged_rc=1)
    ck(g["rc"] != 0 and g.get("go") == "no" and "could not read the merged pull requests" in g["log"],
       "⛔ a refused merged-PR query is an error, never 'nothing merged'", shown(g["log"][-200:]))
    ck(g3.get("queue") is None and triage(None, NOW_Q).get("queue") == NOW_KEY,
       "   an armed pass hands the record the queue it picked from (issue numbers only)")

    # a re-armed pass starts from zero, and a second stand-down never re-tells an issue
    rc3, out3, said3 = record_pass(T5, R5, OLD_PR, issue="24", result=CAP, queue="[18, 21, 24, 25]")
    s3 = on_origin(T5, R5) or {}
    ck(rc3 == 0 and s3.get("streak") == 1 and not s3.get("down_since") and said3 == "",
       "   a re-armed agent gets two passes again: one more at the turn cap does not stand it down",
       "s3=%r" % (s3,))
    rc4, out4, said4 = record_pass(T5, R5, OLD_PR, issue="18", result=CAP, queue="[18, 21, 24, 25]")
    s4 = on_origin(T5, R5) or {}
    ck(rc4 == 0 and bool(s4.get("down_since")) and said4.count("COMMENT ") == 1
       and "COMMENT 24\n" in said4 and "COMMENT 18\n" not in said4,
       "🔴 ...and when it stands down again, #24 is told and #18 (told once already) is not",
       shown(said4[:200]))
finally:
    shutil.rmtree(T5, ignore_errors=True)

# how a pass ended, from the agent's own result
_tf = tempfile.mkdtemp(prefix="sr-outcome-")
try:
    def _res(msgs):
        f = os.path.join(_tf, "r%d.json" % len(os.listdir(_tf)))
        json.dump(msgs, open(f, "w"))
        return f
    eq([S.outcome(0, "failure", _res(CAP)), S.outcome(0, "success", _res(DONE)),
        S.outcome(0, "success", None), S.outcome(0, "failure", None),
        S.outcome(1, "failure", _res(CAP))],
       [S.TURN_CAP, S.NO_PR, S.NO_PR, S.ERROR, S.OPENED_PR],
       "how a pass ended: the turn cap; ran to the end with no PR (with or without its "
       "result file); an error; a PR")
finally:
    shutil.rmtree(_tf, ignore_errors=True)
_a, _t = S.advance({}, "7", S.NO_PR, [7], "2026-09-28T00:00:00Z")
_b, _t2 = S.advance(_a, "9", S.NO_PR, [7, 9], "2026-09-28T06:00:00Z")
ck(bool(_b["down_since"]) and _t2 == [7, 9],
   "🔴 two passes that ran to the end and opened no PR stand it down too")
_e, _ = S.advance(_a, "9", S.ERROR, [7, 9], "2026-09-28T06:00:00Z")
_p, _ = S.advance(_a, "9", S.OPENED_PR, [7, 9], "2026-09-28T06:00:00Z")
ck(_e["streak"] == 1 and _p["streak"] == 0 and _p["tried"] == [],
   "   an error (the agent never ran, or crashed) changes nothing; a PR resets the count")

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴🔴 A NOT-AGENT-REPAIRABLE ISSUE IS NEVER HANDED OVER")
# ══════════════════════════════════════════════════════════════════════
eq(S.pick([iss(4, NR), iss(18)])["number"], 18,
   "🔴🔴 #44 (crons late), oldest in the queue, is passed over for #188")
eq([S.pick([iss(4, NR), iss(22, NR)]), S.key([iss(4, NR), iss(18), iss(22, NR)])],
   [None, [18]], "   a queue of only such issues picks nothing, and they are not in its key")
g = triage(None, [iss(4, NR), iss(22, NR)])
ck(g.get("go") == "no" and g["rc"] == 0,
   "🔴 driven: the staged triage stands down on a queue of only #44 and #192",
   shown(g["log"][-200:]))
g = triage(None, [iss(4, NR), iss(18), iss(22, NR)])
eq(g.get("issue"), "18", "   ...and picks #188 from beside them")

_runs = RR.render([{"name": "collect", "at": "2026-09-28T07:40:00Z", "fails_24h": 30, "url": "u"}],
                  [], ["collect"],
                  missed=[{"cron": "4 10 * * *", "file": "collect.yml",
                           "due": "2026-09-28 10:04Z", "late_min": 263}],
                  missing=["mlb-refit"])
ck(S.is_not_repairable({"body": _runs}),
   "🔴 the runs watcher's issue (#44: late crons, unseen and failing workflows) says so",
   _runs[-240:])
ck(S.is_not_repairable({"body": RR.render_stale([{"file": "self-repair.yml", "hours": 50,
                                                  "kind": "update"}])}),
   "   ...and so does its waiting-upload body (only Sam's upload clears it)")
_cal = C.render({"ncaaf": {"state": "UNDER", "why": "the 80-90% band claimed 84.5% and "
                                                    "delivered 59.3% over 27 graded rows"}})
ck(S.is_not_repairable({"body": _cal}),
   "🔴 the calibration monitor's issue (#192) says so", _cal[-240:])
ck(S.NOT_REPAIRABLE.startswith("<!--") and S.NOT_REPAIRABLE.endswith("-->")
   and S.NOT_REPAIRABLE != S.COUNTER,
   "   the marker is an HTML comment, and not the counter's")

_ag = [s for s in W.steps(SRC, "fix") if s.id == "agent"]
_cap = re.search(r"--max-turns (\d+)", "\n".join(LINES[_ag[0].start:_ag[0].end])) if _ag else None
ck(bool(_cap) and "in %s turns" % _cap.group(1) in S.NEEDS_PERSON,
   "   the comment's turn count is the repair agent's own `--max-turns`",
   "%r vs %r" % (_cap and _cap.group(1), S.NEEDS_PERSON))

# ══════════════════════════════════════════════════════════════════════
section("7. THE REPLAY: SELF-REPAIR #55-#62 THROUGH THE STAGED TRIAGE")
# ══════════════════════════════════════════════════════════════════════
# The watcher queue at each run's start (gh issue list, oldest first) and
# health.json's unrepairable count (each run's own triage log). No PR
# merged to main between 9/26 06:34Z and 9/28 11:48Z. #42 carried its
# counter marker from run #56 on (#55's log counted it). Every pass the
# agent starts ends at the turn cap, as all eight did.
_I = {42: "2026-09-17T11:48:45Z", 44: "2026-09-17T12:52:11Z", 188: "2026-09-26T12:14:15Z",
      190: "2026-09-26T15:19:08Z", 191: "2026-09-26T16:41:36Z", 192: "2026-09-27T17:19:14Z"}


def _q(*spec):
    return [{"number": n, "title": "t", "body": {"C": CNT, "N": NR}.get(k, "b"),
             "createdAt": _I[n]} for n, k in spec]


REPLAY = [(55, "2026-09-26T14:58:56Z", 0, _q((42, ""), (44, "N"), (188, ""))),
          (56, "2026-09-26T19:59:14Z", 0, _q((42, "C"), (44, "N"), (188, ""), (190, ""), (191, ""))),
          (57, "2026-09-27T01:34:39Z", 0, _q((42, "C"), (44, "N"), (188, ""), (190, ""), (191, ""))),
          (58, "2026-09-27T10:37:29Z", 0, _q((42, "C"), (44, "N"), (188, ""), (190, ""), (191, ""))),
          (59, "2026-09-27T15:40:31Z", 1, _q((42, "C"), (44, "N"), (188, ""), (190, ""), (191, ""))),
          (60, "2026-09-27T20:15:03Z", 0, _q((42, "C"), (44, "N"), (188, ""), (191, ""), (192, "N"))),
          (61, "2026-09-28T01:46:43Z", 0, _q((42, "C"), (44, "N"), (188, ""), (191, ""), (192, "N"))),
          (62, "2026-09-28T11:48:48Z", 0, _q((42, "C"), (44, "N"), (188, ""), (191, ""), (192, "N")))]
_state = {"issue": 42, "opened_pr": False, "at": "2026-09-26T10:02:27Z"}   # 292aa8d9, run #54
_ran, _picked, _told = [], {}, {}
for _n, _at, _unrep, _queue in REPLAY:
    _g = triage(_state, _queue, health=BROKEN if _unrep else CLEAN)
    if _g.get("go") != "yes":
        continue
    _ran.append(_n)
    _picked[_n] = int(_g["issue"]) if _g.get("issue") else None
    _state, _tell = S.advance(_state, _g.get("issue"), S.TURN_CAP,
                              json.loads(_g.get("queue") or "[]"), _at)
    if _tell:
        _told[_n] = _tell
_stopped = [n for n, *_ in REPLAY if n not in _ran]
eq(_stopped, [57, 58, 59, 60, 61, 62],
   "🔴🔴 of the eight passes, six would not have started: #57 to #62")
eq((_picked, _told), ({55: 188, 56: 190}, {56: [188, 190]}),
   "   the two that start work #188 and #190 (never #44) and tell both; #190 closing "
   "at 19:19Z on 9/27 and #192 opening (not agent-repairable) re-arm nothing")

note("⛔ WHAT THIS DOES NOT CLAIM: that an agent finishes a REAL repair in 40 "
     "turns. It claims the agent is not handed a counter or an issue no code "
     "change can clear, is not asked to run a suite longer than its job, that "
     "every pass is remembered, and that it is not started again after two "
     "passes in a row that could not finish -- until a PR merges to main or a "
     "new watcher issue opens.")
