#!/usr/bin/env python3
"""test_t60r.py — the backtest grades the PAST, at the approved bar.

🔴 THE THREE WAYS A BACKTEST LIES, and one check each:

1. **LOOKAHEAD.** A signal that can see the result it is predicting turns
   any rule into a winner. ⛔ Driven here on a fixture where a LATER game
   would flip the vote: if it flips, the filter is not holding.
2. **THE BAR DRIFTING FROM THE SPEC.** Sam approved 57.4% / p<0.01 /
   effective n ≥ 1,000 in `research/t60r_spec.md`. ⛔ The constants in
   `t60r.py` are read back FROM that file, so the code cannot quietly
   disagree with the pre-registration it claims to implement.
3. **GRADING THE WRONG SIDE.** A push is a void, and a spread whose sign
   fights the moneyline is a void — never a loss, never a win.

⚠️ `verdict()` is driven on fabricated rows, deliberately: the point is
that the BAR behaves, and a fabricated 60% over 1,200 clean rows is the
only way to see PASS before the real data can reach the floor.

# @vacuity the lookahead filter must really filter
#   file: t60r.py
#   find:     past = [x for x in past_all if kick(x) < k]
#   with:     past = list(past_all)
"""
import gzip
import json
import os
import re
import shutil
import tempfile

from tcheck import ck, note

import t60r

ROOT = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(ROOT, "research", "t60r_spec.md")

# ══════════════════════════════════════════════════════════════════════
# 1. THE CODE'S BAR IS THE SPEC'S BAR
# ══════════════════════════════════════════════════════════════════════
_spec = open(SPEC, encoding="utf-8").read()
ck("🔴🔴 the approved bar in the spec is the bar in the code",
   ("57.4%" in _spec and abs(t60r.BAR_RATE - 0.574) < 1e-9
    and t60r.BAR_P == 0.01 and t60r.MIN_EFF_N == 1000
    and re.search(r"effective n ≥ 1,000", _spec) is not None),
   "⛔ the code must implement the pre-registration it names. "
   "code: rate=%s p=%s n=%s" % (t60r.BAR_RATE, t60r.BAR_P, t60r.MIN_EFF_N))
ck("🔴 ...and the approved thresholds too (section 2)",
   (t60r.GAP_POINTS == 3.0 and t60r.PLAY_AT == 2 and t60r.OUT_GAP == 2
    and t60r.VS_POS == ("QB", "RB", "WR", "TE") and t60r.H2H_DAYS == 365),
   "⛔ a threshold that drifts from the approved rule is a different test")
ck("⛔ ...and the spec is APPROVED, not still proposed",
   "APPROVED BY SAM" in _spec.split("\n")[2],
   "🔴 code for an unapproved pre-registration is the thing rule 13 "
   "forbids; test_prereg_gate.py is the check, this is its echo")


# ══════════════════════════════════════════════════════════════════════
# 2. LOOKAHEAD — the fixture is built so a LATER game would flip §4
# ══════════════════════════════════════════════════════════════════════
def game(gid, d, home, away, hs=None, as_=None, spread=None, total=None,
         ml_h=None, ml_a=None, week=1):
    return {"id": gid, "start": d + "T17:00Z", "home": home, "away": away,
            "home_score": hs, "away_score": as_, "final": hs is not None,
            "closing_spread": spread, "closing_total": total,
            "closing_ml_home": ml_h, "closing_ml_away": ml_a,
            "week": week, "home_class": "fbs", "away_class": "fbs"}


class Tree:
    """A scratch repo root holding only what t60r reads."""

    def __init__(self, games, players=None):
        self.d = tempfile.mkdtemp()
        latest = os.path.join(self.d, "data", "nfl", "latest")
        os.makedirs(latest)
        os.makedirs(os.path.join(self.d, "data", "ncaaf", "latest"))
        with gzip.open(os.path.join(latest, "schedule-2025.json.gz"), "wt",
                       encoding="utf-8") as f:
            json.dump({"season": 2025, "games": games}, f)
        with gzip.open(os.path.join(latest, "players-2025.json.gz"), "wt",
                       encoding="utf-8") as f:
            json.dump({"season": 2025, "players": players or {}}, f)

    def __enter__(self):
        self.old = t60r.ROOT
        t60r.ROOT = self.d
        return self

    def __exit__(self, *a):
        t60r.ROOT = self.old
        shutil.rmtree(self.d, ignore_errors=True)


# A@H on 2025-10-01 priced at home -7. Both sides have two earlier games;
# H has been poor and A strong, so §4 says the visitor. ⛔ THE TWO GAMES
# AFTER IT are lopsided the other way — a leaky filter would see them.
BASE = [
    game("p1", "2025-09-01", "H", "X", 0, 30),
    game("p2", "2025-09-08", "H", "Y", 0, 30),
    game("p3", "2025-09-01", "A", "X", 30, 0),
    game("p4", "2025-09-08", "A", "Y", 30, 0),
    # ⚠️ §2 needs a meeting inside 365 days, or one signal alone can never
    #    reach the net of 2 the rule requires. A won this one 40-0.
    game("p5", "2025-09-15", "A", "H", 40, 0),
    game("t1", "2025-10-01", "H", "A", 10, 20, spread=7.0, total=40.0,
         ml_h=-300, ml_a=250, week=5),
    # ⛔ AFTER the game under test, and lopsided the other way: four H
    #    blowouts and a REMATCH H wins 60-0. A leaky filter flips both §4
    #    and §2 to the home side; the correct one never sees them.
    game("f1", "2025-10-08", "H", "X", 60, 0, week=6),
    game("f2", "2025-10-15", "H", "Y", 60, 0, week=7),
    game("f3", "2025-10-22", "H", "A", 60, 0, week=8),
    game("f4", "2025-10-29", "H", "X", 60, 0, week=9),
]

with Tree(BASE) as _t:
    rows, skipped, cast = t60r.rows_for("nfl")
    _played = [r for r in rows if r["game_id"] == "t1" and r["market"] == "spread"]
    ck("🔴🔴 a game later than kickoff cannot reach the vote",
       len(_played) == 1 and _played[0]["side"] == "away",
       "⛔ §4 reads the last 4 finals BEFORE kickoff: H had been beaten "
       "30-0 twice, A had won 30-0 twice, so the visitor is the side. If "
       "this says 'home', the two 60-0 blowouts AFTER the game leaked in. "
       "got %r" % (_played,))
    ck("⛔ ...and the row is graded against the real result",
       _played and _played[0]["won"] is True,
       "H lost 10-20 as a 7-point favourite, so the away side covered. "
       "got won=%r" % (_played[0]["won"] if _played else None))

# ══════════════════════════════════════════════════════════════════════
# 3. VOIDS — a push and a sign conflict are never graded
# ══════════════════════════════════════════════════════════════════════
_push = [g for g in BASE if g["id"] != "t1"] + [
    game("t1", "2025-10-01", "H", "A", 20, 13, spread=7.0, total=33.0,
         ml_h=-300, ml_a=250, week=5)]
with Tree(_push) as _t:
    rows, skipped, _c = t60r.rows_for("nfl")
    ck("🔴 a spread that lands exactly on the number is a PUSH, not a loss",
       not [r for r in rows if r["market"] == "spread"] and skipped["push"] >= 1,
       "⛔ CLAUDE.md: voids stay out of every denominator. rows=%r "
       "skipped=%r" % (rows, dict(skipped)))

_conflict = [g for g in BASE if g["id"] != "t1"] + [
    game("t1", "2025-10-01", "H", "A", 10, 20, spread=7.0, total=40.0,
         ml_h=250, ml_a=-300, week=5)]      # spread says home, ML says away
with Tree(_conflict) as _t:
    rows, skipped, _c = t60r.rows_for("nfl")
    ck("🔴 a spread whose sign fights the moneyline is VOID and counted",
       not rows and skipped["spread sign conflicts with the moneyline"] == 1,
       "⛔ CLAUDE.md, run_line: the moneyline is the authority. A row "
       "oriented the wrong way is a bet on the other team. skipped=%r"
       % dict(skipped))

# ══════════════════════════════════════════════════════════════════════
# 4. THE BAR BEHAVES — on fabricated rows, with the real verdict()
# ══════════════════════════════════════════════════════════════════════
def fake(n, rate, start=0):
    """n rows in n DIFFERENT games, so clustering cannot shrink them."""
    wins = int(round(n * rate))
    return [{"game_id": "g%d" % (start + i), "won": i < wins,
             "state": "graded", "season": 2025, "league": "nfl",
             "market": "spread"} for i in range(n)]


_small = t60r.verdict(fake(300, 0.70))
ck("⛔ under the n floor it is NOT YET MEASURABLE, whatever the rate",
   _small["verdict"] == "NOT YET MEASURABLE",
   "🔴 70%% on 300 rows is not a pass — that is the three-state rule "
   "T37 and T60 both use. got %r" % _small["verdict"])
_pass = t60r.verdict(fake(1200, 0.60))
ck("✅ a big edge over the floor PASSES", _pass["verdict"] == "PASS",
   "got %r — %s" % (_pass["verdict"], _pass.get("why")))
_fail = t60r.verdict(fake(1200, 0.53))
ck("⛔ break-even-ish over the floor FAILS", _fail["verdict"] == "FAIL",
   "53%% is under the 57.4%% bar. got %r" % _fail["verdict"])
_edge = t60r.verdict(fake(1200, 0.574))
ck("⚠️ exactly at the bar, the p-value still has to clear 0.01",
   _edge["verdict"] in ("PASS", "FAIL") and _edge["p_value"] is not None,
   "⛔ the bar is a rate AND a p-value; a rate alone would pass on luck. "
   "got %r p=%s" % (_edge["verdict"], _edge.get("p_value")))
ck("🔴 no p-value is ever computed on the raw row count",
   _pass["p_value_on_raw_n"] is None,
   "⛔ a pre-registration condition carried over from T60")

# ══════════════════════════════════════════════════════════════════════
# 5. SECTION 3a — three numbers, and the verdict is the COMBINED one
# ══════════════════════════════════════════════════════════════════════
_rep_rows = fake(20, 0.5) + [dict(r, season=2026) for r in fake(20, 0.5, 100)]
_by = {str(s): t60r.verdict([r for r in _rep_rows if r["season"] == s])
       for s in t60r.SEASONS}
ck("🔴 2025 and 2026 are each reported on their own",
   set(_by) == {"2025", "2026"} and all(v["n"] == 20 for v in _by.values()),
   "⛔ spec 3a: three numbers, always. got %r"
   % {k: v["n"] for k, v in _by.items()})
ck("⛔ ...and neither season's n is the combined n",
   t60r.verdict(_rep_rows)["n"] == 40,
   "🔴 the verdict is the combined number and only that")
note("⚠️ THIS FILE DOES NOT CLAIM THE RULE IS ANY GOOD. It claims the "
     "rule that was approved is the rule that runs, on data from before "
     "kickoff, graded the way the spec says. Whether the signals beat "
     "the price is what the report answers, and it is not a test.")

# ══════════════════════════════════════════════════════════════════════
# 6. A WORKFLOW THAT SPENDS CFBD QUOTA IS IN THE BUDGET
# ══════════════════════════════════════════════════════════════════════
# 🔴 CLAUDE.md: "The budget is DERIVED, not written down." `cfbd_budget`
#    read collect.yml and nothing else, which was complete until this
#    file added a second caller. ⛔ The class, not this one script: any
#    root module that talks to the CFBD host must be counted.
import cfbd_budget  # noqa: E402

_callers = {os.path.basename(p) for p in
            __import__("glob").glob(os.path.join(ROOT, "*.py"))
            if cfbd_budget.CFBD_HOST in open(p, encoding="utf-8").read()}
_counted = set(cfbd_budget.cfbd_scripts()) | {"cfb.py", "cfbd_budget.py",
                                              "cfbd_watch.py"}
ck("🔴 every module that calls CFBD is accounted for in the budget",
   _callers <= _counted,
   "⛔ uncounted caller(s): %r — a script that spends quota with no "
   "budget line is how the quota runs out unannounced"
   % sorted(_callers - _counted))
ck("⛔ ...and t60r's per-run call count is READ, not typed",
   cfbd_budget.cfbd_scripts().get("t60r.py") == len(t60r.SEASONS),
   "🔴 one call per season, derived from t60r.SEASONS=%r" % (t60r.SEASONS,))

_wf = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(_wf, ".github", "workflows"))
    with open(os.path.join(_wf, ".github/workflows/t60r.yml"), "w",
              encoding="utf-8") as f:
        f.write('on:\n  schedule:\n    - cron: "17 9 * * 2"\n'
                'jobs:\n  g:\n    steps:\n      - run: python t60r.py lines\n')
    for m in ("t60r.py", "cfb.py"):
        shutil.copy(os.path.join(ROOT, m), os.path.join(_wf, m))
    _got = cfbd_budget.other_workflow_calls(_wf)
    ck("🔴🔴 a weekly cron running `t60r.py lines` lands in the budget",
       sum(_got.values()) == len(t60r.SEASONS),
       "⛔ one fire a week x %d season(s). got %r"
       % (len(t60r.SEASONS), dict(_got)))
finally:
    shutil.rmtree(_wf, ignore_errors=True)
note("⚠️ `docs/upload/t60r.yml` is NOT in `.github/workflows/` until Sam "
     "uploads it by hand, so the live budget counts 0 for it until then — "
     "correct, not a gap: an unuploaded workflow spends nothing.")
