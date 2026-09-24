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
#   with: sched_row = sched_row or {"venue": home, "roof": "outdoors"}
#   if False:
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


def tree(with_dossier=True):
    """A throwaway repo with the data the builder and the card both read."""
    d = tempfile.mkdtemp(prefix="dossier-")
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
import dossier_fb as _DFX  # noqa: E402
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
_TOPF = glob.glob(os.path.join(_d, "data/nfl/latest/top-[0-9][0-9][0-9][0-9].json.gz"))
_claims_none = [s for s in _top
                if "No time-of-possession figures are stored" in (s.get("why") or "")]
if _TOPF:
    ck(not _claims_none and _ok6,
       "🔴🔴 the table is on disk (%s), so NO section says it is not, and "
       "the section answers" % os.path.basename(_TOPF[0]),
       "⛔ a page saying 'nothing is stored' beside a stored table is the "
       "section lying about the disk. %d claim none, %d OK"
       % (len(_claims_none), len(_ok6)))
else:
    ck(not _ok6,
       "🔴🔴 no table on disk, so NO section answers OK",
       "⛔ an OK section with no table under it is a number from nowhere")

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
