#!/usr/bin/env python3
"""test_fb_proj_mean.py — a football row's PROJ is his average over EVERY game its
record is built from, as its note says.

`[2026-10-16]` An independent recheck of the card found PROJ = the 2025 games only:
Torrance Burgess Jr. printed PROJ 23.8 (2025: 12, 18, 17, 48) under "His own average
over the 9 games this record is built from", while his five 2026 games averaged
122.8, and `_prop_consistent` (the liked list's "side agrees with PROJ") read that
23.8. ⛔ `own_mean` is T54's pre-registered input and is NOT changed. The real
builder, in a planted tree, on a player with both seasons.

# @vacuity 🔴 PROJ averages every game the record is built from
#   file: card_fb.py
#   find:     mean_all = (sum(v25) + sum(v26)) / (n25 + n26) if n25 + n26 else None
#   with:     mean_all = (sum(v25) / n25) if n25 else None
#
# @vacuity 🔴 the printed PROJ reads that average
#   file: card_fb.py
#   find:     return d["mean_all"] if "mean_all" in d else r[3]
#   with:     return r[3]
#
# @vacuity 🔴 the card prints projection_of, not the 2025 mean
#   file: card_fb.py
#   find:                     _pj = projection_of(r)
#   with:                     _pj = r[3]
#
# @vacuity 🔴 own_mean (T54's input) is unchanged
#   file: card_fb.py
#   find:                                        else round(r[3], 2))
#   with:                                        else round(projection_of(r), 2))
"""
import gzip
import importlib
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from tcheck import ck, eq, section  # noqa: E402

V25 = [10, 20, 15, 12, 18, 14, 16, 15]            # 2025: mean 15.0
V26 = [100, 110, 120, 130, 140]                    # 2026: mean 120.0
ALL = round(sum(V25 + V26) / len(V25 + V26), 1)    # 55.4 over all 13


def g(v, d=None):
    out = {"rush_yds": v, "car": 10, "rec": 0, "rec_yds": 0, "rec_td": 0, "rush_td": 0,
           "pass_yds": 0, "pass_td": 0, "team": "T", "game_id": "x%s" % v}
    if d:
        out["d"] = d
    return out


tmp, cwd = tempfile.mkdtemp(prefix="projmean-"), os.getcwd()
try:
    os.chdir(tmp)
    os.makedirs("data/ncaaf/latest")
    with gzip.open("data/ncaaf/latest/props.json.gz", "wt") as fh:
        json.dump({"pulled_at": "2026-10-16T12:00:00Z", "n_games": 1, "books_seen": ["fd"],
                   "games": [{"id": "g1", "away": "A", "home": "H", "commence": "2026-10-17T17:00:00Z",
                              "props": [{"player": "Two Season", "market": "player_rush_yds", "line": 60.5,
                                         "sides": {"under": {"price": -110, "book": "fd", "n_books": 3,
                                                             "link": "x"}}}]}]}, fh)
    with gzip.open("data/ncaaf/latest/players-2025.json.gz", "wt") as fh:
        json.dump({"season": 2025, "scope": "all FBS conferences",
                   "players": {"1": {"name": "Two Season", "pos": "RB", "g": [g(v) for v in V25]}}}, fh)
    with gzip.open("data/ncaaf/latest/players-2026.json.gz", "wt") as fh:
        json.dump({"season": 2026, "scope": "all FBS conferences",
                   "players": {"1": {"name": "Two Season", "pos": "RB",
                                     "g": [g(v, "2026-09-%02d" % (5 + 7 * i)) for i, v in enumerate(V26)]}}}, fh)
    os.environ["LEAGUE"] = "ncaaf"
    sys.modules.pop("card_fb", None)
    C = importlib.import_module("card_fb")
    C.main()
    doc = json.load(open("picks/fb-ncaaf-latest.json", encoding="utf-8"))
finally:
    os.chdir(cwd)
    shutil.rmtree(tmp, ignore_errors=True)

section("1. 🔴 PROJ IS THE AVERAGE OVER EVERY GAME THE RECORD IS BUILT FROM")
rows = [r for r in doc.get("picks") or [] if r.get("player") == "Two Season"]
ck(len(rows) == 1 and (rows[0].get("season_detail") or {}).get("n26") == 5,
   "⚠️ the planted row was rated on BOTH seasons (2025 and five 2026 games), so the case is real",
   [(r.get("record"), r.get("season_detail")) for r in rows])
r = rows[0] if rows else {}
eq(r.get("projection"), ALL, "🔴 PROJ = the plain average of all 13 games (~~15.0, the 2025 games only~~)")
eq(r.get("projection_note"), "His own average over the 13 games this record is built from — %.1f rush yds a game." % ALL,
   "🔴 ...which is what its note says")
eq((doc.get("projections") or {}).get("Two Season|player_rush_yds|under|60.5", {}).get("v"), ALL,
   "🔴 the projections map (what the liked list's PROJ check reads) carries the same number")
eq(r.get("own_mean"), 15.0, "⛔ own_mean, T54's pre-registered input, is unchanged")
