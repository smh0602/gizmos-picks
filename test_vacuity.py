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
# 🔴🔴 THIS FILE DECLARES NO `@vacuity` MUTATION, AND THAT IS A FINDING
# RATHER THAN AN OVERSIGHT. `[2026-09-17]` One was written here —
#
#     file: vacuity.py
#     find: return sorted(set(tests(root)) - declared - mapped)
#     with: return []
#
# — and driving it is what exposed why it cannot exist. ⛔ **THIS FILE
# RUNS THE REAL SWEEP.** `V.tier2(ROOT)` below is the whole nightly pass.
# So a declaration naming THIS file as its `test` makes the sweep run
# `test_vacuity.py` as a subprocess, which runs the sweep again, which
# runs `test_vacuity.py` again — **unbounded recursion, every level
# rewriting the same real source files at the same time.**
# 🔴 MEASURED CONSEQUENCE: the outer run finished while a nested one was
# still mutating, its own leak check failed with `nfl.py` left modified,
# and earlier in the evening the same interleaving baked a mutation
# permanently into `vacuity.py` — TWICE.
#
# ⚠️ SO IT IS THE SECOND THING IN THIS REPO NO DECLARED MUTATION CAN
# TEST, for the same family of reason as `tcheck.py`'s `os._exit(1)`
# (recorded in `test_harness.py`): a guard cannot be proven by breaking
# the machinery that would report the break.
# ✅ WHAT COVERS IT INSTEAD: section 6 takes its measurement AT IMPORT,
# before anything mutates the tree, and asserts the set is non-empty —
# so a `blind()` that returns nothing fails here on the next ordinary
# suite run. That is exactly how the corruption was caught, twice.
# ══════════════════════════════════════════════════════════════════════

import atexit
import collections
import glob
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from tcheck import ck, note, section

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vacuity as V  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════════════════
# 🔴 MEASURED HERE, AT IMPORT, BEFORE ANYTHING MUTATES THE TREE.
# ⛔ This file runs the REAL tier-2 sweep further down, which rewrites
# source files in place — including `vacuity.py` itself, which is where
# `blind()` lives. Reading the blind set AFTER that is reading it through
# whatever the sweep is holding at that instant. `[2026-09-17]` It read
# 0 of 81 that way and the ratchet below passed on an empty set.
# ⚠️ A measurement taken while the thing measured is being edited is not
# a measurement.
# ══════════════════════════════════════════════════════════════════════
_BLIND_AT_IMPORT = V.blind(ROOT)
_TESTS_AT_IMPORT = V.tests(ROOT)


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

section("0b. 🔴🔴 EVERY REAL DECLARATION'S `find` STILL MATCHES, EXACTLY ONCE")
# ═══════════════════════════════════════════════════════════════════════
# ⛔ A `find:` THAT MATCHES ZERO TIMES MUTATES NOTHING, AND THE FILE THEN
#    "PASSES" HAVING BEEN ASKED NOTHING. Rule 244. Two matches is the same
#    hole from the other side: the harness cannot say which line it gutted.
#
# 🔴 THE CLASS, NOT THE THREE INSTANCES. `[measured 2026-09-19]` three
#    declarations went stale in ONE night, each one broken by a correct fix
#    to the file it names — `--add-label` added to the line a `find` quoted,
#    a comment that repeated `issues: read` so the literal occurred twice,
#    and a trailing `\` written doubled inside a docstring. ⚠️ Not one of
#    them was a mistake in the declaration when it was WRITTEN. They rot
#    because they are a copy of somebody else's line, and rule 166 applies
#    to a quoted string exactly as it does to a number.
#
# ✅ WHY HERE AND WHY THIS EARLY. `V.tier2()` already reports MALFORMED
#    — that is what found these three — but only after the full sweep,
#    which measured **18m16s**. This asks the same question in
#    milliseconds, off the real tree, BEFORE the expensive pass, so a
#    rotted declaration is named in the first second of the run instead of
#    twenty minutes in. ⛔ It does not replace the sweep and it weakens
#    nothing: a `find` that matches once can still be VACUOUS, and only
#    the sweep can say so.
_DECLS = V.declarations(ROOT)
ck("⚠️ there are declarations to check at all",
   len(_DECLS) >= 20,
   "⛔ rule 67: this whole section is vacuous over an empty set. The "
   "parser returned %d declaration(s)." % len(_DECLS))
_ROT = []
for _d in _DECLS:
    _miss = [k for k in ("file", "find", "with") if not _d.get(k)]
    if _miss:
        _ROT.append((_d.get("test"), _d.get("file"), "missing " + ",".join(_miss)))
        continue
    try:
        _src = open(os.path.join(ROOT, _d["file"]),
                    encoding="utf-8").read()
    except OSError as _e:
        _ROT.append((_d["test"], _d["file"], "unreadable: %s" % _e))
        continue
    _n = _src.count(_d["find"])
    if _n != 1:
        _ROT.append((_d["test"], _d["file"],
                     "`find` occurs %d time(s): %r" % (_n, _d["find"][:70])))
ck("🔴🔴 NO DECLARED MUTATION HAS ROTTED AWAY FROM ITS SUBJECT",
   not _ROT,
   "⛔ each of these declares an edit that would change NOTHING, so the "
   "test it belongs to is proving nothing and saying so in green. Fix the "
   "`find:`, do not delete the declaration. %d of %d rotted:\n%s"
   % (len(_ROT), len(_DECLS),
      "\n".join("       %-28s %-34s %s" % r for r in _ROT)))
note("%d declaration(s) checked statically, %d rotted. \u26a0\ufe0f This says each\n"
     "`find` still RESOLVES, never that the mutation BITES \u2014 only the "
     "sweep below can say that." % (len(_DECLS), len(_ROT)))

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
# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 THE REAL SWEEP RUNS IN A THROWAWAY WORKTREE, NOT THE TREE THE
#      COLLECTOR IS ABOUT TO BUILD DATA FROM.
# ══════════════════════════════════════════════════════════════════════
# `[measured 2026-09-18]` `tier2` rewrites live source files and restores
# them in a `finally`. **SIGTERM DOES NOT RUN `finally`**, and
# `collect.yml`'s Tests step gives every file 600s while this sweep needs
# ~18 minutes — so the timeout fires on this file EVERY collect run.
#
# ⛔ A kill at 90s on `main` left `cfb.py` MODIFIED:
#       -    p = f"{OUT}/{COACHES_PROBE_FILE}"
#       +    p = f"{OUT}/coaches.json"
#    `cfb.py` is a COLLECTOR module, the Tests step is
#    `continue-on-error`, and every step after it builds data, commits it
#    and pushes. ⚠️ `git add data/ picks/` does not save this: it
#    correctly refuses the mutated `.py`, and THE WRONG DATA THAT `.py`
#    PRODUCES is exactly what the allowlist permits.
# ⚠️ And `leaked()` — the guard built for this — never runs, because the
#    process was killed before reaching it.
#
# ✅ A DETACHED WORKTREE SHARES THE OBJECT STORE, so this costs no
#    meaningful disk and no copy. It is a real git tree, so
#    `V._porcelain()` and `V.leaked()` work unchanged, and `data/` is
#    committed so the tests inside it have what they need.
# 🔴 THE QUESTION IS UNCHANGED: still real files, still the repo's own,
#    still under git. What changes is only that a kill can dirty a
#    throwaway tree instead of the collector's.
# ⚠️ VERIFIED, NOT ASSUMED: `git worktree add --detach` works on a
#    SHALLOW clone (`actions/checkout`'s default, which `collect.yml`
#    uses), driven against a real `--depth 1` clone with
#    `git status --porcelain` returning rc=0 inside the worktree.
_swept_root, _wt = None, None


def _drop_wt():
    """Release the throwaway worktree. ⛔ ONE IMPLEMENTATION, three callers.

    ⚠️ Best-effort by design: a leftover temp worktree is housekeeping, not
    a finding, and this must never be able to fail the run.
    """
    if not _wt:
        return
    subprocess.run(["git", "worktree", "remove", "--force", _wt],
                   cwd=ROOT, check=False, capture_output=True)
    shutil.rmtree(_wt, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 THE KILL IS THE NORMAL EXIT FOR THIS FILE, SO CLEANUP HANGS OFF
#      THE KILL — NOT OFF THE END OF THE SCRIPT.
# ══════════════════════════════════════════════════════════════════════
# ⛔ `[measured 2026-09-18, on a real SIGTERM of the merged code]` The
#    removal at the bottom of this file never ran, for exactly the reason
#    this whole file exists: **SIGTERM does not run it**, the same way it
#    does not run a `finally`. After the kill:
#
#        worktrees registered   2 (the main tree + one orphan)
#        directory              still there, 59 MB
#        after `git worktree prune`   still 2, still there
#
# 🔴 AND `prune` CANNOT COVER IT. It only drops registrations whose
#    directory is ALREADY GONE, and this one is not — so the self-healing
#    measure added for orphans does not reach the orphan the timeout
#    actually produces. Every collect run leaked one.
# ⚠️ THE CHAIN THAT CLOSES: orphans accumulate -> the disk fills ->
#    `tempfile.mkdtemp()` raises -> the sweep is refused (below). Every
#    link was observed in one evening. On CI each job is a fresh runner,
#    so this accumulates only in a persistent environment.
# ⛔ SIGKILL still cannot be caught, and that is fine: `timeout -k 15`
#    sends TERM first and only KILLs 15s later. `prune` stays as the cover
#    for the SIGKILL case and costs nothing.
atexit.register(_drop_wt)


def _on_term(_signum, _frame):
    # ⛔ `atexit` DOES NOT RUN ON SIGTERM EITHER, so registering it is not
    #    enough on its own. 143 is 128 + SIGTERM, what the shell reports
    #    for an uncaught one — so the exit code is unchanged.
    _drop_wt()
    os._exit(143)


signal.signal(signal.SIGTERM, _on_term)

def _reap_orphans():
    """Release sweep worktrees whose owning process is GONE.

    ⛔ `git worktree prune` DOES NOT COVER THE SIGKILL CASE, and the
    reason is the one this file already gives for SIGTERM: prune only
    drops registrations whose DIRECTORY IS ALREADY GONE. A SIGKILL leaves
    the directory, so prune walks straight past it.
    🔴 `[measured 2026-09-19]` Driven directly — create a sweep worktree,
    run `git worktree prune`, and the registration and the 59 MB are both
    still there. So a SIGKILLed run leaks one FOR EVER, and this session's
    own container restart produced exactly that.
    ✅ The directory carries its owner's PID, so "is this an orphan" is a
    question with an exact answer rather than a heuristic on age.
    ⚠️ AND A LIVE SWEEP IS NEVER TOUCHED. `vacuity.py` says never run two
    at once and CLAUDE.md repeats it, but a cleanup that could delete a
    running sweep's tree would make that rule destructive rather than
    merely discouraged.
    """
    subprocess.run(["git", "worktree", "prune"], cwd=ROOT, check=False,
                   capture_output=True)
    for _d in glob.glob(os.path.join(tempfile.gettempdir(),
                                     "vacuity-sweep-*")):
        _m = re.search(r"vacuity-sweep-(\d+)-", os.path.basename(_d))
        if not _m:
            continue                      # not PID-tagged: leave it alone
        try:
            os.kill(int(_m.group(1)), 0)
            continue                      # ⛔ still running — hands off
        except ProcessLookupError:
            pass                          # the owner is gone
        except (PermissionError, OSError):
            continue                      # alive but not ours — hands off
        subprocess.run(["git", "worktree", "remove", "--force", _d],
                       cwd=ROOT, check=False, capture_output=True)
        shutil.rmtree(_d, ignore_errors=True)


try:
    # ⚠️ REAP FIRST, for anything an uncatchable SIGKILL left behind.
    _reap_orphans()
    # ⚠️ THE PID IS IN THE NAME so the reap above can tell an orphan from
    #    a live sweep without guessing.
    _wt = tempfile.mkdtemp(prefix="vacuity-sweep-%d-" % os.getpid())
    subprocess.run(["git", "worktree", "add", "--detach", _wt, "HEAD"],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    _swept_root = _wt
except Exception as _e:
    # ⛔ THE SWEEP IS REFUSED, NOT REDIRECTED. `_swept_root` stays None and
    #    the block below runs NOTHING rather than falling back to `ROOT`.
    # 🔴 `[measured 2026-09-19]` THIS PROSE USED TO BE FALSE. It said "DO
    #    NOT SILENTLY FALL BACK TO SWEEPING ROOT" while the next three
    #    lines read `V.tier2(_swept_root or ROOT)` — which is `ROOT` when
    #    `_swept_root` is None. `tcheck.ck()` RECORDS a failure and
    #    RETURNS; it does not abort. So a worktree failure produced a red
    #    check AND swept the collector's own tree anyway. Driven by
    #    forcing the exception and instrumenting the call: `tier2` received
    #    the live tree. It was reported, not prevented, and the comment
    #    claimed prevented.
    # ⚠️ The trigger is not hypothetical: `tempfile.mkdtemp()` raises on a
    #    full disk, and the disk hit 100% mid-sweep while #74 was being
    #    built. The one condition under which this guard matters most was
    #    the condition under which it did not hold.
    note("⛔ could not create the sweep worktree: %s: %s"
         % (type(_e).__name__, _e))
    _swept_root = None

ck("🔴🔴 a throwaway worktree was created for the real sweep",
   bool(_swept_root),
   "⛔ without it the sweep would rewrite the collector's own source, "
   "and a SIGTERM would leave it rewritten. ⚠️ WHEN THIS FAILS THE SWEEP "
   "IS REFUSED — not redirected at ROOT — so the checks below go red on "
   "an UNREADABLE result rather than green on a measurement taken from "
   "the live tree.")

if _swept_root:
    _before = V._porcelain(_swept_root)
    # ⚠️ THE SWEEP RUNS IN `V.JOBS` TREES AT ONCE (`test_vacuity_pool.py`
    #    is that pool's guard). A worker tree left modified is a leak exactly
    #    like this one left modified, so it is folded into the same verdict.
    _wleaks = []
    _t0 = time.time()
    _real2 = V.tier2(_swept_root, leaks=_wleaks)
    _elapsed = time.time() - _t0
    _ok, _dirt = V.leaked(_before, _swept_root)
    if _wleaks:
        _ok, _dirt = False, "%s\n%s" % (_dirt, "\n".join(_wleaks))
else:
    # ⛔ NO WORKTREE, NO SWEEP. Sweeping `ROOT` is the hazard this block
    #    exists to remove; running it anyway and reporting it afterwards
    #    is the hazard plus a receipt.
    # ✅ `leaked()` already fails closed on a tree git cannot be asked
    #    about — `V.leaked(None, ROOT)[0] is False`, asserted a few lines
    #    down. This is the same answer for a tree that was never created.
    # ⚠️ AND THE CHECKS BELOW GOING RED IS CORRECT, NOT COLLATERAL:
    #    nothing was measured, so nothing may be reported as a pass.
    _before, _real2, _elapsed = None, [], 0.0
    _ok, _dirt = False, ["the sweep was REFUSED: no worktree"]
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

# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 AND THE ROOT THAT WAS ACTUALLY SWEPT IS NOT THE COLLECTOR'S OWN.
# ══════════════════════════════════════════════════════════════════════
# ⛔ WITHOUT THIS, SOMEONE PUTS `V.tier2(ROOT)` BACK IN A YEAR AND
#    NOTHING NOTICES until a bad dossier is on the site. The worktree is
#    not a convenience — it is the thing standing between a SIGTERM and a
#    rewritten collector module, so it is asserted, not trusted.
ck("🔴🔴 the real sweep ran in a worktree, NOT the collector's own tree",
   bool(_swept_root)
   and os.path.realpath(_swept_root) != os.path.realpath(ROOT),
   "⛔ a kill during this sweep must be able to dirty ONLY a throwaway "
   "tree. swept=%r ROOT=%r"
   % (_swept_root and os.path.realpath(_swept_root),
      os.path.realpath(ROOT)))
ck("⚠️ ...and it really was a git tree, so leaked() could ask git at all",
   _before is not None,
   "🔴 `leaked()` fails closed on an unaskable tree, so a worktree git "
   "could not read would have surfaced here rather than silently")

# ⚠️ HOUSEKEEPING, NOT A FINDING. A leftover temp worktree costs a few
#    bytes of metadata and is not a defect in anything this file tests,
#    so removal is best-effort and never fails the run.
# ⚠️ THE NORMAL-COMPLETION PATH. `atexit` and the SIGTERM handler cover
#    the two abnormal ones; this releases the worktree as soon as the
#    sweep is done rather than at interpreter shutdown. ⛔ One
#    implementation, three callers (rule 117).
try:
    _drop_wt()
except Exception:
    pass

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

# ⚠️ WHERE THE SWEEP'S TIME WENT, printed every run. `[2026-09-23]` The
#    serial sweep reached 2401s against a 2400s clock and nothing had
#    ever said which test files it was spending on.
_cost = collections.Counter()
for _r in _real2:
    _cost[_r["test"]] += _r.get("secs") or 0
_m = re.search(r"test_vacuity\.py\)\s*echo (\d+)",
               open(os.path.join(ROOT, ".github", "workflows", "pr-tests.yml"),
                    encoding="utf-8").read())
_clock = int(_m.group(1)) if _m else None
note("the sweep took %ds wall in %d tree(s) (clock %ss); per-run total %ds. "
     "Costliest: %s"
     % (_elapsed, V.JOBS, _clock, sum(_cost.values()),
        ", ".join("%s %ds" % kv for kv in _cost.most_common(5))))
if _clock and _elapsed > _clock / 2:
    # ⛔ A WARNING, NOT A FAILURE. Failing at half the clock would halve the
    #    clock, which `test_suite_clock.py` forbids. It is here so the next
    #    slow runner is seen coming instead of met as a TIMEOUT.
    print("::warning::test_vacuity.py's sweep used %ds of its %ds clock"
          % (_elapsed, _clock))

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
_blind, _all = _BLIND_AT_IMPORT, _TESTS_AT_IMPORT
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
