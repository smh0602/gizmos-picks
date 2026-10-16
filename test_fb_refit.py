#!/usr/bin/env python3
"""T65 — THE FOOTBALL GAME MODEL'S WEEKLY CONTEST (research/fb_refit_spec.md).
Planted trees and a pinned clock only. ⛔ Reads no live data, writes nothing
under data/ or picks/; the WINS branch is pushed to a planted bare repo.

# @vacuity 🔴 a challenger's input never reads an entry or game dated on or after the row's Monday
#   file: fb_challengers.py
#   find:         while j < len(items) and items[j][0] < wk:
#   with:         while j < len(items) and items[j][0] <= wk:
#
# @vacuity 🔴 the EPA/PPA solve matches a direct solve
#   file: fb_challengers.py
#   find:             D[t] = sum(w[i] * (s["base"] + s["hfa"] * E[i][3] + O[E[i][1]] - E[i][4]) for i in ix) / (
#   with:             D[t] = sum(w[i] * (s["base"] + s["hfa"] * E[i][3] + O[E[i][1]] - 0.9 * E[i][4]) for i in ix) / (
#
# @vacuity 🔴 the talent-term solve matches a direct solve
#   file: fb_challengers.py
#   find:         s["beta"] = (sum(wi * g[6] * (res(g) - s["hfa"] * g[3]) for wi, g in zip(w, G)) / sw_z
#   with:         s["beta"] = (sum(wi * g[6] * (res(g)) for wi, g in zip(w, G)) / sw_z
#
# @vacuity 🔴 a week before the registration Monday never counts toward the verdict
#   file: fb_refit.py
#   find:                 (scored if wk >= start else hist).append((loss(a[gid][0], y), loss(p_x, y), gid))
#   with:                 (scored if True else hist).append((loss(a[gid][0], y), loss(p_x, y), gid))
#
# @vacuity 🔴 registration is the later of 2026-10-19 and the data's first Monday
#   file: fb_refit.py
#   find:     return max(start, monday_on_or_after(day)) if day else None
#   with:     return monday_on_or_after(day) if day else None
#
# @vacuity 🔴 299 scored predictions is NOT YET MEASURABLE
#   file: fb_refit.py
#   find:         elif s["predictions"] < MIN_SCORED:
#   with:         elif s["predictions"] < MIN_SCORED - 1:
#
# @vacuity 🔴 alpha is 0.01 / the registered, not withdrawn count
#   file: fb_refit.py
#   find:         x["alpha"] = ALPHA / k if k else None
#   with:         x["alpha"] = ALPHA
#
# @vacuity 🔴 a challenger worse on its history is WITHDRAWN and never scored
#   file: fb_refit.py
#   find:     out["scored"] = test([] if out["withdrawn"] else scored)
#   with:     out["scored"] = test(scored)
#
# @vacuity 🔴 a snapshot pulled before the row's Monday never enters the line-move count
#   file: fb_refit.py
#   find:                      if D._near(d, k) and pulled >= wk + "T00:00:00Z")
#   with:                      if D._near(d, k))
#
# @vacuity 🔴 never a second champion branch while one exists
#   file: fb_refit.py
#   find:     if have:
#   with:     if False:
#
# @vacuity 🔴 the branch's only change is the CHAMPION line
#   file: fb_refit.py
#   find:             fh.write(set_champion(src, lg, name))
#   with:             fh.write(set_champion(src, lg, name) + "\n")
#
# @vacuity 🔴 the branch never touches main
#   file: fb_refit.py
#   find:         git("push", "origin", "%s:refs/heads/%s" % (branch, branch), cwd=tmp)
#   with:         git("push", "origin", "%s:refs/heads/main" % branch, cwd=tmp)
#
# @vacuity 🔴 CHAMPION None reads none of the challengers' files
#   file: fb_model.py
#   find:     if CHAMPION.get(lg):                 # ⛔ None reads none of the challengers' files
#   with:     if True:                 # ⛔ None reads none of the challengers' files
#
# @vacuity 🔴 a named champion adds its input
#   file: fb_model.py
#   find:         x = fb_challengers.extend(CHAMPION[r["lg"]], r, market, x, M, T)
#   with:         pass
#
# @vacuity 🔴 ...and "+game-<name>" to the card's method
#   file: card_fb.py
#   find:     return "+game-%s" % model["champion"] if (model or {}).get("champion") else ""
#   with:     return ""
#
# @vacuity 🔴 ...and a freshness row for the file behind it
#   file: freshness.py
#   find:     for fname, due in champion_inputs(league):
#   with:     for fname, due in []:
#
# @vacuity 🔴 the Monday email shows the section
#   file: status.py
#   find:     L += ["", "## Is the football model learning?"] + ["- " + refit_summary(doc, name, now)
#   with:     L += [] + [""
#
# @vacuity 🔴 a WINS goes under "Needs you"
#   file: status.py
#   find:     needs = [f["what"] for f in broken] + [w[0] for w in won]
#   with:     needs = [f["what"] for f in broken]
#
# @vacuity 🔴 T66: S keeps the champion's inputs without head-to-head and signal 9
#   file: fb_challengers.py
#   find: KEEP = {"S": {"spread": (0, 2, 3, 4, 5, 6), "moneyline": (0, 2, 3, 4, 5, 6), "total": (0, 2, 3, 4, 5)},
#   with: KEEP = {"S": {"spread": (0, 1, 2, 3, 4, 5, 6), "moneyline": (0, 2, 3, 4, 5, 6), "total": (0, 2, 3, 4, 5)},
#
# @vacuity 🔴 T66: TS keeps only the line, neutral and dome
#   file: fb_challengers.py
#   find:         "TS": {"spread": (0, 5, 6), "moneyline": (0, 5, 6), "total": (0, 4, 5)}}
#   with:         "TS": {"spread": (0, 5, 6), "moneyline": (0, 5, 6), "total": (0, 3, 4, 5)}}
#
# @vacuity 🔴 T66: TS's first spread and moneyline input is T's talent margin
#   file: fb_challengers.py
#   find:         if name == "S" or market == "total":
#   with:         if True:
#
# @vacuity 🔴 T66: S, which reads no file, is registered on its Monday
#   file: fb_refit.py
#   find:         return start
#   with:         return None
#
# @vacuity 🔴 T66: a champion with no file of its own has no input row
#   file: freshness.py
#   find:     return [inp] if inp else []          # T66's S reads no file of its own
#   with:     return [inp]          # T66's S reads no file of its own
#
# @vacuity 🔴 T71: SM's spread input is (predicted margin - line) / 10
#   file: fb_challengers.py
#   find:         return [(0.0 if m is None or M is None else (m - M) / 10.0) if market == "spread" else
#   with:         return [(0.0 if m is None or M is None else m / 10.0) if market == "spread" else
#
# @vacuity 🔴 T71: SM's number is the score model's own predicted margin AND total
#   file: fb_challengers.py
#   find:         got = {id(p["row"]): (p["margin"], p["total"]) for p in done}
#   with:         got = {id(p["row"]): (p["margin"], p["margin"]) for p in done}
#
# @vacuity 🔴 T71: the merge day comes from main's first-parent line, not the PR's own commit
#   file: fb_refit.py
#   find:     r = subprocess.run(["git", "log", "--first-parent", "--format=%cs", "-S", needle, "--", "fb_challengers.py"],
#   with:     r = subprocess.run(["git", "log", "--format=%cs", "-S", needle, "--", "fb_challengers.py"],
#
# @vacuity 🔴 T71: registration is the later of 2026-10-19 and the Monday after the merge day
#   file: fb_refit.py
#   find:         return max(start, monday_on_or_after(after)) if after else None
#   with:         return start
#
# @vacuity 🔴 T71: ...AFTER it: a Monday merge counts from the next Monday
#   file: fb_refit.py
#   find:         after = (datetime.date.fromisoformat(merged) + datetime.timedelta(days=1)).isoformat() if merged else None
#   with:         after = merged
#
# @vacuity 🔴 T71: a challenger that cannot be built against the champion is NOT APPLICABLE, never a crash
#   file: fb_challengers.py
#   find:     return all(max(KEEP[name][mk]) < len(FM.features(r, mk)) for mk in CHALLENGERS[name]["markets"])
#   with:     return True
#
# @vacuity 🔴 T71: ...and league() reports it so instead of fitting it
#   file: fb_refit.py
#   find:         if reg and rows and not FC.applies(n, rows[0]):
#   with:         if False:
#
# @vacuity 🔴 T71: SM / SMC's numbers are pinned: the matchup layer
#   file: fb_score_model.py
#   find:             home = b[0] + sum(c * x for c, x in zip(beta, f[0]))
#   with:             home = b[0]
#
# @vacuity 🔴 T71: ...and what fb_matchups counts as passing yards
#   file: fb_matchups.py
#   find:                 c["pass_yds"] += float(g.get("pass_yds") or 0)
#   with:                 c["pass_yds"] += float(g.get("pass_yds") or 0) * (pos == "QB")
#
# @vacuity 🔴 T71: ...and what fb_matchups counts as rushing yards
#   file: fb_matchups.py
#   find:                 c["rush_yds"] += float(g.get("rush_yds") or 0)
#   with:                 c["rush_yds"] += float(g.get("rush_yds") or 0) * (pos == "RB")
#
# @vacuity 🔴 T71: ...and carries
#   file: fb_matchups.py
#   find:                 c["rush_car"] += float(g.get("car") or 0)
#   with:                 c["rush_car"] += float(g.get("car") or 0) * (pos == "RB")
#
# @vacuity 🔴 T71: ...and plays (pace)
#   file: fb_matchups.py
#   find:             c["plays"] = c["pass_att"] + c["rush_car"]
#   with:             c["plays"] = c["pass_att"]
#
# @vacuity 🔴 T71: league() itself builds SM's input
#   file: fb_refit.py
#   find:         FC.attach(n, lg, rows, root)
#   with:         FC.attach(n, lg, rows, root) if n != "SM" else None
#
# @vacuity 🔴 T71: the Monday email says NOT APPLICABLE in words
#   file: status.py
#   find:             "NOT APPLICABLE": "not applicable against the current champion (how it should read is yours "
#   with:             "NOT APPLICABLE ": "not applicable against the current champion (how it should read is yours "
#
# @vacuity 🔴 T71: the Monday job checks out full history
#   file: .github/workflows/fb-refit.yml
#   find:           fetch-depth: 0
#   with:           fetch-depth: 1
#
# @vacuity 🔴 a report over 8 days old is said, and DEGRADED in health
#   file: watchdog.py
#   find:         if doc and (age is None or age > FB_REFIT_STALE_DAYS):
#   with:         if doc and (age is None or age > 99):
"""
import atexit
import datetime
import gzip
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
import card_fb  # noqa: E402
import fb_challengers as FC  # noqa: E402
import fb_model as FM  # noqa: E402
import fb_refit as R  # noqa: E402
import freshness as F  # noqa: E402
import status as S  # noqa: E402
import watchdog as W  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 11, 2, 11, 17, tzinfo=UTC)     # a Monday
TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])


def tree():
    t = tempfile.mkdtemp(prefix="fbrefit-")
    TREES.append(t)
    return t


def put(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with (gzip.open(p, "wt") if p.endswith(".gz") else open(p, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


def row(gid, lg, day, home, away, season=2026, **kw):
    return dict({"id": gid, "lg": lg, "season": season, "day": day, "home": home, "away": away,
                 "final": True, "hs": 24, "as": 17, "M": 3.0, "T": 44.5, "pml": 0.6,
                 "sig": {"neutral": 0.0, "dome": 0.0, "own_m": 2.0, "own_t": 45.0, "h2h_m": None,
                         "h2h_t": None, "form_m": None, "form_t": None, "def": None, "poss": None,
                         "out": None, "vac_h": None, "vac_a": None}}, **kw)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 POINT IN TIME: E, P AND T READ NOTHING DATED ON OR AFTER THE ROW'S MONDAY")
# ══════════════════════════════════════════════════════════════════════
T1 = tree()
TEAMS = ["AAA", "BBB", "CCC", "DDD"]
GAMES = [("g%d" % i, "2026-09-%02d" % (1 + 2 * i), TEAMS[i % 4], TEAMS[(i + 1) % 4]) for i in range(10)]
LATE = [("late1", "2026-09-28", "AAA", "CCC"), ("late2", "2026-09-30", "BBB", "DDD")]  # on / after Monday 09-28


def plant(t, games):
    late = lambda g: g.startswith("late")  # noqa: E731
    for lg in ("nfl", "ncaaf"):
        put(t, "data/%s/latest/schedule-2026.json.gz" % lg, {"season": 2026, "games": [
            {"id": g, "start": d + "T17:00:00Z", "home": h, "away": a, "neutral": False, "final": True,
             "home_score": 70 if late(g) else 20, "away_score": 13} for g, d, h, a in games]})
    by_team = {}
    for g, _d, h, a in games:
        for o, dfn in ((h, a), (a, h)):
            by_team.setdefault(dfn, {})[g] = {"opp": o, "plays": 60,
                                              "epa_per_play": (9.0 if late(g) else 0.1) * (1 if o == h else -1)}
    put(t, "data/nfl/latest/def-epa-2026.json.gz", {"by_team": by_team})
    put(t, "data/ncaaf/latest/ppa-2026.json.gz", {"games": {
        g: {h: {"ppa_sum": 540.0 if late(g) else 6.0, "plays_with_ppa": 60},
            a: {"ppa_sum": -3.0, "plays_with_ppa": 60}} for g, _d, h, a in games}})
    put(t, "data/ncaaf/latest/talent-2026.json.gz", {"season": 2026, "teams": {
        "AAA": 900, "BBB": 700, "CCC": 600, "DDD": 500}})


def inputs(t):
    out = {}
    for name, lg in (("E", "nfl"), ("P", "ncaaf"), ("T", "ncaaf")):
        rs = [row("x", lg, "2026-10-01", "AAA", "CCC")]          # Monday 2026-09-28
        FC.attach(name, lg, rs, t)
        out[name] = rs[0]["sig"][FC.CHALLENGERS[name]["key"]]
    return out


plant(T1, GAMES)
before = inputs(T1)
plant(T1, GAMES + LATE)
after = inputs(T1)
for n in ("E", "P", "T"):
    ck(before[n] is not None and abs(before[n] - after[n]) < 1e-12,
       "🔴 %s's input for a 10-01 row is the same with games dated 09-28 and 09-30 added" % n,
       "before %r after %r" % (before[n], after[n]))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 BOTH SOLVERS MATCH A DIRECT SOLVE ON A PLANTED LEAGUE TO 1e-6")
# ══════════════════════════════════════════════════════════════════════
rng = random.Random(65)
WK = "2026-10-05"
E = [("2026-09-%02d" % (1 + i % 28), TEAMS[i % 4], TEAMS[(i + 1 + i // 4) % 4],
      float(i % 2), rng.gauss(0, 0.2), 50 + i) for i in range(40)]
E = sorted(e for e in E if e[1] != e[2])
s = FC.solve_epa(E, WK)
par = ["base", "hfa"] + ["O" + t for t in TEAMS] + ["D" + t for t in TEAMS]
k = len(par)
A, b = [[0.0] * k for _ in range(k)], [0.0] * k
for e in E:
    x = [1.0, e[3]] + [1.0 if e[1] == t else 0.0 for t in TEAMS] + [-1.0 if e[2] == t else 0.0 for t in TEAMS]
    w = FC.weight(e[0], WK)
    for i in range(k):
        b[i] += w * x[i] * e[4]
        for j in range(k):
            A[i][j] += w * x[i] * x[j]
for i in range(2, k):
    A[i][i] += 1.0
direct = FM._solve(A, b)
got = [s["base"], s["hfa"]] + [s["O"][t] for t in TEAMS] + [s["D"][t] for t in TEAMS]
eq(max(abs(a - c) for a, c in zip(got, direct)) < 1e-6, True, "🔴 the EPA/PPA solve matches the direct solve")
m = FC.epa_margin(s, "AAA", "BBB", 0.0)
ck(abs(m - (direct[1] + direct[2] - direct[7] - direct[3] + direct[6]) * (sum(e[5] for e in E) / len(E))) < 1e-6,
   "   ...and its margin is (edge + Off_h - Def_a - Off_a + Def_h) x the mean plays", m)

G = sorted((e[0], e[1], e[2], e[3], 20 + rng.gauss(0, 7), 20 + rng.gauss(0, 7), rng.gauss(0, 1)) for e in E)
s = FC.solve_talent(G, WK)
par = ["hfa", "beta"] + TEAMS
k = len(par)
A, b = [[0.0] * k for _ in range(k)], [0.0] * k
for g in G:
    x = [g[3], g[6]] + [1.0 if g[1] == t else -1.0 if g[2] == t else 0.0 for t in TEAMS]
    w = FC.weight(g[0], WK)
    for i in range(k):
        b[i] += w * x[i] * (g[4] - g[5])
        for j in range(k):
            A[i][j] += w * x[i] * x[j]
for i in range(2, k):
    A[i][i] += 1.0
direct = FM._solve(A, b)
got = [s["hfa"], s["beta"]] + [s["R"][t] for t in TEAMS]
eq(max(abs(a - c) for a, c in zip(got, direct)) < 1e-6, True, "🔴 the talent-term solve matches the direct solve")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE VERDICT: REGISTRATION, 300, ALPHA, WITHDRAWAL")
# ══════════════════════════════════════════════════════════════════════


class Planted:
    def __init__(self, preds):
        self.preds = preds

    def predictions(self, mk, keep=None):
        return self.preds.get(mk, {})


def preds(weeks, p, n_games=40, start=0):
    out = {}
    for i in range(n_games):
        wk = weeks[i % len(weeks)]
        y = 1 if (i * 7) % 10 < 6 else 0
        out["g%d" % (start + i)] = (p(y), y, wk, None)
    return out


HIST, LIVE = ["2026-10-05", "2026-10-12"], ["2026-10-19", "2026-10-26"]
champ = Planted({mk: dict(preds(HIST, lambda y: 0.6), **preds(LIVE, lambda y: 0.6, start=40))
                 for mk in ("spread", "moneyline")})
good = Planted({mk: dict(preds(HIST, lambda y: 0.75 if y else 0.35), **preds(LIVE, lambda y: 0.75 if y else 0.35,
                                                                             start=40))
                for mk in ("spread", "moneyline")})
c = R.contest([], champ, "P", "2026-10-19", "2026-10-19", fits=good)
eq((c["history"]["predictions"], c["scored"]["predictions"]), (80, 80),
   "🔴 weeks before 2026-10-19 are history; only weeks from it on are scored")
eq([R.registration("P", T1, {"P": d}) for d in ("2026-10-01", "2026-10-21", None)],
   ["2026-10-19", "2026-10-26", None],
   "🔴 registration: the later of 2026-10-19 and the first Monday on or after the data's day")
bad = Planted({mk: dict(preds(HIST, lambda y: 0.3 if y else 0.7), **preds(LIVE, lambda y: 0.75 if y else 0.35,
                                                                          start=40))
               for mk in ("spread", "moneyline")})
w = R.contest([], champ, "T", "2026-10-19", "2026-10-19", fits=bad)
ck(w["withdrawn"] and w["scored"]["predictions"] == 0 and w["history"]["p_wrong_way"] < 0.05,
   "🔴 a challenger worse on its history (p < 0.05 the wrong way) is WITHDRAWN and never scored",
   (w["withdrawn"], w["history"], w["scored"]["predictions"]))
e = R.contest([], champ, "E", "2026-10-19", "2026-10-19", fits=bad)
ck(not e["withdrawn"], "   ...and E, registered before any result, is never withdrawn")


def scored(n, mean, p):
    return {"name": "X", "registered": "2026-10-19", "withdrawn": False,
            "scored": {"predictions": n, "mean_d": mean, "p": p}}


v = R.verdicts([scored(299, 0.05, 1e-9), scored(300, 0.05, 0.004), dict(scored(300, 0.05, 0.001), withdrawn=True),
                {"registered": None}])
eq([x.get("verdict") for x in v], ["NOT YET MEASURABLE", "WINS", "WITHDRAWN", None],
   "🔴 299 scored is NOT YET MEASURABLE; 300 at p 0.004 WINS when alpha is 0.01 / 2")
eq(v[1]["alpha"], 0.005, "🔴 alpha = 0.01 / the two registered, not withdrawn")
eq(R.verdicts([scored(300, 0.05, 0.004), scored(300, 0.05, 0.004), scored(300, 0.05, 0.004)])[0]["verdict"],
   "NOT YET", "   ...and with three registered, p 0.004 is NOT YET (alpha 0.0033)")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 LINE MOVES: ONLY SNAPSHOTS PULLED ON OR AFTER THE ROW'S MONDAY")
# ══════════════════════════════════════════════════════════════════════
T4 = tree()


def snap(day, pulled, pt, total, mlh):
    put(T4, "data/nfl/%s/gamelines/%s.json.gz" % (day, pulled[11:13] + pulled[14:16]), {
        "pulled_at": pulled, "games": [{"home": "Seattle Seahawks", "away": "New England Patriots",
                                        "commence": "2026-10-08T00:15:00Z", "books": {"fanduel": {
            "spreads": {"Seattle Seahawks": {"pt": pt, "px": -110}, "New England Patriots": {"pt": -pt, "px": -110}},
            "totals": {"Over": {"pt": total, "px": -110}, "Under": {"pt": total, "px": -110}},
            "h2h": {"Seattle Seahawks": mlh, "New England Patriots": 120}}}}]})


snap("2026-10-04", "2026-10-04T15:00:00Z", -9.0, 50.0, -400)   # Sunday: before the Monday cut
snap("2026-10-05", "2026-10-05T01:00:00Z", -3.0, 44.0, -150)
snap("2026-10-07", "2026-10-07T15:00:00Z", -4.5, 45.5, -130)


class Lean:
    def model(self, wk, mk):        # p 0.88 everywhere: the lean is home / over
        return {"mu": [0.0] * 8, "sd": [1.0] * 8, "w": [2.0] + [0.0] * 8}


lm = R.line_moves([row("x", "nfl", "2026-10-07", "SEA", "NE")], Lean(), R.snapshots("nfl", T4))
eq((lm["games"], lm["spread"]["toward"], lm["total"]["toward"], lm["moneyline"]["against"]), (1, 1, 1, 1),
   "🔴 from 10-05 01:00 to 10-07: the spread and total moved toward the lean, and the moneyline")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 A WINS PUSHES ONE BRANCH, ONLY THE CHAMPION LINE, NEVER MAIN")
# ══════════════════════════════════════════════════════════════════════
T5 = tree()
ORIGIN, WORK = os.path.join(T5, "origin.git"), os.path.join(T5, "work")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main"]


def sh(*a, cwd=None):
    return subprocess.run(GIT + list(a), capture_output=True, text=True, cwd=cwd, check=True).stdout


sh("init", "--bare", ORIGIN)
sh("clone", ORIGIN, WORK)
shutil.copy(os.path.join(ROOT, "fb_model.py"), os.path.join(WORK, "fb_model.py"))
sh("add", "fb_model.py", cwd=WORK)
sh("commit", "-m", "base", cwd=WORK)
sh("push", "origin", "HEAD:refs/heads/main", cwd=WORK)
main0 = sh("rev-parse", "main", cwd=ORIGIN).strip()
got = R.push_branch("nfl", "E", "2026-11-02", WORK)
heads = sh("for-each-ref", "--format=%(refname:short)", "refs/heads", cwd=ORIGIN).split()
diff = [ln for ln in sh("diff", "main", "fb/champion-nfl-E-2026-11-02", cwd=ORIGIN).splitlines()
        if ln[:1] in "+-" and ln[:3] not in ("+++", "---")]
eq(got, ("fb/champion-nfl-E-2026-11-02", True), "🔴 a WINS pushes fb/champion-nfl-E-2026-11-02")
eq(diff, ['-CHAMPION = {"nfl": None, "ncaaf": None}', '+CHAMPION = {"nfl": "E", "ncaaf": None}'],
   "🔴 ...whose only change is the CHAMPION line")
eq(sh("rev-parse", "main", cwd=ORIGIN).strip(), main0, "🔴 ...and main is untouched")
again = R.push_branch("nfl", "E", "2026-11-09", WORK)
eq((again, sorted(sh("for-each-ref", "--format=%(refname:short)", "refs/heads", cwd=ORIGIN).split())),
   (("fb/champion-nfl-E-2026-11-02", False), sorted(heads)),
   "🔴 never a second branch while one exists")

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 CHAMPION None CHANGES NOTHING; A NAMED ONE ADDS ITS INPUT AND ITS METHOD")
# ══════════════════════════════════════════════════════════════════════
eq(FM.CHAMPION, {"nfl": None, "ncaaf": None}, "🔴 main's champions are today's models")
r = row("x", "nfl", "2026-10-07", "SEA", "NE")
r["sig"]["epa_m"] = 7.0
eq([FM.features(r, mk) for mk in FM.MARKETS], [FM.base_features(r, mk) for mk in FM.MARKETS],
   "🔴 with CHAMPION None the inputs are the model's own, unchanged")
_attach = FC.attach
FC.attach = lambda *a, **k: (_ for _ in ()).throw(AssertionError("read a challenger's files"))
T6 = tree()
put(T6, "data/nfl/latest/schedule-2026.json.gz", {"season": 2026, "games": [
    {"id": "a", "start": "2026-09-10T20:20", "home": "SEA", "away": "NE", "week": 1, "final": True,
     "home_score": 20, "away_score": 10}]})
try:
    _rows, _ok = FM.build_rows("nfl", T6, board={}), True
except AssertionError:
    _rows, _ok = None, False
ck(_ok and len(_rows) == 1 and "epa_m" not in _rows[0]["sig"],
   "🔴 ...and build_rows reads none of the challengers' files")
FM.CHAMPION["nfl"] = "E"
try:
    FC.attach = _attach
    eq([len(FM.features(r, mk)) - len(FM.base_features(r, mk)) for mk in FM.MARKETS], [1, 0, 1],
       "🔴 CHAMPION E adds one input to spread and moneyline, none to totals")
    eq(FM.features(r, "spread")[-1], 0.4, "   ...(EPA margin 7 - line 3) / 10")
finally:
    FM.CHAMPION["nfl"] = None
eq((card_fb.game_method({"champion": "E"}), card_fb.game_method({})), ("+game-E", ""),
   "🔴 the card's method gains \"+game-E\", and nothing with no champion")
eq(F.champion_inputs("nfl"), [], "   ...and no champion adds no freshness row")
_ci = F.champion_inputs
F.champion_inputs = lambda lg: _ci(lg, {"nfl": "E"})
try:
    fr = [x for x in F.survey(data=T6.replace("\\", "/") + "/data/nfl", picks=T6, now=NOW)
          if x["path"].endswith("def-epa-2026.json.gz")]
finally:
    F.champion_inputs = _ci
ck(len(fr) == 1 and fr[0]["stale"] and fr[0]["mode"] == "nfl-logs",
   "🔴 CHAMPION E's missing def-epa file is a stale freshness row like the others", fr)

# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 THE MONDAY EMAIL: THE SECTION, A WINS UNDER \"NEEDS YOU\", AND AN OLD REPORT")
# ══════════════════════════════════════════════════════════════════════
T7 = tree()
GAP = {"predictions": 76, "model_log_loss": 0.6814, "books_log_loss": 0.6931, "state": "level",
       "trend": {"state": "no clear change yet"}, "said": 57.8, "hit": 53.9}
DOC = {"built_at": "2026-11-02T09:50:00Z", "miss": {"games": 77, "margin_model": 10.5, "margin_books": 9.8,
                                                    "total_model": 11.4, "total_books": 10.7},
       "scoreboard": {mk: GAP for mk in FM.MARKETS},
       "line_moves": {mk: {"toward": 25, "against": 36, "unmoved": 17, "toward_share": 41.0} for mk in FM.MARKETS},
       "challengers": [{"name": "E", "what": "EPA", "verdict": "NOT YET MEASURABLE", "scored": {"predictions": 0}}]}
put(T7, "data/latest/health.json", {"checked_at": "2026-11-02T10:41:00Z", "findings": []})
put(T7, "data/nfl/latest/fb-refit.json", DOC)
body = S.build(T7, NOW)[0]
ck("## Is the football model learning?" in body and "- NFL: our predicted margins miss by 10.5 points on average, "
   "the books' line by 9.8" in body and "lines moved our way in 25 of 61 games (41%; 50% means no edge)" in body
   and "Challenger E (EPA): 0 of 300 scored predictions, not yet measurable." in body
   and "- College: no weekly report yet." in body, "🔴 the Monday email shows the section, in plain words", body[-900:])
ck(body.startswith("Nothing needs you this week."), "   ...and a contest with no winner needs nothing")
won = dict(DOC, challengers=[{"name": "E", "what": "EPA", "verdict": "WINS", "alpha": 0.01,
                              "branch": "fb/champion-nfl-E-2026-11-02",
                              "scored": {"predictions": 320, "games": 160, "p": 0.004,
                                         "champion_log_loss": 0.68, "challenger_log_loss": 0.67}}])
put(T7, "data/nfl/latest/fb-refit.json", won)
body = S.build(T7, NOW)[0]
ck(body.startswith("Needs you: NFL challenger E (EPA) beat the current game model")
   and "https://github.com/smh0602/gizmos-picks/compare/main...fb/champion-nfl-E-2026-11-02?expand=1" in body
   and "\"Create pull request\" button (twice" in body and "\"All checks have passed\"" in body
   and "\"Confirm merge\"" in body, "🔴 a WINS shows \"Needs you\" with the compare link and the clicks", body[:600])
put(T7, "data/nfl/latest/fb-refit.json", dict(DOC, built_at="2026-10-24T09:50:00Z"))
ck("- NFL: the weekly report is 9 days old" in S.build(T7, NOW)[0], "🔴 a report 9 days old says so")
_root, W.ROOT = W.ROOT, T7
try:
    rep = W.Report()
    W.check_fb_refit(rep, NOW)
finally:
    W.ROOT = _root
eq([(i["key"], i["severity"]) for i in rep.items], [("fb-refit:nfl", "DEGRADED")],
   "🔴 ...and it is a DEGRADED finding in health, not BROKEN")

# ══════════════════════════════════════════════════════════════════════
section("8. 🔴 T66 (§3a): S AND TS, FROZEN INPUTS, ALL THREE MARKETS")
# ══════════════════════════════════════════════════════════════════════
X = row("x", "nfl", "2026-10-25", "AAA", "CCC", M=3.0, T=45.0)
X["sig"].update(own_m=5.0, h2h_m=9.0, form_m=4.0, poss=0.1, out=2.0, dome=1.0, vac_h=0.3, vac_a=0.1,
                own_t=47.0, h2h_t=50.0, form_t=44.0)
X["sig"]["def"] = 0.6
r6 = lambda v: [round(a, 6) for a in v]  # noqa: E731
S_X = {mk: r6(R.challenger_feat("S")(X, mk)) for mk in FM.MARKETS}
eq(S_X, {"spread": [0.2, 0.1, 1.0, 0.666667, 0.0, 1.0], "moneyline": [0.5, 0.4, 1.0, 0.666667, 0.0, 1.0],
         "total": [0.2, -0.1, 0.4, 0.0, 1.0]},
   "🔴 S (NFL): own, form, possession, out, neutral, dome (total: own, form, defence, neutral, dome); "
   "no head-to-head, no signal 9")
ck(len(FM.features(X, "spread")) == 8, "   ...beside a champion that still has both (8 inputs on NFL)")
Y = row("y", "ncaaf", "2026-10-25", "AAA", "CCC", M=3.0, T=45.0)
Y["sig"].update(own_m=5.0, h2h_m=9.0, form_m=4.0, poss=0.1, dome=1.0, own_t=47.0, tal_m=7.0)
eq({mk: r6(R.challenger_feat("TS")(Y, mk)) for mk in FM.MARKETS},
   {"spread": [0.4, 0.0, 1.0], "moneyline": [0.7, 0.0, 1.0], "total": [0.2, 0.0, 1.0]},
   "🔴 TS (college): (T margin - line)/10 or T margin/10, neutral, dome; total (own total - line)/10, "
   "neutral, dome")
_t = [row("z", "ncaaf", "2026-10-01", "AAA", "CCC")]
_u = [row("z", "ncaaf", "2026-10-01", "AAA", "CCC")]
FC.attach("T", "ncaaf", _t, T1)
FC.attach("TS", "ncaaf", _u, T1)
ck(_u[0]["sig"]["tal_m"] is not None and _u[0]["sig"]["tal_m"] == _t[0]["sig"]["tal_m"],
   "🔴 TS's margin is T's own talent solve, from the same Monday cut", (_t[0]["sig"], _u[0]["sig"]))
_v = [row("z", "nfl", "2026-10-01", "AAA", "CCC")]
FC.attach("S", "nfl", _v, T1)
ck(_v[0]["sig"] == row("z", "nfl", "2026-10-01", "AAA", "CCC")["sig"], "   ...and S attaches nothing")
eq({n: (c["league"], c["markets"], c["withdrawable"]) for n, c in FC.CHALLENGERS.items() if n in ("S", "TS")},
   {"S": ("nfl", ("spread", "total", "moneyline"), False),
    "TS": ("ncaaf", ("spread", "total", "moneyline"), False)},
   "🔴 S is NFL, TS college, both on all three markets, neither withdrawable")
# `[Sam, 2026-10-15]` ~~2 and 3~~: T68 (§3b) adds AV and WX in each league; T69 (§3c)
#    adds IN, AT, RS (NFL) and ATC, RSC (college).
# `[Sam, 2026-10-16]` ~~8 and 8~~: T71 (§3e) adds SM and SMC.
eq({lg: sorted(n for n, c in FC.CHALLENGERS.items() if c["league"] == lg) for lg in ("nfl", "ncaaf")},
   {"nfl": ["AT", "AV", "E", "H", "IN", "RS", "S", "SM", "WX"],
    "ncaaf": ["ATC", "AVC", "HC", "P", "RSC", "SMC", "T", "TS", "WXC"]},
   "🔴 so alpha divides by 9 in the NFL and 9 in college (T71 adds SM, SMC)")
eq([R.registration("S", T1), R.registration("TS", T1, {"TS": "2026-10-01"}),
    R.registration("TS", T1, {"TS": "2026-10-21"}), R.registration("TS", T1, {"TS": None})],
   ["2026-10-19", "2026-10-19", "2026-10-26", None],
   "🔴 registration: S on 2026-10-19 (no file of its own); TS the later of that and its talent file's Monday")
ok_s = Planted({mk: dict(preds(HIST, lambda y: 0.3 if y else 0.7), **preds(LIVE, lambda y: 0.75 if y else 0.35,
                                                                           start=40))
                for mk in FM.MARKETS})
champ3 = Planted({mk: dict(preds(HIST, lambda y: 0.6), **preds(LIVE, lambda y: 0.6, start=40))
                  for mk in FM.MARKETS})
ts = R.contest([], champ3, "TS", "2026-10-19", "2026-10-19", fits=ok_s)
ck(not ts["withdrawn"] and ts["history"]["predictions"] == 120 and ts["scored"]["predictions"] == 120,
   "🔴 TS: worse on its history and still never withdrawn; only weeks from 2026-10-19 are scored, "
   "on all three markets", (ts["withdrawn"], ts["history"]["predictions"], ts["scored"]["predictions"]))
eq((F.champion_inputs("nfl", {"nfl": "S"}), F.champion_inputs("ncaaf", {"ncaaf": "TS"})),
   ([], [("talent-{s}.json.gz", None)]),
   "🔴 a champion S adds no freshness row (it reads no file of its own); TS adds talent's")

# ══════════════════════════════════════════════════════════════════════
section("9. 🔴 T71 (§3e): SM AND SMC, THE SCORE-FIRST MODEL, ONE INPUT, ALL THREE MARKETS")
# ══════════════════════════════════════════════════════════════════════
import fb_matchups as MT  # noqa: E402
import fb_score_model as SCM  # noqa: E402
T9 = tree()
plant(T9, GAMES)
_sm = {}
for _t in (T9, T1):                      # T1 also holds games dated 09-28 and 09-30
    _rs = [row("x", "nfl", "2026-10-01", "AAA", "CCC")]
    FC.attach("SM", "nfl", _rs, _t)
    _sm[_t] = _rs[0]["sig"]["score"]
_want = [(p["margin"], p["total"]) for p in
         SCM.walk_forward([row("x", "nfl", "2026-10-01", "AAA", "CCC")], MT.Tables("nfl", T9))][0]
ck(_sm[T9] is not None and _sm[T9] == _want,
   "🔴 SM's number is fb_score_model's own predicted margin and total", (_sm[T9], _want))
eq(_sm[T1], _sm[T9], "🔴 ...and games dated on or after the row's Monday (09-28, 09-30) change nothing")
Z = row("z", "nfl", "2026-10-25", "AAA", "CCC", M=3.0, T=45.0)
Z["sig"]["score"] = (5.0, 47.0)
eq({mk: r6(R.challenger_feat("SM")(Z, mk)) for mk in FM.MARKETS},
   {"spread": [0.2], "moneyline": [0.5], "total": [0.2]},
   "🔴 SM: ONLY (m - line) / 10, m / 10, (t - line) / 10, none of the champion's inputs")
eq(r6(R.challenger_feat("SMC")(Z, "spread", M=7.0)), [-0.2], "   ...at the line being priced")
eq({mk: R.challenger_feat("SMC")(dict(Z, sig=dict(Z["sig"], score=None)), mk) for mk in FM.MARKETS},
   {mk: [0.0] for mk in FM.MARKETS}, "   ...and no prediction is 0")
eq({n: (c["league"], c["markets"], c["withdrawable"]) for n, c in FC.CHALLENGERS.items() if n in ("SM", "SMC")},
   {"SM": ("nfl", ("spread", "total", "moneyline"), False),
    "SMC": ("ncaaf", ("spread", "total", "moneyline"), False)},
   "🔴 SM is NFL, SMC college, both on all three markets, neither withdrawable")
for _n in ("SM", "SMC"):
    _c = R.contest([], champ3, _n, "2026-10-19", "2026-10-19", fits=ok_s)
    ck(not _c["withdrawn"] and _c["history"]["predictions"] == 120 and _c["scored"]["predictions"] == 120,
       "🔴 %s is scored like every challenger: only weeks from its registration, all three markets" % _n)
_al = {lg: R.verdicts([dict(scored(300, 0.05, 0.001), name=n) for n, c in FC.CHALLENGERS.items()
                       if c["league"] == lg])[0]["alpha"] for lg in ("nfl", "ncaaf")}
ck(all(abs(a - 0.01 / 9) < 1e-12 and a < 0.01 / 8 for a in _al.values()),
   "🔴 the divisor is 9 in each league: every bar is stricter than 0.01 / 8, never looser", _al)
# `[2026-10-16]` ~~the first Monday on or after the merge day (10-19 -> 10-19)~~: AFTER it (§3e).
eq([R.registration("SM", T1, {"SM": d}) for d in ("2026-10-16", "2026-10-19", "2026-10-21", "2026-10-26", None)],
   ["2026-10-19", "2026-10-26", "2026-10-26", "2026-11-02", None],
   "🔴 registration: the later of 2026-10-19 and the first Monday AFTER the merge day (a Monday merge "
   "counts from the next Monday)")
G9 = tree()


def _git(*a, date="2026-10-10T12:00:00Z"):
    env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
                          + list(a), cwd=G9, env=env, capture_output=True, text=True, check=True)


_git("init", "-q", "-b", "main")
open(os.path.join(G9, "fb_challengers.py"), "w", encoding="utf-8").write("CHALLENGERS = {}\n")
_git("add", "-A")
_git("commit", "-q", "-m", "base")
_git("checkout", "-q", "-b", "pr")
open(os.path.join(G9, "fb_challengers.py"), "w", encoding="utf-8").write(
    'CHALLENGERS = {\n    "SM": {"league": "nfl", "what": "score model"},\n}\n')
_git("commit", "-q", "-am", "the PR's own commit", date="2026-10-16T02:00:00Z")
_git("checkout", "-q", "main")
_git("merge", "-q", "--no-ff", "pr", "-m", "merge", date="2026-10-21T15:00:00Z")
eq((R.merged_on("SM", G9), R.registration("SM", G9), R.merged_on("SM", T9)), ("2026-10-21", "2026-10-26", None),
   "🔴 the merge day is read from main's first-parent line (the PR's own commit was 10-16); no git, no date")
eq(F.champion_inputs("nfl", {"nfl": "SM"}) + F.champion_inputs("ncaaf", {"ncaaf": "SMC"}), [],
   "a champion SM or SMC adds no freshness row (it reads no file of its own)")

# ══════════════════════════════════════════════════════════════════════
section("10. 🔴 AGAINST EVERY CHAMPION, EVERY CHALLENGER BUILDS OR IS NOT APPLICABLE")
# ══════════════════════════════════════════════════════════════════════
_na, _crash = [], []
for _lg in ("nfl", "ncaaf"):
    _names = [n for n, c in FC.CHALLENGERS.items() if c["league"] == _lg]
    _r = row("p", _lg, "2026-10-25", "AAA", "CCC")
    _old = FM.CHAMPION[_lg]
    try:
        for _ch in _names:
            FM.CHAMPION[_lg] = _ch
            for _o in _names:
                if _o == _ch:
                    continue
                if not FC.applies(_o, _r):
                    _na.append((_ch, _o))
                    continue
                for _mk in FM.MARKETS:
                    try:
                        R.challenger_feat(_o)(_r, _mk)
                    except Exception as _e:  # noqa: BLE001
                        _crash.append((_ch, _o, _mk, type(_e).__name__))
    finally:
        FM.CHAMPION[_lg] = _old
eq(_crash, [], "🔴 against every champion, every other challenger's inputs build in all three markets")
eq(sorted(_na), [("H", "S"), ("HC", "TS"), ("SM", "S"), ("SMC", "TS")],
   "🔴 ...or it is NOT APPLICABLE: exactly S and TS against a champion with shorter lists (H, HC, SM, SMC)")

# ══════════════════════════════════════════════════════════════════════
section("11. 🔴 SM AND SMC ARE PINNED: #275's NUMBERS ON A PLANTED LEAGUE WITH PLAYER LOGS")
# ══════════════════════════════════════════════════════════════════════
T11 = tree()
_rr = random.Random(71)
_tm = ["T%d" % i for i in range(8)]
_rot, _rounds = _tm[:], []
for _ in range(7):
    _rounds.append([(_rot[i], _rot[-1 - i]) for i in range(4)])
    _rot = [_rot[0], _rot[-1]] + _rot[1:-1]
_sch, _logs = [], {}
for _w in range(42):                     # 168 final games, 336 sides, before the pinned Sunday
    _day = (datetime.date(2025, 9, 7) + datetime.timedelta(weeks=_w)).isoformat()
    for _j, (_h, _a) in enumerate(_rounds[_w % 7]):
        _h, _a = (_a, _h) if _w % 2 else (_h, _a)
        _gid, _pts = "g%d_%d" % (_w, _j), {}
        for _o in (_h, _a):
            _pa, _ru, _pl = _rr.randint(150, 330), _rr.randint(60, 190), _rr.randint(52, 72)
            # each its own draw, so a rushing, carry or pace edit moves the numbers
            _qc, _qr, _rc = _rr.randint(0, 9), _rr.randint(-5, 60), _rr.randint(16, 34)
            _pts[_o] = _rr.randint(3, 45) + (_pa - 240) // 25 + (_ru + _qr - 125) // 30
            for _pos, _st in (("QB", {"att": _pl // 2, "pass_yds": _pa - 20, "car": _qc, "rush_yds": _qr}),
                              ("RB", {"car": _rc, "rush_yds": _ru - 10, "rec_yds": 15, "tgt": 4}),
                              ("WR", {"rec_yds": _pa - 50, "tgt": 18,          # trick passes, some games
                                      "pass_yds": _rr.choice((0, 0, 0, 40))}),
                              ("TE", {"rec_yds": 35, "tgt": 6})):
                _logs.setdefault(_o + _pos, {"name": _o + _pos, "pos": _pos, "g": []})["g"].append(
                    dict(_st, d=_day, game_id=_gid, team=_o))
        _sch.append({"id": _gid, "start": _day + "T17:00", "home": _h, "away": _a, "final": True,
                     "neutral": _j == 3 and _w % 5 == 0, "home_score": max(0, _pts[_h]),
                     "away_score": max(0, _pts[_a])})
_rows11 = {}
for _lg in ("nfl", "ncaaf"):
    put(T11, "data/%s/latest/schedule-2025.json.gz" % _lg, {"season": 2025, "games": _sch})
    put(T11, "data/%s/latest/players-2025.json.gz" % _lg, {"players": _logs})
    _rs = [row(g["id"], _lg, g["start"][:10], g["home"], g["away"], season=2025, hs=g["home_score"],
               **{"as": g["away_score"]}) for g in _sch]
    for _x, g in zip(_rs, _sch):
        _x["sig"]["neutral"] = 1.0 if g["neutral"] else 0.0
    _rs += [row("pin1", _lg, "2026-06-28", "T1", "T2", final=False, hs=None, **{"as": None}),
            row("pin2", _lg, "2026-06-28", "T3", "T4", final=False, hs=None, **{"as": None})]
    _rs[-1]["sig"]["neutral"] = 1.0
    FC.attach("SM" if _lg == "nfl" else "SMC", _lg, _rs, T11)
    _rows11[_lg] = _rs
_got = {lg: [tuple(round(v, 6) for v in r["sig"]["score"]) for r in _rows11[lg][-2:]] for lg in _rows11}
_beta = SCM.walk_forward(_rows11["nfl"], MT.Tables("nfl", T11))[-1]["beta"]
ck(all(abs(b) > 1e-6 for b in _beta), "the planted logs run the pass, rush and pace tables and fit all three weights",
   _beta)
PIN = [(-1.041649, 52.42573), (-6.158078, 44.127875)]   # recorded from #275's code, 2026-10-16
ck(all(abs(a - b) < 1e-6 for lg in _got for x, y in zip(_got[lg], PIN) for a, b in zip(x, y)),
   "🔴 SM's and SMC's predicted (margin, total) are the numbers #275's code gives (a change is a new challenger)",
   _got)

# ══════════════════════════════════════════════════════════════════════
section("12. 🔴 THE MONDAY JOB READS FULL GIT HISTORY (REGISTRATION DATES COME FROM IT)")
# ══════════════════════════════════════════════════════════════════════
import re  # noqa: E402
import wfparse  # noqa: E402
_deep = {}
for _f in (".github/workflows/fb-refit.yml", "docs/upload/fb-refit.yml"):
    _p = os.path.join(ROOT, _f)
    if not os.path.exists(_p):
        continue
    _src = open(_p, encoding="utf-8").read()
    _ln = _src.splitlines()
    _co = [s for s in wfparse.steps(_src) if any("actions/checkout@" in x for x in _ln[s.start:s.end])]
    _deep[_f] = bool(_co) and all(re.search(r"(?m)^\s*fetch-depth:\s*0\s*$", "\n".join(_ln[s.start:s.end]))
                                  for s in _co)
ck(".github/workflows/fb-refit.yml" in _deep and all(_deep.values()),
   "🔴 every copy of fb-refit.yml checks out with fetch-depth: 0 (a shallow clone gives the tip's date)", _deep)

# ══════════════════════════════════════════════════════════════════════
section("13. 🔴 league() SCORES EVERY REGISTERED CHALLENGER; ONE IT CANNOT BUILD IS NOT APPLICABLE")
# ══════════════════════════════════════════════════════════════════════
_names = [n for n, c in FC.CHALLENGERS.items() if c["league"] == "nfl"]
_bare = [dict(r, sig={k: v for k, v in r["sig"].items() if k != "score"}) for r in _rows11["nfl"]]
_lgd = R.league("nfl", T11, NOW, rows=_bare, added={n: "2025-01-01" for n in _names})
ck([r["sig"].get("score") for r in _bare] == [r["sig"]["score"] for r in _rows11["nfl"]]
   and sum(1 for r in _bare if r["sig"].get("score")) > 100,
   "🔴 league() builds SM's input itself: rows handed in without it get the score model's own numbers")
_byn = {x["name"]: x for x in _lgd["challengers"]}
ck(sorted(_byn) == sorted(_names) and all(x["history"]["predictions"] > 0 for x in _byn.values()),
   "🔴 every NFL challenger, SM included, is fitted and scored by league()",
   {n: (x.get("verdict"), x.get("history", {}).get("predictions")) for n, x in _byn.items()})
_old = FM.CHAMPION["nfl"]
try:
    FM.CHAMPION["nfl"] = "SM"
    _lgs = R.league("nfl", T11, NOW, rows=[dict(r, sig=dict(r["sig"])) for r in _rows11["nfl"]],
                    added={n: "2025-01-01" for n in _names})
finally:
    FM.CHAMPION["nfl"] = _old
_bys = {x["name"]: x for x in _lgs["challengers"]}
ck(_bys["S"]["verdict"] == "NOT APPLICABLE" and _bys["S"]["alpha"] == 0.01 / 8
   and all(x["history"]["predictions"] > 0 for n, x in _bys.items() if n != "S"),
   "🔴 with SM champion, S is NOT APPLICABLE (still in the divisor) and the rest are scored, no crash",
   {n: x.get("verdict") for n, x in _bys.items()})
_sum = S.refit_summary(_lgs, "NFL", NOW)
_s_line = _sum[_sum.find("Challenger S (fewer inputs):"):].split(". Challenger")[0]
ck(_s_line.startswith("Challenger S (fewer inputs): not applicable against the current champion")
   and "scored predictions" not in _s_line,
   "🔴 the Monday email says S is not applicable, in words, and claims no scored predictions", _s_line)
eq(S.refit_wins(_lgs, "NFL"), [], "   ...and puts nothing under \"Needs you\"")
