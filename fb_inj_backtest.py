#!/usr/bin/env python3
"""fb_inj_backtest.py — THE INJURY BACKTEST, by the bar fixed before it ran.

`[Sam, 2026-10-17]` NFL injuries: "In the sim, backtest-gated" (research/fb_sim_design.md §3);
college: "use the college injury source as long as it's accurate and up to date"
(research/cfb_injuries_design.md §4, the same bar). This is the runner both bars name, committed
so the recorded numbers can be reproduced.

The question, per league: the smooth curve fed the injury-moved predicted score, against the smooth
curve without it, over the Model picks record's walk-forward weeks. Each week's fits, spreads of
results and injury sizes (`fb_model.injury_fit`) come from earlier games only.
  (a) log loss over every final game's main closing spread and total (a push left out);
  (b) the closing-line record's spread and total picks pooled, as profit per bet.
Injuries switch on (`fb_model.INJURIES[lg]`) only if (a) with <= without AND (b) with >= without;
`test_fb_sim.py` §3 fails when the switch disagrees with the recorded entry.

    python fb_inj_backtest.py <nfl|ncaaf> [out.json]           measure and print
    python fb_inj_backtest.py <nfl|ncaaf> --record             ...and record it, ONCE

⛔ `--record` refuses to overwrite a league's recorded entry: the bar is run once.
"""
import collections
import json
import math
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
RECORD = os.path.join(ROOT, "research", "fb_sim_backtest.json")


def logloss_pair(F, rows, lg):
    """(log losses without, with, the last few weekly fits): the smooth curve at each final
    game's main closing spread and total, from the score without and with injuries."""
    weeks = collections.defaultdict(list)
    for r in rows:
        weeks[F.monday(r["day"])].append(r)
    N = statistics.NormalDist()
    ll = {"without": [], "with": []}
    fits = []
    for wk in sorted(weeks):
        train = [r for r in rows if r["day"] < wk]
        models = {}
        for mk in F.MARKETS:
            data = [(F.features(r, mk), F.label(r, mk)) for r in train if F.label(r, mk) is not None]
            models[mk] = F.fit([x for x, _ in data], [y for _, y in data], zmax=F.ZMAX)
        if not models["moneyline"]:
            continue
        sigma, sigma_t = F.score_sigma(train), F.total_sigma(train)
        b = F.injury_fit(train)
        if b:
            fits.append((wk, [round(x, 2) for x in b]))
        for r in weeks[wk]:
            if not r["final"]:
                continue
            scs = {}
            for tag, on in (("without", False), ("with", True)):
                F.INJURIES[lg] = on
                scs[tag] = F.game_score(r, dict(models, injury=b), sigma, sigma_t)[1]
            F.INJURIES[lg] = True
            if not scs["without"] or not scs["with"]:
                continue
            for mk in ("spread", "total"):
                cq = F.closing_quotes(r, mk)
                if not cq or cq[0][1] is None:
                    continue
                ln = cq[0][1]
                y = F.label(r, mk, **({"M": ln} if mk == "spread" else {"T": ln}))
                if y is None:
                    continue
                for tag, sc in scs.items():
                    h, a = float(sc["home"]), float(sc["away"])
                    mu, s = ((h - a), sigma) if mk == "spread" else ((h + a), sigma_t)
                    p = min(1 - 1e-6, max(1e-6, N.cdf((mu - ln) / s)))
                    ll[tag].append(-(y * math.log(p) + (1 - y) * math.log(1 - p)))
    return ll, fits


def returns(F, rows, lg, on):
    """{books|closing: profit per bet in %} of the walk-forward record's spread + total picks."""
    F.INJURIES[lg] = on
    wf = F.walk_forward(rows)
    out = {}
    for name in ("books", "closing"):
        ps = [p for mk in ("spread", "total") for p in wf[name][mk]]
        units = sum((F.decimal(p["price"]) - 1.0) if p["won"] else (0.0 if p["won"] is None else -1.0)
                    for p in ps)
        out[name] = round(100 * units / len(ps), 2) if ps else None
    return out


def measure(lg, root=None):
    """-> the entry `research/fb_sim_backtest.json` records under injuries.<lg>."""
    import fb_model as F
    t0 = time.time()
    saved = dict(F.INJURIES)
    try:
        F.INJURIES[lg] = True
        rows = F.build_rows(lg, root)
        n_inj = sum(1 for r in rows if (r.get("sig") or {}).get("inj"))
        ll, fits = logloss_pair(F, rows, lg)
        off, on = returns(F, rows, lg, False), returns(F, rows, lg, True)
    finally:
        F.INJURIES.clear()
        F.INJURIES.update(saved)
    return {"questions": len(ll["with"]), "rows_with_injury_reading": n_inj,
            "logloss": {k: round(statistics.mean(v), 5) if v else None for k, v in ll.items()},
            "closing_return": {"without": off["closing"], "with": on["closing"]},
            "books_return": {"without": off["books"], "with": on["books"]},
            "fitted_last": list(fits[-1]) if fits else None,
            "seconds": round(time.time() - t0)}


def passes(entry):
    """The bar: log loss with <= without AND closing return with >= without."""
    ll, cr = entry.get("logloss") or {}, entry.get("closing_return") or {}
    if None in (ll.get("with"), ll.get("without"), cr.get("with"), cr.get("without")):
        return False
    return ll["with"] <= ll["without"] and cr["with"] >= cr["without"]


def record(lg, entry, path=RECORD):
    """Write `entry` under injuries.<lg>, ONCE. -> True when written."""
    doc = json.load(open(path, encoding="utf-8"))
    inj = doc.setdefault("injuries", {})
    if lg in inj:
        print("⛔ injuries.%s is already recorded; the bar is run once. Nothing written." % lg)
        return False
    inj[lg] = entry
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return True


def main(argv):
    if not argv or argv[0] not in ("nfl", "ncaaf"):
        print(__doc__)
        return 2
    lg = argv[0]
    entry = measure(lg)
    print(json.dumps(entry, indent=1))
    print("PASSES the bar" if passes(entry) else "FAILS the bar")
    if "--record" in argv[1:]:
        return 0 if record(lg, entry) else 1
    rest = [a for a in argv[1:] if not a.startswith("--")]
    if rest:
        json.dump(entry, open(rest[0], "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
