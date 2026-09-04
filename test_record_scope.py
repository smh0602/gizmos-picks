#!/usr/bin/env python3
"""ONE DIRECTORY, TWO SPORTS — and the Track Record is baseball's.

🔴 WHAT HAPPENED `[measured 2026-09-04]`. `picks/` holds MLB cards named
by date AND football cards named `fb-<league>-<date>.json`. Both football
cards carried `"date": "2026-09-03"` — a COLLEGE date that happens to
collide with a real MLB slate. `collect_record()` globs the whole
directory, so each football card fell through to the hand-built-card
branch and wrote **2026-09-03 into `skipped`, twice, described as "a
hand-built card graded in the ledger as TABLE A".**

⛔ THEN THE VERIFIER BELIEVED IT. `verify_record` took its exclusions from
`record.json`'s own `skipped` list, dropped a legitimately graded MLB day,
reconstructed **300/499 against a published 333/549**, and failed every
run. Two correct artifacts, one wrong list, and the site's own track
record could not be reproduced.

✅ TWO FIXES, AND THIS FILE PINS BOTH:
  1. `collect_record()` skips a card that names a league other than mlb —
     silently, because a football card is not a SKIPPED baseball card,
     it is not this function's sport at all.
  2. `verify_record` derives every exclusion itself. ⛔ A verifier that
     takes its exclusions from the artifact under test cannot catch a
     wrong exclusion; it can only be misled by one.

⚠️ Everything is constructed in a temp tree. No network, and nothing
asserts on the repo's real record.json — which this commit has not
rebuilt yet, and which a test may never require it to have.
"""
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.abspath(__file__))
fails = []


def ck(cond, label, detail=""):
    print(f"  {'ok  ' if cond else '🔴 FAIL'} {label:<58} {detail}")
    if not cond:
        fails.append(label)


def eq(got, want, label):
    ck(got == want, label, f"{got!r}")
    if got != want and fails and fails[-1] == label:
        fails[-1] = f"{label} (got {got!r} want {want!r})"


MLB_CARD = {
    "date": "2026-09-03", "kind": "gizmos-card",
    "picks": [
        {"pid": 1001, "market": "batter_hits", "side": "over", "line": 0.5,
         "kind": "hitter", "player": "A Batter"},
        {"pid": 2002, "market": "strikeouts", "side": "under", "line": 6.5,
         "kind": "pitcher", "pitcher": "A Pitcher"},
    ],
}
# ⚠️ The football card's shape is copied from the real one: its `kind` is
# a rule-55 basis string, NOT "gizmos-card", and its date is a football
# date that collides with an MLB slate. That collision IS the bug.
FB_CARD = {"date": "2026-09-03", "kind": "RECORD + MARKET",
           "league": "ncaaf", "picks": [{"market": "player_pass_tds"}]}
RESULTS = {
    "slate_date": "2026-09-03", "n_games": 1, "n_final": 1,
    "games": [{"id": "g1",
               "pitchers": [{"id": 2002, "started": True, "k": 5, "outs": 18}],
               "batters": [{"id": 1001, "H": 2, "tb": 3, "hr": 0, "r": 1,
                            "rbi": 1}]}],
}


def build_tree(root, extra_cards=()):
    os.makedirs(f"{root}/picks", exist_ok=True)
    os.makedirs(f"{root}/data/2026-09-03/results", exist_ok=True)
    os.makedirs(f"{root}/data/latest", exist_ok=True)
    json.dump(MLB_CARD, open(f"{root}/picks/2026-09-03.json", "w"))
    json.dump(FB_CARD, open(f"{root}/picks/fb-ncaaf-2026-09-03.json", "w"))
    json.dump(FB_CARD, open(f"{root}/picks/fb-ncaaf-latest.json", "w"))
    for name, doc in extra_cards:
        json.dump(doc, open(f"{root}/picks/{name}", "w"))
    with gzip.open(f"{root}/data/2026-09-03/results/final.json.gz", "wt") as fh:
        json.dump(RESULTS, fh)


print("\n1. 🔴 A FOOTBALL CARD IS NOT A SKIPPED BASEBALL CARD")
tmp = tempfile.mkdtemp()
cwd = os.getcwd()
try:
    build_tree(tmp)
    os.chdir(tmp)
    sys.path.insert(0, REPO)
    os.environ.setdefault("LEAGUE", "mlb")
    import collect as C
    C.collect_record()
    rec = json.load(open("data/latest/record.json"))
finally:
    os.chdir(cwd)
    shutil.rmtree(tmp, ignore_errors=True)

_skipped = rec.get("skipped", [])
_sdates = [x["date"] for x in _skipped]
_bydates = [x["date"] for x in rec.get("by_day", [])]
ck("2026-09-03" not in _sdates,
   "the football cards put NOTHING in `skipped`", str(_skipped))
ck("2026-09-03" in _bydates, "and the MLB day is graded", str(_bydates))
eq(rec["overall"]["n"], 2, "  both MLB picks counted")

print("\n2. ⛔ NO DATE IS BOTH GRADED AND SKIPPED")
print("   The invariant the live file violated. It is not about football;")
print("   it is about the record being able to describe itself.")
_both = sorted(set(_sdates) & set(_bydates))
ck(not _both, "graded dates and skipped dates are disjoint", str(_both))
eq(len(_sdates), len(set(_sdates)), "  and no date is skipped twice")

print("\n3. A REAL HAND-BUILT MLB CARD IS STILL SKIPPED, WITH ITS REASON")
print("   ⚠️ The fix must not swallow the case the branch exists for.")
tmp = tempfile.mkdtemp()
try:
    build_tree(tmp, extra_cards=[("2026-08-22.json",
                                  {"date": "2026-08-22", "kind": "MODEL",
                                   "picks": []})])
    os.chdir(tmp)
    C.collect_record()
    rec2 = json.load(open("data/latest/record.json"))
finally:
    os.chdir(cwd)
    shutil.rmtree(tmp, ignore_errors=True)
_s2 = {x["date"]: x["why"] for x in rec2.get("skipped", [])}
ck("2026-08-22" in _s2, "the hand-built card is named", str(sorted(_s2)))
ck("hand-built" in (_s2.get("2026-08-22") or ""),
   "  with the TABLE A reason", _s2.get("2026-08-22"))

print("\n4. 🔴 THE VERIFIER DOES NOT TAKE ITS EXCLUSIONS FROM THE FILE")
print("   ⛔ A wrong `skipped` list must not be able to hide a day.")


def run_verifier(mutate):
    """Build a tree, hand-write record.json, run verify_record.py on it."""
    t = tempfile.mkdtemp()
    try:
        build_tree(t)
        for f in ("verify_record.py",):
            shutil.copy(os.path.join(REPO, f), t)
        rec = {"built_at": "2026-09-04T00:00:00Z", "kind": "DESCRIPTIVE",
               "overall": {"w": 2, "n": 2, "pct": 100.0},
               "by_kind": {"pitcher": {"w": 1, "n": 1},
                           "hitter": {"w": 1, "n": 1}},
               "by_day": [{"date": "2026-09-03", "w": 2, "n": 2, "voids": 0}],
               "by_side": {"over": {"w": 1, "n": 1}, "under": {"w": 1, "n": 1}},
               "skipped": [], "days_graded": 1,
               "detail_file": "data/latest/record-detail.json.gz"}
        mutate(rec)
        json.dump(rec, open(f"{t}/data/latest/record.json", "w"))
        # `days` is a MAP of date -> rows, matching the real file. ⚠️ Got
        # this wrong first time and the verifier raised rather than
        # failing — a fixture in the wrong shape tests the fixture.
        det = {"built_at": rec["built_at"],
               "days": {"2026-09-03": [{"won": True}, {"won": True}]}}
        with gzip.open(f"{t}/data/latest/record-detail.json.gz", "wt") as fh:
            json.dump(det, fh)
        p = subprocess.run([sys.executable, "verify_record.py"], cwd=t,
                           capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr
    finally:
        shutil.rmtree(t, ignore_errors=True)


rc, out = run_verifier(lambda r: None)
ck(rc == 0, "a correct record.json passes", f"rc={rc}")

# THE BUG: the day is graded in by_day AND listed as skipped.
rc2, out2 = run_verifier(lambda r: r.__setitem__(
    "skipped", [{"date": "2026-09-03", "why": "hand-built card"},
                {"date": "2026-09-03", "why": "hand-built card"}]))
ck(rc2 == 0,
   "🔴 a WRONG `skipped` entry no longer hides the day", f"rc={rc2}")
ck("2/2" in out2 or "reproduces (2/2)" in out2,
   "  the verifier still re-grades both picks")

print("\n5. ⛔ AND IT IS NOT TOOTHLESS — a wrong total still fails")
rc3, out3 = run_verifier(lambda r: r["overall"].update({"w": 2, "n": 3}))
ck(rc3 != 0, "an inflated denominator is caught", f"rc={rc3}")
rc4, out4 = run_verifier(lambda r: r["by_day"].__setitem__(
    0, {"date": "2026-09-03", "w": 1, "n": 2, "voids": 0}))
ck(rc4 != 0, "a wrong day is caught", f"rc={rc4}")

print()
if fails:
    print(f"🔴 {len(fails)} FAILURE(S)")
    for f in fails:
        print(f"   - {f}")
    sys.exit(1)
print("✅ the Track Record is baseball's, and reproduces without trusting itself")
