#!/usr/bin/env python3
"""THE SWEEP'S RED RUN MAY STOP AT THE FIRST FAILURE — AND NOTHING ELSE MAY.

🔴 WHY `[2026-09-26]`. Collect #1852's vacuity sweep used 2081s of its
2400s clock (13% margin), before #184 added 15 declarations. The sweep
runs each declaring test twice: RED under the mutation, then GREEN on the
revert. From the red run it reads one bit, "did it exit non-zero", and a
failed check already decides that bit: nothing un-records a failure, and
tcheck's gate turns any failure into exit 1. So `vacuity.run_test(...,
red=True)` sets TCHECK_FAIL_FAST and tcheck stops at the first failed check.

⛔ WHAT MUST NOT CHANGE, and what this file drives:
  · the verdict: every shape of test exits non-zero under fail-fast exactly
    when it does in a full run;
  · the green-on-revert run is a FULL run, never fail-fast;
  · the mode is never inherited by a child the test starts (a planted file
    or a harness copy must run the way it always did).

# @vacuity the mode must not leak into a child the test starts
#   file: tcheck.py
#   find: FAIL_FAST = os.environ.pop("TCHECK_FAIL_FAST", "") == "1"
#   with: FAIL_FAST = os.environ.get("TCHECK_FAIL_FAST", "") == "1"
#
# @vacuity the red run must actually stop at the first failure
#   file: tcheck.py
#   find:             raise SystemExit(1)
#   with:             pass
#
# @vacuity the sweep's red run must ask for fail-fast
#   file: vacuity.py
#   find:         red = run_test(t, root, red=True)
#   with:         red = run_test(t, root)
#
# @vacuity the green-on-revert run must never be fail-fast
#   file: vacuity.py
#   find:     green = run_test(t, root)
#   with:     green = run_test(t, root, red=True)
#
# @vacuity a run's temp dir is deleted however the run ended
#   file: vacuity.py
#   find:         shutil.rmtree(tmp, ignore_errors=True)
#   with:         pass

🔴 AND WHAT A RUN THAT STOPS EARLY LEAVES BEHIND `[2026-09-26, found by
the first full sweep of this change]`. Fixture copies of `data/` are
removed at the END of many test files. A red run stopped at its first
failure skipped that, the copies piled up to 30 GB, the disk filled, and
every later run died on "No space left on device", reading as
RED_BOTH_WAYS. So every run gets its own TMPDIR, deleted afterwards.
Section 4.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

from tcheck import ck, eq, note, section, shown

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import vacuity as V  # noqa: E402

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 THE VERDICT IS THE SAME AS A FULL RUN'S, IN EVERY SHAPE")
# ══════════════════════════════════════════════════════════════════════
SLOW = "import time\ntime.sleep(3)\n"
SHAPES = {
    "the first check fails, then slow work":
        "from tcheck import ck\nck('a', False)\n" + SLOW + "ck('b', True)\n",
    "the LAST check fails":
        "from tcheck import ck\nck('a', True)\nck('b', True)\nck('c', False)\n",
    "every check passes":
        "from tcheck import ck\nck('a', True)\nck('b', True)\n",
    "it crashes after passing checks":
        "from tcheck import ck\nck('a', True)\nraise RuntimeError('boom')\n",
    "it records no checks (the gate's own failure)":
        "from tcheck import note\nnote('nothing asserted')\n",
    "a failure caught by `except BaseException`":
        "from tcheck import ck\ntry:\n    ck('a', False)\nexcept BaseException:\n    pass\n"
        "ck('b', True)\n",
    "a failure inside a worker thread":
        "import threading\nfrom tcheck import ck\n"
        "t = threading.Thread(target=ck, args=('a', False)); t.start(); t.join()\n"
        "ck('b', True)\n",
    "a failed check inside `finally` cleanup":
        "import os, tempfile\nfrom tcheck import ck\nd = tempfile.mkdtemp()\n"
        "try:\n    ck('a', False)\nfinally:\n    os.rmdir(d)\n    print('cleaned', not os.path.exists(d))\n",
}


def run(src, fast):
    d = tempfile.mkdtemp(prefix="failfast-")
    try:
        shutil.copy(os.path.join(ROOT, "tcheck.py"), d)
        open(os.path.join(d, "test_p.py"), "w").write(src)
        env = dict(os.environ)
        env.pop("TCHECK_FAIL_FAST", None)
        if fast:
            env["TCHECK_FAIL_FAST"] = "1"
        t0 = time.time()
        p = subprocess.run([sys.executable, "-B", "test_p.py"], cwd=d, env=env,
                           capture_output=True, text=True, timeout=120)
        return p.returncode, p.stdout + p.stderr, time.time() - t0
    finally:
        shutil.rmtree(d, ignore_errors=True)


for why, src in SHAPES.items():
    full_rc, full_out, _ = run(src, False)
    fast_rc, fast_out, _ = run(src, True)
    eq(fast_rc != 0, full_rc != 0,
       "🔴 %s: red under fail-fast exactly when red in full (full rc %d)" % (why, full_rc))

rc_full, _, t_full = run(SHAPES["the first check fails, then slow work"], False)
rc_fast, out_fast, t_fast = run(SHAPES["the first check fails, then slow work"], True)
ck(rc_fast == 1 and t_fast < t_full - 2 and "✅ b" not in out_fast,
   "✅ ...and it does stop: nothing after the first failure ran (%.1fs vs %.1fs)"
   % (t_fast, t_full), "" if rc_fast == 1 and t_fast < t_full - 2 else shown(out_fast[-300:]))
_, out_fin, _ = run(SHAPES["a failed check inside `finally` cleanup"], True)
ck("cleaned True" in out_fin, "   ⚠️ ...and a `finally` still cleans up (SystemExit, not os._exit)",
   "" if "cleaned True" in out_fin else shown(out_fin[-300:]))

# ══════════════════════════════════════════════════════════════════════
section("2. ⛔ A CHILD THE TEST STARTS NEVER INHERITS THE MODE")
# ══════════════════════════════════════════════════════════════════════
rc, out, _ = run("import os, subprocess, sys\nfrom tcheck import ck\n"
                 "c = subprocess.run([sys.executable, '-c', "
                 "'import os; print(\"child sees\", repr(os.environ.get(\"TCHECK_FAIL_FAST\")))'],"
                 " capture_output=True, text=True)\n"
                 "print(c.stdout)\nck('ran', True)\n", True)
ck("child sees None" in out,
   "🔴🔴 a child started under fail-fast runs without it",
   "⛔ a planted file or a harness copy would stop early and answer a "
   "different question. %s" % ("" if "child sees None" in out else shown(out[-300:])))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 THE SWEEP ASKS FOR IT ON THE RED RUN, AND ONLY THERE")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ A planted declaration whose test exits 1 when the mode is ON and 0
#    when it is OFF, without importing tcheck (which would pop it). The
#    real `_tier2_one` must call it BITES: red under the mutation (mode
#    on), green on the revert (mode off).
d = tempfile.mkdtemp(prefix="failfast-sweep-")
try:
    open(os.path.join(d, "subject.py"), "w").write("X = 1\n")
    open(os.path.join(d, "test_mode.py"), "w").write(
        "# @vacuity the mode is on for the red run and off for the green\n"
        "#   file: subject.py\n#   find: X = 1\n#   with: X = 2\n"
        "import os, sys\n"
        "sys.exit(1 if os.environ.get('TCHECK_FAIL_FAST') == '1' else 0)\n")
    subprocess.run(["git", "init", "-q"], cwd=d, capture_output=True, timeout=60)
    eq(V.run_test("test_mode.py", d, red=True), 1, "   run_test(red=True) sets the mode")
    eq(V.run_test("test_mode.py", d), 0, "   run_test() does not")
    _r = V.tier2(d, jobs=1)
    eq([r["state"] for r in _r], ["BITES"],
       "🔴🔴 the sweep's red run is fail-fast and its green run is a full run")
finally:
    shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴🔴 A RUN THAT STOPS EARLY LEAVES NOTHING IN THE TEMP DIR")
# ══════════════════════════════════════════════════════════════════════
d = tempfile.mkdtemp(prefix="failfast-tmp-")
try:
    open(os.path.join(d, "test_leaky.py"), "w").write(
        "import os, sys, tempfile\n"
        "t = tempfile.mkdtemp(prefix='fixture-')\n"
        "open(os.path.join(t, 'copy.bin'), 'wb').write(b'x' * 1024)\n"
        "open('made.txt', 'w').write(t)\n"
        "sys.exit(1)   # dies before its own cleanup, like a red run\n")
    rc = V.run_test("test_leaky.py", d, red=True)
    made = open(os.path.join(d, "made.txt")).read().strip()
    ck(rc == 1 and made and not os.path.exists(made),
       "🔴🔴 the fixture a dead run left in its temp dir is gone",
       "rc=%s made=%r exists=%s" % (rc, made, os.path.exists(made)))
    ck(not made.startswith(tempfile.gettempdir() + os.sep + "fixture-"),
       "   ...because the run had a temp dir of its own, not the shared one",
       "made=%r" % made)
finally:
    shutil.rmtree(d, ignore_errors=True)

note("⛔ WHAT THIS DOES NOT CLAIM: that stopping early is safe for anything "
     "but the red run's exit code. Nothing reads a red run's output, and "
     "nothing else sets the mode.")
