#!/usr/bin/env python3
"""
A TEST THAT QUERIES LIVE DATA MUST NOT WRITE A DATE DOWN.

🔴🔴 LEDGER RULE 166, NOW FOR THE THIRD TIME — **A CHECK WITH AN EXPIRY
DATE, AND NOTHING EXPIRES IT.**

    test_record_reset   asserted a count true for exactly one day
    test_box_live       asserted "most games have NO stored player log",
                        written at 17 of 202, red at 185 of 339
    test_board_match    probed `boardFor(..., '2026-09-15T20:00:00Z')`
                        and called it "20 days from any record"

⛔ **THE THIRD ONE WENT RED ON 2026-09-14 AGAINST A PERFECTLY CORRECT
PAGE.** It *was* 20 days away — when it was written, against an 08-26
board. The live board then advanced to 09-14..09-16, the literal landed
INSIDE the match window, `boardFor` correctly returned the 09-15 record,
and the assertion failed the product for being right.

➡️ **THE CLASS: a hardcoded absolute date is a claim about WHEN THE TEST
RUNS, and no test controls that.** Against a fixture it is fine and often
necessary — the fixture holds still. Against a LIVE artifact that moves
every day it is a timer counting down to a false alarm.

══════════════════════════════════════════════════════════════════════
⚠️ WHY THIS SWEEP IS NARROW ON PURPOSE, AND WHAT IT REFUSES TO DO.

`[measured 2026-09-14]` **11 test files carry an absolute date literal.**
⛔ Failing all 11 would be a false-alarm machine — rule 238 — because
**nine of them write a temp fixture and drive a fixed clock against it,
which is exactly right**: `test_watchdog.py` MUST pin 00:47 ET Monday to
reproduce the deadline bug.

✅ So the sweep asks a much narrower question: **does this file open a
LIVE artifact AND build no fixture?** Two files qualify today —
`test_board_match.js` and `test_ranking.py` — and only those two are
forbidden a date literal.

🔴 **AND THE FILE LIST IS DISCOVERED, NEVER NAMED.** Rule 246: a check
that names its surfaces inherits the bug that comes from naming surfaces.
A new live-data test is covered the day it ships, by nobody doing
anything.
"""
import glob
import os
import re

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))

# Opening one of the repo's real, moving artifacts — not a temp copy.
LIVE = re.compile(r"""(?:open|readFileSync|load)\s*\(\s*['"]"""
                  r"""(?:data/latest/|data/(?:ncaaf|nfl)/latest/|picks/)""")
# Any sign the file builds its own tree and drives a fixed clock at it.
FIXTURE = re.compile(r"tempfile|mkdtemp|Tree\(\)|TemporaryDirectory|"
                     r"os\.path\.join\(self\.d|t\.write\(")
# 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SSZ' as a literal.
DATE = re.compile(r"""['"](20\d\d-\d\d-\d\d(?:T[\d:]+Z?)?)['"]""")


# ⛔ COMMENTS ARE STRIPPED FIRST, AND THE FIRST RUN OF THIS FILE PROVED
#    WHY. It flagged `test_board_match.js` for a date that appears only
#    inside the comment explaining the very defect this sweep exists for —
#    *"this block used to ask boardFor(..., '2026-09-15T20:00:00Z')"*.
# 🔴 A DATE IN PROSE IS HISTORY. A DATE IN CODE IS A CLAIM ABOUT WHEN THE
#    TEST RUNS. Only the second one expires, and this repo's house style
#    keeps superseded code visible in comments — so an unstripped sweep
#    punishes exactly the files that documented their own fix.
_BLOCK = re.compile(r"/\*.*?\*/", re.S)
_LINE = re.compile(r"^\s*(?://|#).*$", re.M)


def strip_comments(text):
    return _LINE.sub("", _BLOCK.sub("", text))


def scan(text):
    code = strip_comments(text)
    return (bool(LIVE.search(code)), bool(FIXTURE.search(code)),
            sorted(set(DATE.findall(code))))


files = sorted(glob.glob(os.path.join(ROOT, "test_*.py"))
               + glob.glob(os.path.join(ROOT, "test_*.js")))
_probe = "code = 1\n# a comment with '2026-09-15' in it\n/* and '2026-01-01' */"
ck("⛔ the comment stripper actually removes a commented date",
   scan(_probe)[2] == [],
   "🔴 IF THIS FAILS THE SWEEP PUNISHES DOCUMENTATION. This repo keeps "
   "superseded code visible in comments, so an unstripped sweep flags "
   "every file that explained its own fix — and the first run of THIS "
   "file did exactly that. Got %s" % (scan(_probe)[2],))

ck("🔴 the sweep actually found the test suite",
   len(files) > 40,
   "⛔ a glob that matches nothing passes every check below for the worst "
   "possible reason (rule 67). Found %d" % len(files))

live_only, offenders, with_dates = [], [], 0
for p in files:
    if os.path.basename(p) == os.path.basename(__file__):
        continue
    text = open(p, encoding="utf-8", errors="replace").read()
    is_live, has_fix, dates = scan(text)
    if dates:
        with_dates += 1
    if is_live and not has_fix:
        live_only.append(os.path.basename(p))
        if dates:
            offenders.append("%s -> %s" % (os.path.basename(p), dates))

ck("🔴 the sweep found the live-data tests it is written for",
   len(live_only) >= 2,
   "⛔ if this list is empty the check below is vacuous — it would pass a "
   "repo where every live test hardcoded a date. Found: %s" % live_only)

ck("🔴🔴 no test that queries LIVE data writes a date down",
   not offenders,
   "⛔ RULE 166 — a hardcoded date against a moving artifact is a claim "
   "about when the test runs, and no test controls that. It goes red on "
   "a correct product the day the data moves past it, which is worse "
   "than a miss: a false alarm gets the whole suite ignored. ➡️ Derive "
   "the timestamp from the artifact you loaded. Offenders: %s" % offenders)

note("swept %d test files: %d carry a date literal, %d read live data "
     "without a fixture, %d in both sets"
     % (len(files), with_dates, len(live_only), len(offenders)))

# 🔴 AND THE SWEEP IS PROVED TO BITE, because "no offenders" is also what
#    a broken regex returns. The two halves are planted separately so a
#    failure names which half died.
_planted = "x = open('data/latest/board.json'); d = '2026-09-15T20:00:00Z'"
_is_live, _has_fix, _dates = scan(_planted)
ck("⛔ ...and a planted live-data-plus-literal-date file IS caught",
   _is_live and not _has_fix and _dates == ["2026-09-15T20:00:00Z"],
   "🔴 this is the exact line that went red on 2026-09-14. If the sweep "
   "does not flag it, every result above is green for the same reason an "
   "empty list is green. live=%s fixture=%s dates=%s"
   % (_is_live, _has_fix, _dates))

_fixture = ("import tempfile\nd = tempfile.mkdtemp()\n"
            "x = open('data/latest/board.json'); s = '2026-09-15'")
ck("✅ ...and the same date inside a FIXTURE test is NOT flagged",
   all(scan(_fixture)[:2]),
   "⛔ nine files pin a clock against a temp tree and are RIGHT to — "
   "`test_watchdog.py` must reproduce 00:47 ET Monday exactly. A sweep "
   "that fails those is rule 238, not rule 166")

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that a fixture test's fixed clock "
     "is always correct, or that a derived timestamp is always right. ➡️ "
     "It closes ONE class — a literal date asked of an artifact that "
     "moves — and says nothing about the rest.")
