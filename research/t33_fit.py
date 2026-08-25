"""T33 -- fit and evaluate. ONE specification, exactly as registered."""
import json, statistics
import numpy as np
D=json.load(open('research/t33_rows.json')); SPLIT='2026-07-15'
T31A=['a_rs','a_ra','h_rs','h_ra']
T33 =T31A+['park','temp','cold','elev']
tr=[x for x in D if x['d']<SPLIT]; te=[x for x in D if x['d']>=SPLIT]
ytr=np.array([r['total'] for r in tr],float); y=np.array([r['total'] for r in te],float)
def fit(f):
    Xt=np.array([[r[x] for x in f] for r in tr],float)
    Xe=np.array([[r[x] for x in f] for r in te],float)
    b,*_=np.linalg.lstsq(np.c_[np.ones(len(Xt)),Xt],ytr,rcond=None)
    return b, np.c_[np.ones(len(Xe)),Xe]@b
def mae(p): return float(np.mean(np.abs(p-y)))
def rmse(p): return float(np.sqrt(np.mean((p-y)**2)))

b_mean=np.full(len(y),ytr.mean()); b_team=np.array([r['a_rs']+r['h_rs'] for r in te])
b31,p31=fit(T31A); b33,p33=fit(T33)
print(f"ALL SCORED ON THE SAME {len(te)} HELD-OUT ROWS (train {len(tr)})\n")
print(f"  {'estimator':40} {'MAE':>7} {'RMSE':>7}")
for nm,p in ((f'baseline  league mean {ytr.mean():.2f}',b_mean),
             ('baseline  team trailing',b_team),
             ('T31a  four team-form features',p31),
             ('T33   + park, temp, cold, elevation',p33)):
    print(f"  {nm:40} {mae(p):7.4f} {rmse(p):7.4f}")

best=min(mae(b_mean),mae(b_team))
m1=best-mae(p33); m2=mae(p31)-mae(p33)
print(f"\n  MARGIN 1  vs the better baseline : {m1:+.4f}  (bar +0.10000)  {'PASS' if m1>=0.10 else 'FAIL'}")
print(f"  MARGIN 2  vs T31a on these rows : {m2:+.4f}  (bar +0.05000)  {'PASS' if m2>=0.05 else 'FAIL'}")
print(f"\n  PRE-REGISTERED RESULT: {'PASS' if (m1>=0.10 and m2>=0.05) else 'FAIL'}")

print(f"\ncoefficients, per SD of the input (runs of predicted total):")
for f_,bb in zip(T33,b33[1:]):
    sd=statistics.pstdev([r[f_] for r in D])
    print(f"  {f_:6} {bb:+9.5f}  x sd {sd:8.3f}  = {bb*sd:+.3f}")
print(f"\ncorr(predicted, actual) = {np.corrcoef(p33,y)[0,1]:+.4f}"
      f"   (T31 +0.0799, T32a +0.1559)")
print(f"predicted range {p33.min():.2f} to {p33.max():.2f}   actual {y.min():.0f} to {y.max():.0f}")
