#!/usr/bin/env python3
r"""test_cfb_injuries.py — COLLEGE INJURY REPORTS: ACCURATE AND UP TO DATE.

`[Sam, 2026-10-17]` *"use the college injury source as long as it's accurate
and up to date, we wouldn't want misinformation ruining our bets."* Design:
research/cfb_injuries_design.md §1-§3.

A planted tree (schedules for 2025 and 2026), a pinned clock, and planted
feed payloads hand-made in the shapes of the real samples (HDI publish and
archives, Sun Belt and Pac-12 report.json). ⛔ No network (urlopen is
replaced by a tripwire), no repo data/ read or written.

# @vacuity 🔴 every data: string is stripped before anything is stored
#   file: cfb_injuries.py
#   find: return strip_images(fn(*args))
#   with: return fn(*args)
#
# @vacuity 🔴 the alias table maps HDI's short names (Ohio St.)
#   file: cfb_injuries.py
#   find: "Michigan St.": "Michigan State", "Mississippi St.": "Mississippi State", "Ohio St.": "Ohio State",
#   with: "Michigan St.": "Michigan State", "Mississippi St.": "Mississippi State",
#
# @vacuity 🔴 an unknown team name fails closed
#   file: cfb_injuries.py
#   find: return a if a in known else None
#   with: return a or s
#
# @vacuity 🔴 a CFP seed is dropped before the name is looked up
#   file: cfb_injuries.py
#   find: SEED = re.compile(r"^#\d+\s+")
#   with: SEED = re.compile(r"^$")
#
# @vacuity 🔴🔴 the join keys on teamName, never the display name (Miami)
#   file: cfb_injuries.py
#   find: raw = [t.get("teamName") if isinstance(t, dict) else None for t in teams]
#   with: raw = [t.get("teamDisplayName") if isinstance(t, dict) else None for t in teams]
#
# @vacuity 🔴 games[0] is the away team, games[1] the home team
#   file: cfb_injuries.py
#   find: for name, t in ((away, teams[0]), (home, teams[1])):
#   with: for name, t in ((away, teams[1]), (home, teams[0])):
#
# @vacuity 🔴 a report joins exactly ONE stored game
#   file: cfb_injuries.py
#   find: if len(same) != 1:
#   with: if not same:
#
# @vacuity 🔴 a kickoff that is not the schedule's to the minute is refused
#   file: cfb_injuries.py
#   find: same = [g for g in near if g["_k"].replace(second=0, microsecond=0) == kick.replace(second=0, microsecond=0)]
#   with: same = near
#
# @vacuity 🔴 Central time is an hour behind Eastern
#   file: cfb_injuries.py
#   find: ZONES = {"ET": 0, "CT": -1}
#   with: ZONES = {"ET": 0, "CT": 0}
#
# @vacuity 🔴 HDI's posted time is publishDate + postedTime in its zone
#   file: cfb_injuries.py
#   find: posted = local_to_utc(r.get("publishDate"), r.get("postedTime"), zone)
#   with: posted = None
#
# @vacuity 🔴 an archive row joins no game starting under 8 hours after its date
#   file: cfb_injuries.py
#   find: ARCHIVE_WINDOW_H = (8, 36)
#   with: ARCHIVE_WINDOW_H = (6, 36)
#
# @vacuity 🔴 ...and does join one starting exactly 8 hours after it
#   file: cfb_injuries.py
#   find: ARCHIVE_WINDOW_H = (8, 36)
#   with: ARCHIVE_WINDOW_H = (9, 36)
#
# @vacuity 🔴 an archive row joins no game starting over 36 hours after its date
#   file: cfb_injuries.py
#   find: ARCHIVE_WINDOW_H = (8, 36)
#   with: ARCHIVE_WINDOW_H = (8, 38)
#
# @vacuity 🔴 ...and does join one starting exactly 36 hours after it
#   file: cfb_injuries.py
#   find: ARCHIVE_WINDOW_H = (8, 36)
#   with: ARCHIVE_WINDOW_H = (8, 35)
#
# @vacuity 🔴 "at" means the row's team is the away team
#   file: cfb_injuries.py
#   find: (g["away"] == team if side == "at" else (g["home"] == team or g.get("neutral")))]
#   with: True]
#
# @vacuity 🔴 a row naming its team as its own opponent is recovered from team + date
#   file: cfb_injuries.py
#   find: if opp == team:
#   with: if False:
#
# @vacuity 🔴 ...only when exactly one game matches
#   file: cfb_injuries.py
#   find: if len(cand) != 1:
#   with: if not cand:
#
# @vacuity 🔴 a row with no jersey still parses
#   file: cfb_injuries.py
#   find: ROW = re.compile(r"^(?P<pos>\S+) (?:#(?P<num>\d{1,2}) )?(?P<name>.+?)\s*$")
#   with: ROW = re.compile(r"^(?P<pos>\S+) #(?P<num>\d{1,2}) (?P<name>.+?)\s*$")
#
# @vacuity 🔴 a trailing space is not part of the name
#   file: cfb_injuries.py
#   find: ROW = re.compile(r"^(?P<pos>\S+) (?:#(?P<num>\d{1,2}) )?(?P<name>.+?)\s*$")
#   with: ROW = re.compile(r"^(?P<pos>\S+) (?:#(?P<num>\d{1,2}) )?(?P<name>.+)$")
#
# @vacuity 🔴 a row whose name has no letter is unparsed, never guessed
#   file: cfb_injuries.py
#   find: if not m or not _has_letter(m.group("name")):
#   with: if not m:
#
# @vacuity 🔴 one player listed twice is kept once
#   file: cfb_injuries.py
#   find: if key in seen:
#   with: if False:
#
# @vacuity 🔴 one player listed with two statuses is unknown
#   file: cfb_injuries.py
#   find: seen[key]["status"] = UNKNOWN
#   with: pass
#
# @vacuity 🔴 Exempt is unknown, never healthy
#   file: cfb_injuries.py
#   find: _CANON = {s.lower(): s for s in STATUSES}
#   with: _CANON = dict({s.lower(): s for s in STATUSES}, exempt="Available")
#
# @vacuity 🔴 a status outside the known set is stored as unknown
#   file: cfb_injuries.py
#   find:     return UNKNOWN
#   with:     return _clean(raw)
#
# @vacuity 🔴 a college position code is mapped to the NFL code (EDG -> EDGE)
#   file: cfb_injuries.py
#   find: "DL": "DL", "DE": "DE", "DT": "DT", "EDG": "EDGE", "JCK": "EDGE",
#   with: "DL": "DL", "DE": "DE", "DT": "DT", "EDG": "DL", "JCK": "EDGE",
#
# @vacuity 🔴 an unknown position code stays raw
#   file: cfb_injuries.py
#   find: return (code or None), (None if raw is None else _clean(raw))
#   with: return None, (None if raw is None else _clean(raw))
#
# @vacuity 🔴 "Report Pending" is not a report
#   file: cfb_injuries.py
#   find: return not label or label.lower() == "report pending"
#   with: return not label
#
# @vacuity 🔴 a team with nobody listed is absent (no reading), and an empty report is refused
#   file: cfb_injuries.py
#   find: if entries:
#   with: if True:
#
# @vacuity 🔴 a snapshot is written only when the reports change
#   file: cfb_injuries.py
#   find: if prev is not None and _content(allrep) == _content(prev.get("reports") or []):
#   with: if False:
#
# @vacuity 🔴 a source that failed keeps its last reports in the new snapshot
#   file: cfb_injuries.py
#   find: carried = [r for r in (prev or {}).get("reports") or []
#   with: carried = [r for r in []
#
# @vacuity 🔴🔴 one source failing never stops the others
#   file: cfb_injuries.py
#   find: except Exception as ex:                  # ⛔ one source failing never stops the others
#   with: except FeedError as ex:
#
# @vacuity 🔴 a report published more than 36 hours before kickoff is not current
#   file: cfb_injuries.py
#   find: MAX_AGE_H = 36
#   with: MAX_AGE_H = 38
#
# @vacuity 🔴 a live read needs our reading of the source within 6 hours
#   file: cfb_injuries.py
#   find: FETCH_MAX_AGE_H = 6
#   with: FETCH_MAX_AGE_H = 8
#
# @vacuity 🔴 an unchanged pass (no snapshot) still confirms the source through the probe
#   file: cfb_injuries.py
#   find: cands = _probe_ok_times(source, at, root)
#   with: cands = []
#
# @vacuity 🔴🔴 a report fetched after kickoff is never read
#   file: cfb_injuries.py
#   find: return bool(f and k and k - datetime.timedelta(days=SCAN_DAYS) <= f <= at and f < k)
#   with: return bool(f and k and k - datetime.timedelta(days=SCAN_DAYS) <= f <= at)
#
# @vacuity 🔴 the snapshot known at pick time is the last one before 9:00 ET
#   file: cfb_injuries.py
#   find: PICK_HOUR_ET = 9
#   with: PICK_HOUR_ET = 10
#
# @vacuity 🔴 2025 SEC's night-before column is "Friday"
#   file: cfb_injuries.py
#   find: NIGHT_BEFORE = {2025: {"SEC": "Friday", "B12": "Friday", "ACC": "Thursday"}}
#   with: NIGHT_BEFORE = {2025: {"SEC": "Gameday", "B12": "Friday", "ACC": "Thursday"}}
#
# @vacuity 🔴 2025 ACC's night-before column is "Thursday"
#   file: cfb_injuries.py
#   find: NIGHT_BEFORE = {2025: {"SEC": "Friday", "B12": "Friday", "ACC": "Thursday"}}
#   with: NIGHT_BEFORE = {2025: {"SEC": "Friday", "B12": "Friday", "ACC": "Friday"}}
#
# @vacuity 🔴 the 2025 Big Ten (game day only) gives no reading
#   file: cfb_injuries.py
#   find: return NIGHT_BEFORE[season].get(conf)
#   with: return NIGHT_BEFORE[season].get(conf, "Gameday")
#
# @vacuity 🔴 2026's night-before column is "Update 2"
#   file: cfb_injuries.py
#   find: NIGHT_BEFORE_FROM_2026 = "Update 2"
#   with: NIGHT_BEFORE_FROM_2026 = "Game Day"
#
# @vacuity 🔴 a team whose night-before column was not archived has no reading
#   file: cfb_injuries.py
#   find: if not any(col in (r.get("columns") or {}) for r in rows):
#   with: if False:
#
# @vacuity 🔴 Doubtful counts as out
#   file: cfb_injuries.py
#   find: OUT_STATUSES = ("out", "out for season", "doubtful")
#   with: OUT_STATUSES = ("out", "out for season")
#
# @vacuity 🔴 the 2025 archive is fetched once while missing
#   file: cfb_injuries.py
#   find: if conf in have and not refresh:
#   with: if False:
#
# @vacuity 🔴 the current archive is refreshed at most once a day
#   file: cfb_injuries.py
#   find: if conf in have and checked and now - checked < datetime.timedelta(hours=ARCHIVE_REFRESH_H):
#   with: if False:
#
# @vacuity 🔴 the archive is rewritten only when it changes
#   file: cfb_injuries.py
#   find: same = old.get("report_days") == days and old.get("rows") == rows and old.get("refused") == refused
#   with: same = False
#
# @vacuity 🔴 a refused archive row is NAMED (team, opponent, date), never only counted
#   file: cfb_injuries.py
#   find: key = (_clean(r.get("Team")), _clean(r.get("Opponent")),
#   with: key = (None, None,
#
# @vacuity 🔴🔴 a report its source no longer lists (refused or dropped) is not current
#   file: cfb_injuries.py
#   find: if not _holds(newest, rep):
#   with: if False:
#
# @vacuity 🔴 out_players gives no reading for a report that is not current
#   file: cfb_injuries.py
#   find: if not report or report.get("current") is not True or team not in (report.get("teams") or {}):
#   with: if not report or team not in (report.get("teams") or {}):
#
# @vacuity 🔴 a read a month after the game finds the report a read on the day found
#   file: cfb_injuries.py
#   find: return bool(f and k and k - datetime.timedelta(days=SCAN_DAYS) <= f <= at and f < k)
#   with: return bool(f and k and at - datetime.timedelta(days=SCAN_DAYS) <= f <= at and f < k)
#
# @vacuity 🔴 ...the scan is bounded by the game's kickoff, never by the moment asked
#   file: cfb_injuries.py
#   find: lo = hint - datetime.timedelta(days=SCAN_DAYS + HINT_SLACK_D)
#   with: lo = at - datetime.timedelta(days=SCAN_DAYS + 1)
#
# @vacuity 🔴 ...and so it is with no schedule hint (the report's own kickoff)
#   file: cfb_injuries.py
#   find: lo = k - datetime.timedelta(days=SCAN_DAYS + 1)
#   with: lo = at
#
# @vacuity 🔴🔴 a 2025 weekday column is read only for a game on a LATER ET day (no look-ahead)
#   file: cfb_injuries.py
#   find: return WEEKDAYS.index(col) < _eastern(k).weekday()
#   with: return True
#
# @vacuity 🔴 an unchanged report keeps the time we first fetched it
#   file: cfb_injuries.py
#   find: r["fetched_at"] = seen.get(_one(r)) or r["fetched_at"]
#   with: pass
#
# @vacuity 🔴 a posted time later than our first fetch never starts the 36-hour clock late
#   file: cfb_injuries.py
#   find: if posted is not None and (f is None or posted <= f):
#   with: if posted is not None:
#
# @vacuity 🔴 ...and is listed in the probe
#   file: cfb_injuries.py
#   find: for r in reports if r.get("posted_at") and _utc(r["posted_at"]) > _utc(r["fetched_at"])]
#   with: for r in reports if False]
#
# @vacuity 🔴 the call cap holds
#   file: cfb_injuries.py
#   find: if state["calls"] >= MAX_CALLS:
#   with: if False:
#
# @vacuity 🔴 every POST carries the User-Agent
#   file: cfb_injuries.py
#   find: headers={"User-Agent": UA, "Content-Type": "application/json",
#   with: headers={"Content-Type": "application/json",
#
# @vacuity 🔴 every GET carries the User-Agent
#   file: cfb_injuries.py
#   find: req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
#   with: req = urllib.request.Request(url, headers={"Accept": "application/json"})
#
# @vacuity 🔴 every request has a timeout
#   file: cfb_injuries.py
#   find: with urllib.request.urlopen(req, timeout=timeout) as r:
#   with: with urllib.request.urlopen(req) as r:
#
# @vacuity 🔴 a failed source's report is still carried just after kickoff
#   file: cfb_injuries.py
#   find: CARRY_H = 48
#   with: CARRY_H = 0
#
# @vacuity 🔴 ...but never more than CARRY_H after it
#   file: cfb_injuries.py
#   find: if r.get("source") in failed and (_utc(r.get("kickoff")) or now) >= keep]
#   with: if r.get("source") in failed]
#
# @vacuity 🔴 with no probe, the newest snapshot's own reading confirms its source
#   file: cfb_injuries.py
#   find: t = _utc((((newest or {}).get("sources") or {}).get(source) or {}).get("fetched_at"))
#   with: t = None
#
# @vacuity 🔴 the probe's last_ok_at moves only when the snapshot step finished
#   file: cfb_injuries.py
#   find: last = v["fetched_at"] if v["ok"] and state["snapshot_ok"] else
#   with: last = v["fetched_at"] if v["ok"] else
#
# @vacuity 🔴 a same-minute pass whose reports daystore did not store confirms nothing
#   file: cfb_injuries.py
#   find: if not wrote and _content((_snapshot(p) or {}).get("reports") or []) != _content(allrep):
#   with: if False:
"""
import copy
import datetime
import gzip
import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, eq, note, section  # noqa: E402


def _tripwire(*a, **k):
    raise AssertionError("test_cfb_injuries reached the network")


urllib.request.urlopen = _tripwire     # ⛔ before the module can use it

import cfb_injuries as CI  # noqa: E402

UTC = datetime.timezone.utc
IMG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"


def T(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def G(gid, start, home, away, neutral=False):
    return {"id": gid, "start": start, "home": home, "away": away, "neutral": neutral,
            "season_type": "regular", "week": 7, "final": False}


SCHED_2026 = [
    G("g1", "2026-10-17T16:00:00.000Z", "Indiana", "Ohio State"),            # B10 Update 2, 11:00 CT
    G("g2", "2026-10-17T23:00:00.000Z", "Miami", "Florida State"),           # ACC, 19:00 ET
    G("g3", "2026-10-17T16:00:00.000Z", "Bowling Green", "Miami (OH)"),      # MAC, 12:00 ET
    G("g4", "2026-10-17T19:00:00.000Z", "Kansas State", "Kansas"),           # B12: the feed says 14:30 CT
    G("g5a", "2026-10-17T23:30:00.000Z", "Houston", "Oklahoma State"),       # stored twice
    G("g5b", "2026-10-17T23:30:00.000Z", "Houston", "Oklahoma State"),
    G("g6", "2026-10-17T16:30:00.000Z", "Maryland", "Rutgers"),              # ...and a rematch in December
    G("g6b", "2026-12-05T17:00:00.000Z", "Maryland", "Rutgers"),
    G("g7", "2026-10-18T00:00:00.000Z", "UL Monroe", "Louisiana Tech"),      # Sun Belt
    G("g8", "2026-10-17T22:00:00.000Z", "Oregon State", "Washington State"), # Pac-12
    G("g9", "2026-10-17T19:30:00.000Z", "Michigan", "Penn State"),           # the feed misspells Penn St.
    G("g11", "2026-10-17T16:00:00.000Z", "West Virginia", "Cincinnati"),     # an empty report
    G("g12", "2026-10-18T00:00:00.000Z", "Troy", "South Alabama"),           # Sun Belt, mini-trees only
    # the 2026 archive
    G("a1", "2026-09-12T23:00:00.000Z", "Kentucky", "Alabama"),
    G("a2", "2026-09-20T03:30:00.000Z", "Texas Tech", "Utah"),               # date + 27.5h: in
    G("a3", "2026-09-19T07:00:00.000Z", "Baylor", "TCU"),                    # date + 7h: out
    G("a4", "2026-09-20T13:00:00.000Z", "Arizona", "Arizona State"),         # date + 37h: out
    G("a5", "2026-09-19T08:00:00.000Z", "Iowa State", "Kansas State"),       # date + 8h exactly: in
    G("a6", "2026-09-20T12:00:00.000Z", "Oklahoma State", "BYU"),            # date + 36h exactly: in
    G("m1", "2026-09-12T16:00:00.000Z", "Akron", "Miami (OH)"),
    G("m2", "2026-09-19T16:00:00.000Z", "Miami", "Central Michigan"),
]
SCHED_2025 = [
    G("s25", "2025-09-27T23:30:00.000Z", "Georgia", "Alabama"),
    G("n1", "2025-10-11T15:30:00.000Z", "Oklahoma", "Texas", neutral=True),  # Red River, Dallas
    G("f1", "2025-11-01T19:30:00.000Z", "Georgia", "Florida", neutral=True),
    G("f2", "2025-11-01T23:00:00.000Z", "Florida", "Florida State"),          # two Florida games that day
    G("acc25", "2025-09-13T23:00:00.000Z", "Stanford", "Boston College"),
    G("b25", "2025-09-20T16:00:00.000Z", "Indiana", "Illinois"),
    G("x25", "2025-10-04T19:00:00.000Z", "Iowa State", "Kansas State"),
    G("c1", "2025-12-20T20:00:00.000Z", "Indiana", "Alabama"),                # CFP, on campus: Alabama away
    # games on a day a 2025 night-before column is named for (Friday, Thursday)
    G("fri25", "2025-09-12T23:30:00.000Z", "Houston", "Colorado"),            # B12, Friday 7:30 pm ET
    G("thu25", "2025-09-11T23:30:00.000Z", "Wake Forest", "NC State"),        # ACC, Thursday 7:30 pm ET
    G("fri25a", "2025-09-19T23:00:00.000Z", "Syracuse", "Clemson"),           # ACC, Friday: its Thursday is the day before
    G("fri25s", "2025-11-28T20:30:00.000Z", "Mississippi State", "Ole Miss"), # SEC, Black Friday
]


def plant(root):
    lat = os.path.join(root, "data", "ncaaf", "latest")
    os.makedirs(lat, exist_ok=True)
    for yr, games in ((2025, SCHED_2025), (2026, SCHED_2026)):
        with gzip.open(os.path.join(lat, "schedule-%d.json.gz" % yr), "wt", encoding="utf-8") as fh:
            json.dump({"season": yr, "games": games}, fh)


def team(name, rows, display=None):
    return {"teamName": name, "teamDisplayName": display or name, "teamImage": IMG, "teamColor": IMG,
            "teamTextColor": IMG, "rows": [{"name": n, "status": s, "exemptStatus":
                                             "Exempt" if s == "Exempt" else "NonExempt"} for n, s in rows]}


def report(label, zone, kdate, ktime, pdate, ptime, away, home):
    return {"ReportType": label, "conferenceTimeZone": zone, "conferenceImage": IMG, "backgroundImage": IMG,
            "footer": {"date": kdate, "time": ktime, "location": "Somewhere, ST", "networkImage": IMG,
                       "networkAlternateImage": IMG, "venueImage": ""},
            "publishDate": pdate, "postedTime": ptime, "publishDayOfWeek": "Friday", "gameNeutral": False,
            "outCombined": 1, "statusReportOrder": ["Out", "Doubtful", "Questionable", "Available"],
            "games": [away, home]}


OSU = [("WR #0 Brandon Inniss", "Available"), ("S #1 Earl Little Jr.", "Out"),
       ("DE #2 Kenyatta Jackson Jr.", "Doubtful"), ("EDG #9 Some Edge", "Out"),
       ("ATH #8 Ath Player", "Questionable"), ("WR Kris Hughes", "Out"),
       ("RB #26 Chase Belcher ", "Out"), ('DB #4 Karle "KJ" Lacey Jr.', "Out"),
       ("DL #90 Earnest Greene, III", "Out"), ("S #7 Sherrod Covil, Jr.", "Out"),
       ("S #7 Sherrod Covil Jr.", "Out"), ("LB #12", "Out"), ("McShane", "Out"),
       ("LB #44 Exempt Guy", "Exempt"), ("LB #45 Odd Status", "Suspended"),
       ("CB #21 Two Ways", "Out"), ("CB #21 Two Ways", "Questionable"),
       ("LB #55 Image Status", IMG)]
IND = [("DB #0 Carson Williams", "Available"), ("RB #1 Turbo Richard", "Questionable")]


class Feeds:
    """The planted sources. `fail` holds (endpoint, conf) pairs that raise."""

    def __init__(self):
        self.ind = list(IND)
        self.osu = list(OSU)
        self.fail = set()
        self.calls = []
        self.arch_rows_extra = []
        self.kick = {}               # B10 report id -> the kickoff time the feed prints
        self.drop = set()            # B10 report ids the feed no longer lists
        self.pac_note = "Third Report"
        self.sbc_games = None        # a planted Sun Belt game list, in place of the default

    def publish(self, conf):
        if conf == "B10":
            return {k: v for k, v in self._b10().items() if k not in self.drop}
        return self._other(conf)

    def _b10(self):
        return {
            "3169": report("Update 2", "CT", "2026-10-17", self.kick.get("3169", "11:00:00"), "2026-10-16", "19:00:00",
                           team("Ohio St.", self.osu, "Ohio State"), team("Indiana", self.ind)),
            "3170": report("Update 2", "CT", "2026-10-17", "14:30:00", "2026-10-16", "19:00:00",
                           team("Penn St", [("QB #1 A Passer", "Out")]),
                           team("Michigan", [("QB #2 B Passer", "Out")])),
            "3171": report("Update 2", "CT", "2026-10-17", "11:30:00", "2026-10-16", "19:00:00",
                           team("Rutgers", [("RB #3 Rutgers Back", "Out")]),
                           team("Maryland", [("WR #4 Terp Wideout", "Doubtful")])),
        }

    def _other(self, conf):
        if conf == "ACC":
            return {"3226": report("Update 2", "ET", "2026-10-17", "19:00:00", "2026-10-16", "20:00:00",
                                   team("Florida St.", [("QB #1 Nole Passer", "Out")], "Florida State"),
                                   team("Miami (FL)", [("DL #9 Cane Rusher", "Doubtful")], "Miami"))}
        if conf == "MAC":
            return {"3237": report("Update 2", "ET", "2026-10-17", "12:00:00", "2026-10-16", "20:00:00",
                                   team("Miami (OH)", [("QB #7 Redhawk Passer", "Out")], "Miami"),
                                   team("Bowling Green", [("LB #8 Falcon Backer", "Available")])),
                    "3200": report("Report Pending", "ET", "2026-10-17", "12:00:00", "2026-10-17", "11:00:00",
                                   team("Ball St.", [("QB #1 Pending One", "Out")]),
                                   team("Bowling Green", [("QB #2 Pending Two", "Out")])),
                    "3252": dict(report("Game Day", "ET", "2026-10-17", "12:00:00", "2026-10-17", "11:00:00",
                                        team("Kent St.", [("QB #1 Lone Flash", "Out")]), None),
                                 games=[team("Kent St.", [("QB #1 Lone Flash", "Out")])])}
        if conf == "B12":
            return {"4001": report("Update 2", "CT", "2026-10-17", "14:30:00", "2026-10-16", "21:00:00",
                                   team("Kansas", [("QB #1 Jay Hawk", "Out")]),
                                   team("Kansas St.", [("QB #2 Wild Cat", "Out")])),
                    "4002": report("Update 2", "CT", "2026-10-17", "18:30:00", "2026-10-16", "21:00:00",
                                   team("Oklahoma St.", [("QB #1 Cowboy Passer", "Out")]),
                                   team("Houston", [("QB #2 Coog Passer", "Out")])),
                    "4003": report("Update 2", "CT", "2026-10-17", "11:00:00", "2026-10-16", "21:00:00",
                                   team("Cincinnati", []), team("West Virginia", []))}
        return {}                                                 # SEC: nothing this week

    def sbc(self):
        if self.sbc_games is not None:
            return {"config": {}, "games": self.sbc_games}
        return {"config": {"emptyPlayerMessage": "Report will be posted to the institution's conference website.",
                           "helmetBase": "https://example.invalid/helmets/"},
                "games": [{"gameId": "2026-10-17-ULM-LA Tech", "dateISO": "2026-10-17",
                           "updatedAtUTC": "2026-10-16T13:00:00.5092200Z", "kickoff": "19:00:00",
                           "kickoffUTC": "2026-10-18T00:00:00Z", "timeZone": "Central Standard Time",
                           "notes": "Second Report", "venue": "Malone Stadium",
                           "away": {"name": "LA Tech", "players": [
                               {"name": "Jamari Miller ", "position": "WR", "status": "Doubtful"},
                               {"name": "Ryan Green", "position": "ILB", "status": "Out for Season"},
                               {"name": "Blank Position", "position": "", "status": "Out"}]},
                           "home": {"name": "ULM", "players": []}}]}

    def pac(self):
        return {"config": {}, "games": [{"gameId": "2026-10-17-Oregon State-Washington State",
                                         "updatedAtUTC": "2026-10-16T09:00:00.0256021Z",
                                         "kickoffUTC": "2026-10-17T22:00:00Z", "notes": self.pac_note,
                                         "away": {"name": "Washington State", "players": [
                                             {"name": "Kyle Peterson", "position": "DB", "status": "Out"}]},
                                         "home": {"name": "Oregon State", "players": [
                                             {"name": "Kord Shaw", "position": "ILB", "status": "Out"}]}}]}

    def archive(self, conf):
        """get-archive-public, the 2026 season."""
        days = ["Initial", "Update 1", "Update 2", "Game Day"]

        def row(tm, opp, week, player, num, st, extra=None):
            r = {"Team": tm, "TeamDisplay": tm, "Opponent": opp, "OpponentDisplay": opp, "Week": week,
                 "WeekNum": 2, "Player": player, "Number": num}
            r.update({d: s for d, s in zip(days, st)})
            r.update(extra or {})
            return r
        if conf == "SEC":
            wk = "Sat, 12 Sep 2026 00:00:00 GMT"
            return {"loaded": True, "report_days": days, "conferenceLogo": IMG, "data": [
                row("Alabama", "at Kentucky", wk, "AK Dear", "#0", ["Questionable", "Questionable", "Out", "Out"]),
                row("Alabama", "at Kentucky", wk, "Noah Rogers", "#5", ["Available", "Available", "Available", "Out"]),
                row("Alabama", "at Kentucky", wk, "Jireh Edwards", "#10", ["-", "-", "-", "Out"]),
                row("Alabama", "at Kentucky", wk, "Tim Keenan III", "#96", ["Probable", "Doubtful", "Doubtful", "Out"]),
                row("Alabama", "at Kentucky", wk, "Daylen Austin", "#3", ["Out", "Exempt", "Exempt", "Exempt"]),
                row("Kentucky", "vs. Alabama", wk, "Wildcat One", "#1", ["-", "-", "-", "Out"]),
                row("Kentucky", "at Alabama", wk, "Wrong Side", "#2", ["Out", "Out", "Out", "Out"]),
            ] + self.arch_rows_extra}
        if conf == "B12":
            return {"loaded": True, "report_days": days, "data": [
                row("Texas Tech", "vs. Utah", "Sat, 19 Sep 2026 00:00:00 GMT", "Late Night", "#1", ["Out"] * 4),
                row("Baylor", "vs. TCU", "Sat, 19 Sep 2026 00:00:00 GMT", "Too Early", "#2", ["Out"] * 4),
                row("Arizona", "vs. Arizona St.", "Sat, 19 Sep 2026 00:00:00 GMT", "Too Late", "#3", ["Out"] * 4),
                row("Iowa St.", "vs. Kansas St.", "Sat, 19 Sep 2026 00:00:00 GMT", "Edge Early", "#4", ["Out"] * 4),
                row("Oklahoma St.", "vs. BYU", "Sat, 19 Sep 2026 00:00:00 GMT", "Edge Late", "#5", ["Out"] * 4),
            ]}
        if conf == "MAC":
            gd = lambda tm, opp, wk, p, n, s: {"Team": tm, "TeamDisplay": tm, "Opponent": opp,  # noqa: E731
                                                "OpponentDisplay": opp.replace(" (OH)", "").replace(" (FL)", ""),
                                                "Week": wk, "WeekNum": 2, "Player": p, "Number": n,
                                                "Initial": "-", "Game Day": s}
            return {"loaded": True, "report_days": ["Game Day"], "conferenceLogo": IMG, "data": [
                gd("Akron", "vs. Miami (OH)", "Sat, 12 Sep 2026 00:00:00 GMT", "Zip Out", "#1", "Out"),
                gd("Miami (OH)", "at Akron", "Sat, 12 Sep 2026 00:00:00 GMT", "Hawk Out", "#2", "Out"),
                gd("Central Mich.", "at Miami (FL)", "Sat, 19 Sep 2026 00:00:00 GMT", "Chip Out", "#3", "Out"),
            ]}
        if conf == "ACC":
            return {"error": "Invalid parameters"}
        return {"loaded": True, "report_days": days, "data": []}

    def legacy(self, conf):
        """get-archive-legacy-public, 2025."""
        def row(tm, opp, week, player, num, cols):
            r = {"Team": tm, "TeamDisplay": tm, "Opponent": opp, "OpponentDisplay": opp, "Week": week,
                 "WeekNum": 5, "Player": player, "Number": num}
            r.update(cols)
            return r
        full = ["Initial", "Thursday", "Friday", "Gameday"]
        if conf == "SEC":
            return {"loaded": True, "report_days": full, "data": [
                row("Alabama", "at Georgia", "Sat, 27 Sep 2025 00:00:00 GMT", "Jalen Hale", "#8",
                    {"Initial": "Available", "Thursday": "Available", "Friday": "Out", "Gameday": "Out"}),
                row("Alabama", "at Georgia", "Sat, 27 Sep 2025 00:00:00 GMT", "Tim Keenan III", "#96",
                    {"Initial": "Probable", "Thursday": "Probable", "Friday": "Available", "Gameday": "Out"}),
                row("Texas", "vs. Texas", "Sat, 11 Oct 2025 00:00:00 GMT", "Red River", "#11",
                    {"Initial": "Out", "Thursday": "Out", "Friday": "Doubtful", "Gameday": "Out"}),
                row("Florida", "vs. Florida", "Sat, 01 Nov 2025 00:00:00 GMT", "Two Games", "#12",
                    {"Initial": "Out", "Thursday": "Out", "Friday": "Out", "Gameday": "Out"}),
                row("Ole Miss", "at Mississippi State", "Fri, 28 Nov 2025 00:00:00 GMT", "Egg Bowl", "#6",
                    {"Initial": "Out", "Thursday": "Out", "Friday": "Out", "Gameday": "Out"}),
            ]}
        if conf == "ACC":
            return {"loaded": True, "report_days": ["Initial", "Thursday", "Gameday"], "data": [
                row("Boston College", "at Stanford", "Sat, 13 Sep 2025 00:00:00 GMT", "McShane", "#35",
                    {"Initial": "Out", "Thursday": "Out", "Gameday": "Out"}),
                row("NC State", "at Wake Forest", "Thu, 11 Sep 2025 00:00:00 GMT", "Thursday Pack", "#4",
                    {"Initial": "Out", "Thursday": "Out", "Gameday": "Out"}),
                row("Clemson", "at Syracuse", "Fri, 19 Sep 2025 00:00:00 GMT", "Friday Tiger", "#5",
                    {"Initial": "Out", "Thursday": "Out", "Gameday": "Out"})]}
        if conf == "B10":
            return {"loaded": True, "report_days": ["Gameday"], "data": [
                row("Illinois", "at Indiana", "Sat, 20 Sep 2025 00:00:00 GMT", "Jaheim Clarke", "#6",
                    {"Gameday": "Out"})]}
        if conf == "B12":
            return {"loaded": True, "report_days": full, "data": [
                row("Kansas St.", "at Iowa St.", "Sat, 04 Oct 2025 00:00:00 GMT", "Friday Doubt", "#7",
                    {"Initial": "Questionable", "Thursday": "Doubtful", "Friday": "Doubtful", "Gameday": "Out"}),
                row("Colorado", "at Houston", "Fri, 12 Sep 2025 00:00:00 GMT", "Friday Buff", "#9",
                    {"Initial": "Out", "Thursday": "Out", "Friday": "Out", "Gameday": "Out"})]}
        if conf == "CFP":
            return {"loaded": True, "report_days": full, "data": [
                row("#9 Alabama", "vs. #9 Alabama", "Sat, 20 Dec 2025 00:00:00 GMT", "Seeded Tide", "#20",
                    {"Initial": "Out", "Thursday": "Out", "Friday": "Out", "Gameday": "Out"})]}
        return {"error": "Invalid parameters"}

    def post(self, url, body):
        conf = body["conference"]
        ep = url.rsplit("/", 1)[-1]
        self.calls.append((ep, conf))
        if (ep, conf) in self.fail:
            raise urllib.error.URLError("planted outage")
        if ep == "get-publish-public":
            return copy.deepcopy(self.publish(conf))
        if ep == "get-archive-public":
            return copy.deepcopy(self.archive(conf))
        if ep == "get-archive-legacy-public":
            return copy.deepcopy(self.legacy(conf))
        raise AssertionError("unexpected endpoint " + url)

    def get(self, url):
        key = "SBC" if "sunbelt" in url else "PAC12"
        self.calls.append(("report.json", key))
        if ("report.json", key) in self.fail:
            raise urllib.error.URLError("planted outage")
        return copy.deepcopy(self.sbc() if key == "SBC" else self.pac())


def snaps(root):
    return [p for _st, p in CI.snapshot_paths(root)]


def stored(root):
    """(path, text) of every file under root, gzips opened."""
    for d, _x, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            raw = open(p, "rb").read()
            if f.endswith(".gz"):
                raw = gzip.decompress(raw)
            yield p, raw.decode("utf-8", "replace")


def probe(root):
    with open(CI.probe_path(2026, root), encoding="utf-8") as fh:
        return json.load(fh)


def by_name(players):
    return {p["name"]: p for p in players or []}


QUIET = []
log = QUIET.append

root = tempfile.mkdtemp(prefix="cfbinj-")
try:
    plant(root)
    F = Feeds()

    # ══════════════════════════════════════════════════════════════════
    section("1. THE PIECES: strip, names, zones, rows, statuses, positions")
    # ══════════════════════════════════════════════════════════════════
    eq(CI.strip_images({"a": IMG, "b": [IMG, {"c": " data:x", "d": "ok"}], "e": "metadata: fine"}),
       {"b": [{"d": "ok"}], "e": "metadata: fine"}, "every data: string is stripped, at any depth")
    known = {"Penn State", "USC", "Miami", "Miami (OH)", "UL Monroe", "Louisiana Tech", "Indiana", "San José State"}
    eq([CI.team_name(x, known) for x in ("Penn St.", "Southern California", "Miami (FL)", "Miami (OH)",
                                         "ULM", "LA Tech", "#1 Indiana", "  Indiana ", "San Jose St.")],
       ["Penn State", "USC", "Miami", "Miami (OH)", "UL Monroe", "Louisiana Tech", "Indiana", "Indiana",
        "San José State"], "exact names and the alias table resolve (a CFP seed dropped)")
    eq([CI.team_name(x, known) for x in ("Penn St", "Miami (Ohio)", "Mississippi St.", "", None)],
       [None] * 5, "⛔ an unknown name fails closed (no fuzzy match; an alias whose target is not "
       "in the schedule is unknown too)")
    eq(CI.ALIASES, {
        "Arizona St.": "Arizona State", "Ball St.": "Ball State", "Central Mich.": "Central Michigan",
        "Eastern Mich.": "Eastern Michigan", "Florida St.": "Florida State", "Iowa St.": "Iowa State",
        "Kansas St.": "Kansas State", "Kent St.": "Kent State", "Miami (FL)": "Miami",
        "Michigan St.": "Michigan State", "Mississippi St.": "Mississippi State", "Ohio St.": "Ohio State",
        "Oklahoma St.": "Oklahoma State", "Penn St.": "Penn State", "Sacramento St.": "Sacramento State",
        "Southern California": "USC", "Western Mich.": "Western Michigan", "Boise St.": "Boise State",
        "Central Conn. St.": "Central Connecticut", "FIU": "Florida International", "Fresno St.": "Fresno State",
        "Jacksonville St.": "Jacksonville State", "Mississippi Val.": "Mississippi Valley State",
        "North Dakota St.": "North Dakota State", "San Diego St.": "San Diego State",
        "San Jose St.": "San José State", "South Fla.": "South Florida", "Tarleton St.": "Tarleton State",
        "ULM": "UL Monroe", "LA Tech": "Louisiana Tech"},
       "ALIASES is exactly the measured table (map_feed §4): nothing added by guesswork")
    eq([CI._iso(CI.local_to_utc(*a)) for a in (
        ("2026-10-17", "11:00:00", "CT"), ("2026-10-17", "12:00:00", "ET"), ("2026-11-14", "11:00:00", "CT"),
        ("2026-11-14", "12:00", "ET"), ("2026-10-16", "19:00:00", "CT"))],
       ["2026-10-17T16:00:00Z", "2026-10-17T16:00:00Z", "2026-11-14T17:00:00Z", "2026-11-14T17:00:00Z",
        "2026-10-17T00:00:00Z"], "CT and ET wall times reach UTC, with US daylight time ending in November")
    eq([CI.local_to_utc("2026-10-17", "11:00:00", "MT"), CI.local_to_utc("2026-10-17", "", "CT"),
        CI.local_to_utc("2026-10-17", "TBA", "ET")], [None, None, None],
       "an unknown zone or a missing kickoff time gives no time, never a guess")
    eq([CI.parse_row(x) for x in ("WR Kris Hughes", "RB #26 Chase Belcher ", 'DB #4 Karle "KJ" Lacey Jr.',
                                  "DL #90 Earnest Greene, III", "38 #38 Karsten Busch", "LB #12", "McShane", "")],
       [("WR", None, "Kris Hughes"), ("RB", "26", "Chase Belcher"), ("DB", "4", 'Karle "KJ" Lacey Jr.'),
        ("DL", "90", "Earnest Greene, III"), ("38", "38", "Karsten Busch"), None, None, None],
       "\"POS #NUM Name\": no jersey, trailing space, quoted nickname, comma suffix; no name = unparsed")
    eq([CI.canon_status(x) for x in ("Out", " out  for season", "Doubtful", "Game Time Decision",
                                     "Out - (1st Half)", "Exempt", "Suspended", "", None, "-")],
       ["Out", "Out for Season", "Doubtful", "Game Time Decision", "Out - (1st Half)", "unknown", "unknown",
        "unknown", "unknown", "unknown"], "⛔ Exempt and anything outside the known set are unknown")
    eq([CI.position_of(x)[0] for x in ("EDG", "JCK", "STR", "N/S", "DS", "IOL", "CB", "ATH", "P/K", "", None)],
       ["EDGE", "EDGE", "DB", "DB", "DB", "OL", "CB", "ATH", "P/K", None, None],
       "college codes map to the NFL codes; an unknown code stays raw")
    eq((CI.fold("Sherrod Covil, Jr.") == CI.fold("Sherrod Covil Jr."), CI.fold("D’Angelo O'Neal"),
        CI.fold("Anthony Jones Jr.") == CI.fold("Anthony Jones")),
       (True, "d angelo o neal", False), "folding drops punctuation only (a suffix still tells two players apart)")
    eq([CI._iso(CI.pick_cutoff(k)) for k in ("2026-10-17T16:00:00Z", "2026-10-18T00:00:00Z", "2026-11-14T17:00:00Z")],
       ["2026-10-17T12:59:59Z", "2026-10-17T12:59:59Z", "2026-11-14T13:59:59Z"],
       "pick time is the last second before 9:00 ET on the game's ET day (8pm ET Saturday is Saturday)")
    eq(CI.OUT_STATUSES, ("out", "out for season", "doubtful"), "counted as out: Out, Out for Season, Doubtful")
    eq((CI.MAX_AGE_H, CI.FETCH_MAX_AGE_H), (36, 6), "the up-to-date bars are the design's 36 h and 6 h")
    OUTP = {"name": "Gone Guy", "number": "1", "position": "QB", "position_raw": "QB", "status": "Out"}
    eq((CI.out_players(None, "X"), CI.out_players({"teams": {"A": []}, "current": True}, "B"),
        CI.out_players({"teams": {"A": []}, "current": True}, "A")),
       (None, None, []), "⛔ no report, or a team the report does not carry: None (no reading), never zero")
    eq((CI.out_players({"teams": {"A": [OUTP]}, "current": False}, "A"), CI.out_players({"teams": {"A": [OUTP]}}, "A"),
        [p["name"] for p in CI.out_players({"teams": {"A": [OUTP]}, "current": True}, "A") or []]),
       (None, None, ["Gone Guy"]), "🔴 a report that is not current (or was never judged) gives no reading: "
       "§2, it is not shown and does not reach the model")

    # ══════════════════════════════════════════════════════════════════
    section("2. ONE PASS: accepted, refused, and why")
    # ══════════════════════════════════════════════════════════════════
    R1 = T("2026-10-17T07:15:00Z")
    r1 = CI.run(root=root, now=R1, post=F.post, get=F.get, log=log)
    pr = probe(root)
    ck("the pass is ok and wrote one snapshot", r1["ok"] and r1["wrote"] and len(snaps(root)) == 1,
       "ok %s wrote %s snapshots %d" % (r1["ok"], r1["wrote"], len(snaps(root))))
    S1 = CI._jz(snaps(root)[0])
    reps = {r["game_id"]: r for r in S1["reports"]}
    eq(sorted(reps), ["g1", "g2", "g3", "g6", "g7", "g8"], "exactly the joinable reports are accepted")
    reasons = {(x["source"], x["id"]): x["reason"] for x in pr["refused"]}
    eq(reasons.get(("B10", "3170")), "unknown team name", "⛔ an unknown name (\"Penn St\") is refused")
    ck("...and named in the probe", "B10: Penn St" in pr["unknown"]["names"], str(pr["unknown"]["names"]))
    eq(reasons.get(("MAC", "3200")), "report pending", "⛔ \"Report Pending\" is not a report, rows or not")
    ck("a report listing one team is refused", "1 team" in str(reasons.get(("MAC", "3252"))),
       str(reasons.get(("MAC", "3252"))))
    ck("⛔ a kickoff that is not the schedule's to the minute is refused",
       "kickoff" in str(reasons.get(("B12", "4001"))), str(reasons.get(("B12", "4001"))))
    ck("⛔ a report matching two stored games is refused", "2 stored games" in str(reasons.get(("B12", "4002"))),
       str(reasons.get(("B12", "4002"))))
    eq(reasons.get(("B12", "4003")), "empty report", "⛔ an empty report is not a report")
    g3 = reps.get("g3") or {}
    eq((g3.get("away"), g3.get("home"), sorted(g3.get("teams") or {})),
       ("Miami (OH)", "Bowling Green", ["Bowling Green", "Miami (OH)"]),
       "🔴 MAC's Miami (OH), whose display name is \"Miami\", joins its own game (teamName, never the display)")
    eq((reps.get("g2") or {}).get("teams", {}).keys() >= {"Florida State", "Miami"}, True,
       "Miami (FL) is the schedule's Miami")
    eq((reps.get("g6") or {}).get("kickoff"), "2026-10-17T16:30:00Z", "the report joins this week's game, "
       "not the December rematch")
    g1 = reps.get("g1") or {}
    eq((g1.get("away"), g1.get("home"), g1.get("posted_at"), g1.get("kickoff"), g1.get("label")),
       ("Ohio State", "Indiana", "2026-10-17T00:00:00Z", "2026-10-17T16:00:00Z", "Update 2"),
       "games[0] is away, games[1] home; posted 19:00 CT Friday = 00:00Z")
    osu = by_name((g1.get("teams") or {}).get("Ohio State"))
    ind = by_name((g1.get("teams") or {}).get("Indiana"))
    eq(sorted(ind), ["Turbo Richard"], "Indiana's own players are Indiana's (and Available ones are not stored)")
    eq((g1.get("listed") or {}).get("Ohio State"), 14, "...while `listed` keeps how many were on the report")
    eq((osu.get("Some Edge") or {}).get("position"), "EDGE", "EDG is stored as EDGE")
    eq(((osu.get("Ath Player") or {}).get("position"), (osu.get("Ath Player") or {}).get("position_raw")),
       ("ATH", "ATH"), "an unknown code (ATH) stays raw")
    eq((osu.get("Kris Hughes") or {}).get("number", "missing"), None, "no jersey: number None")
    ck("a trailing space is not part of the name", "Chase Belcher" in osu, sorted(osu))
    ck("a quoted nickname and a comma suffix are kept as written",
       'Karle "KJ" Lacey Jr.' in osu and "Earnest Greene, III" in osu, sorted(osu))
    eq(sum(1 for n in osu if "Covil" in n), 1, "🔴 one player listed twice is kept once")
    eq((osu.get("Two Ways") or {}).get("status"), "unknown", "one player with two statuses is unknown")
    eq((osu.get("Exempt Guy") or {}).get("status"), "unknown", "⛔ Exempt is unknown, never healthy")
    eq((osu.get("Odd Status") or {}).get("status"), "unknown", "a status outside the known set is unknown")
    ck("...and counted in the probe", pr["unknown"]["statuses"].get("Suspended") == 1, str(pr["unknown"]))
    ck("no player named from a row that did not parse", not any(n.startswith("#") for n in osu), sorted(osu))
    eq(pr["unparsed"]["count"], 2, "the two rows that do not parse (\"LB #12\", \"McShane\") are counted")
    j1 = CI.report_for("g1", R1, root) or {}
    eq(j1.get("current"), True, "the report, read live right after the pass, is current")
    eq(sorted(p["name"] for p in CI.out_players(j1, "Ohio State") or []),
       sorted(["Earl Little Jr.", "Kenyatta Jackson Jr.", "Some Edge", "Kris Hughes", "Chase Belcher",
               'Karle "KJ" Lacey Jr.', "Earnest Greene, III", "Sherrod Covil, Jr."]),
       "out_players: Out and Doubtful only (Questionable, unknown and Exempt are not)")
    g7 = reps.get("g7") or {}
    eq(sorted(g7.get("teams") or {}), ["Louisiana Tech"], "⛔ Sun Belt: a team with nobody listed is absent, "
       "never an empty list (the feed posts it elsewhere)")
    j7 = CI.report_for("g7", R1, root) or {}
    eq((j7.get("current"), CI.out_players(j7, "UL Monroe")), (True, None), "...so it gives no reading")
    eq(sorted(p["name"] for p in CI.out_players(j7, "Louisiana Tech") or []),
       ["Blank Position", "Jamari Miller", "Ryan Green"], "Out for Season and Doubtful count; the name is trimmed")
    eq((reps.get("g8") or {}).get("posted_at"), "2026-10-16T09:00:00Z", "Pac-12's updatedAtUTC is its posted time")
    leaks = [os.path.relpath(p, root) for p, txt in stored(root) if "data:" in txt]
    eq(leaks, [], "🔴 no stored file holds a data: string (images, and a raw status that was one)")

    # ══════════════════════════════════════════════════════════════════
    section("3. THE ARCHIVES: joined by date window, stored once, refreshed daily")
    # ══════════════════════════════════════════════════════════════════
    A26 = CI._jz(CI.archive_path(2026, root)) or {}
    A25 = CI._jz(CI.archive_path(2025, root)) or {}
    rows26 = [r for c in (A26.get("conferences") or {}).values() for r in c["rows"]]
    rows25 = [r for c in (A25.get("conferences") or {}).values() for r in c["rows"]]
    gids26 = {r["game_id"] for r in rows26}
    ck("an archive row joins a game starting 27.5 h after its date (a late kickoff)", "a2" in gids26, sorted(gids26))
    ck("⛔ ...and none starting 7 h after it", "a3" not in gids26, sorted(gids26))
    ck("⛔ ...or 37 h after it", "a4" not in gids26, sorted(gids26))
    ck("the window's edges, exactly 8 h and 36 h, are inside", {"a5", "a6"} <= gids26, sorted(gids26))
    eq(sorted(r["player"] for r in rows26 if r["game_id"] == "a1" and r["team"] == "Kentucky"), ["Wildcat One"],
       "⛔ \"at Alabama\" for the home team joins nothing (\"at\" means away)")
    eq({r["player"]: (r["game_id"], r["opponent"]) for r in rows26 if r["player"] in ("Hawk Out", "Chip Out")},
       {"Hawk Out": ("m1", "Akron"), "Chip Out": ("m2", "Miami")},
       "🔴 MAC's Miami (OH) and Miami (FL) rows (both displayed \"Miami\") join their own games")
    eq({r["player"]: (r["game_id"], r["opponent"]) for r in rows25 if r["player"] in ("Red River", "Seeded Tide")},
       {"Red River": ("n1", "Oklahoma"), "Seeded Tide": ("c1", "Indiana")},
       "a 2025 row naming its team as its own opponent is recovered from team + date (and a CFP seed dropped)")
    ck("⛔ ...but not when the team has two games in the window",
       not any(r["player"] == "Two Games" for r in rows25), str(A25.get("conferences", {}).get("SEC", {}).get("refused")))
    ck("one archive failing (2026 ACC) is recorded and the others are still stored",
       pr["archives"]["2026"]["ACC"]["ok"] is False and {"SEC", "B12", "MAC"} <= set(A26.get("conferences") or {}),
       str(pr["archives"]["2026"].get("ACC")))
    eq(sorted(A25.get("conferences") or {}), ["ACC", "B10", "B12", "CFP", "SEC"], "the 2025 legacy archive, five parts")
    sec26 = ((A26.get("conferences") or {}).get("SEC") or {}).get("refused")
    eq(sec26, [{"team": "Kentucky", "opponent": "at Alabama", "date": "2026-09-12",
                "reason": "no stored game in the window", "n": 1}],
       "🔴 a refused archive row is NAMED (team, opponent, date, reason, rows), never only counted")
    eq(((pr["archives"].get("2026") or {}).get("SEC") or {}).get("refused"), sec26, "...in the probe too")
    eq(((pr["archives"].get("2026") or {}).get("B12") or {}).get("n_refused"), 2,
       "...which also counts them (the two B12 rows outside the window)")
    ck("...and a 2025 self-opponent row with two games is named with its reason",
       {"team": "Florida", "opponent": "vs. Florida", "date": "2025-11-01",
        "reason": "more than one stored game (names Florida as its own opponent)", "n": 1}
       in (((A25.get("conferences") or {}).get("SEC") or {}).get("refused") or []),
       str(((A25.get("conferences") or {}).get("SEC") or {}).get("refused")))

    # ══════════════════════════════════════════════════════════════════
    section("4. SNAPSHOTS: only on change; a failed source keeps its reports")
    # ══════════════════════════════════════════════════════════════════
    F.calls.clear()
    r2 = CI.run(root=root, now=T("2026-10-17T08:15:00Z"), post=F.post, get=F.get, log=log)
    ck("an unchanged pass writes no snapshot", not r2["wrote"] and len(snaps(root)) == 1,
       "wrote %s, %d snapshots" % (r2["wrote"], len(snaps(root))))
    eq([c for c in F.calls if c[0] == "get-archive-legacy-public"], [], "the 2025 archive is not fetched again")
    eq([c for c in F.calls if c[0] == "get-archive-public"], [("get-archive-public", "ACC")],
       "the 2026 archive is not refreshed within the day (only the part that failed is retried)")
    F.ind = [("DB #0 Carson Williams", "Available"), ("RB #1 Turbo Richard", "Out")]
    r3 = CI.run(root=root, now=T("2026-10-17T09:15:00Z"), post=F.post, get=F.get, log=log)
    ck("a changed status writes a new snapshot", r3["wrote"] and len(snaps(root)) == 2, str(len(snaps(root))))
    F.fail = {("get-publish-public", "ACC")}
    F.ind = [("DB #0 Carson Williams", "Doubtful"), ("RB #1 Turbo Richard", "Out")]
    R4 = T("2026-10-17T10:15:00Z")
    r4 = CI.run(root=root, now=R4, post=F.post, get=F.get, log=log)
    S3 = CI._jz(snaps(root)[-1]) or {}
    ok_others = [s for s in CI.SOURCES if s != "ACC" and (r4["sources"].get(s) or {}).get("ok")]
    eq((r4["ok"], (r4["sources"].get("ACC") or {}).get("ok"), len(ok_others)), (False, False, 6),
       "🔴 one source failing: it is marked failed, every other source still answers")
    eq([(r["game_id"], r["fetched_at"]) for r in S3.get("reports", []) if r["source"] == "ACC"],
       [("g2", "2026-10-17T07:15:00Z")], "the failed source's report is carried, with the time it was first "
       "fetched (07:15; unchanged at 08:15 and 09:15)")
    eq((S3.get("sources") or {}).get("ACC"), {"ok": False, "fetched_at": "2026-10-17T09:15:00Z"},
       "...and the snapshot says when that source last answered")
    eq(probe(root)["sources"]["ACC"].get("last_ok_at"), "2026-10-17T09:15:00Z", "the probe keeps its last good time")

    # ══════════════════════════════════════════════════════════════════
    section("5. UP TO DATE: 36 hours, 6 hours, never after kickoff")
    # ══════════════════════════════════════════════════════════════════
    a = CI.report_for("g1", R4, root)
    eq((a or {}).get("current"), True, "a report posted 16 h before kickoff, read live, is current")
    eq((a or {}).get("fetched_at"), "2026-10-17T10:15:00Z", "...and is the newest one stored")
    eq(sorted(p["name"] for p in CI.out_players(a, "Indiana") or []), ["Carson Williams", "Turbo Richard"],
       "...with its latest statuses")
    p8 = CI.report_for("g8", R4, root)
    eq((p8 or {}).get("current"), False, "⛔ a report posted 37 h before kickoff is not current")
    ck("...and says why", "37.0 hours" in str((p8 or {}).get("why")), str((p8 or {}).get("why")))
    eq((CI.report_for("g7", R4, root) or {}).get("current"), True, "one posted 35 h before kickoff is current")
    F.ind = [("DB #0 Carson Williams", "Available"), ("RB #1 Turbo Richard", "Out")]
    CI.run(root=root, now=T("2026-10-17T13:30:00Z"), post=F.post, get=F.get, log=log)    # ACC still down
    late = T("2026-10-17T16:15:00Z")
    b = CI.report_for("g2", late, root)
    eq(((b or {}).get("current"), (b or {}).get("fetched_at")), (False, "2026-10-17T07:15:00Z"),
       "⛔ a live read whose source was last read 7 h ago is not current")
    ck("...and says why", "ACC" in str((b or {}).get("why")) and "7.0 hours" in str((b or {}).get("why")),
       str((b or {}).get("why")))
    eq((CI.report_for("g2", late, root, live=False) or {}).get("current"), True,
       "the same report is current for a read that is not live (a backtest)")
    F.fail = set()
    n_before = len(snaps(root))
    r6 = CI.run(root=root, now=T("2026-10-17T15:00:00Z"), post=F.post, get=F.get, log=log)
    eq((r6["wrote"], len(snaps(root)) - n_before), (False, 0), "ACC back with what we had: no new snapshot")
    eq((CI.report_for("g2", late, root) or {}).get("current"), True,
       "...but the pass confirmed it, so the live read is current again")
    F.osu = [x if x[0] != "S #1 Earl Little Jr." else (x[0], "Available") for x in OSU]
    r7 = CI.run(root=root, now=T("2026-10-17T16:30:00Z"), post=F.post, get=F.get, log=log)
    ck("a change after kickoff is stored", r7["wrote"], str(r7["wrote"]))
    c = CI.report_for("g1", T("2026-10-17T17:00:00Z"), root)
    eq(((c or {}).get("fetched_at"), "Earl Little Jr." in by_name((c or {}).get("teams", {}).get("Ohio State"))),
       ("2026-10-17T13:30:00Z", True), "🔴 a report fetched after kickoff is never read: the game keeps the last "
       "one fetched before it")
    eq(CI.report_for("nope", late, root), None, "a game with no report: None")
    eq(CI.report_for("g1", "not a time", root), None, "⛔ report_for never raises")

    # ══════════════════════════════════════════════════════════════════
    section("6. PICK TIME: the archive's night-before column, and the 9:00 ET snapshot")
    # ══════════════════════════════════════════════════════════════════
    P26 = CI.pick_time_outs(2026, root)
    eq(sorted(p["name"] for p in (P26.get("g1") or {}).get("Indiana", [])), ["Carson Williams", "Turbo Richard"],
       "🔴 a snapshot game: the newest report fetched before 9:00 ET on game day (10:15Z, not 13:30Z)")
    eq(sorted((P26.get("g7") or {})), ["Louisiana Tech"], "a team with no reading is absent, never []")
    ck("a report that was not current at pick time gives no reading", "g8" not in P26, sorted(P26))
    eq(sorted(p["name"] for p in (P26.get("a1") or {}).get("Alabama", [])), ["AK Dear", "Tim Keenan III"],
       "2026 archive: the \"Update 2\" column; Out and Doubtful count, Exempt and later-only rows do not")
    ck("⛔ a team whose \"Update 2\" was never archived has no reading", "Kentucky" not in (P26.get("a1") or {}),
       str(P26.get("a1")))
    ck("⛔ the 2026 MAC archive (game day only) gives no reading", "m1" not in P26 and "m2" not in P26, sorted(P26))
    ck("a late-kickoff B12 game has its reading", "Late Night" in str(P26.get("a2")), str(P26.get("a2")))
    P25 = CI.pick_time_outs(2025, root)
    eq(sorted(p["name"] for p in (P25.get("s25") or {}).get("Alabama", [])), ["Jalen Hale"],
       "2025 SEC: the \"Friday\" column (Out on Friday counts; Out only on game day does not)")
    eq(sorted(p["name"] for p in (P25.get("n1") or {}).get("Texas", [])), ["Red River"],
       "...a recovered neutral-site row reads the same way")
    eq(sorted(p["name"] for p in (P25.get("acc25") or {}).get("Boston College", [])), ["McShane"],
       "2025 ACC: the \"Thursday\" column")
    eq(sorted(p["name"] for p in (P25.get("x25") or {}).get("Kansas State", [])), ["Friday Doubt"],
       "2025 Big 12: the \"Friday\" column")
    ck("⛔ the 2025 Big Ten (game day only) and the CFP give no reading", "b25" not in P25 and "c1" not in P25,
       sorted(P25))
    eq([g for g in ("fri25", "thu25", "fri25s") if g in P25], [],
       "🔴🔴 no look-ahead: a Friday game's \"Friday\" (B12, SEC) and a Thursday game's \"Thursday\" (ACC) are "
       "its game day, posted perhaps after the 9:00 ET pick time, so they give no reading")
    eq(sorted(p["name"] for p in (P25.get("fri25a") or {}).get("Clemson", [])), ["Friday Tiger"],
       "...while an ACC Friday game reads its \"Thursday\", the day before")
    eq((CI._column_known("Friday", "2025-09-13T16:00:00Z"), CI._column_known("Friday", "2025-09-14T17:00:00Z"),
        CI._column_known("Thursday", "2025-09-01T23:00:00Z"), CI._column_known("Friday", None),
        CI._column_known("Update 2", "2025-09-12T23:00:00Z")),
       (True, True, False, False, True),
       "a weekday column counts only before the game's ET day (a Saturday or Sunday game, not a Monday one); "
       "no kickoff, no reading; a relative column (\"Update 2\") always")

    # ══════════════════════════════════════════════════════════════════
    section("7. THE CURRENT ARCHIVE A DAY LATER: refetched, rewritten only on change")
    # ══════════════════════════════════════════════════════════════════
    path26 = CI.archive_path(2026, root)
    before = open(path26, "rb").read()
    F.calls.clear()
    CI.run(root=root, now=T("2026-10-18T08:20:00Z"), post=F.post, get=F.get, log=log)
    ck("a day later the current archive is fetched again", ("get-archive-public", "SEC") in F.calls, str(F.calls))
    eq([c for c in F.calls if c[0] == "get-archive-legacy-public"], [],
       "...while the 2025 archive, stored once, is never fetched again")
    ck("...and, unchanged, is not rewritten", open(path26, "rb").read() == before,
       "%d bytes before, %d after" % (len(before), os.path.getsize(path26)))
    F.arch_rows_extra = [{"Team": "Alabama", "TeamDisplay": "Alabama", "Opponent": "at Kentucky",
                          "OpponentDisplay": "at Kentucky", "Week": "Sat, 12 Sep 2026 00:00:00 GMT", "WeekNum": 2,
                          "Player": "New Name", "Number": "#77", "Initial": "Out", "Update 1": "Out",
                          "Update 2": "Out", "Game Day": "Out"}]
    CI.run(root=root, now=T("2026-10-19T08:30:00Z"), post=F.post, get=F.get, log=log)
    ck("a changed archive is rewritten", "New Name" in json.dumps(CI._jz(path26)),
       "%d bytes now" % os.path.getsize(path26))

    # ══════════════════════════════════════════════════════════════════
    section("8. A READ LONG AFTER: bounded by the game, never by the moment asked")
    # ══════════════════════════════════════════════════════════════════
    day_of = CI.report_for("g1", T("2026-10-17T15:59:00Z"), root, live=False) or {}
    month = CI.report_for("g1", T("2026-11-17T12:00:00Z"), root, live=False) or {}
    eq(day_of.get("fetched_at"), "2026-10-17T13:30:00Z", "a read on the day: the last report fetched before kickoff")
    eq((month.get("fetched_at"), month.get("current"), bool(day_of.get("teams")) and month.get("teams") == day_of.get("teams")),
       (day_of.get("fetched_at"), True, True),
       "🔴 a read a month after the game (a backtest, a grading run) finds the report a read on the day found")
    sp = os.path.join(root, "data", "ncaaf", "latest", "schedule-2026.json.gz")
    keep_sched = open(sp, "rb").read()
    try:
        with gzip.open(sp, "wt", encoding="utf-8") as fh:
            json.dump({"season": 2026, "games": [g for g in SCHED_2026 if g["id"] != "g1"]}, fh)
        eq(CI._kick_hint("g1", root), None, "(the stored schedule no longer lists g1)")
        gone = CI.report_for("g1", T("2026-11-17T12:00:00Z"), root, live=False) or {}
        eq(gone.get("fetched_at"), "2026-10-17T13:30:00Z",
           "🔴 ...and so does one with no schedule to bound it (the report's own kickoff bounds the scan)")
    finally:
        with open(sp, "wb") as fh:
            fh.write(keep_sched)

    # ══════════════════════════════════════════════════════════════════
    section("9. THE SOURCE STILL STANDS BEHIND IT: a refused or dropped report is not current")
    # ══════════════════════════════════════════════════════════════════
    rb_ = tempfile.mkdtemp(prefix="cfbinj-held-")
    try:
        plant(rb_)
        H = Feeds()
        CI.run(root=rb_, now=T("2026-10-17T02:00:00Z"), post=H.post, get=H.get, log=log)
        h1 = CI.report_for("g1", T("2026-10-17T02:30:00Z"), rb_) or {}
        eq((h1.get("current"), len(CI.out_players(h1, "Ohio State") or [])), (True, 8),
           "stored at 02:00 with eight Ohio State outs, current at 02:30")
        H.kick["3169"] = "14:30:00"            # the feed moves the kickoff; the stored schedule does not
        H.osu = [x if x[0] != "S #1 Earl Little Jr." else (x[0], "Available") for x in OSU]
        CI.run(root=rb_, now=T("2026-10-17T04:00:00Z"), post=H.post, get=H.get, log=log)
        h2 = CI.report_for("g1", T("2026-10-17T04:30:00Z"), rb_) or {}
        eq((h2.get("current"), h2.get("fetched_at")), (False, "2026-10-17T02:00:00Z"),
           "🔴🔴 B10 answered at 04:00 and REFUSED the game (its kickoff moved): the 02:00 report is not current")
        ck("...and says why, with the refusal",
           "no longer stands behind it" in str(h2.get("why")) and "is not the schedule's" in str(h2.get("why")),
           str(h2.get("why")))
        eq(CI.out_players(h2, "Ohio State"), None, "...so it gives no reading (its Out safety is Available now)")
        eq((CI.report_for("g1", T("2026-10-17T04:30:00Z"), rb_, live=False) or {}).get("current"), False,
           "...for a read that is not live too: the snapshots alone say it")
        H.kick.clear()
        CI.run(root=rb_, now=T("2026-10-17T05:00:00Z"), post=H.post, get=H.get, log=log)
        h3 = CI.report_for("g1", T("2026-10-17T05:30:00Z"), rb_) or {}
        eq((h3.get("current"), h3.get("fetched_at")), (True, "2026-10-17T05:00:00Z"),
           "the kickoff agrees again at 05:00: that report is current")
        H.drop = {"3169"}
        CI.run(root=rb_, now=T("2026-10-17T06:00:00Z"), post=H.post, get=H.get, log=log)
        h4 = CI.report_for("g1", T("2026-10-17T06:30:00Z"), rb_) or {}
        eq((h4.get("current"), "no longer stands behind it" in str(h4.get("why")), "refused" in str(h4.get("why"))),
           (False, True, False), "🔴 B10 answered at 06:00 without the game at all: not current")
        H.drop = set()
        H.fail = {("get-publish-public", "B10")}
        CI.run(root=rb_, now=T("2026-10-17T07:00:00Z"), post=H.post, get=H.get, log=log)
        eq((CI.report_for("g1", T("2026-10-17T07:30:00Z"), rb_) or {}).get("current"), False,
           "...and B10 failing afterwards does not bring the dropped report back")
        eq(CI.pick_time_outs(2026, rb_).get("g1"), None,
           "🔴 pick time (9:00 ET) gives no reading for it either: the morning card would not have shown it")
    finally:
        shutil.rmtree(rb_, ignore_errors=True)

    # ══════════════════════════════════════════════════════════════════
    section("10. THE 36-HOUR CLOCK: our first fetch, never a later posted time")
    # ══════════════════════════════════════════════════════════════════
    rc_ = tempfile.mkdtemp(prefix="cfbinj-clock-")
    try:
        plant(rc_)
        C = Feeds()
        C.sbc_games = [
            {"gameId": "2026-10-17-ULM-LA Tech", "kickoffUTC": "2026-10-18T00:00:00Z", "notes": "Initial Report",
             "away": {"name": "LA Tech", "players": [{"name": "No Clock", "position": "WR", "status": "Out"}]},
             "home": {"name": "ULM", "players": []}},
            {"gameId": "2026-10-17-Troy-South Alabama", "kickoffUTC": "2026-10-18T00:00:00Z",
             "updatedAtUTC": "2026-10-16T18:00:00.0000000Z", "notes": "Initial Report",
             "away": {"name": "South Alabama", "players": [{"name": "Early Bird", "position": "CB", "status": "Out"}]},
             "home": {"name": "Troy", "players": []}}]
        CI.run(root=rc_, now=T("2026-10-16T08:00:00Z"), post=C.post, get=C.get, log=log)   # 40 h before kickoff
        early = CI.report_for("g12", T("2026-10-16T08:30:00Z"), rc_, live=False) or {}
        eq((early.get("posted_at"), early.get("fetched_at"), early.get("current")),
           ("2026-10-16T18:00:00Z", "2026-10-16T08:00:00Z", False),
           "🔴 a report we held at 08:00 that says it was posted at 18:00 was published by 08:00: 40 h before "
           "kickoff, not current (its posted time alone would say 30 h)")
        ck("...and says so", "posted time 2026-10-16T18:00:00Z is later" in str(early.get("why")),
           str(early.get("why")))
        late_posts = [(x["source"], x["game_id"]) for x in
                      json.load(open(CI.probe_path(2026, rc_), encoding="utf-8")).get("posted_after_fetch") or []]
        ck("...and the probe lists it (a report with no posted time is not listed)",
           ("SBC", "g12") in late_posts and ("SBC", "g7") not in late_posts, str(late_posts))
        C.pac_note = "Fourth Report"            # another report changes: a new snapshot
        rc2 = CI.run(root=rc_, now=T("2026-10-16T18:00:00Z"), post=C.post, get=C.get, log=log)
        ck("(a new snapshot was written for the other report)", rc2["wrote"], str(rc2["wrote"]))
        nc = CI.report_for("g7", T("2026-10-16T18:30:00Z"), rc_, live=False) or {}
        eq((nc.get("posted_at"), nc.get("fetched_at"), nc.get("current")), (None, "2026-10-16T08:00:00Z", False),
           "🔴 a report with no posted time keeps its FIRST fetch (08:00, 40 h before kickoff) when another "
           "report changes: not current, never restamped to 18:00")
    finally:
        shutil.rmtree(rc_, ignore_errors=True)

    # ══════════════════════════════════════════════════════════════════
    section("11. THE WIRING: call cap, User-Agent, timeout")
    # ══════════════════════════════════════════════════════════════════
    rd_ = tempfile.mkdtemp(prefix="cfbinj-cap-")
    cap = CI.MAX_CALLS
    try:
        plant(rd_)
        D = Feeds()
        CI.MAX_CALLS = 3
        rcap = CI.run(root=rd_, now=R1, post=D.post, get=D.get, log=log)
        capped = [s for s, v in rcap["sources"].items() if "call cap of 3" in str(v.get("error"))]
        eq((len(D.calls), json.load(open(CI.probe_path(2026, rd_), encoding="utf-8"))["calls"], len(capped)),
           (3, 3, 4), "🔴 the call cap holds: 3 calls made, the other 4 live sources recorded as stopped by it")
    finally:
        CI.MAX_CALLS = cap
        shutil.rmtree(rd_, ignore_errors=True)
    ck("...and the real cap covers a full pass (7 live, 5 + 5 archive calls)",
       len(CI.SOURCES) + len(CI.HDI_ARCHIVE) + len(CI.HDI_LEGACY) <= CI.MAX_CALLS, str(CI.MAX_CALLS))
    import fb_weather
    sent = []

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'\xef\xbb\xbf{"ok": 1}'

    def _capture(req, timeout=None):
        sent.append((req, timeout))
        return _Resp()

    urllib.request.urlopen = _capture          # ⛔ still no network: every request is caught here
    try:
        got = (CI._post(CI.HDI + "get-publish-public", CI._body("SEC")), CI._get(CI.FEEDS["SBC"]))
        re_ = tempfile.mkdtemp(prefix="cfbinj-ua-")
        try:
            plant(re_)
            CI.run(root=re_, now=R1, log=log)          # the default post / get: the module's own helpers
        finally:
            shutil.rmtree(re_, ignore_errors=True)
    finally:
        urllib.request.urlopen = _tripwire
    eq(got, ({"ok": 1}, {"ok": 1}), "the helpers read JSON (a byte-order mark allowed)")
    eq([(r.get_method(), r.full_url) for r, _t in sent[:2]],
       [("POST", CI.HDI + "get-publish-public"), ("GET", CI.FEEDS["SBC"])], "a POST to HDI, a GET to the Sun Belt")
    eq(json.loads(sent[0][0].data.decode("utf-8")), CI._body("SEC"), "the POST body names the conference")
    eq(len(sent), 2 + len(CI.SOURCES) + len(CI.HDI_ARCHIVE) + len(CI.HDI_LEGACY),
       "a default run sends every call through those helpers")
    eq(sorted({str(r.get_header("User-agent")) for r, _t in sent}), [fb_weather.UA],
       "🔴 every request, POST and GET, carries the User-Agent")
    ck("🔴 every request has a timeout", all(t == CI.TIMEOUT for _r, t in sent) and 0 < CI.TIMEOUT <= 60,
       str(sorted({str(t) for _r, t in sent})))

    # ══════════════════════════════════════════════════════════════════
    section("12. THE CARRY WINDOW AND THE PROBE: what confirms a source")
    # ══════════════════════════════════════════════════════════════════
    rf_ = tempfile.mkdtemp(prefix="cfbinj-carry-")
    real_archive = CI.daystore.archive
    try:
        plant(rf_)
        K = Feeds()
        CI.run(root=rf_, now=T("2026-10-17T10:00:00Z"), post=K.post, get=K.get, log=log)
        pp = CI.probe_path(2026, rf_)
        os.replace(pp, pp + ".aside")
        try:
            eq((CI.report_for("g1", T("2026-10-17T10:30:00Z"), rf_) or {}).get("current"), True,
               "🔴 with no probe file, the newest snapshot's own reading of B10 (10:00) confirms a live read")
        finally:
            os.replace(pp + ".aside", pp)

        def _full(*a, **k):
            raise OSError("planted: the disk is full")
        K.pac_note = "Fourth Report"
        CI.daystore.archive = _full
        try:
            rbk = CI.run(root=rf_, now=T("2026-10-17T11:00:00Z"), post=K.post, get=K.get, log=log)
        finally:
            CI.daystore.archive = real_archive
        eq((rbk["ok"], "disk is full" in str(rbk.get("error")),
            json.load(open(pp, encoding="utf-8"))["sources"]["ACC"]["last_ok_at"]),
           (False, True, "2026-10-17T10:00:00Z"),
           "🔴 a pass whose snapshot could not be stored is not ok, and ACC's last_ok_at stays at 10:00")
        eq((CI.report_for("g2", T("2026-10-17T16:30:00Z"), rf_) or {}).get("current"), False,
           "...so that pass cannot keep a live read current 6.5 h after the last stored reading")
        K.fail = {("get-publish-public", "B10")}
        K.pac_note = "Fifth Report"
        rk2 = CI.run(root=rf_, now=T("2026-10-17T17:00:00Z"), post=K.post, get=K.get, log=log)
        eq(sorted(r["game_id"] for r in (CI._jz(rk2["snapshot"]) or {}).get("reports", []) if r["source"] == "B10"),
           ["g1", "g6"], "🔴 B10 down an hour after kickoff: its last reports are still carried")
        K.pac_note = "Sixth Report"
        rsm = CI.run(root=rf_, now=T("2026-10-17T17:00:30Z"), post=K.post, get=K.get, log=log)
        eq(("same minute" in str(rsm.get("error")),
            json.load(open(pp, encoding="utf-8"))["sources"]["SEC"]["last_ok_at"], len(snaps(rf_))),
           (True, "2026-10-17T17:00:00Z", 2),
           "🔴 a second pass in the same minute, whose reports daystore kept out, is not stored and confirms "
           "nothing (SEC's last_ok_at stays 17:00:00)")
        K.pac_note = "Seventh Report"
        rk3 = CI.run(root=rf_, now=T("2026-10-19T17:00:00Z"), post=K.post, get=K.get, log=log)
        eq((rk3["wrote"], [r["game_id"] for r in (CI._jz(rk3["snapshot"]) or {}).get("reports", [])
                           if r["source"] == "B10"]), (True, []),
           "🔴 ...but not 49 hours after kickoff: a long outage carries nothing forever")
    finally:
        CI.daystore.archive = real_archive
        shutil.rmtree(rf_, ignore_errors=True)

    # ══════════════════════════════════════════════════════════════════
    section("13. NEVER RAISES")
    # ══════════════════════════════════════════════════════════════════
    bare = tempfile.mkdtemp(prefix="cfbinj-bare-")
    try:
        def boom(*a, **k):
            raise RuntimeError("everything is down")
        rb = CI.run(root=bare, now=R1, post=boom, get=boom, log=log)
        ck("no stored schedule: not ok, no snapshot, the probe still written",
           rb["ok"] is False and rb["snapshot"] is None and os.path.exists(CI.probe_path(2026, bare)), str(rb))
        eq(CI.pick_time_outs(2026, bare), {}, "nothing stored: pick_time_outs is empty")
        plant(bare)
        rc = CI.run(root=bare, now=R1, post=boom, get=boom, log=log)
        ck("every source down: not ok, no snapshot, every error recorded",
           rc["ok"] is False and rc["snapshot"] is None and all("everything is down" in v.get("error", "")
                                                                for v in rc["sources"].values()), str(rc["sources"]))
    finally:
        shutil.rmtree(bare, ignore_errors=True)
    note("%d log lines from the passes (not shown)" % len(QUIET))
finally:
    shutil.rmtree(root, ignore_errors=True)
