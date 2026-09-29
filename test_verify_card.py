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
#
# @vacuity 🔴 PLANTED C2 row: the printed number is the one its stored mapping gives
#   file: verify_card.py
#   find: if (_want is None or abs(_want - r['confidence_value']) > 0.3
#   with: if (_want is None or abs(_want - r['confidence_value']) > 99
#
# @vacuity 🔴 STATIC + COUNT: an exit after section 1 is a verifier that stops checking
#   file: verify_card.py
#   find: ck("Poisson CDF vs 200k simulations", worst < 0.6, f"max gap {worst:.3f} pts")
#   with: ck("Poisson CDF vs 200k simulations", worst < 0.6, f"max gap {worst:.3f} pts"); sys.exit(0)
#
# @vacuity 🔴 the same-game parlay class is caught on its own subject card
#   file: verify_card.py
#   find: _same = [p['legs'] for p in _all_p if len(set(p['game_ids'])) != p['n_legs']]
#   with: _same = []
#
# @vacuity 🔴 the projection class is caught on its own subject card (it landed on NO card before)
#   file: verify_card.py
#   find: _incoh = [(k, sorted(v)) for k, v in _seen_pm.items() if len(v) > 1]
#   with: _incoh = []
"""
import ast
import json
import os
import re
import subprocess
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import card as C  # noqa: E402


def _cards():
    """Every published MLB card that actually has rows, NEWEST FIRST.

    ⚠️ NOT "today's". The point is a REAL document with real prices,
    parlays and projections in it — today's may not exist yet, and
    building one here would spend credits and take minutes.
    """
    for f in sorted(os.listdir(os.path.join(ROOT, "picks")), reverse=True):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.json", f):
            continue
        try:
            d = json.load(open(os.path.join(ROOT, "picks", f),
                               encoding="utf-8"))
        except Exception:
            continue
        if d.get("picks"):
            yield f[:-5], d


def _newest_card(has_case=lambda d: True, cards=None):
    """The newest published card for which `has_case(card)` is true.

    🔴🔴 A CHECK ABOUT ONE ROW SHAPE IS DRIVEN ON A CARD THAT HAS THAT
    SHAPE, NEVER ON WHATEVER CARD IS NEWEST. `[2026-09-26]` The rounding
    guard below was written against the newest card, 2026-09-24, whose
    Dobnak/Painter rows are the case. At 2026-09-25 14:12Z a newer card
    landed with one pitcher row, on the C2 branch; the guard's subject
    moved with the date, and `vacuity.tier2` found it VACUOUS: green with
    the wrong line restored (rule 166). ✅ Published cards are permanent,
    so once a card holds a shape, some card always will.
    """
    for day, d in (_cards() if cards is None else cards):
        if has_case(d):
            return day, d
    return None, None


def _rounding_rows(d):
    """Pitcher rows the ~~`confidence != round(blend)`~~ line wrongly fails.

    The verifier's no-correction branch (`confidence_method` BLEND or
    absent, no applied mapping) on a row whose stored blend ROUNDS to
    another number than the one printed, and is still a correct row:
    `blend` is stored to one decimal (±0.05) and the card rounds the
    unrounded value (±0.5), so a correct row prints within 0.55 of it.
    """
    pcor = d.get("pitcher_correction") or {}
    maps = pcor.get("maps") or {}
    out = []
    for r in (d.get("picks") or []) + (d.get("below_price_floor") or []):
        if r.get("kind") == "hitter" or r.get("blend") is None:
            continue
        if r.get("confidence_method", "BLEND") != "BLEND":
            continue
        if maps.get(r.get("market")) and pcor.get("method"):
            continue
        if (r["confidence"] != round(r["blend"])
                and abs(r["confidence"] - r["blend"]) <= 0.55):
            out.append(r)
    return out


def _has_rounding_case(d):
    return bool(_rounding_rows(d))


DAY, CARD = _newest_card()
# 🔴 THE ROUNDING CASE'S OWN CARD: the newest that CONTAINS it.
RDAY, RCARD = _newest_card(_has_rounding_case)

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


def run(mutate="", day=None):
    """Run the REAL verifier over a stored card (the newest by default),
    optionally broken."""
    src = RUNNER % {"root": ROOT,
                    "path": os.path.join(ROOT, "picks",
                                         "%s.json" % (day or DAY)),
                    "mutate": mutate}
    p = subprocess.run([sys.executable, "-c", src], cwd=ROOT,
                       capture_output=True, text=True, timeout=900)
    out = p.stdout + p.stderr
    return p.returncode, out


# ══════════════════════════════════════════════════════════════════════
# 🔴 A STORED CARD IS ONLY A FAIR SUBJECT WHILE THE LIVE TREE CAN STILL
#    VERIFY IT. `[2026-09-28]` `verify_card.py` reads `data/latest/
#    pitchers.json.gz` and indexes it by every carded pitcher, then divides
#    by his starts BEFORE the card's date. That file is one season: the first
#    pitchers pull of a new season (April) replaces it, and every stored card
#    then dies in section 1 on a KeyError or a ZeroDivisionError — a correct
#    verifier "running 1 check" and "catching nothing" (patterns P1/P3: a
#    subject pinned to a date, driven against a tree that moves on).
# ✅ So a card drives the whole verifier only while the tree can still read
#    it, and what must hold EVERY run is asked of planted inputs instead.
# ══════════════════════════════════════════════════════════════════════
try:
    import gzip as _gz
    _PLIVE = json.load(_gz.open(os.path.join(ROOT, "data", "latest",
                                             "pitchers.json.gz"), "rt"))["players"]
except Exception:           # no pitcher log in this tree -> no card qualifies
    _PLIVE = {}


def _consistent(day, d):
    """Every carded pitcher is in the live log with a start before `day`."""
    for r in (d.get("picks") or []) + (d.get("below_price_floor") or []):
        if r.get("kind") == "hitter":
            continue
        p = _PLIVE.get(str(r.get("pid")))
        if not p or not any(x.get("gs") and (x.get("d") or "") < day
                            for x in p.get("g") or []):
            return False
    return True


def _newest_fair(has_case=lambda d: True):
    """The newest stored card holding the case that the live tree can verify."""
    for day, d in _cards():
        if has_case(d) and _consistent(day, d):
            return day, d
    return None, None


SUBJ, SUBJ_CARD = _newest_fair()

# ══════════════════════════════════════════════════════════════════════
# 🔴 SECTION 39 — THE PRINTED PITCHER NUMBER — DRIVEN ON PLANTED ROWS.
#    Its own lines are read out of `verify_card.py` (between its section
#    header and the next audit block) and run on a planted card: ONE copy of
#    the rule (rule 207), no data tree, no clock. `verify_card.py` is a
#    script, so this is the only way to reach one section without the rest.
#    ⛔ If the markers move, the block below is empty and the rule-67 check
#    says so — it can never pass on nothing.
# ══════════════════════════════════════════════════════════════════════
_VSRC = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
_S39_A = 'print("\\n39. THE PRINTED PITCHER NUMBER'
_S39_B = "# 🔴 AUDIT PROPOSAL B."
_S39 = (_VSRC[_VSRC.index(_S39_A):_VSRC.index(_S39_B)]
        if _S39_A in _VSRC and _S39_B in _VSRC and _VSRC.index(_S39_A) < _VSRC.index(_S39_B)
        else "")


def section39(doc, rows):
    """Run verify_card.py's own section 39 on `doc` -> {check name: ok}."""
    import types
    got = {}

    def _ck(name, ok, detail=""):
        got[re.sub(r"\s*\(\d+ priced rows\)", "", name)] = bool(ok)
    ns = {"doc": doc, "pit_rows": rows, "ck": _ck, "print": lambda *a, **k: None,
          "C": types.SimpleNamespace(LAST_PITCHER_ROWS=[])}
    exec(compile(_S39, "verify_card.py#section39", "exec"), ns)
    return got


import mlb_pitcher_cal as _MPC  # noqa: E402
_S39_NAME = "every pitcher row prints the number its stored correction gives"
_MAP = {"mu": [0.65, 0.22], "sd": [0.40, 0.23], "w": [0.07, 0.14, 0.08],
        "n_train": 400, "before": "2026-09-29"}
_ROUND = {"pitcher": "Planted Blend", "market": "outs", "kind": "pitcher",
          "blend": 69.5, "confidence": 69, "confidence_method": "BLEND",
          "break_even": 55.0}


def _c2_row():
    v = _MPC.corrected({"strikeouts": _MAP}, "strikeouts", 61.6, 63.0)
    return {"pitcher": "Planted C2", "market": "strikeouts", "kind": "pitcher",
            "blend": 61.6, "break_even": 63.0, "confidence_value": round(v, 2),
            "confidence": round(v), "confidence_method": _MPC.SHIPPED,
            "edge": round(v - 63.0, 2),
            "confidence_note": "blended 50/50, then corrected against the price."}


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
    #    (`blend`, `break_even`, the mapping), not from today's logs. ⛔ It
    #    shipped comparing `confidence` to `round(blend)` on a blend stored
    #    to one decimal, and failed the correct 2026-09-24 card: a true 69.45
    #    is stored 69.5 and prints 69. A verifier that fails a correct card
    #    refuses to publish it.
    # 🔴 `[2026-09-28]` ~~ck("...passes on a real published card", newest)~~
    #    asked the NEWEST card — whatever code last wrote it — to stay
    #    silent (P2): Sam's documented off switch (`SHIPPED = None`) turns it
    #    red in the PR that flips it, and it stays red until a newer card
    #    lands, which in the off-season is never. ✅ The rule is now DRIVEN on
    #    planted rows, both branches, both ways; the newest card is reported.
    _pc = [b for b in BASE if "prints the number its stored correction" in b]
    note("%s the newest card (%s) under section 39: %s"
         % ("✅" if not _pc else "⛔", DAY, "no failure" if not _pc else _pc))

print("\n═══ 1b. 🔴 SECTION 39 ON PLANTED ROWS — EVERY RUN ═══")
ck("⚠️ section 39's own lines were read out of verify_card.py",
   "_pbad" in _S39 and _S39_NAME in _S39 and _S39.count("ck(") >= 2,
   "⛔ rule 67: an empty block runs nothing and every check below would "
   "read a missing name as a failure — or worse, a pass. %d chars" % len(_S39))
if _S39:
    _rows = [_ROUND] + ([_c2_row()] if _MPC.SHIPPED else [])
    _doc = {"pitcher_correction": {"method": _MPC.SHIPPED, "maps": {"strikeouts": _MAP}}
            if _MPC.SHIPPED else {}}
    _ok = section39(_doc, _rows)
    ck("🔴🔴 PLANTED: a correct card passes — the rounding row (69.5 stored, "
       "69 printed)%s" % (" and a C2 row" if _MPC.SHIPPED else ""),
       _ok.get(_S39_NAME) is True,
       "⛔ a correct card whose stored blend rounds away from its printed "
       "number must verify. got %s" % _ok)
    _off = dict(_ROUND, confidence=71)
    ck("🔴 PLANTED: ...and a BLEND row printing 2 points off its blend FAILS",
       section39(_doc, [_off]).get(_S39_NAME) is False,
       "⛔ a tolerance that swallows 1.5 points is not a tolerance")
    if _MPC.SHIPPED:
        _bad = _c2_row()
        _bad["confidence_value"] += 2
        _bad["confidence"] += 2
        # ⚠️ its edge moved with it, so ONLY the stored-mapping comparison
        #    can catch this row — the arithmetic around it is consistent.
        _bad["edge"] = round(_bad["confidence_value"] - 63.0, 2)
        ck("🔴 PLANTED: ...and a C2 row 2 points off its stored correction FAILS",
           section39(_doc, [_bad]).get(_S39_NAME) is False,
           "⛔ the printed number must be the one the stored mapping gives")
    else:
        note("⚠️ mlb_pitcher_cal.SHIPPED is off — the C2 branch has no row "
             "to plant; the BLEND branch is driven above")

if DAY is not None:
    # 🔴🔴 `[2026-09-26]` ...AND ON THE NEWEST CARD THAT CONTAINS THE CASE.
    #    Driven on the newest card alone, the check above went VACUOUS the
    #    day a card landed with no row on the no-correction branch
    #    (`_newest_card`). ⛔ No case on any stored card is a FAILURE, not
    #    a note: published cards are permanent, so the case cannot leave.
    _rr = _rounding_rows(RCARD) if RCARD else []
    ck("🔴🔴 a stored card holds the rounding case (%s: %s)"
       % (RDAY, ", ".join("%s %s %s->%s" % (r.get("pitcher"), r["market"],
                                           r["blend"], r["confidence"])
                          for r in _rr[:3])),
       bool(_rr),
       "⛔ no published card has a pitcher row on the no-correction "
       "branch whose stored blend rounds to another number than the one "
       "printed, so nothing below can tell `round(blend)` from the "
       "tolerance")
    if _rr:
        # ⚠️ `[2026-09-28]` THE WHOLE VERIFIER ON THAT CARD IS NOW THE EXTRA.
        #    A FAIL line is still red. But the card is pinned to 2026-09-24
        #    while the tree moves: once the pitcher log rolls to a new season
        #    the run dies before section 39 and prints no line at all — that
        #    is REPORTED, because §1b asks the same rule of planted rows.
        _, _rout = run(day=RDAY)
        _rl = [ln.strip() for ln in _rout.splitlines()
               if "prints the number its stored correction" in ln]
        if _rl:
            ck("🔴🔴 the printed-pitcher-number check passes on %s, which holds "
               "%d rounding row(s)" % (RDAY, len(_rr)),
               any(ln.startswith("PASS ") for ln in _rl)
               and not any(ln.startswith("FAIL ") for ln in _rl),
               "⛔ a correct card whose stored blend rounds away from its "
               "printed number must verify. Got %s" % _rl)
        else:
            note("⚠️ NOT EXERCISED ON %s: the verifier printed no section-39 "
                 "line (an earlier section died against today's tree: %r). §1b "
                 "drove the rule on planted rows."
                 % (RDAY, (_rout.strip().splitlines() or [""])[-1][:160]))
    # ✅ AND A NEWER CARD WITHOUT THE CASE CANNOT TAKE ITS PLACE — which is
    #    exactly what happened at 2026-09-25 14:12Z. A card dated after
    #    every real one, with no pitcher row at all, is put in front.
    _future = ("2099-12-31", {"picks": [{"kind": "hitter", "confidence": 60}]})
    _withf = [_future] + list(_cards())
    ck("🔴 a newer card with no rounding case does not move the case's card",
       _newest_card(cards=_withf)[0] == _future[0]
       and _newest_card(_has_rounding_case, cards=_withf)[0] == RDAY
       and RDAY is not None,
       "⛔ the planted card is newest (%s) and must be skipped: the case's "
       "card must stay %s, got %s"
       % (_newest_card(cards=_withf)[0], RDAY,
          _newest_card(_has_rounding_case, cards=_withf)[0]))

# ⛔ A COUNT, NOT A BOOLEAN. A verifier that early-returns after six checks
#    exits 0 exactly like one that ran ninety, and the exit code cannot tell
#    them apart.
# 🔴 `[2026-09-28]` TWO HALVES, AND ONE ALWAYS RUNS. (a) STATIC, every run:
#    no top-level statement between the verifier's first and last check can
#    exit. (b) THE COUNT, on the newest card the live tree can still verify —
#    ~~the newest card, whatever the tree~~ dropped to 1 PASS every April
#    when the pitcher log rolled over (a crash in section 1, on correct code).
_VT = ast.parse(_VSRC)


def _is_exit(n):
    for x in ast.walk(n):
        if isinstance(x, ast.Call) and (getattr(x.func, "attr", None) or getattr(x.func, "id", None)) \
                in ("exit", "_exit", "quit"):
            return True
        if isinstance(x, ast.Raise) and x.exc is not None and "SystemExit" in ast.dump(x.exc):
            return True
    return False


_ckstmts = [i for i, n in enumerate(_VT.body)
            if not isinstance(n, ast.FunctionDef)
            and any(isinstance(x, ast.Call) and getattr(x.func, "id", None) == "ck"
                    for x in ast.walk(n))]
_early = [n.lineno for i, n in enumerate(_VT.body)
          if _ckstmts and _ckstmts[0] < i < _ckstmts[-1] and _is_exit(n)]
ck("🔴 STATIC: nothing between the verifier's first and last check can exit early",
   len(_ckstmts) >= 60 and not _early,
   "⛔ an exit in the middle is a verifier that stops checking and exits "
   "clean. %d top-level check statements; early exit(s) at line(s) %s"
   % (len(_ckstmts), _early))
if SUBJ is None:
    note("⚠️ NOT EXERCISED: no stored card the live tree can still verify (the "
         "pitcher log has rolled to a new season). The static half above ran.")
else:
    if SUBJ == DAY:
        _spass = _pass
    else:
        _spass = run(day=SUBJ)[1].count("PASS")
    ck("🔴 ...and it actually performed a substantial number of checks (%s)" % SUBJ,
       _spass >= 60,
       "⛔ `verify_card.py` carries roughly ninety. Sixty is a floor with "
       "room for a slate that legitimately skips a section — but SIX is "
       "an early return wearing a green tick. Counted %d" % _spass)
    note("verifier reported %d PASS lines on the %s card" % (_spass, SUBJ))

if DAY is not None:
    print("\n═══ 2. 🔴🔴 FAULT-INJECTED — IT STILL BITES ═══")
    # 🔴 FIVE DISTINCT CLASSES, EACH ONE A DEFECT THAT HAS ACTUALLY
    #    SHIPPED IN THIS PROJECT. Green here is only evidence because a
    #    deliberate red came first (rule 202).
    # 🔴 `[2026-09-28]` EACH CLASS ON ITS OWN SUBJECT: the newest stored card
    #    that HOLDS the case and that the live tree can still verify (the
    #    rounding case's pattern). ~~every class on the newest card, and
    #    "at least one landed"~~ let a class go unproven for weeks — the
    #    projection class landed on NO card at all, because it edited a
    #    number where every card stores a dict.
    CASES = (
        ("the board is out of confidence order",
         "⛔ Sam's standing rule is descending confidence. A board that "
         "jumps around made the page look broken to anyone reading down "
         "the numbers.",
         "_doc['picks'] = list(reversed(_doc['picks']))",
         lambda d: len({p.get("confidence") for p in d.get("picks") or []}) >= 2),

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
         ]),
         lambda d: any(len(set(r.get("game_ids") or [])) > 1
                       for rows in (d.get("parlays") or {}).values() for r in rows)),

        ("a projection no longer matches the player's own mean",
         "⛔ ONE projection per player per stat, the same everywhere — "
         "Sam: *'you should have the same numbers across the entire "
         "website.'* The verifier RECOMPUTES it from the log rather than "
         "checking the field exists.",
         "\n".join([
             "_p = _doc.get('projections') or {}",
             "for _k in list(_p)[:1]:",
             "    if isinstance(_p[_k], dict):",
             "        _p[_k]['v'] = _p[_k]['v'] + 7.5",
             "    elif isinstance(_p[_k], (int, float)):",
             "        _p[_k] = _p[_k] + 7.5",
         ]),
         lambda d: any(isinstance(v, (int, float)) or (isinstance(v, dict) and "v" in v)
                       for v in (d.get("projections") or {}).values())),

        ("a pitcher row prints a number 2 points off its own",
         "⛔ `[2026-09-25]` the printed pitcher number is the blend, or the "
         "blend corrected against the price (C2). A row that prints "
         "anything else is a number nobody computed.",
         "\n".join([
             "for _r in _doc.get('picks') or []:",
             "    if _r.get('kind') != 'hitter' and _r.get('blend') is not None:",
             "        _r['confidence'] += 2",
             "        break",
         ]),
         lambda d: any(r.get("kind") != "hitter" and r.get("blend") is not None
                       for r in d.get("picks") or [])),

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
         ]),
         lambda d: any(isinstance(f, dict) and not f.get("actionable")
                       for r in d.get("picks") or [] for f in (r.get("flags") or []))),
    )

    # 🔴🔴 AN INJECTION IS ONLY "CAUGHT" IF IT PRODUCES A FAILURE THE
    #    BASELINE DID NOT HAVE — THE BASELINE OF ITS OWN SUBJECT CARD. A
    #    signal that fires on everything distinguishes nothing.
    _BASES = {DAY: BASE}
    _bit = 0
    for name, why, mut, has_case in CASES:
        _sd, _sc = _newest_fair(has_case)
        if _sd is None:
            note("⚠️ NOT EXERCISED — %s: no stored card holding this case can "
                 "still be verified against today's tree. ⛔ Reported, not passed."
                 % name)
            continue
        if _sd not in _BASES:
            _BASES[_sd] = _fails(run(day=_sd)[1])
        rc, out = run(mut, day=_sd)
        _new = _fails(out) - _BASES[_sd]
        _bit += bool(_new)
        ck("🔴 caught: %s (on %s)" % (name, _sd), bool(_new),
           "%s Verifier raised %s"
           % (why, ("a NEW failure: %s" % sorted(_new)[0][:110]) if _new else
              "NO new failure — the class is not caught"))

    if SUBJ is not None:
        ck("🔴🔴 the fault injection exercised at least one real class",
           _bit >= 1,
           "⛔ IF NOTHING LANDED, SECTION 2 IS DECORATION. Exercised %d of %d"
           % (_bit, len(CASES)))
    else:
        note("⚠️ NOT EXERCISED: no stored card can be verified against today's "
             "tree. §1b's planted rows still inject a fault into section 39 "
             "and watch it caught, every run.")

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

note("⛔ WHAT THIS FILE STILL DOES NOT COVER: ~~the ~90 checks are exercised "
     "against the NEWEST stored card~~ `[2026-09-28]` the five injected "
     "classes each run on the newest stored card that holds the case AND that "
     "today's tree can still verify, and section 39 runs on planted rows; the "
     "other ~85 checks are exercised only through those real cards, so a "
     "check that fires on a board shape no fair card holds is still unproven "
     "— and between a season's first pitcher pull and its first card with "
     "picks, no stored card is fair and only the static and planted halves "
     "run. ➡️ Stated rather than papered over.")
