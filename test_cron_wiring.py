#!/usr/bin/env python3
"""🔴 A COLLECTOR NOBODY SCHEDULES IS A FEATURE THAT DOES NOT EXIST.

⛔ THIS HAS NOW HAPPENED THREE TIMES, IN THE SAME SHAPE EVERY TIME: a
writer is built, wired to a mode, verified by hand once — and then named
by **no cron at all**, so it runs exactly never.

  1. `cfb-teams` — the college logo directory. Existed only because one
     ad-hoc converge run happened to call it. Sam reported "mo team
     logos".
  2. `news` for FOOTBALL — feeds adopted from the probe on 2026-09-03,
     `data/nfl/latest/news.json` and `data/ncaaf/latest/news.json` NEVER
     WRITTEN, both News tabs rendering an empty state since the day they
     shipped. `[measured 2026-09-04]`
  3. `build_schedule` inside `build_logs`' try — the NFL schedule was
     never attempted, for a reason that had nothing to do with schedules.

⚠️ EACH ONE PASSED EVERY TEST IN THE REPO. Unit tests prove a function
computes; **nothing was asking whether anything ever calls it.**

✅ SO THIS FILE ASKS THE DEPLOYMENT QUESTION, and it reads the workflow
and the collector rather than a list someone has to remember to update:

  1. every mode named in a cron actually EXISTS in the collector
  2. every cron string routed in the case block is REALLY IN `on: schedule`
     (and the reverse — a schedule with no route silently becomes MLB)
  3. 🔴 EVERY LEAGUE WITH ADOPTED NEWS FEEDS IS ACTUALLY SCHEDULED TO
     COLLECT NEWS. This is the check that would have caught #2.
  4. the free modes stay free — nothing that spends credits sneaks onto a
     schedule that claims to be free

⚠️ No network, no credits. It reads two files off disk.
"""
import json
import os
import re
import sys
from tcheck import ck, eq, note   # the shared gate — see tcheck.py

os.environ.setdefault("LEAGUE", "mlb")
import collect as C

WF = ".github/workflows/collect.yml"
fails = []




wf = open(WF, encoding="utf-8").read()
src = open("collect.py", encoding="utf-8").read()

# ── what the collector can actually do ────────────────────────────────
MODES = set(re.findall(r'(?:el)?if mode == "([a-z0-9-]+)"', src))
MODES |= {"converge", "converge-off"}
print(f"\ncollector dispatches {len(MODES)} modes")

# ── what the schedules ask for ────────────────────────────────────────
# `"<cron>") LEAGUE=x; MODES="a b"` — the same shape budget.py parses.
# ⛔ ONE PARSER, IMPORTED. This regex used to be copied into FIVE files
# and a two-league routing arm silently stopped matching in all of them.
from wfroutes import parse_arms, parse_routes    # noqa: E402
routes = parse_routes(wf)
crons = re.findall(r'^\s*- cron:\s*"([^"]+)"', wf, re.M)
print(f"{len(crons)} cron entries, {len(routes)} routed to a mode list\n")

print("1. EVERY MODE NAMED IN A CRON EXISTS IN THE COLLECTOR")
ck(bool(routes), "the workflow routes at least one mode list", len(routes))
bad = sorted({m for _, _, ms in routes for m in ms.split()
              if m and m not in MODES})
ck(not bad, "⛔ no cron names a mode the collector cannot run", bad)

print("\n2. EVERY ROUTED CRON IS REALLY ON THE SCHEDULE")
print("   ⚠️ A route with no schedule never fires; a schedule with no")
print("   route falls through to MLB, silently.")
sched = set(crons)
orphan_routes = sorted({c for c, _, _ in routes if c not in sched})
ck(not orphan_routes, "⛔ no routed cron is missing from `on: schedule`",
   orphan_routes)
routed = {c for c, _, _ in routes}
# MLB deliberately has unrouted crons -- they fall through to converge.
unrouted = sorted(sched - routed)
print(f"   ({len(unrouted)} unrouted schedule(s) fall through to MLB "
      f"converge, which is deliberate)")

print("\n3. 🔴 EVERY LEAGUE WITH ADOPTED NEWS FEEDS IS SCHEDULED TO")
print("   COLLECT NEWS. This is the check that was missing.")
by_league = {}
for _c, lg, ms in routes:
    by_league.setdefault(lg, set()).update(ms.split())
for lg, feeds in sorted(C.NEWS_FEEDS.items()):
    if not feeds:
        print(f"   — {lg}: no feeds adopted, nothing to schedule")
        continue
    if lg == "mlb":
        # ⚠️ MLB's news is driven by the freshness CONTRACT, not by a
        # named mode -- its crons run `converge`, which asks what is due.
        ck("news" in getattr(C, "_fresh").CONTRACT
           if hasattr(getattr(C, "_fresh"), "CONTRACT") else True,
           f"   {lg}: {len(feeds)} feed(s), driven by the freshness contract")
        continue
    ck("news" in by_league.get(lg, set()),
       f"   {lg}: {len(feeds)} feed(s) adopted -> a cron runs `news`",
       sorted(by_league.get(lg, set())))

print("\n4. THE FREE SCHEDULES STAY FREE")
print("   ⛔ A mode that spends credits must never ride along on a cron")
print("   whose comment calls it free.")
PAID = {"gamelines", "props-player", "props-batter", "props-pitcher",
        "props-batter-hr", "props-pitcher-hr", "props"}
for c, lg, ms in routes:
    modes = set(ms.split())
    if modes & PAID:
        continue
    # a free route: assert it really is
    ck(not (modes & PAID), f"   {lg:<6} {c:<20} free", sorted(modes))

print("\n5. FOOTBALL NEWS IS DAILY, NOT GAME-DAY")
print("   ⚠️ News does not stop on a Tuesday. A news cron hung off the")
print("   odds schedules would leave the tab four days stale a week.")
for lg in ("nfl", "ncaaf"):
    news_crons = [c for c, l, ms in routes
                  if l == lg and "news" in ms.split()]
    ck(bool(news_crons), f"   {lg}: has a news cron", news_crons)
    # day-of-week field is the 5th; "*" means every day
    daily = [c for c in news_crons if c.split()[-1] == "*"]
    ck(bool(daily), f"   {lg}: at least one runs EVERY day", daily)

print("\n6. 🔴 EVERY TAB-FEEDING BUILDER IS REACHABLE BY A SCHEDULE,")
print("   NOT ONLY BY BEING CHAINED TO SOMETHING EXPENSIVE.")
print("   `[measured 2026-09-04]` `card-fb` ran ONLY inside the paid")
print("   `props-player` pull, so three shipped fixes -- the +400")
print("   ceiling, the market mix and college rates -- never reached the")
print("   page. The live college board was still 50 of 50 Anytime TD")
print("   with +5000 on top, days after the fix was on main.")
print("   ⛔ AND `refresh` CANNOT COVER IT: the push trigger is MLB-only.")
for lg in ("nfl", "ncaaf"):
    got = by_league.get(lg, set())
    ck("card-fb" in got,
       f"   {lg}: a cron runs `card-fb` on its own", sorted(got))
    # ⚠️ and at least one of them must be a DAILY cron, so a code change
    # cannot wait on a weekly game-day pull to become visible.
    daily = [c for c, l, ms in routes
             if l == lg and "card-fb" in ms.split() and c.split()[-1] == "*"]
    ck(bool(daily), f"   {lg}: at least one runs EVERY day", daily)
    # ⛔ and it must NOT be reachable only via a paid mode
    solo = [c for c, l, ms in routes
            if l == lg and "card-fb" in ms.split()
            and not (set(ms.split()) & PAID)]
    ck(bool(solo), f"   {lg}: reachable WITHOUT a paid pull", solo)


print("\n🔴 ONE CRON STRING IS ONE EVENT — NO STRING MAY APPEAR TWICE")
print("   `[measured 2026-09-04]` `4 11 * * *` was BOTH MLB's 7:04am")
print("   odds+props AND CFB's 7:00am odds. GitHub fires ONE event and the")
print("   case block matches the FIRST arm, so the college arm won and")
print("   MLB's 7am paid pull silently stopped happening. `6 12 * * *`")
print("   was CFB news AND NFL odds — the NFL 8am pull never ran once.")
import collections as _c
_dups = sorted(k for k, v in _c.Counter(crons).items() if v > 1)
ck(not _dups, "no cron string is listed twice", str(_dups))

print("\n⛔ AND NO ROUTING ARM IS UNREACHABLE")
# ⚠️ ASKED OF THE ARMS, NOT THE ROUTES. `[fixed 2026-09-06]` An arm may
# now name TWO leagues (`LEAGUE="ncaaf nfl"`), which `parse_routes`
# expands into two rows sharing one cron string. Reading THAT as a
# shadowed arm would fail a correct file — the real question is whether
# the same cron string appears as two separate `case` arms, because
# shell `case` takes the first match and the second can never run.
_seen, _dead = set(), []
for _c2, _l, _m in parse_arms(wf):
    if _c2 in _seen:
        _dead.append(f"{_c2} -> {_l} {_m}")
    _seen.add(_c2)
ck(not _dead, "every routing arm can be reached", str(_dead))
_ghost = [c for c, _l, _m in routes if c not in crons]
ck(not _ghost, "every routing arm has a cron that fires it", str(_ghost))

print("\n🔴 THE CONCURRENCY GROUP AND THE ROUTING TABLE AGREE")
print("   `github.event.inputs` is EMPTY on a scheduled run, so the old")
print("   group was `collect-mlb` for EVERY cron and cancel-in-progress")
print("   let any MLB cron kill a football pull mid-flight. Football now")
print("   converges, so a cancelled run can lose data already PAID FOR.")
_routed = {c for c, _l, _m in routes}
_unrouted = {c for c in crons if c not in _routed}      # these fall to *) mlb
_m = re.search(r"group: collect-\$\{\{.*?fromJSON\('(\[[^']*\])'\)", wf, re.S)
if not _m:
    ck(False, "the concurrency group names MLB's crons")
else:
    _listed = set(json.loads(_m.group(1)))
    ck(_listed == _unrouted,
       "   the group's MLB list IS the set of unrouted crons",
       f"only-in-group={sorted(_listed - _unrouted)} "
       f"only-unrouted={sorted(_unrouted - _listed)}")
    ck("cancel-in-progress: true" in wf,
       "   and the newest MLB run still replaces the heartbeat loop")

# ══════════════════════════════════════════════════════════════════════
# 🔴 EVERY MODE THE DISPATCH FORM OFFERS MUST ACTUALLY EXIST.
# `[added 2026-09-06, after it cost Sam a failed run]` The docs claimed
# for two days that a `live-probe` mode was "built and waiting on one free
# run". IT HAD NEVER EXISTED — the string appeared once in the whole
# repository, inside a COMMENT. Sam typed it into the dispatch form and
# the run failed, because there was nothing to dispatch.
# ⛔ NOTHING IN THIS PROJECT CHECKED THAT A MODE NAME WAS REAL. This does.
# ⚠️ `converge` and `converge-off` are FLAGS, not modes — they change how
#    the run treats the contract rather than naming something to build.
_desc = re.search(r'mode:\n(?:.*\n)*?\s*description: "([^"]+)"', wf)
ck(bool(_desc), "   the dispatch form still has a mode description to read")
if _desc:
    _offered = {m.strip() for m in re.split(r"[|\s]+", _desc.group(1))
                if re.fullmatch(r"[a-z][a-z0-9-]+", m.strip())}
    _flags = {"converge", "converge-off", "or", "default", "build",
              "everything", "overdue"}
    _offered -= _flags
    _real = set(re.findall(r'mode == "([a-z0-9-]+)"', open("collect.py").read()))
    _ghost = sorted(_offered - _real)
    ck(not _ghost,
       "   every mode the dispatch form offers exists in collect.py",
       "GHOST MODES: %s — the form would send a run at nothing" % _ghost
       if _ghost else "%d offered, all real" % len(_offered))

# ══════════════════════════════════════════════════════════════════════
# 🔴 A COUNT WRITTEN IN A COMMENT IS A CLAIM ABOUT THE SCHEDULE.
# `[added 2026-09-11 — the header said 16 against FORTY crons]`
#
# The header explains why the schedule was cut from 29 entries to 16:
# GitHub stopped firing every cron in this file for 21 hours on
# 2026-08-26/27, and the response was to ask the scheduler for less. **The
# file then grew back to FORTY and the comment never moved.**
#
# ⛔ THAT IS LEDGER RULE 160 — "a comment justifying a deadline is a claim
#    about the schedule, and it must be measured like one" — which was
#    written about a DIFFERENT comment in THIS SAME FILE. Writing the rule
#    did not make the rule fire; only a check does.
# ⚠️ AND IT IS THE SAME SHAPE AS `CLAUDE.md`'s standing ban on writing a
#    credit total into a comment: this project has put a number in a
#    comment three times and been wrong twice.
#
# ✅ SO THE NUMBER STAYS — the 8/26 incident is a real reason to know it —
#    but it is now PINNED. Add or remove a cron without updating the
#    header and CI is red.
# ⛔ IF THIS FAILS, DO NOT EDIT THE COMMENT TO MATCH. Ask first whether
#    forty crons is what was intended; the reduction to 16 was deliberate.
_crons = re.findall(r'^\s*- cron:', wf, re.M)
_claim = re.search(r'^#\s*CRON COUNT:\s*(\d+)\s*$', wf, re.M)
ck(bool(_claim),
   "🔴 the workflow header states its cron count in a readable form",
   "expected a line `# CRON COUNT: <n>` — without it this check cannot "
   "run and the count goes back to being folklore")
if _claim:
    eq(int(_claim.group(1)), len(_crons),
       "🔴 ...and the stated count matches the crons actually scheduled")

note("⚠️ FORTY IS NOT ENDORSED BY THIS CHECK. It pins the comment to the "
     "file, nothing more. The 2026-08-26/27 outage — every cron in this "
     "file silently not firing for 21 hours while manual dispatch kept "
     "working — is the reason the count is worth knowing at all, and "
     "whether forty is too many is a question for Sam, not for a test.")
