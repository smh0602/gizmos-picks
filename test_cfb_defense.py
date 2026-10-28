#!/usr/bin/env python3
"""test_cfb_defense.py — the jerseys and the defensive box score CFBD already
sends, kept (research/cfb_injuries_design.md §1 item 4).

`roster-<season>.json.gz` and `defense-<season>.json.gz` come from the SAME
/roster and /games/players calls every build already makes; 2025 is filled once
while missing, priced first, and only from a complete build. Planted CFBD
responses (`cfb.get` replaced), a temp `cfb.OUT`, a stubbed
`cfbd_budget.preflight`. ⛔ No network, no key, nothing written under data/,
nothing read from production.

# @vacuity 🔴 the defensive TOT column is kept
#   file: cfb.py
#   find: ("defensive", "tot"): "tot",
#   with: ("defensive", "tot_x"): "tot",
#
# @vacuity 🔴 CFBD's "QB HUR" (with its space) is kept as qb_hur
#   file: cfb.py
#   find: ("defensive", "qb hur"): "qb_hur",
#   with: ("defensive", "qb_hur"): "qb_hur",
#
# @vacuity 🔴 interceptions are the INT column, not the return yards
#   file: cfb.py
#   find: ("interceptions", "int"): "int",
#   with: ("interceptions", "yds"): "int",
#
# @vacuity 🔴 a team-aggregate pseudo-athlete is never a player (one rule, both logs)
#   file: cfb.py
#   find: return str(a.get("id")).startswith("-") or not (a.get("name") or "").strip()
#   with: return False
#
# @vacuity 🔴 a defensive row that is not a player record is skipped, never a lost doc
#   file: cfb.py
#   find: if not isinstance(a, dict) or _is_team_row(a):
#   with: if _is_team_row(a):
#
# @vacuity 🔴 the defense file has the players file's FBS scope
#   file: cfb.py
#   find: if scope_confs and e["conf"] not in scope_confs:
#   with: if False:
#
# @vacuity 🔴 the roster keeps the jersey
#   file: cfb.py
#   find: "jersey": r.get("jersey"),
#   with: "jersey": None,
#
# @vacuity 🔴 the roster's name is firstName + lastName
#   file: cfb.py
#   find: name = " ".join(str(x).strip() for x in (r.get("firstName"), r.get("lastName"))
#   with: name = " ".join(str(x).strip() for x in (r.get("lastName"),)
#
# @vacuity 🔴 a roster row with no id is left out
#   file: cfb.py
#   find: if not isinstance(r, dict) or r.get("id") is None or not r.get("team"):
#   with: if not isinstance(r, dict):
#
# @vacuity 🔴 players-<season> is unchanged: no defensive column enters it
#   file: cfb.py
#   find: dest = MAP.get((c, s))
#   with: dest = MAP.get((c, s)) or DEFENSE_MAP.get((c, s))
#
# @vacuity 🔴 ...and the UNMAPPED count (the probe report) is unchanged
#   file: cfb.py
#   find: unmapped[(c, s)] += len(typ.get("athletes") or [])
#   with: unmapped[(c, s)] += 0 if (c, s) in DEFENSE_MAP else len(typ.get("athletes") or [])
#
# @vacuity 🔴 a file whose content did not change is not rewritten
#   file: cfb.py
#   find: if same:
#   with: if False:
#
# @vacuity 🔴 ...judged with the stored file's written_at set aside
#   file: cfb.py
#   find: same = _fr.same_but_stamps(stored, o, fields=("written_at",))
#   with: same = _fr.same_but_stamps(stored, o, fields=())
#
# @vacuity 🔴 a season with any failed CFBD call builds no defense doc
#   file: cfb.py
#   find: if keep["call_failures"]:
#   with: if False:
#
# @vacuity 🔴 ...and a failed /games call (the bowls) is a failed call, not only /games/players
#   file: cfb.py
#   find: keep["call_failures"] = (["/games " + e for e in fetch_errors]
#   with: keep["call_failures"] = ([]
#
# @vacuity 🔴 the log says "kept in defense" only when the defense doc was built
#   file: cfb.py
#   find: if (keep or {}).get("defense") and (c, s) in DEFENSE_MAP else ""))
#   with: if dfn is not None and (c, s) in DEFENSE_MAP else ""))
#
# @vacuity 🔴 ...and a fill, which never writes players-<season>, prints no players-file lines
#   file: cfb.py
#   find: if unmapped and not fill:
#   with: if unmapped:
#
# @vacuity 🔴 the 2025 fill runs only while a file is missing
#   file: cfb.py
#   find: if all(os.path.exists(os.path.join(OUT, f"{k}-{season}.json.gz"))
#   with: if False and all(os.path.exists(os.path.join(OUT, f"{k}-{season}.json.gz"))
#
# @vacuity 🔴 ...writes only the missing file, never a stored one
#   file: cfb.py
#   find: if only_missing and os.path.exists(os.path.join(OUT, f)):
#   with: if False:
#
# @vacuity 🔴 ...is priced before any call, and a refusal calls nothing
#   file: cfb.py
#   find: if not _priced(season_build_max(season), "roster + defense back-fill %d" % season, log):
#   with: if False:
#
# @vacuity 🔴 ...at a ceiling that covers every call it makes, on a 16-week season with no slack
#   file: cfb.py
#   find: return _cb.season_build_calls(max(len(weeks), len(REG_WEEKS) + 1))
#   with: return _cb.season_build_calls(len(REG_WEEKS))
#
# @vacuity 🔴 ...counted by the ONE build_season call count, which matches the build
#   file: cfbd_budget.py
#   find: return 1 + 1 + 2 + (weeks_played + 1)
#   with: return 1 + 1 + 2 + weeks_played
#
# @vacuity 🔴 ...and the schedule's reserve reads that same count (no second copy)
#   file: cfbd_budget.py
#   find: season = season_build_calls(weeks_played)
#   with: season = 1 + 1 + 2 + (weeks_played + 1)
#
# @vacuity 🔴 ...and never writes teams.json (this season's directory)
#   file: cfb.py
#   find: doc, _unmapped, _n = build_season(season, log, keep=keep, fill=True)
#   with: doc, _unmapped, _n = build_season(season, log, keep=keep)
#
# @vacuity 🔴 ...because a fill's build asks /teams/fbs for no directory
#   file: cfb.py
#   find: scope_confs, _scope_teams = fbs_conferences(season, log, directory=not fill)
#   with: scope_confs, _scope_teams = fbs_conferences(season, log)
#
# @vacuity 🔴 ...stores nothing from a build with any gap
#   file: cfb.py
#   find: return "not written, asked again next run: " + "; ".join(gaps)[:600]
#   with: pass
#
# @vacuity 🔴 gap: a doc not built (a failed /games postseason: no bowls)
#   file: cfb.py
#   find: gaps.append(f"no {key} doc ({(keep.get('why_not') or {}).get(key, 'not built')})")
#   with: pass
#
# @vacuity 🔴 gap: no FBS scope (/teams/fbs failed or short)
#   file: cfb.py
#   find: gaps.append("no FBS scope: /teams/fbs failed or listed under %d schools" % FBS_MIN_TEAMS)
#   with: pass
#
# @vacuity 🔴 gap: anything the probe's own verify names
#   file: cfb.py
#   find: gaps += ["verify: " + b for b in verify(doc, log)]
#   with: gaps += []
#
# @vacuity 🔴 gap: a completed week (here the bowls) answered with no defensive rows
#   file: cfb.py
#   find: gaps.append(f"completed week(s) with no defensive rows: {empty}")
#   with: pass
#
# @vacuity 🔴 ...the completed weeks are /games' own finals
#   file: cfb.py
#   find: finals[str(g.get("id"))] = (st, g.get("week"))
#   with: pass
#
# @vacuity 🔴 ...and never raises
#   file: cfb.py
#   find: return "not written: %s: %s" % (type(e).__name__, str(e)[:200])
#   with: raise
#
# @vacuity 🔴 cfb-probe runs the 2025 fill
#   file: cfb.py
#   find: log(f"    roster + defense back-fill {_ds}: {backfill_defense(_ds, log)}")
#   with: pass
#
# @vacuity 🔴 cfb-probe writes the season's roster + defense after its build
#   file: cfb.py
#   find: log(f"    roster + defense {season}: {store_kept(season, keep, log)}")
#   with: pass
#
# @vacuity 🔴 ...from the keep its own build filled (driven, not read as text)
#   file: cfb.py
#   find: keep = {}    # roster + defense, from the same calls
#   with: keep = None
"""
import atexit
import copy
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("CFBD_API_KEY", "x")
import cfb  # noqa: E402
import cfbd_budget  # noqa: E402
import fb_history  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

TMP = tempfile.mkdtemp(prefix="cfbdef-")
atexit.register(lambda: shutil.rmtree(TMP, ignore_errors=True))
cfb.time.sleep = lambda s: None
QUIET = lambda *a, **k: None  # noqa: E731
EVENTS = []          # ("get", path, params) and ("price", calls, purpose), in order
FAIL = {"fn": None}  # (path, params) -> True to answer that call with HTTP 503
EMPTY = {"fn": None}  # (path, params) -> True to answer that call with HTTP 200 and []
ALLOW = {"fn": lambda purpose: True}
UNPLANTED = {"probe": False}   # a probe run answers an unplanted path as CFBD down


def _price(calls, purpose, latest, root=None):
    EVENTS.append(("price", calls, purpose))
    return {"allowed": ALLOW["fn"](purpose), "why": "planted", "purpose": purpose, "calls": calls}


cfbd_budget.preflight = _price

# ── FIXTURE BEGIN ────────────────────────────────────────────────────────
# ⚠️ GOLDEN below is the players-file digest of THIS fixture (at its defaults:
#    two regular weeks, Elo on every game), computed with cfb.py as it was
#    before roster/defense existed (4461f3657).
LAWSON = ("7", "4", "1", "1.5", "1", "2", "0")
DTYPES = ("TOT", "SOLO", "SACKS", "TFL", "PD", "QB HUR", "TD")
GAMES = {"weeks": 2, "no_elo": False}   # regular weeks /games lists; Elo stripped from game 101


def game(gid, week, home, away, hconf, aconf, start, hcls="fbs", acls="fbs"):
    return {"id": gid, "week": week, "startDate": start, "homeTeam": home, "awayTeam": away,
            "homeConference": hconf, "awayConference": aconf, "neutralSite": False,
            "homePregameElo": 1700, "awayPregameElo": 1600, "homeClassification": hcls,
            "awayClassification": acls, "completed": True, "homePoints": 28, "awayPoints": 21}


def games_of(y):
    reg = [game(101, 1, "Alabama", "Georgia", "SEC", "SEC", "%d-08-29T19:00:00.000Z" % y),
           game(102, 1, "Montana", "Idaho", "Big Sky", "Big Sky", "%d-08-29T23:00:00.000Z" % y, "fcs", "fcs"),
           game(103, 2, "Alabama", "Mercer", "SEC", "Southern", "%d-09-05T23:00:00.000Z" % y, "fbs", "fcs")]
    reg += [game(300 + w, w, "Alabama", "Georgia", "SEC", "SEC", "%d-09-%02dT19:00:00.000Z" % (y, w))
            for w in range(3, GAMES["weeks"] + 1)]
    if GAMES["no_elo"]:
        reg[0].update(homePregameElo=None, awayPregameElo=None, homeClassification=None,
                      awayClassification=None)
    return {"regular": reg,
            "postseason": [game(201, 1, "Georgia", "Alabama", "SEC", "SEC", "%d-01-01T20:00:00.000Z" % (y + 1))]}


FBS = ([{"school": "Alabama", "conference": "SEC"}, {"school": "Georgia", "conference": "SEC"}]
       + [{"school": "Filler %d" % i, "conference": "Sun Belt"} for i in range(100)])
FBS_V = {"v": FBS}
ROSTER = [
    {"id": 1, "firstName": "Jalen", "lastName": "Milroe", "team": "Alabama", "jersey": 4, "position": "QB"},
    {"id": 2, "firstName": "Ryan", "lastName": "Williams", "team": "Alabama", "jersey": 2, "position": "WR"},
    {"id": 3, "firstName": "Deontae", "lastName": "Lawson", "team": "Alabama", "jersey": 0, "position": "lb"},
    {"id": 4, "firstName": "Carson", "lastName": "Beck", "team": "Georgia", "jersey": 15, "position": "QB"},
    {"id": 5, "firstName": "Malaki", "lastName": "Starks", "team": "Georgia", "jersey": 24, "position": "DB"},
    {"id": 6, "firstName": "Mercer", "lastName": "Linebacker", "team": "Mercer", "jersey": 9, "position": "LB"},
    {"id": 7, "firstName": "Big", "lastName": "Sky", "team": "Montana", "jersey": 90, "position": "DL"},
    {"id": 8, "firstName": "No", "lastName": "Jersey", "team": "Georgia", "jersey": None, "position": None},
    {"id": None, "firstName": "Ghost", "lastName": "Row", "team": "Alabama", "jersey": 1, "position": "WR"},
]


def cat(name, types):
    return {"name": name, "types": [{"name": t, "athletes": [{"id": i, "name": n, "stat": s} for i, n, s in ath]}
                                    for t, ath in types]}


def defensive(rows):
    return cat("defensive", [(t, [(i, n, vals[k]) for i, n, vals in rows]) for k, t in enumerate(DTYPES)])


def side(team, cats):
    return {"team": team, "conference": "SEC", "homeAway": "home", "points": 0, "categories": cats}


def box_of(lawson=LAWSON):
    mercer = defensive([(6, "Mercer Linebacker", ("12", "8", "0", "1", "0", "0", "0"))])
    mercer["types"][0]["athletes"].append("junk")     # a row that is not a player record at all
    return {
        ("regular", "1"): [
            {"id": 101, "teams": [
                side("Alabama", [
                    cat("passing", [("C/ATT", [(1, "Jalen Milroe", "20/30")]), ("YDS", [(1, "Jalen Milroe", "250")]),
                                    ("TD", [(1, "Jalen Milroe", "2")]), ("INT", [(1, "Jalen Milroe", "1")]),
                                    ("AVG", [(1, "Jalen Milroe", "8.3")])]),
                    cat("rushing", [("CAR", [(1, "Jalen Milroe", "10"), (-1, " Team", "2")]),
                                    ("YDS", [(1, "Jalen Milroe", "55"), (-1, " Team", "-5")])]),
                    cat("receiving", [("REC", [(2, "Ryan Williams", "6")]), ("YDS", [(2, "Ryan Williams", "98")]),
                                      ("TD", [(2, "Ryan Williams", "1")])]),
                    defensive([(3, "Deontae Lawson", lawson), (2, "Ryan Williams", ("1", "1", "0", "0", "0", "0", "0")),
                               (-1, " Team", ("1", "1", "0", "0", "0", "0", "0"))]),
                    cat("kicking", [("FG", [(9, "Kicker Guy", "2/2")])])]),
                side("Georgia", [
                    cat("passing", [("C/ATT", [(4, "Carson Beck", "18/31")]), ("YDS", [(4, "Carson Beck", "210")])]),
                    defensive([(5, "Malaki Starks", ("5", "3", "0", "0", "2", "0", "0")),
                               (77, "  ", ("2", "2", "0", "0", "0", "0", "0"))]),
                    cat("interceptions", [("INT", [(5, "Malaki Starks", "1")]), ("YDS", [(5, "Malaki Starks", "34")]),
                                          ("TD", [(5, "Malaki Starks", "0")])])])]},
            {"id": 102, "teams": [side("Montana", [defensive([(7, "Big Sky", ("9", "5", "1", "2", "0", "1", "0"))])]),
                                  side("Idaho", [])]},
            {"id": 999, "teams": [side("Alabama", [defensive([(3, "Deontae Lawson", ("99",) * 7)])])]}],
        ("regular", "2"): [
            {"id": 103, "teams": [
                side("Alabama", [cat("passing", [("YDS", [(1, "Jalen Milroe", "301")])]),
                                 defensive([(3, "Deontae Lawson", ("6", "2", "0", "1", "0", "1", "0"))])]),
                side("Mercer", [mercer])]}],
        ("postseason", "1"): [
            {"id": 201, "teams": [
                side("Georgia", [defensive([(5, "Malaki Starks", ("3", "2", "0.5", "0.5", "0", "1", "0"))])]),
                side("Alabama", [cat("receiving", [("REC", [(2, "Ryan Williams", "3")])])])]}],
    }


def week_box(w):
    """Regular week 3+ (GAMES["weeks"] > 2): one SEC game, offence and defence."""
    return [{"id": 300 + w, "teams": [
        side("Alabama", [cat("passing", [("YDS", [(1, "Jalen Milroe", "200")])]),
                         defensive([(3, "Deontae Lawson", ("5", "3", "0", "0", "0", "0", "0"))])]),
        side("Georgia", [defensive([(5, "Malaki Starks", ("4", "2", "0", "0", "1", "0", "0"))])])]}]


BOX = {"v": box_of()}


def fake_get(path, params=None, timeout=90, tries=4):
    params = dict(params or {})
    EVENTS.append(("get", path, params))
    if FAIL["fn"] and FAIL["fn"](path, params):
        raise urllib.error.HTTPError("https://cfbd" + path, 503, "Service Unavailable", {}, None)
    if EMPTY["fn"] and EMPTY["fn"](path, params):
        return []
    if path == "/games":
        return copy.deepcopy(games_of(int(params["year"]))[params["seasonType"]])
    if path == "/teams/fbs":
        return copy.deepcopy(FBS_V["v"])
    if path == "/roster":
        return copy.deepcopy(ROSTER)
    if path == "/games/players":
        key = (params["seasonType"], params["week"])
        if key in BOX["v"]:
            return copy.deepcopy(BOX["v"][key])
        w = int(params["week"])
        return week_box(w) if params["seasonType"] == "regular" and 3 <= w <= GAMES["weeks"] else []
    if UNPLANTED["probe"]:
        raise urllib.error.HTTPError("https://cfbd" + path, 503, "Service Unavailable", {}, None)
    raise AssertionError("unplanted CFBD path %s" % path)


def players_digest(doc, unmapped, n, teams):
    """The players file, the UNMAPPED count and teams.json, `built_at` aside."""
    body = {"doc": {k: v for k, v in doc.items() if k != "built_at"},
            "unmapped": sorted([list(k) + [v] for k, v in unmapped.items()]), "n": n,
            "teams_json": {k: v for k, v in teams.items() if k != "built_at"}}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()
# ── FIXTURE END ──────────────────────────────────────────────────────────


GOLDEN = "d24eae08df6fd08925c04b2949837870eaf0e237108219cb17fd060ebf7b8616"
cfb.get = fake_get


def fresh(name):
    d = os.path.join(TMP, name)
    os.makedirs(d)
    cfb.OUT = d
    return d


def jz(p):
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def gz(p, o):
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        json.dump(o, fh)


def snapshot(d):
    out = {}
    for f in sorted(os.listdir(d)):
        if os.path.isfile(os.path.join(d, f)):
            with open(os.path.join(d, f), "rb") as fh:
                out[f] = fh.read()
    return out


def build(season=2026, keep=None, out="b", log=QUIET):
    d = fresh(out)
    doc, unmapped, n = cfb.build_season(season, log, keep=keep)
    teams = {}
    if os.path.exists(os.path.join(d, "teams.json")):    # absent when /teams/fbs failed
        with open(os.path.join(d, "teams.json"), encoding="utf-8") as fh:
            teams = json.load(fh)
    return doc, unmapped, n, teams


def schedule_doc(season, weeks):
    return {"season": season, "games": [
        {"id": w, "week": w, "season_type": "regular", "start": "%d-09-%02dT19:00:00.000Z" % (season, w)}
        for w in range(1, weeks + 1)]}


def plant_2025(d, weeks=2):
    """2025's other stored files, which no fill may touch, and this season's teams.json."""
    files = {"players-2025.json.gz": {"season": 2025, "players": {"1": {"name": "old", "g": []}}},
             "schedule-2025.json.gz": schedule_doc(2025, weeks),
             "ppa-2025.json.gz": {"season": 2025, "games": {}}}
    for f, o in files.items():
        gz(os.path.join(d, f), o)
    with open(os.path.join(d, "teams.json"), "w", encoding="utf-8") as fh:
        json.dump({"season": 2026, "teams": {"Alabama": {"conference": "SEC"}}}, fh)
    return snapshot(d)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE DEFENSIVE BOX SCORE IS KEPT, FROM THE SAME CALLS")
# ══════════════════════════════════════════════════════════════════════
KEEP = {}
del EVENTS[:]
D1 = build(keep=KEEP, out="s1")
calls = [e[1] for e in EVENTS if e[0] == "get"]
eq(sorted(calls), sorted(["/games", "/games", "/roster", "/games/players", "/games/players", "/games/players",
                          "/teams/fbs"]),
   "🔴 zero extra calls: the build's own /games x2, /roster, /games/players per week and /teams/fbs")
DEF = KEEP.get("defense") or {}
P = DEF.get("players") or {}
eq(P.get("3"), {"name": "Deontae Lawson", "team": "Alabama", "g": [
    {"game_id": "101", "d": "2026-08-29", "week": 1, "wk_i": 1, "seasonType": "regular",
     "tot": 7, "solo": 4, "sacks": 1, "tfl": 1.5, "pd": 1, "qb_hur": 2},
    {"game_id": "103", "d": "2026-09-05", "week": 2, "wk_i": 2, "seasonType": "regular",
     "tot": 6, "solo": 2, "sacks": 0, "tfl": 1, "pd": 0, "qb_hur": 1}]},
   "🔴 a linebacker's tackles, solos, sacks, TFL, PD and QB hurries per game, with the players file's "
   "game fields (game_id, d, week, wk_i, seasonType); the defensive TD is not a design field")
eq(P.get("5"), {"name": "Malaki Starks", "team": "Georgia", "g": [
    {"game_id": "101", "d": "2026-08-29", "week": 1, "wk_i": 1, "seasonType": "regular",
     "tot": 5, "solo": 3, "sacks": 0, "tfl": 0, "pd": 2, "qb_hur": 0, "int": 1},
    {"game_id": "201", "d": "2027-01-01", "week": 1, "wk_i": 101, "seasonType": "postseason",
     "tot": 3, "solo": 2, "sacks": 0.5, "tfl": 0.5, "pd": 0, "qb_hur": 1}]},
   "🔴 interceptions are the INT column (1, not the 34 return yards); a bowl is wk_i 101, after week 2; "
   "a game with no interception has no int field (absent, never a guessed 0)")
eq(P.get("2", {}).get("g", [{}])[0].get("tot"), 1,
   "   an offensive player's tackle is kept too (the defense file is every position, a team's tackle total)")
eq(sorted(P), ["2", "3", "5"],
   "🔴 nobody else: no team aggregate (-1, ' Team'), no blank name, no FCS-vs-FCS game (Montana), no FCS team "
   "(Mercer), no box-score game /games did not list (999)")
eq(KEEP.get("call_failures"), [], "   ...and a defensive row that is not a player record ('junk') is skipped, "
   "never a reason to lose the doc (or the season)")
eq(KEEP.get("completed_units"), [["postseason", 1], ["regular", 1], ["regular", 2]],
   "   the completed weeks /games lists with an in-scope game (Montana-Idaho alone would not count)")
eq((DEF.get("season"), DEF.get("kind"), DEF.get("fields"), DEF.get("scope_conferences")),
   (2026, "DESCRIPTIVE", ["int", "pd", "qb_hur", "sacks", "solo", "tfl", "tot"], ["SEC", "Sun Belt"]),
   "   the header names its season, kind, fields and the FBS scope it kept")
_FAIL_OPEN = {}
FAIL["fn"] = lambda path, params: path == "/teams/fbs"
build(keep=_FAIL_OPEN, out="s1-open")
FAIL["fn"] = None
ck(sorted((_FAIL_OPEN.get("defense") or {}).get("players") or {}) == ["2", "3", "5", "6", "7"]
   and (_FAIL_OPEN["defense"].get("scope") or "").startswith("UNFILTERED"),
   "   a failed /teams/fbs narrows nothing in this season's file, exactly as the players file (fail open, "
   "and says so; rebuilt the next run)", sorted((_FAIL_OPEN.get("defense") or {}).get("players") or {}))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE ROSTER KEEPS JERSEY, NAME AND POSITION")
# ══════════════════════════════════════════════════════════════════════
R = (KEEP.get("roster") or {}).get("teams") or {}
eq(R.get("Alabama"), [{"id": "1", "name": "Jalen Milroe", "jersey": 4, "position": "QB"},
                      {"id": "2", "name": "Ryan Williams", "jersey": 2, "position": "WR"},
                      {"id": "3", "name": "Deontae Lawson", "jersey": 0, "position": "LB"}],
   "🔴 id, firstName + lastName, the jersey (0 is a jersey) and the position (upper-cased); the row with no "
   "id is left out")
eq(R.get("Georgia"), [{"id": "4", "name": "Carson Beck", "jersey": 15, "position": "QB"},
                      {"id": "5", "name": "Malaki Starks", "jersey": 24, "position": "DB"},
                      {"id": "8", "name": "No Jersey", "jersey": None, "position": None}],
   "   a player with no jersey or position is kept, with None (never guessed)")
eq(sorted(R), ["Alabama", "Georgia", "Mercer", "Montana"], "   every team CFBD lists, FCS too (the full roster)")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 players-<season> AND EVERY OTHER EXISTING OUTPUT ARE UNCHANGED")
# ══════════════════════════════════════════════════════════════════════
D0 = build(keep=None, out="s3")
eq(players_digest(*D1), GOLDEN,
   "🔴 for the same planted CFBD answers, players-2026, the UNMAPPED count and teams.json are exactly what "
   "cfb.py wrote before the defense file existed (digest pinned from 4461f3657)")
eq(players_digest(*D0), players_digest(*D1), "   ...and keeping the defense changes nothing beside it")
_cols = {k for p in D1[0]["players"].values() for g in p["g"] for k in g}
ck(not (_cols & {"tot", "solo", "sacks", "tfl", "pd", "qb_hur"}) and "jersey" not in _cols
   and sorted(D1[0]["players"]) == ["1", "2", "4"],
   "   (no defensive column and no jersey in any players row; still only the prop positions)", sorted(_cols))
eq((D1[1].get(("defensive", "tot")), D1[1].get(("interceptions", "int")), D1[0]["coverage"]["team_aggregate_rows_excluded"]),
   (10, 1, 2), "   (the defensive types still count as UNMAPPED there, and the team rows excluded are still 2)")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 EACH FILE IS REWRITTEN ONLY WHEN ITS CONTENT CHANGED")
# ══════════════════════════════════════════════════════════════════════
d4 = fresh("s4")
eq(cfb.store_kept(2026, KEEP, QUIET),
   "roster-2026.json.gz written; defense-2026.json.gz written", "the first build writes both")
ck(jz(d4 + "/defense-2026.json.gz")["players"] == P and bool(jz(d4 + "/roster-2026.json.gz").get("written_at")),
   "   the stored defense is the doc, and each file is stamped (written_at)")
before = snapshot(d4)
mt = {f: os.stat(os.path.join(d4, f)).st_mtime_ns for f in before}
eq(cfb.store_kept(2026, copy.deepcopy(KEEP), QUIET),
   "roster-2026.json.gz unchanged; defense-2026.json.gz unchanged",
   "🔴 the next build with the same content rewrites neither")
ck(snapshot(d4) == before and all(os.stat(os.path.join(d4, f)).st_mtime_ns == mt[f] for f in before),
   "   ...byte for byte (git cannot delta a gzip, so an identical rewrite is a full copy kept for ever)")
BOX["v"] = box_of(lawson=("8",) + LAWSON[1:])
K2 = {}
build(keep=K2, out="s4-b")
cfb.OUT = d4
eq(cfb.store_kept(2026, K2, QUIET), "roster-2026.json.gz unchanged; defense-2026.json.gz written",
   "🔴 one more tackle rewrites the defense file and leaves the roster alone")
eq(jz(d4 + "/defense-2026.json.gz")["players"]["3"]["g"][0]["tot"], 8, "   ...with the new number")
BOX["v"] = box_of()
with open(d4 + "/roster-2026.json.gz", "wb") as fh:
    fh.write(b"\x1f\x8b broken")
eq(cfb.write_if_changed("roster-2026.json.gz", KEEP["roster"], QUIET), "written",
   "   an unreadable stored file counts as changed")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 ANY FAILED CALL BUILDS NO DEFENSE DOC (IT WOULD REPLACE A COMPLETE FILE)")
# ══════════════════════════════════════════════════════════════════════
K5 = {}
FAIL["fn"] = lambda path, params: path == "/games/players" and params.get("week") == "2" \
    and params.get("seasonType") == "regular"
build(keep=K5, out="s5")
FAIL["fn"] = None
ck("defense" not in K5 and K5.get("call_failures") == ["/games/players regular week 2: HTTPError"],
   "🔴 a season missing a week builds no defense doc, and names the week", K5.get("call_failures"))
eq(cfb.store_kept(2026, K5, QUIET),
   "roster-2026.json.gz written; defense-2026.json.gz not built: a CFBD call failed: /games/players "
   "regular week 2: HTTPError", "   ...so only the roster is written, and the line says why the defense was not")
K5p = {}
FAIL["fn"] = lambda path, params: path == "/games" and params.get("seasonType") == "postseason"
build(keep=K5p, out="s5-p")
FAIL["fn"] = None
ck("defense" not in K5p and K5p.get("call_failures") == ["/games postseason: HTTPError 503"],
   "🔴 a failed postseason /games (every bowl and CFP game gone from the build) is a failed call too: no "
   "defense doc", K5p.get("call_failures"))
eq(cfb.store_kept(2026, K5p, QUIET),
   "roster-2026.json.gz written; defense-2026.json.gz not built: a CFBD call failed: /games postseason: "
   "HTTPError 503", "   ...so this season's stored defense file keeps its bowls until a complete build")
K5r = {}
FAIL["fn"] = lambda path, params: path == "/roster"
build(keep=K5r, out="s5-r")
FAIL["fn"] = None
ck("roster" not in K5r and K5r.get("why_not", {}).get("roster") == "/roster failed" and "defense" in K5r,
   "   a failed /roster builds no roster doc (never an empty one), and the defense is still kept",
   K5r.get("why_not"))

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 THE LOG SAYS ONLY WHAT IS TRUE")
# ══════════════════════════════════════════════════════════════════════
LINES = []
build(keep={}, out="s6-ok", log=LINES.append)
ck(any("UNMAPPED STAT defensive/tot: 10 rows NOT collected in players-2026 (kept in defense-2026)" in ln
       for ln in LINES),
   "the season build's UNMAPPED line says the defensive stat is kept in defense-2026 when it was",
   [ln for ln in LINES if "UNMAPPED" in ln][:2])
del LINES[:]
FAIL["fn"] = lambda path, params: path == "/games/players" and params.get("week") == "2"
build(keep={}, out="s6-fail", log=LINES.append)
FAIL["fn"] = None
ck(not any("kept in defense" in ln for ln in LINES)
   and any("UNMAPPED STAT defensive/tot" in ln for ln in LINES),
   "🔴 ...and never when the defense doc was not built (a week failed)",
   [ln for ln in LINES if "kept in defense" in ln][:2])
d6 = fresh("s6-fill")
plant_2025(d6)
del LINES[:]
eq(cfb.backfill_defense(2025, LINES.append), "roster-2025.json.gz written; defense-2025.json.gz written",
   "   (a 2025 fill that built and wrote both files, so the line below is asked of a real run)")
ck(any("defense: 3 players" in ln for ln in LINES)
   and not any("NOT collected" in ln or "players-2025" in ln for ln in LINES),
   "🔴 the 2025 fill, which never writes players-2025, prints no players-file line",
   [ln for ln in LINES if "NOT collected" in ln or "players-2025" in ln][:2])

# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 2025: FILLED ONCE WHILE MISSING, PRICED FIRST, NOTHING ELSE TOUCHED")
# ══════════════════════════════════════════════════════════════════════
d7 = fresh("s7")
SNAP = plant_2025(d7)

ALLOW["fn"] = lambda purpose: False
del EVENTS[:]
eq(cfb.backfill_defense(2025, QUIET), "refused", "🔴 a fill the budget refuses...")
eq([e[0] for e in EVENTS], ["price"], "   ...makes no CFBD call at all")
ck(snapshot(d7) == SNAP, "   ...and writes nothing", sorted(set(snapshot(d7)) - set(SNAP)))
ALLOW["fn"] = lambda purpose: True

del EVENTS[:]
got = cfb.backfill_defense(2025, QUIET)
eq(got, "roster-2025.json.gz written; defense-2025.json.gz written", "🔴 allowed: both files are written")
gets = [e for e in EVENTS if e[0] == "get"]
ck(EVENTS and EVENTS[0][0] == "price" and EVENTS[0][2] == "roster + defense back-fill 2025"
   and EVENTS[0][1] == cfb.season_build_max(2025),
   "🔴 ...priced by cfbd_budget.preflight BEFORE the first call, at season_build_max", EVENTS[:2])
eq(sorted({e[1] for e in gets}), ["/games", "/games/players", "/roster", "/teams/fbs"],
   "   the same /games + /roster + /games/players calls as a season build (and /teams/fbs for its scope)")
ck(gets and all(str(e[2].get("year")) == "2025" for e in gets), "   ...for 2025 only",
   sorted({str(e[2].get("year")) for e in gets}))
after = snapshot(d7)
ck(all(after.get(f) == b for f, b in SNAP.items()),
   "🔴 players-2025, schedule-2025, ppa-2025 and teams.json are byte-for-byte untouched (teams.json stays "
   "this season's directory)", [f for f, b in SNAP.items() if after.get(f) != b])
eq(sorted(set(after) - set(SNAP)), ["defense-2025.json.gz", "roster-2025.json.gz"],
   "   ...and no other file appears")
eq(sorted(jz(d7 + "/defense-2025.json.gz")["players"]), ["2", "3", "5"], "   the 2025 defense is built by the same rules")
eq(jz(d7 + "/defense-2025.json.gz")["players"]["3"]["g"][0]["d"], "2025-08-29", "   ...from 2025's games")
del EVENTS[:]
eq((cfb.backfill_defense(2025, QUIET), EVENTS), ("already stored", []),
   "🔴 once both are stored it is never asked again (no price, no call)")

os.remove(d7 + "/defense-2025.json.gz")
gz(d7 + "/roster-2025.json.gz", {"season": 2025, "teams": {"Alabama": [{"id": "1", "name": "an older roster"}]}})
SNAP_R = snapshot(d7)["roster-2025.json.gz"]
eq(cfb.backfill_defense(2025, QUIET), "roster-2025.json.gz already stored; defense-2025.json.gz written",
   "🔴 one file missing: only that one is written")
ck(snapshot(d7)["roster-2025.json.gz"] == SNAP_R, "   ...a stored 2025 file, even an older one, is never rewritten")

os.remove(d7 + "/defense-2025.json.gz")
FAIL["fn"] = lambda path, params: True
got = cfb.backfill_defense(2025, QUIET)
FAIL["fn"] = None
ck(got.startswith("not written: SourceUnavailable") and not os.path.exists(d7 + "/defense-2025.json.gz"),
   "🔴 CFBD refusing everything: the fill returns a line, never raises, writes nothing", got)
_pf = cfbd_budget.preflight
cfbd_budget.preflight = lambda *a, **k: (_ for _ in ()).throw(OSError("budget unreadable"))
got = cfb.backfill_defense(2025, QUIET)
cfbd_budget.preflight = _pf
ck(got.startswith("not written: OSError"), "   ...nor when the price itself cannot be read", got)

# ══════════════════════════════════════════════════════════════════════
section("8. 🔴 THE FILL IS WRITTEN ONCE, SO IT STORES ONLY A COMPLETE SEASON")
# ══════════════════════════════════════════════════════════════════════
# Each case: the fill writes NOTHING (neither file), says why, and the next
# run asks again (not "already stored"). ⚠️ The current season's file is
# rebuilt tomorrow; a history season's is never asked for again.


def gap_case(name, label, want, fail=None, empty=None, fbs=None, no_elo=False):
    d = fresh("s8-" + name)
    snap = plant_2025(d)
    FAIL["fn"], EMPTY["fn"], GAMES["no_elo"] = fail, empty, no_elo
    if fbs is not None:
        FBS_V["v"] = fbs
    try:
        got = cfb.backfill_defense(2025, QUIET)
    finally:
        FAIL["fn"], EMPTY["fn"], GAMES["no_elo"], FBS_V["v"] = None, None, False, FBS
    wrote = sorted(set(snapshot(d)) - set(snap))
    ck(got.startswith("not written, asked again next run: ") and want in got and not wrote,
       label, "%s | wrote %s" % (got[:300], wrote))
    return d


_d8a = gap_case("bowls", "🔴 a failed postseason /games: no bowls in the build, so nothing is stored (not even "
                "the complete roster)", "a CFBD call failed: /games postseason: HTTPError 503",
                fail=lambda path, params: path == "/games" and params.get("seasonType") == "postseason")
cfb.OUT = _d8a
del EVENTS[:]
_again = cfb.backfill_defense(2025, QUIET)
ck(EVENTS and EVENTS[0][0] == "price" and _again == "roster-2025.json.gz written; defense-2025.json.gz written"
   and [g["game_id"] for g in jz(_d8a + "/defense-2025.json.gz")["players"]["5"]["g"]] == ["101", "201"],
   "   ...and the next run asks again (priced again) and stores the season with its bowl", _again)
gap_case("week1", "🔴 a completed regular week answered HTTP 200 with no rows: not stored",
         "completed week(s) with no defensive rows: [['regular', 1]]",
         empty=lambda path, params: path == "/games/players" and params.get("week") == "1"
         and params.get("seasonType") == "regular")
gap_case("week1v", "   ...which the probe's own verify names too (a week missing below the log's latest)",
         "THE PLAYER LOG IS MISSING COMPLETED WEEK(S) [1]",
         empty=lambda path, params: path == "/games/players" and params.get("week") == "1"
         and params.get("seasonType") == "regular")
gap_case("post", "🔴 the bowls answered HTTP 200 with no rows (verify reads regular weeks only): not stored",
         "completed week(s) with no defensive rows: [['postseason', 1]]",
         empty=lambda path, params: path == "/games/players" and params.get("seasonType") == "postseason")
gap_case("fbsfail", "🔴 /teams/fbs failed: an UNFILTERED file is not stored for good",
         "no FBS scope", fail=lambda path, params: path == "/teams/fbs")
gap_case("fbsshort", "   ...nor when /teams/fbs lists under 100 schools",
         "no FBS scope", fbs=FBS[:5])
gap_case("elo", "🔴 anything the probe's verify names stops the fill (here: rows with no Elo and no "
         "classification, which the probe would never write)", "verify: ", no_elo=True)
gap_case("roster", "   a failed /roster: no roster doc, nothing stored", "no roster doc (/roster failed)",
         fail=lambda path, params: path == "/roster")
gap_case("week2", "   a failed /games/players week: nothing stored",
         "no defense doc (a CFBD call failed: /games/players regular week 2: HTTPError)",
         fail=lambda path, params: path == "/games/players" and params.get("week") == "2")

# ══════════════════════════════════════════════════════════════════════
section("9. 💰 THE PRICE COVERS EVERY CALL, ON A FULL SEASON WITH NO SLACK")
# ══════════════════════════════════════════════════════════════════════


def priced_vs_made(weeks):
    d = fresh("s9-%d" % weeks)
    plant_2025(d, weeks=weeks)
    GAMES["weeks"] = weeks
    del EVENTS[:]
    try:
        got = cfb.backfill_defense(2025, QUIET)
    finally:
        GAMES["weeks"] = 2
    priced = [e[1] for e in EVENTS if e[0] == "price"]
    made = sum(1 for e in EVENTS if e[0] == "get")
    return got, (priced[0] if priced else None), made


# ⚠️ At the price's own floor (REG_WEEKS + 1 = 16 today; 2025 had regular weeks
#    1-16), so the planted season leaves the price no room to hide a call.
_W = max(16, len(cfb.REG_WEEKS) + 1)
_got16, _p16, _m16 = priced_vs_made(_W)
eq(_got16, "roster-2025.json.gz written; defense-2025.json.gz written",
   "a planted %d-week season is filled" % _W)
ck(_p16 is not None and _p16 >= _m16 and _p16 - _m16 == 0,
   "🔴 ...priced at exactly the calls it made, NO slack, so one call more in build_season fails this "
   "(%s priced, %d made)" % (_p16, _m16))
_got20, _p20, _m20 = priced_vs_made(20)
ck(_got20.endswith("defense-2025.json.gz written") and _p20 is not None and _p20 >= _m20,
   "   a stored season with 20 regular weeks raises the price to cover them (%s priced, %d made)" % (_p20, _m20))
_real = cfbd_budget.season_build_calls
cfbd_budget.season_build_calls = lambda w: _real(w) + 1000
try:
    _bumped = cfbd_budget.calls_per_build(3)["cfb-probe"]
finally:
    cfbd_budget.season_build_calls = _real
eq(_bumped - cfbd_budget.calls_per_build(3)["cfb-probe"], 1000,
   "🔴 the schedule's reserve (calls_per_build) reads the SAME count as the fill's price: one copy")

# ══════════════════════════════════════════════════════════════════════
section("10. 🔴 cfb-probe, RUN: THIS SEASON'S AND 2025's ROSTER + DEFENSE")
# ══════════════════════════════════════════════════════════════════════
d10 = fresh("s10")
SNAP10 = plant_2025(d10)
_cwd = os.path.join(TMP, "cwd")       # ⛔ nothing relative to the cwd lands in the repo
os.makedirs(_cwd)
_saved = (os.environ.get("SEASON"), cfb.store_new_data, fb_history.store_cfb, subprocess.run, os.getcwd())
_selftest = []


def _run(args, *a, **k):
    if isinstance(args, (list, tuple)) and str(args[-1]).endswith("test_cfb.py"):
        _selftest.append(args[-1])
        return subprocess.CompletedProcess(args, 0, "planted self-test: passed", "")
    return _saved[3](args, *a, **k)


os.environ["SEASON"] = "2026"
cfb.store_new_data = lambda *a, **k: None          # NWS + the stored-only CFBD extras
fb_history.store_cfb = lambda *a, **k: None        # T70's older seasons
subprocess.run = _run                              # the probe's own self-test (test_cfb.py runs on its own)
ALLOW["fn"] = lambda purpose: purpose.startswith("roster + defense back-fill")
UNPLANTED["probe"] = True
PLOG = []
os.chdir(_cwd)
try:
    _ok = cfb.probe(log=PLOG.append)
finally:
    os.chdir(_saved[4])
    if _saved[0] is None:
        os.environ.pop("SEASON", None)
    else:
        os.environ["SEASON"] = _saved[0]
    cfb.store_new_data, fb_history.store_cfb, subprocess.run = _saved[1], _saved[2], _saved[3]
    ALLOW["fn"] = lambda purpose: True
    UNPLANTED["probe"] = False
_a10 = snapshot(d10)
ck(_ok is True and _selftest, "the probe ran (self-test, season 2026, the history steps) and reported success",
   [ln for ln in PLOG if "FAILED" in ln][:3])
eq(sorted(f for f in ("roster-2026.json.gz", "defense-2026.json.gz", "roster-2025.json.gz",
                      "defense-2025.json.gz") if f in _a10),
   ["defense-2025.json.gz", "defense-2026.json.gz", "roster-2025.json.gz", "roster-2026.json.gz"],
   "🔴 one cfb-probe writes this season's roster + defense AND 2025's one-time fill")
ck(jz(d10 + "/defense-2026.json.gz")["players"] == P and "players-2026.json.gz" in _a10,
   "   ...this season's from its own build (the same doc the build kept), beside its players file")
eq(jz(d10 + "/defense-2025.json.gz")["players"]["3"]["g"][0]["d"], "2025-08-29", "   ...2025's from 2025's games")
with open(d10 + "/teams.json", encoding="utf-8") as fh:
    _tj = json.load(fh)
eq(_tj.get("season"), 2026, "🔴 teams.json is this season's directory after the 2025 fill ran")
ck(all(_a10.get(f) == b for f, b in SNAP10.items() if f != "teams.json"),
   "🔴 players-2025, schedule-2025 and ppa-2025 are byte-for-byte untouched by the probe",
   [f for f, b in SNAP10.items() if f != "teams.json" and _a10.get(f) != b])
ck(os.listdir(_cwd) == [], "   (and nothing was written relative to the working directory)", os.listdir(_cwd))
eq(cfb.DEFENSE_HISTORY, (2025,), "   the one-time fill's seasons")
