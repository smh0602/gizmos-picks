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
"""
import datetime
import gzip
import json
import os
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
finally:
    shutil.rmtree(T, ignore_errors=True)
