#!/usr/bin/env python3
"""test_track_record.py — THE TRACK RECORD: BOARD, PLAYER PROPS, GAME LINES, ALL THREE LEAGUES.

`[Sam, 2026-10-17]` *"in track record we should have a game lines tracker so we
an track how the model does for game lines. lose the was the record right?
section of it. i only want the board hit % to be shown(this is the 25 player
props and all the game lines hit %) and i want both hit % to be shown. so we
would have a player prop hit % and a game line hit %. all in all wed have 3
different hit rate % shows at the top of the track record tab, board(all
picks), player props(only player props), and game line(only game lines)"*.
Asked, he chose for MLB "Remove both" ("Does the confidence number mean
anything?" and "Is v5.0 still the best version?") and, below the three, "Just
the by-date lists".

PLANTED DATA ONLY: every card, log, schedule and snapshot below is written into
a temp tree; nothing reads `data/` or `picks/`. It asks:
  1. `record_fb.grade_game_lines`: every game line a football card SHOWED, graded
     once from the final score (moneyline by the margin's sign, a spread or
     alternate spread at the team's own point, a total over / under, a push or a
     tie void); the same game in two cards graded once, from the LATER card; a
     card without a liked list graded from today's list AND its earlier slates;
     a row joined by its `sched_id`, or through `line_ids`; by ET kickoff day.
  2. `record_fb.main` run from a planted tree: `board` = the props + the game
     lines, `overall` still the props alone, record-detail's `game_lines` by day.
  2b. `[2026-10-17]` the REPO's record_fb.py run with the planted tree as its working
     directory grades exactly what its copy there does: every file, the schedule too, from
     the tree (beside game_lines_fb.py, the checkout's live schedule graded planted cards).
  3. MLB: `collect_record` writes `board` = the props + the game lines, and
     `verify_record.py` fails a record whose board disagrees; each game line carries its
     final score.
  4. The page in node, on the records sections 2 and 3 WROTE (never on a record
     shaped by hand): three boxes, Board / Player props / Game lines in that
     order with the grader's numbers; "Player props by day" and "Game lines by
     day", each graded day opening its own rows; ~~"Was the record right?",
     "Does the confidence number mean anything?", "Is v5.0 still the best
     version?", the winners' line and the market table~~ are gone; an anytime TD
     reads "Yes", never "Under null".

# @vacuity 🔴 the same game in two cards: the LATER card decides
#   file: record_fb.py
#   find: last.update(by_game)
#   with: [last.setdefault(_k, _v) for _k, _v in by_game.items()]
#
# @vacuity 🔴 ...later by generated_at, whatever order the cards arrive in
#   file: record_fb.py
#   find: for _f, card in sorted(cards, key=lambda fc: fc[1].get("generated_at") or ""):
#   with: for _f, card in cards:
#
# @vacuity 🔴 a card with no liked list keeps its earlier slates' rows graded
#   file: record_fb.py
#   find: for v in (card.get(card_fb.GL_EARLIER) or {}).values():
#   with: for v in {}.values():
#
# @vacuity 🔴 a card with a liked list is graded on that list, the page's
#   file: record_fb.py
#   find: if "game_lines_liked" in card:
#   with: if False:
#
# @vacuity 🔴 only the model's own rows (kind fb-line) are graded
#   file: record_fb.py
#   find: and r.get("kind") == "fb-line"
#   with: and True
#
# @vacuity 🔴 a row with a sched_id joins by it
#   file: record_fb.py
#   find: sid = str(r.get("sched_id") or ids.get(k) or "")
#   with: sid = str(ids.get(k) or "")
#
# @vacuity 🔴 a row without one joins through line_ids' (away, home, kickoff) map
#   file: record_fb.py
#   find: sid = str(r.get("sched_id") or ids.get(k) or "")
#   with: sid = str(r.get("sched_id") or "")
#
# @vacuity 🔴 line_ids reads a model-picks row's "<away> at <home>"
#   file: record_fb.py
#   find: if (away is None or home is None) and " at " in str(r.get("game") or ""):
#   with: if False:
#
# @vacuity 🔴 a moneyline is graded by the margin's sign ON THE PICK'S SIDE
#   file: record_fb.py
#   find: won = None if m == 0 else (m > 0) == (r.get("side") == "home")
#   with: won = None if m == 0 else (m > 0)
#
# @vacuity 🔴 a tied game's moneyline is void
#   file: record_fb.py
#   find: won = None if m == 0 else (m > 0) == (r.get("side") == "home")
#   with: won = (m > 0) == (r.get("side") == "home")
#
# @vacuity 🔴 a push is void, never a miss
#   file: record_fb.py
#   find: won = grade("total" if mk == "total" else "spread", r.get("side"), r.get("line"), hs, as_)
#   with: won = grade("total" if mk == "total" else "spread", r.get("side"), r.get("line"), hs, as_) or False
#
# @vacuity 🔴 a spread is graded at the PICKED team's own point, home or away
#   file: record_fb.py
#   find: won = grade("total" if mk == "total" else "spread", r.get("side"), r.get("line"), hs, as_)
#   with: won = grade("total" if mk == "total" else "spread", r.get("side") if mk == "total" else "home", r.get("line"), hs, as_)
#
# @vacuity 🔴 a row's day is its ET kickoff date, never the UTC one
#   file: record_fb.py
#   find: rows.append({"date": card_fb.et_date(r.get("commence")), "market": r.get("market"),
#   with: rows.append({"date": str(r.get("commence"))[:10], "market": r.get("market"),
#
# @vacuity 🔴 football's Board is the props plus the game lines
#   file: record_fb.py
#   find: "board": tally(A + _gl_graded),
#   with: "board": tally(A),
#
# @vacuity 🔴 record-detail carries the game lines by day
#   file: record_fb.py
#   find: "game_lines": {d: [x for x in _gl.get("rows") or [] if x["date"] == d]
#   with: "game_lines_off": {d: [x for x in _gl.get("rows") or [] if x["date"] == d]
#
# @vacuity 🔴 MLB's Board is the props plus the game lines
#   file: collect.py
#   find: "board": tally(allrows + gl_rows),
#   with: "board": tally(allrows),
#
# @vacuity 🔴 verify_record fails a board that is not the props plus the game lines
#   file: verify_record.py
#   find: (_b.get("w"), _b.get("n")) == (REC["overall"]["w"] + (_gl.get("w") or 0), REC["overall"]["n"] + (_gl.get("n") or 0))
#   with: True
#
# @vacuity 🔴 a box prints the grader's pct
#   file: index.html
#   find: <div class="v">${t && t.n ? t.pct.toFixed(1) + '%' : '&mdash;'}</div>
#   with: <div class="v">${t && t.n ? t.w + '%' : '&mdash;'}</div>
#
# @vacuity 🔴 ...and an em-dash when nothing is graded, never 0%
#   file: index.html
#   find: <div class="v">${t && t.n ? t.pct.toFixed(1) + '%' : '&mdash;'}</div>
#   with: <div class="v">${t && t.n ? t.pct.toFixed(1) + '%' : '0.0%'}</div>
#
# @vacuity 🔴 a moneyline reads "<team> to win"
#   file: index.html
#   find: if (r.market === 'moneyline') return `${who} to win`;
#   with: if (r.market === 'moneyline') return `${who} ${r.line}`;
#
# @vacuity 🔴 a spread prints its signed point
#   file: index.html
#   find: return `${who} ${r.line == null ? '' : sgn(r.line)}${r.market === 'alternate_spread' ? ' (alternate)' : ''}`;
#   with: return `${who} ${r.line == null ? '' : r.line}${r.market === 'alternate_spread' ? ' (alternate)' : ''}`;
#
# @vacuity 🔴 a void game line reads VOID
#   file: index.html
#   find: (r.void || r.state === 'void') ? ['v', 'VOID']
#   with: false ? ['v', 'VOID']
#
# @vacuity 🔴 a game line prints its final score
#   file: index.html
#   find: const fin = (r.home_score != null && r.away_score != null) ? `${r.away_score}&ndash;${r.home_score}` : '&mdash;';
#   with: const fin = '&mdash;';
#
# @vacuity 🔴 a football game-lines day carries data-gldate, never data-date
#   file: index.html
#   find: ${open ? ` data-gldate="${d.date}"` : ''}
#   with: ${open ? ` data-date="${d.date}"` : ''}
#
# @vacuity 🔴 ...and MLB's too
#   file: index.html
#   find: <tr class="dayrow" data-gldate="${d.date}" title="Click to see every game line from this day">
#   with: <tr class="dayrow" data-date="${d.date}" title="Click to see every game line from this day">
#
# @vacuity 🔴 an MLB game-lines day opens its own box
#   file: index.html
#   find: const box = document.querySelector((gl ? '#gl-' : '#dd-') + date);
#   with: const box = document.querySelector('#dd-' + date);
#
# @vacuity 🔴 a football game-lines day opens its own box
#   file: index.html
#   find: const box = document.querySelector((gl ? '#fbgl-' : '#fbdd-') + date);
#   with: const box = document.querySelector('#fbdd-' + date);
#
# @vacuity 🔴 ...with the day's game lines, not its props
#   file: index.html
#   find: cell.innerHTML = gl ? lineDetailHtml(((D || {}).game_lines || {})[date])
#   with: cell.innerHTML = gl ? fbDayDetailHtml(((D || {}).days || {})[date])
#
# @vacuity 🔴 an anytime TD reads Yes, never Under
#   file: index.html
#   find: <td>${r.side === 'over' ? 'Over' : r.side === 'under' ? 'Under' : 'Yes'}${
#   with: <td>${r.side === 'over' ? 'Over' : 'Under'}${
#
# @vacuity 🔴 ...and prints no "null" line
#   file: index.html
#   find: r.line == null ? '' : ' ' + r.line} ${r.market_label || r.market}</td>
#   with: ' ' + r.line} ${r.market_label || r.market}</td>
#
# @vacuity 🔴 football's three boxes: Board, Player props, Game lines, in that order
#   file: index.html
#   find: const hero = `<div class="tr-hero">${trBox('Board', R && R.board)}${trBox('Player props', R && R.overall)}${
#   with: const hero = `<div class="tr-hero">${trBox('Player props', R && R.overall)}${trBox('Board', R && R.board)}${
#
# @vacuity 🔴 MLB's Board box is the board, not the props
#   file: index.html
#   find: const hero = `<div class="tr-hero">${trBox('Board', R.board)}${trBox('Player props', R.overall)}${
#   with: const hero = `<div class="tr-hero">${trBox('Board', R.overall)}${trBox('Player props', R.overall)}${
#
# @vacuity 🔴 ...and its Game lines box the game lines
#   file: index.html
#   find: trBox('Game lines', G)}</div>`;
#   with: trBox('Game lines', R.overall)}</div>`;
#
# @vacuity ⛔ [Sam, 2026-10-17] football draws no "Was the record right?"
#   file: index.html
#   find: const lineRows = fbLineDayRows(((R && R.game_lines) || {}).by_day || []);
#   with: const lineRows = '<h3>Was the record right?</h3>' + fbLineDayRows(((R && R.game_lines) || {}).by_day || []);
#
# @vacuity ⛔ [Sam, 2026-10-17] MLB draws no "Does the confidence number mean anything?"
#   file: index.html
#   find: ${lineRows ? `<h3 style="margin:18px 0 8px;font-size:14px">Game lines by day</h3>
#   with: <div class="panel"><h2>Does the confidence number mean anything?</h2></div>${lineRows ? `<h3 style="margin:18px 0 8px;font-size:14px">Game lines by day</h3>
#
# @vacuity 🔴 [2026-10-17] football's game_lines carries its tally at the TOP, which the box reads
#   file: record_fb.py
#   find: "game_lines": {**(_gl.get("overall") or {}), **{k: v for k, v in _gl.items() if k != "rows"}},
#   with: "game_lines": {k: v for k, v in _gl.items() if k != "rows"},
#
# @vacuity 🔴 [2026-10-17] the game lines are graded on the schedule in the grader's own tree
#   file: record_fb.py
#   find: _glf.schedule_by_id(LEAGUE, "."), line_ids(LEAGUE), _glf.grade_rung)
#   with: _glf.schedule_by_id(LEAGUE), line_ids(LEAGUE), _glf.grade_rung)
#
# @vacuity 🔴 [2026-10-17] ...and so are the alternate spreads
#   file: record_fb.py
#   find: _glf.schedule_by_id(LEAGUE, "."), _glf.grade_rung)
#   with: _glf.schedule_by_id(LEAGUE), _glf.grade_rung)
#
# @vacuity 🔴 [2026-10-17] an MLB game line carries its final score, as football's does
#   file: collect.py
#   find: "home_score": sc.get("home") if w is not None else None,
#   with: "home_score": None,
"""
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
# ⚠️ collect.py is MLB's grader and reads LEAGUE once, at import; record_fb.py and
#    card_fb.py are football only and exit under mlb. So each is imported under its own.
os.environ["LEAGUE"] = "mlb"
import collect as CO  # noqa: E402
os.environ["LEAGUE"] = "nfl"
import record_fb as RF  # noqa: E402
import game_lines_fb as GLF  # noqa: E402
from jsblock import calls, js_block  # noqa: E402
from tcheck import ck, copy_module, eq, section, shown  # noqa: E402

PAGE = os.path.join(ROOT, "index.html")
SRC = open(PAGE, encoding="utf-8").read()
ENV = dict(os.environ, PYTHONUTF8="1", ODDS_API_KEY="")


def put(root, rel, obj):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with (gzip.open(p, "wt", encoding="utf-8") if p.endswith(".gz")
          else open(p, "w", encoding="utf-8")) as fh:
        json.dump(obj, fh)


def tally(w, n):
    return {"w": w, "n": n, "pct": round(100 * w / n, 1) if n else None}


def ckq(name, ok, detail):
    """`ck` that prints its (long, captured) detail only when the check fails."""
    return ck(name, ok, "" if ok else detail)


# ══════════════════════════════════════════════════════════════════════
# THE PLANTED FOOTBALL WEEK. (away, home, kickoff, schedule id, final home-away)
# ══════════════════════════════════════════════════════════════════════
GAMES = {
    "G1": ("Away One", "Home One", "2026-10-11T17:00:00Z", "S1", (24, 17)),        # home by 7, total 41
    "G2": ("Away Two", "Home Two", "2026-10-13T00:15:00Z", "S2", (20, 30)),        # Monday night ET 10-12
    "G3": ("Away Three", "Home Three", "2026-10-11T20:25:00Z", "S3", (20, 20)),    # a tie
    "G4": ("Away Four", "Home Four", "2026-10-11T17:00:00Z", "S4", (27, 13)),      # in two cards
    "G5": ("Away Five", "Home Five", "2026-10-11T17:00:00Z", "S5", (10, 3)),       # the earlier card only
    "G6": ("Away Six", "Home Six", "2026-10-09T00:15:00Z", "S6", (28, 14)),        # Thursday night ET 10-08
    "G7": ("Away Seven", "Home Seven", "2026-10-05T17:00:00Z", "S7", (24, 21)),    # an earlier slate, total 45
    "G8": ("Away Eight", "Home Eight", "2026-10-11T17:00:00Z", "S8", (30, 0)),     # not on the liked list
    "G9": ("Away Nine", "Home Nine", "2026-10-12T17:00:00Z", "S9", (21, 24)),      # sched_id only
    "G10": ("Away Ten", "Home Ten", "2026-10-11T17:00:00Z", None, None),           # in no schedule
    "G11": ("Away Eleven", "Home Eleven", "2026-10-18T17:00:00Z", "S11", None),    # not played yet
}
LABEL = {"moneyline": "Moneyline", "spread": "Spread", "alternate_spread": "Alternate spread",
         "total": "Total"}


def gl(g, mk, side, line, who, **kw):
    away, home, at = GAMES[g][:3]
    return dict({"kind": "fb-line", "league": "nfl", "market": mk, "market_label": LABEL[mk],
                 "side": side, "line": line, "player": who, "away": away, "home": home,
                 "commence": at, "game": "%s @ %s" % (away, home), "price": -110,
                 "book": "fanduel", "confidence": 60, "confidence_basis": "MODEL",
                 "sched_id": None}, **kw)


PROPS = [{"player": "Plant Receiver", "market": mk, "market_label": lab, "side": side, "line": line,
          "price": -115, "book": "fanduel", "confidence": 64, "confidence_basis": "MODEL",
          "raw": "6 of 9", "commence": "2026-10-11T17:00:00Z", "game": "Away One @ Home One"}
         for mk, lab, side, line in (("player_reception_yds", "Receiving yards", "over", 60.5),   # 80: W
                                     ("player_receptions", "Receptions", "under", 5.5),           # 6: L
                                     ("player_anytime_td", "Anytime TD", "yes", None))]           # 1: W
LIKED_B = [gl("G1", "moneyline", "home", None, "Home One"),
           gl("G1", "spread", "home", -3.5, "Home One"),
           gl("G1", "spread", "home", -7.0, "Home One"),                       # lands on 7: a push
           gl("G1", "alternate_spread", "home", -6.5, "Home One", sched_id="S1"),
           gl("G1", "total", "over", 40.5, "Over"),
           gl("G2", "moneyline", "away", None, "Away Two"),
           gl("G2", "spread", "away", -6.5, "Away Two"),
           gl("G2", "alternate_spread", "away", -10.5, "Away Two", sched_id="S2"),
           gl("G2", "total", "under", 49.5, "Under"),
           gl("G3", "moneyline", "home", None, "Home Three"),
           gl("G4", "moneyline", "home", None, "Home Four"),
           gl("G9", "alternate_spread", "away", 2.5, "Away Nine", sched_id="S9"),
           gl("G10", "moneyline", "home", None, "Home Ten"),
           gl("G11", "moneyline", "home", None, "Home Eleven")]
CARD_B = {"date": "2026-10-11", "league": "nfl", "generated_at": "2026-10-11T12:00:00Z",
          "logs_season": 2026, "picks": PROPS, "liked": PROPS, "game_lines_liked": LIKED_B,
          "game_lines": LIKED_B + [gl("G8", "moneyline", "home", None, "Home Eight")]}
CARD_A = {"date": "2026-10-10", "league": "nfl", "generated_at": "2026-10-10T12:00:00Z",
          "picks": [], "liked": [],
          "game_lines_liked": [gl("G4", "moneyline", "away", None, "Away Four"),
                               gl("G4", "spread", "away", 7.5, "Away Four"),
                               gl("G5", "moneyline", "home", None, "Home Five")]}
CARD_C = {"date": "2026-10-09", "league": "nfl", "generated_at": "2026-10-09T12:00:00Z", "picks": [],
          "game_lines": [gl("G6", "moneyline", "home", None, "Home Six"),
                         dict(gl("G6", "spread", "away", 9.5, "Away Six"), kind="price-gap")],
          "game_lines_earlier_slates": {"2026-10-05": [gl("G7", "total", "over", 44.5, "Over")]}}
SCHEDULE = {"season": 2026, "games": [
    {"id": sid, "away": a, "home": h, "start": at[:16], "final": fin is not None,
     "home_score": fin[0] if fin else None, "away_score": fin[1] if fin else None}
    for a, h, at, sid, fin in GAMES.values() if sid]}
# the (away, home, kickoff) -> schedule id snapshots: model picks name "<away> at <home>",
#    winner picks carry the two teams. ⛔ G9 and G10 are in neither.
MODEL_PICKS = {"league": "nfl", "game_model": [
    {"game": "%s at %s" % (GAMES[g][0], GAMES[g][1]), "game_id": GAMES[g][3], "commence": GAMES[g][2],
     "market": "moneyline"} for g in ("G1", "G3", "G5", "G7")]}
WINNER_PICKS = {"league": "nfl", "rows": [
    {"away": GAMES[g][0], "home": GAMES[g][1], "game_id": GAMES[g][3], "commence": GAMES[g][2]}
    for g in ("G2", "G4", "G6", "G8", "G11")]}
LOG = {"season": 2026, "players": {"p1": {"name": "Plant Receiver", "pos": "WR", "g": [
    {"d": "2026-10-11", "week": 6, "rec": 6, "rec_yds": 80, "rec_td": 1, "rush_td": 0, "car": 0,
     "rush_yds": 0, "pass_yds": 0, "pass_td": 0, "att": 0, "snaps": 50, "snap_pct": 0.8,
     "team": "Home One"}]}}}


def plant_fb(t):
    put(t, "picks/fb-nfl-2026-10-11.json", CARD_B)
    put(t, "picks/fb-nfl-2026-10-10.json", CARD_A)
    put(t, "picks/fb-nfl-2026-10-09.json", CARD_C)
    put(t, "data/nfl/latest/schedule-2026.json.gz", SCHEDULE)
    put(t, "data/nfl/latest/players-2026.json.gz", LOG)
    put(t, "data/nfl/2026-10-10/model-picks/1312.json.gz", MODEL_PICKS)
    put(t, "data/nfl/2026-10-10/winner-picks/1312.json.gz", WINNER_PICKS)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 EVERY GAME LINE A FOOTBALL CARD SHOWED, GRADED ONCE FROM THE FINAL SCORE")
# ══════════════════════════════════════════════════════════════════════
_t1 = tempfile.mkdtemp(prefix="trk-fb1-")
try:
    plant_fb(_t1)
    IDS = RF.line_ids("nfl", root=_t1)
    SCHED = GLF.schedule_by_id("nfl", root=_t1)
finally:
    shutil.rmtree(_t1, ignore_errors=True)
_want_ids = {(GAMES[g][0], GAMES[g][1], GAMES[g][2][:16]): GAMES[g][3]
             for g in ("G1", "G3", "G5", "G7", "G2", "G4", "G6", "G8", "G11")}
eq(IDS, _want_ids, "🔴 line_ids maps (away, home, kickoff minute) to the schedule id, from the model "
   "picks' \"<away> at <home>\" AND the winner picks' two teams")
# ⚠️ the cards arrive LATER FIRST, so only the generated_at order can make the later one decide
GL = RF.grade_game_lines([("b", CARD_B), ("c", CARD_C), ("a", CARD_A)], SCHED, IDS, GLF.grade_rung)
ROWS = GL.get("rows") or []
_by = {}
for _r in ROWS:
    _by.setdefault((_r["game"].split(" @ ")[1], _r["market"], _r["side"], _r["line"]), []).append(_r)


def got(home, mk, side, line=None):
    rs = _by.get((home, mk, side, line)) or []
    return [(r["state"], r["won"]) for r in rs]


ck("🔴 a moneyline is graded by the margin's sign on the pick's side: Home One won 24-17 (HIT), "
   "Away Two won 30-20 on the road (HIT)",
   got("Home One", "moneyline", "home") == [("graded", True)]
   and got("Home Two", "moneyline", "away") == [("graded", True)],
   "%s %s" % (got("Home One", "moneyline", "home"), got("Home Two", "moneyline", "away")))
ck("🔴 a spread at the team's OWN point: home -3.5 on a 7-point win HITS; away -6.5 on a 10-point road "
   "win HITS",
   got("Home One", "spread", "home", -3.5) == [("graded", True)]
   and got("Home Two", "spread", "away", -6.5) == [("graded", True)],
   "%s %s" % (got("Home One", "spread", "home", -3.5), got("Home Two", "spread", "away", -6.5)))
ck("🔴 an alternate spread the same way: home -6.5 HITS, away -10.5 MISSES by half a point, "
   "away +2.5 on a 3-point road win HITS",
   got("Home One", "alternate_spread", "home", -6.5) == [("graded", True)]
   and got("Home Two", "alternate_spread", "away", -10.5) == [("graded", False)]
   and got("Home Nine", "alternate_spread", "away", 2.5) == [("graded", True)],
   str([got("Home One", "alternate_spread", "home", -6.5), got("Home Two", "alternate_spread", "away", -10.5),
        got("Home Nine", "alternate_spread", "away", 2.5)]))
ck("🔴 a total over / under: over 40.5 on 41 HITS, under 49.5 on 50 MISSES, an earlier slate's "
   "over 44.5 on 45 HITS",
   got("Home One", "total", "over", 40.5) == [("graded", True)]
   and got("Home Two", "total", "under", 49.5) == [("graded", False)]
   and got("Home Seven", "total", "over", 44.5) == [("graded", True)])
ck("🔴 a push is VOID, never a miss: home -7 on a 7-point win",
   got("Home One", "spread", "home", -7.0) == [("void", None)], str(got("Home One", "spread", "home", -7.0)))
ck("🔴 a tie is VOID: the 20-20 game's moneyline",
   got("Home Three", "moneyline", "home") == [("void", None)], str(got("Home Three", "moneyline", "home")))
_g4 = [(r["market"], r["side"], r["won"]) for r in ROWS if r["game"] == "Away Four @ Home Four"]
eq(_g4, [("moneyline", "home", True)],
   "🔴 the same game in two cards is graded ONCE, from the LATER card by generated_at (Home Four, "
   "not the earlier card's Away Four rows), whatever order the cards arrive in")
ck("✅ ...and a game only the earlier card showed is still graded from it (Home Five)",
   got("Home Five", "moneyline", "home") == [("graded", True)])
ck("🔴 a card without game_lines_liked is graded from today's list AND its earlier slates "
   "(card_fb.GL_EARLIER): Home Six and the 10-05 total",
   got("Home Six", "moneyline", "home") == [("graded", True)]
   and got("Home Seven", "total", "over", 44.5) == [("graded", True)])
ck("⛔ a card WITH game_lines_liked is graded on that list only: Home Eight, in its game_lines and not "
   "on the page's list, is never graded",
   not any(r["game"] == "Away Eight @ Home Eight" for r in ROWS))
ck("⛔ only the model's own rows (kind fb-line): the price-gap row on Home Six is never graded",
   not any(r["game"] == "Away Six @ Home Six" and r["market"] == "spread" for r in ROWS))
ck("🔴 a row with a sched_id joins by it (Away Nine, in no snapshot), one without through line_ids "
   "(every Home One row)",
   got("Home Nine", "alternate_spread", "away", 2.5) == [("graded", True)]
   and all(r["state"] == "graded" or r["state"] == "void" for r in ROWS if r["game"] == "Away One @ Home One"))
ck("✅ a game in no schedule is unresolved; a game not yet final is pending; neither is in a tally",
   got("Home Ten", "moneyline", "home") == [("no game found", None)]
   and got("Home Eleven", "moneyline", "home") == [("pending", None)]
   and (GL.get("unresolved"), GL.get("pending")) == (1, 1))
_r1 = (_by.get(("Home One", "moneyline", "home", None)) or [{}])[0]
_r11 = (_by.get(("Home Eleven", "moneyline", "home", None)) or [{}])[0]
ck("✅ a graded row carries its final score; a pending one does not",
   (_r1.get("home_score"), _r1.get("away_score")) == (24, 17)
   and (_r11.get("home_score"), _r11.get("away_score")) == (None, None))
eq({k: GL.get(k) for k in ("overall", "shown", "voids", "from")},
   {"overall": tally(11, 13), "shown": 17, "voids": 2, "from": "2026-10-05"},
   "🔴 the game lines' own tally: 11 of 13 graded, 2 void, 17 shown, from 10-05")
eq(GL.get("by_market"), {"moneyline": tally(5, 5), "spread": tally(2, 2),
                         "alternate_spread": tally(2, 3), "total": tally(2, 3)},
   "✅ ...by market")
BY_DAY = [dict(tally(1, 1), date="2026-10-05", voids=0, pending=0),
          dict(tally(1, 1), date="2026-10-08", voids=0, pending=0),
          dict(tally(6, 6), date="2026-10-11", voids=2, pending=0),
          dict(tally(3, 5), date="2026-10-12", voids=0, pending=0),
          dict(tally(0, 0), date="2026-10-18", voids=0, pending=1)]
eq(GL.get("by_day"), BY_DAY,
   "🔴 by ET kickoff day: Thursday's 00:15Z game is 10-08 and Monday's 00:15Z game 10-12, never "
   "their UTC dates")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 record_fb.main: THE BOARD IS THE PROPS PLUS THE GAME LINES (a planted tree)")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ record_fb.py runs from its OWN copy in the tree: game_lines_fb reads the schedule beside
#    the module (its ROOT), so a run of the repo's copy would read the live schedule.
_t2 = tempfile.mkdtemp(prefix="trk-fb2-")
try:
    copy_module("record_fb", _t2)
    plant_fb(_t2)
    _p2 = subprocess.run([sys.executable, os.path.join(_t2, "record_fb.py")], cwd=_t2,
                         env=dict(ENV, LEAGUE="nfl", FB_RECORD_FROM="2026-09-01"),
                         capture_output=True, text=True, timeout=600)
    _rp = os.path.join(_t2, "data", "nfl", "latest", "record.json")
    _dp = os.path.join(_t2, "data", "nfl", "latest", "record-detail.json.gz")
    FB_R = json.load(open(_rp, encoding="utf-8")) if os.path.exists(_rp) else {}
    FB_D = json.load(gzip.open(_dp, "rt", encoding="utf-8")) if os.path.exists(_dp) else {}
finally:
    shutil.rmtree(_t2, ignore_errors=True)
ck("✅ record_fb ran on the planted tree", _p2.returncode == 0 and FB_R,
   "" if _p2.returncode == 0 and FB_R else shown((_p2.stdout + _p2.stderr)[-600:]))
eq(FB_R.get("overall"), tally(2, 3),
   "⛔ `overall` stays the player props alone: 2 of 3 (receiving yards over, the anytime TD)")
_glr = FB_R.get("game_lines") or {}
eq({k: _glr.get(k) for k in ("overall", "by_day", "voids", "pending", "unresolved")},
   {"overall": tally(11, 13), "by_day": BY_DAY, "voids": 2, "pending": 1, "unresolved": 1},
   "🔴 record.json `game_lines` is the game-lines tracker, the same 11 of 13 as section 1")
ck("⛔ ...and carries no rows (they live in record-detail)", "rows" not in _glr)
eq({k: _glr.get(k) for k in ("w", "n", "pct")}, tally(11, 13),
   "🔴 [2026-10-17] ...with its tally at the TOP (w / n / pct), MLB's shape, the one the page's "
   "box reads (nested only, the football box always read \"nothing graded yet\")")
eq((FB_R.get("alt_spreads") or {}).get("overall"), tally(2, 3),
   "✅ the card's alternate spreads, graded from the planted schedule: 2 of 3")
eq(FB_R.get("board"), tally(2 + 11, 3 + 13),
   "🔴 `board` = the props + the game lines: 13 of 16")
_dgl = FB_D.get("game_lines") or {}
eq(sorted(_dgl), [d["date"] for d in BY_DAY],
   "🔴 record-detail carries `game_lines` keyed by ET kickoff day")
eq(sorted((r["player"], r["market"], r["line"], r["state"]) for r in _dgl.get("2026-10-12") or []),
   sorted([("Away Two", "alternate_spread", -10.5, "graded"), ("Away Two", "moneyline", None, "graded"),
           ("Away Two", "spread", -6.5, "graded"), ("Under", "total", 49.5, "graded"),
           ("Away Nine", "alternate_spread", 2.5, "graded")]),
   "✅ ...each day its own rows with their verdicts (10-12: Monday night and Away Nine)")
eq(len((FB_D.get("days") or {}).get("2026-10-11") or []), 3,
   "✅ ...beside the props' own day, unchanged")

# ⛔ `[2026-10-17]` and the REPO's record_fb.py, run with the planted tree as its working
#    directory, reads every file from that tree, its schedule too: beside game_lines_fb.py (its
#    module root), the checkout's LIVE schedule graded a test's planted cards.
_t2b = tempfile.mkdtemp(prefix="trk-fb2b-")
try:
    plant_fb(_t2b)
    _p2b = subprocess.run([sys.executable, os.path.join(ROOT, "record_fb.py")], cwd=_t2b,
                          env=dict(ENV, LEAGUE="nfl", FB_RECORD_FROM="2026-09-01"),
                          capture_output=True, text=True, timeout=600)
    _rp2b = os.path.join(_t2b, "data", "nfl", "latest", "record.json")
    FB_R2 = json.load(open(_rp2b, encoding="utf-8")) if os.path.exists(_rp2b) else {}
finally:
    shutil.rmtree(_t2b, ignore_errors=True)
ck("✅ the repo's record_fb.py ran in the planted tree", _p2b.returncode == 0 and FB_R2,
   "" if _p2b.returncode == 0 and FB_R2 else shown((_p2b.stdout + _p2b.stderr)[-600:]))
_K2 = ("overall", "board", "game_lines", "alt_spreads")
eq({k: FB_R2.get(k) for k in _K2}, {k: FB_R.get(k) for k in _K2},
   "🔴 ...and grades exactly what its copy there grades: the game lines and the alternate "
   "spreads from the TREE's schedule, never the checkout's")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 MLB: collect_record's BOARD, AND verify_record FAILS ONE THAT DISAGREES")
# ══════════════════════════════════════════════════════════════════════
D1 = "2026-09-02"


def mgl(pk, mk, side, line=None):
    return {"kind": "mlb-line", "market": mk, "side": side, "line": line,
            "player": ("Home %d" if side == "home" else "Away %d") % pk, "game_pk": pk,
            "price": -120, "confidence": 60, "game": "Away %d @ Home %d" % (pk, pk)}


MLB_CARD = {"date": D1, "kind": "gizmos-card", "picks": [
    {"kind": "pitcher", "market": "strikeouts", "side": "over", "line": 5.5, "pid": 555,
     "pitcher": "Plant Ace", "confidence": 60, "game": "Away 1 @ Home 1"},       # 7 K: W
    {"kind": "pitcher", "market": "outs", "side": "over", "line": 18.5, "pid": 556,
     "pitcher": "Plant Arm", "confidence": 58, "game": "Away 2 @ Home 2"},       # 18 outs: L
    {"kind": "pitcher", "market": "strikeouts", "side": "over", "line": 2.5, "pid": 556,
     "pitcher": "Plant Arm", "confidence": 57, "game": "Away 2 @ Home 2"}],      # 3 K: W
    "game_lines": [mgl(1, "moneyline", "home"), mgl(2, "run_line", "away", 1.5),
                   mgl(3, "moneyline", "home"), mgl(1, "total", "over", 6.5)]}
MLB_FINAL = {"slate_date": D1, "n_games": 3, "n_final": 2, "games": [
    {"gamePk": 1, "state": "Final", "away": "Away 1", "home": "Home 1", "score": {"away": 2, "home": 5},
     "pitchers": [{"id": 555, "started": True, "k": 7, "outs": 18}], "batters": []},
    {"gamePk": 2, "state": "Final", "away": "Away 2", "home": "Home 2", "score": {"away": 1, "home": 3},
     "pitchers": [{"id": 556, "started": True, "k": 3, "outs": 18}], "batters": []},
    {"gamePk": 3, "state": "Postponed", "away": "Away 3", "home": "Home 3", "score": {},
     "pitchers": [], "batters": []}]}


def mlb_record():
    """collect_record on the planted MLB slate, then verify_record twice: on the record as
    written, and on one whose board disagrees (its own pct kept consistent, so only the
    sum can catch it). -> (record, detail, (rc, out) good, (rc, out) tampered)."""
    t, cwd = tempfile.mkdtemp(prefix="trk-mlb-"), os.getcwd()
    try:
        put(t, "picks/%s.json" % D1, MLB_CARD)
        put(t, "data/%s/results/final.json.gz" % D1, MLB_FINAL)
        os.makedirs(os.path.join(t, "data", "latest"))
        os.chdir(t)
        CO.collect_record()
        rec = json.load(open("data/latest/record.json", encoding="utf-8"))
        det = json.load(gzip.open("data/latest/record-detail.json.gz", "rt", encoding="utf-8"))
        for f in ("verify_record.py", "collect.py", "record_grader.py"):
            shutil.copy(os.path.join(ROOT, f), t)
        res = []
        for tamper in (False, True):
            if tamper:
                b = dict(rec["board"])
                b["w"], b["n"] = b["w"] + 1, b["n"] + 1
                b["pct"] = round(100 * b["w"] / b["n"], 1)
                json.dump(dict(rec, board=b), open("data/latest/record.json", "w", encoding="utf-8"))
            p = subprocess.run([sys.executable, "verify_record.py"], cwd=t, capture_output=True,
                               text=True, env=dict(ENV, LEAGUE="mlb"), timeout=600)
            res.append((p.returncode, p.stdout + p.stderr))
        return rec, det, res[0], res[1]
    finally:
        os.chdir(cwd)
        shutil.rmtree(t, ignore_errors=True)


MLB_R, MLB_D, (_vrc, _vout), (_trc, _tout) = mlb_record()
eq(MLB_R.get("overall"), tally(2, 3), "⛔ MLB `overall` stays the player props alone: 2 of 3")
eq({k: (MLB_R.get("game_lines") or {}).get(k) for k in ("w", "n", "voids")}, {"w": 1, "n": 2, "voids": 1},
   "✅ MLB's game lines in their own line: the moneyline won, the run line lost, the postponed one void")
eq(MLB_R.get("board"), tally(3, 5), "🔴 MLB `board` = the props + the game lines: 3 of 5")
eq((MLB_R.get("game_lines") or {}).get("by_day"), [dict(date=D1, **tally(1, 2))],
   "✅ ...and the game lines by day, which the tab lists")
eq(len((MLB_D.get("game_lines") or {}).get(D1) or []), 3,
   "✅ record-detail carries the day's three game lines, the void one included")
eq({r.get("team"): (r.get("away_score"), r.get("home_score"))
    for r in (MLB_D.get("game_lines") or {}).get(D1) or []},
   {"Home 1": (2, 5), "Away 2": (1, 3), "Home 3": (None, None)},
   "🔴 [2026-10-17] each MLB game line carries its final (away, home), as football's do; a "
   "postponed game none")
_vok = _vrc == 0 and "PASS the board is the props plus the game lines (3/5)" in _vout
ck("✅ verify_record re-checks the board and agrees", _vok, "" if _vok else shown(_vout[-600:]))
_tok = _trc == 1 and "FAIL the board is the props plus the game lines (4/6)" in _tout
ck("🔴 ...and FAILS a record whose board is not the props plus the game lines (4 of 6, its pct "
   "consistent)", _tok, "" if _tok else shown(_tout[-600:]))

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE PAGE, IN NODE, ON THE RECORDS THE GRADERS WROTE")
# ══════════════════════════════════════════════════════════════════════
FNS = ("trBox", "lineDetailHtml", "dayDetailHtml", "fbLineDayRows", "fbDayRows", "fbDayDetailHtml",
       "fbWireDayRows", "fbRecord", "renderRecord")


def _decl(pat):
    """A top-level declaration the page's functions read, pulled out of the page, never retyped."""
    m = re.search(pat, SRC, re.M)
    assert m, "index.html no longer declares %s" % pat
    return m.group(0)

DRIVER = r"""
const fs = require('fs');
const S = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
%(decls)s
let LEAGUE = 'nfl';
let RECORD = null;
const VIEW = {innerHTML: ''};
const $ = sel => VIEW;
const fbShell = inner => inner;
const fbWire = () => {};
const freshness = iso => 'at ' + iso;
let FBR = null, FBD = null, MLBD = null;
async function fbRecordLoad(){ return FBR; }
async function fbDetailLoad(lg, rec){ return FBD; }
async function loadRecordDetail(){ return MLBD; }
async function jget(u){ throw new Error('a test fetches nothing: ' + u); }
/* A DOM read off the markup the page wrote: every <tr class="dayrow"> with its data-*
   attributes, and a box for every id="..." the markup really holds. */
let ROWS = [], BOXES = {};
function fakeTr(ds){ const h = {}; return {dataset: ds, classList: {add(){}, remove(){}},
  addEventListener(e, f){ h[e] = f; }, click(){ return h.click ? h.click() : null; }}; }
function fakeBox(){ const cell = {innerHTML: '', dataset: {}};
  return {hidden: true, cell, querySelector: () => cell}; }
const document = {
  querySelectorAll(sel){
    ROWS = [...VIEW.innerHTML.matchAll(/<tr class="dayrow"([^>]*)>/g)].map(m => {
      const ds = {};
      for (const a of m[1].matchAll(/data-([a-z]+)="([^"]*)"/g)) ds[a[1]] = a[2];
      return fakeTr(ds);
    });
    return ROWS;
  },
  querySelector(sel){
    const id = sel.replace(/^#/, '');
    if (!VIEW.innerHTML.includes('id="' + id + '"')) return null;
    return BOXES[id] || (BOXES[id] = fakeBox());
  }
};
%(fns)s
const tick = () => new Promise(r => setTimeout(r, 5));
const boxes = h => [...h.matchAll(/<div class="k">([^<]*)<\/div>\s*<div class="v">([^<]*)<\/div>\s*<div class="s">([^<]*)<\/div>/g)].map(m => [m[1], m[2], m[3]]);
async function click(pred){ const tr = ROWS.find(pred); if (!tr) return 'no row'; await tr.click(); return 'opened'; }
const cells = () => Object.fromEntries(Object.entries(BOXES).map(([k, b]) => [k, b.cell.innerHTML]));
(async () => {
  const O = {};
  O.trFull = trBox('Board', {w: 3, n: 5, pct: 60});
  O.trEmpty = trBox('Game lines', {w: 0, n: 0, pct: null});
  O.trNone = trBox('Player props', undefined);
  O.lines = S.lines.map(r => lineDetailHtml([r]).replace(/\s+/g, ' '));
  O.lineEmpty = lineDetailHtml([]);
  O.days = fbLineDayRows(S.days).replace(/\s+/g, ' ');
  O.daysEmpty = fbLineDayRows([]);
  O.td = fbDayDetailHtml(S.td).replace(/\s+/g, ' ');
  LEAGUE = 'nfl'; FBR = S.fbR; FBD = S.fbD; BOXES = {}; ROWS = [];
  await fbRecord();
  O.fb = VIEW.innerHTML.replace(/\s+/g, ' '); O.fbBoxes = boxes(VIEW.innerHTML);
  O.fbRows = ROWS.map(t => t.dataset);
  O.fbClickGl = await click(t => t.dataset.gldate === S.fbDay);
  O.fbClickDd = await click(t => t.dataset.date === S.fbDay);
  O.fbCells = cells();
  RECORD = S.mlbR; MLBD = S.mlbD; BOXES = {}; ROWS = [];
  await renderRecord();
  await tick();
  O.mlb = VIEW.innerHTML.replace(/\s+/g, ' '); O.mlbBoxes = boxes(VIEW.innerHTML);
  O.mlbRows = ROWS.map(t => t.dataset);
  O.mlbClickGl = await click(t => t.dataset.gldate === S.mlbDay);
  O.mlbClickDd = await click(t => t.dataset.date === S.mlbDay);
  O.mlbCells = cells();
  process.stdout.write(JSON.stringify(O));
})().catch(e => { process.stdout.write(JSON.stringify({__err: String((e && e.stack) || e)})); });
"""
LINES = [
    {"market": "moneyline", "player": "Away Two", "side": "away", "line": None, "price": 135, "confidence": 61,
     "game": "Away Two @ Home Two", "home_score": 20, "away_score": 30, "won": True, "state": "graded"},
    {"market": "spread", "player": "Home One", "side": "home", "line": -3.5, "price": -110, "confidence": 58,
     "game": "Away One @ Home One", "home_score": 24, "away_score": 17, "won": True, "state": "graded"},
    {"market": "spread", "player": "Away Nine", "side": "away", "line": 2.5, "price": -105, "confidence": 55,
     "game": "Away Nine @ Home Nine", "home_score": 24, "away_score": 21, "won": False, "state": "graded"},
    {"market": "alternate_spread", "player": "Home One", "side": "home", "line": -6.5, "price": 150,
     "confidence": 52, "game": "Away One @ Home One", "home_score": 24, "away_score": 17, "won": True,
     "state": "graded"},
    {"market": "total", "player": "Under", "side": "under", "line": 49.5, "price": -110, "confidence": 57,
     "game": "Away Two @ Home Two", "home_score": 20, "away_score": 30, "won": False, "state": "graded"},
    {"market": "spread", "player": "Home One", "side": "home", "line": -7, "price": -110, "confidence": 54,
     "game": "Away One @ Home One", "home_score": 24, "away_score": 17, "won": None, "state": "void"},
    {"market": "moneyline", "team": "Home 3", "line": None, "price": -120, "confidence": 60,
     "game": "Away 3 @ Home 3", "won": None, "void": True},                                    # MLB's shape
    {"market": "run_line", "team": "Away 2", "line": 1.5, "price": -120, "confidence": 60,
     "game": "Away 2 @ Home 2", "won": False, "void": False},
    {"market": "moneyline", "player": "Home Eleven", "side": "home", "line": None, "price": -150,
     "confidence": 63, "game": "Away Eleven @ Home Eleven", "home_score": None, "away_score": None,
     "won": None, "state": "pending"}]
DAYS = [dict(tally(1, 1), date="2026-10-05", voids=0, pending=0),
        dict(tally(6, 6), date="2026-10-11", voids=2, pending=0),
        dict(tally(0, 0), date="2026-10-14", voids=1, pending=0),
        dict(tally(0, 0), date="2026-10-18", voids=0, pending=1)]
_td = [r for r in (FB_D.get("days") or {}).get("2026-10-11") or [] if r.get("market") == "player_anytime_td"]
_tmp4 = tempfile.mkdtemp(prefix="trk-page-")
try:
    open(os.path.join(_tmp4, "d.js"), "w", encoding="utf-8").write(DRIVER % {
        "decls": _decl(r"^const sgn = .*;$") + "\n" + _decl(r"^const LG_NAME\s*=.*;$"),
        "fns": "\n".join(js_block(n, PAGE) for n in FNS)})
    json.dump({"lines": LINES, "days": DAYS, "td": _td, "fbR": FB_R, "fbD": FB_D, "fbDay": "2026-10-11",
               "mlbR": MLB_R, "mlbD": MLB_D, "mlbDay": D1},
              open(os.path.join(_tmp4, "d.json"), "w", encoding="utf-8"))
    _n = subprocess.run(["node", os.path.join(_tmp4, "d.js"), os.path.join(_tmp4, "d.json")],
                        capture_output=True, text=True, timeout=300)
    try:
        O = json.loads(_n.stdout)
    except ValueError:
        O = {"__err": (_n.stdout + _n.stderr)[-600:]}
finally:
    shutil.rmtree(_tmp4, ignore_errors=True)
ck("✅ the page's own functions ran in node", _n.returncode == 0 and "__err" not in O,
   shown(str(O.get("__err") or _n.stderr)[-600:]))

_bx = lambda h: re.findall(r'<div class="k">([^<]*)</div>\s*<div class="v">([^<]*)</div>\s*'   # noqa: E731
                           r'<div class="s">([^<]*)</div>', h or "")
eq(_bx(O.get("trFull")), [("Board", "60.0%", "3 of 5 graded")],
   "🔴 trBox prints the grader's pct and \"w of n graded\"")
eq(_bx(O.get("trEmpty")) + _bx(O.get("trNone")),
   [("Game lines", "&mdash;", "nothing graded yet"), ("Player props", "&mdash;", "nothing graded yet")],
   "🔴 ...and an em-dash when nothing is graded or there is no record, never 0%")

_L = O.get("lines") or [""] * len(LINES)
_want_lines = [("<b>Away Two to win</b>", "30&ndash;20", "HIT", "+135"),
               ("<b>Home One -3.5</b>", "17&ndash;24", "HIT", "-110"),
               ("<b>Away Nine +2.5</b>", "21&ndash;24", "MISS", "-105"),
               ("<b>Home One -6.5 (alternate)</b>", "17&ndash;24", "HIT", "+150"),
               ("<b>Under 49.5</b>", "30&ndash;20", "MISS", "-110"),
               ("<b>Home One -7</b>", "17&ndash;24", "VOID", "-110"),
               ("<b>Home 3 to win</b>", "&mdash;", "VOID", "-120"),
               ("<b>Away 2 +1.5</b>", "&mdash;", "MISS", "-120"),
               ("<b>Home Eleven to win</b>", "&mdash;", "UNSETTLED", "-150")]
_bad = [(i, w) for i, w in enumerate(_want_lines)
        if not (i < len(_L) and all(x in _L[i] for x in w) and "null" not in _L[i])]
ck("🔴 lineDetailHtml: a moneyline is \"<team> to win\", a spread its signed point (alternate "
   "marked), a total Over / Under its line, the final away-home, HIT / MISS, a push or postponed "
   "game VOID, an unplayed one UNSETTLED; MLB's rows (`team`) and football's (`player`) alike",
   not _bad, shown(str([(_L[i] if i < len(_L) else None, w) for i, w in _bad])[:900]))
ck("✅ ...and an empty day says so", "No game lines stored for that day." in (O.get("lineEmpty") or ""))

_days = O.get("days") or ""
_order = [m.group(1) for m in re.finditer(r"<td>(2026-10-\d\d)", _days)]
eq(_order, ["2026-10-18", "2026-10-14", "2026-10-11", "2026-10-05"],
   "✅ fbLineDayRows lists the days newest first")
eq(re.findall(r'data-gldate="([^"]*)"', _days), ["2026-10-14", "2026-10-11", "2026-10-05"],
   "🔴 every day with a graded or void line is clickable by data-gldate (a void-only day too); "
   "an unplayed one is not")
eq(re.findall(r'id="(fbgl-[^"]*)"', _days), ["fbgl-2026-10-14", "fbgl-2026-10-11", "fbgl-2026-10-05"],
   "✅ ...each with its own fbgl-<date> detail row")
ck("⛔ ...and none carries the props' data-date", "data-date=" not in _days)
ckq("✅ ...the record, the hit rate, and the unsettled count (void + pending)",
   "<td class=\"n\">6/6</td> <td class=\"n\">100.0%</td> <td class=\"n sub\">2</td>" in _days
   and "<td class=\"n\">&mdash;</td> <td class=\"n\">&mdash;</td> <td class=\"n sub\">1</td>" in _days,
   _days[:500])
ck("✅ no graded day: one plain line", "No game lines graded yet." in (O.get("daysEmpty") or ""))

_tdh = O.get("td") or ""
ckq("🔴 fbDayDetailHtml prints the anytime TD (side yes, no line) as \"Yes Anytime TD\", never "
   "\"Under null\"",
   len(_td) == 1 and "<td>Yes Anytime TD</td>" in _tdh and "null" not in _tdh and "Under" not in _tdh,
   _tdh[:400])

# ── the two tabs, on what the graders wrote ───────────────────────────
_fbgl = (FB_R.get("game_lines") or {}).get("overall") or {}
_fmt = lambda t: ("%.1f%%" % t["pct"], "%d of %d graded" % (t["w"], t["n"])) if t and t.get("n") else (  # noqa: E731
    "&mdash;", "nothing graded yet")
for _lg, _rec, _boxes, _gl_t in (("football", FB_R, O.get("fbBoxes"), _fbgl),
                                 ("MLB", MLB_R, O.get("mlbBoxes"), MLB_R.get("game_lines") or {})):
    eq([b[0] for b in _boxes or []], ["Board", "Player props", "Game lines"],
       "🔴 %s: exactly three boxes on top, Board, Player props, Game lines, in that order "
       "(~~Auto card / Pitchers / Hitters / Cards graded / On the board today~~)" % _lg)
    eq([tuple(b[1:]) for b in _boxes or []],
       [_fmt(_rec.get("board")), _fmt(_rec.get("overall")), _fmt(_gl_t)],
       "🔴 %s: each box prints the grader's own number: Board = `board`, Player props = `overall`, "
       "Game lines = the graded game lines (%s)" % (_lg, _fmt(_gl_t)[1]))
for _lg, _blk in (("football", js_block("fbRecord", PAGE)), ("MLB", js_block("renderRecord", PAGE))):
    eq(re.findall(r"trBox\('([^']+)'", _blk), ["Board", "Player props", "Game lines"],
       "✅ %s's renderer calls trBox for Board, Player props and Game lines, in that order" % _lg)

for _lg, _h in (("football", O.get("fb") or ""), ("MLB", O.get("mlb") or "")):
    ckq("🔴 %s draws \"Player props by day\" and then \"Game lines by day\"" % _lg,
       0 <= _h.find("Player props by day") < _h.find("Game lines by day"), _h[:300])
    # `[Sam, 2026-10-17]` "lose the was the record right? section"; MLB "Remove both"; below the
    #    three, "Just the by-date lists". ~~The calibration bands, "Is v5.0 still the best
    #    version?", the winners' line and the by-market table~~ are drawn by neither tab.
    _gone = [x for x in ("Was the record right?", "Does the confidence number mean anything?",
                         "Is v5.0 still the best version?", "data-wrec", 'class="band"',
                         "<th>Market</th>")
             if x in _h]
    ck("⛔ %s draws no \"Was the record right?\", no \"Does the confidence number mean anything?\", "
       "no \"Is v5.0 still the best version?\", no winners' line and no market table" % _lg,
       not _gone, str(_gone))
_srcgone = [(f, x) for f in ("fbRecord", "renderRecord")
            for x in ("winnersRecordLine", "winnersLoad", "fbCalMethods", "fbCalBlock", "bandRow",
                      "refitPanel", "mlbGameLineRecord", "mlb-refit", "by_market", "calibration")
            if x in js_block(f, PAGE)]
ck("⛔ ...nor do their renderers reach the winners' line, the bands, the model check or a market table",
   not _srcgone, str(_srcgone))
_called = {n: calls(n, PAGE) for n in ("bandRow", "refitPanel", "mlbGameLineRecord", "fbCalBlock",
                                       "fbCalMethods")}
ck("⛔ ...and nothing on the page calls the removed panels' renderers", not any(_called.values()),
   str(_called))

# ── each graded day opens its own rows ──────────────────────────────
_fbc, _mlc = O.get("fbCells") or {}, O.get("mlbCells") or {}
ck("🔴 football: the game-lines rows are data-gldate days, the props rows data-date days",
   {"gldate": "2026-10-11"} in (O.get("fbRows") or []) and {"date": "2026-10-11"} in (O.get("fbRows") or [])
   and not any("gldate" in d for d in (O.get("fbRows") or []) if "date" in d), str(O.get("fbRows")))
ckq("🔴 football: a game-lines day opens fbgl-<date> with that day's game lines from record-detail",
   O.get("fbClickGl") == "opened" and "<b>Home One to win</b>" in _fbc.get("fbgl-2026-10-11", "")
   and "<b>Home Four to win</b>" in _fbc.get("fbgl-2026-10-11", "")
   and "Plant Receiver" not in _fbc.get("fbgl-2026-10-11", ""), shown(str(_fbc)[:600]))
ckq("✅ ...and the same date's props day still opens fbdd-<date> with the props",
   O.get("fbClickDd") == "opened" and "Plant Receiver" in _fbc.get("fbdd-2026-10-11", "")
   and "to win" not in _fbc.get("fbdd-2026-10-11", ""), shown(str(_fbc)[:600]))
ckq("🔴 MLB: the game-lines day is a data-gldate row that opens gl-<date> with its game lines",
   {"gldate": D1} in (O.get("mlbRows") or []) and O.get("mlbClickGl") == "opened"
   and "<b>Home 1 to win</b>" in _mlc.get("gl-" + D1, "") and "<b>Away 2 +1.5</b>" in _mlc.get("gl-" + D1, "")
   and "VOID" in _mlc.get("gl-" + D1, ""), shown(str(_mlc)[:600]))
ckq("🔴 [2026-10-17] ...each with its final, away-home, as football's: 2-5 and 1-3",
   "2&ndash;5" in _mlc.get("gl-" + D1, "") and "1&ndash;3" in _mlc.get("gl-" + D1, ""),
   shown(str(_mlc)[:600]))
ckq("✅ ...and its props day still opens dd-<date> with the props",
   O.get("mlbClickDd") == "opened" and "Plant Ace" in _mlc.get("dd-" + D1, "")
   and "to win" not in _mlc.get("dd-" + D1, ""), shown(str(_mlc)[:600]))
