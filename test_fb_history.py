#!/usr/bin/env python3
r"""T70 — MORE SEASONS (research/fb_refit_spec.md §3d): fb_history.py and the H / HC
challengers. `[Sam, 2026-10-15]` "do all changes". Planted trees and fake sources.
⛔ Reads no live data, makes no network call.

# @vacuity 🔴 Oakland is stored as Las Vegas
#   file: fb_history.py
#   find: ALIAS = {"OAK": "LV"}                                        # ⛔ §3d: Oakland became Las Vegas in 2020
#   with: ALIAS = {}                                        # ⛔ §3d: Oakland became Las Vegas in 2020
#
# @vacuity 🔴 a written history file carries a stamp the contract reads
#   file: fb_history.py
#   find: json.dump(dict(doc, written_at=_stamp()), fh, separators=(",", ":"))
#   with: json.dump(doc, fh, separators=(",", ":"))
#
# @vacuity 🔴 an unstamped stored file is stamped in place
#   file: fb_history.py
#   find: if _F.stamp_of(p) is not None:
#   with: if True:
#
# @vacuity 🔴 a stamp write cut short leaves the stored file whole (the write is atomic)
#   file: fb_history.py
#   find:     tmp = p + ".tmp"
#   with:     tmp = p
#
# @vacuity 🔴 a stored file whose stamp the contract cannot read is stamped (one reader)
#   file: fb_history.py
#   find: if _F.stamp_of(p) is not None:
#   with: if any(doc.get(k) for k in ("pulled_at", "built_at", "generated_at", "written_at")):
#
# @vacuity 🔴 one failing NFL season never stops the others
#   file: fb_history.py
#   find:             out[s] = "failed: %s: %s" % (type(e).__name__, str(e)[:200])
#   with:             raise
#
# @vacuity 🔴 [review, 2026-11-17] the real nflverse path never clobbers the end-of-run record (it raised)
#   file: fb_history.py
#   find:                     rel = {r["tag_name"]: [(a["name"], a["size"], a["browser_download_url"])
#   with:                     ends = rel = {r["tag_name"]: [(a["name"], a["size"], a["browser_download_url"])
#
# @vacuity 🔴 a refused CFBD history call fetches nothing
#   file: fb_history.py
#   find:                 if not _cfb._priced(calls, "history %s %d" % (kind, s), log):
#   with:                 if False:
#
# @vacuity 🔴 CFBD's spread is the home handicap, stored as the home margin
#   file: fb_history.py
#   find:             out[str(g.get("id"))] = {"spread": -float(ln["spread"]), "total": float(ln["overUnder"]),
#   with:             out[str(g.get("id"))] = {"spread": float(ln["spread"]), "total": float(ln["overUnder"]),
#
# @vacuity 🔴 one line per game by t60r's provider order
#   file: fb_history.py
#   find:             if best is None or rank < best[0]:
#   with:             if True:
#
# @vacuity 🔴 H's ratings read the history seasons
#   file: fb_challengers.py
#   find:     G = sorted(set(FM.rating_games(lg, root)) | set(history_rating_games(lg, root)))
#   with:     G = sorted(set(FM.rating_games(lg, root)))
#
# @vacuity 🔴 college history rows are FBS vs FBS
#   file: fb_challengers.py
#   find:                 or (lg == "ncaaf" and not (g.get("home_class") == "fbs" and g.get("away_class") == "fbs"))):
#   with:                 or False):
#
# @vacuity 🔴 the contest trains H on the history rows
#   file: fb_refit.py
#   find:     extra = FC.history_rows(lg, root) if FC.CHALLENGERS[name].get("history") else []
#   with:     extra = []
#
# @vacuity 🔴 the daily runs write history into their own tree, never the module's folder
#   file: collect.py
#   find:                 _fh.store_nfl(log, root=".")  # ⛔ this run's own tree (a test runs it from a copy)
#   with:                 _fh.store_nfl(log)  # ⛔ this run's own tree (a test runs it from a copy)
#
# @vacuity 🔴 a history file is stored-only for freshness
#   file: freshness.py
#   find:                          r"|/history/(schedule|lines)-\d{4}\.json\.gz$")
#   with:                          r"|/nowhere/x$")
#
# `[2026-11-17]` A STORED FILE THAT CANNOT BE READ (§4, §5).
# @vacuity 🔴 a truncated gzip is corrupt, never a crash (EOFError)
#   file: fb_history.py
#   find: except (EOFError, zlib.error, OSError, ValueError) as e:
#   with: except (OSError, ValueError) as e:
#
# @vacuity 🔴 a readable file with no games is corrupt too (the reader's and the contract's one test)
#   file: freshness.py
#   find: if not isinstance(doc, dict) or not doc.get("games"):
#   with: if not isinstance(doc, dict):
#
# @vacuity 🔴 ...and so is one whose games are not its kind's shape (lines: a dict)
#   file: freshness.py
#   find: if not isinstance(doc["games"], want):
#   with: if False:
#
# @vacuity 🔴 lines() never raises on an unreadable file (it reads through the one reader)
#   file: fb_history.py
#   find: got = (_stored(p)[0] or {}).get("games")
#   with: got = json.load(gzip.open(p, "rt", encoding="utf-8")).get("games")
#
# @vacuity 🔴 store_nfl rebuilds an unreadable season (it saw a file and moved on)
#   file: fb_history.py
#   find: if state == "present":               # NFL: a readable file is never rebuilt
#   with: if os.path.exists(p):               # NFL: a readable file is never rebuilt
#
# @vacuity 🔴 store_cfb rebuilds an unreadable file (it saw a file and moved on)
#   file: fb_history.py
#   find: if state == "present":               # college: a readable file costs no call
#   with: if os.path.exists(p):               # college: a readable file costs no call
#
# @vacuity 🔴 NFL: the unreadable file is moved aside, never overwritten
#   file: fb_history.py
#   find: moved = _aside(p) if state == "corrupt" else None     # NFL: once the new one is in hand
#   with: moved = None     # NFL: once the new one is in hand
#
# @vacuity 🔴 college: the unreadable file is moved aside, never overwritten
#   file: fb_history.py
#   find: moved = _aside(p) if state == "corrupt" else None     # college: once the new one is in hand
#   with: moved = None     # college: once the new one is in hand
#
# @vacuity 🔴 a file the contract still reads stale after its writer ran is named for the contract's hold
#   file: fb_history.py
#   find: if _landed(path):
#   with: if True:
#
# @vacuity 🔴 college: an unstamped readable file is stamped in place too, at no CFBD call (rule 6)
#   file: fb_history.py
#   find: got = _stamp_once(p, doc0)   # `[review, 2026-11-17]` ...only stamped, when it has none
#   with: got = None   # `[review, 2026-11-17]` ...only stamped, when it has none
#
# @vacuity 🔴 the contract plans a stamped history file with no games (its HEALTH asks the reader's test)
#   file: freshness.py
#   find: (re.compile(r"/(?:nfl|ncaaf)/history/(?:schedule|lines)-\d{4}\.json\.gz$"), _history_health),
#   with: (re.compile(r"/nowhere/x$"), _history_health),
#
# @vacuity 🔴 H / HC never train on part of their seasons
#   file: fb_challengers.py
#   find: need_history(lg, root)
#   with: None
#
# @vacuity 🔴 ...an unreadable season counts, not only a missing one
#   file: fb_challengers.py
#   find: if st != "present"]
#   with: if st == "missing"]
#
# @vacuity 🔴 a champion's declared history files are its inputs (never stored only)
#   file: freshness.py
#   find: for f in c.get("files") or ():
#   with: for f in ():
#
# @vacuity 🔴 ...one row each (the stored-only row gives way)
#   file: freshness.py
#   find: continue                 # `[2026-11-17]` the champion's input (H, HC): its row is above
#   with: pass                 # `[2026-11-17]` the champion's input (H, HC): its row is above
#
# @vacuity 🔴 a rebuild that did not land is held (never a CFBD sweep every pass)
#   file: freshness.py
#   find: held = rebuild_held(r["path"], now, due.get(r["mode"])) if r["stale"] and r["kind"] == "file" else None
#   with: held = None
#
# @vacuity 🔴 ...a held row is not owed
#   file: freshness.py
#   find: and not r.get("held")              # `[2026-11-17]` REBUILD_ATTEMPTS: its writer's next deadline
#   with: and True              # `[2026-11-17]` REBUILD_ATTEMPTS: its writer's next deadline
#
# @vacuity 🔴 ...until its writer's own next deadline, then owed (that deadline's one run retries it)
#   file: freshness.py
#   find: if due is not None and due > when:
#   with: if False:
#
# @vacuity 🔴 ...and never released before it: a fixed 20 h released it at 03:10Z, two CFBD sweeps a day
#   file: freshness.py
#   find: if due is not None and due > when:
#   with: if age >= 20 * 60:
#
# @vacuity 🔴 ...and a writer no deadline releases is retried every 2 days at most
#   file: freshness.py
#   find: if not 0 <= age < REBUILD_RETRY_MAX_MIN:
#   with: if not 0 <= age:
#
# @vacuity 🔴 ...and a late cron stands down past a held row
#   file: freshness.py
#   find: mine = [r for r in rows if r["mode"] == mode and not r.get("held")]
#   with: mine = [r for r in rows if r["mode"] == mode]
"""
import atexit
import gzip
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
import cfb  # noqa: E402
import fb_challengers as FC  # noqa: E402
import fb_history as HX  # noqa: E402
import fb_model as FM  # noqa: E402
import fb_refit as R  # noqa: E402
import freshness as F  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])


def tree():
    t = tempfile.mkdtemp(prefix="fbhist-")
    TREES.append(t)
    return t.replace("\\", "/")


def put(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        json.dump(doc, fh)


def g(gid, day, home, away, hs, as_, **k):
    return dict({"id": gid, "start": day + "T17:00", "home": home, "away": away, "final": True,
                 "home_score": hs, "away_score": as_, "neutral": False, "roof": "outdoors",
                 "closing_spread": 3.0, "closing_total": 44.5, "closing_ml_home": -150,
                 "closing_ml_away": 130}, **k)


quiet = lambda m: None  # noqa: E731


def fill(root, name):
    """Plant every history file challenger `name` declares that the tree lacks, readable and
    adding no training row (a game not yet final; a line for a game no schedule holds)."""
    for p in FC.history_files(name, root):
        if not os.path.exists(p):
            s = int(os.path.basename(p).split("-")[1][:4])
            put(root, os.path.relpath(p, root), {"season": s, "written_at": "2026-10-15T00:00:00Z", "games": (
                {"x%d" % s: {"spread": 1.0, "total": 40.0, "ml_home": None, "ml_away": None}}
                if os.path.basename(p).startswith("lines-") else
                [g("x%d" % s, "%d-09-01" % s, "ZZ1", "ZZ2", 0, 0, final=False)])})


def attempts(root, lg):
    """The files a run could not land (fb_history.ATTEMPTS), {} when none is recorded."""
    try:
        return json.load(open(os.path.join(root, "data", lg, "history", HX.ATTEMPTS), encoding="utf-8"))["files"]
    except (OSError, ValueError, KeyError):
        return {}

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 STORING THE HISTORY: ONCE, OUTSIDE latest/, NEVER RAISING")
# ══════════════════════════════════════════════════════════════════════
T = tree()


def build(s):
    if s == 2019:
        raise RuntimeError("nflverse hiccup")
    return {"season": s, "games": [g("%d_1" % s, "%d-10-06" % s, "OAK", "SEA", 20, 17)]}


res = HX.store_nfl(quiet, T, build=build)
ck(res[2019].startswith("failed") and res[2018].startswith("written") and res[2024].startswith("written"),
   "🔴 every missing NFL season is written once; one that fails is named and the others go on", res)
ck(os.path.exists(T + "/data/nfl/history/schedule-2018.json.gz")
   and not os.path.exists(T + "/data/nfl/latest/schedule-2018.json.gz"),
   "🔴 ...into data/nfl/history/, never latest/ (the champion's ratings are untouched)")
eq(json.load(gzip.open(T + "/data/nfl/history/schedule-2018.json.gz", "rt"))["games"][0]["home"], "LV",
   "🔴 Oakland is stored as LV, so 2018-19 and 2020+ are one team")
eq(sorted(HX.store_nfl(quiet, T, build=build)), [2019], "   ...and the next run only retries the missing season")
# `[2026-10-27]` THE CONTRACT READS A FILE'S OWN STAMP: the seven stored NFL schedules carried none,
#    so all seven read MISSING from 10-16 on and health.json held a standing `fresh:nfl` DEGRADED.
ck(F.stamp_of(T + "/data/nfl/history/schedule-2018.json.gz") is not None,
   "🔴 a written history file carries a stamp the contract reads (freshness.stamp_of)")
# `[review, 2026-11-17]` THE REAL nflverse PATH (build=None), not only a planted `build`: a rename gave
#    the release table the end-of-run record's name, and store_nfl raised ValueError out of
#    _record_attempts on every run that had a season to fetch (nfl-logs red). The nfl module is
#    faked (no network): its release table, its rows, and its build_schedule, 2019 failing.
_nfl_real, _nfl_seen = sys.modules.get("nfl"), {"releases": 0, "rows": []}
_fake_nfl = type(sys)("nfl")
_fake_nfl.SCHEDULE_FILE = "games.csv.gz"
_fake_nfl._releases = lambda log=print, max_pages=10: _nfl_seen.__setitem__("releases", _nfl_seen["releases"] + 1) or [
    {"tag_name": "schedules", "assets": [{"name": "games.csv.gz", "size": 9, "browser_download_url": "x"}]}]
_fake_nfl._rows = lambda seen, tag, fname, log: _nfl_seen["rows"].append((seen, tag, fname)) or [{"r": 1}]


def _fake_schedule(s, seen=None, log=print, lines=None, rows=None, root=None):
    if s == 2019:
        raise RuntimeError("nflverse hiccup")
    return {"season": s, "games": [g("%d_n" % s, "%d-10-06" % s, "OAK", "SEA", 20, 17)]}, {}


_fake_nfl.build_schedule = _fake_schedule
_tn = tree()
sys.modules["nfl"] = _fake_nfl
try:
    try:
        _resn, _errn = HX.store_nfl(quiet, _tn), None
    except Exception as e:        # noqa: BLE001
        _resn, _errn = None, e
finally:
    if _nfl_real is None:
        sys.modules.pop("nfl", None)
    else:
        sys.modules["nfl"] = _nfl_real
ck(_errn is None and sorted(s for s, v in (_resn or {}).items() if str(v).startswith("written")) ==
   [2018, 2020, 2021, 2022, 2023, 2024] and str(_resn[2019]).startswith("failed: RuntimeError")
   and list(attempts(_tn, "nfl")) == ["schedule-2019.json.gz"] and _nfl_seen["releases"] == 1
   and [(sorted(x[0]), x[1], x[2]) for x in _nfl_seen["rows"]] == [(["schedules"], "schedules", "games.csv.gz")],
   "🔴 the real nflverse path (no planted build): never raises, the release table read once, 6 seasons "
   "written, the failing one named in rebuild-attempts.json and nothing else in it",
   repr(_errn) if _errn else (_resn, attempts(_tn, "nfl"), _nfl_seen["releases"]))
_u = tree()
put(_u, "data/nfl/history/schedule-2020.json.gz",
    {"season": 2020, "kind": "DESCRIPTIVE", "history": True, "games": [g("2020_1", "2020-10-04", "LV", "KC", 1, 2)]})
_before = json.load(gzip.open(_u + "/data/nfl/history/schedule-2020.json.gz", "rt"))
_res = HX.store_nfl(quiet, _u, build=lambda s: {"season": s, "games": [g("x", "%d-10-06" % s, "NE", "NYJ", 1, 0)]})
_after = json.load(gzip.open(_u + "/data/nfl/history/schedule-2020.json.gz", "rt"))
ck(str(_res.get(2020)).startswith("stamped") and F.stamp_of(_u + "/data/nfl/history/schedule-2020.json.gz")
   and {k: v for k, v in _after.items() if k != "written_at"} == _before,
   "🔴 an UNSTAMPED stored file is stamped in place once, its games untouched (never re-fetched)",
   _res.get(2020))
eq(HX.store_nfl(quiet, _u, build=build).get(2020), None, "   ...and the next run leaves it alone")
# `[review, 2026-10-27]` stamped is what the CONTRACT reads, not a key being present: a stamp
#    it cannot parse is stamped again, once.
put(_u, "data/nfl/history/schedule-2021.json.gz",
    {"season": 2021, "built_at": "n/a", "games": [g("2021_1", "2021-10-03", "LV", "KC", 1, 2)]})
_res = HX.store_nfl(quiet, _u, build=build)
ck(str(_res.get(2021)).startswith("stamped") and F.stamp_of(_u + "/data/nfl/history/schedule-2021.json.gz"),
   "🔴 a stored file whose stamp the contract cannot read is stamped (freshness.stamp_of, one reader)",
   _res.get(2021))
# ...and a stamp that cannot be written is named, never raised, and leaves the file whole.
put(_u, "data/nfl/history/schedule-2022.json.gz",
    {"season": 2022, "games": [g("2022_1", "2022-10-02", "LV", "KC", 1, 2)]})
_p22 = _u + "/data/nfl/history/schedule-2022.json.gz"
_raw22 = open(_p22, "rb").read()
_dump = HX.json.dump


def _cut(*a, **k):
    a[1].write('{"season": 20')
    raise OSError("disk full")


HX.json.dump = _cut
try:
    _res = HX.store_nfl(quiet, _u, build=build)
    _raised = None
except Exception as e:        # noqa: BLE001
    _raised = e
finally:
    HX.json.dump = _dump
ck(_raised is None and str(_res.get(2022)).startswith("failed: OSError")
   and open(_p22, "rb").read() == _raw22 and not os.path.exists(_p22 + ".tmp"),
   "🔴 a stamp write cut short is named and never raised; the stored file is byte-identical and "
   "no temporary file is left (the write is atomic)", (_raised, _res.get(2022) if _raised is None else None))

_old = (cfb._priced, cfb.build_schedule, cfb.get)
asked, allow = [], {"v": False}
try:
    cfb._priced = lambda calls, purpose, log=None: allow["v"]
    cfb.build_schedule = lambda s, log=None: (asked.append(("games", s)) or
                                              ({"season": s, "games": [g("c%d" % s, "%d-09-06" % s, "A", "B", 1, 0)]}, {}))
    cfb.get = lambda path, params, timeout=90, tries=4: asked.append((path, params["year"])) or [
        {"id": 7, "lines": [{"provider": "consensus", "spread": -3.0, "overUnder": 51.5, "homeMoneyline": -160,
                             "awayMoneyline": 135},
                            {"provider": "DraftKings", "spread": -3.5, "overUnder": 50, "homeMoneyline": -170,
                             "awayMoneyline": 145}]}]
    C = tree()
    out = HX.store_cfb(quiet, C)
    # `[2026-11-17]` ~~"and writes nothing" (no history folder at all)~~: a refusal now names each
    #    file it could not land in ATTEMPTS (the contract's hold, §5), and writes no history file.
    ck(set(out.values()) == {"refused"} and not asked
       and os.path.isdir(C + "/data/ncaaf/history") and os.listdir(C + "/data/ncaaf/history") == [HX.ATTEMPTS]
       and {k: v["outcome"] for k, v in attempts(C, "ncaaf").items()}
       == {"%s.json.gz" % k: "refused" for k in out},
       "🔴 a refused CFBD history call fetches nothing and writes no history file: only the refusals, "
       "named for the contract's hold", out)
    allow["v"] = True
    out = HX.store_cfb(quiet, C)
    L = HX.lines(C)
    eq((sorted(out), L.get("7")), (["lines-2023", "lines-2024", "schedule-2023", "schedule-2024"],
                                   {"spread": 3.0, "total": 51.5, "ml_home": -160, "ml_away": 135,
                                    "provider": "consensus"}),
       "🔴 allowed: schedules and lines stored; one line per game by t60r's provider order (consensus first), "
       "CFBD's home handicap -3 stored as the home margin +3")
finally:
    cfb._priced, cfb.build_schedule, cfb.get = _old

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 H / HC: RATINGS AND TRAINING ROWS OVER THE HISTORY SEASONS")
# ══════════════════════════════════════════════════════════════════════
H = tree()
put(H, "data/nfl/latest/schedule-2025.json.gz", {"season": 2025, "games": [g("n1", "2025-09-07", "SEA", "DEN", 0, 0, final=False)]})
put(H, "data/nfl/history/schedule-2024.json.gz", {"season": 2024, "games": [
    g("h%d" % i, "2024-%02d-%02d" % (9 + i // 4, 1 + 7 * (i % 4)), "SEA" if i % 2 else "DEN", "DEN" if i % 2 else "SEA",
      30 if i % 2 else 17, 13 if i % 2 else 24) for i in range(8)]})
row = {"id": "n1", "lg": "nfl", "season": 2025, "day": "2025-09-07", "home": "SEA", "away": "DEN", "M": 3.0, "T": 44.5,
       "final": False, "sig": {"neutral": 0.0, "dome": 0.0}}
champ_own = FM.own_numbers(FM.own_ratings(FM.rating_games("nfl", H), {"2025-09-01"}).get("2025-09-01"), "SEA", "DEN", 0.0)
FC.attach("H", "nfl", [row], H)
ck(champ_own == (None, None) and row["sig"]["h_own"][0] is not None and row["sig"]["h_own"][0] > 0,
   "🔴 week 1 of 2025: the champion has no earlier game for SEA, H rates SEA from 2024 (and above DEN)",
   (champ_own, row["sig"]["h_own"]))
eq([round(v, 6) for v in FC.extend("H", row, "spread", ["ignored"])],
   [round((row["sig"]["h_own"][0] - 3.0) / 10, 6), 0.0, 0.0],
   "🔴 H's inputs are the own term, neutral and dome only (the champion's others don't exist for history)")
fill(H, "H")       # `[2026-11-17]` H trains on every declared season or none (need_history)
hr = FC.history_rows("nfl", H)
eq((len(hr), hr[0]["M"], hr[0]["T"], hr[0]["final"]), (8, 3.0, 44.5, True),
   "🔴 one training row per final history game, labelled at its closing line by fb_model.training_line")
fits = R.challenger_fits([row], "H", "nfl", H)
eq((len(fits.rows), len(R.challenger_fits([row], "S", "nfl", H).rows)), (9, 1),
   "🔴 the contest trains H on the current rows plus the history rows; every other challenger on the current rows")
CC = tree()
put(CC, "data/ncaaf/history/schedule-2024.json.gz", {"season": 2024, "games": [
    g("f1", "2024-09-07", "A", "B", 30, 20, home_class="fbs", away_class="fbs"),
    g("f2", "2024-09-07", "C", "D", 50, 0, home_class="fbs", away_class="fcs")]})
fill(CC, "HC")
eq([r["id"] for r in FC.history_rows("ncaaf", CC)], ["hist:f1"], "🔴 college history rows are FBS vs FBS only")
# `[2026-10-15]` caught by the sweep's leak check: a test running `collect.py nfl-logs` from a
#    copy wrote data/nfl/history/ into the repo, because the writer defaulted to its own folder.
ck('_fh.store_nfl(log, root=".")' in open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
   and '_fh.store_cfb(log, root=".")' in open(os.path.join(ROOT, "cfb.py"), encoding="utf-8").read(),
   "🔴 the daily runs write the history into their own tree (the collector's working directory)")
ck('if fb_challengers.CHALLENGERS[CHAMPION[lg]].get("history"):' in open(os.path.join(ROOT, "fb_model.py"),
                                                                         encoding="utf-8").read(),
   "   a champion H trains on the history rows too (fb_model.build_rows)")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 REGISTRATION, COUNTS, FRESHNESS")
# ══════════════════════════════════════════════════════════════════════
eq(R.registration("H", T), None, "🔴 H is not registered while any history season's file is missing (2019 here)")
eq(R.registration("H", T, {"H": "2026-10-20"}), "2026-10-26", "   ...and once they all exist, the next Monday")
# `[Sam, 2026-10-16]` ~~8 challengers a league, p < 0.01 / 8~~: T71 (§3e) adds SM, SMC.
# `[Sam, 2026-10-26]` ~~9 challengers a league, p < 0.01 / 9~~: T72 (§3f) adds CL, WL, MC, AJ and
#    CLC, WLC, MCC, AJC.
# `[Sam, 2026-11-10]` ~~13 challengers a league, p < 0.01 / 13~~: T75 (§3k) adds QB, QP and QBC, QPC.
eq({lg: sum(1 for c in FC.CHALLENGERS.values() if c["league"] == lg) for lg in ("nfl", "ncaaf")},
   {"nfl": 15, "ncaaf": 15}, "🔴 15 challengers a league, p < 0.01 / 15")
P = tree()
rows = F.contract(P + "/data/nfl", P + "/picks", None)
hist = [r for r in rows if "/history/" in r[1][1]]
ck(len(hist) == 7 and all(r[0] == "nfl-logs" and r[2] == [] and F.stored_only({"path": r[1][1]}) for r in hist),
   "🔴 a freshness row per NFL history season, by the daily nfl-logs run, late only when missing, stored-only "
   "(never a red run, never a planned rebuild)", [r[1][1] for r in hist][:2])
# `[2026-10-17]` ~~every /history/ row~~: college injuries' conference archives
#    live there too (test_cfb_injuries_wiring.py); this counts T70's own.
eq(len([r for r in F.contract(P + "/data/ncaaf", P + "/picks", None)
        if "/history/schedule-" in r[1][1] or "/history/lines-" in r[1][1]]), 4,
   "   ...and college's 2 seasons x schedule and lines")


# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 A HISTORY FILE THAT CANNOT BE READ IS REBUILT, AND H / HC NEVER TRAIN ON PART OF IT")
# ══════════════════════════════════════════════════════════════════════
# `[2026-11-17]` The reader caught only OSError / ValueError: a truncated gzip raised EOFError out
#    of games() and lines() (the module said "Never raises"), a bad-JSON file read as None while
#    store_nfl / store_cfb saw a file and moved on, so neither was ever rebuilt; and HC, the live
#    college champion, either crashed its build or trained on one season of two (798 rows of
#    1,590, on copies of the real files, 2026-11-13). Planted files, fake sources, no network.
def raw(root, rel, b):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as fh:
        fh.write(b)
    return p


def cut(doc, n=40):
    """A gzip written `n` bytes and stopped: a write cut short."""
    return gzip.compress(json.dumps(doc).encode("utf-8"))[:n]


def aside(root, lg):
    d = os.path.join(root, "data", lg, "history", HX.CORRUPT_DIR)
    return sorted(os.listdir(d)) if os.path.isdir(d) else []


B = tree()
fill(B, "H")
_np = {s: os.path.join(B, "data", "nfl", "history", "schedule-%d.json.gz" % s) for s in HX.NFL_SEASONS}
raw(B, "data/nfl/history/schedule-2020.json.gz", cut({"season": 2020, "games": [g("a", "2020-10-04", "LV", "KC", 1, 2)]}))
raw(B, "data/nfl/history/schedule-2021.json.gz", gzip.compress(b'{"season": 2021, "games": ['))
put(B, "data/nfl/history/schedule-2022.json.gz", {"season": 2022, "games": []})
# `[review, 2026-11-17]` ...and college lines in the same tree, so lines() is asked too (it had been
#    reached only through history_rows, which refuses first): one readable, one truncated, and one
#    whose games are a list where lines keep a dict (lines() would skip it: HC on a subset).
put(B, "data/ncaaf/history/lines-2021.json.gz", {"season": 2021, "games": {"g21": {"spread": 1.0, "total": 40.0}}})
raw(B, "data/ncaaf/history/lines-2023.json.gz", cut({"season": 2023, "games": {"g23": {"spread": 2.0}}}))
put(B, "data/ncaaf/history/lines-2024.json.gz", {"season": 2024, "written_at": "2026-10-15T00:00:00Z",
                                                  "games": [{"g24": {"spread": 3.0}}]})
_was = {s: open(_np[s], "rb").read() for s in (2020, 2021, 2022)}
eq(dict({s: HX.state_of(_np[s]) for s in (2019, 2020, 2021, 2022)},
        **{"lines-%d" % s: HX.state_of(os.path.join(B, "data", "ncaaf", "history", "lines-%d.json.gz" % s))
           for s in (2021, 2023, 2024)}),
   {2019: "present", 2020: "corrupt: EOFError", 2021: "corrupt: JSONDecodeError", 2022: "corrupt: no games",
    "lines-2021": "present", "lines-2023": "corrupt: EOFError", "lines-2024": "corrupt: games is a list, not a dict"},
   "🔴 one reader names each stored file: present, or corrupt with why (a truncated gzip is EOFError, "
   "never a crash; games of the wrong shape are corrupt too)")
try:
    _g, _l, _err = HX.games("nfl", B), HX.lines(B), None
except Exception as e:        # noqa: BLE001
    _g, _l, _err = None, None, e
ck(_err is None and _g is not None and len(_g) == 4 and _l == {"g21": {"spread": 1.0, "total": 40.0}},
   "🔴 games() and lines() never raise on a truncated or bad file: they read the 4 readable schedules and "
   "the one readable lines file only", (_err, _l))
try:
    FC.history_rows("nfl", B)
    _hx = None
except Exception as e:        # noqa: BLE001
    _hx = e
ck(isinstance(_hx, FC.HistoryIncomplete) and all("schedule-%d" % s in str(_hx) for s in (2020, 2021, 2022))
   and "2019" not in str(_hx),
   "🔴 H never trains on part of its seasons: history_rows raises HistoryIncomplete naming the 3 unreadable "
   "files (not EOFError, and not 4 seasons of 7 in silence)", repr(_hx)[:300])
_built = []


def nfl_build(s):
    _built.append(s)
    if s == 2023 and _fail23["v"]:
        raise RuntimeError("nflverse hiccup")
    return {"season": s, "games": [g("r%d" % s, "%d-10-06" % s, "SEA", "DEN", 20, 17)]}


_fail23 = {"v": False}
_res = HX.store_nfl(quiet, B, build=nfl_build)
_moved = aside(B, "nfl")
ck(sorted(_built) == [2020, 2021, 2022]
   and all(str(_res[s]).startswith("rebuilt (was corrupt") for s in (2020, 2021, 2022))
   and all(HX.state_of(_np[s]) == "present" for s in HX.NFL_SEASONS),
   "🔴 store_nfl rebuilds exactly the 3 unreadable seasons (nflverse, free) and leaves 7 readable files",
   (_built, {s: _res.get(s) for s in (2020, 2021, 2022)}))
eq(sorted(open(os.path.join(B, "data/nfl/history", HX.CORRUPT_DIR, m), "rb").read() for m in _moved),
   sorted(_was.values()),
   "🔴 ...each old file moved aside byte for byte into history/%s/ (never deleted)" % HX.CORRUPT_DIR)
ck(len(_moved) == 3 and not any(m.endswith(".json.gz") for m in _moved) and len(HX.games("nfl", B)) == 7,
   "   ...under a name no reader globs (not .json.gz, in its own folder): games() reads the 7 seasons only",
   _moved)
ck(len(FC.history_rows("nfl", B)) == 3, "   ...and H trains again, on every season (3 rebuilt finals)")
_built.clear()
eq((HX.store_nfl(quiet, B, build=nfl_build), _built, aside(B, "nfl")), ({}, [], _moved),
   "   ...and the next run reads 7 good files: no build, nothing moved")
# a rebuild that cannot land leaves the unreadable file where it is, and is named for the contract
raw(B, "data/nfl/history/schedule-2023.json.gz", cut({"season": 2023, "games": []}))
_was23 = open(_np[2023], "rb").read()
_fail23["v"] = True
_res = HX.store_nfl(quiet, B, build=nfl_build)
_att = {"files": attempts(B, "nfl")}
ck(str(_res.get(2023)).startswith("failed") and open(_np[2023], "rb").read() == _was23
   and aside(B, "nfl") == _moved and "schedule-2023.json.gz" in _att["files"],
   "🔴 a rebuild that fails moves nothing (the file stays, byte for byte) and is named in %s for the "
   "contract's hold" % HX.ATTEMPTS, (_res.get(2023), _att.get("files")))
_fail23["v"] = False
HX.store_nfl(quiet, B, build=nfl_build)
_att = {"files": attempts(B, "nfl")}
ck(HX.state_of(_np[2023]) == "present" and "schedule-2023.json.gz" not in _att["files"],
   "   ...and once a run lands it, it leaves the list", _att.get("files"))

# ── college: the same reader, every CFBD call priced first, none for a readable file ──
CB = tree()
put(CB, "data/ncaaf/history/schedule-2024.json.gz", {"season": 2024, "written_at": "2026-10-15T00:00:00Z", "games": [
    g("9", "2024-09-07", "A", "B", 30, 20, home_class="fbs", away_class="fbs")]})
fill(CB, "HC")
_cp = {k: os.path.join(CB, "data", "ncaaf", "history", "%s.json.gz" % k)
       for k in ("schedule-2023", "lines-2023", "schedule-2024", "lines-2024")}
_old = (cfb._priced, cfb.build_schedule, cfb.get)
priced, fetched, allow = [], [], {"v": True}
try:
    cfb._priced = lambda calls, purpose, log=None: priced.append((calls, purpose)) or allow["v"]
    cfb.build_schedule = lambda s, log=None: (fetched.append(("/games", s)) or
                                              ({"season": s, "games": [g("c%d" % s, "%d-09-06" % s, "A", "B", 1, 0)]}, {}))
    cfb.get = lambda path, params, timeout=90, tries=4: fetched.append((path, int(params["year"]))) or [
        {"id": 9, "lines": [{"provider": "consensus", "spread": -3.0, "overUnder": 51.5,
                             "homeMoneyline": -160, "awayMoneyline": 135}]}]
    eq((HX.store_cfb(quiet, CB), priced, fetched), ({}, [], []),
       "🔴 every college history file readable: store_cfb prices nothing and makes ZERO CFBD calls")
    raw(CB, "data/ncaaf/history/lines-2024.json.gz", cut({"season": 2024, "games": {"1": {}}}))
    _wasl = open(_cp["lines-2024"], "rb").read()
    try:
        FC.history_rows("ncaaf", CB)
        _hx = None
    except Exception as e:        # noqa: BLE001
        _hx = e
    ck(isinstance(_hx, FC.HistoryIncomplete) and "lines-2024" in str(_hx) and "schedule-2024" not in str(_hx),
       "🔴 HC never trains on part of its seasons: a truncated lines-2024 is HistoryIncomplete, named",
       repr(_hx)[:300])
    allow["v"] = False
    _res = HX.store_cfb(quiet, CB)
    _att = {"files": attempts(CB, "ncaaf")}
    ck(_res == {"lines-2024": "refused"} and priced == [(1, "history lines 2024")] and not fetched
       and open(_cp["lines-2024"], "rb").read() == _wasl and not aside(CB, "ncaaf")
       and "lines-2024.json.gz" in _att["files"],
       "🔴 refused by the CFBD price check: no call, the file stays byte for byte, and it is named for the "
       "contract's hold", (_res, priced, fetched))
    allow["v"], priced[:] = True, []
    _res = HX.store_cfb(quiet, CB)
    _att = {"files": attempts(CB, "ncaaf")}
    ck(str(_res.get("lines-2024")).startswith("rebuilt (was corrupt: EOFError")
       and priced == [(1, "history lines 2024")] and fetched == [("/lines", 2024)]
       and [open(os.path.join(CB, "data/ncaaf/history", HX.CORRUPT_DIR, m), "rb").read()
            for m in aside(CB, "ncaaf")] == [_wasl]
       and HX.state_of(_cp["lines-2024"]) == "present" and not _att["files"],
       "🔴 allowed: ONE priced call (/lines 2024), the old file moved aside byte for byte, the new one "
       "readable, the hold cleared", (_res, priced, fetched))
    eq([(r["id"], r["M"]) for r in FC.history_rows("ncaaf", CB)], [("hist:9", 3.0)],
       "   ...and HC trains again, on every season, at the rebuilt line")
finally:
    cfb._priced, cfb.build_schedule, cfb.get = _old

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 A CHAMPION'S HISTORY FILES ARE ITS INPUTS: PLANNED WHEN UNREADABLE, ONCE A DAY WHEN A REBUILD FAILS")
# ══════════════════════════════════════════════════════════════════════
import datetime  # noqa: E402

NOW = datetime.datetime(2026, 11, 17, 16, 0, tzinfo=datetime.timezone.utc)
_ci = F.champion_inputs
F.champion_inputs = lambda league, champion=None: _ci(league, {"nfl": None, "ncaaf": "HC"})
try:
    def hist_rows(root):
        return {os.path.basename(r["path"]): r for r in F.survey(root + "/data/ncaaf", root + "/picks", NOW)
                if "/history/schedule-" in r["path"] or "/history/lines-" in r["path"]}

    S0 = tree()
    _r = hist_rows(S0)
    ck(sorted(_r) == sorted(os.path.basename(p) for p in FC.history_files("HC", S0))
       and all(r["why"] == F.CHAMPION_INPUT and not F.stored_only(r) and r["mode"] == "cfb-probe"
               and r["stale"] and F.owes(r) for r in _r.values()),
       "🔴 CHAMPION HC: each of its 4 history files is a champion's-input row (never 'stored only'), and a "
       "MISSING one is owed: cfb-probe is planned", {k: (v["why"], v["stale"]) for k, v in _r.items()})
    fill(S0, "HC")
    _r = hist_rows(S0)
    ck(not any(r["stale"] or F.owes(r) for r in _r.values()),
       "🔴 all 4 present and readable: nothing stale, nothing owed (no extra cfb-probe, so no extra CFBD call)",
       {k: v["stale"] for k, v in _r.items()})
    raw(S0, "data/ncaaf/history/schedule-2023.json.gz", cut({"season": 2023, "games": []}))
    _r = hist_rows(S0)
    ck(_r["schedule-2023.json.gz"]["stale"] and F.owes(_r["schedule-2023.json.gz"])
       and not any(F.owes(v) for k, v in _r.items() if k != "schedule-2023.json.gz"),
       "🔴 an UNREADABLE one reads missing and is owed: its writer is planned and rebuilds it")
    with open(os.path.join(S0, "data/ncaaf/history", F.REBUILD_ATTEMPTS), "w", encoding="utf-8") as fh:
        json.dump({"files": {"schedule-2023.json.gz": {"tried_at": "2026-11-17T15:00:00Z",
                                                        "outcome": "refused"}}}, fh)
    _h = hist_rows(S0)["schedule-2023.json.gz"]
    ck(_h["stale"] and _h.get("held") and not F.owes(_h),
       "🔴 its writer tried an hour ago and could not land it: still stale, HELD, not owed (no CFBD sweep "
       "every pass for a file the price check refuses)", _h.get("held"))
    # `[review, 2026-11-17]` ~~"once REBUILD_RETRY_MIN (20 h) has passed, it is owed again"~~: 20 h ended
    #    before cfb-probe's own next deadline, so the released row alone planned a second sweep a day.
    #    Held until the writer's next own deadline (3:00 ET, 07:00Z), owed from it.
    def _at(root, when, end="/history/schedule-2023.json.gz"):
        return [r for r in F.survey(root + "/data/ncaaf", root + "/picks", when) if r["path"].endswith(end)][0]

    _a = _at(S0, datetime.datetime(2026, 11, 18, 6, 59, tzinfo=datetime.timezone.utc))
    _b = _at(S0, datetime.datetime(2026, 11, 18, 7, 1, tzinfo=datetime.timezone.utc))
    ck(_a.get("held") and not F.owes(_a) and _b["stale"] and not _b.get("held") and F.owes(_b),
       "🔴 ...held until its writer's own next deadline (cfb-probe's 3:00 ET, 07:00Z the next day; a fixed 20 h "
       "held it to 11:00Z), and owed from that deadline, when cfb-probe's own rows plan the ONE run that retries it",
       ((_a.get("held"), F.owes(_a)), (_b.get("held"), F.owes(_b))))
    _p23 = S0 + "/data/ncaaf/history/schedule-2023.json.gz"
    _t = datetime.datetime(2026, 11, 17, 15, 0, tzinfo=datetime.timezone.utc)
    eq([bool(F.rebuild_held(_p23, _t + datetime.timedelta(hours=h), None)) for h in (1, 47, 49)]
       + [bool(F.rebuild_held(_p23, _t + datetime.timedelta(hours=1), d))
          for d in ("2026-11-17T07:00Z", "2026-11-17T15:00Z", "2026-11-17T15:01Z")],
       [True, True, False, True, True, False],
       "🔴 a writer no deadline releases (no dated row) is retried every %d h at most; a deadline at or "
       "before the try holds it, one after it releases it" % (F.REBUILD_RETRY_MAX_MIN // 60))
    _ev = os.path.join(tree(), "event.json")
    with open(_ev, "w", encoding="utf-8") as fh:
        json.dump({"schedule": "4 7 * * *"}, fh)
    _env = {"GITHUB_EVENT_NAME": "schedule", "GITHUB_EVENT_PATH": _ev}
    _served = {"mode": "cfb-probe", "path": "data/ncaaf/latest/players-2026.json.gz", "stale": False,
               "missing": False, "due_at": "2026-11-17T07:00Z", "age_min": 530.0}
    _sd = [_served, dict(_h)]
    eq((F.stand_down(_sd, "cfb-probe", NOW, env=_env),
        F.stand_down([_served, {k: v for k, v in _h.items() if k != "held"}], "cfb-probe", NOW, env=_env)),
       (datetime.datetime(2026, 11, 17, 7, 4, tzinfo=datetime.timezone.utc), None),
       "🔴 a late `4 7` cron stands down past a HELD row (it would sweep CFBD again for a file it cannot "
       "write); an owed one still runs it")
finally:
    F.champion_inputs = _ci

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 THE CLASS: EVERY STATE A CHAMPION'S HISTORY FILE CAN BE IN, BOTH LEAGUES: THE CONTRACT OWES "
        "WHAT THE READER REFUSES, AND ONE WRITER RUN LEAVES IT CURRENT OR HELD, NEVER OWED AGAIN")
# ══════════════════════════════════════════════════════════════════════
# `[review, 2026-11-17]` The reader (`_stored`, need_history), the contract (`stamp_of` + HEALTH) and the
#    writers each judged the file their own way, and they disagreed both ways: a readable college file with
#    no stamp read MISSING (owed every pass, a CFBD sweep an hour) while store_cfb saw a file and did
#    nothing, recorded nothing, held nothing; a stamped file with no games failed HC closed while the
#    contract called it fresh, so nothing planned its repair. Every state, both leagues, both kinds of file.
UTC = datetime.timezone.utc
N6 = datetime.datetime(2026, 11, 17, 14, 0, tzinfo=UTC)       # a Tuesday: both writers' newest deadline 07:00Z
T6S = "2026-11-17T13:30:00Z"                                   # this test's writer runs (HX._stamp, never the clock)
# each writer's next own deadline after T6S: NFL's Tuesday noon ET (16:00Z), college's 3:00 ET (07:00Z)
NEXT6 = {"nfl": datetime.datetime(2026, 11, 17, 16, 0, tzinfo=UTC), "ncaaf": datetime.datetime(2026, 11, 18, 7, 0, tzinfo=UTC)}


def _gz(doc):
    return gzip.compress(json.dumps(doc).encode("utf-8"))


def states(path):
    """(what, the bytes to plant, or None to remove it): every state the reader or the contract refuses."""
    good = json.load(gzip.open(path, "rt", encoding="utf-8"))
    s, is_lines = good["season"], os.path.basename(path).startswith("lines-")
    bare = {k: v for k, v in good.items() if k not in F.STAMP_FIELDS}
    st = {"written_at": "2026-10-15T00:00:00Z"}
    return [("missing", None),
            ("a truncated gzip", _gz(good)[:40]),
            ("not a gzip at all", b"this is not a gzip file"),
            ("bad JSON", gzip.compress(b'{"season": %d, "games": [' % s)),
            ("bad UTF-8", gzip.compress(b'{"season": 2023, "note": "\xff\xfe"}')),
            ("a JSON list, not a document", _gz([1, 2, 3])),
            ("stamped, no games", _gz(dict(st, season=s, games={} if is_lines else []))),
            ("stamped, no games key", _gz(dict(st, season=s))),
            ("stamped, games of the wrong shape",
             _gz(dict(st, season=s, games=[{"x": 1}] if is_lines else {"x": {"start": "x"}}))),
            ("readable, no stamp", _gz(bare)),
            ("readable, a stamp the contract cannot read", _gz(dict(bare, built_at="n/a")))]


UNSTAMPED = ("readable, no stamp", "readable, a stamp the contract cannot read")


def _row6(root, lg, path, when):
    want = os.path.normpath(path)
    return [r for r in F.survey(root + "/data/" + lg, root + "/picks", when) if os.path.normpath(r["path"]) == want][0]


def _nflverse_down(s):
    raise RuntimeError("nflverse is down")


def _refused(root, lg):
    """One writer run whose source will not answer (college: the CFBD price check refuses; NFL: the build fails)."""
    return HX.store_nfl(quiet, root, build=_nflverse_down) if lg == "nfl" else HX.store_cfb(quiet, root)


def _answered(root, lg):
    if lg == "nfl":
        return HX.store_nfl(quiet, root, build=lambda s: {"season": s, "games": [
            g("r%d" % s, "%d-10-06" % s, "SEA", "DEN", 20, 17)]})
    return HX.store_cfb(quiet, root)


_ci6, _st6, _cfb6 = F.champion_inputs, HX._stamp, (cfb._priced, cfb.build_schedule, cfb.get)
_allow6, _calls6 = {"v": False}, []
F.champion_inputs = lambda league, champion=None: _ci6(league, {"nfl": "H", "ncaaf": "HC"})
HX._stamp = lambda: T6S
_bad6, _n6 = {}, 0
try:
    cfb._priced = lambda calls, purpose, log=None: _calls6.append(("priced", calls, purpose)) or _allow6["v"]
    cfb.build_schedule = lambda s, log=None: (_calls6.append(("/games", s)) or (
        {"season": s, "games": [g("c%d" % s, "%d-09-06" % s, "A", "B", 1, 0)]}, {}))
    cfb.get = lambda path, params, timeout=90, tries=4: _calls6.append((path, params["year"])) or [
        {"id": 9, "lines": [{"provider": "consensus", "spread": -3.0, "overUnder": 51.5,
                             "homeMoneyline": -160, "awayMoneyline": 135}]}]
    for _lg, _name, _target in (("nfl", "H", "schedule-2021.json.gz"), ("ncaaf", "HC", "schedule-2024.json.gz"),
                                ("ncaaf", "HC", "lines-2023.json.gz")):
        _probe = tree()
        fill(_probe, _name)
        for _what, _bytes in states(os.path.join(_probe, "data", _lg, "history", _target)):
            _n6 += 1
            X = tree()
            fill(X, _name)
            _p = os.path.join(X, "data", _lg, "history", _target)
            if _bytes is None:
                os.remove(_p)
            else:
                raw(X, os.path.relpath(_p, X), _bytes)
            _key, _why = "%s %s: %s" % (_lg, _target, _what), []
            try:
                FC.need_history(_lg, X)
                _refuses = False
            except FC.HistoryIncomplete:
                _refuses = True
            _r0 = _row6(X, _lg, _p, N6)
            if not (_r0["stale"] and F.owes(_r0) and not _r0.get("held")):
                _why.append("not owed before its writer ran (stale %s, owes %s)" % (_r0["stale"], F.owes(_r0)))
            if _refuses != (_what not in UNSTAMPED):
                _why.append("need_history %s it" % ("refused" if _refuses else "accepted"))
            _allow6["v"], _calls6[:] = False, []
            _refused(X, _lg)
            for _at in (N6, N6 + datetime.timedelta(hours=1), NEXT6[_lg] - datetime.timedelta(minutes=1)):
                _r1 = _row6(X, _lg, _p, _at)       # this pass, the next, and the minute before the next deadline
                if F.owes(_r1) or (_r1["stale"] and not _r1.get("held")):
                    _why.append("owed at %s after a refused run (stale %s, held %s)" % (
                        _at.strftime("%d %H:%MZ"), _r1["stale"], bool(_r1.get("held"))))
                    break
            if _what in UNSTAMPED and (_r1["stale"] or _calls6):
                _why.append("an unstamped readable file was not stamped in place for free (%s)" % _calls6)
            _allow6["v"], _calls6[:] = True, []
            _answered(X, _lg)
            _r3 = _row6(X, _lg, _p, N6)
            if _r3["stale"] or HX.state_of(_p) != "present":
                _why.append("not current after a run whose source answered (%s, %s)" % (
                    _r3["stale"], HX.state_of(_p)))
            try:
                FC.need_history(_lg, X)
            except FC.HistoryIncomplete as e:
                _why.append("need_history still refuses: %s" % e)
            if _why:
                _bad6[_key] = _why
finally:
    F.champion_inputs, HX._stamp = _ci6, _st6
    cfb._priced, cfb.build_schedule, cfb.get = _cfb6
eq((_n6, _bad6), (33, {}),
   "🔴 all 33 (11 states x NFL's schedule, college's schedule and lines): the contract owes each one the reader "
   "refuses (and the unstamped ones), a refused writer run leaves it HELD (never owed again before the next "
   "deadline), an unstamped one is stamped in place at no call, and a run whose source answers leaves it current")

# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 THE CADENCE: A REBUILD THAT KEEPS FAILING NEVER ADDS A RUN OF ITS WRITER, BOTH LEAGUES")
# ══════════════════════════════════════════════════════════════════════
# `[review, 2026-11-17]` 48 hourly passes through freshness.plan, each planned run of the writer played
#    by the REAL writer with a source that refuses (fb_history records the try), against the same 48
#    passes with every history file readable. A fixed 20 h hold released the row at 03:10Z, four hours
#    before cfb-probe's own 07:00Z deadline: two CFBD sweeps a day while the file could not land.


def cadence(lg, champ, writer, bad):
    """-> ([the passes plan() runs `writer` at], [(stale, held) of the champion's `bad` file each pass],
    the writer's other files) over 48 hourly passes (:10 past) from 07:10Z on 11-17, when it last ran."""
    X = tree()
    fill(X, champ)
    bp = os.path.join(X, "data", lg, "history", bad) if bad else None
    if bp:
        raw(X, os.path.relpath(bp, X), _gz(json.load(gzip.open(bp, "rt", encoding="utf-8")))[:40])
    t0 = datetime.datetime(2026, 11, 17, 7, 10, tzinfo=UTC)
    mine = sorted({r["path"] for r in F.survey(X + "/data/" + lg, X + "/picks", t0)
                   if r["mode"] == writer and r["kind"] == "file" and not F.stored_only(r)
                   and r["why"] != F.CHAMPION_INPUT})

    def run(at):
        st = at.strftime("%Y-%m-%dT%H:%M:%SZ")
        for p in mine:                 # the writer's other files, rebuilt by this run
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with (gzip.open(p, "wt", encoding="utf-8") if p.endswith(".gz")
                  else open(p, "w", encoding="utf-8")) as fh:
                json.dump({"built_at": st, "season": 2026}, fh)
        HX._stamp = lambda: st
        _refused(X, lg)

    runs, seen = [], []
    run(t0)
    for h in range(1, 49):
        at = t0 + datetime.timedelta(hours=h)
        modes, rows = F.plan(X + "/data/" + lg, X + "/picks", at)
        if bp:
            seen.extend((r["stale"], bool(r.get("held"))) for r in rows
                        if os.path.normpath(r["path"]) == os.path.normpath(bp))
        if writer in modes:
            runs.append(at.strftime("%m-%d %H:%MZ"))
            run(at)
    return runs, seen, [os.path.basename(p) for p in mine]


_ci7, _st7, _cfb7 = F.champion_inputs, HX._stamp, cfb._priced
F.champion_inputs = lambda league, champion=None: _ci7(league, {"nfl": "H", "ncaaf": "HC"})
cfb._priced = lambda calls, purpose, log=None: False
try:
    _cad = {(lg, b): cadence(lg, c, w, b) for lg, c, w, bad in (("ncaaf", "HC", "cfb-probe", "lines-2024.json.gz"),
                                                                 ("nfl", "H", "nfl-logs", "schedule-2020.json.gz"))
            for b in (None, bad)}
finally:
    F.champion_inputs, HX._stamp, cfb._priced = _ci7, _st7, _cfb7
_base = {lg: _cad[(lg, None)][0] for lg in ("ncaaf", "nfl")}
ck(_base == {"ncaaf": ["11-18 07:10Z", "11-19 07:10Z"], "nfl": ["11-17 16:10Z", "11-18 07:10Z", "11-19 07:10Z"]},
   "every history file readable: each writer runs for its own deadlines only (college 3:00 ET daily; NFL 3:00 ET "
   "daily and Tuesday noon)", (_base, {lg: _cad[(lg, None)][2] for lg in _base}))
for lg, bad in (("ncaaf", "lines-2024.json.gz"), ("nfl", "schedule-2020.json.gz")):
    _runs, _seen, _m = _cad[(lg, bad)]
    ck(_runs == _base[lg] and len(_seen) == 48 and all(s for s, _h in _seen) and sum(1 for _s, h in _seen if h) >= 40,
       "🔴 %s: %s unreadable and every rebuild refused for 48 hourly passes: %s runs at exactly its own deadlines "
       "(%s), never once more (the row stale all 48 passes, held between them)"
       % (lg, bad, {"ncaaf": "cfb-probe", "nfl": "nfl-logs"}[lg], ", ".join(_base[lg])),
       (_runs, sum(1 for _s, h in _seen if h)))
