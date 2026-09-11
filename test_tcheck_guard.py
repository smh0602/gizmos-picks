#!/usr/bin/env python3
"""
🔴 THE GUARD THAT STOPS A TEST WRITING THE PRODUCT — AND THE FALSE
POSITIVE THAT REDDENED A RUN FOR A FILE THAT NEVER CHANGED.

`tcheck.py` fails any test that leaves a file under `data/` or `picks/`
changed. It exists because two test files were rewriting the product's
own committed artifacts **in the same CI job that later runs
`git add data/ picks/`** — and the real damage was not the content, it
was the MONITOR: the freshness contract watches `record.json`'s age to
prove the grader ran, and a test rewriting it hourly made that row
permanently green (rule 123).

⛔ **BUT THE SNAPSHOT IS `(size, mtime_ns)`, NOT A CONTENT HASH** — for
speed, 1,066 files in 19ms. So a file whose mtime moves while its bytes
are identical was indistinguishable from one that was rewritten.

🔴 **AND THAT COST A RED RUN.** `[2026-09-08]` `test_conf_filter.py` was
reported as having MODIFIED `data/ncaaf/latest/teams.json`. **It cannot
have.** It imports nothing but stdlib and `tcheck`, it only READS that
file, and its single write is a JS harness inside a tempdir. It never
reproduced across three full sweeps.

⚠️ **AN mtime-ONLY TOUCH HARMS NEITHER THING THE GUARD PROTECTS:**
`git add` stages CONTENT, so nothing would be committed; and
`freshness.py` BANS `os.path.getmtime` outright — it reads the `built_at`
stamp inside the file — so no freshness row can be held green by one.

✅ **SO GIT ADJUDICATES**, being the same authority that would commit it.
The fast stat walk stays the detector; git is asked only about the
handful it flags, so a clean run costs nothing.

⛔ **THIS FILE EXISTS TO PROVE THE GUARD DID NOT GET WEAKER.** All three
cases are DRIVEN in a real subprocess against the real repo:

    a real content rewrite   -> STILL FAILS
    a newly added file       -> STILL FAILS
    an mtime-only touch      -> passes, and SAYS SO

⚠️ Every case restores the tree itself, and this file's own `tcheck` gate
then confirms it left nothing behind — so the test that checks the guard
is itself subject to it.
"""
import os
import subprocess
import sys
import textwrap

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

PROBE = "data/ncaaf/latest/teams.json"
ADDED = "data/ncaaf/latest/_tcheck_probe_delete_me.json"


def _run(body):
    """Run a throwaway test file that imports the REAL tcheck."""
    src = textwrap.dedent("""
        import os, sys
        sys.path.insert(0, %r)
        os.chdir(%r)
        from tcheck import ck
        ck("the probe recorded a check", True)
    """ % (ROOT, ROOT)) + textwrap.dedent(body)
    p = os.path.join(ROOT, "_tcheck_probe.py")
    open(p, "w", encoding="utf-8").write(src)
    try:
        r = subprocess.run([sys.executable, p], capture_output=True,
                           text=True, cwd=ROOT, timeout=300)
        return r.returncode, r.stdout + r.stderr
    finally:
        os.remove(p)


def _clean():
    """⛔ Restore the tree however the probe left it."""
    subprocess.run(["git", "checkout", "--", PROBE], cwd=ROOT,
                   capture_output=True)
    if os.path.exists(os.path.join(ROOT, ADDED)):
        os.remove(os.path.join(ROOT, ADDED))


print("\n═══ 1. 🔴 A REAL PRODUCT WRITE STILL FAILS ═══")
rc, out = _run("""
    import json
    d = json.load(open(%r))
    d["_tcheck_probe"] = 1
    json.dump(d, open(%r, "w"))
""" % (PROBE, PROBE))
_clean()
ck("🔴 rewriting a watched file FAILS the test file",
   rc == 1 and "MODIFIED" in out,
   "⛔ this is rule 123 and it must never stop biting: exit=%d" % rc)
ck("   ...and it names the file and calls it rewritten",
   PROBE in out and "rewritten" in out,
   "the reader has to know which artifact and how")

print("\n═══ 2. 🔴 A NEWLY ADDED FILE STILL FAILS ═══")
# ⛔ git reports an untracked file as `??`, so the adjudication must catch
#    it too — an added artifact is as committable as a rewritten one.
rc, out = _run("""
    open(%r, "w").write("{}")
""" % ADDED)
_clean()
ck("🔴 creating a file under data/ FAILS the test file",
   rc == 1 and "MODIFIED" in out, "exit=%d" % rc)
ck("   ...and it is reported as ADDED, not rewritten",
   "added" in out, "different facts, different words")

print("\n═══ 3. ✅ AN mtime-ONLY TOUCH DOES NOT ═══")
# 🔴 THE 2026-09-08 FALSE POSITIVE. The bytes are untouched; only the
#    timestamp moves. git has nothing to commit, and freshness never
#    reads mtime, so nothing this guard protects is affected.
rc, out = _run("""
    import os
    os.utime(%r, None)
""" % PROBE)
_clean()
ck("✅ touching mtime without changing bytes does NOT fail",
   rc == 0,
   "⛔ a guard that fails on a file nobody changed teaches people to "
   "ignore it — which is how the original staleness survived a day: "
   "exit=%d" % rc)
ck("⚠️ ...but it is REPORTED, never silent",
   "mtime but NOT content" in out and "mtime only" in out,
   "an absence with no explanation is the blind spot wearing a hat")
ck("   ...and it says git is the authority it asked",
   "git reports nothing to commit" in out,
   "so the next reader knows WHY it was allowed")

print("\n═══ 4. ⛔ WHAT WAS NOT RELAXED ═══")
src = open("tcheck.py", encoding="utf-8").read()
ck("🔴 an unverifiable answer still FAILS",
   "unverifiable change is still a change" in src,
   "no git, no binary, an error — the old behaviour stands. ⛔ The "
   "fallback is the safe direction, and it was PROVEN once by accident: "
   "the first version of this passed a tuple to a list concat, raised "
   "TypeError, and correctly failed the run instead of passing it")
ck("...and the fast stat walk is still the detector",
   "st_mtime_ns" in src and "_snapshot()" in src,
   "git is asked only about the files the walk flags, so a clean run "
   "pays nothing")

note("⚠️ THE GUARD'S QUESTION IS UNCHANGED — 'would this test cause a "
     "change to be committed?' ⛔ What changed is that it now asks the "
     "thing that would do the committing, instead of inferring it from a "
     "timestamp.")
