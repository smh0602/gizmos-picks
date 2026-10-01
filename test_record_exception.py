#!/usr/bin/env python3
"""
🔴 verify_record's NAMED 9/25 EXCEPTION: THREE PICKS AND NOTHING WIDER.

`[Sam, 2026-10-01]` 9/25 BAL @ NYY was a doubleheader. Neither grader can
tell its games apart: collect's grader read game 2's box score for both
games' picks, verify_record reads game 1's. The published record STAYS
(9/25 = 29/45), so verify_record carries a named, dated exception for
exactly the three picks they disagree on, and must stay loud for
everything else. ⛔ Open for next season: the graders cannot tell
doubleheader games apart -- not fixed here, by Sam's decision.

THE CASE IS THE REAL ONE, PLANTED IN ITS OWN TREE: the published 9/24 and
9/25 cards and their stored box scores, graded by the REAL grader
(`collect.collect_record`), then checked by the REAL `verify_record.py`.
⚠️ Never the live tree: `verify_record` may rebuild `record.json`, and a
test asks the code, not today's data (CLAUDE.md, 2026-09-28).

# @vacuity 🔴 the three named picks are counted as published
#   file: verify_record.py
#   find:                 win = _x[0]               # counted as PUBLISHED, see above
#   with:                 pass
#
# @vacuity a fourth disagreement on 9/25 still fails its day
#   file: verify_record.py
#   find:        if (v["w"], v["n"]) != (recday.get(d, {}).get("w"), recday.get(d, {}).get("n"))]
#   with:        if False]
#
# @vacuity a disagreement on another day still fails the overall
#   file: verify_record.py
#   find:    (mine["w"], mine["n"]) == (REC["overall"]["w"], REC["overall"]["n"]),
#   with:    True,
#
# @vacuity the exception stays loud when one of its own picks changes
#   file: verify_record.py
#   find:        and all(dh_seen[k] == DH_EXCEPTION["picks"][k][1] for k in dh_seen),
#   with:        and True,
"""
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, copy_module, note, section, shown  # noqa: E402

TMP = tempfile.mkdtemp(prefix="dh-exception-")
tree = os.path.join(TMP, "tree")
os.makedirs(os.path.join(tree, "picks"))
os.makedirs(os.path.join(tree, "data", "latest"))
copy_module("collect", tree)
copy_module("verify_record", tree)
DAYS = ("2026-09-24", "2026-09-25")
for d in DAYS:
    shutil.copy(os.path.join(ROOT, "picks", d + ".json"), os.path.join(tree, "picks"))
    os.makedirs(os.path.join(tree, "data", d, "results"))
    shutil.copy(os.path.join(ROOT, "data", d, "results", "final.json.gz"),
                os.path.join(tree, "data", d, "results"))
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", LEAGUE="mlb", ODDS_API_KEY="",
           CFBD_API_KEY="")
g = subprocess.run([sys.executable, "-B", "-c",
                    "import collect; collect.collect_record()"],
                   cwd=tree, capture_output=True, text=True, timeout=600, env=ENV)
if g.returncode:
    print(shown(g.stdout[-1500:]), shown(g.stderr[-1500:]))
REC = json.load(open(os.path.join(tree, "data", "latest", "record.json"), encoding="utf-8"))
note("the real grader on the planted tree: %s" % {x["date"]: "%s/%s" % (x["w"], x["n"])
                                                  for x in REC.get("by_day") or []})


D25 = next((x for x in REC.get("by_day") or [] if x["date"] == "2026-09-25"), {})


def verify():
    p = subprocess.run([sys.executable, "-B", "verify_record.py"], cwd=tree,
                       capture_output=True, text=True, timeout=600, env=ENV)
    return p.returncode, p.stdout + p.stderr


def failed(out, name):
    return [ln.strip() for ln in out.splitlines() if ln.strip().startswith("FAIL " + name)]


RES = {d: os.path.join(tree, "data", d, "results", "final.json.gz") for d in DAYS}
ORIG = {d: open(p, "rb").read() for d, p in RES.items()}
STAT = {"batter_hits": "H", "batter_total_bases": "tb", "batter_home_runs": "hr",
        "batter_rbis": "rbi", "batter_hits_runs_rbis": "H"}


def edit(day, pid, fields, game=None):
    """Set one batter's stats in one stored box score (the first game he is
    in, or `game`) -- a planted disagreement with the record already built."""
    r = json.load(gzip.open(RES[day], "rt"))
    for gm in r["games"]:
        if game is not None and gm.get("gamePk") != game:
            continue
        for x in gm.get("batters") or []:
            if x["id"] == pid:
                x.update(fields)
                with gzip.open(RES[day], "wt") as fh:
                    json.dump(r, fh)
                return True
    return False


def flip(day):
    """Flip one hitter pick the exception does NOT name, outside the
    doubleheader: its stored stat moves to the other side of the line."""
    card = json.load(open(os.path.join(tree, "picks", day + ".json"), encoding="utf-8"))
    box = {}
    for gm in json.load(gzip.open(RES[day], "rt"))["games"]:
        for x in gm.get("batters") or []:
            box.setdefault(x["id"], x)
    for row in card["picks"]:
        x, mk = box.get(row.get("pid")), row.get("market")
        if row.get("kind") != "hitter" or row.get("game") == "BAL @ NYY" or not x or mk not in STAT:
            continue
        a = x["H"] + x["r"] + x["rbi"] if mk == "batter_hits_runs_rbis" else x[STAT[mk]]
        won = (a > row["line"]) if row["side"] == "over" else (a < row["line"])
        low = won == (row["side"] == "over")          # move it below the line
        new = ({"H": 0, "r": 0, "rbi": 0} if mk == "batter_hits_runs_rbis" else {STAT[mk]: 0}
               ) if low else {STAT[mk]: int(row["line"]) + 5}
        if edit(day, row["pid"], new):
            return row
    return None


def restore():
    for d, p in RES.items():
        open(p, "wb").write(ORIG[d])


# ══════════════════════════════════════════════════════════════════════
section("1. ✅ THE PUBLISHED 9/25 RECORD VERIFIES, THROUGH THE NAMED EXCEPTION")
rc, out = verify()
ck("🔴 verify_record is green on the real 9/24-9/25 cards and box scores",
   rc == 0 and "THE TRACK RECORD RECONCILES" in out
   and "EXCEPTION 2026-09-25 doubleheader, published 29/45" in out
   and "%s/%s" % (D25.get("w"), D25.get("n")) == "29/45",
   shown(out[-600:]))

section("2. 🔴 A FOURTH DISAGREEMENT ON 9/25 STILL FAILS")
r4 = flip("2026-09-25")
rc, out = verify()
ck("🔴 a planted disagreement on another 9/25 pick fails the day, by name",
   r4 is not None and rc == 1
   and any("2026-09-25" in ln for ln in failed(out, "every graded day reproduces")),
   "%s -> rc %s, %s" % (r4 and (r4.get("player"), r4["market"]), rc,
                        failed(out, "every graded day")))
restore()

section("3. 🔴 A DISAGREEMENT ON ANY OTHER DAY STILL FAILS")
r3 = flip("2026-09-24")
rc, out = verify()
ck("🔴 a planted disagreement on 9/24 fails the overall and names its day",
   r3 is not None and rc == 1 and failed(out, "overall reproduces")
   and any("2026-09-24" in ln for ln in failed(out, "every graded day reproduces")),
   "%s -> rc %s, %s" % (r3 and (r3.get("player"), r3["market"]), rc,
                        failed(out, "")[:3]))
restore()

section("4. 🔴 THE EXCEPTION IS LOUD WHEN ONE OF ITS OWN PICKS CHANGES")
# Jeremiah Jackson's game-1 total bases (4) is what this file re-grades his
# game-2 pick from. At 0 the re-grade agrees with the published win, the
# totals still reproduce -- and the exception no longer describes the data.
ok = edit("2026-09-25", 669236, {"tb": 0}, game=823491)
rc, out = verify()
ck("🔴 an exception pick that stops disagreeing fails the exception's own check",
   ok and rc == 1 and failed(out, "the named exception covers exactly its three picks")
   and not failed(out, "overall reproduces"),
   "rc %s, %s" % (rc, failed(out, "")[:3]))
restore()
