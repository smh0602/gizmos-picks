#!/usr/bin/env python3
"""🔴🔴 A PUBLISHED FOOTBALL ROW IS FROZEN THE MOMENT ITS GAME STARTS.

`CLAUDE.md`: *"`picks/<date>.json` already written — Published estimates
are a permanent record. ⛔ Never edit or delete one after its games have
started."*

`[measured 2026-09-19]` `picks/fb-nfl-2026-09-17.json` holds one game,
kickoff **2026-09-18T00:15:00Z**. It was rewritten SIX times after that
kickoff, the last at **2026-09-18T15:52:33Z** — 15h37m late — and the
rewrite changed **ten prices**, dropped twelve rows and added twelve
different ones:

    Keon Coleman   o1.5 receptions       +158 -> +145
    Dawson Knox    o12.5 reception yds   -113 -> -120
    Jared Goff     u0.5 rush yds         -175 -> -185
    Khalil Shakir  o4.5 receptions       +112 -> +110   … and six more

⛔ `record_fb.py` and `shadow_fb.py` grade against these files, so the
graded record was reconciled against numbers the board never showed at
the time anyone could have bet them.

⚠️ MLB LOOKS PROTECTED AND IS NOT. No `picks/<date>.json` appears in the
rewrite list — but that is the CARD CRON RUNNING ONCE A DAY, not a
guard. `card.py` returns None only when EVERY game on the board has
started, so a rebuild at 20:00Z on a slate with a 23:40Z game would
overwrite the morning's published rows exactly the same way. ⛔ MLB is
frozen and that is REPORTED, not fixed, here.

✅ PER ROW, NOT PER CARD, AND THAT IS THE WHOLE DESIGN DECISION. An NFL
Sunday runs 17:00Z to 03:00Z. Freezing the card whole at the first
kickoff would stop repricing the late games, which is a real loss and is
not what the rule asks for. The rule is about a row whose own game has
started.

# @vacuity 🔴🔴 a published row is not repriced after its game starts
#   file: card_fb.py
#   find:     keep = [r for r in old_rows if isinstance(r, dict)
#   with:     keep = [r for r in [] if isinstance(r, dict)
#
# @vacuity 🔴 ...and a started game never gains a NEW published row
#   file: card_fb.py
#   find:     fresh = [r for r in new_rows if isinstance(r, dict)
#   with:     fresh = [r for r in new_rows if isinstance(r, dict) or True
#
# @vacuity ⛔ ...and the writer actually calls the freeze
#   file: card_fb.py
#   find:     out, _frozen = freeze_published(
#   with:     out, _frozen = (lambda *a, **k: (a[0], 0))(
#
# @vacuity 🔴🔴 the MERGED list is capped, not each half
#   file: card_fb.py
#   find:     if cap is not None and len(out) > cap:
#   with:     if cap is not None and len(out) > cap and False:
#
# @vacuity 🔴🔴 a game line from a slate the list has left is not frozen back into it
#   file: card_fb.py
#   find:             if d and d != _gl_day:
#   with:             if d and d != _gl_day and False:
"""
import ast
import copy
import io
import json
import os
import tempfile

import card_fb as C
from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
BEFORE = "2026-09-17T18:00:00Z"        # before the kickoff below
AFTER = "2026-09-18T15:52:33Z"         # the moment of the real illegal write


def published(doc):
    """Write `doc` to a throwaway path and hand back the path."""
    fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(doc, fh)
    fh.close()
    return fh.name


def row(player, price, conf, commence, gid="G1", market="m", side="over",
        line=1.5):
    return {"player": player, "price": price, "confidence": conf,
            "commence": commence, "game_id": gid, "market": market,
            "side": side, "line": line}


# ════════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 DRIVEN ON A SLATE THAT IS HALF UNDER WAY")
# ════════════════════════════════════════════════════════════════════════
STARTED = "2026-09-18T00:15:00Z"        # kicked off before AFTER
LATER = "2026-09-20T17:00:00Z"          # has not kicked off at AFTER

OLD = {"date": "2026-09-17", "picks": [
    row("Started Sam", 158, 95, STARTED),
    row("Later Lou", -110, 70, LATER, gid="G2")]}

# what a rebuild at 15:52 the next day would have produced
NEW = {"date": "2026-09-17", "picks": [
    row("Started Sam", 145, 88, STARTED),          # repriced AFTER kickoff
    row("Later Lou", -120, 72, LATER, gid="G2"),   # legitimately repriced
    row("Late Arrival", -200, 64, STARTED, gid="G1", market="m2")]}

p = published(OLD)
try:
    got, n = C.freeze_published(copy.deepcopy(NEW), p, AFTER, log=lambda *a: None)
finally:
    os.unlink(p)
by = {r["player"]: r for r in got["picks"]}

ck("🔴🔴 a row whose game has started keeps its PUBLISHED price",
   by.get("Started Sam", {}).get("price") == 158,
   "⛔ THIS IS THE DEFECT. Ten rows of fb-nfl-2026-09-17.json were "
   "repriced 15 hours after the only game on it had finished. got %r"
   % (by.get("Started Sam", {}).get("price"),))
ck("🔴 ...and its published confidence too, not just the price",
   by.get("Started Sam", {}).get("confidence") == 95,
   "⛔ the confidence is the number Sam reads; repricing it after the "
   "fact is the same offence. got %r"
   % (by.get("Started Sam", {}).get("confidence"),))
ck("🔴 a row whose game has NOT started is still updated",
   by.get("Later Lou", {}).get("price") == -120,
   "⛔ THE OTHER FAILURE, and the expensive one: a card frozen whole at "
   "the first kickoff stops repricing the late games of an NFL Sunday. "
   "The rule is per ROW. got %r" % (by.get("Later Lou", {}).get("price"),))
ck("🔴🔴 a NEW row is never published on a game already under way",
   "Late Arrival" not in by,
   "⛔ the same misinformation in the other direction — an estimate "
   "published on a game whose result is partly known. got %s"
   % sorted(by))
ck("⛔ ...and a published row is never DROPPED either",
   len(got["picks"]) == 2 and n == 1,
   "⛔ the real rewrite dropped twelve published rows and added twelve "
   "others. picks=%d frozen=%d" % (len(got["picks"]), n))
ck("⚠️ the board is still sorted by confidence, descending",
   [r["confidence"] for r in got["picks"]] ==
   sorted([r["confidence"] for r in got["picks"]], reverse=True),
   "⛔ Sam's ordering rule survives the merge. got %r"
   % [r["confidence"] for r in got["picks"]])

# ── and BEFORE any kickoff nothing is frozen at all
p = published(OLD)
try:
    pre, npre = C.freeze_published(copy.deepcopy(NEW), p, BEFORE,
                                   log=lambda *a: None)
finally:
    os.unlink(p)
ck("✅ before kickoff the rebuild is untouched — all three rows, repriced",
   npre == 0 and len(pre["picks"]) == 3
   and {r["player"]: r["price"] for r in pre["picks"]}["Started Sam"] == 145,
   "⛔ a guard that fires early would freeze the morning card and stop "
   "the whole day's pricing. frozen=%d picks=%d" % (npre, len(pre["picks"])))

# ── and a card that has never been published is written as built
p = os.path.join(tempfile.mkdtemp(), "fb-nfl-2099-01-01.json")
first, nfirst = C.freeze_published(copy.deepcopy(NEW), p, AFTER,
                                   log=lambda *a: None)
ck("⚠️ a FIRST publication is never blocked by this",
   nfirst == 0 and len(first["picks"]) == 3,
   "⛔ the rule is 'never EDIT one after its games have started'. "
   "Refusing to create one at all would lose a slate. frozen=%d picks=%d"
   % (nfirst, len(first["picks"])))

# ════════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 AND ON THE REAL CARD THAT WAS CORRUPTED")
# ════════════════════════════════════════════════════════════════════════
REAL = os.path.join(ROOT, "picks", "fb-nfl-2026-09-17.json")
if not os.path.exists(REAL):             # pragma: no cover
    ck("the real card is in the repo", False,
       "⛔ this half of the file checks nothing without it — rule 67")
else:
    live = json.load(io.open(REAL, encoding="utf-8"))
    kicks = sorted({r.get("commence") for r in live["picks"]})
    ck("⚠️ the real card's slate really has started",
       bool(kicks) and kicks[0] < AFTER,
       "⛔ if this stops being true the drive below proves nothing "
       "(rule 67). earliest kickoff %r" % (kicks[0] if kicks else None,))
    # a rebuild that moves every single price by 10 points
    rebuild = copy.deepcopy(live)
    for r in rebuild["picks"]:
        if isinstance(r.get("price"), (int, float)):
            r["price"] = r["price"] + 10
    got2, n2 = C.freeze_published(rebuild, REAL, AFTER, log=lambda *a: None)
    same = all(a.get("price") == b.get("price")
               for a, b in zip(live["picks"], got2["picks"]))
    ck("🔴🔴 every one of the real card's %d rows survives a full reprice"
       % len(live["picks"]),
       same and len(got2["picks"]) == len(live["picks"]) and n2 >= len(live["picks"]),
       "⛔ driven against the artifact itself, not a fixture of it. "
       "rows %d -> %d, frozen %d, prices identical: %s"
       % (len(live["picks"]), len(got2["picks"]), n2, same))
    note("the real card: %d published row(s), all kicked off at %s, "
         "%d frozen on a rebuild dated %s"
         % (len(live["picks"]), kicks[0], n2, AFTER))

# ════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 A MERGE OF TWO CAPPED LISTS IS NOT A CAPPED LIST")
# ═══════════════════════════════════════════════════════════════════════
# ⛔ `[measured live 2026-09-19 19:10Z — the FIRST NCAAF card written
#    after this freeze shipped]` `picks/fb-ncaaf-2026-09-19.json` went from
#    **25 picks / 20 top plays at 15:52Z to 34 / 26**, and four of the five
#    frozen sections breached the cap the card declares on itself:
#    `picks 34>25 · top_plays 26>20 · parlays[2] 11>8 · parlays[3] 15>8 ·
#    parlays[4] 16>8 · sgp[2] 10>6 · sgp[3] 8>6`. **Every other card in
#    `picks/` was clean**, which is what pinned it to this commit.
# 🔴 `_merge_list` returned `keep + fresh` — every started row off the
#    published card, plus a full freshly-capped build. **Two lists of ≤N
#    make one list of ≤2N**, and the page was publishing 34 against a
#    `board_max` of 25 that it prints for the reader to check.
# ✅ THE RULE, AND THE ORDER IS THE WHOLE FIX: a FROZEN row is never
#    dropped to make room. The cap is filled from the frozen rows first,
#    the remainder from the highest-confidence fresh rows.
# ⚠️ ASKED OF EVERY SECTION `FREEZE_SECTIONS` NAMES, derived rather than
#    listed — `parlays` and `sgp` had no live assertion at all, which is
#    why nothing caught them.

CAPS = {sec: C.freeze_cap(sec) for sec in C.FREEZE_SECTIONS}
ck("⚠️ every frozen section declares a cap, and none is None",
   all(isinstance(v, int) and v > 0 for v in CAPS.values()),
   "⛔ rule 67: a section with no cap makes every check below vacuous "
   "FOR THAT SECTION and says nothing about it. Got %s" % CAPS)


def _slate(n, started, gid_prefix="C"):
    """`n` rows, the first `started` of them on games already under way."""
    return [row("P%02d" % i, -110, 100 - i,
                STARTED if i < started else LATER,
                gid="%s%d" % (gid_prefix, i), market="m%d" % i)
            for i in range(n)]


over_bad = []
for sec, cap in CAPS.items():
    # 9 already-published started rows, plus a full fresh build of `cap`.
    old_doc = {"board_max": CAPS["picks"], sec: _slate(cap, 9)}
    new_doc = {"board_max": CAPS["picks"], sec: _slate(cap, 0, "N")}
    q = published(old_doc)
    try:
        got, _n = C.freeze_published(copy.deepcopy(new_doc), q, AFTER,
                                     log=lambda *a: None)
    finally:
        os.unlink(q)
    rows = got.get(sec) or []
    if len(rows) > cap:
        over_bad.append((sec, len(rows), cap))

ck("🔴🔴 NO frozen section grows past its cap on a merge",
   not over_bad,
   "⛔ THIS IS THE LIVE DEFECT. `keep + fresh` is two capped lists added "
   "together. Over: %s" % over_bad)

# 🔴 AND THE TRIM COMES OFF THE FRESH ROWS, NEVER THE PUBLISHED ONES.
OLDP = {"board_max": 25, "picks": _slate(25, 9)}
NEWP = {"board_max": 25, "picks": _slate(25, 0, "N")}
q = published(OLDP)
try:
    capped, _ = C.freeze_published(copy.deepcopy(NEWP), q, AFTER,
                                   log=lambda *a: None)
finally:
    os.unlink(q)
_names = [r["player"] for r in capped["picks"]]
_frozen_in = [r["player"] for r in OLDP["picks"][:9]]
ck("🔴🔴 every already-published started row SURVIVES the trim",
   all(nm in _names for nm in _frozen_in),
   "⛔ a published row that has been graded against cannot be withdrawn "
   "to make room for a newer one — that is the record changing after the "
   "fact. missing=%s"
   % [nm for nm in _frozen_in if nm not in _names])
ck("✅ ...and the board is exactly at its cap, not under it",
   len(capped["picks"]) == 25,
   "⛔ trimming more than necessary throws away live pricing. got %d"
   % len(capped["picks"]))
ck("⚠️ ...and the fresh rows kept are the HIGHEST-confidence ones",
   sorted(r["confidence"] for r in capped["picks"] if r["player"] not in
          _frozen_in)[0] >= sorted(
              r["confidence"] for r in NEWP["picks"])[-16],
   "⛔ the cap must cut the weakest fresh rows, not an arbitrary tail")

# ⛔ AND WHEN THE FROZEN ROWS ALONE FILL THE CAP, NOTHING IS ADDED — AND
#    NOTHING IS DROPPED EITHER, EVEN IF THEY EXCEED IT.
OLDF = {"board_max": 25, "picks": _slate(30, 30)}
NEWF = {"board_max": 25, "picks": _slate(25, 0, "N")}
q = published(OLDF)
try:
    full, _ = C.freeze_published(copy.deepcopy(NEWF), q, AFTER,
                                 log=lambda *a: None)
finally:
    os.unlink(q)
ck("⛔ 30 published started rows are ALL kept, over the cap or not",
   len(full["picks"]) == 30,
   "⛔ a card written under an older, larger BOARD_MAX is a record, not "
   "an error. Un-publishing its rows to satisfy today's constant would "
   "rewrite history. got %d" % len(full["picks"]))
ck("🔴 ...and not one FRESH row is added on top of them",
   not [r for r in full["picks"] if r["player"].startswith("P")
        and r["game_id"].startswith("N")],
   "⛔ there is no room. Adding anyway is how 34 happened.")

# ⚠️ A DICT SECTION IS CAPPED PER KEY, WHICH IS HOW THE BUILDER APPLIES IT.
OLDD = {"parlays": {"2": _slate(8, 4), "3": _slate(8, 4)}}
NEWD = {"parlays": {"2": _slate(8, 0, "N"), "3": _slate(8, 0, "N")}}
q = published(OLDD)
try:
    dct, _ = C.freeze_published(copy.deepcopy(NEWD), q, AFTER,
                                log=lambda *a: None)
finally:
    os.unlink(q)
ck("⚠️ a dict section is capped PER KEY, not across the card",
   all(len(v) <= CAPS["parlays"] for v in dct["parlays"].values()),
   "⛔ `PARLAY_PER_SIZE` is per size. Got %s"
   % {k: len(v) for k, v in dct["parlays"].items()})

note("⚠️ WHAT THIS DOES NOT UNDO: `picks/fb-ncaaf-2026-09-19.json` was "
     "published over cap at 19:10Z and **13 of its 15 three-leg parlays "
     "and all 16 four-leg parlays had already started** by the time this "
     "was found. ⛔ Those rows are a published record and this fix will "
     "NOT withdraw them — the card self-heals to 25 picks and 20 top "
     "plays on the next build because only 16 and 11 of those had "
     "started, and the parlay lists stay long for today. ✅ What changes "
     "is that no card can GROW past its cap again.")


section("4. ⛔ AND THE WRITER CALLS IT — STRUCTURALLY, NOT IN PROSE")
# ════════════════════════════════════════════════════════════════════════
tree = ast.parse(io.open(os.path.join(ROOT, "card_fb.py"),
                         encoding="utf-8").read())
main = next((n for n in ast.walk(tree)
             if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
calls, dumps = [], []
for n in ast.walk(main or ast.Module(body=[], type_ignores=[])):
    if isinstance(n, ast.Call):
        nm = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
        if nm == "freeze_published":
            calls.append(n.lineno)
        if nm == "dump":
            dumps.append(n.lineno)
ck("🔴 `main` calls freeze_published",
   bool(calls),
   "⛔ a helper nothing calls is rule 78 in one file. A green test on an "
   "uncalled function is the exact shape of the two vacuous guards "
   "already open on issue #69.")
ck("🔴🔴 ...and it calls it BEFORE it writes either file",
   bool(calls) and bool(dumps) and min(calls) < min(dumps),
   "⛔ freezing after the write would publish the corruption and then "
   "correct it on the next run — the dated record and the `latest` "
   "pointer must never disagree about a row. freeze@%s dump@%s"
   % (calls, dumps))


section("5. 🔴🔴 A MOVED GAME-LINE SLATE DOES NOT DRAG THE OLD DAY WITH IT")
# ════════════════════════════════════════════════════════════════════════
# `[measured 2026-09-21]` the college card, dated 09-19 all week, printed
# game lines "for Thursday Sept 24" over 10 Saturday rows: every rebuild
# froze the started Saturday lines back INTO a list that had moved on.
# test_game_lines_day.py §5 was red on every collect run from 09-20.
SAT = "2026-09-19T20:00:00Z"            # started at NOW
SAT_LATE = "2026-09-20T02:30:00Z"       # a Saturday 10:30pm ET kickoff
THU = "2026-09-24T23:30:00Z"            # not started at NOW
NOW = "2026-09-21T19:00:00Z"
def gl(gid, when, price):
    return {"game_id": gid, "commence": when, "market": "h2h",
            "side": "home", "label": gid, "price": price}
OLDGL = {"date": "2026-09-19",
         "game_lines_meta": {"slate": "2026-09-19"},
         "game_lines": [gl("S1", SAT, -110), gl("S2", SAT_LATE, 120)]}
NEWGL = {"date": "2026-09-19",
         "game_lines_meta": {"slate": "2026-09-24", "is_next_slate": True},
         "game_lines": [gl("T1", THU, 105)]}
p = published(OLDGL)
try:
    got, _ = C.freeze_published(copy.deepcopy(NEWGL), p, NOW, log=lambda *a: None)
finally:
    os.unlink(p)
days = sorted({C.et_date(r["commence"]) for r in got["game_lines"]})
ck("🔴🔴 slate moved: every game line is on the list's declared day",
   days == ["2026-09-24"],
   "the list says Sept 24; it held %s" % days)
arch = got.get(C.GL_EARLIER) or {}
kept = [r for v in arch.values() for r in v]
ck("🔴🔴 ...and NO started row was deleted — both are kept VERBATIM as record",
   sorted(json.dumps(r, sort_keys=True) for r in kept)
   == sorted(json.dumps(r, sort_keys=True) for r in OLDGL["game_lines"]),
   "the permanent-record rule: a started row is never edited or deleted. "
   "archive=%s" % arch)
ck("⛔ ...filed under their own ET day, not the UTC string's",
   list(arch) == ["2026-09-19"],
   "a 10:30pm ET Saturday kickoff is 02:30Z Sunday; got %s" % list(arch))
ck("⛔ ...and the record is a dict, so no list-day check can mistake it "
   "for a published list",
   isinstance(arch, dict) and not isinstance(got.get(C.GL_EARLIER), list))

# carried forward, not duplicated, on the NEXT rebuild
p = published(got)
try:
    again, _ = C.freeze_published(copy.deepcopy(NEWGL), p,
                                  "2026-09-22T19:00:00Z", log=lambda *a: None)
finally:
    os.unlink(p)
ck("🔴 the record survives the next rebuild exactly once",
   again.get(C.GL_EARLIER) == arch,
   "a record that vanishes on the second build is a delete with a delay; "
   "got %s" % again.get(C.GL_EARLIER))

# slate UNCHANGED: the ordinary freeze is untouched
OLDSAME = {"date": "2026-09-19", "game_lines_meta": {"slate": "2026-09-19"},
           "game_lines": [gl("S1", SAT, -110)]}
NEWSAME = {"date": "2026-09-19", "game_lines_meta": {"slate": "2026-09-19"},
           "game_lines": [gl("S1", SAT, -150), gl("S3", "2026-09-19T23:00:00Z", 100)]}
p = published(OLDSAME)
try:
    same, _ = C.freeze_published(copy.deepcopy(NEWSAME), p,
                                 "2026-09-19T21:00:00Z", log=lambda *a: None)
finally:
    os.unlink(p)
s1 = [r for r in same["game_lines"] if r["game_id"] == "S1"]
ck("🔴 slate unchanged: a started line is still frozen at its PUBLISHED price",
   [r["price"] for r in s1] == [-110] and C.GL_EARLIER not in same,
   "got %s" % same)

# the live card, when it was built by a builder with this fix
_lp = os.path.join(ROOT, "picks", "fb-ncaaf-latest.json")
if os.path.exists(_lp):
    _d = json.load(open(_lp, encoding="utf-8"))
    if C.GL_EARLIER in _d or not any(
            C.et_date(r.get("commence")) != (_d.get("game_lines_meta") or {}).get("slate")
            for r in _d.get("game_lines") or []):
        note("live college card is consistent with this section")
    else:
        note("⚠️ the live college card predates this fix; the next card-fb "
             "run rewrites it. ⛔ Reported, not passed — "
             "test_game_lines_day.py §5 is the live assertion.")
