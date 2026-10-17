#!/usr/bin/env python3
"""test_cfb_injury_model.py — HOW MUCH OF A COLLEGE TEAM IS MISSING (the model's reading).

`[Sam, 2026-10-17]` *"we need to make sure we have injury reports and to account for those injuries
and how they affect the outcomes of the games"*; for college *"use the college injury source as
long as it's accurate and up to date"*. research/cfb_injuries_design.md §3, per team, from this
season's games BEFORE the game:
  - QB out: the starting QB (most pass attempts in the team's latest stored game) is listed
    Out / Out for Season / Doubtful;
  - offence out: the share of the team's rushing + receiving yards held by its listed non-QBs;
  - defence out: the share of the team's tackles held by its listed defenders;
  - a report player matched by team + jersey with the same last name, else a unique name on the
    team (card_fb.norm), never a guess; Questionable / Probable / Exempt count nowhere;
  - no pick-time report for BOTH teams, or no stored defence log: no reading (None), never zero.
⛔ It is read only while fb_model.INJURIES["ncaaf"] is on (test_fb_inj_backtest.py §3, §4).

PLANTED DATA ONLY: players / defense / roster logs in a temp root; `pick_time_outs` is a stand-in.

# @vacuity 🔴 the starting QB is the most attempts in the team's latest game
#   file: cfb_injuries.py
#   find:                 att, pid = max(qbs)
#   with:                 att, pid = min(qbs)
#
# @vacuity 🔴 a QB out counts only when he is the starter
#   file: cfb_injuries.py
#   find:                 qb = 1.0 if att > 0 and pid in out else 0.0
#   with:                 qb = 1.0 if any(p in out for _a, p in qbs) else 0.0
#
# @vacuity 🔴 only games BEFORE the game size a player
#   file: cfb_injuries.py
#   find:         off = [(pid, g) for pid, g in t["off"] if (g.get("d") or "") < day]
#   with:         off = [(pid, g) for pid, g in t["off"]]
#
# @vacuity 🔴 the offence share leaves the QB out (he has his own term)
#   file: cfb_injuries.py
#   find:                  and (self.off.get(pid) or {}).get("pos") != "QB") / tot_off) if tot_off > 0 else 0.0
#   with:                  ) / tot_off) if tot_off > 0 else 0.0
#
# @vacuity 🔴 the defence share is the listed defenders' share of the team's tackles
#   file: cfb_injuries.py
#   find:         d = (sum(g.get("tot") or 0 for pid, g in dfn if pid in out) / tot_def) if tot_def > 0 else 0.0
#   with:         d = 0.0
#
# @vacuity ⛔ Questionable / Probable / Exempt count nowhere
#   file: cfb_injuries.py
#   find:                if (p.get("status") or "").strip().lower() in OUT_STATUSES}
#   with:                if (p.get("status") or "").strip().lower() not in ("available",)}
#
# @vacuity 🔴 a jersey match needs the same last name
#   file: cfb_injuries.py
#   find:                     and (norm(e.get("name")).split() or [None])[-1] == last}
#   with:                     }
#
# @vacuity ⛔ an ambiguous name is never matched
#   file: cfb_injuries.py
#   find:         return next(iter(ids)) if len(ids) == 1 else None
#   with:         return next(iter(ids)) if ids else None
#
# @vacuity ⛔ no report for both teams is no reading, never zero
#   file: cfb_injuries.py
#   find:             if r["home"] not in rep or r["away"] not in rep:
#   with:             if False:
#
# @vacuity ⛔ [2026-10-17, review] no game before this one (or no stored defence log) is no reading
#   file: cfb_injuries.py
#   find:         if not off or not dfn or tot_off <= 0 or tot_def <= 0:
#   with:         if False:
"""
import gzip
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "ncaaf")
import cfb_injuries as CI  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402


def put(root, rel, obj):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        json.dump(obj, fh)


def g(team, d, **st):
    return dict({"team": team, "d": d, "game_id": "x" + d}, **st)


# Home U: QB1 starts (30 att in the last game BEFORE 10-17), QB2 the backup; RB 300 + WR 200 + QB 100
# yards before 10-17. The 10-17 game itself (QB2 50 att, the RB 999 yards) must never count: counted,
# QB2 would be the starter and the RB's share 1299 / 1599. Away St.: one RB with every yard.
PLAYERS = {"players": {
    "q1": {"name": "Quinn Starter", "pos": "QB", "g": [g("Home U", "2026-10-03", att=25, rush_yds=60),
                                                       g("Home U", "2026-10-10", att=30, rush_yds=40),
                                                       g("Home U", "2026-10-17", att=10)]},
    "q2": {"name": "Ben Backup", "pos": "QB", "g": [g("Home U", "2026-10-10", att=3),
                                                    g("Home U", "2026-10-17", att=50)]},
    "r1": {"name": "Cameron Runner", "pos": "RB", "g": [g("Home U", "2026-10-03", car=20, rush_yds=150),
                                                        g("Home U", "2026-10-10", car=18, rush_yds=150),
                                                        g("Home U", "2026-10-17", car=30, rush_yds=999)]},
    # ⚠️ both John Smiths hold yards: a mutant that matched EITHER (set order follows the hash seed)
    #    reads 100 / 600, never the 0 that the right answer reads.
    "w1": {"name": "John Smith", "pos": "WR", "g": [g("Home U", "2026-10-10", rec=4, rec_yds=100)]},
    "w2": {"name": "John Smith", "pos": "WR", "g": [g("Home U", "2026-10-10", rec=4, rec_yds=100)]},
    "a1": {"name": "Al Away", "pos": "RB", "g": [g("Away St.", "2026-10-10", car=10, rush_yds=80)]}}}
DEFENSE = {"players": {
    "d1": {"name": "Larry Linebacker", "team": "Home U", "g": [g("Home U", "2026-10-03", tot=20),
                                                               g("Home U", "2026-10-10", tot=20)]},
    "d2": {"name": "Sam Safety", "team": "Home U", "g": [g("Home U", "2026-10-10", tot=160)]},
    "d3": {"name": "Ed Edge", "team": "Away St.", "g": [g("Away St.", "2026-10-10", tot=50)]}}}
ROSTER = {"teams": {"Home U": [{"id": "r1", "name": "Cameron Runner", "jersey": 5, "position": "RB"},
                               {"id": "q1", "name": "Quinn Starter", "jersey": 1, "position": "QB"},
                               {"id": "q2", "name": "Ben Backup", "jersey": 12, "position": "QB"},
                               {"id": "d1", "name": "Larry Linebacker", "jersey": 44, "position": "LB"},
                               {"id": "d2", "name": "Sam Safety", "jersey": 7, "position": "S"}],
                    "Away St.": [{"id": "d3", "name": "Ed Edge", "jersey": 9, "position": "DL"}]}}


def P(name, num=None, status="Out"):
    return {"name": name, "number": num, "position": "X", "status": status}


def run(outs, with_defense=True, day="2026-10-17"):
    t = tempfile.mkdtemp(prefix="cfbinjm-")
    try:
        put(t, "data/ncaaf/latest/players-2026.json.gz", PLAYERS)
        put(t, "data/ncaaf/latest/roster-2026.json.gz", ROSTER)
        if with_defense:
            put(t, "data/ncaaf/latest/defense-2026.json.gz", DEFENSE)
        saved = CI.pick_time_outs
        CI.pick_time_outs = lambda season, root=None: outs
        try:
            rows = [{"id": "G1", "season": 2026, "day": day, "home": "Home U", "away": "Away St.", "sig": {}}]
            CI.attach(rows, t)
        finally:
            CI.pick_time_outs = saved
        return rows[0]["sig"].get("inj")
    finally:
        shutil.rmtree(t, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 QB OUT, OFFENCE SHARE, DEFENCE SHARE, FROM EARLIER GAMES ONLY")
# ══════════════════════════════════════════════════════════════════════
inj = run({"G1": {"Home U": [P("Quinn Starter", 1), P("Cam Runner", 5, "Doubtful"),
                             P("Larry Linebacker", 44, "Out for Season")],
                  "Away St.": []}})
eq(inj, {"qb": (1.0, 0.0), "off": (0.5, 0.0), "def": (0.2, 0.0)},
   "🔴 the starter out (QB 1); the RB held 300 of the team's 600 rushing + receiving yards before the "
   "game (0.5); the LB 40 of its 200 tackles (0.2); the 10-17 game never counts; the side with "
   "nobody listed reads 0")
inj = run({"G1": {"Home U": [P("Ben Backup", 12)], "Away St.": []}})
eq((inj or {}).get("qb"), (0.0, 0.0), "🔴 the BACKUP QB out is not the starter out")
inj = run({"G1": {"Home U": [P("Quinn Starter", 1, "Questionable"), P("Cameron Runner", 5, "Probable"),
                             P("Sam Safety", 7, "Exempt")], "Away St.": []}})
eq(inj, {"qb": (0.0, 0.0), "off": (0.0, 0.0), "def": (0.0, 0.0)},
   "⛔ Questionable, Probable and Exempt count nowhere")

# ══════════════════════════════════════════════════════════════════════
section("2. ⛔ A REPORT PLAYER IS MATCHED, NEVER GUESSED")
# ══════════════════════════════════════════════════════════════════════
inj = run({"G1": {"Home U": [P("Cam Runner", 5)], "Away St.": []}})
eq((inj or {}).get("off"), (0.5, 0.0), "🔴 a nickname matches through team + jersey + the same last name")
inj = run({"G1": {"Home U": [P("Cam Walker", 5)], "Away St.": []}})
eq((inj or {}).get("off"), (0.0, 0.0), "⛔ the same jersey with another last name is not him")
inj = run({"G1": {"Home U": [P("John Smith")], "Away St.": []}})
eq((inj or {}).get("off"), (0.0, 0.0), "⛔ two John Smiths on the team and no jersey: no match, never the "
   "first one")

# ══════════════════════════════════════════════════════════════════════
section("2b. ⛔ A SEASON OPENER IS NO READING, NEVER 'NOBODY OUT'")
# ══════════════════════════════════════════════════════════════════════
# `[2026-10-17, review]` a team with no stored game before this one: nothing is known about who
#    matters, so a starting QB listed Out must not read 0 (design §3: no reading, never zero).
eq(run({"G1": {"Home U": [P("Quinn Starter", 1)], "Away St.": []}}, day="2026-10-03"), None,
   "⛔ Home U's first game (10-03, nothing before it): None, not QB out 0")
eq((run({"G1": {"Home U": [P("Quinn Starter", 1)], "Away St.": []}}, day="2026-10-04") or {}).get("qb"), None,
   "⛔ ...and Away St. has no game before 10-04 either, so the whole game reads None")

# ══════════════════════════════════════════════════════════════════════
section("3. ⛔ NO REPORT IS NO READING, NEVER ZERO")
# ══════════════════════════════════════════════════════════════════════
eq(run({}), None, "⛔ a game with no report: None")
eq(run({"G1": {"Home U": [P("Quinn Starter", 1)]}}), None,
   "⛔ a report for one team only (a conference report covers its own games): None")
eq(run({"G1": {"Home U": [P("Quinn Starter", 1)], "Away St.": []}}, with_defense=False), None,
   "⛔ no stored defence log: None, not a defence share of zero")
ck("✅ the reading is stored on the row's sig, home first", run(
    {"G1": {"Home U": [], "Away St.": [P("Ed Edge", 9)]}}) == {"qb": (0.0, 0.0), "off": (0.0, 0.0),
                                                               "def": (0.0, 1.0)})
