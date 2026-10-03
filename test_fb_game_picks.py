#!/usr/bin/env python3
"""
🔴 THE CARD'S GAME LINES ARE THE GAME MODEL'S PICKS, IN THE PROP ROW'S FORMAT.

`[Sam, 2026-10-01]` *"make the models gizmo picks game line picks the same
format as the player prop picks for gizmos picks"*, and *"include alternate
spreads ... that the model likes, now not a -1000 or anything that is a
gimme, ideally props/game lines at -400 is the lowest we should go"*; ranked
on the books' own odds. `[Sam, 2026-10-03]` *only picks the model gives 50%
or more*, and *the top 25, like the props board*.

✅ `card_fb.card_game_lines`: fb-model.json's picks for ONE day (main passes
`next_line_slate`'s: test_game_lines_day.py §5), 50% or more, -400 or longer,
whole-number confidence, the 25 highest; each spread pick followed by ONE
alternate spread (model's side, highest books' chance at -400 or longer and
50% or more, off the main line, basis MARKET). A row that is not the model's
never stays in `game_lines` and is never drawn. record_fb grades the
alternate spreads once, in their own line. Planted data; the page in node.

# @vacuity 🔴 a spread row is on the team's own point
#   file: card_fb.py
#   find: line = -line if p.get("side") == "home" else line   # the team's own point
#   with: line = line   # the team's own point
#
# @vacuity 🔴 the model rows are the highest-confidence ones, in order
#   file: card_fb.py
#   find: key=lambda r: (-(r.get("confidence") or 0), -(r.get("edge") or 0)))
#   with: key=lambda r: ((r.get("confidence") or 0), (r.get("edge") or 0)))
#
# @vacuity 🔴 only one day
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
#   find: and x.get("mkt") is not None and x.get("pt") != main
#   with: and x.get("mkt") is not None
#
# @vacuity 🔴 ...with the highest books' chance
#   file: card_fb.py
#   find: x = max(ok, key=lambda x: (x["mkt"], x["best"]))
#   with: x = min(ok, key=lambda x: (x["mkt"], x["best"]))
#
# @vacuity 🔴 no model row under 50%
#   file: card_fb.py
#   find: if None in (v["price"], pr) or v["price"] < PRICE_FLOOR or pr < GL_MIN_CONF:
#   with: if None in (v["price"], pr) or v["price"] < PRICE_FLOOR:
#
# @vacuity 🔴 no alternate spread under 50%
#   file: card_fb.py
#   find: and x["mkt"] >= GL_MIN_CONF]
#   with: ]
#
# @vacuity 🔴 at most 25 model rows
#   file: card_fb.py
#   find: GAME_LINES_MAX = BOARD_MAX
#   with: GAME_LINES_MAX = 10 ** 6
#
# @vacuity 🔴 an alternate spread only under its own listed pick
#   file: card_fb.py
#   find: out += [a for a in alt.values() if id(a) in keep]    # published, never dropped
#   with: out += list(alt.values())
#
# @vacuity 🔴 ...placed directly under it
#   file: card_fb.py
#   find: a = alt.pop((r.get("game"), r.get("side")), None) if r.get("market") == "spread" else None
#   with: a = None
#
# @vacuity 🔴 confidence is a whole number, like the prop rows
#   file: card_fb.py
#   find: conf, be = int(round(pr)), v["break_even"]      # a whole number, like the prop rows
#   with: conf, be = pr, v["break_even"]
#
# @vacuity 🔴 an old-format row never stays in game_lines
#   file: card_fb.py
#   find: if (d and d != _gl_day) or not ours:
#   with: if d and d != _gl_day:
#
# @vacuity 🔴 ...and the page never draws one
#   file: index.html
#   find: const g = ((C && C.game_lines) || []).filter(p => p.kind === 'fb-line');
#   with: const g = (C && C.game_lines) || [];
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


def game(n, at="2026-10-04T17:00:00Z"):
    return {"id": "ev%s" % n, "away": "Away %s" % n, "home": "Home %s" % n, "commence": at}


def pick(g, mk, side, team, line, price, prob, be):
    L = lambda v: {"value": v}
    return {"game": "%s at %s" % (g["away"], g["home"]), "commence": g["commence"],
            "market": mk, "side": side, "team": team, "book": "FanDuel", "line": L(line),
            "price": L(price), "model_probability": L(prob), "break_even": L(be)}


def rung(side, pt, best, mkt):
    return {"m": "spread", "side": side, "pt": pt, "best": best, "book": "DraftKings",
            "mkt": mkt, "be": round(100 * C.american_break_even(best), 1)}


G1, G2, G3, G4 = game("A"), game("B"), game("C"), game("D")
PICKS = [pick(G1, "spread", "home", "Home A", -3.5, 100, 56.0, 50.0),     # M -3.5: Home A +3.5
         pick(G1, "total", "over", "Over", 47.5, -110, 55.5, 52.4),
         pick(G2, "spread", "away", "Away B", 6.5, -105, 54.0, 51.2),       # M 6.5: Away B +6.5
         pick(G3, "spread", "home", "Home C", 2.5, -110, 53.0, 52.4),       # no ladder: no alt
         pick(G4, "spread", "away", "Away D", 1.5, -110, 52.0, 52.4),       # alt rungs all < 50%
         pick(G1, "moneyline", "away", "Away A", None, 150, 45.0, 40.0),    # under 50%
         pick(G1, "moneyline", "home", "Home A", None, -450, 85.0, 81.8),   # shorter than -400
         dict(pick(G1, "total", "under", "Under", 44.5, -110, 60.0, 52.4),
              commence="2026-10-06T00:15:00Z")]                             # another day
LADDER = {"games": [
    dict(G1, sched_id="S1", main_spread_home=3.5,
         spread=[rung("home", 3.5, -110, 52), rung("home", 7.5, -300, 75),
                 rung("home", 8.5, -400, 77), rung("home", 9.5, -401, 78),
                 rung("away", -0.5, 100, 95)]),
    dict(G2, sched_id="S2", main_spread_home=-6.5,
         spread=[rung("away", 6.5, -110, 51), rung("away", 13.5, -500, 85)]),
    dict(G4, sched_id="S4", main_spread_home=-1.5,
         spread=[rung("away", 1.5, -110, 51), rung("away", -2.5, 150, 38)])]}
ROWS = C.card_game_lines(PICKS, [G1, G2, G3, G4], LADDER, SLATE)
MODEL = [r for r in ROWS if r["market"] != "alternate_spread"]
ALT = [r for r in ROWS if r["market"] == "alternate_spread"]
FIELDS = ("player", "market_label", "side", "line", "game", "commence", "book", "price",
          "link", "confidence", "break_even", "edge", "why", "rank")

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE MODEL'S PICKS FOR ONE DAY, 50% OR MORE, IN THE PROP ROW'S FIELDS")
# ══════════════════════════════════════════════════════════════════════
_want = {("Home A", "spread", 3.5, 56), ("Over", "total", 47.5, 56), ("Away B", "spread", 6.5, 54),
         ("Home C", "spread", -2.5, 53), ("Away D", "spread", 1.5, 52)}
ck("🔴 the card's game-line rows are the model's picks for the day, -400 or longer, with "
   "the prop-row fields and the team's own point",
   {(r["player"], r["market"], r["line"], r["confidence"]) for r in MODEL} == _want
   and all(all(k in r for k in FIELDS) and r["book"] == "fanduel" and r["kind"] == "fb-line"
           and r["confidence_basis"] == "MODEL" and r["why"] for r in MODEL)
   and {r["game_id"] for r in MODEL} == {"evA", "evB", "evC", "evD"},
   str(sorted((r["player"], r["market"], r["line"], r["confidence"]) for r in MODEL)))
ck("🔴 no game-line row under 50%, model or alternate", ROWS and min(r["confidence"] for r in ROWS) >= 50
   and not [r for r in ALT if r["game"] == "Away D @ Home D"],
   str([(r["player"], r["confidence"]) for r in ROWS]))
ck("🔴 confidence is a whole number, like the prop rows; the edge keeps the exact chance",
   all(isinstance(r["confidence"], int) for r in ROWS)
   and [r["edge"] for r in MODEL if r["player"] == "Over"] == [3.1],
   str([(r["player"], r["confidence"], r["edge"]) for r in ROWS]))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 ONE ALTERNATE SPREAD, DIRECTLY UNDER ITS OWN PICK")
# ══════════════════════════════════════════════════════════════════════
_a = ALT[0] if len(ALT) == 1 else {}
ck("🔴 an alternate-spread row is on the model's side, at -400 or longer, off the main line, "
   "with the highest books' chance of the eligible rungs; none without one or a ladder",
   len(ALT) == 1 and (_a["player"], _a["side"], _a["line"], _a["price"], _a["confidence"]) ==
   ("Home A", "home", 8.5, -400, 77) and _a["confidence_basis"] == "MARKET"
   and _a["basis"].startswith("MARKET") and _a["book"] == "draftkings",
   "alt rows %s" % [(r["player"], r["line"], r["price"], r["confidence"]) for r in ALT])
_order = [(r["player"], r["market"]) for r in ROWS]
ck("🔴 model rows by confidence, each spread pick followed directly by its alternate",
   _order == [("Home A", "spread"), ("Home A", "alternate_spread"), ("Over", "total"),
              ("Away B", "spread"), ("Home C", "spread"), ("Away D", "spread")]
   and [r["rank"] for r in ROWS] == list(range(1, len(ROWS) + 1)), str(_order))
_many = [game(i) for i in range(30)]
_big = C.card_game_lines(
    [pick(g, "spread", "home", g["home"], -3.5, -110, 60.0 + i + 0.1, 52.4)
     for i, g in enumerate(_many)], _many,
    {"games": [dict(g, main_spread_home=3.5, spread=[rung("home", 7.5, -300, 75)]) for g in _many]},
    SLATE)
_bm = [r for r in _big if r["market"] == "spread"]
ck("🔴 at most 25 model rows, the highest-confidence ones",
   len(_bm) == C.GAME_LINES_MAX == 25 and {r["player"] for r in _bm} ==
   {g["home"] for g in _many[5:]}, "%d rows: %s" % (len(_bm), [r["confidence"] for r in _bm]))
ck("🔴 an alternate spread only under its own listed pick",
   all(_big[i + 1]["market"] == "alternate_spread" and _big[i + 1]["game"] == r["game"]
       for i, r in enumerate(_big) if r["market"] == "spread")
   and len(_big) == 2 * len(_bm), "%d rows for %d picks" % (len(_big), len(_bm)))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 AN OLDER CARD'S PRICE-GAP ROW NEVER STAYS, AND IS NEVER DRAWN")
# ══════════════════════════════════════════════════════════════════════
OLD = {"kind": "MARKET", "game": "Away A @ Home A", "game_id": "evA", "commence": G1["commence"],
       "market": "spreads", "side": "Home A", "point": 3.5, "best_price": -105,
       "best_book": "fanduel", "gain_pct": 2.1}
_t = tempfile.mkdtemp(prefix="fbgl-old-")
try:
    _pub = os.path.join(_t, "fb-nfl-latest.json")
    json.dump({"date": SLATE, "game_lines_meta": {"slate": SLATE}, "game_lines": [OLD]},
              open(_pub, "w", encoding="utf-8"))
    _fz, _ = C.freeze_published({"date": SLATE, "game_lines": [dict(r) for r in ROWS],
                                 "game_lines_meta": {"source": "fb-model.json", "slate": SLATE}},
                                _pub, "2026-10-04T18:00:00Z", log=lambda *a, **k: None)
finally:
    shutil.rmtree(_t, ignore_errors=True)
ck("🔴 an old-format row never stays in game_lines: it goes to the archive untouched",
   all(r.get("kind") == "fb-line" for r in _fz["game_lines"])
   and OLD in (_fz.get(C.GL_EARLIER) or {}).get(SLATE, []), str(_fz.get(C.GL_EARLIER)))

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
  S.el + '\n' + S.dn + '\n' + S.pc + '\n' + S.gl + '\nreturn fbGameLines;');
const fbGameLines = fn(document, stub, stub, stub, stub, stub, x => (x > 0 ? '+' : '') + x,
  stub, stub, stub, stub, stub, {}, 'nfl');
process.stdout.write(JSON.stringify(fbGameLines(S.card).replace(/\s+/g, ' ')));
"""
tmp = tempfile.mkdtemp(prefix="fbgl-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"el": _el, "dn": js_block("fbDayName", PAGE), "pc": js_block("pickCard", PAGE),
               "gl": js_block("fbGameLines", PAGE),
               "card": {"game_lines": ROWS + [OLD], "game_lines_meta": {"slate": SLATE}}},
              open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=300)
    HTML = json.loads(r.stdout) if r.returncode == 0 else ""
finally:
    shutil.rmtree(tmp, ignore_errors=True)
ck("🔴 ...and the page never draws one", r.returncode == 0 and "undefined" not in HTML
   and HTML.count("<pk>") == len(ROWS), (r.stderr or "")[-200:] + HTML[:200])
_plays = ["Home A +8.5 Alternate spread", "Home A +3.5 Spread", "Over 47.5 Total",
          "Away B +6.5 Spread", "Home C -2.5 Spread", "Away D +1.5 Spread"]
ck("🔴 the page draws each game-line row with pickCard under a heading naming its day: "
   "its team or Over/Under, no side word",
   all(p in HTML for p in _plays) and not re.search(r" — (Over|Under|Yes)\b", HTML)
   and "Game lines &mdash; " in HTML, HTML[:300])

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
   "Home A +8.5, lost 15-20 by 5: covers. got %s" % {k: _rec[k] for k in ("shown", "overall")})
