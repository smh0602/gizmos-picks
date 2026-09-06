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
