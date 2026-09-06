#!/usr/bin/env python3
"""
THE BOX SCORE IN THE GAME MODAL — AND THE SCROLL THAT MUST NOT MOVE.

🔴 Sam, 2026-09-06: *"user need to be able to click on a score and see the
box score from that game, includes qb passing stats, rb stats, wr stats,
etc"* and *"some of the tabs in cfb refresh on there own and direct me
back to the top of the page, this has to be fixed because its annoying."*

⚠️ THE STATIC HALF RUNS EVERYWHERE, THE BROWSER HALF WHERE THERE IS A
BROWSER — the collector's runner installs a bare Python, and a test that
cannot import fails the whole suite and BLOCKS a push (rule 133).

WHAT IS PINNED:
  1. the numbers in the modal are the ones in the stored log — checked
     against the file, player by player, not "a table appeared"
  2. a game we hold NO log for says so, and says it is an ABSENCE
  3. 🔴 a re-render KEEPS THE READER'S SCROLL POSITION
  4. the live poll does not redraw when the feed has not moved
"""
import glob
import gzip
import http.server
import json
import os
import socketserver
import threading

from jsblock import calls, js_block, source
from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, "index.html")


def serve():
    os.chdir(ROOT)
    h = http.server.SimpleHTTPRequestHandler
    h.log_message = lambda *a, **k: None
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


# ───────────────────────────────────────────────────────────────
print("\n═══ 0. THE JOIN AND THE SHAPE, WITHOUT A BROWSER ═══")
# 🔴 THE JOIN IS WHAT DECIDES WHETHER A BOX SCORE IS POSSIBLE AT ALL, and
#    it is measured against the real files rather than assumed.
for lg, season in (("ncaaf", 2026), ("nfl", 2025)):
    pf = f"{ROOT}/data/{lg}/latest/players-{season}.json.gz"
    sf = f"{ROOT}/data/{lg}/latest/schedule-{season}.json.gz"
    if not (os.path.exists(pf) and os.path.exists(sf)):
        note(f"{lg} {season}: no stored logs here, join not measured")
        continue
    P = json.load(gzip.open(pf, "rt"))["players"]
    S = {str(g["id"]): g for g in json.load(gzip.open(sf, "rt"))["games"]}
    gids, bad = set(), 0
    for p in P.values():
        for r in p.get("g") or []:
            gid = str(r.get("game_id"))
            gids.add(gid)
            if gid in S and r.get("team") not in (S[gid]["away"], S[gid]["home"]):
                bad += 1
    hit = len(gids & set(S))
    ck(f"{lg}: every logged game_id is a schedule id",
       hit == len(gids), f"{hit} of {len(gids)}")
    ck(f"{lg}: every logged team is one of that game's two sides",
       bad == 0, f"{bad} rows name a third team — a name matcher would be "
                 f"needed if this were not 0 (rule 54)")

# 🔴 THE STORED-LOG RENDERER MOVED TO `fbBoxStored` ON 2026-09-06, when
#    ESPN became the first source. ⛔ These checks follow it rather than
#    being deleted: the stored log is still what the Track Record grades
#    against, so it must keep working when ESPN is refused.
box = js_block("fbBoxStored", HTML)
ck("the stored box score is keyed on the game id, never a name",
   "by[String(g.id)]" in box, "rule 54")
ck("a game with no stored log says ABSENCE, not zero",
   "That is an absence, not a zero" in box,
   "⛔ an empty table with no reason reads as a bug")
ck("...and it is reachable from the modal",
   calls("fbBoxScore", HTML) >= 1, "%d call site(s)" % calls("fbBoxScore", HTML))
ck("...and the stored renderer is called by the one that chooses a source",
   "fbBoxStored(g, by)" in js_block("fbBoxScore", HTML),
   "a renderer nobody calls is a decoy (rule 130)")

tbl = js_block("fbBoxTable", HTML)
ck("passing, rushing and receiving all have columns",
   all(c in tbl for c in ("C/ATT", "CAR", "REC", "INT", "TD")))
ck("⚠️ targets are dropped where the feed has none, not zero-filled",
   "list.some(x => fbNum(x.r.tgt) !== null)" in tbl,
   "college play-by-play carries no targets; a 0 would read as "
   "'nobody threw to him'")
ck("a missing number renders an em-dash, never a 0",
   "&mdash;" in tbl and "fbNum" in tbl,
   "the same distinction the Track Record makes")

ck("🔴 the modal no longer claims a played game has not kicked off",
   "fbKickedOff(g)" in js_block("fbOpenBox", HTML),
   "Sam's screenshot: UCLA @ California, 3.5 hours after kickoff")

tick = js_block("fbTick", HTML)
ck("🔴 the live poll skips the redraw when the feed has not moved",
   "if (sig === fbSig) return" in tick,
   "a redraw that changes nothing is a redraw that moves the page")
ck("...and it holds the scroll position when it does redraw",
   "fbKeepScroll(renderFootball)" in tick)
keep = js_block("fbKeepScroll", HTML)
ck("the scroll keeper waits two frames, as MLB's does",
   "requestAnimationFrame(() => requestAnimationFrame(r))" in keep,
   "one for the DOM, one for layout to settle its height")
src = source(HTML)
ck("🔴 every Scores control routes through it, not just the timer",
   src.count("fbKeepScroll(") >= 4,
   "%d call sites — season, week, division, conference chips, the poll"
   % src.count("fbKeepScroll("))

srv, PORT = serve()
try:
    from playwright.sync_api import sync_playwright
    _BROWSER = True
except ImportError:
    _BROWSER = False
    note("⚠️ NO BROWSER HERE — the render checks did not run. Expected on "
         "the collector's runner, which installs a bare Python.")

if _BROWSER:
  with sync_playwright() as ctx:
    br = ctx.chromium.launch(args=["--proxy-bypass-list=<-loopback>"])
    pg = br.new_page(viewport={"width": 1400, "height": 1100})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    # ⚠️ ESPN IS STUBBED EMPTY HERE ON PURPOSE. This file tests the
    #    STORED-LOG path, which is the fallback; the ESPN path is driven
    #    against real captured payloads in `test_box_live.py`. An empty
    #    body makes `fbBoxEspn` return null, which is exactly the
    #    condition the fallback exists for.
    pg.route("**/site.api.espn.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json", body='{"events":[]}'))

    print("\n═══ 1. A GAME WE HOLD A LOG FOR — THE REAL NUMBERS ═══")
    # ⛔ PICKED FROM THE DATA, not typed in: the first college game whose
    #    log has a passer, so the assertion is against a real row.
    P = json.load(gzip.open(f"{ROOT}/data/ncaaf/latest/players-2026.json.gz", "rt"))["players"]
    want = None
    for p in P.values():
        for r in p.get("g") or []:
            if (r.get("att") or 0) > 5:
                want = (str(r["game_id"]), p["name"], r)
                break
        if want:
            break
    ck("the stored logs contain a passer to check against", bool(want))

    if want:
        gid, who, row = want
        pg.goto(f"http://127.0.0.1:{PORT}/index.html",
                wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(1200)
        pg.get_by_text("College Football", exact=True).first.click()
        pg.wait_for_timeout(600)
        pg.locator("#fbview a[data-fbtab='scores']").click()
        pg.wait_for_function("() => window.__fbShown && window.__fbShown.length > 0",
                             timeout=30000)
        # open the modal for that exact game, through the page's own code
        opened = pg.evaluate("""async (gid) => {
            const doc = await fbSchedLoad(fbScSeason);
            const g = (doc.games || []).find(x => String(x.id) === gid);
            if (!g) return false;
            await fbOpenBox(g);
            return true;
        }""", gid)
        ck("the modal opens for a game we hold a log for", opened)
        pg.wait_for_function(
            "() => document.querySelector('#fbbox table.bx')", timeout=30000)
        txt = pg.inner_text("#fbbox").replace("—", "-")
        ck("🔴 the passer from the stored log is in the box score", who in txt,
           who)
        for lbl, key in (("passing yards", "pass_yds"), ("attempts", "att"),
                         ("completions", "cmp")):
            v = row.get(key)
            if v is None:
                continue
            ck(f"...and his {lbl} match the file", str(int(v)) in txt,
               f"{key}={int(v)}")
        # ⚠️ CASE-INSENSITIVE, AND THAT IS NOT LAZINESS. `.bxh` is
        # `text-transform:uppercase`, so the DOM text is "PASSING" while
        # the source says "Passing". This repo has now had FIVE false
        # failures from case-sensitive text checks on correct code — the
        # walk harness carries the same warning in its own docstring.
        _low = txt.lower()
        ck("the three categories are labelled",
           all(w in _low for w in ("passing", "rushing", "receiving")),
           "found: " + ", ".join(w for w in ("passing", "rushing", "receiving")
                                 if w in _low))
        ck("no page error", not errs, str(errs[:1]))
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(300)

    print("\n═══ 2. A GAME WE HOLD NO LOG FOR SAYS SO ═══")
    none_g = pg.evaluate("""async () => {
        const doc = await fbSchedLoad(fbScSeason);
        const by = await fbLogsLoad(fbScSeason);
        const g = (doc.games || []).find(x => !(by || {})[String(x.id)]);
        if (!g) return null;
        await fbOpenBox(g);
        return String(g.id);
    }""")
    if none_g:
        pg.wait_for_timeout(900)
        t2 = pg.inner_text("#fbbox").lower()
        ck("⛔ it names the absence rather than showing an empty table",
           "absence" in t2 and "not a zero" in t2, t2[:90])
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(300)
    else:
        note("every game in this view has a log — the empty case was not driven")

    print("\n═══ 3. 🔴 A RE-RENDER MUST NOT MOVE THE PAGE ═══")
    # ⛔ THE ANNOYANCE SAM REPORTED, MEASURED: scroll down, force the exact
    #    re-render the controls and the poll cause, and check the position.
    pg.evaluate("window.scrollTo(0, 700)")
    pg.wait_for_timeout(200)
    before = pg.evaluate("() => window.scrollY")
    ck("the page is scrolled down to begin with", before > 300, str(before))
    pg.evaluate("() => fbKeepScroll(renderFootball)")
    pg.wait_for_function("() => window.__fbShown && window.__fbShown.length > 0",
                         timeout=30000)
    pg.wait_for_timeout(700)
    after = pg.evaluate("() => window.scrollY")
    ck("🔴 a full re-render leaves the reader where they were",
       abs(after - before) <= 40, f"was {before}, now {after}")
    ck("no page error", not errs, str(errs[:1]))


    print("\n═══ 4. 🔴 THE SAME THING FOR THE NFL — SAM'S STANDING RULE ═══")
    # 🔴 "everything we do for cfb we do for nfl and vice versa."
    # ⛔ A feature driven on ONE league is a feature half-shipped. This
    #    opens an NFL game and checks the numbers against the NFL file,
    #    the same way section 1 does for college.
    NP = json.load(gzip.open(f"{ROOT}/data/nfl/latest/players-2025.json.gz", "rt"))["players"]
    nwant = None
    for p in NP.values():
        for r in p.get("g") or []:
            if (r.get("att") or 0) > 20:
                nwant = (str(r["game_id"]), p["name"], r)
                break
        if nwant:
            break
    ck("the NFL logs contain a passer to check against", bool(nwant))
    if nwant:
        gid, who, row = nwant
        pg.goto(f"http://127.0.0.1:{PORT}/index.html",
                wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(1200)
        pg.get_by_text("NFL", exact=True).first.click()
        pg.wait_for_timeout(600)
        pg.locator("#fbview a[data-fbtab='scores']").click()
        pg.wait_for_function("() => window.__fbShown && window.__fbShown.length > 0",
                             timeout=30000)
        # ⚠️ 2025, because the 2026 NFL logs do not exist until the season
        #    has been played — which the panel says in as many words.
        opened = pg.evaluate("""async (gid) => {
            fbScSeason = 2025;
            const doc = await fbSchedLoad(2025);
            const g = (doc.games || []).find(x => String(x.id) === gid);
            if (!g) return false;
            await fbOpenBox(g);
            return true;
        }""", gid)
        ck("an NFL game modal opens", opened)
        pg.wait_for_function("() => document.querySelector('#fbbox table.bx')",
                             timeout=30000)
        ntxt = pg.inner_text("#fbbox")
        ck("🔴 the NFL passer from the stored log is in the box score",
           who in ntxt, who)
        ck("...and his passing yards match the file",
           str(int(row["pass_yds"])) in ntxt, "pass_yds=%d" % int(row["pass_yds"]))
        ck("⚠️ and the NFL box score carries TARGETS, which college cannot",
           "TGT" in ntxt.upper(),
           "nflverse has targets; CFBD play-by-play does not — the column "
           "is present for one league and absent for the other because "
           "the DATA differs, not the renderer")
        ck("no page error", not errs, str(errs[:1]))
        pg.keyboard.press("Escape")

    print("\n═══ 5. THE 2026 NFL SEASON HAS NO LOGS YET, AND SAYS SO ═══")
    # ⛔ "cannot exist yet" is not "broken" (rule 86). The NFL season has
    #    not been played, so its 2026 logs do not exist — the panel must
    #    name that rather than showing an empty table.
    msg = pg.evaluate("""async () => {
        fbScSeason = 2026;
        const by = await fbLogsLoad(2026);
        return by === null ? 'null' : 'present';
    }""")
    ck("the 2026 NFL player log is genuinely absent", msg == "null",
       "it arrives with the Tuesday rebuild after week 1")
    br.close()
srv.shutdown()
