"""T27 — build the point-in-time hitter dataset.

Pre-registered in claude/owed-tests.md BEFORE anything was fitted.
Run from the repo root:  python research/t27_data.py
Writes research/t27_rows.json. NO FITTING HAPPENS IN THIS FILE.
"""
import gzip, json, collections

H = json.load(gzip.open('data/latest/hitters.json.gz','rt'))['players']
P = json.load(gzip.open('data/latest/pitchers.json.gz','rt'))['players']

# ---------------------------------------------------------------- 1
# THE TRADE-CONSISTENCY CHECK.
# The roster field is each player's CURRENT team, applied to every
# historical row. For a traded player that is wrong for every game before
# the trade, and it would match him against the wrong pitching staff in
# silence. So the real schedule is rebuilt FROM THE DATA: on any date, a
# (team, opponent) pair supported by several different players is a real
# game; a pair supported by one player is that player being in the wrong
# place. Rows whose pair is unsupported are DROPPED, never guessed at.
pair_support = collections.defaultdict(set)
for pid, v in H.items():
    t = v.get('team')
    if not t: continue
    for r in v['g']:
        if r.get('d') and r.get('o'):
            pair_support[(r['d'], t, r['o'])].add(pid)

MIN_SUPPORT = 3
real = {k for k, s in pair_support.items() if len(s) >= MIN_SUPPORT}
print(f"schedule pairs rebuilt from the hitter logs : {len(pair_support)}")
print(f"  supported by {MIN_SUPPORT}+ players (kept)          : {len(real)}")
print(f"  unsupported (traded-player rows, dropped) : {len(pair_support)-len(real)}")

# ---------------------------------------------------------------- 2
# Opposing starter, keyed on (date, the starter's opponent).
starters = collections.defaultdict(list)
for pid, v in P.items():
    for i, r in enumerate(v['g']):
        if r.get('gs') and r.get('d') and r.get('o'):
            starters[(r['d'], r['o'])].append((pid, i))

# point-in-time hits-allowed-per-batter-faced for a starter, before start i
def opp_hpbf(pid, i):
    rows = [x for x in P[pid]['g'][:i] if x.get('gs')]
    h = sum(x['hit'] for x in rows if x.get('hit') is not None)
    bf = sum(x['bf'] for x in rows if x.get('bf') is not None)
    return (h / bf, len(rows)) if bf else (None, len(rows))

WINDOW = 20            # fixed by the pre-registration
MIN_PRIOR = 20
MIN_STARTS = 5
SPLIT = '2026-07-15'

rows_out = []
drop = collections.Counter()
for pid, v in H.items():
    t = v.get('team')
    log = sorted([r for r in v['g'] if (r.get('pa') or 0) > 0], key=lambda r: r['d'])
    for i, r in enumerate(log):
        if i < MIN_PRIOR: drop['<20 prior played games'] += 1; continue
        if (r['d'], t, r['o']) not in real: drop['failed trade-consistency check'] += 1; continue
        cand = starters.get((r['d'], t), [])
        if len(cand) != 1: drop['starter ambiguous or missing'] += 1; continue
        spid, si = cand[0]
        oh, nst = opp_hpbf(spid, si)
        if oh is None or nst < MIN_STARTS: drop['starter has <5 prior starts'] += 1; continue

        prior = log[max(0, i-WINDOW):i]
        pa = sum(x['pa'] for x in prior)
        if not pa: drop['no prior plate appearances'] += 1; continue
        hits = sum(x['H'] or 0 for x in prior)
        # the INCUMBENT: Jeffreys-smoothed rate of 1+ hit games, point-in-time
        allp = log[:i]
        g1 = sum(1 for x in allp if (x['H'] or 0) >= 1)
        inc = (g1 + 0.5) / (len(allp) + 1)

        rows_out.append({
            'pid': pid, 'd': r['d'], 'y': 1 if (r['H'] or 0) >= 1 else 0,
            'hpa': hits / pa,
            'pa20': pa / len(prior),
            'oppH': oh,
            'home': 1 if r.get('h') else 0,
            'inc': inc,
        })

print(f"\nusable rows: {len(rows_out)}")
for k, n in drop.most_common(): print(f"  dropped, {k:34} {n}")
tr = [x for x in rows_out if x['d'] < SPLIT]
te = [x for x in rows_out if x['d'] >= SPLIT]
print(f"\ntrain (before {SPLIT}): {len(tr)}   test ({SPLIT}+): {len(te)}")
print(f"base rate  train {sum(x['y'] for x in tr)/len(tr):.4f}   test {sum(x['y'] for x in te)/len(te):.4f}")
json.dump(rows_out, open('research/t27_rows.json','w'))
print("\nwritten to research/t27_rows.json — NOTHING FITTED YET")
