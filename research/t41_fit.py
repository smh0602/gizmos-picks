#!/usr/bin/env python3
"""T41 — receptions, with injury/depth information. Fits EXACTLY the spec in
research/t41_spec.md, which was written and committed BEFORE this ran."""
import json, gzip, math, statistics, collections

TRAIL, MIN_PRIOR = 8, 6
FIT_MAX_WK, TEST_MIN_WK = 13, 14
POS = {"WR", "TE", "RB"}
D = json.load(gzip.open("players-2025.json.gz", "rt"))["players"]

opp_hist = collections.defaultdict(list)
for p in D.values():
    if p["pos"] in POS:
        for g in p["g"]:
            if g["o"]:
                opp_hist[(g["o"], p["pos"])].append((g["week"], g["rec"]))

def opp_allowed(opp, pos, week):
    v = [y for w, y in opp_hist[(opp, pos)] if w < week]
    return statistics.mean(v) if len(v) >= 8 else None

def mean(x): return statistics.mean(x) if x else None

rows = []
for pid, p in D.items():
    if p["pos"] not in POS: continue
    gs = p["g"]
    for i, g in enumerate(gs):
        prior = gs[:i]
        if len(prior) < MIN_PRIOR: continue
        t8 = prior[-TRAIL:]
        recs = [x["rec"] for x in t8]
        oa = opp_allowed(g["o"], p["pos"], g["week"])
        if oa is None: continue
        rows.append({
            "pid": pid, "pos": p["pos"], "wk": g["week"], "y": g["rec"],
            "tgt": mean([x["tgt"] for x in t8]),
            "snap": mean([x.get("snap_pct", 0.0) for x in t8]),
            "oa": oa,
            "ahead_out": float(g.get("ahead_out", 0)),
            "own_status": float(g.get("inj", 0)),
            "naive1": mean(recs),
            "naive2": mean([x["rec"] for x in prior]),
            "line": statistics.median(recs),
        })
fit = [r for r in rows if r["wk"] <= FIT_MAX_WK]
test = [r for r in rows if r["wk"] >= TEST_MIN_WK]
print(f"rows {len(rows):,}  fit {len(fit):,}  test {len(test):,}")
print(f"ahead_out>0 in fit {sum(1 for r in fit if r['ahead_out']):,} | "
      f"test {sum(1 for r in test if r['ahead_out']):,}")

FEAT = ["tgt", "snap", "oa", "ahead_out", "own_status"]
def design(rs): return [[1.0]+[float(r[f]) for f in FEAT] for r in rs], [r["y"] for r in rs]
def solve(X, y):
    n = len(X[0])
    A=[[sum(X[k][i]*X[k][j] for k in range(len(X))) for j in range(n)] for i in range(n)]
    b=[sum(X[k][i]*y[k] for k in range(len(X))) for i in range(n)]
    for i in range(n):
        pv=max(range(i,n),key=lambda r:abs(A[r][i])); A[i],A[pv]=A[pv],A[i]; b[i],b[pv]=b[pv],b[i]
        for r in range(i+1,n):
            f=A[r][i]/A[i][i]
            for c in range(i,n): A[r][c]-=f*A[i][c]
            b[r]-=f*b[i]
    x=[0.0]*n
    for i in reversed(range(n)):
        x[i]=(b[i]-sum(A[i][j]*x[j] for j in range(i+1,n)))/A[i][i]
    return x
X, y = design(fit); beta = solve(X, y)

n_obs,k=len(X),len(beta)
resid=[y[i]-sum(b*X[i][j] for j,b in enumerate(beta)) for i in range(n_obs)]
s2=sum(r*r for r in resid)/(n_obs-k)
A=[[sum(X[m][i]*X[m][j] for m in range(n_obs)) for j in range(k)] for i in range(k)]
I=[[1.0 if i==j else 0.0 for j in range(k)] for i in range(k)]
for i in range(k):
    pv=max(range(i,k),key=lambda r:abs(A[r][i])); A[i],A[pv]=A[pv],A[i]; I[i],I[pv]=I[pv],I[i]
    dd=A[i][i]; A[i]=[v/dd for v in A[i]]; I[i]=[v/dd for v in I[i]]
    for r in range(k):
        if r!=i:
            f=A[r][i]; A[r]=[a-f*b for a,b in zip(A[r],A[i])]; I[r]=[a-f*b for a,b in zip(I[r],I[i])]
print("\ncoefficients:")
for nm,b,v in zip(["intercept"]+FEAT, beta, [I[i][i] for i in range(k)]):
    se=math.sqrt(max(s2*v,1e-12)); print(f"  {nm:12s} {b:+9.4f}  se {se:7.4f}  t {b/se:+7.2f}")

def predict(r): return max(0.01, beta[0]+sum(b*float(r[f]) for b,f in zip(beta[1:],FEAT)))
def pois_over(lam, line):
    kk=int(math.floor(line))
    return 1.0-sum(math.exp(-lam)*lam**i/math.factorial(i) for i in range(kk+1))
def grade(rs, est):
    br=ae=0.0; n=0
    for r in rs:
        mu=est(r)
        if mu is None: continue
        p=pois_over(max(mu,0.01), r["line"])
        br+=(p-(1.0 if r["y"]>r["line"] else 0.0))**2; ae+=abs(mu-r["y"]); n+=1
    return br/n, ae/n, n

mb,mm,n = grade(test, predict)
n1b,n1m,_ = grade(test, lambda r: r["naive1"])
n2b,n2m,_ = grade(test, lambda r: r["naive2"])
bb,bm = min(n1b,n2b), min(n1m,n2m)
print(f"\n=== HELD-OUT WEEKS 14-22 ===\n{'':10s} {'Brier':>8} {'MAE':>8}")
print(f"{'MODEL':10s} {mb:8.4f} {mm:8.3f}")
print(f"{'naive-8':10s} {n1b:8.4f} {n1m:8.3f}")
print(f"{'naive-std':10s} {n2b:8.4f} {n2m:8.3f}")
print(f"\ntest rows {n}")
print(f"PRIMARY   Brier gain {bb-mb:+.4f} (bar +0.0050)  {'PASS' if bb-mb>=0.005 else 'FAIL'}")
print(f"SECONDARY MAE        {bm-mm:+.3f} (not worse)     {'PASS' if mm<=bm else 'FAIL'}")
print(f"MINIMUM   {n} rows (need 200)                  {'PASS' if n>=200 else 'INSUFFICIENT'}")
print("SUBGROUP")
for pos in sorted(POS):
    sub=[r for r in test if r["pos"]==pos]
    if len(sub)<30: print(f"  {pos}: {len(sub)} rows — not judged"); continue
    sb,_,sn=grade(sub,predict); b1,_,_=grade(sub,lambda r:r["naive1"]); b2,_,_=grade(sub,lambda r:r["naive2"])
    bn=min(b1,b2); print(f"  {pos}: n={sn:4d} model {sb:.4f} naive {bn:.4f} {bn-sb:+.4f} {'ok' if sb<=bn else 'WORSE'}")

# --- diagnostic, NOT part of the bar: within-player effect of ahead_out.
byp=collections.defaultdict(lambda:([],[]))
for r in rows:
    byp[r["pid"]][0 if r["ahead_out"]>0 else 1].append(r["y"])
d=[statistics.mean(a)-statistics.mean(b) for a,b in byp.values() if a and len(b)>=3]
print(f"\nDIAGNOSTIC within-player: {len(d)} players had both states; "
      f"mean receptions when a teammate ahead is OUT minus otherwise = {statistics.mean(d):+.3f}")
