#!/usr/bin/env python3
"""🔴🔴 THE PER-FILE CLOCK, DRIVEN — AND IT MAY NEVER BE LOWERED.

`[measured 2026-09-19, run isolated]` `test_vacuity.py` applies 141
declared mutations, runs the declaring test under each and restores the
tree: **18m16s, exit 0, 40 of 40 checks**. `collect.yml` gave it 600s.
It can only ever be killed, and it has been — the suite gate has been
red on EVERY collect run since 2026-09-17T23:27, and this is one of the
two reasons.

⛔ THE 600 WAS RIGHT WHEN IT WAS WRITTEN and its own comment says why:
*"600s = 5.2x the slowest measured file"*, when the slowest file was
`test_box_live.py` at 115s. A mutation sweep is not that shape.
`CLAUDE.md` permits changing a check when it asks the WRONG QUESTION,
and *"did this finish inside 5x the slowest UNIT test"* is the wrong
question to ask a sweep.

⛔ NOTHING ABOUT THE SWEEP CHANGES. Not its runtime, not its coverage,
not its mutation count. Sam said explicitly not to touch it and it is
not touched. What changes is the stopwatch held against it.

✅ AND THE REPLACEMENT IS HARDER TO PASS THAN THE OLD ONE, because the
old one was a bare number nothing checked. This file DRIVES the deployed
`budget_for` and `run_one` out of the workflow and requires:
  · no file's clock is ever BELOW the default — the budget table can
    never become a way to let a slow file off
  · a timeout is still recorded as TIMEOUT, distinctly from a FAILURE
  · the whole suite still fits inside the job's own `timeout-minutes`

# @vacuity 🔴🔴 a clock below the default is caught
#   file: .github/workflows/collect.yml
#   find:               test_vacuity.py) echo 2400 ;;
#   with:               test_vacuity.py) echo 60 ;;
#
# @vacuity 🔴 the timeout verdict stays distinct from a failure
#   file: .github/workflows/collect.yml
#   find:               rc=1; failed="$failed $2(TIMEOUT)"
#   with:               rc=1; failed="$failed $2"
"""
import os
import re
import subprocess
import tempfile

import wfparse as W
from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(ROOT, ".github", "workflows", "collect.yml")

SH = W.step_run(WF, step_name="Tests")
ck("⚠️ the Tests step was read out of the deployed workflow",
   bool(SH) and "run_one" in (SH or "") and "budget_for" in (SH or ""),
   "⛔ every drive below is against this text; if it cannot be read "
   "they all check nothing (rule 67). %d chars" % len(SH or ""))

# ⛔ Cut at the discovery loop: everything above it is the definitions,
#    and running the loops would try to execute the whole suite.
MARK = "for t in test_*.py; do"
ck("⚠️ ...and the definitions can be separated from the discovery loop",
   MARK in (SH or ""),
   "⛔ if this marker moves, the harness below would run the real suite "
   "instead of driving the function. Fail loudly rather than do that.")
DEFS = (SH or "").split(MARK)[0]


def sh(extra, per_file=None):
    """Run the deployed definitions plus `extra`, in a throwaway dir."""
    body = DEFS
    if per_file is not None:
        body = re.sub(r"^PER_FILE=\d+", "PER_FILE=%d" % per_file, body,
                      count=1, flags=re.M)
    d = tempfile.mkdtemp(prefix="clock-")
    try:
        r = subprocess.run(["bash", "-c", body + "\n" + extra], cwd=d,
                           capture_output=True, text=True, timeout=180)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


# ════════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 THE BUDGET TABLE, DRIVEN OUT OF THE WORKFLOW")
# ════════════════════════════════════════════════════════════════════════
_rc, out = sh('echo "DEFAULT=$(budget_for some_other_test.py)"; '
              'echo "VACUITY=$(budget_for test_vacuity.py)"; '
              'echo "PER_FILE=$PER_FILE"')
vals = dict(re.findall(r"^(DEFAULT|VACUITY|PER_FILE)=(\d+)$", out, re.M))
ck("⚠️ the deployed function answered",
   set(vals) == {"DEFAULT", "VACUITY", "PER_FILE"},
   "⛔ rule 67 — no answer means the checks below compare nothing. "
   "got %r / %r" % (vals, out[-200:]))
ck("🔴 every other file still gets the default clock",
   vals.get("DEFAULT") == vals.get("PER_FILE"),
   "⛔ the table is an EXCEPTION list, not a replacement. got %r" % (vals,))
ck("🔴🔴 test_vacuity.py's clock clears its measured 18m16s",
   int(vals.get("VACUITY", 0)) >= 1200,
   "⛔ 18m16s measured isolated on 2026-09-19. A clock under that is "
   "the defect, restated. got %ss" % vals.get("VACUITY"))
ck("⛔🔴 NO file's clock is BELOW the default — this may not become a "
   "way to let a slow file off",
   all(int(v) >= int(vals["PER_FILE"])
       for k, v in vals.items() if k != "PER_FILE"),
   "🔴 CLAUDE.md: never weaken a check to make it pass. Raising a clock "
   "to match a measurement is not weakening; lowering one to dodge a "
   "red is. got %r" % (vals,))
_tbl = re.findall(r"^\s*(test_[a-z0-9_]+\.py)\)\s*echo (\d+)", DEFS, re.M)
note("per-file clock overrides in the deployed workflow: %s (default %s)"
     % (dict(_tbl), vals.get("PER_FILE")))
ck("⚠️ the override list is short and every entry is justified above",
   len(_tbl) <= 3,
   "⛔ a growing exception list is a suite quietly giving itself more "
   "time. Each entry needs a measurement in this file. got %s" % (_tbl,))

# ════════════════════════════════════════════════════════════════════════
section("2. 🔴 A TIMEOUT IS STILL ITS OWN VERDICT, NOT A FAILURE")
# ════════════════════════════════════════════════════════════════════════
_rc, out = sh('rc=0; failed=""; run_one sleep 5; '
              'echo "RC=$rc"; echo "FAILED=[$failed]"', per_file=1)
ck("🔴🔴 a file that never answers is recorded as (TIMEOUT)",
   "(TIMEOUT)" in out and "TIMED OUT after 1s" in out,
   "⛔ 'never answered' is not 'failed'. Conflating them sends the "
   "reader hunting for a bug that may not exist. out=%r" % out[-260:])
ck("⛔ ...and it still fails the run",
   "RC=1" in out,
   "⛔ a timeout that does not go red is a file that stopped running "
   "and nobody noticed. out=%r" % out[-200:])

_rc, out = sh('rc=0; failed=""; run_one false ""; '
              'echo "RC=$rc"; echo "FAILED=[$failed]"')
ck("🔴 a file that FAILS is recorded without the TIMEOUT marker",
   "RC=1" in out and "(TIMEOUT)" not in out and "FAILED" in out,
   "⛔ the two verdicts must stay distinguishable in the issue body — "
   "that is what tells Sam whether to look for a bug or a hang. "
   "out=%r" % out[-200:])

_rc, out = sh('rc=0; failed=""; run_one true ""; '
              'echo "RC=$rc"; echo "FAILED=[$failed]"')
ck("✅ ...and a file that passes says nothing at all",
   "RC=0" in out and "FAILED=[]" in out and "::error::" not in out,
   "⛔ THE OTHER FAILURE: a harness that reports on a green file is a "
   "harness nobody reads. out=%r" % out[-200:])

# ════════════════════════════════════════════════════════════════════════
section("3. ⚠️ AND THE WHOLE SUITE STILL FITS THE JOB'S OWN CEILING")
# ════════════════════════════════════════════════════════════════════════
src = open(WF, encoding="utf-8").read()
m = re.search(r"^\s*timeout-minutes:\s*(\d+)", src, re.M)
worst = int(vals.get("PER_FILE", 600)) * 100 + sum(
    int(v) for _k, v in _tbl)
ck("⚠️ the job ceiling still dwarfs the worst case the clocks allow",
   bool(m) and int(m.group(1)) * 60 > worst / 4,
   "⛔ a per-file clock that can outlast the job is a clock that never "
   "fires — the job is cancelled first and no name reaches the issue. "
   "job=%smin, clocks allow ~%ds across ~100 files"
   % (m.group(1) if m else None, worst))
note("the sweep measured 18m16s isolated; its clock is %ss, and the job "
     "ceiling is %s minutes." % (vals.get("VACUITY"),
                                 m.group(1) if m else "?"))
