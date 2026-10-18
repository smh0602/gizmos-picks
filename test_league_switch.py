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
import json
import os
import re
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
        # `[Sam, 2026-10-01]` ~~MLB without Game Lines~~: every league has it.
        ck("🔴 ...and the same order, Game Lines in every league",
           all(look[lg]["order"] == WANT for lg in look),
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
           "(Parlays MLB -> NFL, and Game Lines NFL -> MLB, which has it now)",
           (first, first_fb, kept, back) == ("scores", "scores", "parlays", "gamelines"),
           "got %s" % ((first, first_fb, kept, back),))

        # ══════════════════════════════════════════════════════════════
        # 🔴 3. NOTHING WIDER THAN A PHONE, EVERY TAB REACHABLE `[Sam, 2026-10-14]`
        # ══════════════════════════════════════════════════════════════
        # Measured 2026-10-14 at 390 px before the fix: Player Props 180 /
        # 260 px wider than the screen (price and BET cut off), Gizmo's Picks
        # 186 / 195, Trends 48 / 112, Game Lines 6 / 14; 4 of 9 tabs showed.
        # ⚠️ The stored tree with the REAL clock (CLAUDE.md's allowed form),
        #    and then the same tabs with PLANTED wide content injected, so the
        #    check bites whatever today's data holds.
        PLANT = """() => {
          const v = document.querySelector('#fbview');
          const row = `<div class="prow fbprow"><div class="who"><div class="nm2">Christian
            McCaffrey-Longername Jr.</div><div class="tm2">Rushing + receiving yards</div></div>
            <div class="bet"><div class="ln">Over 112.5</div><div class="mk">rush+rec yds</div></div>
            <div class="pr2"><div class="v2">-115</div><span class="bk-chip">DraftKings</span>
            <a class="betbtn" data-planted>Bet &rarr;</a></div><div class="ev2"></div>
            <div class="imp"><b>3</b>books</div></div>`;
          const tr = '<tr>' + Array.from({length: 14}, (_, i) =>
            `<td>Planted column ${i} wide</td>`).join('') + '</tr>';
          v.insertAdjacentHTML('beforeend', `<div class="panel">${row}${row}
            <table class="ob">${tr}</table><table class="fbt">${tr}</table>
            <div class="glwrap"><table class="glmain">${tr}</table></div></div>`);
          const cw = document.documentElement.clientWidth;
          const bet = [...document.querySelectorAll('[data-planted]')];
          return {over: document.documentElement.scrollWidth - cw,
                  betIn: bet.length > 0 && bet.every(b => b.getBoundingClientRect().right <= cw)};
        }"""
        WIDE = "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
        pg.set_viewport_size({"width": 390, "height": 844})
        pg.goto(f"http://127.0.0.1:{PORT}/index.html",
                wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(1200)
        stored, planted = {}, {}
        for lg in ("nfl", "ncaaf"):
            pg.evaluate("setLeague('%s')" % lg)
            pg.wait_for_timeout(1600)
            for tab in WANT:
                pg.locator("nav.subnav a[data-tab='%s']" % tab).click()
                pg.wait_for_timeout(1800)
                stored["%s/%s" % (lg, tab)] = pg.evaluate(WIDE)
                planted["%s/%s" % (lg, tab)] = pg.evaluate(PLANT)
        ck("🔴 at 390 px no football tab is wider than the screen (stored tree)",
           all(v <= 0 for v in stored.values()),
           str({k: v for k, v in stored.items() if v > 0}))
        ck("🔴 ...nor with planted wide rows and tables, and the planted BET buttons are on screen",
           all(v["over"] <= 0 and v["betIn"] for v in planted.values()),
           str({k: v for k, v in planted.items() if v["over"] > 0 or not v["betIn"]}))
        # `[2026-10-17]` MLB too: its Game Lines table made the page 17 px wider than a 390 px
        #    screen (it never had football's scroll-in-its-own-box rule). The stored tree.
        mlb_wide = {}
        pg.evaluate("setLeague('mlb')")
        pg.wait_for_timeout(1600)
        for tab in WANT:
            pg.locator("nav.subnav a[data-tab='%s']" % tab).click()
            pg.wait_for_timeout(1500)
            over = pg.evaluate(WIDE)
            if over > 0:
                mlb_wide[tab] = over
        ck("🔴 ...and no MLB tab is wider than the screen either (stored tree)", not mlb_wide, str(mlb_wide))
        tabs = pg.evaluate("""() => { const cw = document.documentElement.clientWidth;
          const a = [...document.querySelectorAll('nav.subnav a[data-tab]')];
          return {n: a.length, inside: a.every(x => { const r = x.getBoundingClientRect();
                    return r.left >= 0 && r.right <= cw && r.width > 0; }),
                  rows: [...new Set(a.map(x => Math.round(x.getBoundingClientRect().top)))].length,
                  order: a.map(x => x.dataset.tab)}; }""")
        ck("🔴 ...and all 9 tabs are on screen, on two rows, in the same order",
           tabs["n"] == 9 and tabs["inside"] and tabs["rows"] == 2 and tabs["order"] == WANT, str(tabs))

        # ══════════════════════════════════════════════════════════════
        # 🔴 4. A PICK ROW NEVER SQUEEZES ITS PLAYER, AT ANY WIDTH `[Sam, 2026-10-17]` (design I)
        # ══════════════════════════════════════════════════════════════
        # Measured on the first design I build, MLB's 2026-10-17 card: at 601-690 px and
        # 821-960 px the player column shrank to 10-55 px and its words ran 5-100 px into the
        # price ("Junior / Caminero / Over / 0.5 / Hits" one word a line, "Hits" through
        # "Hard Rock"), on 24 of 25 rows; the page was no wider than the screen, so section 3
        # stayed green (`.pk` clips its overflow). ⛔ PLANTED rows through the page's own
        # pickCard (the worst case: an MLB hitter with a headshot and a long name, and a
        # football row), so the check asks the code, not today's card.
        SQUEEZE = """() => {
          const rows = [
            {kind: 'hitter', confidence_basis: 'RECORD', player: 'Christian Bethancourt-Longername Jr.',
             pid: 660271, side: 'under', line: 1.5, market: 'total_bases', market_label: 'Total bases',
             projection: 1.3, projection_unit: 'TB', away: 'Tampa Bay Rays', home: 'Cleveland Guardians',
             away_id: 139, home_id: 114, game: 'TB @ CLE', first_pitch: '8:00pm', price: -350,
             book: 'hardrockbet', link: 'https://example.invalid/slip', confidence: 79,
             break_even: 77.8, edge: 0.8, why: ['A planted reason.'], raw: '38/48', rate: 79},
            {kind: 'fb', confidence_basis: 'MODEL', player: 'Marvin Harrison Jr.', side: 'over', line: 1.5,
             market: 'player_receptions', market_label: 'Receptions', projection: 3.1, projection_unit: 'rec',
             away: 'Houston Texans', home: 'Jacksonville Jaguars', game: 'Houston Texans @ Jacksonville Jaguars',
             commence: '2026-10-18T13:30:00Z', price: -148, book: 'fanduel', link: 'https://example.invalid/slip',
             confidence: 75, break_even: 59.7, edge: 15.3, why: ['A planted reason.']}];
          const v = document.querySelector('#view');
          v.querySelectorAll('[data-sq]').forEach(n => n.remove());
          rows.forEach(r => { const c = pickCard(r); c.dataset.sq = '1'; v.prepend(c); });
          return [...v.querySelectorAll('[data-sq]')].map(c => {
            const t = c.querySelector('.pk-t'), px = c.querySelector('.pk-px');
            const tr = t.getBoundingClientRect(), pr = px.getBoundingClientRect();
            const same = tr.top < pr.bottom && pr.top < tr.bottom;
            let right = tr.left;
            for (const e of t.querySelectorAll('*')) right = Math.max(right, e.getBoundingClientRect().right);
            return {w: Math.round(tr.width), over: same ? Math.round(right - pr.left) : 0};
          });
        }"""
        pg.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(1200)
        squeezed = {}
        for w in (601, 640, 700, 768, 821, 844, 900, 960, 1024, 1280):
            pg.set_viewport_size({"width": w, "height": 900})
            pg.wait_for_timeout(250)
            got = pg.evaluate(SQUEEZE)
            bad = [g for g in got if g["w"] < 120 or g["over"] > 0]
            if bad or len(got) != 2:
                squeezed[w] = got
        ck("🔴 at every width from 601 to 1280 px a pick row keeps its player readable: the column "
           "at least 120 px, and nothing in it runs into the price",
           not squeezed, str(squeezed))
        # ⚠️ The side panel takes 240 px. Shown from 821 px (the first build), it left 600 px at
        #    844 and NFL Game Lines ran 93 px, Player Props 6 px, wider than the screen. From
        #    1024 px it leaves at least 784. The stored tree, as section 3's first half.
        wide_mid = {}
        for w in (844, 900, 1024):
            pg.set_viewport_size({"width": w, "height": 900})
            for lg in ("nfl", "ncaaf"):
                pg.evaluate("setLeague('%s')" % lg)
                pg.wait_for_timeout(1600)
                for tab in ("props", "gamelines"):
                    pg.locator("nav.subnav a[data-tab='%s']" % tab).click()
                    pg.wait_for_timeout(1800)
                    over = pg.evaluate(WIDE)
                    if over > 0:
                        wide_mid["%d/%s/%s" % (w, lg, tab)] = over
        ck("🔴 ...and beside the side panel, football's Player Props and Game Lines are no wider "
           "than the screen (844, 900 and 1024 px; college was 99 / 113 px over at 821)",
           not wide_mid, str(wide_mid))
        pg.set_viewport_size({"width": 1280, "height": 900})

        # ══════════════════════════════════════════════════════════════
        # 🔴 5. EVERY WORD ON EVERY TAB IS READABLE `[Sam, 2026-10-17]` (design I)
        # ══════════════════════════════════════════════════════════════
        # Measured on the first design I build: the "@" between two teams at 1.24:1 (it was
        # drawn in the border colour), Trends' rank column 3.05, its sort arrows 3.65 and its
        # thin-sample rows 2.27. ⛔ WCAG's bar: 4.5:1, 3:1 for large text (24 px, or 18.66 px
        # bold). Text over an image is skipped (its background cannot be read).
        CONTRAST = """() => {
          const parse = c => { const m = c && c.match(/rgba?\\(([^)]+)\\)/); if (!m) return null;
            const p = m[1].split(',').map(Number); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
          const lin = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
          const L = c => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
          const mix = (f, b) => ({r: f.r * f.a + b.r * (1 - f.a), g: f.g * f.a + b.g * (1 - f.a), b: f.b * f.a + b.b * (1 - f.a), a: 1});
          const bg = el => { const st = []; for (let e = el; e; e = e.parentElement){ const cs = getComputedStyle(e);
              if (cs.backgroundImage && cs.backgroundImage !== 'none') return null;
              const c = parse(cs.backgroundColor); if (c && c.a > 0) st.push(c); if (c && c.a === 1) break; }
            let acc = {r: 255, g: 255, b: 255, a: 1}; for (let i = st.length - 1; i >= 0; i--) acc = mix(st[i], acc); return acc; };
          const out = [];
          for (const el of document.body.querySelectorAll('*')){
            if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
            const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
            const cs = getComputedStyle(el); if (cs.visibility === 'hidden') continue;
            const b = bg(el), f = parse(cs.color); if (!b || !f) continue;
            let o = 1; for (let e = el; e; e = e.parentElement) o *= Number(getComputedStyle(e).opacity);
            const t = mix({...f, a: f.a * o}, b), a = L(t), c = L(b);
            const ratio = (Math.max(a, c) + 0.05) / (Math.min(a, c) + 0.05);
            const size = parseFloat(cs.fontSize), large = size >= 24 || (size >= 18.66 && parseInt(cs.fontWeight) >= 700);
            if (ratio < (large ? 3 : 4.5)) out.push(el.textContent.trim().slice(0, 30) + ' ' + ratio.toFixed(2));
          }
          return [...new Set(out)].slice(0, 6);
        }"""
        faint = {}
        for lg in ("mlb", "nfl", "ncaaf"):
            pg.evaluate("setLeague('%s')" % lg)
            pg.wait_for_timeout(1600)
            for tab in WANT:
                pg.locator("nav.subnav a[data-tab='%s']" % tab).click()
                pg.wait_for_timeout(1500)
                got = pg.evaluate(CONTRAST)
                if got:
                    faint["%s/%s" % (lg, tab)] = got
        ck("🔴 every word on every tab of every league reads at 4.5:1 or better (3:1 for large text)",
           not faint, str(faint))

        # ══════════════════════════════════════════════════════════════
        # 🔴 6. SET STATE ON GIZMO'S PICKS OPENS THE PICKER, AND THE STATE MAKES THE BET SLIP `[2026-10-18]`
        # ══════════════════════════════════════════════════════════════
        # Measured 2026-10-18 on MLB's 2026-10-17 card: 4 SET STATE buttons, and a click left the
        # picker `display: none` and the focus on the page body; it did nothing (setTools shows
        # the picker on Odds and Player Props only). Choosing a state on a football tab redrew
        # MLB's tab, not the one being read. ⛔ PLANTED CARDS, every league: one player prop and
        # one game line, each with a `{state}` link, so the check asks the code, not today's card
        # (football's three books carry no `{state}` link today). The real click, at a desktop
        # and a phone width. test_set_state.py asks the same of every tab's code, without a browser.
        import datetime as _dt  # noqa: E402
        _now = _dt.datetime.now(_dt.timezone.utc)
        _day = (_now - _dt.timedelta(hours=5)).strftime("%Y-%m-%d")
        _soon = (_now + _dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        SLIPS = {"prop": "https://sportsbook.caesars.com/us/{state}/bet/betslip?selectionIds=gp-planted-1",
                 "line": "https://sports.{state}.betmgm.com/en/sports?options=gp-planted-2&type=Single"}
        _game = dict(away="Away Club", home="Home Club", game="Away Club @ Home Club",
                     commence=_soon, why=["A planted row."], confidence_basis="MODEL")
        _mlb_prop = dict(_game, kind="pitcher", pitcher="Planted Pitcher", market="strikeouts",
                         side="over", line=5.5, price=-120, book="williamhill_us",
                         link=SLIPS["prop"], confidence=64, break_even=54.5, edge=9.5,
                         first_pitch="7:05pm")
        _mlb_line = dict(_game, kind="mlb-line", player="Home Club", market="h2h",
                         market_label="Moneyline", side="home", line=None, price=-130,
                         book="betmgm", link=SLIPS["line"], confidence=58, break_even=56.5,
                         edge=1.5, first_pitch="7:05pm")
        _fb_prop = dict(_game, kind="fb", player="Planted Receiver", market="player_reception_yds",
                        market_label="Receiving yards", side="over", line=50.5, price=-115,
                        book="williamhill_us", link=SLIPS["prop"], confidence=61,
                        break_even=53.5, edge=7.5)
        _fb_line = dict(_game, kind="fb-line", player="Home Club", market="spreads",
                        market_label="Spread", side="home", line=-3.5, price=-110,
                        book="betmgm", link=SLIPS["line"], confidence=57, break_even=52.4,
                        edge=4.6)
        CARDS = {"mlb": {"date": _day, "picks": [_mlb_prop], "game_lines": [_mlb_line],
                         "top10": [], "pairs": [], "parlays": {}, "projections": {}},
                 "fb": {"date": _day, "odds_pulled_at": _now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "picks": [_fb_prop], "liked": [_fb_prop], "game_lines": [_fb_line],
                        "game_lines_liked": [_fb_line], "game_lines_meta": {"slate": _day},
                        "top_plays": [], "projections": {}}}

        def _card(route):
            path = route.request.url.split("?")[0]
            if re.search(r"/picks/\d{4}-\d{2}-\d{2}\.json$", path):
                body = CARDS["mlb"]
            elif re.search(r"/picks/fb-(nfl|ncaaf)-latest\.json$", path):
                body = CARDS["fb"]
            else:
                return route.fallback()
            route.fulfill(status=200, content_type="application/json", body=json.dumps(body))
        pg.route("**/picks/*.json", _card)
        PICKER = """() => { const s = document.getElementById('st'), r = s.getBoundingClientRect();
          return {shown: s.offsetParent !== null && r.height > 0,
                  inView: r.top >= 0 && r.bottom <= innerHeight,
                  focused: document.activeElement === s}; }"""
        AFTER = """v => ({needs: document.querySelectorAll(v + ' .needs').length,
          hrefs: [...document.querySelectorAll(v + ' .pk-px a.bklink')].map(a => a.href),
          value: document.getElementById('st').value,
          shown: document.getElementById('st').offsetParent !== null})"""
        dead, slips = {}, {}
        for w, h, kinds in ((1280, 900, ("prop", "line")), (390, 844, ("prop",))):
            pg.set_viewport_size({"width": w, "height": h})
            for lg in ("mlb", "nfl", "ncaaf"):
                for kind in kinds:
                    case = "%s/%s/%dpx" % (lg, kind, w)
                    pg.goto(f"http://127.0.0.1:{PORT}/index.html",
                            wait_until="domcontentloaded", timeout=60000)
                    pg.evaluate("localStorage.removeItem('gp_state')")
                    pg.reload(wait_until="domcontentloaded", timeout=60000)
                    pg.wait_for_timeout(1200)
                    if lg != "mlb":
                        pg.evaluate("setLeague('%s')" % lg)
                        pg.wait_for_timeout(1600)
                    pg.locator("nav.subnav a[data-tab='picks']").click()
                    pg.wait_for_timeout(1800)
                    view = "#view" if lg == "mlb" else "#fbview"
                    if kind == "line":
                        pg.locator("%s .kchip[data-%s='lines']"
                                   % (view, "mlbkind" if lg == "mlb" else "fbkind")).click()
                        pg.wait_for_timeout(1200)
                    btn = pg.locator("%s .betbtn.needs" % view)
                    n, hidden = btn.count(), pg.locator("#st").is_hidden()
                    if n:
                        btn.first.click()
                        pg.wait_for_timeout(1000)
                    seen = pg.evaluate(PICKER)
                    if not (n and hidden and seen["shown"] and seen["inView"] and seen["focused"]):
                        dead[case] = dict(seen, buttons=n, hidden_before=hidden)
                    pg.select_option("#st", "NJ")
                    pg.wait_for_timeout(1500)
                    got = pg.evaluate(AFTER, view)
                    want = SLIPS[kind].replace("{state}", "nj")
                    if got["needs"] or want not in got["hrefs"] or got["value"] != "NJ" \
                            or not got["shown"]:
                        slips[case] = got
        pg.set_viewport_size({"width": 1280, "height": 900})
        ck("🔴 on Gizmo's Picks in every league, a SET STATE click shows the hidden state picker, "
           "scrolls to it and focuses it (planted player prop and game line, 1280 and 390 px)",
           not dead, str(dead))
        ck("🔴 ...and choosing a state turns every SET STATE on the tab into the book link, that "
           "state's bet slip, with the picker still showing it",
           not slips, str(slips))

        ck("✅ no page error during any switch", not errs, str(errs[:3]))
        note("%d off-machine request(s) blocked, none answered by the "
             "network: %s" % (len(_offsite),
                              sorted({u.split("/")[2] for u in _offsite})))
        br.close()

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that any particular week is the "
     "right one to show. `fbCurrentWeek()` owns that and it is the first "
     "week holding an unfinished game. What is owned here is that the "
     "answer belongs to the league being viewed and to nothing else.")
