"""T33 -- Phase 3 with PARK, a NON-LINEAR temperature term and ELEVATION.
Pre-registered in claude/owed-tests.md BEFORE any fitting.
Run from the repo root:  python research/t33_data.py
"""
import gzip, json, collections

S=json.load(gzip.open('data/latest/scores.json.gz','rt'))
W=json.load(gzip.open('data/latest/weather.json.gz','rt'))
H=json.load(gzip.open('data/latest/hitters.json.gz','rt'))['players']
assert S.get('schema')==2
# The consumer contract on the weather file, ENFORCED not trusted.
assert W.get('complete') is True, "weather INCOMPLETE -- re-run mode `weather`"
EL={k: float(v) for k,v in (W.get('elevations') or {}).items()}
assert EL, "no elevations -- re-run mode `weather`"

MLB={v['team'] for v in H.values() if v.get('team')}
games=sorted([(d,r) for d,rows in S['days'].items() for r in rows
              if r.get('gameType')=='R' and r['away'] in MLB and r['home'] in MLB],
             key=lambda x:(x[0],x[1]['gamePk']))
print(f"regular-season games: {len(games)}")

WIN=MIN_PRIOR=20
seq=collections.defaultdict(list); prior={}
for d,r in games:
    for club,mine,theirs in ((r['away'],r['away_r'],r['home_r']),
                             (r['home'],r['home_r'],r['away_r'])):
        h=seq[club]
        if len(h)>=MIN_PRIOR:
            w=h[-WIN:]
            prior[(r['gamePk'],club)]=(sum(x[0] for x in w)/len(w),
                                       sum(x[1] for x in w)/len(w))
        h.append((mine,theirs))

# POINT-IN-TIME park factor -- identical construction to T32, hand-verified there.
MIN_PARK=10
ph=collections.defaultdict(list); lg=[]; pf={}
for d,r in games:
    v=r.get('venue_id')
    pf[r['gamePk']]=(sum(ph[v])/len(ph[v])-sum(lg)/len(lg)) if (v is not None and len(ph[v])>=MIN_PARK and lg) else 0.0
    t=r['away_r']+r['home_r']
    if v is not None: ph[v].append(t)
    lg.append(t)

COLD=60.0          # fixed in the pre-registration, NOT tuned
out=[]; drop=collections.Counter()
for d,r in games:
    a,h=prior.get((r['gamePk'],r['away'])),prior.get((r['gamePk'],r['home']))
    if a is None or h is None: drop['club under 20 prior games']+=1; continue
    vid=str(r.get('venue_id'))
    hh='19' if r.get('dayNight')=='night' else '13'
    wx=(W['venues'].get(vid) or {}).get(d,{}).get(hh)
    if not wx or wx.get('temp_f') is None: drop['no weather at game hour']+=1; continue
    if vid not in EL: drop['no elevation for venue']+=1; continue
    out.append({'d':d,'gamePk':r['gamePk'],'total':r['away_r']+r['home_r'],
                'a_rs':a[0],'a_ra':a[1],'h_rs':h[0],'h_ra':h[1],
                'park':pf[r['gamePk']],'temp':wx['temp_f'],
                'cold':1 if wx['temp_f']<COLD else 0,'elev':EL[vid]})

SPLIT='2026-07-15'
tr=[x for x in out if x['d']<SPLIT]; te=[x for x in out if x['d']>=SPLIT]
print(f"\nT33 rows: {len(out)}   train {len(tr)}   test {len(te)}")
for k,n in drop.most_common(): print(f"  dropped, {k:32} {n}")
nc=sum(x['cold'] for x in out)
print(f"\ncold indicator (<{COLD:.0f}F) fires on {nc} of {len(out)} games ({100*nc/len(out):.1f}%)"
      f"  -- held out: {sum(x['cold'] for x in te)}")
print(f"elevation: {min(x['elev'] for x in out):.0f}m to {max(x['elev'] for x in out):.0f}m")
json.dump(out,open('research/t33_rows.json','w'))
print("written -- NOTHING FITTED YET")
