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
# ══════════════════════════════════════════════════════════════════════
# `[2026-09-28]` §4 and §5 ask a PLANTED tree pinned to its own clock
# first; the live tree on the real clock is the extra.
# @vacuity §4 planted: every conditional row is governed there (the case exists)
#   file: freshness.py
#   find: if not _props_warranted(league, latest, now):
#   with: if True:
#
# @vacuity §4 planted: a governed mode nothing schedules or drives is an orphan
#   file: freshness.py
#   find: ("card-fb", ("file", f"{latest}/agreement.json"), T["card"], False,
#   with: ("agreement-x", ("file", f"{latest}/agreement.json"), T["card"], False,
#
# @vacuity §4 planted: with every precondition met only diagnostics are ungoverned
#   file: freshness.py
#   find: if not os.path.exists(f"{latest}/props.json.gz"):
#   with: if True:
#
# @vacuity §5 planted: a kickoff inside the window ARMS the props row
#   file: freshness.py
#   find: return any(due <= k <= end for k in ks)
#   with: return False
#
# @vacuity §5 planted: a deadline with no kickoff in its window does NOT
#   file: freshness.py
#   find: return any(due <= k <= end for k in ks)
#   with: return True
#
# @vacuity §5 live: a stored schedule that yields no kickoffs is red
#   file: freshness.py
#   find: for g in doc.get("games") or []:
#   with: for g in []:
# ══════════════════════════════════════════════════════════════════════
import collections
import datetime
import os
import re

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
# 💰 `alt-lines` rides the props pull `[2026-09-24]`; the chain is asserted
#    against collect.py's source in test_game_lines_fb.py.
DRIVEN_BY = {"props-board": "props-player", "fb-record": "card-fb",
             "alt-lines": "props-player"}

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
# 🔴 `[2026-09-28]` A PLANTED TREE FIRST, PINNED TO ITS OWN CLOCK. The live
#    contract on the real clock only governs the props, alt-line and grader
#    rows on a day production warrants them, so on most weekdays losing
#    `alt-lines` from DRIVEN_BY would have passed here and failed on a game
#    day. The planted tree holds a props board, a dated card and a kickoff
#    inside the window of the deadline before PIN: every conditional row is
#    governed, every run. The live tree below is the extra it always was.
import contextlib  # noqa: E402
import gzip        # noqa: E402
import json        # noqa: E402
import shutil      # noqa: E402
import tempfile    # noqa: E402
PIN = datetime.datetime(2026, 9, 19, 20, 0, tzinfo=datetime.timezone.utc)


def _start(lg, t):
    """A kickoff in the league's OWN stored format (freshness.kickoffs_utc):
    college real UTC with a Z; NFL ET wall-clock, no zone (EDT in Sep)."""
    if lg == "ncaaf":
        return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return (t - datetime.timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M")


@contextlib.contextmanager
def planted(lg, kicks, board=True):
    """cwd = a temp tree for `lg`: the kickoffs given, a props board and a
    dated card. ⚠️ cwd: the grader's gate globs `picks/` relative to it."""
    tmp, cwd = tempfile.mkdtemp(), os.getcwd()
    try:
        os.chdir(tmp)
        os.makedirs("data/%s/latest" % lg)
        os.makedirs("picks")
        if board:
            open("data/%s/latest/props.json.gz" % lg, "wb").close()
            open("picks/fb-%s-2026-09-01.json" % lg, "w").close()
        with gzip.open("data/%s/latest/schedule-%d.json.gz"
                       % (lg, F.current_football_season(PIN)), "wt") as fh:
            json.dump({"games": [{"start": _start(lg, k), "home_class": "fbs",
                                  "away_class": "fbs"} for k in kicks]}, fh)
        yield
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmp, ignore_errors=True)


def _orphans(lg, governed):
    out = []
    for m in governed:
        if SCHED[lg].get(m):
            continue
        parent = DRIVEN_BY.get(m)
        if parent and SCHED[lg].get(parent):
            continue
        out.append(m)
    return sorted(out)


_COND ={"props-player", "props-board", "alt-lines", "card-fb", "fb-record"}
for lg in ("ncaaf", "nfl"):
    _k = F.last_due(F.FB_TIMES[lg]["props"], PIN) + datetime.timedelta(hours=2)
    with planted(lg, [_k]):
        _pg = {r[0] for r in F.contract(data="data/%s" % lg, picks="picks",
                                        now=PIN)}
    ck(f"🔴 {lg}: nothing in the contract is left undriven (planted tree, "
       f"every conditional row governed)",
       _COND <= _pg and not _orphans(lg, _pg),
       "missing conditional rows: %s; orphans: %s"
       % (sorted(_COND - _pg), _orphans(lg, _pg)))
    # ✅ AND WITH EVERY PRECONDITION MET, ONLY THE DIAGNOSTICS STAY
    #    UNGOVERNED — the live check below has to excuse PRECONDITIONED
    #    modes; here there is nothing to excuse, so it is asked exactly.
    ck(f"⚠️ {lg}: with every precondition met, ONLY the diagnostics are "
       f"ungoverned (planted tree)",
       set(SCHED[lg]) - _pg == {"live-probe", "halftime-probe"},
       "ungoverned: %s" % sorted(set(SCHED[lg]) - _pg))
gov = {}
for lg in ("ncaaf", "nfl"):
    rows = F.contract(data=f"data/{lg}", picks="picks")
    gov[lg] = {r[0] for r in rows}
    orphan = _orphans(lg, gov[lg])
    ck(f"🔴 {lg}: nothing in the contract is left undriven (live tree)",
       not orphan,
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
# 🔴 ~~`live-probe` is the ONLY permanently ungoverned mode~~ WIDENED
#    2026-09-11, and the widening is deliberate rather than a concession.
#    `halftime-probe` landed on Sam's "probe it" and is the same KIND of
#    thing: a diagnostic that answers a question and writes no artifact
#    the page reads. Naming one probe made the check a check about a
#    STRING; what it was always trying to own is a PROPERTY.
# ⛔ THE SET IS EXPLICIT ON PURPOSE — this is a TRIPWIRE. A new mode must
#    not be able to become ungoverned by accident; adding one here is a
#    deliberate act, and the check below makes it cost something.
# ⚠️ `cfb-probe` IS NOT ON THIS LIST and must never be: it is named like a
#    probe and is not one — it BUILDS THE TRENDS TABLES, is governed, and
#    would be a real gap if it ever went ungoverned. ➡️ Which is exactly
#    why the set is not derived from the name.
DIAGNOSTIC = {"live-probe", "halftime-probe"}
for lg in ("ncaaf", "nfl"):
    _ung = set(SCHED[lg]) - gov[lg]
    ck(f"⚠️ {lg}: only DIAGNOSTIC modes are permanently ungoverned",
       bool(DIAGNOSTIC & _ung) and not (_ung - DIAGNOSTIC - PRECONDITIONED),
       f"ungoverned now: {sorted(_ung)} — "
       f"{sorted(_ung - DIAGNOSTIC) or 'nothing'} waiting on a "
       f"precondition (a props board, or a game inside the window)")
ck("🔴 ...and every one of them is ungoverned for BOTH, not just one",
   all(m in set(SCHED["ncaaf"]) - gov["ncaaf"]
       and m in set(SCHED["nfl"]) - gov["nfl"]
       for m in DIAGNOSTIC if m in SCHED["ncaaf"] or m in SCHED["nfl"]),
   "a diagnostic writes no product artifact, so nothing should govern it "
   "— but it must be the same answer for both leagues")
# 🔴🔴 AND THE PROPERTY, ASSERTED RATHER THAN ASSUMED. Calling a mode a
#    diagnostic is a claim that it writes no product artifact, and until
#    now nothing checked it — `cfb-probe` is the standing proof that the
#    name does not settle the question.
_cs = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
for m in sorted(DIAGNOSTIC):
    # ⛔ THE FUNCTION NAME IS READ OFF THE DISPATCH ARM, NOT GUESSED FROM
    #    THE MODE NAME. The first form of this check derived `probe_live`
    #    from "live-probe" and FAILED ON CORRECT CODE — the function is
    #    actually called `build_live_probe`. A convention is not a fact
    #    (rule 178); the arm that routes the mode is.
    _arm = re.search(r'mode == "%s"\s*:\s*\n(.*?)\n\s*(?:elif |else:)' % m,
                     _cs, re.S)
    # ⛔ MATCH THE ASSIGNED CALL, not the first word with a bracket after
    #    it. The arms are heavily commented and a bare identifier search
    #    reads prose. Every arm ends `left = <fn>()`.
    _call = (re.search(r"=\s*([a-z_][a-z_0-9]*)\(", _arm.group(1))
             if _arm else None)
    _fn = _call.group(1) if _call else ""
    _i = _cs.find("def %s(" % _fn) if _fn else -1
    _body = _cs[_i:_cs.find("\ndef ", _i + 1)] if _i >= 0 else ""
    _writes = re.findall(r'write\(f"\{LATEST\}/([^"]+)"', _body)
    # ⚠️ FOLLOW THE DELEGATION. `build_live_probe()` writes nothing itself
    #    — it shells out to `liveprobe.py`, which writes the file. ⛔ "I
    #    found no write" is not "it writes nothing"; a check that cannot
    #    tell those apart is asking the wrong question.
    _script = re.search(r'\[sys\.executable, "([a-z_0-9]+\.py)"', _body)
    _via = ""
    if _script and os.path.exists(os.path.join(ROOT, _script.group(1))):
        _via = _script.group(1)
        _sub = open(os.path.join(ROOT, _via), encoding="utf-8").read()
        _writes += re.findall(
            r"""['"](?:[A-Za-z0-9_./{}-]*/)?([A-Za-z0-9_.-]+\.json(?:\.gz)?)['"]""",
            _sub)
    ck("🔴 `%s` writes ONLY a probe artifact, and that is checked" % m,
       bool(_body) and bool(_writes)
       and all("probe" in w for w in _writes),
       "⛔ a mode that writes a file the page reads is NOT a diagnostic "
       "and must be governed like everything else. %s()%s writes: %s"
       % (_fn or "?", (" via " + _via) if _via else "",
          _writes or "nothing found — did the dispatch arm change?"))

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
#    SCHEDULE. Nothing here is an offset anyone chose, so ~~the season
#    moving on cannot falsify it (rule 166)~~ — it could: the file is
#    named by the real clock's season (see the planted case below).
# 🔴 `[2026-09-28]` THE PLANTED CASE FIRST, AND THE TREE AND ITS CLOCK
#    ARE PINNED TOGETHER. The live derivation below needs the CURRENT
#    season's schedule, and the season comes from the real clock: from
#    1 August each year it names a file the collector has not written yet,
#    and this section went red on correct code (or, lacking both states,
#    ran nothing). ✅ One planted Sunday kickoff: the Sunday 11am-ET
#    deadline's window holds it, ~~Friday's~~ Thursday's does not (74 hours
#    out, past the NFL next-slate 72, `[Sam, 2026-10-09]`). Asked every run.
_pk = datetime.datetime(2026, 9, 20, 17, 0, tzinfo=datetime.timezone.utc)
_pa = datetime.datetime(2026, 9, 20, 15, 1, tzinfo=datetime.timezone.utc)
_pq = datetime.datetime(2026, 9, 17, 15, 1, tzinfo=datetime.timezone.utc)   # 74h out: past the NFL next-slate 72h
with planted("nfl", [_pk], board=False):
    _m_pa = {r[0] for r in F.contract(data="data/nfl", picks="picks", now=_pa)}
    _m_pq = {r[0] for r in F.contract(data="data/nfl", picks="picks", now=_pq)}
ck("🔴 a deadline with a kickoff inside its window ARMS the props row "
   "(planted)", "props-player" in _m_pa,
   "⛔ the contract must govern a pull that WOULD buy something. %s"
   % sorted(_m_pa))
ck("⛔ ...and a deadline with NO kickoff inside it does NOT (planted)",
   "props-player" not in _m_pq,
   "🔴 RULE 86 — a pull that would buy nothing is not a late pull. %s"
   % sorted(_m_pq))
ck("✅ the two planted probes really are different states, not the same one twice",
   ("props-player" in _m_pa) != ("props-player" in _m_pq),
   "⛔ RULE 202 — a check that cannot tell its two cases apart is not the check it "
   "claims to be")
# `[Sam, 2026-10-09]` ~~THE LIVE SCHEDULE'S DERIVED PROBES (the extra)~~: "No new or
#    changed test may read the live data tree" (collect went red for a day on two that
#    did, #251/#252). The planted probes above ask the same three questions, armed,
#    quiet and different, at the NFL rule: the next slate within 72 hours.
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

# ══════════════════════════════════════════════════════════════════════
print("\n═══ 7. 🔴 THE TWO BUILDERS MUST MEASURE THE SAME THINGS ═══")
# 🔴 "EVERYTHING WE DO FOR CFB WE DO FOR NFL" IS A HABIT UNTIL SOMETHING
#    CHECKS IT. Section 6 above owns the SCHEDULE half — is each tab
#    driven for both leagues. This owns the CONTENT half: `cfb.py` and
#    `nfl.py` each build a trends table that ONE PAGE reads, so a column
#    added to one and forgotten in the other gives a reader two tables
#    that look alike and are not.
# ⚠️ IT HAS ALREADY HAPPENED TWICE IN TWO DAYS, and both times the miss
#    was caught by hand rather than by a check:
#      2026-09-11  total_yds added to cfb.py, then to nfl.py separately
#      2026-09-11  total_td   added to both in one edit ONLY because the
#                  first miss was fresh in mind
# ⛔ THE FAILURE IS SILENT. Nothing goes red — the NFL table simply has
#    one fewer column, the picker offers one fewer metric, and the page
#    renders perfectly.
_src = {f: open(os.path.join(ROOT, f), encoding="utf-8").read()
        for f in ("cfb.py", "nfl.py")}


def _tuple_after(src, name):
    """The literal tuple assigned to `name`, as a list of its strings.

    ⛔ READ THE ASSIGNMENT, NOT THE FILE. Both builders quote these field
    names in prose comments; a bare findall over the source would count
    the documentation.
    """
    m = re.search(r"^%s\s*=\s*\((.*?)\)\s*$" % name, src, re.S | re.M)
    return re.findall(r'"([a-z_]+)"', m.group(1)) if m else None


for name in ("DEF_FIELDS", "YARD_PARTS", "TD_PARTS"):
    a, b = _tuple_after(_src["cfb.py"], name), _tuple_after(_src["nfl.py"], name)
    ck("🔴 cfb.py and nfl.py define %s identically" % name,
       a is not None and a == b,
       "⛔ one page reads both leagues' files, so a column that means "
       "something different in each — or exists in only one — is worse "
       "than a missing column, because nothing looks wrong.\n"
       "     cfb: %s\n     nfl: %s" % (a, b))

# ⛔ AND THE DERIVED LIST, WHICH IS WHAT ACTUALLY REACHES THE FILE.
#    Asserting the parts match is not asserting the OUTPUT matches: the
#    two files could assemble the same parts into different RANK_FIELDS.
_rf = {f: re.search(r"^RANK_FIELDS\s*=\s*(.+)$", s, re.M) for f, s in _src.items()}
ck("🔴 ...and RANK_FIELDS is assembled the same way in both",
   all(_rf.values()) and (_rf["cfb.py"].group(1).strip()
                          == _rf["nfl.py"].group(1).strip()),
   "the parts matching does not mean the assembled list does. cfb: %s | "
   "nfl: %s" % (_rf["cfb.py"] and _rf["cfb.py"].group(1),
                _rf["nfl.py"] and _rf["nfl.py"].group(1)))

# 🔴🔴 AND THE PAGE'S METRIC LIST MUST NOT OFFER A COLUMN NEITHER BUILDER
#    WRITES. ⛔ The picker filters to what the LOADED file carries, so a
#    stray key here is invisible until the day a file happens to have it.
_html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
_arr = _html[_html.index("const FB_METRICS = ["):]
_arr = _arr[:_arr.index("\n];")]
_keys = set(re.findall(r"\{\s*k\s*:\s*'([a-z_]+)'", _arr))
_built = set(_tuple_after(_src["cfb.py"], "DEF_FIELDS") or []) | {
    "total_yds", "total_td"}
ck("⛔ every metric the picker offers is one a builder actually writes",
   _keys <= _built,
   "a key no builder writes can never appear and is dead weight the "
   "reader cannot see. Orphans: %s" % sorted(_keys - _built))

# ⚠️ REPORTED, NOT ASSERTED — AND THIS IS THE GAP THE CHECKS ABOVE CANNOT
#    CLOSE. The builders agreeing is a fact about the CODE. What reaches
#    the page is the last file each builder WROTE, and the two rebuild on
#    very different cadences:
#        cfb-probe   "4 7 * * *"      DAILY, 3:04am ET
#        nfl-logs    "6 16 * * 2"     WEEKLY, Tue 12:06pm ET
#    ⛔ So a column added to both builders on a Wednesday is on the
#    college table the next morning and on the NFL table SIX DAYS LATER.
#    ➡️ Both modes are FREE. The cadence is not a cost decision.
for lg, stem in (("ncaaf", "allowed"), ("nfl", "allowed")):
    p = os.path.join(ROOT, "data", lg, "latest", "%s-by-position-2026.json.gz"
                     % stem)
    if not os.path.exists(p):
        continue
    import gzip  # noqa: E402
    d = json.load(gzip.open(p, "rt"))
    rows = d.get("defences") or d.get("offences") or {}
    cols = set()
    for t in rows.values():
        for pos in t.values():
            cols |= set(pos)
            break
        break
    note("%-6s table stamped %s — total_yds %s · total_td %s"
         % (lg, d.get("built_at") or d.get("written_at"),
            "total_yds" in cols, "total_td" in cols))
note("⛔ A DIFFERENCE ABOVE IS NOT A DEFECT IN THE CODE — it is the "
     "rebuild lag, and it closes on its own. It is REPORTED rather than "
     "asserted because asserting it would go red for days at a time on "
     "correct code (rule 166).")

# ══════════════════════════════════════════════════════════════════════
# 🔴 BUT THE CADENCE ITSELF IS ASSERTABLE, AND NOW IS.
# ⛔ The TABLES differing is a fact about today and cannot be asserted.
#    The SCHEDULE differing is a fact about the repo and can be — which
#    is the half of rule 224 that was fixable.
# ⚠️ `[measured 2026-09-12]` `cfb-probe` ran DAILY and `nfl-logs` ran
#    ONCE A WEEK, both free, so identical builder code reached the two
#    tables up to SIX DAYS apart. Sam's standing rule is that everything
#    done for CFB is done for NFL; that was true of the code and false of
#    the schedule.
# ⛔ ASSERTED ON "HAS A DAILY CRON", NOT ON A CRON COUNT. Counting crons
#    would go red the next time either league gains a backup slot, which
#    is a change with nothing wrong in it.
# 🔴🔴 READ THE `- cron:` DECLARATIONS, NOT ONLY THE ROUTING ARMS.
#    `SCHED` is built from the routing `case` arms, and the first form of
#    this check asked it alone — so DELETING THE CRON DECLARATION AND
#    LEAVING THE ARM STILL PASSED. ⛔ An arm with no declaration behind it
#    is a dead arm: nothing ever fires it, and the schedule is silently
#    one cron shorter. That is the stale-root-`collect.yml` family of bug
#    (rule 209) in miniature, and it took deleting the line to find.
# ✅ A cron now counts only if it is BOTH declared AND routed.
_decl = set(re.findall(r'^\s*- cron:\s*"([^"]+)"',
                      open(WF, encoding="utf-8").read(), re.M))
_daily = {}
for lg, mode in (("ncaaf", "cfb-probe"), ("nfl", "nfl-logs")):
    _daily[lg] = [c for c in SCHED[lg].get(mode, [])
                  if c in _decl
                  and c.split()[2] == "*" and c.split()[4] == "*"]
ck("🔴 BOTH trends builders have a DAILY cron, DECLARED and ROUTED",
   all(_daily.values()),
   "⛔ a builder change reaches the page only when that builder next "
   "runs. Both modes are FREE, so a weekly rebuild beside a daily one "
   "was not a cost decision — it was an oversight. Daily crons found: "
   "%s" % _daily)
note("⚠️ THE WEEKLY DEADLINE IS UNTOUCHED AND MUST STAY. nflverse "
     "publishes weekly, so a DAILY DEADLINE would be one nothing could "
     "satisfy (rule 112). ⛔ A cron is a chance to land; a deadline is a "
     "promise. Running more often cannot make anything late.")
