"""T34 -- does Poisson fit hitter markets? Bar fixed in t34_spec.md."""
import gzip, json, math, statistics, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import card as C

H = json.load(gzip.open('data/latest/hitters.json.gz', 'rt'))
pl = H.get("players", H)
try:
    L = json.load(gzip.open('data/latest/lineups.json.gz', 'rt'))
except Exception:
    L = None

MK = {"batter_hits": ("H", "hits", (0.5, 1.5, 2.5)),
      "batter_total_bases": ("tb", "total bases", (0.5, 1.5, 2.5, 3.5)),
      "batter_home_runs": ("hr", "home runs", (0.5, 1.5)),
      "batter_rbis": ("rbi", "RBIs", (0.5, 1.5, 2.5)),
      "batter_hits_runs_rbis": (None, "H+R+RBI", (0.5, 1.5, 2.5, 3.5))}

def started(g):
    return (g.get("pa") or 0) >= 3          # documented fallback, CLAUDE.md

def val(g, key):
    if key is None:
        return (g.get("H") or 0) + (g.get("r") or 0) + (g.get("rbi") or 0)
    return g.get(key) or 0

def nb_invert(line, p_over, mean_hint, var):
    """Negative binomial matched to an observed variance > mean.
    Solve for the mean m whose NB(m, var-shape) gives P(X > line) = p_over.
    Shape r is held at the value implied by the OBSERVED mean and variance,
    so the distribution keeps the player's own dispersion."""
    if var <= mean_hint or mean_hint <= 0:
        return C.invert_poisson(line, p_over)
    r = mean_hint * mean_hint / (var - mean_hint)     # NB size

    def sf(m):
        p = r / (r + m)
        k = int(math.floor(line))
        term = p ** r
        cdf = term
        for i in range(1, k + 1):
            term *= (r + i - 1) / i * (1 - p)
            cdf += term
        return 1.0 - min(1.0, cdf)

    lo, hi = 1e-4, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if sf(mid) < p_over: lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)

res = {}
for mkt, (key, label, lines) in MK.items():
    pois, nb = [], []
    for pid, p in pl.items():
        gs = [g for g in (p.get("g") or []) if started(g)]
        if len(gs) < 25:
            continue
        vals = [val(g, key) for g in gs]
        n = len(vals)
        xbar = sum(vals) / n
        var = statistics.variance(vals)
        for line in lines:
            h = sum(1 for v in vals if v > line)
            if h < 3 or h > n - 3:        # a 0% or 100% rate inverts to a bound
                continue
            phat = h / n
            pois.append(C.invert_poisson(line, phat) - xbar)
            nb.append(nb_invert(line, phat, xbar, var) - xbar)
    res[label] = (pois, nb)

def q90(xs):
    a = sorted(abs(x) for x in xs)
    return a[int(0.9 * (len(a) - 1))] if a else float('nan')

print(f"{'market':14} {'n':>6}  {'POISSON mean':>12} {'p90|d|':>7}  {'verdict':9}"
      f"   {'NB mean':>8} {'p90|d|':>7}  {'verdict':9}")
verdicts = {}
for label, (pois, nb) in res.items():
    if not pois:
        continue
    mp, qp = statistics.mean(pois), q90(pois)
    mn, qn = statistics.mean(nb), q90(nb)
    vp = "PASS" if abs(mp) < 0.10 and qp < 0.25 else "FAIL"
    vn = "PASS" if abs(mn) < 0.10 and qn < 0.25 else "FAIL"
    verdicts[label] = (vp, vn)
    print(f"{label:14} {len(pois):>6}  {mp:>+12.4f} {qp:>7.3f}  {vp:9}"
          f"   {mn:>+8.4f} {qn:>7.3f}  {vn:9}")
print()
for label, (vp, vn) in verdicts.items():
    win = "poisson" if vp == "PASS" else ("negbin" if vn == "PASS" else "NEITHER")
    print(f"  {label:14} -> {win}")
