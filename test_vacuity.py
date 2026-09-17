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

# ══════════════════════════════════════════════════════════════════════
# @vacuity the blind set is DERIVED, never an empty list
#   file: vacuity.py
#   find: return sorted(set(tests(root)) - declared - mapped)
#   with: return []
# ══════════════════════════════════════════════════════════════════════

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
   V.verdict([{"state": "BITES"}], False) == V.EXIT_UNREADABLE,
   "🔴 if the tree is dirty every result above is suspect and none of "
   "them may be reported as a pass. ⚠️ THIS ASKED A SUBSTRING QUESTION "
   "UNTIL 2026-09-15 — `\"EXIT_UNREADABLE\" in main\'s source` — which is "
   "rule 249, a check asserting its own prose. It now drives the "
   "judgement, which is strictly harder. Got %s"
   % V.verdict([{"state": "BITES"}], False))
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

section("5. 🔴🔴 THE EXIT CODE IS THE WHOLE INTERFACE, SO IT IS DRIVEN")
# ⛔ `main()` USED TO CLASSIFY INLINE AND NOTHING COULD REACH IT.
#    `[found by Sam, 2026-09-15]` Dropping two of the three bad states from
#    that tuple left this file GREEN while the harness printed "all bite"
#    with a planted vacuous guard sitting in the repo.
# 🔴 SAME SHAPE AS THE STALE-`.pyc` DEFECT IN SECTION 0, one layer up:
#    that one was the harness not SEEING the fire, this one was the harness
#    seeing it and reporting OK. Rule 274 twice over.
# ✅ THE FIX IS ALREADY IN THIS REPO: `runs_report.py` extracts `verdict()`
#    so `test_runs_report.py` can drive it. This drives the same shape.
_R = lambda s: {"tier": 2, "test": "planted.py", "state": s, "why": "w"}
ck("✅ a sweep where everything bites is exit 0",
   V.verdict([_R("BITES"), _R("BITES")], True) == V.EXIT_OK,
   "⛔ the other failure: a detector that never clears is one nobody "
   "reads. Got %s" % V.verdict([_R("BITES"), _R("BITES")], True))
for _s in ("VACUOUS", "RED_BOTH_WAYS", "MALFORMED"):
    ck("🔴🔴 one %s finding among passes is exit 1" % _s,
       V.verdict([_R("BITES"), _R(_s)], True) == V.EXIT_VACUOUS,
       "⛔ `vacuity.yml` branches on this number and on nothing else. A "
       "state missing from the tuple is a guard the nightly job will never "
       "report. Got %s" % V.verdict([_R("BITES"), _R(_s)], True))
ck("⚠️ a sweep that checked NOTHING is exit 2, not a pass",
   V.verdict([], True) == V.EXIT_UNREADABLE,
   "🔴 \"I could not look\" is the third state and CLAUDE.md's watcher "
   "family never closes an issue on it. Got %s" % V.verdict([], True))
ck("⛔ a leak OUTRANKS a finding — an unverifiable restore is not a restore",
   V.verdict([_R("VACUOUS")], False) == V.EXIT_UNREADABLE,
   "🔴 the harness rewrites source files. If the tree cannot be shown "
   "clean, every result above it is suspect. Got %s"
   % V.verdict([_R("VACUOUS")], False))

_VSRC = open(os.path.join(ROOT, "vacuity.py"), encoding="utf-8").read()
_MAIN = _VSRC.split("def main")[1]
ck("⛔ ...and main() no longer classifies at all — it returns that number",
   "verdict(" in _MAIN and 'r["state"]' not in _MAIN,
   "🔴 a judgement inlined in main() is a judgement no test can drive, "
   "which is how this hole opened in the first place")

# 📌 EVERY MUTATION NEEDS ITS OWN PROOF THAT IT LANDED AND STILL
#    COMPILES. Sam's first attempt at mutating a `finally:` here produced a
#    SyntaxError — which goes red for the WRONG reason and is
#    indistinguishable from a working guard. ⛔ A guard proven by a
#    mutation that does not compile is proven by nothing.
_FIND = '("VACUOUS", "RED_BOTH_WAYS", "MALFORMED")'
_WITH = '("MALFORMED",)'
ck("⚠️ the mutation is unambiguous — it matches vacuity.py exactly once",
   _VSRC.count(_FIND) == 1,
   "⛔ a `find` matching 0 or many is not a mutation — the harness says "
   "so about everyone else's declarations (rule 244). Got %d"
   % _VSRC.count(_FIND))
_MUT = _VSRC.replace(_FIND, _WITH)
ck("⚠️ ...and it LANDED", _MUT != _VSRC,
   "⛔ a no-op edit proves nothing about the check it is meant to break")
try:
    _CODE = compile(_MUT, "vacuity[mutated].py", "exec")
    _SYNTAX = ""
except SyntaxError as _e:
    _CODE, _SYNTAX = None, str(_e)
ck("📌 ...and the mutated file STILL COMPILES",
   _CODE is not None,
   "🔴 a SyntaxError turns the test red for the wrong reason and is "
   "indistinguishable from a working guard. Got: %s" % _SYNTAX)
_BLIND = {"__name__": "vacuity_mutated",
          "__file__": os.path.join(ROOT, "vacuity.py")}
if _CODE is not None:
    exec(_CODE, _BLIND)
ck("🔴🔴 UNDER THAT MUTATION THE HARNESS GOES BLIND, and the "
   "checks above are what stop it",
   _CODE is not None
   and _BLIND["verdict"]([_R("VACUOUS")], True) == V.EXIT_OK,
   "⛔ THIS IS THE HALF THAT MAKES THE REST NON-VACUOUS. If the mutated "
   "verdict still returns 1, the exit-code checks above would pass either "
   "way and prove nothing — rule 67. Got %s"
   % (_CODE is not None and _BLIND["verdict"]([_R("VACUOUS")], True)))

note("⛔ WHAT THIS DOES NOT CLAIM: that a guard the harness calls BITES is "
     "a GOOD guard. It claims only that it is not VACUOUS — that something "
     "about it depends on the thing it says it checks. ➡️ The two tiers "
     "catch different shapes, and neither replaces reading the check.")


section("6. 🔴🔴 THE THIRD HOLE — A TEST WITH NO PROOF OF ANY KIND")
# ⛔ Tier 1 reports what it cannot NAME-MAP. Tier 2 reports what it was
#    TOLD about. Neither reported the files that are in NEITHER, and a
#    test with no mapped subject and no declared mutation is checked by
#    nothing at all — while `CLAUDE.md` says every guard ships with the
#    mutation that proves it.
# 🔴 `[measured 2026-09-17]` 59 of 81 test files were in that set, and no
#    number anywhere in this repo said so. The nightly line read "(65
#    unmapped)", which looks like the whole gap and is not: 18 of those
#    unmapped files DO carry declarations.
_blind = V.blind(ROOT)
_all = V.tests(ROOT)
ck("⚠️ the blind set is DERIVED from the repo (%d of %d test file(s))"
   % (len(_blind), len(_all)),
   _blind and len(_all) > 50,
   "⛔ an empty blind set would make the ratchet below pass forever "
   "without checking anything (rule 67). Got %d of %d"
   % (len(_blind), len(_all)))
ck("⛔ ...and it really is files with NEITHER kind of proof",
   all(f not in V.name_map(ROOT) for f in _blind)
   and not ({d["test"] for d in V.declarations(ROOT)} & set(_blind)),
   "🔴 a file with a tier-1 subject or a tier-2 declaration is NOT blind, "
   "and counting it would inflate the number into noise")
ck("🔴🔴 THE BLIND SET HAS NOT GROWN (%d against a ceiling of %d)"
   % (len(_blind), V.BLIND_CEILING),
   len(_blind) <= V.BLIND_CEILING,
   "⛔ IF THIS FAILS BECAUSE YOU ADDED A TEST, DECLARE A MUTATION FOR IT "
   "— do not raise the number. `CLAUDE.md`: every fix ships with a guard, "
   "and a guard nothing has ever tried to break is a guard nobody has "
   "checked. Lowering the ceiling is the only edit that is automatically "
   "right. Newest blind file(s): %s" % _blind[-4:])
ck("⚠️ ...and the nightly run prints it, rather than only this file",
   "BLIND of" in open(os.path.join(ROOT, "vacuity.py"),
                      encoding="utf-8").read(),
   "⛔ a backlog only a contributor's local run can see is a backlog "
   "nobody is counting")
note("📌 WHAT THIS RATCHET DOES NOT CLAIM: that the other %d file(s) are "
     "wrong, or even weak. It claims only that NOTHING HAS EVER TRIED TO "
     "BREAK THEM, which is the state this whole harness exists to make "
     "visible rather than comfortable. ➡️ The ceiling comes down one "
     "declared mutation at a time." % len(_blind))
