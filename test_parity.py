#!/usr/bin/env python3
"""
🔴 NFL/CFB PARITY, MACHINE-CHECKED — Sam's standing rule, made permanent.

Sam, 2026-09-06: *"verify and test that we have all appropriate recurring
runs and that we have the same recurring tasks for the nfl tabs as well as
the cfb ones"*, and earlier: *"everything we do for cfb we do for nfl and
vice versa."*

⛔ THIS IS THE CHECK, NOT THE AUDIT. An audit is a paragraph somebody read
once; this fails the run the day the two leagues drift apart. Every number
is read from the workflow and the contract themselves, never from a doc —
this project has already paid for restating a doc's claim (rule 120).

THE TWO ASYMMETRIES ARE NAMED, JUSTIFIED AND CHECKED AGAINST THE DATA:
  cfb-probe / nfl-logs   the SAME tab (Trends) built from different feeds.
                         nflverse publishes WEEKLY, so a daily NFL deadline
                         would be one nothing could satisfy.
  cfb-teams / (none)     the 32 NFL crests are a hard-coded map in the
                         page; college fetches 138 school logo URLs from
                         CFBD because realignment moves them every year.
⛔ ANYTHING ELSE THAT DIVERGES IS A BUG, and this file says so by name.
"""
import collections
import datetime
import os

import freshness as F
from jsblock import source
from tcheck import ck, note
from wfroutes import parse_routes

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
WF = ".github/workflows/collect.yml"
ROUTES = parse_routes(open(WF, encoding="utf-8").read())

SCHED = collections.defaultdict(lambda: collections.defaultdict(list))
for cron, lg, modes in ROUTES:
    for md in modes.split():
        SCHED[lg][md].append(cron)

# ⛔ THE ONLY PERMITTED DIVERGENCES, each with the fact that justifies it.
PAIRED = {"cfb-probe": "nfl-logs"}          # the same tab, two feeds
CFB_ONLY = {"cfb-teams"}                    # NFL crests are embedded
# ⚠️ A mode that is chained rather than scheduled is driven by its parent.
DRIVEN_BY = {"props-board": "props-player", "fb-record": "card-fb"}

print("\n═══ 1. EVERY FOOTBALL MODE IS ROUTED FOR BOTH LEAGUES ═══")
c, n = set(SCHED["ncaaf"]), set(SCHED["nfl"])
ck("both football leagues are routed at all", bool(c) and bool(n),
   f"ncaaf {len(c)} modes, nfl {len(n)} modes")
c_only = sorted(c - n - CFB_ONLY - set(PAIRED))
n_only = sorted(n - c - set(PAIRED.values()))
ck("🔴 no mode is scheduled for COLLEGE and not the NFL", not c_only,
   str(c_only) or "none beyond the named pair and cfb-teams")
ck("🔴 no mode is scheduled for the NFL and not COLLEGE", not n_only,
   str(n_only) or "none beyond the named pair")
for a, b in PAIRED.items():
    ck(f"the paired Trends builders are both scheduled ({a} / {b})",
       a in c and b in n, f"ncaaf has {a}: {a in c}; nfl has {b}: {b in n}")
for m in CFB_ONLY:
    ck(f"⚠️ {m} is college-only, and the reason is IN THE PAGE",
       m in c and m not in n and "const NFL_LOGOS" in source("index.html"),
       "the 32 NFL crests are a hard-coded map; college fetches 138 "
       "school logo URLs because realignment moves them every year")

print("\n═══ 2. THE SHARED MODES RUN AS OFTEN FOR ONE AS THE OTHER ═══")
shared = sorted((c & n) - set(PAIRED) - set(PAIRED.values()))
ck("there are shared modes to compare", len(shared) >= 5, str(shared))
uneven = [(m, len(SCHED["ncaaf"][m]), len(SCHED["nfl"][m]))
          for m in shared
          if len(SCHED["ncaaf"][m]) != len(SCHED["nfl"][m])]
ck("🔴 every shared mode has the SAME number of crons in both leagues",
   not uneven, str(uneven) or f"{len(shared)} shared modes, all equal")
for m in shared:
    note(f"{m}: {len(SCHED['ncaaf'][m])} cron(s) each — "
         f"{sorted(set(SCHED['ncaaf'][m]) & set(SCHED['nfl'][m]))[:3]}"
         + (" …" if len(SCHED["ncaaf"][m]) > 3 else ""))

print("\n═══ 3. ⚠️ WHERE THEY DIFFER, THE DATA SAYS WHY ═══")
T = F.FB_TIMES
nfl_tr = T["nfl"]["trends"]
cfb_tr = T["ncaaf"]["trends"]
ck("college Trends is daily and the NFL's is weekly",
   len(cfb_tr) >= 1 and all(len(d) == 2 for d in cfb_tr)
   and any(len(d) == 3 for d in nfl_tr),
   f"ncaaf {cfb_tr} · nfl {nfl_tr}")
ck("⛔ ...and the NFL's source really is weekly, per the collector",
   "weekly player stats" in open("nfl.py", encoding="utf-8").read(),
   "a daily NFL deadline would be one nothing could ever satisfy "
   "(rule 112) — this is a data fact, not a gap")

print("\n═══ 4. EVERY GOVERNED ARTIFACT HAS SOMETHING DRIVING IT ═══")
gov = {}
for lg in ("ncaaf", "nfl"):
    rows = F.contract(data=f"data/{lg}", picks="picks")
    gov[lg] = {r[0] for r in rows}
    orphan = []
    for m in gov[lg]:
        if SCHED[lg].get(m):
            continue
        parent = DRIVEN_BY.get(m)
        if parent and SCHED[lg].get(parent):
            continue
        orphan.append(m)
    ck(f"🔴 {lg}: nothing in the contract is left undriven", not orphan,
       str(orphan) or f"{len(gov[lg])} governed artifact(s), all driven")
    extra = sorted(set(SCHED[lg]) - gov[lg])
    note(f"{lg}: scheduled but not governed — {extra or 'none'}")
# 🔴 THE HONEST FORM OF THIS CHECK, AFTER TWO WRONG ONES.
#    v1 compared the two leagues TODAY and failed: the NFL's card-fb and
#    props-player are correctly ungoverned because no NFL game is inside
#    the window (rule 86). v2 compared them 13h before the NFL opener and
#    ALSO failed — at that instant college has no game in its window
#    either, so each league is at a different point in its OWN arming
#    sequence. ⛔ EQUALITY AT A SINGLE MOMENT IS THE WRONG TEST: it
#    measures the calendar, not the parity.
#    ✅ What must be true of both is the SHAPE: exactly one mode is
#    permanently ungoverned — the diagnostic that writes no product
#    artifact — and everything else ungoverned is waiting on a stated
#    precondition.
PRECONDITIONED = {"props-player", "props-board", "card-fb", "fb-record"}
for lg in ("ncaaf", "nfl"):
    _ung = set(SCHED[lg]) - gov[lg]
    ck(f"⚠️ {lg}: `live-probe` is the only PERMANENTLY ungoverned mode",
       "live-probe" in _ung and not (_ung - {"live-probe"} - PRECONDITIONED),
       f"ungoverned now: {sorted(_ung)} — "
       f"{sorted(_ung - {'live-probe'}) or 'nothing'} waiting on a "
       f"precondition (a props board, or a game inside the window)")
ck("🔴 ...and it is ungoverned for BOTH, not just one",
   ("live-probe" in set(SCHED["ncaaf"]) - gov["ncaaf"])
   and ("live-probe" in set(SCHED["nfl"]) - gov["nfl"]),
   "a diagnostic writes no product artifact, so nothing should govern it "
   "— but it must be the same answer for both leagues")

print("\n═══ 5. 🔴 THE NFL ARMS INTO THE SAME CONTRACT COLLEGE HAS ═══")
# ⛔ MEASURED BY MOVING THE CLOCK, not asserted. The NFL's props rows are
#    absent today because no NFL game kicks off inside the window — rule
#    86, an artifact that cannot exist yet is not late. They must appear
#    the moment one does.
# 🔴 ~~PROBED AT FIXED OFFSETS FROM THE FIRST KICKOFF (−3d and −13h).~~
#    STRUCK 2026-09-11 — IT WENT RED ON CORRECT CODE, AND THE REASON IS
#    THE CHECK'S OWN ARITHMETIC. ⛔ The window is anchored to the props
#    DEADLINE, not to the kickoff: `_props_warranted` asks whether a
#    kickoff falls inside `[last_due(now), last_due(now) + 14h]`. So an
#    offset measured from a KICKOFF lands wherever the deadline grid
#    happens to put it, and it happened to work exactly once.
#    `[measured 2026-09-11]` −3d from Sunday's 17:00Z kickoff is Thursday
#    17:00Z, whose 15:00Z deadline has **Thursday Night Football at
#    00:35Z inside its window** -> warranted, not absent. And −13h is
#    Sunday 04:00Z, whose last deadline was SATURDAY 15:00Z, 26 hours
#    before kickoff -> nothing inside 14h -> not armed.
#    ➡️ **BOTH ASSERTIONS WERE BACKWARDS, AND THE CODE WAS RIGHT.**
# ✅ SO THE PROBES ARE DERIVED FROM THE DEADLINE GRID AND THE REAL
#    SCHEDULE. Nothing here is an offset anyone chose, so the season
#    moving on cannot falsify it (rule 166).
import json  # noqa: E402
LAT = "data/nfl/latest"
try:
    _ks = F.kickoffs_utc("nfl", "%s/schedule-%s.json.gz"
                         % (LAT, F.current_football_season(None)))
except Exception:
    _ks = None
ck("the NFL schedule names kickoffs to reason from", bool(_ks),
   "%s kickoff(s)" % (len(_ks) if _ks else 0))

_armed = _quiet = None
if _ks:
    _t0 = min(_ks) - datetime.timedelta(days=2)
    for _d in range(0, 30):
        for _hh, _mm in F.FB_TIMES["nfl"]["props"][:2]:
            _probe = (_t0 + datetime.timedelta(days=_d)).replace(
                hour=0, minute=0, second=0, microsecond=0) \
                + datetime.timedelta(hours=_hh + 5, minutes=_mm + 1)
            _due = F.last_due(F.FB_TIMES["nfl"]["props"], _probe)
            if _due is None:
                continue
            _end = _due + datetime.timedelta(hours=F.FB_PROPS_WINDOW_H)
            _hit = any(_due <= k <= _end for k in _ks)
            if _hit and _armed is None:
                _armed = _probe
            if not _hit and _quiet is None:
                _quiet = _probe
        if _armed and _quiet:
            break

if _armed and _quiet:
    note("probes DERIVED: armed=%s · quiet=%s (window %sh from the "
         "deadline that just passed)"
         % (_armed.isoformat(), _quiet.isoformat(), F.FB_PROPS_WINDOW_H))
    m_armed = {r[0] for r in F.contract(data="data/nfl", picks="picks",
                                        now=_armed)}
    m_quiet = {r[0] for r in F.contract(data="data/nfl", picks="picks",
                                        now=_quiet)}
    ck("🔴 a deadline with a kickoff inside its window ARMS the props row",
       "props-player" in m_armed,
       "⛔ the contract must govern a pull that WOULD buy something. %s"
       % sorted(m_armed))
    ck("⛔ ...and a deadline with NO kickoff inside it does NOT",
       "props-player" not in m_quiet,
       "🔴 RULE 86 — a pull that would buy nothing is not a late pull, "
       "and marking it late asks for a repair no run can make. %s"
       % sorted(m_quiet))
    ck("✅ the two probes really are different states, not the same one twice",
       ("props-player" in m_armed) != ("props-player" in m_quiet),
       "⛔ RULE 202 — a check that cannot tell its two cases apart is not "
       "the check it claims to be")
else:
    # ⚠️ NOT EXERCISED, AND SAID OUT LOUD. A check that quietly stops
    #    running is the same false cover as a test the runner never
    #    discovers (rule 182).
    note("⚠️ NOT EXERCISED — the stored schedule does not contain both an "
         "armed and a quiet deadline in the probed range. armed=%s "
         "quiet=%s" % (_armed, _quiet))
ck("...and nobody has to do anything for that to happen",
   "props-player" in SCHED["nfl"],
   "the crons already exist; only the contract row was waiting")

print("\n═══ 6. THE TAB-BY-TAB ANSWER ═══")
TABS = [("Scores & Matchups", "fb-scores"), ("Odds", "gamelines"),
        ("Player Props", "props-player"), ("Gizmo's Picks", "card-fb"),
        ("Parlays", "card-fb"), ("Track Record", "fb-record"),
        ("News", "news"), ("Trends", None)]
missing = []
for tab, mode in TABS:
    if mode is None:
        note(f"{tab:20s} ncaaf cfb-probe ({len(SCHED['ncaaf']['cfb-probe'])} cron) "
             f"· nfl nfl-logs ({len(SCHED['nfl']['nfl-logs'])} cron) — paired")
        continue
    a = len(SCHED["ncaaf"].get(mode, [])) or (
        len(SCHED["ncaaf"].get(DRIVEN_BY.get(mode, ""), [])))
    b = len(SCHED["nfl"].get(mode, [])) or (
        len(SCHED["nfl"].get(DRIVEN_BY.get(mode, ""), [])))
    note(f"{tab:20s} {mode:14s} ncaaf {a} cron(s) · nfl {b} cron(s)")
    if a == 0 or b == 0 or a != b:
        missing.append((tab, mode, a, b))
ck("🔴 EVERY TAB IS DRIVEN FOR BOTH LEAGUES, AT THE SAME CADENCE",
   not missing, str(missing) or "8 tabs, both leagues, equal")
