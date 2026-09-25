#!/usr/bin/env python3
"""Projected CFBD call volume, DERIVED FROM THE DEPLOYED WORKFLOW.

🔴 WHY THIS EXISTS, AND IT COST US THE TRENDS TAB FOR FIVE DAYS.
`[2026-09-09]` CFBD answered **HTTP 429 on every endpoint from 2026-09-06
to at least 09-09** — games, player game, plays, roster — and the college
Trends table and stored schedule froze solid. **Nothing in this repo knew
how many CFBD calls it was making.** The Odds API has had `budget.py`
since August precisely because "a budget in a comment is a budget that
goes stale"; CFBD had nothing at all, so there was no number to be wrong.

💰 **THE ARITHMETIC, ONCE SOMEONE FINALLY DID IT:**

    CFBD free tier                        1,000 calls / month
    one cfb-probe rebuild                    13 calls
    one fb-scores refresh                     2 calls
    rebuilds actually attempted           ~7 / day  (measured from the
                                          commit history of
                                          backfill-report.txt, 09-06..09-08)
    ⛔ burn BEFORE 2026-09-08's fixes    ~8,200 / month   = 8x the plan

**September's quota resets on the 1st. We spent it in about three days,
and the 429s began on the 6th.** That is the whole story.

⚠️ THE FREE TIER IS 1,000. The Academic tier (a .edu address) is 3,000
and also free; Tier 1 is $1/month for 5,000 and Tier 2 $5/month for
30,000. `[read off collegefootballdata.com/api-tiers, 2026-09-09]`
⛔ **Those numbers are quoted from their pricing page and will go stale.
Re-read the page before trusting them; the DERIVED side is what this
script owns.**

🔴 WHAT THIS SCRIPT OWNS: how many calls the DEPLOYED SCHEDULE implies.
It reads the crons and routing arms out of the workflow and the loop
bounds out of `cfb.py`, exactly as `budget.py` does for the Odds API. If
either moves, this number moves with it.

⚠️ IT MODELS THE FLOOR, NOT THE CEILING, AND SAYS SO. It counts one call
per scheduled build. **Converge retries are the thing that actually blew
the quota** and cannot be priced from a cron, so `--retries N` prices the
same schedule at N attempts a day. **Run it that way before believing a
green headline number.**
"""
import collections
import glob as _g
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from wfroutes import parse_routes   # the ONE routing-table parser

# 🔴 QUOTED FROM CFBD'S PRICING PAGE, NOT DERIVED. Re-read before trusting.
TIERS = [("Free", 1000), ("Academic (.edu)", 3000),
         ("Tier 1 ($1/mo)", 5000), ("Tier 2 ($5/mo)", 30000)]
PLAN = int(os.environ.get("CFBD_PLAN", "1000"))


def _expand(field, lo, hi):
    out = set()
    for part in str(field).split(","):
        if part == "*":
            out |= set(range(lo, hi + 1))
        elif part.startswith("*/"):
            out |= {x for x in range(lo, hi + 1) if x % int(part[2:]) == 0}
        elif "-" in part:
            a, b = part.split("-")
            out |= set(range(int(a), int(b) + 1))
        elif part.strip():
            out.add(int(part))
    return out


def fires_per_week(cron):
    """How many times a cron fires in a week. ⛔ Day-of-week is UTC and
    that is CORRECT here: we are counting REQUESTS, which happen on the
    runner's clock, not slates, which happen on the reader's."""
    m, h, _dom, _mon, dow = cron.split()
    return len(_expand(dow, 0, 6)) * len(_expand(h, 0, 23)) * len(_expand(m, 0, 59))


def signal9_one_time(root=ROOT):
    """Signal 9's one-time CFBD calls still owed: one per endpoint per
    history season whose file is missing, READ OFF `cfb.py`'s own list.
    ⛔ One-time, not monthly: each is fetched once and never again."""
    src = open(os.path.join(root, "cfb.py"), encoding="utf-8").read()
    eps = re.findall(r'\("(/player/(?:returning|portal))",\s*"([a-z]+)-\{s\}\.json\.gz"\)', src)
    try:
        import freshness as _fr
        seasons = _fr.FOOTBALL_HISTORY
    except Exception:
        seasons = (2025, 2026)
    owed = [(ep, s) for ep, stem in eps for s in seasons
            if not os.path.exists(os.path.join(root, "data", "ncaaf", "latest", "%s-%d.json.gz" % (stem, s)))]
    return {"endpoints": [ep for ep, _stem in eps], "owed": owed, "calls": len(owed)}


def calls_per_build(weeks_played=3):
    """CFBD calls one build of each mode makes, READ OFF `cfb.py`.

    ⛔ Do NOT hardcode these. `build_pace` looped `range(1, 17)` for both
    season types until 2026-09-08 — a flat 32 calls whatever the date, of
    which 29 could only return nothing in week 2. A number typed in here
    would still say 32.
    """
    src = open(os.path.join(ROOT, "cfb.py"), encoding="utf-8").read()
    early_stop = "if empty_run >= 2:" in src
    # /plays: two season types. With the early stop it is the played weeks
    # plus the two empties that prove the end; without it, the full range.
    m = re.search(r"def build_pace.*?for wk in range\((\d+),\s*(\d+)\)", src, re.S)
    lo, hi = (int(m.group(1)), int(m.group(2))) if m else (1, 17)
    span = hi - lo
    plays = ((weeks_played + 2) + 2) if early_stop else (span * 2)
    # build_season: /teams/fbs + /roster + /games x2 + /games/players per
    # played week + postseason
    season = 1 + 1 + 2 + (weeks_played + 1)
    return {"cfb-probe": plays + season, "fb-scores": 2,
            "cfb-teams": 1, "_early_stop": early_stop}


# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 THE PLAN CAN BE MEASURED, AND GUESSING IT IS WHAT WENT WRONG.
# ══════════════════════════════════════════════════════════════════════
# ⛔ `PLAN` above is read from the environment with a `1000` default, and
# for the whole of September NO WORKFLOW SET IT. Every scheduled run
# printed "906/month against a 1000 plan — 91%" against a plan that does
# not exist, and that false alarm is what made the CFBD budget look
# urgent. The real tier is 3,000 and the same 906 is 30%.
#
# 🔴 AND OUR OWN DATA HAD ALREADY RULED 1000 OUT. A reading of **2,236
# remaining** is not reachable on a 1,000/month plan, and it was sitting
# in a college schedule probe on disk the entire time. (Named only in
# prose here: `test_coaches_probe.py` reads this file as TEXT and a
# filename in a comment trips its probe-reader ratchet.)
# ➡️ So the header is not just a budget input — it is a CONTRADICTION
# DETECTOR for whatever plan somebody configured, and that is the check
# below that would have caught this without anyone being asked.
#
# ⛔ WHAT THIS DOES NOT DO IS INVENT A NUMBER. A plan inferred from a
# partial series is exactly the mistake `1000` was. `remaining` only ever
# gives a FLOOR on the ceiling — the reading after a reset has already
# had some calls taken out of it — so a floor is what it reports, and
# when it has seen no reset it says UNKNOWN and defers to the tier table.
_REMAIN_KEYS = ("X-CallLimit-Remaining", "x-calllimit-remaining")
_TIME_KEYS = ("recorded_at", "checked_at", "written_at", "built_at")


def _readings(data):
    """Every (when, remaining) the quota RECORD holds.

    ⛔ IT DOES NOT READ THE PROBE ARTIFACTS, AND THAT IS NOT AN
    OVERSIGHT. The first version globbed every plain JSON under `latest/`
    and so picked up a schedule probe — which carries the only two
    quota readings that exist anywhere. `test_coaches_probe.py` failed it
    immediately: *"NO PRODUCT FILE READS A PROBE ARTIFACT… a probe
    becoming a source is a decision Sam makes, not a diff."*
    ⚠️ The filename is deliberately not written here either: that check
    reads this file as TEXT, so naming it in a comment trips the same
    ratchet. (Which is itself a comment-as-code read — but it is a
    pre-existing guard erring toward refusal, and refusing is the safe
    direction for "has a probe become a source".)
    ✅ THE CHECK IS RIGHT AND THE CEILING STAYS AT ZERO. The two probe
    readings are EVIDENCE in a pull request, not an input to a costing
    tool. The series starts here and fills from the next run that can
    call CFBD.
    """
    import glob as _glob
    import gzip as _gzip
    import json as _json
    out = []
    pats = [os.path.join(data, "latest", "cfbd-quota.json"),
            os.path.join(data, "*", "cfbd-quota", "*.json.gz")]
    for pat in pats:
        for f in _glob.glob(pat):
            try:
                op = _gzip.open if f.endswith(".gz") else open
                doc = _json.load(op(f, "rt", encoding="utf-8"))
            except Exception:
                continue
            for when, remaining in _walk_quota(doc):
                out.append((when, remaining, os.path.basename(f)))
    # ⚠️ One reading per timestamp: the same run's block lands in `latest/`
    #    AND in the dated archive, and counting it twice would invent a
    #    reset out of a duplicate.
    seen, uniq = set(), []
    for when, remaining, src in sorted(out):
        if when in seen:
            continue
        seen.add(when)
        uniq.append((when, remaining, src))
    return uniq


def _walk_quota(doc, when=None):
    """Yield (when, remaining) from any nesting of a quota block."""
    if not isinstance(doc, dict):
        return
    when = next((doc[k] for k in _TIME_KEYS if isinstance(doc.get(k), str)),
                when)
    headers = doc.get("headers")
    if isinstance(headers, dict):
        for k in _REMAIN_KEYS:
            if k in headers:
                try:
                    if when:
                        yield when, int(str(headers[k]).strip())
                except (TypeError, ValueError):
                    pass
                break
    for v in doc.values():
        if isinstance(v, dict):
            for got in _walk_quota(v, when):
                yield got


def measured_plan(data):
    """-> dict. `floor` is a LOWER BOUND, never a plan size."""
    rs = _readings(data)
    rep = {"readings": len(rs), "first": rs[0][0] if rs else None,
           "last": rs[-1][0] if rs else None,
           "max_remaining": max((r for _w, r, _s in rs), default=None),
           "resets": 0, "floor": None, "why": ""}
    if len(rs) < 2:
        rep["why"] = ("%d reading(s) — a plan cannot be inferred from fewer "
                      "than two, and two points are a line, not a trend"
                      % len(rs))
        return rep
    # 🔴 A RESET IS THE HEADER GOING UP. The ceiling is the value it
    #    returns to — and that value has already had this month's first
    #    calls taken out of it, so it is a FLOOR and is labelled one.
    for (_w0, r0, _s0), (_w1, r1, _s1) in zip(rs, rs[1:]):
        if r1 > r0:
            rep["resets"] += 1
            rep["floor"] = max(rep["floor"] or 0, r1)
    if not rep["resets"]:
        rep["why"] = ("no reset seen across %d reading(s) — the header has "
                      "only ever gone down, so the ceiling it returns to "
                      "has not been observed" % len(rs))
    else:
        rep["why"] = ("%d reset(s) seen; the header returned to at least %d"
                      % (rep["resets"], rep["floor"]))
    return rep


# ══════════════════════════════════════════════════════════════════════
# 🔴 EVERY WORKFLOW THAT CALLS CFBD COUNTS, NOT ONLY collect.yml.
# ══════════════════════════════════════════════════════════════════════
# `[added 2026-09-22 with t60r.py]` This script derived the whole budget
# from `collect.yml`, which was right while that was the only file making
# CFBD calls. A second workflow would have spent quota that no budget
# line knew about — CLAUDE.md: the budget is DERIVED, and a number
# nobody derives is a number that goes wrong.
# ⚠️ The per-run call count is READ OFF the script, not typed here.
CFBD_HOST = "api.collegefootballdata.com"


def cfbd_scripts(root=ROOT):
    """{script name: calls per run}, read from the scripts themselves."""
    out = {}
    for p in sorted(_g.glob(os.path.join(root, "*.py"))):
        src = open(p, encoding="utf-8").read()
        if CFBD_HOST not in src or os.path.basename(p) in ("cfb.py",
                                                           "cfbd_budget.py",
                                                           "cfbd_watch.py"):
            continue
        m = re.search(r"(?m)^SEASONS\s*=\s*\(([^)]*)\)", src)
        seasons = len([x for x in m.group(1).split(",") if x.strip()]) if m else 1
        out[os.path.basename(p)] = seasons
    return out


def other_workflow_calls(root=ROOT):
    """Weekly CFBD calls made by workflows OTHER than collect.yml."""
    per_run = cfbd_scripts(root)
    weekly = collections.Counter()
    for wf in sorted(_g.glob(os.path.join(root, ".github/workflows/*.yml"))):
        if os.path.basename(wf) == "collect.yml":
            continue
        text = open(wf, encoding="utf-8").read()
        hit = [s for s in per_run if re.search(r"%s\s+lines" % re.escape(s), text)]
        if not hit:
            continue
        fires = sum(fires_per_week(c) for c in
                    re.findall(r"(?m)^\s*-\s*cron:\s*[\"']([^\"']+)[\"']", text))
        for s in hit:
            weekly["%s (%s)" % (os.path.basename(wf), s)] += fires * per_run[s]
    return weekly


def weekly_by_mode(weeks=None, root=ROOT):
    """{mode: CFBD calls a week} for collect.yml's routes. ⛔ Derived, never
    typed — the same computation `main()` prints, split out so the price
    check below reserves exactly what the report says is scheduled."""
    weeks = int(os.environ.get("CFBD_WEEKS_PLAYED", "3")) if weeks is None else weeks
    per = calls_per_build(weeks)
    wf = open(os.path.join(root, ".github/workflows/collect.yml"),
              encoding="utf-8").read()
    weekly = collections.Counter()
    for cron, league, modes in parse_routes(wf):
        if "ncaaf" not in league.split():
            continue
        for mode in modes.split():
            if mode in per:
                weekly[mode] += fires_per_week(cron) * per[mode]
    return weekly, per


# ══════════════════════════════════════════════════════════════════════
# 💰 EVERY NEW CFBD PULL IS PRICED BEFORE IT IS MADE. `[Sam, 2026-09-23]`
# ══════════════════════════════════════════════════════════════════════
# "No paid tiers and no new spend. Have cfbd_budget.py price every CFBD
# call before it is made."
# ⛔ THE PRICE IS A CEILING, READ OFF THE CODE. `plays_sweep_max()` reads
#    the week range out of `cfb.build_pace` — the same regex
#    `calls_per_build` uses — and assumes NO early stop, so the price can
#    only overstate what the sweep spends.
# ⛔ AND THE RESERVE IS THE SCHEDULE. A pull is allowed only if, after its
#    ceiling, CFBD's own remaining-calls header still covers ONE FULL WEEK
#    of every scheduled CFBD call. A one-off must never be what makes the
#    daily builders run dry.
# ⛔ NO READING IS NO PERMISSION. If the header was never seen, the answer
#    is REFUSED — an unknown allowance is not a large one.
def plays_sweep_max(root=ROOT):
    """Ceiling on one `/plays` sweep of a season: both season types, every
    week in `build_pace`'s range, no early stop."""
    src = open(os.path.join(root, "cfb.py"), encoding="utf-8").read()
    m = re.search(r"def build_pace.*?for wk in range\((\d+),\s*(\d+)\)", src, re.S)
    lo, hi = (int(m.group(1)), int(m.group(2))) if m else (1, 17)
    return 2 * (hi - lo)


def remaining_calls(latest):
    """CFBD's own `X-CallLimit-Remaining`, from the committed reading."""
    import json as _json
    try:
        with open(os.path.join(latest, "cfbd-quota.json"), encoding="utf-8") as fh:
            h = (((_json.load(fh) or {}).get("quota") or {}).get("headers") or {})
    except (OSError, ValueError):
        return None
    for k, v in h.items():
        if k.lower() == "x-calllimit-remaining":
            try:
                return int(v)
            except (TypeError, ValueError):
                return None
    return None


def preflight(calls, purpose, latest, root=ROOT):
    """-> {"allowed", "calls", "remaining", "reserve", "why"}. No call made."""
    weekly, _per = weekly_by_mode(root=root)
    reserve = sum(weekly.values()) + sum(other_workflow_calls(root).values())
    left = remaining_calls(latest)
    out = {"purpose": purpose, "calls": int(calls), "remaining": left,
           "reserve_one_week": int(reserve), "allowed": False}
    if left is None:
        out["why"] = ("no CFBD remaining-calls reading on disk — an unknown "
                      "allowance is never permission")
    elif calls + reserve > left:
        out["why"] = ("%d call(s) + a week of scheduled pulls (%d) exceeds "
                      "the %d CFBD says remain" % (calls, reserve, left))
    else:
        out["allowed"] = True
        out["why"] = ("%d call(s) at most; %d remain; %d stay reserved for a "
                      "week of scheduled pulls" % (calls, left, reserve))
    return out


def main():
    retries = 1
    for i, a in enumerate(sys.argv):
        if a == "--retries" and i + 1 < len(sys.argv):
            retries = int(sys.argv[i + 1])
    weekly, per = weekly_by_mode()
    weeks = int(os.environ.get("CFBD_WEEKS_PLAYED", "3"))

    print("CFBD CALL BUDGET — derived from the deployed workflow and cfb.py")
    print(f"  assuming {weeks} played week(s); "
          f"build_pace early-stop: "
          f"{'ON (32 -> %d calls)' % per['cfb-probe'] if per['_early_stop'] else '🔴 OFF — a flat 32 calls per rebuild'}")
    print()
    print(f"  {'mode':12} {'calls/build':>12} {'builds/wk':>10} {'calls/wk':>10}")
    for mode in sorted(weekly):
        builds = weekly[mode] // per[mode]
        print(f"  {mode:12} {per[mode]:12} {builds:10} {weekly[mode]:10}")
    other = other_workflow_calls()
    for name, n in sorted(other.items()):
        print(f"  {name:12} {'':12} {'':10} {n:10}   (outside collect.yml)")
    wk = sum(weekly.values()) + sum(other.values())
    month = round(wk * 52 / 12)
    print(f"  {'':12} {'':12} {'':10} {wk:10}  = {month}/month")

    if retries > 1:
        print(f"\n  ⚠️ AT {retries} ATTEMPTS/DAY (converge retrying a failing "
              f"source — what actually happened):")
        rmonth = round(month * retries)
        print(f"     ~{rmonth}/month")
        month = rmonth

    print()
    worst = None
    for name, lim in TIERS:
        pct = 100.0 * month / lim
        flag = "✅" if pct < 80 else ("⚠️" if pct < 100 else "🔴 OVER")
        print(f"  {name:18} {lim:6}/mo   {pct:5.0f}%  {flag}")
        if name == "Free":
            worst = pct
    print()
    # ══════════════════════════════════════════════════════════════════
    # 🔴🔴 WHAT CFBD ITSELF SAID, AND WHETHER IT CONTRADICTS THE PLAN.
    # ══════════════════════════════════════════════════════════════════
    # ⚠️ INJECTABLE FOR TESTS ONLY — the default is the real tree. A
    #    contradiction check that can only be driven against live data is
    #    one that goes red for reasons nobody caused.
    _m = measured_plan(os.environ.get(
        "CFBD_DATA", os.path.join(ROOT, "data", "ncaaf")))
    if _m["readings"]:
        print("  MEASURED, from CFBD's own header (%d reading(s), %s → %s):"
              % (_m["readings"], (_m["first"] or "?")[:10],
                 (_m["last"] or "?")[:10]))
        print("    highest remaining ever seen   %s" % _m["max_remaining"])
        print("    plan floor from a reset       %s   (%s)"
              % (_m["floor"] if _m["floor"] else "UNKNOWN", _m["why"]))
        # 🔴 THE CHECK THAT WOULD HAVE CAUGHT THE `1000` DEFAULT WITHOUT
        #    ANYONE BEING ASKED. You cannot have more calls left than the
        #    plan holds, so a reading above `PLAN` PROVES `PLAN` wrong.
        #    `[2,236 remaining sat in a probe artifact for the whole of
        #    September while the tier was asked for five times.]`
        if (_m["max_remaining"] or 0) > PLAN:
            print()
            print("🔴 THE CONFIGURED PLAN IS WRONG. CFBD reported %d calls "
                  "REMAINING, which a %d plan cannot hold. ⛔ Set CFBD_PLAN "
                  "to the real tier — the percentage below is meaningless "
                  "until you do." % (_m["max_remaining"], PLAN))
        print()
    else:
        print("  MEASURED: no quota reading on disk yet. ⚠️ `cfb.py` records "
              "one on every run that can call CFBD; this fills in by "
              "itself.")
        print()
    pct = 100.0 * month / PLAN
    if pct >= 100:
        print(f"🔴 {month}/month against a {PLAN} plan — {pct:.0f}%. "
              f"⛔ THE QUOTA WILL RUN OUT MID-MONTH AND EVERY CFBD MODE "
              f"WILL 429 UNTIL THE 1st.")
        return 1
    if pct >= 80:
        print(f"⚠️ {month}/month against a {PLAN} plan — {pct:.0f}%. "
              f"Little headroom for a retry storm.")
        return 0
    print(f"✅ {month}/month against a {PLAN} plan — {pct:.0f}%.")
    print("⚠️ THIS IS A FLOOR. It prices ONE attempt per scheduled build. "
          "Converge retries are what blew the quota in September — "
          "run `--retries 7` to price what actually happened.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
