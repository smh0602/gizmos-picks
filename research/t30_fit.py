"""T30 -- fit and evaluate. ONE specification per arm, exactly as pre-registered.

Run from the repo root, after t30_data.py:  python research/t30_fit.py

THREE estimators scored on the SAME held-out rows:
  (1) the INCUMBENT smoothed rate, recomputed on this sample
  (2) T27's four features, refitted on this sample
  (3) T27's four features PLUS the one new slot term

ARM A uses his trailing-20 mean batting slot   -- shippable on the morning card
ARM B uses today's ACTUAL slot                  -- UPPER BOUND ONLY, ships nowhere

PASS (either arm) = beats the INCUMBENT on Brier by >= 0.005
                AND beats T27-refitted by >= 0.002
                AND is not worse on log loss.  BOTH MARGINS OR IT FAILS.
"""
import json
import numpy as np

D = json.load(open('research/t30_rows.json'))
SPLIT = '2026-07-15'
BASE = ['hpa', 'pa20', 'oppH', 'home']

tr = [x for x in D if x['d'] < SPLIT]
te = [x for x in D if x['d'] >= SPLIT]
yte = np.array([r['y'] for r in te], float)
ytr = np.array([r['y'] for r in tr], float)

def fit(feats):
    Xtr = np.array([[r[f] for f in feats] for r in tr], float)
    Xte = np.array([[r[f] for f in feats] for r in te], float)
    mu, sd = Xtr.mean(0), Xtr.std(0); sd[sd == 0] = 1
    Ztr = np.c_[np.ones(len(Xtr)), (Xtr - mu) / sd]
    Zte = np.c_[np.ones(len(Xte)), (Xte - mu) / sd]
    b = np.zeros(Ztr.shape[1])
    for _ in range(60):
        p = 1 / (1 + np.exp(-Ztr @ b))
        g = Ztr.T @ (ytr - p)
        Hm = -(Ztr.T * (p * (1 - p))) @ Ztr
        nb = b + np.linalg.solve(Hm, -g)
        if np.max(np.abs(nb - b)) < 1e-10: b = nb; break
        b = nb
    p = 1 / (1 + np.exp(-Ztr @ b))
    se = np.sqrt(np.diag(np.linalg.inv((Ztr.T * (p * (1 - p))) @ Ztr)))
    return b, se, 1 / (1 + np.exp(-Zte @ b))

def brier(p): return float(np.mean((p - yte) ** 2))
def logloss(p):
    q = np.clip(p, 1e-9, 1 - 1e-9)
    return float(-np.mean(yte * np.log(q) + (1 - yte) * np.log(1 - q)))

LAB = {'hpa': 'his hits per PA, last 20', 'pa20': 'his mean PA, last 20',
       'oppH': 'opposing starter H/BF', 'home': 'home',
       'slotA': 'his TRAILING-20 MEAN SLOT', 'slotB': "TODAY'S ACTUAL SLOT"}

def show(name, feats, b, se):
    print(f"\n{name}  (standardised inputs -- betas are per-SD and comparable)")
    print(f"  {'term':30} {'beta':>8} {'z':>7}")
    print(f"  {'intercept':30} {b[0]:>8.4f} {b[0]/se[0]:>7.2f}")
    for i, f in enumerate(feats, start=1):
        print(f"  {LAB[f]:30} {b[i]:>8.4f} {b[i]/se[i]:>7.2f}")

pi = np.array([r['inc'] for r in te])
pb = np.full(len(te), ytr.mean())
b0, s0, p27 = fit(BASE)
show('T27 REFITTED on this sample', BASE, b0, s0)

res = {}
for arm, sf in (('A', 'slotA'), ('B', 'slotB')):
    b, s, p = fit(BASE + [sf])
    show(f'ARM {arm} -- T27 features + {LAB[sf]}', BASE + [sf], b, s)
    res[arm] = p

print(f"\nHELD OUT: {len(te)} rows from {SPLIT} onward, base rate {yte.mean():.4f}")
print(f"  {'':34} {'Brier':>9} {'LogLoss':>9}")
rows = [('base rate (predict %.1f%%)' % (100*ytr.mean()), pb),
        ('INCUMBENT smoothed rate', pi),
        ('T27 refitted on this sample', p27),
        ('ARM A -- trailing-20 mean slot', res['A']),
        ("ARM B -- today's actual slot", res['B'])]
for nm, p in rows:
    print(f"  {nm:34} {brier(p):>9.5f} {logloss(p):>9.5f}")

print()
for arm in ('A', 'B'):
    p = res[arm]
    dI = brier(pi) - brier(p)
    d27 = brier(p27) - brier(p)
    dL = logloss(pi) - logloss(p)
    ok = dI >= 0.005 and d27 >= 0.002 and dL >= 0
    print(f"ARM {arm}")
    print(f"  Brier vs INCUMBENT      {dI:+.5f}   (bar +0.00500)  {'PASS' if dI>=0.005 else 'FAIL'}")
    print(f"  Brier vs T27-refitted   {d27:+.5f}   (bar +0.00200)  {'PASS' if d27>=0.002 else 'FAIL'}")
    print(f"  LogLoss vs INCUMBENT    {dL:+.5f}   (must be >= 0)  {'PASS' if dL>=0 else 'FAIL'}")
    print(f"  PRE-REGISTERED RESULT:  {'PASS' if ok else 'FAIL'}"
          + ("   (UPPER BOUND ONLY -- ships nowhere)" if arm == 'B' else ""))
    print()

# context, not a criterion: T27-refitted vs the incumbent on this sample
print(f"context -- T27-refitted beats the incumbent by {brier(pi)-brier(p27):+.5f} Brier on this sample")
