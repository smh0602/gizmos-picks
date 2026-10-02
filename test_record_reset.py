#!/usr/bin/env python3
"""
🔴 THE FOOTBALL RECORD WAS WIPED — AND THE TAB STAYS.

Sam, 2026-09-06: *"wipe the track record dont get rid of the tab
completley"*, and when asked the scope: *"only football"*.

⛔ WHY, AND IT IS NOT TIDINESS. Every football card published before
2026-09-07 was built while the pipeline was still being repaired: the
freshness contract had NO SUNDAY so boards were a day stale; one card
mixed two slate days (31 picks for 09-03, 19 for 09-04); every run without
an explicit season handed the collector a literal 2025; and CFBD was
rate-limiting us while the code called it "season not started".
**A hit rate over those cards measures the outage, not the product.**

⚠️ NOTHING IS DELETED. The cards stay in `picks/` byte-for-byte, so the
earlier period can be graded again by moving ONE date.

WHAT IS PINNED:
  1. MLB's record is NOT touched — it is graded against the ledger
  2. the floor is applied before grading, and what it set aside is COUNTED
  3. the tab still renders~~, and says a reset happened rather than 0-0~~
  4. ~~a product that simply never graded anything must NOT claim a reset~~
     the tab claims no reset at all

`[2026-09-28]` Item 1 is DRIVEN in the sandbox (an MLB record planted
beside the football tree must come out byte-identical), no longer read
off the live MLB record.

`[Sam, 2026-10-01]` Items 3 and 4: no explanation box on any tab ("i just
want what's supposed to be in each tab to be in each tab"; asked what
stays, he chose: remove everything). The reset banner is gone, so the tab
states no reset for anyone. record.json still carries the date, the count
and the sentence (item 2, unchanged).

# @vacuity 🔴 the football grader never writes where MLB's record lives (planted sandbox)
#   file: record_fb.py
#   find: LATEST = f"{DATA}/latest"
#   with: LATEST = "data/latest"
#
# @vacuity [Sam, 2026-10-01] the reset banner stays gone: fbRecord reads neither of its fields
#   file: index.html
#   find: v.innerHTML = fbShell(`<h2>${LG_NAME[LEAGUE]} record</h2>
#   with: v.innerHTML = fbShell(`<h2>${LG_NAME[LEAGUE]} record</h2>${(R && R.record_from_note && (R.cards_before_record_from || 0) > 0) ? R.record_from_note : ''}
#
# @vacuity [Sam, 2026-10-01] ...and the tab claims no reset, in no box
#   file: index.html
#   find: v.innerHTML = fbShell(`<h2>${LG_NAME[LEAGUE]} record</h2>
#   with: v.innerHTML = fbShell(`<h2>${LG_NAME[LEAGUE]} record</h2><div class="fnote"><b>The record was reset.</b></div>
"""
import gzip
import json
import os
import re
import subprocess
import sys
import tempfile

from jsblock import js_block, calls
from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
import record_fb  # noqa: E402

print("\n═══ 1. THE FLOOR EXISTS AND IS ONE DATE ═══")
ck("the record has a start date", bool(record_fb.RECORD_FROM),
   record_fb.RECORD_FROM)
ck("...and it is overridable without editing code",
   "FB_RECORD_FROM" in open("record_fb.py", encoding="utf-8").read(),
   "so the earlier period can be graded again by moving one value")

print("\n═══ 2. ⛔ MLB IS NOT TOUCHED ═══")
# 🔴 `[2026-09-28]` ~~ck("MLB still has its graded record", live n > 0)~~
#    asked PRODUCTION's MLB record to be non-empty (P3): a new season or a
#    rebuild reddened it with football untouched, and it never proved the
#    claim — a football grader that overwrote MLB's file with any graded
#    record would pass. ✅ The claim is now DRIVEN: section 3 puts an MLB
#    `record.json` in the sandbox and both football runs must leave it
#    byte-identical. The live MLB record is reported.
mlb = f"{ROOT}/data/latest/record.json"
if os.path.exists(mlb):
    O = json.load(open(mlb, encoding="utf-8")).get("overall") or {}
    note("the live MLB record: %s of %s (%s%%) graded — reported, not asserted"
         % (O.get("w"), O.get("n"), O.get("pct")))
else:
    note("no MLB record on disk")
ck("...and the football floor is not in MLB's grader",
   "RECORD_FROM" not in open(f"{ROOT}/card.py", encoding="utf-8").read()
   if os.path.exists(f"{ROOT}/card.py") else True,
   "Sam said football only")

print("\n═══ 3. THE WIPE, DRIVEN IN A THROWAWAY TREE ═══")
# ⛔ NEVER IN THE PRODUCT TREE. `tcheck` fails any test that leaves a file
#    under data/ or picks/ changed, and it is right to.
tmp = tempfile.mkdtemp()
for d in ("picks", "data/ncaaf/latest"):
    os.makedirs(os.path.join(tmp, d), exist_ok=True)
for f in os.listdir(f"{ROOT}/picks"):
    if f.startswith("fb-ncaaf-") and f.endswith(".json"):
        with open(f"{ROOT}/picks/{f}", encoding="utf-8") as a, \
             open(os.path.join(tmp, "picks", f), "w", encoding="utf-8") as b:
            b.write(a.read())
# 🔴 COPIED, NEVER HARD-LINKED. The first version used `os.link`, so the
#    grader writing `record.json` in the "sandbox" wrote straight through
#    to the real product file — and `tcheck` caught it, which is exactly
#    what rule 123 built it for. A hard link is not a copy.
import glob as _g      # noqa: E402
import shutil          # noqa: E402
for f in _g.glob(f"{ROOT}/data/ncaaf/latest/*"):
    if os.path.isfile(f):
        shutil.copy2(f, os.path.join(tmp, "data/ncaaf/latest",
                                     os.path.basename(f)))

# 🔴 `[2026-09-28]` AND THE COPIED OUTPUTS ARE REMOVED. The loop above
#    also copied the LIVE `record.json` and `record-detail.json.gz`, so
#    "the grader ran in the sandbox" passed with no grader output at all
#    (measured: a grader writing elsewhere stayed green here), and §3 read
#    production's record instead of this run's.
for _out in ("record.json", "record-detail.json.gz"):
    _op = os.path.join(tmp, "data/ncaaf/latest", _out)
    if os.path.exists(_op):
        os.remove(_op)

# ⛔ MLB'S RECORD, PLANTED IN THE SANDBOX — both football runs below must
#    leave it byte-for-byte as it was (§2's claim, driven).
_MLB_REC = os.path.join(tmp, "data", "latest", "record.json")
os.makedirs(os.path.dirname(_MLB_REC), exist_ok=True)
_MLB_BYTES = json.dumps({"built_at": "2026-09-27T12:00:00Z", "kind": "MLB",
                         "overall": {"w": 3, "n": 5, "pct": 60.0},
                         "calibration": [{"bucket": "60-70%", "predicted": 64.2,
                                          "w": 3, "n": 5, "pct": 60.0}]},
                        indent=1).encode("utf-8")
open(_MLB_REC, "wb").write(_MLB_BYTES)

dated = [f for f in os.listdir(os.path.join(tmp, "picks"))
         if f.startswith("fb-ncaaf-2") and not f.endswith("-latest.json")]
ck("there are real published football cards to set aside", len(dated) > 0,
   f"{len(dated)} dated card(s) copied into the sandbox")

r = subprocess.run([sys.executable, f"{ROOT}/record_fb.py"], cwd=tmp,
                   capture_output=True, text=True,
                   env=dict(os.environ, LEAGUE="ncaaf"))
out = r.stdout + r.stderr
rec_p = os.path.join(tmp, "data/ncaaf/latest/record.json")
ck("the grader ran in the sandbox", os.path.exists(rec_p), out[-200:])
if os.path.exists(rec_p):
    R = json.load(open(rec_p, encoding="utf-8"))
    # ══════════════════════════════════════════════════════════════
    # 🔴 ~~"the record is wiped to nothing"~~ — SAME EXPIRY, ONE LINE
    #    ABOVE THE NOTE THAT DESCRIBES IT. `[2026-09-10]` This read
    #    `overall.n == 0`, which was true only while NOTHING COULD BE
    #    GRADED. The college player log rebuilt at 22:30Z, the 09-07 card
    #    became gradeable, the record correctly read **23/47** — and this
    #    went red. ⛔ The product was right; the check was measuring the
    #    calendar, which is exactly what the block below says about its
    #    own predecessor. **The same lesson, in the same function, missed
    #    because only the line that had already failed got fixed.**
    # ✅ THE DURABLE QUESTION — and it is strictly harder than `n == 0`,
    #    which a grader that simply never ran would also satisfy: every
    #    day the record counts is ON OR AFTER the floor. That tests the
    #    WIPE HELD, at any row count, forever.
    # ══════════════════════════════════════════════════════════════
    _days = sorted((json.load(gzip.open(
        os.path.join(tmp, "data/ncaaf/latest/record-detail.json.gz"), "rt"))
        .get("days") or {}).keys())
    _leaked = [d for d in _days if d < record_fb.RECORD_FROM]
    ck("🔴 no day BEFORE the floor contributes to the record",
       not _leaked,
       "counts %d day(s) %s against floor %s — leaked: %s"
       % (len(_days), _days[:3], record_fb.RECORD_FROM, _leaked))
    if not _days:
        note("⚠️ NOT EXERCISED: the record counts zero days, so the wipe "
             "cannot be distinguished from a grader that never ran.")
    # ══════════════════════════════════════════════════════════════
    # 🔴 THIS ASSERTED "EVERY CARD IS SET ASIDE" AND HAD AN EXPIRY DATE
    #    OF ONE DAY. `[measured 2026-09-08, red on live main]` it read
    #    `== len(dated)`, which was true only while every published card
    #    predated the floor. The moment `fb-ncaaf-2026-09-07.json` was
    #    published — a card ON the floor, correctly counted — it read
    #    **3 of 4** and went red, and stayed red on every run after.
    # ⛔ The product was right. The check was measuring the CALENDAR.
    # ✅ The question that is true forever, and is strictly harder because
    #    it tests the BOUNDARY rather than a coincidence: the number set
    #    aside equals the number of cards dated STRICTLY BEFORE the floor.
    # ══════════════════════════════════════════════════════════════
    before = sorted(f for f in dated
                    if f[len("fb-ncaaf-"):-len(".json")]
                    < record_fb.RECORD_FROM)
    ck("🔴 ...and what it set aside is exactly the cards BEFORE the floor",
       (R.get("cards_before_record_from") or 0) == len(before),
       f"{R.get('cards_before_record_from')} set aside; "
       f"{len(before)} of {len(dated)} card(s) predate "
       f"{record_fb.RECORD_FROM}")
    ck("⚠️ ...and the floor is a real boundary, not a catch-all",
       len(before) < len(dated) or not dated,
       f"{len(dated) - len(before)} card(s) on/after the floor are COUNTED"
       + ("  ⚠️ none yet — this check is not yet exercised"
          if len(before) == len(dated) else ""))
    ck("the file carries the date the page will print",
       R.get("record_from") == record_fb.RECORD_FROM, str(R.get("record_from")))
    ck("...and a sentence built from those numbers, not written by hand",
       str(R.get("record_from_note", "")).startswith(
           f"Counting from {record_fb.RECORD_FROM}"),
       str(R.get("record_from_note"))[:90])
    ck("⚠️ the log says the cards themselves are untouched",
       "untouched in picks/" in out, out[:160])

    # ⛔ AND THE CARDS REALLY ARE UNTOUCHED — compared byte for byte.
    same = all(open(f"{ROOT}/picks/{f}", "rb").read()
               == open(os.path.join(tmp, "picks", f), "rb").read()
               for f in dated)
    ck("🔴 every published card is byte-identical after grading", same,
       "a wipe that rewrote the cards would not be reversible")

print("\n═══ 4. A FUTURE FLOOR GRADES NOTHING; A PAST ONE GRADES AGAIN ═══")
r2 = subprocess.run([sys.executable, f"{ROOT}/record_fb.py"], cwd=tmp,
                    capture_output=True, text=True,
                    env=dict(os.environ, LEAGUE="ncaaf",
                             FB_RECORD_FROM="2000-01-01"))
if os.path.exists(rec_p):
    R2 = json.load(open(rec_p, encoding="utf-8"))
    ck("🔴 moving the date back grades the earlier cards again",
       (R2.get("cards_before_record_from") or 0) == 0,
       f"set aside {R2.get('cards_before_record_from')} with the floor at "
       f"2000-01-01 — the wipe is REVERSIBLE, which is the point of a "
       f"floor rather than a delete")
    ck("...and the tab would then not claim a reset",
       (R2.get("cards_before_record_from") or 0) == 0)
ck("🔴 MLB's record is byte-identical after BOTH football grading runs",
   os.path.exists(_MLB_REC) and open(_MLB_REC, "rb").read() == _MLB_BYTES
   and os.path.exists(rec_p),
   "⛔ Sam: 'only football'. A football grader that wrote where MLB's "
   "record lives would erase the record the calibration accumulators "
   "feed on. rc=%s/%s" % (r.returncode, r2.returncode))
shutil.rmtree(tmp, ignore_errors=True)

# `[Sam, 2026-10-01]` ~~AND EXPLAINS ITSELF~~ — no explanation box on any tab.
print("\n═══ 5. THE TAB SURVIVES, AND CLAIMS NO RESET ═══")
blk = js_block("fbRecord", os.path.join(ROOT, "index.html"))
ck("🔴 the tab is still rendered — not removed", bool(blk) and "fbShell" in blk,
   "Sam: 'dont get rid of the tab completley'")
# 🔴 `[Sam, 2026-10-01]` ~~ck("the reset banner is built from the file's own
#    fields", "R.record_from_note" in blk and "R.cards_before_record_from" in
#    blk)~~ and ~~ck("⛔ a product that never graded anything does NOT claim a
#    reset", "(R.cards_before_record_from || 0) > 0" in blk)~~. The tab
#    explained the reset in a footnote box printed from record.json's own
#    fields, and only when cards had really been set aside. Sam: no
#    explanation, caveat or warning box on any tab; asked what stays, he
#    chose: remove everything. So the banner is required ABSENT, asked of the
#    same function. Comments are stripped first: a dated note saying the
#    banner went is not the banner. ⚠️ record_fb.py still WRITES both fields,
#    and section 3 drives that, unchanged; only the page stopped printing them.
_code = re.sub(r"(?m)^\s*//.*$", "", re.sub(r"/\*.*?\*/", "", blk, flags=re.S))
ck("⛔ [Sam, 2026-10-01] the reset banner is GONE — fbRecord reads neither of its fields",
   not re.search(r"\.\s*(?:record_from_note|cards_before_record_from)\b", _code),
   "rule 132 still holds in the file: record.json computes the sentence; "
   "the page no longer prints it")
ck("⛔ [Sam, 2026-10-01] ...and the tab claims no reset at all, for a new product or a reset one",
   not re.search(r"was\s+reset", _code, re.I)
   and 'class="fnote"' not in _code and 'class="note"' not in _code,
   "'reset' and 'brand new' are still different facts — record.json keeps "
   "both; the page states neither")
# ⚠️ ~~`"Nothing graded since ${R.record_from}" in blk`~~ — the markup
#    moved into `fbDayRows()` on 2026-09-16 when the day rows became
#    clickable, and its variable is `rec` there, not `R`. ⛔ The question
#    is still right; the ADDRESS was wrong, and a substring search in one
#    function is what made it fragile.
# ✅ THE REPLACEMENT IS TWO ASSERTIONS WHERE THERE WAS ONE: the sentence
#    is where the markup now lives, AND `fbRecord` still calls that
#    function — so it cannot drift into dead code, which the old form
#    could never have detected.
# ➡️ `test_fb_record.py` drives the same sentence by RENDERING it.
_dayrows = js_block("fbDayRows", os.path.join(ROOT, "index.html"))
ck("the empty day table names the start date rather than saying 'never'",
   "Nothing graded since ${rec.record_from}" in _dayrows)
ck("   ...and fbRecord still calls the function that draws it",
   "fbDayRows(" in blk and calls("fbDayRows", os.path.join(ROOT, "index.html")) >= 1,
   "🔴 a renderer nobody calls looks exactly like the one that renders "
   "the page — rule 130")
ck("the stat boxes still draw", "tr-hero" in blk and "tr-box" in blk,
   "Sam, 2026-09-03: 'i literally want everything to look exactly the same'")
