#!/usr/bin/env python3
"""THE ACCEPTED-FAILURE GATE — the one tool that can turn a red run green.

🔴 IT HAD NO TEST AT ALL UNTIL 2026-09-04, which is a strange gap for the
only file in the repo whose whole job is deciding whether a failure is
allowed to pass quietly.

⛔ AND IT COST A REAL EVENING. Sam decided to accept T37, typed the entry
onto the end of `card-accepted.txt` — whose last line is a bare `#`
separator — and got `#T37 | ...`: a perfectly formed acceptance, in the
file, in the commit, **and invisible.** The gate then reported *"NOT an
accepted failure — this is new, look at it"*, which was the one thing it
was not. The run stayed red and nobody could see why.

✅ WHAT IS PINNED HERE:
  1. an accepted id turns the gate green, and the card is STILL refused
  2. ⛔ a COMMENTED-OUT entry is NOT honoured — a stray `#` must never
     accept a failure nobody signed off
  3. 🔴 ...but the gate SAYS the entry is sitting there commented out,
     at the moment the operator is reading the failure
  4. an unrelated failure is still red, even with other ids accepted
  5. a failure with no `T<n>` id at all cannot be accepted, and says so
     rather than guessing

⚠️ No network, no repo state: every case writes its own file.

# @vacuity [Sam, 2026-10-01] the page no longer reads card_caveat (no stale bar)
#   file: index.html
#   find: catch(e){ FRESH = null; }
#   with: catch(e){ FRESH = null; } if (FRESH && FRESH.card_caveat) document.title = FRESH.card_caveat;
#
# @vacuity [Sam, 2026-10-01] ...nor card_blocked, anywhere on the page
#   file: index.html
#   find: catch(e){ FRESH = null; }
#   with: catch(e){ FRESH = null; } if (FRESH && FRESH.card_blocked) document.title = FRESH.card_blocked;
#
# @vacuity [Sam, 2026-10-01] neither card sentence is on the page
#   file: index.html
#   find: let FRESH = null;
#   with: let FRESH = null; const CARD_NOTE = "Today's card is published with a known caveat.";
#
# @vacuity [Sam, 2026-10-01] ...nor the refused card's sentence
#   file: index.html
#   find: let FRESH = null;
#   with: let FRESH = null; const CARD_NOTE = "Gizmo's Picks is showing an earlier version.";
#
# @vacuity the absence checks read real code: the refresh loop's FRESH.built_at is found
#   file: index.html
#   find: const built  = (FRESH && FRESH.built_at) || '';
#   with: const built  = '';
"""
import os
import shutil
import subprocess
import sys
import tempfile
from tcheck import ck, note   # the shared gate — see tcheck.py

REPO = os.path.dirname(os.path.abspath(__file__))
fails = []


HEADER = (
    "# CARD FAILURES SAM HAS LOOKED AT AND CHOSEN TO LIVE WITH.\n"
    "#\n"
    "# format:  CHECK_ID | why, and the date the decision was made\n"
    "#\n"
)


def run(accepted_body, failures_line):
    """Drive the real card_gate.py against a constructed pair of files."""
    t = tempfile.mkdtemp()
    try:
        shutil.copy(os.path.join(REPO, "card_gate.py"), t)
        with open(f"{t}/card-accepted.txt", "w", encoding="utf-8") as fh:
            fh.write(HEADER + accepted_body)
        with open(f"{t}/vc.txt", "w", encoding="utf-8") as fh:
            fh.write("  FAIL something\n" + failures_line + "\n")
        p = subprocess.run([sys.executable, "card_gate.py", "vc.txt"], cwd=t,
                           capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr
    finally:
        shutil.rmtree(t, ignore_errors=True)


T37 = "FAILURES: T37: hitter projections contradict <= 5.0% at 70%+ (63 of 1215)"

print("\n1. AN ACCEPTED FAILURE TURNS THE RUN GREEN")
rc, out = run("T37 | a mean-vs-frequency artifact. 2026-09-04\n", T37)
ck(rc == 0, "the gate returns 0", f"rc={rc}")
ck("accepted      ['T37']" in out, "  and names what it accepted")
ck("NOT published" in out,
   "⛔ and it still says the CARD DID NOT PUBLISH (rule 73)")

print("\n2. 🔴 THE BUG OF 2026-09-04: THE ENTRY IS THERE, COMMENTED OUT")
print("   `#T37 | ...` — typed onto the end of the file's bare `#` line.")
rc2, out2 = run("#T37 | a mean-vs-frequency artifact. 2026-09-04\n", T37)
ck(rc2 == 1, "⛔ it is NOT honoured — a stray '#' cannot accept anything",
   f"rc={rc2}")
ck("COMMENTED OUT" in out2,
   "🔴 but the gate SAYS SO, instead of calling it new")
ck("Remove the leading" in out2, "  and says exactly what to do")
ck("this is new, look at it" not in out2,
   "⛔ and it no longer claims a decided thing is new")

print("\n3. AN UNRELATED FAILURE IS STILL RED")
rc3, out3 = run("T37 | accepted. 2026-09-04\n",
                "FAILURES: T21: something else entirely")
ck(rc3 == 1, "T21 is not accepted just because T37 is", f"rc={rc3}")
ck("['T21']" in out3, "  and the error names the right check")

print("\n4. TWO FAILURES, ONE ACCEPTED — STILL RED")
rc4, _ = run("T37 | accepted. 2026-09-04\n",
             "FAILURES: T37: the artifact, T21: something new")
ck(rc4 == 1, "⛔ every failing check must be accepted, not just one",
   f"rc={rc4}")

print("\n5. A FAILURE WITH NO CHECK ID CANNOT BE ACCEPTED")
print("   ⚠️ It returns 2 — 'could not tell' — and never guesses.")
rc5, out5 = run("T37 | accepted. 2026-09-04\n",
                "FAILURES: the Hard Rock flag is written on every row")
ck(rc5 == 2, "could not identify a check id -> 2, not 0", f"rc={rc5}")

print("\n6. NO `FAILURES:` LINE AT ALL -> REFUSE, NEVER GUESS")
t = tempfile.mkdtemp()
try:
    shutil.copy(os.path.join(REPO, "card_gate.py"), t)
    open(f"{t}/card-accepted.txt", "w").write(HEADER)
    open(f"{t}/vc.txt", "w").write("everything passed\n")
    p = subprocess.run([sys.executable, "card_gate.py", "vc.txt"], cwd=t,
                       capture_output=True, text=True)
    ck(p.returncode == 2, "no FAILURES line -> 2", f"rc={p.returncode}")
    ck("refusing to guess" in p.stdout + p.stderr, "  and says why")
finally:
    shutil.rmtree(t, ignore_errors=True)

print("\n7. ⛔ THE REPO'S OWN FILE STILL PARSES")
print("   A header-only file is valid; a malformed one is not.")
sys.path.insert(0, REPO)
os.chdir(REPO)
import card_gate as G
_acc = G.load_accepted()
ck(isinstance(_acc, dict), "load_accepted returns a mapping", str(sorted(_acc)))
ck(all(k.startswith("T") for k in _acc),
   "⚠️ every live entry is a T-number the gate can match", str(sorted(_acc)))


print("\n8. 🔴 AN ACCEPTED FAILURE NOW PUBLISHES THE CARD")
print("   ⛔ Until 2026-09-04 it did not, and that made acceptance")
print("   WORTHLESS: the run went green and the board froze for days.")
print("   Either acceptance publishes, or acceptance should not exist.")
_wf = open(os.path.join(REPO, ".github/workflows/collect.yml"),
           encoding="utf-8").read()
import re as _re

# ⛔ THE ONE LINE THAT MUST NEVER COME BACK: a revert that runs whatever
# the gate decided. Counted, not eyeballed.
_lines = [l for l in _wf.splitlines() if "git checkout -- picks/" in l
          and not l.strip().startswith("#")]
ck(not _lines,
   "⛔ no unconditional `git checkout -- picks/` survives", str(_lines[:1]))

# the revert must live INSIDE the branch taken when card_gate FAILS
_i = _wf.find("if python card_gate.py")
ck(_i > 0, "the workflow branches on card_gate's exit code")
_after = _wf[_i:_i + 2500]
_else = _after.find("else")
_rev = _after.find("git checkout --")
ck(_else > 0 and _rev > _else,
   "🔴 the revert is in the NOT-ACCEPTED branch, never the accepted one",
   f"else@{_else} revert@{_rev}")
ck("card-accepted-now.txt" in _after,
   "  and the accepted path leaves a marker the page can read")

# ══════════════════════════════════════════════════════════════════════
# 🔴 [Sam, 2026-10-01] THE CAVEAT IS STILL PUBLISHED; THE PAGE NO LONGER
#    PRINTS IT. Until today this section also required index.html to read
#    FRESH.card_caveat and print it in the stale bar ("Today's card is
#    published with a known caveat"), worded apart from a refused card
#    ("showing an earlier version"), because that sentence was the stated
#    justification for publishing a card that failed one of its own
#    checks. Sam removed the bar with every other note on every tab: "i
#    just want what's supposed to be in each tab to be in each tab"; asked
#    what stays, he chose: remove everything. So the page checks now
#    require the ABSENCE of the field and both sentences. ⛔ The DATA side
#    is unchanged: collect.py still publishes card_caveat (and
#    card_blocked) into freshness.json from the workflow's marker.
#    Asked of the page's CODE: this repo strikes deleted code in a comment.
# ══════════════════════════════════════════════════════════════════════
print("\n9. ⛔ THE CARD STILL PUBLISHES WHAT IT IS CARRYING")
print("   ...into freshness.json. [Sam, 2026-10-01] the page no longer")
print("   prints it: no stale bar, no caveat line, on any tab.")
_col = open(os.path.join(REPO, "collect.py"), encoding="utf-8").read()
ck('"card_caveat"' in _col,
   "collect.py publishes `card_caveat` into freshness.json")
ck("card-accepted-now.txt" in _col,
   "  derived from the marker the workflow leaves")
_idx = open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
_code = _re.sub(r"<!--.*?-->|/\*.*?\*/", "", _idx, flags=_re.S)
_code = "\n".join(l for l in _code.splitlines() if not l.strip().startswith("//"))
ck("FRESH.built_at" in _code,
   "  (control: comments stripped, the page's code is still there to ask)")
ck("FRESH.card_caveat" not in _code,
   "🔴 index.html no longer reads it (no stale bar)")
ck(_code.count("card_caveat") == 0 and _code.count("card_blocked") == 0,
   "  ...nor the refused-card field, anywhere on the page",
   str((_code.count("card_caveat"), _code.count("card_blocked"))))
# ⛔ ~~REFUSED AND CAVEATED MUST BE DIFFERENT SENTENCES~~ -> NEITHER IS SHOWN.
ck("known caveat" not in _code and "showing an earlier version" not in _code,
   "🔴 neither the caveated nor the refused sentence is on the page")
note("⚠️ WHAT THIS LEAVES OPEN: with the sentence off the page, a card "
     "published under an accepted failure says so only in freshness.json "
     "and in card_gate's ::warning line in the run log. Whether that is "
     "enough is Sam's call; this file does not decide it.")
