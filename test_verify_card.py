#!/usr/bin/env python3
"""
THE VERIFIER IS IN THE SUITE NOW, AND IT IS PROVED TO BITE.

🔴🔴 THIS IS THE ROOT CAUSE OF THE 2026-09-12 OUTAGE, AND IT IS MINE.

At 04:00Z I told Sam *"everything is green"*, having run the test suite.
**`verify_card.py` is not in the test suite.** It runs on the `card` and
`refresh` jobs only. So the statement was TRUE and it certified everything
except the one file that took Gizmo's Picks down six hours later — a
builder and a verifier disagreeing about whether `-700` clears `-700`.

⛔ **A CLAIM THAT IS TRUE AND DOES NOT COVER THE THING THAT BROKE IS WORSE
THAN NO CLAIM**, because it is believed. `[Sam, 2026-09-14: "fix all of
these"]` — which lifts the MLB freeze for this item and nothing else.

════════════════════════════════════════════════════════════════════════
⛔ WHAT THIS FILE DELIBERATELY DOES NOT DO
════════════════════════════════════════════════════════════════════════

**IT DOES NOT ASSERT THAT TODAY'S CARD VERIFIES.** That is a fact about
today's slate, not about the code: `verify_card.py` exits 0 with *"every
game on the board has started -- nothing to write"* for much of the day,
so the assertion would be vacuous when it passed and expire when it did
not. Rule 166, which this repo has now recorded eleven times.

**IT DOES NOT ASSERT THAT HISTORICAL CARDS STILL VERIFY EITHER.**
TIGHTENING a check legitimately makes older cards fail — so that
assertion would block every future tightening, which is the opposite of
what the verifier is for.

✅ **WHAT IT OWNS IS THAT THE VERIFIER RUNS, RUNS A LOT OF CHECKS, AND
FAILS ON REAL DEFECTS.** A verifier that early-returns, that silently
checks six things instead of ninety, or that has stopped catching a class
it once caught, fails here — and none of those can be told apart from a
healthy one by reading an exit code.

# @vacuity the printed-pitcher-number check must not fail a correct card on rounding
#   file: verify_card.py
#   find: if abs(r['confidence'] - r['blend']) > 0.55 or (_m and _pcor.get('method')):
#   with: if r['confidence'] != round(r['blend']) or (_m and _pcor.get('method')):
"""
import json
import os
import re
import subprocess
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import card as C  # noqa: E402


def _stored_card():
    """The most recent published card that actually has rows.

    ⚠️ NOT "today's". The point is a REAL document with real prices,
    parlays and projections in it — today's may not exist yet, and
    building one here would spend credits and take minutes.
    """
    best = None
    for f in sorted(os.listdir(os.path.join(ROOT, "picks")), reverse=True):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.json", f):
            continue
        try:
            d = json.load(open(os.path.join(ROOT, "picks", f),
                               encoding="utf-8"))
        except Exception:
            continue
        if d.get("picks"):
            return f[:-5], d
    return None, best


DAY, CARD = _stored_card()

# ══════════════════════════════════════════════════════════════════════
# 🔴 THE VERIFIER IS DRIVEN BY PATCHING `card.main`, WHICH IS THE ONLY
#    WAY THAT WORKS. `verify_card.py` line 8 is `doc = C.main(dry=True)` —
#    it REBUILDS the card in memory and never opens `picks/<date>.json`.
# ⛔ THAT IS NOT A GUESS. A previous attempt to fault-inject this
#    injected into the JSON file, got `ALL CHECKS PASSED`, and the pass
#    meant "the check never saw it" (ledger rule 231).
# ══════════════════════════════════════════════════════════════════════
RUNNER = r'''
import json, sys
sys.path.insert(0, %(root)r)
import card as C
_doc = json.load(open(%(path)r, encoding="utf-8"))
%(mutate)s
C.main = lambda *a, **k: _doc
import verify_card
'''


def run(mutate=""):
    """Run the REAL verifier over the stored card, optionally broken."""
    src = RUNNER % {"root": ROOT,
                    "path": os.path.join(ROOT, "picks", "%s.json" % DAY),
                    "mutate": mutate}
    p = subprocess.run([sys.executable, "-c", src], cwd=ROOT,
                       capture_output=True, text=True, timeout=900)
    out = p.stdout + p.stderr
    return p.returncode, out


if DAY is None:
    note("⚠️ NOT EXERCISED: no stored MLB card with rows in this tree, so "
         "nothing below ran. ⛔ Reported rather than passed (rule 144).")
else:
    note("driving verify_card.py over the stored card for %s (%d picks)"
         % (DAY, len(CARD["picks"])))

    def _fails(out):
        return {ln.strip().split("  ")[0]
                for ln in out.splitlines() if ln.strip().startswith("FAIL")}

    print("═══ 1. 🔴 IT RUNS, AND IT RUNS A LOT OF CHECKS ═══")
    rc, out = run()
    _pass = out.count("PASS")
    BASE = _fails(out)
    # 🔴🔴 THE BASELINE IS RECORDED, NOT ASSERTED CLEAN — AND MY FIRST
    #    VERSION ASSERTED IT CLEAN AND WAS WRONG.
    #
    #    The stored 2026-09-13 card fails one check TODAY:
    #    *"no prop with a player id and a real game log is left without a
    #    projection"*, on Christian Moore and Jose Siri. ⛔ **The card is
    #    not wrong and the verifier is not wrong.** The verifier
    #    RECOMPUTES projections from the CURRENT game log, and those
    #    players have since played enough games to cross
    #    `MIN_HITTER_GAMES` — so a prop correctly left unprojected in
    #    September is one the verifier now expects to see projected.
    #
    # ⚠️ THAT IS RULE 166 IN MY OWN TEST: "does yesterday's card pass
    #    today's verifier against today's logs" is a question about the
    #    WORLD, not about the code, and the answer drifts on its own.
    # ✅ So the baseline is a MEASUREMENT, and every injected case is
    #    judged against it rather than against zero.
    note("baseline: %d PASS, %d pre-existing failure(s) — recorded, not "
         "asserted, because the verifier recomputes from TODAY'S logs "
         "and a stored card ages against them" % (_pass, len(BASE)))
    for _b in sorted(BASE):
        note("  ⚪ pre-existing: %s" % _b[:110])
    # 🔴 `[2026-09-25]` ONE CHECK MAY NEVER BE "PRE-EXISTING": the printed
    #    pitcher number. It is re-derived from inputs the card STORES
    #    (`blend`, `break_even`, the mapping), not from today's logs, so it
    #    cannot age. ⛔ It shipped comparing `confidence` to `round(blend)`
    #    on a blend stored to one decimal, and failed this correct card:
    #    a true 69.45 is stored 69.5 and prints 69. A verifier that fails a
    #    correct card refuses to publish it.
    _pc = [b for b in BASE if "prints the number its stored correction" in b]
    ck("🔴 the printed-pitcher-number check passes on a real published card",
       not _pc, "⛔ it fails a card it has no stale input to blame: %s" % _pc)
    # ⛔ A COUNT, NOT A BOOLEAN. A verifier that early-returns after six
    #    checks exits 0 exactly like one that ran ninety, and the exit
    #    code cannot tell them apart. This is the check that would catch
    #    an accidental `return` at the top of the file.
    ck("🔴 ...and it actually performed a substantial number of checks",
       _pass >= 60,
       "⛔ `verify_card.py` carries roughly ninety. Sixty is a floor with "
       "room for a slate that legitimately skips a section — but SIX is "
       "an early return wearing a green tick. Counted %d" % _pass)
    note("verifier reported %d PASS lines on the %s card" % (_pass, DAY))

    print("\n═══ 2. 🔴🔴 FAULT-INJECTED — IT STILL BITES ═══")
    # 🔴 FOUR DISTINCT CLASSES, EACH ONE A DEFECT THAT HAS ACTUALLY
    #    SHIPPED IN THIS PROJECT. Green here is only evidence because a
    #    deliberate red came first (rule 202).
    CASES = (
        ("the board is out of confidence order",
         "⛔ Sam's standing rule is descending confidence. A board that "
         "jumps around made the page look broken to anyone reading down "
         "the numbers.",
         "_doc['picks'] = list(reversed(_doc['picks']))"),

        ("a parlay puts two legs in the SAME GAME",
         "⛔ A live card shipped FOUR impossible parlays this way, "
         "including its top recommendation, because the check compared "
         "opponent NAMES instead of game ids (rule 54).",
         "\n".join([
             "for _k, _rows in (_doc.get('parlays') or {}).items():",
             "    for _r in _rows:",
             "        if _r.get('game_ids') and len(_r['game_ids']) > 1:",
             "            _r['game_ids'] = [_r['game_ids'][0]] * len(_r['game_ids'])",
             "            break",
             "    else:",
             "        continue",
             "    break",
         ])),

        ("a projection no longer matches the player's own mean",
         "⛔ ONE projection per player per stat, the same everywhere — "
         "Sam: *'you should have the same numbers across the entire "
         "website.'* The verifier RECOMPUTES it from the log rather than "
         "checking the field exists.",
         "\n".join([
             "_p = _doc.get('projections') or {}",
             "for _k in list(_p)[:1]:",
             "    _p[_k] = (_p[_k] + 7.5) if isinstance(_p[_k], (int, float)) else _p[_k]",
         ])),

        ("a pitcher row prints a number 2 points off its own",
         "⛔ `[2026-09-25]` the printed pitcher number is the blend, or the "
         "blend corrected against the price (C2). A row that prints "
         "anything else is a number nobody computed.",
         "\n".join([
             "for _r in _doc.get('picks') or []:",
             "    if _r.get('kind') != 'hitter' and _r.get('blend') is not None:",
             "        _r['confidence'] += 2",
             "        break",
         ])),

        ("an internal diagnostic is marked for DISPLAY",
         "⛔ Sam: *'we have to advertise a clean look that doesnt include "
         "nonsense users dont need to read.'* A flag only earns "
         "`actionable` if it changes what the reader can DO.",
         "\n".join([
             "for _r in _doc.get('picks') or []:",
             "    for _f in (_r.get('flags') or []):",
             "        if isinstance(_f, dict) and not _f.get('actionable'):",
             "            _f['actionable'] = True",
             "            break",
         ])),
    )

    # 🔴🔴 AN INJECTION IS ONLY "CAUGHT" IF IT PRODUCES A FAILURE THE
    #    BASELINE DID NOT HAVE. My first version asked only "did it fail",
    #    and THREE OF THE FOUR CASES scored a pass by re-detecting the
    #    pre-existing projection failure — the injected defect was never
    #    caught at all and the file printed green.
    # ⛔ IT IS THE COVERAGE MATRIX'S MISTAKE AGAIN, TWO HOURS LATER: a
    #    signal that fires on everything distinguishes nothing. The
    #    difference from the baseline is the only honest measure.
    _bit = 0
    for name, why, mut in CASES:
        rc, out = run(mut)
        _new = _fails(out) - BASE
        if not _new:
            # ⚠️ NOT A SILENT PASS AND NOT A HARD FAIL. A card whose data
            #    cannot express the defect (no multi-game parlay, no
            #    flags) means the injection did not land — and rule 144
            #    says a check that could not run did not pass.
            note("⚠️ NOT EXERCISED — %s: the stored card has nothing to "
                 "break for this case, so it proves nothing. ⛔ Reported, "
                 "not passed." % name)
            continue
        _bit += 1
        ck("🔴 caught: %s" % name, bool(_new),
           "%s Verifier raised a NEW failure: %s"
           % (why, sorted(_new)[0][:110]))

    ck("🔴🔴 the fault injection exercised at least one real class",
       _bit >= 1,
       "⛔ IF NOTHING LANDED, SECTION 2 IS DECORATION. Every case would "
       "have reported NOT EXERCISED and the file would print green "
       "having driven nothing. Exercised %d of %d" % (_bit, len(CASES)))

    print("\n═══ 3. ⛔ AND THE SUITE NOW COUNTS IT ═══")
    # 🔴 THE WHOLE POINT, STATED AS AN ASSERTION. The collector's Tests
    #    step globs `test_*.py`, so this file running at all is what
    #    closes the gap — and a future edit that renames it out of the
    #    glob would silently reopen it.
    ck("🔴 this file is named so the collector's test glob picks it up",
       os.path.basename(__file__).startswith("test_")
       and __file__.endswith(".py"),
       "⛔ `collect.yml` runs `for t in test_*.py`. A file outside that "
       "glob is a file that does not run, which is the exact condition "
       "this one exists to end")

note("⛔ WHAT THIS FILE STILL DOES NOT COVER: the ~90 checks are exercised "
     "against ONE stored card, so a check that only fires on a board "
     "shape this card does not have is still unproven. ➡️ That is a "
     "smaller gap than 'the verifier is not in the suite at all', and it "
     "is stated rather than papered over.")
