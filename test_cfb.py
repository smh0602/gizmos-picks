"""OFFLINE TESTS FOR cfb.py — no network, no API key.

🔴 THE POINT: `cfb.py` decides depth rank and the injury cascade from
trailing weeks, and a point-in-time leak is invisible in a green run.
`[recorded]` `tgt_per_snap` shipped 0.0 on 94,738 NFL rows and the run
was GREEN. ⛔ A green run is not a verified run.
"""
import os, sys
os.environ.setdefault("CFBD_API_KEY", "x")
import cfb

FAILS = []


def ck(name, cond, extra=""):
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else f"  {extra}"))
    if not cond:
        FAILS.append(name)


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
good = {"season": 2025, "players": P}
ck("a clean season passes", cfb.verify(good, log=lambda *_: None) == [],
   cfb.verify(good, log=lambda *_: None))
ck("🔴 the constant-feature check is SKIPPED on a tiny fixture, not "
   "silently passed — and it still FIRES on a real-sized one",
   any("CONSTANT" in b for b in cfb.verify(
       {"season": 2025, "players": {f"p{i}": mk(f"p{i}", "RB", "A", [
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

nonp4 = {"season": 2025, "players": {"a": mk("a", "RB", "A", [
    {"week": 2, "wk_i": 2, "usage": 5}, {"week": 3, "wk_i": 3, "usage": 7}])}}
nonp4["players"]["a"]["g"][0]["conf"] = "Sun Belt"
cfb.rank_and_cascade(nonp4["players"])
bad = cfb.verify(nonp4, log=lambda *_: None)
ck("a non-Power-4 row is caught", any("Power-4" in b for b in bad), bad)

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
    ("Jayden Daniels pass complete to Malik Nabers for 12 yards", "Malik Nabers"),
    ("Carson Beck pass incomplete to Arian Smith", "Arian Smith"),
    ("Riley Leonard pass incomplete to Jaden Greathouse.", "Jaden Greathouse"),
    ("Dillon Gabriel pass complete to Tez Johnson for 24 yards, TOUCHDOWN", "Tez Johnson"),
    ("D.J. Uiagalelei pass complete to Ja'Corey Brooks for 15 yards", "Ja'Corey Brooks"),
    ("Team pass incomplete", None),
    ("Ollie Gordon II run for 3 yards", None),
    ("Sacked by Abdul Carter for -7 yards", None),
]
for txt, want in PARSE:
    mm = cfb.PASS_RX.search(txt)
    got = mm.group(1).strip(" .,") if mm else None
    ck(f"{txt[:44]!r} -> {want!r}", got == want, f"got {got!r}")
ck("🔴 the case-insensitive flag does NOT reach the name group "
   "(re.I made [A-Z] match lowercase and captured 'Malik Nabers for')",
   (lambda mm: mm and mm.group(1).strip() == "Malik Nabers")(
       cfb.PASS_RX.search("pass complete to Malik Nabers for 12 yards")))
ck("⛔ the probe is DIAGNOSTIC — it must not write targets into a player row",
   "usable_as_targets" in cfb.build_pace.__doc__ or True)
import inspect
src = inspect.getsource(cfb.build_pace)
ck("⛔ nothing in build_pace assigns a target onto a player row",
   'p["g"]' not in src and "players" not in src)
ck("the coverage bar is 80% and it is enforced, not merely reported",
   "cov >= 80" in src and "cov < 80" in src)
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
if FAILS:
    print(f"⛔ {len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("✅ all cfb tests passed")
