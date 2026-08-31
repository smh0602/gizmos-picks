#!/usr/bin/env python3
"""The Power 4 gate: does it keep the right games, and does it FAIL CLOSED
when the team names do not join?

🔴 WHY. Props bill PER GAME. An unfiltered NCAAF Saturday is ~70 events =
700 credits for one pull, against ~390/day of headroom. The gate is the
only thing making CFB affordable, so it has to be right in BOTH
directions: keep Power 4 games, and — when the two name lists disagree —
spend NOTHING rather than guess.
⛔ THE NAME JOIN IS UNVERIFIED AGAINST THE REAL FEED. That is precisely
why the failure path is tested harder than the success path.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("LEAGUE", "ncaaf")
import collect

FAIL = []
def ck(n, ok, d=""):
    print(("  [OK  ] " if ok else "  [FAIL] ") + n + (f"  {d}" if d else ""))
    if not ok: FAIL.append(n)

def ev(away, home): return {"away_team": away, "home_team": home}
quiet = lambda *a, **k: None

p4 = collect.power4_teams()
ck(f"the Power 4 list is read from our own data ({len(p4)} teams)",
   60 <= len(p4) <= 72, f"{len(p4)} teams")
ck("it is the CURRENT set, not a hardcoded old one",
   "Oregon" in p4 and "Texas" in p4 and "Ohio State" in p4)
ck("a Group of 5 team is NOT in it", "Boise State" not in p4)

print("\n-- keeping the right games --")
board = [ev("Alabama", "Georgia"), ev("Ohio State", "Michigan"),
         ev("Texas", "Oklahoma"), ev("Boise State", "Oregon"),
         ev("Sam Houston", "UTEP"), ev("Kennesaw State", "Liberty"),
         ev("Clemson", "Florida State"), ev("USC", "UCLA"),
         ev("Penn State", "Wisconsin"), ev("Auburn", "Missouri"),
         ev("Iowa", "Nebraska"), ev("Duke", "Virginia")]
kept, why = collect.filter_power4(board, quiet)
ck("no refusal on a healthy board", why is None, str(why))
ck("only Power-4-vs-Power-4 survives (12 on the board, 3 involve a G5)",
   len(kept) == 9, f"{len(kept)} kept")
names = {(e["away_team"], e["home_team"]) for e in kept}
ck("a P4 team hosting a G5 team is DROPPED (we do not card it)",
   ("Boise State", "Oregon") not in names)
ck("a G5-only game is dropped", ("Sam Houston", "UTEP") not in names)
ck("the marquee games are kept", ("Ohio State", "Michigan") in names)

print("\n-- FAIL CLOSED when the names do not join --")
mascots = [ev("Alabama Crimson Tide", "Georgia Bulldogs"),
           ev("Ohio State Buckeyes", "Michigan Wolverines"),
           ev("Texas Longhorns", "Oklahoma Sooners"),
           ev("Clemson Tigers", "Florida State Seminoles"),
           ev("USC Trojans", "UCLA Bruins"),
           ev("Penn State Nittany Lions", "Wisconsin Badgers"),
           ev("Auburn Tigers", "Missouri Tigers"),
           ev("Iowa Hawkeyes", "Nebraska Cornhuskers"),
           ev("Duke Blue Devils", "Virginia Cavaliers"),
           ev("LSU Tigers", "Florida Gators")]
kept2, why2 = collect.filter_power4(mascots, quiet)
ck("🔴 mascot-suffixed names do NOT silently match", len(kept2) == 0)
ck("🔴 it REFUSES rather than pulling, so nothing is spent",
   why2 is not None, str(why2))
ck("it names both lists in a file we can read",
   os.path.exists("data/ncaaf/latest/event-names.txt"))

print("\n-- an genuinely light slate also refuses, and that is correct --")
kept3, why3 = collect.filter_power4([ev("Alabama", "Georgia")], quiet)
ck("one P4 game on the board is below the floor and refuses",
   kept3 == [] and why3 is not None,
   "a Tuesday MACtion board must not be mistaken for a broken join")

print("\n-- the gate cannot touch the other leagues --")
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "collect.py")).read()
ck("filter_power4 is called only under LEAGUE == 'ncaaf'",
   'if LEAGUE == "ncaaf":\n        events, why = filter_power4' in src)
ck("props-player refuses to run as MLB",
   'if LEAGUE == "mlb":\n                log("FATAL: props-player is a FOOTBALL mode' in src)

print()
if FAIL:
    print(f"⛔ {len(FAIL)} FAILED: {FAIL}"); sys.exit(1)
print("✅ the Power 4 gate keeps the right games and fails closed")
