#!/usr/bin/env python3
"""fb_props_model.py — the football PLAYER-PROPS model, built exactly as
`research/fb_props_design.md` describes (committed before this file).

    LEAGUE=nfl python fb_props_model.py     # retrain, walk-forward, write

Stage 1 predicts each player's stat distribution from the stored player
logs (2021–2026), every input known before kickoff. Stage 2 folds in the
market line, fitted only on EARLIER priced weeks. Walk-forward weekly over
the stored prop snapshots, graded at the best Hard Rock / FanDuel /
DraftKings price, and scored champion-vs-challenger against the existing
props card's own probabilities.

⛔ IT DOES NOT REPLACE THE CARD. `card_fb.py` never imports this file, and
the champion's probabilities are RECOMPUTED with the card's own
`rate_for`, never edited. Switching is Sam's decision.
⛔ NEVER INVENTS A PRICE: a side with no quote at the three books is not
picked, and a rung with no outcome in the logs is not graded.
⚠️ STDLIB ONLY.
"""
import collections
import contextlib
import datetime
import glob
import gzip
import json
import math
import os
import sys

import card_fb                      # the champion: rate_for, norm, price floors — read, never edited
import collect                      # PROP_MARKETS, league_books: what is pulled, and from whom
import dossier_fb as D              # team_codes: book team names -> log team codes
import fb_model as F                # fit, predict, record, devig, implied, decimal, monday, L
import mlb_refit                    # paired_test_clustered: the ONE cluster-robust paired test
import possession as P              # share_before: signal 6 from EARLIER games only
import record_fb                    # _val, _won, _played, JOIN_WINDOW_DAYS: the card's own grader

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUE = os.environ.get("LEAGUE", "nfl")
SEASONS = (2021, 2022, 2023, 2024, 2025, 2026)     # ⛔ design §1
RIDGE = 1.0                                        # ⛔ design §3
MIN_N = 500                                        # ⛔ design §6 (Sam)
ALPHA = 0.05                                       # ⛔ design §6 (Sam)
CLIP = 1e-12
TD_MARKET = "player_anytime_td"
YARDS = ("player_pass_yds", "player_rush_yds", "player_reception_yds")
COUNTS = ("player_pass_tds", "player_receptions")
# ⛔ design §2: the stat, the usage figure, and who is trained on
STAT = {"player_pass_yds": ("pass_yds",), "player_pass_tds": ("pass_td",),
        "player_rush_yds": ("rush_yds",), "player_reception_yds": ("rec_yds",),
        "player_receptions": ("rec",), TD_MARKET: ("rush_td", "rec_td")}
USAGE = {"nfl": {"player_pass_yds": ("att",), "player_pass_tds": ("att",),
                 "player_rush_yds": ("car",), "player_reception_yds": ("tgt",),
                 "player_receptions": ("tgt",), TD_MARKET: ("car", "tgt")},
         "ncaaf": {"player_pass_yds": ("att",), "player_pass_tds": ("att",),
                   "player_rush_yds": ("car",), "player_reception_yds": ("rec",),
                   "player_receptions": ("rec",), TD_MARKET: ("car", "rec")}}
POSITIONS = {"player_pass_yds": {"QB"}, "player_pass_tds": {"QB"},
             "player_rush_yds": {"QB", "RB", "WR"}, "player_reception_yds": {"WR", "TE", "RB"},
             "player_receptions": {"WR", "TE", "RB"}, TD_MARKET: {"QB", "RB", "WR", "TE"}}
N_FEAT = 20


def log(m):
    print(m, flush=True)


def L(value, basis):
    return F.L(value, basis)


def jz(path):
    return F.jz(path)


def markets_for(lg):
    return tuple(collect.PROP_MARKETS.get(lg) or ())


@contextlib.contextmanager
def league(lg):
    """card_fb and record_fb read their league from module globals set at
    import; switch them for one block and put them back."""
    saved = (card_fb.LEAGUE, card_fb.DATA, record_fb.LEAGUE)
    card_fb.LEAGUE, card_fb.DATA, record_fb.LEAGUE = lg, "data/%s" % lg, lg
    try:
        yield
    finally:
        card_fb.LEAGUE, card_fb.DATA, record_fb.LEAGUE = saved


def fnum(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def stat(g, fields):
    return sum(fnum(g.get(f)) for f in fields)


def played(lg, g):
    """NFL: snaps > 0, or no snap field but a stat. College: every row."""
    if lg != "nfl":
        return True
    sn = g.get("snaps")
    if sn is not None:
        return fnum(sn) > 0
    return any(fnum(g.get(f)) > 0 for f in ("att", "car", "tgt", "rec"))


# ══════════════════════════════════════════════════════════════════════
# STAGE 1 — ridge regression solved exactly from running sums
# ══════════════════════════════════════════════════════════════════════
class Sums:
    """Running sums for a ridge regression with standardised inputs and an
    unpenalised intercept. Adding rows in date order and copying at a week
    boundary gives that week's training set exactly."""

    def __init__(self, k=N_FEAT):
        self.k, self.n = k, 0
        self.sx = [0.0] * k
        self.sxx = [[0.0] * k for _ in range(k)]
        self.sy = self.syy = 0.0
        self.sxy = [0.0] * k

    def add(self, x, y):
        self.n += 1
        self.sy += y
        self.syy += y * y
        for i in range(self.k):
            xi = x[i]
            if xi == 0.0:
                continue
            self.sx[i] += xi
            self.sxy[i] += xi * y
            row = self.sxx[i]
            for j in range(i, self.k):
                xj = x[j]
                if xj != 0.0:
                    row[j] += xi * xj

    def copy(self):
        c = Sums(self.k)
        c.n, c.sy, c.syy = self.n, self.sy, self.syy
        c.sx, c.sxy = list(self.sx), list(self.sxy)
        c.sxx = [list(r) for r in self.sxx]
        return c

    def solve(self, ridge=RIDGE):
        """-> {"ybar", "mu", "sd", "w", "sigma", "n"} or None."""
        n, k = self.n, self.k
        if n < 2:
            return None
        mu = [s / n for s in self.sx]
        C = [[0.0] * k for _ in range(k)]
        for i in range(k):
            for j in range(i, k):
                C[i][j] = C[j][i] = self.sxx[i][j] / n - mu[i] * mu[j]
        sd = [math.sqrt(C[i][i]) if C[i][i] > 1e-12 else 1.0 for i in range(k)]
        A = [[n * C[i][j] / (sd[i] * sd[j]) for j in range(k)] for i in range(k)]
        ybar = self.sy / n
        b = [(self.sxy[i] - mu[i] * self.sy) / sd[i] for i in range(k)]
        for i in range(k):
            A[i][i] += ridge
        w = F._solve(A, b)
        if w is None:
            return None
        rss = (self.syy - n * ybar * ybar - 2 * sum(w[i] * b[i] for i in range(k))
               + sum(w[i] * A[i][j] * w[j] for i in range(k) for j in range(k))
               - ridge * sum(x * x for x in w))
        return {"ybar": ybar, "mu": mu, "sd": sd, "w": w, "n": n,
                "sigma": math.sqrt(max(rss, 1e-9) / n)}


def s1_mean(m, x):
    return m["ybar"] + sum(m["w"][j] * (x[j] - m["mu"][j]) / m["sd"][j] for j in range(len(x)))


def _phi(z):
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


def _pois_cdf(kmax, mu):
    if kmax < 0:
        return 0.0
    t = s = math.exp(-mu)
    for i in range(1, int(kmax) + 1):
        t *= mu / i
        s += t
    return min(1.0, s)


def s1_probs(market, m, x, line):
    """Stage 1: (P(over line) or P(yes), P(under line) or None)."""
    mean = s1_mean(m, x)
    if market in YARDS:
        if line is None:
            return None, None
        if line < 0:
            return 1.0, 0.0
        z = (math.sqrt(line) - mean) / m["sigma"]
        return 1.0 - _phi(z), _phi(z)
    mu = max(0.05, mean)
    if market == TD_MARKET:
        return 1.0 - math.exp(-mu), None
    if line is None:
        return None, None
    over = 1.0 - _pois_cdf(math.floor(line), mu)
    under = _pois_cdf(math.ceil(line) - 1, mu)
    return over, under


def target(market, g):
    v = stat(g, STAT[market])
    return math.sqrt(max(v, 0.0)) if market in YARDS else v


# ══════════════════════════════════════════════════════════════════════
# THE LOGS, STREAMED IN DATE ORDER — every input from EARLIER games only
# ══════════════════════════════════════════════════════════════════════
def load_logs(lg, root=None):
    out = {}
    for s in SEASONS:
        d = jz(os.path.join(root or ROOT, "data", lg, "latest", "players-%d.json.gz" % s))
        if d and d.get("players"):
            out[s] = d["players"]
    return out


def possession_games(lg, root=None):
    g = {}
    for s in SEASONS:
        d = jz(os.path.join(root or ROOT, "data", lg, "latest", "top-%d.json.gz" % s)) or {}
        g.update(d.get("games") or {})
    return g


class History:
    """Point-in-time state: a player's earlier games, each defence's
    allowed stat by position, each team's pace. Read, THEN updated, one
    date at a time, so a game never sees itself or its own day."""

    def __init__(self, lg, poss):
        self.lg, self.poss = lg, poss
        self.player = collections.defaultdict(list)       # pid -> [(season, g)]
        self.allowed = collections.defaultdict(float)     # (season, def, pos, market) -> total
        self.def_games = collections.defaultdict(set)     # (season, def) -> {game ids}
        self.lg_allowed = collections.defaultdict(float)  # (season, pos, market) -> total
        self.lg_def_games = collections.defaultdict(int)  # season -> def-games
        self.pace = collections.defaultdict(float)        # (season, team) -> att+car total
        self.team_games = collections.defaultdict(set)    # (season, team) -> {game ids}
        self.lg_pace = collections.defaultdict(float)     # season -> total
        self.lg_team_games = collections.defaultdict(int)

    def features(self, pid, season, market, ctx):
        """The 20 design-§2 inputs, or None if he has no earlier game."""
        H = self.player.get(pid) or []
        if not H:
            return None
        sf, uf = STAT[market], USAGE[self.lg][market]
        ssn = [g for s, g in H if s == season]
        last = [g for _s, g in H[-3:]]
        prev = [g for s, g in H if s == season - 1]
        # 🔴 ON THE TARGET'S OWN SCALE. `[found 2026-09-24, first run]` The
        #    yardage target is √yards; averaging RAW yards into a straight
        #    line to √yards extrapolated a star's 144 and 162 into 218
        #    projected yards on a 96.5 line (P = 0.996). Yardage inputs are
        #    averaged as √ per game, like the target. Counts stay raw.
        tf = (lambda v: math.sqrt(max(v, 0.0))) if market in YARDS else (lambda v: v)  # noqa: E731
        mean = lambda gs, f: (sum(tf(stat(g, f)) for g in gs) / len(gs)) if gs else 0.0  # noqa: E731
        sp = [fnum(g.get("snap_pct")) for g in last if g.get("snap_pct") is not None]
        opp, team, pos = ctx.get("opp"), ctx.get("team"), ctx.get("pos")
        n_def = len(self.def_games.get((season, opp), ()))
        lg_n = self.lg_def_games.get(season, 0)
        f9 = 0.0
        if n_def >= 2 and lg_n:
            f9 = (tf(self.allowed.get((season, opp, pos, market), 0.0) / n_def)
                  - tf(self.lg_allowed.get((season, pos, market), 0.0) / lg_n))

        def pace(t):
            n = len(self.team_games.get((season, t), ()))
            ln = self.lg_team_games.get(season, 0)
            if not n or not ln:
                return 0.0
            return self.pace.get((season, t), 0.0) / n - self.lg_pace.get(season, 0.0) / ln
        f12 = 0.0
        day = ctx.get("day")
        if self.poss and day and team and opp:
            a = P.share_before(self.poss, team, day)["share"]
            b = P.share_before(self.poss, opp, day)["share"]
            if a is not None and b is not None:
                f12 = a - b
        wx = ctx.get("wx") or {}
        nfl = self.lg == "nfl"
        return [mean(ssn, sf), 1.0 if ssn else 0.0, mean(last, sf), mean(prev, sf),
                mean(ssn, uf), mean(last, uf), (sum(sp) / len(sp)) if (nfl and sp) else 0.0,
                math.log1p(len(ssn)), f9, pace(team), pace(opp), f12,
                1.0 if ctx.get("home") else 0.0, 1.0 if ctx.get("neutral") else 0.0,
                1.0 if nfl and (wx.get("roof") or "") in ("dome", "closed") else 0.0,
                (fnum(wx.get("temp")) - 60.0) if nfl and wx.get("temp") is not None else 0.0,
                fnum(wx.get("wind")) if nfl and wx.get("wind") is not None else 0.0,
                fnum(ctx.get("ahead_out")) if nfl else 0.0,
                fnum(ctx.get("ol_out")) if nfl else 0.0,
                fnum(ctx.get("opp_dl_out")) if nfl else 0.0]

    def add_day(self, entries):
        """Fold one date's played games into the state (after that date's
        features were read)."""
        by_game_team = collections.defaultdict(float)
        for season, pid, pos, g in entries:
            if not played(self.lg, g):
                continue
            self.player[pid].append((season, g))
            gid, team, opp = g.get("game_id"), g.get("team"), g.get("o")
            if gid is None:
                continue
            if opp is not None:
                if gid not in self.def_games[(season, opp)]:
                    self.def_games[(season, opp)].add(gid)
                    self.lg_def_games[season] += 1
                for mk, f in STAT.items():
                    if pos in POSITIONS[mk]:
                        v = stat(g, f)
                        self.allowed[(season, opp, pos, mk)] += v
                        self.lg_allowed[(season, pos, mk)] += v
            if team is not None:
                by_game_team[(season, team, gid)] += fnum(g.get("att")) + fnum(g.get("car"))
        for (season, team, gid), v in by_game_team.items():
            if gid not in self.team_games[(season, team)]:
                self.team_games[(season, team)].add(gid)
                self.lg_team_games[season] += 1
            self.pace[(season, team)] += v
            self.lg_pace[season] += v


def ctx_of(pos, g):
    return {"opp": g.get("o"), "team": g.get("team"), "pos": pos, "day": (g.get("d") or "")[:10],
            "home": bool(g.get("home")) and g.get("home") not in (0, "0"), "neutral": bool(g.get("neutral")),
            "wx": g.get("wx"), "ahead_out": g.get("ahead_out"), "ol_out": g.get("ol_out"),
            "opp_dl_out": g.get("opp_dl_out")}


def stream(lg, logs, boundaries, keep_from, poss=None):
    """Walk every player-game in date order. -> (sums snapshots
    {boundary: {market: Sums}}, final {market: Sums}, kept features
    {(pid, date): {market: x}} for games on/after `keep_from`, History)."""
    markets = markets_for(lg)
    entries = collections.defaultdict(list)
    for season, players in logs.items():
        for pid, p in players.items():
            pos = (p.get("pos") or "").upper()
            if pos not in ("QB", "RB", "WR", "TE"):
                continue
            for g in p.get("g") or []:
                d = (g.get("d") or "")[:10]
                if d:
                    entries[d].append((season, pid, pos, g))
    H = History(lg, poss or {})
    sums = {mk: Sums() for mk in markets}
    snaps, kept = {}, {}
    todo = sorted(boundaries)
    for day in sorted(entries):
        while todo and day >= todo[0]:
            snaps[todo.pop(0)] = {mk: s.copy() for mk, s in sums.items()}
        for season, pid, pos, g in entries[day]:
            if not played(lg, g):
                continue
            ctx = ctx_of(pos, g)
            xs = {}
            for mk in markets:
                if pos not in POSITIONS[mk]:
                    continue
                x = H.features(pid, season, mk, ctx)
                if x is None:
                    continue
                sums[mk].add(x, target(mk, g))
                xs[mk] = x
            if day >= keep_from and xs:
                kept[(pid, day)] = xs
        H.add_day(entries[day])
    for b in todo:
        snaps[b] = {mk: s.copy() for mk, s in sums.items()}
    return snaps, sums, kept, H


# ══════════════════════════════════════════════════════════════════════
# PRICES — the last snapshot before each kickoff, Sam's three books
# ══════════════════════════════════════════════════════════════════════
def prop_snapshots(lg, root=None):
    """{event id: (pulled_at, event)} — the LAST snapshot pulled before
    that event's kickoff. ⛔ A snapshot after kickoff is a live price."""
    out = {}
    for path in sorted(glob.glob(os.path.join(root or ROOT, "data", lg, "*", "props-player", "*.json.gz"))):
        doc = jz(path) or {}
        pulled = doc.get("pulled_at") or ""
        for ev in doc.get("events") or []:
            c = ev.get("commence_time") or ""
            if not pulled or not c or pulled >= c:
                continue
            k = ev.get("id")
            if k not in out or pulled > out[k][0]:
                out[k] = (pulled, ev)
    return out


def rungs_of(lg, ev):
    """-> {(player, market, line): {"best": {side: (price, book)},
    "books": {book: {side: price}}}} at Sam's three books, EXACT line."""
    ok = F.books_ok(lg)
    mks = set(markets_for(lg))
    out = {}
    for bk in ev.get("bookmakers") or []:
        b = bk.get("key")
        if b not in ok:
            continue
        for m in bk.get("markets") or []:
            mk = m.get("key")
            if mk not in mks:
                continue
            for o in m.get("outcomes") or []:
                who, side, px = o.get("description"), (o.get("name") or "").lower(), o.get("price")
                if not who or px is None or side not in ("over", "under", "yes"):
                    continue
                line = o.get("point")
                if mk != TD_MARKET and line is None:
                    continue
                key = (who, mk, None if mk == TD_MARKET else float(line))
                r = out.setdefault(key, {"best": {}, "books": {}})
                r["books"].setdefault(b, {})[side] = px
                cur = r["best"].get(side)
                if cur is None or F.decimal(px) > F.decimal(cur[0]):
                    r["best"][side] = (px, b)
    return out


def market_prob(market, rung):
    """p_mkt (design §3): the de-vigged P(over) averaged over the three
    books quoting both sides at this line; for anytime TD the mean implied
    P(yes). None if unavailable."""
    ps = []
    for sides in rung["books"].values():
        if market == TD_MARKET:
            if "yes" in sides:
                ps.append(F.implied(sides["yes"]))
        elif "over" in sides and "under" in sides:
            ps.append(F.devig(sides["over"], sides["under"]))
    return (sum(ps) / len(ps)) if ps else None


# ══════════════════════════════════════════════════════════════════════
# NAMES AND OUTCOMES — the card's matcher and the card's grader
# ══════════════════════════════════════════════════════════════════════
def name_index(logs, seasons=(2025, 2026)):
    """norm(name) -> {pid} over the given seasons. ⛔ >1 pid = ambiguous."""
    idx = collections.defaultdict(set)
    for s in seasons:
        for pid, p in (logs.get(s) or {}).items():
            idx[card_fb.norm(p.get("name") or "")].add(pid)
    return idx


def resolve(idx, who):
    pids = idx.get(card_fb.norm(who or "")) or set()
    return next(iter(pids)) if len(pids) == 1 else None


def game_row(logs, pid, commence):
    """record_fb's ±1-day join: exactly one row, or None."""
    try:
        t = datetime.datetime.strptime((commence or "")[:10], "%Y-%m-%d")
    except ValueError:
        return None, None
    hits = []
    for s, players in logs.items():
        for g in (players.get(pid) or {}).get("g") or []:
            try:
                gd = datetime.datetime.strptime(g.get("d") or "", "%Y-%m-%d")
            except ValueError:
                continue
            if abs((gd - t).days) <= record_fb.JOIN_WINDOW_DAYS:
                hits.append((s, g))
    return hits[0] if len(hits) == 1 else (None, None)


def outcome(lg, market, line, g):
    """1/0 for over (or yes), None if void, a push or ungradable."""
    ok, _why = record_fb._played(g)
    if not ok:
        return None
    val = record_fb._val(g, market)
    side = "yes" if market == TD_MARKET else "over"
    won = record_fb._won(val, line, side)
    if won is None or (side == "over" and val == line):
        return None
    return 1 if won else 0


# ══════════════════════════════════════════════════════════════════════
# THE CHAMPION — the props card's own probability, recomputed
# ══════════════════════════════════════════════════════════════════════
def champion_logs(lg, root=None):
    """(season, players) the card rates from, via the card's own loader."""
    with league(lg):
        old = os.getcwd()
        os.chdir(root or ROOT)
        try:
            season, players = card_fb.load_logs()
        finally:
            os.chdir(old)
        floor = card_fb.USAGE_FLOOR
    return season, players, floor


def card_seasons(lg, root=None):
    """{card date: logs_season} from the published cards, to confirm the
    card rated every scored date from the season recomputed here."""
    out = {}
    for p in glob.glob(os.path.join(root or ROOT, "picks", "fb-%s-2*.json" % lg)):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        out[os.path.basename(p)[len("fb-%s-" % lg):-5]] = d.get("logs_season")
    return out


def champion_prob(lg, cplayers, cidx, floor, who, market, line):
    pids = cidx.get(card_fb.norm(who or ""), [])
    if len(pids) != 1:
        return None, None
    with league(lg):
        card_fb.USAGE_FLOOR = floor
        r = card_fb.rate_for(cplayers[pids[0]].get("g") or [], market, line,
                             "yes" if market == TD_MARKET else "over")
    return (r[0] / 100.0 if r else None), pids[0]


# ══════════════════════════════════════════════════════════════════════
# THE WALK-FORWARD
# ══════════════════════════════════════════════════════════════════════
def logit(p):
    p = min(1 - 1e-6, max(1e-6, p))
    return math.log(p / (1 - p))


def s2_features(market, p1, pm):
    return [logit(p1), logit(pm), 1.0 if market == TD_MARKET else 0.0]


def final_probs(market, p1_over, p1_under, pm, s2):
    """Stage 2 where it exists and the market price does; else stage 1."""
    if s2 is not None and pm is not None:
        p = F.predict(s2, s2_features(market, p1_over, pm))
        return p, (None if market == TD_MARKET else 1.0 - p)
    return p1_over, p1_under


def pick_for(market, rung, p_over, p_under):
    """design §5: the card's price floors, EV at the best three-book price."""
    best = None
    sides = (("yes", p_over),) if market == TD_MARKET else (("over", p_over), ("under", p_under))
    for side, p in sides:
        q = rung["best"].get(side)
        if q is None or p is None:
            continue
        px, book = q
        if not (card_fb.PRICE_FLOOR <= px <= card_fb.PRICE_CEIL):
            continue
        ev = p * F.decimal(px) - 1.0
        if best is None or ev > best["ev"]:
            best = {"side": side, "price": px, "book": book, "p": p, "ev": ev,
                    "break_even": 1.0 / F.decimal(px)}
    return best if best and best["ev"] > 0 else None


def walk_forward(lg, root=None, logs=None):
    """-> dict with graded rungs (both models), picks, and the fitted
    stage-1/stage-2 state for this week's live picks."""
    logs = logs if logs is not None else load_logs(lg, root)
    snaps_by_event = prop_snapshots(lg, root)
    first = min((ev[1].get("commence_time") or "")[:10] for ev in snaps_by_event.values()) \
        if snaps_by_event else "9999-12-31"
    # ⚠️ a log row's LOCAL date can be a day before the kickoff's UTC date
    keep_from = (datetime.date.fromisoformat(first) - datetime.timedelta(days=2)).isoformat() \
        if snaps_by_event else first
    weeks = sorted({F.monday(ev[1]["commence_time"][:10]) for ev in snaps_by_event.values()})
    snaps, final, kept, H = stream(lg, logs, weeks, keep_from, possession_games(lg, root))
    models = {w: {mk: s.solve() for mk, s in snaps[w].items()} for w in weeks}
    idx = name_index(logs)
    cseason, cplayers, floor = champion_logs(lg, root)
    cidx = card_fb.index_by_name(cplayers)
    graded, picks = [], []
    by_week = collections.defaultdict(list)
    for eid, (pulled, ev) in snaps_by_event.items():
        by_week[F.monday(ev["commence_time"][:10])].append((eid, pulled, ev))
    s2_train = []
    s2_used = {}
    with league(lg):                  # record_fb._played reads its league global
        _weeks(lg, weeks, by_week, models, kept, logs, idx, cseason, cplayers, cidx, floor,
               s2_train, s2_used, graded, picks)
    return {"graded": graded, "picks": picks, "weeks": weeks, "stage2_weeks": s2_used,
            "final": final, "H": H, "s2_train": s2_train, "logs": logs, "idx": idx,
            "card_season": cseason, "card_seasons": card_seasons(lg, root)}


def _weeks(lg, weeks, by_week, models, kept, logs, idx, cseason, cplayers, cidx, floor,
           s2_train, s2_used, graded, picks):
    """The weekly loop: stage 2 from EARLIER weeks, predict, grade, pick."""
    for w in weeks:
        s2 = F.fit([x for x, _ in s2_train], [y for _, y in s2_train]) if s2_train else None
        s2_used[w] = s2 is not None
        week_rows = []
        for eid, pulled, ev in by_week[w]:
            for (who, mk, line), rung in rungs_of(lg, ev).items():
                pid = resolve(idx, who)
                if pid is None:
                    continue
                season, g = game_row(logs, pid, ev["commence_time"])
                if g is None:
                    continue
                y = outcome(lg, mk, line, g)
                x = (kept.get((pid, (g.get("d") or "")[:10])) or {}).get(mk)
                m = models[w].get(mk)
                if x is None or m is None:
                    continue
                p1o, p1u = s1_probs(mk, m, x, line)
                if p1o is None:
                    continue
                pm = market_prob(mk, rung)
                po, pu = final_probs(mk, p1o, p1u, pm, s2)
                pc, cpid = champion_prob(lg, cplayers, cidx, floor, who, mk, line)
                row = {"league": lg, "game": "%s:%s" % (lg, eid), "event": eid, "week": w,
                       "player": who, "market": mk, "line": line, "y": y,
                       "p_model": po, "p_under": pu, "p_stage1": p1o, "p_market": pm,
                       "p_card": pc if (cpid == pid) else None,
                       "card_season": cseason, "rung": rung, "commence": ev["commence_time"],
                       "day": (g.get("d") or "")[:10]}
                week_rows.append(row)
        for r in week_rows:
            if r["y"] is not None:
                graded.append(r)
        # picks: one per (event, player, market), the best-EV eligible side
        best = {}
        for r in week_rows:
            pk = pick_for(r["market"], r["rung"], r["p_model"], r["p_under"])
            if not pk:
                continue
            k = (r["event"], r["player"], r["market"])
            if k not in best or pk["ev"] > best[k][0]["ev"]:
                best[k] = (pk, r)
        for pk, r in best.values():
            if r["y"] is None:
                won = None
            elif pk["side"] in ("over", "yes"):
                won = bool(r["y"])
            else:
                won = not r["y"]
            picks.append(dict(pk, game_id=r["game"], market=r["market"], player=r["player"],
                              line=r["line"], week=w, day=r["day"], won=won,
                              state="graded" if won is not None else "void"))
        # this week's graded rungs train stage 2 for LATER weeks only
        for r in week_rows:
            if r["y"] is not None and r["p_market"] is not None:
                s2_train.append((s2_features(r["market"], r["p_stage1"], r["p_market"]), r["y"]))


# ══════════════════════════════════════════════════════════════════════
# RECORD, CALIBRATION, THE DECISION
# ══════════════════════════════════════════════════════════════════════
def logloss(p, y):
    p = min(1 - CLIP, max(CLIP, p))
    return -(math.log(p) if y else math.log(1 - p))


def calibration(rows, key):
    bk = [{"lo": 10 * i, "n": 0, "said": 0.0, "hit": 0} for i in range(10)]
    for r in rows:
        p = r.get(key)
        if p is None or r["y"] is None:
            continue
        b = bk[min(9, int(p * 10))]
        b["n"] += 1
        b["said"] += p
        b["hit"] += r["y"]
    return [{"bucket": "%d-%d%%" % (b["lo"], b["lo"] + 10), "n": L(b["n"], "DESCRIPTIVE"),
             "stated": L(round(100 * b["said"] / b["n"], 1) if b["n"] else None, "MODEL"),
             "observed": L(round(100 * b["hit"] / b["n"], 1) if b["n"] else None, "DESCRIPTIVE")}
            for b in bk]


def paired(rows):
    """design §6: d = champion loss − model loss, clustered by game."""
    pr = [r for r in rows if r.get("p_card") is not None and r.get("p_model") is not None
          and r["y"] is not None]
    d = [logloss(r["p_card"], r["y"]) - logloss(r["p_model"], r["y"]) for r in pr]
    n, mean, t, p, G = mlb_refit.paired_test_clustered(d, [r["game"] for r in pr])
    return {"n": n, "mean_d": mean, "t": t, "p": p, "clusters": G, "verdict": verdict(n, mean, p)}


def verdict(n, mean_d, p):
    if n < MIN_N:
        return "NOT YET MEASURABLE"
    return "QUALIFIES" if (mean_d is not None and mean_d > 0 and p is not None
                           and p < ALPHA) else "DOES NOT QUALIFY"


def compact(rows):
    """The paired rows the pooled decision needs, small enough to store."""
    return [[r["game"], r["market"], r["y"], round(r["p_card"], 4), round(r["p_model"], 6)]
            for r in rows if r.get("p_card") is not None and r["y"] is not None]


def pooled_decision(lg, mine, root=None):
    """Both leagues pooled (Sam's rule): this league's rows plus the other
    league's stored rows from its own latest build."""
    rows = [{"game": g, "market": mk, "y": y, "p_card": pc, "p_model": pm}
            for g, mk, y, pc, pm in mine]
    other = "ncaaf" if lg == "nfl" else "nfl"
    od = {}
    try:
        od = json.load(open(os.path.join(root or ROOT, "data", other, "latest", "fb-props-model.json"),
                            encoding="utf-8"))
    except (OSError, ValueError):
        pass
    rows += [{"game": g, "market": mk, "y": y, "p_card": pc, "p_model": pm}
             for g, mk, y, pc, pm in (od.get("paired_rows") or [])]
    dec = paired(rows)
    dec["leagues"] = sorted({r["game"].split(":")[0] for r in rows})
    # 🔴 SAM'S RULE IS POOLED OVER BOTH LEAGUES. `[found 2026-09-24]` with
    #    the other league's file missing, one league alone read as the
    #    "pooled verdict" — and college alone said QUALIFIES while the
    #    true pooled answer did not. ⛔ One league is never a verdict.
    if dec["leagues"] != ["ncaaf", "nfl"]:
        dec["verdict"] = "INCOMPLETE — needs both leagues"
    return dec


# ══════════════════════════════════════════════════════════════════════
# THIS WEEK'S PICKS
# ══════════════════════════════════════════════════════════════════════
def schedule_ctx(lg, root=None):
    """(home, away, date) -> schedule game, for venue and weather live."""
    out = {}
    for s in (2025, 2026):
        d = jz(os.path.join(root or ROOT, "data", lg, "latest", "schedule-%d.json.gz" % s)) or {}
        for g in d.get("games") or []:
            out[(g.get("home"), g.get("away"), (g.get("start") or "")[:10])] = g
    return out


def current_picks(lg, wf, root=None, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    models = {mk: s.solve() for mk, s in wf["final"].items()}
    s2 = F.fit([x for x, _ in wf["s2_train"]], [y for _, y in wf["s2_train"]]) if wf["s2_train"] else None
    resolve_team = D.team_codes(lg)
    sched = schedule_ctx(lg, root)
    H, logs, idx = wf["H"], wf["logs"], wf["idx"]
    best = {}
    for eid, (pulled, ev) in prop_snapshots(lg, root).items():
        c = ev.get("commence_time") or ""
        if c <= now:
            continue
        home, away = resolve_team(ev.get("home_team")), resolve_team(ev.get("away_team"))
        sg = None
        for dd in (c[:10], (datetime.date.fromisoformat(c[:10]) - datetime.timedelta(days=1)).isoformat()):
            sg = sg or sched.get((home, away, dd))
        for (who, mk, line), rung in rungs_of(lg, ev).items():
            pid = resolve(idx, who)
            if pid is None or not H.player.get(pid):
                continue
            season, g_last = H.player[pid][-1]
            team = g_last.get("team")
            if team not in (home, away):
                continue
            pos = next(((logs[s].get(pid) or {}).get("pos") for s in sorted(logs, reverse=True)
                        if pid in logs[s]), "")
            if (pos or "").upper() not in POSITIONS[mk]:
                continue
            ctx = {"opp": away if team == home else home, "team": team, "pos": (pos or "").upper(),
                   "day": c[:10], "home": team == home, "neutral": bool((sg or {}).get("neutral")),
                   # ⚠️ §7 is unknown before the game's own log row exists: 0 live
                   "wx": ({"roof": sg.get("roof"), "temp": sg.get("temp"), "wind": sg.get("wind")}
                          if (sg and lg == "nfl") else None)}
            # a January game belongs to the season that started the September before
            x = H.features(pid, int(c[:4]) - (1 if int(c[5:7]) < 3 else 0), mk, ctx)
            m = models.get(mk)
            if x is None or m is None:
                continue
            p1o, p1u = s1_probs(mk, m, x, line)
            if p1o is None:
                continue
            po, pu = final_probs(mk, p1o, p1u, market_prob(mk, rung), s2)
            pk = pick_for(mk, rung, po, pu)
            if not pk:
                continue
            k = (eid, who, mk)
            if k not in best or pk["ev"] > best[k]["_ev"]:
                best[k] = {"_ev": pk["ev"], "game": "%s at %s" % (ev.get("away_team"), ev.get("home_team")),
                           "game_id": eid, "commence": c, "player": who, "market": mk,
                           "market_label": card_fb.LABEL.get(mk, mk), "side": pk["side"],
                           "line": L(line, "MARKET"), "price": L(pk["price"], "MARKET"),
                           "book": collect.BOOKS.get(pk["book"], pk["book"]),
                           "model_probability": L(round(100 * pk["p"], 1), "MODEL"),
                           "break_even": L(round(100 * pk["break_even"], 1), "MARKET"),
                           "edge": L(round(100 * pk["ev"], 1), "MODEL"), "priced_at": pulled}
    out = sorted(best.values(), key=lambda r: -r["model_probability"]["value"])
    for r in out:
        r.pop("_ev", None)
    return out


def build(lg=None, root=None, out=None, logs=None):
    lg = (lg or LEAGUE).lower()
    wf = walk_forward(lg, root, logs)
    rec = {}
    for mk in markets_for(lg):
        ps = [p for p in wf["picks"] if p["market"] == mk]
        rec[mk] = dict(F.record(ps), market_label=card_fb.LABEL.get(mk, mk),
                       first_graded=min((p["day"] for p in ps), default=None),
                       last_graded=max((p["day"] for p in ps), default=None),
                       # `[Sam, 2026-09-24]` no closing-line record exists for
                       # props, so its one graded record is the evidence (spec §3)
                       verdict=F.verdict(ps))
    mine = compact(wf["graded"])
    ll = {}
    for mk in markets_for(lg):
        rs = [r for r in wf["graded"] if r["market"] == mk and r.get("p_card") is not None]
        ll[mk] = {"n": len(rs),
                  "card": (sum(logloss(r["p_card"], r["y"]) for r in rs) / len(rs)) if rs else None,
                  "model": (sum(logloss(r["p_model"], r["y"]) for r in rs) / len(rs)) if rs else None}
    doc = {"league": lg, "kind": "MODEL",
           "built_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "design": "research/fb_props_design.md",
           "books": sorted(set(collect.BOOKS[k] for k in F.books_ok(lg))),
           "price_floor": card_fb.PRICE_FLOOR, "price_ceiling": card_fb.PRICE_CEIL,
           "record": rec,
           "weeks": wf["weeks"], "stage2_weeks": wf["stage2_weeks"],
           "graded_rungs": len(wf["graded"]),
           "calibration": {"model": calibration(wf["graded"], "p_model"),
                           "card": calibration([r for r in wf["graded"] if r.get("p_card") is not None],
                                               "p_card")},
           "log_loss": ll,
           "card_logs_season": wf["card_season"], "card_seasons_published": wf["card_seasons"],
           # ⛔ reported BESIDE the pooled verdict, never as it (design §6)
           "league_only": {k: v for k, v in paired(wf["graded"]).items() if k != "verdict"},
           "paired_rows": mine,
           "note": ("Graded only at Hard Rock, FanDuel and DraftKings prices archived before "
                    "kickoff (props from September 2026). Ranges count each game once. The "
                    "card's own probabilities are recomputed with its own rating function to "
                    "compare the two on the same props.")}
    doc["decision"] = pooled_decision(lg, mine, root)
    # ~~the top card_fb.BOARD_MAX on the page, the rest in `more_picks`~~
    # 🔴 NO CAP ON MODEL PICKS `[Sam, 2026-09-24]`: "Only the Gizmo's Picks
    #    card keeps its limit." Every pick the model makes is shown.
    live = current_picks(lg, wf, root)
    doc["picks"] = live
    doc["picks_total"] = len(live)
    path = out or os.path.join(root or ROOT, "data", lg, "latest", "fb-props-model.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    d = doc["decision"]
    log("%s props model: %d graded rungs, %d picks this week; pooled verdict %s (n=%s, p=%s, leagues %s)"
        % (lg, doc["graded_rungs"], len(doc["picks"]), d["verdict"], d["n"], d["p"], d["leagues"]))
    return doc


if __name__ == "__main__":
    build()
    sys.exit(0)
