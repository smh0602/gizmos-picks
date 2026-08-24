"""T27 — fit and evaluate. ONE specification, exactly as pre-registered.

Run from the repo root, after t27_data.py:  python research/t27_fit.py
RESULT 2026-08-24: FAILED. Brier +0.00236 against a +0.00500 bar.
The bar was NOT moved. Nothing shipped.
"""
import json, math
import numpy as np

D = json.load(open('research/t27_rows.json'))
SPLIT = '2026-07-15'
FEATS = ['hpa', 'pa20', 'oppH', 'home']

tr = [x for x in D if x['d'] < SPLIT]
te = [x for x in D if x['d'] >= SPLIT]

def mat(rows):
    X = np.array([[r[f] for f in FEATS] for r in rows], float)
    y = np.array([r['y'] for r in rows], float)
    return X, y

Xtr, ytr = mat(tr); Xte, yte = mat(te)
mu, sd = Xtr.mean(0), Xtr.std(0)
sd[sd == 0] = 1
Ztr = np.c_[np.ones(len(Xtr)), (Xtr - mu) / sd]
Zte = np.c_[np.ones(len(Xte)), (Xte - mu) / sd]

# IRLS. No regularisation, no tuning -- there is nothing to tune.
b = np.zeros(Ztr.shape[1])
for _ in range(50):
    p = 1 / (1 + np.exp(-Ztr @ b))
    W = p * (1 - p)
    g = Ztr.T @ (ytr - p)
    Hm = -(Ztr.T * W) @ Ztr
    step = np.linalg.solve(Hm, -g)
    b_new = b + step
    if np.max(np.abs(b_new - b)) < 1e-10:
        b = b_new; break
    b = b_new

se = np.sqrt(np.diag(np.linalg.inv((Ztr.T * (p * (1 - p))) @ Ztr)))
print("FITTED (standardised inputs, so betas are per-SD and comparable)")
print(f"  {'term':28} {'beta':>8} {'z':>7}")
print(f"  {'intercept':28} {b[0]:>8.4f} {b[0]/se[0]:>7.2f}")
labels = ['his hits per PA, last 20', 'his mean PA, last 20',
          'opposing starter H/BF', 'home']
for i, (nm, lb) in enumerate(zip(FEATS, labels), start=1):
    print(f"  {lb:28} {b[i]:>8.4f} {b[i]/se[i]:>7.2f}")

pm = 1 / (1 + np.exp(-Zte @ b))          # model
pi = np.array([r['inc'] for r in te])    # INCUMBENT: what ships today
pb = np.full(len(te), ytr.mean())        # base rate

def brier(p): return float(np.mean((p - yte) ** 2))
def logloss(p):
    q = np.clip(p, 1e-9, 1 - 1e-9)
    return float(-np.mean(yte * np.log(q) + (1 - yte) * np.log(1 - q)))

print(f"\nHELD OUT: {len(te)} rows from {SPLIT} onward, base rate {yte.mean():.4f}")
print(f"  {'':26} {'Brier':>9} {'LogLoss':>9}")
for nm, p in (('base rate (predict 58.6%)', pb),
              ('INCUMBENT smoothed rate', pi),
              ('T27 model', pm)):
    print(f"  {nm:26} {brier(p):>9.5f} {logloss(p):>9.5f}")

dB = brier(pi) - brier(pm)
dL = logloss(pi) - logloss(pm)
print(f"\n  Brier improvement over the incumbent : {dB:+.5f}   (pass bar +0.00500)")
print(f"  LogLoss improvement                  : {dL:+.5f}   (must not be negative)")
passed = dB >= 0.005 and dL >= 0
print(f"\n  PRE-REGISTERED RESULT: {'PASS' if passed else 'FAIL'}")
