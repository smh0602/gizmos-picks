"""T29 — total bases. P(TB >= 2), the over-1.5 line. ONE specification.

Pre-registered in claude/owed-tests.md BEFORE this ran. Same sample, same
filters and the same chronological split as T27/T28 so all three compare.
Run from the repo root:  python research/t29_fit.py
"""
import gzip, json, collections
import numpy as np

SPLIT='2026-07-15'; WINDOW=20; MIN_PRIOR=20; MIN_STARTS=5
H=json.load(gzip.open('data/latest/hitters.json.gz','rt'))['players']
P=json.load(gzip.open('data/latest/pitchers.json.gz','rt'))['players']

support=collections.defaultdict(set)
for pid,v in H.items():
    t=v.get('team')
    if t:
        for r in v['g']:
            if r.get('d') and r.get('o'): support[(r['d'],t,r['o'])].add(pid)
real={k for k,s in support.items() if len(s)>=3}

starters=collections.defaultdict(list)
for pid,v in P.items():
    for i,r in enumerate(v['g']):
        if r.get('gs') and r.get('d') and r.get('o'): starters[(r['d'],r['o'])].append((pid,i))

def opp_rates(pid,i):
    """Point-in-time H/BF and K/BF. ⚠️ PROXIES -- the pitcher log carries no
    extra-base detail, so total bases allowed cannot be computed."""
    rows=[x for x in P[pid]['g'][:i] if x.get('gs')]
    bf=sum(x['bf'] for x in rows if x.get('bf') is not None)
    if not bf: return None,None,len(rows)
    h=sum(x['hit'] for x in rows if x.get('hit') is not None)
    k=sum(x['k'] for x in rows if x.get('k') is not None)
    return h/bf, k/bf, len(rows)

rows=[]
for pid,v in H.items():
    t=v.get('team')
    log=sorted([r for r in v['g'] if (r.get('pa') or 0)>0], key=lambda r:r['d'])
    for i,r in enumerate(log):
        if i<MIN_PRIOR or (r['d'],t,r['o']) not in real: continue
        cand=starters.get((r['d'],t),[])
        if len(cand)!=1: continue
        oh,ok,nst=opp_rates(*cand[0])
        if oh is None or nst<MIN_STARTS: continue
        prior=log[max(0,i-WINDOW):i]
        pa=sum(x['pa'] for x in prior)
        if not pa: continue
        tb=sum(x.get('tb') or 0 for x in prior)
        allp=log[:i]
        inc=(sum(1 for x in allp if (x.get('tb') or 0)>=2)+0.5)/(len(allp)+1)
        rows.append({'d':r['d'],'y':1 if (r.get('tb') or 0)>=2 else 0,
                     'tbpa':tb/pa,'pa20':pa/len(prior),'oppH':oh,'oppK':ok,
                     'home':1 if r.get('h') else 0,'inc':inc})

FE=['tbpa','pa20','oppH','oppK','home']
tr=[x for x in rows if x['d']<SPLIT]; te=[x for x in rows if x['d']>=SPLIT]
print(f"rows {len(rows)}  train {len(tr)}  test {len(te)}")
X=np.array([[r[f] for f in FE] for r in tr],float); y=np.array([r['y'] for r in tr],float)
mu,sd=X.mean(0),X.std(0); sd[sd==0]=1
Z=np.c_[np.ones(len(X)),(X-mu)/sd]
Xt=np.array([[r[f] for f in FE] for r in te],float); yt=np.array([r['y'] for r in te],float)
Zt=np.c_[np.ones(len(Xt)),(Xt-mu)/sd]
b=np.zeros(Z.shape[1])
for _ in range(60):
    p=1/(1+np.exp(-Z@b)); W=p*(1-p)
    step=np.linalg.solve(-((Z.T*W)@Z), -(Z.T@(y-p))); b=b+step
    if np.max(np.abs(step))<1e-11: break
se=np.sqrt(np.diag(np.linalg.inv((Z.T*(p*(1-p)))@Z)))
lab=['intercept','his total bases per PA, last 20','his mean PA, last 20',
     'opposing starter H/BF (proxy)','opposing starter K/BF (proxy)','home']
print(f"\n{'term':34} {'beta':>8} {'z':>7}")
for nm,c,s in zip(lab,b,se): print(f"{nm:34} {c:>8.4f} {c/s:>7.2f}")

pm=1/(1+np.exp(-Zt@b)); pi=np.array([r['inc'] for r in te]); pb=np.full(len(te),y.mean())
br=lambda p: float(np.mean((p-yt)**2))
ll=lambda p: float(-np.mean(yt*np.log(np.clip(p,1e-9,1-1e-9))+(1-yt)*np.log(np.clip(1-p,1e-9,1-1e-9))))
print(f"\nHELD OUT {len(te)} rows, base rate {yt.mean():.4f}")
print(f"  {'':30} {'Brier':>9} {'LogLoss':>9}")
for nm,p in (('base rate',pb),('INCUMBENT smoothed rate',pi),('T29 model',pm)):
    print(f"  {nm:30} {br(p):>9.5f} {ll(p):>9.5f}")
dB,dL=br(pi)-br(pm), ll(pi)-ll(pm)
print(f"\n  Brier improvement over incumbent : {dB:+.5f}   (bar +0.00500)")
print(f"  LogLoss improvement              : {dL:+.5f}   (must be >= 0)")
print(f"\n  PRE-REGISTERED RESULT: {'PASS' if (dB>=0.005 and dL>=0) else 'FAIL'}")
