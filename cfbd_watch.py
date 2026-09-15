#!/usr/bin/env python3
"""
IS THE CFBD QUOTA GOING TO RUN OUT? `cfbd_budget.py` KNOWS AND NOBODY ASKS.

🔴🔴 THE SECOND BUDGET TOOL NOTHING RAN. `[found 2026-09-15 while wiring
`budget.py`, reported and left; wired now on Sam's instruction.]` It is
the identical defect: a correct, carefully-derived cost tool whose entire
output has only ever reached whoever typed its name.

⛔ AND THE CONSEQUENCE IS NOT HYPOTHETICAL — IT ALREADY HAPPENED ONCE.
`[2026-09-09]` CFBD answered **HTTP 429 on every endpoint from 09-06 to
at least 09-09**: games, player game, plays, roster. The college Trends
table and the stored schedule **froze solid for five days.** September's
quota resets on the 1st; it was spent in about three days at roughly
**8x the plan**. Nothing in this repo knew how many CFBD calls it made.

══════════════════════════════════════════════════════════════════════
⛔ THIS IS NOT A SECOND COPY OF `budget.py`. MEASURED, NOT ASSUMED.

Sam asked the right question first: if the two tools price the same
credits, a second watcher is a second copy of one fact (rule 66) and the
answer is to fold it in, not to run both. **They are disjoint, three
ways:**

    budget.py        the Odds API      20,000 credits/month  ODDS_MONTHLY_PLAN
    cfbd_budget.py   collegefootballdata.com  1,000 calls/month  CFBD_PLAN

  1. Different APIs, different quotas, different units — billed
     `credits` read from snapshots vs HTTP `calls` derived from `cfb.py`'s
     loop bounds. Neither file mentions the other's API.
  2. The priced mode sets do not intersect. `budget.py` prices
     `gamelines` and the four MLB props modes; this prices `cfb-probe`,
     `cfb-teams`, `fb-scores`.
  3. 🔴 THE CLINCHER: **every mode priced here is one `budget.py`
     explicitly reports as FREE.** "Free" there means free *in Odds
     credits* — and those same three modes cost **906 CFBD calls a
     month against a 1,000 quota.** A fact each tool can see and the
     other cannot is not a duplicated fact.

══════════════════════════════════════════════════════════════════════
🔴 THE BAR IS `cfbd_budget.py`'S OWN, NOT INVENTED HERE.

It already prints `⚠️ ... Little headroom for a retry storm` at
`pct >= 80`. This file must not disagree with the tool it runs — a cost
tool that contradicts itself on one page is the failure `budget.py`'s own
header names, and `test_cfbd_watch.py` pins `WARN_FRAC` to that line.

➡️ 80% of 1,000 leaves **200 calls of headroom — about 13 `cfb-probe`
rebuilds.** On a quota this small that is the difference between a bad
week and five days of 429s, which is why the bar is where the tool
already put it.

⚠️ AND `cfbd_budget.py` PRICES A **FLOOR**, WHICH IS THE OPPOSITE OF
`budget.py`'s CEILING PROBLEM. It counts ONE attempt per scheduled
build. **Converge retries are what actually blew the quota** and cannot
be priced from a cron. So the retry figure is REPORTED here, never
alarmed on: at 7 attempts a day it is 634% of the free tier, and a guard
that fires every day on a working system is a guard that gets filtered
(rule 238). ✅ Alarm on the floor, report the retry — exactly the shape
`budget_watch.py` uses for the measurement and the ceiling.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# 🔴 BORROWED FROM `cfbd_budget.py`'s OWN `pct >= 80` LINE. See the
#    header — and the test reads that line and fails if the two drift.
WARN_FRAC = 0.80

# ⚠️ THE NUMBER `cfbd_budget.py`'s OWN HEADER NAMES: "~7 / day, measured
#    from the commit history of backfill-report.txt, 09-06..09-08" — the
#    retry rate that actually blew the quota. ⛔ REPORTED, NEVER A BAR.
RETRY_N = 7

# ⚠️ Reads two local files and no network. 120s is ~60x what it takes.
TIMEOUT = 120

_RE_VERDICT = re.compile(
    r"^[^\n]*?(\d+)/month against a (\d+) plan\s*—\s*(\d+)%", re.M)
_RE_MODE = re.compile(r"^\s{2}([a-z-]+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$", re.M)
_RE_TIER = re.compile(r"^\s{2}(\S.*?)\s{2,}(\d+)/mo\s+(\d+)%", re.M)
_RE_EARLY = re.compile(r"early-stop:\s*(ON|🔴 OFF)")


def run_cfbd(args=(), root=ROOT):
    """Run `cfbd_budget.py`. -> (rc, stdout, stderr); rc None if it died."""
    try:
        p = subprocess.run([sys.executable, "cfbd_budget.py"] + list(args),
                           cwd=root, capture_output=True, text=True,
                           timeout=TIMEOUT)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return None, "", "cfbd_budget.py did not finish in %ds" % TIMEOUT
    except OSError as e:
        return None, "", "could not run cfbd_budget.py: %s" % e


def _bad(why):
    return {"state": "UNREADABLE", "why": why}


def parse(text):
    """`cfbd_budget.py` stdout -> the figures, or UNREADABLE.

    🔴 CROSS-CHECKED, NOT JUST MATCHED — the same discipline
    `budget_watch.py` uses on a prose parser. The percentage the tool
    printed must agree with the one recomputed from its own month and
    plan, and the per-mode calls/week must sum to the weekly total it
    printed. ⛔ Any disagreement is UNREADABLE, never OK: a format drift
    makes this go quiet and warn, it cannot make it say "fine".
    """
    v = _RE_VERDICT.search(text or "")
    if not v:
        return _bad("cfbd_budget.py printed no `N/month against a M plan` "
                    "line — its output format changed and this parser "
                    "has not")
    month, plan, pct_said = int(v.group(1)), int(v.group(2)), int(v.group(3))
    if plan <= 0:
        return _bad("cfbd_budget.py reports a plan of %d calls" % plan)
    pct = 100.0 * month / plan
    # ⚠️ One point of tolerance: the tool prints `%.0f` and this recomputes
    #    from parsed integers. A redundant check, not the judgement.
    if abs(pct - pct_said) > 1.0:
        return _bad("cfbd_budget.py printed %d%% where its own figures "
                    "give %.1f%%" % (pct_said, pct))
    modes = [{"mode": m, "per_build": int(a), "builds_wk": int(b),
              "calls_wk": int(c)} for m, a, b, c in _RE_MODE.findall(text)]
    if not modes:
        return _bad("cfbd_budget.py printed no per-mode table — the "
                    "output format moved")
    tiers = [{"name": n.strip(), "limit": int(l), "pct": int(p)}
             for n, l, p in _RE_TIER.findall(text)]
    early = _RE_EARLY.search(text or "")
    return {"state": "READ", "month": month, "plan": plan, "pct": pct,
            "modes": modes, "tiers": tiers,
            "early_stop": bool(early and early.group(1) == "ON")}


def judge(p):
    """Figures -> a verdict. ⛔ Never raises on a malformed report."""
    if not isinstance(p, dict) or "state" not in p:
        return _bad("nothing to judge: %r" % (p,))
    if p["state"] != "READ":
        return p
    out = dict(p)
    bar = WARN_FRAC * p["plan"]
    if p["month"] >= bar:
        out["state"] = "OVER"
        out["why"] = ("the deployed schedule implies %s CFBD calls a "
                      "month against a %s plan — %.0f%%, at or past the "
                      "%.0f%% bar (%s calls)"
                      % (f"{p['month']:,}", f"{p['plan']:,}", p["pct"],
                         100 * WARN_FRAC, f"{bar:,.0f}"))
        return out
    out["state"] = "OK"
    out["why"] = ("the deployed schedule implies %s CFBD calls a month "
                  "against a %s plan — %.0f%%, inside the %.0f%% bar"
                  % (f"{p['month']:,}", f"{p['plan']:,}", p["pct"],
                     100 * WARN_FRAC))
    return out


def render(v, retry_month=None):
    """The issue body. ⚠️ Every sentence carries a number."""
    o = []
    if v["state"] == "UNREADABLE":
        o.append("⚠️ **COULD NOT LOOK** — %s." % v["why"])
        o.append("")
        o.append("⛔ This is not an all-clear. No open issue is closed on "
                 "the strength of not having looked.")
        return "\n".join(o)
    if v["state"] == "OVER":
        o.append("**The CFBD call budget is close to its quota. This is a "
                 "DATA-OUTAGE finding, not a pipeline one — every job is "
                 "green.**\n")
        o.append("- %s" % v["why"])
    else:
        o.append("✅ %s" % v["why"])
    o.append("")
    o.append("| mode | calls/build | builds/wk | calls/wk |")
    o.append("|---|---:|---:|---:|")
    for m in v.get("modes", []):
        o.append("| `%s` | %d | %d | %d |"
                 % (m["mode"], m["per_build"], m["builds_wk"], m["calls_wk"]))
    o.append("")
    if v.get("tiers"):
        o.append("Against CFBD's tiers: "
                 + ", ".join("**%s** %d%%" % (t["name"], t["pct"])
                             for t in v["tiers"]) + ".")
        o.append("")
    if v["state"] == "OVER":
        o.append("⛔ **WHAT THIS COSTS WHEN IT RUNS OUT — it already has.** "
                 "`[2026-09-09]` CFBD answered **429 on every endpoint for "
                 "five days** and the college Trends table and stored "
                 "schedule froze solid. The quota resets on the 1st; there "
                 "is no way to buy the month back.")
        o.append("")
    if retry_month:
        o.append("⚠️ **THIS IS A FLOOR, NOT A FORECAST.** `cfbd_budget.py` "
                 "prices ONE attempt per scheduled build. **Converge "
                 "retries are what actually blew the quota** — at %d "
                 "attempts a day the same schedule prices at **%s/month "
                 "(%.0f%% of plan)**. ⛔ Nothing alarms on that number: it "
                 "would fire every day on a working system. It is here "
                 "because the floor is the optimistic half."
                 % (RETRY_N, f"{retry_month:,}",
                    100.0 * retry_month / v["plan"]))
        o.append("")
    if not v.get("early_stop"):
        o.append("🔴 **`build_pace`'s early stop is OFF**, so every rebuild "
                 "is a flat 32 calls whatever the date — the exact shape "
                 "that blew the quota in September.")
        o.append("")
    o.append("➡️ **The cheapest fix is not a code change.** CFBD's "
             "**Academic tier is 3,000 calls a month and also free** with "
             "a `.edu` address; Tier 1 is $1/month for 5,000. ⛔ Those "
             "numbers are quoted from their pricing page and go stale — "
             "re-read it before acting.")
    o.append("")
    o.append("⛔ **Do not fix this by retiming or disabling a cron.** "
             "`CLAUDE.md`: the deployed crons keep running, and nothing in "
             "the schedule is to be disabled, retimed or repriced.")
    o.append("")
    o.append("⛔ **Do not fix this by changing the bar.** The 80% is "
             "`cfbd_budget.py`'s own `pct >= 80` line. A check may only "
             "change when it asks the WRONG QUESTION, and the replacement "
             "must be harder to pass.")
    o.append("")
    o.append("_One issue, updated in place, closed by itself when the "
             "derived call volume is back inside the bar. Free: "
             "`cfbd_budget.py` reads the workflow and `cfb.py` and calls "
             "no API._")
    return "\n".join(o)


def main():
    rc, out, err = run_cfbd()
    # ⛔ `cfbd_budget.py` EXITS 1 WHEN IT IS OVER PLAN — that is a VERDICT,
    #    not a crash, so rc 0 and 1 are both readable output. Only a death
    #    (rc None) or an unparseable report is "I could not look".
    if rc is None:
        sys.stderr.write("%s\n" % err)
        print(render(_bad(err)))
        return 2
    v = judge(parse(out))
    if v["state"] == "UNREADABLE":
        # 🔴 "I COULD NOT LOOK" IS NOT "THE QUOTA IS FINE".
        sys.stderr.write("could not read cfbd_budget.py: %s\n" % v["why"])
        print(render(v))
        return 2
    # ⚠️ The retry figure comes from the TOOL, not from multiplying here —
    #    arithmetic done twice is arithmetic that can disagree (rule 66).
    #    ⛔ And a failure to get it degrades the CONTEXT only, never the
    #    verdict.
    retry_month = None
    r_rc, r_out, _ = run_cfbd(["--retries", str(RETRY_N)])
    if r_rc is not None:
        r = parse(r_out)
        if r.get("state") == "READ":
            retry_month = r["month"]
    if v["state"] == "OK":
        print("OK  %d/month  %d%% of %d  (floor; %d at %d retries)"
              % (v["month"], v["pct"], v["plan"], retry_month or 0, RETRY_N))
        return 0
    print(render(v, retry_month))
    return 1


if __name__ == "__main__":
    sys.exit(main())
