#!/usr/bin/env python3
"""🔴 EVERY WATCHER'S ISSUE CARRIES THE LABEL THE WORK QUEUE READS.

`[measured 2026-09-18]` SIX things watch this repo and exactly ONE of them
could produce a fix. `self-repair.yml` gated on `data/latest/health.json`
alone — written by `watchdog.py`, which reads REPO FILES — so a red test,
a failed run and a vacuous guard were none of them findings in it.
`runs_report.py`'s own header says why: **"a red tick on the Actions tab
is not a file in the repo, so it is invisible to every guard this project
has."** All five became an email and stopped.

✅ The queue is now the watchers' own issues, identified by the label
`gizmo-watch`. ⛔ NOT by title: titles are prose, prose drifts, and this
project has been burned by regex-over-prose before.

🔴🔴 SO THIS FILE IS THE THING THAT STOPS THE QUEUE EMPTYING SILENTLY.
A watcher that files without the label is INVISIBLE to triage — it still
emails Sam, so nothing looks wrong, and its problem simply never becomes
anyone's task. That is the exact failure the whole change exists to end,
arriving by the back door.

⛔ THE CALL SITES ARE DERIVED FROM THE WORKFLOWS, NEVER LISTED. A
hardcoded list is a list that goes stale the first time a watcher is
added — and a new watcher is precisely the one most likely to forget.

# @vacuity 🔴 a watcher that files without the label is caught
#   file: .github/workflows/vacuity.yml
#   find:             gh issue create --label gizmo-watch --title "$TITLE" --body-file /tmp/vacuity.md --assignee smh0602 \
#   with:             gh issue create --title "$TITLE" --body-file /tmp/vacuity.md --assignee smh0602 \
#
# @vacuity ⛔ the label is ensured to exist, so a create cannot fail on it
#   file: .github/workflows/vacuity.yml
#   find:             gh label create gizmo-watch --color 5319e7 --description "filed by a Gizmo's Picks watcher; self-repair triages these" 2>/dev/null || true
#   with:             true
#
# @vacuity 🔴 triage reads the issue queue, not health.json alone
#   file: .github/workflows/self-repair.yml
#   find:           QUEUE=$(gh issue list --state open --label gizmo-watch \
#   with:           QUEUE=$(echo "[]" && false || echo "[]" && true && gh issue list --state open --label nope \
#
# @vacuity 🔴🔴 an update-in-place that does not label is caught
#   file: .github/workflows/vacuity.yml
#   find:             gh issue edit "$NUM" --add-label gizmo-watch --body-file /tmp/vacuity.md
#   with:             gh issue edit "$NUM" --body-file /tmp/vacuity.md
#
# @vacuity ⚠️ the queue is oldest-first, so nothing starves
#   file: .github/workflows/self-repair.yml
#   find:                     --jq 'sort_by(.createdAt)' 2>/tmp/ghqueue.err)
#   with:                     --jq 'reverse' 2>/tmp/ghqueue.err)
"""
import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section

LABEL = "gizmo-watch"
WF = sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")))


def lines(f):
    return io.open(f, encoding="utf-8").read().splitlines()


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 EVERY `gh issue create` SITE IS DERIVED, NEVER LISTED")
# ══════════════════════════════════════════════════════════════════════
sites = []
for f in WF:
    for i, l in enumerate(lines(f), 1):
        s = l.strip()
        # ⛔ A COMMENT IS NOT A CALL SITE. `collect.yml` explains the
        #    fallback in prose containing the same words, and counting it
        #    would be reading prose as code — the same defect this repo
        #    has hit four times.
        if s.startswith("#") or "gh issue create" not in s:
            continue
        sites.append((os.path.basename(f), i, s))

note("workflow files that file an issue: %s"
     % sorted({f for f, _i, _s in sites}))
ck("the call sites are discovered from the workflows",
   len(sites) >= 12,
   "⛔ a hardcoded list goes stale the first time a watcher is added, "
   "and a new watcher is the one most likely to forget. found %d"
   % len(sites))
ck("⚠️ ...across every watcher that files, not just one",
   len({f for f, _i, _s in sites}) >= 6,
   "files: %s" % sorted({f for f, _i, _s in sites}))


# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 A WATCHER MAY NOT FILE WITHOUT THE LABEL")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ THE SHAPE IS A CHAIN, AND THE LAST LINK IS DELIBERATELY BARE:
#       create --label ... --assignee   ||   create --label ...   ||   create
#    ⛔ THE ALERT MUST NEVER BE BLOCKED BY A LABEL PROBLEM. If the label
#    has been deleted, an unlabelled issue still reaches Sam — it is
#    merely invisible to triage, which is strictly better than silence.
# ✅ So the question is not "does every line carry the label" but "does
#    every chain LEAD with it".
chains, bad = [], []
for f in WF:
    ls = lines(f)
    for i, l in enumerate(ls):
        s = l.strip()
        if s.startswith("#") or "gh issue create" not in s:
            continue
        if s.startswith("|| gh issue create"):
            continue                      # a fallback, judged by its head
        chains.append((os.path.basename(f), i + 1, s))
        if "--label %s" % LABEL not in s:
            bad.append((os.path.basename(f), i + 1, s[:70]))

note("issue-filing chains found: %d" % len(chains))
ck("🔴🔴 every chain LEADS with the label",
   not bad,
   "⛔ a watcher that files unlabelled still emails Sam, so nothing looks "
   "wrong — and its problem never becomes anyone's task. That is the "
   "failure this whole change exists to end, by the back door. "
   "Offenders: %s" % (bad,))
ck("⚠️ ...and there is at least one chain to judge",
   len(chains) >= 6,
   "⛔ a check over an empty set proves nothing (rule 67). found %d"
   % len(chains))

# ⛔ AND THE LABEL IS ENSURED TO EXIST WHEREVER ONE IS FILED.
missing_ensure = []
for f in WF:
    src = io.open(f, encoding="utf-8").read()
    if "gh issue create --label %s" % LABEL in src \
       and "gh label create %s" % LABEL not in src:
        missing_ensure.append(os.path.basename(f))
ck("⛔ every filing workflow ensures the label exists first",
   not missing_ensure,
   "🔴 `gh issue create --label X` FAILS if X does not exist, and the "
   "label did not exist in this repo until this change. Ensuring it in "
   "the workflow means no manual one-off step can be forgotten or "
   "undone. Missing: %s" % (missing_ensure,))


# ══════════════════════════════════════════════════════════════════════
section("2b. 🔴🔴 AND SO MUST EVERY PATH THAT UPDATES ONE IN PLACE")
# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 THE CREATE PATH WAS NEVER THE ONE THAT MATTERED.
# `[measured 2026-09-19]` every watcher here files ONE issue and then
# updates it in place for ever — that is the design, and it is why the
# queue deduplicates itself. PR #73 labelled `gh issue create` and left
# `gh issue edit` alone, so **five of the six open watcher issues carried
# no label at all**:
#
#     #80  the test suite is failing         gizmo-watch ✅
#     #69  a guard is not guarding anything  —
#     #44  a workflow is failing             —
#     #42  T58 and T59 are accumulating      —
#     #31  CFBD past the free tier           —
#     #16  the board is not delivering       —
#
# ⛔ #69 IS THE ONE THAT HURTS. It reports the two vacuous guards — the
#    exact thing PR #73 existed to turn into somebody's task — and triage
#    reads the queue BY LABEL, so it could never see it.
# ✅ THE EDIT PATH HEALS THE BACKLOG. `--add-label` is idempotent, so the
#    next run of each watcher puts its own issue into the queue. Nothing
#    has to be relabelled by hand, and nothing has to be closed and
#    refiled.
edits, unlabelled_edits = [], []
for f in WF:
    for i, l in enumerate(lines(f), 1):
        s = l.strip()
        if s.startswith("#") or "gh issue edit " not in s:
            continue
        edits.append((os.path.basename(f), i, s))
        if "--add-label %s" % LABEL not in s:
            unlabelled_edits.append((os.path.basename(f), i, s[:72]))

note("issue UPDATE sites found: %d across %s"
     % (len(edits), sorted({f for f, _i, _s in edits})))
ck("🔴🔴 every `gh issue edit` puts the issue INTO the queue",
   not unlabelled_edits,
   "⛔ an issue created before the label existed is updated for ever and "
   "never relabelled, so it is invisible to triage for ever. This is not "
   "hypothetical: five of six were in exactly that state. "
   "Offenders: %s" % (unlabelled_edits,))
ck("⚠️ ...and there are update sites to judge",
   len(edits) >= 8 and len({f for f, _i, _s in edits}) >= 5,
   "⛔ rule 67, and rule 246: a guard covering one file covers one file. "
   "found %d site(s) across %d file(s)"
   % (len(edits), len({f for f, _i, _s in edits})))

# ⛔ AND THE LABEL MUST EXIST BEFORE THE EDIT RUNS, NOT ONLY BEFORE A
#    CREATE. `gh issue edit --add-label X` FAILS when X does not exist,
#    exactly as `create --label X` does. The ensure used to sit inside
#    the `else` branch, which is the one branch that does not run when
#    an issue already exists.
late_ensure = []
for f in WF:
    ls = lines(f)
    ensure_at = [i for i, l in enumerate(ls)
                 if "gh label create %s" % LABEL in l and not l.strip().startswith("#")]
    for i, l in enumerate(ls):
        if "gh issue edit " not in l or l.strip().startswith("#"):
            continue
        if not any(e < i for e in ensure_at):
            late_ensure.append((os.path.basename(f), i + 1))
ck("⛔ ...and the label is ensured BEFORE every update, not inside the else",
   not late_ensure,
   "🔴 `--add-label` on a label that does not exist is an error, and an "
   "errored edit is a watcher that stopped reporting. Sites with no "
   "ensure above them: %s" % (late_ensure,))


# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 TRIAGE READS THE QUEUE, NOT ONE FILE")
# ══════════════════════════════════════════════════════════════════════
SR = io.open(os.path.join(ROOT, ".github", "workflows", "self-repair.yml"),
             encoding="utf-8").read()
ck("triage asks GitHub for open issues with the label",
   "gh issue list --state open --label %s" % LABEL in SR,
   "⛔ `health.json` is written by watchdog.py, which reads repo files — "
   "a red test, a failed run and a vacuous guard are not in it")
ck("⛔ ...and it does NOT identify them by title",
   "--search" not in SR and "grep -i" not in SR.split("QUEUE=")[-1][:400],
   "titles are prose and prose drifts")
ck("⚠️ the queue is oldest-first, so nothing starves",
   "sort_by(.createdAt)" in SR, "a LIFO queue starves its oldest item")
ck("🔴 the existing health.json path still works",
   "unrepairable" in SR and "UNREP" in SR,
   "⛔ the one detector that already produced fixes must not regress")
ck("...and the gate needs BOTH to be empty before standing down",
   '[ "$UNREP" = "0" ] && [ "$QN" = "0" ]' in SR,
   "either source alone is enough to summon the agent")


# ══════════════════════════════════════════════════════════════════════
section("4. ⛔ THE CAPS, AND THEY ARE NOT LOOSENED")
# ══════════════════════════════════════════════════════════════════════
ck("four passes a day, unchanged",
   len(re.findall(r'^\s*- cron:', SR, re.M)) == 4,
   "⛔ widening the gate means it can fire every pass; making it hourly "
   "as well would be two changes at once. crons=%d"
   % len(re.findall(r'^\s*- cron:', SR, re.M)))
ck("🔴 one self-repair PR at a time, repo-wide",
   'startswith("self-repair/")' in SR and 'OPEN' in SR,
   "⛔ a workflow that opens a fresh PR every four hours is a workflow "
   "whose PRs get ignored")
ck("⚠️ an issue that produced no PR is skipped on the NEXT pass only",
   "self-repair-last.json" in SR,
   "⛔ a permanent skip list is a filtered alert, and rule 238 says a "
   "filtered alert is no alert")
ck("...and the skip is explicitly not forever",
   "not forever" in SR.lower() or "one pass" in SR.lower(),
   "the reasoning has to be where the next reader will look")
# ⛔ AND SOMETHING ACTUALLY WRITES IT. A read with no writer is a skip
#    that never happens — the cap would be decoration.
ck("🔴 a step RECORDS whether the pass produced a PR",
   "Record whether this pass produced a pull request" in SR
   and 'json.dump({"issue"' in SR,
   "⛔ the read of self-repair-last.json is meaningless without a writer")
ck("...and it records the PR-LESS case too, which is the whole point",
   "if: always()" in SR and '"opened_pr": opened' in SR,
   "🔴 the case worth recording is the one where the agent produced "
   "NOTHING, which is the case where the earlier steps failed")
ck("⚠️ ...and it commits ONE named file, never `git add -A`",
   "git add data/latest/self-repair-last.json" in SR
   and "git add -A" not in SR,
   "⛔ this job's tree has just had an agent working in it")
ck("⛔ the drill does not write a skip record",
   "needs.triage.outputs.drill != 'yes'" in SR,
   "a drill is a deliberate bypass, not a diagnosis attempt")

# ⛔ NONE OF THE THINGS THAT WERE NEVER ON THE TABLE.
for _never, _why in (
        ("--auto-merge", "no auto-merge, in any form"),
        ("gh pr merge", "no auto-merge"),
        ("git revert", "no auto-revert"),
        ("git push origin main", "no write access to main")):
    ck("⛔ %s: %r is absent" % (_why, _never), _never not in SR,
       "the agent opens a branch and a PR, exactly as it does today")


# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE AGENT'S RULES ARE IN THE PROMPT, VERBATIM")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ WHITESPACE-NORMALISED, BECAUSE A YAML BLOCK SCALAR WRAPS. The
#    prompt genuinely carries "Sam decides what happens to each", split
#    across two indented lines — my first form compared against the
#    unwrapped string and went RED on a prompt that says exactly the
#    right thing. The question is whether the SENTENCE is there, not how
#    the editor broke the line.
_FLAT = " ".join(SR.split())
for _rule in (
        "You may open ONE pull request. You may not merge it. Sam",
        "NEVER WEAKEN A CHECK TO MAKE IT PASS",
        "EVERY FIX SHIPS WITH A GUARD",
        "Do not touch any workflow file containing",
        "picks/<date>.json",
        "you may NOT delete, skip",
        "Sam decides what happens to each",
        "open no PR"):
    ck("the prompt carries: %r" % _rule[:46],
       " ".join(_rule.split()) in _FLAT,
       "⛔ a prompt that stays silent about the constraint most likely to "
       "be violated is a prompt inviting the violation")

ck("🔴🔴 the vacuity clause forbids clearing the queue by deletion",
   "STRENGTHEN it" in _FLAT and "worst possible version" in _FLAT,
   "⛔ THIS IS THE CLAUSE THAT MATTERS. It turns two three-day-old "
   "vacuous guards into somebody's task WITHOUT handing an agent "
   "permission to delete a check to clear its own queue.")


# ══════════════════════════════════════════════════════════════════════
section("6. 🔴🔴 AND THE GATE IS DRIVEN, NOT READ")
# ══════════════════════════════════════════════════════════════════════
# ⛔ EVERY CHECK ABOVE READS THE WORKFLOW AS TEXT. Text can say all the
#    right things and still not run: the step is shell, the shell calls
#    `python -c`, and a `$(...)` whose program DIES returns the empty
#    string rather than failing. `[measured 2026-09-18, on this very
#    branch]` an earlier draft spliced `$LAST` into python source — empty
#    on the first pass and on every pass after one that opened a PR — so
#    the snippet raised SyntaxError, `PICK` came back empty, and the gate
#    read that as "nothing to do". The widening would have shipped green
#    and fired NEVER, with sections 1–5 all passing.
#
# ✅ SO THE REAL STEP IS EXTRACTED FROM THE REAL YAML AND RUN, against
#    fixture `health.json` files and a stub `gh` on PATH. Rule 66: the
#    thing under test is the deployed text, not a copy of it.
# ⛔ NO NETWORK AND NO GH. The stub answers `issue list` and `pr list`
#    from a temp file; nothing reaches GitHub, and the step runs in a
#    throwaway directory, never in this repo's tree.
import json as _json
import re as _re
import shutil as _shutil
import subprocess as _sp
import tempfile as _tf

_SR = os.path.join(ROOT, ".github", "workflows", "self-repair.yml")
try:
    import yaml as _yaml
    _doc = _yaml.safe_load(io.open(_SR, encoding="utf-8"))
    _step = [s for s in _doc["jobs"]["triage"]["steps"]
             if s.get("id") == "decide"][0]
    # ⚠️ `${{ … }}` is GitHub's, not the shell's, and it is substituted
    #    before the runner ever invokes bash. Emptying it is what the
    #    scheduled path actually sees: `inputs.drill` does not exist on a
    #    schedule, so the drill branch is correctly unreachable here.
    _RUN = _re.sub(r"\$\{\{[^}]*\}\}", "", _step["run"])
except Exception as _e:                      # pragma: no cover
    _RUN = None
    note("⛔ could not extract the decide step: %s: %s"
         % (type(_e).__name__, _e))

ck("⚠️ the `decide` step was extracted from the deployed workflow",
   bool(_RUN) and "gizmo-watch" in _RUN and "health.json" in _RUN,
   "⛔ if this cannot be read, every drive below silently checks nothing "
   "— rule 67. The drives are the only checks here that run the step "
   "rather than read it.")


def _drive(health, queue, last=None, openprs=0):
    """Run the real step in a throwaway dir; return its GITHUB_OUTPUT."""
    d = _tf.mkdtemp(prefix="triage-drive-")
    try:
        os.makedirs(os.path.join(d, "data", "latest"))
        if health is not None:
            _json.dump(health,
                       io.open(os.path.join(d, "data/latest/health.json"),
                               "w", encoding="utf-8"))
        if last is not None:
            _json.dump(last,
                       io.open(os.path.join(d,
                               "data/latest/self-repair-last.json"),
                               "w", encoding="utf-8"))
        _json.dump(queue, io.open(os.path.join(d, "queue.json"), "w",
                                  encoding="utf-8"))
        _bin = os.path.join(d, "bin")
        os.makedirs(_bin)
        _gh = os.path.join(_bin, "gh")
        io.open(_gh, "w", encoding="utf-8").write(
            "#!/bin/sh\n"
            "case \"$*\" in\n"
            "  *'issue list'*) cat %s ;;\n"
            "  *'pr list'*) echo %d ;;\n"
            "  *) echo '[]' ;;\n"
            "esac\n" % (_json.dumps(os.path.join(d, "queue.json")), openprs))
        os.chmod(_gh, 0o755)
        _out = os.path.join(d, "out")
        io.open(_out, "w", encoding="utf-8").close()
        _env = dict(os.environ)
        _env["PATH"] = _bin + os.pathsep + _env["PATH"]
        _env["GITHUB_OUTPUT"] = _out
        _sp.run(["bash", "-c", _RUN], cwd=d, env=_env,
                capture_output=True, text=True, timeout=120)
        got = {}
        for ln in io.open(_out, encoding="utf-8").read().split("\n"):
            if "=" in ln and not ln.startswith(" "):
                k, v = ln.split("=", 1)
                if k in ("go", "drill", "issue"):
                    got[k] = v
        return got
    finally:
        _shutil.rmtree(d, ignore_errors=True)


_CLEAN = {"unrepairable": [], "findings": []}
_BROKEN = {"unrepairable": ["x"],
           "findings": [{"severity": "BROKEN", "repair": None,
                         "what": "the board is stale",
                         "why": "gamelines have not landed since 04:00Z"}]}


def _iss(n, t):
    return {"number": n, "title": t, "body": "b",
            "labels": [{"name": LABEL}],
            "createdAt": "2026-09-%02dT00:00:00Z" % n}


# ⛔ THE FIRST ONE IS THE REGRESSION CHECK, AND IT COMES FIRST ON
#    PURPOSE. This change WIDENS a gate. The way a widening goes wrong is
#    by quietly replacing what was there, so the path that already
#    worked is asserted before any of the new ones.
_CASES = [
    ("🔴🔴 health.json unrepairable STILL fires, with an empty queue",
     dict(health=_BROKEN, queue=[]), "yes", None,
     "⛔ THE EXISTING PATH MUST NOT REGRESS. This is the only thing that "
     "summoned an agent before today, and a widening that breaks it has "
     "made the product worse, not better."),
    ("🔴 a watcher issue alone fires it — health.json clean",
     dict(health=_CLEAN, queue=[_iss(7, "vacuous guard")]), "yes", "7",
     "⛔ THIS IS THE WHOLE TASK. Without it a red test, a failed run and "
     "a vacuous guard can only ever become an email."),
    ("✅ nothing unrepairable and an empty queue stands down",
     dict(health=_CLEAN, queue=[]), "no", None,
     "⛔ a gate that always fires is a gate nobody leaves on"),
    ("⚠️ an issue the last pass could not diagnose is skipped",
     dict(health=_CLEAN, queue=[_iss(7, "v")],
          last={"issue": 7, "opened_pr": False}), "no", None,
     "⛔ four passes a day re-reading the same undiagnosable issue is "
     "four wasted agent runs"),
    ("🔴 ...but only for ONE pass — a pass that opened a PR does not skip",
     dict(health=_CLEAN, queue=[_iss(7, "v")],
          last={"issue": 7, "opened_pr": True}), "yes", "7",
     "⛔ RULE 238: A FILTERED ALERT IS NO ALERT. A permanent skip list "
     "turns this queue back into the email nobody reads."),
    ("⚠️ a skipped issue never blocks another",
     dict(health=_CLEAN, queue=[_iss(7, "v"), _iss(9, "w")],
          last={"issue": 7, "opened_pr": False}), "yes", "9",
     "⛔ one undiagnosable issue at the head of the queue would otherwise "
     "starve everything behind it"),
    ("⚠️ the queue is worked OLDEST first",
     dict(health=_CLEAN, queue=[_iss(3, "old"), _iss(9, "new")]),
     "yes", "3",
     "⛔ newest-first starves the oldest problem forever, which is "
     "exactly the three-day-old vacuous guard this task exists for"),
    ("⛔ one self-repair PR at a time, repo-wide",
     dict(health=_BROKEN, queue=[_iss(7, "v")], openprs=1), "no", None,
     "⛔ an open PR means the fix is written and waiting on Sam, not "
     "missing. This cap is UNCHANGED by this task and is asserted so."),
    ("⚠️ no health report yet is not an excuse to fire",
     dict(health=None, queue=[]), "no", None,
     "⛔ a missing file is a claim about our records, not about the repo"),
]

for _name, _kw, _want_go, _want_issue, _why in _CASES:
    _got = _drive(**_kw) if _RUN else {}
    _ok = (_got.get("go") == _want_go
           and (_want_issue is None or _got.get("issue") == _want_issue))
    ck(_name, _ok,
       "%s got go=%r issue=%r, wanted go=%r issue=%r"
       % (_why, _got.get("go"), _got.get("issue"), _want_go, _want_issue))

note("drove the deployed `decide` step %d time(s) against fixtures — no "
     "network, no gh, nothing written inside this repo" % len(_CASES))
