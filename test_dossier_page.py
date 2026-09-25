#!/usr/bin/env python3
"""
🔴🔴 SAM'S EIGHT SIGNALS WERE COMPUTED, AUDITED, ARCHIVED — AND INVISIBLE.

    $ grep -c 'dossier' index.html
    0

`dossier_fb.py` has run on every `card-fb` arm since 2026-09-17, writing
eight checks for every game on both boards, gating itself on an audit and
keeping a dated write-once archive. ⛔ **Nothing read the file.** The page
fetched `board.json`, `freshness.json`, `news.json`, `props.json.gz`,
`record-detail.json.gz` and `record.json`, and nothing else.

⚠️ AND THE MISS THAT ALLOWED IT: reviewing PR #38 the artifact was
verified — 32 of 32 games, all eight sections — and reported as working.
⛔ **Nothing checked that anything READ it.** An artifact nothing renders
is not a feature, and "the file is correct" is a different claim from
"the product shows it".

🔴 SO THIS FILE ASKS THE SECOND QUESTION, AND IT ASKS IT BY RUNNING THE
SHIPPED CODE. It slices the panel out of `index.html`, evals it in node,
and renders THE REAL ARTIFACT for BOTH leagues — ledger rule 197: the
game-lines section existed, was wired, and simply never drew, and that
was found by loading the page rather than by reading it.

⛔ WHAT IT WILL NOT DO IS READ THE SOURCE AND BE SATISFIED. `calls()` is
used for the wiring, because a renderer nobody calls looks exactly like
the one that draws the page (rule 130) — but every claim about what the
reader SEES is made against rendered HTML.
"""

# ══════════════════════════════════════════════════════════════════════
# @vacuity the panel joins on the board's own id, never on team names
#   file: index.html
#   find: (((D || {}).dossiers) || []).forEach(x => { if (x.board_id) m.set(x.board_id, x); });
#   with: (((D || {}).dossiers) || []).forEach(x => { m.set((x.away_name||'') + (x.home_name||''), x); });
#
# @vacuity a section that cannot answer is SHOWN, never hidden
#   file: index.html
#   find: const gap = s.state !== 'OK';
#   with: const gap = s.state !== 'OK'; if (gap) return '';
#
# @vacuity a partial game NAMES the side with no season record
#   file: index.html
#   find: u ? `<span class="dospart">no season record for ${u}</span>` : ''
#   with: ''
#
# @vacuity a section that CAN answer shows a stored value, not a sentence
#   file: index.html
#   find: return f.length ? `<ul class="df">${f.join('')}</ul>` : '';
#   with: return '';   // the values are dropped and only prose is drawn
#
# @vacuity the book count says WHAT IT COUNTS — books with a moneyline
#   file: index.html
#   find: li('Books with a moneyline', L.n_books);
#   with: li('Books priced', L.n_books);   // the label that read "priced 0"
# ══════════════════════════════════════════════════════════════════════

import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from jsblock import calls, js_block
from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, "index.html")
HTML = open(PAGE, encoding="utf-8").read()

# 🔴 THE JARGON BAR IS `verify_card.py`'s OWN LIST, READ OUT OF IT.
# ⛔ A second copy would be a second thing to drift (rule 66), and the
#    MLB card's bar is the standard Sam set — the football panel does not
#    get an easier one.
_VC = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
_m = re.search(r"_JARGON = (\[[^\]]*\])", _VC, re.S)
JARGON = eval(_m.group(1)) if _m else []

# ⚠️ AND A SECOND, STRICTER BAR THE PAGE NEEDS AND THE CARD DOES NOT:
#    filenames, paths, backticked code and collector mode names. Driving
#    this found one section `why` carrying "`top-2026.json.gz` under
#    `data/`" on all 32 NFL games — jargon-list clean and still unreadable
#    (Sam, 2026-08-26: "all of these things that a casual fine wont know
#    about has to go"). ⛔ It was fixed IN THE BUILDER, not filtered here.
OPERATOR = re.compile(r"`[^`]+`|[\w./-]+\.json(?:\.gz)?|nfl-logs|cfb-probe"
                      r"|props-board|card-fb|data/")


def build(lg):
    """The real builder, on the real board, in a throwaway tree.

    ⛔ NOT THE COMMITTED ARTIFACT. `data/nfl/latest/dossiers.json.gz` on
    disk was written before `board_id` existed, so a check reading it
    would be asking about yesterday's builder."""
    d = tempfile.mkdtemp(prefix="dospage-")
    for f in os.listdir(ROOT):
        if f.endswith(".py") or f.endswith(".json"):
            shutil.copy(os.path.join(ROOT, f), d)
    shutil.copytree(os.path.join(ROOT, "data", lg), os.path.join(d, "data", lg))
    p = os.path.join(d, "data", lg, "latest", "dossiers.json.gz")
    if os.path.exists(p):
        os.remove(p)
    r = subprocess.run([sys.executable, "-B", "dossier_fb.py"], cwd=d,
                       timeout=600, capture_output=True, text=True,
                       env=dict(os.environ, LEAGUE=lg))
    doc = json.load(gzip.open(p, "rt")) if os.path.exists(p) else None
    return d, doc, (r.stdout or "") + (r.stderr or "")


# ⚠️ ONE COPY OF THE DRIVER, WRITTEN OUT AT RUN TIME. It slices the panel
#    from the SHIPPED page rather than holding a copy of it — a copy is
#    the failure `test_banner.py`'s ancestor shipped, testing a file that
#    only existed in a scratch directory.
DRIVER = r"""
const fs = require('fs'), zlib = require('zlib');
const html = fs.readFileSync(process.argv[2], 'utf8');
const a = html.indexOf('const FBDOS = {};');
const b = html.indexOf('function fbOddsTable(list){');
if (a < 0 || b < 0 || b <= a){ console.error('PANEL_CODE_NOT_FOUND'); process.exit(2); }
const fn = new Function('LG_DATA','document','jgetGz', html.slice(a, b) +
  '\nreturn {fbDossierBy, fbDossierHtml};');
const M = fn({ mlb:'data', nfl:'data/nfl', ncaaf:'data/ncaaf' },
             { querySelectorAll: () => [], querySelector: () => null },
             async () => null);
const D = JSON.parse(zlib.gunzipSync(fs.readFileSync(process.argv[3])).toString());
const idx = M.fbDossierBy(D);
const rows = (D.dossiers || []).map(x => ({
  board_id: x.board_id || null,
  matched: idx.get(x.board_id) === x,
  unresolved_side: x.unresolved_side || null,
  n_sections: (x.sections || []).length,
  html: M.fbDossierHtml(idx.get(x.board_id))
}));
process.stdout.write(JSON.stringify({
  n_indexed: idx.size,
  miss_html: M.fbDossierHtml(idx.get('a-board-id-no-game-has')),
  rows
}));
"""


def drive(doc, tree):
    """Render every game through the SHIPPED panel code, in node."""
    dp = os.path.join(tree, "drive.js")
    open(dp, "w", encoding="utf-8").write(DRIVER)
    gz = os.path.join(tree, "doc.json.gz")
    with gzip.open(gz, "wt") as fh:
        json.dump(doc, fh)
    r = subprocess.run(["node", dp, PAGE, gz], cwd=tree, timeout=600,
                       capture_output=True, text=True)
    assert r.returncode == 0, "node driver failed: %s" % (r.stderr or "")[-500:]
    return json.loads(r.stdout)


def text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


section("1. 🔴🔴 THE PANEL IS REACHED — NOT MERELY DEFINED")
# ⛔ `calls()`, NOT `in HTML`. `fbScores` once carried a complete row
#    builder that was defined and never called; the tab rendered no live
#    game while the join worked perfectly (rule 130).
for _fn, _least in (("fbDossierLoad", 1), ("fbDossierBy", 1),
                    ("fbDossierHtml", 1), ("fbDosSection", 1),
                    ("fbDosFacts", 1), ("fbWireDossierRows", 1)):
    ck(calls(_fn, PAGE) >= _least,
       "   `%s` is CALLED (%d call site(s))" % (_fn, calls(_fn, PAGE)),
       "⛔ a renderer nobody calls looks exactly like the one that draws "
       "the page. THAT is how eight signals sat on disk unseen")
_odds = js_block("fbOddsTable", PAGE)
ck('class="dosrow"' in _odds and "data-bid=" in _odds,
   "🔴 the board row itself is the thing that opens (`tr.dosrow`)",
   "⛔ Sam asked for a game row that expands, the same shape as the "
   "`fbdd-<date>` rows. A panel with no handle is a panel nobody opens")
ck("fbdos-${g.id}" in _odds,
   "   ...and its detail row is keyed on the BOARD'S OWN id",
   "⛔ never the team names and never the kickoff")
ck("fbWireDossierRows" in js_block("fbOdds", PAGE),
   "   ...and `fbOdds` wires it AFTER drawing the rows",
   "🔴 `#fbview` is rebuilt from scratch by every football renderer, so "
   "a listener bound before the write is bound to a detached row — "
   "rule 197")

section("2. ⛔ THE JOIN IS ONE EXACT KEY, AND NOTHING IS INFERRED")
_by = js_block("fbDossierBy", PAGE)
for _forbidden, _why in (
        ("away_name", "a team-name key. CLAUDE.md: two legs are in "
                      "different games only if the GAME ID differs — a "
                      "live MLB card shipped four impossible parlays off "
                      "a name check, including its top recommendation"),
        ("home_name", "the same, for the other side"),
        ("commence", "a kickoff-time key. That is `boardFor()`'s "
                     "nearest-first-pitch problem, and re-solving it in "
                     "a second language is how the wrong-game bug put "
                     "six games' live odds on the next day's cards")):
    ck(_forbidden not in _by,
       "   the index does not key on `%s`" % _forbidden,
       "🔴 found %s" % _why)
ck("board_id" in _by,
   "🔴 ...it keys on `board_id`, which the BUILDER puts on the frame",
   "⛔ measured 2026-09-17: 0 of 32 dossier `game_id`s appear anywhere "
   "in `board.json` — they are different namespaces, so a page given "
   "only `game_id` cannot join at all")

section("3. 🔴🔴 IT RENDERS THE REAL ARTIFACT, BOTH LEAGUES")
_seen = []
for _lg in ("nfl", "ncaaf"):
    _tree, _doc, _log = build(_lg)
    ck(_doc is not None,
       "⚠️ %s: the builder produced a dossier to render" % _lg,
       "⛔ every check below would pass over nothing (rule 67). %s"
       % _log[-300:])
    if _doc is None:
        shutil.rmtree(_tree, ignore_errors=True)
        continue
    _R = drive(_doc, _tree)
    _rows = _R["rows"]
    ck(len(_rows) >= 10,
       "   %s: %d game(s) rendered through the shipped panel code"
       % (_lg, len(_rows)),
       "⛔ rule 67: a sweep over one game proves nothing about a board")
    ck(_R["n_indexed"] == len(_rows) and all(r["matched"] for r in _rows),
       "🔴 %s: EVERY game joins on `board_id` (%d of %d)"
       % (_lg, _R["n_indexed"], len(_rows)),
       "⛔ a game with no panel is a gap; a game shown ANOTHER game's "
       "panel is misinformation. Unmatched: %s"
       % [r["board_id"] for r in _rows if not r["matched"]][:4])
    ck("No signals stored" in _R["miss_html"],
       "   %s: ...and a board id no game has matches NOTHING" % _lg,
       "🔴 the fallback must be an honest empty state, never a "
       "neighbouring game. Got: %s" % text(_R["miss_html"])[:120])
    # ── EVERY SECTION IS ON THE PAGE, AVAILABLE OR NOT ────────────────
    _names = [s["name"] for s in _doc["dossiers"][0]["sections"]]
    # ⚠️ The artifact's own declared count; files built before signal 9 (9th
    #    section, 2026-09-24) declared nothing and carry eight.
    ck(len(_names) == _doc.get("sections_declared", 8) and len(_names) >= 8,
       "   %s: the artifact carries every section it declares (%d)" % (_lg, len(_names)),
       "⛔ rule 67 again — eight is the premise of every check below. "
       "Got %s" % _names)
    _missing = [(r["board_id"], n) for r in _rows for n in _names
                if n not in r["html"]]
    ck(not _missing,
       "🔴🔴 %s: ALL EIGHT SECTIONS APPEAR FOR EVERY GAME" % _lg,
       "⛔ HIDING A SECTION THAT CANNOT ANSWER IS THE WHOLE FAILURE THIS "
       "ARTIFACT EXISTS AGAINST — it would show a board where every game "
       "looks fully analysed. Missing: %s" % _missing[:4])
    _gaps = sum(1 for r in _rows for _ in re.findall(r'dossec gap', r["html"]))
    _dgaps = sum(1 for x in _doc["dossiers"] for s in x["sections"]
                 if s["state"] != "OK")
    ck(_dgaps >= 1 and _gaps == _dgaps,
       "   %s: every section that cannot answer is DRAWN (%d of %d)"
       % (_lg, _gaps, _dgaps),
       "⛔ the refusals are the honesty. Artifact says %d, page drew %d"
       % (_dgaps, _gaps))
    # ══════════════════════════════════════════════════════════════════
    # 🔴🔴 AND A SECTION THAT CAN ANSWER MUST SHOW ONE OF THE BUILDER'S
    # OWN VALUES, NOT ONLY ITS SENTENCE. `[2026-09-17 — the first draft
    # of the panel printed the `why` and nothing else, so "This season"
    # and "Versus position" read OK with a heading and a paragraph.]`
    # ⛔ That is the Task 27 disease one layer out: a section that knows
    # something and displays none of it looks exactly like one that
    # knows nothing, and the whole point of the eight is that a reader
    # can tell those apart.
    # ⚠️ THE EXPECTATION IS DERIVED FROM THE ARTIFACT, never a list of
    # section numbers. A section is owed a value only if the artifact
    # actually carries one for it — so this cannot fire on a section
    # that legitimately has nothing but its sentence, which is the other
    # failure CLAUDE.md names.
    # ══════════════════════════════════════════════════════════════════
    _META = {"n", "name", "state", "basis"}
    _PROSE = {"why", "remedy", "scale", "verdict", "open_gap", "known_gap",
              "coverage_note", "weather_note", "closing_note", "note"}
    _mute = []
    for _r, _x in zip(_rows, _doc["dossiers"]):
        _frags = _r["html"].split('<div class="dossec')
        for _s in _x["sections"]:
            if _s["state"] != "OK":
                continue
            _pay = {k: v for k, v in _s.items()
                    if k not in _META and k not in _PROSE
                    and v not in (None, {}, [], "")}
            if not _pay:
                continue
            _f = [g for g in _frags if ">%s<" % _s["name"] in g]
            if not _f or "<li>" not in _f[0]:
                _mute.append((_r["board_id"], _s["name"], sorted(_pay)))
    ck(not _mute,
       "🔴 %s: every section that CAN answer shows a stored value, not "
       "just a sentence" % _lg,
       "⛔ a heading and a paragraph over data the artifact is holding is "
       "a section that looks empty while knowing something. Silent: %s"
       % _mute[:4])
    _reasons = [(r["board_id"], s["name"]) for r, x
                in zip(_rows, _doc["dossiers"])
                for s in x["sections"]
                if s["state"] != "OK" and s.get("why")
                and s["why"] not in r["html"]]
    ck(not _reasons,
       "   %s: ...carrying the BUILDER'S OWN reason, verbatim" % _lg,
       "⛔ a second sentence written in JavaScript is a second copy of "
       "the reasoning (rule 132). Reworded: %s" % _reasons[:3])
    _seen.append((_lg, len(_rows), _dgaps,
                  sum(1 for r in _rows if r["unresolved_side"])))
    # ── THE REGISTER ─────────────────────────────────────────────────
    _all = text(" ".join(r["html"] for r in _rows))
    _hits = sorted({j for j in JARGON if j in _all})
    ck(not _hits,
       "🔴 %s: ZERO jargon in the rendered panel (%d term(s) checked)"
       % (_lg, len(JARGON)),
       "⛔ THE LIST IS `verify_card.py`'s OWN and the football panel does "
       "not get an easier one. Found %s" % _hits)
    _ops = sorted(set(OPERATOR.findall(_all)))
    ck(not _ops,
       "   %s: ...and nothing operator-facing either" % _lg,
       "⛔ no filename, path, backticked code or collector mode name. A "
       "reader does not run the jobs. Found %s" % _ops[:6])
    ck("MODEL" not in _all and not re.search(r"\d{1,3}\s*%\s*(conf|chance)",
                                             _all, re.I),
       "   %s: ...and no Gizmo's confidence anywhere on it (rule 55)"
       % _lg,
       "⛔ every number in this artifact is the market's or a record; "
       "none is a model output, and none may sit beside one")
    shutil.rmtree(_tree, ignore_errors=True)
note("   league / games rendered / sections that could not answer / "
     "partial games: %s" % (_seen,))

section("4. 🔴🔴 A PARTIAL GAME LOOKS PARTIAL — DRIVEN, NOT HOPED FOR")
# ══════════════════════════════════════════════════════════════════════
# ⛔ SYNTHETIC ON PURPOSE, AND UNCONDITIONALLY. 16 of the 90 college
# games on today's board carry an opponent the season files do not cover
# — but that is a fact about THE BOARD: measured across 36 stored college
# boards it runs 0 to 41, and 2 of them carried ZERO. Asserting the real
# board holds one would redden this suite on a mid-Saturday board that is
# perfectly good, which is the other failure CLAUDE.md names.
# ✅ So the case is INJECTED and the check is true every day.
# ══════════════════════════════════════════════════════════════════════
_tree4, _doc4, _log4 = build("nfl")
ck(_doc4 is not None, "⚠️ there is a document to inject into", _log4[-200:])
if _doc4 is not None:
    _g4 = _doc4["dossiers"][0]
    _g4["unresolved_side"] = "Slippery Rock Aardvarks"
    _g4["away_name"] = "Slippery Rock Aardvarks"
    _g4["away"] = None
    # ⛔ AND A SECOND FRAME WITH NO `board_id` AT ALL, to prove the index
    #    SKIPS it rather than reaching for another key.
    _g5 = dict(_doc4["dossiers"][1])
    _g5.pop("board_id", None)
    _doc4["dossiers"] = [_g4, _g5]
    _R4 = drive(_doc4, _tree4)
    _h4 = _R4["rows"][0]["html"]
    ck("Slippery Rock Aardvarks" in _h4,
       "🔴🔴 THE SIDE WITH NO SEASON RECORD IS NAMED ON THE PANEL",
       "⛔ NEVER RENDER A BLANK WHERE A TEAM NAME BELONGS. The board has "
       "the name and the builder carries it through — publishing nothing "
       "throws away the one thing we did know. Got: %s" % text(_h4)[:160])
    ck("dospart" in _h4,
       "   ...and the game is MARKED partial, not quietly short",
       "⛔ 16 of 90 college games are like this. A panel that looks "
       "complete on one of them is the failure the eight exist against")
    ck(" at </div>" not in _h4 and " at <span" not in _h4,
       "   ⛔ ...and the header has no empty team slot",
       "🔴 `X at ` with nothing after it is exactly the `Oregon vs None` "
       "shape, moved to the browser. Got: %s" % text(_h4)[:120])
    ck(_R4["n_indexed"] == 1 and not _R4["rows"][1]["matched"],
       "🔴 a frame with NO `board_id` is SKIPPED, not matched some other "
       "way (%d indexed of 2)" % _R4["n_indexed"],
       "⛔ this is the check that stops a name or time fallback creeping "
       "back in. Matched: %s" % [r["matched"] for r in _R4["rows"]])
    shutil.rmtree(_tree4, ignore_errors=True)
section("5. 🔴🔴 THE BOOK COUNT SAYS WHAT IT COUNTS")
# ══════════════════════════════════════════════════════════════════════
# 🔴 "Books priced 0" SAT DIRECTLY BESIDE A TOTAL OF 67.5 THAT A NAMED
# BOOK WAS SHOWING. `[found in review, 2026-09-17]` `n_books` is
# `len(vigs)` in `collect.py` and `vigs` comes from the MONEYLINE de-vig,
# so it counts books showing a two-sided moneyline — not books pricing
# the game. MEASURED on the live college board: 15 of 90 games have an
# empty `best_ml` AND `n_books == 0`, the same 15, and all 15 still carry
# a total and a spread.
#
# ➡️ THE CLASS: A FIELD NAME NARROWER THAN IT READS IS HARMLESS UNTIL
# SOMETHING DISPLAYS IT. `n_books` had been correct and privately
# understood for weeks; the defect was created by putting it on the page
# beside the thing it does not count. ⚠️ AND I GUARDED THE INSTANCE, NOT
# THE CLASS, DELIBERATELY: "re-read what a field actually counts when it
# first reaches the surface" is a thing a person does, not a question a
# check can ask. What IS checkable is that THIS count names its subject
# and never reads as "nothing is priced" — so that is what is checked,
# on the real board and on an injected row.
#
# ⛔ THE ZERO IS NOT SUPPRESSED, and the check below insists on that: a
# game we hold no moneyline for is a real fact about a mismatch this
# size, and hiding it would make those 15 look like the other 75.
# ⚠️ "we hold none", not "no book will quote one" — CLAUDE.md: an absence
# in an API response is evidence about the API, never about the
# sportsbook, and this project has got that backwards five times.
# ══════════════════════════════════════════════════════════════════════
# ⛔ THE CONTRADICTION SHAPE, not the old literal. A label that reads as
#    "nothing is priced" beside a price is the defect whatever word it
#    reaches for, so the pattern covers priced/prices/pricing.
_PRICED0 = re.compile(r"pric(?:ed|es|ing)[^0-9<]{0,40}(?:<[^>]+>\s*)?0\b",
                      re.I)


def market_of(html):
    """The market section's own fragment, or '' if it is not there."""
    for g in html.split('<div class="dossec'):
        if ">Market<" in g:
            return g
    return ""


_tree5, _doc5, _log5 = build("ncaaf")
ck(_doc5 is not None, "⚠️ there is a college document to render", _log5[-200:])
if _doc5 is not None:
    # ── 1. THE REAL BOARD. ⛔ It asserts an ABSENCE, so it cannot
    #    false-alarm on a board that happens to carry no zero — the
    #    board-dependent floor is the mistake #51 just fixed. The
    #    NON-VACUOUS drive is the injected row below.
    _R5 = drive(_doc5, _tree5)
    _mkts = [(r["board_id"], market_of(r["html"])) for r in _R5["rows"]]
    ck(all(m for _b, m in _mkts),
       "⚠️ every game rendered a market section (%d)" % len(_mkts),
       "⛔ rule 67: the sweep below would pass over nothing. Missing: %s"
       % [b for b, m in _mkts if not m][:4])
    _contra = [b for b, m in _mkts if _PRICED0.search(m)]
    ck(not _contra,
       "🔴 no game on the real board reads as 'nothing is priced' beside "
       "a price",
       "⛔ THIS IS THE DEFECT: 'Books priced 0' next to a total of 67.5 "
       "that Hard Rock was showing. A reader who sees 0 beside a number "
       "they can bet stops trusting the page. Games: %s" % _contra[:4])
    _zeros = [(b, m) for b, m in _mkts if "moneyline</b> <b>0<" in
              m.replace("moneyline", "moneyline</b>")]
    _nolabel = [b for b, m in _mkts if "Books" in m
                and "moneyline" not in m]
    ck(not _nolabel,
       "   ⛔ ...and every book count on it NAMES what it counts",
       "🔴 the count is of books showing a two-sided MONEYLINE, and a "
       "bare 'Books' is the reading that was wrong. Games: %s"
       % _nolabel[:4])
    note("   %d of %d real college games carry a zero book count — "
         "reported, NOT asserted (it is a fact about today's board)."
         % (len([1 for x in _doc5["dossiers"]
                 for s_ in x["sections"]
                 if s_.get("n") == 1
                 and (s_.get("live") or {}).get("n_books") == 0]),
            len(_doc5["dossiers"])))

    # ── 2. AND DRIVEN ON AN INJECTED ROW, unconditionally. ⛔ The real
    #    board carried 15 today and could carry none tomorrow; the case
    #    this file exists for must be driven either way.
    _g5 = _doc5["dossiers"][0]
    _m5 = [x for x in _g5["sections"] if x["n"] == 1][0]
    _m5.setdefault("live", {})
    _m5["live"]["n_books"] = 0
    _m5["live"]["total"] = 67.5
    _m5["live"]["run_line"] = -56.5
    _g6 = json.loads(json.dumps(_doc5["dossiers"][0]))
    _g6["board_id"] = "second-frame-for-the-positive-control"
    [x for x in _g6["sections"] if x["n"] == 1][0]["live"]["n_books"] = 4
    _doc5["dossiers"] = [_g5, _g6]
    _R6 = drive(_doc5, _tree5)
    _z = market_of(_R6["rows"][0]["html"])
    _p = market_of(_R6["rows"][1]["html"])
    ck(bool(_z) and bool(_p),
       "⚠️ both injected rows rendered a market section",
       "⛔ rule 67 again — the checks below would pass over empty strings")
    ck(not _PRICED0.search(_z),
       "🔴🔴 A ZERO COUNT BESIDE A LIVE TOTAL DOES NOT SAY 'PRICED'",
       "⛔ THE WHOLE FINDING. Got: %s" % text(_z)[:200])
    ck("67.5" in _z,
       "   ⛔ ...and the total is still shown",
       "🔴 the price is real and it is the one thing we know for sure. "
       "Got: %s" % text(_z)[:200])
    ck("moneyline <b>0</b>" in _z,
       "   ⛔ ...and the ZERO IS NOT SUPPRESSED, it is LABELLED",
       "🔴 hiding it would make these games look like the rest of the "
       "board. Got: %s" % text(_z)[:200])
    ck("moneyline" in _z,
       "🔴 ...and the label NAMES the moneyline, which is what it counts",
       "⛔ `n_books` is `len(vigs)` off the moneyline de-vig. A bare "
       "'Books' is the reading that put 0 beside a price. Got: %s"
       % text(_z)[:200])
    # ⚠️ ON THE NORMALISED TEXT, not the raw HTML. The sentence is a
    #    template literal, so it carries newlines and indentation that a
    #    browser collapses and a substring match does not — a check that
    #    fails on how the source is WRAPPED is a check that reddens on
    #    correct code.
    _ztxt = text(_z)
    ck("moneyline only" in _ztxt and "real prices" in _ztxt,
       "   ✅ ...and the zero is explained in words a reader can use",
       "⛔ the count alone still invites the wrong reading; the sentence "
       "says what is missing and what is real. Got: %s" % _ztxt[:240])
    ck("moneyline" in _p and not _PRICED0.search(_p),
       "   ⚠️ ...and a NON-zero count is labelled the same way",
       "🔴 one label, both cases — a special case for zero would be two "
       "descriptions of one field. Got: %s" % text(_p)[:200])
    ck("real prices" not in text(_p),
       "   ⛔ ...without the zero explanation attached to it",
       "🔴 a sentence about a missing moneyline under a count of 4 is "
       "noise, and noise is what the clean-look rule is about. Got: %s"
       % text(_p)[:200])
    shutil.rmtree(_tree5, ignore_errors=True)
note("⛔ WHAT THIS FILE DOES NOT CLAIM: that the panel is well designed, "
     "or that a reader finds it useful. It claims the eight signals "
     "REACH A READER, every section is shown whether or not it could "
     "answer, the join is exact, and every word on it is the builder's "
     "own and passes the MLB card's jargon bar. ➡️ Whether it reads well "
     "is Sam's call, and it is the one thing no test can make.")
