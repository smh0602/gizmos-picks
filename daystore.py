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


def same_bytes(path, doc):
    """The bytes of the gzip at `path` when it stores `doc` apart from its stamps
    (freshness.same_but_stamps, the heartbeat's own compare: as JSON stores it, so int
    keys read back as strings); None otherwise (no file, unreadable, any other
    difference, at any depth). ⛔ Never raises.
    🔴 `[2026-11-10]` ~~exactly `doc`~~ APART FROM ITS STAMPS. The latest file is written
    by `collect.write`, which adds `written_at`, and a run whose document moved only its
    stamps keeps the latest gzip and writes its heartbeat: compared exactly, the archive
    would dump a second full gzip on every such run (the copy exists to stop that). The
    archive then carries latest's file stamps; its own time is its dated path, and no
    reader takes a stamp from an archive (shadow_fb reads `dossiers`)."""
    try:
        import freshness as _F
        with open(path, "rb") as fh:
            buf = fh.read()
        stored = json.loads(gzip.decompress(buf).decode("utf-8"))
        if stored == json.loads(json.dumps(doc)) or (
                isinstance(stored, dict) and isinstance(doc, dict) and _F.same_but_stamps(stored, doc)):
            return buf
    except Exception:
        pass
    return None


def archive(doc, data, kind, log=print, when=None, same_as=None):
    """Write `doc` to a dated path unless one is already there.

    -> (path, wrote?) — `wrote` False means an earlier reading from this
    same minute was LEFT ALONE, which is the point of the whole module.

    🔴 `same_as` `[2026-11-08]`: the `latest/` gzip the caller has just written
    `doc` to. When that file stores exactly `doc`, the archive is a copy of its
    BYTES, so git stores one blob for the two paths. ⛔ A gzip carries its own
    write time and temporary file name, so the same document dumped twice is two
    different blobs: the dossier archive was a second full copy of
    `latest/dossiers.json.gz` on every `card-fb` run (267 archives, 63.8 MB of
    new gzip from 2026-10-25 to 11-08, every one sampled equal in content to the
    latest file of its commit). Any difference, and it dumps `doc` as before.
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
    buf = same_bytes(same_as, doc) if same_as else None
    if buf is not None:
        with open(p, "wb") as fh:          # the write-once check is the one above, as for a dump
            fh.write(buf)
        return p, True
    with gzip.open(p, "wt") as fh:
        json.dump(doc, fh)
    return p, True
