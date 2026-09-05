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
HTML = os.path.join(ROOT, "index.html")

FAIL = []
NOTE = []


def ck(name, cond, extra=""):
    print(("  ✅ " if cond else "  ❌ ") + name + (("  — " + extra) if extra else ""))
    if not cond:
        FAIL.append(name)
    return cond


def note(s):
    print("  ⚪ " + s)
    NOTE.append(s)


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
# ⚠️ `.teams`, exactly as fbTeamsLoad reads it. The file's top level is a
#    wrapper (season, built_at, n, source); the directory is one key down.
TEAMS = load(os.path.join(ROOT, "data/ncaaf/latest/teams.json"))["teams"]

# Build a node program out of the PAGE'S OWN SOURCE.
harness = "\n".join([
    "const FBTEAMS = { ncaaf: %s, nfl: {} };" % json.dumps(TEAMS),
    "let LEAGUE = 'ncaaf';",
    js_const(r"const FB_TNORM = \{\}.*?const FB_TCACHE = \{\};"),
    js_block("fbNorm"),
    js_const(r"const FB_CONTINUES = new Set\(\[.*?\]\);"),
    js_const(r"const FB_ALIASES = \{.*?\n\};"),
    js_block("fbResolve"),
    "let fbConf = new Set();",
    conf_of, team_pass, game_pass,
    js_block("fbConfList"),
    "const NAMES = %s;" % json.dumps(NAMES),
    r"""
const out = { coverage: {}, confs: fbConfList() };
for (const src in NAMES){
  const miss = NAMES[src].filter(n => fbConfOf(n) === null);
  out.coverage[src] = { n: NAMES[src].length, miss: miss.length, examples: miss.slice(0,8) };
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

tmp = tempfile.mkdtemp()
jsp = os.path.join(tmp, "h.js")
open(jsp, "w", encoding="utf-8").write(harness)
r = subprocess.run(["node", jsp], capture_output=True, text=True)
shutil.rmtree(tmp, ignore_errors=True)
if r.returncode != 0:
    print(r.stderr[-2000:])
    ck("the page's own resolver runs", False)
    R = None
else:
    R = json.loads(r.stdout.strip().splitlines()[-1])
    ck("the page's own resolver runs", True,
       "%d conferences in the directory" % len(R["confs"]))

if R:
    for src, c in sorted(R["coverage"].items()):
        if src.endswith("· FBS"):
            # ⛔ A name that does not resolve is a row the filter can only
            #    DROP, so an unresolved FBS name is a school that vanishes
            #    from the tab the moment any chip is lit.
            ck("%s: every name resolves to a conference" % src,
               c["miss"] == 0 and c["n"] > 0,
               "%d names, %d unresolved%s" % (c["n"], c["miss"],
                  (" — " + ", ".join(c["examples"])) if c["examples"] else ""))
        else:
            # ⚠️ REPORTED, NOT ASSERTED, AND THE DISTINCTION MATTERS. That
            #    an FCS school has no conference is a property of the
            #    directory, not a defect; what would be a defect is an FCS
            #    name QUIETLY RESOLVING to some FBS school's conference,
            #    which is the direction this line watches.
            ck("%s: none of them resolve to an FBS conference" % src,
               c["miss"] == c["n"],
               "%d names, %d resolved (want 0)" % (c["n"], c["n"] - c["miss"]))
            note("%s: %d schools, no conference — with a chip lit their "
                 "game survives only if the FBS side is selected" % (src, c["n"]))

    ck("empty selection shows everything", R["emptyMeansAll"] is True)
    ck("selecting %s keeps exactly its %d schools" % (R["sec"], R["secTotal"]),
       R["secTeams"] == R["secTotal"] and R["secTotal"] > 0,
       "kept %d" % R["secTeams"])
    ck("either side of a game is enough to keep it",
       R["eitherSide"] == [True, True, False],
       str(R["eitherSide"]))
    ck("a game with neither side in the selection is dropped",
       R["unknownDropped"] is True)
    ck("the NFL is never filtered, even with chips lit",
       R["nflUnfiltered"] is True)
    note("conferences offered: " + ", ".join(R["confs"]))

# ───────────────────────────────────────────────────────────────
# 🔴 THE FAILURE GATE IS THE LAST THING IN THIS FILE AND NOTHING MAY BE
#    APPENDED BELOW IT. Rule 97: a section written after the gate reports
#    red and the file still exits 0, which is a test that cannot fail.
print()
if FAIL:
    print("❌ %d FAILED" % len(FAIL))
    for f in FAIL:
        print("   - " + f)
    sys.exit(1)
print("✅ all conference-filter tests passed")
