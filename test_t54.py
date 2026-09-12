#!/usr/bin/env python3
"""
T54 MUST BE ABLE TO ACCUMULATE, AND MUST SAY SO EVERY RUN.

🔴 THE DEFECT THIS FILE EXISTS FOR, MEASURED 2026-09-12:

    published football picks carrying own_mean   339 of 339
    GRADED rows carrying own_mean                  0 of 200

T54 was pre-registered on 2026-09-04 and had been open EIGHT DAYS. Its
sample was not small — it was **structurally stuck at zero**, because
`record_fb.py` built its graded rows without the field the test splits
on. ⛔ **That is not "not yet measurable for lack of sample."** It is a
test that could never have become measurable, sitting open and looking
like it was merely waiting.

➡️ **AN OWED TEST THAT CANNOT ACCUMULATE IS WORSE THAN ONE NOBODY
OPENED**, because the register says it is in progress.

⛔ WHAT THIS FILE DOES NOT DO: check T54's ANSWER. There is no answer yet
and there must not be one until 40 graded stretched rows exist. What it
owns is that the machinery can reach 40 at all, that the specification
has not drifted, and that the count is printed without being asked for.
"""
import gzip
import json
import os
import re
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import t54  # noqa: E402

print("═══ 1. 🔒 THE SPECIFICATION HAS NOT DRIFTED ═══")
# ⛔ THESE THREE NUMBERS WERE FIXED 2026-09-04 BEFORE ANY CUTOFF WAS
#    TRIED. Re-choosing any of them after seeing an outcome is the exact
#    failure the pre-registration exists to prevent, and it is the
#    failure this project has made twice.
# ⚠️ The 2.0 is INHERITED from the warning sentence already shipped on
#    the card — it was never chosen for this test.
for name, want in (("STRETCH_CUTOFF", 2.0), ("MIN_STRETCHED", 40),
                   ("GAP_TOLERANCE", 5.0)):
    got = getattr(t54, name)
    ck("🔒 %s is still %r" % (name, want), got == want,
       "⛔ `claude/owed-tests.md` fixed this on 2026-09-04. If it moved "
       "for a reason, the reason belongs in a NEW pre-registration and "
       "this line changes with it — never to make an outcome nicer. "
       "Got %r" % got)

src = open(os.path.join(ROOT, "t54.py"), encoding="utf-8").read()
ck("⛔ the split is symmetric, as the spec requires",
   "1.0 / s" in src and '"over"' in src,
   "an UNDER is stretched when the line sits far ABOVE the player's "
   "mean and an OVER when it sits far BELOW; one ratio cannot express "
   "both, so the spec names the reciprocal")
ck("⛔ voids and unresolved rows are excluded from every denominator",
   'r.get("won") is None' in src,
   "the specification says so, and a void counted as a loss is a "
   "fabricated observation")

print("\n═══ 2. 🔴 THE GRADER CARRIES THE FIELD THE TEST SPLITS ON ═══")
rec = open(os.path.join(ROOT, "record_fb.py"), encoding="utf-8").read()
# ⛔ ASKED OF THE ROW BUILDER, NOT OF THE FILE. record_fb.py mentions
#    own_mean in the comment explaining why it is carried, so a bare
#    substring search over the source would pass on a file that only
#    documents the field. Fourth instance of that trap in this repo.
_base = rec[rec.index("        base = {"):]
_base = _base[:_base.index("\n        }") + 10]
_live = "\n".join(ln for ln in _base.splitlines()
                  if not ln.strip().startswith("#"))
ck("🔴 record_fb.py puts own_mean ON THE GRADED ROW",
   '"own_mean"' in _live,
   "⛔ without it T54's split cannot be computed and the test can NEVER "
   "reach its minimum, however many slates pass. Measured 2026-09-12: "
   "339 of 339 published picks carried it and 0 of 200 graded rows did")

print("\n═══ 3. 🔴 IT RUNS ON THE JOB THAT WRITES WHAT IT READS ═══")
col = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
_arm = col[col.index('elif mode == "fb-record":'):]
_arm = _arm[:_arm.index('elif mode == "news-probe":')]
ck("🔴 the fb-record job runs T54",
   "import t54" in _arm and "_t54.run()" in _arm,
   "⛔ Sam's standing rule: nothing that updates the site may depend on "
   "somebody remembering. A pre-registered test checked when convenient "
   "is checked when it is convenient to like the answer")
ck("⚠️ ...and a failure there cannot take the grader down",
   "except Exception" in _arm and "did not run" in _arm,
   "the RECORD is the product; this is a note about a test")
ck("⛔ T54 is a MEASUREMENT, not a gate — only BLOCKED exits non-zero",
   'sys.exit(1 if r["verdict"] == "BLOCKED" else 0)' in src,
   "⚠️ a FAIL is a finding for Sam to act on deliberately and must never "
   "redden a collector run that did its job. BLOCKED is different: it "
   "means the test cannot run AT ALL, which is a defect in this repo")

print("\n═══ 4. 🔴 THE FOUR VERDICTS, DRIVEN ON FIXTURES ═══")
# ⛔ DRIVEN THROUGH THE REAL `run()` against a temp tree. A test that
#    re-implements the arithmetic checks its own sums (rule 202).
import tempfile  # noqa: E402


def _tree(rows):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "data", "ncaaf", "latest")
    os.makedirs(p)
    with gzip.open(os.path.join(p, "record-detail.json.gz"), "wt") as fh:
        json.dump({"days": {"2026-09-11": rows}}, fh)
    return d


def _row(stretch, won, conf=80, side="under"):
    """A row whose stretch is exactly `stretch`."""
    return {"won": won, "confidence": conf, "side": side,
            "line": 10.0 * stretch, "own_mean": 10.0}


# (a) BLOCKED — graded rows exist and none carries own_mean
blocked = [{"won": True, "confidence": 80, "side": "under", "line": 5.0}]
r = t54.run(_tree(blocked), quiet=True)
ck("🔴 BLOCKED when no graded row carries own_mean",
   r["verdict"] == "BLOCKED",
   "⛔ this is the state T54 was actually in for eight days, and it must "
   "never again be reported as 'not yet measurable'. Got %r" % r["verdict"])

# (b) NOT YET MEASURABLE — stretched rows exist but under the minimum
r = t54.run(_tree([_row(3.0, True)] * 5 + [_row(1.1, True)] * 50),
            quiet=True)
ck("⚠️ NOT YET MEASURABLE under the 40-row minimum",
   r["verdict"] == "NOT YET MEASURABLE" and r["stretched_n"] == 5,
   "not a pass and not a fail. Got %r at n=%s"
   % (r["verdict"], r.get("stretched_n")))

# (c) PASS — 40+ stretched rows calibrated no worse than normal
r = t54.run(_tree([_row(3.0, True)] * 32 + [_row(3.0, False)] * 8
                  + [_row(1.1, True)] * 80 + [_row(1.1, False)] * 20),
            quiet=True)
ck("✅ PASS when the stretched gap is inside the 5-point bar",
   r["verdict"] == "PASS",
   "stretched %s vs normal %s, delta %s"
   % (r.get("stretched_gap"), r.get("normal_gap"), r.get("delta")))

# (d) FAIL — 40+ stretched rows calibrated much worse
r = t54.run(_tree([_row(3.0, True)] * 12 + [_row(3.0, False)] * 28
                  + [_row(1.1, True)] * 80 + [_row(1.1, False)] * 20),
            quiet=True)
ck("🔴 FAIL when the stretched gap is worse by more than 5 points",
   r["verdict"] == "FAIL" and "STOP BEING RANKED" in r["why"],
   "⛔ and the verdict must STATE the pre-committed consequence — "
   "stretched rows stop being RANKED, are still SHOWN, and keep their "
   "warning. Got %r" % r["verdict"])

print("\n═══ 5. ⚪ WHERE IT ACTUALLY STANDS TODAY ═══")
live = t54.run(ROOT, quiet=True)
note("graded %d · with own_mean %d · STRETCHED %d/%d · verdict %s"
     % (live["graded_rows"], live["rows_with_own_mean"],
        live["stretched_n"], t54.MIN_STRETCHED, live["verdict"]))
# ⛔ ~~ck("T54 is no longer BLOCKED on the live data")~~ STRUCK THE SAME
#    HOUR IT WAS WRITTEN. It asserted a TRANSIENT state — whether the
#    last `fb-record` run happened to include the fix — and it went RED
#    on correct code the moment the regenerated files were reverted so
#    they would not ship in a drop. ⚠️ On a fresh clone of `main` T54 IS
#    blocked until the next grader run rewrites the detail, and that is
#    CORRECT, not a defect.
# ⛔ RULE 166 FOR THE TENTH TIME ON THIS REPO, caught before upload only
#    because the suite was run against a reverted tree.
# ✅ THE DURABLE QUESTION IS WHETHER THE PIPELINE CARRIES THE FIELD, and
#    that is asked by DRIVING THE GRADER below rather than by reading
#    whatever the last cron left on disk.
note("live verdict is %s — ⚠️ BLOCKED here means only that the stored "
     "record detail predates the fix, and the next fb-record run clears "
     "it. It is NOT asserted, because it is a fact about when the cron "
     "last ran." % live["verdict"])

print("\n═══ 6. 🔴 THE GRADER ITSELF, DRIVEN ═══")
# 🔴 THE ONE ASSERTION THAT CANNOT EXPIRE: hand `grade_card` a pick that
#    carries `own_mean` and check the row it returns still has it.
# ⛔ Not "is the string in the file" — section 2 already asks that, and a
#    field can be in the dict literal and still be dropped downstream.
#    This drives the real function.
import record_fb  # noqa: E402
_card = {"picks": [{"player": "Nobody At All", "market": "player_rush_yds",
                    "side": "under", "line": 40.5, "price": -110,
                    "confidence": 80, "own_mean": 12.5, "book": "hardrockbet",
                    "game": "A @ B", "rank": 1}]}
_rows = record_fb.grade_card(_card, {}, {}, None)
ck("🔴 a graded row carries own_mean through the real grader",
   bool(_rows) and _rows[0].get("own_mean") == 12.5,
   "⛔ THIS IS THE CHECK THAT WOULD HAVE CAUGHT THE ORIGINAL DEFECT. The "
   "published cards carried the field on 339 of 339 picks and the graded "
   "rows on 0 of 200, so T54 could never reach its minimum however many "
   "slates passed. Got: %s"
   % (_rows[0].get("own_mean") if _rows else "no rows"))
ck("⚠️ ...and it survives even when the player cannot be resolved",
   bool(_rows) and _rows[0].get("won") is None
   and _rows[0].get("own_mean") == 12.5,
   "an ungradeable row is still a row, and dropping the predictor from "
   "it would bias the sample toward players whose names happen to join")
note("⛔ THE EARLY NUMBERS ARE PRINTED AND MUST NOT BE ACTED ON. "
     "Stretched sits at n=%d against a minimum of %d, and the "
     "specification says under the minimum it is NOT a pass and NOT a "
     "fail. ⚠️ Reading a lean off five rows is exactly what a "
     "pre-registered minimum exists to stop — including when the lean "
     "points the way you expected."
     % (live["stretched_n"], t54.MIN_STRETCHED))
