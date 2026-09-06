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
first = None
try:
    import json
    B = json.load(open("data/nfl/latest/board.json", encoding="utf-8"))
    first = sorted(g["commence"] for g in (B.get("games") or [])
                   if g.get("commence"))[0]
except Exception:
    pass
ck("the NFL board names a first kickoff to reason from", bool(first),
   str(first))
if first:
    k = datetime.datetime.fromisoformat(first.replace("Z", "+00:00"))
    before = F.contract(data="data/nfl", picks="picks",
                        now=k - datetime.timedelta(days=3))
    inside = F.contract(data="data/nfl", picks="picks",
                        now=k - datetime.timedelta(hours=13))
    mb, mi = {r[0] for r in before}, {r[0] for r in inside}
    ck("⛔ three days out, the NFL props row is correctly ABSENT",
       "props-player" not in mb,
       "a pull that would buy nothing is not late (rule 86)")
    ck("🔴 thirteen hours out — inside the window — it ARMS ITSELF",
       "props-player" in mi, sorted(mi))
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
