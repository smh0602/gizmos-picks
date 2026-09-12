#!/usr/bin/env python3
"""
SAM'S -700 FLOOR IS INCLUSIVE, AND BOTH HALVES MUST AGREE ABOUT IT.

🔴 THE FAILURE, LIVE ON 2026-09-12 (run 932, converge pass 3):

    verify_card FAILED
      FAIL no parlay leg is shorter than the -700 floor

    Walbert Ureña o2.5 K  -700  +  Ha-Seong Kim u1.5 TB  -400
                          ^^^^ exactly the floor, and legal

**THE CARD WAS RIGHT AND THE CHECK WAS WRONG.** Ledger rule 187 fixed the
BUILDER on 2026-09-11 from `>` to `>=` — *"-700 ITSELF is the shortest
rung he WILL take"* — and `verify_card.py` was not changed with it. For a
day the builder called a -700 leg legal and the verifier called it a
violation. ⚠️ **It stayed quiet until a parlay actually carried one.**

⛔ **AND THE VERIFIER HAD THE SAME ERROR IN A SECOND PLACE** that had not
fired yet: the below-floor LABEL check collected rows at `<= -700` and
then asserted they were labelled as NOT clearing — which the builder
correctly labels as clearing. **A latent boundary error is the same
defect as a live one; it is waiting for a price, not for a fix.**

🔴 **RULE 207 IN ITS PUREST FORM.** The verifier's whole job is to
disagree with the card, so a SECOND COPY of a rule inside it is the most
expensive place in this repo for a copy to drift. ✅ There is now one
constant, `card.PRICE_FLOOR`, and both halves read it.

⚠️ **CLAUDE.md FORBIDS WEAKENING A CHECK AND REQUIRES THE ARGUMENT BE
MADE EXPLICITLY WHEN ONE IS CHANGED.** It is made here: the rule, in
Sam's words and in CLAUDE.md's own table, is that rungs **BELOW** the
floor are never paired. **-700 is not below -700.** The edit permits one
price the old form rejected, and the suite is made **strictly harder** in
the same change — `verify_card.py` gained a boundary check it had no
equivalent of, and this file did not exist at all.
"""
import os
import re
import subprocess
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import card as C  # noqa: E402

print("═══ 1. 🔒 IT IS SAM'S NUMBER AND IT HAS NOT MOVED ═══")
ck("🔒 PRICE_FLOOR is -700",
   C.PRICE_FLOOR == -700,
   "⛔ CLAUDE.md lists this beside the 1.8x pair floor as a thing that "
   "must not change without Sam saying so. It is HIS number, chosen by "
   "hand, not a tolerance of ours to tune. Got %r" % C.PRICE_FLOOR)

src = open(os.path.join(ROOT, "card.py"), encoding="utf-8").read()
ck("⛔ ...and it is NOT in the model fingerprint",
   "PRICE_FLOOR" not in (re.search(r"FINGERPRINT[^\n]*\n(?:.*\n){0,25}", src)
                         or re.match("", "")).group(0)
   if re.search(r"FINGERPRINT", src) else True,
   "it is not a fitted coefficient and `test_model_version.py` must not "
   "treat it as one — a hand-chosen floor moving is a Sam decision, not "
   "a re-fit")

print("\n═══ 2. 🔴 THE BOUNDARY IS INCLUSIVE, DRIVEN NOT READ ═══")
# ⛔ The predicate itself, exactly as `card.py` writes it. A row priced AT
#    the floor clears; a row one point shorter does not.
for price, want in ((C.PRICE_FLOOR + 1, True),
                    (C.PRICE_FLOOR, True),
                    (C.PRICE_FLOOR - 1, False)):
    ck("✅ a price of %d %s the floor" % (price, "CLEARS" if want else "does NOT clear"),
       (price >= C.PRICE_FLOOR) is want,
       "⛔ '-700, nothing shorter' means -700 itself is IN. Rule 187 is "
       "the day this was got wrong in the other direction and shipped "
       "for eighteen days")

print("\n═══ 3. 🔴 THE VERIFIER READS THE CONSTANT, NOT A LITERAL ═══")
vsrc = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
# ⛔ COMMENTS STRIPPED FIRST. This file quotes the struck `<= -700` forms
#    verbatim while explaining them, and a bare search would read its own
#    documentation as the bug — the fifth time that trap has been hit in
#    this repo.
_live = "\n".join(ln for ln in vsrc.splitlines()
                  if not ln.lstrip().startswith("#"))
_bad = re.findall(r"<=\s*-700|<\s*-700|>=\s*-700|>\s*-700", _live)
ck("🔴 no live line in verify_card.py compares against a -700 LITERAL",
   not _bad,
   "⛔ a literal is a second copy of Sam's number, and the two copies "
   "drifted for a day and took a live run red with them (rule 207). "
   "Found: %s" % _bad)
ck("✅ ...it uses C.PRICE_FLOOR",
   "C.PRICE_FLOOR" in _live,
   "one constant, both readers, so they cannot disagree again")
ck("⛔ and the struck forms are kept as the record",
   "~~`any(a <= -700 ...)`~~" in vsrc or "~~`r['price'] <= -700`~~" in vsrc,
   "Sam's standing rule: strike superseded content visibly rather than "
   "deleting it")

print("\n═══ 4. 🔴🔴 FAULT-INJECTED — THE CHECK STILL BITES ═══")
# 🔴 THE HALF THAT MATTERS. A boundary loosened by one point is exactly
#    the kind of edit that silently stops catching anything, so the check
#    is DRIVEN with a genuine violation rather than read.
# ⛔ `verify_card.py` REBUILDS THE CARD IN MEMORY (`doc = C.main(dry=True)`),
#    so injecting into `picks/<date>.json` proves nothing — the first
#    attempt at this test did exactly that and "passed" against a file
#    the verifier never opens. The builder is patched instead.
INJ = r'''
import sys; sys.path.insert(0, %r)
import card as C
_orig = C.main
def patched(*a, **k):
    d = _orig(*a, **k)
    n = 0
    for rows in (d.get("parlays") or {}).values():
        for r in rows:
            for i, px in enumerate(r.get("prices") or []):
                if px == C.PRICE_FLOOR:
                    r["prices"][i] = C.PRICE_FLOOR - 1
                    n += 1
    print("INJECTED %%d" %% n, file=sys.stderr)
    return d
C.main = patched
import verify_card  # noqa
''' % ROOT

_p = subprocess.run([sys.executable, "-c", INJ], cwd=ROOT,
                    capture_output=True, text=True, timeout=600)
_n = re.search(r"INJECTED (\d+)", _p.stderr)
_injected = int(_n.group(1)) if _n else 0
if not _injected:
    note("⚠️ NOT EXERCISED: today's card has no parlay leg priced at "
         "exactly the floor, so there was nothing to push one point "
         "past it. ⛔ Reported rather than passed — this section proves "
         "nothing on a board without a leg on the boundary.")
else:
    ck("🔴 a leg ONE POINT below the floor still FAILS the verifier",
       _p.returncode != 0
       and "no parlay leg is shorter" in (_p.stdout + _p.stderr),
       "⛔ THIS IS THE CHECK THAT PROVES THE FIX IS A CORRECTION AND NOT "
       "A WEAKENING. If this passes, the boundary edit stopped the check "
       "catching anything at all. injected=%d rc=%d"
       % (_injected, _p.returncode))
    note("injected %d leg(s) at %d and the verifier exited %d"
         % (_injected, C.PRICE_FLOOR - 1, _p.returncode))

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that -700 is a good floor. It is "
     "Sam's number and nothing here measures it. What is owned is that "
     "the builder and the verifier mean the SAME THING by it, which they "
     "did not for a day.")
