#!/usr/bin/env python3
"""
🔴 THE MLB CARD'S SELF-CONTRADICTING ROW — AND WHY NOBODY COULD DIAGNOSE IT.

`[2026-09-06, Sam's #3]` `verify_card` was failing on rows like
*Andrés Chaparro · batter_rbis · UNDER 0.5 · confidence 76 · projection
0.6* — a card that appears to argue with itself.

⛔ THE GATE IS RIGHT AND IS PRE-REGISTERED. T37's fallback (triggered
2026-09-04, after the hitter contradiction rate failed at 5.43% against a
5.00% bar) says a `HITTER_PROJ` market's projection is an INVERSION of the
player's own record at the primary line. **An inversion cannot land on the
losing side of the line it was inverted at**, so zero tolerance is correct
there — unlike a MEAN, which honestly can.

🔴 WHAT WAS WRONG IS ONE LINE OF CONTROL FLOW: when
`hitter_primary_projection` cannot build the inversion, the code fell
through to `hitter_mean` — **the very statistic T37 measured and replaced**
— and said nothing. The row then read "his own per-game average", true of
the value and silent about the method having failed.

⚠️ MEASURED, so the size is known: across every published card, exactly
TWO rows would fail the gate (Luis Lara 08-28, Tommy Edman 09-03), both
`batter_rbis under 0.5`. And in the log those players are genuinely
~74-77% under the line while averaging near it — which is what a
negative-binomial count looks like.

⛔ THIS FILE CHANGES NO NUMBER AND DOES NOT RE-DECIDE T37. It pins that
the card RECORDS which method produced each projection, and SAYS SO on a
row that fell back.
"""
import inspect
import os

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
import card as C  # noqa: E402


def code_only(fn):
    src = inspect.getsource(fn)
    doc = inspect.getdoc(fn)
    if doc:
        for line in doc.splitlines():
            line = line.strip()
            if line:
                src = src.replace(line, "")
    return "\n".join(ln.split("#")[0] for ln in src.splitlines())


print("\n═══ 1. THE PRE-REGISTERED DESIGN IS STILL IN PLACE ═══")
ck("RBIs are declared a skewed count, not a symmetric one",
   C.HITTER_PROJ.get("batter_rbis") == "negbin",
   "a negbin with mean 0.6 and dispersion 0.3 puts 72% of its mass at "
   "ZERO — which is why the MEAN can honestly sit on the far side of "
   "the line and the INVERSION cannot")
ck("hits and home runs use their own passing distribution",
   C.HITTER_PROJ.get("batter_hits") == "poisson"
   and C.HITTER_PROJ.get("batter_home_runs") == "poisson")
ck("⛔ total bases and H+R+RBI are NOT in it",
   not any(k.startswith("batter_total") or "rbis_runs" in k
           for k in C.HITTER_PROJ),
   "T34/T35 rejected all three distributions for them, so they keep the "
   "mean — inverting through a rejected distribution would be worse")
ck("the inversion helper T37's fallback names still exists",
   callable(getattr(C, "hitter_primary_projection", None)),
   "invert ONCE at the primary line and reuse it (rule 66)")

print("\n═══ 2. 🔴 THE FALL-BACK IS NO LONGER SILENT ═══")
src = code_only(C.coherent_projections)
ck("the builder records WHICH method produced each number",
   "_proj_method" in src,
   "without it, a projection that fell back from the inversion to the "
   "mean it replaced is indistinguishable from one that never had a "
   "distribution")
ck("🔴 a HITTER_PROJ market falling through is marked as a FALLBACK",
   "mean_fallback" in src,
   "that is T37's rejected statistic, reached by control flow")
ck("...and a market that never had a distribution is marked differently",
   '"mean"' in src and '"inversion"' in src,
   "three methods, three labels — 'no distribution' and 'the "
   "distribution failed today' are different facts")
ck("the method travels out with the projection",
   '"m": _proj_method.get(k)' in src,
   "a value nobody can trace back to its method is a number without a "
   "provenance")

print("\n═══ 3. AND THE ROW SAYS SO TO THE READER ═══")
note_src = code_only(C.attach_projections) if hasattr(C, "attach_projections") \
    else open(os.path.join(ROOT, "card.py"), encoding="utf-8").read()
ck("a fallback row explains that the usual method could not be built",
   'e.get("m") == "mean_fallback"' in note_src
   and "could not be built" in note_src,
   "the reader is looking at the statistic T37 rejected and deserves to "
   "know")
ck("...and it warns that an average is a poor guide on a lumpy count",
   "lumpy count" in note_src)
ck("⛔ the note is attached to the ROW, not written into the page",
   'r["projection_method"]' in note_src,
   "rule 132 — the page prints what the card computed")

print("\n═══ 4. ⛔ NOTHING WAS RE-DECIDED ═══")
v = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
ck("T37's bar is untouched and still enforced",
   "T37: hitter projections contradict <= " in v,
   "the pre-registered bar governs; this change does not move it")
ck("🔴 the zero-tolerance inversion gate is STILL THERE",
   "NO inverted hitter projection contradicts its own row" in v,
   "it is correct for an inversion and was catching a real defect — "
   "removing it would have hidden the bug rather than fixing it")
ck("⚠️ ...and no projection VALUE is changed by this work",
   "hitter_mean(hlogs, pid, mkt, today)" in code_only(C.coherent_projections),
   "the same number is still published; what is added is the record of "
   "how it was produced")
