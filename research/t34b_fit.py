"""T34b -- can the observed per-game mean serve as the TB / H+R+RBI
projection? Bar fixed in t34_spec.md BEFORE this was run."""
import gzip, json, statistics, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

H = json.load(gzip.open('data/latest/hitters.json.gz', 'rt'))
pl = H.get("players", H)
MK = {"total bases": ("tb", (0.5, 1.5, 2.5, 3.5)),
      "H+R+RBI": (None, (0.5, 1.5, 2.5, 3.5))}

def val(g, key):
    if key is None:
        return (g.get("H") or 0) + (g.get("r") or 0) + (g.get("rbi") or 0)
    return g.get(key) or 0

for label, (key, lines) in MK.items():
    tot = on = 0; misses = []
    for pid, p in pl.items():
        gs = [g for g in (p.get("g") or []) if (g.get("pa") or 0) >= 3]
        if len(gs) < 25: continue
        vals = [val(g, key) for g in gs]
        n = len(vals); xbar = sum(vals) / n
        for line in lines:
            h = sum(1 for v in vals if v > line)
            for side, hit in (("over", h), ("under", n - h)):
                rate = 100.0 * (hit + 0.5) / (n + 1)      # the card's Jeffreys rate
                if rate < 60: continue
                tot += 1
                ok = (xbar > line) if side == "over" else (xbar < line)
                if ok: on += 1
                else: misses.append((p["name"], side, line, round(rate), round(xbar, 2)))
    pct = 100.0 * on / tot if tot else float('nan')
    print(f"{label:12}  {on}/{tot} = {pct:.2f}%   "
          f"{'PASS' if pct >= 97.0 else 'FAIL'}  (bar 97%)")
    from collections import Counter
    print("   misses by side:", Counter(m[1] for m in misses))
    for m in misses[:5]: print("   ", m)
    print()
