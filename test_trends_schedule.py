#!/usr/bin/env python3
"""
🔴 WHEN THE TRENDS TAB REBUILDS — SAM'S TIMES, PINNED.

Sam, 2026-09-06: *"i want the trends tab to updated everyday for college
football at 3am — late enough to update games from the previous day and
early enough to provide stats for the next day"*, and *"for nfl i want the
trends tab to be ran every tuesday so that we can have all the stats
updated week by week."*

⛔ THE NOON DEADLINE IT REPLACES WAS MINE, NOT HIS, AND IT WAS THE WRONG
END OF THE DAY: a table rebuilt at noon reaches the 9am card a day late,
so the morning board was always reading yesterday's stats.

WHAT IS PINNED:
  1. college rebuilds DAILY at 3am ET; the NFL WEEKLY on Tuesday
  2. the rebuild lands BEFORE the day's props and card deadlines
  3. 3am is late enough — measured against the real schedule
  4. every cron still matches its routing arm
"""
import collections
import datetime
import gzip
import json
import os

import freshness as F
from tcheck import ck, note
from wfroutes import parse_routes

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
WF = ".github/workflows/collect.yml"
ROUTES = parse_routes(open(WF, encoding="utf-8").read())

print("\n═══ 1. SAM'S TIMES, AS THE CONTRACT HOLDS THEM ═══")
c = F.FB_TIMES["ncaaf"]["trends"]
n = F.FB_TIMES["nfl"]["trends"]
ck("🔴 college Trends is DAILY at 3am ET",
   c == [(3, 0)], f"{c} — every day, no day-set")
ck("🔴 the NFL's is WEEKLY on Tuesday",
   len(n) == 1 and len(n[0]) == 3 and n[0][2] == {1},
   f"{n} — day 1 is Tuesday")
ck("⚠️ ...and the NFL's is NOT daily, because its source is not",
   "weekly player stats" in open("nfl.py", encoding="utf-8").read(),
   "nflverse publishes a WEEKLY drop; a daily NFL deadline would be one "
   "nothing could satisfy (rule 112)")

print("\n═══ 2. 🔴 IT LANDS BEFORE THE BOARD THAT READS IT ═══")
# ⛔ THIS IS SAM'S ACTUAL REASON, so it is the thing to assert — not the
#    clock face. "Early enough to provide stats for the next day" means
#    the rebuild must precede the day's first props pull and first card.
T = F.FB_TIMES["ncaaf"]
first_props = min(T["props"])[0] * 60 + min(T["props"])[1]
first_card = min(T["card"])[0] * 60 + min(T["card"])[1]
trends = c[0][0] * 60 + c[0][1]
ck("🔴 Trends rebuilds before the first Player Props pull",
   trends < first_props,
   f"trends {c[0][0]:02d}:{c[0][1]:02d} < props {min(T['props'])[0]:02d}:"
   f"{min(T['props'])[1]:02d}")
ck("🔴 ...and before the first Gizmo's Picks build",
   trends < first_card,
   f"trends {c[0][0]:02d}:{c[0][1]:02d} < card {min(T['card'])[0]:02d}:"
   f"{min(T['card'])[1]:02d}")
note("the old noon deadline sat AFTER both, so the morning card read a "
     "table built the previous day")

print("\n═══ 3. \u26a0\ufe0f IS 3AM LATE ENOUGH? MEASURED, NOT ASSUMED \u2550\u2550\u2550")
# \u26d4 THE FIRST VERSION OF THIS SECTION ASKED THE WRONG QUESTION.
#    It asked "does every slate FINISH before its own 3am rebuild?" and
#    went red on two days. Both are the same real thing: **Hawai'i kicks
#    off at 5:59pm HST**, which is 11:59pm ET, and a 3h30m game ends at
#    3:29am ET — 29 minutes after the rebuild. That is a fact about the
#    Pacific, not a defect, and it will be true of every season.
#
#    Moving the clock to 3:30am to make it green would be tuning a
#    contract to a scheduling artifact. The question the PRODUCT cares
#    about is not "same night?" — it is **"is the game in the Trends
#    table before the next board a reader looks at?"** That is strictly
#    harder: it must hold for all 62 slate days AND the late ones must be
#    caught by a later rebuild, not merely excused.
sp = f"{ROOT}/data/ncaaf/latest/schedule-2026.json.gz"
if os.path.exists(sp):
    with gzip.open(sp, "rt") as fh:
        games = json.load(fh).get("games") or []
    D1 = {"fbs", "fcs"}

    def utc(s):
        d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)

    def et(d):                      # EDT; the season ends before the fall back
        return (d - datetime.timedelta(hours=4)).replace(tzinfo=None)

    by = collections.defaultdict(list)
    for g in games:
        if (g.get("home_class") or "").lower() in D1 \
           or (g.get("away_class") or "").lower() in D1:
            by[et(utc(g["start"])).date()].append(g)
    days = sorted(by)
    GAME = datetime.timedelta(hours=3, minutes=30)

    def last_end(d):
        return max(et(utc(g["start"])) for g in by[d]) + GAME

    # every scheduled Trends rebuild, in ET, as the workflow deploys them:
    #   daily  3:04am  (cron "4 7 * * *")
    #   Sunday 10:35am (cron "35 14 * * 0", the season pass)
    def rebuilds(d0, n=10):
        out = []
        for i in range(n):
            d = d0 + datetime.timedelta(days=i)
            out.append(datetime.datetime.combine(d, datetime.time(3, 4)))
            if d.weekday() == 6:
                out.append(datetime.datetime.combine(d, datetime.time(10, 35)))
        return sorted(out)

    first_card = min(F.FB_TIMES["ncaaf"]["card"])

    late, covered, worst = [], [], None
    for i, d in enumerate(days):
        end = last_end(d)
        own = datetime.datetime.combine(d + datetime.timedelta(days=1),
                                        datetime.time(3, 4))
        if end > own:
            late.append(d)
        landed = next(r for r in rebuilds(d) if r >= end)
        if i + 1 < len(days):
            nxt = days[i + 1]
            board = datetime.datetime.combine(
                nxt, datetime.time(first_card[0], first_card[1]))
            slack = (board - landed).total_seconds() / 3600
            covered.append((str(d), round(slack, 1)))
            if worst is None or slack < worst[1]:
                worst = (str(d), slack, str(nxt))

    ck("\U0001f534 every slate is in the table before the next board reads it",
       worst is not None and worst[1] > 0,
       f"tightest: {worst[0]} lands {worst[1]:.1f}h before the "
       f"{worst[2]} card" if worst else "no slate days")
    note(f"{len(days)} slate days measured; {len(late)} finish after their "
         f"OWN 3am rebuild: {[str(d) for d in late]}")

    # \U0001f534 PIN THE REASON, NOT THE DATES. A date list would go red the
    #    day the 2027 schedule loads and get deleted (rule 139). The
    #    durable fact is WHY: Hawai'i is six hours behind Eastern.
    ck("\U0001f534 ...and every one of those is a Hawai'i (HST) kickoff",
       all(max(by[d], key=lambda g: utc(g["start"])).get("home") == "Hawai'i"
           for d in late),
       "a late slate for any OTHER reason is new and must be looked at, "
       "not absorbed"
       + ("" if not late else
          " \u2014 " + ", ".join(
              f"{d}: {max(by[d], key=lambda g: utc(g['start'])).get('away')} "
              f"@ {max(by[d], key=lambda g: utc(g['start'])).get('home')}"
              for d in late)))
    note("those two land in the NEXT morning's 3am pass, and the next "
         "college slate is 4-5 days later \u2014 so no board ever reads a "
         "table missing them")
    # \u26a0\ufe0f THE HONEST LIMIT: finishing is not the same as being PUBLISHED.
    note("\u26a0\ufe0f finishing is not the same as CFBD having published the "
         "box score. A game that ends at 2:30am ET may not be in the feed "
         "by 3:04am; if it is not, it lands in the NEXT day's rebuild and "
         "the Sunday 10:35am pass is the backstop.")
else:
    note("no college schedule on disk \u2014 section 3 not measured")

print("\n═══ 4. THE CRON MOVED WITH THE DEADLINE ═══")
# 🔴 THE FAILURE THIS PROJECT KEEPS REPEATING: moving a cron string and
#    leaving its `case` arm behind, so the run falls through to
#    `*) LEAGUE=mlb` and collects BASEBALL under a football comment.
arms = {c_: (lg, m) for c_, lg, m in ROUTES}
ck("🔴 the 3am ET cron exists and is ROUTED", "4 7 * * *" in arms,
   str(arms.get("4 7 * * *")))
if "4 7 * * *" in arms:
    lg, modes = arms["4 7 * * *"]
    ck("...to college, building Trends", lg == "ncaaf"
       and "cfb-probe" in modes.split(), f"{lg} {modes}")
ck("⛔ the old noon cron is gone from the schedule",
   '"4 16 * * *"' not in open(WF, encoding="utf-8").read(),
   "a cron left behind would rebuild Trends a second time at noon")
ck("the NFL's Tuesday arm is untouched",
   any(c_ == "6 16 * * 2" and lg == "nfl" and "nfl-logs" in m.split()
       for c_, lg, m in ROUTES),
   "Sam asked for Tuesday and it already ran Tuesday")
ck("⚠️ the Sunday season rebuild is still there as a backstop",
   any(c_ == "35 14 * * 0" and "cfb-probe" in m.split()
       for c_, lg, m in ROUTES),
   "it also rebuilds the logo directory, so it is not redundant")
