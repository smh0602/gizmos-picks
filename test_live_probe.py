#!/usr/bin/env python3
"""
THE ESPN LIVE PROBE.

🔴 THE POINT OF THIS FILE IS THAT I HAVE NEVER SEEN A REAL ESPN PAYLOAD.
ESPN is blocked from the build sandbox, so every field name in
`liveprobe.py` is a HYPOTHESIS. ⛔ A parser built on unverified guesses
must not come back with a stack trace — it must come back with the REAL
SHAPE, so the next attempt is exact.

So this drives three payloads through it:
  1. one shaped the way I EXPECT — the happy path
  2. one shaped WRONG — every field name changed
  3. one that is not reachable at all

…and asserts that all three write a readable report, that #2 names what
it actually found instead of dying, and that a probe NEVER writes a
product file.

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


def run(payload=None, fail=False):
    """Run the probe with `fetch` stubbed, in a throwaway tree."""
    tmp = tempfile.mkdtemp()
    shutil.copy(os.path.join(ROOT, "liveprobe.py"), tmp)
    os.makedirs(f"{tmp}/data/ncaaf/latest", exist_ok=True)
    # a stored schedule to join against — ids deliberately OVERLAPPING the
    # first three events, so the join has something true to report
    sched = {"season": 2026, "games": [
        {"id": str(401856700 + i), "away": "A", "home": "H"} for i in range(3)]}
    with gzip.open(f"{tmp}/data/ncaaf/latest/schedule-2026.json.gz", "wt") as fh:
        json.dump(sched, fh)

    stub = ("import json, sys\n"
            "import liveprobe as L\n"
            + ("def _f(url, timeout=30):\n"
               "    raise OSError('network is off in this test')\n"
               if fail else
               "PAYLOAD = json.loads(%r)\n"
               "def _f(url, timeout=30):\n"
               "    return 200, PAYLOAD\n" % json.dumps(payload))
            + "L.fetch = _f\n"
              "sys.exit(L.main())\n")
    open(f"{tmp}/drive.py", "w").write(stub)
    r = subprocess.run([sys.executable, "drive.py"], cwd=tmp,
                       env=dict(os.environ, LEAGUE="ncaaf"),
                       capture_output=True, text=True)
    p = f"{tmp}/data/ncaaf/latest/live-probe.json"
    rep = json.load(open(p)) if os.path.exists(p) else None
    other = sorted(os.path.basename(x)
                   for x in glob.glob(f"{tmp}/data/ncaaf/latest/*")
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
