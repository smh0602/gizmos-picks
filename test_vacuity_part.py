#!/usr/bin/env python3
"""🔴🔴 A SWEEP PART GOES RED WHEN A DECLARATION IN ITS SHARE DOES NOT BITE.

`[measured 2026-09-28, git log -S'_real2' -- test_vacuity.py]` Every
pr-tests `sweep k/4` job, and collect.yml's unsplit run, ran the real
declared-mutation sweep in `test_vacuity.py` and never failed on what it
found. It asserted the share, the leak and the two CFBD mutations. A PR
adding a VACUOUS declaration passed all four parts, and only the nightly
`vacuity.yml` (issue #188) noticed, a day later.

✅ `test_vacuity.py` section 2b now fails on its own share, through
`vacuity.part_gate`, which is `vacuity.verdict()`: the nightly's own exit
code, so the two cannot disagree about which state is bad. This file
proves that gate bites:
  1. `part_gate` itself: VACUOUS, RED_BOTH_WAYS, MALFORMED and TIMEOUT
     each fail a share and are named; a clean share passes; a leak or an
     empty sweep never passes.
  2. THE REAL `test_vacuity.py`, run on a planted tree split in two parts.
     The part holding a vacuous declaration fails exactly one check more
     than the part without one, and that check is the gate, naming it.

⛔ `test_vacuity.py` cannot declare a mutation on itself (its header says
why). This file can, including on `test_vacuity.py`'s gate line: it runs a
planted sweep of three declarations, never the real one.

# @vacuity 🔴🔴 the part's verdict comes from verdict(), not assumed
#   file: vacuity.py
#   find:     if verdict(results, leak_ok) == EXIT_OK:
#   with:     if True:
#
# @vacuity 🔴🔴 test_vacuity.py fails on its gate, not only computes it
#   file: test_vacuity.py
#   find: ck(V.PART_GATE + " (%s)" % _LABEL, _gate_ok, _gate_why)
#   with: ck(V.PART_GATE + " (%s)" % _LABEL, True, _gate_why)
#
# @vacuity 🔴 a dropped bad state is caught (the 2026-09-15 defect)
#   file: vacuity.py
#   find: BAD = ("VACUOUS", "RED_BOTH_WAYS", "MALFORMED")
#   with: BAD = ("VACUOUS", "MALFORMED")
#
# @vacuity 🔴 a TIMEOUT does not pass
#   file: vacuity.py
#   find:     if any(r["state"] == "TIMEOUT" for r in results):
#   with:     if False:
#
# @vacuity 🔴 each offender is named, not only counted
#   file: vacuity.py
#   find:     return [r for r in results if verdict([r], True) != EXIT_OK]
#   with:     return []
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, copy_module, note, section, shown

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import vacuity as V  # noqa: E402

# ⛔ Spelled out, never read from `V.BAD`: a state dropped from that tuple
#    would drop out of this list too, and the check would pass on exactly
#    the defect it is here for.
STATES = ("VACUOUS", "RED_BOTH_WAYS", "MALFORMED", "TIMEOUT")


def _r(state, test="test_ok.py", line=7):
    return {"tier": 2, "test": test, "line": line, "state": state,
            "why": "why-%s" % state}


def brief(why):
    """The report without its closing advice, for a check's detail."""
    return shown("\n".join(ln for ln in why.splitlines()
                           if not ln.startswith("⛔")))


# ════════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 part_gate: EVERY BAD STATE FAILS THE SHARE, AND IS NAMED")
# ════════════════════════════════════════════════════════════════════════
_ok, _why = V.part_gate([_r("BITES"), _r("BITES", "test_ok2.py")], True)
ck("✅ a share where every declaration bites passes", _ok,
   "⛔ the other failure: a gate that is always red is one nobody reads. "
   "%s" % brief(_why))
for _s in STATES:
    _ok, _why = V.part_gate([_r("BITES"), _r(_s, "test_bad.py", 31)], True)
    ck("🔴🔴 a share holding one %s declaration FAILS" % _s, not _ok,
       "⛔ this is the defect: the part swept it and stayed green. %s"
       % brief(_why))
    ck("   ...and the report names it: state, test:line and why",
       _s in _why and "test_bad.py:31" in _why and "why-" + _s in _why,
       "⛔ a red part that does not say which declaration sends the reader "
       "through 100 of them. got %s" % brief(_why))
    ck("   ...and does not accuse the one that bites",
       "test_ok.py:7" not in _why,
       "got %s" % brief(_why))
_ok, _why = V.part_gate([_r("BITES")], False)
ck("⛔ a share that left changes behind never passes", not _ok,
   "🔴 the harness rewrites source files; an unverifiable restore is not a "
   "restore. %s" % brief(_why))
_ok, _why = V.part_gate([], True)
ck("⛔ a share that swept NOTHING never passes", not _ok,
   "🔴 \"I could not look\" is not a pass. %s" % brief(_why))
_mix = [_r("BITES"), _r("TIMEOUT", "test_t.py", 3), _r("VACUOUS", "test_v.py", 4)]
ck("⚠️ the gate is verdict()'s number, not a second classification",
   all(V.part_gate(rs, lk)[0] == (V.verdict(rs, lk) == V.EXIT_OK)
       for rs in ([_r("BITES")], _mix, _mix[:2], []) for lk in (True, False)),
   "⛔ two classifications drift; the nightly and the PR would then "
   "disagree about the same declaration")
_ok, _why = V.part_gate(_mix, True)
ck("🔴 ...and every offender in a mixed share is listed, in sweep order",
   not _ok and 0 <= _why.find("test_t.py:3") < _why.find("test_v.py:4"),
   "got %s" % brief(_why))


# ════════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 THE REAL test_vacuity.py, ON A PLANTED TREE IN TWO PARTS")
# ════════════════════════════════════════════════════════════════════════
# ⚠️ The planted tree is not this repo, so the real file also fails checks
#    that ask about the real repo (at least 20 declarations, the four
#    unmapped files by name, the CFBD mutations). Its exit code alone
#    therefore says nothing. ✅ What is read is the DIFFERENCE between the
#    two parts' failures: it must be exactly the gate, in the part that
#    holds the vacuous declaration.
DECL = "# @vacuity %s\n#   file: subject.py\n#   find: X = 1\n#   with: X = 2\n"
BITES = "import sys, subject\nsys.exit(0 if subject.X == 1 else 1)\n"


def git(d, *a):
    return subprocess.run(["git", "-c", "user.name=vpart",
                           "-c", "user.email=vpart@example.invalid", *a],
                          cwd=d, capture_output=True, text=True, timeout=120)


def plant():
    """A committed tree: the real sweep files, and three declarations.

    Declaration order is file order, so with two parts, part 1 sweeps
    test_p0 and test_p2 (both bite) and part 2 sweeps test_p1 (vacuous).
    """
    d = tempfile.mkdtemp(prefix="vpart-")
    got = copy_module("test_vacuity.py", d, ROOT)
    wf = os.path.join(d, ".github", "workflows")
    os.makedirs(wf)
    shutil.copy(os.path.join(ROOT, ".github", "workflows", "pr-tests.yml"), wf)
    w = lambda n, s: open(os.path.join(d, n), "w", encoding="utf-8").write(s)
    w("subject.py", "X = 1\n")
    w("test_p0_bites.py", DECL % "bites" + BITES)
    w("test_p1_vacuous.py", DECL % "claims to check X, and does not"
      + "import sys\nsys.exit(0)\n")
    w("test_p2_bites.py", DECL % "bites" + BITES)
    git(d, "init", "-q")
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "plant")
    return d, got


def run(d, part):
    """Run the planted tree's test_vacuity.py as one sweep part.

    -> (returncode or None, output). ⚠️ Its own TMPDIR, so its orphan reaper
    and its worktrees never touch anything outside this run; and no
    TCHECK_FAIL_FAST, so a red run of THIS file still gets the whole child.
    """
    tmp = tempfile.mkdtemp(prefix="vpart-tmp-")
    env = dict(os.environ, VACUITY_PART=part, PYTHONDONTWRITEBYTECODE="1",
               PYTHONIOENCODING="utf-8", TMPDIR=tmp, TEMP=tmp, TMP=tmp)
    env.pop("TCHECK_FAIL_FAST", None)
    try:
        p = subprocess.run([sys.executable, "-B", "test_vacuity.py"], cwd=d,
                           env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return None, "test_vacuity.py never answered in 600s"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def gate(out):
    """-> (mark, block) for the gate's own check line: mark is ✅, ❌ or None."""
    lines = out.splitlines()
    at = [i for i, ln in enumerate(lines)
          if V.PART_GATE in ln and ln.lstrip()[:1] in ("✅", "❌")]
    if len(at) != 1:
        return None, "the gate's check line appears %d time(s)" % len(at)
    i = at[0]
    j = i + 1
    while j < len(lines) and lines[j].strip() \
            and lines[j].lstrip()[:1] not in ("✅", "❌", "⚪", "═"):
        j += 1
    return lines[i].lstrip()[:1], "\n".join(lines[i:j])


def failed(out):
    """The names tcheck lists as FAILED, without their part label."""
    m = re.search(r"checks FAILED\n((?:   - .*\n?)+)", out)
    names = re.findall(r"^   - (.*)$", m.group(1), re.M) if m else []
    return {re.sub(r" \((?:all|part \d+ of \d+)\)$", "", n) for n in names}


_d, _got = plant()
try:
    ck("⚠️ the planted tree holds the real sweep files",
       {"test_vacuity.py", "vacuity.py", "tcheck.py"} <= set(_got)
       and V._porcelain(_d) == set(),
       "⛔ without them nothing below runs the real file (rule 67). "
       "copied %s, porcelain %r" % (_got, V._porcelain(_d)))
    ck("⚠️ ...and its two parts split the three declarations as planned",
       [x["test"] for x in V.part_of(V.declarations(_d), (1, 2))]
       == ["test_p0_bites.py", "test_p2_bites.py"]
       and [x["test"] for x in V.part_of(V.declarations(_d), (2, 2))]
       == ["test_p1_vacuous.py"],
       "⛔ if the vacuous one landed in both or neither part, the comparison "
       "below compares nothing. got %s"
       % [(x["test"], x["line"]) for x in V.declarations(_d)])

    # ⚠️ The part holding the vacuous one runs FIRST: under a mutation of
    #    the gate this file fails on it and stops (TCHECK_FAIL_FAST).
    _rc2, _out2 = run(_d, "2/2")
    _m2, _blk2 = gate(_out2)
    ck("🔴🔴 the part holding a VACUOUS declaration FAILS the gate",
       _m2 == "❌",
       "⛔ THIS IS THE DEFECT: the part swept it and said nothing. mark=%s "
       "%s" % (_m2, brief(_blk2) if _m2 else shown(_out2[-600:])))
    ck("   ...after sweeping its share of 1, and names it",
       re.search(r"\b1 of 1 declaration", _blk2)
       and "test_p1_vacuous.py" in _blk2 and "VACUOUS" in _blk2,
       "⛔ a red part that does not say which declaration is a hunt. %s"
       % brief(_blk2))
    ck("   ...and the file goes red", _rc2 not in (0, None),
       "rc=%s" % _rc2)

    _rc1, _out1 = run(_d, "1/2")
    _m1, _blk1 = gate(_out1)
    ck("✅ the part WITHOUT one passes the gate, having swept its 2",
       _m1 == "✅" and re.search(r"\ball 2 declaration", _blk1),
       "⛔ a gate that fails every part is a gate nobody reads; and one "
       "that swept nothing proves nothing. mark=%s %s"
       % (_m1, brief(_blk1) if _m1 else shown(_out1[-600:])))
    _f1, _f2 = failed(_out1), failed(_out2)
    ck("🔴🔴 the two parts' failures differ by EXACTLY the gate",
       _f2 - _f1 == {V.PART_GATE} and not (_f1 - _f2),
       "⛔ the planted tree fails real-repo checks in both parts; only this "
       "difference is the vacuous declaration's doing. only part 2: %s; "
       "only part 1: %s" % (sorted(_f2 - _f1), sorted(_f1 - _f2)))
    note("both parts also fail %d check(s) that ask about the real repo, "
         "not about this plant: %s"
         % (len(_f1 & _f2), "; ".join(sorted(x[:60] for x in _f1 & _f2))))
finally:
    shutil.rmtree(_d, ignore_errors=True)
