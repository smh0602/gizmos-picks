"""T31 -- checks run BEFORE the failure is recorded. Cannot change the verdict."""
import gzip, json, collections, statistics
import numpy as np
D = json.load(open('research/t31_rows.json'))
SPLIT='2026-07-15'; A=['a_rs','a_ra','h_rs','h_ra']; B=A+['a_er','h_er']
def ols(f,tr,ev):
    Xt=np.array([[r[x] for x in f] for r in tr],float); yt=np.array([r['total'] for r in tr],float)
    Ze=np.c_[np.ones(len(ev)),np.array([[r[x] for x in f] for r in ev],float)]
    b,*_=np.linalg.lstsq(np.c_[np.ones(len(Xt)),Xt],yt,rcond=None); return b,Ze@b
def mae(p,y): return float(np.mean(np.abs(p-y)))

print("=== CHECK 1 -- overfitting? in-sample vs out-of-sample gain over team-trailing ===")
for tag,f,sub in (('T31a',A,False),('T31b',B,True)):
    tr=[x for x in D if x['d']<SPLIT and (not sub or 'a_er' in x)]
    te=[x for x in D if x['d']>=SPLIT and (not sub or 'a_er' in x)]
    for nm,ev in (('in-sample',tr),('out-of-sample',te)):
        _,p=ols(f,tr,ev); y=np.array([r['total'] for r in ev],float)
        base=np.array([r['a_rs']+r['h_rs'] for r in ev])
        print(f"  {tag} {nm:14} model {mae(p,y):.4f}  team-trailing {mae(base,y):.4f}  gain {mae(base,y)-mae(p,y):+.4f}")

print("\n=== CHECK 2 -- is the fit sane? predicted range vs actual ===")
tr=[x for x in D if x['d']<SPLIT]; te=[x for x in D if x['d']>=SPLIT]
_,p=ols(A,tr,te); y=np.array([r['total'] for r in te],float)
print(f"  predicted  min {p.min():.2f}  mean {p.mean():.2f}  max {p.max():.2f}")
print(f"  actual     min {y.min():.2f}  mean {y.mean():.2f}  max {y.max():.2f}")
print(f"  correlation(pred, actual) = {np.corrcoef(p,y)[0,1]:+.4f}")

print("\n=== CHECK 3 -- POINT-IN-TIME integrity, recomputed by hand from raw scores ===")
S=json.load(gzip.open('data/latest/scores.json.gz','rt'))['days']
H=json.load(gzip.open('data/latest/hitters.json.gz','rt'))['players']
MLB={v['team'] for v in H.values() if v.get('team')}; OPEN=min(r['d'] for v in H.values() for r in v['g'] if r.get('d'))
gs=sorted([(d,r) for d,v in S.items() for r in v if d>=OPEN and r['away'] in MLB and r['home'] in MLB],
          key=lambda x:(x[0],x[1]['gamePk']))
bad=0
for row in D[::250]:
    hist=[]
    for d,r in gs:
        if r['gamePk']==row['gamePk']:
            break
        if r['away']==row['away']: hist.append((r['away_r'],r['home_r']))
        elif r['home']==row['away']: hist.append((r['home_r'],r['away_r']))
    w=hist[-20:]
    hand=sum(x[0] for x in w)/len(w)
    if abs(hand-row['a_rs'])>1e-9: bad+=1
print(f"  {len(D[::250])} sampled rows re-derived from raw scores: {bad} mismatches")
print("  (a mismatch would mean a window saw a game it should not have)")

print("\n=== CHECK 4 -- what the coefficients actually say ===")
b,_=ols(B,[x for x in D if x['d']<SPLIT and 'a_er' in x],[x for x in D if x['d']>=SPLIT and 'a_er' in x])
sd={f:statistics.pstdev([r[f] for r in D if f in r]) for f in B}
print(f"  {'feature':10} {'beta':>8} {'sd':>7} {'beta*sd (runs)':>16}")
for f,bb in zip(B,b[1:]):
    print(f"  {f:10} {bb:+8.3f} {sd[f]:7.3f} {bb*sd[f]:+16.3f}")
