#!/usr/bin/env python3
"""fb_sim.py — THE GAME SIMULATION: every football game played out 10,000 times.

`[Sam, 2026-10-17]` *"wed be running 1000 simulated games to get 1000 simulated outcomes,
wed be doing this for every single game of the week for both nfl and cfb"*; he chose 10,000
runs, and "Backtest, then switch": the simulation sets a league's spread and total chances
only if, on the same past games, its percentages are at least as accurate as the smooth
curve's (log loss) AND its picks' return is not lower (fixed before anyone looked).

WHAT ONE RUN IS. Each team gets `drives` possessions; each drive ends in a touchdown
(6, 7 or 8 points with the try), a field goal (3) or nothing. A team's chance of scoring on
a drive is set so its average equals the model's own predicted points (`fb_model.game_score`),
and each run first moves both teams' averages by the model's own uncertainty (what is left of
`score_sigma` / `total_sigma` after the drive-to-drive luck), so the spread of results matches
the smooth curve's while the SHAPE is football's: margins land on 3 and 7 as often as real
games do. A tie goes to overtime (NFL: a field goal or a touchdown, or a rare tie; college:
rounds until someone leads). ⛔ No price, line or books' chance is an input (Sam, 2026-10-11).

HOW A RUN IS DRAWN. A team's points over its drives have an exact distribution (the drives
convolved), so each run draws each team's points from it directly (`team_dist`, cached on a
0.25-point grid of the average): the same possession-by-possession game, 10,000 times, in
seconds. Each game's runs are seeded by the game and its inputs, so every build of the same
game gives the same 10,000 results. Stdlib only.

`PARAMS` are fitted to the stored final scores alone (`calibrate`, no model and no pick
involved): the drives per team and the touchdown share of scoring drives that best reproduce
how often real games end by each margin.
"""
import bisect
import functools
import hashlib
import math
import random
import statistics

RUNS = 10000

# the try after a touchdown: 7 (kick), 6 (missed or failed), 8 (two-point conversion)
TD_POINTS = ((7, 0.86), (6, 0.09), (8, 0.05))
FG_POINTS = 3

# `[2026-10-17]` fitted by `calibrate` on the stored final scores (NFL 2018-2026, college FBS
#    v FBS 2023-2026); see research/fb_sim_design.md for the run.
PARAMS = {
    "nfl": {"drives": 10, "td_share": 0.55, "late": 1.0, "ot_tie": 0.07, "ot_td": 0.45},
    "ncaaf": {"drives": 13, "td_share": 0.70, "late": 1.0, "ot_tie": 0.0, "ot_td": 0.5},
}
# `[2026-10-17]` THE MARGIN CORRECTION. The drives alone end NFL games by exactly 3 in about 10%
#    of close games' runs (real games: 14.9% of all games) and college in about 7% (real 10.4%): how real teams play to the score is more
#    than one last drive. So each final margin's runs are weighted by real share / simulated share
#    of that margin over every stored final score (`margin_fix`, final scores only), the same
#    correction for every game. Filled from the stored scores by `margin_fix`; {} = no correction.
MARGIN_FIX = {
    "nfl": {0: 1.3105, 1: 0.806, 2: 0.9244, 3: 1.5131, 4: 0.841, 5: 1.1251, 6: 0.8896, 7: 1.3369,
        8: 1.1404, 9: 0.4114, 10: 0.8951, 11: 0.459, 12: 0.709, 13: 0.485, 14: 1.2966,
        15: 0.6784, 16: 0.865, 17: 1.1193, 18: 0.9703, 19: 0.7665, 20: 0.8692, 21: 0.981,
        22: 0.9164, 23: 1.0505, 24: 1.468, 25: 1.0955, 26: 1.3885, 27: 0.7173, 28: 1.5161,
        29: 1.0949, 30: 0.6515, 31: 2.2812, 32: 1.6481, 33: 0.6814, 34: 1.8951, 35: 2.4434,
        36: 0.3017, 37: 2.179, 38: 2.8372, 39: 0.7435, 40: 1.9505},
    "ncaaf": {0: 1.0, 1: 0.7973, 2: 0.8912, 3: 1.6428, 4: 0.6488, 5: 0.8866, 6: 0.7818, 7: 1.287,
        8: 1.0291, 9: 0.437, 10: 1.068, 11: 0.6322, 12: 0.6406, 13: 0.6157, 14: 1.1131,
        15: 0.6373, 16: 0.5131, 17: 1.1251, 18: 0.8295, 19: 0.9709, 20: 0.6182, 21: 1.3661,
        22: 0.9476, 23: 0.5447, 24: 1.2162, 25: 1.1574, 26: 1.0106, 27: 0.8793, 28: 1.6747,
        29: 0.8786, 30: 0.3088, 31: 1.1703, 32: 1.6975, 33: 0.932, 34: 1.4032, 35: 1.8966,
        36: 1.121, 37: 0.7851, 38: 1.2072, 39: 2.1592, 40: 1.7887},
}
# THE LAST DRIVE (each team's final possession, played after the others, in a random order):
#    what a team does depends on the score, as real teams do. -> (P(TD), P(FG)) at an average
#    team; scaled by the team's own scoring rate and by PARAMS' `late` (1 = as written).
LAST_DRIVE = {"lead": (0.10, 0.12),       # protect the lead, run the clock
              "tied": (0.12, 0.38),       # play for the field goal that wins it
              "close": (0.12, 0.36),      # down 1-3: the kick that ties or wins
              "one_td": (0.26, 0.00),     # down 4-8: only a touchdown will do
              "far": (0.18, 0.08)}        # down 9+: a score that changes little
MU_STEP = 0.25            # the cache grid for a team's average


def _seed(*parts):
    return int(hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:15], 16)


@functools.lru_cache(maxsize=8192)
def team_dist(lg, mu_key, n=None):
    """-> (points, cdf, mean, mean of squares): the exact distribution of one team's points over
    `n` drives (default: all of PARAMS' drives) when its average over them is mu_key * MU_STEP.
    Drive: TD (TD_POINTS) with prob q*f, FG with q*(1-f), else 0."""
    p = PARAMS[lg]
    n, f = (n or p["drives"]), p["td_share"]
    mu = max(0.0, mu_key * MU_STEP)
    per_score = f * sum(v * w for v, w in TD_POINTS) + (1 - f) * FG_POINTS
    q = min(0.97, mu / (n * per_score)) if per_score else 0.0
    drive = {0: 1.0 - q, FG_POINTS: q * (1 - f)}
    for v, w in TD_POINTS:
        drive[v] = drive.get(v, 0.0) + q * f * w
    dist = {0: 1.0}
    for _ in range(n):
        nxt = {}
        for a, pa in dist.items():
            for b, pb in drive.items():
                nxt[a + b] = nxt.get(a + b, 0.0) + pa * pb
        dist = nxt
    pts = sorted(dist)
    cdf, acc = [], 0.0
    for k in pts:
        acc += dist[k]
        cdf.append(acc)
    cdf[-1] = 1.0
    return tuple(pts), tuple(cdf), sum(k * dist[k] for k in pts), sum(k * k * dist[k] for k in pts)


def _var(lg, mu):
    _p, _c, m1, m2 = team_dist(lg, int(round(mu / MU_STEP)))
    return m2 - m1 * m1


def _draw(lg, mu, u, n=None):
    pts, cdf, _m1, _m2 = team_dist(lg, int(round(max(0.0, mu) / MU_STEP)), n)
    return pts[min(len(pts) - 1, bisect.bisect_left(cdf, u))]


def _per_drive(lg):
    p = PARAMS[lg]
    return p["td_share"] * sum(v * w for v, w in TD_POINTS) + (1 - p["td_share"]) * FG_POINTS


def _td(rng):
    u, acc = rng.random(), 0.0
    for v, w in TD_POINTS:
        acc += w
        if u < acc:
            return v
    return TD_POINTS[0][0]


def _last_drive(lg, deficit, mu, rng):
    """One team's final possession, `deficit` = how far it trails (negative: it leads)."""
    p = PARAMS[lg]
    state = ("lead" if deficit < 0 else "tied" if deficit == 0 else "close" if deficit <= 3
             else "one_td" if deficit <= 8 else "far")
    ptd, pfg = LAST_DRIVE[state]
    rate = (mu / p["drives"]) / (_per_drive(lg) * 0.36) if mu > 0 else 0.0   # this team vs an average one
    k = p["late"] * max(0.4, min(1.8, rate))
    u = rng.random()
    if u < min(0.9, ptd * k):
        return _td(rng)
    if u < min(0.95, ptd * k + pfg * k):
        return FG_POINTS
    return 0


def play(lg, mh, ma, rng):
    """One game: every drive but each team's last from the exact distribution, then the two last
    drives in a random order, each playing to the score, then overtime on a tie."""
    p = PARAMS[lg]
    n = p["drives"]
    fh, fa = mh * (n - 1) / n, ma * (n - 1) / n
    h, a = _draw(lg, fh, rng.random(), n - 1), _draw(lg, fa, rng.random(), n - 1)
    if rng.random() < 0.5:
        h += _last_drive(lg, a - h, mh, rng)
        a += _last_drive(lg, h - a, ma, rng)
    else:
        a += _last_drive(lg, h - a, ma, rng)
        h += _last_drive(lg, a - h, mh, rng)
    if h == a:
        h, a = _overtime(lg, p, h, a, mh, ma, rng)
    return h, a


def simulate(lg, home, away, sigma, sigma_t, key="", runs=RUNS):
    """-> {"runs", "margin": {m: weight}, "total": {t: count}, "home_wins", "ties"} for one game:
    `runs` games played out from the predicted points (home, away) with the model's own spread
    of results (sigma for the margin, sigma_t for the total). None without a score or sigma.

    Three steps, all seeded by the game: (1) PILOT games at the averages alone measure what the
    games themselves spread and how far their averages drift from the target; (2) a TUNE run
    with the model's uncertainty added and the margin correction applied measures the corrected
    margin's and the total's average and spread, and both are moved back onto the model's own
    (predicted margin and total, sigma and sigma_t); (3) the `runs` games."""
    if home is None or away is None or not sigma or not sigma_t or lg not in PARAMS:
        return None
    rng = random.Random(_seed(lg, key, round(home, 2), round(away, 2), round(sigma, 4), round(sigma_t, 4), runs))
    tm, tt = home - away, home + away
    luck_m, luck_t, bh, ba = _luck(lg, home, away, rng)
    v_m, v_t = max(0.0, sigma * sigma - luck_m), max(0.0, sigma_t * sigma_t - luck_t)
    bh, ba = home - bh, away - ba
    mg, tl = _runs(lg, bh, ba, v_m, v_t, TUNE, rng)
    mm, vm = _moments(mg)
    mt, vt = _moments(tl)
    dm, dt = mm - tm, mt - tt
    bh, ba = bh - (dt + dm) / 2.0, ba - (dt - dm) / 2.0
    v_m, v_t = max(0.0, v_m - (vm - sigma * sigma)), max(0.0, v_t - (vt - sigma_t * sigma_t))
    margin, total = _runs(lg, bh, ba, v_m, v_t, runs, rng)
    hw = sum(c for m, c in margin.items() if m > 0)
    ties = sum(c for m, c in margin.items() if m == 0)
    return {"runs": runs, "margin": margin, "total": total, "home_wins": hw, "ties": ties}


TUNE = 4000


def _runs(lg, home, away, v_m, v_t, runs, rng):
    """`runs` games: each moves both averages by the model's uncertainty (variance v_m on the
    margin, v_t on the total), plays the game, and counts its margin and total; the margin
    counts then carry the correction (renormalised to `runs`)."""
    s_m, s_t = math.sqrt(v_m), math.sqrt(v_t)
    margin, total = {}, {}
    for _ in range(runs):
        em, et = rng.gauss(0.0, s_m), rng.gauss(0.0, s_t)
        h, a = play(lg, home + (et + em) / 2.0, away + (et - em) / 2.0, rng)
        margin[h - a] = margin.get(h - a, 0) + 1
        total[h + a] = total.get(h + a, 0) + 1
    fix = MARGIN_FIX.get(lg) or {}
    if fix:
        w = {m: c * fix.get(min(abs(m), FIX_CAP), 1.0) for m, c in margin.items()}
        z = sum(w.values())
        margin = {m: v * runs / z for m, v in w.items()}
    return margin, total


def _moments(hist):
    n = float(sum(hist.values()))
    mean = sum(k * c for k, c in hist.items()) / n
    return mean, sum(c * (k - mean) ** 2 for k, c in hist.items()) / n


PILOT = 2000


def _luck(lg, home, away, rng):
    """(var of the margin, var of the total, home's and away's average points minus their
    targets) of PILOT games played at fixed averages (home, away)."""
    ms, ts, hs, as_ = [], [], [], []
    for _ in range(PILOT):
        h, a = play(lg, home, away, rng)
        ms.append(h - a)
        ts.append(h + a)
        hs.append(h)
        as_.append(a)
    return (statistics.pvariance(ms), statistics.pvariance(ts),
            statistics.mean(hs) - home, statistics.mean(as_) - away)


def _overtime(lg, p, h, a, mh, ma, rng):
    """A tie after regulation. NFL: a rare tie, else the side the averages favour (by their
    share of the points) wins by a field goal or a touchdown. College: rounds of one
    possession each (TD 7, FG 3, nothing) until someone leads."""
    ph = mh / (mh + ma) if (mh + ma) > 0 else 0.5
    if lg == "nfl":
        if rng.random() < p["ot_tie"]:
            return h, a
        add = 6 if rng.random() < p["ot_td"] else 3
        return (h + add, a) if rng.random() < ph else (h, a + add)
    for _ in range(20):
        sh = 7 if rng.random() < p["ot_td"] * 2 * ph else (3 if rng.random() < 0.5 else 0)
        sa = 7 if rng.random() < p["ot_td"] * 2 * (1 - ph) else (3 if rng.random() < 0.5 else 0)
        if sh != sa:
            return h + sh, a + sa
    return h + 3, a                                  # never reached in practice


def cover(sim, line, market):
    """-> (p_win, p_push) for the HOME side of a spread at threshold M = line (home wins when its
    margin is above M; fb_model's convention), or the OVER of a total at line. None w/o a sim."""
    if not sim or line is None:
        return None
    hist = sim["margin" if market == "spread" else "total"]
    n = float(sim["runs"])
    win = sum(c for k, c in hist.items() if k > line) / n
    push = sum(c for k, c in hist.items() if k == line) / n
    return win, push


FIX_CAP = 40               # margins past 40 share one weight


def margin_fix(lg, games, runs_per=20, seed=13):
    """-> {|margin|: real share / simulated share} for k = 0..FIX_CAP, from `games` =
    [(home_pts, away_pts)] alone: every stored game replayed `runs_per` times as `calibrate` does
    (no correction applied), each weight shrunk toward 1 with 25 pseudo-games and kept in
    [0.25, 4]."""
    hs = [h for h, _a in games]
    as_ = [a for _h, a in games]
    mh, ma = statistics.mean(hs), statistics.mean(as_)
    sd_team = statistics.pstdev(hs + as_)
    luck = _var(lg, (mh + ma) / 2.0)
    s = math.sqrt(max(0.0, sd_team * sd_team - luck))
    rng = random.Random(seed)
    real, got = {}, {}
    for h, a in games:
        k = min(abs(h - a), FIX_CAP)
        real[k] = real.get(k, 0) + 1
    for _ in range(runs_per):
        for _g in games:
            x, y = play(lg, mh + rng.gauss(0, s), ma + rng.gauss(0, s), rng)
            k = min(abs(x - y), FIX_CAP)
            got[k] = got.get(k, 0) + 1
    n, m = float(len(games)), float(runs_per * len(games))
    out = {}
    for k in range(FIX_CAP + 1):
        pr, ps = real.get(k, 0) / n, got.get(k, 0) / m
        prior = 25.0
        num = real.get(k, 0) + prior * ps          # shrink toward the simulated share (weight 1)
        out[k] = round(max(0.25, min(4.0, (num / (n + prior)) / ps)), 4) if ps > 0 else 1.0
    return out


def summary(sim):
    """The compact form stored per game (fb-model.json `win_chances[].sim`): runs, the home win
    share, and the margin and total counts as lists from their lowest value."""
    if not sim:
        return None
    out = {"runs": sim["runs"], "home_win": round(sim["home_wins"] / sim["runs"], 4),
           "tie": round(sim["ties"] / sim["runs"], 4)}
    for key in ("margin", "total"):
        h = sim[key]
        lo, hi = min(h), max(h)
        out[key + "_from"] = lo
        out[key] = [round(h.get(k, 0), 1) for k in range(lo, hi + 1)]
    return out


def from_summary(s):
    """The stored form back to `simulate`'s (for `cover`), or None."""
    if not s or not s.get("margin") or not s.get("total"):
        return None
    out = {"runs": s["runs"]}
    for key in ("margin", "total"):
        lo = s[key + "_from"]
        out[key] = {lo + i: v for i, v in enumerate(s[key]) if v}
    return out


def team_cover(sim, side, point):
    """-> (p_win, p_push) for a TEAM spread at its own point: home wins when margin + point > 0
    (margin above M = -point), away when -margin + point > 0 (margin below point)."""
    if not sim or point is None or side not in ("home", "away"):
        return None
    n = float(sim["runs"])
    hist = sim["margin"]
    if side == "home":
        win = sum(c for k, c in hist.items() if k + point > 0)
        push = sum(c for k, c in hist.items() if k + point == 0)
    else:
        win = sum(c for k, c in hist.items() if point - k > 0)
        push = sum(c for k, c in hist.items() if point - k == 0)
    return win / n, push / n


# ══════════════════════════════════════════════════════════════════════
# CALIBRATION — from final scores only (no model, no pick)
# ══════════════════════════════════════════════════════════════════════
def calibrate(lg, games, grid_drives=None, grid_share=None, runs_per=2, seed=7, grid_late=(1.0,)):
    """-> (best (drives, td_share), table) for `games` = [(home_pts, away_pts)]. For each
    candidate, every stored game is replayed `runs_per` times with team averages drawn so the
    league's own spread of team points is matched, and the share of games ending by each
    margin 0..21 is compared with the real share (sum of squared differences)."""
    hs = [h for h, _a in games]
    as_ = [a for _h, a in games]
    mh, ma = statistics.mean(hs), statistics.mean(as_)
    real = {}
    for h, a in games:
        k = min(abs(h - a), 22)
        real[k] = real.get(k, 0) + 1
    n = float(len(games))
    real = {k: v / n for k, v in real.items()}
    sd_team = statistics.pstdev(hs + as_)
    grid_drives = grid_drives or range(9, 16)
    grid_share = grid_share or [x / 100.0 for x in range(45, 81, 3)]
    table = []
    saved = dict(PARAMS.get(lg, {}))
    try:
        for d, f, lt in ((d, f, lt) for d in grid_drives for f in grid_share for lt in grid_late):
            if True:
                PARAMS[lg] = dict(saved, drives=d, td_share=f, late=lt)
                team_dist.cache_clear()
                luck = _var(lg, (mh + ma) / 2.0)
                s = math.sqrt(max(0.0, sd_team * sd_team - luck))
                rng = random.Random(seed)
                got = {}
                for _ in range(runs_per):
                    for _g in games:
                        a1, a2 = mh + rng.gauss(0, s), ma + rng.gauss(0, s)
                        x, y = play(lg, a1, a2, rng)
                        k = min(abs(x - y), 22)
                        got[k] = got.get(k, 0) + 1
                m = float(runs_per * len(games))
                err = sum((got.get(k, 0) / m - real.get(k, 0.0)) ** 2 for k in range(0, 23))
                table.append({"drives": d, "td_share": f, "late": lt, "err": err,
                              "p3": got.get(3, 0) / m, "p7": got.get(7, 0) / m})
    finally:
        PARAMS[lg] = saved
        team_dist.cache_clear()
    table.sort(key=lambda r: r["err"])
    return (table[0]["drives"], table[0]["td_share"]), table, {"p3": real.get(3), "p7": real.get(7)}
