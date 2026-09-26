#!/usr/bin/env python3
"""test_agree_flags_page.py — the agreement label and the news flags are
DRAWN on the rows, with the right basis on every number, by the SHIPPED
page code (sliced out of `index.html` and run in node).

# @vacuity the break-even beside the label wears Market
#   file: index.html
#   find:     &middot; break-even ${pct(r.break_even)} <span class="kind k-market">Market</span></span>`;
#   with:     &middot; break-even ${pct(r.break_even)}</span>`;
#
# @vacuity every card row on Gizmo's Picks gets its notes line
#   file: index.html
#   find:   kept.forEach(p => { host.append(pickCard(p)); host.insertAdjacentHTML('beforeend', fbRowNotes(p, AG, FL)); });
#   with:   kept.forEach(p => host.append(pickCard(p)));
#
# @vacuity a started game's row says its label was frozen before kickoff
#   file: index.html
#   find:       ? ' <span class="rec">frozen before kickoff</span>' : ''}
#   with:       ? '' : ''}
"""
import json
import os
import re
import shutil
import subprocess
import tempfile

from jsblock import calls, js_block
from tcheck import ck, section

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, "index.html")

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

DRIVER = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const a = html.indexOf('const FBAG = {}, FBFLAGS = {};');
const b = html.indexOf('const FBGL = {}, FBGLREC = {};');
if (a < 0 || b < 0 || b <= a){ console.error('CODE_NOT_FOUND'); process.exit(2); }
const esc = v => String(v == null ? '' : v).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const fn = new Function('fbEsc', 'jget', 'LG_DATA', 'LEAGUE', html.slice(a, b) +
  '\nreturn {fbRowNotes, fbAgHtml, fbAgFind, fbAgRecordHtml, fbFlagsRecordHtml};');
const M = fn(esc, async () => null, {nfl: 'data/nfl'}, 'nfl');
const d = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
process.stdout.write(JSON.stringify({
  notes: M.fbRowNotes(d.row, d.ag, d.fl),
  model_pick: M.fbAgHtml(M.fbAgFind(d.ag, d.mp)),
  none: M.fbRowNotes(Object.assign({}, d.row, {player: 'Nobody'}), d.ag, d.fl),
  frozen: M.fbRowNotes({game_id: 'g2', player: 'Frozen Guy', market: 'player_rush_yds', side: 'over', line: 50.5}, d.ag, d.fl),
  unfrozen: M.fbRowNotes({game_id: 'g3', player: 'Unfrozen Guy', market: 'player_rush_yds', side: 'over', line: 40.5}, d.ag, d.fl),
  agrec: M.fbAgRecordHtml(d.ag), flrec: M.fbFlagsRecordHtml(d.fl)}));
"""
tmp = tempfile.mkdtemp(prefix="agpage-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"row": ROW, "mp": MODEL_PICK, "ag": AG, "fl": FL}, open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), PAGE, os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=300)
    ck(r.returncode == 0, "⚠️ the shipped helpers ran in node", (r.stderr or "")[-300:])
    R = json.loads(r.stdout) if r.returncode == 0 else {k: "" for k in ("notes", "model_pick", "none", "agrec", "flrec",
                                                                        "frozen", "unfrozen")}
finally:
    shutil.rmtree(tmp, ignore_errors=True)

section("1. THE LABEL AND BOTH NUMBERS, EACH WITH ITS BASIS")
n = R["notes"]
ck(re.search(r'<span class="kind k-desc">SPLIT</span>', n)
   and re.search(r'card 72% <span class="kind k-desc">Record</span>', n)
   and re.search(r'props model 35\.1% <span class="kind k-model">Model</span>', n)
   and re.search(r'break-even 41\.7% <span class="kind k-market">Market</span>', n),
   "🔴🔴 on the row: the label (Descriptive), the card's % (its own basis, Record), the model's % (Model), "
   "the break-even (Market)")
ck("SPLIT" in R["model_pick"], "   ✅ the props model's own pick row finds the same label (its line is wrapped)")
ck(R["none"] == "", "   ✅ a row with no label and no flag draws nothing")

ck('<span class="kind k-desc">AGREE</span> <span class="rec">frozen before kickoff</span>' in R["frozen"]
   and "props model 61% " in R["frozen"],
   "🔴🔴 a started game's row reads its FROZEN label — AGREE, 'frozen before kickoff' — with the numbers it was frozen with",
   R["frozen"][:300])
ck("no label was frozen before kickoff" in R["unfrozen"] and "ONE SOURCE" not in R["unfrozen"]
   and "k-desc\">Descriptive" in R["unfrozen"],
   "🔴 a started row never frozen says so, and never reads ONE SOURCE", R["unfrozen"][:300])

section("2. THE FLAG, DESCRIPTIVE, WITH ITS SOURCE, LINK AND FIRST SEEN")
ck('&#9873; <b>questionable</b>' in n and 'href="https://ex.com/a"' in n and "Jonnu Smith questionable" in n
   and 'title="first seen 2026-09-26T15:00:00Z"' in n and 'k-desc">Descriptive</span>' in n,
   "🔴 the flag shows its status, the headline with its link, first_seen, and Descriptive")
ck("NOT YET MEASURABLE" in R["agrec"] and "changes no" in R["agrec"],
   "   ✅ the agreement record shows the pre-registered question's state and that it changes nothing")
ck("75%" in R["flrec"] and "no public injury reports" in R["flrec"],
   "   ✅ the flags' record shows how often they were right, and college says it is headlines only")

section("3. WIRED WHERE THE ROWS ARE")
ck("fbRowNotes(p, AG, FL)" in js_block("fbPicks", PAGE) and "fbAgRecordHtml(AG)" in js_block("fbPicks", PAGE),
   "🔴 every card row on Gizmo's Picks gets its notes, and the tab shows the record by label")
ck("fbFlagsFor(FL, 'player', p.player, g.id)" in js_block("fbProps", PAGE)
   and "fbParlayFlagsHtml(FL, 'card', PL)" in js_block("fbParlays", PAGE)
   and "fbFlagsFor(FLG, 'team'" in js_block("fbGameLinesTab", PAGE)
   and "fbFlagsRecordHtml(" in js_block("fbNews", PAGE)
   and "fbAgFind(FBAG[LEAGUE], p)" in js_block("fbPropModelHtml", PAGE),
   "🔴 flags reach props rows, card parlay legs and Game Lines games; the label reaches the model's picks")
ck(calls("fbFlagOne", PAGE) >= 1 and "map(fbFlagOne)" in js_block("fbFlagHtml", PAGE),
   "   ✅ the flag renderer is called, not merely defined")
