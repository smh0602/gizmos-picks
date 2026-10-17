#!/usr/bin/env python3
"""
THE TRACK RECORD TAB, EVERY LEAGUE: THREE HIT RATES, AND A DAY YOU CAN OPEN.
~~THE FOOTBALL RECORD TAB: MLB'S BANDS, AND A DAY YOU CAN OPEN.~~

`[Sam, 2026-10-17]` *"in track record we should have a game lines tracker so
we an track how the model does for game lines. lose the was the record right?
section of it. i only want the board hit % to be shown(this is the 25 player
props and all the game lines hit %) and i want both hit % to be shown ... all
in all wed have 3 different hit rate % shows at the top of the track record
tab, board(all picks), player props(only player props), and game line(only
game lines)"*. Asked about MLB he chose "Remove both" ("Does the confidence
number mean anything?" and "Is v5.0 still the best version?") and, below the
three, "Just the by-date lists". So this file now requires, in every league:
the three boxes (Board, Player props, Game lines) with the GRADER'S numbers,
the props by day and the game lines by day, each graded day openable — and
the bands, their heading, their legend, the method tables, the market table,
the winners' line and the refit panel ABSENT. ⚠️ The DATA behind the bands
(record.json `calibration`, `calibration_by_method`; mlb-refit.json) is still
built; only the page stopped drawing it.

🔴 THE JAVASCRIPT IS EXECUTED, NOT READ. `[jsblock.py's own lesson, and
rule 197]` `fbScores` once carried a complete `<tr>` builder that was
defined and never called; the tab rendered nothing and the source looked
perfect. So every check below RUNS the page's own function under node and
asserts on what came back.

⛔ ~~AND THE TRAP THIS FILE EXISTS FOR IS ONE FILE OVER. `card_fb.py` was
bitten on 2026-09-16 by reading MLB's `predicted` from a football record
that names the field `stated` ... `bandRow` is MLB's and takes `said`.~~
`[2026-10-17]` bandRow, fbCalBlock and fbCalMethods are deleted. The trap
that remains is the SAME CLASS: the page reading a field under a name the
grader does not write. So the three boxes are driven on a record.json that
the REAL grader (`record_fb.py`) wrote in a planted tree, never on a record
typed to match what the page expects.
"""
import gzip
import hashlib
import json
import os
import re as _re
import shutil as _sh
import subprocess
import sys
import tempfile

from tcheck import ck, eq, note, section

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsblock import js_block, calls  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(ROOT, "index.html")


# ══════════════════════════════════════════════════════════════════════
# `[Sam, 2026-10-17]` ~~the football bands must render through bandRow, not a
#   table~~ (`const band = c => bandRow({`): the bands left the page. Re-aimed at
#   the new requirement: they are ABSENT, so the mutation draws them again.
# @vacuity [Sam, 2026-10-17] the football Track Record draws NO calibration band
#   file: index.html
#   find: trBox('Game lines', R && R.game_lines)}</div>`;
#   with: trBox('Game lines', R && R.game_lines)}</div>` + ((R && R.calibration) || []).map(c => `<div class="band">${c.bucket}</div>`).join('');
#
# `[Sam, 2026-10-17]` ~~the claimed figure is `stated`; MLB's `predicted` finds
#   nothing~~ (`said: c.stated, ...`): no band claims anything any more. Re-aimed
#   at "lose the was the record right? section".
# @vacuity [Sam, 2026-10-17] the football Track Record has no "Was the record right?" heading
#   file: index.html
#   find: v.innerHTML = fbShell(`<h2>${LG_NAME[LEAGUE]} record</h2>
#   with: v.innerHTML = fbShell(`<h2>${LG_NAME[LEAGUE]} record</h2><h3>Was the record right?</h3>
#
# `[Sam, 2026-10-17]` ~~an empty bucket is "No sample", never a bar sitting at
#   zero~~ (`hit: c.n ? c.pct : null }`): the same honesty, on the new boxes.
# @vacuity [Sam, 2026-10-17] an empty hit rate reads em-dash, never a box at 0%
#   file: index.html
#   find: <div class="v">${t && t.n ? t.pct.toFixed(1) + '%' : '&mdash;'}</div>
#   with: <div class="v">${t ? (t.pct || 0).toFixed(1) + '%' : '&mdash;'}</div>
#
# @vacuity a graded day row must carry data-date, or nothing can open it
#   file: index.html
#   find: <tr class="${open ? 'dayrow' : ''}"${open ? ` data-date="${d.date}"` : ''}${
#   with: <tr class="${open ? 'dayrow' : ''}"${open ? `` : ''}${
#
# @vacuity [Sam, 2026-10-17] a graded game-lines day row must carry data-gldate, or nothing can open it
#   file: index.html
#   find: <tr class="${open ? 'dayrow' : ''}"${open ? ` data-gldate="${d.date}"` : ''}${
#   with: <tr class="${open ? 'dayrow' : ''}"${open ? `` : ''}${
#
# @vacuity the detail cache is keyed BY LEAGUE, never one shared slot
#   file: index.html
#   find: const key = lg;
#   with: const key = 'one';
#
# [Sam, 2026-10-01] ~~degrades to a note~~: the catch now writes ONE plain
#   line. ⚠️ That line is byte-identical to renderRecord's, so the find is the
#   comment that opens fbWireDayRows' catch, which occurs once on the page.
# @vacuity a missing detail file degrades to ONE plain line, never an exception
#   file: index.html
#   find: /* ⛔ DEGRADES TO ONE PLAIN LINE, NEVER A BROKEN TAB. Before the
#   with: throw e; /* ⛔ DEGRADES TO ONE PLAIN LINE, NEVER A BROKEN TAB. Before the
#
# @vacuity [Sam, 2026-10-01] the missing-detail degrade draws NO note box naming the file
#   file: index.html
#   find: /* ⛔ DEGRADES TO ONE PLAIN LINE, NEVER A BROKEN TAB. Before the
#   with: cell.innerHTML = `<div class="note"><b>No detail file yet.</b> The grader writes <code>${(rec && rec.detail_file) || `${LG_DATA[lg]}/latest/record-detail.json.gz`}</code> on its next run.</div>`; return; /* ⛔ DEGRADES TO ONE PLAIN LINE, NEVER A BROKEN TAB. Before the
#
# @vacuity [Sam, 2026-10-01] MLB's dayDetailHtml is pinned WITHOUT its note box
#   file: index.html
#   find: if (!rows || !rows.length) return '<div class="msg">No picks stored for that card.</div>';
#   with: if (!rows || !rows.length) return '<div class="msg">No picks stored for that card.</div>'; if (rows.some(r => r.void)) return '<div class="note"><b>Actual</b> is what the player really did, read off the stored box score.</div>';
#
# @vacuity [Sam, 2026-10-01] MLB's renderRecord is pinned WITHOUT its MODEL tag
#   file: index.html
#   find: <h2>Automatic card</h2>
#   with: <h2>Automatic card <span class="kind k-model">Model</span></h2>
#
# @vacuity [Sam, 2026-10-01] no tab renders the calibration_warning pop-up
#   file: index.html
#   find: head.innerHTML = `<h2>Gizmo's Picks &mdash; ${CARD_DATE}</h2>`;
#   with: head.innerHTML = `<h2>Gizmo's Picks &mdash; ${CARD_DATE}</h2><div class="note"><b>Read the confidence number honestly.</b> ${P.calibration_warning}</div>`;
#
# `[Sam, 2026-10-17]` ~~the football bands must not speak in MLB's first person~~
#   (`}, 'the record claimed');`): nothing on the tab speaks of a claim now.
# @vacuity [Sam, 2026-10-17] no football Track Record speaks of a claim ("the record claimed")
#   file: index.html
#   find: const dayRows = fbDayRows(days, R);
#   with: const dayRows = fbDayRows(days, R) + ((R && R.calibration) || []).map(c => `<tr><td><div class="said" title="the record claimed ${c.stated}%"></div></td></tr>`).join('');
#
# `[Sam, 2026-10-17]` ~~MLB's RENDERED bands must be byte-identical to the frozen
#   copy~~ (`gap.toFixed(1)`, inside the deleted bandRow): MLB's panel is gone.
# @vacuity [Sam, 2026-10-17] MLB's Track Record draws no "Does the confidence number mean anything?" panel
#   file: index.html
#   find: <p><span class="rec">built ${R.built_at}</span></p>
#   with: <p><span class="rec">built ${R.built_at}</span></p><h2>Does the confidence number mean anything?</h2>${(R.calibration || []).map(c => `<div class="band">${c.bucket}</div>`).join('')}
#
# `[Sam, 2026-10-17]` ~~the tab must draw every method's bands, not `calibration`
#   alone~~ (`const calBlock = fbCalMethods(R);`): no method's bands are drawn.
# @vacuity [Sam, 2026-10-17] MLB's Track Record reads no mlb-refit.json ("Is v5.0 still the best version?")
#   file: index.html
#   find: const R = RECORD, G = R.game_lines || {};
#   with: const R = RECORD, G = R.game_lines || {}; let REFIT = null; try { REFIT = await jget('data/latest/mlb-refit.json'); } catch(e){ REFIT = null; }
#
# `[Sam, 2026-10-17]` ~~a method other than the current one must still be drawn~~
#   (`const order = [cur, ...]`): below the three boxes, the by-date lists only.
# @vacuity [Sam, 2026-10-17] the winners' line is gone from MLB's Track Record
#   file: index.html
#   find: const hero = `<div class="tr-hero">${trBox('Board', R.board)}${trBox('Player props', R.overall)}${
#   with: const W = await winnersLoad('mlb'); const hero = winnersRecordLine(W) + `<div class="tr-hero">${trBox('Board', R.board)}${trBox('Player props', R.overall)}${
#
# `[Sam, 2026-10-17]` ~~each method's table carries its own label~~ (the
#   `FB_METHOD_BEFORE` label line): the method tables are gone.
# @vacuity [Sam, 2026-10-17] the winners' line is gone from the football Track Record
#   file: index.html
#   find: const R = await fbRecordLoad();
#   with: const R = await fbRecordLoad(); const W = await winnersLoad(LEAGUE);
#
# `[Sam, 2026-10-17]` ~~a method with no graded picks says so instead of drawing
#   nothing~~ (fbCalBlock's `fb-cal-empty`): the same rule on the game-lines detail.
# @vacuity a game-lines day with no stored rows says so, never an empty box
#   file: index.html
#   find: if (!rows || !rows.length) return '<div class="msg">No game lines stored for that day.</div>';
#   with: if (!rows || !rows.length) return '';
#
# `[Sam, 2026-10-17]` ~~the default voice is preserved for callers that pass none~~
#   (`${saidAs || 'we said'}`, inside the deleted bandRow): the click wiring instead.
# @vacuity [Sam, 2026-10-17] a football game-lines day opens ITS game lines, not the props
#   file: index.html
#   find: cell.innerHTML = gl ? lineDetailHtml(((D || {}).game_lines || {})[date])
#   with: cell.innerHTML = gl ? fbDayDetailHtml(((D || {}).days || {})[date])
#
# @vacuity [Sam, 2026-10-17] MLB's game-lines day opens its OWN box (gl-<date>), not a props box
#   file: index.html
#   find: const box = document.querySelector((gl ? '#gl-' : '#dd-') + date);
#   with: const box = document.querySelector('#dd-' + date);
#
# @vacuity [Sam, 2026-10-17] bandRow is gone from the page, not left defined for nothing to call
#   file: index.html
#   find: let RECDETAIL = null;
#   with: let RECDETAIL = null; function bandRow(b, saidAs){ return `<div class="band" title="${saidAs || 'we said'} ${b.said}%"></div>`; }
#
# @vacuity an anytime TD row reads "Yes ... Anytime TD", never "Under null"
#   file: index.html
#   find: <td>${r.side === 'over' ? 'Over' : r.side === 'under' ? 'Under' : 'Yes'}${
#   with: <td>${r.side === 'over' ? 'Over' : 'Under'}${
#
# @vacuity [Sam, 2026-10-17] the Board box is the props AND the game lines (the grader's `board`)
#   file: record_fb.py
#   find: "board": tally(A + _gl_graded),
#   with: "board": tally(A),
#
# @vacuity the grader WRITES each league's own detail_file (planted tree, not the stored record)
#   file: record_fb.py
#   find: "detail_file": f"{LATEST}/record-detail.json.gz",
#   with: "detail_file": None,
# ══════════════════════════════════════════════════════════════════════


_IDXSRC = open(IDX, encoding="utf-8").read()


def _decl(rx, what):
    """A page-level declaration, pulled out of the page by its own line."""
    m = _re.search(rx, _IDXSRC, _re.M)
    assert m, "index.html no longer declares " + what
    return m.group(0)


def node(body, extra=""):
    """Run `body` under node with the page's real functions in scope.

    ⛔ THE IMPLEMENTATION IS PULLED OUT OF `index.html`, NEVER RETYPED. A
    copy of the function under test is a test of the copy.
    `[Sam, 2026-10-17]` ~~bandRow, fbCalBlock, fbCalMethods~~ (deleted) are no
    longer pulled; the Track Record's own renderers in BOTH leagues are.
    """
    src = "\n".join(js_block(n, IDX) for n in
                    ("trBox", "lineDetailHtml", "fbDayRows", "fbLineDayRows",
                     "fbDayDetailHtml", "fbDetailLoad", "fbWireDayRows", "fbRecord",
                     "freshness", "renderRecord", "loadRecordDetail", "dayDetailHtml"))
    # ⚠️ `const FBDETAIL = {}` (and RECDETAIL, RECORD, LG_NAME, sgn) LIVE OUTSIDE
    #    ANY FUNCTION, so js_block cannot reach them — and retyping them here
    #    would make the cache test a test of my copy. Pulled out of the page by
    #    their own declarations. ~~FB_METHOD_BEFORE~~ is deleted `[2026-10-17]`.
    decls = [_decl(r"^const FBDETAIL = \{\};", "FBDETAIL"),
             _decl(r"^let RECDETAIL = null;", "RECDETAIL"),
             _decl(r"^let RECORD = null;", "RECORD"),
             _decl(r"^const LG_NAME\s*=\s*\{[^}\n]*\};", "LG_NAME"),
             _decl(r"^const sgn = [^\n]*$", "sgn")]
    prog = ("const LG_DATA = { mlb:'data', nfl:'data/nfl', ncaaf:'data/ncaaf' };\n"
            "let LEAGUE = 'nfl';\n"
            + "\n".join(decls) + "\n"
            + extra + "\n" + src + "\n"
            + "(async () => { " + body + " })().catch(e => {"
            "  console.log('__ERR__' + (e && e.message)); process.exit(3); });")
    d = tempfile.mkdtemp(prefix="fbrec-")
    f = os.path.join(d, "probe.js")
    open(f, "w", encoding="utf-8").write(prog)
    try:
        p = subprocess.run(["node", f], capture_output=True, text=True, timeout=120,
                           cwd=ROOT, encoding="utf-8")
    finally:
        _sh.rmtree(d, ignore_errors=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def out(body, extra=""):
    """-> the JSON the probe printed, or a dict describing the failure."""
    rc, o = node(body, extra)
    for line in o.splitlines():
        line = line.strip()
        if line.startswith("{") or line.startswith("["):
            try:
                return json.loads(line)
            except ValueError:
                pass
    return {"__rc": rc, "__out": o[-400:]}


# 🔴 THE SMALLEST DOM THE TRACK RECORD TOUCHES, BUILT FROM WHAT THE PAGE DREW.
# ⚠️ The rows wired are the rows the page RENDERED: `querySelectorAll` reads
#    every `<tr class="dayrow" ...>` out of the view's own HTML at the moment
#    the page asks, with its `data-date` / `data-gldate`; `querySelector('#id')`
#    returns a box only if the HTML holds that id. A row the page did not draw
#    cannot be clicked, and a box it did not draw cannot be opened.
_DOMSTUB = r"""
const V = {innerHTML: ''};
const $ = s => V;
const BOXES = {};
const CLICKS = [];
const document = {
  querySelectorAll: sel => [...V.innerHTML.matchAll(/<tr class="dayrow"([^>]*)>/g)].map(m => {
    const a = m[1], ds = {};
    const d = a.match(/ data-date="([^"]*)"/), g = a.match(/ data-gldate="([^"]*)"/);
    if (d) ds.date = d[1];
    if (g) ds.gldate = g[1];
    return {dataset: ds, classList: {add(){}, remove(){}},
            addEventListener: (ev, fn) => CLICKS.push({ds, fn})};
  }),
  querySelector: sel => {
    const id = String(sel).replace(/^#/, '');
    if (!V.innerHTML.includes(`id="${id}"`)) return null;
    if (!BOXES[id]) { const cell = {dataset: {}, innerHTML: ''};
                      BOXES[id] = {hidden: true, cell, querySelector: () => cell}; }
    return BOXES[id];
  }};
let WINNERS = 0;
async function winnersLoad(){ WINNERS++; return {}; }
function winnersRecordLine(){ WINNERS++; return '<p data-winners>the model picked the winner</p>'; }
"""
_SHOW = ("const html = V.innerHTML;"
         "for (const c of CLICKS) await c.fn();"
         "const cells = Object.fromEntries(Object.entries(BOXES).map(([k, b]) => [k, b.cell.innerHTML]));"
         "console.log(JSON.stringify({html, cells, winners: WINNERS,"
         " fetched: (typeof FETCHED === 'undefined') ? [] : FETCHED,"
         " rows: CLICKS.map(c => c.ds)}));")


def fb_render(rec, detail=None, lg="nfl"):
    """fbRecord, the page's own, on `rec`; then every day row it drew is clicked."""
    extra = (_DOMSTUB
             + "const fbShell = x => x; function fbWire(){}\n"
             + "const REC = %s; const DETAIL = %s; const FETCHED = [];\n" % (
                 json.dumps(rec), json.dumps(detail))
             + "async function fbRecordLoad(){ return REC; }\n"
             + "async function jgetGz(p){ FETCHED.push(p);"
               " if (DETAIL == null) throw new Error(p + ' -> 404'); return DETAIL; }\n")
    return out("LEAGUE = %s; await fbRecord();" % json.dumps(lg) + _SHOW, extra)


def mlb_render(rec, detail=None, refit=None):
    """MLB's renderRecord, the page's own, on `rec`; its timer fired, every row clicked."""
    extra = (_DOMSTUB
             + "const REFIT = %s; const DETAIL = %s; const FETCHED = [];\n" % (
                 json.dumps(refit), json.dumps(detail))
             + "async function jget(p){ FETCHED.push(p);"
               " if (/mlb-refit/.test(p) && REFIT) return REFIT; throw new Error(p + ' -> 404'); }\n"
             + "async function jgetGz(p){ FETCHED.push(p);"
               " if (DETAIL == null) throw new Error(p + ' -> 404'); return DETAIL; }\n"
             + "const TIMERS = []; const setTimeout = fn => { TIMERS.push(fn); };\n")
    return out("RECORD = %s; await renderRecord(); for (const t of TIMERS) t();" % json.dumps(rec)
               + _SHOW, extra)


def boxes(html):
    """[(key, value, sub)] of every Track Record box the HTML holds, in order."""
    return _re.findall(r'<div class="tr-box"><div class="k">([^<]*)</div>\s*'
                       r'<div class="v">([^<]*)</div>\s*<div class="s">([^<]*)</div></div>',
                       html or "")


REAL = {lg: json.load(open(os.path.join(ROOT, "data", lg, "latest",
                                        "record.json"), encoding="utf-8"))
        for lg in ("nfl", "ncaaf")}


# 🔴 EVERY METHOD'S BANDS, NOT `calibration` ALONE. `[2026-09-24]`
# ⛔ `calibration` is only the CURRENT card method's buckets, and the day
#    the method switched it was EMPTY. `[2026-10-17]` Now used only to say
#    whether a LIVE record holds bands the page must NOT draw.
def all_bands(rec):
    by = rec.get("calibration_by_method")
    if by is None:
        return list(rec.get("calibration") or [])
    return [c for v in by.values() for c in v]


BANDS = {lg: all_bands(REAL[lg]) for lg in REAL}
_IDXCODE = _re.sub(r"(?m)^\s*//.*$", "",
                   _re.sub(r"/\*.*?\*/|<!--.*?-->", "", _IDXSRC, flags=_re.S))

section("0. ⚠️ THE FUNCTIONS EXIST AND ARE ACTUALLY CALLED — AND THE REMOVED ONES ARE GONE")
# 🔴 "DOES IT EXIST" IS THE QUESTION THAT GOT `fbScores` WRONG. The
#    question is who CALLS it.
# `[Sam, 2026-10-17]` ~~fbRecord CALLS fbCalMethods~~: the bands left the page;
#    fbRecord now calls trBox (the three boxes) and fbLineDayRows (the game lines
#    by day), and the click handler opens a game-lines day through lineDetailHtml.
_fbrec = js_block("fbRecord", IDX)
_wire = js_block("fbWireDayRows", IDX)
_mlbrec = js_block("renderRecord", IDX)
for _n in ("trBox", "fbDayRows", "fbLineDayRows", "fbWireDayRows"):
    ck(calls(_n, IDX) >= 1 and (_n + "(") in _fbrec,
       "⛔ fbRecord CALLS %s" % _n,
       "🔴 a renderer defined and never called is the defect jsblock.py "
       "was written for — the source reads perfectly and the tab is "
       "blank. Called %d time(s) anywhere; in fbRecord: %s"
       % (calls(_n, IDX), (_n + "(") in _fbrec))
for _n in ("fbDetailLoad", "fbDayDetailHtml", "lineDetailHtml"):
    ck(calls(_n, IDX) >= 1 and (_n + "(") in _wire,
       "⛔ ...and the click handler calls %s" % _n,
       "a cache nothing reaches is not a cache, and a detail renderer "
       "nothing reaches is a blank box")
for _n in ("trBox", "loadRecordDetail", "dayDetailHtml", "lineDetailHtml"):
    ck((_n + "(") in _mlbrec,
       "⛔ MLB's renderRecord CALLS %s" % _n,
       "the same three boxes and the same game-lines detail, in every league")
# ⛔ `[Sam, 2026-10-17]` GONE, NOT LEFT BEHIND. "lose the was the record right?
#    section"; for MLB "Remove both". A renderer left defined for nothing to call
#    is the jsblock.py defect in reverse: it reads as if the tab still drew it.
#    Asked of the page's CODE (comments stripped: a dated note naming a deleted
#    function is not the function).
for _n in ("bandRow", "fbCalBlock", "fbCalMethods", "FB_METHOD_BEFORE",
           "refitPanel", "fbPct", "fbWL"):
    _hits = [m.group(0) for m in _re.finditer(r"[^\n]{0,30}\b%s\b[^\n]{0,30}" % _n, _IDXCODE)]
    ck(not _hits,
       "⛔ [Sam, 2026-10-17] %s is gone from the page — not defined, not called" % _n,
       "its panel left the Track Record; found %s" % _hits[:2])

# ══════════════════════════════════════════════════════════════════════
# `[Sam, 2026-10-17]` ~~1. THE BANDS RENDER THROUGH bandRow — AND NOT A TABLE~~,
# ~~2. THE CLAIMED FIGURE COMES FROM `stated`, NEVER 0~~, ~~3. THE GEOMETRY HOLDS
# AT FOOTBALL'S RANGE~~ and ~~4. AN EMPTY BUCKET IS 'No sample'~~ asked how the
# bands drew. Sam: "lose the was the record right? section of it" and three hit
# rates instead. So 1 asks for the three boxes off the grader's own file, 2 and 3
# for the bands ABSENT in both leagues (on records that still carry them), and 4
# keeps the old honesty on the new boxes: nothing graded is an em-dash, never 0%.
# ══════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 [Sam, 2026-10-17] THREE HIT RATES, OFF THE FILE THE REAL GRADER WROTE")
# ⛔ NOT A RECORD TYPED TO MATCH THE PAGE. `record_fb.py` itself runs in a planted
#    tree — one card showing three game lines (a moneyline that won, a spread
#    that lost, a total whose game has not finished), the model-picks snapshot
#    that joins its games to the schedule, and the schedule. The ONE redirect is
#    `game_lines_fb.ROOT`: the real schedule reader, pointed at the planted tree
#    (it otherwise reads the repo's own data, which a test may not ask).
#    Then the page's own fbRecord draws the record.json that run wrote.
_PLANT_DAY = "2026-10-11"
_GL_ROWS = [
    {"kind": "fb-line", "league": "nfl", "player": "New York Giants", "market": "moneyline",
     "market_label": "Moneyline", "side": "home", "line": None,
     "game": "New Orleans Saints @ New York Giants", "away": "New Orleans Saints",
     "home": "New York Giants", "commence": "2026-10-11T17:00:00Z", "book": "fanduel",
     "price": -150, "confidence_basis": "MODEL", "confidence": 64},
    {"kind": "fb-line", "league": "nfl", "player": "New Orleans Saints", "market": "spread",
     "market_label": "Spread", "side": "away", "line": 3.5,
     "game": "New Orleans Saints @ New York Giants", "away": "New Orleans Saints",
     "home": "New York Giants", "commence": "2026-10-11T17:00:00Z", "book": "draftkings",
     "price": -110, "confidence_basis": "MODEL", "confidence": 58},
    {"kind": "fb-line", "league": "nfl", "player": "Over", "market": "total",
     "market_label": "Total", "side": "over", "line": 44.5,
     "game": "Pittsburgh Steelers @ Tampa Bay Buccaneers", "away": "Pittsburgh Steelers",
     "home": "Tampa Bay Buccaneers", "commence": "2026-10-11T20:25:00Z", "book": "hardrockbet",
     "price": -110, "confidence_basis": "MODEL", "confidence": 55}]
_DRIVER = r'''
import os, sys
root, tree = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
os.chdir(tree)
import game_lines_fb
game_lines_fb.ROOT = tree        # the REAL schedule reader, pointed at the planted tree
import record_fb
sys.exit(record_fb.main())
'''


def _gzdump(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(doc, fh)


_t = tempfile.mkdtemp(prefix="fbrec-gl-")
_W1, _D1, _o1 = {}, {}, ""
try:
    os.makedirs(os.path.join(_t, "picks"))
    json.dump({"league": "nfl", "date": _PLANT_DAY, "generated_at": "2026-10-11T12:00:00Z",
               "picks": [], "game_lines": _GL_ROWS},
              open(os.path.join(_t, "picks", "fb-nfl-%s.json" % _PLANT_DAY), "w", encoding="utf-8"))
    _gzdump(os.path.join(_t, "data", "nfl", _PLANT_DAY, "model-picks", "1200.json.gz"),
            {"game_model": [
                {"game": "New Orleans Saints at New York Giants", "game_id": "2026_06_NO_NYG",
                 "commence": "2026-10-11T17:00:00Z"},
                {"game": "Pittsburgh Steelers at Tampa Bay Buccaneers", "game_id": "2026_06_PIT_TB",
                 "commence": "2026-10-11T20:25:00Z"}]})
    _gzdump(os.path.join(_t, "data", "nfl", "latest", "schedule-2026.json.gz"),
            {"games": [{"id": "2026_06_NO_NYG", "final": True, "home_score": 24, "away_score": 17},
                       {"id": "2026_06_PIT_TB", "final": False, "home_score": None,
                        "away_score": None}]})
    _drv = os.path.join(_t, "drive_record_fb.py")
    open(_drv, "w", encoding="utf-8").write(_DRIVER)
    _p1 = subprocess.run([sys.executable, _drv, ROOT, _t], cwd=_t,
                         env=dict(os.environ, LEAGUE="nfl"), capture_output=True,
                         text=True, timeout=300, encoding="utf-8")
    _o1 = (_p1.stdout or "") + (_p1.stderr or "")
    _rp = os.path.join(_t, "data", "nfl", "latest", "record.json")
    _dp = os.path.join(_t, "data", "nfl", "latest", "record-detail.json.gz")
    _W1 = json.load(open(_rp, encoding="utf-8")) if os.path.exists(_rp) else {}
    _D1 = json.load(gzip.open(_dp, "rt", encoding="utf-8")) if os.path.exists(_dp) else {}
finally:
    _sh.rmtree(_t, ignore_errors=True)
_glw = _W1.get("game_lines") or {}
_glo = _glw.get("overall") if isinstance(_glw.get("overall"), dict) else _glw
# ⚠️ PRECONDITIONS, NOT THE QUESTION: without two graded game lines the page
#    checks below would pass on an empty record (rule 67).
ck((_glo.get("w"), _glo.get("n")) == (1, 2),
   "⚠️ the planted grader run graded the two finished game lines (1 won of 2)",
   "a page check over an empty record proves nothing. record.json game_lines: %s; "
   "run said: %s" % (json.dumps(_glw)[:300], _o1[-300:]))
eq(len((_D1.get("game_lines") or {}).get(_PLANT_DAY) or []), 3,
   "⚠️ ...and its record-detail holds all three rows the card showed, unfinished one too")
eq(((_W1.get("board") or {}).get("w"), (_W1.get("board") or {}).get("n")),
   (((_W1.get("overall") or {}).get("w") or 0) + 1, ((_W1.get("overall") or {}).get("n") or 0) + 2),
   "🔴 [Sam, 2026-10-17] the grader's Board = its player props PLUS its game lines "
   "(\"board(all picks)\")")
_r1 = fb_render(_W1, _D1)
_b1 = boxes(_r1.get("html"))
eq([b[0] for b in _b1], ["Board", "Player props", "Game lines"],
   "🔴🔴 [Sam, 2026-10-17] THREE boxes on top, in his order: board, player props, game line")
_bx = {b[0]: (b[1], b[2]) for b in _b1}
eq(_bx.get("Board"), ("50.0%", "1 of 2 graded"),
   "🔴 Board prints the grader's `board` — the props AND the game lines")
eq(_bx.get("Player props"), ("&mdash;", "nothing graded yet"),
   "   Player props prints `overall` — nothing graded here, so an em-dash, never 0%")
eq(_bx.get("Game lines"), ("50.0%", "1 of 2 graded"),
   "🔴🔴 Game lines prints the grader's OWN game-lines number, off the file it WROTE",
   )
_gld = [d.get("gldate") for d in (_r1.get("rows") or []) if d.get("gldate")]
eq(_gld, [_PLANT_DAY],
   "🔴 [Sam, 2026-10-17] \"a game lines tracker\": the graded day is a row you can open")
_c1 = (_r1.get("cells") or {}).get("fbgl-" + _PLANT_DAY) or ""
for _want, _why in (("New York Giants to win", "the moneyline, named as the bet"),
                    ("New Orleans Saints +3.5", "the spread at the team's own signed point"),
                    ("Over 44.5", "the total"),
                    (">HIT<", "the moneyline that won"), (">MISS<", "the spread that lost"),
                    (">UNSETTLED<", "the game not finished, never a miss"),
                    ("17&ndash;24", "the final score, away first")):
    ck(_want in _c1,
       "   DRIVEN: clicking the day opens its game lines — %s" % _why,
       "%r not in the opened box: %r" % (_want, _c1[:300] or _r1))

section("2. ⛔⛔ [Sam, 2026-10-17] \"LOSE THE WAS THE RECORD RIGHT? SECTION\" — FOOTBALL")
# 🔴 DRIVEN ON RECORDS THAT STILL CARRY EVERYTHING THE OLD PANEL DREW FROM, or
#    "no band" would pass on a record with no bands (rule 67): four planted
#    football bands (one a -53 point miss), two methods, a market table's data.
#    The live records are an extra, asserted when they hold bands.
_PLANT_FB = [{"bucket": "80-90%", "stated": 84.1, "w": 11, "n": 23, "pct": 47.8},
             {"bucket": "60-70%", "stated": 65.1, "w": 14, "n": 32, "pct": 43.8},
             {"bucket": "70-80%", "stated": 74.0, "w": 16, "n": 20, "pct": 80.0},
             {"bucket": "90-100%", "stated": 94.2, "w": 12, "n": 30, "pct": 40.0}]
_OLD = [{"bucket": "80-90%", "stated": 84.1, "w": 20, "n": 49, "pct": 40.8},
        {"bucket": "60-70%", "stated": 65.1, "w": 24, "n": 48, "pct": 50.0}]
_FB_REC = {"built_at": "2026-10-17T04:00:00Z", "card_method_current": "season-blend",
           "calibration": _PLANT_FB,
           "calibration_by_method": {"2025-only": _OLD, "season-blend": _PLANT_FB},
           "overall": {"w": 53, "n": 105, "pct": 50.5},
           "board": {"w": 60, "n": 117, "pct": 51.3},
           "game_lines": {"overall": {"w": 7, "n": 12, "pct": 58.3}, "w": 7, "n": 12, "pct": 58.3,
                          "by_day": [{"date": "2026-10-11", "w": 7, "n": 12, "pct": 58.3,
                                      "voids": 0, "pending": 0}]},
           "by_market": {"player_pass_yds": {"w": 10, "n": 20, "pct": 50.0}},
           "by_day": [{"date": "2026-10-11", "w": 53, "n": 105, "carded": 110, "voids": 1,
                       "unresolved": 4}], "days_graded": 1}
_ABSENT_FB = (('class="band"', "calibration band"),
              ("Was the record right?", "'Was the record right?' heading"),
              ("current method", "method table label (current)"),
              ("2025-only method", "method table label (2025-only)"),
              ("earlier method", "method table label (earlier)"),
              ("fb-cal-empty", "'no graded picks under the method' line"),
              ('class="legend"', "legend for the bands"),
              ("<th>Market</th>", "market table"))
_VOICE = ("claimed", "we said")
for _what, _rec, _lg in (("PLANTED", _FB_REC, "nfl"), ("the live nfl record", REAL["nfl"], "nfl"),
                         ("the live ncaaf record", REAL["ncaaf"], "ncaaf")):
    if _rec is not _FB_REC and not all_bands(_rec):
        note("⚠️ NOT EXERCISED ON %s: it holds no band to leave out — the planted "
             "record asked every question" % _what.upper())
        continue
    _r2 = fb_render(_rec, lg=_lg)
    _h2 = _r2.get("html")
    ck(isinstance(_h2, str) and "record</h2>" in _h2,
       "⚠️ fbRecord drew the tab (%s)" % _what,
       "⛔ an absence check over a tab that never rendered proves nothing: %s" % _r2)
    for _s, _why in _ABSENT_FB:
        ck(isinstance(_h2, str) and _s not in _h2,
           "⛔ [Sam, 2026-10-17] the tab draws no %s (%s)" % (_why, _what),
           "~~drawn under 'Was the record right?'~~; looked for %r" % _s)
    for _s in _VOICE:
        ck(isinstance(_h2, str) and _s not in _h2,
           "⛔ [Sam, 2026-10-17] nothing on the tab speaks of a claim: no %r (%s)" % (_s, _what),
           "~~bandRow's tooltip and legend said 'the record claimed' / 'we said'~~; "
           "looked for %r" % _s)
    eq(_r2.get("winners"), 0,
       "⛔ [Sam, 2026-10-17] \"Just the by-date lists\": the winners' line is not drawn (%s)" % _what)
    eq([b[0] for b in boxes(_h2)], ["Board", "Player props", "Game lines"],
       "   ...and the three boxes are all that sits on top (%s)" % _what)
    ck(isinstance(_h2, str) and "Player props by day" in _h2 and "Game lines by day" in _h2,
       "   ...and the two by-date lists are there (%s)" % _what)

section("3. ⛔⛔ [Sam, 2026-10-17] MLB: \"Remove both\" — AND THE SAME THREE BOXES")
# 🔴 MLB's renderRecord, the page's own, on a planted record in collect.py's
#    shape (`game_lines` = its tally at the top, as `collect_record` writes it
#    and verify_record checks it) that STILL CARRIES the calibration buckets,
#    the by-market and by-kind tables, and an mlb-refit.json to read. Every
#    removed panel had its data; none may draw.
_MLB_REC = {"built_at": "2026-10-17T05:00:00Z",
            "overall": {"w": 30, "n": 50, "pct": 60.0},
            "board": {"w": 36, "n": 60, "pct": 60.0},
            "game_lines": {"w": 6, "n": 10, "pct": 60.0, "voids": 1,
                           "by_market": {"moneyline": {"w": 4, "n": 6, "pct": 66.7},
                                         "run_line": {"w": 2, "n": 4, "pct": 50.0}},
                           "by_day": [{"date": "2026-10-11", "w": 2, "n": 3, "pct": 66.7}]},
            "by_kind": {"pitcher": {"w": 10, "n": 20, "pct": 50.0},
                        "hitter": {"w": 20, "n": 30, "pct": 66.7}},
            "days_graded": 10,
            "by_market": {"strikeouts": {"w": 10, "n": 20, "pct": 50.0}},
            "by_day": [{"date": "2026-10-11", "w": 5, "n": 8, "voids": 0}],
            "calibration": [
                {"bucket": "50-60%", "predicted": 56.5, "w": 99, "n": 205, "pct": 48.3},
                {"bucket": "60-70%", "predicted": 64.2, "w": 200, "n": 395, "pct": 50.6},
                {"bucket": "70-80%", "predicted": 74.8, "w": 71, "n": 90, "pct": 78.9}],
            "calibration_meta": {"rows": 690}}
_MLB_DETAIL = {"days": {"2026-10-11": [
                  {"player": "Logan Webb", "game": "SF @ LAD", "market": "strikeouts",
                   "side": "over", "line": 5.5, "confidence": 71, "price": -130,
                   "actual": 7, "won": True}]},
               "game_lines": {"2026-10-11": [
                  {"team": "Los Angeles Dodgers", "game": "SF @ LAD", "market": "moneyline",
                   "line": None, "confidence": 62, "price": -140, "home_score": 5,
                   "away_score": 3, "won": True}]}}
_REFIT = {"built_at": "2026-10-13T09:00:00Z", "verdict": "DOES NOT QUALIFY",
          "display": {"champion": {}, "challenger": {}, "paired": {}}}
_r3 = mlb_render(_MLB_REC, _MLB_DETAIL, _REFIT)
_h3 = _r3.get("html")
ck(isinstance(_h3, str) and "Automatic card" in _h3,
   "⚠️ MLB's renderRecord drew the tab", "⛔ an absence check over nothing: %s" % _r3)
for _s, _why in (('class="band"', "calibration band"),
                 ("Does the confidence number mean anything?", "confidence panel"),
                 ("Is v5.0 still the best version?", "refit panel ('Is v5.0 still the best version?')"),
                 ('class="legend"', "legend for the bands"),
                 ("<th>Market</th>", "by-market table"),
                 ("data-winners", "winners' line"),
                 ("claimed", "claim ('what we claimed')"), ("we said", "first-person 'we said'")):
    ck(isinstance(_h3, str) and _s not in _h3,
       "⛔ [Sam, 2026-10-17] MLB's Track Record draws no %s" % _why,
       "\"Remove both\" / \"Just the by-date lists\"; looked for %r" % _s)
eq(_r3.get("winners"), 0, "⛔ [Sam, 2026-10-17] ...and asks for no winners' record at all")
ck(not any("mlb-refit" in p for p in (_r3.get("fetched") or [])),
   "⛔ [Sam, 2026-10-17] ...and reads no mlb-refit.json (the file is still built; the page "
   "stopped drawing it)", "fetched %s" % _r3.get("fetched"))
_b3 = boxes(_h3)
eq([b[0] for b in _b3], ["Board", "Player props", "Game lines"],
   "🔴🔴 [Sam, 2026-10-17] MLB's top is the same three boxes (~~Auto card, Pitchers, "
   "Hitters, Cards graded~~ and the game lines' own boxes)")
eq([(b[1], b[2]) for b in _b3],
   [("60.0%", "36 of 60 graded"), ("60.0%", "30 of 50 graded"), ("60.0%", "6 of 10 graded")],
   "   ...each printing the record's own number: board, overall, game_lines")
ck(isinstance(_h3, str) and "Player props by day" in _h3 and "Game lines by day" in _h3,
   "   ...and below them the two by-date lists, and nothing else")
_MLB_LIVE = json.load(open(os.path.join(ROOT, "data", "latest", "record.json"), encoding="utf-8"))
if _MLB_LIVE.get("calibration"):
    _r3l = mlb_render(_MLB_LIVE)
    ck(isinstance(_r3l.get("html"), str) and 'class="band"' not in _r3l["html"]
       and "Does the confidence number mean anything?" not in _r3l["html"],
       "⛔ ...and on the LIVE MLB record, which still carries %d band(s), none is drawn"
       % len(_MLB_LIVE["calibration"]), "got %s" % str(_r3l)[:300])
else:
    note("⚠️ the live MLB record holds no band — the planted record asked the question")

section("4. ⚠️ NOTHING GRADED IS AN EM-DASH, NEVER A BOX AT 0%")
# `[Sam, 2026-10-17]` ~~an empty bucket is 'No sample', not a bar at zero~~:
#    the same honesty on the new boxes — "nothing graded" and "graded 0%" are
#    different facts. Driven on what the grader writes for nothing: its own
#    tally of no rows ({w:0, n:0, pct:null}), and on a record that is missing.
_r4 = out("console.log(JSON.stringify({empty: trBox('Game lines', {w:0, n:0, pct:null}),"
          " missing: trBox('Game lines', undefined), zero: trBox('Board', {w:0, n:4, pct:0})}));")
for _k in ("empty", "missing"):
    ck(boxes(_r4.get(_k)) == [("Game lines", "&mdash;", "nothing graded yet")],
       "   a box with nothing graded reads em-dash and says so (%s)" % _k,
       "⛔ a box nobody graded is not a box that lost. Got %r" % _r4.get(_k))
eq(boxes(_r4.get("zero")), [("Board", "0.0%", "0 of 4 graded")],
   "   ...while four graded and none won IS 0.0% — a real number, shown")

section("5. 🔴 EVERY GRADED DAY ROW IS CLICKABLE, AND ONLY THE GRADED ONES")
_DAYS = [{"date": "2026-09-09", "w": 5, "n": 10, "carded": 12, "voids": 0,
          "unresolved": 2},
         {"date": "2026-09-10", "w": 0, "n": 0, "carded": 4, "voids": 0,
          "unresolved": 4}]
_r5 = out("const h = fbDayRows(%s, {});"
          "console.log(JSON.stringify({dates:[...h.matchAll(/data-date=\"([^\"]*)\"/g)]"
          ".map(m=>m[1]), rows:(h.match(/class=\"dayrow/g)||[]).length,"
          "detail:[...h.matchAll(/id=\"fbdd-([^\"]*)\"/g)].map(m=>m[1]),"
          "carets:(h.match(/class=\"caret\"/g)||[]).length}));" % json.dumps(_DAYS))
eq(_r5.get("dates"), ["2026-09-10", "2026-09-09"][1:],
   "🔴 the graded day carries data-date")
eq(_r5.get("detail"), ["2026-09-09"],
   "   ...and a detail row to open into")
eq(_r5.get("carets"), 1, "   ...and exactly one caret")
ck("2026-09-10" not in (_r5.get("dates") or []),
   "⛔ the day with NOTHING graded is not clickable",
   "🔴 a caret that opens an empty box reads as a broken page, not as an "
   "honest empty state")
_r5b = out("const h = fbDayRows([], {record_from:'2026-09-07'});"
           "console.log(JSON.stringify({h, rows:(h.match(/dayrow/g)||[]).length}));")
eq(_r5b.get("rows"), 0, "   an empty record wires nothing")
ck("Nothing graded since 2026-09-07" in (_r5b.get("h") or ""),
   "   ...and keeps the sentence record_fb.py computed",
   "rule 132: the page prints the grader's number, it does not carry one")
# `[Sam, 2026-10-17]` "a game lines tracker": the game lines by day, the same way.
#    A day settled only by a push still has rows behind it (VOID); a day whose
#    games have not finished has nothing settled and is not clickable.
_GLDAYS = [{"date": "2026-10-11", "w": 1, "n": 2, "pct": 50.0, "voids": 0, "pending": 1},
           {"date": "2026-10-12", "w": 0, "n": 0, "pct": None, "voids": 1, "pending": 0},
           {"date": "2026-10-13", "w": 0, "n": 0, "pct": None, "voids": 0, "pending": 3}]
_r5c = out("const h = fbLineDayRows(%s);"
           "console.log(JSON.stringify({h, gl:[...h.matchAll(/data-gldate=\"([^\"]*)\"/g)].map(m=>m[1]),"
           "props:(h.match(/ data-date=/g)||[]).length,"
           "detail:[...h.matchAll(/id=\"fbgl-([^\"]*)\"/g)].map(m=>m[1]),"
           "carets:(h.match(/class=\"caret\"/g)||[]).length}));" % json.dumps(_GLDAYS))
eq(_r5c.get("gl"), ["2026-10-12", "2026-10-11"],
   "🔴 [Sam, 2026-10-17] every settled game-lines day carries data-gldate, newest first")
eq(_r5c.get("detail"), ["2026-10-12", "2026-10-11"],
   "   ...and its own fbgl-<date> row to open into")
eq(_r5c.get("carets"), 2, "   ...and one caret each")
eq(_r5c.get("props"), 0,
   "⛔ ...and never a props `data-date`: the click must open the game lines, not a card")
ck("2026-10-13" not in (_r5c.get("gl") or []),
   "⛔ the day with nothing settled yet is not clickable")
ck("50.0%" in (_r5c.get("h") or ""),
   "   the day prints its hit rate off the grader's own w/n for that day")
_r5d = out("console.log(JSON.stringify({h: fbLineDayRows([])}));")
ck("No game lines graded yet." in (_r5d.get("h") or "")
   and "dayrow" not in (_r5d.get("h") or ""),
   "   an empty game-lines record says so in one plain line and wires nothing")

section("6. ⛔⛔ THE DETAIL CACHE IS KEYED BY LEAGUE")
# 🔴 MLB's `loadRecordDetail()` caches in ONE module-level `RECDETAIL` and
#    hard-codes `data/latest/`. A football copy of that shape serves nfl's
#    picks under ncaaf the moment you switch — SILENTLY, AND LOOKING
#    CORRECT. This drives exactly that: load nfl, then ncaaf, and assert
#    the second is not the first.
_r6 = out(
    "const a = await fbDetailLoad('nfl', {detail_file:'NFL'});"
    "const b = await fbDetailLoad('ncaaf', {detail_file:'NCAAF'});"
    "const c = await fbDetailLoad('nfl', {detail_file:'NFL'});"
    "console.log(JSON.stringify({a:a.who, b:b.who, c:c.who, fetches:FETCHED}));",
    extra="let FETCHED=[];"
          "async function jgetGz(p){ FETCHED.push(p); return {who:p}; }")
eq(_r6.get("a"), "NFL", "   nfl serves the nfl file")
eq(_r6.get("b"), "NCAAF",
   "🔴🔴 ...AND NCAAF SERVES THE COLLEGE FILE, NOT NFL'S",
   )
eq(_r6.get("c"), "NFL", "   ...and nfl still serves nfl afterwards")
eq(_r6.get("fetches"), ["NFL", "NCAAF"],
   "⚠️ fetched ONCE PER LEAGUE and cached — the third call hit no network",
   )
_r6b = out(
    "const a = await fbDetailLoad('nfl', null);"
    "console.log(JSON.stringify({path:a.who}));",
    extra="async function jgetGz(p){ return {who:p}; }")
eq(_r6b.get("path"), "data/nfl/latest/record-detail.json.gz",
   "   ⚠️ ...and a record with no detail_file falls back to the league path")
# 🔴 `[2026-09-28]` ~~eq(REAL[_lg]["detail_file"], ...)~~ read a field off
#    the STORED record (P2: a fact about the last grader run, not about the
#    grader — rule 181). ✅ The WRITER is driven instead: `record_fb.py` run
#    in an empty tree for each league must write `detail_file` naming that
#    league's drill-down. The stored value is reported.
for _lg in ("nfl", "ncaaf"):
    _t = tempfile.mkdtemp(prefix="fbrec-writer-")
    try:
        _p = subprocess.run([sys.executable, os.path.join(ROOT, "record_fb.py")],
                            cwd=_t, env=dict(os.environ, LEAGUE=_lg),
                            capture_output=True, text=True, timeout=300)
        _rp = os.path.join(_t, "data", _lg, "latest", "record.json")
        _w = json.load(open(_rp, encoding="utf-8")) if os.path.exists(_rp) else {}
    finally:
        _sh.rmtree(_t, ignore_errors=True)
    eq(_w.get("detail_file"), "data/%s/latest/record-detail.json.gz" % _lg,
       "   record_fb.py writes the %s record's OWN detail_file (planted tree)" % _lg)
    # `[Sam, 2026-10-17]` the two new boxes' sources, written even with nothing graded
    ck(isinstance(_w.get("board"), dict) and isinstance(_w.get("game_lines"), dict),
       "   ...and the `board` and `game_lines` the new boxes read (%s, empty tree)" % _lg,
       "record.json keys: %s" % sorted(_w)[:40])
    note("the stored %s record says detail_file=%r"
         % (_lg, REAL[_lg].get("detail_file")))

# `[Sam, 2026-10-01]` ~~DEGRADES TO A NOTE~~ — no explanation box on any tab;
#    the degrade is now ONE plain line, and is driven through the click handler.
section("7. ⛔ A MISSING DETAIL FILE DEGRADES TO ONE PLAIN LINE, NOT AN EXCEPTION")
_r7 = out(
    "let msg='';"
    "try { await fbDetailLoad('nfl', {detail_file:'gone'}); msg='NO THROW'; }"
    "catch(e){ msg='threw: ' + e.message; }"
    "console.log(JSON.stringify({msg}));",
    extra="async function jgetGz(p){ throw new Error(p + ' -> 404'); }")
ck((_r7.get("msg") or "").startswith("threw:"),
   "   the loader propagates the failure to its caller",
   "⛔ swallowing it inside the loader would cache `undefined` as the "
   "league's detail forever. Got %r" % _r7.get("msg"))
_WIRE = js_block("fbWireDayRows", IDX)
ck("catch" in _WIRE and "No detail file yet" in _WIRE,
   "🔴 ...and the CALLER catches it and writes one plain line",
   "⛔ before the first graded card there is no detail file and that is "
   "not an error — a broken tab would say the product is broken when it "
   "is merely new")
# 🔴 `[Sam, 2026-10-01]` ~~ck("record-detail.json.gz" in _WIRE, "   ...naming
#    the file the grader will write")~~. The degrade was a cream note box
#    naming the file the grader would write on its next run. Sam: no
#    explanation, caveat or warning box on any tab ("i just want what's
#    supposed to be in each tab to be in each tab"; asked what stays, he
#    chose: remove everything). So the box and its sentence are required
#    ABSENT, asked of the same function; and because a source read cannot
#    see what a click draws, the handler is DRIVEN: a click on a graded day
#    whose detail file is gone must leave exactly one plain line in the cell.
ck('class="note"' not in _WIRE and "record-detail.json.gz" not in _WIRE
   and "<code>" not in _WIRE,
   "⛔ [Sam, 2026-10-01] ...and NO note box naming the file the grader will write",
   "the file name and 'on its next run' were the box's sentence; the "
   "plain line says only that there is no file")
# ⚠️ THE SMALLEST DOM THE HANDLER TOUCHES, NOT A COPY OF IT: one row, one
#    detail box, one cell. fbWireDayRows itself is pulled from the page (node()).
#    `[Sam, 2026-10-17]` and the same for a game-lines day (`data-gldate`).
_DOM = ("const CELL = {dataset:{}, innerHTML:''};"
        "const BOX = {hidden:true, querySelector: () => CELL};"
        "let CLICK = null;"
        "const TR = {dataset: DS, classList:{add(){}, remove(){}},"
        "  addEventListener: (ev, fn) => { CLICK = fn; }};"
        "const document = {querySelectorAll: () => [TR], querySelector: () => BOX};"
        "async function jgetGz(p){ throw new Error(p + ' -> 404'); }\n")
for _what, _ds in (("a props day", {"date": "2026-09-09"}),
                   ("a game-lines day", {"gldate": "2026-10-11"})):
    _r7c = out("fbWireDayRows('nfl', {detail_file:'data/nfl/latest/record-detail.json.gz'});"
               "if (!CLICK) throw new Error('no click handler was wired');"
               "await CLICK();"
               "console.log(JSON.stringify({html: CELL.innerHTML}));",
               extra="const DS = %s;" % json.dumps(_ds) + _DOM)
    _h7 = _r7c.get("html")
    ck(isinstance(_h7, str)
       and bool(_re.fullmatch(r'\s*<p class="plain">[^<]*</p>\s*', _h7))
       and "No detail file yet" in _h7,
       "🔴 [Sam, 2026-10-01] DRIVEN: the click draws ONE plain line, not a broken tab (%s)" % _what,
       "⛔ a rejected handler leaves 'Loading…' in the cell for good. Got %r"
       % (_h7 if _h7 is not None else _r7c))
    ck(isinstance(_h7, str) and 'class="note"' not in _h7
       and "record-detail.json.gz" not in _h7 and "<code>" not in _h7,
       "⛔ [Sam, 2026-10-01] DRIVEN: ...and the cell holds no note box and no file name (%s)" % _what,
       "the record passed in names its detail_file, which the old box printed")
_r7b = out("const h = fbDayDetailHtml(null);"
           "const g = fbDayDetailHtml([]);"
           "const a = lineDetailHtml(null); const b = lineDetailHtml([]);"
           "const td = fbDayDetailHtml([{player:'Ja\\'Marr Chase', game:'CIN @ PIT', side:'yes',"
           " line:null, market:'player_anytime_td', market_label:'Anytime TD', confidence:41,"
           " price:150, actual:1, won:true}]);"
           "console.log(JSON.stringify({h, g, a, b, td}));")
ck("No rows stored" in (_r7b.get("h") or "")
   and "No rows stored" in (_r7b.get("g") or ""),
   "   ⚠️ and a day present in the file with no rows says so too",
   "an undefined day and an empty day are both 'nothing to show'")
ck("No game lines stored for that day." in (_r7b.get("a") or "")
   and "No game lines stored for that day." in (_r7b.get("b") or ""),
   "   ⚠️ [Sam, 2026-10-17] ...and so does a game-lines day with no rows, never an empty box",
   "got %r / %r" % (_r7b.get("a"), _r7b.get("b")))
_td = _r7b.get("td") or ""
ck("Yes Anytime TD" in _td and "null" not in _td and "Under" not in _td,
   "🔴 an anytime TD row reads \"Yes ... Anytime TD\" (~~\"Under null\"~~)",
   "the prop has one side and no line; got %r" % _td[:300])

section("8. ⛔⛔ MLB'S RECORD FUNCTIONS — BYTE-IDENTICAL, NOT 'I DIDN'T MEAN TO'")
# 🔒 EVERY HASH BELOW WAS TAKEN FROM `origin/main` ON 2026-09-16, BEFORE
#    THIS CHANGE. ⛔ DO NOT UPDATE ONE TO MAKE THIS PASS. The freeze says
#    MLB does not change; teaching `bandRow` about `stated` would be
#    editing MLB through the back door, and this is the check that refuses
#    it. If a hash is red, the answer is to revert the MLB function.
# ⚠️ ~~`bandRow` pinned by hash~~ — REMOVED 2026-09-17, deliberately, and
#    replaced by section 9. The hash asked "did this source change?", and
#    the answer is now YES: it takes an optional label. ⛔ The question
#    that matters is whether MLB's RENDERED OUTPUT changed, and section 9
#    answers it by diffing MLB's real bands through a frozen copy of the
#    old function against the live one.
# 🔴 SAY WHAT THIS GIVES UP: a hash forbids every edit; a rendered diff
#    permits any edit MLB cannot see. That is the narrower licence Sam
#    granted for this change, and it is written down rather than implied.
# ⚠️ renderRecord re-baselined 2026-09-23 (~~20cb8492840fbdc4~~) on Sam's
#    instruction — MLB unfrozen 2026-09-22, and his MLB learning task puts the
#    labelled champion-vs-challenger panel on this tab. The same amendment is
#    recorded in research/mlb_render_frozen.json's `_why`.
# ⚠️ `[Sam, 2026-10-01]` renderRecord (~~0975b831faa24360~~) and
#    dayDetailHtml (~~cf90d3ea7c684cf9~~) RE-BASELINED on Sam's instruction:
#    "i just want what's supposed to be in each tab to be in each tab ... do
#    this for all 3 leagues", and asked what stays he chose: remove
#    everything. Diffed against caa9a69e, each lost ONLY its cream note boxes
#    (renderRecord also its MODEL tag and its explanatory sentences; each
#    empty state is now one plain line); every table, band and figure
#    outside those boxes is unchanged. Pinned at the old bytes these
#    hashes REQUIRED the boxes; pinned at the new bytes they require their
#    ABSENCE. The same amendment is in research/mlb_render_frozen.json's
#    `_why` (c698d885). loadRecordDetail did not change and keeps its hash.
#    Second pass the same day (~~961ab07b215a4018~~): the "machine cards
#    only" caption under the Cards graded tile went too; recorded in the
#    oracle's second 2026-10-01 `_why` entry.
# ⚠️ `[Sam, 2026-10-02]` renderRecord (~~d854430216da3fdc~~) RE-BASELINED on
#    his MLB game-lines instruction: "game-line picks graded once from the
#    final score in their own line of the MLB Track Record, never mixed with
#    props". ONE line added, `${mlbGameLineRecord(R)}` under the props hero;
#    nothing else in the function moved. Recorded in the oracle's 2026-10-03
#    `_why` entry.
# ⚠️ `[Sam, 2026-10-01]` renderRecord (~~981c51d929ac4e9c~~) RE-BASELINED on his Game
#    Lines instruction ("just give the models pick on whos going to win the
#    game outright. do this for all leagues"): ONE line, the winners' own
#    record (`winnersRecordLine(W)`), and the file it is read from. Recorded
#    in the oracle's 2026-10-03 `_why` entry.
# ⚠️ `[Sam, 2026-10-17]` renderRecord (~~52ae9c56871ead09~~) RE-BASELINED on his
#    Track Record instruction: "i only want the board hit % to be shown ... all in
#    all wed have 3 different hit rate % shows at the top of the track record tab,
#    board(all picks), player props(only player props), and game line(only game
#    lines)"; for MLB he chose "Remove both" and, below the three, "Just the by-date
#    lists". Diffed against 1deeada6: the four boxes (Auto card, Pitchers, Hitters,
#    Cards graded), the game lines' own boxes, the winners' line, the by-market
#    table, the confidence panel and the refit panel left; three trBox boxes, the
#    game lines by day and their click (gl-<date>, lineDetailHtml) came in; the
#    props by day and its click are as they were. Pinned at the old bytes the
#    hash REQUIRED the bands and the refit panel; at the new bytes it requires
#    their ABSENCE (section 3 drives it). Recorded in research/mlb_render_frozen.json's
#    2026-10-17 `_why` entry. dayDetailHtml and loadRecordDetail did not change
#    and keep their hashes.
_MAIN = {"renderRecord": "8163724c0ee7fb04",
         "dayDetailHtml": "93671bc164e26a96",
         "loadRecordDetail": "a6fff37555f03ce7"}
for _n, _want in sorted(_MAIN.items()):
    _got = hashlib.sha256(js_block(_n, IDX).encode()).hexdigest()[:16]
    eq(_got, _want, "🔒 %s is byte-identical to its pinned bytes" % _n)
# ⚠️ AND THE HASHES ARE NOT THE WHOLE CLAIM. A hash says "unchanged"; this
#    says WHAT must stay true, so a deliberate MLB edit still trips it.
# `[Sam, 2026-10-17]` ~~bandRow knows nothing of `stated`/`pct`/`bucket` ... and still
#    takes MLB's own `said`/`hit`~~: bandRow is deleted (section 0 requires it gone),
#    so what must stay true is that no call site maps a band at all.
# 🔴 `[Sam, 2026-10-01]` ~~eq(_IDXSRC.count("${P.calibration_warning}"), 1,
#    "⛔ the MLB card's own render is still exactly one occurrence")~~. The
#    MLB card printed its calibration_warning in a cream "Read the confidence
#    number honestly" box, and this pinned that render at exactly one, with
#    no football copy beside it. Sam removed every confidence pop-up on every
#    tab ("we have a track record for a reason"), so the page now reads the
#    field NOWHERE: not MLB's `P.`, not football's `C.` (fbCalNote is
#    deleted). ⚠️ card.py and card_fb.py still WRITE it; this asks only the
#    page. Comments are stripped first: a dated note naming the field is not
#    a render, and a guard that fired on one would fire on correct code.
eq(_IDXCODE.count(".calibration_warning"), 0,
   "⛔ [Sam, 2026-10-01] no tab renders the calibration_warning pop-up — "
   "not MLB's `P.`, not football's `C.`")
# 🔴 `[Sam, 2026-10-17]` ~~`said: c.predicted` appears ONCE — MLB's call site only~~
#    and ~~football's `said: c.stated` is its own, separate call~~: "lose the was the
#    record right? section"; for MLB "Remove both". Neither league maps a band now.
eq(_IDXCODE.count("said: c.predicted"), 0,
   "⛔ [Sam, 2026-10-17] `said: c.predicted` appears NOWHERE — MLB draws no band")
eq(_IDXCODE.count("said: c.stated"), 0,
   "⛔ [Sam, 2026-10-17] ...and neither does football's `said: c.stated`")

section("9. 🔴🔴 MLB'S DAYS OPEN THEIR OWN BOXES — PROPS AND GAME LINES APART")
# `[Sam, 2026-10-17]` ~~A SHARED COMPONENT CARRIES ITS FIRST CALLER'S VOICE~~:
#    this section diffed MLB's bands through `research/bandrow_pre_saidas.js`
#    (a frozen copy of bandRow) against the live bandRow, and pinned the "we
#    said" voice. bandRow is deleted, so there is nothing to diff and no voice
#    to pin; section 0 requires it gone and sections 2-3 that no Track Record
#    speaks of a claim. ⚠️ The oracle stays in research/ as a record; no check
#    reads it. In its place: MLB's renderRecord WIRES its day rows (section 3's
#    render), and each click must open ITS box with ITS detail — the props day
#    through dayDetailHtml, the game-lines day through lineDetailHtml.
_cells = _r3.get("cells") or {}
_rows3 = _r3.get("rows") or []
eq(sorted(tuple(sorted(d.items())) for d in _rows3),
   sorted([(("date", "2026-10-11"),), (("gldate", "2026-10-11"),)]),
   "🔴 [Sam, 2026-10-17] MLB draws one props day (data-date) and one game-lines "
   "day (data-gldate), each clickable")
ck("Logan Webb" in (_cells.get("dd-2026-10-11") or "")
   and "Los Angeles Dodgers" not in (_cells.get("dd-2026-10-11") or ""),
   "   DRIVEN: the props day opens dd-<date> with that card's props, and only those",
   "dd cell: %r" % (_cells.get("dd-2026-10-11") or "")[:300])
_g9 = _cells.get("gl-2026-10-11") or ""
ck("Los Angeles Dodgers to win" in _g9 and ">HIT<" in _g9 and "3&ndash;5" in _g9
   and "Logan Webb" not in _g9,
   "🔴 [Sam, 2026-10-17] DRIVEN: the game-lines day opens gl-<date> with its game "
   "lines (lineDetailHtml), never the props",
   "gl cell: %r; every cell: %s" % (_g9[:300], sorted(_cells)))
ck(any("record-detail" in p for p in (_r3.get("fetched") or [])),
   "   ...both read from the one record-detail file, fetched by loadRecordDetail",
   "fetched %s" % _r3.get("fetched"))

note("📌 THE CLASS, SWEPT AND REPORTED `[2026-09-17]`: of the renderers "
     "BOTH boards share — pickCard, bandRow, freshness, startedToggle, "
     "splitStarted, cardStaleNote — `bandRow` was the ONLY one with a "
     "hard-coded voice in rendered output. `pickCard` already branches on "
     "the row's own `confidence_basis` and prints 'RECORD — no model' "
     "where that is what the row is. `cardStaleNote` says 'projections' "
     "but is called only by MLB's renderPicks and renderParlays, so its "
     "voice matches its only callers. ⛔ Nothing else was fixed here. "
     "`[2026-10-01]` cardStaleNote no longer exists: Sam removed the "
     "stale notes from every tab. `[2026-10-17]` bandRow no longer exists: "
     "Sam removed the bands from every Track Record.")

note("⛔ WHAT THIS DOES NOT CLAIM: that the tab LOOKS right. It claims the "
     "three boxes print the grader's own board / props / game-lines numbers "
     "(football off a record the real grader wrote; MLB off a record in "
     "collect.py's shape, which verify_record re-checks), that no band, "
     "method table, market table, winners' line or refit panel is drawn in "
     "either league, that a graded day of either kind can be opened into its "
     "own rows, that the cache cannot serve the wrong league, and that MLB's "
     "three record functions are byte-for-byte their pinned bytes. Rendering "
     "it in a browser is still the only way to see it.")
