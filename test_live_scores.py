#!/usr/bin/env python3
"""
LIVE FOOTBALL SCORES — DRIVEN IN A REAL BROWSER, AGAINST A STUBBED FEED.

🔴 Sam, 2026-09-06: *"we have to make the scores live, we have to find a
way to make cfb and nfl scores and matchups live."*

The page now fetches ESPN's public scoreboard **itself**, exactly the way
the MLB tab has always polled `statsapi.mlb.com` — no collector, no stored
file, nothing to go stale. ⛔ So the behaviour under test lives IN THE
BROWSER, and this drives a real one and asserts on **cells and counts**,
never on prose (rule 69 — thirteen false failures on correct code so far).

WHAT IS PINNED, each one a way this could ship wrong:
  1. a game the feed calls IN PROGRESS shows the FEED's score and clock
  2. a game the feed did NOT return is left EXACTLY as it was
  3. a stored FINAL is not overwritten by the feed
  4. a disagreement about a final is PUBLISHED, not swallowed
  5. 🔴 a REFUSED fetch degrades to today's tab AND STOPS ASKING
  6. the join is keyed on the ID, so the RIGHT game goes live

⚠️ THE FIXTURE'S SHAPE IS THE ONE SAM'S OWN PROBE RUN CAPTURED on
2026-09-06 — `events[].competitions[0].status.type.state`, `displayClock`,
`period`, `competitors[].score`, `homeAway`. **All seven fields this code
reads were confirmed present in both leagues**, so this is a capture, not
a guess.

# `[2026-09-28]` §0b2: the page's merge on planted games, every run.
# @vacuity §0b2: the lifted merge actually runs
#   file: index.html
#   find: function fbMerge(g){
#   with: function fbMerge(g){ throw new Error('mutated');
#
# @vacuity §0b2: in progress shows the FEED's score
#   file: index.html
#   find: return { home: L.home, away: L.away, final: false, live: true,
#   with: return { home: g.home_score, away: g.away_score, final: false, live: true,
#
# @vacuity §0b2: a disagreeing final is carried out as a conflict
#   file: index.html
#   find: (L.home !== g.home_score || L.away !== g.away_score);
#   with: false;
#
# @vacuity §0b2: an agreeing final is NOT a conflict
#   file: index.html
#   find: (L.home !== g.home_score || L.away !== g.away_score);
#   with: true;
#
# @vacuity §0b2: a feed-only final shows the feed's score
#   file: index.html
#   find: : { home: L.home, away: L.away, final: true, live: false,
#   with: : { home: g.home_score, away: g.away_score, final: true, live: false,
#
# @vacuity §0b2: a game the feed does not carry is unchanged
#   file: index.html
#   find: if (!L) return { home: g.home_score, away: g.away_score, final: !!g.final,
#   with: if (!L) return { home: null, away: null, final: !!g.final,
#
# `[2026-09-28]` §0c: every browser test blocks the network (the class).
# @vacuity §0c: a browser test that loses its catch-all is caught
#   file: test_box_live.py
#   find: pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("http://127.0.0.1:", "http://localhost:")) else (_offsite.append(r.request.url), r.abort()))
#   with: pass
#
# @vacuity §0c: a catch-all left only in a COMMENT does not count
#   file: test_nfl_opener.py
#   find: pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("http://127.0.0.1:", "http://localhost:")) else (_offsite.append(r.request.url), r.abort()))
#   with: # pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("http://127.0.0.1:", "http://localhost:")) else (_offsite.append(r.request.url), r.abort()))
#
# `[Sam, 2026-10-01]` The tab prints no note about itself: fbLiveNote and
# the footer box it sat in are gone, so §0 and §4 require their ABSENCE.
# @vacuity §0: the Scores tab makes no claim about itself
#   file: index.html
#   find: <h2 style="margin:0 0 4px;font-size:16px">Scores &amp; Matchups</h2>
#   with: <h2 style="margin:0 0 4px;font-size:16px">Scores &amp; Matchups</h2>${fbLiveNote(shown)}
#
# @vacuity §0 + §4 (browser): a refused feed prints no 'unavailable' note
#   file: index.html
#   find: <h2 style="margin:0 0 4px;font-size:16px">Scores &amp; Matchups</h2>
#   with: <h2 style="margin:0 0 4px;font-size:16px">Scores &amp; Matchups</h2><div class="note">Live scores are not available in this browser.</div>
"""
import http.server
import json
import os
import socketserver
import threading

from jsblock import calls, js_block, source   # the ONE js reader
from tcheck import ck, note, shown   # the shared gate — see tcheck.py

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8913
ESPN = "**/site.api.espn.com/**"


def serve():
    """⚠️ A FRESH PORT EVERY RUN. A fixed one collides with whatever the
    last run left behind and the file dies before its first check — which
    the harness correctly calls a failure, not a skip."""
    os.chdir(ROOT)
    h = http.server.SimpleHTTPRequestHandler
    h.log_message = lambda *a, **k: None
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def payload(rows):
    """rows: [(id, state, clock, period, away_score, home_score)] -> ESPN JSON"""
    ev = []
    for gid, st, clock, period, away, home in rows:
        ev.append({
            "id": str(gid), "date": "2026-09-05T23:00Z",
            "competitions": [{
                "status": {
                    "displayClock": clock, "period": period,
                    "type": {"state": st,
                             "shortDetail": (f"{clock} - {period}Q"
                                             if st == "in" else "Final")}},
                "competitors": [
                    {"homeAway": "home", "score": None if home is None else str(home),
                     "team": {"displayName": "Home"}},
                    {"homeAway": "away", "score": None if away is None else str(away),
                     "team": {"displayName": "Away"}},
                ]}]})
    return {"events": ev, "season": {"year": 2026}, "week": {"number": 2}}


# ══════════════════════════════════════════════════════════════════════
# 🔴 THE STATIC HALF RUNS EVERYWHERE. THE BROWSER HALF RUNS WHERE THERE
#    IS A BROWSER.
# ══════════════════════════════════════════════════════════════════════
# ⛔ THIS FILE TURNED THE COLLECTOR RED ON ITS FIRST RUN. `[2026-09-06]`
# It imported Playwright at the top and, when the import failed, recorded
# a FAILING check — "a skipped check is not a passing one". **The GitHub
# runner installs a bare Python and has no Playwright**, so every run
# failed, and on a PUSH the test step BLOCKS: nothing was collected.
# 🔴 AND I HAD WRITTEN THE WARNING MYSELF ONE FILE EARLIER —
# `test_multileague.py` refuses to import PyYAML for exactly this reason
# and says so in its own docstring. **Knowing the rule is not the same as
# applying it, which is why the fix has to be structural.**
# ✅ SO: the checks that need no browser ALWAYS run, and they are real
# assertions about the live-score code rather than a placeholder. The
# browser checks run when a browser exists. ⛔ A file that records ZERO
# checks still fails (rule 116) — the static half guarantees it never
# records zero.
# ⚠️ AND THE SKIP IS LOUD. A silent skip is rule 116's defect wearing a
# portability excuse.
HTML = os.path.join(ROOT, "index.html")

print("\n═══ 0. THE LIVE LAYER, CHECKED WITHOUT A BROWSER ═══")
# 🔴 THE CHECK THAT WOULD HAVE CAUGHT THE WORST DEFECT OF THIS BUILD.
#    The live score was first wired into a `row` builder inside `fbScores`
#    that is NEVER CALLED — the tab renders `fbGameCard` nodes. The join
#    worked perfectly and the tab showed nothing.
card = js_block("fbGameCard", HTML)
ck("🔴 the live view is read INSIDE `fbGameCard` — the renderer that runs",
   "fbMerge(g)" in card,
   "⛔ a renderer nobody calls looks exactly like the one that does")
ck("...and `fbGameCard` is actually called by the Scores tab",
   calls("fbGameCard", HTML) >= 1, "%d call site(s)" % calls("fbGameCard", HTML))
ck("the score slot renders the MERGED numbers, not the stored ones",
   "side(g.away, M.away, false)" in card and "side(g.home, M.home, true)" in card,
   "a live score has to reach the same slot a final uses")

loader = js_block("fbLiveLoad", HTML)
ck("⛔ one refusal turns the feed OFF for the session",
   "FB_LIVE_OFF = true" in loader,
   "otherwise a blocked feed is a request every 45s for as long as the "
   "tab is open")
ck("...and the poll is guarded on it",
   "FB_LIVE_OFF) return" in source(HTML),
   "the guard has to be at the interval too, not only in the loader")

joiner = js_block("fbLiveOf", HTML)
ck("🔴 the join is keyed on the ID, never a team name (rule 54)",
   "g.espn || g.id" in joiner and "home" not in joiner.split("return")[0],
   joiner.strip().splitlines()[-2].strip() if joiner else "")

merge = js_block("fbMerge", HTML)
ck("a stored final wins over the feed's",
   "home: g.home_score, away: g.away_score, final: true" in merge,
   "it is what the Track Record grades against")
ck("...and a disagreement is carried out of the merge, not dropped",
   "conflict" in merge and "theirs" in merge)
ck("a game the feed does not carry is returned UNCHANGED",
   "if (!L) return { home: g.home_score, away: g.away_score" in merge,
   "⛔ never blanked on the strength of an absence")

# ⚠️ SCOPED TO THE FUNCTION THAT RENDERS THE NOTE, not the whole file.
# ⛔ The first version searched all of `index.html` and failed on the
# COMMENT that explains why the old sentence was removed — a substring
# check firing on prose about the change rather than the change. Rule 69,
# in the test I wrote to enforce rule 132.
_scores = js_block("fbScores", HTML)
# [Sam, 2026-10-01] ~~"the tab's claim about itself is COMPUTED, not
#    written" (`${fbLiveNote(shown)}`)~~ — the tab makes NO claim about
#    itself any more: Sam removed every explanation box, and fbLiveNote went
#    with the footer note it filled. ✅ The old fixed sentence stays gone,
#    and the live state reaches the reader through the cards themselves —
#    LIVE, the feed's clock and score (sections 2-3).
ck("the tab makes no claim about itself, computed or written",
   "fbLiveNote(" not in _scores and calls("fbLiveNote", HTML) == 0
   and "Not a live scoreboard." not in _scores
   and "not available in this browser" not in _scores
   and 'class="note"' not in _scores,
   "the old fixed sentence was true when written and false the day ESPN "
   "was wired in (rule 132); since 2026-10-01 the tab prints neither")
ck("the football poll reuses MLB's own 45s, not a second number",
   "const FB_LIVE_MS = 45000;" in source(HTML), "one value, one meaning")


# ───────────────────────────────────────────────────────────────
print("\n═══ 0b. 🔴 THE SCOREBOARD MUST BE ASKED FOR BY DIVISION ═══")
# ⛔ WHAT SHIPPED FIRST ASKED FOR THE DEFAULT SCOREBOARD AND GOT A QUARTER
#    OF THE SLATE. Measured live in a browser 2026-09-06:
#        college ?limit=400          25 events
#        college ?groups=80 (FBS)    99
#        college ?groups=81 (FCS)   159
#        NFL     ?limit=400          16
#        NFL     ?groups=80           0   <- never send it here
_ll = js_block("fbLiveLoad", HTML)
_src = source(HTML)
ck("🔴 college asks for BOTH Division I groups",
   "FB_LIVE_GROUPS = { ncaaf: ['80', '81']" in _src,
   "the default scoreboard returned 25 of the 103 games the tab shows")
ck("⛔ the NFL is NOT sent a `groups` parameter",
   "nfl: [null]" in _src,
   "measured: NFL + groups=80 returns 0 events, which would have turned "
   "the NFL live layer off while reporting nothing wrong")
ck("...and the parameter is only appended when there is one",
   "${g ? '&groups=' + g : ''}" in _ll)
ck("the divisions are fetched in parallel and merged by event id",
   "Promise.all(qs.map" in _ll and "concat(x.events || [])" in _ll,
   "ESPN's ids cannot collide, so a merge is a union")
ck("🔴 one bad STATUS keeps the other division; a REFUSAL still turns it off",
   "rs.filter(r => r.ok)" in _ll and "if (!oks.length) throw" in _ll,
   "CORS is decided per origin, not per query string")

# ───────────────────────────────────────────────────────────────
print("\n═══ 0b2. THE MERGE, DRIVEN ON PLANTED GAMES — EVERY RUN ═══")
# 🔴 `[2026-09-28]` THE BROWSER SECTIONS TAKE THEIR GAMES FROM THE LIVE
#    SCHEDULE, so section 3 (a stored final the feed disagrees with) only
#    runs when this week's view happens to hold a final — from a Sunday
#    until the next midweek game it does not, and it says so. ✅ The rule it
#    drives lives in `fbMerge`, a pure function of the stored game and the
#    feed, so it is lifted out of the page and run in node on planted games
#    — in progress, a disagreeing final, an agreeing final, a feed-only
#    final, and a game the feed does not carry — whatever the week holds.
import subprocess as _sp  # noqa: E402
import tempfile as _tf    # noqa: E402
_mjs = "\n".join([
    "let FB_DAY = null;",
    "let FB_LIVE = { byId: {",
    "  '1': { state: 'in', clock: '7:21', period: 3, home: 24, away: 17 },",
    "  '2': { state: 'post', home: 98, away: 99 },",
    "  '3': { state: 'post', home: 30, away: 10 },",
    "  '4': { state: 'post', home: 21, away: 20 } } };",
    js_block("fbLiveOf", HTML), js_block("fbMerge", HTML),
    "const G = [",
    "  { espn: '1', final: false, home_score: null, away_score: null },",
    "  { espn: '2', final: true, home_score: 31, away_score: 28 },",
    "  { espn: '3', final: true, home_score: 30, away_score: 10 },",
    "  { espn: '4', final: false, home_score: null, away_score: null },",
    "  { espn: '5', final: true, home_score: 7, away_score: 3 } ];",
    "console.log(JSON.stringify(G.map(fbMerge)));",
])
_md = _tf.mkdtemp()
try:
    _mp = os.path.join(_md, "merge.js")
    open(_mp, "w", encoding="utf-8").write(_mjs)
    _mr = _sp.run(["node", _mp], capture_output=True, text=True)
finally:
    import shutil as _sh  # noqa: E402
    _sh.rmtree(_md, ignore_errors=True)
_M = json.loads(_mr.stdout.strip().splitlines()[-1]) if _mr.returncode == 0 else None
ck("the page's own merge runs on planted games", _M is not None,
   shown(_mr.stderr[-300:]) if _mr.returncode else "")
if _M:
    ck("🔴 in progress: the FEED's score and clock, marked live",
       (_M[0]["home"], _M[0]["away"], _M[0]["live"], _M[0].get("clock"))
       == (24, 17, True, "7:21"), str(_M[0]))
    ck("🔴 a stored FINAL keeps OUR score when the feed disagrees — and the "
       "disagreement is carried out, with the feed's numbers",
       (_M[1]["home"], _M[1]["away"], _M[1]["final"], _M[1]["conflict"],
        _M[1].get("theirs")) == (31, 28, True, True, "99-98"), str(_M[1]))
    ck("⛔ ...an agreeing final is not a disagreement",
       (_M[2]["home"], _M[2]["conflict"]) == (30, False), str(_M[2]))
    ck("a final only the feed has shows the feed's, marked as from the feed",
       (_M[3]["home"], _M[3]["away"], _M[3]["final"], _M[3].get("fromFeed"))
       == (21, 20, True, True), str(_M[3]))
    ck("⛔ a game the feed does not carry is returned UNCHANGED",
       (_M[4]["home"], _M[4]["away"], _M[4]["covered"], _M[4]["live"])
       == (7, 3, False, False), str(_M[4]))

# ───────────────────────────────────────────────────────────────
print("\n═══ 0c. 🔴 NO BROWSER TEST REACHES THE NETWORK — THE CLASS ═══")
# ⛔ `[2026-09-28]` Sam: "A test must not depend on the network; use
#    recorded fixtures." All five browser tests routed ONLY site.api.espn.com,
#    while every page load boots the MLB tab (statsapi.mlb.com) and asks
#    mlbstatic/espncdn for logos — real third-party answers reaching the
#    "no page error" checks. Each now registers a catch-all FIRST that lets
#    this machine through and aborts everything else (the page copes with a
#    feed it cannot reach), so the stubs registered after it still win.
# ✅ THE CLASS, NOT THE FIVE: every test file that imports Playwright must
#    carry that line, on code (not a comment), before its first other
#    route — a new browser test without it fails here. Runs without a
#    browser, so the collector's runner asks it too.
# ⚠️ The pattern is assembled from two pieces so this file's own guard text
#    can never be the match that satisfies it (rules 67, 244).
import glob as _glob  # noqa: E402
import re as _re      # noqa: E402
_CATCH_ALL = ('.route("**/*", lambda r: r.continue_() if r.request.url.startswith('
              + '("http://127.0.0.1:", "http://localhost:")) else (')
_A_ROUTE = _re.compile(r"\bpg\.route\(")      # a real call, not this text


def _first(lines, pred):
    return next((i for i, l in enumerate(lines)
                 if not l.lstrip().startswith("#") and pred(l)), None)


_net = {}
for _p in sorted(_glob.glob(os.path.join(ROOT, "test_*.py"))):
    _s = open(_p, encoding="utf-8").read()
    if "sync_playwright" not in _s:
        continue
    _ls = _s.splitlines()
    _ic = _first(_ls, lambda l: _CATCH_ALL in l)
    _io = _first(_ls, lambda l: _A_ROUTE.search(l) and _CATCH_ALL not in l)
    _net[os.path.basename(_p)] = (_ic is not None
                                  and (_io is None or _ic < _io))
ck("⚠️ the browser tests were found to ask about", len(_net) >= 5,
   "⛔ a sweep over no files passes having asked nothing (rule 67). "
   "found: %s" % sorted(_net))
ck("🔴 every browser test blocks the network before its first stub",
   _net and all(_net.values()),
   "without it a third party's answer decides a check. missing or out of "
   "order: %s" % sorted(k for k, v in _net.items() if not v))
OFFSITE = []

srv, PORT = serve()
try:
    from playwright.sync_api import sync_playwright
    _BROWSER = True
except ImportError:
    _BROWSER = False
    note("⚠️ NO BROWSER HERE — sections 1-5 did not run. That is expected "
         "on the collector's runner, which installs a bare Python. The "
         "static checks above ran and are real; a browser-capable "
         "environment runs all of it.")

class Page:
    """One browser page, with the ESPN feed stubbed to whatever we say."""

    def __init__(self, br, body=None, fail=False):
        self.errs = []
        self.hits = [0]
        self.pg = br.new_page(viewport={"width": 1400, "height": 1100})
        self.pg.on("pageerror", lambda e: self.errs.append(str(e)))
        # ⛔ NO REQUEST LEAVES THIS MACHINE. `[2026-09-28]` Sam: "A test
        #    must not depend on the network." Every page boots the MLB tab
        #    (statsapi.mlb.com) and asks mlbstatic/espncdn for logos; only
        #    ESPN was stubbed. Registered FIRST — Playwright tries the
        #    newest route first — so the ESPN handler below still answers
        #    its own URLs; anything else off this machine is aborted (the
        #    page already copes with a feed it cannot reach) and counted.
        #    §0 of this file fails if a browser test loses this line.
        _offsite = OFFSITE
        self.pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("http://127.0.0.1:", "http://localhost:")) else (_offsite.append(r.request.url), r.abort()))

        def handler(route):
            self.hits[0] += 1
            if fail:
                # ⚠️ WHAT A CORS REFUSAL ACTUALLY LOOKS LIKE TO JS: the
                # request fails with no useful detail. `abort` reproduces
                # that far better than an HTTP error code would.
                route.abort("failed")
            else:
                route.fulfill(status=200, content_type="application/json",
                              body=json.dumps(body or {"events": []}))
        self.pg.route(ESPN, handler)

    def open(self, league="College Football"):
        self.pg.goto(f"http://127.0.0.1:{PORT}/index.html",
                     wait_until="domcontentloaded", timeout=60000)
        self.pg.wait_for_timeout(1500)
        self.pg.get_by_text(league, exact=True).first.click()
        self.pg.wait_for_timeout(700)
        self.pg.locator("nav.subnav a[data-tab='scores']").click()
        # 🔴 WAIT FOR A STATE, NOT A CLOCK. `[fixed 2026-09-06]` A fixed
        # 2.5s sleep passed twice and failed once on the SAME code — the
        # college schedule is 3,679 games and the render is not always
        # finished when the timer is. ⛔ A flaky test is worse than no
        # test: it teaches you to re-run instead of to look.
        self.pg.wait_for_function(
            "() => window.__fbShown && window.__fbShown.length > 0",
            timeout=30000)
        # ⚠️ …and one frame for the cards, which are appended AFTER the
        # hook is set (they carry click handlers, so they are nodes).
        self.pg.wait_for_function(
            "() => document.querySelectorAll('#fbview .fbcards .g').length"
            " === (window.__fbShown || []).length", timeout=30000)
        return self

    def shown(self):
        return self.pg.evaluate("() => window.__fbShown || []")

    def score_cells(self):
        """🔴 THE SCORE SLOT ONLY — `.sc` — not the whole card.
        ⛔ The first version asked whether the feed's number appeared
        ANYWHERE in the card text and failed a correct render, because the
        card also PUBLISHES the disagreement ("live feed says 99-98").
        **That is rule 69 again: assert on the cell, not the prose.**"""
        return self.pg.evaluate(
            """() => [...document.querySelectorAll('#fbview .fbcards .g')]
                 .map(c => (c.querySelector('.sc') || {}).innerText || '')""")

    def rows_text(self):
        # ⛔ THE CARDS, NOT A TABLE. This tab renders `fbGameCard` nodes —
        # the first version of this test read `table.fbt tbody tr`, found
        # zero rows, and would have reported a working feature broken.
        return self.pg.evaluate(
            """() => [...document.querySelectorAll('#fbview .fbcards .g')]
                 .map(c => c.innerText.replace(/\\s+/g, ' ').trim())""")

    def close(self):
        self.pg.close()


if _BROWSER:
  with sync_playwright() as br_ctx:
      br = br_ctx.chromium.launch(args=["--proxy-bypass-list=<-loopback>"])

      # ═══════════════════════════════════════════════════════════════
      print("\n═══ 1. A FEED WITH NOTHING IN IT CHANGES NOTHING ═══")
      # ⛔ THE BASELINE, AND IT IS THE MOST IMPORTANT ONE. If the live layer
      #    can damage the tab when the feed is empty, it can damage it any
      #    time the feed is thin — and the feed IS thin: 25 events on a day
      #    our schedule held 206 college games.
      base = Page(br, body={"events": []}).open()
      b_rows = base.rows_text()
      b_shown = base.shown()
      ck("the Scores tab renders rows", len(b_rows) > 0, "%d rows" % len(b_rows))
      ck("no page error", not base.errs, str(base.errs[:1]))
      ck("⛔ and NOT ONE game is marked live off an empty feed",
         not any(g["live"] for g in b_shown),
         "%d of %d rows" % (sum(1 for g in b_shown if g["live"]), len(b_shown)))
      base_cells = base.score_cells()
      ids = [g["id"] for g in b_shown]
      ck("the rows carry a join key at all", all(ids), "%d ids" % len(ids))
      base.close()

      # ═══════════════════════════════════════════════════════════════
      print("\n═══ 2. 🔴 ONE GAME IN PROGRESS — THE FEED'S SCORE AND CLOCK ═══")
      target = ids[0]
      live = Page(br, body=payload([(target, "in", "7:21", 3, 17, 24)])).open()
      l_shown = live.shown()
      lives = [g for g in l_shown if g["live"]]
      ck("🔴 exactly ONE game went live, and it is the one the feed named",
         len(lives) == 1 and lives[0]["id"] == target,
         "live=%s target=%s" % ([g["id"] for g in lives], target))
      row = [r for r in live.rows_text() if "7:21" in r]
      ck("the row shows the feed's CLOCK", len(row) == 1, "%d rows carry it" % len(row))
      ck("...and the feed's SCORE, both sides",
         len(row) == 1 and "17" in row[0] and "24" in row[0], (row[0][:90] if row else ""))
      ck("...and it is labelled LIVE", len(row) == 1 and "LIVE" in row[0].upper(),
         (row[0][:60] if row else ""))
      # ⛔ EVERY OTHER ROW MUST BE UNTOUCHED — the feed returned ONE game.
      # ⛔ THE FEED RETURNED ONE GAME, SO EXACTLY ONE SCORE CELL MAY MOVE.
      _lc = live.score_cells()
      _moved = [i for i in range(len(base_cells)) if _lc[i] != base_cells[i]]
      ck("⛔ exactly ONE score cell changed, and it is the live game's",
         len(_moved) == 1 and live.shown()[_moved[0]]["id"] == target,
         "cells changed: %s" % [(base_cells[i], _lc[i]) for i in _moved][:3])
      live.close()

      # ═══════════════════════════════════════════════════════════════
      print("\n═══ 3. A STORED FINAL STAYS OURS, AND A DISAGREEMENT IS SHOWN ═══")
      # 🔴 The stored score is what the Track Record grades against. Two
      #    surfaces disagreeing about a final is the defect rule 66 exists
      #    to stop — but silently picking one hides a real data problem, so
      #    the row has to SAY there is a disagreement.
      finals = [g for g, r in zip(b_shown, b_rows) if "FINAL" in r.upper()]
      if not finals:
          note("no final in this week's stored view, so the disagreement case "
               "could not be driven here")
      else:
          f0 = finals[0]["id"]
          stored_row = [r for g, r in zip(b_shown, b_rows) if g["id"] == f0][0]
          dis = Page(br, body=payload([(f0, "post", "0:00", 4, 99, 98)])).open()
          d_row = [r for g, r in zip(dis.shown(), dis.rows_text()) if g["id"] == f0][0]
          d_sc = [s for g, s in zip(dis.shown(), dis.score_cells())
                  if g["id"] == f0][0]
          ck("🔴 the SCORE SLOT still holds the stored final, not the feed's",
             "99" not in d_sc and "98" not in d_sc,
             "the slot reads %r" % d_sc)
          ck("...and the row PUBLISHES that the feed disagrees",
             "99" in d_row.replace("99", "99") and "disagree" in d_row.lower()
             or "live feed says" in d_row.lower(), d_row[:110])
          ck("...and the stored numbers are still the ones rendered",
             all(tok in d_row for tok in stored_row.split()[:2]), d_row[:90])
          dis.close()

      # ═══════════════════════════════════════════════════════════════
      print("\n═══ 4. 🔴 A REFUSED FETCH — TODAY'S TAB, AND IT STOPS ASKING ═══")
      # ⛔ THE CASE THAT DECIDES WHETHER THIS IS SAFE TO SHIP AT ALL. Nobody
      #    knows yet whether the browser is allowed to fetch ESPN — a server
      #    request sends no Origin, so the probe could not settle it. If the
      #    answer is no, the tab must be EXACTLY what it is today.
      off = Page(br, fail=True).open()
      o_rows = off.rows_text()
      # ⚠️ COMPARED ON THE SCORE CELLS AND THE GAME LIST, NOT ON CARD TEXT.
      # ⛔ Card text includes each logo's ALT fallback, which appears only
      # while the image has not loaded — outbound images are blocked in this
      # sandbox, so that text RACES and produced a red run on correct code.
      # `[rule 69 once more: assert on the cell]`
      ck("🔴 the tab still renders every game it renders today",
         [g["id"] for g in off.shown()] == [g["id"] for g in b_shown],
         "%d vs %d games" % (len(off.shown()), len(b_shown)))
      ck("...with every score cell unchanged",
         off.score_cells() == base_cells,
         "%d cells" % len(base_cells))
      ck("no page error escaped", not off.errs, str(off.errs[:1]))
      ck("nothing is marked live", not any(g["live"] for g in off.shown()))
      # [Sam, 2026-10-01] ~~"the page says live scores are unavailable IN
      #    THIS BROWSER"~~ — that sentence was fbLiveNote's, in the tab's note
      #    box, and the page prints no notes any more. ✅ What it protected is
      #    kept: the reader is shown today's tab exactly (the checks above),
      #    and the page itself knows the feed is off.
      ck("the page prints no 'unavailable' note — and knows the feed is off",
         "not available in this browser" not in off.pg.inner_text("#fbview").lower()
         and off.pg.locator("#fbview .note").count() == 0
         and off.pg.evaluate("() => FB_LIVE_OFF") is True,
         "the reader sees the stored tab, unchanged, with no note about it")
      hits_after_render = off.hits[0]
      off.pg.wait_for_timeout(3000)
      ck("⛔ and it STOPS ASKING after one refusal",
         off.hits[0] == hits_after_render,
         "%d request(s) total — a blocked feed must not become a request "
         "storm every 45s for as long as the tab is open" % off.hits[0])
      off.close()

      # ═══════════════════════════════════════════════════════════════
      print("\n═══ 5. THE NFL SIDE USES THE SAME PATH ═══")
      nfl = Page(br, body={"events": []}).open("NFL")
      n_shown = nfl.shown()
      ck("the NFL Scores tab renders", len(nfl.rows_text()) > 0,
         "%d rows" % len(nfl.rows_text()))
      ck("no page error", not nfl.errs, str(nfl.errs[:1]))
      # ⚠️ THE NFL JOIN KEY IS nflverse's `espn` COLUMN, and the stored file
      #    only gains it on the next Tuesday rebuild (rule 104). Until then
      #    the id is `2026_01_NE_SEA` and the feed simply will not match —
      #    which must be a quiet no-op, never a broken tab.
      have_espn = sum(1 for g in n_shown if str(g["id"]).isdigit())
      note("NFL rows whose join key is already an ESPN id: %d of %d "
           "(the rest arrive with Tuesday's rebuild)" % (have_espn, len(n_shown)))
      ck("⛔ an unmatched NFL key is a no-op, not a broken row",
         not any(g["live"] for g in n_shown) and not nfl.errs)
      nfl.close()
      note("%d off-machine request(s) blocked, none answered by the "
           "network: %s" % (len(OFFSITE),
                            sorted({u.split("/")[2] for u in OFFSITE})))

      br.close()
srv.shutdown()
