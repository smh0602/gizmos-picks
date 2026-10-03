#!/usr/bin/env python3
"""MLB GAME LINES: the game model and its card rows, page and record line.

`[Sam, 2026-10-01..03]` "add gizmos picks gamelines to mlb ... the same format
as the player prop picks"; "use what we use for our pitcher and hitter props to
predict game outcomes for mlb"; "go on with moneyline and run line only.
Totals stay in mlb-game-model.json ... totals come onto the card only by Sam's
decision." Planted data throughout; the page in node.

# @vacuity 🔴 a prediction never reads a schedule saved after first pitch
#   file: mlb_game_model.py
#   find: if at and fp and at < fp and (pk not in best or best[pk][0] < at):
#   with: if at and fp and (pk not in best or best[pk][0] < at):
#
# @vacuity 🔴 ...nor the lineup the game's own box score names
#   file: mlb_game_model.py
#   find:                 st.usual(x["home"]), st.usual(x["away"]), x["venue"])))
#   with:                 (I["lineups"].get(day) or {}).get(x["home"]) or st.usual(x["home"]), st.usual(x["away"]), x["venue"])))
#
# @vacuity 🔴 the two win chances sum to 100
#   file: mlb_game_model.py
#   find:     out = {"win": {"home": 100 * win_h, "away": 100 * (1 - win_h)},
#   with:     out = {"win": {"home": 100 * win_h, "away": 100 * sum(w for h, a, w in joint if a > h)},
#
# @vacuity 🔴 a better starter raises his own side's chance
#   file: mlb_game_model.py
#   find:     lh = pa_away * lineup_factor(st, R, lu_home) * v * R["home"]
#   with:     lh = pa_home * lineup_factor(st, R, lu_home) * v * R["home"]
#
# @vacuity 🔴 a better lineup raises its own side's chance
#   file: mlb_game_model.py
#   find:     return (sum(vals) / len(vals)) / R["bases"]
#   with:     return 1.0
#
# @vacuity 🔴 a row under 50 is never listed
#   file: card.py
#   find: if not q or q.get("price") is None or q["price"] < PRICE_FLOOR or pr < GL_MIN_CONF:
#   with: if not q or q.get("price") is None or q["price"] < PRICE_FLOOR:
#
# @vacuity 🔴 a row shorter than -400 is never listed
#   file: card.py
#   find: if not q or q.get("price") is None or q["price"] < PRICE_FLOOR or pr < GL_MIN_CONF:
#   with: if not q or q.get("price") is None or pr < GL_MIN_CONF:
#
# @vacuity 🔴 a run line is priced only at its exact signed point
#   file: card.py
#   find:                 q = q if q and q.get("pt") == line else None
#   with:                 q = q
#
# @vacuity 🔴 totals never reach the card
#   file: card.py
#   find: GL_MARKETS = ("moneyline", "run_line")
#   with: GL_MARKETS = ("moneyline", "run_line", "total")
#
# @vacuity 🔴 at most 25
#   file: card.py
#   find: GAME_LINES_MAX = 25
#   with: GAME_LINES_MAX = 10 ** 6
#
# @vacuity 🔴 a published row is frozen at first pitch
#   file: card.py
#   find:     keep = [r for r in published or [] if r.get("commence") and _iso(r["commence"]) <= now]
#   with:     keep = []
#
# @vacuity 🔴 nothing new is listed for a game that has started
#   file: card.py
#   find:     fresh = [r for r in rows if _iso(r["commence"]) > now and r.get("game_pk") not in gone]
#   with:     fresh = [r for r in rows if r.get("game_pk") not in gone]
#
# @vacuity 🔴 the page draws MLB game-line rows with pickCard
#   file: index.html
#   find:     .sort((a, b) => (a.rank || 999) - (b.rank || 999)).map(p => pickCard(p));
#   with:     .sort((a, b) => (a.rank || 999) - (b.rank || 999)).map(p => el('div', 'r', p.player));
#
# @vacuity 🔴 ...as a game-line row: its team, no side word
#   file: index.html
#   find:   const gl = p.kind === 'fb-line' || p.kind === 'mlb-line';   // [Sam, 2026-10-01] a game-line pick, same row
#   with:   const gl = p.kind === 'fb-line';
#
# @vacuity 🔴 the record's game-line line is its own, never in a props count
#   file: collect.py
#   find:         days.append({"date": date, "rows": rows, "graded": graded, "lines": lines,
#   with:         days.append({"date": date, "rows": rows + lines, "graded": graded + [x for x in lines if x["won"] is not None], "lines": lines,
#
# @vacuity 🔴 totals never reach the record's game-line line
#   file: collect.py
#   find: GAME_LINE_MARKETS = ("moneyline", "run_line")
#   with: GAME_LINE_MARKETS = ("moneyline", "run_line", "total")
#
# @vacuity 🔴 the verifier recomputes the game-line line
#   file: verify_record.py
#   find:    (_gw, _gn, gl_void) == (_gl.get("w"), _gl.get("n"), _gl.get("voids")),
#   with:    True,
"""
import collections
import datetime
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "mlb")
import card as CA  # noqa: E402
import collect as CO  # noqa: E402
import mlb_game_model as M  # noqa: E402
from jsblock import js_block  # noqa: E402
from tcheck import ck, section  # noqa: E402

D0, D1, H, A = "2026-09-01", "2026-09-02", "Home Club", "Away Club"


def put(root, rel, obj):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with (gzip.open(p, "wt") if p.endswith(".gz") else open(p, "w")) as fh:
        json.dump(obj, fh)


def snap(at, sp_home, sp_away):
    return {"pulled_at": at, "schedule": {"dates": [{"games": [{
        "gamePk": 2, "gameDate": "2026-09-02T23:05:00Z", "gameType": "R", "venue": {"id": 7},
        "teams": {"home": {"team": {"name": H, "id": 1}, "probablePitcher": {"id": sp_home}},
                  "away": {"team": {"name": A, "id": 2}, "probablePitcher": {"id": sp_away}}}}]}]}}


def tree(root, poison):
    """D0 is history; D1's game is predicted. `poison` rewrites everything
    dated D1 (logs, the box-score lineup, the final score)."""
    k = 9 if poison else 1
    lu = lambda team, ids: [{"pid": i, "team": team, "slot": n + 1, "sub": 0, "started": 1}
                            for n, i in enumerate(ids)]
    hs, as_, ps = ["h%d" % i for i in range(9)], ["a%d" % i for i in range(9)], ["p%d" % i for i in range(9)]
    put(root, "data/latest/scores.json.gz", {"days": {
        D0: [{"gamePk": 1, "away": A, "home": H, "away_r": 2, "home_r": 3, "venue_id": 7, "gameType": "R"}],
        D1: [{"gamePk": 2, "away": A, "home": H, "away_r": 4 * k, "home_r": 5, "venue_id": 7, "gameType": "R"}]}})
    put(root, "data/latest/pitchers.json.gz", {"players": {
        "10": {"team": H, "g": [{"d": D0, "o": A, "h": 1, "gs": 1, "outs": 18, "er": 1},
                                {"d": D1, "o": A, "h": 1, "gs": 1, "outs": 18, "er": 2 * k}]},
        "20": {"team": A, "g": [{"d": D0, "o": H, "h": 0, "gs": 1, "outs": 12, "er": 5},
                                {"d": D1, "o": H, "h": 0, "gs": 1, "outs": 15, "er": 3 * k}]},
        "11": {"team": H, "g": []}, "21": {"team": A, "g": []}}})
    put(root, "data/latest/hitters.json.gz", {"players": dict(
        [(i, {"g": [{"d": D0, "pa": 4, "tb": 1, "bb": 0}, {"d": D1, "pa": 4, "tb": 2 * k, "bb": 0}]})
         for i in hs + as_] + [(i, {"g": [{"d": D0, "pa": 4, "tb": 4, "bb": 1}]}) for i in ps])})
    put(root, "data/latest/lineups.json.gz", {"days": {
        D0: lu(H, hs) + lu(A, as_), D1: lu(H, ps if poison else hs) + lu(A, as_)}})
    put(root, "data/2026-09-02/schedule/1200.json.gz", snap("2026-09-02T12:00:00Z", 10, 20))
    put(root, "data/2026-09-03/schedule/0200.json.gz", snap("2026-09-03T02:00:00Z", 11, 21))


def predicted(poison):
    t = tempfile.mkdtemp(prefix="mlbgm-")
    try:
        tree(t, poison)
        _st, recs = M.walk(M.inputs(t), M.schedules(t))
    finally:
        shutil.rmtree(t, ignore_errors=True)
    r = next(r for r in recs if r["game"]["gamePk"] == 2)
    return r["inputs"], {k: r["model"][k] for k in ("win", "expected_runs", "run_line")}


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 NO INPUT DATED AT OR AFTER FIRST PITCH IS READ")
# ══════════════════════════════════════════════════════════════════════
_in, _p = predicted(False)
_in2, _p2 = predicted(True)
ck("🔴 the starters are the ones the schedule saved BEFORE first pitch named",
   (_in["sp_home"], _in["sp_away"]) == (10, 20),
   "⛔ a schedule pulled after first pitch names 11 and 21; got %s" % ((_in["sp_home"], _in["sp_away"]),))
ck("🔴 rewriting every log, lineup and score dated on the game's day changes nothing",
   _p == _p2 and _p["win"]["home"] != 50.0, "%s vs %s" % (_p, _p2))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE WIN CHANCES SUM TO 100 AND MOVE THE RIGHT WAY")
# ══════════════════════════════════════════════════════════════════════
st = M.State()
st.pit["good"].update(er=8, outs=540, n=30)        # 0.40 ER a nine
st.pit["bad"].update(er=90, outs=300, n=20)        # 8.1 ER a nine
for i in range(9):
    st.hit["s%d" % i].update(bases=450, pa=800)
    st.hit["w%d" % i].update(bases=220, pa=800)
S9, W9 = ["s%d" % i for i in range(9)], ["w%d" % i for i in range(9)]
win = lambda sh, sa, lh, la: M.predict(st, H, A, sh, sa, lh, la, 7)["win"]
_all = [win(a, b, c, d) for a in ("good", "bad") for b in ("good", "bad")
        for c in (S9, W9) for d in (S9, W9)]
ck("🔴 the two win chances sum to 100 in every combination",
   all(abs(w["home"] + w["away"] - 100) < 1e-9 for w in _all), str(_all[:2]))
ck("🔴 a better home starter raises the home side's chance, and a better away one lowers it",
   win("good", "x", S9, S9)["home"] > win("bad", "x", S9, S9)["home"]
   and win("x", "good", S9, S9)["home"] < win("x", "bad", S9, S9)["home"])
ck("🔴 a better home lineup raises the home side's chance, and a better away one lowers it",
   win("x", "x", S9, W9)["home"] > win("x", "x", W9, W9)["home"]
   and win("x", "x", W9, S9)["home"] < win("x", "x", W9, W9)["home"])

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE CARD LISTS A SIDE AT 50%+ AND -400 OR LONGER, NEVER A TOTAL")
# ══════════════════════════════════════════════════════════════════════
AT = "2026-09-02T23:05:00Z"


def mg(pk, ml, rl=40.0, at=AT, sp=True, pt=-1.5, extra=None):
    g = {"game_pk": pk, "commence": at, "away": "Away %d" % pk, "home": "Home %d" % pk,
         "starters": {"home": {"id": 1 if sp else None, "name": "H"}, "away": {"id": 2, "name": "A"}},
         "expected_runs": {"home": 4.4, "away": 3.9},
         "card": {"moneyline": {"home": ml, "away": 100 - ml},
                  "run_line": {"point": pt, "home": rl, "away": 100 - rl}}}
    g["card"].update(extra or {})
    return g


def bg(pk, ml_h, ml_a, rl_h, rl_a, pt=-1.5, at=AT):
    return {"id": "ev%d" % pk, "commence": at, "away": "Away %d" % pk, "home": "Home %d" % pk,
            "best_ml": {"Home %d" % pk: {"book": "fanduel", "price": ml_h},
                        "Away %d" % pk: {"book": "draftkings", "price": ml_a}},
            "best_spread": {"Home %d" % pk: {"book": "hardrockbet", "price": rl_h, "pt": pt},
                            "Away %d" % pk: {"book": "fanduel", "price": rl_a, "pt": -pt}}}


MODEL = {"corrected": ["run_line"], "games": [
    mg(1, 50.1, rl=40.0), mg(2, 60.0, rl=40.0), mg(3, 49.9, rl=45.0),
    mg(4, 55.0, rl=40.0), mg(5, 70.0, sp=False), mg(6, 70.0, at="2026-09-03T23:05:00Z"),
    mg(7, 58.0, rl=35.0, extra={"total": {"point": -1.5, "home": 90.0, "away": 10.0}}), mg(8, 70.0)]}
MODEL["games"][2]["card"]["moneyline"]["away"] = 49.9           # neither side reaches 50
MODEL["games"][2]["card"]["run_line"]["away"] = 45.0
BOARD = {"games": [bg(1, -400, 300, 150, -401), bg(2, -401, 300, 150, -150),
                   bg(3, -110, -110, 150, -170), bg(4, -130, 110, 150, -170, pt=1.5),
                   bg(5, -200, 170, 150, -170), bg(6, -200, 170, 150, -170, at="2026-09-03T23:05:00Z"),
                   bg(7, -140, 120, 160, -180)]}
ROWS = CA.game_line_rows(MODEL, BOARD, D1)
_got = sorted((r["player"], r["market"], r["line"], r["price"]) for r in ROWS)
ck("🔴 exactly the sides at 50%+ and -400 or longer: -400 itself in, -401 out, "
   "a side under 50 out, a run line off its signed point out",
   _got == [("Away 2", "run_line", 1.5, -150), ("Away 7", "run_line", 1.5, -180),
            ("Home 1", "moneyline", None, -400), ("Home 4", "moneyline", None, -130),
            ("Home 7", "moneyline", None, -140)], str(_got))
ck("⛔ TOTALS NEVER REACH THE CARD, even at 90% (Sam, 2026-10-03)",
   CA.GL_MARKETS == ("moneyline", "run_line") and not any(r["market"] == "total" for r in ROWS))
ck("  every row is in the prop row's format, confidence a whole number",
   all(r["kind"] == "mlb-line" and isinstance(r["confidence"], int) and r["confidence_basis"] == "MODEL"
       and r["why"] and r["break_even"] == round(100 * CA.implied(r["price"]), 1) for r in ROWS))

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 AT MOST 25, AND FROZEN AT FIRST PITCH")
# ══════════════════════════════════════════════════════════════════════
_many = {"games": [mg(100 + i, 51.0 + i) for i in range(40)]}
_mb = {"games": [bg(100 + i, -150, 130, 150, -170) for i in range(40)]}
_cap = CA.order_game_lines(CA.game_line_rows(_many, _mb, D1))
ck("🔴 at most 25 rows, the highest chances, ranked",
   len(_cap) == 25 and [r["rank"] for r in _cap] == list(range(1, 26))
   and _cap[0]["confidence_value"] == 90.0 and _cap[-1]["confidence_value"] >= 66.0,
   "%d rows" % len(_cap))
_now = datetime.datetime(2026, 9, 2, 18, 0, tzinfo=datetime.timezone.utc)
_early = "2026-09-02T17:05:00Z"
_pub = [dict(CA.game_line_rows({"games": [mg(20, 60.0, at=_early)]},
                               {"games": [bg(20, -150, 130, 150, -170, at=_early)]}, D1)[0], price=-111)]
_new = CA.game_line_rows({"games": [mg(20, 64.0, at=_early), mg(21, 62.0), mg(22, 66.0, at=_early)]},
                         {"games": [bg(20, -160, 140, 150, -170, at=_early), bg(21, -150, 130, 150, -170),
                                    bg(22, -150, 130, 150, -170, at=_early)]}, D1)
_as_published = {k: v for k, v in _pub[0].items() if k != "rank"}
_fz = CA.freeze_game_lines(_new, _pub, _now)
_kept = [{k: v for k, v in r.items() if k != "rank"} for r in _fz if r["game_pk"] == 20]
ck("🔴 a published row whose game has started stays exactly as published",
   _kept == [_as_published] and _as_published["price"] == -111, str(_kept))
ck("🔴 ...and nothing new is listed for a game that has started; an unstarted game is rebuilt",
   sorted({r["game_pk"] for r in _fz}) == [20, 21], str([r["game_pk"] for r in _fz]))

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE PAGE DRAWS MLB GAME-LINE ROWS WITH THE PROP MARKUP")
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
  'bookChip', 'betControl', 'betLink', 'fbMark', 'fbAb', 'FBTEAMS', 'LEAGUE', 'MLBPICKKIND',
  S.el + '\n' + S.pc + '\n' + S.gl + '\n' + S.kb + '\nreturn [mlbGameLines, mlbKindBar];');
const [gl, kb] = fn(document, stub, stub, stub, stub, stub, x => (x > 0 ? '+' : '') + x,
  stub, stub, stub, stub, stub, {}, 'mlb', 'lines');
process.stdout.write(JSON.stringify({rows: gl(S.card).map(n => n.outerHTML.replace(/\s+/g, ' ')),
                                     bar: kb(S.card)}));
"""
_card = {"picks": [{"kind": "pitcher"}] * 3,
         "game_lines": ROWS + [{"kind": "price-gap", "player": "Old Row", "market": "spreads"}]}
tmp = tempfile.mkdtemp(prefix="mlbgl-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"el": _el, "pc": js_block("pickCard", PAGE), "gl": js_block("mlbGameLines", PAGE),
               "kb": js_block("mlbKindBar", PAGE), "card": _card},
              open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=300)
    OUT = json.loads(r.stdout) if r.returncode == 0 else {"rows": [], "bar": ""}
finally:
    shutil.rmtree(tmp, ignore_errors=True)
_html = " ".join(OUT["rows"])
ck("🔴 every MLB game-line row is a pickCard card, and nothing else in game_lines is",
   r.returncode == 0 and len(OUT["rows"]) == len(ROWS) and all(h.startswith("<pk>") for h in OUT["rows"])
   and "Old Row" not in _html, (r.stderr or "")[-300:] + _html[:200])
ck("🔴 ...naming its team with no side word, a run line with its sign",
   "Home 1 Moneyline" in _html and "Away 2 +1.5 Run line" in _html
   and " — Under" not in _html and " — Over" not in _html, _html[:300])
_rp = js_block("renderPicks", PAGE)
ck("🔴 Gizmo's Picks carries the Player props / Game lines switch, the lines drawn before the props board",
   "Player props <span>3</span>" in OUT["bar"] and "Game lines <span>5</span>" in OUT["bar"]
   and "mlbKindBar(P)" in _rp and _rp.index("mlbGameLines(P)") < _rp.index("const dated = P.picks"),
   OUT["bar"][:200])
ck("⛔ the page never reads mlb-game-model.json: the card is its only source of game lines, so a total "
   "cannot reach the page (Sam, 2026-10-03)", "mlb-game-model" not in open(PAGE, encoding="utf-8").read())

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 THE RECORD'S GAME-LINE LINE IS ITS OWN, AND THE VERIFIER RECOMPUTES IT")
# ══════════════════════════════════════════════════════════════════════
gl = lambda pk, mk, side, line=None: {"kind": "mlb-line", "market": mk, "side": side, "line": line,
                                       "player": "T%d" % pk, "game_pk": pk, "price": -120,
                                       "confidence": 60, "game": "A @ H"}
CARD = {"date": D1, "kind": "gizmos-card",
        "picks": [{"kind": "pitcher", "market": "strikeouts", "side": "over", "line": 5.5,
                   "pid": 555, "pitcher": "P", "confidence": 60, "game": "A @ H"}],
        "game_lines": [gl(1, "moneyline", "home"), gl(2, "run_line", "away", 1.5),
                       gl(3, "moneyline", "home"), gl(1, "total", "over", 6.5)]}
FINAL = {"slate_date": D1, "n_games": 3, "n_final": 2, "games": [
    {"gamePk": 1, "state": "Final", "score": {"away": 2, "home": 5},
     "pitchers": [{"id": 555, "started": True, "k": 7, "outs": 18}], "batters": []},
    {"gamePk": 2, "state": "Final", "score": {"away": 1, "home": 3}, "pitchers": [], "batters": []},
    {"gamePk": 3, "state": "Postponed", "score": {}, "pitchers": [], "batters": []}]}


def grade(tamper=None):
    t, cwd = tempfile.mkdtemp(prefix="mlbglrec-"), os.getcwd()
    try:
        put(t, "picks/%s.json" % D1, CARD)
        put(t, "data/%s/results/final.json.gz" % D1, FINAL)
        os.makedirs(os.path.join(t, "data", "latest"))
        os.chdir(t)
        CO.collect_record()
        rec = json.load(open("data/latest/record.json"))
        if tamper:
            tamper(rec)
            json.dump(rec, open("data/latest/record.json", "w"))
        for f in ("verify_record.py", "collect.py", "record_grader.py"):
            shutil.copy(os.path.join(ROOT, f), t)
        p = subprocess.run([sys.executable, "verify_record.py"], cwd=t, capture_output=True,
                           text=True, env=dict(os.environ, PYTHONUTF8="1"))
        return rec, p.returncode, p.stdout + p.stderr
    finally:
        os.chdir(cwd)
        shutil.rmtree(t, ignore_errors=True)


rec, rc, out = grade()
G = rec.get("game_lines") or {}
ck("🔴 the props record holds the one prop and no game line",
   (rec["overall"]["w"], rec["overall"]["n"]) == (1, 1), str(rec["overall"]))
ck("🔴 the game lines are graded in their own line: moneyline won, run line lost, the postponed one void",
   (G.get("w"), G.get("n"), G.get("voids")) == (1, 2, 1)
   and {m: (v["w"], v["n"]) for m, v in (G.get("by_market") or {}).items()}
   == {"moneyline": (1, 1), "run_line": (0, 1)}, str(G))
ck("⛔ ...and a total on a card never enters it (Sam, 2026-10-03)",
   CO.GAME_LINE_MARKETS == ("moneyline", "run_line") and "total" not in (G.get("by_market") or {}))
ck("✅ verify_record re-grades the line a second way and agrees", rc == 0, out[-500:])
_rec2, rc2, out2 = grade(lambda R: R["game_lines"].update(w=2))
ck("🔴 ...and fails a record whose game-line line is wrong", rc2 == 1
   and "the game lines reproduce in their own line" in out2, out2[-300:])
