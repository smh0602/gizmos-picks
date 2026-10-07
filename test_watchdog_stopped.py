#!/usr/bin/env python3
"""THE WATCHDOG SEES WHAT THE CLAUDE AUDITS SAW. `[Sam, 2026-10-07]`

*"the website should do all of them themselves"*: Sam is turning off every
scheduled Claude task and the self-repair workflow. So the repo itself must
notice: a league that stopped updating, a run list too old to judge from, a
re-check (verify_record) that failed, and it must not alert because a
workflow Sam switched off no longer fires. Planted trees, pinned clocks.

# @vacuity 🔴 a stopped league is reported for each of the three leagues
#   file: watchdog.py
#   find:     for lg, d in DATA.items():          # every league, whichever league's run this is
#   with:     for lg, d in list(DATA.items())[:1]:          # every league, whichever league's run this is
#
# @vacuity 🔴 ...BROKEN when a card is past due
#   file: watchdog.py
#   find:         (rep.bad if card else rep.warn)(
#   with:         rep.warn(
#
# @vacuity 🔴 inside the grace it is not reported
#   file: watchdog.py
#   find:     grace = datetime.timedelta(minutes=STOPPED_GRACE_MIN)
#   with:     grace = datetime.timedelta(0)
#
# @vacuity 🔴 a healthy league 22 minutes past a deadline is silent: only rows the file never judged
#   file: watchdog.py
#   find:                 and _when(r["due_at"]) > built and now - _when(r["due_at"]) > grace]
#   with:                 and now - _when(r["due_at"]) > grace]
#
# @vacuity 🔴 a stale run list is named as stale and gives no verdict
#   file: runs_report.py
#   find:     if born is None or born < due:
#   with:     if born is None:
#
# @vacuity 🔴 a failed record re-check appears in health.json
#   file: watchdog.py
#   find:     p = os.path.join(ROOT, "data", "latest", "record-verify-failure.txt")
#   with:     p = os.path.join(ROOT, "data", "latest", "record-verify-failure.off")
#
# @vacuity 🔴 ...naming the check that failed
#   file: verify_record.py
#   find:                   + "".join("FAIL %s\n" % f for f in fails))
#   with:                   + "")
#
# @vacuity 🔴 ...and clears when it passes
#   file: verify_record.py
#   find: elif os.path.exists(_MARK):
#   with: elif False:
#
# @vacuity 🔴 a workflow Sam switched off is not a workflow that must show runs
#   file: runs_report.py
#   find:         if os.path.basename(p) in DISABLED:
#   with:         if False:
#
# @vacuity 🔴 ...nor one whose crons must fire
#   file: runs_report.py
#   find:         if os.path.basename(p) in DISABLED:   # no fire is owed
#   with:         if False:   # no fire is owed
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
import collect as C  # noqa: E402
import runs_report as R  # noqa: E402
import watchdog as W  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

UTC = datetime.timezone.utc
T = lambda s: datetime.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)  # noqa: E731


def put(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with (gzip.open(p, "wt") if p.endswith(".gz") else open(p, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


def stopped(built, at):
    """Each league's freshness.json written at `built` (ok, nothing built since);
    the watchdog asked at `at`. -> {league: (severity, what)}"""
    t, cwd = tempfile.mkdtemp(prefix="stopped-"), os.getcwd()
    saved = W.ROOT
    try:
        # ⚠️ run from inside the tree: football's card row names `picks/...` relative
        #    to the working directory, as the watchdog does from the repo root.
        os.chdir(t)
        for d in W.DATA.values():
            b = built[d] if isinstance(built, dict) else built
            put(t, os.path.join(d, "latest", "freshness.json"), {"built_at": b, "ok": True, "artifacts": []})
            # a props board, as on a game day: football's card rows exist only with one
            put(t, os.path.join(d, "latest", "props.json.gz"), {"pulled_at": b, "games": []})
        W.ROOT = t
        rep = W.Report()
        W.check_stopped_league(rep, T(at))
        return {i["key"].split(":")[1]: (i["severity"], i["what"]) for i in rep.items
                if i["key"].startswith("stopped:")}
    finally:
        W.ROOT = saved
        os.chdir(cwd)
        shutil.rmtree(t, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 A LEAGUE THAT STOPS IS VISIBLE, IN EACH OF THE THREE LEAGUES")
# ══════════════════════════════════════════════════════════════════════
# 2026-10-06 15:52Z, every league's last pass at 11:11Z (MLB's real one).
_s = stopped("2026-10-06T11:11:55Z", "2026-10-06T15:52Z")
ck("🔴 each league with rows past due and no pass since is reported",
   set(_s) == {"mlb", "ncaaf", "nfl"}, str(_s))
eq({lg: sev for lg, (sev, _w) in _s.items()},
   {"mlb": "BROKEN", "ncaaf": "BROKEN", "nfl": "DEGRADED"},
   "🔴 BROKEN where a card is past due (MLB 14:00Z, college 13:30Z); DEGRADED for NFL, "
   "whose card is only 22 minutes past due")
ck("   ...in plain words, with the time of the last pass",
   _s.get("mlb", ("", ""))[1] == "mlb has not updated since Tue 11:11Z", str(_s.get("mlb")))

# ══════════════════════════════════════════════════════════════════════
section("2. ⛔ INSIDE THE GRACE, AND A HEALTHY LEAGUE, ARE SILENT")
# ══════════════════════════════════════════════════════════════════════
eq(stopped("2026-10-06T13:10:00Z", "2026-10-06T14:30Z"), {},
   "🔴 rows past due for less than %d minutes (MLB's card 30, college's card 60) are not "
   "reported" % W.STOPPED_GRACE_MIN)
# the 10-06 measurement: NFL 22 minutes past its card on a healthy 45-minute-old contract
eq(stopped({"data": "2026-10-06T11:11:55Z", "data/ncaaf": "2026-10-06T15:07:50Z",
            "data/nfl": "2026-10-06T15:07:56Z"}, "2026-10-06T15:52Z").get("nfl"), None,
   "🔴 a healthy league 22 minutes past a deadline is silent: rows its file already judged "
   "are its file's to report, and the grace is on the ROW, not the file's age")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE RUN LIST'S AGE IS READ FIRST")
# ══════════════════════════════════════════════════════════════════════
_t = tempfile.mkdtemp(prefix="runlist-")
try:
    _p = os.path.join(_t, "runs.json")
    put(_t, "runs.json", {"generated_at": "2026-10-06T10:41:00Z", "runs": [], "n_failed": 0})
    _doc, _why = R.run_list(_p, T("2026-10-06T15:52Z"))
    eq((_doc, _why), (None, "the run list is 5 hours old"),
       "🔴 a run list 5 hours old is named as stale and gives no verdict")
    put(_t, "runs.json", {"generated_at": "2026-10-06T15:41:00Z", "runs": [], "n_failed": 0})
    _doc, _why = R.run_list(_p, T("2026-10-06T15:52Z"))
    ck("   ...and an 11-minute-old one is read", _doc is not None and _why is None, str(_why))
finally:
    shutil.rmtree(_t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 A FAILED RE-CHECK REACHES health.json, AND CLEARS WHEN IT PASSES")
# ══════════════════════════════════════════════════════════════════════
DAY = "2026-09-03"
_t, _cwd, _saved = tempfile.mkdtemp(prefix="recheck-"), os.getcwd(), W.ROOT


def verify():
    p = subprocess.run([sys.executable, "verify_record.py"], cwd=_t, capture_output=True,
                       text=True, env=dict(os.environ, PYTHONUTF8="1"))
    W.ROOT = _t
    f = [i for i in W.run(T("2026-09-04T12:00Z"))["findings"] if i["key"] == "record-verify:mlb"]
    return p.returncode, f


try:
    put(_t, "picks/%s.json" % DAY, {"date": DAY, "kind": "gizmos-card", "picks": [
        {"kind": "pitcher", "market": "strikeouts", "side": "over", "line": 5.5, "pid": 555,
         "pitcher": "P", "confidence": 60, "game": "A @ H"}]})
    put(_t, "data/%s/results/final.json.gz" % DAY, {"slate_date": DAY, "n_games": 1, "n_final": 1,
        "games": [{"gamePk": 1, "state": "Final", "score": {"home": 3, "away": 2},
                   "pitchers": [{"id": 555, "started": True, "k": 7, "outs": 18}], "batters": []}]})
    os.makedirs(os.path.join(_t, "data", "latest"), exist_ok=True)
    for f in ("verify_record.py", "collect.py", "record_grader.py"):
        shutil.copy(os.path.join(ROOT, f), _t)
    os.chdir(_t)
    C.collect_record()
    _rc0, _f0 = verify()
    _rec = json.load(open(os.path.join(_t, "data", "latest", "record.json")))
    _rec["overall"]["w"] += 1                       # the published record no longer adds up
    json.dump(_rec, open(os.path.join(_t, "data", "latest", "record.json"), "w"))
    _rc1, _f1 = verify()
    C.collect_record()                              # the record is rebuilt and adds up again
    _rc2, _f2 = verify()
finally:
    os.chdir(_cwd)
    W.ROOT = _saved
    shutil.rmtree(_t, ignore_errors=True)
eq((_rc0, _f0), (0, []), "   a record that adds up: verify_record passes, health.json says nothing")
ck("🔴 a record that does not add up: the run fails AND health.json carries a BROKEN finding, "
   "in plain words, naming the check", _rc1 == 1 and len(_f1) == 1 and _f1[0]["severity"] == "BROKEN"
   and _f1[0]["what"] == "the MLB Track Record does not add up"
   and "overall reproduces" in _f1[0]["why"], str(_f1))
eq((_rc2, _f2), (0, []), "🔴 ...and it clears when the re-check passes again")

# ══════════════════════════════════════════════════════════════════════
section("5. ⛔ A WORKFLOW SAM SWITCHED OFF IS NOT EXPECTED TO FIRE")
# ══════════════════════════════════════════════════════════════════════
_names0 = R.scheduled_workflows(ROOT)
ck("   (self-repair is a scheduled workflow while it is on)",
   "self-repair.yml" in _names0.values(), str(sorted(_names0.values())))
R.DISABLED.add("self-repair.yml")
try:
    _names1, _decl1 = R.scheduled_workflows(ROOT), R.declared_crons(ROOT)
finally:
    R.DISABLED.discard("self-repair.yml")
ck("🔴 switched off in GitHub, it is not a workflow that must show runs",
   "self-repair.yml" not in _names1.values(), str(sorted(_names1.values())))
ck("🔴 ...nor one whose crons must fire, so the runs watcher stays quiet about it",
   all(v.get("file") != "self-repair.yml" for v in _decl1.values()),
   str(sorted(v.get("file") for v in _decl1.values())))
