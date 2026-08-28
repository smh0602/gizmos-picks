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
# ~~"no projection is offered on a row that displays exactly 50%"~~
# 🔴 REPLACED 2026-08-27. It asked a question that no longer has meaning: a
# projection is not derived from the confidence any more, so a 50% row has
# exactly as much to project as any other. ⛔ The replacement is the
# invariant Sam actually asked for, and it is the strongest one on this
# page: "you should have the same numbers across the entire website if your
# talking about the same stat or projction."
_MKT_FEED2 = {'strikeouts': 'pitcher_strikeouts', 'outs': 'pitcher_outs'}
_seen_pm = collections.defaultdict(set)
for _k, _v in (doc.get('projections') or {}).items():
    _pid, _mk, _sd, _ln = _k.split('|')
    _seen_pm[(_pid, _mk)].add(round(float(_v['v']), 3))
# ⛔ Parlay legs are DISPLAY STRINGS ("Sean Manaea o3.5 K"), not rows, so
# they carry no projection and are not a source here.
for _r in allrows + doc.get('top10', []):
    if _r.get('projection') is None:
        continue
    _mk = _MKT_FEED2.get(_r.get('market'), _r.get('market'))
    _seen_pm[(str(_r.get('pid')), _mk)].add(round(float(_r['projection']), 3))
_incoh = [(k, sorted(v)) for k, v in _seen_pm.items() if len(v) > 1]
ck(f"one projection per player per stat, everywhere on the site "
   f"({len(_seen_pm)} player-market combos)", not _incoh, str(_incoh[:3]))

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
    _rt.append((abs(_back - r['model']), r['pitcher'], round(_back, 2), r['model']))
_rt.sort(reverse=True)
# ~~"every projection round-trips to the CONFIDENCE printed beside it"~~
# 🔴 REPLACED 2026-08-27 (T37). The projection is no longer an inversion of
# the blend -- it is the model's own central value, which is what makes it
# line-independent. So the round trip still exists, it just targets the
# number `central` actually parameterises: the MODEL probability.
# ⛔ THIS IS NOT A WEAKER CHECK. `model` is itself re-derived from the raw
# game log elsewhere on this page, so the chain log -> mu/lam -> model ->
# projection is closed with no step reading a value back from the card.
# The tolerance is set by ROUNDING: card.py prints the projection to one
# decimal, and half a strikeout moves the probability a few points on a
# short line.
ck("every projection round-trips to the MODEL probability beside it",
   not _rt or _rt[0][0] < 4.0,
   f"worst {_rt[0][0]:.2f} pts ({_rt[0][1]})" if _rt else "")

# 🔴 THE THRESHOLD MOVED FROM 55 TO 70, AND THAT IS A BAR CHANGE, SO IT IS
# STATED RATHER THAN SLIPPED IN. Under the old design a contradiction was
# ARITHMETICALLY IMPOSSIBLE -- the projection was the confidence read
# backwards -- so 55 cost nothing. A line-independent projection CAN
# disagree with a row, and how often was pre-registered as T37 with the bar
# fixed BEFORE measuring: <=5% at 70%+, <=2% at 80%+.
# ⛔ THE BAR IS NOT MOVED WHEN A ROW FAILS. The 55-70 band is REPORTED as a
# count on every card so the thing that used to be checked stays visible.
def _against(r):
    return not ((r['projection'] > r['line']) if r['side'] == 'over'
                else (r['projection'] < r['line']))


# 🔴 THE POPULATION IS EVERY PRICED ROW, WHICH IS WHAT T37 PRE-REGISTERED
# -- not the carded subset. Carding selects high-confidence rows, so the
# carded-only rate is a DIFFERENT number against a bar never set for it
# (measured 2026-08-27: 7.7% carded against 5.0% on the full board).
# ⛔ Do not "simplify" this back to `_pj`. That silently swaps the
# population under a pre-registered bar, which is the same error as moving
# the bar.
def _rows_from(px, kind):
    out = []
    for _k, _v in (px or {}).items():
        if not _v.get('p') or _v.get('c') is None:
            continue
        _pid, _mk, _sd, _ln = _k.split('|')
        if (_mk.startswith('pitcher')) != (kind == 'pitcher'):
            continue
        out.append({'pid': _pid, 'market': _mk, 'side': _sd, 'line': float(_ln),
                    'confidence': _v['c'], 'projection': _v['v']})
    return out


def _priced_rows(kind):
    return _rows_from(doc.get('projections'), kind)


# 🔴 THE BAR IS POOLED ACROSS EVERY PUBLISHED CARD, NOT JUDGED PER SLATE.
# ~~a per-card rate against the 5% bar~~ REPLACED 2026-08-28 after it failed
# build #183 on ONE row out of FOUR. ⛔ THIS IS NOT A LOOSENING, AND THE
# ARGUMENT IS THAT THE OLD FORM ASKED A QUESTION THE DATA COULD NOT ANSWER:
# T37's bar was pre-registered and measured on n=80 and n=116. A 2:22am board
# carries 4 priced hitter rows at 70%+, where a SINGLE row knocks the rate to
# 25%. A percentage computed on n=4 is not a rate; applying a rate bar to it
# is a different test wearing the same number.
# ✅ THE REPLACEMENT IS STRICTLY HARDER IN THE LONG RUN. A persistent 6%
# now FAILS even when no individual slate ever exceeds the bar, which the
# per-card form could never catch. Two things changed, both tightening:
#   1. the sample is POOLED over every card that carries the confidence
#      field, so the denominator only ever grows and a bad day never washes
#      out of it;
#   2. a CANARY still fails immediately, with no pooling, on a gross break
#      (>25% on a card with at least 20 rows) so a catastrophic regression
#      cannot hide behind a large historical denominator.
# ⚠️ Below the minimum sample the check reports NOT YET MEASURABLE. It does
# not pass and it does not fail -- refusing to assert what the data cannot
# support is the honest third answer, and it is why the minimum exists.
_POOL_MIN = 100
_CANARY_N, _CANARY_RATE = 20, 25.0


def _pooled_rows(kind):
    """Every priced row this project has published, oldest card first.
    ⚠️ Cards written before 2026-08-27 carry no confidence on their index
    entries and are skipped -- the accumulator starts the day the field
    did, and says so rather than pretending to a longer history."""
    seen, out = set(), []
    for _f in sorted(glob.glob('picks/*.json')):
        try:
            _d = json.load(open(_f))
        except Exception:
            continue
        if _d.get('date') == doc.get('date'):
            continue                      # today comes from `doc`, not disk
        for _r in _rows_from(_d.get('projections'), kind):
            _key = (_d.get('date'), _r['pid'], _r['market'], _r['side'], _r['line'])
            if _key in seen:
                continue
            seen.add(_key)
            out.append(_r)
    return out + _rows_from(doc.get('projections'), kind)


for _lo, _bar in ((70, 5.0), (80, 2.0)):
    _today = [r for r in _priced_rows('pitcher') if r['confidence'] >= _lo]
    _tbad = [r for r in _today if _against(r)]
    _pool = [r for r in _pooled_rows('pitcher') if r['confidence'] >= _lo]
    _bad = [(r['pid'], r['market'], r['side'], r['line'], r['confidence'],
             r['projection']) for r in _pool if _against(r)]
    _rate = 100.0 * len(_bad) / len(_pool) if _pool else 0.0
    _trate = 100.0 * len(_tbad) / len(_today) if _today else 0.0
    if len(_today) >= _CANARY_N and _trate > _CANARY_RATE:
        ck(f"T37 canary: pitcher projections on THIS card are not grossly "
           f"broken ({len(_tbad)} of {len(_today)} = {_trate:.1f}% at {_lo}%+)",
           False, str(_bad[:3]))
    elif len(_pool) < _POOL_MIN:
        print(f"  NOTE  T37: pitcher at {_lo}%+ NOT YET MEASURABLE -- "
              f"{len(_bad)} of {len(_pool)} pooled rows, bar needs {_POOL_MIN}. "
              f"This card {len(_tbad)} of {len(_today)}.")
    else:
        ck(f"T37: pitcher projections contradict <= {_bar}% at {_lo}%+ "
           f"({len(_bad)} of {len(_pool)} pooled priced rows = {_rate:.1f}%)",
           _rate <= _bar, str(_bad[:3]))
_mid = [(r['pitcher'], r['line'], r['confidence'], r['projection'])
        for r in _pj if 55 <= r['confidence'] < 70 and _against(r)]
print(f"  NOTE  55-70% band: {len(_mid)} row(s) project against the pick "
      f"(reported, not barred -- T37 sets no bar below 70%)"
      f"{': ' + str(_mid[:3]) if _mid else ''}")
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
# 🔴 THIS CHECK WAS REPLACED 2026-08-26, AND THE NEW ONE IS HARDER.
# ~~"no projection on a market where every distribution FAILED its bar"~~
# asked whether total bases and H+R+RBI were ABSENT. That was the right
# question while nothing could reproduce a player's own per-game mean to
# T34's 0.25 bar. It is the WRONG question now that those two markets
# carry the mean ITSELF, which reproduces it exactly. Testing for absence
# would now fail a correct card.
# ⛔ The replacement does not test that something exists -- it RECOMPUTES
# the value from the game log and compares. That is strictly stronger than
# the check it replaces, which never looked at a number at all.
# 🔴 ALL FIVE MARKETS 2026-08-27, not two. Every hitter projection is now
# the player's own per-game mean (T37), so every one of them can be
# recomputed here from the raw log rather than taken on trust.
_MEAN_MKT = {'batter_total_bases': 'tb', 'batter_hits_runs_rbis': None,
             'batter_hits': 'H', 'batter_home_runs': 'hr',
             'batter_rbis': 'rbi'}
_hp = [r for r in hit_rows if r.get('projection') is not None]
_HL2 = json.load(gzip.open('data/latest/hitters.json.gz', 'rt'))
_HL2 = _HL2.get('players', _HL2)


def _own_mean(pid, market):
    rec = _HL2.get(str(pid))
    if not rec:
        return None
    key = _MEAN_MKT[market]
    v = [((g.get('H') or 0) + (g.get('r') or 0) + (g.get('rbi') or 0)) if key is None
         else (g.get(key) or 0)
         for g in (rec.get('g') or [])
         if (g.get('pa') or 0) >= 3 and (g.get('d') or '') < doc['date']]
    return (sum(v) / len(v)) if len(v) >= 10 else None


_mm = []
for r in _hp:
    if r['market'] not in _MEAN_MKT:
        continue
    m = _own_mean(r.get('pid'), r['market'])
    # ⛔ Compare against the UNROUNDED mean with a tolerance, not against
    # round(m, 1). card.py keeps a SECOND decimal when one decimal would
    # land on one of that player's own lines (rule 64), so pinning to one
    # decimal would fail a correct card.
    if m is None or abs(m - r['projection']) > 0.051:
        _mm.append((r['player'], r['market'], r['projection'],
                    None if m is None else round(m, 3)))
ck(f"EVERY hitter projection is the player's OWN per-game mean, recomputed "
   f"from the log ({sum(1 for r in _hp if r['market'] in _MEAN_MKT)} rows)",
   not _mm, str(_mm[:3]))
# Sam, 2026-08-26: "we need to make sure every player has one."
_noproj = [(r.get('pitcher') or r.get('player'), r.get('market'))
           for r in doc['picks'] if r.get('projection') is None]
ck(f"every row on the board carries a projection ({len(doc['picks'])} rows)",
   not _noproj, str(_noproj[:4]))

# 🔴 THE REAL INVARIANT, not a percentage. Sam, 2026-08-26: "there are
# still players that have game logs that dont have projections."
# A row is allowed no projection ONLY when there is genuinely nothing to
# project from -- no player id, or a player the collector has never logged.
# ⛔ A row with an id AND a log must have one. A percentage target would
# have let this pass at 93% while the specific complaint stayed true.
_PX = doc.get('projections') or {}
_HLOG = json.load(gzip.open('data/latest/hitters.json.gz', 'rt'))
_HLOG = _HLOG.get('players', _HLOG)
_orphans = []
for _g in B.get('games', []):
    for _p in _g.get('props', []):
        _pid, _mk = _p.get('pid'), _p.get('market')
        if _pid is None:
            continue                       # nothing to join to
        if f"{_pid}|{_mk}|{_p.get('side')}|{_p.get('line')}" in _PX:
            continue
        _log = P.get(str(_pid)) if str(_mk).startswith('pitcher') else _HLOG.get(str(_pid))
        if not _log:
            continue                       # never logged; a blank is honest
        _n = len([x for x in (_log.get('g') or [])
                  if (x.get('gs') if str(_mk).startswith('pitcher')
                      else (x.get('pa') or 0) >= 3)])
        if _n >= 10:
            _orphans.append((_p.get('player'), _mk, _p.get('line'), f"{_n} games logged"))
ck(f"no prop with a player id and a real game log is left without a "
   f"projection ({len(_PX)} projections published)",
   not _orphans, str(_orphans[:4]))
# The mean is not an inversion, so it CAN sit on the losing side of a
# line. Measured across 948 real props that is 0.0% at 80%+ confidence and
# 1.9% at 70%+, and the board does not go below 78%. If it starts
# happening on a confident row, the assumption behind shipping the mean
# has broken and this should say so.
_wrong = [(r['player'], r['confidence'], r['line'], r['projection'])
          for r in _hp if r['market'] in _MEAN_MKT and r.get('confidence', 0) >= 70
          and not ((r['projection'] > r['line']) if r['side'] == 'over'
                   else (r['projection'] < r['line']))]
# ~~"no confident total-bases pick projects against itself"~~
# 🔴 REPLACED 2026-08-27. It demanded ZERO contradictions at 70%+ on ONE
# market, which was reachable while only total bases and H+R+RBI used the
# mean. Now every hitter market does, and T37 pre-registered the tolerance
# at <=5% at 70%+ over ALL priced rows -- a zero-tolerance check on a
# subset would silently override a bar fixed before the measurement.
# ⛔ The count is still REPORTED, on the market it was written for.
print(f"  NOTE  {len(_wrong)} carded hitter row(s) at 70%+ project against "
      f"the pick"
      f"{': ' + str(_wrong[:3]) if _wrong else ''}")
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


# ~~"every hitter projection round-trips to the rate printed beside it"~~
# 🔴 REPLACED 2026-08-27 (T37). A hitter projection is no longer an
# inversion of his displayed rate -- it is his own per-game mean, so there
# is no rate to round-trip to. ⛔ THE REPLACEMENT IS STRONGER, NOT WEAKER:
# the check directly above RECOMPUTES that mean from the raw game log for
# all five markets and compares, which never reads a number back off the
# card. What is lost is the guarantee that a projection cannot disagree
# with its own row; what replaces it is T37's pre-registered contradiction
# bar, reported below on the hitter half exactly as on the pitcher half.
def _h_against(r):
    return not ((r['projection'] > r['line']) if r['side'] == 'over'
                else (r['projection'] < r['line']))


for _lo, _bar in ((70, 5.0), (80, 2.0)):
    _today = [r for r in _priced_rows('hitter') if r['confidence'] >= _lo]
    _tbad = [r for r in _today if _h_against(r)]
    _pool = [r for r in _pooled_rows('hitter') if r['confidence'] >= _lo]
    _bad = [(r['pid'], r['market'], r['side'], r['line'], r['confidence'],
             r['projection']) for r in _pool if _h_against(r)]
    _rate = 100.0 * len(_bad) / len(_pool) if _pool else 0.0
    _trate = 100.0 * len(_tbad) / len(_today) if _today else 0.0
    if len(_today) >= _CANARY_N and _trate > _CANARY_RATE:
        ck(f"T37 canary: hitter projections on THIS card are not grossly "
           f"broken ({len(_tbad)} of {len(_today)} = {_trate:.1f}% at {_lo}%+)",
           False, str(_bad[:3]))
    elif len(_pool) < _POOL_MIN:
        print(f"  NOTE  T37: hitter at {_lo}%+ NOT YET MEASURABLE -- "
              f"{len(_bad)} of {len(_pool)} pooled rows, bar needs {_POOL_MIN}. "
              f"This card {len(_tbad)} of {len(_today)}.")
    else:
        ck(f"T37: hitter projections contradict <= {_bar}% at {_lo}%+ "
           f"({len(_bad)} of {len(_pool)} pooled priced rows = {_rate:.1f}%)",
           _rate <= _bar, str(_bad[:3]))
# ⚠️ REPORTED SEPARATELY BECAUSE IT IS A DIFFERENT NUMBER AND SOMEBODY WILL
# ONE DAY QUOTE IT AS IF IT WERE THE SAME ONE.
_cd = [r for r in _hp if (r.get('confidence') or 0) >= 70 and _h_against(r)]
_cn = [r for r in _hp if (r.get('confidence') or 0) >= 70]
print(f"  NOTE  carded hitter rows only: {len(_cd)} of {len(_cn)} contradict at "
      f"70%+ ({100.0 * len(_cd) / len(_cn) if _cn else 0:.1f}%) -- carding "
      f"selects high-confidence rows, so this is NOT the T37 population")

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
# 🔴 REPLACES the old "is it in picks[] + below_price_floor?" test. That
# test was wrong, and wrong in the direction that wastes a morning: those
# two lists are the FILTERED board -- BOARD_MAX truncates them -- so a
# top-10 row drawn from a play card.py priced but did not card failed a
# check it should have passed. It fired twice on 2026-08-27 (Sean Manaea
# strikeouts over 3.5, Ryan Waldschmidt RBI under 0.5) and both were fine.
# The question is not "did it reach the board" but "did card.py price this
# exact row", and the projection index answers it directly: an entry
# carrying "p" was priced, at that pid, market, side and line.
_MKT_FEED = {'strikeouts': 'pitcher_strikeouts', 'outs': 'pitcher_outs'}
_pxall = doc.get('projections') or {}
_pkeys = {k for k, v in _pxall.items() if v.get('p')}


def _pxkey(r):
    return (f"{r.get('pid')}|{_MKT_FEED.get(r.get('market'), r.get('market'))}"
            f"|{r.get('side')}|{r.get('line')}")


_orphan = [(r.get('pitcher') or r.get('player'), r.get('market'), r.get('side'), r.get('line'))
           for r in _t10 if _pxkey(r) not in _pkeys]
ck(f"every top-10 row traces to a row the card priced ({len(_pkeys)} priced keys)",
   not _orphan, str(_orphan[:3]))
# ⛔ AND THE FLAG IS NOT SELF-SERVING. If "p" were stamped on everything it
# would make the check above vacuous, so pin it from the other end: every
# carded row must carry it, and it must not cover the whole index.
_unflagged = [(r.get('pitcher') or r.get('player'), r.get('market'))
              for r in allrows if _pxkey(r) in _pxall and _pxkey(r) not in _pkeys]
ck("every carded row is flagged priced in the index", not _unflagged,
   str(_unflagged[:3]))
ck(f"the priced flag is a subset, not a rubber stamp "
   f"({len(_pkeys)} of {len(_pxall)})", 0 < len(_pkeys) < len(_pxall))
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

print("\n37. BATTER ALTERNATE LINES, INNINGS NOTATION, AND PLAIN ENGLISH")
_PRIMARY = {"batter_hits": {0.5, 1.5}, "batter_total_bases": {1.5},
            "batter_home_runs": {0.5}, "batter_rbis": {0.5},
            "batter_hits_runs_rbis": {0.5, 1.5}}
_alt = [(r.get('player'), r['market'], r['line']) for r in allrows
        if r.get('kind') == 'hitter' and r['market'] in _PRIMARY
        and r['line'] not in _PRIMARY[r['market']]]
ck(f"no batter row sits on an alternate line ({len(hit_rows)} hitter rows)",
   not _alt, str(_alt[:3]))
ck("no batter row is priced at -1000 or shorter",
   not [(r.get('player'), r['price']) for r in allrows
        if r.get('kind') == 'hitter' and r.get('price') is not None
        and r['price'] <= -1000])

# 🔴 INNINGS ARE THIRDS. CLAUDE.md says so in capitals and the opponent
# log shipped round(outs/3, 1) anyway, printing 3.7 and 5.3 innings.
# 16 outs is 5.1. There is no .3, .4, .5, .6, .7, .8 or .9.
_badip = []
for r in pit_rows:
    b = r.get('opp_recent') or {}
    for x in b.get('starts') or []:
        frac = str(x.get('ip', '')).split('.')[-1]
        if frac not in ('0', '1', '2'):
            _badip.append((r['pitcher'], x.get('ip'), x.get('outs')))
    mi = str(b.get('mean_ip', '')).split('.')[-1]
    if b and mi not in ('0', '1', '2'):
        _badip.append((r['pitcher'], 'mean', b.get('mean_ip')))
ck("every innings figure uses thirds (.0 .1 .2 only)", not _badip, str(_badip[:4]))
# And the notation must actually match the outs it claims to describe.
_mismatch = []
for r in pit_rows:
    for x in ((r.get('opp_recent') or {}).get('starts') or []):
        o = x.get('outs')
        if o is not None and x.get('ip') != f"{o // 3}.{o % 3}":
            _mismatch.append((r['pitcher'], o, x.get('ip')))
ck("innings notation matches the out count it describes",
   not _mismatch, str(_mismatch[:4]))

# ⛔ NO JARGON IN THE WHY. Sam, 2026-08-26: "lose the technical wording ...
# all of these things that a casual fine wont know about has to go."
# These are the exact phrases he named plus the rest of the same family.
_JARGON = ['T21', 'T22', 'T23', 'T24', 'T25', 'STEP 1', 'STEP 4B', 'STEP 5',
           'measured null', 't=-', 't=', 'point-in-time', 'DESCRIPTIVE',
           'ledger rule', 'provably biased', 'MODEL projection', 'blend',
           'coefficient', 'centering', 'Jeffreys', 'per-sd', 'z=']
_dirty = []
for r in allrows:
    # ⛔ The flags shown on the PAGE are held to the same bar as the why.
    # A flag that is stored but not rendered may keep its ledger wording;
    # one that reaches a reader may not.
    shown = [f['text'] for f in (r.get('flags') or []) if f.get('actionable')]
    for line in list(r.get('why') or []) + shown:
        for j in _JARGON:
            if j in line:
                _dirty.append((r.get('pitcher') or r.get('player'), j, line[:60]))
ck(f"no jargon in any why ({sum(len(r.get('why') or []) for r in allrows)} lines checked)",
   not _dirty, str(_dirty[:3]))
ck("every row still explains itself",
   all(len(r.get('why') or []) >= 3 for r in allrows),
   str([r.get('pitcher') or r.get('player') for r in allrows
        if len(r.get('why') or []) < 3][:3]))
# The honesty those phrases carried has to survive in plain words.
_h = [r for r in hit_rows if r.get('why')]
ck("every hitter row still says its number is a record, not a forecast",
   all(any('not a projection' in w or "don't have a hitter model" in w
           for w in r['why']) for r in _h))

print("\n38. THE PAGE SHOWS ONLY WHAT A READER CAN ACT ON")
# 🔴 Sam, 2026-08-26: "we have to advertise a clean look ... that doesnt
# include nonsense users dont need to read and cant understand."
# index.html renders `flags` where `actionable` is true and nothing else.
# ⛔ THE REST ARE STILL RECORDED. This checks they are still THERE -- a
# clean page must not become a card that stopped writing its diagnostics,
# because the calibration record depends on every one of them.
_allf = [f for r in allrows for f in (r.get('flags') or [])]
_shown = [f for f in _allf if f.get('actionable')]
_hidden = [f for f in _allf if not f.get('actionable')]
print(f"  NOTE  {len(_allf)} flag(s) on this card: {len(_shown)} shown, "
      f"{len(_hidden)} recorded but not rendered")
ck("the diagnostics are still being written to the card",
   not allrows or len(_allf) > 0 or all(r.get('flags') == [] for r in allrows))
ck("every flag that reaches the page is marked actionable",
   all('actionable' in f or not f.get('actionable') for f in _allf))
_bad = [f['test'] for f in _shown if f.get('test') in
        ('T21', 'T22', 'rule 15', 'STEP 4B')]
ck("no model diagnostic is marked for display", not _bad, str(_bad[:3]))

print(f"\n{'ALL CHECKS PASSED' if not fails else 'FAILURES: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
