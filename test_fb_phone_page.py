#!/usr/bin/env python3
"""test_fb_phone_page.py — the football tabs, `[Sam, 2026-10-14]`: "look at every
aspect of the github repo, and the website and your only goal is to do anything to
make it better"; and "the way i want you to predict outcomes of football games is
by predicted scores".

Planted rows, a pinned clock, the SHIPPED page code in node. ⛔ Reads no live data.
  1. a football row whose card edge is <= 0 carries `below_price`; the page prints
     its %, break-even and edge, once, in its own line; ~~a row above its price adds
     the edge to the break-even line; MLB's line is unchanged~~ `[Sam, 2026-10-17]`
     "i like the light blue on i think that oone is good" (design I, one row for all
     three leagues): every row above its price prints "Break-even x%" and "Edge +y",
     MLB too, the edge green only above zero
  2. ~~"Above their price only" hides exactly the rows with edge <= 0, and nothing
     while off (the default, also when storage throws)~~ `[Sam, 2026-10-17]` "no above
     their price only button in gizmos pikcs not needed": the button, its switch and its
     storage are gone from the page; the board shows the card's liked lists whenever the
     card has them, and every row the card lists, at any edge
  3. Game Lines lists every planted game of the week, grouped by ET day, "ET" times
  4. the predicted score is the FULL model's (margin = sigma x NormalInverse of
     the chance shown): the higher score is always the pick's, 50% is a tie, a
     bigger chance a bigger margin; picks and chances byte-identical without it
  5. the phone layout's rules are in the page (the WEAK half; the 390 px
     measurement is test_league_switch.py §3, in a browser)

# @vacuity 🔴 a row at or below its price carries below_price
#   file: card_fb.py
#   find:         if r.get("edge") is not None and r["edge"] <= 0:
#   with:         if r.get("edge") is not None and r["edge"] < 0:
#
# @vacuity 🔴 [Sam, 2026-10-17] a row below its price prints its numbers once, in its C8 line (~~the edge joins the break-even line only on a row above its price~~)
#   file: index.html
#   find:   if (!p.below_price && (p.break_even != null || p.edge != null))
#   with:   if (p.break_even != null || p.edge != null)
#
# @vacuity 🔴 [Sam, 2026-10-17] every row above its price prints its break-even and edge, MLB's too (~~the props board adds the edge line~~)
#   file: index.html
#   find:   if (!p.below_price && (p.break_even != null || p.edge != null))
#   with:   if (p.kind !== 'hitter' && !p.below_price && (p.break_even != null || p.edge != null))
#
# @vacuity 🔴 [Sam, 2026-10-17] the edge is green only above zero
#   file: index.html
#   find:   + (p.edge != null ? `<div>Edge <b${p.edge > 0 ? ' class="eg-pos"' : ''}>${
#   with:   + (p.edge != null ? `<div>Edge <b${p.edge != null ? ' class="eg-pos"' : ''}>${
#
# @vacuity 🔴 [Sam, 2026-10-17] no board patches a row afterwards: the props board draws pickCard's own row
#   file: index.html
#   find:   kept.forEach(p => host.append(pickCard(p)));
#   with:   kept.forEach(p => host.append(fbEdgeLine(pickCard(p), p)));
#
# @vacuity 🔴 [Sam, 2026-10-17] ...and the game lines draw it too
#   file: index.html
#   find:   + g.map(p => pickCard(p).outerHTML).join('');
#   with:   + g.map(p => fbEdgeLine(pickCard(p), p).outerHTML).join('');
#
# `[Sam, 2026-10-17]` the next three were ~~"the filter hides exactly the rows with edge <= 0"~~,
#    ~~"the filter is ON by default [Sam, 2026-10-15]"~~ and ~~"the props board runs through the
#    filter"~~; each now re-adds the removed filter or button, and section 2 must go red.
# @vacuity 🔴 [Sam, 2026-10-17] the game lines draw every row the card lists (re-adds the edge <= 0 filter)
#   file: index.html
#   find:   const g = ((C && C.game_lines) || []).filter(p => p.kind === 'fb-line');
#   with:   const g = ((C && C.game_lines) || []).filter(p => p.kind === 'fb-line' && !(p.edge != null && p.edge <= 0));
#
# @vacuity 🔴 [Sam, 2026-10-17] no "Above their price only" button in the kind bar (re-adds it)
#   file: index.html
#   find:     chip('lines', 'Game lines', nLines)}</div>`;
#   with:     chip('lines', 'Game lines', nLines)}<button class="kchip on" data-fbabove>Above their price only</button></div>`;
#
# @vacuity 🔴 [Sam, 2026-10-17] the props board shows every row the card lists (re-adds the edge <= 0 filter)
#   file: index.html
#   find:   const kept = inConf;
#   with:   const kept = inConf.filter(p => !(p && p.edge != null && p.edge <= 0));
#
# @vacuity 🔴 the week lists every game in the win chances
#   file: winners.py
#   find:             if slate is None or et_date(g["commence"]) == slate]
#   with:             if et_date(g["commence"]) == slate]
#
# @vacuity 🔴 kickoff times are ET, with "ET" written
#   file: index.html
#   find:       <td>${r.away} @ ${r.home}</td><td>${fbKickTime(r.commence)}</td>
#   with:       <td>${r.away} @ ${r.home}</td><td>${new Date(r.commence).toLocaleTimeString()}</td>
#
# @vacuity 🔴 the higher predicted score is the pick's team
#   file: fb_model.py
#   find:     margin = sigma * statistics.NormalDist().inv_cdf(min(1 - 1e-9, max(1e-9, p_home)))
#   with:     margin = -sigma * statistics.NormalDist().inv_cdf(min(1 - 1e-9, max(1e-9, p_home)))
#
# @vacuity 🔴 [Sam, 2026-10-16] the predicted score is printed to the decimal its picks are judged on
#   file: index.html
#   find:     ? `${fbAb(r.away)} ${Number(r.score.away).toFixed(1)} &ndash; ${fbAb(r.home)} ${Number(r.score.home).toFixed(1)}`
#   with:     ? `${fbAb(r.away)} ${Math.round(r.score.away)} &ndash; ${fbAb(r.home)} ${Math.round(r.score.home)}`
#
# @vacuity 🔴 [Sam, 2026-10-17] the tab prints the whole-number score that never contradicts a pick
#   file: index.html
#   find:     ? `${fbAb(r.away)} ${r.score_shown.away} &ndash; ${fbAb(r.home)} ${r.score_shown.home}`
#   with:     ? `${fbAb(r.away)} ${Math.round(r.score.away)} &ndash; ${fbAb(r.home)} ${Math.round(r.score.home)}`
#
# @vacuity 🔴 ...which winners.json carries from the card for every game of the week
#   file: winners.py
#   find:                  score=g.get("score"), score_shown=whole.get((g["away"], g["home"])))
#   with:                  score=g.get("score"), score_shown=None)
#
# @vacuity 🔴 a 50% chance is a tied score
#   file: fb_model.py
#   find:     return {"home": round((ot + margin) / 2.0, 1), "away": round((ot - margin) / 2.0, 1)}
#   with:     return {"home": round((ot + margin) / 2.0 + 0.5, 1), "away": round((ot - margin) / 2.0, 1)}
#
# @vacuity 🔴 a larger chance gives a larger margin
#   file: fb_model.py
#   find:     margin = sigma * statistics.NormalDist().inv_cdf(min(1 - 1e-9, max(1e-9, p_home)))
#   with:     margin = sigma * (0.3 if p_home > 0.5 else -0.3 if p_home < 0.5 else 0.0)
#
# @vacuity 🔴 sigma is the root-mean-square miss of the own margin
#   file: fb_model.py
#   find:     return math.sqrt(sum(x * x for x in d) / len(d)) if d else None
#   with:     return statistics.pstdev(d) if d else None
#
# @vacuity 🔴 the predicted score never touches a chance
#   file: fb_model.py
#   find:             _ph, out[-1]["score"] = game_score(r, {"moneyline": m, "total": mt, "injury": inj}, sigma, sigma_t)
#   with:             _ph, out[-1]["score"] = game_score(r, {"moneyline": m, "total": mt, "injury": inj}, sigma, sigma_t); out[-1]["p_home"] = 50.0
#
# @vacuity 🔴 a football prop row wraps on a phone
#   file: index.html
#   find:   .fbprow{flex-wrap:wrap}
#   with:   .fbprow{flex-wrap:nowrap}
"""
import copy
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "nfl")
import card_fb as CF  # noqa: E402
import fb_model as FM  # noqa: E402
import winners as W  # noqa: E402
from jsblock import css_rules, js_block  # noqa: E402
from tcheck import ck, section  # noqa: E402

PAGE = os.path.join(ROOT, "index.html")
SRC = open(PAGE, encoding="utf-8").read()
NOW = "2026-10-14T12:00:00Z"                      # ⛔ the pinned clock


def node(driver, payload):
    tmp = tempfile.mkdtemp(prefix="fbphone-")
    try:
        open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(driver)
        json.dump(payload, open(os.path.join(tmp, "d.json"), "w", encoding="utf-8"))
        r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                           capture_output=True, text=True, timeout=300, encoding="utf-8")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ck("⚠️ the page's own code ran in node", r.returncode == 0, (r.stderr or "")[-300:])
    return json.loads(r.stdout) if r.returncode == 0 else None


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 A FOOTBALL ROW BELOW ITS PRICE SAYS SO WITH ITS NUMBERS")
# ══════════════════════════════════════════════════════════════════════
def prop(conf, be, edge, **k):
    return dict(dict(kind="fb-prop", player="Tory Horton", market="receptions", market_label="Receptions",
                     side="over", line=0.5, game="SEA @ DEN", price=-155, book="hardrockbet",
                     confidence_basis="MODEL", confidence=conf, break_even=be, edge=edge), **k)


ROWS = [prop(57, 60.8, -3.8), prop(54, 54.0, 0.0), prop(55, 53.7, 1.3), prop(None, None, None),
        dict(prop(58, 55.0, 3.0), kind="fb-line", market="moneyline")]
MARKED = CF.mark_below_price(copy.deepcopy(ROWS))
ck("🔴 card_fb: edge -3.8 and edge 0.0 carry below_price; +1.3, +3.0 and no edge do not",
   [bool(r.get("below_price")) for r in MARKED] == [True, True, False, False, False],
   str([r.get("below_price") for r in MARKED]))
ck("🔴 ...and a stale label on a row now above its price is removed",
   not CF.mark_below_price([dict(ROWS[2], below_price=True)])[0].get("below_price"))
_src = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
_i = _src.index('    out, _frozen = freeze_published(')
ck("🔴 ...run on the card's props AND game lines, before freeze_published (a published row is never "
   "relabelled)",
   'mark_below_price(out.get("picks") or [])' in _src[_i - 200:_i]
   and 'mark_below_price(out.get("game_lines") or [])' in _src[_i - 200:_i])

_el = next(ln for ln in SRC.splitlines() if ln.startswith("const el = "))
CARD = r"""
const S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
function node(){ return {className: '', innerHTML: '', kids: [],
  append(...n){ this.kids.push(...n); },
  insertAdjacentHTML(_, h){ this.kids.push({innerHTML: h, kids: []}); } }; }
const document = {createElement: () => node()};
const text = n => (n.innerHTML || '') + ' ' + (n.kids || []).map(text).join(' ');
const stub = () => '';
const mk = lg => new Function('document', 'confClass', 'headUrl', 'projChip', 'mark', 'ab', 'sgn',
  'bookChip', 'betControl', 'betLink', 'fbMark', 'fbAb', 'FBTEAMS', 'LEAGUE',
  S.el + '\n' + S.fn + '\nreturn pickCard;')(document, stub, stub, stub, stub,
  stub, String, stub, stub, stub, stub, stub, {}, lg);
// `[Sam, 2026-10-17]` every league's row through pickCard alone, as all four boards draw it
// (~~football rows through fbEdgeLine, MLB's through pickCard alone~~)
process.stdout.write(JSON.stringify(S.runs.map(([lg, r]) => text(mk(lg)(r)).replace(/\s+/g, ' '))));
"""
_NEG = dict(MARKED[2], kind="mlb-line", market="moneyline", player="Home 1", edge=-1.2, below_price=False)
OUT = node(CARD, {"el": _el, "fn": js_block("pickCard", PAGE),
                  "runs": [["nfl", MARKED[0]], ["ncaaf", MARKED[2]], ["mlb", dict(MARKED[2], kind="hitter")],
                           ["nfl", MARKED[4]], ["mlb", _NEG]]}) or ["", "", "", "", ""]
ck("🔴 the page prints the below-price row's %, break-even and edge, once, in its own line (C8)",
   "Below its price: 57% vs 60.8% break-even (edge -3.8%)" in OUT[0] and "Edge <b" not in OUT[0]
   and "Break-even <b" not in OUT[0], OUT[0][:400])
ck("🔴 [Sam, 2026-10-17] a football row above its price: \"Break-even 53.7%\" and \"Edge +1.3\", green "
   "(~~\"Break-even 53.7% · edge +1.3\"~~)",
   "Break-even <b>53.7%</b>" in OUT[1] and 'Edge <b class="eg-pos">+1.3</b>' in OUT[1]
   and "Below its price" not in OUT[1], OUT[1][-300:])
ck("🔴 ...a game-line row the same", 'Edge <b class="eg-pos">+3</b>' in OUT[3], OUT[3][-200:])
ck("🔴 [Sam, 2026-10-17] MLB the same: design I is one row for all three leagues, and \"lets have "
   "the colors of the tabs and the layout be the same for each league\" (Sam, 2026-10-01) "
   "(~~MLB unchanged, no edge~~)", "Break-even <b>53.7%</b>" in OUT[2] and 'Edge <b class="eg-pos">+1.3</b>' in OUT[2],
   OUT[2][-200:])
ck("🔴 [Sam, 2026-10-17] an edge at or below zero on a row not marked below its price is plain ink, "
   "never green", "Edge <b>-1.2</b>" in OUT[4] and "eg-pos" not in OUT[4], OUT[4][-200:])
_body = lambda n: re.sub(r"/\*.*?\*/", "", js_block(n, PAGE), flags=re.S)
ck("🔴 [Sam, 2026-10-17] no board patches a row afterwards: each row prints its own edge "
   "(~~fbEdgeLine on the football boards~~)",
   "fbEdgeLine" not in _body("fbPicks") and "fbEdgeLine" not in _body("fbGameLines")
   and "kept.forEach(p => host.append(pickCard(p)));" in _body("fbPicks")
   and "+ g.map(p => pickCard(p).outerHTML).join('');" in _body("fbGameLines"))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 ~~\"ABOVE THEIR PRICE ONLY\": OFF BY DEFAULT, HIDES EXACTLY EDGE <= 0~~ "
        "`[Sam, 2026-10-17]` NO SUCH BUTTON: THE BOARD SHOWS EVERY ROW THE CARD LISTS")
# ══════════════════════════════════════════════════════════════════════
# `[Sam, 2026-10-17]` "no above their price only button in gizmos pikcs not needed."
#    ~~[Sam, 2026-10-14] off by default / [Sam, 2026-10-15] on by default, hides exactly the
#    rows with edge <= 0, remembered per browser~~. The requirement is now its ABSENCE: no
#    button, no switch, no stored setting, and no edge filter on either board. The card's own
#    liked lists (card_fb.best_liked) are what the board shows whenever the card has them.
_code = re.sub(r"/\*.*?\*/|<!--.*?-->", "", SRC, flags=re.S)     # comments may quote the old text
_gone = {k: _code.count(k) for k in ("Above their price only", "FBABOVE", "fbAbovePass", "gp_fb_above",
                                      "data-fbabove")}
ck("🔴 the button, its switch (FBABOVE), its filter (fbAbovePass) and its stored setting "
   "(gp_fb_above) are gone from the page's code (~~present, ON by default~~)",
   not any(_gone.values()), str(_gone))
KB = r"""
const S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const fbKindBar = new Function('FBPICKKIND', S.fn + '\nreturn fbKindBar;')('props');
process.stdout.write(JSON.stringify(fbKindBar(S.card).replace(/\s+/g, ' ')));
"""
_kb = node(KB, {"fn": js_block("fbKindBar", PAGE),
                "card": {"picks": ROWS[:4], "game_lines": ROWS[4:]}}) or ""
ck("🔴 the kind bar holds exactly its two chips, Player props and Game lines, and nothing else",
   _kb.count("<button") == 2 and _kb.count("data-fbkind=") == 2 and "Player props" in _kb
   and "Game lines" in _kb and "price" not in _kb.lower(), _kb)

# The shipped fbPicks, with the shipped fbView, fbNoLiked and fbGameLines; only the DOM and
# the loaders are stubbed. Each drawn row prints its player and edge.
PK = r"""
const S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const text = n => (n.innerHTML || '') + ' ' + (n.kids || []).map(text).join(' ');
function node(){ return {className: '', innerHTML: '', kids: [],
  get children(){ return this.kids; },
  append(...k){ this.kids.push(...k); },
  insertAdjacentHTML(_, h){ this.kids.push({innerHTML: h, kids: []}); },
  get outerHTML(){ return text(this); } }; }
const document = {createElement: () => node()};
const row = p => { const n = node(); n.innerHTML = '<row>' + p.player + '|' + p.edge + '</row>'; return n; };
const nil = () => '';
async function run(card, kind){
  const v = node();
  const fbPicks = new Function('$', 'document', 'fbShell', 'fbWire', 'fbCardLoad', 'fbDayHead',
    'fbKindBar', 'FBPICKKIND', 'fbDayName', 'fbNoCard', 'splitStarted', 'freshness', 'fbConfBar',
    'startedToggle', 'fbConfPass', 'pickCard', 'fbConf', 'fbTopPlays', 'fbKindWire',
    'showStarted', S.blocks.join('\n') + '\nreturn fbPicks;')(
    s => s === '#fbview' ? v : null, document, h => h, nil, async () => JSON.parse(JSON.stringify(card)),
    nil, nil, kind, d => d, nil, ps => ({list: ps, nStarted: 0, allDone: false}), nil, nil, nil,
    () => true, row, new Set(), nil, nil, false);
  await fbPicks();
  return text(v).match(/<row>[^<]*<\/row>/g) || [];
}
(async () => {
  const out = [];
  for (const [card, kind] of S.runs) out.push(await run(card, kind));
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
"""
PROPS = [dict(r, player="P%d" % i) for i, r in enumerate(ROWS[:4])]       # edges -3.8, 0.0, +1.3, none
LINES = [dict(ROWS[4], player="Line below", edge=-1.0, below_price=True), dict(ROWS[4], player="Line above")]
OLDC = {"date": "2026-10-18", "picks": PROPS, "game_lines": LINES, "game_lines_meta": {"slate": "2026-10-18"}}
NEWC = dict(OLDC, liked=[PROPS[2]], game_lines_liked=[LINES[1]])
PB = node(PK, {"blocks": [js_block(f, PAGE) for f in ("fbView", "fbNoLiked", "fbGameLines", "fbPicks")],
               "runs": [[OLDC, "props"], [OLDC, "lines"], [NEWC, "props"], [NEWC, "lines"]]}) or [[]] * 4
_rows = lambda rs: ["<row>%s|%s</row>" % (r["player"], "null" if r["edge"] is None  # noqa: E731
                                            else "%g" % r["edge"]) for r in rs]           # as JS prints it
ck("🔴 a card with no liked list: the props board draws every row it lists, edge -3.8, 0.0, +1.3 "
   "and none alike, in the card's order (~~edge <= 0 hidden while the button was on~~)",
   PB[0] == _rows(PROPS), str(PB[0]))
ck("🔴 ...and its game lines every fb-line row, the one below its price too",
   PB[1] == _rows(LINES), str(PB[1]))
ck("🔴 a card with liked lists: the board always shows them (~~only while the button was on~~), "
   "props and game lines, exactly as the card wrote them",
   PB[2] == _rows([PROPS[2]]) and PB[3] == _rows([LINES[1]]), str(PB[2:]))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 GAME LINES SHOWS THE WEEK, BY ET DAY, WITH \"ET\" TIMES")
# ══════════════════════════════════════════════════════════════════════
FBM = {"win_chances": [
    {"game_id": "g3", "commence": "2026-10-19T00:20:00Z", "away": "Las Vegas Raiders",
     "home": "Kansas City Chiefs", "p_home": 71.0, "best_ml": {}, "score": {"home": 27.2, "away": 17.6}},
    {"game_id": "g1", "commence": "2026-10-16T00:15:00Z", "away": "Seattle Seahawks",
     "home": "Denver Broncos", "p_home": 42.0, "best_ml": {"away": {"price": -130, "book": "fanduel"}},
     "score": {"home": 20.6, "away": 23.9}},
    {"game_id": "g2", "commence": "2026-10-18T17:00:00Z", "away": "Detroit Lions", "home": "Chicago Bears",
     "p_home": 34.0, "best_ml": {}, "score": None}]}
et = lambda c: (datetime.datetime.strptime(c, "%Y-%m-%dT%H:%M:%SZ")   # noqa: E731
                - datetime.timedelta(hours=4)).strftime("%Y-%m-%d")     # EDT, as test_game_lines_page
# `[Sam, 2026-10-17]` the card's whole-number scores (card_fb.shown_scores): Seattle's is 24-20,
#    not the plain 24-21, because a planted pick needs it; Kansas City's has none (no whole score
#    agrees with all its picks), so the tab falls back to the model's one decimal
SHOWN = [{"away": "Seattle Seahawks", "home": "Denver Broncos", "score": {"home": 20, "away": 24}},
         {"away": "Las Vegas Raiders", "home": "Kansas City Chiefs", "score": None}]
WEEK = W.fb_rows(FBM, None, et, SHOWN)
ck("🔴 winners carries the card's whole-number score beside the model's own, game by game",
   {r["game_id"]: r["score_shown"] for r in WEEK} == {"g1": {"home": 20, "away": 24}, "g2": None, "g3": None},
   str([(r["game_id"], r["score_shown"]) for r in WEEK]))
ck("🔴 winners: the week holds every game in the win chances, each with its predicted score",
   sorted(r["game_id"] for r in WEEK) == ["g1", "g2", "g3"]
   and {r["game_id"]: r["score"] for r in WEEK}["g1"] == {"home": 20.6, "away": 23.9})
ck("⛔ ...while the graded rows stay the slate's one day",
   [r["game_id"] for r in W.fb_rows(FBM, "2026-10-15", et)] == ["g1"])
_wsrc = open(os.path.join(ROOT, "winners.py"), encoding="utf-8").read()
ck("🔴 winners.json carries the week for football (built from the same fb-model.json)",
   # `[2026-10-17]` ~~'week = fb_rows(fbm, None, card_fb.et_date)'~~: with the card's whole scores
   'week = fb_rows(fbm, None, card_fb.et_date, shown)' in _wsrc and 'doc["week"] = week' in _wsrc
   and '"picks", "fb-%s-latest.json" % lg)) or {}).get("scores_shown")' in _wsrc)
WK = r"""
const S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const fbAb = n => n.slice(0, 3).toUpperCase();
const fn = new Function('sgn', 'bookName', 'fbAb', 'fbDayName',
  'const etDate = ' + S.et + ';\n' + S.blocks.join('\n') + '\nreturn winnersWeekHtml;');
const h = fn(x => (x > 0 ? '+' : '') + x, k => k, fbAb, d => 'DAY:' + d)(S.W);
process.stdout.write(JSON.stringify(h.replace(/\s+/g, ' ')));
"""
_et = re.search(r"const etDate = (iso => \{.*?\n\});", SRC, re.S).group(1)
H = node(WK, {"et": _et, "W": {"rows": [], "week": WEEK, "record": {"w": 5, "n": 8, "pct": 62.5}},
              "blocks": [js_block(f, PAGE) for f in ("winnersRecordLine", "winnersHtml", "fbKickDate",
                                                     "fbKickTime", "winnersWeekHtml")]}) or ""
_days = re.findall(r'data-day="([\d-]+)"', H)
ck("🔴 every planted game listed once, under its ET day, earliest day first",
   _days == ["2026-10-15", "2026-10-18"]
   and sorted(re.findall(r'data-game="(\w+)"', H)) == ["g1", "g2", "g3"]
   and H.index("DAY:2026-10-15") < H.index('data-game="g1"') < H.index("DAY:2026-10-18"), str(_days))
ck("🔴 kickoff in ET with \"ET\" written (a 00:15Z kickoff is 8:15 PM ET the day before)",
   "8:15 PM ET" in H and "1:00 PM ET" in H and "8:20 PM ET" in H, H[:600])
ck("🔴 the model's predicted score, away then home, in WHOLE numbers; none printed as a dash",
   # `[Sam, 2026-10-17]` "we need to not have decimal places in the predicted scores and make them
   #    only whole numbers", rounded so they never contradict a pick ("Round, stay consistent"):
   #    Seattle prints the card's 24-20 (~~"SEA 23.9 &ndash; DEN 20.6"~~, `[2026-10-16]` one
   #    decimal), never plain rounding's 24-21; a game with no agreeing whole score keeps one decimal.
   "SEA 24 &ndash; DEN 20" in H and "LAS 17.6 &ndash; KAN 27.2" in H and H.count("<td data-score>&mdash;</td>") == 1,
   re.findall(r"<td data-score>[^<]*</td>", H))
ck("🔴 the graded record line stays at the top", H.startswith("<p data-wrec>") and "5 won, 3 lost" in H)
ck("🔴 the football tab draws the week", "winnersWeekHtml(W)" in js_block("fbGameLinesTab", PAGE))

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE PREDICTED SCORE (`[Sam, 2026-10-16]` ~~OUTPUT ONLY~~: every football spread and total pick comes from it)")
# ══════════════════════════════════════════════════════════════════════
def row(i, final, om, ot, day):
    sig = {"h2h_m": None, "h2h_t": None, "form_m": (i % 7) - 3.0, "form_t": None, "def": None,
           "poss": None, "out": None, "vac_h": None, "vac_a": None, "neutral": 0.0, "dome": 0.0,
           "own_m": om, "own_t": ot}
    return {"id": "r%d" % i, "lg": "nfl", "season": 2026, "day": day, "final": final,
            "hs": (24 if (i * 7) % 5 > 1 else 17) if final else None, "as": 20 if final else None,
            "M": None, "T": None, "pml": 0.5 if final else None, "sig": sig,
            "snap": None if final else {"commence": day + "T17:00:00Z", "names": ["Home %d" % i, "Away %d" % i],
                                        "books": {}}}


ROWS4 = [row(i, True, (i % 11) - 5.0, 44.0, "2026-09-%02d" % (1 + i % 28)) for i in range(200)]
ROWS4 += [row(900 + i, False, 3.3 - i, 44.5, "2026-10-18") for i in range(12)]
ROWS4 += [row(990, False, None, None, "2026-10-19")]
_miss = [r["hs"] - r["as"] - r["sig"]["own_m"] for r in ROWS4 if r["final"]]
SIG = FM.score_sigma(ROWS4)
ck("🔴 sigma = the root-mean-square of (final margin - own margin) over the final rows",
   abs(SIG - (sum(x * x for x in _miss) / len(_miss)) ** 0.5) < 1e-12, (SIG, sum(_miss) / len(_miss)))
_r = ROWS4[-2]
_s = {p: FM.predicted_score(_r, p, 13.4) for p in (0.3, 0.5, 0.52, 0.6, 0.75, 0.9)}
_mg = [_s[p]["home"] - _s[p]["away"] for p in (0.52, 0.6, 0.75, 0.9)]
ck("🔴 a 50% chance gives equal scores; the totals stay the own total",
   _s[0.5]["home"] == _s[0.5]["away"] and all(abs(v["home"] + v["away"] - 44.5) < 0.11 for v in _s.values()),
   _s)
ck("🔴 a larger chance gives a larger margin (52% < 60% < 75% < 90%), and 30% favours the away side",
   all(a < b for a, b in zip(_mg, _mg[1:])) and _mg[0] > 0 and _s[0.3]["away"] > _s[0.3]["home"], (_mg, _s[0.3]))
ck("🔴 no own total: no score (never a guess)", FM.predicted_score(ROWS4[-1], 0.6, 13.4) is None)
A = FM.win_chances(copy.deepcopy(ROWS4), now=NOW)
B = FM.win_chances(copy.deepcopy(ROWS4), now=NOW, scores=False)
_scored = [x for x in A if x.get("score")]
_wrong = [(x["game_id"], x["p_home"], x["score"]) for x in _scored
          if (x["score"]["home"] > x["score"]["away"]) != (x["p_home"] > 50)
          and not (x["p_home"] == 50 and x["score"]["home"] == x["score"]["away"])]
ck("🔴 in every priced row the higher predicted score is the pick's team (%d rows)" % len(_scored),
   len(_scored) == 12 and not _wrong and len({x["p_home"] for x in _scored}) > 3, _wrong or len(_scored))
ck("🔴 the picks and chances are byte-identical with and without it",
   # `[2026-10-17]` ~~k != "score"~~: the 10,000-run simulation rides the score (fb_sim), and
   #    neither moves a pick or a chance
   json.dumps([{k: v for k, v in x.items() if k not in ("score", "sim")} for x in A], sort_keys=True)
   == json.dumps(B, sort_keys=True) and all("score" not in x for x in B))

# ══════════════════════════════════════════════════════════════════════
section("5. ⚠️ THE PHONE LAYOUT'S RULES ARE IN THE PAGE (the weak half)")
# ══════════════════════════════════════════════════════════════════════
# ⛔ A source check cannot say the page fits a phone; test_league_switch.py §3
#    measures scrollWidth at 390 px in a browser. This only fails fast when a
#    rule is deleted, on runners with no browser.
_m = css_rules(PAGE).get("@media(max-width:600px)", "").replace(" ", "")
ck("🔴 under 600 px: the tab bar is a 5-column grid (two rows of nine), football tables scroll in "
   "their own box, a prop row wraps and its price row takes the full width",
   all(x in _m for x in (".subnavul{display:grid;grid-template-columns:repeat(5,minmax(0,1fr))",
                         "#fbviewtable.ob,#fbviewtable.fbt,#fbviewtable.glmain{display:block;overflow-x:auto",
                         ".fbprow{flex-wrap:wrap}", ".fbprow.pr2{order:3;flex:11100%")), _m[-600:])
