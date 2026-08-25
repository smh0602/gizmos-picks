"""T30 -- independent checks run BEFORE the failure is recorded.

Nothing here can change the verdict. It exists to establish that the FAIL is
a real result and not a broken fit or a broken sample.
"""
import gzip, json, collections
import numpy as np

D = json.load(open('research/t30_rows.json'))
SPLIT = '2026-07-15'
BASE = ['hpa','pa20','oppH','home']
tr = [x for x in D if x['d'] < SPLIT]; te = [x for x in D if x['d'] >= SPLIT]
ytr = np.array([r['y'] for r in tr], float); yte = np.array([r['y'] for r in te], float)

def fit(feats, evalrows):
    Xtr = np.array([[r[f] for f in feats] for r in tr], float)
    Xev = np.array([[r[f] for f in feats] for r in evalrows], float)
    mu, sd = Xtr.mean(0), Xtr.std(0); sd[sd==0]=1
    Ztr = np.c_[np.ones(len(Xtr)), (Xtr-mu)/sd]; Zev = np.c_[np.ones(len(Xev)), (Xev-mu)/sd]
    b = np.zeros(Ztr.shape[1])
    for _ in range(60):
        p = 1/(1+np.exp(-Ztr@b)); g = Ztr.T@(ytr-p); Hm = -(Ztr.T*(p*(1-p)))@Ztr
        nb = b + np.linalg.solve(Hm,-g)
        if np.max(np.abs(nb-b))<1e-10: b=nb; break
        b=nb
    return b, 1/(1+np.exp(-Zev@b))

def brier(p,y): return float(np.mean((p-y)**2))

print("=== CHECK 1 -- in-sample vs out-of-sample gain (is it overfitting?) ===")
for nm, feats in (('T27 refitted', BASE), ('ARM A', BASE+['slotA']), ('ARM B', BASE+['slotB'])):
    _, pin = fit(feats, tr); _, pout = fit(feats, te)
    inc_in = np.array([r['inc'] for r in tr]); inc_out = np.array([r['inc'] for r in te])
    print(f"  {nm:14} in-sample {brier(inc_in,ytr)-brier(pin,ytr):+.5f}   "
          f"out-of-sample {brier(inc_out,yte)-brier(pout,yte):+.5f}")

print("\n=== CHECK 2 -- is the SLOT VARIABLE itself sound? slot alone, held out ===")
_, ps = fit(['slotB'], te)
print(f"  slot-only model Brier {brier(ps,yte):.5f} vs base rate {brier(np.full(len(te),ytr.mean()),yte):.5f}"
      f"   gain {brier(np.full(len(te),ytr.mean()),yte)-brier(ps,yte):+.5f}")
print("  raw P(1+ hit) by TODAY'S ACTUAL SLOT over the whole T30 sample:")
by = collections.defaultdict(list)
for r in D: by[r['slotB']].append(r['y'])
for s in sorted(by):
    v = by[s]; pa = np.mean([r['pa20'] for r in D if r['slotB']==s])
    print(f"    slot {s}  P(1+ hit) {np.mean(v)*100:5.1f}%   trailing PA {pa:.2f}   n {len(v)}")

print("\n=== CHECK 3 -- how much slot information the incumbent ALREADY holds ===")
sB = np.array([r['slotB'] for r in D], float); sA = np.array([r['slotA'] for r in D], float)
inc = np.array([r['inc'] for r in D], float); pa = np.array([r['pa20'] for r in D], float)
print(f"  corr(today's slot, trailing-20 mean slot) {np.corrcoef(sB,sA)[0,1]:+.3f}")
print(f"  corr(today's slot, trailing-20 mean PA)   {np.corrcoef(sB,pa)[0,1]:+.3f}")
print(f"  corr(today's slot, INCUMBENT rate)        {np.corrcoef(sB,inc)[0,1]:+.3f}")
print(f"  corr(trailing mean slot, INCUMBENT rate)  {np.corrcoef(sA,inc)[0,1]:+.3f}")

print("\n=== CHECK 4 -- held-out calibration of ARM B (the better arm) ===")
_, pB = fit(BASE+['slotB'], te)
for lo in np.arange(0.40,0.85,0.05):
    m = (pB>=lo)&(pB<lo+0.05)
    if m.sum()>50: print(f"  predicted {lo*100:.0f}-{lo*100+5:.0f}%  ->  actual {yte[m].mean()*100:5.1f}%   n {int(m.sum())}")

print("\n=== CHECK 5 -- the INCUMBENT is genuinely point-in-time (hand recount) ===")
H = json.load(gzip.open('data/latest/hitters.json.gz','rt'))['players']
L = json.load(gzip.open('data/latest/lineups.json.gz','rt'))['days']
lu = collections.defaultdict(list)
for d, rows in L.items():
    for e in rows: lu[(int(e['pid']), d)].append(e)
bad = 0
for r in D[::1500]:
    per_date = collections.Counter(x['d'] for x in H[r['pid']]['g'] if x.get('d'))
    log=[]
    for x in sorted([z for z in H[r['pid']]['g'] if z.get('d')], key=lambda z: z['d']):
        ent = lu.get((int(r['pid']), x['d']))
        if not ent: continue
        st=[e for e in ent if e.get('sub')==0]
        n=per_date[x['d']]
        if n==1:
            if len(st)!=1: continue
            s=st[0]['slot']
        else:
            if len(st)!=n or len({e['slot'] for e in st})!=1: continue
            s=st[0]['slot']
        log.append((x['d'], x))
    idx=[i for i,(d,_) in enumerate(log) if d==r['d']]
    if not idx: bad+=1; continue
    i=idx[0]
    g1=sum(1 for _,x in log[:i] if (x['H'] or 0)>=1)
    hand=(g1+0.5)/(i+1)
    if abs(hand-r['inc'])>1e-12: bad+=1
print(f"  {len(D[::1500])} sampled rows re-derived from the raw log: {bad} mismatches")

print("\n=== CHECK 6 -- sample shape against the pre-registration's reconnaissance ===")
print(f"  rows {len(D)}   distinct hitters {len({r['pid'] for r in D})}"
      f"   dates {len({r['d'] for r in D})}")
print(f"  P(1+ hit) on started games, whole sample {np.mean([r['y'] for r in D])*100:.1f}%"
      f"   (reconnaissance said 38.76% went hitless -> 61.24%)")
