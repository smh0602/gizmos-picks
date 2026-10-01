#!/usr/bin/env python3
"""
🔴 THE MLB CARD HOLDS ONLY GAMES ON ITS OWN ET DATE (ledger rule 101).

`[2026-10-01]` 10/01 had ONE game (PHI @ ATL) and the rolling board already
held the next round. `picks/2026-10-01.json` carried 17 of its 29 picks and
2 of its top 10 on 10/03 games, and the watchdog reported day:mlb:picks and
day:mlb:top10 BROKEN. card_fb.py has filtered this since 09-04; card.py
never did. ✅ One filter (`card.on_day`) now runs before the pairs, the top
10, the parlays and the board are built, and the card says what it held back.

THE CASE IS PLANTED, NEVER BORROWED FROM TODAY'S BOARD (rule 67): a
pitcher-props snapshot with three games between six starters from the
stored pull, ONE on the card's day and two on later days, the clock pinned
just after the pull, then the REAL board builder (`collect_props_board`) and
the REAL card (`card.main(dry=True)`) in an isolated tree.
⚠️ The day is judged by the WATCHDOG's ET date (`watchdog._etd`), never by
card.py's own, and every dated list is DISCOVERED (`watchdog._dated_lists`),
so a list added later is covered the day it ships.

⛔ WHAT A PASS DOES NOT CLAIM: that `picks/2026-10-01.json` is right. It is
published and stays as it was; editing a published pick is Sam's call.

# @vacuity ⛔ the card keeps only its own day's rows
#   file: card.py
#   find:     return ([x for x in rows if et_date(x["commence"]) == day],
#   with:     return (list(rows),
#
# @vacuity the top 10 (and the pairs) are built from the filtered pool
#   file: card.py
#   find:     plays_all, _ = on_day(plays_all, today)
#   with:     _ = on_day(plays_all, today)
#
# @vacuity the board's pitcher seats are filled from the filtered rows
#   file: card.py
#   find:     plays, _off_p = on_day(plays, today)
#   with:     _off_p = on_day(plays, today)[1]
#
# @vacuity the card says HOW MANY rows wait for their own day
#   file: card.py
#   find:                      + (f": {len(off_day)} priced row(s) for {', '.join(off_dates)} "
#   with:                      + (f": some priced row(s) for {', '.join(off_dates)} "
#
# @vacuity the card records the held-back count for the page
#   file: card.py
#   find:         "n_off_slate_day": len(off_day),
#   with:         "n_off_slate_day": 0,
"""
import datetime
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

import collect as CM  # noqa: E402
import watchdog as W  # noqa: E402

TMP = tempfile.mkdtemp(prefix="single-day-")

DRIVER = r"""
import datetime as _d, contextlib, gzip, io, json, os, sys
root = os.path.dirname(os.path.abspath(__file__)); os.chdir(root); sys.path.insert(0, root)
FIX = _d.datetime.strptime(sys.argv[2], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_d.timezone.utc)
import collect, card
collect.now = lambda: FIX
class _DT(_d.datetime):
    @classmethod
    def now(cls, tz=None):
        return FIX if tz else FIX.replace(tzinfo=None)
card.datetime = _DT
with contextlib.redirect_stdout(io.StringIO()):
    collect.collect_props_board()
    doc = card.main(dry=True)
board = json.load(gzip.open("data/latest/props.json.gz", "rt"))
json.dump({"board": board, "card": doc}, open(sys.argv[1], "w"), sort_keys=True)
"""


def _mkt(key, who, line, over, under):
    return {"key": key, "outcomes": [
        {"name": "Over", "description": who, "point": line, "price": over},
        {"name": "Under", "description": who, "point": line, "price": under}]}


# ── THE PLANTED TREE ──────────────────────────────────────────────────
tree = os.path.join(TMP, "tree")
os.makedirs(os.path.join(tree, "data"))
copy_module("card", tree)
shutil.copytree(os.path.join(ROOT, "data", "latest"), os.path.join(tree, "data", "latest"))
open(os.path.join(tree, "driver.py"), "w").write(DRIVER)
PD = json.load(gzip.open(os.path.join(tree, "data", "latest", "pitchers.json.gz"), "rt"))

# Six starters from six different teams, each name unique in the model pool
# (the same draw as test_mlb_tables (c1), so `resolve()` never refuses one).
mp = CM.model_pitchers(PD["players"])
names = {}
for v in mp.values():
    names[CM.norm_name(v["name"])] = names.get(CM.norm_name(v["name"]), 0) + 1
by_team = {}
for _pid, v in sorted(mp.items(), key=lambda kv: (-sum(1 for r in kv[1].get("g") or []
                                                      if r.get("gs")), kv[0])):
    starts = sum(1 for r in v.get("g") or [] if r.get("gs"))
    if (starts >= 5 and v.get("team") and v["team"] not in by_team
            and names[CM.norm_name(v["name"])] == 1):
        by_team[v["team"]] = v
six = list(by_team.values())[:6]

pull_at = datetime.datetime.strptime(PD["pulled_at"], "%Y-%m-%dT%H:%M:%SZ")
FIX = (pull_at + datetime.timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
# 🔴 ONE game on the card's day, the next round two and three days later --
#    the 10/01 shape: a thin day with the board already rolled forward.
KO = [(pull_at + datetime.timedelta(days=d)).strftime("%Y-%m-%dT23:05:00Z")
      for d in (1, 3, 4)]
DAY = W._etd(KO[0])
events = []
for gi in range(3):
    aw, hm = six[2 * gi], six[2 * gi + 1]
    events.append({"id": "planted-%d" % gi, "commence_time": KO[gi],
                   "away_team": aw["team"], "home_team": hm["team"],
                   "bookmakers": [
                       {"key": bk, "markets": [
                           m for q in (aw, hm) for m in (
                               _mkt("pitcher_strikeouts", q["name"], 5.5, -115 + dx, -105 - dx),
                               _mkt("pitcher_outs", q["name"], 16.5, -110 + dx, -110 - dx))]}
                       for bk, dx in (("draftkings", 0), ("fanduel", 5))]})
snap = os.path.join(tree, "data", FIX[:10], "props-pitcher")
os.makedirs(snap)
with gzip.open(os.path.join(snap, FIX[11:13] + FIX[14:16] + ".json.gz"), "wt") as fh:
    json.dump({"pulled_at": FIX, "n_events": len(events), "events": events}, fh)

out = os.path.join(TMP, "out.json")
p = subprocess.run([sys.executable, "-B", "driver.py", out, FIX], cwd=tree,
                   capture_output=True, text=True, timeout=600,
                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
if p.returncode:
    print(shown(p.stdout[-2000:]), shown(p.stderr[-2000:]))
res = json.load(open(out, encoding="utf-8")) if not p.returncode else {}
B, C = res.get("board") or {}, res.get("card") or {}
TODAY_GAMES = {g["id"] for g in B.get("games") or [] if W._etd(g.get("commence")) == DAY}
LATER = sorted({W._etd(g.get("commence")) for g in B.get("games") or []} - {DAY})
note("planted: %d game(s) on %s %s, later days %s; card dated %s, %d picks, %d top 10"
     % (len(TODAY_GAMES), DAY, sorted(TODAY_GAMES), LATER, C.get("date"),
        len(C.get("picks") or []), len(C.get("top10") or [])))
note("the board holds %d game(s); the case needs one on the card's day and "
     "rows on later days, or the checks below pass blind" % len(B.get("games") or []))


def on_card_day(rows):
    """Every row's game is today's one game, on the card's own ET date."""
    return all(r.get("game_id") in TODAY_GAMES and W._etd(r.get("commence")) == DAY
               for r in rows)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 A ONE-GAME DAY: THE CARD CARRIES ONLY THAT GAME'S ROWS")
picks = C.get("picks") or []
ck("🔴 every pick is the one game on the card's day, and there are picks",
   C.get("date") == DAY and len(TODAY_GAMES) == 1 and len(LATER) == 2
   and picks and on_card_day(picks),
   "date %s, %d picks on %s"
   % (C.get("date"), len(picks),
      sorted({(r.get("game_id"), W._etd(r.get("commence"))) for r in picks})))

section("2. 🔴 THE TOP 10 LIKEWISE")
t10 = C.get("top10") or []
ck("🔴 every top-10 row is the one game on the card's day, and there is a top 10",
   C.get("date") == DAY and t10 and on_card_day(t10),
   "%d rows on %s" % (len(t10), sorted({W._etd(r.get("commence")) for r in t10})))
ck("...and a one-game day builds no pair: a pair needs two games, and the "
   "other games are on other days",
   C.get("date") == DAY and not (C.get("pairs") or []),
   "%d pair(s)" % len(C.get("pairs") or []))

section("3. 🔴 EVERY DATED LIST, DISCOVERED -- NOT JUST THE TWO THAT BROKE")
lists = W._dated_lists(C)
leak = {k: sorted({W._etd(r.get("commence")) for r in v
                   if isinstance(r, dict) and W._etd(r.get("commence")) != DAY})
        for k, v in lists.items()}
leak = {k: v for k, v in leak.items() if v}
ck("🔴 no list on the card carries a row from another day",
   C.get("date") == DAY and "picks" in lists and not leak,
   "lists %s; off-day rows in %s" % (sorted(lists), leak))

section("4. ✅ A THIN DAY SAYS SO")
n_off = C.get("n_off_slate_day")
ck("the card records how many priced rows wait for their own day, and which days",
   isinstance(n_off, int) and n_off > 0 and C.get("off_slate_dates") == LATER
   and C.get("single_day") is True and C.get("slate_date") == DAY,
   "n_off_slate_day=%r off_slate_dates=%r" % (n_off, C.get("off_slate_dates")))
cov = C.get("coverage") or ""
ck("...and the coverage line the page prints says it, with the number",
   ("This card is %s only" % DAY) in cov
   and ("%s priced row(s) for %s" % (n_off, ", ".join(LATER))) in cov,
   shown(cov[-260:]))
