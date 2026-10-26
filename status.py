#!/usr/bin/env python3
"""THE WEEKLY STATUS EMAIL. `[Sam, 2026-10-07]` status.yml runs daily and posts
`today()` to ONE issue assigned to Sam: Mondays the week, other days only a
health check too old to read. Built only from the repo's own files. Free. "Needs
you: ..." (a BROKEN finding, a health check too old to read) ends with
`watchdog.what_to_do`. ⛔ A report, never a task (`self_repair.COUNTER`).
Usage: python status.py <body file>    (an empty file: nothing to post today)"""
import datetime
import json
import os
import re
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
FB = (("NFL", "data/nfl"), ("College", "data/ncaaf"))
REPO = "https://github.com/smh0602/gizmos-picks"
NOT_UPDATING = "No: %s, so no collect run has finished since."


def stale_health(health, now):
    """None while health.json is recent enough to read; else why not, in words."""
    seen = W._when(health.get("checked_at"))
    if seen and now - seen <= datetime.timedelta(hours=HEALTH_MAX_H):
        return None
    return ("the health check has not run for %d hours" % ((now - seen).total_seconds() // 3600)
            if seen else "the health check has never run")


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


def refit_summary(doc, name, now, due=None):
    """`[Sam, 2026-10-12]` One football league's "is the model learning?"
    paragraph from its fb-refit.json (fb_refit.py), or why there is none.
    `[R1, 2026-10-18]` `due`: the contest's latest scheduled run (watchdog.last_due_for).
    A report built before it is LAST week's and is said to be, never shown as current:
    Monday runs have started 7-9 hours late, after this email."""
    seen = W._when((doc or {}).get("built_at"))
    head = ("%s: this week's contest has not reported yet (its run was due %s)" % (
        name, due.strftime("%a %Y-%m-%d %H:%MZ")) if due is not None and (seen is None or seen < due) else None)
    if not doc:
        return head + ", and no weekly report has landed before." if head else "%s: no weekly report yet." % name
    age = W.fb_refit_age_days(doc, now)
    if age is None or age > W.FB_REFIT_STALE_DAYS:
        return "%s the weekly report is %s days old (built %s), so there is no current reading." % (
            head + ", and" if head else name + ":", "?" if age is None else int(age), doc.get("built_at"))
    lead = ("%s. Last week's report, built %s, said: " % (head, doc.get("built_at")) if head else "%s: " % name)
    ms, lm = doc.get("miss") or {}, doc.get("line_moves") or {}
    out = [lead + ("our predicted margins miss by %.1f points on average, the books' line by %.1f; totals "
                   "%.1f against %.1f (%d games)." % (ms["margin_model"], ms["margin_books"], ms["total_model"],
                                                      ms["total_books"], ms["games"])
                   if ms.get("games") else "no finished games to measure yet.")]
    for mk, title in (("spread", "Spread"), ("moneyline", "Moneyline"), ("total", "Totals")):
        g, m = (doc.get("scoreboard") or {}).get(mk) or {}, lm.get(mk) or {}
        if not g.get("predictions"):
            out.append("%s: nothing to score yet." % title)
            continue
        n = (m.get("toward") or 0) + (m.get("against") or 0)
        out.append("%s: %s the books (log loss %.3f against %.3f), %s; %s; when it favours a side it says "
                   "%.1f%% and that side wins %.1f%%." % (
                       title, {"ahead": "ahead of", "behind": "behind"}.get(g["state"], "level with"),
                       g["model_log_loss"], g["books_log_loss"], {
                           "closer": "getting closer over the last 4 weeks",
                           "further": "falling further back over the last 4 weeks"}.get(
                           g["trend"]["state"], g["trend"]["state"]),
                       "lines moved our way in %d of %d games (%d%%; 50%% means no edge)" % (
                           m["toward"], n, round(m["toward_share"])) if n else "no line moves to read yet",
                       g["said"], g["hit"]))
    for x in doc.get("challengers") or []:
        v, s = x["verdict"], x.get("scored") or {}
        out.append("Challenger %s (%s): %s." % (x["name"], x["what"], {
            "NO DATA": "its data is not stored yet",
            "WITHDRAWN": "withdrawn, it was worse on past games",
            "NOT APPLICABLE": "not applicable against the current champion (how it should read is yours "
                              "to decide)"}.get(v, "%d of %d scored predictions, %s" % (
                s.get("predictions") or 0, 300, {"NOT YET MEASURABLE": "not yet measurable",
                                                 "NOT YET": "not better yet", "WINS": "it WINS"}.get(v, v)))))
    return " ".join(out)


def own_branch(branch, name):
    """`branch` is challenger `name`'s own fb/champion-<lg>-<name>-<date> (fb_refit.push_branch)."""
    return bool(re.match(r"fb/champion-[a-z]+-%s-\d{4}-\d{2}-\d{2}$" % re.escape(name), branch or ""))


def refit_wins(doc, name):
    """[(the "Needs you" item, its clicks)] for every challenger that WINS.
    `[R1, 2026-10-18]` A merge link only to the challenger's OWN branch: fb_refit pushes
    nothing while another fb/champion-<lg>-* branch is on GitHub (a merged one stays
    there), and nothing while the league already has a champion (`needs_sam`)."""
    out = []
    for x in (doc or {}).get("challengers") or []:
        if x.get("verdict") != "WINS":
            continue
        s = x["scored"]
        what = ("%s challenger %s (%s) beat the current game model: log loss %.4f against %.4f over %d "
                "scored predictions in %d games, one-sided p = %.4g (it needed under %.4g)" % (
                    name, x["name"], x["what"], s["challenger_log_loss"], s["champion_log_loss"],
                    s["predictions"], s["games"], s["p"], x["alpha"]))
        br = x.get("branch")
        if not br:
            out.append((what + ". %s" % (x.get("needs_sam") or "NEEDS SAM: no branch was pushed for it"),
                        ["Nothing to merge: no branch was pushed, so the site keeps the current model. "
                         "How a second switch should work (CHAMPION as an ordered list, so the model put "
                         "on the site is the one that was scored) is a frozen rule in "
                         "research/fb_refit_spec.md §3, and it is yours to decide."]))
            continue
        if not own_branch(br, x["name"]):
            out.append((what + ", but an older champion branch, %s, is still on GitHub, so no branch was "
                        "pushed for %s: that older branch must be merged, or closed and deleted, first" % (
                            br, x["name"]),
                        ["1. On GitHub open Pull requests and find the one for %s (or Code, then Branches)." % br,
                         "2. Merge it, or close it and delete the branch %s with its trash icon." % br,
                         "3. If %s still wins on a later Monday, its own branch is pushed then and this "
                         "email links it." % x["name"]]))
            continue
        out.append((what,
                    ["1. Open %s/compare/main...%s?expand=1" % (REPO, br),
                     "2. Click the green \"Create pull request\" button (twice: once on the page, once under "
                     "the title box).",
                     "3. Wait until the box at the bottom says \"All checks have passed\".",
                     "4. Click \"Merge pull request\", then \"Confirm merge\" (or \"Close pull request\" to "
                     "keep the current model)."]))
    return out


def injury_recorded(root, lg):
    """`[2026-10-26]` Does THIS tree's research/fb_sim_backtest.json hold `lg`'s injury entry?
    (It reaches main only by Sam's merge of the injury branch.)"""
    return lg in (_read(os.path.join(root, "research", "fb_sim_backtest.json")).get("injuries") or {})


def injury_branch(doc, name, recorded=False):
    """`[Sam, 2026-10-17]` [(the "Needs you" item, its clicks)] when the injury test fixed in advance
    (research/cfb_injuries_design.md §4, fb_inj_backtest.auto) has run and its branch waits for Sam.
    `[2026-10-26]` ⛔ Not once `recorded` (main holds the entry: the branch was merged).
    fb-refit.json still says "measured" until the next Monday's job, and the email kept asking
    Sam to merge a branch he had merged."""
    st = (doc or {}).get("injury_backtest") or {}
    if recorded:
        return []
    if st.get("state") != "measured" or not st.get("branch"):
        return []
    e = st.get("entry") or {}
    ll, cr = e.get("logloss") or {}, e.get("closing_return") or {}
    what = ("%s injuries took the test fixed in advance and %s it: log loss %s with them against %s without, "
            "closing-line return %s%% against %s%%, on %s questions (%s)" % (
                name, "PASSED" if st.get("passes") else "FAILED", ll.get("with"), ll.get("without"),
                cr.get("with"), cr.get("without"), e.get("questions"),
                "merging switches them on in the picks" if st.get("passes")
                else "merging only records the result; they stay off"))
    return [(what, ["1. Open %s/compare/main...%s?expand=1" % (REPO, st["branch"]),
                    "2. Click the green \"Create pull request\" button (twice: once on the page, once under "
                    "the title box).",
                    "3. Wait until the box at the bottom says \"All checks have passed\".",
                    "4. Click \"Merge pull request\", then \"Confirm merge\"."])]


def build(root=ROOT, now=None):
    """-> (body, needs): the weekly issue's text and what needs Sam (empty: nothing)."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    since = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    health = _read(os.path.join(root, "data", "latest", "health.json"))
    old = stale_health(health, now)
    findings = [] if old else health.get("findings") or []
    runs, stale = R.run_list(os.path.join(root, "data", "latest", "runs.json"), now)
    wf = (runs or {}).get("by_workflow") or {}
    broken = ([{"key": "watchdog:health", "severity": "BROKEN", "what": old}] if old else []) + [
        f for f in findings if f.get("severity") == "BROKEN"]
    refit = [(name, d, _read(os.path.join(root, d, "latest", "fb-refit.json"))) for name, d in FB]
    won = [w for name, d, doc in refit for w in refit_wins(doc, name) + injury_branch(
        doc, name, injury_recorded(root, d.split("/")[-1]))]
    needs = [f["what"] for f in broken] + [w[0] for w in won]
    L = ["Needs you: %s." % "; ".join(needs) if needs else "Nothing needs you this week."]
    for what, clicks in won:
        L += ["", "**%s.**" % what] + clicks
    L += ["", "## Records (last 7 days / overall)"]
    for name, d in LEAGUES:
        L.append("**%s**" % name)
        L += ["- %s: %s / %s" % (k, _rate(*wk), _rate(*al)) for k, wk, al in records(root, d, since)]
    L += ["", "## Is the football model learning?"] + ["- " + refit_summary(doc, name, now, W.last_due_for(
        d + "/latest/fb-refit.json", now)) for name, d, doc in refit]
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
            if r.get("measured") and (r.get("late_min") or 0) > F.GRACE_MIN and str(r.get("due_at")) >= since:
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
        L.append(W.what_to_do(broken, NOT_UPDATING % old if old else W.site_updating(findings)))
    return "\n".join(L) + "\n", needs


def today(root=ROOT, now=None):
    """`[Sam, 2026-10-07]` THE DAILY DEAD-MAN CHECK: the watchdog runs inside collect,
    so a collect that stops entirely says nothing. Monday (UTC): the week. Any other
    day: only a health check too old to read; otherwise "" (nothing is posted)."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if now.weekday() == 0:
        return build(root, now)[0]
    old = stale_health(_read(os.path.join(root, "data", "latest", "health.json")), now)
    if not old:
        return ""
    return "Needs you: %s.\n\n%s\n%s\n" % (old, self_repair.COUNTER, W.what_to_do(
        [{"key": "watchdog:health", "severity": "BROKEN", "what": old}], NOT_UPDATING % old))


if __name__ == "__main__":
    with open(sys.argv[1], "w", encoding="utf-8") as fh:
        fh.write(today())
