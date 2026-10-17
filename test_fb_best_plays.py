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
     one per player (or game), chosen by edge and `[Sam, 2026-10-17]` SHOWN BY
     CONFIDENCE, highest first ("we need to sort our gizmos picks by confidence
     score, the highest at the top and working down"; ~~by edge~~); graded on
     what it shows; the page ~~starts
     on them, says so when there are none, and shows today's full list when off~~
     `[Sam, 2026-10-17]` ("no above their price only button in gizmos pikcs not
     needed") always shows them when the card has them, says so when there are
     none, and shows a card from before the liked lists as it is

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
#   find:                  and r.get("edge") is not None and r["edge"] > 0
#   with:                  and r.get("edge") is not None
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
# @vacuity 🔴 each player's line is CHOSEN by edge, then chance (his best-value liked line)
#   file: card_fb.py
#   find:                 key=lambda r: (-r["edge"], -r["confidence"]))
#   with:                 key=lambda r: (-r["confidence"], -r["edge"]))
#
# @vacuity 🔴 [Sam, 2026-10-17] the list is SHOWN by confidence, highest first (~~by edge~~)
#   file: card_fb.py
#   find:     out.sort(key=lambda r: (-r["confidence"], -r["edge"]))
#   with:     pass
#
# @vacuity 🔴 [Sam, 2026-10-17] ...and stays in confidence order through the freeze (~~edge order~~)
#   file: card_fb.py
#   find:             kept.sort(key=lambda r: (-(r.get("confidence") or 0), -(r.get("edge") or 0)))
#   with:             pass
#
# @vacuity 🔴 the freeze trims the lowest-EDGE fresh rows past the cap, never the lowest-confidence
#   file: card_fb.py
#   find:             merged.sort(key=lambda r: (-(r.get("edge") or 0), -(r.get("confidence") or 0)))
#   with:             pass
#
# @vacuity 🔴 a liked prop is priced under +150
#   file: card_fb.py
#   find:     if (r.get("price") or 0) >= LIKED_PROP_MAX_PRICE or not role_ok(r):
#   with:     if (r.get("price") or 0) > LIKED_PROP_MAX_PRICE or not role_ok(r):
#
# @vacuity 🔴 a liked prop's side agrees with its printed projection
#   file: card_fb.py
#   find:     return v > r["line"] if r["side"] == "over" else v < r["line"]
#   with:     return True
#
# @vacuity 🔴 a projection equal to the line is no lean
#   file: card_fb.py
#   find:     return v > r["line"] if r["side"] == "over" else v < r["line"]
#   with:     return v > r["line"] if r["side"] == "over" else v <= r["line"]
#
# @vacuity 🔴 a row with no projection keeps today's rule
#   file: card_fb.py
#   find:     if v is None or r.get("line") is None or r.get("side") not in ("over", "under"):
#   with:     if r.get("line") is None or r.get("side") not in ("over", "under"):
#
# @vacuity 🔴 the card's liked props are checked against its own projections
#   file: card_fb.py
#   find:             best_liked(rows, lambda r: (r.get("game_id"), r.get("player")), proj=projections),
#   with:             best_liked(rows, lambda r: (r.get("game_id"), r.get("player"))),
#
# @vacuity 🔴 a low-role player's over is never liked (snap share)
#   file: card_fb.py
#   find:     if role["snap"] < ROLE_MIN_SNAP:
#   with:     if False:
#
# @vacuity 🔴 a receiving over needs a real target share
#   file: card_fb.py
#   find:     if r.get("market") in RECEIVING and role["tgt_share"] < ROLE_MIN_TGT_SHARE:
#   with:     if False:
#
# @vacuity 🔴 the role check never blocks an under
#   file: card_fb.py
#   find:     if not role or r.get("side") not in ("over", "yes"):
#   with:     if not role:
#
# @vacuity 🔴 the card stores each NFL row's role
#   file: card_fb.py
#   find:                     row["role"] = current_role(who, pids, plog, season)
#   with:                     row["role"] = None
#
# `[2026-10-16]` "the role is this season's, not the rated season's" is declared in
#    test_fb_role_season.py, which builds this season's log (current_role).
#
# @vacuity 🔴 the record grades what the card shows
#   file: record_fb.py
#   find:     for p in card["liked"] if "liked" in card else card.get("picks", []):
#   with:     for p in card.get("picks", []):
#
# `[Sam, 2026-10-17]` ~~"the page shows the liked list while the button is on"~~: there is no
#    button; the next one turns the liked list off (the old switch, stuck off).
# @vacuity 🔴 the page always shows the liked list when the card has one
#   file: index.html
#   find:   return (C && C.liked) ? Object.assign({}, C, {
#   with:   return (C && false && C.liked) ? Object.assign({}, C, {
#
# @vacuity 🔴 no liked play: the board says so (~~while the button is on~~ always)
#   file: index.html
#   find:   return all ? `<div class="msg">The model has no ${k === 'picks' ? 'plays' : 'game lines'
#   with:   return false ? `<div class="msg">The model has no ${k === 'picks' ? 'plays' : 'game lines'
#
# `[Sam, 2026-10-17]` ~~"the button starts ON, still remembered per browser"~~: nothing is
#    remembered; the next one re-adds the button's click branch and its stored setting.
# @vacuity 🔴 [Sam, 2026-10-17] the page remembers no "above their price" setting
#   file: index.html
#   find:     FBPICKKIND = b.dataset.fbkind;
#   with:     if (b.hasAttribute('data-fbabove')) { try { localStorage.setItem('gp_fb_above', '1'); } catch(e){} } else FBPICKKIND = b.dataset.fbkind;
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
section("3. 🔴 THE BEST PLAYS THE MODEL LIKES, ONE PER PLAYER, SHOWN BY CONFIDENCE")
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
# `[Sam, 2026-10-17]` "we need to sort our gizmos picks by confidence score, the highest at the top
#    and working down": ~~[("J.K. Dobbins", 54.5, 1), ("Tie A", 30.5, 2), ("Tory Horton", 2.5, 3),
#    ("Lil'Jordan Humphrey", 1.5, 4)], by edge then chance~~. The same four rows (each player's line
#    still chosen by edge: Dobbins' 54.5 at +4.0, not his 49.5 at 58%), now shown 66, 61, 55, 52.
eq([(r["player"], r["line"], r["confidence"], r["rank"]) for r in L],
   [("Tie A", 30.5, 66, 1), ("Tory Horton", 2.5, 61, 2), ("J.K. Dobbins", 54.5, 55, 3),
    ("Lil'Jordan Humphrey", 1.5, 52, 4)],
   "🔴 [Sam, 2026-10-17] one row per player (his best-value liked line), SHOWN by confidence, highest "
   "first; nothing at edge <= 0 or under 50%")
_tie = CF.best_liked([prop("Lo Edge", "rec", "over", 2.5, 60, 1.0), prop("Hi Edge", "rec", "over", 3.5, 60, 5.0)],
                     lambda r: r["player"])
eq([r["player"] for r in _tie], ["Hi Edge", "Lo Edge"], "   ...a tie in confidence is broken by edge")
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
   "🔴 ...and it stays in confidence order through the freeze (~~edge order~~; a published card with no "
   "liked list yet)")
# `[2026-10-17]` the freeze still TRIMS by edge (the cap keeps the best-value fresh rows), then shows the
#    kept ones by confidence: one row too many, the lowest edge and the highest confidence, is the one cut.
_ft = tempfile.mkdtemp(prefix="bpfreeze2-")
try:
    _many = [dict(prop("P%02d" % i, "rec", "over", 2.5, 55, 5.0 + i), commence="2026-10-18T17:00:00Z")
             for i in range(CF.BOARD_MAX)]
    _many.append(dict(prop("High Chance Low Edge", "rec", "over", 2.5, 80, 0.5), commence="2026-10-18T17:00:00Z"))
    _old2 = os.path.join(_ft, "old.json")
    json.dump({"picks": [], "game_lines": []}, open(_old2, "w"))
    _doc2, _n2 = CF.freeze_published({"liked": sorted(_many, key=lambda r: -r["confidence"]), "picks": []}, _old2,
                                     "2026-10-15T12:00:00Z", log=lambda m: None)
finally:
    shutil.rmtree(_ft, ignore_errors=True)
_names2 = [r["player"] for r in _doc2["liked"]]
ck(len(_names2) == CF.BOARD_MAX and "High Chance Low Edge" not in _names2,
   "🔴 the freeze trims the lowest-EDGE fresh row past the cap, never the lowest-confidence one", str(_names2[:3]))
card = {"liked": [ROWS[1]], "picks": ROWS}
eq(len(RF.grade_card(card, {}, {}, None)), 1, "🔴 a card with a liked list is graded on what it shows")

# `[Sam, 2026-10-15]` PROPS: under +150, and never against the row's own PROJ.
P2 = [dict(prop("At 150", "rush", "over", 0.5, 56, 9.0), price=150),
      dict(prop("At 149", "rush", "over", 0.5, 56, 9.0), price=149),
      dict(prop("Proj Above", "rec", "under", 1.5, 52, 6.0), price=107),
      dict(prop("Proj Equal", "rec", "under", 2.5, 52, 6.0), price=-110),
      dict(prop("Proj Below Over", "yds", "over", 2.5, 52, 6.0), price=-110),
      dict(prop("No Proj", "rec", "under", 3.5, 52, 6.0), price=-110),
      dict(prop("Agrees", "rec", "over", 3.5, 52, 5.0), price=-120),
      dict(prop("Anytime", "td", "yes", None, 52, 5.0), price=120)]
PROJ = {"Proj Above|rec|under|1.5": {"v": 4.1}, "Proj Equal|rec|under|2.5": {"v": 2.5},
        "Proj Below Over|yds|over|2.5": {"v": 2.2}, "Agrees|rec|over|3.5": {"v": 4.4},
        "Anytime|td|yes|None": {"v": 0.4}}
eq(sorted(r["player"] for r in CF.best_liked(P2, lambda r: r["player"], proj=PROJ)),
   ["Agrees", "Anytime", "At 149", "No Proj"],
   "🔴 props: +150 is not liked and +149 is; an under with PROJ above (or equal to) its line and an over "
   "with PROJ below it are not; no projection, or no line, keeps today's rule")
eq(sorted(r["player"] for r in CF.best_liked(P2, lambda r: r["player"])), sorted(r["player"] for r in P2),
   "   ...and without `proj` (game lines) nothing extra is dropped")
# `[Sam, 2026-10-15]` "we can't be betting on guys like tory horton ... he's a wr4".
R3 = [dict(prop("WR4", "player_reception_yds", "over", 3.5, 56, 3.4), price=-111,
           role={"snap": 0.195, "tgt_share": 0.058, "car": 0.0}),
      dict(prop("Low Target RB", "player_receptions", "over", 1.5, 55, 1.5), price=-115,
           role={"snap": 0.44, "tgt_share": 0.069, "car": 15.3}),
      dict(prop("Lead RB", "player_rush_yds", "under", 66.5, 54, 0.9), price=-113,
           role={"snap": 0.52, "tgt_share": 0.09, "car": 16.7}),
      dict(prop("QB Under", "player_rush_yds", "under", 13.5, 55, 2.0), price=-115,
           role={"snap": 0.99, "tgt_share": 0.0, "car": 3.3}),
      dict(prop("WR1", "player_reception_yds", "over", 92.5, 55, 2.0), price=-113,
           role={"snap": 0.86, "tgt_share": 0.30, "car": 0.3}),
      dict(prop("College", "player_reception_yds", "over", 22.5, 55, 5.0), price=-118),
      dict(prop("Part-time RB", "player_rush_yds", "over", 20.5, 55, 2.0), price=-110,
           role={"snap": 0.30, "tgt_share": 0.05, "car": 10.0})]
eq(sorted(r["player"] for r in CF.best_liked(R3, lambda r: r["player"], proj={})),
   ["College", "Lead RB", "QB Under", "WR1"],
   "🔴 role: a WR4's over (19% of snaps), a part-time RB's rushing over (30% of snaps, 10 carries) and an "
   "RB's receptions over (7% of targets) are never liked; an "
   "under is never blocked by a small role; a row with no role (college) keeps today's rule")
src = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
ck('row["role"] = current_role(who, pids, plog, season)' in src and CF.role_of({"g": [{"d": "2026-10-0%d" % i, "snap_pct": 0.5, "tgt_share": 0.2,
                                                                 "car": 3} for i in range(1, 6)]})
   == {"snap": 0.5, "tgt_share": 0.2, "car": 3.0, "n": 3},
   "🔴 the card stores each NFL row's role: means over his last 3 games")
ck('best_liked(rows, lambda r: (r.get("game_id"), r.get("player")), proj=projections),'
   in open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read(),
   "🔴 the card's liked props are checked against the card's own projections map")
eq(len(RF.grade_card({"picks": ROWS[:3]}, {}, {}, None)), 3, "   ...and a card from before the switch as it was")

# `[Sam, 2026-10-17]` "no above their price only button in gizmos pikcs not needed": ~~run
#    with FBABOVE on and off~~ -- fbView and fbNoLiked now take no switch (none is passed: one
#    named in their code would throw here), and have ONE behaviour: the card's liked lists
#    whenever it has them; a card from before the liked lists exactly as it is.
PG = r"""
const S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const [fbView, fbNoLiked] = new Function('fbDayName', S.v + '\n' + S.n + '\nreturn [fbView, fbNoLiked];')(d => d);
const C = {date: '2026-10-18', liked: [], game_lines_liked: [], picks: [{player: 'A'}, {player: 'B'}],
           game_lines: [{game: 'x'}], game_lines_meta: {slate: '2026-10-18'}};
const OLD = {date: '2026-10-18', picks: [{player: 'A'}, {player: 'B'}], game_lines: [{game: 'x'}],
             game_lines_meta: {slate: '2026-10-18'}};
const none = fbView(C), old = fbView(OLD),
      full = fbView(Object.assign({}, C, {liked: [{player: 'B'}], game_lines_liked: [{game: 'y'}]}));
process.stdout.write(JSON.stringify([none.picks.length, fbNoLiked(none, 'picks'), fbNoLiked(none, 'game_lines'),
  old.picks.length, fbNoLiked(old, 'picks'), full.picks.map(p => p.player),
  old === OLD, (full.game_lines || []).map(g => g.game), (full.picks_all || []).length,
  (full.game_lines_all || []).length]));
"""
tmp = tempfile.mkdtemp(prefix="bestplays-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(PG)
    json.dump({"v": js_block("fbView", PAGE), "n": js_block("fbNoLiked", PAGE)},
              open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=300)
    OUT = json.loads(r.stdout) if r.returncode == 0 else [None] * 10
finally:
    shutil.rmtree(tmp, ignore_errors=True)
ck(r.returncode == 0, "⚠️ the page's own code ran in node", (r.stderr or "")[-300:])
ck(OUT[0] == 0 and "has no plays it likes for 2026-10-18" in (OUT[1] or "")
   and "has no game lines it likes" in (OUT[2] or ""),
   "🔴 ~~button on,~~ nothing liked: one plain line says the model has no plays it likes for that slate", OUT[:3])
eq((OUT[3], OUT[4], OUT[5]), (2, "", ["B"]),
   "🔴 ~~button off: today's full list returns (no line); on: the card's liked list~~ a card from before "
   "the liked lists shows its full list (no line); a card with one, the card's liked list")
eq((OUT[6], OUT[7], OUT[8], OUT[9]), (True, ["y"], 2, 1),
   "   ...the old card untouched; the liked game lines replace the full list, which is kept beside them")
_code = re.sub(r"/\*.*?\*/|<!--.*?-->", "", open(PAGE, encoding="utf-8").read(), flags=re.S)
_left = [k for k in ("FBABOVE", "gp_fb_above", "fbAbovePass", "data-fbabove") if k in _code]
ck(not _left,
   "   ~~the button starts ON (Sam, 2026-10-15), still remembered per browser~~ `[Sam, 2026-10-17]` no "
   "button: the page's code keeps no switch (FBABOVE) and remembers no setting (gp_fb_above)", _left)
