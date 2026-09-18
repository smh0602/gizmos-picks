#!/usr/bin/env python3
"""AN ARTIFACT NOTHING TRACKS IS AN ARTIFACT NOBODY MISSES.

🔴🔴 THE DEFECT, MEASURED 2026-09-18 — the first full production day of
the college path. The dossier landed in both leagues. **Section 6 was
UNAVAILABLE for all 32 NFL games**, because `build_possession` never ran:
the daily `14 7 * * *` arm was dropped, which GitHub does and this repo
has measured repeatedly. ⛔ That part is not a code defect.

⛔ **THE DEFECT IS THAT NOTHING NOTICED.** `top-<season>` had no freshness
entry of any kind. `freshness.py` tracked `allowed-by-position-2026` for
the same mode — due Tuesdays — and the contract read `stale: False,
ok: True` while the possession artifact did not exist at all. §6 would
have stayed UNAVAILABLE indefinitely with the contract reporting healthy.

✅ **SO THE ARTIFACT GETS ITS OWN ROW**, and converge repairs it on any
arm rather than waiting for one daily cron to land.

══════════════════════════════════════════════════════════════════════
⛔ AND THE ROW PROBES THE *PROBE*, NOT THE TABLE.
══════════════════════════════════════════════════════════════════════
`top-{season}.json.gz` is written only when the derivation holds together;
`top-probe-{season}.json` is written EITHER WAY. So they answer different
questions and only one is a freshness question:

    probe MISSING/STALE       -> the builder DID NOT RUN. Repairable. ✅
    probe FRESH, table absent -> the builder RAN AND REFUSED. Not late.

🔴 THE SECOND CASE IS NOT HYPOTHETICAL AND IT IS WHY THIS DISTINCTION IS
CHECKED RATHER THAN ASSUMED: college's derivation is refusing right now
over CFBD's play ordering, correctly. A row on the TABLE would mark the
site stale on every run until that is settled — **a banner nobody can
clear**, the exact failure `freshness.py` argues against in four places
and has already lived through once.

⚠️ EVERY CASE BELOW IS DRIVEN AGAINST A SYNTHETIC TREE, never against the
live one — the live tree moves under a test and a test that reads it is a
test that goes red for reasons that are nobody's fault.

⚠️ No network, no CFBD calls, no credits.
"""
import ast
import datetime
import gzip
import io
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section

import freshness as F

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 9, 18, 18, 0, tzinfo=UTC)     # 2pm ET, a Friday
SEASON = F.current_football_season(NOW)


# ══════════════════════════════════════════════════════════════════════
# @vacuity the possession row must probe the probe, not the trends table
#   file: freshness.py
#   find: ("file", f"{latest}/top-probe-{season}.json"), T["possession"],
#   with: ("file", tpath), T["possession"],
#
# @vacuity cfb.py's second write path must stamp, or the row can never clear
#   file: cfb.py
#   find: o = dict(o, written_at=datetime.datetime.now(
#   with: o = dict(o, not_a_stamp=datetime.datetime.now(
# ══════════════════════════════════════════════════════════════════════


def _stamped(obj, minutes_ago, now=NOW):
    """A document carrying a real timestamp, `minutes_ago` old."""
    t = (now - datetime.timedelta(minutes=minutes_ago))
    return dict(obj, written_at=t.strftime("%Y-%m-%dT%H:%M:%SZ"))


def tree(league, trends_age=60, probe_age=None, table_age=None):
    """A synthetic league tree. `None` means THE FILE IS NOT THERE."""
    d = tempfile.mkdtemp(prefix="possfresh-")
    latest = os.path.join(d, league, "latest")
    os.makedirs(latest)
    def put(n, age):
        # ⚠️ A `.gz` NAME MUST REALLY BE GZIP. `freshness._load()` reads
        #    the file to find its stamp; a plain-text file with a `.gz`
        #    name fails to parse, reads as MISSING, and the fixture
        #    silently tests the wrong thing.
        body = json.dumps(_stamped({"kind": "TEST"}, age))
        path = os.path.join(latest, n)
        if n.endswith(".gz"):
            with gzip.open(path, "wt", encoding="utf-8") as fh:
                fh.write(body)
        else:
            io.open(path, "w", encoding="utf-8").write(body)
    if trends_age is not None:
        put("allowed-by-position-%d.json.gz" % SEASON, trends_age)
    if probe_age is not None:
        put("top-probe-%d.json" % SEASON, probe_age)
    if table_age is not None:
        put("top-%d.json.gz" % SEASON, table_age)
    return d


def rows_for(league, **kw):
    d = tree(league, **kw)
    try:
        return F.survey(data=os.path.join(d, league), picks="picks", now=NOW)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def poss_rows(rows):
    return [r for r in rows if "top-" in r["path"]]


# ══════════════════════════════════════════════════════════════════════
section("1. ⚠️ THE ROW EXISTS, FOR BOTH LEAGUES (rule 67)")
# ══════════════════════════════════════════════════════════════════════
for _lg in ("ncaaf", "nfl"):
    _r = poss_rows(rows_for(_lg, probe_age=30))
    ck("⚠️ %s has exactly one possession row" % _lg,
       len(_r) == 1,
       "⛔ zero rows makes every drive below vacuous; two rows means the "
       "contract disagrees with itself. got %s"
       % [x["path"].split("/")[-1] for x in _r])
    ck("🔴 ...and it probes the PROBE, which is written either way",
       bool(_r) and _r[0]["path"].endswith("top-probe-%d.json" % SEASON),
       "⛔ probing `top-{season}.json.gz` would mark the site stale on "
       "every run while the derivation is correctly refusing — a banner "
       "nobody can clear. got %s"
       % (_r[0]["path"].split("/")[-1] if _r else "no row"))
    ck("⛔ ...and it is NOT the defence-vs-position table",
       bool(_r) and "allowed-by-position" not in _r[0]["path"],
       "🔴 THE BRIEF'S OWN WARNING: a contract entry pointing at the "
       "wrong file is worse than none — it reports healthy about a file "
       "it is not watching. got %s"
       % (_r[0]["path"] if _r else "no row"))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 THE DEFECT ITSELF — TRENDS FRESH, POSSESSION ABSENT")
# ══════════════════════════════════════════════════════════════════════
# ⛔ THIS IS THE CASE THAT PASSED ON `main`, WHICH IS THE WHOLE DEFECT:
#    `allowed-by-position` fresh, no possession artifact anywhere, and the
#    contract reporting `ok`.
for _lg in ("ncaaf", "nfl"):
    _rows = rows_for(_lg, trends_age=10, probe_age=None, table_age=None)
    _trend = [r for r in _rows if "allowed-by-position" in r["path"]]
    _poss = poss_rows(_rows)
    ck("⚠️ %s: the trends row really is fresh in this tree" % _lg,
       bool(_trend) and not _trend[0]["stale"],
       "⛔ if trends were stale too, the drive below would prove nothing "
       "about the possession row — rule 67. trends stale=%s"
       % (_trend[0]["stale"] if _trend else "no row"))
    ck("🔴🔴 %s: the contract is NOT ok when possession is missing" % _lg,
       bool(_poss) and _poss[0]["stale"] and _poss[0]["missing"],
       "⛔ THE DEFECT. On main this tree reported healthy and §6 would "
       "have stayed UNAVAILABLE for ever. stale=%s missing=%s"
       % (_poss[0]["stale"] if _poss else "-",
          _poss[0]["missing"] if _poss else "-"))

# ══════════════════════════════════════════════════════════════════════
section("3. ⛔ BUT A CORRECT REFUSAL IS NOT LATENESS")
# ══════════════════════════════════════════════════════════════════════
# 🔴 THE OTHER HALF, AND THE ONE A NAIVE FIX GETS WRONG. The builder ran,
#    looked at the data, and declined to publish. The probe says why. That
#    is the product working, and the contract must not call it stale.
for _lg in ("ncaaf", "nfl"):
    _poss = poss_rows(rows_for(_lg, trends_age=10, probe_age=30,
                               table_age=None))
    ck("⛔ %s: probe fresh + table absent reads OK (the refusal case)" % _lg,
       bool(_poss) and not _poss[0]["stale"],
       "🔴 college is in exactly this state TODAY, refusing over CFBD's "
       "play ordering. A row that fires here is a banner nobody can "
       "clear, and `freshness.py` exists partly to prevent that. "
       "stale=%s" % (_poss[0]["stale"] if _poss else "-"))

# ⚠️ AND A STALE PROBE IS STILL STALE — the grace above must not become a
#    blanket excuse. A probe older than its deadline means the builder has
#    not run since, whatever it decided last time.
for _lg in ("ncaaf", "nfl"):
    _poss = poss_rows(rows_for(_lg, trends_age=10, probe_age=60 * 40))
    ck("⚠️ %s: a probe older than its deadline IS stale" % _lg,
       bool(_poss) and _poss[0]["stale"] and not _poss[0]["missing"],
       "⛔ otherwise 'the builder refused' would excuse 'the builder "
       "stopped running', which is the defect wearing the fix's clothes. "
       "stale=%s missing=%s" % (_poss[0]["stale"] if _poss else "-",
                                _poss[0]["missing"] if _poss else "-"))

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE ARTIFACT CAN ACTUALLY BE AGED — IT WAS BORN BLIND")
# ══════════════════════════════════════════════════════════════════════
# ⛔ `freshness.stamp_of()` reads a timestamp out of a file's CONTENT and
#    NEVER from the filesystem. `cfb.py` writes its own artifacts through
#    a second path that skipped `collect.write()`'s stamping choke point,
#    so the college possession probe carried NO timestamp and read as
#    MISSING for ever — a row on it could never have cleared.
_src = io.open(os.path.join(ROOT, "cfb.py"), encoding="utf-8").read()
_tree_ast = ast.parse(_src)
_stamps = [n for n in ast.walk(_tree_ast)
           if isinstance(n, ast.keyword) and n.arg == "written_at"]
ck("🔴 cfb.py's own write path stamps what it writes, in CODE",
   bool(_stamps),
   "⛔ read from the AST, not the text, so a comment naming `written_at` "
   "cannot satisfy it. `collect.write()` says why this matters: stamping "
   "at the choke point means a NEW artifact cannot be born un-ageable. "
   "keyword sites found: %d" % len(_stamps))

# ✅ AND DRIVEN, not merely located: a report with no stamp of its own,
#    run through the same expression, must become ageable.
_d = tempfile.mkdtemp(prefix="stamp-")
try:
    _o = {"season": SEASON, "usable": False}
    _o = dict(_o, written_at=datetime.datetime.now(UTC)
              .strftime("%Y-%m-%dT%H:%M:%SZ"))
    _p = os.path.join(_d, "top-probe-%d.json" % SEASON)
    json.dump(_o, io.open(_p, "w", encoding="utf-8"), indent=1)
    _age = F.age_minutes(_p)
finally:
    shutil.rmtree(_d, ignore_errors=True)
ck("🔴🔴 a probe written that way is AGEABLE, not MISSING",
   _age < F.MISSING,
   "⛔ MISSING means 'no usable timestamp — treat as infinitely old', so "
   "an unstamped artifact is permanently stale and its row can never "
   "clear. age=%s MISSING=%d" % (_age, F.MISSING))

# ══════════════════════════════════════════════════════════════════════
section("5. ⚠️ THE DEADLINE SITS BEFORE THE CRON, NOT AFTER IT")
# ══════════════════════════════════════════════════════════════════════
# ⛔ `freshness.py` learned this the hard way for `scores`: "A deadline is
#    satisfied by a build AT OR AFTER it; having one just BEFORE it proves
#    nothing." A deadline AFTER the cron is worse — the artifact the cron
#    just wrote reads older than the deadline and the row never clears.
# ⚠️ DERIVED FROM THE WORKFLOW, not typed.
_wf = io.open(os.path.join(ROOT, ".github", "workflows", "collect.yml"),
              encoding="utf-8").read()
# ⚠️ THE SPACING IN THE WORKFLOW IS COLUMN-ALIGNED, NOT SINGLE-SPACED —
#    `LEAGUE=nfl;   MODES=` against `LEAGUE=ncaaf; MODES=`. A regex that
#    assumes one space matches one league and silently drops the other,
#    which is how a two-league check becomes a one-league check.
_ARM = re.compile(r'"(\d+) (\d+) \* \* \*"\)\s+LEAGUE=(\w+);\s+MODES="([^"]+)"')
_daily = {}
for _m, _h, _lg, _modes in _ARM.findall(_wf):
    for _mode in _modes.split():
        if _mode in ("cfb-probe", "nfl-logs"):
            _daily.setdefault(_lg, []).append(int(_h) * 60 + int(_m))
ck("⚠️ both leagues really do have a DAILY arm building possession",
   sorted(_daily) == ["ncaaf", "nfl"],
   "⛔ if the arms moved, the deadline below is being compared against "
   "nothing — rule 67. found %s" % _daily)
for _lg, _mins in sorted(_daily.items()):
    _due_h, _due_m = F.FB_TIMES[_lg]["possession"][0][:2]
    # the contract's times are ET; the crons are UTC. ET = UTC-4 in September.
    _due_utc = ((_due_h + 4) % 24) * 60 + _due_m
    ck("⚠️ %s: the %02d:%02d ET deadline precedes its %02d:%02dZ arm"
       % (_lg, _due_h, _due_m, min(_mins) // 60, min(_mins) % 60),
       _due_utc <= min(_mins),
       "⛔ a deadline AFTER the cron can never be met: the run writes the "
       "file, the deadline rolls past it, and the row is stale again "
       "within the hour. due=%dZ arm=%dZ" % (_due_utc, min(_mins)))

# ══════════════════════════════════════════════════════════════════════
section("6. ⛔ ONE MODE, ONE ENTRY IN THE PLAN")
# ══════════════════════════════════════════════════════════════════════
# 🔴 THE POSSESSION ROW SHARES ITS MODE WITH THE TRENDS ROW — that is the
#    point, they are built together — so a pass where both are stale must
#    not run that mode twice. For a free mode that is wasted minutes; for
#    a paid one it would be wasted credits.
for _lg in ("ncaaf", "nfl"):
    _d = tree(_lg, trends_age=60 * 24 * 30, probe_age=None)
    try:
        _modes, _rows = F.plan(data=os.path.join(_d, _lg), picks="picks",
                               now=NOW, allow_paid=False)
    finally:
        shutil.rmtree(_d, ignore_errors=True)
    _mode = "cfb-probe" if _lg == "ncaaf" else "nfl-logs"
    ck("⛔ %s: `%s` appears at most once in the plan" % (_lg, _mode),
       _modes.count(_mode) <= 1,
       "⛔ two contract rows, one mode — without a dedupe converge runs "
       "the builder twice in a single pass. plan=%s" % _modes)
    ck("⚠️ ...and it IS in the plan, so the dedupe is not hiding it",
       _mode in _modes,
       "⛔ a dedupe that dropped the mode entirely would satisfy the "
       "check above while breaking the repair. plan=%s" % _modes)

# ⚠️ AND THE MODE IS ONE THE COLLECTOR CAN ACTUALLY DISPATCH. `plan()`
#    returns mode names straight to converge; a name nothing answers to is
#    a repair that silently never happens.
_collect = io.open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
for _lg, _mode in (("ncaaf", "cfb-probe"), ("nfl", "nfl-logs")):
    ck("⚠️ %s's possession row names a REAL collector mode (%s)"
       % (_lg, _mode),
       ('"%s"' % _mode) in _collect,
       "⛔ converge receives this string and dispatches on it. A kind "
       "that is not a mode is a row that reports a problem nothing can "
       "fix.")

note("season %d · deadlines %s · daily arms %s"
     % (SEASON, {l: F.FB_TIMES[l]["possession"] for l in ("ncaaf", "nfl")},
        _daily))
