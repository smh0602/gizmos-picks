#!/usr/bin/env python3
"""signal9.py — signal 9, "Opportunity change": the ONE implementation of
the expected share, read by the props model, the card, the game model and
the dossier. `research/fb_signal9_spec.md` §3 (Sam, 2026-09-24; frozen
before any scoring).

⛔ ONE COPY (rule 117). Every use reads these functions; none recomputes a
share of its own.
⚠️ STDLIB ONLY.
"""
import gzip
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
K = 4.0                               # ⛔ spec §3: E = (4·s_adj + Σ obs) / (4 + n)
MARKET_CAT = {"player_reception_yds": "tgt", "player_receptions": "tgt",
              "player_rush_yds": "car", "player_anytime_td": "combined"}
CARD_MARKETS = ("player_reception_yds", "player_receptions", "player_rush_yds")  # ⛔ spec §3
PRIOR_GAMES = 17.0                    # ⛔ spec §3: TOT / 17 = the prior per-game volume

# `(league, season) -> opportunity table` supplied by a caller (a scorer
# run on locally computed tables, or a test). Empty in production.
OVERRIDE = {}


def load(lg, season, root=None):
    """The stored opportunity table for (league, season), or None."""
    if (lg, season) in OVERRIDE:
        return OVERRIDE[(lg, season)]
    if lg != "nfl":
        return None                   # college: its CFBD tables, once stored (spec §1)
    try:
        doc = json.load(gzip.open(os.path.join(root or ROOT, "data", lg, "latest",
                                               "players-%d.json.gz" % int(season)), "rt", encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return doc.get("opportunity")


def _week(opp, week):
    ws = [int(w) for w in (opp.get("weeks") or [])]
    if not ws:
        return None
    try:
        w = int(week)
    except (TypeError, ValueError):
        w = max(ws)
    return str(max([x for x in ws if x <= w] or [min(ws)]))


def vacated(opp, team, week, cat):
    """vacated[T][w][cat] share, or None."""
    if not opp:
        return None
    t = (opp.get("teams") or {}).get(team)
    wk = _week(opp, week)
    if not t or wk is None:
        return None
    return (((t.get("weeks") or {}).get(wk) or {}).get(cat) or {}).get("share")


def s_adj(opp, pid, team, week, cat):
    """(s_adj, s25, changed) per spec §3, or None when he has no prior."""
    if not opp:
        return None
    p = (opp.get("players") or {}).get(pid)
    if not p:
        return None
    s25 = (p.get("share25") or {}).get(cat)
    if s25 is None:
        return None
    if p.get("changed"):
        return s25, s25, True
    v = vacated(opp, team, week, cat)
    if v is None or v >= 1.0:
        return s25, s25, False
    return min(1.0, s25 / (1.0 - v)), s25, False


def e_share(adj, obs):
    """E_share = (K·s_adj + Σ obs_i) / (K + n) — spec §3."""
    obs = [o for o in obs if o is not None]
    return (K * adj + sum(obs)) / (K + len(obs))


def team_prior_per_game(opp, team, cat):
    t = (opp or {}).get("teams", {}).get(team) or {}
    tot = (t.get("totals") or {}).get(cat)
    return (tot / PRIOR_GAMES) if tot else None


def card_scale(opp, pid, team, week, market):
    """r = s_adj / s25 for the card's volume markets (1 otherwise)."""
    cat = MARKET_CAT.get(market)
    if market not in CARD_MARKETS or not cat:
        return 1.0
    a = s_adj(opp, pid, team, week, cat)
    if not a or a[2] or not a[1]:
        return 1.0
    return a[0] / a[1]


def team_vacated_combined(opp, team, week):
    """V for the game model: vacated targets + carries, as a share."""
    return vacated(opp, team, week, "combined")


def week_of(lg, day, root=None):
    """The league week a card dated `day` is for: the first week whose last
    game is on or after that day (schedule file). None when unknown.
    ⛔ Point in time: a week-1 card must read week-1 roster status, never a
    later week's."""
    try:
        d = json.load(gzip.open(os.path.join(root or ROOT, "data", lg, "latest",
                                             "schedule-%s.json.gz" % str(day)[:4]), "rt", encoding="utf-8"))
    except (OSError, ValueError):
        return None
    last = {}
    for g in d.get("games") or []:
        w, s = g.get("week"), (g.get("start") or "")[:10]
        if isinstance(w, int) and s:
            last[w] = max(last.get(w, ""), s)
    later = [w for w, s in last.items() if s >= str(day)[:10]]
    return min(later) if later else None
