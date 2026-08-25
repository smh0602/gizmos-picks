"""T31 -- fit and evaluate. ONE specification per arm, exactly as registered.

Run from the repo root, after t31_data.py:  python research/t31_fit.py

T31a  four team-form features   -> must beat the BETTER baseline by >= 0.10 MAE
T31b  those four + both starters -> must beat T31a by >= 0.05 MAE

BOTH ARMS ARE SANITY GATES, NOT SHIPPING GATES. Beating a naive baseline
means nothing at a sportsbook. Only T31c (vs the book) can ship anything,
and it has 55 of the 400 games it needs.
"""
import json
import numpy as np

D = json.load(open('research/t31_rows.json'))
SPLIT = '2026-07-15'
A = ['a_rs', 'a_ra', 'h_rs', 'h_ra']
B = A + ['a_er', 'h_er']

def ols(feats, train, evalrows):
    Xt = np.array([[r[f] for f in feats] for r in train], float)
    yt = np.array([r['total'] for r in train], float)
    Xe = np.array([[r[f] for f in feats] for r in evalrows], float)
    Zt = np.c_[np.ones(len(Xt)), Xt]
    Ze = np.c_[np.ones(len(Xe)), Xe]
    beta, *_ = np.linalg.lstsq(Zt, yt, rcond=None)
    return beta, Ze @ beta

def mae(p, y): return float(np.mean(np.abs(p - y)))
def rmse(p, y): return float(np.sqrt(np.mean((p - y) ** 2)))

def report(tag, rows_tr, rows_te, feats):
    y = np.array([r['total'] for r in rows_te], float)
    ytr = np.array([r['total'] for r in rows_tr], float)
    beta, pred = ols(feats, rows_tr, rows_te)
    b_mean = np.full(len(y), ytr.mean())                       # baseline (i)
    b_team = np.array([r['a_rs'] + r['h_rs'] for r in rows_te])  # baseline (ii)
    print(f"\n{tag}   train {len(rows_tr)}  test {len(rows_te)}")
    print(f"  {'estimator':38} {'MAE':>7} {'RMSE':>7}")
    for nm, p in ((f"baseline (i)  league mean {ytr.mean():.2f}", b_mean),
                  ("baseline (ii) team trailing", b_team),
                  (f"MODEL ({len(feats)} features)", pred)):
        print(f"  {nm:38} {mae(p,y):7.4f} {rmse(p,y):7.4f}")
    print(f"  coefficients: intercept {beta[0]:+.3f}  "
          + "  ".join(f"{f} {b:+.3f}" for f, b in zip(feats, beta[1:])))
    best = min(mae(b_mean, y), mae(b_team, y))
    return mae(pred, y), best, pred, y

tr_a = [x for x in D if x['d'] < SPLIT]
te_a = [x for x in D if x['d'] >= SPLIT]
print("=" * 66)
print("T31a -- team form only. Bar: beat the BETTER baseline by >= 0.10 MAE")
m_a, best_a, _, _ = report("T31a", tr_a, te_a, A)
gain_a = best_a - m_a
print(f"\n  gain over the better baseline: {gain_a:+.4f} MAE   (bar +0.10000)")
pass_a = gain_a >= 0.10
print(f"  PRE-REGISTERED RESULT: {'PASS' if pass_a else 'FAIL'}")

# ---------------------------------------------------------------- T31b
# The head-to-head MUST be scored on the SAME rows. T31b's sample is a
# SUBSET (both starters resolved), so comparing its MAE against T31a's
# figure from the full set would be measuring the SAMPLE CHANGE, not the
# starters -- exactly the trap T30's second margin was written to catch.
tr_b = [x for x in D if x['d'] < SPLIT and 'a_er' in x]
te_b = [x for x in D if x['d'] >= SPLIT and 'a_er' in x]
print("\n" + "=" * 66)
print("T31b -- plus both starters. Bar: beat T31a by >= 0.05 MAE, SAME rows")
m_b, best_b, _, _ = report("T31b", tr_b, te_b, B)
m_a_sub, _, _, _   = report("T31a re-scored on T31b's rows", tr_b, te_b, A)
gain_b = m_a_sub - m_b
print(f"\n  T31a on these rows {m_a_sub:.4f}   T31b {m_b:.4f}")
print(f"  gain from adding both starters: {gain_b:+.4f} MAE   (bar +0.05000)")
pass_b = gain_b >= 0.05
print(f"  PRE-REGISTERED RESULT: {'PASS' if pass_b else 'FAIL'}")

print("\n" + "=" * 66)
print(f"T31a {'PASS' if pass_a else 'FAIL'}   T31b {'PASS' if pass_b else 'FAIL'}")
print("Neither is a shipping gate. T31c (vs the book) is the only one that is,")
print("and it stands at 55 of the 400 games it needs.")
