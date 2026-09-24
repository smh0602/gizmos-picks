#!/usr/bin/env python3
"""test_fb_ledger.py — the football models' frozen ledger and verdict
labels keep the rules in `research/fb_model_live_spec.md` (Sam, 2026-09-24).

# @vacuity a snapshot saves only games that have not kicked off
#   file: fb_ledger.py
#   find:     game = [p for p in gm.get("picks") or [] if (p.get("commence") or "") > now]
#   with:     game = list(gm.get("picks") or [])
#
# @vacuity the ledger never takes a pick from a snapshot after kickoff
#   file: fb_ledger.py
#   find:                 if s["taken_at"] < (ps[0].get("commence") or ""):
#   with:                 if True:
#
# @vacuity the LAST snapshot before kickoff is the one that counts
#   file: fb_ledger.py
#   find:                     chosen[(model, gid)] = (s["taken_at"], ps)
#   with:                     chosen.setdefault((model, gid), (s["taken_at"], ps))
#
# @vacuity nothing dated before the ledger's start is ever added
#   file: fb_ledger.py
#   find:         if day < LEDGER_FROM:
#   with:         if False:
#
# @vacuity a graded pick is never graded again
#   file: fb_ledger.py
#   find:             if p["key"] in stored:
#   with:             if False:
#
# @vacuity the FIRST stored grade of a pick is the one that stands
#   file: fb_ledger.py
#   find:             out.setdefault(g["key"], g)
#   with:             out[g["key"]] = g
#
# @vacuity an NFL player who took no snaps is VOID in the ledger
#   file: fb_ledger.py
#   find:     ok, _why = record_fb._played(g)
#   with:     ok = True
#
# @vacuity PROVEN needs at least 300 picks
#   file: fb_model.py
#   find:     if n >= VERDICT_MIN_N and mean is not None and mean > 0 and pval is not None and pval < VERDICT_ALPHA:
#   with:     if mean is not None and mean > 0 and pval is not None and pval < VERDICT_ALPHA:
#
# @vacuity LOSING is the TOP of the 95% range below break-even
#   file: fb_model.py
#   find:     elif iv is not None and be is not None and iv[1] < be:
#   with:     elif iv is not None and be is not None and iv[0] < be:
#
# @vacuity the verdict's test clusters by GAME
#   file: fb_model.py
#   find:     _n, mean, _t, pval, G = mlb_refit.paired_test_clustered(d, [p["game_id"] for p in graded])
#   with:     _n, mean, _t, pval, G = mlb_refit.paired_test_clustered(d, list(range(n)))
#
# @vacuity the page shows the ledger after the models
#   file: index.html
#   find:   if (v && v.isConnected !== false) v.insertAdjacentHTML('beforeend', fbModelHtml(M) + fbPropModelHtml(PM) + fbLedgerHtml(LD));
#   with:   if (v && v.isConnected !== false) v.insertAdjacentHTML('beforeend', fbModelHtml(M) + fbPropModelHtml(PM));
"""
import datetime
import glob
import gzip
import json
import os
import shutil
import sys
import tempfile

from tcheck import ck

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import fb_ledger as LG  # noqa: E402
import fb_model as F  # noqa: E402
import jsblock  # noqa: E402

Q = lambda *a, **k: None  # noqa: E731


def T(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _w(path, doc, gz=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if gz:
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(doc, fh)
    else:
        json.dump(doc, open(path, "w", encoding="utf-8"))


def _gp(gid, commence, side="home", line=3.0, market="spread"):
    return {"game_id": gid, "commence": commence, "market": market, "side": side,
            "team": "HOM", "game": "A at H", "line": {"value": line, "basis": "MARKET"},
            "price": {"value": -110, "basis": "MARKET"}, "book": "DraftKings",
            "model_probability": {"value": 58.0, "basis": "MODEL"},
            "break_even": {"value": 52.4, "basis": "MARKET"}}


def _tree():
    root = tempfile.mkdtemp()
    lat = os.path.join(root, "data", "nfl", "latest")
    _w(os.path.join(lat, "fb-model.json"), {"picks": [
        _gp("g1", "2026-09-27T17:00:00Z"), _gp("g0", "2026-09-24T12:00:00Z")],
        "record": {"spread": {"verdict": {"label": "NOT YET MEASURABLE", "picks": 3, "min_picks": 300}}}})
    _w(os.path.join(lat, "fb-props-model.json"), {"picks": [
        {"game_id": "e1", "commence": "2026-09-27T17:00:00Z", "player": "Test Back",
         "market": "player_rush_yds", "side": "over", "line": {"value": 50.5, "basis": "MARKET"},
         "break_even": {"value": 52.4, "basis": "MARKET"}}], "record": {}})
    _w(os.path.join(lat, "schedule-2026.json.gz"), {"games": [
        {"id": "g1", "final": True, "home_score": 24, "away_score": 20},
        {"id": "g2", "final": True, "home_score": 23, "away_score": 20}]}, gz=True)
    _w(os.path.join(lat, "players-2026.json.gz"), {"players": {"p1": {"name": "Test Back", "pos": "RB", "g": [
        {"d": "2026-09-27", "snaps": 0, "snap_pct": 0.0, "rush_yds": 0.0, "car": 0.0, "game_id": "x"}]}}}, gz=True)
    return root


# ══════════════════════════════════════════════════════════════════════
# 1. THE SNAPSHOT: games not yet kicked off, written once
# ══════════════════════════════════════════════════════════════════════
_r = _tree()
try:
    _p, _wrote = LG.snapshot("nfl", _r, T("2026-09-25T10:00:00Z"), Q)
    _doc = json.load(gzip.open(_p, "rt"))
    ck([p["game_id"] for p in _doc["game_model"]] == ["g1"],
       "🔴🔴 a snapshot saves only games that have NOT kicked off (g0 already started)",
       "got %r" % [p["game_id"] for p in _doc["game_model"]])
    _p2, _wrote2 = LG.snapshot("nfl", _r, T("2026-09-25T10:00:30Z"), Q)
    ck(_wrote and not _wrote2 and _p2 == _p,
       "🔴 a snapshot is WRITE-ONCE: a second run in the same minute leaves the first alone (daystore)")
finally:
    shutil.rmtree(_r, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
# 2. WHICH SNAPSHOT COUNTS: the last before kickoff; nothing before the start
# ══════════════════════════════════════════════════════════════════════
_s = [{"taken_at": "2026-09-26T10:00:00Z", "game_model": [_gp("g1", "2026-09-27T17:00:00Z", side="home")]},
      {"taken_at": "2026-09-27T14:00:00Z", "game_model": [_gp("g1", "2026-09-27T17:00:00Z", side="away")]},
      {"taken_at": "2026-09-27T18:00:00Z", "game_model": [_gp("g1", "2026-09-27T17:00:00Z", side="home", line=9.0)]}]
_lp = LG.ledger_picks(_s)
ck(len(_lp) == 1 and _lp[0]["side"] == "away" and _lp[0]["snapshot"] == "2026-09-27T14:00:00Z",
   "🔴🔴 the pick that counts is the LAST one shown BEFORE kickoff (14:00 'away') — never an earlier "
   "one, never one after kickoff",
   "got %r" % [(p["side"], p["snapshot"]) for p in _lp])
_r = _tree()
try:
    _w(os.path.join(_r, "data", "nfl", "2026-09-23", "model-picks", "1000.json.gz"),
       {"taken_at": "2026-09-23T10:00:00Z", "game_model": [_gp("gX", "2026-09-23T17:00:00Z")]}, gz=True)
    _w(os.path.join(_r, "data", "nfl", "2026-09-25", "model-picks", "1000.json.gz"),
       {"taken_at": "2026-09-25T10:00:00Z", "game_model": [_gp("g1", "2026-09-27T17:00:00Z")]}, gz=True)
    ck([s["taken_at"] for s in LG.snapshots("nfl", _r)] == ["2026-09-25T10:00:00Z"],
       "🔴 the ledger starts 2026-09-24: an earlier snapshot is never added")
finally:
    shutil.rmtree(_r, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
# 3. GRADED ONCE, THEN FROZEN
# ══════════════════════════════════════════════════════════════════════
_r = _tree()
try:
    _w(os.path.join(_r, "data", "nfl", "2026-09-25", "model-picks", "1000.json.gz"),
       {"taken_at": "2026-09-25T10:00:00Z", "game_model": [_gp("g1", "2026-09-27T17:00:00Z", line=3.0),
                                                           _gp("g2", "2026-09-27T17:00:00Z", line=3.0)],
        "props_model": [{"game_id": "e1", "commence": "2026-09-27T17:00:00Z", "player": "Test Back",
                         "market": "player_rush_yds", "side": "over",
                         "line": {"value": 50.5, "basis": "MARKET"}}]}, gz=True)
    # an EARLIER stored grade says g1 LOST; today's schedule says it won
    _w(os.path.join(_r, "data", "nfl", "2026-09-27", "ledger-grades", "2300.json.gz"),
       {"grades": [{"key": "game_model|g1|spread", "state": "graded", "won": False}]}, gz=True)
    _w(os.path.join(_r, "data", "nfl", "2026-09-28", "ledger-grades", "0100.json.gz"),
       {"grades": [{"key": "game_model|g1|spread", "state": "graded", "won": True}]}, gz=True)
    _d = LG.build("nfl", _r, out=os.path.join(_r, "led.json"), when=T("2026-09-28T12:00:00Z"), log=Q)
    _by = {(r["model"], r.get("market"), r.get("game")): r for r in _d["picks"]}
    _g1 = [r for r in _d["picks"] if r["model"] == "game_model" and r["state"] == "graded"
           and r["commence"] == "2026-09-27T17:00:00Z"]
    _states = sorted((r["model"], r["state"], r["won"]) for r in _d["picks"])
    ck(("game_model", "graded", False) in _states,
       "🔴🔴 a stored grade is NEVER recalculated — the FIRST stored result stands, whatever today's data says",
       "⛔ Sam: 'never recalculates the past'. got %r" % _states)
    ck(("game_model", "void", None) in _states,
       "🔴 a push (23-20 on 3) is void, graded once and stored", "got %r" % _states)
    ck(("props_model", "void", None) in _states,
       "🔴 an NFL player who took no snaps is VOID in the ledger — never a winning under", "got %r" % _states)
    _gfiles = glob.glob(os.path.join(_r, "data", "nfl", "*", "ledger-grades", "*.json.gz"))
    _new = [g for f in _gfiles for g in json.load(gzip.open(f, "rt"))["grades"]]
    ck(sum(1 for g in _new if g["key"] == "game_model|g1|spread") == 2,
       "   ✅ ...and no new grade was written for a pick already graded", "got %r" % _new)
finally:
    shutil.rmtree(_r, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
# 4. THE VERDICT, in Sam's order
# ══════════════════════════════════════════════════════════════════════


def _picks(n, hit_every, be=0.524, games_per=1):
    return [{"game_id": "g%d" % (i // games_per), "won": (i % hit_every != 0), "break_even": be,
             "state": "graded"} for i in range(n)]


_win = F.verdict(_picks(400, 3))            # hits 2 of 3 = 66.7% vs 52.4%
ck(_win["label"] == "PROVEN", "✅ 400 picks at 67% against 52% break-even is PROVEN", "got %r" % _win)
ck(F.verdict(_picks(200, 3))["label"] != "PROVEN",
   "🔴 PROVEN needs at least 300 picks — 200 winning picks are not enough",
   "got %r" % F.verdict(_picks(200, 3)))
_lose = F.verdict([{"game_id": "g%d" % i, "won": i % 4 == 0, "break_even": 0.524} for i in range(200)])
ck(_lose["label"] == "LOSING",
   "🔴🔴 LOSING when the TOP of the 95% range is below break-even (25% on 200 picks), even under 300",
   "got %r" % _lose)
_near = F.verdict([{"game_id": "g%d" % i, "won": i % 2 == 0, "break_even": 0.524} for i in range(400)])
ck(_near["label"] == "NOT PROVEN",
   "✅ 50% on 400 picks: not proven, not losing (the range still reaches 52.4%)", "got %r" % _near)
ck(F.verdict(_picks(40, 3))["label"] == "NOT YET MEASURABLE",
   "✅ 40 winning picks are NOT YET MEASURABLE")
_clu = F.verdict(_picks(400, 3, games_per=4))
ck(_clu["games"] == 100,
   "🔴 the verdict's test clusters by GAME (400 picks from 100 games)", "got %r" % _clu)
ck(_win.get("basis") == "DESCRIPTIVE", "   ⚠️ ...and the label is labelled DESCRIPTIVE (rule 55)")

# ══════════════════════════════════════════════════════════════════════
# 5. THE PAGE
# ══════════════════════════════════════════════════════════════════════
_html = os.path.join(ROOT, "index.html")
_app = jsblock.js_block("fbModelAppend", _html)
_lh = jsblock.js_block("fbLedgerHtml", _html)
_mh = jsblock.js_block("fbModelHtml", _html)
_ph = jsblock.js_block("fbPropModelHtml", _html)
ck("fbLedgerHtml(LD)" in _app and "What the model showed, graded" in _lh and "Hit" in _lh and "Miss" in _lh,
   "🔴 the page shows 'What the model showed, graded', every pick marked hit or miss, after the models")
ck("fbVerdictTag(r.verdict)" in _mh and "fbVerdictTag(r.verdict)" in _ph and "fbVerdictTag(r.verdict)" in _lh,
   "🔴 the verdict label sits next to every record: game model, props model and the ledger")
