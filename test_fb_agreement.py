#!/usr/bin/env python3
"""test_fb_agreement.py — the card vs props-model label keeps the rules
`research/fb_agreement_spec.md` fixed before any scoring (Sam, 2026-09-25).

# @vacuity AGREE means the SAME side of the break-even — both above OR both below
#   file: fb_agreement.py
#   find:     return "AGREE" if (card_p >= be) == (model_p >= be) else "SPLIT"
#   with:     return "AGREE" if card_p >= be and model_p >= be else "SPLIT"
#
# @vacuity a row is graded on the last copy frozen BEFORE its kickoff
#   file: fb_agreement.py
#   find:             if d.get("taken_at", "") < (r.get("commence") or ""):
#   with:             if True:
#
# @vacuity two stored grades for one row: the FIRST stands
#   file: fb_agreement.py
#   find:             out.setdefault(g["key"], g)                # ⛔ the FIRST stored grade stands
#   with:             out[g["key"]] = g
#
# @vacuity the question's error is clustered by GAME, not by row
#   file: fb_agreement.py
#   find:         s = by.setdefault(r["game_id"], [0.0, 0.0])
#   with:         s = by.setdefault(id(r), [0.0, 0.0])
#
# @vacuity under the minimum sample the question is NOT YET MEASURABLE
#   file: fb_agreement.py
#   find:     if na < MIN_AGREE or ns < MIN_SPLIT or weeks < MIN_WEEKS:
#   with:     if False:
"""
import datetime
import glob
import gzip
import json
import os
import random
import shutil
import sys
import tempfile

from tcheck import ck, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import fb_agreement as AG  # noqa: E402
import fb_ledger  # noqa: E402

UTC = datetime.timezone.utc

section("1. THE LABEL")
ck(AG.label(60, 70, 50) == "AGREE" and AG.label(30, 40, 50) == "AGREE",
   "🔴🔴 AGREE: both above the break-even, or both below it")
ck(AG.label(60, 40, 50) == "SPLIT" and AG.label(40, 60, 50) == "SPLIT",
   "🔴 SPLIT: one above, one below")
ck(AG.label(None, 60, 50) == "ONE SOURCE" and AG.label(60, None, 50) == "ONE SOURCE"
   and AG.label(None, None, 50) is None,
   "🔴 ONE SOURCE: only one of them rates the row")
ck(AG.label(50, 50, 50) == "AGREE", "   ✅ exactly at the break-even counts as the ≥ side for both")

KICK = "2026-09-27T17:00:00Z"
card = {"picks": [
    {"game_id": "g1", "player": "Jonnu Smith", "market": "player_receptions", "side": "over", "line": 1.5,
     "price": 140, "break_even": 41.7, "confidence": 72, "confidence_basis": "RECORD", "commence": KICK},
    {"game_id": "g1", "player": "Drake London", "market": "player_anytime_td", "side": "yes", "line": None,
     "price": 185, "break_even": 35.1, "confidence": 30, "confidence_basis": "RECORD", "commence": KICK},
    {"game_id": "g2", "player": "Solo Row", "market": "player_rush_yds", "side": "under", "line": 40.5,
     "price": -110, "break_even": 52.4, "confidence": 60, "confidence_basis": "RECORD", "commence": KICK}]}
model = {"rated": [
    {"game_id": "g1", "player": "Jonnu Smith", "market": "player_receptions", "line": 1.5, "side": "over", "p": 35.1},
    {"game_id": "g1", "player": "Jonnu Smith", "market": "player_receptions", "line": 1.5, "side": "under", "p": 64.9},
    {"game_id": "g1", "player": "Drake London", "market": "player_anytime_td", "line": None, "side": "yes", "p": 28.3},
    {"game_id": "g2", "player": "Solo Row", "market": "player_rush_yds", "line": 40.5, "side": "over", "p": 55.0}],
    "picks": [{"game_id": "g1", "player": "Jonnu Smith", "market": "player_receptions", "side": "under",
               "line": {"value": 1.5, "basis": "MARKET"}, "price": {"value": -185, "basis": "MARKET"},
               "model_probability": {"value": 64.9, "basis": "MODEL"},
               "break_even": {"value": 64.9, "basis": "MARKET"}, "commence": KICK}]}
rs = {(r["player"], r["side"]): r for r in AG.rows(card, model)}
ck(rs[("Jonnu Smith", "over")]["label"] == "SPLIT" and rs[("Jonnu Smith", "over")]["model_p"] == 35.1
   and rs[("Jonnu Smith", "over")]["break_even"] == 41.7,
   "🔴🔴 the SAME side of the SAME rung: card over 72% vs the model's over 35.1%, at the card's break-even 41.7%")
ck(rs[("Drake London", "yes")]["label"] == "AGREE",
   "   ✅ a line-less market (anytime TD) joins too: 30% and 28.3% both under 35.1%")
ck(rs[("Solo Row", "under")]["label"] == "ONE SOURCE" and rs[("Solo Row", "under")]["model_p"] is None,
   "🔴 the model rating the OTHER side is not a rating of this one → ONE SOURCE")
ck(rs[("Jonnu Smith", "under")]["label"] == "ONE SOURCE" and rs[("Jonnu Smith", "under")]["card_p"] is None
   and len(rs) == 4, "   ✅ a model-only pick is labelled ONE SOURCE and every row is counted once")
ck(rs[("Jonnu Smith", "over")]["card_basis"] == "RECORD" and AG.BASES["model_p"] == "MODEL"
   and AG.BASES["break_even"] == "MARKET" and AG.BASES["label"] == "DESCRIPTIVE",
   "🔴 rule 55: label DESCRIPTIVE, model MODEL, break-even MARKET, and the card keeps its own basis (RECORD)")
_src = open(os.path.join(ROOT, "fb_props_model.py"), encoding="utf-8").read()
ck('doc["rated"] = rated' in _src and "rated.append(" in _src
   and _src.index("rated.append(") < _src.index("pk = pick_for(mk, rung, po, pu)"),
   "   ✅ the props model records every side it rates BEFORE (and apart from) choosing its pick")

section("2. FROZEN BEFORE KICKOFF, GRADED ONCE")
root = tempfile.mkdtemp(prefix="ag-")
_real = fb_ledger.grade_prop_pick
try:
    os.makedirs(os.path.join(root, "picks"))
    os.makedirs(os.path.join(root, "data", "nfl", "latest"))
    os.makedirs(os.path.join(root, "data", "ncaaf", "latest"))
    json.dump(card, open(os.path.join(root, "picks", "fb-nfl-latest.json"), "w"))
    json.dump(model, open(os.path.join(root, "data", "nfl", "latest", "fb-props-model.json"), "w"))
    arch = lambda k: sorted(glob.glob(os.path.join(root, "data", "nfl", "*", k, "*.json.gz")))  # noqa: E731
    AG.build("nfl", root=root, now=datetime.datetime(2026, 9, 26, 15, 0, tzinfo=UTC), log=lambda m: None, logs={})
    AG.build("nfl", root=root, now=datetime.datetime(2026, 9, 26, 15, 30, tzinfo=UTC), log=lambda m: None, logs={})
    ck(len(arch("agreement")) == 1, "🔴 labels are frozen when the card is built, and not again while unchanged")
    # a copy taken after kickoff flips the label; it must never be the one graded
    _late = os.path.join(root, "data", "nfl", "2026-09-27", "agreement")
    os.makedirs(_late, exist_ok=True)
    with gzip.open(os.path.join(_late, "1800.json.gz"), "wt") as fh:
        _row = [r for r in AG.rows(card, model) if r["player"] == "Jonnu Smith" and r["side"] == "over"][0]
        json.dump({"taken_at": "2026-09-27T18:00:00Z", "rows": [dict(_row, label="AGREE")]}, fh)
    fr = {r["key"]: r for r in AG.frozen_rows("nfl", root)}
    _k = AG.key_of("g1", "Jonnu Smith", "player_receptions", "over", 1.5)
    ck(fr[_k]["label"] == "SPLIT" and fr[_k]["taken_at"] == "2026-09-26T15:00:00Z",
       "🔴🔴 a row is graded on the last copy frozen BEFORE kickoff, never one taken after")
    fb_ledger.grade_prop_pick = lambda lg, p, logs, idx: ("graded", p["side"] != "over")
    AG.build("nfl", root=root, now=datetime.datetime(2026, 9, 28, 12, 0, tzinfo=UTC), log=lambda m: None, logs={})
    g = AG.stored_grades("nfl", root)
    ck(g[_k]["won"] is False and len(g) == 4, "   ✅ every frozen row is graded from the result")
    wgz = os.path.join(root, "data", "nfl", "2026-09-30", "agreement-grades")
    os.makedirs(wgz, exist_ok=True)
    with gzip.open(os.path.join(wgz, "0900.json.gz"), "wt") as fh:
        json.dump({"grades": [{"key": _k, "state": "graded", "won": True}]}, fh)
    ck(AG.stored_grades("nfl", root)[_k]["won"] is False,
       "🔴🔴 a row graded once is never re-graded: the FIRST stored grade stands")
    doc = json.load(open(os.path.join(root, "data", "nfl", "latest", "agreement.json"), encoding="utf-8"))
    ck(set(doc["record"]) == {"AGREE", "SPLIT", "ONE SOURCE"} and doc["kind"] == "DESCRIPTIVE"
       and doc["record"]["SPLIT"]["picks"]["value"] == 1 and "clustered by game" in doc["note"],
       "🔴 a record by label, in its own file, clustered by game")
finally:
    fb_ledger.grade_prop_pick = _real
    shutil.rmtree(root, ignore_errors=True)

section("3. THE PRE-REGISTERED QUESTION")
random.seed(3)


def mk(n_games, per, lab, p_win, be=50.0, lg="nfl", week0=0):
    out = []
    for i in range(n_games):
        day = (datetime.date(2026, 9, 7) + datetime.timedelta(days=7 * ((i + week0) % 6))).isoformat()
        for _j in range(per):
            out.append({"label": lab, "won": random.random() < p_win, "break_even": be,
                        "game_id": "%s%s%d" % (lg, lab, i), "commence": day + "T17:00:00Z", "league": lg})
    return out


base = mk(200, 2, "AGREE", 0.60) + mk(80, 2, "SPLIT", 0.45)
q = AG.question(base)
d, _p = AG.cr1_diff(base)
_ma = sum((1.0 if r["won"] else 0.0) - 0.5 for r in base if r["label"] == "AGREE") / 400
_ms = sum((1.0 if r["won"] else 0.0) - 0.5 for r in base if r["label"] == "SPLIT") / 160
ck(abs(d - (_ma - _ms)) < 1e-12 and q["state"] == "PASSES" and q["p"] < 0.05,
   "🔴 Δ is mean(won − break-even) of AGREE minus SPLIT; a real gap on enough games PASSES",
   "got %r" % q)
random.seed(11)
mild = mk(200, 2, "AGREE", 0.53) + mk(80, 2, "SPLIT", 0.50)
_pm = AG.cr1_diff(mild)[1]
dup = [dict(r) for r in mild for _k in range(5)]
ck(0.05 < _pm < 0.6 and abs(AG.cr1_diff(dup)[1] - _pm) < 0.02,
   "🔴🔴 clustered by GAME: copying every row five times inside its game does not make it more significant",
   "p %s -> %s" % (_pm, AG.cr1_diff(dup)[1]))
ck(AG.question(mk(40, 2, "AGREE", 0.9) + mk(20, 2, "SPLIT", 0.1))["state"] == "NOT YET MEASURABLE",
   "🔴 under 300 AGREE / 100 SPLIT graded rows it is NOT YET MEASURABLE, however big the gap")
ck(AG.question(mk(200, 2, "AGREE", 0.45) + mk(80, 2, "SPLIT", 0.60))["state"] == "FAILS",
   "   ✅ enough rows and no gap FAILS")
ck("Nothing changes on its own" in q["consequence"],
   "   ✅ whatever the answer, nothing changes on its own — Sam decides")
