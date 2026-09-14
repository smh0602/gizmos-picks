#!/usr/bin/env python3
"""
COVERAGE MATRIX — BREAK THE PRODUCT N WAYS AND SEE WHAT THE WATCHDOG SAYS.

🔴 THIS FILE IS THE ANSWER TO "WILL IT CATCH THINGS SO I DO NOT HAVE TO."
Every case below is a way the PAGE can be wrong for a reader. The question
is never "is this a bug" — it is **would Sam have to notice it himself**.

⛔ THE FIRST RUN OF THIS MATRIX REPORTED 100% COVERAGE AND IT WAS A LIE.
The fixture tree had no `index.html`, so the new `page:missing` check
fired on EVERY case — including the control — and every row scored
"caught". ⚠️ **A check that fires on everything catches nothing**, and a
matrix that cannot be quiet cannot measure. ✅ The control case exists to
make that impossible to miss again: if the control is not SILENT, every
other row on this page is meaningless.

➡️ ONE MISS IS EXPECTED AND DOCUMENTED. A parlay leg below the -700 floor
is real, and it is deliberately NOT checked here — `verify_card.py` owns
that rule and a copy in the watchdog would be a THIRD reader of Sam's
number. The second copy is what broke the card on 2026-09-12.
"""
import datetime
import json
import os
import shutil
import sys
import tempfile

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import watchdog as W  # noqa: E402
import freshness as F  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 9, 14, 18, 0, tzinfo=UTC)   # 2pm ET
DAY = F.et_date(F.last_due(F.CARD, NOW))
OLD = W.ROOT
ROWS = []



def healthy_tree():
    d = tempfile.mkdtemp()
    for p in ("picks", "data/latest", "data/ncaaf/latest", "data/nfl/latest"):
        os.makedirs(os.path.join(d, p), exist_ok=True)
    w(d, "picks/%s.json" % DAY, {
        "date": DAY, "picks": [{"player": "A", "commence": "2026-09-14T23:00:00Z",
                                "price": -150, "confidence": 70}],
        "parlays": {"2": [{"legs": ["a", "b"], "prices": [-150, -150]}]},
        "projections": {"A|hits": 1.2},
        "top10": [{"player": "A", "price": -150, "commence": "2026-09-14T23:00:00Z"}],
    })
    for lg, dt in (("ncaaf", "2026-09-12"), ("nfl", "2026-09-13")):
        w(d, "picks/fb-%s-latest.json" % lg, {
            "date": dt, "picks": [], "game_lines": [], "top_plays": [],
            "game_lines_meta": {"slate": dt}})
    for sub in ("latest", "ncaaf/latest", "nfl/latest"):
        w(d, "data/%s/freshness.json" % sub, {"ok": True, "rows": []})
        w(d, "data/%s/record.json" % sub, {"n": 1})
    # 🔴 THE REAL PAGE, COPIED IN. Without it `page:missing` fires on
    #    EVERY case including the control — and a check that fires on
    #    everything catches nothing, while scoring 100% on this matrix.
    #    The harness nearly reported perfect coverage on that basis.
    shutil.copy(os.path.join(ROOT, "index.html"), os.path.join(d, "index.html"))
    return d


def w(d, rel, obj):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if isinstance(obj, str):
        open(p, "w", encoding="utf-8").write(obj)
    else:
        json.dump(obj, open(p, "w", encoding="utf-8"))


def case(name, what_reader_sees, mutate):
    d = healthy_tree()
    try:
        mutate(d)
        W.ROOT = d
        # record.json mtime is "now", so the record check cannot fire;
        # that is correct for every case except the one that targets it.
        r = W.run(NOW)
        W.ROOT = OLD
        caught = not r["healthy"]
        keys = sorted({i["key"] for i in r["findings"]})
        ROWS.append((name, what_reader_sees, caught, keys,
                     r["repairs"], bool(r.get("unrepairable"))))
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── sanity ──────────────────────────────────────────────────────────
case("CONTROL — nothing wrong", "a correct page", lambda d: None)

# ── the ones it was built for ───────────────────────────────────────
case("MLB card missing", "Gizmo's Picks empty",
     lambda d: os.remove(os.path.join(d, "picks/%s.json" % DAY)))
case("MLB card refused by verifier", "Gizmo's Picks empty, silently",
     lambda d: w(d, "data/latest/card-verify-failure.txt", "  FAIL x\n"))
case("football game_lines on another day", "next week's lines under a one-day header",
     lambda d: w(d, "picks/fb-nfl-latest.json",
                 {"date": "2026-09-13", "picks": [], "top_plays": [],
                  "game_lines": [{"commence": "2026-09-20T17:00:00Z"}],
                  "game_lines_meta": {"slate": "2026-09-13"}}))
case("football picks on another day", "a Saturday row on a Sunday card",
     lambda d: w(d, "picks/fb-nfl-latest.json",
                 {"date": "2026-09-13", "game_lines": [], "top_plays": [],
                  "picks": [{"commence": "2026-09-20T17:00:00Z"}],
                  "game_lines_meta": {"slate": "2026-09-13"}}))
case("freshness contract reports stale", "tabs showing old data",
     lambda d: w(d, "data/ncaaf/latest/freshness.json",
                 {"ok": False, "rows": [{"key": "props-player", "stale": True}]}))
case("football card file gone", "football Gizmo's Picks empty",
     lambda d: os.remove(os.path.join(d, "picks/fb-nfl-latest.json")))

# ── the ones I suspect it MISSES ────────────────────────────────────
case("top_plays on another day", "Top Plays listing a game from next week",
     lambda d: w(d, "picks/fb-nfl-latest.json",
                 {"date": "2026-09-13", "picks": [], "game_lines": [],
                  "top_plays": [{"commence": "2026-09-20T17:00:00Z"}],
                  "game_lines_meta": {"slate": "2026-09-13"}}))
case("MLB card exists but has ZERO picks", "Gizmo's Picks renders an empty board",
     lambda d: w(d, "picks/%s.json" % DAY,
                 {"date": DAY, "picks": [], "parlays": {}, "projections": {},
                  "top10": [], "coverage_detail": {"skipped": {"x": 40}}}))
case("MLB card lost every projection", "no PROJ chip anywhere on Player Props",
     lambda d: w(d, "picks/%s.json" % DAY,
                 {"date": DAY, "picks": [{"player": "A", "price": -150}],
                  "parlays": {}, "projections": {}, "top10": []}))
case("football card has ZERO picks", "football board empty",
     lambda d: w(d, "picks/fb-nfl-latest.json",
                 {"date": "2026-09-13", "picks": [], "game_lines": [],
                  "n_priced": 967,
                  "top_plays": [], "game_lines_meta": {"slate": "2026-09-13"}}))
case("a card is corrupt JSON", "the tab fails to load",
     lambda d: w(d, "picks/%s.json" % DAY, "{ this is not json"))
case("index.html throws — blank page", "the ENTIRE site is blank",
     lambda d: w(d, "index.html", "<script>syntax error(</script>"))
case("record.json shows an impossible rate", "Track Record reads 140%",
     lambda d: w(d, "data/latest/record.json",
                 {"overall": {"w": 14, "n": 10, "pct": 140.0}}))
case("a parlay leg is below the price floor", "an unbettable slip on the page",
     lambda d: w(d, "picks/%s.json" % DAY,
                 {"date": DAY, "picks": [{"player": "A", "price": -150}],
                  "parlays": {"2": [{"legs": ["a", "b"],
                                     "prices": [-900, -150]}]},
                  "projections": {"A|hits": 1.0}, "top10": []}))
case("the card is for the WRONG DAY entirely", "yesterday's board labelled today",
     lambda d: (os.remove(os.path.join(d, "picks/%s.json" % DAY)),
                w(d, "picks/2026-09-13.json", {"date": "2026-09-13", "picks": []})))

# ══════════════════════════════════════════════════════════════════════
# ⛔ THE EXPECTED MISS, NAMED. Anything else that stops being caught is a
#    regression in the watchdog and fails this file.
EXPECTED_MISS = {"a parlay leg is below the price floor"}

print("%-42s %-8s %s" % ("FAILURE INJECTED", "CAUGHT", "what fired"))
print("-" * 96)
for name, seen, caught, keys, repairs, unrep in ROWS:
    print("  %-40s %-8s %s" % (name[:40], "yes" if caught else "** NO **",
                               ", ".join(keys) or "-"))

_ctrl = [r for r in ROWS if r[0].startswith("CONTROL")][0]
ck("🔴🔴 THE CONTROL IS SILENT",
   not _ctrl[2],
   "⛔ IF THIS FAILS, EVERY OTHER ROW ON THIS PAGE IS MEANINGLESS. A "
   "watchdog that fires on a correct tree catches nothing and gets muted. "
   "The first run of this matrix scored 100%% purely because a missing "
   "fixture file made one check fire on all 17 cases. Fired: %s"
   % (_ctrl[3] or "-"))

for name, seen, caught, keys, repairs, unrep in ROWS:
    if name.startswith("CONTROL"):
        continue
    if name in EXPECTED_MISS:
        note("⚠️ EXPECTED MISS — %s. Reader would see: %s. ⛔ Not checked "
             "on purpose: `verify_card.py` owns that rule and a copy here "
             "would be a THIRD reader of Sam's number." % (name, seen))
        continue
    ck("🔴 caught: %s" % name,
       caught,
       "⛔ a reader would see: %s — and nothing would tell Sam. This case "
       "was caught when the matrix was written, so losing it is a "
       "REGRESSION in the watchdog, not a gap in this file." % seen)

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that these are the only ways the "
     "page can be wrong. It claims that these %d ways are covered and "
     "stay covered. ➡️ Every new failure shape Sam reports earns a row "
     "here — that is the maintenance cost of the guarantee."
     % (len(ROWS) - 1))
