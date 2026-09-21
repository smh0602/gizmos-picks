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
#   find: python verify_nfl.py --current
#   with: true verify_nfl.py --current
# ⚠️ ~~`python verify_nfl.py --current \\`~~ — the trailing backslash
#    was written DOUBLED, because this declaration lives in a Python
#    docstring and the habit is to escape it. ⛔ `vacuity.py` reads the
#    declaration out of the FILE TEXT with a regex, not out of the
#    parsed string, so it searched `collect.yml` for two backslashes
#    and found ZERO — a mutation that changes nothing, rule 244.
#    ✅ The continuation is simply not part of the `find` any more, so
#    there is no backslash left to get wrong.
#
# @vacuity 🔴🔴 snap coverage is judged week by week, not pooled
#   file: verify_nfl.py
#   find:     thin = [w for w in complete if frac[w] < SNAP_MIN]
#   with:     thin = []
#
# @vacuity 🔴 the newest-week grace expires
#   file: verify_nfl.py
#   find:             early = (pull - last).total_seconds() < SNAP_LAG_DAYS * 86400
#   with:             early = True
#
# @vacuity ⛔ only the schedule decides a week is unfinished
#   file: verify_nfl.py
#   find:     complete = sorted(w for w in frac if st is None or (st.get(w) or (False,))[0])
#   with:     complete = sorted(frac)
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
# ══════════════════════════════════════════════════════════════════════
# 🔴 ~~`nnym >= 1` and "RED, for a real and current reason" ON THE LIVE
#    TREE~~ — REPLACED 2026-09-21. ⛔ BOTH ASKED THE WRONG QUESTION: they
#    asserted what the live data looked like in week 2 ("something is not
#    yet measurable", "the logs are behind"), so they went red the moment
#    the season moved on and the data caught up — on every collect run
#    from 2026-09-20. ⛔ And the second one passed BY ACCIDENT: the text
#    it looked for, "the logs cover every week the schedule calls final",
#    is the name of a check, printed on its PASS line too.
# ✅ THE BEHAVIOUR IS NOW DRIVEN ON A FIXTURE WHOSE STATE CANNOT DRIFT,
#    and the live tree gets only the assertions that hold in every week.
# ══════════════════════════════════════════════════════════════════════
import verify_nfl as V  # noqa: E402


def _drive(weeks, status, pulled_at):
    """weeks: {week: (rows, rows_with_snaps)} -> (PASS, NYM, FAIL) names."""
    for lst in (V.PASS, V.FAIL, V.WARN, V.NYM):
        del lst[:]
    rows = []
    for w, (n, h) in weeks.items():
        rows += [("p%d_%d" % (w, i), {"pos": "WR"},
                  dict({"week": w}, **({"snap_pct": 0.5} if i < h else {})))
                 for i in range(n)]
    _o = sys.stdout
    sys.stdout = io.StringIO()
    try:
        V.check_snap_coverage(2099, rows, pulled_at, status=status)
    finally:
        sys.stdout = _o
    return list(V.PASS), list(V.NYM), list(V.FAIL)


_FULL = (100, 100)
# a. week 1 complete, week 2 half-played and thin — the 2026-09-21 tree
ps, ny, fl = _drive({1: _FULL, 2: (100, 6)},
                    {1: (True, "2099-09-14T20:15"), 2: (False, "2099-09-21T20:15")},
                    "2099-09-21T07:52:26Z")
ck("🔴🔴 a week still being played is NOT YET MEASURABLE — and not a pass",
   not fl and any("week 2" in n for n in ny)
   and not any("week 2" in n for n in ps),
   "⛔ folding it into `passed` would make the third verdict a way of "
   "quietly going green. PASS=%s NYM=%s FAIL=%s" % (ps, ny, fl))
ck("   ...while the complete week IS judged, and passes on its own",
   any("every complete week" in n for n in ps), "PASS=%s" % ps)
# a2. ...and it is the SCHEDULE that says so, not the pull's timing: a
#     week with a postponed game is still not complete a fortnight on.
ps, ny, fl = _drive({1: _FULL, 2: (100, 6)},
                    {1: (True, "2099-09-14T20:15"), 2: (False, "2099-09-21T20:15")},
                    "2099-10-05T07:52:26Z")
ck("⛔ ...because the SCHEDULE says the week is unfinished, however late "
   "the pull",
   not fl and any("week 2" in n for n in ny),
   "NYM=%s FAIL=%s" % (ny, fl))

# b. an interior week missing — pooled this is 80.0% and PASSED
ps, ny, fl = _drive({1: _FULL, 2: _FULL, 3: (100, 0), 4: _FULL, 5: _FULL},
                    {w: (True, "2099-09-%02dT20:15" % (7 * w)) for w in range(1, 6)},
                    "2099-10-10T07:00:00Z")
ck("🔴🔴 a whole missing week can no longer hide behind full ones",
   bool(fl) and not ny,
   "⛔ 4 weeks at 100%% and one at 0%% pools to exactly the 80%% bar. "
   "FAIL=%s NYM=%s" % (fl, ny))

# c. the latest complete week is thin: early pull = NYM, late pull = FAIL
_st = {1: (True, "2099-09-14T20:15"), 2: (True, "2099-09-21T20:15")}
ps, ny, fl = _drive({1: _FULL, 2: (100, 6)}, _st, "2099-09-22T07:52:00Z")
ck("🔴 the newest complete week, pulled before nflverse posted it, is "
   "NOT YET MEASURABLE",
   not fl and any("week 2" in n for n in ny), "NYM=%s FAIL=%s" % (ny, fl))
ps, ny, fl = _drive({1: _FULL, 2: (100, 6)}, _st, "2099-09-28T07:52:00Z")
ck("🔴🔴 ...and the grace EXPIRES: a week later it is a FAILURE",
   bool(fl) and not ny,
   "⛔ a grace with no end is a switched-off check. FAIL=%s NYM=%s"
   % (fl, ny))
ps, ny, fl = _drive({1: (100, 6), 2: _FULL}, _st, "2099-09-22T07:52:00Z")
ck("⛔ ...and it NEVER reaches an interior week, however early the pull",
   bool(fl), "FAIL=%s" % fl)

# d. no schedule to read: nothing is excused
ps, ny, fl = _drive({1: _FULL, 2: (100, 6)}, None, "2099-09-22T07:52:00Z")
ck("⛔ with no schedule artifact, every week is judged — nothing excused",
   bool(fl) and not ny, "FAIL=%s NYM=%s" % (fl, ny))

# the live tree: only what holds in every week of every season
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
    ck("🔴 ...and the exit code follows the FAILURES only",
       (r.returncode == 1) == (nfail > 0),
       "⛔ the job gates on this number. rc=%s fails=%d"
       % (r.returncode, nfail))
    ck("🔴 ...and every FAILED line is also an ::error:: annotation",
       nfail == out.count("::error::"),
       "⛔ a failure the Actions page does not show is a failure Sam "
       "cannot find. %d failed, %d annotated" % (nfail, out.count("::error::")))
    note("verify_nfl --current on this tree: %s" % m.group(0))
