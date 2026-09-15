#!/usr/bin/env python3
"""
THE VACUITY DETECTOR MUST NOT BE VACUOUS.

🔴🔴 RULE 274 IS THE FIRE-ALARM TEST THAT COULD NOT REPORT A FIRE. A
harness built to catch guards that prove nothing, which itself proves
nothing, is this repo's favourite joke told one level up — and it would
be the most expensive version of it, because everything downstream would
then be trusted.

✅ SO THE HARNESS IS DRIVEN AGAINST PLANTED GUARDS WITH KNOWN ANSWERS.
Two of them are deliberately vacuous and the harness MUST name them; two
genuinely bite and it MUST NOT. ⛔ Both halves matter: a detector that
calls everything vacuous is as useless as one that calls nothing vacuous,
and only the second half catches that.
"""
import os
import subprocess
import sys
import tempfile

from tcheck import ck, note, section

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vacuity as V  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))


def plant():
    """A tiny repo with two honest guards and two vacuous ones."""
    d = tempfile.mkdtemp(prefix="vacuity-self-")
    w = lambda n, s: open(os.path.join(d, n), "w", encoding="utf-8").write(s)
    # ── subjects ──
    w("pretend.py", "def answer():\n    return 42\n")
    w("pretend2.py", "def answer():\n    return 42\n")
    # ── TIER 1: one that depends on its subject, one that does not ──
    w("test_pretend.py",
      "import sys, pretend\nsys.exit(0 if pretend.answer() == 42 else 1)\n")
    w("test_pretend2.py",
      "import sys, pretend2\nsys.exit(0)   # never looks at its subject\n")
    # ── TIER 2: a declaration that bites, and one that does not ──
    w("test_declared_ok.py",
      "# @vacuity the answer must come from pretend.py\n"
      "#   file: pretend.py\n"
      "#   find: return 42\n"
      "#   with: return 43\n"
      "import sys, pretend\n"
      "sys.exit(0 if pretend.answer() == 42 else 1)\n")
    w("test_declared_vacuous.py",
      "# @vacuity claims to check the answer, and does not\n"
      "#   file: pretend2.py\n"
      "#   find: return 42\n"
      "#   with: return 43\n"
      "import sys, pretend2\n"
      "sys.exit(0)   # passes whatever pretend2 says\n")
    # ── a declaration whose `find` matches nothing ──
    w("test_declared_bad.py",
      "# @vacuity points at text that is not there\n"
      "#   file: pretend.py\n"
      "#   find: this string does not exist\n"
      "#   with: neither does this\n"
      "import sys\nsys.exit(0)\n")
    subprocess.run(["git", "init", "-q"], cwd=d, timeout=60)
    return d


section("0. 🔴🔴 THE RUNNER MUST SEE A MUTATION PYTHON WANTS TO CACHE AWAY")
# ⛔ THIS IS THE DEFECT THAT MADE THIS HARNESS VACUOUS BEFORE IT SHIPPED.
#    Python invalidates a `.pyc` on source mtime (WHOLE SECONDS) and size.
#    A tier-2 mutation is usually the SAME LENGTH as what it replaces, and
#    the harness rewrites/runs/reverts inside one second — so the stale
#    bytecode was reused and the MUTATED run returned 0 with the mutation
#    never taking effect.
# 🔴 AND MY FIRST ATTEMPT TO GUARD IT WAS A RACE: removing `-B` left the
#    planted-guard section GREEN, because tier 1 running first happened to
#    push the writes into different seconds. ⛔ A guard that only fails
#    when the clock cooperates is not a guard.
# ✅ SO THE MTIME IS FORCED IDENTICAL WITH `os.utime`. Deterministic, and
#    it asserts BOTH halves: a naive runner IS fooled here, and
#    `V.run_test` is NOT. The first half is what stops this check passing
#    on a machine where the trap does not exist.
_bc = tempfile.mkdtemp(prefix="vacuity-bytecode-")
_pp = os.path.join(_bc, "pretend.py")
open(_pp, "w", encoding="utf-8").write("def answer():\n    return 42\n")
open(os.path.join(_bc, "t_probe.py"), "w", encoding="utf-8").write(
    "import sys, pretend\nsys.exit(0 if pretend.answer() == 42 else 1)\n")
_naive = lambda: subprocess.run([sys.executable, "t_probe.py"], cwd=_bc,
                                capture_output=True, timeout=120).returncode
_naive()                                  # prime __pycache__
_st = os.stat(_pp)
open(_pp, "w", encoding="utf-8").write("def answer():\n    return 43\n")
os.utime(_pp, (_st.st_atime, _st.st_mtime))   # same mtime AND same size
ck("⚠️ the stale-bytecode trap is real on this machine",
   _naive() == 0,
   "⛔ if a naive runner already sees the mutation here, the check below "
   "proves nothing — it would pass on a platform where the trap cannot "
   "happen, which is rule 67. Got %d" % _naive())
ck("🔴🔴 run_test SEES a same-size mutation with an unchanged mtime",
   V.run_test("t_probe.py", _bc) != 0,
   "⛔ THIS IS THE HARNESS BEING VACUOUS IN THE WAY IT EXISTS TO DETECT. "
   "Without `-B` AND a purged __pycache__, the mutated run returns 0 and "
   "every tier-2 verdict is about an edit that never happened (rule 274, "
   "the fire alarm that cannot report a fire)")

note("⚠️ ONLY THE PURGE IS DRIVEN HERE, AND THAT IS STATED RATHER THAN "
     "IMPLIED: removing `_purge_pycache` turns the check above RED, "
     "removing `-B` alone does NOT — with the purge in place there is no "
     "stale `.pyc` left to read. ➡️ `-B` is the backstop for the case the "
     "purge fails silently (`rmtree(..., ignore_errors=True)` can), so it "
     "is kept and asserted as a constant, not driven. Same shape as "
     "`P_MAX` in test_calibration.py.")
ck("⚠️ ...and `-B` is still actually there, since nothing else pins it",
   '"-B"' in open(os.path.join(ROOT, "vacuity.py"), encoding="utf-8").read(),
   "⛔ a backstop nobody checks is a backstop that quietly disappears")

section("1. 🔴🔴 THE HARNESS, DRIVEN AGAINST PLANTED GUARDS")
_d = plant()
_t1 = {r["test"]: r for r in V.tier1(_d)}
ck("⚠️ tier 1 found both planted pairs to check",
   set(_t1) == {"test_pretend.py", "test_pretend2.py"},
   "⛔ a check over the wrong set proves nothing (rule 67). Got %s"
   % sorted(_t1))
ck("🔴🔴 TIER 1 NAMES THE PLANTED VACUOUS GUARD",
   _t1.get("test_pretend2.py", {}).get("state") == "VACUOUS",
   "⛔ THIS IS THE WHOLE POINT. `test_pretend2.py` passes with its "
   "subject gutted and the harness must say so. Got %s"
   % _t1.get("test_pretend2.py", {}).get("state"))
ck("✅ ...and does NOT accuse the honest one",
   _t1.get("test_pretend.py", {}).get("state") == "BITES",
   "⛔ a detector that calls everything vacuous is as useless as one "
   "that calls nothing vacuous — and only this half catches that. Got %s"
   % _t1.get("test_pretend.py", {}).get("state"))

_t2 = {r["test"]: r for r in V.tier2(_d)}
ck("⚠️ tier 2 found all three planted declarations",
   set(_t2) == {"test_declared_ok.py", "test_declared_vacuous.py",
                "test_declared_bad.py"},
   "⛔ a declaration the harness never parses is a guard silently "
   "skipped. Got %s" % sorted(_t2))
ck("🔴🔴 TIER 2 NAMES THE GUARD THAT SURVIVES ITS OWN DECLARED MUTATION",
   _t2.get("test_declared_vacuous.py", {}).get("state") == "VACUOUS",
   "⛔ this is the kind tier 1 cannot reach — the subject is untouched "
   "and another file's constant is what matters. Got %s"
   % _t2.get("test_declared_vacuous.py", {}).get("state"))
ck("✅ ...and does NOT accuse the one that bites",
   _t2.get("test_declared_ok.py", {}).get("state") == "BITES",
   "⛔ red under the mutation AND green on the revert. Got %s"
   % _t2.get("test_declared_ok.py", {}).get("state"))
ck("⛔ a declaration whose `find` matches nothing is MALFORMED, not a skip",
   _t2.get("test_declared_bad.py", {}).get("state") == "MALFORMED",
   "🔴 THE STRIPPED-COMMENT FAILURE ONE LEVEL UP (rule 244): a mutation "
   "that matches 0 times changes nothing, so the test 'passes' having "
   "been asked nothing. Got %s"
   % _t2.get("test_declared_bad.py", {}).get("state"))

section("2. ⛔ IT REPORTS. IT NEVER EDITS.")
_before = V._porcelain(ROOT)
_real2 = V.tier2(ROOT)
_ok, _dirt = V.leaked(_before, ROOT)
ck("🔴🔴 the harness leaves NOTHING behind after mutating real files",
   _ok,
   "⛔ it rewrites cfbd_budget.py and cfbd.yml in place. A leaked "
   "mutation would be committed by the next collector run. Leaked: %r"
   % _dirt)
ck("⛔ ...and a leak would make the whole run UNREADABLE, not clean",
   "EXIT_UNREADABLE" in open(os.path.join(ROOT, "vacuity.py"),
                             encoding="utf-8").read().split("def main")[1],
   "🔴 if the tree is dirty every result above is suspect and none of "
   "them may be reported as a pass")
ck("⛔ ...and it fails closed when git cannot be asked",
   V.leaked(None, ROOT)[0] is False,
   "🔴 the harness rewrites source files; an unverifiable restore is not "
   "a restore")
ck("⛔ the harness never deletes or rewrites a guard it accuses",
   "DO NOT DELETE OR WEAKEN" in V.render(
       [{"tier": 1, "test": "x.py", "state": "VACUOUS", "why": "w"}], [], []),
   "🔴 CLAUDE.md forbids removing a check outright. A weak guard removed "
   "is strictly worse than a weak guard reported")

section("3. 🔴 THE MAPPING IS NAME-ONLY, AND THAT WAS MEASURED")
# ⛔ A looser rule ("the one non-test module this file imports") produced
#    FOUR accusations on 2026-09-15 and ALL FOUR WERE WRONG.
_um = V.unmapped(ROOT)
for _f in ("test_scores_live.py", "test_card_revert.py", "test_names.py",
           "test_tcheck_guard.py"):
    ck("⛔ %s is UNMAPPED, not accused" % _f,
       _f in _um,
       "🔴 the loose mapping called this vacuous and it was a MIS-MAP — "
       "it tests index.html / a workflow / every .py in the repo / "
       "tcheck.py. A vacuity detector that cries wolf is rule 238 aimed "
       "at the one channel that has to be trustworthy")
ck("⚠️ the unmapped set is REPORTED, never silently skipped",
   "UNMAPPED and tier 1 says nothing about them" in V.render([], [], _um),
   "⛔ an unmapped file skipped in silence is the same vacuity one level "
   "up — which is the defect this whole file exists for")
ck("⚠️ name-mapping still covers the pairs it should",
   V.name_map(ROOT).get("test_cfbd_watch.py") == "cfbd_watch.py"
   and V.name_map(ROOT).get("test_budget_watch.py") == "budget_watch.py",
   "🔴 conservative is not the same as empty. Got %d pair(s)"
   % len(V.name_map(ROOT)))

section("4. ✅ THE TWO REAL BACK-FILLED MUTATIONS BOTH BITE")
_by = {(r["file"], r["find"]): r for r in _real2}
ck("🔴🔴 the CFBD bar mutation turns test_cfbd_watch.py red",
   _by.get(("cfbd_budget.py", "if pct >= 80:"), {}).get("state") == "BITES",
   "⛔ this is the exact edit that left the suite GREEN on 2026-09-15 "
   "with the two bars disagreeing. Got %s"
   % _by.get(("cfbd_budget.py", "if pct >= 80:"), {}).get("state"))
ck("🔴🔴 the issue-in-place mutation turns it red too",
   any(r["state"] == "BITES" and r["file"].endswith("cfbd.yml")
       for r in _real2),
   "⛔ the other one Sam found by hand: `gh issue edit` -> a fresh `gh "
   "issue create`, a new quota issue every day. Got %s"
   % [(r["file"], r["state"]) for r in _real2])
note("tier 2 currently covers %d declared mutation(s); tier 1 covers %d "
     "name-mapped pair(s); %d test file(s) are unmapped and reported every "
     "run." % (len(_real2), len(V.name_map(ROOT)), len(_um)))

note("⛔ WHAT THIS DOES NOT CLAIM: that a guard the harness calls BITES is "
     "a GOOD guard. It claims only that it is not VACUOUS — that something "
     "about it depends on the thing it says it checks. ➡️ The two tiers "
     "catch different shapes, and neither replaces reading the check.")
