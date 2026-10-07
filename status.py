#!/usr/bin/env python3
"""THE WEEKLY STATUS EMAIL. `[Sam, 2026-10-07]` Every Monday status.yml posts this
to ONE issue assigned to Sam, built only from the repo's own files. Free. "Needs
you: ..." (a BROKEN finding, a health check too old to read) ends with
`watchdog.what_to_do`. ⛔ A report, never a task (`self_repair.COUNTER`).
Usage: python status.py <body file>"""
import datetime
import json
import os
import sys

import freshness as F
import runs_report as R
import self_repair
import watchdog as W
import winners as WN

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUES = (("MLB", "data"), ("NFL", "data/nfl"), ("College", "data/ncaaf"))
# ⚠️ MEASURED 2026-10-07: 528 health reports on main 09-23 -> 10-07, the longest
#    gap 5.85 hours. Older than this, "right now" is not supported.
HEALTH_MAX_H = 12


def _read(p):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _rate(w, n):
    return "%d-%d (%d%%)" % (w, n - w, round(100.0 * w / n)) if n else "nothing graded"


def _week(rows, since):
    rows = [r for r in rows or [] if str(r.get("date") or "") >= since]
    return sum(r.get("w") or 0 for r in rows), sum(r.get("n") or 0 for r in rows)


def _won(rows):
    return sum(1 for r in rows if r.get("won")), len(rows)


def records(root, d, since):
    """[(kind, (w, n) in the last 7 days, (w, n) overall)] for one league."""
    latest = os.path.join(root, d, "latest")
    rec = _read(os.path.join(latest, "record.json"))
    o = rec.get("overall") or {}
    out = [("Props", _week(rec.get("by_day"), since), (o.get("w") or 0, o.get("n") or 0))]
    if d == "data":                      # MLB: record.json's own game-line line
        g = rec.get("game_lines") or {}
        out.append(("Game-line picks", _week(g.get("by_day"), since), (g.get("w") or 0, g.get("n") or 0)))
    else:                                # football: the game model's graded picks (fb_ledger)
        led = [p for p in _read(os.path.join(latest, "model-ledger.json")).get("picks") or []
               if p.get("model") == "game_model" and p.get("state") == "graded"]
        out.append(("Game-line picks", _won([p for p in led if str(p.get("commence"))[:10] >= since]),
                    _won(led)))
    gr = [g for g in WN.stored_grades(os.path.join(root, d)).values() if g.get("state") == "graded"]
    out.append(("Pick to win", _won([g for g in gr if str(g.get("graded_at"))[:10] >= since]), _won(gr)))
    return out


def build(root=ROOT, now=None):
    """-> (body, needs): the weekly issue's text and what needs Sam (empty: nothing)."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    since = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    health = _read(os.path.join(root, "data", "latest", "health.json"))
    seen = W._when(health.get("checked_at"))
    old = (None if seen and now - seen <= datetime.timedelta(hours=HEALTH_MAX_H) else
           "the health check has not run for %d hours" % ((now - seen).total_seconds() // 3600)
           if seen else "the health check has never run")
    findings = [] if old else health.get("findings") or []
    runs, stale = R.run_list(os.path.join(root, "data", "latest", "runs.json"), now)
    wf = (runs or {}).get("by_workflow") or {}
    broken = ([{"key": "watchdog:health", "severity": "BROKEN", "what": old}] if old else []) + [
        f for f in findings if f.get("severity") == "BROKEN"]
    needs = [f["what"] for f in broken]
    L = ["Needs you: %s." % "; ".join(needs) if needs else "Nothing needs you this week.",
         "", "## Records (last 7 days / overall)"]
    for name, d in LEAGUES:
        L.append("**%s**" % name)
        L += ["- %s: %s / %s" % (k, _rate(*wk), _rate(*al)) for k, wk, al in records(root, d, since)]
    c = health.get("credits") or {}
    bal, at = c.get("balance"), str(c.get("pulled_at"))
    L += ["", "## Odds API credits"]
    if not isinstance(bal, int):
        L.append("- No credit reading on file.")
    elif at[:7] == now.strftime("%Y-%m"):
        import collect
        L.append("- {:,} used this month, {:,} left (read {}).".format(collect.MONTHLY_PLAN - bal, bal, at))
    else:
        L.append("- No reading yet this month; the last one ({}) left {:,}.".format(at, bal))
    late = {}
    for name, d in LEAGUES:
        f = _read(os.path.join(root, d, "latest", F.LATENESS_FILE))
        for r in (f.get("late") or []) + list((f.get("artifacts") or {}).values()):
            if (r.get("late_min") or 0) > F.GRACE_MIN and str(r.get("due_at")) >= since:
                late[(name, r.get("path"), r.get("due_at"))] = (r["late_min"], name, r)
    L += ["", "## Late builds (last 7 days)"]
    if late:
        m, name, r = max(late.values(), key=lambda x: x[0])
        L.append("- %d built more than %d minutes after they were due. The worst: %s %s, %d minutes "
                 "late (due %s)." % (len(late), F.GRACE_MIN, name, r.get("mode"), round(m), r.get("due_at")))
    else:
        L.append("- None.")
    bad = sorted(((v or {}).get("failed") or 0, n) for n, v in wf.items() if (v or {}).get("failed"))
    L += ["", "## Failed runs", "- Can't say: %s." % stale if stale else
          "- %d in the last %s hours: %s." % (sum(x for x, _n in bad), runs.get("window_hours"), ", ".join(
              "%s %d" % (n, x) for x, n in sorted(bad, reverse=True))) if bad else
          "- None in the last %s hours." % runs.get("window_hours"), "", "## Right now"]
    L += (["- Can't say: %s." % old] if old else
          ["- %s: %s" % (f.get("severity"), f.get("what")) for f in findings]
          or ["- Nothing is broken or degraded."])
    L += ["", self_repair.COUNTER]
    if broken:
        L.append(W.what_to_do(broken, "No: %s, so no collect run has finished since." % old
                              if old else W.site_updating(findings)))
    return "\n".join(L) + "\n", needs


if __name__ == "__main__":
    with open(sys.argv[1], "w", encoding="utf-8") as fh:
        fh.write(build()[0])
