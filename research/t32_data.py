"""T32 -- Phase 3 with PARK, WEATHER and DAY/NIGHT. Pre-registered before fitting.
Run from the repo root:  python research/t32_data.py   -> research/t32_rows.json
"""
import gzip, json, collections

S = json.load(gzip.open('data/latest/scores.json.gz','rt'))
W = json.load(gzip.open('data/latest/weather.json.gz','rt'))
H = json.load(gzip.open('data/latest/hitters.json.gz','rt'))['players']
P = json.load(gzip.open('data/latest/pitchers.json.gz','rt'))['players']

assert S.get('schema') == 2, "scores must be schema 2 (venue/gameType/dayNight)"
# THE CONSUMER CONTRACT, enforced rather than trusted. The weather file says
# in its own text: refuse to fit while `complete` is false.
assert W.get('complete') is True, "weather is INCOMPLETE -- re-run mode `weather`"

MLB = {v['team'] for v in H.values() if v.get('team')}
games = [(d, r) for d, rows in S['days'].items() for r in rows
         if r.get('gameType') == 'R' and r['away'] in MLB and r['home'] in MLB]
games.sort(key=lambda x: (x[0], x[1]['gamePk']))
print(f"regular-season games (gameType=='R'): {len(games)}")

# ---- point-in-time team form (identical construction to T31)
WIN = MIN_PRIOR = 20
seq = collections.defaultdict(list); prior = {}
for d, r in games:
    for club, mine, theirs in ((r['away'], r['away_r'], r['home_r']),
                               (r['home'], r['home_r'], r['away_r'])):
        h = seq[club]
        if len(h) >= MIN_PRIOR:
            w = h[-WIN:]
            prior[(r['gamePk'], club)] = (sum(x[0] for x in w)/len(w),
                                          sum(x[1] for x in w)/len(w))
        h.append((mine, theirs))

# ---- POINT-IN-TIME park factor. A season-long factor used inside its own
# season is LOOKAHEAD -- the error already struck for T22 and T24.
MIN_PARK = 10
park_hist = collections.defaultdict(list); league = []
park_factor = {}
for d, r in games:
    v = r.get('venue_id')
    if v is not None and len(park_hist[v]) >= MIN_PARK and league:
        park_factor[r['gamePk']] = (sum(park_hist[v])/len(park_hist[v])
                                    - sum(league)/len(league))
    else:
        park_factor[r['gamePk']] = 0.0
    t = r['away_r'] + r['home_r']
    if v is not None: park_hist[v].append(t)
    league.append(t)

# ---- opposing-starter join (identical to T27/T30/T31)
starters = collections.defaultdict(list)
for pid, v in P.items():
    for i, x in enumerate(v['g']):
        if x.get('gs') and x.get('d') and x.get('o'):
            starters[(x['d'], x['o'])].append((pid, i))

def starter_feats(date, opposing_club):
    cand = starters.get((date, opposing_club), [])
    if len(cand) != 1: return None
    pid, i = cand[0]
    rows = [x for x in P[pid]['g'][:i] if x.get('gs')]
    if len(rows) < 5: return None
    w = rows[-8:]
    er = [x['er'] for x in w if x.get('er') is not None]
    ou = [x['outs'] for x in w if x.get('outs') is not None]
    k  = [x['k'] for x in w if x.get('k') is not None]
    if not (er and ou and k): return None
    return sum(er)/len(er), sum(ou)/len(ou), sum(k)/len(k)

out = []; drop = collections.Counter()
for d, r in games:
    a, h = prior.get((r['gamePk'], r['away'])), prior.get((r['gamePk'], r['home']))
    if a is None or h is None: drop['club under 20 prior games'] += 1; continue
    af = starter_feats(d, r['home']); hf = starter_feats(d, r['away'])
    if af is None or hf is None: drop['starter unresolved or under 5 starts'] += 1; continue
    hh = '19' if r.get('dayNight') == 'night' else '13'
    wx = W['venues'].get(str(r.get('venue_id')), {}).get(d, {}).get(hh)
    if not wx or wx.get('temp_f') is None or wx.get('wind_mph') is None:
        drop['no weather reading at game hour'] += 1; continue
    out.append({'d': d, 'gamePk': r['gamePk'], 'total': r['away_r'] + r['home_r'],
                'a_rs': a[0], 'a_ra': a[1], 'h_rs': h[0], 'h_ra': h[1],
                'a_er': af[0], 'h_er': hf[0],
                'park': park_factor[r['gamePk']],
                'temp': wx['temp_f'], 'wind': wx['wind_mph'],
                'night': 1 if r.get('dayNight') == 'night' else 0,
                'a_outs': af[1], 'h_outs': hf[1], 'a_k': af[2], 'h_k': hf[2]})

SPLIT = '2026-07-15'
print(f"\nT32 rows: {len(out)}   train {sum(1 for x in out if x['d']<SPLIT)}"
      f"   test {sum(1 for x in out if x['d']>=SPLIT)}")
for k, n in drop.most_common(): print(f"  dropped, {k:38} {n}")
import statistics
print(f"\npark factor: min {min(x['park'] for x in out):+.2f}  "
      f"max {max(x['park'] for x in out):+.2f}  "
      f"zero (thin park) {sum(1 for x in out if x['park']==0.0)}")
json.dump(out, open('research/t32_rows.json','w'))
print("written to research/t32_rows.json -- NOTHING FITTED YET")
