#!/usr/bin/env python3
"""test_game_lines_page.py — THE GAME LINES TAB IS THE MODEL'S PICK TO WIN EACH GAME.

`[Sam, 2026-10-01]` *"remove the game lines standalone tab with moneyline
predictions, in this tab you will simply just give the models pick on whos
going to win the game outright. do this for all leagues"*; asked what the tab
becomes: *"replace it with moneyline predictions and just have the models
picks for who wins outright"*.

⚠️ REWRITTEN TO THE NEW REQUIREMENT, not deleted (CLAUDE.md: Sam changed the
requirement). ~~This file rendered the alt ladders, books' chance, fair lines,
rung sort and the alt-rung record~~; those left the page. It now asks, on
planted data and through the SHIPPED page code in node: one row per slate
game with the higher-chance side picked; an MLB game missing a starter has no
pick; no ladder, box or tag in any league; a pick frozen at the start and
graded once; the winners' record its own, re-computed by the verifier. (The
same tab order in every league, Game Lines included: test_tab_bar.py.)

# @vacuity 🔴 the pick is the side with the higher chance
#   file: winners.py
#   find:     side = "home" if p_home >= 100 - p_home else "away"
#   with:     side = "home"
#
# @vacuity 🔴 football lists one day only, the slate's
#   file: winners.py
#   find:             for g in (model or {}).get("win_chances") or [] if et_date(g["commence"]) == slate]
#   with:             for g in (model or {}).get("win_chances") or []]
#
# @vacuity 🔴 an MLB game missing a starter has no pick
#   file: winners.py
#   find:                             (g.get("win") or {}).get("home") if named else None,
#   with:                             (g.get("win") or {}).get("home"),
#
# @vacuity 🔴 the page draws every slate game, one row each
#   file: index.html
#   find:   const rows = ((W && W.rows) || []).slice()
#   with:   const rows = ((W && W.rows) || []).slice(0, 1)
#
# @vacuity 🔴 the tab draws no tag
#   file: index.html
#   find:       <td>${r.away} @ ${r.home}</td><td>${when(r.commence)}</td>
#   with:       <td>${r.away} @ ${r.home} <span class="kind">MODEL</span></td><td>${when(r.commence)}</td>
#
# @vacuity 🔴 the MLB tab's heading names the day like football's [Sam, 2026-10-06]
#   file: index.html
#   find:   v.innerHTML = `<div class="panel"><h2>Game Lines${W && W.slate ? ' &mdash; ' + fbDayName(W.slate) : ''}</h2>
#   with:   v.innerHTML = `<div class="panel"><h2>Game Lines${W && W.slate ? ' &mdash; ' + W.slate : ''}</h2>
#
# @vacuity 🔴 a started game shows its frozen pick, never a rebuilt one
#   file: winners.py
#   find:     rows = [fz.get(r["game_id"], r) if r["commence"] <= now else r for r in rows]
#   with:     rows = rows
#
# @vacuity 🔴 a save taken after the start never sets the pick
#   file: winners.py
#   find:             if t < (r.get("commence") or "") and t > best.get(r["game_id"], ("",))[0]:
#   with:             if t > best.get(r["game_id"], ("",))[0]:
#
# @vacuity 🔴 graded once: the first stored grade stands
#   file: winners.py
#   find:             out.setdefault(g["game_id"], g)
#   with:             out[g["game_id"]] = g
#
# @vacuity 🔴 the winners' record is its own file
#   file: winners.py
#   find:     with open(os.path.join(latest, "winners.json"), "w", encoding="utf-8") as fh:
#   with:     with open(os.path.join(latest, "record.json"), "w", encoding="utf-8") as fh:
#
# @vacuity 🔴 the verifier re-computes the winners' record
#   file: verify_record.py
#   find:        not _bad and tuple(_tally) == (_wr.get("w"), _wr.get("n"), _wr.get("voids")),
#   with:        True,
"""
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
import collect as CO  # noqa: E402
import winners as W  # noqa: E402
from jsblock import js_block  # noqa: E402
from tcheck import ck, section  # noqa: E402

PAGE = os.path.join(ROOT, "index.html")
SRC = open(PAGE, encoding="utf-8").read()
UTC = datetime.timezone.utc
DAY, T1, T2 = "2026-09-02", "2026-09-02T17:05:00Z", "2026-09-02T23:05:00Z"


def put(root, rel, obj):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with (gzip.open(p, "wt") if p.endswith(".gz") else open(p, "w")) as fh:
        json.dump(obj, fh)


def mg(pk, at, p_home, sp_away=2):
    return {"game_pk": pk, "commence": at, "away": "Away %d" % pk, "home": "Home %d" % pk,
            "starters": {"home": {"id": 1}, "away": {"id": sp_away}},
            "win": {"home": p_home, "away": 100 - p_home}}


def bg(pk, at, ml_h, ml_a):
    return {"id": "ev%d" % pk, "commence": at, "away": "Away %d" % pk, "home": "Home %d" % pk,
            "best_ml": {"Home %d" % pk: {"book": "fanduel", "price": ml_h},
                        "Away %d" % pk: {"book": "draftkings", "price": ml_a}}}


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 ONE ROW PER SLATE GAME, THE HIGHER-CHANCE SIDE PICKED")
# ══════════════════════════════════════════════════════════════════════
MODEL = {"slate": DAY, "games": [mg(1, T1, 61.0), mg(2, T2, 42.0), mg(3, T2, 70.0, sp_away=None)]}
BOARD = {"games": [bg(1, T1, -150, 130), bg(2, T2, 120, -140), bg(3, T2, -200, 170)]}
MLB = W.mlb_rows(MODEL, BOARD)
ck("🔴 MLB: every game in the model's file has exactly one row, the pick the higher-chance side, "
   "priced at the board's best for that team",
   [(r["game_id"], r["pick"], r["chance"], r["price"]) for r in MLB]
   == [("1", "Home 1", 61, -150), ("2", "Away 2", 58, -140), ("3", None, None, None)],
   str([(r["game_id"], r["pick"], r["chance"], r["price"]) for r in MLB]))
ck("🔴 MLB: a game whose two starters are not both named shows the game with no pick yet",
   MLB[2]["pick"] is None and MLB[2]["away"] == "Away 3")
et = lambda c: (datetime.datetime.strptime(c, "%Y-%m-%dT%H:%M:%SZ")   # noqa: E731
                - datetime.timedelta(hours=4)).strftime("%Y-%m-%d")
FBM = {"win_chances": [
    {"game_id": "g1", "commence": "2026-09-27T17:00:00Z", "away": "Jets", "home": "Bills",
     "p_home": 64.2, "best_ml": {"home": {"price": -190, "book": "fanduel"}}},
    {"game_id": "g2", "commence": "2026-09-27T20:25:00Z", "away": "Lions", "home": "Bears",
     "p_home": 33.0, "best_ml": {"away": {"price": -180, "book": "hardrockbet"}}},
    {"game_id": "g3", "commence": "2026-09-29T00:15:00Z", "away": "Rams", "home": "Saints",
     "p_home": 55.0, "best_ml": {}}]}
FB = W.fb_rows(FBM, "2026-09-27", et)
ck("🔴 football: every game of the slate's ONE day, both teams' chances in, the higher one picked",
   [(r["game_id"], r["pick"], r["chance"], r["price"]) for r in FB]
   == [("g1", "Bills", 64, -190), ("g2", "Lions", 67, -180)],
   str([(r["game_id"], r["pick"], r["chance"]) for r in FB]))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE SHIPPED PAGE DRAWS EACH ROW, AND NO LADDER, BOX OR TAG, IN ANY LEAGUE")
# ══════════════════════════════════════════════════════════════════════
DRIVER = r"""
const S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const fn = new Function('sgn', 'bookName', S.rl + '\n' + S.wh + '\nreturn winnersHtml;');
const winnersHtml = fn(x => (x > 0 ? '+' : '') + x, k => k);
process.stdout.write(JSON.stringify(S.docs.map(d => winnersHtml(d).replace(/\s+/g, ' '))));
"""
DOCS = [{"league": "mlb", "rows": MLB, "record": {"w": 3, "n": 5, "pct": 60.0}},
        {"league": "nfl", "rows": FB, "record": {"w": 0, "n": 0}},
        {"league": "ncaaf", "rows": list(reversed(FB)), "record": {}}]
tmp = tempfile.mkdtemp(prefix="winpage-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"rl": js_block("winnersRecordLine", PAGE), "wh": js_block("winnersHtml", PAGE),
               "docs": DOCS}, open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=300)
    OUT = json.loads(r.stdout) if r.returncode == 0 else ["", "", ""]
finally:
    shutil.rmtree(tmp, ignore_errors=True)
_rows = [h.count("<tr>") - 1 for h in OUT]          # minus the header row
ck("🔴 the shipped page draws one row per slate game in every league",
   r.returncode == 0 and _rows == [3, 2, 2], "%s %s" % (_rows, (r.stderr or "")[-200:]))
ck("🔴 ...the pick, its chance and its price; an MLB game missing a starter reads 'No pick yet'",
   "<b>Home 1</b>" in OUT[0] and "61%" in OUT[0] and "-150 fanduel" in OUT[0]
   and "No pick yet" in OUT[0] and "<b>Lions</b>" in OUT[1] and "67%" in OUT[1], OUT[0][:300])
ck("🔴 ...sorted by start time, whatever order the file holds",
   OUT[2].index("Bills") < OUT[2].index("Lions"), OUT[2][:200])
ck("🔴 the winners' own record line at the top, only when something is graded",
   OUT[0].startswith("<p data-wrec>") and "3 won, 2 lost" in OUT[0] and "data-wrec" not in OUT[1])
_BANNED = ("glr", "glgame", "ladder", "rung", "Alt ", "fair", "class=\"kind", "note", "warn",
           "⚠", "Model %", "Books&rsquo; chance")
ck("⛔ no ladder, box or tag in the tab, in any league",
   all(not any(b in h for b in _BANNED) for h in OUT), str([b for h in OUT for b in _BANNED if b in h]))
_gone = [f for f in ("fbGlRung", "fbGlMain", "fbGlFair", "fbGlGame", "fbGlParlays",
                     "fbGlRecordHtml", "fbGameLinesHtml") if ("function %s(" % f) in SRC]
ck("⛔ ...and the ladder renderers are gone from the shipped page; both tabs draw winnersHtml",
   not _gone and "winnersHtml(W)" in js_block("fbGameLinesTab", PAGE)
   and "winnersHtml(W)" in js_block("renderGameLines", PAGE)
   and "gamelines:renderGameLines" in js_block("show", PAGE), "still defined: %s" % _gone)

# `[Sam, 2026-10-06]` the MLB heading read the raw date ("2026-10-03"); it is
#    drawn through football's own day helper, rendered here by the shipped code.
HEAD = r"""
const S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const view = {innerHTML: ''};
const fn = new Function('$', 'winnersLoad', 'winnersHtml',
  S.dn + '\n' + S.gl + '\nreturn renderGameLines;');
fn(() => view, async () => ({slate: '2026-10-03', rows: []}), () => '')()
  .then(() => process.stdout.write(JSON.stringify(view.innerHTML)));
"""
tmp = tempfile.mkdtemp(prefix="winhead-")
try:
    open(os.path.join(tmp, "h.js"), "w", encoding="utf-8").write(HEAD)
    json.dump({"dn": js_block("fbDayName", PAGE), "gl": js_block("renderGameLines", PAGE)},
              open(os.path.join(tmp, "h.json"), "w"))
    _h = subprocess.run(["node", os.path.join(tmp, "h.js"), os.path.join(tmp, "h.json")],
                        capture_output=True, text=True, timeout=300)
    _head = json.loads(_h.stdout) if _h.returncode == 0 else ""
finally:
    shutil.rmtree(tmp, ignore_errors=True)
ck("🔴 the MLB tab's heading names the day the way football's does (\"Saturday, October 3\"), "
   "through the same helper, never the raw date",
   all(w in _head for w in ("Game Lines", "Saturday", "October", " 3"))
   and "2026-10-03" not in _head and "fbDayName(W.slate)" in js_block("renderGameLines", PAGE)
   and "fbDayName(W.slate)" in js_block("fbGameLinesTab", PAGE),
   (_head or _h.stderr)[-300:])

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 FROZEN AT THE START, GRADED ONCE, ITS OWN RECORD, RE-COMPUTED")
# ══════════════════════════════════════════════════════════════════════
at = lambda hh, mm=0: datetime.datetime(2026, 9, 2, hh, mm, tzinfo=UTC)   # noqa: E731
FINAL = lambda h, a: {"slate_date": DAY, "n_games": 1, "n_final": 1, "games": [   # noqa: E731
    {"gamePk": 1, "state": "Final", "score": {"home": h, "away": a}, "pitchers": [], "batters": []}]}
t, cwd = tempfile.mkdtemp(prefix="winrec-"), os.getcwd()
try:
    put(t, "data/latest/board.json", BOARD)
    put(t, "picks/%s.json" % DAY, {"date": DAY, "kind": "gizmos-card", "picks": []})
    put(t, "data/latest/mlb-game-model.json", {"slate": DAY, "games": [mg(1, T1, 61.0)]})
    W.build("mlb", root=t, when=at(14), log=lambda *a: None)          # before the start: home
    put(t, "data/latest/mlb-game-model.json", {"slate": DAY, "games": [mg(1, T1, 30.0)]})
    put(t, "data/2026-09-02/winner-picks/1800.json.gz",                 # a save AFTER the start
        {"league": "mlb", "taken_at": "2026-09-02T18:00:00Z",
         "rows": [dict(W.make_row(1, T1, "Away 1", "Home 1", 30.0, None, None))]})
    _mid = W.build("mlb", root=t, when=at(18, 30), log=lambda *a: None)
    put(t, "data/%s/results/final.json.gz" % DAY, FINAL(5, 3))       # filed under its slate
    _g1 = W.build("mlb", root=t, when=at(23), log=lambda *a: None)
    put(t, "data/2026-09-03/winner-grades/0100.json.gz",               # a LATER grade, flipped
        {"league": "mlb", "grades": [{"game_id": "1", "state": "graded", "won": False}]})
    _g2 = W.build("mlb", root=t, when=at(23, 30), log=lambda *a: None)
    _latest = sorted(os.listdir(os.path.join(t, "data", "latest")))
    os.chdir(t)
    CO.collect_record()                                                 # the props record, beside it
    _rec = json.load(open("data/latest/record.json"))
    for f in ("verify_record.py", "collect.py", "record_grader.py"):
        shutil.copy(os.path.join(ROOT, f), t)
    _v1 = subprocess.run([sys.executable, "verify_record.py"], cwd=t, capture_output=True,
                         text=True, env=dict(os.environ, PYTHONUTF8="1"))
    _wj = json.load(open("data/latest/winners.json"))
    _wj["record"]["w"] = 0
    json.dump(_wj, open("data/latest/winners.json", "w"))
    _v2 = subprocess.run([sys.executable, "verify_record.py"], cwd=t, capture_output=True,
                         text=True, env=dict(os.environ, PYTHONUTF8="1"))
finally:
    os.chdir(cwd)
    shutil.rmtree(t, ignore_errors=True)
ck("🔴 a started game shows the pick saved before its start (Home 1), not the model's newer "
   "number, and a save taken after the start never sets it",
   [(r["pick"], r["chance"]) for r in _mid["rows"]] == [("Home 1", 61)], str(_mid["rows"]))
ck("🔴 graded once from the final score: won 5-3, and a later, different grade never replaces it",
   (_g1["record"]["w"], _g1["record"]["n"]) == (1, 1)
   and (_g2["record"]["w"], _g2["record"]["n"]) == (1, 1), "%s / %s" % (_g1["record"], _g2["record"]))
ck("🔴 the winners' record is its own file: winners.json beside an untouched props record",
   "winners.json" in _latest and _rec.get("overall", {}).get("n") == 0
   and "winners" not in json.dumps(_rec), "%s %s" % (_latest, _rec.get("overall")))
ck("✅ verify_record re-computes the winners' record a second way and agrees",
   _v1.returncode == 0 and "the mlb winners reproduce in their own line (1/1, 0 void)" in _v1.stdout,
   (_v1.stdout + _v1.stderr)[-400:])
ck("🔴 ...and fails a winners record that is wrong",
   _v2.returncode == 1 and "the mlb winners reproduce" in _v2.stdout, _v2.stdout[-300:])
ck("🔴 each league's Track Record shows the winners' line from winners.json, never from record.json",
   "winnersRecordLine(W)" in js_block("renderRecord", PAGE) and "winnersRecordLine(W)" in js_block("fbRecord", PAGE)
   and "winnersLoad('mlb')" in js_block("renderRecord", PAGE) and "winnersLoad(LEAGUE)" in js_block("fbRecord", PAGE))
