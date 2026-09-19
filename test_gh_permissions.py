#!/usr/bin/env python3
"""🔴🔴 A JOB THAT CALLS `gh` MUST HOLD THE SCOPE THAT CALL NEEDS.

`[measured 2026-09-19 on the DEPLOYED run 35424213172]` `self-repair.yml`'s
`triage` job held `contents: read` and `pull-requests: read` and called
`gh issue list`. At 05:32:22Z it printed:

    unrepairable findings: 0
    open watcher issues: 0
    nothing unrepairable and no watcher issue open

…while issue **#80** was open and carried the `gizmo-watch` label. The same
query asked with a token that can read issues returns it. The whole point of
PR #73 — turning a red test, a failed run and a vacuous guard into somebody's
task — **fired zero times between merging and this file existing**.

⛔ **WHY NO EXISTING CHECK COULD SEE IT.** `test_watch_label.py` reads the
workflow as text in §1–5 and DRIVES it in §6 — with a stub `gh` on `PATH`,
which has every permission in the world. **Nothing in this repository read a
job's `permissions:` block.** A drive against a stub can only ever prove the
logic, never the grant.

🔴 SO THIS GUARDS THE CLASS, NOT THE INSTANCE. `CLAUDE.md`: *ask what CLASS
the defect belongs to and guard the class where the class is answerable.* It
is answerable — the `gh` sub-command names the noun, the noun names the
scope, and the job declares what it holds. Every job, every workflow, today
and the next one somebody adds.

⚠️ AND THE OTHER HALF WAS THE LINE, NOT THE SCOPE. `2>/dev/null || echo "[]"`
turns *"I was refused"* into *"there is nothing to do"*. §4 drives the real
step with a `gh` that FAILS and requires it to say so and exit non-zero — a
queue you could not read is not an empty queue.

⛔ NO PyYAML. It is not installed on the runner (that is F3, the sibling
finding), so the parse comes from `wfparse.py` — the one hand parser.

# @vacuity 🔴🔴 a job that calls gh without the scope is caught
#   file: .github/workflows/self-repair.yml
#   find:       issues: read
#   with:       # issues: read
#
# @vacuity 🔴 a refused query is not an empty queue
#   file: .github/workflows/self-repair.yml
#   find:                     --jq 'sort_by(.createdAt)' 2>/tmp/ghqueue.err)
#   with:                     --jq 'sort_by(.createdAt)' 2>/dev/null || echo "[]")
"""
import glob
import os
import re
import shutil
import subprocess
import tempfile

import wfparse as W
from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
WFDIR = os.path.join(ROOT, ".github", "workflows")
FILES = sorted(glob.glob(os.path.join(WFDIR, "*.yml")))

# ── the noun names the scope ────────────────────────────────────────────
# ⚠️ `api` is deliberately absent: `gh api /repos/...` can mean anything and
#    a guard that guesses is a guard that accuses. It is REPORTED instead.
NOUN_SCOPE = {
    "issue": "issues",
    "label": "issues",
    "pr": "pull-requests",
    "run": "actions",
    "workflow": "actions",
    "cache": "actions",
    "release": "contents",
    "repo": "contents",
}
READ_VERBS = {"list", "view", "status", "checks", "diff", "download"}
WRITE_VERBS = {"create", "edit", "comment", "close", "reopen", "delete",
               "merge", "ready", "lock", "unlock", "pin", "unpin", "develop",
               "transfer", "rename", "upload", "restore", "add", "remove",
               "set", "clone", "fork", "sync"}
RANK = {None: 0, "none": 0, "read": 1, "write": 2}

_GH = re.compile(r"(?:^|[\s;&|(`$])gh\s+([a-z-]+)(?:\s+([a-z-]+))?")


def strip_comments(sh):
    """Shell source with `#` comments removed, quotes respected.

    🔴 THIS IS THE HALF THAT STOPS A FALSE ACCUSATION. The `triage` job's
    own comment block contains the words *"derives the `gh issue create`"*,
    and a matcher that reads prose as code demands `issues: write` on a job
    that only ever lists. The audit that found the real bug also caught this
    one before it shipped.
    """
    out = []
    for ln in (sh or "").split("\n"):
        q, esc, cut = None, False, None
        for i, ch in enumerate(ln):
            if esc:
                esc = False
                continue
            if ch == "\\" and q != "'":
                esc = True
                continue
            if q:
                if ch == q:
                    q = None
                continue
            if ch in "'\"":
                q = ch
                continue
            if ch == "#" and (i == 0 or ln[i - 1] in " \t"):
                cut = i
                break
        out.append(ln if cut is None else ln[:cut])
    return "\n".join(out)


def calls(sh):
    """Every (noun, verb) `gh` invocation in real shell, comments removed."""
    found = set()
    for m in _GH.finditer(strip_comments(sh)):
        found.add((m.group(1), m.group(2)))
    return found


def needed(sh):
    """{scope: level} this script needs, plus the nouns we cannot judge."""
    want, unknown = {}, set()
    for noun, verb in calls(sh):
        scope = NOUN_SCOPE.get(noun)
        if scope is None:
            unknown.add(noun)
            continue
        lvl = "write" if verb in WRITE_VERBS else (
            "read" if verb in READ_VERBS else "write")
        if RANK[lvl] > RANK.get(want.get(scope)):
            want[scope] = lvl
    return want, unknown


# ════════════════════════════════════════════════════════════════════════
section("1. 🔴 THE `gh` CALLS ARE DERIVED FROM THE WORKFLOWS, NEVER LISTED")
# ════════════════════════════════════════════════════════════════════════
USERS = []          # (file, job, permissions, needed, unknown)
TOTAL = 0
for f in FILES:
    for jb in W.jobs(f):
        sh = "\n".join(st.run or "" for st in W.steps(f, jb.name))
        want, unknown = needed(sh)
        TOTAL += len(calls(sh))
        if want or unknown:
            USERS.append((os.path.basename(f), jb.name, jb.permissions,
                          want, unknown))

note("workflow files parsed: %d; jobs calling gh: %d; distinct gh calls: %d"
     % (len(FILES), len(USERS), TOTAL))
ck("⚠️ there are jobs to judge at all",
   len(USERS) >= 8 and TOTAL >= 10,
   "⛔ a check over an empty set proves nothing (rule 67). If the extractor "
   "breaks, this file must go RED rather than green on nothing. "
   "jobs=%d calls=%d" % (len(USERS), TOTAL))
ck("⚠️ ...and they came from more than one workflow",
   len({u[0] for u in USERS}) >= 5,
   "⛔ rule 246/130: a guard that covers the one file that broke covers "
   "exactly that file. files=%s" % sorted({u[0] for u in USERS}))

# ════════════════════════════════════════════════════════════════════════
section("2. ⛔ PROSE IS NOT CODE")
# ════════════════════════════════════════════════════════════════════════
_PROSE = ("# the operator derives the `gh issue create` call sites\n"
          "echo 'gh issue create is mentioned here too'\n"
          "gh issue list --state open\n")
ck("🔴 a `gh` named only in a COMMENT is not a call",
   ("issue", "create") not in calls(_PROSE),
   "⛔ `self-repair.yml`'s triage job says *\"derives the `gh issue "
   "create`\"* in a comment. A matcher that reads that as code demands "
   "`issues: write` on a job that only lists — and an accusation that is "
   "wrong is rule 238 aimed at the channel that has to be trusted.")
ck("⚠️ ...and the real call on the line below IS found",
   ("issue", "list") in calls(_PROSE),
   "⛔ the other failure: a stripper that eats the code with the comment "
   "would make this whole file vacuous.")
ck("⚠️ a `#` inside a quoted string is not a comment",
   calls("gh issue list --search 'x #1' && gh pr list") ==
   {("issue", "list"), ("pr", "list")},
   "⛔ titles and bodies in this repo contain `#`; cutting there would "
   "truncate the line and lose the call after it. got %s"
   % sorted(calls("gh issue list --search 'x #1' && gh pr list")))

# ════════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 EVERY JOB HOLDS WHAT ITS OWN CALLS NEED")
# ════════════════════════════════════════════════════════════════════════
for fname, jname, perms, want, unknown in USERS:
    ck("⛔ %s/%s declares a permissions block" % (fname, jname),
       bool(perms),
       "🔴 a job that calls `gh` and declares nothing inherits a default "
       "this repository does not control. State it. got %r" % (perms,))
    missing = []
    for scope, lvl in sorted(want.items()):
        if RANK.get(perms.get(scope)) < RANK[lvl]:
            missing.append("%s: %s (has %r)" % (scope, lvl, perms.get(scope)))
    ck("🔴 %s/%s holds every scope it calls" % (fname, jname),
       not missing,
       "⛔ THIS IS THE DEFECT OF 2026-09-19: `gh issue list` under a token "
       "with no `issues` scope returns nothing and the job reads that as an "
       "empty queue. needs=%r has=%r MISSING=%s"
       % (want, perms, missing or "none"))
    if unknown:
        note("⚠️ %s/%s calls `gh %s` — not judgeable from the command line, "
             "so it is reported and not accused"
             % (fname, jname, ", ".join(sorted(unknown))))

TRIAGE = [u for u in USERS if u[0] == "self-repair.yml" and u[1] == "triage"]
ck("🔴🔴 the instance: self-repair triage can READ ISSUES",
   bool(TRIAGE) and TRIAGE[0][2].get("issues") in ("read", "write"),
   "⛔ this is the one that was measured wrong in production. Without it "
   "the queue gate stands down on every pass and the repair channel is "
   "decorative. got %r" % (TRIAGE[0][2] if TRIAGE else None))

# ════════════════════════════════════════════════════════════════════════
section("4. 🔴🔴 AND A REFUSED QUERY IS NOT AN EMPTY ONE — DRIVEN")
# ════════════════════════════════════════════════════════════════════════
SR = os.path.join(WFDIR, "self-repair.yml")
_RUN = W.step_run(SR, step_id="decide")
if _RUN:
    _RUN = re.sub(r"\$\{\{[^}]*\}\}", "", _RUN)
ck("⚠️ the deployed `decide` step was extracted without PyYAML",
   bool(_RUN) and "gizmo-watch" in _RUN and "health.json" in _RUN,
   "⛔ if this cannot be read the drives below check nothing — rule 67. "
   "`wfparse.py` is cross-checked against PyYAML in test_wfparse.py.")


def drive(gh_body, health='{"unrepairable": [], "findings": []}'):
    """Run the real step against a stub `gh`; return (rc, stdout, outputs)."""
    d = tempfile.mkdtemp(prefix="ghperm-")
    try:
        os.makedirs(os.path.join(d, "data", "latest"))
        with open(os.path.join(d, "data/latest/health.json"), "w") as fh:
            fh.write(health)
        b = os.path.join(d, "bin")
        os.makedirs(b)
        with open(os.path.join(b, "gh"), "w") as fh:
            fh.write(gh_body)
        os.chmod(os.path.join(b, "gh"), 0o755)
        out = os.path.join(d, "out")
        open(out, "w").close()
        env = dict(os.environ)
        env["PATH"] = b + os.pathsep + env["PATH"]
        env["GITHUB_OUTPUT"] = out
        p = subprocess.run(["bash", "-c", _RUN], cwd=d, env=env,
                           capture_output=True, text=True, timeout=120)
        got = {}
        for ln in open(out).read().split("\n"):
            if "=" in ln and not ln.startswith(" "):
                k, v = ln.split("=", 1)
                if k in ("go", "issue", "drill"):
                    got[k] = v
        return p.returncode, (p.stdout or "") + (p.stderr or ""), got
    finally:
        shutil.rmtree(d, ignore_errors=True)


_DENY = ("#!/bin/sh\n"
         "echo 'gh: Resource not accessible by integration (HTTP 403)' >&2\n"
         "exit 1\n")
_EMPTY = ("#!/bin/sh\n"
          "case \"$*\" in\n"
          "  *'issue list'*) echo '[]' ;;\n"
          "  *'pr list'*) echo 0 ;;\n"
          "  *) echo '[]' ;;\n"
          "esac\n")

if _RUN:
    rc, log, got = drive(_DENY)
    ck("🔴🔴 a REFUSED `gh issue list` fails the step, loudly",
       rc != 0 and "::error::" in log,
       "⛔ THIS IS THE WHOLE FINDING. `2>/dev/null || echo \"[]\"` made a 403 "
       "indistinguishable from an empty queue, and the gate read the "
       "emptiness as 'nothing to do'. rc=%s error_in_log=%s"
       % (rc, "::error::" in log))
    ck("⛔ ...and it does NOT quietly report a clean queue",
       got.get("go") != "yes" and "open watcher issues: 0" not in log,
       "⛔ standing down is only honest when we actually looked. got=%r" % got)
    ck("⚠️ ...and it names the refusal in words a reader can act on",
       "could not read" in log.lower() and "403" in log,
       "⛔ `::error::` with no cause sends the reader to a log GitHub will "
       "delete. log tail: %r" % log[-200:])

    rc2, log2, got2 = drive(_EMPTY)
    ck("✅ a genuinely empty queue still stands down QUIETLY, rc 0",
       rc2 == 0 and got2.get("go") == "no",
       "⛔ THE OTHER FAILURE, and the one that matters more: a guard that "
       "fires on correct code is not a safe guard. Nothing unrepairable and "
       "no open issue must remain an ordinary, green stand-down. "
       "rc=%s got=%r" % (rc2, got2))
    ck("⛔ ...and that path says nothing alarming",
       "::error::" not in log2,
       "⛔ an error annotation on the normal path is how an alert channel "
       "gets muted. log: %r" % log2[-200:])
