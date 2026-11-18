#!/usr/bin/env python3
"""fb_history.py — OLDER FOOTBALL SEASONS FOR T70's H / HC (research/fb_refit_spec.md §3d).

`[Sam, 2026-10-15]` "do all changes": the NFL game model learns from about 361
games (2025-26) and college from about 1,040. This stores earlier seasons, once,
for the challengers that train on them:

    NFL 2018-2024      data/nfl/history/schedule-<season>.json.gz   (nflverse, free)
    college 2023-2024  data/ncaaf/history/schedule-<season>.json.gz (CFBD /games)
                       data/ncaaf/history/lines-<season>.json.gz    (CFBD /lines)

⛔ NEVER INTO `latest/`: the champion rates teams from every schedule there, so a
history file there would change the live model without a test. ⛔ Written once
while missing by the daily runs (`nfl-logs`, `cfb-probe`); every CFBD call
priced first by `cfbd_budget.preflight`; a refusal fetches and writes nothing.
⛔ Never raises. Stdlib only.

`[2026-11-17]` A STORED FILE THAT CANNOT BE READ IS REBUILT, NOT SKIPPED. The old reader
caught only OSError / ValueError: a truncated gzip raised EOFError out of every reader,
and a bad-JSON file read as None while its writer saw a file and moved on, so neither
was ever rebuilt (and with HC the college champion, either one crashed its build or
trained it on one season of two). ✅ `_stored` is the one reader: present (a dict with
games of its kind's shape, `freshness.history_problem`, the same test the contract's
HEALTH asks), missing or corrupt. A corrupt file is rebuilt by the same path as a missing
one, and only once the new one is in hand is the old one moved to
`history/corrupt/<name>.<UTC time>`: never deleted, never read (no reader looks in that
folder, and the name no longer ends in .json.gz). A readable file with no stamp the
contract reads is stamped in place, in BOTH leagues, at no call. ~~A missing or corrupt
file a run could not land~~ `[review, 2026-11-17]` Every file the contract still reads
stale when a run ends, whatever the run did or skipped (`_landed`, asked of the contract
itself), is named in `history/rebuild-attempts.json` (`ATTEMPTS`), which
`freshness.rebuild_held` reads: a CHAMPION's file is retried by its writer's own next
deadline run, never by an extra one (each `cfb-probe` is a CFBD sweep).
"""
import datetime
import glob
import gzip
import json
import os
import zlib

import freshness as _F       # stdlib only: the contract's own stamp reader

ROOT = os.path.dirname(os.path.abspath(__file__))
NFL_SEASONS = (2018, 2019, 2020, 2021, 2022, 2023, 2024)     # ⛔ §3d
CFB_SEASONS = (2023, 2024)                                   # ⛔ §3d
ALIAS = {"OAK": "LV"}                                        # ⛔ §3d: Oakland became Las Vegas in 2020
CORRUPT_DIR = "corrupt"          # history/corrupt/: an unreadable file, moved aside, never read
ATTEMPTS = _F.REBUILD_ATTEMPTS   # history/rebuild-attempts.json: the files a run could not land


def log(m):
    print(m, flush=True)


def hdir(lg, root=None):
    return os.path.join(root or ROOT, "data", lg, "history")


def _stored(p):
    """-> (doc, state, why): THE ONE READER of a stored history file. `state` is "present" (a
    dict whose `games` freshness.history_problem accepts: a schedule's a non-empty list, lines' a
    non-empty dict), "missing" or "corrupt" (`why`: the error's name, or history_problem's
    reason). ⛔ Never raises: a truncated gzip (EOFError), a damaged stream (zlib.error), a
    bad header (OSError) or bad JSON or text (ValueError) is corrupt, never a crash.
    ⛔ Its content test is the contract's own (one copy, `[review, 2026-11-17]`): with two, a
    stamped file with no games was corrupt here and fresh to the contract, so HC failed on it
    and nothing planned its repair."""
    if not os.path.exists(p):
        return None, "missing", None
    try:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (EOFError, zlib.error, OSError, ValueError) as e:
        return None, "corrupt", type(e).__name__
    bad = _F.history_problem(p, doc)
    if bad:
        return None, "corrupt", bad
    return doc, "present", None


def _landed(p):
    """Does the CONTRACT read the file at `p` as current now: a stamp it reads (`stamp_of`) and
    no health finding (`health`, history_problem for these files)? A history row has no deadline,
    so that is the whole of its row's verdict. The writers' post-condition (`_record_attempts`)."""
    return _F.stamp_of(p) is not None and _F.health(p) is None


def _stamp_once(p, doc):
    """A readable stored file the contract reads no stamp in (its own reader, so one list of stamp
    fields) is stamped once, its games untouched, at no call. -> the outcome, or None when it has
    one. `[2026-10-27]` NFL's (unstamped, its seven schedules read MISSING 10-16 -> 10-27);
    `[review, 2026-11-17]` college's too (rule 6): an unstamped HC file read MISSING, so it was
    owed on every pass, while store_cfb saw a file and spent nothing on it, and planned a CFBD
    sweep an hour for ever."""
    if _F.stamp_of(p) is not None:
        return None
    _write(p, doc)
    return "stamped (%d games)" % len(doc["games"])


def state_of(p):
    """"present", "missing" or "corrupt: <why>" (fb_challengers.need_history names it)."""
    _doc, state, why = _stored(p)
    return state if why is None else "%s: %s" % (state, why)


def _aside(p):
    """Move an unreadable stored file to history/corrupt/<name>.<UTC time>; -> where.
    ⛔ Never deleted (rule 13: deleting data is Sam's) and never read again."""
    d = os.path.join(os.path.dirname(p), CORRUPT_DIR)
    os.makedirs(d, exist_ok=True)
    base = os.path.join(d, "%s.%s" % (os.path.basename(p),
                                      datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")))
    dst, n = base, 1
    while os.path.exists(dst):
        n += 1
        dst = "%s-%d" % (base, n)
    os.replace(p, dst)
    return dst


def _record_attempts(lg, root, ends):
    """`ends`: {file name: (path, this run's outcome, or None for none)} for EVERY file the writer
    owns. THE WRITER'S POST-CONDITION, asked of the contract itself (`_landed`): a file the contract
    reads as current leaves ATTEMPTS; one it still reads stale, whatever this run did or skipped
    (refused, failed, no games, or a "present" file the contract cannot stamp), is kept with this
    run's time, so `freshness.rebuild_held` holds its row until its writer's own next deadline,
    never every pass. `[review, 2026-11-17]` ~~only the missing or corrupt files it tried, by their
    outcome's words~~: an unstamped college file was "present", never tried, never held, and owed
    on every pass. Written only when it changes. ⛔ Never raises."""
    p = os.path.join(hdir(lg, root), ATTEMPTS)
    try:
        with open(p, encoding="utf-8") as fh:
            have = json.load(fh).get("files") or {}
    except (OSError, ValueError, AttributeError):
        have = {}
    files = dict(have)
    for name, (path, outcome) in ends.items():
        if _landed(path):
            files.pop(name, None)
        else:
            files[name] = {"tried_at": _stamp(), "outcome": str(
                outcome or "unchanged: the contract still reads it stale (%s)" % state_of(path))[:300]}
    if files == have:
        return
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p + ".tmp", "w", encoding="utf-8") as fh:
            json.dump({"kind": "DESCRIPTIVE", "league": lg, "written_at": _stamp(), "files": files},
                      fh, indent=1, sort_keys=True)
        os.replace(p + ".tmp", p)
    except OSError:
        try:
            os.remove(p + ".tmp")
        except OSError:
            pass


def _stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(p, doc):
    """`[2026-10-27]` Every file carries `written_at`: the NFL schedules were written with no
    stamp, so the contract read all seven as MISSING from 10-16 on, and health.json carried
    a standing `fresh:nfl` DEGRADED that a real NFL staleness would have hidden under.
    ⛔ Atomic (a temporary file, then `os.replace`): a stored season is now rewritten in
    place, and a write cut short would leave a file that never rebuilds `[review]`."""
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    try:
        with gzip.open(tmp, "wt", encoding="utf-8") as fh:
            json.dump(dict(doc, written_at=_stamp()), fh, separators=(",", ":"))
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def alias(doc):
    """The schedule with every relocated team under its current code."""
    for g in (doc or {}).get("games") or []:
        for k in ("home", "away"):
            g[k] = ALIAS.get(g.get(k), g.get(k))
    return doc


def store_nfl(log=log, root=None, build=None):
    """Each missing or unreadable NFL history season, from nflverse (free). `build(season) -> doc`
    (tests plant one). -> {season: outcome}. ⛔ Never raises."""
    out, rows, ends = {}, None, {}
    for s in NFL_SEASONS:
        p = os.path.join(hdir("nfl", root), "schedule-%d.json.gz" % s)
        doc, state, why = _stored(p)
        try:
            if state == "present":               # NFL: a readable file is never rebuilt
                got = _stamp_once(p, doc)        # `[2026-10-27]` ...only stamped, when it has none
                if got:
                    out[s] = got
                    log("  history nfl %d: %s" % (s, out[s]))
                continue
            if build is None:
                import nfl as _nfl
                if rows is None:
                    # ⛔ its own name: `[review, 2026-11-17]` reusing the end-of-run record's name
                    #    made this table the record, and the real nflverse path raised out of store_nfl
                    rel = {r["tag_name"]: [(a["name"], a["size"], a["browser_download_url"])
                                           for a in (r.get("assets") or [])] for r in _nfl._releases(log)}
                    rows = _nfl._rows(rel, "schedules", _nfl.SCHEDULE_FILE, log)
                doc, _rep = _nfl.build_schedule(s, None, log, rows=rows)
            else:
                doc = build(s)
            if not (doc or {}).get("games"):
                out[s] = "not written: no games"
                continue
            doc = alias(dict(doc, kind="DESCRIPTIVE", history=True))
            moved = _aside(p) if state == "corrupt" else None     # NFL: once the new one is in hand
            _write(p, doc)
            out[s] = ("written (%d games)" % len(doc["games"]) if moved is None else
                      "rebuilt (was corrupt: %s; the old file is %s)"
                      % (why, os.path.relpath(moved, hdir("nfl", root)).replace(os.sep, "/")))
        except Exception as e:
            out[s] = "failed: %s: %s" % (type(e).__name__, str(e)[:200])
        finally:
            ends["schedule-%d.json.gz" % s] = (p, out.get(s))
        log("  history nfl %d: %s" % (s, out[s]))
    _record_attempts("nfl", root, ends)
    return out


def pick_lines(data):
    """CFBD /lines rows -> t60r's shape {game id: {spread, total, ml_home, ml_away,
    provider}}, one line per game by t60r.PROVIDER_ORDER (§3d)."""
    import t60r
    out = {}
    for g in data or []:
        best = None
        for ln in g.get("lines") or []:
            if ln.get("spread") is None or ln.get("overUnder") is None:
                continue
            rank = t60r.provider_rank(ln.get("provider"))
            if best is None or rank < best[0]:
                best = (rank, ln)
        if best:
            ln = best[1]
            out[str(g.get("id"))] = {"spread": -float(ln["spread"]), "total": float(ln["overUnder"]),
                                     "ml_home": ln.get("homeMoneyline"), "ml_away": ln.get("awayMoneyline"),
                                     "provider": ln.get("provider")}
    return out


def store_cfb(log=log, root=None):
    """Each missing or unreadable college history season's schedule (2 calls) and lines (1 call),
    every call priced first. -> {file: outcome}. ⛔ Never raises.
    `[2026-11-17]` A present file costs no call (an unstamped one is stamped in place, as
    NFL's); a corrupt one is priced and rebuilt like a missing one, and moved aside only once
    the new one is in hand."""
    out, ends = {}, {}
    try:
        import cfb as _cfb
    except Exception as e:
        return {"import": "failed: %s" % type(e).__name__}
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for s in CFB_SEASONS:
        for kind, calls in (("schedule", 2), ("lines", 1)):
            p = os.path.join(hdir("ncaaf", root), "%s-%d.json.gz" % (kind, s))
            doc0, state, why = _stored(p)
            key = "%s-%d" % (kind, s)
            if state == "present":               # college: a readable file costs no call
                try:
                    got = _stamp_once(p, doc0)   # `[review, 2026-11-17]` ...only stamped, when it has none
                except Exception as e:
                    got = "failed: %s: %s" % (type(e).__name__, str(e)[:200])
                if got:
                    out[key] = got
                    log("  history ncaaf %s: %s" % (key, got))
                ends["%s.json.gz" % key] = (p, out.get(key))
                continue
            try:
                if not _cfb._priced(calls, "history %s %d" % (kind, s), log):
                    out[key] = "refused"
                    continue
                if kind == "schedule":
                    doc, _rep = _cfb.build_schedule(s, log)
                    if not (doc or {}).get("games"):
                        out[key] = "not written: no games"
                        continue
                    doc = dict(doc, history=True)
                else:
                    lines = pick_lines(_cfb.get("/lines", {"year": str(s), "seasonType": "regular"}))
                    if not lines:
                        out[key] = "not written: no lines"
                        continue
                    doc = {"season": s, "kind": "DESCRIPTIVE", "endpoint": "/lines",
                           "built_at": stamp, "games": lines}
                moved = _aside(p) if state == "corrupt" else None     # college: once the new one is in hand
                _write(p, doc)
                out[key] = ("written (%d games)" % len(doc["games"]) if moved is None else
                            "rebuilt (was corrupt: %s; the old file is %s)"
                            % (why, os.path.relpath(moved, hdir("ncaaf", root)).replace(os.sep, "/")))
            except Exception as e:
                out[key] = "failed: %s: %s" % (type(e).__name__, str(e)[:200])
            finally:
                ends["%s.json.gz" % key] = (p, out.get(key))
            log("  history ncaaf %s: %s" % (key, out[key]))
    _record_attempts("ncaaf", root, ends)
    return out


def games(lg, root=None):
    """Every stored history game, with its season. ⛔ Never raises: an unreadable file adds
    nothing here (a history challenger asks fb_challengers.need_history first)."""
    out = []
    for p in sorted(glob.glob(os.path.join(hdir(lg, root), "schedule-*.json.gz"))):
        doc = _stored(p)[0] or {}
        for g in doc.get("games") or []:
            if isinstance(g, dict) and g.get("start") and g.get("home") and g.get("away"):
                out.append(dict(g, season=doc.get("season")))
    return out


def lines(root=None):
    """College history lines, every season, in t60r's shape. ⛔ Never raises."""
    out = {}
    for p in sorted(glob.glob(os.path.join(hdir("ncaaf", root), "lines-*.json.gz"))):
        got = (_stored(p)[0] or {}).get("games")
        if isinstance(got, dict):
            out.update(got)
    return out
