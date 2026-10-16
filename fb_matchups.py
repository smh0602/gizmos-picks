#!/usr/bin/env python3
"""fb_matchups.py — THE SHARED FOOTBALL TEAM-UNIT TABLES. `[Sam, 2026-10-15]`

"how teams play against certain stats like passing rushing receiving ... this can
tie directly into player props, finding out opposing teams weaknesses". Per league,
team and week: points, passing, rushing and receiving yards by position, plays
(pace), NFL targets by position, each FOR and ALLOWED, adjusted for the opponents
faced. Settings: research/fb_score_model_design.md §1 (fixed before any backtest).
    tables = fb_matchups.load("nfl")
    tables.unit_for("KC", "pass_yds", "2026-10-15")      # per game vs an average defence
    tables.unit_allowed("KC", "pass_yds", "2026-10-15")  # per game vs an average offence
    tables.expect("KC", "BUF", "rush_yds", "2026-10-15", home=True)

⛔ ONE SOLVER: the weighting, shrinkage and point-in-time cut are
`fb_model.solve_ratings`'s points equations, reused, never copied (rule 117).
⛔ POINT IN TIME: "as of" a day reads only games dated before that day's Monday.
⛔ It feeds no pick, chance, card row or page; the score-first model reports with it.
⚠️ STDLIB ONLY.
"""
import collections
import glob
import os
import re

import fb_model as F

ROOT = os.path.dirname(os.path.abspath(__file__))
POSITIONS = ("WR", "TE", "RB")
UNITS = ("points", "pass_yds", "rush_yds", "rec_yds_WR", "rec_yds_TE", "rec_yds_RB",
         "plays", "pass_att", "rush_car")
NFL_UNITS = UNITS + ("tgt_WR", "tgt_TE", "tgt_RB")      # college logs carry no targets
UNIT_TOL = 1e-7                                         # design §1; points keep fb_model's 1e-10


def units(lg):
    return NFL_UNITS if lg == "nfl" else UNITS


def seasons(lg, root=None):
    """Every season with a stored schedule."""
    return sorted(int(m.group(1)) for p in glob.glob(os.path.join(
        root or ROOT, "data", lg, "latest", "schedule-*.json.gz"))
        if (m := re.search(r"schedule-(\d{4})\.json\.gz$", p)))


def team_games(lg, root=None):
    """{game_id: {team: Counter(unit -> that offence's total in that game)}}
    from every stored players-<season> log of a season with a schedule."""
    out = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for s in seasons(lg, root):
        doc = F.jz(os.path.join(root or ROOT, "data", lg, "latest", "players-%d.json.gz" % s)) or {}
        for pl in (doc.get("players") or {}).values():
            for g in pl.get("g") or []:
                if not g.get("game_id") or not g.get("team"):
                    continue
                c = out[str(g["game_id"])][g["team"]]
                pos = g.get("pos") or pl.get("pos")
                c["pass_yds"] += float(g.get("pass_yds") or 0)
                c["rush_yds"] += float(g.get("rush_yds") or 0)
                c["pass_att"] += float(g.get("att") or 0)
                c["rush_car"] += float(g.get("car") or 0)
                if pos in POSITIONS:
                    c["rec_yds_" + pos] += float(g.get("rec_yds") or 0)
                    c["tgt_" + pos] += float(g.get("tgt") or 0)
    for teams in out.values():
        for c in teams.values():
            c["plays"] = c["pass_att"] + c["rush_car"]
    return out


def unit_games(lg, root=None):
    """{unit: [(day, home, away, home flag, home value, away value)]}, oldest
    first. Points: `fb_model.rating_games`. Other units: final scheduled games
    whose two offences are both in the player logs."""
    tg = team_games(lg, root)
    both = []
    for s in seasons(lg, root):
        doc = F.jz(os.path.join(root or ROOT, "data", lg, "latest", "schedule-%d.json.gz" % s)) or {}
        for g in doc.get("games") or []:
            t = tg.get(str(g.get("id"))) or {}
            if (g.get("final") and F.t60r.kick(g) is not None and g.get("home") in t
                    and g.get("away") in t):
                both.append((g["start"][:10], g["home"], g["away"], 0.0 if g.get("neutral") else 1.0,
                             t[g["home"]], t[g["away"]]))
    both.sort(key=lambda x: x[:4])
    out = {"points": F.rating_games(lg, root)}
    for u in units(lg)[1:]:
        out[u] = [(d, h, a, f, vh[u], va[u]) for d, h, a, f, vh, va in both]
    return out


class Tables:
    """Every unit's ratings for one league, solved once per Monday and cached,
    each warm-started from the nearest earlier Monday already solved."""

    def __init__(self, lg, root=None):
        self.lg = lg
        self.G = unit_games(lg, root)
        self._solved = {u: {} for u in self.G}

    def solve(self, unit, as_of):
        wk = F.monday(as_of[:10])
        done = self._solved[unit]
        if wk not in done:
            earlier = [w for w in done if w < wk]
            done[wk] = F.solve_ratings([g for g in self.G[unit] if g[0] < wk], wk,
                                       done[max(earlier)] if earlier else None,
                                       tol=F.RATING_TOL if unit == "points" else UNIT_TOL)
        return done[wk]

    def unit_for(self, team, unit, as_of):
        s = self.solve(unit, as_of)
        return s["base"] + s["O"][team] if team in s["teams"] else None

    def unit_allowed(self, team, unit, as_of):
        s = self.solve(unit, as_of)
        return s["base"] - s["D"][team] if team in s["teams"] else None

    def expect(self, offence, defence, unit, as_of, home=False):
        s = self.solve(unit, as_of)
        if offence not in s["teams"] or defence not in s["teams"]:
            return None
        return s["base"] + s["hpe"] * (1.0 if home else 0.0) + s["O"][offence] - s["D"][defence]

    def gap(self, offence, defence, unit, as_of):
        """O_offence - D_defence: the matchup above (+) or below an average one; 0 if unknown."""
        s = self.solve(unit, as_of)
        if offence not in s["teams"] or defence not in s["teams"]:
            return 0.0
        return s["O"][offence] - s["D"][defence]

    def home_edge(self, unit, as_of):
        return self.solve(unit, as_of)["hpe"]

    def table(self, as_of):
        """{unit: {team: {for, allowed, games, raw_for, raw_allowed}}} as of a day:
        the adjusted numbers beside the plain per-game averages they come from."""
        cut, out = F.monday(as_of[:10]), {}
        for u in self.G:
            raw = collections.defaultdict(lambda: [0, 0.0, 0.0])
            for _d, h, a, _f, vh, va in (g for g in self.G[u] if g[0] < cut):
                for team, got, gave in ((h, vh, va), (a, va, vh)):
                    raw[team][0] += 1
                    raw[team][1] += got
                    raw[team][2] += gave
            out[u] = {t: {"for": round(self.unit_for(t, u, cut), 2),
                          "allowed": round(self.unit_allowed(t, u, cut), 2),
                          "games": n, "raw_for": round(f / n, 2), "raw_allowed": round(al / n, 2)}
                      for t, (n, f, al) in sorted(raw.items())}
        return out


_LOADED = {}


def load(lg, root=None):
    """One Tables per league and tree, built once."""
    key = (lg, root or ROOT)
    if key not in _LOADED:
        _LOADED[key] = Tables(lg, root)
    return _LOADED[key]


def unit_for(team, unit, as_of, lg=None, root=None):
    return load(lg or F.LEAGUE, root).unit_for(team, unit, as_of)


def unit_allowed(team, unit, as_of, lg=None, root=None):
    return load(lg or F.LEAGUE, root).unit_allowed(team, unit, as_of)


def reconcile(tables, lg, season, root=None):
    """The tables' raw per-game passing and rushing yards allowed in one season
    against allowed-by-position-<season> (summed over positions): how many
    defences both carry, and the largest gap in yards per game. ⛔ A report."""
    doc = F.jz(os.path.join(root or ROOT, "data", lg, "latest",
                            "allowed-by-position-%d.json.gz" % season)) or {}
    lo, hi = "%d-03-01" % season, "%d-03-01" % (season + 1)
    out = {}
    for u in ("pass_yds", "rush_yds"):
        raw = collections.defaultdict(list)
        for d, h, a, _f, vh, va in tables.G[u]:
            if lo <= d < hi:
                raw[a].append(vh)
                raw[h].append(va)
        gaps = [abs(sum(p.get(u) or 0.0 for p in pos.values()) - sum(raw[t]) / len(raw[t]))
                for t, pos in (doc.get("defences") or {}).items() if raw.get(t)]
        out[u] = {"defences": len(gaps), "max_gap": round(max(gaps), 1) if gaps else None,
                  "median_gap": round(sorted(gaps)[len(gaps) // 2], 1) if gaps else None}
    return out
