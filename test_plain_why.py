#!/usr/bin/env python3
"""test_plain_why.py — no pick's "why" carries a caveat sentence, all three leagues.

`[Sam, 2026-11-18]` Asked: "MLB's 'why' under every hitter pick ends with 'One thing to know:
that number is his own track record at this exact line, not a projection - we don't have a
hitter model yet...' ... Pitcher rows add 'That's recent history, not part of the model's
math'. Football's whys dropped their caveat sentences on 10-09 at your request. Drop MLB's the
same way, from the first 2027 card? Published cards are not touched, and the 'may not play
tonight' lineup warning stays." He chose "Drop them like football": "The 'One thing to know'
line and the 'not part of the model's math' endings go."

Planted rows and planted cards only; nothing here reads the live data tree or the clock.
  1. ONE list (`plain_why.PHRASES`) catches every caveat sentence either league removed.
  2. The MLB whys card.py writes, on planted rows reaching every removed branch, carry none of
     them; the stat in each sentence stays, the lineup-risk clause stays, and every label stays
     in the DATA (RECORD, DESCRIPTIVE); the opponent log still feeds no number.
  3. `card.why_caveats` checks every list of a card this code built, never a published one.
  4. verify_card.py's own lines, run on planted cards: red on a caveat, green without one, silent
     on a card published before the change, red on a new card that lost its stamp.
  5. Football reads the same list, and its own whys are plain under it.

# @vacuity 🔴 the hitter's "One thing to know" line never comes back
#   file: card.py
#   find: f"time just to break even. His own record puts it at <b>{rate:.0f}%</b>.")
#   with: f"time just to break even. His own record puts it at <b>{rate:.0f}%</b>."); w.append("One thing to know: that number is his own track record at this exact line, not a projection.")
#
# @vacuity 🔴 ...nor the hitter's small-sample warning
#   file: card.py
#   find: w.append(f"Against {opp} he's {vh} for {vn} on this line.")
#   with: w.append(f"Against {opp} he's {vh} for {vn} on this line." + (" Too small a sample to read much into." if vn < 8 else ""))
#
# @vacuity 🔴 ...nor the pitcher's "not part of the model's math" ending
#   file: card.py
#   find: f"and <b>{same} of {r['n']}</b> landed on this side of {line}.")
#   with: f"and <b>{same} of {r['n']}</b> landed on this side of {line}. That's recent history, not part of the model's math.")
#
# @vacuity 🔴 ...on the outs line too
#   file: card.py
#   find: f"<b>{same} of {r['n']}</b> finished on this side of {line} outs.")
#   with: f"<b>{same} of {r['n']}</b> finished on this side of {line} outs. That's recent history, not part of the model's math.")
#
# @vacuity 🔴 ...nor the pitcher's small-sample warning
#   file: card.py
#   find: f"{'s' if vs[1] > 1 else ''} and {verb} it {vs[0]}.")
#   with: f"{'s' if vs[1] > 1 else ''} and {verb} it {vs[0]}." + (" That's too small a sample to read much into." if vs[1] < 4 else ""))
#
# @vacuity 🔴 ...nor "nothing to read there"
#   file: card.py
#   find: f"{ab(opp_team)} exist this season.")
#   with: f"{ab(opp_team)} exist this season, so there's nothing to read there either way.")
#
# @vacuity 🔴 the hitter's why still gives his record as the number
#   file: card.py
#   find: f"time just to break even. His own record puts it at <b>{rate:.0f}%</b>.")
#   with: f"time just to break even.")
#
# @vacuity 🔴 the hitter row stays labelled RECORD in the data
#   file: card.py
#   find:         "confidence_basis": "RECORD",
#   with:         "confidence_basis": "MODEL",
#
# @vacuity 🔴 the opponent's recent starter log still feeds no number (T36)
#   file: card.py
#   find:     shown = pcal.corrected(PCAL, market, blend, be)
#   with:     blend = blend + (opp_recent or {}).get("mean_k", 0) / 10; shown = pcal.corrected(PCAL, market, blend, be)
#
# @vacuity 🔴 a card published before the change is never checked
#   file: card.py
#   find:     if not isinstance(doc, dict) or doc.get("why_rule") != WHY_RULE:
#   with:     if not isinstance(doc, dict):
#
# @vacuity 🔴 every list the card holds is walked, not only the board
#   file: card.py
#   find:                 if k != "why":
#   with:                 if k == "picks":
#
# @vacuity 🔴 a phrase inside a tag is still a phrase
#   file: plain_why.py
#   find:     return _TAG.sub("", str(text or "")).replace(chr(0x2019), "'").replace(chr(0x2018), "'").lower()
#   with:     return str(text or "").replace(chr(0x2019), "'").replace(chr(0x2018), "'").lower()
#
# @vacuity 🔴 verify_card.py runs the guard on the card main() built
#   file: verify_card.py
#   find: _cav = C.why_caveats(doc)
#   with: _cav = []
#
# @vacuity 🔴 verify_card.py fails a new card that lost its stamp
#   file: verify_card.py
#   find:    doc.get('why_rule') == C.WHY_RULE or str(doc.get('date') or '') <= '2026-11-18',
#   with:    True,
#
# @vacuity 🔴 verify_card.py's hitter check asks for the row's own number
#   file: verify_card.py
#   find:          or not any("His own record puts it at <b>%s%%</b>" % r.get('confidence') in w
#   with:          or not any("His own record puts it at" in w
"""
import ast
import copy
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "mlb"
from tcheck import ck, eq, section, shown  # noqa: E402

import card  # noqa: E402
import plain_why  # noqa: E402

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 ONE LIST CATCHES EVERY CAVEAT SENTENCE EITHER LEAGUE REMOVED")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ The sentences as the code wrote them before each removal (MLB: card.py to 2026-11-18;
#    football: card_fb.build_why to 2026-10-09), names and numbers planted.
REMOVED_MLB = [
    "He has faced SEA 2 times and cleared it 2. That's too small a sample to read much into.",
    "Only 2 comparable starts against SEA exist this season, so there's nothing to read there "
    "either way.",
    "The last 10 starters to face SEA averaged <b>6.2 strikeouts</b> over 5.2 innings, and <b>6 of "
    "10</b> landed on this side of 5.5. That's recent history, not part of the model's math.",
    "Against SEA he's 1 for 3 on this line. Too small a sample to read much into.",
    "One thing to know: that number is his own track record at this exact line, not a projection "
    "— we don't have a hitter model yet, so this is history rather than a forecast.",
    "⚠️ Too few to mean anything.",
    "⚠️ Home/road is DESCRIPTIVE here — it has never been tested on hitters in this project.",
]
REMOVED_FB = [
    "College box scores list a player only when he did something, so a game he played quietly "
    "can be missing from that count — which nudges an over slightly high.",
    "⚠️ That line is a long way from what he actually did last season, which usually means his "
    "role has changed. His record is history; it is not evidence about a line he never faced.",
    "That is a small sample — too few games to read much into on its own.",
    "This is his own record from last season, not a forecast. Rosters and roles change between "
    "seasons, so read it as history rather than a prediction.",
]
ck(len(plain_why.PHRASES) >= 10 and all(p == p.lower() for p in plain_why.PHRASES),
   "⚠️ the list is there, and every phrase is lower case (it is matched lower case)",
   str(plain_why.PHRASES[:4]))
eq([s[:40] for s in REMOVED_MLB + REMOVED_FB if not plain_why.found(s)], [],
   "🔴 every caveat sentence MLB (to 11-18) and football (to 10-09) wrote is caught")
eq([plain_why.found(s) for s in ("<b>Too small</b> a sample to read much into.",
                                 "That's recent history, not part of the model" + chr(0x2019) + "s math.",
                                 "ONE THING TO KNOW: it is his record.")],
   [["small a sample", "read much into"], ["part of the model's math", "recent history"],
    ["one thing to know"]],
   "🔴 ...inside a tag, with a curly apostrophe, in capitals")
eq([plain_why.found(s) for s in (
    "He has faced SEA 2 times and cleared it 2.",
    "Only 2 comparable starts against SEA exist this season.",
    "He's been in the lineup for <b>60%</b> of his team's games, so there's a real chance he "
    "doesn't play tonight — that usually voids the bet rather than losing it.",
    "The game model gives Milwaukee Brewers 61% to win. It expects 3.9 runs to 2.9.",
    "<b>Model Guy</b> went over 3.5 rec in <b>4 of 4 games</b> in 2026, when he played at least "
    "half the snaps.")],
   [[]] * 5, "✅ a stat sentence is never caught (the count, the lineup risk, a game line, football's)")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE MLB WHYS card.py WRITES: NO CAVEAT, THE STAT STAYS, THE LABELS STAY IN THE DATA")
# ══════════════════════════════════════════════════════════════════════
TODAY = "2026-09-20"
GAME = {"home": "HOU", "away": "SEA", "id": "g1", "commence": "2026-09-20T20:10:00Z"}


def _starts():
    out = [{"d": "2026-08-%02d" % (2 + 4 * j), "gs": True, "k": 6 + (j % 3), "outs": 17 + (j % 3),
            "np": 92 + j, "o": "TEX"} for j in range(6)]
    return out + [{"d": "2026-09-%02d" % (3 + 5 * j), "gs": True, "k": 9, "outs": 18, "np": 95, "o": "SEA"}
                  for j in range(2)]


PITCHERS = {
    101: {"name": "Ace One", "team": "HOU", "era": "3.40", "whip": 1.15, "throws": "R", "g": _starts()},
    # another team's starter who faced SEA eight times: the opponent's recent starter log
    201: {"name": "Arm Two", "team": "TEX", "era": "4.10", "whip": 1.3, "throws": "L",
          "g": [{"d": "2026-09-%02d" % (1 + 2 * j), "gs": True, "k": 4 + j % 4, "outs": 15 + j % 4,
                 "np": 90, "o": "SEA"} for j in range(8)]}}


def pitcher_row(mk, line):
    prop = {"market": mk, "line": line, "side": "over", "price": -120, "book": "draftkings", "pid": 101}
    return card.build_play(prop, PITCHERS[101], PITCHERS, 8.0, 8.0, 6, GAME, TODAY, {"SEA": 5})


def hitter_row(vs, team_games):
    prop = {"market": "batter_hits", "line": 0.5, "side": "over", "price": -150, "book": "hardrockbet",
            "hr": {"price": -150, "book": "hardrockbet", "link": "x"},
            "player": "Bat Man", "pid": 300, "team": "HOU",
            "evidence": {"season": "40/60", "last15": "11/15", "home": "21/30", "road": "19/30",
                         "vs_opp": vs, "opp": "SEA"}}
    return card.hitter_play(prop, GAME, {}, {"HOU": team_games}, None, TODAY)


PK, PO = pitcher_row("pitcher_strikeouts", 5.5), pitcher_row("pitcher_outs", 16.5)
H_RISK, H_FULL = hitter_row("1/3", 100), hitter_row("6/12", 70)
ROWS = [PK, PO, H_RISK, H_FULL]
ck(all(isinstance(r, dict) and r.get("why") for r in ROWS), "⚠️ every planted row is built, with a why",
   str([r if not isinstance(r, dict) else r.get("why") for r in ROWS])[:300])
if not all(isinstance(r, dict) for r in ROWS):
    raise SystemExit(1)
_pw = " ".join(PK["why"])
ck(PK.get("opp_recent") and PO.get("opp_recent") and "He has faced SEA 2 times" in _pw
   and "Only " in _pw and H_RISK["lineup_risk"] and not H_FULL["lineup_risk"],
   "⚠️ rule 67: the rows reach every branch a caveat sat in (two meetings, a few comparable starts, "
   "the opponent log on both markets, a hitter 1 for 3 against them, a bench bat)",
   shown(_pw[:300]))
eq([(r.get("pitcher") or r.get("player"), w[:50]) for r in ROWS for w in r["why"] if plain_why.found(w)], [],
   "🔴 no why line card.py writes carries a caveat phrase")
eq([w for w in PK["why"] if w.startswith("Ace One")][0].split(" — ")[1],
   "8 of 8 on the road. He has faced SEA 2 times and cleared it 2.",
   "🔴 the meetings sentence keeps its count and ends there")
ck("Only 2 comparable starts against SEA exist this season." in PK["why"],
   "🔴 the comparable-starts sentence keeps its count and ends there", shown(str(PK["why"])))
ck(any(w.endswith("landed on this side of 5.5.") for w in PK["why"])
   and any(w.endswith("finished on this side of 16.5 outs.") for w in PO["why"]),
   "🔴 the opponent log's sentence keeps its numbers and ends on them, both markets",
   shown(str([w[-60:] for w in PK["why"] + PO["why"]])))
eq((H_RISK["why"][1], H_FULL["why"][1]),
   ("Against SEA he's 1 for 3 on this line.", "Against SEA he's 6 for 12 on this line."),
   "🔴 the hitter's meetings sentence keeps its count and ends there")
ck(any("there's a real chance he doesn't play tonight — that usually voids the bet rather than losing it."
       in w for w in H_RISK["why"]),
   "✅ the lineup-risk clause STAYS (Sam: 'the may not play tonight lineup warning stays')",
   shown(str(H_RISK["why"])))
eq([r["why"][-1] for r in (H_RISK, H_FULL)],
   ["At <b>-150</b> this has to hit about <b>60%%</b> of the time just to break even. "
    "His own record puts it at <b>%d%%</b>." % H_RISK["confidence"]] * 2,
   "🔴 a hitter's why ends on his record as the number: nothing after it")
eq([(r["confidence_basis"], "no hitter model" in r["confidence_note"], "not a projection" in r["confidence_note"],
     "MARKET" in r["basis"]) for r in (H_RISK, H_FULL)], [("RECORD", True, True, True)] * 2,
   "🔴 every hitter label stays in the DATA: RECORD, 'no hitter model ... not a projection'")
eq([(r["confidence_basis"], r["opp_recent"]["basis"], "DESCRIPTIVE" in r["opp_recent"]["note"])
    for r in (PK, PO)], [("MODEL", "DESCRIPTIVE", True)] * 2,
   "🔴 the opponent log stays DESCRIPTIVE in the DATA, its note saying so")

# The opponent log still feeds no number (T36): the same row with no log and with a wild one.
_real = card.opponent_starters
_NUM = ("confidence", "confidence_value", "blend", "carried", "band", "model", "edge")
try:
    card.opponent_starters = lambda *a, **k: None
    _none = pitcher_row("pitcher_strikeouts", 5.5)
    card.opponent_starters = lambda *a, **k: dict(_real(*a, **k), mean_k=19.0, mean_outs=27.0)
    _wild = pitcher_row("pitcher_strikeouts", 5.5)
finally:
    card.opponent_starters = _real
ck(_none.get("opp_recent") is None and _wild["opp_recent"]["mean_k"] == 19.0,
   "⚠️ the two rows differ in their opponent log only")
eq([{k: r[k] for k in _NUM} for r in (_none, _wild)], [{k: PK[k] for k in _NUM}] * 2,
   "🔴 no log, or a wild one: the same confidence, blend, carried, band, model and edge")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 card.why_caveats: EVERY LIST OF A CARD THIS CODE BUILT, NEVER A PUBLISHED ONE")
# ══════════════════════════════════════════════════════════════════════
GL = {"kind": "mlb-line", "player": "Houston Astros", "market": "moneyline",
      "why": ["The game model gives Houston Astros 61% to win. It expects 3.9 runs to 2.9."]}


def planted(stamp=card.WHY_RULE, date="2027-04-01"):
    d = {"date": date, "picks": copy.deepcopy([PK, PO, H_RISK, H_FULL]),
         "below_price_floor": [], "top10": copy.deepcopy([H_FULL, PK]),
         "game_lines": [copy.deepcopy(GL)],
         "parlays": {"two_leg": [{"legs": [copy.deepcopy(H_RISK)]}]}}
    if stamp is not None:
        d["why_rule"] = stamp
    return d


CAVEAT = "That's recent history, not part of the model's math."
eq(card.why_caveats(planted()), [], "✅ a card this code built: nothing to report")
_cases = {}
for where, get in (("picks", lambda d: d["picks"][0]), ("top10", lambda d: d["top10"][0]),
                   ("game_lines", lambda d: d["game_lines"][0]),
                   ("a parlay leg", lambda d: d["parlays"]["two_leg"][0]["legs"][0])):
    _d = planted()
    get(_d)["why"].append(CAVEAT)
    _cases[where] = [(w, p) for w, p, _l in card.why_caveats(_d) or []]
eq(_cases, {"picks": [("Ace One", "part of the model's math"), ("Ace One", "recent history")],
            "top10": [("Bat Man", "part of the model's math"), ("Bat Man", "recent history")],
            "game_lines": [("Houston Astros", "part of the model's math"), ("Houston Astros", "recent history")],
            "a parlay leg": [("Bat Man", "part of the model's math"), ("Bat Man", "recent history")]},
   "🔴 a caveat is found in every list the card holds, named by its row")
_old = planted(stamp=None, date="2026-10-28")
_old["picks"][2]["why"].append(REMOVED_MLB[4])
eq((card.why_caveats(_old), card.why_caveats(dict(_old, why_rule="plain-2020-01-01"))), (None, None),
   "🔴 a card with no stamp (or another one) was published before the change: never checked, "
   "never rebuilt")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 verify_card.py's OWN LINES, ON PLANTED CARDS")
# ══════════════════════════════════════════════════════════════════════
_VSRC = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
_A, _B = "# 🔴 [Sam, 2026-11-18] THE WHY CARRIES NO CAVEAT SENTENCE.", 'print("\\n38.'
_SLICE = (_VSRC[_VSRC.index(_A):_VSRC.index(_B)]
          if _A in _VSRC and _B in _VSRC and _VSRC.index(_A) < _VSRC.index(_B) else "")
ck("C.why_caveats(doc)" in _SLICE and _SLICE.count("ck(") >= 3,
   "⚠️ rule 67: the section's lines were read out of verify_card.py",
   "⛔ an empty slice runs nothing, and every check below would pass on nothing")
ck(_VSRC.index("doc = C.main(dry=True)") < _VSRC.index("_cav = C.why_caveats(doc)")
   if "_cav = C.why_caveats(doc)" in _VSRC else False,
   "🔴 ...and verify_card.py runs them on the card main() built, before the card is committed")
HITTER, STAMP, CAV = ("every hitter row's why gives its number as his own record",
                      "a card dated after Sam's 2026-11-18 change carries the why stamp",
                      "no why on the card carries a caveat sentence")


def verify(doc):
    """verify_card.py's own section on `doc` -> {check: ok} (a check that did not run is absent)."""
    got = {}

    def _ck(name, ok, detail=""):
        got[re.sub(r"\s*\(\d+ rows\)", "", name)] = bool(ok)
    rows = (doc.get("picks") or []) + (doc.get("below_price_floor") or [])
    exec(compile(_SLICE, "verify_card.py#plain-why", "exec"),
         {"doc": doc, "hit_rows": [r for r in rows if r.get("kind") == "hitter"], "C": card,
          "ck": _ck, "print": lambda *a, **k: None})
    return got


def with_line(doc, idx, line):
    doc["picks"][idx]["why"].append(line)
    return doc


eq(verify(planted()), {HITTER: True, STAMP: True, CAV: True}, "✅ a card this code built passes all three")
eq(verify(with_line(planted(), 2, REMOVED_MLB[4])).get(CAV), False,
   "🔴 the hitter's 'One thing to know' line back on a new card: FAIL")
eq(verify(with_line(planted(), 0, CAVEAT)).get(CAV), False,
   "🔴 the pitcher's 'not part of the model's math' ending back on a new card: FAIL")
eq(verify(with_line(planted(stamp=None, date="2026-10-28"), 2, REMOVED_MLB[4])), {HITTER: True, STAMP: True},
   "🔴 a card published before the change, caveats and all: nothing fails, and the caveat check does "
   "not run on it (published cards are permanent)")
eq(verify(planted(stamp=None)).get(STAMP), False,
   "🔴 a card dated after the change without the stamp: FAIL (the guard cannot be switched off "
   "by losing the stamp)")
_nr = planted()
_nr["picks"][2]["why"] = _nr["picks"][2]["why"][:-1]
_wn = planted()
_wn["picks"][3]["why"][-1] = _wn["picks"][3]["why"][-1].replace(
    "<b>%d%%</b>" % H_FULL["confidence"], "<b>%d%%</b>" % (H_FULL["confidence"] + 3))
eq((verify(_nr).get(HITTER), verify(_wn).get(HITTER)), (False, False),
   "🔴 a hitter why without its record sentence, or with another number than the row's: FAIL")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 FOOTBALL READS THE SAME LIST, AND ITS OWN WHYS ARE PLAIN UNDER IT")
# ══════════════════════════════════════════════════════════════════════
_FB = os.path.join(ROOT, "test_fb_props_confidence.py")
_fsrc = open(_FB, encoding="utf-8").read()
_lits = {n.value for n in ast.walk(ast.parse(_fsrc)) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
ck("plain_why.found(" in _fsrc and not (_lits & set(plain_why.PHRASES)),
   "🔴 football's caveat check reads plain_why and keeps no copy of a phrase (rule 117)",
   str(sorted(_lits & set(plain_why.PHRASES))))
_DRV = r"""
import json, os, sys
sys.path.insert(0, %r)
import card_fb as CF
CF.CUR_SEASON = 2026
print(json.dumps([CF.build_why("KD", "player_rush_yds", 34.5, "under", 8, 9, 2025, "rush yds"),
                  CF.build_why("KD", "player_rush_yds", 34.5, "over", 2, 3, 2025, "rush yds",
                               {"h26": 1, "n26": 2, "h25": 1, "n25": 1}),
                  CF.build_why("TD Guy", "player_anytime_td", None, "over", 1, 2, 2025, "")]))
""" % ROOT
_fb = {}
for lg in ("nfl", "ncaaf"):
    _p = subprocess.run([sys.executable, "-c", _DRV], cwd=ROOT, capture_output=True, text=True,
                        encoding="utf-8", timeout=300, env=dict(os.environ, LEAGUE=lg, PYTHONUTF8="1"))
    try:
        _fb[lg] = json.loads(_p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        print(shown(_p.stdout[-800:]), shown(_p.stderr[-800:]))
        _fb[lg] = []
ck(all(len(_fb.get(lg) or []) == 3 and all(len(w) == 1 for w in _fb[lg]) for lg in ("nfl", "ncaaf")),
   "⚠️ football's one-sentence whys were built, both leagues, small samples included", str(_fb)[:300])
eq([s for lg in _fb for w in _fb[lg] for s in w if plain_why.found(s)], [],
   "✅ ...and the list never fires on them (a guard that fires on correct code is the other failure)")
