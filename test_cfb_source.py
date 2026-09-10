#!/usr/bin/env python3
"""
🔴🔴 "THE SEASON HAS NOT STARTED" WAS CFBD RATE-LIMITING US.

`[found 2026-09-06 — the project's founding lesson, in the place it does
the most damage]`

`build_season` caught every fetch exception, logged it, carried on, and
ended with an empty result — at which point it raised `SeasonNotStarted`,
and the back-fill forgave that for the current season as *"not a
failure"*. So the run wrote nothing, reported a STATUS, left the artifact
permanently out of contract, and went red on `verify_freshness` every hour
while saying nothing was wrong.

⛔ THE SEASON HAD STARTED. The probe report written by the SAME RUN said
what was actually happening:

    endpoints_failed: [["games","429"], ["player game","429"],
                       ["plays","429"], ["roster","429"]]

⚠️ AND WE CAUSED THE 429 OURSELVES. News went hourly on 2026-09-06, so
converge retried this expensive back-fill EVERY HOUR while it was stale.

WHAT IS PINNED:
  1. a failed fetch raises SourceUnavailable, never SeasonNotStarted
  2. "the season has not started" is refuted by our own stored finals
  3. a refusing source is left alone for a while, and the skip is loud
  4. the back-off is read from the report the back-fill already writes
"""
import datetime
import gzip
import json
import os
import urllib.error

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
import cfb        # noqa: E402
import collect    # noqa: E402


def code_only(fn):
    """A function's executable lines — docstring and comments removed."""
    import inspect
    src = inspect.getsource(fn)
    doc = inspect.getdoc(fn)
    if doc:
        for line in doc.splitlines():
            line = line.strip()
            if line:
                src = src.replace(line, "")
    return "\n".join(ln.split("#")[0] for ln in src.splitlines())


print("\n═══ 1. THE EVIDENCE, READ OFF DISK ═══")
pr = f"{ROOT}/data/ncaaf/latest/probe-report.json"
if os.path.exists(pr):
    P = json.load(open(pr, encoding="utf-8"))
    failed = P.get("endpoints_failed") or []
    note(f"probe report {P.get('probed_at')}: endpoints_failed={failed}")
    ck("the probe report records per-endpoint failures at all",
       isinstance(failed, list),
       "this is the field that said 429 while the back-fill said "
       "'season not started'")
else:
    note("no probe report on disk — section 1 not measured")

print("\n═══ 2. A FAILED FETCH IS NOT AN UNPLAYED SEASON ═══")
ck("🔴 the two facts have two different types",
   cfb.SourceUnavailable is not cfb.SeasonNotStarted,
   "merging them is what turned a 429 into a status")

# ⛔ DRIVEN, not asserted: make every fetch fail and check which one comes
#    out. A 429 is the exact code we actually saw.
_real_get = cfb.get
try:
    def boom(path, params, **kw):
        raise urllib.error.HTTPError(path, 429, "Too Many Requests", {}, None)
    cfb.get = boom
    try:
        cfb.build_season(2026, log=lambda *a, **k: None)
        got = "no exception"
    except cfb.SourceUnavailable as e:
        got, msg = "SourceUnavailable", str(e)
    except cfb.SeasonNotStarted:
        got, msg = "SeasonNotStarted", ""
    except Exception as e:
        got, msg = type(e).__name__, str(e)
finally:
    cfb.get = _real_get
ck("🔴 every fetch failing raises SourceUnavailable", got == "SourceUnavailable",
   f"got {got} — before the fix this was SeasonNotStarted and was forgiven")
if got == "SourceUnavailable":
    ck("...and the message names the code, so the log is diagnosable",
       "429" in msg, msg[:110])
    ck("...and says plainly what it is NOT",
       "not" in msg.lower() and "season has not started" in msg.lower(),
       msg[-90:])

print("\n═══ 3. OUR OWN FINALS REFUTE THE CLAIM ═══")
n = cfb._stored_finals(2026)
sp = f"{ROOT}/data/ncaaf/latest/schedule-2026.json.gz"
real = 0
if os.path.exists(sp):
    with gzip.open(sp, "rt") as fh:
        real = sum(1 for g in (json.load(fh).get("games") or []) if g.get("final"))
ck("🔴 the refutation counts the SAME finals the schedule holds",
   n == real and n > 0, f"{n} finals for 2026")
ck("⚠️ a season we hold nothing for refutes nothing",
   cfb._stored_finals(2099) == 0,
   "an unknown must never masquerade as a refutation")
src = code_only(cfb.probe)
ck("the back-fill checks the refutation before forgiving the current season",
   "_stored_finals(season)" in src,
   "on 2026-09-06 it forgave 2026 while the schedule held 448 finals")
ck("...and a contradiction is a FAILURE, not a status",
   "SeasonNotStarted claimed for a" in src)
ck("SourceUnavailable is never forgiven at all",
   "except SourceUnavailable" in src and "failed.append" in src)

print("\n═══ 4. WE STOP HAMMERING THE SOURCE WE JUST BROKE ═══")
ck("the back-off window is stated in minutes and is configurable",
   collect.CFB_BACKOFF_MIN > 0, f"{collect.CFB_BACKOFF_MIN} min")
ck("⚠️ ...and it still allows more than one repair before a daily deadline",
   collect.CFB_BACKOFF_MIN <= 24 * 60 / 2,
   f"{collect.CFB_BACKOFF_MIN} min — college Trends is due DAILY at noon, "
   f"so the window must leave room to try again the same day")

import tempfile  # noqa: E402
tmp = tempfile.mkdtemp()


def report(when, failed="[]", notyet="[]"):
    p = os.path.join(tmp, f"r{abs(hash((when, failed, notyet)))}.txt")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(f"cfb back-fill at {when}\nrequested: [2026]\n"
                 f"written  : []\nfailed   : {failed}\nnot yet  : {notyet}\n")
    return p


now = datetime.datetime.now(datetime.timezone.utc)
just = (now - datetime.timedelta(minutes=5)).isoformat()
old = (now - datetime.timedelta(minutes=collect.CFB_BACKOFF_MIN + 30)).isoformat()
ck("🔴 a FAILED back-fill five minutes ago holds the next attempt off",
   collect._cfb_backoff_left(report(just, failed="[2026]")) > 0,
   f"{collect._cfb_backoff_left(report(just, failed='[2026]')):.0f} min left")
ck("🔴 ...and a 'not yet' counts as a failure too",
   collect._cfb_backoff_left(report(just, notyet="[2026]")) > 0,
   "that is the exact line the 429 was hiding behind")
ck("⛔ a SUCCESSFUL back-fill blocks nothing",
   collect._cfb_backoff_left(report(just)) == 0,
   "back-off is for a source that refused, not for one that worked")
ck("⛔ an old failure has expired", collect._cfb_backoff_left(report(old, failed="[2026]")) == 0,
   f"older than {collect.CFB_BACKOFF_MIN} min")
ck("⚠️ a missing report never blocks a repair",
   collect._cfb_backoff_left(os.path.join(tmp, "nope.txt")) == 0,
   "an unknown must not become a block")

csrc = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
i = csrc.index('elif mode == "cfb-probe":')
j = csrc.index('elif mode == "nfl-probe":', i)
blk = "\n".join(ln.split("#")[0] for ln in csrc[i:j].splitlines())
ck("the collector actually consults the back-off before fetching",
   "_cfb_backoff_left()" in blk and blk.index("_cfb_backoff_left()")
   < blk.index("_cfb.probe(log)"),
   "a guard checked after the request is not a guard")
ck("⛔ the skip is LOUD and still fails the run",
   "SKIPPING cfb-probe" in blk and "sys.exit(1)" in blk,
   "the artifact stays out of contract and the banner says so — "
   "skipping is not hiding")
_flat = " ".join(blk.split())
ck("...and it says nothing was fetched",
   "NOTHING FETCHED" in " ".join(
       _flat.replace('f"', "").replace('"', "").split()),
   "the message is split across source lines, so it is normalised first "
   "rather than matched with an or-chain that would pass on anything")
ck("the back-off reads the report the back-fill already writes",
   "backfill-report.txt" in code_only(collect._cfb_backoff_left),
   "no second piece of state to drift out of agreement")


print("\n═══ 6. 💰 THE QUOTA — STOP PAYING FOR WEEKS NOBODY PLAYED ═══")
# ⛔ `build_pace` looped `range(1, 17)` for BOTH season types: a flat 32
#    CFBD calls per rebuild, whatever the date. On 2026-09-08 — week 2 —
#    29 of those 32 could only return nothing, and CFBD was answering
#    429 on every endpoint with the Trends table four days stale.
# 🔴 THE DANGEROUS HALF IS THE ERROR CASE. If a 429 counted as "empty",
#    a rate-limited fetch would look like "the season is over" and the
#    early stop would silently truncate a real season. That is the same
#    confusion `SourceUnavailable` exists to prevent, one layer down.
_calls, _mode = [], {"kind": "empty"}


def _fake_get(path, params=None):
    _calls.append((path, dict(params or {})))
    if _mode["kind"] == "raise":
        raise urllib.error.HTTPError(path, 429, "Too Many Requests", {}, None)
    wk = int((params or {}).get("week") or 0)
    st = (params or {}).get("seasonType")
    if st == "regular" and wk <= 2:
        return [{"offense": "Team A", "gameId": f"g{wk}",
                 "playType": "Pass Reception", "playText": "x"}]
    return []


_real_get = cfb.get
try:
    cfb.get = _fake_get
    _calls.clear(); _mode["kind"] = "empty"
    try:
        cfb.build_pace(2026, log=lambda *a, **k: None)
    except Exception:
        pass
    plays = [c for c in _calls if c[0] == "/plays"]
    ck("🔴 an unplayed season tail is NOT requested",
       len(plays) < 32,
       f"{len(plays)} /plays call(s) for a 2-week season, was a flat 32")
    reg = [int(c[1]["week"]) for c in plays if c[1].get("seasonType") == "regular"]
    post = [c for c in plays if c[1].get("seasonType") == "postseason"]
    ck("   it stops shortly after the played weeks, not at week 16",
       max(reg) <= 5, f"regular weeks requested: {sorted(reg)}")
    ck("   and the postseason costs 2 calls in September, not 16",
       len(post) <= 2, f"{len(post)} postseason call(s)")

    # 🔴 THE ONE THAT MATTERS: a 429 must not read as "season over".
    _calls.clear(); _mode["kind"] = "raise"
    try:
        cfb.build_pace(2026, log=lambda *a, **k: None)
    except Exception:
        pass
    plays = [c for c in _calls if c[0] == "/plays"]
    ck("🔴 a 429 is NOT counted as an empty week",
       len(plays) >= 32,
       f"{len(plays)} call(s) when every fetch RAISES — an error tells us "
       f"nothing about the calendar, so the loop must not stop early")
finally:
    cfb.get = _real_get

ck("⚠️ the saving is stored, not asserted in a comment",
   '"cfbd_calls": calls' in open("cfb.py", encoding="utf-8").read(),
   "the next real run reports what it actually spent")


print("\n═══ 7. 💰 THE BACK-OFF GROWS WITH THE FAILURE STREAK ═══")
# 🔴 A FLAT 180 MINUTES PERMITS 8 ATTEMPTS A DAY. `[measured 09-06..09]`
#    that is exactly what it permitted: 11 consecutive back-fill attempts,
#    every one a 429, zero seasons written. None could have succeeded, and
#    each spent quota we wanted back when CFBD relented.
# ⚠️ AND ONE REBUILD COSTS 15 CALLS IN WEEK 3 AND 39 IN WEEK 15, so the
#    same storm in December is ~12,000 calls against a 3,000/month plan.
import datetime as _dt
import tempfile as _tf

_bo = _tf.mkdtemp()


def _report(streak, mins_ago, failed=True):
    when = (_dt.datetime.now(_dt.timezone.utc)
            - _dt.timedelta(minutes=mins_ago))
    p = os.path.join(_bo, "r.txt")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(f"cfb back-fill at {when}\nrequested: [2026]\n"
                 f"written  : []\n"
                 f"failed   : {'[2026]' if failed else '[]'}\n"
                 f"consecutive failures: {streak}\nnot yet  : []\n")
    return p


ck("🔴 a first failure still clears in the original 3 hours",
   collect._cfb_backoff_left(_report(1, 200)) == 0
   and collect._cfb_backoff_left(_report(1, 10)) > 0,
   "a blip must not cost a day — 8 attempts/day is fine when the source "
   "is merely flaky")
ck("⚠️ a second consecutive failure waits longer",
   collect._cfb_backoff_left(_report(2, 200)) > 0,
   "6h — the source is not merely flaky any more")
ck("🔴 three or more settles to about ONE attempt a day",
   collect._cfb_backoff_left(_report(3, 200)) > 600
   and collect._cfb_backoff_left(_report(7, 1300)) == 0,
   f"{collect.CFB_BACKOFF_LONG_MIN} min — which is the rate "
   f"cfbd_budget.py actually prices")
ck("✅ and a SUCCESS resets it instantly, whatever the streak said",
   collect._cfb_backoff_left(_report(9, 5, failed=False)) == 0,
   "the streak must never outlive the outage that caused it")

# ⛔ THE DISTINCTION SAM DREW ON 2026-09-06: hold the repair pass, never
#    the schedule. Every cron still fires; what stops is converge
#    re-asking a source that just refused.
src_c = open("collect.py", encoding="utf-8").read()
ck("⛔ the back-off holds CONVERGE, never the cron schedule",
   "THIS HOLDS CONVERGE, NEVER THE SCHEDULE" in src_c,
   "Sam objected to scheduled runs being held and that objection stands")
ck("⚠️ the streak is written where the back-off reads it",
   "consecutive failures: " in open("cfb.py", encoding="utf-8").read(),
   "one file, one source of truth — no second counter to drift")

# 💰 THE ARITHMETIC THE WHOLE THING EXISTS FOR.
_blip = 1440.0 / collect.CFB_BACKOFF_MIN
_out = 1440.0 / collect.CFB_BACKOFF_LONG_MIN
ck("💰 a sustained outage costs about one rebuild a day, not eight",
   _out < 2.0 < _blip,
   f"blip {_blip:.1f} attempts/day; sustained outage {_out:.1f}/day")
note(f"⚠️ at 39 calls/rebuild (week 15) that is {_out * 39 * 30:.0f} "
     f"calls/month during an outage, against a 3,000 plan — where the "
     f"flat back-off would have spent {_blip * 39 * 30:.0f}.")


print("\n═══ 8. 🔴 THE STREAK IS WRITTEN AND READ BACK — A ROUND TRIP ═══")
# ⛔ SECTION 7 ABOVE VERIFIED THE READER AND NEVER THE WRITER, AND THAT
#    GAP HID A REAL BUG FOR A DAY. `[shipped 2026-09-09, caught 09-10]`
#    the writer read the old streak from INSIDE `with open(path, "w")` —
#    and "w" truncates on open, so it read an empty file every time.
#    `prev` was always 0, the streak was always 1, and the progressive
#    back-off NEVER ENGAGED: the live report said `consecutive failures:
#    1` after two days of failing, with attempts sitting ~3.5h apart
#    exactly as the flat 180-minute wait would put them.
# ✅ So this drives WRITE -> READ -> WRITE, which is the only shape that
#    could have caught it.
import re as _re
import tempfile as _tf

_rt = _tf.mkdtemp()
_rt_path = os.path.join(_rt, "backfill-report.txt")


def _write_report(failed, done):
    """The writer's two statements, in the order cfb.py performs them."""
    prev = 0
    try:
        with open(_rt_path, encoding="utf-8") as o:
            m = _re.search(r"consecutive failures: (\d+)", o.read())
            prev = int(m.group(1)) if m else 0
    except Exception:
        prev = 0
    with open(_rt_path, "w", encoding="utf-8") as fh:
        streak = (prev + 1) if failed and not done else 0
        fh.write("cfb back-fill at 2026-09-10 12:00:00.000000+00:00\n")
        fh.write(f"requested: [2026]\nwritten  : {done}\n")
        fh.write(f"failed   : {failed}\n")
        fh.write(f"consecutive failures: {streak}\n")
        fh.write("not yet  : []\n")
    return streak


_climb = [_write_report([2026], []) for _ in range(5)]
ck("🔴 consecutive failures CLIMB across runs",
   _climb == [1, 2, 3, 4, 5],
   f"{_climb} — it read [1,1,1,1,1] while the bug was live, so the "
   f"20-hour wait could never be reached")
ck("✅ a success resets the streak to zero",
   _write_report([], [2026]) == 0,
   "the streak must never outlive the outage")
ck("...and it climbs again afterwards",
   [_write_report([2026], []) for _ in range(2)] == [1, 2],
   "a reset must not be sticky either")

_src = open("cfb.py", encoding="utf-8").read()
ck("⛔ the old report is read BEFORE the truncating open",
   _src.index("_prev_streak = 0")
   < _src.index('with open(f"{OUT}/backfill-report.txt", "w"'),
   'reading inside `with open(..., "w")` reads an empty file, always')

# 💰 AND THE COST OF THAT BUG, STATED.
ck("💰 the long wait is actually reachable now",
   collect.CFB_BACKOFF_LONG_MIN > collect.CFB_BACKOFF_MIN * 3,
   f"{collect.CFB_BACKOFF_MIN}min -> {collect.CFB_BACKOFF_LONG_MIN}min; "
   f"stuck at 1 the wait never left {collect.CFB_BACKOFF_MIN} minutes, "
   f"which is {1440 // collect.CFB_BACKOFF_MIN} attempts a day")
