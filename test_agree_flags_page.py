#!/usr/bin/env python3
"""test_agree_flags_page.py — the agreement label and the news flags, as the
SHIPPED page code draws them (sliced out of `index.html` and run in node).

`[Sam, 2026-10-01]` *"i just want what's supposed to be in each tab to be in
each tab"*: no tag, no per-row flag, no explanation on any tab. This file
USED TO REQUIRE the label and every news flag on the rows, each number
wearing its basis (Descriptive / Record / Model / Market). It now requires
the label and its numbers with NO tag, NO news flag on any row, and the two
records' tables without their explanations. ⛔ `fb_agreement.py` and
`news_flags_fb.py` still write every label, basis and flag; this file asks
only what is DRAWN.

# @vacuity [Sam, 2026-10-01] the label's numbers wear no tag (the break-even used to wear Market)
#   file: index.html
#   find:     &middot; break-even ${pct(r.break_even)}</span>`;
#   with:     &middot; break-even ${pct(r.break_even)} <span class="kind k-market">Market</span></span>`;
#
# @vacuity [Sam, 2026-10-01] a card row on Gizmo's Picks gets no notes line under it
#   file: index.html
#   find:   kept.forEach(p => host.append(pickCard(p)));
#   with:   kept.forEach(p => { host.append(pickCard(p)); host.insertAdjacentHTML('beforeend', fbRowNotes(p, AG, FL)); });
#
# @vacuity [Sam, 2026-10-01] a started game's row no longer says 'frozen before kickoff'
#   file: index.html
#   find:   return `<span class="agl"><b>${r.label}</b>
#   with:   return `<span class="agl"><b>${r.label}</b>${r.frozen_before_kickoff ? ' <span class="rec">frozen before kickoff</span>' : ''}
#
# @vacuity [Sam, 2026-10-01] a started row never frozen draws nothing, not its label_note
#   file: index.html
#   find:   if (!r || !r.label) return '';
#   with:   if (!r || !r.label) return (r && r.label_note) ? `<span class="agl">${fbEsc(r.label_note)}</span>` : '';
#
# @vacuity a row with no label draws nothing
#   file: index.html
#   find:   if (!r || !r.label) return '';
#   with:   if (!r || !r.label) return '<span class="agl"></span>';
#
# @vacuity [Sam, 2026-10-01] no row-flag renderer is left in the shipped code
#   file: index.html
#   find:   function fbAgRecordHtml(AG){
#   with:   function fbFlagOne(f){ return '<span class="fbflag">' + f.status + '</span>'; } function fbAgRecordHtml(AG){
#
# @vacuity [Sam, 2026-10-01] the agreement record carries no explanation paragraph
#   file: index.html
#   find:   <th>Break-even</th><th>Games (eff. n)</th></tr>${rows}</table></div></div>`;
#   with:   <th>Break-even</th><th>Games (eff. n)</th></tr>${rows}</table></div><p>Pre-registered question: <b>${(AG.question || {}).state}</b>. ${(AG.question || {}).consequence}</p></div>`;
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

from jsblock import calls, js_block, top_level_blocks
from tcheck import ck, section

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, "index.html")

# `[Sam, 2026-10-01]` ANY tag, whatever its quotes or its kind: the class
#    `kind` and every `k-<basis>` the page used to print beside a number.
TAG = re.compile(r"""class=["'][^"']*\bkind\b|\bk-(?:model|market|desc|live|record)\b""")
# The renderers that drew a note or a news flag ON A ROW. ⛔ Gone since
#    2026-10-01; the records' own tables (fbAgRecordHtml, fbFlagsRecordHtml)
#    and the label cell (fbAgHtml) stay.
GONE = ("fbRowNotes", "fbFlagOne", "fbFlagHtml", "fbFlagsFor", "fbParlayFlagsHtml")

AG = {"rows": [{"game_id": "g1", "player": "Jonnu Smith", "market": "player_receptions", "side": "over",
                "line": 1.5, "card_p": 72, "card_basis": "RECORD", "model_p": 35.1, "break_even": 41.7,
                "label": "SPLIT"},
               # `[2026-09-26]` a started game: its label frozen before kickoff
               {"game_id": "g2", "player": "Frozen Guy", "market": "player_rush_yds", "side": "over",
                "line": 50.5, "card_p": 70, "card_basis": "RECORD", "model_p": 61.0, "break_even": 52.4,
                "label": "AGREE", "frozen_before_kickoff": True, "frozen_at": "2026-09-26T15:00:00Z"},
               # ...and a started row never frozen
               {"game_id": "g3", "player": "Unfrozen Guy", "market": "player_rush_yds", "side": "over",
                "line": 40.5, "card_p": 60, "card_basis": "RECORD", "model_p": None, "break_even": 52.4,
                "label": None, "frozen_before_kickoff": False,
                "label_note": "no label was frozen before kickoff"}],
      "counts": {"AGREE": 14, "SPLIT": 11, "ONE SOURCE": 1},
      "record": {"AGREE": {}, "SPLIT": {}, "ONE SOURCE": {}},
      "question": {"state": "NOT YET MEASURABLE", "agree_graded": 0, "split_graded": 0,
                   "min": {"agree": 300, "split": 100}, "consequence": "Nothing changes on its own."}}
FL = {"sources": ["headlines"], "college_note": "College football has no public injury reports we may use.",
      "flags": [{"key": "k1", "kind": "player", "subject": "Jonnu Smith", "game_id": "g1", "source": "headline",
                 "status": "questionable", "headline": "Jonnu Smith questionable", "link": "https://ex.com/a",
                 "first_seen": "2026-09-26T15:00:00Z", "basis": "DESCRIPTIVE"}],
      "record": {"absence": {"graded": 4, "did_not_play": 3, "played": 1, "right_pct": 75.0},
                 "caution": {"graded": 2, "did_not_play": 0, "played": 2}}}
ROW = {"game_id": "g1", "player": "Jonnu Smith", "market": "player_receptions", "side": "over", "line": 1.5}
MODEL_PICK = dict(ROW, line={"value": 1.5, "basis": "MARKET"})

# `[Sam, 2026-10-01]` The label is asked of `fbAgHtml(fbAgFind(...))` -- the
#    one place the page still draws it, the props model's "Card vs model"
#    cell. `fbRowNotes` (label + flags under a card row) is gone, so the
#    driver ASKS whether each of GONE is still defined in the shipped slice
#    instead of calling it.
DRIVER = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const a = html.indexOf('const FBAG = {}, FBFLAGS = {};');
const b = html.indexOf('const FBGL = {}, FBGLREC = {};');
if (a < 0 || b < 0 || b <= a){ console.error('CODE_NOT_FOUND'); process.exit(2); }
const esc = v => String(v == null ? '' : v).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const d = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const fn = new Function('fbEsc', 'jget', 'LG_DATA', 'LEAGUE', html.slice(a, b) +
  '\nreturn {fbAgHtml, fbAgFind, fbAgRecordHtml, fbFlagsRecordHtml, defined: {' +
  d.gone.map(n => n + ": typeof " + n + " !== 'undefined'").join(', ') + '}};');
const M = fn(esc, async () => null, {nfl: 'data/nfl'}, 'nfl');
const lab = p => M.fbAgHtml(M.fbAgFind(d.ag, p));
process.stdout.write(JSON.stringify({
  label: lab(d.row),
  model_pick: lab(d.mp),
  none: lab(Object.assign({}, d.row, {player: 'Nobody'})),
  frozen: lab({game_id: 'g2', player: 'Frozen Guy', market: 'player_rush_yds', side: 'over', line: 50.5}),
  unfrozen: lab({game_id: 'g3', player: 'Unfrozen Guy', market: 'player_rush_yds', side: 'over', line: 40.5}),
  agrec: M.fbAgRecordHtml(d.ag), flrec: M.fbFlagsRecordHtml(d.fl), defined: M.defined}));
"""
tmp = tempfile.mkdtemp(prefix="agpage-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"row": ROW, "mp": MODEL_PICK, "ag": AG, "fl": FL, "gone": list(GONE)},
              open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), PAGE, os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=300)
    ck(r.returncode == 0, "⚠️ the shipped helpers ran in node", (r.stderr or "")[-300:])
    R = json.loads(r.stdout) if r.returncode == 0 else dict(
        {k: "" for k in ("label", "model_pick", "none", "agrec", "flrec", "frozen", "unfrozen")}, defined={})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

section("1. THE LABEL AND ITS NUMBERS, WITH NO TAG ON ANY OF THEM")
# `[Sam, 2026-10-01]` These USED TO REQUIRE the label to wear Descriptive,
#    the card's % its own basis (Record), the model's % Model and the
#    break-even Market. Sam removed every MODEL / MARKET / DESCRIPTIVE /
#    RECORD tag, so they now require the label and all three numbers and NO
#    tag. The data keeps `card_basis` (fb_agreement.py).
n = R["label"]
ck("<b>SPLIT</b>" in n and "card 72%" in n and "props model 35.1%" in n and "break-even 41.7%" in n
   and not TAG.search(n),
   "🔴🔴 on the row: the label and all three numbers (card 72%, props model 35.1%, break-even 41.7%), and "
   "[Sam, 2026-10-01] no tag on any of them -- they used to wear Descriptive / Record / Model / Market",
   n[:300])
ck("SPLIT" in R["model_pick"], "   ✅ the props model's own pick row finds the same label (its line is wrapped)")
ck(R["none"] == "", "   ✅ a row with no label draws nothing")

# `[Sam, 2026-10-01]` The label is still the FROZEN one (fb_agreement.settle
#    writes it, the page prints it). The 'frozen before kickoff' note beside
#    it used to be required; like every note on the page it is now absent.
ck("<b>AGREE</b>" in R["frozen"] and "props model 61%" in R["frozen"]
   and "frozen before kickoff" not in R["frozen"] and not TAG.search(R["frozen"]),
   "🔴🔴 a started game's row reads its FROZEN label -- AGREE -- with the numbers it was frozen with, and "
   "[Sam, 2026-10-01] no 'frozen before kickoff' note or tag beside it",
   R["frozen"][:300])
# `[Sam, 2026-10-01]` This used to require the row's own note ("no label was
#    frozen before kickoff", Descriptive). The note is gone; the row draws
#    NOTHING -- which still means never a fresh ONE SOURCE.
ck(R["unfrozen"] == "",
   "🔴 a started row never frozen draws nothing -- never ONE SOURCE -- and [Sam, 2026-10-01] no longer "
   "its 'no label was frozen before kickoff' note",
   R["unfrozen"][:300])

section("2. NO NEWS FLAG ON ANY ROW; THE TWO RECORDS KEEP THEIR NUMBERS")
# `[Sam, 2026-10-01]` "no per-row flag". This USED TO REQUIRE the flag on
#    the row -- its status, the headline with its link, first_seen and
#    Descriptive. It now requires every row-flag renderer to be GONE from
#    the shipped code. news_flags_fb.py still writes every flag, and the
#    News tab keeps their record (section 3).
_left = sorted(k for k, v in (R["defined"] or {}).items() if v)
ck(len(R["defined"] or {}) == len(GONE) and not _left,
   "🔴 [Sam, 2026-10-01] no row draws a news flag: fbRowNotes, fbFlagOne, fbFlagHtml, fbFlagsFor and "
   "fbParlayFlagsHtml are gone from the shipped code (a row used to show the flag's status, headline "
   "link, first seen and Descriptive)",
   "asked %d of %d; still defined: %r" % (len(R["defined"] or {}), len(GONE), _left))
# `[Sam, 2026-10-01]` These USED TO REQUIRE each record's explanation: the
#    pre-registered question's state and "changes no pick" on the agreement
#    record, the sources sentence and college's "headlines only" note on the
#    flags' record. Explanations are gone from every tab; the tables stay.
ck(all("<td><b>%s</b></td><td>%d</td>" % (k, c) in R["agrec"]
       for k, c in (("AGREE", 14), ("SPLIT", 11), ("ONE SOURCE", 1)))
   and "NOT YET MEASURABLE" not in R["agrec"] and "changes no" not in R["agrec"]
   and not TAG.search(R["agrec"]),
   "   ✅ the agreement record still shows its counts by label (14 / 11 / 1), and [Sam, 2026-10-01] no "
   "longer the pre-registered question's state, the 'changes no pick' sentence or a tag",
   R["agrec"][:300])
ck("75%" in R["flrec"] and "no public injury reports" not in R["flrec"]
   and "A flag is a note" not in R["flrec"] and not TAG.search(R["flrec"]),
   "   ✅ the flags' record still shows how often they were right (75%), and [Sam, 2026-10-01] no longer "
   "its explanation, college's 'no public injury reports' note or a tag",
   R["flrec"][:300])

section("3. WIRED WHERE THE ROWS ARE -- AND NO FLAG WIRED ANYWHERE")
# `[Sam, 2026-10-01]` This USED TO REQUIRE `fbRowNotes(p, AG, FL)` under
#    every card row on Gizmo's Picks. Each card row is now the pick card
#    alone; the record by label stays under the board.
_pk = js_block("fbPicks", PAGE)
ck("kept.forEach(p => host.append(pickCard(p)));" in _pk and not re.search(r"fbRowNotes|fbAgHtml|fbFlag", _pk)
   and "fbAgRecordHtml(AG)" in _pk,
   "🔴 [Sam, 2026-10-01] a card row on Gizmo's Picks gets NO notes line (it used to get its label and "
   "news flags under it), and the tab still shows the record by label")
# `[Sam, 2026-10-01]` This USED TO REQUIRE flags on props rows, on card
#    parlay legs and on Game Lines games. It now requires that none of those
#    three tabs reaches any flag code; the flags' record stays on News and
#    the label still reaches the props model's picks.
_flagged = {t: re.findall(r"fbFlag\w*|\w*FlagsHtml|fbRowNotes", js_block(t, PAGE))
            for t in ("fbProps", "fbParlays", "fbGameLinesTab")}
ck(not any(_flagged.values())
   and "fbFlagsRecordHtml(" in js_block("fbNews", PAGE)
   and "fbAgFind(FBAG[LEAGUE], p)" in js_block("fbPropModelHtml", PAGE),
   "🔴 [Sam, 2026-10-01] NO flag reaches props rows, card parlay legs or Game Lines games any more; the "
   "flags' record stays on News and the label still reaches the model's picks",
   "flag code left: %r" % {k: v for k, v in _flagged.items() if v})
# `[Sam, 2026-10-01]` This USED TO REQUIRE that fbFlagOne was called, not
#    merely defined. Now no row-flag renderer may be defined OR called
#    anywhere on the page.
_blocks = top_level_blocks(PAGE)
_live = [g for g in GONE if g in _blocks or calls(g, PAGE)]
ck(not _live,
   "   ✅ [Sam, 2026-10-01] and the flag renderers are neither defined nor called anywhere on the page",
   "still there: %r" % _live)
