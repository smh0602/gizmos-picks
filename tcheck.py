#!/usr/bin/env python3
"""tcheck.py — the one check harness every test file uses.

    from tcheck import ck, note, section

That is the whole API. ⛔ **There is no gate to write and none to
forget**: the failure gate is an `atexit` hook this module registers when
it is imported, so it runs after the last line of your file whatever that
line is.

════════════════════════════════════════════════════════════════════════
🔴 THIS EXISTS BECAUSE TWO DEFECTS KEPT SHIPPING, AND BOTH ARE STRUCTURAL
════════════════════════════════════════════════════════════════════════

**1. A SECTION APPENDED AFTER THE FAILURE GATE CANNOT FAIL.** Ledger rule
97. Checks were appended below a file's `if fails: sys.exit(1)`; they
printed 🔴 and the file still exited 0. ⛔ **It happened TWICE IN ONE DAY,
hours apart, by the person who wrote the rule** — which says the problem
is the SHAPE, not the discipline.
✅ **`atexit` makes it impossible.** There is no "after" in a file whose
gate runs at interpreter shutdown; anything appended runs BEFORE it.

**2. FOUR DIFFERENT `ck` SIGNATURES, AND ELEVEN FILES SILENTLY PASSED ON
A SWAP.** `[measured 2026-09-06 across the whole suite]`

    def ck(cond, label, detail="")    11 files   condition FIRST
    def ck(name, cond, extra="")       5 files   name FIRST
    def ck(n, ok, d="")                1 file
    def ck(name, ok, detail="")        1 file

⛔ Calling a condition-first `ck` the other way round passes **a non-empty
string as the condition**, which is TRUTHY. **Measured: 11 of 11 such
files printed a tick, recorded no failure, and never evaluated the real
condition at all.** A check that cannot fail is rule 67 in its purest
form, and eleven files were one habit away from it.
⚠️ It had already cost a live TypeError in `test_cfb.py` — that was the
LOUD version of the same mistake, and the loud version is the lucky one.

✅ **SO THIS `ck` READS THE TYPES, NOT THE POSITIONS.** Exactly one
argument must be a `str` (the name); the other is the condition. Both
orders are accepted and neither can be misread. ⛔ Ambiguity — two
strings, or no string — RAISES, because guessing is how this started.
"""
import atexit
import os
import subprocess
import sys

FAILURES = []
_CHECKS = [0]
_NOTES = []

# ══════════════════════════════════════════════════════════════════════
# 🔴 AND THE THIRD DEFECT, FOUND ON 2026-09-06 AND LIVE IN PRODUCTION:
#    TWO TEST FILES WERE WRITING THE PRODUCT'S OWN PUBLISHED ARTIFACTS.
# ══════════════════════════════════════════════════════════════════════
# `test_record_fb.py` called `record_fb.main()` in the repo root, and
# `test_p4.py` drove the Power-4 gate into its fail-closed branch, which
# writes a diagnostic file. ⛔ THE TESTS RUN IN THE SAME CI JOB THAT
# LATER RUNS `git add data/ picks/` — so `data/ncaaf/latest/record.json`
# was being rewritten and COMMITTED by every collect run of every league,
# including MLB's.
# 🔴 THE REAL DAMAGE IS NOT THE CONTENT, IT IS THE MONITOR. The freshness
# contract watches that file's age to prove the GRADER ran. A test that
# rewrites it every hour makes that row permanently green — a check that
# can no longer fail, which is rule 67 wearing an artifact for a costume.
# ✅ So the guard lives HERE, where every test file already imports it,
# rather than in a rule nobody can enforce.
# ⚠️ (path, size, mtime), not content hashes: 1,066 files in 19ms.
_WATCH = ("data", "picks")


def _snapshot():
    seen = {}
    for root in _WATCH:
        for d, _, fs in os.walk(root):
            for f in fs:
                p = os.path.join(d, f)
                try:
                    s = os.stat(p)
                    seen[p] = (s.st_size, s.st_mtime_ns)
                except OSError:
                    pass
    return seen


# ⚠️ TAKEN AT IMPORT, from whatever directory the test was started in. A
# file run from somewhere with no data/ simply watches nothing, which is
# the correct behaviour for a fixture tree, not a reason to fail.
_BEFORE = _snapshot()


def _order(a, b):
    """(name, cond) from either order. ⛔ Raises rather than guessing."""
    a_s, b_s = isinstance(a, str), isinstance(b, str)
    if a_s and not b_s:
        return a, b
    if b_s and not a_s:
        return b, a
    if a_s and b_s:
        raise TypeError(
            "ck() got two strings — one of them has to be the condition. "
            f"Got {a!r} and {b!r}. ⛔ This is not guessed: a condition that "
            "is a string is exactly the bug this harness exists to stop.")
    raise TypeError(
        "ck() got no string — one of the two arguments has to be the "
        f"check's NAME. Got {a!r} and {b!r}.")


def ck(a, b, extra=""):
    """Record one check. Name and condition in either order.

    ⚠️ The condition may be any truthy value — a bool, a count, a list.
    It just may not be a `str`, because a string condition is always
    truthy and is the failure mode this harness was built for.
    """
    name, cond = _order(a, b)
    _CHECKS[0] += 1
    ok = bool(cond)
    print(("  ✅ " if ok else "  ❌ ") + name + (f"  — {extra}" if extra else ""))
    if not ok:
        FAILURES.append(name)
    return ok


def note(s):
    """Something worth printing that is NOT a pass/fail claim.

    ⛔ Use this for anything REPORTED rather than asserted — a measurement
    of the world that a test may not turn red on (ledger rule 76).
    """
    _NOTES.append(s)
    print("  ⚪ " + str(s))


def section(title):
    print("\n═══ " + str(title) + " ═══")


def eq(got, want, name):
    """`got == want`, with both values printed on the row.

    ⚠️ SEVEN FILES CARRIED A BYTE-IDENTICAL COPY OF THIS before the
    harness existed, each appending to its own `fails` list. ⛔ Seven
    copies of a helper is seven places for a gate to be forgotten.
    """
    return ck(name, got == want, f"got {got!r}, want {want!r}")


def fail(name, extra=""):
    """Record a failure with no condition to evaluate."""
    return ck(name, False, extra)


@atexit.register
def _gate():
    """🔴 THE GATE. Registered at import, runs at interpreter exit.

    ⛔ **Nothing can be appended past this**, which is the entire point:
    a check written at the bottom of a test file runs BEFORE this, not
    after it. Ledger rule 97 becomes unwritable rather than merely
    forbidden.

    ⚠️ `os._exit` AFTER AN EXPLICIT FLUSH. `sys.exit` inside an atexit
    hook raises SystemExit, which Python reports and then ignores for the
    process's status — the run would print a failure and exit 0, which is
    the very defect this file is here to prevent. `os._exit` skips the
    remaining hooks and buffers, so the flush is done by hand first.
    """
    try:
        # 🔴 DID THIS FILE WRITE THE PRODUCT? Checked BEFORE the summary,
        # so a side effect is a failure like any other and cannot hide
        # behind a green count.
        after = _snapshot()
        touched = sorted(p for p in set(_BEFORE) | set(after)
                         if _BEFORE.get(p) != after.get(p))
        # ══════════════════════════════════════════════════════════════
        # 🔴 AN mtime THAT MOVED IS NOT A PRODUCT THAT CHANGED, AND THIS
        #    REDDENED A RUN FOR ONE. `[2026-09-08, never reproduced]`
        #    `test_conf_filter.py` was reported as having MODIFIED
        #    `data/ncaaf/latest/teams.json`. It cannot have: it imports
        #    nothing but stdlib and `tcheck`, it only READS that file,
        #    and its one write is a JS harness inside a tempdir. Three
        #    full sweeps since have never reproduced it.
        # ⛔ THE SNAPSHOT IS `(size, mtime_ns)` FOR SPEED — 1,066 files in
        #    19ms — so a file whose mtime moves while its BYTES are
        #    identical is indistinguishable from one that was rewritten.
        # ⚠️ AND AN mtime-ONLY TOUCH HARMS NEITHER THING THIS GUARD
        #    PROTECTS: `git add` stages CONTENT, so nothing would be
        #    committed; and `freshness.py` BANS `os.path.getmtime`
        #    outright, reading the `built_at` stamp inside the file — so
        #    no freshness row can be held green by it either.
        # ✅ SO ASK GIT, WHICH IS THE AUTHORITY THAT WOULD COMMIT IT, and
        #    is the exact question rule 123 cares about. The fast stat
        #    walk stays the DETECTOR; git adjudicates only the handful it
        #    flags, so this costs nothing on a clean run.
        # ⛔ NOT WEAKER: every content change is still caught, including
        #    an ADDED file (git reports it as `??`) and a DELETED one.
        #    What stops failing is the case where nothing changed at all.
        #    ⚠️ If git cannot answer — no repo, no binary, an error — the
        #    old behaviour stands and the run fails. An unverifiable
        #    change is still a change.
        # ══════════════════════════════════════════════════════════════
        if touched:
            try:
                _g = subprocess.run(
                    ["git", "status", "--porcelain", "--"] + list(_WATCH),
                    capture_output=True, text=True, timeout=60)
                if _g.returncode == 0:
                    _dirty = {ln[3:].strip().strip('"')
                              for ln in _g.stdout.splitlines() if ln[3:].strip()}
                    _real = [p for p in touched
                             if any(p == d or p.startswith(d.rstrip("/") + "/")
                                    or d.startswith(p) for d in _dirty)]
                    if not _real:
                        print("  ⚪ ⚠️ %d file(s) under data/ or picks/ changed "
                              "mtime but NOT content — git reports nothing to "
                              "commit, so the product is untouched. Reported, "
                              "not failed." % len(touched))
                        for _p in touched[:4]:
                            print(f"     - {_p}  (mtime only)")
                        touched = []
                    else:
                        touched = _real
            except Exception as _e:
                print("  ⚠️ could not ask git whether the content changed "
                      "(%s) — failing on the stat difference, because an "
                      "unverifiable change is still a change" % type(_e).__name__)
        if touched:
            _CHECKS[0] += 1
            name = ("🔴 this test MODIFIED %d file(s) under data/ or picks/ "
                    "— a test must not write the product" % len(touched))
            print("  ❌ " + name)
            for p in touched[:8]:
                kind = ("added" if p not in _BEFORE else
                        "deleted" if p not in after else "rewritten")
                print(f"     - {p}  ({kind})")
            print("     ⛔ Run it in a temp tree instead. These files are "
                  "committed by the same CI job that runs the tests, and an "
                  "artifact a test keeps fresh is a freshness row that can "
                  "never go red.")
            FAILURES.append(name)
        if FAILURES:
            print(f"\n❌ {len(FAILURES)} of {_CHECKS[0]} checks FAILED")
            for f in FAILURES:
                print("   - " + f)
        elif _CHECKS[0]:
            print(f"\n✅ all {_CHECKS[0]} checks passed")
        else:
            # ⛔ A FILE THAT CHECKED NOTHING IS NOT A PASSING FILE. A test
            # that silently stops asserting is indistinguishable from a
            # deleted one, and CI would go green either way.
            print("\n❌ this file recorded NO checks at all — a test that "
                  "asserts nothing cannot pass")
            FAILURES.append("no checks recorded")
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
    if FAILURES:
        os._exit(1)
