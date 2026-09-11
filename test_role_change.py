#!/usr/bin/env python3
"""
🔴🔴 THE CARD PROJECTED A STARTING QUARTERBACK FOR 3.5 PASSING YARDS AND
PUT 94% ON THE UNDER.

`[Sam, 2026-09-11]` *"isiah marshall, strarting qb for kansas, wont only
get 3.5 passing yards thats blasphemous. the reason he has this
projetion is because he was not starting last year."*

⛔ **HE IS RIGHT, AND IT WAS ON THE LIVE BOARD.** Measured from the
stored logs:

    2025   8 appearances · THREE pass attempts all season · usage 2.2/gm
           seven of the eight games have no `att` at all
    card   under 196.5 pass yds · 94% · "8 of 8" · projection 3.5
    2026   week 1: 19 att, 246 pass yds, 7 car, usage 26

➡️ **HE CLEARED THAT LINE TWO WEEKS AGO.** The "8 of 8" means "in eight
games where he was not the quarterback, he never threw for 196.5 yards".

🔴 **THE UNION DENOMINATOR IS NOT THE BUG AND IS NOT REVERTED.** Rating a
player over every game he appears in was MEASURED — worth +35.7 points
for a college RB — and it is right for a player doing the SAME JOB: a
game he played and got no carries in really is evidence about his
rushing. ⛔ **What it cannot survive is a ROLE CHANGE**, where the games
it adds are games he held a different job.

✅ **TWO GATES, AND NEITHER INTRODUCES A NEW CONSTANT:**

1. **PARTICIPATION.** The `MIN_GAMES` floor now counts games he took part
   in THAT MARKET. Marshall's passing participation is 1 of 8, under the
   6 that was always required.
2. **THE USAGE FLOOR THE DATA ALREADY SHIPPED.** `players-*.json.gz`
   carries `usage_floor: 3.0`, *"T37-CFB, FROZEN. Applied by the
   CONSUMER"*, and the 2026 file's `consumer_contract` says outright
   *"NO usage floor has been applied."* ⛔ **The consumer is `card_fb.py`
   and it never read the field.** 15 of 50 live rows sat below it.

⚠️ **THIS IS THE MLB LESSON, ALREADY LEARNED TWICE, NEVER APPLIED TO
FOOTBALL.** `CLAUDE.md`: *"Pitcher rates are computed over STARTS ONLY"*
and *"A hitter is rated only over games he STARTED"* — both written
because a different-role appearance was being counted as evidence.

⛔ **NOTHING IS DELETED FROM THE BOARD BY THIS (rule 53).** The row keeps
its price and its book and loses its rate, and the card SAYS WHY with
the current season's own numbers.
"""
import os
import sys

from tcheck import ck, eq, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

os.environ.setdefault("LEAGUE", "ncaaf")
os.environ.setdefault("ODDS_API_KEY", "")
import card_fb as C  # noqa: E402


def gm(**kw):
    g = {"att": None, "cmp": None, "pass_yds": None, "car": None,
         "rush_yds": None, "rec": None, "rec_yds": None, "usage": 0}
    g.update(kw)
    return g


# 🔴 THE LIVE SHAPE, REBUILT AS A FIXTURE so no calendar and no board can
#    falsify it (rule 166). Seven mop-up runs and one game with 3 passes.
BACKUP_QB = ([gm(car=1, rush_yds=13, usage=1)] * 4
             + [gm(car=2, rush_yds=13, usage=2)]
             + [gm(car=5, rush_yds=36, usage=5)]
             + [gm(car=1, rush_yds=6, usage=1)]
             + [gm(att=3, cmp=3, pass_yds=28, car=3, rush_yds=23, usage=6)])
# ✅ A REAL STARTER: same game count, the job actually done.
STARTER_QB = [gm(att=30, cmp=20, pass_yds=250, car=4, rush_yds=20,
                 usage=34)] * 8

print("\n═══ 1. 🔴 A BACKUP'S LOG IS NOT A RATE ABOUT A STARTER'S LINE ═══")
C.USAGE_FLOOR = None       # isolate the participation gate
eq(len(BACKUP_QB), 8, "eight appearances, which clears MIN_GAMES on count")
_part = sum(1 for g in BACKUP_QB if (g.get("att") or 0) > 0)
eq(_part, 1, "...and ONE of them is a game he attempted a pass")
ck("🔴 no passing rate is produced from it",
   C.rate_for(BACKUP_QB, "player_pass_yds", 196.5, "under") is None,
   "⛔ THE LIVE DEFECT: this returned 94%% on the under with a 3.5 "
   "projection, for the 2026 starter who threw for 246 in week 1. "
   "MIN_GAMES=%d, participation=%d" % (C.MIN_GAMES, _part))
ck("✅ ...and a real starter's identical game count DOES rate",
   C.rate_for(STARTER_QB, "player_pass_yds", 196.5, "under") is not None,
   "⛔ THE GATE MUST NOT JUST EMPTY THE BOARD. Eight games of actually "
   "playing the position is exactly what a rate is for")

print("\n═══ 2. ✅ THE UNION DENOMINATOR SURVIVES, WHICH IS THE POINT ═══")
# ⛔ A RB who played eight games and was held to nothing in two of them
#    is STILL rated over all eight — that is the +35.7 points the union
#    was measured for, and this fix must not quietly undo it.
RB = [gm(car=12, rush_yds=60, usage=12)] * 6 + [gm(car=0, rush_yds=0,
                                                   usage=3)] * 2
r = C.rate_for(RB, "player_rush_yds", 49.5, "under")
ck("🔴 a back with 6 carrying games and 2 blanks is still rated",
   r is not None, "participation is 6, which is the floor exactly")
eq(r[2], 8,
   "⛔ AND THE DENOMINATOR IS STILL ALL EIGHT GAMES — the blanks are "
   "real evidence about his rushing, worth +35.7 points when it was "
   "measured. The gate decides WHETHER to rate, never WHAT OVER")

print("\n═══ 3. 🔴 THE FLOOR THE DATA SHIPS IS ACTUALLY APPLIED ═══")
LOW = [gm(car=2, rush_yds=14, usage=2)] * 10
C.USAGE_FLOOR = 3.0
ck("⛔ 2.0 touches a game is under the shipped 3.0 and gets no rate",
   C.rate_for(LOW, "player_rush_yds", 24.5, "under") is None,
   "🔴 `usage_floor` is FROZEN BY T37-CFB and the file says in words "
   "that the CONSUMER applies it — and `card_fb.py` never read the "
   "field. 15 of 50 live rows sat below it")
C.USAGE_FLOOR = None
ck("✅ ...and with NO floor shipped, nothing is gated on it",
   C.rate_for(LOW, "player_rush_yds", 24.5, "under") is not None,
   "⛔ AN ABSENT FLOOR IS NOT A FLOOR OF ZERO. A season file that ships "
   "no `usage_floor` must not silently acquire one")
ck("🔴 ...and the floor is read from the FILE, never restated in code",
   "d.get(\"usage_floor\")" in open("card_fb.py", encoding="utf-8").read(),
   "rule 66 — a second copy of a frozen constant is a second thing to "
   "drift, which is exactly what rule 207 was about this morning")

print("\n═══ 4. ⛔ THE ROW KEEPS ITS PRICE AND SAYS WHY (rule 53) ═══")
# ⚠️ THE FLOOR IS RESTORED FIRST. Section 3 left it at None to isolate the
#    other gate, and the first form of this section forgot — so the
#    usage-floor sentence check failed on correct code because the floor
#    was switched off (rule 202, the fixture half, again).
C.USAGE_FLOOR = 3.0
_why = C.no_rate_reason(True, {"g": BACKUP_QB}, "A Player",
                        "player_pass_yds", 2025)
ck("🔴 the reason names PARTICIPATION, not 'too few games'",
   "took part in this market in only 1 of his 8" in _why,
   "⛔ THE OLD SENTENCE SAID 'appears in too few games' WHATEVER HAD "
   "HAPPENED — so the row that mattered most read as a thin sample "
   "rather than as the WRONG sample: %s" % _why[:140])
ck("✅ ...and it says what a record over the wrong games is worth",
   "did not play the position" in _why, _why[:120])
_why2 = C.no_rate_reason(True, {"g": LOW}, "B Player",
                         "player_rush_yds", 2025)
ck("⚠️ a usage-floor row gets its OWN sentence, with the number",
   "touches a game" in _why2 and "2.0" in _why2,
   "⛔ two different causes must not share one message — that is the "
   "09-10 empty-board defect's shape (rule 179): %s" % _why2[:140])
eq(_why == _why2, False,
   "🔴 participation and low usage are DIFFERENT FACTS about a player "
   "and a reader has to be able to tell which one happened")

print("\n═══ 5. ⚠️ THE ROLE-CHANGE NOTE IS DESCRIPTIVE AND NEVER A RATE ═══")
# ⛔ DRIVEN ON A SYNTHETIC CURRENT SEASON, not on the live log. The live
#    one is one game deep today and will be fifteen in December, so a
#    check that reads it has an expiry date (rule 166).
C.CUR_SEASON = 2026
C.CUR_P = {"x1": {"name": "A Player", "pos": "QB",
                  "g": [gm(att=19, cmp=12, pass_yds=246, car=7,
                           rush_yds=49, usage=26)]}}
C._CUR_IDX = None
_role = C.role_change_note("A Player", "player_pass_yds", 2025)
ck("🔴 it reports what he is doing NOW, in his own numbers",
   _role and "26 touches a game" in _role and "246 pass yds a game" in _role,
   "⛔ THE ANSWER TO SAM'S QUESTION IS A MEASUREMENT, NOT A SHRUG. "
   "`he was not starting last year` is visible in the current log: %s"
   % (_role or "None"))
ck("⛔ ...and it carries no percentage and no projection",
   _role and "%" not in _role and "projection" not in _role.lower(),
   "🔴 ONE GAME IS NOT A RATE. `MIN_GAMES` exists precisely because a "
   "week-1 log cannot carry a percentage — what it CAN do is say the "
   "record describes a different job")
ck("✅ ...and the no-rate sentence carries it through to the reader",
   "In 2026 so far" in C.no_rate_reason(True, {"g": BACKUP_QB}, "A Player",
                                        "player_pass_yds", 2025),
   "a reason the reader cannot check is a reason they will not believe")
ck("⛔ it says NOTHING when the current season IS the rated one",
   C.role_change_note("A Player", "player_pass_yds", 2026) is None,
   "🔴 there is no comparison to make, and inventing one would fold two "
   "seasons into a claim about one")
C.CUR_P = {"x1": {"name": "A Player", "g": [gm(usage=26)]},
           "x2": {"name": "A Player", "g": [gm(usage=1)]}}
C._CUR_IDX = None
ck("⛔ ...and NOTHING when two players share the name",
   C.role_change_note("A Player", "player_pass_yds", 2025) is None,
   "🔴 `index_by_name` keeps duplicates as a LIST on purpose, for the "
   "same reason the MLB collector's `resolve()` refuses a first match: "
   "attaching one player's season to another player's price is worse "
   "than saying nothing")

note("⛔ WHAT THIS DOES NOT DO: predict what the new role is worth. "
     "There is no football model — T46, T47, T50 and T57 all lost to a "
     "player's own season average — so the card shows the PRICE and "
     "says the record does not apply. ➡️ Guessing a starter's line from "
     "one game would be the exact thing four pre-registered tests said "
     "not to do.")
note("⚠️ AND THE BOARD GETS SMALLER, WHICH IS CORRECT. On the live "
     "2026-09-11 college board this takes 50 rated rows to 37, and the "
     "13 keep their prices. A smaller honest board beats a full one "
     "carrying 94% on a number nobody measured.")
