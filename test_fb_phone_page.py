#!/usr/bin/env python3
"""test_fb_phone_page.py — the football tabs, `[Sam, 2026-10-14]`: "look at every
aspect of the github repo, and the website and your only goal is to do anything to
make it better"; and "the way i want you to predict outcomes of football games is
by predicted scores".

Planted rows, a pinned clock, the SHIPPED page code in node. ⛔ Reads no live data.
  1. a football row whose card edge is <= 0 carries `below_price`; the page prints
     its %, break-even and edge; a row above its price adds the edge to the
     break-even line; MLB's line is unchanged
  2. "Above their price only" hides exactly the rows with edge <= 0, and nothing
     while off (the default, also when storage throws)
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
# @vacuity 🔴 the edge joins the break-even line only on a row above its price
#   file: index.html
#   find:   if (ev && p && !p.below_price && p.break_even != null && p.edge != null && p.edge > 0)
#   with:   if (ev && p && p.break_even != null && p.edge != null)
#
# @vacuity 🔴 the props board adds the edge line
#   file: index.html
#   find:   [...host.children].forEach((c, i) => fbEdgeLine(c, kept[i]));
#   with:   [...host.children].forEach((c, i) => c);
#
# @vacuity 🔴 the filter hides exactly the rows with edge <= 0
#   file: index.html
#   find:   return !FBABOVE || !(p && p.edge != null && p.edge <= 0);
#   with:   return !FBABOVE || !(p && p.edge != null && p.edge < 0);
#
# @vacuity 🔴 the filter is ON by default [Sam, 2026-10-15]
#   file: index.html
#   find: let FBABOVE = (() => { try { return localStorage.getItem('gp_fb_above') !== '0'; }
#   with: let FBABOVE = (() => { try { return localStorage.getItem('gp_fb_above') === '1'; }
#
# @vacuity 🔴 the props board runs through the filter
#   file: index.html
#   find:   const kept = inConf.filter(fbAbovePass);
#   with:   const kept = inConf;
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
#   find:             out[-1]["score"] = predicted_score(
#   with:             out[-1]["p_home"] = 50.0; out[-1]["score"] = predicted_score(
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
  S.el + '\n' + S.fn + '\n' + S.edge + '\nreturn [pickCard, fbEdgeLine];')(document, stub, stub, stub, stub,
  stub, String, stub, stub, stub, stub, stub, {}, lg);
// football rows go through fbEdgeLine as fbPicks / fbGameLines do; MLB's through pickCard alone
process.stdout.write(JSON.stringify(S.runs.map(([lg, r]) => { const [pc, fe] = mk(lg);
  return text(lg === 'mlb' ? pc(r) : fe(pc(r), r)).replace(/\s+/g, ' '); })));
"""
OUT = node(CARD, {"el": _el, "fn": js_block("pickCard", PAGE), "edge": js_block("fbEdgeLine", PAGE),
                  "runs": [["nfl", MARKED[0]], ["ncaaf", MARKED[2]], ["mlb", dict(MARKED[2], kind="hitter")],
                           ["nfl", MARKED[4]]]}) or ["", "", "", ""]
ck("🔴 the page prints the below-price row's %, break-even and edge, and no second edge",
   "Below its price: 57% vs 60.8% break-even (edge -3.8%)" in OUT[0] and "&middot; edge" not in OUT[0],
   OUT[0][:400])
ck("🔴 a football row above its price: \"Break-even 53.7% · edge +1.3\"",
   "Break-even <b>53.7%</b> &middot; edge <b>+1.3</b>" in OUT[1] and "Below its price" not in OUT[1],
   OUT[1][-300:])
ck("🔴 ...a game-line row the same", "edge <b>+3</b>" in OUT[3], OUT[3][-200:])
ck("⛔ MLB unchanged: pickCard alone prints no edge on the break-even line (pickCard is frozen by "
   "test_mlb_untouched.py)", "Break-even <b>53.7%</b>" in OUT[2] and "edge <b>" not in OUT[2], OUT[2][-200:])
ck("🔴 both football boards add it: the props board after each card, the game lines on each row",
   "[...host.children].forEach((c, i) => fbEdgeLine(c, kept[i]));" in js_block("fbPicks", PAGE)
   and "fbEdgeLine(pickCard(p), p)" in js_block("fbGameLines", PAGE))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 \"ABOVE THEIR PRICE ONLY\": OFF BY DEFAULT, HIDES EXACTLY EDGE <= 0")
# ══════════════════════════════════════════════════════════════════════
_init = re.search(r"\nlet FBABOVE = .*?\}\)\(\);", SRC, re.S).group(0)
FILT = r"""
const S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const run = (store, on) => new Function('localStorage', 'ROWS', 'ON',
  S.init + '\n' + S.fn + '\nif (ON !== null) FBABOVE = ON;'
  + '\nreturn [FBABOVE, ROWS.map(r => fbAbovePass(r))];')(store, S.rows, on);
const empty = {getItem: () => null}, set = {getItem: () => '0'},
      boom = {getItem: () => { throw new Error('blocked'); }};
process.stdout.write(JSON.stringify([run(empty, null), run(boom, null), run(set, null),
                                     run(empty, true), run(empty, false)]));
"""
F = node(FILT, {"init": _init, "fn": js_block("fbAbovePass", PAGE), "rows": ROWS}) or [[None, []]] * 5
# `[Sam, 2026-10-15]` ~~off by default~~: "i just want you to have the best plays our
#    model likes simple as that" -- ON by default, and when storage throws; OFF only
#    when this browser remembered it switched off.
ck("🔴 ON by default and when storage throws; off when the browser remembered off",
   [F[0][0], F[1][0], F[2][0]] == [True, True, False], str(F[:3]))
ck("🔴 off: every row shows", F[4][1] == [True] * len(ROWS), str(F[4][1]))
ck("🔴 on: hidden are exactly the rows with edge <= 0 (-3.8 and 0.0); +1.3, +3.0 and no edge stay",
   F[3][1] == [False, False, True, True, True], str(F[3][1]))
_pk, _gl = js_block("fbPicks", PAGE), js_block("fbGameLines", PAGE)
ck("🔴 the props board and the game lines both run through it, and the button sits in the kind bar",
   "const kept = inConf.filter(fbAbovePass);" in _pk and "fbAbovePass(p)" in _gl
   and "Above their price only" in js_block("fbKindBar", PAGE)
   and "localStorage.setItem('gp_fb_above'" in js_block("fbKindWire", PAGE))

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
WEEK = W.fb_rows(FBM, None, et)
ck("🔴 winners: the week holds every game in the win chances, each with its predicted score",
   sorted(r["game_id"] for r in WEEK) == ["g1", "g2", "g3"]
   and {r["game_id"]: r["score"] for r in WEEK}["g1"] == {"home": 20.6, "away": 23.9})
ck("⛔ ...while the graded rows stay the slate's one day",
   [r["game_id"] for r in W.fb_rows(FBM, "2026-10-15", et)] == ["g1"])
_wsrc = open(os.path.join(ROOT, "winners.py"), encoding="utf-8").read()
ck("🔴 winners.json carries the week for football (built from the same fb-model.json)",
   'week = fb_rows(fbm, None, card_fb.et_date)' in _wsrc and 'doc["week"] = week' in _wsrc)
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
ck("🔴 the model's predicted score, away then home; none printed as a dash",
   "SEA 24 &ndash; DEN 21" in H and "LAS 18 &ndash; KAN 27" in H and H.count("<td data-score>&mdash;</td>") == 1,
   re.findall(r"<td data-score>[^<]*</td>", H))
ck("🔴 the graded record line stays at the top", H.startswith("<p data-wrec>") and "5 won, 3 lost" in H)
ck("🔴 the football tab draws the week", "winnersWeekHtml(W)" in js_block("fbGameLinesTab", PAGE))

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE PREDICTED SCORE: OUTPUT ONLY")
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
   json.dumps([{k: v for k, v in x.items() if k != "score"} for x in A], sort_keys=True)
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
