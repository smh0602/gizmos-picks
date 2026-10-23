#!/usr/bin/env python3
"""A POSTPONED GAME PLAYED LATER UNDER THE SAME ID IS GRADED FROM ITS REAL FINAL.

`[2026-10-23]` Rays @ Guardians (MLB game 849817) was postponed on 10-16. The
Game Lines tab's builder graded it VOID at 10-17 10:05Z ("the first stored
grade stands"), the game was played on 10-18 under the same id (Tampa Bay 3-1,
the model's pick), and verify_record, re-grading from the newest box score,
called it a win: "the mlb winners reproduce in their own line (7/16, 0 void) --
winners.json says 6/15, 1 void". Every MLB record run has been red since 10-19
and the watchdog has called the MLB Track Record BROKEN since then (#305).
✅ A void gives way to a later real grade, in both graders; a real grade is
never replaced. ✅ verify_record reads the box scores oldest first, so the
newest state wins whatever order the directory lists them in.
Everything is planted in a throwaway tree (the real 849817 times and score).

# @vacuity 🔴🔴 a void gives way to a later real grade
#   file: winners.py
#   find:     return bool(have) and have.get("state") == "void" and g.get("state") == "graded"
#   with:     return False
#
# @vacuity 🔴🔴 the builder asks a stored void again
#   file: winners.py
#   find:         if gid not in stored or stored[gid].get("state") == "void":
#   with:         if gid not in stored:
#
# @vacuity 🔴 ...and writes nothing new for a game that is still void
#   file: winners.py
#   find:             if state != "pending" and (gid not in stored or state == "graded"):
#   with:             if state != "pending":
#
# @vacuity 🔴🔴 the verifier re-checks the grade that STANDS
#   file: verify_record.py
#   find:             if _have is None or (_have.get("state") == "void" and _gr.get("state") == "graded"):
#   with:             if _have is None:
#
# @vacuity 🔴 the verifier reads the newest box score, whatever the directory order
#   file: verify_record.py
#   find:     _src = sorted(glob.glob("data/*/results/final.json.gz") if _lg == "mlb"
#   with:     _src = (glob.glob("data/*/results/final.json.gz") if _lg == "mlb"
"""
import datetime
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "mlb")
import collect as CO  # noqa: E402
import winners as W  # noqa: E402
from tcheck import ck, eq, section, shown  # noqa: E402

UTC = datetime.timezone.utc
GID = "849817"
_SUPERSEDED = getattr(W, "superseded", lambda have, g: None)
FIRST, MADE_UP = "2026-10-17T00:00:00Z", "2026-10-18T21:08:00Z"
# ⚠️ Reverses every glob in verify_record's process, so a reader that leans on
#    the directory's own order reads the OLDEST box score last.
REVERSE = ("import glob as _g\n_o = _g.glob\n"
           "_g.glob = lambda *a, **k: sorted(_o(*a, **k), reverse=True)\n")


def at(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def put(root, rel, obj):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with (gzip.open(p, "wt") if p.endswith(".gz") else open(p, "w")) as fh:
        json.dump(obj, fh)


def save(root, taken, commence, p_home):
    day, hhmm = taken[:10], taken[11:13] + taken[14:16]
    put(root, "data/%s/winner-picks/%s.json.gz" % (day, hhmm),
        {"league": "mlb", "taken_at": taken,
         "rows": [W.make_row(GID, commence, "Tampa Bay Rays", "Cleveland Guardians",
                             p_home, None, None)]})


def final(root, day, state, home=None, away=None):
    put(root, "data/%s/results/final.json.gz" % day,
        {"slate_date": day, "n_games": 1, "n_final": int(state == "Final"),
         "games": [{"gamePk": int(GID), "state": state, "score": {"home": home, "away": away},
                    "pitchers": [], "batters": []}]})


def tree():
    t = tempfile.mkdtemp(prefix="winpp-")
    put(t, "data/latest/board.json", {"games": []})
    put(t, "data/latest/mlb-game-model.json", {"slate": "2026-10-23", "games": []})
    put(t, "picks/2026-10-16.json", {"date": "2026-10-16", "kind": "gizmos-card", "picks": []})
    save(t, "2026-10-16T21:15:10Z", FIRST, 45.0)            # Tampa Bay (away)
    final(t, "2026-10-16", "Postponed")
    return t


def grade_files(t, day):
    d = os.path.join(t, "data", day, "winner-grades")
    return sorted(os.listdir(d)) if os.path.isdir(d) else []


def build(t, when):
    return W.build("mlb", root=t, when=at(when), log=lambda *a: None)["record"]


def verify(t, reverse=False):
    """The REAL verify_record.py, run in the tree -> (rc, the winners line)."""
    cwd = os.getcwd()
    try:
        os.chdir(t)
        CO.collect_record()
    finally:
        os.chdir(cwd)
    for f in ("verify_record.py", "collect.py", "record_grader.py"):
        shutil.copy(os.path.join(ROOT, f), t)
    env = dict(os.environ, PYTHONUTF8="1")
    if reverse:
        os.makedirs(os.path.join(t, "_rev"), exist_ok=True)
        open(os.path.join(t, "_rev", "sitecustomize.py"), "w").write(REVERSE)
        env["PYTHONPATH"] = os.path.join(t, "_rev")
    p = subprocess.run([sys.executable, "verify_record.py"], cwd=t, capture_output=True,
                       text=True, env=env, timeout=600)
    line = next((ln.strip() for ln in p.stdout.splitlines() if "mlb winners reproduce" in ln),
                (p.stdout + p.stderr)[-300:])
    return p.returncode, line


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 849817, REPLAYED: VOID WHILE POSTPONED, GRADED ONCE IT IS PLAYED")
# ══════════════════════════════════════════════════════════════════════
t = tree()
try:
    eq(build(t, "2026-10-17T10:05:28Z"), {"w": 0, "l": 0, "n": 0, "pct": None, "voids": 1},
       "10-17 10:05Z: postponed, so a VOID (unchanged)")
    save(t, "2026-10-18T11:13:36Z", MADE_UP, 55.0)          # Cleveland
    save(t, "2026-10-18T14:03:31Z", MADE_UP, 48.0)          # Tampa Bay
    save(t, "2026-10-18T20:04:59Z", MADE_UP, 47.0)          # Tampa Bay: the last before 21:08
    final(t, "2026-10-18", "Final", home=1, away=3)
    eq(build(t, "2026-10-19T05:57:00Z"), {"w": 1, "l": 0, "n": 1, "pct": 100.0, "voids": 0},
       "🔴🔴 10-19: played 10-18 under the same id, so GRADED from the final, Tampa Bay 3-1 "
       "(the pick saved last before 21:08Z)")
    _grades = grade_files(t, "2026-10-19")
    eq(build(t, "2026-10-19T08:00:00Z"), {"w": 1, "l": 0, "n": 1, "pct": 100.0, "voids": 0},
       "   ...and it stays graded on the next run")
    eq(grade_files(t, "2026-10-19"), _grades,
       "   ...with no new grade written for it (graded once)")
    _rc, _line = verify(t)
    ck("🔴🔴 verify_record re-derives the same record and passes",
       _rc == 0 and "(1/1, 0 void)" in _line, shown(_line))
    _rc, _line = verify(t, reverse=True)
    ck("🔴 ...whatever order the directory lists the box scores in",
       _rc == 0 and "(1/1, 0 void)" in _line, shown(_line))
finally:
    shutil.rmtree(t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("2. ⛔ NOTHING ELSE MOVES: A REAL GRADE STANDS, A VOID STAYS VOID")
# ══════════════════════════════════════════════════════════════════════
t = tree()
try:
    build(t, "2026-10-17T10:05:28Z")
    eq(build(t, "2026-10-19T05:57:00Z"), {"w": 0, "l": 0, "n": 0, "pct": None, "voids": 1},
       "🔴 a postponed game never played again stays one VOID")
    eq(grade_files(t, "2026-10-19"), [],
       "   ...and no second void is written for it")
    _rc, _line = verify(t)
    ck("   ...and verify_record agrees (0/0, 1 void)", _rc == 0 and "(0/0, 1 void)" in _line,
       shown(_line))
finally:
    shutil.rmtree(t, ignore_errors=True)

t = tree()
try:
    final(t, "2026-10-16", "Final", home=2, away=5)          # played as scheduled
    eq(build(t, "2026-10-17T10:05:28Z")["w"], 1, "a game played as scheduled: graded won")
    put(t, "data/2026-10-18/winner-grades/0100.json.gz",
        {"league": "mlb", "grades": [{"game_id": GID, "state": "void", "won": None}]})
    put(t, "data/2026-10-18/winner-grades/0200.json.gz",
        {"league": "mlb", "grades": [{"game_id": GID, "state": "graded", "won": False}]})
    eq(build(t, "2026-10-19T05:57:00Z"), {"w": 1, "l": 0, "n": 1, "pct": 100.0, "voids": 0},
       "⛔ a real grade is never replaced, by a later void or a later, different grade")
    eq(_SUPERSEDED({"state": "graded", "won": True}, {"state": "graded", "won": False}), False,
       "   superseded(): graded never gives way")
    eq(_SUPERSEDED({"state": "void"}, {"state": "void"}), False,
       "   ...and a void never gives way to another void")
finally:
    shutil.rmtree(t, ignore_errors=True)
