#!/usr/bin/env python3
"""T72 — THE MATCHUP GRADE (research/fb_refit_spec.md §3f): CL / CLC (class against
above-average opponents), WL / WLC (the win-loss resume), MC / MCC (blowouts capped)
and AJ / AJC (form and the defence rank, opponent-adjusted). `[Sam, 2026-10-26]`
Planted trees and a pinned clock only. ⛔ Reads no live data and writes nothing under
data/ or picks/: rule 13, no history, fit or log loss of these challengers is computed
on the real games. Their numbers are pinned in test_fb_refit.py §17 (§3f names it).

# @vacuity 🔴 CL: a team's margin class is its result MINUS what its rating says
#   file: fb_challengers.py
#   find:                 num[t][0] += w * ((pf - pa) - (s["hfa"] * f + R[t] - R[o]))
#   with:                 num[t][0] += w * ((pa - pf) - (s["hfa"] * f + R[t] - R[o]))
#
# @vacuity 🔴 CL: the class number is shrunk by 10, fixed
#   file: fb_challengers.py
#   find: CLASS_SHRINK = 10.0
#   with: CLASS_SHRINK = 1.0
#
# @vacuity 🔴 CL: only games against an above-average opponent count
#   file: fb_challengers.py
#   find:             if o in good["R"]:           # C: margin class
#   with:             if True:           # C: margin class
#
# @vacuity 🔴 CL: a row's class term counts only against an above-average opponent
#   file: fb_challengers.py
#   find:     ab = lambda k, t: 1.0 if t in good[k] else 0.0  # noqa: E731
#   with:     ab = lambda k, t: 1.0  # noqa: E731
#
# @vacuity 🔴 CL: cl_t's away-defence term is gated on the HOME offence
#   file: fb_challengers.py
#   find:             co_h * ab("D", away) + cd_a * ab("O", home) + co_a * ab("D", home) + cd_h * ab("O", away))
#   with:             co_h * ab("D", away) + cd_a * ab("O", away) + co_a * ab("D", home) + cd_h * ab("O", away))
#
# @vacuity 🔴 CL: the defence class reads the points the team ALLOWED
#   file: fb_challengers.py
#   find:                 num[t][2] += w * (pa - (s["base"] + s["hpe"] * (1.0 if f < 0 else 0.0) + O[o] - D[t]))
#   with:                 num[t][2] += w * (pf - (s["base"] + s["hpe"] * (1.0 if f < 0 else 0.0) + O[o] - D[t]))
#
# @vacuity 🔴 CL: nothing dated on or after the row's Monday is read
#   file: fb_challengers.py
#   find:     return G[:bisect.bisect_left(G, (wk,))]
#   with:     return G
#
# @vacuity 🔴 AJ: a team's last 4 are its last 4 BEFORE the row's Monday
#   file: fb_challengers.py
#   find:         last = gs[:bisect.bisect_left(gs, (wk,))][-FORM_GAMES:]
#   with:         last = gs[-FORM_GAMES:]
#
# @vacuity 🔴 WL / MC: the weekly solves read nothing dated on the row's Monday
#   file: fb_challengers.py
#   find:         while j < len(items) and items[j][0] < wk:
#   with:         while j < len(items) and items[j][0] <= wk:
#
# @vacuity 🔴 WL: a tie counts 0.5
#   file: fb_challengers.py
#   find:     y = [1.0 if g[4] > g[5] else 0.0 if g[4] < g[5] else 0.5 for g in G]
#   with:     y = [1.0 if g[4] > g[5] else 0.0 if g[4] < g[5] else 0.0 for g in G]
#
# @vacuity 🔴 WL: the score margin is never read
#   file: fb_challengers.py
#   find:     y = [1.0 if g[4] > g[5] else 0.0 if g[4] < g[5] else 0.5 for g in G]
#   with:     y = [_p((g[4] - g[5]) / 7.0) for g in G]
#
# @vacuity 🔴 WL: ridge 1 on every team term
#   file: fb_challengers.py
#   find:             num, den = -RIDGE * B[t], RIDGE
#   with:             num, den = 0.0, RIDGE
#
# @vacuity 🔴 WL: the home edge is fitted, unpenalised
#   file: fb_challengers.py
#   find:         s["a"] += _home_step(num, den, s["a"], G, w, y, B)
#   with:         s["a"] += 0.0
#
# @vacuity 🔴 WL: a long step on the home edge is not trusted (the warm start that blew up to -2e15)
#   file: fb_challengers.py
#   find:     step = math.copysign(min(abs(num) / den if den > 0 else math.inf, A_STEP), num)
#   with:     return num / den if den > 0 else 0.0
#
# @vacuity 🔴 WL: ...and is halved until the fit is no worse
#   file: fb_challengers.py
#   find:         while abs(step) >= 1.0 and _home_fit(a + step, G, w, y, B) < here:
#   with:         while False:
#
# @vacuity 🔴 WL: the fit it checks against is §3f's likelihood
#   file: fb_challengers.py
#   find:             out -= wi * (yi * _softplus(-z) + (1.0 - yi) * _softplus(z))
#   with:             out -= wi * (yi * _softplus(z) + (1.0 - yi) * _softplus(-z))
#
# @vacuity 🔴 every solver weekly() drives is replayed warm and cold
#   file: fb_challengers.py
#   find:         sol = weekly(FM.rating_games(lg, root), weeks, solve_resume)
#   with:         sol = weekly(FM.rating_games(lg, root), weeks, lambda G, wk, warm: solve_resume(G, wk, None))
#
# @vacuity 🔴 AJ: a defence not ranked is no rank, though 10 or more are
#   file: fb_challengers.py
#   find:             "def": (f[r["home"]] + f[r["away"]]) / 2.0 if r["home"] in f and r["away"] in f else None}
#   with:             "def": (f.get(r["home"], 0.5) + f.get(r["away"], 0.5)) / 2.0 if f else None}
#
# @vacuity 🔴 MC: the NFL cap is 21 points
#   file: fb_challengers.py
#   find: CAP = {"nfl": 21.0, "ncaaf": 28.0}
#   with: CAP = {"nfl": 28.0, "ncaaf": 28.0}
#
# @vacuity 🔴 MC: the college cap is 28 points
#   file: fb_challengers.py
#   find: CAP = {"nfl": 21.0, "ncaaf": 28.0}
#   with: CAP = {"nfl": 21.0, "ncaaf": 21.0}
#
# @vacuity 🔴 MC: a margin is capped both ways
#   file: fb_challengers.py
#   find:     return [(d, h, a, f, max(-cap, min(cap, hp - ap)), 0.0, 0.0) for d, h, a, f, hp, ap in FM.rating_games(lg, root)]
#   with:     return [(d, h, a, f, min(cap, hp - ap), 0.0, 0.0) for d, h, a, f, hp, ap in FM.rating_games(lg, root)]
#
# @vacuity 🔴 MC: the capped margin replaces the FIRST input
#   file: fb_challengers.py
#   find:         return [first] + list(x[1:])
#   with:         return list(x) + [first]
#
# @vacuity 🔴 AJ: the adjusted form replaces the third input (index 2)
#   file: fb_challengers.py
#   find:         x[2] = ((0.0 if fm is None or M is None else (fm - M) / 10.0) if market == "spread" else
#   with:         x[1] = ((0.0 if fm is None or M is None else (fm - M) / 10.0) if market == "spread" else
#
# @vacuity 🔴 AJ: the adjusted defence rank replaces the total's fourth input (index 3)
#   file: fb_challengers.py
#   find:             x[3] = 0.0 if aj.get("def") is None else (aj["def"] - 0.5) * 4.0
#   with:             x[4] = 0.0 if aj.get("def") is None else (aj["def"] - 0.5) * 4.0
#
# @vacuity 🔴 AJ: a game's offence reading adds the opponent's defence rating
#   file: fb_challengers.py
#   find:             pf - s["hpe"] * (1.0 if f > 0 else 0.0) + s["D"][o] - s["base"],
#   with:             pf - s["hpe"] * (1.0 if f > 0 else 0.0) - s["base"],
#
# @vacuity 🔴 AJ: form_t carries the home points edge
#   file: fb_challengers.py
#   find:             (s["base"] + s["hpe"] * h + or_h - dr_a) + (s["base"] + or_a - dr_h))
#   with:             (s["base"] + or_h - dr_a) + (s["base"] + or_a - dr_h))
#
# @vacuity 🔴 AJ: fewer than 2 earlier games is no form
#   file: fb_challengers.py
#   find: FORM_GAMES, FORM_MIN = 4, 2
#   with: FORM_GAMES, FORM_MIN = 4, 1
#
# @vacuity 🔴 AJ: the last 4 games
#   file: fb_challengers.py
#   find: FORM_GAMES, FORM_MIN = 4, 2
#   with: FORM_GAMES, FORM_MIN = 5, 2
#
# @vacuity 🔴 AJ: rank 1 = allows the most; rank = 1 + the number allowing more
#   file: fb_challengers.py
#   find:     return {t: (1 + len(v) - bisect.bisect_right(v, x)) / float(len(v)) for t, x in allow.items()}
#   with:     return {t: (len(v) - bisect.bisect_right(v, x)) / float(len(v)) for t, x in allow.items()}
#
# @vacuity 🔴 AJ: fewer than 10 ranked defences is no rank
#   file: fb_challengers.py
#   find: DEF_MIN = 10
#   with: DEF_MIN = 9
#
# @vacuity 🔴 AJ: ...and 10 is enough
#   file: fb_challengers.py
#   find: DEF_MIN = 10
#   with: DEF_MIN = 11
#
# @vacuity 🔴 AJ: the defence table reads nothing dated on the row's Monday
#   file: fb_matchups.py
#   find:             done[wk] = F.solve_ratings([g for g in self.G[unit] if g[0] < wk], wk,
#   with:             done[wk] = F.solve_ratings([g for g in self.G[unit] if g[0] <= wk], wk,
#
# @vacuity 🔴 against another champion: AJ, AJC, MC and MCC build only beside one that appends
#   file: fb_challengers.py
#   find:         return ch is None or ch in APPEND_ONLY
#   with:         return True
#
# @vacuity 🔴 ...the append-only list is §3f's (IN appends)
#   file: fb_challengers.py
#   find: APPEND_ONLY = ("E", "P", "AV", "AVC", "WX", "WXC", "IN", "RS", "RSC", "CL", "CLC", "WL", "WLC")
#   with: APPEND_ONLY = ("E", "P", "AV", "AVC", "WX", "WXC", "RS", "RSC", "CL", "CLC", "WL", "WLC")
#
# @vacuity 🔴 registration: never before 2026-11-02
#   file: fb_refit.py
#   find:         return max(start, monday_on_or_after(after)) if after else None
#   with:         return monday_on_or_after(after) if after else None
#
# @vacuity 🔴 CL is an NFL challenger (13 a league)
#   file: fb_challengers.py
#   find:     "CL": {"league": "nfl", "what": "class vs good teams", "markets": ("spread", "total", "moneyline"),
#   with:     "CL": {"league": "ncaaf", "what": "class vs good teams", "markets": ("spread", "total", "moneyline"),
#
# @vacuity 🔴 league() builds every T72 input itself
#   file: fb_challengers.py
#   find:         return attach_grade(name, lg, rows, root)
#   with:         return rows
"""
import atexit
import datetime
import gzip
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
import fb_challengers as FC  # noqa: E402
import fb_matchups as MT  # noqa: E402
import fb_model as FM  # noqa: E402
import fb_refit as R  # noqa: E402
from tcheck import ck, eq, note, section  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 11, 2, 11, 17, tzinfo=UTC)     # a Monday
NEW = {"nfl": ["CL", "WL", "MC", "AJ"], "ncaaf": ["CLC", "WLC", "MCC", "AJC"]}
TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])


def tree():
    t = tempfile.mkdtemp(prefix="fbgrade-")
    TREES.append(t)
    return t


def put(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with (gzip.open(p, "wt") if p.endswith(".gz") else open(p, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


def row(gid, lg, day, home, away, season=2025, **kw):
    return dict({"id": gid, "lg": lg, "season": season, "day": day, "home": home, "away": away,
                 "final": False, "hs": None, "as": None, "M": 3.0, "T": 44.5, "pml": 0.6,
                 "sig": {"neutral": 0.0, "dome": 0.0, "own_m": 2.0, "own_t": 45.0, "h2h_m": 1.0,
                         "h2h_t": 46.0, "form_m": 2.5, "form_t": 43.0, "def": 0.55, "poss": 0.02,
                         "out": 1.0, "vac_h": 0.2, "vac_a": 0.1}}, **kw)


def rounds(teams):
    """A round robin by the circle method (an odd list gets a bye)."""
    rot = list(teams) + ([None] if len(teams) % 2 else [])
    out = []
    for _ in range(len(rot) - 1):
        out.append([(rot[i], rot[-1 - i]) for i in range(len(rot) // 2) if rot[i] and rot[-1 - i]])
        rot = [rot[0], rot[-1]] + rot[1:-1]
    return out


def league_games(teams, weeks, seed, start=datetime.date(2025, 9, 7)):
    """Weekly Sunday games: (id, day, home, away, neutral, home pts, away pts, yards {team: (pass, rush)})."""
    rr = random.Random(seed)
    power = {t: rr.gauss(0, 8) for t in teams}
    rds, out = rounds(teams), []
    for w in range(weeks):
        day = (start + datetime.timedelta(weeks=w)).isoformat()
        for j, (h, a) in enumerate(rds[w % len(rds)]):
            h, a = (a, h) if w % 2 else (h, a)
            neutral = j == 0 and w % 4 == 0
            pts = {o: max(0, int(round(22 + (power[o] - power[x]) / 2 + rr.gauss(0, 10)
                                       + (1.5 if o == h and not neutral else 0))))
                   for o, x in ((h, a), (a, h))}
            if w == 3 and j == 1:
                pts[a] = pts[h]                                   # a tie
            yds = {o: (rr.randint(150, 330) + int(4 * power[o]), rr.randint(60, 190) - int(3 * power[x]))
                   for o, x in ((h, a), (a, h))}
            out.append(("g%d_%d" % (w, j), day, h, a, neutral, pts[h], pts[a], yds))
    return out


def plant(t, games, fcs=("T10", "T11"), lgs=("nfl", "ncaaf"), nolog=()):
    """Both leagues get the same games; college lists `fcs` as FCS, the rest FBS. A team in
    `nolog` has no player logs (its games carry points but no yards)."""
    logs = {}
    for gid, day, h, a, _n, _hp, _ap, yds in games:
        for o in (h, a):
            if o in nolog:
                continue
            pa, ru = yds[o]
            for pos, st in (("QB", {"att": 30, "pass_yds": pa}), ("RB", {"car": 25, "rush_yds": ru})):
                logs.setdefault(o + pos, {"name": o + pos, "pos": pos, "g": []})["g"].append(
                    dict(st, d=day, game_id=gid, team=o))
    for lg in lgs:
        put(t, "data/%s/latest/schedule-2025.json.gz" % lg, {"season": 2025, "games": [
            {"id": gid, "start": day + "T17:00:00Z", "home": h, "away": a, "neutral": n, "final": True,
             "home_score": hp, "away_score": ap, "home_class": "fcs" if h in fcs else "fbs",
             "away_class": "fcs" if a in fcs else "fbs"} for gid, day, h, a, n, hp, ap, _y in games]})
        put(t, "data/%s/latest/players-2025.json.gz" % lg, {"players": logs})


def weight(day, wk):            # ⛔ written out here, not FC.weight: an independent copy of §3f's w
    return 0.5 ** ((datetime.date.fromisoformat(wk) - datetime.date.fromisoformat(day)).days / 150.0)


TEAMS = ["T%02d" % i for i in range(12)]
GAMES = league_games(TEAMS, 30, 72)              # 2025-09-07 .. 2026-03-29, Sundays
WK = "2026-03-30"                                # the rows' Monday
ROWS_AT = [("r1", "2026-04-01", "T00", "T05", 0.0), ("r2", "2026-04-01", "T03", "T10", 1.0),
           ("r3", "2026-04-02", "T11", "T07", 0.0)]


def rows_for(lg):
    out = []
    for gid, day, h, a, n in ROWS_AT:
        r = row(gid, lg, day, h, a)
        r["sig"]["neutral"] = n
        out.append(r)
    return out


def numbers(t, lg):
    """Every T72 number of every planted row, attached the way league() does."""
    rs = rows_for(lg)
    for n in NEW[lg]:
        FC.attach(n, lg, rs, t)
    return [{k: r["sig"].get(k) for k in ("cl", "wl", "mc", "aj")} for r in rs]


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 POINT IN TIME: NOTHING DATED ON OR AFTER THE ROW'S MONDAY CHANGES A T72 NUMBER")
# ══════════════════════════════════════════════════════════════════════
T1 = tree()
plant(T1, GAMES)
before_ = {lg: numbers(T1, lg) for lg in NEW}
_late = [("late0", WK, "T00", "T05", False, 70, 0, {"T00": (900, 400), "T05": (5, 0)}),
         ("late1", WK, "T10", "T03", False, 0, 63, {"T10": (0, 0), "T03": (800, 500)}),
         ("late2", "2026-04-01", "T11", "T07", False, 3, 3, {"T11": (2, 1), "T07": (999, 999)}),
         ("late3", "2026-04-01", "T02", "T09", False, 56, 3, {"T02": (700, 300), "T09": (1, 1)})]
plant(T1, GAMES + _late)
after_ = {lg: numbers(T1, lg) for lg in NEW}
for lg in NEW:
    ck(all(v["cl"] and v["wl"] is not None and v["mc"] is not None and v["aj"]["form"] and v["aj"]["def"]
           for v in before_[lg]), "%s: every planted row has every T72 number" % lg, before_[lg])
    eq(after_[lg], before_[lg], "🔴 %s: games dated on the Monday (%s) and after it, with 70-0 scores and "
       "900-yard days, change none of CL, WL, MC or AJ's numbers" % (lg, WK))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 CL: CLASS, BY HAND (THE RESIDUALS, THE [x] GATES, THE /(SUM w + 10) SHRINK, cl_t)")
# ══════════════════════════════════════════════════════════════════════
# X beats BAD by 42 and loses to GOOD twice. w: 150 days before the Monday 0.5, 300 0.25, 450 0.125.
_wk = "2026-10-05"
_d = lambda n: (datetime.date(2026, 10, 5) - datetime.timedelta(days=n)).isoformat()  # noqa: E731
G2 = sorted([(_d(150), "X", "GOOD", 1.0, 10.0, 30.0),       # X at home, loses by 20
             (_d(300), "BAD", "X", 1.0, 3.0, 45.0),         # X away, wins by 42
             (_d(450), "X", "GOOD", 0.0, 14.0, 24.0)])      # neutral, X loses by 10
S2 = {"hfa": 2.0, "base": 21.0, "hpe": 1.5, "R": {"X": 4.0, "GOOD": 6.0, "BAD": -8.0},
      "O": {"X": 2.0, "GOOD": 3.0, "BAD": -5.0}, "D": {"X": 1.0, "GOOD": 4.0, "BAD": -6.0},
      "teams": {"X", "GOOD", "BAD"}}
GOOD2 = {"R": {"GOOD"}, "D": {"GOOD"}, "O": {"GOOD", "X"}}
C2 = FC.class_numbers(G2, _wk, S2, GOOD2)
# C_X: GOOD games only. 10-30 at home: -20 - (2 + 4 - 6) = -20, x0.5; neutral 14-24: -10 - (4 - 6) = -8, x0.125.
# CO_X: 10 - (21 + 1.5 + 2 - 4) = -10.5 x0.5; 14 - (21 + 2 - 4) = -5 x0.125.
# CD_X: allowed 30 - (21 + 0 + 3 - 1) = 7 x0.5; 24 - (21 + 3 - 1) = 1 x0.125.
# GOOD: only CD (X is an above-average OFFENCE): 10 - (21 + 1.5 + 2 - 4) = -10.5 x0.5; 14 - 19 = -5 x0.125.
# BAD: only CD: allowed 45 - (21 + 0 + 2 + 6) = 16 x0.25, / (0.25 + 10).
_want = {"X": (-11.0 / 10.625, -5.875 / 10.625, 3.625 / 10.625), "GOOD": (0.0, 0.0, -5.875 / 10.625),
         "BAD": (0.0, 0.0, 4.0 / 10.25)}
ck(all(abs(a - b) < 1e-9 for t in _want for a, b in zip(C2[t], _want[t])) and set(C2) == set(_want),
   "🔴 C, CO and CD by hand: residuals against above-average opponents only, sum(w x residual) / "
   "(sum w + 10); a team with none is 0", C2)
ck(C2["X"][0] < 0, "🔴 X, who beats bad teams by a lot and loses to good ones, has a NEGATIVE margin class")
eq([tuple(round(v, 9) for v in FC.class_row(S2, GOOD2, C2, h, a)) for h, a in (("X", "GOOD"), ("X", "BAD"))],
   [(round(-11.0 / 10.625, 9), round(-8.125 / 10.625, 9)), (0.0, round(4.0 / 10.25, 9))],
   "🔴 rows: X v GOOD: cl_m = C_X x [R_GOOD] - C_GOOD x [R_X] = C_X; cl_t = CO_X + CD_GOOD + CD_X. "
   "X v BAD: cl_m = 0 (neither is above average in R); cl_t = CD_BAD x [O_X] alone")
eq(FC.class_row(S2, GOOD2, C2, "X", "NEW"), None, "   ...and a team not in s gives no number (both inputs 0)")

# The wiring, on the planted league: s is the champion's own solve for the Monday, "above average"
# is fb_model.above_average (college: against the FBS mean), and every game before the Monday counts.
for lg in NEW:
    _G = FM.rating_games(lg, T1)
    _s = FM.own_ratings(_G, {WK})[WK]
    _ref = [t for t in _s["teams"] if lg == "nfl" or t not in ("T10", "T11")]
    _good = {k: {t for t in _s["teams"] if _s[k][t] > sum(_s[k][x] for x in _ref) / len(_ref)} for k in "ROD"}
    _num = {t: [0.0, 0.0, 0.0] for t in _s["teams"]}
    _den = {t: [0.0, 0.0, 0.0] for t in _s["teams"]}
    for d, h, a, hf, hp, ap in _G:
        if d >= WK:
            continue
        w = weight(d, WK)
        for t, o, f, pf, pa in ((h, a, hf, hp, ap), (a, h, -hf, ap, hp)):
            exp_m = _s["hfa"] * f + _s["R"][t] - _s["R"][o]
            exp_f = _s["base"] + (_s["hpe"] if f == 1 else 0.0) + _s["O"][t] - _s["D"][o]
            exp_a = _s["base"] + (_s["hpe"] if f == -1 else 0.0) + _s["O"][o] - _s["D"][t]
            for k, key, res in ((0, "R", pf - pa - exp_m), (1, "D", pf - exp_f), (2, "O", pa - exp_a)):
                if o in _good[key]:
                    _num[t][k] += w * res
                    _den[t][k] += w
    _C = {t: [_num[t][k] / (_den[t][k] + 10.0) for k in range(3)] for t in _s["teams"]}
    _ab = lambda k, t: 1.0 if t in _good[k] else 0.0  # noqa: E731
    _rs = FC.attach("CL" if lg == "nfl" else "CLC", lg, rows_for(lg), T1)
    _bad = []
    for r in _rs:
        h, a = r["home"], r["away"]
        want = (_C[h][0] * _ab("R", a) - _C[a][0] * _ab("R", h),
                _C[h][1] * _ab("D", a) + _C[a][2] * _ab("O", h) + _C[a][1] * _ab("D", h) + _C[h][2] * _ab("O", a))
        if max(abs(x - y) for x, y in zip(r["sig"]["cl"], want)) > 1e-6:
            _bad.append((r["id"], r["sig"]["cl"], want))
    ck(not _bad and any(abs(v) > 0.01 for r in _rs for v in r["sig"]["cl"]),
       "🔴 %s: attach reads the champion's own solve for the row's Monday and §3f's 'above average' "
       "(%s), every earlier game with its weight" % (lg, "every team" if lg == "nfl" else "the FBS mean"), _bad)
    _fcs = FM.above_average(_s, lg, FM.fbs_teams(T1))
    if lg == "ncaaf":
        ck(_fcs == _good and FM.fbs_teams(T1) == set(TEAMS) - {"T10", "T11"},
           "   ...college compares against the FBS teams' mean; the FCS teams stay in the solve")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 WL: THE RESUME MATCHES A DIRECT NEWTON SOLVE; TIES 0.5; THE MARGIN NEVER READ")
# ══════════════════════════════════════════════════════════════════════


def direct_bt(G, wk):
    """The same penalised likelihood maximised by full Newton steps on every number at once."""
    teams = sorted({g[1] for g in G} | {g[2] for g in G})
    ix = {t: i + 1 for i, t in enumerate(teams)}
    k = len(teams) + 1
    th = [0.0] * k
    for _ in range(200):
        gr, H = [0.0] * k, [[0.0] * k for _ in range(k)]
        for d, h, a, f, hp, ap in G:
            w = weight(d, wk)
            y = 1.0 if hp > ap else (0.0 if hp < ap else 0.5)
            x = [0.0] * k
            x[0], x[ix[h]], x[ix[a]] = f, 1.0, -1.0
            p = 1.0 / (1.0 + math.exp(-sum(u * v for u, v in zip(x, th))))
            for i in range(k):
                gr[i] += w * (y - p) * x[i]
                for j in range(k):
                    H[i][j] += w * p * (1.0 - p) * x[i] * x[j]
        for i in range(1, k):
            gr[i] -= th[i]
            H[i][i] += 1.0
        step = FM._solve(H, gr)
        th = [a + b for a, b in zip(th, step)]
        if max(abs(v) for v in step) < 1e-13:
            break
    return th[0], {t: th[ix[t]] for t in teams}


G3 = [g for g in FM.rating_games("nfl", T1) if g[0] < WK]
ck(any(g[4] == g[5] for g in G3) and any(g[3] == 0.0 for g in G3), "the planted games hold a tie and a neutral site")
s3 = FC.solve_resume(G3, WK)
a3, B3 = direct_bt(G3, WK)
ck(abs(s3["a"] - a3) < 1e-6 and max(abs(s3["B"][t] - B3[t]) for t in B3) < 1e-6 and abs(a3) > 0.01,
   "🔴 WL's solve (a and every B) matches a direct Newton solve of the same penalised likelihood to 1e-6",
   (s3["a"], a3))
_warm = FC.weekly(G3 + [g for g in FM.rating_games("nfl", T1) if g[0] >= WK], ["2026-03-02", WK], FC.solve_resume)
ck(max([abs(_warm[WK]["a"] - a3)] + [abs(_warm[WK]["B"][t] - B3[t]) for t in B3]) < 1e-6,
   "   ...also warm-started from an earlier Monday")
_tie = [g for g in G3 if g[4] == g[5]][0]
_as_home_win = [g if g != _tie else g[:4] + (g[4] + 1.0, g[5]) for g in G3]
ck(abs(FC.solve_resume(_as_home_win, WK)["a"] - s3["a"]) > 1e-4, "🔴 a tie is not a home win...")
_y0 = [g if g != _tie else g[:4] + (g[4], g[5] + 1.0) for g in G3]
ck(abs(FC.solve_resume(_y0, WK)["a"] - s3["a"]) > 1e-4, "🔴 ...nor an away win: it counts 0.5")
_rescored = [g[:4] + ((g[4] * 3 + 1, g[5]) if g[4] > g[5] else (g[4], g[5] * 2 + 7) if g[4] < g[5]
                      else (g[4] + 20, g[5] + 20)) for g in G3]
s3b = FC.solve_resume(_rescored, WK)
ck(abs(s3b["a"] - s3["a"]) < 1e-12 and max(abs(s3b["B"][t] - s3["B"][t]) for t in s3["B"]) < 1e-12,
   "🔴 every score changed, every winner kept: the resume does not move (the margin is never read)")
eq(FC.resume_margin(s3, "T00", "T05", 1.0), s3["B"]["T00"] - s3["B"]["T05"], "   a neutral row is B_H - B_A")
eq(FC.resume_margin(s3, "T00", "T05", 0.0), s3["a"] + s3["B"]["T00"] - s3["B"]["T05"], "   ...else a + B_H - B_A")
eq(FC.resume_margin(s3, "T00", "NEW", 0.0), None, "   ...and a team with no earlier game gives no number")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 MC: BLOWOUTS CAPPED AT 21 (NFL) / 28 (COLLEGE); UNCAPPED IT IS THE CHAMPION'S OWN MARGIN")
# ══════════════════════════════════════════════════════════════════════
eq(FC.CAP, {"nfl": 21.0, "ncaaf": 28.0}, "🔴 the caps are three and four touchdowns")
T4 = tree()
_big = [(gid, day, h, a, n, hp + (40 if i % 3 == 0 else 0), ap, y)
        for i, (gid, day, h, a, n, hp, ap, y) in enumerate(GAMES)]       # blowouts to cap
plant(T4, _big)
for lg, cap in (("nfl", 21.0), ("ncaaf", 28.0)):
    _cg = FC.capped_games(lg, T4)
    _rg = FM.rating_games(lg, T4)
    eq([g[4] for g in _cg], [max(-cap, min(cap, g[4] - g[5])) for g in _rg],
       "🔴 %s: every margin capped at +/- %d" % (lg, cap))
    ck(any(g[4] - g[5] > cap for g in _rg) and any(g[4] - g[5] < -cap for g in _rg),
       "   ...the planted %s league has blowouts both ways" % lg)
    _G = [g for g in _cg if g[0] < WK]
    teams = sorted({g[1] for g in _G} | {g[2] for g in _G})
    k = len(teams) + 1
    A, b = [[0.0] * k for _ in range(k)], [0.0] * k
    for g in _G:
        x = [g[3]] + [1.0 if g[1] == t else -1.0 if g[2] == t else 0.0 for t in teams]
        w = weight(g[0], WK)
        for i in range(k):
            b[i] += w * x[i] * g[4]
            for j in range(k):
                A[i][j] += w * x[i] * x[j]
    for i in range(1, k):
        A[i][i] += 1.0
    direct = FM._solve(A, b)
    _rs = FC.attach(NEW[lg][2], lg, rows_for(lg), T4)
    _want = [direct[0] * (1.0 - r["sig"]["neutral"]) + direct[1 + teams.index(r["home"])]
             - direct[1 + teams.index(r["away"])] for r in _rs]
    ck(max(abs(r["sig"]["mc"] - w) for r, w in zip(_rs, _want)) < 1e-6,
       "🔴 %s: MC's margin is a direct solve of the champion's margin equation on capped margins "
       "(weights, ridge 1 on R only)" % lg, ([r["sig"]["mc"] for r in _rs], _want))
    _own = FM.own_ratings(FM.rating_games(lg, T4), {WK})[WK]
    _old = FC.CAP[lg]
    FC.CAP[lg] = float("inf")
    try:
        _rs = FC.attach(NEW[lg][2], lg, rows_for(lg), T4)
    finally:
        FC.CAP[lg] = _old
    _ch = [FM.own_numbers(_own, r["home"], r["away"], r["sig"]["neutral"])[0] for r in _rs]
    ck(max(abs(r["sig"]["mc"] - c) for r, c in zip(_rs, _ch)) < 1e-6,
       "🔴 %s: with no cap MC's margin IS the champion's own margin (fb_model.own_numbers) to 1e-6" % lg,
       ([r["sig"]["mc"] for r in _rs], _ch))

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 AJ: THE LAST 4 READ AGAINST s (INDEX 2), THE ADJUSTED DEFENCE RANK (TOTAL INDEX 3)")
# ══════════════════════════════════════════════════════════════════════
for lg in NEW:
    _G = [g for g in FM.rating_games(lg, T1) if g[0] < WK]
    _s = FM.own_ratings(FM.rating_games(lg, T1), {WK})[WK]
    tb = MT.Tables(lg, T1)
    _al = {}
    for t in _s["teams"]:
        p, ru = tb.unit_allowed(t, "pass_yds", WK), tb.unit_allowed(t, "rush_yds", WK)
        if p is not None and ru is not None:
            _al[t] = p + ru
    _frac = {t: (1 + sum(1 for u in _al.values() if u > v)) / len(_al) for t, v in _al.items()}

    def _reads(t):
        mine = [g for g in _G if t in (g[1], g[2])][-4:]
        out = []
        for d, h, a, hf, hp, ap in mine:
            if t == h:
                o, f, pf, pa = a, hf, hp, ap
            else:
                o, f, pf, pa = h, -hf, ap, hp
            out.append((pf - pa - _s["hfa"] * f + _s["R"][o],
                        pf - (_s["hpe"] if f == 1 else 0.0) + _s["D"][o] - _s["base"],
                        _s["base"] + (_s["hpe"] if f == -1 else 0.0) + _s["O"][o] - pa))
        return [sum(x[i] for x in out) / len(out) for i in range(3)]
    _rs = FC.attach(NEW[lg][3], lg, rows_for(lg), T1)
    _bad = []
    for r in _rs:
        h = 1.0 - r["sig"]["neutral"]
        rh, ra = _reads(r["home"]), _reads(r["away"])
        want_f = (_s["hfa"] * h + rh[0] - ra[0], (_s["base"] + _s["hpe"] * h + rh[1] - ra[2]) + (_s["base"] + ra[1] - rh[2]))
        want_d = (_frac[r["home"]] + _frac[r["away"]]) / 2.0
        got = r["sig"]["aj"]
        if max(abs(x - y) for x, y in zip(got["form"], want_f)) > 1e-6 or abs(got["def"] - want_d) > 1e-9:
            _bad.append((r["id"], got, want_f, want_d))
    ck(not _bad and len(_al) == 12, "🔴 %s: form_m, form_t from each team's last 4 games read against s, and the "
       "defence fraction (rank 1 = allows the most passing + rushing yards, opponent-adjusted), by hand" % lg, _bad)
    ck(any(abs(r["sig"]["aj"]["def"] - 0.5) > 0.05 for r in _rs), "   ...and the planted ranks are not all middling")

R5 = row("x", "nfl", "2026-04-01", "T00", "T05", M=3.0, T=45.0)
R5["sig"]["aj"] = {"form": (4.0, 47.0), "def": 0.7}
for n in ("AJ", "AJC"):
    r5 = dict(R5, lg=FC.CHALLENGERS[n]["league"])
    base = {mk: FM.features(r5, mk) for mk in FM.MARKETS}
    got = {mk: R.challenger_feat(n)(r5, mk) for mk in FM.MARKETS}
    want = {mk: list(base[mk]) for mk in FM.MARKETS}
    want["spread"][2], want["moneyline"][2], want["total"][2], want["total"][3] = 0.1, 0.4, 0.2, (0.7 - 0.5) * 4.0
    ck(all(len(got[mk]) == len(want[mk]) and max(abs(a - b) for a, b in zip(got[mk], want[mk])) < 1e-12
           for mk in FM.MARKETS),
       "🔴 %s: index 2 is (form_m - line) / 10, form_m / 10, (form_t - line) / 10; the total's index 3 is "
       "(fraction - 0.5) x 4; head-to-head (index 1) and every other input untouched" % n, (got, want))
    none = dict(r5, sig=dict(r5["sig"], aj={"form": None, "def": None}))
    nb = {mk: FM.features(none, mk) for mk in FM.MARKETS}
    ck(all(R.challenger_feat(n)(none, mk)[2] == 0.0 for mk in FM.MARKETS)
       and R.challenger_feat(n)(none, "total")[3] == 0.0
       and all(R.challenger_feat(n)(none, mk)[:2] + R.challenger_feat(n)(none, mk)[4:] == nb[mk][:2] + nb[mk][4:]
               for mk in FM.MARKETS),
       "   ...and no number is 0 (not the champion's raw form or rank)")
T5 = tree()
plant(T5, [g for g in GAMES if g[1] < "2025-09-08"] + [g for g in GAMES if g[1] > "2026-03-01"])
_one = FC.attach("AJ", "nfl", [row("y", "nfl", "2025-09-10", "T00", "T05")], T5)[0]["sig"]["aj"]
eq(_one["form"], None, "🔴 one earlier game each is no form (fewer than 2, as the champion)")
_two = FC.attach("AJ", "nfl", [row("y", "nfl", "2026-03-11", "T00", "T05")], T5)[0]["sig"]["aj"]
ck(_two["form"] is not None, "   ...and two are", _two)
for _n_teams, _want_def in ((10, True), (9, False)):
    T6 = tree()
    plant(T6, league_games(TEAMS[:_n_teams], 9, 74), fcs=())
    _d6 = FC.attach("AJ", "nfl", [row("w", "nfl", "2025-11-12", "T00", "T05")], T6)[0]["sig"]["aj"]["def"]
    eq(_d6 is not None, _want_def, "🔴 %d ranked defences: %s" % (_n_teams, "a rank" if _want_def else
                                                                 "no rank (fewer than 10 -> input 0)"))
# `[2026-10-26]` A review found §3f's other "-> 0", "a defence not ranked", never asked: every planted
# row's teams were ranked whenever 10 were. NEWB plays three earlier games (points, so it is in s and
# has a form) but has no player logs, so neither yard table carries it: 12 ranked, NEWB not.
T7 = tree()
_newb = [("nb%d" % i, d, h, a, False, hp, ap, {o: (210, 95) for o in (h, a)}) for i, (d, h, a, hp, ap) in
         enumerate((("2026-03-07", "NEWB", "T00", 24, 17), ("2026-03-14", "T01", "NEWB", 20, 23),
                    ("2026-03-21", "NEWB", "T02", 10, 13)))]
plant(T7, GAMES + _newb, nolog=("NEWB",))
for n in ("AJ", "AJC"):
    lg7 = FC.CHALLENGERS[n]["league"]
    _r7 = [row("n%d" % i, lg7, "2026-04-01", h, a) for i, (h, a) in enumerate((("NEWB", "T00"), ("T03", "NEWB"),
                                                                              ("T01", "T02")))]
    FC.attach(n, lg7, _r7, T7)
    _aj7 = [r["sig"]["aj"] for r in _r7]
    _fr7 = FC.def_fractions(MT.Tables(lg7, T7), WK)
    ck(len(_fr7) == 12 and "NEWB" not in _fr7 and _aj7[2]["def"] is not None,
       "%s: the planted Monday ranks 12 defences, not NEWB's (no yards), and a ranked pair gets a rank" % n, _fr7)
    ck(_aj7[0]["def"] is None and _aj7[1]["def"] is None and _aj7[0]["form"] and _aj7[1]["form"],
       "🔴 %s: a row with one defence not ranked (home or away) has no rank, though 12 others are ranked "
       "and both teams have a form" % n, _aj7)
    _x7 = [R.challenger_feat(n)(r, "total")[3] for r in _r7]
    ck(_x7[0] == 0.0 and _x7[1] == 0.0 and abs(_x7[2] - (_aj7[2]["def"] - 0.5) * 4.0) < 1e-12,
       "   ...so its total's index 3 is 0, not half a rank (the ranked pair's is (fraction - 0.5) x 4)", _x7)

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 THE INPUTS, MARKET BY MARKET (extend), AND NO NUMBER IS 0")
# ══════════════════════════════════════════════════════════════════════
X6 = row("x", "nfl", "2026-04-01", "T00", "T05", M=3.0, T=45.0)
X6["sig"].update(cl=(1.5, -2.0), wl=0.37, mc=6.0, aj={"form": (4.0, 47.0), "def": 0.7})
r9 = lambda v: [round(a, 9) for a in v]  # noqa: E731
for lg in NEW:
    x6 = dict(X6, lg=lg)
    base = {mk: FM.features(x6, mk) for mk in FM.MARKETS}
    cl, wl, mc = NEW[lg][0], NEW[lg][1], NEW[lg][2]
    eq({mk: r9(R.challenger_feat(cl)(x6, mk)) for mk in FM.MARKETS},
       {"spread": r9(base["spread"] + [0.15]), "moneyline": r9(base["moneyline"] + [0.15]),
        "total": r9(base["total"] + [-0.2])}, "🔴 %s: spread cl_m / 10, moneyline cl_m / 10, total cl_t / 10, "
       "appended" % cl)
    eq({mk: r9(R.challenger_feat(wl)(x6, mk)) for mk in FM.MARKETS},
       {"spread": r9(base["spread"] + [0.37]), "moneyline": r9(base["moneyline"] + [0.37]),
        "total": r9(base["total"])}, "🔴 %s: spread wl, moneyline wl, appended; totals unchanged" % wl)
    eq({mk: r9(R.challenger_feat(mc)(x6, mk)) for mk in FM.MARKETS},
       {"spread": r9([0.3] + base["spread"][1:]), "moneyline": r9([0.6] + base["moneyline"][1:]),
        "total": r9(base["total"])}, "🔴 %s: the first input is (capped - line) / 10 or capped / 10; totals "
       "unchanged" % mc)
    eq(r9(R.challenger_feat(mc)(x6, "spread", M=7.0))[0], -0.1, "   ...at the line being priced")
    nil = dict(x6, sig=dict(x6["sig"], cl=None, wl=None, mc=None, aj=None))
    nb = {mk: FM.features(nil, mk) for mk in FM.MARKETS}
    eq({n: {mk: R.challenger_feat(n)(nil, mk) for mk in FM.MARKETS} for n in NEW[lg]},
       {NEW[lg][0]: {mk: nb[mk] + [0.0] for mk in FM.MARKETS},
        NEW[lg][1]: {"spread": nb["spread"] + [0.0], "moneyline": nb["moneyline"] + [0.0], "total": nb["total"]},
        NEW[lg][2]: {"spread": [0.0] + nb["spread"][1:], "moneyline": [0.0] + nb["moneyline"][1:],
                     "total": nb["total"]},
        NEW[lg][3]: {"spread": nb["spread"][:2] + [0.0] + nb["spread"][3:],
                     "moneyline": nb["moneyline"][:2] + [0.0] + nb["moneyline"][3:],
                     "total": nb["total"][:2] + [0.0, 0.0] + nb["total"][4:]}},
       "🔴 %s: no number is 0 in every slot it fills" % lg)
eq({n: (c["league"], c["markets"], c["withdrawable"], c["files"], c["input"], c["registered_from"], c["on_merge"])
    for n, c in FC.CHALLENGERS.items() if n in NEW["nfl"] + NEW["ncaaf"]},
   {n: (lg, mk, False, (), None, "2026-11-02", True) for lg in NEW for n, mk in zip(NEW[lg], (
       ("spread", "total", "moneyline"), ("spread", "moneyline"), ("spread", "moneyline"),
       ("spread", "total", "moneyline")))},
   "🔴 CL, AJ (all three markets), WL, MC (spread, moneyline) per league; no file, no freshness input, "
   "never withdrawn, registered from the merge, no earlier than 2026-11-02")

# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 AGAINST ANOTHER CHAMPION: AJ, AJC, MC, MCC ONLY BESIDE ONE THAT ONLY APPENDS")
# ══════════════════════════════════════════════════════════════════════
APPENDS = {"E", "P", "AV", "AVC", "WX", "WXC", "IN", "RS", "RSC", "CL", "CLC", "WL", "WLC"}     # §3f, verbatim
_got, _want = {}, {}
for lg in NEW:
    _r = row("p", lg, "2026-04-01", "T00", "T05")
    _old = FM.CHAMPION[lg]
    try:
        for ch in [None] + [n for n, c in FC.CHALLENGERS.items() if c["league"] == lg]:
            FM.CHAMPION[lg] = ch
            for n in NEW[lg]:
                if n == ch:
                    continue
                _got[(lg, ch, n)] = FC.applies(n, _r)
                _want[(lg, ch, n)] = (n in ("CL", "CLC", "WL", "WLC")) or ch is None or ch in APPENDS
    finally:
        FM.CHAMPION[lg] = _old
eq(_got, _want, "🔴 CL, CLC, WL, WLC build against every champion; AJ, AJC, MC, MCC against none or E, P, AV, "
   "AVC, WX, WXC, IN, RS, RSC, CL, CLC, WL, WLC, else NOT APPLICABLE")
ck(not _got[("nfl", "AT", "AJ")] and not _got[("ncaaf", "T", "MCC")]
   and _got[("nfl", "IN", "MC")] and _got[("ncaaf", "WLC", "AJC")], "   e.g. AJ is NOT APPLICABLE beside AT, MCC "
   "beside T; MC builds beside IN, AJC beside WLC")

# ══════════════════════════════════════════════════════════════════════
section("8. 🔴 REGISTRATION: THE FIRST MONDAY AFTER THE MERGE, NO EARLIER THAN 2026-11-02")
# ══════════════════════════════════════════════════════════════════════
_days = ["2026-10-20", "2026-10-25"] + ["2026-10-%02d" % d for d in range(26, 32)] + ["2026-11-01", "2026-11-02"]
for n in NEW["nfl"] + NEW["ncaaf"]:
    eq([R.registration(n, T1, {n: d}) for d in _days] + [R.registration(n, T1, {n: None})],
       ["2026-11-02"] * 9 + ["2026-11-09", None],
       "🔴 %s: merged 10-20 to 11-01 -> 2026-11-02; merged Monday 11-02 -> 11-09; not merged -> none" % n)
G8 = tree()
shutil.copy(os.path.join(ROOT, "fb_challengers.py"), os.path.join(G8, "fb_challengers.py"))
_env = dict(os.environ, GIT_AUTHOR_DATE="2026-10-28T12:00:00Z", GIT_COMMITTER_DATE="2026-10-28T12:00:00Z")
for _a in (["init", "-q", "-b", "main"], ["add", "-A"],
           ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "t72"]):
    subprocess.run(["git"] + _a, cwd=G8, env=_env, capture_output=True, check=True)
eq({n: (R.merged_on(n, G8), R.registration(n, G8)) for n in NEW["nfl"] + NEW["ncaaf"]},
   {n: ("2026-10-28", "2026-11-02") for n in NEW["nfl"] + NEW["ncaaf"]},
   "🔴 each entry's line in the real fb_challengers.py is found by its merge-day needle")

# ══════════════════════════════════════════════════════════════════════
section("9. 🔴 league(): 13 CHALLENGERS A LEAGUE, EACH BUILT AND SCORED, alpha = 0.01 / 13")
# ══════════════════════════════════════════════════════════════════════
T9 = tree()
_g9 = league_games(TEAMS, 32, 75, start=datetime.date(2025, 3, 2))       # 192 games: fits need 150
plant(T9, _g9)
WANT13 = {"nfl": ["AJ", "AT", "AV", "CL", "E", "H", "IN", "MC", "RS", "S", "SM", "WL", "WX"],
          "ncaaf": ["AJC", "ATC", "AVC", "CLC", "HC", "MCC", "P", "RSC", "SMC", "T", "TS", "WLC", "WXC"]}
for lg in NEW:
    names = [n for n, c in FC.CHALLENGERS.items() if c["league"] == lg]
    eq(sorted(names), WANT13[lg], "🔴 %s: 13 challengers (T72 adds %s)" % (lg, ", ".join(NEW[lg])))
    rs = []
    for gid, day, h, a, n, hp, ap, _y in _g9:
        r = row(gid, lg, day, h, a, final=True, hs=hp, M=1.5 if hp % 2 else -2.5, T=44.5, pml=0.55,
                **{"as": ap})
        r["sig"]["neutral"] = 1.0 if n else 0.0
        rs.append(r)
    doc = R.league(lg, T9, NOW, rows=rs, added={n: "2025-01-01" for n in names})
    by = {x["name"]: x for x in doc["challengers"]}
    eq(sorted(by), WANT13[lg], "🔴 %s: league() reports all 13" % lg)
    ck(all(abs(x["alpha"] - 0.01 / 13) < 1e-15 and x["alpha"] < 0.01 / 9 for x in by.values()),
       "🔴 %s: every registered challenger's bar is 0.01 / 13, stricter than 0.01 / 9" % lg,
       {n: x.get("alpha") for n, x in by.items()})
    ck(all(by[n]["history"]["predictions"] > 0 for n in NEW[lg])
       and all(rs[-1]["sig"].get(k) is not None for k in ("cl", "wl", "mc", "aj")),
       "🔴 %s: league() builds %s's inputs itself and fits and scores each" % (lg, ", ".join(NEW[lg])),
       {n: by[n].get("history", {}).get("predictions") for n in NEW[lg]})

# ══════════════════════════════════════════════════════════════════════
section("10. 🔴 EVERY WARM-STARTED WEEKLY SOLVE GIVES ITS COLD ANSWER, EVEN AFTER A MONDAY WITH NO FINITE BEST")
# ══════════════════════════════════════════════════════════════════════
# `[2026-10-26]` A review found WL's resume blown up for good on a planted league: a first Monday whose
# non-neutral games were all home wins has no finite home edge (a ran to ~37), and the next Monday's
# warm start took a Newton step of ~-2e15 from where the fit was flat; every p was then exactly 0 and a
# never moved again (-2.2e15 on every later Monday, where a cold solve gave -0.005). §3 above only
# warm-started from a well-mixed Monday. The CLASS: a weekly() solve whose answer depends on the Monday
# it was warm-started from. So every solver fb_challengers drives through weekly() is read from its
# source, and each is replayed warm and cold over chains that open on such Mondays, both ways.
_src10 = open(os.path.join(ROOT, "fb_challengers.py"), encoding="utf-8").read()
_driven = sorted(set(re.findall(r"\bweekly\(.*,\s*(solve_\w+)\)\s*$", _src10, re.M)))
eq(_driven, ["solve_epa", "solve_resume", "solve_talent"], "every solver weekly() drives (E / P, WL / WLC, "
   "T / TS / MC / MCC) is replayed here; a new one must be added")
_teams10 = ["T%02d" % i for i in range(12)]


def chain(first, n_first, seed):
    """Saturday games for 13 weeks from 2025-08-23: in the first `n_first` weeks every non-neutral
    game ends `first` ("home" wins or "away" wins) and one is neutral; later weeks at random."""
    rr = random.Random(seed)
    out = []
    for k in range(13):
        day = (datetime.date(2025, 8, 23) + datetime.timedelta(weeks=k)).isoformat()
        sh = _teams10[:]
        rr.shuffle(sh)
        for i in range(0, 12, 2):
            hp, ap = float(rr.randint(3, 40)), float(rr.randint(3, 40))
            f = 0.0 if (k < n_first and i == 0) else 1.0
            if k < n_first and f:
                hp, ap = (max(hp, ap) + 1.0, min(hp, ap)) if first == "home" else (min(hp, ap), max(hp, ap) + 1.0)
            out.append((day, sh[i], sh[i + 1], f, hp, ap))
    return sorted(out)


def shapes(G, seed):
    """One planted chain in each solver's own shape."""
    rr = random.Random(seed)
    E = []
    for d, h, a, f, hp, ap in G:
        E += [(d, h, a, f, hp / 7.0 - 3.0, 60.0 + rr.randint(0, 9)), (d, a, h, 0.0, ap / 7.0 - 3.0, 61.0)]
    return {"solve_resume": G, "solve_talent": [(d, h, a, f, hp, ap, rr.uniform(-1, 1)) for d, h, a, f, hp, ap in G],
            "solve_epa": sorted(E)}


def gap10(u, v):
    """The largest difference between two solves' numbers (every scalar, every team's)."""
    out = 0.0 if u["teams"] == v["teams"] else float("inf")
    for k, x in v.items():
        if isinstance(x, dict):
            out = max([out] + [abs(u[k][t] - x[t]) for t in x])
        elif isinstance(x, float):
            out = max(out, abs(u[k] - x))
    return out


_weeks10 = [(datetime.date(2025, 8, 25) + datetime.timedelta(weeks=k)).isoformat() for k in range(13)]
for first, n_first, seed in (("home", 1, 5), ("away", 2, 6)):
    G10 = chain(first, n_first, seed)
    _flat = FC.solve_resume(FC.before(G10, _weeks10[0]), _weeks10[0])["a"]
    ck(abs(_flat) > 20 and all((g[4] > g[5]) == (first == "home") for g in G10 if g[3] and g[0] < _weeks10[n_first - 1]),
       "the planted chain opens with %d Monday(s) whose non-neutral games all went to the %s side: no finite home "
       "edge (a ran to %.1f)" % (n_first, first, _flat))
    for name, items in shapes(G10, seed).items():
        solve = getattr(FC, name)
        warm = FC.weekly(items, _weeks10, solve)
        worst = max(gap10(warm[wk], solve(FC.before(items, wk), wk)) for wk in _weeks10[n_first:])
        ck(worst < 1e-6, "🔴 %s, %s-side opening: warm-started every Monday after it gives the cold solve's every "
           "number to 1e-6" % (name, first), worst)
    _wl10, _bt = FC.weekly(G10, _weeks10, FC.solve_resume), []
    for wk in _weeks10[n_first:]:
        a10, B10 = direct_bt(FC.before(G10, wk), wk)
        _bt.append(gap10(_wl10[wk], {"a": a10, "B": B10, "teams": set(B10)}))
    ck(max(_bt) < 1e-6, "🔴 ...and WL's warm answer is the maximum itself: a direct Newton solve of §3f's likelihood "
       "to 1e-6, every later Monday", max(_bt))

# The fit the long step is checked against IS §3f's likelihood (the part that moves with a), at any a.
_G10 = [g[:3] + (0.0 if i % 5 == 0 else 1.0,) + ((g[4], g[4]) if i % 7 == 3 else g[4:])
        for i, g in enumerate(chain("home", 0, 7))]                   # some neutral sites, some ties
_rr10 = random.Random(8)
_w10 = [weight(g[0], _weeks10[-1]) for g in _G10]
_y10 = [1.0 if g[4] > g[5] else 0.0 if g[4] < g[5] else 0.5 for g in _G10]
_B10 = {t: _rr10.uniform(-1.5, 1.5) for t in _teams10}
_fit_bad = []
for a in (-6.0, -2.0, 0.0, 0.7, 3.0, 6.0):
    want = 0.0
    for wi, yi, g in zip(_w10, _y10, _G10):
        if g[3]:
            p = 1.0 / (1.0 + math.exp(-(a + _B10[g[1]] - _B10[g[2]])))
            want += wi * ((yi * math.log(p) if yi else 0.0) + ((1.0 - yi) * math.log(1.0 - p) if yi < 1 else 0.0))
    if abs(FC._home_fit(a, _G10, _w10, _y10, _B10) - want) > 1e-9 * max(1.0, abs(want)):
        _fit_bad.append((a, FC._home_fit(a, _G10, _w10, _y10, _B10), want))
ck(not _fit_bad and any(g[3] == 0.0 for g in _G10) and any(g[4] == g[5] for g in _G10 if g[3])
   and any(g[4] < g[5] for g in _G10 if g[3]),
   "🔴 the fit a long step must not worsen is sum(w (y log p + (1 - y) log(1 - p))) over the games with a home "
   "side (ties 0.5, neutral sites out), by hand at a from -6 to 6", _fit_bad)

note("rule 13: every contest number above is on planted games; none is computed on the real ones here")
