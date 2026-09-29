#!/usr/bin/env python3
"""A DAY WITH NO MLB GAMES OWES NO CARD AND NO RESULTS — IN THE CONTRACT TOO.

`[2026-09-29]` #200 stopped the WATCHDOG calling a no-games day's MLB card
BROKEN. The freshness contract still did: collect #1983 (2026-09-29 04:42Z)
failed with "mlb is out of contract" -- "card MISSED its 10:00 ET build:
never built" and `data/2026-09-28/results` missing -- for 2026-09-28, a day
with 0 MLB games. The postseason has more off-days coming.

✅ `freshness.no_games_day` is the ONE copy (watchdog.py imports it), and the
contract leaves out the MLB `card` and `results` rows for a day every
schedule reading says had 0 games. ⛔ Fail closed: no reading, an unreadable
one, one without `totalGames`, or any reading with a game means they are due.
Driven on a tree pinned to #1983's own clock, never on production data.

Also here: nothing in the product code still says MLB is frozen (Sam lifted
the freeze on 2026-09-22).

# @vacuity 🔴 an off-day's card is not in the contract
#   file: freshness.py
#   find:         rows = [r for r in rows if r[0] != "card"]
#   with:         pass
#
# @vacuity 🔴 ...nor its results
#   file: freshness.py
#   find:         rows = [r for r in rows if r[0] != "results"]
#   with:         pass
#
# @vacuity ⛔ a game day with no card is still late
#   file: freshness.py
#   find:     if no_games_day(due_date(CARD, now), data):
#   with:     if True:
#
# @vacuity ⛔ ...and a game day's missing results still are
#   file: freshness.py
#   find:     if no_games_day(slate_date(now), data):
#   with:     if True:
#
# @vacuity ⛔ no schedule reading still counts as due
#   file: freshness.py
#   find:     return bool(seen) and all(n == 0 for n in seen)
#   with:     return all(n == 0 for n in seen)
#
# @vacuity 🔴 nothing in the product code says MLB is frozen
#   file: calibration.py
#   find:                "monitor does not read MLB._")
#   with:                "monitor does not read MLB: MLB is frozen._")
"""
import datetime
import glob
import gzip
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import freshness as F  # noqa: E402
from tcheck import ck, note, section  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 9, 29, 4, 42, tzinfo=UTC)   # collect #1983
DAY = "2026-09-28"                                          # 0 MLB games


def survey(readings):
    """Survey a fresh tree holding only the given schedule readings for DAY.
    `readings`: list of (name, doc | bytes). -> {mode: [rows]}."""
    t = tempfile.mkdtemp(prefix="mlb-offday-")
    try:
        data = t.replace("\\", "/") + "/data"
        for name, doc in readings:
            p = os.path.join(t, "data", DAY, "schedule", name)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if isinstance(doc, bytes):
                open(p, "wb").write(doc)
            else:
                with gzip.open(p, "wt") as fh:
                    json.dump(doc, fh)
        out = {}
        for r in F.survey(data, t.replace("\\", "/") + "/picks", NOW):
            out.setdefault(r["mode"], []).append(r)
        return out
    finally:
        shutil.rmtree(t, ignore_errors=True)


def games(n):
    return {"date": DAY, "schedule": {"totalGames": n}}


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 AN OFF-DAY RAISES NOTHING FOR CARD OR RESULTS")
# ══════════════════════════════════════════════════════════════════════
ck("⚠️ the clock is #1983's: the card's day and the results' slate are both %s" % DAY,
   F.due_date(F.CARD, NOW) == DAY and F.slate_date(NOW) == DAY,
   "card %s, slate %s" % (F.due_date(F.CARD, NOW), F.slate_date(NOW)))
off = survey([("0900.json.gz", games(0)), ("2100.json.gz", games(0))])
ck("🔴 a day every reading says had 0 games owes no card",
   "card" not in off, "card rows: %s" % off.get("card"))
ck("🔴 ...and no results", "results" not in off, "results rows: %s" % off.get("results"))
ck("⚠️ ...and the exemption is narrow: the other MLB rows are still judged",
   all(m in off for m in ("scores", "pitchers", "record", "gamelines")),
   "modes: %s" % sorted(off))

# ══════════════════════════════════════════════════════════════════════
section("2. ⛔ A GAME DAY WITH NO CARD IS STILL LATE")
# ══════════════════════════════════════════════════════════════════════
on = survey([("0900.json.gz", games(0)), ("2100.json.gz", games(3))])
ck("⛔ any reading with a game: the missing card is due and stale",
   bool(on.get("card")) and all(r["stale"] for r in on["card"]),
   "card rows: %s" % on.get("card"))
ck("⛔ ...and the missing results are too",
   bool(on.get("results")) and all(r["stale"] for r in on["results"]),
   "results rows: %s" % on.get("results"))

# ══════════════════════════════════════════════════════════════════════
section("3. ⛔ NO SCHEDULE READING STILL COUNTS AS DUE")
# ══════════════════════════════════════════════════════════════════════
for label, readings in (("no reading at all", []),
                        ("an unreadable reading beside a 0", [("0900.json.gz", games(0)),
                                                              ("1200.json.gz", b"junk")]),
                        ("a reading without totalGames beside a 0",
                         [("0900.json.gz", games(0)),
                          ("1200.json.gz", {"date": DAY, "schedule": {"dates": []}})])):
    got = survey(readings)
    ck("⛔ %s: card and results are due and stale" % label,
       bool(got.get("card")) and bool(got.get("results"))
       and all(r["stale"] for r in got["card"] + got["results"]),
       "card %s / results %s" % (got.get("card"), got.get("results")))
note("the real 2026-09-28 (read, not asserted): no_games_day=%s"
     % F.no_games_day(DAY, os.path.join(ROOT, "data")))

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 NOTHING IN THE PRODUCT CODE SAYS MLB IS FROZEN")
# ══════════════════════════════════════════════════════════════════════
# Sam lifted the freeze on 2026-09-22 ("unfreeze all mlb"). A line that
# still states it -- an issue body, a log line, a prompt, a comment that
# reads as a current rule -- is scanned for; a struck (`~~`) line, or one
# that says the freeze was lifted, is history and is allowed.
FROZEN = re.compile(r"(?i)mlb\s+(is|stays|remains)\s+frozen|do not touch mlb|"
                    r"mlb perfected|claude\.md`?\s+freezes|the mlb freeze\b")


def frozen_lines(lines):
    return [ln for ln in lines if FROZEN.search(ln)
            and "~~" not in ln and "lifted" not in ln.lower()]


ck("⚠️ the scanner catches a planted claim and passes struck history",
   frozen_lines(['msg = "Football only; MLB is frozen."',
                 "# ~~MLB IS FROZEN~~ (lifted 2026-09-22)",
                 "# Sam lifted the MLB freeze"]) == ['msg = "Football only; MLB is frozen."'],
   "rule 67: a scanner that finds nothing on a planted line proves nothing")
_files = sorted(p for p in glob.glob(os.path.join(ROOT, "*.py"))
                if not os.path.basename(p).startswith("test_"))
_bad = []
for _p in _files:
    for _i, _ln in enumerate(open(_p, encoding="utf-8").read().splitlines(), 1):
        if frozen_lines([_ln]):
            _bad.append("%s:%d: %s" % (os.path.basename(_p), _i, _ln.strip()[:100]))
ck("⚠️ it scanned the product code (%d files)" % len(_files), len(_files) >= 50,
   "rule 67")
ck("🔴 no product file still says MLB is frozen", not _bad, "\n".join(_bad[:10]))
