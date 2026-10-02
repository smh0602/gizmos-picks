#!/usr/bin/env python3
"""test_game_lines_page.py — the Game Lines tab DRAWS what the builder wrote.

It builds a real `game-lines.json.gz` with `game_lines_fb.py` from a small
stored pull, slices the tab's renderer out of the SHIPPED `index.html`,
runs it in node and asks the rendered HTML: every rung drawn, every book's
price labelled for a phone, the heading, no chip / warning / note, and the
sort. ⛔ Not a copy of the page — the page itself.

[Sam, 2026-10-01] "i just want what's supposed to be in each tab to be in
each tab"; asked what stays, he chose: remove everything. The checks that
REQUIRED the Market / Model chips, the ⚠ on a rung that failed the
alt-lines check, the "read the books' chance first" note, the "below
−700 · never paired" chip and the parlays' chip now require their ABSENCE
from the same render — and each first confirms the builder still WRITES
what used to be drawn (`cal`, `warn`, `check`, `floor`, `joint_note`), so
an absence can never pass because the data stopped carrying the thing.

# @vacuity no rung of a market that failed the check carries a warning ON THE ROW [Sam, 2026-10-01]
#   file: index.html
#   find: <div data-l="Model %">${r.p == null ? '&mdash;' : r.p + '%'}</div>
#   with: <div data-l="Model %">${r.p == null ? '&mdash;' : r.p + '%'}${r.cal ? '' : ` <span class="glwarn" title="${r.warn || ''}">&#9888;</span>`}</div>
#
# @vacuity no other line shows one either: a rung that PASSED (an inverted flag) [Sam, 2026-10-01]
#   file: index.html
#   find: <div data-l="Edge">${r.edge == null ? '&mdash;' : (r.edge > 0 ? '+' : '') + r.edge + '%'}</div>
#   with: <div data-l="Edge">${r.edge == null ? '&mdash;' : (r.edge > 0 ? '+' : '') + r.edge + '%'}${r.cal ? ' <span class="glwarn">&#9888;</span>' : ''}</div>
#
# @vacuity no other line shows one either: the model's fair total [Sam, 2026-10-01]
#   file: index.html
#   find: ${one("Model's fair total", g.fair_total, v => '' + v)}</div>`;
#   with: ${one("Model's fair total", g.fair_total, v => '' + v)}${g.fair_total_warn ? ` <span class="glwarn" title="${g.fair_total_warn}">${g.fair_total_warn}</span>` : ''}</div>`;
#
# @vacuity no column header wears a Market / Model chip [Sam, 2026-10-01]
#   file: index.html
#   find: <div>Model %</div>
#   with: <div>Model % <span class="kind k-model">Model</span></div>
#
# @vacuity no note on the tab says what the alt-lines check found [Sam, 2026-10-01]
#   file: index.html
#   find: ${games.map(g => fbGlGame(g, G, st)).join('') || '<div class="msg">No games on this slate match the filters.</div>'}
#   with: <div class="note"><b>Read the books&rsquo; chance first.</b> ${((G.check || {}).total || {}).finding}</div>${games.map(g => fbGlGame(g, G, st)).join('') || '<div class="msg">No games on this slate match the filters.</div>'}
#
# @vacuity the alt parlays wear no chip [Sam, 2026-10-01]
#   file: index.html
#   find: <div class="panel" style="margin-top:18px"><h2>Alt-line parlays</h2>
#   with: <div class="panel" style="margin-top:18px"><h2>Alt-line parlays <span class="kind k-market">Market</span></h2>
#
# @vacuity ...and the builder's joint note is not drawn under them [Sam, 2026-10-01]
#   file: index.html
#   find: <div data-l="Books&rsquo; chance all land">${p.joint}%</div></div>`).join('')).join('')}</div>`;
#   with: <div data-l="Books&rsquo; chance all land">${p.joint}%</div></div>`).join('')).join('')}<div style="margin-top:8px">${P[sizes[0]][0].joint_note || ''}</div></div>`;
#
# @vacuity a rung below -700 is drawn with no chip on it [Sam, 2026-10-01]
#   file: index.html
#   find: <div class="glw"><b>${who} ${fbGlPt(r)}</b></div>
#   with: <div class="glw"><b>${who} ${fbGlPt(r)}</b>${r.floor ? '' : ' <span class="rec">below &minus;700 &middot; never paired</span>'}</div>
#
# @vacuity the heading carries the slate's day [Sam, 2026-10-01]
#   file: index.html
#   find: Game Lines${G && G.slate_date ? ' &mdash; ' + fbDayName(G.slate_date) : ''}</h2></div>
#   with: Game Lines</h2></div>
#
# @vacuity the Game Lines tab is dispatched, not merely defined
#   file: index.html
#   find:   if (FBTAB === 'gamelines' && !document.querySelector('#fbview [data-gl]')) { fbGameLinesTab(); return; }
#   with:   if (false) { fbGameLinesTab(); return; }
#
# @vacuity the books' chance is drawn on every rung, ahead of the model's %
#   file: index.html
#   find:     <div data-l="Books&rsquo; chance"><b>${r.mkt == null ? '&mdash;' : r.mkt + '%'}</b></div>
#   with:     <div></div>
"""
import datetime
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from jsblock import calls, js_block
from tcheck import ck, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import fb_model as F  # noqa: E402
import game_lines_fb as G  # noqa: E402

PAGE = os.path.join(ROOT, "index.html")
HTML = open(PAGE, encoding="utf-8").read()
UTC = datetime.timezone.utc


def wgz(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(obj, fh)


def wjs(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)


# ── a real artifact from a small stored pull ──────────────────────────
H, A_ = "Buffalo Bills", "Los Angeles Chargers"
KICK = "2026-09-27T17:00:00Z"
tree = tempfile.mkdtemp(prefix="glpage-")
lg = os.path.join(tree, "data", "nfl")
sig = {k: None for k in ("h2h_m", "h2h_t", "form_m", "form_t", "def", "poss", "out", "vac_h", "vac_a")}
sig.update(neutral=0.0, dome=0.0)
prow = {"id": "S1", "lg": "nfl", "season": 2026, "day": KICK[:10], "kick": KICK, "week": 4,
        "home": H, "away": A_, "M": 6.5, "T": 47.5, "pml": 0.7, "sig": sig,
        "names": [H, A_], "commence": KICK}
H2, A2, KICK2 = "Detroit Lions", "New York Jets", "2026-09-27T20:25:00Z"
prow2 = dict(prow, id="S2", home=H2, away=A2, kick=KICK2, names=[H2, A2], commence=KICK2)
ks, kt = len(F.features(prow, "spread")), len(F.features(prow, "total"))
wjs(os.path.join(lg, "latest", "fb-model.json"), {"pricing": {"games": [prow, prow2], "models": {
    "spread": {"mu": [0.0] * ks, "sd": [1.0] * ks, "w": [0.0, -1.0] + [0.0] * (ks - 1)},
    "total": {"mu": [0.0] * kt, "sd": [1.0] * kt, "w": [0.0, -1.0] + [0.0] * (kt - 1)}}}})
wjs(os.path.join(lg, "latest", "alt-lines-check.json"),
    {"markets": {"spread": {"state": "PASS", "bands": []},
                 "total": {"state": "FAIL", "bands": [{"stated": 64.0, "n": 40, "w": 10}]}}})
book = {"spreads": {H: {"pt": -6.5, "px": -110}, A_: {"pt": 6.5, "px": -110}},
        "totals": {"Over": {"pt": 47.5, "px": -110}, "Under": {"pt": 47.5, "px": -110}},
        "h2h": {H: -280, A_: 230}}
wgz(os.path.join(lg, "2026-09-26", "gamelines", "1400.json.gz"),
    {"pulled_at": "2026-09-26T14:00:00Z", "games": [{"id": "g1", "commence": KICK, "home": H, "away": A_,
                                                     "books": {"hardrockbet": book, "draftkings": book,
                                                               "fanduel": book}},
                                                    {"id": "g2", "commence": KICK2, "home": H2, "away": A2,
                                                     "books": {}}]})
o = lambda n, pt, px: {"name": n, "point": pt, "price": px}  # noqa: E731
wgz(os.path.join(lg, "2026-09-26", "alt-lines", "1500.json.gz"), {"pulled_at": "2026-09-26T15:00:00Z", "events": [
    {"id": "g1", "commence": KICK, "home": H, "away": A_, "bookmakers": [
        {"key": "hardrockbet", "markets": [
            {"key": "alternate_spreads", "outcomes": [o(H, -3.5, -150), o(A_, 3.5, 125), o(H, -10.5, 250),
                                                      o(A_, 10.5, -320), o(A_, 24.5, -2000)]},
            {"key": "alternate_totals", "outcomes": [o("Over", 44.5, -160), o("Under", 44.5, 130),
                                                     o("Over", 50.5, 140), o("Under", 50.5, -170)]}]},
        {"key": "draftkings", "markets": [
            {"key": "alternate_spreads", "outcomes": [o(H, -3.5, -145), o(A_, 3.5, 120)]}]}]},
    {"id": "g2", "commence": KICK2, "home": H2, "away": A2, "bookmakers": [
        {"key": "hardrockbet", "markets": [
            {"key": "alternate_spreads", "outcomes": [o(H2, -2.5, -140), o(A2, 2.5, 118)]}]}]}]})
DOC = G.build("nfl", root=tree, now=datetime.datetime(2026, 9, 26, 16, 0, tzinfo=UTC), log=lambda m: None)

DRIVER = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const a = html.indexOf('const FBGL = {}, FBGLREC = {};');
const b = html.indexOf('async function fbGameLinesTab(){');
if (a < 0 || b < 0 || b <= a){ console.error('TAB_CODE_NOT_FOUND'); process.exit(2); }
const sgn = v => v == null ? '—' : (v > 0 ? '+' + v : '' + v);
// [Sam, 2026-10-01] fbDayLine is deleted; the heading calls fbDayName(G.slate_date).
// Stubbed to echo its input, so the heading check can see WHICH date the page passed.
const fn = new Function('sgn', 'fbAb', 'fbMark', 'fbKickTime', 'fbDayName', 'jget', 'jgetGz', 'LG_DATA', 'LEAGUE',
  html.slice(a, b) + '\nreturn {fbGameLinesHtml, fbGlSort};');
const M = fn(sgn, n => n.split(' ').pop().slice(0, 3).toUpperCase(), () => '', () => '1:00 PM',
             d => 'DAY(' + d + ')', async () => null, async () => null, {nfl: 'data/nfl'}, 'nfl');
const doc = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const out = {};
for (const [k, st] of Object.entries({line: {market: 'both', sort: 'line'}, p: {market: 'both', sort: 'p'},
                                      sp: {market: 'spread', sort: 'edge'}}))
  out[k] = M.fbGameLinesHtml(doc, {markets: {}}, doc.games, st);
process.stdout.write(JSON.stringify(out));
"""
try:
    dp, jp = os.path.join(tree, "drive.js"), os.path.join(tree, "doc.json")
    open(dp, "w", encoding="utf-8").write(DRIVER)
    json.dump(DOC, open(jp, "w", encoding="utf-8"))
    r = subprocess.run(["node", dp, PAGE, jp], cwd=tree, timeout=300, capture_output=True, text=True)
    ck(r.returncode == 0, "⚠️ the shipped tab code ran in node", (r.stderr or "")[-400:])
    R = json.loads(r.stdout) if r.returncode == 0 else {"line": "", "p": "", "sp": ""}
finally:
    shutil.rmtree(tree, ignore_errors=True)

section("1. EVERY RUNG IS DRAWN, EACH BOOK NAMED FOR A PHONE")
rows = re.findall(r'<div class="glr(?: nofloor)?">(.*?)\n  </div>', R["line"], re.S)
n = DOC["n_rungs"]
ck(n == 11 and len(rows) == n,
   "🔴🔴 all %d rungs the books posted are drawn — no cap, no filter (%d rows)" % (n, len(rows)))
ck(all(all('data-l="%s"' % b in x for b in ("DraftKings", "FanDuel", "Hard Rock", "Best", "Break-even",
                                            "Books&rsquo; chance", "Model %", "Edge")) for x in rows)
   and all(x.index('data-l="Books&rsquo; chance"') < x.index('data-l="Model %"') for x in rows),
   "🔴 every row names each cell, so on a phone no price loses its label")
# [Sam, 2026-10-01] ~~a rung below -700 is drawn, marked as never paired~~ — the
#    "below −700 · never paired" chip was a per-row flag and is gone with the
#    rest. The rung is still DRAWN (no play is hidden), and the −700 floor still
#    decides pairing in the builder: the rung carries `floor: false`.
_low = [r for g in DOC["games"] for m in ("spread", "total") for r in g.get(m, []) if not r["floor"]]
ck(len(_low) == 1 and len(rows) == n
   and "&minus;700" not in R["line"] and "never paired" not in R["line"],
   "   ✅ a rung below -700 is still drawn, and carries no chip saying so",
   "rungs below the floor in the data: %d, rows drawn: %d of %d" % (len(_low), len(rows), n))

# [Sam, 2026-10-01] ~~2. RULE 55 AND THE CHECK'S LABEL, ON THE ROW~~ — the page
#    carries no MODEL / MARKET tag and no ⚠ on any tab now. Every check below
#    used to REQUIRE the chip, the warning or the note; each now requires it
#    ABSENT, asked of the same render, after confirming the builder still
#    writes it (the data keeps every kind, check and warning field).
section("2. THE HEADING AND THE NUMBERS — NO CHIP, NO WARNING, NO NOTE")
_h2 = re.search(r"<h2[^>]*>(.*?)</h2>", R["line"], re.S)
ck(_h2 is not None and DOC.get("slate_date")
   and _h2.group(1) == "Game Lines &mdash; DAY(%s)" % DOC["slate_date"],
   "✅ the heading names the tab and the slate's day, and nothing else",
   "the day sits in the heading in place of the deleted fbDayLine sentence: %r"
   % (_h2.group(1) if _h2 else None))
_hd = re.search(r'<div class="glr gh">(.*?)</div></div>', R["line"], re.S)
head = _hd.group(1) if _hd else ""
_cells = re.findall(r"<div>(.*?)</div>", head + "</div>")   # the match ate the last cell's close
# ~~prices and break-evens wear Market, the model's % and edge wear Model~~
ck(_cells == ["Line", "Books&rsquo; chance"] + list(DOC["books"]) + ["Best", "Break-even", "Model %", "Edge"]
   and 'class="kind' not in R["line"],
   "🔴 no column wears a chip — each header cell names its column and nothing else, and no chip anywhere on the tab",
   "header cells: %r" % _cells)
tot_rows = [x for x in rows if ("Over" in x or "Under" in x)]
sp_rows = [x for x in rows if x not in tot_rows]
_warned = lambda x: "glwarn" in x or "&#9888;" in x or "⚠" in x or G.A.WARNING in x  # noqa: E731
_rungs = [(m, r) for g in DOC["games"] for m in ("spread", "total") for r in g.get(m, [])]
_failed = [r for m, r in _rungs if (DOC["check"].get(m) or {}).get("state") != "PASS"]
# ~~every rung of a market that failed the check shows the warning ON ITS ROW~~
ck(tot_rows and _failed and all(r["cal"] is False and r.get("warn") for r in _failed)
   and not any(_warned(x) for x in tot_rows),
   "🔴🔴 no rung of a market that failed the check shows a warning on its row",
   "rows: %d, failed-market rungs the builder still marks cal=false with a warning: %d"
   % (len(tot_rows), len(_failed)))
# ~~and a rung that passed does not (the warning is the result, not decoration)~~
ck(sp_rows and any(r["cal"] for m, r in _rungs) and any(g.get("fair_total_warn") for g in DOC["games"])
   and not _warned(R["line"]),
   "   ✅ and no other line shows one either — not a rung that passed, not the model's fair lines")
# ~~the books' chance comes first, labelled Market, and the note says the model points the wrong way~~
_finding = ((DOC.get("check") or {}).get("total") or {}).get("finding") or ""
ck("Books&rsquo; chance" in head and "Model %" in head
   and head.index("Books&rsquo; chance") < head.index("Model %")
   and "points the wrong way away from the main line" in _finding
   and "points the wrong way away from the main line" not in R["line"]
   and 'class="note"' not in R["line"],
   "🔴 the books' chance still comes first, and no note says what the check found",
   "the finding stays in the data (check.total.finding): %r" % _finding[:90])
_par = R["line"][R["line"].find("Alt-line parlays"):]
_par = _par[:_par.find("Track record")] if "Track record" in _par else _par
_pl = [p for k in sorted(DOC.get("parlays") or {}) for p in (DOC["parlays"][k] or [])]
# ~~the alt parlays are drawn, wear Market, and show no model number~~
ck("Alt-line parlays" in R["line"] and 'class="kind' not in _par
   and 'k-market' not in _par and 'k-model' not in _par
   and "Model %" not in _par and "data-l=\"Books&rsquo; chance all land\"" in _par
   and 'class="note"' not in _par and not re.search(r"<p[\s>]", _par)
   and _pl and all(p.get("joint_note") for p in _pl) and not any(p["joint_note"] in _par for p in _pl),
   "🔴 the alt parlays are drawn with no chip, no note and no model number",
   R["line"][R["line"].find("Alt-line parlays")-100:][:1800])

section("3. THE SORT AND THE MARKET FILTER")
ps = [float(v) for v in re.findall(r'data-l="Model %">([\d.]+)%', R["p"])]
sp_ps = ps[:5]                      # the first game's spread ladder
ck(sp_ps == sorted(sp_ps, reverse=True) and len(sp_ps) == 5,
   "🔴 sorted by model %: each ladder reads highest first", "got %r" % sp_ps)
_lad = R["sp"].split("Alt-line parlays")[0]     # the parlays list is not filtered by market
ck("Over" not in re.sub(r"<[^>]+>", " ", _lad) and len(re.findall(r'data-l="Edge"', _lad)) == len(sp_rows),
   "   ✅ the market filter shows spreads only")

section("4. WIRED, AND IT FITS A PHONE")
ck("'props','gamelines'" in js_block("fbShell", PAGE).replace(" ", ""),
   "   ✅ the tab sits beside Player Props")
_wire = js_block("fbWire", PAGE)
_tab = js_block("fbGameLinesTab", PAGE)
ck("FBTAB === 'gamelines'" in _wire and "fbGameLinesTab()" in _wire and calls("fbGameLinesHtml", PAGE) >= 1
   and "gamelines:" in HTML[HTML.index("const FB_EMPTY = {"):HTML.index("const FB_EMPTY = {") + 2500],
   "🔴 the tab is ROUTED (every football render ends in fbWire) and its renderer CALLED — rule 130")
ck(_tab.count("data-gl") >= 3,
   "   ✅ every shell the tab draws carries data-gl, so its own fbWire() cannot loop")
_mq = re.search(r"@media\(max-width:600px\)\{(.*?)\n\}", HTML, re.S)
ck(bool(_mq) and ".glr.gh{display:none}" in _mq.group(1) and "content:attr(data-l)" in _mq.group(1),
   "🔴 on a phone the header folds away and every cell carries its own label")
