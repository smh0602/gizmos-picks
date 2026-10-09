#!/usr/bin/env python3
"""
THE DOSSIER IS A REPORT, AND A REPORT THAT MOVES A NUMBER IS A MODEL.

🔴 THE CHECK THAT MATTERS MOST IS THE THIRD ONE: a card built with this
file present must be BYTE-IDENTICAL to a card built without it. Not "I
did not import it" — the cards, diffed. `card_fb.py` is what Sam bets
from, and the licence for adding a tool beside it is that the tool cannot
reach it.

⚠️ AND EVERY SECTION MUST BE THERE. An absent section is
indistinguishable from a section that found nothing — the `own_mean`
shape, which sat at 0 of 200 graded rows while the cards carried it on
all 339 and nothing said so.

⛔ NEVER IN THE PRODUCT TREE. The builder writes
`data/<league>/latest/dossiers.json.gz`, so every run here happens in a
throwaway copy; `tcheck` fails any test that leaves a file under `data/`
changed, and it is right to.

🔴 EVERY CASE IS PLANTED, NEVER WAITED FOR. `[2026-09-28]` The sweeps
below used to run over the LIVE board alone, so a Monday with 7 games
(mostly finished) turned "the real board has games to describe" red on
correct code, a board with no rematch turned the prior-meeting check red,
and an empty board killed the file at its first fixture. ✅ Every tree now
carries real schedule games PLANTED at the front of its board (`plant()`,
the #156 shape), so each check has its case on any day; the live games
stay behind them, and a check about the live slate alone is an EXTRA that
asserts only when the live board holds the case and is a note() otherwise.
⛔ AND NOTHING HERE TOUCHES THE NETWORK. `collect.py` runs pass
`converge-off` with blank keys and a socket blocker, and a check fails if
any attempt was made.
"""
import atexit
import ast
import datetime
import glob
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, note, section, copy_module

ROOT = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════════════
# @vacuity every board game gets a dossier, or is NAMED as skipped
#   file: dossier_fb.py
#   find: skipped.append(_skip(g, "neither team name is in the code table"))
#   with: pass  # the skip is dropped instead of named
#
# @vacuity all EIGHT sections are written for every game
#   file: dossier_fb.py
#   find: s_personnel(teams, players, this_season, missing, week, lg),
#   with: # s_personnel(teams, players, this_season, missing, week, lg),
#
# @vacuity section 6 answers from the stored table, and never denies it is there
#   file: dossier_fb.py
#   find:     if not top:
#   with:     if True:
#
# @vacuity a section that cannot answer says UNAVAILABLE, never vanishes
#   file: dossier_fb.py
#   find: d = {"n": n, "name": name, "state": "UNAVAILABLE", "basis": None,
#   with: d = {"n": n, "name": name, "state": "OK", "basis": None,
#
# @vacuity the vs-position rank NEVER travels without its measured verdict
#   file: dossier_fb.py
#   find: "verdict": VS_VERDICT,
#   with: "verdict": "",
#
# @vacuity a verdict field must never reach the published file
#   file: dossier_fb.py
#   find: "sections": [
#   with: "score": 0.73, "confidence": 88, "sections": [
#
# @vacuity a venue is never invented when the schedule has no row
#   file: dossier_fb.py
#   find: if not sched_row:
#   with: if not (sched_row := sched_row or {"venue": home, "roof": "outdoors"}):
#   ⚠️ `[2026-09-28]` ~~`sched_row = sched_row or {...}`~~ left the
#      indented `return` under it and landed as an IndentationError: the
#      builder could not start, so this went red for the WRONG reason. The
#      walrus invents the row AND keeps the line a valid `if`.
#
# @vacuity a week is PLACED by the calendar or refused, never guessed
#   find: return {d: next(iter(w)) for d, w in seen.items() if len(w) == 1}
#   file: dossier_fb.py
#   with: return {d: 1 for d in seen}
#
# @vacuity an ambiguous schedule key REFUSES, it does not pick the first
#   file: dossier_fb.py
#   find: sideidx.setdefault((side, x[side], d), []).append(x)
#   with: sideidx[(side, x[side], d)] = [x]
#
# @vacuity no section asks the ENVIRONMENT which league it is describing
#   file: dossier_fb.py
#   find: _lg = os.path.basename((data or DATA).rstrip(os.sep)).strip().lower()
#   with: _lg = (LEAGUE or "nfl").strip().lower()  # the environment
#
# @vacuity a section comparing two sides REFUSES when one does not resolve
#   file: dossier_fb.py
#   find: return no_opponent(5, "Versus position", missing)
#   with: pass  # fall through — a null opponent reaches an OK section
#
# @vacuity the audit REFUSES to write, it does not merely warn
#   file: dossier_fb.py
#   find: if bad:
#   with: if bad and False:
#
# @vacuity the carried-subtree list cannot be padded to hide a verdict
#   file: dossier_fb.py
#   find: CARRIED = ("live", "closing", "meetings", "by_team", "by_player",
#   with: CARRIED = ("sections", "live", "closing", "meetings", "by_team", "by_player",
#
# @vacuity the dossier must be CHAINED to a mode a cron actually routes to
#   file: collect.py
#   find: _rc = _dos.build(LEAGUE)
#   with: _rc = 0  # _dos.build(LEAGUE)
#
# ⚠️ THE TWO ARCHIVE MUTATIONS NOW POINT AT `daystore.py`, because the
#    writer MOVED there on 2026-09-17 so `shadow_fb.py` could share it
#    (rule 117). ⛔ The QUESTIONS are unchanged and they are still asked
#    from here, driving the dossier's own archive — what moved is the
#    line the mutation lands on. The harness said MALFORMED the moment
#    the old `find` stopped matching, which is exactly its job.
# @vacuity the dossier is ARCHIVED to a dated path, not only to latest/
#   file: daystore.py
#   find: if os.path.exists(p):
#   with: if True:
#
# @vacuity the dated archive is WRITE-ONCE and a later run cannot rewrite it
#   file: daystore.py
#   find: return p, False
#   with: pass   # fall through and OVERWRITE the earlier reading
#   ⚠️ ...and it mutates the EARLY RETURN, not the write. Gutting the
#      write would make "the archive exists" fail — a different question
#      going red for a different reason. Removing the return is what
#      breaks write-once and nothing else.
#
# @vacuity nothing in the dossier is ever labelled MODEL
#   file: dossier_fb.py
#   find: MARKET, DESC = "MARKET", "DESCRIPTIVE"
#   with: MARKET, DESC = "MARKET", "MODEL"
#
# ── `[2026-09-28]` THE PLANTED CASES, EACH WITH ITS OWN MUTATION ─────────
# @vacuity the board under test always has planted games, and a builder that describes none is caught
#   file: dossier_fb.py
#   find: for g in (board.get("games") or []):
#   with: for g in (board.get("games") or [])[:0]:
#
# @vacuity the fixture reads the builder's own team table, and an empty table is caught before any sweep
#   file: dossier_fb.py
#   find: return dict(ast.literal_eval(n.value))
#   with: return {}
#
# @vacuity an UNAVAILABLE section always says why, on the planted game that is always UNAVAILABLE somewhere
#   file: dossier_fb.py
#   find: d = {"n": n, "name": name, "state": "UNAVAILABLE", "basis": None,
#   with: d = {"n": n, "name": name, "state": "UNAVAILABLE", "basis": None, "why": ""} or {
#
# @vacuity the card diff compares FRESH cards built from a planted props board, never frozen copies
#   file: card_fb.py
#   find: conf = (H + K_PRIOR * p0) / (N + K_PRIOR)
#   with: conf = (H + K_PRIOR * p0) / (N + K_PRIOR) - (0.01 if __import__("glob").glob("do*_fb.py") else 0)
#   ⚠️ The replacement must not SPELL the file's name: "card_fb.py does not
#      mention the dossier" would go red on the text alone and the sweep
#      would read BITES whether or not the diff saw anything — which is
#      how this mutation first passed while the WITHOUT tree held the file.
#
# @vacuity at least one vs-position section answers, so the verdict phrases are never checked over nothing
#   file: dossier_fb.py
#   find: j = allowed.get(this_season) or allowed.get(this_season - 1)
#   with: j = None
#
# @vacuity the planted prior meeting carries the score that happened, by value
#   file: dossier_fb.py
#   find: "home_score": x.get("home_score"),
#   with: "home_score": None,
#
# @vacuity a game neither team has an earlier possession row for still names a remedy
#   file: dossier_fb.py
#   find: "it fills in once the season's log build stores a "
#   with: None and "it fills in once the season's log build stores a "
#
# @vacuity every carried-subtree exemption appears on the PLANTED slate, so padding is caught on any day
#   file: dossier_fb.py
#   find: CARRIED = ("live", "closing", "meetings", "by_team", "by_player",
#   with: CARRIED = ("junk_subtree", "live", "closing", "meetings", "by_team", "by_player",
#
# @vacuity `card-fb` runs ALONE here: no converge pass, so no other mode, no network and no paid pull
#   file: collect.py
#   find: if "converge-off" in args or not _fresh.has_contract(LEAGUE):
#   with: if not _fresh.has_contract(LEAGUE):
# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# ⛔ THE ARTIFACT UNDER TEST IS STRIPPED FROM THE THROWAWAY TREE.
# 🔴🔴 A PRECONDITION THAT WAS TRUE ONLY UNTIL THE FEATURE STARTED
# WORKING, `[2026-09-17]`. The gate check below injects a `score` into a
# copy of the builder, runs it, and asserts it "wrote nothing at all" —
# by testing that `latest/dossiers.json.gz` does not exist. That was
# right while the dossier had never been published. The moment `card-fb`
# started publishing one, `copytree` brought it into every throwaway
# tree, and the check went red **because the thing it guards had
# succeeded.** The suite was red on main on every collector run after.
# ✅ STRIPPING IT ASKS THE SAME QUESTION AND ASKS IT HARDER: "this run
# wrote nothing" instead of "the fixture happened not to have one".
# ⛔ Do not answer this by deleting the assertion — a refusal that still
# published the file would then pass.
# ══════════════════════════════════════════════════════════════════════
PRODUCED = ("data/nfl/latest/dossiers.json.gz",
            "data/nfl/latest/t54.json")


_TEAM_OUT_PATCHED = {}      # players file name -> patched gz bytes, or None

# ⚠️ THE BUILDER'S OWN MODULE, imported once for its team table
#    (`nfl_table`, rule 117) and its declared section count.
import dossier_fb as _DFX  # noqa: E402

# ══════════════════════════════════════════════════════════════════════
# 🧹 EVERY THROWAWAY TREE THIS FILE MAKES LIVES UNDER ONE PARENT, AND THE
#    PARENT IS REMOVED WHEN THE FILE EXITS — pass, fail or crash.
#    `[measured 2026-09-28]` Only 4 of this file's 13 trees were ever
#    removed, and a run stopped at its first failure removed none: 5,317
#    `dossier-*` dirs, about 82 GB, sat in %TEMP%. ⛔ Only what THIS
#    process made is removed, never a glob over %TEMP% — that would take
#    another run's trees out from under it.
#    ⚠️ Registered AFTER `tcheck` is imported, so it runs BEFORE tcheck's
#    gate (atexit is last-in, first-out) and the gate's `os._exit` on a
#    failure cannot skip it.
# ══════════════════════════════════════════════════════════════════════
_RUN_TMP = tempfile.mkdtemp(prefix="dossier-run-")
_MADE = []                  # every tree this process made, for the final check


def _cleanup():
    shutil.rmtree(_RUN_TMP, ignore_errors=True)


atexit.register(_cleanup)

# ══════════════════════════════════════════════════════════════════════
# ⛔ NO `collect.py` RUN HERE MAY REACH THE NETWORK OR SPEND A CREDIT.
#    `[measured 2026-09-28]` `collect.py card-fb` WITHOUT `converge-off`
#    converges: it fetched news from cbssports.com and profootballtalk on
#    every run, and on the 2026-09-27 tree it planned THREE PAID MODES,
#    refused only because the Tests step happens to have no key. So every
#    run passes `converge-off`, blank keys, and this socket blocker, which
#    records each attempt so a check can fail on it (`run_collect`).
# ══════════════════════════════════════════════════════════════════════
_NETBLOCK = os.path.join(_RUN_TMP, "netblock")
os.makedirs(_NETBLOCK)
with open(os.path.join(_NETBLOCK, "sitecustomize.py"), "w", encoding="utf-8") as _fh:
    _fh.write('''\
# Written by test_dossier_fb.py: every non-local connection is refused and logged.
import os, socket
_LOG = os.environ.get("DOSSIER_TEST_NETLOG")
_gai, _conn = socket.getaddrinfo, socket.socket.connect
def _local(h):
    return str(h) in ("localhost", "127.0.0.1", "::1", "")
def _say(what):
    if _LOG:
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(str(what) + "\\n")
def getaddrinfo(host, *a, **k):
    if not _local(host):
        _say(host)
        raise OSError("network blocked by test_dossier_fb.py: %s" % host)
    return _gai(host, *a, **k)
def connect(self, addr):
    h = addr[0] if isinstance(addr, tuple) else addr
    if not _local(h):
        _say(addr)
        raise OSError("network blocked by test_dossier_fb.py: %r" % (addr,))
    return _conn(self, addr)
socket.getaddrinfo = getaddrinfo
socket.socket.connect = connect
''')


def run_collect(d, mode="card-fb"):
    """`collect.py <mode> converge-off` in tree `d` -> (rc, log, attempts).

    ⛔ `converge-off`, so the mode runs ALONE; blank keys, so a paid mode
    could not spend even if one were reached; and the blocker above on
    PYTHONPATH, so any network attempt fails fast and is RETURNED."""
    net = os.path.join(d, "network-attempts.log")
    env = dict(os.environ, LEAGUE="nfl", ODDS_API_KEY="", CFBD_API_KEY="",
               DOSSIER_TEST_NETLOG=net,
               PYTHONPATH=os.pathsep.join(
                   [_NETBLOCK] + [p for p in [os.environ.get("PYTHONPATH")] if p]))
    p = subprocess.run([sys.executable, "collect.py", mode, "converge-off"],
                       cwd=d, timeout=1200, capture_output=True, text=True,
                       env=env)
    tried = (open(net, encoding="utf-8").read().splitlines()
             if os.path.exists(net) else [])
    return p.returncode, (p.stdout or "") + (p.stderr or ""), tried


def _load(path):
    """The dossier file, or `{}` if the builder refused to write one."""
    if not os.path.exists(path):
        return {}
    try:
        return json.load(gzip.open(path, "rt"))
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════
# 🌱 PLANT, NEVER WAIT. `[2026-09-28, Sam: "Each check must always have its
#    case by planting a fixture (the way #156 did), never by waiting for
#    live data."]`
# ══════════════════════════════════════════════════════════════════════
# Every tree's board gets FIXTURE_N REAL games at its front: rows of the
# stored schedule, named by the builder's OWN team table, ids
# `fixture-<schedule id>`. The live games stay behind them as extras.
# ⚠️ FROM THE CALENDAR'S SECOND WEEK, NEVER THE FIRST: in week 1 no team
#    has an earlier game, so the possession and this-season sections would
#    have nothing to read. ⚠️ Read from the NEWEST schedule, the season the
#    builder itself reads, so a season rollover moves the fixture with it.
# ⛔ The old live floor was 10 board games; the planted floor is 12
#    described games, on every day, before a single live game is counted.
# `extras=True` (section 1's tree ONLY) also plants:
#   - a PRIOR MEETING for the first game, 200 days earlier, 23-20, so a
#     meeting with a known score always exists (in every tree it would
#     become section 1c's earliest schedule date and break that fixture);
#   - a POSSESSION ROW for that pair the day before, in the table for the
#     builder's season, creating that table if the calendar has not yet;
#   - a game dated 30 days before every possession row, so the refusal
#     "carries neither team" always has a case (week 1, every season).
FIXTURE_N = 12
_PLANTS = {}                # tree -> what plant() put there


def _fixture(board_id):
    return str(board_id or "").startswith("fixture-")


def plant(d, extras=False):
    lat = os.path.join(d, "data", "nfl", "latest")
    name = {}
    for n, c in sorted(_DFX.nfl_table(d).items()):
        name.setdefault(c, n)           # code -> a board name the builder resolves
    info = {"pick": [], "season": None, "meeting": None, "no_row_id": None}
    # ⚠️ `[Sam, 2026-10-09]` THE NEWEST SCHEDULE THAT CAN HOLD THE FIXTURE, not
    #    merely the newest file: a season published before its games (or one too
    #    short) would turn the check below red on correct code. The builder reads
    #    every stored season (`dossier_fb.seasons`), so an earlier one is as real.
    sps = sorted(glob.glob(os.path.join(
        lat, "schedule-[0-9][0-9][0-9][0-9].json.gz")))
    S, pick = {}, []
    for sp in reversed(sps):
        S = _load(sp) or {}
        sg = sorted((x for x in (S.get("games") or [])
                     if x.get("start") and x.get("week") is not None
                     and x.get("home") in name and x.get("away") in name),
                    key=lambda x: x["start"])
        weeks = sorted({x["week"] for x in sg})
        pick = [x for x in sg if len(weeks) > 1 and x["week"] == weeks[1]][:FIXTURE_N]
        if len(pick) == FIXTURE_N:
            break
    sps = [sp] if sps else []
    if sps:
        info["season"] = int(re.search(r"(\d{4})\.json\.gz$", sps[-1]).group(1))
    info["pick"] = pick
    rows = [{"id": "fixture-%s" % x["id"], "home": name[x["home"]],
             "away": name[x["away"]], "commence": x["start"][:16] + ":00Z"}
            for x in pick]
    if extras and len(pick) >= 2:
        x0, x1 = pick[0], pick[1]
        k0 = datetime.date.fromisoformat(x0["start"][:10])
        met = {"id": "fixture-prior-meeting", "home": x0["away"],
               "away": x0["home"], "week": None, "final": True,
               "start": (k0 - datetime.timedelta(days=200)).isoformat() + "T13:00",
               "home_score": 23, "away_score": 20}
        S["games"].append(met)
        with gzip.open(sps[-1], "wt") as fh:
            json.dump(S, fh)
        info["meeting"] = met
        tp = os.path.join(lat, "top-%d.json.gz" % info["season"])
        T = _load(tp) or {"season": info["season"], "kind": "FIXTURE",
                          "teams": {}}
        if not isinstance(T.get("games"), dict):
            T["games"] = {}
        T["games"]["fixture-top"] = {
            "date": (k0 - datetime.timedelta(days=1)).isoformat(),
            "coverage": 1.0, "withheld": False,
            "teams": {x0["home"]: {"share": 0.55, "seconds": 1980, "drives": 11},
                      x0["away"]: {"share": 0.45, "seconds": 1620, "drives": 10}}}
        with gzip.open(tp, "wt") as fh:
            json.dump(T, fh)
        first = min(str(g.get("date"))[:10] for g in T["games"].values()
                    if g.get("date"))
        pre = datetime.date.fromisoformat(first) - datetime.timedelta(days=30)
        info["no_row_id"] = "fixture-no-possession-row"
        rows.append({"id": info["no_row_id"], "home": name[x1["home"]],
                     "away": name[x1["away"]],
                     "commence": pre.isoformat() + "T17:00:00Z"})
    bp = os.path.join(lat, "board.json")
    try:
        B = json.load(open(bp, encoding="utf-8"))
    except (OSError, ValueError):
        B = {"games": []}
    B["games"] = rows + (B.get("games") or [])
    json.dump(B, open(bp, "w", encoding="utf-8"))
    return info


def tree(with_dossier=True, extras=False):
    """A throwaway repo with the data the builder and the card both read,
    and FIXTURE_N real games planted at the front of its board."""
    d = tempfile.mkdtemp(prefix="dossier-", dir=_RUN_TMP)
    _MADE.append(d)
    shutil.copytree(os.path.join(ROOT, "data", "nfl"),
                    os.path.join(d, "data", "nfl"))
    # ══════════════════════════════════════════════════════════════════
    # 🔴 A PLAYERS FILE BUILT BEFORE SIGNAL 7 GETS THE BLOCK A NEW BUILD
    #    WRITES. `[2026-09-23]` This tree copies the LIVE data, and until
    #    the first `nfl-logs` run after the players-out count shipped, the
    #    live file has no `team_out`. ⛔ Without this, the suite's verdict
    #    would depend on WHEN it ran — and the collector runs the suite
    #    BEFORE it collects, so red here could stop the very build that
    #    turns it green. Same shape `team_out_from_rows` emits; a file that
    #    already carries the real block is left exactly as it is.
    # ══════════════════════════════════════════════════════════════════
    # ⚠️ PATCHED ONCE PER PROCESS, THEN COPIED AS BYTES. `[measured
    #    2026-09-23]` Re-reading and re-writing six players files in every
    #    `tree()` cost 3s a call — 91s -> 131s for this file — and the
    #    nightly `vacuity` sweep runs this file 34 times, which pushed
    #    `test_vacuity.py` past its 2400s clock on PR #138.
    for _pf in glob.glob(os.path.join(d, "data", "nfl", "latest",
                                      "players-*.json.gz")):
        _name = os.path.basename(_pf)
        if _name not in _TEAM_OUT_PATCHED:
            with gzip.open(_pf, "rt", encoding="utf-8") as _fh:
                _doc = json.load(_fh)
            if "team_out_report" in _doc:
                _TEAM_OUT_PATCHED[_name] = None       # the real block: leave it
            else:
                _teams = sorted({r.get("team") for v in (_doc.get("players") or {}).values()
                                 for r in (v.get("g") or []) if r.get("team")})
                _doc["team_out"] = {t: {"1": {"out": 1, "injury_report": 1,
                                              "roster_status": 0,
                                              "players": [{"name": "Fixture Player",
                                                           "why": ["injury report: out"]}]}}
                                    for t in _teams}
                _doc["team_out_report"] = {"usable": True, "fixture": True}
                _TEAM_OUT_PATCHED[_name] = gzip.compress(
                    json.dumps(_doc).encode("utf-8"), compresslevel=1)
        if _TEAM_OUT_PATCHED[_name] is not None:
            with open(_pf, "wb") as _fh:
                _fh.write(_TEAM_OUT_PATCHED[_name])
    for _rel in PRODUCED:
        _p = os.path.join(d, _rel)
        if os.path.exists(_p):
            os.remove(_p)
    os.makedirs(os.path.join(d, "picks"), exist_ok=True)
    for f in glob.glob(os.path.join(ROOT, "picks", "fb-nfl-*.json")):
        shutil.copy(f, os.path.join(d, "picks"))
    copy_module("card_fb", d)
    # ⚠️ `collect.py` COMES WITH ITS OWN IMPORTS. `dossier_fb.py` does not
    #    IMPORT it — it parses `NFL_TEAMS` out of its source at runtime, a
    #    file read the walk cannot see — but section 8 EXECUTES the real
    #    `card-fb` mode, and the collector imports `freshness`, `nfl` and
    #    more. `copy_module` brings them; a bare `shutil.copy` did not,
    #    and the section died on `ModuleNotFoundError` rather than
    #    answering its question.
    copy_module("collect", d)
    if with_dossier:
        copy_module("dossier_fb", d)
    else:
        # ══════════════════════════════════════════════════════════════
        # 🔴🔴 THE "WITHOUT" TREE HAD THE FILE ALL ALONG. `[found
        # 2026-09-28 by driving section 3's mutation]` `collect.py`
        # imports `dossier_fb` inside its `card-fb` branch, so the
        # `copy_module("collect")` above copies it — and section 3's
        # "card built WITHOUT this file" was built beside it. A card
        # that reached the dossier would have reached it in BOTH trees,
        # and the diff could not see it. ✅ Removed here, and section 3
        # checks the two trees differ in exactly this file.
        # ══════════════════════════════════════════════════════════════
        _dx = os.path.join(d, "dossier_fb.py")
        if os.path.exists(_dx):
            os.remove(_dx)
    # 🌱 LAST, so the table it reads is the tree's own `collect.py`.
    _PLANTS[d] = plant(d, extras)
    return d


def run(d, script, league="nfl"):
    p = subprocess.run([sys.executable, script], cwd=d, timeout=600,
                       capture_output=True, text=True,
                       env=dict(os.environ, LEAGUE=league))
    return p.returncode, (p.stdout or "") + (p.stderr or "")


section("1. ⚠️ IT RUNS, AND EVERY BOARD GAME IS ACCOUNTED FOR")
_d = tree(extras=True)
_FX = _PLANTS[_d]
_PICK = _FX["pick"]
ck(bool(len(_PICK) == FIXTURE_N and _FX["meeting"] and _FX["no_row_id"]),
   "⚠️ the fixture planted %d real week-%s games from the %s schedule, plus "
   "its prior meeting and its no-possession-row game"
   % (len(_PICK), _PICK[0].get("week") if _PICK else "?", _FX["season"]),
   "⛔ rule 67 — every sweep below stands on these games. The schedule "
   "names the teams and the builder's own table (`nfl_table`) names them "
   "on the board; an empty table or a one-week calendar plants nothing")
_rc, _out = run(_d, "dossier_fb.py")
ck(_rc == 0, "the builder exits clean", _out[-400:])
_P = os.path.join(_d, "data/nfl/latest/dossiers.json.gz")
ck(os.path.exists(_P), "⛔ ...and wrote a dossier file", _out[-300:])
_D = _load(_P)
# ══════════════════════════════════════════════════════════════════════
# 🔴 ~~"the real board has games to describe" (`_NG >= 10` over the LIVE
# board)~~ REPLACED 2026-09-28. ⛔ It waited for live data: a Monday board
# of 7 games, mostly finished, turned it red on correct code (collect red
# from 2026-09-26 16:16Z), and an empty board killed this file at its
# first fixture. ✅ The board under test is now the TREE's board — the
# planted games in front, the live ones behind — and the floor is 12
# DESCRIBED planted games: a higher bar than 10 board rows, met every day.
# ══════════════════════════════════════════════════════════════════════
_BOARD = json.load(open(os.path.join(_d, "data/nfl/latest/board.json"),
                        encoding="utf-8"))
_NG = len(_BOARD.get("games") or [])
_FIXIDS = [g.get("id") for g in (_BOARD.get("games") or []) if _fixture(g.get("id"))]
_NP = sum(1 for g in (_D.get("dossiers") or []) if _fixture(g.get("board_id")))
ck(_NP == len(_FIXIDS) and _NP >= FIXTURE_N,
   "⚠️ the board under test has games to describe (%d planted + %d live)"
   % (_NP, _NG - len(_FIXIDS)),
   "⛔ a sweep over an empty board passes and proves nothing (rule 67). %d "
   "planted board row(s), %d described" % (len(_FIXIDS), _NP))
ck(_D.get("n_dossiers", 0) + len(_D.get("skipped") or []) == _NG,
   "🔴🔴 EVERY board game is either a dossier or a NAMED skip",
   "⛔ a game that simply vanished from the output is the shape this "
   "check exists for. %d dossier(s) + %d skip(s) vs %d board game(s)"
   % (_D.get("n_dossiers", 0), len(_D.get("skipped") or []), _NG))
ck(all(s.get("why") for s in (_D.get("skipped") or [])),
   "   ⛔ ...and every skip carries its reason",
   "🔴 a game missing from the output and a game with nothing to say are "
   "different facts. Skipped: %s" % (_D.get("skipped") or []))
# ── THE LIVE BOARD, AS AN EXTRA: asserted only when it holds games ────
# ⚠️ A skip carries no board id (`dossier_fb._skip`), so a live game is
#    matched to one by the board's own (home, away) strings.
_LIVE = [g for g in (_BOARD.get("games") or []) if not _fixture(g.get("id"))]
if _LIVE:
    _ids1 = {g.get("board_id") for g in (_D.get("dossiers") or [])}
    _sk1 = {(s.get("home"), s.get("away")) for s in (_D.get("skipped") or [])}
    _lost1 = [(g.get("away"), g.get("home")) for g in _LIVE
              if g.get("id") not in _ids1
              and (g.get("home"), g.get("away")) not in _sk1]
    ck(not _lost1,
       "   ✅ ...including every game on the LIVE board (%d)" % len(_LIVE),
       "⛔ the planted games prove the builder; this proves today's slate. "
       "Neither described nor named: %s" % _lost1)
else:
    note("   the live board holds no games right now — the planted games "
         "carry every check in this file, which is what they are for")
note("   %d of %d board games produced a dossier (%d planted, %d live); %d "
     "skipped." % (_D.get("n_dossiers", 0), _NG, _NP, len(_LIVE),
                   len(_D.get("skipped") or [])))

section("1a. ⛔ AND THE 'OR NAMED' HALF IS DRIVEN, NOT ASSUMED")
# 🔴 CAUGHT BY DRIVING THE MUTATION, NOT BY READING. Every game on today's
#    board maps to a team code, so `skipped` is always empty and deleting
#    the line that records a skip changed NOTHING — the guard above was
#    half vacuous. A board with a name the code table does not hold is the
#    only thing that exercises it.
# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 AND IT WENT VACUOUS A SECOND TIME, THE SAME WAY. `[2026-09-17]`
# The college port split one outcome into two: a game with ONE
# unresolvable side is now DESCRIBED and named in `one_sided`, and only a
# game with NEITHER side resolvable is skipped. The fixture below had one
# unmappable side, so after the port `skipped` was empty again and the
# harness called the declaration VACUOUS — correctly, and for the second
# time on the same line.
# ➡️ SO THE FIXTURE NOW CARRIES BOTH SHAPES: a game with one side
# missing and a game with both. Each of the two lists has exactly one
# entry, and each entry is checked BY NAME, so neither path can go quiet
# without a check going red.
# ══════════════════════════════════════════════════════════════════════
# ⚠️ `games[0]` IS A PLANTED ROW `[2026-09-28]`: every tree's board opens
#    with FIXTURE_N real schedule games, so these fixtures are built on
#    any day. It used to be the first LIVE game, and an empty live board
#    raised IndexError here and killed every check after it.
_d2 = tree()
_bp = os.path.join(_d2, "data/nfl/latest/board.json")
_b2 = json.load(open(_bp, encoding="utf-8"))
_b2["games"] = _b2["games"][:2] + [dict(_b2["games"][0],
                                        home="Nonexistent Ballclub",
                                        away="Detroit Lions"),
                                   dict(_b2["games"][0],
                                        home="Imaginary Athletic",
                                        away="Phantom Nine")]
json.dump(_b2, open(_bp, "w", encoding="utf-8"))
_rc2, _out2 = run(_d2, "dossier_fb.py")
ck(_rc2 == 0, "   the builder survives a name it cannot resolve",
   "⛔ one unmappable game must not cost the other 31 their dossiers. %s"
   % _out2[-300:])
# ⚠️ `.get`-STYLE, NOT A BARE LOAD. When a mutation makes the builder
#    correctly REFUSE, no file exists — and a FileNotFoundError kills this
#    file and costs every check after it its turn. A guard that dies
#    reports "an unknown number never ran", which is strictly less than a
#    guard that fails.
_D2 = _load(os.path.join(_d2, "data/nfl/latest/dossiers.json.gz"))
# ══════════════════════════════════════════════════════════════════════
# ⚠️ THE QUESTION IS UNCHANGED; THE ANSWER GAINED A SECOND SHAPE.
# `[college port, 2026-09-17]` A game with ONE unresolvable side is no
# longer skipped — 16 of the 88 college board sides are FCS schools
# absent from the FBS table, and dropping those games would lose 18 pct
# of the Saturday board. They are DESCRIBED and the missing side is
# NAMED in `one_sided`. Only a game with NEITHER side resolvable is
# skipped.
# ⛔ SO THIS ASKS THE SAME THING AND ASKS IT HARDER: the unmappable name
# must appear in one of the two lists, and it must appear BY NAME —
# "named somewhere" alone would pass on a list that named the wrong game.
# ══════════════════════════════════════════════════════════════════════
_skip2 = _D2.get("skipped") or []
_one2 = _D2.get("one_sided") or []
ck(len(_skip2) == 1 and len(_one2) == 1,
   "🔴🔴 BOTH UNMAPPABLE GAMES ARE NAMED (%d skipped, %d one-sided)"
   % (len(_skip2), len(_one2)),
   "⛔ a game that simply vanished from the output is indistinguishable "
   "from one with nothing to say, and an EMPTY list is the shape that "
   "made this declaration vacuous twice (rule 67). Got %s / %s"
   % (_skip2, _one2))
ck(any(x.get("home") == "Imaginary Athletic" for x in _skip2),
   "   ...the unsalvageable one BY THE NAME THE BOARD USED, in `skipped`",
   "🔴 neither side of this game resolves, so there is nothing to "
   "describe — naming it is the whole obligation. Got %s" % _skip2)
ck(any(x.get("home") == "Nonexistent Ballclub" for x in _one2),
   "   ...and the half-resolvable one in `one_sided`, also by name",
   "Got %s" % _one2)
ck(any(x.get("not_in_table") == "Nonexistent Ballclub" for x in _one2),
   "   ⛔ ...and the side that could not be resolved is named SEPARATELY",
   "🔴 'one side is missing' is useless without which side. Got %s"
   % _one2)
ck(_D2.get("n_dossiers", 0) + len(_D2.get("skipped") or [])
   == len(_b2["games"]),
   "   ⛔ ...and the two still account for every board game",
   "%d + %d vs %d" % (_D2.get("n_dossiers", 0),
                      len(_D2.get("skipped") or []), len(_b2["games"])))

section("1b. 🔴🔴 AN UNIDENTIFIED OPPONENT IS NEVER AN `OK` SECTION")
# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 19 OF 88 COLLEGE ROWS PUBLISHED A NULL OPPONENT AND FIVE SECTIONS
# STILL READ `OK`. `[found in review of the college port, 2026-09-17]`
# ⛔ AND THE NULL WAS NOT THE WORST OF IT. Head to head said "No meeting
# between these two inside 365 days" — a statement about a comparison
# THAT WAS NEVER ATTEMPTED, because there is no "these two". A reader
# takes it as "they have not played recently"; the truth is "we do not
# know who the opponent is". Versus position — whose whole subject is
# the OPPOSING defence — read `OK` with one defence in it.
#
# 🔴 THE CLASS: A REFERENCE SET NARROWER THAN THE BOARD SILENTLY
# TRUNCATES THE BOARD. The top-division team list is the right source
# for top-division teams and the wrong source for "who is playing
# tonight" — the board is a SUPERSET by construction, because books
# price top-division-vs-lower-division games. ➡️ Wherever a lookup set
# and the thing looked up come from different sources, the mismatch is a
# DATA CLASS, not an edge case.
#
# ⚠️ NFL CANNOT HAVE THIS, WHICH IS WHY NOTHING CAUGHT IT: every NFL
# opponent is an NFL team, and all 32 NFL board games join a schedule
# row. ⛔ A fact about NFL is not a fact about the board.
#
# ⛔ SO THE FIRST CHECK IS DERIVED FROM THE SOURCE, NOT A LIST OF THREE
# SECTION NUMBERS. Naming §2, §5 and §6 would guard exactly those three
# and leave the next pair-wise section wide open — rules 246 and 130,
# which this repo has now shipped twice.
# ══════════════════════════════════════════════════════════════════════
# ⛔ ONE READ OF THE SOURCE FOR THE WHOLE FILE (section 5 reuses it) —
#    two copies of the same file read is two things to drift.
_DSRC = open(os.path.join(ROOT, "dossier_fb.py"), encoding="utf-8").read()
_SFNS = [n for n in ast.parse(_DSRC).body
         if isinstance(n, ast.FunctionDef) and n.name.startswith("s_")]
_pairwise, _gated = [], []
for _n in _SFNS:
    _args = {a.arg for a in _n.args.args}
    _used = {x.id for x in ast.walk(_n) if isinstance(x, ast.Name)}
    if {"home", "away"} <= (_args & _used):
        _pairwise.append(_n.name)
        if "no_opponent" in _used:
            _gated.append(_n.name)
ck(len(_pairwise) >= 3,
   "⚠️ the sections that COMPARE the two sides are derived (%s)"
   % ", ".join(_pairwise),
   "⛔ rule 67: an empty list here would make the check below pass "
   "forever. A section is pair-wise if it takes BOTH `home` and `away` "
   "and USES them — which is why venue, whose subject is the ground, is "
   "correctly not in this list. Found %s" % _pairwise)
ck(_pairwise == _gated,
   "🔴🔴 ...AND EVERY ONE OF THEM ROUTES THROUGH `no_opponent`",
   "⛔ a section whose subject is the PAIR cannot answer at all when one "
   "side is unknown — it must say so, not show the half it has. "
   "Ungated: %s" % sorted(set(_pairwise) - set(_gated)))

# ── AND DRIVEN, on a board row whose AWAY side does not resolve ──────
# ⚠️ AWAY on purpose: all 16 real cases are the away team, because the
#    lower-division side is the visitor in a money game.
_d1b = tree()
# ══════════════════════════════════════════════════════════════════════
# ⚠️ THE PER-TEAM SECTIONS THAT NAME THE MISSING HALF NEED A PLAYERS FILE
# FOR THE SEASON THE BUILDER READS, AND THE CALENDAR DOES NOT ALWAYS HAVE
# ONE. `[found 2026-09-28 by replaying a season rollover]` This Season (§4)
# and Personnel (§7) read `players-<season>`; from the day next season's
# schedule lands until its first game is logged there is no such file
# (or one with no rows), both refuse, and the floor of two named sections
# below went red on correct output. ✅ So in that gap this tree's file
# for the builder's season is the newest stored one that holds the home
# team — planted, like the games, and said out loud.
# ══════════════════════════════════════════════════════════════════════
_s1b = _PLANTS[_d1b]["season"]
_lat1b = os.path.join(_d1b, "data/nfl/latest")


def _holds(path, team):
    return any(r.get("team") == team
               for v in ((_load(path).get("players") or {}).values())
               for r in (v.get("g") or []))


_det1b = _DFX.nfl_table(_d1b).get("Detroit Lions")
if _s1b and not _holds(os.path.join(_lat1b, "players-%d.json.gz" % _s1b), _det1b):
    _src1b = next((p for p in sorted(glob.glob(os.path.join(
        _lat1b, "players-[0-9][0-9][0-9][0-9].json.gz")), reverse=True)
        if _holds(p, _det1b)), None)
    if _src1b:
        shutil.copy(_src1b, os.path.join(_lat1b, "players-%d.json.gz" % _s1b))
    note("   the %s season has no %s player rows yet, so the 1b tree reads %s "
         "as that season's players file"
         % (_s1b, _det1b, os.path.basename(_src1b or "nothing")))
_bp1b = os.path.join(_d1b, "data/nfl/latest/board.json")
_b1b = json.load(open(_bp1b, encoding="utf-8"))
_b1b["games"] = _b1b["games"][:2] + [dict(_b1b["games"][0],
                                          home="Detroit Lions",
                                          away="Slippery Rock Aardvarks")]
json.dump(_b1b, open(_bp1b, "w", encoding="utf-8"))
_rc1b, _out1b = run(_d1b, "dossier_fb.py")
ck(_rc1b == 0, "   the builder still exits clean on that board",
   "⛔ one unidentifiable opponent must not cost the slate its dossiers. "
   "%s" % _out1b[-300:])
_D1b = _load(os.path.join(_d1b, "data/nfl/latest/dossiers.json.gz"))
_part = [g for g in (_D1b.get("dossiers") or [])
         if g.get("away_name") == "Slippery Rock Aardvarks"]
ck(len(_part) == 1,
   "🔴 the game is DESCRIBED, not dropped (%d row)" % len(_part),
   "⛔ §1 is real — the price is a price and the game is bettable. "
   "Suppressing the whole game loses a row Sam can bet. Got %s"
   % [g.get("away_name") for g in (_D1b.get("dossiers") or [])])
_pg = (_part or [{}])[0]
ck(_pg.get("away_name") == "Slippery Rock Aardvarks",
   "🔴🔴 ...AND IT CARRIES THE BOARD'S OWN NAME FOR THAT SIDE",
   "⛔ A GAME THE READER CAN NAME MUST NEVER RENDER AS None. The board "
   "is complete — it has the name — and publishing null instead threw "
   "away the one thing we did know. Got %r" % _pg.get("away_name"))
ck(_pg.get("unresolved_side") == "Slippery Rock Aardvarks",
   "   ⛔ ...and the gap is ON THE ROW, not only in a list elsewhere",
   "🔴 a consumer reading one row must not have to cross-reference "
   "another key to learn half of it is missing. Got %r"
   % _pg.get("unresolved_side"))
_sec1b = {s.get("n"): s for s in (_pg.get("sections") or [])}
_okpair = sorted(n for n in _sec1b
                 if _sec1b[n].get("name") in
                 ("Head to head", "Versus position", "Time of possession")
                 and _sec1b[n].get("state") == "OK")
ck(not _okpair,
   "🔴🔴 ...AND NO PAIR-WISE SECTION READS `OK` ON IT",
   "⛔ NEVER WEAKEN A CHECK TO MAKE IT PASS, and never widen what OK "
   "means either: a section that compared nothing must read UNAVAILABLE. "
   "Still OK: %s" % [(n, _sec1b[n].get("name")) for n in _okpair])
ck(all("Slippery Rock Aardvarks" in (_sec1b[n].get("why") or "")
       for n in _sec1b
       if _sec1b[n].get("name") in ("Head to head", "Versus position",
                                    "Time of possession")),
   "   ⛔ ...and each refusal NAMES the side it could not identify",
   "🔴 'not available' with no subject is unreadable. Got %s"
   % [(_sec1b[n].get("name"), (_sec1b[n].get("why") or "")[:60])
      for n in sorted(_sec1b)])
_h2h1b = _sec1b.get(2) or {}
ck("No meeting between these two" not in (_h2h1b.get("why") or ""),
   "🔴🔴 ...AND HEAD TO HEAD NO LONGER ASSERTS A CHECK THAT NEVER RAN",
   "⛔ THIS IS THE FOUNDING ERROR OF THIS PROJECT IN COLLEGE COLOURS: a "
   "fact about a query is not a fact about the world. There is no "
   "'these two'. Got: %s" % (_h2h1b.get("why") or "")[:140])
ck((_sec1b.get(1) or {}).get("state") == "OK",
   "   ✅ ...while §1 STAYS OK — the market is the thing we do know",
   "⛔ do not suppress the game. The price is real and it is on the "
   "board. Got %s" % (_sec1b.get(1) or {}).get("state"))
_nullkey = sorted(n for n in _sec1b
                  if isinstance(_sec1b[n].get("by_team"), dict)
                  and any(k in (None, "null", "None")
                          for k in _sec1b[n]["by_team"]))
ck(not _nullkey,
   "   ⛔ ...and no per-team table carries a `null` team key",
   "🔴 a None in the team list published a literal \"null\" key inside "
   "`by_team` — junk in a permanent record. Sections: %s" % _nullkey)
_named1b = sorted(n for n in _sec1b
                  if _sec1b[n].get("state") == "OK"
                  and isinstance(_sec1b[n].get("by_team"), dict)
                  and _sec1b[n].get("not_covered")
                  == "Slippery Rock Aardvarks")
ck(len(_named1b) >= 2,
   "   ✅ ...and each per-team section NAMES the half it covers nothing "
   "for (%s)" % _named1b,
   "⛔ a section covering one team of two and saying nothing about it is "
   "the same 'looks complete' failure one step quieter. Got %s"
   % [(n, _sec1b[n].get("not_covered")) for n in sorted(_sec1b)])
ck(_D1b.get("n_partial") == 1 and "PARTIAL" in _out1b,
   "   ⚠️ ...and the count is STATED, in the file and in the log",
   "⛔ rule 166: \"88 of 88\" read as full coverage while 19 rows had no "
   "identified opponent. n_partial=%r, log says PARTIAL=%s"
   % (_D1b.get("n_partial"), "PARTIAL" in _out1b))

section("1c. 🔴🔴 A MISSING SCHEDULE ROW WAS A FAILED JOIN, NOT AN ABSENCE")
# ══════════════════════════════════════════════════════════════════════
# 🔴 19 COLLEGE GAMES READ "the schedule has no row for this game" AND 17
# OF THEM WERE IN `schedule-2026.json.gz` ALL ALONG. `[measured
# 2026-09-18]` The pair key is built from the RESOLVED code on BOTH
# sides, and an FCS away team resolves to `None`, so `(home, None, date)`
# could never match. ⚠️ The schedule holds that school's name perfectly
# well — it is the FBS-only TEAM LIST that does not. Same
# reference-set-narrower-than-the-board class as task 27, one join over.
# ✅ SO: the exact pair first, then ONE SIDE PLUS THE DATE — and UNIQUE
# OR NOTHING. Measured across 4 stored schedules, 8,063 of 8,065
# (team, date ±1) keys hold exactly one game; the two that do not are a
# Division III fixture duplicated under two ids. A key that is unique
# 99.98% of the time is not a key you may assume.
# ⛔ AND THE WINDOW IS LOAD-BEARING: the college schedule stamps `start`
# with a `Z` and the NFL one stores `2026-09-09T20:20` with no zone at
# all, so an NFL night game files a day earlier there than on the board.
# ══════════════════════════════════════════════════════════════════════
_d1c = tree()
_sp = os.path.join(_d1c, "data/nfl/latest/schedule-2026.json.gz")
_S = _load(_sp)
_sg = _S.get("games") or []
ck(len(_sg) > 50, "⚠️ the fixture has a real schedule to join against (%d)"
   % len(_sg), "⛔ rule 67 — every check below would pass over nothing")
# ⚠️ DERIVED FROM THE ARTIFACT, never a literal date. The stored
#    schedules age, and a hard-coded day reddens on correct code (#51).
_real = sorted(_sg, key=lambda x: x.get("start") or "")[0]
_covered = (_real.get("start") or "")[:10]
_dates = sorted({(x.get("start") or "")[:10] for x in _sg if x.get("start")})
_uncovered = (datetime.datetime.strptime(_dates[0], "%Y-%m-%d")
              - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
# ⚠️ A DATE THE CALENDAR **DOES** COVER, for the third fixture below.
#    ⛔ THE HARNESS CALLED AN EARLIER VERSION OF THIS SECTION VACUOUS AND
#    IT WAS RIGHT: every fixture used an UNCOVERABLE date, so mutating
#    `week_calendar` to hand back week 1 for everything changed nothing
#    observable and the declaration proved nothing (rule 244). A guard
#    that only tests the refusal never tests the placement.
_placed = _dates[-1]
_placed_week = next(x["week"] for x in _sg
                    if (x.get("start") or "")[:10] == _placed
                    and x.get("week") is not None)
_bp1c = os.path.join(_d1c, "data/nfl/latest/board.json")
_b1c = json.load(open(_bp1c, encoding="utf-8"))
# ⚠️ THE BOARD NAMES THE HOME TEAM IN FULL; reuse the builder's OWN
#    resolver rather than a second copy of the mapping (rule 66).
#    ⚠️ `_DFX` is imported once, beside `tree()`, which plants with it.
_res = _DFX.team_codes("nfl")
_homefull = next(g["home"] for g in _b1c["games"] if _res(g.get("home")))
_homecode = _res(_homefull)
# ⛔ A SCHEDULE ROW THAT EXISTS FOR (home, date) BUT WHOSE AWAY SIDE THE
#    TEAM LIST CANNOT RESOLVE — the exact 17-game shape.
# ⛔ AND THE HOME TEAM HAS NO ROW NEAR `_placed` EITHER, so that game
#    reaches the calendar rather than a schedule row.
_S["games"] = [x for x in _sg
               if not (x.get("home") == _homecode
                       and abs((datetime.datetime.strptime(
                           (x.get("start") or "1900-01-01")[:10], "%Y-%m-%d")
                           - datetime.datetime.strptime(_covered, "%Y-%m-%d")
                       ).days) <= 1)
               and not (x.get("home") == _homecode
                        and abs((datetime.datetime.strptime(
                            (x.get("start") or "1900-01-01")[:10], "%Y-%m-%d")
                            - datetime.datetime.strptime(_placed, "%Y-%m-%d")
                        ).days) <= 1)]
_S["games"].append({"home": _homecode, "away": "Slippery Rock",
                    "start": _covered + "T18:00", "week": 99,
                    "venue": "A Real Stored Stadium", "roof": "outdoors",
                    "surface": "grass", "neutral": False,
                    "id": "fixture-one-side"})
with gzip.open(_sp, "wt") as _fh:
    json.dump(_S, _fh)
# ⚠️ THE REAL GAMES STAY ON THE BOARD BESIDE THE TWO FIXTURES. A board
#    of two synthetic games carries no prior meetings and no ranked
#    defences, so `audit()` correctly REFUSES to write — its stale-
#    exception check fires because `meetings`, `by_player` and
#    `by_defence` never appear at all. ⛔ That is the audit working; a
#    fixture thin enough to trip it is testing the fixture.
# ⚠️ `[2026-09-28]` THE SIX KEPT ARE THE PLANTED GAMES, real schedule
#    rows at the front of every tree's board, so this no longer needs
#    six live games to exist (an empty board stopped it at StopIteration).
_b1c["games"] = _b1c["games"][:6] + [
    dict(_b1c["games"][0], home=_homefull,
         away="Slippery Rock Aardvarks",
         commence=_covered + "T18:00:00Z", id="bid-oneside"),
    dict(_b1c["games"][0], home=_homefull,
         away="Nowhere Nine",
         commence=_uncovered + "T18:00:00Z", id="bid-uncovered"),
    dict(_b1c["games"][0], home=_homefull,
         away="Nobody State",
         commence=_placed + "T18:00:00Z", id="bid-placed")]
json.dump(_b1c, open(_bp1c, "w", encoding="utf-8"))
_rc1c, _out1c = run(_d1c, "dossier_fb.py")
ck(_rc1c == 0, "   the builder runs on that board", _out1c[-300:])
_D1c = {x.get("board_id"): x
        for x in (_load(os.path.join(
            _d1c, "data/nfl/latest/dossiers.json.gz")).get("dossiers") or [])}
_one = _D1c.get("bid-oneside") or {}
_unc = _D1c.get("bid-uncovered") or {}
ck(bool(_one) and bool(_unc), "⚠️ both fixture games were described",
   "⛔ rule 67. Got %s" % sorted(_D1c))
_s8one = next((s for s in (_one.get("sections") or []) if s["n"] == 8), {})
ck(_s8one.get("state") == "OK"
   and _s8one.get("venue") == "A Real Stored Stadium",
   "🔴🔴 A ROW THE PAIR KEY MISSES IS FOUND ON ONE SIDE PLUS THE DATE",
   "⛔ 17 of 19 college games carried their venue, roof and surface in "
   "the stored schedule and the dossier said it had no row. Got %s / %r"
   % (_s8one.get("state"), _s8one.get("venue")))
ck("the home team and the date" in (_one.get("row_basis") or ""),
   "   ⚠️ ...and the row SAYS it was joined on one side, not the pair",
   "🔴 a weaker join with no provenance beside it gets read as the "
   "stronger one. Got %r" % _one.get("row_basis"))
ck(_one.get("week") == 99,
   "   ⛔ ...and the week comes from that row (%s)" % _one.get("week"),
   "🔴 the recovered row is the authority when there is one")

section("1d. ⛔ AND WHERE IT GENUINELY CANNOT ANSWER, IT STILL REFUSES")
_s8unc = next((s for s in (_unc.get("sections") or []) if s["n"] == 8), {})
ck(_s8unc.get("state") != "OK" and not _s8unc.get("venue"),
   "🔴🔴 NO SCHEDULE ROW MEANS NO VENUE — IT IS NOT INVENTED",
   "⛔ DO NOT INVENT A VENUE. A home-team default is not a stadium and a "
   "dome is not an assumption. Got %s / %r"
   % (_s8unc.get("state"), _s8unc.get("venue")))
_s3unc = next((s for s in (_unc.get("sections") or []) if s["n"] == 3), {})
ck(_unc.get("week") is None and _s3unc.get("state") != "OK",
   "🔴 a date the calendar cannot place is NOT placed (%r)"
   % _unc.get("week"),
   "⛔ the weeks do not tile the calendar — week 1 ends 09-07 and week 2 "
   "opens 09-10, and week 14 is absent entirely. A date in a gap is "
   "refused, not rounded to a neighbour. Got %s" % _s3unc.get("state"))
ck(_uncovered in (_s3unc.get("why") or ""),
   "   ⛔ ...and the refusal NAMES the date it could not place",
   "🔴 \"could not place it\" without saying which date is unactionable. "
   "Got: %s" % (_s3unc.get("why") or "")[:140])
ck(_unc.get("week_basis") is None,
   "   ⚠️ ...and claims no provenance for a week it does not have",
   "Got %r" % _unc.get("week_basis"))
# ── AND THE OTHER HALF: a date the calendar CAN place, with no row ───
_pl = _D1c.get("bid-placed") or {}
_s3pl = next((s for s in (_pl.get("sections") or []) if s["n"] == 3), {})
ck(bool(_pl) and _pl.get("game_id") is None,
   "⚠️ the third fixture game reaches the calendar (no schedule row)",
   "⛔ rule 67 — with a row it would never exercise the calendar at "
   "all. game_id %r" % _pl.get("game_id"))
ck(_pl.get("week") == _placed_week,
   "🔴🔴 A DATE THE CALENDAR COVERS IS PLACED IN **THE RIGHT WEEK** "
   "(%s, expected %s)" % (_pl.get("week"), _placed_week),
   "⛔ THE HARNESS CALLED THE EARLIER VERSION OF THIS VACUOUS: every "
   "fixture used an uncoverable date, so a `week_calendar` that handed "
   "back week 1 for everything changed nothing and the declaration "
   "proved nothing. ⚠️ The expected week is read out of the schedule "
   "artifact, never written here")
ck("season calendar" in (_pl.get("week_basis") or ""),
   "   ⚠️ ...and says the calendar placed it, not a schedule row",
   "🔴 two different strengths of claim. Got %r" % _pl.get("week_basis"))
ck(_s3pl.get("state") == "OK" or "prior-season" in (_s3pl.get("why") or ""),
   "   ✅ ...so section 3 can answer, or refuses for a REAL reason",
   "⛔ a placed week that still reads 'we cannot place this date' would "
   "mean the week never reached the section. Got %s / %s"
   % (_s3pl.get("state"), (_s3pl.get("why") or "")[:80]))
shutil.rmtree(_d1c, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 AND AN AMBIGUOUS KEY REFUSES RATHER THAN PICKING THE FIRST MATCH.
# ⛔ (team, date ±1) is unique in 8,063 of 8,065 stored rows, and the two
# that are not are a Division III fixture duplicated under two CFBD ids.
# A key that is unique 99.98% of the time is not a key you may assume —
# `resolve()`'s rule, one file over: this project does not guess.
# ⚠️ DRIVEN, because the real schedules contain no such collision for any
# board team, so nothing would ever exercise this branch on live data.
# ══════════════════════════════════════════════════════════════════════
_d1e = tree()
_sp1e = os.path.join(_d1e, "data/nfl/latest/schedule-2026.json.gz")
_S1e = _load(_sp1e)
_g1e = _S1e.get("games") or []
_day1e = sorted({(x.get("start") or "")[:10] for x in _g1e if x.get("start")})[0]
_bp1e = os.path.join(_d1e, "data/nfl/latest/board.json")
_b1e = json.load(open(_bp1e, encoding="utf-8"))
_hf1e = next(g["home"] for g in _b1e["games"] if _res(g.get("home")))
_hc1e = _res(_hf1e)
# ⚠️ THE DOSSIER'S KEY IS (team, date ±1), SO THE FIXTURE CLEARS ±1 TOO.
#    `[measured 2026-09-21]` clearing only the exact day left a real
#    adjacent-day row in the window once the season had games on
#    consecutive days, and the builder — correctly — counted THREE
#    candidates. The test expected two and went red on correct code.
_win1e = {(datetime.date.fromisoformat(_day1e)
           + datetime.timedelta(days=_k)).isoformat() for _k in (-1, 0, 1)}
_S1e["games"] = [x for x in _g1e
                 if not (x.get("home") == _hc1e
                         and (x.get("start") or "")[:10] in _win1e)]
for _i in (1, 2):
    _S1e["games"].append({"home": _hc1e, "away": "Ghost %d" % _i,
                          "start": _day1e + "T18:00", "week": 50 + _i,
                          "venue": "Stadium %d" % _i, "id": "dup%d" % _i})
with gzip.open(_sp1e, "wt") as _fh:
    json.dump(_S1e, _fh)
_b1e["games"] = _b1e["games"][:6] + [
    dict(_b1e["games"][0], home=_hf1e, away="Slippery Rock Aardvarks",
         commence=_day1e + "T18:00:00Z", id="bid-amb")]
json.dump(_b1e, open(_bp1e, "w", encoding="utf-8"))
run(_d1e, "dossier_fb.py")
_amb = next((x for x in (_load(os.path.join(
    _d1e, "data/nfl/latest/dossiers.json.gz")).get("dossiers") or [])
    if x.get("board_id") == "bid-amb"), {})
ck(bool(_amb), "⚠️ the ambiguous fixture game was described",
   "⛔ rule 67 — nothing to check otherwise")
ck(_amb.get("game_id") is None,
   "🔴🔴 TWO CANDIDATES FOR ONE KEY ATTACH NEITHER (game_id %r)"
   % _amb.get("game_id"),
   "⛔ picking the first match is how a dossier ends up describing "
   "another game — the wrong-game class, at a different join")
ck("REFUSED" in (_amb.get("row_basis") or "")
   and "2 schedule rows" in (_amb.get("row_basis") or ""),
   "   ⛔ ...and the row SAYS it refused, and how many it saw",
   "🔴 a silent refusal is indistinguishable from an absent row. Got %r"
   % _amb.get("row_basis"))
_s8amb = next((s for s in (_amb.get("sections") or []) if s["n"] == 8), {})
ck(_s8amb.get("state") != "OK" and not _s8amb.get("venue"),
   "   ⛔ ...so no venue is attached from either of them",
   "🔴 Got %s / %r" % (_s8amb.get("state"), _s8amb.get("venue")))
shutil.rmtree(_d1e, ignore_errors=True)

section("2. ⚠️ ALL NINE SECTIONS, EVERY GAME, PRESENT OR UNAVAILABLE")
_docs = _D.get("dossiers") or []
# `[Sam, 2026-09-24]` section 9, "Opportunity change", added after Venue.
_WANT = ["Market", "Head to head", "Time of year", "This season",
         "Versus position", "Time of possession", "Personnel", "Venue",
         "Opportunity change"]
_bad = []
for _g in _docs:
    _names = [s.get("name") for s in _g.get("sections") or []]
    if _names != _WANT:
        _bad.append((_g.get("home"), _names))
ck(_docs and not _bad,
   "🔴🔴 ALL NINE SECTIONS, IN ORDER, ON EVERY GAME",
   "⛔ an absent section is indistinguishable from a section that found "
   "nothing — the `own_mean` shape. Offenders: %s" % _bad[:3])
_states = {s["state"] for g in _docs for s in g["sections"]}
ck(_states and _states <= {"OK", "UNAVAILABLE"},
   "   every section is OK or explicitly UNAVAILABLE", str(_states))
# ⚠️ RULE 67 FOR THE CHECK BELOW `[2026-09-28]`: on a slate where every
#    section answers, "every UNAVAILABLE section says why" passes over
#    nothing. The planted game dated before every possession row is
#    UNAVAILABLE in three sections on any day.
_unav = [(g.get("home"), s["name"]) for g in _docs for s in g["sections"]
         if s["state"] == "UNAVAILABLE"]
ck(_unav, "⚠️ there are UNAVAILABLE sections to check (%d)" % len(_unav),
   "⛔ rule 67 — an empty sweep proves nothing")
_silent = [(g["home"], s["name"]) for g in _docs for s in g["sections"]
           if s["state"] == "UNAVAILABLE" and not s.get("why")]
ck(not _silent,
   "🔴 ...and an UNAVAILABLE section always says WHY",
   "⛔ 'not shown' with no reason is the gap this whole shape exists to "
   "close. Offenders: %s" % _silent[:3])
_un = sorted({s["name"] for g in _docs for s in g["sections"]
              if s["state"] == "UNAVAILABLE"})
note("   sections reporting UNAVAILABLE somewhere: %s" % _un)

section("3. ⛔⛔ NO PROJECTION MOVES — THE CARDS ARE DIFFED, NOT ASSERTED")
# 🔴 "I did not import it" is not the proof. Build the card in a tree
#    WITH this file and in a tree WITHOUT it, and compare what Sam bets
#    from.
# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 TWO WAYS THIS DIFF COULD PASS HAVING COMPARED NOTHING, BOTH REAL.
# `[measured 2026-09-28]`
#   1. FROZEN COPIES. `card_fb.freeze_published` copies a started game's
#      rows VERBATIM from the committed card of the same slate, and
#      `tree()` copies every committed card into both trees. On the
#      2026-09-27 data 18 rows came out with the committed cards present
#      and 25 FRESH rows with them removed: on a mostly-started day the
#      diff was comparing two copies of one file.
#   2. NO PROPS. The rows come from the LIVE props board, so a day whose
#      next slate is not priced yet has fewer than 5 rows, or none.
#   3. NO "WITHOUT". The WITHOUT tree held `dossier_fb.py` too (see
#      `tree()`): a `card_fb.py` that shifted every confidence whenever
#      that file sat beside it passed all 121 checks of the old file.
# ✅ SO BOTH TREES LOSE EVERY COMMITTED CARD BEFORE EITHER BUILDS, and
#    the proof is built from a PLANTED props board: the priced props of a
#    published card (`picks/fb-nfl-2026-09-20.json` — permanent history,
#    append-only, never edited), 25 props across its games. The live props
#    board is diffed the same way as an EXTRA, asserted when it builds a
#    card and a note() when it does not.
# ⛔ And the row floor is HARDER than it was: 5 rows that carry both a
#    projection and a confidence, not 5 rows of anything.
# ══════════════════════════════════════════════════════════════════════
_CARD_FX = os.path.join(ROOT, "picks", "fb-nfl-2026-09-20.json")
_with, _without = tree(True), tree(False)
ck(os.path.exists(os.path.join(_with, "dossier_fb.py"))
   and not os.path.exists(os.path.join(_without, "dossier_fb.py")),
   "⚠️ the WITH tree holds `dossier_fb.py` and the WITHOUT tree does not",
   "⛔ rule 67 — `copy_module(\"collect\")` brings the dossier along, and "
   "two trees that both hold it diff to identical whatever the card does")


def _card(d):
    f = sorted(glob.glob(os.path.join(d, "picks", "fb-nfl-2*.json")))
    return json.load(open(f[-1], encoding="utf-8")) if f else None


def _fresh_card(d, props=None):
    """Build the card in `d` with NO committed card beside it, from
    `props` (a props board) or, when None, the tree's own live copy."""
    for _f in glob.glob(os.path.join(d, "picks", "fb-nfl-*.json")):
        os.remove(_f)
    _pp = os.path.join(d, "data/nfl/latest/props.json.gz")
    if props is None:
        _src = os.path.join(ROOT, "data/nfl/latest/props.json.gz")
        if os.path.exists(_src):
            shutil.copy(_src, _pp)
    else:
        with gzip.open(_pp, "wt") as _fh:
            json.dump(props, _fh)
    _rc_, _o_ = run(d, "card_fb.py")
    return _rc_, _o_, _card(d)


def _props_from(card):
    """A props board holding exactly the priced props a published card
    carried, in the shape `props-board` writes (one priced side each)."""
    games = {}
    for p in card.get("picks") or []:
        g = games.setdefault(p.get("game_id"), {
            "id": p.get("game_id"), "home": p.get("home"),
            "away": p.get("away"), "commence": p.get("commence"), "props": []})
        g["props"].append({"player": p.get("player"), "market": p.get("market"),
                           "line": p.get("line"),
                           "sides": {p.get("side"): {
                               "price": p.get("price"), "book": p.get("book"),
                               "link": p.get("link"), "n_books": p.get("n_books")}}})
    return {"kind": "FIXTURE", "league": "nfl", "games": list(games.values())}


def _diff(cw, co, where):
    _pw = [p.get("projection") for p in cw.get("picks") or []]
    _po = [p.get("projection") for p in co.get("picks") or []]
    ck(_pw == _po,
       "🔴🔴 EVERY PROJECTION IS IDENTICAL, WITH AND WITHOUT THIS FILE (%s)"
       % where,
       "⛔ THE LICENCE FOR ADDING A TOOL BESIDE THE CARD IS THAT IT "
       "CANNOT REACH IT. with=%s without=%s" % (_pw[:4], _po[:4]))
    ck([p.get("confidence") for p in cw["picks"]]
       == [p.get("confidence") for p in co["picks"]],
       "🔴 ...and every confidence number too (%s)" % where,
       "a projection is not the only number a reader acts on")
    ck(json.dumps(cw.get("picks"), sort_keys=True)
       == json.dumps(co.get("picks"), sort_keys=True),
       "🔴🔴 ...and the whole board is byte-identical (%s)" % where,
       "⛔ the cards are DIFFED, not asserted about")


# ── 3a. THE PROOF: a planted props board, every day ────────────────────
_PFX = _props_from(json.load(open(_CARD_FX, encoding="utf-8"))
                   if os.path.exists(_CARD_FX) else {})
_rcw, _ow, _cw = _fresh_card(_with, _PFX)
_rco, _oo, _co = _fresh_card(_without, _PFX)
ck((_rcw, _rco) == (0, 0), "both cards build from the planted props board",
   (_ow + _oo)[-400:])
ck(_cw and _co, "⚠️ both trees produced a FRESH card to compare",
   "⛔ comparing two absent cards is the emptiest possible pass, and a "
   "committed card left in the tree would be compared instead")
if _cw and _co:
    _full = [p for p in _cw.get("picks") or []
             if p.get("projection") is not None and p.get("confidence") is not None]
    ck(len(_full) >= 5,
       "⚠️ ...carrying rows to compare (%d, %d with a projection and a "
       "confidence)" % (len(_cw.get("picks") or []), len(_full)),
       "⛔ rule 67 — a diff of rows that carry no number compares nothing. "
       "Planted from %s" % os.path.relpath(_CARD_FX, ROOT))
    _diff(_cw, _co, "planted props")

# ── 3b. THE LIVE PROPS BOARD, AS AN EXTRA ─────────────────────────────
_rcw2, _ow2, _cw2 = _fresh_card(_with)
_rco2, _oo2, _co2 = _fresh_card(_without)
if _cw2 and _co2 and (_cw2.get("picks") or _co2.get("picks")):
    ck((_rcw2, _rco2) == (0, 0), "   both cards build from the LIVE props board",
       (_ow2 + _oo2)[-400:])
    _diff(_cw2, _co2, "live props, %d rows" % len(_cw2.get("picks") or []))
else:
    note("   the live props board built no card with rows today (rc %s/%s) — "
         "the planted board above is the proof" % (_rcw2, _rco2))
_SRC = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
ck("dossier" not in _SRC.lower(),
   "⛔ card_fb.py does not mention the dossier at all",
   "🔴 the diff above is the proof; this is the reason it holds")

section("4. 🔴 THE VS-POSITION RANK CARRIES ITS MEASURED VERDICT")
_vs = [s for g in _docs for s in g["sections"] if s["name"] == "Versus position"]
ck(_vs, "⚠️ there are vs-position sections to check (%d)" % len(_vs))
# ⚠️ RULE 67 `[2026-09-28]`: the phrase checks below read only the sections
#    that ANSWER, so with none OK every one of them passed over nothing.
#    The planted games' defences are in the stored table on any day.
ck(any(s["state"] == "OK" for s in _vs),
   "⚠️ ...and at least one of them answers (%d OK)"
   % sum(1 for s in _vs if s["state"] == "OK"),
   "⛔ rule 67 — a verdict check over no OK section proves nothing")
for _phrase in ("4.4 rushing yards", "27 yards", "DISPLAYED, NOT APPLIED",
                "moves no projection"):
    ck(all(_phrase in (s.get("verdict") or "") for s in _vs if s["state"] == "OK"),
       "   the verdict states %r" % _phrase,
       "⛔ IT WAS DROPPED IN BOTH SPORTS. A rank with no scale beside it "
       "reads as a reason to bet, and the measurement is what stops that")
ck(all(_phrase in (s.get("why") or "") for s in _vs if s["state"] == "OK"
       for _phrase in ("DISPLAYED, NOT APPLIED",)),
   "   ...and it travels in `why` too, not only in a field a reader "
   "might not render")

section("5. ⛔ NOTHING IS A MODEL, AND MLB IS UNTOUCHED")
_bases = {s.get("basis") for g in _docs for s in g["sections"]}
ck("MODEL" not in _bases,
   "🔴🔴 NO SECTION IS LABELLED MODEL",
   "⛔ this artifact predicts nothing. A MODEL label would be a claim it "
   "has not earned and a test it has not passed. Got %s" % sorted(
       _bases, key=str))
ck(_bases <= {"MARKET", "DESCRIPTIVE", None}, "   only MARKET / DESCRIPTIVE",
   str(sorted(_bases, key=str)))
# ⚠️ EXACT KEYS, RECURSIVELY — not the word anywhere. A head-to-head
#    meeting legitimately carries `home_score` and `away_score`: those are
#    results that happened, which is the whole point of section 2. What
#    must not exist is a key that IS a judgement: a `score` for the game,
#    a `rating`, a `pick`. The loose form failed on real history and would
#    have forced the honest data out to satisfy the check.
_FORBIDDEN = {"score", "rating", "grade", "confidence", "edge", "pick",
              "lean", "bet", "recommendation", "verdict_score", "overall"}


def _keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            for x in _keys(v):
                yield x
    elif isinstance(o, list):
        for v in o:
            for x in _keys(v):
                yield x


_judge = sorted({k for g in _docs for k in _keys(g.get("sections"))
                 if k.lower() in _FORBIDDEN})
ck(not _judge,
   "🔴🔴 NO SECTION CARRIES A KEY THAT IS A JUDGEMENT",
   "⛔ a combined number is the NEXT task and it needs a pre-registered "
   "test first. Found %s" % _judge)
_hist = sorted({k for g in _docs for k in _keys(g.get("sections"))
                if k in ("home_score", "away_score")})
ck(_hist == ["away_score", "home_score"],
   "   ✅ ...while prior meetings still carry the scores that happened",
   "⛔ THE CHECK MUST NOT FORCE OUT HONEST HISTORY. A result is a fact; a "
   "score for THIS game would be a claim. Got %s" % _hist)
# ⚠️ AND BY VALUE, ON THE PLANTED MEETING `[2026-09-28]`. The key check
#    above needed a live game with a rematch inside 365 days — a 1-game
#    board without one turned it red on correct code — and it passes on a
#    meeting whose scores are all None. The planted meeting is 23-20.
_M = _FX["meeting"] or {}
_g0 = next((g for g in _docs if _PICK
            and g.get("board_id") == "fixture-%s" % _PICK[0]["id"]), {})
_m0 = [m for s in (_g0.get("sections") or []) if s.get("n") == 2
       for m in (s.get("meetings") or []) if m.get("date") == _M.get("start", "")[:10]]
ck(len(_m0) == 1 and (_m0[0].get("home"), _m0[0].get("away"),
                      _m0[0].get("home_score"), _m0[0].get("away_score"))
   == (_M.get("home"), _M.get("away"), 23, 20),
   "   🔴 ...the planted prior meeting reads %s %s-%s %s, as it happened"
   % (_M.get("home"), _M.get("home_score"), _M.get("away_score"), _M.get("away")),
   "⛔ a meeting with the score dropped, or the sides swapped, is a record "
   "of a game that did not happen. Got %s" % _m0)
_livem = [m for g in _docs if not _fixture(g.get("board_id"))
          for s in (g.get("sections") or []) if s.get("n") == 2
          for m in (s.get("meetings") or [])]
if _livem:
    ck(all("home_score" in m and "away_score" in m for m in _livem),
       "   ✅ ...and so do the live slate's %d meeting(s)" % len(_livem),
       "Got %s" % _livem[:2])
else:
    note("   no live game has a prior meeting inside 365 days today — the "
         "planted meeting carries the check")
ck("data/mlb" not in _DSRC and '"mlb"' not in _DSRC,
   "⛔ the builder has no MLB path at all — the absence IS the guard",
   "🔴 CLAUDE.md: the freeze forbids a scheduled check that reads MLB "
   "state, and a path nobody can flip is stronger than a flag")
# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 NO SECTION ASKS THE ENVIRONMENT WHICH LEAGUE IT IS DESCRIBING.
# `[2026-09-17, found in my own college port before it landed]`
# `build(league)` takes a league and hands every section the matching
# `data` root. A section reading the module-level `LEAGUE` instead is
# reading `os.environ` — so `build("ncaaf")` under `LEAGUE=nfl` would
# emit a document about college carrying a section written for the NFL.
# ⛔ GUARDING THE CLASS, NOT THE INSTANCE. The port put this in section 6
# only, but the defect belongs to all eight and to every section added
# later, so the check sweeps `s_*` by AST rather than naming the one that
# had it (CLAUDE.md: rules 246 and 130, guarding the instance, twice).
# ⚠️ Section 6 is the only one that has ever needed the league at all, so
# a search for the STRING would pass on a repo where nothing asks —
# hence the sweep is over the functions and the emptiness is asserted
# against a non-empty list of them.
# ══════════════════════════════════════════════════════════════════════
_sfns = [n for n in ast.parse(_DSRC).body
         if isinstance(n, ast.FunctionDef) and n.name.startswith("s_")]
ck(len(_sfns) == 9,
   "⚠️ the sweep below really does see all nine sections, signal 9 included (%d)"
   % len(_sfns),
   "⛔ rule 67: a sweep over an empty or short list of functions proves "
   "nothing. Found %s" % [n.name for n in _sfns])
_envlg = sorted({n.name for n in _sfns
                 for x in ast.walk(n)
                 if isinstance(x, ast.Name) and x.id == "LEAGUE"})
ck(not _envlg,
   "🔴🔴 ...AND NONE OF THEM READS THE MODULE-LEVEL `LEAGUE`",
   "⛔ that global is `os.environ.get(\"LEAGUE\")`, and the league a "
   "document is FOR arrives as an argument. A section that disagrees "
   "with its own document is misinformation, not a gap. Reads it: %s"
   % _envlg)
# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 ~~"A NON-NFL LEAGUE EXITS CLEAN AND SAYS IT IS NOT BUILT"~~ —
# THAT CHECK IS GONE BECAUSE THE BEHAVIOUR IT GUARDED WAS THE DEFECT.
# `return 0` on an unimplemented path is SUCCESS: the college card built,
# the chained call ran, and 88 board games carried no signals at all
# while every check in this repo passed. College is built now, and
# `test_dossier_coverage.py` holds that on the class — every league
# `collect.yml` routes to `card-fb`, derived, not listed.
# ✅ WHAT REPLACES IT IS STRICTLY STRONGER: a league NOT in the built set
# must exit NON-ZERO, so the next unimplemented league is visible to
# every watcher instead of only to the log.
# ══════════════════════════════════════════════════════════════════════
_rc_un, _out_un = run(tree(), "dossier_fb.py", league="kabaddi")
ck(_rc_un != 0,
   "🔴🔴 AN UNBUILT LEAGUE EXITS NON-ZERO (rc=%s)" % _rc_un,
   "⛔ THIS IS THE WHOLE FINDING. `return 0` made a product hole "
   "invisible to every watcher — the more carefully the refusal was "
   "written, the less anything noticed. Got: %s" % _out_un[-200:])
ck("is not one of" in _out_un and "kabaddi" in _out_un,
   "   ...and says which league and what the built set is",
   "⛔ a refusal that does not name itself cannot be acted on. Got: %s"
   % _out_un[-200:])
import dossier_fb as _DF  # noqa: E402
ck("ncaaf" in getattr(_DF, "LEAGUES_BUILT", ()),
   "✅ ...and college is IN the built set now",
   "🔴 88 board games had no signals 1-8 at all, on the biggest slate "
   "of the week. Built: %s" % (getattr(_DF, "LEAGUES_BUILT", ()),))

section("6. ⚠️ THE MEASUREMENTS THIS FILE STANDS ON ARE WRITTEN DOWN")
for _claim in ("189 of those carry BOTH", "285 of 285",
               "FIRST-HALF MARKETS ARE NOT HELD"):
    ck(_claim in _DSRC, "   the file records %r" % _claim,
       "⛔ rule 166: a number written down is a claim about the world. "
       "These were measured on 2026-09-17 and the source says so")
# ⚠️ THE POSSESSION MEASUREMENTS MOVED, THEY DID NOT VANISH. The probe
#    numbers this file used to check for (`drive_time_of_possession`,
#    `2457 of 2491`) were the reason section 6 could not answer; the
#    section answers now, and the numbers that govern WHAT it answers
#    live in `possession.py`. Rule 166 applies to them just the same.
_PSRC = open(os.path.join(ROOT, "possession.py"), encoding="utf-8").read()
for _claim in ("min 0.30", "median 0.87", "r = +0.6426",
               "202 of 217", "269 of 269 regulation games"):
    ck(_claim in _PSRC, "   `possession.py` records %r" % _claim,
       "⛔ rule 166. Measured 2026-09-17 over the whole 2019 college "
       "season and the whole 2025 NFL season")
_top = [s for g in _docs for s in g["sections"]
        if s["name"] == "Time of possession"]
# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 ~~"every section 6 reports UNAVAILABLE"~~ — REPLACED 2026-09-21.
# ⛔ IT ASKED THE WRONG QUESTION: it asserted a FACT ABOUT THE CALENDAR
#    ("no possession table exists yet"), so it went red the moment the
#    table shipped — `top-2026.json.gz` landed 2026-09-20 08:53Z and this
#    file failed every collect run from then on, on CORRECT output.
# ✅ THE REPLACEMENT IS HARDER, NOT SOFTER. It now asks the question in
#    BOTH states and checks the section against the DISK, where the old
#    form only ever checked one state and never looked at the disk:
#      1. an OK section is DESCRIPTIVE, names at least one team, and every
#         share is a real fraction whose minutes say the same thing;
#      2. every UNAVAILABLE section still names a remedy;
#      3. a section may not claim "no figures are stored" while the table
#         IS on disk — nor answer OK while it is not;
#      4. and the ABSENT case is DRIVEN on a tree with the table removed,
#         so the old assertion still holds exactly where it is true.
# ══════════════════════════════════════════════════════════════════════
ck(bool(_top), "⚠️ there are section-6 rows to check (%d)" % len(_top),
   "⛔ rule 67 — an empty sweep proves nothing")
_ok6 = [s for s in _top if s["state"] == "OK"]
_bad6 = []
for s in _ok6:
    bt = s.get("by_team") or {}
    if s.get("basis") != "DESCRIPTIVE" or not bt:
        _bad6.append(("basis/by_team", s.get("basis"), list(bt)))
    for t, v in bt.items():
        sh = v.get("share")
        spg = v.get("seconds_per_game")
        if not (isinstance(sh, (int, float)) and 0 < sh < 1):
            _bad6.append((t, "share", sh))
        elif not (isinstance(spg, int)
                  and v.get("minutes") == "%d:%02d" % divmod(spg, 60)
                  and abs(spg - sh * 3600) <= 60):
            _bad6.append((t, "minutes/seconds disagree", v))
ck(not _bad6,
   "🔴 every OK section 6 is DESCRIPTIVE, names a team, and its shares "
   "are real fractions whose minutes agree (%d OK)" % len(_ok6),
   "⛔ a possession share of 0, 1 or more is a join fault, and minutes "
   "that disagree with the share are two sources for one fact (rule 66). "
   "Bad: %s" % _bad6[:4])
ck(all(s["state"] == "OK" or "remedy" in s for s in _top),
   "   ...and every section that is not OK names what would fix it",
   "a gap with no remedy is a complaint")
# ══════════════════════════════════════════════════════════════════════
# 🔴 AND THE REFUSAL WEEK 1 PRODUCES ON EVERY GAME NAMES ONE TOO.
# `[measured 2026-09-28]` When the table exists but neither team has a
# game before this kickoff — every game of week 1, every season — the
# section said "a possession file exists but carries neither" and named
# NO remedy, so the check above went red on correct output every week 1
# and was never asked on any other week. ✅ The builder now names one, and
# the case is PLANTED: a game dated 30 days before every stored row.
# ══════════════════════════════════════════════════════════════════════
_nr = next((g for g in _docs if _FX["no_row_id"]
            and g.get("board_id") == _FX["no_row_id"]), {})
_nr6 = next((s for s in (_nr.get("sections") or []) if s.get("n") == 6), {})
ck(bool(_nr6.get("state") == "UNAVAILABLE" and _nr6.get("remedy")
        and "carries neither" in (_nr6.get("why") or "")),
   "🔴 a game neither team has an earlier possession row for refuses AND "
   "names a remedy (planted, %s)" % (_nr.get("commence") or "missing")[:10],
   "⛔ a gap with no remedy is a complaint, and week 1 is this gap on every "
   "game. Got %s / %r / remedy %r" % (_nr6.get("state"),
                                     (_nr6.get("why") or "")[:80],
                                     _nr6.get("remedy")))
# ══════════════════════════════════════════════════════════════════════
# 🔴 ~~`_TOPF = glob(top-[0-9]{4}.json.gz)` — ANY season's table~~
# REPLACED 2026-09-28. ⛔ The builder reads `top-<the season it builds>`
# only (`s_possession`), so at the season rollover — `schedule-2027` on
# disk, `top-2027` not yet — the old glob found `top-2026`, demanded an OK
# section, and went red on correct output. ✅ This reads the season the
# document itself names, and `plant()` guarantees that table in this tree
# (the stored one, or a planted one while the calendar has none), so the
# present-case question is asked on every day. The ABSENT case is driven
# below on a tree with every table removed.
# ══════════════════════════════════════════════════════════════════════
_TOPF = os.path.join(_d, "data/nfl/latest/top-%s.json.gz" % _D.get("season"))
_claims_none = [s for s in _top
                if "No time-of-possession figures are stored" in (s.get("why") or "")]
ck(os.path.exists(_TOPF),
   "⚠️ the possession table for the season the builder reads is on disk "
   "(%s)" % os.path.basename(_TOPF),
   "⛔ rule 67 — the question below needs it; `plant()` writes it")
ck(os.path.exists(_TOPF) and not _claims_none and _ok6,
   "🔴🔴 the table is on disk (%s), so NO section says it is not, and "
   "the section answers" % os.path.basename(_TOPF),
   "⛔ a page saying 'nothing is stored' beside a stored table is the "
   "section lying about the disk. %d claim none, %d OK"
   % (len(_claims_none), len(_ok6)))

# 4. THE ABSENT CASE, DRIVEN — the old assertion, exactly where it holds.
_d6 = tree()
for _f in glob.glob(os.path.join(_d6, "data/nfl/latest/top-[0-9][0-9][0-9][0-9].json.gz")):
    os.remove(_f)
_rc6, _out6 = run(_d6, "dossier_fb.py")
_top6 = [s for g in (_load(os.path.join(_d6, "data/nfl/latest/dossiers.json.gz"))
                     .get("dossiers") or [])
         for s in g["sections"] if s["name"] == "Time of possession"]
ck(_rc6 == 0 and _top6
   and all(s["state"] == "UNAVAILABLE" and "remedy" in s for s in _top6),
   "🔴 table removed: every section 6 reports UNAVAILABLE and names a "
   "remedy (%d)" % len(_top6),
   "⛔ the probe confirms a field, not an artifact. rc=%s %s"
   % (_rc6, sorted({s["state"] for s in _top6})))
shutil.rmtree(_d6, ignore_errors=True)
section("7. 🔴🔴 NO VERDICT MAY REACH THE PUBLISHED FILE")
# ⛔ THE ONE BOUNDARY THIS FILE EXISTS TO HOLD, AND NOTHING HELD IT.
#    `[Sam, 2026-09-17]` `"score": 0.73, "confidence": 88` beside
#    `"sections": [` reached the PUBLISHED dossiers.json.gz with the suite
#    fully green. Section 5 walked `sections` and never looked at the
#    dossier's own frame.
# ✅ THE GATE IS NOW IN THE BUILDER: it refuses to write at all.
import dossier_fb as DF  # noqa: E402

_bad, _miss = DF.audit(_D)
# ⚠️ `_D` ALWAYS HOLDS THE PLANTED GAMES `[2026-09-28]`, so this walk has
#    real content on any day; on an empty live board it used to walk a
#    document with no games in it.
ck(_D.get("dossiers") and not _bad,
   "🔴🔴 THE REAL DOCUMENT CARRIES NO NUMERIC JUDGEMENT FIELD",
   "⛔ a report that scores a game is a model, and a model needs a "
   "pre-registered test this artifact does not have. Found %s" % _bad[:5])
# ══════════════════════════════════════════════════════════════════════
# 🔴 ~~`ck(not _miss)` over the LIVE document~~ REPLACED 2026-09-28: IT
# ASKED THE WRONG QUESTION OF THE LIVE SLATE.
# ⛔ Whether `meetings` (or `weather`, or `closing`) appears is a fact
#    about the SLATE: the builder struck exactly this refusal on
#    2026-09-19 as a guard firing on correct data, and now only REPORTS it
#    as `carried_absent` (dossier_fb.py, beside `CARRIED`, and `build()`).
#    Measured: a 1-game board with no rematch (IND@WAS) turned this red —
#    "Stale: ['meetings']" — on correct output.
# ✅ THE SAME QUESTION, ASKED WHERE THE ANSWER IS KNOWN, AND NO EASIER: the
#    planted slate carries every `CARRIED` subtree by construction (its
#    prior meeting, its final games' closing lines, its venues), and the
#    planted games are a SUBSET of the document the old check read — so
#    every name appearing on the planted slate implies it appeared in the
#    whole document. Passing the new check implies passing the old one on
#    the same run. The live result is REPORTED; the static half (every
#    name is a key this module emits) is `test_dossier_coverage.py`'s.
# ══════════════════════════════════════════════════════════════════════
_PL = dict(_D, dossiers=[g for g in (_D.get("dossiers") or [])
                         if _fixture(g.get("board_id"))])
_bp7, _mp7 = DF.audit(_PL)
ck(_PL["dossiers"] and not _bp7 and not _mp7,
   "⛔ ...and every carried-subtree exemption actually appears (on the "
   "PLANTED slate, %d games)" % len(_PL["dossiers"]),
   "🔴 THE EXCEPTION SURFACE MUST BE REAL. A name in `CARRIED` that no "
   "longer appears means the walk is skipping a subtree that is not "
   "there — and could be skipping one that is. Stale: %s, judgement "
   "fields: %s" % (_mp7, _bp7[:3]))
_mlive = DF.audit(dict(_D, dossiers=[g for g in (_D.get("dossiers") or [])
                                     if not _fixture(g.get("board_id"))]))[1]
note("   carried subtrees the LIVE slate alone does not carry: %s — a fact "
     "about today's games, which the builder reports as `carried_absent`"
     % (_mlive or "none"))

# ⚠️ A CLASS, NOT A BLOCKLIST OF THREE. The next synonym is what walks
#    past a list of `score`/`rank`/`confidence`.
for _syn in ("score", "confidence", "rating", "tier", "signal", "priority",
             "conviction_index", "strength", "ev", "edge_pts"):
    ck(DF._verdicty(_syn), "   `%s` reads as a judgement" % _syn,
       "⛔ a blocklist of three names is what the next synonym walks "
       "straight past")
for _fact in ("week", "season", "games", "n_meetings", "temp", "wind",
              "snap_pct", "flagged"):
    ck(not DF._verdicty(_fact),
       "   ✅ ...and `%s` does not" % _fact,
       "⛔ A GUARD THAT FIRES ON CORRECT DATA IS THE OTHER FAILURE. These "
       "are facts the dossier reports, not verdicts it forms")

# 🔴 DRIVEN END TO END, exactly as Sam drove it: inject the field, run the
#    builder, and assert NOTHING IS PUBLISHED.
_d3 = tree()
_dp = os.path.join(_d3, "dossier_fb.py")
_src3 = open(_dp, encoding="utf-8").read()
_inj = _src3.replace('            "sections": [',
                     '            "score": 0.73, "confidence": 88,\n'
                     '            "sections": [', 1)
ck(_inj != _src3, "⚠️ the injection landed in the copy",
   "⛔ a no-op edit proves nothing about the gate")
open(_dp, "w", encoding="utf-8").write(_inj)
_rc3, _out3 = run(_d3, "dossier_fb.py")
ck(_rc3 != 0,
   "🔴🔴 THE BUILDER REFUSES TO RUN CLEAN WITH A SCORE IN THE DOCUMENT",
   "⛔ Sam's own mutation reached the published file with the suite "
   "green. rc=%s out=%s" % (_rc3, _out3[-300:]))
ck(not os.path.exists(os.path.join(_d3, "data/nfl/latest/dossiers.json.gz")),
   "🔴🔴 ...AND WROTE NOTHING AT ALL",
   "⛔ publishing a verdict is the forbidden act; not publishing is the "
   "safe direction. A warning that still writes the file is not a gate")
ck("REFUSING TO WRITE" in _out3 and "score" in _out3,
   "   ...saying what it found and where",
   "Got: %s" % _out3[-300:])

# ⚠️ AND A VERDICT INSIDE A SECTION IS CAUGHT TOO, not only at the frame.
_d4 = tree()
_dp4 = os.path.join(_d4, "dossier_fb.py")
_s4 = open(_dp4, encoding="utf-8").read().replace(
    '    d["why"] = "Where it is played',
    '    d["rating"] = 0.5\n    d["why"] = "Where it is played', 1)
open(_dp4, "w", encoding="utf-8").write(_s4)
_rc4, _out4 = run(_d4, "dossier_fb.py")
ck(_rc4 != 0 and "REFUSING TO WRITE" in _out4,
   "🔴 a judgement inside a SECTION is refused as well",
   "⛔ the frame and the sections are the same rule. rc=%s %s"
   % (_rc4, _out4[-200:]))

section("8. 🔴🔴 IT RUNS ON A SCHEDULE — AND ON A MODE A CRON REACHES")
# ⛔ NOTHING ON THE SITE MAY DEPEND ON A MANUAL RUN (Sam's standing rule).
# 🔴 AND "IT IS WIRED" IS NOT ENOUGH — `t54.py`'s counter is wired into
#    `collect.py`'s `fb-record` branch, which NO cron routes to, so
#    `data/*/latest/t54.json` has never been written once. The class check
#    is: the mode this is chained to must be one some cron actually
#    reaches. ⚠️ The routing is read with `wfroutes.py`, the repo's one
#    parser for it — five hand-rolled copies of that regex is why it
#    exists (rule 117).
import wfroutes  # noqa: E402

_WF = open(os.path.join(ROOT, ".github/workflows/collect.yml"),
           encoding="utf-8").read()
_CSRC = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
_routes = wfroutes.parse_routes(_WF)
ck(len(_routes) >= 10, "⚠️ the routing table parsed (%d arm(s))" % len(_routes),
   "⛔ an empty routing table would make every claim below vacuous")
# 🔴🔴 ~~`"_dos.build(LEAGUE)" in collect.py`~~ — THAT CHECK WAS VACUOUS
#    AND DRIVING IT IS WHAT FOUND THAT. Commenting the call out as
#    `_rc = 0  # _dos.build(LEAGUE)` left the substring in place and all
#    70 checks green. A source string says the text exists; it says
#    NOTHING about whether the line runs.
# ✅ SO THE REAL `card-fb` MODE IS EXECUTED and the artifact is looked
#    for. Slower, and it is the only form that can tell a live wire from
#    a commented one.
_d5 = tree()
os.remove(os.path.join(_d5, "data/nfl/latest/dossiers.json.gz")) \
    if os.path.exists(os.path.join(_d5, "data/nfl/latest/dossiers.json.gz")) \
    else None
# ⛔ `converge-off`, BLANK KEYS, NO NETWORK `[2026-09-28]` — see
#    `run_collect`. Without them this run converged the whole tree: news
#    fetched from two outside sites on every run, and paid modes planned.
_rc5, _o5, _net5 = run_collect(_d5)
_made = os.path.exists(os.path.join(_d5, "data/nfl/latest/dossiers.json.gz"))
ck(_made,
   "🔴🔴 RUNNING THE REAL `card-fb` MODE PRODUCES THE DOSSIER",
   "⛔ a tool nothing runs is a tool that rots, and a SOURCE STRING "
   "cannot tell a live call from a commented-out one. rc=%s %s"
   % (_rc5, _o5[-300:]))
ck("dossier_fb[nfl]" in _o5,
   "   ...and the collector's own log says so",
   _o5[-250:])
ck("FRESHNESS SURVEY" not in _o5,
   "⛔ ...and `card-fb` ran ALONE: no converge pass, so no other mode, no "
   "network and no paid pull",
   "🔴 a test that converges the tree runs every stale mode in it — news "
   "from outside sites, and the paid pulls whenever a key is in the "
   "environment. Log: %s" % _o5[:300])
ck(not _net5,
   "⛔ ...and reached for NO network (%d attempt(s) refused)" % len(_net5),
   "🔴 a test must not depend on the network. Tried: %s" % _net5[:4])
_modes_with_crons = {m for _c, _lg, m in _routes}
ck("card-fb" in _modes_with_crons,
   "🔴🔴 ...AND A CRON ACTUALLY ROUTES TO `card-fb`",
   "⛔ THIS IS THE t54 TEST. Its counter sits in `fb-record`, which no "
   "cron reaches, so it has never run. Modes with crons: %s"
   % sorted(_modes_with_crons))
_n_cardfb = sum(1 for _c, _lg, m in _routes if m == "card-fb")
ck(_n_cardfb >= 2,
   "   ...on %d cron arm(s), not one that could vanish" % _n_cardfb)
ck("fb-record" not in _modes_with_crons,
   "   ⚠️ ...while `fb-record` still has none — the finding stands",
   "📌 THE FINDING THIS LINE RECORDED IS NOW FIXED `[#39]`: t54's counter "
   "moved to `card-fb`. What stays true is that `fb-record` is reached "
   "by no cron, so nothing may publish from it. Modes: %s"
   % sorted(_modes_with_crons))

note("✅ FIXED, NOT JUST REPORTED: `dossier_fb.py` is now chained to "
     "`card-fb`, which eight cron arms route to — no new cron, no CRON "
     "TOTAL change, and the existing data commit publishes the artifact. "
     "✅ AND THE t54 FINDING THIS FILE NAMED IS CLOSED TOO `[#39]`: its "
     "counter moved to `card-fb` and `t54.json` now exists. `fb-record` "
     "is still reached by no cron and nothing publishes from it any "
     "more — `test_accumulators.py` holds that on the class.")


section("9. 🔴🔴 EVERY READING IS ARCHIVED — `latest/` KEEPS NO HISTORY")
# ⛔ `latest/dossiers.json.gz` IS OVERWRITTEN ON ALL EIGHT DAILY `card-fb`
#    ARMS. Every section in it is a POINT-IN-TIME reading — the market
#    moves, season-to-date rows grow, an UNAVAILABLE section flips to OK —
#    so with no archive there is nothing to check against what happened,
#    and every day that passes is observations that cannot be recovered.
# ✅ DRIVEN THROUGH THE REAL `card-fb` MODE, for the reason section 8
#    gives: a source string says the text exists and says nothing about
#    whether the line runs.
_d9 = tree()
_lat9 = os.path.join(_d9, "data/nfl/latest/dossiers.json.gz")
for _f in glob.glob(os.path.join(_d9, "data/nfl/*/dossiers/*.json.gz")):
    os.remove(_f)
if os.path.exists(_lat9):
    os.remove(_lat9)
_rc9, _out9, _net9 = run_collect(_d9)
_arch9 = sorted(glob.glob(os.path.join(_d9, "data/nfl/*/dossiers/*.json.gz")))
ck(os.path.exists(_lat9),
   "⚠️ the run wrote `latest/dossiers.json.gz` as it always did",
   "⛔ if it wrote nothing at all the claim below would pass having "
   "checked nothing (rule 67). rc=%s %s" % (_rc9, _out9[-300:]))
ck("FRESHNESS SURVEY" not in _out9 and not _net9,
   "   ⛔ ...running `card-fb` alone, with no network (%d attempt(s))"
   % len(_net9),
   "🔴 Tried: %s. Log: %s" % (_net9[:4], _out9[:200]))
ck(len(_arch9) == 1,
   "🔴🔴 ...AND A DATED COPY BESIDE IT (%s)"
   % (os.path.relpath(_arch9[0], _d9) if _arch9 else "none"),
   "⛔ a report with no archive cannot be checked against what actually "
   "happened, and `latest/` is overwritten eight times a day. Found: %s"
   % [os.path.relpath(a, _d9) for a in _arch9])
if _arch9:
    _dd = os.path.relpath(_arch9[0], _d9).split(os.sep)
    ck(re.match(r"^\d{4}-\d{2}-\d{2}$", _dd[2])
       and re.match(r"^\d{4}\.json\.gz$", _dd[4]),
       "   ...at `data/<league>/<date>/dossiers/<HHMM>.json.gz`",
       "⛔ the shape the collector's own dated writes already use. Got %s"
       % _dd)
    ck(_load(_arch9[0]) == _load(_lat9),
       "   ...carrying the same document, not a summary of it",
       "⛔ an archive that drops fields is not an archive of this file")
    ck((_load(_arch9[0]).get("dossiers") or []) and
       len(_load(_arch9[0])["dossiers"][0].get("sections") or []) == _DFX.SECTIONS_DECLARED,
       "   ...with every declared section in it (%d game(s))"
       % len(_load(_arch9[0]).get("dossiers") or []),
       "⛔ an archive of an empty document proves nothing")

# 🔴 AND IT IS WRITE-ONCE. An archive a later run can rewrite is not an
#    archive — it is `latest/` with a longer name.
if _arch9:
    # ══════════════════════════════════════════════════════════════
    # 🔴 A SENTINEL AT EVERY MINUTE THE SECOND RUN COULD LAND IN, not
    #    only the first file. `[2026-09-24, found by the sweep]` With one
    #    sentinel the check bit only when both runs shared a MINUTE: once
    #    `card-fb` took longer, the clock rolled, the mutated writer made
    #    a NEW file, the sentinel survived and the mutation read VACUOUS.
    #    ✅ Now wherever the run lands it meets an earlier reading, so a
    #    writer that overwrites is red whatever the clock says.
    # ══════════════════════════════════════════════════════════════
    import daystore as _dsx
    _now9 = datetime.datetime.now(datetime.timezone.utc)
    _planted = sorted({_arch9[0]} | {
        os.path.abspath(_dsx.path(os.path.join(_d9, "data", "nfl"), "dossiers",
                                  _now9 + datetime.timedelta(minutes=_m)))
        for _m in range(-1, 61)})
    for _pp in _planted:
        os.makedirs(os.path.dirname(_pp), exist_ok=True)
        with gzip.open(_pp, "wt") as _fh:
            json.dump({"sentinel": "the earlier reading"}, _fh)
    _rc9b, _out9b, _net9b = run_collect(_d9)
    _again = sorted(glob.glob(
        os.path.join(_d9, "data/nfl/*/dossiers/*.json.gz")))
    ck("FRESHNESS SURVEY" not in _out9b and not _net9b,
       "   ⛔ the second run too ran `card-fb` alone, with no network (%d "
       "attempt(s))" % len(_net9b),
       "🔴 Tried: %s. Log: %s" % (_net9b[:4], _out9b[:200]))
    # ⚠️ ASKED OF THE BUILDER, NOT OF THE EXIT CODE. A run that never
    #    reached the builder would leave the sentinel intact too, which
    #    would make the claim below pass having tested nothing (rule 67).
    #    ~~"This sandbox has no network, so `card-fb` exits non-zero on the
    #    feeds it cannot reach"~~ — that was the converge pass this run no
    #    longer makes (`[2026-09-28]`, `converge-off`); the exit code still
    #    answers a different question from "did the builder run".
    ck("dossier_fb[nfl]" in _out9b,
       "⚠️ the second run really did rebuild the dossier",
       "⛔ the sentinel survives a run that did nothing, so this has to "
       "be established first. %s" % _out9b[-250:])
    # ══════════════════════════════════════════════════════════════
    # ⚠️ TIME-INDEPENDENT, AND THE FIRST DRAFT WAS NOT. `[2026-09-17]`
    # It asserted exactly ONE archive and that the log said "already
    # exists" — both true only when the two runs land inside the SAME
    # MINUTE. The runs take seconds, so it passed most of the time and
    # failed whenever the clock rolled between them. A check that
    # depends on when it is run is a check that will redden on correct
    # code, which is the other failure CLAUDE.md names.
    # ✅ THE REAL INVARIANT IS THAT THE EARLIER READING IS NEVER
    # REWRITTEN. `[2026-09-24]` The minute question is gone: every minute
    # the run can land in already holds a reading, so there is one branch.
    # ══════════════════════════════════════════════════════════════
    _norm9 = lambda xs: {os.path.normcase(os.path.abspath(x)) for x in xs}  # noqa: E731
    ck("already exists" in _out9b and _norm9(_again) == _norm9(_planted),
       "   ...it landed on an earlier reading, said so out loud, and wrote no new file",
       "⛔ a write-once that is silent about declining to write is a "
       "write-once nobody can audit. %s" % _out9b[-250:])
    _hit = [os.path.relpath(a, _d9) for a in _planted
            if _load(a).get("sentinel") != "the earlier reading"]
    ck(not _hit,
       "🔴🔴 ...AND LEAVES EVERY EARLIER READING EXACTLY AS IT WAS (%d planted)"
       % len(_planted),
       "⛔ WRITE-ONCE. A later run overwriting it destroys the very "
       "history this exists to keep. Rewritten: %s" % _hit)
    ck(os.path.getsize(_lat9) > 200,
       "   ...while `latest/` is refreshed as normal (%d bytes)"
       % os.path.getsize(_lat9),
       "⛔ the page reads `latest/`; write-once must not freeze it too")
note("💾 DATED AND WRITE-ONCE RATHER THAN ONE CUMULATIVE ARCHIVE, and "
     "the reason is measured (rule 285): git cannot delta-compress a "
     "gzip, so a one-row change rewrites the whole output and git stores "
     "each version IN FULL. 5.17 MiB for a 20-week season written this "
     "way against 2,896 MiB rewritten eight times a day — 560x.")
shutil.rmtree(_d9, ignore_errors=True)

section("10. 🧹 NOTHING THIS FILE MADE OUTLIVES IT")
# ⚠️ `[2026-09-28]` The atexit hook removes the parent on ANY exit; this
#    runs it now so a removal that silently fails (a Windows file lock, a
#    tree made outside the parent) is a red check rather than disk.
_n_made = len(_MADE)
_outside = [t for t in _MADE
            if os.path.dirname(os.path.abspath(t)) != os.path.abspath(_RUN_TMP)]
_cleanup()
_left = [t for t in _MADE + [_RUN_TMP] if os.path.exists(t)]
ck(_n_made >= 10 and not _outside and not _left,
   "⛔ every throwaway tree this file made is removed (%d trees)" % _n_made,
   "🔴 5,317 leaked `dossier-*` trees, about 82 GB, sat in %%TEMP%% before "
   "this. Outside the parent: %s. Still on disk: %s" % (_outside, _left))
