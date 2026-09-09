#!/usr/bin/env python3
"""Projected CFBD call volume, DERIVED FROM THE DEPLOYED WORKFLOW.

🔴 WHY THIS EXISTS, AND IT COST US THE TRENDS TAB FOR FIVE DAYS.
`[2026-09-09]` CFBD answered **HTTP 429 on every endpoint from 2026-09-06
to at least 09-09** — games, player game, plays, roster — and the college
Trends table and stored schedule froze solid. **Nothing in this repo knew
how many CFBD calls it was making.** The Odds API has had `budget.py`
since August precisely because "a budget in a comment is a budget that
goes stale"; CFBD had nothing at all, so there was no number to be wrong.

💰 **THE ARITHMETIC, ONCE SOMEONE FINALLY DID IT:**

    CFBD free tier                        1,000 calls / month
    one cfb-probe rebuild                    13 calls
    one fb-scores refresh                     2 calls
    rebuilds actually attempted           ~7 / day  (measured from the
                                          commit history of
                                          backfill-report.txt, 09-06..09-08)
    ⛔ burn BEFORE 2026-09-08's fixes    ~8,200 / month   = 8x the plan

**September's quota resets on the 1st. We spent it in about three days,
and the 429s began on the 6th.** That is the whole story.

⚠️ THE FREE TIER IS 1,000. The Academic tier (a .edu address) is 3,000
and also free; Tier 1 is $1/month for 5,000 and Tier 2 $5/month for
30,000. `[read off collegefootballdata.com/api-tiers, 2026-09-09]`
⛔ **Those numbers are quoted from their pricing page and will go stale.
Re-read the page before trusting them; the DERIVED side is what this
script owns.**

🔴 WHAT THIS SCRIPT OWNS: how many calls the DEPLOYED SCHEDULE implies.
It reads the crons and routing arms out of the workflow and the loop
bounds out of `cfb.py`, exactly as `budget.py` does for the Odds API. If
either moves, this number moves with it.

⚠️ IT MODELS THE FLOOR, NOT THE CEILING, AND SAYS SO. It counts one call
per scheduled build. **Converge retries are the thing that actually blew
the quota** and cannot be priced from a cron, so `--retries N` prices the
same schedule at N attempts a day. **Run it that way before believing a
green headline number.**
"""
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from wfroutes import parse_routes   # the ONE routing-table parser

# 🔴 QUOTED FROM CFBD'S PRICING PAGE, NOT DERIVED. Re-read before trusting.
TIERS = [("Free", 1000), ("Academic (.edu)", 3000),
         ("Tier 1 ($1/mo)", 5000), ("Tier 2 ($5/mo)", 30000)]
PLAN = int(os.environ.get("CFBD_PLAN", "1000"))


def _expand(field, lo, hi):
    out = set()
    for part in str(field).split(","):
        if part == "*":
            out |= set(range(lo, hi + 1))
        elif part.startswith("*/"):
            out |= {x for x in range(lo, hi + 1) if x % int(part[2:]) == 0}
        elif "-" in part:
            a, b = part.split("-")
            out |= set(range(int(a), int(b) + 1))
        elif part.strip():
            out.add(int(part))
    return out


def fires_per_week(cron):
    """How many times a cron fires in a week. ⛔ Day-of-week is UTC and
    that is CORRECT here: we are counting REQUESTS, which happen on the
    runner's clock, not slates, which happen on the reader's."""
    m, h, _dom, _mon, dow = cron.split()
    return len(_expand(dow, 0, 6)) * len(_expand(h, 0, 23)) * len(_expand(m, 0, 59))


def calls_per_build(weeks_played=3):
    """CFBD calls one build of each mode makes, READ OFF `cfb.py`.

    ⛔ Do NOT hardcode these. `build_pace` looped `range(1, 17)` for both
    season types until 2026-09-08 — a flat 32 calls whatever the date, of
    which 29 could only return nothing in week 2. A number typed in here
    would still say 32.
    """
    src = open(os.path.join(ROOT, "cfb.py"), encoding="utf-8").read()
    early_stop = "if empty_run >= 2:" in src
    # /plays: two season types. With the early stop it is the played weeks
    # plus the two empties that prove the end; without it, the full range.
    m = re.search(r"def build_pace.*?for wk in range\((\d+),\s*(\d+)\)", src, re.S)
    lo, hi = (int(m.group(1)), int(m.group(2))) if m else (1, 17)
    span = hi - lo
    plays = ((weeks_played + 2) + 2) if early_stop else (span * 2)
    # build_season: /teams/fbs + /roster + /games x2 + /games/players per
    # played week + postseason
    season = 1 + 1 + 2 + (weeks_played + 1)
    return {"cfb-probe": plays + season, "fb-scores": 2,
            "cfb-teams": 1, "_early_stop": early_stop}


def main():
    retries = 1
    for i, a in enumerate(sys.argv):
        if a == "--retries" and i + 1 < len(sys.argv):
            retries = int(sys.argv[i + 1])
    weeks = int(os.environ.get("CFBD_WEEKS_PLAYED", "3"))

    per = calls_per_build(weeks)
    wf = open(os.path.join(ROOT, ".github/workflows/collect.yml"),
              encoding="utf-8").read()
    weekly = collections.Counter()
    for cron, league, modes in parse_routes(wf):
        if "ncaaf" not in league.split():
            continue
        for mode in modes.split():
            if mode in per:
                weekly[mode] += fires_per_week(cron) * per[mode]

    print("CFBD CALL BUDGET — derived from the deployed workflow and cfb.py")
    print(f"  assuming {weeks} played week(s); "
          f"build_pace early-stop: "
          f"{'ON (32 -> %d calls)' % per['cfb-probe'] if per['_early_stop'] else '🔴 OFF — a flat 32 calls per rebuild'}")
    print()
    print(f"  {'mode':12} {'calls/build':>12} {'builds/wk':>10} {'calls/wk':>10}")
    for mode in sorted(weekly):
        builds = weekly[mode] // per[mode]
        print(f"  {mode:12} {per[mode]:12} {builds:10} {weekly[mode]:10}")
    wk = sum(weekly.values())
    month = round(wk * 52 / 12)
    print(f"  {'':12} {'':12} {'':10} {wk:10}  = {month}/month")

    if retries > 1:
        print(f"\n  ⚠️ AT {retries} ATTEMPTS/DAY (converge retrying a failing "
              f"source — what actually happened):")
        rmonth = round(month * retries)
        print(f"     ~{rmonth}/month")
        month = rmonth

    print()
    worst = None
    for name, lim in TIERS:
        pct = 100.0 * month / lim
        flag = "✅" if pct < 80 else ("⚠️" if pct < 100 else "🔴 OVER")
        print(f"  {name:18} {lim:6}/mo   {pct:5.0f}%  {flag}")
        if name == "Free":
            worst = pct
    print()
    pct = 100.0 * month / PLAN
    if pct >= 100:
        print(f"🔴 {month}/month against a {PLAN} plan — {pct:.0f}%. "
              f"⛔ THE QUOTA WILL RUN OUT MID-MONTH AND EVERY CFBD MODE "
              f"WILL 429 UNTIL THE 1st.")
        return 1
    if pct >= 80:
        print(f"⚠️ {month}/month against a {PLAN} plan — {pct:.0f}%. "
              f"Little headroom for a retry storm.")
        return 0
    print(f"✅ {month}/month against a {PLAN} plan — {pct:.0f}%.")
    print("⚠️ THIS IS A FLOOR. It prices ONE attempt per scheduled build. "
          "Converge retries are what blew the quota in September — "
          "run `--retries 7` to price what actually happened.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
