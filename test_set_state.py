#!/usr/bin/env python3
r"""
🔴 A SET STATE CONTROL MUST LEAD TO A STATE PICKER, ON EVERY TAB OF EVERY LEAGUE.

Some books run a site per state, so their bet-slip links carry a literal
`{state}` (every Caesars link, plus BetMGM and betPARX). Until the reader
picks a state the page draws SET STATE instead of the link (betControl,
priceCell), and the click calls focusState(), which scrolls to the picker
(`#st`) in the tools row and focuses it.

THE DEFECT, MEASURED 2026-10-18 IN A BROWSER on MLB Gizmo's Picks (card
2026-10-17, 4 SET STATE buttons): the click did NOTHING. `setTools` shows
the picker only on Odds and Player Props, and a hidden select cannot be
scrolled to or focused: after the click `#st` was still `display: none` and
the focus stayed on the page body. Design I made the book the row's bet link
(PR #296) and kept SET STATE for a `{state}` link, on a tab that hides the
picker. And choosing a state redrew only MLB's Odds and Player Props, keyed on
MLB's tab even while a football league was shown, so no other tab's SET STATE
ever turned into a link.

✅ THE FIX: focusState() shows the picker before it scrolls and focuses, on
whatever tab it is called from; stateChosen() redraws the tab being read in
whichever league and leaves the picker where the reader just used it.

WHAT THIS FILE ASKS, OF THE PAGE'S OWN CODE (node, no browser):
  1. THE CLASS: every SET STATE control on the page calls focusState().
  2. focusState() leaves the picker shown and focused after setTools() on
     EVERY tab of EVERY league (the tab list read out of the page, never
     typed here), and setTools() hides it on at least one, so the question
     is a real one.
  3. Choosing a state redraws exactly the tab being read, in every league,
     and the picker stays shown; the picker's change event goes there.
  4. A pick row with a `{state}` link: SET STATE before, and after the
     state is chosen the book link is that bet slip with the state filled in.
⚠️ The real click in a real browser, all three leagues' Gizmo's Picks at a
desktop and a phone width, is test_league_switch.py section 6 (pr-tests'
`render` jobs and browser.yml have Chromium; this runner may not).

# @vacuity 🔴 the picker is shown before it is focused, on every tab of every league
#   file: index.html
#   find:   el.style.display = '';
#   with:   void 0;
#
# @vacuity 🔴 choosing a state redraws the tab being read, in every league
#   file: index.html
#   find:   if (LEAGUE === 'mlb') show(TAB); else renderFootball();
#   with:   if (TAB === 'odds' || TAB === 'props') show(TAB);
#
# @vacuity the picker stays where the reader just used it
#   file: index.html
#   find:   $('#st').style.display = '';
#   with:   void 0;
#
# @vacuity the picker's change event goes to stateChosen
#   file: index.html
#   find:   stSel.addEventListener('change', e => stateChosen(e.target.value));
#   with:   stSel.addEventListener('change', e => { setBetState(e.target.value); const again = {odds: renderOdds, props: renderProps}; if (again[TAB]) again[TAB](); });
#
# @vacuity 🔴 a SET STATE drawn without focusState is caught wherever it is drawn
#   file: index.html
#   find:   if (needsState(v.link)) return `<span class="cell best needs" onclick="focusState()">${body}</span>`;
#   with:   if (needsState(v.link)) return `<span class="cell best needs">${body}</span>`;
#
# @vacuity 🔴 a pick row with a {state} link asks for the state rather than dropping the button
#   file: index.html
#   find:   if (needsState(url)) return `<button class="betbtn needs" onclick="focusState()">SET STATE</button>`;
#   with:   if (needsState(url)) return '';
#
# @vacuity ...and once the state is chosen the book link is that state's bet slip
#   file: index.html
#   find:   return st ? url.replace(/\{state\}/g, st.toLowerCase()) : null;
#   with:   return st ? url : null;
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

from tcheck import ck, note, section  # noqa: E402

import jsblock  # noqa: E402

PAGE = os.path.join(ROOT, "index.html")
SRC = open(PAGE, encoding="utf-8").read()
CODE = jsblock.script_code(PAGE)          # every <script>, comments removed
BLOCKS = jsblock.top_level_blocks(PAGE)


def fn(name):
    try:
        return jsblock.js_block(name, PAGE)
    except AssertionError:
        return ""


def const(name):
    m = re.search(r"\nconst %s = .*?;\r?\n" % re.escape(name), SRC, re.S)
    return m.group(0).strip() if m else ""


def line_of(prefix):
    return next((ln for ln in SRC.splitlines() if ln.startswith(prefix)), "")


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE CLASS: EVERY SET STATE CONTROL CALLS focusState()")
# ⚠️ Asked of the CODE (comments removed), so a struck control in a comment is
#    not a control, and a new one anywhere on the page is asked the same question.
_drawers = sorted(n for n, b in BLOCKS.items()
                  if n != "needsState" and "needsState(" in jsblock.strip_js(b))
_no_focus = [n for n in _drawers
             if 'onclick="focusState()"' not in jsblock.strip_js(BLOCKS[n])]
ck("the functions that draw a control for a {state} link were found (needsState callers)",
   len(_drawers) >= 2, "found %s" % _drawers)
ck("🔴 a SET STATE drawn without focusState is caught wherever it is drawn",
   _drawers and not _no_focus,
   "⛔ a control that asks for the state must take the reader to the picker; "
   "these draw one that does not: %s" % _no_focus)
_words = [m.start() for m in re.finditer(r"SET STATE", CODE)]
_bad_words = [CODE[max(0, i - 120):i + 10].replace("\n", " ") for i in _words
              if 'onclick="focusState()"' not in CODE[CODE.rfind("<", 0, i):i]]
ck("every SET STATE label on the page sits in a control that calls focusState()",
   _words and not _bad_words, "%d label(s); without the call: %s" % (len(_words), _bad_words))
_refs = re.findall(r"[^\n]*\bfocusState\b[^\n]*", CODE)
_odd = [r.strip() for r in _refs
        if "function focusState(" not in r and "window.focusState = focusState" not in r
        and 'onclick="focusState()"' not in r]
ck("focusState is reached only from those controls (nothing else calls it differently)",
   not _odd, "other references: %s" % _odd)

# ══════════════════════════════════════════════════════════════════════
section("2-4. 🔴 RUN IN NODE: THE PAGE'S OWN setTools, focusState, stateChosen AND pickCard")
DRIVER = r"""
const fs = require('fs');
const S = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const mk = id => ({id, style: {display: ''}, textContent: '', value: '',
  classList: {add(){}, remove(){}}, scrollIntoView(){},
  focus(){ document.activeElement = this; }});
const els = {};
['#dt', '#filt', '#st', '#stamp', '#ttl'].forEach(k => els[k] = mk(k));
function node(){ return {className: '', innerHTML: '', kids: [],
  append(...n){ this.kids.push(...n); },
  insertAdjacentHTML(_, h){ this.kids.push({innerHTML: h, kids: []}); } }; }
const html = n => (n.className ? `<${n.className}>` : '') + (n.innerHTML || '') + ' '
                  + (n.kids || []).map(html).join(' ');
const document = {activeElement: null, getElementById: id => els['#' + id] || null,
                  querySelector: q => els[q] || null, createElement: () => node()};
const $ = q => els[q];
const window = {};
const setTimeout = () => 0;
let STORE = {};
const localStorage = {getItem: k => (k in STORE ? STORE[k] : null),
                      setItem: (k, v) => { STORE[k] = String(v); },
                      removeItem: k => { delete STORE[k]; }};
let LEAGUE = 'mlb', TAB = 'scores', FBTAB = 'scores';
/* The two renderers stateChosen may call. Each does what the page's own does
   first (show() and renderFootball() both start with setTools) and records
   the tab it drew. */
const drawn = [];
function show(t){ TAB = t; drawn.push('mlb|' + t); setTools(t); }
function renderFootball(){ drawn.push(LEAGUE + '|' + FBTAB); setTools(FBTAB); }
const stub = () => '', confClass = stub, headUrl = stub, projChip = stub, mark = stub,
      fbMark = stub, ab = String, fbAb = String, sgn = String, FBTEAMS = {};
const bookChip = k => `<span class="bk-chip">${k}</span>`;
eval(S.code);
const st = els['#st'];
const out = {reveal: [], redraw: []};
for (const lg of ['mlb', 'nfl', 'ncaaf']){
  for (const [tab] of tabsFor(lg)){
    LEAGUE = lg;
    st.style.display = '';
    setTools(tab);
    const hid = st.style.display === 'none';
    document.activeElement = null;
    focusState();
    out.reveal.push({lg, tab, hid, shown: st.style.display !== 'none',
                     focused: document.activeElement === st});
    /* The other league's tab is left on a different tab on purpose: a redraw
       keyed on the wrong league's tab draws that one instead. */
    if (typeof stateChosen !== 'function'){ out.redraw = null; continue; }
    if (lg === 'mlb'){ TAB = tab; FBTAB = 'odds'; } else { TAB = 'odds'; FBTAB = tab; }
    st.style.display = '';
    setTools(tab);
    STORE = {}; drawn.length = 0;
    stateChosen('NJ');
    out.redraw.push({lg, tab, drawn: drawn.slice(), state: STORE.gp_state || null,
                     shown: st.style.display !== 'none'});
  }
}
LEAGUE = 'mlb';
const card = () => html(pickCard(S.row)).replace(/\s+/g, ' ');
STORE = {};
out.before = {control: betControl(S.row.link), card: card()};
STORE = {gp_state: 'NJ'};
out.after = {control: betControl(S.row.link), card: card()};
process.stdout.write(JSON.stringify(out));
"""
_code = "\n".join([const("TABS"), const("TABS_OFF"), fn("tabsFor"), fn("setTools"),
                   line_of("const el = "), fn("betState"), fn("setBetState"), fn("betLink"),
                   fn("needsState"), fn("focusState"), fn("betControl"), fn("stateChosen"),
                   fn("pickCard")])
SLIP = "https://sportsbook.caesars.com/us/{state}/bet/betslip?selectionIds=gp-planted-1"
ROW = dict(kind="pitcher", pitcher="Planted Pitcher", game="AWY @ HOM", market="strikeouts",
           side="over", line=5.5, price=-120, book="williamhill_us", link=SLIP,
           confidence_basis="MODEL", confidence=64, break_even=54.5, edge=9.5,
           why=["A planted row."])
tmp = tempfile.mkdtemp(prefix="setstate-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"code": _code, "row": ROW}, open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=120)
    R = json.loads(r.stdout) if r.returncode == 0 else \
        {"reveal": [], "redraw": [], "before": {}, "after": {}}
finally:
    shutil.rmtree(tmp, ignore_errors=True)
ck("the page's own setTools, focusState, stateChosen, betControl and pickCard ran in node",
   r.returncode == 0 and R["reveal"], (r.stderr or "")[-400:])

section("2. 🔴 focusState() SHOWS AND FOCUSES THE PICKER, WHATEVER THE TAB")
_tabs = {(x["lg"], x["tab"]) for x in R["reveal"]}
ck("every tab of every league was asked (the list read out of the page's TABS)",
   len(_tabs) >= 27 and {lg for lg, _t in _tabs} == {"mlb", "nfl", "ncaaf"},
   "%d (league, tab) pairs" % len(_tabs))
_hidden = sorted("%s/%s" % (x["lg"], x["tab"]) for x in R["reveal"] if x["hid"])
ck("setTools hides the picker on some tabs (Gizmo's Picks among them), so the question is real",
   "mlb/picks" in _hidden and "nfl/picks" in _hidden and "ncaaf/picks" in _hidden,
   "hidden on %s" % _hidden)
_dead = ["%s/%s" % (x["lg"], x["tab"]) for x in R["reveal"]
         if not (x["shown"] and x["focused"])]
ck("🔴 the picker is shown before it is focused, on every tab of every league",
   R["reveal"] and not _dead,
   "⛔ a SET STATE click on these tabs leaves the picker hidden or unfocused, so it does "
   "nothing: %s" % _dead)

section("3. 🔴 CHOOSING A STATE REDRAWS THE TAB BEING READ")
ck("the page has one function a chosen state goes to (stateChosen)",
   R["redraw"] is not None, "⛔ no stateChosen on the page")
R["redraw"] = R["redraw"] or []
_wrong = ["%s/%s drew %s" % (x["lg"], x["tab"], x["drawn"]) for x in R["redraw"]
          if x["drawn"] != ["%s|%s" % (x["lg"], x["tab"])]]
ck("🔴 choosing a state redraws the tab being read, in every league",
   R["redraw"] and not _wrong,
   "⛔ a tab that is not redrawn keeps its SET STATE buttons after the state is chosen: %s"
   % _wrong[:6])
ck("...and the state chosen is the one kept",
   R["redraw"] and all(x["state"] == "NJ" for x in R["redraw"]),
   str([x["state"] for x in R["redraw"]][:6]))
_gone = ["%s/%s" % (x["lg"], x["tab"]) for x in R["redraw"] if not x["shown"]]
ck("the picker stays where the reader just used it",
   R["redraw"] and not _gone, "hidden again after the choice on %s" % _gone)
_wired = re.findall(r"stSel\.addEventListener\('change',\s*e\s*=>\s*stateChosen\(e\.target\.value\)\)",
                    CODE)
_listeners = re.findall(r"stSel\.addEventListener\(", CODE)
ck("the picker's change event goes to stateChosen",
   len(_wired) == 1 and len(_listeners) == 1,
   "%d change listener(s) on the picker, %d to stateChosen" % (len(_listeners), len(_wired)))

section("4. 🔴 A PICK ROW WITH A {state} LINK")
_b, _a = R.get("before", {}), R.get("after", {})
ck("🔴 a pick row with a {state} link asks for the state rather than dropping the button",
   'onclick="focusState()"' in _b.get("control", "") and "SET STATE" in _b.get("card", "")
   and 'onclick="focusState()"' in _b.get("card", ""),
   "control %r; card %r" % (_b.get("control", ""), _b.get("card", "")[-300:]))
_want = SLIP.replace("{state}", "nj")
ck("...and once the state is chosen the book link is that state's bet slip",
   ('class="bklink" href="%s"' % _want) in _a.get("card", "")
   and "SET STATE" not in _a.get("card", "") and "{state}" not in _a.get("card", ""),
   "card %r" % _a.get("card", "")[-300:])
ck("...and betControl itself turns into that link",
   ('href="%s"' % _want) in _a.get("control", ""), _a.get("control", ""))

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that a book has a site in the state chosen (the "
     "book is the authority, and a state where it has none returns the book's own error), "
     "or anything about a real click: test_league_switch.py section 6 clicks it in Chromium.")
