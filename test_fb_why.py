#!/usr/bin/env python3
r"""test_fb_why.py — the "why" under each football Gizmo's Picks pick (fb_why.py).

`[Sam, 2026-10-15]` "i also want a "why" behind the picks underneath each gizmo
picks pick". `[2026-10-16]` Every sentence was then recomputed from the raw files
by independent checkers (225 sentences); each defect they confirmed is planted
below as a case. Planted logs, opponent tables, injury reports, schedule and model
file. ⛔ Reads no live data.

`[Sam, 2026-10-17]` *"use the college injury source as long as it's accurate and
up to date, we wouldn't want misinformation ruining our bets."* Section 4: a
college prop's why names the opponent's Out / Doubtful defenders only from a
CURRENT report of THIS game, read through cfb_injuries from reports its own
run() stored in a planted root from planted feed payloads (no network: urlopen
is a tripwire; the repo's teams.json is never read).

`[Sam, 2026-10-26]` *"let's do all of this"*, approving the proposal "add one plain line
to each game pick's why, like 'Washington is 2–3 against teams rated above average'.
That's information only and moves no %."
Section 5: a game line's why gives each team's record this season against the teams
the model rates above average at THIS game's Monday. Section 6: fb-model.json's
`above_average`, from the solve the rows already read, built on a synthetic league
with and without it: every other field byte for byte the same.

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
#
# @vacuity 🔴 a college prop's why names the opponent's defenders from a CURRENT report of THIS game
#   file: fb_why.py
#   find: elif ctx.lg == "ncaaf":     # `[Sam, 2026-10-17]` only a CURRENT report of THIS game
#   with: elif False:     # `[Sam, 2026-10-17]` only a CURRENT report of THIS game
#
# @vacuity 🔴 college never reads the NFL's per-week report store
#   file: fb_why.py
#   find: if ctx.lg == "nfl":         # THIS game's week's report
#   with: if True:         # THIS game's week's report
#
# @vacuity 🔴 college position codes reach GUARDS through POSITION_MAP (EDG, JCK -> EDGE; STR, N/S -> DB)
#   file: fb_why.py
#   find: pos = CI.POSITION_MAP.get(raw, raw)
#   with: pos = raw
#
# @vacuity 🔴 a college why names only the defenders who guard him
#   file: fb_why.py
#   find: if pos in guards:
#   with: if True:
#
# @vacuity 🔴 a college report cfb_injuries does not judge current is never shown
#   file: fb_why.py
#   find: for p in CI.out_players(self.cfb[gid], team) or []:     # ⛔ None unless the report is CURRENT
#   with: for p in CI.out_players(dict(self.cfb[gid] or {}, current=True), team) or []:     # ⛔ None unless the report is CURRENT
#
# @vacuity 🔴 the card's read is live: our newest reading of the source must be at most 6 hours old
#   file: fb_why.py
#   find: self.cfb[gid] = CI.report_for(gid, at=self.now, root=root, live=True)
#   with: self.cfb[gid] = CI.report_for(gid, at=self.now, root=root, live=False)
#
# @vacuity 🔴 two stored games that could be THIS one give no sentence, never a guess
#   file: fb_why.py
#   find: if len(hits) != 1:              # ⛔ two stored games could be this one: never a guess
#   with: if not hits:              # ⛔ two stored games could be this one: never a guess
#
# @vacuity 🔴 at most 4 defenders are named
#   file: fb_why.py
#   find: ", ".join(outs[:4])
#   with: ", ".join(outs)
#
# @vacuity 🔴 a college report published over 36 hours before kickoff is not shown
#   file: cfb_injuries.py
#   find: MAX_AGE_H = 36
#   with: MAX_AGE_H = 48
#
# @vacuity 🔴 a Questionable college defender is never listed
#   file: cfb_injuries.py
#   find: OUT_STATUSES = ("out", "out for season", "doubtful")
#   with: OUT_STATUSES = ("out", "out for season", "doubtful", "questionable")
#
# @vacuity 🔴 a Probable college defender is never listed
#   file: cfb_injuries.py
#   find: OUT_STATUSES = ("out", "out for season", "doubtful")
#   with: OUT_STATUSES = ("out", "out for season", "doubtful", "probable")
#
# @vacuity 🔴 an Exempt college defender (stored as unknown) is never listed
#   file: cfb_injuries.py
#   find: OUT_STATUSES = ("out", "out for season", "doubtful")
#   with: OUT_STATUSES = ("out", "out for season", "doubtful", "unknown")
#
# @vacuity 🔴 the card's own call (a RELATIVE data/ncaaf/latest) still finds THIS game's current report
#   file: fb_why.py
#   find: if os.path.normcase(os.path.abspath(CI.latest(root))) != os.path.normcase(os.path.abspath(self.latest)):
#   with: if CI.latest(root) != self.latest:
#
# @vacuity 🔴 explain reads the reports at the build time it is given, never the real clock
#   file: fb_why.py
#   find: ctx = Context(lg, latest, season, now=now)
#   with: ctx = Context(lg, latest, season)
#
# @vacuity 🔴 the record's list is THIS game's Monday's, found by its schedule day (never the odds' UTC kickoff)
#   file: fb_why.py
#   find: wk = (ctx.above.get("monday") or {}).get(kick[:10])
#   with: wk = (ctx.above.get("monday") or {}).get((r.get("commence") or "")[:10])
#
# @vacuity 🔴 a tie is a tie (W-L-T), never a loss
#   file: fb_why.py
#   find: w, lo, ti = w + (us > them), lo + (us < them), ti + (us == them)
#   with: w, lo, ti = w + (us > them), lo + (us <= them), ti
#
# @vacuity 🔴 only games before THIS game's kickoff count
#   file: fb_why.py
#   find: if team not in (g["home"], g["away"]) or not (g.get("start") or "")[:16] < kick[:16]:
#   with: if team not in (g["home"], g["away"]):
#
# @vacuity 🔴 only games against a team on THIS Monday's above-average list count
#   file: fb_why.py
#   find: if (g["away"] if home else g["home"]) not in good:
#   with: if False:
#
# @vacuity 🔴 a result is the team's own score against its opponent's
#   file: fb_why.py
#   find: us, them = (g["home_score"], g["away_score"]) if home else (g["away_score"], g["home_score"])
#   with: us, them = (g["home_score"], g["away_score"])
#
# @vacuity 🔴 away first, then home, as the points sentences
#   file: fb_why.py
#   find: for name, team in ((r.get("away"), away), (r.get("home"), home)):
#   with: for name, team in ((r.get("home"), home), (r.get("away"), away)):
#
# @vacuity 🔴 no list for the game's Monday, no sentence (never 0-0 for everyone)
#   file: fb_why.py
#   find: good = set((ctx.above.get("teams") or {}).get(wk) or ())
#   with: good = set((ctx.above.get("teams") or {}).get(wk) or ()) or {"?"}
#
# @vacuity 🔴 two stored games that could be THIS one: no record sentence, never a guess
#   file: fb_why.py
#   find: if len(hits) != 1:              # ⛔ none, or two stored games that could be this one
#   with: if not hits:              # ⛔ none, or two stored games that could be this one
#
# @vacuity 🔴 the stored list is the MARGIN rating's (R), never the offence's
#   file: fb_model.py
#   find: out["teams"][wk] = sorted(above_average(own[wk], lg, fbs)["R"])
#   with: out["teams"][wk] = sorted(above_average(own[wk], lg, fbs)["O"])
#
# @vacuity 🔴 a game's day maps to the Monday its ratings are read at
#   file: fb_model.py
#   find: wk = monday(d) if d else None
#   with: wk = d
#
# @vacuity 🔴 only the Game Lines tab's games add a Monday
#   file: fb_model.py
#   find: for w in wins or []:
#   with: for w in [{"game_id": i} for i in day]:
#
# @vacuity 🔴 college compares against the FBS teams' mean
#   file: fb_model.py
#   find: fbs = fbs_teams(root) if lg == "ncaaf" and wins else None
#   with: fbs = None
#
# @vacuity 🔴 build_rows hands over the solve its rows read
#   file: fb_model.py
#   find: ratings.update(own)              #    "above average" list (no second solve)
#   with: pass
#
# @vacuity 🔴 build writes the list from that handed-over solve
#   file: fb_model.py
#   find: rows = build_rows(lg, root, extra_top, extra_players, ratings=own, inj_now=now)
#   with: rows = build_rows(lg, root, extra_top, extra_players, inj_now=now)
#
# @vacuity 🔴 the list changes no other field of fb-model.json
#   file: fb_model.py
#   find: out["monday"][d] = wk
#   with: out["monday"][d] = w.setdefault("monday", wk)
#
# @vacuity 🔴 ...nor one it changes before it reads any solve (the baseline build runs no list code at all)
#   file: fb_model.py
#   find: for w in wins or []:
#   with: for w in [x.update(p_home=0.0) or x for x in wins or []]:
#
# @vacuity 🔴 a model file with no above_average block: no sentence, never a list made up in its place
#   file: fb_why.py
#   find: good = set((ctx.above.get("teams") or {}).get(wk) or ())
#   with: good = set((ctx.above.get("teams") or {}).get(wk) or ()) or (set() if ctx.above else {t for g in ctx.finals for t in (g["home"], g["away"])})
#
# @vacuity 🔴 ...nor a default block read in its place
#   file: fb_why.py
#   find: self.above = fm.get("above_average") or {}
#   with: self.above = fm.get("above_average") or {"monday": {"2026-10-25": "x"}, "teams": {"x": ["?"]}}
"""
import datetime
import gzip
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "nfl")
import card_fb as CF  # noqa: E402
import dossier_fb as D  # noqa: E402
import fb_why as W  # noqa: E402
import ranking  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

UTC = datetime.timezone.utc


def _tripwire(*a, **k):
    raise AssertionError("test_fb_why reached the network")


urllib.request.urlopen = _tripwire     # ⛔ section 4 runs cfb_injuries' own fetch pass, on planted feeds only
T = tempfile.mkdtemp(prefix="fbwhy-")
L = os.path.join(T, "data", "nfl", "latest")
os.makedirs(L)


def put(name, doc, at=None):
    p = os.path.join(at or L, name)
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
                              MODEL],
       "🔴 college: no role sentence (no snaps or targets stored); ~~no injury sentence (no reports)~~ `[Sam, "
       "2026-10-17]` \"as long as it's accurate and up to date\": an injury sentence only from a CURRENT college "
       "report of THIS game (section 4). This tree holds none, and the NFL's per-week report store (Pat Surtain "
       "II, Out, week 6) is never read for college")
    ctx.lg = "nfl"
    src = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
    ck('"liked": fb_why.explain(' in src and '"game_lines_liked": fb_why.explain(' in src,
       "🔴 the card writes the why on its liked props and liked game lines (the lists Gizmo's Picks shows)")

    # ══════════════════════════════════════════════════════════════════
    section("4. 🔴 COLLEGE: THE OPPONENT'S OUT / DOUBTFUL DEFENDERS, ONLY FROM A CURRENT REPORT OF THIS GAME")
    # ══════════════════════════════════════════════════════════════════
    # `[Sam, 2026-10-17]` "use the college injury source as long as it's accurate and up to date, we
    # wouldn't want misinformation ruining our bets." A planted repo root whose reports are written by
    # cfb_injuries' OWN run() from planted HDI payloads (the feed's shape): no network, no repo data.
    import cfb_injuries as CI  # noqa: E402
    CR = os.path.join(T, "college")
    CL = os.path.join(CR, "data", "ncaaf", "latest")
    os.makedirs(CL)

    def sg(gid, start, home, away, week=8):
        return {"id": gid, "start": start, "home": home, "away": away, "week": week, "season_type": "regular",
                "neutral": False, "final": False, "home_score": None, "away_score": None}

    put("schedule-2026.json.gz", {"season": 2026, "games": [
        sg("g0", "2026-10-10T19:30:00.000Z", "Michigan", "Washington", 7),   # Michigan's game the week before
        sg("g1", "2026-10-17T16:00:00.000Z", "Indiana", "Ohio State"),
        sg("g2", "2026-10-17T19:30:00.000Z", "Illinois", "Purdue"),
        sg("g3", "2026-10-17T16:00:00.000Z", "Northwestern", "Michigan"),    # no report of THIS game
        sg("g5a", "2026-10-17T16:00:00.000Z", "Maryland", "Rutgers"),        # two stored games, a day apart
        sg("g5b", "2026-10-18T16:00:00.000Z", "Maryland", "Rutgers")]}, CL)

    def pl(name, pos, team):
        return {"name": name, "pos": pos, "g": [{"d": "2026-10-10", "team": team, "rec_yds": 50, "rush_yds": 50}]}

    put("players-2026.json.gz", {"players": {
        "c1": pl("Hoosier Wideout", "WR", "Indiana"), "c2": pl("Hoosier Back", "RB", "Indiana"),
        "c3": pl("Buckeye Wideout", "WR", "Ohio State"), "c4": pl("Illini Wideout", "WR", "Illinois"),
        "c5": pl("Wildcat Wideout", "WR", "Northwestern"), "c6": pl("Terp Wideout", "WR", "Maryland")}}, CL)

    def side(name, rows):
        return {"teamName": name, "teamDisplayName": name, "rows": [
            {"name": n, "status": s, "exemptStatus": "Exempt" if s == "Exempt" else "NonExempt"} for n, s in rows]}

    def hdi(kdate, ktime, pdate, ptime, away, home):
        return {"ReportType": "Update 2", "conferenceTimeZone": "CT", "publishDate": pdate, "postedTime": ptime,
                "footer": {"date": kdate, "time": ktime, "location": "Somewhere, ST"}, "games": [away, home]}

    # the never-listed first, so any of them leaking shows inside the four a sentence names
    OSU = [("CB #4 Corner Maybe", "Questionable"), ("LB #44 Backer Probable", "Probable"),
           ("LB #45 Exempt Guy", "Exempt"), ("WR #0 Wideout Gone", "Out"), ("EDG #9 Edge Rusher", "Out"),
           ("DT #95 Tackle Gone", "Out"), ("ATH #8 Ath Utility", "Out"), ("S #1 Safety Gone", "Out"),
           ("STR #3 Star Gone", "Doubtful"), ("N/S #6 Nickel Back", "Out"), ("JCK #7 Jack Rusher", "Out"),
           ("CB #21 Corner Season", "Out for Season"), ("DS #2 Dime Back", "Out"), ("DB #10 Healthy Back", "Available")]
    FEED = {}

    def post(url, body):
        if url.endswith("/get-publish-public"):
            return json.loads(json.dumps(FEED.get(body.get("conference"), {})))
        raise urllib.error.URLError("no archive planted")

    def get(url):
        return {"games": []}

    QUIET = []
    FEED["B10"] = {"100": hdi("2026-10-10", "14:30:00", "2026-10-09", "19:00:00", side("Washington", [
        ("QB #1 Husky Passer", "Out")]), side("Michigan", [("S #2 Wolverine Safety", "Out"), ("CB #3 Wolverine Corner", "Doubtful")]))}
    r1 = CI.run(root=CR, now=datetime.datetime(2026, 10, 10, 7, 0, tzinfo=UTC), post=post, get=get, log=QUIET.append)
    FEED["B10"] = {
        "101": hdi("2026-10-17", "11:00:00", "2026-10-16", "19:00:00", side("Ohio St.", OSU),
                   side("Indiana", [("CB #5 Hoosier Corner", "Out"), ("WR #11 Hoosier Receiver", "Out")])),
        "102": hdi("2026-10-17", "14:30:00", "2026-10-15", "19:00:00", side("Purdue", [("S #9 Boiler Safety", "Out")]),
                   side("Illinois", [("CB #8 Illini Corner", "Out")])),       # posted 43.5 hours before kickoff
        "105": hdi("2026-10-17", "11:00:00", "2026-10-16", "19:00:00", side("Rutgers", [("CB #1 Knight Corner", "Out")]),
                   side("Maryland", [("S #2 Terp Safety", "Out")]))}
    r2 = CI.run(root=CR, now=datetime.datetime(2026, 10, 17, 7, 15, tzinfo=UTC), post=post, get=get, log=QUIET.append)
    AT = datetime.datetime(2026, 10, 17, 9, 0, tzinfo=UTC)        # the card's build time: 1h45 after the reading
    LATE = datetime.datetime(2026, 10, 17, 13, 30, tzinfo=UTC)    # 6h15 after it
    rep = {g: CI.report_for(g, at=AT, root=CR) for g in ("g1", "g2", "g3", "g5a")}
    old = CI.report_for("g0", at=datetime.datetime(2026, 10, 10, 9, 0, tzinfo=UTC), root=CR)
    ck(bool(r1.get("wrote") and r2.get("wrote") and rep["g1"] and rep["g1"]["current"] and rep["g5a"]
            and rep["g5a"]["current"] and rep["g2"] and not rep["g2"]["current"] and "more than 36" in rep["g2"]["why"]
            and rep["g3"] is None and old and old["current"]
            and (CI.report_for("g1", at=LATE, root=CR) or {}).get("current") is False),
       "the planted tree is what the cases below read: cfb_injuries' own run() stored both passes; at 09:00Z "
       "g1 and g5a are current, g2 is not (published 43.5 h before kickoff), g3 has none, and Michigan's g0 "
       "report WAS current for its own game; at 13:30Z g1 is not (its reading is 6.25 h old)",
       (r1, r2, rep, old))

    NAMES = {"Indiana Hoosiers": "Indiana", "Ohio State Buckeyes": "Ohio State", "Illinois Fighting Illini": "Illinois",
             "Purdue Boilermakers": "Purdue", "Northwestern Wildcats": "Northwestern",
             "Michigan Wolverines": "Michigan", "Maryland Terrapins": "Maryland", "Rutgers Scarlet Knights": "Rutgers"}
    real_codes, real_report_for = D.team_codes, CI.report_for
    D.team_codes = lambda lg=None: NAMES.get          # ⛔ never the repo's own teams.json
    try:
        cx = W.Context("ncaaf", CL, 2026, now=AT)

        def crow(player, market, home, away, commence="2026-10-17T16:00:00Z", **k):
            return dict({"player": player, "market": market, "side": "over", "line": 55.5, "home": home,
                         "away": away, "commence": commence, "confidence": 55, "confidence_basis": "MODEL",
                         "break_even": 52.4, "price": -110, "record": None, "why": []}, **k)

        CM = "The model gives it <b>55%</b>; at -110 it needs 52.4% to pay."
        REC = crow("Hoosier Wideout", "player_reception_yds", "Indiana Hoosiers", "Ohio State Buckeyes")
        LIST_REC = ("The Ohio State Buckeyes list S Safety Gone (Out), DB Star Gone (Doubtful), DB Nickel Back (Out), "
                    "CB Corner Season (Out for Season).")
        eq(W.prop_why(REC, cx), [LIST_REC, CM],
           "🔴 a CURRENT report of THIS game: the opponent's Out / Out for Season / Doubtful defenders who cover a "
           "receiver, college codes mapped (STR, N/S -> DB), at most 4 (DS Dime Back is the fifth); never "
           "Questionable, Probable or Exempt, never a WR, an EDGE, a DT or an ATH on a receiving prop")
        eq(W.prop_why(crow("Hoosier Back", "player_rush_yds", "Indiana Hoosiers", "Ohio State Buckeyes"), cx),
           ["The Ohio State Buckeyes list EDGE Edge Rusher (Out), DT Tackle Gone (Out), EDGE Jack Rusher (Out).", CM],
           "🔴 a rushing prop: the front (EDG and JCK reach EDGE through POSITION_MAP); no defensive back")
        eq(W.prop_why(crow("Buckeye Wideout", "player_reception_yds", "Indiana Hoosiers", "Ohio State Buckeyes"), cx),
           ["The Indiana Hoosiers list CB Hoosier Corner (Out).", CM],
           "🔴 the OTHER team's list: an Ohio State receiver reads Indiana's defenders, never his own team's")
        eq(W.prop_why(REC, W.Context("ncaaf", CL, 2026, now=LATE)), [CM],
           "🔴 not current: at 13:30Z our newest reading of the Big Ten is 6.25 hours old (more than 6), so no "
           "sentence")
        eq(W.prop_why(crow("Illini Wideout", "player_reception_yds", "Illinois Fighting Illini", "Purdue Boilermakers",
                           "2026-10-17T19:30:00Z"), cx), [CM],
           "🔴 not current: Purdue's report was published 43.5 hours before kickoff (more than 36), so no sentence")
        eq(W.prop_why(crow("Wildcat Wideout", "player_reception_yds", "Northwestern Wildcats", "Michigan Wolverines"),
                      cx), [CM],
           "🔴 a different game's report: Michigan's list is stored only for its game the week before (and other "
           "games' reports are current today), none for THIS game, so no sentence")
        eq(W.prop_why(crow("Terp Wideout", "player_reception_yds", "Maryland Terrapins", "Rutgers Scarlet Knights"),
                      cx), [CM],
           "🔴 two stored games within a day could be THIS one (g5a holds a current report, g5b a day later): "
           "no sentence, never a guess")
        D_AT = W.explain([dict(REC)], "ncaaf", CL, now=AT)
        eq(D_AT[0]["why"], [LIST_REC, CM], "🔴 explain reads the reports at the card's build time it is given")
        D_LATE = W.explain([dict(REC)], "ncaaf", CL, now=LATE)
        eq(D_LATE[0]["why"], [CM],
           "🔴 ... and at a build time 6h15 after the reading, no sentence: the two cases together cannot both pass "
           "on the real clock, at any hour")
        # the card's OWN call: card_fb passes f"{DATA}/latest" (data/ncaaf/latest), relative to the repo root
        csrc = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
        ck('DATA = f"data/{LEAGUE}"' in csrc and csrc.count('LEAGUE, f"{DATA}/latest"') == 2,
           "the card hands fb_why a RELATIVE data/<league>/latest (the form the next case drives)")
        here = os.getcwd()
        try:
            os.chdir(CR)
            D_REL = W.explain([dict(REC)], "ncaaf", "data/ncaaf/latest", now=AT)
        finally:
            os.chdir(here)
        eq(D_REL[0]["why"], [LIST_REC, CM],
           "🔴 the card's own call, run from the repo root with a RELATIVE data/ncaaf/latest, still finds THIS "
           "game's current report")

        def boom(*a, **k):
            raise RuntimeError("planted")

        CI.report_for = boom
        kept = W.explain([dict(REC, why=["old"]), crow("Hoosier Wideout", "player_reception_yds", "Nowhere FC", "Nobody")],
                         "ncaaf", CL, ctx=W.Context("ncaaf", CL, 2026, now=AT))
        ck(kept[0]["why"] == ["old"] and kept[1]["why"] == [CM],
           "🔴 a why never raises: a report lookup that fails keeps the row's old why, and the next row still gets "
           "its own", kept)
    finally:
        D.team_codes, CI.report_for = real_codes, real_report_for

    # ══════════════════════════════════════════════════════════════════
    section("5. 🔴 A GAME LINE'S RECORD AGAINST THE TEAMS THE MODEL RATES ABOVE AVERAGE")
    # ══════════════════════════════════════════════════════════════════
    # `[Sam, 2026-10-26]` "let's do all of this", approving the proposal "add one plain line to each
    # game pick's why, like 'Washington is 2–3 against teams rated above average'. That's information
    # only and moves no %." The list is fb-model.json's
    # `above_average` (section 6 builds it): a game's schedule day -> the Monday the model rated it at
    # -> the teams rated above average then. Planted NFL schedule (ET kickoffs, as nflverse stores them).
    import fb_model as F  # noqa: E402
    L5 = os.path.join(T, "five", "data", "nfl", "latest")
    os.makedirs(L5)

    def fin(start, home, away, hs, as_):
        return {"start": start, "home": home, "away": away, "final": True, "home_score": hs, "away_score": as_}

    def upc(start, home, away):
        return {"start": start, "home": home, "away": away, "final": False, "home_score": None, "away_score": None}

    put("schedule-2026.json.gz", {"games": [
        fin("2026-09-13T13:00", "KC", "SEA", 20, 27),       # SEA beat KC (rated above average all along)
        fin("2026-09-13T16:25", "DEN", "MIA", 20, 10),      # MIA is never above average
        fin("2026-09-20T16:05", "SEA", "LAC", 17, 17),      # a TIE with LAC
        fin("2026-09-20T13:00", "NE", "DEN", 24, 21),
        fin("2026-10-04T16:25", "KC", "DEN", 24, 31),      # DEN won AT KC: a road win reads as a win
        fin("2026-09-27T13:00", "SEA", "NYJ", 10, 14),      # NYJ: above average only from Monday 10-26
        fin("2026-10-04T13:00", "SEA", "MIA", 31, 3),
        fin("2026-10-11T13:00", "BUF", "SEA", 30, 13),      # SEA lost at BUF
        upc("2026-10-25T20:20", "DEN", "SEA"),              # Sunday night: the books say 00:20Z MONDAY 10-26
        upc("2026-10-26T20:15", "NYJ", "MIA"),              # Monday night: rated at Monday 10-26
        upc("2026-10-29T20:15", "LV", "SEA"),               # Thursday: rated at Monday 10-26
        fin("2026-11-01T13:00", "SEA", "KC", 3, 40),        # AFTER both kickoffs (a rebuilt card): never counted
        upc("2026-11-01T13:00", "NE", "NYJ"), upc("2026-11-02T20:15", "NE", "NYJ")]}, L5)   # two within a day
    AA = {"monday": {"2026-10-25": "2026-10-19", "2026-10-26": "2026-10-26", "2026-10-29": "2026-10-26",
                     "2026-11-01": "2026-10-26", "2026-11-02": "2026-11-02"},
          "teams": {"2026-10-19": ["BUF", "KC", "LAC"], "2026-10-26": ["BUF", "KC", "LAC", "NYJ"],
                    "2026-11-02": ["BUF", "KC", "LAC", "NYJ"]}}
    ck(all(F.monday(d) == wk for d, wk in AA["monday"].items()),
       "the planted day -> Monday map is fb_model.monday's (the one fb_model.build writes)", AA["monday"])
    json.dump({"win_chances": [], "above_average": AA}, open(os.path.join(L5, "fb-model.json"), "w", encoding="utf-8"))
    cx5 = W.Context("nfl", L5, 2026)
    SNF = gl(market="moneyline", side="away", line=None, player="Seattle Seahawks", commence="2026-10-26T00:20:00Z")
    THU = gl(market="spread", side="away", line=-3.5, player="Seattle Seahawks", home="Las Vegas Raiders",
             commence="2026-10-30T00:15:00Z")
    VS = "Against teams the model rates above average this season: %s."
    eq(W.line_why(SNF, cx5),
       ["own sentence", "The Seattle Seahawks score 16.8 and allow 20.7 points a game this season (6 games).",
        "The Denver Broncos score 24 and allow 19.3 points a game this season (3 games).",
        VS % "Seattle Seahawks 1-1-1, Denver Broncos 1-0"],
       "🔴 Sunday night SEA @ DEN, rated at Monday 10-19 (its schedule day, 10-25; the books' UTC kickoff is "
       "already Monday 10-26): Seattle beat KC, tied LAC, lost at BUF = 1-1-1; NOT the NYJ loss (above average "
       "only from 10-26), not MIA (never), not the 11-01 KC game (after kickoff); Denver won AT KC = 1-0 "
       "(its own score, not the home side's); away first, after the two points sentences")
    eq(W.line_why(THU, cx5)[-1], VS % "Seattle Seahawks 1-2-1, Las Vegas Raiders 0-0",
       "🔴 Thursday LV vs SEA, rated at Monday 10-26: NYJ is above average now, so the NYJ loss counts (1-2-1); "
       "a team with no game this season is 0-0; still never the 11-01 game")
    two = gl(market="moneyline", side="home", line=None, home="New England Patriots", away="New York Jets",
             commence="2026-11-02T01:00:00Z")
    ck(not any(s.startswith("Against") for s in W.line_why(two, cx5)),
       "🔴 two stored games within a day could be THIS one: no sentence, never a guess", W.line_why(two, cx5))
    ck(not any(s.startswith("Against") for s in W.line_why(gl(market="moneyline", side="home", line=None,
                                                             home="Nowhere FC", commence="2026-10-26T00:20:00Z"), cx5)),
       "   a team it cannot resolve: no sentence")
    _aa, cx5.above = cx5.above, {"monday": AA["monday"], "teams": {}}
    try:
        eq(W.line_why(SNF, cx5)[-1], "The Denver Broncos score 24 and allow 19.3 points a game this season (3 games).",
           "🔴 no list for the game's Monday: no sentence (never 0-0 for everyone)")
    finally:
        cx5.above = _aa
    # the same game and schedule as the first check, so the game IS found and only the block is missing
    #    (section 1's tree stores no DEN-SEA game within a day of 10-26: it would stop before reading the block)
    L5N = os.path.join(T, "five-noblock", "data", "nfl", "latest")
    os.makedirs(L5N)
    shutil.copy(os.path.join(L5, "schedule-2026.json.gz"), L5N)
    put("fb-model.json", {"win_chances": []}, L5N)
    eq(W.line_why(SNF, W.Context("nfl", L5N, 2026)),
       ["own sentence", "The Seattle Seahawks score 16.8 and allow 20.7 points a game this season (6 games).",
        "The Denver Broncos score 24 and allow 19.3 points a game this season (3 games)."],
       "🔴 a model file with no above_average block (every file before 2026-10-26), the game found: every other "
       "sentence, and no record sentence (never a list made up in its place)")
    done = W.explain([dict(SNF, confidence=61, price=-150)], "nfl", L5, kind="lines")
    ck(done[0]["why"][-1] == VS % "Seattle Seahawks 1-1-1, Denver Broncos 1-0"
       and done[0]["confidence"] == 61 and done[0]["price"] == -150,
       "🔴 explain writes it on a liked game line and changes no chance or price", done[0])
    _vc = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
    _jm = re.search(r"_JARGON = (\[[^\]]*\])", _vc, re.S)
    _jargon = eval(_jm.group(1)) if _jm else []
    ck(len(_jargon) > 10 and not [j for j in _jargon if j in done[0]["why"][-1]],
       "🔴 the sentence passes verify_card.py's own jargon list (read out of it)", _jargon)

    # ══════════════════════════════════════════════════════════════════
    section("6. 🔴 fb-model.json's above_average: THE ROWS' OWN SOLVE, AND NOTHING ELSE MOVES")
    # ══════════════════════════════════════════════════════════════════
    def rate(R, O=None, D=None):
        return {"teams": set(R), "R": R, "O": O or {t: 0.0 for t in R}, "D": D or {t: 0.0 for t in R}}

    # R and O pick different teams, so a list of the wrong rating cannot pass
    S19 = rate({"KC": 5.0, "SEA": -1.0, "DEN": -2.0, "BUF": 3.0}, O={"KC": -3.0, "SEA": 4.0, "DEN": 2.0, "BUF": -1.0})
    S26 = rate({"KC": 4.0, "SEA": 1.5, "DEN": -2.0, "BUF": 2.0, "NYJ": 3.0})
    OWN = {"2026-10-12": rate({"MIA": 9.0, "KC": 0.0}), "2026-10-19": S19, "2026-10-26": S26}
    ROWS6 = [{"id": "f1", "day": "2026-10-11", "final": True}, {"id": "g1", "day": "2026-10-25", "final": False},
             {"id": "g2", "day": "2026-10-29", "final": False}, {"id": "g3", "day": "2026-10-13", "final": False}]
    eq(F.above_average_block("nfl", ROWS6, [{"game_id": "g1"}, {"game_id": "g2"}], OWN),
       {"monday": {"2026-10-25": "2026-10-19", "2026-10-29": "2026-10-26"},
        "teams": {"2026-10-19": ["BUF", "KC"], "2026-10-26": ["BUF", "KC", "NYJ"]}},
       "🔴 each Game Lines game's schedule day -> the Monday its ratings are read at -> the teams whose MARGIN "
       "rating (R) is above the plain mean then (not the offence's SEA and DEN); a game not on the Game Lines "
       "tab (g3, Monday 10-12) and a played one add nothing")
    CR6 = os.path.join(T, "six")
    os.makedirs(os.path.join(CR6, "data", "ncaaf", "latest"))
    put("schedule-2026.json.gz", {"games": [
        {"home": "Alpha", "away": "Beta", "home_class": "fbs", "away_class": "fbs"},
        {"home": "Gamma", "away": "Lowly", "home_class": "fbs", "away_class": "fcs"},
        {"home": "Gamma", "away": "Climber", "home_class": "fbs", "away_class": "fcs"}]},
        os.path.join(CR6, "data", "ncaaf", "latest"))
    SC = rate({"Alpha": 10.0, "Beta": 0.0, "Gamma": -4.0, "Lowly": -30.0, "Climber": 5.0})
    eq(F.above_average_block("ncaaf", [{"id": "c1", "day": "2026-10-31", "final": False}], [{"game_id": "c1"}],
                             {"2026-10-26": SC}, CR6)["teams"],
       {"2026-10-26": ["Alpha", "Climber"]},
       "🔴 college: above the FBS teams' mean (2.0), so Beta and Gamma are not (they would be against every "
       "team's mean, -3.8), and an FCS team above the FBS mean (Climber) is")

    # fb_model.build: the same synthetic league built twice, the solve handed over both times: once with
    #    the real list, once with a stub in its place that reads none of its arguments (the baseline: no
    #    list code runs at all). A baseline that ran the list code too would move with any change it made
    #    before reading the solve, and that change would never be seen.
    NOW6 = datetime.datetime.now(UTC)
    SYN = []
    for i in range(230):
        d = (datetime.date(2025, 9, 1) + datetime.timedelta(days=i // 3)).isoformat()
        won = i % 5 != 0
        SYN.append({"id": "s%d" % i, "lg": "nfl", "season": 2025, "day": d, "kick": d, "week": 1,
                    "home": "HOM", "away": "AWY", "final": True, "hs": 30 if won else 20, "as": 17 if won else 23,
                    "M": 3.0, "T": 44.5, "pml": 0.6, "snap": None, "dk_ml": None,
                    "close": {"spread": [(3.0, -110, -110, False)], "total": [(44.5, -110, -110, False)],
                              "moneyline": [(None, -150, 130, False)]},
                    "sig": {"h2h_m": None, "h2h_t": None, "form_m": None, "form_t": None, "def": None, "poss": None,
                            "out": None, "neutral": 0.0, "dome": 0.0, "own_m": 5.0 if won else -2.0, "own_t": 44.0}})
    MONS = []
    for j, ahead in enumerate((datetime.timedelta(hours=12), datetime.timedelta(days=7, hours=12))):
        c = (NOW6 + ahead).strftime("%Y-%m-%dT%H:%M:%SZ")
        MONS.append(F.monday(c[:10]))
        SYN.append(dict(SYN[0], id="u%d" % j, day=c[:10], kick=c, final=False, hs=None, **{"as": None},
                        snap={"names": ["Home Town", "Away Town"], "commence": c, "pulled_at": c[:10] + "T00:00:00Z",
                              "books": {"fanduel": {"h2h": {"Home Town": -150, "Away Town": 130},
                                                    "spreads": {"Home Town": {"pt": -3.0, "px": -110},
                                                                "Away Town": {"pt": 3.0, "px": -110}},
                                                    "totals": {"Over": {"pt": 44.5, "px": -110},
                                                               "Under": {"pt": 44.5, "px": -110}}}}}))
    OWN6 = {MONS[0]: S19, MONS[1]: S26}

    def fake_rows(*a, ratings=None, **k):
        if ratings is not None:
            ratings.update(OWN6)
        return json.loads(json.dumps(SYN))          # a fresh copy each build

    _orig6 = (F.build_rows, F.log, F.above_average_block)
    DOCS, TXT = {}, {}
    try:
        F.log, F.build_rows = (lambda m: None), fake_rows
        for real in (False, True):                  # the baseline first, before any list code has run
            F.above_average_block = _orig6[2] if real else (lambda *a, **k: {"monday": {}, "teams": {}})
            out6 = os.path.join(T, "fb-model-%d.json" % real)
            DOCS[real] = F.build("nfl", out=out6)
            TXT[real] = re.sub(r'"built_at": "[^"]*"', '"built_at": ""', open(out6, encoding="utf-8").read())
    finally:
        F.build_rows, F.log, F.above_average_block = _orig6
    ck(len(DOCS[True]["win_chances"]) == 2,
       "⚠️ the case exists: both upcoming games are on the Game Lines tab", DOCS[True]["win_chances"])
    eq(DOCS[True]["above_average"],
       {"monday": {SYN[-2]["day"]: MONS[0], SYN[-1]["day"]: MONS[1]},
        "teams": {MONS[0]: ["BUF", "KC"], MONS[1]: ["BUF", "KC", "NYJ"]}},
       "🔴 fb_model.build writes each Game Lines game's day, its Monday, and the teams rated above average "
       "then, from the solve build_rows handed it")
    eq(list(DOCS[True])[-1], "above_average", "🔴 ...as the LAST key of fb-model.json")
    _cut = lambda s: s[:s.index(',\n "above_average"')]  # noqa: E731
    ck(_cut(TXT[True]) == _cut(TXT[False]) and list(DOCS[False])[-1] == "above_average",
       "🔴🔴 every other field of fb-model.json is byte for byte what the build writes with NO list code at all "
       "(picks, chances, scores, simulations, records, pricing): information only, it moves no %",
       (len(TXT[True]), len(TXT[False])))

    # build_rows itself, on a planted tree: the solve it hands over is the one its rows read
    _t6 = os.path.join(T, "rows6")
    os.makedirs(os.path.join(_t6, "data", "nfl", "latest"))
    put("schedule-2026.json.gz", {"games": [
        dict(fin("2026-09-13T17:00", "AAA", "BBB", 30, 10), id="r1", week=1),
        dict(fin("2026-09-13T17:00", "CCC", "DDD", 20, 17), id="r2", week=1),
        dict(fin("2026-09-17T00:15", "AAA", "CCC", 35, 3), id="r3", week=2),
        dict(upc("2026-09-20T17:00", "AAA", "DDD"), id="r4", week=2),
        dict(upc("2026-09-27T17:00", "BBB", "CCC"), id="r5", week=3)]}, os.path.join(_t6, "data", "nfl", "latest"))

    class _NoAllowed:
        def __init__(self, lg):
            pass

        def fraction(self, g):
            return None

    _old6 = (F.t60r.history, F.t60r.Allowed)
    try:
        F.t60r.history, F.t60r.Allowed = (lambda lg: []), _NoAllowed
        HANDED = {}
        R_WITH = F.build_rows("nfl", root=_t6, board={}, ratings=HANDED)
        R_WITHOUT = F.build_rows("nfl", root=_t6, board={})
    finally:
        F.t60r.history, F.t60r.Allowed = _old6
    _js = lambda x: json.dumps(x, sort_keys=True, default=sorted)  # noqa: E731
    _direct = F.own_ratings(F.rating_games("nfl", _t6), {F.monday(r["day"]) for r in R_WITHOUT})
    ck(len(R_WITH) == 5 and _js(R_WITH) == _js(R_WITHOUT),
       "🔴 handing the solve over leaves every row exactly as it was")
    ck(sorted(HANDED) == ["2026-09-07", "2026-09-14", "2026-09-21"] and _js(HANDED) == _js(_direct),
       "🔴 ...and what it hands over is the solve the rows read: every row's Monday, the same numbers (no "
       "second, different solve)", sorted(HANDED))
finally:
    shutil.rmtree(T, ignore_errors=True)
