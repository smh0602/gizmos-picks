#!/usr/bin/env python3
"""test_whole_scores.py — football predicted scores in whole numbers that never contradict a pick.

`[Sam, 2026-10-17]` "in the game lines tab i see that the predicted scores are not whole numbers.
we need to not have decimal places in the predicted scores and make them only whole numbers";
asked how to round, he chose "Round, stay consistent": the nearest whole-number score that still
agrees with every pick shown for that game (plain rounding reads Texas -6 on a predicted 6.3 as
a push). `one_side.shown_score` is the rule, `card_fb.shown_scores` applies it to every game of
the week against the model's picks, the card's game lines and the parlay legs, and the why under
a pick prints the same numbers. Planted rows; ⛔ reads nothing live.

# @vacuity 🔴 the expected winner leads the whole score (a near-tie never prints as a tie)
#   file: one_side.py
#   find:             if winner in ("home", "away") and lead != winner:
#   with:             if False:
#
# @vacuity 🔴 every pick the model's score agrees with still agrees with the whole score
#   file: one_side.py
#   find:             if any(lead != b for b in mls) or not all(score_side_ok(r, s, point(r)) for r in need):
#   with:             if any(lead != b for b in mls):
#
# @vacuity 🔴 ...a moneyline pick's team leads it too
#   file: one_side.py
#   find:             if any(lead != b for b in mls) or not all(score_side_ok(r, s, point(r)) for r in need):
#   with:             if not all(score_side_ok(r, s, point(r)) for r in need):
#
# @vacuity 🔴 ...and of those, the NEAREST to the model's score
#   file: one_side.py
#   find:             key = ((h - h0) ** 2 + (a - a0) ** 2, abs((h - a) - (h0 - a0)), abs((h + a) - (h0 + a0)), -h)
#   with:             key = (-(h - h0) ** 2 - (a - a0) ** 2, abs((h - a) - (h0 - a0)), abs((h + a) - (h0 + a0)), -h)
#
# @vacuity 🔴 the card turns a model pick's home-margin line into the team's own point
#   file: card_fb.py
#   find:                 ln = -ln if p.get("side") == "home" else ln   # M on the home margin -> own point
#   with:                 ln = ln
#
# @vacuity 🔴 the card's game lines constrain the whole score
#   file: card_fb.py
#   find:         rows += [r for r in game_lines or [] if r.get("game") == g]
#   with:         rows += []
#
# @vacuity 🔴 ...and so do the same-game parlays' line legs, at their own point
#   file: card_fb.py
#   find:         rows += [dict(r, line=r.get("point")) for r in legs or [] if r.get("game") == g]
#   with:         rows += []
#
# @vacuity 🔴 the why under a game-line pick prints the card's whole score
#   file: fb_why.py
#   find:         ctx.scores = {**ctx.scores, **scores}
#   with:         pass
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "ncaaf")
import one_side as O  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE RULE: THE NEAREST WHOLE SCORE THAT AGREES WITH EVERY PICK")
# ══════════════════════════════════════════════════════════════════════
SP = lambda side, pt: {"market": "spread", "side": side, "line": pt}  # noqa: E731
TOT = lambda side, ln: {"market": "total", "side": side, "line": ln}  # noqa: E731
eq(O.shown_score({"home": 23.4, "away": 17.1}, [SP("home", -6)], "home"), {"home": 24, "away": 17},
   "🔴 Sam's example: Texas -6 on a predicted 6.3-point win prints a 7-point win (24-17), never a push (23-17)")
eq(O.shown_score({"home": 23.4, "away": 17.1}, [], "home"), {"home": 23, "away": 17},
   "   ...with nothing to agree with, it is the plain nearest (23-17)")
eq(O.shown_score({"home": 17.4, "away": 23.0}, [SP("away", -5.5)], "away"), {"home": 17, "away": 23},
   "🔴 Baylor -5.5 on a predicted 5.6 prints a 6-point win (`[2026-10-16]` plain rounding read 18-23)")
eq(O.shown_score({"home": 20.4, "away": 20.2}, [], "home"), {"home": 21, "away": 20},
   "🔴 a near-tie beside a pick to win prints the winner ahead (21-20), never 20-20")
eq(O.shown_score({"home": 24.0, "away": 23.3}, [TOT("under", 47.5)], "home"), {"home": 24, "away": 23},
   "🔴 an Under 47.5 on a predicted 47.3 prints a total under 47.5 (24-23, not 24-24's 48)")
eq([O.shown_score({"home": 21.4, "away": 21.3}, [{"market": "moneyline", "side": "home"}], None),
    O.shown_score({"home": 21.4, "away": 21.3}, [], None)],
   [{"home": 22, "away": 21}, {"home": 21, "away": 21}],
   "🔴 a moneyline pick's team leads the whole score (22-21), where plain rounding ties it (21-21)")
eq([O.shown_score({"home": 23.2, "away": 20.0}, [SP("home", -3), SP("away", 3.5)], "home"),
    O.shown_score(None, [SP("home", -3)], "home"), O.shown_score({"home": None, "away": 3}, [], "home")],
   [None, None, None],
   "🔴 no whole score between a -3 and a +3.5 that both hold (above 3, below 3.5): None, never a "
   "contradiction; no score: None")
eq(O.shown_score({"home": 24.0, "away": 23.3}, [TOT("over", 47.5)], "home"), {"home": 24, "away": 23},
   "   ...and a row the model's own score does NOT agree with (a frozen Over 47.5 on 47.3) constrains "
   "nothing: the plain nearest with the winner ahead (24-23)")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 EVERY GAME OF THE WEEK, AGAINST EVERY PICK SHOWN FOR IT")
# ══════════════════════════════════════════════════════════════════════
import card_fb as CF  # noqa: E402
WASH, PUR, TEX, FLA = "Washington Huskies", "Purdue Boilermakers", "Texas Longhorns", "Florida Gators"
WIN = [{"away": WASH, "home": PUR, "p_home": 52.9, "score": {"home": 24.4, "away": 23.0}},
       {"away": FLA, "home": TEX, "p_home": 75.0, "score": {"home": 30.4, "away": 24.1}},
       {"away": "A", "home": "B", "p_home": 50.0, "score": None},
       # only the card's game line decides this one, and only the parlay leg the next
       {"away": "C", "home": "D", "p_home": 60.0, "score": {"home": 20.4, "away": 17.2}},
       {"away": "E", "home": "F", "p_home": 55.0, "score": {"home": 27.6, "away": 27.2}}]
# the model's own picks: Purdue -1 at home is M = 1 on the home margin (own point -1);
#    a model Texas -6 is M = 6
MODEL = [{"game": "%s at %s" % (WASH, PUR), "market": "spread", "side": "home", "line": {"value": 1.0}},
         {"game": "%s at %s" % (FLA, TEX), "market": "spread", "side": "home", "line": {"value": 6.0}}]
# the card: Washington's moneyline would be off the winner (a frozen row: constrains nothing); a
#    Texas alternate -5.5; a parlay leg Under 55.5 in Florida @ Texas (a predicted 54.5)
GLS = [{"game": "%s @ %s" % (FLA, TEX), "away": FLA, "home": TEX, "market": "alternate_spread",
        "side": "home", "line": -5.5},
       {"game": "C @ D", "away": "C", "home": "D", "market": "spread", "side": "home", "line": -3}]
LEGS = [{"game": "%s @ %s" % (FLA, TEX), "market": "totals", "side": "Under", "point": 55.5},
        {"game": "E @ F", "market": "totals", "side": "Under", "point": 55}]
SH = {(x["away"], x["home"]): x["score"] for x in CF.shown_scores(WIN, MODEL, GLS, LEGS)}
eq(SH, {(WASH, PUR): {"home": 25, "away": 23}, (FLA, TEX): {"home": 31, "away": 24}, ("A", "B"): None,
         ("C", "D"): {"home": 21, "away": 17}, ("E", "F"): {"home": 28, "away": 26}},
   "🔴 Purdue -1 on 1.4 prints 25-23 (plain 24-23 would land ON -1); Texas -6 and -5.5 on 6.3 print "
   "31-24 (plain 30-24 would push the -6) and keep the Under 55.5 (55); the card's D -3 on 3.2 prints "
   "21-17 (plain 20-17 pushes); the parlay leg Under 55 on 54.8 prints 28-26 (plain 28-27 lands ON 55); "
   "no score: None")
_bad = []
for w in WIN:
    s = SH[(w["away"], w["home"])]
    if not s:
        continue
    g = "%s @ %s" % (w["away"], w["home"])
    rows = ([{"market": "spread", "side": p["side"], "game": g,
              "line": -p["line"]["value"] if p["side"] == "home" else p["line"]["value"]}
             for p in MODEL if p["game"] == "%s at %s" % (w["away"], w["home"])]
            + [r for r in GLS if r["game"] == g] + [dict(r, line=r["point"]) for r in LEGS if r["game"] == g])
    for r in rows:
        if O.score_side_ok(r, w["score"], r["line"]) and not O.score_side_ok(r, s, r["line"]):
            _bad.append((g, r))
    if (s["home"] > s["away"]) != (O.expected_side(w["p_home"]) == "home"):
        _bad.append((g, "winner"))
eq(_bad, [], "🔴 the guard: in every game, every pick the model's score agrees with agrees with the whole "
   "score, and the expected winner leads")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE WHY UNDER A GAME-LINE PICK PRINTS THE SAME WHOLE SCORE")
# ══════════════════════════════════════════════════════════════════════
import fb_why as WY  # noqa: E402


class _Ctx:
    scores = {(FLA, TEX): {"home": 30.4, "away": 24.1}}
    resolve = staticmethod(lambda name: None)

    def pf_pa(self, team):
        return None


_row = {"kind": "fb-line", "market": "spread", "side": "home", "line": -6, "away": FLA, "home": TEX,
        "why": ["The game model gives Texas Longhorns 58% to cover -6."]}
_why = WY.explain([dict(_row)], "ncaaf", "", kind="lines", ctx=_Ctx(), scores={(FLA, TEX): {"home": 31, "away": 24}})[0]["why"]
ck(any("predicted score: Florida Gators 24, Texas Longhorns 31 (total 55)" in w for w in _why),
   "🔴 the why prints the card's whole score (24-31, total 55), the Game Lines tab's numbers, never the "
   "model's 24.1-30.4", str(_why))

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE CARD MAKES THEM AND HANDS THEM TO THE WHY AND THE TAB")
# ══════════════════════════════════════════════════════════════════════
_main = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
_main = _main[_main.index("\ndef main("):]
ck('scores_shown = shown_scores(_model.get("win_chances") or [], _model.get("picks") or [],' in _main
   and "game_lines, _gl_all)" in _main and 'kind="lines", scores=_whole),' in _main
   and '"scores_shown": scores_shown,' in _main,
   "🔴 card_fb.main makes the week's whole scores from the model's picks, the card's game lines and the "
   "parlay legs, prints them in the why and writes them on the card (winners.json reads them there)")
