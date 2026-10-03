#!/usr/bin/env python3
"""
MLB GAME MODEL: each side's runs from what the prop models read. `[Sam, 2026-10-02]`
*"use what we use for our pitcher and hitter props to predict game outcomes for mlb"*.

ONE FUNCTION FROM STORED FILES TO NUMBERS (`predict`), no fitted black box:

  expected runs for a side = the OPPOSING pitching to an average lineup
        (its starter's earned runs per out over his projected outs, from his
         prior starts in the start logs; its bullpen's runs per out over the
         rest of 27 outs, from stored scores minus its starters' runs)
      x the side's LINEUP (its nine starters' total bases + walks per plate
         appearance from the hitter logs, against the league; the confirmed
         lineup, else the usual one from its last 10 games)
      x the VENUE (runs per game there against the league) x HOME / AWAY.

Two run figures -> negative-binomial run distributions (their spread from this
season's team runs) -> the win chance (a tie after nine is split by the run
ratio), the chance to cover -1.5 / +1.5, and over / under a posted total.
Every rate is shrunk toward the league by a FIXED amount (K_*), set before the
walk-forward check and never tuned on it.

⛔ NO LOOK-AHEAD. A game reads only logs dated BEFORE its own day (`State` is
advanced a whole day after that day's games are predicted). The starters and
the lineup named for the day are posted before first pitch. Stdlib only.
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
    return s_outs * s_rate + (OUTS - s_outs) * b_rate, s_outs


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
    pa_home, outs_h = pitching(st, R, sp_home, home)       # what HOME's pitching allows
    pa_away, outs_a = pitching(st, R, sp_away, away)
    lh = pa_away * lineup_factor(st, R, lu_home) * v * R["home"]
    la = pa_home * lineup_factor(st, R, lu_away) * v * R["away"]
    out = chances(lh, la, R["r"], total)
    out["expected_runs"] = {"home": round(lh, 2), "away": round(la, 2)}
    out["total_at"] = lambda t: chances(lh, la, R["r"], t)["total"]
    out["starter_outs"] = {"home": round(outs_h, 1), "away": round(outs_a, 1)}
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
    return {"scores": S.get("days") or {}, "starts": starts, "hits": hits, "lineups": lus,
            "names": {pid: p.get("name") for pid, p in (P.get("players") or {}).items()}}


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


def walk(I, through=None):
    """Predict every finished game from the days before it. -> (state, records)."""
    st, recs = State(), []
    for day in sorted(I["scores"]):
        if through and day > through:
            break
        games = [g for g in I["scores"][day] if g.get("gameType") in GAME_TYPES]
        pairs = collections.Counter((g["away"], g["home"]) for g in games)
        for g in games:
            if g.get("home_r") is None or pairs[(g["away"], g["home"])] > 1:
                continue
            sh = starter(I, day, g["home"], g["away"], True)
            sa = starter(I, day, g["away"], g["home"], False)
            if not (sh and sa):
                continue
            lu = I["lineups"].get(day) or {}
            lh = lu.get(g["home"]) if len(lu.get(g["home"]) or []) == 9 else st.usual(g["home"])
            la = lu.get(g["away"]) if len(lu.get(g["away"]) or []) == 9 else st.usual(g["away"])
            recs.append(dict(day=day, game=g, model=predict(st, g["home"], g["away"], sh, sa,
                                                            lh, la, g.get("venue_id"))))
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
# THE TOTALS CORRECTION. `[Sam, 2026-10-02]` "If a band is off by more than
# 5 points on 100 or more games, correct it the way the pitcher correction
# (C2) does, fitted walk-forward, and say so. ... Do not tune on it beyond
# that correction."
#   MEASURED 2026-10-03 (`python mlb_game_model.py check`, games 03-25 ->
#   09-27): the total had two such bands (55-60: 145 games said 57.2, won
#   44.8; 60-70: 106 said 63.0, won 47.2; every 50%+ side together 49.1% on
#   460). Moneyline and run line had none. Corrected, walk-forward from
#   09-03 (the first 150 priced games only train it): 52.9% on 310 games,
#   the books' favoured side 52.6% on the same games.
#   C2's form exactly: `fb_model.fit` (ridge logistic, its own RIDGE and
#   MIN_TRAIN) on [logit(model's chance), logit(the market's chance)], refitted
#   each day on earlier graded games only. ONE change of input, said here:
#   the market's chance is the books' NO-VIG over chance, not one side's
#   break-even, so over and under still sum to 100.
# ══════════════════════════════════════════════════════════════════════
CORRECTED = ("total",)


def total_features(model_over, books_over):
    return [logit(model_over / 100.0), logit(books_over / 100.0)]


def total_mapping(graded, before):
    """The fit on every graded game dated before `before`; None below MIN_TRAIN.
    graded: [(day, model over %, books over %, went over)]."""
    tr = [g for g in graded if g[0] < before]
    m = fb_model.fit([total_features(g[1], g[2]) for g in tr], [1 if g[3] else 0 for g in tr])
    return None if m is None else dict(m, n_train=len(tr), before=before)


def corrected_over(m, model_over, books_over):
    """The corrected over chance (percent), or None with no mapping."""
    if m is None or model_over is None or books_over is None:
        return None
    return 100.0 * fb_model.predict(m, total_features(model_over, books_over))


def graded_totals(recs, B):
    """[(day, model over %, books over %, went over)] for every priced game, pushes left out."""
    out = []
    for r in recs:
        g, b = r["game"], B.get((r["day"], r["game"]["away"], r["game"]["home"]))
        if b and b["over"] is not None and g["home_r"] + g["away_r"] != b["total"]:
            out.append((r["day"], r["model"]["total_at"](b["total"])["over"], b["over"],
                        g["home_r"] + g["away_r"] > b["total"]))
    return out


def check(recs, B):
    """The walk-forward record: the side given 50%+ by band, with the books' own
    no-vig chance for that same side on the same games beside it."""
    ml, ml_same, ml_books, rl, rl_books = ([] for _ in range(5))
    for r in recs:
        g, m = r["game"], r["model"]
        margin = g["home_r"] - g["away_r"]
        ml.append(_side(m["win"]["home"], margin > 0))
        b = B.get((r["day"], g["away"], g["home"]))
        if not b:
            continue
        if b["win_home"] is not None:
            ml_same.append(_side(m["win"]["home"], margin > 0, b["win_home"]))
            ml_books.append(_side(b["win_home"], margin > 0))
        if b["rl_home"] is not None:
            pt = b["rl_home_pt"]
            pm = m["run_line"]["home %+.1f" % pt]
            rl.append(_side(pm, margin + pt > 0, b["rl_home"]))
            rl_books.append(_side(b["rl_home"], margin + pt > 0))
    graded = graded_totals(recs, B)
    to = [_side(po, over, bo) for _, po, bo, over in graded]
    to_books = [_side(bo, over) for _, po, bo, over in graded]
    to_corr, maps = [], {}
    for d, po, bo, over in graded:                      # walk-forward: earlier days only
        if d not in maps:
            maps[d] = total_mapping(graded, d)
        c = corrected_over(maps[d], po, bo)
        if c is not None:
            to_corr.append(_side(c, over, bo))
    out = {"moneyline": {"model": _table(ml), "model_on_priced_games": _table(ml_same),
                         "books_on_priced_games": _table(ml_books)},
           "run_line": {"model": _table(rl), "books": _table(rl_books)},
           "total": {"model": _table(to), "books": _table(to_books),
                     "corrected": _table(to_corr),
                     "corrected_from": min((d for d, m in maps.items() if m), default=None)}}
    out["off_bands"] = {k: off_bands(out[k]["model"]) for k in ("moneyline", "run_line", "total")}
    out["off_bands"]["total_corrected"] = off_bands(out["total"]["corrected"])
    return out


def _print_check(c):
    for name, key in (("MONEYLINE, the season", ("moneyline", "model")),
                      ("MONEYLINE, priced games", ("moneyline", "model_on_priced_games")),
                      ("RUN LINE (1.5), priced games", ("run_line", "model")),
                      ("TOTAL, priced games, raw", ("total", "model")),
                      ("TOTAL, priced games, corrected", ("total", "corrected"))):
        print(name)
        for b in c[key[0]][key[1]]:
            print("  %-6s n %4d  model %5s  won %5s  books %5s"
                  % (b["band"], b["n"], b["chance"], b["won"], b["books"]))
    print("off by more than 5 on 100+ games:", c["off_bands"])
    print("correction fitted from:", c["total"]["corrected_from"])


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["check"]:
        I = inputs()
        _st, _recs = walk(I)
        _print_check(check(_recs, books()))
