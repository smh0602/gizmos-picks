#!/usr/bin/env python3
"""fb_alt_lines.py — is the game model calibrated away from the main line?

Scores the check `research/fb_alt_lines_spec.md` pre-registered (Sam,
2026-09-24; committed on its own before this file existed): walk-forward
over 2025 and 2026 finals, the model's probability at rungs of the main
line ±3, ±7 and ±10 against a normal market baseline whose spread is fitted
on earlier weeks only, log loss clustered by game.

⛔ THE RESULT DECIDES A LABEL, NEVER WHETHER A NUMBER SHOWS. The Game Lines
tab prints every rung's model % either way; this file only says which ones
carry "not calibrated away from the main line".
⛔ Changes no model, no probability, no card. Nothing MLB.
⚠️ STDLIB ONLY. Called by `fb_model.build` with the rows it already built,
so it adds no second pass over the data (card-fb's time is budgeted).
"""
import collections
import datetime
import json
import math
import os

import calibration                  # band_flags, MIN_N — the ONE per-band rule
import fb_model as F
import mlb_refit                    # paired_test_clustered — the ONE clustered test

ROOT = os.path.dirname(os.path.abspath(__file__))
DELTAS = (-10, -7, -3, 3, 7, 10)    # ⛔ spec §3a
MARKETS = ("spread", "total")       # ⛔ spec §1: moneylines have no rungs
MIN_N = calibration.MIN_N           # ⛔ spec §3b
TESTED_RANGE = 10                   # ⛔ spec §3d
CLIP = 1e-12                        # ⛔ spec §3a
WARNING = "not calibrated away from the main line"


def logloss(p, y):
    p = min(1.0 - CLIP, max(CLIP, p))
    return -(math.log(p) if y else math.log(1.0 - p))


def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _main(r, mk):
    return r["M"] if mk == "spread" else r["T"]


def _outcome(r, mk):
    hs, a = float(r["hs"]), float(r["as"])
    return hs - a if mk == "spread" else hs + a


def _at(r, mk, line):
    return {"M": line} if mk == "spread" else {"T": line}


def score(rows):
    """-> [unit] for every (game, market, δ) the spec scores, walk-forward."""
    weeks = collections.defaultdict(list)
    for r in rows:
        weeks[F.monday(r["day"])].append(r)
    units = []
    for wk in sorted(weeks):
        train = [r for r in rows if r["day"] < wk]
        for mk in MARKETS:
            lab = [r for r in train if F.label(r, mk) is not None]
            model = F.fit([F.features(r, mk) for r in lab], [F.label(r, mk) for r in lab],
                          ridge=F.RIDGE)
            if not model:
                continue
            sq = [(_outcome(r, mk) - _main(r, mk)) ** 2 for r in lab]
            sigma = math.sqrt(sum(sq) / len(sq)) if sq else None
            if not sigma:
                continue
            for r in weeks[wk]:
                if not r["final"] or r["hs"] is None or r["as"] is None or _main(r, mk) is None:
                    continue
                for dl in DELTAS:
                    line = _main(r, mk) + dl
                    y = F.label(r, mk, **_at(r, mk, line))
                    if y is None:
                        continue
                    pm = F.predict(model, F.features(r, mk, **_at(r, mk, line)))
                    pb = 1.0 - phi(dl / sigma)
                    units.append({"game": r["id"], "season": r["season"], "market": mk,
                                  "delta": dl, "p_model": pm, "p_base": pb, "y": y,
                                  "d": logloss(pb, y) - logloss(pm, y)})
    return units


def verdict(units):
    """spec §3b: NOT YET MEASURABLE under MIN_N, else PASS iff mean d >= 0."""
    n = len(units)
    if not n:
        return {"state": "NOT YET MEASURABLE", "n": 0, "games": 0, "mean_d": None, "p": None}
    _n, mean, _t, p, G = mlb_refit.paired_test_clustered([u["d"] for u in units],
                                                         [u["game"] for u in units])
    state = ("NOT YET MEASURABLE" if n < MIN_N else "PASS" if mean >= 0 else "FAIL")
    return {"state": state, "n": n, "games": G, "mean_d": mean, "p": p}


def band_of(p):
    """The 10-point band a stated probability falls in, as calibration names it."""
    i = min(9, max(0, int(100.0 * p // 10)))
    return "%d-%d%%" % (10 * i, 10 * i + 10)


def bands(units):
    """spec §3c: both sides of every unit, 10-point bands, judged by
    calibration.band_flags — never a second copy of that rule."""
    acc = collections.OrderedDict((band_of(i / 10.0 + 0.05), [0, 0, 0.0]) for i in range(10))
    for u in units:
        for p, y in ((u["p_model"], u["y"]), (1.0 - u["p_model"], 1 - u["y"])):
            b = acc[band_of(p)]
            b[0] += 1
            b[1] += y
            b[2] += 100.0 * p
    cal = [{"bucket": k, "n": n, "w": w, "stated": s / n} for k, (n, w, s) in acc.items() if n]
    return calibration.band_flags(cal)


def finding(m):
    """What the check found for one market, in plain words, or None if it
    passed. ⚠️ Read off the stored bands and log losses — it describes the
    result and changes nothing the frozen rule decides."""
    if not m or m.get("state") == "PASS":
        return None
    hi = [b for b in m.get("bands") or [] if (b.get("stated") or 0) >= 60]
    n, w = sum(b["n"] for b in hi), sum(b["w"] for b in hi)
    if n >= calibration.BAND_MIN_N and w / n < 0.5:
        return ("it points the wrong way away from the main line: rungs it rated "
                "60%% or more won %d%% of the time" % round(100.0 * w / n))
    if m.get("state") == "FAIL" and m.get("log_loss_model") is not None:
        return ("it is less accurate than the books' own line away from the main line "
                "(log loss %.3f against %.3f)" % (m["log_loss_model"], m["log_loss_baseline"]))
    return "it has not been tested away from the main line yet"


def label(check, market, p, distance):
    """spec §3d -> (calibrated?, warning or None) for one shown rung.

    `check` is the stored document, `p` the probability shown for that side,
    `distance` |rung − main line|. ⛔ The number is shown either way."""
    m = ((check or {}).get("markets") or {}).get(market) or {}
    if m.get("state") != "PASS":
        why = "not yet tested" if m.get("state") in (None, "NOT YET MEASURABLE") else None
        return False, WARNING + (" (%s)" % why if why else "")
    if distance is None or distance > TESTED_RANGE:
        return False, WARNING + " (beyond the tested 10 points)"
    under = {b["bucket"] for b in m.get("bands") or [] if b.get("state") == "UNDER"}
    if p is not None and band_of(p) in under:
        return False, WARNING + " (this band ran under)"
    return True, None


def build(lg, rows=None, root=None, log=print):
    rows = rows if rows is not None else F.build_rows(lg, root)
    units = score(rows)
    doc = {"league": lg, "kind": "DESCRIPTIVE", "spec": "research/fb_alt_lines_spec.md",
           "built_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "warning": WARNING, "tested_range": TESTED_RANGE, "min_n": MIN_N, "markets": {}}
    for mk in MARKETS:
        us = [u for u in units if u["market"] == mk]
        v = verdict(us)
        v["by_distance"] = {}
        for k in (3, 7, 10):
            ds = [u["d"] for u in us if abs(u["delta"]) == k]
            v["by_distance"][str(k)] = {"n": len(ds), "mean_d": (sum(ds) / len(ds)) if ds else None}
        v["by_season"] = {}
        for s in sorted({u["season"] for u in us}):
            ds = [u["d"] for u in us if u["season"] == s]
            v["by_season"][str(s)] = {"n": len(ds), "mean_d": sum(ds) / len(ds)}
        v["log_loss_model"] = (sum(logloss(u["p_model"], u["y"]) for u in us) / len(us)) if us else None
        v["log_loss_baseline"] = (sum(logloss(u["p_base"], u["y"]) for u in us) / len(us)) if us else None
        v["bands"] = bands(us)
        doc["markets"][mk] = v
        log("alt-lines check %s %-6s %s  n=%d games=%s mean d=%s p=%s" % (
            lg, mk, v["state"], v["n"], v["games"],
            "%+.4f" % v["mean_d"] if v["mean_d"] is not None else "—",
            "%.3f" % v["p"] if v["p"] is not None else "—"))
    path = os.path.join(root or ROOT, "data", lg, "latest", "alt-lines-check.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    return doc


if __name__ == "__main__":
    import sys
    build(os.environ.get("LEAGUE", "nfl"))
    sys.exit(0)
