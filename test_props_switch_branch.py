#!/usr/bin/env python3
r"""test_props_switch_branch.py — the branch a §3i WINS pushes passes its own tests.

`[review, 2026-10-27]` A T74 WINS (research/fb_refit_spec.md §3i) pushes one branch whose only
change is that league's line in `card_fb.PROPS_SEASONS` (fb_refit.set_props_seasons). Sam's
email tells him to wait for "All checks have passed" before merging it. The first version's
tests read the live switch as if it could never be on, so on that branch they went red: the
PR could never turn green, and merged anyway every collect run would have.
✅ THE CLASS: for each league, the tests that read the switch are run on a copy of the code
with that one edit made, exactly as the branch would hold it, and must pass. A test file that
starts reading the switch must be added to SWITCH_TESTS (it reads PROPS_SEASONS or LAST_TWO).

# @vacuity the props-seasons test sets the switch, never reads it
#   file: test_fb_props_seasons.py
#   find: CF.PROPS_SEASONS.update(nfl="all", ncaaf="all")  # SET, never read
#   with: pass  # SET, never read
#
# @vacuity the card test sets the switch, never reads it
#   file: test_fb_props_confidence.py
#   find:         cf.PROPS_SEASONS["nfl"] = cf.LAST_TWO if last_two else "all"
#   with:         cf.PROPS_SEASONS["nfl"] = cf.LAST_TWO if last_two else cf.PROPS_SEASONS["nfl"]
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
from tcheck import ck, eq, section, shown  # noqa: E402

import fb_refit as R  # noqa: E402

SWITCH_TESTS = ("test_fb_props_seasons.py", "test_fb_props_confidence.py")

section("1. every test that reads the props switch is named here")
_readers = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "test_*.py"))
                  if os.path.basename(p) != os.path.basename(__file__)
                  and re.search(r"PROPS_SEASONS|LAST_TWO|props_suffix",
                                open(p, encoding="utf-8").read()))
eq(_readers, sorted(SWITCH_TESTS), "🔴 a new test that reads the switch is run on the switched branch too")

section("2. 🔴 on the branch a WINS pushes, for either league, those tests pass")
_src = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
for lg in ("nfl", "ncaaf"):
    t = tempfile.mkdtemp(prefix="props-switch-%s-" % lg)
    try:
        for f in glob.glob(os.path.join(ROOT, "*")):          # the code and the page, not data/
            if os.path.isfile(f):
                shutil.copy(f, t)
        if os.path.isdir(os.path.join(ROOT, "research")):
            shutil.copytree(os.path.join(ROOT, "research"), os.path.join(t, "research"))
        with open(os.path.join(t, "card_fb.py"), "w", encoding="utf-8", newline="") as fh:
            fh.write(R.set_props_seasons(re.sub(r'(?m)^(    "%s": )LAST_TWO,' % lg, r'\g<1>"all",', _src), lg))
        env = dict(os.environ, PYTHONUTF8="1", ODDS_API_KEY="")
        env.pop("LEAGUE", None)
        for test in SWITCH_TESTS:
            p = subprocess.run([sys.executable, test], cwd=t, env=env, capture_output=True, text=True, timeout=900)
            ck(p.returncode == 0, "🔴 %s passes with the %s switch on, as its branch holds it" % (test, lg),
               shown((p.stdout or "")[-600:] + (p.stderr or "")[-300:]))
    finally:
        shutil.rmtree(t, ignore_errors=True)
