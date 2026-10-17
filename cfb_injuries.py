#!/usr/bin/env python3
"""cfb_injuries.py — COLLEGE INJURY REPORTS: FETCHED, CHECKED, STORED, READ.

`[Sam, 2026-10-17]` *"use the college injury source as long as it's accurate
and up to date, we wouldn't want misinformation ruining our bets."*
The design is binding: research/cfb_injuries_design.md (§1 the data, §2 what a
report must pass, §3 the report known at pick time).

THE SOURCES, one pass per call of `run()` (the `cfb-injuries` mode):
  - HD Intelligence `get-publish-public` for SEC, ACC, B10, B12 and MAC: every
    travel-roster player as "POS #NUM Name" with a status.
  - The Sun Belt and Pac-12 `report.json`: only the players who are not
    available, with a real `updatedAtUTC`.
  - The archives, into data/ncaaf/history/injury-archive-<season>.json.gz:
    `get-archive-legacy-public` (2025; SEC, ACC, B10, B12, CFP) once while a
    conference is missing, and `get-archive-public` (the current season)
    at most once a day, rewritten only when its content changes.
  ⛔ None of these goes through `cfb.get` or the CFBD budget: no key is sent.
  ⛔ Every `data:` string (the images, 98% of the bytes) is stripped the moment
     a payload arrives, before anything can be stored or echoed.

ACCURATE (§2), or the report is refused and named in the probe:
  1. Both team names are the stored schedule's, exactly or through ALIASES.
     ⛔ Keyed on `teamName` / `Team` / `Opponent`, NEVER the display names
     ("Miami" is both Miami schools there). An unknown name fails closed.
  2. It joins exactly ONE stored schedule game: away and home in the
     report's own order, kickoff equal to the schedule's `start` to the
     minute where the feed gives one. Archive rows join the game starting
     within their date + 8h to + 36h UTC; a 2025 neutral-site row naming the
     team as its own opponent is recovered from team + date only when
     exactly one game matches.
  3. Every player row parses; one that does not is counted, never guessed.
     The same player listed twice (team, jersey, punctuation-folded name) is
     kept once (two different statuses for him: `unknown`).
  4. A status is one of STATUSES, else `unknown`. ⛔ Exempt is `unknown`,
     never healthy. "Report Pending" and an empty report are not reports.

UP TO DATE (§2, `report_for`): the last report stored for the game, fetched at
or before the moment asked and before kickoff, is `current` only if it was
published no more than MAX_AGE_H before kickoff and, for a live read, our
newest reading of its source is no more than FETCH_MAX_AGE_H old.

WHAT IS STORED (§1):
  data/ncaaf/<UTC day>/injury-reports/<hhmm>.json.gz   (daystore, write-once)
      only when the accepted reports differ from the newest stored snapshot;
      a report keeps every listed player who is NOT "Available" (its
      `listed` says how many were on it), so a quiet roster change is not a
      new snapshot. A source that failed this pass keeps its last reports.
  data/ncaaf/latest/injuries-probe-<season>.json        every attempt
  data/ncaaf/history/injury-archive-<season>.json.gz    the archives

⛔ NEVER RAISES: `run`, `report_for`, `out_players` and `pick_time_outs` catch
everything; a failure is written into the probe, never into an exit code.
⛔ No fit, pick or chance reads college injuries until the pre-registered bar
in the design (§4) passes; until then a current report may only be SHOWN (the
why). Stdlib only.
"""
import collections
import copy
import datetime
import email.utils
import glob
import gzip
import json
import os
import re
import unicodedata
import urllib.request

import daystore
from fb_weather import UA, _us_eastern_offset, kickoff_utc

ROOT = os.path.dirname(os.path.abspath(__file__))
UTC = datetime.timezone.utc
LG = "ncaaf"

HDI = "https://app.hdintelligence.com/api/"
HDI_PUBLISH = ("SEC", "ACC", "B10", "B12", "MAC")     # get-publish-public
HDI_ARCHIVE = ("SEC", "ACC", "B10", "B12", "MAC")     # get-archive-public, the current season
HDI_LEGACY = ("SEC", "ACC", "B10", "B12", "CFP")      # get-archive-legacy-public
LEGACY_SEASON = 2025
SBC = "https://sbcautostorage.blob.core.windows.net/availability-reports/%s-football/prod/report.json"
FEEDS = {"SBC": SBC % "sunbelt", "PAC12": SBC % "pac12"}
SOURCES = HDI_PUBLISH + tuple(FEEDS)

TIMEOUT = 30                 # seconds per call (SEC's publish is 7.5 MB with its images)
MAX_CALLS = 20               # per run: 7 live + 5 archive + 5 legacy, with room
ARCHIVE_REFRESH_H = 24       # the current season's archive: at most once a day
MAX_AGE_H = 36               # §2 (a): published at most this long before kickoff
FETCH_MAX_AGE_H = 6          # §2 (b): a live read needs a reading this recent
SCAN_DAYS = 7                # a report fetched longer before the moment asked is never read
CARRY_H = 48                 # a failed source's reports are carried this long past kickoff
PICK_HOUR_ET = 9             # §3: the morning card
ARCHIVE_WINDOW_H = (8, 36)   # §2: an archive row's game starts within its date + 8h to + 36h UTC

OUT_STATUSES = ("out", "out for season", "doubtful")   # lower-cased compare
STATUSES = ("Out", "Out for Season", "Doubtful", "Questionable", "Probable", "Available",
            "Game Time Decision", "Out - (1st Half)")
UNKNOWN = "unknown"
AVAILABLE = "Available"
_CANON = {s.lower(): s for s in STATUSES}

# §3, the archives' night-before column. 2025's columns were named for days:
# SEC and Big 12 "Friday", ACC "Thursday"; the 2025 Big Ten kept only a
# game-day column (no reading) and the CFP column is not fixed (no reading).
NIGHT_BEFORE = {2025: {"SEC": "Friday", "B12": "Friday", "ACC": "Thursday"}}
NIGHT_BEFORE_FROM_2026 = "Update 2"

# HDI / Sun Belt name -> the stored schedule's (CFBD) name. map_feed §4,
# exactly. ⛔ Never fuzzy: a name neither exact nor here is refused.
ALIASES = {
    "Arizona St.": "Arizona State", "Ball St.": "Ball State", "Central Mich.": "Central Michigan",
    "Eastern Mich.": "Eastern Michigan", "Florida St.": "Florida State", "Iowa St.": "Iowa State",
    "Kansas St.": "Kansas State", "Kent St.": "Kent State", "Miami (FL)": "Miami",
    "Michigan St.": "Michigan State", "Mississippi St.": "Mississippi State", "Ohio St.": "Ohio State",
    "Oklahoma St.": "Oklahoma State", "Penn St.": "Penn State", "Sacramento St.": "Sacramento State",
    "Southern California": "USC", "Western Mich.": "Western Michigan",
    # opponents seen only in the MAC archive
    "Boise St.": "Boise State", "Central Conn. St.": "Central Connecticut", "FIU": "Florida International",
    "Fresno St.": "Fresno State", "Jacksonville St.": "Jacksonville State",
    "Mississippi Val.": "Mississippi Valley State", "North Dakota St.": "North Dakota State",
    "San Diego St.": "San Diego State", "San Jose St.": "San José State", "South Fla.": "South Florida",
    "Tarleton St.": "Tarleton State",
    # the Sun Belt feed
    "ULM": "UL Monroe", "LA Tech": "Louisiana Tech",
}

# College position code -> the NFL code fb_why / fb_challengers read. A code
# not here stays raw (ATH, P/K, SP, a blank, a stray number) and is counted
# in the probe, never guessed.
POSITION_MAP = {
    "QB": "QB", "RB": "RB", "FB": "FB", "WR": "WR", "TE": "TE",
    "OL": "OL", "OT": "OT", "C": "C", "IOL": "OL",
    "DL": "DL", "DE": "DE", "DT": "DT", "EDG": "EDGE", "JCK": "EDGE",
    "LB": "LB", "ILB": "ILB", "OLB": "OLB",
    "DB": "DB", "CB": "CB", "S": "S", "STR": "DB", "N/S": "DB", "DS": "DB",
    "K": "K", "P": "P", "LS": "LS",
}

ROW = re.compile(r"^(?P<pos>\S+) (?:#(?P<num>\d{1,2}) )?(?P<name>.+?)\s*$")
SEED = re.compile(r"^#\d+\s+")
OPP = re.compile(r"^(at|vs\.)\s+(.+)$")
DAYDIR = re.compile(r"^\d{4}-\d\d-\d\d$")
HHMM = re.compile(r"^(\d{4})\.json\.gz$")
ZONES = {"ET": 0, "CT": -1}          # hours from Eastern; both keep US daylight time


class FeedError(Exception):
    """The source answered, but not with reports."""


def log_(m):
    print(m, flush=True)


# ══════════════════════════════════════════════════════════════════════
# small helpers
# ══════════════════════════════════════════════════════════════════════
def _iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if t else None


def _utc(s):
    """An ISO time with Z or an offset (any number of fractional digits) ->
    aware UTC, or None. A time with no zone is not guessed."""
    if isinstance(s, datetime.datetime):
        return s if s.tzinfo else s.replace(tzinfo=UTC)
    m = re.match(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d(?::\d\d)?)(?:\.\d+)?(Z|[+-]\d\d:?\d\d)$", str(s or "").strip())
    if not m:
        return None
    z = "+00:00" if m.group(2) == "Z" else m.group(2)
    try:
        return datetime.datetime.fromisoformat(m.group(1) + z).astimezone(UTC)
    except ValueError:
        return None


def _when(at):
    t = _utc(at) if at is not None else datetime.datetime.now(UTC)
    if t is None:
        raise ValueError("not a time: %r" % (at,))
    return t


def local_to_utc(date, time, zone):
    """A conference's wall time (CT or ET, US daylight time computed, not looked
    up) -> aware UTC, or None for an unknown zone or a missing date/time."""
    shift = ZONES.get(str(zone or "").strip().upper())
    if shift is None or not date or not time:
        return None
    s = "%s %s" % (str(date).strip(), str(time).strip())
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            naive = datetime.datetime.strptime(s, fmt)
            break
        except ValueError:
            naive = None
    if naive is None:
        return None
    return (naive - datetime.timedelta(hours=_us_eastern_offset(naive) + shift)).replace(tzinfo=UTC)


def _eastern(t):
    """UTC -> Eastern wall time (naive)."""
    naive = t.astimezone(UTC).replace(tzinfo=None)
    return naive + datetime.timedelta(hours=_us_eastern_offset(naive - datetime.timedelta(hours=5)))


def pick_cutoff(kickoff):
    """§3: the last moment BEFORE 9:00 am ET on the game's own ET day."""
    k = _utc(kickoff)
    if k is None:
        return None
    d = _eastern(k).date()
    nine = datetime.datetime(d.year, d.month, d.day, PICK_HOUR_ET)
    return (nine - datetime.timedelta(hours=_us_eastern_offset(nine))).replace(tzinfo=UTC) \
        - datetime.timedelta(seconds=1)


def strip_images(x):
    """Every `data:` string removed, at any depth (map_feed §7)."""
    if isinstance(x, dict):
        return {k: strip_images(v) for k, v in x.items() if not _is_image(v)}
    if isinstance(x, list):
        return [strip_images(v) for v in x if not _is_image(v)]
    return x


def _is_image(v):
    return isinstance(v, str) and v.lstrip()[:5].lower() == "data:"


def fold(name):
    """Punctuation folded, for telling one player listed twice from two
    players: accents dropped, lower case, every run of non-letters and
    non-digits one space. ⚠️ Not card_fb.norm, which also deletes Jr/III (two
    different players on one team can differ only by that) and exits on
    import under LEAGUE=mlb."""
    n = unicodedata.normalize("NFKD", str(name or ""))
    n = "".join(c for c in n if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", n).split())


def _clean(s):
    return " ".join(str(s if s is not None else "").split())


def team_name(raw, known):
    """The schedule's name for a feed's team name, or None. A CFP seed ("#1 ")
    is dropped; then the name is exact, or in ALIASES. ⛔ Nothing else."""
    s = SEED.sub("", _clean(raw))
    if s in known:
        return s
    a = ALIASES.get(s)
    return a if a in known else None


def canon_status(raw, tally=None):
    """One of STATUSES, else UNKNOWN. ⛔ Exempt is UNKNOWN, never healthy."""
    k = _clean(raw).lower()
    if k in _CANON:
        return _CANON[k]
    if tally is not None:
        if k == "exempt":
            tally["exempt"] += 1
        else:
            tally["statuses"][_clean(raw)] += 1
    return UNKNOWN


def position_of(raw, tally=None):
    """(position, position_raw). An unknown code stays raw and is counted."""
    code = _clean(raw).upper() if raw is not None else ""
    if code in POSITION_MAP:
        return POSITION_MAP[code], _clean(raw)
    if tally is not None:
        tally["positions"][code] += 1
    return (code or None), (None if raw is None else _clean(raw))


def _has_letter(s):
    return bool(re.search(r"[^\W\d_]", s or ""))


def parse_row(text):
    """"POS #NUM Name" -> (pos, num or None, name), or None when it does not
    parse (or the name has no letter in it). ⛔ Never guessed."""
    m = ROW.match(str(text or "").lstrip())
    if not m or not _has_letter(m.group("name")):
        return None
    return m.group("pos"), m.group("num"), m.group("name")


def _tally():
    return {"statuses": collections.Counter(), "positions": collections.Counter(), "exempt": 0,
            "unparsed": 0, "unparsed_examples": [], "duplicates": 0, "names": set()}


def _unparsed(tally, src, text):
    tally["unparsed"] += 1
    if len(tally["unparsed_examples"]) < 20:
        tally["unparsed_examples"].append("%s: %s" % (src, _clean(text)[:80]))


def _jz(p):
    try:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError, EOFError):
        return None


def _write_gz(p, doc):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as fh:
        fh.write(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    os.replace(tmp, p)


def _write_json(p, doc):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, p)


def latest(root=None):
    return os.path.join(root or ROOT, "data", LG, "latest")


def history(root=None):
    return os.path.join(root or ROOT, "data", LG, "history")


def probe_path(season, root=None):
    return os.path.join(latest(root), "injuries-probe-%d.json" % season)


def archive_path(season, root=None):
    return os.path.join(history(root), "injury-archive-%d.json.gz" % season)


def _rel(p, root):
    return os.path.relpath(p, root).replace(os.sep, "/") if p else None


# ══════════════════════════════════════════════════════════════════════
# the stored schedule, and the one join
# ══════════════════════════════════════════════════════════════════════
class Schedule:
    """One season's stored schedule, indexed for the join."""

    def __init__(self, games):
        self.games, self.teams = [], set()
        self.by_pair, self.by_team = collections.defaultdict(list), collections.defaultdict(list)
        for g in games or []:
            k = kickoff_utc(g.get("start"))
            if not g.get("id") or not g.get("home") or not g.get("away") or k is None:
                continue
            g = dict(g, _k=k)
            self.games.append(g)
            self.teams.update((g["home"], g["away"]))
            self.by_pair[(g["home"], g["away"])].append(g)
            self.by_team[g["home"]].append(g)
            self.by_team[g["away"]].append(g)

    @classmethod
    def load(cls, season, root=None):
        doc = _jz(os.path.join(latest(root), "schedule-%d.json.gz" % season))
        return cls(doc.get("games")) if doc and doc.get("games") else None

    def join_live(self, home, away, kick, date=None, zone=None):
        """-> (game, None) for exactly one game, else (None, why). Away and
        home in the report's own order; the kickoff equal to `start` to the
        minute where the feed gives one (else the same date in its zone)."""
        pair = self.by_pair.get((home, away), [])
        if kick is not None:
            near = [g for g in pair if abs(g["_k"] - kick) <= datetime.timedelta(days=3)]
            same = [g for g in near if g["_k"].replace(second=0, microsecond=0) == kick.replace(second=0, microsecond=0)]
            if not near:
                return None, "no stored game %s at %s near %s" % (away, home, _iso(kick))
            if not same:
                return None, "kickoff %s is not the schedule's %s" % (
                    _iso(kick), ", ".join(_iso(g["_k"]) for g in near))
        else:
            if not date or ZONES.get(str(zone or "").strip().upper()) is None:
                return None, "no kickoff given"
            shift = ZONES[str(zone).strip().upper()]
            same = [g for g in pair if (_eastern(g["_k"]) + datetime.timedelta(hours=shift)).date().isoformat()
                    == str(date).strip()]
            if not same:
                return None, "no stored game %s at %s on %s" % (away, home, date)
        if len(same) != 1:
            return None, "%d stored games match %s at %s" % (len(same), away, home)
        return same[0], None

    def join_archive(self, team, opp, side, day):
        """An archive row's game: `team` playing `opp` and starting within
        `day` + 8h to + 36h UTC. "at" = team away; "vs." = team home or a
        neutral site. A row naming the team as its own opponent (2025's
        neutral sites) is recovered from team + date when exactly one game
        matches."""
        midnight = datetime.datetime(day.year, day.month, day.day, tzinfo=UTC)
        lo, hi = (midnight + datetime.timedelta(hours=h) for h in ARCHIVE_WINDOW_H)
        cand = [g for g in self.by_team.get(team, []) if lo <= g["_k"] <= hi]
        if opp == team:
            why = "names %s as its own opponent" % team
        else:
            why = None
            cand = [g for g in cand if opp in (g["home"], g["away"]) and
                    (g["away"] == team if side == "at" else (g["home"] == team or g.get("neutral")))]
        if len(cand) != 1:
            return None, "%s%s" % ("no stored game in the window" if not cand else "more than one stored game",
                                   " (%s)" % why if why else "")
        return cand[0], None


# ══════════════════════════════════════════════════════════════════════
# normalise: a feed's payload -> accepted reports + refusals
# ══════════════════════════════════════════════════════════════════════
def _team_list(entries, tally):
    """[(name, number, pos_raw, status_raw)] -> (players not Available, listed).
    ⛔ One player listed twice (jersey + folded name) is kept once."""
    seen, out = {}, []
    for name, num, pos_raw, st in entries:
        key = (num, fold(name))
        status = canon_status(st, tally)
        if key in seen:
            tally["duplicates"] += 1
            if seen[key]["status"] != status:
                seen[key]["status"] = UNKNOWN          # two statuses for one player: not known
            continue
        position, position_raw = position_of(pos_raw, tally)
        p = {"name": name, "number": num, "position": position, "position_raw": position_raw,
             "status": status}
        seen[key] = p
        out.append(p)
    return [p for p in out if p["status"] != AVAILABLE], len(out)


def _report(game, source, label, posted, fetched_at, lists, listed):
    return {"game_id": str(game["id"]), "home": game["home"], "away": game["away"],
            "kickoff": _iso(game["_k"]), "source": source, "label": label,
            "posted_at": _iso(posted), "fetched_at": fetched_at, "teams": lists, "listed": listed}


def _pending(label):
    return not label or label.lower() == "report pending"


def _teams_of(raw, sched, source, tally):
    """(away, home) schedule names, or None after naming the unknown ones."""
    names = [team_name(x, sched.teams) for x in raw]
    for x, n in zip(raw, names):
        if n is None:
            tally["names"].add("%s: %s" % (source, _clean(x)))
    return None if None in names else names


def _accept(game, source, label, posted, fetched_at, per_team, tally, ref, reports, refused):
    """Accept one joined report, or refuse it as empty. `per_team` is
    [(schedule name, [(name, number, pos_raw, status_raw)])]."""
    lists, listed = {}, {}
    for name, entries in per_team:
        if entries:          # ⛔ a team with no player row has no report here: absent, never zero
            lists[name], listed[name] = _team_list(entries, tally)
    if not lists:
        refused.append(dict(ref, reason="empty report"))
        return
    reports.append(_report(game, source, label, posted, fetched_at, lists, listed))


def normalise_hdi(source, payload, sched, fetched_at, tally):
    """HDI get-publish-public -> (reports, refused). games[0] is AWAY,
    games[1] HOME (all 34 of the sample, checked against the schedule)."""
    if isinstance(payload, dict) and "error" in payload and not isinstance(payload.get("error"), dict):
        raise FeedError("the feed said: %s" % _clean(payload.get("error"))[:120])
    if isinstance(payload, dict):
        items = list(payload.items())
    elif isinstance(payload, list):
        items = list(enumerate(payload))
    else:
        raise FeedError("not a report list: %s" % type(payload).__name__)
    reports, refused = [], []
    for rid, r in items:
        if not isinstance(r, dict):
            refused.append({"source": source, "id": str(rid), "reason": "not a report"})
            continue
        label = _clean(r.get("ReportType"))
        teams = r.get("games") if isinstance(r.get("games"), list) else []
        raw = [t.get("teamName") if isinstance(t, dict) else None for t in teams]   # ⛔ never teamDisplayName
        ref = {"source": source, "id": str(rid), "label": label, "teams": [_clean(x) for x in raw]}
        if _pending(label):
            refused.append(dict(ref, reason="report pending"))
            continue
        if len(teams) != 2:
            refused.append(dict(ref, reason="lists %d team(s), not two" % len(teams)))
            continue
        both = _teams_of(raw, sched, source, tally)
        if both is None:
            refused.append(dict(ref, reason="unknown team name"))
            continue
        away, home = both
        zone = r.get("conferenceTimeZone")
        foot = r.get("footer") if isinstance(r.get("footer"), dict) else {}
        kick = local_to_utc(foot.get("date"), foot.get("time"), zone)
        game, why = sched.join_live(home, away, kick, foot.get("date"), zone)
        if game is None:
            refused.append(dict(ref, reason=why))
            continue
        per_team = []
        for name, t in ((away, teams[0]), (home, teams[1])):
            entries = []
            for row in t.get("rows") or []:
                p = parse_row(row.get("name") if isinstance(row, dict) else None)
                if p is None:
                    _unparsed(tally, source, row.get("name") if isinstance(row, dict) else row)
                    continue
                entries.append((p[2], p[1], p[0], row.get("status")))
            per_team.append((name, entries))
        posted = local_to_utc(r.get("publishDate"), r.get("postedTime"), zone)
        _accept(game, source, label, posted, fetched_at, per_team, tally, ref, reports, refused)
    return reports, refused


def normalise_feed(source, payload, sched, fetched_at, tally):
    """Sun Belt / Pac-12 report.json -> (reports, refused). Only listed
    (non-healthy) players and no jersey; a team with nobody listed has no
    report here (the feed's own message: "Report will be posted to the
    institution's conference website"), so it is left out, never zero."""
    games = payload.get("games") if isinstance(payload, dict) else None
    if not isinstance(games, list):
        raise FeedError("no games list")
    reports, refused = [], []
    for g in games:
        if not isinstance(g, dict):
            continue
        label = _clean(g.get("notes"))
        sides = [g.get("away") if isinstance(g.get("away"), dict) else {},
                 g.get("home") if isinstance(g.get("home"), dict) else {}]
        raw = [s.get("name") for s in sides]
        ref = {"source": source, "id": _clean(g.get("gameId")), "label": label, "teams": [_clean(x) for x in raw]}
        if _pending(label):
            refused.append(dict(ref, reason="report pending"))
            continue
        both = _teams_of(raw, sched, source, tally)
        if both is None:
            refused.append(dict(ref, reason="unknown team name"))
            continue
        away, home = both
        kick = _utc(g.get("kickoffUTC"))
        if kick is None:
            refused.append(dict(ref, reason="no kickoffUTC"))
            continue
        game, why = sched.join_live(home, away, kick)
        if game is None:
            refused.append(dict(ref, reason=why))
            continue
        per_team = []
        for name, side in ((away, sides[0]), (home, sides[1])):
            entries = []
            for p in side.get("players") or []:
                nm = _clean(p.get("name")) if isinstance(p, dict) else ""
                if not _has_letter(nm):
                    _unparsed(tally, source, p)
                    continue
                entries.append((nm, None, p.get("position"), p.get("status")))
            per_team.append((name, entries))
        _accept(game, source, label, _utc(g.get("updatedAtUTC")), fetched_at, per_team, tally, ref, reports, refused)
    return reports, refused


def _week_date(s):
    s = _clean(s)
    if re.match(r"^\d{4}-\d\d-\d\d$", s):
        return datetime.date.fromisoformat(s)
    try:
        return email.utils.parsedate_to_datetime(s).astimezone(UTC).date()
    except (TypeError, ValueError, IndexError, AttributeError):
        return None


def normalise_archive(source, payload, sched, tally):
    """An HDI archive -> (report_days, rows, refused counts). Rows are
    {game_id, team, opponent, date, player, number, columns:{day: status}};
    "-" (not on that report, or not archived yet) is left out of columns."""
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        err = payload.get("error") if isinstance(payload, dict) else None
        raise FeedError("the feed said: %s" % _clean(err)[:120] if err else "no data list")
    days = [d for d in payload.get("report_days") or [] if isinstance(d, str)]
    rows, refused, seen = [], collections.Counter(), {}
    for r in payload["data"]:
        if not isinstance(r, dict):
            refused["not a row"] += 1
            continue
        team = team_name(r.get("Team"), sched.teams)
        m = OPP.match(_clean(r.get("Opponent")))
        opp = team_name(m.group(2), sched.teams) if m else None
        if team is None or (m and opp is None):
            for x, n in ((r.get("Team"), team), (m.group(2) if m else None, opp)):
                if n is None and x is not None:
                    tally["names"].add("%s: %s" % (source, _clean(x)))
            refused["unknown team name"] += 1
            continue
        if not m:
            refused["opponent without 'at' or 'vs.'"] += 1
            continue
        day = _week_date(r.get("Week"))
        if day is None:
            refused["no date"] += 1
            continue
        game, why = sched.join_archive(team, opp, m.group(1), day)
        if game is None:
            refused[why] += 1
            continue
        player = _clean(r.get("Player"))
        if not _has_letter(player):
            _unparsed(tally, source, r.get("Player"))
            continue
        num = re.match(r"^#?(\d{1,2})$", _clean(r.get("Number")))
        num = num.group(1) if num else None
        cols = {d: canon_status(r.get(d), tally) for d in days if _clean(r.get(d)) not in ("", "-")}
        twice = seen.get((str(game["id"]), team, num, fold(player)))
        if twice is not None:
            tally["duplicates"] += 1
            old = twice["columns"]
            for d, st in cols.items():
                if old.get(d, st) != st:
                    old[d] = UNKNOWN
                old.setdefault(d, st)
            continue
        row = {"game_id": str(game["id"]), "team": team,
               "opponent": game["home"] if game["away"] == team else game["away"],
               "date": day.isoformat(), "player": player, "number": num, "columns": cols}
        seen[(row["game_id"], team, num, fold(player))] = row
        rows.append(row)
    rows.sort(key=lambda x: (x["date"], x["game_id"], x["team"], x["number"] or "", x["player"]))
    return days, rows, dict(refused)


# ══════════════════════════════════════════════════════════════════════
# the network (injectable; never used by a test)
# ══════════════════════════════════════════════════════════════════════
def _post(url, body, timeout=TIMEOUT):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"User-Agent": UA, "Content-Type": "application/json",
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8-sig"))


def _get(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8-sig"))


def _body(conf):
    return {"sport": "Football", "organization": conf, "conference": conf}


# ══════════════════════════════════════════════════════════════════════
# the snapshots
# ══════════════════════════════════════════════════════════════════════
def snapshot_paths(root=None):
    """[(stamp, path)] of every stored snapshot, oldest first."""
    base = os.path.join(root or ROOT, "data", LG)
    out = []
    try:
        days = os.listdir(base)
    except OSError:
        return out
    for d in days:
        kd = os.path.join(base, d, "injury-reports")
        if not DAYDIR.match(d) or not os.path.isdir(kd):
            continue
        for f in os.listdir(kd):
            m = HHMM.match(f)
            if m:
                try:
                    st = datetime.datetime.strptime(d + m.group(1), "%Y-%m-%d%H%M").replace(tzinfo=UTC)
                except ValueError:
                    continue
                out.append((st, os.path.join(kd, f)))
    return sorted(out)


_CACHE = collections.OrderedDict()
_CACHE_MAX = 8


def _snapshot(path):
    try:
        s = os.stat(path)
    except OSError:
        return None
    key = (path, s.st_mtime_ns, s.st_size)
    if key in _CACHE:
        _CACHE.move_to_end(key)
        return _CACHE[key]
    doc = _jz(path)
    if not isinstance(doc, dict):
        return None
    _CACHE[key] = doc
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)
    return doc


def newest_snapshot(root=None, until=None):
    """(path, doc) of the newest snapshot fetched at or before `until`."""
    for st, p in reversed(snapshot_paths(root)):
        if until is not None and st > until:
            continue
        doc = _snapshot(p)
        f = _utc((doc or {}).get("fetched_at"))
        if doc and f and (until is None or f <= until):
            return p, doc
    return None, None


def _content(reports):
    """What a snapshot SAYS: its reports without the time we fetched them."""
    return json.dumps([{k: v for k, v in r.items() if k != "fetched_at"} for r in reports],
                      sort_keys=True, separators=(",", ":"))


def _eligible(rep, at):
    """§2: a stored report can answer for the moment `at` only if it was
    fetched at or before `at` (and not more than SCAN_DAYS before it), and
    ⛔ before its kickoff."""
    f, k = _utc(rep.get("fetched_at")), _utc(rep.get("kickoff"))
    return bool(f and k and at - datetime.timedelta(days=SCAN_DAYS) <= f <= at and f < k)


def _probe_ok_times(source, at, root):
    out = []
    for p in glob.glob(os.path.join(latest(root), "injuries-probe-*.json")):
        try:
            with open(p, encoding="utf-8") as fh:
                t = _utc(((json.load(fh).get("sources") or {}).get(source) or {}).get("last_ok_at"))
        except (OSError, ValueError, AttributeError):
            continue
        if t and t <= at:
            out.append(t)
    return out


def source_confirmed(source, at, root=None, newest=None):
    """The newest moment at or before `at` at which `source` answered and our
    stored snapshot held what it said: the newest snapshot's own reading of
    it, or the probe's `last_ok_at` (a pass whose content was unchanged
    writes no snapshot but still confirms the newest one)."""
    if newest is None:
        _p, newest = newest_snapshot(root, at)
    cands = _probe_ok_times(source, at, root)
    t = _utc((((newest or {}).get("sources") or {}).get(source) or {}).get("fetched_at"))
    if t and t <= at:
        cands.append(t)
    return max(cands) if cands else None


def _judge(rep, at, live, root, newest=None):
    """A stored report -> the dict report_for returns, with `current` and `why`."""
    out = copy.deepcopy(rep)
    kick = _utc(rep.get("kickoff"))
    pub = _utc(rep.get("posted_at")) or _utc(rep.get("fetched_at"))
    age = (kick - pub).total_seconds() / 3600.0
    word = "published" if rep.get("posted_at") else "first fetched"
    if age > MAX_AGE_H:
        out["current"], out["why"] = False, "%s %.1f hours before kickoff, more than %d" % (word, age, MAX_AGE_H)
        return out
    if live:
        conf = source_confirmed(rep.get("source"), at, root, newest)
        old = None if conf is None else (at - conf).total_seconds() / 3600.0
        if old is None or old > FETCH_MAX_AGE_H:
            out["current"] = False
            out["why"] = ("our newest reading of %s is %s, more than %d hours" % (
                rep.get("source"), "missing" if old is None else "%.1f hours old" % old, FETCH_MAX_AGE_H))
            return out
    out["current"], out["why"] = True, "%s %.1f hours before kickoff" % (word, age)
    return out


def report_for(game_id, at, root=None, live=True):
    """The last report stored for `game_id` fetched at or before `at` and
    before kickoff -> {game_id, home, away, kickoff, source, label, posted_at,
    fetched_at, teams, listed, current, why}, or None. ⛔ Never raises."""
    try:
        at = _when(at)
        gid = str(game_id)
        newest = None
        for st, p in reversed(snapshot_paths(root)):
            if st > at:
                continue
            if st < at - datetime.timedelta(days=SCAN_DAYS + 1):
                break
            doc = _snapshot(p)
            if not doc:
                continue
            f = _utc(doc.get("fetched_at"))
            if newest is None and f and f <= at:
                newest = doc
            for r in doc.get("reports") or []:
                if str(r.get("game_id")) == gid and _eligible(r, at):
                    return _judge(r, at, live, root, newest)
        return None
    except Exception:
        return None


def out_players(report, team):
    """The players of `team` in `report` who are Out, Out for Season or
    Doubtful. ⛔ None (no reading, never zero) when there is no report or the
    report does not carry that team."""
    try:
        if not report or team not in (report.get("teams") or {}):
            return None
        return [dict(p) for p in report["teams"][team]
                if str(p.get("status") or "").lower() in OUT_STATUSES]
    except Exception:
        return None


def night_before(season, conf):
    """§3: the archive column known the night before, or None (no reading)."""
    if season in NIGHT_BEFORE:
        return NIGHT_BEFORE[season].get(conf)
    return NIGHT_BEFORE_FROM_2026 if season >= 2026 else None


def pick_time_outs(season, root=None):
    """§3: {game_id: {team: [Out / Out for Season / Doubtful players]}} as
    known at pick time. From the archive: its night-before column. From the
    snapshots: the report `report_for` would give for the last moment before
    9:00 am ET on the game's ET day, if it is current (not a live read). A
    snapshot's reading replaces the archive's for its teams. A team with no
    reading is absent, ⛔ never an empty list. ⛔ Never raises."""
    out = {}
    try:
        doc = _jz(archive_path(season, root)) or {}
        for conf, c in sorted((doc.get("conferences") or {}).items()):
            col = night_before(season, conf)
            if not col or col not in (c.get("report_days") or []):
                continue
            groups = collections.defaultdict(list)
            for r in c.get("rows") or []:
                groups[(r["game_id"], r["team"])].append(r)
            for (gid, team), rows in groups.items():
                if not any(col in (r.get("columns") or {}) for r in rows):
                    continue                              # that report was not archived
                out.setdefault(gid, {})[team] = [
                    {"name": r["player"], "number": r.get("number"), "position": None,
                     "position_raw": None, "status": r["columns"][col]}
                    for r in rows if str((r.get("columns") or {}).get(col) or "").lower() in OUT_STATUSES]
    except Exception:
        pass
    try:
        best = {}
        for _st, p in reversed(snapshot_paths(root)):
            snap = _snapshot(p)
            if not snap or snap.get("season") != season:
                continue
            for r in snap.get("reports") or []:
                gid = str(r.get("game_id"))
                cut = pick_cutoff(r.get("kickoff"))
                if gid not in best and cut and _eligible(r, cut):
                    best[gid] = (r, cut)
        for gid, (r, cut) in best.items():
            j = _judge(r, cut, False, root)
            if j["current"]:
                for team in j["teams"]:
                    out.setdefault(gid, {})[team] = out_players(j, team)
    except Exception:
        pass
    return out


# ══════════════════════════════════════════════════════════════════════
# the archives
# ══════════════════════════════════════════════════════════════════════
def _archives(root, now, season, call, post, scheds, prev_probe, tally, log):
    """The legacy season once while a conference is missing; the current
    season at most once every ARCHIVE_REFRESH_H, rewritten only on change.
    -> {season: {conf: info}}. ⛔ A failure is recorded, never raised."""
    info = {}
    plan = [(LEGACY_SEASON, "get-archive-legacy-public", HDI_LEGACY, False)]
    if season != LEGACY_SEASON:
        plan.append((season, "get-archive-public", HDI_ARCHIVE, True))
    prev = (prev_probe or {}).get("archives") or {}
    for yr, endpoint, confs, refresh in plan:
        out = info.setdefault(str(yr), {})
        path = archive_path(yr, root)
        doc = _jz(path) or {}
        have = doc.get("conferences") if isinstance(doc.get("conferences"), dict) else {}
        changed = False
        for conf in confs:
            last = dict((prev.get(str(yr)) or {}).get(conf) or {})
            checked = _utc(last.get("checked_at"))
            if conf in have and not refresh:
                out[conf] = dict(last, ok=True, due=False, wrote=False)
                continue
            if conf in have and checked and now - checked < datetime.timedelta(hours=ARCHIVE_REFRESH_H):
                out[conf] = dict(last, due=False, wrote=False)
                continue
            sched = scheds(yr)
            if sched is None:
                out[conf] = dict(last, ok=False, error="no stored schedule-%d" % yr, due=True)
                continue
            try:
                days, rows, refused = normalise_archive(conf, call(post, HDI + endpoint, _body(conf)), sched, tally)
            except Exception as ex:
                out[conf] = dict(last, ok=False, error="%s: %s" % (type(ex).__name__, str(ex)[:160]), due=True)
                continue
            old = have.get(conf) or {}
            same = old.get("report_days") == days and old.get("rows") == rows
            if not same:
                have[conf] = {"fetched_at": _iso(now), "report_days": days, "rows": rows, "refused": refused}
                changed = True
            out[conf] = {"ok": True, "checked_at": _iso(now), "rows": len(rows), "refused": refused,
                         "wrote": not same, "due": False}
        if changed:
            _write_gz(path, {"season": yr, "kind": "DESCRIPTIVE", "built_at": _iso(now),
                             "source": "HD Intelligence %s (images stripped)" % endpoint,
                             "note": "Rows list only players who were not Available on at least one "
                                     "report that week; '-' (not on that report) is left out of columns.",
                             "conferences": have})
            log("    injury archive %d written (%s)" % (yr, ", ".join(sorted(have))))
    return info


# ══════════════════════════════════════════════════════════════════════
# one pass
# ══════════════════════════════════════════════════════════════════════
def run(root=None, now=None, post=None, get=None, log=log_):
    """One pass: every source, then the snapshot (only on change), the
    archives and the probe (always). -> {"ok", "sources", "snapshot",
    "wrote", "probe", "archives"}. `ok` is True when every live source
    answered and the snapshot step finished. ⛔ Never raises."""
    root = root or ROOT
    post, get = post or _post, get or _get
    out = {"ok": False, "sources": {}, "snapshot": None, "wrote": False, "probe": None, "archives": {}}
    try:
        import freshness
        now = _utc(now) if now is not None else datetime.datetime.now(UTC)
        season = freshness.current_football_season(now)
        out["probe"] = probe_path(season, root)
    except Exception as ex:
        log("    ⚠️ college injuries did not start: %s: %s" % (type(ex).__name__, ex))
        out["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:200])
        return out
    tally, refused, state = _tally(), [], {"calls": 0, "snapshot_ok": False}
    prev_probe = None
    try:
        with open(out["probe"], encoding="utf-8") as fh:
            prev_probe = json.load(fh)
    except (OSError, ValueError):
        prev_probe = None

    def call(fn, *args):
        if state["calls"] >= MAX_CALLS:
            raise FeedError("call cap of %d reached this run" % MAX_CALLS)
        state["calls"] += 1
        return strip_images(fn(*args))           # ⛔ before anything reads or stores it

    scheds = {}

    def sched_for(yr):
        if yr not in scheds:
            scheds[yr] = Schedule.load(yr, root)
        return scheds[yr]

    fetched = _iso(now)
    reports = []
    try:
        sched = sched_for(season)
        for src in SOURCES:
            if sched is None:
                out["sources"][src] = {"ok": False, "error": "no stored schedule-%d" % season, "fetched_at": None}
                continue
            try:
                if src in FEEDS:
                    reps, ref = normalise_feed(src, call(get, FEEDS[src]), sched, fetched, tally)
                else:
                    reps, ref = normalise_hdi(src, call(post, HDI + "get-publish-public", _body(src)),
                                              sched, fetched, tally)
                out["sources"][src] = {"ok": True, "n_reports": len(reps), "n_refused": len(ref),
                                       "fetched_at": fetched}
                reports += reps
                refused += ref
            except Exception as ex:                  # ⛔ one source failing never stops the others
                out["sources"][src] = {"ok": False, "error": "%s: %s" % (type(ex).__name__, str(ex)[:200]),
                                       "fetched_at": None}
        answered = [s for s in SOURCES if out["sources"][s]["ok"]]
        if answered:
            prev_path, prev = newest_snapshot(root)
            failed = set(SOURCES) - set(answered)
            keep = now - datetime.timedelta(hours=CARRY_H)
            carried = [r for r in (prev or {}).get("reports") or []
                       if r.get("source") in failed and (_utc(r.get("kickoff")) or now) >= keep]
            allrep = sorted(reports + carried, key=lambda r: (r["kickoff"], r["game_id"], r["source"]))
            psrc = (prev or {}).get("sources") or {}
            srcmeta = {s: {"ok": out["sources"][s]["ok"],
                           "fetched_at": fetched if out["sources"][s]["ok"] else (psrc.get(s) or {}).get("fetched_at")}
                       for s in SOURCES}
            if prev is not None and _content(allrep) == _content(prev.get("reports") or []):
                out["snapshot"], out["wrote"] = prev_path, False
            else:
                doc = {"kind": "cfb-injury-reports", "season": season, "fetched_at": fetched,
                       "sources": srcmeta, "reports": allrep, "refused": refused}
                p, wrote = daystore.archive(doc, os.path.join(root, "data", LG), "injury-reports",
                                            log=log, when=now)
                out["snapshot"], out["wrote"] = p, wrote
            state["snapshot_ok"] = True
    except Exception as ex:
        out["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:200])
        log("    ⚠️ college injuries: %s" % out["error"])
    try:
        out["archives"] = _archives(root, now, season, call, post, sched_for, prev_probe, tally, log)
    except Exception as ex:
        out["archives"] = {"error": "%s: %s" % (type(ex).__name__, str(ex)[:200])}
    out["ok"] = bool(state["snapshot_ok"] and all(v["ok"] for v in out["sources"].values()))
    try:
        _write_probe(root, now, season, out, refused, tally, prev_probe, state)
    except Exception as ex:
        log("    ⚠️ college injury probe not written: %s: %s" % (type(ex).__name__, ex))
    n = sum(v.get("n_reports") or 0 for v in out["sources"].values())
    log("    college injuries %d: %d report(s) accepted, %d refused, snapshot %s" % (
        season, n, len(refused), "written" if out["wrote"] else "unchanged"))
    return out


def _write_probe(root, now, season, out, refused, tally, prev_probe, state):
    psrc = (prev_probe or {}).get("sources") or {}
    sources = {}
    for s, v in out["sources"].items():
        last = v["fetched_at"] if v["ok"] and state["snapshot_ok"] else (psrc.get(s) or {}).get("last_ok_at")
        sources[s] = dict(v, last_ok_at=last)
    np, ndoc = newest_snapshot(root)
    nf = _utc((ndoc or {}).get("fetched_at"))
    probe = {
        "season": season, "kind": "DIAGNOSTIC", "built_at": _iso(now), "ok": out["ok"],
        "error": out.get("error"), "calls": state["calls"], "sources": sources,
        "refused": refused,
        "unknown": {"names": sorted(tally["names"]), "positions": dict(tally["positions"]),
                    "statuses": dict(tally["statuses"]), "exempt": tally["exempt"]},
        "unparsed": {"count": tally["unparsed"], "examples": tally["unparsed_examples"]},
        "duplicates": tally["duplicates"],
        "snapshot": {"path": _rel(np, root), "wrote": out["wrote"], "fetched_at": _iso(nf),
                     "age_h": None if nf is None else round((now - nf).total_seconds() / 3600.0, 2)},
        "archives": out.get("archives") or {},
        "note": ("College injury reports (SEC, ACC, Big Ten, Big 12, MAC through HD Intelligence; "
                 "Sun Belt; Pac-12). A refused report is named with its reason; nothing refused "
                 "is stored. research/cfb_injuries_design.md."),
    }
    _write_json(out["probe"], probe)


if __name__ == "__main__":
    run()                      # ⛔ never an exit code: the probe says what happened
