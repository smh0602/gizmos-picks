"""T30 -- build the point-in-time STARTED-GAMES hitter dataset, with batting slot.

Pre-registered in claude/owed-tests.md BEFORE anything was fitted.
Run from the repo root:  python research/t30_data.py
Writes research/t30_rows.json. NO FITTING HAPPENS IN THIS FILE.

The sample is the one the pre-registration fixed: games the hitter STARTED
BY REAL BATTING ORDER (sub == 0 in the lineup backfill) -- NOT T27's pa > 0
sample and NOT the pa >= 3 proxy.
"""
import gzip, json, collections

H = json.load(gzip.open('data/latest/hitters.json.gz','rt'))['players']
P = json.load(gzip.open('data/latest/pitchers.json.gz','rt'))['players']
L = json.load(gzip.open('data/latest/lineups.json.gz','rt'))['days']

# ---------------------------------------------------------------- 1
# THE TRADE-CONSISTENCY CHECK -- identical to T27's, deliberately.
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
# THE LINEUP INDEX -- (pid, date) -> the real batting slot, or None.
# A date on which the join cannot be made UNAMBIGUOUSLY is dropped, never
# guessed at: a doubleheader gives two hitter-log rows on one date, and
# unless every lineup entry that day agrees there is no way to say which
# game is which.
lu = collections.defaultdict(list)
for d, rows in L.items():
    for e in rows:
        lu[(int(e['pid']), d)].append(e)

lineup_dates = set(L)
amb = collections.Counter()

def slot_on(pid, d, n_log_rows):
    """Real batting slot if he STARTED, 0 if he did not, None if unknowable."""
    ent = lu.get((int(pid), d))
    if ent is None:
        return None if d in lineup_dates else None   # no lineup card for that date
    starts = [e for e in ent if e.get('sub') == 0]
    if n_log_rows == 1:
        if len(starts) == 1: return starts[0]['slot']
        if len(starts) == 0: return 0
        # two lineup entries, one log row -- cannot align
        amb['two lineup entries, one log row'] += 1
        return None
    # doubleheader: only usable if EVERY game that day was a start at the SAME slot
    if len(starts) == n_log_rows and len({e['slot'] for e in starts}) == 1:
        return starts[0]['slot']
    amb['doubleheader, lineup entries disagree'] += 1
    return None

# ---------------------------------------------------------------- 3
# Opposing starter, keyed on (date, the starter's opponent) -- as T27.
starters = collections.defaultdict(list)
for pid, v in P.items():
    for i, r in enumerate(v['g']):
        if r.get('gs') and r.get('d') and r.get('o'):
            starters[(r['d'], r['o'])].append((pid, i))

def opp_hpbf(pid, i):
    rows = [x for x in P[pid]['g'][:i] if x.get('gs')]
    h = sum(x['hit'] for x in rows if x.get('hit') is not None)
    bf = sum(x['bf'] for x in rows if x.get('bf') is not None)
    return (h / bf, len(rows)) if bf else (None, len(rows))

WINDOW = 20            # fixed by the pre-registration -- NOT to be changed
MIN_PRIOR = 20
MIN_STARTS = 5
SPLIT = '2026-07-15'

rows_out = []
drop = collections.Counter()
no_slot = 0
for pid, v in H.items():
    t = v.get('team')
    per_date = collections.Counter(r['d'] for r in v['g'] if r.get('d'))
    # the STARTED log: games he started by real batting order, in date order
    log = []
    for r in sorted([x for x in v['g'] if x.get('d')], key=lambda x: x['d']):
        s = slot_on(pid, r['d'], per_date[r['d']])
        if s is None:
            no_slot += 1
            continue
        if s == 0:
            continue                      # played but did not start -- not in this sample
        log.append(dict(r, slot=s))
    for i, r in enumerate(log):
        if i < MIN_PRIOR: drop['<20 prior STARTED games'] += 1; continue
        if (r['d'], t, r['o']) not in real: drop['failed trade-consistency check'] += 1; continue
        cand = starters.get((r['d'], t), [])
        if len(cand) != 1: drop['starter ambiguous or missing'] += 1; continue
        spid, si = cand[0]
        oh, nst = opp_hpbf(spid, si)
        if oh is None or nst < MIN_STARTS: drop['starter has <5 prior starts'] += 1; continue

        prior = log[i-WINDOW:i]
        pa = sum(x['pa'] or 0 for x in prior)
        if not pa: drop['no prior plate appearances'] += 1; continue
        hits = sum(x['H'] or 0 for x in prior)
        allp = log[:i]
        g1 = sum(1 for x in allp if (x['H'] or 0) >= 1)
        inc = (g1 + 0.5) / (len(allp) + 1)   # INCUMBENT, recomputed on THIS sample

        rows_out.append({
            'pid': pid, 'd': r['d'], 'y': 1 if (r['H'] or 0) >= 1 else 0,
            'hpa': hits / pa,
            'pa20': pa / len(prior),
            'oppH': oh,
            'home': 1 if r.get('h') else 0,
            'inc': inc,
            'slotA': sum(x['slot'] for x in prior) / len(prior),  # ARM A -- shippable
            'slotB': r['slot'],                                   # ARM B -- upper bound only
        })

print(f"\nrows with no usable lineup join (dropped from the started log): {no_slot}")
for k, n in amb.most_common(): print(f"  of which {k:38} {n}")
print(f"\nusable rows: {len(rows_out)}")
for k, n in drop.most_common(): print(f"  dropped, {k:34} {n}")
tr = [x for x in rows_out if x['d'] < SPLIT]
te = [x for x in rows_out if x['d'] >= SPLIT]
print(f"\ntrain (before {SPLIT}): {len(tr)}   test ({SPLIT}+): {len(te)}")
print(f"base rate  train {sum(x['y'] for x in tr)/len(tr):.4f}   test {sum(x['y'] for x in te)/len(te):.4f}")
json.dump(rows_out, open('research/t30_rows.json','w'))
print("\nwritten to research/t30_rows.json -- NOTHING FITTED YET")
