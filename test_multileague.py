#!/usr/bin/env python3
"""
ONE RUN, TWO LEAGUES — AND THIS EXECUTES THE WORKFLOW'S OWN BASH.

🔴 WHY IT EXISTS. Sam, 2026-09-06: *"if any of these runs can be done for
nfl and cfb its expected we do that so we can kill two birds with one
stone."* ⛔ That meant changing the CONVERGE LOOP — the block that spends
credits, commits to the repo and gates the run — which is the highest-risk
file in this project and the one whose past edits caused the most damage.

⚠️ SO THIS DOES NOT READ THE FILE AND HOPE. It pulls the actual `run:`
script out of `collect.yml` with a YAML parser, drops a fake `python`,
`git` and `date` on PATH, and RUNS IT — then asserts on what the stubs
were asked to do.
⛔ A substring check on bash would have "passed" for every version of this
change I got wrong while writing it. `[rule 69, thirteen false failures
and counting — and this is the mirror case: a false PASS]`

WHAT IS PINNED:
  1. a ONE-league run is unchanged — the exact calls it always made
  2. a TWO-league run runs every mode for BOTH, with the right LEAGUE
  3. a league that FAILS does not skip the next one
  4. `verify_freshness` is graded ONCE PER LEAGUE, not once per run
  5. MLB's verifiers can never be reached by a football run
"""
import os
import re
import shutil
import subprocess
import tempfile

from tcheck import ck, note   # the shared gate — see tcheck.py

ROOT = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(ROOT, ".github/workflows/collect.yml")


def converge_script(text=None):
    """The real `run:` block of the 'Converge and hold' step.

    ⛔ Parsed from the workflow, never pasted in here — a copy of the
    script under test is not the script under test.
    ⚠️ BY HAND, NOT WITH PyYAML. The CI runner installs a bare Python and
    NOTHING in this repo has ever needed a third-party package. A test
    that cannot import is a test that fails the whole suite — and on a
    push the suite BLOCKS. `[ledger rule 67: a test that never runs is
    worse than no test; this is its louder cousin.]`
    ✅ The extraction is cross-checked against PyYAML below wherever
    PyYAML happens to be installed."""
    lines = (text or open(WF, encoding="utf-8").read()).splitlines()
    for i, ln in enumerate(lines):
        if ln.strip() != "id: collect":
            continue
        for j in range(i, len(lines)):
            m = re.match(r"^(\s+)run: \|\s*$", lines[j])
            if not m:
                continue
            pad = len(m.group(1)) + 2
            out = []
            for k in range(j + 1, len(lines)):
                cur = lines[k]
                if cur.strip() and not cur.startswith(" " * pad):
                    break
                out.append(cur[pad:] if len(cur) >= pad else "")
            return "\n".join(out).rstrip() + "\n"
    return None


SCRIPT = converge_script()
# ⚠️ `$MODES`, NOT `$LEAGUES`. Both versions of the step loop over
# `$MODES`; only the new one loops over `$LEAGUES`, and that difference is
# what `MULTI` below keys on. ⛔ Requiring `$LEAGUES` here would make this
# file unable to run against the workflow it ships alongside.
ck("the converge step's script can be read out of the workflow",
   bool(SCRIPT) and "$MODES" in SCRIPT and "collect.py" in SCRIPT,
   "%d chars" % len(SCRIPT or ""))
# ✅ AND THE HAND PARSE IS CHECKED AGAINST A REAL YAML PARSER wherever one
#    exists — so "I wrote my own extractor" is measured, not asserted.
try:
    import yaml as _yaml
except ImportError:
    note("PyYAML not installed here, so the hand-parse was not "
         "cross-checked — it IS still driven end to end below")
else:
    _doc0 = _yaml.safe_load(open(WF, encoding="utf-8"))
    _ref = [s for s in _doc0["jobs"]["collect"]["steps"]
            if s.get("id") == "collect"][0]["run"]
    ck("⛔ the hand-written extractor agrees with PyYAML, line for line",
       SCRIPT.strip() == _ref.strip(),
       "%d vs %d chars" % (len(SCRIPT.strip()), len(_ref.strip())))


def drive(leagues, modes="live-probe", fail_for=None):
    """Run the real script with stubbed tools. Returns the call log."""
    tmp = tempfile.mkdtemp()
    bin_ = f"{tmp}/bin"
    os.makedirs(bin_)
    log = f"{tmp}/calls.log"

    # ⚠️ THE STUB RECORDS `LEAGUE` AS THE SCRIPT SET IT, which is the whole
    # question: the tools read the league from the ENVIRONMENT.
    open(f"{bin_}/python", "w").write(
        '#!/bin/sh\n'
        'echo "python LEAGUE=${LEAGUE:-<unset>} $*" >> "$CALLS"\n'
        'case "$*" in\n'
        '  *"$FAIL_TOKEN"*) [ -n "$FAIL_TOKEN" ] && exit 1 ;;\n'
        'esac\n'
        'exit 0\n')
    # git must not touch a real repo, and `git diff --staged --quiet`
    # returning 0 keeps the commit path out of the way.
    open(f"{bin_}/git", "w").write(
        '#!/bin/sh\necho "git $*" >> "$CALLS"\nexit 0\n')
    for f in ("python", "git"):
        os.chmod(f"{bin_}/{f}", 0o755)

    env = dict(os.environ,
               PATH=f"{bin_}:{os.environ['PATH']}",
               CALLS=log,
               FAIL_TOKEN=fail_for or "",
               # ⚠️ ALL THREE NAMES ARE SUPPLIED ON PURPOSE. The step's
               # own `env:` block decides which it reads — the version
               # BEFORE this change reads `LEAGUE`/`LEAGUE_NAME`, the one
               # after reads `LEAGUES`. Giving all three is what the real
               # runner effectively does (it provides exactly the block in
               # the file), and it lets sections 1 and 2 prove the
               # single-league case against EITHER version.
               LEAGUES=leagues,
               LEAGUE=leagues.split()[0],
               LEAGUE_NAME=leagues,
               MODES=modes,
               SEASON="2026",
               LOOP_MINUTES="0",
               GITHUB_RUN_NUMBER="1",
               # ⚠️ THE REAL RUNNER ALWAYS SETS THIS. Without it the
               # script's last line redirects into an empty filename —
               # a fault in this harness, not in the workflow.
               GITHUB_OUTPUT=f"{tmp}/gh_output")
    r = subprocess.run(["bash", "-c", SCRIPT], cwd=tmp, env=env,
                       capture_output=True, text=True, timeout=120)
    calls = open(log).read().splitlines() if os.path.exists(log) else []
    # ⚠️ THE STEP'S REAL VERDICT IS `rc` IN $GITHUB_OUTPUT, NOT ITS EXIT
    # CODE. The step deliberately exits 0 so the commit and the gate below
    # it still run; a LATER step (`Fail if any pass failed`) reads this and
    # fails the job. ⛔ Asserting on the exit code would be measuring the
    # wrong unit — which is what the first version of this test did.
    out = open(f"{tmp}/gh_output").read() if os.path.exists(f"{tmp}/gh_output") else ""
    shutil.rmtree(tmp, ignore_errors=True)
    r.rc_out = out
    return r, calls


def collect_calls(calls, mode):
    """Which leagues `collect.py <mode>` was run for, in order."""
    out = []
    for c in calls:
        m = re.match(r"python LEAGUE=(\S+) collect\.py (\S+)$", c)
        if m and m.group(2) == mode:
            out.append(m.group(1))
    return out


def freshness_calls(calls):
    return [re.match(r"python LEAGUE=(\S+) ", c).group(1)
            for c in calls if "verify_freshness.py" in c]


# ───────────────────────────────────────────────────────────────
print("\n═══ 1. ONE LEAGUE — THE NORMAL CASE MUST BE UNCHANGED ═══")
# ⛔ THIS IS THE CHECK THAT MATTERS MOST. Every existing cron routes ONE
#    league; if the loop changed their behaviour at all, this change is a
#    regression wearing a feature's clothes.
r1, c1 = drive("ncaaf", "live-probe")
ck("it exits clean", r1.returncode == 0, (r1.stderr or "")[-300:])
ck("`collect.py live-probe` runs exactly once, for ncaaf",
   collect_calls(c1, "live-probe") == ["ncaaf"],
   str(collect_calls(c1, "live-probe")))
ck("freshness is graded exactly once, for ncaaf",
   freshness_calls(c1) == ["ncaaf"], str(freshness_calls(c1)))
ck("⛔ and no MLB verifier is reached by a football run",
   not any("verify_board" in c or "verify_record" in c or "verify_card" in c
           for c in c1),
   "those are baseball, guarded on the league and not the mode")

print("\n═══ 2. MLB IS STILL MLB ═══")
r2, c2 = drive("mlb", "converge")
ck("it exits clean", r2.returncode == 0, (r2.stderr or "")[-300:])
ck("MLB still gets its own extra pull",
   ["mlb"] == collect_calls(c2, "schedule")[:1] or any(
       "collect.py schedule converge-off" in c for c in c2),
   "the statsapi schedule pull is MLB-only")
ck("MLB still runs its three verifiers",
   all(any(v in c for c in c2)
       for v in ("verify_card.py", "verify_board.py", "verify_record.py")),
   "guarded on LEAGUE == mlb, which a two-word value can never equal")

# ══════════════════════════════════════════════════════════════════════
# ⚠️ THE MULTI-LEAGUE SECTIONS RUN ONLY ONCE THE WORKFLOW CARRIES THE
# LOOP, AND THAT IS A DELIVERY FACT, NOT A SOFTENED CHECK.
# 🔴 The loop lives in `.github/workflows/collect.yml`; this file lives in
# the repo ROOT. They ship as TWO commits, because an upload instruction
# with two destinations has one outcome and `.github` is hidden on Windows
# (rule 111). ⛔ Asserting the loop unconditionally would make the ROOT
# commit red until the workflow one landed — a red run guaranteed by the
# delivery, which is exactly the trap the grader drop fell into.
# ✅ SO IT IS KEYED ON A FACT ABOUT THE FILE UNDER TEST: once the script
# contains `$LEAGUES`, every check below is HARD and cannot be skipped.
# ⛔ And the skip is LOUD — a silent skip is rule 116's defect wearing a
# delivery excuse.
# ══════════════════════════════════════════════════════════════════════
MULTI = "$LEAGUES" in (SCRIPT or "")
if not MULTI:
    note("⚠️ THE WORKFLOW DOES NOT CARRY THE LEAGUE LOOP YET — sections "
         "3-5 are NOT RUN. This is the state between the root commit and "
         "the workflow commit; the checks turn hard the moment "
         "`collect.yml` lands, with no edit to this file.")

print("\n═══ 3. TWO LEAGUES, ONE RUN — SAM'S ASK ═══")
r3, c3, c3b, c4, c5 = (None,) * 5
if MULTI:
    r3, c3 = drive("ncaaf nfl", "live-probe")
    ck("it exits clean", r3.returncode == 0, (r3.stderr or "")[-300:])
    ck("🔴 the mode runs for BOTH leagues, in the order routed",
       collect_calls(c3, "live-probe") == ["ncaaf", "nfl"],
       str(collect_calls(c3, "live-probe")))
    ck("🔴 and freshness is graded for BOTH",
       freshness_calls(c3) == ["ncaaf", "nfl"], str(freshness_calls(c3)))
    # ⛔ THE ORDER IS THE ROUTING'S, NOT ALPHABETICAL: the arm names the
    #    league whose games are actually on FIRST.
    r3b, c3b = drive("nfl ncaaf", "live-probe")
    ck("the routed order is respected, not sorted",
       collect_calls(c3b, "live-probe") == ["nfl", "ncaaf"],
       str(collect_calls(c3b, "live-probe")))

    print("\n═══ 4. TWO MODES × TWO LEAGUES ═══")
    r4, c4 = drive("ncaaf nfl", "news card-fb")
    ck("every mode runs for every league",
       collect_calls(c4, "news") == ["ncaaf", "nfl"]
       and collect_calls(c4, "card-fb") == ["ncaaf", "nfl"],
       "news=%s card-fb=%s" % (collect_calls(c4, "news"),
                           collect_calls(c4, "card-fb")))
    ck("⛔ and a league finishes its modes before the next league starts",
       [c for c in c4 if "collect.py" in c][:2]
       == ["python LEAGUE=ncaaf collect.py news",
       "python LEAGUE=ncaaf collect.py card-fb"],
       "one league at a time — a half-built league is harder to read in a log")

    print("\n═══ 5. 🔴 A FAILING LEAGUE MUST NOT SKIP THE NEXT ONE ═══")
    # ⛔ SAME REASON THE MODE LOOP DOES NOT ABORT: data already on disk --
    #    possibly already PAID FOR -- has to reach the repo. A run that gave
    #    up on ncaaf and silently skipped nfl would lose a pull nobody knew
    #    was missing.
    r5, c5 = drive("ncaaf nfl", "card-fb", fail_for="card-fb")
    ck("nfl still ran after ncaaf failed",
       collect_calls(c5, "card-fb") == ["ncaaf", "nfl"],
       str(collect_calls(c5, "card-fb")))
    ck("...and the run is RED, not quietly green",
       "rc=1" in r5.rc_out,
       "the step reports %r, and `Fail if any pass failed` turns that into a "
       "red job" % r5.rc_out.strip())
    # ✅ AND THE STEP THAT ACTS ON IT REALLY EXISTS — a verdict nothing reads
    #    is not a verdict.
    _wf_text = open(WF, encoding="utf-8").read()
    _after = _wf_text.split("steps.collect.outputs.rc")[1:]
    ck("⛔ and a later step actually fails the job on it",
       bool(_after) and "exit 1" in _after[0][:400],
       "a verdict nothing reads is not a verdict")
    ck("a clean two-league run reports rc=0", "rc=0" in r3.rc_out,
       r3.rc_out.strip())
    ck("...and both leagues were still graded",
       freshness_calls(c5) == ["ncaaf", "nfl"], str(freshness_calls(c5)))

print("\n═══ 6. THE ROUTING TABLE ACTUALLY USES IT ═══")
from wfroutes import parse_arms, parse_routes    # noqa: E402
wf = open(WF, encoding="utf-8").read()
arms = parse_arms(wf)
multi = [(c, l, m) for c, l, m in arms if len(l.split()) > 1]
# ⚠️ REPORTED, NOT ASSERTED, AND THE REASON IS DELIVERY ORDER.
# 🔴 THIS FILE AND THE WORKFLOW SHIP AS TWO COMMITS (rule 111: an upload
# instruction with two destinations has one outcome, and `.github` is a
# hidden folder on Windows). If this asserted "a two-league arm exists",
# the ROOT commit would be RED until the workflow commit landed — and the
# reverse ordering is red too, because main's tests cannot parse a
# two-league arm at all.
# ⛔ A CHECK THAT FORCES TWO COMMITS TO LAND IN ONE INSTANT IS A CHECK
# THAT MAKES A RED RUN INEVITABLE. `[the two-commit ordering discipline,
# learned 2026-09-06 when the grader needed the same split]`
# ✅ WHAT IS ASSERTED INSTEAD IS EVERY INVARIANT THAT MUST HOLD IN BOTH
# STATES — no unknown league, no paid mode doubled — plus the LOOP ITSELF,
# driven end to end above. Those cannot regress silently either way.
note("%d of %d routing arms name two leagues" % (len(multi), len(arms)))
ck("every league named anywhere is one the collector knows",
   {x for _c, l, _m in arms for x in l.split()} <= {"mlb", "nfl", "ncaaf"},
   str(sorted({x for _c, l, _m in arms for x in l.split()})))
# ⚠️ PAID MODES STAY SINGLE-LEAGUE ON PURPOSE. Sam chose per-league times
# for the pulls that cost money; doubling those up would change his
# schedule and his spend, which is not what he asked for.
_paid = {"props-player", "gamelines"}
_doubled_paid = [(c, l, m) for c, l, m in multi
                 if _paid & set(m.split())]
ck("⛔ no PAID mode was quietly doubled up",
   not _doubled_paid,
   "props and odds keep the per-league times Sam set: %s" % _doubled_paid)
note("two-league arms: " + ", ".join(sorted({m for _c, _l, m in multi})))
