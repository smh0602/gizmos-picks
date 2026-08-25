"""T31 -- build the point-in-time GAME-LEVEL dataset. Phase 3.

Pre-registered in claude/owed-tests.md BEFORE anything was fitted.
Run from the repo root:  python research/t31_data.py
Writes research/t31_rows.json. NO FITTING HAPPENS IN THIS FILE.
"""
import gzip, json, collections

S = json.load(gzip.open('data/latest/scores.json.gz','rt'))['days']
H = json.load(gzip.open('data/latest/hitters.json.gz','rt'))['players']
P = json.load(gzip.open('data/latest/pitchers.json.gz','rt'))['players']

# ---------------------------------------------------------------- 1
# THE SAMPLE FILTER, and it is part of the SPECIFICATION rather than a
# later cleanup. sportId=1 also returns the World Baseball Classic, spring
# training, minor-league exhibitions and the All-Star game. Spring training
# scores 5.02 runs per team-game against the regular season's 4.47, so
# pooling reads +0.070 too high -- a bias that looks like signal.
# Neither the club list nor opening day is hand-typed: both are DERIVED.
MLB = {v['team'] for v in H.values() if v.get('team')}
OPEN = min(r['d'] for v in H.values() for r in v['g'] if r.get('d'))
assert len(MLB) == 30, f"expected 30 clubs, derived {len(MLB)}"
print(f"clubs derived from the hitter DB : {len(MLB)}")
print(f"opening day derived from the logs: {OPEN}")

games = []
drop = collections.Counter()
for d, rows in S.items():
    for r in rows:
        if d < OPEN:
            drop['before opening day (spring training)'] += 1; continue
        if r['away'] not in MLB or r['home'] not in MLB:
            drop['non-MLB club (WBC / minors / All-Star)'] += 1; continue
        games.append((d, r))
games.sort(key=lambda x: (x[0], x[1]['gamePk']))
print(f"\nclean regular-season games: {len(games)}")
for k, n in drop.most_common(): print(f"  dropped, {k:42} {n}")

# ---------------------------------------------------------------- 2
# POINT-IN-TIME team form. Each club's own game sequence, in order; every
# window is built ONLY from games strictly BEFORE the row.
WIN = 20            # fixed by the pre-registration
MIN_PRIOR = 20
seq = collections.defaultdict(list)          # club -> [(scored, allowed)]
prior = {}                                   # (gamePk, club) -> window stats
for d, r in games:
    for club, mine, theirs in ((r['away'], r['away_r'], r['home_r']),
                               (r['home'], r['home_r'], r['away_r'])):
        h = seq[club]
        if len(h) >= MIN_PRIOR:
            w = h[-WIN:]
            prior[(r['gamePk'], club)] = (sum(x[0] for x in w)/len(w),
                                          sum(x[1] for x in w)/len(w))
        h.append((mine, theirs))

# ---------------------------------------------------------------- 3
# The opposing-starter join, same construction T27/T30 used: a starter's
# own row names his date and his opponent, so starters[(date, X)] is
# whoever started AGAINST club X that day.
starters = collections.defaultdict(list)
for pid, v in P.items():
    for i, x in enumerate(v['g']):
        if x.get('gs') and x.get('d') and x.get('o'):
            starters[(x['d'], x['o'])].append((pid, i))

MIN_STARTS = 5
def starter_er(date, opposing_club):
    """Trailing-8 EARNED RUNS per start for whoever started against
    `opposing_club`, computed from starts strictly BEFORE this one."""
    cand = starters.get((date, opposing_club), [])
    if len(cand) != 1:
        return None, 'ambiguous or missing'
    pid, i = cand[0]
    rows = [x for x in P[pid]['g'][:i] if x.get('gs')]
    if len(rows) < MIN_STARTS:
        return None, 'under 5 prior starts'
    w = rows[-8:]
    er = [x['er'] for x in w if x.get('er') is not None]
    if not er:
        return None, 'no earned-run data'
    return sum(er)/len(er), None

out = []
d2 = collections.Counter()
for d, r in games:
    a, h = prior.get((r['gamePk'], r['away'])), prior.get((r['gamePk'], r['home']))
    if a is None or h is None:
        d2['a club has under 20 prior games'] += 1; continue
    row = {'d': d, 'gamePk': r['gamePk'], 'away': r['away'], 'home': r['home'],
           'total': r['away_r'] + r['home_r'],
           'a_rs': a[0], 'a_ra': a[1], 'h_rs': h[0], 'h_ra': h[1]}
    # T31b only -- both starters, or the row is simply not b-eligible.
    aer, why1 = starter_er(d, r['home'])     # away club's starter faced the home club
    her, why2 = starter_er(d, r['away'])
    if aer is not None and her is not None:
        row['a_er'], row['h_er'] = aer, her
    else:
        d2[f"not T31b-eligible: {why1 or why2}"] += 1
    out.append(row)

SPLIT = '2026-07-15'
tr = [x for x in out if x['d'] < SPLIT]; te = [x for x in out if x['d'] >= SPLIT]
b  = [x for x in out if 'a_er' in x]
print(f"\nT31a rows: {len(out)}   train {len(tr)}   test {len(te)}")
print(f"T31b rows: {len(b)}   train {sum(1 for x in b if x['d']<SPLIT)}"
      f"   test {sum(1 for x in b if x['d']>=SPLIT)}")
for k, n in d2.most_common(): print(f"  {k:42} {n}")
import statistics
print(f"\ncombined runs: mean {statistics.mean([x['total'] for x in out]):.2f}"
      f"  sd {statistics.pstdev([x['total'] for x in out]):.2f}")
json.dump(out, open('research/t31_rows.json','w'))
print("\nwritten to research/t31_rows.json -- NOTHING FITTED YET")
