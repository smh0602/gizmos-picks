#!/usr/bin/env python3
"""T65's college data (research/fb_refit_spec.md): challenger P's ppa from the
/plays sweep, 2025's one back-fill sweep, and challenger T's /talent.
Planted /plays rows and a stub CFBD. ⛔ No call leaves this file and nothing is
written under data/ (cfb.OUT is a temp directory).

# @vacuity 🔴 only a ppa that is a number counts
#   file: cfb.py
#   find:                     if isinstance(v, (int, float)) and not isinstance(v, bool):
#   with:                     if v is not None:
#
# @vacuity 🔴 ...summed per offence per game
#   file: cfb.py
#   find:                         ppa_sum[(str(gid), off)][0] += v
#   with:                         ppa_sum[(str(gid), off)][0] = v
#
# @vacuity 🔴 the 2025 sweep runs only while its file is missing
#   file: cfb.py
#   find:     if os.path.exists(os.path.join(OUT, f"ppa-{season}.json.gz")):
#   with:     if False:
#
# @vacuity 🔴 ...priced first: a refused 2025 sweep fetches nothing
#   file: cfb.py
#   find:         return "refused: %s" % price["why"]
#   with:         pass
#
# @vacuity 🔴 ...and a partial sweep writes nothing
#   file: cfb.py
#   find:     if doc.get("fetch_failures") or not doc.get("games"):
#   with:     if not doc.get("games"):
#
# @vacuity 🔴 a refused /talent never raises, and leaves a DIAGNOSTIC
#   file: cfb.py
#   find:         why = "%s: %s" % (type(e).__name__, str(e)[:300])
#   with:         raise
#
# @vacuity 🔴 ...and is not asked again for 7 days
#   file: cfb.py
#   find:         if old > (now - datetime.timedelta(days=TALENT_RETRY_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ"):
#   with:         if False:
"""
import atexit
import datetime
import gzip
import json
import os
import shutil
import sys
import tempfile
import urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import cfb  # noqa: E402
import cfbd_budget  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

TMP = tempfile.mkdtemp(prefix="cfbppa-")
atexit.register(lambda: shutil.rmtree(TMP, ignore_errors=True))
cfb.OUT = TMP
cfb.time.sleep = lambda s: None
cfbd_budget.preflight = lambda calls, purpose, latest, root=None: {"allowed": True, "why": "planted"}
QUIET = lambda *a, **k: None  # noqa: E731
NOW = datetime.datetime(2026, 10, 14, 6, 0, tzinfo=datetime.timezone.utc)
CALLS = []


def play(gid, off, n, ppa):
    return {"gameId": gid, "offense": off, "period": 1, "playNumber": n, "driveId": "%s-%s" % (gid, off),
            "driveNumber": 1, "clock": {"minutes": 10, "seconds": n}, "minutes": 10, "seconds": n,
            "playType": "Rush", "playText": "run", "ppa": ppa}


PLAYS = [play(101, "Alabama", 1, 0.5), play(101, "Alabama", 2, -0.25), play(101, "Alabama", 3, None),
         play(101, "Alabama", 4, "0.9"), play(101, "Auburn", 5, 1.0), play(102, "Alabama", 6, 0.125)]


def plays_get(path, params=None, **kw):
    CALLS.append((path, dict(params or {})))
    if path != "/plays":
        raise AssertionError(path)
    if params.get("seasonType") == "regular" and params.get("week") in ("1", "2"):
        return PLAYS if params["week"] == "1" else [play(103, "Georgia", 7, 0.0)]
    return []


cfb.get = plays_get

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 P'S PPA RIDES THE /plays SWEEP: SUM AND COUNT PER OFFENCE PER GAME")
# ══════════════════════════════════════════════════════════════════════
doc = {}
cfb.build_pace(2026, log=QUIET, ppa=doc)
eq(doc["games"]["101"], {"Alabama": {"ppa_sum": 0.25, "plays_with_ppa": 2},
                         "Auburn": {"ppa_sum": 1.0, "plays_with_ppa": 1}},
   "🔴 game 101: Alabama 0.5 - 0.25 over the 2 plays that carry a number (None and \"0.9\" do not)")
eq((doc["games"]["102"]["Alabama"], doc["games"]["103"]["Georgia"]["plays_with_ppa"]),
   ({"ppa_sum": 0.125, "plays_with_ppa": 1}, 1), "   ...and every other game its own")
ck(doc["season"] == 2026 and doc["kind"] == "DESCRIPTIVE" and bool(doc["built_at"]) and doc["cfbd_calls"] == len(CALLS),
   "   ...with the stamped header, and the calls are the sweep's own (zero extra)", doc["cfbd_calls"])

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 2025: ONE SWEEP, ONLY WHILE ppa-2025 IS MISSING")
# ══════════════════════════════════════════════════════════════════════
_allow = cfbd_budget.preflight
cfbd_budget.preflight = lambda calls, purpose, latest, root=None: {"allowed": False, "why": "planted refusal"}
del CALLS[:]
got = cfb.backfill_ppa(2025, QUIET)
cfbd_budget.preflight = _allow
ck(got.startswith("refused") and not CALLS and not os.path.exists(os.path.join(TMP, "ppa-2025.json.gz")),
   "🔴 a 2025 sweep the budget refuses makes no call and writes nothing", (got, len(CALLS)))
del CALLS[:]
got = cfb.backfill_ppa(2025, QUIET)
n1 = len(CALLS)
with gzip.open(os.path.join(TMP, "ppa-2025.json.gz"), "rt", encoding="utf-8") as fh:
    on_disk = json.load(fh)
ck(got.startswith("written") and n1 >= 4 and on_disk["season"] == 2025 and bool(on_disk.get("written_at")),
   "🔴 a missing ppa-2025 costs one sweep (%d calls) and is written, stamped" % n1, got)
eq(cfb.SPENT.get("ppa back-fill 2025"), n1, "   ...and its calls go into the quota record")
del CALLS[:]
eq((cfb.backfill_ppa(2025, QUIET), len(CALLS)), ("already stored", 0), "🔴 ...and never again")
os.remove(os.path.join(TMP, "ppa-2025.json.gz"))
_good = cfb.get
cfb.get = lambda path, params=None, **kw: (_ for _ in ()).throw(OSError("down")) \
    if params.get("week") == "2" else _good(path, params)
got = cfb.backfill_ppa(2025, QUIET)
cfb.get = _good
ck(got.startswith("not written") and not os.path.exists(os.path.join(TMP, "ppa-2025.json.gz")),
   "🔴 a sweep with a failed week writes nothing, so it is asked again next run", got)

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 /talent: ONCE A SEASON, AND A REFUSAL NEVER RAISES")
# ══════════════════════════════════════════════════════════════════════
asked = []


def refuse(path, params):
    asked.append(path)
    raise urllib.error.HTTPError("https://api/talent", 401, "Unauthorized", {}, None)


cfb._counted_get = refuse
try:
    got, raised = cfb.fetch_talent(2026, QUIET, NOW), None
except BaseException as e:            # noqa: B902 — the guard is that nothing escapes
    got, raised = None, e
probe = cfb._read_json(os.path.join(TMP, "talent-probe-2026.json"))
ck(raised is None and got.startswith("DIAGNOSTIC") and probe.get("kind") == "DIAGNOSTIC"
   and "401" in probe.get("error", "") and not os.path.exists(os.path.join(TMP, "talent-2026.json.gz")),
   "🔴 CFBD refusing /talent raises nothing, writes a DIAGNOSTIC and no talent file", (got, raised, probe))
eq((cfb.fetch_talent(2026, QUIET, NOW + datetime.timedelta(days=3))[:7], asked),
   ("refused", ["/talent"]), "🔴 ...and it is not asked again for 7 days")
cfb._counted_get = lambda path, params: asked.append(path) or [
    {"year": 2026, "team": "Alabama", "talent": "981.2"}, {"year": 2026, "school": "Auburn", "talent": 900},
    {"year": 2026, "team": "Nowhere", "talent": None}]
got = cfb.fetch_talent(2026, QUIET, NOW + datetime.timedelta(days=8))
with gzip.open(os.path.join(TMP, "talent-2026.json.gz"), "rt", encoding="utf-8") as fh:
    tal = json.load(fh)
eq((got, tal["teams"], tal["season"]), ("written (2 teams)", {"Alabama": 981.2, "Auburn": 900.0}, 2026),
   "🔴 after 7 days it asks once more and stores each team's number")
eq((cfb.fetch_talent(2026, QUIET, NOW + datetime.timedelta(days=9)), len(asked)), ("already stored", 2),
   "🔴 ...and never again for that season")
