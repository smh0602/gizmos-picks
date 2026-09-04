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
"""
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.abspath(__file__))
fails = []


def ck(cond, label, detail=""):
    print(f"  {'ok  ' if cond else '🔴 FAIL'} {label:<58} {detail}")
    if not cond:
        fails.append(label)


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

print()
if fails:
    print(f"🔴 {len(fails)} FAILURE(S)")
    for f in fails:
        print(f"   - {f}")
    sys.exit(1)
print("✅ card_gate: accepts what was signed off, and nothing else")
