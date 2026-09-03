#!/usr/bin/env python3
"""Projected Odds API spend, DERIVED FROM THE DEPLOYED WORKFLOW.

🔴 WHY THIS EXISTS. This project's own standing lesson is: never put a
count anywhere you cannot auto-update. The credit budget has been written
into comments three times and been wrong twice -- once costed at one
region after the pull had moved to two, once quoting a schedule that had
already changed. A budget in a comment is a budget that goes stale.

This reads the cron schedule out of .github/workflows/collect.yml and the
market lists out of collect.py, and computes the spend. If either moves,
this number moves with it.

⚠️ It models the CEILING: a full slate with props posted on every game.
Real spend runs lower, because games with no props posted yet return 404
and bill nothing -- a 28-event window still billed exactly 150.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PLAN, RESERVE, GAMES = 20000, 750, 15

src = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()


def listlen(name):
    m = re.search(name + r"\s*=\s*\[(.*?)\]", src, re.S)
    return len(re.findall(r'"', m.group(1))) // 2 if m else 0


LEAGUE_OF = {}
BAT, PIT, GAME_M = listlen("BATTER_MARKETS"), listlen("PITCHER_MARKETS"), listlen("GAME_MARKETS")
wf = open(os.path.join(ROOT, ".github/workflows/collect.yml"), encoding="utf-8").read()
crons = re.findall(r'- cron: "([^"]+)"', wf)
# 🔴 A MODE IS A LIST (ledger rule 63). The old pattern was `[a-z-]+`,
# which cannot match "props-pitcher-hr props-batter-hr props-board" -- so
# every batched cron read as UNMAPPED, the props vanished from the total,
# and this script reported 126/day against a true 606. ⛔ A budget tool
# that silently under-reports is worse than no budget tool: it says ✅ fits.
modes = dict(re.findall(r'"([\d ,*-]+)"\)\s*echo "mode=([a-z0-9 -]+)"', wf))
modes = {c: v.split() for c, v in modes.items()}

# 🔴 FOOTBALL WAS INVISIBLE TO THIS TOOL. The football crons are routed by
# a `case` block, not by an `echo "mode=..."`, so every one of them read
# as UNMAPPED and the budget reported MLB alone. ⛔ A budget tool that
# silently omits a whole sport is worse than none: it says ✅ fits while
# the spend it cannot see grows every weekend.
# ⚠️ PARSED FROM THE WORKFLOW, never written down here, per the same rule
# that put this file in the repo.
for _c, _lg, _ms in re.findall(
        r'"([\d ,*/-]+)"\)\s*LEAGUE=(\w+);\s*MODES="([a-z0-9 -]+)"', wf):
    modes[_c] = _ms.split()
    LEAGUE_OF[_c] = _lg
ALL_MODES = sorted({m for v in modes.values() for m in v})


def _slots(field, hi):
    """How many values a cron field selects, out of a range of size `hi`.

    🔴 STEPS WERE COUNTED AS ONE. `[measured 2026-09-01]` the old version
    tested for "*" and for "-" and fell through to `t += 1` on anything
    else -- so `*/6` read as ONE fire a day instead of FOUR. Both football
    line-movement crons use `*/6`, and the budget under-reported them by
    108 credits a week.
    ⛔ THIS IS THE SECOND TIME THIS FILE HAS SILENTLY UNDER-REPORTED, and
    its own header says why that is the worst failure available to it: a
    budget tool that under-counts still prints ✅ fits.
    ⚠️ So parse the real grammar -- "*", "a-b", "a/n", "*/n", lists of
    those -- rather than the two cases someone happened to think of.
    """
    if field == "*":
        return hi
    total = 0
    for part in field.split(","):
        rng, _, step = part.partition("/")
        step = int(step) if step else 1
        if rng == "*":
            a, b = 0, hi - 1
        elif "-" in rng:
            a, b = (int(x) for x in rng.split("-"))
        else:
            a = b = int(rng)
            # ⚠️ A bare value WITH a step means "from here to the end":
            # `9/3` is 9,12,15,18,21. Cron's grammar, not an edge case.
            if step > 1:
                b = hi - 1
        total += (b - a) // step + 1
    return total


def fires(cron):
    """Runs per day for a 5-field cron: lists, ranges AND steps."""
    mins, hours = cron.split()[0], cron.split()[1]
    return _slots(mins, 60) * _slots(hours, 24)


# ⚠️ SLATE SIZES ARE MEASURED, NOT ASSUMED.
#   NCAAF: 103 events on the 2026-09-01 board, of which the Power 4 gate
#          kept 20. ⛔ THE GATE IS WHAT MAKES COLLEGE AFFORDABLE -- an
#          unfiltered pull is 5 x 2 x 103 = 1,030, above the whole cap.
#   NFL  : 16 games a Sunday; a Thursday or a December Saturday is 1-3.
# 🔴 MEASURED OFF THE REAL 2026 SCHEDULES, 2026-09-03, at the deployed
# 36h window with the AT-LEAST-ONE-SIDE-FBS gate.
#   ncaaf: the old value of 20 was the BOTH-sides-Power-4 slate. That gate
#          threw away 122 of September's 189 Power 4 games -- Alabama, USC,
#          Oklahoma -- for playing smaller schools. FBS-wide averages ~41
#          games per pull across the three weekly crons.
#   nfl  : ~12 per pull (1 Thursday, ~14 Sunday, plus the Saturday backup).
# ⛔ Do not lower these to make the total look better. Run the script.
FB_GAMES = {"ncaaf": 41, "nfl": 12}
# 🔴 READ *ONLY* THE PROP_MARKETS BLOCK, NOT EVERY `"nfl": [...]` IN THE
# FILE. ⛔ THIS UNDER-REPORTED TO ZERO ON 2026-09-03: `collect.py` gained
# `NEWS_FEEDS = {"nfl": [], "ncaaf": []}`, the old whole-file regex matched
# it too, and a dict comprehension keeps the LAST match -- so an empty news
# list silently overwrote the real market list and football props priced at
# 0 while the tool still printed "✅ FITS".
# ⚠️ THAT IS LEDGER RULE 68 FOR THE THIRD TIME. Scope the search to the
# block that actually defines the pull, and FAIL LOUD if it is not found.
_pm = re.search(r'^PROP_MARKETS\s*=\s*\{(.*?)^\}', src, re.S | re.M)
if not _pm:
    sys.exit("FATAL: cannot find PROP_MARKETS in collect.py — refusing to "
             "price football at zero. Fix this parser, do not guess.")
FB_MARKETS = {lg: len(re.findall(r'"player_[a-z_]+"', m))
              for lg, m in re.findall(
                  r'"(nfl|ncaaf)":\s*\[(.*?)\]', _pm.group(1), re.S)}
if sorted(FB_MARKETS) != ["ncaaf", "nfl"] or not all(FB_MARKETS.values()):
    sys.exit(f"FATAL: football markets parsed as {FB_MARKETS} — a zero or a "
             f"missing league means the cost is WRONG, not cheap.")

COST = {
    "gamelines":        GAME_M * 2,                 # per CALL, whole slate
    "props-batter":     BAT * 2 * GAMES,
    "props-pitcher":    PIT * 2 * GAMES,
    "props-batter-hr":  BAT * 1 * GAMES,
    "props-pitcher-hr": PIT * 1 * GAMES,
}
print(f"markets: batter {BAT}  pitcher {PIT}  gamelines {GAME_M}   (slate modelled at {GAMES} games)\n")
print(f"{'mode':20} {'runs/day':>9} {'per run':>9} {'per day':>9}")
per_day, unmapped, backups = 0, [], 0
seen = {}
for c in crons:
    ms = modes.get(c)
    if ms is None:
        unmapped.append(c)
        continue
    lg = LEAGUE_OF.get(c)
    if lg in ("nfl", "ncaaf"):
        # ⛔ Football is reported WEEKLY below, not folded into the daily
        # MLB figure -- a Saturday-only cost divided by seven is a number
        # that is wrong on every day of the week.
        continue
    if False:
        # ⛔ Football props bill markets x regions x GAMES, same as MLB.
        cost = sum((FB_MARKETS.get(lg, 0) * 2 * FB_GAMES[lg])
                   if m == "props-player" else
                   (GAME_M * 2) if m == "gamelines" else 0
                   for m in ms)
    else:
        cost = sum(COST.get(m, 0) for m in ms)
    if not cost:
        continue
    r = fires(c)
    # A second cron for the SAME MODE LIST inside the same hour is a BACKUP
    # and the freshness guard makes it free when the primary lands.
    key = (" ".join(ms), c.split()[1])
    if key in seen:
        backups += r
        continue
    seen[key] = True
    per_day += cost * r
for m in [x for x in ALL_MODES if x in COST]:
    rs = sum(fires(c) for c in crons if m in modes.get(c, []))
    print(f"{m:20} {rs:>9} {COST[m]:>9} {'—':>9}")
# ── football, itemised, because it is new and it is the thing that grows
# ══════════════════════════════════════════════════════════════════════
# 🔴 MLB'S SPEND CANNOT BE DERIVED FROM THE CRON LIST, AND PRETENDING
# OTHERWISE IS WHY THIS TOOL REPORTED A NUMBER NOBODY RECOGNISED.
# Every MLB cron runs `converge`, which decides AT RUNTIME what is past
# due -- so there is no mode list to price. ⛔ The cron-derived figure is
# a CEILING for a full slate with props on every game, and the measured
# spend has been running at roughly HALF of it.
# ✅ So read what was actually spent. The snapshots carry `credits_used`.
# ⚠️ This is the same rule as everywhere else tonight: the artifact, not
# the estimate.
# ══════════════════════════════════════════════════════════════════════
import glob as _glob, gzip as _gzip, json as _json, collections as _c
_spend = _c.Counter()
for _p in _glob.glob(os.path.join(ROOT, "data/20*/*/*.json.gz")):
    try:
        with _gzip.open(_p, "rt") as _fh:
            _u = _json.load(_fh).get("credits_used")
    except Exception:
        continue
    if _u:
        _spend[_p.split(os.sep)[-3]] += _u
_days = sorted(_spend)[-7:]
_meas = round(sum(_spend[d] for d in _days) / max(1, len(_days)))
print("\nMLB — MEASURED, not derived (converge has no cron-visible mode list)")
for _d in _days:
    print(f"  {_d}  {_spend[_d]:>5} credits")
print(f"  {'mean of last ' + str(len(_days)):<12} {_meas:>5}/day"
      f"   (cron-derived ceiling was {per_day})")

print(f"\nFOOTBALL  markets: nfl {FB_MARKETS.get('nfl')}  ncaaf "
      f"{FB_MARKETS.get('ncaaf')}   (slates modelled at "
      f"nfl {FB_GAMES['nfl']}, ncaaf {FB_GAMES['ncaaf']} games)")
fb_week = 0
for c, lg in sorted(LEAGUE_OF.items(), key=lambda kv: kv[1]):
    ms = modes.get(c, [])
    cost = sum((FB_MARKETS.get(lg, 0) * 2 * FB_GAMES[lg]) if m == "props-player"
               else (GAME_M * 2) if m == "gamelines" else 0 for m in ms)
    if not cost:
        continue
    days = _slots(c.split()[4], 7)   # ⚠️ same parser: a step here would have lied too
    wk = cost * fires(c) * days
    fb_week += wk
    print(f"  {lg:<6} {c:<20} {' '.join(ms):<26} {cost:>5}/run  {wk:>6}/wk")
print(f"  {'':<6} {'':<20} {'FOOTBALL WEEKLY':<26} {'':>5}       {fb_week:>6}")
_mo = _meas * 30 + fb_week * 4.3
print(f"\n{'MLB (measured)':22} {_meas:>7}/day   {_meas*30:>7}/month")
print(f"{'FOOTBALL (derived)':22} {'':>7}       {round(fb_week*4.3):>7}/month")
print(f"{'TOTAL':22} {'':>7}       {round(_mo):>7}/month "
      f"of {PLAN:,}  ({100.0*_mo/PLAN:.0f}%)")
if _mo > PLAN * 0.9:
    print("\n🔴 ABOVE 90% OF PLAN. ⛔ Do not add a second props pull per")
    print("   game day. ⚠️ MLB ends in weeks and frees roughly "
          f"{_meas*30:,}/month -- but until it does, this is the ceiling.")
else:
    print(f"\n✅ FITS, with {PLAN - round(_mo):,} credits of headroom.")
print(f"{backups} backup run(s)/day cost 0 while the primary lands (freshness guard)")
# ⛔ `props-player` IS NOT FREE. It is priced in the FOOTBALL block above,
# not in COST, so a bare "not in COST" test listed the single most
# expensive football pull as free -- directly contradicting the 198/run
# printed six lines earlier. ⚠️ A cost tool that contradicts itself is the
# same class of failure as one that under-counts (ledger rule 68).
PAID_ELSEWHERE = {"props-player"}
free = [m for m in ALL_MODES if m not in COST and m not in PAID_ELSEWHERE]
print(f"free modes (statsapi or local compute): {', '.join(free)}")
# ⛔ THE OLD 30/31-DAY BLOCK IS GONE. It multiplied `per_day`, which no
# longer holds anything now that MLB is measured and football is weekly,
# so it printed "0 of 20000 ✅ fits" beside a real total of 13,406.
# 🔴 A LINE THAT SAYS ✅ WHILE THE REAL NUMBER IS ELSEWHERE IS WORSE THAN
# NO LINE. The monthly verdict is printed once, above, from both halves.

# ⚠️ MLB'S CRONS RUN `converge`, WHICH HAS NO CRON-VISIBLE MODE LIST, so
# they are UNMAPPABLE BY DESIGN -- not broken.
# ⛔ THE OLD MESSAGE SAID "the workflow will now FAIL on these" AND EXITED
# 1. That is a false alarm on every MLB cron, and a tool that cries wolf
# is a tool nobody reads -- which is exactly how tonight's three real
# defects survived being green for days.
_conv = [c for c in unmapped if c not in LEAGUE_OF]
if _conv:
    print(f"\n⚠️ {len(_conv)} MLB cron(s) run `converge` and cannot be priced "
          f"from the schedule.")
    print("   Their real cost is the MEASURED figure above, not a ceiling.")
_real = [c for c in unmapped if c in LEAGUE_OF]
if _real:
    print(f"\n🔴 GENUINELY UNMAPPED: {_real}")
    sys.exit(1)
