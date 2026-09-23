#!/usr/bin/env python3
"""fb_model.py — the football pick model, built exactly as
`research/fb_model_design.md` describes (committed before any result).

    LEAGUE=nfl python fb_model.py     # retrain, walk-forward, write the file

One ridge-logistic model per league × market (spread, total, moneyline) on
signals 1–8. Walk-forward weekly over 2025 and 2026, graded ONLY at Hard
Rock, FanDuel and DraftKings prices that existed before kickoff.

⛔ IT DOES NOT REPLACE THE CARD. `card_fb.py` never imports this file; the
page shows these picks in their own MODEL section beside the card.
⛔ NEVER INVENTS A PRICE. A game with no price at the three books is
trained on and not graded.
⛔ UNCERTAINTY IS CLUSTERED BY GAME (`shadow_fb.cluster`); no p-value or
interval is ever taken on raw rows.
⚠️ STDLIB ONLY — the logistic fit is Newton's method by hand.
"""
import collections
import datetime
import glob
import gzip
import json
import math
import os
import statistics
import sys

import collect                      # league_books: the ONE football book filter
import dossier_fb as D              # team_codes, _near: the board -> schedule join
import possession as P              # share_before: signal 6 from EARLIER games only
import shadow_fb                    # cluster: effective n by game
import t60r                         # point-in-time §2, §4, §5 — read, never edited

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUE = os.environ.get("LEAGUE", "nfl")
SEASONS = (2025, 2026)
MARKETS = ("spread", "total", "moneyline")
RIDGE = 1.0                  # ⛔ design §2
MIN_TRAIN = 150              # ⛔ design §4
Z95 = 1.959964
BASES = ("MODEL", "MARKET", "DESCRIPTIVE")
FEATURES = {
    "spread": ["line", "h2h", "form", "possession", "personnel", "neutral", "dome"],
    "total": ["line", "h2h", "form", "defence", "neutral", "dome"],
    "moneyline": ["market", "h2h", "form", "possession", "personnel", "neutral", "dome"],
}


def log(m):
    print(m, flush=True)


def L(value, basis):
    assert basis in BASES, basis
    return {"value": value, "basis": basis}


def jz(path):
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


# ══════════════════════════════════════════════════════════════════════
# PRICES
# ══════════════════════════════════════════════════════════════════════
def implied(american):
    a = float(american)
    return 100.0 / (a + 100.0) if a > 0 else -a / (-a + 100.0)


def decimal(american):
    a = float(american)
    return 1.0 + (a / 100.0 if a > 0 else 100.0 / -a)


def devig(a, b):
    """Two American prices -> the first side's probability with the vig out."""
    ia, ib = implied(a), implied(b)
    return ia / (ia + ib) if ia + ib > 0 else None


def books_ok(lg):
    return set(collect.league_books(lg))


def board_prices(lg, resolve, root=None):
    """{(home, away, 'YYYY-MM-DD'): {"pulled_at", "commence", "books": {...}}}

    ⛔ THE LAST SNAPSHOT PULLED BEFORE KICKOFF, and only Sam's three books.
    A snapshot pulled after kickoff carries live prices and is never used.
    """
    ok = books_ok(lg)
    out = {}
    for f in sorted(glob.glob(os.path.join(root or ROOT, "data", lg, "20*", "gamelines",
                                           "*.json.gz"))):
        doc = jz(f) or {}
        pulled = doc.get("pulled_at") or ""
        for g in doc.get("games") or []:
            commence = g.get("commence") or ""
            if not pulled or not commence or pulled >= commence:
                continue
            home, away = resolve(g.get("home")), resolve(g.get("away"))
            if not (home and away):
                continue
            bk = {k: v for k, v in (g.get("books") or {}).items() if k in ok}
            if not bk:
                continue
            key = (home, away, commence[:10])
            if key not in out or pulled > out[key]["pulled_at"]:
                out[key] = {"pulled_at": pulled, "commence": commence, "books": bk,
                            "names": (g.get("home"), g.get("away"))}
    return out


def book_lines(snap):
    """-> {"spread": [(book, M, home_px, away_px)], "total": [(book, T, over_px,
    under_px)], "moneyline": [(book, home_px, away_px)]} from one snapshot."""
    hname, aname = snap["names"]
    out = {"spread": [], "total": [], "moneyline": []}
    for b, v in sorted(snap["books"].items()):
        sp = v.get("spreads") or {}
        if hname in sp and aname in sp and sp[hname].get("pt") is not None:
            out["spread"].append((b, -float(sp[hname]["pt"]), sp[hname].get("px"),
                                  sp[aname].get("px")))
        to = v.get("totals") or {}
        if "Over" in to and "Under" in to and to["Over"].get("pt") is not None:
            out["total"].append((b, float(to["Over"]["pt"]), to["Over"].get("px"),
                                 to["Under"].get("px")))
        ml = v.get("h2h") or {}
        if hname in ml and aname in ml:
            out["moneyline"].append((b, ml[hname], ml[aname]))
    return out


# ══════════════════════════════════════════════════════════════════════
# GAMES, LINES AND SIGNALS — one row per game, in kickoff order
# ══════════════════════════════════════════════════════════════════════
def schedule_games(lg, root=None):
    out = []
    for s in SEASONS:
        doc = jz(os.path.join(root or ROOT, "data", lg, "latest", "schedule-%d.json.gz" % s)) or {}
        for g in doc.get("games") or []:
            if not g.get("start") or not g.get("home") or not g.get("away"):
                continue
            if lg == "ncaaf" and not (g.get("home_class") == "fbs" and g.get("away_class") == "fbs"):
                continue
            out.append(dict(g, season=s))
    return sorted(out, key=lambda g: g["start"])


def team_out_table(lg, root=None, extra=None):
    """{(season, team): {week: n_out}} from players-<season> `team_out`."""
    out = {}
    for s in SEASONS:
        doc = (extra or {}).get(s) or jz(os.path.join(root or ROOT, "data", lg, "latest",
                                                      "players-%d.json.gz" % s)) or {}
        for team, weeks in (doc.get("team_out") or {}).items():
            for wk, c in weeks.items():
                out.setdefault((s, team), {})[int(wk)] = c.get("out", 0)
    return out


def possession_games(lg, root=None, extra=None):
    out = {}
    for s in SEASONS:
        doc = (extra or {}).get(s) or jz(os.path.join(root or ROOT, "data", lg, "latest",
                                                      "top-%d.json.gz" % s)) or {}
        out.update(doc.get("games") or {})
    return out


def training_line(g, snap, cfb):
    """(M, T, p_home_ml) — the line a game is labelled against, or Nones."""
    if snap:
        bl = book_lines(snap)
        Ms = [m for _b, m, _h, _a in bl["spread"]]
        Ts = [t for _b, t, _o, _u in bl["total"]]
        ps = [devig(h, a) for _b, h, a in bl["moneyline"] if h is not None and a is not None]
        if Ms and Ts:
            return (statistics.median(Ms), statistics.median(Ts),
                    statistics.median(ps) if ps else None)
    m, t, why = t60r.market(g, cfb)
    if why:
        return None, None, None
    if cfb is not None:
        row = cfb.get(str(g.get("id"))) or {}
        mh, ma = row.get("ml_home"), row.get("ml_away")
    else:
        mh, ma = g.get("closing_ml_home"), g.get("closing_ml_away")
    p = devig(mh, ma) if mh is not None and ma is not None else None
    return m, t, p


def build_rows(lg, root=None, extra_top=None, extra_players=None, board=None):
    """Every game with its line, label and point-in-time signals.

    ⛔ FORWARD ONLY: rows are built in kickoff order, and every signal reads
    only games dated before the row's own date (the `past` cut, t60r's
    Allowed.upto, possession.share_before, team_out of an earlier week).
    """
    resolve = D.team_codes(lg)
    snaps = board_prices(lg, resolve, root) if board is None else board
    cfb = (jz(os.path.join(root or ROOT, "data", "t60r", "cfbd-lines.json.gz")) or {}).get("games") \
        if lg == "ncaaf" else None
    old_root = t60r.ROOT
    if root:
        t60r.ROOT = root
    try:
        hist = t60r.history(lg)
        allowed = t60r.Allowed(lg)
    finally:
        t60r.ROOT = old_root
    poss = possession_games(lg, root, extra_top)
    outs = team_out_table(lg, root, extra_players)
    rows = []
    for g in schedule_games(lg, root):
        k = t60r.kick(g)
        if k is None:
            continue
        day = k.strftime("%Y-%m-%d")
        snap = None
        for (h, a, d), v in snaps.items():
            if h == g["home"] and a == g["away"] and D._near(d, k):
                snap = v
                break
        M, T, pml = training_line(g, snap, cfb if lg == "ncaaf" else None)
        past = [x for x in hist if t60r.kick(x) < k]
        h2h_m, h2h_t = t60r.s2_h2h(g, past)
        f_m, f_t = t60r.s4_this_season(g, past)
        frac = allowed.fraction(g)
        sb_h = P.share_before(poss, g["home"], day)["share"]
        sb_a = P.share_before(poss, g["away"], day)["share"]
        wk = g.get("week")
        o_h = o_a = None
        if lg == "nfl" and wk:
            prev = lambda team: max(((w, n) for w, n in (outs.get((g["season"], team)) or {}).items()  # noqa: E731
                                     if w < int(wk)), default=(None, None))[1]
            o_h, o_a = prev(g["home"]), prev(g["away"])
        rows.append({
            "id": str(g.get("id")), "season": g["season"], "day": day, "kick": g["start"],
            "week": wk, "home": g["home"], "away": g["away"], "final": bool(g.get("final")),
            "hs": g.get("home_score"), "as": g.get("away_score"),
            "M": M, "T": T, "pml": pml, "snap": snap,
            "sig": {"h2h_m": h2h_m, "h2h_t": h2h_t, "form_m": f_m, "form_t": f_t,
                    "def": frac, "poss": (sb_h - sb_a) if sb_h is not None and sb_a is not None else None,
                    "out": (o_a - o_h) if o_h is not None and o_a is not None else None,
                    "neutral": 1.0 if g.get("neutral") else 0.0,
                    "dome": 1.0 if (g.get("roof") or "") in ("dome", "closed") else 0.0},
        })
    return rows


def features(r, market, M=None, T=None):
    """The design-§1 inputs for one row at a given line. Missing -> 0."""
    s = r["sig"]
    M = r["M"] if M is None else M
    T = r["T"] if T is None else T
    z = lambda x: 0.0 if x is None else float(x)  # noqa: E731
    if market == "spread":
        return [z(M) / 7.0,
                z(None if s["h2h_m"] is None else s["h2h_m"] - M) / 10.0,
                z(None if s["form_m"] is None else s["form_m"] - M) / 10.0,
                z(s["poss"]) * 10.0, z(s["out"]) / 3.0, s["neutral"], s["dome"]]
    if market == "total":
        return [(z(T) - 45.0) / 10.0,
                z(None if s["h2h_t"] is None else s["h2h_t"] - T) / 10.0,
                z(None if s["form_t"] is None else s["form_t"] - T) / 10.0,
                z(None if s["def"] is None else s["def"] - 0.5) * 4.0, s["neutral"], s["dome"]]
    p = r["pml"]
    lo = math.log(p / (1 - p)) if p and 0 < p < 1 else 0.0
    return [lo, z(s["h2h_m"]) / 10.0, z(s["form_m"]) / 10.0,
            z(s["poss"]) * 10.0, z(s["out"]) / 3.0, s["neutral"], s["dome"]]


def label(r, market, M=None, T=None):
    """1/0, or None for a push, a tie, or a game not final / not priced."""
    if not r["final"] or r["hs"] is None or r["as"] is None:
        return None
    margin = float(r["hs"]) - float(r["as"])
    if market == "spread":
        M = r["M"] if M is None else M
        if M is None or margin == M:
            return None
        return 1 if margin > M else 0
    if market == "total":
        T = r["T"] if T is None else T
        pts = float(r["hs"]) + float(r["as"])
        if T is None or pts == T:
            return None
        return 1 if pts > T else 0
    if r["pml"] is None or margin == 0:
        return None
    return 1 if margin > 0 else 0


# ══════════════════════════════════════════════════════════════════════
# THE MODEL — ridge logistic by Newton's method
# ══════════════════════════════════════════════════════════════════════
def _solve(A, b):
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda i: abs(M[i][c]))
        if abs(M[piv][c]) < 1e-12:
            return None
        M[c], M[piv] = M[piv], M[c]
        p = M[c][c]
        M[c] = [v / p for v in M[c]]
        for i in range(n):
            if i != c and M[i][c]:
                f = M[i][c]
                M[i] = [a - f * bb for a, bb in zip(M[i], M[c])]
    return [M[i][n] for i in range(n)]


def fit(X, y, ridge=RIDGE, iters=50):
    """-> {"mu", "sd", "w"} or None. Inputs standardised on the training set;
    the intercept (w[0]) is not penalised."""
    if len(X) < MIN_TRAIN or len(set(y)) < 2:
        return None
    k = len(X[0])
    mu = [sum(x[j] for x in X) / len(X) for j in range(k)]
    sd = [math.sqrt(sum((x[j] - mu[j]) ** 2 for x in X) / len(X)) or 1.0 for j in range(k)]
    Z = [[1.0] + [(x[j] - mu[j]) / sd[j] for j in range(k)] for x in X]
    w = [0.0] * (k + 1)
    for _ in range(iters):
        g = [0.0] * (k + 1)
        H = [[0.0] * (k + 1) for _ in range(k + 1)]
        for z, t in zip(Z, y):
            e = sum(a * b for a, b in zip(w, z))
            p = 1.0 / (1.0 + math.exp(-max(-35.0, min(35.0, e))))
            for i in range(k + 1):
                g[i] += (p - t) * z[i]
                for j in range(i, k + 1):
                    H[i][j] += p * (1 - p) * z[i] * z[j]
        for i in range(1, k + 1):
            g[i] += ridge * w[i]
            H[i][i] += ridge
        for i in range(k + 1):
            for j in range(i):
                H[i][j] = H[j][i]
        step = _solve(H, g)
        if step is None:
            return None
        w = [a - b for a, b in zip(w, step)]
        if max(abs(s) for s in step) < 1e-8:
            break
    return {"mu": mu, "sd": sd, "w": w}


def predict(m, x):
    z = [1.0] + [(x[j] - m["mu"][j]) / m["sd"][j] for j in range(len(x))]
    e = sum(a * b for a, b in zip(m["w"], z))
    return 1.0 / (1.0 + math.exp(-max(-35.0, min(35.0, e))))


# ══════════════════════════════════════════════════════════════════════
# PICKS — best Hard Rock / FanDuel / DraftKings price, EV above zero
# ══════════════════════════════════════════════════════════════════════
def best_pick(r, market, model):
    """-> {"side", "book", "line", "price", "p", "ev", "break_even"} or None."""
    if not r["snap"] or not model:
        return None
    bl = book_lines(r["snap"])[market]
    cands = []
    if market == "spread":
        for b, M, hp, ap in bl:
            p = predict(model, features(r, "spread", M=M))
            cands += [("home", b, M, hp, p), ("away", b, M, ap, 1 - p)]
    elif market == "total":
        for b, T, op, up in bl:
            p = predict(model, features(r, "total", T=T))
            cands += [("over", b, T, op, p), ("under", b, T, up, 1 - p)]
    else:
        p = predict(model, features(r, "moneyline"))
        for b, hp, ap in bl:
            cands += [("home", b, None, hp, p), ("away", b, None, ap, 1 - p)]
    best = None
    for side, b, ln, px, p in cands:
        if px is None:
            continue
        ev = p * decimal(px) - 1.0
        if best is None or ev > best["ev"]:
            best = {"side": side, "book": b, "line": ln, "price": px, "p": p, "ev": ev,
                    "break_even": 1.0 / decimal(px)}
    return best if best and best["ev"] > 0 else None


def grade(r, market, pick):
    """True / False / None (push or not final)."""
    if not r["final"] or r["hs"] is None:
        return None
    margin = float(r["hs"]) - float(r["as"])
    if market == "spread":
        d = margin - pick["line"]
        if d == 0:
            return None
        return (d > 0) == (pick["side"] == "home")
    if market == "total":
        d = float(r["hs"]) + float(r["as"]) - pick["line"]
        if d == 0:
            return None
        return (d > 0) == (pick["side"] == "over")
    if margin == 0:
        return None
    return (margin > 0) == (pick["side"] == "home")


# ══════════════════════════════════════════════════════════════════════
# WALK-FORWARD
# ══════════════════════════════════════════════════════════════════════
def monday(day):
    d = datetime.date.fromisoformat(day)
    return (d - datetime.timedelta(days=d.weekday())).isoformat()


def walk_forward(rows):
    """-> {market: [pick rows]} graded week by week, trained only on games
    that kicked off before each week's Monday."""
    weeks = collections.defaultdict(list)
    for r in rows:
        weeks[monday(r["day"])].append(r)
    out = {mk: [] for mk in MARKETS}
    for wk in sorted(weeks):
        train = [r for r in rows if r["day"] < wk]
        for mk in MARKETS:
            data = [(features(r, mk), label(r, mk)) for r in train if label(r, mk) is not None]
            model = fit([x for x, _ in data], [y for _, y in data])
            if not model:
                continue
            for r in weeks[wk]:
                if not r["final"]:
                    continue
                pk = best_pick(r, mk, model)
                if not pk:
                    continue
                won = grade(r, mk, pk)
                out[mk].append(dict(pk, game_id=r["id"], week=wk, day=r["day"],
                                    home=r["home"], away=r["away"], won=won,
                                    state="graded" if won is not None else "push"))
    return out


def record(picks):
    """Picks, hit rate, break-even, and a 95% interval on the CLUSTERED n."""
    c = shadow_fb.cluster(picks, key="game_id")
    graded = [p for p in picks if p["won"] is not None]
    be = (sum(p["break_even"] for p in graded) / len(graded)) if graded else None
    rate = c.get("rate")
    en = c.get("eff_n") or 0
    half = Z95 * math.sqrt(rate * (1 - rate) / en) if rate is not None and en else None
    return {"picks": L(len(graded), "DESCRIPTIVE"),
            "wins": L(c.get("wins"), "DESCRIPTIVE"),
            "hit_rate": L(round(100 * rate, 1) if rate is not None else None, "DESCRIPTIVE"),
            "break_even": L(round(100 * be, 1) if be is not None else None, "MARKET"),
            "interval_95": L([round(100 * max(0.0, rate - half), 1), round(100 * min(1.0, rate + half), 1)]
                             if half is not None else None, "DESCRIPTIVE"),
            "effective_n": L(round(en, 1), "DESCRIPTIVE"),
            "pushes": L(sum(1 for p in picks if p["won"] is None), "DESCRIPTIVE")}


def current_picks(lg, rows, root=None):
    """This week's picks for games on the live board, trained on every final."""
    board = json.load(open(os.path.join(root or ROOT, "data", lg, "latest", "board.json"),
                           encoding="utf-8")) if os.path.exists(
        os.path.join(root or ROOT, "data", lg, "latest", "board.json")) else {}
    resolve = D.team_codes(lg)
    ok = books_ok(lg)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    models = {}
    for mk in MARKETS:
        data = [(features(r, mk), label(r, mk)) for r in rows if label(r, mk) is not None]
        models[mk] = fit([x for x, _ in data], [y for _, y in data])
    byk = {(r["home"], r["away"]): r for r in rows if not r["final"]}
    for g in board.get("games") or []:
        if (g.get("commence") or "") <= now:
            continue
        h, a = resolve(g.get("home")), resolve(g.get("away"))
        r = byk.get((h, a))
        if not r:
            continue
        snap = {"pulled_at": board.get("pulled_at") or "", "commence": g["commence"],
                "names": (g.get("home"), g.get("away")),
                "books": {k: v for k, v in (g.get("books") or {}).items() if k in ok}}
        rr = dict(r, snap=snap)
        for mk in MARKETS:
            pk = best_pick(rr, mk, models[mk])
            if pk:
                out.append({"game": "%s at %s" % (g.get("away"), g.get("home")),
                            "commence": g["commence"], "market": mk,
                            "side": pk["side"], "book": collect.BOOKS.get(pk["book"], pk["book"]),
                            "line": L(pk["line"], "MARKET"), "price": L(pk["price"], "MARKET"),
                            "model_probability": L(round(100 * pk["p"], 1), "MODEL"),
                            "break_even": L(round(100 * pk["break_even"], 1), "MARKET"),
                            "edge": L(round(100 * pk["ev"], 1), "MODEL")})
    return out


def build(lg=None, root=None, out=None, extra_top=None, extra_players=None):
    lg = (lg or LEAGUE).lower()
    rows = build_rows(lg, root, extra_top, extra_players)
    wf = walk_forward(rows)
    first = {mk: (min(p["day"] for p in wf[mk]) if wf[mk] else None) for mk in MARKETS}
    doc = {"league": lg, "kind": "MODEL",
           "built_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "design": "research/fb_model_design.md",
           "books": sorted(set(collect.BOOKS[k] for k in books_ok(lg))),
           "record": {mk: dict(record(wf[mk]), first_graded=first[mk]) for mk in MARKETS},
           "picks": current_picks(lg, rows, root),
           "games_trained": {mk: sum(1 for r in rows if label(r, mk) is not None) for mk in MARKETS},
           "signal_coverage": {k: sum(1 for r in rows if r["sig"].get(k) is not None)
                               for k in ("h2h_m", "form_m", "def", "poss", "out")},
           "note": ("Graded only at Hard Rock, FanDuel and DraftKings prices that existed "
                    "before kickoff; those are archived from September 2026. Earlier games "
                    "train the model but are not graded. Intervals use the effective n "
                    "clustered by game."),
           "graded": {mk: wf[mk] for mk in MARKETS}}
    path = out or os.path.join(root or ROOT, "data", lg, "latest", "fb-model.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    for mk in MARKETS:
        r = doc["record"][mk]
        log("%s %-9s picks %s hit %s%% break-even %s%% (eff n %s, from %s)" % (
            lg, mk, r["picks"]["value"], r["hit_rate"]["value"], r["break_even"]["value"],
            r["effective_n"]["value"], r["first_graded"]))
    return doc


if __name__ == "__main__":
    build()
    sys.exit(0)
