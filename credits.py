#!/usr/bin/env python3
"""THE CREDIT BALANCE CHAIN -- one reader, for collect.py and watchdog.py.

Every paid Odds API snapshot stores the API's own `credits_remaining`.
`[2026-09-29]` Two things read that balance and neither read it right:
  - watchdog picked the newest FILE NAME, so two paid pulls in one minute
    tied on the path and props-pitcher/1113 (3,848) was reported while
    props-batter/1113 (3,808) was the newer reading;
  - collect.py's daily allowance summed the snapshots it could see, which
    ran 2,918 credits light of the API's own balance by 2026-09-26.
✅ One rule, here: readings are ordered by the MINUTE they were pulled, and
within a minute the LOWER balance is the newer one -- spend only lowers the
balance, and the monthly reset (the one thing that raises it) is always a
later minute. ⛔ Stdlib only, and it never imports collect.py: the paid
kinds are handed in (collect.PAID_KINDS is the one registry).
"""
import glob
import gzip
import json
import os
import re


def snapshot_re(kinds):
    """A stored PAID snapshot: `<date>/<kind>/<HHMM>[-n].json.gz` for a
    registered kind. The `-n` is a second paid write in the same minute,
    which collect.write() files beside the first instead of over it."""
    return re.compile(r"(\d{4}-\d{2}-\d{2})/(%s)/(\d{4})((?:-\d+)?)\.json\.gz$"
                      % "|".join(re.escape(k) for k in kinds))


def readings(data, kinds):
    """-> [(pulled_at, credits_remaining, path)] for every paid snapshot under
    `data` (every league's directory beneath it), NEWEST PATH FIRST.
    ⛔ Read-only, zero spend. An unreadable file is skipped, never a 0."""
    if not kinds:
        return []
    rx = snapshot_re(kinds)
    rows = []
    for f in glob.glob(os.path.join(data, "**", "*.json.gz"), recursive=True):
        m = rx.search(f.replace(os.sep, "/"))
        if not m:
            continue
        try:
            j = json.load(gzip.open(f, "rt"))
        except Exception:
            continue
        if not isinstance(j, dict):
            continue
        key = (m.group(1), m.group(3), int(m.group(4)[1:] or 0))
        rows.append((key, (j.get("pulled_at"), j.get("credits_remaining"), f)))
    rows.sort(key=lambda r: r[0], reverse=True)
    return [r for _k, r in rows]


def newest(rows):
    """The newest balance reading BY THE CHAIN, or None.

    `rows`: (pulled_at, credits_remaining, path). Only integer balances
    count. Ordered by the minute pulled, then by the LOWER balance."""
    have = [r for r in rows if isinstance(r[1], int) and r[0]]
    if not have:
        return None
    return max(have, key=lambda r: (str(r[0])[:16], -r[1]))
