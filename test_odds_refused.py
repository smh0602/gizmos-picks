#!/usr/bin/env python3
"""A REFUSED ODDS API KEY IS BROKEN, IN THE API'S OWN WORDS, WITH SAM'S STEPS.

`[2026-10-23]` Sam's plan lapsed on 10-22 and was bought again. From 21:42Z
every Odds API call came back "HTTP Error 401: Unauthorized" and nothing more,
until he replaced the ODDS_API_KEY secret at 17:10Z the next day. The runs
warned (an outside source inside its deadline, Sam's 09-26 rule), then went
red on stale odds; health.json at 14:41Z called it DEGRADED staleness "the
converge loop repairs on its own", and its alert would have handed Sam a
prompt for Claude about the MLB record. Three defects, one guard file:
  1. the API's reason was never read or kept;
  2. nothing turned "every call is refused" into a finding;
  3. the alert's only instruction was a code fix, never "replace the key".
Every case is planted in a throwaway tree; nothing reads production data, and
the key used is a fake one made up here.

# @vacuity 🔴🔴 a refused call is recorded
#   file: collect.py
#   find:                 why = record_refusal(path, e)
#   with:                 why = {"error_code": None, "message": None}
#
# @vacuity 🔴🔴 the key never reaches the file or the log
#   file: collect.py
#   find:         s = s.replace(ODDS_KEY, "***")
#   with:         pass
#
# @vacuity 🔴 only a 401 or 403 is a refusal
#   file: collect.py
#   find: REFUSED_CODES = (401, 403)
#   with: REFUSED_CODES = (401, 403, 500)
#
# @vacuity 🔴 a run of refusals keeps the time it began
#   file: collect.py
#   find:             first = old
#   with:             pass
#
# @vacuity 🔴🔴 a refusal with no paid pull after it is BROKEN
#   file: watchdog.py
#   find:     if good and str(good[0]) >= str(j["at"]):
#   with:     if good:
#
# @vacuity 🔴 the watchdog runs the check
#   file: watchdog.py
#   find:           check_odds_refused,
#   with:           check_credit_balance,
#
# @vacuity 🔴🔴 Sam's steps come first, ahead of an older BROKEN finding
#   file: watchdog.py
#   find:     f = next((x for x in findings if str(x.get("key")).split(":")[0] in SAM_DOES), findings[0])
#   with:     f = findings[0]
#
# @vacuity 🔴 the steps are quoted from the doc Sam can also read on his own
#   file: watchdog.py
#   find:         steps = txt.split("<!-- steps -->", 1)[1].split("<!-- /steps -->", 1)[0].strip()
#   with:         steps = ""
#
# @vacuity 🔴 a refused key never summons a code-fixing agent
#   file: watchdog.py
#   find:                                 and i["key"].split(":")[0] not in SAM_DOES}),
#   with:                                 }),
"""
import datetime
import gzip
import io
import json
import os
import shutil
import sys
import tempfile
import urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import collect as C  # noqa: E402
import freshness as F  # noqa: E402
import watchdog as W  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

UTC = datetime.timezone.utc
FAKE_KEY = "fake-key-made-up-for-this-test-0123456789"
# ⚠️ The path is the contract between the two sides (collect writes it, the
#    watchdog reads it), so it is pinned here, not read from either.
REFUSED = os.path.join("data", "latest", "odds-refused.json")
_CHECK = getattr(W, "check_odds_refused", lambda rep, now: None)


def at(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def put(root, rel, doc):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if rel.endswith(".gz"):
        with gzip.open(p, "wt") as fh:
            json.dump(doc, fh)
    else:
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
    return p


def reading(root, rel, pulled, left, used=6):
    return put(root, rel, {"pulled_at": pulled, "credits_remaining": left,
                           "credits_used": used})


def refusal(code, body):
    return urllib.error.HTTPError(
        "https://api.the-odds-api.com/v4/sports/x/odds?apiKey=%s" % FAKE_KEY,
        code, "Unauthorized" if code == 401 else "Error", {}, io.BytesIO(body))


class Sandbox:
    """A throwaway working tree for collect.py, pinned to `when`, its `get`
    raising `err` (an Odds API answer)."""
    SAVE = ("now", "log", "get", "ODDS_KEY")

    def __init__(self, when):
        self.when, self.logs = at(when), []

    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="refused-")
        self.cwd = os.getcwd()
        os.chdir(self.d)
        self.saved = {k: getattr(C, k) for k in self.SAVE}
        C.now = lambda: self.when
        C.log = lambda *a, **k: self.logs.append(" ".join(str(x) for x in a))
        C.ODDS_KEY = FAKE_KEY
        return self

    def call(self, err, when=None):
        """One odds_get through the REAL code -> the exception it raised."""
        if when:
            self.when = at(when)

        def _get(url, timeout=30):
            raise err
        C.get = _get
        try:
            C.odds_get("/sports/americanfootball_nfl/odds", {"regions": "us"})
        except Exception as e:
            return e
        return None

    def doc(self):
        try:
            return json.load(open(REFUSED, encoding="utf-8"))
        except OSError:
            return None

    def __exit__(self, *a):
        for k, v in self.saved.items():
            setattr(C, k, v)
        os.chdir(self.cwd)
        shutil.rmtree(self.d, ignore_errors=True)


_BODY = json.dumps({"message": "API key is not valid: %s" % FAKE_KEY,
                    "error_code": "INVALID_KEY"}).encode()

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 A REFUSED CALL IS RECORDED, IN THE API'S WORDS, AND NEVER THE KEY")
# ══════════════════════════════════════════════════════════════════════
with Sandbox("2026-10-22T21:42:37Z") as box:
    _e = box.call(refusal(401, _BODY))
    ck("the call still raises the same HTTPError (Sam's 09-26 rule judges it, unchanged)",
       isinstance(_e, urllib.error.HTTPError) and _e.code == 401, repr(_e))
    eq(F.outside_source(_e), "HTTP 401 from the source",
       "   ...and it is still an OUTSIDE SOURCE to judge_failures")
    _d = box.doc() or {}
    ck("🔴🔴 odds-refused.json holds when, the status and the API's own reason",
       _d.get("at") == "2026-10-22T21:42:37Z" and _d.get("status") == 401
       and _d.get("error_code") == "INVALID_KEY" and "not valid" in (_d.get("message") or ""),
       "doc=%s" % _d)
    eq(_d.get("first_at"), "2026-10-22T21:42:37Z", "   ...and the run of refusals began then")
    _text = json.dumps(_d) + "\n".join(box.logs)
    ck("🔴🔴 the key is in neither the file nor the log (rule 10)", FAKE_KEY not in _text,
       "leaked in: %s" % ("file" if FAKE_KEY in json.dumps(_d) else "log"))
    ck("   ...and the log says the key was refused, with the reason",
       any("REFUSED the key: HTTP 401 INVALID_KEY" in ln for ln in box.logs), box.logs)
    eq(_d.get("request"), "/sports/americanfootball_nfl/odds",
       "   the request is the path alone, never its query")

    box.call(refusal(401, _BODY), when="2026-10-23T14:41:00Z")
    _d = box.doc() or {}
    eq((_d.get("at"), _d.get("first_at")), ("2026-10-23T14:41:00Z", "2026-10-22T21:42:37Z"),
       "🔴 a later refusal with no paid pull between keeps the time the run began")
    reading(".", "data/2026-10-23/gamelines/1727.json.gz", "2026-10-23T17:27:42Z", 19989)
    box.call(refusal(403, b"Forbidden"), when="2026-10-23T18:00:00Z")
    _d = box.doc() or {}
    eq((_d.get("status"), _d.get("first_at"), _d.get("message")),
       (403, "2026-10-23T18:00:00Z", "Forbidden"),
       "🔴 ...but after a paid pull landed, a new refusal starts a new run; a body that "
       "is not JSON is kept as the message")

with Sandbox("2026-10-23T12:00:00Z") as box:
    _e = box.call(refusal(500, b'{"message": "server error"}'))
    ck("🔴 a 500 is not a refusal of the key: raised, nothing recorded",
       isinstance(_e, urllib.error.HTTPError) and box.doc() is None, "doc=%s" % box.doc())
    _e = box.call(urllib.error.URLError("timed out"))
    ck("   ...nor is a network failure", box.doc() is None and _e is not None)

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 THE 10-23 OUTAGE, REPLAYED: BROKEN UNTIL A PAID PULL LANDS AFTER IT")
# ══════════════════════════════════════════════════════════════════════


def _check(tree, when):
    saved = W.ROOT
    try:
        W.ROOT = tree
        rep = W.Report()
        _CHECK(rep, at(when))
        return rep.items
    finally:
        W.ROOT = saved


_t = tempfile.mkdtemp(prefix="refused-wd-")
try:
    reading(_t, "data/ncaaf/2026-10-22/alt-lines/1932.json.gz", "2026-10-22T19:32:53Z", 11800)
    put(_t, "data/latest/odds-refused.json",
        {"at": "2026-10-23T14:40:12Z", "first_at": "2026-10-22T21:42:37Z", "status": 401,
         "error_code": "INVALID_KEY", "message": "API key is not valid: ***"})
    _f = _check(_t, "2026-10-23T14:41:30Z")
    ck("🔴🔴 at 14:41Z (health.json said DEGRADED) the refusal is BROKEN",
       [(i["key"], i["severity"]) for i in _f] == [("odds:refused", "BROKEN")],
       "findings=%s" % _f)
    _why = (_f[0]["why"] if _f else "")
    ck("   ...saying since when, the status, the API's reason and the newest good pull",
       all(s in _why for s in ("2026-10-22T21:42:37Z", "HTTP 401", "INVALID_KEY",
                               "2026-10-22T19:32:53Z")), _why)
    reading(_t, "data/ncaaf/2026-10-23/gamelines/1727.json.gz", "2026-10-23T17:27:42Z", 19989)
    eq(_check(_t, "2026-10-23T18:15:00Z"), [],
       "🔴 the first paid pull that works clears it, with no file to delete")
    put(_t, "data/latest/odds-refused.json", {"at": "2026-10-23T17:14:06Z", "status": 401})
    eq(_check(_t, "2026-10-23T18:15:00Z"), [],
       "   ...and a slower run's refusal pushed AFTER that pull, but stamped before it, "
       "stays quiet (the 16:59Z run, still on the old secret)")
    os.remove(os.path.join(_t, "data/latest/odds-refused.json"))
    eq(_check(_t, "2026-10-23T18:15:00Z"), [], "   no file, no finding")
finally:
    shutil.rmtree(_t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 THE ALERT GIVES SAM HIS STEPS, NOT A PROMPT FOR CLAUDE")
# ══════════════════════════════════════════════════════════════════════
_REC = {"key": "record-verify:mlb", "severity": "BROKEN", "repair": None,
        "what": "the MLB Track Record does not add up", "why": "..."}
_ODDS = {"key": "odds:refused", "severity": "BROKEN", "repair": None,
         "what": "the Odds API is refusing our key, so no new odds or props are coming in",
         "why": "..."}
_w = W.what_to_do([_REC, _ODDS], W.site_updating([_REC, _ODDS]))
ck("🔴🔴 with the MLB record listed FIRST, the refused key still leads, with Sam's steps",
   "**What is wrong:** the Odds API is refusing our key" in _w and "(and 1 more above)" in _w
   and "settings/secrets/actions" in _w and "ODDS_API_KEY" in _w and "Update secret" in _w,
   _w[:600])
ck("   ...and no prompt for Claude, which cannot fix a key", "paste this into Claude" not in _w)
ck("   ...and the steps never carry a key", FAKE_KEY not in _w)
ck("   'Is the site still updating?' says the odds and props are not",
   "Partly: the odds and props are not" in _w, _w[:400])
_w2 = W.what_to_do([_REC], W.site_updating([_REC]))
ck("   a code finding alone keeps the Claude prompt, unchanged",
   "paste this into Claude Code" in _w2 and "settings/secrets" not in _w2)
_doc = open(os.path.join(ROOT, "docs", "FIX-ODDS-KEY.md"), encoding="utf-8").read()
_steps = _doc.split("<!-- steps -->", 1)[-1].split("<!-- /steps -->", 1)[0].strip()
ck("🔴 the steps are docs/FIX-ODDS-KEY.md's own, quoted whole (one copy, which Sam can "
   "also read by itself)", len(_steps) > 200 and _steps in _w, _steps[:200])
_sd = getattr(W, "SRCDIR", ROOT)
_e = tempfile.mkdtemp(prefix="refused-nodoc-")
try:
    W.SRCDIR = _e
    _w3 = W.what_to_do([_ODDS], "")
finally:
    W.SRCDIR = _sd
    shutil.rmtree(_e, ignore_errors=True)
ck("   ...and with the doc unreadable, the alert still sends him to it, never to nothing",
   "docs/FIX-ODDS-KEY.md" in _w3, _w3[-300:])

_t = tempfile.mkdtemp(prefix="refused-run-")
_saved = (W.ROOT, W.CHECKS)
try:
    put(_t, "data/latest/odds-refused.json",
        {"at": "2026-10-23T14:40:12Z", "first_at": "2026-10-22T21:42:37Z", "status": 401})
    ck("🔴 the watchdog's own check list runs it", _CHECK in _saved[1])
    W.ROOT, W.CHECKS = _t, (_CHECK,)
    _out = W.run(at("2026-10-23T14:41:30Z"))
    ck("🔴 the report names it Sam's, and never asks an agent to fix it in code",
       _out.get("sam_only") == ["odds"] and "odds" not in (_out.get("unrepairable") or []),
       "sam_only=%s unrepairable=%s" % (_out.get("sam_only"), _out.get("unrepairable")))
    ck("   ...and it emails Sam (BROKEN)", W.alerting(_out))
    _body = W.render(_out)
    ck("   the issue body says only he can fix it and that it needs no code change",
       "only you can fix" in _body and "needs a code change" not in _body
       and "@claude" not in _body, _body[:700])
finally:
    W.ROOT, W.CHECKS = _saved
    shutil.rmtree(_t, ignore_errors=True)
