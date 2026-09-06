#!/usr/bin/env python3
"""
THE ESPN LIVE PROBE.

🔴 THE POINT OF THIS FILE IS THAT I HAVE NEVER SEEN A REAL ESPN PAYLOAD.
ESPN is blocked from the build sandbox, so every field name in
`liveprobe.py` is a HYPOTHESIS. ⛔ A parser built on unverified guesses
must not come back with a stack trace — it must come back with the REAL
SHAPE, so the next attempt is exact.

So this drives several payloads through it:
  1. one shaped the way I EXPECT — the happy path
  2. one shaped WRONG — every field name changed
  3. one that is not reachable at all
  4. a SWEEP where each URL variant returns a different slate
  5. a slate where ESPN returns 2 of our 10 games — the coverage case
  6. an NFL schedule whose own id does not match and whose `espn`
     column does

…and asserts that all of them write a readable report, that #2 names what
it actually found instead of dying, and that a probe NEVER writes a
product file.

🔴 RUN 1 HAPPENED ON 2026-09-06 AND MOVED THE QUESTION.
✅ Reachable, free, every needed field present, 5 college games live with
a clock — and **25 of 25 event ids WERE our game ids.**
⛔ But it returned **25 events on a day our schedule holds 206 college
games**, and reported *"100% of ESPN events matched"* — true, and the
WRONG DIRECTION. Sections 6–9 exist because of that: sweep the
parameters, and count the games ESPN did NOT send (rules 88, 109).

⚠️ AND THE HISTORY, BECAUSE IT IS THE REASON THIS EXISTS.
`claude/football-todo.md` claimed for two days that "the `live-probe`
mode is built and waiting on one free run from Sam." IT HAD NEVER
EXISTED — the string appeared once in the repo, in a comment. Sam
dispatched it and the run failed. Ledger rules 25–27.
"""
import glob
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, note   # the shared gate — see tcheck.py

ROOT = os.path.dirname(os.path.abspath(__file__))


def good_payload(n_live=2, n_final=3):
    """What I BELIEVE ESPN returns. ⛔ A hypothesis, not a capture."""
    ev = []
    for i in range(n_live + n_final):
        live = i < n_live
        ev.append({
            "id": str(401856700 + i),
            "date": "2026-09-06T00:00Z",
            "competitions": [{
                "status": {
                    "displayClock": "7:21" if live else "0:00",
                    "period": 3 if live else 4,
                    "type": {"state": "in" if live else "post",
                             "shortDetail": "7:21 - 3rd" if live else "Final"},
                },
                "competitors": [
                    {"homeAway": "home", "score": "21",
                     "team": {"displayName": "Home Team %d" % i}},
                    {"homeAway": "away", "score": "17",
                     "team": {"displayName": "Away Team %d" % i}},
                ],
            }],
        })
    return {"events": ev, "leagues": [], "season": {"year": 2026}}


def run(payload=None, fail=False, sched=None, by_url=None, league="ncaaf",
        then=None):
    """Run the probe with `fetch` stubbed, in a throwaway tree.

    `by_url` maps a SUBSTRING of the URL to its own payload, so the
    parameter sweep can be driven with each variant returning a
    different slate — which is the whole point of sweeping."""
    tmp = tempfile.mkdtemp()
    shutil.copy(os.path.join(ROOT, "liveprobe.py"), tmp)
    os.makedirs(f"{tmp}/data/{league}/latest", exist_ok=True)
    # a stored schedule to join against — ids deliberately OVERLAPPING the
    # first three events, so the join has something true to report
    if sched is None:
        sched = {"season": 2026, "games": [
            {"id": str(401856700 + i), "away": "A", "home": "H",
             "start": "2026-09-05T23:00:00.000Z"} for i in range(3)]}
    with gzip.open(f"{tmp}/data/{league}/latest/schedule-2026.json.gz",
                   "wt") as fh:
        json.dump(sched, fh)

    stub = ("import json, sys\n"
            "import liveprobe as L\n"
            + ("def _f(url, timeout=30):\n"
               "    raise OSError('network is off in this test')\n"
               if fail else
               "BY_URL = json.loads(%r)\n"
               "PAYLOAD = json.loads(%r)\n"
               "THEN = json.loads(%r)\n"
               "SEEN = []\n"
               "def _f(url, timeout=30):\n"
               "    # ⏱️ THE RE-CHECK RE-ASKS THE URL IT ALREADY CHOSE, so\n"
               "    # a second hit on the SAME url is the refresh pull.\n"
               "    if THEN is not None and url in SEEN:\n"
               "        return 200, THEN\n"
               "    SEEN.append(url)\n"
               "    for frag, p in (BY_URL or {}).items():\n"
               "        if frag in url:\n"
               "            return 200, p\n"
               "    return 200, PAYLOAD\n"
               % (json.dumps(by_url or {}), json.dumps(payload),
                  json.dumps(then)))
            + "L.fetch = _f\n"
              "sys.exit(L.main())\n")
    open(f"{tmp}/drive.py", "w").write(stub)
    r = subprocess.run([sys.executable, "drive.py"], cwd=tmp,
                       # ⚠️ NO REAL WAIT IN A TEST. The probe's default is
                       # 45s; the behaviour under test is the COMPARISON,
                       # not the sleep.
                       env=dict(os.environ, LEAGUE=league,
                                LIVE_PROBE_RECHECK_S="0"),
                       capture_output=True, text=True)
    p = f"{tmp}/data/{league}/latest/live-probe.json"
    rep = json.load(open(p)) if os.path.exists(p) else None
    other = sorted(os.path.basename(x)
                   for x in glob.glob(f"{tmp}/data/{league}/latest/*")
                   if not x.endswith("live-probe.json"))
    shutil.rmtree(tmp, ignore_errors=True)
    return r, rep, other


# ───────────────────────────────────────────────────────────────
print("\n═══ 1. THE MODE EXISTS THIS TIME ═══")
# ⛔ THE CHECK THAT WOULD HAVE CAUGHT THE ORIGINAL ERROR. The docs claimed
#    a mode that was never wired; nothing asserted it.
cy = open(f"{ROOT}/collect.py").read()
ck("collect.py has a `live-probe` arm", 'mode == "live-probe"' in cy)
ck("it is registered FREE", "live-probe" in cy.split("FREE = (")[1].split(")")[0],
   "ESPN's public scoreboard — no key, no quota")
ck("liveprobe.py exists to be run", os.path.exists(f"{ROOT}/liveprobe.py"))
wf = open(f"{ROOT}/.github/workflows/collect.yml").read()
# ⚠️ REPORTED, NOT ASSERTED — and the distinction is deliberate. The
# dispatch `mode` input is FREE TEXT (`MODES="${{ github.event.inputs.mode
# }}"`), so typing `live-probe` reaches the collector whether or not the
# description advertises it. The description is DOCUMENTATION; the
# functional guard is `test_cron_wiring.py`'s "every mode the form OFFERS
# exists", which is what would have caught the original error.
# ⛔ Asserting the description here would force a `.github/` edit into
# every drop that touches this file — and a hidden folder on Windows is
# exactly what broke the last delivery.
note("dispatch description lists live-probe: %s (documentation only — the "
     "input is free text either way)" % ("yes" if "live-probe" in wf else "NO"))
# ⚠️ THE INPUT IS `mode`, SINGULAR — the instruction that failed said
#    "modes", which is not a field on the form.
ck("the dispatch input is named `mode`, singular",
   "\n      mode:\n" in wf and "\n      modes:\n" not in wf)

print("\n═══ 2. THE HAPPY PATH, ON A PAYLOAD SHAPED AS EXPECTED ═══")
r, rep, other = run(good_payload())
ck("it exits clean", r.returncode == 0, r.stderr[-200:] if r.returncode else "")
ck("it writes a report", rep is not None)
if rep:
    ck("it counts the events", rep.get("events") == 5, str(rep.get("events")))
    ck("it counts what is IN PROGRESS separately from finals",
       rep.get("in_progress") == 2 and rep.get("by_state", {}).get("post") == 3,
       str(rep.get("by_state")))
    ck("it reports which live-state fields were present",
       (rep.get("live_state_fields") or {}).get("with a running clock") == 2,
       str(rep.get("live_state_fields")))
    ck("every field the parser needs is confirmed present, one by one",
       rep.get("all_needed_fields_present") is True,
       str(rep.get("fields_this_parser_needs")))
    # 🔴 THE JOIN IS THE QUESTION THAT DECIDES THE FEATURE.
    j = rep.get("join") or {}
    ck("it measures the id join against our stored schedule",
       j.get("ids_in_common") == 3 and j.get("espn_events") == 5,
       "%s of %s ESPN events matched" % (j.get("ids_in_common"),
                                         j.get("espn_events")))
    ck("a PARTIAL join is called partial, not exact",
       "PARTIAL" in (j.get("verdict") or ""), (j.get("verdict") or "")[:60])
    ck("and it shows the unmatched ones so the gap is checkable",
       len(j.get("unmatched_examples") or []) > 0)

print("\n═══ 3. NOTHING IN PROGRESS — IT MUST REFUSE TO CONCLUDE ═══")
# ⛔ A slate of finals says NOTHING about whether the feed carries a
#    moving clock. Reading it as evidence either way is the defect.
r2, rep2, _ = run(good_payload(n_live=0, n_final=4))
ck("a slate with no live game still writes a report", rep2 is not None)
if rep2:
    ck("it does NOT claim the live fields were checked",
       rep2.get("live_state_fields") is None)
    ck("and it says why, and says to re-run",
       "NOT ANSWERED" in (rep2.get("live_state_note") or "")
       and "Re-run" in (rep2.get("live_state_note") or ""))

print("\n═══ 4. A PAYLOAD SHAPED WRONG — THE CASE I CANNOT RULE OUT ═══")
# 🔴 I HAVE NEVER SEEN A REAL ESPN RESPONSE. If my field names are wrong,
#    the probe has to come back with the REAL shape rather than a crash —
#    otherwise the next attempt is another guess.
weird = {"events": [{"eventId": "999",          # not `id`
                     "matchups": [{"clock": "1:00"}]}],  # not `competitions`
         "meta": {}}
r3, rep3, _ = run(weird)
ck("an unexpected shape still writes a report", rep3 is not None,
   "a stack trace teaches nothing")
if rep3:
    ck("it reports the TOP-LEVEL keys it actually saw",
       "meta" in (rep3.get("payload_shape") or {}).get("top_level", []),
       str((rep3.get("payload_shape") or {}).get("top_level")))
    ck("it reports the EVENT keys it actually saw",
       "eventId" in (rep3.get("payload_shape") or {}).get("event", []),
       str((rep3.get("payload_shape") or {}).get("event")))
    ck("it names each field it needed and marks the missing ones",
       rep3.get("all_needed_fields_present") is False
       and rep3.get("fields_this_parser_needs", {}).get("events[].id") is False,
       "so the next version is exact rather than another guess")

print("\n═══ 5. UNREACHABLE, AND A PROBE THAT WRITES NOTHING ELSE ═══")
r4, rep4, other4 = run(fail=True)
ck("an unreachable source still writes a report", rep4 is not None)
if rep4:
    ck("the report carries the error", bool(rep4.get("error")))
    ck("it warns that this may be the RUNNER, not the feed",
       "runner's network" in (rep4.get("conclusion") or ""),
       "⛔ do not conclude 'ESPN has no live feed' from a blocked runner")
# ⛔ A GREEN RUN WITH AN ERROR REPORT IN IT IS THE SAME DEFECT AS A GREEN
#    LINE ON A RED RUN.
ck("an unreachable probe FAILS the run", r4.returncode != 0,
   "exit %d" % r4.returncode)

# 🔴 THE PROBE CONTRACT: it writes its report and touches nothing else.
ck("the probe writes NO product file — only its own report",
   other == ["schedule-2026.json.gz"],
   "left behind: %s (the schedule is the fixture it read)" % other)


# ══════════════════════════════════════════════════════════════════════
print("\n═══ 6. THE PARAMETER SWEEP — RUN 1 ASKED ONE URL AND COULD NOT "
      "SAY WHY ═══")
# 🔴 RUN 1 (Sam's dispatch, 2026-09-06) RETURNED 25 EVENTS ON A DAY OUR
#    OWN SCHEDULE HELD 206 COLLEGE GAMES. Nothing in that report could
#    explain the gap, because it asked exactly one URL.
# ⛔ Adopting `groups=80` because it is a plausible explanation is the
#    guess this project keeps paying for. The sweep asks every candidate
#    and the NUMBERS choose.
wide = good_payload(n_live=1, n_final=9)      # 10 events
narrow = good_payload(n_live=1, n_final=1)    # 2 events
r6, rep6, _ = run(narrow, by_url={"groups=80": wide})
ck("it sweeps more than one URL", len(rep6.get("variant_sweep") or []) >= 2,
   "variants tried: %d" % len(rep6.get("variant_sweep") or []))
ck("every variant's own event count is reported",
   all("events" in v or "error" in v for v in rep6["variant_sweep"]),
   str([(v["variant"], v.get("events")) for v in rep6["variant_sweep"]]))
ck("🔴 it uses the WIDEST response, not the first",
   rep6.get("events") == 10 and "groups=80" in (rep6.get("variant_used") or ""),
   "chose %r with %s events" % (rep6.get("variant_used"), rep6.get("events")))
ck("and the report says which URL the numbers came from",
   "groups=80" in (rep6.get("url") or ""), rep6.get("url", ""))
# ⚠️ A VARIANT THAT 404s MUST NOT SINK THE RUN — it is one data point
#    about that parameter, not a failure of the probe.
ck("a variant that is fine still carries its http code",
   all(v.get("http") == 200 for v in rep6["variant_sweep"] if "error" not in v))

print("\n═══ 7. 🔴 COVERAGE — THE DIRECTION RUN 1 COULD NOT SEE ═══")
# ⛔ RUN 1 REPORTED "100% OF ESPN EVENTS MATCHED" AND THAT WAS TRUE AND
#    THE WRONG DIRECTION. Matching every event ESPN sent says NOTHING
#    about the games it did not send. A tab that goes live for 25 of 206
#    games and leaves 181 looking unstarted is worse than one honestly
#    not live. Ledger rules 88 and 109.
ten = {"season": 2026, "games": [
    {"id": str(401856700 + i), "away": f"A{i}", "home": f"H{i}",
     "start": "2026-09-05T23:00:00.000Z"} for i in range(10)]}
r7, rep7, _ = run(good_payload(n_live=1, n_final=1), sched=ten)   # 2 of 10
cov = rep7.get("coverage") or {}
ck("coverage is measured at all", cov.get("measurable") is True)
d7 = (cov.get("per_date") or [{}])[0]
ck("🔴 it counts OUR games ESPN did NOT return",
   d7.get("our_games") == 10 and d7.get("ours_that_espn_returned") == 2
   and d7.get("ours_MISSING_from_espn") == 8,
   "ours %s · returned %s · missing %s" % (d7.get("our_games"),
                                           d7.get("ours_that_espn_returned"),
                                           d7.get("ours_MISSING_from_espn")))
ck("a 20% slate is called PARTIAL, loudly",
   "PARTIAL" in (cov.get("verdict") or "") and cov.get(
       "worst_pct_of_ours_present") == 20.0,
   (cov.get("verdict") or "")[:80])
ck("and it names games that were missing, so the gap is checkable",
   len(d7.get("missing_examples") or []) > 0,
   str((d7.get("missing_examples") or [])[:2]))
# ✅ AND THE OTHER SIDE: a feed that returns everything must say FULL,
#    or the warning becomes noise nobody reads.
two = {"season": 2026, "games": [
    {"id": str(401856700 + i), "away": f"A{i}", "home": f"H{i}",
     "start": "2026-09-05T23:00:00.000Z"} for i in range(2)]}
r7b, rep7b, _ = run(good_payload(n_live=1, n_final=1), sched=two)
ck("a feed that returns every one of our games is called FULL",
   "FULL" in ((rep7b.get("coverage") or {}).get("verdict") or ""),
   ((rep7b.get("coverage") or {}).get("verdict") or "")[:60])

print("\n═══ 8. 🔴 THE NFL JOIN, VIA nflverse's OWN `espn` COLUMN ═══")
# 🔴 MEASURED IN RUN 1: 0 OF 16 NFL EVENTS JOINED, because our id is
#    `2026_01_NE_SEA` and ESPN's is `401872656`.
# ✅ nflverse publishes the ESPN id as a column of the same file we
#    already download — 272 of 272 rows of 2026 carry one. So the probe
#    must try BOTH keys and say which one worked.
nflsched = {"season": 2026, "games": [
    {"id": "2026_01_A_B", "espn": "401856700", "away": "NE", "home": "SEA",
     "start": "2026-09-05T20:20"},
    {"id": "2026_01_C_D", "espn": "401856701", "away": "SF", "home": "LA",
     "start": "2026-09-05T20:20"},
]}
r8, rep8, _ = run(good_payload(n_live=1, n_final=1), sched=nflsched,
                  league="nfl")
j8 = rep8.get("join") or {}
ck("🔴 it joins on the espn column when our own id does not match",
   j8.get("matched_on_our_id") == 0 and j8.get("matched_on_our_espn_column") == 2,
   "on id %s · on espn %s" % (j8.get("matched_on_our_id"),
                              j8.get("matched_on_our_espn_column")))
ck("and it SAYS which key it joined on",
   "espn" in (j8.get("join_field") or ""), j8.get("join_field"))
ck("that makes the NFL verdict EXACT, not NONE",
   "EXACT" in (j8.get("verdict") or ""), (j8.get("verdict") or "")[:60])
# ⚠️ NFL STORES A NAIVE LOCAL STAMP AND CFB STORES UTC. Converting both
#    the same way drags every night game back a day.
ck("a naive NFL kickoff is dated by its own local day, not shifted",
   ((rep8.get("coverage") or {}).get("per_date") or [{}])[0].get(
       "et_date") == "2026-09-05",
   str((rep8.get("coverage") or {}).get("per_date")))

print("\n═══ 9. NOTHING JOINED — COVERAGE MUST REFUSE, NOT REPORT 0% ═══")
# ⛔ "0% of our games are live" and "we cannot tell which of our games are
#    live" are DIFFERENT FACTS (rule 103). Reporting the first when the
#    truth is the second invents a finding.
nojoin = {"season": 2026, "games": [
    {"id": "no-overlap-1", "away": "A", "home": "H",
     "start": "2026-09-05T23:00:00.000Z"}]}
r9, rep9, _ = run(good_payload(n_live=1, n_final=1), sched=nojoin)
c9 = rep9.get("coverage") or {}
ck("coverage says it is NOT measurable", c9.get("measurable") is False)
ck("and says why, naming the join as the thing to fix first",
   "join" in (c9.get("why_not") or ""), (c9.get("why_not") or "")[:70])
ck("the join itself still reports NONE", "NONE" in (rep9["join"]["verdict"]))


print("\n═══ 10. ⏱️ DOES IT ACTUALLY MOVE? THE SECOND PULL ═══")
# 🔴 RUN 1 SAID, CORRECTLY, THAT ONE PULL CANNOT MEASURE A REFRESH RATE —
#    and then stopped, which costs another dispatch to answer. ✅ So the
#    probe takes the second pull itself, in the same free run.
ticked = good_payload(n_live=1, n_final=1)
ticked["events"][0]["competitions"][0]["status"]["displayClock"] = "6:02"
r10, rep10, _ = run(good_payload(n_live=1, n_final=1), then=ticked)
rc = rep10.get("refresh_check") or {}
ck("⏱️ a clock that advanced is reported as movement",
   rc.get("games_whose_clock_or_period_changed") == 1
   and "IT MOVES" in (rc.get("verdict") or ""),
   (rc.get("verdict") or "")[:70])
ck("and it shows the before and after, so the claim is checkable",
   (rc.get("example") or {}).get("was") != (rc.get("example") or {}).get("now"),
   str(rc.get("example")))
# ⛔ AND THE HONEST NEGATIVE. Two identical pulls point AT a cache; they
#    do not prove the feed never updates, and the wording must not say so.
r10b, rep10b, _ = run(good_payload(n_live=1, n_final=1),
                      then=good_payload(n_live=1, n_final=1))
rcb = rep10b.get("refresh_check") or {}
ck("an unchanged second pull is reported as unchanged",
   rcb.get("games_whose_clock_or_period_changed") == 0)
ck("⛔ ...but it does NOT conclude the feed is static",
   "not proof" in (rcb.get("verdict") or ""), (rcb.get("verdict") or "")[:70])
# ⛔ AND IT MUST NOT WASTE THE WAIT ON A BOARD OF FINALS.
r10c, rep10c, _ = run(good_payload(n_live=0, n_final=3))
ck("nothing live → no second pull is taken at all",
   rep10c.get("refresh_check") is None
   and "NOT MEASURED" in (rep10c.get("refresh_note") or ""),
   (rep10c.get("refresh_note") or "")[:60])
