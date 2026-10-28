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
        v = x["verdict"]
        said = {"NOT YET MEASURABLE": "not yet measurable", "NOT YET": "not better yet", "WINS": "it WINS"}.get(v, v)
        if v == "WINS" and x.get("outranked_by"):
            # `[2026-10-26]` "went to" only when the winner holds its OWN branch: with a champion
            #    already named, or an older champion branch on GitHub, no branch was pushed for it.
            # `[2026-10-27, review 2]` ~~"so the league's one switch is X's"~~: false with a champion
            #    named (no switch to X can happen) and when the older branch is THIS challenger's own;
            #    and the reason X ranks first is §3g's (`ahead`), not always "by more".
            top = next((y for y in doc.get("challengers") or [] if y.get("name") == x["outranked_by"]), {})
            t, why, br = x["outranked_by"], ahead(top, x), top.get("branch")
            if own_branch(br, t):
                said += "; the one branch went to %s, which %s" % (t, why)
            elif not br:                      # fb_refit pushes nothing while the league names a champion
                said += "; %s %s and ranks first, but no branch was pushed: the league already has a champion%s" % (
                    t, why, " (%s)" % doc["champion"] if doc.get("champion") else "")
            elif own_branch(br, x["name"]):
                said += ("; %s %s and ranks first this week, so no branch was pushed for it: %s's own branch "
                         "from an earlier Monday, %s, is still on GitHub" % (t, why, x["name"], br))
            else:
                said += ("; %s %s and ranks first, but no branch was pushed for it: an older champion branch, "
                         "%s, is still on GitHub" % (t, why, br))
        # `[Sam, 2026-10-27]` §3h: a withdrawal is permanent, and the email says so with its day.
        out.append("Challenger %s (%s): %s." % (x["name"], x["what"], {
            "NO DATA": "its data is not stored yet",
            "WITHDRAWN": ("withdrawn for good on %s, it was worse on past games" % x["withdrawn_since"]
                          if x.get("withdrawn_since") else "withdrawn, it was worse on past games"),
            "NOT APPLICABLE": "not applicable against the current champion (how it should read is yours "
                              "to decide)"}.get(v, "%s, %s" % (counted_words(x, doc), said))))
    ps = props_summary(doc)
    if ps:
        out.append(ps)
    return " ".join(out)


def _span(seasons):
    s = sorted(seasons or [])
    return "%s-%s" % (s[0], s[-1]) if len(s) > 1 else (str(s[0]) if s else "?")


def props_summary(doc):
    """`[Sam, 2026-10-27]` §3i T74: the props model's contest in one sentence, or None before it
    has a report. ⛔ Its numbers as the report holds them; a week it failed says so."""
    ps = (doc or {}).get("props_seasons")
    if not ps:
        return None
    lead = "Props model trained on last season plus this one (%s) against today's (%s): " % (
        _span(ps.get("challenger_seasons")), _span(ps.get("champion_seasons")))
    if ps.get("error"):
        return lead + "the contest could not be run this week (%s)%s." % (ps["error"], (
            "; it won before, and its switch still waits for you (Needs you)" if ps.get("verdict") == "WINS" else ""))
    c, v = ps.get("counted") or {}, ps.get("verdict")
    if v in ("WINS", "NOT YET") and c.get("predictions"):
        nums = "log loss %.4f against %.4f over %d predictions in %d games, one-sided p = %.3g (it needs under %g)" % (
            c["challenger_log_loss"], c["champion_log_loss"], c["predictions"], c["games"], c["p"], ps["alpha"])
    else:
        nums = ""
    return lead + {
        "NOT YET REGISTERED": "it enters the contest on %s" % ps.get("registered") if ps.get("registered")
                              else "it has not entered the contest yet",
        "NO DATA": "its data is not stored yet (%s)" % ps.get("why", ""),
        "SWITCHED": "switched: this league's props model trains on last season plus this one",
        "NOT YET MEASURABLE": "not yet measurable (%d of the %d paired predictions it needs)" % (
            c.get("predictions") or 0, ps.get("floor") or 0),
        "NOT YET": "not better yet: " + nums,
        "WINS": "it WINS: " + nums + "; the switch waits for you (Needs you)"
                if ps.get("branch") else "it WINS: " + nums + "; no branch was pushed (%s)" % (
                    ps.get("branch_error") or "see the weekly report")}.get(v, str(v)) + "."


def props_switched(root, lg):
    """`[review, 2026-10-27]` Does THIS tree's card_fb.py already switch `lg`'s props model (Sam
    merged its branch)? Read from the text: status.py imports no model."""
    try:
        src = open(os.path.join(root, "card_fb.py"), encoding="utf-8").read()
    except OSError:
        return False
    return bool(re.search(r'(?m)^    "%s": LAST_TWO,' % re.escape(lg), src))


def props_wins(doc, name, switched=False):
    """`[Sam, 2026-10-27]` §3i T74: [(the "Needs you" item, its clicks)] when P2526 WINS. The
    branch switches only that league's props model; nothing changes until Sam merges it.
    `[review, 2026-10-27]` ⛔ Not once `switched` (main holds the switch: the branch was merged,
    and the report says WINS until the next Monday's run); a week the contest failed keeps the
    win it stored (its branch still waits)."""
    ps = (doc or {}).get("props_seasons") or {}
    if ps.get("verdict") != "WINS" or switched:
        return []
    c = ps.get("counted") or {}
    what = ("%s props model trained on last season plus this one (%s) beat today's (%s): log loss %.4f against "
            "%.4f over %d predictions in %d games, one-sided p = %.4g (it needed under %g)" % (
                name, _span(ps.get("challenger_seasons")), _span(ps.get("champion_seasons")),
                c["challenger_log_loss"], c["champion_log_loss"], c["predictions"], c["games"], c["p"], ps["alpha"]))
    br = ps.get("branch")
    if not br:
        return [(what + ". NEEDS SAM: no branch was pushed for it (%s)" % (ps.get("branch_error") or "see the weekly report"),
                 ["Nothing to merge: no branch was pushed, so the site keeps today's props model."])]
    return [(what, ["1. Open %s/compare/main...%s?expand=1" % (REPO, br),
                    "2. Click the green \"Create pull request\" button (twice: once on the page, once under "
                    "the title box).",
                    "3. Wait until the box at the bottom says \"All checks have passed\".",
                    "4. Click \"Merge pull request\", then \"Confirm merge\" (or \"Close pull request\" to "
                    "keep today's props model)."])]


def counted_kind(x):
    """`[Sam, 2026-10-26]` T73 (§3g): what a challenger's verdict counts, in Sam's words."""
    if "counted" not in x:                           # a report from before §3g: its own rule
        return "scored predictions"
    # `[2026-10-27, review 2]` after a champion switch the eight's scored weeks restart at
    #    `scored_from` (§3), so ~~"since registration"~~ would claim weeks it no longer counts
    if x.get("counts") != "all" and (x.get("scored_from") or "") > (x.get("registered") or "9"):
        return "predictions scored since %s (the count restarted with the new champion)" % x["scored_from"]
    return ("counted predictions (last season and this season)" if x.get("counts") == "all"
            else "predictions scored since registration")


def _exact(x):
    """A challenger's counted mean d and p, unrounded where fb_refit stored them (§3g's order)."""
    c = x.get("counted") or x.get("scored") or {}
    return c.get("mean_d_exact", c.get("mean_d")), c.get("p_exact", c.get("p"))


def ahead(top, other):
    """`[2026-10-27, review 2]` Why WINS `top` ranks ahead of WINS `other` in §3g's order
    (fb_refit.branch_order: the larger mean d, a tie the smaller p, then the challenger list), in
    words. ~~"beat the current model by more"~~ was said whatever the reason, a tie included."""
    (m1, p1), (m2, p2) = _exact(top), _exact(other)
    c1, c2 = top.get("counted") or {}, other.get("counted") or {}
    if m1 is not None and m2 is not None and m1 > m2:
        return "beat the current model by more" + (
            " (by less than the 6 decimals the report prints)" if c1.get("mean_d") == c2.get("mean_d") else "")
    if p1 is not None and p2 is not None and p1 < p2:
        return "beat the current model by the same amount, with the smaller p" + (
            " (smaller past the 6 decimals the report prints)" if c1.get("p") == c2.get("p") else "")
    return "beat the current model by the same amount, at the same p, and comes first in the challenger list"


def counted_words(x, doc):
    """`[Sam, 2026-10-26]` §3g: how many predictions one challenger's verdict counts, how many
    differ from the current model's and the floor, read from the report (fb_refit.MIN_SCORED,
    stored as `floor`; ⛔ never a number written here). A report from before §3g says only
    its scored count, the rule it was judged by."""
    c = x.get("counted")
    if c is None:
        return "%d scored predictions" % ((x.get("scored") or {}).get("predictions") or 0)
    if x.get("registered") and x["registered"] > str(doc.get("built_at") or "")[:10]:
        return "it enters the contest on %s, so nothing is counted yet" % x["registered"]
    floor = doc.get("floor")
    return "%d %s, %d of them different from the current model's%s" % (
        c.get("predictions") or 0, counted_kind(x), c.get("differing") or 0,
        " (%d needed)" % floor if isinstance(floor, int) else "")


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
        if x.get("outranked_by"):            # `[Sam, 2026-10-26]` §3g: said under the winner it lost the branch to
            continue
        s = x.get("counted") or x["scored"]
        what = ("%s challenger %s (%s) beat the current game model: log loss %.4f against %.4f over %d "
                "%s in %d games, one-sided p = %.4g (it needed under %.4g)" % (
                    name, x["name"], x["what"], s["challenger_log_loss"], s["champion_log_loss"],
                    s["predictions"], counted_kind(x), s["games"], s["p"], x["alpha"]))
        also = [y["name"] for y in doc.get("challengers") or [] if y.get("outranked_by") == x["name"]]
        if also:
            # `[2026-10-27, review 2]` "the one branch goes to" only when it went (`own_branch`), and
            #    "the biggest gain" only when it was (`ahead`, against the closest of the others)
            near = min((y for y in doc["challengers"] if y.get("outranked_by") == x["name"]),
                       key=lambda y: (-(_exact(y)[0] or 0), _exact(y)[1] if _exact(y)[1] is not None else 1))
            why = ahead(x, near)
            if not own_branch(x.get("branch"), x["name"]):
                what += " (%s also won this week; %s %s, and no branch was pushed)" % (
                    ", ".join(also), x["name"], why)
            elif why == "beat the current model by more":
                what += " (%s also won this week; the one branch goes to the biggest gain, %s)" % (
                    ", ".join(also), x["name"])
            else:
                what += " (%s also won this week; the one branch goes to %s, which %s)" % (
                    ", ".join(also), x["name"], why)
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


def injury_checks(root, now, days=7):
    """`[2026-10-26, review]` The game-day injury checks of the last `days` ET days, per football
    league (Sam: "make sure we're looking at injury status at 12pm of games starting and 7pm"):
    how many ran before their games, from the probe's slot log and the schedule
    (`F.injury_check_history`). A slot still open (a game after it to come) that has not run
    yet is not counted, nor one before the probe's first check (`log_since`: the week the
    check shipped is not a week of misses). ⛔ A count in the weekly, never a finding."""
    out = []
    since = F._et_today(now) - datetime.timedelta(days=days)
    for name, d in FB:
        latest = os.path.join(root, d, "latest")
        probe = _read(os.path.join(latest, "injury-check.json"))
        if not probe.get("log_since"):
            out.append("- %s: no check has run yet." % name)
            continue
        try:
            hist = F.injury_check_history(d.split("/")[-1], latest, probe.get("log") or {}, since, now)
        except Exception as e:
            out.append("- %s: can't say (%s)." % (name, type(e).__name__))
            continue
        first, log = F._parse(probe["log_since"]), probe.get("log") or {}
        hist = [h for h in hist if (h["attempts"] or h["ok_at"] or not h["open"])
                and (h["utc"] in log or first is None or F._parse(h["utc"]) >= first)]
        if not hist:
            out.append("- %s: no game day." % name)
            continue
        def say(hs):
            return ", ".join("%s %s ET" % (datetime.date.fromisoformat(h["day"]).strftime("%a %m-%d"),
                                           h["et"]) for h in hs)
        ran = [h for h in hist if h["ok_at"]]
        late = [h for h in ran if h["started"]]
        failed = [h for h in hist if not h["ok_at"] and h["attempts"]]
        missed = [h for h in hist if not h["ok_at"] and not h["attempts"]]
        line = "- %s: %d of %d checks ran" % (name, len(ran), len(hist))
        line += (" (%d after some of their games had started: %s)" % (len(late), say(late))) if late else ""
        line += ("; read nothing: %s" % say(failed)) if failed else ""
        line += ("; never ran: %s" % say(missed)) if missed else ""
        out.append(line + ".")
    return out


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
    won = [w for name, d, doc in refit for w in refit_wins(doc, name) + props_wins(
        doc, name, props_switched(root, d.split("/")[-1])) + injury_branch(
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
    L += ["", "## Game-day injury checks (last 7 days)"] + injury_checks(root, now)
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
