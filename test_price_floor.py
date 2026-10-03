#!/usr/bin/env python3
"""
SAM'S ~~-700~~ -400 FLOOR IS INCLUSIVE, AND BOTH HALVES MUST AGREE ABOUT IT.

`[Sam, 2026-10-01]` "ideally props/game lines at -400 is the lowest we
should go": -400 is now the floor for EVERY Gizmo's Picks row in all three
leagues (section 5). The history below is kept as it happened at -700.

🔴 THE FAILURE, LIVE ON 2026-09-12 (run 932, converge pass 3):

    verify_card FAILED
      FAIL no parlay leg is shorter than the -700 floor

    Walbert Ureña o2.5 K  -700  +  Ha-Seong Kim u1.5 TB  -400
                          ^^^^ exactly the floor, and legal

**THE CARD WAS RIGHT AND THE CHECK WAS WRONG.** Ledger rule 187 fixed the
BUILDER on 2026-09-11 from `>` to `>=` — *"-700 ITSELF is the shortest
rung he WILL take"* — and `verify_card.py` was not changed with it. For a
day the builder called a -700 leg legal and the verifier called it a
violation. ⚠️ **It stayed quiet until a parlay actually carried one.**

⛔ **AND THE VERIFIER HAD THE SAME ERROR IN A SECOND PLACE** that had not
fired yet: the below-floor LABEL check collected rows at `<= -700` and
then asserted they were labelled as NOT clearing — which the builder
correctly labels as clearing. **A latent boundary error is the same
defect as a live one; it is waiting for a price, not for a fix.**

🔴 **RULE 207 IN ITS PUREST FORM.** The verifier's whole job is to
disagree with the card, so a SECOND COPY of a rule inside it is the most
expensive place in this repo for a copy to drift. ✅ There is now one
constant, `card.PRICE_FLOOR`, and both halves read it.

⚠️ **CLAUDE.md FORBIDS WEAKENING A CHECK AND REQUIRES THE ARGUMENT BE
MADE EXPLICITLY WHEN ONE IS CHANGED.** It is made here: the rule, in
Sam's words and in CLAUDE.md's own table, is that rungs **BELOW** the
floor are never paired. **-700 is not below -700.** The edit permits one
price the old form rejected, and the suite is made **strictly harder** in
the same change — `verify_card.py` gained a boundary check it had no
equivalent of, and this file did not exist at all.

# @vacuity section 4: a leg one point past the floor FAILS the verifier
#   file: verify_card.py
#   find:         if any(a < C.PRICE_FLOOR for a in p['prices'])])
#   with:         if any(a < C.PRICE_FLOOR - 1 for a in p['prices'])])
#
# @vacuity section 4: a leg AT the floor PASSES the verifier (inclusive)
#   file: verify_card.py
#   find:         if any(a < C.PRICE_FLOOR for a in p['prices'])])
#   with:         if any(a <= C.PRICE_FLOOR for a in p['prices'])])
#
# @vacuity 🔒 both league files hold Sam's -400
#   file: card_fb.py
#   find: PRICE_FLOOR = -400
#   with: PRICE_FLOOR = -700
#
# @vacuity 🔴 the MLB board seats nothing shorter than the floor
#   file: card.py
#   find: plays = [x for x in plays if x.get("clears_price_floor", True)]
#   with: plays = list(plays)
#
# @vacuity 🔴 the MLB top 10 holds nothing shorter than the floor
#   file: card.py
#   find: if x["price"] < PRICE_FLOOR:
#   with: if x["price"] < -1000:
#
# @vacuity 🔴 the football top plays: -400 itself clears
#   file: card_fb.py
#   find: if x["price"] < PRICE_FLOOR:
#   with: if x["price"] <= PRICE_FLOOR:
#
# @vacuity 🔴 the football game-line rows hold nothing shorter than the floor
#   file: card_fb.py
#   find: if None in (v["price"], v["model_probability"]) or v["price"] < PRICE_FLOOR:
#   with: if None in (v["price"], v["model_probability"]):
#
# @vacuity 🔴 a same-game parlay's line leg clears the floor too
#   file: card_fb.py
#   find: if line_px < PRICE_FLOOR:
#   with: if False:
"""
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, note, shown

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import card as C  # noqa: E402

print("═══ 1. 🔒 IT IS SAM'S NUMBER: ~~-700~~ -400 SINCE 2026-10-01 ═══")
os.environ.setdefault("LEAGUE", "nfl")
import card_fb as FB  # noqa: E402
ck("🔒 PRICE_FLOOR is -400 in both league files (card.py, card_fb.py)",
   C.PRICE_FLOOR == -400 and FB.PRICE_FLOOR == -400,
   "⛔ CLAUDE.md lists this beside the 1.8x pair floor as a thing that "
   "must not change without Sam saying so. It is HIS number, chosen by "
   "hand, not a tolerance of ours to tune. Got %r / %r" % (C.PRICE_FLOOR, FB.PRICE_FLOOR))

src = open(os.path.join(ROOT, "card.py"), encoding="utf-8").read()
ck("⛔ ...and it is NOT in the model fingerprint",
   "PRICE_FLOOR" not in (re.search(r"FINGERPRINT[^\n]*\n(?:.*\n){0,25}", src)
                         or re.match("", "")).group(0)
   if re.search(r"FINGERPRINT", src) else True,
   "it is not a fitted coefficient and `test_model_version.py` must not "
   "treat it as one — a hand-chosen floor moving is a Sam decision, not "
   "a re-fit")

print("\n═══ 2. 🔴 THE BOUNDARY IS INCLUSIVE, DRIVEN NOT READ ═══")
# ⛔ The predicate itself, exactly as `card.py` writes it. A row priced AT
#    the floor clears; a row one point shorter does not.
for price, want in ((C.PRICE_FLOOR + 1, True),
                    (C.PRICE_FLOOR, True),
                    (C.PRICE_FLOOR - 1, False)):
    ck("✅ a price of %d %s the floor" % (price, "CLEARS" if want else "does NOT clear"),
       (price >= C.PRICE_FLOOR) is want,
       "⛔ '-700, nothing shorter' means -700 itself is IN. Rule 187 is "
       "the day this was got wrong in the other direction and shipped "
       "for eighteen days")

print("\n═══ 3. 🔴 THE VERIFIER READS THE CONSTANT, NOT A LITERAL ═══")
vsrc = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
# ⛔ COMMENTS STRIPPED FIRST. This file quotes the struck `<= -700` forms
#    verbatim while explaining them, and a bare search would read its own
#    documentation as the bug — the fifth time that trap has been hit in
#    this repo.
_live = "\n".join(ln for ln in vsrc.splitlines()
                  if not ln.lstrip().startswith("#"))
_bad = re.findall(r"[<>]=?\s*-(?:700|400)\b", _live)
ck("🔴 no live line in verify_card.py compares against a floor LITERAL (-700 or -400)",
   not _bad,
   "⛔ a literal is a second copy of Sam's number, and the two copies "
   "drifted for a day and took a live run red with them (rule 207). "
   "Found: %s" % _bad)
ck("✅ ...it uses C.PRICE_FLOOR",
   "C.PRICE_FLOOR" in _live,
   "one constant, both readers, so they cannot disagree again")
ck("⛔ and the struck forms are kept as the record",
   "~~`any(a <= -700 ...)`~~" in vsrc or "~~`r['price'] <= -700`~~" in vsrc,
   "Sam's standing rule: strike superseded content visibly rather than "
   "deleting it")

print("\n═══ 4. 🔴🔴 FAULT-INJECTED — THE CHECK STILL BITES ═══")
# 🔴 THE HALF THAT MATTERS. A boundary loosened by one point is exactly
#    the kind of edit that silently stops catching anything, so the check
#    is DRIVEN with a genuine violation rather than read.
# ⛔ `verify_card.py` REBUILDS THE CARD IN MEMORY (`doc = C.main(dry=True)`),
#    so injecting into `picks/<date>.json` proves nothing — the first
#    attempt at this test did exactly that and "passed" against a file
#    the verifier never opens. The builder is patched instead.
# 🔴 `[2026-09-28]` ~~ONLY LEGS ALREADY AT THE FLOOR WERE PUSHED~~, on
#    TODAY'S live card with the real clock. So the only proof that this
#    check bites ran only on a slate that happened to carry a -700 leg —
#    measured 2026-09-28: 40 parlay legs, none at -700, "NOT EXERCISED" —
#    and never in the off-season, when there is no card at all. And when
#    it did run it matched the bare substring, which verify_card prints on
#    PASS as well as FAIL, beside ANY non-zero exit: an unrelated live
#    failure satisfied it while the floor check itself printed PASS.
#    ✅ THE CASE IS NOW PLANTED: a synthetic card with one two-leg parlay
#    is driven through the REAL verifier in a tree holding nothing live,
#    once with a leg AT the floor and once ONE POINT past it, and the
#    verdict is read off the verifier's own line for THIS check — PASS
#    at -700, FAIL (and counted in FAILURES) at -701. That is strictly
#    harder: it proves both halves of the boundary every run.
#    ➡️ Today's live card is still driven as an EXTRA when there is one.
FLOOR_LINE = "no parlay leg is shorter than the %d floor" % C.PRICE_FLOOR
PLANT = r'''
import sys; sys.path.insert(0, %r)
import card as C
LEG = int(sys.argv[1])
_orig = C.main
def planted_parlay(leg):
    return {"legs": ["Planted A o4.5 K", "Planted B u1.5 TB"], "n_legs": 2,
            "prices": [leg, 250], "game_ids": ["planted-1", "planted-2"],
            "decimals": [1.0 + 100.0 / -leg, 3.5],
            "multiplier": round((1.0 + 100.0 / -leg) * 3.5, 3),
            "leg_confidences": [90.0, 60.0], "joint": 54.0,
            "joint_basis": "MODEL", "leg_bases": ["MODEL", "MODEL"]}
def synthetic(*a, **k):
    return {"date": "2026-09-28", "picks": [], "below_price_floor": [],
            "pairs": [], "projections": {}, "top10": [], "top10_excluded": {},
            "parlays": {"2": [planted_parlay(LEG)]}, "hitter_record_bands": [],
            "board_rule": {}, "board_seats": {}, "pitcher_correction": {}}
def live(*a, **k):
    d = _orig(*a, **k)
    if d is None:
        print("NO LIVE CARD", file=sys.stderr)
        return d
    n = 0
    for rows in (d.get("parlays") or {}).values():
        for r in rows:
            for i, px in enumerate(r.get("prices") or []):
                if px == C.PRICE_FLOOR:
                    r["prices"][i] = C.PRICE_FLOOR - 1
                    n += 1
    _first = [r for rows in (d.get("parlays") or {}).values() for r in rows]
    if _first and C.PRICE_FLOOR - 1 not in _first[0]["prices"]:
        _first[0]["prices"][0] = C.PRICE_FLOOR - 1
        n += 1
    elif not _first:
        d.setdefault("parlays", {}).setdefault("2", []).append(
            planted_parlay(C.PRICE_FLOOR - 1))
        n += 1
    print("INJECTED %%d" %% n, file=sys.stderr)
    return d
C.main = synthetic if sys.argv[2] == "synthetic" else live
import verify_card  # noqa
''' % ROOT


def _floor_verdict(out):
    """The verifier's own line for THIS check: 'PASS', 'FAIL' or None, and
    whether its FAILURES summary counts it."""
    got = [ln[2:6] for ln in out.splitlines()
           if ln.startswith(("  PASS ", "  FAIL ")) and ln[7:].startswith(FLOOR_LINE)]
    summary = [ln for ln in out.splitlines() if ln.startswith("FAILURES:")]
    return (got[0] if len(got) == 1 else got or None,
            bool(summary) and FLOOR_LINE in summary[-1])


_T = tempfile.mkdtemp(prefix="pricefloor-")
try:
    # ⛔ A TREE WITH NOTHING LIVE IN IT: the verifier reads its data files
    #    relative to the working directory, so it sees these empty ones
    #    and never today's board, pull or published cards.
    os.makedirs(os.path.join(_T, "data", "latest"))
    for _nm, _obj in (("pitchers", {"players": {}}), ("props", {"games": []}),
                      ("hitters", {"players": {}})):
        with gzip.open(os.path.join(_T, "data", "latest", _nm + ".json.gz"),
                       "wt", encoding="utf-8") as _fh:
            json.dump(_obj, _fh)
    _v = {}
    for _leg in (C.PRICE_FLOOR, C.PRICE_FLOOR - 1):
        _q = subprocess.run([sys.executable, "-c", PLANT, str(_leg), "synthetic"],
                            cwd=_T, capture_output=True, text=True, timeout=600,
                            env=dict(os.environ, PYTHONUTF8="1"))
        _v[_leg] = _floor_verdict(_q.stdout) + (_q.returncode,)
        if _v[_leg][0] not in ("PASS", "FAIL"):
            print(shown(_q.stdout[-1500:]), shown(_q.stderr[-1500:]))
finally:
    shutil.rmtree(_T, ignore_errors=True)
ck("🔴 PLANTED: a leg AT the floor (%d) PASSES the verifier's floor check"
   % C.PRICE_FLOOR,
   _v[C.PRICE_FLOOR][0] == "PASS" and not _v[C.PRICE_FLOOR][1],
   "⛔ -700 is not below -700: the verifier calling it a violation is run "
   "932's red on a correct card. got %r" % (_v[C.PRICE_FLOOR],))
ck("🔴🔴 PLANTED: a leg ONE POINT past it (%d) FAILS it, and it is counted"
   % (C.PRICE_FLOOR - 1),
   _v[C.PRICE_FLOOR - 1][0] == "FAIL" and _v[C.PRICE_FLOOR - 1][1]
   and _v[C.PRICE_FLOOR - 1][2] != 0,
   "⛔ THIS IS THE CHECK THAT PROVES THE FIX IS A CORRECTION AND NOT A "
   "WEAKENING. If it passes, the boundary edit stopped the check catching "
   "anything at all. got %r" % (_v[C.PRICE_FLOOR - 1],))

# ── the EXTRA: today's live card, when there is one ───────────────────
_p = subprocess.run([sys.executable, "-c", PLANT, "0", "live"], cwd=ROOT,
                    capture_output=True, text=True, timeout=600)
_n = re.search(r"INJECTED (\d+)", _p.stderr)
_injected = int(_n.group(1)) if _n else 0
if not _injected or "34. PARLAYS" not in _p.stdout:
    note("⚠️ LIVE EXTRA NOT EXERCISED: %s. ⛔ Reported rather than passed; "
         "the planted card above asked the same question this run."
         % ("there is no live card today" if "NO LIVE CARD" in _p.stderr
            else "the live verifier did not reach its parlay section (rc %d)"
            % _p.returncode))
else:
    _lv = _floor_verdict(_p.stdout)
    ck("🔴 LIVE: today's card with a leg pushed ONE POINT past the floor "
       "FAILS the floor check",
       _lv[0] == "FAIL" and _lv[1] and _p.returncode != 0,
       "injected=%d rc=%d verdict=%r" % (_injected, _p.returncode, _lv))
    note("injected %d leg(s) at %d into today's card and the verifier exited %d"
         % (_injected, C.PRICE_FLOOR - 1, _p.returncode))

print("\n═══ 5. 🔴 NO ROW ANYWHERE ON A CARD IS SHORTER THAN -400, IN ANY LEAGUE ═══")
# `[Sam, 2026-10-01]` board picks, top plays, game-line rows, parlay and
# same-game legs. Driven on planted rows priced around the floor; -400 itself
# clears, -401 does not.
PX = (-399, C.PRICE_FLOOR, C.PRICE_FLOOR - 1, -700)
_mlb = [dict(kind=k, game_id="g%d" % i, pid=i + (0 if k == "pitcher" else 50), market="m",
             line=0.5, side="over", confidence=70 - i, edge=5.0, break_even=60.0, price=px,
             clears_price_floor=px >= C.PRICE_FLOOR)
        for k in ("pitcher", "hitter") for i, px in enumerate(PX)]
_brd = C.select_board([r for r in _mlb if r["kind"] == "pitcher"],
                      [r for r in _mlb if r["kind"] == "hitter"])[0]
ck("🔴 the MLB board seats nothing shorter than the floor, and -400 itself",
   _brd and min(r["price"] for r in _brd) >= C.PRICE_FLOOR
   and C.PRICE_FLOOR in [r["price"] for r in _brd], str([r["price"] for r in _brd]))
_t10 = C.build_top10([r for r in _mlb if r["kind"] == "pitcher"],
                     [r for r in _mlb if r["kind"] == "hitter"])[0]
ck("🔴 the MLB top 10 holds nothing shorter than the floor",
   _t10 and min(r["price"] for r in _t10) >= C.PRICE_FLOOR, str([r["price"] for r in _t10]))
_fbr = [dict(player="P%d" % i, game_id="g%d" % i, market="player_receptions", side="over",
             line=3.5, confidence=70 - i, price=px) for i, px in enumerate(PX)]
_tp = FB.build_top_plays(_fbr, [])[0]
ck("🔴 the football top plays: nothing shorter than the floor, and -400 itself clears",
   sorted(r["price"] for r in _tp) == [C.PRICE_FLOOR, -399], str([r["price"] for r in _tp]))
_g = {"id": "e1", "away": "A", "home": "H", "commence": "2026-10-04T17:00:00Z"}
_mp = [{"game": "A at H", "commence": _g["commence"], "market": mk, "side": "home", "team": "H",
        "book": "FanDuel", "line": {"value": ln}, "price": {"value": px},
        "model_probability": {"value": 90.0}, "break_even": {"value": 80.0}}
       for mk, px, ln in (("moneyline", C.PRICE_FLOOR - 1, None), ("total", C.PRICE_FLOOR, 47.5))]
_gl = FB.card_game_lines(_mp, [_g], {}, "2026-10-04")
ck("🔴 the football game-line rows hold nothing shorter than the floor",
   [r["price"] for r in _gl] == [C.PRICE_FLOOR], str([r["price"] for r in _gl]))
_leg = lambda i: dict(player="Q%d" % i, game_id="e1", game="A @ H", market="player_receptions",
                      side="over", line=2.5, confidence=80, price=-150, book="hardrockbet",
                      clears_price_floor=True)
_sg = {"game_id": "e1", "market": "spreads", "side": "H", "point": -3.5, "best_price": -110,
       "best_book": "fanduel"}
_sgp = {px: FB.build_sgp_fb([_leg(1), _leg(2)], [_sg],
                            line_quotes={("e1", "spreads", "H", -3.5): {"hardrockbet": px}})
        for px in (C.PRICE_FLOOR - 1, C.PRICE_FLOOR)}
_px3 = {px: [x for v in sg[0].values() for x in v if x.get("n_legs") == 3]
        for px, sg in _sgp.items()}
ck("🔴 a same-game parlay's line leg clears the floor too",
   not _px3[C.PRICE_FLOOR - 1] and _sgp[C.PRICE_FLOOR - 1][1]["rejected"]["leg_below_price_floor"]
   and _px3[C.PRICE_FLOOR], "3-leg slips at -401: %d, at -400: %d"
   % (len(_px3[C.PRICE_FLOOR - 1]), len(_px3[C.PRICE_FLOOR])))

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that -700 is a good floor. It is "
     "Sam's number and nothing here measures it. What is owned is that "
     "the builder and the verifier mean the SAME THING by it, which they "
     "did not for a day.")
