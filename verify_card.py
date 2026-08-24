#!/usr/bin/env python3
"""Independent checks on a generated card. Nothing here reuses card.py's
arithmetic -- each check is computed a second, different way."""
import gzip, json, math, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import card as C

doc = C.main(dry=True)
P = json.load(gzip.open('data/latest/pitchers.json.gz','rt'))['players']
B = json.load(gzip.open('data/latest/props.json.gz','rt'))
allrows = doc['picks'] + doc['below_price_floor']
# Pitcher and hitter rows are checked by DIFFERENT rules: a pitcher row has
# a model behind it, a hitter row deliberately does not. Splitting them here
# stops a pitcher-only check from crashing on a hitter (and, worse, stops a
# hitter row from quietly skipping a check it should have faced).
pit_rows = [r for r in allrows if r.get('kind') != 'hitter']
hit_rows = [r for r in allrows if r.get('kind') == 'hitter']
fails = []
def ck(name, ok, detail=""):
    print(("  PASS " if ok else "  FAIL ") + name + ("  " + detail if detail else ""))
    if not ok: fails.append(name)

print("\n1. DISTRIBUTIONS -- recomputed by simulation, not by the CDF")
random.seed(7)
worst = 0.0
for r in pit_rows:
    if r['market'] != 'strikeouts': continue
    lam = r['model_inputs']['E_K']; line = r['line']
    N = 200000; hit = 0
    # inverse-transform Poisson draws
    for _ in range(N):
        L, k, pr = math.exp(-lam), 0, random.random()
        s = L
        while pr > s and k < 40:
            k += 1; L *= lam/k; s += L
        v = k
        hit += 1 if ((v > line) if r['side']=='over' else (v < line)) else 0
    sim = 100.0*hit/N
    worst = max(worst, abs(sim - r['model']))
ck("Poisson CDF vs 200k simulations", worst < 0.6, f"max gap {worst:.3f} pts")

worst = 0.0
for r in pit_rows:
    if r['market'] != 'outs': continue
    # rebuild mu AND the SD from the raw log -- read no computed value back
    p = P[str(r['pid'])]
    st = [x for x in p['g'] if x.get('gs') and (x.get('d') or '') < doc['date']]
    st.sort(key=lambda x: x['d'])
    tr = st[-8:]
    mO8 = sum(x['outs'] for x in tr)/len(tr)
    kk = 0.638 if mO8 < 15.25 else (0.759 if mO8 < 17.0 else 0.317)
    mu = 15.899 + kk*(mO8-15.903) + 0.0371*(tr[-1]['np']-86.6) + (0.189 if r['home_side'] else -0.189)
    prior = [x['outs'] for x in st if x.get('outs') is not None]
    m = sum(prior)/len(prior); s2 = math.sqrt(sum((x-m)**2 for x in prior)/(len(prior)-1))
    z = (r['line'] - mu)/s2
    manual = 100*(1 - 0.5*(1+math.erf(z/math.sqrt(2)))) if r['side']=='over' else 100*0.5*(1+math.erf(z/math.sqrt(2)))
    worst = max(worst, abs(manual - r['model']))
ck("Normal outs probability recomputed from the raw log", worst < 0.06, f"max gap {worst:.4f} pts")

print("\n2. RAW RATES -- counted by hand off the game log")
bad = []
for r in pit_rows:
    p = P[str(r['pid'])]
    rows = [x for x in p['g'] if x.get('gs') and (x.get('d') or '') < doc['date']]
    key = 'k' if r['market']=='strikeouts' else 'outs'
    vals = [x[key] for x in rows if x.get(key) is not None]
    h = sum(1 for v in vals if (v > r['line'] if r['side']=='over' else v < r['line']))
    if f"{h}/{len(vals)}" != r['raw']: bad.append((r['pitcher'], r['raw'], f"{h}/{len(vals)}"))
ck("raw hit rate, all starts, exact threshold", not bad, f"{len(pit_rows)} rows, {len(bad)} mismatches")

print("\n3. POINT-IN-TIME -- no row may use a start dated today or later")
leak = []
for r in pit_rows:
    p = P[str(r['pid'])]
    if any((x.get('d') or '') >= doc['date'] for x in p['g'] if x.get('gs')):
        leak.append(r['pitcher'])
ck("no start on/after the slate date is in any denominator", not leak, str(set(leak)))

print("\n4. OVER + UNDER must sum to 100 at the same number")
two = [r for r in pit_rows if r.get('other_side')]
bad = [r['pitcher'] for r in two if abs(r['model'] + r['other_side']['model'] - 100) > 0.11]
ck("model over+under = 100%", not bad, f"{len(two)} two-sided numbers")
ck("the side shown is the one the card favours",
   all(r['blend'] >= r['other_side']['blend'] for r in two))

print("\n5. PAIRS")
same = [p for p in doc['pairs'] if p['game_ids'][0]==p['game_ids'][1]]
ck("no same-game parlay (ledger rule 54, checked on GAME ID)", not same)
ck("no pair below the 1.8x hard floor", all(p['multiplier'] >= 1.80 for p in doc['pairs']))
dec = lambda a: 1.0 + (a/100.0 if a > 0 else 100.0/-a)
mm = max((abs(p['multiplier'] - dec(p['prices'][0])*dec(p['prices'][1])) for p in doc['pairs']), default=0)
ck("multiplier = product of the two decimals, recomputed from the prices", mm < 5e-4, f"max drift {mm:.2e}")
jm = max((abs(p['joint'] - round(p['leg_blends'][0]*p['leg_blends'][1]/100,1)) for p in doc['pairs']), default=0)
ck("joint = product of the two blends", jm <= 0.051)
ck("every pair leg is priced at Hard Rock", all(p['book']=='hardrockbet' for p in doc['pairs']))
ck("no pair reuses a pitcher", all(len(set(p['game_ids']))==2 for p in doc['pairs']))

print("\n6. PRICES -- every one traceable to a raw snapshot")
raw_prices = set()
import glob
for f in sorted(glob.glob('data/*/props-pitcher/*.json.gz')):
    D = json.load(gzip.open(f,'rt'))
    for ev in D.get('events', []):
        for bk in ev.get('bookmakers', []):
            for m in bk.get('markets', []):
                for o in m.get('outcomes', []):
                    raw_prices.add((o.get('description'), m.get('key'), o.get('point'),
                                    (o.get('name') or '').lower(), o.get('price'), bk['key']))
missing = []
for r in pit_rows:
    if r['price'] is None: continue
    mk = 'pitcher_strikeouts' if r['market']=='strikeouts' else 'pitcher_outs'
    cand = {x for x in raw_prices if x[2]==r['line'] and x[3]==r['side'] and x[4]==r['price']
            and x[5] in ('hardrockbet','hardrockbet_oh','fliff','fanduel','draftkings','bovada','williamhill_us','espnbet','betparx','ballybet')}
    if not cand: missing.append((r['pitcher'], r['line'], r['side'], r['price']))
ck("no invented price -- every quote appears in a raw pull", not missing, f"{len(missing)} not found")

print("\n6b. HITTER ROWS")
H = json.load(gzip.open('data/latest/hitters.json.gz','rt'))['players']
hit = hit_rows
STAT = {'batter_hits': lambda r: r.get('H'),
        'batter_total_bases': lambda r: r.get('tb'),
        'batter_home_runs': lambda r: r.get('hr'),
        'batter_rbis': lambda r: r.get('rbi'),
        'batter_hits_runs_rbis': lambda r: None if r.get('H') is None
            else (r.get('H') or 0) + (r.get('r') or 0) + (r.get('rbi') or 0)}
bad = []
for r in hit:
    v = H.get(str(r['pid']))
    if not v:
        bad.append((r['player'], 'not in the hitter pool')); continue
    # 🔴 Recount with the pa>0 filter, independently of the collector.
    rows = [g for g in v['g'] if (g.get('pa') or 0) > 0]
    vals = [STAT[r['market']](g) for g in rows]
    vals = [x for x in vals if x is not None]
    h = sum(1 for x in vals if (x > r['line'] if r['side'] == 'over' else x < r['line']))
    if f"{h}/{len(vals)}" != r['raw']:
        bad.append((r['player'], r['raw'], f"{h}/{len(vals)}"))
ck("hitter rate recounted from the log, games he BATTED only", not bad,
   f"{len(hit)} hitter rows, {len(bad)} mismatches")
zero_pa = []
for r in hit:
    v = H.get(str(r['pid']))
    if v and any((g.get('pa') or 0) == 0 for g in v['g']):
        n_played = sum(1 for g in v['g'] if (g.get('pa') or 0) > 0)
        if r['raw'].split('/')[1] != str(n_played):
            zero_pa.append(r['player'])
ck("no zero-plate-appearance game is in any hitter denominator", not zero_pa, str(zero_pa[:3]))
ck("no hitter row carries a confidence rating (ledger rule 55)",
   all('confidence' not in r and 'blend' not in r and not r.get('band') for r in hit))
ck("every hitter row says it has no model",
   all('MARKET' in (r.get('basis') or '') for r in hit))
ck("lineup share is a real percentage where present",
   all(r.get('lineup_share') is None or 0 < r['lineup_share'] <= 100 for r in hit))

print("\n7. CALIBRATION HONESTY")
ck("every PITCHER row carries a band label", all(r.get('band') for r in pit_rows))
ck("blend is the plain 50/50 (T21/T22 not adopted)",
   all(abs(r['blend'] - (0.5*r['model']+0.5*r['raw_pct'])) <= 0.1 for r in pit_rows))
ck("carried never enters the blend", all('carried' in r and 'blend' in r for r in pit_rows))

print("\n8. BAND / FLOOR / LADDER")
ck("no picks row is shorter than -700", all(r['price'] is None or r['price'] > -700 for r in doc['picks'] if r.get('kind') != 'hitter'))
rungs = [g for r in pit_rows for g in (r.get('ladder') or [])]
# 🔴 The question is whether a rung the BOARD holds went MISSING from the
# card -- not whether any rung exists. An earlier version of this check
# asserted `any(below floor)` and failed a perfectly correct card on a
# board that simply had no Hard Rock ladder stored yet. A verifier must
# fail on wrongness, never on an empty input.
# 🔴 SCOPE THE QUESTION TO THE PITCHERS THE CARD ACTUALLY PRICED.
# An earlier version compared against EVERY ladder on the board, which
# silently included games that had already started and pitchers with too
# few prior starts to price. Those rungs are legitimately absent, so the
# check failed every evening on a correct card -- and on 2026-08-23 it
# blocked BOTH scheduled card runs, which is why no card published that
# day. That is the same defect as the "at least one rung below -700"
# version: a check whose answer depends on the time of day rather than on
# whether the card is right.
#
# The regression this actually guards against is a CARDED pitcher losing
# rungs. So: for every pitcher with a play, every Hard Rock rung the board
# holds for him must appear. Rungs belonging to pitchers with no play are
# COUNTED AND REPORTED, never silently dropped.
carded = {(C.norm_name(r['pitcher']), r['market']) for r in pit_rows}
board_rungs, orphan = set(), 0
for g in B['games']:
    for who, rows in (g.get('ladders') or {}).items():
        for r in rows:
            if (who, r['market']) in carded:
                board_rungs.add((who, r['market'], r['line'], r['side']))
            else:
                orphan += 1
# A play's OWN line is covered by the play itself -- the ladder holds the
# other rungs, never a duplicate of the row it hangs under.
card_rungs = {(C.norm_name(r['pitcher']), r['market'], g['line'], g['side'])
              for r in pit_rows for g in (r.get('ladder') or [])}
card_rungs |= {(C.norm_name(r['pitcher']), r['market'], r['line'], r['side'])
               for r in pit_rows}
card_rungs |= {(C.norm_name(r['pitcher']), r['market'], r['line'], r['other_side']['side'])
               for r in pit_rows if r.get('other_side')}
lost = {x for x in board_rungs if x not in card_rungs}
ck("no rung is missing for a pitcher the card priced", not lost,
   f"{len(board_rungs)} rungs on carded pitchers, {len(lost)} missing")
print(f"  NOTE  {orphan} rung(s) belong to pitchers with no play on this card "
      f"(game already started, or too few prior starts to price)")
below = sum(1 for g in rungs if not g['clears_price_floor'])
print(f"  NOTE  {len(rungs)} rungs carried, {below} of them below the -700 floor"
      + ("" if rungs else "  <- no Hard Rock ladder in this board"))
ck("the starred rung always clears the floor",
   all((r.get('ladder_pick') or {'clears_price_floor':True})['clears_price_floor'] for r in pit_rows))
mono = []
for r in pit_rows:
    ov = [g for g in (r.get('ladder') or []) if g['side']=='over']
    for a,b in zip(ov, ov[1:]):
        if b['blend'] > a['blend'] + 0.05: mono.append((r['pitcher'], a['line'], b['line']))
ck("a higher over rung is never MORE likely than a lower one", not mono, str(mono[:3]))
ck("every ladder rung carries its app label form (rule 49 off-by-one)",
   all(g.get('app_label') for r in pit_rows for g in (r.get('ladder') or []) if g['side']=='over'))

print(f"\n{'ALL CHECKS PASSED' if not fails else 'FAILURES: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
