#!/usr/bin/env python3
"""`build_def_epa` — the T48 collector, tested against a synthetic feed.

🔴 WHY A FIXTURE AND NOT A LIVE PULL. Every defect this project has
shipped in a collector survived because the only way to see it was to
run the real thing and eyeball the output: the `stats_player_reg`
season-totals trap, the name join that matched 0 of 1,848, the `re.I`
that captured "Malik Nabers for", the participation release that read as
empty. ⛔ EYEBALLING IS NOT A TEST.

✅ So the feed is FAKED, with the answers computed by hand, and the
things that must not happen are asserted:
  1. the DEFENCE is grouped by `defteam`, not `posteam` -- the Max Muncy
     rule in its NFL form. **Talking about the wrong team is this
     project's single most repeated data error.**
  2. EPA's SIGN is preserved. `epa` is signed from the OFFENCE's side, so
     for a defence LOWER IS BETTER. ⛔ A flipped sign would invert every
     conclusion T48 draws and would still look perfectly plausible.
  3. pass and rush split correctly and each is a PER-PLAY RATE.
  4. non-pass, non-rush plays (kicks, punts, no-plays) are EXCLUDED.
  5. ⛔ IT FAILS CLOSED. Missing columns and a thin `epa` column write
     NOTHING and say why.

⚠️ No network, no data files, no clock.
"""
import sys

import nfl

fails = []


def eq(got, want, label):
    ok = got == want
    print(f"  {'ok  ' if ok else '🔴 FAIL'} {label:<44} {got!r:>22}  want {want!r}")
    if not ok:
        fails.append(label)


def run(rows, season=2025):
    """Call build_def_epa against a fake play-by-play feed."""
    nfl._rows = lambda seen, tag, fname, log: rows
    return nfl.build_def_epa(season, seen={}, log=lambda *a, **k: None)


def play(game, week, off, dfn, epa, kind):
    r = {"game_id": game, "week": week, "posteam": off, "defteam": dfn,
         "epa": epa, "pass": "0", "rush": "0"}
    if kind in ("pass", "rush"):
        r[kind] = "1"
    return r


# ══════════════════════════════════════════════════════════════════════
print("1. the DEFENCE is the defence — the Max Muncy rule, NFL edition")
# BUF's offence gains, KC's defence concedes. The row must land on KC.
rows = [play("G1", 1, "BUF", "KC", 0.50, "pass"),
        play("G1", 1, "BUF", "KC", 0.10, "rush"),
        play("G1", 1, "KC", "BUF", -0.30, "pass"),
        play("G1", 1, "KC", "BUF", -0.10, "rush")]
doc, rep = run(rows)
eq(rep["usable"], True, "usable")
eq(sorted(doc["by_team"]), ["BUF", "KC"], "both defences present")
eq(doc["by_team"]["KC"]["G1"]["epa_per_play"], 0.30,
   "KC DEFENCE concedes BUF's +0.50/+0.10")
eq(doc["by_team"]["BUF"]["G1"]["epa_per_play"], -0.20,
   "BUF DEFENCE concedes KC's -0.30/-0.10")
eq(doc["by_team"]["KC"]["G1"]["opp"], "BUF", "opponent is the OFFENCE")
# ⛔ If the grouping key were `posteam` these two would be swapped and
# every number would still look like a plausible EPA. That is the whole
# danger.
eq(doc["by_team"]["KC"]["G1"]["epa_per_play"]
   != doc["by_team"]["BUF"]["G1"]["epa_per_play"], True,
   "the two defences are NOT the same row")

print("\n2. the SIGN survives — lower is better for a defence")
rows = [play("G1", 1, "BUF", "KC", 1.00, "pass"),
        play("G1", 1, "BUF", "KC", 1.00, "pass"),
        play("G2", 2, "BUF", "NE", -1.00, "pass"),
        play("G2", 2, "BUF", "NE", -1.00, "pass")]
doc, _ = run(rows)
eq(doc["by_team"]["KC"]["G1"]["epa_per_play"], 1.0, "porous defence POSITIVE")
eq(doc["by_team"]["NE"]["G2"]["epa_per_play"], -1.0, "stout defence NEGATIVE")
eq(doc["by_team"]["NE"]["G2"]["epa_per_play"]
   < doc["by_team"]["KC"]["G1"]["epa_per_play"], True,
   "the BETTER defence has the LOWER number")

print("\n3. pass and rush split, each as its own per-play rate")
rows = [play("G1", 1, "BUF", "KC", 0.90, "pass"),
        play("G1", 1, "BUF", "KC", 0.30, "pass"),
        play("G1", 1, "BUF", "KC", -0.20, "rush")]
doc, _ = run(rows)
g = doc["by_team"]["KC"]["G1"]
eq(g["plays"], 3, "plays")
eq(g["pass_plays"], 2, "pass plays")
eq(g["rush_plays"], 1, "rush plays")
eq(g["pass_epa_per_play"], 0.60, "pass epa/play = (0.9+0.3)/2")
eq(g["rush_epa_per_play"], -0.20, "rush epa/play")
eq(round(g["epa_per_play"], 5), round((0.9 + 0.3 - 0.2) / 3, 5),
   "total is over ALL plays, not the mean of the two rates")
# ⚠️ A defence that faced no rushes must not divide by zero.
rows = [play("G1", 1, "BUF", "KC", 0.50, "pass")]
doc, _ = run(rows)
eq(doc["by_team"]["KC"]["G1"]["rush_epa_per_play"], None,
   "no rush plays -> None, not 0.0 and not a crash")

print("\n4. kicks, punts and no-plays are EXCLUDED")
rows = [play("G1", 1, "BUF", "KC", 0.40, "pass"),
        play("G1", 1, "BUF", "KC", 0.20, "rush"),
        play("G1", 1, "BUF", "KC", 9.99, "punt"),      # neither flag set
        play("G1", 1, "BUF", "KC", -9.99, "kickoff")]
doc, rep = run(rows)
eq(rep["pass_or_rush_plays"], 2, "only pass+rush counted")
eq(doc["by_team"]["KC"]["G1"]["epa_per_play"], 0.30,
   "the 9.99 punt did not reach the average")

print("\n5. ⛔ FAIL-CLOSED — the part that matters most")
# (a) a missing column
bad = [{"game_id": "G1", "week": 1, "posteam": "BUF",
        "epa": 0.5, "pass": "1", "rush": "0"}]          # no defteam
doc, rep = run(bad)
eq(doc, None, "missing `defteam` -> writes NOTHING")
eq(rep["usable"], False, "reported unusable")
eq("defence" in str(rep.get("error", "")), True, "error NAMES the column")
eq("columns_available" in rep, True, "and lists what WAS there")

# (b) epa populated on too few plays -- 2 of 10 = 20%, bar is 80%
thin = [play("G1", 1, "BUF", "KC", 0.5 if i < 2 else None, "pass")
        for i in range(10)]
doc, rep = run(thin)
eq(doc, None, "epa thin -> writes NOTHING")
eq(rep["epa_populated_pct"], 20.0, "the coverage is REPORTED, not hidden")
eq("80" in str(rep.get("error", "")) or "20" in str(rep.get("error", "")),
   True, "error states the coverage against the bar")

# (c) just over the bar still writes -- the bar is a bar, not a mood
ok9 = [play("G1", 1, "BUF", "KC", 0.5 if i < 9 else None, "pass")
       for i in range(10)]
doc, rep = run(ok9)
eq(rep["epa_populated_pct"], 90.0, "90% coverage")
eq(doc is not None, True, "90% >= 80% -> writes")

print("\n6. the artifact says what it is (ledger rule 55)")
doc, _ = run([play("G1", 1, "BUF", "KC", 0.5, "pass")])
eq(doc["kind"], "DESCRIPTIVE", "kind is DESCRIPTIVE, not MODEL")
eq(doc["test"], "T48", "carries its test number")
eq("LOWER IS BETTER" in doc["note"], True, "the sign convention travels")

print()
if fails:
    print(f"🔴 {len(fails)} FAILED: {', '.join(fails)}")
    sys.exit(1)
print("✅ build_def_epa OK")
