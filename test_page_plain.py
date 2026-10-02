#!/usr/bin/env python3
"""
🔴 THE PAGE SHOWS EACH TAB'S CONTENT, NOT NOTES ABOUT IT.

`[Sam, 2026-10-01]` *"honestly i don't want any of the yellow boxes
explaining each tab in any tab anymore ... i just want what's supposed to
be in each tab to be in each tab. do this for all 3 leagues"* -- and on
Gizmo's Picks, *"we have a track record for a reason"*. Asked what stays,
he chose: remove everything.

So on every MLB, NFL and college tab there is no explanation, caveat or
warning box (note / fnote / fbnotes / glwarn / domnote / domrow), no
confidence pop-up, no badge legend, no MODEL / MARKET / DESCRIPTIVE /
RECORD / LIVE tag (span.kind), no per-row flag, no stale-data bar or "out
of date" note, and nothing in the yellow box palette. Two Trends headers
carry their own meaning instead: "Rank (1 = most allowed)" on defence and
"Per game vs FBS" for college, gated on the builder's own flag.

THE QUESTION IS ASKED OF THE SHIPPED PAGE, THE WAY test_page_contract.py
ASKS IT: index.html's own code with every comment removed (a struck note
in a comment is not on the page), the tab list read out of the page's own
navigation and dispatch, never typed here, and the row renderers run in
node. ⛔ The DATA keeps every kind / basis / flag / note field and every
server-side check on them stays -- this file asks only what is DRAWN.

# @vacuity 🔴 no note-type box anywhere on the page
#   file: index.html
#   find: <div class="tagline" id="tagline">MLB &mdash; live board</div>
#   with: <div class="tagline" id="tagline">MLB &mdash; live board</div><div class="note">Read this first.</div>
#
# @vacuity 🔴 no MODEL / MARKET / DESCRIPTIVE tag anywhere on the page
#   file: index.html
#   find: head.innerHTML = `<h2>Gizmo's Picks &mdash; ${CARD_DATE}</h2>`;
#   with: head.innerHTML = `<h2>Gizmo's Picks &mdash; ${CARD_DATE} <span class="kind k-model">Model</span></h2>`;
#
# @vacuity 🔴 no stale-data bar
#   file: index.html
#   find: <div class="tagline" id="tagline">MLB &mdash; live board</div>
#   with: <div class="tagline" id="tagline">MLB &mdash; live board</div><div id="stalebar" class="stalebar"></div>
#
# @vacuity 🔴 no confidence pop-up
#   file: index.html
#   find: head.innerHTML = `<h2>Gizmo's Picks &mdash; ${CARD_DATE}</h2>`;
#   with: head.innerHTML = `<h2>Gizmo's Picks &mdash; ${CARD_DATE}</h2><p>${P.calibration_warning}</p>`;
#
# @vacuity no badge legend
#   file: index.html
#   find: <div class="tagline" id="tagline">MLB &mdash; live board</div>
#   with: <div class="tagline" id="tagline">MLB &mdash; live board</div><footer><b>How to read the badges</b> Model is ours.</footer>
#
# @vacuity 🔴 no per-row flag in the shipped code
#   file: index.html
#   find: c.append(el('div','pk-b', '<ul>' + p.why.map(w => `<li>${w}</li>`).join('') + '</ul>'));
#   with: c.append(el('div','pk-b', '<ul>' + p.why.map(w => `<li>${w}</li>`).join('') + '</ul>')); if (p.lineup_risk) c.append(el('div','fl fl-flag','<b>Lineup risk</b>'));
#
# @vacuity nothing in the yellow box palette
#   file: index.html
#   find: .plain{font-size:12.5px;color:var(--mut);margin:8px 0}
#   with: .plain{font-size:12.5px;color:var(--mut);margin:8px 0;background:#fff9ec}
#
# @vacuity 🔴 every tab of every league is clean, tab by tab
#   file: index.html
#   find: v.innerHTML = fbShell(`<h2>Around the league</h2>
#   with: v.innerHTML = fbShell(`<h2>Around the league</h2><div class="fbnotes">Headlines from the feed.</div>
#
# @vacuity 🔴 the defence rank header says rank 1 allows the most
#   file: index.html
#   find: fbSide==='off' ? 'Rk' : 'Rank (1 = most allowed)'}</th>
#   with: fbSide==='off' ? 'Rk' : 'Rk'}</th>
#
# @vacuity 🔴 the college per-game header says vs FBS
#   file: index.html
#   find: ? 'Per game vs FBS' : 'Per gm'} ${sortArrow}</th>
#   with: ? 'Per gm' : 'Per gm'} ${sortArrow}</th>
#
# @vacuity 🔴 a rendered pick card shows its numbers and no flag
#   file: index.html
#   find: c.append(el('div','pk-b', '<ul>' + p.why.map(w => `<li>${w}</li>`).join('') + '</ul>'));
#   with: c.append(el('div','pk-b', '<ul>' + p.why.map(w => `<li>${w}</li>`).join('') + '</ul>')); (p.flags||[]).filter(f => f.actionable).forEach(f => c.append(el('div', 'fl fl-warn', f.text)));
#
# @vacuity a rendered labelled number is the number alone
#   file: index.html
#   find: return x.value == null ? `—${unit || ''}` : fmt(x.value);
#   with: return x.value == null ? `—${unit || ''}` : fmt(x.value) + ` <span class="kind k-${x.basis.toLowerCase()}">${x.basis}</span>`;
#
# @vacuity the tab list is read out of the page, every tab mapped to its renderer
#   file: index.html
#   find: if (FBTAB === 'record') return fbRecord();
#   with: if (FBTAB === 'recordx') return fbRecord();
#
# @vacuity the page's own pickCard runs in node
#   file: index.html
#   find: const c = el('div','pk');
#   with: const c = el('div','pk'); helperThePageNeverDefined();
#
# @vacuity a hitter row draws no RECORD chip
#   file: index.html
#   find: c.append(el('div','pk-b', '<ul>' + p.why.map(w => `<li>${w}</li>`).join('') + '</ul>'));
#   with: c.append(el('div','pk-b', '<ul>' + p.why.map(w => `<li>${w}</li>`).join('') + '</ul>')); if (p.confidence_basis === 'RECORD') c.append(el('span','bandchip rec','RECORD'));
#
# @vacuity the started-games control names what it shows
#   file: index.html
#   find: showStarted ? 'Hide' : 'Show'} ${n} started game${n === 1 ? '' : 's'}</a></div>`;
#   with: showStarted ? 'Hide them' : 'Show anyway'}</a></div>`;
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


def strip_js(js):
    """JavaScript with every comment removed. Strings, template literals and
    regex literals are kept as code; an HTML comment inside a template
    literal (emitted into innerHTML, never seen) is removed too."""
    out, i, n = [], 0, len(js)
    frames = [["code", 0]]
    prev = ""
    while i < n:
        kind, c = frames[-1][0], js[i]
        if kind == "code":
            if js.startswith("/*", i):
                j = js.find("*/", i + 2)
                i = n if j < 0 else j + 2
                out.append(" ")
                continue
            if js.startswith("//", i):
                j = js.find("\n", i)
                i = n if j < 0 else j
                continue
            if c == "/" and (prev == "" or prev in "(,=:[!&|?{};+-*%<>~^"):
                j, cls = i + 1, False                     # a regex literal
                while j < n and js[j] != "\n":
                    if js[j] == "\\":
                        j += 2
                        continue
                    if js[j] == "[":
                        cls = True
                    elif js[j] == "]":
                        cls = False
                    elif js[j] == "/" and not cls:
                        break
                    j += 1
                out.append(js[i:j + 1])
                i, prev = j + 1, "/"
                continue
            if c in "\"'":
                j = i + 1
                while j < n and js[j] != c and js[j] != "\n":
                    j += 2 if js[j] == "\\" else 1
                out.append(js[i:j + 1])
                i, prev = j + 1, c
                continue
            if c == "`":
                frames.append(["tpl", 0])
                out.append(c)
                i += 1
                continue
            if c == "{":
                frames[-1][1] += 1
            elif c == "}":
                if frames[-1][1] == 0 and len(frames) > 1:
                    frames.pop()
                    out.append(c)
                    i += 1
                    prev = "}"
                    continue
                frames[-1][1] -= 1
            out.append(c)
            if not c.isspace():
                prev = c
            i += 1
            continue
        if c == "\\":
            out.append(js[i:i + 2])
            i += 2
            continue
        if js.startswith("<!--", i):
            j = js.find("-->", i + 4)
            i = n if j < 0 else j + 3
            continue
        if c == "`":
            frames.pop()
            out.append(c)
            i, prev = i + 1, "`"
            continue
        if js.startswith("${", i):
            frames.append(["code", 0])
            out.append("${")
            i += 2
            prev = "{"
            continue
        out.append(c)
        i += 1
    return "".join(out)


_s0, _s1 = SRC.index("<style>"), SRC.index("</style>")
_j0, _j1 = SRC.index("<script>") + len("<script>"), SRC.rindex("</script>")
CSS = re.sub(r"/\*.*?\*/", " ", SRC[_s0:_s1], flags=re.S)
BODY = re.sub(r"<!--.*?-->", " ", SRC[_s1:_j0], flags=re.S)
JS = strip_js(SRC[_j0:_j1])
LIVE = BODY + "\n" + JS

BOXES = {"note", "fnote", "fbnotes", "glwarn", "domnote", "domrow"}
TAGS = {"kind", "k-model", "k-market", "k-desc", "k-live", "k-record"}
FLAGS = {"fl-warn", "fl-flag", "bandchip"}


def class_tokens(code):
    """Every class name the code can draw: class="..." attributes, el()'s
    class argument, className / classList, and every string literal (a
    class can be chosen through a map such as {MODEL:'k-model'})."""
    vals = re.findall(r"""class\s*=\s*(["'])(.*?)\1""", code)
    vals = [v for _q, v in vals]
    vals += re.findall(r"""el\(\s*['"][^'"]*['"]\s*,\s*['"]([^'"]*)['"]""", code)
    vals += re.findall(r"""className\s*[+]?=\s*['"]([^'"]*)['"]""", code)
    vals += re.findall(r"""classList\.(?:add|toggle)\(\s*['"]([^'"]*)['"]""", code)
    # ⚠️ A plain string counts only when it LOOKS LIKE A CLASS LIST (lowercase
    #    class names, at most four): "No plays of that kind on this card." is
    #    a sentence, not the `kind` class.
    vals += [v for v in re.findall(r"'([^'\n]*)'", code) + re.findall(r'"([^"\n]*)"', code)
             if re.fullmatch(r"[a-z0-9_-]+(?:\s+[a-z0-9_-]+){0,3}", v.strip())]
    toks = set()
    for v in vals:
        for t in re.split(r"[\s${}?:+'\"`]+", v):
            if t:
                toks.add(t)
    return toks


def hits(code, names):
    return sorted(class_tokens(code) & names)


# ══════════════════════════════════════════════════════════════════════
section("0. THE PAGE WAS READ, AND THE COMMENT STRIPPER IS NOT A BLINDFOLD")
# ⛔ A PRECONDITION OF EVERY ABSENCE BELOW, not a check of its own: a
#    stripper that ate the code would make "nothing found" pass blind, so
#    each absence check is ANDed with READ.
READ = (len(CSS) > 1000 and len(BODY) > 500 and len(JS) > 100000
        and all(("function %s(" % f) in JS for f in jsblock.top_level_blocks(PAGE)))
note("read: css %d, body %d, script %d characters; every top-level function "
     "survives the comment stripper: %s" % (len(CSS), len(BODY), len(JS), READ))

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 NOTHING THAT EXPLAINS A TAB IS DRAWN, ON ANY TAB")
ck("🔴 no note-type box anywhere on the page (note, fnote, fbnotes, glwarn, domnote, domrow)",
   READ and not hits(LIVE, BOXES), "found %s" % hits(LIVE, BOXES))
ck("🔴 no MODEL / MARKET / DESCRIPTIVE tag anywhere on the page (span.kind, k-*)",
   READ and not hits(LIVE, TAGS), "found %s" % hits(LIVE, TAGS))
_stale = [w for w in ("stalebar", "renderStaleBanner", "cardStaleNote") if w in LIVE]
ck("🔴 no stale-data bar and no out-of-date card note", READ and not _stale, "found %s" % _stale)
_pop = [w for w in ("calibration_warning", "Read the confidence number honestly",
                    "held up", "card-calibration") if w in LIVE]
ck("🔴 no confidence pop-up (either league)", READ and not _pop, "found %s" % _pop)
_leg = [w for w in ("How to read the badges", "Model is ours", "<footer") if w in LIVE]
ck("no badge legend", READ and not _leg, "found %s" % _leg)
_fl = hits(LIVE, FLAGS) + [w for w in (".actionable", "Lineup risk", "RE-ORIENTED") if w in LIVE]
ck("🔴 no per-row flag in the shipped code (Hard Rock, lineup risk, re-oriented, row chips)",
   READ and not _fl, "found %s" % _fl)
_yel = [c for c in ("#fff9ec", "#f0dfb8") if c in CSS.lower()]
ck("nothing in the yellow box palette", READ and not _yel, "found %s" % _yel)

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 EVERY TAB OF EVERY LEAGUE, READ OUT OF THE PAGE")
BLOCKS = {k: strip_js(v) for k, v in jsblock.top_level_blocks(PAGE).items()}


def closure(fn):
    """`fn` and every top-level function it can reach by name."""
    seen, todo = set(), [fn]
    while todo:
        f = todo.pop()
        if f in seen or f not in BLOCKS:
            continue
        seen.add(f)
        todo += [g for g in BLOCKS if g not in seen
                 and re.search(r"\b%s\b" % re.escape(g), BLOCKS[f])]
    return seen


_mlb_tabs = sorted(set(re.findall(r'data-tab="([a-z]+)"', BODY)))
_m = re.search(r"\(\{(\s*scores\s*:\s*renderScores[^}]*)\}\)", JS)
_mlb_fn = dict(re.findall(r"(\w+)\s*:\s*(render\w+)", _m.group(1))) if _m else {}
_fb_tabs = re.search(r"const tabs = \[([^\]]*)\];", BLOCKS.get("fbNav", "") or JS)
_fb_tabs = re.findall(r"'([a-z]+)'", _fb_tabs.group(1)) if _fb_tabs else []
_fb_fn = dict(re.findall(r"FBTAB === '([a-z]+)'\) return (fb\w+)\(\)", BLOCKS.get("renderFootball", "")))
_gl = re.search(r"FBTAB === 'gamelines'[^;]*?(fb\w+)\(\)", JS)
if _gl:
    _fb_fn["gamelines"] = _gl.group(1)
_fb_fn.setdefault("trends", "renderFootball")
TABS = [("mlb", t, _mlb_fn.get(t)) for t in _mlb_tabs] + \
       [(lg, t, _fb_fn.get(t)) for lg in ("nfl", "ncaaf") for t in _fb_tabs]
ck("the tab list comes from the page: 8 MLB tabs and 9 per football league",
   len(_mlb_tabs) >= 8 and len(_fb_tabs) >= 9 and all(fn for _lg, _t, fn in TABS),
   "mlb %s; football %s; unmapped %s"
   % (_mlb_tabs, _fb_tabs, [(lg, t) for lg, t, fn in TABS if not fn]))
_dirty = []
for lg, tab, fn in TABS:
    code = "\n".join(BLOCKS[f] for f in closure(fn)) if fn else ""
    bad = hits(code, BOXES | TAGS | FLAGS) + [w for w in ("calibration_warning", "stalebar")
                                               if w in code]
    if bad or not fn:
        _dirty.append((lg, tab, fn, bad))
ck("🔴 every tab of every league is clean, tab by tab (%d tabs, each with every "
   "function it can reach)" % len(TABS), READ and not _dirty, "dirty: %s" % _dirty)

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE TWO TRENDS COLUMNS EXPLAIN THEMSELVES IN THEIR HEADER")
_tr = BLOCKS.get("renderFootball", "")
ck("🔴 the defence rank header says rank 1 allows the most",
   "fbSide==='off' ? 'Rk' : 'Rank (1 = most allowed)'" in _tr,
   "⛔ the box that said so is gone, so the header has to")
ck("🔴 the college per-game header says vs FBS, on the builder's own flag",
   re.search(r"LEAGUE === 'ncaaf' && doc\.per_game_scope\s*\?\s*'Per game vs FBS'", _tr) is not None,
   "⛔ gated on per_game_scope (rule 132): a season built before the flag keeps 'Per gm'")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 RENDERED IN NODE: A CARD CARRYING EVERY RETIRED FLAG SHOWS ONLY NUMBERS")
_el = next(l for l in SRC.splitlines() if l.startswith("const el = "))
DRIVER = r"""
const fs = require('fs');
function node(){ return {className: '', innerHTML: '', kids: [],
  append(...n){ this.kids.push(...n); },
  insertAdjacentHTML(_, h){ this.kids.push({innerHTML: h, kids: []}); } }; }
const document = {createElement: () => node()};
const html = n => (n.className ? `<${n.className}>` : '') + (n.innerHTML || '') + ' '
                  + (n.kids || []).map(html).join(' ');
const S = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const stub = () => '';
const pc = new Function('document', 'confClass', 'headUrl', 'projChip', 'mark', 'ab', 'sgn',
  'bookChip', 'betControl', 'betLink', 'fbMark', 'fbAb', 'FBTEAMS', 'LEAGUE',
  S.el + '\n' + S.pickCard + '\nreturn pickCard;')(
  document, stub, stub, stub, stub, stub, String, stub, stub, stub, stub, stub, {}, 'mlb');
const labN = new Function(S.labN + '\nreturn labN;')();
let showStarted = false;
const st = new Function('showStarted', S.toggle + '\nreturn startedToggle;');
process.stdout.write(JSON.stringify({
  cards: S.rows.map(r => html(pc(r)).replace(/\s+/g, ' ')),
  lab: [labN({value: 62.5, basis: 'MODEL'}, '%'), labN({value: 3, basis: 'MARKET'}),
        labN({value: null, basis: 'DESCRIPTIVE'}), labN(7)],
  toggle: [st(false)(3, 'x', false), st(true)(1, 'x', false), st(false)(3, 'x', true)]}));
"""
_flagged = dict(kind="pitcher", pitcher="Trevor Rogers", game="MIA @ WSH", market="outs",
                side="over", line=17.5, price=-210, book="hardrockbet",
                confidence_basis="MODEL", confidence=66, break_even=67.7, edge=-2.0,
                below_price=True, lineup_risk=True, lineup_share=41,
                flags=[{"text": "Hard Rock didn't post this", "actionable": True},
                       {"text": "T21 shadow", "actionable": False}],
                why=["Went 6+ innings in 4 of his last 5 starts."])
_hitter = dict(_flagged, kind="hitter", player="Some Hitter", pitcher=None,
               market="batter_hits", line=0.5, confidence_basis="RECORD", below_price=False)
tmp = tempfile.mkdtemp(prefix="plain-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"el": _el, "pickCard": jsblock.js_block("pickCard", PAGE),
               "labN": jsblock.js_block("labN", PAGE),
               "toggle": jsblock.js_block("startedToggle", PAGE),
               "rows": [_flagged, _hitter]}, open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=300)
    ck(r.returncode == 0, "the page's own pickCard, labN and startedToggle ran in node",
       (r.stderr or "")[-300:])
    R = json.loads(r.stdout) if r.returncode == 0 else {"cards": ["", ""], "lab": [""] * 4,
                                                        "toggle": [""] * 3}
finally:
    shutil.rmtree(tmp, ignore_errors=True)
_card = R["cards"][0]
_bad = [w for w in ("fl-warn", "fl-flag", "bandchip", "kind", "Hard Rock didn", "Lineup risk",
                    "T21", "MODEL", "fill the board out") if w in _card]
ck("🔴 a rendered pick card shows its numbers and no flag",
   not _bad and "66%" in _card and "67.7%" in _card and "-2%" in _card
   and "Went 6+ innings" in _card,
   "flags drawn %s; card %r" % (_bad, _card[-300:]))
ck("...and a hitter row draws no RECORD chip either",
   not [w for w in ("RECORD", "bandchip", "kind") if w in R["cards"][1]], R["cards"][1][-200:])
ck("a rendered labelled number is the number alone",
   R["lab"] == ["62.5%", "3", "—", "7"], "got %s" % R["lab"])
ck("the started-games control names what it shows, and is gone when every game started",
   R["toggle"][0].endswith(">Show 3 started games</a></div>")
   and ">Hide 1 started game</a>" in R["toggle"][1] and R["toggle"][2] == ""
   and "note" not in "".join(R["toggle"]), "got %s" % R["toggle"])

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that a number on the page is right, or that "
     "the data files dropped a field. The cards, the records and every verify_* "
     "check still carry kind, basis, flags and notes; only the page stopped drawing them.")
