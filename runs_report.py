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


def analyse(runs, now=None, root="."):
    """runs: the JSON `gh run list` emits.

    Returns (broken, flapping, seen, truncated, missing).
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


def render(broken, flapping, seen, truncated=False, missing=()):
    out = []
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
    if not broken and not flapping and not missing and not truncated:
        print("OK")
        return 0
    print(render(broken, flapping, seen, truncated, missing))
    return 1


if __name__ == "__main__":
    sys.exit(main())
