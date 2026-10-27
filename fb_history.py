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
"""
import datetime
import glob
import gzip
import json
import os

import freshness as _F       # stdlib only: the contract's own stamp reader

ROOT = os.path.dirname(os.path.abspath(__file__))
NFL_SEASONS = (2018, 2019, 2020, 2021, 2022, 2023, 2024)     # ⛔ §3d
CFB_SEASONS = (2023, 2024)                                   # ⛔ §3d
ALIAS = {"OAK": "LV"}                                        # ⛔ §3d: Oakland became Las Vegas in 2020


def log(m):
    print(m, flush=True)


def hdir(lg, root=None):
    return os.path.join(root or ROOT, "data", lg, "history")


def _jz(p):
    try:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


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
    """Each missing NFL history season, from nflverse (free). `build(season) -> doc`
    (tests plant one). -> {season: outcome}. ⛔ Never raises."""
    out, rows = {}, None
    for s in NFL_SEASONS:
        p = os.path.join(hdir("nfl", root), "schedule-%d.json.gz" % s)
        try:
            if os.path.exists(p):
                # `[2026-10-27]` a stored file the contract reads no stamp in (its own reader,
                # so one list of stamp fields) is stamped once: its games untouched
                doc = _jz(p)
                if doc and doc.get("games") and _F.stamp_of(p) is None:
                    _write(p, doc)
                    out[s] = "stamped (%d games)" % len(doc["games"])
                    log("  history nfl %d: %s" % (s, out[s]))
                continue
            if build is None:
                import nfl as _nfl
                if rows is None:
                    seen = {r["tag_name"]: [(a["name"], a["size"], a["browser_download_url"])
                                            for a in (r.get("assets") or [])] for r in _nfl._releases(log)}
                    rows = _nfl._rows(seen, "schedules", _nfl.SCHEDULE_FILE, log)
                doc, _rep = _nfl.build_schedule(s, None, log, rows=rows)
            else:
                doc = build(s)
            if not (doc or {}).get("games"):
                out[s] = "not written: no games"
                continue
            doc = alias(dict(doc, kind="DESCRIPTIVE", history=True))
            _write(p, doc)
            out[s] = "written (%d games)" % len(doc["games"])
        except Exception as e:
            out[s] = "failed: %s: %s" % (type(e).__name__, str(e)[:200])
        log("  history nfl %d: %s" % (s, out[s]))
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
    """Each missing college history season's schedule (2 calls) and lines (1 call),
    every call priced first. -> {file: outcome}. ⛔ Never raises."""
    out = {}
    try:
        import cfb as _cfb
    except Exception as e:
        return {"import": "failed: %s" % type(e).__name__}
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for s in CFB_SEASONS:
        for kind, calls in (("schedule", 2), ("lines", 1)):
            p = os.path.join(hdir("ncaaf", root), "%s-%d.json.gz" % (kind, s))
            if os.path.exists(p):
                continue
            key = "%s-%d" % (kind, s)
            try:
                if not _cfb._priced(calls, "history %s %d" % (kind, s), log):
                    out[key] = "refused"
                    continue
                if kind == "schedule":
                    doc, _rep = _cfb.build_schedule(s, log)
                    if not (doc or {}).get("games"):
                        out[key] = "not written: no games"
                        continue
                    _write(p, dict(doc, history=True))
                    out[key] = "written (%d games)" % len(doc["games"])
                else:
                    lines = pick_lines(_cfb.get("/lines", {"year": str(s), "seasonType": "regular"}))
                    if not lines:
                        out[key] = "not written: no lines"
                        continue
                    _write(p, {"season": s, "kind": "DESCRIPTIVE", "endpoint": "/lines",
                               "built_at": stamp, "games": lines})
                    out[key] = "written (%d games)" % len(lines)
            except Exception as e:
                out[key] = "failed: %s: %s" % (type(e).__name__, str(e)[:200])
            log("  history ncaaf %s: %s" % (key, out[key]))
    return out


def games(lg, root=None):
    """Every stored history game, with its season."""
    out = []
    for p in sorted(glob.glob(os.path.join(hdir(lg, root), "schedule-*.json.gz"))):
        doc = _jz(p) or {}
        for g in doc.get("games") or []:
            if g.get("start") and g.get("home") and g.get("away"):
                out.append(dict(g, season=doc.get("season")))
    return out


def lines(root=None):
    """College history lines, every season, in t60r's shape."""
    out = {}
    for p in sorted(glob.glob(os.path.join(hdir("ncaaf", root), "lines-*.json.gz"))):
        out.update((_jz(p) or {}).get("games") or {})
    return out
