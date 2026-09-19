#!/usr/bin/env python3
"""
IS THE ODDS API SPEND ON A TRAJECTORY TO BLOW THE PLAN? NOTHING ASKED.

🔴🔴 `budget.py` HAS ALWAYS COMPUTED THIS AND NO WORKFLOW HAS EVER RUN IT.
`[measured 2026-09-15]` Both mentions of `budget.py` in `collect.yml` are
**comments**. It is a correct tool that has only ever run when a human
typed its name — which is to say, it has reported the spend trajectory to
nobody.

⛔ THE CAPS ARE NOT THE ANSWER TO THIS QUESTION, AND IT IS EASY TO THINK
THEY ARE. `collect.py` enforces `FLAT_DAILY_CAP` (600) and
`HARD_DAY_CEIL` (1,200), so **money cannot run away in a day**. But
1,200/day sustained is **36,000 a month against a 20,000 plan** — 180%.
➡️ The caps bound the SPIKE. Nothing bounds the CREEP, and a creep is
what lands you at 100% of plan on the 28th with a dead key and a board
with no prices.

➡️ FIVE WATCHERS NOW, FIVE QUESTIONS:

    watchdog.py      is the PRODUCT right?         (reads repo files)
    collect.yml      did the TEST STEP fail?
    runs_report.py   did any RUN fail, did a cron land?
    calibration.py   are the PICKS WINNING?
    this file        is the SPEND on trajectory?

══════════════════════════════════════════════════════════════════════
🔴 IT RUNS `budget.py`. IT DOES NOT REIMPLEMENT IT.

⛔ A second copy of the costing would be a second thing to keep in step
with `collect.py`'s market lists, and this repo's founding lesson is that
the copy goes stale and still prints ✅. So the numbers come from
`budget.py`'s own stdout and the ONLY thing added here is the VERDICT.

⚠️ THAT MAKES THIS A PARSER OF ANOTHER TOOL'S PROSE, WHICH IS A REAL
RISK, AND IT IS HANDLED BY FAILING CLOSED. Four figures are cross-checked
against each other (the two per-sport months must sum to the total, each
month must be 30x its own day rate, and the printed percentage must match
the one recomputed from the plan). ⛔ If ANY of that disagrees, the answer
is `UNREADABLE` — never `OK`. A format drift makes this go quiet and warn,
it cannot make it say "fine". `test_budget_watch.py` drives the parser
against the REAL `budget.py`, so drift goes red in CI rather than silent
in production.

══════════════════════════════════════════════════════════════════════
🔴 THE BAR IS BORROWED FROM TWO NUMBERS ALREADY IN THE REPO, AND THEY
   AGREE WITH EACH OTHER. NEITHER WAS INVENTED HERE.

  1. `budget.py` already prints `🔴 ABOVE 90% OF PLAN` at `_mo > PLAN*0.9`.
     **This file must not disagree with the tool it runs** — a cost tool
     that contradicts itself on one page is the failure `budget.py`'s own
     header names. `test_budget_watch.py` pins `WARN_FRAC` to that line.
  2. 90% of a 20,000 plan over 30 days is **600/day**, and `collect.py`'s
     `FLAT_DAILY_CAP` is `int(20000/31*0.93)` = **600/day**. The bar is
     therefore exactly "the measured run-rate has reached the daily
     allowance the collector already rations itself to."

➡️ So the alarm means something concrete and checkable: *spend is no
longer inside the budget the collector was designed around.* It is not a
vibe and it is not a round number somebody liked.

══════════════════════════════════════════════════════════════════════
⚠️ IT DOES **NOT** ALARM ON THE CEILING, AND THAT IS DELIBERATE.

`budget.py` also prints a cron-derived CEILING — 217% of plan today. ⛔
That number is a ceiling and its own author says in capitals that it is
**NOT A FORECAST**: it prices every football props cron as if it fired on
a full slate, which `freshness._props_warranted()` stands down most days.
Alarming on it would fire every single day on a system that is working
(`CLAUDE.md`: *a guard that fires on correct code is the other failure,
not a safe one*). ✅ It is REPORTED in the body, never alarmed on.

══════════════════════════════════════════════════════════════════════
⛔ AND THE REMEDY IS NEVER "RETIME A CRON". `CLAUDE.md`: **the deployed
MLB crons keep running** — nothing in the schedule is to be disabled,
retimed or repriced. The body says so out loud, because the agent most
likely to read this issue at 3am is the one that needs telling.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# 🔴 BORROWED FROM `budget.py`, NOT CHOSEN HERE. See the header — and
#    `test_budget_watch.py` reads `budget.py`'s own `PLAN * 0.9` and fails
#    if these two ever drift apart.
WARN_FRAC = 0.90

# 🔴 A RATE OVER A WINDOW THAT MISSES A WEEKEND IS NOT A RATE.
#    `[measured 2026-09-15 from budget.py's own per-day output]` football
#    billed 475 on Saturday and 258 on Sunday against 30-75 on weekdays —
#    a 6-16x swing. A 3-day window ending on a Wednesday would read the
#    football half of the bill at a fifth of its true rate.
# ⚠️ Under this it reports NOT YET MEASURABLE: not a pass, not a fail.
MIN_DAYS = 7

# ⚠️ `budget.py` walks every snapshot under data/ — 1,000+ gzip files. It
#    takes ~2s today. 300s is 150x that: generous on purpose, because a
#    timeout chosen tight is a guard that fires on correct code.
BUDGET_TIMEOUT = 300

# ── the output contract, in one place ─────────────────────────────────
# ⛔ EVERY ONE OF THESE MUST MATCH OR THE ANSWER IS `UNREADABLE`. A
#    partial parse is the shape that reports a confident wrong number.
_RE_MLB = re.compile(r"^MLB \(measured\)\s+(\d+)/day\s+(\d+)/month", re.M)
_RE_FB = re.compile(r"^FOOTBALL \(measured\)\s+(\d+)/day\s+(\d+)/month", re.M)
_RE_TOT = re.compile(
    r"^TOTAL \(measured\)\s+(\d+)/month of ([\d,]+)\s+\((\d+)%\)", re.M)
_RE_WINDOW = re.compile(r"^\s*mean of last (\d+)\s", re.M)
_RE_DAY = re.compile(r"^\s{2}(\d{4}-\d{2}-\d{2})\s+(\d+) credits\s*$", re.M)
_RE_CEIL = re.compile(r"^\s*\.\.\.worst case.*?(\d+)/month\s+\((\d+)%\)", re.M)


def run_budget(root=ROOT):
    """Run `budget.py` and hand back (rc, stdout, stderr).

    ⚠️ `cwd=root` MATTERS. `budget.py`'s per-mode section globs a RELATIVE
    `data/...` path, so running it from anywhere else silently drops that
    block. Everything this file parses is absolute-pathed, but pinning the
    cwd costs nothing and removes a class of question.
    """
    try:
        p = subprocess.run([sys.executable, "budget.py"], cwd=root,
                           capture_output=True, text=True,
                           timeout=BUDGET_TIMEOUT)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return None, "", "budget.py did not finish in %ds" % BUDGET_TIMEOUT
    except OSError as e:
        return None, "", "could not run budget.py: %s" % e


def _bad(why):
    return {"state": "UNREADABLE", "why": why}


def parse(text):
    """`budget.py` stdout -> the four measured figures, or UNREADABLE.

    🔴 CROSS-CHECKED, NOT JUST MATCHED. Four regexes agreeing with a file
    that changed shape underneath them is exactly how a parser reports a
    confident wrong number, so the figures are made to agree with EACH
    OTHER before any of them is believed.
    """
    m, f, t = _RE_MLB.search(text), _RE_FB.search(text), _RE_TOT.search(text)
    missing = [n for n, x in (("MLB (measured)", m), ("FOOTBALL (measured)", f),
                              ("TOTAL (measured)", t)) if not x]
    if missing:
        return _bad("budget.py printed no %s line — its output format "
                    "changed and this parser has not" % ", ".join(missing))
    mlb_day, mlb_mo = int(m.group(1)), int(m.group(2))
    fb_day, fb_mo = int(f.group(1)), int(f.group(2))
    total_mo, plan = int(t.group(1)), int(t.group(2).replace(",", ""))
    pct_said = int(t.group(3))
    if plan <= 0:
        return _bad("budget.py reports a plan of %d credits" % plan)
    # ⛔ THE THREE AGREEMENTS. Any one failing means the numbers scraped
    #    off the page are not the numbers the page is about.
    if mlb_mo != mlb_day * 30 or fb_mo != fb_day * 30:
        return _bad("per-sport month is not 30x its day rate (mlb %d/%d, "
                    "fb %d/%d) — the output format moved"
                    % (mlb_day, mlb_mo, fb_day, fb_mo))
    if total_mo != mlb_mo + fb_mo:
        return _bad("total %d is not mlb %d + football %d — this parser is "
                    "reading a different report than it thinks"
                    % (total_mo, mlb_mo, fb_mo))
    pct = 100.0 * total_mo / plan
    # ⚠️ ONE POINT OF TOLERANCE, because `budget.py` prints `%.0f` and this
    #    recomputes from the parsed integers. It is a redundant check on a
    #    figure already agreed three other ways, not the judgement.
    if abs(pct - pct_said) > 1.0:
        return _bad("budget.py printed %d%% of plan where its own figures "
                    "give %.1f%%" % (pct_said, pct))
    # ⚠️ THE WINDOW IS THE SHORTER OF THE TWO SPORTS'. A 7-day football
    #    mean beside a 2-day MLB mean is a 2-day answer.
    windows = [int(w) for w in _RE_WINDOW.findall(text)]
    if not windows:
        return _bad("budget.py printed no `mean of last N` line — cannot "
                    "tell how many days the rate is averaged over")
    ceil = _RE_CEIL.search(text)
    return {"state": "READ", "mlb_day": mlb_day, "fb_day": fb_day,
            "day": mlb_day + fb_day, "month": total_mo, "plan": plan,
            "pct": pct, "days": min(windows),
            "ceil_month": int(ceil.group(1)) if ceil else None,
            "ceil_pct": int(ceil.group(2)) if ceil else None}


def direction(text):
    """Older half vs newer half of the per-day series. CONTEXT, NOT A BAR.

    ⛔ THIS NEVER CHANGES THE VERDICT. A rising week is what every
    football Saturday looks like; alarming on it would fire on correct
    behaviour. It is here because 'is it going up' is the question a
    human actually asks when they read the number.
    ⚠️ Returns None whenever it cannot answer, and the caller says so
    rather than filling the gap in.
    """
    days = {}
    for d, v in _RE_DAY.findall(text):
        days[d] = days.get(d, 0) + int(v)
    keys = sorted(days)
    if len(keys) < 4:
        return None
    half = len(keys) // 2
    old = sum(days[k] for k in keys[:half]) / half
    new = sum(days[k] for k in keys[-half:]) / half
    return {"old": old, "new": new, "delta": new - old,
            "from": keys[0], "to": keys[-1]}


def judge(p):
    """A parsed report -> a verdict. ⛔ Never raises on a malformed one.

    🔴 `{}` USED TO COME BACK AS `{}` AND THE CALLER DIED ON `v["state"]`.
    `[found 2026-09-15 by driving it]` A watcher that raises before it
    reports is indistinguishable from all-clear, so ANYTHING that is not a
    successful parse leaves here as UNREADABLE, carrying a state.
    """
    if not isinstance(p, dict) or "state" not in p:
        return _bad("nothing to judge: %r" % (p,))
    if p["state"] != "READ":
        return p
    bar = WARN_FRAC * p["plan"]
    out = dict(p)
    # ⛔ THE SAMPLE GATE COMES FIRST, exactly as it does in
    #    `calibration.py`. A rate off three weekdays is not a rate.
    if p["days"] < MIN_DAYS:
        out["state"] = "NOT_MEASURABLE"
        out["why"] = ("the rate is averaged over %d day(s), under the %d "
                      "needed to cover a full week — football bills 6-16x "
                      "more at a weekend than midweek, so a short window "
                      "is not a run-rate" % (p["days"], MIN_DAYS))
        return out
    if p["month"] >= bar:
        out["state"] = "OVER"
        out["why"] = ("measured %d credits/day over the last %d days "
                      "projects %s for the month — %.0f%% of the %s plan, "
                      "at or past the %.0f%% bar (%s credits)"
                      % (p["day"], p["days"], f"{p['month']:,}", p["pct"],
                         f"{p['plan']:,}", 100 * WARN_FRAC, f"{bar:,.0f}"))
        return out
    out["state"] = "OK"
    out["why"] = ("measured %d credits/day projects %s for the month — "
                  "%.0f%% of the %s plan, inside the %.0f%% bar"
                  % (p["day"], f"{p['month']:,}", p["pct"],
                     f"{p['plan']:,}", 100 * WARN_FRAC))
    return out


def render(v, trend=None):
    """The issue body. ⚠️ Every sentence carries a number."""
    o = []
    if v["state"] == "OVER":
        # ⛔ ~~"— every job is green and every cap is holding."~~
        # STRUCK 2026-09-19. This module reads `budget.py`'s output and
        # the stored credit readings; it cannot see a workflow run, and
        # it printed that while `collect.yml` was red on every run for
        # 32 hours. ✅ The cap half IS measured here, so it stays; the
        # job half was never measured and is gone.
        o.append("**The Odds API spend is on a trajectory to exceed the "
                 "plan. This is a MONEY finding: every cap below is "
                 "holding and the spend still does not fit.**\n")
        o.append("- %s" % v["why"])
        o.append("- MLB **%d/day**, football **%d/day**, combined "
                 "**%d/day**." % (v["mlb_day"], v["fb_day"], v["day"]))
        o.append("")
        o.append("⛔ **The caps do not solve this.** `collect.py` holds any "
                 "single day under `HARD_DAY_CEIL` (1,200), but 1,200/day "
                 "sustained is 36,000 a month against a 20,000 plan. The "
                 "caps bound a spike; this is a creep.")
    elif v["state"] == "NOT_MEASURABLE":
        o.append("⚠️ **NOT YET MEASURABLE** — %s. Not a pass and not a "
                 "fail." % v["why"])
    elif v["state"] == "UNREADABLE":
        o.append("⚠️ **COULD NOT LOOK** — %s." % v["why"])
        o.append("")
        o.append("⛔ This is not an all-clear. No open issue is closed on "
                 "the strength of not having looked.")
        return "\n".join(o)
    else:
        o.append("✅ %s" % v["why"])
    if v.get("ceil_pct"):
        o.append("")
        o.append("⚠️ For scale, `budget.py`'s cron-derived CEILING is %s"
                 "/month (%d%% of plan). ⛔ **That is a ceiling, not a "
                 "forecast** — it prices every football props cron as if "
                 "it fired on a full slate, and `_props_warranted()` "
                 "stands most of them down. Nothing here alarms on it."
                 % (f"{v['ceil_month']:,}", v["ceil_pct"]))
    o.append("")
    if trend:
        o.append("📈 Direction over %s → %s: **%+.0f credits/day** (%.0f → "
                 "%.0f). ⚠️ Context only — a rising week is what a football "
                 "Saturday looks like, and nothing alarms on it."
                 % (trend["from"], trend["to"], trend["delta"],
                    trend["old"], trend["new"]))
    else:
        o.append("📈 Direction: **not readable** — fewer than 4 days in "
                 "`budget.py`'s per-day series. Reported as unknown rather "
                 "than filled in.")
    o.append("")
    o.append("⛔ **Do not fix this by retiming, disabling or repricing a "
             "cron.** `CLAUDE.md`: the deployed MLB crons keep running, and "
             "nothing in the schedule is to be disabled, retimed or "
             "repriced. The lever this issue is about is whether a NEW "
             "market, region or cron gets added — not the ones already "
             "there.")
    o.append("")
    o.append("⛔ **Do not fix this by changing the bar.** The 90% comes "
             "from `budget.py`'s own `PLAN * 0.9` line and coincides with "
             "`collect.py`'s `FLAT_DAILY_CAP` of 600/day. A check may only "
             "change when it asks the WRONG QUESTION, and the replacement "
             "must be harder to pass.")
    o.append("")
    o.append("_One issue, updated in place, closed by itself when the "
             "measured run-rate is back inside plan. Free: `budget.py` "
             "reads committed snapshots and calls no API._")
    return "\n".join(o)


def main():
    rc, out, err = run_budget()
    if rc is None:
        sys.stderr.write("%s\n" % err)
        print(render(_bad(err)))
        return 2
    if rc != 0:
        # ⛔ `budget.py` EXITS NON-ZERO WHEN ITS OWN INPUTS DO NOT PARSE —
        #    a genuinely unmapped cron, a missing market list. Its numbers
        #    are not trustworthy then, so this is "I could not look".
        why = ("budget.py exited %d — its own parse of collect.py or the "
               "workflow failed, so its figures are not trustworthy: %s"
               % (rc, (err or out).strip().splitlines()[-1:] or ["no output"]))
        sys.stderr.write("%s\n" % why)
        print(render(_bad(why)))
        return 2
    v = judge(parse(out))
    if v["state"] == "UNREADABLE":
        # 🔴 "I COULD NOT LOOK" IS NOT "THE SPEND IS FINE".
        sys.stderr.write("could not read budget.py: %s\n" % v["why"])
        print(render(v))
        return 2
    if v["state"] == "NOT_MEASURABLE":
        # ⛔ AND NEITHER IS "I DO NOT HAVE ENOUGH DAYS TO SAY". This
        #    deliberately differs from `calibration.py`, which folds its
        #    NOT_MEASURABLE into the OK exit: there, a thin sample sits
        #    beside leagues that ARE measurable. Here it is the whole
        #    answer, and an exit of 0 would CLOSE an open money issue on
        #    the strength of a short window.
        sys.stderr.write("not yet measurable: %s\n" % v["why"])
        print(render(v, direction(out)))
        return 2
    if v["state"] == "OK":
        print("OK  %d/day  %d/month  %.0f%% of %d  (window %dd)"
              % (v["day"], v["month"], v["pct"], v["plan"], v["days"]))
        return 0
    print(render(v, direction(out)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
