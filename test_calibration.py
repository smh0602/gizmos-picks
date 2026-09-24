#!/usr/bin/env python3
"""
THE WATCHER THAT ASKS WHETHER THE PICKS ARE WINNING MUST NOT CRY WOLF.

🔴🔴 `[Sam, 2026-09-15: "lets fix this and make them automatic then"]`

⛔ THIS IS THE ONE THAT REPORTS A MONEY PROBLEM, so both failure modes
are worse here than anywhere else:

  A MISS         Sam keeps betting a board that stopped working.
  A FALSE ALARM  He stops trusting the only thing that would tell him.

⚠️ AND IT SITS NEXT TO A PRE-REGISTERED TEST IT MUST NOT BECOME. T58 owns
the NFL over/under asymmetry, with a bar fixed before any data. **A
monitor that quietly answered T58 would destroy the test**, because the
whole value of pre-registration is that the bar was chosen blind.

# @vacuity a band far below its claim is flagged even when the pooled figure is fine
#   file: calibration.py
#   find:     if under:
#   with:     if False:
#
# @vacuity a band under its floor of rows is not asked
#   file: calibration.py
#   find:         if n < BAND_MIN_N:
#   with:         if n < 1:
#
# @vacuity the card's banner opens with the warning when a band is flagged
#   file: card_fb.py
#   find:     return (alarm + "; ".join(parts) + "."
#   with:     return ("; ".join(parts) + "."
"""
import json
import math
import os
import sys

from tcheck import ck, note

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calibration as C  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))


def bucket(stated, w, n):
    return {"bucket": "x", "stated": stated, "w": w, "n": n, "pct": 0}


def doc(buckets):
    return {"built_at": "2026-09-15T00:00:00Z", "calibration": buckets}


print("═══ 1. 🔴🔴 MLB IS NEVER READ HERE ═══")
# ⛔ Sam's freeze names "no scheduled checks that read MLB state". The
#    guard is the ABSENCE of a path, not a flag somebody can flip back.
ck("🔴 the league list is football only",
   tuple(C.LEAGUES) == ("nfl", "ncaaf"),
   "⛔ a daily job reading data/latest/record.json is exactly the "
   "'scheduled check that reads MLB state' the freeze forbids. Got %s"
   % (C.LEAGUES,))
_src = open(os.path.join(ROOT, "calibration.py"), encoding="utf-8").read()
ck("⛔ ...and no MLB path exists anywhere in the file",
   '"mlb"' not in _src and "'mlb'" not in _src,
   "🔴 a disabled MLB branch is one edit away from being a live one. The "
   "absence is the guard")
_wf = open(os.path.join(ROOT, ".github/workflows/calibration.yml"),
           encoding="utf-8").read()
ck("⛔ ...and the workflow does not reach into MLB either",
   "data/latest" not in _wf,
   "🔴 the freeze covers the workflow as much as the script")

print("\n═══ 2. ⛔ A PERCENTAGE ON A THIN SAMPLE IS NOT A RATE ═══")
# 🔴 T37's lesson: build #183 failed on ONE contradiction out of FOUR
#    priced rows. A 40-point gap on 6 rows is noise wearing a finding's
#    clothes, and alarming on it is how this channel gets muted.
_thin = C.judge(doc([bucket(90.0, 1, 6)]))
ck("🔴🔴 a huge gap on a TINY sample does NOT alarm",
   _thin["state"] == "NOT_MEASURABLE",
   "⛔ stated 90%%, delivered 16.7%%, n=6 — a 73-point gap, and still "
   "not a rate. Got %s" % _thin["state"])
# 🔴 ~~`"measurable" in _thin["why"]`~~ REPLACED 2026-09-15 WITH A
#    STRICTLY HARDER QUESTION. The old form asked only whether the word
#    appeared SOMEWHERE in `why` — which passed on the live body that
#    read **"NOT YET MEASURABLE — not yet measurable — 88 graded rows"**,
#    because `render()` prints the state name and `why` repeated it.
# ✅ So ask it of the RENDERED BODY, which is the thing Sam reads, and
#    require the verdict ONCE and the numbers present. ⛔ Not a
#    relaxation: this fails on the duplicated text the old check allowed,
#    and it still fails if the thin case is ever reported as OK.
_thin_body = C.render({"ncaaf": _thin})
ck("✅ ...and the BODY says NOT YET MEASURABLE exactly once, with its numbers",
   _thin["state"] == "NOT_MEASURABLE"
   and _thin_body.lower().count("not yet measurable") == 1
   and "6 graded rows" in _thin_body,
   "🔴 'not a pass and not a fail' is the honest third answer; calling "
   "it OK would be a false all-clear — and saying it twice in one "
   "sentence is how a careful body starts reading like a generated one. "
   "Got %d occurrence(s)" % _thin_body.lower().count("not yet measurable"))
ck("⚠️ the minimum is T37's, not invented here",
   C.MIN_N == 100,
   "⛔ a bar chosen to make today's data behave is not a bar. 100 is the "
   "pooled minimum T37 already uses. Got %d" % C.MIN_N)

print("\n═══ 3. 🔴🔴 THE ALARM, DRIVEN BOTH WAYS ═══")
# ⛔ n=200 at a stated 65% delivering 45% — a 20-point gap on a real
#    sample, which is the shape that costs money.
_bad = C.judge(doc([bucket(65.0, 90, 200)]))
ck("🔴🔴 a real gap on a real sample ALARMS",
   _bad["state"] == "UNDER",
   "⛔ stated 65%%, delivered 45%%, n=200. If this is silent the whole "
   "file is decorative. Got %s" % _bad["state"])
ck("✅ ...and the message carries the numbers, not an adjective",
   all(s in _bad["why"] for s in ("65.0", "45.0", "200")),
   "🔴 'calibration is off' tells Sam nothing he can act on")
# ✅ AND THE OTHER DIRECTION — a board performing as claimed is SILENT.
_ok = C.judge(doc([bucket(60.0, 122, 200)]))
ck("✅ a board delivering what it claims is SILENT",
   _ok["state"] == "OK",
   "⛔ a guard that fires on correct behaviour is the other failure, not "
   "a safe one — CLAUDE.md. stated 60%%, delivered 61%%, n=200. Got %s"
   % _ok["state"])
# ⚠️ A BIG GAP THAT IS NOT SIGNIFICANT MUST ALSO STAY SILENT.
_noisy = C.judge(doc([bucket(50.0, 42, 100)]))
ck("⚠️ a gap inside the noise does not alarm",
   _noisy["state"] == "OK",
   "🔴 8 points on n=100 is p≈0.11 — real sampling variation, and "
   "alarming on it teaches Sam to ignore the channel. Got %s (%s)"
   % (_noisy["state"], _noisy["why"]))

# 🔴🔴 STATISTICALLY CERTAIN BUT PRACTICALLY SMALL — THE CASE A BIG
#    SAMPLE MAKES COMMON. stated 60%, delivered 55%, n=1000: p=0.0014, so
#    the gap is REAL, and it is five points. ⛔ Alarming on it would fire
#    every week on a board that is working, which is exactly how this
#    channel gets muted (rule 238).
# ✅ THIS IS WHAT `GAP_POINTS` IS FOR, and it is the only one of the two
#    thresholds that can be driven — see the note below on `P_MAX`.
_small = C.judge(doc([bucket(60.0, 550, 1000)]))
ck("🔴🔴 a REAL but SMALL gap on a huge sample stays silent",
   _small["state"] == "OK",
   "⛔ p=0.0014 makes this certain, and five points is not a product "
   "failure. A bar of 'statistically significant' alone would alarm "
   "weekly on a working board. Got %s (%s)"
   % (_small["state"], _small["why"]))
note("⚠️ `P_MAX` IS ASSERTED AS A CONSTANT AND NOT DRIVEN, AND THAT IS "
     "STATED RATHER THAN HIDDEN: at n≥100 a 15-point gap is already "
     "~3 standard errors, so the two thresholds are nearly collinear "
     "and no fixture separates them. ➡️ It is belt-and-braces for the "
     "day a bigger sample makes a small gap significant — which the "
     "check above is the real defence against.")

print("\n═══ 4. ⚠️ GOOD NEWS IS A NOTE, NEVER AN ALARM ═══")
_over = C.judge(doc([bucket(50.0, 150, 200)]))
ck("⚠️ over-performing is reported as OVER, not UNDER",
   _over["state"] == "OVER",
   "⛔ a board beating its stated confidence is still miscalibrated and "
   "worth knowing — but it is not what Sam loses money to. Got %s"
   % _over["state"])
ck("⛔ ...and the alarming state is reserved for losing",
   _bad["state"] == "UNDER" and _over["state"] != "UNDER",
   "🔴 rule 238 — an alarm that fires on good news is an alarm that "
   "gets filtered")

print("\n═══ 5. 🔴 THE DENOMINATOR IS THE ONE IT MEASURES ═══")
# ⚠️ Measured 2026-09-15: ncaaf `overall` counts 97 rows while its
#    calibration buckets hold 88, because a row with no confidence has no
#    bucket. Taking `stated` from one denominator and `actual` from the
#    other produces a number nobody can reproduce.
_n, _w, _st = C.pooled([bucket(80.0, 8, 10), bucket(40.0, 4, 10)])
ck("🔴 stated is weighted by each bucket's own n",
   abs(_st - 60.0) < 1e-9 and _n == 20 and _w == 12,
   "⛔ an unweighted mean of bucket labels is not the board's stated "
   "confidence. Got n=%s w=%s stated=%s" % (_n, _w, _st))
ck("⛔ an empty calibration block is UNREADABLE, not OK",
   C.judge(doc([]))["state"] == "UNREADABLE"
   and C.judge({})["state"] == "UNREADABLE",
   "🔴 THE MOST DANGEROUS OUTPUT IN THIS REPO IS A FALSE ALL-CLEAR. A "
   "missing record must never read as a passing one")
ck("⛔ ...and a malformed file does not crash the watcher",
   C.judge(None)["state"] == "UNREADABLE"
   and C.judge({"calibration": [None, {}]})["state"] == "UNREADABLE",
   "🔴 a watcher that dies before it looks reports nothing, which is "
   "indistinguishable from all-clear")

print("\n═══ 6. ⛔ IT MUST NOT BECOME T58 ═══")
# 🔴 T58 is PRE-REGISTERED and its whole value is that the bar was
#    chosen blind. A monitor that quietly answered it would destroy it.
ck("🔴🔴 the body says in words that this is not T58",
   "T58" in C.render({"nfl": _bad}) and
   "pre-registered" in C.render({"nfl": _bad}),
   "⛔ someone reading this issue must not conclude the owed test has "
   "been answered. Nothing here passes, fails or pre-empts it")
ck("⚠️ ...and the bar is borrowed from T58 rather than invented",
   C.GAP_POINTS == 15.0 and C.P_MAX == 0.01,
   "⛔ THE BAR WAS SET AFTER SEEING TODAY'S NUMBERS, which is stated "
   "plainly in the header. It is defensible only because both values "
   "were fixed for T58 before any data existed — so the threshold was "
   "not tuned to make today trip. Got gap=%s p=%s"
   % (C.GAP_POINTS, C.P_MAX))
ck("⛔ the source says so too, where a future editor will see it",
   "NOT** AN ANSWER TO T58" in _src or "NOT AN ANSWER TO T58" in _src,
   "🔴 a constraint that lives only in a test is a constraint the "
   "person editing the script never reads")

print("\n═══ 7. ⛔ 'I COULD NOT LOOK' IS NOT 'THE PICKS ARE FINE' ═══")
ck("🔴 an unreadable record exits 2, not 0",
   "return 2" in _src,
   "⛔ if a parse failure exited 0 the workflow would CLOSE an open "
   "issue on the strength of not having looked")
ck("⛔ ...and the workflow leaves an open issue alone on `unknown`",
   "leaving any open issue alone" in _wf,
   "🔴 closing a money alert because the check broke is how a real "
   "problem goes quiet")
ck("⚠️ it is its own workflow, daily, off :00",
   "name: calibration" in _wf and "cron: \"52 12 * * *\"" in _wf,
   "⛔ a calibration gap moves over WEEKS; hourly would be 24 identical "
   "answers a day. And :00 slots get dropped by GitHub's scheduler")

print("\n═══ 8. 📋 WHAT IT SAYS ABOUT THE LIVE BOARD RIGHT NOW ═══")
_live = C.read_all(ROOT)
for _lg, _r in sorted(_live.items()):
    note("%s — %s: %s" % (_lg, _r["state"], _r["why"]))
ck("⚠️ the live records are readable at all",
   all(r["state"] != "UNREADABLE" for r in _live.values()),
   "⛔ this check is what stops section 8 from being a decorative "
   "print. Got %s" % {k: v["state"] for k, v in _live.items()})

note("⛔ WHAT THIS DOES NOT CLAIM: that a green run means the picks are "
     "good, or that an alarm means the model is wrong. It claims the "
     "board delivered materially less than it stated, on enough rows to "
     "read, and that a human should look. ➡️ Four watchers, four "
     "questions, and none of them replaces another.")

# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 EVERY 10-POINT BAND ON ITS OWN  `[Sam, 2026-09-24]`
# ══════════════════════════════════════════════════════════════════════
# The live miss: college's 80-90 band delivered 59% against 85% and its
# 90-100 band 62% against 95%, and the POOLED gap read -9.4, "inside the
# bar". Here a low band over-delivers and hides a high band that fails.
_hidden = C.judge(doc([bucket(40.0, 60, 100), bucket(85.0, 12, 25)]))
ck("🔴🔴 a band far below its claim is flagged even when the POOLED figure looks fine",
   _hidden["state"] == "UNDER" and "85.0%" in _hidden["why"],
   "pooled here is +8.6 points; the 85%% band delivered 48%%. got %r" % (_hidden,))
_floor = C.judge(doc([bucket(40.0, 60, 100), bucket(90.0, 1, 9)]))
ck("⚠️ ...but a band under its floor of %d rows is not asked" % C.BAND_MIN_N,
   _floor["state"] != "UNDER",
   "a 1-of-9 band is noise wearing a finding's clothes. got %r" % _floor.get("state"))
_near = C.judge(doc([bucket(40.0, 60, 100), bucket(85.0, 19, 25)]))
ck("✅ ...and a band within 15 points of its claim is not flagged",
   _near["state"] != "UNDER", "76%% against 85%% is inside the bar. got %r" % _near.get("state"))

import card_fb as _CF  # noqa: E402
_flags = [b for b in C.band_flags([bucket(85.0, 12, 25)]) if b["state"] == "UNDER"]
_ban = _CF.calibration_sentence_fb({"80-plus": {"n": 25, "w": 12, "delivered": 48.0,
                                                "claimed": 85.0, "delta": -37.0}}, 0, _flags)
ck("🔴🔴 the card's banner OPENS with a plain warning when a band is flagged",
   _ban.startswith("⚠️ These confidence numbers are running high") and "48% (25 graded)" in _ban,
   "⛔ Sam: the banner printed the gap as one figure among four and never warned. got %r" % _ban[:160])
_quiet = _CF.calibration_sentence_fb({"80-plus": {"n": 25, "w": 21, "delivered": 84.0,
                                                  "claimed": 85.0, "delta": -1.0}}, 0, [])
ck("   ✅ ...and says nothing alarming when no band is flagged",
   not _quiet.startswith("⚠️"), "got %r" % _quiet[:120])


sys.exit(0)
