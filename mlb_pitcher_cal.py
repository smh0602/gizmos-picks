#!/usr/bin/env python3
"""MLB pitcher rows: does a correction beat the printed confidence?

Scores `research/mlb_pitcher_cal_spec.md` (audit proposals C and D), which
was committed and hashed BEFORE this file existed. ⛔ Every definition
below is that spec's section 3; if the two ever disagree, the spec wins
and this file is the bug.

    python mlb_pitcher_cal.py            score, print, write the run JSON

Stdlib only, no API call, no spend. ⛔ It never edits the card, `blend`,
`carried`, a coefficient or a published pick.
"""
import datetime
import gzip
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import mlb_refit  # noqa: E402  the one clustered paired test (spec §3)


def _load_fb_fit():
    """`fb_model.fit` and `fb_model.predict`, READ FROM fb_model.py'S OWN
    SOURCE without importing the module.

    🔴 WHY NOT `import fb_model`. The spec names `fb_model.fit` as the fit,
    and rule 117 forbids a second copy of it. But importing `fb_model`
    imports the whole football stack, and `card_fb.py` EXITS the process
    when LEAGUE is `mlb` (measured 2026-09-25: this file died on import
    under LEAGUE=mlb). The MLB card must never depend on a football
    import graph. ✅ So the four definitions the fit needs (`fit`,
    `predict`, `_solve`, and the constants `RIDGE` and `MIN_TRAIN`) are
    compiled from that file's source, unchanged: one copy, no football
    import, and an edit to the football fit reaches this file too.
    """
    import ast
    src = open(os.path.join(ROOT, "fb_model.py"), encoding="utf-8").read()
    want_fn, want_const = {"fit", "predict", "_solve"}, {"RIDGE", "MIN_TRAIN"}
    keep = []
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name in want_fn:
            keep.append(node)
        elif (isinstance(node, ast.Assign) and len(node.targets) == 1
              and getattr(node.targets[0], "id", None) in want_const):
            keep.append(node)
    got = {getattr(n, "name", None) or n.targets[0].id for n in keep}
    if got != want_fn | want_const:
        raise SystemExit("mlb_pitcher_cal: fb_model.py no longer defines %s"
                         % sorted((want_fn | want_const) - got))
    # constants first, so the functions' default arguments resolve
    keep.sort(key=lambda n: isinstance(n, ast.FunctionDef))
    ns = {"math": math}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "fb_model.py", "exec"), ns)

    class _FB:
        fit = staticmethod(ns["fit"])
        predict = staticmethod(ns["predict"])
        MIN_TRAIN = ns["MIN_TRAIN"]
        RIDGE = ns["RIDGE"]
    return _FB


fb_model = _load_fb_fit()   # the one ridge-logistic fit (spec §3)

MARKETS = ("strikeouts", "outs")
CANDIDATES = ("C1", "C2", "D")
MIN_N = 300
ALPHA = 0.05 / len(CANDIDATES)
EPS = 1e-12


def _jload(p):
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def logit(p):
    p = min(0.99, max(0.01, p))
    return math.log(p / (1.0 - p))


def loss(p, y):
    p = min(1.0 - EPS, max(EPS, p))
    return -(math.log(p) if y else math.log(1.0 - p))


def parse_raw(s):
    try:
        h, n = str(s).split("/")
        return int(h), int(n)
    except (ValueError, AttributeError):
        return None, None


def load_rows(root=ROOT):
    """Graded pitcher rows joined to their card row. -> (rows, unjoined)."""
    det = _jload(os.path.join(root, "data", "latest",
                              "record-detail.json.gz"))["days"]
    rows, unjoined = [], 0
    for date, drows in sorted(det.items()):
        cp = os.path.join(root, "picks", "%s.json" % date)
        picks = _jload(cp).get("picks", []) if os.path.exists(cp) else []
        j = 0
        for r in drows:
            p = None
            while j < len(picks):
                q = picks[j]
                j += 1
                if ((q.get("pitcher") or q.get("player")) == r.get("player")
                        and q.get("market") == r.get("market")
                        and q.get("side") == r.get("side")
                        and q.get("line") == r.get("line")):
                    p = q
                    break
            if r.get("kind") != "pitcher" or r.get("market") not in MARKETS:
                continue
            if r.get("won") is None:
                continue                          # a void is left out
            h, n = parse_raw((p or {}).get("raw"))
            if (p is None or r.get("blend") is None or r.get("implied") is None
                    or p.get("model") is None or n is None or n <= 0):
                unjoined += 1
                continue
            rows.append({"date": date, "market": r["market"],
                         "y": 1 if r["won"] else 0,
                         "blend": r["blend"] / 100.0,
                         "be": r["implied"] / 100.0,
                         "model": p["model"] / 100.0, "h": h, "n": n,
                         "cluster": "%s|%s" % (date, p.get("game_id") or r.get("game"))})
    return rows, unjoined


# ══════════════════════════════════════════════════════════════════════
# 🔴 WHAT SHIPPED `[scored 2026-09-25]`: C2, the blend with the price.
# card.py reads THESE two functions and nothing else, so the number the
# card prints is fitted by exactly the code the test scored (rule 117).
# ══════════════════════════════════════════════════════════════════════
SHIPPED = "C2"


def graded_rows(root=ROOT, before=None):
    """Graded pitcher rows straight from the record detail, card date
    strictly before `before`. -> [{date, market, y, blend, be}]"""
    p = os.path.join(root, "data", "latest", "record-detail.json.gz")
    try:
        det = _jload(p)["days"]
    except (OSError, ValueError, KeyError):
        return []
    out = []
    for date, drows in sorted(det.items()):
        if before is not None and date >= before:
            continue
        for r in drows:
            if (r.get("kind") != "pitcher" or r.get("market") not in MARKETS
                    or r.get("won") is None or r.get("blend") is None
                    or r.get("implied") is None):
                continue
            out.append({"date": date, "market": r["market"],
                        "y": 1 if r["won"] else 0, "blend": r["blend"] / 100.0,
                        "be": r["implied"] / 100.0})
    return out


def mappings(before, root=ROOT):
    """{market: fitted C2 mapping, or None below fb_model.MIN_TRAIN}, fitted
    on every graded row with a card date before `before` (walk-forward)."""
    rows = graded_rows(root, before)
    out = {}
    for mk in MARKETS:
        tr = [r for r in rows if r["market"] == mk]
        m = fb_model.fit([features(r, SHIPPED) for r in tr], [r["y"] for r in tr])
        out[mk] = None if m is None else dict(m, n_train=len(tr), before=before)
    return out


def corrected(maps, market, blend_pct, be_pct):
    """The printed confidence (0-100), or None when there is no mapping."""
    # ⛔ SAM'S OFF SWITCH: `SHIPPED = None` prints the plain blend again.
    m = (maps or {}).get(market) if SHIPPED else None
    if m is None or blend_pct is None or be_pct is None:
        return None
    return 100.0 * fb_model.predict(
        m, features({"blend": blend_pct / 100.0, "be": be_pct / 100.0}, SHIPPED))


def smoothed(r):
    """D: ½·model + ½·(h + ½)/(n + 1)."""
    return 0.5 * r["model"] + 0.5 * (r["h"] + 0.5) / (r["n"] + 1.0)


def features(r, cand):
    return [logit(r["blend"])] if cand == "C1" else [logit(r["blend"]), logit(r["be"])]


def walk_forward(rows):
    """-> {cand: [(row, p_candidate)]} and the last fitted mappings."""
    out = {c: [] for c in CANDIDATES}
    last = {}
    for r in rows:
        out["D"].append((r, smoothed(r)))
    for mk in MARKETS:
        mrows = [r for r in rows if r["market"] == mk]
        for d in sorted({r["date"] for r in mrows}):
            train = [r for r in mrows if r["date"] < d]
            test = [r for r in mrows if r["date"] == d]
            for cand in ("C1", "C2"):
                m = fb_model.fit([features(r, cand) for r in train],
                                 [r["y"] for r in train])
                if m is None:
                    continue
                last[(cand, mk)] = {"date": d, "n_train": len(train), **m}
                for r in test:
                    out[cand].append((r, fb_model.predict(m, features(r, cand))))
    return out, last


def judge(scored):
    d = [loss(r["blend"], r["y"]) - loss(p, r["y"]) for r, p in scored]
    n, mean, t, p, g = mlb_refit.paired_test_clustered(
        d, [r["cluster"] for r, _ in scored])
    per = {}
    for mk in MARKETS:
        sub = [(r, q) for r, q in scored if r["market"] == mk]
        if sub:
            per[mk] = {"n": len(sub),
                       "card": sum(loss(r["blend"], r["y"]) for r, _ in sub) / len(sub),
                       "candidate": sum(loss(q, r["y"]) for r, q in sub) / len(sub)}
            per[mk]["mean_d"] = per[mk]["card"] - per[mk]["candidate"]
    if n < MIN_N:
        v = "NOT YET MEASURABLE"
    elif (mean is not None and mean > 0 and p is not None and p < ALPHA
          and all(x["mean_d"] >= 0 for x in per.values())):
        v = "QUALIFIES"
    else:
        v = "DOES NOT QUALIFY"
    return {"n": n, "games": g, "mean_d": mean, "t": t, "p": p,
            "per_market": per, "verdict": v}


def bands(scored, key):
    b = {}
    for r, q in scored:
        p = r["blend"] if key == "card" else q
        k = min(9, int(p * 10)) * 10
        x = b.setdefault(k, {"n": 0, "w": 0, "s": 0.0})
        x["n"] += 1
        x["w"] += r["y"]
        x["s"] += p
    return [{"band": "%d-%d" % (k, k + 10), "n": x["n"],
             "stated": round(100 * x["s"] / x["n"], 1),
             "hit": round(100 * x["w"] / x["n"], 1)} for k, x in sorted(b.items())]


def pick_winner(res, scored):
    q = [c for c in CANDIDATES if res[c]["verdict"] == "QUALIFIES"]
    if not q:
        return None
    keys = set.intersection(*[{id(r) for r, _ in scored[c]} for c in q])

    def ll(c):
        s = [(r, p) for r, p in scored[c] if id(r) in keys]
        return sum(loss(p, r["y"]) for r, p in s) / max(1, len(s))
    return min(q, key=ll)


def score(root=ROOT):
    rows, unjoined = load_rows(root)
    scored, last = walk_forward(rows)
    res = {c: judge(scored[c]) for c in CANDIDATES}
    for c in CANDIDATES:
        res[c]["bands_card"] = bands(scored[c], "card")
        res[c]["bands_candidate"] = bands(scored[c], "cand")
    return {"spec": "research/mlb_pitcher_cal_spec.md",
            "built_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rows": len(rows), "unjoined": unjoined,
            "rows_by_market": {mk: sum(1 for r in rows if r["market"] == mk) for mk in MARKETS},
            "card_dates": [min(r["date"] for r in rows), max(r["date"] for r in rows)] if rows else None,
            "min_n": MIN_N, "alpha": ALPHA,
            "candidates": res,
            "last_mappings": {"%s/%s" % k: v for k, v in last.items()},
            "ships": pick_winner(res, scored)}


def main():
    out = score()
    for c in CANDIDATES:
        r = out["candidates"][c]
        print("%-3s %-18s n=%d games=%d mean_d=%+.4f p=%s  %s" % (
            c, r["verdict"], r["n"], r["games"], r["mean_d"] or 0,
            "%.4f" % r["p"] if r["p"] is not None else "-",
            "  ".join("%s card %.3f -> %.3f" % (mk, x["card"], x["candidate"])
                      for mk, x in r["per_market"].items())))
    print("ships:", out["ships"])
    path = os.path.join(ROOT, "research", "mlb_pitcher_cal_run_%s.json"
                        % out["built_at"][:10])
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
