#!/usr/bin/env python3
"""T53 — NFL score by quarter, derived from play-by-play.

🔴 WHY A TEST AND NOT A LIVE RUN. The build container has no outbound
network, so this derivation cannot be exercised against the real
play-by-play from here. ⛔ That is exactly why the bars live in the code
and the report is written pass or fail — but it also means the DERIVATION
ITSELF has to be proved against constructed play-by-play, where the right
answer is known in advance.

⚠️ EVERY CASE BELOW IS A HAND-BUILT FEED. No network, no credits, no
nflverse.

✅ WHAT IS PINNED:
  1. A plain game derives the quarters the constructed feed implies.
  2. 🔴 THE ONE ASSUMPTION I COULD NOT VERIFY FROM HERE — whether the
     cumulative score is BEFORE or AFTER the play — FAILS LOUDLY rather
     than shipping quarters that are each short by a score.
  3. Overtime produces a fifth period, and the schedule's own `overtime`
     column is cross-checked against it. ⚠️ Two different files, one
     claim.
  4. A game whose quarters do not sum to its final is DROPPED, never
     shown, and counted.
  5. ⛔ MAX, NOT LAST ROW. Shuffling the feed must not change the answer.
  6. The home side is checked against the schedule — quarters attached to
     the wrong team is the run-line attribution bug in another sport.
  7. Missing columns write NOTHING.
  8. The join into build_schedule is fail-closed: no lines -> None, and
     the report counts what actually attached.
"""
import os
import random
import sys

os.environ.setdefault("LEAGUE", "nfl")
import nfl as N

fails = []


def eq(got, want, label):
    ok = got == want
    print(f"  {'ok  ' if ok else '🔴 FAIL'} {label:<58} {got!r}")
    if not ok:
        fails.append(f"{label} (got {got!r} want {want!r})")


def ck(cond, label, detail=""):
    print(f"  {'ok  ' if cond else '🔴 FAIL'} {label:<58} {detail}")
    if not cond:
        fails.append(label)


# ── a fake nflverse in one place ──────────────────────────────────────
SEASON = 2026


def sched_row(gid, home, away, hs, as_, ot=0):
    return {"season": str(SEASON), "game_id": gid, "home_team": home,
            "away_team": away, "home_score": hs, "away_score": as_,
            "overtime": ot}


def plays(gid, home, away, hq, aq):
    """A feed whose cumulative score is the score AFTER the play."""
    out, ch, ca = [], 0, 0
    for i, (h, a) in enumerate(zip(hq, aq), start=1):
        # two filler plays a quarter, then the quarter's points land
        for _ in range(2):
            out.append({"game_id": gid, "qtr": i, "home_team": home,
                        "away_team": away,
                        "total_home_score": ch, "total_away_score": ca})
        ch += h
        ca += a
        out.append({"game_id": gid, "qtr": i, "home_team": home,
                    "away_team": away,
                    "total_home_score": ch, "total_away_score": ca})
    return out


def run(schedule, pbp):
    """Drive build_line_scores with a constructed source."""
    def fake_rows(seen, tag, fname, log):
        return schedule if tag == "schedules" else pbp
    old = N._rows
    N._rows = fake_rows
    try:
        return N.build_line_scores(SEASON, seen={}, log=lambda *a: None)
    finally:
        N._rows = old


print("\n1. A PLAIN GAME DERIVES WHAT THE FEED IMPLIES")
S = [sched_row("G1", "KC", "BUF", 24, 20)]
P = plays("G1", "KC", "BUF", [7, 3, 7, 7], [0, 10, 3, 7])
doc, rep = run(S, P)
ck(doc is not None, "it produced a document", rep.get("error"))
if doc:
    eq(doc["by_game"]["G1"]["home_line"], [7, 3, 7, 7], "home quarters")
    eq(doc["by_game"]["G1"]["away_line"], [0, 10, 3, 7], "away quarters")
    eq(sum(doc["by_game"]["G1"]["home_line"]), 24, "  and they sum to the final")
eq(rep.get("coverage_pct"), 100.0, "coverage")
eq(rep.get("columns_used", {}).get("quarter"), "qtr", "the quarter column NAMED")

print("\n2. 🔴 THE ASSUMPTION I COULD NOT VERIFY FROM HERE FAILS LOUDLY")
print("   If the cumulative score is the score BEFORE the play, the last")
print("   score of the game is missing and the sum comes up short.")
BEFORE = []
for r in P:
    BEFORE.append(dict(r))
# strip the final row of each quarter -> the 'before the play' shape
BEFORE = [r for i, r in enumerate(BEFORE) if (i + 1) % 3 != 0]
doc2, rep2 = run(S, BEFORE)
ck(doc2 is None, "⛔ it writes NOTHING rather than shipping short quarters",
   rep2.get("error", "")[:60])
eq(rep2.get("dropped_sum_mismatch"), 1, "  the game is counted as dropped")
ck(bool(rep2.get("dropped_sum_examples")), "  and the report names it",
   str(rep2.get("dropped_sum_examples"))[:70])

print("\n3. OVERTIME — a fifth period, cross-checked against the SCHEDULE")
S3 = [sched_row("G2", "DAL", "PHI", 27, 24, ot=1)]
P3 = plays("G2", "DAL", "PHI", [7, 7, 3, 7, 3], [7, 3, 7, 7, 0])
doc3, rep3 = run(S3, P3)
ck(doc3 is not None, "it produced a document", rep3.get("error"))
if doc3:
    eq(len(doc3["by_game"]["G2"]["home_line"]), 5, "five periods")
    eq(doc3["by_game"]["G2"]["home_line"][4], 3, "the overtime period")
eq(rep3.get("overtime_agreement_pct"), 100.0, "overtime agreement")

print("   ⚠️ AND A DISAGREEMENT IS A FAILURE, NOT A SHRUG —")
print("   five periods on a game the schedule says was not overtime:")
S3b = [sched_row("G2", "DAL", "PHI", 27, 24, ot=0)]
doc3b, rep3b = run(S3b, P3)
eq(rep3b.get("overtime_agreement_pct"), 0.0, "agreement collapses")
ck(doc3b is None, "⛔ and it writes NOTHING", rep3b.get("error", "")[:60])

print("\n4. A GAME THAT DOES NOT RECONCILE IS DROPPED, THE REST SHIP")
S4 = [sched_row(f"H{i}", "KC", "BUF", 14, 14) for i in range(40)]
P4 = []
for i in range(40):
    hq, aq = [7, 0, 7, 0], [0, 7, 0, 7]
    P4 += plays(f"H{i}", "KC", "BUF", hq, aq)
# one game's schedule final disagrees with its own play-by-play
S4[7]["home_score"] = 21
doc4, rep4 = run(S4, P4)
ck(doc4 is not None, "39 good games still ship", rep4.get("error"))
eq(rep4.get("games_derived"), 39, "games derived")
eq(rep4.get("dropped_sum_mismatch"), 1, "the bad one is dropped")
eq(rep4.get("coverage_pct"), 97.5, "coverage 39/40")
ck(doc4 and "H7" not in doc4["by_game"],
   "⛔ the unreconciled game is ABSENT, not shown wrong")

print("   ...and below the 95% bar nothing ships at all:")
S5 = list(S4)
for i in (1, 2, 3):
    S5[i] = dict(S5[i], home_score=35)
doc5, rep5 = run(S5, P4)
eq(rep5.get("coverage_pct"), 90.0, "coverage 36/40")
ck(doc5 is None, "⛔ below the pre-registered 95% bar -> NOTHING",
   rep5.get("error", "")[:60])

print("\n5. ⛔ MAX, NOT LAST ROW — order must not change the answer")
shuf = list(P)
random.Random(7).shuffle(shuf)
doc6, _ = run(S, shuf)
ck(doc6 is not None and doc6["by_game"]["G1"]["home_line"] == [7, 3, 7, 7],
   "a shuffled feed derives the identical quarters",
   doc6 and doc6["by_game"]["G1"]["home_line"])

print("\n6. THE HOME SIDE IS CHECKED AGAINST THE SCHEDULE")
print("   Quarters attached to the wrong team is the run-line")
print("   attribution bug in another sport.")
S7 = [sched_row("G1", "BUF", "KC", 24, 20)]      # schedule says BUF at home
doc7, rep7 = run(S7, P)                          # play-by-play says KC
eq(rep7.get("dropped_home_side_mismatch"), 1, "the game is dropped")
ck(doc7 is None, "⛔ and nothing ships", rep7.get("error", "")[:50])

print("\n7. MISSING COLUMNS WRITE NOTHING")
NOQ = [{k: v for k, v in r.items() if k != "qtr"} for r in P]
doc8, rep8 = run(S, NOQ)
ck(doc8 is None, "no quarter column -> no document")
ck("quarter" in str(rep8.get("error")), "  and the report names it",
   str(rep8.get("error"))[:70])
ck(bool(rep8.get("columns_available")), "  and lists what WAS available",
   str(rep8.get("columns_available"))[:60])

print("\n8. THE JOIN IS FAIL-CLOSED AND COUNTS ITSELF")


def build_sched(lines):
    def fake_rows(seen, tag, fname, log):
        return [sched_row("G1", "KC", "BUF", 24, 20),
                sched_row("G9", "SF", "SEA", 17, 10)]
    old = N._rows
    N._rows = fake_rows
    try:
        return N.build_schedule(SEASON, seen={}, log=lambda *a: None,
                                lines=lines)
    finally:
        N._rows = old


d, r = build_sched(None)
ck(d is not None, "no lines at all -> the schedule STILL builds")
ck(all(g["home_line"] is None for g in d["games"]),
   "  every home_line is None, exactly today's behaviour")
eq(r.get("line_scores_joined"), 0, "  and the report says 0 joined")

d, r = build_sched({"G1": {"home_line": [7, 3, 7, 7],
                          "away_line": [0, 10, 3, 7]}})
g1 = next(g for g in d["games"] if g["id"] == "G1")
g9 = next(g for g in d["games"] if g["id"] == "G9")
eq(g1["home_line"], [7, 3, 7, 7], "the game with a line score gets it")
eq(g9["home_line"], None, "⛔ the one without stays None")
eq(r.get("line_scores_joined"), 1, "the report counts what ATTACHED")
eq(r.get("line_scores_offered"), 1, "  and what was offered")

print("   ⚠️ A DICT THAT MATCHES NOTHING IS A SILENT HOLE, so the two")
print("   numbers must be able to disagree:")
d, r = build_sched({"NOPE": {"home_line": [1], "away_line": [2]}})
eq(r.get("line_scores_offered"), 1, "offered")
eq(r.get("line_scores_joined"), 0, "joined — the gap is visible")

print()
if fails:
    print(f"🔴 {len(fails)} FAILURE(S)")
    for f in fails:
        print(f"   - {f}")
    sys.exit(1)
print("✅ T53 line scores: all checks passed")
