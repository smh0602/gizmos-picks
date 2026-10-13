#!/usr/bin/env python3
"""fb_challengers.py — the football game model's frozen CHALLENGERS (T65,
`research/fb_refit_spec.md`, pre-registered 2026-10-12 before any result).

    E  NFL      the opponent-adjusted EPA margin (nflverse, def-epa-<season>)
    P  college  the same, from CFBD /plays `ppa` (ppa-<season>, cfb.py)
    T  college  CFBD /talent, z-scored per season, one unpenalised term in
                the champion's margin solve (talent-<season>, cfb.py)

⛔ FROZEN. Any change is a NEW challenger with a new name.
⛔ POINT IN TIME: a row's input reads only entries / games dated (UTC kickoff
date) before its own week's Monday, the walk-forward's cut.
✅ `fb_model` imports this for the CHAMPION's input only (`fb_model.CHAMPION`);
with every CHAMPION None the card build never calls it. `fb_refit.py` scores
all of them weekly. Stdlib only, pure-Python Gauss-Seidel like
`fb_model.solve_ratings`.
"""
import collections
import datetime
import glob
import os
import statistics

import fb_model as FM

HALF_LIFE = FM.RATING_HALF_LIFE      # 150 days, the champion's weights
RIDGE = FM.RATING_RIDGE              # 1 on every team term
TOL, SWEEPS = FM.RATING_TOL, FM.RATING_SWEEPS

CHALLENGERS = {
    "E": {"league": "nfl", "what": "EPA", "markets": ("spread", "moneyline"),
          "files": ("def-epa-{s}.json.gz",), "key": "epa_m", "withdrawable": False,
          "input": ("nfl-logs", "def-epa-{s}.json.gz", "possession")},
    "P": {"league": "ncaaf", "what": "PPA", "markets": ("spread", "moneyline"),
          "files": ("ppa-{s}.json.gz",), "key": "ppa_m", "withdrawable": True,
          "input": ("cfb-probe", "ppa-{s}.json.gz", "possession")},
    "T": {"league": "ncaaf", "what": "talent", "markets": ("spread", "moneyline"),
          "files": ("talent-{s}.json.gz",), "key": "tal_m", "withdrawable": True,
          # written once a season: stale only when the season's file is missing
          "input": ("cfb-probe", "talent-{s}.json.gz", None)},
}


def latest(lg, root=None):
    return os.path.join(root or FM.ROOT, "data", lg, "latest")


def weight(day, wk):
    return 0.5 ** ((datetime.date.fromisoformat(wk) - datetime.date.fromisoformat(day)).days / HALF_LIFE)


def schedule_by_id(lg, root=None):
    """{game_id: game} over every stored schedule, all divisions."""
    out = {}
    for p in sorted(glob.glob(os.path.join(latest(lg, root), "schedule-*.json.gz"))):
        doc = FM.jz(p) or {}
        for g in doc.get("games") or []:
            if g.get("start") and g.get("home") and g.get("away"):
                out[str(g.get("id"))] = dict(g, season=doc.get("season"))
    return out


# ══════════════════════════════════════════════════════════════════════
# E AND P — one entry per offence per game: (day, offence, defence, home, value, plays)
# ══════════════════════════════════════════════════════════════════════
def _entry(g, off, dfn, value, plays):
    h = 1.0 if (off == g["home"] and not g.get("neutral")) else 0.0
    return (g["start"][:10], off, dfn, h, float(value), float(plays))


def epa_entries(root=None):
    """E: each by_team[defence][game_id] is what that offence (`opp`) did."""
    sched, out = schedule_by_id("nfl", root), []
    for s in FM.SEASONS:
        doc = FM.jz(os.path.join(latest("nfl", root), "def-epa-%d.json.gz" % s)) or {}
        for dfn, games in (doc.get("by_team") or {}).items():
            for gid, e in games.items():
                g = sched.get(str(gid))
                if g and e.get("opp") and e.get("epa_per_play") is not None and e.get("plays"):
                    out.append(_entry(g, e["opp"], dfn, e["epa_per_play"], e["plays"]))
    return sorted(out)


def ppa_entries(root=None):
    """P: per offence per game, the mean ppa over the plays that carry one."""
    sched, out = schedule_by_id("ncaaf", root), []
    for s in FM.SEASONS:
        doc = FM.jz(os.path.join(latest("ncaaf", root), "ppa-%d.json.gz" % s)) or {}
        for gid, offs in (doc.get("games") or {}).items():
            g = sched.get(str(gid))
            if not g:
                continue
            for off, v in offs.items():
                n = v.get("plays_with_ppa") or 0
                if n and off in (g["home"], g["away"]):
                    dfn = g["away"] if off == g["home"] else g["home"]
                    out.append(_entry(g, off, dfn, v["ppa_sum"] / n, n))
    return sorted(out)


def solve_epa(E, wk, warm=None):
    """value = base + home edge x home + Off_offence - Def_defence, weighted
    0.5 ** (days / 150), ridge 1 on Off and Def only, entries dated before `wk`."""
    w = [weight(e[0], wk) for e in E]
    s = {"base": 0.0, "hfa": 0.0, "O": {}, "D": {}}
    if warm:
        s = {"base": warm["base"], "hfa": warm["hfa"], "O": dict(warm["O"]), "D": dict(warm["D"])}
    by_o, by_d = collections.defaultdict(list), collections.defaultdict(list)
    for i, e in enumerate(E):
        by_o[e[1]].append(i)
        by_d[e[2]].append(i)
    teams = set(by_o) | set(by_d)
    for t in teams:
        s["O"].setdefault(t, 0.0)
        s["D"].setdefault(t, 0.0)
    O, D = s["O"], s["D"]
    sw, sw_h = sum(w), sum(wi * e[3] for wi, e in zip(w, E))
    for _n in range(SWEEPS if E else 0):
        old = (s["base"], s["hfa"], dict(O), dict(D))
        s["base"] = sum(wi * (e[4] - s["hfa"] * e[3] - O[e[1]] + D[e[2]]) for wi, e in zip(w, E)) / sw
        s["hfa"] = (sum(wi * e[3] * (e[4] - s["base"] - O[e[1]] + D[e[2]]) for wi, e in zip(w, E)) / sw_h
                    if sw_h else 0.0)
        for t, ix in by_o.items():
            O[t] = sum(w[i] * (E[i][4] - s["base"] - s["hfa"] * E[i][3] + D[E[i][2]]) for i in ix) / (
                sum(w[i] for i in ix) + RIDGE)
        for t, ix in by_d.items():
            D[t] = sum(w[i] * (s["base"] + s["hfa"] * E[i][3] + O[E[i][1]] - E[i][4]) for i in ix) / (
                sum(w[i] for i in ix) + RIDGE)
        moved = max([abs(s["base"] - old[0]), abs(s["hfa"] - old[1])]
                    + [abs(O[t] - old[2].get(t, 0.0)) + abs(D[t] - old[3].get(t, 0.0)) for t in teams])
        if moved < TOL:
            break
    s["teams"] = teams
    s["plays"] = sum(e[5] for e in E) / len(E) if E else 0.0
    return s


def epa_margin(s, home, away, neutral):
    """The EPA margin in points, or None when either team has no earlier entry."""
    if not s or home not in s["teams"] or away not in s["teams"]:
        return None
    h = 0.0 if neutral else 1.0
    return (s["hfa"] * h + s["O"][home] - s["D"][away] - s["O"][away] + s["D"][home]) * s["plays"]


# ══════════════════════════════════════════════════════════════════════
# T — the champion's margin solve plus beta x (z_home - z_away)
# ══════════════════════════════════════════════════════════════════════
def talent_z(root=None):
    """{season: {team: z}} — each season's file z-scored within itself."""
    out = {}
    for p in glob.glob(os.path.join(latest("ncaaf", root), "talent-*.json.gz")):
        doc = FM.jz(p) or {}
        t = {k: float(v) for k, v in (doc.get("teams") or {}).items() if v is not None}
        if doc.get("season") is not None and len(t) > 1:
            mu, sd = statistics.mean(t.values()), statistics.pstdev(t.values()) or 1.0
            out[int(doc["season"])] = {k: (v - mu) / sd for k, v in t.items()}
    return out


def talent_games(root=None, z=None):
    """The champion's rating games (`fb_model.rating_games`), each with its own
    season's z gap: (day, home, away, home flag, home pts, away pts, z gap)."""
    z = talent_z(root) if z is None else z
    out = []
    for p in sorted(glob.glob(os.path.join(latest("ncaaf", root), "schedule-*.json.gz"))):
        doc = FM.jz(p) or {}
        zs = z.get(doc.get("season")) or {}
        for g in doc.get("games") or []:
            if (g.get("final") and FM.t60r.kick(g) is not None and g.get("home") and g.get("away")
                    and g.get("home_score") is not None and g.get("away_score") is not None):
                out.append((g["start"][:10], g["home"], g["away"], 0.0 if g.get("neutral") else 1.0,
                            float(g["home_score"]), float(g["away_score"]),
                            zs.get(g["home"], 0.0) - zs.get(g["away"], 0.0)))
    return sorted(out)


def solve_talent(G, wk, warm=None):
    """margin = home edge x home + beta x z gap + R_home - R_away; ridge 1 on R only."""
    w = [weight(g[0], wk) for g in G]
    s = {"hfa": 0.0, "beta": 0.0, "R": {}}
    if warm:
        s = {"hfa": warm["hfa"], "beta": warm["beta"], "R": dict(warm["R"])}
    adj = collections.defaultdict(list)
    for i, g in enumerate(G):
        adj[g[1]].append(i)
        adj[g[2]].append(i)
    for t in adj:
        s["R"].setdefault(t, 0.0)
    R = s["R"]
    sw_h = sum(wi * g[3] for wi, g in zip(w, G))
    sw_z = sum(wi * g[6] * g[6] for wi, g in zip(w, G))
    for _n in range(SWEEPS if G else 0):
        old = (s["hfa"], s["beta"], dict(R))
        res = lambda g: g[4] - g[5] - R[g[1]] + R[g[2]]  # noqa: E731
        s["hfa"] = (sum(wi * g[3] * (res(g) - s["beta"] * g[6]) for wi, g in zip(w, G)) / sw_h
                    if sw_h else 0.0)
        s["beta"] = (sum(wi * g[6] * (res(g) - s["hfa"] * g[3]) for wi, g in zip(w, G)) / sw_z
                     if sw_z else 0.0)
        for t, ix in adj.items():
            num = 0.0
            for i in ix:
                g = G[i]
                m = g[4] - g[5] - s["hfa"] * g[3] - s["beta"] * g[6]
                num += w[i] * ((m + R[g[2]]) if g[1] == t else -(m - R[g[1]]))
            R[t] = num / (sum(w[i] for i in ix) + RIDGE)
        moved = max([abs(s["hfa"] - old[0]), abs(s["beta"] - old[1])]
                    + [abs(R[t] - old[2].get(t, 0.0)) for t in adj])
        if moved < TOL:
            break
    s["teams"] = set(adj)
    return s


def talent_margin(s, home, away, neutral, zs):
    if not s or home not in s["teams"] or away not in s["teams"]:
        return None
    return (s["hfa"] * (0.0 if neutral else 1.0) + s["beta"] * (zs.get(home, 0.0) - zs.get(away, 0.0))
            + s["R"][home] - s["R"][away])


# ══════════════════════════════════════════════════════════════════════
# ATTACH AND EXTEND — one input per row, from that row's own Monday
# ══════════════════════════════════════════════════════════════════════
def weekly(items, weeks, solve):
    """{Monday: solve(items dated before it, Monday, last week's answer)}."""
    out, warm, j = {}, None, 0
    for wk in sorted(weeks):
        while j < len(items) and items[j][0] < wk:
            j += 1
        warm = out[wk] = solve(items[:j], wk, warm)
    return out


def attach(name, lg, rows, root=None):
    """Write challenger `name`'s number into every row's `sig` (None: no number)."""
    c = CHALLENGERS[name]
    weeks = {FM.monday(r["day"]) for r in rows}
    if name == "T":
        z = talent_z(root)
        sol = weekly(talent_games(root, z), weeks, solve_talent)
        for r in rows:
            r["sig"][c["key"]] = talent_margin(sol.get(FM.monday(r["day"])), r["home"], r["away"],
                                               r["sig"]["neutral"], z.get(r["season"]) or {})
        return rows
    sol = weekly(epa_entries(root) if name == "E" else ppa_entries(root), weeks, solve_epa)
    for r in rows:
        r["sig"][c["key"]] = epa_margin(sol.get(FM.monday(r["day"])), r["home"], r["away"],
                                        r["sig"]["neutral"])
    return rows


def extend(name, r, market, x, M=None):
    """The inputs with challenger `name` applied. E, P: appended after the
    champion's (spread (margin - line) / 10, moneyline margin / 10). T: its own
    margin replaces the champion's in the first input. Totals unchanged."""
    c = CHALLENGERS[name]
    if market not in c["markets"]:
        return x
    m = r["sig"].get(c["key"])
    M = r["M"] if M is None else M
    v = (0.0 if m is None or M is None else (m - M) / 10.0) if market == "spread" else \
        (0.0 if m is None else m / 10.0)
    return [v] + list(x[1:]) if name == "T" else list(x) + [v]

