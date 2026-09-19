#!/usr/bin/env python3
"""🔴🔴 THE ONE NUMBER THE PRODUCT EXISTS TO PRODUCE, AND NOTHING WATCHED IT.

`[measured 2026-09-19 on data/latest/record.json]`

    by_kind.pitcher   {"w": 290, "n": 580, "pct": 50.0}
    calibration       50-60%  predicted 56.4, delivered 46.4  n=181
                      60-70%  predicted 64.2, delivered 49.5  n=279
                      70-80%  predicted 73.5, delivered 59.2  n=98
                      80-90%  predicted 85.5, delivered 47.1  n=17

The MLB pitcher board is a coin flip advertising 58–93%. The page says
so honestly — `index.html:1702` renders `calibration_warning` under
*"Read the confidence number honestly."* — and **nothing alarms**,
because `calibration.py` was football-only by design.

⛔⛔ THAT DESIGN IS SAM'S AND THE FREEZE STATES IT: *"no scheduled checks
that read MLB state."* This file and the change it guards live on a
branch named so they cannot be merged by accident. **The decision is
his.** What is here is the change, working, with its cost measured.

⚠️ AND IT DOES NOT FIRE. Pooled, MLB reads **stated 64.2%, delivered
50.0% over 580 rows, p≈0 — a gap of −14.2 points against a −15.0 bar.**
It misses by three quarters of a point. ⛔ THE BAR IS NOT MOVED. It is
borrowed from T58 and was fixed before any of these numbers existed;
tuning it to make today trip is the single thing `CLAUDE.md` forbids
most plainly. §3 asserts the constants are untouched.

✅ WHAT CHANGES IS THAT THE NUMBER IS SHOWN. The renderer now prints
every league's measured line, so a gap that misses the bar by a point is
visible instead of absent.

# @vacuity 🔴🔴 the two leagues' bucket key is resolved, never defaulted
#   file: calibration.py
#   find:     key = ("stated" if any("stated" in b for b in rows)
#   with:     key = ("stated" if True
#
# @vacuity 🔴 the alarm bar is not tuned to today's numbers
#   file: calibration.py
#   find: GAP_POINTS = 15.0
#   with: GAP_POINTS = 14.0
"""
import io
import json
import os

import calibration as C
from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))

# ════════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 THE TWO LEAGUES NAME THE SAME NUMBER DIFFERENTLY")
# ════════════════════════════════════════════════════════════════════════
# ⛔ Football buckets carry `stated`; MLB's carry `predicted`. The old
#    reader was `b.get("stated") or 0.0`, which returns 0.0 — not None —
#    against an MLB bucket. The gap would have become `actual - 0`, every
#    league would have read as beating its claim by sixty points, and the
#    alarm would never have fired. Same shape as the watchdog reading
#    `rows` off a file the collector writes with `artifacts`.
FB = [{"bucket": "60-70%", "n": 100, "w": 50, "stated": 65.0}]
MLB = [{"bucket": "60-70%", "n": 100, "w": 50, "predicted": 65.0}]
NEITHER = [{"bucket": "60-70%", "n": 100, "w": 50}]

ck("🔴 a football bucket is read through `stated`",
   C.pooled(FB) == (100, 50, 65.0),
   "got %r" % (C.pooled(FB),))
ck("🔴🔴 an MLB bucket is read through `predicted`",
   C.pooled(MLB) == (100, 50, 65.0),
   "⛔ THE BUG THIS AVOIDS: `b.get('stated') or 0.0` gives 0.0 here, the "
   "gap becomes +50 and the board reads as beating its claim. "
   "got %r" % (C.pooled(MLB),))
ck("⛔ a bucket carrying NEITHER key is UNREADABLE, never zero",
   C.pooled(NEITHER)[2] is None,
   "🔴 defaulting to 0.0 is how a silent misread becomes a green tick. "
   "got %r" % (C.pooled(NEITHER),))
ck("   ...and `judge` turns that into UNREADABLE, not OK",
   C.judge({"calibration": NEITHER}).get("state") == "UNREADABLE",
   "got %r" % (C.judge({"calibration": NEITHER}),))

# ════════════════════════════════════════════════════════════════════════
section("2. 🔴 MLB'S RECORD IS AT data/latest, NOT data/mlb/latest")
# ════════════════════════════════════════════════════════════════════════
ck("🔴 the MLB path skips the league directory it never had",
   C.record_path("mlb", ROOT) == os.path.join(ROOT, "data", "latest",
                                              "record.json"),
   "⛔ MLB was the first league and never got a subdirectory. A path "
   "built from the league name lands nowhere and reports UNREADABLE — "
   "honest, and useless. got %r" % C.record_path("mlb", ROOT))
ck("⚠️ ...and football still resolves the ordinary way",
   C.record_path("nfl", ROOT) == os.path.join(ROOT, "data", "nfl", "latest",
                                              "record.json"),
   "got %r" % C.record_path("nfl", ROOT))
ck("⚠️ every league in LEAGUES has a record on disk",
   all(os.path.exists(C.record_path(lg, ROOT)) for lg in C.LEAGUES),
   "⛔ rule 67 — a league whose file is missing reads UNREADABLE and "
   "proves nothing below. missing=%s"
   % [lg for lg in C.LEAGUES if not os.path.exists(C.record_path(lg, ROOT))])

# ════════════════════════════════════════════════════════════════════════
section("3. ⛔ AND THE BAR IS NOT TUNED TO TODAY'S NUMBERS")
# ════════════════════════════════════════════════════════════════════════
ck("⛔ GAP_POINTS is still 15.0, borrowed from T58",
   C.GAP_POINTS == 15.0,
   "🔴 MLB reads a gap of −14.2. Lowering this by one point would make "
   "it fire, which is precisely why it may not move. `CLAUDE.md`: never "
   "weaken — or strengthen to taste — a bar to get the answer you want. "
   "got %r" % C.GAP_POINTS)
ck("⛔ P_MAX is still 0.01 and MIN_N still 100",
   C.P_MAX == 0.01 and C.MIN_N == 100,
   "got p_max=%r min_n=%r" % (C.P_MAX, C.MIN_N))

RES = C.read_all(ROOT)
mlb = RES.get("mlb") or {}
ck("🔴 MLB is read, and pooled over a real sample",
   mlb.get("n", 0) >= 500 and mlb.get("stated") is not None,
   "⛔ this is the whole change. got n=%r stated=%r"
   % (mlb.get("n"), mlb.get("stated")))
ck("⚠️ ...and it does NOT trip the borrowed bar",
   mlb.get("state") in ("OK", "NOT_MEASURABLE"),
   "🔴 SAID OUT LOUD. The gap is %.1f points against a %.1f bar — it "
   "misses. If this ever becomes UNDER that is the product changing, "
   "not this file. state=%r gap=%r"
   % (mlb.get("gap", 0.0), -C.GAP_POINTS, mlb.get("state"), mlb.get("gap")))
note("MLB pooled: stated %.1f%%, delivered %.1f%% over %d rows, gap %+.1f, "
     "p=%.5f — verdict %s"
     % (mlb.get("stated", 0), mlb.get("actual", 0), mlb.get("n", 0),
        mlb.get("gap", 0), mlb.get("p") or 0, mlb.get("state")))

# ════════════════════════════════════════════════════════════════════════
section("4. 🔴 A NUMBER THAT MISSES THE BAR IS STILL PRINTED")
# ════════════════════════════════════════════════════════════════════════
body = C.render(RES)
ck("🔴🔴 every league with a sample appears in the body",
   all(("`%s`" % lg) in body for lg in C.LEAGUES
       if (RES.get(lg) or {}).get("n")),
   "⛔ a monitor that prints only failures cannot show a gap that "
   "misses by three quarters of a point. Under the old renderer MLB "
   "would have appeared nowhere at all. body=%r" % body[-400:])
ck("⚠️ ...with its stated, delivered, rows and gap",
   "| stated | delivered | rows | gap |" in body.replace("league | ", ""),
   "⛔ a league name with no numbers beside it is not a report. "
   "body=%r" % body[-400:])
ck("⛔ ...and the body still says the bar, so nobody has to guess it",
   ("%.0f points" % -C.GAP_POINTS) in body and "p<0.01" in body,
   "🔴 a threshold the reader cannot see is a threshold they cannot "
   "argue with.")
ck("⛔ ...and it no longer claims MLB is never read",
   "MLB is frozen and is never read here" not in body,
   "🔴 rule 166 again: the footer was true until this change and would "
   "have been a fresh false claim the moment it landed.")
