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
import glob
import json
import re
import os
import subprocess
import shutil
import tempfile
import sys

from tcheck import ck, note, section

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import runs_report as R  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 9, 14, 23, 0, tzinfo=UTC)


def run(name, concl, hours_ago, url="u"):
    t = NOW - datetime.timedelta(hours=hours_ago)
    return {"name": name, "conclusion": concl, "url": url,
            "createdAt": t.strftime("%Y-%m-%dT%H:%M:%SZ")}


print("═══ 1. ✅ A GREEN REPO IS SILENT ═══")
# ⛔ PROVED FIRST, BEFORE ANY DETECTION. A watcher that cannot be quiet
#    will be muted, and then it detects nothing at all.
broken, flap, seen, trunc, miss = R.analyse(
    [run("collect", "success", h) for h in range(1, 20)], NOW)
ck("🔴 nothing is reported when every run is green",
   not broken and not flap,
   "⛔ a false alarm is the failure that kills an alert channel. "
   "Got broken=%s flapping=%s" % (broken, flap))

print("\n═══ 2. 🔴 A WORKFLOW WHOSE LATEST RUN FAILED IS REPORTED ═══")
broken, flap, seen, trunc, miss = R.analyse(
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
broken, flap, seen, trunc, miss = R.analyse(
    [run("collect", "success", 1), run("collect", "failure", 2)]
    + [run("collect", "success", h) for h in range(3, 10)], NOW)
ck("⛔ a single recovered failure raises NOTHING",
   not broken and not flap,
   "🔴 rule 238 — alarming on weather gets the whole channel filtered, "
   "and a filtered alert is no alert. Got broken=%s flap=%s" % (broken, flap))

print("\n═══ 4. ⚠️ BUT REPEATED FAILURE IS REPORTED EVEN AFTER RECOVERY ═══")
# 🔴 THIS IS THE 09-14 SHAPE: every run red for 2h25m, then green the
#    moment the fix landed, and nobody was ever told.
broken, flap, seen, trunc, miss = R.analyse(
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
broken, flap, seen, trunc, miss = R.analyse(
    [run("collect", None, 0), run("collect", "failure", 1)]
    + [run("collect", "success", h) for h in range(2, 6)], NOW)
ck("🔴 an in-progress run does not hide the failure beneath it",
   [b["name"] for b in broken] == ["collect"],
   "⛔ if a running job counted as a pass, every alarm would be silenced "
   "by the next scheduled run starting. Got %s" % broken)
broken2, _, _, _, _ = R.analyse(
    [run("collect", None, 0)] + [run("collect", "success", h)
                                 for h in range(1, 6)], NOW)
ck("✅ ...and it does not invent a failure either",
   not broken2,
   "a blank conclusion is not a red one. Got %s" % broken2)

print("\n═══ 6. 🔴 EVERY WORKFLOW IS WATCHED, NOT JUST `collect` ═══")
# ⛔ DROP 52's ALERT LIVED INSIDE collect.yml AND COULD SEE NOTHING ELSE.
#    There are four workflows deployed.
broken, flap, seen, trunc, miss = R.analyse(
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

print("\n═══ 6b. 🔴🔴 GROUPED BY THE WORKFLOW, NOT THE RUN'S DISPLAY NAME ═══")
# ⛔ `gh run list` offers BOTH `name` and `workflowName`, which is itself
#    the evidence they differ. `name` is the RUN's display name, and for a
#    PUSH-triggered run GitHub derives it from the commit message — and
#    both `collect.yml` and `browser.yml` have push triggers.
# 🔴 GROUPING BY `name` WOULD MAKE EVERY PUSH RUN ITS OWN "WORKFLOW": each
#    a set of one, each its own latest, and the flapping count could never
#    reach 3. **A silent false all-clear — the most dangerous output this
#    repo has.** ➡️ Ledger rule 268.
_push = [{"name": "watchdog: health report 2026-09-15T00:00Z",
          "workflowName": "collect", "conclusion": "failure",
          "url": "u", "createdAt": "2026-09-14T22:00:00Z"},
         {"name": "collect[mlb]: converge pass 1",
          "workflowName": "collect", "conclusion": "success",
          "url": "u", "createdAt": "2026-09-14T21:00:00Z"},
         {"name": "Merge pull request #7",
          "workflowName": "collect", "conclusion": "failure",
          "url": "u", "createdAt": "2026-09-14T20:00:00Z"}]
broken, flap, seen, trunc, miss = R.analyse(_push, NOW)
ck("🔴🔴 three runs with three different display names are ONE workflow",
   seen == ["collect"],
   "⛔ if these group by display name, every push run is its own "
   "'workflow' — each its own latest, flapping never reaches 3, and a "
   "broken collector reads as a healthy repo. Got %s" % seen)
ck("🔴 ...and the latest of them decides, so the failure IS reported",
   [b["name"] for b in broken] == ["collect"] and broken[0]["fails_24h"] == 2,
   "the newest completed run failed, and both failures belong to the "
   "same workflow. Got %s" % broken)
ck("✅ ...and a run with only `name` still groups, rather than vanishing",
   R.analyse([{"name": "browser", "conclusion": "failure", "url": "u",
               "createdAt": "2026-09-14T22:00:00Z"}], NOW)[0][0]["name"]
   == "browser",
   "⛔ the fallback matters: if `workflowName` is ever absent, dropping "
   "the row would be a silent miss, which is worse than a wrong name")

print("\n═══ 6c. 🔴🔴 A TRUNCATED LIST IS NOT A CLEAN BILL OF HEALTH ═══")
# ⛔ MEASURED 2026-09-15: ~96 cron runs/day plus push runs, against a
#    `--limit 100` ask. The list covered BARELY A DAY — so `browser`
#    (2/day) and `self-repair` (4/day) could be flooded out of it
#    entirely by `collect`, leaving the watcher blind to exactly the
#    low-frequency workflows it most needs to see.
# 🔴 AND THE COUNTS WOULD HAVE READ AS COMPLETE. A 24h flapping count
#    taken from 20h of data, reported without caveat, is a false
#    all-clear. ➡️ Ledger rule 270.
_fresh = [run("collect", "success", h / 10.0) for h in range(1, 40)]
b, f, seen, trunc, miss = R.analyse(_fresh, NOW)
ck("🔴🔴 a list whose OLDEST run is inside the window is flagged truncated",
   trunc,
   "⛔ if the oldest run returned is younger than the window, the list "
   "did not reach back far enough and every 24h count below it is "
   "understated. Got truncated=%s" % trunc)
# 🔴 ~~`"truncated" in render(...)`~~ REPLACED 2026-09-15. The old form
#    asked for a WORD, and it broke the moment the body was reworded —
#    while the behaviour it cared about was untouched. ⛔ A check a
#    rewrite can break is a check that discourages rewriting.
# ✅ So ask the EXIT CODE, which is the actual interface `runs.yml`
#    branches on, and separately that the body says so. Strictly harder:
#    the old check passed on a body that said "truncated" while main()
#    returned 0.
ck("⛔ ...and that alone breaks the silence, so it cannot pass as healthy",
   R.verdict(b, f, miss, trunc, [], []) != R.EXIT_OK
   and "did not reach back a full"
   in R.render(b, f, seen, trunc, miss),
   "🔴 the whole point is that an undercount must not read as a clean "
   "bill of health. Got verdict=%s"
   % R.verdict(b, f, miss, trunc, [], []))
# ⚠️ AND NOT A COVERAGE VERDICT HERE, WHICH IS CORRECT AND WORTH SAYING:
#    this fixture holds only `collect` runs, so four scheduled workflows
#    read as UNSEEN alongside the truncation. That is a real finding, so
#    the verdict is EXIT_BROKEN. ⛔ "Truncation ALONE exits 3" is a
#    different fixture and is driven in section D3, in an isolated tree
#    with one workflow — asserting it here would be asserting it of a
#    list that has something else wrong with it too.
note("this fixture is truncated AND has %d unseen workflow(s), so its "
     "verdict is %s — coverage-alone is D3's fixture, not this one."
     % (len(miss), R.verdict(b, f, miss, trunc, [], [])))
_deep = [run("collect", "success", h) for h in (0.5, 5, 12, 26)]
ck("✅ ...and a list that DOES reach past the window is not flagged",
   not R.analyse(_deep, NOW)[3],
   "⛔ flagging every list would be rule 238 — the false alarm that gets "
   "the channel filtered")

print("\n═══ 6d. 🔴 A SCHEDULED WORKFLOW WITH NO RUNS IS UNSEEN, NOT HEALTHY ═══")
# 🔴 THE `ncaaf` 19:0x CLASS (rule 251): a cron that declares a run and
#    never lands, invisible because nothing compared the DECLARATION to
#    the reality. ⛔ Nothing in this repo had ever made that comparison.
_sched = R.scheduled_workflows(".")
ck("🔴 the expected set is READ from the workflow files, not named",
   "collect" in _sched and "runs" in _sched and len(_sched) >= 3,
   "⛔ a hardcoded list covers exactly the workflows somebody remembered "
   "(rule 246). Got %s" % sorted(_sched))
# ⚠️ THE NAME IS READ FROM THE FILE, NOT GUESSED. My first version of
#    this check asserted `"claude" not in _sched` — but `claude.yml`
#    declares `name: Claude`, so the needle never appeared either way and
#    the check passed with the cron filter DELETED. **Vacuous, rule 67,
#    seventh time this week.** ✅ Caught by driving it: disabling the
#    filter left the suite green.
_claude_name = None
for _p in glob.glob(".github/workflows/*.yml"):
    _t = open(_p, encoding="utf-8").read()
    if not re.search(r"^\s*-?\s*cron:", _t, re.M):
        _m = re.search(r"^name:\s*(.+)$", _t, re.M)
        if _m:
            _claude_name = _m.group(1).strip()
ck("⛔ ...and a workflow with NO cron is correctly excluded",
   _claude_name is not None and _claude_name not in _sched,
   "🔴 a workflow declaring no schedule is correctly absent from a run "
   "list; flagging it would be a permanent false alarm. Excluded name "
   "must be REAL — got %r against %s" % (_claude_name, sorted(_sched)))
_only = [run("collect", "success", h) for h in (0.5, 5, 12, 26)]
_b, _f, _seen, _t, _miss = R.analyse(_only, NOW)
ck("🔴🔴 a scheduled workflow that produced NO runs is reported",
   "browser" in _miss and "self-repair" in _miss,
   "⛔ 'we saw no runs from it' and 'it is healthy' are different "
   "findings, and only one of them is true. Got missing=%s" % _miss)
ck("✅ ...and the body says UNSEEN rather than healthy",
   "UNSEEN" in R.render(_b, _f, _seen, _t, _miss),
   "🔴 the wording is the whole value — a reader must not take silence "
   "about a workflow as evidence about it")

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


print("\n═══ 8. 🔴🔴 WHICH CRON FIRED THIS RUN? ═══")
# 🔴🔴 THE QUESTION THAT LEFT `ncaaf` 19:0x OPEN FOR SIX DAYS. Section 6d
#    asks whether a WORKFLOW produced any runs. That is not enough: a
#    workflow with 43 crons produces runs all day long while ONE of those
#    43 silently never lands, and `missing` reads it as healthy because
#    the workflow is plainly running.
# ⛔ AND I COULD NOT ANSWER IT BY HAND EITHER. `4 19 * * *` (gamelines)
#    and `18 19 * * *` (props) both land in the 19:00Z hour, GitHub
#    delays both, and a commit message names the MODE, not the cron.
#    **Two measurements disagreed and neither could be resolved.**
# ✅ `run-name:` stamps `github.event.schedule` into the run's display
#    name, which `gh run list` returns as `name`. Free, no commit, and
#    recorded even when the run fails before committing.

_CRONS = R.declared_crons(".")
ck("🔴 the cron list is READ from the workflow files",
   _CRONS.get("collect", {}).get("crons") and
   len(_CRONS["collect"]["crons"]) >= 40 and
   "4 19 * * *" in _CRONS["collect"]["crons"],
   "⛔ a remembered list covers exactly the crons somebody remembered. "
   "Got %d cron(s) for collect" % len(_CRONS.get("collect", {})
                                      .get("crons", [])))
ck("🔴🔴 EVERY cron-declaring workflow stamps its schedule",
   all(d["stamped"] for d in _CRONS.values()) and len(_CRONS) >= 4,
   "⛔ an unstamped workflow's runs cannot be attributed to a cron, so a "
   "cron that never fires is INVISIBLE. Unstamped: %s"
   % [k for k, d in _CRONS.items() if not d["stamped"]])

# 🔴🔴 ...AND SO DOES EVERY WORKFLOW STAGED FOR SAM TO UPLOAD.
# `[2026-09-22]` `docs/upload/t60r.yml` was handed over with no stamp. The
#    check above only reads `.github/workflows/`, so the file was NEVER
#    TESTED before it reached Sam — it went red on `main` the moment he
#    uploaded it, and he had to upload it twice. ⛔ THE CLASS: a cron
#    workflow can only reach `main` by hand, so the staging folder is the
#    LAST place a test can see it. Checked there, with the same reader.
_STAGED = R.declared_crons(".", pattern="docs/upload/*.yml")
ck("🔴🔴 every cron workflow STAGED for upload stamps its schedule too",
   all(d["stamped"] for d in _STAGED.values()),
   "⛔ a file Sam uploads by hand is checked here or nowhere. Unstamped: %s"
   % [k for k, d in _STAGED.items() if not d["stamped"]])

# ── the cron arithmetic, pinned by hand against cron's own grammar ──
# ⛔ NOT READ OFF THE CODE. `budget.py` shipped `*/6` counted as ONE fire
#    a day and printed a plausible number for a week (rule 260 shape).
ck("⚠️ `*/3` in hours is 8 fires a day, not 1",
   sorted(R.parse_cron("9 */3 * * *")["hour"]) == [0, 3, 6, 9, 12, 15, 18, 21],
   "🔴 the exact bug budget.py shipped: a step read as a single value")
ck("⚠️ a list field expands",
   sorted(R.parse_cron("40 1,3,5,13 * * 0")["hour"]) == [1, 3, 5, 13],
   "a comma list is four fires, not one")
ck("⛔ cron's Sunday is 0 AND 7, and Python's is 6",
   R.cron_matches(R.parse_cron("0 12 * * 0"),
                  datetime.datetime(2026, 9, 13, 12, 0, tzinfo=UTC))
   and not R.cron_matches(R.parse_cron("0 12 * * 0"),
                          datetime.datetime(2026, 9, 14, 12, 0, tzinfo=UTC)),
   "🔴 getting this backwards shifts every weekly cron by a day and the "
   "check alarms on a workflow that ran perfectly. 2026-09-13 is a "
   "Sunday, 09-14 a Monday")
ck("⛔ dom and dow both restricted is OR, not AND",
   R.cron_matches(R.parse_cron("0 12 1 * 1"),
                  datetime.datetime(2026, 9, 1, 12, 0, tzinfo=UTC)),
   "🔴 POSIX says `0 0 1 * 1` is 'the 1st OR any Monday'. Treating it as "
   "AND under-counts fires — the false all-clear shape. 2026-09-01 is a "
   "Tuesday the 1st, so only the dom half matches")
ck("⚠️ `5/20` means 'from 5, every 20' — not '5 only'",
   sorted(R.parse_cron("5/20 * * * *")["min"]) == [5, 25, 45],
   "🔴 the SAME grammar bug budget.py shipped, in the other spelling. No "
   "cron in this repo uses `N/M` today, which is exactly why the branch "
   "would rot unwatched until the day one does")
ck("⚠️ a malformed cron is reported, never silently skipped",
   R.parse_cron("4 19 * *") is None and R.parse_cron("") is None,
   "a cron the parser cannot read is a cron nothing is watching")

# ── the detection itself, driven both ways ──
def _r(wf, cron, mins_ago, concl="success"):
    """cron=None builds an UNSTAMPED run — what every run looked like
    before `run-name:` shipped, and what 23 of the first 24 hours of any
    run list will look like on deploy day."""
    t = NOW - datetime.timedelta(minutes=mins_ago)
    name = ("%s [cron %s]" % (wf, cron) if cron
            else "%s[mlb]: converge pass 1" % wf)
    return {"workflowName": wf, "name": name,
            "conclusion": concl, "url": "u",
            "createdAt": t.strftime("%Y-%m-%dT%H:%M:%SZ")}

# NOW is 2026-09-14 23:00Z. `4 19 * * *` was due 19:04Z — 3h56m ago,
# well past the 45-minute grace and inside the window the list covers.
_both = ([_r("collect", "4 19 * * *", 230)]
         + [_r("collect", "18 19 * * *", 218)]
         + [_r("collect", "20 * * * *", m) for m in (40, 100, 160, 1300)])
_missed, _unatt = R.missed_fires(_both, NOW)
ck("✅ a cron that DID land is not reported",
   not any(m["cron"] == "4 19 * * *" for m in _missed),
   "⛔ a guard that fires on correct behaviour is the other failure, not "
   "a safe one. Got %s" % [m["cron"] for m in _missed])

# ⛔ THE BITE: remove ONLY the 19:04 run and keep 19:18. That is exactly
#    the live shape — the hour still has a run, the workflow is plainly
#    healthy, and one cron is missing.
_one = [x for x in _both if "4 19 * * *" not in x["name"]]
_missed2, _ = R.missed_fires(_one, NOW)
ck("🔴🔴 ONE missing cron is caught while its hour-mate lands",
   any(m["cron"] == "4 19 * * *" for m in _missed2)
   and not any(m["cron"] == "18 19 * * *" for m in _missed2),
   "⛔ THIS IS THE `ncaaf` 19:0x FINDING, and nothing in this repo could "
   "make it before. Got missed=%s" % [m["cron"] for m in _missed2])
ck("✅ ...and the body names the cron AND the file",
   "4 19 * * *" in R.render([], [], [], False, (), _missed2)
   and "collect.yml" in R.render([], [], [], False, (), _missed2),
   "🔴 'a cron is missing' with no name is not actionable")

# ── the two ways this guard could false-alarm, both closed ──
# ⛔ DRIVEN, NOT ASSERTED AS A CONSTANT. `R.GRACE_MIN >= 30` would pass
#    with the grace never consulted — the vacuous shape (rule 67).
#    `4 19 * * *` is due 19:04Z; NOW is 23:00Z. The only run for it here
#    landed at 19:19Z, FIFTEEN MINUTES LATE, which is what GitHub
#    actually does to this repo every single day.
_fifteen = ([_r("collect", "4 19 * * *", 221)]
            + [_r("collect", "18 19 * * *", 218)]
            + [_r("collect", "20 * * * *", m) for m in (40, 100, 1300)])
_m_late, _ = R.missed_fires(_fifteen, NOW)
ck("⚠️ a run 15 minutes late still COUNTS as that cron firing",
   not any(m["cron"] == "4 19 * * *" for m in _m_late) and R.GRACE_MIN >= 30,
   "🔴 measured on this repo 2026-09-15: the 19:04 and 19:18 crons land "
   "at ~19:15 and ~19:28 EVERY DAY. A guard that calls that a miss "
   "alarms daily on correct behaviour. Got missed=%s GRACE_MIN=%d"
   % ([m["cron"] for m in _m_late], R.GRACE_MIN))
# ⚠️ AND THE OTHER SIDE: a cron due only MINUTES ago has not been given
#    its grace yet and must not be judged at all.
_young, _ = R.missed_fires([_r("collect", "20 * * * *", 70)],
                           NOW.replace(hour=22, minute=25))
ck("⛔ ...and a cron due 5 minutes ago is not judged yet",
   not any(m["cron"] == "20 * * * *" and m["due"].endswith("22:20Z")
           for m in _young),
   "🔴 judging a fire before GitHub has had its grace turns every "
   "scheduler delay into an alert. Got %s" % [m["due"] for m in _young])
_shallow = [_r("collect", "20 * * * *", 5), _r("collect", "20 * * * *", 65)]
_m_sh, _ = R.missed_fires(_shallow, NOW)
ck("⛔ a fire OLDER than the list reaches is NOT reported missing",
   not any(m["cron"] == "4 19 * * *" for m in _m_sh),
   "🔴 RULE 270: a count over a window you did not verify is a count you "
   "invented. The oldest run here is 65 minutes old, so 19:04 is simply "
   "outside what the list can speak to. Got %s"
   % [m["cron"] for m in _m_sh])

# ── the honesty half: unstamped means 'cannot tell', not 'fine' ──
_tmp = tempfile.mkdtemp()
os.makedirs(os.path.join(_tmp, ".github/workflows"))
open(os.path.join(_tmp, ".github/workflows/x.yml"), "w",
     encoding="utf-8").write("name: x\non:\n  schedule:\n"
                             "    - cron: \"4 19 * * *\"\n")
_m_u, _u = R.missed_fires(_both, NOW, root=_tmp)
ck("🔴🔴 a cron workflow with NO run-name stamp is UNATTRIBUTABLE",
   any(u["name"] == "x" for u in _u) and not _m_u,
   "⛔ 'I could not tell which cron fired' must be reported as that. "
   "Reporting it as MISSED would be a false alarm; reporting nothing "
   "would be a false all-clear. Got unattributable=%s missed=%s"
   % (_u, _m_u))
ck("✅ ...and the body says so in words",
   "cannot be attributed" in R.render([], [], [], False, (), (), _u),
   "🔴 a reader must not take silence about a cron as evidence about it")
shutil.rmtree(_tmp, ignore_errors=True)

# 🔴🔴 THE DAY THE STAMP SHIPS, 23 OF THE 24 HOURS IN THE LIST
#    HAVE NO STAMP. ⛔ Measured on that exact shape before it ever fired:
#    **27 crons reported missing, every one of which had run perfectly.**
#    They simply ran before the run title carried a cron.
# ⚠️ That is `CLAUDE.md`'s worse failure — *"a guard that fires on
#    correct code is the other failure, not a safe one"* — and 27 false
#    findings in the first issue this check ever opens is how an alert
#    channel gets muted on day one.
_fresh_deploy = ([_r("collect", None, m) for m in range(60, 1400, 15)]
                 + [_r("collect", "20 * * * *", m) for m in (5, 45)])
_m_deploy, _ = R.missed_fires(_fresh_deploy, NOW)
ck("🔴🔴 the hour after the stamp ships reports NOTHING missing",
   not _m_deploy,
   "⛔ a cron cannot be judged for a period before its runs were being "
   "stamped — there is no evidence either way, and absence of evidence "
   "reported as a finding is a false alarm. Got %s"
   % [m["cron"] for m in _m_deploy])
# ✅ AND THE FLOOR IS PER WORKFLOW. `browser` runs twice a day, so its
#    first stamped run can be 12 hours behind `collect`'s. A single shared
#    floor would judge `browser` over a window it has no evidence for.
# ⛔ DRIVEN AGAINST A GLOBAL FLOOR, WHICH STAYS GREEN ON THE EASY CASE.
#    My first version of this check used a `browser` with NO stamped runs
#    at all — excluded either way, so a single shared floor passed it.
#    **Vacuous, rule 67.** This shape separates them: `collect` has been
#    stamping for 22h, `browser` for 40 minutes, and `browser`'s 01:37
#    cron fired 21h ago — inside `collect`'s window, outside its own.
_mixed = ([_r("collect", "20 * * * *", m) for m in range(5, 1400, 60)]
          + [_r("browser", "37 13 * * *", 40)])
_m_mixed, _ = R.missed_fires(_mixed, NOW)
ck("✅ ...and the floor is PER WORKFLOW, not one shared clock",
   not any(m["file"] == "browser.yml" for m in _m_mixed),
   "⛔ `collect` stamping for 22h says NOTHING about `browser`, which "
   "fires twice a day and started stamping 40 minutes ago. A shared "
   "floor judges it over a window it has no evidence for — the same "
   "mistake one level up. Got %s"
   % [(m["file"], m["cron"]) for m in _m_mixed])
# ⛔ AND THE BITE: once a workflow HAS been stamping, a cron of its own
#    that goes missing inside that window is still caught.
_live = ([_r("collect", "20 * * * *", m) for m in range(5, 700, 60)]
         + [_r("collect", "18 19 * * *", 218)])
_m_live, _ = R.missed_fires(_live, NOW)
ck("🔴 a cron missing INSIDE the stamped window is still caught",
   any(m["cron"] == "4 19 * * *" for m in _m_live),
   "⛔ the floor must bound the check, never disable it. Got %s"
   % [m["cron"] for m in _m_live])

note("⛔ WHAT THIS DOES NOT CLAIM: that a stamped run means the cron did "
     "its JOB. It means the cron FIRED. A run that fires and collects "
     "nothing is green here and caught by the freshness contract "
     "instead. ➡️ Different question, different watcher.")


# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 DROP: A MISCATEGORISED ALARM IS THE SAME DISEASE AS A FALSE ONE.
#
# `[measured 2026-09-15]` **Issue #6 was OPEN, titled "Gizmo's Picks - a
# workflow is failing", and NOTHING was failing.** Its entire content was
# the truncation warning. ~351 runs/day against `gh run list --limit
# 300`, of which **254 were `pages build and deployment`** — one per
# commit to `main`.
#
# ⛔ SO TWO THINGS WERE WRONG AND ONLY ONE OF THEM IS THE COUNT: the list
#    was short, AND "I cannot see a full day" was filed under an outage
#    title. Sam reads the title from his phone; an outage title on a
#    coverage problem teaches him the title is noise, and the next real
#    outage is the one he scrolls past (rule 238).
# ══════════════════════════════════════════════════════════════════════
section("D1. ⛔ COVER THE WINDOW, DO NOT GUESS A COUNT")

_PER = R.REST_PER_PAGE


def _page_maker(total, span_h, per=None):
    """A fake `/actions/runs` paginator: `total` runs spread over `span_h`."""
    per = per or _PER
    now = datetime.datetime.now(UTC)
    rows = [{"name": "collect [cron 41 * * * *]",
             "display_title": "collect [cron 41 * * * *]",
             "path": ".github/workflows/collect.yml",
             "conclusion": "success",
             "created_at": (now - datetime.timedelta(
                 hours=span_h * i / max(1, total - 1))
             ).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "html_url": "u"}
            for i in range(total)]
    calls = []

    def fetch(page):
        calls.append(page)
        return rows[(page - 1) * per:page * per]
    return fetch, calls


# 🔴🔴 THE DEFECT ITSELF: one page of 100 does NOT cover 24h at this
#    repo's rate, and a collector that stops after one page reports a
#    count it invented (rule 270).
_fetch, _calls = _page_maker(351, 24.0)
_runs, _pages, _covered = R.collect(_fetch, root=".")
ck("🔴🔴 it keeps paging until the 24h window is COVERED",
   _covered and _pages > 1,
   "⛔ 351 runs/day against 100 per page — stopping at page 1 is the "
   "defect that left issue #6 open. Got pages=%d covered=%s runs=%d"
   % (_pages, _covered, len(_runs)))
ck("⚠️ ...and it stops as soon as it IS covered, not at the cap",
   _pages < R.MAX_PAGES and _calls == list(range(1, _pages + 1)),
   "⛔ paging past the answer is wasted API calls on every run of an "
   "hourly workflow. Got pages=%d of a %d cap, calls=%s"
   % (_pages, R.MAX_PAGES, _calls))
# ⚠️ THE STOPPING RULE READS TIMESTAMPS, NOT A COUNT — so a repo that
#    suddenly runs 10x more does not silently under-report.
_fetch10, _ = _page_maker(3510, 24.0)
_r10, _p10, _c10 = R.collect(_fetch10, root=".")
ck("🔴 at 10x the volume it pages further rather than under-reporting",
   _p10 > _pages,
   "⛔ a fixed count is a guess with an expiry date; the rule has to "
   "move with the rate. Got %d page(s) at 10x vs %d at 1x"
   % (_p10, _pages))
# ⛔ AND THE CAP IS HONEST ABOUT ITSELF: a rate past the cap reports
#    NOT covered, which becomes the coverage finding rather than silence.
_fetchcap, _ = _page_maker(5000, 2.0)
_rc, _pc, _cc = R.collect(_fetchcap, root=".")
ck("⛔ past the page cap it reports NOT covered rather than under-counting",
   _pc == R.MAX_PAGES and not _cc,
   "🔴 a cap that silently truncates is the old bug with a new number. "
   "Got pages=%d covered=%s" % (_pc, _cc))
# ✅ AND END OF HISTORY IS COVERAGE, NOT FAILURE — a young repo has
#    nothing older, and flagging that would fire on correct behaviour.
_fetchsmall, _ = _page_maker(12, 1.0)
_rs, _ps, _cs = R.collect(_fetchsmall, root=".")
ck("✅ a short page means end of history, which IS covered",
   _cs and _ps == 1 and len(_rs) == 12,
   "⛔ CLAUDE.md — a guard that fires on correct code is the other "
   "failure. Got pages=%d covered=%s runs=%d" % (_ps, _cs, len(_rs)))

section("D2. 🔴🔴 REST `name` IS THE RUN, NOT THE WORKFLOW")
# ⛔ MEASURED AGAINST THIS REPO'S OWN /actions/runs, 2026-09-15 — not
#    read off the docs, which explain neither field.
#      scheduled + run-name:  name = "collect [cron 9 */3 * * *]"
#      push, pre run-name:    name = "collect"
#    So `.name` is the RUN name whenever `run-name:` is set, and mapping
#    it to `workflowName` would shatter one workflow into one group per
#    run — each its own latest, the flapping count never reaching 3.
#    **A silent false all-clear, the most dangerous output this repo has.**
_NAMES = R.workflow_names(".")
_real = [
    {"name": "collect [cron 9 */3 * * *]",
     "display_title": "collect [cron 9 */3 * * *]",
     "path": ".github/workflows/collect.yml", "conclusion": None,
     "created_at": "2026-09-15T18:20:45Z", "html_url": "u1"},
    {"name": "collect", "display_title": "Add files via upload",
     "path": ".github/workflows/collect.yml", "conclusion": "success",
     "created_at": "2026-08-27T17:08:27Z", "html_url": "u2"},
    {"name": ".github/workflows/collect.yml",
     "display_title": "Fix JSON file path for picks data retrieval",
     "path": ".github/workflows/collect.yml", "conclusion": "failure",
     "created_at": "2026-08-22T21:18:22Z", "html_url": "u3"},
]
_norm = [R.normalise(r, _NAMES) for r in _real]
ck("🔴🔴 three real `collect` runs group under ONE workflow name",
   {n["workflowName"] for n in _norm} == {"collect"},
   "⛔ mapping REST `.name` to workflowName would give %s — three "
   "'workflows' from one. Got %s"
   % (sorted({r["name"] for r in _real}),
      sorted({n["workflowName"] for n in _norm})))
ck("✅ ...and the cron stamp is readable off `name`, which is the RUN title",
   (R.CRON_STAMP.search(_norm[0]["name"] or "") or [None]) and
   R.CRON_STAMP.search(_norm[0]["name"]).group(1).strip() == "9 */3 * * *",
   "⛔ `missed_fires()` reads the stamp out of `name`. If the run title "
   "does not land there, every cron reads as never having fired. Got %r"
   % _norm[0]["name"])
ck("⚠️ a run whose path is not a repo workflow keeps its own name",
   R.normalise({"name": "pages build and deployment",
                "display_title": "pages build and deployment",
                "path": "dynamic/pages/pages-build-deployment"},
               _NAMES)["workflowName"] == "pages build and deployment",
   "⛔ 254 of 351 runs a day are these. They are never in the expected "
   "set, so they must never read as UNSEEN — but they must still group")
ck("⛔ ...and `claude.yml` resolves to its declared name, not its filename",
   _NAMES.get(".github/workflows/claude.yml") == "Claude",
   "🔴 `scheduled_workflows()` keys off the `name:` line, so the "
   "grouping key has to be that same string or the two disagree about "
   "what a workflow is called. Got %r"
   % _NAMES.get(".github/workflows/claude.yml"))

section("D3. 🔴🔴 THE EXIT CODE, DRIVEN END TO END")
# ⚠️ TRAP I HIT WRITING THESE: `main()` reads the WALL clock, so a
#    fixture dated from the module-level `NOW` above goes stale and every
#    cron reads as missed. ✅ So these run in an ISOLATED TEMP TREE with
#    ONE workflow and ONE cron, on timestamps generated relative to
#    `datetime.now()`.


def _tree():
    """A temp repo with exactly one scheduled, stamped workflow."""
    d = tempfile.mkdtemp(prefix="runswatch-")
    os.makedirs(os.path.join(d, ".github/workflows"))
    open(os.path.join(d, ".github/workflows/only.yml"), "w",
         encoding="utf-8").write(
        "name: only\n"
        "run-name: ${{ github.event.schedule && format('only [cron {0}]',"
        " github.event.schedule) || format('only [{0}]',"
        " github.event.event_name) }}\n"
        "on:\n  schedule:\n    - cron: \"41 * * * *\"\n"
        "jobs:\n  x:\n    runs-on: ubuntu-latest\n"
        "    steps:\n      - run: echo hi\n")
    shutil.copy(os.path.join(ROOT, "runs_report.py"), d)
    # ⚠️ runs_report.py imports wfparse (the staged-upload check, 2026-09-23);
    #    a fixture missing a module the script imports tests a crash.
    shutil.copy(os.path.join(ROOT, "wfparse.py"), d)
    return d


def _r_now(concl, minutes_ago, stamped=True):
    t = datetime.datetime.now(UTC) - datetime.timedelta(minutes=minutes_ago)
    return {"workflowName": "only",
            "name": ("only [cron 41 * * * *]" if stamped
                     else "some commit message"),
            "conclusion": concl, "url": "u",
            "createdAt": t.strftime("%Y-%m-%dT%H:%M:%SZ")}


def _exit(runs, tree=None):
    """Run the REAL runs_report.py over `runs`. Returns (rc, stdout)."""
    d = tree or _tree()
    p = subprocess.run([sys.executable, os.path.join(d, "runs_report.py")],
                       input=json.dumps(runs), cwd=d,
                       capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout


# ✅ A COMPLETE, HEALTHY LIST IS SILENT. The 30h-old run is what makes
#    the window covered — and it carries NO cron stamp, so it cannot drag
#    the missed-fire floor back with it.
_clean = ([_r_now("success", 20), _r_now("success", 80)]
          + [_r_now("success", 30 * 60, stamped=False)])
_rc_clean, _out_clean = _exit(_clean)
ck("✅ a complete healthy list exits 0 and says nothing",
   _rc_clean == R.EXIT_OK and _out_clean.strip() == "OK",
   "⛔ if the clean case is not silent, every check below is measuring "
   "noise. Got rc=%d out=%r" % (_rc_clean, _out_clean[:300]))

# 🔴🔴 TRUNCATION ALONE IS A COVERAGE FINDING, NOT AN OUTAGE. This is
#    issue #6, exactly: nothing failing, the list simply too short.
_trunc = [_r_now("success", 20), _r_now("success", 80)]
_rc_t, _out_t = _exit(_trunc)
ck("🔴🔴 truncation ALONE exits 3, not 1",
   _rc_t == R.EXIT_COVERAGE,
   "⛔ THIS IS ISSUE #6. Exiting 1 files 'I cannot see a full day' under "
   "'a workflow is failing', with nothing failing. Got rc=%d" % _rc_t)
# ⚠️ ASKED AS "does it CLAIM a failure", not "does the word appear" —
#    the body legitimately contains "No workflow is reported failing",
#    and my first version of this check failed on that sentence.
ck("✅ ...and the body says it is NOT an outage",
   "NOT AN OUTAGE" in _out_t.upper()
   and "failing right now" not in _out_t
   and "cannot answer its own question" in _out_t,
   "🔴 the body is what Sam reads after the title. It must not carry the "
   "outage headline. Got %r" % _out_t[:400])
ck("⛔ ...and it no longer tells anyone to raise a `--limit`",
   "--limit" not in _out_t,
   "🔴 there is no limit to raise any more — the list is paged. Stale "
   "advice in an alert body is how a reader learns to skip the body")

# ⛔ A RED WORKFLOW STILL OUTRANKS TRUNCATION. A short list that also
#    shows a failure is still, first and foremost, a failure.
_both = [_r_now("failure", 20), _r_now("success", 80)]
_rc_b, _out_b = _exit(_both)
ck("🔴🔴 truncation PLUS a red workflow still exits 1",
   _rc_b == R.EXIT_BROKEN,
   "⛔ downgrading a real outage to a coverage note because the list was "
   "also short would be the same bug pointing the other way. Got rc=%d"
   % _rc_b)
ck("✅ ...and that body reports the failure first, truncation after",
   "failing right now" in _out_b
   and _out_b.index("failing right now") < _out_b.lower().index("truncat")
   if "truncat" in _out_b.lower() else "failing right now" in _out_b,
   "🔴 order is the message: the reader must not have to hunt for the "
   "outage under a coverage note")
# ⛔ AND "I COULD NOT LOOK" IS STILL ITS OWN ANSWER, UNCHANGED.
_p_bad = subprocess.run([sys.executable, os.path.join(ROOT, "runs_report.py")],
                        input="not json", capture_output=True, text=True,
                        timeout=60)
ck("⛔ unreadable input still exits 2 — unchanged by this drop",
   _p_bad.returncode == R.EXIT_UNREADABLE,
   "🔴 four codes now, and the third state must not have been clobbered "
   "by adding the fourth. Got rc=%d" % _p_bad.returncode)

section("D4. ⛔ THE COVERAGE FINDING HAS ITS OWN TITLE AND CLEANS UP #6")
_YML = open(os.path.join(ROOT, ".github/workflows/runs.yml"),
            encoding="utf-8").read()


def _live(text):
    """Non-comment lines only.

    ⚠️ TRAP I HIT: asserting `"--limit 300" not in _YML` PASSES ONLY IF
    nobody documents why the limit was wrong — and I had documented it
    three lines above, so the check failed on my own comment. A guard
    that a comment can break is a guard that teaches people not to
    comment.
    """
    return "\n".join(l for l in text.splitlines()
                     if not l.lstrip().startswith("#"))


_LIVE = _live(_YML)
ck("⚠️ the struck-through `--limit 300` survives as a COMMENT",
   "--limit 300" in _YML,
   "⛔ the reason a number was wrong is the only thing that stops it "
   "being chosen again")
ck("🔴🔴 ...and no LIVE line still asks for a fixed count",
   "--limit 300" not in _LIVE and "gh run list" not in _LIVE,
   "⛔ a fixed count is a guess with an expiry date, and 300 had already "
   "expired nine hours after it was raised from 100")
ck("✅ the collection is paged, in Python, from the live step",
   "runs_report.py --collect" in _LIVE,
   "🔴 rule 66 — a shell loop deciding when the window is covered is a "
   "second copy of the judgement, and the copy no test reaches")
_COV_TITLE = "Gizmo's Picks - the run watcher cannot see a full day"
_FAIL_TITLE = "Gizmo's Picks - a workflow is failing"
ck("🔴🔴 the workflow files coverage under its OWN title",
   _COV_TITLE in _LIVE and _FAIL_TITLE in _LIVE
   and _COV_TITLE != _FAIL_TITLE,
   "⛔ one title for two questions is what put 'nothing is failing' "
   "under 'a workflow is failing'. Got coverage title present=%s"
   % (_COV_TITLE in _LIVE))
ck("✅ ...and it branches on the new exit code 3",
   '"$rc" = "3"' in _LIVE and "state=coverage" in _LIVE,
   "🔴 a Python exit code nothing reads is a Python exit code that does "
   "not exist")


def _drive(state, fail_num="", cov_num=""):
    """Run the REAL 'Tell Sam' shell with a fake `gh`. -> the argv log.

    ⛔ THE STEP IS EXECUTED, NOT GREPPED. A check that asserts the
    presence of a sentence passes on a step that prints the sentence and
    then does the opposite (rule 249).
    """
    d = tempfile.mkdtemp(prefix="runstell-")
    log = os.path.join(d, "gh.log")
    gh = os.path.join(d, "gh")
    open(gh, "w", encoding="utf-8").write(
        '#!/bin/bash\nprintf "%s\\n" "$*" >> "$GH_LOG"\n'
        'if [ "$1 $2" = "issue list" ]; then\n'
        '  case "$*" in\n'
        '    *"cannot see a full day"*) echo "$FAKE_COV" ;;\n'
        '    *) echo "$FAKE_FAIL" ;;\n'
        '  esac\nfi\nexit 0\n')
    os.chmod(gh, os.stat(gh).st_mode | 0o111)
    body = None
    for _n, _b in [(n, b) for n, b in _steps(_YML) if "gh issue create" in b]:
        body = _b
    src = re.sub(r"\$\{\{\s*steps\.look\.outputs\.state\s*\}\}", state, body)
    src = re.sub(r"\$\{\{[^}]*\}\}", "x", src)
    sh = os.path.join(d, "step.sh")
    open(sh, "w", encoding="utf-8").write(src)
    open(os.path.join(d, "body.md"), "w").write("x")
    subprocess.run(["bash", sh], cwd=d, timeout=60, capture_output=True,
                   text=True,
                   env=dict(os.environ, PATH=d + os.pathsep + os.environ["PATH"],
                            GH_LOG=log, FAKE_FAIL=fail_num, FAKE_COV=cov_num))
    return open(log, encoding="utf-8").read() if os.path.exists(log) else ""


def _steps(text):
    out, lines, name = [], text.splitlines(), "?"
    for i, ln in enumerate(lines):
        m = re.match(r"^\s*- name:\s*(.+)$", ln)
        if m:
            name = m.group(1).strip()
        m = re.match(r"^(\s*)run:\s*\|", ln)
        if not m:
            continue
        ind, body = len(m.group(1)), []
        for nxt in lines[i + 1:]:
            if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= ind:
                break
            body.append(nxt)
        out.append((name, "\n".join(body)))
    return out


# 🔴 PROVEN ABLE TO SEE A CLOSE FIRST, so "it did not close" cannot pass
#    on a step that did nothing at all (rule 67).
_log_ok = _drive("ok", fail_num="6")
ck("🔴 the harness CAN observe a close — proven on the ok path",
   "issue close 6" in _log_ok,
   "⛔ if the fake `gh` never runs, every assertion below is vacuous. "
   "Got %r" % _log_ok)
_log_cov = _drive("coverage", fail_num="6", cov_num="")
ck("🔴🔴 a COVERAGE finding CLOSES the false 'a workflow is failing' issue",
   "issue close 6" in _log_cov,
   "⛔ THIS IS THE LINE THAT CLEANS UP #6. Nothing is failing, so that "
   "issue is false and must not be left open. Got %r" % _log_cov)
ck("✅ ...and opens the coverage issue under its own title",
   "cannot see a full day" in _log_cov and "issue create" in _log_cov,
   "🔴 closing the wrong issue without filing the right one loses the "
   "finding entirely. Got %r" % _log_cov)
ck("⛔ ...and a coverage finding NEVER opens the failing issue",
   "issue create --title Gizmo's Picks - a workflow is failing"
   not in _log_cov,
   "🔴 that is the miscategorisation this whole drop is about")
# ⛔ A RED WORKFLOW LEAVES THE COVERAGE ISSUE ALONE — outranking it is
#    not the same as resolving it.
_log_bad = _drive("bad", fail_num="", cov_num="9")
ck("⛔ a real outage does not close an open coverage issue",
   "issue close 9" not in _log_bad,
   "🔴 a red workflow outranks a short list; it does not make the list "
   "longer. Got %r" % _log_bad)
ck("✅ ...and it does open the failing issue",
   "issue create" in _log_bad and "a workflow is failing" in _log_bad,
   "⛔ the other half of the contract. Got %r" % _log_bad)
# ⛔ AND `unknown` STILL TOUCHES NOTHING.
_log_unk = _drive("unknown", fail_num="6", cov_num="9")
ck("🔴🔴 `unknown` closes neither issue — 'I could not look' is not 'fine'",
   "issue close" not in _log_unk and "issue create" not in _log_unk
   and "issue edit" not in _log_unk,
   "⛔ closing an alert because the check itself broke is how a real "
   "problem goes quiet. Got %r" % _log_unk)
# ✅ AND `ok` CLEARS BOTH, because both questions are answered.
ck("✅ `ok` closes the coverage issue too",
   "issue close 9" in _drive("ok", fail_num="6", cov_num="9"),
   "🔴 a coverage issue that never closes itself is a permanent red dot "
   "on the repo, which is rule 238 by another route")

note("⛔ WHAT THIS DROP DOES NOT CLAIM: that the run list can never be "
     "short again. It claims the list is now PAGED until the timestamps "
     "say the window is covered, that the page cap failing is REPORTED "
     "rather than silent, and that 'I cannot see a full day' no longer "
     "wears the title of an outage. ➡️ The truncation detector is kept "
     "as the backstop precisely because the collection can still fail.")
note("⚠️ NOT FIXED, REPORTED: when the list IS truncated, `missing` and "
     "`missed_fires` are computed over a window that was not covered — "
     "so an UNSEEN workflow could in principle be an artifact of the "
     "short list rather than a fact about the workflow (`CLAUDE.md`: an "
     "absence in an API response is evidence about the API). Those "
     "findings return 1 and would still file as an outage. It is latent, "
     "not live — #6 had no such finding — and suppressing them is a "
     "behaviour change beyond this drop. ➡️ Sam's call.")


# ══════════════════════════════════════════════════════════════════════
# @vacuity a workflow with no slot yet due must NOT read as UNSEEN
#   file: runs_report.py
#   find: if any(last_fire(c, now - datetime.timedelta(minutes=GRACE_MIN),
#   with: if True or any(last_fire(c, now - datetime.timedelta(minutes=GRACE_MIN),
#
# @vacuity a slot that came due with no run must STILL read as UNSEEN
#   file: runs_report.py
#   find: floor) is not None for c in parsed):
#   with: floor) is None for c in parsed):
#
# @vacuity an unknown registration time REPORTS, it never suppresses
#   file: runs_report.py
#   find: names.append(w)          # ⛔ ignorance never buys silence
#   with: continue                 # ⛔ ignorance never buys silence
#
# @vacuity the floor is applied to EVERY declared workflow, not the first
#   file: runs_report.py
#   find: for w, f in sorted(scheduled_workflows(root).items()):
#   with: for w, f in list(sorted(scheduled_workflows(root).items()))[:1]:
# ══════════════════════════════════════════════════════════════════════

section("20. 🔴🔴 THE UNSEEN CHECK HAD NO EVIDENCE FLOOR")
# ⛔ A workflow declared on disk with no runs in the window read as UNSEEN
#    whether or not it had ever HAD a slot to miss — and then filed "a
#    workflow is failing" with nothing failing. FOUR occurrences; six
#    workflows were exposed at once on 2026-09-17.
# ✅ The fix already existed one function above: `missed_fires()` has
#    carried `stamp_floor` per workflow since rule 273.
_ROOT20 = os.path.dirname(os.path.abspath(__file__))
_UTC = datetime.timezone.utc
_DECL20 = R.scheduled_workflows(_ROOT20)
ck(len(_DECL20) >= 5,
   "⚠️ the REAL declared set is what these run against (%d workflow(s))"
   % len(_DECL20),
   "⛔ a fixture of one proves nothing about a check that sweeps a "
   "directory. Got %s" % sorted(_DECL20))

# 🔴 GitHub's own timestamp format, measured 2026-09-17 on all 11
#    workflows: an ISO OFFSET, not a `Z`. A `strptime(..., "...Z")` would
#    have thrown on every one.
ck(R._dt("2026-09-16T15:12:50-04:00") is not None,
   "🔴 the registry's real `created_at` format parses (offset, not Z)",
   "⛔ `2026-09-16T15:12:50-04:00` is what the API actually returns. If "
   "this is red the registry is empty, which reports everything — noisy, "
   "but never a false all-clear")
ck(R._dt("2026-09-16T15:12:50-04:00").utcoffset().total_seconds() == -14400,
   "   ...and the offset is honoured, not dropped",
   "a timestamp read as UTC when it is -04:00 is four hours of floor "
   "this check does not have")

section("20a. ✅ NOT YET DUE IS NOT UNSEEN — AND THE CLOCK IS THE ONLY DIFFERENCE")
# `owed-tests` declares `38 11 * * *`. Registered at 08:00Z, a 09:00Z
# reading has had no slot; a 12:30Z reading has had exactly one.
_WF, _FILE = "owed-tests", "owed_tests.yml"
ck(_DECL20.get(_WF) == _FILE, "⚠️ the fixture names a REAL declared workflow",
   "⛔ if this workflow ever leaves the repo this section is testing a "
   "ghost. Got %s" % _DECL20.get(_WF))
_BORN = datetime.datetime(2026, 9, 17, 8, 0, tzinfo=_UTC)
_REG = {_FILE: _BORN}
_EARLY = datetime.datetime(2026, 9, 17, 9, 0, tzinfo=_UTC)
_LATE = datetime.datetime(2026, 9, 17, 12, 30, tzinfo=_UTC)
_n_early, _f_early = R.unseen_workflows({}, _EARLY, _ROOT20, _REG)
_n_late, _f_late = R.unseen_workflows({}, _LATE, _ROOT20, _REG)
ck(_WF not in _n_early,
   "🔴🔴 REGISTERED 1h AGO, FIRST SLOT NOT YET DUE -> NOT UNSEEN",
   "⛔ THIS IS THE DEFECT. Four scheduled workflows filed a spurious "
   "outage on their first day because this read as a failure. Got %s"
   % _n_early)
ck(_WF in _n_late,
   "🔴🔴 ...AND ONCE 11:38 PASSED WITH NO RUN -> UNSEEN",
   "⛔ the floor must not become a mute button. Got %s" % _n_late)
# ⚠️ `.get`, NOT `[...]`. A KeyError here KILLS THE FILE and the 13
#    checks after it never run — the "first workflow only" mutation
#    empties this map. A guard that dies reports "an unknown number never
#    ran", which is strictly less than a guard that fails.
ck(_f_early.get(_WF) == _BORN and _f_late.get(_WF) == _BORN,
   "⚠️ THE TWO READINGS DIFFER ONLY BY THE CLOCK",
   "🔴 same declared set, same registry, same floor — only `now` moved. "
   "If anything else differs, these two are not a pair and the first "
   "could be passing for the wrong reason")

section("20b. ⛔ NO WEAKENING: AN OLD WORKFLOW THAT NEVER RAN IS STILL UNSEEN")
# 🔴 THE `ncaaf` 19:0x CLASS (rule 251) — a cron that declares a run and
#    never lands. If the floor could silence that, the fix would have
#    removed the only reason this check exists.
for _days, _label in ((3, "3 days"), (400, "400 days")):
    _old = {_FILE: _LATE - datetime.timedelta(days=_days)}
    _n_old, _ = R.unseen_workflows({}, _LATE, _ROOT20, _old)
    ck(_WF in _n_old,
       "🔴 registered %s ago and never ran -> UNSEEN" % _label,
       "⛔ eligibility older than the window must NOT buy silence — the "
       "floor is bounded to the window for exactly this. Got %s" % _n_old)

section("20c. ⚠️ AN UNKNOWN FLOOR REPORTS, AND SAYS SO")
# ⛔ Suppressing on ignorance is the dangerous direction: a false alarm
#    wastes attention, a false all-clear hides an outage.
_n_unk, _f_unk = R.unseen_workflows({}, _LATE, _ROOT20, {})
ck(_WF in _n_unk,
   "🔴 registration unavailable -> STILL UNSEEN",
   "⛔ 'I could not establish the floor' is not 'it is fine'. Got %s"
   % _n_unk)
ck(_f_unk.get(_WF) is None, "   ...and the floor is recorded as unknown")
_body = R.render([], [], [], False, [_WF], floors=_f_unk)
ck("could NOT be" in _body and "rather than suppressed" in _body,
   "🔴 ...and the BODY says the floor could not be established",
   "⛔ a reader who cannot tell 'a slot was missed' from 'I could not "
   "check' will treat both the same way, which is how the channel dies")
_body_known = R.render([], [], [], False, [_WF], floors={_WF: _BORN})
ck("could NOT be" not in _body_known,
   "   ✅ ...and says nothing of the sort when the floor IS known",
   "⛔ a caveat that never clears is decoration. Got: %s"
   % _body_known[:160])

section("20d. ⛔ DRIVEN ACROSS THE WHOLE DECLARED SET, NOT ONE FIXTURE")
# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 EACH WORKFLOW IS JUDGED AT A MOMENT ITS OWN SLOT CAME DUE.
# ══════════════════════════════════════════════════════════════════════
# `[rewritten 2026-09-22, when t60r.yml landed]` This section used to
#    drive every workflow at ONE moment — `_LATE`, a THURSDAY 12:30Z — and
#    assert all of them unseen. That silently assumed every cron fires at
#    least once a day. `t60r` fires TUESDAYS ONLY (`17 9 * * 2`), so no
#    slot of it is due in the 24h before a Thursday noon, and the watcher
#    — CORRECTLY — did not list it: "not yet due is not unseen" is 20a's
#    whole point. The test went red on correct code (CLAUDE.md: the other
#    failure, not a safe one).
# ⛔ NOT WEAKENED. The old form proved "unseen" for the workflows that
#    happened to be due on a Thursday. This proves it for EVERY declared
#    workflow at its own due moment — weekly, hourly, weekend-only alike —
#    plus the two negatives at that same moment, plus a coverage check
#    that counts cron FILES without going through the watcher's reader.
_ANCHOR = datetime.datetime(2026, 9, 14, 0, 0, tzinfo=_UTC)    # a Monday


def _first_slot(name):
    """The first minute at/after _ANCHOR that any of `name`'s crons fire.

    ⚠️ The cron arithmetic is `R.cron_matches`, which the hand-pinned
    grammar checks above cover (`*/3`, lists, Sunday as 0 AND 7). A week
    is scanned because a weekly cron is the sparsest this repo schedules.
    """
    parsed = [c for c in (R.parse_cron(e) for e in
                          (R.declared_crons(_ROOT20).get(name) or {})
                          .get("crons", [])) if c]
    t = _ANCHOR
    for _ in range(8 * 24 * 60):
        if any(R.cron_matches(c, t) for c in parsed):
            return t
        t += datetime.timedelta(minutes=1)
    return None


_DUE = {}
for _w in sorted(_DECL20):
    _slot = _first_slot(_w)
    if _slot is not None:
        # One minute past the grace: the first moment a miss is a miss.
        _DUE[_w] = _slot + datetime.timedelta(minutes=R.GRACE_MIN + 1)
ck(sorted(_DUE) == sorted(_DECL20),
   "🔴 every declared workflow has a slot inside one week of the anchor",
   "⛔ a workflow with no findable slot cannot be driven below, and "
   "would be excused by omission. Missing: %s"
   % sorted(set(_DECL20) - set(_DUE)))

_bad_old, _bad_new, _bad_seen = [], [], []
for _w, _now in sorted(_DUE.items()):
    _old = {f: _now - datetime.timedelta(days=8) for f in _DECL20.values()}
    _new = {f: _now - datetime.timedelta(minutes=1) for f in _DECL20.values()}
    if _w not in R.unseen_workflows({}, _now, _ROOT20, _old)[0]:
        _bad_old.append(_w)
    if _w in R.unseen_workflows({}, _now, _ROOT20, _new)[0]:
        _bad_new.append(_w)
    if _w in R.unseen_workflows({_w}, _now, _ROOT20, _old)[0]:
        _bad_seen.append(_w)
ck(not _bad_old and len(_DUE) == len(_DECL20),
   "🔴 ...and EACH one, registered 8 days ago with no runs, is UNSEEN "
   "once its own slot is due (%d of %d)" % (len(_DUE) - len(_bad_old),
                                            len(_DECL20)),
   "⛔ the floor must bite for every workflow, not only the daily ones. "
   "Not reported: %s" % _bad_old)
ck(not _bad_new,
   "🔴 EVERY workflow registered one minute before that moment -> NOT unseen",
   "⛔ six were exposed at once on 2026-09-17 (budget, calibration, "
   "cfbd, runs, vacuity, owed_tests). Wrongly reported: %s" % _bad_new)
ck(not _bad_seen,
   "   ⚠️ a workflow WITH runs is never listed, floor or no floor",
   "Wrongly reported: %s" % _bad_seen)

# ✅ AND THE WEEKLY CASE PINNED IN BOTH DIRECTIONS, on the real t60r cron:
#    a Thursday is NOT evidence, the Tuesday after the fire IS.
if "t60r" in _DECL20:
    _reg_t = {_DECL20["t60r"]: _ANCHOR}
    _thu = datetime.datetime(2026, 9, 24, 12, 30, tzinfo=_UTC)
    _tue = datetime.datetime(2026, 9, 22, 10, 41, tzinfo=_UTC)
    ck("t60r" not in R.unseen_workflows({}, _thu, _ROOT20, _reg_t)[0],
       "✅ a TUESDAY-only workflow is not unseen on a Thursday",
       "⛔ no slot came due in the window — absence there is not evidence")
    ck("t60r" in R.unseen_workflows({}, _tue, _ROOT20, _reg_t)[0],
       "🔴 ...and IS unseen at the first watcher run after a missed Tuesday",
       "⛔ runs.yml fires hourly at :41; 10:41 is the first run past the "
       "09:17 slot plus its 45-minute grace")

# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 COVERAGE: NO SCHEDULED WORKFLOW CAN BE LEFT OUT OF THE WATCHER.
# ══════════════════════════════════════════════════════════════════════
# ⛔ Counted from the FILES, with a regex that is not the watcher's own,
#    and compared by FILE. `scheduled_workflows()` keys by the `name:`
#    field, so two workflows sharing a name would collapse into one entry
#    and the second would never be watched — silently. This is the check
#    that notices.
def _cron_files(root):
    return sorted(os.path.basename(p) for p in
                  glob.glob(os.path.join(root, ".github", "workflows", "*.yml"))
                  if re.search(r"(?m)^\s*-\s*cron:",
                               open(p, encoding="utf-8").read()))


def _left_out(root):
    return sorted(set(_cron_files(root)) - set(R.scheduled_workflows(root).values()))


ck(not _left_out(_ROOT20) and len(_cron_files(_ROOT20)) == len(_DECL20),
   "🔴🔴 every workflow file with a cron is one the watcher watches "
   "(%d file(s), %d watched)" % (len(_cron_files(_ROOT20)), len(_DECL20)),
   "⛔ left out: %s" % _left_out(_ROOT20))
_col = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(_col, ".github", "workflows"))
    for _f in ("a.yml", "b.yml"):
        with open(os.path.join(_col, ".github", "workflows", _f), "w",
                  encoding="utf-8") as _h:
            _h.write('name: same\non:\n  schedule:\n    - cron: "1 1 * * *"\n')
    # ⚠️ Which of the two is dropped is dict-overwrite order (the LAST
    #    file wins the name, so a.yml vanishes) — an accident, not a
    #    rule, so the check asserts that exactly ONE goes unwatched.
    ck(len(_left_out(_col)) == 1 and set(_left_out(_col)) <= {"a.yml", "b.yml"},
       "⛔ ...and that check FAILS when two workflows share a name",
       "🔴 proven on a scratch tree: a guard that cannot fail is not a "
       "guard. Got %s" % _left_out(_col))
finally:
    shutil.rmtree(_col, ignore_errors=True)

section("20e. ⚠️ analyse() KEEPS ITS 5-TUPLE, AND ITS DEFAULT FAILS SAFE")
# 🔴 Rule 269: the arity does not move. `registered` is a KEYWORD with a
#    default, so no positional caller changes.
_res = R.analyse([], _LATE, _ROOT20)
eq_len = len(_res)
ck(eq_len == 5, "⛔ analyse still returns exactly 5 values",
   "rule 269 — a signature change has no safe upload order. Got %d"
   % eq_len)
ck(sorted(_res[4]) == sorted(_DECL20),
   "🔴 ...and with NO registry supplied it reports everything",
   "⛔ THE DEFAULT MUST BE THE NOISY ONE. A caller that forgets the "
   "registry must get the old behaviour, never a quieter one. Got %s"
   % _res[4])
_res2 = R.analyse([], _EARLY, _ROOT20, _REG)
ck(_WF not in _res2[4],
   "   ✅ ...and applies the floor when it is supplied",
   "Got %s" % _res2[4])
note("⚠️ WHAT IS NOT COVERED: `gh_workflows()` itself is not driven here — "
     "it shells out to `gh api`, which needs a token and a repository this "
     "test has neither of. Its FORMAT assumption is pinned above against "
     "the real string GitHub returned, and its failure path is pinned by "
     "20c: an empty registry reports everything. ➡️ The first live run is "
     "what proves the fetch, and #33 closing is what will show it.")
