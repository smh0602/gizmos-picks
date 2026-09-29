#!/usr/bin/env python3
"""
THE CFB CONFERENCE FILTER.

⛔ THIS TEST DOES NOT REIMPLEMENT THE FILTER. It lifts the page's OWN
functions out of index.html and runs them in node against the REAL data
files. A test that re-derives "which conference is Oregon in" would pass
happily while the page used a different rule -- and every filter defect
this project has met is a disagreement between two copies of a rule,
never a rule that was wrong in one place.

🔴 THE FAILURE THIS IS BUILT AROUND. The football page needed `fbResolve`
because a direct dictionary lookup of a board name hit 0 of 322. A
conference filter is a SECOND lookup on the same names, so if it silently
falls back to null the tab renders EMPTY and looks broken rather than
filtered. So the coverage check below is the point of the file, and it
asserts on COUNTS of real names, not on the presence of a string.

Ledger: rule 69/72 (assert on counts, never substrings, where a count is
available), rule 76 (reconstruct, don't count what the artifact says
about itself), rule 88 (a check enumerating what is PRESENT cannot see
what is ABSENT -- hence the "every view that filters also draws the bar"
check, which is written from the FILTER sites, not from the bar sites).

`[2026-09-28]` Section 3 plants its cases: a directory for the behaviour,
recorded real names for the coverage; the live files are the extras.
# @vacuity planted: either side of a game in the selection keeps it
#   file: index.html
#   find: return fbConfTeamPass(away) || fbConfTeamPass(home);
#   with: return fbConfTeamPass(away) && fbConfTeamPass(home);
#
# @vacuity planted: a lit chip keeps exactly its own conference's schools
#   file: index.html
#   find: return !!(c && fbConf.has(c));
#   with: return !!c;
#
# @vacuity recorded: a board name carrying its mascot still resolves
#   file: index.html
#   find: if (rest.length > 2) continue;
#   with: if (rest.length > 0) continue;
"""
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from tcheck import ck, note, shown   # the shared gate — see tcheck.py

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, "index.html")

FAIL = []
NOTE = []


SRC = open(HTML, encoding="utf-8").read()


def js_block(name):
    """Source of `function <name>(` through its matching close brace."""
    m = re.search(r"\n(?:async )?function " + re.escape(name) + r"\s*\(", SRC)
    assert m, "no function " + name
    i = SRC.index("{", m.end() - 1)
    depth, j = 0, i
    while j < len(SRC):
        if SRC[j] == "{":
            depth += 1
        elif SRC[j] == "}":
            depth -= 1
            if depth == 0:
                return SRC[m.start() + 1:j + 1]
        j += 1
    raise AssertionError("unbalanced " + name)


def js_const(pattern):
    m = re.search(pattern, SRC, re.S)
    assert m, pattern
    return m.group(0)


# ───────────────────────────────────────────────────────────────
print("\n═══ 1. THE FILTER IS ONE RULE, NOT TWO ═══")

conf_of = js_block("fbConfOf")
ck("fbConfOf resolves through fbResolve",
   "fbResolve(" in conf_of,
   "the same matcher the logos use")

team_pass = js_block("fbConfTeamPass")
game_pass = js_block("fbConfPass")

# ⛔ Exactly one place compares a conference to the selection. fbConfBar
#    reads fbConf.has to decide which chip is lit, which is presentation,
#    not selection -- so it is excluded by name and the count is over the
#    two predicates only.
ck("fbConfTeamPass is the only place a conference is compared",
   team_pass.count("fbConf.has(") == 1 and game_pass.count("fbConf.has(") == 0,
   "team=%d game=%d" % (team_pass.count("fbConf.has("), game_pass.count("fbConf.has(")))

ck("fbConfPass is defined as either side of fbConfTeamPass",
   game_pass.count("fbConfTeamPass(") == 2 and "||" in game_pass)

for nm, blk in (("fbConfTeamPass", team_pass), ("fbConfPass", game_pass)):
    ck("%s: empty selection means ALL" % nm,
       "!fbConf.size) return true" in blk)
    ck("%s: never filters the NFL" % nm,
       "LEAGUE !== 'ncaaf'" in blk)

bar = js_block("fbConfBar")
ck("fbConfBar draws nothing outside college",
   re.search(r"LEAGUE !== 'ncaaf'\) return ''", bar) is not None)
ck("the conference list is asked of the directory, not typed",
   "FBTEAMS[LEAGUE]" in js_block("fbConfList")
   and not re.search(r"'(SEC|Big Ten|ACC|Big 12)'", js_block("fbConfList")),
   "realignment moves schools every August")

# ───────────────────────────────────────────────────────────────
print("\n═══ 2. EVERY VIEW THAT FILTERS ALSO DRAWS A BAR ═══")
# 🔴 WRITTEN FROM THE FILTER SITES, NOT THE BAR SITES (rule 88). Counting
#    the bars can only tell you about bars that exist; the question is
#    whether a view filters WITHOUT one, which is a filter a reader cannot
#    turn off.
VIEWS = {
    "fbOdds":   "fbOdds",
    "fbScores": "fbScores",
    "fbProps":  "fbProps",
    "fbPicks":  "fbPicks",
}
for nm in VIEWS:
    b = js_block(nm)
    filters = ("fbConfPass(" in b) or ("fbConfTeamPass(" in b)
    draws = "fbConfBar()" in b
    ck("%s: filters (%s) and draws the bar (%s)" % (nm, filters, draws),
       filters and draws)

# Trends lives inside renderFootball, which also dispatches to the others.
rf = js_block("renderFootball")
ck("Trends filters on the team's own conference",
   "fbConfTeamPass(" in rf,
   "a Trends row is one team, not a game")
ck("Trends draws the bar", "fbConfBar()" in rf)

wire = js_block("fbWire")
ck("fbConfWire is called from fbWire, which every tab already calls",
   "fbConfWire(" in wire,
   "so a rendered bar cannot be an unwired no-op")
ck("no view wires the chips itself",
   sum(("fbConfWire(" in js_block(v)) for v in VIEWS) == 0,
   "one wiring site, like the rule it enforces")

# 🔴 THE RANK MUST NOT CHANGE MEANING WHEN A CHIP IS CLICKED.
ck("Trends ranks over every team and filters only the display",
   "rankedAll" in rf and "rankOf.get(" in rf and "rankedAll[0].v" in rf,
   "a filtered SEC row keeps its national rank and the league-wide bar")

# ⛔ The week picker is built before the conference filter is applied.
sc = js_block("fbScores")
i_weeks = sc.index("const weeks =")
i_conf = sc.index("fbConfPass(")
ck("Scores builds the week picker BEFORE filtering by conference",
   i_weeks < i_conf,
   "else a conference idle this week would move the reader to another one")

# ───────────────────────────────────────────────────────────────
print("\n═══ 3. IT RESOLVES THE NAMES THE FEEDS ACTUALLY SEND ═══")


def load(p):
    if p.endswith(".gz"):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.load(open(p, encoding="utf-8"))


# 🔴 THE DIRECTORY IS FBS-ONLY, SO "EVERY NAME RESOLVES" IS THE WRONG BAR
#    AND ASSERTING IT WOULD BE RED FOREVER. `[measured 2026-09-05]` 38 of
#    the 154 names on the live college board do not resolve -- Abilene
#    Christian, Alcorn State, Austin Peay, Bryant -- and every one of them
#    is an FCS school playing an FBS opponent in week 1. They have no
#    conference because teams.json has no FCS in it.
#
#    ⛔ SO THE BAR IS TWO CLAIMS, NOT ONE: every FBS name resolves, AND
#    every name that does not resolve is one the feed itself classifies as
#    not FBS. The second half is what stops "0 FBS misses" from being
#    vacuously true because the FBS set was built wrong.
#
#    ⚠️ The classification comes from the SCHEDULE's own `home_class` /
#    `away_class` -- the same field the Scores tab's division control
#    uses -- never from a typed list of schools.

def _norm(x):
    return re.sub(r"[^a-z0-9]", "", str(x or "").lower())


SCHED = load(os.path.join(ROOT, "data/ncaaf/latest/schedule-2026.json.gz"))
CLASS = {}
for _g in SCHED.get("games", []):
    for _t, _c in ((_g.get("home"), _g.get("home_class")),
                   (_g.get("away"), _g.get("away_class"))):
        if _t:
            CLASS[_t] = (_c or "").lower()
# longest first, so "Idaho State" is tried before "Idaho"
_SCH = sorted(CLASS, key=lambda s: -len(_norm(s)))


# 🔴 THE ALIASES ARE READ OUT OF THE PAGE, NOT RETYPED HERE. The first
#    draft of this classifier did retype nothing and filed "Appalachian
#    State Mountaineers" as NOT FBS -- because the odds feed says
#    "Appalachian State" and the schedule says "App State", so no prefix
#    of one is a prefix of the other. ⛔ That is the ENTIRE reason
#    FB_ALIASES exists in index.html, and a test that ignores it invents
#    a disagreement the product already solved. Sun Belt, and FBS.
_ALIASES = dict(re.findall(r"^\s*([a-z]+):\s*'([^']+)'",
                           js_const(r"const FB_ALIASES = \{.*?\n\};"), re.M))


def classify(name):
    """The feed's own classification for a name from ANY college file.

    ⚠️ Board names carry a mascot ("Alcorn State Braves"); schedule names
    do not ("Alcorn State"). Longest normalised prefix wins, which is the
    same shape as the page's resolver but is used here only to READ a
    label off the feed -- never to decide a conference."""
    n = _norm(name)
    for k, v in _ALIASES.items():
        if n.startswith(k) and v in CLASS:
            return CLASS[v]
    for s in _SCH:
        if n.startswith(_norm(s)):
            return CLASS[s]
    return "unknown"


def names_ncaaf():
    """Every team name a college tab asks the filter about, split by the
    feed's own division so each half can be judged on its own bar."""
    raw = {}
    b = os.path.join(ROOT, "data/ncaaf/latest/board.json")
    if os.path.exists(b):
        raw["board"] = {t for g in load(b).get("games", [])
                        for t in (g.get("away"), g.get("home")) if t}
    c = os.path.join(ROOT, "picks/fb-ncaaf-latest.json")
    if os.path.exists(c):
        raw["card"] = {t for p in load(c).get("picks", [])
                       for t in (p.get("away"), p.get("home")) if t}
    raw["schedule"] = {t for t, cl in CLASS.items() if cl == "fbs"}
    tr = os.path.join(ROOT, "data/ncaaf/latest/allowed-by-position-2026.json.gz")
    if os.path.exists(tr):
        d = load(tr)
        raw["trends"] = set((d.get("defences") or d.get("offences") or {}).keys())
    out = {}
    for k, v in raw.items():
        out[k + " · FBS"] = sorted(n for n in v if classify(n) == "fbs")
        other = sorted(n for n in v if classify(n) != "fbs")
        if other:
            out[k + " · not FBS"] = other
    return out


NAMES = names_ncaaf()
# ⛔ CFBD's FBS directory, by construction: `teams.json` holds FBS schools
#    only, so a board name that RESOLVES INTO IT is a school CFBD calls
#    FBS today — whatever an older schedule row still says.
# ⚠️ `.teams`, exactly as fbTeamsLoad reads it. The file's top level is a
#    wrapper (season, built_at, n, source); the directory is one key down.
TEAMS = load(os.path.join(ROOT, "data/ncaaf/latest/teams.json"))["teams"]

# Build a node program out of the PAGE'S OWN SOURCE.
# ⚠️ `[2026-09-28]` A FUNCTION OF (directory, names), run three times: the
#    PLANTED directory (behaviour), the RECORDED names and directory
#    (coverage), and today's LIVE files (the extras they always were).
def _harness(teams, names):
  return "\n".join([
    "const FBTEAMS = { ncaaf: %s, nfl: {} };" % json.dumps(teams),
    "let LEAGUE = 'ncaaf';",
    js_const(r"const FB_TNORM = \{\}.*?const FB_TCACHE = \{\};"),
    js_block("fbNorm"),
    js_const(r"const FB_CONTINUES = new Set\(\[.*?\]\);"),
    js_const(r"const FB_ALIASES = \{.*?\n\};"),
    js_block("fbResolve"),
    "let fbConf = new Set();",
    conf_of, team_pass, game_pass,
    js_block("fbConfList"),
    "const NAMES = %s;" % json.dumps(names),
    r"""
const out = { coverage: {}, confs: fbConfList() };
for (const src in NAMES){
  const miss = NAMES[src].filter(n => fbConfOf(n) === null);
  /* ⚠️ THE NAMES, NOT JUST THE COUNT. "1 resolved (want 0)" cannot tell
     you whether a school was promoted or the matcher went wrong, and
     those need opposite responses. */
  out.coverage[src] = { n: NAMES[src].length, miss: miss.length,
                        examples: miss.slice(0, 8),
                        resolvedNames: NAMES[src].filter(n => fbConfOf(n) !== null) };
}
/* behaviour, exercised rather than read */
out.emptyMeansAll = fbConfPass('Oregon Ducks','Boise State Broncos')
                 && fbConfTeamPass('Oregon');
const sec = fbConfList().indexOf('SEC') > -1 ? 'SEC' : fbConfList()[0];
fbConf = new Set([sec]);
out.sec = sec;
out.secTeams = Object.keys(FBTEAMS.ncaaf).filter(t => fbConfTeamPass(t)).length;
out.secTotal = Object.keys(FBTEAMS.ncaaf).filter(
  t => (FBTEAMS.ncaaf[t]||{}).conference === sec).length;
/* either side is enough */
const inSec  = Object.keys(FBTEAMS.ncaaf).find(t => (FBTEAMS.ncaaf[t]||{}).conference === sec);
const outSec = Object.keys(FBTEAMS.ncaaf).find(t => (FBTEAMS.ncaaf[t]||{}).conference &&
                                                    FBTEAMS.ncaaf[t].conference !== sec);
out.eitherSide = [ fbConfPass(inSec, outSec), fbConfPass(outSec, inSec),
                   fbConfPass(outSec, outSec) ];
/* an unknown name must not sneak past a live selection */
out.unknownDropped = fbConfPass('Some FCS School', 'Another FCS School') === false;
/* the NFL is never filtered, even with chips lit */
LEAGUE = 'nfl';
out.nflUnfiltered = fbConfPass('Detroit Lions','Chicago Bears') && fbConfTeamPass('Detroit Lions');
LEAGUE = 'ncaaf';
console.log(JSON.stringify(out));
""",
  ])


def _run(teams, names, what):
    tmp = tempfile.mkdtemp()
    jsp = os.path.join(tmp, "h.js")
    open(jsp, "w", encoding="utf-8").write(_harness(teams, names))
    r = subprocess.run(["node", jsp], capture_output=True, text=True)
    shutil.rmtree(tmp, ignore_errors=True)
    if r.returncode != 0:
        print(shown(r.stderr[-2000:]))
        ck("the page's own resolver runs (%s)" % what, False)
        return None
    out = json.loads(r.stdout.strip().splitlines()[-1])
    ck("the page's own resolver runs (%s)" % what, True,
       "%d conferences in the directory" % len(out["confs"]))
    return out


def _behaviour(R, what):
    ck("empty selection shows everything (%s)" % what, R["emptyMeansAll"] is True)
    ck("selecting %s keeps exactly its %d schools (%s)"
       % (R["sec"], R["secTotal"], what),
       R["secTeams"] == R["secTotal"] and R["secTotal"] > 0,
       "kept %d" % R["secTeams"])
    ck("either side of a game is enough to keep it (%s)" % what,
       R["eitherSide"] == [True, True, False],
       str(R["eitherSide"]))
    ck("a game with neither side in the selection is dropped (%s)" % what,
       R["unknownDropped"] is True)
    ck("the NFL is never filtered, even with chips lit (%s)" % what,
       R["nflUnfiltered"] is True)


# ═══════════════════════════════════════════════════════════════
# 🔴 `[2026-09-28]` THE CASES ARE PLANTED FIRST.
# ═══════════════════════════════════════════════════════════════
# ⛔ The behaviour checks took their schools from the LIVE teams.json and
#    the coverage checks their names from the LIVE board and card, so each
#    had its case only because production held it (a directory refresh
#    with one conference, or a board with no FBS names, left them asking
#    nothing or red on correct page code).
# ✅ BEHAVIOUR: a planted directory with two conferences, every run.
# ✅ COVERAGE: 423 real names as the feeds spelled them on 2026-09-28 —
#    board, card, schedule and trends, every one classed FBS — and CFBD's
#    directory as it stood, RECORDED in research/, so "every FBS name
#    resolves" is asked of real spellings every run. The live files below
#    are asked the same questions as the extras they always were.
print("\n   — planted directory (behaviour) —")
PLANTED = {"Alpha State": {"conference": "SEC"},
           "Beta Tech": {"conference": "SEC"},
           "Gamma University": {"conference": "Big Ten"},
           "Delta College": {"conference": "Big Ten"},
           "Epsilon A&M": {"conference": "Sun Belt"}}
_RP = _run(PLANTED, {}, "planted directory")
if _RP:
    _behaviour(_RP, "planted directory")

print("\n   — recorded names and directory (coverage) —")
_REC = json.load(open(os.path.join(ROOT, "research",
                                   "conf_filter_names_20260928.json"),
                      encoding="utf-8"))
_RR = _run(_REC["teams"], _REC["names"], "recorded 2026-09-28")
if _RR:
    _cov = _RR["coverage"]
    _n = sum(c["n"] for c in _cov.values())
    _miss = {s: c["examples"] for s, c in _cov.items() if c["miss"]}
    ck("🔴 every recorded FBS name resolves to a conference (%d names, %d "
       "sources)" % (_n, len(_cov)),
       _n >= 400 and len(_cov) == 4 and not _miss,
       "⛔ an unresolved FBS name is a school that vanishes from the tab "
       "the moment any chip is lit. unresolved: %s" % _miss)

print("\n   — today's live files (the extras) —")
R = _run(TEAMS, NAMES, "live files")

if R:
    for src, c in sorted(R["coverage"].items()):
        if src.endswith("· FBS"):
            # ⛔ A name that does not resolve is a row the filter can only
            #    DROP, so an unresolved FBS name is a school that vanishes
            #    from the tab the moment any chip is lit.
            # 🔴 "NO NAME FAILS TO RESOLVE" IS THE RULE. "AT LEAST ONE
            #    NAME EXISTS" IS A DEMAND THAT DATA EXIST, AND IT WENT RED
            #    ON A CORRECT CARD. `[2026-09-10]` the college card held
            #    **zero priced rows** — a Thursday with nothing posted —
            #    so `card · FBS` contributed 0 names and `c["n"] > 0`
            #    failed while every name it did carry (none) resolved
            #    perfectly. ⛔ The emptiness is REPORTED below so it can
            #    never pass silently; the resolution rule is unchanged.
            ck("%s: every name resolves to a conference" % src,
               c["miss"] == 0,
               "%d names, %d unresolved%s" % (c["n"], c["miss"],
                  (" — " + ", ".join(c["examples"])) if c["examples"] else ""))
            if not c["n"]:
                note("⚠️ NOT EXERCISED: `%s` contributed 0 names, so the "
                     "resolver was never asked anything. Not a pass — an "
                     "empty card is a legitimate state, an empty SCHEDULE "
                     "would not be." % src)
        else:
            # ⚠️ REPORTED, NOT ASSERTED, AND THE DISTINCTION MATTERS. That
            #    an FCS school has no conference is a property of the
            #    directory, not a defect; what would be a defect is an FCS
            #    name QUIETLY RESOLVING to some FBS school's conference,
            #    which is the direction this line watches.
            # 🔴 ONE OF THEM DID RESOLVE, ON 2026-09-06, AND IT IS NOT A
            #    FILTER BUG — IT IS TWO SOURCES DISAGREEING ABOUT A
            #    SCHOOL'S DIVISION.
            # ⛔ `teams.json` is CFBD's CURRENT FBS directory, so a name
            #    being in it means CFBD calls that school FBS today. The
            #    stored schedule's `home_class` is from the same feed but
            #    a different endpoint, and it still says FCS for schools
            #    that were PROMOTED — Delaware, Sam Houston and
            #    Jacksonville State all moved up recently.
            # ✅ SO THE TWO CASES ARE SEPARATED RATHER THAN MERGED. A name
            #    the directory knows is a RECLASSIFICATION: reported, with
            #    the school named, because the filter is right to use the
            #    newer source. A name the directory does NOT know that
            #    still lands on a conference would be a real
            #    mis-resolution, and that still fails.
            # ⚠️ Merging them would have meant either a red run every week
            #    of the season, or no check at all. Neither is the answer.
            # ⚠️ Resolving AT ALL means the page's matcher found it in
            #    `teams.json`, which is FBS-only — so every resolved name
            #    is one CFBD currently classes as FBS. A "mis-resolution"
            #    would be a name that resolves to a conference the school
            #    does not belong to, and the FBS block above is what
            #    watches that direction.
            _res = list(c.get("resolvedNames", []))
            _known, _wrong = _res, []
            ck("%s: no name resolves by MISTAKE" % src, not _wrong,
               ("mis-resolved: " + ", ".join(_wrong)) if _wrong
               else "%d of %d resolved, and every one is in CFBD's own FBS "
                    "directory" % (len(_known), c["n"]))
            if _known:
                note("⚠️ %d school(s) the stored schedule still calls FCS but "
                     "CFBD's FBS directory lists: %s — a PROMOTION the "
                     "schedule feed has not caught up with. The filter uses "
                     "the directory, which is the newer source."
                     % (len(_known), ", ".join(_known)))
            note("%s: %d schools, no conference — with a chip lit their "
                 "game survives only if the FBS side is selected" % (src, c["n"]))

    # ⚠️ THE LIVE DIRECTORY'S BEHAVIOUR IS THE EXTRA: asked when it holds
    #    two conferences or more (the case "either side" needs), reported
    #    otherwise. The planted directory above asks it every run.
    if len(R["confs"]) >= 2:
        _behaviour(R, "live directory")
    else:
        note("⚠️ the live directory holds %d conference(s), so the live "
             "behaviour checks were not asked; the planted directory above "
             "was" % len(R["confs"]))
    note("conferences offered: " + ", ".join(R["confs"]))

# ───────────────────────────────────────────────────────────────
# 🔴 THE FAILURE GATE IS THE LAST THING IN THIS FILE AND NOTHING MAY BE
#    APPENDED BELOW IT. Rule 97: a section written after the gate reports
#    red and the file still exits 0, which is a test that cannot fail.
