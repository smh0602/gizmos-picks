"""T35 -- compound Poisson for total bases. Bar = T34's bar, fixed before run."""
import gzip, json, math, statistics, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

H = json.load(gzip.open('data/latest/hitters.json.gz', 'rt'))
pl = H.get("players", H)
MAXTB = 30

def compound_pmf(lam_h, mix):
    """P(TB = t) when hits ~ Poisson(lam_h) and each hit is worth 1..4
    bases with probabilities `mix`. Convolve, one hit at a time."""
    # dist over TB given exactly j hits, built by repeated convolution
    pmf = [0.0] * (MAXTB + 1)
    cur = [0.0] * (MAXTB + 1); cur[0] = 1.0          # j = 0
    term = math.exp(-lam_h)
    for j in range(0, 26):
        for t in range(MAXTB + 1):
            if cur[t]: pmf[t] += term * cur[t]
        nxt = [0.0] * (MAXTB + 1)
        for t in range(MAXTB + 1):
            if not cur[t]: continue
            for b in (1, 2, 3, 4):
                if t + b <= MAXTB: nxt[t + b] += cur[t] * mix[b - 1]
        cur = nxt
        term *= lam_h / (j + 1)
    return pmf

def sf(lam_h, mix, line):
    pmf = compound_pmf(lam_h, mix)
    k = int(math.floor(line))
    return 1.0 - sum(pmf[:k + 1])

def invert(line, p_over, mix):
    lo, hi = 1e-4, 12.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if sf(mid, mix, line) < p_over: lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)

d = []
for pid, p in pl.items():
    gs = [g for g in (p.get("g") or []) if (g.get("pa") or 0) >= 3]
    if len(gs) < 25: continue
    tb = [g.get("tb") or 0 for g in gs]
    hh = [g.get("H") or 0 for g in gs]
    hr = sum(g.get("hr") or 0 for g in gs)
    nh = sum(hh); ntb = sum(tb)
    if nh < 10: continue
    # base mix from his OWN season: solve singles/doubles/triples from H, TB, HR
    # TB = 1B + 2*2B + 3*3B + 4*HR ; we have H, TB, HR but not 2B/3B split.
    # Distribute the surplus over singles across 2B/3B at the league 9:1 ratio.
    extra = ntb - nh - 3 * hr                    # bases above 1-per-hit, non-HR
    if extra < 0: continue
    xb = extra / 1.18                            # 2B worth +1, 3B worth +2, 9:1
    n2 = xb * 0.9; n3 = xb * 0.1 / 1.0
    n1 = nh - n2 - n3 - hr
    if n1 < 0: continue
    mix = [n1 / nh, n2 / nh, n3 / nh, hr / nh]
    s = sum(mix); mix = [m / s for m in mix]
    xbar = sum(tb) / len(tb)
    n = len(tb)
    for line in (0.5, 1.5, 2.5, 3.5):
        h = sum(1 for v in tb if v > line)
        if h < 3 or h > n - 3: continue
        lam_h = invert(line, h / n, mix)
        implied = lam_h * sum((i + 1) * mix[i] for i in range(4))   # E[TB]
        d.append(implied - xbar)

def q90(xs):
    a = sorted(abs(x) for x in xs); return a[int(0.9 * (len(a) - 1))]
m, q = statistics.mean(d), q90(d)
ok = abs(m) < 0.10 and q < 0.25
print(f"total bases, compound Poisson:  n={len(d)}  mean {m:+.4f}  p90|d| {q:.3f}"
      f"   {'PASS' if ok else 'FAIL'}  (bar |mean|<0.10, p90<0.25)")
print(f"  for comparison -- plain Poisson p90 was 0.673, negative binomial 0.350")
