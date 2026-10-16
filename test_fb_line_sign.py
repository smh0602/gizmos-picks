#!/usr/bin/env python3
r"""test_fb_line_sign.py — a model pick's spread prints as the TEAM'S OWN point, signed.

`[2026-10-16]` An independent recheck of the rebuilt cards found the football "Model
picks" table and "What the model showed, graded" printing every HOME spread pick with
the wrong sign: fb_model stores a spread pick's `line` as the threshold on the home
margin (M = -home point), and the page printed it raw beside the team — "Cleveland
Browns -3.5" for Cleveland +3.5 (a +180 underdog), "Kansas City Chiefs 8.5" for KC
-8.5; 7 NFL and 26 college picks that day. The card itself was right
(card_fb.model_game_rows flips it). The class: a stored line printed raw. The SHIPPED
page code runs in node on planted picks; and no code in index.html may print a stored
`line.value` raw again. ⛔ Reads no live data.

# @vacuity 🔴 a HOME spread pick's own point is -M
#   file: index.html
#   find:   const pt = p.side === 'home' ? -v : v;
#   with:   const pt = v;
#
# @vacuity 🔴 a spread point carries its sign ("+3.5", never a bare "3.5")
#   file: index.html
#   find:   return (pt > 0 ? '+' : '') + String(pt === 0 ? 0 : pt);
#   with:   return String(pt);
#
# @vacuity 🔴 a total or a prop prints its line as stored, unsigned
#   file: index.html
#   find:   if (!/spread/.test(String(p.market || ''))) return String(v);
#   with:   if (false) return String(v);
#
# @vacuity 🔴 Model picks prints through fbPointText
#   file: index.html
#   find:       <td>${fbPointText(p) ?? ''}</td>
#   with:       <td>${p.line && p.line.value != null ? labN(p.line) : ''}</td>
#
# @vacuity 🔴 the ledger prints through fbPointText
#   file: index.html
#   find: const fbLedgerPoint = p => fbPointText(p) != null ? ' ' + fbPointText(p) : '';   // the ledger's line, signed
#   with: const fbLedgerPoint = p => p.line && p.line.value != null ? ' ' + p.line.value : '';   // the ledger's line, signed
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
import jsblock  # noqa: E402
from tcheck import ck, eq, section, shown  # noqa: E402

IDX = os.path.join(ROOT, "index.html")
BLOCKS = ["labN", "fbEsc", "fbKickDate", "fbKickTime", "fbVerdictTag", "fbPointText",
          "fbModelHtml", "fbLedgerHtml", "fbPropModelHtml"]


def L(v):
    return {"value": v, "basis": "MARKET"}


def gm(team, side, market, line):
    return {"game": "X at Y", "commence": "2026-10-18T17:00:00Z", "market": market, "team": team, "side": side,
            "line": L(line) if line is not None else None, "price": L(-110), "book": "fd",
            "model_probability": {"value": 60.0, "basis": "MODEL"}, "break_even": {"value": 52.4, "basis": "MARKET"}}


M = {"built_at": "t", "record": {}, "picks": [
    gm("Cleveland Browns", "home", "spread", -3.5), gm("Kansas City Chiefs", "home", "spread", 8.5),
    gm("Houston Texans", "away", "spread", 2.5), gm("Las Vegas Raiders", "away", "spread", -4.5),
    gm("Over", "over", "total", 53.5), gm("New York Giants", "home", "moneyline", None)]}
LD = {"built_at": "t", "record": {}, "picks": [
    dict(gm("Cleveland Browns", "home", "spread", -3.5), model="game_model", state="pending"),
    dict(gm("Under", "under", "total", 48.5), model="game_model", state="pending"),
    {"model": "props_model", "player": "Some Back", "game": "X at Y", "commence": "2026-10-18T17:00:00Z",
     "market": "player_rush_yds", "market_label": "Rush yds", "side": "over", "line": L(47.5),
     "price": L(-110), "state": "pending"}]}
PM = {"built_at": "t", "record": {}, "picks": [
    {"player": "Some Back", "game": "X at Y", "commence": "2026-10-18T17:00:00Z", "market": "player_rush_yds",
     "market_label": "Rush yds", "side": "under", "line": L(66.5), "price": L(-113), "book": "dk",
     "model_probability": {"value": 54.0, "basis": "MODEL"}, "break_even": {"value": 53.1, "basis": "MARKET"}}]}

js = "\n".join(jsblock.js_block(b, IDX) for b in BLOCKS)
_lp = re.search(r"^const fbLedgerPoint = .*$", open(IDX, encoding="utf-8").read(), re.M)
ck(_lp is not None, "⚠️ the ledger's line helper was found in the page", "")
js += "\n" + (_lp.group(0) if _lp else "")
driver = """
const LEAGUE = 'nfl', FBAG = {};
const etDate = s => String(s).slice(0, 10);   // dates are not under test here
function fbAgHtml(){ return ''; }
function fbAgFind(){ return null; }
%s
const D = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const cells = h => [...h.matchAll(/<td[^>]*>([\\s\\S]*?)<\\/td>/g)].map(m => m[1].replace(/<[^>]+>/g, '').trim());
console.log(JSON.stringify({
  points: D.M.picks.map(p => fbPointText(p)),
  model: cells(fbModelHtml(D.M)), ledger: cells(fbLedgerHtml(D.LD)), props: cells(fbPropModelHtml(D.PM))}));
""" % js
tmp = tempfile.mkdtemp(prefix="linesign-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(driver)
    json.dump({"M": M, "LD": LD, "PM": PM}, open(os.path.join(tmp, "d.json"), "w", encoding="utf-8"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, encoding="utf-8")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
ck(r.returncode == 0, "⚠️ the page's own code ran in node", shown((r.stderr or "")[-400:]))
out = json.loads(r.stdout) if r.returncode == 0 else {"points": [], "model": [], "ledger": [], "props": []}

section("1. 🔴 THE TEAM'S OWN POINT, SIGNED")
eq(out["points"], ["+3.5", "-8.5", "+2.5", "-4.5", "53.5", None],
   "🔴 home picks flip (Cleveland M -3.5 -> +3.5, Kansas City M 8.5 -> -8.5), away picks keep theirs, "
   "every spread carries its sign; a total prints as stored; a moneyline has none")

section("2. 🔴 EVERY MODEL TABLE PRINTS IT")
ck("+3.5" in out["model"] and "-8.5" in out["model"] and "-3.5" not in out["model"] and "8.5" not in out["model"],
   "🔴 Model picks: Cleveland +3.5 and Kansas City -8.5, never the stored -3.5 / 8.5", out["model"])
ck("53.5" in out["model"], "   ...and the total at 53.5")
ck(any(c.endswith("Home +3.5") for c in out["ledger"]) and not any(c.endswith("Home -3.5") for c in out["ledger"]),
   "🔴 the ledger: Cleveland's pick reads 'Home +3.5'", out["ledger"])
ck(any(c.endswith("Under 48.5") for c in out["ledger"]) and any(c.endswith("Over 47.5") for c in out["ledger"]),
   "   ...a total and a prop as stored", out["ledger"])
ck("Under 66.5" in out["props"], "   Prop model picks: 'Under 66.5' as stored", out["props"])

section("3. 🔴 THE CLASS: NO STORED LINE PRINTED RAW ANYWHERE ON THE PAGE")
src = open(IDX, encoding="utf-8").read()
body = jsblock.js_block("fbPointText", IDX)
raw = [m.group(0) for m in re.finditer(r"labN\(\s*\w+\.line\s*\)|\w+\.line\.value", src.replace(body, ""))]
eq(raw, [], "🔴 outside fbPointText, index.html prints no `x.line.value` and no `labN(x.line)` "
            "(a stored model line printed raw is how the wrong sign shipped)")
