#!/usr/bin/env python3
"""fb_challengers.py — the football game model's frozen CHALLENGERS (T65,
`research/fb_refit_spec.md`, pre-registered 2026-10-12 before any result).

    E  NFL      the opponent-adjusted EPA margin (nflverse, def-epa-<season>)
    P  college  the same, from CFBD /plays `ppa` (ppa-<season>, cfb.py)
    T  college  CFBD /talent, z-scored per season, one unpenalised term in
                the champion's margin solve (talent-<season>, cfb.py)
    S  NFL      T66: the champion's inputs WITHOUT head-to-head and signal 9
    AV NFL / AVC college   T68: Sam's averages (points for and against per game)
    WX NFL / WXC college   T68: the NWS kickoff wind, totals only
    IN NFL                 T69: injuries on both sides of the ball (Out/Doubtful,
                           weighted by snap share; starting QB out)
    AT NFL / ATC college   T69: Sam's averages blended into the total
    RS NFL / RSC college   T69: rest days
    H NFL / HC college     T70: own ratings, neutral, dome, trained on more seasons
    SM NFL / SMC college   T71: the score-first model's predicted margin and total
                           (the score-first model), the only input
    CL NFL / CLC college   T72: class, how a team does against above-average
                           opponents beyond what its rating says
    WL NFL / WLC college   T72: the resume, a win-loss (Bradley-Terry) rating
    MC NFL / MCC college   T72: the champion's margin with blowouts capped (21 / 28)
    AJ NFL / AJC college   T72: form and the defence rank, opponent-adjusted
    TS college  T66: T's talent margin in place of the own margin, and only
                the line, neutral and dome beside it

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
import bisect
import math
import os
import statistics

import fb_model as FM

HALF_LIFE = FM.RATING_HALF_LIFE      # 150 days, the champion's weights
RIDGE = FM.RATING_RIDGE              # 1 on every team term
TOL, SWEEPS = FM.RATING_TOL, FM.RATING_SWEEPS

CHALLENGERS = {
    "E": {"league": "nfl", "what": "EPA", "markets": ("spread", "moneyline"),
          "files": ("def-epa-{s}.json.gz",), "key": "epa_m", "withdrawable": False,
          "input": ("def-epa-{s}.json.gz", "possession")},
    "P": {"league": "ncaaf", "what": "PPA", "markets": ("spread", "moneyline"),
          "files": ("ppa-{s}.json.gz",), "key": "ppa_m", "withdrawable": True,
          "input": ("ppa-{s}.json.gz", "possession")},
    "T": {"league": "ncaaf", "what": "talent", "markets": ("spread", "moneyline"),
          "files": ("talent-{s}.json.gz",), "key": "tal_m", "withdrawable": True,
          # written once a season: stale only when the season's file is missing
          "input": ("talent-{s}.json.gz", None)},
    # `[2026-10-14]` T66 (research/fb_refit_spec.md §3a), pre-registered by Cowork.
    #    ⚠️ Designed AFTER Cowork saw their history, so only games after
    #    `registered_from` count, as for every challenger. No withdrawal rule.
    "S": {"league": "nfl", "what": "fewer inputs", "markets": ("spread", "total", "moneyline"),
          "files": (), "key": None, "withdrawable": False, "input": None,
          "registered_from": "2026-10-19"},
    "TS": {"league": "ncaaf", "what": "talent, few inputs", "markets": ("spread", "total", "moneyline"),
           "files": ("talent-{s}.json.gz",), "key": "tal_m", "withdrawable": False,
           "input": ("talent-{s}.json.gz", None), "registered_from": "2026-10-19"},
    # `[Sam, 2026-10-15]` T68 (research/fb_refit_spec.md §3b), pre-registered by
    #    Cowork: Sam's predicted-scores formula and the weather, "just apart of the
    #    model". Only games after `registered_from` count. No withdrawal rule.
    "AV": {"league": "nfl", "what": "Sam's averages", "markets": ("spread", "total", "moneyline"),
           "files": (), "key": "sam_m", "withdrawable": False, "input": None,
           "registered_from": "2026-10-19"},
    "AVC": {"league": "ncaaf", "what": "Sam's averages", "markets": ("spread", "total", "moneyline"),
            "files": (), "key": "sam_m", "withdrawable": False, "input": None,
            "registered_from": "2026-10-19"},
    # no 2025 forecasts exist: registration looks only at `seasons`
    "WX": {"league": "nfl", "what": "weather", "markets": ("total",), "files": ("weather-{s}.json.gz",),
           "seasons": (2026,), "key": "wx_wind", "withdrawable": False,
           "input": ("weather-{s}.json.gz", "possession"), "registered_from": "2026-10-19"},
    "WXC": {"league": "ncaaf", "what": "weather", "markets": ("total",), "files": ("weather-{s}.json.gz",),
            "seasons": (2026,), "key": "wx_wind", "withdrawable": False,
            "input": ("weather-{s}.json.gz", "possession"), "registered_from": "2026-10-19"},
    # `[Sam, 2026-10-15]` T69 (research/fb_refit_spec.md §3c): "do all changes";
    #    "injuries should've always been a factor on both sides of the ball".
    "IN": {"league": "nfl", "what": "injuries, both sides", "markets": ("spread", "total", "moneyline"),
           "files": ("injuries-{s}.json.gz",), "key": "inj", "withdrawable": False,
           "input": ("injuries-{s}.json.gz", "possession"), "registered_from": "2026-10-19"},
    "AT": {"league": "nfl", "what": "Sam's averages, totals", "markets": ("total",), "files": (),
           "key": "sam_t", "withdrawable": False, "input": None, "registered_from": "2026-10-19"},
    "ATC": {"league": "ncaaf", "what": "Sam's averages, totals", "markets": ("total",), "files": (),
            "key": "sam_t", "withdrawable": False, "input": None, "registered_from": "2026-10-19"},
    "RS": {"league": "nfl", "what": "rest", "markets": ("spread", "moneyline"), "files": (),
           "key": "rest_d", "withdrawable": False, "input": None, "registered_from": "2026-10-19"},
    "RSC": {"league": "ncaaf", "what": "rest", "markets": ("spread", "moneyline"), "files": (),
            "key": "rest_d", "withdrawable": False, "input": None, "registered_from": "2026-10-19"},
    # `[Sam, 2026-10-15]` T70 (§3d): trained on the history seasons too (fb_history.py).
    "H": {"league": "nfl", "what": "more seasons", "markets": ("spread", "total", "moneyline"),
          "files": ("../history/schedule-{s}.json.gz",), "seasons": (2018, 2019, 2020, 2021, 2022, 2023, 2024),
          "key": "h_own", "withdrawable": False, "input": None, "registered_from": "2026-10-19",
          "history": True},
    "HC": {"league": "ncaaf", "what": "more seasons", "markets": ("spread", "total", "moneyline"),
           "files": ("../history/schedule-{s}.json.gz", "../history/lines-{s}.json.gz"), "seasons": (2023, 2024),
           "key": "h_own", "withdrawable": False, "input": None, "registered_from": "2026-10-19",
           "history": True},
    # `[Sam, 2026-10-16]` T71 (§3e): the score-first model, registered from the first
    #    Monday AFTER the day its entry reaches main (a Monday merge counts from the next
    #    Monday), no earlier than 2026-10-19 (fb_refit.registration).
    "SM": {"league": "nfl", "what": "score model", "markets": ("spread", "total", "moneyline"),
           "files": (), "key": "score", "withdrawable": False, "input": None, "registered_from": "2026-10-19",
           "on_merge": True},
    "SMC": {"league": "ncaaf", "what": "score model", "markets": ("spread", "total", "moneyline"),
            "files": (), "key": "score", "withdrawable": False, "input": None, "registered_from": "2026-10-19",
            "on_merge": True},
    # `[Sam, 2026-10-26]` T72 (§3f), the matchup grade: "make sure the model understands bad
    #    teams and good teams". Registered from the first Monday AFTER the day its entry reaches
    #    main, no earlier than 2026-11-02 (fb_refit.registration). They read only the stored
    #    schedules (AJ / AJC also the player logs fb_matchups reads). No withdrawal rule.
    "CL": {"league": "nfl", "what": "class vs good teams", "markets": ("spread", "total", "moneyline"),
           "files": (), "key": "cl", "withdrawable": False, "input": None, "registered_from": "2026-11-02",
           "on_merge": True},
    "CLC": {"league": "ncaaf", "what": "class vs good teams", "markets": ("spread", "total", "moneyline"),
            "files": (), "key": "cl", "withdrawable": False, "input": None, "registered_from": "2026-11-02",
            "on_merge": True},
    "WL": {"league": "nfl", "what": "win-loss resume", "markets": ("spread", "moneyline"),
           "files": (), "key": "wl", "withdrawable": False, "input": None, "registered_from": "2026-11-02",
           "on_merge": True},
    "WLC": {"league": "ncaaf", "what": "win-loss resume", "markets": ("spread", "moneyline"),
            "files": (), "key": "wl", "withdrawable": False, "input": None, "registered_from": "2026-11-02",
            "on_merge": True},
    "MC": {"league": "nfl", "what": "blowouts capped", "markets": ("spread", "moneyline"),
           "files": (), "key": "mc", "withdrawable": False, "input": None, "registered_from": "2026-11-02",
           "on_merge": True},
    "MCC": {"league": "ncaaf", "what": "blowouts capped", "markets": ("spread", "moneyline"),
            "files": (), "key": "mc", "withdrawable": False, "input": None, "registered_from": "2026-11-02",
            "on_merge": True},
    "AJ": {"league": "nfl", "what": "form and defence adjusted", "markets": ("spread", "total", "moneyline"),
           "files": (), "key": "aj", "withdrawable": False, "input": None, "registered_from": "2026-11-02",
           "on_merge": True},
    "AJC": {"league": "ncaaf", "what": "form and defence adjusted", "markets": ("spread", "total", "moneyline"),
            "files": (), "key": "aj", "withdrawable": False, "input": None, "registered_from": "2026-11-02",
            "on_merge": True},
}
HIST = ("H", "HC")
SCORE = ("SM", "SMC")
SAM = ("AV", "AVC")
AT = ("AT", "ATC")
RS = ("RS", "RSC")
REST_CAP = 14                # ⛔ §3c: days, and the rest of a team with no earlier game
OUT_STATUSES = ("out", "doubtful")       # ⛔ §3c: Questionable is not counted
OFF_POS = {"RB", "FB", "HB", "WR", "TE", "T", "OT", "G", "OG", "C", "OL", "LT", "RT", "LG", "RG"}
DEF_POS = {"DE", "DT", "NT", "DL", "EDGE", "LB", "ILB", "OLB", "MLB", "CB", "S", "SAF", "FS", "SS", "DB"}
WX = ("WX", "WXC")
SAM_MIN_GAMES = 3            # ⛔ §3b: fewer are topped up from the earlier season
SAM_HOME = 1.5               # ⛔ §3b: Sam's home edge, points
# ⛔ T66 §3a, FROZEN: which of the champion's inputs S and TS keep, by index into
#    today's lists (spread / moneyline: own, h2h, form, poss, out, neutral, dome
#    [+ s9 NFL]; total: own_t, h2h_t, form_t, def, neutral, dome [+ s9 NFL]).
#    TS's slot 0 on spread and moneyline is T's talent margin, not the own margin.
KEEP = {"S": {"spread": (0, 2, 3, 4, 5, 6), "moneyline": (0, 2, 3, 4, 5, 6), "total": (0, 2, 3, 4, 5)},
        "TS": {"spread": (0, 5, 6), "moneyline": (0, 5, 6), "total": (0, 4, 5)}}
# ⛔ T72 §3f, FROZEN with CL/CLC, WL/WLC, MC/MCC and AJ/AJC (a change is a new challenger).
CLASS, RESUME, CAPPED, ADJUSTED = ("CL", "CLC"), ("WL", "WLC"), ("MC", "MCC"), ("AJ", "AJC")
CLASS_SHRINK = 10.0          # ⛔ §3f: fixed, not tuned (ten full-weight games against good teams count half)
CAP = {"nfl": 21.0, "ncaaf": 28.0}       # ⛔ §3f: three and four touchdowns, fixed, not tuned
FORM_GAMES, FORM_MIN = 4, 2              # ⛔ §3f: the champion's last 4; fewer than 2 -> 0
DEF_MIN = 10                             # ⛔ §3f: fewer ranked defences -> 0
DEF_UNITS = ("pass_yds", "rush_yds")     # ⛔ §3f: passing plus rushing yards allowed
A_STEP = 64.0                # WL / WLC's solve: the longest step on the home edge (`_home_step`); the
                             #    logistic is flat past |z| ~ 37, so one step crosses any flat stretch
# ⛔ §3f: AJ, AJC, MC and MCC replace inputs at fixed places in today's lists, so they build
#    only against no champion or one that only appends; otherwise NOT APPLICABLE (Sam's to decide).
APPEND_ONLY = ("E", "P", "AV", "AVC", "WX", "WXC", "IN", "RS", "RSC", "CL", "CLC", "WL", "WLC")



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


# ══════════════════════════════════════════════════════════════════════
# AV AND WX (T68 §3b) — Sam's averages, and the kickoff wind
# ══════════════════════════════════════════════════════════════════════
def team_games(lg, root=None):
    """{(season, team): [(day, points for, points against)]} over every final
    scored game in the stored schedules, any opponent, every division, by day."""
    out = {}
    for g in schedule_by_id(lg, root).values():
        if not g.get("final") or g.get("home_score") is None or g.get("away_score") is None:
            continue
        d, h, a = g["start"][:10], float(g["home_score"]), float(g["away_score"])
        out.setdefault((g["season"], g["home"]), []).append((d, h, a))
        out.setdefault((g["season"], g["away"]), []).append((d, a, h))
    for v in out.values():
        v.sort()
    return out


def sam_rates(TG, season, team, wk):
    """(PF, PA) per game from games dated before `wk` in `season`, topped up to
    SAM_MIN_GAMES with the team's latest games of the earlier season. None: none."""
    cur = TG.get((season, team)) or []
    cur = cur[:bisect.bisect_left(cur, (wk,))]
    if len(cur) < SAM_MIN_GAMES:
        prev = [x for x in TG.get((season - 1, team)) or [] if x[0] < wk]
        cur = prev[max(0, len(prev) - (SAM_MIN_GAMES - len(cur))):] + cur if prev else cur
    if not cur:
        return None
    return sum(x[1] for x in cur) / len(cur), sum(x[2] for x in cur) / len(cur)


def sam_numbers(TG, r):
    """(sam_m, sam_t) for one row, or (None, None): §3b."""
    wk = FM.monday(r["day"])
    h, a = sam_rates(TG, r["season"], r["home"], wk), sam_rates(TG, r["season"], r["away"], wk)
    if h is None or a is None:
        return None, None
    hf = 0.0 if r["sig"]["neutral"] else 1.0
    return ((h[0] + a[1] - a[0] - h[1]) / 2.0 + SAM_HOME * hf, (h[0] + a[1] + a[0] + h[1]) / 2.0)


def wx_wind(lg, root=None, season=2026):
    """{game id: wind mph} from weather-<season>'s "last" forecast; indoor -> 0."""
    p = os.path.join(latest(lg, root), "weather-%d.json.gz" % season)
    out = {}
    for gid, e in ((FM.jz(p) or {}).get("games") or {}).items():
        out[str(gid)] = 0.0 if e.get("indoor") else (e.get("last") or {}).get("wind")
    return out


def rest_days(lg, root=None):
    """{team: sorted game days} over every stored schedule, any season (§3c)."""
    out = {}
    for g in schedule_by_id(lg, root).values():
        for t in (g["home"], g["away"]):
            out.setdefault(t, []).append(g["start"][:10])
    return {t: sorted(set(v)) for t, v in out.items()}


def rest_of(days, team, day):
    prev = [d for d in days.get(team) or [] if d < day]
    if not prev:
        return REST_CAP
    gap = (datetime.date.fromisoformat(day) - datetime.date.fromisoformat(prev[-1])).days
    return min(REST_CAP, gap)


def injury_tables(root=None):
    """(reports, logs): reports {(season, team, week): [players]}, logs {gsis:
    [(day, team, snap_pct, att, def_pct)] by day} — §3c's two inputs."""
    reports, logs = {}, {}
    for s in FM.SEASONS:
        doc = FM.jz(os.path.join(latest("nfl", root), "injuries-%d.json.gz" % s)) or {}
        for team, weeks in (doc.get("teams") or {}).items():
            for wk, v in weeks.items():
                reports[(s, team, str(wk))] = v.get("players") or []
        P = (FM.jz(os.path.join(latest("nfl", root), "players-%d.json.gz" % s)) or {}).get("players") or {}
        for gid, p in P.items():
            for g in p.get("g") or []:
                logs.setdefault(gid, []).append((g.get("d") or "", g.get("team"), g.get("snap_pct") or 0.0,
                                                 g.get("att") or 0.0, g.get("def_pct") or 0.0))
    for v in logs.values():
        v.sort()
    return reports, logs


def team_out(reports, logs, team_qb, season, team, week, day):
    """(qb_out, off_out, def_out) for one team and game: §3c."""
    listed = [p for p in reports.get((season, team, str(week))) or []
              if (p.get("report_status") or "").strip().lower() in OUT_STATUSES]
    qb = team_qb(team, day)
    qb_out, off, dfn = 0.0, 0.0, 0.0
    for p in listed:
        gid, pos = p.get("gsis_id"), (p.get("position") or "").upper()
        if pos == "QB":
            qb_out = 1.0 if gid and gid == qb else qb_out
            continue
        k = 4 if pos in DEF_POS else 2   # a defender's DEFENSIVE snap share
        last = [x[k] for x in logs.get(gid) or [] if x[1] == team and x[0] < day][-3:]
        w = sum(last) / len(last) if last else 0.0
        if pos in OFF_POS:
            off += w
        elif pos in DEF_POS:
            dfn += w
    return qb_out, off, dfn


def history_rating_games(lg, root=None):
    """fb_model.rating_games' tuples for the history seasons (fb_history.py)."""
    import fb_history
    out = []
    for g in fb_history.games(lg, root):
        if (g.get("final") and FM.t60r.kick(g) is not None and g.get("home_score") is not None
                and g.get("away_score") is not None):
            out.append((g["start"][:10], g["home"], g["away"], 0.0 if g.get("neutral") else 1.0,
                        float(g["home_score"]), float(g["away_score"])))
    return out


def h_own(lg, rows, root=None):
    """§3d: each row's own margin and total from the frozen own-ratings solve over
    `latest/` AND `history/` (one copy per date, home, away)."""
    G = sorted(set(FM.rating_games(lg, root)) | set(history_rating_games(lg, root)))
    own = FM.own_ratings(G, {FM.monday(r["day"]) for r in rows})
    for r in rows:
        r["sig"]["h_own"] = FM.own_numbers(own.get(FM.monday(r["day"])), r["home"], r["away"],
                                           r["sig"]["neutral"])
    return rows


def history_rows(lg, root=None):
    """§3d: one training row per final history game (college FBS vs FBS), labelled
    at its closing line by fb_model.training_line, with its own numbers."""
    import fb_history
    cfb = fb_history.lines(root) if lg == "ncaaf" else None
    out = []
    for g in fb_history.games(lg, root):
        k = FM.t60r.kick(g)
        if (k is None or not g.get("final") or g.get("home_score") is None or g.get("away_score") is None
                or (lg == "ncaaf" and not (g.get("home_class") == "fbs" and g.get("away_class") == "fbs"))):
            continue
        M, T, pml = FM.training_line(g, None, cfb)
        out.append({"id": "hist:%s" % g.get("id"), "lg": lg, "season": g.get("season"),
                    "day": k.strftime("%Y-%m-%d"), "kick": g["start"], "week": g.get("week"),
                    "home": g["home"], "away": g["away"], "final": True,
                    "hs": g["home_score"], "as": g["away_score"], "M": M, "T": T, "pml": pml,
                    "snap": None, "dk_ml": None, "close": {},
                    "sig": {"h2h_m": None, "h2h_t": None, "form_m": None, "form_t": None, "def": None,
                            "poss": None, "out": None, "vac_h": None, "vac_a": None,
                            "neutral": 1.0 if g.get("neutral") else 0.0,
                            "dome": 1.0 if (g.get("roof") or "") in ("dome", "closed") else 0.0,
                            "own_m": None, "own_t": None}})
    return h_own(lg, sorted(out, key=lambda r: r["kick"]), root)


# ══════════════════════════════════════════════════════════════════════
# T72 (§3f) — THE MATCHUP GRADE: who a team has played. `[Sam, 2026-10-26]`
# "make sure the model understands bad teams and good teams."
# ⛔ s, a row's ratings, is the champion's own-ratings solve for the row's Monday,
#    made exactly as fb_model.build_rows makes it (`own_solve`); "a team's games" are
#    that solve's games (fb_model.rating_games dated before the Monday), each with its
#    weight 0.5 ** (days / 150). Nothing dated on or after the row's Monday is read.
# ══════════════════════════════════════════════════════════════════════
def own_solve(lg, rows, root=None):
    """(games, {Monday: s}) for every row's Monday: fb_model.own_ratings over
    fb_model.rating_games, as build_rows solves it."""
    G = FM.rating_games(lg, root)
    return G, FM.own_ratings(G, {FM.monday(r["day"]) for r in rows})


def before(G, wk):
    """The games of G (sorted by day) dated before Monday `wk`."""
    return G[:bisect.bisect_left(G, (wk,))]


def class_numbers(G, wk, s, good):
    """CL / CLC: {team: (C, CO, CD)} at Monday `wk` from its games G. Over a team's games
    against an above-average opponent (`good`, fb_model.above_average), the weighted
    residual against what s says, / (the summed weights + 10); no such game -> 0.
    f = +1 when the team was at home at a non-neutral site, -1 when the opponent was, 0."""
    num = collections.defaultdict(lambda: [0.0, 0.0, 0.0])
    den = collections.defaultdict(lambda: [0.0, 0.0, 0.0])
    R, O, D = s["R"], s["O"], s["D"]
    for d, h, a, hf, hp, ap in G:
        w = weight(d, wk)
        for t, o, f, pf, pa in ((h, a, hf, hp, ap), (a, h, -hf, ap, hp)):
            if o in good["R"]:           # C: margin class
                num[t][0] += w * ((pf - pa) - (s["hfa"] * f + R[t] - R[o]))
                den[t][0] += w
            if o in good["D"]:           # CO: offence class, against a good defence
                num[t][1] += w * (pf - (s["base"] + s["hpe"] * (1.0 if f > 0 else 0.0) + O[t] - D[o]))
                den[t][1] += w
            if o in good["O"]:           # CD: defence class (points allowed), against a good offence
                num[t][2] += w * (pa - (s["base"] + s["hpe"] * (1.0 if f < 0 else 0.0) + O[o] - D[t]))
                den[t][2] += w
    return {t: tuple(n / (dn + CLASS_SHRINK) for n, dn in zip(num[t], den[t])) for t in s["teams"]}


def class_row(s, good, C, home, away):
    """(cl_m, cl_t) for one game, or None when either team is not in s (its inputs are 0)."""
    if not s or home not in s["teams"] or away not in s["teams"]:
        return None
    ab = lambda k, t: 1.0 if t in good[k] else 0.0  # noqa: E731
    (c_h, co_h, cd_h), (c_a, co_a, cd_a) = C[home], C[away]
    return (c_h * ab("R", away) - c_a * ab("R", home),
            co_h * ab("D", away) + cd_a * ab("O", home) + co_a * ab("D", home) + cd_h * ab("O", away))


def _p(x):
    """The logistic, without overflow at either end."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def _softplus(x):
    """log(1 + exp(x)), without overflow at either end."""
    return x + math.log1p(math.exp(-x)) if x > 0 else math.log1p(math.exp(x))


def _home_fit(a, G, w, y, B):
    """WL / WLC: the part of the fit that moves with the home edge a,
    sum(w (y log p + (1 - y) log(1 - p))) over the games with a home side
    (log p = -softplus(-z), log(1 - p) = -softplus(z))."""
    out = 0.0
    for wi, yi, g in zip(w, y, G):
        if g[3]:
            z = a * g[3] + B[g[1]] - B[g[2]]
            out -= wi * (yi * _softplus(-z) + (1.0 - yi) * _softplus(z))
    return out


def _home_step(num, den, a, G, w, y, B):
    """WL / WLC: the Newton step on the home edge a (num = the fit's slope in a, den = minus
    its curve). 🔴 `[2026-10-26]` A long one is not trusted. Where the fit is flat in a,
    every home side's p is ~1 or ~0 and num / den is ~1e15 or infinite: warm-started from a
    Monday whose non-neutral games were all home wins (a ran to ~37, no finite best), a
    landed at -2e15, every p became exactly 0, den 0, and a never moved again, every later
    Monday (a planted league; no stored Monday had that shape). So a step of 1 or more is at
    most A_STEP long and halved until the fit is no worse; a shorter one is Newton's,
    unchanged. ⛔ The maximum §3f names is the same; only the path to it is safe."""
    if not num:
        return 0.0
    step = math.copysign(min(abs(num) / den if den > 0 else math.inf, A_STEP), num)
    if abs(step) >= 1.0:
        here = _home_fit(a, G, w, y, B)
        while abs(step) >= 1.0 and _home_fit(a + step, G, w, y, B) < here:
            step /= 2.0
    return step


def solve_resume(G, wk, warm=None):
    """WL / WLC: the weighted Bradley-Terry fit on games G (all dated before Monday `wk`):
    P(home side wins) = 1 / (1 + exp(-(a x h + B_home - B_away))), h = 0 at a neutral site;
    y = 1 home win, 0 away win, 0.5 a tie; ⛔ the score margin is never read. It maximises
    sum(w (y log p + (1 - y) log(1 - p))) - 0.5 sum(B ^ 2) (ridge 1 on every team term, none
    on a): one Newton step per number per sweep, a first, then each team in the champion's
    order, until no number moves 1e-10 or the champion's sweep cap; warm-started. A step on
    a of 1 or more is checked first (`_home_step`): a warm start from a flat fit must not
    throw it away. ⚠️ A Monday whose non-neutral games all went one way has no finite best
    a (§3f does not say what it gives): a runs until every p rounds to 1 (or 0) and stops."""
    w = [weight(g[0], wk) for g in G]
    y = [1.0 if g[4] > g[5] else 0.0 if g[4] < g[5] else 0.5 for g in G]
    s = {"a": warm["a"], "B": dict(warm["B"])} if warm else {"a": 0.0, "B": {}}
    adj = collections.defaultdict(list)
    for i, g in enumerate(G):
        adj[g[1]].append(i)
        adj[g[2]].append(i)
    for t in adj:
        s["B"].setdefault(t, 0.0)
    B = s["B"]
    for _n in range(SWEEPS if G else 0):
        old = (s["a"], dict(B))
        num = den = 0.0
        for wi, yi, g in zip(w, y, G):
            if g[3]:
                p = _p(s["a"] * g[3] + B[g[1]] - B[g[2]])
                num += wi * g[3] * (yi - p)
                den += wi * g[3] * g[3] * p * (1.0 - p)
        s["a"] += _home_step(num, den, s["a"], G, w, y, B)
        for t, ix in adj.items():
            num, den = -RIDGE * B[t], RIDGE
            for i in ix:
                g = G[i]
                p = _p(s["a"] * g[3] + B[g[1]] - B[g[2]])
                num += w[i] * ((y[i] - p) if g[1] == t else (p - y[i]))
                den += w[i] * p * (1.0 - p)
            B[t] += num / den
        moved = max([abs(s["a"] - old[0])] + [abs(B[t] - old[1][t]) for t in adj])
        if moved < TOL:
            break
    s["teams"] = set(adj)
    return s


def resume_margin(s, home, away, neutral):
    """wl = a x h + B_home - B_away, or None when either team has no earlier game."""
    if not s or home not in s["teams"] or away not in s["teams"]:
        return None
    return s["a"] * (0.0 if neutral else 1.0) + s["B"][home] - s["B"][away]


def capped_games(lg, root=None):
    """MC / MCC: the champion's games with each margin capped at +/- CAP[lg], in
    `solve_talent`'s shape with no talent gap: beta stays 0, so its solve is the champion's
    margin equation alone (the same weights, ridge 1 on R only, tolerance and sweep cap)."""
    cap = CAP[lg]
    return [(d, h, a, f, max(-cap, min(cap, hp - ap)), 0.0, 0.0) for d, h, a, f, hp, ap in FM.rating_games(lg, root)]


def game_reads(g, t, s):
    """AJ / AJC: one game of team t read against s -> (rating, offence, defence):
    t's margin - hfa x f + R_o; t's points - hpe x [t home, not neutral] + D_o - base;
    base + hpe x [o home, not neutral] + O_o - the points t allowed."""
    _d, h, a, hf, hp, ap = g
    o, f, pf, pa = (a, hf, hp, ap) if t == h else (h, -hf, ap, hp)
    return ((pf - pa) - s["hfa"] * f + s["R"][o],
            pf - s["hpe"] * (1.0 if f > 0 else 0.0) + s["D"][o] - s["base"],
            s["base"] + s["hpe"] * (1.0 if f < 0 else 0.0) + s["O"][o] - pa)


def adjusted_form(by_team, wk, s, home, away, neutral):
    """AJ / AJC: (form_m, form_t) from each team's last 4 games before Monday `wk` (any
    stored season), read against s; None when either team has fewer than 2."""
    reads = []
    for t in (home, away):
        gs = by_team.get(t) or []
        last = gs[:bisect.bisect_left(gs, (wk,))][-FORM_GAMES:]
        if len(last) < FORM_MIN:
            return None
        v = [game_reads(g, t, s) for g in last]
        reads.append([sum(x[k] for x in v) / len(v) for k in range(3)])
    (rr_h, or_h, dr_h), (rr_a, or_a, dr_a) = reads
    h = 0.0 if neutral else 1.0
    return (s["hfa"] * h + rr_h - rr_a,
            (s["base"] + s["hpe"] * h + or_h - dr_a) + (s["base"] + or_a - dr_h))


def def_fractions(tables, wk):
    """AJ / AJC: {defence: rank fraction} at Monday `wk`: opponent-adjusted passing plus
    rushing yards allowed per game (fb_matchups.Tables.unit_allowed), among every team both
    tables carry; rank = 1 + the number allowing more; fraction = rank / teams ranked.
    {} when fewer than 10 are ranked."""
    teams = set.intersection(*(tables.solve(u, wk)["teams"] for u in DEF_UNITS))
    if len(teams) < DEF_MIN:
        return {}
    allow = {t: sum(tables.unit_allowed(t, u, wk) for u in DEF_UNITS) for t in teams}
    v = sorted(allow.values())
    return {t: (1 + len(v) - bisect.bisect_right(v, x)) / float(len(v)) for t, x in allow.items()}


def attach_grade(name, lg, rows, root=None):
    """T72's numbers for every row, from that row's own Monday: `cl` (cl_m, cl_t), `wl`,
    `mc` (the capped margin) or `aj` ({"form": (form_m, form_t), "def": fraction}); None
    (or a None part) is no number, an input of 0."""
    weeks = {FM.monday(r["day"]) for r in rows}
    if name in RESUME:
        sol = weekly(FM.rating_games(lg, root), weeks, solve_resume)
        for r in rows:
            r["sig"]["wl"] = resume_margin(sol.get(FM.monday(r["day"])), r["home"], r["away"],
                                           r["sig"]["neutral"])
        return rows
    if name in CAPPED:
        sol = weekly(capped_games(lg, root), weeks, solve_talent)
        for r in rows:
            r["sig"]["mc"] = talent_margin(sol.get(FM.monday(r["day"])), r["home"], r["away"],
                                           r["sig"]["neutral"], {})
        return rows
    G, own = own_solve(lg, rows, root)
    if name in CLASS:
        fbs = FM.fbs_teams(root) if lg == "ncaaf" else None
        per = {}
        for wk in sorted(weeks):
            s = own.get(wk)
            good = FM.above_average(s, lg, fbs)
            per[wk] = (s, good, class_numbers(before(G, wk), wk, s, good))
        for r in rows:
            r["sig"]["cl"] = class_row(*per[FM.monday(r["day"])], r["home"], r["away"])
        return rows
    import fb_matchups                   # AJ / AJC: the tables SM / SMC read, frozen with them (§3e)
    tables = fb_matchups.Tables(lg, root)
    fr = {wk: def_fractions(tables, wk) for wk in sorted(weeks)}      # oldest first: warm starts
    by_team = {}
    for g in G:
        by_team.setdefault(g[1], []).append(g)
        by_team.setdefault(g[2], []).append(g)
    for r in rows:
        wk = FM.monday(r["day"])
        f = fr[wk]
        r["sig"]["aj"] = {
            "form": adjusted_form(by_team, wk, own.get(wk), r["home"], r["away"], r["sig"]["neutral"]),
            "def": (f[r["home"]] + f[r["away"]]) / 2.0 if r["home"] in f and r["away"] in f else None}
    return rows


def attach(name, lg, rows, root=None):
    """Write challenger `name`'s number into every row's `sig` (None: no number)."""
    c = CHALLENGERS[name]
    if c["key"] is None:                 # S reads only the champion's own inputs
        return rows
    if name in HIST:
        return h_own(lg, rows, root)
    if name in CLASS + RESUME + CAPPED + ADJUSTED:     # T72 §3f
        return attach_grade(name, lg, rows, root)
    if name in SCORE:                    # §3e: fb_score_model's own walk-forward, as merged in #275
        import fb_matchups
        import fb_score_model
        done = fb_score_model.walk_forward(rows, fb_matchups.Tables(lg, root))
        got = {id(p["row"]): (p["margin"], p["total"]) for p in done}
        for r in rows:
            r["sig"]["score"] = got.get(id(r))
        return rows
    if name in RS:
        days = rest_days(lg, root)
        for r in rows:
            r["sig"]["rest_d"] = rest_of(days, r["home"], r["day"]) - rest_of(days, r["away"], r["day"])
        return rows
    if name == "IN":
        reports, logs = injury_tables(root)
        games = {}                       # (team, day) -> [(gsis, att)]
        for gid, v in logs.items():
            for d, t, _sp, att, _dp in v:
                games.setdefault((t, d), []).append((gid, att))
        by_team = {}
        for t, d in games:
            by_team.setdefault(t, []).append(d)
        for v in by_team.values():
            v.sort()

        def team_qb(team, day):
            prev = [d for d in by_team.get(team) or [] if d < day]
            if not prev:
                return None
            best = max(games[(team, prev[-1])], key=lambda x: x[1])
            return best[0] if best[1] > 0 else None
        for r in rows:
            h = team_out(reports, logs, team_qb, r["season"], r["home"], r.get("week"), r["day"])
            a = team_out(reports, logs, team_qb, r["season"], r["away"], r.get("week"), r["day"])
            r["sig"]["inj"] = {"qb": (h[0], a[0]), "off": (h[1], a[1]), "def": (h[2], a[2])}
        return rows
    if name in SAM or name in AT:
        TG = team_games(lg, root)
        for r in rows:
            r["sig"]["sam_m"], r["sig"]["sam_t"] = sam_numbers(TG, r)
        return rows
    if name in WX:
        w = wx_wind(lg, root)
        for r in rows:
            r["sig"]["wx_wind"] = w.get(str(r["id"]))
        return rows
    weeks = {FM.monday(r["day"]) for r in rows}
    if name in ("T", "TS"):
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


def applies(name, r):
    """`[2026-10-16]` Can challenger `name`'s frozen inputs be built against the current
    CHAMPION? S's and TS's (§3a) are indexes into today's champion's lists; H, HC, SM
    and SMC as champion have shorter ones, so there they cannot (fb_refit reports NOT
    APPLICABLE; how S and TS should read then is Sam's to decide).
    `[Sam, 2026-10-26]` T72 (§3f): AJ, AJC, MC and MCC replace inputs at fixed places in
    today's lists, so they build only against no champion or one that only appends
    (APPEND_ONLY); CL, CLC, WL and WLC only append, so they always build."""
    if name in CAPPED + ADJUSTED:
        ch = FM.CHAMPION.get(r.get("lg") or CHALLENGERS[name]["league"])
        return ch is None or ch in APPEND_ONLY
    if name not in KEEP:
        return True
    return all(max(KEEP[name][mk]) < len(FM.features(r, mk)) for mk in CHALLENGERS[name]["markets"])


def extend(name, r, market, x, M=None, T=None):
    """The inputs with challenger `name` applied. E, P: appended after the
    champion's (spread (margin - line) / 10, moneyline margin / 10). T: its own
    margin replaces the champion's in the first input. Totals unchanged.
    S, TS (T66): only the KEEP inputs; TS's first spread / moneyline input is
    T's margin (spread (margin - line) / 10, moneyline margin / 10).
    AV, AVC (T68): one input appended, spread (sam_m - line) / 10, moneyline
    sam_m / 10, total (sam_t - T) / 10 at the total line priced. WX, WXC: totals
    only, wind / 10. A missing number is 0.
    T69: IN appends (away - home) qb/off/def outs on spread and moneyline, their
    sums on totals; AT, ATC replace the first total input with ((own total +
    sam_t) / 2 - T) / 10 (unchanged without sam_t); RS, RSC append rest / 7.
    T70: H, HC are [own term (history ratings), neutral, dome] in every market.
    T71: SM, SMC are ONLY the score model's term: spread (m - line) / 10, moneyline
    m / 10, total (t - line) / 10.
    T72 (§3f): CL, CLC append cl_m / 10 (spread, moneyline) or cl_t / 10 (total); WL, WLC
    append wl (spread, moneyline); MC, MCC put the capped margin in the first input
    (spread (capped - line) / 10, moneyline capped / 10); AJ, AJC put the adjusted form in
    the third (index 2: (form_m - line) / 10, form_m / 10, (form_t - line) / 10) and the
    adjusted defence rank in the total's fourth (index 3: (fraction - 0.5) x 4)."""
    c = CHALLENGERS[name]
    if market not in c["markets"]:
        return x
    if name in CLASS:
        v = r["sig"].get("cl")
        return list(x) + [0.0 if v is None else v[1 if market == "total" else 0] / 10.0]
    if name in RESUME:
        v = r["sig"].get("wl")
        return list(x) + [0.0 if v is None else v]
    if name in CAPPED + ADJUSTED:
        M = r["M"] if M is None else M
        T = r["T"] if T is None else T
    if name in CAPPED:
        m = r["sig"].get("mc")
        first = (0.0 if m is None or M is None else (m - M) / 10.0) if market == "spread" else \
            (0.0 if m is None else m / 10.0)
        return [first] + list(x[1:])
    if name in ADJUSTED:
        aj = r["sig"].get("aj") or {}
        fm, ft = aj.get("form") or (None, None)
        x = list(x)
        x[2] = ((0.0 if fm is None or M is None else (fm - M) / 10.0) if market == "spread" else
                (0.0 if ft is None or T is None else (ft - T) / 10.0) if market == "total" else
                (0.0 if fm is None else fm / 10.0))
        if market == "total":
            x[3] = 0.0 if aj.get("def") is None else (aj["def"] - 0.5) * 4.0
        return x
    if name in HIST:
        om, ot = r["sig"].get("h_own") or (None, None)
        M = r["M"] if M is None else M
        T = r["T"] if T is None else T
        v = ((0.0 if om is None or M is None else (om - M) / 10.0) if market == "spread" else
             (0.0 if ot is None or T is None else (ot - T) / 10.0) if market == "total" else
             (0.0 if om is None else om / 10.0))
        return [v, r["sig"]["neutral"], r["sig"]["dome"]]
    if name in SCORE:
        m, t = r["sig"].get("score") or (None, None)
        M = r["M"] if M is None else M
        T = r["T"] if T is None else T
        return [(0.0 if m is None or M is None else (m - M) / 10.0) if market == "spread" else
                (0.0 if t is None or T is None else (t - T) / 10.0) if market == "total" else
                (0.0 if m is None else m / 10.0)]
    if name in KEEP:
        x = [x[i] for i in KEEP[name][market]]
        if name == "S" or market == "total":
            return x
    m = r["sig"].get(c["key"])
    M = r["M"] if M is None else M
    T = r["T"] if T is None else T
    if name in SAM and market == "total":
        t = r["sig"].get("sam_t")
        return list(x) + [0.0 if t is None or T is None else (t - T) / 10.0]
    if name in AT:
        t, ot = r["sig"].get("sam_t"), r["sig"].get("own_t")
        if t is None or ot is None or T is None:
            return x
        return [((ot + t) / 2.0 - T) / 10.0] + list(x[1:])
    if name in RS:
        return list(x) + [0.0 if m is None else m / 7.0]
    if name == "IN":
        j = m or {"qb": (0.0, 0.0), "off": (0.0, 0.0), "def": (0.0, 0.0)}
        if market == "total":
            return list(x) + [sum(j["qb"]), sum(j["off"]), sum(j["def"])]
        return list(x) + [j["qb"][1] - j["qb"][0], j["off"][1] - j["off"][0], j["def"][1] - j["def"][0]]
    v = (0.0 if m is None or M is None else (m - M) / 10.0) if market == "spread" else \
        (0.0 if m is None else m / 10.0)
    return [v] + list(x[1:]) if name in ("T", "TS") else list(x) + [v]

