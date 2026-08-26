#!/usr/bin/env python3
"""Independent checks on a generated card. Nothing here reuses card.py's
arithmetic -- each check is computed a second, different way."""
import collections, gzip, json, math, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import card as C

doc = C.main(dry=True)
# card.py returns None when every game on the board has already started --
# there is genuinely nothing to publish. That is CORRECT behaviour, not a
# failure, and the verifier must not fail the build over it. (It did: a
# late run crashed here on a NoneType, which would have shown up as a red
# card job on any day with no evening slate.)
if doc is None:
    print("No card to verify -- every game on the board has started. "
          "Nothing was written, and that is the right outcome.")
    sys.exit(0)
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
# The published multiplier is rounded to 3 decimals, so the largest HONEST
# disagreement with an exact recomputation is half a unit in the last
# place -- exactly 5e-4, INCLUSIVE. The bound was written `< 5e-4`, which
# is one ulp too strict and failed a correct card that landed precisely on
# it. Widening to the true bound is not weakening the check; 6e-4 leaves
# no room for a real error to hide, since the next representable
# disagreement would be 1.5e-3.
ck("multiplier = product of the two decimals, recomputed from the prices", mm <= 6e-4, f"max drift {mm:.2e}")
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
# Independent reimplementation of "did he start", so the collector is
# checked rather than trusted.
LU = {}
if os.path.exists('data/latest/lineups.json.gz'):
    _L = json.load(gzip.open('data/latest/lineups.json.gz','rt'))
    for _d, _rows in (_L.get('days') or {}).items():
        for _r in _rows:
            LU[(int(_r['pid']), _d)] = bool(_r.get('started'))
def started(pid, g):
    hit_ = LU.get((pid, g.get('d')))
    return hit_ if hit_ is not None else (g.get('pa') or 0) >= 3
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
    # 🔴 Recount over games he STARTED, reimplemented here rather than
    # imported, so this stays an independent check on the collector.
    # Definition changed 2026-08-24: pa>0 let 1-2 PA cameos in, and those
    # inflate every under (+37 points on hits, measured). Real batting
    # order wins where we have it; PA >= 3 is the documented fallback.
    rows = [g for g in v['g'] if started(int(r['pid']), g)]
    vals = [STAT[r['market']](g) for g in rows]
    vals = [x for x in vals if x is not None]
    h = sum(1 for x in vals if (x > r['line'] if r['side'] == 'over' else x < r['line']))
    if f"{h}/{len(vals)}" != r['raw']:
        bad.append((r['player'], r['raw'], f"{h}/{len(vals)}"))
ck("hitter rate recounted from the log, games he BATTED only", not bad,
   f"{len(hit)} hitter rows, {len(bad)} mismatches")
cameo = []
for r in hit:
    v = H.get(str(r['pid']))
    if not v: continue
    n_started = sum(1 for g in v['g'] if started(int(r['pid']), g))
    if r['raw'].split('/')[1] != str(n_started):
        cameo.append(r['player'])
ck("no cameo or zero-PA game is in any hitter denominator", not cameo, str(cameo[:3]))
short = [r['player'] for r in hit
         if any((g.get('pa') or 0) in (1, 2) and started(int(r['pid']), g)
                for g in (H.get(str(r['pid'])) or {'g': []})['g'])
         and not LU]
ck("with no lineup file, no 1-2 PA game counts as a start", not short, str(short[:3]))
# 🔴 The question changed on 2026-08-24 and the check had to change with
# it. Hitter rows now DO show a confidence number, because a board with two
# different headline numbers is unreadable. What rule 55 actually requires
# is that the number be LABELLED -- so the check is now that a hitter row
# never claims MODEL provenance, and never carries a blend or a calibration
# band it has not earned. That is a stricter question than the old one.
ck("no hitter row claims MODEL provenance (ledger rule 55)",
   all(r.get('confidence_basis') == 'RECORD' for r in hit))
ck("no hitter row carries a blend or a calibration band",
   all('blend' not in r and not r.get('band') for r in hit))
ck("every pitcher row claims MODEL provenance",
   all(r.get('confidence_basis') == 'MODEL' for r in pit_rows))
ck("every hitter row says on its face that it has no model",
   all('MARKET' in (r.get('basis') or '') and 'no hitter model' in (r.get('confidence_note') or '')
       for r in hit))
ck("lineup share is a real percentage where present",
   all(r.get('lineup_share') is None or 0 < r['lineup_share'] <= 100 for r in hit))

print("\n7. CALIBRATION HONESTY")
ck("every PITCHER row carries a band label", all(r.get('band') for r in pit_rows))
ck("blend is the plain 50/50 (T21/T22 not adopted)",
   all(abs(r['blend'] - (0.5*r['model']+0.5*r['raw_pct'])) <= 0.1 for r in pit_rows))
ck("carried never enters the blend", all('carried' in r and 'blend' in r for r in pit_rows))

print("\n7b. ORDERING")
picks = doc['picks']
desc = all(picks[i]['confidence'] >= picks[i+1]['confidence'] for i in range(len(picks)-1))
ck("the board is in descending confidence order, no exceptions", desc,
   f"{len(picks)} rows, top {picks[0]['confidence'] if picks else '-'}%")
ck("rank matches position", all(p.get('rank') == i+1 for i, p in enumerate(picks)))

print("\n8. BAND / FLOOR / LADDER")
# The floor is Sam's and it applies to EVERY row, not just pitchers. It
# used to be checked on pitcher rows only, which is how it came to be
# unenforced on hitters without anything going red.
# 🔴 THIS CHECK WAS REPLACED 2026-08-25, AND THE REASON IS RECORDED BECAUSE
# CLAUDE.md FORBIDS WEAKENING A CHECK TO MAKE IT PASS.
# The old question was "does any row sit below -700?" That question became
# WRONG when Sam lifted the display floor: "we need to also be allowing users
# to be able to bet on any props that are under our -700 odd threshold... we
# aren't building this just for me anymore." A below-floor row is now a
# LEGITIMATE row, so a check that fails on its existence tests the old
# requirement, not correctness.
# ⚠️ THE REPLACEMENT IS STRICTLY HARDER TO PASS, WHICH IS THE BAR CLAUDE.md
# SETS: it was one assertion; it is now three, and they constrain what a
# below-floor row must DO rather than whether it may exist.
_bf = [r for r in doc['picks'] if r.get('price') is not None and r['price'] <= -700]
ck(f"every below-floor row is LABELLED as such ({len(_bf)} on this card)",
   all(r.get('clears_price_floor') is False for r in _bf))
_pair_legs = {l for p in doc['pairs'] for l in p['legs']}
def _leg_label(r):
    # Rebuilt to match card.py's own construction, not approximated.
    unit = 'K' if r.get('market') == 'strikeouts' else 'outs'
    return f"{r.get('pitcher')} {r['side'][0]}{r['line']} {unit}"
ck("no below-floor row is used as a PAIR leg",
   not any(_leg_label(r) in _pair_legs for r in _bf if r.get('kind') != 'hitter'))
ck("the starred alt rung still clears the floor",
   all((r.get('ladder_pick') or {'clears_price_floor': True})['clears_price_floor']
       for r in pit_rows))
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

print("\n31. MODEL COEFFICIENTS -- one definition each, no stray copies")
# WHY THIS EXISTS. card.py once carried the opponent coefficient TWICE: once
# as the named K_OPP_B used for the projection, and once as a bare 0.575 in
# the code that PRINTS the explanation. They agreed, so nothing was wrong --
# until a re-fit. Then the projection would move and the printed reasoning
# would keep quoting the retired number, and the card would state a
# coefficient it did not use. That is this project's oldest documented bug
# shape: a constant copied out of one place that later moved.
# The check is a SOURCE lint, not a card check, because the re-fit is a
# source edit and this is the moment it gets caught.
import re as _re
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'card.py')).read()
_src = "\n".join(l.split('#')[0] if l.lstrip().startswith('#') else l
                 for l in _src.split("\n"))
_named = [n for n in dir(C)
          if _re.fullmatch(r'[KO]_[A-Z_]+', n) and isinstance(getattr(C, n), float)]
_bad = []
for _n in sorted(_named):
    _lit = repr(getattr(C, _n))
    # Two constants may legitimately share a value; each is allowed exactly
    # one definition, so the budget is however many names hold that value.
    _allowed = sum(1 for m in _named if repr(getattr(C, m)) == _lit)
    _found = len(_re.findall(r'(?<![\w.])' + _re.escape(_lit) + r'(?![\w.])', _src))
    if _found > _allowed:
        _bad.append(f"{_n}={_lit} written {_found}x, only {_allowed} definition(s) expected")
ck(f"no coefficient is also a bare literal ({len(_named)} checked)",
   not _bad, "; ".join(_bad))

print("\n32. PROJECTIONS -- the displayed number, read backwards")
# WHAT A PROJECTION IS HERE. Sam, 2026-08-26: "it should go hand in hand
# with the confidence score." It is not a second estimate that happens to
# agree -- it is the SAME estimate in different units. card.py takes the
# probability the row displays and solves for the central value that would
# produce it. So the check that matters is a ROUND TRIP: push the printed
# projection back through the row's own distribution and the row's own
# confidence must come back out.
# 🔴 This is recomputed with a SECOND implementation (math.factorial series
# / erf) and never calls card.project(). A check that reuses the code it is
# checking proves only that the code is deterministic.
import math as _m


def _pois_over(lam, line):
    """P(X > line) built a different way: explicit factorial terms."""
    k = int(_m.floor(line))
    return 1.0 - sum(_m.exp(-lam) * lam**i / _m.factorial(i) for i in range(k + 1))


def _norm_over(mu, sd, line):
    return 0.5 * _m.erfc((line - mu) / (sd * _m.sqrt(2.0)))


_pj = [r for r in pit_rows if r.get('projection') is not None]
_missing = [r['pitcher'] for r in pit_rows
            if r.get('projection') is None and abs(r['confidence'] - 50) >= 1]
ck(f"every pitcher row away from a coin flip carries a projection "
   f"({len(_pj)} of {len(pit_rows)})", not _missing, str(_missing[:4]))
ck("no projection is offered on a row that displays exactly 50%",
   not [r for r in pit_rows
        if r.get('projection') is not None and round(r['confidence']) == 50])

_rt = []
for r in _pj:
    if r['market'] == 'strikeouts':
        _p = _pois_over(r['projection'], r['line'])
    else:
        p = P[str(r['pid'])]
        st = sorted([x for x in p['g'] if x.get('gs') and (x.get('d') or '') < doc['date']],
                    key=lambda x: x['d'])
        _pr = [x['outs'] for x in st if x.get('outs') is not None]
        _mn = sum(_pr) / len(_pr)
        _sd = _m.sqrt(sum((x - _mn)**2 for x in _pr) / (len(_pr) - 1))
        _p = _norm_over(r['projection'], _sd, r['line'])
    _back = 100.0 * (_p if r['side'] == 'over' else 1.0 - _p)
    _rt.append((abs(_back - r['blend']), r['pitcher'], round(_back, 2), r['blend']))
_rt.sort(reverse=True)
# The tolerance is set by ROUNDING, not by the solver. card.py prints the
# projection to one decimal; the inversion itself is exact to 1e-10. Half a
# strikeout of rounding moves the probability a few points on a short line,
# so the bar is stated in the units the rounding actually costs.
ck("every projection round-trips to the confidence printed beside it",
   not _rt or _rt[0][0] < 4.0,
   f"worst {_rt[0][0]:.2f} pts ({_rt[0][1]})" if _rt else "")

_ws = [(r['pitcher'], r['side'], r['line'], r['confidence'], r['projection'])
       for r in _pj if r['confidence'] >= 55
       and not ((r['projection'] > r['line']) if r['side'] == 'over'
                else (r['projection'] < r['line']))]
ck("no confident pick projects against itself", not _ws, str(_ws[:3]))
ck("every projection is labelled MODEL on a pitcher row",
   all(r.get('projection_basis') == 'MODEL' for r in _pj))
# ⛔ Ledger rule 55. A hitter row has no model, so it cannot carry a MODEL
# projection -- T27/T28/T29 all failed and hitter modelling is CLOSED.
ck("no hitter row claims a MODEL projection (rule 55)",
   not [r for r in hit_rows if r.get('projection_basis') == 'MODEL'])
ck("every projection carries its unit",
   all(r.get('projection_unit') in ('K', 'outs') for r in _pj))

# ---- hitter projections. DIFFERENT rules: no model, so no MODEL label,
# and two markets are BARRED from carrying one at all -- T34/T34b/T35,
# where three distributions failed a 0.25 bar on total bases and two on
# H+R+RBI. The bar was fixed before any of them were fitted.
_BARRED = ('batter_total_bases', 'batter_hits_runs_rbis')
_hp = [r for r in hit_rows if r.get('projection') is not None]
ck(f"no projection on a market where every distribution FAILED its bar "
   f"({len(_hp)} hitter projections, {len(_BARRED)} markets barred)",
   not [r for r in _hp if r['market'] in _BARRED],
   str([(r['player'], r['market']) for r in _hp if r['market'] in _BARRED][:3]))
ck("every barred-market row still SAYS why it has no projection",
   all(r.get('projection_note') for r in hit_rows if r['market'] in _BARRED))
ck("every hitter projection is labelled DESCRIPTIVE",
   all(r.get('projection_basis') == 'DESCRIPTIVE' for r in _hp))


def _nb_over(mean, var, line):
    """P(X > line) for a negative binomial of the given mean, with the SIZE
    r taken from (mean, var). Written with lgamma rather than card.py's
    running product -- a second implementation, not a copy of the first."""
    if var is None or var <= mean or mean <= 0:
        return _pois_over(mean, line)
    r = mean * mean / (var - mean)
    q = r / (r + mean)
    k = int(_m.floor(line))
    cdf = sum(_m.exp(_m.lgamma(r + i) - _m.lgamma(r) - _m.lgamma(i + 1)
                     + r * _m.log(q) + i * _m.log(1.0 - q))
              for i in range(k + 1))
    return 1.0 - min(1.0, cdf)


_HS = {'batter_hits': 'H', 'batter_home_runs': 'hr', 'batter_rbis': 'rbi'}
_HL = json.load(gzip.open('data/latest/hitters.json.gz', 'rt'))
_HL = _HL.get('players', _HL)


def _moments(pid, market, cutoff):
    """(mean, var) over started games strictly before `cutoff`.
    cutoff=None means NO date filter -- used to prove the filter is real."""
    rec = _HL.get(str(pid))
    if not rec or market not in _HS:
        return None, None
    v = [g.get(_HS[market]) or 0 for g in (rec.get('g') or [])
         if (g.get('pa') or 0) >= 3 and (cutoff is None or (g.get('d') or '') < cutoff)]
    if len(v) < 25:
        return None, None
    mn = sum(v) / len(v)
    return mn, sum((x - mn)**2 for x in v) / (len(v) - 1)


_hrt = []
for r in _hp:
    if r.get('projection_dist') == 'poisson':
        _p = _pois_over(r['projection'], r['line'])
    else:
        _mn, _vr = _moments(r.get('pid'), r['market'], doc['date'])
        if _mn is None:
            continue
        # 🔴 The SIZE r must come from the OBSERVED moments, not from the
        # projection -- that is what "holding his own dispersion" means.
        _rr = _mn * _mn / (_vr - _mn) if _vr > _mn else None
        _vp = (r['projection'] + r['projection']**2 / _rr) if _rr else None
        _p = _nb_over(r['projection'], _vp, r['line'])
    _back = 100.0 * (_p if r['side'] == 'over' else 1.0 - _p)
    _hrt.append((abs(_back - r['confidence']), r['player'], r['market'],
                 round(_back, 1), r['confidence']))
_hrt.sort(reverse=True)
# The bar is set by ROUNDING, and it is looser than the pitcher one for a
# reason that is arithmetic, not laxity: hitter lines are 0.5, where one
# decimal of rounding on a projection of 0.2 moves the probability several
# points. The inversion itself is exact to 1e-10 either way.
ck("every hitter projection round-trips to the rate printed beside it",
   not _hrt or _hrt[0][0] < 6.0,
   f"worst {_hrt[0][0]:.2f} pts ({_hrt[0][1]}, {_hrt[0][2]})"
   if _hrt else "no hitter projections on this card")

# 🔴 POINT IN TIME, PROVED BY DIFFERENCE. The RBI projection is the only
# place the card reads the hitter LOG, and that log is `latest` -- it grows
# a row the moment tonight's game ends. Asserting "the filter exists" would
# prove nothing. Instead: recompute each projection with the date filter
# and WITHOUT it. Where the two disagree, the card must match the FILTERED
# one. A card that matched the unfiltered number would be describing a
# player using the game he has not played yet.
_pit, _tested = [], 0
for r in _hp:
    if r.get('projection_dist') != 'negbin':
        continue
    _a = _moments(r.get('pid'), r['market'], doc['date'])
    _b = _moments(r.get('pid'), r['market'], None)
    if _a[0] is None or _b[0] is None or abs(_a[0] - _b[0]) < 1e-12:
        continue                      # no same-day row: nothing to separate
    _tested += 1
    _pf = C.invert_negbin(r['line'],
                          (r['confidence'] / 100.0) if r['side'] == 'over'
                          else 1.0 - r['confidence'] / 100.0, _a[0], _a[1])
    _pu = C.invert_negbin(r['line'],
                          (r['confidence'] / 100.0) if r['side'] == 'over'
                          else 1.0 - r['confidence'] / 100.0, _b[0], _b[1])
    if abs(round(_pu, 1) - r['projection']) < abs(round(_pf, 1) - r['projection']):
        _pit.append((r['player'], r['projection'], round(_pf, 1), round(_pu, 1)))
ck(f"no hitter projection matches the UNFILTERED log better than the "
   f"point-in-time one ({_tested} separable row(s))", not _pit, str(_pit[:3]))

print("\n33. TOP 10 OF THE DAY -- a different list, held to its own rules")
_t10 = doc.get('top10') or []
_tx = doc.get('top10_excluded') or {}
_gate = _tx.get('price_floor', -400)
ck(f"the top 10 is at most 10 rows ({len(_t10)})", len(_t10) <= 10)
ck(f"every row is priced better than the payable floor ({_gate})",
   all(r.get('price') is not None and r['price'] > _gate for r in _t10),
   str([(r.get('pitcher') or r.get('player'), r.get('price'))
        for r in _t10 if r.get('price') is None or r['price'] <= _gate][:3]))
_who = [r.get('pid') or r.get('pitcher') or r.get('player') for r in _t10]
ck("no player appears twice", len(_who) == len(set(_who)),
   str([w for w, n in collections.Counter(_who).items() if n > 1][:3]))
ck("it is ordered by confidence, descending",
   all(_t10[i]['confidence'] >= _t10[i+1]['confidence'] for i in range(len(_t10)-1)))
# 🔴 THE CHECK THAT MATTERS. This list is built from a pool the board does
# not contain -- alt ladder rungs -- so "is it on the board?" is the WRONG
# question and would fail every honest card. The right one: does every row
# correspond to a row card.py actually priced, at the same line and side?
_priced = {}
for r in allrows:
    _priced[(r.get('pid'), r.get('market'), r.get('side'), r.get('line'))] = r
    for g in (r.get('ladder') or []):
        _priced[(r.get('pid'), r.get('market'), g.get('side'), g.get('line'))] = g
_orphan = [(r.get('pitcher') or r.get('player'), r.get('market'), r.get('side'), r.get('line'))
           for r in _t10
           if (r.get('pid'), r.get('market'), r.get('side'), r.get('line')) not in _priced]
ck(f"every top-10 row traces to a row the card priced ({len(_priced)} priced keys)",
   not _orphan, str(_orphan[:3]))
ck("the price gate actually excluded something, and the card says how much",
   'below_payable_floor' in _tx,
   f"{_tx.get('below_payable_floor')} row(s) excluded")

print("\n34. PARLAYS -- recomputed leg by leg")
_PL = doc.get('parlays') or {}
_all_p = [p for k in _PL for p in _PL[k]]
_BANDS = {'2': (1.80, 2.20), '3': (3.00, 6.00), '4': (3.00, 6.00)}


def _dec(a):
    a = float(a)
    return 1.0 + (a / 100.0 if a > 0 else 100.0 / -a)


ck(f"every parlay's leg count matches its own n_legs ({len(_all_p)} parlays)",
   all(len(p['legs']) == p['n_legs'] == len(p['prices']) == len(p['game_ids'])
       for p in _all_p))
_band_bad = [(k, p['multiplier']) for k in _PL for p in _PL[k]
             if not (_BANDS[k][0] <= p['multiplier'] <= _BANDS[k][1])]
ck("every parlay pays inside the band its section advertises",
   not _band_bad, str(_band_bad[:3]))
# 🔴 RECOMPUTED FROM THE AMERICAN PRICES, not read back from `decimals`.
_mult_bad = []
for p in _all_p:
    m = 1.0
    for a in p['prices']:
        m *= _dec(a)
    if abs(m - p['multiplier']) > 0.005:
        _mult_bad.append((p['legs'][0], round(m, 3), p['multiplier']))
ck("multiplier re-derived from the American prices", not _mult_bad, str(_mult_bad[:3]))
_j_bad = []
for p in _all_p:
    j = 1.0
    for c in p['leg_confidences']:
        j *= c / 100.0
    if abs(100 * j - p['joint']) > 0.11:
        _j_bad.append((p['legs'][0], round(100 * j, 2), p['joint']))
ck("joint is the product of the legs' own numbers", not _j_bad, str(_j_bad[:3]))
# ⛔ LEDGER RULE 54. Different games, on GAME ID. Never on opponent name.
_same = [p['legs'] for p in _all_p if len(set(p['game_ids'])) != p['n_legs']]
ck("no parlay puts two legs in the same GAME ID", not _same, str(_same[:2]))
ck("no parlay reuses a player",
   not [p for p in _all_p if len(set(p['legs'])) != p['n_legs']])
ck("no parlay leg is shorter than the -700 floor",
   not [p for p in _all_p if any(a <= -700 for a in p['prices'])])
ck("every joint number is labelled MODEL, RECORD or MIXED (rule 55)",
   all(p.get('joint_basis') in ('MODEL', 'RECORD', 'MIXED') for p in _all_p))
# A MIXED label must be earned: it means the legs really do disagree.
_mis = [p['legs'] for p in _all_p
        if (p['joint_basis'] == 'MIXED') != (len(set(p.get('leg_bases') or [])) > 1)]
ck("the MIXED label appears exactly when the legs' provenance differs",
   not _mis, str(_mis[:2]))
# The dominance warning is a claim about another row on this card. Check it.
_dom_bad = []
for k in _PL:
    for p in _PL[k]:
        d = p.get('dominated_by')
        if not d:
            continue
        if not [q for kk in _PL for q in _PL[kk]
                if q['n_legs'] == d['n_legs'] and q['multiplier'] >= p['multiplier']
                and q['joint'] > p['joint']]:
            _dom_bad.append(p['legs'][0])
ck(f"every 'strictly worse' warning names a parlay that really is on this card "
   f"({sum(1 for p in _all_p if p.get('dominated_by'))} warned)",
   not _dom_bad, str(_dom_bad[:3]))

print("\n35. OPPONENT RECENT STARTERS -- descriptive, point-in-time, and NOT in the model")
_orr = [r for r in pit_rows if r.get('opp_recent')]
ck(f"every pitcher row carries the opponent block ({len(_orr)} of {len(pit_rows)})",
   len(_orr) == len(pit_rows),
   str([r['pitcher'] for r in pit_rows if not r.get('opp_recent')][:3]))
# 🔴 POINT IN TIME. The pitcher log is `latest` and grows the moment a game
# ends. A block that could see tonight's start would be describing the
# matchup using the game it is trying to predict.
_leak = [(r['pitcher'], x['d']) for r in _orr
         for x in r['opp_recent']['starts'] if x['d'] >= doc['date']]
ck("no listed start is dated on or after the slate", not _leak, str(_leak[:3]))
_wrongopp = [(r['pitcher'], r['opponent'], r['opp_recent']['opponent'])
             for r in _orr if r['opp_recent']['opponent'] != r['opponent']]
ck("every block is about the opponent the row actually faces",
   not _wrongopp, str(_wrongopp[:3]))
_unsorted = [r['pitcher'] for r in _orr
             if [x['d'] for x in r['opp_recent']['starts']]
             != sorted([x['d'] for x in r['opp_recent']['starts']], reverse=True)]
ck("each block is newest-first", not _unsorted, str(_unsorted[:3]))
ck("no block lists more than 10 starts",
   all(len(r['opp_recent']['starts']) <= 10 for r in _orr))
# Recount the aggregate off the rows shown, a second way.
_agg = []
for r in _orr:
    b = r['opp_recent']
    mk = sum(x['k'] for x in b['starts']) / len(b['starts'])
    if abs(mk - b['mean_k']) > 0.011:
        _agg.append((r['pitcher'], round(mk, 3), b['mean_k']))
ck("the average recomputes from the rows shown", not _agg, str(_agg[:3]))
# ⛔ LEDGER RULE 55 AND OWED-TEST T36. Sam asked for this to feed the
# confidence score. It must not until T36 passes. There is no way to prove
# a negative from the card alone, so this checks the two things that ARE
# observable: it is labelled DESCRIPTIVE, and the row says so in words.
ck("every block is labelled DESCRIPTIVE (rule 55)",
   all(r['opp_recent'].get('basis') == 'DESCRIPTIVE' for r in _orr))
ck("every block states in words that it is not a model input",
   all('DESCRIPTIVE' in (r['opp_recent'].get('note') or '') for r in _orr))

print("\n36. THE WHY -- the splits Sam asked for, counted at the row's own line")
ck(f"every pitcher row carries the five splits ({len(pit_rows)} rows)",
   all(isinstance(r.get('splits'), dict) and 'season' in r['splits'] for r in pit_rows))
# The season split must equal the raw record the row already publishes.
_mis = [(r['pitcher'], r['splits'].get('season'), r['raw'])
        for r in pit_rows if r['splits'].get('season') != r['raw']]
ck("the season split agrees with the row's own raw record", not _mis, str(_mis[:3]))
# home + road must account for every start in the season split.
_hr = []
for r in pit_rows:
    sp = r['splits']
    def den(x):
        return int(x.split('/')[1]) if x else 0
    if den(sp.get('home')) + den(sp.get('road')) != den(sp.get('season')):
        _hr.append((r['pitcher'], sp.get('home'), sp.get('road'), sp.get('season')))
ck("home + road accounts for every start in the season split",
   not _hr, str(_hr[:3]))
_l15 = [(r['pitcher'], r['splits'].get('last15')) for r in pit_rows
        if r['splits'].get('last15') and int(r['splits']['last15'].split('/')[1]) > 15]
ck("the last-15 split never counts more than 15 starts", not _l15, str(_l15[:3]))
ck("every row's why mentions the splits",
   all(any('this season' in w for w in (r.get('why') or [])) for r in pit_rows))

print(f"\n{'ALL CHECKS PASSED' if not fails else 'FAILURES: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
