#!/usr/bin/env python3
"""T68 — SAM'S AVERAGES AND WEATHER AS FROZEN CHALLENGERS (research/fb_refit_spec.md §3b).

`[Sam, 2026-10-15]` "should be just apart of the model and system we have now,
learn to implement this as well". Planted schedules, planted weather files,
planted rows. ⛔ Reads no live data; writes only to temporary trees.

# @vacuity 🔴 a game on or after the row's Monday never enters its averages
#   file: fb_challengers.py
#   find:     cur = cur[:bisect.bisect_left(cur, (wk,))]
#   with:     cur = cur[:bisect.bisect_right(cur, (wk + "~",))]
#
# @vacuity 🔴 a top-up with fewer earlier games than needed keeps them all
#   file: fb_challengers.py
#   find:         cur = prev[max(0, len(prev) - (SAM_MIN_GAMES - len(cur))):] + cur if prev else cur
#   with:         cur = prev[len(prev) - (SAM_MIN_GAMES - len(cur)):] + cur if prev else cur
#
# @vacuity 🔴 fewer than 3 games are topped up from the earlier season
#   file: fb_challengers.py
#   find:     if len(cur) < SAM_MIN_GAMES:
#   with:     if False:
#
# @vacuity 🔴 a neutral site has no home edge
#   file: fb_challengers.py
#   find:     hf = 0.0 if r["sig"]["neutral"] else 1.0
#   with:     hf = 1.0
#
# @vacuity 🔴 sam_m is (PF_home + PA_away - PF_away - PA_home) / 2 + 1.5h
#   file: fb_challengers.py
#   find:     return ((h[0] + a[1] - a[0] - h[1]) / 2.0 + SAM_HOME * hf, (h[0] + a[1] + a[0] + h[1]) / 2.0)
#   with:     return ((h[0] - a[0]) / 2.0 + SAM_HOME * hf, (h[0] + a[1] + a[0] + h[1]) / 2.0)
#
# @vacuity 🔴 AV's total input is priced at the line given
#   file: fb_challengers.py
#   find:         return list(x) + [0.0 if t is None or T is None else (t - T) / 10.0]
#   with:         return list(x) + [0.0 if t is None or T is None else (t - r["T"]) / 10.0]
#
# @vacuity 🔴 an indoor game's wind is 0
#   file: fb_challengers.py
#   find:         out[str(gid)] = 0.0 if e.get("indoor") else (e.get("last") or {}).get("wind")
#   with:         out[str(gid)] = (e.get("last") or {}).get("wind", 9.0)
#
# @vacuity 🔴 E, P and T leave totals alone
#   file: fb_challengers.py
#   find:     if market not in c["markets"]:
#   with:     if False:
#
# @vacuity 🔴 a champion passes the total line through
#   file: fb_model.py
#   find:         x = fb_challengers.extend(CHAMPION[r["lg"]], r, market, x, M, T)
#   with:         x = fb_challengers.extend(CHAMPION[r["lg"]], r, market, x, M)
#
# @vacuity 🔴 the contest passes the total line through
#   file: fb_refit.py
#   find:     return lambda r, mk, M=None, T=None: FC.extend(name, r, mk, FM.features(r, mk, M=M, T=T), M, T)
#   with:     return lambda r, mk, M=None, T=None: FC.extend(name, r, mk, FM.features(r, mk, M=M, T=T), M)
#
# @vacuity 🔴 WX needs only weather-2026 to register
#   file: fb_refit.py
#   find:              for s in c.get("seasons", FM.SEASONS) for f in c["files"]]
#   with:              for s in FM.SEASONS for f in c["files"]]
#
# @vacuity 🔴 alpha counts every registered challenger in the league (7 and 7 since T69)
#   file: fb_challengers.py
#   find:     "WXC": {"league": "ncaaf", "what": "weather",
#   with:     "WXC": {"league": "nfl", "what": "weather",
#
# @vacuity 🔴 a champion's weather file is a hard input, not stored-only
#   file: freshness.py
#   find:     return bool(STORED_ONLY.search(r.get("path") or "")) and r.get("why") != CHAMPION_INPUT
#   with:     return bool(STORED_ONLY.search(r.get("path") or ""))
"""
import atexit
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
import fb_challengers as FC  # noqa: E402
import fb_model as FM  # noqa: E402
import fb_refit as R  # noqa: E402
import freshness as F  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])


def tree():
    t = tempfile.mkdtemp(prefix="fbt68-")
    TREES.append(t)
    return t


def put(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        json.dump(doc, fh)


def g(gid, day, home, away, hs, as_, neutral=False):
    return {"id": gid, "start": day + "T17:00:00Z", "home": home, "away": away, "neutral": neutral,
            "final": True, "home_score": hs, "away_score": as_}


def row(gid, lg, day, home, away, neutral=0.0, season=2026):
    return {"id": gid, "lg": lg, "season": season, "day": day, "home": home, "away": away, "final": False,
            "hs": None, "as": None, "M": 3.0, "T": 45.0, "pml": None,
            "sig": {"neutral": neutral, "dome": 1.0, "own_m": 5.0, "own_t": 47.0, "h2h_m": 9.0, "h2h_t": 50.0,
                    "form_m": 4.0, "form_t": 44.0, "def": 0.6, "poss": 0.1, "out": 2.0, "vac_h": 0.3,
                    "vac_a": 0.1, "epa_m": 6.5, "ppa_m": -2.5, "tal_m": 7.0}}


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 SAM'S AVERAGES, WORKED BY HAND (Monday 2026-09-28)")
# ══════════════════════════════════════════════════════════════════════
# AAA, 2026 before the Monday: 20-10, 17-24, 30-20 -> PF 67/3, PA 54/3.
# BBB, 2026 before the Monday: 21-14 (one game) -> topped up with its two
# LATEST 2025 games, 10-30 and 28-7 (not the earlier 3-3) -> PF 59/3, PA 51/3.
G26 = [g(1, "2026-09-07", "AAA", "XXX", 20, 10), g(2, "2026-09-14", "YYY", "AAA", 24, 17),
       g(3, "2026-09-21", "AAA", "ZZZ", 30, 20), g(4, "2026-09-20", "BBB", "WWW", 21, 14)]
G25 = [g(11, "2025-11-01", "BBB", "QQQ", 3, 3), g(12, "2025-12-01", "QQQ", "BBB", 30, 10),
       g(13, "2025-12-20", "BBB", "RRR", 28, 7)]
LATE = [g(21, "2026-09-28", "AAA", "BBB", 70, 0), g(22, "2026-09-30", "BBB", "AAA", 0, 63)]
T1 = tree()


def plant(t, late=()):
    put(t, "data/nfl/latest/schedule-2026.json.gz", {"season": 2026, "games": G26 + list(late)})
    put(t, "data/nfl/latest/schedule-2025.json.gz", {"season": 2025, "games": G25})


def sam(t, *rows_):
    rs = [dict(r, sig=dict(r["sig"])) for r in rows_]
    FC.attach("AV", "nfl", rs, t)
    return [(r["sig"]["sam_m"], r["sig"]["sam_t"]) for r in rs]


plant(T1)
PF_H, PA_H, PF_A, PA_A = Fraction(67, 3), Fraction(54, 3), Fraction(59, 3), Fraction(51, 3)
WANT_M = (PF_H + PA_A - PF_A - PA_H) / 2
WANT_T = (PF_H + PA_A + PF_A + PA_H) / 2
X = row("x", "nfl", "2026-10-01", "AAA", "BBB")
N = row("n", "nfl", "2026-10-01", "AAA", "BBB", neutral=1.0)
U = row("u", "nfl", "2026-10-01", "AAA", "NEW")
got = sam(T1, X, N, U)
ck(abs(got[0][0] - float(WANT_M + Fraction(3, 2))) < 1e-9 and abs(got[0][1] - float(WANT_T)) < 1e-9,
   "🔴 sam_m = (PF_h + PA_a - PF_a - PA_h)/2 + 1.5 and sam_t = (PF_h + PA_a + PF_a + PA_h)/2, by hand "
   "(%.4f, %.4f), BBB topped up to 3 from its latest 2025 games" % (WANT_M + Fraction(3, 2), WANT_T), got[0])
ck(abs(got[1][0] - float(WANT_M)) < 1e-9 and abs(got[1][1] - float(WANT_T)) < 1e-9,
   "🔴 a neutral site has no 1.5", got[1])
eq(got[2], (None, None), "🔴 a team with no earlier game at all has no number")
plant(T1, LATE)
eq(sam(T1, X)[0], got[0], "🔴 games on (09-28) and after (09-30) the row's Monday never enter its averages")
# `[2026-10-15]` Cowork's review: two earlier games and a need of three kept only the LAST.
TG = {(2025, "TWO"): [("2025-11-01", 10.0, 20.0), ("2025-12-01", 30.0, 40.0)],
      (2025, "FOUR"): [("2025-10-%02d" % (i + 1), 10.0 * i, 10.0 * i) for i in range(4)]}
eq([FC.sam_rates(TG, 2026, t, "2026-09-28") for t in ("TWO", "FOUR")], [(20.0, 30.0), (20.0, 20.0)],
   "🔴 a top-up keeps every earlier-season game when there are fewer than needed; 3+ keep only the latest 3")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 AV APPENDS ONE INPUT; WX CHANGES TOTALS ONLY; THE LINE PASSES THROUGH")
# ══════════════════════════════════════════════════════════════════════
A = dict(X, sig=dict(X["sig"], sam_m=2.5, sam_t=38.5))
for mk in FM.MARKETS:
    base, av = FM.features(A, mk), R.challenger_feat("AV")(A, mk)
    ck(len(av) == len(base) + 1 and av[:-1] == base,
       "🔴 AV %s: the champion's inputs byte-identical, exactly one appended" % mk, (base, av))
eq([round(R.challenger_feat("AV")(A, mk)[-1], 9) for mk in ("spread", "moneyline", "total")],
   [-0.05, 0.25, -0.65], "🔴 AV: (sam_m - line)/10, sam_m/10, (sam_t - line)/10")
alt = R.challenger_feat("AV")(A, "total", T=40.0)
ck(round(alt[-1], 9) == -0.15 and alt[:-1] == FM.features(A, "total", T=40.0),
   "🔴 extend(..., T=alt) prices AV's total input at the alt line (38.5 - 40)/10", alt)
W1 = tree()
put(W1, "data/nfl/latest/weather-2026.json.gz", {"games": {
    "g1": {"last": {"wind": 14.0}, "first": {"wind": 9.0}}, "g2": {"indoor": True, "last": {"wind": 20.0}},
    "g3": {"first": {"wind": 11.0}}}})
WR = [row(i, "nfl", "2026-10-18", "AAA", "BBB") for i in ("g1", "g2", "g3", "g4")]
FC.attach("WX", "nfl", WR, W1)
eq([R.challenger_feat("WX")(r, "total")[-1] for r in WR], [1.4, 0.0, 0.0, 0.0],
   "🔴 WX: the last forecast's wind/10; indoor, no last and no entry give 0")
ck(all(R.challenger_feat("WX")(r, mk) == FM.features(r, mk) for r in WR for mk in ("spread", "moneyline")),
   "🔴 WX leaves spread and moneyline byte-identical")
ck(R.challenger_feat("WX")(WR[0], "total", T=40.0) == FM.features(WR[0], "total", T=40.0) + [1.4],
   "🔴 ...and its total is the champion's at the alt line, plus the wind")
_old = dict(FM.CHAMPION)
try:
    FM.CHAMPION.update(nfl="AV")
    ck(FM.features(A, "total", T=40.0)[-1] == alt[-1] and len(FM.features(A, "total")) == len(alt),
       "🔴 as CHAMPION, AV's alt total is priced at its own line (fb_model.features passes T)")
finally:
    FM.CHAMPION.clear()
    FM.CHAMPION.update(_old)

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 E, P, T, S AND TS ARE BYTE-IDENTICAL TO BEFORE T68")
# ══════════════════════════════════════════════════════════════════════
# ⛔ Recorded from main's code (b6147b86b) before this change, on this row.
BEFORE = {"E": {"spread": [0.2, 0.6, 0.1, 1.0, 0.666666667, 0.0, 1.0, 0.2, 0.35],
                "total": [0.2, 0.5, -0.1, 0.4, 0.0, 1.0, 0.4],
                "moneyline": [0.5, 0.9, 0.4, 1.0, 0.666666667, 0.0, 1.0, 0.2, 0.65]},
          "P": {"spread": [0.2, 0.6, 0.1, 1.0, 0.666666667, 0.0, 1.0, -0.55], "total": [0.2, 0.5, -0.1, 0.4, 0.0, 1.0],
                "moneyline": [0.5, 0.9, 0.4, 1.0, 0.666666667, 0.0, 1.0, -0.25]},
          "T": {"spread": [0.4, 0.6, 0.1, 1.0, 0.666666667, 0.0, 1.0], "total": [0.2, 0.5, -0.1, 0.4, 0.0, 1.0],
                "moneyline": [0.7, 0.9, 0.4, 1.0, 0.666666667, 0.0, 1.0]},
          "S": {"spread": [0.2, 0.1, 1.0, 0.666666667, 0.0, 1.0], "total": [0.2, -0.1, 0.4, 0.0, 1.0],
                "moneyline": [0.5, 0.4, 1.0, 0.666666667, 0.0, 1.0]},
          "TS": {"spread": [0.4, 0.0, 1.0], "total": [0.2, 0.0, 1.0], "moneyline": [0.7, 0.0, 1.0]}}
NOW_ = {}
for n in BEFORE:
    r = row("x", FC.CHALLENGERS[n]["league"], "2026-10-25", "AAA", "CCC")
    NOW_[n] = {mk: [round(v, 9) for v in R.challenger_feat(n)(r, mk)] for mk in FM.MARKETS}
eq(NOW_, BEFORE, "🔴 every earlier challenger's inputs, all three markets, unchanged")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 REGISTRATION, ALPHA AND FRESHNESS")
# ══════════════════════════════════════════════════════════════════════
G1 = tree()
put(G1, "data/nfl/latest/weather-2026.json.gz", {"games": {}})
env = dict(os.environ, GIT_AUTHOR_DATE="2026-10-16T12:00:00Z", GIT_COMMITTER_DATE="2026-10-16T12:00:00Z")
for a in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "w"]):
    subprocess.run(["git"] + a, cwd=G1, env=env, capture_output=True)
eq([R.registration("WX", G1), R.registration("AV", G1)], ["2026-10-19", "2026-10-19"],
   "🔴 WX registers on weather-2026 alone (no 2025 forecasts exist); AV needs no file")


def res(name):
    return {"name": name, "registered": "2026-10-19", "withdrawn": False,
            "scored": {"predictions": 300, "mean_d": 0.05, "p": 0.0021}}


al = {lg: R.verdicts([res(n) for n, c in FC.CHALLENGERS.items() if c["league"] == lg])[0]["alpha"]
      for lg in ("nfl", "ncaaf")}
# `[Sam, 2026-10-15]` ~~0.01/4 and 0.01/5~~: T69 (§3c) adds IN, AT, RS and ATC, RSC.
# `[Sam, 2026-10-16]` ~~0.01/8 and 0.01/8~~: T71 (§3e) adds SM and SMC.
# `[Sam, 2026-10-26]` ~~0.01/9 and 0.01/9~~: T72 (§3f) adds CL, WL, MC, AJ and CLC, WLC, MCC, AJC.
ck(abs(al["nfl"] - 0.01 / 13) < 1e-12 and abs(al["ncaaf"] - 0.01 / 13) < 1e-12,
   "🔴 alpha: 0.01/13 in the NFL (E, S, AV, WX, IN, AT, RS, H, SM, CL, WL, MC, AJ) and 0.01/13 in college "
   "(P, T, TS, AVC, WXC, ATC, RSC, HC, SMC, CLC, WLC, MCC, AJC)", al)
eq((F.champion_inputs("nfl", {"nfl": "WX"}), F.champion_inputs("ncaaf", {"ncaaf": "WXC"}),
    F.champion_inputs("nfl", {"nfl": "AV"})),
   ([("weather-{s}.json.gz", "possession")], [("weather-{s}.json.gz", "possession")], []),
   "🔴 a champion WX reads its weather file on the daily deadline; AV adds no row (like S)")
_w = "x/data/nfl/latest/weather-2026.json.gz"
ck(not F.stored_only({"path": _w, "why": F.CHAMPION_INPUT}) and F.stored_only({"path": _w, "why": "Stored only"}),
   "🔴 ...and once a champion reads it, the weather file is a hard input like E's, not stored-only")
