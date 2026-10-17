#!/usr/bin/env python3
r"""test_cfb_injuries_wiring.py — THE COLLEGE INJURY READER RUNS ITSELF. `[Sam, 2026-10-17]`

*"use the college injury source as long as it's accurate and up to date, we
wouldn't want misinformation ruining our bets."* research/cfb_injuries_design.md
§1 item 2: the `cfb-injuries` mode (cfb_injuries.run) runs on the college passes
that already happen, with NO cron change: its PROBE carries a freshness contract
row that converge plans, and Wednesday to Saturday it is planned on every
college pass. A reader that ran but read nothing is not fresh (`freshness.health`),
and neither is a defensive box score that stopped changing. Its stored files
never plan a run and are never red. Planted trees, a pinned clock (or the real
clock on a planted tree, never one of each), fake sources. ⛔ Reads no live
data, makes no network call, writes nothing under data/.

# @vacuity 🔴 a probe with no deadline is never run again
#   file: freshness.py
#   find:             ("cfb-injuries", ("file", f"{latest}/injuries-probe-{season}.json"), T["news"], False,
#   with:             ("cfb-injuries", ("file", f"{latest}/injuries-probe-{season}.json"), [], False,
#
# @vacuity 🔴 the reader's row is college only
#   file: freshness.py
#   find:     if league == "ncaaf":          # college only: the NFL's injuries ride nfl-logs
#   with:     if True:
#
# @vacuity 🔴 the reader runs before the card that reads its reports
#   file: freshness.py
#   find:     rows += [
#   with:     rows[:0] = [
#
# @vacuity 🔴 a failed read is a warning, never a red run
#   file: freshness.py
#   find: SOFT |= {"cfb-injuries"}
#   with: SOFT |= set()
#
# @vacuity 🔴 Wednesday to Saturday the reader runs on EVERY college pass
#   file: freshness.py
#   find: EVERY_PASS = {"ncaaf": {"cfb-injuries": frozenset({2, 3, 4, 5})}}     # Wed-Sat ET
#   with: EVERY_PASS = {"ncaaf": {"cfb-injuries": frozenset()}}     # Wed-Sat ET
#
# @vacuity 🔴 the plan takes the every-pass modes
#   file: freshness.py
#   find:         | every_pass(data, now)
#   with:         | set()
#
# @vacuity 🔴 a file on time but saying nothing new is stale (survey asks its health)
#   file: freshness.py
#   find:         sick = None if late or kind != "file" else health(path, now)
#   with:         sick = None
#
# @vacuity ⛔ an unhealthy row was built on time: it is never LATE
#   file: freshness.py
#   find:             "late_min": (None if (built is None or due is None or not late)
#   with:             "late_min": (None if (built is None or due is None or not stale)
#
# @vacuity 🔴 a source unread past FETCH_MAX_AGE_H is named
#   file: freshness.py
#   find:             elif now - ok > datetime.timedelta(hours=fetch_h):
#   with:             elif False:
#
# @vacuity 🔴 a source never read is named
#   file: freshness.py
#   find:                 bad.append(f"{s} has never been read")
#   with:                 pass
#
# @vacuity 🔴 a reader that read no source at all is named
#   file: freshness.py
#   find:         if not src:
#   with:         if False:
#
# @vacuity ⛔ sources are judged only while a game is close (no warning in a quiet week)
#   file: freshness.py
#   find:     if games is None or any(now < k <= now + datetime.timedelta(hours=age_h) for k, _g in games):
#   with:     if True:
#
# @vacuity 🔴 no readable schedule is CANNOT TELL, and cannot-tell keeps the sources judged
#   file: freshness.py
#   find:     if games is None or any(now < k <= now + datetime.timedelta(hours=age_h) for k, _g in games):
#   with:     if games is not None and any(now < k <= now + datetime.timedelta(hours=age_h) for k, _g in games):
#
# @vacuity 🔴 a conference archive no longer refreshed in season is named
#   file: freshness.py
#   find:             if c is not None and now - c > datetime.timedelta(hours=2 * arch_h):
#   with:             if False:
#
# @vacuity ⛔ the archives are judged only while the season is on
#   file: freshness.py
#   find:     if str(season) != str(legacy) and (games is None or any(
#   with:     if str(season) != str(legacy) and (True or any(
#
# @vacuity 🔴 a failed archive step is named
#   file: freshness.py
#   find:         if arch.get("error"):
#   with:         if False:
#
# @vacuity 🔴 a defensive box score the newest final game never reached is stale
#   file: freshness.py
#   find:     if due is not None and built < due:
#   with:     if False:
#
# @vacuity ⛔ a game under DEFENSE_LAG_H old is not judged yet (one dropped build is not a warning)
#   file: freshness.py
#   find:     edge = now - datetime.timedelta(hours=DEFENSE_LAG_H)
#   with:     edge = now
#
# @vacuity ⛔ only a FINAL game is owed to the box score (a cancelled one is not)
#   file: freshness.py
#   find:     due = max((k for k, g in games if g.get("final") and k <= edge), default=None)
#   with:     due = max((k for k, g in games if k <= edge), default=None)
#
# @vacuity ⛔ a health check that cannot run says so, never silence
#   file: freshness.py
#   find:                 return f"its health check could not run ({type(e).__name__}: {str(e)[:120]})"
#   with:                 return None
#
# @vacuity 🔴 CFBD's roster and defense files are stored-only
#   file: freshness.py
#   find: STORED_ONLY = re.compile(r"/(weather|injuries|adv|venues|cfbd-weather|roster|defense)-\d{4}\.json\.gz$"
#   with: STORED_ONLY = re.compile(r"/(weather|injuries|adv|venues|cfbd-weather)-\d{4}\.json\.gz$"
#
# @vacuity 🔴 the conference archives are stored-only
#   file: freshness.py
#   find:                          r"|/history/injury-archive-\d{4}\.json\.gz$"
#   with:                          r"|/history/injury-archive-NEVER\.json\.gz$"
#
# @vacuity 🔴 the dated report snapshots are stored-only
#   file: freshness.py
#   find:                          r"|/\d{4}-\d{2}-\d{2}/injury-reports(/\d{4}\.json\.gz)?$"
#   with:                          r"|/NEVER/injury-reports$"
#
# @vacuity ⛔ an archive's age says nothing: no clock deadline
#   file: freshness.py
#   find:             rows.append(("cfb-injuries", ("file", f"{data}/history/injury-archive-{_y}.json.gz"), [], False,
#   with:             rows.append(("cfb-injuries", ("file", f"{data}/history/injury-archive-{_y}.json.gz"), T["news"], False,
#
# @vacuity ⛔ a roster or defense file's age says nothing: no clock deadline
#   file: freshness.py
#   find:                 rows.append(("cfb-probe", ("file", f"{latest}/{_k}-{_y}.json.gz"), [], False,
#   with:                 rows.append(("cfb-probe", ("file", f"{latest}/{_k}-{_y}.json.gz"), T["possession"], False,
#
# @vacuity ⛔ a row on the dated snapshots (written only on a change) cries wolf on a quiet week
#   file: freshness.py
#   find:             rows.append(("cfb-injuries", ("file", f"{data}/history/injury-archive-{_y}.json.gz"), [], False,
#   with:             rows.append(("cfb-injuries", ("dir", f"{data}/{utc_day}/injury-reports"), [], False, "x")); rows.append(("cfb-injuries", ("file", f"{data}/history/injury-archive-{_y}.json.gz"), [], False,
#
# @vacuity 🔴 the mode needs no Odds key
#   file: collect.py
#   find:             "cfb-injuries")
#   with:             )
#
# @vacuity 🔴 a run that names the mode is a college run
#   file: collect.py
#   find:                "cfb-injuries": "ncaaf"}
#   with:                }
#
# @vacuity 🔴 the arm does nothing under another league
#   file: collect.py
#   find:             if LEAGUE != "ncaaf":
#   with:             if False:
#
# @vacuity 🔴 the arm runs the reader, in this run's own tree
#   file: collect.py
#   find:             _res = _ci.run(root=".", log=log)   # ⛔ this run's own tree (a test runs it from a copy)
#   with:             _res = {"sources": {"SEC": {"ok": True}}}
#
# @vacuity 🔴 a pass that stored nothing says so
#   file: collect.py
#   find:             if _res.get("error") or not _src or len(_down) == len(_src):
#   with:             if False:
#
# @vacuity 🔴 a source down long enough to matter is named in the run's annotations
#   file: collect.py
#   find:             if _sick:
#   with:             if False:
#
# @vacuity ⛔ the mode is dispatched (converge runs the mode a row names)
#   file: collect.py
#   find:         elif mode == "cfb-injuries":
#   with:         elif mode == "cfb-injuries-DISABLED":
#
# @vacuity 🔴 [2026-10-17, review] the college injury read is the FIRST row, before every card-building mode
#   file: freshness.py
#   find:         rows.insert(0,
#   with:         rows.append(
#
# @vacuity ⛔ [2026-10-17, review] the dossier's college line never says the reports are not collected
#   file: dossier_fb.py
#   find:     "Not covered for college games: this check covers NFL games only. College "
#   with:     "Not covered for college games, so we don't collect them: this check covers NFL games only. College "
#
# @vacuity ⛔ [2026-10-17, review] ...nor the news flags' college note
#   file: news_flags_fb.py
#   find: COLLEGE_NOTE = ("College flags here come from headlines only; the conference injury reports are read "
#   with: COLLEGE_NOTE = ("College football has no public injury reports we may use; the conference injury reports are read "
#
# @vacuity 🔴 every stale row counts at the end of a pass, not each mode's last one
#   file: collect.py
#   find:     still = list(dict.fromkeys(r["mode"] for r in rows2 if r["stale"]))
#   with:     still = [m for m, r in {r["mode"]: r for r in rows2}.items() if r["stale"]]
"""
import contextlib
import datetime
import gzip
import importlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from tcheck import ck, eq, note, section, shown  # noqa: E402

os.environ["LEAGUE"] = "ncaaf"
os.environ["ODDS_API_KEY"] = ""          # ⛔ keys blank: a FREE mode must not need one
import cfb_injuries as CI  # noqa: E402
import daystore  # noqa: E402
import freshness as F  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 10, 15, 14, 30, tzinfo=UTC)      # ⛔ the pinned clock (Thu 10:30 ET)
SEASON = F.current_football_season(NOW)
YEARS = sorted(set(F.FOOTBALL_HISTORY) | {SEASON})
H, D, M = datetime.timedelta(hours=1), datetime.timedelta(days=1), datetime.timedelta(minutes=1)
TREES = []
_REAL_RUN, _REAL_POST, _REAL_GET = CI.run, CI._post, CI._get
_REAL_HEALTH = F.HEALTH


def tree(lg="ncaaf"):
    d = tempfile.mkdtemp(prefix="cfbinj-wiring-")
    TREES.append(d)
    os.makedirs(os.path.join(d, "data", *(() if lg == "mlb" else (lg,)), "latest"))
    os.makedirs(os.path.join(d, "picks"))
    return d


def stamp(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def put(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if path.endswith(".gz"):
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(doc, fh)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)


def probe(built, ok_at="same", season=SEASON, archives=None, **over):
    """A probe as cfb_injuries._write_probe writes it: every source last read at
    `ok_at` (default: when the probe was built), `over` replacing single sources."""
    ok_at = built if ok_at == "same" else ok_at
    src = {s: {"ok": ok_at is not None, "last_ok_at": None if ok_at is None else stamp(ok_at)}
           for s in CI.SOURCES}
    for s, t in over.items():
        src[s] = {"ok": False, "error": "URLError: down", "last_ok_at": None if t is None else stamp(t)}
    return {"season": season, "kind": "DIAGNOSTIC", "built_at": stamp(built), "sources": src,
            "archives": archives if archives is not None else {}}


def game(k, final=False, fbs=True, gid="1"):
    return {"id": gid, "home": "Alabama", "away": "Georgia", "start": k.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "home_class": "fbs" if fbs else "fcs", "away_class": "fbs" if fbs else "fcs", "final": final}


def schedule(data, games, season=SEASON):
    put("%s/latest/schedule-%d.json.gz" % (data, season),
        {"season": season, "games": [dict(g, id=str(i)) for i, g in enumerate(games)]})


def norm(p):
    return os.path.normcase(os.path.normpath(p))


def is_stored(row):
    return F.stored_only({"path": row[1][1], "why": row[4]})


def row_of(data, picks, now, path):
    got = [r for r in F.survey(data, picks, now) if norm(r["path"]) == norm(path)]
    return got[0] if len(got) == 1 else {"stale": None, "unhealthy": None, "late_min": None, "missing": None}


@contextlib.contextmanager
def inside(d):
    cwd = os.getcwd()
    os.chdir(d)
    try:
        yield
    finally:
        os.chdir(cwd)


def lines(buf):
    return buf.getvalue().splitlines()


try:
    # ══════════════════════════════════════════════════════════════════
    section("1. 🔴 THE PROBE ROW PLANS THE READER, ON EVERY COLLEGE PASS WED-SAT")
    # ══════════════════════════════════════════════════════════════════
    P = tree()
    DATA, PICKS = P + "/data/ncaaf", P + "/picks"
    open(DATA + "/latest/props.json.gz", "wb").close()     # a board is stored, so the card rows exist
    ROWS = F.contract(DATA, PICKS, NOW)
    _probe = [r for r in ROWS if r[0] == "cfb-injuries" and not is_stored(r)]
    eq(len(_probe), 1, "🔴 college has ONE row that plans `cfb-injuries`: its probe, not a stored-only file")
    PROBE = _probe[0] if _probe else ("cfb-injuries", ("file", ""), [], False, "")
    # `[2026-10-17, review]` THE READ COMES BEFORE EVERY MODE THAT BUILDS THE CARD: `props-player`
    #    builds it as well as `card-fb` (~~before the card rows~~ was not enough). Read from
    #    collect.run_mode's own arms, never listed here.
    _src = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
    _body = _src[_src.index("\ndef run_mode("):]
    _body = _body[:_body.index("\ndef ", 1)]
    _arms = re.split(r'(?m)^        (?:el)?if mode == "([^"]+)":', _body)
    CARD_MODES = {_arms[i] for i in range(1, len(_arms) - 1, 2) if "build_card_fb(" in _arms[i + 1]}
    _modes = [r[0] for r in ROWS]
    _first = _modes.index("cfb-injuries") if "cfb-injuries" in _modes else len(_modes)
    _late = sorted(m for m in CARD_MODES if m in _modes and _modes.index(m) < _first)
    ck(CARD_MODES >= {"props-player", "card-fb"} and not _late,
       "🔴 the college injury read comes before EVERY mode that builds the card (%s), so a card built "
       "in a pass reads that pass's reports" % ", ".join(sorted(CARD_MODES)), "built before it: %s" % _late)
    ck(PROBE[1][0] == "file" and norm(PROBE[1][1]) == norm(CI.probe_path(SEASON, P)),
       "   ...on the file the reader writes on EVERY attempt (cfb_injuries.probe_path), never one typed here",
       PROBE[1])
    ck(not PROBE[3], "   ...and free, so a paid-pull budget never skips it", PROBE[3])
    for _lg, _d in (("nfl", "/data/nfl"), ("mlb", "/data")):
        _T = tree(_lg)
        _m = sorted({r[0] for r in F.contract(_T + _d, _T + "/picks", NOW)})
        ck(_m and "cfb-injuries" not in _m,
           "🔴 %s has no such row: the reader is college only (the NFL's injuries ride nfl-logs)" % _lg, _m)
        eq(F.every_pass(_T + _d, NOW), set(), "   ...and %s plans nothing on every pass" % _lg)

    MODES = F.plan(DATA, PICKS, NOW)[0]
    ck("cfb-injuries" in MODES, "🔴 a missing probe is planned (the reader has never run here)", MODES)
    ck("card-fb" in MODES and "cfb-injuries" in MODES and MODES.index("cfb-injuries") < MODES.index("card-fb"),
       "🔴 ...and BEFORE the card, so a card built in the same pass reads this pass's reports", MODES)

    # ⚠️ EVERY HOUR OF A WHOLE WEEK, Monday 00:30 ET onwards, with a HEALTHY probe
    #    (every source read when it was built): one from before the top of the
    #    hour is planned every day; one built a minute ago is planned again
    #    Wednesday to Saturday (every college pass) and not Sunday to Tuesday.
    _week = datetime.datetime(2026, 10, 12, 4, 30, tzinfo=UTC)
    _missed, _wedsat, _twice, _marked = [], [], [], []
    for _h in range(7 * 24):
        _t = _week + _h * H
        _wd = (_t - F.ET_OFFSET).weekday()
        put(PROBE[1][1], probe(_t - 61 * M))
        if "cfb-injuries" not in F.plan(DATA, PICKS, _t)[0]:
            _missed.append(_t.strftime("%a %H:%MZ"))
        put(PROBE[1][1], probe(_t - M))
        _modes, _rows = F.plan(DATA, PICKS, _t)
        if _wd in (2, 3, 4, 5) and "cfb-injuries" not in _modes:
            _wedsat.append(_t.strftime("%a %H:%MZ"))
        if _wd not in (2, 3, 4, 5) and "cfb-injuries" in _modes:
            _twice.append(_t.strftime("%a %H:%MZ"))
        if any(r["stale"] for r in _rows if norm(r["path"]) == norm(PROBE[1][1])):
            _marked.append(_t.strftime("%a %H:%MZ"))
    ck(not _missed, "🔴 at every hour of a week (168), a probe from before the top of the hour plans the reader",
       "never planned at: %s" % _missed[:6])
    ck(not _wedsat, "🔴 Wednesday to Saturday ET a probe built a minute ago is planned AGAIN: every college pass "
       "reads the reports before the card it builds", "not planned at: %s" % _wedsat[:6])
    ck(not _twice, "   ...Sunday to Tuesday one built since the top of the hour is not run again",
       "run twice at: %s" % _twice[:6])
    ck(not _marked, "⛔ ...and planned, never marked stale: a pass that just read the reports never ends "
       "with its row out of contract", "stale at: %s" % _marked[:6])
    _tue, _wed = datetime.datetime(2026, 10, 14, 3, 59, tzinfo=UTC), datetime.datetime(2026, 10, 14, 4, 1, tzinfo=UTC)
    eq((F.every_pass(DATA, _tue), F.every_pass(DATA, _wed)), (set(), {"cfb-injuries"}),
       "   the ET day turns at midnight ET (the contract's fixed offset): Tue 23:59 no, Wed 00:01 yes")
    # ⚠️ No cron names the mode: the hourly college news cron's converge pass is
    #    what reaches it, because the two rows share ONE hourly list.
    ck(PROBE[2] == F.FB_TIMES["ncaaf"]["news"],
       "   ...on the same hourly list the hourly college news cron answers, so its pass plans the reader",
       PROBE[2][:3])

    put(PROBE[1][1], probe(NOW - 3 * H))
    _prow = [r for r in F.survey(DATA, PICKS, NOW) if r["mode"] == "cfb-injuries" and r["path"] == PROBE[1][1]]
    _hard, _soft = F.classify(_prow, DATA, refused=False, block={"state": None})
    ck(len(_prow) == 1 and _prow[0]["stale"] and not _hard and len(_soft) == 1,
       "🔴 a stale probe is a WARNING (soft), never a red run: a failed read costs a why sentence, never a card",
       "hard=%d soft=%d" % (len(_hard), len(_soft)))

    # ══════════════════════════════════════════════════════════════════
    section("2. 🔴 A READER THAT RAN BUT READ NOTHING IS NOT FRESH (freshness.health)")
    # ══════════════════════════════════════════════════════════════════
    # The probe is written on EVERY attempt, so its deadline alone said fresh on
    # a pass where every source failed. Monday 12:30 ET: no every-pass planning,
    # and the probe was built a minute ago, inside its hourly deadline.
    MON = datetime.datetime(2026, 10, 12, 16, 30, tzinfo=UTC)
    HT = tree()
    HD, HP = HT + "/data/ncaaf", HT + "/picks"
    HPATH = CI.probe_path(SEASON, HT)
    FETCH, AGE, ARCH = CI.FETCH_MAX_AGE_H, CI.MAX_AGE_H, CI.ARCHIVE_REFRESH_H
    eq(F._injury_limits(), (FETCH, AGE, CI.ARCHIVE_REFRESH_H, CI.LEGACY_SEASON),
       "   the limits are cfb_injuries.py's own (parsed, one copy): %dh unread, %dh before kickoff" % (FETCH, AGE))
    schedule(HD, [game(MON + 12 * H), game(MON - 3 * D, final=True)])

    def judged(doc, now=MON):
        put(HPATH, doc)
        return row_of(HD, HP, now, HPATH)

    _r = judged(probe(MON - M))
    ck(_r["stale"] is False and _r["unhealthy"] is None, "   every source read a minute ago: fresh", _r["unhealthy"])
    _r = judged(probe(MON - M, SEC=MON - (FETCH + 1) * H))
    ck(_r["stale"] and "SEC not read for %dh" % (FETCH + 1) in (_r["unhealthy"] or ""),
       "🔴 ONE source (SEC) unread for %dh, the others answering, while a game kicks off within %dh: stale, "
       "and the reason names it" % (FETCH + 1, AGE), _r["unhealthy"])
    ck(_r["late_min"] is None and not _r["missing"],
       "⛔ ...never LATE: the probe was built on time (no `late:` finding, no lateness entry)", _r["late_min"])
    _hard, _soft = F.classify([_r], HD, refused=False, block={"state": None})
    ck(not _hard and len(_soft) == 1, "   ...a warning (soft), never a red run", "hard=%d" % len(_hard))
    eq([m for m in F.plan(HD, HP, MON)[0] if m == "cfb-injuries"], ["cfb-injuries"],
       "🔴 ...and the pass plans the reader again (Monday: nothing else would)")
    _r = judged(probe(MON - M, SEC=MON - (FETCH - 1) * H))
    ck(_r["stale"] is False, "   ...SEC unread for %dh (under %dh): its reports are still shown, so fresh"
       % (FETCH - 1, FETCH), _r["unhealthy"])
    _r = judged(probe(MON - M, ok_at=None))
    ck(_r["stale"] and (_r["unhealthy"] or "").count("has never been read") == len(CI.SOURCES),
       "🔴 every source never read (the reviewer's case: all seven raising): stale, each named", _r["unhealthy"])
    _r = judged(dict(probe(MON - M), sources={}, error="FeedError: no stored schedule"))
    ck(_r["stale"] and "no source was read (FeedError: no stored schedule)" in (_r["unhealthy"] or ""),
       "🔴 a reader that read no source at all says why", _r["unhealthy"])

    schedule(HD, [game(MON + (AGE + 12) * H), game(MON + 3 * H, fbs=False)])
    _r = judged(probe(MON - M, ok_at=None))
    ck(_r["stale"] is False, "⛔ no FBS game within %dh (the next is %dh away; an FCS game in 3h is not ours): "
       "sources are not judged, so a quiet week warns nobody" % (AGE, AGE + 12), _r["unhealthy"])
    os.remove("%s/latest/schedule-%d.json.gz" % (HD, SEASON))
    _r = judged(probe(MON - M, SEC=MON - (FETCH + 1) * H))
    ck(_r["stale"] and "SEC not read" in (_r["unhealthy"] or ""),
       "🔴 no stored schedule is CANNOT TELL, and cannot-tell keeps the sources judged", _r["unhealthy"])

    # The current season's archives, refreshed once a day by the reader.
    def arch(**confs):
        return {str(SEASON): {c: ({"ok": True, "checked_at": stamp(t)} if t is not None else
                                  {"ok": False, "error": "FeedError: x"}) for c, t in confs.items()}}
    schedule(HD, [game(MON - 3 * D, final=True), game(MON + 4 * D)])
    _r = judged(probe(MON - M, archives=arch(SEC=MON - H, ACC=MON - H)))
    ck(_r["stale"] is False, "   in season, every conference archive refreshed an hour ago: fresh", _r["unhealthy"])
    _r = judged(probe(MON - M, archives=arch(SEC=MON - (2 * ARCH + 2) * H, ACC=MON - H)))
    ck(_r["stale"] and "the %d SEC archive not refreshed for %dh" % (SEASON, 2 * ARCH + 2) in (_r["unhealthy"] or ""),
       "🔴 in season (a final game 3 days ago), an archive that answered before and has not been refreshed for "
       "%dh: stale, named" % (2 * ARCH + 2), _r["unhealthy"])
    _r = judged(probe(MON - M, archives=arch(SEC=None, ACC=MON - H)))
    ck(_r["stale"] is False, "⛔ a conference whose archive never answered is in the probe, not judged: a warning "
       "nobody could clear", _r["unhealthy"])
    _r = judged(probe(MON - M, archives={"error": "KeyError: 'data'"}))
    ck(_r["stale"] and "the archive step failed (KeyError: 'data')" in (_r["unhealthy"] or ""),
       "🔴 an archive step that failed outright is named", _r["unhealthy"])
    schedule(HD, [game(MON - (F.IN_SEASON_D + 2) * D, final=True), game(MON + 4 * D)])
    _r = judged(probe(MON - M, archives=arch(SEC=MON - 30 * D)))
    ck(_r["stale"] is False, "⛔ no final game in the last %d days (the off-season): the archives are not judged"
       % F.IN_SEASON_D, _r["unhealthy"])

    def boom_check(path, now):
        raise ValueError("planted")
    try:
        F.HEALTH = ((re.compile(r"/ncaaf/latest/injuries-probe-\d{4}\.json$"), boom_check),)
        _r = judged(probe(MON - M))
    finally:
        F.HEALTH = _REAL_HEALTH
    ck(_r["stale"] and "its health check could not run (ValueError: planted)" in (_r["unhealthy"] or ""),
       "⛔ a health check that cannot run says so (soft), never a silent fresh", _r["unhealthy"])

    # ══════════════════════════════════════════════════════════════════
    section("3. ⛔ THE STORED FILES NEVER PLAN A RUN AND ARE NEVER RED")
    # ══════════════════════════════════════════════════════════════════
    # design §1: the archives (written by the reader) and CFBD's roster jerseys
    # and defensive box score (cfb.py, part P2's `store_kept`, named by §1 item 4).
    WANT = {norm(CI.archive_path(y, P)): "cfb-injuries" for y in YEARS}
    WANT.update({norm("%s/latest/%s-%d.json.gz" % (DATA, k, y)): "cfb-probe"
                 for y in YEARS for k in ("roster", "defense")})
    STORED = [r for r in ROWS if norm(r[1][1]) in WANT]
    eq(sorted((norm(r[1][1])[len(norm(P)):], r[0]) for r in STORED),
       sorted((k[len(norm(P)):], v) for k, v in WANT.items()),
       "🔴 a row each, for 2025 and this season: the archives under the reader, roster and defense under cfb-probe")
    ck(STORED and all(is_stored(r) for r in STORED), "   ...every one stored-only",
       [r[1][1][len(P):] for r in STORED if not is_stored(r)])
    eq(sorted({len(r[2]) for r in STORED}), [0],
       "   ...and no clock deadline: each is rewritten only when its content changes")
    _fake = [{"mode": r[0], "path": r[1][1], "why": r[4], "stale": True, "missing": True,
              "paid": False, "age_min": None} for r in STORED]
    _hard, _soft = F.classify(_fake, DATA, refused=False, block={"state": None})
    ck(_fake and not _hard and len(_soft) == len(_fake), "🔴 a missing stored file is a warning, never a red run",
       [r["path"][len(P):] for r in _hard])
    _sv, _sm, _ep = F.survey, F.slate_moves, F.every_pass
    try:
        F.survey = lambda data="data", picks="picks", now=None: _fake
        F.slate_moves = lambda data, picks, now: set()
        F.every_pass = lambda data="data", now=None: set()
        eq(F.plan(DATA, PICKS, NOW)[0], [],
           "🔴 ...and never plans a run (no CFBD rebuild, no conference calls, for a file no model reads)")
    finally:
        F.survey, F.slate_moves, F.every_pass = _sv, _sm, _ep

    _old = NOW - 5 * D
    _snap, _w = daystore.archive({"fetched_at": stamp(_old), "reports": []}, DATA, "injury-reports",
                                 log=lambda m: None, when=_old)
    _snap = _snap.replace(os.sep, "/")                  # a contract path is written with "/"
    ck(_w and F.stored_only({"path": _snap}) and F.stored_only({"path": os.path.dirname(_snap)}),
       "🔴 the dated report snapshots (daystore's own path) and their day directory are stored-only too, so a "
       "row added on them later can never plan or redden a run", _snap[len(P):])
    ck(not F.stored_only({"path": PROBE[1][1]}), "   ⛔ ...but the PROBE is not: its row exists to plan the reader")

    # ⛔ A QUIET WEEK NEVER WARNS. Nothing has changed for five days (no new
    #    snapshot, archive, roster or defense file: each is written only on a
    #    change), the last final game was six days ago, the next is three days
    #    off, and the reader ran ten minutes ago with every source answering.
    Q = tree()
    QD = Q + "/data/ncaaf"
    for _y in YEARS:
        put(CI.archive_path(_y, Q), {"built_at": stamp(_old)})
        for _k in ("roster", "defense"):
            put("%s/latest/%s-%d.json.gz" % (QD, _k, _y), {"written_at": stamp(_old)})
    schedule(QD, [game(NOW - 6 * D, final=True), game(NOW + 3 * D)])
    daystore.archive({"fetched_at": stamp(_old), "reports": []}, QD, "injury-reports", log=lambda m: None, when=_old)
    put(CI.probe_path(SEASON, Q), probe(NOW - 10 * M, archives=arch(SEC=NOW - H, B10=NOW - 2 * H)))
    _fam = [r for r in F.survey(QD, Q + "/picks", NOW)
            if r["mode"] == "cfb-injuries" or re.search(r"/(roster|defense)-\d{4}\.json\.gz$", r["path"])]
    eq(len(_fam), 1 + 3 * len(YEARS), "   the quiet tree holds every college-injury row (the probe and %d stored "
       "files), so the check below asks about all of them" % (3 * len(YEARS)))
    eq([(r["path"][len(Q):], r["unhealthy"]) for r in _fam if r["stale"]], [],
       "⛔ a quiet week (nothing changed for five days, the reader ran ten minutes ago) leaves no college-injury "
       "row stale")

    # ══════════════════════════════════════════════════════════════════
    section("4. 🔴 A DEFENSIVE BOX SCORE THAT STOPPED CHANGING IS CAUGHT BY ITS GAMES, NOT ITS AGE")
    # ══════════════════════════════════════════════════════════════════
    # defense-<season> is rewritten only when a game's box scores add to it, so
    # its age says nothing; the newest FINAL FBS game over DEFENSE_LAG_H old
    # says when it should last have changed.
    DT = tree()
    DD, DP = DT + "/data/ncaaf", DT + "/picks"
    DEF = "%s/latest/defense-%d.json.gz" % (DD, SEASON)
    K1, K2 = NOW - 3 * D, NOW - 20 * H                 # final 3 days ago; final 20h ago (under the lag)
    schedule(DD, [game(K1, final=True), game(K2, final=True), game(NOW + 2 * D)])

    def defense(written, now=NOW):
        put(DEF, {"season": SEASON, "players": {}, "written_at": stamp(written)})
        return row_of(DD, DP, now, DEF)

    _r = defense(K1 - D)
    ck(_r["stale"] and "kickoff %s" % K1.strftime("%a %d %b %H:%MZ") in (_r["unhealthy"] or ""),
       "🔴 last written the day BEFORE a game that went final 3 days ago: stale, naming the game it lacks",
       _r["unhealthy"])
    ck(_r["late_min"] is None and F.stored_only(_r), "   ...never LATE, and stored-only", (_r["late_min"], _r["path"]))
    _hard, _soft = F.classify([_r], DD, refused=False, block={"state": None})
    ck(not _hard and len(_soft) == 1, "⛔ ...so a warning, never a red run, and never a planned CFBD rebuild",
       "hard=%d" % len(_hard))
    _r = defense(K1 + 10 * H)
    ck(_r["stale"] is False, "   written after that game, before one that went final 20h ago (under %dh): fresh"
       % F.DEFENSE_LAG_H, _r["unhealthy"])
    schedule(DD, [game(K1, final=True), game(NOW - 2 * D, final=False), game(NOW + 2 * D)])
    _r = defense(K1 + 10 * H)
    ck(_r["stale"] is False, "⛔ a game two days ago that never went final (cancelled) is owed nothing",
       _r["unhealthy"])
    schedule(DD, [game(NOW - 40 * D, final=True)])
    _r = defense(NOW - 39 * D)
    ck(_r["stale"] is False, "⛔ the off-season: written after the last final game, 39 days old, is fresh",
       _r["unhealthy"])
    _R = "%s/latest/roster-%d.json.gz" % (DD, SEASON)
    put(_R, {"season": SEASON, "teams": {}, "written_at": stamp(NOW - 60 * D)})
    _r = row_of(DD, DP, NOW, _R)
    ck(_r["stale"] is False and _r["unhealthy"] is None,
       "   ⚠️ a roster is not judged by games (it does not change with one): an accepted gap", _r["unhealthy"])

    # ══════════════════════════════════════════════════════════════════
    section("5. 🔴 THE MODE: FREE, COLLEGE ONLY, PINNED THERE, AND IT RUNS THE READER")
    # ══════════════════════════════════════════════════════════════════
    import collect as C  # noqa: E402
    _argv = sys.argv[:]
    try:
        os.environ["LEAGUE"] = "mlb"
        sys.argv = [_argv[0], "converge-off", "cfb-injuries"]
        with contextlib.redirect_stdout(io.StringIO()):
            importlib.reload(C)
        eq((C.LEAGUE, C.DATA), ("ncaaf", "data/ncaaf"),
           "🔴 a run that names cfb-injuries is a college run whatever the league input said (MODE_LEAGUE)")
    finally:
        sys.argv = _argv
        os.environ["LEAGUE"] = "ncaaf"
        with contextlib.redirect_stdout(io.StringIO()):
            importlib.reload(C)
    eq((C.LEAGUE, C.ODDS_KEY), ("ncaaf", ""), "   (the harness: a college collector with no Odds key)")
    C._ensure_cfb_team_directory = lambda: None        # ⛔ no CFBD call for logos in a test

    CALLS = []

    def fake_run(root=None, now=None, post=None, get=None, log=print):
        CALLS.append((root, os.getcwd()))
        return {"ok": True, "sources": {"SEC": {"ok": True}}, "snapshot": None, "probe": "p"}

    CI.run = fake_run
    MT = tree()
    with inside(MT):
        _out = io.StringIO()
        try:
            with contextlib.redirect_stdout(_out):
                C.run_mode("gamelines")
            _gate = None
        except SystemExit as e:
            _gate = e.code
        ck(_gate == 1 and any("ODDS_API_KEY is not set" in l for l in lines(_out)),
           "   the harness is live: a paid mode with no key stops at the gate", "exit %r" % _gate)
        _out = io.StringIO()
        try:
            with contextlib.redirect_stdout(_out):
                C.run_mode("cfb-injuries")
            _exit = None
        except SystemExit as e:
            _exit = e.code
        ck(_exit is None, "🔴 cfb-injuries needs no Odds key (FREE): it never spends a credit",
           "exit %r: %s" % (_exit, shown(lines(_out)[-2:])))
        ck(len(CALLS) == 1 and CALLS[0][0] == "." and norm(CALLS[0][1]) == norm(MT),
           "🔴 ...and it runs the reader ONCE, in this run's own tree", CALLS)
        _w = [l for l in lines(_out) if l.startswith("::")]
        eq(_w, [], "   ...and a pass where the sources answered prints no annotation")
        del CALLS[:]
        C.LEAGUE = "nfl"
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                C.run_mode("cfb-injuries")
        finally:
            C.LEAGUE = "ncaaf"
        eq(CALLS, [], "🔴 under another league the arm does nothing: no conference report reaches the NFL's tree")

        def returning(res):
            def _r(root=None, now=None, post=None, get=None, log=print):
                return res
            return _r
        for _label, _res, _want in (
                ("one source down (its reports are simply not shown)",
                 {"ok": False, "sources": {"SEC": {"ok": False}, "ACC": {"ok": True}}, "probe": "p"}, False),
                ("every source down",
                 {"ok": False, "sources": {"SEC": {"ok": False}, "ACC": {"ok": False}}, "probe": "p"}, True),
                ("the snapshot step failed",
                 {"ok": False, "error": "FeedError: x", "sources": {"SEC": {"ok": True}}, "probe": "p"}, True)):
            CI.run = returning(_res)
            _out = io.StringIO()
            with contextlib.redirect_stdout(_out):
                C.run_mode("cfb-injuries")
            _w = [l for l in lines(_out) if l.startswith("::warning::cfb-injuries read nothing for ncaaf")]
            ck(bool(_w) == _want, "%s %s: %s" % ("🔴" if _want else "  ", _label,
                                                 "a warning annotation" if _want else "no annotation"),
               shown(_w))

        # 🔴 ONE SOURCE DOWN LONG ENOUGH TO MATTER is named in the run's own
        #    annotations, read from the probe the reader just wrote (real clock,
        #    this planted tree: a game in 12 hours, SEC unread for 7).
        _now = datetime.datetime.now(UTC)
        _season = F.current_football_season(_now)
        schedule("data/ncaaf", [game(_now + 12 * H)], season=_season)
        _pp = CI.probe_path(_season, ".")

        def writing(doc):
            def _r(root=None, now=None, post=None, get=None, log=print):
                put(_pp, doc)
                return {"ok": False, "sources": {"SEC": {"ok": False}, "ACC": {"ok": True}}, "probe": _pp}
            return _r
        for _label, _doc, _want in (
                ("SEC unread for %dh, a game in 12h" % (FETCH + 1),
                 probe(_now, season=_season, SEC=_now - (FETCH + 1) * H), True),
                ("SEC down this pass only (read an hour ago)",
                 probe(_now, season=_season, SEC=_now - H), False)):
            CI.run = writing(_doc)
            _out = io.StringIO()
            with contextlib.redirect_stdout(_out):
                C.run_mode("cfb-injuries")
            _w = [l for l in lines(_out) if l.startswith("::warning::cfb-injuries for ncaaf: ")]
            ck(bool(_w) == _want and (not _want or "SEC not read for %dh" % (FETCH + 1) in _w[0]),
               "%s %s: %s" % ("🔴" if _want else "  ", _label,
                              "a warning naming it" if _want else "no health annotation"), shown(_w))

    # ══════════════════════════════════════════════════════════════════
    section("6. 🔴 END TO END: THE READER THE ARM RUNS WRITES THE FILE ITS ROW WATCHES")
    # ══════════════════════════════════════════════════════════════════
    # The real cfb_injuries.run on a planted tree, at the real clock. The
    # contract is asked at the instant the reader stamped its probe, so the
    # reader and the contract read ONE clock and the top of an hour falling
    # between the two calls cannot decide the verdict. ⛔ Offline: every source
    # call is fake (raising, or an empty answer).
    NET = []

    def offline(*a, **k):
        NET.append(a[:1])
        raise urllib.error.URLError("offline: a test makes no network call")

    def empty_post(url, body, timeout=None):
        NET.append(url)
        return {}                                   # HDI: no current reports

    def empty_get(url, timeout=None):
        NET.append(url)
        return {"games": []}                       # Sun Belt / Pac-12: no games listed

    for _label, _post, _get, _ok in (("every source raising", offline, offline, False),
                                     ("every source answering (no reports this week)", empty_post, empty_get, True)):
        CI.run, CI._post, CI._get = _REAL_RUN, _post, _get
        E = tree()
        with inside(E):
            _t0 = datetime.datetime.now(UTC)
            schedule("data/ncaaf", [game(_t0 + 12 * H)], season=F.current_football_season(_t0))
            _before = F.plan("data/ncaaf", "picks", _t0)[0]
            _out = io.StringIO()
            with contextlib.redirect_stdout(_out):
                C.run_mode("cfb-injuries")
            _probes = sorted(n for n in os.listdir("data/ncaaf/latest") if n.startswith("injuries-probe-"))
            _built = [F.stamp_of(os.path.join("data/ncaaf/latest", n)) for n in _probes]
            _t1 = _built[0] if len(_built) == 1 and _built[0] else datetime.datetime.now(UTC)
            _after, _arows = F.plan("data/ncaaf", "picks", _t1)
        _p = [r for r in _arows if r["mode"] == "cfb-injuries" and not F.stored_only(r)]
        _every = (_t1 - F.ET_OFFSET).weekday() in F.EVERY_PASS["ncaaf"]["cfb-injuries"]
        ck("cfb-injuries" in _before and len(_p) == 1, "   %s: planned before the reader ran (no probe yet)"
           % _label, _before)
        if _ok:
            ck(len(_p) == 1 and not _p[0]["stale"] and ("cfb-injuries" in _after) == _every,
               "🔴 %s: satisfied after, its probe is the file its row watches (planned again only by "
               "Wed-Sat's every pass: %s)" % (_label, _every), _p[0]["unhealthy"] if _p else _p)
        else:
            ck(len(_p) == 1 and _p[0]["stale"] and "cfb-injuries" in _after
               and (_p[0]["unhealthy"] or "").count("has never been read") == len(CI.SOURCES),
               "🔴 %s: NOT satisfied after (the reviewer's case): stale with every source named, and planned "
               "again" % _label, _p[0]["unhealthy"] if _p else _p)
            ck(any(l.startswith("::warning::cfb-injuries read nothing for ncaaf") for l in lines(_out))
               and any(l.startswith("::warning::cfb-injuries for ncaaf: college injury reports:")
                       for l in lines(_out)),
               "   ...and the pass says so twice: it read nothing, and which sources are down",
               shown([l for l in lines(_out) if l.startswith("::")]))
    note("source calls made to fakes: %d" % len(NET))

    # ══════════════════════════════════════════════════════════════════
    section("7. ⛔ A READER THAT RAISES IS NOT A CRASH OF THE PASS, AND ITS ROW IS NOT HIDDEN")
    # ══════════════════════════════════════════════════════════════════
    def boom(root=None, now=None, post=None, get=None, log=print):
        raise RuntimeError("the reader blew up")

    CI.run, CI._post, CI._get = boom, _REAL_POST, _REAL_GET
    X = tree()
    open(X + "/data/ncaaf/latest/props.json.gz", "wb").close()     # the card rows exist
    # ⚠️ The reader's stored archives are present (their rows are inside contract)
    #    and its probe says no source was ever read, so the probe row is the one
    #    stale row of the mode: the end-of-pass report must still name it.
    _tx = datetime.datetime.now(UTC)
    _sx = F.current_football_season(_tx)
    # ⛔ ONE CLOCK: the contract's own years at the clock the pass runs on (~~the pinned
    #    YEARS~~: from 2027-08-01 a 2027 archive row would be the mode's last row, stale).
    for _y in sorted(set(F.FOOTBALL_HISTORY) | {_sx}):
        put(CI.archive_path(_y, X), {"built_at": stamp(_tx)})
    put(CI.probe_path(_sx, X), probe(_tx, season=_sx, ok_at=None))
    RAN = []
    _real_mode, _real_spend = C.run_mode, C.daily_spend

    def run_mode(m):
        RAN.append(m)
        if m == "cfb-injuries":
            return _real_mode(m)               # the real arm; every other mode is a no-op here

    try:
        C.run_mode, C.daily_spend = run_mode, (lambda: 0)
        with inside(X):
            _out = io.StringIO()
            with contextlib.redirect_stdout(_out):
                _code = C.converge()
    finally:
        C.run_mode, C.daily_spend = _real_mode, _real_spend
        C._RAN_PAID.clear()
    _w = [l for l in lines(_out) if l.startswith("::warning::cfb-injuries failed for ncaaf")]
    eq(_code, 0, "🔴 the pass stays green when the reader raises")
    ck(_w and "RuntimeError" in _w[0], "   ...and says so as a warning naming the mode and the error", shown(_w))
    eq([l for l in lines(_out) if l.startswith("::error::")], [], "   ...with no error annotation")
    ck("cfb-injuries" in RAN and "card-fb" in RAN and RAN.index("cfb-injuries") < RAN.index("card-fb"),
       "🔴 ...and the card planned after it still ran", RAN)
    _still = [l for l in lines(_out) if "STILL OUT OF CONTRACT:" in l]
    ck(_still and "cfb-injuries" in _still[0].split("STILL OUT OF CONTRACT:")[1].split(),
       "🔴 the end-of-pass report names the stale probe, though the mode's LAST row (its archive) is fresh",
       shown(_still))
    _unh = [l for l in lines(_out) if "UNHEALTHY: college injury reports:" in l]
    if (_tx - F.ET_OFFSET).strftime("%Y%m%d%H") == (datetime.datetime.now(UTC) - F.ET_OFFSET).strftime("%Y%m%d%H"):
        ck(bool(_unh), "   ...and the pass's survey prints why the probe is due (UNHEALTHY: ...)", shown(_unh[:1]))
    else:
        note("the top of an hour fell inside the pass, so the probe read LATE first; the UNHEALTHY line was not asked")

    # ══════════════════════════════════════════════════════════════════
    section("8. ⛔ NOTHING THE READER SEES SAYS THE COLLEGE REPORTS ARE NOT COLLECTED")
    # ══════════════════════════════════════════════════════════════════
    # `[Sam, 2026-10-17]` he chose to use the conference reports; every reader-facing college
    #    sentence about injuries must then be true (the dossier's §7 still said "we don't collect
    #    them" on the college Odds tab). The class: the dossier's college Personnel line and the
    #    news flags' college note.
    import dossier_fb  # noqa: E402
    import news_flags_fb  # noqa: E402
    _says = {"dossier §7, college": ((dossier_fb.s_personnel(["Texas Longhorns"], {2026: {"players": {}}}, 2026,
                                                             None, 8, "ncaaf") or {}).get("why") or ""),
             "news flags, college": news_flags_fb.COLLEGE_NOTE or ""}
    _false = re.compile(r"don.t collect|do not collect|not collected|no public injury report|forbid|"
                        r"do not allow the reports", re.I)
    _bad = {k: v for k, v in _says.items() if _false.search(v)}
    ck(all(_says.values()) and not _bad,
       "⛔ no college sentence says the conference injury reports are not collected or may not be used",
       shown(str(_bad)))
finally:
    CI.run, CI._post, CI._get = _REAL_RUN, _REAL_POST, _REAL_GET
    F.HEALTH = _REAL_HEALTH
    for _t in TREES:
        shutil.rmtree(_t, ignore_errors=True)
