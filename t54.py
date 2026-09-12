#!/usr/bin/env python3
"""
T54 — SHOULD A RECORD AGAINST A LINE THE PLAYER NEVER FACED BE *RANKED*?

🔒 THE SPECIFICATION WAS FIXED ON 2026-09-04, BEFORE ANY CUTOFF WAS TRIED,
and is reproduced here VERBATIM FROM `claude/owed-tests.md` so that
running it cannot quietly become re-choosing it:

  Population  every published football pick carrying `confidence` and
              `own_mean`, both leagues, graded W/L by the normal record
              path. Voids excluded from every denominator.
  The split   stretch = line / own_mean (and its RECIPROCAL for OVER
              rows, so the measure is symmetric).
              STRETCHED = stretch >= 2.0 ; NORMAL = everything else.
              ⚠️ The 2.0 is INHERITED from the sentence threshold already
              shipped — it is NOT re-chosen here.
  Metric      hit rate minus mean stated confidence — the CALIBRATION
              GAP — computed separately for STRETCHED and NORMAL.
  Minimum     40 graded STRETCHED rows. Under that: NOT YET MEASURABLE,
              not a pass and not a fail.
  PASS        the STRETCHED gap is no worse than the NORMAL gap by more
              than 5 percentage points.
  FAIL        worse by more than 5 points -> stretched rows stop being
              RANKED. They are still SHOWN, still labelled, still
              carrying their warning.
  ⛔ ONE SPECIFICATION. NO SWEEP over the cutoff, the metric or the
     position.

════════════════════════════════════════════════════════════════════════
🔴 WHY THIS FILE EXISTS AT ALL, AND IT IS NOT "TO RUN THE TEST"
════════════════════════════════════════════════════════════════════════

`[measured 2026-09-12]` T54 had been open for EIGHT DAYS and its sample
was **structurally stuck at zero**:

    published football picks carrying own_mean    339 of 339
    GRADED rows carrying own_mean                   0 of 200

`record_fb.py` built its graded rows without the field, so **the
predictor T54 splits on was discarded at grading time.**

⛔ THAT IS NOT "NOT YET MEASURABLE FOR LACK OF SAMPLE." It is a test that
could never have become measurable, sitting open and reporting a
shortfall whose cause was in the grader rather than in the slate. ⚠️ An
owed test that cannot accumulate is worse than one nobody opened, because
it looks like it is waiting.

➡️ SO THE POINT OF THIS FILE IS THAT THE COUNT IS PRINTED EVERY RUN. A
pre-registered test that depends on somebody remembering to check it is a
test that gets checked when it is convenient — which is the same failure
as choosing the cutoff after seeing the data, one step earlier.
"""
import glob
import gzip
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

STRETCH_CUTOFF = 2.0      # ⛔ INHERITED from the shipped sentence. Not tuned.
MIN_STRETCHED = 40        # ⛔ Fixed 2026-09-04. Not negotiable downward.
GAP_TOLERANCE = 5.0       # percentage points


def stretch_of(row):
    """`line / own_mean`, reciprocal on an OVER so the measure is symmetric.

    ⚠️ SYMMETRIC BY SPECIFICATION, not by preference. An UNDER is stretched
    when the line sits far ABOVE what the player does; an OVER is stretched
    when it sits far BELOW. One ratio cannot express both, so the spec
    names the reciprocal and this reproduces it.
    ⛔ Returns None rather than guessing when the mean is zero or missing —
    a player with a zero mean is not infinitely stretched, he is
    unmeasurable on this axis, and dropping him is the honest answer.
    """
    m, line = row.get("own_mean"), row.get("line")
    if m is None or line is None:
        return None
    try:
        m, line = float(m), float(line)
    except (TypeError, ValueError):
        return None
    if m <= 0 or line <= 0:
        return None
    s = line / m
    if row.get("side") == "over":
        s = 1.0 / s if s else None
    return s


def collect(root=ROOT):
    """Every GRADED row from both leagues' record detail.

    ⛔ GRADED, not published. `won is None` means void, unresolved or an
    ungradeable market, and the specification excludes those from every
    denominator.
    """
    out = []
    for p in sorted(glob.glob(os.path.join(root, "data", "*", "latest",
                                           "record-detail.json.gz"))):
        lg = p.split(os.sep)[-3]
        try:
            d = json.load(gzip.open(p, "rt"))
        except Exception as e:
            print("  ⚠️ unreadable %s: %s" % (p, e))
            continue
        for day, rows in (d.get("days") or {}).items():
            for r in rows:
                if r.get("won") is None:
                    continue
                if r.get("confidence") is None:
                    continue
                out.append(dict(r, _league=lg, _day=day))
    return out


def gap(rows):
    """Hit rate minus mean stated confidence, in percentage points."""
    if not rows:
        return None, 0
    hit = 100.0 * sum(1 for r in rows if r["won"]) / len(rows)
    conf = sum(float(r["confidence"]) for r in rows) / len(rows)
    return hit - conf, len(rows)


def run(root=ROOT, quiet=False):
    rows = collect(root)
    with_mean = [r for r in rows if stretch_of(r) is not None]
    stretched = [r for r in with_mean if stretch_of(r) >= STRETCH_CUTOFF]
    normal = [r for r in with_mean if stretch_of(r) < STRETCH_CUTOFF]

    s_gap, s_n = gap(stretched)
    n_gap, n_n = gap(normal)

    rep = {
        "test": "T54", "kind": "OWED TEST",
        "spec_fixed": "2026-09-04",
        "cutoff": STRETCH_CUTOFF, "min_stretched": MIN_STRETCHED,
        "graded_rows": len(rows),
        "rows_with_own_mean": len(with_mean),
        "stretched_n": s_n, "normal_n": n_n,
        "stretched_gap": None if s_gap is None else round(s_gap, 2),
        "normal_gap": None if n_gap is None else round(n_gap, 2),
    }

    # 🔴 THE MISSING-INPUT CASE IS ITS OWN VERDICT, AND IT IS NOT
    #    "NOT YET MEASURABLE". Those are different states with different
    #    causes and different fixes, and collapsing them is how this test
    #    sat open for eight days looking like it was merely waiting.
    if rows and not with_mean:
        rep["verdict"] = "BLOCKED"
        rep["why"] = ("%d graded rows carry NO own_mean, so the split "
                      "cannot be computed at all. ⛔ This is a GRADER "
                      "defect, not a thin slate — the published cards "
                      "carry the field and record_fb.py must carry it "
                      "through." % len(rows))
    elif s_n < MIN_STRETCHED:
        rep["verdict"] = "NOT YET MEASURABLE"
        rep["why"] = ("%d graded stretched rows of the %d required. "
                      "⚠️ Not a pass and not a fail. Stretched rows are "
                      "~7%% of a card, so this is months of slates."
                      % (s_n, MIN_STRETCHED))
    else:
        delta = s_gap - n_gap
        rep["delta"] = round(delta, 2)
        if delta >= -GAP_TOLERANCE:
            rep["verdict"] = "PASS"
            rep["why"] = ("stretched calibration gap %.1f vs normal %.1f "
                          "— %.1f points, inside the %.0f-point bar. "
                          "Stretched rows keep their ranking and NOTHING "
                          "CHANGES." % (s_gap, n_gap, delta, GAP_TOLERANCE))
        else:
            rep["verdict"] = "FAIL"
            rep["why"] = ("stretched calibration gap %.1f vs normal %.1f "
                          "— %.1f points, worse than the %.0f-point bar. "
                          "⛔ THE PRE-COMMITTED CONSEQUENCE: stretched "
                          "rows STOP BEING RANKED. They are still shown, "
                          "still labelled, still carrying their warning."
                          % (s_gap, n_gap, delta, GAP_TOLERANCE))

    if not quiet:
        print("═══ T54 — should a record against a line the player never "
              "faced be RANKED? ═══")
        print("  spec fixed %s · cutoff %.1f · minimum %d stretched rows"
              % (rep["spec_fixed"], STRETCH_CUTOFF, MIN_STRETCHED))
        print("  graded rows          %d" % rep["graded_rows"])
        print("  ...carrying own_mean %d" % rep["rows_with_own_mean"])
        print("  STRETCHED  n=%-4d gap %s"
              % (s_n, "—" if s_gap is None else "%+.1f pts" % s_gap))
        print("  NORMAL     n=%-4d gap %s"
              % (n_n, "—" if n_gap is None else "%+.1f pts" % n_gap))
        print("  VERDICT: %s" % rep["verdict"])
        print("  %s" % rep["why"])
        print("  ⛔ ONE SPECIFICATION. No sweep over the cutoff, the "
              "metric or the position — re-choosing any of them after "
              "seeing this output is the failure the pre-registration "
              "exists to prevent.")
    return rep


if __name__ == "__main__":
    r = run()
    out = os.path.join(ROOT, "data", "t54.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(r, open(out, "w", encoding="utf-8"), indent=1)
    # ⛔ EXIT 0 ON EVERY VERDICT INCLUDING FAIL. This is a MEASUREMENT, not
    #    a gate: a failing owed test is a finding to act on deliberately,
    #    not a reason to redden a collector run that did its job.
    #    ⚠️ BLOCKED is the one exception and it exits 1, because BLOCKED
    #    means the test cannot run at all — that IS a defect in this repo,
    #    and it is exactly the state that went unnoticed for eight days.
    sys.exit(1 if r["verdict"] == "BLOCKED" else 0)
