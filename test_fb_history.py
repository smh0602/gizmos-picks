#!/usr/bin/env python3
r"""T70 — MORE SEASONS (research/fb_refit_spec.md §3d): fb_history.py and the H / HC
challengers. `[Sam, 2026-10-15]` "do all changes". Planted trees and fake sources.
⛔ Reads no live data, makes no network call.

# @vacuity 🔴 Oakland is stored as Las Vegas
#   file: fb_history.py
#   find: ALIAS = {"OAK": "LV"}                                        # ⛔ §3d: Oakland became Las Vegas in 2020
#   with: ALIAS = {}                                        # ⛔ §3d: Oakland became Las Vegas in 2020
#
# @vacuity 🔴 one failing NFL season never stops the others
#   file: fb_history.py
#   find:             out[s] = "failed: %s: %s" % (type(e).__name__, str(e)[:200])
#   with:             raise
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
# @vacuity 🔴 a history file is stored-only for freshness
#   file: freshness.py
#   find:                          r"|/history/(schedule|lines)-\d{4}\.json\.gz$")
#   with:                          r"|/nowhere/x$")
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
    ck(set(out.values()) == {"refused"} and not asked and not os.path.exists(C + "/data/ncaaf/history"),
       "🔴 a refused CFBD history call fetches nothing and writes nothing", out)
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
eq([r["id"] for r in FC.history_rows("ncaaf", CC)], ["hist:f1"], "🔴 college history rows are FBS vs FBS only")
ck('if fb_challengers.CHALLENGERS[CHAMPION[lg]].get("history"):' in open(os.path.join(ROOT, "fb_model.py"),
                                                                         encoding="utf-8").read(),
   "   a champion H trains on the history rows too (fb_model.build_rows)")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 REGISTRATION, COUNTS, FRESHNESS")
# ══════════════════════════════════════════════════════════════════════
eq(R.registration("H", T), None, "🔴 H is not registered while any history season's file is missing (2019 here)")
eq(R.registration("H", T, {"H": "2026-10-20"}), "2026-10-26", "   ...and once they all exist, the next Monday")
eq({lg: sum(1 for c in FC.CHALLENGERS.values() if c["league"] == lg) for lg in ("nfl", "ncaaf")},
   {"nfl": 8, "ncaaf": 8}, "🔴 8 challengers a league, p < 0.01 / 8")
P = tree()
rows = F.contract(P + "/data/nfl", P + "/picks", None)
hist = [r for r in rows if "/history/" in r[1][1]]
ck(len(hist) == 7 and all(r[0] == "nfl-logs" and r[2] == [] and F.stored_only({"path": r[1][1]}) for r in hist),
   "🔴 a freshness row per NFL history season, by the daily nfl-logs run, late only when missing, stored-only "
   "(never a red run, never a planned rebuild)", [r[1][1] for r in hist][:2])
eq(len([r for r in F.contract(P + "/data/ncaaf", P + "/picks", None) if "/history/" in r[1][1]]), 4,
   "   ...and college's 2 seasons x schedule and lines")
