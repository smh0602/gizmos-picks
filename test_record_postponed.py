#!/usr/bin/env python3
"""A POSTPONED GAME MUST NOT HOLD ITS WHOLE DAY OUT OF THE TRACK RECORD.

🔴 WHAT HAPPENED `[research/mlb_calibration_audit.md §4, Proposal A]`.
TOR @ BAL was Postponed on 2026-09-22. `collect_record()` graded a day
only when every game was `Final`, so the day read "15/16 games final --
not settled" on every rebuild, forever. The card's other picks never
reached the record, and every check stayed green because the record file
itself kept being rebuilt on time.

✅ THE FIX: Postponed and Cancelled games are SETTLED-VOID. The other
games grade; the postponed game's picks are voids (a refund at the book).
✅ THE GUARDS, both pinned here:
  1. a fixture day with one postponed game grades the other game and
     voids the postponed game's picks -- in the builder AND the verifier;
  2. the CLASS: any MLB machine card more than 3 days old and missing from
     the record turns the watchdog red, whatever held it back.

⚠️ Everything runs in a temp tree. Nothing reads or writes the repo's own
record.json.

# @vacuity the builder counting only Final games must hold the day back
#   file: collect.py
#   find: return n_final + n_void == len(games), n_void
#   with: return n_final == len(games), n_void
# @vacuity the verifier counting only Final games must disagree
#   file: verify_record.py
#   find: if n_g and n_f + n_v == n_g:
#   with: if n_g and n_f == n_g:
# @vacuity a watchdog that never reports a late card must go red
#   file: watchdog.py
#   find: if age > UNGRADED_AFTER_DAYS and day not in graded:
#   with: if False:
"""
import ast
import datetime
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, eq

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
os.environ.setdefault("LEAGUE", "mlb")

DAY = "2026-09-22"
CARD = {
    "date": DAY, "kind": "gizmos-card",
    "picks": [
        # played game: a pitcher and a hitter, both gradeable
        {"pid": 11, "market": "strikeouts", "side": "over", "line": 5.5,
         "kind": "pitcher", "pitcher": "Final Pitcher", "game": "LAA @ ATH"},
        {"pid": 12, "market": "batter_hits", "side": "under", "line": 0.5,
         "kind": "hitter", "player": "Final Hitter", "game": "LAA @ ATH"},
        # the postponed game: both must VOID, neither may count
        {"pid": 21, "market": "strikeouts", "side": "under", "line": 6.5,
         "kind": "pitcher", "pitcher": "Rained Out", "game": "TOR @ BAL"},
        {"pid": 22, "market": "batter_rbis", "side": "under", "line": 0.5,
         "kind": "hitter", "player": "Also Rained Out", "game": "TOR @ BAL"},
    ],
}


def results(second_state):
    """The stored results file, in the collector's real shape: a postponed
    game is listed with its state and no players."""
    games = [
        {"gamePk": 1, "state": "Final", "away": "Los Angeles Angels",
         "home": "Athletics",
         "pitchers": [{"id": 11, "started": True, "k": 7, "outs": 18}],
         "batters": [{"id": 12, "H": 1, "tb": 1, "hr": 0, "r": 0, "rbi": 0}]},
        {"gamePk": 2, "state": second_state, "away": "Toronto Blue Jays",
         "home": "Baltimore Orioles", "pitchers": [], "batters": []},
    ]
    return {"slate_date": DAY, "n_games": 2,
            "n_final": sum(1 for g in games if g["state"] == "Final"),
            "games": games}


def build(root, second_state):
    for d in ("picks", f"data/{DAY}/results", "data/latest"):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    json.dump(CARD, open(f"{root}/picks/{DAY}.json", "w"))
    with gzip.open(f"{root}/data/{DAY}/results/final.json.gz", "wt") as fh:
        json.dump(results(second_state), fh)


def grade(second_state):
    """Run the real builder, then the real verifier, in a temp tree."""
    import collect as C
    t, cwd = tempfile.mkdtemp(), os.getcwd()
    try:
        build(t, second_state)
        os.chdir(t)
        C.collect_record()
        rec = json.load(open("data/latest/record.json"))
        det = json.load(gzip.open("data/latest/record-detail.json.gz", "rt"))
        shutil.copy(os.path.join(REPO, "verify_record.py"), t)
        p = subprocess.run([sys.executable, "verify_record.py"], cwd=t,
                           capture_output=True, text=True)
        return rec, det, p.returncode, p.stdout + p.stderr
    finally:
        os.chdir(cwd)
        shutil.rmtree(t, ignore_errors=True)


for state in ("Postponed", "Cancelled"):
    print(f"\n1. 🔴 ONE {state.upper()} GAME: THE DAY GRADES, ITS PICKS VOID")
    rec, det, rc, out = grade(state)
    days = {d["date"]: d for d in rec.get("by_day", [])}
    ck(DAY in days,
       f"🔴 the day with a {state} game is GRADED, not held back",
       "⛔ this is the 2026-09-22 bug: skipped=%s" % rec.get("skipped"))
    d = days.get(DAY, {})
    eq((d.get("w"), d.get("n")), (1, 2),
       "  the played game's two picks grade (over 5.5 K on 7 won; "
       "under 0.5 hits on 1 lost)")
    eq(d.get("voids"), 2, "  both picks on the postponed game are VOIDS")
    rows = {r["player"]: r for r in det["days"].get(DAY, [])}
    ck(all(rows.get(n, {}).get("void") is True and rows[n]["won"] is None
           for n in ("Rained Out", "Also Rained Out")),
       "  ...and each one is recorded as a void, with won=None",
       str({n: rows.get(n) for n in ("Rained Out", "Also Rained Out")}))
    ck(any(state in g for g in d.get("void_games") or []),
       "  the day names the game that voided", str(d.get("void_games")))
    eq(rec["overall"]["n"], 2, "  ⛔ no void enters the denominator")
    ck(rc == 0, "✅ verify_record.py re-grades the same day and agrees",
       out[-600:])

print("\n2. ⛔ STILL STRICT: A GAME THAT HAS NOT FINISHED HOLDS THE DAY")
for state in ("Scheduled", "In Progress", "Suspended"):
    rec, _det, rc, out = grade(state)
    ck(DAY not in {d["date"] for d in rec.get("by_day", [])},
       f"  a {state} game keeps the day ungraded",
       "🔴 an unfinished game is not a void; grading now would call its "
       "picks refunds before they are played")
    ck(rc == 0 and "NOT GRADED" in out,
       f"  ...and the verifier agrees it is not graded ({state})", out[-400:])

print("\n3. ⛔ THE VERIFIER'S COPY OF THE RULE IS THE BUILDER'S")
import collect as C  # noqa: E402
_tree = ast.parse(open(os.path.join(REPO, "verify_record.py"),
                       encoding="utf-8").read())
_vr = None
for node in _tree.body:
    if (isinstance(node, ast.Assign)
            and any(getattr(t, "id", None) == "VOID_STATES" for t in node.targets)):
        _vr = set(ast.literal_eval(node.value.args[0]))
eq(_vr, set(C.VOID_STATES),
   "🔴 verify_record.VOID_STATES == collect.VOID_STATES (two copies by "
   "design; they must never drift)")

print("\n4. 🔴 THE CLASS: A CARD OLDER THAN 3 DAYS AND UNGRADED IS RED")
import watchdog as W  # noqa: E402
UTC = datetime.timezone.utc


def watch(cards, by_day, now, skipped=()):
    t, old = tempfile.mkdtemp(), W.ROOT
    try:
        os.makedirs(os.path.join(t, "picks"))
        os.makedirs(os.path.join(t, "data", "latest"))
        for name, doc in cards:
            json.dump(doc, open(os.path.join(t, "picks", name), "w"))
        json.dump({"by_day": [{"date": x, "w": 0, "n": 0} for x in by_day],
                   "skipped": [{"date": a, "why": b} for a, b in skipped]},
                  open(os.path.join(t, "data", "latest", "record.json"), "w"))
        W.ROOT = t
        rep = W.Report()
        W.check_record_ungraded(rep, now)
        return [i for i in rep.items if i["key"] == "record:mlb:ungraded"]
    finally:
        W.ROOT = old
        shutil.rmtree(t, ignore_errors=True)


NOW = datetime.datetime(2026, 9, 26, 15, 0, tzinfo=UTC)     # 11am ET 09-26
mcard = ("2026-09-22.json", {"date": "2026-09-22", "kind": "gizmos-card",
                             "picks": []})
f = watch([mcard], [], NOW, skipped=[("2026-09-22", "15/16 games final -- not settled")])
ck(bool(f) and f[0]["severity"] == "BROKEN",
   "🔴 a 4-day-old card missing from the record turns the watchdog RED",
   "⛔ 2026-09-22 sat out of the record with every check green. Got %s" % f)
ck(bool(f) and "not settled" in f[0]["why"] and "2026-09-22" in f[0]["why"],
   "  ...and the finding names the day and why it was skipped",
   f and f[0]["why"])
ck(bool(f) and f[0]["repair"] == "record",
   "  ...and offers the free `record` rebuild (escalates if it cannot fix it)")
ck(not watch([mcard], ["2026-09-22"], NOW),
   "✅ the same card, graded, is silent")
ck(not watch([mcard], [], datetime.datetime(2026, 9, 25, 15, 0, tzinfo=UTC)),
   "⏳ exactly 3 days old is not yet late")
ck(not watch([("2026-08-22.json", {"date": "2026-08-22", "kind": "MODEL"})],
             [], NOW),
   "⛔ the hand-built 2026-08-22 card (graded in the ledger) is silent")
ck(not watch([("fb-nfl-2026-09-01.json",
               {"date": "2026-09-01", "kind": "gizmos-card", "league": "nfl"})],
             [], NOW),
   "⛔ a football card is not an MLB card")
ck(W.check_record_ungraded in W.CHECKS,
   "🔴 the check is in the watchdog's run list, so it actually runs")
