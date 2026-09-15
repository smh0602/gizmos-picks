#!/usr/bin/env python3
"""
IS THE PRODUCT STILL WINNING? NOTHING IN THIS REPO HAS EVER ASKED.

🔴🔴 `[Sam, 2026-09-15: "lets fix this and make them automatic then"]` —
on the gap I reported as **the biggest remaining hole, and the only one
that costs money rather than sleep.**

⛔ THE WATCHDOG CHECKS THE RECORD IS *SANE*, NEVER THAT IT IS *GOOD*. It
asks whether the percentage is 0–100 and whether grading is still
happening. **It would have said "healthy" every hour while the NFL board
delivered 48% against a stated 64.5% on 100 graded rows.** That is not a
pipeline failure — every job was green, every artifact fresh — which is
precisely why nothing saw it.

➡️ FOUR WATCHERS NOW, FOUR QUESTIONS:

    watchdog.py      is the PRODUCT right?         (reads repo files)
    collect.yml      did the TEST STEP fail?
    runs_report.py   did any RUN fail, did a cron land?
    this file        are the PICKS WINNING?

══════════════════════════════════════════════════════════════════════
⛔ FOOTBALL ONLY. MLB IS NEVER READ HERE.

`[Sam, 2026-09-12: "we have mlb perfected we dont need to touch it"]` —
and the freeze names **"no scheduled checks that read MLB state."** A
daily job that reads `data/latest/record.json` would be exactly that, so
`LEAGUES` is `nfl` and `ncaaf` and there is no MLB path to disable later.

══════════════════════════════════════════════════════════════════════
🔴🔴 THIS IS A MONITOR. IT IS **NOT** AN ANSWER TO T58.

⛔ T58 is the PRE-REGISTERED test of the NFL over/under asymmetry, and its
bar was fixed before any data: ≤ −15 points AND p<0.01 on ≥120 FRESH rows
across ≥3 distinct NFL weeks, VOID if CFB develops the same gap. **Nothing
in this file may be read as passing, failing or pre-empting it**, and
tripping here changes nothing about the card.

⚠️ AND THE BAR HERE WAS SET *AFTER* SEEING TODAY'S NUMBERS — stated
plainly rather than dressed up as pre-registration. It is defensible
because it is **borrowed, not invented**: the ≥15 points and p<0.01 come
from T58, and the n≥100 minimum from T37's pooled form. ⛔ What that buys
is that the threshold was not tuned to make today trip; what it costs is
that this is a monitor's bar, not a test's, and it is labelled that way.

══════════════════════════════════════════════════════════════════════
⚠️ IT ALARMS ONLY ON UNDER-PERFORMANCE, AND THAT IS DELIBERATE.

A board that beats its stated confidence is also miscalibrated, and it is
worth a NOTE — but it is not the failure Sam loses money to. An alarm that
fires on good news is an alarm that gets filtered (rule 238).
"""
import datetime
import json
import math
import os
import sys

# ⛔ NEVER `mlb`. See the header — the freeze forbids a scheduled check
#    that reads MLB state, and the absence of the path is the guard.
LEAGUES = ("nfl", "ncaaf")

# 🔴 A PERCENTAGE ON A THIN SAMPLE IS NOT A RATE. `[T37's lesson: build
#    #183 failed on 1 contradiction out of 4 rows]` Under this it reports
#    NOT YET MEASURABLE — not a pass, and not a fail.
MIN_N = 100
# ⛔ BORROWED FROM T58, NOT INVENTED HERE. Both numbers were fixed for
#    that test before any data existed.
GAP_POINTS = 15.0
P_MAX = 0.01


def _two_sided_p(w, n, p0):
    """Normal approximation to the binomial, two-sided."""
    if n <= 0 or not (0.0 < p0 < 1.0):
        return None
    se = math.sqrt(p0 * (1.0 - p0) / n)
    if se == 0:
        return None
    z = (float(w) / n - p0) / se
    return z, math.erfc(abs(z) / math.sqrt(2.0))


def pooled(cal):
    """(n, wins, stated%) pooled across the calibration buckets.

    ⚠️ THE DENOMINATOR IS THE CALIBRATION BLOCK, NOT `overall`. Measured
    2026-09-15: ncaaf `overall` counts 97 rows while its buckets hold 88,
    because a row with no confidence has no bucket. **Comparing a stated
    average from one denominator against an actual from another is the
    shape that produces a number nobody can reproduce.**
    """
    rows = [b for b in (cal or []) if (b or {}).get("n")]
    n = sum(b["n"] for b in rows)
    w = sum(b.get("w") or 0 for b in rows)
    if not n:
        return 0, 0, None
    stated = sum((b.get("stated") or 0.0) * b["n"] for b in rows) / n
    return n, w, stated


def judge(doc):
    """One league -> a verdict dict. Never raises on a malformed file."""
    if not isinstance(doc, dict):
        return {"state": "UNREADABLE", "why": "record.json is not an object"}
    n, w, stated = pooled(doc.get("calibration"))
    if not n or stated is None:
        return {"state": "UNREADABLE",
                "why": "no calibration buckets carrying a sample"}
    actual = 100.0 * w / n
    gap = actual - stated
    zp = _two_sided_p(w, n, stated / 100.0)
    z, p = zp if zp else (None, None)
    out = {"n": n, "w": w, "stated": stated, "actual": actual,
           "gap": gap, "z": z, "p": p,
           "built_at": doc.get("built_at")}
    # ⛔ THE SAMPLE GATE COMES FIRST. A 40-point gap on 6 rows is noise
    #    wearing a finding's clothes.
    if n < MIN_N:
        out["state"] = "NOT_MEASURABLE"
        out["why"] = ("not yet measurable — %d graded rows, under the %d "
                      "needed to read a rate" % (n, MIN_N))
        return out
    if gap <= -GAP_POINTS and p is not None and p < P_MAX:
        out["state"] = "UNDER"
        out["why"] = ("stated %.1f%%, delivered %.1f%% over %d rows "
                      "(%+.1f points, p=%.5f)" % (stated, actual, n, gap, p))
        return out
    # ⚠️ Over-performance is reported, never alarmed. See the header.
    if gap >= GAP_POINTS and p is not None and p < P_MAX:
        out["state"] = "OVER"
        out["why"] = ("stated %.1f%%, delivered %.1f%% over %d rows "
                      "(%+.1f points) — better than claimed, which is "
                      "still miscalibrated" % (stated, actual, n, gap))
        return out
    out["state"] = "OK"
    out["why"] = ("stated %.1f%%, delivered %.1f%% over %d rows (%+.1f "
                  "points) — inside the bar" % (stated, actual, n, gap))
    return out


def read_all(root="."):
    out = {}
    for lg in LEAGUES:
        p = os.path.join(root, "data", lg, "latest", "record.json")
        try:
            doc = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError) as e:
            out[lg] = {"state": "UNREADABLE", "why": "%s: %s" % (p, e)}
            continue
        out[lg] = judge(doc)
    return out


def render(res):
    bad = [lg for lg, r in res.items() if r["state"] == "UNDER"]
    out = []
    if bad:
        out.append("**The board is delivering materially less than it "
                   "claims. This is a MONEY finding, not a pipeline "
                   "one — every job is green.**\n")
        for lg in bad:
            r = res[lg]
            out.append("- **`%s`** — %s" % (lg, r["why"]))
        out.append("")
    for lg, r in sorted(res.items()):
        if r["state"] in ("OVER", "UNREADABLE"):
            out.append("- `%s` — **%s**: %s" % (lg, r["state"], r["why"]))
    out.append("")
    out.append("⛔ **THIS IS NOT T58.** T58 is the pre-registered test of "
               "the NFL over/under asymmetry, with its own bar fixed "
               "before any data (≥120 fresh rows, ≥3 distinct NFL weeks). "
               "Nothing here passes, fails or pre-empts it, and no card "
               "changes because this fired.")
    out.append("")
    out.append("⛔ **Do not fix this by changing the bar.** Read "
               "`CLAUDE.md`. A check may only change when it asks the "
               "WRONG QUESTION, and the replacement must be harder to "
               "pass.")
    out.append("")
    out.append("_One issue, updated in place, closed by itself when every "
               "league is back inside the bar. Football only — MLB is "
               "frozen and is never read here._")
    for lg, r in sorted(res.items()):
        if r["state"] == "NOT_MEASURABLE":
            out.append("")
            out.append("⚠️ `%s` is **NOT YET MEASURABLE** — %s. Not a pass "
                       "and not a fail." % (lg, r["why"]))
    return "\n".join(out)


def main():
    res = read_all()
    if any(r["state"] == "UNREADABLE" for r in res.values()):
        # ⛔ "I COULD NOT LOOK" IS NOT "THE PICKS ARE FINE".
        sys.stderr.write("could not read a record: %s\n"
                         % {k: v.get("why") for k, v in res.items()
                            if v["state"] == "UNREADABLE"})
        print(render(res))
        return 2
    if not any(r["state"] in ("UNDER", "OVER") for r in res.values()):
        print("OK  " + "  ".join(
            "%s=%s(%s)" % (lg, r["state"], r.get("n", 0))
            for lg, r in sorted(res.items())))
        return 0
    print(render(res))
    return 1


if __name__ == "__main__":
    sys.exit(main())
