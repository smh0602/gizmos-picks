#!/usr/bin/env python3
r"""test_injury_check.py — THE GAME-DAY INJURY CHECK: 9AM, 12PM, 7PM ET. `[Sam, 2026-10-26]`

Sam: *"make sure we're looking at injury status at 12pm of games starting and 7pm so we can make
sure the models adjusted for injuries when deciding outcome for a vame"*; asked whether college's
adjustment should read the 12pm/7pm reports or the 9am one it was tested on: *"do 9am, 12pm, 7pm"*.

It asks:
  1. the slots are REAL Eastern time (9:00 = 13:00Z under daylight time, 14:00Z from 2026-11-01;
     12:00 = 16:00Z / 17:00Z; 19:00 = 23:00Z / 00:00Z), from ONE rule (freshness.et_wall_utc,
     fb_weather's), and an NFL kickoff reads the same with or without a tz database;
  2. the `injury-check` row plans the check at 9:05, 12:05 and 19:05 ET on an NFL Sunday,
     Monday night, Thursday night and a college Saturday; never on a day without a game, never
     before the slot, never for a slot whose games have all started; card-fb follows it in the
     same plan (and does NOT follow the college reader's every-pass); it is soft, never in
     lateness.json, and the hourly news cron reaches every slot within 20 minutes (no cron change);
  3. the mode: free, both football leagues, writes its probe on every attempt; the NFL half keeps a
     dated snapshot ONLY when the statuses or inactives changed, never rewrites an unchanged
     injuries file, records a failed source without raising, honours nfl-logs' back-off; college
     reads the reports once per slot;
  4. college's model reading (Sam's "do 9am, 12pm, 7pm"): a game still to start reads the newest
     report as of the build; a started or final game, and every caller that passes no moment (the
     training rows, fb_inj_backtest), reads §3's tested 9:00 cut; `[2026-10-26, review]` a played
     game is ALSO read as of its last pre-kickoff build (the ledger's last snapshot that looked at
     it) into `inj_shown`, which the record's replay reads (test_fb_model_record.py §5);
     `[2026-10-27, review 2]` at that build's OWN moment (a property over 120 build moments: the
     replay reads what the live build read), dated by the model's reading (`read_at`);
  5. `[2026-10-26, review]` what the reviews found: the injuries file keeps its 3am deadline
     (nfl-logs rewrites it daily; only the check skips an unchanged rewrite), an empty nflverse
     answer is a failed source, a refused releases call is not repeated, a check that read
     nothing is retried ONCE in its slot, a source failing at 2 slots in a row is a warning that
     is never replanned, a season with no stored schedule owes nothing, and every slot's attempts
     are logged for the Monday status ("N of M checks ran").

PLANTED TREES ONLY, each pinned to its own clock. ⛔ The network is a tripwire: nflverse and the
conference feeds are stand-ins, and a real call fails the file.

# @vacuity 🔴 the noon slot is one of the three
#   file: freshness.py
#   find: INJURY_CHECK_ET = ((9, 0), (12, 0), (19, 0))
#   with: INJURY_CHECK_ET = ((9, 0), (19, 0))
#
# @vacuity 🔴 the slots are real Eastern time, not the contract's fixed UTC-4
#   file: freshness.py
#   find:     return (naive - datetime.timedelta(hours=_us_eastern_offset(naive))).replace(tzinfo=UTC)
#   with:     return (naive + datetime.timedelta(hours=4)).replace(tzinfo=UTC)
#
# @vacuity 🔴 a platform without a tz database reads an NFL kickoff by the same rule
#   file: freshness.py
#   find:             k = et_wall_utc(t)          # ~~t.replace(tzinfo=UTC) + ET_OFFSET~~ [2026-10-26]
#   with:             k = t.replace(tzinfo=UTC) + ET_OFFSET
#
# @vacuity ⛔ freshness.py imports no other repo module (sandboxes copy it alone)
#   file: freshness.py
#   find:     return (naive - datetime.timedelta(hours=_us_eastern_offset(naive))).replace(tzinfo=UTC)
#   with:     import fb_weather; return (naive - datetime.timedelta(hours=_us_eastern_offset(naive))).replace(tzinfo=UTC)
#
# @vacuity ⛔ never on a day without a game after the slot
#   file: freshness.py
#   find:         if kicks is None or any(k > slot for k in kicks):
#   with:         if True:
#
# @vacuity ⛔ a slot whose later games have all started is owed nothing
#   file: freshness.py
#   find:     kicks = None if games is None else [k for k, _g in games if start <= k < end and k > now]
#   with:     kicks = None if games is None else [k for k, _g in games if start <= k < end]
#
# @vacuity 🔴 a Moments deadline is the newest moment at or before now
#   file: freshness.py
#   find:         return max((m for m in times_et if m <= now), default=None)
#   with:         return None
#
# @vacuity 🔴 the card is rebuilt after the check, in the same pass
#   file: freshness.py
#   find:     "injury-check":  ["card-fb"],
#   with:     "injury-check":  [],
#
# @vacuity 🔴 a failed check is a warning, never a red run
#   file: freshness.py
#   find: SOFT |= {"injury-check"}
#   with: SOFT |= set()
#
# @vacuity ⛔ GitHub's start delay is not a lateness finding about the check
#   file: freshness.py
#   find: UNTIMED = {"injury-check"}
#   with: UNTIMED = set()
#
# @vacuity 🔴 injuries-<season> keeps its 3am deadline (an nflverse outage reads stale) [2026-10-26, review]
#   file: freshness.py
#   find:         _store += [(f"injuries-{s}", T["possession"] if s == season else []) for s in _yrs]
#   with:         _store += [(f"injuries-{s}", []) for s in _yrs]
#
# @vacuity 🔴 nfl-logs' daily call rewrites the injuries file, changed or not (its heartbeat)
#   file: nfl.py
#   find: def store_injuries(base, seasons, log=print, now=None, fetch_rows=None, only_on_change=False):
#   with: def store_injuries(base, seasons, log=print, now=None, fetch_rows=None, only_on_change=True):
#
# @vacuity 🔴 the check's call does not rewrite an unchanged injuries file
#   file: nfl.py
#   find:             if only_on_change and _same_but_stamp(old, doc):     # `[2026-10-26]` the check's call
#   with:             if False:
#
# @vacuity 🔴 ...because the check asks for it
#   file: nfl.py
#   find:                                                   only_on_change=True)[season]
#   with:                                                   only_on_change=False)[season]
#
# @vacuity ⛔ an empty nflverse answer is a failed source, never every player cleared
#   file: nfl.py
#   find:                     raise ValueError("answered with no rows for %s" % season)
#   with:                     pass
#
# @vacuity ⛔ a refused releases call is not repeated for the second source
#   file: nfl.py
#   find:                         raise seen[1]
#   with:                         pass
#
# @vacuity 🔴 an NFL snapshot only when the statuses or inactives changed
#   file: nfl.py
#   find:         if prev is not None and (prev.get("season"), prev.get("week"), prev.get("teams")) == \
#   with:         if False and (prev.get("season"), prev.get("week"), prev.get("teams")) == \
#
# @vacuity 🔴 the game-day inactives are kept
#   file: nfl.py
#   find:                 and (r.get("status") or "").strip().upper() == INACTIVE:
#   with:                 and False:
#
# @vacuity ⛔ half a reading is never stored as a change
#   file: nfl.py
#   find:         if len(rows) < 2 or out["week"] is None:
#   with:         if out["week"] is None:
#
# @vacuity 🔴 the mode needs no Odds key
#   file: collect.py
#   find:             "injury-check",
#   with:             "cfb-teams",
#
# @vacuity ⛔ the mode is dispatched (converge runs the mode a row names)
#   file: collect.py
#   find:         elif mode == "injury-check":
#   with:         elif mode == "injury-check-DISABLED":
#
# @vacuity 🔴 the probe is written on every attempt
#   file: collect.py
#   find:     write(f"{LATEST}/injury-check.json", probe)
#   with:     pass
#
# @vacuity ⛔ a check never feeds an nflverse rate-limit storm (nfl-logs' back-off)
#   file: collect.py
#   find:             if wait > 0:
#   with:             if False:
#
# @vacuity ⛔ college reads the reports once per slot (the reader's run in this pass is reused)
#   file: collect.py
#   find:             if served is not None and ran is not None and ran >= served[1]:
#   with:             if False:
#
# @vacuity 🔴 a check that read nothing says so in its probe (`ok`)
#   file: collect.py
#   find:     probe["ok"] = bool(not probe.get("error") and any((v or {}).get("ok") for v in _src.values()))
#   with:     probe["ok"] = True
#
# @vacuity 🔴 a failing source's slots accumulate (the health check's evidence)
#   file: collect.py
#   find:             fs = [x for x in (p.get("failing_slots") or []) if x != _key][-5:] + [_key]
#   with:             fs = [_key]
#
# @vacuity 🔴 the slot log records only a check that read something as having run
#   file: collect.py
#   find:         e["ok_at"] = e.get("ok_at") or (ts if probe["ok"] else None)
#   with:         e["ok_at"] = ts
#
# @vacuity 🔴 ...from the probe's first check, carried forward
#   file: collect.py
#   find:     probe["log_since"] = prev.get("log_since") or ts        # the first check this probe recorded
#   with:     probe["log_since"] = ts
#
# @vacuity 🔴 a failed check is retried in its slot
#   file: freshness.py
#   find:                 and (sl.get("attempt") or 1) <= INJURY_RETRIES):
#   with:                 and False):
#
# @vacuity ⛔ ...once, never every pass
#   file: freshness.py
#   find: INJURY_RETRIES = 1
#   with: INJURY_RETRIES = 99
#
# @vacuity 🔴 a source failing at 2 slots in a row is named
#   file: freshness.py
#   find:         if n >= INJURY_FAILED_SLOTS:
#   with:         if False:
#
# @vacuity ⛔ ...only while the checks are running (the off-season is no warning)
#   file: freshness.py
#   find:     if at is None or now - at > datetime.timedelta(days=IN_SEASON_D):
#   with:     if at is None:
#
# @vacuity ⛔ ...and it is reported, never replanned (no card rebuild every pass)
#   file: freshness.py
#   find: REPORT_ONLY_HEALTH = {"injury-check"}
#   with: REPORT_ONLY_HEALTH = set()
#
# @vacuity ⛔ a season with no stored schedule owes nothing
#   file: freshness.py
#   find:     if not os.path.exists(path):          # no stored schedule for the season: nothing owed
#   with:     if False:
#
# @vacuity 🔴 a Moments deadline's next moment is the first one after now
#   file: freshness.py
#   find:         return min((m for m in times_et if m > now), default=None)
#   with:         return None
#
# @vacuity 🔴 the Monday status counts a slot that never ran
#   file: status.py
#   find:         missed = [h for h in hist if not h["ok_at"] and not h["attempts"]]
#   with:         missed = []
#
# @vacuity ⛔ ...but never one before the probe's first check
#   file: status.py
#   find:                 and (h["utc"] in log or first is None or F._parse(h["utc"]) >= first)]
#   with:                 ]
#
# @vacuity 🔴 a college game still to start reads the newest report as of the build
#   file: cfb_injuries.py
#   find:     return max(cut, now)
#   with:     return cut
#
# @vacuity ⛔ a game that has kicked off keeps §3's 9:00 cut
#   file: cfb_injuries.py
#   find:     if cut is None or now is None or k is None or k <= now:
#   with:     if cut is None or now is None or k is None:
#
# @vacuity 🔴 a played game is read as of ITS moment when one is given (the record's replay)
#   file: cfb_injuries.py
#   find:                 cut = (shown_cut(r.get("kickoff"), when[gid]) if gid in when      # the replay: at its build
#   with:                 cut = (read_cut(r.get("kickoff"), now) if gid in when      # the replay: at its build
#
# @vacuity 🔴 [2026-10-27, review 2] ...at that build's own moment, never a later 9:00 cut (the property)
#   file: cfb_injuries.py
#   find:                 cut = (shown_cut(r.get("kickoff"), when[gid]) if gid in when      # the replay: at its build
#   with:                 cut = (read_cut(r.get("kickoff"), when[gid]) if gid in when      # the replay: at its build
#
# @vacuity ⛔ [2026-10-27, review 2] ...and a game that had kicked off by that build keeps §3's cut, as live
#   file: cfb_injuries.py
#   find:     if t is None or k is None or k <= t:
#   with:     if t is None or k is None:
#
# @vacuity 🔴 ...into `inj_shown`, beside the 9:00 reading
#   file: cfb_injuries.py
#   find:                 r["sig"]["inj_shown"] = _reading(shown, r, roles)
#   with:                 pass
#
# @vacuity 🔴 ...at the ledger's last snapshot before kickoff, on the live build
#   file: fb_model.py
#   find:             shown = fb_ledger.looked_moments(lg, root)
#   with:             shown = None
#
# @vacuity 🔴 [2026-10-27, review 2] fb-model.json says when its rows read the injury reports
#   file: fb_model.py
#   find:            "read_at": (now if now.tzinfo else now.replace(tzinfo=datetime.timezone.utc))
#   with:            "read_at_": (now if now.tzinfo else now.replace(tzinfo=datetime.timezone.utc))
#
# @vacuity 🔴 [2026-10-27, review 2] ...the ledger's snapshot copies it
#   file: fb_ledger.py
#   find:         doc["model_read_at"] = gm["read_at"]
#   with:         pass
#
# @vacuity 🔴 [2026-10-27, review 2] ...and the replay is dated by it, never by the snapshot's later minute
#   file: fb_ledger.py
#   find:             out[gid] = r if isinstance(r, str) and r <= taken else taken
#   with:             out[gid] = taken
#
# @vacuity ⛔ [2026-10-27, review 2] ...nor by a reading stamped after its snapshot
#   file: fb_ledger.py
#   find:             out[gid] = r if isinstance(r, str) and r <= taken else taken
#   with:             out[gid] = r if isinstance(r, str) else taken
#
# @vacuity 🔴 the live build passes its moment to the rows
#   file: fb_model.py
#   find:     rows = build_rows(lg, root, extra_top, extra_players, ratings=own, inj_now=now)
#   with:     rows = build_rows(lg, root, extra_top, extra_players, ratings=own)
#
# @vacuity ⛔ no training or backtest caller passes the live moment (fb_inj_backtest)
#   file: fb_inj_backtest.py
#   find:         rows = F.build_rows(lg, root)
#   with:         rows = F.build_rows(lg, root, inj_now=time.time())
"""
import ast
import contextlib
import datetime
import glob
import gzip
import importlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from tcheck import ck, eq, note, section, shown  # noqa: E402

os.environ["LEAGUE"] = "nfl"
os.environ["ODDS_API_KEY"] = ""          # ⛔ keys blank: a FREE mode must not need one
import cfb_injuries as CI  # noqa: E402
import daystore  # noqa: E402
import freshness as F  # noqa: E402
import nfl  # noqa: E402

UTC = datetime.timezone.utc
M, H, D = datetime.timedelta(minutes=1), datetime.timedelta(hours=1), datetime.timedelta(days=1)
TREES = []
NET = []


def Z(s):
    """'2026-10-25 16:05' (UTC) -> aware UTC."""
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def tripwire(*a, **k):
    NET.append(a[:1])
    raise AssertionError("a test made a network call: %r" % (a[:1],))


_REAL = {"urlopen": urllib.request.urlopen, "raw": nfl._raw, "releases": nfl._releases, "rows": nfl._rows,
         "ci_run": CI.run}
urllib.request.urlopen = tripwire
nfl._raw = tripwire


def tree():
    d = tempfile.mkdtemp(prefix="injchk-")
    TREES.append(d)
    for lg in ("nfl", "ncaaf"):
        os.makedirs(os.path.join(d, "data", lg, "latest"))
    os.makedirs(os.path.join(d, "picks"))
    return d


def put(path, doc):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if path.endswith(".gz"):
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(doc, fh)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)


def nfl_sched(root, starts, week=8):
    """NFL kickoffs as nflverse stores them: ET wall clock, no zone. `starts`: [(start, week)] or
    [start] (this `week`)."""
    games = []
    for i, s in enumerate(starts):
        s, wk = (s, week) if isinstance(s, str) else s
        games.append({"id": "2026_%02d_A%d_H%d" % (wk, i, i), "week": wk, "start": s, "home": "H%d" % i,
                      "away": "A%d" % i, "home_class": None, "away_class": None})
    put(os.path.join(root, "data", "nfl", "latest", "schedule-2026.json.gz"), {"season": 2026, "games": games})


def cfb_sched(root, starts_utc, fbs=True):
    """College kickoffs as CFBD stores them: real UTC with a Z."""
    put(os.path.join(root, "data", "ncaaf", "latest", "schedule-2026.json.gz"),
        {"season": 2026, "games": [{"id": str(i), "start": s, "home": "H%d" % i, "away": "A%d" % i,
                                    "home_class": "fbs" if fbs else "fcs", "away_class": "fbs" if fbs else "fcs"}
                                   for i, s in enumerate(starts_utc)]})


def probe_at(root, lg, built):
    p = os.path.join(root, "data", lg, "latest", "injury-check.json")
    if built is None:
        if os.path.exists(p):
            os.remove(p)
        return p
    put(p, {"league": lg, "built_at": iso(built), "checked_at": iso(built)})
    return p


def planned(root, lg, t):
    return F.plan(root + "/data/" + lg, root + "/picks", t)[0]


@contextlib.contextmanager
def inside(d):
    cwd = os.getcwd()
    os.chdir(d)
    try:
        yield
    finally:
        os.chdir(cwd)


try:
    # ══════════════════════════════════════════════════════════════════
    section("1. 🔴 THE SLOTS ARE REAL EASTERN TIME, FROM ONE RULE")
    # ══════════════════════════════════════════════════════════════════
    eq(F.INJURY_CHECK_ET, ((9, 0), (12, 0), (19, 0)), "🔴 ONE constant holds the three slots: 9am, 12pm, 7pm ET")
    _want = {"2026-10-25": ["2026-10-25 13:00", "2026-10-25 16:00", "2026-10-25 23:00"],      # EDT
             "2026-11-01": ["2026-11-01 14:00", "2026-11-01 17:00", "2026-11-02 00:00"]}      # EST
    for _day, _w in _want.items():
        _d = datetime.date.fromisoformat(_day)
        eq([F.et_wall_utc(datetime.datetime(_d.year, _d.month, _d.day, h, m)) for h, m in F.INJURY_CHECK_ET],
           [Z(x) for x in _w], "🔴 %s (%s): 9:00 / 12:00 / 19:00 ET are %s UTC" % (
               _day, "EDT" if _day < "2026-11-01" else "EST", " / ".join(x[-5:] for x in _w)))
    _saved_zone = F._et_zone
    for _label, _zone in (("with the tz database", _saved_zone), ("WITHOUT a tz database (Windows)", lambda: None)):
        P = tree()
        nfl_sched(P, ["2026-10-25T13:00", "2026-11-01T13:00", "2026-11-01T20:20"])
        F._et_zone = _zone
        try:
            _k = sorted(F.kickoffs_utc("nfl", os.path.join(P, "data", "nfl", "latest", "schedule-2026.json.gz")))
        finally:
            F._et_zone = _saved_zone
        eq(_k, [Z("2026-10-25 17:00"), Z("2026-11-01 18:00"), Z("2026-11-02 01:20")],
           "🔴 an NFL kickoff (ET wall clock) %s: 1pm is 17:00Z in October, 18:00Z in November" % _label)
    # ⛔ `[2026-10-26]` FRESHNESS.PY STANDS ALONE: tests and the gate copy it into sandboxes by
    #    itself (test_source_block.py, test_card_refusal.py), and its first build of this check
    #    imported the DST rule from fb_weather.py, so every football contract in such a sandbox
    #    died on an ImportError. The rule lives in freshness.py; fb_weather.py reads it from there.
    import subprocess  # noqa: E402
    S = tree()
    shutil.copy2(os.path.join(ROOT, "freshness.py"), os.path.join(S, "freshness.py"))
    nfl_sched(S, ["2026-11-01T13:00"])
    _code = ("import sys, datetime; sys.path.insert(0, %r); import freshness as F; "
             "n = datetime.datetime(2026, 11, 1, 17, 5, tzinfo=datetime.timezone.utc); "
             "print([r[0] for r in F.contract('data/nfl', 'picks', n)][:1], "
             "F.injury_check_slots('nfl', 'data/nfl/latest', n)[1][1].strftime('%%H:%%MZ'))" % S)
    _r = subprocess.run([sys.executable, "-E", "-s", "-c", _code], cwd=S, capture_output=True, text=True,
                        timeout=120)
    ck((_r.returncode, _r.stdout.strip()) == (0, "['injury-check'] 17:00Z"),
       "⛔ freshness.py ALONE in a directory (no other repo module) builds a football contract with the "
       "check's real-ET slots", "rc %s, %r: %s" % (_r.returncode, _r.stdout.strip(),
                                                    shown((_r.stderr or "").strip().splitlines()[-2:])))

    # ══════════════════════════════════════════════════════════════════
    section("2. 🔴 THE ROW PLANS THE CHECK AT 9:05, 12:05 AND 19:05 ET ON A GAME DAY, AND ONLY THEN")
    # ══════════════════════════════════════════════════════════════════
    _cases = [
        ("NFL Sunday 10-25", "nfl", ["2026-10-25T13:00", "2026-10-25T16:25", "2026-10-25T20:20"], None,
         ["2026-10-25 13:00", "2026-10-25 16:00", "2026-10-25 23:00"]),
        ("NFL Monday night 10-26", "nfl", ["2026-10-26T20:15"], None,
         ["2026-10-26 13:00", "2026-10-26 16:00", "2026-10-26 23:00"]),
        ("NFL Thursday night 10-22", "nfl", ["2026-10-22T20:15"], None,
         ["2026-10-22 13:00", "2026-10-22 16:00", "2026-10-22 23:00"]),
        ("college Saturday 10-24", "ncaaf", None,
         ["2026-10-24T16:00:00.000Z", "2026-10-24T19:30:00.000Z", "2026-10-24T23:30:00.000Z"],
         ["2026-10-24 13:00", "2026-10-24 16:00", "2026-10-24 23:00"]),
    ]
    for _label, _lg, _nfl, _cfb, _slots in _cases:
        P = tree()
        nfl_sched(P, _nfl or []) if _lg == "nfl" else cfb_sched(P, _cfb)
        _miss, _extra = [], []
        for _s in _slots:
            s = Z(_s)
            probe_at(P, _lg, s - M)                     # the last check was a minute before the slot
            if "injury-check" not in planned(P, _lg, s + 5 * M):
                _miss.append(_s[-5:])
            probe_at(P, _lg, s + 2 * M)                 # ...and one made two minutes after it
            if "injury-check" in planned(P, _lg, s + 5 * M):
                _extra.append(_s[-5:])
        ck(not _miss, "🔴 %s: planned 5 minutes after each slot (%s UTC)" % (_label, ", ".join(x[-5:] for x in _slots)),
           "not planned after: %s" % _miss)
        ck(not _extra, "   ...and not again once a check has been made after the slot", "planned again: %s" % _extra)
        probe_at(P, _lg, Z(_slots[0]) - 15 * H)          # last night's check
        ck("injury-check" not in planned(P, _lg, Z(_slots[0]) - 5 * M),
           "   ...and not before the first slot (8:55 ET) though the last check was last night")

    # ⛔ NOT BEFORE THE SLOT, NOT ON A DAY WITHOUT A GAME, NOT FOR A SLOT WHOSE GAMES ALL STARTED
    P = tree()
    nfl_sched(P, ["2026-10-25T13:00", "2026-10-26T20:15", "2026-10-29T20:15"])     # Sun 1pm, MNF, TNF
    probe_at(P, "nfl", Z("2026-10-25 13:10"))                                      # the 9am check, made
    ck("injury-check" not in planned(P, "nfl", Z("2026-10-25 15:55")),
       "⛔ not before the slot: 11:55 ET, the 9:00 check made at 9:10")
    ck("injury-check" in planned(P, "nfl", Z("2026-10-25 16:05")),
       "   ...and at 12:05 ET it is due (the 1pm games are still to start)")
    probe_at(P, "nfl", Z("2026-10-25 12:00"))                                      # 8am: before both
    ck("injury-check" not in planned(P, "nfl", Z("2026-10-25 17:30")),
       "⛔ 1:30 ET with only 1pm games, the 9am and noon checks never made: every game after them has "
       "started, so neither is owed (a late pass does no pointless work)")
    ck("injury-check" not in planned(P, "nfl", Z("2026-10-25 23:05")),
       "⛔ 7:05 ET on a Sunday with no night game: the 7pm slot has no game after it")
    eq(F.injury_check_slots("nfl", P + "/data/nfl/latest", Z("2026-10-25 17:30")), [],
       "   ...the day's slots are all done once its last game has started")
    probe_at(P, "nfl", Z("2026-10-26 23:30"))                                      # Monday's last check
    ck(all("injury-check" not in planned(P, "nfl", Z("2026-10-27 %s" % h)) for h in ("13:05", "16:05", "23:05")),
       "⛔ Tuesday (no NFL game): not at 9:05, 12:05 or 19:05 ET")
    Q = tree()
    cfb_sched(Q, ["2026-10-25T18:00:00.000Z", "2026-10-25T23:30:00.000Z"], fbs=False)
    probe_at(Q, "ncaaf", Z("2026-10-24 23:30"))
    ck(all("injury-check" not in planned(Q, "ncaaf", Z("2026-10-25 %s" % h)) for h in ("13:05", "16:05", "23:05")),
       "⛔ a college day with FCS games only (no FBS side): never owed, as no college row prices one")

    # 🔴 DAYLIGHT TIME ENDS 2026-11-01: THE NOON CHECK IS 17:00Z, THE 9AM ONE 14:00Z
    P = tree()
    nfl_sched(P, ["2026-11-01T13:00", "2026-11-01T20:20"])
    probe_at(P, "nfl", Z("2026-10-31 23:00"))
    eq(("injury-check" in planned(P, "nfl", Z("2026-11-01 13:55")),
        "injury-check" in planned(P, "nfl", Z("2026-11-01 14:05"))), (False, True),
       "🔴 2026-11-01 (EST): the 9am check is 14:00Z: not at 13:55Z, yes at 14:05Z")
    probe_at(P, "nfl", Z("2026-11-01 14:10"))
    eq(("injury-check" in planned(P, "nfl", Z("2026-11-01 16:30")),
        "injury-check" in planned(P, "nfl", Z("2026-11-01 17:05"))), (False, True),
       "🔴 ...the noon check is 17:00Z: a 16:30Z pass does NOT run it (11:30 EST), a 17:05Z pass does")
    eq([(l, m) for l, m in F.injury_check_slots("nfl", P + "/data/nfl/latest", Z("2026-11-01 17:05"))],
       [("9:00", Z("2026-11-01 14:00")), ("12:00", Z("2026-11-01 17:00")), ("19:00", Z("2026-11-02 00:00"))],
       "   ...and the 7pm check is 00:00Z the next UTC day")
    P = tree()
    nfl_sched(P, ["2026-10-25T13:00", "2026-10-25T20:20"])
    probe_at(P, "nfl", Z("2026-10-24 23:00"))
    eq(("injury-check" in planned(P, "nfl", Z("2026-10-25 12:55")),
        "injury-check" in planned(P, "nfl", Z("2026-10-25 13:05"))), (False, True),
       "🔴 2026-10-25 (EDT): the 9am check is 13:00Z")
    probe_at(P, "nfl", Z("2026-10-25 13:10"))
    eq(("injury-check" in planned(P, "nfl", Z("2026-10-25 15:55")),
        "injury-check" in planned(P, "nfl", Z("2026-10-25 16:05"))), (False, True),
       "🔴 ...and the noon check 16:00Z")

    # ⛔ AFTER THE LAST KICKOFF NOTHING IS OWED, so a check GitHub never ran is no stopped league
    probe_at(P, "nfl", Z("2026-10-25 16:30"))
    _r = [r for r in F.survey(P + "/data/nfl", P + "/picks", Z("2026-10-26 00:40"))
          if r["mode"] == "injury-check"]
    ck(len(_r) == 1 and _r[0]["stale"] is False and _r[0]["due_at"] is None,
       "⛔ 8:40 ET Sunday, the 7pm check never made but the night game has started: not stale, no "
       "deadline (no `stopped:` finding, no warning)", _r)

    # ══════════════════════════════════════════════════════════════════
    section("2b. 🔴 THE CARD IS REBUILT AFTER THE CHECK, IN THE SAME PASS (and only after it)")
    # ══════════════════════════════════════════════════════════════════
    _src = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
    _body = _src[_src.index("\ndef run_mode("):]
    _body = _body[:_body.index("\ndef ", 1)]
    _arms = re.split(r'(?m)^        (?:el)?if mode == "([^"]+)":', _body)
    CARD_MODES = {_arms[i] for i in range(1, len(_arms) - 1, 2) if "build_card_fb(" in _arms[i + 1]}
    ck(CARD_MODES >= {"props-player", "card-fb"}, "   the card-building modes are read off run_mode's arms",
       sorted(CARD_MODES))

    def fresh_card(root, lg, t):
        """Every card-fb row's file built a minute ago (cwd = root: the card path is relative)."""
        for m, (_k, p), *_ in F.contract("data/" + lg, "picks", t):
            if m == "card-fb":
                put(p, {"built_at": iso(t - M)})

    for _lg, _day in (("nfl", "2026-10-25"), ("ncaaf", "2026-10-24")):
        P = tree()
        nfl_sched(P, ["2026-10-25T20:20"]) if _lg == "nfl" else cfb_sched(P, ["2026-10-24T23:30:00.000Z"])
        open(os.path.join(P, "data", _lg, "latest", "props.json.gz"), "wb").close()  # the card rows exist
        t = Z(_day + " 16:05")
        with inside(P):
            fresh_card(P, _lg, t)
            _modes = [r[0] for r in F.contract("data/" + _lg, "picks", t)]
            _first = _modes.index("injury-check")
            _late = sorted(m for m in CARD_MODES if m in _modes and _modes.index(m) < _first)
            ck(not _late, "🔴 %s: the check comes before every card-building mode (%s)"
               % (_lg, ", ".join(sorted(CARD_MODES))), "built before it: %s" % _late)
            probe_at(".", _lg, t - 2 * H)
            _plan = F.plan("data/" + _lg, "picks", t)[0]
            ck("card-fb" in _plan and _plan.index("injury-check") < _plan.index("card-fb"),
               "🔴 %s: a due check plans card-fb after it, though the card itself is inside its deadline" % _lg,
               _plan)
            probe_at(".", _lg, t - M)
            _plan = F.plan("data/" + _lg, "picks", t)[0]
            ck("card-fb" not in _plan and "injury-check" not in _plan,
               "   ...and a check already made plans no card rebuild", _plan)
            if _lg == "ncaaf":
                ck("cfb-injuries" in _plan and "card-fb" not in _plan,
                   "⛔ the college reader planned on this pass (Saturday: every pass) does NOT pull the card "
                   "after it", _plan)
    eq(sorted(F.CASCADE.get("cfb-injuries") or []), [], "⛔ ...nothing cascades from the college reader")
    eq(F.CASCADE.get("injury-check"), ["card-fb"], "🔴 the check cascades to card-fb, and only to it")

    # ══════════════════════════════════════════════════════════════════
    section("2c. ⛔ SOFT, NEVER LATE IN lateness.json, AND NO CRON CHANGE")
    # ══════════════════════════════════════════════════════════════════
    P = tree()
    nfl_sched(P, ["2026-10-25T20:20"])
    probe_at(P, "nfl", Z("2026-10-25 12:00"))
    _r = [r for r in F.survey(P + "/data/nfl", P + "/picks", Z("2026-10-25 16:05"))
          if r["mode"] == "injury-check"]
    _hard, _soft = F.classify(_r, P + "/data/nfl", refused=False, block={"state": None})
    ck(len(_r) == 1 and _r[0]["stale"] and not _hard and len(_soft) == 1,
       "🔴 a stale check is a WARNING (soft), never a red run: the card it cascades to stays hard",
       "hard=%d soft=%d" % (len(_hard), len(_soft)))
    ck(not _r[0]["paid"] if _r else False, "   ...and free: a paid-pull budget never skips it")
    _lp = os.path.join(P, "data", "nfl", "latest", F.LATENESS_FILE)
    _rows = [{"mode": "injury-check", "path": "x/injury-check.json", "due_at": "2026-10-25T23:00Z",
              "stale": False, "age_min": 1.0},
             {"mode": "card-fb", "path": "x/fb-model.json", "due_at": "2026-10-25T15:30Z", "stale": False,
              "age_min": 1.0}]
    F.record_builds(_rows, _lp, Z("2026-10-26 01:25"))          # the 7pm check built 145 minutes late
    _arts = json.load(open(_lp, encoding="utf-8"))["artifacts"]
    ck(not any(v["mode"] == "injury-check" for v in _arts.values())
       and any(v["mode"] == "card-fb" for v in _arts.values()),
       "⛔ lateness.json never records the check (a 145-minute GitHub delay is no `late:` finding); the card "
       "beside it is still recorded", sorted(v["mode"] for v in _arts.values()))
    ck("injury-check" in F.UNTIMED and "injury-check" in F.SOFT, "   (UNTIMED and SOFT name it)")
    from wfroutes import parse_routes  # noqa: E402
    ROUTES = parse_routes(open(os.path.join(ROOT, ".github", "workflows", "collect.yml"), encoding="utf-8").read())
    ck(ROUTES and not any("injury-check" in ms.split() for _c, _l, ms in ROUTES),
       "🔴 NO CRON names the mode: converge plans it from its row (no workflow upload for Sam)")

    def _set(spec, lo, hi):
        out = set()
        for part in spec.split(","):
            rng, _, step = part.partition("/")
            a, b = (lo, hi) if rng == "*" else (tuple(int(x) for x in rng.split("-")) if "-" in rng
                                                 else (int(rng), int(rng) if not step else hi))
            out |= set(range(a, b + 1, int(step or 1)))
        return out

    def fires(cron, t):
        mi, hh, dom, mon, dow = cron.split()
        d_ok = dom == "*" or t.day in _set(dom, 1, 31)
        w_ok = dow == "*" or ((t.weekday() + 1) % 7) in {x % 7 for x in _set(dow, 0, 7)}
        day_ok = (d_ok or w_ok) if dom != "*" and dow != "*" else (d_ok and w_ok)
        return t.minute in _set(mi, 0, 59) and t.hour in _set(hh, 0, 23) and t.month in _set(mon, 1, 12) and day_ok

    _lag = []
    for _lg in ("nfl", "ncaaf"):
        crons = [c for c, l, ms in ROUTES if l == _lg and "news" in ms.split()]
        for _day in ("2026-10-25", "2026-11-01", "2026-12-06"):
            _d = datetime.date.fromisoformat(_day)
            for h, m in F.INJURY_CHECK_ET:
                s = F.et_wall_utc(datetime.datetime(_d.year, _d.month, _d.day, h, m))
                n = next((i for i in range(0, 21) if any(fires(c, s + i * M) for c in crons)), None)
                if n is None:
                    _lag.append("%s %s %d:%02d" % (_lg, _day, h, m))
    ck(not _lag, "🔴 every slot, daylight and standard time, both leagues, has a news cron (whose pass plans "
       "the check) within 20 minutes after it", "none within 20 min: %s" % _lag)

    # ══════════════════════════════════════════════════════════════════
    section("2d. 🔴 THE INJURIES FILE KEEPS ITS 3AM DEADLINE: AN NFLVERSE OUTAGE IS SEEN")
    # ══════════════════════════════════════════════════════════════════
    # ⛔ `[2026-10-26, review]` ~~FILES WRITTEN ONLY ON A CHANGE HAVE NO CLOCK DEADLINE~~: the first
    #    build stopped nfl-logs rewriting an unchanged injuries file and took the deadline off it, so
    #    a 10-day nflverse outage (the file 10 days old, the check's probe fresh with both sources
    #    failed) was stale nowhere, and with T69 IN champion its input could rot without a red run.
    #    Only the check skips an unchanged rewrite; nfl-logs' daily rewrite is the file's heartbeat.
    P = tree()
    nfl_sched(P, ["2026-10-25T20:20"])
    NOWO = Z("2026-10-25 16:40")                                   # Sunday 12:40 EDT
    _poss = list(F.FB_TIMES["nfl"]["possession"])
    _rows = F.contract(P + "/data/nfl", P + "/picks", NOWO)
    _inj = {re.search(r"injuries-(\d{4})", r[1][1]).group(1): list(r[2]) for r in _rows
            if re.search(r"/injuries-\d{4}\.json\.gz$", r[1][1].replace(os.sep, "/"))}
    eq(_inj, {"2025": [], "2026": _poss},
       "🔴 injuries-<this season> keeps nfl-logs' 3am deadline (a past season, written once, has none)")
    _ci = F.champion_inputs
    try:
        F.champion_inputs = lambda league, champion=None: [("injuries-{s}.json.gz", "possession")]
        _ch = [r for r in F.contract(P + "/data/nfl", P + "/picks", NOWO) if r[4] == F.CHAMPION_INPUT]
    finally:
        F.champion_inputs = _ci
    ck(len(_ch) == 1 and list(_ch[0][2]) == _poss,
       "🔴 ...and as a champion's input (T69 IN reads it), the same deadline", [(r[1][1][-21:], r[2]) for r in _ch])
    _lat = os.path.join(P, "data", "nfl", "latest")
    put(os.path.join(_lat, "injuries-2026.json.gz"), {"season": 2026, "built_at": iso(NOWO - 10 * D), "teams": {}})
    put(os.path.join(_lat, "injury-check.json"),
        {"league": "nfl", "built_at": iso(NOWO - 30 * M), "checked_at": iso(NOWO - 30 * M), "ok": False,
         "sources": {"injuries": {"ok": False, "error": "HTTPError 404"},
                     "weekly_rosters": {"ok": False, "error": "HTTPError 404"}}})
    _st = {r["path"].replace(os.sep, "/").split("/latest/")[-1]: r
           for r in F.survey(P + "/data/nfl", P + "/picks", NOWO)}
    _r = _st.get("injuries-2026.json.gz") or {}
    _hard, _soft = F.classify([_r], P + "/data/nfl", refused=False, block={"state": None}) if _r else ([], [])
    ck(_r.get("stale") and _r.get("due_at") == "2026-10-25T07:00Z" and not _hard and len(_soft) == 1,
       "🔴 a 10-day nflverse outage (file 10 days old, the check's probe fresh): injuries-2026 is STALE, a "
       "warning (stored only), though the check ran 30 minutes ago", {k: _r.get(k) for k in ("stale", "due_at")})
    try:
        F.champion_inputs = lambda league, champion=None: [("injuries-{s}.json.gz", "possession")]
        _cr = [r for r in F.survey(P + "/data/nfl", P + "/picks", NOWO) if r["why"] == F.CHAMPION_INPUT]
    finally:
        F.champion_inputs = _ci
    _hard, _soft = F.classify(_cr, P + "/data/nfl", refused=False, block={"state": None})
    ck(len(_cr) == 1 and _cr[0]["stale"] and len(_hard) == 1,
       "🔴 ...and with T69 IN champion, a RED run (its input has rotted)", "hard=%d soft=%d" % (len(_hard), len(_soft)))
    _logs = []
    _o1 = nfl.store_injuries(_lat, [2026], log=_logs.append, now=NOWO, fetch_rows=lambda s: [])
    _b = json.load(gzip.open(os.path.join(_lat, "injuries-2026.json.gz"), "rt", encoding="utf-8"))
    _o2 = nfl.store_injuries(_lat, [2026], log=_logs.append, now=NOWO + M, fetch_rows=lambda s: [])
    _b2 = json.load(gzip.open(os.path.join(_lat, "injuries-2026.json.gz"), "rt", encoding="utf-8"))
    ck(_o2[2026].startswith("written") and _b2.get("built_at") == iso(NOWO + M) and _b.get("built_at") == iso(NOWO),
       "🔴 nfl-logs' call (no only_on_change) rewrites an UNCHANGED file: its built_at is when nflverse last "
       "answered", (_o1, _o2))
    _r = {r["path"].replace(os.sep, "/").split("/latest/")[-1]: r
          for r in F.survey(P + "/data/nfl", P + "/picks", NOWO + M)}.get("injuries-2026.json.gz") or {}
    ck(_r and not _r["stale"], "   ...so after a good nfl-logs run the row is fresh again", _r.get("stale"))
    _o3 = nfl.store_injuries(_lat, [2026], log=_logs.append, now=NOWO + 2 * M, fetch_rows=lambda s: [],
                             only_on_change=True)
    ck(_o3[2026].startswith("unchanged"), "   (the check's call, only_on_change, leaves it as it is)", _o3)

    # ══════════════════════════════════════════════════════════════════
    section("3. 🔴 THE MODE: FREE, BOTH LEAGUES, ITS PROBE ON EVERY ATTEMPT")
    # ══════════════════════════════════════════════════════════════════
    import collect as C  # noqa: E402
    C._ensure_cfb_team_directory = lambda: None        # ⛔ no CFBD call for logos in a test
    ck("injury-check" not in C.MODE_LEAGUE,
       "   not pinned to one league (MODE_LEAGUE): it runs in whichever football pass plans it")
    ck("injury-check" not in C.PAID_KINDS, "💰 not a paid kind: budget.py's projection cannot move")

    def lines(buf):
        return buf.getvalue().splitlines()

    def league(lg):
        C.LEAGUE, C.DATA, C.LATEST = lg, C.LEAGUES[lg]["data"], C.LEAGUES[lg]["data"] + "/latest"

    INJ = [{"gsis_id": "p1", "full_name": "A One", "position": "WR", "team": "SEA", "week": "8",
            "report_status": "Questionable", "practice_status": "Limited Participation in Practice"},
           {"gsis_id": "p2", "full_name": "B Two", "position": "T", "team": "SEA", "week": "8",
            "report_status": "", "practice_status": "Full Participation in Practice"},
           {"gsis_id": "p3", "full_name": "C Three", "position": "RB", "team": "SEA", "week": "7",
            "report_status": "Out", "practice_status": "Did Not Participate In Practice"}]
    ROST = [{"gsis_id": "p1", "full_name": "A One", "position": "WR", "team": "SEA", "week": "8", "status": "ACT"},
            {"gsis_id": "p4", "full_name": "D Four", "position": "CB", "team": "KC", "week": "8", "status": "INA"},
            {"gsis_id": "p5", "full_name": "E Five", "position": "LB", "team": "KC", "week": "7", "status": "INA"}]
    SRC = {"injuries": INJ, "weekly_rosters": ROST}
    FAIL = set()
    CALLS = []

    def fake_releases(log=print, max_pages=10):
        CALLS.append("releases")
        return [{"tag_name": t, "assets": [{"name": n, "size": 1, "browser_download_url": "planted://" + n}]}
                for t, n in (("injuries", "injuries_2026.csv.gz"), ("weekly_rosters", "roster_weekly_2026.csv.gz"))]

    def fake_rows(seen, tag, fname, log):
        CALLS.append(tag)
        if tag in FAIL:
            raise urllib.error.HTTPError("planted://" + fname, 503, "planted outage", None, None)
        return [dict(r) for r in SRC[tag]]
    import urllib.error  # noqa: E402
    nfl._releases, nfl._rows = fake_releases, fake_rows

    N = tree()
    nfl_sched(N, [("2026-10-18T13:00", 7), "2026-10-25T13:00", "2026-10-25T16:25", "2026-10-25T20:20"])
    PIN = Z("2026-10-25 16:41")                                # 12:41 EDT, Sunday
    with inside(N):
        league("nfl")
        INJF = os.path.join("data", "nfl", "latest", "injuries-2026.json.gz")
        _p = C.collect_injury_check(at=PIN)
        _snaps = sorted(glob.glob(os.path.join("data", "nfl", "*", "injury-reports", "*.json.gz")))
        eq((_p["slot"], _p["next_slot"], _p["slots_owed_today"]),
           ({"et": "12:00", "utc": "2026-10-25T16:00Z", "attempt": 1, "late_min": 41.0},
            {"et": "19:00", "utc": "2026-10-25T23:00Z"}, ["9:00", "12:00", "19:00"]),
           "🔴 the probe names the slot it served (12:00 ET = 16:00Z, 41 minutes after it, its first attempt) "
           "and the next one")
        eq((_p["week"], _p["counts"], {k: v["ok"] for k, v in _p["sources"].items()}),
           (8, {"teams": 2, "with_status": 1, "inactive": 1}, {"injuries": True, "weekly_rosters": True}),
           "🔴 NFL: the check's week (8, today's games, not last week's 7), every player with a status, and "
           "the game-day inactives, from both nflverse files")
        _probe = json.load(open(os.path.join("data", "nfl", "latest", "injury-check.json"), encoding="utf-8"))
        ck(_probe.get("built_at") == iso(PIN) and _probe.get("checked_at") == iso(PIN),
           "   ...written to latest/injury-check.json, stamped at the check (its row's probe)",
           {k: _probe.get(k) for k in ("built_at", "checked_at")})
        _s1 = json.load(gzip.open(_snaps[0], "rt", encoding="utf-8")) if _snaps else {}
        eq(([os.path.relpath(x, "data").replace(os.sep, "/") for x in _snaps], _s1.get("week"),
            [p["full_name"] for p in ((_s1.get("teams") or {}).get("SEA") or {}).get("report", [])],
            [p["full_name"] for p in ((_s1.get("teams") or {}).get("KC") or {}).get("inactive", [])]),
           (["nfl/2026-10-25/injury-reports/1641.json.gz"], 8, ["A One"], ["D Four"]),
           "🔴 a dated snapshot through daystore: this week's statuses (Questionable) and inactives only")
        ck(_snaps and F.stored_only({"path": _snaps[0].replace(os.sep, "/")})
           and not any(os.path.normpath(r[1][1]) == os.path.normpath(_snaps[0])
                       or os.path.normpath(r[1][1]) == os.path.normpath(os.path.dirname(_snaps[0]))
                       for r in F.contract("data/nfl", "picks", PIN)),
           "⛔ STORED ONLY: freshness.STORED_ONLY names it and no contract row watches it (written only on "
           "a change; the probe row watches its writer)")
        _b1 = open(INJF, "rb").read()
        eq((_p["injuries_file"] or "")[:7], "written", "   this season's injuries file is refreshed")

        _p2 = C.collect_injury_check(at=PIN + 30 * M)
        _snaps2 = sorted(glob.glob(os.path.join("data", "nfl", "*", "injury-reports", "*.json.gz")))
        eq((_p2["changed"], len(_snaps2), _p2["snapshot"] == _snaps[0] if _snaps else None),
           (False, 1, True), "🔴 nothing changed 30 minutes later: no new snapshot, the probe names the old one")
        ck((_p2["injuries_file"] or "").startswith("unchanged") and open(INJF, "rb").read() == _b1,
           "🔴 ...and the injuries file is NOT rewritten (git cannot delta a gzip)", _p2["injuries_file"])

        INJ[0]["report_status"] = "Out"                        # A One downgraded
        _p3 = C.collect_injury_check(at=PIN + 60 * M)
        ck(_p3["changed"] and len(glob.glob(os.path.join("data", "nfl", "*", "injury-reports", "*.json.gz"))) == 2
           and (_p3["injuries_file"] or "").startswith("written") and open(INJF, "rb").read() != _b1,
           "🔴 a status changed (Questionable -> Out): a second snapshot, and the injuries file rewritten",
           (_p3["changed"], _p3["injuries_file"]))
        ROST.append({"gsis_id": "p6", "full_name": "F Six", "position": "QB", "team": "SEA", "week": "8",
                     "status": "INA"})                       # the 90-minute inactives list posted
        _p4 = C.collect_injury_check(at=PIN + 90 * M)
        eq((_p4["changed"], _p4["counts"].get("inactive")), (True, 2),
           "🔴 a game-day inactive posted (nothing else changed): a snapshot, with both inactives")

        FAIL.add("weekly_rosters")
        _n = len(glob.glob(os.path.join("data", "nfl", "*", "injury-reports", "*.json.gz")))
        _out = io.StringIO()
        with contextlib.redirect_stdout(_out):
            _p5 = C.collect_injury_check(at=PIN + 120 * M)
        ck(_p5["sources"]["weekly_rosters"]["ok"] is False and "503" in _p5["sources"]["weekly_rosters"]["error"]
           and _p5["sources"]["injuries"]["ok"] and _p5.get("why_no_snapshot") and not _p5.get("error")
           and len(glob.glob(os.path.join("data", "nfl", "*", "injury-reports", "*.json.gz"))) == _n,
           "🔴 one source down: recorded in the probe (HTTP 503), no exception, and NO snapshot (half a "
           "reading would read as every inactive cleared)", {k: _p5.get(k) for k in ("sources", "why_no_snapshot")})
        eq([l for l in lines(_out) if l.startswith("::")], [], "   ...and no annotation: the other source answered")
        FAIL.add("injuries")
        _out = io.StringIO()
        with contextlib.redirect_stdout(_out):
            _p6 = C.collect_injury_check(at=PIN + 150 * M)
        ck(any(l.startswith("::warning::injury-check read nothing for nfl") for l in lines(_out))
           and os.path.exists(os.path.join("data", "nfl", "latest", "injury-check.json")),
           "🔴 every source down: a warning annotation, and the probe still written", shown(lines(_out)[-3:]))
        FAIL.clear()

        # ⛔ nfl-logs' back-off stands: a check never adds to an nflverse rate-limit storm
        with open(os.path.join("data", "nfl", "latest", "backfill-report.txt"), "w", encoding="utf-8") as fh:
            fh.write("nfl-logs back-fill at %s\nrequested: [2026]\nwritten  : []\nfailed   : [2026]\n"
                     % C.stamp())
        del CALLS[:]
        with contextlib.redirect_stdout(io.StringIO()):         # its "read nothing" warning
            _p7 = C.collect_injury_check(at=PIN + 180 * M)
        ck(CALLS == [] and all("standing down" in (v.get("error") or "") for v in _p7["sources"].values()),
           "⛔ while nfl-logs backs off nflverse, the check fetches nothing and says why", (CALLS, _p7["sources"]))
        os.remove(os.path.join("data", "nfl", "latest", "backfill-report.txt"))

        # the mode through run_mode: no key, both leagues, nothing for MLB
        # ⛔ `[2026-10-26, review]` on the tree's own clock (PIN), never the real one: "the real
        #    clock, or a tree pinned to NOW, never one of each" (CLAUDE.md)
        _out = io.StringIO()
        _now = C.now
        try:
            C.now = lambda: PIN + 200 * M
            with contextlib.redirect_stdout(_out):
                C.run_mode("injury-check")
            _exit = None
        except SystemExit as e:
            _exit = e.code
        finally:
            C.now = _now
        _pr = json.load(open(os.path.join("data", "nfl", "latest", "injury-check.json"), encoding="utf-8"))
        eq(_pr.get("checked_at"), iso(PIN + 200 * M), "   (run_mode's check ran on the tree's pinned clock)")
        ck(_exit is None and not any("unknown mode" in l for l in lines(_out)),
           "🔴 run_mode dispatches injury-check with no Odds key (FREE): it never spends a credit",
           "exit %r: %s" % (_exit, shown(lines(_out)[-2:])))
        _out = io.StringIO()
        try:
            with contextlib.redirect_stdout(_out):
                C.run_mode("gamelines")
            _gate = None
        except SystemExit as e:
            _gate = e.code
        ck(_gate == 1, "   (the harness is live: a paid mode with no key stops at the gate)", "exit %r" % _gate)
        os.remove(os.path.join("data", "nfl", "latest", "injury-check.json"))
        league("mlb")
        with contextlib.redirect_stdout(io.StringIO()):
            C.run_mode("injury-check")
        ck(not glob.glob(os.path.join("data", "*", "latest", "injury-check.json"))
           and not os.path.exists(os.path.join("data", "latest", "injury-check.json")),
           "⛔ under MLB the arm does nothing (MLB has no injury check)")
        league("nfl")

    # 🔴 COLLEGE: the conference reports, ONCE per slot
    RAN = []

    def fake_ci_run(root=None, now=None, post=None, get=None, log=print):
        RAN.append(root)
        return {"ok": True, "sources": {"SEC": {"ok": True, "fetched_at": "x"}, "ACC": {"ok": True}}, "probe": "p"}
    CI.run = fake_ci_run
    G = tree()
    cfb_sched(G, ["2026-10-24T19:30:00.000Z", "2026-10-24T23:30:00.000Z"])
    PINC = Z("2026-10-24 16:30")                              # 12:30 EDT, Saturday
    _rep = {"game_id": "0", "home": "H0", "away": "A0", "kickoff": "2026-10-24T19:30:00Z", "source": "SEC",
            "label": "Game Day", "posted_at": "2026-10-24T16:00:00Z", "fetched_at": "2026-10-24T16:10:00Z",
            "teams": {"H0": [{"name": "Q B", "number": 1, "position": "QB", "status": "Out"}],
                      "A0": [{"name": "W R", "number": 2, "position": "WR", "status": "Questionable"}]},
            "listed": True}
    with inside(G):
        league("ncaaf")
        daystore.archive({"kind": "cfb-injury-reports", "season": 2026, "fetched_at": "2026-10-24T16:10:00Z",
                          "sources": {}, "reports": [_rep], "refused": []}, os.path.join("data", "ncaaf"),
                         "injury-reports", log=lambda m: None, when=Z("2026-10-24 16:10"))
        _pp = CI.probe_path(2026, ".")
        put(_pp, {"season": 2026, "built_at": "2026-10-24T16:10:00Z",
                  "sources": {"SEC": {"ok": True, "last_ok_at": "2026-10-24T16:10:00Z"}}})
        _pc = C.collect_injury_check(at=PINC)
        eq((RAN, _pc["slot"]["et"], sorted(_pc["sources"]), _pc["counts"]),
           ([], "12:00", ["SEC"], {"games": 1, "teams": 2, "with_status": 2, "out": 1}),
           "🔴 college: the reader already ran after the noon slot (this pass's cfb-injuries): reused, not "
           "read again; the counts are the reports for games still to start")
        put(_pp, {"season": 2026, "built_at": "2026-10-24T15:50:00Z", "sources": {}})
        _pc = C.collect_injury_check(at=PINC)
        eq((RAN, sorted(_pc["sources"])), (["."], ["ACC", "SEC"]),
           "🔴 ...and its last run was before the slot: the reader runs, once, in this run's own tree")
        league("nfl")
    CI.run = _REAL["ci_run"]

    # ══════════════════════════════════════════════════════════════════
    section("4. 🔴 COLLEGE'S MODEL READING: \"do 9am, 12pm, 7pm\"")
    # ══════════════════════════════════════════════════════════════════
    # Game g1 kicks off 15:30 ET (19:30Z); its QB is Out at 7:30 ET and cleared at 12:30 ET.
    # Game g2 kicks off 19:00 ET (23:00Z); cleared all day, then a 19:30 ET report lists its QB Out.
    R = tree()
    _qb = lambda st: [{"name": "Que Bee", "number": 7, "position": "QB", "position_raw": "QB", "status": st}]  # noqa: E731

    def rep(gid, home, away, kick, posted, fetched, home_list):
        return {"game_id": gid, "home": home, "away": away, "kickoff": kick, "source": "SEC", "label": "x",
                "posted_at": posted, "fetched_at": fetched, "teams": {home: home_list, away: []},
                "listed": {home: len(home_list), away: 0}}
    r1 = rep("g1", "Alabama", "Georgia", "2026-10-24T19:30:00Z", "2026-10-24T11:00:00Z", "2026-10-24T11:30:00Z", _qb("Out"))
    r2 = rep("g1", "Alabama", "Georgia", "2026-10-24T19:30:00Z", "2026-10-24T16:20:00Z", "2026-10-24T16:30:00Z",
             _qb("Available"))
    q1 = rep("g2", "LSU", "Ole Miss", "2026-10-24T23:00:00Z", "2026-10-24T11:00:00Z", "2026-10-24T11:30:00Z",
             _qb("Available"))
    q3 = rep("g2", "LSU", "Ole Miss", "2026-10-24T23:00:00Z", "2026-10-24T23:20:00Z", "2026-10-24T23:30:00Z",
             _qb("Out"))
    for when, reports in (("2026-10-24 11:30", [r1, q1]), ("2026-10-24 16:30", [r2, q1]),
                          ("2026-10-24 23:30", [r2, q3])):
        daystore.archive({"kind": "cfb-injury-reports", "season": 2026, "fetched_at": iso(Z(when)),
                          "sources": {"SEC": {"ok": True, "fetched_at": iso(Z(when))}}, "reports": reports,
                          "refused": []}, os.path.join(R, "data", "ncaaf"), "injury-reports",
                         log=lambda m: None, when=Z(when))

    def read(gid, team, now):
        got = CI.pick_time_outs(2026, R, now).get(gid)
        return None if got is None else [p["name"] for p in got.get(team) or []]
    eq(read("g1", "Alabama", None), ["Que Bee"], "   no build moment (training, the record, the backtest): §3's "
       "9:00 reading, the 7:30 report (QB Out)")
    eq(read("g1", "Alabama", Z("2026-10-24 21:00")), ["Que Bee"],
       "⛔ a game that has kicked off (final) keeps §3's 9:00 reading, though a later report is stored")
    eq(read("g1", "Alabama", Z("2026-10-24 14:00")), ["Que Bee"],
       "   a build at 10:00 ET: the 7:30 report (the 12:30 one does not exist yet at that moment)")
    eq(read("g1", "Alabama", Z("2026-10-24 17:00")), [],
       "🔴 a build at 1:00 pm ET, the game still to start: the 12:30 report (QB cleared)")
    eq((read("g2", "LSU", Z("2026-10-25 00:00")), read("g2", "LSU", Z("2026-10-24 22:00"))), ([], []),
       "⛔ a 7:30 pm report is never read for a game that kicked off at 7:00 pm, at a build after kickoff "
       "or before it")
    eq(CI.read_cut("2026-10-24T19:30:00Z", Z("2026-10-24 12:00")), CI.pick_cutoff("2026-10-24T19:30:00Z"),
       "   before 9:00 ET the cut IS §3's (8:59:59 ET)")
    eq([CI.shown_cut("2026-10-24T19:30:00Z", Z(t)) for t in ("2026-10-24 12:00", "2026-10-24 20:00")],
       [Z("2026-10-24 12:00"), CI.read_cut("2026-10-24T19:30:00Z", Z("2026-10-24 20:00"))],
       "🔴 `[2026-10-27, review 2]` a REPLAYED build reads at its own moment (8:00 am ET, never the later 9:00 "
       "cut); one after the kickoff keeps §3's cut, as the live read does")

    # 🔴 `[2026-10-26, review]` THE RECORD READS WHAT THE SITE SHOWED. Once g1 is played, the live
    #    build reads it at §3's 9:00 cut (QB Out) for TRAINING, and ALSO as of its last pre-kickoff
    #    build (1:00 pm ET: QB cleared, the pick the site showed) into `inj_shown`, the record's.
    _at = CI.pick_time_outs(2026, R, Z("2026-10-24 21:00"), at={"g1": "2026-10-24T17:00:00Z"})
    eq(([p["name"] for p in (_at.get("g1") or {}).get("Alabama", [])],
        [p["name"] for p in (_at.get("g2") or {}).get("LSU", [])]), ([], []),
       "🔴 `at` reads a played game as of ITS moment (g1 at 1:00 pm: cleared); a game not in it as `now` says")

    class FakeRoles:                 # one QB out = (1, 0, 0); the roster maths is test_cfb_injury_model's
        def __init__(self, season, root=None):
            pass

        def team_out(self, team, players, day):
            return (1.0 if any(p.get("position") == "QB" for p in players) else 0.0, 0.0, 0.0)
    _roles = CI.Roles
    try:
        CI.Roles = FakeRoles
        _rows = [{"id": g, "season": 2026, "day": "2026-10-24", "final": fin, "sig": {}, "home": h, "away": a}
                 for g, fin, h, a in (("g1", True, "Alabama", "Georgia"), ("g2", True, "LSU", "Ole Miss"))]
        CI.attach(_rows, R, now=Z("2026-10-25 01:00"), shown_at={"g1": "2026-10-24T17:00:00Z"})
        _r1, _r2 = _rows
        eq((_r1["sig"]["inj"]["qb"], (_r1["sig"].get("inj_shown") or {}).get("qb"), "inj_shown" in _r2["sig"]),
           ((1.0, 0.0), (0.0, 0.0), False),
           "🔴 attach: played g1 trains on §3's 9:00 reading (QB Out) and carries `inj_shown` as of its last "
           "pre-kickoff build (cleared); g2, with no recorded build, carries none")
        _up = [{"id": "g1", "season": 2026, "day": "2026-10-24", "final": False, "sig": {}, "home": "Alabama",
                "away": "Georgia"}]
        CI.attach(_up, R, now=Z("2026-10-24 17:00"), shown_at={"g1": "2026-10-24T16:00:00Z"})
        eq((_up[0]["sig"]["inj"]["qb"], "inj_shown" in _up[0]["sig"]), ((0.0, 0.0), False),
           "   a game still to start reads the newest report as of the build, and carries no `inj_shown`")

        # 🔴 `[2026-10-27, review 2]` THE REPLAY READS WHAT A BUILD AT ITS MOMENT COULD SEE, AT ANY
        #    MOMENT. The property, over build moments B every 30 minutes from 30 hours before kickoff
        #    to the kickoff (the evening before, before 9:00 ET on game day, after it), for a 3:30 pm
        #    ET kickoff and a 1:00 am ET one (whose 9:00 cut falls AFTER its kickoff), with reports
        #    changing before and after each B: the record's replay, attach(shown_at={g: B}) on every
        #    stored report, reads what a live attach(now=B) read on a tree holding only the reports
        #    stamped at or before B. max(9:00 cut, B) read a build before 9:00 ET as of 9:00 (or
        #    of the kickoff), with reports that build never saw.
        PROP = []
        for _kick, _day, _fetch in (
                ("2026-10-24T19:30:00Z", "2026-10-24",
                 [("2026-10-23 22:00", "Out"), ("2026-10-24 10:30", "Available"), ("2026-10-24 12:30", "Out"),
                  ("2026-10-24 14:00", "Available"), ("2026-10-24 18:00", "Out"), ("2026-10-24 19:40", "Available")]),
                ("2026-10-25T05:00:00Z", "2026-10-25",
                 [("2026-10-24 14:00", "Out"), ("2026-10-24 22:00", "Available"), ("2026-10-25 01:00", "Out"),
                  ("2026-10-25 04:30", "Available"), ("2026-10-25 05:30", "Out")])):
            _full, _grow = tree(), tree()
            for _t in (_full, _grow):
                put(os.path.join(_t, "data", "ncaaf", "latest", "schedule-2026.json.gz"),
                    {"season": 2026, "games": [{"id": "p1", "start": _kick, "home": "Alabama", "away": "Georgia",
                                                "home_class": "fbs", "away_class": "fbs"}]})

            def _plant(root, when, st, kick=_kick):
                daystore.archive({"kind": "cfb-injury-reports", "season": 2026, "fetched_at": iso(when),
                                  "sources": {"SEC": {"ok": True, "fetched_at": iso(when)}},
                                  "reports": [rep("p1", "Alabama", "Georgia", kick, iso(when - 10 * M), iso(when),
                                                  _qb(st))], "refused": []},
                                 os.path.join(root, "data", "ncaaf"), "injury-reports", log=lambda m: None, when=when)
            _left = [(Z(w), st) for w, st in _fetch]
            for _w, _st in _left:
                _plant(_full, _w, _st)
            _k = CI._utc(_kick)
            _b = _k - 30 * H
            while _b < _k:
                while _left and _left[0][0] <= _b:
                    _plant(_grow, *_left.pop(0))
                _live = [{"id": "p1", "season": 2026, "day": _day, "final": False, "sig": {}, "home": "Alabama",
                          "away": "Georgia"}]
                CI.attach(_live, _grow, now=_b)
                _rec = [dict(_live[0], final=True, sig={})]
                CI.attach(_rec, _full, now=_k + 6 * H, shown_at={"p1": iso(_b)})
                _q = lambda s, k: (s[k] or {}).get("qb") if k in s else "ABSENT"  # noqa: E731
                PROP.append((_kick, iso(_b), _b < CI.pick_cutoff(_kick), _q(_live[0]["sig"], "inj"),
                             _q(_rec[0]["sig"], "inj_shown")))
                _b += 30 * M
        ck(len(PROP) == 120 and {(x[0], x[2]) for x in PROP} == {("2026-10-24T19:30:00Z", True),
                                                                 ("2026-10-24T19:30:00Z", False),
                                                                 ("2026-10-25T05:00:00Z", True)}
           and {x[3] for x in PROP} == {(1.0, 0.0), (0.0, 0.0), None},
           "⚠️ the case exists: 120 build moments, before and after the 9:00 cut, reading the QB out, cleared and "
           "no report at all", sorted({(x[0], x[2], x[3]) for x in PROP}, key=str))
        eq([x for x in PROP if x[3] != x[4]], [],
           "🔴🔴 at EVERY build moment the record's replay (`inj_shown`) reads exactly what that build read live "
           "from the reports it could see: the evening before, before 9:00 ET, after it, and a 1:00 am kickoff")
    finally:
        CI.Roles = _roles
    # ...and the moment is the ledger's: the LAST snapshot before kickoff that looked at the game
    for _when, _look in (("2026-10-24 16:00", {"g1": "2026-10-24T19:30:00Z"}),
                         ("2026-10-24 17:00", {"g1": "2026-10-24T19:30:00Z", "g2": "2026-10-24T23:00:00Z"}),
                         ("2026-10-24 20:00", {"g2": "2026-10-24T23:00:00Z", "g1": "2026-10-24T19:30:00Z"})):
        daystore.archive({"league": "ncaaf", "taken_at": iso(Z(_when)), "game_model": [], "props_model": [],
                          "looked_at": {"game_model": _look, "props_model": {}}},
                         os.path.join(R, "data", "ncaaf"), "model-picks", log=lambda m: None, when=Z(_when))
    import fb_model as FM  # noqa: E402
    GOT = []
    _att = CI.attach
    try:
        CI.attach = lambda rows, root=None, now=None, shown_at=None: GOT.append((now, shown_at))
        FM.injury_readings("ncaaf", [], R, now=Z("2026-10-25 01:00"))
        FM.injury_readings("ncaaf", [], R)
    finally:
        CI.attach = _att
    eq(GOT, [(Z("2026-10-25 01:00"), {"g1": "2026-10-24T17:00:00Z", "g2": "2026-10-24T20:00:00Z"}), (None, None)],
       "🔴 the live build hands attach each game's last pre-kickoff snapshot (g1: 1:00 pm, not the 4:00 pm one "
       "after its kickoff; g2: 4:00 pm); a caller with no build moment reads no ledger")

    # 🔴 `[2026-10-27, review 2]` ...AND ITS MOMENT IS THE GAME MODEL'S READING, NOT THE SNAPSHOT'S MINUTE.
    #    fb_model.build stamps when its rows read the reports (`read_at`); the ledger's snapshot copies it
    #    (`model_read_at`) and looked_moments dates the replay with it. Here the 12:00 pm build read at
    #    16:00Z (QB Out, the 11:30 am report); the 1:00 pm pass's model build failed, so its snapshot
    #    at 17:00Z saved the 12:00 build's picks. The 12:45 pm report (QB cleared) was never read for them.
    L = tree()
    _lat = os.path.join(L, "data", "ncaaf", "latest")
    put(os.path.join(_lat, "schedule-2026.json.gz"),
        {"season": 2026, "games": [{"id": "g1", "start": "2026-10-24T19:30:00Z", "home": "Alabama", "away": "Georgia",
                                    "home_class": "fbs", "away_class": "fbs"}]})
    for _w, _st in (("2026-10-24 15:30", "Out"), ("2026-10-24 16:45", "Available")):
        daystore.archive({"kind": "cfb-injury-reports", "season": 2026, "fetched_at": iso(Z(_w)),
                          "sources": {"SEC": {"ok": True, "fetched_at": iso(Z(_w))}},
                          "reports": [rep("g1", "Alabama", "Georgia", "2026-10-24T19:30:00Z", iso(Z(_w) - 10 * M),
                                          iso(Z(_w)), _qb(_st))], "refused": []},
                         os.path.join(L, "data", "ncaaf"), "injury-reports", log=lambda m: None, when=Z(_w))
    _brl, _lgf = FM.build_rows, FM.log
    try:
        FM.build_rows, FM.log = (lambda *a, **k: []), (lambda m: None)
        FM.build("ncaaf", root=L, out=os.path.join(_lat, "fb-model.json"), now=Z("2026-10-24 16:00"))
    finally:
        FM.build_rows, FM.log = _brl, _lgf
    _fm = json.load(open(os.path.join(_lat, "fb-model.json"), encoding="utf-8"))
    eq(_fm.get("read_at"), "2026-10-24T16:00:00Z", "🔴 fb-model.json says when its rows read the injury reports "
       "(`read_at`, the build's moment)")
    _fm["win_chances"] = [{"game_id": "g1", "commence": "2026-10-24T19:30:00Z"}]   # the game its list held
    put(os.path.join(_lat, "fb-model.json"), _fm)
    import fb_ledger  # noqa: E402
    fb_ledger.snapshot("ncaaf", L, when=Z("2026-10-24 17:00"), log=lambda m: None)
    eq(fb_ledger.looked_moments("ncaaf", L), {"g1": "2026-10-24T16:00:00Z"},
       "🔴 the snapshot taken at 1:00 pm (that pass's model build failed) dates g1's replay at its picks' own "
       "reading, 12:00 pm, never at the snapshot's minute")
    _roles = CI.Roles
    try:
        CI.Roles = FakeRoles
        _pl = [{"id": "g1", "season": 2026, "day": "2026-10-24", "final": True, "sig": {}, "home": "Alabama",
                "away": "Georgia"}]
        CI.attach(_pl, L, now=Z("2026-10-25 01:00"), shown_at=fb_ledger.looked_moments("ncaaf", L))
    finally:
        CI.Roles = _roles
    eq((_pl[0]["sig"].get("inj_shown") or {}).get("qb"), (1.0, 0.0),
       "🔴🔴 ...so the record replays g1 with the QB Out, as the picks the site showed were built (not the 12:45 "
       "pm report fetched between that reading and the snapshot)")
    _late = sorted(glob.glob(os.path.join(L, "data", "ncaaf", "*", "model-picks", "*.json.gz")))[-1]
    with gzip.open(_late, "rt", encoding="utf-8") as fh:
        _sd = json.load(fh)
    _sd["model_read_at"] = "2026-10-24T18:00:00Z"
    put(_late, _sd)
    eq(fb_ledger.looked_moments("ncaaf", L), {"g1": "2026-10-24T17:00:00Z"},
       "⛔ a reading stamped after its snapshot is not believed: never a moment later than `taken_at`")

    # 🔴 THE LIVE BUILD PASSES ITS MOMENT; NO TRAINING OR BACKTEST CALLER DOES
    import fb_inj_backtest as B  # noqa: E402
    import fb_model as FM  # noqa: E402
    SEEN = []

    class Stop(Exception):
        pass

    def stub(*a, **k):
        SEEN.append(k.get("inj_now", "absent"))
        raise Stop()
    _br = FM.build_rows
    T = tree()
    try:
        FM.build_rows = stub
        for _call in (lambda: FM.build("ncaaf", root=T, out=os.path.join(T, "x.json"), now=Z("2026-10-24 17:00")),
                      lambda: FM.build("ncaaf", root=T, out=os.path.join(T, "x.json")),
                      lambda: B.measure("ncaaf", T)):
            try:
                _call()
            except Stop:
                pass
    finally:
        FM.build_rows = _br
    _clock = SEEN[1] if len(SEEN) > 1 else None
    ck(len(SEEN) == 3 and SEEN[0] == Z("2026-10-24 17:00")
       and isinstance(_clock, datetime.datetime) and abs((datetime.datetime.now(UTC) - _clock).total_seconds()) < 600,
       "🔴 fb_model.build hands its moment to the rows (pinned by a test, the clock otherwise)", SEEN[:2])
    eq(SEEN[2:], ["absent"], "⛔ fb_inj_backtest.measure never does: the recorded test's numbers path reads "
       "§3's 9:00 cut for every game")
    # ⛔ THE CLASS: every caller of build_rows in the repo, read with ast
    _with, _without = [], []
    for _f in sorted(glob.glob(os.path.join(ROOT, "*.py"))):
        if os.path.basename(_f).startswith("test_"):
            continue
        _t = ast.parse(open(_f, encoding="utf-8").read())
        for _fn in [n for n in ast.walk(_t) if isinstance(n, (ast.FunctionDef, ast.Module))]:
            for _n in ast.walk(_fn):
                if isinstance(_n, ast.Call) and (getattr(_n.func, "id", None) == "build_rows"
                                                  or getattr(_n.func, "attr", None) == "build_rows"):
                    _k = (os.path.basename(_f), getattr(_fn, "name", "<module>"))
                    (_with if any(kw.arg == "inj_now" for kw in _n.keywords) else _without).append(_k)
    _with = sorted(set(k for k in _with if k[1] != "<module>"))
    ck(_with == [("fb_model.py", "build")] and ("fb_inj_backtest.py", "measure") in _without,
       "⛔ only fb_model.build passes the live moment; every other caller of build_rows (the backtest, the "
       "refit, the score model, the lambda test, the alt-lines check) reads §3's cut",
       "with: %s; without: %s" % (_with, sorted(set(k for k in _without if k[1] != "<module>"))))

    # ══════════════════════════════════════════════════════════════════
    section("5. 🔴 THE REVIEWS' FINDINGS `[2026-10-26, review]`")
    # ══════════════════════════════════════════════════════════════════
    # 5a. ⛔ an EMPTY nflverse answer is a failed source; a refused releases call is not repeated
    E = tree()
    nfl_sched(E, ["2026-10-25T13:00", "2026-10-25T16:25"])
    PE = Z("2026-10-25 13:05")                                  # 9:05 EDT, Sunday
    with inside(E):
        league("nfl")
        _f = os.path.join("data", "nfl", "latest", "injuries-2026.json.gz")
        put(_f, {"season": 2026, "built_at": iso(PE - 6 * H), "teams": {"SEA": {"8": {"players": [
            {"gsis_id": "p1", "full_name": "A One", "report_status": "Out"}], "starting_qb": None}}}})
        _before = open(_f, "rb").read()
        _inj_rows, SRC["injuries"] = SRC["injuries"], []
        try:
            _pe = C.collect_injury_check(at=PE)
        finally:
            SRC["injuries"] = _inj_rows
        _s = _pe["sources"]["injuries"]
        ck(_s["ok"] is False and "no rows" in (_s.get("error") or "") and open(_f, "rb").read() == _before
           and not glob.glob(os.path.join("data", "nfl", "*", "injury-reports", "*.json.gz")),
           "⛔ nflverse answered with NO ROWS: a failed source, the stored file is NOT rewritten as every player "
           "cleared, and no snapshot", _s)
        del CALLS[:]
        _rel = nfl._releases

        def refused(log=print, max_pages=10):
            CALLS.append("releases")
            raise urllib.error.HTTPError("planted://releases", 403, "rate limited", None, None)
        nfl._releases = refused
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                _pr = C.collect_injury_check(at=PE + M)
        finally:
            nfl._releases = _rel
        eq((CALLS.count("releases"), sorted(k for k, v in _pr["sources"].items() if v["ok"] is False)),
           (1, ["injuries", "weekly_rosters"]),
           "⛔ GitHub refused the releases call: ONE call, both sources recorded failed (not a second refused call)")

        # 5b. 🔴 ONE RETRY WITHIN THE SLOT, NEVER EVERY PASS
        os.remove(os.path.join("data", "nfl", "latest", "injury-check.json"))
        FAIL.update({"injuries", "weekly_rosters"})
        with contextlib.redirect_stdout(io.StringIO()):
            _a1 = C.collect_injury_check(at=PE)

        def _row(t):
            return [r for r in F.survey("data/nfl", "picks", t) if r["mode"] == "injury-check"][0]
        _r1 = _row(PE + 15 * M)
        ck(_a1["ok"] is False and _a1["slot"]["attempt"] == 1 and _r1["stale"] and _r1["due_at"] == "2026-10-25T13:05Z"
           and "injury-check" in planned(".", "nfl", PE + 15 * M),
           "🔴 the 9:00 check read nothing (both sources down): its row is due again just after it, and the next "
           "pass plans the check once more", {k: _r1.get(k) for k in ("stale", "due_at")})
        with contextlib.redirect_stdout(io.StringIO()):
            _a2 = C.collect_injury_check(at=PE + 60 * M)
        _r2 = _row(PE + 75 * M)
        ck(_a2["slot"]["attempt"] == 2 and not _r2["stale"] and "injury-check" not in planned(".", "nfl", PE + 75 * M),
           "⛔ ...it failed again: ONE retry only, the row is fresh until the noon slot (no check, and no card "
           "rebuild, on every pass)", {k: _r2.get(k) for k in ("stale", "due_at", "unhealthy")})

        # 5c. 🔴 A SOURCE DOWN AT 2 SLOTS IN A ROW IS A WARNING THAT IS NEVER REPLANNED
        ck(not _r2.get("unhealthy"), "   one slot down is not yet a warning", _r2.get("unhealthy"))
        with contextlib.redirect_stdout(io.StringIO()):
            C.collect_injury_check(at=Z("2026-10-25 16:05"))
            _a4 = C.collect_injury_check(at=Z("2026-10-25 16:35"))
        _r4 = _row(Z("2026-10-25 16:50"))
        _hard, _soft = F.classify([_r4], "data/nfl", refused=False, block={"state": None})
        ck(_r4["stale"] and "weekly_rosters has not answered at the last 2 game-day checks" in (_r4["unhealthy"] or "")
           and not _hard and len(_soft) == 1 and "injury-check" not in planned(".", "nfl", Z("2026-10-25 16:50")),
           "🔴 9:00 and 12:00 both read nothing: the row is STALE with the reason (a soft warning, a `fresh:` "
           "finding), and NOT planned again (it would rebuild the card every pass)", _r4.get("unhealthy"))
        eq([len(v["failing_slots"]) for _k, v in sorted(_a4["sources"].items())], [2, 2],
           "   (the probe counts the slots each source failed at in a row)")
        eq({k: (v["attempts"], v["ok_at"]) for k, v in _a4["log"].items()},
           {"2026-10-25T13:00Z": (2, None), "2026-10-25T16:00Z": (2, None)},
           "🔴 ...and its slot log: the 9:00 and 12:00 slots each tried twice, and NEITHER ran (no `ok_at`)")
        FAIL.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            _a5 = C.collect_injury_check(at=Z("2026-10-25 23:05"))
        _r5 = _row(Z("2026-10-25 23:10"))
        ck(_a5["ok"] and not _r5["stale"] and all(v["failing_slots"] == [] and v["last_ok_at"] == "2026-10-25T23:05:00Z"
                                                  for v in _a5["sources"].values()),
           "   nflverse back at 7:00 pm: the warning clears and each source's last answer is recorded", _r5.get("unhealthy"))
        _pp = os.path.join("data", "nfl", "latest", "injury-check.json")
        _p = json.load(open(_pp, encoding="utf-8"))
        for v in _p["sources"].values():
            v["failing_slots"], v["failing_since"] = ["a", "b"], "x"
        _p["checked_at"] = iso(Z("2026-10-25 23:05") - 9 * D)
        put(_pp, _p)
        eq(F.health(_pp, Z("2026-10-25 23:10")), None,
           "⛔ a failing source whose last check was over 8 days ago (the off-season) is no warning")
        _p["checked_at"] = iso(Z("2026-10-25 23:05"))
        put(_pp, _p)
        ck(bool(F.health(_pp, Z("2026-10-25 23:10"))), "   (the same probe, checked this week, is one)")
        put(os.path.join("data", "ncaaf", "latest", "injury-check.json"), _p)
        eq(F.health(os.path.join("data", "ncaaf", "latest", "injury-check.json"), Z("2026-10-25 23:10")), None,
           "⛔ college's check is not judged here: its sources are the conference reader's, judged on its own probe")

    # 5d. ⛔ A SEASON WITH NO STORED SCHEDULE OWES NOTHING; AN UNREADABLE ONE OWES EVERY SLOT
    Q = tree()
    eq(F.injury_check_slots("nfl", Q + "/data/nfl/latest", Z("2027-08-05 13:05")), [],
       "⛔ August 1st names the 2027 season before its schedule is stored: no check owed (both cards would be "
       "rebuilt three times a day for nothing)")
    with open(os.path.join(Q, "data", "nfl", "latest", "schedule-2027.json.gz"), "wb") as fh:
        fh.write(b"not a gzip")
    eq([s[0] for s in F.injury_check_slots("nfl", Q + "/data/nfl/latest", Z("2027-08-05 13:05"))],
       ["9:00", "12:00", "19:00"], "   ...an UNREADABLE stored schedule is cannot-tell: every slot owed, as before")

    # 5e. 🔴 MOMENTS: next_due is the first moment after now
    _mo = F.Moments([Z("2026-10-25 13:00"), Z("2026-10-25 16:00")], label="x")
    eq((F.next_due(_mo, Z("2026-10-25 14:00")), F.next_due(_mo, Z("2026-10-25 16:00"))), (Z("2026-10-25 16:00"), None),
       "🔴 a Moments' next deadline is its first moment strictly after now (after_last_survey reads it)")

    # 5f. 🔴 EVERY SLOT'S ATTEMPTS ARE LOGGED, AND THE MONDAY STATUS COUNTS THEM
    import status as ST  # noqa: E402
    S2 = tree()
    nfl_sched(S2, ["2026-10-25T13:00", "2026-10-25T16:25", "2026-10-25T20:20", "2026-10-26T20:15"])
    put(os.path.join(S2, "data", "nfl", "latest", "injury-check.json"), {"log_since": "2026-10-22T13:05:00Z", "log": {
        "2026-10-25T13:00Z": {"et": "9:00", "attempts": 1, "ok_at": "2026-10-25T13:10:00Z"},
        "2026-10-25T16:00Z": {"et": "12:00", "attempts": 1, "ok_at": "2026-10-25T17:30:00Z"},
        "2026-10-26T13:00Z": {"et": "9:00", "attempts": 2, "ok_at": None},
        "2026-10-26T16:00Z": {"et": "12:00", "attempts": 1, "ok_at": "2026-10-26T16:20:00Z"}}})
    _lines = ST.injury_checks(S2, Z("2026-10-26 23:30"))
    eq(_lines, ["- NFL: 3 of 5 checks ran (1 after some of their games had started: Sun 10-25 12:00 ET); read "
                "nothing: Mon 10-26 9:00 ET; never ran: Sun 10-25 19:00 ET.", "- College: no check has run yet."],
       "🔴 the Monday status: Sunday 9:00 ran; 12:00 ran after the 1pm games had started; 19:00 never ran before "
       "the 8:20pm game; Monday 9:00 read nothing; Monday 19:00 is still open (the 8:15pm game), so not counted")
    _pp2 = os.path.join(S2, "data", "nfl", "latest", "injury-check.json")
    _d2 = json.load(open(_pp2, encoding="utf-8"))
    _d2["log_since"] = "2026-10-25T23:30:00Z"
    put(_pp2, _d2)
    eq(ST.injury_checks(S2, Z("2026-10-26 23:30"))[0],
       "- NFL: 3 of 4 checks ran (1 after some of their games had started: Sun 10-25 12:00 ET); read nothing: "
       "Mon 10-26 9:00 ET.",
       "⛔ a slot before the probe's first check (`log_since`: the check shipped Sunday evening) is not a miss")
    _body = ST.build(S2, Z("2026-10-26 23:30"))[0]
    ck("## Game-day injury checks (last 7 days)" in _body and ST.injury_checks(S2, Z("2026-10-26 23:30"))[0] in _body,
       "   ...in the weekly email's body, under its own heading")
    E2 = tree()
    nfl_sched(E2, ["2026-10-25T13:00", "2026-10-25T16:25"])
    with inside(E2):
        league("nfl")
        FAIL.update({"injuries", "weekly_rosters"})
        with contextlib.redirect_stdout(io.StringIO()):
            C.collect_injury_check(at=PE)
            FAIL.clear()
            C.collect_injury_check(at=PE + 60 * M)
            _lg = C.collect_injury_check(at=Z("2026-10-25 16:10"))["log"]
    eq(_lg, {"2026-10-25T13:00Z": {"et": "9:00", "attempts": 2, "first_at": iso(PE), "ok_at": iso(PE + 60 * M)},
             "2026-10-25T16:00Z": {"et": "12:00", "attempts": 1, "first_at": "2026-10-25T16:10:00Z",
                                   "ok_at": "2026-10-25T16:10:00Z"}},
       "🔴 the probe's slot log: the 9:00 slot's two attempts (the first read nothing, the retry did) and the 12:00 one")
    with inside(E2):
        eq(json.load(open(os.path.join("data", "nfl", "latest", "injury-check.json"), encoding="utf-8")).get("log_since"),
           iso(PE), "   ...from its first check (`log_since`), carried forward")
    FAIL.clear()
finally:
    urllib.request.urlopen = _REAL["urlopen"]
    nfl._raw, nfl._releases, nfl._rows = _REAL["raw"], _REAL["releases"], _REAL["rows"]
    CI.run = _REAL["ci_run"]
    for _d in TREES:
        shutil.rmtree(_d, ignore_errors=True)

eq(NET, [], "⛔ no network call was made")
