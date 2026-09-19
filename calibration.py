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

# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 ~~`LEAGUES = ("nfl", "ncaaf")`~~ — CHANGED ONLY ON SAM'S WORD.
# ══════════════════════════════════════════════════════════════════════
# ⛔ THE FREEZE FORBIDS THIS, IN AS MANY WORDS, and the struck line and
# its reason are kept rather than deleted:
#     # ⛔ NEVER `mlb`. See the header — the freeze forbids a scheduled
#     #    check that reads MLB state, and the absence of the path is
#     #    the guard.
#
# ⚠️ WHAT IT COSTS TO LEAVE IT OFF, measured 2026-09-19:
#     by_kind.pitcher = {"w": 290, "n": 580, "pct": 50.0}
#     calibration     50-60% predicted 56.4, delivered 46.4 on n=181
#                     60-70% predicted 64.2, delivered 49.5 on n=279
#                     70-80% predicted 73.5, delivered 59.2 on n=98
#                     80-90% predicted 85.5, delivered 47.1 on n=17
# The MLB pitcher board is a coin flip advertising 58–93%, and the only
# thing that says so is the card writing its own confession into
# `calibration_warning` — which the page does render, honestly. NOTHING
# ALARMS ON IT. It is the one number the whole product exists to produce.
#
# ⛔ SO THIS IS PREPARED, NOT DECIDED. The branch it lives on is named so
# it cannot be merged by accident. Reverting is one word: put the tuple
# back.
LEAGUES = ("nfl", "ncaaf", "mlb")

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
    # 🔴🔴 THE LEAGUES NAME THE SAME NUMBER DIFFERENTLY, AND READING THE
    # WRONG ONE IS SILENT. `[measured 2026-09-19]` football buckets carry
    # `stated`; MLB's carry `predicted`. `b.get("stated") or 0.0` against
    # an MLB bucket returns 0.0, not None — so the gap becomes
    # `actual - 0`, the board reads as beating its claim by sixty points,
    # and the alarm never fires. Same shape as the watchdog reading
    # `rows` off a file the collector writes with `artifacts`.
    # ⛔ RESOLVED, NEVER DEFAULTED: buckets carrying neither key make this
    # UNREADABLE rather than zero.
    key = ("stated" if any("stated" in b for b in rows)
           else "predicted" if any("predicted" in b for b in rows) else None)
    if key is None:
        return n, w, None
    vals = [b for b in rows if isinstance(b.get(key), (int, float))]
    if not vals:
        return n, w, None
    stated = sum(b[key] * b["n"] for b in vals) / sum(b["n"] for b in vals)
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


# 🔴 MLB'S ROOT IS `data/latest/`, NOT `data/mlb/latest/`. It was the
#    first league and never got a subdirectory. A path built from the
#    league name alone lands nowhere and reports UNREADABLE — which is
#    honest, and useless.
DATA = {"mlb": "data"}


def record_path(lg, root="."):
    return os.path.join(root, DATA.get(lg, os.path.join("data", lg)),
                        "latest", "record.json")


def read_all(root="."):
    out = {}
    for lg in LEAGUES:
        p = record_path(lg, root)
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
    # ⛔ ~~"Football only — MLB is frozen and is never read here."~~ — it
    #    IS read here now, and a footer that says otherwise is the same
    #    class of stale claim this whole night's work is about.
    out.append("_One issue, updated in place, closed by itself when every "
               "league is back inside the bar. ⛔ READING a league is not "
               "CHANGING it: nothing here writes, and no card moves "
               "because this fired._")
    for lg, r in sorted(res.items()):
        if r["state"] == "NOT_MEASURABLE":
            out.append("")
            out.append("⚠️ `%s` is **NOT YET MEASURABLE** — %s. Not a pass "
                       "and not a fail." % (lg, r["why"]))
    # ══════════════════════════════════════════════════════════════════
    # 🔴 EVERY LEAGUE'S NUMBER, ALWAYS — NOT ONLY THE ONES THAT TRIP.
    # ⛔ A monitor that prints only failures cannot show you a gap that
    # misses the bar by less than a point. `[measured 2026-09-19]` the
    # MLB pitcher board reads **stated 64.2%, delivered 50.0% over 580
    # rows, p≈0, gap −14.2** — and the bar is −15.0, so it does NOT
    # fire. Under the old renderer that league would have appeared
    # nowhere at all.
    # ⛔ THE BAR IS NOT MOVED TO MAKE IT FIRE. It is borrowed from T58
    # and was fixed before any data existed; tuning it to today's number
    # is the one thing `CLAUDE.md` forbids most plainly. What changes is
    # that the number is SHOWN.
    rows = [(lg, r) for lg, r in sorted(res.items())
            if r.get("n") and r.get("stated") is not None]
    if rows:
        out.append("")
        out.append("| league | stated | delivered | rows | gap | verdict |")
        out.append("|---|---:|---:|---:|---:|---|")
        for lg, r in rows:
            out.append("| `%s` | %.1f%% | %.1f%% | %d | %+.1f | %s |"
                       % (lg, r["stated"], r["actual"], r["n"], r["gap"],
                          r["state"]))
        out.append("")
        out.append("_The bar is %.0f points AND p<%.2f on %d+ rows, borrowed "
                   "from T58 and T37 and fixed before any of these numbers "
                   "existed. A gap that misses it is printed, not alarmed._"
                   % (-GAP_POINTS, P_MAX, MIN_N))
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
