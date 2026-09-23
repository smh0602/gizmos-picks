#!/usr/bin/env python3
"""mlb_refit.py — MLB champion vs challenger, exactly as
`research/mlb_refit_spec.md` was approved by Sam on 2026-09-23.

    python mlb_refit.py pull [2025|2026]   # statsapi game logs -> data/latest
    python mlb_refit.py score              # walk-forward -> data/latest/mlb-refit.json
    python mlb_refit.py weekly             # pull what is missing/current, then score
    python mlb_refit.py open-pr            # open "[ASK SAM]" PR iff the challenger QUALIFIES

⛔ IT CHANGES NO COEFFICIENT AND SWITCHES NO MODEL. The champion's
coefficients are READ from `card.py` (never copied), and the challenger's
live only in the report and in a proposal PR for Sam.

🔴 THE RULE AND THE ARITHMETIC ARE FROZEN. Section 2 (Sam's rule) and
section 3 (the definitions this file implements) are fingerprinted by
`test_prereg_gate.py`. Every constant below that carries a ⛔ comes from
section 3, and `test_mlb_refit.py` reads them back from the spec.

⚠️ STDLIB ONLY. `numpy` is not on the CI runner (measured 2026-09-23: the
only `pip install` in any workflow is Playwright), so the least squares is
solved by hand-written Gauss-Jordan — the routine v5.0 was cross-checked
against to 1.6e-14.
"""
import datetime
import gzip
import json
import math
import os
import subprocess
import sys

import card                      # the champion: v5.0, read, never copied
import collect                   # `get` and the one game-log row mapper

ROOT = os.path.dirname(os.path.abspath(__file__))
LATEST = os.path.join(ROOT, "data", "latest")
STATS = collect.STATS

# ── section 3, frozen ────────────────────────────────────────────────
SEASONS = (2025, 2026)
POST_TYPES = "F,D,L,W"            # wild card, division, league, World Series
MIN_PRIOR_STARTS = 3              # ⛔ pitcher's earlier starts that season
MIN_OPP_STARTS = 20               # ⛔ opponent's earlier starts faced that season
MIN_TRAIN = 1000                  # ⛔ challenger starts after this many eligible starts
MIN_TIER_ROWS = 20                # a tier fit with fewer rows does not solve
LAMBDA_FLOOR = 0.05               # ⛔ as card.py floors lambda
P_FLOOR = 1e-12                   # ⛔ both models alike
MIN_PAIRED = 500                  # ⛔ Sam's "at least 500 predictions"
ALPHA = 0.05                      # ⛔ Sam's one-sided p < 0.05
K_LINES = [x + 0.5 for x in range(0, 13)]      # ⛔ 0.5 .. 12.5
OUT_LINES = [x + 0.5 for x in range(9, 22)]    # ⛔ 9.5 .. 21.5
BASES = ("MODEL", "MARKET", "DESCRIPTIVE")


def log(m):
    print(m, flush=True)


def L(value, basis):
    """A number the page may show, with its rule-55 label beside it."""
    assert basis in BASES, basis
    return {"value": value, "basis": basis}


# ══════════════════════════════════════════════════════════════════════
# 1. THE PULL — every 2025 and 2026 regular-season and postseason start
# ══════════════════════════════════════════════════════════════════════
def _finals(season, game_type):
    d, _ = collect.get(f"{STATS}/schedule?sportId=1&season={season}&gameType={game_type}"
                       "&fields=dates,games,gamePk,status,detailedState", timeout=60)
    return len({g["gamePk"] for x in d.get("dates", []) for g in x.get("games", [])
                if (g.get("status") or {}).get("detailedState")
                in ("Final", "Completed Early", "Game Over")})


def _starters(season, game_type):
    d, _ = collect.get(f"{STATS}/stats?stats=season&group=pitching&season={season}"
                       f"&gameType={game_type}&playerPool=All&limit=2000&sortStat=gamesStarted"
                       "&fields=stats,splits,player,id,fullName,stat,gamesStarted", timeout=60)
    sp = (d.get("stats") or [{}])[0].get("splits", []) if d.get("stats") else []
    if len(sp) >= 2000:
        raise RuntimeError("starter pool hit its limit — it may be truncated")
    return {s["player"]["id"]: s["player"].get("fullName")
            for s in sp if (s.get("stat") or {}).get("gamesStarted")}


def _post_starters(season):
    """Postseason starters, read from each finished game's BOX SCORE.

    🔴 `[measured 2026-09-23]` The season-stats endpoint IGNORES a postseason
    `gameType`: asked for `F,D,L,W` it returned the 873-arm regular-season
    pool. So the first pull fetched postseason logs only for REGULAR-SEASON
    starters, and missed the two 2025 openers who started a playoff game
    (Kittredge 10-01, Megill 10-11) — 92 of 94 starts. ✅ The box score lists
    each side's pitchers in order, the starter first. 💰 One call per game.
    """
    d, _ = collect.get(f"{STATS}/schedule?sportId=1&season={season}&gameType={POST_TYPES}"
                       "&fields=dates,games,gamePk,status,detailedState", timeout=60)
    out = {}
    for x in d.get("dates", []):
        for g in x.get("games", []):
            if (g.get("status") or {}).get("detailedState") not in (
                    "Final", "Completed Early", "Game Over"):
                continue
            b, _ = collect.get(f"{STATS}/game/{g['gamePk']}/boxscore"
                               "?fields=teams,away,home,pitchers", timeout=60)
            for side in ("away", "home"):
                ps = ((b.get("teams") or {}).get(side) or {}).get("pitchers") or []
                if ps:
                    out.setdefault(ps[0], None)
    return out


def coverage(starts_by_type, finals_by_type):
    """Every game has exactly two starters. ⛔ A mismatch is REPORTED, per
    game type, so a missing log is a named gap and never a silent one."""
    out = {}
    for gt, fin in finals_by_type.items():
        have = starts_by_type.get(gt, 0)
        out[gt] = {"finals": fin, "starts": have, "expected": 2 * fin,
                   "complete": have == 2 * fin}
    return out


def pull(season):
    """-> the season document. 💰 statsapi is free and needs no key."""
    logs, viol, failed = {}, 0, []
    counts = {"R": 0, "P": 0}
    for gt, api_gt in (("R", "R"), ("P", POST_TYPES)):
        for pid, name in sorted((_starters(season, api_gt) if gt == "R"
                                 else _post_starters(season)).items()):
            try:
                d, _ = collect.get(f"{STATS}/people/{pid}/stats?stats=gameLog&group=pitching"
                                   f"&season={season}&gameType={api_gt}"
                                   + collect.PITCHING_LOG_FIELDS, timeout=60)
                sp = (d.get("stats") or [{}])[0].get("splits", []) if d.get("stats") else []
            except Exception as e:
                failed.append((pid, gt, type(e).__name__))
                continue
            for g in sp:
                try:
                    r = collect.pitching_log_row(g)
                except ValueError:
                    viol += 1
                    continue
                r["gt"] = gt
                logs.setdefault(str(pid), {"name": name, "g": []})["g"].append(r)
                if name is None and logs[str(pid)]["name"] is None:
                    logs[str(pid)]["name"] = str(pid)
                counts[gt] += r["gs"]
    cov = coverage(counts, {"R": _finals(season, "R"), "P": _finals(season, POST_TYPES)})
    doc = {"season": season, "source": "statsapi.mlb.com game logs",
           "pulled_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "coverage": cov, "complete": all(v["complete"] for v in cov.values()),
           "failed": failed, "domain_violations": viol, "pitchers": logs}
    log("mlb %d: %s" % (season, json.dumps(cov)))
    return doc


def starts_path(season, root=None):
    return os.path.join(root or LATEST, "mlb-starts-%d.json.gz" % season)


def load(season, root=None):
    try:
        with gzip.open(starts_path(season, root), "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


# ══════════════════════════════════════════════════════════════════════
# 2. POINT-IN-TIME INPUTS — the card's own definitions, within a season
# ══════════════════════════════════════════════════════════════════════
def eligible_rows(docs):
    """Every eligible start with the inputs both models read.

    ⛔ A WHOLE DATE IS SCORED BEFORE ANY OF ITS STARTS JOINS THE HISTORY —
    v5.0's own rule. The running tallies below are updated only after
    every start on a date has been read.
    """
    out = []
    for doc in docs:
        season = doc["season"]
        starts = sorted(((r["d"], pid, r) for pid, v in doc["pitchers"].items()
                         for r in v["g"] if r.get("gs") and r.get("d")),
                        key=lambda x: (x[0], x[1]))
        by_pitcher, by_opp = {}, {}
        league_k, league_n = 0.0, 0
        i = 0
        while i < len(starts):
            day = starts[i][0]
            j = i
            while j < len(starts) and starts[j][0] == day:
                j += 1
            for d, pid, r in starts[i:j]:
                prior = by_pitcher.get(pid, [])
                opp = by_opp.get(r.get("o"), [])
                if (len(prior) < MIN_PRIOR_STARTS or len(opp) < MIN_OPP_STARTS
                        or not league_n or r.get("k") is None or r.get("outs") is None):
                    continue
                trail = prior[-card.TRAIL_N:]
                prev_np = trail[-1].get("np")
                s_out = card.sd([x.get("outs") for x in prior])
                mk8 = card.mean([x.get("k") for x in trail])
                mo8 = card.mean([x.get("outs") for x in trail])
                if prev_np is None or not s_out or mk8 is None or mo8 is None:
                    continue
                out.append({"season": season, "d": d, "pid": pid, "gt": r.get("gt"),
                            "home": 1 if r.get("h") else 0, "k": r["k"], "outs": r["outs"],
                            "mk8": mk8, "mo8": mo8, "np": prev_np, "sd": s_out,
                            "oppk": sum(opp) / len(opp), "center": league_k / league_n})
            for d, pid, r in starts[i:j]:
                by_pitcher.setdefault(pid, []).append(r)
                if r.get("k") is not None and r.get("o"):
                    by_opp.setdefault(r["o"], []).append(r["k"])
                    league_k += r["k"]
                    league_n += 1
            i = j
    return sorted(out, key=lambda x: (x["d"], x["pid"]))


# ══════════════════════════════════════════════════════════════════════
# 3. THE TWO MODELS — same shape, different coefficients
# ══════════════════════════════════════════════════════════════════════
def champion():
    """v5.0, READ from card.py at call time — never a copy."""
    return {"k": {"b0": card.K_INTERCEPT, "trail": card.K_TRAIL_B, "c": card.K_TRAIL_C,
                  "opp": card.K_OPP_B, "home": card.K_HOME},
            "o": {"a0": card.O_INTERCEPT, "c": card.O_TRAIL_C, "np": card.O_NP_B,
                  "cnp": card.O_NP_C, "home": card.O_HOME,
                  "tiers": [card.O_TIER_B_LO, card.O_TIER_B_MID, card.O_TIER_B_HI]}}


def tier_of(mo8):
    return 0 if mo8 < card.O_TIER_CUT_LO else (1 if mo8 < card.O_TIER_CUT_HI else 2)


def predict(m, r):
    hs = 1.0 if r["home"] else -1.0
    lam = (m["k"]["b0"] + m["k"]["trail"] * (r["mk8"] - m["k"]["c"])
           + m["k"]["opp"] * (r["oppk"] - r["center"]) + m["k"]["home"] * hs)
    o = m["o"]
    mu = (o["a0"] + o["tiers"][tier_of(r["mo8"])] * (r["mo8"] - o["c"])
          + o["np"] * (r["np"] - o["cnp"]) + o["home"] * hs)
    return max(LAMBDA_FLOOR, lam), mu


def solve(X, y):
    """Least squares by the normal equations, Gauss-Jordan with partial
    pivoting. -> coefficients, or None if the system is singular."""
    k = len(X[0])
    A = [[sum(r[i] * r[j] for r in X) for j in range(k)]
         + [sum(r[i] * yy for r, yy in zip(X, y))] for i in range(k)]
    for c in range(k):
        piv = max(range(c, k), key=lambda i: abs(A[i][c]))
        if abs(A[piv][c]) < 1e-9:
            return None
        A[c], A[piv] = A[piv], A[c]
        p = A[c][c]
        A[c] = [v / p for v in A[c]]
        for i in range(k):
            if i != c and A[i][c]:
                f = A[i][c]
                A[i] = [a - f * b for a, b in zip(A[i], A[c])]
    return [A[i][k] for i in range(k)]


def fit(train):
    """v5.0's recipe on `train`. -> model dict, or None if a fit won't solve."""
    if len(train) < MIN_TRAIN:
        return None
    ck = sum(r["mk8"] for r in train) / len(train)
    co = sum(r["mo8"] for r in train) / len(train)
    cnp = sum(r["np"] for r in train) / len(train)
    hs = lambda r: 1.0 if r["home"] else -1.0  # noqa: E731
    bk = solve([[1.0, r["mk8"] - ck, r["oppk"] - r["center"], hs(r)] for r in train],
               [r["k"] for r in train])
    xo = lambda r: [1.0, r["mo8"] - co, r["np"] - cnp, hs(r)]  # noqa: E731
    bo = solve([xo(r) for r in train], [r["outs"] for r in train])
    tiers = []
    for t in range(3):
        rows = [r for r in train if tier_of(r["mo8"]) == t]
        bt = solve([xo(r) for r in rows], [r["outs"] for r in rows]) \
            if len(rows) >= MIN_TIER_ROWS else None
        tiers.append(bt[1] if bt else None)
    if not bk or not bo or None in tiers:
        return None
    return {"k": {"b0": bk[0], "trail": bk[1], "c": ck, "opp": bk[2], "home": bk[3]},
            "o": {"a0": bo[0], "c": co, "np": bo[2], "cnp": cnp, "home": bo[3],
                  "tiers": tiers}, "n": len(train)}


# ══════════════════════════════════════════════════════════════════════
# 4. SCORING
# ══════════════════════════════════════════════════════════════════════
def _phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def loss_k(k, lam):
    lp = -lam + k * math.log(lam) - math.lgamma(k + 1)
    return -max(lp, math.log(P_FLOOR))


def loss_outs(o, mu, s):
    lo = -math.inf if o <= 0 else (o - 0.5 - mu) / s
    p = _phi((o + 0.5 - mu) / s) - (0.0 if lo == -math.inf else _phi(lo))
    return -math.log(max(p, P_FLOOR))


def p_over_k(lam, line):
    return 1.0 - card.pois_cdf(lam, int(math.floor(line)))


def p_over_outs(mu, s, line):
    return 1.0 - _phi((line - mu) / s)


def _betacf(a, b, x):
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1.0 + aa / c if abs(1.0 + aa / c) > 1e-300 else 1e-300
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1.0 + aa / c if abs(1.0 + aa / c) > 1e-300 else 1e-300
        de = d * c
        h *= de
        if abs(de - 1.0) < 1e-12:
            break
    return h


def t_sf(t, df):
    """P(T > t) for Student's t with df degrees of freedom."""
    x = df / (df + t * t)
    lb = (math.lgamma(df / 2.0 + 0.5) - math.lgamma(df / 2.0) - math.lgamma(0.5)
          + (df / 2.0) * math.log(x) + 0.5 * math.log(1.0 - x)) if 0 < x < 1 else None
    if lb is None:
        return 0.5 if t == 0 else (0.0 if t > 0 else 1.0)
    front = math.exp(lb)
    if x < (df / 2.0 + 1.0) / (df / 2.0 + 0.5 + 2.0):
        ib = front * _betacf(df / 2.0, 0.5, x) / (df / 2.0)
    else:
        ib = 1.0 - front * _betacf(0.5, df / 2.0, 1.0 - x) / 0.5
    return ib / 2.0 if t > 0 else 1.0 - ib / 2.0


def paired_test(d):
    """One-sided paired t-test of mean(d) > 0. -> (n, mean, t, p)."""
    n = len(d)
    if n < 2:
        return n, (d[0] if d else None), None, None
    m = sum(d) / n
    v = sum((x - m) ** 2 for x in d) / (n - 1)
    if v <= 0:
        return n, m, None, (0.0 if m > 0 else 1.0)
    t = m / math.sqrt(v / n)
    return n, m, t, t_sf(t, n - 1)


def paired_test_clustered(d, clusters):
    """One-sided test of mean(d) > 0, with CLUSTER-ROBUST standard errors by
    pitcher. -> (n, mean, t, p, n_clusters).

    🔴 `[Sam, 2026-09-23, tightened after the first run]` "The paired test
    must treat all predictions from the same pitcher as one cluster."
    ✅ CR1: V = G/(G-1) · Σ_g (Σ_{i∈g} (d_i − mean))² / n², t = mean/√V,
    Student's t on G − 1 degrees of freedom. The estimand is unchanged —
    the per-prediction mean Sam's rule names — only its uncertainty is
    corrected for predictions that are not independent.
    """
    n = len(d)
    if n < 2:
        return n, (d[0] if d else None), None, None, len(set(clusters))
    m = sum(d) / n
    sums = {}
    for x, g in zip(d, clusters):
        sums[g] = sums.get(g, 0.0) + (x - m)
    G = len(sums)
    if G < 2:
        return n, m, None, None, G
    v = (G / (G - 1.0)) * sum(s * s for s in sums.values()) / (n * n)
    if v <= 0:
        return n, m, None, (0.0 if m > 0 else 1.0), G
    t = m / math.sqrt(v)
    return n, m, t, t_sf(t, G - 1), G


def verdict(n, mean_d, p):
    if n < MIN_PAIRED:
        return "NOT YET MEASURABLE"
    return "QUALIFIES" if (mean_d is not None and mean_d > 0 and p is not None
                           and p < ALPHA) else "DOES NOT QUALIFY"


def _buckets():
    return [{"lo": 10 * i, "n": 0, "said": 0.0, "hit": 0} for i in range(10)]


def _bucket_add(bk, p, hit):
    b = bk[min(9, int(p * 10))]
    b["n"] += 1
    b["said"] += p
    b["hit"] += 1 if hit else 0


def _calib(r, lam, mu, bk):
    for line in K_LINES:
        _bucket_add(bk, p_over_k(lam, line), r["k"] > line)
    for line in OUT_LINES:
        _bucket_add(bk, p_over_outs(mu, r["sd"], line), r["outs"] > line)


def walk_forward(rows):
    """-> dict of results. Weeks run Monday to Sunday across both seasons."""
    champ = champion()
    weeks = {}
    for r in rows:
        dd = datetime.date.fromisoformat(r["d"][:10])
        weeks.setdefault((dd - datetime.timedelta(days=dd.weekday())).isoformat(), []).append(r)
    res = {"champ": {"k": [], "o": []}, "chal": {"k": [], "o": []}, "d": [], "d_pid": [],
           "d_by": {"k": [], "o": []}, "pid_by": {"k": [], "o": []},
           "cal_champ": _buckets(), "cal_chal": _buckets(), "weeks": [], "last_fit": None}
    for monday in sorted(weeks):
        test = weeks[monday]
        train = [r for r in rows if r["d"][:10] < monday]
        chal = fit(train)
        wk = {"week": monday, "starts": len(test), "train": len(train),
              "challenger": bool(chal)}
        for r in test:
            lam, mu = predict(champ, r)
            lk, lo = loss_k(r["k"], lam), loss_outs(r["outs"], mu, r["sd"])
            res["champ"]["k"].append(lk)
            res["champ"]["o"].append(lo)
            _calib(r, lam, mu, res["cal_champ"])
            if chal:
                lam2, mu2 = predict(chal, r)
                lk2, lo2 = loss_k(r["k"], lam2), loss_outs(r["outs"], mu2, r["sd"])
                res["chal"]["k"].append(lk2)
                res["chal"]["o"].append(lo2)
                _calib(r, lam2, mu2, res["cal_chal"])
                res["d"] += [lk - lk2, lo - lo2]
                res["d_pid"] += [r["pid"], r["pid"]]
                res["d_by"]["k"].append(lk - lk2)
                res["d_by"]["o"].append(lo - lo2)
                res["pid_by"]["k"].append(r["pid"])
                res["pid_by"]["o"].append(r["pid"])
        if chal:
            res["last_fit"] = dict(chal, week=monday)
        res["weeks"].append(wk)
    return res


# ══════════════════════════════════════════════════════════════════════
# 5. THE REPORT — every number the page shows carries its label
# ══════════════════════════════════════════════════════════════════════
def _mean(xs):
    return round(sum(xs) / len(xs), 5) if xs else None


def _record(losses):
    allx = losses["k"] + losses["o"]
    return {"predictions": L(len(allx), "DESCRIPTIVE"),
            "mean_log_loss": L(_mean(allx), "DESCRIPTIVE"),
            "strikeouts_mean_log_loss": L(_mean(losses["k"]), "DESCRIPTIVE"),
            "outs_mean_log_loss": L(_mean(losses["o"]), "DESCRIPTIVE")}


def _cal_table(bk):
    return [{"bucket": "%d-%d%%" % (b["lo"], b["lo"] + 10),
             "rows": L(b["n"], "DESCRIPTIVE"),
             "model_said": L(round(100.0 * b["said"] / b["n"], 1) if b["n"] else None, "MODEL"),
             "it_hit": L(round(100.0 * b["hit"] / b["n"], 1) if b["n"] else None, "DESCRIPTIVE")}
            for b in bk]


def _coefs(m):
    if not m:
        return None
    return {"strikeouts": {k: L(round(v, 4), "MODEL") for k, v in m["k"].items()},
            "outs": {k: (L([round(x, 4) for x in v], "MODEL") if isinstance(v, list)
                         else L(round(v, 4), "MODEL")) for k, v in m["o"].items()}}


def report(docs, res):
    n, md, t, p, G = paired_test_clustered(res["d"], res["d_pid"])
    v = verdict(n, md, p)
    per = {mk: paired_test_clustered(res["d_by"][mk], res["pid_by"][mk]) for mk in ("k", "o")}
    return {
        "spec": "research/mlb_refit_spec.md",
        "built_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verdict": v,
        "rule": ("The challenger replaces v5.0 only if its per-prediction log loss is "
                 "lower with one-sided p < 0.05 (paired test, every prediction from one "
                 "pitcher treated as one cluster) over at least 500 predictions. "
                 "[Sam, 2026-09-23]"),
        "display": {
            "champion": dict(_record(res["champ"]), name="v5.0 (frozen coefficients)"),
            "challenger": dict(_record(res["chal"]), name="re-fitted each week on earlier games"),
            "paired": {"predictions": L(n, "DESCRIPTIVE"),
                       "pitchers": L(G, "DESCRIPTIVE"),
                       "mean_improvement": L(round(md, 5) if md is not None else None, "DESCRIPTIVE"),
                       "t": L(round(t, 3) if t is not None else None, "DESCRIPTIVE"),
                       "p_one_sided": L(round(p, 6) if p is not None else None, "DESCRIPTIVE"),
                       "strikeouts_mean_improvement": L(round(per["k"][1], 5) if per["k"][1] is not None else None, "DESCRIPTIVE"),
                       "outs_mean_improvement": L(round(per["o"][1], 5) if per["o"][1] is not None else None, "DESCRIPTIVE")},
            "calibration": {"champion": _cal_table(res["cal_champ"]),
                            "challenger": _cal_table(res["cal_chal"])},
            "coverage": {str(d["season"]): {gt: {"finals": L(c["finals"], "DESCRIPTIVE"),
                                                 "starts": L(c["starts"], "DESCRIPTIVE"),
                                                 "complete": c["complete"]}
                                            for gt, c in d["coverage"].items()} for d in docs},
            "latest_challenger_coefficients": _coefs(res["last_fit"]),
            "champion_coefficients": _coefs(champion()),
        },
        "weeks": res["weeks"],
        "note": ("A prediction is one start in one market; both markets pooled "
                 "(spec 3). p is cluster-robust by pitcher (Sam, 2026-09-23): every "
                 "prediction from one pitcher counts as one cluster."),
    }


def score(out=None, root=None):
    docs = [d for d in (load(s, root) for s in SEASONS) if d]
    if not docs:
        raise RuntimeError("no mlb-starts-<season>.json.gz on disk — run `pull` first")
    res = walk_forward(eligible_rows(docs))
    rep = report(docs, res)
    path = out or os.path.join(LATEST, "mlb-refit.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    dp = rep["display"]["paired"]
    log("champion %s | challenger %s | paired n=%s mean_d=%s p=%s -> %s" % (
        rep["display"]["champion"]["mean_log_loss"]["value"],
        rep["display"]["challenger"]["mean_log_loss"]["value"],
        dp["predictions"]["value"], dp["mean_improvement"]["value"],
        dp["p_one_sided"]["value"], rep["verdict"]))
    return rep


# ══════════════════════════════════════════════════════════════════════
# 6. THE WEEKLY PR — only when the challenger QUALIFIES, and only once
# ══════════════════════════════════════════════════════════════════════
PR_TITLE = "[ASK SAM] MLB challenger qualified"


def open_pr(rep, dry_run=False, run=subprocess.run):
    """⛔ Edits no coefficient: it proposes one, for Sam to decide."""
    if rep.get("verdict") != "QUALIFIES":
        return "not qualified: %s" % rep.get("verdict")
    gh = os.environ.get("GH", "gh")
    got = run([gh, "pr", "list", "--state", "open", "--search", PR_TITLE + " in:title",
               "--json", "number"], capture_output=True, text=True)
    if got.returncode != 0:
        raise RuntimeError("could not list PRs: %s" % got.stderr.strip())
    if json.loads(got.stdout or "[]"):
        return "a challenger PR is already open"
    day = rep["built_at"][:10]
    branch = "mlb/challenger-%s" % day
    path = os.path.join("research", "mlb_challenger_%s.json" % day)
    if dry_run:
        return "would open %s on %s" % (PR_TITLE, branch)
    with open(os.path.join(ROOT, path), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    for cmd in (["git", "checkout", "-b", branch], ["git", "add", path],
                ["git", "commit", "-m", "mlb: challenger qualified %s — proposal for Sam" % day],
                ["git", "push", "-u", "origin", branch]):
        r = run(cmd, capture_output=True, text=True, cwd=ROOT)
        if r.returncode != 0:
            raise RuntimeError("%s failed: %s" % (" ".join(cmd), r.stderr.strip()))
    dp = rep["display"]["paired"]
    body = ("## In plain English\n\nThe re-fitted MLB model beat v5.0 under your rule "
            "(research/mlb_refit_spec.md): lower log loss on %s paired predictions, "
            "one-sided p = %s. **Nothing on the card has changed.** Switching models is "
            "your decision. The proposed coefficients and both records are in `%s`.\n\n"
            "⚠️ A PR opened by a workflow does not start other workflows, so the tests "
            "have not run on it. Close and reopen it to run them.\n\n"
            "🤖 Generated with [Claude Code](https://claude.com/claude-code)\n"
            % (dp["predictions"]["value"], dp["p_one_sided"]["value"], path))
    r = run([gh, "pr", "create", "--base", "main", "--head", branch,
             "--title", "%s (%s)" % (PR_TITLE, day), "--body", body],
            capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        raise RuntimeError("gh pr create failed: %s" % r.stderr.strip())
    return r.stdout.strip()


def main(argv):
    mode = argv[1] if len(argv) > 1 else "score"
    if mode == "pull":
        for s in ([int(argv[2])] if len(argv) > 2 else SEASONS):
            doc = pull(s)
            with gzip.open(starts_path(s), "wt", encoding="utf-8") as fh:
                json.dump(doc, fh)
        return 0
    if mode == "weekly":
        cur = max(SEASONS)
        for s in SEASONS:
            old = load(s)
            # ⚠️ A finished season that is COMPLETE is pulled once and kept.
            if s != cur and old and old.get("complete"):
                continue
            doc = pull(s)
            with gzip.open(starts_path(s), "wt", encoding="utf-8") as fh:
                json.dump(doc, fh)
        score()
        return 0
    if mode == "score":
        score()
        return 0
    if mode == "open-pr":
        with open(os.path.join(LATEST, "mlb-refit.json"), encoding="utf-8") as fh:
            log(open_pr(json.load(fh)))
        return 0
    log("usage: mlb_refit.py [pull|score|weekly|open-pr]")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
