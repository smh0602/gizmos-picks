#!/usr/bin/env python3
"""EACH GAME OF A DOUBLEHEADER GETS ITS OWN ODDS — replayed from 2026-09-25.

🔴 WHAT HAPPENED. Two doubleheaders on one board pull, 12:08Z:

    CHC @ BOS   odds 17:06Z and 22:06Z   MLB 17:05Z and 22:05Z (later 21:35Z)
    BAL @ NYY   odds 20:05Z and 23:06Z   MLB 20:05Z and **20:10Z, startTimeTBD**

MLB lists the second game of a traditional doubleheader at a PLACEHOLDER
five minutes after the first. `boardFor()` matched on the nearest first
pitch, so BAL @ NYY game 2's card was handed GAME 1's odds (5 minutes
"away", against 2h56m for its own record). And its ~~4-hour~~ window was
wider than the 3.0h gap between that pair's two records, so a card whose
own record had left the board would have taken its sibling's instead.
`test_board_match.js` went red on the window, on every collect run from
06:44Z.

✅ THE FIX (index.html): the EVENT decides first — MLB's `gameNumber`
against the board's first-pitch order, when both sources list the same
number of games for the pair that day. Only when they disagree does a
FIRM first pitch decide, inside a 90-minute window, never between two
records, never on a placeholder time.

⛔ THE FIXTURE IS THE REAL DATA, NOT A SKETCH OF IT. Every row below is
copied from `data/2026-09-25/gamelines/1208.json.gz` and the schedule
snapshots `1208` and `1747` (MLB moved game 2 of CHC @ BOS from 22:05Z to
21:35Z between them, and swapped which gamePk was BAL @ NYY game 1 — only
`gameNumber` held still). §0 re-reads those files and fails if the
fixture ever drifts from them. The page's OWN `boardFor` and `etDate` are
lifted out of index.html and run in node — never a copy.

# @vacuity the old 4-hour window hands a lone half its sibling's odds
#   file: index.html
#   find: const BOARD_MATCH_WINDOW_MS = 90 * 60 * 1000;
#   with: const BOARD_MATCH_WINDOW_MS = 4 * 3600 * 1000;
#
# @vacuity without the game-number match, game 2 gets game 1's odds
#   file: index.html
#   find:   if (game){
#   with:   if (false){
#
# @vacuity an ordinal that always takes the first record is caught
#   file: index.html
#   find: return same[n - 1];
#   with: return same[0];
#
# @vacuity a placeholder time must never be matched by the clock
#   file: index.html
#   find: if (tbd) return null;
#   with: if (false) return null;
#
# @vacuity two records inside the window is a guess, and is refused
#   file: index.html
#   find: return near.length === 1 ? near[0] : null;
#   with: return near.length >= 1 ? near[0] : null;
#
# @vacuity the card must pass the game, or none of this is reached
#   file: index.html
#   find: const b = boardFor(away, home, g.gameDate, g);
#   with: const b = boardFor(away, home, g.gameDate);
"""
import gzip
import json
import os
import re
import subprocess

from jsblock import js_block
from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, "index.html")

# ── the board, `data/2026-09-25/gamelines/1208.json.gz` (id, away, home, commence)
BOARD = [
    ('a85710fa5f6fd3a6a40fe17c4907c312', 'Chicago Cubs', 'Boston Red Sox', '2026-09-25T17:06:00Z'),
    ('d4b069a134ec3ae75f0a644498b793c6', 'Baltimore Orioles', 'New York Yankees', '2026-09-25T20:05:00Z'),
    ('c1c95aa0c77e6735bae6602eec2b42be', 'Chicago Cubs', 'Boston Red Sox', '2026-09-25T22:06:00Z'),
    ('3aa03f1c80c2ca97a49e0b7548d9e647', 'Pittsburgh Pirates', 'Detroit Tigers', '2026-09-25T22:41:00Z'),
    ('6e8b1f358bb5c3837f473e61ecb68650', 'Tampa Bay Rays', 'Philadelphia Phillies', '2026-09-25T22:41:00Z'),
    ('80d706190519a0e4956a64e84e72ed94', 'New York Mets', 'Washington Nationals', '2026-09-25T22:46:00Z'),
    ('3fe14d478bc1ffac17198c460085ca70', 'Baltimore Orioles', 'New York Yankees', '2026-09-25T23:06:00Z'),
    ('890be5ce6e3ea3d7c6f0b76bd9a0e45a', 'Cincinnati Reds', 'Toronto Blue Jays', '2026-09-25T23:08:00Z'),
    ('2d3d378044cc538b0a3d77acaacd15a1', 'Atlanta Braves', 'Miami Marlins', '2026-09-25T23:11:00Z'),
    ('b6829a3017da7786aceea335c5c36bb3', 'Colorado Rockies', 'Chicago White Sox', '2026-09-25T23:40:00Z'),
    ('7bd30076728c7fcf1f893c1d269a60af', 'Cleveland Guardians', 'Kansas City Royals', '2026-09-25T23:41:00Z'),
    ('12c52c4f4de763e9a171ffac0f4f02ef', 'St. Louis Cardinals', 'Milwaukee Brewers', '2026-09-25T23:41:00Z'),
    ('9f08a9d734982153de27326c32e8be0e', 'Texas Rangers', 'Minnesota Twins', '2026-09-26T00:11:00Z'),
    ('eb8b9160f66fc6d5f6bd58bf4a888011', 'Arizona Diamondbacks', 'San Diego Padres', '2026-09-26T01:41:00Z'),
    ('de8bbf8d379bf416df612c557ddd338a', 'Houston Astros', 'Athletics', '2026-09-26T01:41:00Z'),
    ('60b3d02ac77cf6a81e234358cfe187bb', 'Los Angeles Angels', 'Seattle Mariners', '2026-09-26T02:11:00Z'),
    ('e47efe97f629cae0287ca6f3ea6d6794', 'Los Angeles Dodgers', 'San Francisco Giants', '2026-09-26T02:16:00Z'),
]
# ── MLB's schedule as the page fetched it
# (gamePk, away, home, gameDate, officialDate, doubleHeader, gameNumber, startTimeTBD)
MLB = {
    "1208": [
        (824703, 'Chicago Cubs', 'Boston Red Sox', '2026-09-25T17:05:00Z', '2026-09-25', 'S', 1, False),
        (824706, 'Chicago Cubs', 'Boston Red Sox', '2026-09-25T22:05:00Z', '2026-09-25', 'S', 2, False),
        (823491, 'Baltimore Orioles', 'New York Yankees', '2026-09-25T20:05:00Z', '2026-09-25', 'Y', 1, False),
        (823489, 'Baltimore Orioles', 'New York Yankees', '2026-09-25T20:10:00Z', '2026-09-25', 'Y', 2, True),
        (824220, 'Pittsburgh Pirates', 'Detroit Tigers', '2026-09-25T22:40:00Z', '2026-09-25', 'N', 1, False),
        (823409, 'Tampa Bay Rays', 'Philadelphia Phillies', '2026-09-25T22:40:00Z', '2026-09-25', 'N', 1, False),
        (822681, 'New York Mets', 'Washington Nationals', '2026-09-25T22:45:00Z', '2026-09-25', 'N', 1, False),
        (822760, 'Cincinnati Reds', 'Toronto Blue Jays', '2026-09-25T23:07:00Z', '2026-09-25', 'N', 1, False),
        (823816, 'Atlanta Braves', 'Miami Marlins', '2026-09-25T23:10:00Z', '2026-09-25', 'N', 1, False),
        (824058, 'Cleveland Guardians', 'Kansas City Royals', '2026-09-25T23:40:00Z', '2026-09-25', 'N', 1, False),
        (824544, 'Colorado Rockies', 'Chicago White Sox', '2026-09-25T23:40:00Z', '2026-09-25', 'N', 1, False),
        (823735, 'St. Louis Cardinals', 'Milwaukee Brewers', '2026-09-25T23:40:00Z', '2026-09-25', 'N', 1, False),
        (823652, 'Texas Rangers', 'Minnesota Twins', '2026-09-26T00:10:00Z', '2026-09-25', 'N', 1, False),
        (824947, 'Houston Astros', 'Athletics', '2026-09-26T01:40:00Z', '2026-09-25', 'N', 1, False),
        (823248, 'Arizona Diamondbacks', 'San Diego Padres', '2026-09-26T01:40:00Z', '2026-09-25', 'N', 1, False),
        (823085, 'Los Angeles Angels', 'Seattle Mariners', '2026-09-26T02:10:00Z', '2026-09-25', 'N', 1, False),
        (823167, 'Los Angeles Dodgers', 'San Francisco Giants', '2026-09-26T02:15:00Z', '2026-09-25', 'N', 1, False),
    ],
}
# 1747: the same slate after MLB moved CHC @ BOS game 2 to 21:35Z.
MLB["1747"] = [r if r[0] != 824706 else r[:3] + ('2026-09-25T21:35:00Z',) + r[4:]
               for r in MLB["1208"]]

# ⛔ THE ANSWER KEY IS WRITTEN DOWN, NOT DERIVED FROM THE RULE UNDER TEST.
# Game 1 of a doubleheader is played first; each pair's single game has one
# record. Checked by hand against the snapshots above.
EXPECT = {
    824703: 'a85710fa5f6fd3a6a40fe17c4907c312',   # CHC @ BOS game 1 · 17:06Z
    824706: 'c1c95aa0c77e6735bae6602eec2b42be',   # CHC @ BOS game 2 · 22:06Z
    823491: 'd4b069a134ec3ae75f0a644498b793c6',   # BAL @ NYY game 1 · 20:05Z
    823489: '3fe14d478bc1ffac17198c460085ca70',   # BAL @ NYY game 2 · 23:06Z
}
_rec_of = {(a, h): i for i, a, h, _c in BOARD}
for pk, a, h, *_ in MLB["1208"]:
    if pk not in EXPECT:
        EXPECT[pk] = _rec_of[(a, h)]
DH = (824703, 824706, 823491, 823489)


def game(row):
    pk, a, h, when, day, dh, n, tbd = row
    return {"gamePk": pk, "gameDate": when, "officialDate": day,
            "doubleHeader": dh, "gameNumber": n,
            "status": {"startTimeTBD": tbd},
            "teams": {"away": {"team": {"name": a}},
                      "home": {"team": {"name": h}}}}


def board(rows):
    return [{"id": i, "away": a, "home": h, "commence": c} for i, a, h, c in rows]


SRC = open(PAGE, encoding="utf-8").read()
_WIN = re.search(r"const BOARD_MATCH_WINDOW_MS\s*=\s*[^;]+;", SRC)
_ET = re.search(r"const etDate = [\s\S]*?\n};", SRC)
MATCHER = "\n".join([_ET.group(0) if _ET else "",
                     _WIN.group(0) if _WIN else "",
                     js_block("boardFor", PAGE)])
HARNESS = r"""
const I = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const out = I.queries.map(q => {
  const f = new Function('BOARD', I.src + '\n; return [boardFor, BOARD_MATCH_WINDOW_MS];');
  const [boardFor, W] = f({games: q.board});
  const r = boardFor(q.away, q.home, q.when, q.game || undefined);
  return {id: r ? r.id : null, window: W};
});
process.stdout.write(JSON.stringify(out));
"""


def run(queries):
    p = subprocess.run(["node", "-e", HARNESS], input=json.dumps(
        {"src": MATCHER, "queries": queries}), capture_output=True,
        text=True, timeout=120)
    if p.returncode != 0:
        raise SystemExit("the page's matcher did not run in node:\n" + p.stderr[-800:])
    return json.loads(p.stdout)


def ask(rows, mlb_row, with_game=True, when=None):
    g = game(mlb_row)
    return {"board": board(rows), "away": g["teams"]["away"]["team"]["name"],
            "home": g["teams"]["home"]["team"]["name"],
            "when": when or g["gameDate"], "game": g if with_game else None}


# ══════════════════════════════════════════════════════════════════════
section("0. ⛔ THE FIXTURE IS THE STORED DATA, NOT A MEMORY OF IT")
# ══════════════════════════════════════════════════════════════════════
_src_board = os.path.join(ROOT, "data/2026-09-25/gamelines/1208.json.gz")
if os.path.exists(_src_board):
    _b = json.load(gzip.open(_src_board, "rt"))
    _got = sorted((g["id"], g["away"], g["home"], g["commence"]) for g in _b["games"])
    ck(_got == sorted(BOARD), "🔴 the fixture board IS the 12:08Z pull, record "
       "for record (%d)" % len(BOARD), "differs: %s" % sorted(set(_got) ^ set(BOARD)))
else:
    note("the 12:08Z board snapshot is not in this checkout; fixture used as written")
for _snap, _rows in MLB.items():
    _p = os.path.join(ROOT, "data/2026-09-25/schedule/%s.json.gz" % _snap)
    if not os.path.exists(_p):
        note("schedule %s is not in this checkout; fixture used as written" % _snap)
        continue
    _s = json.load(gzip.open(_p, "rt"))["schedule"]
    _got = sorted((g["gamePk"], g["teams"]["away"]["team"]["name"],
                   g["teams"]["home"]["team"]["name"], g["gameDate"],
                   g.get("officialDate"), g.get("doubleHeader"),
                   g.get("gameNumber"), bool(g["status"].get("startTimeTBD")))
                  for d in _s["dates"] for g in d["games"])
    ck(_got == sorted(_rows), "🔴 schedule %s is the stored snapshot, game for "
       "game (%d)" % (_snap, len(_rows)), "differs: %s" % sorted(set(_got) ^ set(_rows)))
ck(bool(_WIN and _ET), "the page still declares its window and etDate where "
   "this file reads them", "window=%s etDate=%s" % (bool(_WIN), bool(_ET)))

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 EVERY GAME GETS ITS OWN RECORD — BOTH MOMENTS OF THE DAY")
# ══════════════════════════════════════════════════════════════════════
for _snap, _rows in MLB.items():
    _res = run([ask(BOARD, r) for r in _rows])
    _wrong = [(r[0], r[1][:10], r[6], x["id"] and x["id"][:8], EXPECT[r[0]][:8])
              for r, x in zip(_rows, _res) if x["id"] != EXPECT[r[0]]]
    ck(not _wrong, "%s: all %d games matched to their own record" % (_snap, len(_rows)),
       "⛔ (gamePk, team, game#, got, want): %s" % _wrong)
    _dh = {r[0]: x["id"] for r, x in zip(_rows, _res) if r[0] in DH}
    ck(len(set(_dh.values())) == 4 and None not in _dh.values(),
       "  🔴 %s: the four doubleheader games got FOUR different records" % _snap,
       "⛔ this is the live bug: BAL @ NYY game 2 (20:10Z placeholder) was "
       "shown game 1's odds. got %s" % {k: v and v[:8] for k, v in _dh.items()})

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 A HALF THAT LEFT THE BOARD GETS NOTHING — NEVER ITS SIBLING'S")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ The odds feed drops a game once it is over, so for part of every
#    doubleheader day one half is missing. Its card must show NO odds.
_q, _who = [], []
for _snap, _rows in MLB.items():
    for _gone in DH:
        _left = [r for r in BOARD if r[0] != EXPECT[_gone]]
        for r in _rows:
            if r[0] in DH and (r[1], r[2]) == next((x[1], x[2]) for x in _rows if x[0] == _gone):
                _q.append(ask(_left, r))
                _who.append((_snap, _gone, r[0]))
_res = run(_q)
_leak, _lost_own = [], []
for (_snap, _gone, _pk), x in zip(_who, _res):
    if _pk == _gone and x["id"] is not None:
        _leak.append("%s: game %d lost its record and got %s" % (_snap, _pk, x["id"][:8]))
    if _pk != _gone and x["id"] not in (EXPECT[_pk], None):
        _leak.append("%s: game %d got %s, not its own" % (_snap, _pk, x["id"][:8]))
    if _pk != _gone and x["id"] is None:
        _lost_own.append((_snap, _pk))
ck(len(_who) == 16 and not _leak,
   "🔴🔴 with either half removed, the missing game shows NO odds and the "
   "other shows only its own (%d cases)" % len(_who),
   "⛔ a card showing another game's line is misinformation: %s" % _leak)
note("fail-closed cases (own record present, but the counts disagree and "
     "the time is a placeholder): %s" % (_lost_own or "none"))

# ══════════════════════════════════════════════════════════════════════
section("3. ⛔ THE WINDOW IS NARROWER THAN EVERY SAME-PAIR GAP ON THIS BOARD")
# ══════════════════════════════════════════════════════════════════════
_W = run([ask(BOARD, MLB["1208"][0])])[0]["window"]
_by = {}
for _i, _a, _h, _c in BOARD:
    _by.setdefault((_a, _h), []).append(_c)
from datetime import datetime  # noqa: E402
_ts = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000
_gaps = [b - a for v in _by.values() for a, b in
         zip(sorted(map(_ts, v)), sorted(map(_ts, v))[1:])]
ck(bool(_gaps) and _W < min(_gaps),
   "the %.1fh window < the closest same-pair gap (%.1fh)"
   % (_W / 3.6e6, min(_gaps or [0]) / 3.6e6),
   "⛔ a window as wide as the gap can hand a lone half its sibling's line")

# ══════════════════════════════════════════════════════════════════════
section("4. ⛔ TWO RECORDS INSIDE THE WINDOW IS A GUESS, AND IS REFUSED")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ Derived from the real pair: the feed listing game 2 where MLB does —
#    at the 20:10Z placeholder. Asked by clock alone, nothing is certain.
_twin = [r if r[0] != EXPECT[823489] else r[:3] + ('2026-09-25T20:10:00Z',)
         for r in BOARD]
_bal1 = next(r for r in MLB["1208"] if r[0] == 823491)
_bal2 = next(r for r in MLB["1208"] if r[0] == 823489)
_res = run([ask(_twin, _bal1, with_game=False, when='2026-09-25T20:07:00Z'),
            ask(_twin, _bal1), ask(_twin, _bal2)])
ck(_res[0]["id"] is None,
   "by clock alone, two records 5 minutes apart -> null", "got %s" % _res[0]["id"])
ck(_res[1]["id"] == EXPECT[823491] and _res[2]["id"] == EXPECT[823489],
   "  ...while the game number still separates them",
   "got %s / %s" % (_res[1]["id"], _res[2]["id"]))

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE CARD PASSES THE GAME — or none of the above is reached")
# ══════════════════════════════════════════════════════════════════════
_card = js_block("gameCard", PAGE)
_calls = re.findall(r"boardFor\(([^)]*)\)", _card)
ck(_calls == ["away, home, g.gameDate, g"],
   "gameCard asks boardFor with the MLB game object",
   "⛔ without it the game-number match never runs. calls: %s" % _calls)
