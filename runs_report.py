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
import sys

# ⛔ NOT A THRESHOLD FOR THE ALARM — the alarm is "latest run failed".
#    This is only how many failures make a RECOVERED workflow worth a note.
FLAP_MIN = 3
WINDOW_H = 24


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
    wf_of_run = {}
    for r in runs or []:
        r = r or {}
        m = CRON_STAMP.search(r.get("name") or "")
        t = _dt(r.get("createdAt"))
        if m and t:
            seen_at[m.group(1).strip()].append(t)
            wf_of_run.setdefault(m.group(1).strip(),
                                 r.get("workflowName") or r.get("name"))

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
        for expr in d["crons"]:
            c = parse_cron(expr)
            if not c:
                unattributable.append({"name": wf, "file": d["file"],
                                       "crons": 0, "bad": expr})
                continue
            due = last_fire(c, now - datetime.timedelta(minutes=GRACE_MIN),
                            floor)
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
        out.append("⚠️ **The run list did not reach back a full %dh** — it "
                   "was truncated by volume, so the 24h counts above are "
                   "UNDERSTATED and a low-frequency workflow may be absent "
                   "entirely. Raise the `--limit` in `runs.yml`." % WINDOW_H)
        out.append("")
    out.append("_Workflows seen: %s. This issue is updated in place and "
               "closes itself when every workflow's latest run is green._"
               % ", ".join("`%s`" % s for s in seen))
    return "\n".join(out)


def main():
    try:
        runs = json.load(sys.stdin)
    except (ValueError, OSError) as e:
        # ⛔ A PARSE FAILURE IS NOT "EVERYTHING IS FINE". Exit 2 so the
        #    workflow can tell "nothing is broken" from "I could not look".
        sys.stderr.write("could not read run list: %s\n" % e)
        return 2
    broken, flapping, seen, truncated, missing = analyse(runs)
    missed, unattributable = missed_fires(runs)
    if not (broken or flapping or missing or truncated
            or missed or unattributable):
        print("OK")
        return 0
    print(render(broken, flapping, seen, truncated, missing,
                 missed, unattributable))
    return 1


if __name__ == "__main__":
    sys.exit(main())
