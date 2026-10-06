#!/usr/bin/env python3
"""THE RELAY: an MLB run that reaches the end of its hold starts its successor.

`[Sam, 2026-10-06]` *"a card is on time even when GitHub starts a scheduled
run hours late"*. MEASURED 2026-10-06: the MLB card was due 14:00Z and built
16:02Z. The only MLB run of the morning started 07:15Z (its 01:05Z cron, 370
minutes late), held its 320 minutes and ended 12:42Z; nothing was alive at the
deadline, and queued crons in that window ran a median 282 minutes late.

✅ At the end of its hold, an MLB run (a scheduled one, a push, or a relay
link) dispatches ONE successor (`workflow_dispatch`, `relay=true`) that holds
like a scheduled MLB run. Replayed on the 2026-10-06 run records, a link
started at 12:43Z is the run alive at 14:00Z. The crons are unchanged: they
restart a chain that stopped. MLB only: football runs are one pass each in a
queue per cron, so a holding football chain could buy a pull twice.

⛔ IT MUST NOT RUN AWAY. No successor when:
  - this is not the run's first attempt (a re-run);
  - another MLB run is queued or in progress: that one carries on;
  - RELAY_DAY_CAP links have started today (UTC);
  - `[Sam, 2026-10-06]` the MLB contract owes no card: on a no-games day and
    in the off-season the contract drops its card row (its own no-games
    rule, `freshness.no_games_day`), the chain ends by itself and the crons
    restart it.
⛔ IT MUST NOT SPEND: a link runs `converge` and buys only what the contract
says is due, under the same daily guard (test_relay.py).
Stdlib only. Exit 0 = dispatch the successor, 1 = do not.
"""
import argparse
import datetime
import json
import os
import re
import sys

import freshness as F
import wfroutes

RELAY_DAY_CAP = 5          # links a league may start in one UTC day
LIVE = {"queued", "in_progress", "pending", "waiting", "requested"}
WORKFLOW = os.path.join(".github", "workflows", "collect.yml")


def leagues_of(title, routes):
    """The leagues a collect run is for, read off its run title; None when the
    title does not say (an older dispatch), which counts as every league."""
    m = re.match(r"collect \[(.*)\]$", title or "")
    if not m:
        return None
    words = m.group(1).split()
    if words[:1] == ["cron"]:
        return routes.get(" ".join(words[1:]), {"mlb"})   # unrouted crons fall to mlb
    if words == ["push"]:
        return {"mlb"}
    if words[:1] in (["relay"], ["workflow_dispatch"]) and len(words) > 1:
        return set(words[1:])
    return None


def card_owed(now=None, data="data", picks="picks"):
    """(owed?, why): does the MLB contract carry its card row right now?"""
    rows = F.contract(data, picks, now)
    day = F.due_date(F.CARD, now)
    if any(r[0] == "card" for r in rows):
        return True, "the MLB card for %s is owed" % day
    return False, ("the MLB contract owes no card for %s (no games): the chain ends "
                   "and the crons restart it" % day)


def decide(runs, me, attempt=1, league="mlb", now=None, wf_text="", data="data",
           picks="picks"):
    """(dispatch?, why) for the run `me` at the end of its hold."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if int(attempt or 1) != 1:
        return False, "attempt %s is a re-run: it starts no successor" % attempt
    routes = {}
    for cron, lg, _m in wfroutes.parse_routes(wf_text):
        routes.setdefault(cron, set()).add(lg)
    busy = [r for r in runs if str(r.get("databaseId")) != str(me)
            and r.get("status") in LIVE
            and league in (leagues_of(r.get("displayTitle"), routes) or {league})]
    if busy:
        return False, "another %s run is %s (%s): it carries on" % (
            league, busy[0].get("status"), busy[0].get("displayTitle"))
    today = now.strftime("%Y-%m-%d")
    links = [r for r in runs if r.get("displayTitle") == "collect [relay %s]" % league
             and str(r.get("createdAt") or "")[:10] == today]
    if len(links) >= RELAY_DAY_CAP:
        return False, "%d relay links already started today (cap %d)" % (len(links), RELAY_DAY_CAP)
    owed, why = card_owed(now, data, picks)
    if not owed:
        return False, why
    return True, "%s; no other %s run is queued or running; link %d of %d today" % (
        why, league, len(links) + 1, RELAY_DAY_CAP)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", help="`gh run list --json databaseId,status,displayTitle,createdAt`")
    ap.add_argument("--league", default="mlb")
    ap.add_argument("--run-id", default="0")
    ap.add_argument("--attempt", default="1")
    a = ap.parse_args(argv)
    try:
        runs = json.load(open(a.runs, encoding="utf-8"))
        wf = open(WORKFLOW, encoding="utf-8").read()
        go, why = decide(runs, a.run_id, a.attempt, a.league, wf_text=wf)
    except Exception as e:                      # an unknown is never a dispatch
        go, why = False, "relay could not decide (%s: %s)" % (type(e).__name__, e)
    print("relay: %s — %s" % ("dispatching a successor" if go else "no successor", why))
    return 0 if go else 1


if __name__ == "__main__":
    sys.exit(main())
