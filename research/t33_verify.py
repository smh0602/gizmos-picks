"""T33 -- checks run BEFORE the failure is recorded. Cannot change the verdict."""
import json, statistics
import numpy as np
D=json.load(open('research/t33_rows.json')); SPLIT='2026-07-15'
T31A=['a_rs','a_ra','h_rs','h_ra']; T33=T31A+['park','temp','cold','elev']
tr=[x for x in D if x['d']<SPLIT]; te=[x for x in D if x['d']>=SPLIT]
ytr=np.array([r['total'] for r in tr],float); y=np.array([r['total'] for r in te],float)
def fit(f,ev):
    Xt=np.array([[r[x] for x in f] for r in tr],float)
    b,*_=np.linalg.lstsq(np.c_[np.ones(len(Xt)),Xt],ytr,rcond=None)
    Xe=np.array([[r[x] for x in f] for r in ev],float)
    return b, np.c_[np.ones(len(Xe)),Xe]@b
def mae(p,yy): return float(np.mean(np.abs(p-yy)))

print("=== CHECK 1 -- the collinearity my own pre-registration told me to suspect ===")
pk=np.array([r['park'] for r in D]); el=np.array([r['elev'] for r in D])
print(f"  corr(park factor, elevation) = {np.corrcoef(pk,el)[0,1]:+.4f}")
X=np.array([[r[f] for f in T33] for r in D],float)
C=np.corrcoef(X.T)
print("  |corr| > 0.30 among the eight features:")
for i in range(len(T33)):
    for j in range(i+1,len(T33)):
        if abs(C[i,j])>0.30: print(f"    {T33[i]:6} <-> {T33[j]:6}  {C[i,j]:+.4f}")
# VIF for elevation
def vif(k):
    o=[f for f in T33 if f!=k]
    A=np.c_[np.ones(len(D)),np.array([[r[f] for f in o] for r in D],float)]
    t=np.array([r[k] for r in D],float)
    b,*_=np.linalg.lstsq(A,t,rcond=None); pred=A@b
    r2=1-np.sum((t-pred)**2)/np.sum((t-t.mean())**2)
    return 1/(1-r2) if r2<1 else float('inf')
for f in ('elev','park','temp','cold'):
    print(f"  VIF {f:6} = {vif(f):6.2f}   {'<-- inflated' if vif(f)>2.5 else ''}")

print("\n=== CHECK 2 -- what happened to h_ra, the biggest term in T31? ===")
b31,_=fit(T31A,te); b33,_=fit(T33,te)
sd={f:statistics.pstdev([r[f] for r in D]) for f in T33}
print(f"  {'term':6} {'T31a (beta x sd)':>18} {'T33 (beta x sd)':>18}")
for i,f in enumerate(T31A):
    print(f"  {f:6} {b31[i+1]*sd[f]:>18.3f} {b33[i+1]*sd[f]:>18.3f}")
print("  a home club's runs ALLOWED was T31's single largest term. Adding park")
print("  and elevation absorbed it -- the same fact, counted twice.")

print("\n=== CHECK 3 -- is the COLD term testable at all on this split? ===")
nc_tr=sum(x['cold'] for x in tr); nc_te=sum(x['cold'] for x in te)
print(f"  cold games in TRAIN: {nc_tr} of {len(tr)} ({100*nc_tr/len(tr):.1f}%)")
print(f"  cold games in TEST : {nc_te} of {len(te)} ({100*nc_te/len(te):.1f}%)")
print("  A chronological split at mid-July puts nearly every cold game in TRAIN.")
print("  The cold term is fitted on 165 games and evaluated on 2. It is NOT tested.")

print("\n=== CHECK 4 -- overfitting ===")
for nm,f in (('T31a',T31A),('T33',T33)):
    _,pi=fit(f,tr); _,po=fit(f,te)
    base_i=np.array([r['a_rs']+r['h_rs'] for r in tr]); base_o=np.array([r['a_rs']+r['h_rs'] for r in te])
    print(f"  {nm:5} in-sample {mae(base_i,ytr)-mae(pi,ytr):+.4f}   out-of-sample {mae(base_o,y)-mae(po,y):+.4f}")
