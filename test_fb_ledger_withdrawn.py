#!/usr/bin/env python3
"""test_fb_ledger_withdrawn.py — a pick the model withdrew before kickoff is not graded.

`[Sam, 2026-10-16]` research/fb_model_live_spec.md §3a: "Don't grade withdrawn: change the
rule: the last snapshot that looked at a game decides, even when it holds no pick." After
#278 the ledger still held 8 pre-fix picks on teams the model expects to lose, because §3
kept a pick "unless the game had no pick in any later snapshot". Planted snapshots and trees;
⛔ reads nothing live.

# @vacuity 🔴 a game the last snapshot looked at with no pick is withdrawn: nothing graded
#   file: fb_ledger.py
#   find:                     chosen[(model, gid)] = (s["taken_at"], [])        # withdrawn: nothing graded
#   with:                     pass
#
# @vacuity 🔴 a look AFTER kickoff never withdraws a pick
#   file: fb_ledger.py
#   find:                 if gid not in by_game and s["taken_at"] < (commence or ""):
#   with:                 if gid not in by_game:
#
# @vacuity 🔴 a snapshot that holds a pick for the game keeps it, even though it also looked at it
#   file: fb_ledger.py
#   find:                 if gid not in by_game and s["taken_at"] < (commence or ""):
#   with:                 if s["taken_at"] < (commence or ""):
#
# @vacuity 🔴 the snapshot records what each model looked at
#   file: fb_ledger.py
#   find:            "looked_at": looked, "spec": "research/fb_model_live_spec.md"}
#   with:            "looked_at": {}, "spec": "research/fb_model_live_spec.md"}
#
# @vacuity 🔴 a snapshot is written when a model looked at games but shows no pick at all
#   file: fb_ledger.py
#   find:     if not game and not props and not any(looked.values()):
#   with:     if not game and not props:
#
# @vacuity 🔴 a rated prop game's kickoff comes from the props board
#   file: fb_ledger.py
#   find:             for g in (_gz(os.path.join(latest, "props.json.gz")) or {}).get("games") or []}
#   with:             for g in []}
#
# @vacuity 🔴 only unstarted games are listed as looked at
#   file: fb_ledger.py
#   find:                              if (w.get("commence") or "") > now},
#   with:                              },
"""
import datetime
import gzip
import json
import os
import shutil
import sys
import tempfile

from tcheck import ck, eq, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import fb_ledger as LG  # noqa: E402

Q = lambda *a, **k: None  # noqa: E731
K1 = "2026-10-17T16:00:00Z"            # g1's kickoff


def T(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _w(path, doc, gz=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with (gzip.open(path, "wt", encoding="utf-8") if gz else open(path, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


def gp(gid, commence=K1, side="away", market="moneyline", team="Michigan State Spartans"):
    return {"game_id": gid, "commence": commence, "market": market, "side": side, "team": team,
            "game": "Northwestern Wildcats at Michigan State Spartans",
            "line": {"value": None, "basis": "MARKET"}, "price": {"value": 250, "basis": "MARKET"},
            "book": "Hard Rock", "model_probability": {"value": 29.3, "basis": "MODEL"},
            "break_even": {"value": 28.6, "basis": "MARKET"}}


def pp(gid, commence=K1, player="Test Back"):
    return {"game_id": gid, "commence": commence, "player": player, "market": "player_rush_yds",
            "side": "over", "line": {"value": 50.5, "basis": "MARKET"}}


def picked(snaps, model="game_model"):
    return sorted((p["game_id"], p["snapshot"]) for p in LG.ledger_picks(snaps) if p["model"] == model)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE LAST SNAPSHOT THAT LOOKED AT A GAME DECIDES, EVEN WITH NO PICK")
# ══════════════════════════════════════════════════════════════════════
S1 = {"taken_at": "2026-10-16T15:37:06Z", "game_model": [gp("g1"), gp("g2")]}      # before the rule
S2 = {"taken_at": "2026-10-16T16:40:52Z", "game_model": [gp("g2")],
      "looked_at": {"game_model": {"g1": K1, "g2": K1}}}                              # g1 withdrawn
eq(picked([S1, S2]), [("g2", "2026-10-16T16:40:52Z")],
   "🔴🔴 Sam's case: the 15:37 pick on g1 is withdrawn by the 16:40 snapshot that looked at g1 with no "
   "pick, so nothing is graded for g1 (g2's newer pick still counts)")
eq(picked([S1, dict(S2, looked_at={})]), [("g1", "2026-10-16T15:37:06Z"), ("g2", "2026-10-16T16:40:52Z")],
   "🔴 a snapshot written BEFORE the amendment (no looked_at) looked only at its own picks: the old "
   "rule still applies, so the past is not recalculated")
S3 = {"taken_at": "2026-10-17T12:00:00Z", "game_model": [gp("g1", team="Northwestern Wildcats", side="home")],
      "looked_at": {"game_model": {"g1": K1}}}
eq(sorted((p["game_id"], p["team"]) for p in LG.ledger_picks([S1, S2, S3])),
   [("g1", "Northwestern Wildcats"), ("g2", "Michigan State Spartans")],
   "🔴 a pick the model shows AGAIN later counts (the last look holds a pick); a snapshot that both "
   "holds a pick and lists the game keeps the pick")
S4 = {"taken_at": "2026-10-17T18:00:00Z", "game_model": [], "looked_at": {"game_model": {"g1": K1}}}
eq(picked([S1, S4]), [("g1", "2026-10-16T15:37:06Z"), ("g2", "2026-10-16T15:37:06Z")],
   "🔴 a look AFTER kickoff never withdraws a pick (only snapshots before kickoff count)")
S5 = {"taken_at": "2026-10-16T15:37:06Z", "game_model": [gp("g1")], "props_model": [pp("g1")]}
S6 = {"taken_at": "2026-10-16T16:40:52Z", "game_model": [], "props_model": [pp("g1")],
      "looked_at": {"game_model": {"g1": K1}, "props_model": {"g1": K1}}}
eq((picked([S5, S6]), picked([S5, S6], "props_model")), ([], [("g1", "2026-10-16T16:40:52Z")]),
   "🔴 each model is judged on its own: the game model withdrew g1, the props model still shows its pick")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE SNAPSHOT RECORDS EVERY UNSTARTED GAME EACH MODEL LOOKED AT")
# ══════════════════════════════════════════════════════════════════════
_r = tempfile.mkdtemp(prefix="ledgerwd-")
try:
    lat = os.path.join(_r, "data", "ncaaf", "latest")
    _w(os.path.join(lat, "fb-model.json"), {"picks": [], "win_chances": [
        {"game_id": "g1", "commence": K1, "p_home": 29.3, "p_away": 70.7},
        {"game_id": "g0", "commence": "2026-10-16T12:00:00Z", "p_home": 60.0, "p_away": 40.0}]})
    _w(os.path.join(lat, "fb-props-model.json"), {"picks": [], "rated": [
        {"game_id": "e1", "player": "Test Back", "market": "player_rush_yds", "line": 50.5, "side": "over", "p": 0.45},
        {"game_id": "e9", "player": "No Kick", "market": "player_rush_yds", "line": 40.5, "side": "over", "p": 0.5}]})
    _w(os.path.join(lat, "props.json.gz"), {"games": [{"id": "e1", "commence": K1}]}, gz=True)
    _res = LG.snapshot("ncaaf", _r, T("2026-10-16T16:40:52Z"), Q)
    ck(_res is not None, "🔴 a snapshot is written when the models looked at games but show no pick at all "
       "(otherwise a league-wide withdrawal would never be recorded)")
    _doc = json.load(gzip.open(_res[0], "rt", encoding="utf-8")) if _res else {}
    eq(_doc.get("looked_at"), {"game_model": {"g1": K1}, "props_model": {"e1": K1}},
       "🔴 looked_at: the game model's unstarted priced games (g0 already kicked off is left out) and the "
       "props model's rated games, kickoff from the props board (e9, no known kickoff, is left out)")
finally:
    shutil.rmtree(_r, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE REAL build(): THE WITHDRAWN PICK LEAVES; A GRADED ONE NEVER MOVES")
# ══════════════════════════════════════════════════════════════════════
_r = tempfile.mkdtemp(prefix="ledgerwd-")
try:
    lg = os.path.join(_r, "data", "ncaaf")
    lat = os.path.join(lg, "latest")
    # the pre-amendment 15:37 snapshot: g1 (not started yet) and gF (already final, graded once)
    _w(os.path.join(lg, "2026-10-10", "model-picks", "1500.json.gz"),
       {"taken_at": "2026-10-10T15:00:00Z", "game_model": [gp("gF", commence="2026-10-11T16:00:00Z")]}, gz=True)
    _w(os.path.join(lg, "2026-10-11", "ledger-grades", "2300.json.gz"),
       {"grades": [{"key": "game_model|gF|moneyline", "state": "graded", "won": False}]}, gz=True)
    _w(os.path.join(lg, "2026-10-16", "model-picks", "1537.json.gz"),
       {"taken_at": "2026-10-16T15:37:06Z", "game_model": [gp("g1")]}, gz=True)
    # the 16:40 build: the model still prices g1 but (one team per game) holds no pick for it
    _w(os.path.join(lat, "fb-model.json"), {"picks": [], "record": {},
                                            "win_chances": [{"game_id": "g1", "commence": K1}]})
    _w(os.path.join(lat, "fb-props-model.json"), {"picks": [], "rated": [], "record": {}})
    _w(os.path.join(lat, "schedule-2026.json.gz"), {"games": [
        {"id": "gF", "final": True, "home_score": 30, "away_score": 20}]}, gz=True)
    _before = sorted((p["game_id"], p["snapshot"]) for p in LG.ledger_picks(LG.snapshots("ncaaf", _r)))
    _after = LG.build("ncaaf", _r, out=os.path.join(_r, "b.json"), when=T("2026-10-16T16:40:52Z"), log=Q)
finally:
    shutil.rmtree(_r, ignore_errors=True)
_rows = lambda d: sorted((r["game"][:5], r["market"], r["state"], r["won"], r["shown_at"]) for r in d["picks"])  # noqa: E731
eq(_before, [("g1", "2026-10-16T15:37:06Z"), ("gF", "2026-10-10T15:00:00Z")],
   "⚠️ the case exists: before the 16:40 build the ledger holds the old 15:37 g1 pick and the graded gF pick")
eq(_rows(_after), [("North", "moneyline", "graded", False, "2026-10-10T15:00:00Z")],
   "🔴🔴 the real build: the withdrawn g1 pick is gone from the ledger, and the pick graded on 10-11 "
   "keeps its stored grade exactly")
