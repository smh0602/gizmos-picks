#!/usr/bin/env python3
"""test_agree_flags_page.py — the agreement label and the news flags, as the
SHIPPED page code draws them (sliced out of `index.html` and run in node).

`[Sam, 2026-10-01]` *"i just want what's supposed to be in each tab to be in
each tab"*: no tag, no per-row flag, no explanation on any tab. This file
USED TO REQUIRE the label and every news flag on the rows, each number
wearing its basis (Descriptive / Record / Model / Market). ~~It now requires
the label and its numbers with NO tag, NO news flag on any row, and the two
records' tables without their explanations.~~

`[Sam, 2026-10-17]` *"it should be as simple as the mlb gizmos picks"*: the
props model's panel -- the one place the label was still drawn, its "Card
vs model" cell -- and the "Card vs props model" record under the board both
left Gizmo's Picks. So this file now requires the label, its finder, its
loader and its record to be GONE from the page (nothing loads
agreement.json), NO news flag on any row, and the flags' record (the News
tab) with its numbers and without its explanation. ⛔ `fb_agreement.py` still
writes, freezes and grades every label (`test_fb_agreement.py`) and
`news_flags_fb.py` every flag (`test_news_flags_fb.py`); this file asks only
what is DRAWN.

# @vacuity [Sam, 2026-10-17] the label renderer is gone from the shipped code (~~[Sam, 2026-10-01] the label's numbers wear no tag~~): one put back in the slice
#   file: index.html
#   find: const FBFLAGS = {};
#   with: const FBFLAGS = {}; function fbAgHtml(r){ return (r && r.label) ? '<span class="agl"><b>' + r.label + '</b> card ' + r.card_p + '% &middot; break-even ' + r.break_even + '%</span>' : ''; }
#
# @vacuity [Sam, 2026-10-01] a card row on Gizmo's Picks gets no notes line under it
#   file: index.html
#   find:   kept.forEach(p => host.append(pickCard(p)));
#   with:   kept.forEach(p => { host.append(pickCard(p)); host.insertAdjacentHTML('beforeend', fbRowNotes(p, AG, FL)); });
#
# @vacuity [Sam, 2026-10-17] the page loads nothing from agreement.json (~~[Sam, 2026-10-01] a started game's row no longer says 'frozen before kickoff'~~)
#   file: index.html
#   find:   FBFLAGS[LEAGUE] = await jget(
#   with:   FBFLAGS.ag = await jget(`${LG_DATA[LEAGUE]}/latest/agreement.json`); FBFLAGS[LEAGUE] = await jget(
#
# @vacuity [Sam, 2026-10-17] no row draws a label span (~~[Sam, 2026-10-01] a started row never frozen draws nothing, not its label_note~~)
#   file: index.html
#   find:   [...host.children].forEach((c, i) => fbEdgeLine(c, kept[i]));
#   with:   [...host.children].forEach((c, i) => { fbEdgeLine(c, kept[i]); if (kept[i].label_note) c.insertAdjacentHTML('beforeend', '<span class="agl">' + fbEsc(kept[i].label_note) + '</span>'); });
#
# @vacuity [Sam, 2026-10-17] no label finder is defined anywhere on the page (~~a row with no label draws nothing~~)
#   file: index.html
#   find: function fbFlagsRecordHtml(FL){
#   with: function fbAgFind(AG, p){ return ((AG || {}).rows || []).find(r => r.player === p.player); } function fbFlagsRecordHtml(FL){
#
# @vacuity [Sam, 2026-10-01] no row-flag renderer is left in the shipped code
#   file: index.html
#   find: function fbFlagsRecordHtml(FL){
#   with: function fbFlagOne(f){ return '<span class="fbflag">' + f.status + '</span>'; } function fbFlagsRecordHtml(FL){
#
# @vacuity [Sam, 2026-10-17] no 'Card vs props model' record panel is drawn (~~[Sam, 2026-10-01] the agreement record carries no explanation paragraph~~)
#   file: index.html
#   find:   v.insertAdjacentHTML('beforeend', fbTopPlays(C, kept));
#   with:   v.insertAdjacentHTML('beforeend', fbTopPlays(C, kept) + '<div class="panel"><h2>Card vs props model &mdash; do they agree?</h2></div>');
#
# @vacuity [Sam, 2026-10-17] Gizmo's Picks draws no record by label under the board (~~the tab still shows the record by label~~)
#   file: index.html
#   find:   v.insertAdjacentHTML('beforeend', fbTopPlays(C, kept));
#   with:   v.insertAdjacentHTML('beforeend', fbTopPlays(C, kept)); v.insertAdjacentHTML('beforeend', fbAgRecordHtml(FBAG[LEAGUE]));
#
# @vacuity [Sam, 2026-10-01] the flags' record carries no explanation (college's note)
#   file: index.html
#   find:   <div class="panel" style="margin-top:18px"><h2>News flags &mdash; how often they were right</h2>
#   with:   <div class="panel" style="margin-top:18px"><h2>News flags &mdash; how often they were right</h2><p>${FL.college_note || ''}</p>
#
# @vacuity [Sam, 2026-10-01] no news flag reaches a props row
#   file: index.html
#   find:   rows += rowHtml(p, k, sides[k]); total++;
#   with:   rows += rowHtml(p, k, sides[k]) + fbFlagHtml(fbFlagsFor(FBFLAGS[LEAGUE], 'player', p.player, g.id)); total++;
#
# @vacuity [Sam, 2026-10-01] the flag renderers are neither defined nor called anywhere on the page
#   file: index.html
#   find:   v.insertAdjacentHTML('beforeend', fbFlagsRecordHtml(await fbFlagsLoad()));
#   with:   v.insertAdjacentHTML('beforeend', fbFlagsRecordHtml(await fbFlagsLoad()) + ((FBFLAGS[LEAGUE] || {}).flags || []).map(f => fbFlagOne(f)).join(''));
"""
import json
import os
import re
import shutil
import subprocess
import tempfile

from jsblock import calls, js_block, source, top_level_blocks
from tcheck import ck, section

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, "index.html")

# `[Sam, 2026-10-01]` ANY tag, whatever its quotes or its kind: the class
#    `kind` and every `k-<basis>` the page used to print beside a number.
TAG = re.compile(r"""class=["'][^"']*\bkind\b|\bk-(?:model|market|desc|live|record)\b""")
# The renderers that drew a note or a news flag ON A ROW. ⛔ Gone since
#    2026-10-01; the flags' own table (fbFlagsRecordHtml) stays on News.
GONE_FLAGS = ("fbRowNotes", "fbFlagOne", "fbFlagHtml", "fbFlagsFor", "fbParlayFlagsHtml")
# `[Sam, 2026-10-17]` The card-vs-model label's loader, finder, cell and
#    record. ⛔ Gone with the props model's panel and the record under the
#    board (~~the label cell fbAgHtml and the record fbAgRecordHtml stay~~).
GONE_AG = ("FBAG", "fbAgLoad", "fbAgFind", "fbAgHtml", "fbAgRecordHtml")
GONE = GONE_FLAGS + GONE_AG


def _code(s):
    """`s` with its JavaScript comments removed. ⛔ The page STRIKES removed
    code in a comment (~~like this~~), so an absence asked of the raw text
    would fire on correct code; it is asked of what runs."""
    nb = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return "\n".join(ln for ln in nb.splitlines() if not ln.strip().startswith("//"))


SRC = source(PAGE)
CODE = _code(SRC)
ck(len(CODE) < len(SRC) and "function fbFlagsRecordHtml(" in CODE and "async function fbPicks(" in CODE,
   "⚠️ the comment stripper removed comments and kept the code (if this fails every absence below "
   "is reading prose)", "%d -> %d chars" % (len(SRC), len(CODE)))

FL = {"sources": ["headlines"], "college_note": "College football has no public injury reports we may use.",
      "flags": [{"key": "k1", "kind": "player", "subject": "Jonnu Smith", "game_id": "g1", "source": "headline",
                 "status": "questionable", "headline": "Jonnu Smith questionable", "link": "https://ex.com/a",
                 "first_seen": "2026-09-26T15:00:00Z", "basis": "DESCRIPTIVE"}],
      "record": {"absence": {"graded": 4, "did_not_play": 3, "played": 1, "right_pct": 75.0},
                 "caution": {"graded": 2, "did_not_play": 0, "played": 2}}}

# `[Sam, 2026-10-17]` ~~The label is asked of `fbAgHtml(fbAgFind(...))` --
#    the one place the page still draws it, the props model's "Card vs
#    model" cell.~~ That cell left with its panel, so the driver ASKS whether
#    each of GONE (the row-flag renderers since 2026-10-01, the agreement
#    code since 2026-10-17) is still defined in the shipped slice, and calls
#    the one renderer that stays, the flags' record.
DRIVER = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const a = html.indexOf('const FBFLAGS = {};');   // [Sam, 2026-10-17] ~~const FBAG = {}, FBFLAGS = {};~~
const b = html.indexOf('const WINNERS = {};');   // [Sam, 2026-10-01] ~~const FBGL~~: the Game Lines tab's first line
if (a < 0 || b < 0 || b <= a){ console.error('CODE_NOT_FOUND'); process.exit(2); }
const esc = v => String(v == null ? '' : v).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const d = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const fn = new Function('fbEsc', 'jget', 'LG_DATA', 'LEAGUE', html.slice(a, b) +
  '\nreturn {fbFlagsRecordHtml, defined: {' +
  d.gone.map(n => n + ": typeof " + n + " !== 'undefined'").join(', ') + '}};');
const M = fn(esc, async () => null, {nfl: 'data/nfl'}, 'nfl');
process.stdout.write(JSON.stringify({flrec: M.fbFlagsRecordHtml(d.fl), defined: M.defined}));
"""
tmp = tempfile.mkdtemp(prefix="agpage-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"fl": FL, "gone": list(GONE)}, open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), PAGE, os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=300)
    ck(r.returncode == 0, "⚠️ the shipped helpers ran in node", (r.stderr or "")[-300:])
    R = json.loads(r.stdout) if r.returncode == 0 else {"flrec": "", "defined": {}}
finally:
    shutil.rmtree(tmp, ignore_errors=True)
DEF = R["defined"] or {}
_blocks = top_level_blocks(PAGE)

section("1. NO CARD-VS-MODEL LABEL ANYWHERE ON THE PAGE")
# `[Sam, 2026-10-01]` These USED TO REQUIRE the label to wear Descriptive,
#    the card's % its own basis (Record), the model's % Model and the
#    break-even Market; then the label and all three numbers with NO tag.
#    `[Sam, 2026-10-17]` The label's only place, the props model's "Card vs
#    model" cell, left with its panel ("as simple as the mlb gizmos picks"),
#    so they now require the label's code to be GONE. The data keeps every
#    label, `card_basis` and break-even (fb_agreement.py).
_ag_left = sorted(k for k in GONE_AG if DEF.get(k))
ck(set(GONE_AG) <= set(DEF) and not _ag_left,
   "🔴🔴 [Sam, 2026-10-17] no row draws the card-vs-model label: FBAG, fbAgLoad, fbAgFind, fbAgHtml and "
   "fbAgRecordHtml are gone from the shipped code (~~the label and all three numbers, card 72%, props model "
   "35.1%, break-even 41.7%, with [Sam, 2026-10-01] no tag on any of them~~)",
   "asked %d of %d; still defined: %r" % (len(set(GONE_AG) & set(DEF)), len(GONE_AG), _ag_left))
_ag_live = [g for g in GONE_AG if g in _blocks or calls(g, PAGE)]
ck(not _ag_live and not re.search(r"\bFBAG\b", CODE) and not re.search(r">\s*Card vs (?:props )?model\b", CODE),
   "   ✅ [Sam, 2026-10-17] and none of it is defined, called or read anywhere on the page, and no "
   "'Card vs model' cell is drawn (~~the props model's own pick row finds the same label~~: that row "
   "left with its panel)",
   "still there: %r" % (_ag_live + re.findall(r"\bFBAG\b|>\s*Card vs (?:props )?model\b", CODE)))
# `[Sam, 2026-10-01]` These used to require: a row with no label draws
#    nothing; a started game's row reads its FROZEN label (AGREE, with the
#    numbers it was frozen with) and no 'frozen before kickoff' note; a
#    started row never frozen draws nothing, never a fresh ONE SOURCE.
#    `[Sam, 2026-10-17]` No row draws a label at all now, frozen or not, so
#    they require that the page loads nothing from agreement.json and that
#    no label span is drawn. fb_agreement.settle still freezes each label
#    before kickoff and the ledger grades the frozen one.
_trace = re.findall(r"\bagreement\.json|class=[\"']agl\b", CODE)
ck(not _trace,
   "🔴 [Sam, 2026-10-17] the page loads nothing from agreement.json and draws no label span on any row "
   "(~~a row with no label draws nothing; a started game's row reads its FROZEN label, AGREE, with no "
   "'frozen before kickoff' note; a started row never frozen draws nothing, never ONE SOURCE~~)",
   "found: %r" % _trace)

section("2. NO NEWS FLAG ON ANY ROW; NO RECORD BY LABEL; THE FLAGS' RECORD KEEPS ITS NUMBERS")
# `[Sam, 2026-10-01]` "no per-row flag". This USED TO REQUIRE the flag on
#    the row -- its status, the headline with its link, first_seen and
#    Descriptive. It now requires every row-flag renderer to be GONE from
#    the shipped code. news_flags_fb.py still writes every flag, and the
#    News tab keeps their record (below).
_left = sorted(k for k in GONE_FLAGS if DEF.get(k))
ck(set(GONE_FLAGS) <= set(DEF) and not _left,
   "🔴 [Sam, 2026-10-01] no row draws a news flag: fbRowNotes, fbFlagOne, fbFlagHtml, fbFlagsFor and "
   "fbParlayFlagsHtml are gone from the shipped code (a row used to show the flag's status, headline "
   "link, first seen and Descriptive)",
   "asked %d of %d; still defined: %r" % (len(set(GONE_FLAGS) & set(DEF)), len(GONE_FLAGS), _left))
# `[Sam, 2026-10-01]` This USED TO REQUIRE the agreement record's
#    explanation (the pre-registered question's state, "changes no pick"),
#    then its counts by label without it. `[Sam, 2026-10-17]` The record by
#    label left Gizmo's Picks with everything below the board, so it now
#    requires that no tab draws it. agreement.json keeps the counts and the
#    graded record (fb_agreement.py, test_fb_agreement.py).
_rec = [n for n in ("fbAgRecordHtml",) if DEF.get(n) or n in _blocks or calls(n, PAGE)] \
    + re.findall(r"do they agree\?|<h2>\s*Card vs props model", CODE)
ck(not _rec,
   "🔴 [Sam, 2026-10-17] no tab draws the record by label: no fbAgRecordHtml and no 'Card vs props model "
   "-- do they agree?' panel (~~the agreement record still shows its counts by label, 14 / 11 / 1, and "
   "[Sam, 2026-10-01] no longer the pre-registered question's state, the 'changes no pick' sentence or "
   "a tag~~)",
   "still there: %r" % _rec)
# `[Sam, 2026-10-01]` This USED TO REQUIRE the flags' record explanation:
#    the sources sentence and college's "headlines only" note. Explanations
#    are gone from every tab; the table stays (News).
ck("75%" in R["flrec"] and "no public injury reports" not in R["flrec"]
   and "A flag is a note" not in R["flrec"] and not TAG.search(R["flrec"]),
   "   ✅ the flags' record still shows how often they were right (75%), and [Sam, 2026-10-01] no longer "
   "its explanation, college's 'no public injury reports' note or a tag",
   R["flrec"][:300])

section("3. WIRED WHERE THE ROWS ARE -- AND NO FLAG OR LABEL WIRED ANYWHERE")
# `[Sam, 2026-10-01]` This USED TO REQUIRE `fbRowNotes(p, AG, FL)` under
#    every card row on Gizmo's Picks. Each card row is now the pick card
#    alone. ~~the record by label stays under the board~~ `[Sam, 2026-10-17]`
#    nothing of the agreement is under it (the MLB tab's shape: the picks,
#    then the top plays).
_pk = js_block("fbPicks", PAGE)
ck("kept.forEach(p => host.append(pickCard(p)));" in _pk and not re.search(r"fbRowNotes|fbAgHtml|fbFlag", _pk)
   and not re.search(r"\bfbAg\w*|\bFBAG\b|agreement", _code(_pk)),
   "🔴 [Sam, 2026-10-01] a card row on Gizmo's Picks gets NO notes line (it used to get its label and "
   "news flags under it), and [Sam, 2026-10-17] the tab loads and draws nothing of the agreement under "
   "the board (~~the tab still shows the record by label~~)",
   "fbPicks reaches: %r" % re.findall(r"fbRowNotes|fbFlag\w*|\bfbAg\w*|\bFBAG\b|agreement", _code(_pk)))
# `[Sam, 2026-10-01]` This USED TO REQUIRE flags on props rows, on card
#    parlay legs and on Game Lines games. It now requires that none of those
#    three tabs reaches any flag code; the flags' record stays on News.
#    `[Sam, 2026-10-17]` ~~and the label still reaches the props model's
#    picks~~: that list left the page, so no function on it reaches the
#    label's code.
_flagged = {t: re.findall(r"fbFlag\w*|\w*FlagsHtml|fbRowNotes", js_block(t, PAGE))
            for t in ("fbProps", "fbParlays", "fbGameLinesTab")}
_ag_users = sorted(n for n, b in _blocks.items() if re.search(r"\bfbAg\w*|\bFBAG\b", _code(b)))
ck(not any(_flagged.values())
   and "fbFlagsRecordHtml(" in js_block("fbNews", PAGE)
   and not _ag_users,
   "🔴 [Sam, 2026-10-01] NO flag reaches props rows, card parlay legs or Game Lines games any more; the "
   "flags' record stays on News; and [Sam, 2026-10-17] no function on the page reaches the label's code "
   "(~~the label still reaches the model's picks~~)",
   "flag code left: %r; label code reached by: %r" % ({k: v for k, v in _flagged.items() if v}, _ag_users))
# `[Sam, 2026-10-01]` This USED TO REQUIRE that fbFlagOne was called, not
#    merely defined. Now no row-flag renderer -- and `[Sam, 2026-10-17]` no
#    agreement function -- may be defined OR called anywhere on the page.
_live = [g for g in GONE if g in _blocks or calls(g, PAGE)]
ck(not _live,
   "   ✅ [Sam, 2026-10-01] and the flag renderers -- [Sam, 2026-10-17] and the agreement code -- are "
   "neither defined nor called anywhere on the page",
   "still there: %r" % _live)
