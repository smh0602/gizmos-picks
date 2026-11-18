#!/usr/bin/env python3
r"""EVERY CHALLENGER THAT READS A STORED HISTORY SEASON READS ALL OF THEM OR REFUSES (research/fb_refit_spec.md
§3d, §3k). `[review 2, 2026-11-17]` Planted trees and a pinned clock only; reads no live data.

The defect: need_history (H / HC train on every declared history season or none) guarded their TRAINING
ROWS only. The other way into the same files, fb_challengers.history_rating_games -> fb_history.games, fed
h_own (H / HC's input), rated_games and attach_qb (T75's QB, QP, QBC, QPC: "solved on every stored schedule,
latest and history", §3k), and once fb_history.games stopped raising (this branch, so a corrupt file is
rebuilt instead of crashing every reader) an unreadable season was dropped there in silence. On a copy of the
real tree a truncated NFL 2020 moved 514 of 557 rows' QB inputs with no error, while H, on the same file,
was refused; the Monday contest would have scored QB and QP on 6 seasons of 7.

The class, asked of EVERY challenger in both leagues (none named champion, so HC is one too), with one stored
history season unreadable at a time (declared and undeclared, schedules and lines, cut short and bad JSON):
  §1 (a) its input, and H / HC's training rows, are byte-identical or it raises HistoryIncomplete; never a
         different number in silence;
     (b) one that refuses a season the contract tracks names it and DECLARES it, so named champion that
         file is its contract input (freshness.champion_inputs plans the repair);
     (c) and really reads it: with the season not stored, its input moves or it refuses it as missing;
     (e) H / HC's input itself refuses a missing DECLARED season (it was saved only by history_rows, later);
  §2 (d) no module reads fb_history.games / lines except through fb_challengers.history_games /
         history_lines, the one place a stored season that cannot be read is refused;
  §3 the college Monday contest (rule 6): HC, QBC and QPC are NOT APPLICABLE with the file named, and the
     others are built and judged (NFL's is test_fb_refit.py §18).

# @vacuity 🔴 a stored history schedule that cannot be read is refused, never dropped (T75's QB read 6 of 7)
#   file: fb_challengers.py
#   find:     _refuse(root, bad, "every stored " + lg + " history season is read or none, and %d stored file(s)")
#   with:     pass
#
# @vacuity 🔴 ...and stored college history lines too (an undeclared season: need_history never sees it)
#   file: fb_challengers.py
#   find:     _refuse(root, bad, "every stored ncaaf history lines file is read or none, and %d stored file(s)")
#   with:     pass
#
# @vacuity 🔴 H / HC's input itself asks for every declared season (it was saved only by history_rows)
#   file: fb_challengers.py
#   find:     need_history(lg, root)                   # H / HC's own input: every declared season, or none
#   with:     pass
#
# @vacuity 🔴 T75's QB declares the history schedules it reads (so named champion, they are its inputs)
#   file: fb_challengers.py
#   find:            "files": ("../history/schedule-{s}.json.gz",), "seasons": (2018, 2019, 2020, 2021, 2022, 2023, 2024),  # QB
#   with:            "files": (),  # QB
#
# @vacuity 🔴 ...and QBC (college) the college ones (rule 6)
#   file: fb_challengers.py
#   find:             "files": ("../history/schedule-{s}.json.gz",), "seasons": (2023, 2024),  # QBC
#   with:             "files": (),  # QBC
#
# @vacuity 🔴 no module reads fb_history.games outside the one way in (a read that changes no number)
#   file: fb_challengers.py
#   find:     G = list(FM.rating_games(lg, root))
#   with:     G = list(FM.rating_games(lg, root)) + [] * len(__import__("fb_history").games(lg, root))
#
# @vacuity 🔴 the college contest: an input that refuses makes ITS challenger NOT APPLICABLE
#   file: fb_refit.py
#   find:                 if reg and n in unread:              # its inputs could not be built (above)
#   with:                 if False:              # its inputs could not be built (above)
"""
import ast
import atexit
import datetime
import glob
import gzip
import json
import os
import random
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"

import fb_challengers as FC  # noqa: E402
import fb_model as FM  # noqa: E402
import fb_refit as R  # noqa: E402
import freshness as F  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

# A test asks the code: no champion named, whatever main names (so HC is a challenger here too).
FM.CHAMPION.update(nfl=None, ncaaf=None)
UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 11, 2, 11, 17, tzinfo=UTC)     # a Monday
TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])
TEAMS = ["T%d" % i for i in range(8)]
RNG = random.Random(1117)
DECLARED = {"nfl": "H", "ncaaf": "HC"}       # each league's history challenger: the seasons the contract tracks


def tree():
    t = tempfile.mkdtemp(prefix="fbhin-")
    TREES.append(t)
    return t


def put(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with (gzip.open(p, "wt", encoding="utf-8") if p.endswith(".gz") else open(p, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


def season_games(lg, s):
    """Eight final games of history season `s` among TEAMS, FBS against FBS, with closing lines."""
    out = []
    for i in range(8):
        h, a = RNG.sample(TEAMS, 2)
        out.append({"id": "%s%d_%d" % (lg, s, i), "start": "%d-%02d-%02dT17:00:00Z" % (s, 9 + i // 3, 3 + 9 * (i % 3)),
                    "home": h, "away": a, "final": True, "neutral": False, "home_class": "fbs", "away_class": "fbs",
                    "home_score": RNG.randint(3, 45), "away_score": RNG.randint(3, 45),
                    "closing_spread": -3.0, "closing_total": 44.5, "closing_ml_home": -160, "closing_ml_away": 140})
    return out


# ── the planted league: 12 weeks of 2025 (schedule + player logs), the same games in both leagues ──
BASE = tree()
_rot, _rounds = TEAMS[:], []
for _ in range(7):
    _rounds.append([(_rot[i], _rot[-1 - i]) for i in range(4)])
    _rot = [_rot[0], _rot[-1]] + _rot[1:-1]
SCHED, LOGS = [], {}
for w in range(12):
    day = (datetime.date(2025, 9, 7) + datetime.timedelta(weeks=w)).isoformat()
    for j, (h, a) in enumerate(_rounds[w % 7]):
        h, a = (a, h) if w % 2 else (h, a)
        gid, pts = "g%d_%d" % (w, j), {}
        for o in (h, a):
            pa, ru, pl = RNG.randint(150, 330), RNG.randint(60, 190), RNG.randint(52, 72)
            pts[o] = RNG.randint(3, 45) + (pa - 240) // 25 + (ru - 125) // 30
            for pos, st in (("QB", {"att": pl // 2, "pass_yds": pa - 20, "car": RNG.randint(0, 9),
                                    "rush_yds": RNG.randint(-5, 60)}),
                            ("RB", {"car": RNG.randint(16, 34), "rush_yds": ru - 10, "rec_yds": 15, "tgt": 4}),
                            ("WR", {"rec_yds": pa - 50, "tgt": 18})):
                LOGS.setdefault(o + pos, {"name": o + pos, "pos": pos, "g": []})["g"].append(
                    dict(st, d=day, game_id=gid, team=o))
        SCHED.append({"id": gid, "start": day + "T17:00", "home": h, "away": a, "final": True, "neutral": False,
                      "home_score": max(0, pts[h]), "away_score": max(0, pts[a])})
for lg in ("nfl", "ncaaf"):
    put(BASE, "data/%s/latest/schedule-2025.json.gz" % lg, {"season": 2025, "games": SCHED})
    put(BASE, "data/%s/latest/players-2025.json.gz" % lg, {"players": LOGS})
# every declared history season (H: NFL 2018-2024; HC: college 2023-2024 schedules and lines), and one
#    season stored but declared by nobody (NFL 2017, college 2022): every STORED one is read
for lg, extra in (("nfl", 2017), ("ncaaf", 2022)):
    for s in sorted(set(FC.CHALLENGERS[DECLARED[lg]]["seasons"]) | {extra}):
        games = season_games(lg, s)
        put(BASE, "data/%s/history/schedule-%d.json.gz" % (lg, s),
            {"season": s, "written_at": "2026-10-15T00:00:00Z", "games": games})
        if lg == "ncaaf":                     # lines that differ from the schedule's closing ones
            put(BASE, "data/ncaaf/history/lines-%d.json.gz" % s, {"season": s, "written_at": "2026-10-15T00:00:00Z",
                "games": {g["id"]: {"spread": 7.0, "total": 51.5, "ml_home": -300, "ml_away": 240} for g in games}})


def row(g):
    return {"id": g["id"], "season": 2025, "day": g["start"][:10], "home": g["home"], "away": g["away"],
            "final": True, "hs": g["home_score"], "as": g["away_score"], "M": 3.0, "T": 44.5, "pml": 0.6,
            "sig": {"neutral": 0.0, "dome": 0.0, "own_m": 2.0, "own_t": 45.0, "h2h_m": None, "h2h_t": None,
                    "form_m": None, "form_t": None, "def": None, "poss": None, "out": None, "vac_h": None,
                    "vac_a": None}}


ROWS = {lg: [dict(row(g), lg=lg) for g in SCHED if "g1_" <= g["id"][:3] <= "g5_"] for lg in ("nfl", "ncaaf")}


def inputs(n, t):
    """Challenger n's input on every planted row, attached as fb_refit.league attaches it (fresh copies of
    the same rows), or ("raised", the message) for HistoryIncomplete."""
    lg = FC.CHALLENGERS[n]["league"]
    rs = [dict(r, sig=dict(r["sig"])) for r in ROWS[lg]]
    try:
        FC.attach(n, lg, rs, t)
    except FC.HistoryIncomplete as e:
        return ("raised", str(e))
    return json.dumps([r["sig"] for r in rs], sort_keys=True, default=repr)


def training(lg, t):
    """H / HC's training rows (fb_challengers.history_rows), or ("raised", the message)."""
    try:
        return json.dumps(FC.history_rows(lg, t), sort_keys=True, default=repr)
    except FC.HistoryIncomplete as e:
        return ("raised", str(e))


def variant(rel, how):
    """A copy of BASE with data/<rel> cut short ("truncate"), bad JSON ("json") or not stored ("gone")."""
    t = tree()
    shutil.rmtree(t)
    shutil.copytree(BASE, t)
    p = os.path.join(t, "data", rel)
    if how == "gone":
        os.remove(p)
    elif how == "truncate":
        b = open(p, "rb").read()
        open(p, "wb").write(b[:len(b) // 2])
    else:
        open(p, "wb").write(gzip.compress(b'{"season": 2000, "games": {'))
    return t


def tracked(lg, rel):
    """Is data/<rel> a file the freshness contract has a row for (a declared history season)?"""
    d = os.path.join(BASE, "data", lg).replace("\\", "/")
    return any(r[1][1].replace("\\", "/") == "%s/%s" % (os.path.join(BASE, "data").replace("\\", "/"), rel)
               for r in F.contract(d, os.path.join(BASE, "picks"), NOW))


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 NO CHALLENGER'S INPUT MOVES IN SILENCE WHEN A STORED HISTORY SEASON CANNOT BE READ, BOTH LEAGUES")
# ══════════════════════════════════════════════════════════════════════
INTACT = {n: inputs(n, BASE) for n in FC.CHALLENGERS}
TRAIN = {lg: training(lg, BASE) for lg in ("nfl", "ncaaf")}
ck(all(not isinstance(v, tuple) for v in list(INTACT.values()) + list(TRAIN.values()))
   and all(json.loads(TRAIN[lg]) for lg in TRAIN),
   "   (on the intact tree every challenger of both leagues builds its input, and H / HC have training rows)",
   {n: v for n, v in INTACT.items() if isinstance(v, tuple)})
CASES = (("nfl/history/schedule-2024.json.gz", "truncate"),      # declared (H), cut short
         ("nfl/history/schedule-2017.json.gz", "json"),          # stored, declared by nobody
         ("ncaaf/history/schedule-2024.json.gz", "truncate"),    # declared (HC)
         ("ncaaf/history/lines-2023.json.gz", "json"),           # declared (HC), lines
         ("ncaaf/history/lines-2022.json.gz", "json"))           # stored, declared by nobody: need_history never asks
silent, undeclared, unread, missing_ok, refused = {}, {}, {}, {}, {}
for rel, how in CASES:
    lg = rel.split("/")[0]
    tv, tg = variant(rel, how), variant(rel, "gone")
    for n, c in FC.CHALLENGERS.items():
        if c["league"] != lg:
            continue
        got = inputs(n, tv)
        if not isinstance(got, tuple):
            if got != INTACT[n]:
                silent["%s %s" % (n, rel)] = "its input moved with no error"
            continue
        refused.setdefault(rel, []).append(n)
        if rel + " (corrupt:" not in got[1]:
            undeclared["%s %s" % (n, rel)] = "does not name it: " + got[1][:160]
        if tracked(lg, rel):
            want = os.path.join(tv, "data", rel).replace("\\", "/")
            mine = {F.champion_path(os.path.join(tv, "data", lg).replace("\\", "/"), pat, 2026)
                    for pat, _due in F.champion_inputs(lg, {lg: n})}
            if want not in mine:
                undeclared["%s %s" % (n, rel)] = "named champion, the file is not its contract input"
        gone = inputs(n, tg)
        if not (isinstance(gone, tuple) and rel + " (missing)" in gone[1]) and gone == INTACT[n]:
            unread["%s %s" % (n, rel)] = "unchanged with the season not stored"
        if c.get("history") and tracked(lg, rel):
            missing_ok["%s %s" % (n, rel)] = isinstance(gone, tuple) and rel + " (missing)" in gone[1]
    hist = DECLARED[lg]                       # H / HC's training rows: every stored season or none
    got = training(lg, tv)
    if not isinstance(got, tuple) and got != TRAIN[lg]:
        silent["%s training rows %s" % (hist, rel)] = "moved with no error"
    elif isinstance(got, tuple):
        refused.setdefault(rel, []).append(hist + " (training rows)")
eq(silent, {}, "🔴 (a) one stored history season unreadable (an NFL and a college schedule cut short, bad JSON in "
   "a schedule or a lines file, declared or not): no challenger of either league builds a different input, and "
   "H / HC no different training rows, in silence; each is byte-identical or refuses")
ck(all(refused.get(rel) for rel, _how in CASES)
   and all(any(x.startswith(DECLARED[rel.split("/")[0]]) for x in refused[rel]) for rel, _how in CASES),
   "   (each planted season is read: every case has a challenger that refuses, H / HC in each of theirs)", refused)
eq(undeclared, {}, "🔴 (b) every challenger that refuses names the unreadable file, and one the contract tracks is "
   "a file it DECLARES: named champion, it is its contract input (freshness.champion_inputs plans the repair)")
eq(unread, {}, "🔴 (c) ...and it really reads it: with that season not stored, its input moves (T75: every stored "
   "season) or it refuses it as missing (H / HC: every declared season)")
ck(missing_ok and all(missing_ok.values()),
   "🔴 (e) H / HC's input ITSELF refuses a missing declared season (h_own asks need_history; it was saved only "
   "because history_rows asked later in the same build)", missing_ok)

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE ONE WAY IN: fb_history.games AND lines ARE READ ONLY THROUGH history_games / history_lines")
# ══════════════════════════════════════════════════════════════════════
seen, bad = set(), []
ALLOWED = {("fb_challengers.py", "history_games"), ("fb_challengers.py", "history_lines")}


def walk(node, fn, mod, mods):
    for ch in ast.iter_child_nodes(node):
        f = ch.name if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)) else fn
        if isinstance(ch, ast.Attribute) and ch.attr in ("games", "lines") and (
                (isinstance(ch.value, ast.Name) and ch.value.id in mods)
                or (isinstance(ch.value, ast.Call) and getattr(ch.value.func, "id", None) == "__import__"
                    and [getattr(a, "value", None) for a in ch.value.args[:1]] == ["fb_history"])):
            if (mod, f) in ALLOWED:
                seen.add((mod, f))
            else:
                bad.append("%s:%d (in %s)" % (mod, ch.lineno, f))
        walk(ch, f, mod, mods)


for p in sorted(glob.glob(os.path.join(ROOT, "*.py"))):
    m = os.path.basename(p)
    if m.startswith("test_") or m == "fb_history.py":
        continue
    t = ast.parse(open(p, encoding="utf-8").read())
    mods = {a.asname or a.name for x in ast.walk(t) if isinstance(x, ast.Import) for a in x.names
            if a.name == "fb_history"}
    bad += ["%s:%d (from fb_history import %s)" % (m, x.lineno, a.name) for x in ast.walk(t)
            if isinstance(x, ast.ImportFrom) and x.module == "fb_history" for a in x.names
            if a.name in ("games", "lines", "*")]
    walk(t, None, m, mods)
ck(not bad and seen == ALLOWED,
   "🔴 (d) no module reads fb_history.games or fb_history.lines except through fb_challengers.history_games and "
   "history_lines, where a stored season that cannot be read is refused (and the scan finds those two)",
   (bad, sorted(seen)))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE COLLEGE MONDAY CONTEST (RULE 6): EVERY CHALLENGER THAT READS THE SEASON IS NOT APPLICABLE")
# ══════════════════════════════════════════════════════════════════════
# NFL's is test_fb_refit.py §18 (one season missing, one corrupt, through weekly()). ⚠️ No rows, as §18:
#    every challenger is still built and judged, quickly, and the history seasons are read first.
T3 = variant("ncaaf/history/schedule-2024.json.gz", "truncate")
doc = R.league("ncaaf", T3, NOW, rows=[], added={n: "2025-01-01" for n in FC.CHALLENGERS})
by = {x["name"]: x for x in doc["challengers"]}
reads = sorted(n for n in by if FC.CHALLENGERS[n].get("seasons") and any(
    p.replace(os.sep, "/").endswith("ncaaf/history/schedule-2024.json.gz") for p in FC.history_files(n, T3)))
k = sum(1 for x in by.values() if x["registered"] and not x.get("withdrawn"))
ck("HC" in reads and len(reads) > 1 and len(by) == k == 15
   and all(by[n]["verdict"] == "NOT APPLICABLE" and by[n].get("alpha") == 0.01 / k and "counted" not in by[n]
           and "ncaaf/history/schedule-2024.json.gz (corrupt:" in by[n].get("history_incomplete", "") for n in reads)
   and all(x["verdict"] != "NOT APPLICABLE" and "counted" in x for n, x in by.items() if n not in reads),
   "🔴 college, one declared schedule cut short, no champion: %s are NOT APPLICABLE with the file named, still "
   "in the divisor (0.01 / 15), never scored on the seasons that could be read; the other %d are built and "
   "judged" % (", ".join(reads), len(by) - len(reads)),
   {n: (x.get("verdict"), (x.get("history_incomplete") or "")[:90]) for n, x in by.items()})
