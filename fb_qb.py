#!/usr/bin/env python3
"""fb_qb.py — T75, THE BACKUP-QB BACKGROUND CHECK (research/fb_refit_spec.md §3k).

`[Sam, 2026-11-10]` *"when teams have a backup qb starting or a 3rd string qb starting the model
gives them more porints than they actually score ... the model finds the backup who is starting
and does a "backggriudn check" ... seeing how theyve performed in other starts from either that
year or previous years."*

One league's stored QB starts, and for a game, each team's QB DELTA: the expected starter's
grade minus the grade of the QBs the team's rating was built on. ⛔ FROZEN with QB, QBC, QP and
QPC (fb_challengers.py): a change is a new challenger.

  starter of record   the team's QB with the most pass attempts in a game (else its top passer
                      of any position), from the stored logs (§3k: "Use what's stored now"); a tie
                      goes to the larger player id, compared as text
  usual starter (U)   the most starts in the team's previous USUAL_GAMES games, any season; a tie
                      goes to the most recent
  expected starter    U, if U is not listed out and the last game's starter (L) started because U
                      was listed out at L's game; else L, unless L is listed out: then the team's
                      other QB with the most attempts this season, then last season, not listed
                      out (a tie: the larger player id, as text; none: an unknown backup)
  a start's mark      the team's points minus the points the model's own ratings expected for that
                      game (fb_model.own_ratings on every stored schedule, latest and history, at
                      that game's own Monday: earlier games only)
  a QB's grade        (his marks + K x the prior) / (his marked starts + K), every stored start before
                      the cut, any team (an unmarked start adds to neither sum, but is still a
                      stored start for the prior's count); the prior (replacement level) is the mean mark of starts in
                      EARLIER seasons by QBs with PRIOR_MAX or fewer prior stored starts whose first
                      stored start came after his team's first stored season of logs (there every
                      QB of that team starts at 0, veterans too; college logs before 2025 are Power
                      4 only); 0 before any
  the delta           grade(expected starter) - the rating's own QB mix: the grades of the team's
                      starters over the games the CHAMPION's own rating reads (`rated`), weighted
                      0.5 ** (days / 150); no such game: no reading

⛔ POINT IN TIME: a game reads starts, results and ratings dated before its own day (the cut), and
its listed-out reports as §3k says (fb_challengers.attach_qb: NFL, the game week's report;
college, cfb_injuries' 9:00 ET pick time on the game's own ET day).
Stdlib only.
"""
import bisect
import collections
import datetime
import glob
import os

import fb_model as FM

K = 8.0                      # ⛔ §3k: the prior's weight, in starts
PRIOR_MAX = 3                # ⛔ §3k: replacement level = starts by QBs with this many or fewer before
USUAL_GAMES = 8              # ⛔ §3k: the usual starter's window, in the team's games
HALF_LIFE = FM.RATING_HALF_LIFE      # ⛔ the rating's own weights (150 days)


class Book:
    """One league's stored starts and marks.
    `G`: every stored schedule's rating games (fb_model.rating_games plus the history seasons'),
    sorted; each start's mark reads them.
    `rated`: the (team, day) games the CHAMPION's own rating reads (fb_challengers.rated_games),
    the only games the mix reads; None: every game in G."""

    def __init__(self, lg, G, root=None, rated=None):
        lat = os.path.join(root or FM.ROOT, "data", lg, "latest")
        att = {}                                  # (team, day) -> {pid: attempts}
        self.pos, self.season, self.week, self.gid = {}, {}, {}, {}
        self.name = {}                                # pid -> his stored name (the NFL reserve list's key)
        self.first = {}                               # (team, pid) -> his first log row's day for that team
        for p in sorted(glob.glob(os.path.join(lat, "players-*.json.gz"))):
            try:
                s = int(os.path.basename(p)[len("players-"):len("players-") + 4])
            except ValueError:
                continue
            for pid, v in ((FM.jz(p) or {}).get("players") or {}).items():
                pid = str(pid)
                self.pos.setdefault(pid, (v.get("pos") or "").upper())
                self.name.setdefault(pid, v.get("name") or "")
                for g in v.get("g") or []:
                    t, d = g.get("team") or v.get("team"), g.get("d") or ""
                    if not t or not d:
                        continue
                    key = (t, d)
                    if (t, pid) not in self.first or d < self.first[(t, pid)]:
                        self.first[(t, pid)] = d
                    self.season[key], self.week[key] = s, g.get("week")
                    if g.get("game_id") is not None:
                        self.gid[key] = str(g.get("game_id"))
                    a = g.get("att") or 0
                    if a > 0:
                        att.setdefault(key, {})[pid] = att.get(key, {}).get(pid, 0) + a
        self.att = att
        self.starter = {}
        for key, by in att.items():
            qbs = [(a, pid) for pid, a in by.items() if self.pos.get(pid) == "QB"]
            best = max(qbs or [(a, pid) for pid, a in by.items()])
            self.starter[key] = best[1]
        self.days = collections.defaultdict(list)     # team -> sorted days with a starter
        for t, d in sorted(self.starter):
            self.days[t].append(d)
        # each start's mark, from its own Monday's ratings
        by = {}
        for d, h, a, hf, hs, as_ in G:
            by[(h, d)] = (hs, h, a, hf, True)
            by[(a, d)] = (as_, h, a, hf, False)
        self.rated = set(by) if rated is None else set(rated)
        need = {FM.monday(d) for (t, d) in self.starter if (t, d) in by}
        own = FM.own_ratings(G, need) if need else {}
        marks = {}
        for (t, d) in self.starter:
            g = by.get((t, d))
            if g is None:
                continue
            pts, h, a, hf, home = g
            m, tot = FM.own_numbers(own.get(FM.monday(d)), h, a, hf == 0.0)
            if m is None:
                continue
            marks[(t, d)] = pts - ((tot + m) / 2.0 if home else (tot - m) / 2.0)
        self.marks = marks
        # each team's first stored season with a starter: before it, its QBs' careers are not stored
        team_first = {}
        for (t, d) in self.starter:
            s = self.season.get((t, d))
            if s is not None and (t not in team_first or s < team_first[t]):
                team_first[t] = s
        starts = collections.defaultdict(list)        # pid -> [(day, season, mark or None, team)]
        for (t, d), pid in sorted(self.starter.items(), key=lambda kv: kv[0][1]):
            starts[pid].append((d, self.season.get((t, d)), marks.get((t, d)), t))
        self.starts = {}
        early = collections.defaultdict(list)         # season -> marks of early-career starts
        for pid, v in starts.items():
            v.sort(key=lambda x: x[0])
            s0, t0 = v[0][1], v[0][3]
            new = s0 is not None and team_first.get(t0) is not None and s0 > team_first[t0]
            days, cum, n = [], [0.0], [0]
            for i, (d, s, mk, _t) in enumerate(v):
                days.append(d)
                cum.append(cum[-1] + (mk or 0.0))
                n.append(n[-1] + (0 if mk is None else 1))
                if new and mk is not None and i <= PRIOR_MAX and s is not None:
                    early[s].append(mk)
            self.starts[pid] = (days, cum, n)
        self._early = dict(early)
        self._prior = {}

    def prior(self, season):
        """Replacement level at `season`: the mean mark of early-career starts in EVERY season before
        it (a QB first seen starting after his team's first stored season, PRIOR_MAX or fewer stored
        before), whether or not `season`'s own logs are stored yet; 0 before any."""
        if season is None:
            return 0.0
        if season not in self._prior:
            pool = [m for s, v in self._early.items() if s < season for m in v]
            self._prior[season] = sum(pool) / len(pool) if pool else 0.0
        return self._prior[season]

    def grade(self, pid, cut, season):
        """A QB's grade from his stored starts dated before `cut` (his marks + K x the prior) / (his
        marked starts + K); None (an unknown backup): the prior."""
        p = self.prior(season)
        if pid is None or pid not in self.starts:
            return p
        days, cum, n = self.starts[pid]
        i = bisect.bisect_left(days, cut)
        return (cum[i] + K * p) / (n[i] + K)

    def before(self, team, cut):
        v = self.days.get(team) or []
        return v[:bisect.bisect_left(v, cut)]

    def usual(self, team, cut):
        last = self.before(team, cut)[-USUAL_GAMES:]
        if not last:
            return None
        c = collections.Counter(self.starter[(team, d)] for d in last)
        top = max(c.values())
        return next(self.starter[(team, d)] for d in reversed(last) if c[self.starter[(team, d)]] == top)

    def replacement(self, team, cut, season, out, last):
        """The team's other QB with the most attempts this season (then last season) before the cut,
        neither listed out nor the last starter; None: an unknown backup."""
        for s in (season, season - 1 if season is not None else None):
            tot = collections.Counter()
            for d in self.before(team, cut):
                if self.season.get((team, d)) != s:
                    continue
                for pid, a in (self.att.get((team, d)) or {}).items():
                    if self.pos.get(pid) == "QB" and pid not in out and pid != last:
                        tot[pid] += a
            if tot:
                return max(tot.items(), key=lambda kv: (kv[1], kv[0]))[0]
        return None

    def expected(self, team, cut, season, out_now, out_at):
        """(expected starter or None, why). `out_now`: the QB ids listed out for this game (an empty
        set when there is no report); `out_at(team, day)`: those listed out at the team's game that
        day (an empty set when unknown). The usual starter's return is checked first: it holds
        whether or not the fill-in is listed out now."""
        prev = self.before(team, cut)
        if not prev:
            return None, "no earlier start"
        last = self.starter[(team, prev[-1])]
        u = self.usual(team, cut)
        if u is not None and u != last and u not in out_now and u in out_at(team, prev[-1]):
            return u, "usual starter returns"
        if last in out_now:
            return self.replacement(team, cut, season, out_now, last), "last starter listed out"
        return last, "last starter"

    def mix(self, team, cut, season):
        """The rating's own QB mix: the starters' grades over the games the champion's rating reads
        (`rated`) dated before the cut's Monday, weighted 0.5 ** (days / 150) from it. None: no
        such game (no reading)."""
        wk = FM.monday(cut)
        num = den = 0.0
        for d in self.before(team, wk):
            if (team, d) not in self.rated:
                continue
            w = 0.5 ** ((datetime.date.fromisoformat(wk) - datetime.date.fromisoformat(d)).days / HALF_LIFE)
            num += w * self.grade(self.starter[(team, d)], cut, season)
            den += w
        return num / den if den > 0 else None

    def delta(self, team, cut, season, out_now, out_at):
        """grade(expected starter) - the rating's QB mix, in points; None: no reading."""
        e, why = self.expected(team, cut, season, out_now, out_at)
        if why == "no earlier start":
            return None
        base = self.mix(team, cut, season)
        if base is None:
            return None
        return self.grade(e, cut, season) - base
