#!/usr/bin/env python3
"""fb_card_calibration.py — calibrating the football props card's printed
confidence, exactly as `research/fb_card_calibration_spec.md` fixes it
(Sam, 2026-09-24; committed before this file existed).

    LEAGUE=nfl python fb_card_calibration.py

Walk-forward: each week's mapping from printed to calibrated confidence is
fitted only on the card's picks graded BEFORE that week, both leagues
pooled. Raw and calibrated are scored on the same picks, clustered by game.

⛔ IT CHANGES NOTHING THE CARD PRINTS. If the rule is met, applying it is
a separate PR and Sam's decision (spec §3). It never edits a published
pick, and it never reads MLB.
⚠️ STDLIB ONLY.
"""
import datetime
import gzip
import json
import math
import os
import sys

import calibration as C             # band_flags: the ONE per-band rule
import fb_model as F                # fit, predict, monday, L: the one logistic fit
import mlb_refit                    # paired_test_clustered: the ONE cluster-robust paired test
import record_fb                    # calibration_by_method: the ONE per-method bucketer

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUE = os.environ.get("LEAGUE", "nfl")
LEAGUES = ("nfl", "ncaaf")          # ⛔ football only — never MLB
MIN_N = 500                         # ⛔ spec §2 (Sam)
ALPHA = 0.05                        # ⛔ spec §2 (Sam)
CLIP_RAW = (0.01, 0.99)             # ⛔ spec §3
CLIP = 1e-12
# `[Sam, 2026-09-24]` "Keep #155's calibration test running. Report picks
# from before and after the fix separately so they are never mixed." The
# registered test reads the method it was registered on; the fixed card's
# picks are scored the same way, apart, and never pooled with it.
REGISTERED_METHOD = "2025-only"


def log(m):
    print(m, flush=True)


def L(value, basis):
    return F.L(value, basis)


def logit(p):
    p = min(CLIP_RAW[1], max(CLIP_RAW[0], p))
    return math.log(p / (1.0 - p))


def logloss(p, y):
    p = min(1 - CLIP, max(CLIP, p))
    return -(math.log(p) if y else math.log(1 - p))


def load_picks(root=None, method=REGISTERED_METHOD):
    """spec §3: every graded, rated row of the card's own record, both
    leagues. ⛔ A void or ungradable row (won is None) is left out."""
    out = []
    for lg in LEAGUES:
        try:
            det = json.load(gzip.open(os.path.join(root or ROOT, "data", lg, "latest",
                                                   "record-detail.json.gz"), "rt", encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for day, rows in (det.get("days") or {}).items():
            for r in rows or []:
                if r.get("confidence") is None or r.get("won") not in (True, False):
                    continue
                if (r.get("card_method") or REGISTERED_METHOD) != method:
                    continue
                out.append({"league": lg, "day": day, "raw": float(r["confidence"]) / 100.0,
                            "y": 1 if r["won"] else 0,
                            "game": "%s:%s:%s" % (lg, r.get("game"), (r.get("commence") or "")[:10]),
                            "player": r.get("player"), "market": r.get("market"), "side": r.get("side")})
    return sorted(out, key=lambda p: p["day"])


def mapping(model):
    """(a, b) on the logit scale from fb_model's standardised fit."""
    w0, w1 = model["w"]
    mu, sd = model["mu"][0], model["sd"][0]
    return w0 - w1 * mu / sd, w1 / sd


def walk_forward(picks):
    """-> (scored picks, {week: (a, b) or None}). Each week's mapping is
    fitted on picks from card dates BEFORE that week's Monday only."""
    weeks = sorted({F.monday(p["day"]) for p in picks})
    scored, maps = [], {}
    for wk in weeks:
        train = [p for p in picks if p["day"] < wk]
        model = F.fit([[logit(p["raw"])] for p in train], [p["y"] for p in train])
        maps[wk] = mapping(model) if model else None
        if not model:
            continue
        for p in picks:
            if F.monday(p["day"]) == wk:
                scored.append(dict(p, cal=F.predict(model, [logit(p["raw"])]), week=wk))
    return scored, maps


def verdict(n, mean_d, p):
    if n < MIN_N:
        return "NOT YET MEASURABLE"
    return "QUALIFIES" if (mean_d is not None and mean_d > 0 and p is not None
                           and p < ALPHA) else "DOES NOT QUALIFY"


def decision(scored):
    """spec §3: d = raw loss − calibrated loss, clustered by game, pooled."""
    d = [logloss(s["raw"], s["y"]) - logloss(s["cal"], s["y"]) for s in scored]
    n, mean, t, p, G = mlb_refit.paired_test_clustered(d, [s["game"] for s in scored])
    return {"n": n, "mean_d": mean, "t": t, "p": p, "clusters": G, "verdict": verdict(n, mean, p)}


def bands(rows, key):
    """Stated vs actual in 10-point bands — DESCRIPTIVE."""
    bk = [{"lo": 10 * i, "n": 0, "said": 0.0, "hit": 0} for i in range(10)]
    for r in rows:
        b = bk[min(9, int(r[key] * 100 // 10))]
        b["n"] += 1
        b["said"] += r[key]
        b["hit"] += r["y"]
    return [{"bucket": "%d-%d%%" % (b["lo"], b["lo"] + 10), "n": b["n"],
             "stated": round(100 * b["said"] / b["n"], 1), "actual": round(100 * b["hit"] / b["n"], 1)}
            for b in bk if b["n"]]


def _band_rows(flags):
    """calibration.band_flags rows -> the page's rows. ⛔ One copy, read by
    both the current method's table and the before-the-fix table."""
    return [{"bucket": b["bucket"], "graded": L(b["n"], "DESCRIPTIVE"),
             "stated": L(round(b["stated"], 1), "DESCRIPTIVE"),
             "actual": L(b["actual"], "DESCRIPTIVE"), "flag": b["state"]}
            for b in flags]


def page_bands(lg, root=None):
    """The card's own record, every 10-point band, with calibration.py's
    per-band verdict. What the page shows next to the card."""
    try:
        rec = json.load(open(os.path.join(root or ROOT, "data", lg, "latest", "record.json"),
                             encoding="utf-8"))
    except (OSError, ValueError):
        return []
    # ⚠️ The rows below are calibration.band_flags' OWN rows (it adds
    #    `actual` and `state`), not record.json's — so they are read from
    #    that function's result, held apart from the file.
    flags = C.band_flags(rec.get("calibration"))
    return _band_rows(flags)


def _graded_rows(lg, root=None):
    """The card's graded rows, oldest card first, from its own detail file."""
    try:
        det = json.load(gzip.open(os.path.join(root or ROOT, "data", lg, "latest",
                                               "record-detail.json.gz"), "rt", encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [r for _day, rows in sorted((det.get("days") or {}).items()) for r in rows or []
            if r.get("won") in (True, False)]


def _method_of(r):
    # ⚠️ A row with no method was printed before the field existed, and
    #    every such card rated the 2025-only way.
    return r.get("card_method") or REGISTERED_METHOD


def _method_now(lg, root=None):
    rows = _graded_rows(lg, root)
    return _method_of(rows[-1]) if rows else REGISTERED_METHOD


def page_bands_before(lg, root=None):
    """The card's EARLIER method(s), each band apart — never pooled with
    the current method's table `[Sam, 2026-09-24]`. Buckets by record_fb's
    own `calibration_by_method` (one copy), from the graded rows."""
    rows = [dict(r, card_method=_method_of(r)) for r in _graded_rows(lg, root)]
    cur = _method_of(rows[-1]) if rows else REGISTERED_METHOD
    _now, by = record_fb.calibration_by_method(rows, cur)
    out = {}
    for m, cal in by.items():
        if m == cur:
            continue
        out[m] = _band_rows(C.band_flags(cal))
    return out


def build(lg=None, root=None, out=None):
    lg = (lg or LEAGUE).lower()
    picks = load_picks(root)
    scored, maps = walk_forward(picks)
    dec = decision(scored)
    # the fixed card's own picks, the same test, APART
    picks_fx = load_picks(root, method="season-blend")
    scored_fx, _maps_fx = walk_forward(picks_fx)
    dec_fx = decision(scored_fx)
    per = {}
    for x in LEAGUES:
        ss = [s for s in scored if s["league"] == x]
        per[x] = {"n": len(ss),
                  "raw": (sum(logloss(s["raw"], s["y"]) for s in ss) / len(ss)) if ss else None,
                  "calibrated": (sum(logloss(s["cal"], s["y"]) for s in ss) / len(ss)) if ss else None}
    doc = {"league": lg, "kind": "DESCRIPTIVE",
           "built_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "spec": "research/fb_card_calibration_spec.md",
           "bands": page_bands(lg, root),
           "bands_before": page_bands_before(lg, root),
           "method_now": _method_now(lg, root),
           "test": dict(dec, graded_picks=len(picks), min_n=MIN_N, applied=False),
           "test_after_fix": dict(dec_fx, graded_picks=len(picks_fx), min_n=MIN_N,
                                  method="season-blend"),
           "log_loss": per,
           "scored_bands": {"raw": bands(scored, "raw"), "calibrated": bands(scored, "cal")},
           "mappings": {wk: (list(ab) if ab else None) for wk, ab in maps.items()},
           "note": ("Stated is what the card printed; actual is how those plays did. A correction "
                    "replaces the printed number only if it passes Sam's rule, and even then only "
                    "by his decision.")}
    path = out or os.path.join(root or ROOT, "data", lg, "latest", "card-calibration.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    log("%s card calibration: %s (n=%s of %s needed, p=%s), %d graded picks"
        % (lg, dec["verdict"], dec["n"], MIN_N, dec["p"], len(picks)))
    return doc


if __name__ == "__main__":
    build()
    sys.exit(0)
