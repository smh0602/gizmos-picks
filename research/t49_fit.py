#!/usr/bin/env python3
"""T49 — does CFB `rush_allowed` beat a model that ALREADY knows opp_elo?

⛔ SPECIFICATION FIXED IN `claude/owed-tests.md` BEFORE THIS FILE
EXISTED. Nothing below is a choice made after seeing data:
  - target: an RB's rushing yards in a game
  - sample: pos == RB, 2021-2025, opposing defence is Power 4,
            player has >= 4 prior games that season,
            defence has >= 3 prior games that season
  - point-in-time throughout, w < week STRICTLY
  - rush_allowed is a PER-CARRY RATE (T42's pace confound)
  - A = trailing rush_yds ; B = A + opp_elo ; C = B + rush_allowed
  - VALUE IS C vs B, NOT C vs A
  - fit 2021-2023, hold out 2024 AND 2025
  - PASS = C beats B on held-out MAE by >= 1.0% IN BOTH SEASONS
  - ONE RUN.

🔴 THE RULER IS CHECKED BEFORE ANY RESULT IS BELIEVED. T48's planned
control failed and nearly let an unreportable null through; T39's passed
at r = 0.80 and is the only reason its failure was credible. Controls
here: (1) trailing form must beat a constant, or the whole frame is
broken; (2) rush_allowed must correlate with opp_elo in the RIGHT
DIRECTION, or the measure is inverted.
"""
import gzip
import json
import math
import os
import statistics
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE = "players-2024.json.gz"
D = next((os.path.normpath(c) for c in
          (os.path.join(_HERE, "..", "data", "ncaaf", "latest"),
           os.path.join(_HERE, "data", "ncaaf", "latest"))
          if os.path.isfile(os.path.join(c, _PROBE))), None)
if D is None:
    sys.exit(f"🔴 {_PROBE} not found from {_HERE} — run inside the repo.")

SEASONS = [2021, 2022, 2023, 2024, 2025]
FIT, HELD = [2021, 2022, 2023], [2024, 2025]
MIN_PLAYER_GAMES, MIN_DEF_GAMES = 4, 3
BAR = 0.010          # 1.0% relative MAE gain, DECLARED BEFORE THE RUN
P4 = set()


# ── plain OLS, normal equations with Gaussian elimination ────────────
def ols(X, y):
    n, k = len(X), len(X[0])
    A = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)]
         + [sum(X[i][a] * y[i] for i in range(n))] for a in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(A[r][c]))
        A[c], A[p] = A[p], A[c]
        if abs(A[c][c]) < 1e-12:
            continue
        for r in range(k):
            if r != c:
                f = A[r][c] / A[c][c]
                for j in range(c, k + 1):
                    A[r][j] -= f * A[c][j]
    return [A[i][k] / A[i][i] if abs(A[i][i]) > 1e-12 else 0.0
            for i in range(k)]


def predict(b, x):
    return sum(bi * xi for bi, xi in zip(b, x))


def mae(ys, ps):
    return statistics.fmean(abs(a - b) for a, b in zip(ys, ps))


# ── load ─────────────────────────────────────────────────────────────
# per season: every player-game, plus the P4 team set
seasons = {}
for s in SEASONS:
    doc = json.load(gzip.open(f"{D}/players-{s}.json.gz", "rt"))
    seasons[s] = doc["players"]
    P4.update(g["team"] for v in doc["players"].values() for g in v["g"])
print(f"seasons loaded: {sorted(seasons)}   P4 teams seen: {len(P4)}")

# ── build the defensive rushing table, POINT-IN-TIME ────────────────
# def_rush[(season, defence)] = [(week, yards_allowed, carries_allowed)]
# ⚠️ A defence's row comes from the OPPOSING players' carries -- the
# Max Muncy rule: `o` is the opponent, `team` is who the player plays
# for, and a defence is credited by `o`.
defrush = {}
for s, players in seasons.items():
    per = {}
    for v in players.values():
        for g in v["g"]:
            car, yds = g.get("car") or 0, g.get("rush_yds") or 0
            if not car:
                continue
            key = (g["o"], g["week"], g["game_id"])
            a = per.setdefault(key, [0, 0])
            a[0] += yds
            a[1] += car
    for (dfn, wk, _gid), (yds, car) in per.items():
        defrush.setdefault((s, dfn), []).append((wk, yds, car))
print(f"defence-seasons with rushing rows: {len(defrush)}")


def pit_rush_allowed(season, defence, week):
    """Yards allowed per carry, strictly before `week`. None if too thin."""
    rows = defrush.get((season, defence))
    if not rows:
        return None
    prior = [(y, c) for w, y, c in rows if w < week]
    if len(prior) < MIN_DEF_GAMES:
        return None
    ty, tc = sum(y for y, _ in prior), sum(c for _, c in prior)
    return ty / tc if tc else None


# ── build rows ───────────────────────────────────────────────────────
rows = []
for s, players in seasons.items():
    for v in players.values():
        if v.get("pos") != "RB":
            continue
        gs = sorted(v["g"], key=lambda g: g["week"])
        for i, g in enumerate(gs):
            prior = gs[:i]                       # ⛔ STRICTLY BEFORE
            if len(prior) < MIN_PLAYER_GAMES:
                continue
            opp = g["o"]
            if opp not in P4:                    # defence must be P4
                continue
            elo = g.get("opp_elo")
            if elo is None:                      # FCS -> never imputed
                continue
            ra = pit_rush_allowed(s, opp, g["week"])
            if ra is None:
                continue
            trail = statistics.fmean([(p.get("rush_yds") or 0)
                                      for p in prior])
            rows.append({"season": s, "y": float(g.get("rush_yds") or 0),
                         "trail": trail, "elo": float(elo), "ra": ra})

print(f"rows: {len(rows)}   fit {sum(1 for r in rows if r['season'] in FIT)}"
      f"   held {sum(1 for r in rows if r['season'] in HELD)}")
if len(rows) < 500:
    sys.exit("🔴 sample too small to report — stopping rather than fitting.")

# ══════════════════════════════════════════════════════════════════════
print("\n── CONTROL 1: does trailing form beat a constant? ──")
tr = [r for r in rows if r["season"] in FIT]
const = statistics.fmean([r["y"] for r in tr])
for name, seas in (("2024", [2024]), ("2025", [2025])):
    te = [r for r in rows if r["season"] in seas]
    ys = [r["y"] for r in te]
    b = ols([[1.0, r["trail"]] for r in tr], [r["y"] for r in tr])
    m_const = mae(ys, [const] * len(ys))
    m_tr = mae(ys, [predict(b, [1.0, r["trail"]]) for r in te])
    print(f"  {name}  constant {m_const:6.2f}   trailing {m_tr:6.2f}   "
          f"gain {100*(m_const-m_tr)/m_const:+5.2f}%")

print("\n── CONTROL 2: is rush_allowed pointing the RIGHT WAY? ──")
# A defence with a HIGHER Elo should allow FEWER yards per carry.
xs = [r["elo"] for r in rows]
ys2 = [r["ra"] for r in rows]
mx, my = statistics.fmean(xs), statistics.fmean(ys2)
num = sum((a-mx)*(b-my) for a, b in zip(xs, ys2))
dx = math.sqrt(sum((a-mx)**2 for a in xs))
dy = math.sqrt(sum((b-my)**2 for b in ys2))
r_eo = num/(dx*dy)
print(f"  corr(opp_elo, rush_allowed) = {r_eo:+.4f}   "
      f"{'✅ negative, as it must be' if r_eo < 0 else '🔴 WRONG SIGN'}")
print(f"  rush_allowed: mean {statistics.fmean(ys2):.3f} yds/carry, "
      f"sd {statistics.stdev(ys2):.3f}")

# ══════════════════════════════════════════════════════════════════════
ARMS = {"A  trailing only":        lambda r: [1.0, r["trail"]],
        "B  + opp_elo":            lambda r: [1.0, r["trail"], r["elo"]],
        "C  + rush_allowed":       lambda r: [1.0, r["trail"], r["elo"],
                                              r["ra"]]}
print("\n" + "=" * 68)
print("T49 — HELD-OUT MAE.  BAR: C beats B by >= 1.0% IN BOTH SEASONS")
print("=" * 68)
fit_rows = [r for r in rows if r["season"] in FIT]
coef = {}
for name, f in ARMS.items():
    coef[name] = ols([f(r) for r in fit_rows], [r["y"] for r in fit_rows])

res = {}
print(f"{'arm':<22} " + "".join(f"{s:>12}" for s in HELD))
for name, f in ARMS.items():
    line = []
    for s in HELD:
        te = [r for r in rows if r["season"] == s]
        line.append(mae([r["y"] for r in te],
                        [predict(coef[name], f(r)) for r in te]))
    res[name] = line
    print(f"{name:<22} " + "".join(f"{v:>12.3f}" for v in line))

print("\n" + "-" * 68)
B, C = res["B  + opp_elo"], res["C  + rush_allowed"],
A = res["A  trailing only"]
ok = True
print("SECOND DECLARED QUESTION — does opp_elo earn its place? (B vs A)")
for i, s in enumerate(HELD):
    g = (A[i] - B[i]) / A[i]
    print(f"  {s}   {100*g:+6.2f}%   {'PASS' if g >= BAR else 'FAIL'}")
print("\n🔴 THE TEST — rush_allowed's incremental value (C vs B)")
for i, s in enumerate(HELD):
    g = (B[i] - C[i]) / B[i]
    good = g >= BAR
    ok = ok and good
    print(f"  {s}   {100*g:+6.2f}%   vs bar +1.00%   "
          f"{'PASS' if good else 'FAIL'}")
print("-" * 68)
print(f"\nT49 VERDICT: {'✅ PASS' if ok else '⛔ FAIL'}"
      "   (both held-out seasons required)")
print("\ncoefficients on the C arm (fit 2021-2023):")
for n, b in zip(["const", "trailing", "opp_elo", "rush_allowed"],
                coef["C  + rush_allowed"]):
    print(f"  {n:<14} {b:+.5f}")
