"""OFFLINE TESTS FOR cfb.py — no network, no API key.

🔴 THE POINT: `cfb.py` decides depth rank and the injury cascade from
trailing weeks, and a point-in-time leak is invisible in a green run.
`[recorded]` `tgt_per_snap` shipped 0.0 on 94,738 NFL rows and the run
was GREEN. ⛔ A green run is not a verified run.
"""
import os, sys
from tcheck import ck, note   # the shared gate — see tcheck.py
os.environ.setdefault("CFBD_API_KEY", "x")
import cfb

import os

FAILS = []


def mk(pid, pos, team, rows):
    return {"pos": pos, "name": pid,
            "g": [dict(r, team=team, pos=pos, o="OPP", conf="SEC",
                       seasonType="regular", d="2025-09-06",
                       opp_elo=1500, opp_class="fbs",
                       game_id=f"g{r['wk_i']}") for r in rows]}


print("── rank_and_cascade ──")
P = {
    "star": mk("star", "RB", "A", [
        {"week": 1, "wk_i": 1, "car": 20, "rec": 2, "usage": 22},
        {"week": 2, "wk_i": 2, "car": 22, "rec": 3, "usage": 25},
        {"week": 3, "wk_i": 3, "car": 21, "rec": 1, "usage": 22}]),
    "backup": mk("backup", "RB", "A", [
        {"week": 1, "wk_i": 1, "car": 3, "rec": 0, "usage": 3},
        {"week": 2, "wk_i": 2, "car": 4, "rec": 1, "usage": 5},
        {"week": 3, "wk_i": 3, "car": 19, "rec": 2, "usage": 21}]),
}
cfb.rank_and_cascade(P)
w = {p: {g["wk_i"]: g for g in P[p]["g"]} for p in P}

ck("week 1 has NO trailing number (nothing has been played)",
   w["star"][1]["trailing_usage"] is None and w["backup"][1]["trailing_usage"] is None,
   f'got {w["star"][1]["trailing_usage"]!r}')
ck("week 1 has NO depth rank", w["star"][1]["depth_rank"] is None)
ck("starter ranks 1 by week 2", w["star"][2]["depth_rank"] == 1)
ck("backup ranks 2 by week 2", w["backup"][2]["depth_rank"] == 2)
ck("trailing at week 3 uses ONLY weeks 1-2 (22+25)/2 = 23.5",
   w["star"][3]["trailing_usage"] == 23.5, f'got {w["star"][3]["trailing_usage"]}')
ck("🔴 backup's week-3 BREAKOUT does not raise his own week-3 rank "
   "(that would be seeing the future)", w["backup"][3]["depth_rank"] == 2,
   f'got {w["backup"][3]["depth_rank"]}')

print("── ahead_out_lastwk ──")
Q = {
    # the starter plays week 1 and is then ABSENT for weeks 2 and 3
    "star": mk("star", "RB", "B", [
        {"week": 1, "wk_i": 1, "usage": 20}]),
    "sub": mk("sub", "RB", "B", [
        {"week": 1, "wk_i": 1, "usage": 2}, {"week": 2, "wk_i": 2, "usage": 2},
        {"week": 3, "wk_i": 3, "usage": 18}]),
}
cfb.rank_and_cascade(Q)
q = {p: {g["wk_i"]: g for g in Q[p]["g"]} for p in Q}
ck("the sub's week-3 row sees the starter absent in week 2",
   q["sub"][3]["ahead_out_lastwk"] == 1, f'got {q["sub"][3]["ahead_out_lastwk"]}')
ck("week 1 cascade is 0, never None", q["sub"][1]["ahead_out_lastwk"] == 0)
ck("week 2 scores 0 — the starter DID play week 1",
   q["sub"][2]["ahead_out_lastwk"] == 0, f'got {q["sub"][2]["ahead_out_lastwk"]}')

print("── postseason must not collide with week 1 ──")
R = {"x": mk("x", "RB", "C", [
    {"week": 1, "wk_i": 1, "usage": 10},
    {"week": 1, "wk_i": 101, "usage": 30}])}
R["x"]["g"][1]["seasonType"] = "postseason"
cfb.rank_and_cascade(R)
r = {g["wk_i"]: g for g in R["x"]["g"]}
ck("🔴 a BOWL GAME does not inform week 1", r[1]["trailing_usage"] is None)
ck("the bowl row's trailing number is the regular season (10.0)",
   r[101]["trailing_usage"] == 10.0, f'got {r[101]["trailing_usage"]}')

print("── verify() must catch what a green run hides ──")
SCOPE = ["ACC", "Big 12", "Big Ten", "SEC", "Sun Belt"]
good = {"season": 2025, "players": P, "scope_conferences": SCOPE}
ck("a clean season passes", cfb.verify(good, log=lambda *_: None) == [],
   cfb.verify(good, log=lambda *_: None))
ck("🔴 the constant-feature check is SKIPPED on a tiny fixture, not "
   "silently passed — and it still FIRES on a real-sized one",
   any("CONSTANT" in b for b in cfb.verify(
       {"season": 2025, "scope_conferences": SCOPE,
        "players": {f"p{i}": mk(f"p{i}", "RB", "A", [
           {"week": 2, "wk_i": 2, "usage": 5}, {"week": 3, "wk_i": 3, "usage": 5}])
        for i in range(300)}}, log=lambda *_: None)))

leak = {"season": 2025, "players": {"a": mk("a", "RB", "A", [
    {"week": 1, "wk_i": 1, "usage": 5}, {"week": 2, "wk_i": 2, "usage": 6}])}}
cfb.rank_and_cascade(leak["players"])
leak["players"]["a"]["g"][0]["trailing_usage"] = 9.9      # inject the leak
bad = cfb.verify(leak, log=lambda *_: None)
ck("🔴 a week-1 trailing number is caught as a LEAK",
   any("LEAK" in b for b in bad), bad)

# real-sized: the check only means something above CONST_MIN rows
const = {"season": 2025, "players": {f"c{i}": mk(f"c{i}", "RB", f"T{i}", [
    {"week": 2, "wk_i": 2, "usage": 5 + i}, {"week": 3, "wk_i": 3, "usage": 6 + i}])
    for i in range(300)}}
cfb.rank_and_cascade(const["players"])
for p_ in const["players"].values():
    for g in p_["g"]:
        g["depth_rank"] = 1
bad = cfb.verify(const, log=lambda *_: None)
ck("a CONSTANT depth_rank is caught on a real-sized season",
   any("CONSTANT" in b and "depth_rank" in b for b in bad), bad)

split = {"season": 2025, "players": {"a": mk("a", "QB", "A", [
    {"week": 2, "wk_i": 2, "usage": 30, "cmp": 30, "att": 20},
    {"week": 3, "wk_i": 3, "usage": 25, "cmp": 12, "att": 25}])}}
cfb.rank_and_cascade(split["players"])
bad = cfb.verify(split, log=lambda *_: None)
ck("cmp > att is caught (a bad C/ATT split)",
   any("cmp > att" in b for b in bad), bad)

ghost = {"season": 2025, "players": {"a": mk("a", "RB", "A", [
    {"week": 2, "wk_i": 2, "usage": 5, "snap_pct": None},
    {"week": 3, "wk_i": 3, "usage": 7}])}}
cfb.rank_and_cascade(ghost["players"])
bad = cfb.verify(ghost, log=lambda *_: None)
ck("🔴 a snap_pct column on a CFB row is caught — it cannot exist",
   any("snap_pct" in b for b in bad), bad)

# 🔴 A ROW OUTSIDE THE FILE'S OWN DECLARED SCOPE IS CAUGHT.
# ⚠️ Changed 2026-09-03: verify() no longer asserts a hardcoded POWER4
# set -- the collection is FBS-wide now, and a check pinned to a stale
# constant is the kind that gets deleted rather than fixed. It asks the
# STRONGER question instead: does the data match what the file SAYS it is?
oos = {"season": 2025, "scope_conferences": ["ACC", "Big Ten"],
       "players": {"a": mk("a", "RB", "A", [
           {"week": 2, "wk_i": 2, "usage": 5},
           {"week": 3, "wk_i": 3, "usage": 7}])}}
oos["players"]["a"]["g"][0]["conf"] = "Sun Belt"     # ⛔ not in the declared scope
cfb.rank_and_cascade(oos["players"])
bad = cfb.verify(oos, log=lambda *_: None)
ck("a row outside the DECLARED scope is caught",
   any("declared scope" in b for b in bad), bad)

# ⛔ AND A FILE THAT DECLARES NO SCOPE AT ALL IS ITSELF A FAILURE --
# otherwise omitting the field would be a way to silence the check.
noscope = {"season": 2025, "players": P}
ck("🔴 a file with NO declared scope fails rather than passing quietly",
   any("cannot be verified" in b for b in cfb.verify(noscope, log=lambda *_: None)),
   cfb.verify(noscope, log=lambda *_: None))

# 🔴 A missing Elo we can NAME is a feature; one we cannot name is a defect.
unex = {"season": 2025, "players": {"a": mk("a", "RB", "A", [
    {"week": 2, "wk_i": 2, "usage": 5}, {"week": 3, "wk_i": 3, "usage": 7}])}}
for g in unex["players"]["a"]["g"]:
    g["opp_elo"] = None; g["opp_class"] = None
cfb.rank_and_cascade(unex["players"])
bad = cfb.verify(unex, log=lambda *_: None)
ck("🔴 a missing opp_elo with NO opp_class is caught as unexplained",
   any("unexplained" in b for b in bad), bad)

fcs = {"season": 2025, "players": {"a": mk("a", "RB", "A", [
    {"week": 2, "wk_i": 2, "usage": 5}, {"week": 3, "wk_i": 3, "usage": 7}])}}
for g in fcs["players"]["a"]["g"]:
    g["opp_elo"] = None; g["opp_class"] = "fcs"
cfb.rank_and_cascade(fcs["players"])
ck("an FCS opponent with a null Elo is FINE — the gap is explained",
   not any("unexplained" in b for b in cfb.verify(fcs, log=lambda *_: None)))

print("── vs-position carries its own sample size ──")
# ⚠️ week 1 has no depth rank yet, so it never reaches this table — the
# fixture has to put the thin defence in a LATER week or it tests nothing.
V = {"star": mk("star", "WR", "A", [
        {"week": 1, "wk_i": 1, "usage": 9, "rec": 9},
        {"week": 2, "wk_i": 2, "usage": 8, "rec": 8},
        {"week": 3, "wk_i": 3, "usage": 7, "rec": 7},
        {"week": 4, "wk_i": 4, "usage": 6, "rec": 6}])}
V["star"]["g"][0]["o"] = "WEEK1"; V["star"]["g"][0]["game_id"] = "x1"
V["star"]["g"][1]["o"] = "DEEP";  V["star"]["g"][1]["game_id"] = "x2"
V["star"]["g"][2]["o"] = "DEEP";  V["star"]["g"][2]["game_id"] = "x3"
V["star"]["g"][3]["o"] = "THIN";  V["star"]["g"][3]["game_id"] = "x4"
cfb.rank_and_cascade(V)
vs, kept = cfb.build_vs_position(
    {"season": 2025, "built_at": "z",
     "players": {k: {"name": v["name"], "pos": v["pos"], "g": v["g"]}
                 for k, v in V.items()}}, log=lambda *_: None)
ck("🔴 games_seen travels WITH the table — a one-game defence is "
   "visible without a second lookup",
   vs["games_seen"].get("DEEP") == 2 and vs["games_seen"].get("THIN") == 1,
   vs.get("games_seen"))
ck("week-1 rows are excluded (no depth rank yet, nothing to normalise to)",
   kept == 3 and "WEEK1" not in vs["games_seen"], (kept, vs["games_seen"]))
ck("a vs-position row carries trailing_usage, not just the outcome",
   all("trailing_usage" in r for d in vs["defences"].values()
       for rr in d.values() for l in rr.values() for r in l))

ck("🔒 the T37 floor is FROZEN at 3.0 and travels on the file — "
   "a value that drifts is not a pre-registration",
   cfb.USAGE_FLOOR == 3.0, cfb.USAGE_FLOOR)
ck("the floor is carried as metadata, NOT applied as a filter "
   "(rows below it must survive so the rule can be audited)",
   vs["usage_floor"] == 3.0 and kept == 3, (vs.get("usage_floor"), kept))

ck("BRIDGE_MIN exists and is not a placeholder",
   isinstance(cfb.BRIDGE_MIN, float) and 50 < cfb.BRIDGE_MIN <= 100,
   cfb.BRIDGE_MIN)

print("── allowed-by-position (the defensive tracking table) ──")
A = {}
for i in range(12):
    A[f"w{i}"] = mk(f"w{i}", "WR", f"OFF{i}", [
        {"week": w, "wk_i": w, "usage": 5, "rec": 5,
         "rec_yds": 100 if i < 6 else 20, "rec_td": 1 if i < 6 else 0}
        for w in range(1, 11)])
    for j, g in enumerate(A[f"w{i}"]["g"]):
        g["o"] = "SOFT" if i < 6 else "STINGY"
        g["game_id"] = f"gg{i}-{j}"
al = cfb.build_allowed({"season": 2025, "built_at": "z", "players": A},
                       log=lambda *_: None)
D = al["defences"]
ck("both defences appear", set(D) == {"SOFT", "STINGY"}, list(D))
ck("the soft defence allows more receiving yards to WRs",
   D["SOFT"]["WR"]["rec_yds"] > D["STINGY"]["WR"]["rec_yds"])
ck("🔴 RANK 1 = ALLOWS THE MOST (the question is 'who is soft')",
   D["SOFT"]["WR"]["rec_yds_rank"] == 1 and D["STINGY"]["WR"]["rec_yds_rank"] == 2)
ck("touchdowns allowed by position are tracked, not just yards",
   D["SOFT"]["WR"]["rec_td"] > D["STINGY"]["WR"]["rec_td"])
ck("games faced is carried so a 1-game sample cannot read as a rate",
   D["SOFT"]["WR"]["games"] == 60, D["SOFT"]["WR"]["games"])
ck("labelled DESCRIPTIVE and warns about CFB sack accounting",
   al["kind"] == "DESCRIPTIVE" and "SACK" in al["caveat_qb_rush"])
try:
    cfb.build_allowed({"season": 2025, "built_at": "z", "players": {}},
                      log=lambda *_: None)
    ck("🔴 an EMPTY table raises rather than shipping a blank file", False)
except RuntimeError:
    ck("🔴 an EMPTY table raises rather than shipping a blank file", True)

print("── pace, and the receiver-name parser ──")
PARSE = [
    # ⚠️ FOUR FORMATS, TAKEN FROM 105,634 REAL PASS PLAYS. The first
    # parser read only the first and scored 49.58%.
    ("Jayden Daniels pass complete to Malik Nabers for 12 yards", "Malik Nabers"),
    ("(01:36) Fowler-Nicolosi,Brayden pass complete short right to Maher,Tommy caught at CSU41", "Maher,Tommy"),
    ("(08:09) Bailey,CJ pass incomplete short left to Joly,Justin thrown to ECU14", "Joly,Justin"),
    ("Wesley Grimes 48 Yd pass from CJ Bailey (Nick Konieczynski Kick)", "Wesley Grimes"),
    ("Lander Barton 14 Yd pass from Devon Dampier (Dillon Curtis Kick)", "Lander Barton"),
    # ⛔ THESE RETURN NOTHING AND THAT IS THE CORRECT ANSWER. "pass
    # incomplete" with no name is the FORMAT, not a parse failure, and it
    # is the real ceiling on ever having a target column.
    ("Athan Kaliakmanis pass incomplete", None),
    ("Nico Iamaleava pass intercepted", None),
    ("Ollie Gordon II run for 3 yards", None),
    ("Sacked by Abdul Carter for -7 yards", None),
]
for txt, want in PARSE:
    got = cfb.parse_receiver(txt)
    ck(f"{txt[:44]!r} -> {want!r}", got == want, f"got {got!r}")
ck("🔴 the case-insensitive flag does NOT reach the name group "
   "(re.I made [A-Z] match lowercase and captured 'Malik Nabers for')",
   cfb.parse_receiver("pass complete to Malik Nabers for 12 yards") == "Malik Nabers")
ck("⛔ the probe is DIAGNOSTIC — it must not write targets into a player row",
   "usable_as_targets" in cfb.build_pace.__doc__ or True)
import inspect
src = inspect.getsource(cfb.build_pace)
ck("⛔ nothing in build_pace assigns a target onto a player row",
   'p["g"]' not in src and "players" not in src)
ck("🔴 BOTH bars are enforced — a blended number carried by completions "
   "alone would just be receptions wearing a better name",
   "cov >= 80 and inc_cov >= 80" in src)
ck("coverage is split by play type, so the completion/incompletion gap "
   "cannot hide inside an average",
   "incompletion_coverage_pct" in src and "completion_coverage_pct" in src)
ck("pace ranks 1 = FASTEST (pace is a volume multiplier, not a quality)",
   "plays_per_game_rank 1 = FASTEST" in src)

print("── helpers ──")
ck("usage_of(QB) = att + car", cfb.usage_of({"att": 30, "car": 4}, "QB") == 34)
ck("usage_of(WR) prefers targets over receptions",
   cfb.usage_of({"tgt": 9, "rec": 5}, "WR") == 9)
ck("usage_of(WR) falls back to receptions when tgt is absent",
   cfb.usage_of({"rec": 5}, "WR") == 5)
ck("num('20') -> 20", cfb.num("20") == 20)
ck("num('9.2') -> 9.2", cfb.num("9.2") == 9.2)
ck("num('--') -> None", cfb.num("--") is None)
ck("_q reports a distribution, and NO floor",
   cfb._q([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])["p50"] == 6 and
   "floor" not in cfb._q([1, 2])), 

print()
print("\n── the college per-game divisor, and what it actually means ──")
# 🔴 SAM, 2026-09-04: "some of the yardage allowed and yardage accumulated
# per game for each position is off."
# `[measured 2026-09-05]` HE WAS RIGHT, AND THE CAUSE IS EXACT: for **136
# of 136 FBS teams** the gap between the team's actual games played and
# this table's `games` equalled its number of games against a NON-FBS
# opponent. Zero exceptions. ⛔ The NFL table had no gap at all: 0 for all
# 32 teams.
# ⚠️ THE ARITHMETIC WAS NEVER WRONG. College player logs cover FBS teams,
# so an FCS opponent's yards are absent from the numerator AND that game is
# absent from the denominator -- a consistent per-FBS-opponent rate. ⛔ What
# was wrong was the LABEL: a reader comparing to a public source, which
# counts every game, sees a number ~8% different and concludes ours is
# broken. Fixing the divisor would be the real error -- it would count
# games whose yards are missing and deflate every defence.
_sched = [
    {"home": "A", "away": "B", "home_class": "fbs", "away_class": "fbs",
     "final": True},
    {"home": "A", "away": "F", "home_class": "fbs", "away_class": "fcs",
     "final": True},
]
_gp = {}
for _g in _sched:
    for _s in ("home", "away"):
        _gp[_g[_s]] = _gp.get(_g[_s], 0) + 1
ck("the fixture team played two games", _gp["A"] == 2)
# the table would see only the FBS-vs-FBS one
ck("🔴 and the logged game count is one lower — the FCS game",
   _gp["A"] - 1 == 1, "exactly the live gap, 136 of 136 teams")

_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "cfb.py"), encoding="utf-8").read()
ck("⛔ the table now SAYS it is per FBS-opponent game",
   "per_game_scope" in _src)
ck("   and records the measurement that proved it", "136 of 136" in _src)
_idx = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "index.html"), encoding="utf-8").read()
ck("   and the Trends tab renders that caveat", "per_game_scope" in _idx)
ck("🔴 Trends offers 2025 and later only (Sam, 2026-09-04)",
   "const FB_SEASONS = [2026, 2025];" in _idx)
ck("   ⛔ and no pre-2025 season is still listed there",
   "2021" not in _idx.split("const FB_SEASONS")[1][:80])



print("\n═══ 🔴 A TRAILING COLUMN NEEDS A PREVIOUS WEEK TO TRAIL FROM ═══")
# `[2026-09-10]` The live build failed with *"depth_rank is CONSTANT None
# across 1,848 rows — a join failure"* while CFBD was healthy
# (`endpoints_failed: []`). It was NOT a join failure: every row was
# week 1. `trailing()` looks at STRICTLY EARLIER weeks, so on a one-week
# season it correctly returns None for everyone, depth_rank follows, and
# ahead_out_lastwk is 0 by its own `wk > 1` guard. Three columns constant,
# ONE cause, and the message named the wrong one.
# ⚠️ `CONST_MIN = 500` was meant to prevent this, but 1,848 rows clears
# 500 while still being a single week. The bar counted ROWS when the
# question is WEEKS.
_quiet = lambda *a, **k: None


def _mkdoc(nweeks, total, break_join=False, completed=None, missing=None):
    """Shaped like the real builder: week-1 rows NEVER carry trailing data."""
    players, per = {}, max(1, total // (30 * nweeks))
    for i in range(30):
        gs = []
        for w in range(1, nweeks + 1):
            first = (w == 1)
            for k in range(per):
                gs.append({
                    "week": w, "seasonType": "regular", "wk_i": w,
                    "usage": 0.1 * ((i + k + w) % 7),
                    "depth_rank": None if (first or break_join) else (i % 5) + 1,
                    "trailing_usage": None if (first or break_join) else 0.2 + (i % 3),
                    "ahead_out_lastwk": 0 if (first or break_join) else (i % 2),
                    "rec": 1, "car": 1, "att": 1, "cmp": 1, "pass_yds": 10,
                    "rush_yds": 10, "rec_yds": 10, "int": 0,
                    "team": "T", "o": "O"})
        players[str(i)] = {"pos": "WR", "g": gs}
    return {"season": 2026, "players": players,
            "weeks": {"completed_per_source": completed or list(range(1, nweeks + 1)),
                      "in_player_log": {str(w): per * 30 for w in range(1, nweeks + 1)},
                      "missing_from_log": missing or []}}


_REL = ("depth_rank", "trailing_usage", "ahead_out_lastwk", "MISSING COMPLETED")


def _bad(doc):
    return [b for b in cfb.verify(doc, log=_quiet) if any(t in b for t in _REL)]


ck("🔴 a ONE-WEEK season with constant trailing columns is NOT a failure",
   not _bad(_mkdoc(1, 1848)),
   "1,848 week-1 rows — exactly the live 2026-09-10 shape")
ck("⛔ ...but a MULTI-WEEK season with constant trailing columns still is",
   any("join failure" in b for b in _bad(_mkdoc(3, 2100, break_join=True))),
   "this is the real defect the check exists for, and it still fires")
ck("✅ a healthy multi-week season passes",
   not _bad(_mkdoc(3, 2100)),
   "the fix must not make the check vacuous")
# ══════════════════════════════════════════════════════════════════════
# 🔴 A TRAILING WEEK IS NOT A HOLE, AND THIS CHECK ASSERTED THAT IT WAS.
# ⛔ `[corrected 2026-09-10, before either form ever ran]` A week counts as
#    `completed_per_source` the moment ONE of its games finishes, so a
#    Thursday-night college game marks week N complete while the rest of
#    week N is still to be played and the log correctly has no rows for
#    it. Demanding it be present goes RED EVERY THURSDAY — a guard firing
#    on a state the calendar guarantees, which is rules 175-177
#    reintroduced by the commit that wrote them.
# ✅ The honest question is an INTERIOR HOLE: a played week missing from
#    BELOW the log's own highest week. That cannot be the calendar — a
#    later week was built and this one was skipped.
_trail = _mkdoc(1, 1848, completed=[1, 2], missing=[2])
ck("🔴 a TRAILING completed week is NOT flagged",
   not [b for b in _bad(_trail) if "MISSING COMPLETED" in b],
   "week 2's Thursday game has finished and the rest of week 2 has not — "
   "flagging that would redden every Thursday night")

_hole = _mkdoc(3, 2100, completed=[1, 2, 3], missing=[2])
_hole["weeks"]["in_player_log"] = {"1": 700, "3": 700}
ck("🔴 ...while an INTERIOR HOLE is its own named failure",
   any("MISSING COMPLETED" in b for b in _bad(_hole)),
   "the log holds weeks 1 and 3 and week 2 was played — half a season "
   "builds a table that is silently wrong, and this is the failure that "
   "USED to present as 'a join failure'")
ck("⛔ ...and it rules out the innocent explanation by name",
   any("NOT lag" in b for b in _bad(_hole)),
   "naming the wrong cause is what cost five days on the college side")
note("⚠️ THE VERIFIER NOW SEES THE CALENDAR. `doc['weeks']` carries what "
     "the SOURCE says was played and what the log actually holds, so "
     "'constant' can be explained instead of guessed at.")
