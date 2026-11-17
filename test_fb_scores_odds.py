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
     `[2026-11-13, review]` Also: two teams the board has in two DIFFERENT games that day
     (Duke @ UCLA), both sides one directory entry (Ohio Dominican @ Ohio), and the college
     rematch 6 days 16 hours later (a finale, then the conference title game), so the window
     is held below a week, not only present;
  3. ⛔ no two sportsbook names resolve to one team: Houston's card had drawn no odds beside
     "Houston Baptist Huskies" (Houston Christian, read as Houston). Planted in 1, and asked of
     every name in every stored gamelines snapshot, both leagues, RECORDED in research/.
  `[2026-11-13, review round 2]` Two more, planted in 1:
  * 🔴 an FBS team against an FCS school (outside CFBD's FBS directory, so it never resolves)
    draws its odds: Chattanooga @ Alabama, Minnesota at Northern Iowa (the FCS side at home on
    the board), Houston Christian @ Rice. ⛔ And it fails closed: Division II's "Minnesota
    Duluth" reads as Minnesota (the schedule's own class must say FBS), an FBS team in two
    board games that day (Samford @ Auburn), an FBS team whose one board game is against
    another FBS team (Tennessee Tech @ Mississippi State), and two FBS schools missing from a
    stale directory beside a board game that is missing from it too (Missouri State @ Delaware);
  * 🔴 CFBD's midnight placeholder for a NIGHT game: the board's 10:30pm Eastern kickoff is the
    next UTC date and 22.5 hours away (Indiana @ Washington), so neither a UTC date nor a
    12-hour window can stand in for the Eastern date.
⛔ A TEST ASKS THE CODE, NEVER PRODUCTION: every case is planted or recorded, the clock is
never read by an assertion. Today's live college and NFL files are measured as a `note()` only.

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
# @vacuity ⛔ neither side in the directory: two missing FBS schools borrow a missing pair's odds
#   file: index.html
#   find: if (h === a) return null;
#   with: if (h && h === a) return null;
#
# @vacuity 🔴 a neutral site: each team's numbers are read by the board's name for THAT team
#   file: index.html
#   find: if (e) return bh === e ? b.home : ba === e ? b.away : null;
#   with: if (e) return bh === e ? b.away : ba === e ? b.home : null;
#
# @vacuity 🔴 an FBS team against an FCS school: the card fails closed again and draws nothing
#   file: index.html
#   find: if (!h || !a) return fbBoardForFcs(g, B, has, h ? 'home' : 'away');
#   with: if (!h || !a) return null;
#
# @vacuity ⛔ the schedule's own class unread: Division II's "Minnesota Duluth" takes Minnesota's
#   file: index.html
#   find: if (String(g[side + '_class'] || '').toLowerCase() !== 'fbs') return null;
#   with: if (false) return null;
#
# @vacuity ⛔ an FBS team in two board games that day: the first one is taken
#   file: index.html
#   find: if (day.length !== 1) return null;
#   with: if (!day.length) return null;
#
# @vacuity ⛔ the FBS team's one board game is against another FBS team: the FCS card takes it
#   file: index.html
#   find: return fbResolve(other) ? null : x;
#   with: return x;
#
# @vacuity 🔴 the FCS team's own numbers: read by the board's side outside the directory
#   file: index.html
#   find: return (bh && !ba) ? b.away : (ba && !bh) ? b.home : null;
#   with: return (bh && !ba) ? b.home : (ba && !bh) ? b.away : null;
#
# @vacuity 🔴 a UTC date is not a game's date: CFBD's placeholder beside a 10:30pm Eastern kickoff
#   file: index.html
#   find: || (d < 25 * 3600e3 && etDate(x.getTime()) === etDate(y.getTime()));
#   with: || (d < 25 * 3600e3 && x.toISOString().slice(0, 10) === y.toISOString().slice(0, 10));
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
#
# @vacuity ⛔ the two teams in two DIFFERENT board games that day: one team's game is taken
#   file: index.html
#   find: return (withH.length === 1 && withA.length === 1 && withH[0] === withA[0])
#   with: return (withH.length === 1 && withA.length === 1)
#
# @vacuity ⛔ both sides one directory entry (Ohio Dominican read as Ohio): Ohio's odds twice
#   file: index.html
#   find: if (h === a) return null;
#   with: if (!h && !a) return null;
#
# @vacuity ⛔ the game-day window widened past a week: the finale reads the title game's odds
#   file: index.html
#   find: const FB_KICK_WINDOW_H = 4;
#   with: const FB_KICK_WINDOW_H = 24 * 8;
#
# @vacuity 🔴 "Houston Baptist Huskies" read as Houston again: Houston's own card is blank
#   file: index.html
#   find: 'kentucky','methodist','chicago','st','saint','a','baptist']);
#   with: 'kentucky','methodist','chicago','st','saint','a']);
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
const __collide = names => {   // directory entries two different names resolve to
  const by = new Map();
  [...new Set(names)].forEach(n => { const e = fbResolve(n); if (e) by.set(e, (by.get(e) || []).concat([n])); });
  const out = {n: new Set(names).size, resolved: 0, collide: []};
  by.forEach((v, e) => { out.resolved += v.length; if (v.length > 1) out.collide.push([e.abbr || '?', v]); });
  return out;
};
(async () => {
  if (__S.live){     // the measurement: the board lookup only, over the whole season
    const used = new Set();
    let cards = 0;
    __S.schedule.forEach(g => { const b = fbBoardFor(g); if (b){ cards++; used.add(b); } });
    const names = __collide(__S.board.games.flatMap(b => [b.away, b.home]).filter(Boolean));
    process.stdout.write(JSON.stringify({live: {board: __S.board.games.length, joined: used.size, cards,
                                                collide: names.collide}}));
    return;
  }
  if (__S.names){    // the class: no two sportsbook names may resolve to one team
    process.stdout.write(JSON.stringify({names: __collide(__S.names)}));
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


def run(league, teams, schedule, board, live=False, names=None):
    """The page's card and modal for every schedule game, or None if node failed."""
    tmp = tempfile.mkdtemp(prefix="scodds-")
    try:
        js, data = os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")
        open(js, "w", encoding="utf-8").write(DRIVER.replace("%PAGE%", PAGE_JS))
        json.dump({"league": league, "teams": teams, "schedule": schedule,
                   "board": board, "live": live, "names": names},
                  open(data, "w", encoding="utf-8"))
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


def cg(key, away, home, start, cls=("fbs", "fbs"), neutral=False):
    """A CFBD-style schedule game: `sg` plus CFBD's own division of each side
    (`away_class`, `home_class`: 'fbs', 'fcs', 'ii', 'iii')."""
    return dict(sg(key, away, home, start, neutral=neutral), away_class=cls[0], home_class=cls[1])


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
           "Utah": "UTAH", "TCU": "TCU", "Oregon State": "ORST", "Houston": "HOU",
           "Rice": "RICE", "Alabama": "ALA", "Minnesota": "MINN", "Auburn": "AUB",
           "Tennessee": "TENN", "Mississippi State": "MSST", "Arkansas": "ARK",
           "Indiana": "IND", "Washington": "WASH"}
DIR = {k: {"abbr": v, "conference": "Planted", "logo": None} for k, v in SCHOOLS.items()}
CFB_SCHED = [
    cg("memphis-usf", "Memphis", "South Florida", "2026-11-13T01:00:00.000Z"),
    cg("duke-miami", "Duke", "Miami", "2026-11-14T17:00:00.000Z"),
    cg("ohio-miamioh", "Ohio", "Miami (OH)", "2026-11-14T17:00:00.000Z"),
    cg("usc-ucla", "USC", "UCLA", "2026-11-14T20:30:00.000Z"),
    cg("sc-clemson", "South Carolina", "Clemson", "2026-11-14T20:30:00.000Z"),
    # CFBD files a kickoff time not yet set at midnight Eastern (05:00Z in November)
    cg("ttu-baylor-tbd", "Texas Tech", "Baylor", "2026-11-21T05:00:00.000Z"),
    # a neutral site: CFBD calls Army the home side, the board calls Navy the home side
    cg("navy-army-neutral", "Navy", "Army", "2026-12-12T20:00:00.000Z", neutral=True),
    # 11:59pm Eastern on the schedule, moved to 12:30am Eastern (the next date) on the board
    cg("fresno-hawaii-midnight", "Fresno State", "Hawai'i", "2026-11-15T04:59:00.000Z"),
    # the same two teams 6 days 16 hours later, the closest a football rematch comes: a
    # Saturday-night finale, then the conference title game the next Saturday at noon. The
    # board holds only the first meeting, and the finished card must never read it.
    cg("usf-memphis-rematch", "South Florida", "Memphis", "2026-11-19T17:00:00.000Z"),
    # the board holds TWO records for this pair
    cg("utah-tcu-two-records", "Utah", "TCU", "2026-11-14T21:00:00.000Z"),
    # neither school is in the directory (FCS); the board's same-day game is unresolved too
    cg("idahost-nau-unresolved", "Idaho State", "Northern Arizona", "2026-11-14T21:00:00.000Z",
       ("fcs", "fcs")),
    # the stored schedule pairs two teams the board has in two DIFFERENT games that day (a
    # matchup re-booked, or a stale schedule file): Duke is in b2, UCLA in b4
    cg("duke-ucla-matchup-moved", "Duke", "UCLA", "2026-11-14T20:30:00.000Z"),
    # both sides one directory entry: the prefix walk reads Ohio Dominican (Division II, a
    # real schedule name) as Ohio, so the card would show Ohio's odds under both teams
    cg("ohiodom-ohio-one-entry", "Ohio Dominican", "Ohio", "2026-11-14T17:00:00.000Z", ("ii", "fbs")),
    # the Odds API still names Houston Christian "Houston Baptist Huskies" (b12 below). Read
    # as Houston, Houston was in two board games that day and its OWN card drew no odds
    cg("orst-houston", "Oregon State", "Houston", "2026-11-14T16:00:00.000Z"),
    # ...and Houston Christian (FCS) @ Rice is an FBS-vs-FCS game, joined on Rice (below)
    cg("hc-rice", "Houston Christian", "Rice", "2026-11-14T23:00:00.000Z", ("fcs", "fbs")),
    # CFBD's midnight placeholder beside a NIGHT kickoff: 10:30pm Eastern on the board is
    # 03:30Z the NEXT UTC date and 22.5 hours away. Only the Eastern date joins them.
    cg("ind-wash-tbd-night", "Indiana", "Washington", "2026-11-21T05:00:00.000Z"),
    # ── `[2026-11-13, review round 2]` AN FBS TEAM AGAINST AN FCS SCHOOL ──
    # teams.json is CFBD's FBS directory, so the FCS side never resolves. The FBS side's
    # one board game that day, whose other side is outside the directory too, is its game.
    cg("chatt-alabama-fcs", "Chattanooga", "Alabama", "2026-11-21T19:00:00.000Z", ("fcs", "fbs")),
    # an FBS team at an FCS school's ground: the board's HOME side is the unresolved one
    cg("minnesota-at-uni-fcs", "Minnesota", "Northern Iowa", "2026-11-21T20:00:00.000Z",
       ("fbs", "fcs")),
    # ⛔ Division II, the same day: "Minnesota Duluth" reads as Minnesota, and Minnesota's one
    # board game is against an unresolved school. Only the schedule's own class refuses it.
    cg("augustana-umd-d2", "Augustana (SD)", "Minnesota Duluth", "2026-11-21T19:00:00.000Z",
       ("ii", "ii")),
    # ⛔ the board lists the FBS team in TWO games that day (b16, b17): neither is taken
    cg("samford-auburn-two-games", "Samford", "Auburn", "2026-11-21T17:00:00.000Z", ("fcs", "fbs")),
    # ⛔ the FBS team's one board game is against another FBS team (b18: a re-booked schedule):
    # never the FCS opponent's odds
    cg("ttech-msst-fbs-opponent", "Tennessee Tech", "Mississippi State", "2026-11-21T18:00:00.000Z",
       ("fcs", "fbs")),
    # ⛔ two FBS schools a stale directory is missing (both unresolved), beside the day's one
    # board game whose two schools it is missing too (b19): never that game's odds
    cg("mostate-delaware-gap", "Missouri State", "Delaware", "2026-11-28T19:00:00.000Z"),
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
    bg("b11", "Oregon State Beavers", "Houston Cougars", "2026-11-14T16:00:00Z", (155, -185), (38.2, 61.8)),
    bg("b12", "Houston Baptist Huskies", "Rice Owls", "2026-11-14T23:00:00Z", (1400, -5000), (4.0, 96.0)),
    bg("b13", "Indiana Hoosiers", "Washington Huskies", "2026-11-22T03:30:00Z", (-240, 198), (68.0, 32.0)),
    bg("b14", "Chattanooga Mocs", "Alabama Crimson Tide", "2026-11-21T19:00:00Z", (2200, -8000), (3.1, 96.9)),
    bg("b15", "Minnesota Golden Gophers", "Northern Iowa Panthers", "2026-11-21T20:00:00Z", (-900, 600), (88.5, 11.5)),
    bg("b16", "Samford Bulldogs", "Auburn Tigers", "2026-11-21T17:00:00Z", (2000, -6000), (3.4, 96.6)),
    bg("b17", "Mercer Bears", "Auburn Tigers", "2026-11-21T21:00:00Z", (1600, -4000), (4.6, 95.4)),
    bg("b18", "Arkansas Razorbacks", "Mississippi State Bulldogs", "2026-11-21T18:00:00Z", (135, -160), (41.5, 58.5)),
    bg("b19", "Jacksonville State Gamecocks", "Kennesaw State Owls", "2026-11-28T19:00:00Z", (-145, 122), (57.0, 43.0)),
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
    # Houston's own numbers, with "Houston Baptist Huskies" on the board the same day
    "orst-houston": (155, -185, 38.2, 61.8),
    "ind-wash-tbd-night": (-240, 198, 68.0, 32.0),
    # FBS against FCS: the FCS school's own numbers are the board's side outside the directory
    "hc-rice": (1400, -5000, 4.0, 96.0),
    "chatt-alabama-fcs": (2200, -8000, 3.1, 96.9),
    "minnesota-at-uni-fcs": (-900, 600, 88.5, 11.5),
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
section("3. ⛔ NO TWO SPORTSBOOK NAMES ARE ONE TEAM (EVERY STORED NAME, RECORDED)")
# ══════════════════════════════════════════════════════════════════════
# THE CLASS behind Houston. The join refuses a team it finds in two board games that day, so
# a board name the resolver reads as ANOTHER school blanks that school's own card (and the
# Odds tab gives the other school its logo and conference). Section 1 plants the one case
# found; this asks it of every name the Odds API has sent: every away/home name in every
# stored gamelines snapshot, both leagues, with CFBD's FBS directory, RECORDED in research/
# on 2026-11-13 (a test asks the code, never production). No directory entry may be reached
# by two different names. ⚠️ And the resolver must still be asked something: at least 100
# college names resolve (138 when recorded; the Odds tab's coverage is test_conf_filter.py's),
# and every one of the 32 NFL names does.
REC = json.load(open(os.path.join(ROOT, "research", "fb_board_names_20261113.json"),
                     encoding="utf-8"))
for lg, teams, floor in (("ncaaf", REC["teams_ncaaf"], 100), ("nfl", "nfl", 32)):
    NR = run(lg, teams, [], {"games": []}, names=REC["names"][lg])
    ck(NR is not None, "⚠️ the page's resolver ran in node on the recorded %s names" % lg, "")
    if NR is None:
        continue
    NR = NR["names"]
    ck(not NR["collide"] and NR["resolved"] >= floor,
       "⛔ %s: no two of the %d recorded sportsbook names resolve to one team, and at least %d "
       "resolve" % (lg, NR["n"], floor),
       "%d resolve%s" % (NR["resolved"], ("; one team, two names: %r" % NR["collide"])
                         if NR["collide"] else ""))

# ══════════════════════════════════════════════════════════════════════
section("4. ⚪ TODAY'S LIVE FILES (MEASURED, NEVER ASSERTED)")
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
         "%s; one team, two board names: %s" % (lg, L["joined"], L["board"], L["cards"],
                                                scheds[-1], L["collide"] or "none"))
