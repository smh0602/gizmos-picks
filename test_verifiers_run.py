#!/usr/bin/env python3
"""🔴 A VERIFIER NOTHING INVOKES, RUNS NEVER — RULE 78.

`[measured 2026-09-19]` `verify_nfl.py` — whose own header says it
*"caught four real defects, two before Sam saw them"* — was invoked by
**no workflow and no test**. Its only four mentions in the repository
are comments in `cfb.py` and `nfl.py`. It had been failing on the live
tree the entire time and there was no way to know:

    5 FAILED   snap coverage on QB/RB/WR/TE
               `ahead_out` is CONSTANT across 1,117 rows
               `week` is CONSTANT across 1,117 rows
               `ahead_out` resolves
               vs-position has no defences at all

Three of those five turned out to be the verifier firing on correct
early-season data; the other two are real, and one of them —
`players-2026.json.gz` holding week 1 while the schedule already records
finals for weeks 1 and 2 — is the visible edge of a 47-hour nflverse
outage.

⛔ SO THE RULE IS MECHANICAL. Every top-level `verify_*.py` must be
reachable from something that runs on a schedule, or from a test. The
list is DERIVED from the repository, so a verifier added next month is
covered by the same line.

# @vacuity 🔴 a verifier nothing invokes is caught
#   file: .github/workflows/collect.yml
#   find:               python verify_nfl.py --current \\
#   with:               true verify_nfl.py --current \\
"""
import glob
import io
import os
import re
import subprocess
import sys

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
WF = sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")))
VERIFIERS = sorted(os.path.basename(p)
                   for p in glob.glob(os.path.join(ROOT, "verify_*.py")))

WF_TEXT = {os.path.basename(f): io.open(f, encoding="utf-8").read()
           for f in WF}
TEST_TEXT = {os.path.basename(p): io.open(p, encoding="utf-8").read()
             for p in glob.glob(os.path.join(ROOT, "test_*.py"))}


def invoked_by_workflow(name):
    """`python verify_x.py` as a COMMAND, never a mention in prose."""
    stem = name[:-3]
    pat = re.compile(r"(?<![#\w])python3?\s+%s\.py\b" % re.escape(stem))
    return sorted(w for w, txt in WF_TEXT.items()
                  if any(pat.search(ln.split("#")[0]) for ln in txt.split("\n")))


def used_by_test(name):
    stem = name[:-3]
    pat = re.compile(r"(?<![#\w])(import\s+%s\b|%s\.py)" % (re.escape(stem),
                                                            re.escape(stem)))
    out = []
    for t, txt in TEST_TEXT.items():
        for ln in txt.split("\n"):
            code = ln.split("#")[0]
            if pat.search(code):
                out.append(t)
                break
    return sorted(out)


# ════════════════════════════════════════════════════════════════════════
section("1. 🔴 EVERY VERIFIER IS REACHED BY SOMETHING THAT RUNS")
# ════════════════════════════════════════════════════════════════════════
ck("⚠️ the verifiers were discovered from the repo, not listed here",
   len(VERIFIERS) >= 4,
   "⛔ a hardcoded list goes stale the first time one is added — which "
   "is exactly how `verify_nfl.py` went unrun. found %s" % VERIFIERS)

orphans = []
for v in VERIFIERS:
    wfs, tests = invoked_by_workflow(v), used_by_test(v)
    note("%-22s workflows=%s tests=%s"
         % (v, wfs or "—", (tests[:3] + ["…"] if len(tests) > 3 else tests)
            or "—"))
    if not wfs and not tests:
        orphans.append(v)
ck("🔴🔴 no verifier is invoked by nothing",
   not orphans,
   "⛔ RULE 78. `verify_nfl.py` sat like this and was failing the whole "
   "time. A check nobody runs is not cover, it is the belief in cover. "
   "orphans: %s" % (orphans or "none"))

ck("🔴 ...and `verify_nfl.py` is reached by a WORKFLOW, not only a test",
   bool(invoked_by_workflow("verify_nfl.py")),
   "⛔ a test proves it still works; only a scheduled run proves it "
   "still looks. got %s" % invoked_by_workflow("verify_nfl.py"))

# ⛔ AND PROSE IS NOT AN INVOCATION — the trap that made this finding
#    hard to see in the first place.
ck("⛔ a mention in a COMMENT is not an invocation",
   not invoked_by_workflow("no_such_verifier.py"),
   "sanity: an unknown name must resolve to nothing")
_fake = "# python verify_nfl.py is discussed here"
ck("⛔ ...and a commented-out command is not one either",
   not re.compile(r"(?<![#\w])python3?\s+verify_nfl\.py\b").search(
       _fake.split("#")[0]),
   "🔴 `verify_nfl.py`'s four references in cfb.py and nfl.py are ALL "
   "comments. A matcher that counted them would have reported this "
   "verifier as covered — the exact false clean bill the audit warns "
   "about.")

# ════════════════════════════════════════════════════════════════════════
section("2. ⚠️ AND THE ONE BEING WIRED IN RUNS THE CURRENT SEASON")
# ════════════════════════════════════════════════════════════════════════
COLLECT = WF_TEXT.get("collect.yml", "")
ck("⚠️ the football verifier is scoped to the season the run built",
   re.search(r"python3?\s+verify_nfl\.py\s+--current", COLLECT) is not None,
   "⛔ a whole-history sweep would gate today's football job on 2022's "
   "snap coverage (78.3%) — a real gap this job did not create and "
   "cannot repair. A bare `python verify_nfl.py` still reports it.")
ck("🔴 ...and a failure turns the run red rather than being swallowed",
   re.search(r"verify_nfl\.py --current[^\n]*\n[^\n]*rc=1", COLLECT)
   is not None,
   "⛔ `CLAUDE.md`: a green tick that proves nothing is worse than a "
   "red one. The verifier has to be able to fail the job.")
ck("⛔ ...and it runs AFTER the commit, like MLB's verifiers",
   COLLECT.index("verify_nfl.py") > COLLECT.index("collect[$LEAGUE_NAME]"),
   "🔴 the data it checks cost credits and cannot be re-bought; a "
   "failure must turn the run red WITHOUT discarding the snapshot. "
   "That is the rule the MLB verifiers already follow.")


# ════════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 AND 'NOT YET MEASURABLE' IS NOT A PASS")
# ════════════════════════════════════════════════════════════════════════
# ⛔ Three of `verify_nfl.py`'s five failures were the verifier firing on
#    correct early-season data — a constancy test read in week 1, when
#    `ahead_out` is 0 across ALL of 2025's week-1 rows too. Those became
#    a THIRD verdict rather than being deleted, and a third verdict is
#    only honest if it can never be mistaken for a pass.
r = subprocess.run([sys.executable, "-B", os.path.join(ROOT, "verify_nfl.py"),
                    "--current"], cwd=ROOT, capture_output=True, text=True,
                   timeout=600)
out = (r.stdout or "") + (r.stderr or "")
m = re.search(r"(\d+) passed, (\d+) not yet measurable, (\d+) warnings, "
              r"(\d+) FAILED", out)
ck("⚠️ the verifier reports all four states in its summary",
   m is not None,
   "⛔ a state that is not printed is a state nobody can audit. "
   "tail=%r" % out[-220:])
if m:
    npass, nnym, _nwarn, nfail = (int(x) for x in m.groups())
    ck("🔴🔴 a NOT-YET-MEASURABLE is counted apart from a pass",
       nnym >= 1,
       "⛔ if it were folded into `passed`, this whole distinction "
       "would be a way of quietly going green. got %s" % (m.group(0),))
    ck("🔴 ...and the exit code follows the FAILURES only",
       (r.returncode == 1) == (nfail > 0),
       "⛔ the job gates on this number. rc=%s fails=%d"
       % (r.returncode, nfail))
    ck("🔴🔴 ...and on this tree it is RED, for a real and current reason",
       nfail >= 1 and "the logs cover every week the schedule calls final"
       in out,
       "⛔ `players-2026.json.gz` holds week 1 while the schedule "
       "already records finals for weeks 1 AND 2 — the visible edge of "
       "a 47-hour nflverse outage. This check is the point of the "
       "whole change; if it ever passes by accident, say so. %s"
       % (m.group(0),))
    note("verify_nfl --current on this tree: %s" % m.group(0))
