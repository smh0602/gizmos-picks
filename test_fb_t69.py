#!/usr/bin/env python3
"""T69 — INJURIES ON BOTH SIDES, SAM'S AVERAGES FOR TOTALS, REST (fb_refit_spec.md §3c).

`[Sam, 2026-10-15]` "do all changes"; "injuries should've always been a factor on
both sides of the ball". Planted injury reports, logs and schedules; a pinned
day. ⛔ Reads no live data.

# @vacuity 🔴 Questionable is never counted as out
#   file: fb_challengers.py
#   find: OUT_STATUSES = ("out", "doubtful")       # ⛔ §3c: Questionable is not counted
#   with: OUT_STATUSES = ("out", "doubtful", "questionable")       # ⛔ §3c: Questionable is not counted
#
# @vacuity 🔴 a defender is weighed by his DEFENSIVE snap share
#   file: fb_challengers.py
#   find:         k = 4 if pos in DEF_POS else 2   # a defender's DEFENSIVE snap share
#   with:         k = 2   # a defender's DEFENSIVE snap share
#
# @vacuity 🔴 only games before the game day weigh a player
#   file: fb_challengers.py
#   find:         last = [x[k] for x in logs.get(gid) or [] if x[1] == team and x[0] < day][-3:]
#   with:         last = [x[k] for x in logs.get(gid) or [] if x[1] == team][-3:]
#
# @vacuity 🔴 the starting QB out is its own input
#   file: fb_challengers.py
#   find:             qb_out = 1.0 if gid and gid == qb else qb_out
#   with:             qb_out = 0.0
#
# @vacuity 🔴 spread and moneyline read away minus home
#   file: fb_challengers.py
#   find:         return list(x) + [j["qb"][1] - j["qb"][0], j["off"][1] - j["off"][0], j["def"][1] - j["def"][0]]
#   with:         return list(x) + [j["qb"][0] - j["qb"][1], j["off"][0] - j["off"][1], j["def"][0] - j["def"][1]]
#
# @vacuity 🔴 AT blends Sam's total with the model's own total
#   file: fb_challengers.py
#   find:         return [((ot + t) / 2.0 - T) / 10.0] + list(x[1:])
#   with:         return [(t - T) / 10.0] + list(x[1:])
#
# @vacuity 🔴 rest is capped at 14 days
#   file: fb_challengers.py
#   find:     return min(REST_CAP, gap)
#   with:     return gap
#
# @vacuity 🔴 the NFL logs keep each defender's defensive snap share
#   file: nfl.py
#   find:             row["def_pct"] = round(_num(sn.get("defense_pct")), 3)
#   with:             row["def_pct"] = 0.0
#
# @vacuity 🔴 a players file without defensive snap shares is rebuilt
#   file: nfl.py
#   find:             if "def_snaps_logged" not in _pl:
#   with:             if False:
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
import fb_challengers as FC  # noqa: E402
import fb_model as FM  # noqa: E402
import fb_refit as R  # noqa: E402
import nfl  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])


def tree():
    t = tempfile.mkdtemp(prefix="fbt69-")
    TREES.append(t)
    return t


def put(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        json.dump(doc, fh)


def row(gid="g", day="2026-10-18", home="DEN", away="SEA", week=6, lg="nfl"):
    return {"id": gid, "lg": lg, "season": 2026, "day": day, "home": home, "away": away, "week": week,
            "final": False, "hs": None, "as": None, "M": 3.0, "T": 45.0, "pml": None,
            "sig": {"neutral": 0.0, "dome": 0.0, "own_m": 5.0, "own_t": 47.0, "h2h_m": None, "h2h_t": None,
                    "form_m": None, "form_t": None, "def": None, "poss": None, "out": None,
                    "vac_h": None, "vac_a": None}}


def lg_row(d, team, snap=0.0, dfp=0.0, att=0.0):
    return {"d": d, "team": team, "snap_pct": snap, "def_pct": dfp, "att": att, "week": 1}


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 IN: INJURIES ON BOTH SIDES OF THE BALL")
# ══════════════════════════════════════════════════════════════════════
T1 = tree()
put(T1, "data/nfl/latest/players-2026.json.gz", {"players": {
    "cb1": {"name": "Star CB", "pos": "CB", "g": [lg_row("2026-10-04", "DEN", 0.0, 0.9), lg_row("2026-10-11", "DEN", 0.0, 1.0),
                                                  lg_row("2026-10-18", "DEN", 0.0, 0.1)]},
    "s1": {"name": "Safety", "pos": "SAF", "g": [lg_row("2026-10-11", "DEN", 0.0, 0.8)]},
    "q1": {"name": "Questionable LB", "pos": "LB", "g": [lg_row("2026-10-11", "DEN", 0.0, 1.0)]},
    "rb1": {"name": "SEA RB", "pos": "RB", "g": [lg_row("2026-10-11", "SEA", 0.6), lg_row("2026-10-04", "SEA", 0.3)]},
    "qb1": {"name": "SEA QB", "pos": "QB", "g": [lg_row("2026-10-11", "SEA", 1.0, att=34)]},
    "qb2": {"name": "SEA QB2", "pos": "QB", "g": [lg_row("2026-10-11", "SEA", 0.1, att=2)]},
    "new": {"name": "No Log", "pos": "WR", "g": []}}})
put(T1, "data/nfl/latest/injuries-2026.json.gz", {"teams": {
    "DEN": {"6": {"players": [{"gsis_id": "cb1", "position": "CB", "report_status": "Out"},
                              {"gsis_id": "s1", "position": "S", "report_status": "Doubtful"},
                              {"gsis_id": "q1", "position": "LB", "report_status": "Questionable"}]}},
    "SEA": {"6": {"players": [{"gsis_id": "rb1", "position": "RB", "report_status": "Out"},
                              {"gsis_id": "qb1", "position": "QB", "report_status": "Doubtful"},
                              {"gsis_id": "new", "position": "WR", "report_status": "Out"}]}}}})
rows = [row()]
FC.attach("IN", "nfl", rows, T1)
j = rows[0]["sig"]["inj"]
eq({k: tuple(round(v, 6) for v in j[k]) for k in j}, {"qb": (0.0, 1.0), "off": (0.0, 0.45), "def": (1.75, 0.0)},
   "🔴 Denver's defence out = CB 0.95 + S 0.80 by DEFENSIVE snap share (the 10-18 game itself and the "
   "Questionable LB never count); Seattle's RB 0.45 off its last games; Seattle's starting QB (34 attempts "
   "last game) Doubtful -> qb out; a listed player with no earlier game weighs 0")
x = FM.features(rows[0], "spread")
eq([round(v, 6) for v in R.challenger_feat("IN")(rows[0], "spread")[len(x):]], [1.0, 0.45, -1.75],
   "🔴 spread / moneyline append away minus home: QB out, offence out, defence out")
eq([round(v, 6) for v in R.challenger_feat("IN")(rows[0], "total")[len(FM.features(rows[0], "total")):]],
   [1.0, 0.45, 1.75], "🔴 totals append both teams' sums")
ck(R.challenger_feat("IN")(rows[0], "moneyline")[:len(x)] == FM.features(rows[0], "moneyline"),
   "   ...and leave the champion's own inputs byte-identical")
r2 = [row(week=7)]
FC.attach("IN", "nfl", r2, T1)
eq(r2[0]["sig"]["inj"], {"qb": (0.0, 0.0), "off": (0.0, 0.0), "def": (0.0, 0.0)},
   "   no report for that team-week -> 0 for both teams")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 AT / ATC: SAM'S AVERAGES BLENDED INTO THE TOTAL; RS / RSC: REST")
# ══════════════════════════════════════════════════════════════════════
A = dict(row(), sig=dict(row()["sig"], sam_t=41.0))
eq(round(R.challenger_feat("AT")(A, "total")[0], 9), round(((47.0 + 41.0) / 2 - 45.0) / 10, 9),
   "🔴 AT's first total input is ((own total + sam_t) / 2 - line) / 10")
eq(R.challenger_feat("AT")(A, "total")[1:], FM.features(A, "total")[1:], "   ...the rest of the total inputs unchanged")
ck(R.challenger_feat("AT")(row(), "total") == FM.features(row(), "total")
   and R.challenger_feat("AT")(A, "spread") == FM.features(A, "spread"),
   "   no sam_t: unchanged; spread and moneyline never touched")
eq(round(R.challenger_feat("AT")(A, "total", T=40.0)[0], 9), round(((47.0 + 41.0) / 2 - 40.0) / 10, 9),
   "   ...at the alt total line priced")
T2 = tree()
put(T2, "data/nfl/latest/schedule-2026.json.gz", {"season": 2026, "games": [
    {"id": 1, "start": "2026-09-27T17:00", "home": "DEN", "away": "XXX"},
    {"id": 2, "start": "2026-10-12T17:00", "home": "YYY", "away": "SEA"},
    {"id": 3, "start": "2026-10-18T17:00", "home": "DEN", "away": "SEA"}]})
rs = [row(), row(home="NEW", away="SEA")]
FC.attach("RS", "nfl", rs, T2)
eq([r["sig"]["rest_d"] for r in rs], [14 - 6, 14 - 6],
   "🔴 rest: Denver 21 days since its last game, capped at 14, vs Seattle 6 days -> +8; a team with no earlier game rests 14")
eq(R.challenger_feat("RS")(rs[0], "spread")[-1], 8 / 7.0, "   ...appended as rest difference / 7")
ck(R.challenger_feat("RS")(rs[0], "total") == FM.features(rs[0], "total"), "   totals unchanged")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 COUNTS, REGISTRATION, FRESHNESS AND THE NFL DEFENSIVE SNAPS")
# ══════════════════════════════════════════════════════════════════════
eq({lg: sorted(n for n, c in FC.CHALLENGERS.items() if c["league"] == lg) for lg in ("nfl", "ncaaf")},
   {"nfl": ["AT", "AV", "E", "IN", "RS", "S", "WX"], "ncaaf": ["ATC", "AVC", "P", "RSC", "T", "TS", "WXC"]},
   "🔴 7 challengers a league, so alpha is 0.01 / 7")
eq([R.registration("IN", T1, {"IN": "2026-10-15"}), R.registration("AT", T1), R.registration("RSC", T1)],
   ["2026-10-19"] * 3, "🔴 registered 2026-10-19 (IN after its injuries files exist)")
import freshness as F  # noqa: E402
eq(F.champion_inputs("nfl", {"nfl": "IN"}), [("injuries-{s}.json.gz", "possession")],
   "🔴 a champion IN reads the injuries file on the daily deadline, a hard input")
T3 = tree()
base = os.path.join(T3, "data", "nfl", "latest")
os.makedirs(base)
json.dump({}, open(os.path.join(base, "top-probe-2025.json"), "w"))
put(T3, "data/nfl/latest/top-2025.json.gz", {"games": [], "inside10": {}})
put(T3, "data/nfl/latest/players-2025.json.gz", {"team_out_report": {}, "opportunity_report": {}})
gap = nfl.history_gap(base, 2025) or ""
put(T3, "data/nfl/latest/players-2025.json.gz", {"team_out_report": {}, "opportunity_report": {}, "def_snaps_logged": True})
ck("defensive snap shares" in gap and "defensive snap shares" not in (nfl.history_gap(base, 2025) or ""),
   "🔴 a stored season without defensive snap shares is rebuilt once by the daily run, then never again", gap)
ck('row["def_pct"] = round(_num(sn.get("defense_pct")), 3)' in open(os.path.join(ROOT, "nfl.py"), encoding="utf-8").read(),
   "🔴 the NFL logs store each player's defensive snap share (nflverse defense_pct)")
