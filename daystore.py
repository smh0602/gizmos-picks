#!/usr/bin/env python3
"""daystore.py — THE ONE DATED, WRITE-ONCE ARCHIVE WRITER.

    from daystore import archive

⚠️ WHY IT IS A MODULE AND NOT A COPY. `dossier_fb.py` grew this logic on
2026-09-17 and `shadow_fb.py` needs exactly it the next day. ⛔ A helper
duplicated is a helper that breaks in the file you did not edit — this
repo has paid for that with five copies of the workflow routing regex and
fifteen of `eq()` (ledger rule 117).

══════════════════════════════════════════════════════════════════════
💾 DATED AND WRITE-ONCE, NOT ONE CUMULATIVE FILE, AND THE REASON IS
MEASURED (ledger rule 285): ⛔ GIT CANNOT DELTA-COMPRESS A GZIP.

A one-row input change rewrites essentially the whole output, so
consecutive versions share no usable delta and git stores each IN FULL.
At 34 b/row gzipped and ~8,000 rows a week that is 5.17 MiB for a 20-week
season written this way, against 2,896 MiB for one cumulative archive
rewritten eight times a day. **560x.**

⛔ WRITE-ONCE. An archive a later run can rewrite is not an archive; it
is `latest/` with a longer name. Two runs inside one minute leave the
first one's reading alone — and every one of these files is a
POINT-IN-TIME reading, which is the whole reason to keep it: the market's
numbers move, a season-to-date row grows, a section flips from
UNAVAILABLE to OK. A report with no archive cannot be checked against
what actually happened.

⚠️ THE DATE IS UTC, DELIBERATELY. `data/<lg>/<date>/` is written by the
collector's `daydir()`, which stamps UTC — `picks/` is the tree that is
ET-dated. ⛔ Two date conventions inside one directory is a trap, so this
follows the neighbours it lands beside, not `picks/`.

⛔ AND IT NEVER WRITES INTO `picks/`. Those are a permanent published
record of what was advertised; a report about them is not one of them.
══════════════════════════════════════════════════════════════════════
"""
import datetime
import gzip
import json
import os

# ⛔ THE ONE DIRECTORY THIS REFUSES. `picks/` is append-only-once-a-slate-
#    starts, and a reporting tool has no business inside it.
FORBIDDEN = ("picks",)


def stamp(when=None):
    """(YYYY-MM-DD, HHMM) in UTC. ⚠️ Injectable for tests ONLY."""
    n = when or datetime.datetime.now(datetime.timezone.utc)
    return n.strftime("%Y-%m-%d"), n.strftime("%H%M")


def path(data, kind, when=None):
    """`<data>/<UTC date>/<kind>/<HHMM>.json.gz` — the shape, no writing."""
    day, hhmm = stamp(when)
    return os.path.join(data, day, kind, hhmm + ".json.gz")


def archive(doc, data, kind, log=print, when=None):
    """Write `doc` to a dated path unless one is already there.

    -> (path, wrote?) — `wrote` False means an earlier reading from this
    same minute was LEFT ALONE, which is the point of the whole module.
    """
    p = path(data, kind, when)
    parts = os.path.normpath(p).split(os.sep)
    if any(x in FORBIDDEN for x in parts):
        # ⛔ REFUSE, never "helpfully" relocate. A tool that silently
        #    writes somewhere else is a tool nobody can audit.
        raise ValueError("daystore refuses to write under %s: %s"
                         % ("/".join(FORBIDDEN), p))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p):
        log("daystore: %s already exists — left as it was" % p)
        return p, False
    with gzip.open(p, "wt") as fh:
        json.dump(doc, fh)
    return p, True
