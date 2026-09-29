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

`[2026-09-28]` Item 3 is asked of PLANTED schedules every run (one that
must pass, two that must fail); the live CFBD schedule is reported.

# @vacuity 🔴 the planted Friday slate must be in the table before Saturday's first card
#   file: freshness.py
#   find: "card":   [(9, 0), (9, 30)],
#   with: "card":   [(2, 0), (9, 30)],
#
# @vacuity ⚠️ the rebuild instants are the ROUTED college cfb-probe crons
#   file: .github/workflows/collect.yml
#   find: "4 7 * * *")        LEAGUE=ncaaf; MODES="cfb-probe";  SEASON=CUR ;;
#   with: "4 7 * * *")        LEAGUE=ncaaf; MODES="cfb-teams";  SEASON=CUR ;;
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

print("\n═══ 3. ⚠️ IS 3AM LATE ENOUGH? MEASURED, NOT ASSUMED ═══")
# ⛔ THE FIRST VERSION OF THIS SECTION ASKED THE WRONG QUESTION.
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
#
# 🔴 `[2026-09-28]` ~~ck() over the LIVE schedule-2026.json.gz~~ (pattern
#    P3). CFBD rewrites that file several times a day, so the verdict was
#    a fact about the feed, not about the contract: one Pacific kickoff
#    moved 15 minutes later turned both checks red with no code change, and
#    on a schedule with no late day the Hawai'i check passed over an empty
#    list. ✅ The measurement is now ONE function, driven every run on
#    PLANTED schedules — one that must pass and two that must fail — and
#    the live schedule is measured by the same function and REPORTED.
# ⚠️ AND THE INPUTS ARE THE PRODUCT'S OWN: the rebuild instants are every
#    ROUTED college `cfb-probe` cron (not a copy of their times), and the
#    board is the contract's first college card deadline, placed in UTC
#    the way `freshness.py` places every deadline (`ET_OFFSET`).
# ⚠️ ~~"EDT; the season ends before the fall back"~~ — FALSE, the college
#    season runs into December. Slate days are now binned by the real
#    Eastern date (EDT until the first Sunday of November, EST after), so
#    a 6pm HST November kickoff (23:00 EST) is not filed under Sunday.
D1 = {"fbs", "fcs"}
GAME = datetime.timedelta(hours=3, minutes=30)
UTC = datetime.timezone.utc


def utc(s):
    d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=UTC)


def _nth_sunday(y, mo, nth):
    d = datetime.date(y, mo, 1)
    d += datetime.timedelta(days=(6 - d.weekday()) % 7)
    return d + datetime.timedelta(weeks=nth - 1)


def et_date(d):
    """The US Eastern calendar date of a UTC instant (DST by the US rule:
    2am local on the 2nd Sunday of March to the 1st Sunday of November).
    ⚠️ Hand-rolled, not zoneinfo, so it needs no tzdata on any machine."""
    y = d.year
    on = datetime.datetime.combine(_nth_sunday(y, 3, 2), datetime.time(7), UTC)
    off = datetime.datetime.combine(_nth_sunday(y, 11, 1), datetime.time(6), UTC)
    return (d - datetime.timedelta(hours=4 if on <= d < off else 5)).date()


def rebuild_crons(routes):
    """[(minute, hour, weekday-or-None)] for every routed college Trends
    rebuild. Cron weekday 0 is Sunday; Python's is Monday=0."""
    out = []
    for c_, lg_, m_ in routes:
        if lg_ != "ncaaf" or "cfb-probe" not in m_.split():
            continue
        f = c_.split()
        if len(f) == 5 and f[0].isdigit() and f[1].isdigit() and f[2] == f[3] == "*":
            out.append((int(f[0]), int(f[1]),
                        None if f[4] == "*" else (int(f[4]) - 1) % 7))
    return out


def measure(games, crons, first_card):
    """-> {days, late, reasons, worst}. `late` = slates that end after their
    OWN overnight rebuild; `worst` = the tightest (slate, hours between the
    rebuild that catches it and the NEXT slate's first card, next slate)."""
    by = collections.defaultdict(list)
    for g in games:
        if (g.get("home_class") or "").lower() in D1 \
           or (g.get("away_class") or "").lower() in D1:
            by[et_date(utc(g["start"]))].append(g)
    days = sorted(by)

    def instants(d0, n=10):
        out = []
        for i in range(n):
            day = d0 + datetime.timedelta(days=i)
            for mm, hh, wd in crons:
                if wd is None or day.weekday() == wd:
                    out.append(datetime.datetime.combine(day, datetime.time(hh, mm), UTC))
        return sorted(out)

    daily = [(mm, hh) for mm, hh, wd in crons if wd is None]
    late, reasons, worst = [], {}, None
    for i, d in enumerate(days):
        last = max(by[d], key=lambda g: utc(g["start"]))
        end = utc(last["start"]) + GAME
        if daily:
            own = datetime.datetime.combine(
                d + datetime.timedelta(days=1), datetime.time(daily[0][1], daily[0][0]), UTC)
            if end > own:
                late.append(d)
                reasons[d] = (last.get("away"), last.get("home"))
        landed = next((r for r in instants(d) if r >= end), None)
        if i + 1 < len(days) and landed is not None:
            nxt = days[i + 1]
            board = datetime.datetime.combine(
                nxt, datetime.time(first_card[0], first_card[1]), UTC) + F.ET_OFFSET
            slack = (board - landed).total_seconds() / 3600
            if worst is None or slack < worst[1]:
                worst = (str(d), slack, str(nxt))
    return {"days": days, "late": late, "reasons": reasons, "worst": worst,
            "hawaii_only": all(h == "Hawai'i" for _a, h in reasons.values())}


CRONS = rebuild_crons(ROUTES)
FIRST_CARD = min(F.FB_TIMES["ncaaf"]["card"])
ck("⚠️ the college Trends rebuilds are read from the routed crons, one of them daily",
   bool(CRONS) and any(wd is None for _m, _h, wd in CRONS),
   "⛔ rule 67: with no rebuild instant nothing below can be late or "
   "covered. got %s" % CRONS)


def _g(start, home="Home U", away="Away U"):
    return {"start": start, "home": home, "away": away,
            "home_class": "fbs", "away_class": "fbs"}


# ✅ MUST PASS — the shapes the contract is built for: a Friday game that
#    must be in the table by Saturday's first card, a Saturday slate whose
#    last game is Hawai'i at 5:59pm HST (LATE, and caught next pass), and
#    the next slate on Wednesday night.
_ok = measure([_g("2026-10-02T23:00:00Z"),                    # Fri 7pm ET
               _g("2026-10-03T16:00:00Z"), _g("2026-10-03T23:30:00Z"),
               _g("2026-10-04T03:59:00Z", home="Hawai'i"),    # Sat 11:59pm ET
               _g("2026-10-08T00:00:00Z")],                   # Wed 8pm ET
              CRONS, FIRST_CARD)
ck("🔴 PLANTED: every slate is in the table before the next board reads it",
   _ok["worst"] is not None and _ok["worst"][1] > 0,
   "tightest: %s" % (_ok["worst"],))
ck("🔴 PLANTED: ...the Hawai'i slate IS late, and Hawai'i is the only reason",
   [str(d) for d in _ok["late"]] == ["2026-10-03"] and _ok["hawaii_only"],
   "late %s, reasons %s" % ([str(d) for d in _ok["late"]], _ok["reasons"]))
# ⛔ MUST FAIL — the two defects the live check exists to surface. They
#    prove the measurement can go red; a guard that cannot fail is not one.
_other = measure([_g("2026-10-03T16:00:00Z"),
                  _g("2026-10-04T03:45:00Z", home="Nevada"),  # 11:45pm ET, not HST
                  _g("2026-10-08T00:00:00Z")], CRONS, FIRST_CARD)
ck("⛔ PLANTED: a late slate for any reason but Hawai'i is FLAGGED, not absorbed",
   bool(_other["late"]) and not _other["hawaii_only"],
   "late %s, reasons %s" % ([str(d) for d in _other["late"]], _other["reasons"]))
_tight = measure([_g("2026-10-03T03:59:00Z", home="Hawai'i"),  # Fri 11:59pm ET
                  _g("2026-10-03T16:00:00Z")], CRONS, FIRST_CARD)  # Sat noon ET
ck("⛔ PLANTED: a late Friday before a Saturday slate is a board reading a "
   "stale table — FLAGGED",
   _tight["worst"] is not None and _tight["worst"][1] <= 0,
   "tightest: %s" % (_tight["worst"],))
_nov = measure([_g("2026-11-15T04:00:00Z", home="Hawai'i")], CRONS, FIRST_CARD)
ck("⚠️ PLANTED: a 6pm HST kickoff in November is SATURDAY's slate (23:00 EST)",
   [str(d) for d in _nov["days"]] == ["2026-11-14"],
   "⛔ a fixed UTC-4 files it under a Sunday slate that does not exist. "
   "got %s" % [str(d) for d in _nov["days"]])

sp = f"{ROOT}/data/ncaaf/latest/schedule-2026.json.gz"
if os.path.exists(sp):
    with gzip.open(sp, "rt") as fh:
        _live = measure(json.load(fh).get("games") or [], CRONS, FIRST_CARD)
    _w = _live["worst"]
    # ⚠️ REPORTED, NOT ASSERTED: CFBD edits this file every day. A late or
    #    uncovered LIVE slate is a finding about the feed for a person to
    #    read — the contract's own shapes are asserted above, every run.
    note("%s LIVE: %d slate days; tightest %s lands %.1fh before the %s card"
         % ("✅" if (_w and _w[1] > 0) else "⛔ UNCOVERED",
            len(_live["days"]), _w[0] if _w else "-", _w[1] if _w else 0.0,
            _w[2] if _w else "-"))
    note("%s LIVE: %d finish after their OWN 3am rebuild: %s"
         % ("✅" if _live["hawaii_only"] else "⛔ NOT ONLY HAWAI'I —",
            len(_live["late"]),
            ", ".join("%s: %s @ %s" % (d, a, h) for d, (a, h) in sorted(_live["reasons"].items()))
            or "none"))
    note("those land in the NEXT morning's 3am pass, and the next college "
         "slate is 4-5 days later — so no board ever reads a table missing them")
    # ⚠️ THE HONEST LIMIT: finishing is not the same as being PUBLISHED.
    note("⚠️ finishing is not the same as CFBD having published the "
         "box score. A game that ends at 2:30am ET may not be in the feed "
         "by 3:04am; if it is not, it lands in the NEXT day's rebuild and "
         "the Sunday 10:35am pass is the backstop.")
else:
    note("no college schedule on disk — the live schedule was not measured; "
         "the planted schedules above were")

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
# 🔴 ASK THE SCHEDULE, NOT THE FILE. A raw `in` over the whole workflow
#    reads STRUCK COMMENTS as live crons — this project has already had
#    six false failures from string-searching source that quotes its own
#    history. The question is "is it in the schedule block", and the
#    schedule block is exactly what `parse_routes` returns.
_deployed = {c_ for c_, _l, _m in ROUTES}
ck("⛔ the old noon cron is gone from the schedule",
   "4 16 * * *" not in _deployed,
   "a cron left behind would rebuild Trends a second time at noon; "
   f"{len(_deployed)} cron(s) deployed")
note("⚠️ this reads the ROUTED crons, so a commented-out or documented "
     "cron cannot fail it and an unrouted one cannot hide from it")
ck("the NFL's Tuesday arm is untouched",
   any(c_ == "6 16 * * 2" and lg == "nfl" and "nfl-logs" in m.split()
       for c_, lg, m in ROUTES),
   "Sam asked for Tuesday and it already ran Tuesday")
ck("⚠️ the Sunday season rebuild is still there as a backstop",
   any(c_ == "35 14 * * 0" and "cfb-probe" in m.split()
       for c_, lg, m in ROUTES),
   "it also rebuilds the logo directory, so it is not redundant")
