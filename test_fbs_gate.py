#!/usr/bin/env python3
"""The FBS props gate — AT LEAST ONE SIDE, and it stays that way.

🔴 THIS IS THE THIRD TIME THE BOTH-SIDES MISTAKE HAS SHIPPED, and Sam
caught all three. Twice on the Scores division filter, once here on the
props spend gate. ⛔ SO THE BOTH-SIDES FORM IS NOW TESTED AGAINST BY NAME:
section 1 fails if a marquee game is dropped because its opponent is small.

**What the both-sides version actually cost, measured 2026-09-03 on the
real 2026 schedule:** of the 189 September games involving a Power 4 team,
it kept **67** and threw away **122** — Alabama, USC, Oklahoma, Michigan
State, Utah, Missouri, Minnesota, and that night's Rutgers, UCF and Wake
Forest. Every one of them dropped for playing a smaller school, which is
exactly the game people bet.

Sam, 2026-09-03: *"if a fbs team is playing a fcs team i woudl want that
included, for example usf, ucf vs a fcs team."*
⚠️ USF is American Athletic and UCF is Big 12 — **a Power 4 conference
list gets one and not the other.** FBS is a DIVISION, so it covers both
and survives realignment.

✅ WHAT IS PINNED:
  1. 🔴 An FBS school playing an FCS school IS kept. (the whole point)
  2. FCS-vs-FCS is dropped — what Sam asked for, and the books barely
     price it anyway.
  3. ⛔ A BROKEN NAME JOIN SPENDS NOTHING. On a real board ~97% of games
     have an FBS side; matching under 30% means the names stopped
     joining, and that must fail closed rather than quietly collect a
     third of the slate.
  4. The prefix traps still hold — "Washington State" is not "Washington".
  5. The list is READ FROM DISK, never hardcoded, with a floor.

⚠️ No network, no credits. The events are constructed.
"""
import os
import sys

os.environ.setdefault("LEAGUE", "ncaaf")
import collect as C

fails = []


def eq(got, want, label):
    ok = got == want
    print(f"  {'ok  ' if ok else '🔴 FAIL'} {label:<58} {got!r}")
    if not ok:
        fails.append(f"{label} (got {got!r} want {want!r})")


def ev(away, home):
    return {"id": f"{away}@{home}", "away_team": away, "home_team": home}


def names(evs):
    return [e["id"] for e in evs]


# A stand-in FBS list. ⚠️ The REAL one is read from the schedule on disk;
# section 5 checks that path separately.
FAKE_FBS = {"Alabama", "Ohio State", "UCF", "South Florida", "Rutgers",
            "Wake Forest", "Minnesota", "Washington", "Washington State",
            "Florida State", "Florida"}

_real = C.fbs_teams
C.fbs_teams = lambda: FAKE_FBS

print("1. 🔴 AN FBS TEAM PLAYING AN FCS TEAM IS KEPT — the whole point")
marquee = [
    ev("East Carolina Pirates", "Alabama Crimson Tide"),
    ev("Bethune-Cookman Wildcats", "UCF Knights"),
    ev("Massachusetts Minutemen", "Rutgers Scarlet Knights"),
    ev("Akron Zips", "Wake Forest Demon Deacons"),
    ev("Eastern Illinois Panthers", "Minnesota Golden Gophers"),
    ev("Tennessee State Tigers", "South Florida Bulls"),
]
kept, why = C.filter_fbs(marquee, log=lambda *a: None)
eq(len(kept), 6, "all six marquee games kept")
eq(why, None, "and the gate does not refuse")
print("      ⛔ the BOTH-SIDES version kept ZERO of these six.")

print("\n2. FCS vs FCS is dropped, as asked")
mixed = marquee + [ev("Merrimack Warriors", "Delaware Blue Hens"),
                   ev("Bryant Bulldogs", "Stonehill Skyhawks")]
kept, why = C.filter_fbs(mixed, log=lambda *a: None)
eq(len(kept), 6, "the two FCS-only games are dropped")
eq(any("Merrimack" in n for n in names(kept)), False, "Merrimack not kept")

print("\n3. an FBS team on EITHER side qualifies")
eq(len(C.filter_fbs([ev("Alabama Crimson Tide", "Merrimack Warriors")],
                    log=lambda *a: None)[0]), 1, "FBS away, FCS home")
eq(len(C.filter_fbs([ev("Merrimack Warriors", "Alabama Crimson Tide")],
                    log=lambda *a: None)[0]), 1, "FCS away, FBS home")

print("\n4. ⛔ A BROKEN NAME JOIN SPENDS NOTHING")
junk = [ev(f"Nonesuch {i} A", f"Nonesuch {i} B") for i in range(20)]
kept, why = C.filter_fbs(junk, log=lambda *a: None)
eq(kept, [], "🔴 nothing kept, so nothing is bought")
eq(why is not None, True, "and it says WHY, rather than looking like a light slate")
eq("join looks broken" in (why or ""), True, "  ...naming the real cause")
# ⚠️ a genuinely small but VALID slate must still pass
kept, why = C.filter_fbs([ev("Akron Zips", "Wake Forest Demon Deacons")],
                         log=lambda *a: None)
eq((len(kept), why), (1, None), "a one-game Thursday is NOT mistaken for a break")

print("\n5. the prefix traps still hold (the Max Muncy rule for teams)")
kept, _ = C.filter_fbs([ev("Merrimack Warriors", "Washington State Cougars")],
                       log=lambda *a: None)
eq(len(kept), 1, "Washington State is itself FBS here, so kept")
C.fbs_teams = lambda: {"Washington"}          # ⛔ ONLY Washington is FBS
kept, why = C.filter_fbs([ev("Merrimack Warriors", "Washington State Cougars")],
                         log=lambda *a: None)
eq(len(kept), 0, "🔴 'Washington State' must NOT match 'Washington'")
C.fbs_teams = lambda: FAKE_FBS

print("\n6. the real list comes from disk, with a floor, and is not hardcoded")
C.fbs_teams = _real
real = C.fbs_teams()
eq(len(real) >= C.FBS_MIN_TEAMS, True,
   f"read {len(real)} FBS schools from the schedule (floor {C.FBS_MIN_TEAMS})")
for t in ("Alabama", "Ohio State", "UCF", "South Florida", "Florida State"):
    eq(t in real, True, f"  {t} is in the list")
eq("Merrimack" in real, False, "  an FCS school is NOT in the list")

print("\n7. the props window is 36h — the smallest that catches Monday night")
eq(C.FB_PROPS_WINDOW_H, 36, "window constant")

print()
if fails:
    print(f"🔴 {len(fails)} FAILED:")
    for f in fails:
        print("   " + f)
    sys.exit(1)
print("✅ FBS gate OK — one FBS side is enough, FCS-vs-FCS dropped, "
      "broken join spends nothing")
