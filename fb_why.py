#!/usr/bin/env python3
"""fb_why.py — THE "WHY" UNDER EACH FOOTBALL GIZMO'S PICKS PICK.

`[Sam, 2026-10-15]` "i also want a "why" behind the picks underneath each gizmo
picks pick". Written his way (his props standard): the player's role, how he has
done at this line this season, what the opponent allows to his position, the
opponent's injuries at the spots that guard him (NFL), and the model's chance
against the price. Game lines: the model's predicted score and each team's points
for and against.

⛔ Reader sentences, every one with a number, no jargon (CLAUDE.md "THE WHY IS
WRITTEN FOR A READER"). ⛔ A fact that cuts against the pick is stated, never
hidden. ⛔ It explains; it changes no pick, chance, rank or price. Only the liked
lists (`liked`, `game_lines_liked`) carry it. A fact it cannot find is left out,
never guessed (an ambiguous name, a team it cannot resolve). Stdlib only.
"""
import glob
import gzip
import json
import os

STAT = {"player_pass_yds": "pass_yds", "player_pass_tds": "pass_td", "player_rush_yds": "rush_yds",
        "player_reception_yds": "rec_yds", "player_receptions": "rec", "player_anytime_td": "total_td"}
WORD = {"pass_yds": "passing yards", "pass_td": "passing TDs", "rush_yds": "rushing yards",
        "rec_yds": "receiving yards", "rec": "catches", "total_td": "touchdowns"}
POS_WORD = {"QB": "quarterbacks", "RB": "running backs", "WR": "wide receivers", "TE": "tight ends"}
OUT = ("out", "doubtful")
SECONDARY = {"CB", "S", "SAF", "FS", "SS", "DB"}
FRONT = {"DE", "DT", "NT", "DL", "EDGE", "LB", "ILB", "OLB", "MLB"}
GUARDS = {  # (position, stat) -> the defenders who guard it
    "rec": SECONDARY | {"LB", "ILB", "OLB", "MLB"}, "rec_yds": SECONDARY | {"LB", "ILB", "OLB", "MLB"},
    "rush_yds": FRONT, "pass_yds": SECONDARY | {"DE", "EDGE", "OLB"}, "pass_td": SECONDARY | {"DE", "EDGE", "OLB"},
    "total_td": SECONDARY | FRONT}


def _jz(p):
    try:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def ordinal(n):
    return "%d%s" % (n, "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


def num(v):
    return ("%d" % v) if float(v).is_integer() else ("%.1f" % v)


def _season(latest):
    seasons = sorted(int(os.path.basename(p)[len("players-"):-len(".json.gz")])
                     for p in glob.glob(os.path.join(latest, "players-*.json.gz")))
    return seasons[-1] if seasons else None


class Context:
    """The files one card's whys read, loaded once."""

    def __init__(self, lg, latest, season=None):
        import card_fb as C
        import dossier_fb as D
        self.lg, self.season = lg, season or _season(latest)
        P = (_jz(os.path.join(latest, "players-%s.json.gz" % self.season)) or {}).get("players") or {}
        self.P, self.idx, self.norm = P, C.index_by_name(P), C.norm
        self.allowed = (_jz(os.path.join(latest, "allowed-by-position-%s.json.gz" % self.season))
                        or {}).get("defences") or {}
        inj = (_jz(os.path.join(latest, "injuries-%s.json.gz" % self.season)) or {}).get("teams") or {}
        self.injuries = inj
        self.resolve = D.team_codes(lg)
        sched = (_jz(os.path.join(latest, "schedule-%s.json.gz" % self.season)) or {}).get("games") or []
        self.finals = [g for g in sched if g.get("final") and g.get("home_score") is not None
                       and g.get("away_score") is not None]
        fm = json.load(open(os.path.join(latest, "fb-model.json"), encoding="utf-8")) \
            if os.path.exists(os.path.join(latest, "fb-model.json")) else {}
        self.scores = {(w.get("away"), w.get("home")): w.get("score") for w in fm.get("win_chances") or []}

    def log_of(self, who):
        pids = self.idx.get(self.norm(who)) or []
        return self.P[pids[0]] if len(pids) == 1 else None    # ⛔ ambiguous: no sentence, never a guess

    def rank(self, team, pos, stat):
        """(per game, rank or None, ranked teams) — rank 1 = allows the most; a team
        under the table's minimum games has a number and no rank."""
        row = (self.allowed.get(team) or {}).get(pos) or {}
        v, rk = row.get(stat), row.get(stat + "_rank")
        if v is None:
            return None
        n = sum(1 for t in self.allowed.values() if ((t.get(pos) or {}).get(stat + "_rank")) is not None)
        return v, rk, n

    def out_list(self, team, guards):
        """Names of `team`'s defenders listed Out/Doubtful on its latest report, at `guards`."""
        weeks = self.injuries.get(team) or {}
        if not weeks:
            return []
        wk = max(weeks, key=lambda w: int(w) if str(w).isdigit() else -1)
        return ["%s %s (%s)" % ((p.get("position") or "").upper(), p.get("full_name"), p.get("report_status"))
                for p in weeks[wk].get("players") or []
                if (p.get("report_status") or "").strip().lower() in OUT
                and (p.get("position") or "").upper() in guards]

    def pf_pa(self, team):
        """(points for, points against, games) per game this season, or None."""
        pts = [(g["home_score"], g["away_score"]) if g["home"] == team else (g["away_score"], g["home_score"])
               for g in self.finals if team in (g["home"], g["away"])]
        if not pts:
            return None
        return sum(p for p, _a in pts) / len(pts), sum(a for _p, a in pts) / len(pts), len(pts)


def prop_why(r, ctx):
    """Reader sentences for one liked prop."""
    out = []
    stat, plog = STAT.get(r.get("market")), ctx.log_of(r.get("player") or "")
    g = sorted((plog or {}).get("g") or [], key=lambda x: x.get("d") or "")
    who, line, side = r.get("player"), r.get("line"), r.get("side")
    role = r.get("role")
    if role and ctx.lg == "nfl":
        bits = ["%d%% of the snaps" % round(100 * role["snap"])]
        if r.get("market") in ("player_receptions", "player_reception_yds"):
            bits.append("%d%% of the team's targets" % round(100 * role["tgt_share"]))
        if r.get("market") in ("player_rush_yds",):
            bits.append("%s carries a game" % num(role["car"]))
        out.append("Over his last 3 games he has played %s." % " and ".join(bits))
    if g and stat and stat != "total_td" and line is not None and side in ("over", "under"):
        vals = [float(x.get(stat) or 0) for x in g]
        hit = sum(1 for v in vals if (v > line if side == "over" else v < line))
        out.append("This season he has gone %s %s in <b>%d of %d</b> games, averaging %s %s." % (
            side, num(line), hit, len(vals), num(round(sum(vals) / len(vals), 1)), WORD[stat]))
    team = g[-1].get("team") if g else None
    home, away = ctx.resolve(r.get("home") or ""), ctx.resolve(r.get("away") or "")
    opp = away if team and team == home else home if team and team == away else None
    pos = (plog or {}).get("pos")
    if opp and pos in POS_WORD and stat:
        rk = ctx.rank(opp, pos, stat)
        name = r.get("home") if opp == home else r.get("away")
        if rk:
            v, k, n = rk
            where = "" if k is None else " (%s)" % (
                "%s most of %d" % (ordinal(k), n) if k <= (n + 1) / 2 else "%s fewest of %d" % (ordinal(n - k + 1), n))
            out.append("The %s allow %s %s a game to %s%s." % (
                name, num(round(v, 1)), WORD[stat], POS_WORD[pos], where))
        if ctx.lg == "nfl":
            outs = ctx.out_list(opp, GUARDS.get(stat, set()))
            if outs:
                out.append("The %s list %s." % (name, ", ".join(outs[:4])))
    if r.get("confidence") is not None and r.get("break_even") is not None:
        out.append("The model gives it <b>%d%%</b>; at %+d it needs %s%% to pay." % (
            r["confidence"], r["price"], num(r["break_even"])))
    return out


def line_why(r, ctx):
    """Reader sentences for one liked game line: the pick's own sentence, then the
    model's predicted score and each team's points for and against."""
    out = list(r.get("why") or [])
    s = ctx.scores.get((r.get("away"), r.get("home")))
    if s and s.get("home") is not None and s.get("away") is not None:
        out.append("The model's predicted score: %s %s, %s %s (total %s)." % (
            r.get("away"), num(round(s["away"], 1)), r.get("home"), num(round(s["home"], 1)),
            num(round(s["away"] + s["home"], 1))))
    for name in (r.get("away"), r.get("home")):
        t = ctx.resolve(name or "")
        f = ctx.pf_pa(t) if t else None
        if f:
            out.append("The %s score %s and allow %s points a game this season (%d game%s)." % (
                name, num(round(f[0], 1)), num(round(f[1], 1)), f[2], "" if f[2] == 1 else "s"))
    return out


def explain(rows, lg, latest, kind="props", ctx=None):
    """The liked rows with `why` written. ⛔ Never raises: a row whose why fails
    keeps the why it had, and the other rows still get theirs."""
    try:
        ctx = ctx or Context(lg, latest)
    except Exception as e:
        print("  ⚠️ the picks' why was not written: %s: %s" % (type(e).__name__, e), flush=True)
        return rows
    for r in rows:
        try:
            why = prop_why(r, ctx) if kind == "props" else line_why(r, ctx)
        except Exception as e:
            print("  ⚠️ no why for %s: %s: %s" % (r.get("player"), type(e).__name__, e), flush=True)
            continue
        if why:
            r["why"] = why
    return rows
