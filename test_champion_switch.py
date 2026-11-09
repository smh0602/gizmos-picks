#!/usr/bin/env python3
"""§3j — AFTER A CHAMPION SWITCH (research/fb_refit_spec.md). `[Sam, 2026-11-08]`

HC won college's 11-02 contest, the first WINS, so its branch is the first champion switch the
code would run. Three questions were put to Sam, each with a default; he answered *"ok i approve
of all 3"*:

1. k keeps the champion: a switch never loosens the bar (college stays 0.01 / 13, fewer only by a
   withdrawal, §3h: with HC named, P's window is measured against HC and P is withdrawn, so 0.01 / 12).
2. A challenger that would throw the champion's first input away (T, AT, ATC against H, HC, SM,
   SMC, and the class) is NOT APPLICABLE: never scored, never withdrawn, still one of k.
3. The spread of results, the injury sizing and the email's "miss by" read the CHAMPION's own
   predicted numbers (`fb_model.own_score`), not today's model's.

And what §2 and §3g already said, now kept everywhere: H and HC's history rows TRAIN and are
never scored, graded, counted or measured.

Every check is a property of the code, asked against EVERY registered challenger as champion
where it is cheap, on planted rows. Planted rows and trees only. ⛔ Reads no live data, writes
nothing under data/ or picks/.

# @vacuity 🔴 own_score follows the champion (fb_model)
#   file: fb_model.py
#   find:         return fb_challengers.own_score(ch, r)
#   with:         return s.get("own_m"), s.get("own_t")
#
# @vacuity 🔴 own_score is the number each champion's first input is built from (T's talent margin)
#   file: fb_challengers.py
#   find:         m = s.get("tal_m")
#   with:         m = s.get("own_m")
#
# @vacuity 🔴 the injury sizing reads the champion's own numbers
#   file: fb_model.py
#   find:         om, ot = own_score(r)            # §3j: the champion's own numbers (today's: own_m, own_t)
#   with:         om, ot = r["sig"]["own_m"], r["sig"]["own_t"]
#
# @vacuity 🔴 the predicted total without a line is the champion's own total
#   file: fb_model.py
#   find:           if T is not None and p_over is not None and sigma_t else own_score(r)[1])   # §3j
#   with:           if T is not None and p_over is not None and sigma_t else r["sig"].get("own_t"))
#
# @vacuity 🔴 the email's "miss by" reads the champion's own numbers
#   file: fb_refit.py
#   find:     ok = [(r, FM.own_score(r)) for r in rows if r["season"] == SEASON and r["final"] and r["hs"] is not None
#   with:     ok = [(r, (r["sig"].get("own_m"), r["sig"].get("own_t"))) for r in rows if r["season"] == SEASON and r["final"] and r["hs"] is not None
#
# @vacuity 🔴 history rows carry their flag
#   file: fb_challengers.py
#   find: "season": g.get("season"), "history": True,
#   with: "season": g.get("season"),
#
# @vacuity 🔴 a contest prediction is never a history row
#   file: fb_refit.py
#   find:             if y is None or FM.is_history(r) or not keep(r):     # §3j: history rows only train
#   with:             if y is None or not keep(r):
#
# @vacuity 🔴 the graded record never grades a history row
#   file: fb_model.py
#   find:                 if not r["final"] or is_history(r):
#   with:                 if not r["final"]:
#
# @vacuity 🔴 the spread of results is measured over the same games whoever is champion
#   file: fb_model.py
#   find:         if not r["final"] or r.get("hs") is None or r.get("as") is None or is_history(r):
#   with:         if not r["final"] or r.get("hs") is None or r.get("as") is None:
#
# @vacuity 🔴 the email's "miss by" never measures a history row
#   file: fb_refit.py
#   find:           and not FM.is_history(r) and r["M"] is not None and r["T"] is not None]
#   with:           and r["M"] is not None and r["T"] is not None]
#
# @vacuity 🔴 the alt-lines check never scores a history row
#   file: fb_alt_lines.py
#   find:                         or F.is_history(r)):
#   with:                         or False):
#
# @vacuity 🔴 the lambda report never picks its ridge on a history row
#   file: fb_model_lambda.py
#   find:                if F.label(r, market) is not None and not F.is_history(r)]      # history row
#   with:                if F.label(r, market) is not None]
#
# @vacuity 🔴 the lambda report never scores a history row
#   file: fb_model_lambda.py
#   find:                 if not r["final"] or F.is_history(r):
#   with:                 if not r["final"]:
#
# @vacuity 🔴 the lambda report lists no week of history rows only
#   file: fb_model_lambda.py
#   find:             if any(r["final"] and not F.is_history(r) for r in weeks[wk]):   # a week not yet played
#   with:             if any(r["final"] for r in weeks[wk]):   # a week not yet played
#
# @vacuity 🔴 a challenger with only its own inputs never trains on the champion's history rows
#   file: fb_refit.py
#   find:     own = [r for r in rows if not FM.is_history(r)] if name in FC.OWN_SCORE else list(rows)
#   with:     own = list(rows)
#
# @vacuity 🔴 ...nor is its number attached to them
#   file: fb_refit.py
#   find:         FC.attach(n, lg, [r for r in rows if not FM.is_history(r)] if n in FC.OWN_SCORE else rows, root)
#   with:         FC.attach(n, lg, rows, root)
#
# @vacuity 🔴 k keeps the champion
#   file: fb_refit.py
#   find:     k = sum(1 for x in results if x["registered"] and not x.get("withdrawn")) + (1 if champion else 0)
#   with:     k = sum(1 for x in results if x["registered"] and not x.get("withdrawn"))
#
# @vacuity 🔴 ...and the weekly report passes the champion to the verdict
#   file: fb_refit.py
#   find:             "challengers": verdicts(res, champion)}
#   with:             "challengers": verdicts(res)}
#
# @vacuity 🔴 a challenger that would throw the champion's first input away is NOT APPLICABLE
#   file: fb_challengers.py
#   find:     if name in FIRST and not all(first_own(ch, mk, k) for mk, k in FIRST[name].items()):    # §3j
#   with:     if False:
#
# @vacuity 🔴 ...and the same number already there (T against TS) is not a throw-away
#   file: fb_challengers.py
#   find:     return champion is None or (champion not in OWN_SCORE and FIRST.get(champion, {}).get(market) in (None, number))
#   with:     return champion is None or (champion not in OWN_SCORE and FIRST.get(champion, {}).get(market) is None)
#
# @vacuity 🔴 the injury backtest scores no history row; the census flags a row builder with no is_history
#   file: fb_inj_backtest.py
#   find:             if not r["final"] or F.is_history(r):      # §3j: history rows train, never scored
#   with:             if not r["final"] or False:      # §3j: history rows train, never scored
"""
import ast
import atexit
import datetime
import glob
import gzip
import json
import math
import os
import random
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import fb_alt_lines as A  # noqa: E402
import fb_challengers as FC  # noqa: E402
import fb_inj_backtest as IB  # noqa: E402
import fb_model as FM  # noqa: E402
import fb_model_lambda as LAM  # noqa: E402
import fb_refit as R  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 11, 9, 10, 0, tzinfo=UTC)          # a Monday
SAVED = dict(FM.CHAMPION)
TREES = []


def tree():
    t = tempfile.mkdtemp(prefix="champswitch-")
    TREES.append(t)
    return t


@atexit.register
def _clean():
    FM.CHAMPION.clear()
    FM.CHAMPION.update(SAVED)
    for t in TREES:
        shutil.rmtree(t, ignore_errors=True)


def put(root, rel, doc):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        json.dump(doc, fh)


class champion:
    """FM.CHAMPION[lg] = name for the block, restored after (an exception too)."""

    def __init__(self, lg, name):
        self.lg, self.name = lg, name

    def __enter__(self):
        self.was = FM.CHAMPION.get(self.lg)
        FM.CHAMPION[self.lg] = self.name

    def __exit__(self, *a):
        FM.CHAMPION[self.lg] = self.was


def names(lg):
    return [n for n, c in FC.CHALLENGERS.items() if c["league"] == lg]


def sig(rng, om, ot):
    """Every number any challenger reads, each distinct, so an input that moved is seen moving."""
    g = lambda s: rng.gauss(0, s)  # noqa: E731
    return {"neutral": 0.0, "dome": 0.0, "own_m": om, "own_t": ot,
            "h2h_m": om + g(4), "h2h_t": ot + g(4), "form_m": om + g(5), "form_t": ot + g(5),
            "def": 0.3 + rng.random() * 0.4, "poss": g(0.05), "out": g(1), "vac_h": g(0.2), "vac_a": g(0.2),
            "h_own": (om + g(2), ot + g(2)), "score": (om + g(2.5), ot + g(2.5)), "tal_m": om + g(3),
            "mc": om + g(1.5), "sam_m": om + g(3), "sam_t": ot + g(3), "epa_m": om + g(4), "ppa_m": om + g(4),
            "cl": (g(1), g(1)), "wl": g(0.5), "aj": {"form": (om + g(4), ot + g(4)), "def": 0.2 + rng.random() * 0.6},
            "inj": {"qb": (float(rng.random() < 0.1), float(rng.random() < 0.1)),
                    "off": (rng.random() * 0.3, rng.random() * 0.3), "def": (rng.random() * 0.3, rng.random() * 0.3)},
            "rest_d": float(rng.choice((-3, 0, 0, 3, 7))), "wx_wind": rng.random() * 20}


def row(rng, i, lg, day, season, history=False):
    teams = ["U%02d" % k for k in range(16)]
    h, a = rng.sample(teams, 2)
    om, ot = rng.gauss(0, 7), 45 + rng.gauss(0, 5)
    s = sig(rng, om, ot)
    hm, ht = s["h_own"]
    margin, total = hm + rng.gauss(0, 11), ht + rng.gauss(0, 10)       # the results follow HC's numbers
    hs, as_ = max(0, round((total + margin) / 2)), max(0, round((total - margin) / 2))
    M, T = math.floor(om) + 0.5, math.floor(ot) + 0.5
    r = {"id": ("hist:%d" if history else "g%d") % i, "lg": lg, "season": season, "day": day,
         "kick": day + "T17:00:00Z", "week": 1, "home": h, "away": a, "final": True, "hs": hs, "as": as_,
         "M": M, "T": T, "pml": 0.6, "snap": None, "dk_ml": None, "sig": s,
         # closing quotes on every row, history rows too, so ONLY the flag keeps them out
         "close": {"spread": [(M, -110, -110, True)], "total": [(T, -110, -110, True)],
                   "moneyline": [(None, -150, 130, False)]}}
    if history:
        r["history"] = True
    return r


def days(start, weeks, per):
    d0 = datetime.date.fromisoformat(start)
    return [(d0 + datetime.timedelta(weeks=w, days=k % 3)).isoformat() for w in range(weeks) for k in range(per)]


def league_rows(lg, seed):
    """R: 2025 (training) and three 2026 weeks; H: a 2024 history season, plus six history rows
    planted INSIDE the 2026 weeks with season 2026, so a season filter alone cannot keep them out."""
    rng = random.Random(seed)
    R_ = [row(rng, i, lg, d, 2025) for i, d in enumerate(days("2025-09-01", 13, 12))]
    R_ += [row(rng, 500 + i, lg, d, 2026) for i, d in enumerate(days("2026-09-07", 3, 10))]
    H = [row(rng, i, lg, d, 2024, history=True) for i, d in enumerate(days("2024-09-02", 10, 9))]
    H += [row(rng, 900 + i, lg, d, 2026, history=True) for i, d in enumerate(days("2026-09-07", 3, 2))]
    return sorted(R_, key=lambda r: r["day"]), sorted(H, key=lambda r: r["day"])


def unflag(rows):
    """The same rows with the history flag taken off: the CONTROL that shows they are scoreable."""
    out = []
    for r in rows:
        c = dict(r, sig=dict(r["sig"]))
        c.pop("history", None)
        out.append(c)
    return out


def as_today(rows, ch):
    """Rows whose today's own numbers ARE champion `ch`'s (fb_challengers.own_score): today's model
    measured on them must give what champion `ch` measures on the originals."""
    out = []
    for r in rows:
        c = dict(r, sig=dict(r["sig"]))
        c["sig"]["own_m"], c["sig"]["own_t"] = FC.own_score(ch, r)
        out.append(c)
    return out


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 own_score IS WHAT EACH CHAMPION'S FIRST INPUTS ARE BUILT FROM (EVERY CHALLENGER)")
# ══════════════════════════════════════════════════════════════════════
_bad, _moved = [], set()
for _lg in ("nfl", "ncaaf"):
    _r = row(random.Random(1), 1, _lg, "2026-10-25", 2026)
    for _ch in [None] + names(_lg):
        with champion(_lg, _ch):
            m, t = FM.own_score(_r)
            xm, xs, xt = (FM.features(_r, mk) for mk in ("moneyline", "spread", "total"))
        if (m, t) != (_r["sig"]["own_m"], _r["sig"]["own_t"]):
            _moved.add(_ch)
        for got, want, what in ((xm[0], m / 10.0, "moneyline"), (xs[0], (m - _r["M"]) / 10.0, "spread"),
                                (xt[0], (t - _r["T"]) / 10.0, "total")):
            if abs(got - want) > 1e-12:
                _bad.append((_lg, _ch, what, got, want))
eq(_bad, [], "🔴 against every champion (and none), its first moneyline, spread and total inputs are "
             "own_score's margin / 10, (margin - line) / 10 and (total - line) / 10")
eq(sorted(_moved), sorted(["H", "HC", "SM", "SMC", "T", "TS", "MC", "MCC", "AT", "ATC"]),
   "🔴 ...and exactly these champions predict from numbers that are not today's own (the rest append or keep)")
with champion("ncaaf", None):
    _r = row(random.Random(2), 2, "ncaaf", "2026-10-25", 2026)
    eq(FM.own_score(_r), (_r["sig"]["own_m"], _r["sig"]["own_t"]),
       "🔴 with no champion named, own_score is today's own margin and total, unchanged")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE SPREAD OF RESULTS, THE INJURY SIZING, THE TOTAL AND \"MISS BY\" FOLLOW THE CHAMPION")
# ══════════════════════════════════════════════════════════════════════
_wrong = []
for _lg in ("nfl", "ncaaf"):
    _rows, _ = league_rows(_lg, 30 if _lg == "nfl" else 31)
    for _ch in names(_lg):
        with champion(_lg, _ch):
            got = (FM.score_sigma(_rows), FM.total_sigma(_rows), FM.injury_fit(_rows), R.misses(_rows),
                   FM.predicted_score(dict(_rows[-1], T=None), 0.6, 13.0))
        _today = as_today(_rows, _ch)
        with champion(_lg, None):
            want = (FM.score_sigma(_today), FM.total_sigma(_today), FM.injury_fit(_today), R.misses(_today),
                    FM.predicted_score(dict(_today[-1], T=None), 0.6, 13.0))
        if got != want:
            _wrong.append((_lg, _ch))
eq(_wrong, [], "🔴 against every champion, score_sigma, total_sigma, injury_fit, the predicted total without "
               "a line and fb_refit.misses are today's model measured on that champion's own numbers")
_rows, _ = league_rows("ncaaf", 31)
with champion("ncaaf", None):
    _was = (FM.score_sigma(_rows), FM.total_sigma(_rows), FM.injury_fit(_rows), R.misses(_rows)["margin_model"])
with champion("ncaaf", "HC"):
    _now = (FM.score_sigma(_rows), FM.total_sigma(_rows), FM.injury_fit(_rows), R.misses(_rows)["margin_model"])
ck(all(a != b for a, b in zip(_was, _now)) and _now[0] < _was[0],
   "   ...and they really move: under HC each is HC's (the planted results follow HC's numbers, so its "
   "spread of results is the narrower one)", (_was[:2], _now[:2]))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 HISTORY ROWS TRAIN; THEY ARE NEVER SCORED (EVERY SCORER, PLANTED ROWS THAT LOOK SCOREABLE)")
# ══════════════════════════════════════════════════════════════════════
_R, _H = league_rows("ncaaf", 3)
_ids, _hid = {r["id"] for r in _R}, {r["id"] for r in _H}
_INJ = dict(FM.INJURIES)
with champion("ncaaf", "HC"):
    _all, _ctl = _R + _H, _R + unflag(_H)
    # the contest's predictions (every window: history, scored, counted, withdrawal)
    _p = {mk: set(R.Fits(_all, FM.features).predictions(mk)) for mk in FM.MARKETS}
    _pc = {mk: set(R.Fits(_ctl, FM.features).predictions(mk)) for mk in FM.MARKETS}
    ck(all(_p[mk] and _p[mk] <= _ids for mk in FM.MARKETS),
       "🔴 the contest prices only 2025-26 rows, the history rows train", {mk: len(v) for mk, v in _p.items()})
    ck(all(_pc[mk] & _hid for mk in FM.MARKETS),
       "   ...(control: the same rows unflagged ARE priced, so the flag is what keeps them out)")
    # the graded record (and its closing-line record)
    _wf = FM.walk_forward(_all)
    _wfc = FM.walk_forward(_ctl)
    _g = {p["game_id"] for rec in _wf.values() for v in rec.values() for p in v}
    _gc = {p["game_id"] for rec in _wfc.values() for v in rec.values() for p in v}
    ck(_g and _g <= _ids and _gc & _hid, "🔴 the graded record grades only 2025-26 games (control: unflagged, "
       "the history rows would be graded)", (len(_g), len(_gc & _hid)))
    # the spread of results and the email's miss by
    eq((FM.score_sigma(_all), FM.total_sigma(_all), R.misses(_all)),
       (FM.score_sigma(_R), FM.total_sigma(_R), R.misses(_R)),
       "🔴 the spread of results and \"miss by\" are measured over the same games with or without history rows")
    ck(FM.score_sigma(_ctl) != FM.score_sigma(_R) and R.misses(_ctl) != R.misses(_R),
       "   ...(control: unflagged, the history rows would move both)")
    # the alt-lines check
    _u = {u["game"] for u in A.score(_all)}
    ck(_u and _u <= _ids and {u["game"] for u in A.score(_ctl)} & _hid,
       "🔴 the alt-lines check scores only 2025-26 games (control: unflagged, it would score history rows)")
    # the lambda report: the ridge choice and the scored set
    _own = sum(len(e[2]) for e in LAM.weekly_fits(_all, "spread"))
    eq(_own, sum(1 for r in _R if FM.label(r, "spread") is not None),
       "🔴 the lambda report chooses its ridge on 2025-26 games only (history rows are never 'a week's games')")
    _sc = {s["game"].split(":", 1)[1] for s in LAM.score_league("ncaaf", _all)["scored"]}
    ck(_sc and _sc <= _ids, "🔴 ...and scores only them", len(_sc))
    # ...and lists no week of its own: enough history rows that their own weeks have a fit
    _rb = random.Random(4)
    _Hbig = [row(_rb, 2000 + i, "ncaaf", d, 2024, history=True) for i, d in enumerate(days("2024-09-02", 15, 12))]
    _hw = {FM.monday(r["day"]) for r in _Hbig}
    _listed = {wk for v in LAM.score_league("ncaaf", _R + _Hbig)["lambdas"].values() for wk, _l in v}
    _listed_c = {wk for v in LAM.score_league("ncaaf", _R + unflag(_Hbig))["lambdas"].values() for wk, _l in v}
    ck(_listed and not _listed & _hw and _listed_c & _hw,
       "🔴 ...and lists a ridge for no week that holds only history rows (control: unflagged, it would)",
       (len(_listed), sorted(_listed_c & _hw)[:3]))
    # the injury backtest: the same training rows, once with the history rows unscoreable (no
    #    closing line, as real ones are), so a different count can only be a history row scored
    _bare = [dict(r, close={}) for r in _H]
    try:
        _ll = IB.logloss_pair(FM, _all, "ncaaf")[0]["with"]
        _llr = IB.logloss_pair(FM, _R + _bare, "ncaaf")[0]["with"]
        _llc = IB.logloss_pair(FM, _ctl, "ncaaf")[0]["with"]
    finally:
        FM.INJURIES.clear()
        FM.INJURIES.update(_INJ)
    ck(_ll and len(_ll) == len(_llr) < len(_llc),
       "🔴 the injury backtest scores no history row, though they train its fits (control: unflagged, it would)",
       (len(_ll), len(_llr), len(_llc)))

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 WHO TRAINS ON THEM: THE CHAMPION AND ITS ADD-ONS, NEVER A CHALLENGER WITH ITS OWN INPUTS")
# ══════════════════════════════════════════════════════════════════════
with champion("ncaaf", "HC"):
    _own_rows = R.challenger_fits(_R + _H, "SMC", "ncaaf", tree()).rows
    _addon = R.challenger_fits(_R + _H, "P", "ncaaf", tree()).rows
ck(not any(FM.is_history(r) for r in _own_rows) and len(_own_rows) == len(_R),
   "🔴 SMC (only its own inputs) trains on the 2025-26 rows, never HC's history rows")
ck(sum(1 for r in _addon if FM.is_history(r)) == len(_H),
   "🔴 P (HC plus one input) trains on every row HC trains on, its history rows included")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 k KEEPS THE CHAMPION; THE WEEKLY REPORT UNDER HC (NOT APPLICABLE, k, WHAT EACH CHALLENGER READ)")
# ══════════════════════════════════════════════════════════════════════
_res = [{"name": n, "registered": "2026-10-19", "withdrawn": False, "verdict": "NOT APPLICABLE"}
        for n in names("ncaaf") if n != "HC"]
eq(len(_res), 12, "the planted report: the twelve college challengers other than HC")
eq(R.verdicts([dict(x) for x in _res], "HC")[0]["alpha"], 0.01 / 13,
   "🔴 with HC as champion the bar is 0.01 / 13: HC is still one of k")
eq(R.verdicts([dict(x) for x in _res])[0]["alpha"], 0.01 / 12, "   ...(and with no champion passed, 0.01 / 12)")
_T5 = tree()
os.makedirs(os.path.join(_T5, "data", "ncaaf", "latest"))
_got_rows, _attach = {}, FC.attach


def _rec_attach(name, lg, rows, root=None):
    _got_rows[name] = rows
    return rows


try:
    FC.attach = _rec_attach
    with champion("ncaaf", "HC"):
        _doc = R.league("ncaaf", _T5, NOW, rows=_R + _H, prev=None,
                        added={n: "2026-09-01" for n in FC.CHALLENGERS})
finally:
    FC.attach = _attach
_x = {x["name"]: x for x in _doc["challengers"]}
eq(sorted(n for n, x in _x.items() if x["verdict"] == "NOT APPLICABLE"), ["AJC", "ATC", "MCC", "T", "TS"],
   "🔴 under HC: T and ATC are NOT APPLICABLE (Sam's answer), beside TS, MCC and AJC (§4)")
ck(all(not _x[n].get("withdrawn") and not ({"history", "scored", "counted", "withdrawal_window"} & set(_x[n]))
       for n in ("T", "ATC")),
   "🔴 ...so neither is scored at all (no history, scored, counted or withdrawal window), and T, which could be "
   "withdrawn for good, cannot be: there is nothing to withdraw it on", {n: sorted(_x[n]) for n in ("T", "ATC")})
_k = 1 + sum(1 for x in _doc["challengers"] if x["registered"] and not x.get("withdrawn"))
ck(all(x.get("alpha") == 0.01 / _k for x in _doc["challengers"] if x["registered"]) and _k >= 12,
   "🔴 every challenger's bar counts HC: 0.01 / %d" % _k, sorted({x.get("alpha") for x in _doc["challengers"]}))
ck(all(not any(FM.is_history(r) for r in _got_rows[n]) for n in ("SMC",))
   and all(any(FM.is_history(r) for r in _got_rows[n]) for n in ("P", "CLC")),
   "🔴 the weekly report attaches SMC's number to 2025-26 rows only, and P's and CLC's to every row "
   "the champion trains on", {n: sum(1 for r in v if FM.is_history(r)) for n, v in _got_rows.items()})

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 NO SCORED CHALLENGER THROWS THE CHAMPION'S INPUT AWAY (EVERY CHAMPION x EVERY CHALLENGER)")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ S and TS (KEEP) pick the champion's inputs by index: how they should read against another champion
#    is still Sam's to decide (§4), so they are not judged here; H, HC, SM and SMC never read the
#    champion's inputs at all.
_throw, _scored = [], 0
for _lg in ("nfl", "ncaaf"):
    _r = row(random.Random(6), 6, _lg, "2026-10-25", 2026)
    for _ch in [None] + names(_lg):
        with champion(_lg, _ch):
            for _o in names(_lg):
                if _o == _ch or _o in FC.OWN_SCORE or _o in FC.KEEP or not FC.applies(_o, _r):
                    continue
                for _mk in FC.CHALLENGERS[_o]["markets"]:
                    xc, xb = FM.features(_r, _mk), FM.base_features(_r, _mk)
                    xe = FC.extend(_o, _r, _mk, xc)
                    _scored += 1
                    for i in range(len(xc)):
                        if i >= len(xe) or (xe[i] != xc[i] and (i >= len(xb) or xc[i] != xb[i])):
                            _throw.append((_lg, _ch, _o, _mk, i))
ck(_scored > 300, "the matrix is not empty", _scored)
eq(_throw, [], "🔴 every applicable challenger keeps every champion input, or replaces only one that is still "
               "today's (the input it was defined against)")
_na = {(c, o): None for c, o in (("HC", "T"), ("HC", "ATC"), ("SMC", "T"), ("SMC", "ATC"),
                                  ("H", "AT"), ("SM", "AT"), ("MCC", "T"), ("MCC", "TS"))}
for (c, o) in list(_na):
    lg = FC.CHALLENGERS[c]["league"]
    with champion(lg, c):
        _na[(c, o)] = FC.applies(o, row(random.Random(7), 7, lg, "2026-10-25", 2026))
eq(_na, {k: False for k in _na}, "🔴 Sam's cells: T, AT and ATC against H, HC, SM and SMC are NOT APPLICABLE "
                                 "(and T and TS against MCC, the same reason)")
_ok = {}
for (c, o) in (("TS", "T"), ("T", "TS"), ("TS", "ATC"), ("CLC", "T"), ("P", "ATC")):
    with champion("ncaaf", c):
        _ok[(c, o)] = FC.applies(o, row(random.Random(8), 8, "ncaaf", "2026-10-25", 2026))
eq(_ok, {k: True for k in _ok}, "🔴 ...and where the champion still has that input (or the same number), they "
                                 "are scored as before")
with champion("nfl", None), champion("ncaaf", None):
    eq([n for n in FC.CHALLENGERS if not FC.applies(n, row(random.Random(9), 9, FC.CHALLENGERS[n]["league"],
                                                                "2026-10-25", 2026))], [],
       "🔴 against today's model every challenger is scored, as before")

# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 THE CENSUS: A MODULE THAT BUILDS ROWS KEEPS HISTORY ROWS OUT OF WHAT IT SCORES")
# ══════════════════════════════════════════════════════════════════════
# The class: history rows reach a module through `build_rows` (a history champion's) or
# `history_rows`. Every module that calls either must call `is_history` (or be one that only
# builds them). A new one fails here until it does.
BUILDERS = {"fb_challengers.py": "writes history_rows itself (the flag)"}


def _calls(src):
    tree_ = ast.parse(src)
    got = set()
    for n in ast.walk(tree_):
        if isinstance(n, ast.Call):
            f = n.func
            got.add(f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None)
    return got


def census(files):
    out = []
    for p in files:
        try:
            c = _calls(open(p, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        name = os.path.relpath(p, ROOT).replace("\\", "/")
        if c & {"build_rows", "history_rows"} and "is_history" not in c and name not in BUILDERS:
            out.append(name)
    return sorted(out)


_mods = [p for p in glob.glob(os.path.join(ROOT, "*.py")) + glob.glob(os.path.join(ROOT, "research", "*.py"))
         if not os.path.basename(p).startswith("test_")]
_users = sorted(os.path.relpath(p, ROOT).replace("\\", "/") for p in _mods
                if _calls(open(p, encoding="utf-8").read()) & {"build_rows", "history_rows"})
ck(len(_users) >= 6, "the census finds the modules that build rows", _users)
eq(census(_mods), [], "🔴 every module that builds rows or history rows calls is_history")
_T7 = tree()
for _n, _src in (("a.py", "import fb_model as F\nrows = F.build_rows('nfl')\n"),
                 ("b.py", "from fb_model import build_rows\nrows = build_rows('nfl')\n"),
                 ("c.py", "import fb_challengers as FC\nrows = FC.history_rows('nfl')\n"),
                 ("ok.py", "import fb_model as F\nrows = [r for r in F.build_rows('nfl') if not F.is_history(r)]\n")):
    with open(os.path.join(_T7, _n), "w", encoding="utf-8") as fh:
        fh.write(_src)
eq([os.path.basename(x) for x in census(glob.glob(os.path.join(_T7, "*.py")))], ["a.py", "b.py", "c.py"],
   "   ...(planted: a module, a bare import and a history_rows caller are flagged; one that checks is not)")
_T7h = tree()
put(_T7h, "data/nfl/history/schedule-2019.json.gz", {"season": 2019, "games": [
    {"id": "x%d" % i, "season": 2019, "start": "2019-09-%02dT17:00:00Z" % (8 + i), "home": "SEA", "away": "NE",
     "final": True, "home_score": 20 + i, "away_score": 17, "closing_spread": 3.0, "closing_total": 44.5,
     "closing_ml_home": -160, "closing_ml_away": 140} for i in range(4)]})
_hr = FC.history_rows("nfl", _T7h)
ck(len(_hr) == 4 and all(FM.is_history(r) and r["season"] not in FM.SEASONS for r in _hr),
   "🔴 every history row carries the flag (and none is a counted season)", [(r["id"], r.get("history")) for r in _hr])
