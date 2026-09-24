#!/usr/bin/env python3
"""fb_model_lambda.py — the football game model with a SELF-CHOSEN ridge
strength, scored against today's fixed λ = 1.0, exactly as
`research/fb_model_lambda_spec.md` fixes it (pre-registered by Sam
2026-09-24, committed before this file existed).

    python fb_model_lambda.py            # both leagues, stored data only

⛔ IT NEVER SWITCHES THE LIVE MODEL. It reads `fb_model.py`'s functions,
changes none of them, never writes `data/<league>/latest/fb-model.json`
and never touches `fb_model.RIDGE`. Switching is Sam's decision.
⛔ THE VERDICT IS THE POOLED ONE (spec §2): both leagues, all three
markets, clustered by game. Per-league and per-market figures are reported
beside it and are never a verdict.
⚠️ STDLIB ONLY, like fb_model.py.
"""
import collections
import datetime
import json
import math
import os
import sys

import fb_model as F                 # the model, the pick rule, the prices — read, never edited
import mlb_refit                     # paired_test_clustered: the ONE cluster-robust paired test

ROOT = os.path.dirname(os.path.abspath(__file__))
GRID = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0)   # ⛔ spec §2
FIXED = F.RIDGE                                  # today's value, 1.0
MIN_WEEKS = 4                                    # ⛔ spec §2: fewer earlier predicted weeks -> λ = 1.0
MIN_N = 500                                      # ⛔ spec §2
ALPHA = 0.05                                     # ⛔ spec §2
TIE = 1e-12                                      # ⛔ spec §3
CLIP = 1e-12                                     # ⛔ spec §3
LEAGUES = ("nfl", "ncaaf")


def log(m):
    print(m, flush=True)


def logloss(p, y):
    p = min(1.0 - CLIP, max(CLIP, p))
    return -(math.log(p) if y else math.log(1.0 - p))


def closing_outcome(r, market, line):
    """1/0 against the CLOSING line, or None for a push, a tie or a game
    not final. ⛔ Judged at the same line the probability is taken at."""
    if not r["final"] or r["hs"] is None or r["as"] is None:
        return None
    margin = float(r["hs"]) - float(r["as"])
    if market == "spread":
        d = margin - line
    elif market == "total":
        d = float(r["hs"]) + float(r["as"]) - line
    else:
        d = margin
    return None if d == 0 else (1 if d > 0 else 0)


def closing_features(r, market, line):
    if market == "spread":
        return F.features(r, "spread", M=line)
    if market == "total":
        return F.features(r, "total", T=line)
    return F.features(r, "moneyline")


# ══════════════════════════════════════════════════════════════════════
# THE WEEKLY FITS — every week, every λ, trained on games before its Monday
# ══════════════════════════════════════════════════════════════════════
def weekly_fits(rows, market, grid=GRID):
    """-> [(week, {λ: model or None}, [(features, label)] of that week's
    labelled games)] in week order. One fit per week per λ: the inner
    walk-forward and the outer one both read from it."""
    weeks = collections.defaultdict(list)
    for r in rows:
        weeks[F.monday(r["day"])].append(r)
    out = []
    for wk in sorted(weeks):
        train = [r for r in rows if r["day"] < wk]
        data = [(F.features(r, market), F.label(r, market)) for r in train
                if F.label(r, market) is not None]
        X, y = [x for x, _ in data], [t for _, t in data]
        models = {lam: F.fit(X, y, ridge=lam) for lam in grid}
        own = [(F.features(r, market), F.label(r, market)) for r in weeks[wk]
               if F.label(r, market) is not None]
        out.append((wk, models, own))
    return out


def predicted(entry):
    """Spec §3: today's model (λ = 1.0) fits AND there is a labelled game."""
    _wk, models, own = entry
    return models.get(FIXED) is not None and bool(own)


def choose(fits, week):
    """The λ for `week`, from the inner walk-forward over EARLIER predicted
    weeks only. -> (λ, {λ: mean log loss}) ."""
    earlier = [e for e in fits if e[0] < week and predicted(e)]
    if len(earlier) < MIN_WEEKS:
        return FIXED, {}
    means = {}
    for lam in GRID:
        if any(e[1].get(lam) is None for e in earlier):
            continue                                  # ⛔ spec §3: a failed fit drops that λ
        tot = n = 0
        for _wk, models, own in earlier:
            for x, y in own:
                tot += logloss(F.predict(models[lam], x), y)
                n += 1
        means[lam] = tot / n
    if not means:
        return FIXED, {}
    best = min(means.values())
    return max(lam for lam, v in means.items() if v <= best + TIE), means   # tie -> the LARGER λ


# ══════════════════════════════════════════════════════════════════════
# SCORING — the decision set, and both records under both versions
# ══════════════════════════════════════════════════════════════════════
def score_league(lg, rows):
    """-> {"scored": [...], "picks": {version: {record: {market: [...]}}},
    "lambdas": {market: [[week, λ], ...]}}"""
    weeks = collections.defaultdict(list)
    for r in rows:
        weeks[F.monday(r["day"])].append(r)
    scored = []
    picks = {v: {rec: {mk: [] for mk in F.MARKETS} for rec, _q in F.RECORDS}
             for v in ("fixed", "self")}
    lambdas = {}
    for mk in F.MARKETS:
        fits = weekly_fits(rows, mk)
        lambdas[mk] = []
        for entry in fits:
            wk, models = entry[0], entry[1]
            if models.get(FIXED) is None:
                continue                              # today's model makes no prediction
            lam, _means = choose(fits, wk)
            if any(r["final"] for r in weeks[wk]):     # a week not yet played has no choice to report
                lambdas[mk].append([wk, lam])
            m = {"fixed": models[FIXED], "self": models.get(lam)}
            for r in weeks[wk]:
                if not r["final"]:
                    continue
                # the decision set: every final game with a closing line
                for _b, line, _pa, _pb, _assumed in F.closing_quotes(r, mk)[:1]:
                    y = closing_outcome(r, mk, line)
                    if y is None:
                        continue
                    x = closing_features(r, mk, line)
                    pf = F.predict(m["fixed"], x)
                    ps = F.predict(m["self"], x) if m["self"] else None
                    scored.append({"league": lg, "game": "%s:%s" % (lg, r["id"]), "market": mk,
                                   "week": wk, "line": line, "y": y, "lam": lam,
                                   "p_fixed": pf, "p_self": ps})
                # both published records, under each version, same rule and prices
                for v in ("fixed", "self"):
                    if m[v] is None:
                        continue
                    for rec, quotes in F.RECORDS:
                        pk = F.best_pick(r, mk, m[v], quotes)
                        if not pk:
                            continue
                        won = F.grade(r, mk, pk)
                        picks[v][rec][mk].append(dict(pk, game_id=r["id"], week=wk, day=r["day"],
                                                      won=won, state="graded" if won is not None else "push"))
    return {"scored": scored, "picks": picks, "lambdas": lambdas}


def paired(scored):
    """Spec §3: d = today's loss − self-chosen loss on the paired set,
    clustered by game. -> dict with n, mean_d, t, p, clusters, verdict."""
    pairs = [s for s in scored if s["p_self"] is not None]
    d = [logloss(s["p_fixed"], s["y"]) - logloss(s["p_self"], s["y"]) for s in pairs]
    n, mean, t, p, G = mlb_refit.paired_test_clustered(d, [s["game"] for s in pairs])
    return {"n": n, "mean_d": mean, "t": t, "p": p, "clusters": G, "verdict": verdict(n, mean, p)}


def verdict(n, mean_d, p):
    if n < MIN_N:
        return "NOT YET MEASURABLE"
    return "QUALIFIES" if (mean_d is not None and mean_d > 0 and p is not None
                           and p < ALPHA) else "DOES NOT QUALIFY"


def report(results):
    """The pooled verdict plus everything reported beside it."""
    scored = [s for lg in results for s in results[lg]["scored"]]
    out = {"spec": "research/fb_model_lambda_spec.md",
           "built_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "grid": list(GRID), "fixed": FIXED,
           "decision": paired(scored),
           "log_loss": {}, "records": {}, "lambdas": {}}
    for lg, res in results.items():
        out["lambdas"][lg] = res["lambdas"]
        out["log_loss"][lg] = {}
        out["records"][lg] = {}
        for mk in F.MARKETS:
            ss = [s for s in res["scored"] if s["market"] == mk and s["p_self"] is not None]
            out["log_loss"][lg][mk] = {
                "n": len(ss),
                "fixed": (sum(logloss(s["p_fixed"], s["y"]) for s in ss) / len(ss)) if ss else None,
                "self": (sum(logloss(s["p_self"], s["y"]) for s in ss) / len(ss)) if ss else None}
            out["records"][lg][mk] = {
                v: {rec: F.record(res["picks"][v][rec][mk]) for rec, _q in F.RECORDS}
                for v in ("fixed", "self")}
    return out


def main(out=None, rows_by_league=None):
    results = {}
    for lg in LEAGUES:
        rows = (rows_by_league or {}).get(lg) or F.build_rows(lg)
        log("scoring %s: %d rows" % (lg, len(rows)))
        results[lg] = score_league(lg, rows)
    rep = report(results)
    path = out or os.path.join(ROOT, "research", "fb_model_lambda_run_%s.json"
                               % datetime.date.today().isoformat())
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    d = rep["decision"]
    log("VERDICT %s: n=%s mean d=%s t=%s p=%s games=%s" % (
        d["verdict"], d["n"], d["mean_d"], d["t"], d["p"], d["clusters"]))
    return rep


if __name__ == "__main__":
    main()
    sys.exit(0)
