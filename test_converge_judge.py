#!/usr/bin/env python3
"""A FAILED PASS IS RED ONLY WHEN IT LEFT THE SITE OUT OF CONTRACT -- OR WAS OURS.

🔴 WHAT HAPPENED `[Sam, 2026-09-26]`. runs.json showed collect runs red on
"mode 'news' failed for ncaaf", "mode 'cfb-probe' failed for ncaaf" and,
for nfl, nfl-logs / card-fb / news, while every artifact was inside its
freshness deadline. Sam: make a pass failure red only when it leaves an
artifact stale or missing (the freshness contract is the judge); otherwise
a warning with the source named; SOFT stays soft.

⚠️ MEASURED FIRST: all seven of those failures were football `props-board`
raising `TypeError: '<' not supported between instances of 'dict' and
'int'` -- OUR code, after the board was written, so the contract saw
nothing stale. The workflow's line named the mode the cron launched.
So the rule shipped is Sam's, with the one condition this repo already
requires of any excuse (`freshness.source_block`): a failure is downgraded
only with EVIDENCE that an outside source failed. Our own exception stays
red whatever the contract says; the props-board defect itself is fixed and
guarded in `test_run_mode_left.py`.

This drives the REAL `collect.converge` in a sandbox, with only `run_mode`
and the spend counter stubbed.

# @vacuity 🔴 an artifact left out of contract keeps the run red
#   file: freshness.py
#   find:         elif mode in hard_by:
#   with:         elif False:
#
# @vacuity 🔴 our own code failing stays red even while the artifact is fresh
#   file: freshness.py
#   find:         elif not source:
#   with:         elif False:
#
# @vacuity ⛔ a mode no contract row can judge fails closed
#   file: freshness.py
#   find:         if not own:
#   with:         if False:
#
# @vacuity an HTTP error is evidence of an outside source
#   file: freshness.py
#   find:             return f"HTTP {exc.code} from the source"
#   with:             return None
#
# @vacuity converge actually consults the judge
#   file: collect.py
#   find:     failed, excused = _fresh.judge_failures(failed, rows2, DATA)
#   with:     failed, excused = [(m, w, [], "x") for m, w, _s in failed], []
#
# @vacuity the downgrade is an annotation GitHub shows, naming the source
#   file: collect.py
#   find:         print(f"::warning::{m} failed for {LEAGUE} ({why}) — {verdict}: "
#   with:         print(f"{m} failed for {LEAGUE} ({why}) — {verdict}: "
#
# @vacuity 🔴 the renamed news archive row (#182) stays soft under its writer
#   file: freshness.py
#   find: SOFT = {"news", "weather", "lineups", "cfb-teams", "runs"}
#   with: SOFT = {"weather", "lineups", "cfb-teams", "runs"}
#
# @vacuity a SOFT failure is an annotation too
#   file: collect.py
#   find:         print(f"::warning::{mode} failed for {LEAGUE} ({why}) — a SOFT "
#   with:         print(f"{mode} failed for {LEAGUE} ({why}) — a SOFT "
"""
import contextlib
import datetime
import importlib
import io
import json
import os
import shutil
import sys
import tempfile
import urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, eq, note, section  # noqa: E402

os.environ["LEAGUE"] = "mlb"
os.environ.setdefault("ODDS_API_KEY", "test")
import freshness as F  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime.now(UTC)


def sandbox(board_age_min, news_age_min=5):
    """An MLB data tree holding only board.json and news.json, at the given
    ages. Every other artifact is missing, so converge plans it; the stub
    lets those succeed, which cannot change the verdict on a FAILED mode."""
    d = tempfile.mkdtemp(prefix="judge-")
    os.makedirs(f"{d}/data/latest")
    os.makedirs(f"{d}/picks")
    for path, age in (("board.json", board_age_min), ("news.json", news_age_min)):
        ts = (NOW - datetime.timedelta(minutes=age)).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(f"{d}/data/latest/{path}", "w") as fh:
            json.dump({"pulled_at": ts}, fh)
    return d


def converge(d, fail, explicit=()):
    """Run the real converge in `d`; `fail` maps a mode to the exception it
    raises. -> (exit code, stdout)."""
    cwd = os.getcwd()
    os.chdir(d)
    try:
        import collect
        importlib.reload(collect)

        def run_mode(m):
            if m in fail:
                raise fail[m]
        collect.run_mode = run_mode
        collect.daily_spend = lambda: 0
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = collect.converge(explicit=list(explicit))
        return code, out.getvalue()
    finally:
        os.chdir(cwd)


def http(code):
    return urllib.error.HTTPError("https://example.invalid", code, "down", {}, None)


def annotations(out, kind):
    return [l for l in out.splitlines() if l.startswith(f"::{kind}::")]


# The board's deadline, from the contract itself: a board built 2 minutes
# ago is inside it; one built three days ago is not.
FRESH, STALE = 2, 3 * 24 * 60
_d = sandbox(FRESH)
_rows = {r["mode"]: r for r in F.survey(data=_d + "/data", picks=_d + "/picks", now=NOW)}
shutil.rmtree(_d, ignore_errors=True)
ck(not _rows["gamelines"]["stale"], "the sandbox's fresh board is inside contract",
   str(_rows["gamelines"]))

# ══════════════════════════════════════════════════════════════════════
section("1. SAM'S CASE: A FAILED NEWS PASS WITH FRESH NEWS -> GREEN, WITH A WARNING")
# ══════════════════════════════════════════════════════════════════════
d = sandbox(FRESH)
try:
    code, out = converge(d, {"news": urllib.error.URLError("feed down")}, ["news"])
    eq(code, 0, "🔴 the run stays green")
    w = annotations(out, "warning")
    ck(any(l.startswith("::warning::news failed for mlb") and "URLError" in l for l in w),
       "   ...and says so as an annotation GitHub shows, naming news and the error", str(w))
    ck(not annotations(out, "error"), "   ...and raises no error annotation")
finally:
    shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("2. AN OUTSIDE SOURCE FAILS, THE ARTIFACT IS STILL CURRENT -> GREEN, WARNING")
# ══════════════════════════════════════════════════════════════════════
d = sandbox(FRESH)
try:
    code, out = converge(d, {"gamelines": http(503)}, ["gamelines"])
    eq(code, 0, "🔴 a HARD mode's source outage inside its deadline does not turn the run red")
    w = [l for l in annotations(out, "warning") if l.startswith("::warning::gamelines")]
    ck(len(w) == 1 and "HTTP 503 from the source" in w[0] and "board.json" in w[0]
       and "inside its deadline" in w[0],
       "   ...the warning names the mode, the source's error and the artifact still current",
       str(w))
finally:
    shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE SAME FAILURE LEAVING THE ARTIFACT STALE -> RED")
# ══════════════════════════════════════════════════════════════════════
d = sandbox(STALE)
try:
    code, out = converge(d, {"gamelines": http(503)}, ["gamelines"])
    eq(code, 1, "🔴🔴 a failed pass that leaves an artifact stale turns the run red")
    e = [l for l in annotations(out, "error") if l.startswith("::error::gamelines")]
    ck(len(e) == 1 and "out of contract" in e[0],
       "   ...and the error names the mode that failed, not the one the cron launched", str(e))
finally:
    shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("4. ⛔ OUR OWN CODE FAILING STAYS RED, EVEN WITH THE ARTIFACT FRESH")
# ══════════════════════════════════════════════════════════════════════
# The shape of all seven 09-24/25 failures: the board was written, THEN
# our code raised. The contract sees a fresh file; only the error says why.
d = sandbox(FRESH)
try:
    code, out = converge(d, {"gamelines": TypeError(
        "'<' not supported between instances of 'dict' and 'int'")}, ["gamelines"])
    eq(code, 1, "🔴🔴 a TypeError of ours is red whatever the contract says")
    e = [l for l in annotations(out, "error") if l.startswith("::error::gamelines")]
    ck(len(e) == 1 and "our own code" in e[0], "   ...and says it is ours", str(e))
    # ...and a fetch error re-raised inside our own wrapper still counts
    try:
        try:
            raise http(429)
        except urllib.error.HTTPError as inner:
            raise RuntimeError("could not fetch the odds") from inner
    except RuntimeError as wrapped:
        ck(F.outside_source(wrapped) == "HTTP 429 from the source",
           "   ✅ an outside error re-raised in our wrapper is still read as the source's")
    ck(F.outside_source(RuntimeError("depth_rank is CONSTANT None")) is None
       and F.outside_source(KeyError("x")) is None,
       "   ⛔ a RuntimeError or KeyError of our own is never evidence of a source")
finally:
    shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("5. ⛔ A MODE THE CONTRACT CANNOT JUDGE FAILS CLOSED")
# ══════════════════════════════════════════════════════════════════════
d = sandbox(FRESH)
try:
    code, out = converge(d, {"live-probe": http(503)}, ["live-probe"])
    eq(code, 1, "a failed mode with no freshness row stays red")
    e = [l for l in annotations(out, "error") if l.startswith("::error::live-probe")]
    ck(len(e) == 1 and "no freshness row" in e[0], "   ...and says why", str(e))
finally:
    shutil.rmtree(d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("6. THE NEWS ARCHIVE ROW, RENAMED TO ITS WRITER `news` (#182)")
# ══════════════════════════════════════════════════════════════════════
# `[2026-09-26]` #182 renamed the dated archive's row from `news-archive`
# (a mode `run_mode` never had) to `news`, and took `news-archive` out of
# SOFT. The judge must still treat it as the SOFT row it always was: a
# stale archive is the gate's warning, never a red run, and a failed news
# pass beside it is never red. Driven on the REAL football contracts, with
# only the archive row forced stale.
for _lg in ("nfl", "ncaaf"):
    _d = os.path.join(ROOT, "data", _lg)
    _rows = F.survey(_d, os.path.join(ROOT, "picks"))
    _arc = [r for r in _rows if r["kind"] == "dir" and r["path"].endswith("/news")]
    ck(len(_arc) == 1 and _arc[0]["mode"] == "news",
       "%s: the archive row is found by path, under its writer `news`" % _lg,
       str([(r["mode"], r["path"]) for r in _arc]))
    if len(_arc) != 1:
        continue
    _forced = [dict(r, stale=True, missing=False, age_min=r["age_min"] or 90)
               if r is _arc[0] else r for r in _rows]
    _hard, _soft = F.classify(_forced, _d)
    ck(any(r["path"] == _arc[0]["path"] for r in _soft)
       and not any(r["path"] == _arc[0]["path"] for r in _hard),
       "   🔴 a stale archive is SOFT in the gate, never hard")
    _red, _warned = F.judge_failures(
        [("news", "URLError: feed down", "URLError reaching the source")], _forced, _d)
    ck(not _red and len(_warned) == 1,
       "   🔴 ...and a failed news pass beside it is a warning, not a red run",
       "red=%r" % ([x[3] for x in _red],))

note("⛔ WHAT THIS DOES NOT CLAIM: that a warning is harmless forever. The "
     "pass-end gate (verify_freshness.py) still turns the run red the moment "
     "the artifact goes past due, and every downgrade is a ::warning:: on the "
     "run page.")
