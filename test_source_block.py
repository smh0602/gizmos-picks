#!/usr/bin/env python3
"""
🔴 A THIRD-PARTY SOURCE THAT WILL NOT SERVE US IS A KNOWN STATE.

Sam, 2026-09-09: *"i keep getting emails saying the collect run is
failing."* **Every college run and every NFL run was red, on a loop** —
46 football runs a day — for two states that were already diagnosed,
already recorded, and had no action left in them:

    ncaaf   CFBD answered 429 on every endpoint from 09-06. The monthly
            quota was spent. Sam had already upgraded the key.
    nfl     nflverse has NOT published `stats_player_week_2026` — "that
            release holds 542 assets; those mentioning 2026: NONE". The
            NFL season opened 2026-09-09; week 1 had not been played.

⛔ NEITHER IS A DEFECT IN THIS REPO. `verify_freshness.py` had already
made this exact argument once and won it, about the refused card:

    "22 consecutive red runs for a decision that had already been made
     and recorded. AN ALARM THAT FIRES EVERY FIFTEEN MINUTES GETS
     IGNORED, AND IGNORING RED IS EXACTLY HOW THE ORIGINAL STALENESS
     SURVIVED A WHOLE DAY."

✅ So this is the SAME policy applied to two more recognisable states,
with the same shape — **downgrade to a warning, and BOUND IT** — never a
new licence to be quiet.

WHAT IS PINNED HERE:
  1. the state is read from the report the BUILDER writes, not a second
     copy of the truth
  2. a refusal and a not-yet are different facts with different graces
  3. within grace -> warning; past grace -> the run fails again
  4. MLB is untouched, and so is any stale artifact with no recorded cause
  5. a deliberate stand-down exits 0; an ATTEMPTED fetch that fails still
     exits 1
"""
import datetime
import os
import shutil
import subprocess
import sys
import tempfile

import freshness as F
from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
UTC = datetime.timezone.utc


def _tree(body, sub="ncaaf"):
    """A sandbox data tree carrying one back-fill report."""
    d = tempfile.mkdtemp()
    os.makedirs(f"{d}/latest", exist_ok=True)
    if body is not None:
        with open(f"{d}/latest/backfill-report.txt", "w", encoding="utf-8") as fh:
            fh.write(body)
    return d


def _report(when, failed=(), not_yet=(), extra=""):
    return (f"cfb back-fill at {when}\n"
            f"requested: [2026]\nwritten  : []\n"
            f"failed   : {list(failed)}\n"
            f"not yet  : {list(not_yet)}   (season not started — not a failure)\n\n"
            f"{extra}\n")


NOW = datetime.datetime.now(UTC)

print("\n═══ 1. 🔴 THE STATE IS READ FROM THE BUILDER'S OWN REPORT ═══")
# ⛔ A second place to record "is the source up" would drift out of
#    agreement with the first — the same argument that put `fb-scores`
#    behind `cfb-probe`'s back-off instead of giving it its own.
d = _tree(_report(NOW, failed=[2026],
                  extra="SourceUnavailable: ... regular: HTTPError 429; "
                        "postseason: HTTPError 429."))
b = F.source_block(d, now=NOW)
ck("🔴 a refusal is recognised, with its status code",
   b["state"] == "refused" and "429" in (b["detail"] or ""), str(b))

d = _tree(_report(NOW, not_yet=[2026],
                  extra="stats_player: asset 'stats_player_week_2026.csv.gz' "
                        "not published. That release holds 542 assets"))
b = F.source_block(d, now=NOW)
ck("🔴 'the season has not started' is a DIFFERENT fact",
   b["state"] == "not_yet" and "not published" in (b["detail"] or ""), str(b))

d = _tree(_report(NOW))
ck("✅ a clean report blocks nothing",
   F.source_block(d, now=NOW)["state"] is None,
   "a healthy source must never excuse a stale artifact")

ck("⚠️ and NO report blocks nothing either",
   F.source_block(_tree(None), now=NOW)["state"] is None,
   "an unknown is not an excuse — MLB has no back-fill report at all")

# 🔴 BOTH LISTED: a refusal is the stronger claim and the one with a
#    status code behind it.
d = _tree(_report(NOW, failed=[2026], not_yet=[2025], extra="HTTPError 429"))
ck("🔴 a report claiming BOTH resolves to the refusal",
   F.source_block(d, now=NOW)["state"] == "refused",
   "'we asked and were refused' outranks 'we did not ask'")

print("\n═══ 2. ⛔ THE GRACE IS A BOUND, NOT AN EXEMPTION ═══")
ck("a refusal buys days, not forever",
   0 < F.SOURCE_REFUSED_GRACE_MIN <= 14 * 24 * 60,
   f"{F.SOURCE_REFUSED_GRACE_MIN / 1440:.0f} days — long enough to cover a "
   f"tier upgrade taking effect, short enough that waiting turns back "
   f"into deciding")
ck("⚠️ 'not yet' gets longer, because it resolves on the SPORT's clock",
   F.SOURCE_NOT_YET_GRACE_MIN > F.SOURCE_REFUSED_GRACE_MIN,
   f"{F.SOURCE_NOT_YET_GRACE_MIN / 1440:.0f} days — nflverse publishes "
   f"week 1 after week 1 is played")
ck("⛔ the set of source-backed modes is small and explicit",
   F.SOURCE_BACKED <= {"cfb-probe", "nfl-logs", "fb-scores"},
   f"{sorted(F.SOURCE_BACKED)} — nothing else may claim a source excuse")

print("\n═══ 3. 🔴 DRIVEN: WITHIN GRACE WARNS, PAST GRACE FAILS ═══")
# ⛔ ASSERTED BY RUNNING THE REAL GATE against a real tree, not by
#    reading its source.
def _gate(age_days, state="refused"):
    """Copy the live ncaaf tree, age its report, and run the gate."""
    d = tempfile.mkdtemp()
    shutil.copytree(f"{ROOT}/data/ncaaf", f"{d}/data/ncaaf")
    for f in ("freshness.py", "verify_freshness.py", "tcheck.py",
              "wfroutes.py", "collect.py", "cfb.py", "nfl.py"):
        if os.path.exists(f"{ROOT}/{f}"):
            shutil.copy2(f"{ROOT}/{f}", f"{d}/{f}")
    os.makedirs(f"{d}/picks", exist_ok=True)
    when = NOW - datetime.timedelta(minutes=5)
    body = (_report(when, failed=[2026], extra="HTTPError 429")
            if state == "refused"
            else _report(when, not_yet=[2026], extra="not published."))
    with open(f"{d}/data/ncaaf/latest/backfill-report.txt", "w",
              encoding="utf-8") as fh:
        fh.write(body)
    env = dict(os.environ, LEAGUE="ncaaf",
               SOURCE_REFUSED_GRACE_MIN=str(int(age_days * 1440)))
    r = subprocess.run([sys.executable, "verify_freshness.py"], cwd=d,
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


rc, out = _gate(age_days=30)          # grace far exceeds the real staleness
# ⚠️ ASSERT ON THE ROW, NOT THE WHOLE GATE. The sandbox tree carries
#    other genuinely-stale artifacts (no props board, no card) and those
#    SHOULD still fail — that is the point of the narrowness. What this
#    check owns is whether the BLOCKED row was downgraded.
def _row(text, mode, kind):
    return [l for l in text.splitlines()
            if l.startswith(f"::{kind}::") and mode in l]

ck("🔴 inside the grace the blocked row is a WARNING",
   bool(_row(out, "cfb-probe", "warning")) and "KNOWN state" in out,
   "the warning names the cause, the age and the grace remaining")
ck("⛔ ...and is NOT an error",
   not _row(out, "cfb-probe", "error"),
   "a downgraded row must not also be reported as a failure")
ck("⚠️ ...while an UNblocked stale row still fails the run",
   rc == 1 and any(_row(out, m, "error")
                   for m in ("props-board", "card-fb", "props-player")),
   "the sandbox has no props board — that is a real gap and stays red, "
   "which is how we know the downgrade is narrow")
ck("...and it names the actual reason, not a generic one",
   "429" in out, [l for l in out.splitlines() if "::warning::" in l][:1])

rc2, out2 = _gate(age_days=0.001)     # grace effectively zero
ck("🔴 past the grace the run FAILS again",
   rc2 == 1 and "BLOCKED TOO LONG" in out2,
   "a known state must never become permanent silence")
ck("⛔ ...and it says the next move is a DECISION, not a wait",
   "decision now, not an outage" in out2,
   "change the tier, change the source, or drop the tab")

print("\n═══ 4. ⛔ NOTHING ELSE IS DOWNGRADED ═══")
# 🔴 MLB has no back-fill report, so it cannot claim a source excuse even
#    by accident.
r = subprocess.run([sys.executable, "verify_freshness.py"], cwd=ROOT,
                   capture_output=True, text=True,
                   env=dict(os.environ, LEAGUE="mlb"))
ck("MLB is untouched by any of this",
   "BLOCKED TOO LONG" not in r.stdout and "KNOWN state" not in r.stdout,
   "no report -> no block -> the gate behaves exactly as before")
ck("⚠️ and the downgrade requires the row to be SOURCE-BACKED",
   "card" not in F.SOURCE_BACKED and "props-player" not in F.SOURCE_BACKED,
   "a stale card is never excused by a stale source")

print("\n═══ 5. 🔴 A STAND-DOWN IS NOT AN ERROR; A FAILED FETCH STILL IS ═══")
C = open("collect.py", encoding="utf-8").read()
# 🔴 DRIVEN, NOT READ. Reading the source cannot tell the stand-down's
#    exit from the NEXT branch's exit — the first version of this check
#    tried and was wrong. Run the collector with the back-off armed.
def _standdown(mode):
    d = tempfile.mkdtemp()
    shutil.copytree(f"{ROOT}/data/ncaaf", f"{d}/data/ncaaf")
    for f in os.listdir(ROOT):
        if f.endswith(".py"):
            shutil.copy2(f"{ROOT}/{f}", f"{d}/{f}")
    os.makedirs(f"{d}/picks", exist_ok=True)
    with open(f"{d}/data/ncaaf/latest/backfill-report.txt", "w",
              encoding="utf-8") as fh:
        fh.write(_report(NOW - datetime.timedelta(minutes=1),
                         failed=[2026], extra="HTTPError 429"))
    r = subprocess.run([sys.executable, "collect.py", mode], cwd=d,
                       capture_output=True, text=True,
                       env=dict(os.environ, LEAGUE="ncaaf",
                                CFB_BACKOFF_MIN="180"))
    return r.returncode, r.stdout + r.stderr


for _m in ("cfb-probe", "fb-scores"):
    _rc, _o = _standdown(_m)
    ck(f"🔴 {_m}: a back-off stand-down exits 0",
       _rc == 0 and "SKIPPING" in _o,
       f"exit={_rc}; 46 red runs a day for a decision is the "
       f"alarm-fatigue failure mode")
    ck(f"   ...and says so in the log rather than going quiet",
       "NOTHING FETCHED" in _o, "silence would be the actual defect")
ck("⛔ but a fetch that was ATTEMPTED and returned nothing still does",
   "NOTHING WRITTEN --" in C
   and "sys.exit(1)" in C.split("NOTHING WRITTEN --")[1][:400],
   "we asked and got nothing is an EVENT; standing down is a DECISION")
ck("🔴 and a stand-down must not overwrite a real diagnosis",
   "_srep is None" in C and "overwrite a REAL diagnosis" in C,
   "writing an empty probe report would erase the status code, the body "
   "and the quota block that explain the outage")

note("⚠️ THE GATE IS STILL THE THING THAT REPORTS IT. Standing down keeps "
     "the artifact OUT OF CONTRACT; verify_freshness warns every run and "
     "fails once the grace expires; and the Trends tab prints its own age.")


print("\n═══ 6. 🔴 'FAILED' IS NOT 'THE SOURCE REFUSED US' ═══")
# ⛔ CAUGHT 2026-09-10, BEFORE THIS EVER SHIPPED. The very first real
#    report this function was pointed at read:
#        failed   : [2026]
#        RuntimeError: depth_rank is CONSTANT None across 1,848 rows
#    — OUR OWN BUILD refusing its own output, with CFBD healthy and
#    `endpoints_failed: []`. The first draft called that "the source
#    refused us" and would have downgraded a real bug to a warning for
#    seven days.
# 🔴 A GRACE THAT ANY EXCEPTION CAN CLAIM IS NOT A GRACE, IT IS A MUTE
#    BUTTON. A refusal needs POSITIVE evidence from the source.
d = _tree(_report(NOW, failed=[2026],
                  extra="RuntimeError: depth_rank is CONSTANT None across "
                        "1,848 rows — a join failure, not a result"))
b = F.source_block(d, now=NOW)
ck("🔴 our own RuntimeError is NOT excused",
   b["state"] is None,
   f"{b['detail']} — this is ours and stays red")

d = _tree(_report(NOW, failed=[2026], extra="regular: HTTPError 429"))
ck("✅ an HTTP status IS a refusal",
   F.source_block(d, now=NOW)["state"] == "refused",
   "a status code is evidence about THEM")

d = _tree(_report(NOW, failed=[2026],
                  extra="SourceUnavailable: CFBD returned nothing because "
                        "the request failed"))
ck("✅ ...and so is the typed SourceUnavailable",
   F.source_block(d, now=NOW)["state"] == "refused",
   "the fetch layer raises it only when the FETCH failed")

d = _tree(_report(NOW, failed=[2026], extra="ValueError: something of ours"))
ck("⛔ anything else in `failed:` stays hard",
   F.source_block(d, now=NOW)["state"] is None,
   "the default must be 'this is ours', never 'this is theirs'")
note("⚠️ THIS IS THE WHOLE REASON THE DOWNGRADE IS SAFE. Without it the "
     "grace would have covered every exception this collector can raise.")
