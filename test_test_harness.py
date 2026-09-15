#!/usr/bin/env python3
"""
A TEST THAT NEVER ANSWERS MUST BE REPORTED AS NEVER ANSWERING.

🔴🔴 `[Sam, 2026-09-15, after I told him two test files could not run
here: "fix these two"]` — **and the first thing fixing them found was
that my stated cause was invented.**

⛔ WHAT I HAD WRITTEN DOWN, IN THE LEDGER, AS FACT:

    test_box_live.py   "hangs — the proxy blocks ESPN"
    test_budget.py     "hangs — the proxy blocks CollegeFootballData"

⛔ BOTH FALSE, AND MEASURED FALSE IN UNDER A MINUTE. `test_budget.py`
reaches no network at all and passes 33 checks. `test_box_live.py` serves
its ESPN payloads from `espnfix.json` over a LOCAL `http.server` and
passes 51. **Neither hangs.** `test_box_live.py` takes 115 seconds and I
had been killing it at 45, then writing the timeout down as a diagnosis.

    ➡️ ALL 71 FILES, MEASURED 2026-09-15: green, 308 seconds total.
       **The blind spot did not exist. The explanation did.**

══════════════════════════════════════════════════════════════════════
🔴 SO THE CLASS, WHICH IS WORTH MORE THAN EITHER FILE:

**A TIMEOUT IS A FACT ABOUT THE CLOCK YOU CHOSE, NEVER A FACT ABOUT THE
CODE.** "It hung" is not a diagnosis; it is the absence of one. Anything
that stops waiting must say how long it waited and must not dress that up
as a cause.

⛔ AND THE CI HARNESS HAD THE SAME HOLE FROM THE OTHER SIDE. The `Tests`
step in `collect.yml` ran every discovered file with NO per-file bound,
under a job `timeout-minutes: 350`. A single genuinely hanging file would
have burned **nearly six hours** of runner time and then been CANCELLED —
no `::error::`, no name in the `failed=` output, nothing in the issue
`collect.yml` opens. ➡️ **The one failure mode that produces no evidence
at all**, in the step whose entire job is producing evidence.

⚠️ THIS FILE DRIVES THE REAL SHELL FUNCTION, extracted from the workflow
and executed. It does not read the YAML and agree with itself — that is
rule 260, and I shipped it eleven days ago.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(ROOT, ".github/workflows/collect.yml")
YML = open(WF, encoding="utf-8").read()

# ── the Tests step, on its own ────────────────────────────────────────
_m = re.search(r"\n      - name: Tests\n(.*?)\n      - name: ", YML, re.S)
STEP = _m.group(1) if _m else ""
ck("🔴 the Tests step is still findable at all", bool(STEP) and len(STEP) > 400,
   "⛔ if this stops matching, every check below goes vacuously green "
   "against an empty string — the exact shape of rule 67. Got %d chars"
   % len(STEP))

print("\n═══ 1. 🔴🔴 EVERY DISCOVERED FILE RUNS UNDER A CLOCK ═══")
# ⛔ THE CLASS, NOT THE INSTANCE. Not "test_box_live.py is bounded" —
#    ANY loop in ANY workflow that runs discovered files must be.
_loops = []
for _fn in sorted(os.listdir(os.path.join(ROOT, ".github/workflows"))):
    if not _fn.endswith(".yml"):
        continue
    _t = open(os.path.join(ROOT, ".github/workflows", _fn),
              encoding="utf-8").read()
    for _lm in re.finditer(r"(?m)^\s*for \w+ in (test_|.*\*)\S*; do$", _t):
        _body = _t[_lm.start():_t.find("done", _lm.start())]
        _loops.append((_fn, _lm.group(0).strip(), _body))
ck("⚠️ there is at least one discovery loop to bound",
   len(_loops) >= 2,
   "⛔ a check over an empty set passes and proves nothing. Found %d"
   % len(_loops))
_unbounded = [(f, h) for f, h, b in _loops
              if "timeout" not in b and "run_one" not in b]
ck("🔴🔴 NO discovery loop runs a file without a timeout",
   not _unbounded,
   "⛔ job timeout-minutes is 350. One hanging file burns six hours of "
   "runner time and is CANCELLED with no name attached. Unbounded: %s"
   % _unbounded)

print("\n═══ 2. ⛔ 'NEVER ANSWERED' IS NOT 'FAILED' ═══")
ck("🔴 a timeout is reported as a TIMEOUT, in its own words",
   "TIMED OUT" in STEP and "it never answered" in STEP,
   "⛔ a red assertion tells you WHAT is wrong; a timeout tells you only "
   "that nothing came back. Conflating them sends the reader hunting "
   "for a bug that may not exist — which is what I did to myself")
ck("🔴 ...and 124 AND 137 are both recognised",
   '"124"' in STEP and '"137"' in STEP,
   "⚠️ `timeout` exits 124; `timeout -k` escalating to SIGKILL surfaces "
   "as 137. Catching only one leaves the other reported as a plain "
   "FAILED, which is the misdiagnosis this file exists to stop")
# ⛔ ~~a static "124 ... rc=1" search~~ — **STRUCK, IT WAS VACUOUS.**
#    `rc=1` appears three times in this step, so the search matched the
#    FAILED branch and stayed green with the timeout branch's `rc=1`
#    deleted. Rule 67 again, caught by disabling it and watching. ➡️ The
#    real question is answered by DRIVING it, in section 4.
ck("⛔ ...and its NAME reaches the issue, not just the run page",
   "failed=\"$failed $2(TIMEOUT)\"" in STEP,
   "🔴 RULE 261: `::error::` reaches the run page and nowhere else, and "
   "the run page is the thing nobody is watching at 3am. The name has "
   "to land in `failed=`, which is what becomes the emailed issue")
ck("⚠️ every file prints how long it took",
   "date +%s" in STEP and "${d}s" in STEP,
   "🔴 A TIMEOUT IS A FACT ABOUT THE CLOCK YOU CHOSE. Without the "
   "duration beside it nobody can tell a file that is 3s from the limit "
   "from one that is 300s from it — and the first one is about to go "
   "red for no reason at all")

print("\n═══ 3. ⛔ THE CLOCK IS BOUNDED ON BOTH SIDES ═══")
_per = re.search(r"PER_FILE=(\d+)", STEP)
_per = int(_per.group(1)) if _per else 0
_job = re.search(r"(?m)^    timeout-minutes: (\d+)", YML)
_job = int(_job.group(1)) if _job else 0
# 🔴 SLOWEST FILE MEASURED 2026-09-15, not guessed: test_box_live.py at
#    115s on this container. A CI runner is slower, so the margin is
#    large on purpose.
ck("⚠️ generous against the slowest MEASURED file (115s)",
   _per >= 115 * 3,
   "⛔ CLAUDE.md: a guard that fires on correct code is the other "
   "failure, not a safe one. A tight bound here turns a slow runner "
   "into a nightly false alarm. PER_FILE=%d" % _per)
ck("🔴 ...and strictly under the job's own timeout",
   0 < _per < _job * 60,
   "⛔ a per-file bound above the job bound can never fire — the job is "
   "cancelled first and the file is never named. PER_FILE=%ds against "
   "timeout-minutes=%d (%ds)" % (_per, _job, _job * 60))

print("\n═══ 4. 🔴🔴 THE SHELL FUNCTION, ACTUALLY EXECUTED ═══")
# ⛔ RULE 260: I once wrote a check that read its expectation off the
#    thing it was checking. Reading `TIMED OUT` out of the YAML proves
#    the string is present, NOT that the logic works. So: pull the real
#    function out of the workflow and run it against planted files.
_fn = re.search(r"(PER_FILE=\d+\n.*?^          \}\n)", STEP, re.S | re.M)
ck("🔴 the runner function is extractable to be driven",
   bool(_fn),
   "⛔ if this stops matching, section 4 proves nothing. A guard that "
   "cannot reach its subject is not a guard")

if _fn:
    _tmp = tempfile.mkdtemp()
    try:
        open(os.path.join(_tmp, "hang.py"), "w").write(
            "import time\ntime.sleep(600)\n")
        open(os.path.join(_tmp, "bad.py"), "w").write("raise SystemExit(1)\n")
        open(os.path.join(_tmp, "good.py"), "w").write("print('ok')\n")
        body = _fn.group(1).replace("PER_FILE=600", "PER_FILE=3")
        body = re.sub(r"(?m)^          ", "", body)
        script = ("set +e\nrc=0\nfailed=\"\"\n" + body +
                  "\nrun_one python3 hang.py\nrun_one python3 bad.py\n"
                  "run_one python3 good.py\n"
                  "echo \"RC=$rc\"\necho \"FAILED=$failed\"\n")
        # ⚠️ 30s AGAINST A 3s PER_FILE. If the harness has lost its
        #    timeout, THIS is what hangs — so the hang is caught and
        #    reported as the finding rather than being allowed to become
        #    the same six-hour silence one level up.
        try:
            r = subprocess.run(["bash", "-c", script], cwd=_tmp,
                               capture_output=True, text=True, timeout=30)
            out = r.stdout + r.stderr
        except subprocess.TimeoutExpired:
            out = "!! THE HARNESS ITSELF NEVER STOPPED !!"
        ck("🔴🔴 a HANGING file is killed and named a TIMEOUT",
           "hang.py TIMED OUT" in out,
           "⛔ this is the whole point, driven rather than read — the "
           "function is pulled out of the YAML and executed")
        ck("⛔ ...and a FAILING file is named a FAILURE, not a timeout",
           "bad.py FAILED" in out and "bad.py TIMED OUT" not in out,
           "🔴 if every non-zero exit read as a timeout the distinction "
           "would be decorative")
        ck("✅ ...and a PASSING file is named neither",
           "good.py" not in out.replace("run_one python3 good.py", ""),
           "⛔ a harness that reports a healthy file as broken is the "
           "false-alarm failure")
        ck("🔴 both of them turn the suite red",
           "RC=1" in out,
           "⛔ NEVER WEAKEN A CHECK TO MAKE IT PASS — a file that never "
           "answered has not passed")
        # 🔴🔴 A TIMEOUT **ALONE**, WITH NOTHING ELSE FAILING. The static
        #    version of this check was vacuous: `rc=1` appears three
        #    times in the step, so it matched the FAILED branch and
        #    stayed green with the timeout branch's `rc=1` removed.
        solo = subprocess.run(
            ["bash", "-c", "set +e\nrc=0\nfailed=\"\"\n" + body +
             "\nrun_one python3 hang.py\necho \"RC=$rc\""],
            cwd=_tmp, capture_output=True, text=True, timeout=30)
        ck("🔴🔴 a TIMEOUT ALONE is enough to turn the suite red",
           "RC=1" in (solo.stdout + solo.stderr),
           "⛔ if only a real FAILURE reddens the run, a suite that "
           "stopped answering ships green — the false all-clear. Got: %s"
           % (solo.stdout + solo.stderr).strip()[-120:])
        ck("⛔ ...and BOTH names reach the emailed list",
           "hang.py(TIMEOUT)" in out and "bad.py" in
           out.split("FAILED=")[-1],
           "🔴 rule 261 — a name that stops at the run page reaches "
           "nobody. Got: %s" % out.split("FAILED=")[-1].strip())
        _t3 = re.search(r"hang\.py.*?\n\s*(\d+)s", out, re.S)
        ck("⚠️ the kill happens at the clock, not at the job limit",
           _t3 and int(_t3.group(1)) <= 20,
           "⛔ a `timeout` that does not actually stop the process leaves "
           "the six-hour burn in place. Got %s"
           % (_t3.group(1) + "s" if _t3 else "no duration printed"))
    finally:
        shutil.rmtree(_tmp, ignore_errors=True)

note("⛔ WHAT THIS DOES NOT CLAIM: that the suite is fast, or that 600s "
     "is right forever. It claims that when a file stops answering, the "
     "run says SO — with the file's name, the wall clock it was given, "
     "and no invented cause. ➡️ The cause is a separate investigation, "
     "and pretending otherwise is what put two false lines in the "
     "ledger.")

sys.exit(0)
