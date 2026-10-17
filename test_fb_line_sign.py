#!/usr/bin/env python3
r"""test_fb_line_sign.py — a model pick's spread prints as the TEAM'S OWN point, signed.

`[2026-10-16]` An independent recheck of the rebuilt cards found the football "Model
picks" table and "What the model showed, graded" printing every HOME spread pick with
the wrong sign: fb_model stores a spread pick's `line` as the threshold on the home
margin (M = -home point), and the page printed it raw beside the team — "Cleveland
Browns -3.5" for Cleveland +3.5 (a +180 underdog), "Kansas City Chiefs 8.5" for KC
-8.5; 7 NFL and 26 college picks that day. The card itself was right
(card_fb.model_game_rows flips it). The class: a stored line printed raw. ~~The SHIPPED
page code runs in node on planted picks (fbPointText, fbModelHtml, fbLedgerHtml,
fbPropModelHtml); and no code in index.html outside fbPointText may print a stored
`line.value` raw again.~~

`[Sam, 2026-10-17]` "lose everything in the gizmos picks tab after the model picks
gamelines tab, so this means to lose its record, week by week, on games it had not seen
and everything below that. it should be as simple as the mlb gizmos picks": the Model
picks, Prop model picks and "What the model showed, graded" panels left the page, and
with them fbPointText, the one place a stored model line was turned into a team's own
point on the page. fb-model.json, fb-props-model.json and model-ledger.json are still
built and graded; only the page stopped drawing them. So the guard now asks:
  1. the panels and their line printer are GONE (page source and js_block results);
  2. the one road a model spread still takes to the page is the card's game lines:
     card_fb.model_game_rows turns fb-model.json's M (on the HOME margin) into the
     team's own point (-M for a home pick, M for an away pick), and the page's own
     fbGameLines -> pickCard prints it signed, a total unsigned — run in node;
  3. the class, with no exception left: index.html prints no stored `x.line.value`
     and no `labN(x.line)` ANYWHERE (~~outside fbPointText~~).
⛔ Reads no live data.

# @vacuity 🔴 a HOME spread pick's own point is -M, an AWAY pick's is M (the card)
#   file: card_fb.py
#   find: line = -line if p.get("side") == "home" else line   # the team's own point
#   with: line = -line if p.get("side") == "away" else line   # the team's own point
# `[2026-10-17]` ~~find: `const pt = p.side === 'home' ? -v : v;`~~ -- fbPointText left the
#   page with the model panels (Sam); the flip lives only in the card now, same intent.
#
# @vacuity 🔴 a spread point carries its sign ("+3.5", never a bare "3.5")
#   file: index.html
#   find:     : ` ${gl && /spread|run_line/.test(p.market) && p.line > 0 ? '+' : ''}${p.line}`;
#   with:     : ` ${p.line}`;
# `[2026-10-17]` ~~find: `return (pt > 0 ? '+' : '') + String(pt === 0 ? 0 : pt);`~~ --
#   fbPointText is gone; pickCard is what signs a card game-line row's point now.
#
# @vacuity 🔴 a total prints its line as stored, unsigned
#   file: index.html
#   find:     : ` ${gl && /spread|run_line/.test(p.market) && p.line > 0 ? '+' : ''}${p.line}`;
#   with:     : ` ${gl && p.line > 0 ? '+' : ''}${p.line}`;
# `[2026-10-17]` ~~find: `if (!/spread/.test(String(p.market || ''))) return String(v);`~~ --
#   fbPointText is gone; pickCard's market test is what keeps a total unsigned.
#
# @vacuity 🔴 the Model picks panels are never appended to Gizmo's Picks again
#   file: index.html
#   find:   const t = $('#fb-pk-started');
#   with:   const t = $('#fb-pk-started'); await fbModelAppend(v, LEAGUE);
# `[2026-10-17]` ~~find: `<td>${fbPointText(p) ?? ''}</td>` (Model picks prints through
#   fbPointText)~~ -- Sam removed the panel; the question is now that it stays removed.
#
# @vacuity 🔴 the ledger's line printer does not come back (and would print M raw)
#   file: index.html
#   find: const FBFLAGS = {};
#   with: const FBFLAGS = {}; const fbLedgerPoint = p => p.line && p.line.value != null ? ' ' + p.line.value : '';
# `[2026-10-17]` ~~find: `const fbLedgerPoint = p => fbPointText(p) != null ? ...`~~ -- the
#   ledger panel and its helper left the page (Sam); the question is now that they stay gone.
#
# @vacuity 🔴 fbPointText does not come back as a page function
#   file: index.html
#   find: function fbTopPlays(C, shownPicks){
#   with: function fbPointText(p){ return p && p.line ? String(p.line) : null; } function fbTopPlays(C, shownPicks){
#
# @vacuity 🔴 a removed panel's heading is not drawn again
#   file: index.html
#   find: <h2>Top ${t.length} play${t.length === 1 ? '' : 's'} of the day</h2>
#   with: <h2>Model picks</h2><h2>Top ${t.length} play${t.length === 1 ? '' : 's'} of the day</h2>
#
# @vacuity 🔴 THE CLASS: a stored line printed raw anywhere on the page goes red
#   file: index.html
#   find:           ${x.line == null ? '' : x.line} ${x.market_label || ''}
#   with:           ${x.line == null ? '' : labN(x.line)} ${x.market_label || ''}
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
import card_fb  # noqa: E402
import jsblock  # noqa: E402
from tcheck import ck, eq, section, shown  # noqa: E402

IDX = os.path.join(ROOT, "index.html")
SRC = open(IDX, encoding="utf-8").read()

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE MODEL PANELS AND THEIR LINE PRINTER ARE GONE `[Sam, 2026-10-17]`")
# ══════════════════════════════════════════════════════════════════════
# `[Sam, 2026-10-17]` "it should be as simple as the mlb gizmos picks". ~~The page draws
# Model picks, Prop model picks and the ledger, each line through fbPointText~~.
GONE_FUNCS = ["fbPointText", "fbModelHtml", "fbPropModelHtml", "fbLedgerHtml", "fbVerdictTag",
              "fbModelAppend", "fbModelLoad", "fbPropModelLoad", "fbLedgerLoad"]
GONE_NAMES = GONE_FUNCS + ["fbLedgerPoint", "FBMODEL", "FBPROPMODEL", "FBLEDGER"]
_top = jsblock.top_level_blocks(IDX)
eq(sorted(n for n in GONE_FUNCS if n in _top), [],
   "🔴 no model-panel function is on the page any more (~~fbPointText, fbModelHtml, "
   "fbPropModelHtml, fbLedgerHtml, fbVerdictTag, fbModelAppend and their loaders~~)")
# ⚠️ CODE-SHAPED, NOT A BARE NAME: the page's own comment records the removal by name
#    ("panels (fbModelAppend)~~ left the page"), and a check reddening on that comment would
#    be the guard that fires on correct code. A definition, a call, or an index is code.
_code = {n: [m.group(0) for m in re.finditer(
    r"(?:\b(?:function|const|let|var)\s+|,\s*)%s\b|\b%s\s*[(\[]" % (n, n), SRC)] for n in GONE_NAMES}
eq({n: v for n, v in _code.items() if v}, {},
   "🔴 ...and none is defined, called or read anywhere in index.html (fbLedgerPoint and the "
   "FBMODEL / FBPROPMODEL / FBLEDGER caches included)")
_heads = ["<h2>Model picks</h2>", "<h2>Prop model picks</h2>", "<h2>What the model showed, graded</h2>",
          ">Its record, week by week, on games it had not seen</h3>"]
eq([h for h in _heads if h in SRC], [],
   "🔴 no panel heading Sam removed is drawn: Model picks, Prop model picks, \"What the model "
   "showed, graded\", \"Its record, week by week, on games it had not seen\"")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE ONE ROAD LEFT: THE CARD'S GAME LINES, AT THE TEAM'S OWN POINT, SIGNED")
# ══════════════════════════════════════════════════════════════════════
# fb-model.json's convention, unchanged: a spread pick's `line` is M, the threshold on the
# HOME margin (M = -home point), so a HOME pick's own point is -M and an AWAY pick's is M.
SLATE = "2026-10-18"
KO = SLATE + "T17:00:00Z"


def L(v):
    return {"value": v, "basis": "MARKET"}


def gm(game, team, side, market, line):
    return {"game": game, "commence": KO, "market": market, "team": team, "side": side,
            "line": L(line) if line is not None else None, "price": L(-110), "book": "fd",
            "model_probability": {"value": 60.0, "basis": "MODEL"},
            "break_even": {"value": 52.4, "basis": "MARKET"}}


G1, G2 = "Pittsburgh Steelers at Cleveland Browns", "Denver Broncos at Kansas City Chiefs"
G3, G4 = "Houston Texans at Tennessee Titans", "Las Vegas Raiders at Los Angeles Chargers"
G5, G6 = "Buffalo Bills at Miami Dolphins", "Dallas Cowboys at New York Giants"
PICKS = [gm(G1, "Cleveland Browns", "home", "spread", -3.5), gm(G2, "Kansas City Chiefs", "home", "spread", 8.5),
         gm(G3, "Houston Texans", "away", "spread", 2.5), gm(G4, "Las Vegas Raiders", "away", "spread", -4.5),
         gm(G5, "Over", "over", "total", 53.5), gm(G6, "New York Giants", "home", "moneyline", None)]
GAMES = [{"away": g.partition(" at ")[0], "home": g.partition(" at ")[2], "id": "g%d" % i}
         for i, g in enumerate([G1, G2, G3, G4, G5, G6], 1)]
ROWS = card_fb.model_game_rows(PICKS, GAMES, SLATE)
eq([(r["player"], r["market"], r["line"]) for r in ROWS],
   [("Cleveland Browns", "spread", 3.5), ("Kansas City Chiefs", "spread", -8.5),
    ("Houston Texans", "spread", 2.5), ("Las Vegas Raiders", "spread", -4.5),
    ("Over", "total", 53.5), ("New York Giants", "moneyline", None)],
   "🔴 DATA: the card turns M into the team's own point (Cleveland M -3.5 -> +3.5, Kansas City "
   "M 8.5 -> -8.5), away picks keep theirs, a total as stored, a moneyline has none")

_el = next((l for l in SRC.splitlines() if l.startswith("const el = ")), "")
ck(bool(_el), "⚠️ the page's element helper was found", "")
DRIVER = r"""
const S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const text = n => '<' + (n.className || '') + '>' + (n.innerHTML || '') + ' '
  + (n.kids || []).map(text).join(' ');
function node(){ return {className: '', innerHTML: '', kids: [],
  append(...k){ this.kids.push(...k); }, insertAdjacentHTML(_, h){ this.kids.push({innerHTML: h}); },
  get outerHTML(){ return text(this); } }; }
const document = {createElement: () => node()};
const stub = () => '';
const fn = new Function('document', 'confClass', 'headUrl', 'projChip', 'mark', 'ab', 'sgn',
  'bookChip', 'betControl', 'betLink', 'fbMark', 'fbAb', 'FBTEAMS', 'LEAGUE',
  S.el + '\n' + S.dn + '\n' + S.pc + '\n' + S.gl + '\n' + S.ed + '\nreturn fbGameLines;');
const fbGameLines = fn(document, stub, stub, stub, stub, stub, x => (x > 0 ? '+' : '') + x,
  stub, stub, stub, stub, stub, {}, 'nfl');
process.stdout.write(JSON.stringify(fbGameLines(S.card).replace(/\s+/g, ' ')));
"""
tmp = tempfile.mkdtemp(prefix="linesign-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"el": _el, "dn": jsblock.js_block("fbDayName", IDX), "pc": jsblock.js_block("pickCard", IDX),
               "gl": jsblock.js_block("fbGameLines", IDX), "ed": jsblock.js_block("fbEdgeLine", IDX),
               "card": {"game_lines": ROWS, "game_lines_meta": {"slate": SLATE}}},
              open(os.path.join(tmp, "d.json"), "w", encoding="utf-8"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
ck(r.returncode == 0, "⚠️ the page's own code ran in node", shown((r.stderr or "")[-400:]))
HTML = json.loads(r.stdout) if r.returncode == 0 else ""
_want = ["Cleveland Browns +3.5 Spread", "Kansas City Chiefs -8.5 Spread", "Houston Texans +2.5 Spread",
         "Las Vegas Raiders -4.5 Spread", "Over 53.5 Total", "New York Giants Moneyline"]
eq([w for w in _want if w not in HTML], [],
   "🔴 PAGE: Gizmo's Picks' game lines print each spread at the team's own point, signed, "
   "a total as stored and a moneyline with no line (fbGameLines -> pickCard)")
_never = ["Cleveland Browns -3.5", "Kansas City Chiefs 8.5", "Houston Texans 2.5 ", "Over +53.5"]
eq([w for w in _never if w in HTML], [],
   "🔴 ...never the stored M (Cleveland -3.5, Kansas City 8.5), never a bare unsigned spread, "
   "never a signed total")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE CLASS: NO STORED LINE PRINTED RAW ANYWHERE ON THE PAGE")
# ══════════════════════════════════════════════════════════════════════
# ~~outside fbPointText~~ `[2026-10-17]` fbPointText is gone (Sam), so nothing is excused:
# the whole page. `.line?.value` and a labN over any `<expr>.line` count too.
raw = [m.group(0) for m in re.finditer(
    r"labN\(\s*[\w$.\[\]'\"]+\.line\s*[,)]|\.line\s*\??\.\s*value\b", SRC)]
eq(raw, [], "🔴 index.html prints no `x.line.value` and no `labN(x.line)` anywhere "
            "(~~outside fbPointText~~; a stored model line printed raw is how the wrong sign shipped)")
