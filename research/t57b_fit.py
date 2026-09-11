#!/usr/bin/env python3
"""T57 - DOES THE GAME'S OWN MARKET LINE CARRY WHAT T46/T47/T50 LACKED?

THIS FILE IS research/t47_fit.py WITH THREE PREDICTORS ADDED AND NOTHING
ELSE TOUCHED. Same season, same positions, same trailing window, same
MIN_PRIOR, same fit/test week split, same row filter, same line, same
naives, same grading, same bar. That is deliberate: only ONE thing
changes, so a pass is attributable to the market line and nothing else.

THE THREE, pre-registered in claude/owed-tests.md BEFORE this ran:
  own_spread     signed from the PLAYER'S OWN team (positive = favoured).
                 nflverse's closing_spread is the HOME team's number and
                 POSITIVE MEANS HOME FAVOURED - verified empirically,
                 corr(closing_spread, home margin) = +0.506 over 285
                 games, not taken on faith from a column name.
  own_implied    total/2 + own_spread/2 - his team's implied points.
  spread x pos   THE GAME-SCRIPT INTERACTION, IN THE PRIMARY AT SAM'S
                 EXPLICIT INSTRUCTION. His mechanism: a big favourite
                 runs more late, so the RB gains and the WR loses. This
                 makes the test HARDER, and that was his call.

RUN ONCE. The result is logged whichever way it falls.
"""
import json, gzip, math, os, statistics, collections, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_P = "players-2025.json.gz"
_D = next((os.path.normpath(c) for c in
           (os.path.join(_HERE, "..", "data", "nfl", "latest"),
            os.path.join(_HERE, "data", "nfl", "latest"))
           if os.path.isfile(os.path.join(c, _P))), None)
if _D is None:
    sys.exit(f"🔴 {_P} not found from {_HERE} — run inside the repo.")
TRAIL = 8
MIN_PRIOR = 6
FIT_MAX_WK, TEST_MIN_WK = 13, 14
POS = {"RB"}

D = json.load(gzip.open(os.path.join(_D, _P), "rt"))["players"]

_S = json.load(gzip.open(os.path.join(_D, "schedule-2025.json.gz"), "rt"))["games"]
LINE = {}
for _g in _S:
    if _g.get("closing_spread") is None or _g.get("closing_total") is None:
        continue
    LINE[_g["id"]] = (float(_g["closing_spread"]), float(_g["closing_total"]))
print(f"game lines loaded: {len(LINE):,} of {len(_S):,} games")

# ---- opponent: receiving yards allowed to each position, POINT IN TIME.
# built as (opp, pos) -> list of (week, yds) so a lookup can exclude the
# game being predicted and everything after it.
opp_hist = collections.defaultdict(list)
for p in D.values():
    if p["pos"] not in POS:
        continue
    for g in p["g"]:
        if g["o"]:
            opp_hist[(g["o"], p["pos"])].append((g["week"], g["rush_yds"]))

def opp_allowed(opp, pos, week):
    v = [y for w, y in opp_hist[(opp, pos)] if w < week]
    return statistics.mean(v) if len(v) >= 8 else None

def mean(x):
    return statistics.mean(x) if x else None

def _own_spread(g):
    """Spread from the PLAYER'S team's view; positive = his team favoured."""
    sp = LINE.get(g.get("game_id"))
    if sp is None:
        return None
    return sp[0] if (g.get("home") or 0) else -sp[0]

def _own_implied(g):
    """His own team's implied points: total/2 + own_spread/2."""
    sp = LINE.get(g.get("game_id"))
    if sp is None:
        return None
    s, tot = sp
    own = s if (g.get("home") or 0) else -s
    return tot / 2.0 + own / 2.0

# ---- rows: one per (player, game) with only prior-game inputs.
rows = []
for pid, p in D.items():
    if p["pos"] not in POS:
        continue
    gs = p["g"]
    for i, g in enumerate(gs):
        prior = gs[:i]
        if len(prior) < MIN_PRIOR:
            continue
        t8 = prior[-TRAIL:]
        tgt = mean([x["tgt"] for x in t8])
        yds = [x["rush_yds"] for x in t8]
        tot_t = sum(x["tgt"] for x in t8)
        ypt = (sum(yds) / tot_t) if tot_t else 0.0
        snap = mean([x.get("snap_pct", 0.0) for x in t8])
        oa = opp_allowed(g["o"], p["pos"], g["week"])
        rows.append({
            "pid": pid, "pos": p["pos"], "wk": g["week"], "y": g["rush_yds"],
            "tgt": tgt, "ypt": ypt, "snap": snap, "home": g["home"] or 0,
            "oa": oa,
            # ── T47's four new inputs, ALL NAMED IN THE SPEC ──────
            # ⚠️ Read off the GAME BEING PREDICTED, which is legal: the
            # injury report and the inactives list are published BEFORE
            # kickoff. ⛔ They are NOT trailing averages -- the question
            # is who is playing THIS week.
            "inj": g.get("inj", 0),
            "ahead_out": g.get("ahead_out", 0),
            "ol_out": g.get("ol_out", 0),
            "opp_dl_out": g.get("opp_dl_out", 0),
            "own_spread": _own_spread(g),
            "own_implied": _own_implied(g),
            "naive1": mean(yds),                                  # trailing-8 mean
            "naive2": mean([x["rush_yds"] for x in prior]),        # season to date
            "line": statistics.median(yds),                       # ~where a book sets it
            "sd_own": statistics.pstdev(yds) if len(yds) > 1 else None,
        })

rows = [r for r in rows if r["oa"] is not None]
_t47_n = len(rows)
rows = [r for r in rows if r["own_spread"] is not None]
print(f"rows after T47 filter {_t47_n:,}; after requiring a game line "
      f"{len(rows):,} ({100.0*len(rows)/max(1,_t47_n):.1f}% kept)")
if len(rows) < 0.95 * _t47_n:
    print("MORE THAN 5% OF T47's SAMPLE LOST TO THE LINE JOIN - "
          "the comparison to T46/T47/T50 is NOT-QUITE-COMPARABLE")
fit = [r for r in rows if r["wk"] <= FIT_MAX_WK]
test = [r for r in rows if r["wk"] >= TEST_MIN_WK]
print(f"rows {len(rows):,}  fit {len(fit):,}  test {len(test):,}")

# ---- OLS by normal equations, stdlib only.
# 🔴 `oa` IS ABSENT ON PURPOSE — see the module docstring. The row filter
# below still REQUIRES it, so the sample is T46's sample exactly.
FEAT = ["tgt", "ypt", "snap", "home",
        "inj", "ahead_out", "ol_out", "opp_dl_out",
        "own_spread", "own_implied"]
IPOS = []          # single position: no interaction to build
def design(rs):
    X = []
    for r in rs:
        row = [1.0] + [float(r[f]) for f in FEAT]
        for q in IPOS:
            row.append(float(r["own_spread"]) if r["pos"] == q else 0.0)
        X.append(row)
    return X, [r["y"] for r in rs]
NAMES = ["intercept"] + FEAT + ["spread_x_" + q for q in IPOS]

def solve(X, y):
    n = len(X[0])
    A = [[sum(X[k][i] * X[k][j] for k in range(len(X))) for j in range(n)]
         for i in range(n)]
    b = [sum(X[k][i] * y[k] for k in range(len(X))) for i in range(n)]
    for i in range(n):                       # gaussian elimination
        piv = max(range(i, n), key=lambda r: abs(A[r][i]))
        A[i], A[piv] = A[piv], A[i]; b[i], b[piv] = b[piv], b[i]
        for r in range(i + 1, n):
            f = A[r][i] / A[i][i]
            for c in range(i, n): A[r][c] -= f * A[i][c]
            b[r] -= f * b[i]
    x = [0.0] * n
    for i in reversed(range(n)):
        x[i] = (b[i] - sum(A[i][j] * x[j] for j in range(i + 1, n))) / A[i][i]
    return x

X, y = design(fit)
beta = solve(X, y)
print("\ncoefficients (T47 pre-registered spec, in order):")
for name, b in zip(NAMES, beta):
    print(f"  {name:10s} {b:+10.4f}")

def predict(r):
    return sum(b * v for b, v in zip(beta, design([r])[0][0]))

# residual sd on the FIT set, floored per position
res = collections.defaultdict(list)
for r in fit: res[r["pos"]].append(r["y"] - predict(r))
sd_pos = {k: statistics.pstdev(v) for k, v in res.items()}
print("\nresidual sd by position:", {k: round(v, 1) for k, v in sd_pos.items()})

def norm_over(mu, sd, line):
    if not sd or sd <= 0: return 0.5
    return 0.5 * math.erfc((line - mu) / (sd * math.sqrt(2.0)))

def grade(rs, est, sdfn, label):
    br, ae, n = 0.0, 0.0, 0
    for r in rs:
        mu = est(r)
        if mu is None: continue
        p = norm_over(mu, sdfn(r), r["line"])
        br += (p - (1.0 if r["y"] > r["line"] else 0.0)) ** 2
        ae += abs(mu - r["y"]); n += 1
    return br / n, ae / n, n

naive_sd = lambda r: max(r["sd_own"] or 0, sd_pos.get(r["pos"], 40))
model_sd = lambda r: sd_pos.get(r["pos"], 40)

print("\n=== T57-SECONDARY (RB RUSHING YARDS) — HELD-OUT WEEKS 14-22 ===")
mb, mm, n = grade(test, predict, model_sd, "model")
n1b, n1m, _ = grade(test, lambda r: r["naive1"], naive_sd, "naive1")
n2b, n2m, _ = grade(test, lambda r: r["naive2"], naive_sd, "naive2")
best_b, best_m = min(n1b, n2b), min(n1m, n2m)
print(f"{'':10s} {'Brier':>8} {'MAE':>8}")
print(f"{'MODEL':10s} {mb:8.4f} {mm:8.2f}")
print(f"{'naive-8':10s} {n1b:8.4f} {n1m:8.2f}")
print(f"{'naive-std':10s} {n2b:8.4f} {n2m:8.2f}")
print(f"\ntest rows: {n}")
print(f"PRIMARY   Brier gain vs better naive: {best_b - mb:+.4f}  "
      f"(bar >= +0.0050)  {'PASS' if best_b - mb >= 0.005 else 'FAIL'}")
print(f"SECONDARY MAE vs better naive:        {best_m - mm:+.2f}  "
      f"(must not be worse)  {'PASS' if mm <= best_m else 'FAIL'}")
print(f"MINIMUM   {n} test rows (need >= 200)  {'PASS' if n >= 200 else 'INSUFFICIENT'}")
print("\nSUBGROUP")
for pos in sorted(POS):
    sub = [r for r in test if r["pos"] == pos]
    if len(sub) < 30:
        print(f"  {pos}: only {len(sub)} rows — not judged"); continue
    sb, sm, sn = grade(sub, predict, model_sd, pos)
    b1, _, _ = grade(sub, lambda r: r["naive1"], naive_sd, pos)
    b2, _, _ = grade(sub, lambda r: r["naive2"], naive_sd, pos)
    bn = min(b1, b2)
    print(f"  {pos}: n={sn:4d}  model {sb:.4f}  naive {bn:.4f}  "
          f"{bn - sb:+.4f}  {'ok' if sb <= bn else 'WORSE THAN NAIVE'}")

# ---- coefficient significance, to grade prediction #2 honestly.
import itertools
n_obs, k = len(X), len(beta)
resid = [y[i] - sum(b * X[i][j] for j, b in enumerate(beta)) for i in range(n_obs)]
s2 = sum(r * r for r in resid) / (n_obs - k)
A = [[sum(X[m][i] * X[m][j] for m in range(n_obs)) for j in range(k)] for i in range(k)]
I = [[1.0 if i == j else 0.0 for j in range(k)] for i in range(k)]
for i in range(k):
    p = max(range(i, k), key=lambda r: abs(A[r][i]))
    A[i], A[p] = A[p], A[i]; I[i], I[p] = I[p], I[i]
    d = A[i][i]
    A[i] = [v / d for v in A[i]]; I[i] = [v / d for v in I[i]]
    for r in range(k):
        if r == i: continue
        f = A[r][i]
        A[r] = [a - f * b for a, b in zip(A[r], A[i])]
        I[r] = [a - f * b for a, b in zip(I[r], I[i])]
print("\n=== coefficient significance (fit set) ===")
for name, b, v in zip(NAMES, beta, [I[i][i] for i in range(k)]):
    se = math.sqrt(max(s2 * v, 1e-12))
    print(f"  {name:10s} {b:+9.4f}  se {se:7.4f}  t {b/se:+7.2f}")
