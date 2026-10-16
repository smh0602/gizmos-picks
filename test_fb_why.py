#!/usr/bin/env python3
"""test_fb_why.py — the "why" under each football Gizmo's Picks pick (fb_why.py).

`[Sam, 2026-10-15]` "i also want a "why" behind the picks underneath each gizmo
picks pick". Planted logs, opponent tables, injury reports, schedule and model
file. ⛔ Reads no live data.

# @vacuity 🔴 a rank past the middle reads as "fewest", never "27th most"
#   file: fb_why.py
#   find:                 "%s most of %d" % (ordinal(k), n) if k <= (n + 1) / 2 else "%s fewest of %d" % (ordinal(n - k + 1), n))
#   with:                 "%s most of %d" % (ordinal(k), n))
#
# @vacuity 🔴 only Out / Doubtful defenders are named
#   file: fb_why.py
#   find: OUT = ("out", "doubtful")
#   with: OUT = ("out", "doubtful", "questionable")
#
# @vacuity 🔴 a receiver's why names the defenders who cover him
#   file: fb_why.py
#   find:     "rec": SECONDARY | {"LB", "ILB", "OLB", "MLB"}, "rec_yds": SECONDARY | {"LB", "ILB", "OLB", "MLB"},
#   with:     "rec": FRONT, "rec_yds": FRONT,
#
# @vacuity 🔴 an ambiguous name gets no log-based sentence
#   file: fb_why.py
#   find:         return self.P[pids[0]] if len(pids) == 1 else None    # ⛔ ambiguous: no sentence, never a guess
#   with:         return self.P[pids[0]] if pids else None    # ⛔ ambiguous: no sentence, never a guess
#
# @vacuity 🔴 the record counts the pick's own side
#   file: fb_why.py
#   find:         hit = sum(1 for v in vals if (v > line if side == "over" else v < line))
#   with:         hit = sum(1 for v in vals if v > line)
#
# @vacuity 🔴 the opponent is the other team in the game
#   file: fb_why.py
#   find:     opp = away if team and team == home else home if team and team == away else None
#   with:     opp = home if team and team == home else away if team and team == away else None
#
# @vacuity 🔴 one row whose why fails does not cost the next row its why
#   file: fb_why.py
#   find:             print("  ⚠️ no why for %s: %s: %s" % (r.get("player"), type(e).__name__, e), flush=True)
#   with:             return rows
#
# @vacuity 🔴 the card writes the why on its liked props
#   file: card_fb.py
#   find:         "liked": fb_why.explain(       # `[Sam, 2026-10-15]` the why under each pick
#   with:         "liked": (lambda rows, *a, **k: rows)(       # `[Sam, 2026-10-15]` the why under each pick
"""
import gzip
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "nfl")
import fb_why as W  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

T = tempfile.mkdtemp(prefix="fbwhy-")
L = os.path.join(T, "data", "nfl", "latest")
os.makedirs(L)


def put(name, doc):
    p = os.path.join(L, name)
    with (gzip.open(p, "wt", encoding="utf-8") if p.endswith(".gz") else open(p, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


def gm(d, team, **k):
    return dict({"d": d, "team": team, "snap_pct": 0.9, "tgt_share": 0.3, "car": 0}, **k)


try:
    put("players-2026.json.gz", {"players": {
        "w1": {"name": "Star Receiver", "pos": "WR", "g": [gm("2026-09-21", "SEA", rec_yds=100), gm("2026-10-04", "SEA", rec_yds=80),
                                                          gm("2026-09-28", "SEA", rec_yds=120)]},
        "a1": {"name": "Same Name", "pos": "WR", "g": [gm("2026-10-04", "SEA", rec_yds=200)]},
        "a2": {"name": "Same Name", "pos": "RB", "g": [gm("2026-10-04", "DEN", rec_yds=1)]},
        "r1": {"name": "Home Back", "pos": "RB", "g": [gm("2026-10-04", "DEN", rush_yds=40), gm("2026-10-11", "DEN", rush_yds=90)]}}})
    teams = {("T%02d" % i): {"WR": {"rec_yds": 150.0 - i, "rec_yds_rank": i + 1}, "RB": {"rush_yds": 130.0 - i, "rush_yds_rank": i + 1}}
             for i in range(30)}
    teams["DEN"] = {"WR": {"rec_yds": 117.8, "rec_yds_rank": 27}, "RB": {"rush_yds": 111.0, "rush_yds_rank": 4}}
    teams["SEA"] = {"RB": {"rush_yds": 77.8, "rush_yds_rank": None}}
    put("allowed-by-position-2026.json.gz", {"defences": teams})
    put("injuries-2026.json.gz", {"teams": {"DEN": {"5": {"players": [{"full_name": "Old Report", "position": "CB", "report_status": "Out"}]},
                                                    "6": {"players": [
        {"full_name": "Pat Surtain II", "position": "CB", "report_status": "Out"},
        {"full_name": "Talanoa Hufanga", "position": "S", "report_status": "Doubtful"},
        {"full_name": "Riley Moss", "position": "CB", "report_status": "Questionable"},
        {"full_name": "Big Tackle", "position": "DT", "report_status": "Out"}]}}}})
    put("schedule-2026.json.gz", {"games": [
        {"home": "DEN", "away": "SEA", "final": True, "home_score": 20, "away_score": 24},
        {"home": "SEA", "away": "T01", "final": True, "home_score": 30, "away_score": 10},
        {"home": "DEN", "away": "T02", "final": False, "home_score": None, "away_score": None}]})
    json.dump({"win_chances": [{"away": "Seattle Seahawks", "home": "Denver Broncos", "score": {"home": 18.7, "away": 20.7}}]},
              open(os.path.join(L, "fb-model.json"), "w", encoding="utf-8"))
    ctx = W.Context("nfl", L)

    # ══════════════════════════════════════════════════════════════════
    section("1. 🔴 A PROP'S WHY: ROLE, FORM AT THE LINE, MATCHUP, INJURIES, MODEL")
    # ══════════════════════════════════════════════════════════════════
    row = {"player": "Star Receiver", "market": "player_reception_yds", "side": "over", "line": 92.5,
           "home": "Denver Broncos", "away": "Seattle Seahawks", "confidence": 56, "break_even": 52.6, "price": -111,
           "role": {"snap": 0.863, "tgt_share": 0.302, "car": 0.3}}
    why = W.prop_why(row, ctx)
    eq(why[0], "Over his last 3 games he has played 86% of the snaps and 30% of the team's targets.",
       "🔴 his role, from the card's own numbers")
    eq(why[1], "This season he has gone over 92.5 in <b>2 of 3</b> games, averaging 100 receiving yards.",
       "🔴 how he has done at THIS line this season")
    eq(why[2], "The Denver Broncos allow 117.8 receiving yards a game to wide receivers (5th fewest of 31).",
       "🔴 what the opponent allows his position, rank read the right way round (27th most of 31 = 5th fewest)")
    eq(why[3], "The Denver Broncos list CB Pat Surtain II (Out), S Talanoa Hufanga (Doubtful).",
       "🔴 the opponent's Out / Doubtful defenders who cover him, from its LATEST report (not Questionable, "
       "not a DT, not last week's)")
    eq(why[4], "The model gives it <b>56%</b>; at -111 it needs 52.6% to pay.", "🔴 the model's chance against the price")
    under = dict(row, side="under", line=110.5)
    ck(W.prop_why(under, ctx)[1].startswith("This season he has gone under 110.5 in <b>2 of 3</b>"),
       "🔴 an under counts the games he went UNDER", W.prop_why(under, ctx)[1])
    back = {"player": "Home Back", "market": "player_rush_yds", "side": "under", "line": 66.5,
            "home": "Denver Broncos", "away": "Seattle Seahawks", "confidence": 54, "break_even": 53.1, "price": -113}
    eq(W.prop_why(back, ctx)[1], "The Seattle Seahawks allow 77.8 rushing yards a game to running backs.",
       "🔴 the opponent is the OTHER team in his game; a defence with no rank still gets its number")
    amb = dict(row, player="Same Name", role=None)
    eq(W.prop_why(amb, ctx), ["The model gives it <b>56%</b>; at -111 it needs 52.6% to pay."],
       "🔴 an ambiguous name gets no sentence from anyone's log (never a guess)")
    eq(W.prop_why(dict(row, home="Nowhere FC", away="Nobody"), ctx)[2:],
       ["The model gives it <b>56%</b>; at -111 it needs 52.6% to pay."],
       "   a game whose teams cannot be resolved gets no matchup or injury sentence")

    # ══════════════════════════════════════════════════════════════════
    section("2. 🔴 A GAME LINE'S WHY: ITS SENTENCE, THE PREDICTED SCORE, POINTS FOR AND AGAINST")
    # ══════════════════════════════════════════════════════════════════
    gl = {"player": "Denver Broncos", "market": "spread", "home": "Denver Broncos", "away": "Seattle Seahawks",
          "why": ["The game model gives Denver Broncos 60% to cover +2.5; the price -105 needs 51.2%."]}
    eq(W.line_why(gl, ctx), [
        "The game model gives Denver Broncos 60% to cover +2.5; the price -105 needs 51.2%.",
        "The model's predicted score: Seattle Seahawks 20.7, Denver Broncos 18.7 (total 39.4).",
        "The Seattle Seahawks score 27 and allow 15 points a game this season (2 games).",
        "The Denver Broncos score 20 and allow 24 points a game this season (1 game)."],
       "🔴 the pick's own sentence, then the model's predicted score (away first, as the row reads), then "
       "each team's FINAL games only")

    # ══════════════════════════════════════════════════════════════════
    section("3. 🔴 IT EXPLAINS AND NEVER BREAKS THE CARD")
    # ══════════════════════════════════════════════════════════════════
    bare = W.explain([dict(row, role=None)], "nfl", os.path.join(T, "missing"))
    eq(bare[0]["why"], ["The model gives it <b>56%</b>; at -111 it needs 52.6% to pay."],
       "   a card whose data files are missing still builds, with only the facts it has")
    two = W.explain([dict(row, role={"snap": None}, why=["old"]), dict(back)], "nfl", L, ctx=ctx)
    ck(two[0]["why"] == ["old"] and len(two[1].get("why") or []) >= 2,
       "🔴 a row whose why fails keeps its old one, and the NEXT row still gets its why", two)
    ctx.lg = "ncaaf"
    eq(W.prop_why(row, ctx)[0], "This season he has gone over 92.5 in <b>2 of 3</b> games, averaging 100 receiving yards.",
       "   college: no role sentence (its logs carry no snaps or targets)")
    ck(not any(s.startswith("The Denver Broncos list") for s in W.prop_why(row, ctx)),
       "   college: no injury sentence (no injury reports)")
    ctx.lg = "nfl"
    rows = W.explain([dict(row)], "nfl", L, ctx=ctx)
    ck(rows[0]["why"] == why and rows[0]["confidence"] == 56 and rows[0]["price"] == -111,
       "🔴 explain writes the why and changes no pick, chance or price")
    src = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
    ck('"liked": fb_why.explain(' in src and '"game_lines_liked": fb_why.explain(' in src,
       "🔴 the card writes the why on its liked props and liked game lines (the lists Gizmo's Picks shows)")
finally:
    shutil.rmtree(T, ignore_errors=True)
