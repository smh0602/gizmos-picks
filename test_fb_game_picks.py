#!/usr/bin/env python3
"""
🔴 THE CARD'S GAME LINES ARE THE GAME MODEL'S PICKS, IN THE PROP ROW'S FORMAT.

`[Sam, 2026-10-01]` *"make the models gizmo picks game line picks the same
format as the player prop picks for gizmos picks"*, and *"include alternate
spreads ... that the model likes, now not a -1000 or anything that is a
gimme, ideally props/game lines at -400 is the lowest we should go"*. Asked
how alternate spreads are ranked, he chose the books' own odds, nothing
shorter than -400.

✅ `card_fb.card_game_lines`: fb-model.json's picks for the card's slate day,
one row per pick in the prop row's fields, ranked by confidence; plus ONE
alternate spread per game with a pulled ladder and a model spread pick: on
the model's side, the highest books' chance at -400 or longer, off the main
line, basis MARKET. The page draws every row with pickCard; record_fb grades
the alternate spreads once from the final score, in their own line.
Driven on planted data; the page through its own code in node.

# @vacuity 🔴 a spread row is on the team's own point
#   file: card_fb.py
#   find: line = -line if p.get("side") == "home" else line   # the team's own point
#   with: line = line   # the team's own point
#
# @vacuity 🔴 the rows are ranked by confidence, like the prop rows
#   file: card_fb.py
#   find: rows = sorted(rows + alt_spread_rows(rows, ladder), key=lambda r: -r["confidence"])
#   with: rows = sorted(rows + alt_spread_rows(rows, ladder), key=lambda r: r["confidence"])
#
# @vacuity 🔴 only the card's slate day
#   file: card_fb.py
#   find: if et_date(p.get("commence")) != slate:
#   with: if False:
#
# @vacuity 🔴 the alternate spread is on the model's side
#   file: card_fb.py
#   find: ok = [x for x in g.get("spread") or [] if x.get("side") == r["side"]
#   with: ok = [x for x in g.get("spread") or [] if True
#
# @vacuity 🔴 ...at -400 or longer
#   file: card_fb.py
#   find: and x.get("best") is not None and x["best"] >= PRICE_FLOOR
#   with: and x.get("best") is not None
#
# @vacuity 🔴 ...off the main line
#   file: card_fb.py
#   find: and x.get("mkt") is not None and x.get("pt") != main]
#   with: and x.get("mkt") is not None]
#
# @vacuity 🔴 ...with the highest books' chance
#   file: card_fb.py
#   find: x = max(ok, key=lambda x: (x["mkt"], x["best"]))
#   with: x = min(ok, key=lambda x: (x["mkt"], x["best"]))
#
# @vacuity 🔴 a game-line row names its team, with no side word
#   file: index.html
#   find: t.append(el('div','play', `${who}${gl ? '' : ' — ' + sideWord}${lineTxt} ${unit}`
#   with: t.append(el('div','play', `${who} — ${sideWord}${lineTxt} ${unit}`
#
# @vacuity 🔴 the page draws game-line rows with pickCard
#   file: index.html
#   find: + g.map(p => pickCard(p).outerHTML).join('');
#   with: + g.map(p => '<div class="r">' + p.player + '</div>').join('');
#
# @vacuity 🔴 the alternate spreads are graded in their own line
#   file: record_fb.py
#   find: if r.get("market") != "alternate_spread":
#   with: if False:
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

import card_fb as C  # noqa: E402
import game_lines_fb as GLF  # noqa: E402
import record_fb as R  # noqa: E402
from jsblock import js_block  # noqa: E402
from tcheck import ck, section  # noqa: E402

SLATE = "2026-10-04"
G1 = {"id": "ev1", "away": "Away A", "home": "Home H", "commence": "2026-10-04T17:00:00Z"}
G2 = {"id": "ev2", "away": "Away B", "home": "Home J", "commence": "2026-10-04T20:25:00Z"}
G3 = {"id": "ev3", "away": "Away C", "home": "Home K", "commence": "2026-10-04T23:00:00Z"}


def pick(g, mk, side, team, line, price, prob, be):
    L = lambda v, b: {"value": v, "basis": b}
    return {"game": "%s at %s" % (g["away"], g["home"]), "game_id": "nfl_" + g["id"],
            "commence": g["commence"], "market": mk, "side": side, "team": team,
            "book": "FanDuel", "line": L(line, "MARKET"), "price": L(price, "MARKET"),
            "model_probability": L(prob, "MODEL"), "break_even": L(be, "MARKET"),
            "edge": L(1.0, "MODEL"), "priced_at": "2026-10-03T12:00:00Z"}


PICKS = [pick(G1, "spread", "home", "Home H", -3.5, 100, 56.0, 50.0),     # M -3.5: Home H +3.5
         pick(G1, "moneyline", "away", "Away A", None, 150, 45.0, 40.0),
         pick(G1, "total", "over", "Over", 47.5, -110, 55.5, 52.4),
         pick(G2, "spread", "away", "Away B", 6.5, -105, 54.0, 51.2),       # M 6.5: Away B +6.5
         pick(G3, "spread", "home", "Home K", 2.5, -110, 53.0, 52.4),       # no ladder: no alt row
         pick(G1, "moneyline", "home", "Home H", None, -450, 85.0, 81.8),   # shorter than -400
         dict(pick(G1, "total", "under", "Under", 44.5, -110, 60.0, 52.4),
              commence="2026-10-06T00:15:00Z")]                             # another day


def rung(side, pt, best, mkt):
    return {"m": "spread", "side": side, "pt": pt, "best": best, "book": "DraftKings",
            "mkt": mkt, "be": round(100 * C.american_break_even(best), 1)}


LADDER = {"games": [
    dict(G1, sched_id="S1", main_spread_home=3.5,
         spread=[rung("home", 3.5, -110, 52), rung("home", 6.5, -250, 72),
                 rung("home", 7.5, -300, 75), rung("home", 8.5, -400, 77),
                 rung("home", 9.5, -401, 78), rung("home", 10.5, -450, 82),
                 rung("away", -0.5, 100, 95)]),
    dict(G2, sched_id="S2", main_spread_home=-6.5,
         spread=[rung("away", 6.5, -110, 51), rung("away", 13.5, -500, 85)])]}
ROWS = C.card_game_lines(PICKS, [G1, G2, G3], LADDER, SLATE)
MODEL = [r for r in ROWS if r["market"] != "alternate_spread"]
ALT = [r for r in ROWS if r["market"] == "alternate_spread"]
FIELDS = ("player", "market_label", "side", "line", "game", "commence", "book", "price",
          "link", "confidence", "break_even", "edge", "why", "rank")

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE MODEL'S PICKS, ONE ROW EACH, IN THE PROP ROW'S FIELDS")
# ══════════════════════════════════════════════════════════════════════
_want = {("Home H", "spread", 3.5, 100, 56.0, 50.0), ("Away A", "moneyline", None, 150, 45.0, 40.0),
         ("Over", "total", 47.5, -110, 55.5, 52.4), ("Away B", "spread", 6.5, -105, 54.0, 51.2),
         ("Home K", "spread", -2.5, -110, 53.0, 52.4)}
_got = {(r["player"], r["market"], r["line"], r["price"], r["confidence"], r["break_even"])
        for r in MODEL}
ck("🔴 the card's game-line rows are the model's picks for the slate day, at -400 or longer, "
   "with the prop-row fields and the team's own point",
   _got == _want and len(MODEL) == 5
   and all(all(k in r for k in FIELDS) and r["book"] == "fanduel" and r["kind"] == "fb-line"
           and r["confidence_basis"] == "MODEL" and r["edge"] == round(r["confidence"] - r["break_even"], 1)
           and r["game"] == "%s @ %s" % (r["away"], r["home"]) and r["why"] for r in MODEL)
   and {r["game_id"] for r in MODEL} == {"ev1", "ev2", "ev3"},
   "got %s" % sorted(_got, key=str))
ck("🔴 ...ranked by confidence, like the prop rows",
   [r["rank"] for r in ROWS] == list(range(1, len(ROWS) + 1))
   and all(ROWS[i]["confidence"] >= ROWS[i + 1]["confidence"] for i in range(len(ROWS) - 1)),
   str([(r["rank"], r["confidence"]) for r in ROWS]))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 ONE ALTERNATE SPREAD: MODEL'S SIDE, -400 OR LONGER, HIGHEST BOOKS' CHANCE")
# ══════════════════════════════════════════════════════════════════════
_a = ALT[0] if len(ALT) == 1 else {}
ck("🔴 an alternate-spread row is on the model's side, at -400 or longer, off the main line, "
   "with the highest books' chance of the eligible rungs; none without a rung or a ladder",
   len(ALT) == 1 and (_a["player"], _a["side"], _a["line"], _a["price"], _a["confidence"]) ==
   ("Home H", "home", 8.5, -400, 77) and _a["confidence_basis"] == "MARKET"
   and _a["basis"].startswith("MARKET") and _a["market_label"] == "Alternate spread"
   and _a["book"] == "draftkings" and all(k in _a for k in FIELDS),
   "alt rows %s" % [(r["player"], r["line"], r["price"], r["confidence"]) for r in ALT])

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE PAGE DRAWS THEM WITH THE PROP ROWS' OWN MARKUP")
# ══════════════════════════════════════════════════════════════════════
PAGE = os.path.join(ROOT, "index.html")
_el = next(l for l in open(PAGE, encoding="utf-8").read().splitlines() if l.startswith("const el = "))
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
  S.el + '\n' + S.pc + '\n' + S.gl + '\nreturn fbGameLines;');
const fbGameLines = fn(document, stub, stub, stub, stub, stub, x => (x > 0 ? '+' : '') + x,
  stub, stub, stub, stub, stub, {}, 'nfl');
process.stdout.write(JSON.stringify(fbGameLines({game_lines: S.rows}).replace(/\s+/g, ' ')));
"""
tmp = tempfile.mkdtemp(prefix="fbgl-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"el": _el, "pc": js_block("pickCard", PAGE), "gl": js_block("fbGameLines", PAGE),
               "rows": ROWS}, open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=300)
    HTML = json.loads(r.stdout) if r.returncode == 0 else ""
finally:
    shutil.rmtree(tmp, ignore_errors=True)
_plays = ["Home H +8.5 Alternate spread", "Home H +3.5 Spread", "Over 47.5 Total",
          "Away B +6.5 Spread", "Home K -2.5 Spread", "Away A Moneyline"]
ck("🔴 the page draws each game-line row with pickCard: its team or Over/Under, no side word",
   r.returncode == 0 and HTML.count("<pk>") == len(ROWS) and all(p in HTML for p in _plays)
   and not re.search(r" — (Over|Under|Yes)\b", HTML) and "Game lines" in HTML,
   (r.stderr or "")[-200:] + HTML[:300])

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE ALTERNATE SPREADS ARE GRADED IN THEIR OWN LINE")
# ══════════════════════════════════════════════════════════════════════
_rec = R.grade_alt_spreads([("f", {"date": SLATE, "league": "nfl", "game_lines": ROWS})],
                           {"S1": {"final": True, "home_score": 15, "away_score": 20}},
                           GLF.grade_rung)
ck("🔴 the alternate spreads are graded once from the final score, in their own line, "
   "and nothing else on the card is",
   _rec["shown"] == 1 and _rec["overall"]["w"] == 1 and _rec["overall"]["n"] == 1
   and _rec["rows"][0]["won"] is True and _rec["basis"] == "MARKET",
   "Home H +8.5, lost 15-20 by 5: covers. got %s" % {k: _rec[k] for k in ("shown", "overall")})
