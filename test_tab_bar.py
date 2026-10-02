#!/usr/bin/env python3
"""
🔴 ONE TAB BAR, ONE ORDER, THE SAME LOOK, IN EVERY LEAGUE.

`[Sam, 2026-10-01]` *"lets have the colors of the tabs and the layout be the
same for each league, mlb looks different than the other 2 leagues. we need
same order of tab from left to right, same colors, etc."* MLB drew its tabs
in the header's `.subnav`; football drew a second, differently styled bar
inside its own view, in another order, opening on Trends.

✅ Now the header's `.subnav` is the ONLY tab bar. One list (`TABS`) gives
every league the same order and names -- Scores, Gizmo's Picks, Odds,
Player Props, Game Lines, Parlays, Trends, Track Record, News -- with MLB
leaving out Game Lines until it has one. Every league opens on Scores, and
switching league keeps the tab when the new league has it.

ASKED OF THE SHIPPED PAGE: `drawTabs`, `tabsFor`, `nextTab`, `tabName` and
`setTools` are cut out of index.html and run in node for each league; the
look is the stylesheet's own rules for that one element, with nothing in
the markup or the CSS that could differ by league. The REAL computed style,
in a browser, is measured by test_league_switch.py on pr-tests' render job.

# @vacuity the page's own tab code runs in node
#   file: index.html
#   find: const ul = document.querySelector('.subnav ul'); if (!ul) return;
#   with: const ul = document.querySelector('.subnav ul'); if (!ul) return; tabHelperThePageNeverDefined();
#
# @vacuity 🔴 football draws no tab bar of its own
#   file: index.html
#   find: return fbPanel(inner);
#   with: return '<nav class="subnav"><ul><li><a data-tab="trends">Trends</a></li></ul></nav>' + fbPanel(inner);
#
# @vacuity 🔴 switching to football never hides the one bar
#   file: index.html
#   find: if (lg === 'mlb') TAB = nextTab(cur, lg); else FBTAB = nextTab(cur, lg);
#   with: if (lg === 'mlb') TAB = nextTab(cur, lg); else FBTAB = nextTab(cur, lg); document.querySelector('.subnav').style.display = lg === 'mlb' ? '' : 'none';
#
# @vacuity 🔴 the same left-to-right order in every league
#   file: index.html
#   find: ['trends', 'Trends'], ['record', 'Track Record'], ['news', 'News']];
#   with: ['record', 'Track Record'], ['trends', 'Trends'], ['news', 'News']];
#
# @vacuity 🔴 the same tab names in every league ("Scores")
#   file: index.html
#   find: const TABS = [['scores', 'Scores'], ['picks', "Gizmo's Picks"], ['odds', 'Odds'],
#   with: const TABS = [['scores', 'Scores &amp; Matchups'], ['picks', "Gizmo's Picks"], ['odds', 'Odds'],
#
# @vacuity 🔴 the same markup for active and inactive tabs in every league
#   file: index.html
#   find: `<li><a data-tab="${k}" class="${k === cur ? 'on' : ''}">${nm}</a></li>`).join('');
#   with: `<li><a data-tab="${k}" class="${k === cur ? 'on' : ''}"${LEAGUE === 'mlb' ? '' : ' style="font-size:12px"'}>${nm}</a></li>`).join('');
#
# @vacuity 🔴 no CSS rule styles the bar differently for one league
#   file: index.html
#   find: .subnav a.on{color:#fff;box-shadow:inset 0 -3px 0 var(--accent2)}
#   with: .subnav a.on{color:#fff;box-shadow:inset 0 -3px 0 var(--accent2)} body.fb .subnav a.on{color:#f0a500}
#
# @vacuity 🔴 MLB shows no Game Lines tab yet; football does
#   file: index.html
#   find: const TABS_OFF = { mlb: ['gamelines'] };
#   with: const TABS_OFF = { mlb: [] };
#
# @vacuity 🔴 every league opens on Scores
#   file: index.html
#   find: let FBTAB  = 'scores';
#   with: let FBTAB  = 'trends';
#
# @vacuity 🔴 switching league keeps the tab when the new league has it
#   file: index.html
#   find: function nextTab(cur, lg){ return tabsFor(lg).some(([k]) => k === cur) ? cur : 'scores'; }
#   with: function nextTab(cur, lg){ return 'scores'; }
#
# @vacuity 🔴 setLeague carries the reader's tab across
#   file: index.html
#   find: if (lg === 'mlb') TAB = nextTab(cur, lg); else FBTAB = nextTab(cur, lg);
#   with: if (lg === 'mlb') TAB = 'scores'; else FBTAB = 'scores';
#
# @vacuity a control a league does not use is not shown
#   file: index.html
#   find: const day = LEAGUE === 'mlb' && tab === 'scores';
#   with: const day = tab === 'scores';
#
# @vacuity the heading is the tab's own name in every league
#   file: index.html
#   find: const t = $('#ttl'); if (t) t.textContent = tabName(FBTAB) || 'Football';
#   with: const t = $('#ttl'); if (t) t.textContent = 'Football';
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

# Sam's order and names, 2026-10-01: the REQUIREMENT, so it is written here.
WANT = [("scores", "Scores"), ("picks", "Gizmo's Picks"), ("odds", "Odds"),
        ("props", "Player Props"), ("gamelines", "Game Lines"), ("parlays", "Parlays"),
        ("trends", "Trends"), ("record", "Track Record"), ("news", "News")]
LEAGUES = ("mlb", "nfl", "ncaaf")


def fn(name):
    try:
        return jsblock.js_block(name, PAGE)
    except AssertionError:
        return ""


def const(name):
    m = re.search(r"\nconst %s = .*?;\r?\n" % re.escape(name), SRC, re.S)
    return m.group(0).strip() if m else ""


DRIVER = r"""
const fs = require('fs');
const S = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const ul = {innerHTML: ''};
const els = {};
['#dt', '#filt', '#st', '#stamp', '#ttl'].forEach(k => els[k] = {style: {display: ''}, textContent: ''});
const document = {querySelector: q => q === '.subnav ul' ? ul : null};
const $ = q => els[q];
let LEAGUE = 'mlb', TAB = 'scores', FBTAB = 'scores';
eval(S.code);
const out = {bars: {}, next: {}, tools: {}, names: {}};
for (const lg of ['mlb', 'nfl', 'ncaaf']){
  LEAGUE = lg; TAB = 'parlays'; FBTAB = 'parlays';
  drawTabs(); out.bars[lg] = ul.innerHTML;
  for (const tab of ['scores', 'odds', 'trends']){
    setTools(tab);
    out.tools[lg + '|' + tab] = ['#dt', '#filt', '#st'].map(k => els[k].style.display === '' ? 1 : 0);
  }
}
for (const [cur, lg] of [['parlays','nfl'], ['gamelines','mlb'], ['trends','ncaaf'],
                         ['gamelines','ncaaf'], ['news','mlb'], ['props','nfl']])
  out.next[cur + '>' + lg] = nextTab(cur, lg);
for (const k of ['scores', 'gamelines', 'record']) out.names[k] = tabName(k);
process.stdout.write(JSON.stringify(out));
"""
CODE = "\n".join([const("TABS"), const("TABS_OFF"), fn("tabsFor"), fn("nextTab"),
                  fn("tabName"), fn("drawTabs"), fn("setTools")])
tmp = tempfile.mkdtemp(prefix="tabbar-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"code": CODE}, open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=120)
    R = json.loads(r.stdout) if r.returncode == 0 else {"bars": {}, "next": {}, "tools": {}, "names": {}}
finally:
    shutil.rmtree(tmp, ignore_errors=True)


def links(html):
    """[(key, label, attrs)] for every tab the bar draws."""
    return [(k, lab, a) for a, k, lab in
            re.findall(r'<a (data-tab="([a-z]+)"[^>]*)>([^<]*)</a>', html)]


BAR = {lg: links(R["bars"].get(lg, "")) for lg in LEAGUES}

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 ONE TAB BAR: THE HEADER'S, FOR EVERY LEAGUE")
ck("the page's own drawTabs, tabsFor, nextTab, tabName and setTools ran in node",
   r.returncode == 0 and all(BAR[lg] for lg in LEAGUES), (r.stderr or "")[-300:])
_head = SRC[SRC.index("<header>"):SRC.index("</header>")]
_navs = len(re.findall(r'<nav class="subnav"', SRC))
ck("🔴 football draws no tab bar of its own: the one bar is the header's",
   "subnav" not in fn("fbShell") and "<nav" not in fn("fbShell")
   and "data-tab" not in fn("fbShell") and "data-fbtab" not in SRC
   and _navs == 1 and '<nav class="subnav">' in _head
   and "document.querySelector('.subnav ul')" in fn("drawTabs"),
   "fbShell draws: %r; subnav elements in the page: %d" % (fn("fbShell")[:120], _navs))
ck("🔴 switching to football never hides the one bar",
   ".subnav').style.display" not in SRC and "drawTabs();" in fn("setLeague"),
   "the bar must stay up for every league")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE SAME ORDER, NAMES AND MARKUP IN ALL THREE LEAGUES")
_keys = {lg: [k for k, _l, _a in BAR[lg]] for lg in LEAGUES}
_want = [k for k, _ in WANT]
ck("🔴 the same left-to-right order in every league (Sam's order; MLB without Game Lines)",
   _keys["nfl"] == _want and _keys["ncaaf"] == _want
   and _keys["mlb"] == [k for k in _want if k != "gamelines"],
   "got %s" % _keys)
_names = {lg: {k: lab for k, lab, _a in BAR[lg]} for lg in LEAGUES}
ck("🔴 the same tab names in every league (\"Scores\", not \"Scores & Matchups\")",
   all(_names[lg].get(k) == lab for lg in LEAGUES for k, lab in WANT
       if not (lg == "mlb" and k == "gamelines")) and R["names"].get("scores") == "Scores",
   "got %s" % _names)


def shape(lg, active):
    """The attributes of an active / an inactive tab, minus which tab it is."""
    a = [re.sub(r'data-tab="[a-z]+"', "", at).strip() for k, _l, at in BAR[lg]
         if (k == "parlays") == active]
    return sorted(set(a))


ck("🔴 the same markup for active and inactive tabs in every league, and no inline style",
   all(shape(lg, True) == ['class="on"'] and shape(lg, False) == ['class=""'] for lg in LEAGUES)
   and "style=" not in "".join(R["bars"].values()),
   "active %s; inactive %s" % ({lg: shape(lg, True) for lg in LEAGUES},
                               {lg: shape(lg, False) for lg in LEAGUES}))
# THE STYLE: one element, the same classes, so the same rules -- unless a
# rule reaches it through something that differs by league. Every selector
# that names the bar may use only the bar's own ancestry.
_ok = {"header", "nav", ".subnav", "div", ".wrap", "ul", "li", "a", ".on", ".off", "body", "html"}
_bad = []
for sel, _decl in jsblock.css_rules(PAGE).items():
    for one in sel.split(","):
        if "subnav" not in one:
            continue
        parts = re.findall(r"[.#]?[\w-]+|\[[^\]]*\]", re.sub(r":[\w-]+(\([^)]*\))?", "", one))
        odd = [p for p in parts if p not in _ok]
        if odd:
            _bad.append((one.strip(), odd))
_rules = [s for s in jsblock.css_rules(PAGE) if "subnav" in s]
ck("🔴 no CSS rule styles the bar differently for one league (%d rule(s) name it)" % len(_rules),
   len(_rules) >= 5 and not _bad, "league-scoped: %s" % _bad)

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 MLB HAS NO GAME LINES TAB YET; FOOTBALL DOES")
ck("🔴 MLB shows no Game Lines tab yet; NFL and college show it",
   "gamelines" not in _keys["mlb"] and all("gamelines" in _keys[lg] for lg in ("nfl", "ncaaf")),
   "got %s" % _keys)

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 EVERY LEAGUE OPENS ON SCORES AND KEEPS THE TAB ACROSS A SWITCH")
ck("🔴 every league opens on Scores",
   re.search(r"\blet FBTAB\s*=\s*'scores';", SRC) is not None
   and re.search(r"\bTAB = 'scores';", SRC) is not None and "show('scores');" in SRC,
   "MLB's TAB, football's FBTAB and the first paint must all start on Scores")
_want_next = {"parlays>nfl": "parlays", "gamelines>mlb": "scores", "trends>ncaaf": "trends",
              "gamelines>ncaaf": "gamelines", "news>mlb": "news", "props>nfl": "props"}
ck("🔴 switching league keeps the tab when the new league has it, else Scores",
   R["next"] == _want_next, "got %s" % R["next"])
_sl = fn("setLeague")
ck("🔴 setLeague carries the reader's tab across",
   re.search(r"const cur = LEAGUE === 'mlb' \? TAB : FBTAB;[\s\S]*LEAGUE = lg;", _sl) is not None
   and "TAB = nextTab(cur, lg)" in _sl and "FBTAB = nextTab(cur, lg)" in _sl,
   "the tab is read BEFORE the league changes and handed to nextTab")

# ══════════════════════════════════════════════════════════════════════
section("5. THE SAME LAYOUT AROUND THE TABS")
_t = R["tools"]
ck("a control a league does not use is not shown: the date and live filter on MLB Scores only, "
   "the bet-state picker on Odds and Player Props in every league",
   _t.get("mlb|scores") == [1, 1, 0] and _t.get("nfl|scores") == [0, 0, 0]
   and _t.get("ncaaf|scores") == [0, 0, 0]
   and all(_t.get(lg + "|odds") == [0, 0, 1] and _t.get(lg + "|trends") == [0, 0, 0]
           for lg in LEAGUES), "got %s" % _t)
ck("the heading is the tab's own name in every league",
   "tabName(tab)" in fn("show") and "tabName(FBTAB)" in fn("renderFootball")
   and R["names"].get("gamelines") == "Game Lines",
   "the same <h1>, the same words as the tab")
note("⛔ WHAT THIS FILE DOES NOT CLAIM: that a tab's content is the same across leagues. "
     "It claims the bar, its order, its names, its look and the controls around it are.")
