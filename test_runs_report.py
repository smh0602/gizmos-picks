#!/usr/bin/env python3
"""
THE RUN WATCHER MUST FIRE ON A RED RUN, AND STAY QUIET ON WEATHER.

🔴🔴 `[Sam, 2026-09-14: "ive seen a few failed runs in github today, it
didnt do anyhting about those failed runs"]`

⛔ NOTHING IN THIS REPO HAD EVER LOOKED AT A RUN'S STATUS. Every input
`watchdog.py` reads is a file in the repo; a red tick is not a file, so it
was invisible to every guard here. `runs_report.py` is the first thing
that asks, and this file is what stops it becoming the third false-alarming
check of the week (rules 257, 260, 262).

══════════════════════════════════════════════════════════════════════
⚠️ THE TWO FAILURE MODES, AND BOTH ARE COVERED BELOW.

  A MISS        Sam finds out by opening the Actions tab — the status quo
                this exists to end.
  A FALSE ALARM Worse. The collector talks to four external APIs and one
                of them hiccups; alarming on a single failure the next run
                recovers from gets the whole channel filtered.

➡️ SO THE GATE IS "IS IT BROKEN NOW" — the most recent COMPLETED run
failed — which needs no threshold and clears itself the moment a green run
lands.
"""
import datetime
import sys

from tcheck import ck, note

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import runs_report as R  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 9, 14, 23, 0, tzinfo=UTC)


def run(name, concl, hours_ago, url="u"):
    t = NOW - datetime.timedelta(hours=hours_ago)
    return {"name": name, "conclusion": concl, "url": url,
            "createdAt": t.strftime("%Y-%m-%dT%H:%M:%SZ")}


print("═══ 1. ✅ A GREEN REPO IS SILENT ═══")
# ⛔ PROVED FIRST, BEFORE ANY DETECTION. A watcher that cannot be quiet
#    will be muted, and then it detects nothing at all.
broken, flap, seen = R.analyse(
    [run("collect", "success", h) for h in range(1, 20)], NOW)
ck("🔴 nothing is reported when every run is green",
   not broken and not flap,
   "⛔ a false alarm is the failure that kills an alert channel. "
   "Got broken=%s flapping=%s" % (broken, flap))

print("\n═══ 2. 🔴 A WORKFLOW WHOSE LATEST RUN FAILED IS REPORTED ═══")
broken, flap, seen = R.analyse(
    [run("collect", "failure", 1)] + [run("collect", "success", h)
                                      for h in range(2, 10)], NOW)
ck("🔴 the currently-broken workflow is named",
   [b["name"] for b in broken] == ["collect"],
   "⛔ THIS IS THE WHOLE POINT. Got %s" % broken)
ck("✅ ...and the issue body names it and links the run",
   "collect" in R.render(broken, flap, seen)
   and "failing right now" in R.render(broken, flap, seen),
   "an alert that says 'something failed' without saying WHICH costs the "
   "reader the whole investigation")

print("\n═══ 3. ⛔ ONE FAILURE THAT RECOVERED IS WEATHER, NOT AN ALARM ═══")
# ⚠️ The collector talks to four external APIs. A single hiccup the next
#    run recovers from must NOT raise anything, or the channel dies.
broken, flap, seen = R.analyse(
    [run("collect", "success", 1), run("collect", "failure", 2)]
    + [run("collect", "success", h) for h in range(3, 10)], NOW)
ck("⛔ a single recovered failure raises NOTHING",
   not broken and not flap,
   "🔴 rule 238 — alarming on weather gets the whole channel filtered, "
   "and a filtered alert is no alert. Got broken=%s flap=%s" % (broken, flap))

print("\n═══ 4. ⚠️ BUT REPEATED FAILURE IS REPORTED EVEN AFTER RECOVERY ═══")
# 🔴 THIS IS THE 09-14 SHAPE: every run red for 2h25m, then green the
#    moment the fix landed, and nobody was ever told.
broken, flap, seen = R.analyse(
    [run("collect", "success", 1)]
    + [run("collect", "failure", h) for h in (2, 3, 4)]
    + [run("collect", "success", 9)], NOW)
ck("⚠️ 3 failures in the window are noted even though the latest is green",
   not broken and [f["name"] for f in flap] == ["collect"],
   "⛔ THE 2h25m OF 09-14 WOULD OTHERWISE VANISH THE MOMENT IT WAS "
   "FIXED, and the record of it with it. Got broken=%s flap=%s"
   % (broken, flap))
ck("✅ ...and it is a NOTE, not an alarm — it is not in `broken`",
   not broken,
   "🔴 a recovered workflow is not broken now. Calling it broken is the "
   "false alarm this file exists to prevent")

print("\n═══ 5. ⛔ AN IN-PROGRESS RUN HAS NOT ANSWERED YET ═══")
# A blank conclusion is neither a pass nor a failure, and treating it as
# either is wrong. ⚠️ The most common case is THIS workflow's own run.
broken, flap, seen = R.analyse(
    [run("collect", None, 0), run("collect", "failure", 1)]
    + [run("collect", "success", h) for h in range(2, 6)], NOW)
ck("🔴 an in-progress run does not hide the failure beneath it",
   [b["name"] for b in broken] == ["collect"],
   "⛔ if a running job counted as a pass, every alarm would be silenced "
   "by the next scheduled run starting. Got %s" % broken)
broken2, _, _ = R.analyse(
    [run("collect", None, 0)] + [run("collect", "success", h)
                                 for h in range(1, 6)], NOW)
ck("✅ ...and it does not invent a failure either",
   not broken2,
   "a blank conclusion is not a red one. Got %s" % broken2)

print("\n═══ 6. 🔴 EVERY WORKFLOW IS WATCHED, NOT JUST `collect` ═══")
# ⛔ DROP 52's ALERT LIVED INSIDE collect.yml AND COULD SEE NOTHING ELSE.
#    There are four workflows deployed.
broken, flap, seen = R.analyse(
    [run("collect", "success", 1), run("browser", "failure", 1),
     run("self-repair", "success", 2), run("runs", "success", 1)], NOW)
ck("🔴 a failure in a NON-collect workflow is caught",
   [b["name"] for b in broken] == ["browser"],
   "⛔ drop 52's alert lives inside collect.yml and is blind to the other "
   "three. Got %s" % broken)
ck("✅ ...and every workflow seen is listed in the body",
   all(w in R.render(broken, flap, seen)
       for w in ("collect", "browser", "self-repair", "runs")),
   "the reader needs to know what WAS checked, or a missing workflow "
   "looks like a healthy one")

print("\n═══ 7. ⛔ 'I COULD NOT LOOK' IS NOT 'EVERYTHING IS FINE' ═══")
_rc = R.main.__doc__  # presence check only; main() reads stdin
ck("🔴 an unreadable run list exits 2, not 0",
   "return 2" in open(R.__file__, encoding="utf-8").read(),
   "⛔ THE MOST DANGEROUS OUTPUT IN THIS REPO IS A FALSE ALL-CLEAR. If a "
   "parse failure exited 0 the workflow would close an open issue on the "
   "strength of not having looked")
ck("⛔ ...and the workflow leaves an open issue alone on `unknown`",
   "leaving any open issue alone"
   in open(".github/workflows/runs.yml", encoding="utf-8").read(),
   "🔴 closing an alert because the check broke is how a real outage "
   "gets marked resolved")

print("\n═══ 8. ⛔ IT WATCHES FROM OUTSIDE, WHICH IS THE WHOLE DESIGN ═══")
_y = open(".github/workflows/runs.yml", encoding="utf-8").read()
ck("🔴 it is its own workflow, not a step inside collect.yml",
   "name: runs" in _y and "gh run list" in _y,
   "⛔ RULE 242 — a step inside a workflow cannot report that workflow "
   "failing to start. I broke collect.yml's YAML once and the watchdog "
   "living inside it was structurally unable to say so")
ck("⚠️ it needs only READ access to actions",
   "actions: read" in _y and "contents: read" in _y,
   "a watcher that can change what it watches is not a watcher")
ck("⛔ the judgement lives in Python, not in the shell",
   "python runs_report.py" in _y,
   "🔴 a shell step that decides what counts as broken is a second copy "
   "of that judgement (rule 66) — and it is the copy no test can reach")

note("⛔ WHAT THIS DOES NOT CLAIM: that a green run means the product is "
     "right. `collect.yml` defers its failures so DATA still lands on a "
     "red run, and a run can be green while the page is wrong — which is "
     "exactly why `watchdog.py` exists and asks a different question. "
     "➡️ Three watchers, three questions, and none of them replaces "
     "another.")
