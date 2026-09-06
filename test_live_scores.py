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
"""
import http.server
import json
import os
import socketserver
import threading

from tcheck import ck, note   # the shared gate — see tcheck.py

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


srv, PORT = serve()
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    ck("a browser is available to drive the page", False,
       "⛔ playwright missing — a skipped check is not a passing one")
    raise SystemExit(1)


class Page:
    """One browser page, with the ESPN feed stubbed to whatever we say."""

    def __init__(self, br, body=None, fail=False):
        self.errs = []
        self.hits = [0]
        self.pg = br.new_page(viewport={"width": 1400, "height": 1100})
        self.pg.on("pageerror", lambda e: self.errs.append(str(e)))

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
        self.pg.locator("#fbview a[data-fbtab='scores']").click()
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
    ck("the page says live scores are unavailable IN THIS BROWSER",
       "not available in this browser" in off.pg.inner_text("#fbview").lower(),
       "the reader is told, rather than shown a tab that looks broken")
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

    br.close()
srv.shutdown()
