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
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("LEAGUE", "ncaaf")
import collect

FAIL = []
def ck(n, ok, d=""):
    print(("  [OK  ] " if ok else "  [FAIL] ") + n + (f"  {d}" if d else ""))
    if not ok: FAIL.append(n)

p4 = collect.power4_teams()
NORM = {collect._norm_team(t): t for t in p4}
m = lambda s: collect._match_team(s, NORM)
ev = lambda a, h: {"away_team": a, "home_team": h}
quiet = lambda *a, **k: None

ck(f"the Power 4 list is read from our own data ({len(p4)} teams)",
   60 <= len(p4) <= 72, f"{len(p4)}")

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
kept, why = collect.filter_power4(board, quiet)
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
k2, w2 = collect.filter_power4(junk, quiet)
ck("unrecognisable names spend NOTHING", k2 == [] and w2 is not None)

print()
if FAIL:
    print(f"⛔ {len(FAIL)} FAILED: {FAIL}"); sys.exit(1)
print("✅ the gate names the right team, or refuses")
