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
}
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


def attach(name, lg, rows, root=None):
    """Write challenger `name`'s number into every row's `sig` (None: no number)."""
    c = CHALLENGERS[name]
    if c["key"] is None:                 # S reads only the champion's own inputs
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
    sam_t) / 2 - T) / 10 (unchanged without sam_t); RS, RSC append rest / 7."""
    c = CHALLENGERS[name]
    if market not in c["markets"]:
        return x
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

