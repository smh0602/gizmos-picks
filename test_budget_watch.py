#!/usr/bin/env python3
"""
THE WATCHER THAT ASKS WHETHER THE SPEND IS BLOWING THE PLAN.

🔴🔴 THE DEFECT IT SHIPS WITH: `budget.py` computed the spend trajectory
and **no workflow ever ran it.** `[measured 2026-09-15]` Both mentions of
it in `collect.yml` are COMMENTS. A correct tool, maintained for weeks,
reporting to nobody.

⛔ SO THE GUARD CANNOT BE "does the string `budget.py` appear in a
workflow" — that was TRUE THE WHOLE TIME IT WAS BROKEN, and it is still
true of `collect.yml` today. ✅ The guard below asks whether `budget.py`
is REACHABLE from a scheduled workflow along live, non-comment lines, and
it is driven against `collect.yml` — the real file that mentions it in
comments only — to prove the comment-stripper actually bites. `[rule 244:
a stripped comment has passed green in this repo while proving nothing]`

══════════════════════════════════════════════════════════════════════
⚠️ CLASS OR INSTANCE? BOTH, AND THE SPLIT IS STATED RATHER THAN FUDGED.
`CLAUDE.md`: *ask what CLASS the defect belongs to and guard the class
where the class is answerable; guard the instance only when it is not,
and say which you did.*

  ➡️ **CLASS, ASSERTED (section 2).** Every issue-writing workflow in the
     repo must have the three-state shape and must never close an issue
     on "I could not look". That was checked one-file-at-a-time in
     `test_runs_report.py` and `test_calibration.py`, so the THIRD such
     watcher — this one — could have shipped without it, and so could the
     fourth. It is now asked of the directory, and it is asked by RUNNING
     the shell, not by grepping its prose.

  ➡️ **INSTANCE, ASSERTED (section 1).** "Every tool in the repo is run by
     something" is NOT cleanly answerable: measured 2026-09-15, five
     non-test root modules are unreachable and most are legitimately so
     (`t54.py` is research, `wfroutes.py` is a library). ⛔ A check that
     reddened main for those would be a guard firing on correct code,
     which `CLAUDE.md` calls the other failure, not a safe one. ✅ So the
     REACHABILITY MACHINERY is generic, the assertion is about
     `budget.py`, and the rest of the unreachable set is REPORTED by
     `note()` — rule 76 — so the next reader sees `cfbd_budget.py` sitting
     there rather than discovering it in a month.
"""
import glob
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile

from tcheck import ck, note, section

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import budget_watch as B  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
WF_DIR = os.path.join(ROOT, ".github/workflows")


def read(path):
    """File contents, or "" if it is not there.

    🔴 THIS FILE USED TO DIE ON A MISSING `budget.yml`. `[found
    2026-09-15 by deleting it to prove the guard bites]` The exit code was
    right (1) and the message was a `FileNotFoundError` with **0 checks
    run** — so the one defect this file exists to catch produced the least
    informative red available. ⛔ `tcheck.py`'s own header is about
    exactly that: a file that stopped is not a file that answered.
    ✅ A missing artifact is now a FAILED CHECK that says what is missing,
    not a traceback.
    """
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return ""


SRC = read(os.path.join(ROOT, "budget_watch.py"))
WF = read(os.path.join(WF_DIR, "budget.yml"))

PY_FILES = {os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "*.py"))}


def live(text):
    """Drop whole-line comments — YAML `#` and shell `#` alike.

    ⚠️ WHOLE-LINE ONLY, DELIBERATELY. A `#` inside a quoted shell string
    is not a comment, and a stripper clever enough to know the difference
    is a stripper with its own bugs. Every comment in this repo's
    workflows is whole-line, which section 1 MEASURES rather than assumes.
    """
    return "\n".join(l for l in text.splitlines()
                     if not l.lstrip().startswith("#"))


def named(text):
    """Root modules this text invokes or imports."""
    out = {n for n in re.findall(r"\b([a-z_][a-z0-9_]*\.py)\b", text)
           if n in PY_FILES}
    for mod in re.findall(r"^\s*(?:from|import)\s+([a-z_][a-z0-9_]*)",
                          text, re.M):
        if mod + ".py" in PY_FILES:
            out.add(mod + ".py")
    return out


def reachable(wf_dir=WF_DIR):
    """Root modules reachable from a CRON-BEARING workflow, live lines only.

    🔴🔴 A TEST FILE IS NOT A PATH. `[found 2026-09-15 by driving this
    check against the pre-fix repo]` My first version followed test files
    too — and `test_budget.py` names `budget.py`, so **`budget.py` came
    back REACHABLE on the broken repo and the headline guard passed
    green.** ⛔ Rule 67, caught only by running it against the defect.
    ✅ CI running a tool's TESTS is not the tool REPORTING to anybody, so
    the traversal neither starts at a `test_*.py` nor walks into one.
    """
    def ok(f):
        return not os.path.basename(f).startswith("test_")
    seeds = set()
    for p in sorted(glob.glob(os.path.join(wf_dir, "*.yml"))):
        t = open(p, encoding="utf-8").read()
        if not re.search(r"^\s*-?\s*cron:", t, re.M):
            continue          # ⚠️ claude.yml is mention-triggered, not scheduled
        seeds |= {f for f in named(live(t)) if ok(f)}
    seen, frontier = set(seeds), set(seeds)
    while frontier:
        nxt = set()
        for f in frontier:
            p = os.path.join(ROOT, f)
            if os.path.exists(p):
                nxt |= {g for g in named(live(open(p, encoding="utf-8").read()))
                        if ok(g)}
        nxt -= seen
        seen |= nxt
        frontier = nxt
    return seen


def run_blocks(text):
    """(step name, shell body) for every `run: |` block in a workflow."""
    out, lines, name = [], text.splitlines(), "?"
    for i, ln in enumerate(lines):
        m = re.match(r"^\s*- name:\s*(.+)$", ln)
        if m:
            name = m.group(1).strip()
        m = re.match(r"^(\s*)run:\s*\|", ln)
        if not m:
            continue
        ind, body = len(m.group(1)), []
        for nxt in lines[i + 1:]:
            if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= ind:
                break
            body.append(nxt)
        out.append((name, "\n".join(body)))
    return out


section("1. 🔴🔴 THE DEFECT: A TOOL NOTHING RUNS")
# ⛔ THE CHECK THAT WOULD HAVE PASSED THROUGHOUT THE OUTAGE, shown failing
#    to be worth anything at all. `collect.yml` names `budget.py` twice and
#    has never run it once.
ck("🔴🔴 the workflow that runs the spend watcher EXISTS",
   bool(WF),
   "⛔ THIS IS THE DEFECT, AT ITS PLAINEST: no .github/workflows/budget.yml, "
   "so nothing is scheduled to ask what the spend is doing. Everything "
   "below is downstream of this one fact")
_collect = read(os.path.join(WF_DIR, "collect.yml"))
ck("⚠️ collect.yml really does still name budget.py",
   "budget.py" in _collect,
   "⛔ if this stops being true the next check is vacuous — it would be "
   "proving a stripper works on a string that was never there (rule 67)")
ck("🔴🔴 ...and the comment-stripper REMOVES it, on the real file",
   "budget.py" not in live(_collect),
   "⛔ THIS IS THE PROOF THE GUARD BITES. Both mentions in collect.yml "
   "are comments; a stripper that left them would make every check below "
   "pass on the broken repo. `[rule 244 — a stripped comment has passed "
   "green here while proving nothing]`")
_reach = reachable()
ck("🔴🔴 budget.py IS REACHABLE from a scheduled workflow",
   "budget.py" in _reach,
   "⛔ THIS IS THE DEFECT ITSELF. budget.py computes the spend "
   "trajectory and for weeks nothing ran it. Reachable set: %s"
   % sorted(_reach))
ck("✅ ...along the path this PR actually built",
   "budget_watch.py" in named(live(WF)) and "budget.py" in named(live(SRC)),
   "⛔ budget.yml runs budget_watch.py, which runs budget.py. If either "
   "hop is only a comment the chain is decorative")
ck("⚠️ the workflow that reaches it is SCHEDULED, not manual-only",
   bool(re.search(r"^\s*- cron:", WF, re.M)),
   "🔴 a workflow_dispatch-only job reports the trajectory to whoever "
   "remembers to click it — which is the state this PR is fixing")
# ⚠️ REPORTED, NOT ASSERTED — rule 76. See the header on class vs instance.
_orphans = sorted(PY_FILES - _reach - {p for p in PY_FILES
                                       if p.startswith("test_")})
note("⚠️ %d non-test root module(s) reachable from NO scheduled "
     "workflow: %s. ⛔ REPORTED, NOT FAILED (rule 76) — most are library "
     "or research code, and reddening main for them would be a guard "
     "firing on correct code. ➡️ Read the list anyway: `cfbd_budget.py` "
     "is a SECOND budget tool nothing runs, which is the same defect "
     "this file exists for, left for Sam to call."
     % (len(_orphans), _orphans))

section("2. 🔴🔴 THE CLASS: 'I COULD NOT LOOK' MUST NEVER CLOSE AN ISSUE")
# ⛔ ASKED OF THE DIRECTORY, NOT OF THIS FILE. `[CLAUDE.md: a check naming
#    the one file that broke covers exactly that file — shipped twice
#    already, rules 246 and 130]`
# 🔴 AND ASKED BY RUNNING THE SHELL, NOT BY GREPPING IT. A check that
#    asserts the presence of the sentence "leaving any open issue alone"
#    is a check asserting its own prose (rule 249) — it would pass on a
#    step that printed that sentence and then closed the issue anyway.
# ⚠️ SCOPED TO THE THREE-STATE CONTRACT, AND THE SCOPE IS MEASURED.
#    `collect.yml` also opens an issue, but from a DIFFERENT shape — a
#    test-failure alert with its own outputs and no `unknown` state at
#    all. ⛔ Sweeping it in here reddened three checks on a file that is
#    not broken, which is a guard firing on correct code (CLAUDE.md).
#    ✅ So the set is every step that reads a `steps.look.outputs.state`
#    into `$STATE` — the watcher contract itself — which is still
#    DISCOVERED, and still covers a watcher nobody has written yet.
_issue_wf, _other_issue = [], set()
for _p in sorted(glob.glob(os.path.join(WF_DIR, "*.yml"))):
    _t = open(_p, encoding="utf-8").read()
    for _n, _b in run_blocks(_t):
        if "gh issue create" not in live(_b):
            continue
        if "steps.look.outputs.state" in _b and "$STATE" in _b:
            _issue_wf.append((os.path.basename(_p), _n, _b))
        else:
            _other_issue.add(os.path.basename(_p))
ck("⚠️ every three-state watcher in the repo is discovered",
   len(_issue_wf) >= 3,
   "⛔ a check over a set that shrank to nothing passes and proves "
   "nothing (rule 67). Found %s"
   % sorted({f for f, _, _ in _issue_wf}))
note("⚠️ issue-writing steps OUTSIDE the three-state contract, not swept "
     "here: %s. ⛔ collect.yml's test alert has no `unknown` state to get "
     "wrong — it is a different shape, not a broken one, and failing it "
     "would be a guard firing on correct code."
     % (sorted(_other_issue) or "none"))
ck("✅ ...and the new watcher is one of them",
   any(f == "budget.yml" for f, _, _ in _issue_wf),
   "🔴 if budget.yml is not in the swept set, section 2 says nothing "
   "about the file this PR adds. Found %s"
   % sorted({f for f, _, _ in _issue_wf}))


def drive(body, state, open_issue):
    """Run an issue step's real shell with a fake `gh`. Returns its argv log.

    ⛔ THE STEP IS EXECUTED, NOT READ. This is the only way to tell a
    workflow that HANDLES `unknown` from one that merely mentions it.
    """
    d = tempfile.mkdtemp(prefix="budgetwatch-")
    log = os.path.join(d, "gh.log")
    gh = os.path.join(d, "gh")
    with open(gh, "w", encoding="utf-8") as fh:
        fh.write('#!/bin/bash\nprintf "%s\\n" "$*" >> "$GH_LOG"\n'
                 'if [ "$1 $2" = "issue list" ]; then echo "$FAKE_NUM"; fi\n'
                 'exit 0\n')
    os.chmod(gh, os.stat(gh).st_mode | stat.S_IEXEC)
    script = os.path.join(d, "step.sh")
    # ⚠️ The ONLY substitution is the expression GitHub itself would
    #    expand. Everything else is the deployed shell, byte for byte.
    src = re.sub(r"\$\{\{\s*steps\.look\.outputs\.state\s*\}\}", state, body)
    src = re.sub(r"\$\{\{[^}]*\}\}", "x", src)
    open(script, "w", encoding="utf-8").write(src)
    env = dict(os.environ, PATH=d + os.pathsep + os.environ["PATH"],
               GH_LOG=log, FAKE_NUM=(open_issue or ""))
    subprocess.run(["bash", script], env=env, cwd=d,
                   capture_output=True, text=True, timeout=60)
    return open(log, encoding="utf-8").read() if os.path.exists(log) else ""


# 🔴 THE HARNESS IS PROVEN ABLE TO SEE A CLOSE BEFORE IT IS TRUSTED TO
#    REPORT THE ABSENCE OF ONE. ⛔ Otherwise a fake `gh` that never ran at
#    all would make every "does not close" check below pass (rule 67).
# ⚠️ ~~`drive(b, "ok")` must close~~ — REPLACED 2026-09-16, and the
#    replacement is STRICTLY HARDER, not looser. The old form asked "does
#    the OK path close?", which is a PROXY for "can the harness see a
#    close at all?" and it is the wrong question for a watcher whose
#    normal state is a COUNTER: `owed_tests.yml` reports progress for
#    months and resolves on `answered`. ⛔ The fix is not to exempt it.
# ✅ EACH WORKFLOW NOW DECLARES THE STATE THAT RESOLVES IT, and the
#    harness asserts it closes on THAT state **and on no other**. The old
#    check never asked whether `bad` closes an issue — this one does, for
#    every workflow, so a close that migrated onto the alarm path is now
#    caught where before it was invisible.
# ⛔ THE MAP MUST BE COMPLETE. A workflow missing from it FAILS rather
#    than being skipped, so a new watcher cannot slip past by omission.
# ⚠️ EACH VALUE IS THE COMPLETE SET, and every member needs a reason —
#    an undeclared close is a failure, so the map cannot be padded
#    quietly.
# @vacuity a watcher's declared resolving path must really close
#   file: .github/workflows/owed_tests.yml
#   find: gh issue close "$NUM"
#   with: echo "deliberately not closing"
_RESOLVES_ON = {
    "budget.yml": {"ok"}, "calibration.yml": {"ok"}, "cfbd.yml": {"ok"},
    "vacuity.yml": {"ok"},
    # ⚠️ TWO, AND THE SECOND IS DELIBERATE `[PR #19]`. On `coverage` the
    #    run watcher CLOSES the false "a workflow is failing" issue while
    #    opening the coverage one — the whole point of that drop was that
    #    a truncated run list is not an outage. Found by this check on the
    #    day it was written, and it is correct behaviour, not an offender.
    "runs.yml": {"ok", "coverage"},
    # ⚠️ NOT `ok`. Progress is this watcher's normal state for months and
    #    must never close the counter; the bar being met is what resolves
    #    it. See the header of `t58_t59.py`.
    "owed_tests.yml": {"answered"},
}
_STATES = ("ok", "bad", "unknown", "progress", "shrank", "answered",
           "coverage")
_unmapped = sorted({f for f, _, _ in _issue_wf} - set(_RESOLVES_ON))
ck("⛔ every issue-writing workflow declares the state that resolves it",
   not _unmapped,
   "🔴 a workflow absent from the map is a workflow this section says "
   "nothing about — the same silence as an empty sweep. Unmapped: %s"
   % _unmapped)
_blind, _wrong = [], []
for _f, _, _b in _issue_wf:
    _want = _RESOLVES_ON.get(_f)
    if _want is None:
        continue
    _closes = {st for st in _STATES
               if "issue close 77" in drive(_b, st, "77")}
    if not (_want & _closes):
        _blind.append((_f, sorted(_want), sorted(_closes)))
    if _closes - _want:
        _wrong.append((_f, sorted(_closes - _want)))
ck("🔴🔴 the harness CAN observe a close — proven on each one's own path",
   not _blind,
   "⛔ if the fake `gh` is never invoked, 'it did not close the issue' is "
   "true of a step that did nothing at all, and section 2 proves "
   "NOTHING. Workflows whose declared path closed no issue: %s" % _blind)
ck("⛔ ...and NOTHING closes an issue on any OTHER state",
   not _wrong,
   "🔴 THE OLD CHECK NEVER ASKED THIS. A close that migrated onto the "
   "alarm path would resolve the issue at the exact moment it fires. "
   "Offenders: %s" % _wrong)
_closed = [f for f, _, b in _issue_wf
           if "issue close" in drive(b, "unknown", "77")]
ck("🔴🔴 NO issue-writing workflow closes an issue on `unknown`",
   not _closed,
   "⛔ 'I could not look' is not 'everything is fine'. Closing a money "
   "or outage alert because the check itself broke is how a real problem "
   "goes quiet. Offenders: %s" % _closed)
_touched = [f for f, _, b in _issue_wf
            if re.search(r"issue (create|edit|comment)",
                         drive(b, "unknown", "77"))]
ck("⛔ ...and none of them writes an issue on `unknown` either",
   not _touched,
   "🔴 an alert body overwritten with 'could not look' loses the "
   "finding a human still has to act on. Offenders: %s" % _touched)
_nocreate = [f for f, _, b in _issue_wf
             if "issue create" not in drive(b, "bad", "")]
ck("✅ ...and every one of them DOES open an issue on a real finding",
   not _nocreate,
   "⛔ the other half of the contract. A watcher that never opens an "
   "issue is a watcher nobody hears. Silent on `bad`: %s" % _nocreate)

section("3. 🔴 THE PARSER, DRIVEN AGAINST THE REAL budget.py")
# ⛔ NOT AGAINST A FIXTURE I WROTE. `CLAUDE.md`: drive it against the real
#    artifact, not against your expectation of it. This is the check that
#    goes red the day budget.py's output format moves.
_rc, _out, _err = B.run_budget(ROOT)
ck("⚠️ budget.py runs at all from here",
   _rc == 0,
   "⛔ rc=%s err=%s — every check below reads its output" % (_rc, _err[-300:]))
_real = B.parse(_out)
ck("🔴🔴 the parser reads the REAL budget.py output",
   _real.get("state") == "READ",
   "⛔ THIS IS THE FORMAT-DRIFT ALARM. budget.py's output moved and this "
   "parser did not: %s" % _real.get("why"))
ck("✅ ...and the figures it read agree with each other",
   _real.get("state") == "READ"
   and _real["month"] == (_real["mlb_day"] + _real["fb_day"]) * 30,
   "🔴 the cross-check is what makes a prose parser safe. Got %s" % _real)
note("live spend right now: %d/day (mlb %d + football %d) -> %s/month, "
     "%.0f%% of a %s plan, over a %d-day window"
     % (_real.get("day", 0), _real.get("mlb_day", 0), _real.get("fb_day", 0),
        f"{_real.get('month', 0):,}", _real.get("pct", 0),
        f"{_real.get('plan', 0):,}", _real.get("days", 0)))

section("4. 🔴🔴 THE ALARM, DRIVEN BOTH WAYS")


def report(mlb, fb, plan=20000, days=7):
    """A synthetic budget.py report at a chosen spend."""
    tot = (mlb + fb) * 30
    return ("\n".join("  2026-09-%02d    %d credits" % (8 + i, mlb)
                      for i in range(days))
            + "\n  mean of last %d   %d/day   (cron-derived ceiling was 0)\n"
            + "\n".join("  2026-09-%02d    %d credits" % (8 + i, fb)
                        for i in range(days))
            + "\n  mean of last %d   %d/day   (cron-derived CEILING was 1)\n"
            + "MLB (measured)   %d/day   %d/month\n"
            + "FOOTBALL (measured)   %d/day   %d/month\n"
            + "TOTAL (measured)     %d/month of %s  (%d%%)\n"
            ) % (days, mlb, days, fb, mlb, mlb * 30, fb, fb * 30,
                 tot, f"{plan:,}", round(100.0 * tot / plan))


_bar = B.WARN_FRAC * 20000 / 30.0          # 600/day
_over = B.judge(B.parse(report(500, 200)))  # 700/day -> 21,000/mo
ck("🔴🔴 a run-rate past the bar ALARMS",
   _over["state"] == "OVER",
   "⛔ 700/day is 21,000 a month against a 20,000 plan. If this is "
   "silent the whole file is decorative. Got %s" % _over["state"])
ck("✅ ...and the message carries the numbers, not an adjective",
   all(s in _over["why"] for s in ("700", "21,000", "20,000")),
   "🔴 'spend is high' tells Sam nothing he can act on. Got %r"
   % _over["why"])
_fine = B.judge(B.parse(report(300, 139)))  # 439/day -> 13,170/mo, today-ish
ck("✅ a run-rate inside plan is SILENT",
   _fine["state"] == "OK",
   "⛔ a guard that fires on correct code is the other failure, not a "
   "safe one — CLAUDE.md. 439/day is 66%% of plan. Got %s"
   % _fine["state"])
# 🔴 THE BOUNDARY, FROM BOTH SIDES. A bar nobody drives is a bar nobody
#    knows the direction of.
ck("🔴 exactly at the bar alarms, one credit under does not",
   B.judge(B.parse(report(600, 0)))["state"] == "OVER"
   and B.judge(B.parse(report(599, 0)))["state"] == "OK",
   "⛔ 600/day x 30 = 18,000 = 90%% of plan. Got %s / %s"
   % (B.judge(B.parse(report(600, 0)))["state"],
      B.judge(B.parse(report(599, 0)))["state"]))
# 🔴 DRIVEN ON THE REAL REPORT, WHICH TODAY IS EXACTLY THE AWKWARD CASE:
#    measured 67% of plan, cron-derived CEILING 217%. A watcher that read
#    the ceiling would alarm right now, every day, on a working system.
ck("⚠️ a report whose CEILING is over plan but whose MEASUREMENT is not "
   "stays silent",
   _real.get("ceil_pct", 0) > 100 and _real["pct"] < 90
   and B.judge(_real)["state"] == "OK",
   "⛔ budget.py's ceiling is %s%% of plan today and its own author says "
   "in capitals it is NOT A FORECAST — it prices every football props "
   "cron as if it fired on a full slate. Alarming on it would fire every "
   "day forever. measured=%.0f%% ceiling=%s%% verdict=%s"
   % (_real.get("ceil_pct"), _real.get("pct", 0), _real.get("ceil_pct"),
      B.judge(_real)["state"]))
ck("✅ ...and the body still SHOWS the ceiling rather than hiding it",
   "CEILING" in B.render(B.judge(_real)) and "not a\n"
   not in B.render(B.judge(_real)),
   "🔴 the ceiling is the number to reach for before ADDING a cron. Not "
   "alarming on it is not the same as concealing it")

section("5. ⛔ A THIN WINDOW IS NOT A RATE")
_thin = B.judge(B.parse(report(900, 400, days=3)))
ck("🔴🔴 a huge run-rate over THREE days does not alarm",
   _thin["state"] == "NOT_MEASURABLE",
   "⛔ 1,300/day is 195%% of plan and still not a rate — football bills "
   "475 on a Saturday against 30 on a Tuesday. Got %s" % _thin["state"])
ck("✅ ...and it says NOT MEASURABLE, not OK",
   "not a run-rate" in _thin["why"],
   "🔴 'not a pass and not a fail' is the honest third answer; calling a "
   "short window OK would be a false all-clear")
# 🔴🔴 THE EXIT CODE IS WHAT THE WORKFLOW ACTUALLY BRANCHES ON, so it is
#    DRIVEN, not grepped. `[my first version asserted NOT_MEASURABLE
#    appeared before a `return 2` in the source — and matched the TIMEOUT
#    branch instead. A source grep that lands on the wrong line is a
#    check that cannot fail for the right reason.]`
# ✅ Each case runs the REAL budget_watch.py against a REAL subprocess
#    whose stdout is a report of my choosing.
_EXITS = [
    ("a run-rate inside plan", report(300, 100), 0, 0),
    ("a run-rate past the bar", report(500, 200), 0, 1),
    ("a window too thin to read", report(900, 400, days=3), 0, 2),
    ("output this parser cannot read", "nothing like a budget report", 0, 2),
    ("budget.py failing its OWN parse", report(300, 100), 1, 2),
]
for _label, _stdout, _brc, _want in _EXITS:
    _d = tempfile.mkdtemp(prefix="bw-exit-")
    shutil.copy(os.path.join(ROOT, "budget_watch.py"), _d)
    with open(os.path.join(_d, "budget.py"), "w", encoding="utf-8") as _fh:
        _fh.write("import sys\nsys.stdout.write(%r)\nsys.exit(%d)\n"
                  % (_stdout, _brc))
    _p = subprocess.run([sys.executable, os.path.join(_d, "budget_watch.py")],
                        capture_output=True, text=True, timeout=120)
    ck("⛔ %s -> exit %d" % (_label, _want),
       _p.returncode == _want,
       "🔴 the workflow branches on this number and nothing else: 0 CLOSES "
       "an open issue, 1 opens one, 2 leaves it exactly as it is. Got %d"
       % _p.returncode)
note("⛔ EXIT 2 ON A THIN WINDOW DELIBERATELY DIFFERS FROM calibration.py, "
     "which folds its NOT_MEASURABLE into the ok exit. There a thin league "
     "sits beside leagues that ARE measurable; here it is the WHOLE "
     "answer, and exiting 0 would CLOSE a money issue on the strength of "
     "a short window.")
ck("⚠️ the minimum window is a full week, with a measured reason",
   B.MIN_DAYS == 7,
   "⛔ a window that misses a weekend reads football at a fifth of its "
   "rate. Got %d" % B.MIN_DAYS)

section("6. 🔴🔴 FAIL CLOSED: A BROKEN PARSE IS NEVER 'FINE'")
# ⛔ THE MOST DANGEROUS OUTPUT IN THIS REPO IS A FALSE ALL-CLEAR, and a
#    parser of another tool's prose is the likeliest place to produce one.
_good = report(300, 100)
for _name, _txt in [
        ("empty output", ""),
        ("no TOTAL line", _good.replace("TOTAL (measured)", "TOTAL x")),
        ("no MLB line", _good.replace("MLB (measured)", "MLB x")),
        ("no window line", re.sub(r"mean of last \d+", "mean", _good)),
        ("month no longer 30x the day rate",
         _good.replace("300/day   9000/month", "300/day   9999/month")),
        ("total no longer the sum of its halves",
         _good.replace("12000/month of", "999/month of")),
        ("printed %% disagrees with the plan", _good.replace("(60%)", "(12%)")),
        ("a zero plan", _good.replace("of 20,000", "of 0")),
]:
    _v = B.judge(B.parse(_txt))
    ck("⛔ %s -> UNREADABLE" % _name,
       _v["state"] == "UNREADABLE",
       "🔴 a partial parse that still answers OK is the shape that "
       "reports a confident wrong number. Got %s" % _v["state"])
ck("⛔ ...and judge() never raises on rubbish",
   B.judge(None)["state"] == "UNREADABLE"
   and B.judge({})["state"] == "UNREADABLE"
   and B.judge("nonsense")["state"] == "UNREADABLE",
   "🔴 a watcher that dies before it looks reports nothing, which is "
   "indistinguishable from all-clear")
ck("⛔ ...and a non-zero budget.py exit is 'could not look', not 'fine'",
   "rc != 0" in SRC and "not trustworthy" in SRC,
   "🔴 budget.py exits 1 when its own parse of collect.py fails. Its "
   "figures are meaningless then and must not be judged")

section("7. 🔴 THE BAR IS BORROWED FROM THE REPO, NOT INVENTED HERE")
# ⛔ A COST TOOL THAT CONTRADICTS ITSELF ON ONE PAGE is the failure
#    budget.py's own header names. This file RUNS budget.py, so if their
#    bars drift apart the issue body and the tool's own last line disagree.
_bsrc = open(os.path.join(ROOT, "budget.py"), encoding="utf-8").read()
_m = re.search(r"_mo\s*>\s*PLAN\s*\*\s*([\d.]+)", _bsrc)
ck("🔴🔴 WARN_FRAC is budget.py's own bar, read from budget.py",
   _m is not None and abs(float(_m.group(1)) - B.WARN_FRAC) < 1e-9,
   "⛔ budget.py prints '🔴 ABOVE 90%% OF PLAN' at PLAN*%s and this file "
   "judges at %s. The day those differ, the issue and the tool it quotes "
   "say opposite things about the same number"
   % (_m.group(1) if _m else "<not found>", B.WARN_FRAC))
# ✅ AND THE SECOND, INDEPENDENT NUMBER IT COINCIDES WITH.
_csrc = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
_plan = int(re.search(r'MONTHLY_PLAN = int\(os\.environ\.get\('
                      r'"ODDS_MONTHLY_PLAN", "(\d+)"\)\)', _csrc).group(1))
_flat = int(_plan / 31 * 0.93)
ck("✅ ...and it lands on collect.py's own FLAT_DAILY_CAP",
   abs(B.WARN_FRAC * _plan / 30.0 - _flat) <= 1,
   "⛔ THE BAR HAS TO MEAN SOMETHING. 90%% of a %d plan over 30 days is "
   "%.0f/day; collect.py rations itself to %d/day. They agree, which is "
   "why the alarm reads 'spend has reached the allowance the collector "
   "was designed around' rather than 'a number I liked'"
   % (_plan, B.WARN_FRAC * _plan / 30.0, _flat))
ck("⛔ the body tells a 3am reader NOT to fix it by retiming a cron",
   "retiming" in B.render(_over) and "MLB crons keep running"
   in B.render(_over),
   "🔴 CLAUDE.md: the deployed MLB crons keep running, and nothing in "
   "the schedule is to be disabled, retimed or repriced. The agent most "
   "likely to read this issue is the one that needs telling")
ck("⛔ ...and not by moving the bar either",
   "changing the bar" in B.render(_over),
   "🔴 a check may only change when it asks the WRONG question, and the "
   "replacement must be harder to pass")

section("8. ⚠️ THE WORKFLOW'S OWN SHAPE")
ck("⚠️ it is daily, off :00 and :30",
   re.search(r'- cron: "(\d+) 13 \* \* \*"', WF)
   and re.search(r'- cron: "(\d+) ', WF).group(1) not in ("0", "00", "30"),
   "⛔ a rate that moves once a day asked hourly is 24 identical answers "
   "and an issue nobody reads; :00 and :30 slots get dropped")
_mins = {c.split()[0] for c in re.findall(r'- cron: "([^"]+)"', WF)}
_others = set()
for _p in glob.glob(os.path.join(WF_DIR, "*.yml")):
    if os.path.basename(_p) == "budget.yml":
        continue
    for _c in re.findall(r'- cron: "([^"]+)"', open(_p, encoding="utf-8").read()):
        _f = _c.split()
        if _f[1] in ("13", "*"):
            _others.add(_f[0])
ck("⚠️ ...and its minute collides with nothing already in that hour",
   not (_mins & _others),
   "🔴 GitHub drops runs in congested slots; stacking a new cron on an "
   "occupied minute is asking for it. Taken in hour 13: %s, ours: %s"
   % (sorted(_others), sorted(_mins)))
ck("⛔ the judgement is in Python, not in the shell step",
   "budget_watch.py" in WF and "PLAN" not in live(WF)
   and "0.9" not in live(WF),
   "🔴 rule 66 — a shell step that decides what counts as over-budget is "
   "a second copy of the judgement, and it is the copy no test reaches")
ck("⚠️ the run carries its cron so runs_report can attribute it",
   "event.schedule" in WF and "[cron " in WF,
   "⛔ ledger rule 271 — runs_report.py reads run-name back to tell a "
   "landed cron from a dropped one. Unstamped, it is seen but not "
   "attributable")
ck("⚠️ it has its own concurrency group",
   re.search(r"concurrency:\s*\n\s*group: budget", WF),
   "⛔ CLAUDE.md — a shared group silently cancels queued scheduled runs "
   "when someone triggers a job by hand")
ck("💰 it spends nothing: no Odds API key, no Claude action",
   "ODDS_API_KEY" not in WF and "anthropics/claude-code-action" not in WF,
   "🔴 this is a FREE watcher. A key in it would make reporting the "
   "spend cost spend")
ck("⛔ and it never reads MLB product state — only billing metadata",
   "picks/" not in live(WF) and "record.json" not in live(WF)
   and "card.py" not in live(WF),
   "⚠️ budget.py reads `credits_used` out of snapshots — what the "
   "ACCOUNT was billed, never a pick, a card, a projection or a record. "
   "See the PR body: whether that counts as 'a scheduled check that "
   "reads MLB state' is Sam's call, and it is asked rather than assumed")

note("⛔ WHAT THIS DOES NOT CLAIM: that an alarm means anything is "
     "broken, or that silence means the plan is safe forever. It claims "
     "the MEASURED run-rate over a full week projects past the bar the "
     "repo already rations itself to. ➡️ Five watchers, five questions, "
     "and none of them replaces another.")
