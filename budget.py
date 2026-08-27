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
ALL_MODES = sorted({m for v in modes.values() for m in v})


def fires(cron):
    """Runs per day for a 5-field cron, ranges and lists included."""
    mins, hours = cron.split()[0], cron.split()[1]

    def n(f):
        if f == "*":
            return 24
        t = 0
        for part in f.split(","):
            if "-" in part:
                a, b = part.split("-")
                t += int(b) - int(a) + 1
            else:
                t += 1
        return t
    return n(mins) * n(hours)


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
print(f"\n{'PAID TOTAL':20} {'':>9} {'':>9} {per_day:>9}/day")
print(f"{backups} backup run(s)/day cost 0 while the primary lands (freshness guard)")
free = [m for m in ALL_MODES if m not in COST]
print(f"free modes (statsapi or local compute): {', '.join(free)}")
for days in (30, 31):
    tot = per_day * days
    room = PLAN - RESERVE - tot
    print(f"\n  {days}-day month: {tot:>6} of {PLAN}   "
          f"{'✅ fits' if room >= 0 else '❌ OVER'}  "
          f"({abs(room)} {'spare after the ' + str(RESERVE) + '-credit reserve' if room >= 0 else 'OVER the reserve'})")
if unmapped:
    print(f"\n🔴 UNMAPPED CRONS -- the workflow will now FAIL on these: {unmapped}")
    sys.exit(1)
