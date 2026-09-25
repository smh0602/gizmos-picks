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
# 🔴🔴 AND EVERY 10-POINT BAND IS ASKED ON ITS OWN. `[Sam, 2026-09-24]`
#    The pooled question alone let a band hide behind its neighbours:
#    college's 80-90 band hit 59% against a claimed 85% and its 90-100
#    band 62% against 95% while the POOLED gap read −9.4, "inside the
#    bar". ⚠️ GAP_POINTS and P_MAX are the same borrowed bars. The one new
#    number is the band floor, set 2026-09-24 AFTER seeing the gap and said
#    so: 10 rows, below which a band is not asked. The p is an EXACT
#    one-sided binomial tail, because a band's n is small.
BAND_MIN_N = 10


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


def _binom_low(w, n, p0):
    """Exact P(X <= w) for X ~ Binomial(n, p0).

    ⚠️ IN LOG SPACE. `[2026-09-24]` The direct form multiplied `math.comb(n,
    k)` by a float, and past n ≈ 1,000 the integer is too large to convert:
    the alt-lines check's college bands (n in the thousands) raised
    OverflowError. Same sum, same answer on small n (`test_calibration.py`)."""
    if n <= 0 or not (0.0 < p0 < 1.0):
        return None
    lp, lq, lc = math.log(p0), math.log1p(-p0), math.lgamma(n + 1)
    t = [lc - math.lgamma(k + 1) - math.lgamma(n - k + 1) + k * lp + (n - k) * lq
         for k in range(0, int(w) + 1)]
    m = max(t)
    return min(1.0, math.exp(m) * sum(math.exp(x - m) for x in t))


def band_flags(cal):
    """Every 10-point band asked on its own. -> [{bucket, n, w, stated,
    actual, gap, p, state}] with state UNDER / NOT_MEASURABLE / OK."""
    out = []
    for b in cal or []:
        if not isinstance(b, dict) or not b.get("n") or b.get("stated") is None:
            continue
        n, w, stated = int(b["n"]), int(b.get("w") or 0), float(b["stated"])
        actual = 100.0 * w / n
        row = {"bucket": b.get("bucket"), "n": n, "w": w, "stated": stated,
               "actual": round(actual, 1), "gap": round(actual - stated, 1), "p": None}
        if n < BAND_MIN_N:
            row["state"] = "NOT_MEASURABLE"
        else:
            p = _binom_low(w, n, stated / 100.0)
            row["p"] = p
            row["state"] = ("UNDER" if (actual - stated <= -GAP_POINTS and p is not None
                                        and p < P_MAX) else "OK")
        out.append(row)
    return out


def judge(doc):
    """One league -> a verdict dict. Never raises on a malformed file."""
    if not isinstance(doc, dict):
        return {"state": "UNREADABLE", "why": "record.json is not an object"}
    n, w, stated = pooled(doc.get("calibration"))
    if (not n or stated is None) and any(pooled(v)[0] for v in (doc.get("calibration_by_method") or {}).values()):
        # `[Sam, 2026-09-24]` the card changed how it rates. Its earlier
        # method's record is kept apart; the new one has nothing graded yet.
        # ⛔ NOT A PASS: "not yet measurable" until its own plays are graded.
        return {"state": "NOT_MEASURABLE", "n": 0,
                "why": ("the card's current method (%s) has no graded plays yet; "
                        "its earlier method's record is kept apart"
                        % doc.get("card_method_current"))}
    if not n or stated is None:
        return {"state": "UNREADABLE",
                "why": "no calibration buckets carrying a sample"}
    bands = band_flags(doc.get("calibration"))
    under = [b for b in bands if b["state"] == "UNDER"]
    if under:
        # ⛔ A BAND THIS FAR OFF IS FLAGGED WHATEVER THE POOLED FIGURE SAYS.
        return {"n": n, "w": w, "stated": stated, "actual": 100.0 * w / n,
                "gap": 100.0 * w / n - stated, "z": None, "p": None,
                "built_at": doc.get("built_at"), "bands": bands, "state": "UNDER",
                "why": "; ".join("the %s band claimed %.1f%% and delivered %.1f%% over %d "
                                 "graded rows (%+.1f points, p=%.5f)"
                                 % (b["bucket"], b["stated"], b["actual"], b["n"], b["gap"], b["p"])
                                 for b in under)}
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
        # ⛔ THE STATE NAME IS NOT REPEATED HERE. `[fixed 2026-09-15]`
        #    `render()` already prints "**NOT YET MEASURABLE** — %s", so a
        #    `why` that opened with the same words produced **"NOT YET
        #    MEASURABLE — not yet measurable — 88 graded rows"** in the
        #    live issue body. ⚠️ `why` carries the NUMBERS; the state
        #    carries the verdict.
        out["why"] = ("%d graded rows, under the %d needed to read a rate"
                      % (n, MIN_N))
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
        # ⛔ ~~"— every job is green."~~ STRUCK 2026-09-19. This module
        # reads `record.json` and nothing else; it has never been able to
        # see a workflow run. `[measured]` it printed that sentence into
        # issue #16 while `collect.yml` was red on 68 consecutive runs.
        # Rule 166/293: a number — or a status — written down is a claim
        # about the world, and this one was not measured by the thing
        # making it. ✅ The DISTINCTION it was drawing is real and is
        # kept, said in terms of what this file actually reads.
        out.append("**The board is delivering materially less than it "
                   "claims. This is a MONEY finding: it is about what "
                   "the board DELIVERS against what it printed, not "
                   "about whether anything ran.**\n")
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
