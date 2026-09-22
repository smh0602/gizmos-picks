#!/usr/bin/env python3
"""THE PUBLISHED MLB PITCHER TABLE AND OPPONENT TABLE, REBUILT BY THE RUNNER.

    python3 mlb_tables.py [--through YYYY-MM-DD] [--out DIR]

🔴 WHY THIS EXISTS. Both tables used to be rebuilt only by an interactive
browser session running THE RECIPE, so they went stale a slate at a time
(the opponent table was 31 slates and 840 starts behind on 2026-09-21).
Every number in them is a query over `data/latest/pitchers.json.gz`, which
the collector already stores -- so they are rebuilt here, right after the
`pitchers` mode writes that file. Zero network, zero credits. STDLIB ONLY.

DEFINITIONS (Sam's project docs, `mlb-pitcher-database` /
`mlb-opponent-database`) -- STARTS ONLY (`gs == 1`), through the latest
COMPLETED slate:

  pitcher table   name|hand|n|mK|mK8|mO|mO8|cvK|cvO|mNP|tail
    n        season starts;  only n >= 8 is published
    mK / mO  season mean strikeouts / outs
    mK8/mO8  mean over the last 8 starts
    cvK/cvO  sample SD (n-1) / mean
    mNP      mean pitches per start (int)
    tail     share of starts with outs more than 2 sample SDs below own mean
  opponent table  team|n|meanK|ΔE[K]|mean outs allowed
    n        starts faced;  meanK = mean K by the opposing starter
    ΔE[K]    (meanK - C) * K_OPP_B, C = league mean starter K over the SAME
             population, K_OPP_B read from card.py (never restated here)

🔴🔴 THE POPULATION IS EVERY STARTER, NOT THE MODEL POOL. The published
opponent table counts every start a team faced. `collect.py` therefore
pulls starters under the 20-IP bar too, marked `below_min_ip`; `card.py`
excludes them (its own opponent term is unchanged) and THIS module
includes them. ⛔ It refuses to build when the pull says the starter pool
is not complete -- an IP-filtered table under a full-population label is
the exact mis-scaling the opponent doc warns about.

⛔ DESCRIPTIVE, NOT MODEL. These are tables of what happened. Nothing here
feeds `blend`, a band, a probability or a pair, and nothing is written
into `picks/`.
"""
import argparse
import datetime
import decimal
import gzip
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

MIN_N = 8          # published only at n >= 8 (mlb-pitcher-database)
TRAIL = 8          # mK8 / mO8 window
ARTIFACTS = ("pitcher-table.json", "pitcher-table.md",
             "opponent-table.json", "opponent-table.md")


def _slope():
    # 🔴 THE SHIPPED SLOPE, FROM THE ONE PLACE IT LIVES. The docs quote
    # 0.575 (v4.0); card.py ships its re-fit. A second copy here would be
    # the same defect as two copies of a coefficient.
    from card import K_OPP_B
    return K_OPP_B


def _abbr():
    from card import ABBR
    return ABBR


def _utc(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc)


def latest_completed_slate(pulled_at):
    """The ET date BEFORE the pull's ET date. A 06:00 ET pull holds last
    night's finals; a mid-slate re-pull holds half of today's, and a half
    slate is not a completed one. (ET fixed at -4, as freshness.et_date.)"""
    et = _utc(pulled_at) - datetime.timedelta(hours=4)
    return (et.date() - datetime.timedelta(days=1)).isoformat()


def load(path, allow_incomplete=False):
    """⚠️ `allow_incomplete` exists for the CLI demo and the 8/20 reproduction
    test ONLY (the n >= 8 pitcher rows do not depend on the low-IP starters).
    ⛔ The collector never passes it, and a doc built with it says so in
    `population_complete: false` and in its markdown headline."""
    D = json.load(gzip.open(path, "rt", encoding="utf-8"))
    pool = D.get("starter_pool")
    if pool != "complete" and not allow_incomplete:
        raise RuntimeError(
            "pitchers.json.gz does not carry the complete starter pool "
            f"(starter_pool={pool!r}) -- refusing to build a full-population "
            "table from an IP-filtered pull")
    return D


def starts(D, through):
    """pid -> {name, throws, rows (oldest first)}: starts dated <= through."""
    out = {}
    for pid, p in D["players"].items():
        rows = [r for r in p.get("g") or []
                if r.get("gs") == 1 and (r.get("d") or "") <= through]
        if not rows:
            continue
        bad = [r for r in rows if r.get("k") is None or r.get("outs") is None
               or not r.get("o")]
        if bad:
            raise ValueError(f"{p.get('name')}: {len(bad)} start(s) with no K/outs/opponent")
        rows.sort(key=lambda r: r["d"])
        out[str(pid)] = {"name": p["name"], "throws": p.get("throws"), "rows": rows}
    return out


def pitcher_rows(S):
    tab = []
    for pid, s in S.items():
        rows = s["rows"]
        n = len(rows)
        if n < MIN_N:
            continue
        K = [r["k"] for r in rows]
        O = [r["outs"] for r in rows]
        NP = [r["np"] for r in rows if r.get("np") is not None]
        mK, mO = st.mean(K), st.mean(O)
        sK, sO = st.stdev(K), st.stdev(O)          # sample SD, n-1
        tab.append({
            "id": pid, "name": s["name"], "hand": s["throws"] or "?", "n": n,
            "mK": mK, "mK8": st.mean(K[-TRAIL:]), "mO": mO, "mO8": st.mean(O[-TRAIL:]),
            "cvK": (sK / mK) if mK else None, "cvO": (sO / mO) if mO else None,
            "mNP": int(_half_up(st.mean(NP))) if NP else None,
            "tail": sum(1 for o in O if o < mO - 2 * sO) / n})
    tab.sort(key=lambda r: (-round(r["mK"], 2), r["name"]))
    return tab


def opponent_rows(S, slope):
    ab = _abbr()
    opp = {}
    for s in S.values():
        for r in s["rows"]:
            opp.setdefault(r["o"], []).append(r)
    N = sum(len(v) for v in opp.values())
    if not N:
        raise ValueError("no starts in the population")
    C = sum(r["k"] for v in opp.values() for r in v) / N
    tab = []
    for t, v in opp.items():
        mk = st.mean(r["k"] for r in v)
        tab.append({"team": ab.get(t, t), "team_name": t, "n": len(v), "meanK": mk,
                    "dEK": (mk - C) * slope, "meanO": st.mean(r["outs"] for r in v)})
    tab.sort(key=lambda r: (-r["meanK"], r["team"]))
    return tab, C, N


def _half_up(x, dp=0):
    """ROUND HALF UP, as the published tables print (9.125 -> 9.13, 94.5 ->
    95). ⛔ Not `round()`/`%.2f`: both round half to EVEN on these exact
    eighths and disagree with the published row."""
    q = decimal.Decimal(1).scaleb(-dp)
    return decimal.Decimal(repr(x)).quantize(q, rounding=decimal.ROUND_HALF_UP)


def _f(x, dp):
    if x is None:
        return "—"
    s = str(_half_up(x, dp))
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def build(path, through=None, built_at=None, allow_incomplete=False):
    """-> (pitcher_doc, opponent_doc). Pure: reads `path`, writes nothing."""
    D = load(path, allow_incomplete)
    through = through or latest_completed_slate(D["pulled_at"])
    S = starts(D, through)
    if not S:
        raise ValueError(f"no starts through {through}")
    last = max(r["d"] for s in S.values() for r in s["rows"])
    slope = _slope()
    ptab = pitcher_rows(S)
    otab, C, N = opponent_rows(S, slope)
    built_at = built_at or datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    head = {
        "through": through, "last_start_date": last,
        "population_starts": N, "population_starters": len(S),
        "centering_constant": round(C, 4),
        "source": "data/latest/pitchers.json.gz",
        "source_pulled_at": D["pulled_at"], "built_at": built_at,
        "starter_pool": D.get("starter_pool"),
        "population_complete": D.get("starter_pool") == "complete",
        "label": "DESCRIPTIVE",
        "note": ("Starts only (gamesStarted == 1), every starter the season pool "
                 "returns -- including those under the model's 20-IP bar. "
                 "Descriptive: nothing here enters the model's probabilities."),
    }
    pdoc = dict(head, kind="mlb-pitcher-table", min_n=MIN_N, trail_n=TRAIL,
                columns=["name", "hand", "n", "mK", "mK8", "mO", "mO8", "cvK", "cvO",
                         "mNP", "tail"],
                rows=len(ptab), sum_n=sum(r["n"] for r in ptab), pitchers=ptab)
    odoc = dict(head, kind="mlb-opponent-table", slope=slope,
                slope_source="card.py K_OPP_B",
                columns=["team", "n", "meanK", "dEK", "meanO"],
                rows=len(otab), sum_n=N, opponents=otab)
    return pdoc, odoc


def _warn(doc):
    if doc["population_complete"]:
        return []
    return [f"⚠️ **POPULATION INCOMPLETE** (`starter_pool`: {doc['starter_pool']!r}) — "
            "built from an IP-filtered pull; starters under 20 IP are missing.", ""]


def render_pitchers_md(doc):
    out = [f"# MLB pitcher table — through {doc['through']}", ""] + _warn(doc) + [
           f"Built {doc['built_at']} from `{doc['source']}` (pulled "
           f"{doc['source_pulled_at']}). DESCRIPTIVE. Starts only; n >= {doc['min_n']} "
           f"published: **{doc['rows']} pitchers, {doc['sum_n']} starts** "
           f"(population {doc['population_starts']} starts).", "",
           "name|hand|n|mK|mK8|mO|mO8|cvK|cvO|mNP|tail",
           "---|---|---|---|---|---|---|---|---|---|---"]
    for r in doc["pitchers"]:
        out.append("|".join([r["name"], r["hand"], str(r["n"]), _f(r["mK"], 2),
                             _f(r["mK8"], 2), _f(r["mO"], 2), _f(r["mO8"], 2),
                             _f(r["cvK"], 3), _f(r["cvO"], 3),
                             "—" if r["mNP"] is None else str(r["mNP"]), _f(r["tail"], 3)]))
    return "\n".join(out) + "\n"


def render_opponents_md(doc):
    out = [f"# MLB opponent table — through {doc['through']}", ""] + _warn(doc) + [
           f"Built {doc['built_at']} from `{doc['source']}` (pulled "
           f"{doc['source_pulled_at']}). DESCRIPTIVE. **{doc['population_starts']} starts**, "
           f"centering constant **C = {doc['centering_constant']:.4f}**, "
           f"ΔE[K] = (meanK − C) × {doc['slope']} ({doc['slope_source']}).", "",
           "team|n|meanK|ΔE[K]|mean outs allowed", "---|---|---|---|---"]
    for r in doc["opponents"]:
        d = _half_up(r["dEK"], 2)
        out.append(f"{r['team']}|{r['n']}|{_half_up(r['meanK'], 2)}|"
                   f"{'+' if d >= 0 else ''}{d}|{_half_up(r['meanO'], 2)}")
    return "\n".join(out) + "\n"


def _atomic_text(path, text):
    tmp = f"{path}.tmp.{os.getpid()}"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _refuse_picks(out_dir):
    # ⛔ `picks/` is the permanent published record. A descriptive table
    # has no business there, whatever directory a caller passes.
    parts = os.path.normpath(os.path.abspath(out_dir)).split(os.sep)
    if "picks" in parts:
        raise ValueError(f"refusing to write MLB tables into {out_dir}: picks/ is the record")


def write_all(latest, source=None, through=None, allow_incomplete=False):
    """Build both tables from `<latest>/pitchers.json.gz` and write the four
    artifacts into `latest`. -> (pitcher_doc, opponent_doc)."""
    _refuse_picks(latest)
    pdoc, odoc = build(source or os.path.join(latest, "pitchers.json.gz"), through,
                       allow_incomplete=allow_incomplete)
    import collect as _c              # the ONE atomic, stamping JSON writer
    _c.write(os.path.join(latest, "pitcher-table.json"), pdoc)
    _c.write(os.path.join(latest, "opponent-table.json"), odoc)
    _atomic_text(os.path.join(latest, "pitcher-table.md"), render_pitchers_md(pdoc))
    _atomic_text(os.path.join(latest, "opponent-table.md"), render_opponents_md(odoc))
    print(f"[mlb_tables] through {pdoc['through']}: pitcher table {pdoc['rows']} rows "
          f"sum(n) {pdoc['sum_n']}; opponent table {odoc['rows']} teams, "
          f"{odoc['population_starts']} starts, C {odoc['centering_constant']}", flush=True)
    return pdoc, odoc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--through")
    ap.add_argument("--out", default=os.path.join("data", "latest"))
    ap.add_argument("--source")
    ap.add_argument("--allow-incomplete", action="store_true",
                    help="build from an IP-filtered pull; the output SAYS it is incomplete")
    a = ap.parse_args(argv)
    write_all(a.out, a.source, a.through, a.allow_incomplete)


if __name__ == "__main__":
    main()
