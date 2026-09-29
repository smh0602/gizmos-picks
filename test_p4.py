#!/usr/bin/env python3
"""The Power 4 gate — does it name the RIGHT team?

🔴 SAM'S RULE, 2026-09-01: "just make sure your talking about the right
team, just like the max muncy situation for the batters." MLB has two Max
Muncys; a name-only join credits one with the other's line.
⛔ COLLEGE IS WORSE: the collisions are PREFIXES. "Washington State
Cougars" starts with "Washington". "Miami RedHawks" starts with "Miami".
A naive prefix match pulls Group of 5 games onto the Power 4 board and
pays per game for them.

⚠️ THE FEED'S ACTUAL SPELLING IS STILL UNSEEN. So every plausible spelling
is tested here, and the gate still fails closed if too few match.

🔴 `[2026-09-28]` ~~every check read the LIVE `players-*.json.gz`~~ (pattern
P3). In week 1 of a new season the newest log holds 40-66 Power 4 teams:
the 60..72 count went red, a named team that had not played yet turned
its mapping red, and the Max Muncy guards ("Miami RedHawks" -> None) went
quiet whenever the shorter school was missing — while the first
`filter_power4` call, run in the REPO tree, could write a fail-closed
`event-names.txt` into `data/`. ✅ Every question is now asked of a PLANTED
tree whose Power 4 set is DECLARED below (the 2026 conference map as
measured on 2026-09-28), next to a newer part-played season the reader
must skip. The live set is reported, and re-asked when it is complete.

# @vacuity ⛔ a longer school must not match a shorter one (GUARD A), on the planted set
#   file: collect.py
#   find:         if len(rest) > 2:
#   with:         if False:
#
# @vacuity ⛔ MAC Miami is never ACC Miami, on the planted set
#   file: collect.py
#   find: _AMBIGUOUS = {"miami": "hurricanes"}
#   with: _AMBIGUOUS = {}
#
# @vacuity 🔴 a newer, part-played season is skipped, not read as the Power 4 set
#   file: collect.py
#   find:     P4_MIN_TEAMS = 40
#   with:     P4_MIN_TEAMS = 0
"""
import gzip, json, os, shutil, sys, tempfile
from tcheck import ck, note   # the shared gate — see tcheck.py
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "ncaaf")
import collect

FAIL = []
# ⛔ DECLARED, NOT DERIVED (see the Max Muncy note below): the 2026 Power 4
#    map as CFBD spells it, measured on the live log 2026-09-28. A
#    realignment changes the LIVE set, reported at the end — never this.
P4_DECLARED = {
    "ACC": ("Boston College", "California", "Clemson", "Duke", "Florida State",
            "Georgia Tech", "Louisville", "Miami", "NC State", "North Carolina",
            "Pittsburgh", "SMU", "Stanford", "Syracuse", "Virginia",
            "Virginia Tech", "Wake Forest"),
    "Big 12": ("Arizona", "Arizona State", "BYU", "Baylor", "Cincinnati",
               "Colorado", "Houston", "Iowa State", "Kansas", "Kansas State",
               "Oklahoma State", "TCU", "Texas Tech", "UCF", "Utah",
               "West Virginia"),
    "Big Ten": ("Illinois", "Indiana", "Iowa", "Maryland", "Michigan",
                "Michigan State", "Minnesota", "Nebraska", "Northwestern",
                "Ohio State", "Oregon", "Penn State", "Purdue", "Rutgers",
                "UCLA", "USC", "Washington", "Wisconsin"),
    "SEC": ("Alabama", "Arkansas", "Auburn", "Florida", "Georgia", "Kentucky",
            "LSU", "Mississippi State", "Missouri", "Oklahoma", "Ole Miss",
            "South Carolina", "Tennessee", "Texas", "Texas A&M", "Vanderbilt"),
}
P4_SET = {t for ts in P4_DECLARED.values() for t in ts}
PLANT = tempfile.mkdtemp(prefix="p4-")


def _plant_players(season, team_conf):
    d = os.path.join(PLANT, "data", "ncaaf", "latest")
    os.makedirs(d, exist_ok=True)
    with gzip.open(os.path.join(d, "players-%d.json.gz" % season), "wt",
                   encoding="utf-8") as fh:
        json.dump({"season": season, "players": {
            "p%d" % i: {"name": "Planted %d" % i,
                        "g": [{"team": t, "conf": c, "d": "%d-09-06" % season}]}
            for i, (t, c) in enumerate(sorted(team_conf.items()))}}, fh)


_plant_players(2026, {t: c for c, ts in P4_DECLARED.items() for t in ts})
# ⚠️ A NEWER SEASON WITH SEVEN TEAMS — the 2026-09-02 shape (Week 0 only).
_plant_players(2099, {t: "SEC" for t in P4_DECLARED["SEC"][:7]})


def in_tree(root, fn, *a):
    """`power4_teams`/`filter_power4` read and write RELATIVE paths."""
    _here = os.getcwd()
    try:
        os.chdir(root)
        return fn(*a)
    finally:
        os.chdir(_here)


p4 = in_tree(PLANT, collect.power4_teams)
NORM = {collect._norm_team(t): t for t in p4}
m = lambda s: collect._match_team(s, NORM)
ev = lambda a, h: {"away_team": a, "home_team": h}
quiet = lambda *a, **k: None

ck(f"the Power 4 list is read from our own data ({len(p4)} teams)",
   p4 == P4_SET,
   "⛔ exactly the planted 2026 map — not the newer seven-team season beside "
   "it. missing %s, extra %s" % (sorted(P4_SET - p4), sorted(p4 - P4_SET)))
# ⛔ RULE 67: each Max Muncy case below guards against a SHORTER school
#    stealing a longer name. It only asks anything if that school is in the
#    set, so the set is asserted to hold every one of them.
_STEMS = {"Washington", "Miami", "Arkansas", "North Carolina", "Georgia",
          "Florida", "Ohio State", "Michigan", "Texas", "Kansas", "Iowa",
          "Oklahoma", "Mississippi State"}
ck("⚠️ every shorter school a guard below protects against is in the set",
   _STEMS <= p4, "missing: %s" % sorted(_STEMS - p4))

print("\n-- exact names, whatever the feed calls them --")
for nm in ("Ohio State", "Alabama", "Texas A&M", "Ole Miss", "USC",
           "Miami", "NC State", "Pittsburgh"):
    got = m(nm)
    ck(f"{nm!r} -> {got!r}", got is not None or nm not in p4,
       "" if got else "not in our list either, which is a data question")

print("\n-- mascot suffixes must MATCH (this is what makes it work) --")
for nm, want in (("Ohio State Buckeyes", "Ohio State"),
                 ("Alabama Crimson Tide", "Alabama"),
                 ("Georgia Bulldogs", "Georgia"),
                 ("Texas Longhorns", "Texas"),
                 ("Penn State Nittany Lions", "Penn State"),
                 ("Miami Hurricanes", "Miami"),
                 ("Wake Forest Demon Deacons", "Wake Forest")):
    ck(f"{nm!r} -> {want!r}", m(nm) == want, f"got {m(nm)!r}")

print("\n-- 🔴 THE MAX MUNCY CASES: a longer school must NOT match a shorter one --")
# ⛔ EXPECTATIONS ARE DECLARED, NOT DERIVED. A first draft computed them
# from the team list and got "Miami RedHawks" wrong -- it saw "Miami" in
# the Power 4 set and demanded a match for a MAC school. A test that
# infers its own answer can inherit the very bug it is checking for.
CASES = [
    ("Washington State Cougars",  None),            # Wazzu is not Big Ten
    ("Michigan State Spartans",   "Michigan State"),
    ("Miami RedHawks",            None),            # MAC Miami (OH)
    ("Miami Hurricanes",          "Miami"),         # ACC Miami (FL)
    ("Oklahoma State Cowboys",    "Oklahoma State"),
    ("Kansas State Wildcats",     "Kansas State"),
    ("Mississippi State Bulldogs", "Mississippi State"),
    ("Florida State Seminoles",   "Florida State"),
    ("San Jose State Spartans",   None),
    ("Boise State Broncos",       None),
    ("Iowa State Cyclones",       "Iowa State"),
    ("Ohio Bobcats",              None),            # MAC Ohio, not Ohio St
]
for nm, want in CASES:
    got = m(nm)
    ck(f"{nm!r} -> {want!r}", got == want, f"got {got!r}")

print("\n-- 🔴 CASES TAKEN FROM THE REAL 103-GAME BOARD, 2026-09-01 --")
# ⛔ These are not invented. They are the actual strings the Odds API
# returned, pulled for 6 credits precisely so this test could stop
# guessing. Two of them were LIVE FALSE POSITIVES before the guards:
#   'Arkansas Pine Bluff Golden Lions' matched our 'Arkansas'
#   'North Carolina A&T Aggies'        would have matched 'North Carolina'
REAL = [
    ("Arkansas Pine Bluff Golden Lions", None),          # FCS SWAC
    ("North Carolina A&T Aggies",        None),          # FCS CAA
    ("Miami (OH) RedHawks",              None),          # MAC
    ("Arkansas State Red Wolves",        None),          # Sun Belt
    ("Georgia Southern Eagles",          None),
    ("Florida International Panthers",   None),
    ("Ohio Bobcats",                     None),
    ("Arkansas Razorbacks",     "Arkansas"),
    ("Georgia Tech Yellow Jackets", "Georgia Tech"),
    ("Texas Tech Red Raiders",   "Texas Tech"),
    ("Arizona State Sun Devils", "Arizona State"),
    ("California Golden Bears",  "California"),
    ("Illinois Fighting Illini", "Illinois"),
    ("Ole Miss Rebels",          "Ole Miss"),
    ("USC Trojans",              "USC"),
    ("Stanford Cardinal",        "Stanford"),
    ("Ohio State Buckeyes",      "Ohio State"),
    ("Texas A&M Aggies",         "Texas A&M"),
]
for nm, want in REAL:
    got = m(nm)
    ck(f"{nm!r} -> {want!r}", got == want, f"got {got!r}")

print("\n-- the gate end to end --")
board = [ev("Alabama Crimson Tide", "Georgia Bulldogs"),
         ev("Ohio State Buckeyes", "Michigan Wolverines"),
         ev("Texas Longhorns", "Oklahoma Sooners"),
         ev("Clemson Tigers", "Florida State Seminoles"),
         ev("USC Trojans", "UCLA Bruins"),
         ev("Penn State Nittany Lions", "Wisconsin Badgers"),
         ev("Auburn Tigers", "Missouri Tigers"),
         ev("Iowa Hawkeyes", "Nebraska Cornhuskers"),
         ev("Duke Blue Devils", "Virginia Cavaliers"),
         ev("LSU Tigers", "Florida Gators"),
         ev("Boise State Broncos", "Oregon Ducks"),
         ev("Miami RedHawks", "Ohio Bobcats"),
         ev("Washington State Cougars", "San Diego State Aztecs")]
kept, why = in_tree(PLANT, collect.filter_power4, board, quiet)
ck("a mascot-suffixed board now MATCHES instead of refusing", why is None, str(why))
ck("the 10 Power-4-vs-Power-4 games are kept", len(kept) == 10, f"{len(kept)}")
names = {(e["away_team"], e["home_team"]) for e in kept}
ck("⛔ Boise State @ Oregon is dropped (G5 visitor)",
   ("Boise State Broncos", "Oregon Ducks") not in names)
ck("⛔ Miami RedHawks is NOT mistaken for ACC Miami",
   ("Miami RedHawks", "Ohio Bobcats") not in names)
ck("⛔ Washington State is NOT mistaken for Washington",
   ("Washington State Cougars", "San Diego State Aztecs") not in names)

print("\n-- and it still fails closed on names it cannot resolve --")
junk = [ev(f"Team {i} FC", f"Club {i}") for i in range(10)]
# ⚠️ IN A THROWAWAY DIRECTORY. `[fixed 2026-09-06]` The fail-closed
# branch WRITES `data/ncaaf/latest/event-names.txt` — a real diagnostic,
# and the right thing for the collector to do — but the tests run in the
# same CI job that then does `git add data/`, so this test was committing
# a file built from ten fake teams called "Team 3 FC".
# ⛔ `filter_power4` writes to a RELATIVE path, so moving the cwd is
# enough; nothing about the code under test changes.
# ⚠️ THE DATA COMES WITH IT: the planted tree holds a 67-team season, so
# this reaches "the name join is unproven" — not "no Power 4 team list",
# which a bare directory would, passing for the wrong reason. ⛔ A sandbox
# that changes which branch runs is not a sandbox, it is a different test.
# ✅ And since `[2026-09-28]` the mascot board above runs in the same
# planted tree, so NO call in this file can write into the repo.
k2, w2 = in_tree(PLANT, collect.filter_power4, junk, quiet)
ck("unrecognisable names spend NOTHING — on the name-join branch",
   k2 == [] and w2 is not None and "name join is unproven" in str(w2),
   str(w2))
# ✅ AND THE DIAGNOSTIC IS STILL WRITTEN. Moving the write out of the
#    repo must not quietly delete the thing that makes a name-join
#    failure legible — so this asserts it landed in the sandbox.
_diag = os.path.join(PLANT, "data", "ncaaf", "latest", "event-names.txt")
ck("...and the two name lists are still written for comparison",
   os.path.exists(_diag)
   and "Team 0 FC" in open(_diag, encoding="utf-8").read(),
   "in the throwaway tree, where a fake board belongs")
shutil.rmtree(PLANT, ignore_errors=True)

print("\n-- the LIVE Power 4 set: reported, and re-asked when it is complete --")
live = in_tree(ROOT, collect.power4_teams)
note("live Power 4 set: %d teams (planted: %d); %s"
     % (len(live), len(P4_SET),
        "same teams" if live == P4_SET else
        "missing %s, extra %s" % (sorted(P4_SET - live)[:8], sorted(live - P4_SET)[:8])))
_named = ({w for _, w in CASES + REAL if w}
          | {"Ohio State", "Alabama", "Georgia", "Texas", "Penn State", "Miami",
             "Wake Forest"} | _STEMS)
if _named <= live:
    _LN = {collect._norm_team(t): t for t in live}
    _off = [(nm, want, collect._match_team(nm, _LN)) for nm, want in CASES + REAL
            if collect._match_team(nm, _LN) != want]
    ck("✅ every declared mapping also holds against the LIVE set", not _off,
       "got %s" % _off)
else:
    note("⚠️ NOT EXERCISED ON THE LIVE SET: it lacks %s — a part-played "
         "season. Every mapping above ran on the planted set."
         % sorted(_named - live))

