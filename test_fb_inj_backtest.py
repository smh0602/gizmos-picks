#!/usr/bin/env python3
"""test_fb_inj_backtest.py — THE INJURY BAR'S RUNNER, AND WHICH LEAGUE'S READINGS A ROW GETS.

`[Sam, 2026-10-17]` NFL injuries: "In the sim, backtest-gated"; college: "use the college injury
source as long as it's accurate and up to date, we wouldn't want misinformation ruining our bets"
(research/cfb_injuries_design.md §4: the same bar). It asks:
  1. `fb_inj_backtest.passes` is the bar: log loss with <= without AND closing return with >=
     without, both, and agrees with test_fb_sim.py §3's reading of every recorded entry.
  2. `fb_inj_backtest.record` writes a league's entry ONCE and refuses to overwrite it.
  3. `fb_model.injury_readings`: a college row gets the conference reports' readings
     (`cfb_injuries.attach`), never T69 IN's, which read data/nfl; an NFL row gets IN's.

PLANTED DATA ONLY: the record file is a temp copy; the attach functions are stand-ins.

# @vacuity 🔴 the bar needs the log loss to hold
#   file: fb_inj_backtest.py
#   find: return ll["with"] <= ll["without"] and cr["with"] >= cr["without"]
#   with: return cr["with"] >= cr["without"]
#
# @vacuity 🔴 ...and the closing return to hold
#   file: fb_inj_backtest.py
#   find: return ll["with"] <= ll["without"] and cr["with"] >= cr["without"]
#   with: return ll["with"] <= ll["without"]
#
# @vacuity 🔴 a missing number never passes
#   file: fb_inj_backtest.py
#   find: if None in (ll.get("with"), ll.get("without"), cr.get("with"), cr.get("without")):
#   with: if False:
#
# @vacuity ⛔ a recorded entry is never overwritten: the bar is run once
#   file: fb_inj_backtest.py
#   find: if lg in inj:
#   with: if False:
#
# @vacuity ⛔ a college row never gets T69 IN's NFL readings
#   file: fb_model.py
#   find:     if lg == "ncaaf":
#   with:     if False:
#
# @vacuity 🔴 an NFL row gets T69 IN's readings
#   file: fb_model.py
#   find:     return fb_challengers.attach("IN", lg, rows, root)
#   with:     return rows
"""
import json
import os
import shutil
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "nfl")
import fb_inj_backtest as B  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

E = lambda llw, llo, crw, cro: {"logloss": {"with": llw, "without": llo},  # noqa: E731
                                "closing_return": {"with": crw, "without": cro}}

# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE BAR: BOTH NUMBERS, EVERY TIME")
# ══════════════════════════════════════════════════════════════════════
ck("✅ both hold -> passes", B.passes(E(0.700, 0.701, 2.0, 1.0)))
ck("✅ ...ties pass (at most / at least)", B.passes(E(0.700, 0.700, 1.0, 1.0)))
ck("🔴 the log loss worse -> fails, however good the return (NFL's real case: .70281 v .70259, "
   "+3.92% v +1.85%)", not B.passes(E(0.70281, 0.70259, 3.92, 1.85)))
ck("🔴 the return worse -> fails, however good the log loss", not B.passes(E(0.690, 0.700, 1.0, 2.0)))
ck("🔴 a missing number never passes", not B.passes(E(None, 0.70, 2.0, 1.0))
   and not B.passes({"logloss": {"with": 0.6, "without": 0.7}}))
_rec = json.load(open(B.RECORD, encoding="utf-8"))
_tfs = {lg: v["logloss"]["with"] <= v["logloss"]["without"]
        and v["closing_return"]["with"] >= v["closing_return"]["without"]
        for lg, v in (_rec.get("injuries") or {}).items()}
eq({lg: B.passes(v) for lg, v in (_rec.get("injuries") or {}).items()}, _tfs,
   "✅ ...and it reads every recorded entry exactly as test_fb_sim.py §3 does")

# ══════════════════════════════════════════════════════════════════════
section("2. ⛔ A LEAGUE'S ENTRY IS RECORDED ONCE")
# ══════════════════════════════════════════════════════════════════════
_t = tempfile.mkdtemp(prefix="injbt-")
try:
    _p = os.path.join(_t, "rec.json")
    json.dump({"run": "x", "injuries": {"nfl": E(0.7, 0.6, 1.0, 2.0)}}, open(_p, "w", encoding="utf-8"))
    _before = open(_p, encoding="utf-8").read()
    ck("⛔ an existing entry is refused", B.record("nfl", E(0.1, 0.9, 9.0, 0.0), _p) is False)
    eq(open(_p, encoding="utf-8").read(), _before, "⛔ ...and the file is untouched")
    ck("✅ a new league's entry is written", B.record("ncaaf", E(0.7, 0.71, 1.0, 0.5), _p) is True)
    _d = json.load(open(_p, encoding="utf-8"))
    eq((_d["injuries"]["ncaaf"]["logloss"], _d["run"], sorted(_d["injuries"])),
       ({"with": 0.7, "without": 0.71}, "x", ["ncaaf", "nfl"]), "✅ ...beside what was there")
    ck("⛔ ...and a second run of it is refused", B.record("ncaaf", E(0.1, 0.9, 9.0, 0.0), _p) is False)
finally:
    shutil.rmtree(_t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("3. ⛔ EACH LEAGUE'S ROWS GET ITS OWN READINGS")
# ══════════════════════════════════════════════════════════════════════
import fb_challengers  # noqa: E402
import fb_model as FM  # noqa: E402

_calls = []
_fake = types.ModuleType("cfb_injuries")
_fake.attach = lambda rows, root=None: _calls.append(("college", len(rows))) or rows
_saved_mod, _saved_in = sys.modules.get("cfb_injuries"), fb_challengers.attach
sys.modules["cfb_injuries"] = _fake
fb_challengers.attach = lambda name, lg, rows, root=None: _calls.append(("IN", lg)) or rows
try:
    FM.injury_readings("ncaaf", [{}, {}])
    _college = list(_calls)
    _calls.clear()
    FM.injury_readings("nfl", [{}])
    _nfl = list(_calls)
finally:
    fb_challengers.attach = _saved_in
    if _saved_mod is None:
        sys.modules.pop("cfb_injuries", None)
    else:
        sys.modules["cfb_injuries"] = _saved_mod
eq(_college, [("college", 2)], "⛔ a college row gets the conference reports' readings, never T69 IN's "
   "(which read data/nfl: every college team would read zero)")
eq(_nfl, [("IN", "nfl")], "🔴 an NFL row gets T69 IN's readings")
