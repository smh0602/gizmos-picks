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
# @vacuity nothing in the dossier is ever labelled MODEL
#   file: dossier_fb.py
#   find: MARKET, DESC = "MARKET", "DESCRIPTIVE"
#   with: MARKET, DESC = "MARKET", "MODEL"
# ══════════════════════════════════════════════════════════════════════


def tree(with_dossier=True):
    """A throwaway repo with the data the builder and the card both read."""
    d = tempfile.mkdtemp(prefix="dossier-")
    shutil.copytree(os.path.join(ROOT, "data", "nfl"),
                    os.path.join(d, "data", "nfl"))
    os.makedirs(os.path.join(d, "picks"), exist_ok=True)
    for f in glob.glob(os.path.join(ROOT, "picks", "fb-nfl-*.json")):
        shutil.copy(f, os.path.join(d, "picks"))
    copy_module("card_fb", d)
    # ⚠️ `collect.py` IS COPIED BY HAND AND THAT IS DELIBERATE.
    #    `dossier_fb.py` does not IMPORT it — it parses `NFL_TEAMS` out of
    #    its source at runtime — so `copy_module`'s import walk cannot see
    #    the dependency. A runtime file read is not an import.
    shutil.copy(os.path.join(ROOT, "collect.py"), d)
    if with_dossier:
        copy_module("dossier_fb", d)
    return d


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
_D = json.load(gzip.open(_P, "rt")) if os.path.exists(_P) else {}
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
_D2 = json.load(gzip.open(os.path.join(_d2, "data/nfl/latest/dossiers.json.gz"),
                          "rt"))
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
for _claim in ("drive_time_of_possession", "2457 of 2491",
               "189 of those carry BOTH", "285 of 285",
               "FIRST-HALF MARKETS ARE NOT HELD"):
    ck(_claim in _DSRC, "   the file records %r" % _claim,
       "⛔ rule 166: a number written down is a claim about the world. "
       "These were measured on 2026-09-17 and the source says so")
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
note("📌 REPORTED, NOT FIXED: nothing runs `dossier_fb.py` on a schedule. "
     "It is a tool, exactly as `t54.py` was before its hook — and that "
     "hook landed in `collect.py`'s `fb-record` branch, which no cron "
     "fires, so `t54.json` has never been written once. ➡️ Wiring this "
     "means touching `collect.py` or a workflow, which this task did not "
     "ask for. Sam's call.")
