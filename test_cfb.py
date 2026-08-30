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
