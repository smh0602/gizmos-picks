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
balance, and a reset (the one thing that raises it) is always a later
minute. ~~the monthly reset~~ `[2026-10-23]` A reset is the 1st of the month
OR a plan bought again mid-month (`periods`). ⛔ Stdlib only, and it never
imports collect.py: the paid kinds are handed in (collect.PAID_KINDS is the
one registry).
"""
import ast
import glob
import gzip
import json
import os
import re
import subprocess
import sys


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
        rows.append((key + (f,), (j.get("pulled_at"), j.get("credits_remaining"), f)))
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


def periods(rows):
    """The readings split into QUOTA PERIODS, oldest first, each in chain
    order (the minute pulled, then the LOWER balance). Only integer balances.

    🔴 `[2026-10-23]` A NEW PERIOD STARTS WHEREVER THE BALANCE RISES. Spend
    only lowers it, so a rise is a reset: the 1st of the month, and a plan
    bought again mid-month. Sam's plan lapsed on 10-22 and was bought back:
    11,800 left at 10-22 19:32Z, 19,989 at 10-23 17:27Z. The watchdog grouped
    readings by calendar month and reported ~7,900 credits "unrecorded".
    ⚠️ Measured over the 945 stored readings from 08-22 to 10-23: the chain
    rises exactly three times (09-01, 10-01 and that re-subscription), so no
    interleaving of two runs has ever raised it."""
    have = sorted((r for r in rows if isinstance(r[1], int) and r[0]),
                  key=lambda r: (str(r[0])[:16], -r[1]))
    out = []
    for r in have:
        if not out or r[1] > out[-1][-1][1]:
            out.append([])
        out[-1].append(r)
    return out


def spent_nothing(path):
    """True when a paid snapshot records that the run bought NOTHING:
    `credits_used` is an explicit 0 and no balance header was read.
    `[2026-09-30]` alt-lines writes such a file when every game is held or
    out of window (data/ncaaf/2026-09-29/alt-lines/2344), and the watchdog
    called the balance STALE against it: no credit was spent, so there is
    nothing the held balance fails to reflect. ⚠️ Anything unreadable, or a
    file that does not say 0, is treated as a real pull (stale stays loud)."""
    try:
        j = json.load(gzip.open(path, "rt"))
    except Exception:
        return False
    if not isinstance(j, dict):
        return False
    used = j.get("credits_used")
    return (used == 0 and not isinstance(used, bool)
            and not isinstance(j.get("credits_remaining"), int))


def paid_kinds(src_dir):
    """`collect.PAID_KINDS`, READ from `src_dir`/collect.py's source -- never
    imported, never copied. `[2026-10-23]` Moved here from watchdog.py, so the
    landing step (push_retry.sh -> `keep-both` below) reads the same list the
    watchdog does. None when unreadable."""
    try:
        src = open(os.path.join(src_dir, "collect.py"), encoding="utf-8").read()
        for n in ast.parse(src).body:
            if (isinstance(n, ast.Assign) and len(n.targets) == 1
                    and getattr(n.targets[0], "id", "") == "PAID_KINDS"):
                kinds = tuple(ast.literal_eval(n.value))
                return kinds or None
    except (OSError, SyntaxError, ValueError):
        pass
    return None


def keep_both(tip, kinds, cwd=None):
    """🔴 LANDING NEVER REPLACES A PAID SNAPSHOT ANOTHER RUN ALREADY LANDED.

    `[measured 2026-10-23]` Two collect runs queued through a 19-hour key
    outage started together and both bought NFL gamelines + props at 17:28Z
    (6 + 144 credits each). Both wrote `data/nfl/2026-10-23/<kind>/1728.json.gz`;
    push_retry.sh's `rebase -X theirs` kept the second run's file, so the
    first run's receipt and its 150 credits left main's tip (the watchdog
    reported them unrecorded). Main's history holds two more: 10-11 19:19Z
    (ncaaf gamelines, 6 credits) and 08-23 01:15Z (props-batter, 65).
    `_paid_free_name` already keeps two same-minute pulls of ONE run apart;
    only the landing sees two runs.

    ✅ For every paid snapshot that HEAD would change on `tip` (the commit
    this push lands on): `tip`'s file stays at its name, and this run's copy
    moves to the next `HHMM-n` name free in both trees (`snapshot_re` reads
    it). Folded into HEAD's commit, so nothing else in the index moves.
    -> [(path, kept_as)]. ⛔ Only renames this run's copy; never another path,
    never a deletion, never a file that is not a paid snapshot.
    """
    rx = snapshot_re(kinds)

    def git(*args):
        return subprocess.run(("git",) + args, cwd=cwd, check=True,
                              capture_output=True).stdout

    def held(rev, path):
        return subprocess.run(("git", "cat-file", "-e", f"{rev}:{path}"),
                              cwd=cwd, capture_output=True).returncode == 0

    top = git("rev-parse", "--show-toplevel").decode().strip()
    cwd = top
    out = git("diff", "--name-status", "--no-renames", "-z", tip, "HEAD")
    parts = out.decode("utf-8").split("\0")
    kept, taken = [], set()
    for st, path in zip(parts[0::2], parts[1::2]):
        m = rx.search(path)
        if st != "M" or not m:
            continue
        stem = path[:m.start(3)] + m.group(3)
        n = 1
        while (f"{stem}-{n}.json.gz" in taken or held(tip, f"{stem}-{n}.json.gz")
               or held("HEAD", f"{stem}-{n}.json.gz")):
            n += 1
        free = f"{stem}-{n}.json.gz"
        taken.add(free)
        mine, theirs = git("cat-file", "blob", f"HEAD:{path}"), git("cat-file", "blob", f"{tip}:{path}")
        for rel, blob in ((free, mine), (path, theirs)):
            with open(os.path.join(top, rel), "wb") as fh:
                fh.write(blob)
        kept.append((path, free))
    if kept:
        paths = [p for pair in kept for p in pair]
        git("add", "--", *paths)
        git("commit", "-q", "--amend", "--no-edit", "--only", "--", *paths)
    return kept


if __name__ == "__main__":
    # `python credits.py keep-both <tip>`: push_retry.sh's landing step.
    # ⛔ Exit 1 when the registry cannot be read: the caller warns, never guesses.
    if len(sys.argv) == 3 and sys.argv[1] == "keep-both":
        _kinds = paid_kinds(os.path.dirname(os.path.abspath(__file__)))
        if not _kinds:
            print("no `PAID_KINDS = (...)` tuple was found in collect.py")
            sys.exit(1)
        for _path, _free in keep_both(sys.argv[2], _kinds):
            print(f"{_path} was already on the remote (another run's paid "
                  f"pull): this run's copy is kept beside it as "
                  f"{os.path.basename(_free)}, never over it")
        sys.exit(0)
    print("usage: credits.py keep-both <tip>")
    sys.exit(2)
