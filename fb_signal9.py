#!/usr/bin/env python3
"""fb_signal9.py — scores signal 9's three uses by Sam's keep rule, exactly
as `research/fb_signal9_spec.md` §3 fixes it (committed before this file).

Each use, per league, is scored walk-forward WITH and WITHOUT signal 9,
everything else identical, on that use's own record:
  props model  -> its graded rungs
  card         -> the graded published props (as fb_card_fix)
  game model   -> its closing-line walk-forward
d = log loss without − log loss with; KEPT if mean d >= 0 (the clustered
p is reported beside, never part of the rule). A use with nothing to
score stays OFF.

⛔ It changes nothing live by itself: each use's switch is a constant set
from the recorded result, and a test fails if they disagree. Nothing MLB.
⚠️ STDLIB ONLY.
"""
import math

import card_fb
import fb_card_fix as X
import fb_model as F
import fb_model_lambda as FL
import fb_props_model as M
import mlb_refit
import signal9

CLIP = 1e-12


def logloss(p, y):
    p = min(1 - CLIP, max(CLIP, p))
    return -(math.log(p) if y else math.log(1 - p))


def keep_rule(pairs):
    """pairs: [(ll_without, ll_with, cluster)]. spec §3: kept iff mean d >= 0."""
    if not pairs:
        return {"n": 0, "mean_d": None, "p": None, "clusters": 0, "keep": False,
                "why": "nothing to score — stays off"}
    d = [a - b for a, b, _c in pairs]
    n, mean, t, p, G = mlb_refit.paired_test_clustered(d, [c for _a, _b, c in pairs])
    return {"n": n, "mean_d": mean, "t": t, "p": p, "clusters": G, "keep": mean >= 0,
            "why": ("not worse (mean log-loss difference %+.4f >= 0)" % mean) if mean >= 0
            else ("worse (mean log-loss difference %+.4f < 0)" % mean)}


def _with_flag(module, name, value, fn, lg="nfl"):
    """Run fn with ONE league's switch set to value; restore after."""
    old = dict(getattr(module, name))
    getattr(module, name)[lg] = value
    try:
        return fn()
    finally:
        setattr(module, name, old)


# ── props model ─────────────────────────────────────────────────────────
def score_props(lg, root=None):
    if not signal9.load(lg, 2026, root):
        return keep_rule([]), None
    wf0 = _with_flag(M, "S9_PROPS", False, lambda: M.walk_forward(lg, root), lg)
    wf1 = _with_flag(M, "S9_PROPS", True, lambda: M.walk_forward(lg, root), lg)
    key = lambda r: (r["game"], r["player"], r["market"], r["line"])  # noqa: E731
    on = {key(r): r for r in wf1["graded"] if r.get("p_model") is not None}
    pairs = [(logloss(r["p_model"], r["y"]), logloss(on[key(r)]["p_model"], r["y"]), r["game"])
             for r in wf0["graded"] if r.get("p_model") is not None and key(r) in on]
    rec = {v: {mk: F.record([p for p in wf["picks"] if p["market"] == mk]) for mk in M.markets_for(lg)}
           for v, wf in (("without", wf0), ("with", wf1))}
    return keep_rule(pairs), rec


# ── card ─────────────────────────────────────────────────────────────────
def score_card(lg, root=None):
    opp = signal9.load(lg, 2026, root)
    if not opp:
        return keep_rule([]), None

    def scale(pid, row):
        pl = (opp.get("players") or {}).get(pid) or {}
        return signal9.card_scale(opp, pid, pl.get("team_now"), signal9.week_of(lg, row["day"], root),
                                  row.get("market"))
    base, _u0 = X.score_league(lg, root)
    s9, _u1 = X.score_league(lg, root, scale=scale)
    key = lambda r: (r["day"], r.get("player"), r.get("market"), r.get("side"), r.get("line"))  # noqa: E731
    on = {key(r): r for r in s9}
    pairs = [(logloss(r["fixed"], r["y"]), logloss(on[key(r)]["fixed"], r["y"]), r["cluster"])
             for r in base if key(r) in on]
    rec = {v: {"n": len(rs), "log_loss": (sum(logloss(r["fixed"], r["y"]) for r in rs) / len(rs)) if rs else None,
               "bands": X.bands(rs, "fixed")} for v, rs in (("without", base), ("with", s9))}
    return keep_rule(pairs), rec


# ── game model ───────────────────────────────────────────────────────────
def _closing_preds(rows, flag):
    """{(game, market): (p, y)} from the closing-line walk-forward at λ = 1."""
    def run():
        out = {}
        for mk in F.MARKETS:
            fits = FL.weekly_fits(rows, mk, grid=(F.RIDGE,))
            weeks = {}
            for r in rows:
                weeks.setdefault(F.monday(r["day"]), []).append(r)
            for wk, models, _own in fits:
                m = models.get(F.RIDGE)
                if m is None:
                    continue
                for r in weeks.get(wk, []):
                    if not r["final"]:
                        continue
                    for _b, line, _pa, _pb, _as in F.closing_quotes(r, mk)[:1]:
                        y = FL.closing_outcome(r, mk, line)
                        if y is not None:
                            out[(r["id"], mk)] = (F.predict(m, FL.closing_features(r, mk, line)), y)
        return out
    lg = rows[0].get("lg", "nfl") if rows else "nfl"
    return _with_flag(F, "S9_GAME", flag, run, lg)


def score_game(lg, rows):
    if not any(r["sig"].get("vac_h") is not None for r in rows):
        return keep_rule([]), None
    p0, p1 = _closing_preds(rows, False), _closing_preds(rows, True)
    pairs = [(logloss(p, y), logloss(p1[k][0], y), "%s:%s" % (lg, k[0])) for k, (p, y) in p0.items() if k in p1]
    rec = {}
    for v, flag in (("without", False), ("with", True)):
        wf = _with_flag(F, "S9_GAME", flag, lambda: F.walk_forward(rows), lg)
        rec[v] = {name: {mk: F.record(wf[name][mk]) for mk in F.MARKETS} for name in ("books", "closing")}
    return keep_rule(pairs), rec
