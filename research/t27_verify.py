"""T27 — verify the pipeline BEFORE trusting its verdict.

A wrong FAIL is as costly as a wrong PASS. Checks that the incumbent is
genuinely point-in-time, that the outcome column is right, that the fit is
not merely overfitting, and that the model is calibrated.
Run from the repo root:  python research/t27_verify.py
"""
import json, gzip, math, collections
import numpy as np
D = json.load(open('research/t27_rows.json')); SPLIT='2026-07-15'
te=[x for x in D if x['d']>=SPLIT]
H = json.load(gzip.open('data/latest/hitters.json.gz','rt'))['players']

print("1. Is the INCUMBENT point-in-time, or is it peeking?")
# recompute one player's incumbent by hand at a specific row
r = te[len(te)//2]; pid=r['pid']
log=sorted([x for x in H[pid]['g'] if (x.get('pa') or 0)>0], key=lambda x:x['d'])
i=[k for k,x in enumerate(log) if x['d']==r['d']][0]
prior=log[:i]; g1=sum(1 for x in prior if (x['H'] or 0)>=1)
hand=(g1+0.5)/(len(prior)+1)
print(f"   {H[pid]['name']} on {r['d']}: stored {r['inc']:.6f} | hand {hand:.6f} | match {abs(hand-r['inc'])<1e-12}")
after=[x for x in log[i:] if (x['H'] or 0)>=1]
print(f"   uses {len(prior)} prior games and IGNORES the {len(log)-i} from this date on  ✓")

print("\n2. Outcome column correct?")
bad=sum(1 for x in te if x['y'] not in (0,1))
sample=[x for x in te[:400]]
mm=0
for x in sample:
    lg=sorted([q for q in H[x['pid']]['g'] if (q.get('pa') or 0)>0], key=lambda q:q['d'])
    row=[q for q in lg if q['d']==x['d']][0]
    if x['y'] != (1 if (row['H'] or 0)>=1 else 0): mm+=1
print(f"   non-binary y: {bad} | recounted 400 rows from the log, mismatches: {mm}")

print("\n3. Does the model's edge hold in-sample too? (a broken fit often does not)")
FEATS=['hpa','pa20','oppH','home']
tr=[x for x in D if x['d']<SPLIT]
def mat(rows):
    return (np.array([[r[f] for f in FEATS] for r in rows],float),
            np.array([r['y'] for r in rows],float))
Xtr,ytr=mat(tr); Xte,yte=mat(te)
mu,sd=Xtr.mean(0),Xtr.std(0); sd[sd==0]=1
Ztr=np.c_[np.ones(len(Xtr)),(Xtr-mu)/sd]; Zte=np.c_[np.ones(len(Xte)),(Xte-mu)/sd]
b=np.zeros(Ztr.shape[1])
for _ in range(50):
    p=1/(1+np.exp(-Ztr@b)); W=p*(1-p)
    b=b+np.linalg.solve(-((Ztr.T*W)@Ztr), -(Ztr.T@(ytr-p)))
ptr=1/(1+np.exp(-Ztr@b)); pte=1/(1+np.exp(-Zte@b))
itr=np.array([r['inc'] for r in tr]); ite=np.array([r['inc'] for r in te])
br=lambda p,y: float(np.mean((p-y)**2))
print(f"   train  incumbent {br(itr,ytr):.5f}  model {br(ptr,ytr):.5f}  gain {br(itr,ytr)-br(ptr,ytr):+.5f}")
print(f"   test   incumbent {br(ite,yte):.5f}  model {br(pte,yte):.5f}  gain {br(ite,yte)-br(pte,yte):+.5f}")
print("   (a similar in/out gain means it is not overfitting -- the signal really is this small)")

print("\n4. Model calibration on the held-out set")
bk=collections.defaultdict(list)
for p,y in zip(pte,yte): bk[int(p*20)/20].append(y)
for k in sorted(bk):
    v=bk[k]
    if len(v)>=100: print(f"   predicted {k*100:4.0f}-{(k+0.05)*100:4.0f}%  n={len(v):5d}  actual {100*sum(v)/len(v):5.1f}%")
print(f"\n   model range: {pte.min():.3f} to {pte.max():.3f}  (incumbent {ite.min():.3f} to {ite.max():.3f})")
