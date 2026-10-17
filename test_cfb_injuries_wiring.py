#!/usr/bin/env python3
r"""test_cfb_injuries_wiring.py — THE COLLEGE INJURY READER RUNS ITSELF. `[Sam, 2026-10-17]`

*"use the college injury source as long as it's accurate and up to date, we
wouldn't want misinformation ruining our bets."* research/cfb_injuries_design.md
§1 item 2: the `cfb-injuries` mode (cfb_injuries.run) runs on the college passes
that already happen, with NO cron change, because its PROBE carries a freshness
contract row that converge plans. Its stored files never plan a run and are
never red. Planted trees, a pinned clock (or the real clock on a planted tree,
never one of each), fake sources. ⛔ Reads no live data, makes no network call,
writes nothing under data/.

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
# @vacuity ⛔ an archive's age says nothing: late only when missing
#   file: freshness.py
#   find:             rows.append(("cfb-injuries", ("file", f"{data}/history/injury-archive-{_y}.json.gz"), [], False,
#   with:             rows.append(("cfb-injuries", ("file", f"{data}/history/injury-archive-{_y}.json.gz"), T["news"], False,
#
# @vacuity ⛔ a roster or defense file's age says nothing: late only when missing
#   file: freshness.py
#   find:                 rows.append(("cfb-probe", ("file", f"{latest}/{_k}-{_y}.json.gz"), [], False,
#   with:                 rows.append(("cfb-probe", ("file", f"{latest}/{_k}-{_y}.json.gz"), T["possession"], False,
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
# @vacuity ⛔ the mode is dispatched (converge runs the mode a row names)
#   file: collect.py
#   find:         elif mode == "cfb-injuries":
#   with:         elif mode == "cfb-injuries-DISABLED":
#
# @vacuity ⛔ a row on the dated snapshots (written only on a change) cries wolf on a quiet week
#   file: freshness.py
#   find:             rows.append(("cfb-injuries", ("file", f"{data}/history/injury-archive-{_y}.json.gz"), [], False,
#   with:             rows.append(("cfb-injuries", ("dir", f"{data}/{utc_day}/injury-reports"), [], False, "x")); rows.append(("cfb-injuries", ("file", f"{data}/history/injury-archive-{_y}.json.gz"), [], False,
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
TREES = []
_REAL_RUN, _REAL_POST, _REAL_GET = CI.run, CI._post, CI._get


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


def norm(p):
    return os.path.normcase(os.path.normpath(p))


def is_stored(row):
    return F.stored_only({"path": row[1][1], "why": row[4]})


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
    section("1. 🔴 THE PROBE ROW PLANS THE READER, ON EVERY COLLEGE PASS")
    # ══════════════════════════════════════════════════════════════════
    P = tree()
    DATA, PICKS = P + "/data/ncaaf", P + "/picks"
    open(DATA + "/latest/props.json.gz", "wb").close()     # a board is stored, so the card rows exist
    ROWS = F.contract(DATA, PICKS, NOW)
    probe = [r for r in ROWS if r[0] == "cfb-injuries" and not is_stored(r)]
    eq(len(probe), 1, "🔴 college has ONE row that plans `cfb-injuries`: its probe, not a stored-only file")
    PROBE = probe[0] if probe else ("cfb-injuries", ("file", ""), [], False, "")
    ck(PROBE[1][0] == "file" and norm(PROBE[1][1]) == norm(CI.probe_path(SEASON, P)),
       "   ...on the file the reader writes on EVERY attempt (cfb_injuries.probe_path), never one typed here",
       PROBE[1])
    ck(not PROBE[3], "   ...and free, so a paid-pull budget never skips it", PROBE[3])
    for _lg, _d in (("nfl", "/data/nfl"), ("mlb", "/data")):
        _T = tree(_lg)
        _m = sorted({r[0] for r in F.contract(_T + _d, _T + "/picks", NOW)})
        ck(_m and "cfb-injuries" not in _m,
           "🔴 %s has no such row: the reader is college only (the NFL's injuries ride nfl-logs)" % _lg, _m)

    MODES = F.plan(DATA, PICKS, NOW)[0]
    ck("cfb-injuries" in MODES, "🔴 a missing probe is planned (the reader has never run here)", MODES)
    ck("card-fb" in MODES and "cfb-injuries" in MODES and MODES.index("cfb-injuries") < MODES.index("card-fb"),
       "🔴 ...and BEFORE the card, so a card built in the same pass reads this pass's reports", MODES)

    # ⚠️ EVERY HOUR OF A WHOLE WEEK, Monday 00:30 ET onwards: a probe from before
    #    the top of the hour is planned, one from after it is not run twice. So the
    #    first pass after each hour runs the reader: every pass Wed-Sat unless two
    #    land in one hour, and Sun-Tue at least daily.
    _week = datetime.datetime(2026, 10, 12, 4, 30, tzinfo=UTC)
    _missed, _twice = [], []
    for _h in range(7 * 24):
        _t = _week + datetime.timedelta(hours=_h)
        put(PROBE[1][1], {"built_at": stamp(_t - datetime.timedelta(minutes=61))})
        if "cfb-injuries" not in F.plan(DATA, PICKS, _t)[0]:
            _missed.append(_t.strftime("%a %H:%MZ"))
        put(PROBE[1][1], {"built_at": stamp(_t - datetime.timedelta(minutes=1))})
        if "cfb-injuries" in F.plan(DATA, PICKS, _t)[0]:
            _twice.append(_t.strftime("%a %H:%MZ"))
    ck(not _missed, "🔴 at every hour of a week (168), a probe from before the top of the hour plans the reader",
       "never planned at: %s" % _missed[:6])
    ck(not _twice, "   ...and one built since the top of the hour is not run again", "run twice at: %s" % _twice[:6])
    # ⚠️ No cron names the mode: the hourly college news cron's converge pass is
    #    what reaches it, because the two rows share ONE hourly list.
    ck(PROBE[2] == F.FB_TIMES["ncaaf"]["news"],
       "   ...on the same hourly list the hourly college news cron answers, so its pass plans the reader",
       PROBE[2][:3])

    put(PROBE[1][1], {"built_at": stamp(NOW - datetime.timedelta(hours=3))})
    _prow = [r for r in F.survey(DATA, PICKS, NOW) if r["mode"] == "cfb-injuries" and r["path"] == PROBE[1][1]]
    _hard, _soft = F.classify(_prow, DATA, refused=False, block={"state": None})
    ck(len(_prow) == 1 and _prow[0]["stale"] and not _hard and len(_soft) == 1,
       "🔴 a stale probe is a WARNING (soft), never a red run: a failed read costs a why sentence, never a card",
       "hard=%d soft=%d" % (len(_hard), len(_soft)))

    # ══════════════════════════════════════════════════════════════════
    section("2. ⛔ THE STORED FILES NEVER PLAN A RUN AND ARE NEVER RED")
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
       "   ...and late only when MISSING: each is rewritten only when its content changes")
    _fake = [{"mode": r[0], "path": r[1][1], "why": r[4], "stale": True, "missing": True,
              "paid": False, "age_min": None} for r in STORED]
    _hard, _soft = F.classify(_fake, DATA, refused=False, block={"state": None})
    ck(_fake and not _hard and len(_soft) == len(_fake), "🔴 a missing stored file is a warning, never a red run",
       [r["path"][len(P):] for r in _hard])
    _sv, _sm = F.survey, F.slate_moves
    try:
        F.survey = lambda data="data", picks="picks", now=None: _fake
        F.slate_moves = lambda data, picks, now: set()
        eq(F.plan(DATA, PICKS, NOW)[0], [],
           "🔴 ...and never plans a run (no CFBD rebuild, no conference calls, for a file no model reads)")
    finally:
        F.survey, F.slate_moves = _sv, _sm

    _old = NOW - datetime.timedelta(days=5)
    _snap, _w = daystore.archive({"fetched_at": stamp(_old), "reports": []}, DATA, "injury-reports",
                                 log=lambda m: None, when=_old)
    _snap = _snap.replace(os.sep, "/")                  # a contract path is written with "/"
    ck(_w and F.stored_only({"path": _snap}) and F.stored_only({"path": os.path.dirname(_snap)}),
       "🔴 the dated report snapshots (daystore's own path) and their day directory are stored-only too, so a "
       "row added on them later can never plan or redden a run", _snap[len(P):])
    ck(not F.stored_only({"path": PROBE[1][1]}), "   ⛔ ...but the PROBE is not: its row exists to plan the reader")

    # ⛔ A QUIET WEEK NEVER WARNS. Nothing has changed for five days (no new
    #    snapshot, archive, roster or defense file: each is written only on a
    #    change) and the reader ran ten minutes ago. A row judging one of these
    #    files by its age, or a row on the dated snapshots, would be a warning
    #    nobody can clear, every quiet day and all off-season.
    Q = tree()
    QD = Q + "/data/ncaaf"
    for _y in YEARS:
        put(CI.archive_path(_y, Q), {"built_at": stamp(_old)})
        for _k in ("roster", "defense"):
            put("%s/latest/%s-%d.json.gz" % (QD, _k, _y), {"written_at": stamp(_old)})
    daystore.archive({"fetched_at": stamp(_old), "reports": []}, QD, "injury-reports", log=lambda m: None, when=_old)
    put(CI.probe_path(SEASON, Q), {"built_at": stamp(NOW - datetime.timedelta(minutes=10))})
    _fam = [r for r in F.survey(QD, Q + "/picks", NOW)
            if r["mode"] == "cfb-injuries" or re.search(r"/(roster|defense)-\d{4}\.json\.gz$", r["path"])]
    eq(len(_fam), 1 + 3 * len(YEARS), "   the quiet tree holds every college-injury row (the probe and %d stored "
       "files), so the check below asks about all of them" % (3 * len(YEARS)))
    eq([r["path"][len(Q):] for r in _fam if r["stale"]], [],
       "⛔ a quiet week (nothing changed for five days, the reader ran ten minutes ago) leaves no college-injury "
       "row stale")

    # ══════════════════════════════════════════════════════════════════
    section("3. 🔴 THE MODE: FREE, COLLEGE ONLY, PINNED THERE, AND IT RUNS THE READER")
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
    M = tree()
    with inside(M):
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
        ck(len(CALLS) == 1 and CALLS[0][0] == "." and norm(CALLS[0][1]) == norm(M),
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

    # ══════════════════════════════════════════════════════════════════
    section("4. 🔴 END TO END: THE READER THE ARM RUNS WRITES THE FILE ITS ROW WATCHES")
    # ══════════════════════════════════════════════════════════════════
    # The real cfb_injuries.run on a planted tree, at the real clock. The
    # contract is asked at the instant the reader stamped its probe, so the
    # reader and the contract read ONE clock and the top of an hour falling
    # between the two calls cannot decide the verdict. ⛔ Offline: every source
    # call raises.
    NET = []

    def offline(*a, **k):
        NET.append(a[:1])
        raise urllib.error.URLError("offline: a test makes no network call")

    CI.run, CI._post, CI._get = _REAL_RUN, offline, offline
    E = tree()
    with inside(E):
        _t0 = datetime.datetime.now(UTC)
        _before = F.plan("data/ncaaf", "picks", _t0)[0]
        _out = io.StringIO()
        with contextlib.redirect_stdout(_out):
            C.run_mode("cfb-injuries")
        _probes = sorted(os.listdir("data/ncaaf/latest")) if os.path.isdir("data/ncaaf/latest") else []
        _built = [F.stamp_of(os.path.join("data/ncaaf/latest", n)) for n in _probes
                  if n.startswith("injuries-probe-")]
        _t1 = _built[0] if len(_built) == 1 and _built[0] else datetime.datetime.now(UTC)
        _after, _arows = F.plan("data/ncaaf", "picks", _t1)
    _p = [r for r in _arows if r["mode"] == "cfb-injuries" and not F.stored_only(r)]
    ck("cfb-injuries" in _before and "cfb-injuries" not in _after and len(_p) == 1 and not _p[0]["stale"],
       "🔴 planned before the reader ran, satisfied after: its probe is the file its row watches",
       "before %s, after %s" % ("cfb-injuries" in _before, "cfb-injuries" in _after))
    ck(any(l.startswith("::warning::cfb-injuries read nothing for ncaaf") for l in lines(_out)),
       "   ...and a pass that stored nothing (no stored schedule here) says so as an annotation",
       shown([l for l in lines(_out) if l.startswith("::")]))
    note("source calls attempted offline: %d" % len(NET))

    # ══════════════════════════════════════════════════════════════════
    section("5. ⛔ A READER THAT RAISES IS NOT A CRASH OF THE PASS")
    # ══════════════════════════════════════════════════════════════════
    def boom(root=None, now=None, post=None, get=None, log=print):
        raise RuntimeError("the reader blew up")

    CI.run = boom
    X = tree()
    open(X + "/data/ncaaf/latest/props.json.gz", "wb").close()     # the card rows exist
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
finally:
    CI.run, CI._post, CI._get = _REAL_RUN, _REAL_POST, _REAL_GET
    for _t in TREES:
        shutil.rmtree(_t, ignore_errors=True)
