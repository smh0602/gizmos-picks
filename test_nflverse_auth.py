#!/usr/bin/env python3
"""🔴🔴 nflverse IS ASKED WITH A TOKEN, AND THE TOKEN GOES NOWHERE ELSE.

`[measured 2026-09-19]` every NFL build had been failing for 47 hours:

    $ cat data/nfl/latest/backfill-report.txt
    nfl-logs back-fill at 2026-09-19T07:38:29Z
    requested: [2026]   written: []   failed: [2026]
    --- 2026 ---
    HTTPError: HTTP Error 403: rate limit exceeded

    $ cat data/nfl/latest/schedule-probe-2026.json
    {"usable": false, "error": "HTTPError: HTTP Error 403: rate limit
     exceeded", "written_at": "2026-09-19T07:38:29Z"}

What that cost, measured on the tree:
  · `players-2026.json.gz` holds **week 1 only** while
    `schedule-2026.json.gz` already records finals for weeks **1 and 2**
  · `vs-position-2026.json.gz` has `defences: {}`
  · `top-probe-2026.json` — the NFL possession artifact the dossier's §6
    needs — has **never been written, not once**
  · NFL `fb-scores` ran 3.5h stale while college's was 25m

nflverse publishes through `api.github.com`. An unauthenticated GitHub
API call is capped at **60 requests an hour per IP**, and an Actions
runner shares that IP. Football converges ~46 times a day and each pass
asks for up to ten pages of releases. **We were rate-limiting ourselves
out of our own data.**

✅ TWO HALVES, AND BOTH ARE NEEDED.
  1. `GITHUB_TOKEN` raises the ceiling to 1,000/hour. No new secret.
  2. `nfl-logs` now STANDS DOWN after a failure, exactly as `cfb-probe`
     already does, so a source outage stops being a retry storm that
     guarantees the next attempt fails too.

⛔ AND THE TOKEN IS SENT TO api.github.com AND NOWHERE ELSE. A release
asset redirects to `objects.githubusercontent.com`, and urllib re-sends
headers across a redirect — a token attached to an asset URL is a token
handed to a CDN. §2 drives a REAL redirect between two hostnames and
fails if the header survives it.

⚠️ WHAT THIS FILE DOES NOT CLAIM: that the token clears the production
403. That cannot be measured from here — this sandbox's own egress proxy
refuses `api.github.com` for repositories outside its allow-list, so the
403 visible from here is not GitHub's. What IS measured is that the
header reaches the API host, never reaches the redirect target, and that
a refusal is loud either way.

# @vacuity 🔴🔴 the releases API is asked with a token
#   file: nfl.py
#   find:     if tok and host.lower() in API_HOSTS:
#   with:     if False:
#
# @vacuity 🔴🔴 ...and the token never survives a redirect off the API host
#   file: nfl.py
#   find:             if host not in API_HOSTS:
#   with:             if False:
#
# @vacuity 🔴 nfl-logs stands down after a failure instead of storming
#   file: collect.py
#   find:             _nwait = _cfb_backoff_left(f"{base}/backfill-report.txt")
#   with:             _nwait = 0
#
# @vacuity ⛔ ...and a stand-down does not overwrite the report it reads
#   file: collect.py
#   find:             if _nwait <= 0:
#   with:             if True:
"""
import datetime
import io
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import collect
import nfl
from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
SEEN = []          # (host_header, path, authorization)


class _H(BaseHTTPRequestHandler):
    """403s without a bearer token; 302s off-host on /redirect."""

    def do_GET(self):
        SEEN.append((self.headers.get("Host", ""), self.path,
                     self.headers.get("Authorization")))
        if self.path.startswith("/redirect"):
            self.send_response(302)
            self.send_header("Location", self.server.elsewhere)
            self.end_headers()
            return
        if self.path.startswith("/landing"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"landed": true}')
            return
        if not self.headers.get("Authorization"):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'{"message": "rate limit exceeded"}')
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'[{"tag_name": "stats_player"}]')

    def log_message(self, *a):          # keep the test output readable
        pass


def serve():
    srv = HTTPServer(("127.0.0.1", 0), _H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# ════════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 THE API CALL CARRIES THE TOKEN — DRIVEN, NOT READ")
# ════════════════════════════════════════════════════════════════════════
ck("⛔ the real API host list names api.github.com and nothing else",
   tuple(nfl.API_HOSTS) == ("api.github.com",),
   "🔴 the drives below repoint this at a loopback server, so the real "
   "value has to be asserted separately or they prove nothing about "
   "production (rule 67). got %r" % (nfl.API_HOSTS,))
ck("⛔ ...and the CDN that serves the assets is NOT on it",
   "objects.githubusercontent.com" not in nfl.API_HOSTS
   and "github.com" not in nfl.API_HOSTS,
   "🔴 a release asset redirects there. A token on that host is a token "
   "given away. got %r" % (nfl.API_HOSTS,))

srv = serve()
port = srv.server_address[1]
_old_hosts, _old_env = nfl.API_HOSTS, os.environ.get("GITHUB_TOKEN")
try:
    os.environ["GITHUB_TOKEN"] = "TESTTOKEN"
    # ── anonymous first: the server answers exactly as GitHub did
    nfl.API_HOSTS = ("nowhere.invalid",)
    SEEN[:] = []
    err = None
    try:
        nfl._raw("http://127.0.0.1:%d/releases" % port, timeout=10)
    except Exception as e:
        err = e
    ck("🔴 without the token the source answers 403, as it did in production",
       err is not None and "403" in str(err),
       "⛔ if the stub cannot reproduce the failure, the pass below "
       "proves nothing. got %r" % (err,))
    ck("   ...and no Authorization header was sent",
       SEEN and SEEN[-1][2] is None,
       "got %r" % (SEEN[-1][2] if SEEN else None,))

    # ── and now with the host on the list
    nfl.API_HOSTS = ("127.0.0.1",)
    SEEN[:] = []
    body = nfl._raw("http://127.0.0.1:%d/releases" % port, timeout=10)
    ck("🔴🔴 with the token the same call succeeds",
       b"stats_player" in body,
       "⛔ THIS IS THE FIX. got %r" % (body[:60],))
    ck("   ...and the header really was `Bearer <token>`",
       SEEN and SEEN[-1][2] == "Bearer TESTTOKEN",
       "⛔ a header the server never saw is a fix that exists only in "
       "the diff. got %r" % (SEEN[-1][2] if SEEN else None,))

    # ══════════════════════════════════════════════════════════════════
    section("2. ⛔ AND IT DOES NOT SURVIVE A REDIRECT OFF THE API HOST")
    # ══════════════════════════════════════════════════════════════════
    other = serve()
    oport = other.server_address[1]
    srv.elsewhere = "http://localhost:%d/landing" % oport
    other.elsewhere = ""
    SEEN[:] = []
    got = nfl._raw("http://127.0.0.1:%d/redirect" % port, timeout=10)
    hops = [s for s in SEEN]
    ck("⚠️ the redirect really was followed to the other host",
       b"landed" in got and len(hops) == 2
       and hops[0][0].startswith("127.0.0.1")
       and hops[1][0].startswith("localhost"),
       "⛔ a redirect that never happened cannot prove the header was "
       "stripped (rule 67). hops=%r" % ([h[:2] for h in hops],))
    ck("🔴🔴 the first hop carried the token",
       hops and hops[0][2] == "Bearer TESTTOKEN",
       "got %r" % (hops[0][2] if hops else None,))
    ck("🔴🔴 ...and the SECOND hop did not",
       len(hops) > 1 and hops[1][2] is None,
       "⛔ urllib re-sends headers across a redirect by default. A "
       "release asset redirects to objects.githubusercontent.com, so "
       "this is the difference between authenticating and leaking. "
       "got %r" % (hops[1][2] if len(hops) > 1 else None,))
    other.shutdown()
finally:
    nfl.API_HOSTS = _old_hosts
    if _old_env is None:
        os.environ.pop("GITHUB_TOKEN", None)
    else:
        os.environ["GITHUB_TOKEN"] = _old_env
    srv.shutdown()

# ════════════════════════════════════════════════════════════════════════
section("3. 🔴 AND A FAILURE STANDS THE NEXT PASS DOWN")
# ════════════════════════════════════════════════════════════════════════
tmp = tempfile.mkdtemp(prefix="nflbackoff-")


def report(when, failed="[]", notyet="[]"):
    p = os.path.join(tmp, "backfill-report.txt")
    io.open(p, "w", encoding="utf-8").write(
        "nfl-logs back-fill at %s\nrequested: [2026]\nwritten  : []\n"
        "failed   : %s\nnot yet  : %s\n\n--- 2026 ---\n"
        "HTTPError: HTTP Error 403: rate limit exceeded\n"
        % (when, failed, notyet))
    return p


just = datetime.datetime.now(datetime.timezone.utc).isoformat()
ck("🔴 a fresh 403 leaves back-off on the clock",
   collect._cfb_backoff_left(report(just, failed="[2026]")) > 0,
   "⛔ 46 football passes a day against a 60-per-hour limit IS the "
   "outage. %0.f min left"
   % collect._cfb_backoff_left(report(just, failed="[2026]")))
ck("✅ ...and a report with nothing failed does not block anything",
   collect._cfb_backoff_left(report(just)) == 0,
   "⛔ a back-off that never clears is an outage of its own making")
ck("⚠️ the same function serves both leagues — one implementation",
   collect._cfb_backoff_left(os.path.join(tmp, "nope.txt")) == 0,
   "🔴 rule 117. The name is historical; it is path-driven, and "
   "`nfl-logs` writes a report of exactly the shape it parses.")

# ── DRIVEN: the deployed mode, standing down, fetching nothing
d = tempfile.mkdtemp(prefix="nflmode-")
os.makedirs(os.path.join(d, "data", "nfl", "latest"))
shutil.copy(report(just, failed="[2026]"),
            os.path.join(d, "data", "nfl", "latest", "backfill-report.txt"))
_before = io.open(os.path.join(d, "data/nfl/latest/backfill-report.txt"),
                  encoding="utf-8").read()
r = subprocess.run([sys.executable, os.path.join(ROOT, "collect.py"),
                    "nfl-logs", "converge-off"], cwd=d,
                   capture_output=True, text=True, timeout=300,
                   env=dict(os.environ, PYTHONPATH=ROOT, SEASON="2026",
                            ODDS_API_KEY="", CFB_BACKOFF_MIN="180"))
out = (r.stdout or "") + (r.stderr or "")
_after = io.open(os.path.join(d, "data/nfl/latest/backfill-report.txt"),
                 encoding="utf-8").read()
ck("🔴🔴 the deployed mode SKIPS while the back-off is on the clock",
   "SKIPPING nfl-logs" in out,
   "⛔ driven, not read — this is the real `collect.py nfl-logs`. "
   "tail: %r" % (out[-240:],))
ck("⛔ ...and it fetched nothing at all",
   "NOTHING FETCHED" in out and "back-filling seasons" in out,
   "⛔ a stand-down that still downloads is the storm with extra steps. "
   "tail: %r" % (out[-240:],))
ck("🔴🔴 ...and it did NOT overwrite the report the back-off reads",
   _after == _before,
   "⛔ THE SUBTLE ONE. The streak lives in that file. Rewriting it with "
   "an empty attempt clears the back-off and restores the storm on the "
   "very next pass.")
ck("✅ ...and a deliberate stand-down is not an error exit",
   r.returncode == 0,
   "⛔ 46 red runs a day for an outage already diagnosed is how an alarm "
   "gets ignored — the same reversal cfb-probe made on 2026-09-09. The "
   "artifact stays out of contract and verify_freshness still reports "
   "it. rc=%s" % r.returncode)
shutil.rmtree(d, ignore_errors=True)
shutil.rmtree(tmp, ignore_errors=True)
note("nfl-logs now shares cfb-probe's back-off: one implementation, two "
     "leagues, and the report it reads is never clobbered by a pass that "
     "did not run.")
