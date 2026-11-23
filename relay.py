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
restart a chain that stopped. ~~MLB only: football runs are one pass each in a
queue per cron, so a holding football chain could buy a pull twice.~~

🔴 `[Sam, 2026-11-18]` AND FOOTBALL HAS ITS OWN CHAIN, ONE FOR BOTH LEAGUES. Asked
"Turn the relay on for football?", Sam: "Yes". MEASURED 11-13 -> 11-20: 101
football deadlines were first built more than an hour late (median 130 minutes,
max 477), and the college card was on time at 2 of the 7 deadlines that were
recorded at all. ✅ `collect [relay ncaaf nfl]` (`FOOTBALL`, whatever order a
cron's arm names the leagues) converges both leagues for FB_HOLD_MIN minutes
counted from the JOB's first step, then dispatches ONE successor. Every
scheduled football run ends with the same step, so a football cron that ends
with no link alive restarts the chain. The double buy the old line feared is
answered three ways: a scheduled football run is HELD while a link is alive and
beating (`held`, `freshness.relay_holds`: it builds nothing the contract owes);
a late cron's paid mode stands down once its deadline's pull has landed
(`freshness.stand_down`, #364); and a deadline bought twice is named
(`watchdog.check_double_buys`). A dead chain is named too
(`watchdog.check_relay_chain`).

⛔ IT MUST NOT RUN AWAY. No MLB successor when:
  - this is not the run's first attempt (a re-run);
  - another MLB run is queued or in progress: that one carries on;
  - RELAY_DAY_CAP links have started today (UTC);
  - `[Sam, 2026-10-06]` no MLB card is owed: every stored schedule reading
    says BOTH the last card deadline's day AND the next one's have no games
    (`freshness.no_games_day`, fail closed: no reading = owed). The
    off-season ends the chain by itself and the crons restart it.
    ~~the contract's card row~~: it follows the LAST deadline's day until
    14:00Z, so after every off-day the chain was dead through the next
    morning (Cowork, on 10-02 -> 10-03), the card it exists for.
⛔ AND NO FOOTBALL SUCCESSOR when (`decide_football`): it is a re-run; another
football relay LINK is queued or running (a live football cron, an MLB run, a
push or a hand run never counts: only a link holds the chain); FB_DAY_CAP links
started today (UTC), derived from the hold so a hold change cannot starve the
chain; or no game in either league's stored current-season schedule kicks off
between FB_OWED_BEFORE_D days ago and FB_OWED_AFTER_D days ahead
(`football_owed`, fail closed: a schedule that cannot be read is owed).
⛔ IT MUST NOT SPEND: a link runs `converge` and buys only what the contract
says is due, under the same daily guard (test_relay.py).
Stdlib only. `relay.py <runs>` (or `relay.py decide <runs>`): exit 0 = dispatch
the successor, 1 = do not. `relay.py held <runs> --leagues ...`: exit 0 = this
scheduled football run is held (a link is alive and every league's beat is
fresh), 1 = it is not, and any error is 1 (not held: it converges as before).
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

# ══════════════════════════════════════════════════════════════════════
# 🔴 `[Sam, 2026-11-18]` THE FOOTBALL CHAIN: ONE LINK FOR BOTH LEAGUES.
# ══════════════════════════════════════════════════════════════════════
# ⚠️ ITS LEAGUE STRING IS ONE CANONICAL VALUE. The run title (`collect [relay
#    ncaaf nfl]`), the concurrency group (`collect-ncaaf nfl`) and the busy rule
#    all read it; cron arms name the leagues in either order.
FOOTBALL = "ncaaf nfl"
FOOTBALL_LEAGUES = frozenset(FOOTBALL.split())
# 🔴 THE HOLD COUNTS FROM THE JOB'S FIRST STEP (`Start the job clock`), never
#    from the end of Tests: Tests grew from ~7 to 31 minutes (measured 11-13 ->
#    11-20: median 20.3, max 31.5), and a clock started after them needs a
#    Tests allowance written down that goes stale (rule 166). Counted from the
#    job's start, slower Tests only shorten the hold; they can never push a link
#    into the 350-minute kill. ⚠️ 280, ~~290~~ (the design's): re-measured
#    11-13 -> 11-20, the longest football pass was 36.8 minutes (`4 7`, college,
#    11-19), not 22.1, and the steps after Converge took up to 16.3 (ROOM_MIN).
FB_HOLD_MIN = 280
# ⚠️ DERIVED FROM THE HOLD, so a hold change can never starve the chain: every
#    full hold a day, one that straddles midnight, and two restarts.
FB_DAY_CAP = 1440 // FB_HOLD_MIN + 3
# ⚠️ THE ROOM A LINK NEEDS AFTER ITS HOLD, under the job's `timeout-minutes`
#    (read only by the clock test): the longest football pass measured 11-13 ->
#    11-20 (36.8) + the longest steps after Converge (16.3) + the second league's
#    share of a two-league pass. FB_HOLD_MIN + ROOM_MIN must fit the job clock.
ROOM_MIN = 60
# ⚠️ `[2026-11-20, review]` THE LONGEST LINK PASS, both leagues, from the first
#    league's beat to the pass's push: ROOM_MIN's allowance less the 16.3 minutes
#    of steps after Converge, i.e. the longest football pass measured (36.8) and
#    the second league's share. test_relay.py §8e holds it inside ROOM_MIN.
LINK_PASS_MAX_MIN = 43
# The Converge step's sleep between two passes (its `SLEEP=900`; test_relay.py §8e
# reads it from the workflow, so the two cannot drift).
LINK_SLEEP_MIN = 15
# A scheduled football run is held only while the link BEATS: a hung link
# stops holding the crons back after this long (`held`).
# 🔴 `[2026-11-20, review]` DERIVED FROM THE LINK'S OWN CYCLE (~~60~~, the design's,
#    sized when the longest pass was 22.1 minutes). A link writes each league's beat
#    at the START of that league's converge, but the pass reaches main only after
#    both leagues, the gates and push_retry, and a cron reads the beat on main. So
#    just before pass k+1 lands, that beat is a whole pass, the sleep and the next
#    whole pass old. At 60 the hold lapsed around every heavy pass (the cfb-probe
#    sweep; a props pull and HC's card), exactly the passes that spend, and a late
#    cron then converged, and could buy, beside the link's unpushed pass.
#    test_relay.py §8e drives the real Converge step and asks `held` at every minute.
HELD_BEAT_MIN = 2 * LINK_PASS_MAX_MIN + LINK_SLEEP_MIN
# ⚠️ ABOVE THE WORST SIMULATED HANDOVER GAP (~110 minutes) AND HELD_BEAT_MIN: no
#    football link has passed for this long while a game is near ->
#    `relay:football` (watchdog).
RELAY_BEAT_GRACE_MIN = 150
# A football game within this window (days before / after now) owes the chain.
FB_OWED_BEFORE_D, FB_OWED_AFTER_D = 3, 8
BEAT_FILE = "relay-beat.json"     # data/<lg>/latest/, written by a link's converge pass


def chain_of(league):
    """The chain a run's league field belongs to: "mlb", or FOOTBALL for nfl, ncaaf
    or both in either order. ⛔ Anything else raises (an unknown is never a dispatch)."""
    words = set(str(league or "").split())
    if words == {"mlb"}:
        return "mlb"
    if words and words <= FOOTBALL_LEAGUES:
        return FOOTBALL
    raise ValueError("no relay chain for league %r" % (league,))


def _link_chain(title):
    """The chain a relay link's title names, or None for any other run."""
    m = re.match(r"collect \[relay (.*)\]$", title or "")
    if not m:
        return None
    try:
        return chain_of(m.group(1))
    except ValueError:
        return None


def links_of(runs, me, chain):
    """The LIVE relay links of `chain` other than `me` (title `collect [relay <leagues>]`
    with the same league SET). ⛔ Only a link: a live cron, a push or a hand run is not."""
    return [r for r in runs if str(r.get("databaseId")) != str(me)
            and r.get("status") in LIVE and _link_chain(r.get("displayTitle")) == chain]


def football_owed(now=None, data="data"):
    """(owed?, why): does a football game kick off in either league's stored
    current-season schedule between FB_OWED_BEFORE_D days ago and FB_OWED_AFTER_D
    days ahead? ⛔ A schedule that cannot be read is owed (fail closed, as MLB's
    `card_owed`: no reading = owed)."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    season = F.current_football_season(now)
    lo = now - datetime.timedelta(days=FB_OWED_BEFORE_D)
    hi = now + datetime.timedelta(days=FB_OWED_AFTER_D)
    for lg in sorted(FOOTBALL_LEAGUES):
        path = os.path.join(data, lg, "latest", "schedule-%d.json.gz" % season)
        kicks = F.kickoffs_utc(lg, path)
        if kicks is None:
            return True, "the %s schedule (%s) cannot be read: a football link is owed (fail closed)" % (
                lg, path)
        near = sorted(k for k in kicks if lo <= k <= hi)
        if near:
            return True, "a %s game kicks off %s, inside %d days back / %d ahead" % (
                lg, near[0].strftime("%Y-%m-%d %H:%MZ"), FB_OWED_BEFORE_D, FB_OWED_AFTER_D)
    return False, ("no football game kicks off between %s and %s by either league's stored %d "
                   "schedule: the chain ends and the crons restart it" % (
                       lo.strftime("%Y-%m-%d"), hi.strftime("%Y-%m-%d"), season))


def football_chain_on(wf):
    """(on?, why): is the football chain SWITCHED ON in the collect.yml `wf` (a path or its
    text: the DEPLOYED one, for the watchdog)? On = its routing step (`id: mode`) names the
    chain (`echo "relay_league=ncaaf nfl"`, a line that is not a comment) AND FB_DAY_CAP lets
    a link start. `[2026-11-20, review]` A beat file left on main is no evidence: after a
    switch-off (the previous collect.yml uploaded again, or FB_DAY_CAP 0) the old beats stay,
    and `relay:football` read DEGRADED all season, saying a cron would restart the chain."""
    if FB_DAY_CAP <= 0:
        return False, "relay.FB_DAY_CAP is %d: no football relay link may start" % FB_DAY_CAP
    import wfparse
    route = wfparse.step_run(wf, step_id="mode") or ""
    if not any(l.strip().startswith('echo "relay_league=%s"' % FOOTBALL) for l in route.splitlines()):
        return False, "the deployed collect.yml's routing step names no football chain"
    return True, "the deployed collect.yml routes the football chain (%s)" % FOOTBALL


def decide_football(runs, me, now, data="data"):
    """(dispatch?, why) for a football run at its end (R2). The re-run rule is decide()'s."""
    holding = links_of(runs, me, FOOTBALL)
    if holding:
        return False, "football relay link %s is %s: it carries on" % (
            holding[0].get("databaseId"), holding[0].get("status"))
    today = now.strftime("%Y-%m-%d")
    started = [r for r in runs if _link_chain(r.get("displayTitle")) == FOOTBALL
               and str(r.get("createdAt") or "")[:10] == today]   # today's (UTC) links only
    if len(started) >= FB_DAY_CAP:
        return False, "%d football relay links already started today (cap %d)" % (
            len(started), FB_DAY_CAP)
    owed, why = football_owed(now, data)
    if not owed:
        return False, why
    return True, "%s; no football relay link is queued or running; link %d of %d today" % (
        why, len(started) + 1, FB_DAY_CAP)


def beat_age_min(lg, now, data="data"):
    """Minutes since league `lg`'s last football link pass began (its beat), or
    None when there is no readable beat."""
    try:
        with open(os.path.join(data, lg, "latest", BEAT_FILE), encoding="utf-8") as fh:
            at = datetime.datetime.strptime(json.load(fh)["at"], "%Y-%m-%dT%H:%M:%SZ")
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return (now - at.replace(tzinfo=datetime.timezone.utc)).total_seconds() / 60.0


def held(runs, me, leagues, now=None, data="data"):
    """(held?, why) for a SCHEDULED football run before it converges (R4): a live
    football link other than itself is listed AND every league it routes has a beat
    younger than HELD_BEAT_MIN. ⛔ Anything else is not held (it converges as before)."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    lgs = str(leagues or "").split()
    if not lgs or chain_of(" ".join(lgs)) != FOOTBALL:
        return False, "%r is not a football run" % (leagues,)
    alive = links_of(runs, me, FOOTBALL)
    if not alive:
        return False, "no football relay link is queued or running"
    ages = {lg: beat_age_min(lg, now, data) for lg in lgs}
    for lg in lgs:
        if ages[lg] is None or not 0 <= ages[lg] < HELD_BEAT_MIN:
            return False, ("football relay link %s is %s, but the %s beat is %s (held only while "
                           "it is under %d minutes old)" % (
                               alive[0].get("databaseId"), alive[0].get("status"), lg,
                               "missing" if ages[lg] is None else "%.0f minutes old" % ages[lg],
                               HELD_BEAT_MIN))
    return True, ("football relay link %s is %s and beat %s: it converges %s and verifies it "
                  "on its own pass" % (alive[0].get("databaseId"), alive[0].get("status"),
                                       ", ".join("%s %.0f min ago" % (lg, ages[lg]) for lg in lgs),
                                       " ".join(lgs)))


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


def card_owed(now=None, data="data"):
    """(owed?, why): is an MLB card due at the last card deadline or the next?"""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    last, nxt = F.due_date(F.CARD, now), F.et_date(F.next_due(F.CARD, now))
    if F.no_games_day(last, data) and F.no_games_day(nxt, data):
        return False, ("no MLB games on %s or %s by every stored schedule: the chain ends "
                       "and the crons restart it" % (last, nxt))
    return True, "an MLB card is owed for %s or %s" % (last, nxt)


def decide(runs, me, attempt=1, league="mlb", now=None, wf_text="", data="data"):
    """(dispatch?, why) for the run `me` at the end of its hold."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if int(attempt or 1) != 1:
        return False, "attempt %s is a re-run: it starts no successor" % attempt
    if chain_of(league) == FOOTBALL:              # `[Sam, 2026-11-18]` ⛔ an unknown raises
        return decide_football(runs, me, now, data)
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
    owed, why = card_owed(now, data)
    if not owed:
        return False, why
    return True, "%s; no other %s run is queued or running; link %d of %d today" % (
        why, league, len(links) + 1, RELAY_DAY_CAP)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # ⚠️ `relay.py <runs> --league mlb ...` IS TODAY'S CLI AND STAYS IT: the deployed
    #    workflow calls it that way until Sam uploads the staged one.
    cmd = argv.pop(0) if argv[:1] in (["decide"], ["held"]) else "decide"
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", help="`gh run list --json databaseId,status,displayTitle,createdAt`")
    ap.add_argument("--league", default="mlb")
    ap.add_argument("--leagues", default=FOOTBALL, help="held: the leagues this run routes")
    ap.add_argument("--run-id", default="0")
    ap.add_argument("--attempt", default="1")
    ap.add_argument("--data", default="data")
    a = ap.parse_args(argv)
    if cmd == "held":
        try:
            runs = json.load(open(a.runs, encoding="utf-8"))
            go, why = held(runs, a.run_id, a.leagues, data=a.data)
        except Exception as e:                  # an unknown is never held
            go, why = False, "relay could not tell (%s: %s): not held" % (type(e).__name__, e)
        print("relay: %s — %s" % ("HELD" if go else "not held", why))
        return 0 if go else 1
    try:
        runs = json.load(open(a.runs, encoding="utf-8"))
        wf = open(WORKFLOW, encoding="utf-8").read()
        go, why = decide(runs, a.run_id, a.attempt, a.league, wf_text=wf, data=a.data)
    except Exception as e:                      # an unknown is never a dispatch
        go, why = False, "relay could not decide (%s: %s)" % (type(e).__name__, e)
    print("relay: %s — %s" % ("dispatching a successor" if go else "no successor", why))
    return 0 if go else 1


if __name__ == "__main__":
    sys.exit(main())
