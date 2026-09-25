#!/usr/bin/env python3
"""fb_card_fix.py — scores the football props card's season fix against
the current card, exactly as `research/fb_card_fix_spec.md` fixes it
(Sam, 2026-09-24; committed before this file existed).

    python fb_card_fix.py           # both leagues -> research/fb_card_fix_run_<date>.json

For every prop the card published and that has been graded, the fixed
card's confidence is recomputed as of that card's date (only earlier games,
so walk-forward by construction) and scored against the number the card
printed, clustered by game.

⛔ IT CHANGES NOTHING THE CARD PRINTS. `card_fb.CARD_METHOD` is set by the
ship rule in the PR that records the result. Nothing MLB.
⚠️ STDLIB ONLY.
"""
import datetime
import gzip
import json
import math
import os
import sys

import card_fb                      # rate_blend, position_pools/prior, norm — the ONE rating code
import fb_props_model as M          # league(): card_fb's globals per league; load_logs; champion_logs
import mlb_refit                    # paired_test_clustered: the ONE cluster-robust paired test

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUES = ("nfl", "ncaaf")          # ⛔ football only
MIN_N = 500                         # ⛔ spec §2 (Sam): the small-sample branch
ALPHA = 0.05                        # ⛔ spec §2 (Sam)
CLIP = 1e-12


def log(m):
    print(m, flush=True)


def logloss(p, y):
    p = min(1 - CLIP, max(CLIP, p))
    return -(math.log(p) if y else math.log(1 - p))


def graded_props(lg, root=None):
    """spec §3: every published prop with a printed confidence and a graded
    result. ⛔ Voids and ungradable rows are left out."""
    try:
        det = json.load(gzip.open(os.path.join(root or ROOT, "data", lg, "latest",
                                               "record-detail.json.gz"), "rt", encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for day, rows in sorted((det.get("days") or {}).items()):
        for r in rows or []:
            if r.get("confidence") is None or r.get("won") not in (True, False):
                continue
            out.append(dict(r, day=day, y=1 if r["won"] else 0, current=r["confidence"] / 100.0,
                            cluster="%s:%s:%s" % (lg, r.get("game"), (r.get("commence") or "")[:10])))
    return out


def score_league(lg, root=None, scale=None):
    """-> rows with both probabilities, and the count the fix could not rate.
    `scale(pid, row)` -> r gives signal 9's 2025 scaling (fb_signal9.py); 1 by default."""
    logs = M.load_logs(lg, root)
    season, P25, floor = M.champion_logs(lg, root)
    P26 = logs.get(2026) or {}
    out, unrated = [], 0
    with M.league(lg):
        card_fb.USAGE_FLOOR = floor
        pools = card_fb.position_pools([P25, P26])
        idx = card_fb.index_by_name(P25)
        for r in graded_props(lg, root):
            pids = idx.get(card_fb.norm(r.get("player") or ""), [])
            if len(pids) != 1:
                unrated += 1
                continue
            p = P25[pids[0]]
            day = r["day"]
            g26 = card_fb.games_before((P26.get(pids[0]) or {}).get("g"), day)
            side = r.get("side")
            p0 = card_fb.position_prior(pools, p.get("pos"), r.get("market"), side, r.get("line"), day)
            _r = scale(pids[0], r) if scale else 1.0
            fx = card_fb.rate_blend(p.get("g") or [], g26, r.get("market"), r.get("line"), side, p0, _r)
            if fx is None:
                unrated += 1
                continue
            out.append(dict(r, league=lg, fixed=fx[0] / 100.0, detail=fx[4], pid=pids[0]))
    return out, unrated


def ship(rows):
    """spec §3: d = current loss − fixed loss, clustered by game, pooled."""
    d = [logloss(r["current"], r["y"]) - logloss(r["fixed"], r["y"]) for r in rows]
    n, mean, t, p, G = mlb_refit.paired_test_clustered(d, [r["cluster"] for r in rows])
    if mean is not None and mean > 0 and p is not None and p < ALPHA:
        verdict, why = "LIVE", "its log loss beats the current card's, one-sided p < 0.05"
    elif n < MIN_N and mean is not None and mean >= 0:
        verdict, why = "LIVE", "fewer than 500 graded props, and it is not worse (mean difference >= 0)"
    else:
        verdict, why = "STAYS", "it did not beat the current card, and it is worse on average"
    return {"n": n, "mean_d": mean, "t": t, "p": p, "clusters": G, "verdict": verdict, "why": why}


def bands(rows, key):
    bk = [{"lo": 10 * i, "n": 0, "said": 0.0, "hit": 0} for i in range(10)]
    for r in rows:
        b = bk[min(9, int(r[key] * 100 // 10))]
        b["n"] += 1
        b["said"] += r[key]
        b["hit"] += r["y"]
    return [{"bucket": "%d-%d%%" % (b["lo"], b["lo"] + 10), "n": b["n"],
             "stated": round(100 * b["said"] / b["n"], 1), "actual": round(100 * b["hit"] / b["n"], 1)}
            for b in bk if b["n"]]


def main(out=None, root=None):
    rows, per = [], {}
    for lg in LEAGUES:
        rs, unrated = score_league(lg, root)
        rows += rs
        per[lg] = {"scored": len(rs), "not_rated_by_fix": unrated,
                   "log_loss_current": (sum(logloss(r["current"], r["y"]) for r in rs) / len(rs)) if rs else None,
                   "log_loss_fixed": (sum(logloss(r["fixed"], r["y"]) for r in rs) / len(rs)) if rs else None,
                   "hit_rate": (sum(r["y"] for r in rs) / len(rs)) if rs else None,
                   "bands_current": bands(rs, "current"), "bands_fixed": bands(rs, "fixed")}
    dec = ship(rows)
    doc = {"spec": "research/fb_card_fix_spec.md",
           "built_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "decision": dec, "leagues": per,
           "rows": [{k: r.get(k) for k in ("league", "day", "player", "market", "side", "line",
                                           "current", "fixed", "y", "cluster", "detail")} for r in rows]}
    path = out or os.path.join(root or ROOT, "research", "fb_card_fix_run_%s.json"
                               % datetime.date.today().isoformat())
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    log("card fix: %s — %s (n=%s, mean d=%s, p=%s, games=%s)"
        % (dec["verdict"], dec["why"], dec["n"], dec["mean_d"], dec["p"], dec["clusters"]))
    return doc


if __name__ == "__main__":
    main()
    sys.exit(0)
