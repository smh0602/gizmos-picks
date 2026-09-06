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
  3. the tab still renders, and says a reset happened rather than 0-0
  4. a product that simply never graded anything must NOT claim a reset
"""
import json
import os
import subprocess
import sys
import tempfile

from jsblock import js_block
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
mlb = f"{ROOT}/data/latest/record.json"
if os.path.exists(mlb):
    O = json.load(open(mlb, encoding="utf-8")).get("overall") or {}
    ck("🔴 MLB still has its graded record", (O.get("n") or 0) > 0,
       f"{O.get('w')} of {O.get('n')} ({O.get('pct')}%) — graded against "
       f"the ledger and feeding the calibration accumulators")
    ck("...and the football floor is not in MLB's grader",
       "RECORD_FROM" not in open(f"{ROOT}/card.py", encoding="utf-8").read()
       if os.path.exists(f"{ROOT}/card.py") else True,
       "Sam said football only")
else:
    note("no MLB record on disk — section 2 not measured")

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
    ck("🔴 the record is wiped to nothing",
       (R.get("overall") or {}).get("n") == 0, str(R.get("overall")))
    ck("🔴 ...and what it set aside is COUNTED, not silently dropped",
       (R.get("cards_before_record_from") or 0) == len(dated),
       f"{R.get('cards_before_record_from')} of {len(dated)} card(s)")
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

print("\n═══ 5. THE TAB SURVIVES AND EXPLAINS ITSELF ═══")
blk = js_block("fbRecord", os.path.join(ROOT, "index.html"))
ck("🔴 the tab is still rendered — not removed", bool(blk) and "fbShell" in blk,
   "Sam: 'dont get rid of the tab completley'")
ck("the reset banner is built from the file's own fields",
   "R.record_from_note" in blk and "R.cards_before_record_from" in blk,
   "rule 132 — the page prints computed numbers, it does not carry the "
   "sentence")
ck("⛔ a product that never graded anything does NOT claim a reset",
   "(R.cards_before_record_from || 0) > 0" in blk,
   "'reset' and 'brand new' are different facts")
ck("the empty day table names the start date rather than saying 'never'",
   "Nothing graded since ${R.record_from}" in blk)
ck("the stat boxes still draw", "tr-hero" in blk and "tr-box" in blk,
   "Sam, 2026-09-03: 'i literally want everything to look exactly the same'")
