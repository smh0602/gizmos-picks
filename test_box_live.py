#!/usr/bin/env python3
"""
THE LIVE BOX SCORE — ESPN'S OWN SUMMARY, DRIVEN AGAINST REAL PAYLOADS.

🔴 Sam, 2026-09-06: *"not all games in the scores tab have a full box
score when click into them, needs to be fixed and needs to allow the user
to click into games in real time and see the live boxscore as well as
seeing box scores for games that have finished."*

⛔ WHY THE STORED LOG COULD NEVER ANSWER IT, MEASURED AGAINST THE SHIPPED
FILES (section 0 re-measures this every run rather than quoting it):

    Division I games played              202
    ...carrying a stored player log       17
    Saturday 2026-09-05 alone            103
    ...carrying a stored player log        0

🔴 THE FIXTURES IN `espnfix.json` ARE REAL ESPN PAYLOADS, captured in a
browser from this product's own origin on 2026-09-06 — not written by
hand. `cfb` and `nfl` are finals with players; `d2` is a game ESPN carries
with ZERO players, which is the case that made the panel look broken.
⚠️ A hand-written fixture would have agreed with whatever the parser
already did; these disagree with each other, which is the point:

    college passing labels  C/ATT YDS AVG TD INT QBR            (6)
    NFL     passing labels  C/ATT YDS AVG TD INT SACKS QBR RTG  (8)

WHAT IS PINNED:
  1. the columns come from `labels[]`, and BOTH leagues render correctly
  2. a game ESPN carries with no players says so and falls back
  3. a REFUSAL turns the layer off for the session; a 404 does not
  4. the live poll refreshes the panel and NEVER moves the reader
  5. ESPN strings are escaped before they reach innerHTML
"""
import glob
import gzip
import http.server
import json
import os
import socketserver
import threading
import datetime

from jsblock import calls, js_block, source
from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, "index.html")
FIX = os.path.join(ROOT, "espnfix.json")


def serve():
    os.chdir(ROOT)
    h = http.server.SimpleHTTPRequestHandler
    h.log_message = lambda *a, **k: None
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


# ───────────────────────────────────────────────────────────────
print("\n═══ 0. THE GAP THAT MADE THIS NECESSARY, RE-MEASURED ═══")
sf = f"{ROOT}/data/ncaaf/latest/schedule-2026.json.gz"
pf = f"{ROOT}/data/ncaaf/latest/players-2026.json.gz"
if os.path.exists(sf) and os.path.exists(pf):
    games = json.load(gzip.open(sf, "rt"))["games"]
    logged = set()
    for p in json.load(gzip.open(pf, "rt"))["players"].values():
        for r in p.get("g") or []:
            logged.add(str(r.get("game_id")))
    D1 = {"fbs", "fcs"}

    def et(s):
        d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return (d - datetime.timedelta(hours=4)).date().isoformat()

    d1 = [g for g in games
          if (g.get("home_class") or "").lower() in D1
          or (g.get("away_class") or "").lower() in D1]
    played = [g for g in d1 if g.get("final")]
    have = sum(1 for g in played if str(g["id"]) in logged)
    ck("🔴 most Division I games played have NO stored player log",
       have < len(played) / 2,
       f"{have} of {len(played)} — this is the bug, stated as a fraction")
    # The single worst day is the one a reader actually clicks on.
    byday = {}
    for g in played:
        byday.setdefault(et(g["start"]), []).append(g)
    if byday:
        worst = min(byday.items(),
                    key=lambda kv: sum(1 for g in kv[1] if str(g["id"]) in logged)
                    - 0.0001 * len(kv[1]))
        n = sum(1 for g in worst[1] if str(g["id"]) in logged)
        note(f"worst day {worst[0]}: {n} of {len(worst[1])} games have a log")
else:
    note("no stored college files here — the gap was not re-measured")

# ───────────────────────────────────────────────────────────────
print("\n═══ 1. THE SHAPE RULES, WITHOUT A BROWSER ═══")
parse = js_block("fbBoxParse", HTML)
fetch = js_block("fbBoxFetch", HTML)
blk = js_block("fbBoxBlock", HTML)
srt = js_block("fbBoxSort", HTML)
chooser = js_block("fbBoxScore", HTML)
src = source(HTML)

ck("🔴 the columns are read from the payload, never hard-coded",
   "s.labels" in parse and "b.labels" in blk,
   "rule 121 — the two leagues carry different passing columns")
ck("...and no positional column name is written into the renderer",
   not any(w in blk for w in ("'C/ATT'", '"C/ATT"', "'SACKS'", '"RTG"')),
   "a literal here is an assumption about a schema we do not own")
ck("a row with more values than headings is NOT shifted left to fit",
   "Math.min(b.labels.length, wide)" in blk and "odd" in blk,
   "it renders the columns both sides carry and says the rest arrived")
ck("the sort finds its column by LABEL, not by index",
   "b.labels.indexOf('YDS')" in srt and "if (i < 0) return b.rows" in srt,
   "and keeps the feed's own order when there is no such column")

ck("🔴 ONE REFUSAL turns the layer off; ONE 404 does not",
   "FB_BOX_OFF = true" in fetch and "{http: r.status}" in fetch,
   "merging them lets a single missing event silence the session")
ck("...and the refusal is only set in the catch, not on a bad status",
   fetch.index("catch") < fetch.index("FB_BOX_OFF = true"),
   "a thrown fetch is CORS/offline; a status is one game")
ck("the poll reuses the live layer's own 45s, not a second number",
   "FB_LIVE_MS" in js_block("fbOpenBox", HTML) and "FB_BOX_MS" not in src,
   "rule 66 — one number per fact")

ck("🔴 ESPN is preferred and the stored log is the FALLBACK",
   chooser.index("fbBoxEspn(box)") < chooser.index("fbBoxStored(g, by)"),
   "preferring the stored log would keep the empty panel Sam reported")
ck("a game ESPN carries with no players says so, and says ABSENCE",
   "publishes no\n            player stats" in chooser
   or "publishes no" in chooser and "absence, not a zero" in chooser.lower(),
   "the Division II case in the fixtures")
ck("🔴 an unplayed game is NOT reported as 'no player stats'",
   "box.state === 'pre'" in chooser and "has not kicked off" in chooser,
   "measured live: the 2026 NFL opener returns state=pre with 0 players "
   "and the kickoff time — calling that 'ESPN publishes none' repeats "
   "rule 134")
ck("...and a game under way with no stats yet says THAT instead",
   "box.live" in chooser and "not posted any player stats yet" in chooser,
   "three different facts, three different sentences")
ck("...and the panel names WHICH source it is showing",
   "grades\n      against our own stored logs" in js_block("fbBoxEspn", HTML)
   or "stored logs, not against this" in js_block("fbBoxEspn", HTML),
   "two numbers must never look like one number changing its mind")

esc = js_block("fbEsc", HTML)
ck("🔴 there is a real escaper and it covers all five characters",
   all(c in esc for c in ("&amp;", "&lt;", "&gt;", "&quot;", "&#39;")))
ck("...and every ESPN string in the renderer goes through it",
   "fbEsc(r.name)" in blk and "fbEsc(l)" in blk and "fbEsc(r.stats[i])" in blk,
   "this is the first third-party text this page puts into innerHTML")
ck("⛔ the page has no OTHER global escaper this could have reused",
   src.count("function fbEsc") == 1,
   "the two bare `esc` identifiers in this file are Escape-key handlers")

ck("the live poll is cleared when the modal closes",
   "clearTimeout(BOXT)" in js_block("fbOpenBox", HTML)
   and "fbclose" in js_block("fbOpenBox", HTML),
   "a poll that outlives its modal is a leak that compounds per click")
ck("...and only a LIVE game starts one",
   "if (box && box.live && !FB_BOX_OFF)" in js_block("fbOpenBox", HTML))
ck("🔴 the refresh restores the scroll position",
   "body.scrollTop = y" in js_block("fbOpenBox", HTML),
   "rule 135 — a timer must never move the page under someone's hands")
ck("...and it restores the element that ACTUALLY scrolls",
   "const body = ovl;" in js_block("fbOpenBox", HTML),
   "`.ovl` has overflow-y:auto; `.modal-b` has no overflow, so targeting "
   "it was a silent no-op — caught by the guard on the scroll check")
ck("both sources are fetched in parallel, not in series",
   "Promise.all" in js_block("fbOpenBox", HTML),
   "the stored log is up to 520KB; the summary must not wait for it")
ck("🔴 it refuses to ask when the id is not ESPN's own",
   "/^\\d+$/.test(String(id))" in fetch and "noid" in fetch,
   "NFL 2025 keys are nflverse's (2025_01_DAL_PHI) — measured 0 of 285 "
   "carry an espn column, so asking would be a guaranteed 404")
ck("...and the panel says that rather than showing an HTTP error",
   "do not hold ESPN&#39;s id" in chooser or "do not hold ESPN's id" in chooser,
   "a 404 the page caused itself is not news to the reader")
ck("the join is keyed on the id, never a team name",
   "fbBoxFetch(g.espn || g.id" in js_block("fbOpenBox", HTML), "rule 54")

# ───────────────────────────────────────────────────────────────
srv, PORT = serve()
try:
    from playwright.sync_api import sync_playwright
    _BROWSER = True
except ImportError:
    _BROWSER = False
    note("⚠️ NO BROWSER HERE — the render checks did not run. Expected on "
         "the collector's runner, which installs a bare Python (rule 133).")

if _BROWSER and os.path.exists(FIX):
  FIXTURES = json.load(open(FIX, encoding="utf-8"))
  with sync_playwright() as ctx:
    br = ctx.chromium.launch(args=["--proxy-bypass-list=<-loopback>"])
    # ⚠️ A SHORT VIEWPORT ON PURPOSE. Section 5 has to prove the reader
    #    does not move, and a modal that fits on screen cannot scroll —
    #    the check would pass at 0px -> 0px while asserting nothing
    #    (rule 116). This makes the modal body genuinely scrollable.
    pg = br.new_page(viewport={"width": 1100, "height": 620})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))

    STATE = {"key": "cfb", "hits": 0, "live": False}

    def espn(route):
        u = route.request.url
        if "/summary?" in u:
            STATE["hits"] += 1
            d = json.loads(json.dumps(FIXTURES[STATE["key"]]))
            if STATE["live"]:
                d["header"]["competitions"][0]["status"]["type"] = {
                    "state": "in", "detail": "2nd Quarter — 7:14"}
            return route.fulfill(status=200, content_type="application/json",
                                 body=json.dumps(d))
        return route.fulfill(status=200, content_type="application/json",
                             body='{"events":[]}')

    pg.route("**/site.api.espn.com/**", espn)

    def open_first(league, tab_text):
        pg.goto(f"http://127.0.0.1:{PORT}/index.html",
                wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(1200)
        pg.get_by_text(tab_text, exact=True).first.click()
        pg.wait_for_timeout(600)
        pg.locator("#fbview a[data-fbtab='scores']").click()
        pg.wait_for_function(
            "() => window.__fbShown && window.__fbShown.length > 0",
            timeout=30000)
        return pg.evaluate("""async () => {
            const doc = await fbSchedLoad(fbScSeason);
            const g = (doc.games || []).find(x => x.final) || (doc.games || [])[0];
            if (!g) return null;
            await fbOpenBox(g);
            return String(g.espn || g.id);
        }""")

    print("\n═══ 2. COLLEGE — A REAL ESPN PAYLOAD IN THE MODAL ═══")
    STATE["key"] = "cfb"
    gid = open_first("ncaaf", "College Football")
    ck("the modal opened on a college game", bool(gid), str(gid))
    pg.wait_for_function("() => document.querySelector('#fbbox table.bx')",
                         timeout=30000)
    txt = pg.inner_text("#fbbox")
    low = txt.lower()
    shown = pg.evaluate("() => window.__fbBoxShown")
    ck("🔴 the panel is served from ESPN, not the stored log",
       shown and shown.get("source") == "espn", str(shown))
    # ⛔ ASSERTED AGAINST THE FIXTURE, not against a string typed here.
    cfb = FIXTURES["cfb"]["boxscore"]["players"]
    pblk = [b for t in cfb for b in t["statistics"] if b["name"] == "passing"]
    who = pblk[0]["athletes"][0]["athlete"]["displayName"]
    stats = pblk[0]["athletes"][0]["stats"]
    ck("the passer in the payload is on the page", who in txt, who)
    ck("...and his line is the payload's line",
       all(str(s) in txt for s in stats[:3]),
       "C/ATT + YDS + AVG = " + " ".join(map(str, stats[:3])))
    ck("the three Sam named are labelled",
       all(w in low for w in ("passing", "rushing", "receiving")),
       "case-insensitive: `.bxh` is uppercased by CSS (five false "
       "failures in this repo from forgetting that)")
    hdr = pblk[0]["labels"]
    ck("🔴 the COLLEGE column headings are the payload's own",
       all(h.lower() in low for h in hdr),
       "expected " + " ".join(hdr))
    ck("no page error", not errs, str(errs[:1]))
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(250)

    print("\n═══ 3. NFL — THE SAME RENDERER, DIFFERENT COLUMNS ═══")
    STATE["key"] = "nfl"
    gid = open_first("nfl", "NFL")
    ck("the modal opened on an NFL game", bool(gid), str(gid))
    pg.wait_for_function("() => document.querySelector('#fbbox table.bx')",
                         timeout=30000)
    ntxt = pg.inner_text("#fbbox")
    nlow = ntxt.lower()
    nblk = [b for t in FIXTURES["nfl"]["boxscore"]["players"]
            for b in t["statistics"] if b["name"] == "passing"][0]
    ck("🔴 the NFL heading set is WIDER than college's, and it renders",
       len(nblk["labels"]) > len(hdr)
       and all(h.lower() in nlow for h in nblk["labels"]),
       f"NFL {len(nblk['labels'])} vs college {len(hdr)}: "
       + " ".join(nblk["labels"]))
    ck("...which is exactly what a positional parser would have got wrong",
       "sacks" in nlow and "sacks" not in low,
       "college has no SACKS column in passing")
    nwho = nblk["athletes"][0]["athlete"]["displayName"]
    ck("the NFL passer in the payload is on the page", nwho in ntxt, nwho)
    ck("no page error", not errs, str(errs[:1]))
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(250)

    print("\n═══ 4. 🔴 THE GAME ESPN CARRIES WITH NO PLAYERS ═══")
    STATE["key"] = "d2"
    d2 = FIXTURES["d2"]["boxscore"]["players"]
    n_ath = sum(len(b.get("athletes") or []) for t in d2 for b in t["statistics"])
    ck("the fixture really is empty of players", n_ath == 0, str(n_ath))
    gid = open_first("ncaaf", "College Football")
    pg.wait_for_timeout(1500)
    t4 = pg.inner_text("#fbbox").lower()
    ck("⛔ it says ESPN publishes no player stats for this game",
       "publishes no" in t4 and "player stats" in t4, t4[:110])
    ck("...and calls it an absence rather than showing zeros",
       "absence" in t4 and "not a zero" in t4, t4[:110])
    ck("no page error", not errs, str(errs[:1]))
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(250)

    print("\n═══ 5. 🔴 A LIVE GAME REFRESHES AND MUST NOT MOVE THE READER ═══")
    STATE["key"] = "cfb"
    STATE["live"] = True
    gid = open_first("ncaaf", "College Football")
    pg.wait_for_function("() => document.querySelector('#fbbox table.bx')",
                         timeout=30000)
    t5 = pg.inner_text("#fbbox")
    ck("a live game is badged LIVE with the feed's own clock",
       "LIVE" in t5 and "2nd Quarter" in t5, t5[:90])
    live_flag = pg.evaluate("() => (window.__fbBoxShown||{}).live")
    ck("...and the page knows it is live", live_flag is True, str(live_flag))
    # Scroll the MODAL BODY down, wait for one poll, and check it stayed.
    pg.evaluate("() => { const b=document.querySelector('.ovl');"
                " if (b) b.scrollTop = 320; }")
    pg.wait_for_timeout(150)
    y0 = pg.evaluate("() => { const b=document.querySelector('.ovl');"
                     " return b ? b.scrollTop : -1; }")
    # 🔴 THE GUARD ON THE GUARD. If the panel never scrolled, "it did not
    #    move" is true of nothing. This repo has had five checks that
    #    passed while asserting nothing.
    ck("the modal really is scrolled down before the poll fires",
       y0 > 50, f"{y0}px — a 0 here would make the next check vacuous")
    n0 = STATE["hits"]
    pg.wait_for_timeout(47000)
    n1 = STATE["hits"]
    y1 = pg.evaluate("() => { const b=document.querySelector('.ovl');"
                     " return b ? b.scrollTop : -1; }")
    ck("🔴 it polled again while the modal stayed open", n1 > n0,
       f"{n0} -> {n1} summary requests")
    ck("🔴 and the reader did not move", abs(y1 - y0) <= 12,
       f"{y0}px -> {y1}px")
    ck("no page error", not errs, str(errs[:1]))

    print("\n═══ 6. CLOSING THE MODAL STOPS THE POLL ═══")
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    n2 = STATE["hits"]
    pg.wait_for_timeout(50000)
    ck("⛔ no further request after it closed", STATE["hits"] == n2,
       f"{n2} -> {STATE['hits']}")

    print("\n═══ 7. A REFUSAL FALLS BACK, ONCE, AND STOPS ASKING ═══")
    STATE["live"] = False
    pg.unroute("**/site.api.espn.com/**")
    REF = {"n": 0}

    def refuse(route):
        if "/summary?" in route.request.url:
            REF["n"] += 1
            return route.abort()
        return route.fulfill(status=200, content_type="application/json",
                             body='{"events":[]}')

    pg.route("**/site.api.espn.com/**", refuse)
    gid = open_first("ncaaf", "College Football")
    pg.wait_for_timeout(1600)
    t7 = pg.inner_text("#fbbox").lower()
    ck("🔴 a refused fetch says so in plain words",
       "could not reach" in t7, t7[:110])
    ck("...and it falls back to the stored logs rather than an empty box",
       "stored player log" in t7 or "absence" in t7 or "no player log" in t7,
       t7[:110])
    first = REF["n"]
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(200)
    pg.evaluate("""async () => {
        const doc = await fbSchedLoad(fbScSeason);
        const g = (doc.games || []).filter(x => x.final)[1] || (doc.games||[])[1];
        if (g) await fbOpenBox(g);
    }""")
    pg.wait_for_timeout(1400)
    ck("⛔ ONE refusal is enough — it does not ask again this session",
       REF["n"] == first, f"{first} -> {REF['n']} requests")
    ck("no page error", not errs, str(errs[:1]))

    br.close()
elif _BROWSER:
    note("⚠️ espnfix.json is missing — the render checks did not run.")

srv.shutdown()
