#!/usr/bin/env python3
"""🔴🔴 THE NIGHTLY SWEEPS IN PARTS, AND A PART THAT NEVER REPORTED IS NEVER A PASS.

`[2026-11-01]` On one runner the nightly's 120-minute clock ran out on 9 of
its last 15 nights. A timed-out sweep prints nothing, and Tell Sam read that
empty state as a finding: it wrote an empty body over issue #249 all 9 nights,
with 4 real findings in it. `vacuity.yml` now sweeps in four jobs and one more
reports, through `vacuity.py --merge`.

⛔ A SPLIT IS ONLY SAFE IF THE PIECES ARE JUDGED AS THE WHOLE. The new way to be
wrong is a clean answer about a share of the sweep: three parts report nothing
bad, the fourth died, and the issue closes. So this file asks:
  1. `merge()` on planted reports: every clean part -> 0; any finding -> 1;
     a part missing with nothing bad -> 2, NEVER 0; a finding with a part
     missing -> 3, NEVER 1; a leak -> 2; nothing -> 2.
  2. `main()` writes what `merge()` reads; unset, it writes nothing and sweeps
     everything, which is what the deployed nightly does until Sam's upload.
  3. The real program, run on a planted repo: the parts add up to the whole.
  4. The workflow as it will be live: the report job runs whatever happened to
     the parts, a run that could not look is RED, and so is a short report,
     which is added to the issue and never written over it.

⚠️ CLASS OR INSTANCE. Section 4 is this one workflow (no other sweeps in parts).
The class, "an empty state or report writes to no issue", is
test_budget_watch.py §2.

⚠️ A step this file runs is picked by what it DOES, never by name, except the
last one, which writes nothing: `test_step_tmp.py` treats a step named by a
test that starts bash as driven, and the other three keep their fixed /tmp paths
(Tell Sam reads one). `run_step` points those at a directory of its own.

# @vacuity 🔴🔴 a part that never reported can never read as clean
#   file: vacuity.py
#   find:     if rc == EXIT_OK and gaps:
#   with:     if False:
#
# @vacuity 🔴🔴 a missing part is noticed at all
#   file: vacuity.py
#   find:                  if k not in have]
#   with:                  if False]
#
# @vacuity 🔴 a leak in any one part outranks the rest
#   file: vacuity.py
#   find:     leak_ok = all(rep["leak_ok"] for rep in reports)
#   with:     leak_ok = True
#
# @vacuity 🔴🔴 every part's tier 2 findings reach the report
#   file: vacuity.py
#   find:     t2 = [row for rep in reports for row in rep["t2"]]
#   with:     t2 = []
#
# @vacuity 🔴 every part's tier 1 findings reach the report
#   file: vacuity.py
#   find:     t1 = [row for rep in reports for row in rep["t1"]]
#   with:     t1 = []
#
# @vacuity 🔴 the report says which parts are missing
#   file: vacuity.py
#   find:     if gaps:
#   with:     if False:
#
# @vacuity ⛔ a report nobody can read is a gap, not a skip
#   file: vacuity.py
#   find:             gaps.append("`%s` cannot be read (%s: %s)"
#   with:             str("`%s` cannot be read (%s: %s)"
#
# @vacuity ⛔ parts that disagree on N are not one sweep
#   file: vacuity.py
#   find:         gaps.append("the parts disagree on how many there are: %s" % ns)
#   with:         pass
#
# @vacuity ⛔ one part reported twice is not two parts
#   file: vacuity.py
#   find:              for k in sorted(set(have)) if have.count(k) > 1]
#   with:              for k in []]
#
# @vacuity 🔴 no report at all says so
#   file: vacuity.py
#   find:         return [], gaps + ["no part reported"]
#   with:         return [], gaps
#
# @vacuity 🔴🔴 a nightly part leaves its report for `watch`
#   file: vacuity.py
#   find:     if os.environ.get("VACUITY_OUT"):
#   with:     if False:
#
# @vacuity ⛔ a test the sweep runs never inherits the sweep's report path
#   file: vacuity.py
#   find:         env.pop("VACUITY_OUT", None)
#   with:         pass
#
# @vacuity 🔴🔴 a crash is "could not look", never exit 1 (exit 1 is a finding)
#   file: vacuity.py
#   find:         sys.exit(EXIT_UNREADABLE)
#   with:         raise
#
# @vacuity 🔴🔴 the report job runs whatever happened to the parts
#   file: docs/upload/vacuity.yml
#   find:     if: always() # a part that ran out its clock must not skip the report
#   with:     if: success()
#
# @vacuity 🔴 the report job waits for the parts
#   file: docs/upload/vacuity.yml
#   find:     needs: sweep
#   with:     needs: []
#
# @vacuity 🔴 one part failing does not cancel the others
#   file: docs/upload/vacuity.yml
#   find:       fail-fast: false
#   with:       fail-fast: true
#
# @vacuity 🔴🔴 a run that could not look is red, on an EMPTY state too
#   file: docs/upload/vacuity.yml
#   find:             ok|bad) echo "the sweep reported: $STATE" ;;
#   with:             ok|bad|"") echo "the sweep reported: $STATE" ;;
#
# @vacuity 🔴🔴 ...and `unknown` is red at all
#   file: docs/upload/vacuity.yml
#   find:             *) echo "::error::the nightly sweep could not look (state '$STATE')"; exit 1 ;;
#   with:             *) ;;
#
# @vacuity 🔴🔴 exit 2 is never read as a finding (that is the wipe, again)
#   file: docs/upload/vacuity.yml
#   find:           elif [ "$rc" = "1" ]; then
#   with:           elif [ "$rc" = "2" ]; then
#
# @vacuity 🔴 the report job merges the parts, it does not sweep again
#   file: docs/upload/vacuity.yml
#   find:           python vacuity.py --merge "$PARTS" > /tmp/vacuity.md 2>/tmp/vacuity.err
#   with:           python vacuity.py "$PARTS" > /tmp/vacuity.md 2>/tmp/vacuity.err
#
# @vacuity 🔴 a part that left a mutation behind does not report
#   file: docs/upload/vacuity.yml
#   find:             rm -f "$VACUITY_OUT"
#   with:             true
#
# @vacuity 🔴🔴 a finding with a part missing is not a whole report
#   file: vacuity.py
#   find:     return EXIT_PARTIAL if rc == EXIT_VACUOUS and gaps else rc
#   with:     return rc
#
# @vacuity 🔴🔴 ...the report job reads that as its own state
#   file: docs/upload/vacuity.yml
#   find:           elif [ "$rc" = "3" ]; then
#   with:           elif [ "$rc" = "9" ]; then
#
# @vacuity 🔴🔴 ...a short report never replaces a full one
#   file: docs/upload/vacuity.yml
#   find:           if [ -n "$NUM" ] && [ "$STATE" = "partial" ]; then
#   with:           if false; then
#
# @vacuity 🔴🔴 ...and the run goes red with the finding reported
#   file: docs/upload/vacuity.yml
#   find:             partial) echo "::error::a part of the nightly sweep never reported; the issue has what the others found"; exit 1 ;;
#   with:             partial) ;;
#
# @vacuity 🔴 the reports reach the report job
#   file: docs/upload/vacuity.yml
#   find:           pattern: vacuity-part-*
#   with:           pattern: nothing-*
#
# @vacuity 🔴 ...from where the sweep wrote them
#   file: docs/upload/vacuity.yml
#   find:           path: ${{ runner.temp }}/vacuity-part.json
#   with:           path: vacuity-part.json
"""
import contextlib
import fnmatch
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import vacuity as V
import wfparse as W
from tcheck import ck, note, section, shown

ROOT = os.path.dirname(os.path.abspath(__file__))
ENV = ("VACUITY_PART", "VACUITY_OUT")
_trees = []


def tree():
    d = tempfile.mkdtemp(prefix="vmerge-")
    _trees.append(d)
    return d


PAIR = {"tier": 1, "test": "test_pair.py", "subject": "pair.py",
        "state": "BITES", "why": "goes red"}
MUT = {"tier": 2, "test": "test_mut.py", "state": "BITES", "why": "red, then green"}
FOUND2 = {"tier": 2, "test": "test_found2.py", "state": "VACUOUS",
          "why": "passes under its own mutation"}
FOUND1 = {"tier": 1, "test": "test_found1.py", "subject": "found1.py",
          "state": "VACUOUS", "why": "passes with its subject gutted"}


def P(k, n=4, t1=(PAIR,), t2=(MUT,), leak_ok=True, dirty=""):
    return ((k, n), list(t1), list(t2), leak_ok, dirty)


def plant(*reports):
    """A folder laid out as download-artifact leaves it. -> its path."""
    d = tree()
    for i, r in enumerate(reports):
        V.write_part(os.path.join(d, "vacuity-part-%d" % i, "vacuity-part.json"), *r)
    return d


def M(d):
    """`merge(d)`. -> (rc, everything it printed)."""
    o = io.StringIO()
    with contextlib.redirect_stdout(o), contextlib.redirect_stderr(o):
        rc = V.merge(d)
    return rc, o.getvalue()


# ════════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 merge() ON PLANTED REPORTS: ONE JUDGEMENT OVER THE UNION")
# ════════════════════════════════════════════════════════════════════════
_rc, _o = M(plant(P(1), P(2), P(3), P(4)))
ck("✅ all four in and clean is exit 0", _rc == V.EXIT_OK,
   "⛔ a report that never clears is one nobody reads. rc=%s %s" % (_rc, _o[:200]))
ck("✅ ...and says the whole sweep's numbers",
   "tier1 4 pair(s), tier2 4 mutation(s), all bite" in _o,
   "⛔ the union, not one part's share. %s" % _o[:200])

_rc, _o = M(plant(P(1), P(2, t2=[MUT, FOUND2]), P(3), P(4)))
ck("🔴🔴 one finding in one part is exit 1, and the report names it",
   _rc == V.EXIT_VACUOUS and "test_found2.py" in _o and FOUND2["why"] in _o,
   "⛔ `vacuity.yml` branches on this number. rc=%s %s" % (_rc, _o[:300]))

_rc, _o = M(plant(P(1, t1=[FOUND1]), P(2), P(3, t2=[FOUND2]), P(4)))
ck("🔴🔴 findings in two parts, tier 1 and tier 2, are BOTH in the report",
   _rc == V.EXIT_VACUOUS and "test_found1.py" in _o and "test_found2.py" in _o,
   "⛔ a union that keeps one part drops the other part's guards. %s" % _o[:300])
ck("✅ ...and the count is the whole sweep's",
   "Tier 1 checked 4 name-mapped pair(s); tier 2 applied 4 declared" in _o,
   "%s" % _o[-500:])

_rc, _o = M(plant(P(1), P(2), P(4)))
ck("🔴🔴 THE HOLE: three clean parts and one missing is exit 2, NEVER 0",
   _rc == V.EXIT_UNREADABLE,
   "⛔ exit 0 closes the issue on a share nobody swept: a timed-out part "
   "would resolve the finding it was about to report. rc=%s" % _rc)
ck("🔴 ...and says which part", "part 3/4 never reported" in _o, "%s" % _o[:300])

_rc, _o = M(plant(P(1), P(2, t2=[FOUND2])))
ck("🔴🔴 a finding with parts missing is exit 3, and names what is missing",
   _rc == V.EXIT_PARTIAL and "test_found2.py" in _o
   and "part 3/4 never reported" in _o and "part 4/4 never reported" in _o,
   "⛔ FOUND IN REVIEW: this was 1, so the night read as a whole report. It "
   "overwrote the issue, dropping what the dead part held, and nothing went red. "
   "rc=%s %s" % (_rc, _o[:300]))

_d = plant(P(1, t2=[FOUND2]), P(2), P(3), P(4))
with open(os.path.join(_d, "vacuity-part-0", "stray.json"), "w", encoding="utf-8") as _fh:
    _fh.write("{not json")
_rc, _o = M(_d)
ck("🔴 ...and so is a finding beside a report nobody can read",
   _rc == V.EXIT_PARTIAL and "stray.json" in _o and "test_found2.py" in _o,
   "⛔ every gap counts, not only a missing part. rc=%s %s" % (_rc, _o[:300]))

_rc, _o = M(plant(P(1), P(2, leak_ok=False, dirty=" M card.py"), P(3), P(4)))
ck("🔴 a part that left a mutation behind makes the whole sweep exit 2",
   _rc == V.EXIT_UNREADABLE and "card.py" in _o,
   "⛔ an unverifiable restore is not a restore. rc=%s %s" % (_rc, _o[:200]))
_rc, _o = M(plant(P(1, t2=[FOUND2]), P(2, leak_ok=False, dirty=" M card.py"),
                  P(3), P(4)))
ck("🔴 ...and it outranks a finding in another part, as in verdict()",
   _rc == V.EXIT_UNREADABLE, "rc=%s" % _rc)
_rc, _o = M(plant(P(1, t2=[FOUND2]), P(2, leak_ok=False, dirty=" M card.py"), P(3)))
ck("🔴 ...and a missing part as well: every result is suspect, so no finding is written",
   _rc == V.EXIT_UNREADABLE, "rc=%s" % _rc)

_rc, _o = M(tree())
ck("🔴🔴 no reports at all is exit 2", _rc == V.EXIT_UNREADABLE, "rc=%s" % _rc)
ck("🔴 ...and says so", "no part reported" in _o, "%s" % _o[:200])
_rc, _o = M(os.path.join(tree(), "never-made"))
ck("🔴 ...and so is a folder nobody made (no artifact downloaded)",
   _rc == V.EXIT_UNREADABLE, "rc=%s" % _rc)
_rc, _o = M(plant(P(1, t1=[], t2=[]), P(2, t1=[], t2=[]), P(3, t1=[], t2=[]),
                  P(4, t1=[], t2=[])))
ck("🔴 four parts that checked nothing are not a pass", _rc == V.EXIT_UNREADABLE,
   "rc=%s" % _rc)

_d = plant(P(1), P(2), P(3), P(4))
with open(os.path.join(_d, "vacuity-part-0", "stray.json"), "w", encoding="utf-8") as _fh:
    _fh.write("{not json")
_rc, _o = M(_d)
ck("⛔ a report that cannot be read is a gap, not a skip",
   _rc == V.EXIT_UNREADABLE and "stray.json" in _o,
   "⛔ a truncated upload must not read as a part with nothing to say. "
   "rc=%s %s" % (_rc, _o[:200]))
for _i, _bad in enumerate(({"t1": [], "t2": [], "leak_ok": True, "dirty": ""},
                           {"part": "1/4", "t1": "x", "t2": [], "leak_ok": True, "dirty": ""},
                           {"part": "1/4", "t1": [{"test": "t"}], "t2": [],
                            "leak_ok": True, "dirty": ""},
                           {"part": "9/4", "t1": [], "t2": [], "leak_ok": True, "dirty": ""},
                           ["a", "list"])):
    _d = plant(P(1), P(2), P(3), P(4))
    with open(os.path.join(_d, "bad%d.json" % _i), "w", encoding="utf-8") as _fh:
        json.dump(_bad, _fh)
    _rc, _o = M(_d)
    ck("⛔ ...malformed report %d of 5 too" % (_i + 1),
       _rc == V.EXIT_UNREADABLE and ("bad%d.json" % _i) in _o,
       "⛔ it must never crash (a crash used to be exit 1, a finding) or vanish. "
       "rc=%s %s" % (_rc, _o[:200]))

_rc, _o = M(plant(P(1, 2), P(2, 3), P(3, 3)))
ck("⛔ parts that disagree on how many there are are not one sweep",
   _rc == V.EXIT_UNREADABLE and "disagree" in _o,
   "⛔ 1/2, 2/3 and 3/3 name no missing part and repeat none, and they are no "
   "partition of anything. rc=%s %s" % (_rc, _o[:200]))
_rc, _o = M(plant(P(1, 2), P(1, 2), P(2, 2)))
ck("⛔ one part reported twice is not two parts",
   _rc == V.EXIT_UNREADABLE and "part 1 reported 2 times" in _o,
   "rc=%s %s" % (_rc, _o[:200]))


# ════════════════════════════════════════════════════════════════════════
section("2. 🔴 main() WRITES WHAT merge() READS, AND UNSET STAYS THE OLD main()")
# ════════════════════════════════════════════════════════════════════════
def run_main(env, t1=(PAIR,), t2=(FOUND2,), leak=None):
    """`main()` with its tiers stubbed. ⛔ This file's own env is put back.

    pr-tests runs this file with VACUITY_PART set for the sweep jobs, so the
    variables are always cleared first.
    """
    keep = (V._porcelain, V.tier1, V.tier2, V.leaked)
    saved = {k: os.environ.pop(k, None) for k in ENV}
    try:
        os.environ.update(env)
        V._porcelain = lambda *a, **k: set()
        V.leaked = lambda *a, **k: leak or (True, "")
        V.tier1 = lambda *a, **k: list(t1)
        V.tier2 = lambda *a, **k: list(t2)
        o = io.StringIO()
        with contextlib.redirect_stdout(o), contextlib.redirect_stderr(o):
            rc = V.main()
    finally:
        V._porcelain, V.tier1, V.tier2, V.leaked = keep
        for k in ENV:
            os.environ.pop(k, None)
            if saved[k] is not None:
                os.environ[k] = saved[k]
    return rc


_d = tree()
_out = os.path.join(_d, "deep", "er", "vacuity-part.json")
_rc = run_main({"VACUITY_PART": "2/4", "VACUITY_OUT": _out})
ck("🔴🔴 a part leaves its report, making the folder if it must",
   os.path.exists(_out), "⛔ no report means this part reads as missing every night")
ck("✅ ...and still exits by verdict()", _rc == V.EXIT_VACUOUS, "rc=%s" % _rc)
_rep, _gaps = V.read_parts(_d)
ck("🔴 ...and merge reads it back as that part, rows and all",
   len(_rep) == 1 and _rep[0]["part"] == (2, 4) and _rep[0]["t1"] == [PAIR]
   and _rep[0]["t2"] == [FOUND2] and _rep[0]["leak_ok"] is True,
   "got %r" % _rep)
ck("🔴 ...with the other three parts named as missing",
   _gaps == ["part %d/4 never reported" % k for k in (1, 3, 4)], "got %r" % _gaps)

_d = tree()
_out = os.path.join(_d, "vacuity-part.json")
run_main({"VACUITY_PART": "1/4", "VACUITY_OUT": _out}, leak=(False, " M card.py"))
_r = json.load(open(_out, encoding="utf-8"))
ck("🔴 a leak travels in the report", _r["leak_ok"] is False and "card.py" in _r["dirty"],
   "got %r" % _r)

_d = tree()
_rc = run_main({})
ck("🔴 UNSET, nothing is written: the deployed nightly until Sam's upload",
   _rc == V.EXIT_VACUOUS and not os.listdir(_d), "rc=%s %r" % (_rc, os.listdir(_d)))
_d = tree()
_out = os.path.join(_d, "whole.json")
run_main({"VACUITY_OUT": _out})
ck("✅ a whole sweep with a report is part 1/1 and needs no other",
   not V.read_parts(_d)[1] and V.read_parts(_d)[0][0]["part"] == (1, 1),
   "got %r" % (V.read_parts(_d),))

# ⛔ A test the sweep runs must not inherit its report path: two test files
#    drive main() with its tiers stubbed.
_d = tree()
with open(os.path.join(_d, "test_env.py"), "w", encoding="utf-8") as _fh:
    _fh.write("import os, sys\nsys.exit(1 if os.environ.get('VACUITY_OUT') "
              "or os.environ.get('VACUITY_PART') else 0)\n")
_saved = {k: os.environ.pop(k, None) for k in ENV}
try:
    os.environ.update({"VACUITY_OUT": "x", "VACUITY_PART": "1/4"})
    _rc = V.run_test("test_env.py", _d)
finally:
    for _k in ENV:
        os.environ.pop(_k, None)
        if _saved[_k] is not None:
            os.environ[_k] = _saved[_k]
ck("⛔ a test the sweep runs never sees the sweep's part or report path",
   _rc == 0, "⛔ a stubbed main() in a child would overwrite the real report. rc=%s" % _rc)

# ════════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 THE REAL PROGRAM ON A PLANTED REPO: THE PARTS ADD UP TO THE WHOLE")
# ════════════════════════════════════════════════════════════════════════
# ⛔ The file under test, run as the workflow runs it. It works on the folder
#    it sits in, so a copy here can touch nothing in this repo.
_r = tree()


def _w(name, text):
    with open(os.path.join(_r, name), "w", encoding="utf-8") as fh:
        fh.write(text)


_DECL = "# @vacuity %s\n#   file: pretend.py\n#   find: return 42\n#   with: return 43\n"
_DEP = "import sys, pretend\nsys.exit(0 if pretend.answer() == 42 else 1)\n"
_w("pretend.py", "def answer():\n    return 42\n")
_w("test_pretend.py", _DEP)
_w("test_a_bites.py", _DECL % "bites" + _DEP)
_w("test_b_vacuous.py", _DECL % "vacuous" + "import sys\nsys.exit(0)\n")
shutil.copy(os.path.join(ROOT, "vacuity.py"), _r)
for _a in (["init", "-q"], ["add", "-A"],
           ["-c", "user.name=vmerge", "-c", "user.email=vmerge@example.invalid",
            "commit", "-q", "-m", "plant"]):
    subprocess.run(["git"] + _a, cwd=_r, capture_output=True, timeout=120, check=True)


def prog(*args, **env):
    """`python vacuity.py ARGS` in the planted repo. -> (rc, stdout, stderr)."""
    e = {k: v for k, v in os.environ.items() if k not in ENV}
    e.update(env, PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, "-B", "vacuity.py"] + list(args), cwd=_r,
                       env=e, capture_output=True, encoding="utf-8", timeout=300)
    return p.returncode, p.stdout, p.stderr


_rcw, _ow, _ew = prog()
ck("⚠️ the whole sweep ran and found the planted guard (exit 1)",
   _rcw == V.EXIT_VACUOUS and "test_b_vacuous.py" in _ow,
   "⛔ every comparison below is against this run (rule 67). rc=%s %s %s"
   % (_rcw, shown(_ow[:300]), shown(_ew[-300:])))
_parts = tree()
_o1, _o2 = (os.path.join(_parts, "vacuity-part-%d" % k, "vacuity-part.json") for k in (1, 2))
_rc1 = prog(VACUITY_PART="1/2", VACUITY_OUT=_o1)
_rc2 = prog(VACUITY_PART="2/2", VACUITY_OUT=_o2)
_s1, _s2 = (json.load(open(p, encoding="utf-8")) for p in (_o1, _o2))
ck("🔴 each part swept its own share: tier 1's pair and one declaration, or the other",
   [r["test"] for r in _s1["t1"] + _s1["t2"]] == ["test_pretend.py", "test_a_bites.py"]
   and [r["test"] for r in _s2["t1"] + _s2["t2"]] == ["test_b_vacuous.py"],
   "⛔ got %r / %r" % (_s1, _s2))
_rcm, _om, _em = prog("--merge", _parts)
ck("🔴🔴 merged, the two parts say what the whole sweep said",
   _rcm == _rcw and "test_b_vacuous.py" in _om,
   "⛔ rc %s vs whole %s. %s" % (_rcm, _rcw, shown(_om[:300])))
ck("🔴 ...with the whole sweep's counts",
   "Tier 1 checked 1 name-mapped pair(s); tier 2 applied 2 declared" in _om
   and "Tier 1 checked 1 name-mapped pair(s); tier 2 applied 2 declared" in _ow,
   "%s" % shown(_om[-500:]))

os.rename(_o2, _o2 + ".gone")
_rcm, _om, _em = prog("--merge", _parts)
ck("🔴🔴 THE NIGHT THE PROBLEM PART DIES: a clean part alone is exit 2, not 0",
   _rcm == V.EXIT_UNREADABLE and "part 2/2 never reported" in _om,
   "⛔ exit 0 would close an open issue about a guard nobody re-checked. "
   "rc=%s %s" % (_rcm, shown(_om[:300])))
os.rename(_o2 + ".gone", _o2)
os.remove(_o1)
_rcm, _om, _em = prog("--merge", _parts)
ck("🔴 ...and the night a CLEAN part dies, the finding still gets out, as a short report",
   _rcm == V.EXIT_PARTIAL and "test_b_vacuous.py" in _om and "part 1/2 never reported" in _om,
   "rc=%s %s" % (_rcm, shown(_om[:300])))

_rcx, _ox, _ex = prog(VACUITY_PART="bogus")
ck("🔴🔴 A CRASH IS EXIT 2: an uncaught exception would exit 1, and 1 is a finding",
   _rcx == V.EXIT_UNREADABLE and "ValueError" in _ex,
   "⛔ `vacuity.yml` would read it as `bad` and write the empty report over the "
   "issue: the wipe again, by another door. rc=%s %s" % (_rcx, shown(_ex[-300:])))
ck("🔴 ...and --merge with nowhere to look is exit 2", prog("--merge")[0] == V.EXIT_UNREADABLE,
   "rc=%s" % prog("--merge")[0])

# ════════════════════════════════════════════════════════════════════════
section("4. 🔴🔴 THE WORKFLOW AS IT WILL BE LIVE (the staged copy, while one waits)")
# ════════════════════════════════════════════════════════════════════════
WF = W.effective_workflows(ROOT)["vacuity.yml"]
LINES = W.read(WF).splitlines()
JOBS = {j.name: j for j in W.jobs(WF)}


def job_text(name):
    j = JOBS.get(name)
    return "\n".join(LINES[j.start:j.end]) if j else ""


ck("🔴 `sweep` comes first, and `watch` is the only other job",
   list(JOBS) == ["sweep", "watch"],
   "⛔ test_vacuity_pool.py reads the file's first clock as the nightly's. got %r" % list(JOBS))
_wt, _st = job_text("watch"), job_text("sweep")
ck("🔴🔴 the report job runs whatever happened to the parts: `if: always()`",
   re.search(r"(?m)^    if: always\(\)(\s+#.*)?$", _wt),
   "⛔ FOUND IN REVIEW. Without it a part that ran out its clock SKIPS the "
   "report, and a skipped report job is a quiet one")
ck("🔴 ...and it waits for them", re.search(r"(?m)^    needs: sweep\s*$", _wt),
   "⛔ a report that runs beside the sweep finds nothing to merge")
ck("🔴 one part failing does not cancel the others",
   re.search(r"(?m)^      fail-fast: false\s*$", _st),
   "⛔ matrix jobs fail fast by default: one red part would throw away three reports")
ck("🔴 only the report job can write to an issue",
   "issues" not in JOBS["sweep"].permissions and JOBS["watch"].permissions.get("issues") == "write",
   "⛔ one issue, one writer. got %r / %r" % (JOBS["sweep"].permissions, JOBS["watch"].permissions))
_ss, _ws = W.steps(WF, "sweep"), W.steps(WF, "watch")
_swp = next((s for s in _ss if s.run and "python vacuity.py" in s.run), None)
_look = next((s for s in _ws if s.run and "--merge" in s.run), None)
ck("⚠️ the two steps were found", _swp is not None and _look is not None,
   "⛔ every drive below needs them (rule 67)")
ck("🔴 the issue is written only after the merge, in the report job",
   _look is not None and any("gh issue edit" in (s.run or "") for s in _ws[_ws.index(_look):])
   and not any("gh issue" in (s.run or "") for s in _ss),
   "⛔ a part that files for itself is the wipe with four writers")
LAST = "A run that could not look is red"
ck("🔴 the red step is the job's LAST, and `if: always()`",
   _ws[-1].name == LAST and _ws[-1].cond == "always()",
   "⛔ after Tell Sam, and it must run when an earlier step did not finish. "
   "got %r %r" % (_ws[-1].name, _ws[-1].cond))


def _with_of(step):
    """{key: value} under a step's `with:`, read off its own lines."""
    out = {}
    for ln in LINES[step.start:step.end]:
        m = re.match(r"^\s+([a-z-]+): (.+?)\s*$", ln)
        if m and not ln.lstrip().startswith(("#", "-")):
            out[m.group(1)] = m.group(2)
    return out


_up = next((s for s in _ss if "upload-artifact@" in LINES[s.start]), None)
_dn = next((s for s in _ws if "download-artifact@" in LINES[s.start]), None)
ck("⚠️ the upload and download steps were found", _up is not None and _dn is not None,
   "⛔ rule 67")
_uw, _dw = _with_of(_up), _with_of(_dn)
_senv = W.step_env(WF, step_name=_swp.name) or {}
_lenv = W.step_env(WF, step_name=_look.name) or {}
ck("🔴 the report is uploaded from where the sweep wrote it, whatever the sweep did",
   _uw.get("path") == _senv.get("VACUITY_OUT") and _up.cond == "always()",
   "⛔ got %r / %r / %r" % (_uw.get("path"), _senv.get("VACUITY_OUT"), _up.cond))
ck("🔴 ...and the sweep writes it outside the checkout",
   (_senv.get("VACUITY_OUT") or "").startswith("${{ runner.temp }}/"),
   "⛔ inside, it would read as a leftover mutation. got %r" % _senv.get("VACUITY_OUT"))
ck("🔴 the report job downloads every part, to the folder it merges",
   fnmatch.fnmatch(_uw.get("name", ""), _dw.get("pattern") or "-")
   and _dw.get("path") == _lenv.get("PARTS"),
   "⛔ got %r / %r / %r" % (_uw.get("name"), _dw, _lenv.get("PARTS")))

SHIMS = {"python": '#!/bin/sh\necho "$@" >> "$ARGS_LOG"\n'
                   'if [ -n "$VACUITY_OUT" ]; then echo x > "$VACUITY_OUT"; fi\n'
                   'exit "${FAKE_RC:-0}"\n',
         "git": '#!/bin/sh\nif [ -n "$FAKE_DIRTY" ]; then echo " M card.py"; fi\nexit 0\n',
         "gh": '#!/bin/sh\necho "$@" >> "$GH_LOG"\n'
               'if [ "$1 $2" = "issue list" ]; then echo "$FAKE_NUM"; fi\nexit 0\n'}


def run_step(body, state="", report=None, **env):
    """Run a step's real shell. -> (rc, output, GITHUB_OUTPUT, args, folder, gh log).

    ⚠️ Its fixed /tmp paths are pointed at a folder of this run's own, and the
    expression GitHub would expand is expanded; the rest is the step, byte for
    byte. Under the shell GitHub uses. `report` is what the look step left.
    """
    d = tree()
    b = os.path.join(d, "bin")
    os.makedirs(b)
    for exe, text in SHIMS.items():
        with open(os.path.join(b, exe), "w", newline="\n") as fh:
            fh.write(text)
        os.chmod(os.path.join(b, exe), 0o755)
    src = re.sub(r"\$\{\{\s*steps\.look\.outputs\.state\s*\}\}", state, body)
    src = src.replace("/tmp/vacuity", d.replace("\\", "/") + "/vacuity")
    script = os.path.join(d, "step.sh")
    with open(script, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    if report is not None:
        with open(os.path.join(d, "vacuity.md"), "w", encoding="utf-8") as fh:
            fh.write(report)
    log, out, gh = (os.path.join(d, f) for f in ("args.log", "out", "gh.log"))
    e = dict({k: v for k, v in os.environ.items() if k not in ENV},
             PATH=b + os.pathsep + os.environ["PATH"], ARGS_LOG=log, GITHUB_OUTPUT=out,
             GH_LOG=gh, **env)
    p = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", script],
                       cwd=d, env=e, capture_output=True, encoding="utf-8", timeout=60)

    def _read(path):
        return open(path, encoding="utf-8").read() if os.path.exists(path) else ""

    return p.returncode, p.stdout + p.stderr, _read(out), _read(log), d, _read(gh)


if _look is not None:
    _want = {0: "state=ok", 1: "state=bad", 2: "state=unknown", 3: "state=partial",
             4: "state=unknown"}
    _got = {rc: run_step(_look.run, FAKE_RC=str(rc), PARTS="the-parts")[2].strip() for rc in _want}
    ck("🔴🔴 the report job reads merge's exit: 0 ok, 1 bad, 3 partial, anything else unknown",
       _got == _want,
       "⛔ 2 read as `bad` is the wipe again: an empty report over the issue. got %r" % _got)
    _args = run_step(_look.run, PARTS="the-parts")[3].split()
    ck("🔴 ...and what it runs is the merge of that folder",
       _args == ["vacuity.py", "--merge", "the-parts"], "got %r" % _args)

_lastrun = W.step_run(WF, step_name=LAST)
ck("⚠️ the last step was read", bool(_lastrun), "⛔ rule 67")
if _lastrun:
    _red = {st: run_step(_lastrun, state=st)[0]
            for st in ("ok", "bad", "partial", "unknown", "", "nonsense")}
    ck("🔴🔴 unknown turns the run red", _red["unknown"] != 0, "got %r" % _red)
    ck("🔴🔴 ...and so does an EMPTY state: the merge step never finished",
       _red[""] != 0,
       "⛔ FOUND IN REVIEW. An empty state is the case that started this. got %r" % _red)
    ck("🔴 ...and so does anything else it does not know", _red["nonsense"] != 0,
       "got %r" % _red)
    ck("🔴🔴 ...and so does a finding with a part missing",
       _red["partial"] != 0,
       "⛔ FOUND IN REVIEW. With any finding in a surviving part the run stayed "
       "green, so a dead part was seen by nobody. got %r" % _red)
    ck("✅ ok and bad stay green: a finding is reported, not a failed run",
       _red["ok"] == 0 and _red["bad"] == 0,
       "⛔ a red run on every finding would be a red run nobody reads. got %r" % _red)

# ⛔ THE NIGHT A PART DIES WITH A FINDING ELSEWHERE. The issue may hold what that
#    part found, so a short report is added beside it; a whole one replaces it.
_tell = next((s for s in _ws if s.run and "gh issue edit" in s.run), None)
ck("⚠️ the issue step was found", _tell is not None, "⛔ rule 67")
if _tell is not None:
    _short = "part 2/4 never reported\n"
    _o77 = run_step(_tell.run, state="partial", report=_short, FAKE_NUM="77")[5]
    ck("🔴🔴 a short report is ADDED to the open issue, never written over it",
       "issue comment 77 --body-file" in _o77 and "issue edit" not in _o77
       and "issue close" not in _o77,
       "⛔ FOUND IN REVIEW. `gh issue edit` here dropped what the dead part held. "
       "got %r" % _o77)
    _o0 = run_step(_tell.run, state="partial", report=_short, FAKE_NUM="")[5]
    ck("🔴 ...and with no issue open, the finding still opens one",
       "issue create" in _o0, "got %r" % _o0)
    _oall = run_step(_tell.run, state="bad", report="the whole report\n", FAKE_NUM="77")[5]
    ck("✅ a whole report still replaces the body",
       "issue edit 77" in _oall and "issue comment" not in _oall, "got %r" % _oall)

if _swp is not None:
    _clean = run_step(_swp.run, VACUITY_OUT="report.json", FAKE_RC="1")
    _dirty = run_step(_swp.run, VACUITY_OUT="report.json", FAKE_DIRTY="1")
    ck("🔴 a part leaves its report when the tree is clean, whatever it found",
       _clean[0] == 0 and os.path.exists(os.path.join(_clean[4], "report.json")),
       "⛔ exit 1 is a finding, and `watch` needs to read it. rc=%s" % _clean[0])
    ck("🔴 ...and no report when it left a mutation behind: that part reads as missing",
       _dirty[0] == 0 and not os.path.exists(os.path.join(_dirty[4], "report.json")),
       "⛔ the second pair of eyes. rc=%s" % _dirty[0])

_same = open(WF, encoding="utf-8").read().replace("\r", "") == open(
    os.path.join(ROOT, W.DEPLOYED_DIR, "vacuity.yml"), encoding="utf-8").read().replace("\r", "")
note("vacuity.yml: %s" % ("deployed copy read (no upload waiting)" if _same
                          else "staged copy read; waiting for Sam's upload"))

for _d in _trees:
    shutil.rmtree(_d, ignore_errors=True)
