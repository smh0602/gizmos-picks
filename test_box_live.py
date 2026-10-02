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

`[Sam, 2026-10-01]` *"i just want what's supposed to be in each tab to be
in each tab"* — the panel draws no note and no tag any more: no source
note, no ESPN / LIVE tag, no refusal / id / HTTP note, no "absence, not a
zero" sentence. The checks that required them now require their ABSENCE,
and each declares the edit that puts back what it guards. A browser check
(sections 4, 5, 7) shares its declaration with the section-1 check that
asks the same thing without a browser — the sweep runs where there is none.

# @vacuity §1: a block with more values than headings carries no note
#   file: index.html
#   find: return `<h4 class="bxh">${nm.charAt(0).toUpperCase() + nm.slice(1)}</h4>
#   with: return `<h4 class="bxh">${nm.charAt(0).toUpperCase() + nm.slice(1)}</h4><div class="note">Only the columns both sides carry are shown.</div>
#
# @vacuity §1 + §4 (browser): the Division II case is one plain line, no 'absence' sentence
#   file: index.html
#   find: ? `<p class="plain">ESPN carries this game but publishes no
#   with: ? `<div class="note">An absence, not a zero.</div><p class="plain">ESPN carries this game but publishes no
#
# @vacuity §1: the ESPN panel carries no source note
#   file: index.html
#   find: return `<p class="plain">${fbEsc(box.detail || (box.live ? 'in progress' : 'final'))}</p>
#   with: return `<div class="note bxsrc">The Track Record grades against our own stored logs, not against this.</div><p class="plain">${fbEsc(box.detail || (box.live ? 'in progress' : 'final'))}</p>
#
# @vacuity §1 + §5 (browser): a live panel carries no LIVE tag
#   file: index.html
#   find: return `<p class="plain">${fbEsc(box.detail || (box.live ? 'in progress' : 'final'))}</p>
#   with: return `<p class="plain">${box.live ? '<span class="kind k-live">LIVE</span> ' : ''}${fbEsc(box.detail || (box.live ? 'in progress' : 'final'))}</p>
#
# @vacuity §1: an id-less request prints no note
#   file: index.html
#   find: const why = (box && box.state === 'pre')
#   with: const why = (box && box.noid) ? '<div class="note">We do not hold ESPN&#39;s id for this season.</div>' : (box && box.state === 'pre')
#
# @vacuity §1 + §7 (browser): a refused request prints no note
#   file: index.html
#   find: const why = (box && box.state === 'pre')
#   with: const why = FB_BOX_OFF ? '<div class="note">Your browser could not reach ESPN&#39;s game summary.</div>' : (box && box.state === 'pre')
#
# @vacuity §1 (driven) + §7 (browser): a refused request still falls back to the stored log
#   file: index.html
#   find: const stored = fbBoxStored(g, by);
#   with: const stored = box ? fbBoxStored(g, by) : '';
"""
import glob
import gzip
import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import tempfile
import threading
import datetime

from jsblock import calls, js_block, source
from tcheck import ck, note, shown

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
    # ⛔ ~~ck("🔴 most Division I games played have NO stored player log",
    #        have < len(played) / 2, ...)~~
    # 🔴🔴 STRUCK 2026-09-14. **THIS CHECK ASSERTED THAT A BUG STILL
    #    EXISTED, SO IT WENT RED WHEN THE PRODUCT GOT BETTER.**
    #
    #    It was written on 2026-09-06 to prove the stored log could never
    #    answer Sam's box-score question — 17 of 202 games had one. The
    #    college logs moved to a DAILY rebuild that same night, coverage
    #    climbed, and on 2026-09-14 it read **185 of 339 (55%)** and the
    #    assertion failed. ⛔ **Every scheduled run had been going red on
    #    it**, which is worse than useless: Sam reported *"a bunch of
    #    failed runs"* and a real failure was by then indistinguishable
    #    from this one.
    #
    # ➡️ **RULE 166 IN ITS PUREST FORM — a check whose subject is a
    #    TRANSIENT state has an expiry date and nothing expires it — with
    #    the cruellest twist available: the expiry condition was the fix
    #    landing.** A check that fails when the thing it describes is
    #    repaired is not a regression test, it is a snapshot with an
    #    assertion bolted on.
    #
    # ⚠️ CLAUDE.md FORBIDS WEAKENING A CHECK AND REQUIRES THE ARGUMENT BE
    #    MADE. Here it is: the question *"is the stored log thin?"* was
    #    only ever evidence for a DECISION that is already taken and
    #    already asserted elsewhere in this file — *"ESPN is preferred and
    #    the stored log is the FALLBACK"*, section 2. Re-proving the
    #    motive every run buys nothing and costs a red tick.
    # ✅ AND IT IS REPLACED WITH A STRICTLY HARDER ONE, not merely
    #    deleted. The measurement survives as a `note`; the assertion
    #    becomes a durable property of the data that CANNOT expire and
    #    that nothing else in the suite covers.
    note(f"stored-log coverage today: {have} of {len(played)} Division I "
         f"games played ({100.0 * have / max(1, len(played)):.0f}%). "
         f"⚪ MEASURED, NOT ASSERTED — this number is allowed to be "
         f"anything, including 100%.")

    # 🔴 THE REPLACEMENT, AND IT IS ABOUT A CAPABILITY RATHER THAN A
    #    DEFECT: every played game the tab can open must carry ESPN's own
    #    event id, or the reader is stuck with whatever the stored log
    #    has and has NO ROUTE to the live source at all.
    # ⛔ THIS IS NOT HYPOTHETICAL. The id is a COLUMN of the weekly
    #    rebuild, and it has already been absent once — 0 of 285 NFL 2025
    #    games carry one, which is why that season is refused rather than
    #    404'd. A rebuild that drops the column again would silently
    #    disable the live box score for every game, and **the old check
    #    would have gone GREEN on exactly that failure** — losing the
    #    live path makes the stored log MORE load-bearing, not less.
    _noid = [g for g in played if not g.get("espn")]
    ck("🔴 every played Division I game carries ESPN's own event id",
       not _noid,
       "⛔ without it `fbOpenBox` refuses to ask (section 2) and the "
       "reader is left on the stored log with no way to the live source. "
       f"{len(_noid)} of {len(played)} game(s) have no id: "
       f"{[g.get('id') for g in _noid[:5]]}")
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
# `[Sam, 2026-10-01]` THE BOXES AND TAGS THE PAGE NO LONGER DRAWS, asked of
#    one renderer's body at a time (test_page_plain.py asks the whole page).
_BOXED = re.compile(r"""class=["'][^"']*\b(?:note|fnote|fbnotes|glwarn|domnote|kind)\b""")

ck("🔴 the columns are read from the payload, never hard-coded",
   "s.labels" in parse and "b.labels" in blk,
   "rule 121 — the two leagues carry different passing columns")
ck("...and no positional column name is written into the renderer",
   not any(w in blk for w in ("'C/ATT'", '"C/ATT"', "'SACKS'", '"RTG"')),
   "a literal here is an assumption about a schema we do not own")
# [Sam, 2026-10-01] ~~"...and says the rest arrived"~~ — that was a note box
#    ("This block arrived with N column headings ...") and the page draws no
#    explanation boxes any more. The rule beside it is kept: only the
#    columns both sides carry are rendered, and nothing is shifted.
ck("a row with more values than headings is NOT shifted left to fit",
   "Math.min(b.labels.length, wide)" in blk and not _BOXED.search(blk),
   "it renders the columns both sides carry — and, since 2026-10-01, no "
   "note about the rest")
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
# [Sam, 2026-10-01] ~~"...and says ABSENCE"~~ — "An absence, not a zero" was
#    a sentence in a note box, and the boxes are gone: the Division II case
#    is ONE plain line now. (The old form accepted the line OR the sentence;
#    this requires the line AND the sentence gone.)
ck("a game ESPN carries with no players says so, in one plain line",
   '<p class="plain">ESPN carries this game but publishes no' in chooser
   and "absence, not a zero" not in chooser.lower(),
   "the Division II case in the fixtures")
ck("🔴 an unplayed game is NOT reported as 'no player stats'",
   "box.state === 'pre'" in chooser and "has not kicked off" in chooser,
   "measured live: the 2026 NFL opener returns state=pre with 0 players "
   "and the kickoff time — calling that 'ESPN publishes none' repeats "
   "rule 134")
ck("...and a game under way with no stats yet says THAT instead",
   "box.live" in chooser and "not posted any player stats yet" in chooser,
   "three different facts, three different sentences")
# [Sam, 2026-10-01] ~~"...and the panel names WHICH source it is showing"~~ —
#    that was a note box ("player stats from ESPN's public game summary ...
#    The Track Record grades against our own stored logs, not against this")
#    under an ESPN / LIVE tag, and the page draws neither any more. ✅ Kept:
#    the PAGE still records which source drew the panel
#    (`window.__fbBoxShown.source`), which section 2 reads in a browser.
_espn = js_block("fbBoxEspn", HTML)
ck("...and the panel carries no source note and no tag — the page keeps the source",
   not _BOXED.search(_espn) and "stored logs, not against this" not in _espn
   and "(box && box.sides) ? 'espn'" in js_block("fbOpenBox", HTML),
   "two numbers must never look like one number changing its mind — the "
   "source is the page's own record now, not a sentence")

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
# [Sam, 2026-10-01] ~~"...and the panel says that rather than showing an HTTP
#    error"~~ — "We do not hold ESPN's id for this season" was a note box, as
#    were "Your browser could not reach ESPN's game summary" and "ESPN
#    returned no summary (HTTP n)", and the page draws no explanation boxes
#    any more. ✅ Kept: none of the three has a branch of its own in the
#    chooser, so each falls through to the stored log — and still no HTTP
#    error reaches the reader.
ck("...and the panel prints nothing for it but the stored log",
   not any(s in chooser for s in ("box.noid", "box.http", "FB_BOX_OFF",
                                  "do not hold ESPN", "could not reach"))
   and not _BOXED.search(chooser),
   "a 404 the page caused itself is not news to the reader — nor, since "
   "2026-10-01, is a refusal or a failed status")
# [Sam, 2026-10-01] THE SILENT FALLBACK, DRIVEN ON EVERY RUNNER. Section 7
#    drives a refusal in a browser and the collector's runner has none, so
#    the page's own renderers are lifted into node (as test_live_scores.py
#    §0b2 lifts fbMerge): a refused, id-less or failed request must render
#    EXACTLY what the stored log renders — its tables, or its own line.
_lift = "\n".join([
    "let LEAGUE = 'ncaaf', fbScSeason = 2026, FB_BOX_OFF = false;",
    "const FB_BOX_MAIN = ['passing', 'rushing', 'receiving'];",
    "const fbMark = () => '', fbAb = x => x;",
    "const fbBoxTable = (m, k, l) => k === 'pass'"
    " ? '<table class=\"bs bx\"><tr><td>' + l + m.length + '</td></tr></table>' : '';",
    *[js_block(f, HTML) for f in ("fbEsc", "fbBoxSort", "fbBoxBlock", "fbBoxSide",
                                  "fbBoxEspn", "fbBoxStored", "fbBoxScore")],
    "const g = { id: 7, away: 'A', home: 'H' };",
    "const by = { '7': [{ r: { team: 'A' } }, { r: { team: 'H' } }] };",
    "const out = [];",
    "for (const [off, box] of [[true, null], [false, { noid: true }], [false, { http: 404 }]])",
    "  for (const b of [by, {}, null]) {",
    "    FB_BOX_OFF = off;",
    "    out.push([fbBoxScore(g, b, box), fbBoxStored(g, b)]);",
    "  }",
    "console.log(JSON.stringify(out));",
])
_ld = tempfile.mkdtemp()
try:
    open(os.path.join(_ld, "fallback.js"), "w", encoding="utf-8").write(_lift)
    _lr = subprocess.run(["node", os.path.join(_ld, "fallback.js")],
                         capture_output=True, text=True, encoding="utf-8")
finally:
    shutil.rmtree(_ld, ignore_errors=True)
_FB = (json.loads(_lr.stdout.strip().splitlines()[-1])
       if _lr.returncode == 0 and _lr.stdout.strip() else None)
ck("🔴 ...and each of them renders EXACTLY the stored log — driven, not read",
   bool(_FB) and all(got == want for got, want in _FB) and "<table" in _FB[0][1],
   shown(_lr.stderr[-300:]) if _lr.returncode
   else "%d of %d case(s) differ from the stored log"
        % (sum(1 for got, want in (_FB or []) if got != want), len(_FB or [])))
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
    # ⛔ NO REQUEST LEAVES THIS MACHINE. `[2026-09-28]` Sam: "A test must
    #    not depend on the network." Every page load boots the MLB tab
    #    (statsapi.mlb.com) and asks mlbstatic/espncdn for logos; none of
    #    that was stubbed, so a live third-party answer could reach the "no
    #    page error" checks. Registered FIRST — Playwright tries the newest
    #    route first — so the ESPN stubs below still answer their own URLs;
    #    anything else off this machine is aborted (the page already copes
    #    with a feed it cannot reach) and counted. test_live_scores.py §0
    #    fails if a browser test loses this line.
    _offsite = []
    pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("http://127.0.0.1:", "http://localhost:")) else (_offsite.append(r.request.url), r.abort()))

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
        pg.locator("nav.subnav a[data-tab='scores']").click()
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
    # [Sam, 2026-10-01] ~~"...and calls it an absence rather than showing
    #    zeros" ("absence" / "not a zero")~~ — that sentence was in a note
    #    box, and the page draws no explanation boxes any more. What it
    #    protected is read off what renders: the empty payload is never the
    #    panel's source, so no table of zeros can come from it.
    s4 = pg.evaluate("() => window.__fbBoxShown || {}")
    ck("...and draws nothing from the empty payload, with no 'absence' note",
       s4.get("source") in ("stored", "none") and "not a zero" not in t4
       and pg.locator("#fbbox .note").count() == 0,
       "%s — %s" % (s4.get("source"), t4[:110]))
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
    # [Sam, 2026-10-01] ~~"a live game is badged LIVE with the feed's own
    #    clock"~~ — the LIVE badge was a tag (`span.kind k-live`), and the page
    #    draws no tags any more. ✅ Kept: the feed's own clock is the panel's
    #    first line, and the page still knows the game is live (next check).
    ck("a live game shows the feed's own clock, with no LIVE tag",
       "2nd Quarter" in t5 and pg.locator("#fbbox .kind").count() == 0,
       t5[:90])
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
    # ⚠️ `[2026-10-01]` WAIT FOR THE PANEL, NOT A CLOCK: the first check below
    #    asserts an ABSENCE, and an absence read before the panel has drawn
    #    is true of nothing (rule 116).
    pg.wait_for_function("() => window.__fbBoxShown", timeout=30000)
    t7 = pg.inner_text("#fbbox").lower()
    s7 = pg.evaluate("() => window.__fbBoxShown || {}")
    # [Sam, 2026-10-01] ~~"🔴 a refused fetch says so in plain words" ("could
    #    not reach")~~ — that sentence was a note box, and the page draws no
    #    explanation boxes any more: a refusal prints nothing and the stored
    #    log shows. (Section 1 drives the same rule in node, every run.)
    ck("🔴 a refused fetch prints no note of its own",
       "could not reach" not in t7 and pg.locator("#fbbox .note").count() == 0,
       t7[:110])
    # [Sam, 2026-10-01] THE FALLBACK IS UNCHANGED. It was read off the note's
    #    wording ("stored player log") and is now read off what renders: the
    #    stored log's tables, or the stored log's own one-line empty state.
    n7 = pg.locator("#fbbox table").count()
    ck("...and it falls back to the stored logs rather than an empty box",
       (s7.get("source") == "stored" and n7 > 0)
       or (s7.get("source") == "none" and "no player log" in t7),
       "%s, %d table(s): %s" % (s7.get("source"), n7, t7[:110]))
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
    note("%d off-machine request(s) blocked, none answered by the network: "
         "%s" % (len(_offsite), sorted({u.split("/")[2] for u in _offsite})))

    br.close()
elif _BROWSER:
    note("⚠️ espnfix.json is missing — the render checks did not run.")

srv.shutdown()
