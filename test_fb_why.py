#!/usr/bin/env python3
r"""test_fb_why.py — the "why" under each football Gizmo's Picks pick (fb_why.py).

`[Sam, 2026-10-15]` "i also want a "why" behind the picks underneath each gizmo
picks pick". `[2026-10-16]` Every sentence was then recomputed from the raw files
by independent checkers (225 sentences); each defect they confirmed is planted
below as a case. Planted logs, opponent tables, injury reports, schedule and model
file. ⛔ Reads no live data.

# @vacuity 🔴 a tied rank reads from the right end ("1st fewest", not "2nd")
#   file: fb_why.py
#   find:         few = 1 + sum(1 for x in vals if x < v)
#   with:         few = len(vals) - rk + 1
#
# @vacuity 🔴 a rank past the middle reads as "fewest", never "31st most"
#   file: fb_why.py
#   find:                 "%s most of %d" % (ordinal(k), n) if k <= few else "%s fewest of %d" % (ordinal(few), n))
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
# @vacuity 🔴 the injury report is THIS game's week, never the newest one stored
#   file: fb_why.py
#   find:         rep = (self.injuries.get(team) or {}).get(str(week)) if week is not None else None
#   with:         rep = (self.injuries.get(team) or {}).get(max(self.injuries.get(team) or {"0": 0}, key=int))
#
# @vacuity 🔴 the game's week is the meeting within a day of kickoff, not an earlier one
#   file: fb_why.py
#   find:                     and d is not None and gd is not None and abs((gd - d).days) <= 1):
#   with:                     and d is not None and gd is not None):
#
# @vacuity 🔴 an ambiguous name gets no log-based sentence
#   file: fb_why.py
#   find:         return self.P[pids[0]] if len(pids) == 1 else None    # ⛔ ambiguous: no sentence, never a guess
#   with:         return self.P[pids[0]] if pids else None    # ⛔ ambiguous: no sentence, never a guess
#
# @vacuity 🔴 the record is the card's own, and only when the card shows one
#   file: fb_why.py
#   find:     if r.get("record") is not None:      # ⛔ the card's own record, under the card's own gates
#   with:     if True:      # ⛔ the card's own record, under the card's own gates
#
# @vacuity 🔴 the role says how many games it averaged
#   file: fb_why.py
#   find:                    ("Over his last %d games he has played %s." % (role["n"], " and ".join(bits))))
#   with:                    ("Over his last %d games he has played %s." % (3, " and ".join(bits))))
#
# @vacuity 🔴 a role with no game count gets no sentence (never an assumed 3)
#   file: fb_why.py
#   find:     if role and role.get("n") and ctx.lg == "nfl":
#   with:     if role and ctx.lg == "nfl":
#
# @vacuity 🔴 "the model" only on a MODEL row
#   file: fb_why.py
#   find:         if basis == "MODEL":
#   with:         if True:
#
# @vacuity 🔴 the predicted score is printed only when it lands on the pick's side
#   file: fb_why.py
#   find:     if s and s.get("home") is not None and s.get("away") is not None and score_agrees(r, s):
#   with:     if s and s.get("home") is not None and s.get("away") is not None:
#
# @vacuity 🔴 a spread's score agrees when the margin beats ITS line
#   file: fb_why.py
#   find:         return r.get("line") is not None and round(m + float(r["line"]), 6) > 0
#   with:         return m > 0
#
# @vacuity 🔴 an under agrees when the total is BELOW the line
#   file: fb_why.py
#   find:         return d > 0 if side == "over" else d < 0
#   with:         return d > 0
#
# @vacuity 🔴 a January game belongs to the season before
#   file: fb_why.py
#   find:     return d.year if d.month >= 3 else d.year - 1
#   with:     return d.year
#
# @vacuity 🔴 a second pass rebuilds the same why (the card's own sentence is kept)
#   file: fb_why.py
#   find:     return list(r["why_card"] if "why_card" in r else (r.get("why") or []))
#   with:     return list(r.get("why") or [])
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
# @vacuity 🔴 the card's role carries how many games it averaged
#   file: card_fb.py
#   find:             "n": len(g)}
#   with:             "n": 3}
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
import card_fb as CF  # noqa: E402
import fb_why as W  # noqa: E402
import ranking  # noqa: E402
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


MODEL = "The model gives it <b>56%</b>; at -111 it needs 52.6% to pay."
CARD = "<b>Star Receiver</b> went over 92.5 rec yds in <b>2 of 3 games</b> in 2026, when he played at least half the snaps."
try:
    put("players-2026.json.gz", {"players": {
        "w1": {"name": "Star Receiver", "pos": "WR", "g": [gm("2026-09-21", "SEA", rec_yds=100), gm("2026-10-04", "SEA", rec_yds=80),
                                                          gm("2026-09-28", "SEA", rec_yds=120)]},
        "a1": {"name": "Same Name", "pos": "WR", "g": [gm("2026-10-04", "SEA", rec_yds=200)]},
        "a2": {"name": "Same Name", "pos": "RB", "g": [gm("2026-10-04", "DEN", rec_yds=1)]},
        "r1": {"name": "Home Back", "pos": "RB", "g": [gm("2026-10-04", "DEN", rush_yds=40), gm("2026-10-11", "DEN", rush_yds=90)]}}})
    # the real ranker, so ties are shared exactly as the stored table shares them
    wr = [("T%02d" % i, 150.0 - i) for i in range(30)] + [("DEN", 100.0), ("KC", 100.0)]
    rk = ranking.competition_ranks(wr)
    teams = {t: {"WR": {"rec_yds": v, "rec_yds_rank": rk[t][0]}} for t, v in wr}
    teams["SEA"] = {"RB": {"rush_yds": 77.8, "rush_yds_rank": None}}
    put("allowed-by-position-2026.json.gz", {"defences": teams})
    put("injuries-2026.json.gz", {"teams": {
        "DEN": {"5": {"players": [{"full_name": "Old Report", "position": "CB", "report_status": "Out"}]},
                "6": {"players": [
                    {"full_name": "Pat Surtain II", "position": "CB", "report_status": "Out"},
                    {"full_name": "Talanoa Hufanga", "position": "S", "report_status": "Doubtful"},
                    {"full_name": "Riley Moss", "position": "CB", "report_status": "Questionable"},
                    {"full_name": "Big Tackle", "position": "DT", "report_status": "Out"}]},
                "7": {"players": [{"full_name": "Next Week", "position": "CB", "report_status": "Out"}]}},
        "SEA": {"4": {"players": [{"full_name": "Old Seahawk", "position": "LB", "report_status": "Out"}]}}}})
    put("schedule-2026.json.gz", {"games": [
        {"week": 2, "start": "2026-09-20T16:05", "home": "DEN", "away": "SEA", "final": True, "home_score": 20, "away_score": 24},
        {"week": 3, "start": "2026-09-27T13:00", "home": "SEA", "away": "T01", "final": True, "home_score": 30, "away_score": 10},
        {"week": 6, "start": "2026-10-15T20:15", "home": "DEN", "away": "SEA", "final": False, "home_score": None, "away_score": None}]})
    json.dump({"win_chances": [{"away": "Seattle Seahawks", "home": "Denver Broncos", "score": {"home": 18.7, "away": 20.7}}]},
              open(os.path.join(L, "fb-model.json"), "w", encoding="utf-8"))
    ctx = W.Context("nfl", L, 2026)

    # ══════════════════════════════════════════════════════════════════
    section("1. 🔴 A PROP'S WHY: ROLE, THE CARD'S RECORD, MATCHUP, INJURIES, CHANCE")
    # ══════════════════════════════════════════════════════════════════
    row = {"player": "Star Receiver", "market": "player_reception_yds", "side": "over", "line": 92.5,
           "home": "Denver Broncos", "away": "Seattle Seahawks", "commence": "2026-10-16T00:15:00Z",
           "confidence": 56, "confidence_basis": "MODEL", "break_even": 52.6, "price": -111,
           "record": "2 of 3", "why": [CARD], "role": {"snap": 0.863, "tgt_share": 0.302, "car": 0.3, "n": 3}}
    why = W.prop_why(row, ctx)
    eq(why, ["Over his last 3 games he has played 86% of the snaps and 30% of the team's targets.",
             CARD,
             "The Denver Broncos allow 100 receiving yards a game to wide receivers (1st fewest of 32).",
             "The Denver Broncos list CB Pat Surtain II (Out), S Talanoa Hufanga (Doubtful).",
             MODEL],
       "🔴 role, the CARD'S own record sentence, the opponent vs his position (tied for the fewest reads "
       "1st, not 2nd), the opponent's Out/Doubtful defenders who cover him from THIS game's week (not "
       "Questionable, not a DT, not week 5's or week 7's report), the model's chance against the price")
    eq(W.prop_why(dict(row, role=dict(row["role"], n=2)), ctx)[0],
       "Over his last 2 games he has played 86% of the snaps and 30% of the team's targets.",
       "🔴 a player with 2 games this season: the role says 2 (Horton, 10-15)")
    eq(W.prop_why(dict(row, role=dict(row["role"], n=1)), ctx)[0],
       "In his last game he played 86% of the snaps and 30% of the team's targets.", "   ...and 1 game reads as one")
    eq(W.prop_why(dict(row, role={"snap": 0.86, "tgt_share": 0.3, "car": 0.3}), ctx)[0], CARD,
       "🔴 a role with no game count (a card from before 10-16) gets no role sentence, never an assumed 3")
    eq(CF.role_of({"g": [gm("2026-10-0%d" % i, "SEA") for i in (1, 2)]})["n"], 2,
       "🔴 the card's role carries how many games it averaged")
    gated = dict(row, record=None, why=["The player name join did not clear its gate on this slate, so no record "
                                        "is shown rather than a record that might belong to someone else."])
    ck(not any("join" in s or "went over" in s or "2 of 3" in s for s in W.prop_why(gated, ctx)),
       "🔴 a row the card shows no record for gets none from the why (no second count over cameo games)",
       W.prop_why(gated, ctx))
    eq(W.prop_why(dict(row, confidence_basis="RECORD"), ctx)[-1],
       "His record at this line makes it <b>56%</b>; at -111 it needs 52.6% to pay.",
       "🔴 a RECORD row's chance is his record's, never \"the model's\"")
    ck(not any("<b>56%</b>" in s for s in W.prop_why(dict(row, confidence_basis=None), ctx)),
       "   ...and a row with no basis gets no chance sentence")
    back = {"player": "Home Back", "market": "player_rush_yds", "side": "under", "line": 66.5,
            "home": "Denver Broncos", "away": "Seattle Seahawks", "commence": "2026-10-16T00:15:00Z",
            "confidence": 54, "confidence_basis": "MODEL", "break_even": 53.1, "price": -113, "record": None, "why": []}
    eq(W.prop_why(back, ctx), ["The Seattle Seahawks allow 77.8 rushing yards a game to running backs.",
                               "The model gives it <b>54%</b>; at -113 it needs 53.1% to pay."],
       "🔴 the opponent is the OTHER team in his game; a defence with no rank still gets its number; the "
       "opponent's only stored report is week 4, so no injury sentence")
    amb = dict(row, player="Same Name", role=None, record=None, why=[])
    eq(W.prop_why(amb, ctx), [MODEL], "🔴 an ambiguous name gets no sentence from anyone's log (never a guess)")
    eq(W.prop_why(dict(row, home="Nowhere FC", away="Nobody", role=None), ctx), [CARD, MODEL],
       "   a game whose teams cannot be resolved gets no matchup or injury sentence")

    # ══════════════════════════════════════════════════════════════════
    section("2. 🔴 A GAME LINE'S WHY: THE PREDICTED SCORE ONLY WHERE IT AGREES WITH THE PICK")
    # ══════════════════════════════════════════════════════════════════
    SCORE = "The model's predicted score: Seattle Seahawks 20.7, Denver Broncos 18.7 (total 39.4)."
    PFPA = ["The Seattle Seahawks score 27 and allow 15 points a game this season (2 games).",
            "The Denver Broncos score 20 and allow 24 points a game this season (1 game)."]

    def gl(**k):
        return dict({"player": "Denver Broncos", "home": "Denver Broncos", "away": "Seattle Seahawks",
                     "why": ["own sentence"]}, **k)

    eq(W.line_why(gl(market="spread", side="home", line=2.5), ctx), ["own sentence", SCORE] + PFPA,
       "🔴 Denver +2.5 beside Denver losing by 2: the score agrees, so it is shown; then each team's FINAL "
       "games only")
    eq(W.line_why(gl(market="spread", side="home", line=1.5), ctx), ["own sentence"] + PFPA,
       "🔴 Denver +1.5 beside Denver losing by 2 loses the pick: no score (Jets +7 beside 16.1-27.7, 10-16)")
    eq(W.line_why(gl(market="alternate_spread", side="away", line=-3.5), ctx), ["own sentence"] + PFPA,
       "   an alternate spread the same way (Seattle -3.5 beside a 2-point win)")
    eq([SCORE in W.line_why(gl(market="moneyline", side=s, line=None), ctx) for s in ("home", "away")], [False, True],
       "🔴 a moneyline: only the side the score has winning")
    eq([SCORE in W.line_why(gl(market="total", side=sd, line=ln), ctx)
        for sd, ln in (("under", 40.5), ("under", 38.5), ("over", 38.5), ("over", 40.5))], [True, False, True, False],
       "🔴 a total: under 40.5 and over 38.5 agree with 39.4; under 38.5 and over 40.5 do not")

    # ══════════════════════════════════════════════════════════════════
    section("3. 🔴 THE SEASON IS THE KICKOFF'S, AND IT NEVER BREAKS THE CARD")
    # ══════════════════════════════════════════════════════════════════
    eq([W.season_of(x) for x in ("2026-09-10T00:20:00Z", "2027-01-10T18:00:00Z", "2027-02-14T23:30:00Z", None)],
       [2026, 2026, 2026, None], "🔴 a January or February game belongs to the season before")
    jan = W.explain([dict(row, commence="2027-01-10T18:00:00Z", role=None)], "nfl", L)
    ck(any("allow 100 receiving yards" in s for s in jan[0]["why"]),
       "🔴 explain reads the kickoff's season (a January game reads 2026's files)", jan[0]["why"])
    nxt = W.explain([dict(row, commence="2027-09-12T17:00:00Z", role=None)], "nfl", L)
    eq(nxt[0]["why"], [CARD, MODEL],
       "🔴 a season with no stored files gets no log, matchup or injury sentence (never last season's)")
    bare = W.explain([dict(row, role=None)], "nfl", os.path.join(T, "missing"))
    eq(bare[0]["why"], [CARD, MODEL], "   a card whose data files are missing still builds, with only the facts it has")
    two = W.explain([dict(row, role={"snap": None, "n": 3}, why=["old"]), dict(back)], "nfl", L, ctx=ctx)
    ck(two[0]["why"] == ["old"] and len(two[1].get("why") or []) == 2,
       "🔴 a row whose why fails keeps its old one, and the NEXT row still gets its why", two)
    once = W.explain([dict(row)], "nfl", L, ctx=ctx)
    twice = W.explain(once, "nfl", L, ctx=ctx)
    ck(twice[0]["why"] == why and twice[0]["why_card"] == [CARD],
       "🔴 a second pass rebuilds the same why from the card's own sentence (kept in why_card)", twice[0]["why"])
    ck(once[0]["confidence"] == 56 and once[0]["price"] == -111 and once[0]["record"] == "2 of 3",
       "🔴 explain changes no pick, chance or price")
    ctx.lg = "ncaaf"
    eq(W.prop_why(row, ctx), [CARD, "The Denver Broncos allow 100 receiving yards a game to wide receivers (1st fewest of 32).",
                              MODEL], "   college: no role and no injury sentence (no snaps, targets or reports)")
    ctx.lg = "nfl"
    src = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
    ck('"liked": fb_why.explain(' in src and '"game_lines_liked": fb_why.explain(' in src,
       "🔴 the card writes the why on its liked props and liked game lines (the lists Gizmo's Picks shows)")
finally:
    shutil.rmtree(T, ignore_errors=True)
