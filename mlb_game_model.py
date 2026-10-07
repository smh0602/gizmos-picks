#!/usr/bin/env python3
"""
MLB GAME MODEL: each side's runs from what the prop models read. `[Sam, 2026-10-02]`
*"use what we use for our pitcher and hitter props to predict game outcomes for mlb"*.
ONE FUNCTION FROM STORED FILES TO NUMBERS (`predict`), no fitted black box:

  a side's expected runs = the OPPOSING staff to an average lineup (its starter's
      earned runs per out over his projected outs, from his prior starts; its
      bullpen's runs per out over the rest of 27, from stored scores minus its
      starters' runs) x the side's usual NINE (total bases + walks per plate
      appearance against the league, its most-used nine of its last 10 games)
      x the VENUE (runs per game there against the league) x HOME / AWAY.

Negative-binomial runs give the win chance (a tie after nine split by the run
ratio), the -1.5 / +1.5 cover and over / under a posted total. Every rate is
shrunk toward the league by a FIXED amount (K_*), never tuned on the check.
⛔ NO LOOK-AHEAD: a game reads logs dated before its own day only, and the
starters a schedule saved BEFORE its first pitch named. No stored file holds a
lineup posted before first pitch, so every lineup is the usual one. Stdlib only.
"""
import collections
import datetime
import glob
import gzip
import json
import math
import os

from mlb_pitcher_cal import fb_model, logit    # C2's one ridge-logistic fit, no football import

ROOT = os.path.dirname(os.path.abspath(__file__))
GAME_TYPES = {"R", "F", "D", "L", "W"}    # regular season and postseason, never spring
OUTS = 27
K_START_OUTS = 60      # a starter's ER per out, toward the league, over 60 outs (20 IP)
K_START_N = 4          # his outs per start, toward the league mean, over 4 starts
K_PEN_OUTS = 150       # a bullpen's runs per out, toward the league, over 150 outs
K_PA = 60              # a hitter's (TB + BB) per PA, toward the league, over 60 PA
K_VENUE = 30           # a venue's runs per game, toward the league, over 30 games
BANDS = ((50, 55), (55, 60), (60, 70), (70, 101))


def _load(path):
    try:
        return json.load(gzip.open(path, "rt") if path.endswith(".gz") else open(path, encoding="utf-8"))
    except Exception:
        return {}


class State:
    """Everything known at the START of a day: running sums over earlier days only."""

    def __init__(self):
        self.lg = collections.Counter()
        self.pit = collections.defaultdict(collections.Counter)    # pitcher id -> er, outs, n
        self.pen = collections.defaultdict(collections.Counter)    # team -> runs, outs
        self.ven = collections.defaultdict(collections.Counter)    # venue id -> runs, games
        self.hit = collections.defaultdict(collections.Counter)    # hitter id -> bases, pa
        self.lineups = collections.defaultdict(lambda: collections.deque(maxlen=10))

    def rates(self):
        g = self.lg
        tg = max(g["team_games"], 1)
        mu = g["runs"] / tg if g["team_games"] else 4.5
        var = g["runs_sq"] / tg - mu * mu if g["team_games"] > 30 else 2 * mu
        return {"mu": mu,
                "r": mu * mu / (var - mu) if var > mu * 1.05 else 50.0,
                "home": (g["home_runs"] / g["home_games"]) / mu if g["home_games"] > 30 else 1.02,
                "away": (g["away_runs"] / g["away_games"]) / mu if g["away_games"] > 30 else 0.98,
                "s_rate": g["s_er"] / g["s_outs"] if g["s_outs"] else mu / OUTS,
                "s_outs": g["s_outs"] / g["s_n"] if g["s_n"] else 16.0,
                "b_rate": g["b_runs"] / g["b_outs"] if g["b_outs"] else mu / OUTS,
                "bases": g["bases"] / g["pa"] if g["pa"] else 0.40}

    def usual(self, team):
        """The nine who started most often in the team's last 10 lineups."""
        c = collections.Counter(p for lu in self.lineups[team] for p in lu)
        return [p for p, _ in c.most_common(9)]


def pitching(st, R, pid, team):
    """Runs this pitching staff allows an average lineup at a neutral park."""
    p, b = st.pit.get(str(pid)) or collections.Counter(), st.pen.get(team) or collections.Counter()
    s_rate = (p["er"] + K_START_OUTS * R["s_rate"]) / (p["outs"] + K_START_OUTS)
    s_outs = min(OUTS, (p["outs"] + K_START_N * R["s_outs"]) / (p["n"] + K_START_N))
    b_rate = (b["runs"] + K_PEN_OUTS * R["b_rate"]) / (b["outs"] + K_PEN_OUTS)
    return s_outs * s_rate + (OUTS - s_outs) * b_rate


def lineup_factor(st, R, pids):
    vals = [(st.hit[str(p)]["bases"] + K_PA * R["bases"]) / (st.hit[str(p)]["pa"] + K_PA)
            for p in pids] or [R["bases"]]
    return (sum(vals) / len(vals)) / R["bases"]


def venue_factor(st, R, vid):
    v = st.ven.get(vid) or collections.Counter()
    return ((v["runs"] + K_VENUE * 2 * R["mu"]) / (v["games"] + K_VENUE)) / (2 * R["mu"])


def nb(mean, r, kmax=30):
    p = r / (r + mean)
    out = [math.exp(math.lgamma(k + r) - math.lgamma(r) - math.lgamma(k + 1)
                    + r * math.log(p) + k * math.log(1 - p)) for k in range(kmax)]
    s = sum(out)
    return [x / s for x in out]


def chances(lh, la, r, total=None):
    """Win, cover and over/under chances (percent, UNROUNDED: a side is decided on
    the exact number and rounded only where it is shown) from the two run figures."""
    H, A = nb(lh, r), nb(la, r)
    joint = [(h, a, ph * pa) for h, ph in enumerate(H) for a, pa in enumerate(A)]
    tie = sum(w for h, a, w in joint if h == a)
    win_h = sum(w for h, a, w in joint if h > a) + tie * lh / (lh + la)
    out = {"win": {"home": 100 * win_h, "away": 100 * (1 - win_h)},
           "run_line": {"home -1.5": 100 * sum(w for h, a, w in joint if h - a >= 2),
                        "home +1.5": 100 * sum(w for h, a, w in joint if h - a >= -1)}}
    out["run_line"]["away +1.5"] = 100 - out["run_line"]["home -1.5"]
    out["run_line"]["away -1.5"] = 100 - out["run_line"]["home +1.5"]
    if total is not None:
        o = sum(w for h, a, w in joint if h + a > total)
        u = sum(w for h, a, w in joint if h + a < total)
        out["total"] = {"line": total, "over": 100 * o / (o + u), "under": 100 * u / (o + u)}
    return out


def predict(st, home, away, sp_home, sp_away, lu_home, lu_away, venue, total=None):
    """THE one function: state + the day's named starters and lineups -> numbers."""
    R = st.rates()
    v = venue_factor(st, R, venue)
    pa_home = pitching(st, R, sp_home, home)       # what HOME's pitching allows
    pa_away = pitching(st, R, sp_away, away)
    lh = pa_away * lineup_factor(st, R, lu_home) * v * R["home"]
    la = pa_home * lineup_factor(st, R, lu_away) * v * R["away"]
    out = chances(lh, la, R["r"], total)
    out["expected_runs"] = {"home": round(lh, 2), "away": round(la, 2)}
    out["total_at"] = lambda t: chances(lh, la, R["r"], t)["total"]
    return out


# ══════════════════════════════════════════════════════════════════════
# The stored files, by day
# ══════════════════════════════════════════════════════════════════════
def inputs(root=ROOT):
    d = os.path.join(root, "data", "latest")
    S, P, H, L = (_load(os.path.join(d, f)) for f in
                  ("scores.json.gz", "pitchers.json.gz", "hitters.json.gz", "lineups.json.gz"))
    starts, hits = collections.defaultdict(list), collections.defaultdict(list)
    for pid, p in (P.get("players") or {}).items():
        for g in p.get("g") or []:
            if g.get("gs"):
                starts[g["d"]].append((pid, g))
    for pid, p in (H.get("players") or {}).items():
        for g in p.get("g") or []:
            hits[g["d"]].append((pid, g))
    lus = {}
    for day, rows in (L.get("days") or {}).items():
        t = collections.defaultdict(list)
        for x in sorted(rows, key=lambda x: x.get("slot") or 0):
            if x.get("started") and not x.get("sub"):
                t[x["team"]].append(str(x["pid"]))
        lus[day] = dict(t)
    return {"scores": S.get("days") or {}, "starts": starts, "hits": hits, "lineups": lus}


def starter(I, day, team_home, opp, home_side):
    """(pitcher id) who started for one side, from the start logs; None if not exactly one."""
    c = [pid for pid, g in I["starts"].get(day, ())
         if g.get("o") == opp and bool(g.get("h")) == home_side]
    return c[0] if len(c) == 1 else None


def advance(st, I, day):
    """Fold one whole day's games into the state (called AFTER the day is predicted)."""
    games = [g for g in I["scores"].get(day, ()) if g.get("gameType") in GAME_TYPES]
    pairs = collections.Counter((g["away"], g["home"]) for g in games)
    for g in games:
        h, a = g.get("home_r"), g.get("away_r")
        if h is None or a is None:
            continue
        st.lg.update(runs=h + a, runs_sq=h * h + a * a, team_games=2, home_runs=h,
                     home_games=1, away_runs=a, away_games=1)
        st.ven[g.get("venue_id")].update(runs=h + a, games=1)
        if pairs[(g["away"], g["home"])] > 1:
            continue                                    # a doubleheader: no bullpen split
        for team, opp, home_side, allowed in ((g["home"], g["away"], True, a),
                                              (g["away"], g["home"], False, h)):
            pid = starter(I, day, team, opp, home_side)
            s = next((x for p, x in I["starts"].get(day, ()) if p == pid), None)
            if s is None:
                continue
            runs, outs = max(0, allowed - (s.get("er") or 0)), max(0, OUTS - (s.get("outs") or 0))
            st.pen[team].update(runs=runs, outs=outs)
            st.lg.update(b_runs=runs, b_outs=outs)
    for pid, s in I["starts"].get(day, ()):
        st.pit[pid].update(er=s.get("er") or 0, outs=s.get("outs") or 0, n=1)
        st.lg.update(s_er=s.get("er") or 0, s_outs=s.get("outs") or 0, s_n=1)
    for pid, x in I["hits"].get(day, ()):
        st.hit[pid].update(bases=(x.get("tb") or 0) + (x.get("bb") or 0), pa=x.get("pa") or 0)
        st.lg.update(bases=(x.get("tb") or 0) + (x.get("bb") or 0), pa=x.get("pa") or 0)
    for team, lu in (I["lineups"].get(day) or {}).items():
        if len(lu) == 9:
            st.lineups[team].append(lu)


def pregame(g, at):
    """One game as a schedule snapshot named it before first pitch."""
    t = g.get("teams") or {}
    team = lambda s: (t.get(s) or {}).get("team") or {}
    sp = lambda s: (t.get(s) or {}).get("probablePitcher") or {}
    return {"game_pk": g.get("gamePk"), "commence": g.get("gameDate"), "pulled_at": at,
            "home": team("home").get("name"), "away": team("away").get("name"),
            "home_id": team("home").get("id"), "away_id": team("away").get("id"),
            "sp_home": sp("home").get("id"), "sp_away": sp("away").get("id"),
            "sp_home_name": sp("home").get("fullName"), "sp_away_name": sp("away").get("fullName"),
            "venue": (g.get("venue") or {}).get("id"), "game_type": g.get("gameType")}


def schedules(root=ROOT):
    """gamePk -> that game as the LAST schedule snapshot pulled BEFORE its own first
    pitch listed it. ⛔ The starters, teams and venue a prediction reads come from
    here, never from the game's own box score or start log (both written after it)."""
    best = {}
    for p in glob.glob(os.path.join(root, "data", "[0-9]*", "schedule", "*.json.gz")):
        d = _load(p)
        at = d.get("pulled_at") or ""
        for dd in (d.get("schedule") or {}).get("dates") or []:
            for g in dd.get("games") or []:
                fp, pk = g.get("gameDate") or "", g.get("gamePk")
                if at and fp and at < fp and (pk not in best or best[pk][0] < at):
                    best[pk] = (at, g)
    return {pk: pregame(g, at) for pk, (at, g) in best.items()}


def walk(I, S):
    """Predict every finished game that a schedule snapshot named BEFORE its first
    pitch, from the days before it: the starters that snapshot named and each
    side's usual nine (no stored file holds a lineup posted before first pitch).
    -> (state, records)."""
    st, recs = State(), []
    for day in sorted(I["scores"]):
        games = [g for g in I["scores"][day] if g.get("gameType") in GAME_TYPES]
        pairs = collections.Counter((g["away"], g["home"]) for g in games)
        for g in games:
            x = S.get(g.get("gamePk"))
            if (g.get("home_r") is None or pairs[(g["away"], g["home"])] > 1 or not x
                    or not (x["sp_home"] and x["sp_away"])):
                continue
            recs.append(dict(day=day, game=g, inputs=x, model=predict(
                st, x["home"], x["away"], x["sp_home"], x["sp_away"],
                st.usual(x["home"]), st.usual(x["away"]), x["venue"])))
        advance(st, I, day)
    return st, recs


# ══════════════════════════════════════════════════════════════════════
# The books' own no-vig chance, from the stored gamelines pulls (2026-08-22 on)
# ══════════════════════════════════════════════════════════════════════
def _dec(a):
    return 1 + (a / 100.0 if a > 0 else 100.0 / -a)


def _nv(a, b):
    qa, qb = 1 / _dec(a), 1 / _dec(b)
    return qa / (qa + qb)


def _et_day(iso):
    t = datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ") - datetime.timedelta(hours=4)
    return t.strftime("%Y-%m-%d")       # EDT covers the whole MLB season


def _mode(xs):
    return collections.Counter(xs).most_common(1)[0][0] if xs else None


def books(root=ROOT):
    """(ET day, away, home) -> the books' no-vig chances from the LAST pull before first pitch."""
    last = {}
    for p in sorted(glob.glob(os.path.join(root, "data", "2026-*", "gamelines", "*.json.gz"))):
        d = _load(p)
        for g in d.get("games") or []:
            c = g.get("commence") or ""
            if c and (d.get("pulled_at") or "") < c:
                last[(_et_day(c), g.get("away"), g.get("home"))] = g
    out = {}
    for k, g in last.items():
        _, away, home = k
        bk = [b for b in (g.get("books") or {}).values()]
        ml = [_nv(b["h2h"][home], b["h2h"][away]) for b in bk
              if home in (b.get("h2h") or {}) and away in b["h2h"]]
        rl = [(b["spreads"][home]["pt"], b["spreads"][home]["px"], b["spreads"][away]["px"])
              for b in bk if home in (b.get("spreads") or {}) and away in b["spreads"]
              and abs(b["spreads"][home].get("pt") or 0) == 1.5]
        to = [(b["totals"]["Over"]["pt"], b["totals"]["Over"]["px"], b["totals"]["Under"]["px"])
              for b in bk if "Over" in (b.get("totals") or {}) and "Under" in b["totals"]
              and b["totals"]["Over"].get("pt") == b["totals"]["Under"].get("pt")]
        rp, tp = _mode([x[0] for x in rl]), _mode([x[0] for x in to])
        rl, to = [_nv(a, b) for p, a, b in rl if p == rp], [_nv(a, b) for p, a, b in to if p == tp]
        out[k] = {"win_home": 100 * sum(ml) / len(ml) if ml else None,
                  "rl_home_pt": rp, "rl_home": 100 * sum(rl) / len(rl) if rl else None,
                  "total": tp, "over": 100 * sum(to) / len(to) if to else None}
    return out


def _band(p):
    return next(("%d-%d" % (lo, hi) if hi < 101 else "%d+" % lo)
                for lo, hi in BANDS if lo <= p < hi)


def _side(p, hit, books=None):
    """(chance for the side given 50%+, did it win, the books' chance for that same side)."""
    s = p >= 50
    return (p if s else 100 - p, hit == s, None if books is None else (books if s else 100 - books))


def _table(rows):
    """rows of _side() -> per band: n, mean chance, won %, the books' mean chance on those games."""
    acc = collections.OrderedDict(("%d-%d" % b if b[1] < 101 else "%d+" % b[0], [0, 0, 0.0, 0.0, 0])
                                  for b in BANDS)
    for p, won, bk in rows:
        a = acc[_band(p)]
        a[0] += 1
        a[1] += won
        a[2] += p
        if bk is not None:
            a[3] += bk
            a[4] += 1
    out = [{"band": k, "n": n, "chance": round(s / n, 1) if n else None,
            "won": round(100.0 * w / n, 1) if n else None,
            "books": round(sb / nb_, 1) if nb_ else None} for k, (n, w, s, sb, nb_) in acc.items()]
    n = len(rows)
    out.append({"band": "all", "n": n, "chance": round(sum(r[0] for r in rows) / n, 1) if n else None,
                "won": round(100.0 * sum(r[1] for r in rows) / n, 1) if n else None,
                "books": None})
    return out


def off_bands(table):
    """Sam's item 3 trigger: a band OFF BY MORE THAN 5 POINTS ON 100 OR MORE GAMES."""
    return [b["band"] for b in table if b["band"] != "all" and b["n"] >= 100
            and abs(b["chance"] - b["won"]) > 5]


# ══════════════════════════════════════════════════════════════════════
# THE CORRECTION. `[Sam, 2026-10-02]` "If a band is off by more than 5
# points on 100 or more games, correct it the way the pitcher correction
# (C2) does, fitted walk-forward, and say so. ... Do not tune on it beyond
# that correction."
#   C2's form exactly: `fb_model.fit` (ridge logistic, its own RIDGE and
#   MIN_TRAIN) on [logit(model's chance), logit(the market's chance)],
#   refitted each day on earlier graded games only. ONE change of input,
#   said here: the market's chance is the books' NO-VIG chance for the home
#   side / the over, not one side's break-even, so the two sides still sum
#   to 100.
#   MEASURED 2026-10-03 (`python mlb_game_model.py check`; every game with a
#   schedule saved before first pitch, 08-22 on):
#     moneyline  no band off
#     run line   50-55: 102 games said 52.7, won 58.8 -> MEASURED ONLY
#     total      55-60: 152 said 57.1, won 48.7; 60-70: 102 said 63.1,
#                won 48.0 -> CORRECTED, and ⛔ NOT ON THE CARD (below)
# 🔴 THE RUN LINE IS THE MODEL'S OWN CHANCE. `[2026-10-03]` ~~corrected~~:
#   its fit put a NEGATIVE weight on the model's chance on every day it was
#   fitted (-0.03 to -0.25) and +0.45 to +0.72 on the books', so the
#   "corrected" number was the books' tilted against the model. On the same
#   326 games the model's own side won 59.8%, the corrected 60.1%, the
#   books' 61.7%, and it picked the OTHER side on 47 (14%) while its row
#   said "the game model gives". ✅ Its corrected table stays in the check
#   as a measurement (MEASURED); nothing a person reads uses it.
#   CORRECTED: the corrections the file applies. MEASURED: the corrections
#   the check measures. `check.<market>.off_bands` says whether the newest
#   games still agree.
# ⛔ TOTALS NEVER REACH THE CARD, THE PAGE OR THE RECORD'S GAME-LINE LINE.
#   `[Sam, 2026-10-03]` "go on with moneyline and run line only. Totals stay
#   in mlb-game-model.json with both records (uncorrected and corrected) and
#   keep being graded there". Only Sam's decision brings them onto the card
#   (`card.GL_MARKETS`, test_mlb_game_lines.py).
# ══════════════════════════════════════════════════════════════════════
CORRECTED = ("total",)
MEASURED = ("run_line", "total")
MARKETS = ("moneyline", "run_line", "total")


def features(model_pct, books_pct):
    return [logit(model_pct / 100.0), logit(books_pct / 100.0)]


def mapping(rows, before):
    """The fit on every graded game dated before `before`; None below MIN_TRAIN.
    rows: [(day, model %, books %, the home side / the over won)]."""
    tr = [g for g in rows if g[0] < before]
    m = fb_model.fit([features(g[1], g[2]) for g in tr], [1 if g[3] else 0 for g in tr])
    return None if m is None else dict(m, n_train=len(tr), before=before)


def corrected(m, model_pct, books_pct):
    """The corrected chance (percent, unrounded), or None with no mapping."""
    if m is None or model_pct is None or books_pct is None:
        return None
    return 100.0 * fb_model.predict(m, features(model_pct, books_pct))


def graded(recs, B):
    """market -> [(day, model %, books %, won)] for the HOME side (moneyline, run
    line at the books' point) and the OVER, on priced games; pushes left out."""
    out = {mk: [] for mk in MARKETS}
    for r in recs:
        g, m = r["game"], r["model"]
        b = B.get((r["day"], g["away"], g["home"]))
        if not b:
            continue
        margin, runs = g["home_r"] - g["away_r"], g["home_r"] + g["away_r"]
        if b["win_home"] is not None:
            out["moneyline"].append((r["day"], m["win"]["home"], b["win_home"], margin > 0))
        if b["rl_home"] is not None:
            pt = b["rl_home_pt"]
            out["run_line"].append((r["day"], m["run_line"]["home %+.1f" % pt], b["rl_home"],
                                    margin + pt > 0))
        if b["over"] is not None and runs != b["total"]:
            out["total"].append((r["day"], m["total_at"](b["total"])["over"], b["over"],
                                 runs > b["total"]))
    return out


def check(recs, B):
    """THE WALK-FORWARD RECORD, per market: the side given 50%+ by band, with the
    books' own no-vig chance for that same side on the same games beside it,
    and (for a corrected market) the same after the correction."""
    out = {"games": len(recs), "from": min((r["day"] for r in recs), default=None),
           "through": max((r["day"] for r in recs), default=None)}
    for mk, rows in graded(recs, B).items():
        t = {"model": _table([_side(p, w, bk) for _, p, bk, w in rows]),
             "books": _table([_side(bk, w) for _, p, bk, w in rows])}
        t["off_bands"] = off_bands(t["model"])
        if mk in MEASURED:
            maps, corr = {}, []
            for d, p, bk, w in rows:
                if d not in maps:
                    maps[d] = mapping(rows, d)
                c = corrected(maps[d], p, bk)
                if c is not None:
                    corr.append(_side(c, w, bk))
            t["corrected"] = _table(corr)
            t["corrected_off_bands"] = off_bands(t["corrected"])
            t["corrected_from"] = min((d for d, x in maps.items() if x), default=None)
        out[mk] = t
    return out


# ══════════════════════════════════════════════════════════════════════
# THE SLATE -> data/latest/mlb-game-model.json (built by the card run, free)
# ══════════════════════════════════════════════════════════════════════
def _r1(v):
    return None if v is None else round(v, 1)


def slate_game(st, x, b, maps):
    """One slate game's numbers. `card` holds what a card row reads: the model's
    own chance for the moneyline and the run line (neither is in CORRECTED)."""
    b = b or {}
    lu_h, lu_a = st.usual(x["home"]), st.usual(x["away"])
    m = predict(st, x["home"], x["away"], x["sp_home"], x["sp_away"], lu_h, lu_a,
                x["venue"], b.get("total"))
    fix = lambda mk, p, bk: corrected(maps.get(mk), p, bk) if mk in CORRECTED else p
    pt = b.get("rl_home_pt")
    ml = fix("moneyline", m["win"]["home"], b.get("win_home"))
    rl = fix("run_line", m["run_line"]["home %+.1f" % pt], b.get("rl_home")) if pt is not None else None
    ov = fix("total", m["total"]["over"], b.get("over")) if "total" in m else None
    out = {k: x[k] for k in ("game_pk", "commence", "away", "home", "away_id", "home_id", "venue")}
    out.update({
        "starters": {s: {"id": x["sp_" + s], "name": x["sp_%s_name" % s]} for s in ("home", "away")},
        "lineup": {"home": {"confirmed": False, "players": lu_h},
                   "away": {"confirmed": False, "players": lu_a}},
        "expected_runs": m["expected_runs"],
        "win": {k: _r1(v) for k, v in m["win"].items()},
        "run_line": {k: _r1(v) for k, v in m["run_line"].items()},
        "total": None if "total" not in m else {
            "line": b["total"], "over": _r1(m["total"]["over"]), "under": _r1(m["total"]["under"]),
            "over_corrected": _r1(ov), "under_corrected": None if ov is None else _r1(100 - ov)},
        "books": {k: (v if k in ("rl_home_pt", "total") else _r1(v)) for k, v in b.items()},
        "card": {"moneyline": None if ml is None else {"home": ml, "away": 100 - ml},
                 "run_line": None if rl is None else {"point": pt, "home": rl, "away": 100 - rl}},
    })
    return out


def next_slate(root=ROOT, now=None):
    """The ET day of the earliest scheduled game not yet started (today's ET
    date when none is stored): the slate the Game Lines tab shows next."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    days = [_et_day(x["commence"]) for x in schedules(root).values()
            if (x.get("commence") or "") > at and x.get("game_type") in GAME_TYPES]
    return min(days) if days else _et_day(at)


def build(day, root=ROOT, write=True):
    """Every game on ET day `day` that a schedule saved before first pitch names,
    with its numbers, its inputs and the check's record. -> the doc."""
    I, S, B = inputs(root), schedules(root), books(root)
    st, recs = walk(I, S)
    G = graded(recs, B)
    maps = {mk: mapping(G[mk], day) for mk in CORRECTED}
    games = [slate_game(st, x, B.get((day, x["away"], x["home"])), maps)
             for x in sorted(S.values(), key=lambda x: x["commence"] or "")
             if x["commence"] and _et_day(x["commence"]) == day
             and x.get("game_type") in GAME_TYPES and x["home"] and x["away"]]
    doc = {"generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "kind": "mlb-game-model", "slate": day, "generated_by": "mlb_game_model.py, in the card run",
           "method": ("Each side's runs: the opposing starter's earned runs per out over his "
                      "projected outs and its bullpen's runs per out over the rest, times the "
                      "side's usual nine's bases per plate appearance against the league, times "
                      "the park and home field; negative-binomial runs give the win, run-line "
                      "and total chances. Starters are the ones a schedule saved before first "
                      "pitch named; no stored file holds a lineup posted before first pitch, so "
                      "every lineup is the usual one."),
           "corrected": list(CORRECTED), "measured": list(MEASURED),
           "correction_maps": {mk: None if m is None else {k: m[k] for k in ("mu", "sd", "w", "n_train", "before")}
                               for mk, m in maps.items()},
           "totals_on_card": False,
           "totals_rule": ("Sam, 2026-10-03: totals stay in this file with both records and are "
                           "never on the card, the page or the record's game-line line until he "
                           "decides otherwise."),
           "games": games, "check": check(recs, B)}
    if write:
        os.makedirs(os.path.join(root, "data", "latest"), exist_ok=True)
        with open(os.path.join(root, "data", "latest", "mlb-game-model.json"), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, separators=(",", ":"))
    return doc


def _print_check(c):
    print("games %s, %s -> %s" % (c["games"], c["from"], c["through"]))
    for mk in MARKETS:
        for key in ("model", "corrected"):
            if key not in c[mk]:
                continue
            print("%s, %s" % (mk.upper(), key))
            for b in c[mk][key]:
                print("  %-6s n %4d  said %5s  won %5s  books %5s"
                      % (b["band"], b["n"], b["chance"], b["won"], b["books"]))
        print("  books' own side: all %s won %s%%; off by 5+ on 100+: %s%s"
              % (c[mk]["books"][-1]["n"], c[mk]["books"][-1]["won"], c[mk]["off_bands"],
                 "; corrected from %s, still off: %s" % (c[mk]["corrected_from"],
                                                          c[mk]["corrected_off_bands"])
                 if mk in MEASURED else ""))


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["check"]:
        _st, _recs = walk(inputs(), schedules())
        _print_check(check(_recs, books()))
