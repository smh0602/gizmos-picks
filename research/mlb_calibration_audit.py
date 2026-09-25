"""MLB props card calibration audit -- INVESTIGATION ONLY.

Reads the card's own graded record (data/latest/record-detail.json.gz), joins
every graded row back to the published card it came from (picks/<date>.json,
same order -- collect.py builds the detail by walking card["picks"]), and
answers three questions:

  1. stated confidence vs actual hit rate, 10-point bands, per market,
     with uncertainty CLUSTERED BY GAME (two props in one game share an
     outcome environment, so they are not independent draws);
  2. the ten highest-confidence misses, each re-derived end to end from the
     stored game logs and box scores;
  3. the football structural checks (PR #155 / #158) asked of MLB: thin
     samples printed as near-certain, a stale season, and a board that
     selects the most extreme ratings.

⛔ Changes nothing. Writes one JSON of the numbers beside the doc.
Stdlib only.   python research/mlb_calibration_audit.py
"""
import gzip
import json
import math
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def jload(p):
    if p.endswith(".gz"):
        with gzip.open(p, "rt") as f:
            return json.load(f)
    with open(p) as f:
        return json.load(f)


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


# ---------------------------------------------------------------- join
def load_rows():
    det = jload("data/latest/record-detail.json.gz")["days"]
    rows, mism = [], 0
    for date, drows in sorted(det.items()):
        card = jload(f"picks/{date}.json")
        picks = card.get("picks", [])
        # the grader keeps only pitcher/batter markets it can grade; walk both
        # lists in step, matching on player+market+side+line
        j = 0
        for r in drows:
            while j < len(picks):
                p = picks[j]
                j += 1
                nm = p.get("pitcher") or p.get("player")
                if (nm == r["player"] and p.get("market") == r["market"]
                        and p.get("side") == r["side"] and p.get("line") == r["line"]):
                    break
            else:
                mism += 1
                p = {}
            rows.append(dict(r, date=date, pick=p,
                             cluster=(date, p.get("game_id") or r["game"]),
                             model_version=card.get("model_version")))
    return rows, mism


def market_of(r):
    if r["kind"] == "pitcher":
        return "pitcher_" + r["market"]
    return "hitters"


# ---------------------------------------------------------------- stats
def clustered(rows):
    """Hit rate, mean stated, gap (hit - stated) and its cluster-robust SE.

    The gap's SE sums residuals (won - stated) within each game before
    squaring, with the usual G/(G-1) small-sample factor. `neff` is the
    effective sample size implied by that SE for the hit rate."""
    n = len(rows)
    if not n:
        return None
    hit = sum(1 for r in rows if r["won"]) / n
    st = sum(r["confidence"] for r in rows) / n / 100.0
    gap = hit - st
    by = defaultdict(float)
    byh = defaultdict(float)
    for r in rows:
        e = (1.0 if r["won"] else 0.0) - r["confidence"] / 100.0
        by[r["cluster"]] += e - gap
        byh[r["cluster"]] += (1.0 if r["won"] else 0.0) - hit
    G = len(by)
    if G < MIN_G:
        se = seh = float("nan")
    corr = G / (G - 1) if G > 1 else float("nan")
    if G >= MIN_G:
        se = math.sqrt(corr * sum(v * v for v in by.values())) / n if G > 1 else float("nan")
        seh = math.sqrt(corr * sum(v * v for v in byh.values())) / n if G > 1 else float("nan")
    naive = math.sqrt(hit * (1 - hit) / n) if 0 < hit < 1 else float("nan")
    neff = (hit * (1 - hit) / seh ** 2) if seh and seh == seh and seh > 0 else None
    p_under = norm_sf(-gap / se) if se and se == se and se > 0 else None
    return {"n": n, "games": G, "stated": round(100 * st, 1), "hit": round(100 * hit, 1),
            "gap": round(100 * gap, 1), "se": round(100 * se, 1) if se == se else None,
            "lo": round(100 * (gap - 1.96 * se), 1) if se == se else None,
            "hi": round(100 * (gap + 1.96 * se), 1) if se == se else None,
            "naive_se_hit": round(100 * naive, 1) if naive == naive else None,
            "cluster_se_hit": round(100 * seh, 1) if seh == seh else None,
            "neff": round(neff) if neff else None,
            # one-sided: probability of a gap at least this negative if the
            # card were calibrated (normal approximation on the clustered SE)
            "p_one_sided_running_high": (round(p_under, 4) if p_under is not None and G >= MIN_G else None)}


# fewer games than this and a clustered interval is not worth printing
MIN_G = 10


def band(c):
    b = int(c // 10) * 10
    return f"{b}-{b + 10}" if b < 90 else "90-100"


def table(rows):
    out = {}
    for b in sorted({band(r["confidence"]) for r in rows}):
        out[b] = clustered([r for r in rows if band(r["confidence"]) == b])
    out["ALL"] = clustered(rows)
    return out


def logloss(rows, key):
    s = 0.0
    for r in rows:
        p = min(max(key(r) / 100.0, 1e-4), 1 - 1e-4)
        s += -math.log(p if r["won"] else 1 - p)
    return s / len(rows)


# ---------------------------------------------------------------- traces
def box_actual(date, pid, market):
    R = jload(f"data/{date}/results/final.json.gz")
    for g in R["games"]:
        for p in g.get("pitchers") or []:
            if p["id"] == pid and p.get("started") and market in ("strikeouts", "outs"):
                return p["k"] if market == "strikeouts" else p["outs"], g["state"]
        for b in g.get("batters") or []:
            if b["id"] == pid and market.startswith("batter_"):
                return b, g["state"]
    return None, None


LINEUPS = {}


def load_lineups():
    D = jload("data/latest/lineups.json.gz")
    for d, rws in (D.get("days") or {}).items():
        for x in rws:
            LINEUPS[(int(x["pid"]), d)] = bool(x.get("started"))


def retrace(r, P, H):
    """Recompute the numbers a row printed from the stored logs, point in
    time (games strictly before the card date). Returns a dict of checks."""
    p, out = r["pick"], {}
    line, side = r["line"], r["side"]
    beats = (lambda v: v > line) if side == "over" else (lambda v: v < line)
    if r["kind"] == "pitcher":
        rec = P["players"].get(str(p.get("pid")))
        if not rec:
            return {"note": "pitcher not in latest pull"}
        starts = [g for g in rec["g"] if g.get("gs") and (g.get("d") or "") < r["date"]]
        stat = "k" if r["market"] == "strikeouts" else "outs"
        vals = [g[stat] for g in starts if g.get(stat) is not None]
        h = sum(1 for v in vals if beats(v))
        out["raw_recomputed"] = f"{h}/{len(vals)}"
        out["raw_printed"] = p.get("raw")
        out["last_start_before_card"] = starts[-1]["d"] if starts else None
        out["trail8"] = [g[stat] for g in starts[-8:]]
        out["team_logged"] = rec.get("team")
        out["team_printed"] = p.get("team")
        this = [g for g in rec["g"] if g.get("d") == r["date"]]
        out["log_on_card_date"] = [{k: g.get(k) for k in ("o", "gs", "outs", "k", "np")} for g in this]
        blend_re = 0.5 * (p.get("model") or 0) + 0.5 * (100.0 * h / len(vals) if vals else 0)
        out["blend_recomputed_from_printed_model"] = round(blend_re, 1)
    else:
        rec = H["players"].get(str(p.get("pid")))
        if not rec:
            return {"note": "hitter not in latest pull"}
        field = {"batter_rbis": "rbi", "batter_hits": "H", "batter_total_bases": "tb",
                 "batter_home_runs": "hr"}.get(r["market"])
        prior = [g for g in rec["g"] if (g.get("d") or "") < r["date"]]
        # the collector's own rule (collect.started_game): the real batting
        # order where lineups.json holds it, PA >= 3 only as the fallback
        st3 = [g for g in prior
               if LINEUPS.get((int(p["pid"]), g.get("d")), (g.get("pa") or 0) >= 3)]
        if field:
            vals = [g[field] for g in st3]
        else:
            vals = [g["H"] + g["r"] + g["rbi"] for g in st3]
        h = sum(1 for v in vals if beats(v))
        out["started_record_recomputed"] = f"{h}/{len(vals)}"
        out["record_printed"] = p.get("raw")
        out["games_any_pa_before"] = sum(1 for g in prior if (g.get("pa") or 0) > 0)
        out["lineup_share_printed"] = p.get("lineup_share")
        out["lineup_risk_printed"] = p.get("lineup_risk")
        out["team_logged"] = rec.get("team")
        out["team_printed"] = p.get("team")
        this = [g for g in rec["g"] if g.get("d") == r["date"]]
        out["log_on_card_date"] = [{k: g.get(k) for k in ("o", "pa", "H", "tb", "rbi", "r")} for g in this]
    box, state = box_actual(r["date"], p.get("pid"), r["market"])
    if isinstance(box, dict):
        v = {"batter_rbis": box.get("rbi"), "batter_hits": box.get("h", box.get("H")),
             "batter_total_bases": box.get("tb"), "batter_home_runs": box.get("hr")}.get(r["market"])
        out["box_row"] = {k: box.get(k) for k in box if k not in ("id", "name")}
        out["box_value"] = v
    else:
        out["box_value"] = box
    out["box_game_state"] = state
    out["graded_actual"] = r["actual"]
    return out


# ---------------------------------------------------------------- main
def main():
    rows, mism = load_rows()
    graded = [r for r in rows if r["won"] is not None]
    for r in graded:
        r["mk"] = market_of(r)
    res = {"built_from": "data/latest/record-detail.json.gz joined to picks/<date>.json",
           "graded": len(graded), "voids": sum(1 for r in rows if r["won"] is None),
           "join_mismatches": mism,
           "dates": [min(r["date"] for r in rows), max(r["date"] for r in rows)]}

    # ---- 1. bands
    res["bands"] = {"ALL": table(graded)}
    for mk in ("pitcher_strikeouts", "pitcher_outs", "hitters"):
        res["bands"][mk] = table([r for r in graded if r["mk"] == mk])
    for mk in sorted({r["market"] for r in graded if r["kind"] == "hitter"}):
        res["bands"]["hitters:" + mk] = table([r for r in graded if r["market"] == mk])

    # log loss: printed vs the break-even the price implies (vig included --
    # a conservative stand-in for the market) and, for hitters, the
    # de-vigged market number the card itself stores.
    ll = {}
    for mk in ("pitcher_strikeouts", "pitcher_outs", "hitters"):
        rs = [r for r in graded if r["mk"] == mk and r.get("implied") is not None]
        ll[mk] = {"n": len(rs), "printed": round(logloss(rs, lambda r: r["confidence"]), 4),
                  "price_break_even": round(logloss(rs, lambda r: r["implied"]), 4),
                  "mean_break_even": round(sum(r["implied"] for r in rs) / len(rs), 1),
                  "hit": round(100 * sum(r["won"] for r in rs) / len(rs), 1)}
        dv = [r for r in rs if r["pick"].get("market_implied") is not None]
        if dv:
            ll[mk]["devig_n"] = len(dv)
            ll[mk]["devig_printed"] = round(logloss(dv, lambda r: r["confidence"]), 4)
            ll[mk]["devig_market"] = round(logloss(dv, lambda r: r["pick"]["market_implied"]), 4)
            ll[mk]["devig_mean"] = round(sum(r["pick"]["market_implied"] for r in dv) / len(dv), 1)
    res["log_loss"] = ll

    # pitcher: model half vs raw half, which one carries the miss?
    pit = [r for r in graded if r["kind"] == "pitcher" and r["pick"].get("model") is not None]
    comp = {}
    for mk in ("strikeouts", "outs"):
        rs = [r for r in pit if r["market"] == mk]
        comp[mk] = {"n": len(rs),
                    "mean_model": round(sum(r["pick"]["model"] for r in rs) / len(rs), 1),
                    "mean_raw": round(sum(r["pick"]["raw_pct"] for r in rs) / len(rs), 1),
                    "mean_blend": round(sum(r["pick"]["blend"] for r in rs) / len(rs), 1),
                    "hit": round(100 * sum(r["won"] for r in rs) / len(rs), 1),
                    "ll_model": round(logloss(rs, lambda r: r["pick"]["model"]), 4),
                    "ll_raw": round(logloss(rs, lambda r: min(max(r["pick"]["raw_pct"], 1), 99)), 4),
                    "ll_blend": round(logloss(rs, lambda r: r["pick"]["blend"]), 4),
                    "ll_break_even": round(logloss(rs, lambda r: r["implied"]), 4)}
    res["pitcher_halves"] = comp

    # pitchers by model version and by side; flat-stake return at the
    # printed price (1 unit a play, voids refunded), clustered by game
    def roi(rs):
        by = defaultdict(float)
        tot = 0.0
        for r in rs:
            pr = r["price"]
            win = (pr / 100.0) if pr > 0 else (100.0 / -pr)
            v = win if r["won"] else -1.0
            tot += v
            by[r["cluster"]] += v
        n, G = len(rs), len(by)
        m = tot / n
        se = math.sqrt(G / (G - 1) * sum((v - m * cnt) ** 2 for v, cnt in (
            (by[c], sum(1 for r in rs if r["cluster"] == c)) for c in by))) / n
        return {"n": n, "games": G, "roi_pct": round(100 * m, 1), "se": round(100 * se, 1)}
    extra = {}
    for mk in ("pitcher_strikeouts", "pitcher_outs", "hitters"):
        rs = [r for r in graded if r["mk"] == mk]
        extra[f"{mk}: flat-stake return"] = roi(rs)
        for v in ("v4.0", "v5.0"):
            part = [r for r in rs if r["model_version"] == v]
            if part:
                extra[f"{mk}: {v}"] = clustered(part)
        for sd_ in ("over", "under"):
            part = [r for r in rs if r["side"] == sd_]
            if len(part) >= 10:
                extra[f"{mk}: {sd_}"] = clustered(part)
    res["splits"] = extra

    # ---- 3a. thin samples
    def n_of(r):
        raw = r["pick"].get("raw")
        try:
            return int(str(raw).split("/")[1])
        except Exception:
            return None
    thin = {}
    for kind, cuts in (("pitcher", [(0, 9), (10, 19), (20, 99)]),
                       ("hitter", [(0, 49), (50, 89), (90, 999)])):
        for lo, hi in cuts:
            rs = [r for r in graded if r["kind"] == kind and n_of(r) is not None and lo <= n_of(r) <= hi]
            if rs:
                thin[f"{kind} n={lo}-{hi}"] = clustered(rs)
    rs = [r for r in graded if r["kind"] == "pitcher" and r["pick"].get("raw")
          and r["pick"]["raw"].split("/")[0] == r["pick"]["raw"].split("/")[1]]
    thin["pitcher perfect record (h==n)"] = clustered(rs) if rs else None
    hi80 = [r for r in graded if r["confidence"] >= 80]
    thin["80+ rows: min / median sample"] = {
        k: (min(v), sorted(v)[len(v) // 2]) for k, v in (
            ("pitcher", [n_of(r) for r in hi80 if r["kind"] == "pitcher" and n_of(r)]),
            ("hitter", [n_of(r) for r in hi80 if r["kind"] == "hitter" and n_of(r)])) if v}
    res["thin"] = thin

    # ---- 3b. stale season / stale inputs
    stale = {}
    lag = []
    for d in sorted({r["date"] for r in rows}):
        c = jload(f"picks/{d}.json")
        lag.append((d, c.get("logs_pulled_at"), c.get("odds_pulled_at"), c.get("generated_at"),
                    c.get("model_version")))
    stale["cards"] = lag
    load_lineups()
    P = jload("data/latest/pitchers.json.gz")
    H = jload("data/latest/hitters.json.gz")
    stale["log_seasons"] = {"pitchers": P.get("season"), "hitters": H.get("season")}
    # a pitcher whose most recent start before the card is >20 days old
    # (IL return / role change) -- does the card read a stale form line?
    gaps = []
    for r in graded:
        if r["kind"] != "pitcher":
            continue
        rec = P["players"].get(str(r["pick"].get("pid")))
        if not rec:
            continue
        st = [g["d"] for g in rec["g"] if g.get("gs") and g["d"] < r["date"]]
        if st:
            from datetime import date as _d
            gap = (_d.fromisoformat(r["date"]) - _d.fromisoformat(st[-1])).days
            gaps.append((gap, r))
    long = [r for g, r in gaps if g > 20]
    stale["pitcher rows whose last start was >20 days before the card"] = clustered(long) if long else None
    stale["pitcher rows, last start <=20 days"] = clustered([r for g, r in gaps if g <= 20])
    # hitter: is the last-15 record out of line with the season record he is rated on?
    drift = []
    for r in graded:
        if r["kind"] != "hitter":
            continue
        sp = r["pick"].get("splits") or {}
        l15 = sp.get("last15_pct")
        if l15 is None:
            continue
        drift.append((l15 - (r["pick"].get("rate") or r["confidence"]), r))
    stale["hitter rows where last15 runs >=15 pts BELOW the season rate"] = clustered([r for d, r in drift if d <= -15])
    stale["hitter rows, last15 within 15 pts"] = clustered([r for d, r in drift if -15 < d < 15])
    stale["hitter rows, last15 >=15 pts ABOVE"] = clustered([r for d, r in drift if d >= 15])
    res["stale"] = stale

    # ---- 3c. selection: the board is edge > 0, then top by confidence.
    sel = {}
    for mk in ("pitcher_strikeouts", "pitcher_outs", "hitters"):
        rs = [r for r in graded if r["mk"] == mk and r.get("edge") is not None]
        rs.sort(key=lambda r: r["edge"])
        k = len(rs) // 3
        for name, part in (("low edge third", rs[:k]), ("middle third", rs[k:2 * k]),
                           ("high edge third", rs[2 * k:])):
            c = clustered(part)
            c["mean_edge"] = round(sum(r["edge"] for r in part) / len(part), 1)
            c["mean_break_even"] = round(sum(r["implied"] for r in part) / len(part), 1)
            sel[f"{mk}: {name}"] = c
    # hitters: disagreement with the de-vigged market
    hv = [r for r in graded if r["kind"] == "hitter" and r["pick"].get("market_implied") is not None]
    for lo, hi in ((-99, 5), (5, 15), (15, 99)):
        part = [r for r in hv if lo <= r["confidence"] - r["pick"]["market_implied"] < hi]
        if part:
            c = clustered(part)
            c["mean_devig_market"] = round(sum(r["pick"]["market_implied"] for r in part) / len(part), 1)
            sel[f"hitters: card minus de-vigged market in [{lo},{hi})"] = c
    res["selection"] = sel

    # ---- 2. highest-confidence misses
    misses = sorted([r for r in graded if not r["won"]],
                    key=lambda r: (-r["confidence"], r["date"]))[:10]
    tr = []
    for r in misses:
        p = r["pick"]
        tr.append({
            "date": r["date"], "player": r["player"], "game": r["game"],
            "market": r["market"], "side": r["side"], "line": r["line"],
            "price": r["price"], "book": p.get("book"), "printed": r["confidence"],
            "basis": r.get("confidence_basis") or p.get("confidence_basis"),
            "model": p.get("model"), "raw": p.get("raw"), "raw_pct": p.get("raw_pct"),
            "rate": p.get("rate"), "splits": p.get("splits"),
            "model_inputs": p.get("model_inputs"),
            "lineup_share": p.get("lineup_share"), "lineup_risk": p.get("lineup_risk"),
            "break_even": r.get("implied"), "market_implied": p.get("market_implied"),
            "actual": r["actual"], "retrace": retrace(r, P, H)})
    res["misses"] = tr

    json.dump(res, open("research/mlb_calibration_audit_run_2026-09-24.json", "w"),
              indent=1, default=str)
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: r[k] for k in ("graded", "voids", "join_mismatches", "dates")}))
    for mk, t in r["bands"].items():
        print("\n==", mk)
        for b, c in t.items():
            if c:
                print(f"  {b:7} n={c['n']:4} g={c['games']:3} said {c['stated']:5} hit {c['hit']:5} "
                      f"gap {c['gap']:6} ±{c['se']} [{c['lo']},{c['hi']}] neff={c['neff']} p={c['p_one_sided_running_high']}")
    sys.exit(0)
