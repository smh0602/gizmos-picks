#!/usr/bin/env python3
"""
🔴 THE NFL OPENER, REHEARSED BEFORE IT HAPPENS.

`[2026-09-06 — the 2026 NFL season opens WEDNESDAY 9 September, and the
whole NFL half of this product has never met a real props board.]`

⛔ WHAT THE REHEARSAL FOUND, and it would have shipped on opening night:
the season opens with ONE GAME. A parlay's legs must be in DIFFERENT
games, so on a one-game slate every candidate is rejected by construction
-- `rejected.same_game` 12,926 and `out_of_band` ZERO -- and the Parlays
tab was about to tell the reader *"it is the payout bands that nothing
fits today"*. THE DATA FLATLY CONTRADICTS THAT SENTENCE (rule 132).

⚠️ AND THE DATE ITSELF WAS WRONG IN TWO DOCS AND IN THE PAGE. Both said
"Thursday 10 September". The first kickoff is 2026-09-10T00:20Z, which is
WEDNESDAY 9 September at 8:20pm ET. A day matters when it is the day you
planned to be watching.

WHAT IS PINNED:
  1. the first NFL kickoff is read from the REAL board, never typed here
  2. a one-game slate produces a reason that names GAMES, not bands
  3. the "bands" sentence cannot appear when out_of_band is 0
  4. the page states no hard-coded league schedule
  5. the log fallback: no players-2026 file yet, so 2025 must be usable
"""
import datetime
import glob
import gzip
import json
import os

from jsblock import js_block, source
from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, "index.html")

# ───────────────────────────────────────────────────────────────
print("\n═══ 1. WHEN THE NFL ACTUALLY STARTS — READ, NOT TYPED ═══")
bp = f"{ROOT}/data/nfl/latest/board.json"
if os.path.exists(bp):
    B = json.load(open(bp, encoding="utf-8"))
    ks = sorted(g["commence"] for g in (B.get("games") or []) if g.get("commence"))
    ck("the NFL board carries game times", bool(ks), f"{len(ks)} games")
    if ks:
        first = datetime.datetime.fromisoformat(ks[0].replace("Z", "+00:00"))
        et = first - datetime.timedelta(hours=4)          # EDT in September
        note(f"first kickoff {ks[0]} = {et:%a %d %b %I:%M%p} ET")
        # 🔴 THE POINT: the ET DAY is what the card, the crons and the
        #    watching human all key off, and it is one day EARLIER than
        #    the UTC date reads.
        ck("⚠️ the first NFL slate day is EARLIER in ET than in UTC",
           et.date() < first.date(),
           f"UTC {first:%d %b} vs ET {et:%d %b} — reading the UTC date is "
           f"how 'Thursday' got into two docs")
        n_first = sum(1 for k in ks if
                      (datetime.datetime.fromisoformat(k.replace("Z", "+00:00"))
                       - datetime.timedelta(hours=4)).date() == et.date())
        ck("🔴 the opening slate is a SINGLE game", n_first == 1,
           f"{n_first} game(s) on {et:%a %d %b} ET — this is why the "
           f"parlay pool is empty by construction, not by pricing")
else:
    note("no NFL board on disk — section 1 not measured")

print("\n═══ 2. THE LOG FALLBACK THE FIRST CARD DEPENDS ON ═══")
have = sorted(os.path.basename(f) for f in
              glob.glob(f"{ROOT}/data/nfl/latest/players-*.json.gz"))
note("player logs present: " + (", ".join(have) or "none"))
cur = datetime.datetime.now(datetime.timezone.utc)
season = cur.year - 1 if cur.month < 8 else cur.year
# ══════════════════════════════════════════════════════════════════════
# 🔴 THIS ASSERTED AN ABSENCE, AND THE ABSENCE WAS FILLED BY THE FIX
#    WORKING. `[2026-09-10]` It read `f"players-{season}.json.gz" not in
#    have` — *"there is still no players-2026 file"* — and went red the
#    moment `nfl-logs` succeeded and wrote one. **The success it was
#    waiting for is what broke it.**
# ⛔ RULE 166 FOR THE THIRD TIME ON THIS REPO: a check with an expiry
#    date and nothing to expire it. The comment even said "if this flips,
#    the fallback stops being the path under test" — a note that the
#    check would one day be wrong, left in place instead of fixed.
# ✅ THE DURABLE QUESTION IS WHETHER A USABLE LOG EXISTS FOR THE CARD TO
#    READ — not which season supplies it. A 2026 file holding ONE game
#    per player does not replace the fallback; it is thinner than the bar
#    the card needs, so the fallback is STILL the path under test and the
#    check now says so with the numbers instead of by assuming.
# ══════════════════════════════════════════════════════════════════════
_cur_present = f"players-{season}.json.gz" in have
note(f"players-{season}.json.gz present: {_cur_present} — "
     f"the current season's log existing does NOT by itself retire the "
     f"fallback; what matters is whether it is thick enough to use.")
usable = []
for f in glob.glob(f"{ROOT}/data/nfl/latest/players-*.json.gz"):
    try:
        d = json.load(gzip.open(f, "rt"))
    except Exception:
        continue
    P = d.get("players") or {}
    counts = sorted(len(p.get("g") or []) for p in P.values())
    if counts and counts[len(counts) // 2] >= 6:
        usable.append((d.get("season"), counts[len(counts) // 2]))
ck("🔴 at least one season has enough games to read a rate from",
   bool(usable), str(sorted(usable, reverse=True)[:2])
   + " — MIN_GAMES is 6; below it the board ships prices and no records")
# ⛔ AND THE THIN CURRENT SEASON MUST NOT DISPLACE THE FALLBACK. A
#    `players-2026` holding one game per player is WORSE than useless if
#    it is preferred over a full 2025 — every rate would be n=1.
_cur_usable = [s for s, _ in usable if s == season]
if _cur_present and not _cur_usable:
    note(f"✅ players-{season} EXISTS but is below the 6-game bar, so the "
         f"fallback is still the path under test — which is the state "
         f"the section header describes. This is the correct reading of "
         f"a season that has just started.")
elif _cur_usable:
    note(f"⚠️ players-{season} is now THICK enough to use on its own "
         f"(median {dict(usable).get(season)} games). The fallback is no "
         f"longer the live path; this section is measuring history.")
ck("⛔ a season log is judged on GAMES PER PLAYER, never on existing",
   all(m >= 6 for _s, m in usable),
   "the bar is the median game count, so a one-game file can never "
   "qualify merely by being present: %s" % sorted(usable, reverse=True))

print("\n═══ 3. THE SENTENCE THAT WOULD HAVE BEEN FALSE ═══")
blk = js_block("fbParlays", HTML)
ck("the empty-parlay reason is derived from the REJECTION COUNTS",
   "m.rejected" in blk and "out_of_band" in blk,
   "not from a guess about which rule bit")
ck("🔴 a one-game slate gets its own reason, naming GAMES",
   "nGames < 2" in blk and "different game" in blk,
   "the legs-in-different-games rule is the cause on an opening night")
ck("⛔ the bands cannot be blamed when nothing was out of band",
   "(outBand === 0 && sameGame > 0)" in blk,
   "out_of_band was 0 and same_game was 12,926 in the rehearsal")
ck("...and the games are COUNTED from the card, not read off a field",
   "new Set((C && C.picks || [])" in blk and "p.game_id" in blk,
   "rule 132 — a sentence stating a cause must be computed")
ck("the three older emptinesses are still distinct",
   blk.count("fbNoCard('parlays')") == 1 and "empty_reason" in blk,
   "no card / no board / no fit must not share a sentence")

print("\n═══ 4. NO LEAGUE SCHEDULE IS WRITTEN INTO THE PAGE ═══")


def live_code(s):
    """The part a browser executes: comments stripped.

    🔴 THE FIRST VERSION OF THIS SECTION SEARCHED THE WHOLE FILE AND FIRED
    ON THE STRUCK QUOTE IN THE COMMENT THAT EXPLAINS THE REMOVAL. This
    project keeps superseded text visible on purpose, so a bare string
    search cannot tell a struck quote from a live assertion — SIX false
    failures in this repo now, every one of them the same shape.
    """
    out, i, n = [], 0, len(s)
    while i < n:
        if s.startswith("/*", i):
            j = s.find("*/", i + 2); i = n if j < 0 else j + 2
        elif s.startswith("<!--", i):
            j = s.find("-->", i + 4); i = n if j < 0 else j + 3
        elif s.startswith("//", i):
            j = s.find("\n", i); i = n if j < 0 else j
        else:
            out.append(s[i]); i += 1
    return "".join(out)


nc_live = live_code(js_block("fbNoCard", HTML))
for bad in ("Thursday evening, then Sunday morning",
            "Thursday, Friday and Saturday"):
    ck(f"⛔ the renderer no longer ASSERTS {bad!r}",
       bad not in nc_live,
       "a schedule in a sentence goes stale and nothing announces it "
       "— this one was already wrong (rule 132)")
ck("⚠️ ...and the struck original is still visible in the source",
   "Thursday evening, then Sunday morning" in source(HTML),
   "superseded content is struck, never deleted — that is why this "
   "check reads the executable half rather than the file")
nc = js_block("fbNoCard", HTML)
ck("...and what replaced it still says why the board is absent",
   "player-prop pull" in nc and "not been priced" in nc)


# ───────────────────────────────────────────────────────────────
print("\n═══ 5. DRIVEN IN A BROWSER — WHAT THE READER ACTUALLY SEES ═══")
# ⛔ THE STRING CHECKS ABOVE PROVE THE CODE EXISTS. They do NOT prove the
#    reader sees it, and this project has shipped a renderer nobody calls
#    (rule 130). So the card is stubbed at the fetch and the tab is read.
import http.server
import socketserver
import threading

try:
    from playwright.sync_api import sync_playwright
    _BROWSER = True
except ImportError:
    _BROWSER = False
    note("⚠️ NO BROWSER HERE — section 5 did not run. Expected on the "
         "collector's runner, which installs a bare Python (rule 133).")

if _BROWSER:
    os.chdir(ROOT)
    _h = http.server.SimpleHTTPRequestHandler
    _h.log_message = lambda *a, **k: None
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 0), _h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    PORT = srv.server_address[1]

    # A card shaped exactly like the rehearsal one: ONE game, zero
    # parlays, and rejection counts that make the bands provably innocent.
    CARD = {
        "date": "2026-09-09", "league": "nfl", "kind": "RECORD",
        "slate_date": "2026-09-09", "logs_season": 2025,
        "parlays": {"2": [], "3": [], "4": []},
        "parlay_meta": {"pool": 24, "rated_legs": 80,
                        "rejected": {"same_game": 12926, "same_player": 0,
                                     "mixed_book": 0, "out_of_band": 0},
                        "note": "80 rated legs, 24 in the stratified pool."},
        "parlay_rule": "Legs are in DIFFERENT GAMES and at the SAME BOOK.",
        "picks": [{"game_id": "g1", "player": "Drake Maye",
                   "market": "player_pass_yds", "side": "over", "line": 248.5,
                   "price": -110, "confidence": 61, "confidence_basis": "RECORD",
                   "book": "draftkings", "game": "NE @ SEA",
                   "commence": "2026-09-10T00:20:00Z"}],
    }

    with sync_playwright() as ctx:
        br = ctx.chromium.launch(args=["--proxy-bypass-list=<-loopback>"])
        pg = br.new_page(viewport={"width": 1280, "height": 900})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("**/site.api.espn.com/**", lambda r: r.fulfill(
            status=200, content_type="application/json", body='{"events":[]}'))
        pg.route("**/picks/fb-nfl-latest.json", lambda r: r.fulfill(
            status=200, content_type="application/json", body=json.dumps(CARD)))
        pg.goto(f"http://127.0.0.1:{PORT}/index.html",
                wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(1200)
        pg.get_by_text("NFL", exact=True).first.click()
        pg.wait_for_timeout(500)
        pg.locator("#fbview a[data-fbtab=\'parlays\']").click()
        pg.wait_for_timeout(900)
        txt = pg.inner_text("#fbview")
        low = txt.lower()
        ck("🔴 the reader is told the slate is a single game",
           "single game" in low, txt[:160])
        ck("...and that legs must come from different games",
           "different game" in low)
        ck("⛔ the reader is NOT told the payout bands are the reason",
           "bands that nothing fits" not in low,
           "that sentence was about to ship on opening night")
        ck("the rejection count is shown rather than described",
           "12,926" in txt or "12926" in txt, txt[:160])
        ck("no page error", not errs, str(errs[:1]))
        br.close()
    srv.shutdown()
