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
#
# @vacuity a game that has kicked off shows its FROZEN label, never a fresh one
#   file: fb_agreement.py
#   find:     started = {r["game_id"] for r in rs if (r.get("commence") or "") <= now_s}
#   with:     started = set()
#
# @vacuity a started row that was never frozen carries NO label, never ONE SOURCE
#   file: fb_agreement.py
#   find:             out.append(dict(r, label=None, model_p=None, frozen_before_kickoff=False, label_note=NOT_FROZEN))
#   with:             out.append(dict(r, frozen_before_kickoff=False, label_note=NOT_FROZEN))
#
# @vacuity a started row finds ITS OWN frozen copy by key
#   file: fb_agreement.py
#   find:         f = by_game.get(r["game_id"], {}).get(r["key"])
#   with:         f = None
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

from tcheck import ck, note, section

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


section("4. 🔴🔴 A GAME THAT HAS KICKED OFF KEEPS ITS FROZEN LABEL")
# `[2026-09-26]` The defect: the props model rates only games NOT yet
# started, so relabelling after kickoff found no model number and every
# row read ONE SOURCE — 25/25 NFL and 23/23 college on the live file.
root = tempfile.mkdtemp(prefix="ag4-")
try:
    lat = os.path.join(root, "data", "nfl", "latest")
    os.makedirs(lat)
    os.makedirs(os.path.join(root, "data", "ncaaf", "latest"))
    os.makedirs(os.path.join(root, "picks"))
    K1, K0 = "2026-09-27T17:00:00Z", "2026-09-26T13:00:00Z"   # g1 later; g0 kicked off before any build
    card4 = {"picks": [
        {"game_id": "g1", "player": "Agree Guy", "market": "player_rush_yds", "side": "over", "line": 50.5,
         "price": -110, "break_even": 52.4, "confidence": 70, "confidence_basis": "RECORD", "commence": K1},
        {"game_id": "g0", "player": "Early Guy", "market": "player_rush_yds", "side": "over", "line": 40.5,
         "price": -110, "break_even": 52.4, "confidence": 60, "confidence_basis": "RECORD", "commence": K0}]}
    json.dump(card4, open(os.path.join(root, "picks", "fb-nfl-latest.json"), "w"))
    # before kickoff the model rates g1 on the same side of the break-even -> AGREE,
    # and at 14:00 it also picked a row it had dropped by 15:00
    _rated = [{"game_id": "g1", "player": "Agree Guy", "market": "player_rush_yds", "line": 50.5,
               "side": "over", "p": 61.0}]
    _drop = {"game_id": "g1", "player": "Dropped Guy", "market": "player_receptions", "side": "over",
             "line": {"value": 3.5}, "price": {"value": 120}, "model_probability": {"value": 55.0},
             "break_even": {"value": 45.5}, "commence": K1}
    json.dump({"rated": _rated, "picks": [_drop]}, open(os.path.join(lat, "fb-props-model.json"), "w"))
    AG.build("nfl", root=root, now=datetime.datetime(2026, 9, 26, 14, 0, tzinfo=UTC), log=lambda m: None, logs={})
    json.dump({"rated": _rated, "picks": []}, open(os.path.join(lat, "fb-props-model.json"), "w"))
    before = datetime.datetime(2026, 9, 26, 15, 0, tzinfo=UTC)
    d0 = AG.build("nfl", root=root, now=before, log=lambda m: None, logs={})
    # after kickoff the model rates nothing for g1 (it only rates games not started)
    json.dump({"rated": [], "picks": []}, open(os.path.join(lat, "fb-props-model.json"), "w"))
    after = datetime.datetime(2026, 9, 27, 18, 30, tzinfo=UTC)
    AG.build("nfl", root=root, now=after, log=lambda m: None, logs={})
    page = json.load(open(os.path.join(lat, "agreement.json"), encoding="utf-8"))
    by = {r["player"]: r for r in page["rows"]}
    ck({r["player"]: r["label"] for r in d0["rows"]}.get("Agree Guy") == "AGREE",
       "   ✅ before kickoff: the card (70%) and the model (61%) both sit above the 52.4% break-even -> AGREE")
    ck(by["Agree Guy"]["label"] == "AGREE" and by["Agree Guy"]["frozen_before_kickoff"] is True
       and by["Agree Guy"]["frozen_at"] == "2026-09-26T15:00:00Z" and by["Agree Guy"]["model_p"] == 61.0
       and page["counts"]["AGREE"] == 1,
       "🔴🔴 after kickoff the PAGE FILE still reads AGREE — the label frozen before kickoff, marked as "
       "such — never a fresh ONE SOURCE", "got %r" % by.get("Agree Guy"))
    ck(by["Early Guy"]["label"] is None and by["Early Guy"]["label_note"] == AG.NOT_FROZEN
       and page["counts"]["ONE SOURCE"] == 0 and page["not_frozen"] == 1,
       "🔴 a started row that was never frozen shows NO label and says so — never ONE SOURCE",
       "got %r" % by.get("Early Guy"))
    ck("Dropped Guy" not in by and any(r["player"] == "Dropped Guy" for r in AG.frozen_rows("nfl", root))
       and len(page["rows"]) == 2,
       "🔴 a started game shows exactly the rows its card still shows: a frozen row no longer on the "
       "board is not counted there (the record still holds it)")
    ck(all(r.get("frozen_before_kickoff") is True or r["label"] is None
           for r in page["rows"] if r["commence"] <= page["built_at"]),
       "🔴 the class: no row of a started game carries a label computed after its kickoff")
finally:
    shutil.rmtree(root, ignore_errors=True)

section("5. ...AND ON THE REAL STORED CARDS, MODEL FILES AND FROZEN COPIES")
# Driven against the real artifacts (copied, never written in place), with
# the clock set after every card game's kickoff, so every row is settled.
_seen = 0
for _lg in AG.LEAGUES:
    _card = os.path.join(ROOT, "picks", "fb-%s-latest.json" % _lg)
    _cp = (json.load(open(_card, encoding="utf-8")).get("picks") or []) if os.path.exists(_card) else []
    _ks = [r.get("commence") for r in _cp if r.get("commence")]
    if not _ks:
        continue
    rt = tempfile.mkdtemp(prefix="ag5-")
    try:
        os.makedirs(os.path.join(rt, "picks"))
        shutil.copy(_card, os.path.join(rt, "picks"))
        for _o in AG.LEAGUES:
            os.makedirs(os.path.join(rt, "data", _o, "latest"), exist_ok=True)
        _mf = os.path.join(ROOT, "data", _lg, "latest", "fb-props-model.json")
        if os.path.exists(_mf):
            shutil.copy(_mf, os.path.join(rt, "data", _lg, "latest"))
        for _a in glob.glob(os.path.join(ROOT, "data", _lg, "20*", "agreement", "*.json.gz")):
            _dst = os.path.join(rt, os.path.relpath(_a, ROOT))
            os.makedirs(os.path.dirname(_dst), exist_ok=True)
            shutil.copy(_a, _dst)
        _now = datetime.datetime.strptime(max(_ks), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC) \
            + datetime.timedelta(hours=1)
        _doc = AG.build(_lg, root=rt, now=_now, log=lambda m: None, logs={})
        _fz = {r["key"]: r["label"] for r in AG.frozen_rows(_lg, rt)}
        _started = [r for r in _doc["rows"] if r["commence"] <= _doc["built_at"]]
        _bad = [r["key"] for r in _started
                if not ((r.get("frozen_before_kickoff") and r["label"] == _fz.get(r["key"]))
                        or (r["label"] is None and r.get("label_note") == AG.NOT_FROZEN))]
        _seen += len(_started)
        if not _started:
            note("%s: the real card has no rated row on a started game today — nothing to drive" % _lg)
            continue
        ck(not _bad,
           "🔴 %s, real files: all %d started rows show their frozen label (%d) or no label (%d) — "
           "none relabelled after kickoff" % (_lg, len(_started),
                                              sum(1 for r in _started if r.get("frozen_before_kickoff")),
                                              sum(1 for r in _started if r["label"] is None)),
           "relabelled: %s" % _bad[:3])
    finally:
        shutil.rmtree(rt, ignore_errors=True)
note("real-file drive: %d started row(s) checked across both leagues (section 4 is the guard; this "
     "confirms the real files, and a day with none to drive is noted, never failed)" % _seen)
