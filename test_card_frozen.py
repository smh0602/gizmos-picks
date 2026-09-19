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
section("3. ⛔ AND THE WRITER CALLS IT — STRUCTURALLY, NOT IN PROSE")
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
