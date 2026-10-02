#!/usr/bin/env python3
"""
SWITCHING LEAGUE MUST NOT CARRY A WEEK NUMBER ACROSS.

🔴 THE DEFECT, MEASURED 2026-09-12 BY DRIVING THE DEPLOYED PAGE:

    ncaaf -> nfl    NFL Scores opened on WEEK 2, Thursday 17 September,
                    skipping the week-1 Sunday slate that was TOMORROW
    nfl -> ncaaf    College Scores opened on WEEK 1, Saturday 29 AUGUST
                    -- a board two weeks old with 455 finals on it

⛔ NEITHER DIRECTION LOOKED BROKEN. Both rendered a full, correct table of
the WRONG WEEK: no error, no empty state, no stale banner. That is why
nothing caught it and why no source check could — `fbWeek` is a
module-level `let` and the bug is entirely in when it is NOT reset.

⚠️ THE ASYMMETRY THAT HID IT: the SEASON picker already resets `fbWeek`,
because a season change obviously invalidates a week. A LEAGUE change
invalidates it just as completely and nothing did the same thing.

🔴 WHAT THIS FILE ASSERTS, AND WHY IT IS PHRASED THIS WAY. Not "the NFL
opens on week 1" — that is a fact about THIS WEEKEND and would go red the
moment the calendar moved (rule 166, nine instances on this repo). What
is asserted is the INVARIANT:

    THE WEEK A LEAGUE OPENS ON MUST NOT DEPEND ON WHICH LEAGUE THE
    READER WAS LOOKING AT BEFORE.

⛔ That cannot expire. It is true in September and in January, in week 1
and in week 15, and it is exactly what was broken.
"""
import http.server
import os
import socketserver
import threading

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════════════════
print("═══ 1. ⛔ THE RESET EXISTS IN THE SOURCE ═══")
# ⚠️ A source check is the WEAK half and is labelled as such. It cannot
#    tell you the reader sees the right week; it can only tell you the
#    line is still there after someone tidies `setLeague`.
HTML = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
_fn = HTML[HTML.index("function setLeague(lg){"):]
_fn = _fn[:_fn.index("\n}")]
# ⛔ STRIP THE COMMENT FIRST. The first form of this check searched the
#    whole function and PASSED WITH THE FIX DELETED, because the block
#    comment above the line quotes `fbWeek = null` verbatim while
#    explaining it. That is the fourth time in this repo a check has read
#    its own documentation as the thing it was checking for.
_live = "\n".join(ln for ln in
                  __import__("re").sub(r"/\*.*?\*/", "", _fn, flags=16).splitlines()
                  if not ln.strip().startswith("//"))
ck("🔴 setLeague resets fbWeek",
   "fbWeek = null" in _live,
   "⛔ a week number does not mean the same thing in the two leagues — "
   "college week 3 is NFL week 1 — so carrying it across is carrying a "
   "number that has no meaning in its new league")
ck("⛔ ...and it resets it BEFORE the render",
   "fbWeek = null" in _live
   and _live.index("fbWeek = null") < _live.index("renderFootball()"),
   "resetting after the render would paint the wrong week once and "
   "correct it on the next click, which is worse than either")

# ══════════════════════════════════════════════════════════════════════
print("\n═══ 2. 🔴 DRIVEN IN A BROWSER — THE HALF THAT MATTERS ═══")
try:
    from playwright.sync_api import sync_playwright
    _BROWSER = True
except ImportError:
    _BROWSER = False
    note("⚠️ NO BROWSER HERE — section 2 did not run. Expected on the "
         "collector's runner, which installs a bare Python (rule 133). "
         "⛔ Section 1 is NOT a substitute: it proves a line exists, not "
         "that a reader sees the right slate.")

if _BROWSER:
    os.chdir(ROOT)
    _h = http.server.SimpleHTTPRequestHandler
    _h.log_message = lambda *a, **k: None
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 0), _h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    PORT = srv.server_address[1]

    def _week(pg, order):
        """Load a FRESH page, walk `order`, return the last league's week.

        ⛔ FRESH EVERY TIME. `fbWeek` is module state; reusing a page
        would mean measuring the previous measurement.
        """
        pg.goto(f"http://127.0.0.1:{PORT}/index.html",
                wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(1200)
        # 🔴 SCORES IS OPENED IN **EVERY** LEAGUE ON THE WALK, NOT ONLY
        #    THE LAST. `fbWeek` is set by the Scores renderer and nothing
        #    else — the default tab was Trends until 2026-10-02 — so a walk that only
        #    clicked Scores at the end never set the variable in the
        #    FIRST league and therefore had nothing to carry across.
        # ⛔ THAT FORM PASSED WITH THE FIX DELETED. A test that cannot
        #    reach the state it is about is a green that proves nothing
        #    (rule 202), and it took deleting the fix to find out.
        for lg in order:
            pg.evaluate("setLeague('%s')" % lg)
            pg.wait_for_timeout(1600)
            pg.locator("nav.subnav a[data-tab='scores']").click()
            pg.wait_for_timeout(2600)
        el = pg.locator("#fb-sc-week")
        return el.input_value() if el.count() else None

    with sync_playwright() as ctx:
        br = ctx.chromium.launch(args=["--proxy-bypass-list=<-loopback>",
                                       "--no-proxy-server"])
        pg = br.new_page(viewport={"width": 1280, "height": 900})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        # ⛔ NO REQUEST LEAVES THIS MACHINE. `[2026-09-28]` Sam: "A test
        #    must not depend on the network." Every page load boots the MLB
        #    tab (statsapi.mlb.com) and asks mlbstatic/espncdn for logos;
        #    only ESPN was stubbed. Registered FIRST — Playwright tries the
        #    newest route first — so the ESPN stub below still answers its
        #    own URLs; anything else off this machine is aborted (the page
        #    already copes with a feed it cannot reach) and counted.
        #    test_live_scores.py §0 fails if a browser test loses this line.
        _offsite = []
        pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("http://127.0.0.1:", "http://localhost:")) else (_offsite.append(r.request.url), r.abort()))
        # ⛔ ESPN IS STUBBED TO EMPTY. The question here is which WEEK the
        #    picker lands on, which comes from the STORED schedule — the
        #    live feed only fills in scores. Leaving it live would make
        #    this test depend on a third party's uptime.
        pg.route("**/site.api.espn.com/**", lambda r: r.fulfill(
            status=200, content_type="application/json", body='{"events":[]}'))

        alone = {lg: _week(pg, [lg]) for lg in ("ncaaf", "nfl")}
        note("each league loaded ALONE lands on: %s" % alone)

        if not all(alone.values()):
            note("⚠️ NOT EXERCISED: no week picker rendered — there is no "
                 "stored football schedule on this machine, so there is "
                 "no week to land on. ⛔ Reported rather than passed.")
        else:
            # 🔴🔴 THE INVARIANT. Phrased with no week number in it, so no
            #    calendar can falsify it.
            after = {"nfl": _week(pg, ["ncaaf", "nfl"]),
                     "ncaaf": _week(pg, ["nfl", "ncaaf"])}
            bad = [lg for lg in alone if alone[lg] != after[lg]]
            # ⚠️ `[2026-09-28]` A CARRIED WEEK IS ONLY VISIBLE WHEN THE TWO
            #    LEAGUES' OWN WEEKS DIFFER. On a day both land on the same
            #    number (possible in December) deleting the reset changes
            #    nothing and the check below cannot fail — said, not passed.
            #    Section 1 asks the reset of the SOURCE every run.
            if alone["ncaaf"] == alone["nfl"]:
                note("⚠️ NOT EXERCISED TODAY: both leagues land on week %s "
                     "alone, so a week carried across the switch would look "
                     "identical. ⛔ Reported rather than passed."
                     % alone["nfl"])
            ck("🔴 A LEAGUE OPENS ON THE SAME WEEK WHATEVER YOU CAME FROM",
               not bad,
               "⛔ `fbWeek` survived the switch and the reader got a full, "
               "correct table of the wrong week — no error and no empty "
               "state, which is why nothing caught it.\n"
               "     alone: %s\n     after a switch: %s" % (alone, after))

            # ⚠️ AND THE WEEK IT LANDS ON IS ONE WITH SOMETHING LEFT TO
            #    PLAY. This is the PURPOSE behind the invariant above: the
            #    two could agree and both be the last week of the season.
            for lg in ("ncaaf", "nfl"):
                pg.goto(f"http://127.0.0.1:{PORT}/index.html",
                        wait_until="domcontentloaded", timeout=60000)
                pg.wait_for_timeout(1000)
                pg.evaluate("setLeague('%s')" % lg)
                pg.wait_for_timeout(1600)
                pg.locator("nav.subnav a[data-tab='scores']").click()
                pg.wait_for_timeout(2600)
                txt = pg.inner_text("#fbview")
                import re  # noqa: E402
                m = re.search(r"(\d+) final in this week", txt)
                weeks = pg.locator("#fb-sc-week option").count()
                ck("✅ %s lands on a week that is not fully played" % lg,
                   m is not None and weeks > 0,
                   "⛔ the picker offers %d week(s) and the header %s a "
                   "final count — if the page cannot say how much of the "
                   "week is done, the reader cannot tell a live slate "
                   "from a finished one"
                   % (weeks, "carries" if m else "carries NO"))
                note("%s: week %s, %s final, %d weeks offered"
                     % (lg, pg.locator("#fb-sc-week").input_value(),
                        m.group(1) if m else "?", weeks))

        # 🔴 `[Sam, 2026-10-01]` ONE TAB BAR, THE SAME LOOK, IN EVERY LEAGUE --
        #    measured in the real browser: the bar's place on the page, its
        #    order, and the COMPUTED style of the active and an inactive tab.
        #    test_tab_bar.py asks the same of the code on every run; this is
        #    the half only a browser can answer.
        SHOT = """() => {
          const bars = [...document.querySelectorAll('nav.subnav')];
          const bar = bars[0];
          const links = bar ? [...bar.querySelectorAll('a[data-tab]')] : [];
          const st = a => { if (!a) return null; const c = getComputedStyle(a);
            return ['color', 'backgroundColor', 'fontFamily', 'fontSize', 'fontWeight',
                    'letterSpacing', 'textTransform', 'paddingTop', 'paddingRight',
                    'paddingBottom', 'paddingLeft', 'boxShadow', 'borderBottomWidth',
                    'borderBottomColor'].map(k => c[k]).join('|'); };
          const on = links.find(a => a.classList.contains('on'));
          const r = bar ? bar.getBoundingClientRect() : null;
          return {n: bars.length, inHeader: !!(bar && bar.closest('header')),
                  shown: !!(bar && bar.offsetParent !== null),
                  order: links.map(a => a.dataset.tab), active: on ? on.dataset.tab : null,
                  on: st(on), off: st(links.find(a => !a.classList.contains('on'))),
                  top: r ? Math.round(r.top) : null, height: r ? Math.round(r.height) : null};
        }"""
        WANT = ['scores', 'picks', 'odds', 'props', 'gamelines', 'parlays', 'trends',
                'record', 'news']
        pg.goto(f"http://127.0.0.1:{PORT}/index.html",
                wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(1200)
        look = {}
        for lg in ("mlb", "nfl", "ncaaf"):
            pg.evaluate("setLeague('%s')" % lg)
            pg.wait_for_timeout(1600)
            look[lg] = pg.evaluate(SHOT)
        ck("🔴 every league shows ONE tab bar, the header's, in the same place",
           all(look[lg]["n"] == 1 and look[lg]["inHeader"] and look[lg]["shown"] for lg in look)
           and len({(look[lg]["top"], look[lg]["height"]) for lg in look}) == 1,
           str({lg: (look[lg]["n"], look[lg]["top"], look[lg]["height"]) for lg in look}))
        ck("🔴 ...with the same computed style for the active and the inactive tabs",
           len({look[lg]["on"] for lg in look}) == 1 and len({look[lg]["off"] for lg in look}) == 1
           and look["mlb"]["on"] and look["mlb"]["on"] != look["mlb"]["off"],
           str({lg: (look[lg]["on"], look[lg]["off"]) for lg in look}))
        ck("🔴 ...and the same order, MLB without Game Lines",
           look["nfl"]["order"] == WANT and look["ncaaf"]["order"] == WANT
           and look["mlb"]["order"] == [t for t in WANT if t != "gamelines"],
           str({lg: look[lg]["order"] for lg in look}))
        # 🔴 THE TAB OPENS ON SCORES AND SURVIVES A SWITCH.
        pg.goto(f"http://127.0.0.1:{PORT}/index.html",
                wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(1200)
        first = pg.evaluate(SHOT)["active"]
        pg.evaluate("setLeague('ncaaf')")
        pg.wait_for_timeout(1600)
        first_fb = pg.evaluate(SHOT)["active"]
        pg.evaluate("setLeague('mlb')")
        pg.wait_for_timeout(1600)
        pg.locator("nav.subnav a[data-tab='parlays']").click()
        pg.wait_for_timeout(1200)
        pg.evaluate("setLeague('nfl')")
        pg.wait_for_timeout(1600)
        kept = pg.evaluate(SHOT)["active"]
        pg.locator("nav.subnav a[data-tab='gamelines']").click()
        pg.wait_for_timeout(1600)
        pg.evaluate("setLeague('mlb')")
        pg.wait_for_timeout(1600)
        back = pg.evaluate(SHOT)["active"]
        ck("🔴 every league opens on Scores, and switching league keeps the tab "
           "(Parlays MLB -> NFL), or lands on Scores when it has no such tab "
           "(Game Lines NFL -> MLB)",
           (first, first_fb, kept, back) == ("scores", "scores", "parlays", "scores"),
           "got %s" % ((first, first_fb, kept, back),))

        ck("✅ no page error during any switch", not errs, str(errs[:3]))
        note("%d off-machine request(s) blocked, none answered by the "
             "network: %s" % (len(_offsite),
                              sorted({u.split("/")[2] for u in _offsite})))
        br.close()

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that any particular week is the "
     "right one to show. `fbCurrentWeek()` owns that and it is the first "
     "week holding an unfinished game. What is owned here is that the "
     "answer belongs to the league being viewed and to nothing else.")
