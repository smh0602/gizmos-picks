#!/usr/bin/env python3
"""test_one_side_props.py — ONE SIDE PER PROP: every list shows only the side the model gives 50%+.

`[Sam, 2026-10-16]` After #278 (one team per game) a sweep of every list found the same props
model on both sides of 5 props (the card's Hunter Tipton Under 3.5 at 55%, its own pick list's
Over 3.5 at 45% because +162 paid). Asked, Sam chose "Model's 50%+ side only: Every list shows
only the side the model gives 50% or more." Planted rows, boards and cards; ⛔ reads nothing
live.

# @vacuity 🔴 only the favoured side at 50%+ stays
#   file: one_side.py
#   find:         ok = len(sides) == 1 and sides[0] == r["side"] and top >= 50 and v is not None and v >= 50
#   with:         ok = True
#
# @vacuity 🔴 an exact tie keeps neither side
#   file: one_side.py
#   find:         ok = len(sides) == 1 and sides[0] == r["side"] and top >= 50 and v is not None and v >= 50
#   with:         ok = sides[0] == r["side"] and top >= 50 and v is not None and v >= 50
#
# @vacuity 🔴 a one-sided market (anytime TD) is never touched
#   file: one_side.py
#   find:         s = best.get(key(r)) if r.get("side") in TWO_SIDED else None
#   with:         s = best.get(key(r))
#
# @vacuity 🔴 the favourite must reach 50%
#   file: one_side.py
#   find:     return side if p >= half else None
#   with:     return side
#
# @vacuity 🔴 the props model's live pick is only ever on its 50%+ side
#   file: fb_props_model.py
#   find:                 po, pu = (po if _fav == "over" else None), (pu if _fav == "under" else None)
#   with:                 pass
#
# @vacuity 🔴 ...and its anytime-TD picks are left alone
#   file: fb_props_model.py
#   find:             if mk != TD_MARKET:
#   with:             if True:
#
# @vacuity 🔴 the football card's pool keeps one side per prop, before every list
#   file: card_fb.py
#   find:     rows, _wrong_side = one_side.keep_props(rows, prop_key, prop_value)
#   with:     _wrong_side = []
#
# @vacuity 🔴 a MODEL row is judged on the model's unrounded chance (49.8 never ties 50.2)
#   file: card_fb.py
#   find:     return r.get("model_p") if r.get("confidence_basis") == "MODEL" else r.get("confidence")
#   with:     return r.get("confidence")
#
# @vacuity 🔴 MLB: every pool keeps the side its printed number favours
#   file: card.py
#   find:     ok = {id(x) for x in one_side.keep_props(plays_all + hitters, _propkey, conf)[0]}
#   with:     ok = {id(x) for x in plays_all + hitters}
#
# @vacuity 🔴 MLB: the board's blend side stays only when the printed number agrees
#   file: card.py
#   find:     main = {id(x) for x in plays if id(x) in ok}
#   with:     main = {id(x) for x in plays}
#
# @vacuity 🔴 MLB: the verifier judges the card main() built with the card's own guard
#   file: verify_card.py
#   find: _osp = C.one_side_problems(doc)
#   with: _osp = []
#
# @vacuity 🔴 MLB: the guard catches a parlay leg under 50%
#   file: card.py
#   find:             if any(c is not None and c < 50 for c in p.get("leg_confidences") or [])]
#   with:             if False]
#
# @vacuity 🔴 MLB: the guard catches a starred ladder rung under 50%
#   file: card.py
#   find:             for r in rows + top if r.get("ladder_pick") and (r["ladder_pick"].get("blend") or 0) < 50]
#   with:             for r in rows + top if False]
"""
import datetime
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types

from tcheck import ck, eq, section, shown

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
import one_side as O  # noqa: E402
import fb_props_model as M  # noqa: E402

UTC = datetime.timezone.utc
key = lambda r: (r.get("game"), r.get("player"), r.get("market"), r.get("line"))  # noqa: E731
val = lambda r: r.get("p")  # noqa: E731


def R(player, side, p, line=3.5, market="rec", game="g1"):
    return {"game": game, "player": player, "market": market, "line": line, "side": side, "p": p}


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE RULE: THE FAVOURED SIDE AT 50%+, A TIE NEITHER, ONE-SIDED MARKETS UNTOUCHED")
# ══════════════════════════════════════════════════════════════════════
eq([O.prop_side(0.45, 0.55), O.prop_side(55, 45, half=50), O.prop_side(0.5, 0.5), O.prop_side(0.48, 0.47),
    O.prop_side(None, 0.6)], ["under", "over", None, None, None],
   "🔴 prop_side: the higher side at 50%+; a tie, two sides under 50% (non-complementary numbers), or a "
   "missing number name no side")
_rows = [R("Tipton", "over", 45.2), R("Tipton", "under", 54.8),
         R("Coin", "over", 50.0), R("Coin", "under", 50.0),
         R("Lone", "over", 46.0),
         R("Both", "over", 51.0), R("Both", "under", 53.0),
         R("Td", "yes", 30.0, line=None, market="td"),
         R("Unrated", "over", None), R("Unrated", "under", None),
         R("Half", "over", 60.0), R("Half", "under", None)]
_k, _d = O.keep_props(_rows, key, val)
eq(sorted((r["player"], r["side"]) for r in _k),
   [("Both", "under"), ("Half", "over"), ("Td", "yes"), ("Tipton", "under"), ("Unrated", "over"), ("Unrated", "under")],
   "🔴 kept: Tipton's Under (54.8, never his 45.2 Over); neither side of a 50/50 tie; nothing for a lone Over at "
   "46%; the higher of two sides both over 50 (53 > 51); the anytime TD untouched; a wager with no number on any "
   "side left as it is; and an unpriced side never rides along with a priced favourite")
eq(O.prop_conflicts([r for r in _k if r["player"] != "Unrated"], key, val), [],
   "   ...and the guard finds nothing left to flag among the rows that carry a number (a wager with no number "
   "on either side has nothing to choose a side by, and is left as the card built it)")
eq(sorted(O.prop_conflicts([R("A", "over", 45.0), R("B", "over", 60.0), R("B", "under", 40.0)], key, val)),
   [(("g1", "A", "rec", 3.5), "a side the model gives under 50%"), (("g1", "B", "rec", 3.5), "a side the model gives under 50%"),
    (("g1", "B", "rec", 3.5), "both sides")],
   "🔴 the guard flags a side under 50% and a wager shown both ways")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE PROPS MODEL'S OWN PICK LIST: ONLY ITS 50%+ SIDE")
# ══════════════════════════════════════════════════════════════════════
MK, TD = "player_receptions", M.TD_MARKET
WHO = {0: ("Value Over", MK, 3.5, 162, -220, (0.45, 0.55)),   # the Tipton case: +EV only on the 45% side
       1: ("Fav Under", MK, 3.5, 162, 105, (0.45, 0.55)),      # both +EV; the old pick took the richer Over
       2: ("Coin Flip", MK, 3.5, 110, 110, (0.50, 0.50)),      # no favourite
       3: ("Td Scorer", TD, None, 400, None, (0.30, 0.70))}    # one-sided: yes at 30%, +EV
WF = {"final": {MK: types.SimpleNamespace(solve=lambda: "m"), TD: types.SimpleNamespace(solve=lambda: "m")},
      "s2_train": [],
      "H": types.SimpleNamespace(player={str(i): [(2026, {"team": "HOM"})] for i in WHO},
                                 features=lambda pid, season, mk, ctx: [float(pid)]),
      "logs": {2026: {str(i): {"name": w[0], "pos": "WR"} for i, w in WHO.items()}}}
WF["idx"] = M.name_index(WF["logs"])


def _side(px):
    return {"price": px, "books": {b: {"price": px} for b in ("hardrockbet", "fanduel", "draftkings")}}


_board = {"pulled_at": "2026-10-16T14:00:00Z", "games": [{
    "id": "e1", "home": "HOM", "away": "AWY", "commence": "2099-10-18T17:00:00Z",
    "props": [{"player": w, "market": mk, "line": ln,
               "sides": ({"yes": _side(ov)} if mk == TD else {"over": _side(ov), "under": _side(un)})}
              for w, mk, ln, ov, un, _p in WHO.values()]}]}
_old = (M.s1_probs, M.D.team_codes)
_t = tempfile.mkdtemp(prefix="oneprop-")
try:
    M.s1_probs = lambda mk, m, x, line: WHO[int(x[0])][5]
    M.D.team_codes = lambda lg: (lambda name: name)
    _rated = []
    _picks = M.current_picks("nfl", WF, root=_t, now="2026-10-16T15:00:00Z", rated=_rated, board=_board)
finally:
    M.s1_probs, M.D.team_codes = _old
    shutil.rmtree(_t, ignore_errors=True)
eq(sorted((p["player"], p["side"]) for p in _picks), [("Fav Under", "under"), ("Td Scorer", "yes")],
   "🔴 the live pick list: no pick on Value Over's 45% Over (+162) — its 55% Under does not pay; Fav Under's "
   "Under (55%, +105), never the richer 45% Over; nothing on a 50/50 prop; the anytime TD left as it was")
ck(len(_rated) == 7 and ("Value Over", "over", 45.0) in {(r["player"], r["side"], r["p"]) for r in _rated},
   "   ✅ every side is still RATED as it was (the card and the agreement label read these)",
   str(sorted((r["player"], r["side"], r["p"]) for r in _rated)))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 A WHOLE FOOTBALL CARD (the real card_fb.main): EVERY LIST, ONE SIDE PER PROP")
# ══════════════════════════════════════════════════════════════════════
_n = datetime.datetime.now(UTC)
_K = (_n + datetime.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
_P = (_n - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
# per game: (player, line, over price, under price, model over %, model under %)
_PL = [("Tipton", 3.5, 162, -220, 45.2, 54.8),      # the card's Under; the old liked list took the Over
       ("Robinson", 4.5, 115, -140, 49.8, 50.2),    # 49.8 shows "50": the old liked list took the Over
       ("Starter", 2.5, -150, 120, 62.0, 38.0)]     # a plain favourite Over
_GAMES = [("ev1", "Memphis Tigers", "Tulane Green Wave"), ("ev2", "Rutgers Scarlet Knights", "Maryland Terrapins")]
_T = tempfile.mkdtemp(prefix="oneprop-card-")


def put(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with (gzip.open(path, "wt", encoding="utf-8") if path.endswith(".gz") else open(path, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


def who(gi, w):
    return "%s %d" % (w, gi)


try:
    _L = os.path.join(_T, "data", "ncaaf", "latest")
    put(os.path.join(_L, "props.json.gz"), {"pulled_at": _P, "games": [
        {"id": gid, "away": a, "home": h, "commence": _K, "props": [
            {"player": who(gi, w), "market": MK, "line": ln,
             "sides": {"over": {"price": ov, "book": "fanduel", "n_books": 3},
                       "under": {"price": un, "book": "fanduel", "n_books": 3}}} for w, ln, ov, un, _o, _u in _PL]}
        for gi, (gid, a, h) in enumerate(_GAMES)]})
    put(os.path.join(_L, "players-2025.json.gz"), {"season": 2025, "players": {
        "%d-%d" % (gi, i): {"name": who(gi, w), "pos": "WR", "team": "T%d" % gi,
                            "g": [{"d": "2025-09-%02d" % (j + 6), "rec": 4, "rec_yds": 50} for j in range(8)]}
        for gi in range(2) for i, (w, *_x) in enumerate(_PL)}})
    put(os.path.join(_L, "fb-props-model.json"), {"board_pulled_at": _P, "picks": [], "rated": [
        {"game_id": gid, "player": who(gi, w), "market": MK, "line": ln, "side": s, "p": p}
        for gi, (gid, _a, _h) in enumerate(_GAMES) for w, ln, _ov, _un, po, pu in _PL
        for s, p in (("over", po), ("under", pu))]})
    _q = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, %r); import card_fb; card_fb.main()" % ROOT],
                        cwd=_T, capture_output=True, text=True, encoding="utf-8", timeout=900,
                        env=dict(os.environ, PYTHONUTF8="1", LEAGUE="ncaaf"))
    try:
        CARD = json.load(open(os.path.join(_T, "picks", "fb-ncaaf-latest.json"), encoding="utf-8"))
    except (OSError, ValueError):
        CARD = {}
        print(shown(_q.stdout[-1500:]), shown(_q.stderr[-1500:]))
finally:
    shutil.rmtree(_T, ignore_errors=True)
_ck = lambda r: (r.get("game_id"), r.get("player"), r.get("market"), r.get("line"))  # noqa: E731
_shown = {(r.get("player"), r.get("side")) for k in ("picks", "liked", "top_plays") for r in CARD.get(k) or []}
_legs = [leg for v in list((CARD.get("parlays") or {}).values()) + list((CARD.get("sgp") or {}).values())
         if isinstance(v, list) for p in v for leg in p.get("legs") or []]
ck(bool(CARD.get("picks")) and bool(_legs), "⚠️ the planted card was built, with a board and parlay legs",
   "%d picks, %d legs, rc %s" % (len(CARD.get("picks") or []), len(_legs), _q.returncode))
_allowed = {(who(gi, w), s) for gi in range(2) for w, s in (("Tipton", "under"), ("Robinson", "under"), ("Starter", "over"))}
ck(bool(_shown) and _shown <= _allowed,
   "🔴 board, liked list and top plays hold only each prop's 50%+ side: Tipton's and Robinson's Unders, the "
   "Starter's Over (the old liked list took Tipton's 45% and Robinson's 49.8% Overs)", str(sorted(_shown - _allowed)))
ck(any(r.get("player", "").startswith("Robinson") and r.get("side") == "under" for r in CARD.get("picks") or []),
   "🔴 Robinson's Under (50.2) stays on the board although his Over shows the same rounded 50")
_wrong = [leg for leg in _legs for gi in range(2) for w, side in (("Tipton", "o"), ("Robinson", "o"), ("Starter", "u"))
          if leg.startswith("%s %s" % (who(gi, w), side))]
eq(_wrong, [], "🔴 ...and no cross-game or same-game parlay leg is on a side under 50%")
eq(O.prop_conflicts([r for k in ("picks", "liked", "top_plays") for r in CARD.get(k) or []], _ck,
                    lambda r: r.get("model_p")), [],
   "🔴 the guard on the built card: no list shows a side under 50% or a prop both ways")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 MLB: THE POOLS KEEP THE SIDE THE PRINTED NUMBER FAVOURS")
# ══════════════════════════════════════════════════════════════════════
os.environ["LEAGUE"] = "mlb"
import card as C  # noqa: E402


def mp(pid, side, conf, line=12.5, alt=False, blend=None, mk="outs", game="g1"):
    return {"kind": "pitcher", "pid": pid, "pitcher": "P%d" % pid, "market": mk, "line": line, "side": side,
            "confidence": conf, "blend": blend, "alt_rung": alt, "game_id": game}


def mh(pid, side, conf, line=0.5):
    return {"kind": "hitter", "pid": pid, "player": "H%d" % pid, "market": "hits", "line": line, "side": side,
            "confidence": conf, "game_id": "g1"}


# pitcher 1: blend picked the Over, the printed numbers agree (60 / 40)
# pitcher 2: Nick Martinez 10-16 — blend 86% Over, printed Over 51 / Under 53: the numbers disagree
_p1o, _p1u = mp(1, "over", 60, blend=70.0), mp(1, "under", 40, blend=30.0)
_p2o, _p2u = mp(2, "over", 51, blend=85.9), mp(2, "under", 53, blend=14.1)
_r1o, _r1u = mp(1, "over", 35, line=14.5, alt=True), mp(1, "under", 65, line=14.5, alt=True)
_h1o, _h1u, _h2u = mh(7, "over", 62), mh(7, "under", 38), mh(8, "under", 45)
_plays, _all, _hit, _gone = C.one_side_pools([_p1o, _p2o], [_p1o, _p1u, _p2o, _p2u, _r1o, _r1u], [_h1o, _h1u, _h2u])
eq(([x["pid"] for x in _plays], sorted((x["pid"], x["side"], x["line"]) for x in _all),
    [(x["pid"], x["side"]) for x in _hit]),
   ([1], [(1, "over", 12.5), (1, "under", 14.5)], [(7, "over")]),
   "🔴 the board keeps pitcher 1's Over (blend and printed agree) and drops pitcher 2 (blend 86% Over, printed "
   "51 against the Under's 53); the pairs/top-10/parlay pool holds the board's own side and, on the 14.5 rung, "
   "the 65% Under; hitters keep only a side at 50%+ (H7's Over, not H8's lone 45% Under)")
_src = open(os.path.join(ROOT, "card.py"), encoding="utf-8").read()
_m = _src[_src.index("\ndef main("):]
ck(_m.index("hitters, _off_h = on_day(hitters, today)") < _m.index("one_side_pools(plays, plays_all, hitters)")
   < _m.index("pairs = build_pairs(plays_all)") < _m.index("top10, top10_drops = build_top10(plays_all, hitters)")
   < _m.index("board, seats_acct = select_board(plays, hitters)"),
   "🔴 card.main filters its pools after the single-day filter and BEFORE the pairs, the top 10, the parlays and "
   "the board are built")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE MLB CARD'S OWN GUARD, WHICH verify_card.py RUNS ON THE CARD main() BUILT")
# ══════════════════════════════════════════════════════════════════════
def krow(pid, side, conf, line=5.5):
    return {"kind": "pitcher", "pid": pid, "pitcher": "P%d" % pid, "market": "strikeouts", "line": line,
            "side": side, "confidence": conf, "game_id": "g1"}


def doc(case):
    picks, top10 = [krow(1, "over", 60)], [krow(1, "over", 60)]
    pairs = [{"label": "P1 o5.5 K + P2 o4.5 K", "leg_confidences": [60, 58]}]
    parlays = {"3": [{"label": "P1 o5.5 K + P2 o4.5 K + H3 o0.5 H", "leg_confidences": [60, 58, 55]}]}
    if case == "board_low":
        picks = picks + [krow(2, "over", 47)]
    if case == "both":
        picks = picks + [krow(1, "under", 52)]
    if case == "top_low":
        top10 = top10 + [krow(3, "under", 44, 6.5)]
    if case == "leg_low":
        pairs = [{"label": "P1 o5.5 K + P2 u4.5 K", "leg_confidences": [60, 46]}]
    if case == "parlay_low":
        parlays = {"3": [{"label": "P1 o5.5 K + P2 o4.5 K + H3 u0.5 H", "leg_confidences": [60, 58, 41]}]}
    if case == "star_low":
        picks = [dict(picks[0], ladder_pick={"line": 7.5, "side": "over", "blend": 41.0})]
    return {"picks": picks, "top10": top10, "pairs": pairs, "parlays": parlays}


_cases = ("clean", "board_low", "both", "top_low", "leg_low", "parlay_low", "star_low")
eq({c: bool(C.one_side_problems(doc(c))) for c in _cases},
   {"clean": False, "board_low": True, "both": True, "top_low": True, "leg_low": True, "parlay_low": True,
    "star_low": True},
   "🔴 the guard: a clean card passes; a board row at 47%, a prop shown both ways, a top-10 row at 44%, a pair leg "
   "at 46%, a parlay leg at 41% and a starred ladder rung at 41% are each caught")
_vsrc = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
ck("_osp = C.one_side_problems(doc)" in _vsrc and "not _osp" in _vsrc
   and _vsrc.index("doc = C.main(dry=True)") < _vsrc.index("_osp = C.one_side_problems(doc)"),
   "🔴 verify_card.py runs that guard on the card main() built, before every MLB card is committed")
