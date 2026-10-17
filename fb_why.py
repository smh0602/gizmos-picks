#!/usr/bin/env python3
"""fb_why.py — THE "WHY" UNDER EACH FOOTBALL GIZMO'S PICKS PICK.

`[Sam, 2026-10-15]` "i also want a "why" behind the picks underneath each gizmo
picks pick". Written his way (his props standard): the player's role, his record
at this line, what the opponent allows to his position, the opponent's injuries
at the spots that guard him (NFL), and the chance against the price. Game lines:
the pick's own sentence, the model's predicted score and each team's points for
and against.

⛔ Reader sentences, every one with a number, no jargon (CLAUDE.md "THE WHY IS
WRITTEN FOR A READER"). ⛔ It explains; it changes no pick, chance, rank or
price. Only the liked lists (`liked`, `game_lines_liked`) carry it. A fact it
cannot find is left out, never guessed (an ambiguous name, a team it cannot
resolve, a season or week with no stored file). Stdlib only.

`[2026-10-16]` Checked sentence by sentence against the raw files (225 of them)
and corrected: the record is the CARD'S OWN sentence (its half-the-snaps and
6-game gates; none when the card shows none), never a second count over cameo
games; the role says how many games it averaged; the chance is "the model's"
only on a MODEL row; a tied rank reads from the right end; the injury report is
THIS game's week; the season is the kickoff's, never the newest file on disk;
and the predicted score is printed only when it lands on the pick's side (today
the score comes from the moneyline and total fits and the spread fit is
separate, so a spread pick could sit beside a score that loses it).
"""
import datetime
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
GUARDS = {  # stat -> the defenders who guard it
    "rec": SECONDARY | {"LB", "ILB", "OLB", "MLB"}, "rec_yds": SECONDARY | {"LB", "ILB", "OLB", "MLB"},
    "rush_yds": FRONT, "pass_yds": SECONDARY | {"DE", "EDGE", "OLB"}, "pass_td": SECONDARY | {"DE", "EDGE", "OLB"},
    "total_td": SECONDARY | FRONT}
SPREADS = ("spread", "alternate_spread")
TOTALS = ("total", "alternate_total")


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


def _day(s):
    try:
        return datetime.date.fromisoformat((s or "")[:10])
    except ValueError:
        return None


def season_of(when):
    """The football season a kickoff belongs to: a January or February game is
    the season before. ⛔ Never the newest file on disk (a week-1 card was
    built before players-2026 existed)."""
    d = _day(when)
    if d is None:
        return None
    return d.year if d.month >= 3 else d.year - 1


class Context:
    """The files one card's whys read, loaded once, for ONE season."""

    def __init__(self, lg, latest, season):
        import card_fb as C
        import dossier_fb as D
        self.lg, self.season = lg, season
        P = (_jz(os.path.join(latest, "players-%s.json.gz" % season)) or {}).get("players") or {}
        self.P, self.idx, self.norm = P, C.index_by_name(P), C.norm
        self.allowed = (_jz(os.path.join(latest, "allowed-by-position-%s.json.gz" % season))
                        or {}).get("defences") or {}
        self.injuries = (_jz(os.path.join(latest, "injuries-%s.json.gz" % season)) or {}).get("teams") or {}
        self.resolve = D.team_codes(lg)
        self.sched = (_jz(os.path.join(latest, "schedule-%s.json.gz" % season)) or {}).get("games") or []
        self.finals = [g for g in self.sched if g.get("final") and g.get("home_score") is not None
                       and g.get("away_score") is not None]
        p = os.path.join(latest, "fb-model.json")
        fm = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
        self.scores = {(w.get("away"), w.get("home")): w.get("score") for w in fm.get("win_chances") or []}

    def log_of(self, who):
        pids = self.idx.get(self.norm(who)) or []
        return self.P[pids[0]] if len(pids) == 1 else None    # ⛔ ambiguous: no sentence, never a guess

    def rank(self, team, pos, stat):
        """(per game, rank, fewest-rank, ranked teams) or None. rank 1 = allows the
        most, ties share it (competition ranks); the fewest-rank is counted from
        the other end the same way, so a tie reads right from both ends. A team
        under the table's minimum games has a number and no rank (None, None)."""
        row = (self.allowed.get(team) or {}).get(pos) or {}
        v, rk = row.get(stat), row.get(stat + "_rank")
        if v is None:
            return None
        vals = [(t.get(pos) or {}).get(stat) for t in self.allowed.values()
                if (t.get(pos) or {}).get(stat + "_rank") is not None]
        vals = [x for x in vals if x is not None]
        if rk is None:
            return v, None, None, len(vals)
        few = 1 + sum(1 for x in vals if x < v)
        return v, rk, few, len(vals)

    def week_of(self, home, away, when):
        """The schedule week of THIS game (its codes, kickoff within a day), or None."""
        d = _day(when)
        for g in self.sched:
            gd = _day(g.get("start"))
            if (g.get("home") == home and g.get("away") == away and g.get("week") is not None
                    and d is not None and gd is not None and abs((gd - d).days) <= 1):
                return g["week"]
        return None

    def out_list(self, team, guards, week):
        """`team`'s defenders listed Out/Doubtful on THIS game week's report, at
        `guards`. ⛔ No report stored for that week -> nothing (never an older one)."""
        rep = (self.injuries.get(team) or {}).get(str(week)) if week is not None else None
        return ["%s %s (%s)" % ((p.get("position") or "").upper(), p.get("full_name"), p.get("report_status"))
                for p in (rep or {}).get("players") or []
                if (p.get("report_status") or "").strip().lower() in OUT
                and (p.get("position") or "").upper() in guards]

    def pf_pa(self, team):
        """(points for, points against, games) per game this season, or None."""
        pts = [(g["home_score"], g["away_score"]) if g["home"] == team else (g["away_score"], g["home_score"])
               for g in self.finals if team in (g["home"], g["away"])]
        if not pts:
            return None
        return sum(p for p, _a in pts) / len(pts), sum(a for _p, a in pts) / len(pts), len(pts)


def _own(r):
    """The card's own sentence(s) for the row, as the card wrote them."""
    return list(r["why_card"] if "why_card" in r else (r.get("why") or []))


def prop_why(r, ctx):
    """Reader sentences for one liked prop."""
    out = []
    stat, plog = STAT.get(r.get("market")), ctx.log_of(r.get("player") or "")
    g = sorted((plog or {}).get("g") or [], key=lambda x: x.get("d") or "")
    role = r.get("role")
    if role and role.get("n") and ctx.lg == "nfl":
        bits = ["%d%% of the snaps" % round(100 * role["snap"])]
        if r.get("market") in ("player_receptions", "player_reception_yds"):
            bits.append("%d%% of the team's targets" % round(100 * role["tgt_share"]))
        if r.get("market") in ("player_rush_yds",):
            bits.append("%s carries a game" % num(role["car"]))
        out.append(("In his last game he played %s." % " and ".join(bits)) if role["n"] == 1 else
                   ("Over his last %d games he has played %s." % (role["n"], " and ".join(bits))))
    if r.get("record") is not None:      # ⛔ the card's own record, under the card's own gates
        out.extend(_own(r))
    team = g[-1].get("team") if g else None
    home, away = ctx.resolve(r.get("home") or ""), ctx.resolve(r.get("away") or "")
    opp = away if team and team == home else home if team and team == away else None
    pos = (plog or {}).get("pos")
    if opp and pos in POS_WORD and stat:
        rk = ctx.rank(opp, pos, stat)
        name = r.get("home") if opp == home else r.get("away")
        if rk:
            v, k, few, n = rk
            where = "" if k is None else " (%s)" % (
                "%s most of %d" % (ordinal(k), n) if k <= few else "%s fewest of %d" % (ordinal(few), n))
            out.append("The %s allow %s %s a game to %s%s." % (
                name, num(round(v, 1)), WORD[stat], POS_WORD[pos], where))
        if ctx.lg == "nfl":
            outs = ctx.out_list(opp, GUARDS.get(stat, set()), ctx.week_of(home, away, r.get("commence")))
            if outs:
                out.append("The %s list %s." % (name, ", ".join(outs[:4])))
    if r.get("confidence") is not None and r.get("break_even") is not None and r.get("price") is not None:
        basis = r.get("confidence_basis")
        if basis == "MODEL":
            out.append("The model gives it <b>%d%%</b>; at %+d it needs %s%% to pay." % (
                r["confidence"], r["price"], num(r["break_even"])))
        elif basis == "RECORD":
            out.append("His record at this line makes it <b>%d%%</b>; at %+d it needs %s%% to pay." % (
                r["confidence"], r["price"], num(r["break_even"])))
    return out


def score_agrees(r, s):
    """Does the printed (rounded) score land on the pick's side? A spread: the
    picked side's margin beats its line; a moneyline: the picked side wins; a
    total: over / under the line. Anything else: no."""
    s = {k: round(s[k], 1) for k in ("home", "away")}
    mk, side = r.get("market"), r.get("side")
    if mk in SPREADS + ("moneyline",) and side in ("home", "away"):
        m = s[side] - s["away" if side == "home" else "home"]
        if mk == "moneyline":
            return round(m, 6) > 0
        # ⚠️ rounded: 21.1 - 14.1 - 7 is 1.8e-15 in binary, which is ON the number
        return r.get("line") is not None and round(m + float(r["line"]), 6) > 0
    if mk in TOTALS and side in ("over", "under") and r.get("line") is not None:
        d = round(s["home"] + s["away"] - float(r["line"]), 6)
        return d > 0 if side == "over" else d < 0
    return False


def line_why(r, ctx):
    """Reader sentences for one liked game line: the pick's own sentence, then the
    model's predicted score (only when it lands on the pick's side) and each
    team's points for and against."""
    out = _own(r)
    s = ctx.scores.get((r.get("away"), r.get("home")))
    if s and s.get("home") is not None and s.get("away") is not None and score_agrees(r, s):
        out.append("The model's predicted score: %s %s, %s %s (total %s)." % (
            r.get("away"), num(round(s["away"], 1)), r.get("home"), num(round(s["home"], 1)),
            num(round(round(s["away"], 1) + round(s["home"], 1), 1))))
    for name in (r.get("away"), r.get("home")):
        t = ctx.resolve(name or "")
        f = ctx.pf_pa(t) if t else None
        if f:
            out.append("The %s score %s and allow %s points a game this season (%d game%s)." % (
                name, num(round(f[0], 1)), num(round(f[1], 1)), f[2], "" if f[2] == 1 else "s"))
    return out


def explain(rows, lg, latest, kind="props", ctx=None, scores=None):
    """The liked rows with `why` written; the card's own sentence is kept in
    `why_card`, so a second pass rebuilds the same why. The season is the
    kickoff's. ⛔ Never raises: a row whose why fails keeps the why it had, and
    the other rows still get theirs. `[Sam, 2026-10-17]` `scores`: {(away, home):
    whole-number score} (card_fb.shown_scores), printed instead of the model's
    one-decimal score, so the why and the Game Lines tab show the same numbers."""
    try:
        if ctx is None:
            season = next((season_of(r.get("commence")) for r in rows if season_of(r.get("commence"))), None)
            if season is None:
                return rows
            ctx = Context(lg, latest, season)
    except Exception as e:
        print("  ⚠️ the picks' why was not written: %s: %s" % (type(e).__name__, e), flush=True)
        return rows
    if scores:
        ctx.scores = {**ctx.scores, **scores}
    for r in rows:
        try:
            why = prop_why(r, ctx) if kind == "props" else line_why(r, ctx)
        except Exception as e:
            print("  ⚠️ no why for %s: %s: %s" % (r.get("player"), type(e).__name__, e), flush=True)
            continue
        if "why_card" not in r:
            r["why_card"] = list(r.get("why") or [])
        r["why"] = why
    return rows
