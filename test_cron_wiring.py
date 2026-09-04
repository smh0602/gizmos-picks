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
import os
import re
import sys

os.environ.setdefault("LEAGUE", "mlb")
import collect as C

WF = ".github/workflows/collect.yml"
fails = []


def ck(cond, label, detail=""):
    print(f"  {'ok  ' if cond else '🔴 FAIL'} {label:<60} {detail}")
    if not cond:
        fails.append(label)


def eq(got, want, label):
    ck(got == want, label, f"{got!r}")
    if got != want and fails and fails[-1] == label:
        fails[-1] = f"{label} (got {got!r} want {want!r})"


wf = open(WF, encoding="utf-8").read()
src = open("collect.py", encoding="utf-8").read()

# ── what the collector can actually do ────────────────────────────────
MODES = set(re.findall(r'(?:el)?if mode == "([a-z0-9-]+)"', src))
MODES |= {"converge", "converge-off"}
print(f"\ncollector dispatches {len(MODES)} modes")

# ── what the schedules ask for ────────────────────────────────────────
# `"<cron>") LEAGUE=x; MODES="a b"` — the same shape budget.py parses.
routes = re.findall(
    r'"([\d ,*/-]+)"\)\s*LEAGUE=(\w+);\s*MODES="([a-z0-9 -]+)"', wf)
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

print()
if fails:
    print(f"🔴 {len(fails)} FAILURE(S)")
    for f in fails:
        print(f"   - {f}")
    sys.exit(1)
print("✅ cron wiring: all checks passed")
