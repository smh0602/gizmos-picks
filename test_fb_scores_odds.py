#!/usr/bin/env python3
r"""test_fb_scores_odds.py — every football Scores card draws ITS OWN game's odds, both leagues.

`[2026-11-13]` A verified audit found that no college Scores card had shown a moneyline or a
win % since at least PR #218 (2026-10-02). Sam asked on 2026-09-03 for "the odds under each
team". `fbBoardFor` matched a schedule game to the odds board by comparing team NAMES:
`nm(full(schedule name)) === nm(board name)`. The NFL's embedded directory carries each
team's full name, so "SEA" became "Seattle Seahawks" and 27 of 27 NFL board games joined.
College's teams.json entries carry no `name`, so the schedule's "Memphis" was compared with
the board's "Memphis Tigers", and 0 of 76 college board games joined. The card then read
`best_ml` and `win_pct` by the schedule's name too, and the board keys those by its own
spelling. No test called `fbBoardFor`.

THE CLASS: a schedule-to-board read that depends on two feeds spelling a team the same way.
So this guard runs the page's OWN code in node (`fbGameCard`, the card, and `fbOpenBox`, its
box-score modal, with every top-level function and constant they reach, lifted from
index.html) on PLANTED feeds in each league's own naming:
  * college: a CFBD-style schedule ("Memphis", zoned UTC stamps, CFBD's midnight-Eastern
    placeholder for a time not yet set), an Odds-API-style board ("Memphis Tigers", prices
    keyed by that name) and a teams.json-style directory (keyed by school, no `name`);
  * NFL: an nflverse-style schedule ("SEA", unzoned Eastern wall time), the same board shape,
    and the page's own embedded directory.
It asks:
  1. 🔴 every planted game the board carries draws BOTH teams' moneyline and win % on its card,
     and both moneylines in its modal, each team's OWN numbers (a neutral site where the two
     feeds disagree on home and away included);
  2. ⛔ nothing borrows another game's odds: Miami beside Miami (OH) and USC beside South
     Carolina on one day, the Rams beside the Chargers, a rematch weeks later, two board
     records for one pair, two unresolved teams, and a directory that cannot tell Miami from
     Miami (OH) (both refused). Such a card draws no moneyline, no win % and no betting bar.
⛔ A TEST ASKS THE CODE, NEVER PRODUCTION: every case is planted, the clock is never read by
an assertion. Today's live college and NFL files are measured as a `note()` only.

# @vacuity 🔴 the base defect: a board game is found by the feeds' NAMES again (0 of N college)
#   file: index.html
#   find: const day = B.filter(x => x && (has(x, h) || has(x, a)) && fbSameGameDay(g.start, x.commence));
#   with: const day = B.filter(x => x && [[g.home, x.home], [g.away, x.away]].every(([s, o]) => String(((fbResolve(s) || {}).name) || s).toLowerCase() === String(o).toLowerCase()));
#
# @vacuity 🔴 the base defect's other half: the card reads the board by OUR spelling of the team
#   file: index.html
#   find: const k = fbBoardKey(b, t);
#   with: const k = b && ((fbResolve(t) || {}).name || t);
#
# @vacuity 🔴 the modal reads a moneyline by the schedule's name
#   file: index.html
#   find: ${line(fbAb(g.away), (b.best_ml || {})[fbBoardKey(b, g.away)]
#   with: ${line(fbAb(g.away), (b.best_ml || {})[g.away]
#
# @vacuity ⛔ no game-day test: a rematch weeks later borrows this week's odds
#   file: index.html
#   find: const day = B.filter(x => x && (has(x, h) || has(x, a)) && fbSameGameDay(g.start, x.commence));
#   with: const day = B.filter(x => x && (has(x, h) || has(x, a)));
#
# @vacuity ⛔ two board records for one pair: the first one is taken instead of refused
#   file: index.html
#   find: return (withH.length === 1 && withA.length === 1 && withH[0] === withA[0])
#   with: return (withH.filter(x => withA.indexOf(x) > -1).length > 0)
#
# @vacuity ⛔ two unresolved teams match any board game whose teams are unresolved too
#   file: index.html
#   find: if (!h || !a || h === a) return null;
#   with: if (false) return null;
#
# @vacuity 🔴 a neutral site: each team's numbers are read by the board's name for THAT team
#   file: index.html
#   find: return fbResolve(b.home) === e ? b.home : fbResolve(b.away) === e ? b.away : null;
#   with: return fbResolve(b.home) === e ? b.away : fbResolve(b.away) === e ? b.home : null;
#
# @vacuity 🔴 CFBD's midnight placeholder for a time not yet set is the same game day
#   file: index.html
#   find: || (d < 25 * 3600e3 && etDate(x.getTime()) === etDate(y.getTime()));   // an Eastern day is at most 25h
#   with: || false;
#
# @vacuity 🔴 a kickoff moved across midnight Eastern is still the same game
#   file: index.html
#   find: return d <= FB_KICK_WINDOW_H * 3600e3
#   with: return false
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
import jsblock  # noqa: E402
from tcheck import ck, note, section, shown  # noqa: E402

IDX = os.path.join(ROOT, "index.html")

# ══════════════════════════════════════════════════════════════════════
# THE PAGE'S OWN CODE: the card and the modal, and everything they reach.
# ══════════════════════════════════════════════════════════════════════
FUNCS = jsblock.top_level_blocks(IDX)
CODE = jsblock.script_code(IDX)          # comment-free, for the constants


def _consts():
    """{name: (offset, text)} for every top-level `const`/`let` on the page,
    each through the `;` that ends it (strings and templates skipped)."""
    out = {}
    for m in re.finditer(r"^(?:const|let) ([A-Za-z_$][\w$]*)\s*=", CODE, re.M):
        j, depth, n = m.end(), 0, len(CODE)
        while j < n:
            c = CODE[j]
            if c in "\"'":
                j = jsblock._skip_quoted(CODE, j)
                continue
            if c == "`":
                j = jsblock._skip_template(CODE, j)
                continue
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
            elif c == ";" and depth == 0:
                break
            j += 1
        out[m.group(1)] = (m.start(), CODE[m.start():j + 1])
    return out


CONSTS = _consts()
IDENT = re.compile(r"[A-Za-z_$][\w$]*")


def closure(roots):
    """The top-level functions and constants `roots` reach, by name."""
    fn, cs, todo = set(), set(), list(roots)
    while todo:
        name = todo.pop()
        if name in FUNCS and name not in fn:
            fn.add(name)
            body = jsblock.strip_js(FUNCS[name])
        elif name in CONSTS and name not in cs:
            cs.add(name)
            body = CONSTS[name][1]
        else:
            continue
        todo.extend(set(IDENT.findall(body)) - fn - cs)
    return fn, cs


ROOTS = ["fbGameCard", "fbOpenBox", "fbBoardFor", "nflDirectory"]
_fn, _cs = closure(ROOTS)
ck(all(r in _fn for r in ROOTS) and {"FBBOARD", "FBTEAMS", "LEAGUE", "el"} <= _cs,
   "⚠️ the page's card, modal, board lookup and directory were lifted out of index.html",
   "%d function(s), %d constant(s)" % (len(_fn), len(_cs)))
PAGE_JS = "\n".join([CONSTS[c][1] for c in sorted(_cs, key=lambda c: CONSTS[c][0])]
                    + [FUNCS[f] for f in sorted(_fn)])

DRIVER = r"""
const __BODY = [];
function __node(tag){ return {tag, className: '', innerHTML: '', kids: [], textContent: '',
  append(...k){ this.kids.push(...k); }, addEventListener(){}, remove(){}, dispatchEvent(){},
  querySelector(s){ return s === '.x' ? __node('button') : null; }, isConnected: false}; }
const document = {createElement: t => __node(t), body: {append(n){ __BODY.push(n); }},
                  addEventListener(){}, removeEventListener(){}};
const window = {};
const __S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
""" + "\n%PAGE%\n" + r"""
LEAGUE = __S.league;
FBTEAMS[LEAGUE] = __S.teams === 'nfl' ? nflDirectory() : __S.teams;
FBBOARD[LEAGUE] = __S.board;
const __strip = h => String(h == null ? '' : h).replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
const __sideOf = n => {
  const kid = c => (n.kids || []).find(k => k.className === c);
  const win = kid('win'), ml = kid('ml');
  return {win: win ? __strip(win.innerHTML) : null, ml: ml ? __strip(ml.innerHTML) : null};
};
(async () => {
  if (__S.live){     // the measurement: the board lookup only, over the whole season
    const used = new Set();
    let cards = 0;
    __S.schedule.forEach(g => { const b = fbBoardFor(g); if (b){ cards++; used.add(b); } });
    process.stdout.write(JSON.stringify({live: {board: __S.board.games.length, joined: used.size, cards}}));
    return;
  }
  const out = [];
  for (const g of __S.schedule){
    const c = fbGameCard(g);
    const top = c.kids.find(k => k.className === 'g-top');
    const sides = top.kids.filter(k => /^tm/.test(k.className));
    __BODY.length = 0;
    await fbOpenBox(g);
    const html = __BODY.length ? __BODY[0].innerHTML : '';
    const lab = {};
    (html.match(/<span class="lab">[^<]*<\/span> <b>[^<]*<\/b>/g) || []).forEach(s => {
      const m = /<span class="lab">([^<]*)<\/span> <b>([^<]*)<\/b>/.exec(s); lab[m[1]] = m[2]; });
    out.push({key: g.key, away: __sideOf(sides[0]), home: __sideOf(sides[1]),
              bar: !!c.kids.find(k => k.className === 'bar'),
              modal: {away: lab[fbAb(g.away)] || null, home: lab[fbAb(g.home)] || null,
                      none: /No live odds stored for this game/.test(html)}});
  }
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
"""


def run(league, teams, schedule, board, live=False):
    """The page's card and modal for every schedule game, or None if node failed."""
    tmp = tempfile.mkdtemp(prefix="scodds-")
    try:
        js, data = os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")
        open(js, "w", encoding="utf-8").write(DRIVER.replace("%PAGE%", PAGE_JS))
        json.dump({"league": league, "teams": teams, "schedule": schedule,
                   "board": board, "live": live}, open(data, "w", encoding="utf-8"))
        r = subprocess.run(["node", js, data], capture_output=True, text=True,
                           encoding="utf-8", timeout=300)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if r.returncode != 0:
        print(shown((r.stderr or "")[-1500:]))
        return None
    return json.loads(r.stdout)


def bg(id_, away, home, commence, ml, win, total=44.5):
    """An Odds-API-style board record: every number keyed by the board's own team name."""
    return {"id": id_, "commence": commence, "away": away, "home": home,
            "win_pct": {away: win[0], home: win[1]},
            "best_ml": {away: {"book": "fanduel", "price": ml[0]},
                        home: {"book": "draftkings", "price": ml[1]}},
            "total": total, "run_line": -3.5, "run_line_team": home, "n_books": 3}


def sg(key, away, home, start, neutral=False):
    return {"key": key, "id": key, "away": away, "home": home, "start": start,
            "neutral": neutral, "final": False, "home_score": None, "away_score": None}


def sgn(v):
    return ("+%d" % v) if v > 0 else str(v)


def want_odds(R, cases, what):
    """Every case in `cases` ({key: (away ml, home ml, away win, home win)}) drew exactly
    those numbers on its card AND in its modal; every other planted game drew none."""
    got = {r["key"]: r for r in R}
    drawn = {k: ((r["away"]["ml"], r["home"]["ml"], r["away"]["win"], r["home"]["win"]),
                 (r["modal"]["away"], r["modal"]["home"]), r["bar"]) for k, r in got.items()}
    want = {k: ((sgn(v[0]), sgn(v[1]), "%g%%" % v[2], "%g%%" % v[3]),
                (sgn(v[0]), sgn(v[1])), True) for k, v in cases.items()}
    bad = {k: {"drew": drawn.get(k), "want": w} for k, w in want.items() if drawn.get(k) != w}
    ck(not bad,
       "🔴 %s: every game the board carries draws BOTH teams' OWN moneyline and win %% on its "
       "card, both moneylines in its modal and the betting bar" % what,
       "%d of %d planted game(s) drew them%s" % (len(want) - len(bad), len(want),
                                                 ("; wrong: %r" % bad) if bad else ""))
    blank = ((None, None, None, None), (None, None), False)
    crossed = {k: d for k, d in drawn.items() if k not in want
               and (d != blank or not got[k]["modal"]["none"])}
    ck(not crossed,
       "⛔ %s: every other planted game draws no moneyline, no win %%, no bar and says its "
       "modal has no odds, never another game's (%s)"
       % (what, ", ".join(sorted(k for k in drawn if k not in want))),
       ("borrowed: %r" % crossed) if crossed else "")


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 COLLEGE: CFBD SCHEDULE NAMES JOIN THE ODDS API'S MASCOT NAMES")
# ══════════════════════════════════════════════════════════════════════
# teams.json's shape: keyed by CFBD's school name, and NO `name` field (the base defect).
SCHOOLS = {"Memphis": "MEM", "South Florida": "USF", "Duke": "DUKE", "Miami": "MIA",
           "Miami (OH)": "M-OH", "Ohio": "OHIO", "USC": "USC", "UCLA": "UCLA",
           "South Carolina": "SC", "Clemson": "CLEM", "Army": "ARMY", "Navy": "NAVY",
           "Texas Tech": "TTU", "Baylor": "BAY", "Fresno State": "FRES", "Hawai'i": "HAW",
           "Utah": "UTAH", "TCU": "TCU"}
DIR = {k: {"abbr": v, "conference": "Planted", "logo": None} for k, v in SCHOOLS.items()}
CFB_SCHED = [
    sg("memphis-usf", "Memphis", "South Florida", "2026-11-13T01:00:00.000Z"),
    sg("duke-miami", "Duke", "Miami", "2026-11-14T17:00:00.000Z"),
    sg("ohio-miamioh", "Ohio", "Miami (OH)", "2026-11-14T17:00:00.000Z"),
    sg("usc-ucla", "USC", "UCLA", "2026-11-14T20:30:00.000Z"),
    sg("sc-clemson", "South Carolina", "Clemson", "2026-11-14T20:30:00.000Z"),
    # CFBD files a kickoff time not yet set at midnight Eastern (05:00Z in November)
    sg("ttu-baylor-tbd", "Texas Tech", "Baylor", "2026-11-21T05:00:00.000Z"),
    # a neutral site: CFBD calls Army the home side, the board calls Navy the home side
    sg("navy-army-neutral", "Navy", "Army", "2026-12-12T20:00:00.000Z", neutral=True),
    # 11:59pm Eastern on the schedule, moved to 12:30am Eastern (the next date) on the board
    sg("fresno-hawaii-midnight", "Fresno State", "Hawai'i", "2026-11-15T04:59:00.000Z"),
    # the same two teams two weeks later: the board holds only the first meeting
    sg("usf-memphis-rematch", "South Florida", "Memphis", "2026-11-27T17:00:00.000Z"),
    # the board holds TWO records for this pair
    sg("utah-tcu-two-records", "Utah", "TCU", "2026-11-14T21:00:00.000Z"),
    # neither school is in the directory (FCS); the board's same-day game is unresolved too
    sg("idahost-nau-unresolved", "Idaho State", "Northern Arizona", "2026-11-14T21:00:00.000Z"),
]
CFB_BOARD = {"games": [
    bg("b1", "Memphis Tigers", "South Florida Bulls", "2026-11-13T01:00:00Z", (-200, 180), (64.6, 35.4)),
    bg("b2", "Duke Blue Devils", "Miami Hurricanes", "2026-11-14T17:00:00Z", (240, -300), (28.1, 71.9)),
    bg("b3", "Ohio Bobcats", "Miami (OH) RedHawks", "2026-11-14T17:00:00Z", (-125, 105), (53.2, 46.8)),
    bg("b4", "USC Trojans", "UCLA Bruins", "2026-11-14T20:30:00Z", (-650, 460), (84.0, 16.0)),
    bg("b5", "Texas Tech Red Raiders", "Baylor Bears", "2026-11-21T17:00:00Z", (-380, 300), (77.5, 22.5)),
    bg("b6", "Army Black Knights", "Navy Midshipmen", "2026-12-12T20:00:00Z", (120, -142), (44.4, 55.6)),
    bg("b7", "Fresno State Bulldogs", "Hawaii Rainbow Warriors", "2026-11-15T05:30:00Z", (-170, 145), (61.0, 39.0)),
    bg("b8", "Utah Utes", "TCU Horned Frogs", "2026-11-14T21:00:00Z", (-110, -110), (50.0, 50.0)),
    bg("b9", "Utah Utes", "TCU Horned Frogs", "2026-11-14T21:00:00Z", (-150, 125), (58.0, 42.0)),
    bg("b10", "Weber State Wildcats", "Montana Grizzlies", "2026-11-14T21:00:00Z", (190, -230), (33.0, 67.0)),
]}
CFB_WANT = {
    "memphis-usf": (-200, 180, 64.6, 35.4),
    "duke-miami": (240, -300, 28.1, 71.9),
    "ohio-miamioh": (-125, 105, 53.2, 46.8),
    "usc-ucla": (-650, 460, 84.0, 16.0),
    "ttu-baylor-tbd": (-380, 300, 77.5, 22.5),
    # schedule away = Navy: Navy's own -142 and 55.6, never Army's (the board's away side)
    "navy-army-neutral": (-142, 120, 55.6, 44.4),
    "fresno-hawaii-midnight": (-170, 145, 61.0, 39.0),
}
R = run("ncaaf", DIR, CFB_SCHED, CFB_BOARD)
ck(R is not None, "⚠️ the page's own code ran in node on the planted college feeds", "")
if R is not None:
    want_odds(R, CFB_WANT, "college")

print("\n   — a directory that cannot tell Miami from Miami (OH) —")
# Without "Miami (OH)" in the directory, the resolver's prefix walk reads "Miami (OH)" and
# "Miami (OH) RedHawks" as Miami: Miami is then in two board games that day, and neither
# Miami card may show odds (it cannot know which record is its own).
DIR2 = {k: v for k, v in DIR.items() if k != "Miami (OH)"}
R2 = run("ncaaf", DIR2, [g for g in CFB_SCHED if g["key"] in
                         ("memphis-usf", "duke-miami", "ohio-miamioh")], CFB_BOARD)
ck(R2 is not None, "⚠️ the page's own code ran in node on the collapsed directory", "")
if R2 is not None:
    want_odds(R2, {"memphis-usf": CFB_WANT["memphis-usf"]}, "college, Miami collapsed")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 NFL: NFLVERSE ABBREVIATIONS AND EASTERN WALL TIME JOIN THE ODDS API")
# ══════════════════════════════════════════════════════════════════════
NFL_SCHED = [
    sg("sea-la", "SEA", "LA", "2026-11-15T16:05"),
    # flexed: 1:00pm Eastern on the stored schedule, 4:25pm on the board (3h25m)
    sg("kc-den-flex", "KC", "DEN", "2026-11-15T13:00"),
    sg("dal-was", "DAL", "WAS", "2026-11-15T13:00"),
    # the division rematch six weeks later, home and away reversed
    sg("was-dal-rematch", "WAS", "DAL", "2026-12-27T13:00"),
    # the other Los Angeles team, the same day, not on the board
    sg("lac-lv", "LAC", "LV", "2026-11-15T16:25"),
    sg("nyj-nyg", "NYJ", "NYG", "2026-11-16T20:15"),
]
NFL_BOARD = {"games": [
    bg("n1", "Seattle Seahawks", "Los Angeles Rams", "2026-11-15T21:05:00Z", (150, -178), (39.0, 61.0)),
    bg("n2", "Kansas City Chiefs", "Denver Broncos", "2026-11-15T21:25:00Z", (-135, 114), (55.8, 44.2)),
    bg("n3", "Dallas Cowboys", "Washington Commanders", "2026-11-15T18:00:00Z", (105, -125), (47.5, 52.5)),
    bg("n4", "New York Jets", "New York Giants", "2026-11-17T01:15:00Z", (130, -155), (42.0, 58.0)),
]}
NFL_WANT = {"sea-la": (150, -178, 39.0, 61.0), "kc-den-flex": (-135, 114, 55.8, 44.2),
            "dal-was": (105, -125, 47.5, 52.5), "nyj-nyg": (130, -155, 42.0, 58.0)}
RN = run("nfl", "nfl", NFL_SCHED, NFL_BOARD)
ck(RN is not None, "⚠️ the page's own code ran in node on the planted NFL feeds", "")
if RN is not None:
    want_odds(RN, NFL_WANT, "NFL")

# ══════════════════════════════════════════════════════════════════════
section("3. ⚪ TODAY'S LIVE FILES (MEASURED, NEVER ASSERTED)")
# ══════════════════════════════════════════════════════════════════════


def _load(p):
    with (gzip.open(p, "rt", encoding="utf-8") if p.endswith(".gz") else
          open(p, encoding="utf-8")) as f:
        return json.load(f)


for lg in ("ncaaf", "nfl"):
    base = os.path.join(ROOT, "data", lg, "latest")
    try:
        board = _load(os.path.join(base, "board.json"))
        scheds = sorted(f for f in os.listdir(base) if re.match(r"schedule-\d{4}\.json\.gz$", f))
        sched = _load(os.path.join(base, scheds[-1]))["games"]
        teams = "nfl" if lg == "nfl" else _load(os.path.join(base, "teams.json")).get("teams", {})
    except (OSError, ValueError, IndexError, KeyError) as e:
        note("%s: live files not readable here (%s)" % (lg, e))
        continue
    L = run(lg, teams, [dict(g, key=str(g.get("id"))) for g in sched],
            {"games": board.get("games") or []}, live=True)
    if L is None:
        note("%s: the live measurement did not run" % lg)
        continue
    L = L["live"]
    note("%s live: %d of %d board games join a schedule game (%d card(s) draw odds), "
         "%s" % (lg, L["joined"], L["board"], L["cards"], scheds[-1]))
