#!/usr/bin/env python3
"""FOOTBALL PROPS: THE CARD SHOWS THE PROPS MODEL'S OWN CHANCE. `[Sam, 2026-10-11]`

"only show confidence score on each pick that the model picks, BASED ON THE
MODELS CONFIDENCE SCORE NOT THE SPORTSBOOKS." Stage 2 is stage 1 corrected by
its own past misses, with no price (~~stage 1 mixed with the books' chance~~),
applied whether or not a price exists. Planted board and history only; nothing
here reads the live data tree.
  1. Changing every price leaves every rated side's chance unchanged.
  2. That chance is stage 1 corrected by its own misses, never stage 1 raw.
  3. The Track Record opens a new method and keeps the old bands as graded.

# @vacuity 🔴 a shown chance never reads the books' chance
#   file: fb_props_model.py
#   find: "side": _side, "p": round(100 * _p, 1)})
#   with: "side": _side, "p": round(100 * (market_prob(mk, rung) if _side == "over" and market_prob(mk, rung) else _p), 1)})
#
# @vacuity 🔴 stage 2 is applied, priced or not
#   file: fb_props_model.py
#   find:     if s2 is not None:
#   with:     if False:
#
# @vacuity 🔴 the Track Record opens a new method at the switch
#   file: card_fb.py
#   find: METHOD_PROPS_MODEL = "+props-own"
#   with: METHOD_PROPS_MODEL = "+props-model"
"""
import os
import random
import sys
import tempfile
import shutil
import types

from tcheck import ck, eq, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
import card_fb as CF  # noqa: E402
import fb_props_model as M  # noqa: E402
import record_fb as R  # noqa: E402

MK = "player_reception_yds"
WHO = ["Wide One", "Wide Two", "Wide Three"]
# Stage 1 runs hot: it says 86% on rungs that hit about half the time.
_rnd = random.Random(9)
S2_TRAIN = [(M.s2_features(MK, 0.86), 1 if _rnd.random() < 0.5 else 0) for _ in range(400)]
WF = {"final": {MK: types.SimpleNamespace(solve=lambda: "m")}, "s2_train": S2_TRAIN,
      "H": types.SimpleNamespace(player={str(i): [(2026, {"team": "HOM"})] for i in range(3)},
                                 features=lambda pid, season, mk, ctx: [1.0]),
      "logs": {2026: {str(i): {"name": w, "pos": "WR"} for i, w in enumerate(WHO)}}}
WF["idx"] = M.name_index(WF["logs"])


def board(flip):
    """One unstarted game, three receivers at 40.5, both sides at all three books;
    `flip` moves every price and makes the other side the favourite."""
    def side(px):
        return {"price": px, "books": {b: {"price": px - d} for b, d in
                                       (("hardrockbet", 0), ("fanduel", 5), ("draftkings", 10))}}
    return {"pulled_at": "2026-10-11T14:00:00Z", "games": [{
        "id": "e1", "home": "HOM", "away": "AWY", "commence": "2099-10-11T17:00:00Z",
        "props": [{"player": w, "market": MK, "line": 40.5,
                   "sides": ({"over": side(130 + 10 * i), "under": side(-160 - 10 * i)} if flip else
                             {"over": side(-120 - 10 * i), "under": side(105 + 10 * i)})}
                  for i, w in enumerate(WHO)]}]}


def rated(flip):
    out, old = [], (M.s1_probs, M.D.team_codes)
    t = tempfile.mkdtemp(prefix="pown-")
    try:
        M.s1_probs = lambda mk, m, x, line: (0.86, 0.14)
        M.D.team_codes = lambda lg: (lambda name: name)
        M.current_picks("nfl", WF, root=t, now="2026-10-11T15:00:00Z", rated=out, board=board(flip))
    finally:
        M.s1_probs, M.D.team_codes = old
        shutil.rmtree(t, ignore_errors=True)
    return sorted((r["player"], r["side"], r["p"]) for r in out)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 A PRICE NEVER MOVES A PROPS CHANCE")
# ══════════════════════════════════════════════════════════════════════
_a, _b = rated(False), rated(True)
ck(len(_a) == 6 and _a == _b, "🔴 every rated side keeps its chance when every price moves and the favourite flips",
   "%s vs %s" % (_a[:2], _b[:2]))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 ...AND IT IS STAGE 1 CORRECTED BY ITS OWN MISSES")
# ══════════════════════════════════════════════════════════════════════
_fit = M.F.fit([x for x, _ in S2_TRAIN], [y for _, y in S2_TRAIN])
_want = round(100 * M.F.predict(_fit, M.s2_features(MK, 0.86)), 1)
eq({p for _w, s, p in _a if s == "over"}, {_want},
   "🔴 stage 1 says 86%%; corrected by its own past misses (about half hit) the card shows %s%%" % _want)
ck(abs(_want - 86.0) > 20, "⚠️ the correction really moves the number, so the check asks something")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE TRACK RECORD OPENS A NEW METHOD; THE OLD BANDS STAY AS GRADED")
# ══════════════════════════════════════════════════════════════════════
_old_m, _new_m = CF.METHOD_FIXED + "+props-model", CF.METHOD_FIXED + CF.METHOD_PROPS_MODEL
ck(_new_m not in (_old_m, CF.METHOD_FIXED, CF.METHOD_CURRENT), "🔴 the switch is a new method",
   _new_m)
_old = [{"confidence": 72, "won": i < 4, "card_method": _old_m} for i in range(10)]
_new = [{"confidence": 55, "won": i < 6, "card_method": _new_m} for i in range(10)]
_cur, _by = R.calibration_by_method(_old + _new, _new_m)
eq((_by.get(_old_m), _cur), (R.calibration_by_method(_old, _old_m)[0], R.calibration_by_method(_new, _new_m)[0]),
   "🔴 the old method's band is exactly its own rows, and the new method opens its own")
