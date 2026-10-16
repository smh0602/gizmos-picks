#!/usr/bin/env python3
"""THE SCORE-FIRST FOOTBALL GAME MODEL AND ITS TEAM-UNIT TABLES. `[Sam, 2026-10-15]`

"your trying to predict the score of both team ... how teams play against certain
stats like passing rushing receiving". `fb_matchups.py` (the shared tables) and
`fb_score_model.py` (report only). Planted leagues and a pinned clock only;
nothing here reads the live data tree.
  1. Point in time: a table as of a day reads only games before its Monday, and a
     prediction's weights, sigmas and k's read only earlier weeks.
  2. Opponent adjustment: yards against soft defences count for less.
  3. The home edge is MEASURED from past games, and a neutral site gets none.
  4. The matchup layer (pass, rush, pace) moves the predicted total.
  5. Every chance comes from the predicted score's normal curve.
  6. No card change: only collect.py's card-fb run (after the card) names the
     model, and a build writes its one file and nothing else.
  7. The code runs the settings research/fb_score_model_design.md fixed.

# @vacuity 🔴 a table reads only games before its Monday
#   file: fb_matchups.py
#   find: done[wk] = F.solve_ratings([g for g in self.G[unit] if g[0] < wk], wk,
#   with: done[wk] = F.solve_ratings([g for g in self.G[unit] if g[0] <= wk], wk,
#
# @vacuity 🔴 ...the Monday of the day asked, not the day itself
#   file: fb_matchups.py
#   find: wk = F.monday(as_of[:10])
#   with: wk = as_of[:10]
#
# @vacuity 🔴 a prediction's weights, sigmas and k's read only earlier WEEKS
#   file: fb_score_model.py
#   find: weeks[F.monday(r["day"])].append(r)
#   with: weeks[r["day"]].append(r)
#
# @vacuity 🔴 a team's number is adjusted for the defences it faced
#   file: fb_matchups.py
#   find: return s["base"] + s["O"][team] if team in s["teams"] else None
#   with: return (lambda v: sum(v) / len(v) if v else None)([g[4] if g[1] == team else g[5] for g in self.G[unit] if team in g[1:3]])
#
# @vacuity 🔴 a matchup gap reads the defence too
#   file: fb_matchups.py
#   find: return s["O"][offence] - s["D"][defence]
#   with: return s["O"][offence]
#
# @vacuity 🔴 the home edge is the measured one, not a fixed 1.5
#   file: fb_score_model.py
#   find: return (s["base"] + s["hpe"] * at_home + s["O"][h] - s["D"][a],
#   with: return (s["base"] + 1.5 * at_home + s["O"][h] - s["D"][a],
#
# @vacuity 🔴 a neutral site gets no home edge
#   file: fb_score_model.py
#   find: at_home = 0.0 if r["sig"]["neutral"] else 1.0
#   with: at_home = 1.0
#
# @vacuity 🔴 the matchup layer moves each side's points
#   file: fb_score_model.py
#   find: home = b[0] + sum(c * x for c, x in zip(beta, f[0]))
#   with: home = b[0]
#
# @vacuity 🔴 ...with weights fitted on earlier games
#   file: fb_score_model.py
#   find: A = [[sum(x[i] * x[j] for x, _ in sides) / (sd[i] * sd[j]) + (MATCH_RIDGE if i == j else 0.0)
#   with: A = [[sum(x[i] * x[j] for x, _ in sides) / (sd[i] * sd[j]) + (1e12 if i == j else 0.0)
#
# @vacuity 🔴 ...and both teams' pace is one of its inputs
#   file: fb_score_model.py
#   find: pace = tables.gap(h, a, "plays", d) + tables.gap(a, h, "plays", d)
#   with: pace = 0.0
#
# @vacuity 🔴 the chance is the normal curve of the predicted score
#   file: fb_score_model.py
#   find: return ((p["total"] if mk == "total" else p["margin"]) - ln) / sig
#   with: return (p["margin"] - ln) / sig
#
# @vacuity 🔴 the moneyline is the margin against 0
#   file: fb_score_model.py
#   find: return {"spread": r.get("M"), "total": r.get("T"), "moneyline": 0.0}[mk]
#   with: return {"spread": r.get("M"), "total": r.get("T"), "moneyline": 3.0}[mk]
#
# @vacuity 🔴 the calibrated version widens the curve by k
#   file: fb_score_model.py
#   find: return None if z is None else PHI.cdf(z / (p["k"][mk] if cal else 1.0))
#   with: return None if z is None else PHI.cdf(z)
#
# @vacuity 🔴 no card, pick or page module reads the score model
#   file: card_fb.py
#   find: import unicodedata
#   with: import unicodedata  # fb_score_model
#
# @vacuity 🔴 a build writes its own file and nothing else
#   file: fb_score_model.py
#   find: path = out or os.path.join(root or ROOT, "data", lg, "latest", "fb-score-model.json")
#   with: path = out or os.path.join(root or ROOT, "data", lg, "latest", "fb-model.json")
#
# @vacuity 🔴 the code runs the design's settings
#   file: fb_score_model.py
#   find: MATCH_RIDGE = 100.0
#   with: MATCH_RIDGE = 50.0
"""
import ast
import atexit
import datetime
import glob
import gzip
import hashlib
import json
import math
import os
import random
import re
import shutil
import statistics
import sys
import tempfile

from tcheck import ck, eq, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
import fb_matchups as FM  # noqa: E402
import fb_model as F  # noqa: E402
import fb_score_model as S  # noqa: E402

NOW = "2026-11-19T12:00:00Z"            # ⛔ pinned: the planted league's clock
TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])
TEAMS = ["T%d" % i for i in range(10)]


def jgz(path, doc):
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(doc, fh)


def plant(home_edge=5.0, seed=11):
    """A ten-team league: 2025 weeks 1-30 and 2026 weeks 1-12 (11 and 12 unplayed),
    five games a week, plus a Thursday and a Monday game in 2026 week 8."""
    rnd = random.Random(seed)
    lat = {t: {k: rnd.gauss(0, sd) for k, sd in (("pts", 4), ("dpts", 4), ("pass", 30), ("dpass", 30),
                                                  ("rush", 20), ("drush", 20), ("pace", 4), ("dpace", 4))}
           for t in TEAMS}
    root = tempfile.mkdtemp(prefix="fbsm-")
    TREES.append(root)
    latest = os.path.join(root, "data", "nfl", "latest")
    os.makedirs(latest)
    rot, rounds = TEAMS[:], []
    for _ in range(9):
        rounds.append([(rot[i], rot[-1 - i]) for i in range(5)])
        rot = [rot[0], rot[-1]] + rot[1:-1]
    slots = [(2025, datetime.date(2025, 9, 7) + datetime.timedelta(weeks=i), i + 1) for i in range(30)] + \
            [(2026, datetime.date(2026, 9, 13) + datetime.timedelta(weeks=i), i + 1) for i in range(12)]
    games = []
    for n, (season, day, wk) in enumerate(slots):
        pairs = [(a, h) if n % 2 else (h, a) for h, a in rounds[n % 9]]
        if (season, wk) == (2026, 8):
            pairs += [("T0", "T5", -3), ("T1", "T6", 1)]       # Thursday, Monday
        for j, pr in enumerate(pairs):
            games.append((season, day + datetime.timedelta(days=pr[2] if len(pr) > 2 else 0), wk,
                          pr[0], pr[1], (n * 5 + j) % 7 == 0))
    sched, logs = {2025: [], 2026: []}, {2025: {}, 2026: {}}
    for i, (season, day, wk, h, a, neutral) in enumerate(games):
        final = day.isoformat() < NOW[:10]
        hf = 0.0 if neutral else 1.0
        u = {}
        for o, d in ((h, a), (a, h)):
            u[o] = {"pass": 230 + lat[o]["pass"] - lat[d]["dpass"] + rnd.gauss(0, 15),
                    "rush": 115 + lat[o]["rush"] - lat[d]["drush"] + rnd.gauss(0, 10),
                    "plays": 60 + lat[o]["pace"] - lat[d]["dpace"] + rnd.gauss(0, 3)}
            u[o]["pts"] = max(0, round(21 + (home_edge * hf if o == h else 0.0) + lat[o]["pts"] - lat[d]["dpts"]
                                       + 0.03 * (u[o]["pass"] - 230) + 0.03 * (u[o]["rush"] - 115)
                                       + 0.2 * (u[o]["plays"] - 60) + rnd.gauss(0, 6)))
        em = home_edge * hf + lat[h]["pts"] - lat[a]["dpts"] - lat[a]["pts"] + lat[h]["dpts"]
        M = (round(2 * em) / 2) or 1.0
        gid = "%d_%02d_%s_%s" % (season, wk, a, h)
        sched[season].append({
            "id": gid, "week": wk, "start": day.isoformat() + "T17:00", "home": h, "away": a,
            "neutral": neutral, "final": final, "home_score": u[h]["pts"] if final else None,
            "away_score": u[a]["pts"] if final else None, "closing_spread": str(M),
            "closing_total": str(round(2 * (42 + 0.0)) / 2), "closing_ml_home": -150 if M > 0 else 130,
            "closing_ml_away": 130 if M > 0 else -150, "closing_spread_odds_home": -110,
            "closing_spread_odds_away": -110, "closing_over_odds": -110, "closing_under_odds": -110})
        if not final:
            continue
        for t in (h, a):
            plays, pas, rush = u[t]["plays"], u[t]["pass"], u[t]["rush"]
            for pos, st in (("QB", {"att": 0.55 * plays, "pass_yds": pas, "car": 2, "rush_yds": 5}),
                            ("RB", {"car": 0.45 * plays - 2, "rush_yds": rush - 5, "rec_yds": 0.1 * pas, "tgt": 4}),
                            ("WR", {"rec_yds": 0.65 * pas, "tgt": 20}), ("TE", {"rec_yds": 0.25 * pas, "tgt": 7})):
                logs[season].setdefault(t + pos, {"name": t + pos, "pos": pos, "g": []})["g"].append(
                    dict(st, d=day.isoformat(), game_id=gid, team=t, o=a if t == h else h))
    for s in (2025, 2026):
        jgz(os.path.join(latest, "schedule-%d.json.gz" % s), {"games": sched[s]})
        jgz(os.path.join(latest, "players-%d.json.gz" % s), {"players": logs[s]})
    with open(os.path.join(latest, "fb-model.json"), "w", encoding="utf-8") as fh:
        json.dump({"planted": True}, fh)
    return root


class _Allowed:
    def __init__(self, lg):
        pass

    def fraction(self, g):
        return None


_OLD = (F.board_prices, F.t60r.history, F.t60r.Allowed)
F.board_prices = lambda lg, resolve, root=None: {}
F.t60r.history = lambda lg: []
F.t60r.Allowed = _Allowed
atexit.register(lambda: setattr(F, "board_prices", _OLD[0]))
LG = plant()
TB = FM.Tables("nfl", LG)
ROWS = [r for r in F.build_rows("nfl", root=LG) if r["final"] or r["day"] <= "2026-11-27"]
DONE = S.walk_forward(ROWS, TB)

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 POINT IN TIME")
# ══════════════════════════════════════════════════════════════════════
_G = TB.G["pass_yds"]
ck(any(g[0] == "2026-11-02" for g in _G) and any(g[0] == "2026-10-29" for g in _G),
   "the planted league has a Thursday (10-29) and a Monday (11-02) game")
_got = TB.solve("pass_yds", "2026-11-04")                        # a Wednesday
_cut = F.solve_ratings([g for g in _G if g[0] < "2026-11-02"], "2026-11-02", tol=FM.UNIT_TOL)
_with = F.solve_ratings([g for g in _G if g[0] <= "2026-11-02"], "2026-11-02", tol=FM.UNIT_TOL)
_d = lambda a, b: max(abs(a["O"][t] - b["O"][t]) + abs(a["D"][t] - b["D"][t]) for t in TEAMS)  # noqa: E731
ck(_d(_got, _cut) < 1e-3, "🔴 a table as of Wednesday 11-04 reads only games before Monday 11-02",
   "%.1e yards from a cold solve" % _d(_got, _cut))
ck(_d(_with, _cut) > 0.1, "...and Monday's own game would have moved it (the cut bites)")
_w5 = TB.solve("pass_yds", "2026-10-30")                         # the Friday after the Thursday game
_c5 = F.solve_ratings([g for g in _G if g[0] < "2026-10-26"], "2026-10-26", tol=FM.UNIT_TOL)
ck(_d(_w5, _c5) < 1e-3, "🔴 as of a Friday, the Thursday before it is NOT read: the cut is the Monday")
_sun = next(p for p in DONE if p["row"]["day"] == "2026-11-01")
_thu = next(r for r in ROWS if r["day"] == "2026-10-29")
_prev = next(r for r in ROWS if r["day"] == "2026-10-25")
_key = lambda p: (round(p["home"], 6), round(p["away"], 6), p["sigma"]["margin"], p["k"]["spread"])  # noqa: E731


def _redo(row, bump):
    old = row["hs"]
    row["hs"] = old + bump
    try:
        return _key(next(p for p in S.walk_forward(ROWS, TB) if p["row"] is _sun["row"]))
    finally:
        row["hs"] = old


eq(_redo(_thu, 30), _key(_sun), "🔴 Sunday's prediction ignores that week's Thursday result")
ck(_redo(_prev, 30) != _key(_sun), "...and an earlier week's result does move it")
ck(all(p["week"] == F.monday(p["row"]["day"]) for p in DONE), "every prediction is made as of its own Monday")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 OPPONENT ADJUSTMENT")
# ══════════════════════════════════════════════════════════════════════
_tb = FM.Tables.__new__(FM.Tables)
_tb.lg, _tb._solved = "nfl", {"pass_yds": {}}
_d0, _rows = datetime.date(2026, 9, 6), []
for i in range(8):     # Z (average offence) shows W is soft and S is hard; X plays W, Y plays S
    d = (_d0 + datetime.timedelta(weeks=i)).isoformat()
    _rows += [(d, "X", "W", 1.0, 300.0, 230.0), (d, "Y", "S", 1.0, 250.0, 230.0),
              (d, "Z", "W", 1.0, 330.0, 230.0), (d, "Z2", "S", 1.0, 170.0, 230.0)]
_tb.G = {"pass_yds": sorted(_rows)}
_raw = lambda t: statistics.mean(g[4] for g in _tb.G["pass_yds"] if g[1] == t)  # noqa: E731
_x, _y = _tb.unit_for("X", "pass_yds", "2026-12-01"), _tb.unit_for("Y", "pass_yds", "2026-12-01")
ck(_raw("X") > _raw("Y") and _y > _x,
   "🔴 X gained more raw yards (vs soft W) but Y rates higher (vs hard S)", "X %.1f, Y %.1f" % (_x, _y))
ck(_tb.unit_allowed("W", "pass_yds", "2026-12-01") > _tb.unit_allowed("S", "pass_yds", "2026-12-01"),
   "the soft defence allows more than the hard one")
ck(_tb.gap("X", "W", "pass_yds", "2026-12-01") > _tb.gap("X", "S", "pass_yds", "2026-12-01") + 50,
   "🔴 a matchup gap reads the defence too: X vs W is worth far more than X vs S")
ck(TB.table(NOW)["rec_yds_WR"]["T0"]["games"] > 0, "the tables carry receiving yards by position")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE HOME EDGE IS MEASURED, AND A NEUTRAL SITE GETS NONE")
# ══════════════════════════════════════════════════════════════════════
_he = TB.home_edge("points", NOW)
ck(3.5 < _he < 6.5, "🔴 the points table measures the planted +5 home edge", "measured %.2f" % _he)
_up = next(r for r in ROWS if not r["final"] and not r["sig"]["neutral"])
_bh = S.base_score(TB, _up)
_bn = S.base_score(TB, dict(_up, sig=dict(_up["sig"], neutral=1.0)))
ck(abs((_bh[0] - _bh[1]) - (_bn[0] - _bn[1]) - TB.home_edge("points", _up["day"])) < 1e-9,
   "🔴 a home game's margin carries exactly the measured edge (not Sam's fixed 1.5)",
   "home %.2f, neutral %.2f" % (_bh[0] - _bh[1], _bn[0] - _bn[1]))
ck(abs(_bh[1] - _bn[1]) < 1e-12 and abs(_bh[0] - _bn[0]) > 1.0, "a neutral site moves the home side's points, never the away side's")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE MATCHUP LAYER MOVES THE TOTAL")
# ══════════════════════════════════════════════════════════════════════
_rnd = random.Random(5)
_sides = [([_rnd.gauss(0, 30), _rnd.gauss(0, 20), _rnd.gauss(0, 6)], 0.0) for _ in range(1000)]
_sides = [(x, 0.05 * x[0] + 0.1 * x[1] + 0.5 * x[2]) for x, _ in _sides]
_b = S.fit_matchup(_sides)
ck(all(0.8 * t < b <= t for b, t in zip(_b, (0.05, 0.1, 0.5))),
   "🔴 the weights are fitted from earlier games (and shrunk a little, never grown)", str(_b))
eq(S.fit_matchup(_sides[:S.MIN_SIDES - 1]), [0.0, 0.0, 0.0], "under 200 earlier sides every weight is 0")
_late = [p for p in DONE if p["row"]["day"] >= "2026-10-01"]
ck(_late and all(any(b != 0.0 for b in p["beta"]) for p in _late), "late 2026 predictions carry fitted weights")
_exact = sum(abs(p["total"] - sum(b0) - sum(c * (x + y) for c, x, y in zip(p["beta"], f[0], f[1]))) < 1e-9
             for p in _late for b0, f in [(S.base_score(TB, p["row"]), S.matchup(TB, p["row"]))])
eq(_exact, len(_late), "🔴 every late total = base total + the matchup layer on both sides")


class _Flat:
    """A league whose points table sees no team apart: only the matchup layer can explain the scores."""
    def __init__(self, gaps):
        self.gaps = gaps

    def solve(self, unit, as_of):
        return {"teams": set(TEAMS), "base": 21.0, "hpe": 0.0, "O": dict.fromkeys(TEAMS, 0.0),
                "D": dict.fromkeys(TEAMS, 0.0)}

    def gap(self, offence, defence, unit, as_of):
        return self.gaps[(offence, defence)][S.MATCH_UNITS.index(unit)]


_rnd = random.Random(8)
_gaps = {(o, d): (_rnd.gauss(0, 40), _rnd.gauss(0, 25), _rnd.gauss(0, 5)) for o in TEAMS for d in TEAMS if o != d}
_fr = []
for i in range(400):
    h, a = _rnd.sample(TEAMS, 2)
    pace = _gaps[(h, a)][2] + _gaps[(a, h)][2]
    pts = [21 + 0.04 * _gaps[(o, d)][0] + 0.1 * _gaps[(o, d)][1] + 0.2 * pace for o, d in ((h, a), (a, h))]
    _fr.append({"day": (datetime.date(2025, 9, 7) + datetime.timedelta(weeks=i // 5)).isoformat(),
                "home": h, "away": a, "sig": {"neutral": 0.0}, "final": True, "hs": pts[0], "as": pts[1],
                "M": 0.5, "T": 42.5, "pml": 0.5})
_hi = max(_gaps, key=lambda k: _gaps[k][0] + _gaps[k][2] + _gaps[(k[1], k[0])][0] + _gaps[(k[1], k[0])][2])
_fr.append(dict(_fr[0], day="2027-01-03", home=_hi[0], away=_hi[1], final=False, hs=None, **{"as": None}))
_pn = S.walk_forward(_fr, _Flat(_gaps))[-1]
_want = sum(0.04 * _gaps[k][0] + 0.1 * _gaps[k][1] + 0.2 * (_gaps[_hi][2] + _gaps[(_hi[1], _hi[0])][2])
            for k in (_hi, (_hi[1], _hi[0])))
ck(_want > 5 and 0.5 * _want < _pn["total"] - 42.0 <= _want,
   "🔴 a fast, pass-heavy matchup moves the predicted total up by what earlier games showed",
   "moved %.2f, earlier games say %.2f" % (_pn["total"] - 42.0, _want))
# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 EVERY CHANCE COMES FROM THE PREDICTED SCORE'S CURVE")
# ══════════════════════════════════════════════════════════════════════
_p = {"row": {"M": 3.0, "T": 44.5}, "margin": 7.0, "total": 47.0, "sigma": {"margin": 13.0, "total": 14.0},
      "k": {"spread": 1.5, "total": 1.2, "moneyline": 2.0}}
_N = statistics.NormalDist()
eq([round(S.chance(_p, mk), 9) for mk in F.MARKETS],
   [round(_N.cdf(4 / 13), 9), round(_N.cdf(2.5 / 14), 9), round(_N.cdf(7 / 13), 9)],
   "🔴 spread, total and moneyline = Phi((predicted - line) / sigma), the moneyline's line 0")
eq([round(S.chance(_p, mk, cal=True), 9) for mk in F.MARKETS],
   [round(_N.cdf(4 / 13 / 1.5), 9), round(_N.cdf(2.5 / 14 / 1.2), 9), round(_N.cdf(7 / 13 / 2.0), 9)],
   "🔴 the calibrated version is the same curve with sigma x k")
_rnd = random.Random(9)
_past = []
for _ in range(3000):      # the truth is twice as wide as the curve: the right k is about 2
    z = _rnd.gauss(0, 1.5)
    _past.append({"row": {"M": 0.0, "final": True, "hs": 1, "as": 0, "pml": 0.5}, "margin": 13.0 * z,
                  "total": 0.0, "sigma": {"margin": 13.0, "total": 1.0}})
    _past[-1]["row"]["hs"] = 1 if _rnd.random() < _N.cdf(z / 2.0) else -1
ck(1.6 <= S.pick_k(_past, "spread") <= 2.4, "an overconfident curve is widened by k fitted on earlier games",
   "k = %s" % S.pick_k(_past, "spread"))
eq(S.pick_k(_past[:S.MIN_CAL - 1], "spread"), 1.0, "under 100 earlier games k = 1")

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 NO CARD CHANGE: REPORT ONLY")
# ══════════════════════════════════════════════════════════════════════
_named = []
for f in sorted(glob.glob(os.path.join(ROOT, "*.py")) + glob.glob(os.path.join(ROOT, "*.html"))
                + glob.glob(os.path.join(ROOT, "*.js")) + glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))):
    b = os.path.basename(f)
    if b.startswith("test_"):
        continue
    src = open(f, encoding="utf-8").read()
    if re.search(r"fb-score-model|\bfb_score_model\b", src):
        _named.append(b)
eq(_named, ["collect.py", "fb_score_model.py", "freshness.py"],
   "🔴 only collect.py's card-fb run, freshness and the module itself name the score model")
_src = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
_cfb = _src[_src.index('elif mode == "card-fb":'):_src.index('elif mode == "halftime-probe":')]
ck(_cfb.index("left = build_card_fb()") < _cfb.index("_fsm.build(LEAGUE)"),
   "it is built AFTER the card, so the card never waits on it")


def _in_try(src, call):
    """True when every `call(...)` statement in `src` sits inside a try: body."""
    tree = ast.parse(src)
    calls = {id(n) for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) == call}
    inside = {id(n) for t in ast.walk(tree) if isinstance(t, ast.Try) for b in t.body for n in ast.walk(b)}
    return bool(calls) and calls <= inside


ck(_in_try(_src, "_fsm.build"), "a score-model failure is caught: it never costs the card run")
ck(not _in_try("import x as _fsm\n_fsm.build(1)\n", "_fsm.build"), "...and that check bites on a bare call")
_before = {os.path.relpath(f, LG): hashlib.sha256(open(f, "rb").read()).hexdigest()
           for f in glob.glob(os.path.join(LG, "**", "*"), recursive=True) if os.path.isfile(f)}
_doc = S.build("nfl", root=LG, now=NOW)
_after = {os.path.relpath(f, LG): hashlib.sha256(open(f, "rb").read()).hexdigest()
          for f in glob.glob(os.path.join(LG, "**", "*"), recursive=True) if os.path.isfile(f)}
eq(sorted(k for k in _after if _before.get(k) != _after[k]),
   [os.path.join("data", "nfl", "latest", "fb-score-model.json")],
   "🔴 a build writes fb-score-model.json and changes nothing else")
ck(_doc["report_only"] is True and _doc["upcoming"] and all(
    g["score"]["home"] is not None and g["score_curve"]["moneyline"] is not None for g in _doc["upcoming"]),
   "the file holds this week's predicted scores and chances, marked report only")
ck(_doc["backtest"]["games_predicted"] > 100 and _doc["backtest"]["log_loss"]["spread"]["games"] > 0,
   "...and the walk-forward backtest")

# ══════════════════════════════════════════════════════════════════════
section("7. THE CODE RUNS THE SETTINGS THE DESIGN FIXED")
# ══════════════════════════════════════════════════════════════════════
_des = open(os.path.join(ROOT, S.DESIGN), encoding="utf-8").read()
for _claim, _ok in (("ridge 100", S.MATCH_RIDGE == 100.0), ("under 200 earlier sides", S.MIN_SIDES == 200),
                    ("under 100 such games, no chance", S.MIN_SIGMA == 100),
                    ("under 100 such games, k = 1", S.MIN_CAL == 100),
                    ("1.00, 1.05, …, 3.00", S.K_GRID[:2] == (1.0, 1.05) and S.K_GRID[-1] == 3.0),
                    ("Monday / 150", F.RATING_HALF_LIFE == 150.0), ("ridge 1 on every team term", F.RATING_RIDGE == 1.0),
                    ("other units to 1e-7", FM.UNIT_TOL == 1e-7), ("next 8 days", F.PRICING_DAYS == 8),
                    ("`pass_yds`; rush", S.MATCH_UNITS == ("pass_yds", "rush_yds", "plays")),
                    ("65–70, 70+", S.BANDS == (0.50, 0.55, 0.60, 0.65, 0.70))):
    ck(_claim in _des and _ok, "design says %r and the code runs it" % _claim)
