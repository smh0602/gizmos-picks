#!/usr/bin/env python3
"""A GRADING-RULE CHANGE MUST NOT TURN A RUN RED ON A RECORD THE OLD RULE WROTE.

🔴 WHAT HAPPENED `[2026-09-25]`. PR #166 changed the MLB grading rule (a
postponed game is a void, not a day held back). `record.json` on main had
been written by the OLD rule at 09-24 12:05Z, and `verify_record.py`, now
re-grading with the NEW rule, failed collect runs #1803, #1813 and
#1816-#1819 until the 12:08Z rebuild. Measured: that exact file, verified
by today's code, fails 5 checks (overall 923/1499 vs 871/1411, ...).

✅ THE FIX: `collect_record()` stamps `record_grader.fingerprint` into the
file; `verify_record.py` rebuilds a record whose stamp differs from the
collect.py beside it, THEN verifies.

⛔ AND THE FIX MUST NOT BECOME A WAY TO HIDE A REAL DISAGREEMENT. §3's
control plants the same stale content under the CURRENT stamp: it must
stay red, and the file must not be touched.

§3 REPLAYS THE INCIDENT, IT DOES NOT SKETCH IT: the stale record is built
by the real collector with `slate_settled` put back to its pre-#166 line,
then verified by today's code in the same tree.

# @vacuity without the rebuild, the old rule's record fails the new verifier
#   file: verify_record.py
#   find: if REC.get("grader") != _NOW:
#   with: if False:
#
# @vacuity a verifier that ALWAYS rebuilds hides a real disagreement
#   file: verify_record.py
#   find: if REC.get("grader") != _NOW:
#   with: if True:
#
# @vacuity the builder must stamp which grader wrote the file
#   file: collect.py
#   find: "grader": record_grader.fingerprint(os.path.abspath(__file__)),
#   with: "grader": None,
#
# @vacuity the fingerprint must follow the grader into the helpers it calls
#   file: record_grader.py
#   find: todo.extend(n.id for n in ast.walk(node) if isinstance(n, ast.Name))
#   with: pass
#
# @vacuity a docstring edit must not force a rebuild
#   file: record_grader.py
#   find: tree = _strip_docstrings(ast.parse(open(path, encoding="utf-8").read()))
#   with: tree = ast.parse(open(path, encoding="utf-8").read())
"""
import glob
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, note, section
import record_grader as G

REPO = os.path.dirname(os.path.abspath(__file__))
BUILDER = os.path.join(REPO, "collect.py")
SRC = open(BUILDER, encoding="utf-8").read()

# The rule #166 replaced, and the line that replaced it (collect.py).
NEW_RULE = "return n_final + n_void == len(games), n_void"
OLD_RULE = "return n_final == len(games), n_void"


def fp_of(text):
    """Fingerprint of a collect.py whose source is `text`."""
    d = tempfile.mkdtemp()
    try:
        p = os.path.join(d, "collect.py")
        open(p, "w", encoding="utf-8").write(text)
        return G.fingerprint(p)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def edit(old, new):
    n = SRC.count(old)
    ck(n == 1, "  (the edit site `%s` is in collect.py once)" % old.strip()[:50],
       "" if n == 1 else "found %d — the probe below would not be testing what it says" % n)
    return SRC.replace(old, new)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE FINGERPRINT FOLLOWS THE GRADER, NOT A LIST OF NAMES")
# ══════════════════════════════════════════════════════════════════════
BASE = G.fingerprint(BUILDER)
_cov = set(G.closure(BUILDER))
ck(len(BASE) == 16 and {"collect_record", "slate_settled", "_won",
                         "VOID_STATES", "BATTER_RESULT"} <= _cov,
   "the grader and the helpers it reaches are covered (%d names)" % len(_cov),
   "covers %s" % sorted(_cov))
ck(fp_of(SRC) == BASE, "same source -> same fingerprint")
for what, old, new in (
        ("#166's own change (slate_settled)", NEW_RULE, OLD_RULE),
        ("a void state added (VOID_STATES)", 'VOID_STATES = frozenset({"Postponed", "Cancelled"})',
         'VOID_STATES = frozenset({"Postponed", "Cancelled", "Suspended"})'),
        ("a push graded as a win (_won)",
         'return (val > line) if side == "over" else (val < line)',
         'return (val >= line) if side == "over" else (val < line)'),
        ("a market's stat changed (BATTER_RESULT)",
         '"batter_home_runs":      lambda b: b.get("hr"),',
         '"batter_home_runs":      lambda b: b.get("tb"),')):
    ck(fp_of(edit(old, new)) != BASE,
       "🔴 %s -> a DIFFERENT fingerprint" % what,
       "⛔ a grading change the stamp cannot see is a stale record verified as current")
_doc = '    """(settled, n_void) for one stored results file.'
ck(fp_of(edit(_doc, _doc.replace("one stored", "one STORED"))) == BASE
   and fp_of(edit("def _won(val, line, side):\n",
                  "def _won(val, line, side):\n    # a comment\n")) == BASE,
   "✅ a docstring or comment edit -> the SAME fingerprint (no needless rebuild)")
ck(fp_of(edit('    d = now().strftime("%Y-%m-%d")\n    body, _ = get(',
              '    d = now().strftime("%Y-%m-%d") \n    body, _ = get(')) == BASE
   and fp_of(edit('log(f"schedule: {len(games)} games")',
                  'log(f"schedule: {len(games)} game(s)")')) == BASE,
   "✅ a change the grader never reaches (collect_schedule) -> the SAME fingerprint")

# ══════════════════════════════════════════════════════════════════════
# the tree: every top-level module (collect.py imports several), one card,
# one results file with a Final game and a Postponed one.
# ══════════════════════════════════════════════════════════════════════
DAY = "2026-09-22"
CARD = {"date": DAY, "kind": "gizmos-card", "picks": [
    {"pid": 11, "market": "strikeouts", "side": "over", "line": 5.5,
     "kind": "pitcher", "pitcher": "Final Pitcher", "game": "LAA @ ATH"},
    {"pid": 12, "market": "batter_hits", "side": "under", "line": 0.5,
     "kind": "hitter", "player": "Final Hitter", "game": "LAA @ ATH"},
    {"pid": 21, "market": "strikeouts", "side": "under", "line": 6.5,
     "kind": "pitcher", "pitcher": "Rained Out", "game": "TOR @ BAL"}]}
RESULTS = {"slate_date": DAY, "n_games": 2, "n_final": 1, "games": [
    {"gamePk": 1, "state": "Final", "away": "Los Angeles Angels", "home": "Athletics",
     "pitchers": [{"id": 11, "started": True, "k": 7, "outs": 18}],
     "batters": [{"id": 12, "H": 1, "tb": 1, "hr": 0, "r": 0, "rbi": 0}]},
    {"gamePk": 2, "state": "Postponed", "away": "Toronto Blue Jays",
     "home": "Baltimore Orioles", "pitchers": [], "batters": []}]}


def tree():
    t = tempfile.mkdtemp()
    for f in glob.glob(os.path.join(REPO, "*.py")):
        shutil.copy(f, t)
    for d in ("picks", "data/%s/results" % DAY, "data/latest"):
        os.makedirs(os.path.join(t, d), exist_ok=True)
    json.dump(CARD, open(os.path.join(t, "picks", DAY + ".json"), "w"))
    with gzip.open(os.path.join(t, "data", DAY, "results", "final.json.gz"), "wt") as fh:
        json.dump(RESULTS, fh)
    return t


def sh(t, *argv):
    p = subprocess.run([sys.executable, "-B"] + list(argv), cwd=t, capture_output=True,
                       text=True, timeout=300, env=dict(os.environ, LEAGUE="mlb"))
    return p.returncode, p.stdout + p.stderr


def rec(t):
    return json.load(open(os.path.join(t, "data", "latest", "record.json")))


def build_with_old_rule(t):
    """The record exactly as the pre-#166 collector wrote it."""
    cp = os.path.join(t, "collect.py")
    cur = open(cp, encoding="utf-8").read()
    open(cp, "w", encoding="utf-8").write(cur.replace(NEW_RULE, OLD_RULE))
    try:
        rc, out = sh(t, "collect.py", "record", "converge-off")
    finally:
        open(cp, "w", encoding="utf-8").write(cur)
    return rc, out


# ══════════════════════════════════════════════════════════════════════
section("2. THE BUILDER STAMPS WHICH GRADER WROTE THE FILE")
# ══════════════════════════════════════════════════════════════════════
t = tree()
try:
    rc, out = sh(t, "collect.py", "record", "converge-off")
    ck(rc == 0 and rec(t).get("grader") == BASE,
       "record.json carries the fingerprint of the collect.py that built it",
       "rc=%d grader=%r want %s %s" % (rc, rec(t).get("grader") if rc == 0 else None,
                                       BASE, out[-300:] if rc else ""))
finally:
    shutil.rmtree(t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 THE INCIDENT, REPLAYED: THE OLD RULE'S RECORD, TODAY'S VERIFIER")
# ══════════════════════════════════════════════════════════════════════
t = tree()
try:
    rc, out = build_with_old_rule(t)
    stale = rec(t)
    ck(rc == 0 and DAY not in [d["date"] for d in stale.get("by_day", [])]
       and stale.get("grader") not in (None, BASE),
       "the planted record is the real pre-#166 output: the day HELD BACK, "
       "stamped with the old grader",
       "rc=%d by_day=%s grader=%r" % (rc, stale.get("by_day"), stale.get("grader")))
    rc, out = sh(t, "verify_record.py")
    now = rec(t)
    ck(rc == 0, "🔴🔴 verify_record.py is GREEN: it rebuilt the record, then verified it",
       "" if rc == 0 else "⛔ this is runs #1813 and #1816-#1819: " + out[-700:])
    ck("REBUILD" in out and now.get("grader") == BASE
       and DAY in [d["date"] for d in now.get("by_day", [])],
       "  ...and the file on disk is now the CURRENT grader's: stamped, day graded",
       "grader=%r by_day=%s" % (now.get("grader"), now.get("by_day")))
finally:
    shutil.rmtree(t, ignore_errors=True)

# ⛔ THE CONTROL. Same stale content, but stamped as if the CURRENT grader
#    wrote it — i.e. a builder and verifier that truly disagree.
t = tree()
try:
    build_with_old_rule(t)
    p = os.path.join(t, "data", "latest", "record.json")
    r = rec(t)
    r["grader"] = BASE
    json.dump(r, open(p, "w"))
    before = open(p).read()
    rc, out = sh(t, "verify_record.py")
    ck(rc != 0 and "REBUILD" not in out,
       "⛔ a record stamped CURRENT that disagrees is still RED, and is not rebuilt",
       "🔴 if this passes the rebuild is hiding a real builder/verifier split. rc=%d" % rc)
    ck(open(p).read() == before, "  ...and the file was not touched")
finally:
    shutil.rmtree(t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("4. EVERY RECORD WRITTEN BEFORE THIS CHANGE CARRIES NO STAMP")
# ══════════════════════════════════════════════════════════════════════
t = tree()
try:
    build_with_old_rule(t)
    p = os.path.join(t, "data", "latest", "record.json")
    r = rec(t)
    r.pop("grader", None)
    json.dump(r, open(p, "w"))
    rc, out = sh(t, "verify_record.py")
    ck(rc == 0 and rec(t).get("grader") == BASE,
       "an unstamped record is rebuilt once and verified (the first run after merge)",
       "" if rc == 0 else "rc=%d %s" % (rc, out[-400:]))
finally:
    shutil.rmtree(t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("5. ⛔ A REBUILD THAT FAILS IS LOUD, NOT A PASS")
# ══════════════════════════════════════════════════════════════════════
t = tree()
try:
    build_with_old_rule(t)
    # the stored box score the rebuild must read, corrupted
    open(os.path.join(t, "data", DAY, "results", "final.json.gz"), "wb").write(b"not gzip")
    rc, out = sh(t, "verify_record.py")
    ck(rc != 0 and "could not be rebuilt" in out,
       "a failed rebuild exits non-zero and says why",
       "rc=%d" % rc if rc != 0 and "could not be rebuilt" in out else "rc=%d %s" % (rc, out[-300:]))
finally:
    shutil.rmtree(t, ignore_errors=True)

note("⛔ WHAT THIS DOES NOT CLAIM: that the current grader is right. That is "
     "verify_record.py's own re-grade, which this change leaves untouched.")
