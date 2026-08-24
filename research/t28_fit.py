"""T28 — two-stage hitter model. ONE specification, exactly as pre-registered.

Stage 1: E[PA]           (OLS)
Stage 2: P(hit per PA)   (logistic)
Combine: P(H>=1) = 1 - (1-p)^E[PA]

Pass bar, fixed in claude/owed-tests.md BEFORE this ran:
  beat the T27 model by >= 0.002 Brier  AND  beat the incumbent by >= 0.005.
"""
import gzip, json, collections, math
import numpy as np

SPLIT = '2026-07-15'; WINDOW = 20; MIN_PRIOR = 20; MIN_STARTS = 5
H = json.load(gzip.open('data/latest/hitters.json.gz','rt'))['players']
P = json.load(gzip.open('data/latest/pitchers.json.gz','rt'))['players']

# --- identical filters to T27, including the trade-consistency check ---
support = collections.defaultdict(set)
for pid, v in H.items():
    t = v.get('team')
    if t:
        for r in v['g']:
            if r.get('d') and r.get('o'): support[(r['d'], t, r['o'])].add(pid)
real = {k for k, s in support.items() if len(s) >= 3}

starters = collections.defaultdict(list)
for pid, v in P.items():
    for i, r in enumerate(v['g']):
        if r.get('gs') and r.get('d') and r.get('o'): starters[(r['d'], r['o'])].append((pid, i))

def opp_hpbf(pid, i):
    rows = [x for x in P[pid]['g'][:i] if x.get('gs')]
    h = sum(x['hit'] for x in rows if x.get('hit') is not None)
    bf = sum(x['bf'] for x in rows if x.get('bf') is not None)
    return (h/bf, len(rows)) if bf else (None, len(rows))

# 🆕 TEAM RUNS PER GAME -- the spec allowed this "if derivable". It is:
# sum every player's runs for that team on that date.
team_runs = collections.defaultdict(int)
team_dates = collections.defaultdict(set)
for pid, v in H.items():
    t = v.get('team')
    if not t: continue
    for r in v['g']:
        if r.get('d') and (r.get('pa') or 0) > 0:
            team_runs[(t, r['d'])] += (r.get('r') or 0)
            team_dates[t].add(r['d'])
team_hist = {t: sorted(ds) for t, ds in team_dates.items()}

rows = []
for pid, v in H.items():
    t = v.get('team')
    log = sorted([r for r in v['g'] if (r.get('pa') or 0) > 0], key=lambda r: r['d'])
    for i, r in enumerate(log):
        if i < MIN_PRIOR or (r['d'], t, r['o']) not in real: continue
        cand = starters.get((r['d'], t), [])
        if len(cand) != 1: continue
        spid, si = cand[0]
        oh, nst = opp_hpbf(spid, si)
        if oh is None or nst < MIN_STARTS: continue
        prior = log[max(0, i-WINDOW):i]
        pa = sum(x['pa'] for x in prior)
        if not pa: continue
        hits = sum(x['H'] or 0 for x in prior)
        allp = log[:i]
        inc = (sum(1 for x in allp if (x['H'] or 0) >= 1) + 0.5) / (len(allp) + 1)
        # team runs over its last 20 games strictly before this date
        past = [d for d in team_hist.get(t, []) if d < r['d']][-WINDOW:]
        trg = (sum(team_runs[(t, d)] for d in past) / len(past)) if past else None
        if trg is None: continue
        rows.append({'d': r['d'], 'y': 1 if (r['H'] or 0) >= 1 else 0, 'pa': r['pa'],
                     'hpa': hits/pa, 'pa20': pa/len(prior), 'oppH': oh,
                     'home': 1 if r.get('h') else 0, 'trg': trg, 'inc': inc,
                     'H': r['H'] or 0})

tr = [x for x in rows if x['d'] < SPLIT]; te = [x for x in rows if x['d'] >= SPLIT]
print(f"rows {len(rows)}  train {len(tr)}  test {len(te)}   (T27 used 21,323 / 13,444 / 7,879)")

def z(rows_, feats, ref=None):
    X = np.array([[r[f] for f in feats] for r in rows_], float)
    if ref is None: ref = (X.mean(0), np.where(X.std(0)==0, 1, X.std(0)))
    return np.c_[np.ones(len(X)), (X-ref[0])/ref[1]], ref

# --- Stage 1: E[PA] by OLS ---
S1 = ['pa20','trg','home']
A, ref1 = z(tr, S1); yv = np.array([r['pa'] for r in tr], float)
w1 = np.linalg.lstsq(A, yv, rcond=None)[0]
B, _ = z(te, S1, ref1)
pa_tr, pa_te = A @ w1, B @ w1
print(f"\nSTAGE 1  E[PA]  (OLS)   RMSE train {np.sqrt(np.mean((pa_tr-yv)**2)):.3f}"
      f"  test {np.sqrt(np.mean((pa_te-np.array([r['pa'] for r in te]))**2)):.3f}")
for nm, c in zip(['intercept']+['his trailing-20 PA','team runs/game, trailing 20','home'], w1):
    print(f"   {nm:30} {c:+.4f}")

# --- Stage 2: P(hit per PA), weighted by plate appearances ---
S2 = ['hpa','oppH']
C, ref2 = z(tr, S2, None)
hits = np.array([r['H'] for r in tr], float); pas = np.array([r['pa'] for r in tr], float)
b = np.zeros(C.shape[1])
for _ in range(60):
    p = 1/(1+np.exp(-C@b)); W = pas*p*(1-p)
    step = np.linalg.solve(-((C.T*W)@C), -(C.T@(hits - pas*p)))
    b = b + step
    if np.max(np.abs(step)) < 1e-11: break
D_, _ = z(te, S2, ref2)
p_hit_te = 1/(1+np.exp(-D_@b))
print(f"\nSTAGE 2  P(hit per PA)  (logistic, PA-weighted)   league ~{hits.sum()/pas.sum():.4f}")
for nm, c in zip(['intercept','his trailing-20 hits/PA','opposing starter H/BF'], b):
    print(f"   {nm:30} {c:+.4f}")

pa_te_c = np.clip(pa_te, 1.0, 7.0)
p28 = 1 - (1 - p_hit_te)**pa_te_c
yte = np.array([r['y'] for r in te], float)
inc = np.array([r['inc'] for r in te], float)

# T27's model, refitted on this identical sample so the comparison is fair
F27 = ['hpa','pa20','oppH','home']
E, ref3 = z(tr, F27); Fm, _ = z(te, F27, ref3)
ytr = np.array([r['y'] for r in tr], float); b27 = np.zeros(E.shape[1])
for _ in range(60):
    p = 1/(1+np.exp(-E@b27)); W = p*(1-p)
    b27 = b27 + np.linalg.solve(-((E.T*W)@E), -(E.T@(ytr-p)))
p27 = 1/(1+np.exp(-Fm@b27))

br = lambda p: float(np.mean((p-yte)**2))
ll = lambda p: float(-np.mean(yte*np.log(np.clip(p,1e-9,1-1e-9))+(1-yte)*np.log(np.clip(1-p,1e-9,1-1e-9))))
print(f"\nHELD OUT {len(te)} rows, base rate {yte.mean():.4f}")
print(f"  {'':28} {'Brier':>9} {'LogLoss':>9}")
for nm, p in (('INCUMBENT smoothed rate', inc), ('T27 model', p27), ('T28 two-stage', p28)):
    print(f"  {nm:28} {br(p):>9.5f} {ll(p):>9.5f}")
d27, dinc = br(p27)-br(p28), br(inc)-br(p28)
print(f"\n  T28 vs T27      : {d27:+.5f}   (bar +0.00200)")
print(f"  T28 vs incumbent: {dinc:+.5f}   (bar +0.00500)")
print(f"\n  PRE-REGISTERED RESULT: {'PASS' if (d27>=0.002 and dinc>=0.005) else 'FAIL'}")
