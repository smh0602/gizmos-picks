"""T32 -- checks run BEFORE the failure is recorded. Cannot change the verdict."""
import json, statistics
import numpy as np
D=json.load(open('research/t32_rows.json')); SPLIT='2026-07-15'
T31B=['a_rs','a_ra','h_rs','h_ra','a_er','h_er']
T32A=T31B+['park','temp','wind','night']; T32B=T32A+['a_outs','h_outs','a_k','h_k']
tr=[x for x in D if x['d']<SPLIT]; te=[x for x in D if x['d']>=SPLIT]
ytr=np.array([r['total'] for r in tr],float); yte=np.array([r['total'] for r in te],float)
def fit(f,ev):
    Xt=np.array([[r[x] for x in f] for r in tr],float)
    b,*_=np.linalg.lstsq(np.c_[np.ones(len(Xt)),Xt],ytr,rcond=None)
    Xe=np.array([[r[x] for x in f] for r in ev],float)
    return b, np.c_[np.ones(len(Xe)),Xe]@b
def mae(p,y): return float(np.mean(np.abs(p-y)))

print("=== CHECK 1 -- is the added complexity OVERFITTING? ===")
print(f"  {'arm':6} {'k':>3} {'in-sample':>10} {'out-of-sample':>14} {'gap':>8}")
for nm,f in (('T31b',T31B),('T32a',T32A),('T32b',T32B)):
    _,pi=fit(f,tr); _,po=fit(f,te)
    print(f"  {nm:6} {len(f):3} {mae(pi,ytr):10.4f} {mae(po,yte):14.4f} {mae(po,yte)-mae(pi,ytr):8.4f}")
print(f"  training rows: {len(tr)}")

print("\n=== CHECK 2 -- do the NEW inputs carry signal, separately from the fit? ===")
for f in ('park','temp','wind','night'):
    x=np.array([r[f] for r in D],float); t=np.array([r['total'] for r in D],float)
    print(f"  corr(total, {f:5}) = {np.corrcoef(x,t)[0,1]:+.4f}")

print("\n=== CHECK 3 -- a NONSENSE SIGN is the signature of an unstable fit ===")
b,_=fit(T32A,te)
for f,bb in zip(T32A,b[1:]):
    flag=""
    if f=='h_rs' and bb<0: flag="  <-- NEGATIVE: a home club scoring MORE lately predicts FEWER total runs. Physically nonsense."
    if f=='a_rs' and bb<0: flag="  <-- NEGATIVE, same problem"
    print(f"  {f:8} {bb:+8.4f}{flag}")

print("\n=== CHECK 4 -- park factor is POINT-IN-TIME (no lookahead) ===")
early=[r['park'] for r in sorted(D,key=lambda r:r['d'])[:50]]
late =[r['park'] for r in sorted(D,key=lambda r:r['d'])[-50:]]
print(f"  earliest 50 rows: {sum(1 for x in early if x==0.0)}/50 are 0.0 (thin park history)")
print(f"  latest   50 rows: {sum(1 for x in late  if x==0.0)}/50 are 0.0")
print("  a park factor that were LOOKAHEAD would be equally informative on day one")
