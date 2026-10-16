#!/usr/bin/env python3
"""fb_score_model.py — THE SCORE-FIRST FOOTBALL GAME MODEL, REPORT ONLY. `[Sam, 2026-10-15]`

"your trying to predict the score of both team. this directly results in predicting
the spread, point total, moneyline." Settings: research/fb_score_model_design.md.
    LEAGUE=nfl python fb_score_model.py    # -> data/<lg>/latest/fb-score-model.json
1. Each side's points from `fb_matchups`' points table plus the home edge it
   MEASURES (Sam's fixed +1.5 is challenger AV in the weekly contest, untouched).
2. A matchup layer (pass vs pass, rush vs rush, both teams' pace), its weights
   fitted on earlier weeks only.
3. Chances from the predicted score's normal curve (sigma measured walk-forward),
   a calibrated sigma x k beside it.
⛔ REPORT ONLY: no pick, chance, card row or page reads this file or module.
⛔ POINT IN TIME: games dated before the Monday only. ⚠️ STDLIB ONLY.
"""
import collections
import datetime
import json
import math
import os
import statistics
import sys

import fb_matchups as FM
import fb_model as F

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUE = os.environ.get("LEAGUE", "nfl")
DESIGN = "research/fb_score_model_design.md"
MATCH_UNITS = ("pass_yds", "rush_yds", "plays")      # ⛔ design §2: pass, rush, pace
MATCH_RIDGE = 100.0
MIN_SIDES = 200
MIN_SIGMA = 100
MIN_CAL = 100
K_GRID = tuple(round(1.0 + 0.05 * i, 2) for i in range(41))     # 1.00 ... 3.00
BANDS = (0.50, 0.55, 0.60, 0.65, 0.70)
VERSIONS = ("score_curve", "calibrated", "fb_model")
PHI = statistics.NormalDist()
SIDES = {"spread": ("home", "away"), "total": ("over", "under"), "moneyline": ("home", "away")}
NOTE = ("Report only. No pick, chance, card row or page reads this file; switching the "
        "game-line picks to the score model is Sam's decision after he sees the backtest.")


def base_score(tables, r):
    """(home points, away points) from the points table as of the row's Monday, or None."""
    s = tables.solve("points", r["day"])
    h, a = r["home"], r["away"]
    if h not in s["teams"] or a not in s["teams"]:
        return None
    at_home = 0.0 if r["sig"]["neutral"] else 1.0
    return (s["base"] + s["hpe"] * at_home + s["O"][h] - s["D"][a],
            s["base"] + s["O"][a] - s["D"][h])


def matchup(tables, r):
    """[home side, away side] inputs (design §2): pass gap, rush gap, combined pace."""
    h, a, d = r["home"], r["away"], r["day"]
    pace = tables.gap(h, a, "plays", d) + tables.gap(a, h, "plays", d)
    return [[tables.gap(h, a, "pass_yds", d), tables.gap(h, a, "rush_yds", d), pace],
            [tables.gap(a, h, "pass_yds", d), tables.gap(a, h, "rush_yds", d), pace]]


def fit_matchup(sides):
    """Points per unit of each matchup input: ridge least squares on [(inputs,
    real points - base score)], inputs scaled to unit root mean square, no intercept."""
    k = len(MATCH_UNITS)
    if len(sides) < MIN_SIDES:
        return [0.0] * k
    sd = [math.sqrt(sum(x[j] ** 2 for x, _ in sides) / len(sides)) or 1.0 for j in range(k)]
    A = [[sum(x[i] * x[j] for x, _ in sides) / (sd[i] * sd[j]) + (MATCH_RIDGE if i == j else 0.0)
          for j in range(k)] for i in range(k)]
    w = F._solve(A, [sum(x[i] * y for x, y in sides) / sd[i] for i in range(k)]) or [0.0] * k
    return [w[j] / sd[j] for j in range(k)]


def line_of(r, mk):
    return {"spread": r.get("M"), "total": r.get("T"), "moneyline": 0.0}[mk]


def zscore(p, mk, line=None):
    """(predicted - line) / sigma for one market, or None."""
    sig = p["sigma"]["total" if mk == "total" else "margin"]
    ln = line_of(p["row"], mk) if line is None else line
    if not sig or ln is None:
        return None
    return ((p["total"] if mk == "total" else p["margin"]) - ln) / sig


def chance(p, mk, line=None, cal=False):
    """THE SCORE CURVE: P(home covers / over / home wins) at `line` (default the
    row's own) = Phi((predicted - line) / (sigma x k)); k = 1 unless `cal`."""
    z = zscore(p, mk, line)
    return None if z is None else PHI.cdf(z / (p["k"][mk] if cal else 1.0))


def logloss(q, y):
    q = min(1 - 1e-9, max(1e-9, q))
    return -math.log(q if y else 1.0 - q)


def pick_k(past, mk):
    """The sigma multiplier with the lowest log loss over earlier labelled games."""
    pts = [(z, y) for p in past if (y := F.label(p["row"], mk)) is not None
           and (z := zscore(p, mk)) is not None]
    if len(pts) < MIN_CAL:
        return 1.0
    return min(K_GRID, key=lambda k: sum(logloss(PHI.cdf(z / k), y) for z, y in pts))


def walk_forward(rows, tables):
    """Every row's prediction as it would have been made: tables as of its own
    Monday; matchup weights, sigmas and k's from earlier weeks' finals only."""
    weeks = collections.defaultdict(list)
    for r in rows:
        weeks[F.monday(r["day"])].append(r)
    done = []
    for wk in sorted(weeks):
        past = [p for p in done if p["sides"]]           # earlier weeks, final
        beta = fit_matchup([sd for p in past for sd in p["sides"]])
        sig = {name: (math.sqrt(sum(p[key] ** 2 for p in past) / len(past))
                      if len(past) >= MIN_SIGMA else None)
               for name, key in (("margin", "err_m"), ("total", "err_t"))}
        k = {mk: pick_k(past, mk) for mk in F.MARKETS}
        for r in weeks[wk]:
            b = base_score(tables, r)
            if b is None:
                continue
            f = matchup(tables, r)
            home = b[0] + sum(c * x for c, x in zip(beta, f[0]))
            away = b[1] + sum(c * x for c, x in zip(beta, f[1]))
            p = {"row": r, "week": wk, "home": home, "away": away, "margin": home - away,
                 "total": home + away, "beta": beta, "sigma": sig, "k": k, "sides": []}
            if r["final"] and r["hs"] is not None and r["as"] is not None:
                hs, as_ = float(r["hs"]), float(r["as"])
                p["sides"] = [(f[0], hs - b[0]), (f[1], as_ - b[1])]
                p["err_m"], p["err_t"] = hs - as_ - p["margin"], hs + as_ - p["total"]
            done.append(p)
    return done


def fb_model_fits(rows):
    """{(Monday, market): fb_model's own fit on games before that Monday} — the
    training `fb_model.walk_forward` grades with."""
    out = {}
    for wk in sorted({F.monday(r["day"]) for r in rows}):
        train = [r for r in rows if r["day"] < wk]
        for mk in F.MARKETS:
            data = [(F.features(r, mk), y) for r in train if (y := F.label(r, mk)) is not None]
            out[(wk, mk)] = F.fit([x for x, _ in data], [y for _, y in data], zmax=F.ZMAX)
        out[(wk, "sigma")] = F.score_sigma(train)          # = pricing.sigma.spread, earlier games
    return out


def fb_chance(model, r, mk, line=None):
    """fb_model's chance of the same side at `line` (default the row's own)."""
    ln = line_of(r, mk) if line is None else line
    if not model or ln is None:
        return None
    return F.predict(model, F.features(r, mk, **({"M": ln} if mk == "spread" else
                                                  {"T": ln} if mk == "total" else {})))


def ml_curve(p_win, line, sigma):
    """`[2026-10-16]` fb_model's own WIN chance carried to a spread line on the normal curve
    game_lines_fb prices alternate spreads with: Phi(PhiInv(p_win) - line / sigma). ⛔ Measured
    here only; fb_model's live spread still comes from its own spread fit."""
    if p_win is None or line is None or not sigma:
        return None
    return PHI.cdf(PHI.inv_cdf(min(1 - 1e-9, max(1e-9, p_win))) - line / sigma)


def versions(p, fits, mk, line=None):
    m = fits.get((p["week"], mk))
    out = {"score_curve": chance(p, mk, line), "calibrated": chance(p, mk, line, cal=True),
           "fb_model": fb_chance(m, p["row"], mk, line)}
    if mk == "spread":
        out["ml_curve"] = ml_curve(fb_chance(fits.get((p["week"], "moneyline")), p["row"], "moneyline"),
                                   p["row"].get("M") if line is None else line, fits.get((p["week"], "sigma")))
    return out


def coherence(done, fits):
    """`[2026-10-16]` Per version: games where the side laying points is likelier to COVER
    than to WIN (impossible: covering is winning by more), at each final game's own line."""
    out = {}
    for p in done:
        M = p["row"].get("M")
        if not p["sides"] or not M:
            continue
        sp, ml = versions(p, fits, "spread"), versions(p, fits, "moneyline")
        for v, q in sp.items():
            w = ml["fb_model" if v == "ml_curve" else v]
            if q is None or w is None:
                continue
            cover, win = (q, w) if M > 0 else (1.0 - q, 1.0 - w)
            c = out.setdefault(v, [0, 0])
            c[0], c[1] = c[0] + 1, c[1] + (cover > win + 1e-9)
    return {v: {"games": n, "cover_above_win": bad} for v, (n, bad) in out.items()}


def opposite_picks(picks):
    """`[2026-10-16]` Games where fb_model picks the side LAYING points (or a pick'em) on the
    spread and the OTHER team to win, at chances adding up to more than 100%: both cannot hit.
    ⚠️ A side GETTING points and the other team to win can both hit (the favourite wins by
    less than the line), so that pair is never counted. `line` is the home margin line."""
    by = collections.defaultdict(dict)
    for k in picks:
        by[k["game_id"]][k["market"]] = k
    both = [g for g in by.values() if "spread" in g and "moneyline" in g]
    lays = lambda k: k["line"] == 0 or (k["line"] > 0) == (k["side"] == "home")  # noqa: E731
    bad = [g for g in both if g["spread"]["side"] != g["moneyline"]["side"] and lays(g["spread"])
           and g["spread"]["p"] + g["moneyline"]["p"] > 1.0 + 1e-9]
    return {"games_with_both": len(both), "cannot_both_hit": len(bad),
            "games": [{"game_id": g["spread"]["game_id"], "spread": [g["spread"]["side"], g["spread"].get("line"),
                                                                     round(100 * g["spread"]["p"], 1)],
                       "moneyline": [g["moneyline"]["side"], round(100 * g["moneyline"]["p"], 1)]} for g in bad]}


def rms(xs):
    return math.sqrt(sum(x * x for x in xs) / len(xs)) if xs else None


def point_errors(done):
    """Margin and total misses: the score model, fb_model's own ratings, the closing line."""
    got = []
    for p in done:
        r, c = p["row"], p["row"].get("close") or {}
        if not p["sides"] or r["sig"].get("own_m") is None or not c.get("spread") or not c.get("total"):
            continue
        hs, as_ = float(r["hs"]), float(r["as"])
        got.append({"margin": (p["err_m"], hs - as_ - r["sig"]["own_m"], hs - as_ - c["spread"][0][0]),
                    "total": (p["err_t"], hs + as_ - r["sig"]["own_t"], hs + as_ - c["total"][0][0])})
    out = {"games": len(got)}
    for key in ("margin", "total"):
        out[key] = {name: {"mae": round(sum(abs(g[key][i]) for g in got) / len(got), 2) if got else None,
                           "rmse": round(rms([g[key][i] for g in got]), 2) if got else None}
                    for i, name in enumerate(("score_model", "fb_model_own_ratings", "closing_line"))}
    return out


def scored(done, fits, mk):
    """[(row, label, {version: chance at the row's own line})] on games every version prices."""
    out = []
    for p in done:
        y = F.label(p["row"], mk) if p["sides"] else None
        v = versions(p, fits, mk) if y is not None else None
        if v and all(v[x] is not None for x in VERSIONS):
            out.append((p["row"], y, v))
    return out


def calibration(items, version):
    """Chosen side's chance by band: games, average stated %, real hit %."""
    bands = collections.defaultdict(list)
    for _r, y, v in items:
        q = v[version]
        side, hit = (q, y == 1) if q >= 0.5 else (1.0 - q, y == 0)
        bands[max(b for b in BANDS if side >= b)].append((side, hit))
    return [{"band": "%d+" % (100 * b) if b == BANDS[-1] else "%d-%d" % (100 * b, 100 * b + 5),
             "games": len(bands[b]),
             "stated": round(100 * sum(s for s, _ in bands[b]) / len(bands[b]), 1) if bands[b] else None,
             "hit": round(100 * sum(1 for _, h in bands[b] if h) / len(bands[b]), 1) if bands[b] else None}
            for b in BANDS]


def roi(done, fits, mk, version, quotes):
    """Picks at 50%+: per final game, every side at 50% or more at a quote's own
    line, at the best price among them; graded; pushes out; 1 unit each."""
    n = wins = assumed = 0
    profit = 0.0
    for p in done:
        if not p["sides"]:
            continue
        best = None
        for _b, ln, pa, pb, asm in quotes(p["row"], mk):
            q = versions(p, fits, mk, ln if mk != "moneyline" else None)[version]
            if q is None:
                continue
            for side, px, qq in ((SIDES[mk][0], pa, q), (SIDES[mk][1], pb, 1.0 - q)):
                if px is not None and qq >= 0.5 and (best is None or qq * F.decimal(px) > best[0]):
                    best = (qq * F.decimal(px), {"side": side, "line": ln, "price": px, "assumed": asm})
        won = F.grade(p["row"], mk, best[1]) if best else None
        if won is None:
            continue
        n, wins, assumed = n + 1, wins + bool(won), assumed + bool(best[1]["assumed"])
        profit += (F.decimal(best[1]["price"]) - 1.0) if won else -1.0
    return {"picks": n, "wins": wins, "hit_rate": round(100.0 * wins / n, 1) if n else None,
            "roi": round(100.0 * profit / n, 1) if n else None, "price_assumed": assumed}


def backtest(done, fits):
    finals = [p for p in done if p["sides"]]
    out = {"games_predicted": len(finals),
           "first": min((p["row"]["day"] for p in finals), default=None),
           "last": max((p["row"]["day"] for p in finals), default=None),
           "point_error": point_errors(done), "log_loss": {}, "calibration": {}, "roi": {},
           "coin_flip_log_loss": round(math.log(2), 4)}
    for mk in F.MARKETS:
        items = scored(done, fits, mk)
        vs = VERSIONS + (("ml_curve",) if mk == "spread" else ())
        ll = {v: round(sum(logloss(x[2][v], x[1]) for x in items) / len(items), 4) if items else None
              for v in VERSIONS}
        if mk == "spread":                # fb_model's win chance on the curve, on the games it prices
            sub = [x for x in items if x[2]["ml_curve"] is not None]
            ll["ml_curve"], ll["ml_curve_games"] = (round(sum(logloss(x[2]["ml_curve"], x[1]) for x in sub)
                                                          / len(sub), 4) if sub else None), len(sub)
            ll["fb_model_on_ml_curve_games"] = (round(sum(logloss(x[2]["fb_model"], x[1]) for x in sub)
                                                      / len(sub), 4) if sub else None)
        if mk == "moneyline":
            ll["books_devigged"] = round(sum(logloss(r["pml"], y) for r, y, _v in items) / len(items), 4) \
                if items else None
        out["log_loss"][mk] = dict(ll, games=len(items))
        out["calibration"][mk] = {v: calibration([x for x in items if x[2][v] is not None], v) for v in vs}
        out["roi"][mk] = {rec: {v: roi(done, fits, mk, v, q) for v in vs} for rec, q in F.RECORDS}
    out["coherence"] = coherence(done, fits)
    return out


def upcoming(done, rows, now):
    """Every unplayed game in the next `PRICING_DAYS`: the predicted score and
    chances at its lines, beside fb_model's chances from today's fit."""
    horizon = (datetime.date.fromisoformat(now[:10]) + datetime.timedelta(days=F.PRICING_DAYS)).isoformat()
    live = {"sigma": F.score_sigma(rows)}
    for mk in F.MARKETS:
        data = [(F.features(r, mk), y) for r in rows if (y := F.label(r, mk)) is not None]
        live[mk] = F.fit([x for x, _ in data], [y for _, y in data], zmax=F.ZMAX)
    pct = lambda q: None if q is None else round(100.0 * q, 1)  # noqa: E731
    out = []
    for p in done:
        r = p["row"]
        if r["final"] or not (now[:10] <= r["day"] <= horizon):
            continue
        out.append({"game_id": r["id"], "day": r["day"], "kick": r["kick"], "home": r["home"],
                    "away": r["away"], "neutral": bool(r["sig"]["neutral"]),
                    "score": {"home": round(p["home"], 1), "away": round(p["away"], 1)},
                    "margin": round(p["margin"], 1), "total": round(p["total"], 1),
                    "line": {"spread": r.get("M"), "total": r.get("T")},
                    "score_curve": {mk: pct(chance(p, mk)) for mk in F.MARKETS},
                    "calibrated": {mk: pct(chance(p, mk, cal=True)) for mk in F.MARKETS},
                    "fb_model": {mk: pct(fb_chance(live[mk], r, mk)) for mk in F.MARKETS},
                    "fb_model_ml_curve_spread": pct(ml_curve(fb_chance(live["moneyline"], r, "moneyline"),
                                                             r.get("M"), live["sigma"]))})
    return sorted(out, key=lambda g: (g["kick"], g["game_id"]))


def build(lg=None, root=None, out=None, now=None):
    lg = (lg or LEAGUE).lower()
    now = now or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    horizon = (datetime.date.fromisoformat(now[:10]) + datetime.timedelta(days=F.PRICING_DAYS)).isoformat()
    rows = [r for r in F.build_rows(lg, root)
            if r.get("season") in F.SEASONS and (r["final"] or r["day"] <= horizon)]
    tables = FM.Tables(lg, root)
    done = walk_forward(rows, tables)
    fits = fb_model_fits(rows)
    last = done[-1] if done else {"beta": [0.0] * len(MATCH_UNITS), "sigma": {}, "k": {}}
    season = max(FM.seasons(lg, root), default=None)
    doc = {"league": lg, "kind": "MODEL", "report_only": True, "built_at": now, "design": DESIGN,
           "note": NOTE,
           "settings": {"home_edge_points": round(tables.home_edge("points", now), 2),
                        "matchup_points_per_unit": {u: round(b, 4) for u, b in zip(MATCH_UNITS, last["beta"])},
                        "sigma": {k: round(v, 2) if v else None for k, v in last["sigma"].items()},
                        "k": last["k"]},
           "upcoming": upcoming(done, rows, now),
           "backtest": backtest(done, fits),
           "tables_reconcile": FM.reconcile(tables, lg, season, root) if season else None}
    wf = F.walk_forward(rows)
    doc["fb_model_opposite_picks"] = dict(
        {name: opposite_picks([dict(k, market=mk) for mk in F.MARKETS for k in wf[name][mk]])
         for name, _q in F.RECORDS},
        this_week=opposite_picks([dict(k, p=k["model_probability"]["value"] / 100.0, line=k["line"]["value"])
                                  for k in F.current_picks(lg, rows, root, now)]))
    path = out or os.path.join(root or ROOT, "data", lg, "latest", "fb-score-model.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    bt = doc["backtest"]
    print("%s score model: %d games predicted %s to %s; home edge %s; log loss %s" % (
        lg, bt["games_predicted"], bt["first"], bt["last"], doc["settings"]["home_edge_points"],
        {mk: {v: bt["log_loss"][mk][v] for v in VERSIONS} for mk in F.MARKETS}), flush=True)
    return doc


if __name__ == "__main__":
    build()
    sys.exit(0)
