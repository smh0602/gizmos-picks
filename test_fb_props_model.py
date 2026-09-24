#!/usr/bin/env python3
"""test_fb_props_model.py — the football props model keeps the promises
in `research/fb_props_design.md` (Sam, 2026-09-24).

# @vacuity a prop snapshot pulled after kickoff is never a price
#   file: fb_props_model.py
#   find:             if not pulled or not c or pulled >= c:
#   with:             if not pulled or not c:
#
# @vacuity only Hard Rock, FanDuel and DraftKings prop prices are used
#   file: fb_props_model.py
#   find:         if b not in ok:
#   with:         if False:
#
# @vacuity two prices are compared only at the EXACT same line
#   file: fb_props_model.py
#   find:                 key = (who, mk, None if mk == TD_MARKET else float(line))
#   with:                 key = (who, mk, None)
#
# @vacuity a week's model never trains on a game played on that week's Monday or later
#   file: fb_props_model.py
#   find:         while todo and day >= todo[0]:
#   with:         while todo and day > todo[0]:
#
# @vacuity yardage inputs sit on the target's own square-root scale
#   file: fb_props_model.py
#   find:         tf = (lambda v: math.sqrt(max(v, 0.0))) if market in YARDS else (lambda v: v)  # noqa: E731
#   with:         tf = (lambda v: v)  # noqa: E731
#
# @vacuity an NFL player who took no snaps is VOID, never a graded under
#   file: fb_props_model.py
#   find:     ok, _why = record_fb._played(g)
#   with:     ok = True
#
# @vacuity the card's own price floors bound every model pick
#   file: fb_props_model.py
#   find:         if not (card_fb.PRICE_FLOOR <= px <= card_fb.PRICE_CEIL):
#   with:         if False:
#
# @vacuity a prop pick needs a positive expected value
#   file: fb_props_model.py
#   find:     return best if best and best["ev"] > 0 else None
#   with:     return best
#
# @vacuity the champion is scored on the card's own P(over), not another side
#   file: fb_props_model.py
#   find:                              "yes" if market == TD_MARKET else "over")
#   with:                              "yes" if market == TD_MARKET else "under")
#
# @vacuity d = card loss − model loss, so d > 0 means the model predicted better
#   file: fb_props_model.py
#   find:     d = [logloss(r["p_card"], r["y"]) - logloss(r["p_model"], r["y"]) for r in pr]
#   with:     d = [logloss(r["p_model"], r["y"]) - logloss(r["p_card"], r["y"]) for r in pr]
#
# @vacuity the paired test clusters by GAME
#   file: fb_props_model.py
#   find:     n, mean, t, p, G = mlb_refit.paired_test_clustered(d, [r["game"] for r in pr])
#   with:     n, mean, t, p, G = mlb_refit.paired_test_clustered(d, list(range(len(pr))))
#
# @vacuity one league alone is never the verdict
#   file: fb_props_model.py
#   find:     if dec["leagues"] != ["ncaaf", "nfl"]:
#   with:     if False:
#
# @vacuity the builder caps the page's list at the card's BOARD_MAX
#   file: fb_props_model.py
#   find:     return live[:card_fb.BOARD_MAX], live[card_fb.BOARD_MAX:]
#   with:     return live, []
#
# @vacuity the page shows the props model beside the card, after it
#   file: index.html
#   find:   if (v && v.isConnected !== false) v.insertAdjacentHTML('beforeend', fbModelHtml(M) + fbPropModelHtml(PM));
#   with:   if (v && v.isConnected !== false) v.insertAdjacentHTML('beforeend', fbModelHtml(M));
"""
import gzip
import json
import os
import shutil
import sys
import tempfile

from tcheck import ck

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import card_fb  # noqa: E402
import fb_props_model as M  # noqa: E402
import jsblock  # noqa: E402

RUSH = "player_rush_yds"

# ══════════════════════════════════════════════════════════════════════
# 1. PRICES: before kickoff, three books, the exact line
# ══════════════════════════════════════════════════════════════════════
_tmp = tempfile.mkdtemp()
try:
    _dir = os.path.join(_tmp, "data", "nfl", "2026-09-20", "props-player")
    os.makedirs(_dir)
    _ev = {"id": "e1", "commence_time": "2026-09-20T17:00:00Z", "home_team": "H", "away_team": "A",
           "bookmakers": [{"key": "draftkings", "markets": [{"key": RUSH, "outcomes": [
               {"name": "Over", "description": "Test Back", "price": -110, "point": 50.5}]}]}]}
    for hhmm, pulled, px in (("1100", "2026-09-20T11:00:00Z", -110), ("1800", "2026-09-20T18:00:00Z", +500)):
        e = json.loads(json.dumps(_ev))
        e["bookmakers"][0]["markets"][0]["outcomes"][0]["price"] = px
        with gzip.open(os.path.join(_dir, hhmm + ".json.gz"), "wt", encoding="utf-8") as fh:
            json.dump({"pulled_at": pulled, "events": [e]}, fh)
    _snap = M.prop_snapshots("nfl", _tmp)
    ck(_snap["e1"][0] == "2026-09-20T11:00:00Z",
       "🔴🔴 a prop snapshot pulled AFTER kickoff is never a price",
       "⛔ the 18:00 snapshot of a 17:00 kickoff is a live price. kept %r" % (_snap["e1"][0],))
finally:
    shutil.rmtree(_tmp, ignore_errors=True)

_ev2 = {"bookmakers": [
    {"key": "draftkings", "markets": [{"key": RUSH, "outcomes": [
        {"name": "Over", "description": "Test Back", "price": -110, "point": 50.5},
        {"name": "Under", "description": "Test Back", "price": -110, "point": 50.5}]}]},
    {"key": "fanduel", "markets": [{"key": RUSH, "outcomes": [
        {"name": "Over", "description": "Test Back", "price": 100, "point": 52.5}]}]},
    {"key": "betmgm", "markets": [{"key": RUSH, "outcomes": [
        {"name": "Over", "description": "Test Back", "price": 200, "point": 50.5}]}]}]}
_r = M.rungs_of("nfl", _ev2)
_k = ("Test Back", RUSH, 50.5)
ck(_k in _r and _r[_k]["best"]["over"] == (-110, "draftkings") and "betmgm" not in _r[_k]["books"],
   "🔴🔴 only Hard Rock, FanDuel and DraftKings prices — BetMGM's +200 never appears",
   "got %r" % (_r.get(_k),))
ck(("Test Back", RUSH, 52.5) in _r and len(_r) == 2,
   "🔴 FanDuel's 52.5 is its own rung — prices are compared only at the exact same line",
   "⛔ CLAUDE.md: never compare two prices without confirming they are the same wager. got %r"
   % sorted(_r))
ck(abs(M.market_prob(RUSH, _r[_k]) - 0.5) < 1e-9,
   "   ✅ ...and the market's own probability is DraftKings' two sides, de-vigged")

# ══════════════════════════════════════════════════════════════════════
# 2. POINT IN TIME: history before the game, the week before its Monday
# ══════════════════════════════════════════════════════════════════════


def _g(d, gid, yds, car=20):
    return {"d": d, "game_id": gid, "team": "T", "o": "O", "home": 1, "snaps": 30,
            "snap_pct": 0.6, "rush_yds": yds, "car": car}


_logs = {2025: {"p1": {"name": "Test Back", "pos": "RB", "g": [
    _g("2025-09-07", "g1", 100.0), _g("2025-09-14", "g2", 144.0), _g("2025-09-15", "g3", 60.0)]}}}
_snaps, _final, _kept, _H = M.stream("nfl", _logs, ["2025-09-15"], "2025-09-01")
ck(("p1", "2025-09-07") not in _kept,
   "🔴 a player's first game has no inputs — it cannot read itself")
ck(_snaps["2025-09-15"][RUSH].n == 1,
   "🔴🔴 the model for the week of Monday 09-15 never trains on a game played that Monday",
   "⛔ a Monday-night game would be predicting itself. trained on %d rows" % _snaps["2025-09-15"][RUSH].n)
_x = _kept[("p1", "2025-09-14")][RUSH]
ck(abs(_x[0] - 10.0) < 1e-9,
   "🔴 yardage inputs are on the target's √ scale: one earlier 100-yard game reads 10, not 100",
   "⛔ raw yards into a straight line to √yards projected 218 on a 96.5 line. got %r" % _x[0])

# ══════════════════════════════════════════════════════════════════════
# 3. OUTCOMES: the card's own grader
# ══════════════════════════════════════════════════════════════════════
with M.league("nfl"):
    _void = M.outcome("nfl", RUSH, 50.5, dict(_g("2026-09-20", "x", 0.0), snaps=0))
    _won = M.outcome("nfl", RUSH, 50.5, _g("2026-09-20", "x", 60.0))
    _push = M.outcome("nfl", RUSH, 60.0, _g("2026-09-20", "x", 60.0))
ck(_void is None,
   "🔴🔴 an NFL player who took no snaps is VOID — never a winning under",
   "got %r" % _void)
ck(_won == 1 and _push is None, "   ✅ ...60 yards over 50.5 is an over, and 60 on 60.0 is a push, left out")

# ══════════════════════════════════════════════════════════════════════
# 4. THE PICK RULE: the card's floors, positive EV
# ══════════════════════════════════════════════════════════════════════
_rung = {"best": {"over": (-900, "draftkings"), "under": (150, "fanduel")}}
ck(M.pick_for(RUSH, _rung, 0.99, 0.01) is None,
   "🔴 a side priced below the card's −700 floor is never picked, however likely",
   "got %r" % M.pick_for(RUSH, _rung, 0.99, 0.01))
_even = {"best": {"over": (-110, "draftkings"), "under": (-110, "fanduel")}}
ck(M.pick_for(RUSH, _even, 0.5, 0.5) is None,
   "🔴 a coin flip never picks into the vig — EV must be above zero")
ck((M.pick_for(RUSH, _even, 0.6, 0.4) or {}).get("side") == "over",
   "   ✅ ...and a real edge picks the right side")

# ══════════════════════════════════════════════════════════════════════
# 5. THE CHAMPION: the card's own probability, recomputed
# ══════════════════════════════════════════════════════════════════════
_cp = {"p": {"name": "Test Back", "pos": "RB",
             "g": [_g("2025-%02d-01" % (9 + i // 4), "c%d" % i, v) for i, v in
                   enumerate((60.0, 70.0, 80.0, 20.0, 90.0, 100.0))]}}
_ci = card_fb.index_by_name(_cp)
_pc, _pid = M.champion_prob("nfl", _cp, _ci, None, "Test Back", RUSH, 50.5)
with M.league("nfl"):
    _direct = card_fb.rate_for(_cp["p"]["g"], RUSH, 50.5, "over")
ck(_pid == "p" and _direct and abs(_pc - _direct[0] / 100.0) < 1e-12 and abs(_pc - 0.79) < 1e-12,
   "🔴🔴 the champion is the card's OWN rate_for P(over), 5 of 6 smoothed = 79%",
   "got %r vs rate_for %r" % (_pc, _direct))

# ══════════════════════════════════════════════════════════════════════
# 6. THE DECISION: sign, clustering by game, both leagues
# ══════════════════════════════════════════════════════════════════════
_rows = [{"game": "nfl:g%d" % (i // 3), "y": 1, "p_card": 0.5, "p_model": 0.6} for i in range(600)]
_d = M.paired(_rows)
ck(_d["mean_d"] > 0, "🔴🔴 d = card loss − model loss, so a better model has d > 0", "got %r" % _d["mean_d"])
ck(_d["clusters"] == 200,
   "🔴🔴 clustered by GAME — three props of one game are one cluster",
   "⛔ Sam: 'clustered by game'. 600 rows from 200 games gave %r" % _d["clusters"])
ck(M.paired(_rows[:300])["verdict"] == "NOT YET MEASURABLE",
   "🔴 under 500 predictions the verdict is NOT YET MEASURABLE")
_tmp = tempfile.mkdtemp()
try:
    _one = M.pooled_decision("nfl", [[r["game"], RUSH, 1, 0.5, 0.9] for r in _rows], _tmp)
finally:
    shutil.rmtree(_tmp, ignore_errors=True)
ck(_one["verdict"].startswith("INCOMPLETE"),
   "🔴🔴 one league alone is never the verdict — Sam's rule pools both",
   "⛔ found 2026-09-24: college alone read as the pooled verdict. got %r" % _one["verdict"])

# ══════════════════════════════════════════════════════════════════════
# 7. THE PAGE: its own MODEL section, after the card, record per market
# ══════════════════════════════════════════════════════════════════════
_html = os.path.join(ROOT, "index.html")
_app = jsblock.js_block("fbModelAppend", _html)
_pm = jsblock.js_block("fbPropModelHtml", _html)
ck("fbPropModelHtml(PM)" in _app and "k-model" in _pm and "labN(r.hit_rate" in _pm
   and "labN(r.break_even" in _pm and "board_max" not in _pm and ".slice(" not in _pm,
   "🔴 the page shows the props model as its own MODEL section with picks, hit rate and break-even",
   "⛔ Sam: 'their own section, labelled MODEL ... picks, hit rate and break-even'")
_shown, _more = M.cap_picks(list(range(40)))
ck(len(_shown) == card_fb.BOARD_MAX and _more == list(range(card_fb.BOARD_MAX, 40)),
   "🔴 the BUILDER caps the page at the card's BOARD_MAX, and keeps the rest in the file",
   "⛔ rule 66: the cap is the builder's, never the page's; rule 7: nothing is hidden. got %d + %d"
   % (len(_shown), len(_more)))

