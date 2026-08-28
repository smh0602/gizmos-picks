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

import sys
import freshness as F

# ⛔ ONE DEFINITION, in freshness.py — the gate and the collector must
# never disagree about what may be lost.
from freshness import SOFT


def main():
    rows = F.survey()
    hard, soft = [], []
    for r in rows:
        if not r["stale"]:
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
