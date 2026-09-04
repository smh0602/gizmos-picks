"""THE FRESHNESS GATE — fail the run when the site is not current.

🔴 WHY THIS IS A VERIFIER AND NOT A LOG LINE.

`[measured 2026-08-28]` the dashboard served 15-hour-old player props,
a card priced off the previous night's odds, and a track record with three
ungraded slates in it — and NOTHING ANYWHERE SAID SO. Every Actions run
was green, because every run did the one job its cron was named after.
The site was broken and the machine reported success.

⛔ A STALE SITE THAT LOOKS CURRENT IS THE PRODUCT FAILURE. It is worse
than an outage: an outage is visible, and a confidently wrong number is
not. With real users this is the thing that burns you, because they act
on it.

➡️ So staleness is now a FAILING CHECK, exactly like a bad card. It runs
after every converge pass, and the run goes red while the data that WAS
collected stays committed.

⚠️ It is deliberately NOT a blocker before the commit: half-fresh data is
worth more than none, and the freshest thing available is what the page
should show. This turns the run red so it is visible, and leaves the
snapshot in place.
"""

import os
import sys
import freshness as F

# ⛔ ONE DEFINITION, in freshness.py — the gate and the collector must
# never disagree about what may be lost.
from freshness import SOFT


# 🔴 THE GATE READS THE LEAGUE, AND UNTIL 2026-09-04 IT DID NOT.
# `F.survey()` with no arguments is MLB, always. While the workflow ran
# this for MLB only that was harmless; **switching the gate on for
# football without this line would have graded college artifacts against
# BASEBALL's deadlines** -- the exact hazard the workflow warned about on
# 2026-08-28, arriving by the other door.
# ⛔ ONE MAPPING, and it is the same shape `collect.py`'s LEAGUES table
# uses: MLB at the root, every other league in its own subtree.
# ⚠️ `picks` stays at the ROOT for every league, because `card_fb.py`
# writes the football card to `picks/fb-<league>-latest.json`.
_LEAGUE = (os.environ.get("LEAGUE") or "mlb").strip().lower() or "mlb"
_DATA = "data" if _LEAGUE == "mlb" else f"data/{_LEAGUE}"


def main():
    rows = F.survey(data=_DATA, picks="picks")

    # 🔴 A REFUSED CARD IS A KNOWN STATE, NOT AN UNKNOWN FAILURE.
    # `[measured 2026-08-29]` `verify_card` blocked the card on T37 and
    # every converge pass afterwards went red — **22 consecutive red runs
    # for a decision that had already been made and recorded.**
    # ⛔ AN ALARM THAT FIRES EVERY FIFTEEN MINUTES GETS IGNORED, AND
    # IGNORING RED IS EXACTLY HOW THE ORIGINAL STALENESS SURVIVED A WHOLE
    # DAY. Sam had to notice the site was wrong and ask.
    # ✅ THE GATE'S JOB IS TO CATCH STALENESS NOBODY KNOWS ABOUT. When the
    # card is late *because it was refused*, the reason is written to
    # `card-verify-failure.txt`, published in `freshness.json`, and shown
    # on the page in plain words. That is the opposite of unknown.
    # ⚠️ NARROW ON PURPOSE — it downgrades ONLY the card, ONLY while the
    # failure file exists. A card late for ANY OTHER reason still fails,
    # and so does every other artifact.
    refused = os.path.exists(f"{_DATA}/latest/card-verify-failure.txt")

    hard, soft = [], []
    for r in rows:
        if not r["stale"]:
            continue
        if r["mode"] == "card" and refused:
            soft.append(r)
            continue
        (soft if r["mode"] in SOFT else hard).append(r)

    print("=" * 70)
    print("FRESHNESS GATE")
    for r in rows:
        age = "MISSING" if r["missing"] else f"{r['age_min']:.0f}m"
        mark = "STALE" if r["stale"] else " ok  "
        late = "" if not r["late_min"] else f"  {r['late_min']:.0f}m LATE"
        print(f"  {mark}  {r['mode']:<14} {age:>9}  due {r['due_et']:<14}"
              f"{late}   {r['why']}")
    print("=" * 70)

    if refused and any(r["mode"] == "card" for r in soft):
        try:
            with open(f"{_DATA}/latest/card-verify-failure.txt",
                      encoding="utf-8") as fh:
                why = [l for l in fh if l.startswith("FAILURES:")]
            why = why[0][9:].strip() if why else "see card-verify-failure.txt"
        except Exception:
            why = "see card-verify-failure.txt"
        print(f"::warning::the card was REFUSED, not merely late — {why}")
        print( "::warning::the page says so on its face; this is a known "
               "state and does not fail the run")

    for r in soft:
        print(f"::warning::{r['mode']} has missed its {r['due_et']} build "
              f"({'never built' if r['missing'] else 'last built ' + str(int(r['age_min'])) + 'm ago'})"
              f" — soft, not failing the run")

    if not hard:
        print("PASS — everything the page depends on is inside contract")
        return 0

    for r in hard:
        age = "never built" if r["missing"] else f"last built {int(r['age_min'])}m ago"
        late = f", {int(r['late_min'])}m past due" if r["late_min"] else ""
        print(f"::error::{r['mode']} MISSED its {r['due_et']} ET build: "
              f"{age}{late} — {r['why']}")
    print(f"FAIL — {len(hard)} artifact(s) past due")
    return 1


if __name__ == "__main__":
    sys.exit(main())
