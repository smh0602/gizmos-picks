#!/usr/bin/env python3
"""A CHANGE TO HOW THE WINNERS ARE GRADED TAKES EFFECT IN THE PASS THAT CHECKS IT.

🔴 WHAT HAPPENED `[2026-10-23]`. PR #310 changed how winners.py grades the Game
Lines tab (a void gives way to a later real grade: 849817, postponed 10-16,
played 10-18). It merged at 23:37Z. The next MLB pass (collect 40040807226)
found everything in contract and ran no mode, so winners.json was still the
file the OLD rule wrote, and verify_record, re-grading with the NEW rule,
failed it: "the mlb winners reproduce in their own line (7/16, 0 void) --
winners.json says 6/15, 1 void". It stayed red until a mode rebuilt the file.
record.json had the same failure on 09-25 and was fixed then
(record_grader.py, test_record_grader.py); winners.json had no stamp.

✅ THE FIX, THE CLASS: winners.build stamps `grader` =
record_grader.winners_fingerprint (the grading code, `winners.graded`, and
everything it reaches IN ANY MODULE: collect.VOID_STATES for MLB,
fb_ledger.schedule_by_id for football, daystore). verify_record rebuilds a
winners.json whose stamp is not the winners.py beside it, in every league,
then verifies.

⛔ AND IT MUST NOT HIDE A REAL DISAGREEMENT: §4 plants the same stale files
stamped CURRENT; they stay red and untouched.

§2 REPLAYS THE INCIDENT, IT DOES NOT SKETCH IT: the stale files are built by
the real builder with #310's three lines put back, then verified by today's
code in the same tree. MLB is 849817's own shape (postponed, then played);
football's is the same shape through its own finals (a 20-20 final corrected
to 20-23), since a football void is a tie.

# @vacuity 🔴🔴 without the rebuild, the old grader's winners.json fails the new verifier
#   file: verify_record.py
#   find: if _wj.get("grader") != _WNOW:
#   with: if False:
#
# @vacuity ⛔ a verifier that ALWAYS rebuilds hides a real disagreement
#   file: verify_record.py
#   find: if _wj.get("grader") != _WNOW:
#   with: if True:
#
# @vacuity 🔴 the builder stamps which grading code wrote the file
#   file: winners.py
#   find: "grader": record_grader.winners_fingerprint(os.path.abspath(__file__)),
#   with: "grader": None,
#
# @vacuity 🔴 the fingerprint follows the grading into the other modules it reads
#   file: record_grader.py
#   find: queue.extend(_foreign(p, defs, mod_imports, seen))
#   with: pass
#
# @vacuity ⛔ a module it cannot find is "cannot tell", never "it matches"
#   file: record_grader.py
#   find: elif top not in sys.stdlib_module_names:
#   with: elif False:
#
# @vacuity ✅ the stamp is the GRADING, not the whole builder (a display edit costs no rebuild)
#   file: record_grader.py
#   find: WINNERS = "graded"
#   with: WINNERS = "build"
#
# @vacuity ⛔ a rebuild that fails is loud
#   file: verify_record.py
#   find: ck(f"the stale {_lg} winners could be rebuilt", False,
#   with: ck(f"the stale {_lg} winners could be rebuilt", True,
"""
import glob
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
os.environ.setdefault("LEAGUE", "mlb")
import collect as CO  # noqa: E402
import record_grader as G  # noqa: E402
import winners as W  # noqa: E402
from tcheck import ck, note, section, shown  # noqa: E402

_WFP = getattr(G, "winners_fingerprint", None)
SRC = open(os.path.join(REPO, "winners.py"), encoding="utf-8").read()

# #310's three lines, and the lines they replaced (the old grader).
POST_310 = (
    ('    return bool(have) and have.get("state") == "void" and g.get("state") == "graded"',
     "    return False"),
    ('        if gid not in stored or stored[gid].get("state") == "void":',
     "        if gid not in stored:"),
    ('            if state != "pending" and (gid not in stored or state == "graded"):',
     '            if state != "pending":'),
)
STAMP = '"grader": record_grader.winners_fingerprint(os.path.abspath(__file__)),'


def edit(src, old, new, where="winners.py"):
    n = src.count(old)
    ck(n == 1, "  (the edit site `%s` is in %s once)" % (old.strip()[:50], where),
       "" if n == 1 else "found %d -- the probe would not be testing what it says" % n)
    return src.replace(old, new)


def old_builder(stamped):
    """winners.py with #310 put back: the grading as it was before 10-23.
    Unstamped is every winners.json on main before this change."""
    s = SRC
    for new, old in POST_310:
        s = edit(s, new, old)
    return s if stamped else edit(s, STAMP, "")


def fp(path):
    try:
        return _WFP(path)
    except Exception as e:      # noqa: BLE001 -- a probe, reported as a failed check
        return "%s: %s" % (type(e).__name__, e)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE STAMP FOLLOWS THE GRADING, INTO EVERY MODULE IT READS, AND NOTHING ELSE")
# ══════════════════════════════════════════════════════════════════════
F = tempfile.mkdtemp(prefix="wgfp-")
try:
    for f in glob.glob(os.path.join(REPO, "*.py")):
        shutil.copy(f, F)
    BASE = fp(os.path.join(REPO, "winners.py")) if _WFP else None
    ck(_WFP is not None and BASE == fp(os.path.join(F, "winners.py")) and len(BASE or "") == 16,
       "winners.py's grading has a fingerprint, the same in a copy of the repo",
       "record_grader.winners_fingerprint -> %r" % (BASE,))
    try:
        _cov = set(G.closure(os.path.join(REPO, "winners.py"), G.WINNERS, follow=True))
    except Exception as e:      # noqa: BLE001
        _cov = {"%s: %s" % (type(e).__name__, e)}
    _need = {"graded", "frozen", "stored_grades", "superseded", "grade", "finals",
             "collect.VOID_STATES", "fb_ledger.schedule_by_id", "daystore.archive"}
    ck(_need <= _cov, "it covers the grading and what it reads in collect, fb_ledger and daystore",
       "missing %s; covers %s" % (sorted(_need - _cov), sorted(_cov)))

    def probe(fname, old, new):
        p = os.path.join(F, fname)
        cur = open(p, encoding="utf-8").read()
        open(p, "w", encoding="utf-8").write(edit(cur, old, new, fname))
        try:
            return fp(os.path.join(F, "winners.py"))
        finally:
            open(p, "w", encoding="utf-8").write(cur)

    for what, fname, old, new in (
            ("#310's own change (superseded)",) + ("winners.py",) + POST_310[0],
            ("the void asked again (graded)",) + ("winners.py",) + POST_310[1],
            ("a tie no longer a void (grade)", "winners.py",
             '    if st in void_states or (st == "Final" and h is not None and h == a):',
             "    if st in void_states:"),
            ("the pick graded: a save after the start (frozen)", "winners.py",
             '            if t < (r.get("commence") or "") and t > best.get(r["game_id"], ("",))[0]:',
             '            if t > best.get(r["game_id"], ("",))[0]:'),
            ("the tally", "winners.py",
             '                "voids": sum(1 for x in g if x["state"] == "void")}',
             '                "voids": 0}'),
            ("MLB's void states (collect.VOID_STATES, another module)", "collect.py",
             'VOID_STATES = frozenset({"Postponed", "Cancelled"})',
             'VOID_STATES = frozenset({"Postponed", "Cancelled", "Suspended"})'),
            ("football's finals (fb_ledger.schedule_by_id, another module)", "fb_ledger.py",
             "    for s in (2025, 2026):", "    for s in (2026,):"),
            ("where a grade is filed, so which stands (daystore, another module)", "daystore.py",
             'return os.path.join(data, day, kind, hhmm + ".json.gz")',
             'return os.path.join(data, kind, day, hhmm + ".json.gz")')):
        ck(probe(fname, old, new) != BASE, "🔴 %s -> a DIFFERENT fingerprint" % what,
           "⛔ a grading change the stamp cannot see is a stale winners.json verified as current")
    for what, fname, old, new in (
            ("a comment in the grading", "winners.py",
             "    fz = frozen(data)\n", "    fz = frozen(data)  # the picks\n"),
            ("the grading's docstring", "winners.py",
             "    tally -> (frozen picks, the record).", "    tally -> (the frozen picks, the record)."),
            ("the page's sim share (display)", "winners.py",
             "sim_win=int(round(100 * w))", "sim_win=int(100 * w)"),
            ("the tab's rule text (display)", "winners.py",
             "frozen at the start and graded once from the final score.",
             "frozen at the start, graded once from the final score."),
            ("a collect.py line the grading never reaches", "collect.py",
             'log(f"schedule: {len(games)} games")', 'log(f"schedule: {len(games)} game(s)")'),
            ("an fb_ledger.py line the grading never reaches", "fb_ledger.py",
             'LEDGER_FROM = "2026-09-24"', 'LEDGER_FROM = "2026-09-25"'),):
        ck(probe(fname, old, new) == BASE, "✅ %s -> the SAME fingerprint (no needless rebuild)" % what)
    os.remove(os.path.join(F, "fb_ledger.py"))
    _gone = fp(os.path.join(F, "winners.py"))
    ck(_gone.startswith("LookupError"),
       "⛔ a module the grading reads that is not there -> it RAISES (\"cannot tell\"), never a "
       "quieter fingerprint", "got %r" % _gone)
finally:
    shutil.rmtree(F, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
# The tree: every module, and per league one game, picked away (45%), saved
# 10-16 21:15Z before a 10-17 00:00Z start. MLB: postponed 10-16, played
# 10-18 1-3. Football: final 20-20 (a void), corrected to 20-23.
# ══════════════════════════════════════════════════════════════════════
LEAGUES = (("mlb", "data", "849817"), ("nfl", "data/nfl", "401770007"),
           ("ncaaf", "data/ncaaf", "401770008"))
START = "2026-10-17T00:00:00Z"
DRIVER = ("import datetime, sys\nimport winners\n"
          "w = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%dT%H:%M:%SZ')"
          ".replace(tzinfo=datetime.timezone.utc)\n"
          "winners.build(sys.argv[1], when=w, log=lambda *a: None)\n")


def put(root, rel, obj):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with (gzip.open(p, "wt") if p.endswith(".gz") else open(p, "w")) as fh:
        json.dump(obj, fh)


def finals(t, lg, dd, gid, played):
    if lg == "mlb":
        put(t, "data/2026-10-16/results/final.json.gz",
            {"slate_date": "2026-10-16", "n_games": 1, "n_final": 0, "games": [
                {"gamePk": int(gid), "state": "Postponed", "score": {}, "pitchers": [], "batters": []}]})
        if played:
            put(t, "data/2026-10-18/results/final.json.gz",
                {"slate_date": "2026-10-18", "n_games": 1, "n_final": 1, "games": [
                    {"gamePk": int(gid), "state": "Final", "score": {"home": 1, "away": 3},
                     "pitchers": [], "batters": []}]})
    else:
        put(t, dd + "/latest/schedule-2026.json.gz", {"games": [
            {"id": gid, "final": True, "home_score": 20, "away_score": 23 if played else 20}]})


def env(lg):
    # ⛔ KEYS BLANKED: nothing here may spend (test_collect_subprocess.py).
    return dict(os.environ, LEAGUE=lg, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1",
                ODDS_API_KEY="", CFBD_API_KEY="")


def run(t, lg, *argv):
    p = subprocess.run([sys.executable, "-B"] + list(argv), cwd=t, capture_output=True,
                       text=True, timeout=600, env=env(lg))
    return p.returncode, p.stdout + p.stderr


def tree():
    t = tempfile.mkdtemp(prefix="wgr-")
    for f in glob.glob(os.path.join(REPO, "*.py")):
        shutil.copy(f, t)
    put(t, "data/latest/board.json", {"games": []})
    put(t, "data/latest/mlb-game-model.json", {"slate": "2026-10-16", "games": []})
    put(t, "picks/2026-10-16.json", {"date": "2026-10-16", "kind": "gizmos-card", "picks": []})
    for lg, dd, gid in LEAGUES:
        put(t, dd + "/2026-10-16/winner-picks/2115.json.gz",
            {"league": lg, "taken_at": "2026-10-16T21:15:10Z",
             "rows": [W.make_row(gid, START, "Away " + lg, "Home " + lg, 45.0, None, None)]})
        finals(t, lg, dd, gid, played=False)
    cwd = os.getcwd()
    try:
        os.chdir(t)
        CO.collect_record()                 # the props record beside it, current stamp
    finally:
        os.chdir(cwd)
    return t


def stale(stamped):
    """The 10-23 shape: the old grader builds the void, the game is then
    played (or corrected), the old grader builds again and keeps the void."""
    t = tree()
    wp = os.path.join(t, "winners.py")
    open(wp, "w", encoding="utf-8").write(old_builder(stamped))
    bad = []
    try:
        for lg, dd, gid in LEAGUES:
            rc1, o1 = run(t, lg, "-c", DRIVER, lg, "2026-10-17T10:05:28Z")
            finals(t, lg, dd, gid, played=True)
            rc2, o2 = run(t, lg, "-c", DRIVER, lg, "2026-10-19T05:57:00Z")
            if rc1 or rc2:
                bad.append((lg, o1[-300:], o2[-300:]))
    finally:
        open(wp, "w", encoding="utf-8").write(SRC)
    return t, bad


def wj(t, dd):
    return json.load(open(os.path.join(t, *dd.split("/"), "latest", "winners.json")))


def line(out, lg):
    return next((ln.strip() for ln in out.splitlines() if "%s winners reproduce" % lg in ln),
                "(no %s winners line) " % lg + out[-300:])


# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 THE INCIDENT, REPLAYED IN EVERY LEAGUE: THE OLD RULE'S FILE, TODAY'S VERIFIER")
# ══════════════════════════════════════════════════════════════════════
for stamped, how in ((False, "unstamped, as every winners.json on main before this change"),
                     (True, "stamped with the OLD grading code's fingerprint")):
    t, bad = stale(stamped)
    try:
        ck(not bad, "the old builder ran in every league (%s)" % how, shown(str(bad)))
        _before = {lg: wj(t, dd) for lg, dd, _ in LEAGUES}
        ck(all(_before[lg]["record"] == {"w": 0, "l": 0, "n": 0, "pct": None, "voids": 1}
               and _before[lg].get("grader") != BASE for lg, _, _ in LEAGUES),
           "  the planted files are the real old output: the game still a VOID, not today's stamp",
           str({lg: (b["record"], b.get("grader")) for lg, b in _before.items()}))
        rc, out = run(t, "mlb", "verify_record.py")
        ck(rc == 0, "🔴🔴 verify_record.py is GREEN: it rebuilt each league's winners, then verified "
                    "them (%s)" % how,
           "" if rc == 0 else "⛔ this is collect 40040807226: " + shown(out[-900:]))
        for lg, dd, _ in LEAGUES:
            _now = wj(t, dd)
            _ok = ("REBUILD the %s winners.json" % lg in out and "(1/1, 0 void)" in line(out, lg)
                   and _now.get("grader") == BASE
                   and _now["record"] == {"w": 1, "l": 0, "n": 1, "pct": 100.0, "voids": 0})
            ck(_ok, "  %s: rebuilt, graded from the real final (1/1, 0 void), stamped current" % lg,
               "" if _ok else shown("%s | grader=%r record=%s"
                                    % (line(out, lg), _now.get("grader"), _now["record"])))
    finally:
        shutil.rmtree(t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("3. ✅ A CURRENT FILE IS NEVER REBUILT")
# ══════════════════════════════════════════════════════════════════════
t = tree()
try:
    for lg, dd, gid in LEAGUES:
        run(t, lg, "-c", DRIVER, lg, "2026-10-17T10:05:28Z")
        finals(t, lg, dd, gid, played=True)
        run(t, lg, "-c", DRIVER, lg, "2026-10-19T05:57:00Z")
    _before = {dd: open(os.path.join(t, *dd.split("/"), "latest", "winners.json")).read()
               for _, dd, _ in LEAGUES}
    rc, out = run(t, "mlb", "verify_record.py")
    _ok = (rc == 0 and "REBUILD the" not in out
           and all("(1/1, 0 void)" in line(out, lg) for lg, _, _ in LEAGUES))
    ck(_ok, "today's builder's files: verified as they are, no rebuild",
       "" if _ok else shown(out[-600:]))
    ck(all(open(os.path.join(t, *dd.split("/"), "latest", "winners.json")).read() == b
           for dd, b in _before.items()), "  ...and not one of them was touched")
finally:
    shutil.rmtree(t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("4. ⛔ THE CONTROL: THE SAME STALE FILES STAMPED CURRENT STAY RED")
# ══════════════════════════════════════════════════════════════════════
t, bad = stale(stamped=True)
try:
    for lg, dd, _ in LEAGUES:
        p = os.path.join(t, *dd.split("/"), "latest", "winners.json")
        d = json.load(open(p))
        d["grader"] = BASE
        json.dump(d, open(p, "w"))
    _before = {dd: open(os.path.join(t, *dd.split("/"), "latest", "winners.json")).read()
               for _, dd, _ in LEAGUES}
    rc, out = run(t, "mlb", "verify_record.py")
    _ok = (rc != 0 and "REBUILD the" not in out
           and all("FAIL the %s winners reproduce" % lg in out for lg, _, _ in LEAGUES))
    ck(_ok, "⛔ a winners.json stamped CURRENT that disagrees is still RED in every league, and "
            "not rebuilt",
       "" if _ok else "🔴 if this passes the rebuild is hiding a real builder/verifier split. "
       "rc=%d %s" % (rc, shown(out[-600:])))
    ck(all(open(os.path.join(t, *dd.split("/"), "latest", "winners.json")).read() == b
           for dd, b in _before.items()), "  ...and no file was touched")
finally:
    shutil.rmtree(t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("5. ⛔ A REBUILD THAT FAILS IS LOUD, NOT A PASS")
# ══════════════════════════════════════════════════════════════════════
t, bad = stale(stamped=False)
try:
    put(t, "data/latest/mlb-game-model.json", {"slate": "2026-10-16", "games": [{"game_pk": 1}]})
    rc, out = run(t, "mlb", "verify_record.py")
    _ok = (rc != 0 and "FAIL the stale mlb winners could be rebuilt" in out
           and "(1/1, 0 void)" in line(out, "nfl"))
    ck(_ok, "the MLB rebuild crashed: the run is RED and says so; the other leagues are still "
            "verified", "" if _ok else "rc=%d %s" % (rc, shown(out[-600:])))
finally:
    shutil.rmtree(t, ignore_errors=True)

note("⛔ WHAT THIS DOES NOT CLAIM: that the grading is right. That is verify_record.py's own "
     "re-derivation (test_winners_postponed.py, test_game_lines_page.py), left untouched.")
