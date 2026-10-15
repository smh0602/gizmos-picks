#!/usr/bin/env python3
"""test_fb_best_plays.py — football Gizmo's Picks makes sense. `[Sam, 2026-10-15]`
"the player props and the game lines on gizmo picks genuinly makes no sense" ...
"i just want you to have the best plays our model likes simple as that".

Planted rows, planted models, a pinned clock, the shipped page code in node.
  1. off-main spreads and totals sit on ONE normal curve through the main line's
     fit: the chance falls as the line gets harder, equals p0 at the main line,
     and a Denver -23.5 at +2000 rung is under 5% and gets no row
  2. the predicted total sits on the over/under's side of its line
  3. the board lists the plays the model likes: chance 50%+, above its price,
     one per player (or game), by edge; graded on what it shows; the page starts
     on them, says so when there are none, and shows today's full list when off

# @vacuity 🔴 every off-main rung is priced on the curve, never the fit at that line
#   file: game_lines_fb.py
#   find:         ph = ND.cdf((mu - (-pt if side == "home" else pt)) / s)
#   with:         ph = ND.cdf((mu - (-pt if side == "home" else pt)) / (50 * s))
#
# @vacuity 🔴 the curve passes through the main line's own chance
#   file: game_lines_fb.py
#   find:     return main + s * ND.inv_cdf(min(1 - 1e-9, max(1e-9, p0)))
#   with:     return main + s * ND.inv_cdf(min(1 - 1e-9, max(1e-9, p0))) + 1.0
#
# @vacuity 🔴 a total rung is priced on its own curve
#   file: game_lines_fb.py
#   find:     po = ND.cdf((mu - pt) / s)
#   with:     po = ND.cdf((pt - mu) / s)
#
# @vacuity 🔴 the predicted total comes from the total fit at the line
#   file: fb_model.py
#   find:     ot = (T + sigma_t * statistics.NormalDist().inv_cdf(min(1 - 1e-9, max(1e-9, p_over)))
#   with:     ot = (T - sigma_t * statistics.NormalDist().inv_cdf(min(1 - 1e-9, max(1e-9, p_over)))
#
# @vacuity 🔴 a liked play is above its price
#   file: card_fb.py
#   find:                  and r.get("edge") is not None and r["edge"] > 0),
#   with:                  and r.get("edge") is not None),
#
# @vacuity 🔴 a liked play is 50% or more
#   file: card_fb.py
#   find:     ok = sorted((r for r in rows if r.get("confidence") is not None and r["confidence"] >= LIKED_MIN_CONF
#   with:     ok = sorted((r for r in rows if r.get("confidence") is not None
#
# @vacuity 🔴 one row per player
#   file: card_fb.py
#   find:         if who(r) not in seen:
#   with:         if True:
#
# @vacuity 🔴 ordered by edge, then chance
#   file: card_fb.py
#   find:                 key=lambda r: (-r["edge"], -r["confidence"]))
#   with:                 key=lambda r: (-r["confidence"], -r["edge"]))
#
# @vacuity 🔴 the published liked list stays in edge order through the freeze
#   file: card_fb.py
#   find:             merged.sort(key=lambda r: (-(r.get("edge") or 0), -(r.get("confidence") or 0)))
#   with:             pass
#
# @vacuity 🔴 the record grades what the card shows
#   file: record_fb.py
#   find:     for p in card["liked"] if "liked" in card else card.get("picks", []):
#   with:     for p in card.get("picks", []):
#
# @vacuity 🔴 the page shows the liked list while the button is on
#   file: index.html
#   find:   return (C && FBABOVE && C.liked) ? Object.assign({}, C, {
#   with:   return (C && false && C.liked) ? Object.assign({}, C, {
#
# @vacuity 🔴 no liked play: the board says so
#   file: index.html
#   find:   return FBABOVE && all ? `<div class="msg">The model has no ${k === 'picks' ? 'plays' : 'game lines'
#   with:   return FBABOVE && false ? `<div class="msg">The model has no ${k === 'picks' ? 'plays' : 'game lines'
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from statistics import NormalDist

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "nfl")
import card_fb as CF  # noqa: E402
import fb_model as FM  # noqa: E402
import game_lines_fb as G  # noqa: E402
import record_fb as RF  # noqa: E402
from jsblock import js_block  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

PAGE = os.path.join(ROOT, "index.html")
SIG = {"spread": 13.4, "total": 13.0}
ROW = {"id": "S1", "lg": "nfl", "season": 2026, "day": "2026-10-18", "home": "DEN", "away": "SEA",
       "M": -2.5, "T": 43.5, "pml": 0.45,
       "sig": {"h2h_m": None, "h2h_t": None, "form_m": None, "form_t": None, "def": None, "poss": None,
               "out": None, "vac_h": None, "vac_a": None, "neutral": 0.0, "dome": 0.0,
               "own_m": 1.0, "own_t": 41.0}}


def const_model(market, p):
    k = len(FM.features(ROW, market))
    return {"mu": [0.0] * k, "sd": [1.0] * k, "w": [math.log(p / (1 - p))] + [0.0] * k}


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 ONE CURVE THROUGH THE MAIN PICK")
# ══════════════════════════════════════════════════════════════════════
MODELS = {"spread": const_model("spread", 0.60), "total": const_model("total", 0.40)}
M0, T0 = -2.5, 43.5                    # Denver +2.5 at home; total 43.5
eq(round(G.model_p(MODELS, ROW, "spread", "home", -M0, M0, SIG), 9), 0.6,
   "🔴 at the main line the chance is the fit's own p0 (0.60, Denver +2.5)")
home = [G.model_p(MODELS, ROW, "spread", "home", pt, M0, SIG) for pt in (10.5, 2.5, -3.5, -10.5, -23.5)]
away = [G.model_p(MODELS, ROW, "spread", "away", pt, M0, SIG) for pt in (23.5, 10.5, 3.5, -2.5, -10.5)]
over = [G.model_p(MODELS, ROW, "total", "over", t, T0, SIG) for t in (30.5, 40.5, 43.5, 47.5, 60.5)]
under = [G.model_p(MODELS, ROW, "total", "under", t, T0, SIG) for t in (60.5, 47.5, 43.5, 40.5, 30.5)]
ck(all(all(a > b for a, b in zip(v, v[1:])) for v in (home, away, over, under)),
   "🔴 every spread and total rung's chance falls as its line gets harder, both sides", (home, away, over, under))
eq(round(over[2], 9), 0.4, "   ...and the total's curve passes through its own p0 (0.40 over 43.5)")
den = G.model_p(MODELS, ROW, "spread", "home", -23.5, M0, SIG)
ck(den < 0.05, "🔴 Denver -23.5 is under 5% (it read 54% on 10-15 beside 44% to win)", den)
lad = {("home", -23.5): {"DraftKings": 2000}, ("home", -6.5): {"FanDuel": 150}}
rungs = G.rungs_for(lad, "spread", M0, MODELS, ROW, None, SIG)
ladder = {"games": [{"away": "SEA", "home": "DEN", "commence": "2026-10-19T00:20:00Z", "main_spread_home": 2.5,
                     "spread": rungs, "sched_id": "S1"}]}
pick = {"market": "spread", "side": "home", "line": 2.5, "away": "SEA", "home": "DEN", "player": "Denver Broncos",
        "commence": "2026-10-19T00:20:00Z", "game": "SEA @ DEN", "confidence": 60}
alts = CF.alt_spread_rows([pick], ladder)
ck(not any(a["line"] == -23.5 for a in alts), "🔴 ...so the +2000 rung gets no alternate-spread row",
   [(a["line"], a["confidence"]) for a in alts])
eq(G.fair_line(MODELS, ROW, "spread", M0, SIG)[0], round(M0 + 13.4 * NormalDist().inv_cdf(0.6), 1),
   "🔴 the fair line is the curve's centre, mu = M0 + sigma x NormalInverse(p0)")
eq(G.model_p(MODELS, ROW, "spread", "home", -6.5, M0, {}), None,
   "   a file with no sigma prices nothing (never the fit at an off-main line)")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE PREDICTED TOTAL SITS ON THE OVER/UNDER'S SIDE")
# ══════════════════════════════════════════════════════════════════════
bad = []
for T, p_over in ((40.5, 0.35), (40.5, 0.62), (47.5, 0.44), (47.5, 0.51), (55.0, 0.70)):
    s = FM.predicted_score(dict(ROW, T=T), 0.45, 13.4, p_over, 13.0)
    tot = s["home"] + s["away"]
    if (tot > T) != (p_over > 0.5):
        bad.append((T, p_over, tot))
ck(not bad, "🔴 in every planted row the predicted total is on the side the total fit picks at the line", bad)
eq(FM.predicted_score(dict(ROW, T=None), 0.45, 13.4, None, 13.0)["home"]
   + FM.predicted_score(dict(ROW, T=None), 0.45, 13.4, None, 13.0)["away"], 41.0,
   "   no total line: the own total, as before")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE BEST PLAYS THE MODEL LIKES, ONE PER PLAYER, BY EDGE")
# ══════════════════════════════════════════════════════════════════════
def prop(player, mk, side, line, conf, edge, game="g1"):
    return {"player": player, "market": mk, "side": side, "line": line, "confidence": conf, "edge": edge,
            "game_id": game, "game": game, "kind": "fb-prop"}


ROWS = [prop("J.K. Dobbins", "rush", "over", 49.5, 58, 3.1), prop("J.K. Dobbins", "rush", "over", 54.5, 55, 4.0),
        prop("J.K. Dobbins", "rush", "under", 64.5, 52, 1.0), prop("Tory Horton", "rec", "over", 2.5, 61, 2.2),
        prop("Lil'Jordan Humphrey", "rec", "over", 0.5, 54, -15.7), prop("Lil'Jordan Humphrey", "rec", "under", 1.5, 52, 0.5),
        prop("Low Chance", "rec", "under", 3.5, 48, 9.0), prop("Tie A", "yds", "over", 30.5, 66, 2.2, "g2"),
        prop("No Edge", "yds", "over", 30.5, 70, 0.0, "g2")]
L = CF.best_liked(ROWS, lambda r: (r["game_id"], r["player"]))
eq([(r["player"], r["line"], r["rank"]) for r in L],
   [("J.K. Dobbins", 54.5, 1), ("Tie A", 30.5, 2), ("Tory Horton", 2.5, 3), ("Lil'Jordan Humphrey", 1.5, 4)],
   "🔴 one row per player (his best liked line), by edge then chance; nothing at edge <= 0 or under 50%")
ck(all(r["edge"] > 0 and r["confidence"] >= 50 for r in L) and len({r["player"] for r in L}) == len(L),
   "   ...no player twice, no row at or below its price, none under 50%")
eq(len(CF.best_liked([dict(r, player="P%d" % i) for i, r in enumerate(ROWS * 6)], lambda r: r["player"], 25)), 25,
   "   at most 25")
GL = [{"game": "SEA @ DEN", "market": "spread", "confidence": 60, "edge": 2.0, "kind": "fb-line"},
      {"game": "SEA @ DEN", "market": "total", "confidence": 55, "edge": 4.0, "kind": "fb-line"},
      {"game": "PIT @ TB", "market": "moneyline", "confidence": 59, "edge": -1.0, "kind": "fb-line"}]
eq([(r["game"], r["market"]) for r in CF.best_liked(GL, lambda r: r["game"])], [("SEA @ DEN", "total")],
   "🔴 game lines: one per game, its best liked line")
eq(CF.freeze_cap("liked"), CF.BOARD_MAX, "🔴 the liked list is frozen at kickoff like the board it replaces")
# `[2026-10-15]` caught on the rebuilt NFL card: the freeze re-sorted it by confidence.
_ft = tempfile.mkdtemp(prefix="bpfreeze-")
try:
    _fut = [dict(r, commence="2026-10-18T17:00:00Z") for r in L]
    _old = os.path.join(_ft, "old.json")
    json.dump({"picks": [], "game_lines": []}, open(_old, "w"))
    _doc, _n = CF.freeze_published({"liked": [dict(r) for r in _fut], "picks": []}, _old,
                                   "2026-10-15T12:00:00Z", log=lambda m: None)
finally:
    shutil.rmtree(_ft, ignore_errors=True)
eq([(r["player"], r["rank"]) for r in _doc["liked"]], [(r["player"], r["rank"]) for r in L],
   "🔴 ...and it stays in edge order through the freeze (a published card with no liked list yet)")
card = {"liked": [ROWS[1]], "picks": ROWS}
eq(len(RF.grade_card(card, {}, {}, None)), 1, "🔴 a card with a liked list is graded on what it shows")
eq(len(RF.grade_card({"picks": ROWS[:3]}, {}, {}, None)), 3, "   ...and a card from before the switch as it was")

PG = r"""
const S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const run = on => new Function('fbDayName', 'FBABOVE', S.v + '\n' + S.n + '\nreturn [fbView, fbNoLiked];')(d => d, on);
const [vOn, nOn] = run(true), [vOff, nOff] = run(false);
const C = {date: '2026-10-18', liked: [], game_lines_liked: [], picks: [{player: 'A'}, {player: 'B'}],
           game_lines: [{game: 'x'}], game_lines_meta: {slate: '2026-10-18'}};
const on = vOn(C), off = vOff(C), full = vOn(Object.assign({}, C, {liked: [{player: 'B'}]}));
process.stdout.write(JSON.stringify([on.picks.length, nOn(on, 'picks'), nOn(on, 'game_lines'),
  off.picks.length, nOff(off, 'picks'), full.picks.map(p => p.player)]));
"""
tmp = tempfile.mkdtemp(prefix="bestplays-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(PG)
    json.dump({"v": js_block("fbView", PAGE), "n": js_block("fbNoLiked", PAGE)},
              open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=300)
    OUT = json.loads(r.stdout) if r.returncode == 0 else [None] * 6
finally:
    shutil.rmtree(tmp, ignore_errors=True)
ck(r.returncode == 0, "⚠️ the page's own code ran in node", (r.stderr or "")[-300:])
ck(OUT[0] == 0 and "has no plays it likes for 2026-10-18" in (OUT[1] or "")
   and "has no game lines it likes" in (OUT[2] or ""),
   "🔴 button on, nothing liked: one plain line says the model has no plays it likes for that slate", OUT[:3])
eq((OUT[3], OUT[4], OUT[5]), (2, "", ["B"]),
   "🔴 button off: today's full list returns (no line); on: the card's liked list")
ck(re.search(r"localStorage\.getItem\('gp_fb_above'\) !== '0'", open(PAGE, encoding="utf-8").read()) is not None,
   "   the button starts ON (Sam, 2026-10-15), still remembered per browser")
