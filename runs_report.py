#!/usr/bin/env python3
"""
DID ANY WORKFLOW RUN FAIL? NOTHING IN THIS REPO HAS EVER ASKED.

🔴🔴 `[Sam, 2026-09-14: "ive seen a few failed runs in github today, it
didnt do anyhting about those failed runs"]` — **and he is right, because
nothing could have.**

⛔ MEASURED BEFORE BUILDING THIS: every input `watchdog.py` reads is a
FILE IN THE REPO — the cards, `card-verify-failure.txt`, `freshness.json`,
`health.json`, `index.html`. **A red tick on the Actions tab is not a file
in the repo, so it is invisible to every guard this project has.**

➡️ THE THREE QUESTIONS, AND ONLY NOW ARE THERE THREE:

    watchdog.py     is the PRODUCT right?        (reads repo files)
    collect.yml     did the TEST STEP fail?      (drop 52, one workflow)
    this file       did any RUN fail at all?     (reads the Actions API)

⚠️ DROP 52 WAS NOT ENOUGH AND THIS IS WHY. Its alert lives *inside*
`collect.yml` and fires only from the test step. It cannot see a run that
failed **before** reaching that step, a run of `browser.yml`,
`self-repair.yml` or `claude.yml`, or a `collect` run that died on a
converge pass. `[4 workflows deployed; 1 partially covered]`

══════════════════════════════════════════════════════════════════════
⛔ THE GATE IS "IS IT BROKEN NOW", NOT "HAS IT EVER FAILED".

A single failed run that the next run recovers from is **weather** — the
collector talks to four external APIs and one of them hiccups. Alarming
on that is rule 238, and a filtered alert is no alert.

✅ So a workflow is reported when its **most recent completed run FAILED**
— that is "broken right now", it needs no threshold, and **it clears
itself the moment a green run lands.**

⚠️ AND SEPARATELY, FLAPPING IS REPORTED WITHOUT ALARMING: a workflow whose
latest run is green but which failed 3+ times in the window is listed as a
note. **That is the shape that hid for 2h25m on 09-14** — every run red,
then green the moment the fix landed, with nobody told.
"""
import collections
import datetime
import glob
import json
import os
import re
import subprocess
import sys

# ⛔ NOT A THRESHOLD FOR THE ALARM — the alarm is "latest run failed".
#    This is only how many failures make a RECOVERED workflow worth a note.
FLAP_MIN = 3
WINDOW_H = 24

# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 EXIT CODES ARE THE WHOLE INTERFACE, AND THERE ARE FOUR.
# `[added 2026-09-15 after issue #6 sat OPEN titled "a workflow is
#  failing" with NOTHING failing — its entire content was the truncation
#  warning.]`
# ⛔ A MISCATEGORISED ALARM IS THE SAME DISEASE AS A FALSE ONE. Sam reads
#    the TITLE from his phone; a coverage problem filed as an outage
#    teaches him the title is noise, and the next real outage is the one
#    he scrolls past (rule 238).
# ✅ So "I cannot see a full day" gets its own code and its own issue.
# ⚠️ AND A RED WORKFLOW STILL OUTRANKS IT: a short list that also shows a
#    failure is still, first and foremost, a failure.
# ══════════════════════════════════════════════════════════════════════
EXIT_OK = 0
EXIT_BROKEN = 1
EXIT_UNREADABLE = 2
EXIT_COVERAGE = 3

# ══════════════════════════════════════════════════════════════════════
# 💰 HOW THE LIST IS COLLECTED. COVER THE WINDOW, DO NOT GUESS A COUNT.
# 🔴 THIS FILE'S OWN HEADER ALREADY SAID SO AND IT WAS STILL A GUESS.
#    `[measured 2026-09-15]` ~**351 runs/day** against `--limit 300`, of
#    which **254 are `pages build and deployment`** — one per commit to
#    `main`, and the collector commits constantly. The limit was raised
#    from 100 to 300 nine hours earlier and had ALREADY expired.
# ⛔ A FIXED LIMIT IS A GUESS WITH AN EXPIRY DATE. Any number chosen
#    today is wrong the next time the commit rate moves, and the failure
#    is silent: the list just stops reaching back a full day.
# ✅ So page until the DATA says the window is covered. The stopping rule
#    reads the timestamps, not a count.
# ⚠️ CAPPED, because an unbounded loop against a paginated API is its own
#    outage. 10 pages x 100 = 1,000 runs, ~3x the measured daily volume —
#    generous on purpose (a guard that fires on correct code is the other
#    failure). If the cap is ever reached the coverage finding fires,
#    which is the honest answer rather than a quiet under-count.
# ══════════════════════════════════════════════════════════════════════
REST_PER_PAGE = 100
MAX_PAGES = 10
# ⚠️ ONE HOUR OF MARGIN. Reaching EXACTLY to the cutoff proves nothing
#    about the run that sits a minute the other side of it.
COVER_MARGIN_H = 1


def _dt(s):
    try:
        return datetime.datetime.fromisoformat((s or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def scheduled_workflows(root="."):
    """Workflow NAMES that declare a cron — the ones that must show runs.

    ⛔ DECLARED, NOT REMEMBERED. Reading the workflow files means a new
    scheduled workflow is covered the day it ships (rule 246). ⚠️ A
    workflow with NO schedule — `claude.yml` is mention-triggered — is
    correctly absent from a run list and must never be flagged.
    """
    out = {}
    for p in sorted(glob.glob(os.path.join(root, ".github/workflows/*.yml"))):
        try:
            t = open(p, encoding="utf-8").read()
        except OSError:
            continue
        if not re.search(r"^\s*-?\s*cron:", t, re.M):
            continue
        m = re.search(r"^name:\s*(.+)$", t, re.M)
        out[(m.group(1).strip() if m else
             os.path.basename(p)[:-4])] = os.path.basename(p)
    return out


# 🔴🔴 HOW LATE GITHUB IS ALLOWED TO BE BEFORE A FIRE COUNTS AS MISSED.
#    `[measured 2026-09-15 on this repo: the 19:04 and 19:18 crons landed
#      at ~19:15-19:19 and ~19:27-19:30 — 11 to 15 minutes late, every
#      day for 8 days]` GitHub's own docs say a scheduled run "may be
#      delayed during periods of high load", with no bound.
# ⛔ 45 MINUTES IS CHOSEN TO NOT FIRE ON CORRECT BEHAVIOUR. `CLAUDE.md`:
#    *"a guard that fires on correct code is the other failure, not a
#    safe one."* A cron 20 minutes late is GitHub being GitHub; a cron
#    45+ minutes late with a later cron of the same workflow already
#    landed is a cron that did not run.
GRACE_MIN = 45

# ⚠️ The marker `collect.yml` and friends stamp into `run-name:`. It is
#    read back out of the run's DISPLAY name — `name` in `gh run list`,
#    the field rule 268 warns is the display one. **That is exactly why
#    it is the right field here**: display is what `run-name:` sets.
CRON_STAMP = re.compile(r"\[cron ([^\]]+)\]")


def _field(spec, lo, hi):
    """One cron field -> the set of values it matches."""
    out = set()
    for part in (spec or "").split(","):
        step = 1
        if "/" in part:
            part, s = part.split("/", 1)
            step = max(1, int(s))
        if part in ("*", ""):
            a, b = lo, hi
        elif "-" in part:
            x, y = part.split("-", 1)
            a, b = int(x), int(y)
        else:
            a = int(part)
            # ⚠️ `5/2` means "from 5, every 2" — NOT "5 only". Rule 166's
            #    shape: budget.py already shipped `*/6` counted as one
            #    fire a day and under-reported by 108 credits a week.
            b = hi if step > 1 else a
        out.update(v for v in range(a, b + 1) if (v - a) % step == 0)
    return out


def parse_cron(expr):
    """A 5-field cron expression -> a matcher dict, or None."""
    p = (expr or "").split()
    if len(p) != 5:
        return None
    try:
        return {"expr": " ".join(p),
                "min": _field(p[0], 0, 59), "hour": _field(p[1], 0, 23),
                "dom": _field(p[2], 1, 31), "mon": _field(p[3], 1, 12),
                # ⚠️ cron's day-of-week is Sun=0 AND Sun=7. Python's
                #    weekday() is Mon=0..Sun=6. Getting this backwards
                #    shifts every weekly cron by a day and the check
                #    would alarm on a workflow that ran perfectly.
                "dow": set(d % 7 for d in _field(p[4], 0, 7)),
                "dom_star": p[2] == "*", "dow_star": p[4] == "*"}
    except ValueError:
        return None


def cron_matches(c, dt):
    if (dt.minute not in c["min"] or dt.hour not in c["hour"]
            or dt.month not in c["mon"]):
        return False
    d_ok = dt.day in c["dom"]
    w_ok = ((dt.weekday() + 1) % 7) in c["dow"]
    # ⛔ POSIX: when BOTH day fields are restricted the match is OR, not
    #    AND. `0 0 1 * 1` is "the 1st **or** any Monday". Treating it as
    #    AND would make a cron look like it fired far less often than it
    #    does — a silent under-count, which is the false all-clear shape.
    if c["dom_star"] and c["dow_star"]:
        return True
    if c["dom_star"]:
        return w_ok
    if c["dow_star"]:
        return d_ok
    return d_ok or w_ok


def last_fire(c, now, floor):
    """The most recent minute at or before `now` this cron matches."""
    t = now.replace(second=0, microsecond=0)
    while t >= floor:
        if cron_matches(c, t):
            return t
        t -= datetime.timedelta(minutes=1)
    return None


def declared_crons(root="."):
    """{workflow name: {"file", "crons", "stamped"}} for cron workflows.

    ⛔ `stamped` IS THE HONEST HALF. A workflow that declares crons but
    does not write `github.event.schedule` into its `run-name:` produces
    runs that CANNOT be attributed to a cron — and "I could not tell"
    must be reported as that, never as "it fired". `[This is the exact
    hole that left the ncaaf 19:0x question open for six days: two crons
    in one hour, two runs in one hour, and no way to say which was
    which. Ledger rule 251.]`
    """
    out = {}
    for p in sorted(glob.glob(os.path.join(root, ".github/workflows/*.yml"))):
        try:
            t = open(p, encoding="utf-8").read()
        except OSError:
            continue
        crons = re.findall(r"^\s*-?\s*cron:\s*[\"']?([^\"'#\n]+?)[\"']?\s*(?:#.*)?$",
                           t, re.M)
        if not crons:
            continue
        m = re.search(r"^name:\s*(.+)$", t, re.M)
        rn = re.search(r"^run-name:.*$", t, re.M)
        out[(m.group(1).strip() if m else os.path.basename(p)[:-4])] = {
            "file": os.path.basename(p),
            "crons": [c.strip() for c in crons],
            # ⚠️ Both halves required: a `run-name:` that does not carry
            #    the schedule stamps nothing useful.
            "stamped": bool(rn) and "event.schedule" in rn.group(0)
                       and "[cron " in rn.group(0),
        }
    return out


def missed_fires(runs, now=None, root="."):
    """Crons that SHOULD have fired inside the covered window and did not.

    🔴🔴 THIS IS THE QUESTION `missing` COULD NOT ANSWER. `missing` asks
    whether a WORKFLOW produced any runs at all. A workflow with 43 crons
    produces runs all day while one of those 43 never lands — and that is
    the live, six-day-old `ncaaf` 19:0x finding.

    ⛔ IT IS BOUNDED BY WHAT THE LIST ACTUALLY COVERS. An expected fire
    older than the oldest run returned is NOT reported — the list simply
    does not reach it, and rule 270 is that a count over a window you did
    not verify is a count you invented.

    Returns (missed, unattributable).
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    decl = declared_crons(root)

    seen_at = collections.defaultdict(list)
    # 🔴🔴 WHEN DID STAMPING START FOR THIS WORKFLOW? `[added 2026-09-15,
    #    caught 26 minutes before the first hourly run would have fired it]`
    # ⛔ WITHOUT THIS THE CHECK FALSE-ALARMS ON EVERY CRON FOR A FULL DAY.
    #    Measured on the real shape one hour after the stamp shipped —
    #    23h of UNSTAMPED runs plus 1h of stamped ones — it reported
    #    **27 crons missing.** Every one of them had run perfectly; they
    #    simply ran before the run title carried a cron.
    # ⚠️ AND THAT IS THE FAILURE `CLAUDE.md` NAMES AS THE WORSE ONE: *"a
    #    guard that fires on correct code is the other failure, not a
    #    safe one."* 27 false findings in the first issue this thing ever
    #    opened is how an alert channel gets muted on day one.
    # ✅ PER WORKFLOW, NOT GLOBAL. `browser` runs twice a day, so its
    #    first stamped run can be 12 hours behind `collect`'s. A single
    #    shared floor would judge `browser` over a window it has no
    #    evidence for — the same mistake one level up.
    # ⛔ A workflow with NO stamped run yet is judged NOT AT ALL. Total
    #    silence from a workflow is already `missing`'s question (drop
    #    58); this one only speaks where it has evidence.
    stamp_floor = {}
    for r in runs or []:
        r = r or {}
        m = CRON_STAMP.search(r.get("name") or "")
        t = _dt(r.get("createdAt"))
        if m and t:
            seen_at[m.group(1).strip()].append(t)
            wf = r.get("workflowName") or r.get("name")
            if wf and (wf not in stamp_floor or t < stamp_floor[wf]):
                stamp_floor[wf] = t

    stamps = [t for t in (_dt(r.get("createdAt")) for r in (runs or [])) if t]
    # ⛔ FLOOR = THE OLDEST RUN THE LIST ACTUALLY RETURNED, never a
    #    nominal 24h. With no runs at all there is nothing to bound
    #    against and the honest answer is to report nothing here.
    floor = max(stamps and min(stamps) or now,
                now - datetime.timedelta(hours=WINDOW_H))

    missed, unattributable = [], []
    for wf, d in sorted(decl.items()):
        if not d["stamped"]:
            unattributable.append({"name": wf, "file": d["file"],
                                   "crons": len(d["crons"])})
            continue
        # ⛔ NOTHING STAMPED FROM THIS WORKFLOW YET — no evidence, so no
        #    verdict. Silent on purpose; see the comment on `stamp_floor`.
        if wf not in stamp_floor:
            continue
        wf_floor = max(floor, stamp_floor[wf])
        for expr in d["crons"]:
            c = parse_cron(expr)
            if not c:
                unattributable.append({"name": wf, "file": d["file"],
                                       "crons": 0, "bad": expr})
                continue
            due = last_fire(c, now - datetime.timedelta(minutes=GRACE_MIN),
                            wf_floor)
            if due is None:
                continue          # not expected to have fired in range
            # ⚠️ A run counts for this fire if it started at or after the
            #    scheduled minute. GitHub is late, never early.
            if not any(t >= due for t in seen_at.get(c["expr"], [])):
                missed.append({"name": wf, "file": d["file"],
                               "cron": c["expr"],
                               "due": due.strftime("%Y-%m-%d %H:%M") + "Z",
                               "late_min": int((now - due).total_seconds()
                                               // 60)})
    return missed, unattributable


def workflow_names(root="."):
    """`.github/workflows/<file>` -> the `name:` that file declares.

    ⚠️ READ FROM THE CHECKOUT, which is the same source `scheduled_workflows()`
    and `declared_crons()` already use — so the grouping key and the
    expected-workflow set cannot disagree about what a workflow is called.
    """
    out = {}
    for p in sorted(glob.glob(os.path.join(root, ".github/workflows/*.yml"))):
        try:
            t = open(p, encoding="utf-8").read()
        except OSError:
            continue
        m = re.search(r"^name:\s*(.+)$", t, re.M)
        out[".github/workflows/" + os.path.basename(p)] = (
            m.group(1).strip() if m else os.path.basename(p)[:-4])
    return out


def normalise(run, names=None):
    """One REST workflow-run object -> the shape `analyse()` reads.

    ══════════════════════════════════════════════════════════════════
    🔴🔴 THE REST FIELDS ARE NOT THE CLI FIELDS, AND `name` IS THE TRAP
    IN BOTH — differently. `[MEASURED 2026-09-15 against this repo's own
    /actions/runs, not read off the docs.]`

      scheduled run, `run-name:` set (6 of our 7 workflows):
          name          = "collect [cron 9 */3 * * *]"   <- the RUN
          display_title = "collect [cron 9 */3 * * *]"
      push run, before `run-name:` existed:
          name          = "collect"                      <- the WORKFLOW
          display_title = "Add files via upload"         <- the commit

    ⛔ SO REST `name` IS THE RUN NAME WHENEVER `run-name:` IS SET, AND
       THE WORKFLOW NAME ONLY WHEN IT IS NOT. Mapping it to
       `workflowName` would shatter every workflow into one group per
       run — each its own latest, each green-or-red alone, and the
       flapping count never reaching 3. **That is the silent false
       all-clear `analyse()`'s own comment warns about.**
    ✅ THE WORKFLOW IDENTITY COMES FROM `path`, which is the workflow
       FILE and cannot be overridden by `run-name:`. It is resolved
       through the checkout so it lands on the same string
       `scheduled_workflows()` reports (`claude.yml` declares
       `name: Claude`, so the file name alone would not match).
    ⚠️ Runs whose `path` is not a repo workflow file — `pages build and
       deployment` lives at `dynamic/pages/...` and is 254 of the 351
       runs a day — keep their own `name`. They are never in the
       expected set, so they can never read as UNSEEN.
    ✅ AND `display_title` IS THE RUN TITLE, which is the half that
       carries the `[cron ...]` stamp `missed_fires()` reads.
    ══════════════════════════════════════════════════════════════════
    """
    r = run or {}
    names = names if names is not None else {}
    wf = names.get(r.get("path") or "") or r.get("name")
    return {"workflowName": wf,
            # ⚠️ `display_title` first: it is the run title under both
            #    shapes above. `name` is the fallback for a payload that
            #    does not carry one.
            "name": r.get("display_title") or r.get("name"),
            "conclusion": r.get("conclusion"),
            "createdAt": r.get("created_at") or r.get("createdAt"),
            "url": r.get("html_url") or r.get("url")}


def collect(fetch_page, now=None, root=".", max_pages=MAX_PAGES,
            window_h=WINDOW_H):
    """Page until the window is covered. -> (runs, pages_read, covered).

    `fetch_page(n)` returns the REST `workflow_runs` list for 1-based page
    `n`. ⛔ INJECTED, so `test_runs_report.py` can drive the stopping rule
    without a network — a collection loop nothing can test is a collection
    loop that silently stops early.

    ⚠️ THREE WAYS TO STOP, AND ONLY ONE OF THEM IS A FAILURE:
      1. the oldest run seen is past the cutoff + margin  -> covered
      2. the page came back short or empty (end of history) -> covered,
         because seeing everything there is IS covering the window
      3. the page cap was reached                          -> NOT covered,
         and that becomes the coverage finding rather than a quiet
         under-count
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    floor = now - datetime.timedelta(hours=window_h + COVER_MARGIN_H)
    runs, pages, covered = [], 0, False
    names = workflow_names(root)
    for page in range(1, max_pages + 1):
        batch = fetch_page(page) or []
        pages = page
        runs.extend(normalise(r, names) for r in batch)
        if len(batch) < REST_PER_PAGE:
            covered = True       # end of history — nothing older exists
            break
        stamps = [_dt(r.get("createdAt")) for r in runs]
        stamps = [t for t in stamps if t]
        if stamps and min(stamps) <= floor:
            covered = True
            break
    return runs, pages, covered


def gh_page(page, per_page=REST_PER_PAGE):
    """One page of `/actions/runs`, via the `gh` CLI already in the runner.

    ⚠️ `gh api` RATHER THAN A RAW REQUEST: it carries `GH_TOKEN`, handles
    the host, and is already the tool this workflow depends on. ⛔ It
    raises on a non-zero exit so the caller reports "could not look"
    rather than judging a short list.
    """
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise RuntimeError("GITHUB_REPOSITORY is not set — refusing to "
                           "guess which repository to read")
    out = subprocess.run(
        ["gh", "api", "-H", "Accept: application/vnd.github+json",
         "/repos/%s/actions/runs?per_page=%d&page=%d" % (repo, per_page, page),
         "--jq", ".workflow_runs"],
        capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise RuntimeError("gh api page %d failed: %s"
                           % (page, (out.stderr or "").strip()[:400]))
    return json.loads(out.stdout or "[]")


def verdict(broken, flapping, missing, truncated, missed, unattributable):
    """The findings -> the exit code. ⛔ A red workflow outranks coverage.

    🔴 THIS IS THE FIX FOR ISSUE #6. Truncation used to return 1, which
    filed "I cannot see a full day" under "a workflow is failing" — an
    outage title on a coverage problem, with nothing failing.
    ⚠️ ORDER MATTERS AND IS EXPLICIT: any real finding wins, so a short
    list that ALSO shows a red workflow is still an outage.
    """
    if broken or flapping or missing or missed or unattributable:
        return EXIT_BROKEN
    if truncated:
        return EXIT_COVERAGE
    return EXIT_OK


def analyse(runs, now=None, root="."):
    """runs: the JSON `gh run list` emits.

    Returns (broken, flapping, seen, truncated, missing).

    ⛔ THE ARITY IS DELIBERATELY UNCHANGED. Drop 58 changed this from 3
    to 5 and the OLD test on `main` died with `ValueError: too many
    values to unpack` the moment upload A landed. Rule 269: when a
    signature changes, NO upload order is safe. The cron work is
    therefore a SEPARATE function (`missed_fires`), not a sixth return.
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(hours=WINDOW_H)

    by = collections.defaultdict(list)
    for r in runs or []:
        # 🔴🔴 `workflowName` FIRST, AND `name` IS A TRAP. `gh run list`
        #    offers BOTH — which is itself the evidence they differ — and
        #    `name` is the RUN's display name. For a push-triggered run
        #    GitHub derives that from the commit message, and both
        #    `collect.yml` and `browser.yml` have push triggers.
        # ⛔ Grouping by `name` would make every push run its own
        #    "workflow", so "the most recent completed run of X" would be
        #    a set of one, every one of them its own latest, and the
        #    flapping count would never reach 3. **A silent false
        #    all-clear — the most dangerous output this repo has.**
        # ⚠️ The CLI docs list the fields and explain neither, so this is
        #    written to survive either meaning rather than to bet on one
        #    (rule 252).
        r = r or {}
        name = r.get("workflowName") or r.get("name")
        if not name:
            continue
        by[name].append(r)

    # 🔴🔴 DID THE LIST EVEN COVER THE WINDOW? `[measured 2026-09-15:
    #    ~96 cron runs/day plus push runs, against a `--limit 100` ask]`
    # ⛔ If the OLDEST run returned is younger than the window, the list
    #    was TRUNCATED — the 24h counts below are understated and a
    #    low-frequency workflow may be missing entirely. **A count from a
    #    truncated list reported as complete is a false all-clear**, which
    #    is the most dangerous output this repo has.
    # ⚠️ Detection comes from the DATA, not from a magic limit: the list
    #    tells you whether it reached back far enough, so raising the
    #    limit later cannot silently un-fix this. ➡️ Ledger rule 270.
    stamps = [_dt(r.get("createdAt")) for r in (runs or [])]
    stamps = [t for t in stamps if t]
    truncated = bool(stamps) and min(stamps) > cutoff

    broken, flapping = [], []
    for name, rs in sorted(by.items()):
        # ⛔ ONLY COMPLETED RUNS DECIDE. An in-progress run has no
        #    conclusion, and treating a blank as a pass OR a failure would
        #    both be wrong — it simply has not answered yet.
        done = [r for r in rs if r.get("conclusion")]
        done.sort(key=lambda r: r.get("createdAt") or "", reverse=True)
        if not done:
            continue
        latest = done[0]
        recent = [r for r in done
                  if (_dt(r.get("createdAt")) or now) >= cutoff]
        fails = [r for r in recent if r.get("conclusion") == "failure"]
        if latest.get("conclusion") == "failure":
            broken.append({"name": name, "url": latest.get("url"),
                           "at": latest.get("createdAt"),
                           "fails_24h": len(fails)})
        elif len(fails) >= FLAP_MIN:
            flapping.append({"name": name, "fails_24h": len(fails),
                             "url": (fails[0] or {}).get("url")})
    # ⛔ A SCHEDULED WORKFLOW WITH NO RUNS AT ALL IS NOT "HEALTHY", IT IS
    #    UNSEEN — and that is the `ncaaf` 19:0x class (rule 251): a cron
    #    that declares a run and never lands, invisible because nothing
    #    compared the declaration to the reality.
    missing = [w for w in sorted(scheduled_workflows(root)) if w not in by]
    return broken, flapping, sorted(by), truncated, missing


def render(broken, flapping, seen, truncated=False, missing=(),
           missed=(), unattributable=()):
    out = []
    # 🔴 FIRST, BECAUSE IT IS THE FINDING NOTHING IN THIS REPO COULD MAKE
    #    UNTIL NOW. A workflow can be green all day with one of its crons
    #    silently never landing.
    if missed:
        out.append("**These crons were DUE and no run carries their "
                   "stamp — they did not fire:**\n")
        for m in missed:
            out.append("- `%s` in `%s` — due %s, %d minute(s) ago, no run"
                       % (m["cron"], m["file"], m["due"], m["late_min"]))
        out.append("")
    if unattributable:
        out.append("**These cron workflows cannot be attributed — their "
                   "`run-name:` does not stamp `github.event.schedule`, "
                   "so a cron that never fires is invisible:**\n")
        for u in unattributable:
            out.append("- `%s` (`%s`)%s" % (u["name"], u["file"],
                       (" — unparseable cron `%s`" % u["bad"])
                       if u.get("bad") else ""))
        out.append("")
    if missing:
        out.append("**These workflows declare a schedule and produced NO "
                   "runs in the window — they are UNSEEN, not healthy:**\n")
        for m in missing:
            out.append("- `%s` — declares a cron, no run found" % m)
        out.append("")
    if broken:
        out.append("**These workflows are failing right now — their most "
                   "recent completed run was red.**\n")
        for b in broken:
            out.append("- **`%s`** — last run failed at %s (%d failure(s) "
                       "in %dh)\n  %s"
                       % (b["name"], (b["at"] or "?")[:16].replace("T", " "),
                          b["fails_24h"], WINDOW_H, b["url"] or ""))
        out.append("")
    if flapping:
        out.append("**Recovered, but failing repeatedly — worth a look:**\n")
        for f in flapping:
            out.append("- `%s` — %d failure(s) in %dh, latest run green\n  %s"
                       % (f["name"], f["fails_24h"], WINDOW_H, f["url"] or ""))
        out.append("")
    out.append("⛔ A red run does not stop the data — the collector still "
               "commits and the page keeps updating. What it stops is the "
               "guarantee that the numbers were checked before they "
               "shipped.")
    out.append("")
    out.append("⛔ Do not fix this by weakening a check. Read `CLAUDE.md`. "
               "A check may only change when it asks the WRONG QUESTION, "
               "and the replacement must be harder to pass.")
    out.append("")
    if truncated:
        # ⛔ ~~"Raise the `--limit` in `runs.yml`."~~ STRUCK 2026-09-15.
        #    There is no limit to raise any more — the list is PAGED until
        #    the window is covered, so reaching here means the page cap was
        #    hit and the advice is a different one.
        out.append("⚠️ **The run list did not reach back a full %dh** — "
                   "pagination hit its %d-page cap (%d runs), so the %dh "
                   "counts above are UNDERSTATED and a low-frequency "
                   "workflow may be absent entirely."
                   % (WINDOW_H, MAX_PAGES, MAX_PAGES * REST_PER_PAGE,
                      WINDOW_H))
        out.append("")
    out.append("_Workflows seen: %s. This issue is updated in place and "
               "closes itself when every workflow's latest run is green._"
               % ", ".join("`%s`" % s for s in seen))
    return "\n".join(out)


def render_coverage(seen, pages=None, runs=None):
    """The body for a COVERAGE-ONLY finding. ⛔ Not an outage report.

    🔴 ISSUE #6 WAS THIS TEXT UNDER AN OUTAGE TITLE. Nothing was failing;
    the whole content was the truncation warning. So this body says what
    is actually wrong, what it does NOT mean, and what to do — and it
    never claims a workflow is broken.
    """
    out = []
    out.append("**The run watcher could not see a full %dh of runs, so it "
               "cannot answer its own question.**\n" % WINDOW_H)
    out.append("- Paged back %s and still did not reach %dh + %dh of "
               "margin%s."
               % (("%d page(s)" % pages) if pages else "as far as it could",
                  WINDOW_H, COVER_MARGIN_H,
                  (" (%d runs)" % len(runs)) if runs is not None else ""))
    out.append("- The %dh failure counts are **UNDERSTATED**, and a "
               "low-frequency workflow may be absent from the list "
               "entirely." % WINDOW_H)
    out.append("")
    out.append("⛔ **THIS IS NOT AN OUTAGE.** No workflow is reported "
               "failing, no cron is reported missed. This says only that "
               "the watcher's own view is short — which is a different "
               "finding, and it is why it no longer files itself under "
               "*a workflow is failing*.")
    out.append("")
    out.append("⚠️ **An absence in an API response is evidence about the "
               "API, never about the world** — `CLAUDE.md`. Read nothing "
               "into what is missing from a list this short.")
    out.append("")
    # ⛔ NO FLAG IS NAMED HERE ON PURPOSE. The old body said "raise the
    #    `--limit` in runs.yml" and there is no longer a limit to raise —
    #    stale advice in an alert body is how a reader learns to skip the
    #    body.
    out.append("➡️ The list is PAGED until the window is covered, so "
               "reaching here means the run rate grew past `MAX_PAGES` "
               "(%d) x `REST_PER_PAGE` (%d) = %d runs a day. Raise "
               "`MAX_PAGES` in `runs_report.py`, or cut the volume — "
               "`[measured 2026-09-15]` **254 of 351 runs a day were "
               "`pages build and deployment`**, one per commit to `main`."
               % (MAX_PAGES, REST_PER_PAGE, MAX_PAGES * REST_PER_PAGE))
    out.append("")
    out.append("⛔ Do not fix this by weakening a check. Read `CLAUDE.md`. "
               "A check may only change when it asks the WRONG QUESTION, "
               "and the replacement must be harder to pass.")
    out.append("")
    out.append("_Workflows seen: %s. This issue is updated in place and "
               "closes itself when the watcher can see a full day again._"
               % ", ".join("`%s`" % x for x in seen))
    return "\n".join(out)


def main(argv=None):
    """stdin -> a verdict, or `--collect` -> the run list on stdout.

    ⚠️ TWO MODES, ONE FILE, because the collection and the judgement are
    both things a test has to be able to drive. ⛔ Neither belongs in the
    shell step (rule 66): a shell loop deciding when the window is
    covered is a second copy of that judgement, and the copy no test
    reaches.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--collect" in argv:
        # ⛔ EXIT 2, NOT 1, on a collection failure — "I could not look"
        #    must never reach the judgement path as a short list.
        try:
            runs, pages, covered = collect(gh_page)
        except Exception as e:          # noqa: BLE001 - reported, not hidden
            sys.stderr.write("could not collect the run list: %s: %s\n"
                             % (type(e).__name__, e))
            return EXIT_UNREADABLE
        sys.stderr.write("collected %d run(s) over %d page(s); window "
                         "covered=%s\n" % (len(runs), pages, covered))
        json.dump(runs, sys.stdout)
        return EXIT_OK
    try:
        runs = json.load(sys.stdin)
    except (ValueError, OSError) as e:
        # ⛔ A PARSE FAILURE IS NOT "EVERYTHING IS FINE". Exit 2 so the
        #    workflow can tell "nothing is broken" from "I could not look".
        sys.stderr.write("could not read run list: %s\n" % e)
        return 2
    broken, flapping, seen, truncated, missing = analyse(runs)
    missed, unattributable = missed_fires(runs)
    rc = verdict(broken, flapping, missing, truncated, missed, unattributable)
    if rc == EXIT_OK:
        print("OK")
        return EXIT_OK
    # 🔴 THE COVERAGE-ONLY CASE GETS ITS OWN BODY AND ITS OWN CODE, so
    #    `runs.yml` can file it under its own title. Issue #6 is what
    #    happens without this.
    if rc == EXIT_COVERAGE:
        print(render_coverage(sorted(set(
            (r or {}).get("workflowName") or (r or {}).get("name") or ""
            for r in (runs or [])) - {""}), runs=runs))
        return EXIT_COVERAGE
    print(render(broken, flapping, seen, truncated, missing,
                 missed, unattributable))
    return EXIT_BROKEN


if __name__ == "__main__":
    sys.exit(main())
