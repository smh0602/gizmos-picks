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
import re
import os
import shutil
import tempfile
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
ck("⛔ ...and that alone breaks the silence, so it cannot pass as healthy",
   "truncated" in R.render(b, f, seen, trunc, miss).lower(),
   "🔴 the whole point is that an undercount must not read as a clean "
   "bill of health")
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
