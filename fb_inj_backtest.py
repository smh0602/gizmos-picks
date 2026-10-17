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
    """(log losses without, with, the weekly fits, how many scored questions the injuries MOVED):
    the smooth curve at each final game's main closing spread and total, from the score without
    and with injuries."""
    weeks = collections.defaultdict(list)
    for r in rows:
        weeks[F.monday(r["day"])].append(r)
    N = statistics.NormalDist()
    ll = {"without": [], "with": []}
    fits = []
    moved = 0
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
                ps = {}
                for tag, sc in scs.items():
                    h, a = float(sc["home"]), float(sc["away"])
                    mu, s = ((h - a), sigma) if mk == "spread" else ((h + a), sigma_t)
                    p = min(1 - 1e-6, max(1e-6, N.cdf((mu - ln) / s)))
                    ps[tag] = p
                    ll[tag].append(-(y * math.log(p) + (1 - y) * math.log(1 - p)))
                if ps["with"] != ps["without"]:
                    moved += 1
    return ll, fits, moved


def returns(F, rows, lg, on):
    """{books|closing: profit per bet in %} of the walk-forward record's spread + total picks."""
    F.INJURIES[lg] = on
    wf = F.walk_forward(rows)
    out = {}
    for name in ("books", "closing"):
        ps = [p for mk in ("spread", "total") for p in wf[name][mk]]
        units = sum((F.decimal(p["price"]) - 1.0) if p["won"] else (0.0 if p["won"] is None else -1.0)
                    for p in ps)
        out[name] = 100.0 * units / len(ps) if ps else None      # ⛔ unrounded: the bar is decided on it
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
        ll, fits, moved = logloss_pair(F, rows, lg)
        off, on = returns(F, rows, lg, False), returns(F, rows, lg, True)
    finally:
        F.INJURIES.clear()
        F.INJURIES.update(saved)
    lle = {k: statistics.mean(v) if v else None for k, v in ll.items()}
    r2 = lambda x: None if x is None else round(x, 2)  # noqa: E731
    return {"questions": len(ll["with"]), "questions_moved": moved, "rows_with_injury_reading": n_inj,
            "logloss": {k: None if v is None else round(v, 5) for k, v in lle.items()},
            "closing_return": {"without": r2(off["closing"]), "with": r2(on["closing"])},
            "books_return": {"without": r2(off["books"]), "with": r2(on["books"])},
            # `[2026-10-17, review]` the bar is decided on these, never on the rounded display
            "exact": {"logloss": lle, "closing_return": {"without": off["closing"], "with": on["closing"]}},
            "fitted_last": list(fits[-1]) if fits else None,
            "seconds": round(time.time() - t0)}


def passes(entry):
    """The bar: log loss with <= without AND closing return with >= without, on the EXACT numbers
    where the entry carries them (`[2026-10-17, review]`: a slightly worse "with" must not tie
    after rounding), else the recorded ones (the NFL's entry, which fails by a clear margin)."""
    ex = entry.get("exact") or {}
    ll = ex.get("logloss") or entry.get("logloss") or {}
    cr = ex.get("closing_return") or entry.get("closing_return") or {}
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


# ══════════════════════════════════════════════════════════════════════
# 🔴 IT RUNS ITSELF. `[Sam, 2026-10-17]` "nothing running in Claude": the weekly fb-refit job
# (fb_refit.weekly, Mondays) calls `auto` per league. ONCE the data the bar needs is stored, it
# measures, keeps the result in data/<lg>/latest/fb-refit.json, and pushes ONE branch for Sam that
# records the entry in research/fb_sim_backtest.json and, only when it passes, switches
# fb_model.INJURIES[lg] on. ⛔ Never main, never a PR, never a second measurement: the first
# measured result stands until the record reaches main.
# ══════════════════════════════════════════════════════════════════════
def needed(lg, root=ROOT, now=None):
    """The stored data the bar needs before it may run (design §1): college, both seasons' defence
    and roster logs and injury archives, and in each archive every conference that gives a
    pick-time reading, none of them still owed a refresh. -> [what is missing]."""
    if lg != "ncaaf":
        return []
    import cfb_injuries as CI
    import freshness
    cur = freshness.current_football_season(now)
    lat = os.path.join(root, "data", "ncaaf", "latest")
    his = os.path.join(root, "data", "ncaaf", "history")
    want = [os.path.join(lat, "%s-%d.json.gz" % (k, s)) for s in (cur - 1, cur) for k in ("defense", "roster")]
    want += [os.path.join(his, "injury-archive-%d.json.gz" % s) for s in (cur - 1, cur)]
    rel = lambda p: os.path.relpath(p, root).replace(os.sep, "/")  # noqa: E731
    out = [rel(p) for p in want if not os.path.exists(p)]
    # `[2026-10-17, review]` ⛔ A FILE IS NOT A SEASON: an archive that answered for some
    #    conferences only would make the one measurement without the rest.
    try:
        with open(CI.probe_path(cur, root), encoding="utf-8") as fh:
            owed = json.load(fh).get("archives") or {}
    except (OSError, ValueError):
        owed = {}
    for s in (cur - 1, cur):
        have = (CI._jz(CI.archive_path(s, root)) or {}).get("conferences") or {}
        for c in (CI.HDI_LEGACY if s == CI.LEGACY_SEASON else CI.HDI_ARCHIVE):
            if CI.night_before(s, c) and (c not in have or ((owed.get(str(s)) or {}).get(c) or {}).get("due")):
                out.append("%s#%s" % (rel(CI.archive_path(s, root)), c))
    return out


def set_injuries(src, lg):
    """fb_model.py's source with INJURIES[lg] switched on. ⛔ Exactly one switch line, or it raises."""
    import re
    pat = re.compile(r'^(INJURIES = \{[^\n]*"%s": )False' % lg, re.M)
    if len(pat.findall(src)) != 1:
        raise RuntimeError("INJURIES line for %s not found once in fb_model.py" % lg)
    return pat.sub(r"\g<1>True", src)


def auto(lg, root=ROOT, now=None, run=None, prev=None):
    """-> the state fb-refit.json keeps under "injury_backtest": recorded / waiting / measured."""
    import datetime
    import subprocess
    now = now or datetime.datetime.now(datetime.timezone.utc)
    run = run or subprocess.run
    rec = (json.load(open(os.path.join(root, "research", "fb_sim_backtest.json"), encoding="utf-8"))
           .get("injuries") or {})
    if lg in rec:
        return {"state": "recorded", "passes": passes(rec[lg]), "entry": rec[lg]}
    if prev and prev.get("state") == "measured" and prev.get("entry"):
        st = dict(prev)                    # ⛔ ONCE: the first measured result stands
    else:
        # `[2026-10-17, review]` ⛔ ...and a result already on a branch is never measured again,
        #    even if last week's fb-refit.json never landed: the branch's own entry is the result.
        import fb_refit
        try:
            branch, text = fb_refit.branch_file("fb/injuries-%s-" % lg, "research/fb_sim_backtest.json", root, run)
        except Exception as e:
            return {"state": "waiting", "why": "could not ask origin for an injury branch (%s: %s)"
                    % (type(e).__name__, e), "checked_at": now.strftime("%Y-%m-%dT%H:%MZ")}
        if branch:
            e0 = ((json.loads(text or "{}").get("injuries") or {}).get(lg))
            if not e0:
                return {"state": "waiting", "branch": branch,
                        "why": "the branch %s holds no injuries.%s entry" % (branch, lg)}
            return {"state": "measured", "entry": e0, "passes": passes(e0), "branch": branch,
                    "branch_pushed": False, "measured_at": now.strftime("%Y-%m-%dT%H:%MZ")}
        missing = needed(lg, root, now)
        if missing:
            return {"state": "waiting", "missing": missing, "checked_at": now.strftime("%Y-%m-%dT%H:%MZ")}
        entry = measure(lg, root)
        if not entry.get("fitted_last") or not entry.get("questions_moved"):
            # ⛔ NO FIT, NO TEST: too few games carry a reading to size an injury (or the only fits
            #    are for weeks not yet played), so no scored question moves, "with" equals "without"
            #    and would pass while proving nothing. Not recorded; asked again next week.
            return {"state": "waiting", "why": "too few injury readings to fit (%s rows, %s questions "
                    "moved)" % (entry.get("rows_with_injury_reading"), entry.get("questions_moved")),
                    "checked_at": now.strftime("%Y-%m-%dT%H:%MZ")}
        st = {"state": "measured", "entry": entry, "passes": passes(entry),
              "measured_at": now.strftime("%Y-%m-%dT%H:%MZ")}
    if st.get("branch"):
        return st
    import fb_refit

    def edit(tree):
        record(lg, st["entry"], os.path.join(tree, "research", "fb_sim_backtest.json"))
        if st["passes"]:
            p = os.path.join(tree, "fb_model.py")
            src = open(p, encoding="utf-8").read()
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(set_injuries(src, lg))
    try:
        st["branch"], st["branch_pushed"] = fb_refit.push_change(
            "fb/injuries-%s-" % lg, "fb/injuries-%s-%s" % (lg, now.strftime("%Y-%m-%d")), edit,
            "fb: %s injuries %s the test fixed in advance — %s for Sam" % (
                lg, "PASSED" if st["passes"] else "FAILED",
                "switch on" if st["passes"] else "record only, they stay off"), root, run)
        st.pop("branch_error", None)
    except Exception as e:
        st["branch_error"] = "%s: %s" % (type(e).__name__, e)
    return st


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
