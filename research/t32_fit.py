"""T32 -- fit and evaluate. ONE specification per arm, exactly as registered."""
import json
import numpy as np
D = json.load(open('research/t32_rows.json'))
SPLIT='2026-07-15'
T31B = ['a_rs','a_ra','h_rs','h_ra','a_er','h_er']
T32A = T31B + ['park','temp','wind','night']
T32B = T32A + ['a_outs','h_outs','a_k','h_k']
tr=[x for x in D if x['d']<SPLIT]; te=[x for x in D if x['d']>=SPLIT]
y=np.array([r['total'] for r in te],float); ytr=np.array([r['total'] for r in tr],float)

def fit(f):
    Xt=np.array([[r[x] for x in f] for r in tr],float)
    Xe=np.array([[r[x] for x in f] for r in te],float)
    b,*_=np.linalg.lstsq(np.c_[np.ones(len(Xt)),Xt],ytr,rcond=None)
    return b, np.c_[np.ones(len(Xe)),Xe]@b
def mae(p): return float(np.mean(np.abs(p-y)))
def rmse(p): return float(np.sqrt(np.mean((p-y)**2)))

print(f"ALL ARMS SCORED ON THE SAME {len(te)} HELD-OUT ROWS (train {len(tr)})\n")
res={}
for nm,f in (('T31b  6 feat (reference)',T31B),('T32a  +park/temp/wind/night',T32A),
             ('T32b  +starter outs & K',T32B)):
    b,p=fit(f); res[nm]=(mae(p),rmse(p),b,f)
base_team=np.array([r['a_rs']+r['h_rs'] for r in te])
print(f"  {'estimator':32} {'MAE':>7} {'RMSE':>7}")
print(f"  {'baseline  team trailing':32} {mae(base_team):7.4f} {rmse(base_team):7.4f}")
print(f"  {'baseline  league mean':32} {mae(np.full(len(y),ytr.mean())):7.4f} {rmse(np.full(len(y),ytr.mean())):7.4f}")
for nm,(m,r_,_,_) in res.items(): print(f"  {nm:32} {m:7.4f} {r_:7.4f}")

m31=res['T31b  6 feat (reference)'][0]
m32a=res['T32a  +park/temp/wind/night'][0]
m32b=res['T32b  +starter outs & K'][0]
print(f"\nT32a vs T31b : {m31-m32a:+.4f} MAE   (bar +0.05000)  "
      f"{'PASS' if m31-m32a>=0.05 else 'FAIL'}")
print(f"T32b vs T32a : {m32a-m32b:+.4f} MAE   (bar +0.05000)  "
      f"{'PASS' if m32a-m32b>=0.05 else 'FAIL'}")

b,p=fit(T32A)
print(f"\nT32a coefficients, per SD of the input (runs of predicted total):")
import statistics
for f_,bb in zip(T32A,b[1:]):
    sd=statistics.pstdev([r[f_] for r in D])
    print(f"  {f_:8} {bb:+8.4f}  x sd {sd:6.3f}  = {bb*sd:+.3f}")
_,pa=fit(T32A)
print(f"\ncorr(predicted, actual) T32a = {np.corrcoef(pa,y)[0,1]:+.4f}   (T31 read +0.0799)")
print(f"predicted range {pa.min():.2f} to {pa.max():.2f}   actual {y.min():.0f} to {y.max():.0f}")
