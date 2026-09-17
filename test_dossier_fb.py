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
"""
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
#   find: skipped.append(_skip(g, "team name not in the code table"))
#   with: pass  # the skip is dropped instead of named
#
# @vacuity all EIGHT sections are written for every game
#   file: dossier_fb.py
#   find: s_personnel(teams, players, this_season),
#   with: # s_personnel(teams, players, this_season),
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
# @vacuity the dossier is ARCHIVED to a dated path, not only to latest/
#   file: dossier_fb.py
#   find: if os.path.exists(arch):
#   with: if True:
#
# @vacuity the dated archive is WRITE-ONCE and a later run cannot rewrite it
#   file: dossier_fb.py
#   find: if os.path.exists(arch):
#   with: if False:
#
# @vacuity nothing in the dossier is ever labelled MODEL
#   file: dossier_fb.py
#   find: MARKET, DESC = "MARKET", "DESCRIPTIVE"
#   with: MARKET, DESC = "MARKET", "MODEL"
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


def tree(with_dossier=True):
    """A throwaway repo with the data the builder and the card both read."""
    d = tempfile.mkdtemp(prefix="dossier-")
    shutil.copytree(os.path.join(ROOT, "data", "nfl"),
                    os.path.join(d, "data", "nfl"))
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
    return d


def _load(path):
    """The dossier file, or `{}` if the builder refused to write one."""
    if not os.path.exists(path):
        return {}
    try:
        return json.load(gzip.open(path, "rt"))
    except Exception:
        return {}


def run(d, script, league="nfl"):
    p = subprocess.run([sys.executable, script], cwd=d, timeout=600,
                       capture_output=True, text=True,
                       env=dict(os.environ, LEAGUE=league))
    return p.returncode, (p.stdout or "") + (p.stderr or "")


section("1. ⚠️ IT RUNS, AND EVERY BOARD GAME IS ACCOUNTED FOR")
_d = tree()
_rc, _out = run(_d, "dossier_fb.py")
ck(_rc == 0, "the builder exits clean", _out[-400:])
_P = os.path.join(_d, "data/nfl/latest/dossiers.json.gz")
ck(os.path.exists(_P), "⛔ ...and wrote a dossier file", _out[-300:])
_D = _load(_P)
_BOARD = json.load(open(os.path.join(ROOT, "data/nfl/latest/board.json"),
                        encoding="utf-8"))
_NG = len(_BOARD.get("games") or [])
ck(_NG >= 10, "⚠️ the real board has games to describe (%d)" % _NG,
   "⛔ a sweep over an empty board passes and proves nothing (rule 67)")
ck(_D.get("n_dossiers", 0) + len(_D.get("skipped") or []) == _NG,
   "🔴🔴 EVERY board game is either a dossier or a NAMED skip",
   "⛔ a game that simply vanished from the output is the shape this "
   "check exists for. %d dossier(s) + %d skip(s) vs %d board game(s)"
   % (_D.get("n_dossiers", 0), len(_D.get("skipped") or []), _NG))
ck(all(s.get("why") for s in (_D.get("skipped") or [])),
   "   ⛔ ...and every skip carries its reason",
   "🔴 a game missing from the output and a game with nothing to say are "
   "different facts. Skipped: %s" % (_D.get("skipped") or []))
note("   %d of %d board games produced a dossier; %d skipped."
     % (_D.get("n_dossiers", 0), _NG, len(_D.get("skipped") or [])))

section("1a. ⛔ AND THE 'OR NAMED' HALF IS DRIVEN, NOT ASSUMED")
# 🔴 CAUGHT BY DRIVING THE MUTATION, NOT BY READING. Every game on today's
#    board maps to a team code, so `skipped` is always empty and deleting
#    the line that records a skip changed NOTHING — the guard above was
#    half vacuous. A board with a name the code table does not hold is the
#    only thing that exercises it.
_d2 = tree()
_bp = os.path.join(_d2, "data/nfl/latest/board.json")
_b2 = json.load(open(_bp, encoding="utf-8"))
_b2["games"] = _b2["games"][:2] + [dict(_b2["games"][0],
                                        home="Nonexistent Ballclub",
                                        away="Detroit Lions")]
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
ck(len(_D2.get("skipped") or []) == 1,
   "🔴🔴 THE UNMAPPABLE GAME IS NAMED IN `skipped`",
   "⛔ a game that simply vanished from the output is indistinguishable "
   "from one with nothing to say. Got %s" % (_D2.get("skipped") or []))
ck(any(x.get("home") == "Nonexistent Ballclub"
       for x in (_D2.get("skipped") or [])),
   "   ...by the name the board used",
   "Got %s" % (_D2.get("skipped") or []))
ck(_D2.get("n_dossiers", 0) + len(_D2.get("skipped") or [])
   == len(_b2["games"]),
   "   ⛔ ...and the two still account for every board game",
   "%d + %d vs %d" % (_D2.get("n_dossiers", 0),
                      len(_D2.get("skipped") or []), len(_b2["games"])))

section("2. ⚠️ ALL EIGHT SECTIONS, EVERY GAME, PRESENT OR UNAVAILABLE")
_docs = _D.get("dossiers") or []
_WANT = ["Market", "Head to head", "Time of year", "This season",
         "Versus position", "Time of possession", "Personnel", "Venue"]
_bad = []
for _g in _docs:
    _names = [s.get("name") for s in _g.get("sections") or []]
    if _names != _WANT:
        _bad.append((_g.get("home"), _names))
ck(_docs and not _bad,
   "🔴🔴 ALL EIGHT SECTIONS, IN ORDER, ON EVERY GAME",
   "⛔ an absent section is indistinguishable from a section that found "
   "nothing — the `own_mean` shape. Offenders: %s" % _bad[:3])
_states = {s["state"] for g in _docs for s in g["sections"]}
ck(_states and _states <= {"OK", "UNAVAILABLE"},
   "   every section is OK or explicitly UNAVAILABLE", str(_states))
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
_with, _without = tree(True), tree(False)
_rcw, _ow = run(_with, "card_fb.py")
_rco, _oo = run(_without, "card_fb.py")
ck((_rcw, _rco) == (0, 0), "both cards build", (_ow + _oo)[-400:])


def _card(d):
    f = sorted(glob.glob(os.path.join(d, "picks", "fb-nfl-2*.json")))
    return json.load(open(f[-1], encoding="utf-8")) if f else None


_cw, _co = _card(_with), _card(_without)
ck(_cw and _co, "⚠️ both trees produced a card to compare",
   "⛔ comparing two absent cards is the emptiest possible pass")
if _cw and _co:
    _pw = [p.get("projection") for p in _cw.get("picks") or []]
    _po = [p.get("projection") for p in _co.get("picks") or []]
    ck(len(_pw) >= 5, "⚠️ ...carrying rows to compare (%d)" % len(_pw))
    ck(_pw == _po,
       "🔴🔴 EVERY PROJECTION IS IDENTICAL, WITH AND WITHOUT THIS FILE",
       "⛔ THE LICENCE FOR ADDING A TOOL BESIDE THE CARD IS THAT IT "
       "CANNOT REACH IT. with=%s without=%s" % (_pw[:4], _po[:4]))
    ck([p.get("confidence") for p in _cw["picks"]]
       == [p.get("confidence") for p in _co["picks"]],
       "🔴 ...and every confidence number too",
       "a projection is not the only number a reader acts on")
    ck(json.dumps(_cw.get("picks"), sort_keys=True)
       == json.dumps(_co.get("picks"), sort_keys=True),
       "🔴🔴 ...and the whole board is byte-identical",
       "⛔ the cards are DIFFED, not asserted about")
_SRC = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
ck("dossier" not in _SRC.lower(),
   "⛔ card_fb.py does not mention the dossier at all",
   "🔴 the diff above is the proof; this is the reason it holds")

section("4. 🔴 THE VS-POSITION RANK CARRIES ITS MEASURED VERDICT")
_vs = [s for g in _docs for s in g["sections"] if s["name"] == "Versus position"]
ck(_vs, "⚠️ there are vs-position sections to check (%d)" % len(_vs))
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
_DSRC = open(os.path.join(ROOT, "dossier_fb.py"), encoding="utf-8").read()
ck("data/mlb" not in _DSRC and '"mlb"' not in _DSRC,
   "⛔ the builder has no MLB path at all — the absence IS the guard",
   "🔴 CLAUDE.md: the freeze forbids a scheduled check that reads MLB "
   "state, and a path nobody can flip is stronger than a flag")
_rc_cf, _out_cf = run(tree(), "dossier_fb.py", league="ncaaf")
ck(_rc_cf == 0, "⚠️ a non-NFL league exits clean...", _out_cf[-200:])
ck("not built yet" in _out_cf,
   "   ...and says it is not built, rather than half-building",
   "⛔ a half-built college dossier would look complete and describe a "
   "different sport's data shape. Got: %s" % _out_cf[-200:])

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
ck(_top and all(s["state"] == "UNAVAILABLE" for s in _top),
   "🔴 time of possession reports UNAVAILABLE — the column EXISTS but "
   "nothing under data/ carries it",
   "⛔ the probe confirmed the field; it did NOT confirm an artifact, and "
   "claiming one would be the thing the brief forbade")
ck(all("remedy" in s for s in _top),
   "   ...and names what would fix it",
   "a gap with no remedy is a complaint")
section("7. 🔴🔴 NO VERDICT MAY REACH THE PUBLISHED FILE")
# ⛔ THE ONE BOUNDARY THIS FILE EXISTS TO HOLD, AND NOTHING HELD IT.
#    `[Sam, 2026-09-17]` `"score": 0.73, "confidence": 88` beside
#    `"sections": [` reached the PUBLISHED dossiers.json.gz with the suite
#    fully green. Section 5 walked `sections` and never looked at the
#    dossier's own frame.
# ✅ THE GATE IS NOW IN THE BUILDER: it refuses to write at all.
import dossier_fb as DF  # noqa: E402

_bad, _miss = DF.audit(_D)
ck(not _bad,
   "🔴🔴 THE REAL DOCUMENT CARRIES NO NUMERIC JUDGEMENT FIELD",
   "⛔ a report that scores a game is a model, and a model needs a "
   "pre-registered test this artifact does not have. Found %s" % _bad[:5])
ck(not _miss,
   "⛔ ...and every carried-subtree exemption actually appears",
   "🔴 THE EXCEPTION SURFACE MUST BE REAL. A name in `CARRIED` that no "
   "longer appears means the walk is skipping a subtree that is not "
   "there — and could be skipping one that is. Stale: %s" % _miss)

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
_rc5 = subprocess.run([sys.executable, "collect.py", "card-fb"], cwd=_d5,
                      timeout=1200, capture_output=True, text=True,
                      env=dict(os.environ, LEAGUE="nfl"))
_made = os.path.exists(os.path.join(_d5, "data/nfl/latest/dossiers.json.gz"))
ck(_made,
   "🔴🔴 RUNNING THE REAL `card-fb` MODE PRODUCES THE DOSSIER",
   "⛔ a tool nothing runs is a tool that rots, and a SOURCE STRING "
   "cannot tell a live call from a commented-out one. rc=%s %s"
   % (_rc5.returncode, (_rc5.stdout + _rc5.stderr)[-300:]))
ck("dossier_fb[nfl]" in (_rc5.stdout + _rc5.stderr),
   "   ...and the collector's own log says so",
   (_rc5.stdout + _rc5.stderr)[-250:])
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
_rc9 = subprocess.run([sys.executable, "collect.py", "card-fb"], cwd=_d9,
                      timeout=1200, capture_output=True, text=True,
                      env=dict(os.environ, LEAGUE="nfl"))
_out9 = (_rc9.stdout or "") + (_rc9.stderr or "")
_arch9 = sorted(glob.glob(os.path.join(_d9, "data/nfl/*/dossiers/*.json.gz")))
ck(os.path.exists(_lat9),
   "⚠️ the run wrote `latest/dossiers.json.gz` as it always did",
   "⛔ if it wrote nothing at all the claim below would pass having "
   "checked nothing (rule 67). rc=%s %s" % (_rc9.returncode, _out9[-300:]))
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
       len(_load(_arch9[0])["dossiers"][0].get("sections") or []) == 8,
       "   ...with all eight sections in it (%d game(s))"
       % len(_load(_arch9[0]).get("dossiers") or []),
       "⛔ an archive of an empty document proves nothing")

# 🔴 AND IT IS WRITE-ONCE. An archive a later run can rewrite is not an
#    archive — it is `latest/` with a longer name.
if _arch9:
    with gzip.open(_arch9[0], "wt") as _fh:
        json.dump({"sentinel": "the earlier reading"}, _fh)
    _rc9b = subprocess.run([sys.executable, "collect.py", "card-fb"],
                           cwd=_d9, timeout=1200, capture_output=True,
                           text=True, env=dict(os.environ, LEAGUE="nfl"))
    _again = sorted(glob.glob(
        os.path.join(_d9, "data/nfl/*/dossiers/*.json.gz")))
    _out9b = (_rc9b.stdout or "") + (_rc9b.stderr or "")
    # ⚠️ ASKED OF THE BUILDER, NOT OF THE EXIT CODE. This sandbox has no
    #    network, so `card-fb` exits non-zero on the feeds it cannot
    #    reach — and a run that never reached the builder would leave the
    #    sentinel intact too, which would make the claim below pass
    #    having tested nothing (rule 67).
    ck("dossier_fb[nfl]" in _out9b,
       "⚠️ the second run really did rebuild the dossier",
       "⛔ the sentinel survives a run that did nothing, so this has to "
       "be established first. %s" % _out9b[-250:])
    ck("already exists" in _out9b,
       "   ...and said out loud that it left the archive alone",
       "⛔ a write-once that is silent about declining to write is a "
       "write-once nobody can audit. %s" % _out9b[-250:])
    ck(len(_again) == 1,
       "   ...and added no second archive for the same minute (%d)"
       % len(_again),
       "Found: %s" % [os.path.relpath(a, _d9) for a in _again])
    ck(_load(_arch9[0]).get("sentinel") == "the earlier reading",
       "🔴🔴 ...AND LEAVES THE EARLIER READING EXACTLY AS IT WAS",
       "⛔ WRITE-ONCE. A later run overwriting it destroys the very "
       "history this exists to keep. Got %s" % str(_load(_arch9[0]))[:120])
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
