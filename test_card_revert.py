#!/usr/bin/env python3
"""
🔴🔴 A CARD THAT FAILED ITS OWN VERIFICATION WAS PUBLISHED, BECAUSE THE
REVERT CANNOT REVERT A FILE GIT HAS NEVER SEEN.

`[2026-09-11]` `picks/2026-09-11.json` was **ADDED** to the repo in commit
`9ab382f` at 14:07Z — **the same commit that wrote
`data/latest/card-verify-failure.txt`.** The workflow had already decided
the card must not ship:

    rc=1
    ::error::verify_card failed ... nobody has accepted -- reverting the card
    git checkout -- "picks/$(date -u +%Y-%m-%d).json" 2>/dev/null || true

⛔ **`git checkout` CANNOT REVERT AN UNTRACKED FILE.** On the FIRST card
build of any day the card is brand new, so the revert exits 1, changes
nothing, and the `git add -A` a few lines later **stages and publishes
it.** `|| true` swallowed the error, so no log line anywhere said so.

    $ git checkout -- picks/new.json
    error: pathspec 'picks/new.json' did not match any file(s) known to git
    exit 1 -- file untouched -- then staged as `A`

⚠️ **TODAY'S CARD WAS NOT WRONG.** The check that failed was the one
running v4.0's coefficients against a v5.0 card (ledger rule 207), and
the card's own numbers verify at a 0.0424 pt gap. ⛔ **But that is LUCK,
not a safety property**, and this repo's first rule is that a card which
fails its checks does not reach a page Sam bets from.

✅ **THE FIX IS NOT A PARAPHRASE AND NEITHER IS THIS TEST.** The revert
block is **read out of `.github/workflows/collect.yml` and executed** in a
throwaway git repo, so what is proved here is the shipped shell — not a
restatement of it that can drift (rule 66).

➡️ **BOTH BRANCHES MATTER AND BOTH ARE DRIVEN:** a card git already knows
is RESTORED to its committed bytes; a card git has never seen is DELETED.
⛔ And a revert that cannot be done sets `rc=1` rather than `|| true`.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, eq, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

WF = ".github/workflows/collect.yml"
src = open(WF, encoding="utf-8").read()


def sh(cmd, cwd):
    return subprocess.run(["bash", "-c", cmd], cwd=cwd,
                          capture_output=True, text=True)


print("\n═══ 1. 🔴 THE OLD FORM IS GONE FROM THE WORKFLOW ═══")
# ⛔ Struck lines inside comments are KEPT ON PURPOSE (Sam's standing
#    rule), so the search must ignore comments or it fails on the very
#    convention that records the fix.
live = "\n".join(l for l in src.splitlines()
                 if not l.lstrip().startswith("#"))
ck("🔴 no bare `git checkout -- picks/...` swallowed by `|| true`",
   not re.search(r'git checkout -- "picks/[^"]*"\s*2>/dev/null\s*\|\|\s*true',
                 live),
   "⛔ THIS IS THE LINE THAT PUBLISHED AN UNVERIFIED CARD. It cannot "
   "revert an untracked file, and `|| true` meant nothing reported the "
   "failure")
ck("✅ ...and the revert now asks git whether it KNOWS the file",
   "git ls-files --error-unmatch" in live,
   "⛔ tracked and untracked need different verbs: restore vs delete. "
   "One verb for two states is how this shipped")
ck("⛔ ...and a revert that cannot be done is an ERROR, not a shrug",
   live.count("::error::could not restore") >= 1
   and live.count("::error::could not remove unverified") >= 1,
   "the whole point is that the card does not reach the page; failing "
   "to withhold it is the most important thing this step can report")

print("\n═══ 2. 🔴 THE SHIPPED BLOCK IS EXECUTED, NOT PARAPHRASED ═══")
m = re.search(r"^(\s*)for _c in .*?^\s*done$", src, re.M | re.S)
ck("the revert block is findable in the workflow", bool(m),
   "⛔ if this stops matching, the block was rewritten and this file is "
   "testing nothing — which is worse than not testing it (rule 182)")
BLOCK = None
if m:
    pad = len(m.group(1))
    BLOCK = "\n".join(l[pad:] if l.startswith(" " * pad) else l
                      for l in m.group(0).splitlines())
    note("driving %d line(s) lifted verbatim from %s" %
         (len(BLOCK.splitlines()), WF))

if BLOCK:
    # ⛔ THE FIXTURE'S FIRST FORM PUT BOTH CASES IN ONE REPO, KEYED ON THE
    #    BLOCK'S OWN TWO DATES -- AND FOR TEN HOURS OF EVERY DAY THOSE TWO
    #    DATES ARE THE SAME ONE. `date -u -d '10 hours ago'` is still today
    #    until 10:00Z, so the tracked card and the untracked card were
    #    written to the SAME PATH and the untracked case never existed.
    #    The check then failed on correct code (rule 202, the fixture half).
    # ✅ TWO REPOS, ONE CASE EACH, BOTH ON THE PATH THE BLOCK ITSELF
    #    COMPUTES -- so no date arithmetic here has to agree with the
    #    workflow's.
    def run_case(tracked_first):
        tmp = tempfile.mkdtemp(prefix="revert-")
        try:
            sh("git init -q . && git config user.email t@t "
               "&& git config user.name t && mkdir -p picks", tmp)
            day = sh("date -u +%Y-%m-%d", tmp).stdout.strip()
            card = os.path.join(tmp, "picks", day + ".json")
            # something committed, so the repo has a HEAD either way
            open(os.path.join(tmp, "picks", "keep.json"), "w").write("K")
            if tracked_first:
                open(card, "w").write("GOOD")
            sh("git add -A && git commit -qm base", tmp)
            open(card, "w").write("UNVERIFIED")
            r = sh("rc=0\n" + BLOCK + "\necho \"RC=$rc\"", tmp)
            state = (open(card).read() if os.path.exists(card) else None)
            staged = sh("git add -A && git status --porcelain", tmp).stdout
            return r, state, staged, day, tmp
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    r, state, staged, day, _ = run_case(tracked_first=True)
    eq(state, "GOOD",
       "✅ a card git KNOWS is restored to its committed bytes, not deleted")
    ck("✅ ...and nothing is left staged from it",
       "picks/%s.json" % day not in staged,
       "a restored card is byte-identical to HEAD, so git sees no change: "
       "%s" % staged.strip())

    r, state, staged, day, _ = run_case(tracked_first=False)
    note("untracked case: exit=%d  %s" % (r.returncode, r.stdout.strip()[-60:]))
    ck("🔴 a card git has NEVER SEEN is DELETED, not published",
       state is None,
       "⛔ THIS IS THE LIVE DEFECT. `picks/2026-09-11.json` was ADDED at "
       "14:07Z in the SAME COMMIT as `card-verify-failure.txt` — the "
       "first card build of the day, so `git checkout` had nothing to "
       "check out and `git add -A` published it anyway. state=%r" % state)
    ck("⛔ ...and it SAYS so, rather than withholding in silence",
       "was NEW and failed verify" in r.stdout,
       "a card withheld without a word is a card nobody knows is "
       "missing: %s" % r.stdout.strip()[:120])
    ck("✅ ...and there is nothing left for the commit step to stage",
       "picks/%s.json" % day not in staged,
       "⛔ the revert and the `git add -A` are a few lines of shell apart "
       "and nothing between them re-checks: %s" % staged.strip())

    print("\n═══ 3. ⛔ AND THE STRUCK LINE REALLY DID FAIL — DRIVEN ═══")
    # 🔴 RULE 202: a check is not written until it has been seen to fail on
    #    the thing it is about. The old line is run against the identical
    #    untracked case.
    tmp = tempfile.mkdtemp(prefix="revert-old-")
    try:
        sh("git init -q . && git config user.email t@t "
           "&& git config user.name t && mkdir -p picks", tmp)
        day = sh("date -u +%Y-%m-%d", tmp).stdout.strip()
        open(os.path.join(tmp, "picks", "keep.json"), "w").write("K")
        sh("git add -A && git commit -qm base", tmp)
        card = os.path.join(tmp, "picks", day + ".json")
        open(card, "w").write("UNVERIFIED")
        old = sh('git checkout -- "picks/%s.json" 2>/dev/null || true' % day, tmp)
        ck("🔴 the struck line leaves the unverified card sitting there",
           os.path.exists(card) and open(card).read() == "UNVERIFIED",
           "⛔ it exits %d having changed nothing, and `|| true` turns "
           "that into silence" % old.returncode)
        staged = sh("git add -A && git status --porcelain", tmp).stdout
        ck("⛔ ...and `git add -A` would indeed have published it",
           bool(re.search(r"^A\s+picks/%s\.json" % re.escape(day),
                          staged, re.M)),
           "the file git could not revert is staged as an ADDITION: %s"
           % staged.strip())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    note("⚠️ THE WORKFLOW'S TWO PATHS ARE THE SAME DATE FOR TEN HOURS OF "
         "EVERY DAY — `date -u -d '10 hours ago'` does not roll over until "
         "10:00Z. ⛔ That is harmless in the loop (`[ -e ]` then handled "
         "once more, idempotently) but it is what broke this file's first "
         "fixture, so it is written down rather than rediscovered.")

note("⚠️ WHAT THIS DOES NOT PROVE: that `verify_card.py` asks the right "
     "questions. It proves only that when it says NO, the card does not "
     "ship. ⛔ Those are different guarantees and this repo needs both.")
note("➡️ THE RULE THIS LEAVES BEHIND: a REVERT is a state transition, and "
     "a file that does not exist yet is one of the states. ⛔ `|| true` on "
     "a safety step converts 'I could not withhold this' into silence.")
