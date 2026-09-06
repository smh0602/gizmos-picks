#!/usr/bin/env python3
"""
THE HARNESS IS THE ONLY GATE. This file is what keeps it that way.

🔴 WHY IT EXISTS. Two defects kept shipping and neither was a discipline
problem:

**1. A SECTION APPENDED AFTER THE FAILURE GATE CANNOT FAIL** (ledger rule
97). Checks were written below a file's `if fails: sys.exit(1)`; they
printed 🔴 and the file exited 0. ⛔ It happened **twice in one day, hours
apart, by the person who wrote the rule.**

**2. ELEVEN FILES SILENTLY PASSED ON AN ARGUMENT SWAP.** `[measured
2026-09-06]` The suite carried FOUR `ck` signatures — 11 files took the
condition FIRST, 7 took the name first. Calling a condition-first `ck` the
other way round passes a non-empty string as the condition, which is
truthy: **11 of 11 printed a tick, recorded no failure, and never
evaluated the real condition.**

✅ `tcheck.py` fixes both by SHAPE rather than by rule — the gate is an
`atexit` hook, so there is no "after"; and `ck` reads the argument TYPES,
so neither order can be misread.

⛔ **THIS FILE IS THE PART THAT DOES NOT DECAY.** A harness nobody is
required to use is a suggestion, and the next test file written in the old
shape brings both defects straight back.
"""
import glob
import os
import re
import subprocess
import sys
import tempfile

from tcheck import ck, note   # the shared gate — see tcheck.py

ROOT = os.path.dirname(os.path.abspath(__file__))
TESTS = sorted(os.path.basename(p) for p in glob.glob(f"{ROOT}/test_*.py")
               if os.path.basename(p) != "test_harness.py")

print("\n═══ 1. EVERY TEST FILE USES THE SHARED HARNESS ═══")
note(f"{len(TESTS)} test files in the suite")

no_import, own_ck, own_gate = [], [], []
for t in TESTS:
    src = open(f"{ROOT}/{t}", encoding="utf-8").read()
    if not re.search(r"^from tcheck import ", src, re.M):
        no_import.append(t)
    # ⛔ A LOCAL `ck` OR `eq` IS THE OLD SHAPE COMING BACK. It would carry
    #    its own argument order and its own idea of what a failure is.
    if re.search(r"^def (ck|eq|note)\(", src, re.M):
        own_ck.append(t)
    # ⛔ AND A BARE `sys.exit(1)` AT THE END IS THE OLD GATE. Anything
    #    written below it cannot fail — rule 97, exactly.
    if re.search(r"^\s*sys\.exit\(1[^)]*\)", src, re.M):
        own_gate.append(t)

ck("every test file imports the shared harness", not no_import,
   "missing in: " + ", ".join(no_import) if no_import else "")
ck("no test file defines its own ck / eq / note", not own_ck,
   "still local in: " + ", ".join(own_ck) if own_ck else
   "one signature, one meaning of failure")
# 🔴 AND NO FILE MAY PRINT ITS OWN SUCCESS BANNER.
# `[found 2026-09-06, in my own migration]` 25 files ended with
# `print("✅ all X passed")`. In the OLD shape that line sat AFTER the
# gate, so it only ran on success. ⛔ Removing the gate made it
# UNCONDITIONAL — a green line printed on a red run, which is exactly the
# defect the harness exists to kill, reintroduced by the migration that
# was killing it. ✅ The harness owns the summary; a file that writes its
# own is claiming a verdict it cannot know.
# ⚠️ THE TICK MUST BE THE FIRST CHARACTER OF THE STRING. `test_card_fb.py`
# prints an INDENTED "   ✅ ..." as part of an explanatory block — that is
# prose about a decision, not a claim that the run passed, and matching it
# would be a check firing on the wrong thing.
own_banner = [t for t in TESTS
              if re.search(r"^\s*print\((?:f)?[\"']✅",
                           open(f"{ROOT}/{t}", encoding="utf-8").read(), re.M)]
ck("no test file prints its own success banner", not own_banner,
   "still printing in: " + ", ".join(own_banner) if own_banner else
   "the harness owns the verdict")

ck("no test file carries its own exit gate", not own_gate,
   "still gating in: " + ", ".join(own_gate) if own_gate else
   "rule 97 is unwritable, not merely forbidden")

print("\n═══ 2. THE GATE ACTUALLY BITES, AND FROM THE BOTTOM OF A FILE ═══")
# 🔴 DRIVEN, NOT READ. The whole claim is about what the interpreter does
#    at exit, and only running it can show that.
CASES = [
    ("a passing file exits 0",
     "from tcheck import ck\nck('fine', True)\n", 0),
    ("a failing file exits 1",
     "from tcheck import ck\nck('broken', False)\n", 1),
    ("🔴 a check written BELOW where the old gate lived still fails the run",
     "from tcheck import ck\nck('first', True)\n"
     "# --- this is where `if FAIL: sys.exit(1)` used to sit ---\n"
     "ck('appended afterwards', False)\n", 1),
    ("a file that asserts NOTHING cannot pass",
     "from tcheck import note\nnote('I did no work')\n", 1),
    ("a swapped call is read by TYPE and still fails",
     "from tcheck import ck\nck(1 == 2, 'the condition came first')\n", 1),
    ("...and the same swap passes when it should",
     "from tcheck import ck\nck(1 == 1, 'the condition came first')\n", 0),
    ("two strings raise rather than guess",
     "from tcheck import ck\nck('a', 'b')\n", 1),
]
for name, body, want in CASES:
    d = tempfile.mkdtemp()
    p = os.path.join(d, "t.py")
    open(p, "w").write(body)
    r = subprocess.run([sys.executable, p], cwd=ROOT, capture_output=True,
                       text=True, env=dict(os.environ, PYTHONPATH=ROOT))
    ck(name, r.returncode == want, f"exit {r.returncode}, want {want}")

print("\n═══ 3. THE OLD SHAPE IS THE ONE THAT WOULD HAVE PASSED ═══")
# ⚠️ NOT VACUOUS: this reproduces the defect and shows it going green, so
#    the reader can see what the harness is actually preventing rather
#    than taking the docstring's word for it.
d = tempfile.mkdtemp()
p = os.path.join(d, "old.py")
open(p, "w").write(
    "import sys\n"
    "FAIL = []\n"
    "def ck(cond, label, detail=''):\n"
    "    print(('  ok   ' if cond else '  FAIL ') + label)\n"
    "    if not cond: FAIL.append(label)\n"
    "ck(True, 'a real check')\n"
    "if FAIL:\n"
    "    print('FAILED'); sys.exit(1)\n"
    "ck(False, 'appended below the gate')\n")
r = subprocess.run([sys.executable, p], capture_output=True, text=True)
ck("the OLD shape exits 0 with a failing check in it", r.returncode == 0,
   "which is the whole reason tcheck exists")
ck("...and it printed the failure while doing so",
   "FAIL appended below the gate" in r.stdout.replace("  ", " ")
   or "appended below the gate" in r.stdout,
   "a red line and a green run — indistinguishable from a pass in CI")
