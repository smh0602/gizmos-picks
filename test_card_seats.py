#!/usr/bin/env python3
"""EACH KIND KEEPS ITS OWN 25 SEATS ON GIZMO'S PICKS.

🔴 WHAT HAPPENED `[Sam, 2026-09-25, C8]`. The page showed 1 pitcher prop
and 46 hitter props (the card, `picks/2026-09-25.json`: 1 and 49). card.py
gave each kind half the board and let an unused half SPILL to the other.
Since C2 (#166) corrected the pitcher number against its price, few
pitcher rows beat their break-even, so hitters took the pitcher seats.
Sam: pitcher props on the board, no more than 25 hitters, "and it must
not happen again".

✅ `card.select_board`: hitters up to 25 (the rule as it was, capped);
pitchers beating their price first, then the best remaining pitcher rows
by the corrected number, each marked `below_price`; never both sides of
one prop; the page states the printed %, break-even and edge on such a row.

This file drives it on TODAY'S REAL SLATE (the inputs of the 14:12Z build,
anchored to the published card below), on synthetic slates, and drives the
page's own `pickCard` in node for the label.

# @vacuity no kind may take the other's seats (the spill that caused C8)
#   file: card.py
#   find:         if seats.get(x["kind"], 0) <= 0 or id(x) in used:
#   with:         if len(board) >= sum(cap.values()) or id(x) in used:
#
# @vacuity hitters are capped at 25, not at the board
#   file: card.py
#   find: SEATS = {"pitcher": BOARD_MAX // 2, "hitter": BOARD_MAX // 2}
#   with: SEATS = {"pitcher": BOARD_MAX // 2, "hitter": BOARD_MAX}
#
# @vacuity empty pitcher seats are filled with pitcher rows
#   file: card.py
#   find:     for x in fill:
#   with:     for x in fill[:0]:
#
# @vacuity ...by the corrected number, not by edge
#   file: card.py
#   find:     fill.sort(key=by_conf)
#   with:     fill.sort(key=lambda x: -x["edge"])
#
# @vacuity a row seated below its price is marked so
#   file: card.py
#   find:             x["below_price"] = True
#   with:             pass
#
# @vacuity never both sides of one prop
#   file: card.py
#   find:         if _propkey(x) in on:
#   with:         if False:
#
# @vacuity a doubleheader's game 2 is another prop, not the same one
#   file: card.py
#   find:     return (x.get("game_id"), (x.get("pid") or x.get("player") or x.get("pitcher")),
#   with:     return (None, (x.get("pid") or x.get("player") or x.get("pitcher")),
#
# @vacuity the page states the edge on a row below its price
#   file: index.html
#   find: (edge <b>${p.edge > 0 ? '+' : ''}${p.edge}%</b>).
#   with: .
"""
ROWS_FIXTURE = [
    ('p', 'a85710fa', 605280, 'outs', 15.5, 'over', 47, -5.7, 52.4),
    ('p', 'a85710fa', 605280, 'strikeouts', 4.5, 'under', 48, -10.1, 58.3),
    ('p', 'd4b069a1', 669432, 'outs', 17.5, 'over', 66, -2.0, 67.7),
    ('p', 'd4b069a1', 669432, 'outs', 18.5, 'under', 66, -2.6, 68.8),
    ('p', 'd4b069a1', 669432, 'strikeouts', 5.5, 'over', 48, -13.7, 61.4),
    ('p', 'd4b069a1', 669432, 'strikeouts', 6.5, 'under', 54, -6.7, 60.8),
    ('p', '3aa03f1c', 696149, 'outs', 15.5, 'under', 54, -3.7, 57.4),
    ('p', '3aa03f1c', 696149, 'strikeouts', 4.5, 'under', 43, -11.7, 54.5),
    ('p', '3aa03f1c', 695549, 'outs', 15.5, 'under', 56, -3.2, 59.2),
    ('p', '3aa03f1c', 695549, 'strikeouts', 4.5, 'over', 46, -17.2, 63.6),
    ('p', '3aa03f1c', 695549, 'strikeouts', 5.5, 'under', 48, -12.7, 60.8),
    ('p', '6e8b1f35', 650911, 'outs', 18.5, 'under', 48, -4.7, 52.4),
    ('p', '6e8b1f35', 650911, 'strikeouts', 5.5, 'over', 51, -9.4, 60.0),
    ('p', '6e8b1f35', 642547, 'outs', 14.5, 'over', 49, -5.7, 54.5),
    ('p', '6e8b1f35', 642547, 'strikeouts', 4.5, 'over', 43, -2.5, 45.5),
    ('p', '80d70619', 674841, 'outs', 14.5, 'over', 56, -4.0, 60.0),
    ('p', '80d70619', 674841, 'strikeouts', 4.5, 'over', 53, -6.9, 60.0),
    ('p', '890be5ce', 666157, 'outs', 17.5, 'under', 48, -5.7, 53.5),
    ('p', '890be5ce', 666157, 'strikeouts', 3.5, 'over', 49, -13.2, 62.3),
    ('p', '890be5ce', 666157, 'strikeouts', 4.5, 'under', 52, -5.3, 57.4),
    ('p', '2d3d3780', 691587, 'outs', 14.5, 'over', 53, -4.8, 57.4),
    ('p', '2d3d3780', 691587, 'strikeouts', 4.5, 'over', 53, -9.0, 62.3),
    ('p', '2d3d3780', 691587, 'strikeouts', 5.5, 'under', 48, -14.0, 61.5),
    ('p', 'b6829a30', 680732, 'outs', 16.5, 'under', 47, -4.7, 51.2),
    ('p', 'b6829a30', 680732, 'strikeouts', 5.5, 'under', 45, 3.0, 42.0),
    ('p', 'b6829a30', 680732, 'strikeouts', 6.5, 'under', 59, -0.9, 60.0),
    ('p', 'b6829a30', 608372, 'outs', 14.5, 'over', 57, -4.1, 60.8),
    ('p', 'b6829a30', 608372, 'strikeouts', 3.5, 'under', 43, -10.5, 53.5),
    ('p', '7bd30076', 668909, 'outs', 17.5, 'under', 49, -4.6, 53.5),
    ('p', '7bd30076', 668909, 'strikeouts', 6.5, 'over', 48, -9.2, 57.4),
    ('p', '7bd30076', 702070, 'outs', 17.5, 'under', 41, -5.1, 46.5),
    ('p', '7bd30076', 702070, 'strikeouts', 3.5, 'over', 58, -2.3, 60.0),
    ('p', '7bd30076', 702070, 'strikeouts', 4.5, 'over', 43, -1.8, 44.4),
    ('p', '12c52c4f', 700241, 'outs', 14.5, 'over', 54, -5.2, 59.2),
    ('p', '12c52c4f', 700241, 'strikeouts', 3.5, 'over', 46, -8.3, 54.5),
    ('p', '12c52c4f', 688107, 'outs', 15.5, 'under', 53, -3.6, 56.5),
    ('p', '12c52c4f', 688107, 'strikeouts', 4.5, 'over', 45, -16.9, 62.3),
    ('p', '9f08a9d7', 594798, 'outs', 15.5, 'under', 59, -2.8, 61.5),
    ('p', '9f08a9d7', 594798, 'strikeouts', 6.5, 'under', 48, -9.8, 57.4),
    ('p', '9f08a9d7', 657746, 'outs', 15.5, 'over', 49, -4.6, 53.5),
    ('p', '9f08a9d7', 657746, 'strikeouts', 5.5, 'under', 43, -2.5, 45.5),
    ('p', '9f08a9d7', 657746, 'strikeouts', 6.5, 'under', 55, -7.0, 62.1),
    ('p', 'eb8b9160', 694297, 'outs', 17.5, 'under', 50, -4.3, 54.5),
    ('p', 'eb8b9160', 694297, 'strikeouts', 3.5, 'over', 44, -13.2, 57.4),
    ('p', 'de8bbf8d', 686613, 'outs', 17.5, 'under', 48, -5.0, 53.5),
    ('p', 'de8bbf8d', 686613, 'strikeouts', 5.5, 'over', 47, -7.0, 53.5),
    ('p', 'de8bbf8d', 686613, 'strikeouts', 6.5, 'under', 47, -20.1, 66.7),
    ('p', 'de8bbf8d', 682052, 'outs', 14.5, 'over', 58, -3.5, 61.5),
    ('p', 'de8bbf8d', 682052, 'outs', 15.5, 'under', 58, -3.2, 61.5),
    ('p', 'de8bbf8d', 682052, 'strikeouts', 4.5, 'over', 46, -8.4, 54.5),
    ('p', '60b3d02a', 682243, 'outs', 15.5, 'over', 52, -3.7, 55.6),
    ('p', '60b3d02a', 682243, 'strikeouts', 6.5, 'under', 56, -3.4, 59.2),
    ('p', '60b3d02a', 672282, 'outs', 16.5, 'over', 50, -4.3, 54.5),
    ('p', '60b3d02a', 672282, 'strikeouts', 6.5, 'under', 45, -3.5, 48.8),
    ('p', 'e47efe97', 669373, 'outs', 17.5, 'over', 62, -2.4, 64.3),
    ('p', 'e47efe97', 669373, 'strikeouts', 6.5, 'under', 42, -0.1, 41.7),
    ('p', 'e47efe97', 669373, 'strikeouts', 7.5, 'under', 56, -1.7, 57.4),
    ('h', 'd4b069a1', 665966, 'batter_rbis', 0.5, 'under', 90, 3.1, 86.7),
    ('h', '3fe14d47', 665966, 'batter_rbis', 0.5, 'under', 90, 4.6, 85.2),
    ('h', '890be5ce', 663647, 'batter_rbis', 0.5, 'under', 90, 6.4, 83.3),
    ('h', '890be5ce', 663647, 'batter_total_bases', 1.5, 'under', 87, 5.2, 81.8),
    ('h', 'b6829a30', 668670, 'batter_total_bases', 1.5, 'under', 85, 8.2, 76.5),
    ('h', 'd4b069a1', 665966, 'batter_total_bases', 1.5, 'under', 84, 1.1, 82.6),
    ('h', '3fe14d47', 665966, 'batter_total_bases', 1.5, 'under', 84, 1.1, 82.6),
    ('h', '2d3d3780', 665923, 'batter_rbis', 0.5, 'under', 84, 5.5, 78.9),
    ('h', 'de8bbf8d', 678489, 'batter_rbis', 0.5, 'under', 82, 6.0, 76.5),
    ('h', 'de8bbf8d', 695720, 'batter_rbis', 0.5, 'under', 82, 2.8, 79.5),
    ('h', '7bd30076', 680757, 'batter_rbis', 0.5, 'under', 81, 3.1, 77.8),
    ('h', '12c52c4f', 695336, 'batter_rbis', 0.5, 'under', 81, 2.9, 77.8),
    ('h', '7bd30076', 681807, 'batter_rbis', 0.5, 'under', 80, 1.2, 78.9),
    ('h', '60b3d02a', 685133, 'batter_rbis', 0.5, 'under', 80, 0.4, 80.0),
    ('h', '2d3d3780', 573262, 'batter_rbis', 0.5, 'under', 79, 1.1, 77.8),
    ('h', 'eb8b9160', 656976, 'batter_total_bases', 1.5, 'under', 79, 5.7, 73.3),
    ('h', 'eb8b9160', 669392, 'batter_hits_runs_rbis', 0.5, 'over', 79, 19.6, 59.2),
    ('h', 'a85710fa', 678882, 'batter_hits_runs_rbis', 0.5, 'over', 78, 14.2, 63.6),
    ('h', '80d70619', 805999, 'batter_rbis', 0.5, 'under', 78, 1.5, 76.5),
    ('h', 'b6829a30', 678246, 'batter_hits', 1.5, 'under', 78, 4.8, 73.3),
    ('h', 'a85710fa', 596115, 'batter_hits_runs_rbis', 0.5, 'over', 77, 14.7, 62.3),
    ('h', '3fe14d47', 669236, 'batter_total_bases', 1.5, 'under', 77, 0.7, 76.5),
    ('h', '7bd30076', 608070, 'batter_hits', 1.5, 'under', 77, 5.2, 71.4),
    ('h', 'd4b069a1', 671218, 'batter_rbis', 0.5, 'under', 76, 2.9, 73.3),
    ('h', '6e8b1f35', 666018, 'batter_hits_runs_rbis', 0.5, 'over', 76, 10.1, 66.1),
    ('h', '3fe14d47', 671218, 'batter_rbis', 0.5, 'under', 76, 2.9, 73.3),
    ('h', '2d3d3780', 573262, 'batter_total_bases', 1.5, 'under', 76, 1.0, 75.0),
    ('h', '2d3d3780', 672640, 'batter_hits', 0.5, 'over', 76, 4.2, 71.4),
    ('h', 'de8bbf8d', 701358, 'batter_rbis', 0.5, 'under', 76, 5.0, 70.6),
    ('h', 'a85710fa', 678882, 'batter_hits', 0.5, 'over', 75, 18.3, 56.5),
    ('h', '80d70619', 620443, 'batter_rbis', 0.5, 'under', 75, 1.3, 73.3),
    ('h', '890be5ce', 672386, 'batter_hits', 0.5, 'over', 75, 7.6, 67.7),
    ('h', '890be5ce', 807727, 'batter_total_bases', 1.5, 'under', 75, 2.8, 72.2),
    ('h', 'b6829a30', 664983, 'batter_hits', 0.5, 'over', 75, 9.3, 65.5),
    ('h', '9f08a9d7', 607043, 'batter_rbis', 0.5, 'under', 75, 4.1, 70.6),
    ('h', 'de8bbf8d', 665161, 'batter_hits', 0.5, 'over', 75, 1.7, 73.3),
    ('h', '60b3d02a', 694208, 'batter_total_bases', 1.5, 'under', 75, 2.0, 73.3),
    ('h', 'e47efe97', 813841, 'batter_hits_runs_rbis', 0.5, 'over', 75, 12.7, 62.3),
    ('h', 'd4b069a1', 687952, 'batter_hits_runs_rbis', 0.5, 'over', 74, 9.7, 64.3),
    ('h', '3aa03f1c', 805808, 'batter_hits', 0.5, 'over', 74, 6.9, 66.7),
    ('h', '80d70619', 543760, 'batter_total_bases', 1.5, 'under', 74, 2.9, 70.6),
    ('h', '3fe14d47', 687952, 'batter_hits_runs_rbis', 0.5, 'over', 74, 9.7, 64.3),
    ('h', 'b6829a30', 666160, 'batter_hits_runs_rbis', 0.5, 'over', 74, 19.0, 54.5),
    ('h', 'eb8b9160', 672515, 'batter_hits', 0.5, 'over', 74, 7.5, 66.1),
    ('h', 'eb8b9160', 669392, 'batter_hits', 0.5, 'over', 74, 20.3, 53.5),
    ('h', 'de8bbf8d', 514888, 'batter_hits', 1.5, 'under', 74, 1.6, 72.2),
    ('h', 'de8bbf8d', 514888, 'batter_rbis', 0.5, 'under', 74, 6.1, 67.7),
    ('h', 'e47efe97', 605141, 'batter_hits', 1.5, 'under', 74, 2.9, 70.6),
    ('h', 'd4b069a1', 806146, 'batter_hits_runs_rbis', 0.5, 'over', 73, 10.4, 62.3),
    ('h', '6e8b1f35', 802415, 'batter_hits', 0.5, 'over', 73, 8.3, 64.3),
    ('h', '6e8b1f35', 691406, 'batter_hits', 0.5, 'over', 73, 5.7, 67.7),
    ('h', '80d70619', 666182, 'batter_hits', 1.5, 'under', 73, 3.5, 69.2),
    ('h', '3fe14d47', 806146, 'batter_hits_runs_rbis', 0.5, 'over', 73, 9.7, 63.0),
    ('h', '2d3d3780', 669364, 'batter_hits', 0.5, 'over', 73, 8.1, 64.9),
    ('h', '7bd30076', 677951, 'batter_hits', 0.5, 'over', 73, 2.8, 70.6),
    ('h', '7bd30076', 608070, 'batter_rbis', 0.5, 'under', 73, 4.1, 69.2),
    ('h', '7bd30076', 686681, 'batter_hits_runs_rbis', 0.5, 'over', 73, 8.2, 64.7),
]
# ⚠️ The inputs `select_board` received in the 14:12Z build of 2026-09-25
# (the published card's own build: data at 67ce2e4, clock at 14:12Z):
# every priced pitcher row, and every positive-edge hitter row down to the
# 49th-best's confidence (ties kept) -- the only hitters any rule can seat.
# (kind, game_id[:8], pid, market, line, side, confidence, edge, break_even)

import collections
import json
import os
import random
import shutil
import subprocess
import tempfile

from jsblock import js_block
from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("LEAGUE", "mlb")
import card as C  # noqa: E402

KIND = {"p": "pitcher", "h": "hitter"}


def rows(fixture=ROWS_FIXTURE):
    return [dict(kind=KIND[k], game_id=g, pid=pid, market=m, line=ln, side=sd,
                 confidence=cf, edge=e, break_even=be)
            for k, g, pid, m, ln, sd, cf, e, be in fixture]


def key(x):
    return (x["game_id"], x["pid"], x["market"], x["line"])


def split(r):
    return [x for x in r if x["kind"] == "pitcher"], [x for x in r if x["kind"] == "hitter"]


def invariants(board, acct, plays, hitters, why):
    """What must hold on ANY slate. Computed here, not read from card.py."""
    n = collections.Counter(x["kind"] for x in board)
    eligible = {key(x) for x in plays if x["edge"] is not None and x["break_even"] is not None}
    ks = collections.Counter(key(x) for x in board)
    ok = (n["hitter"] <= 25 and n["pitcher"] <= 25
          and n["pitcher"] == min(25, len(eligible))
          and all(v == 1 for v in ks.values())
          and all((x["edge"] > 0) != bool(x.get("below_price")) for x in board)
          and all(board[i]["confidence"] >= board[i + 1]["confidence"] for i in range(len(board) - 1))
          and acct["pitcher"]["shown"] == n["pitcher"] and acct["hitter"]["shown"] == n["hitter"])
    return ok, "%s: %d pitcher, %d hitter, %d eligible pitcher props, dup keys %s" % (
        why, n["pitcher"], n["hitter"], len(eligible), [k for k, v in ks.items() if v > 1][:2])


# ══════════════════════════════════════════════════════════════════════
section("1. THE FIXTURE IS TODAY'S REAL SLATE")
# ══════════════════════════════════════════════════════════════════════
PUB = json.load(open(os.path.join(ROOT, "picks", "2026-09-25.json"), encoding="utf-8"))
_pub = collections.Counter(p["kind"] for p in PUB["picks"])
eq((_pub["pitcher"], _pub["hitter"]), (1, 49),
   "the published card IS the defect: 1 pitcher row, 49 hitter rows (⛔ never edited)")
R = rows()
_fk = {(x["game_id"], x["pid"], x["market"], x["line"], x["side"]) for x in R}
_ph = [(p["game_id"][:8], p["pid"], p["market"], p["line"], p["side"]) for p in PUB["picks"]]
ck(all(k in _fk for k in _ph),
   "every row on the published card is in the fixture (all 50)",
   str([k for k in _ph if k not in _fk][:3]))
PLAYS, HITTERS = split(R)
_beat = [x for x in PLAYS if x["edge"] > 0]
eq([(x["pid"], x["market"], x["line"], x["side"]) for x in _beat],
   [(p["pid"], p["market"], p["line"], p["side"]) for p in PUB["picks"] if p["kind"] == "pitcher"],
   "   ...and its ONE pitcher row beating the price is the published card's one pitcher row")
eq(len({key(x) for x in PLAYS}), 57, "   57 pitcher props priced, as the card's board_rule says")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 ON TODAY'S SLATE: 25 PITCHERS, 25 HITTERS")
# ══════════════════════════════════════════════════════════════════════
eq(C.SEATS, {"pitcher": 25, "hitter": 25}, "card.py's seats are Sam's 25 and 25")
B, A = C.select_board(PLAYS, HITTERS)
_n = collections.Counter(x["kind"] for x in B)
eq((_n["pitcher"], _n["hitter"]), (25, 25),
   "🔴🔴 1 positive-edge pitcher row and 25 pitcher rows are still shown; hitters stop at 25")
eq(sum(1 for x in B if x["kind"] == "pitcher" and not x.get("below_price")), 1,
   "   the one pitcher row that beats its price is on, unmarked")
# The 24 others, derived HERE: the best remaining pitcher rows by the
# corrected number, one side per prop.
_want, _seen = [], {key(_beat[0])}
for x in sorted([x for x in PLAYS if x["edge"] <= 0], key=lambda x: -x["confidence"]):
    if key(x) not in _seen and len(_want) < 24:
        _want.append((key(x), x["side"]))
        _seen.add(key(x))
_got = [(key(x), x["side"]) for x in B if x["kind"] == "pitcher" and x.get("below_price")]
eq(sorted(_got), sorted(_want),
   "🔴 the other 24 are the best remaining pitcher props by the corrected number, one side each, "
   "every one marked below its price")
_hl = sorted([x for x in HITTERS if x["edge"] > 0], key=lambda x: -x["confidence"])
ck(min(x["confidence"] for x in B if x["kind"] == "hitter") >= _hl[24]["confidence"]
   and not any(x.get("below_price") for x in B if x["kind"] == "hitter"),
   "   hitters: the rule as it was -- the best 25 that beat their price, none below it")
ok, why = invariants(B, A, PLAYS, HITTERS, "today")
ck(ok, "   every invariant holds (caps, one side per prop, labels true both ways, descending)", why)
eq(A, {"pitcher": {"seats": 25, "beat_price": 1, "below_price": 24, "shown": 25, "eligible_props": 57},
       "hitter": {"seats": 25, "beat_price": 25, "below_price": 0, "shown": 25}},
   "   the card's own accounting says the same")

# ══════════════════════════════════════════════════════════════════════
section("3. SYNTHETIC SLATES: THE CAPS HOLD WHATEVER THE SLATE")
# ══════════════════════════════════════════════════════════════════════
def prop(kind, g, pid, conf, be, line=0.5, market="m", side="over"):
    return dict(kind=kind, game_id=g, pid=pid, market=market, line=line, side=side,
                confidence=conf, break_even=be, edge=round(conf - be, 1))


def both(kind, g, pid, conf, be_o, be_u, market="m", line=0.5):
    return [prop(kind, g, pid, conf, be_o, line, market, "over"),
            prop(kind, g, pid, 100 - conf, be_u, line, market, "under")]


# Sam's case, built from nothing: ONE pitcher row beats its price.
P1 = [prop("pitcher", "g0", 1, 60, 55)]
for i in range(40):
    P1 += both("pitcher", "g%d" % (i % 15), 100 + i, 50 + i % 20, 60 + i % 20, 60)
H1 = [prop("hitter", "g%d" % (i % 15), 1000 + i, 70 + i % 25, 60) for i in range(100)]
B1, A1 = C.select_board(P1, H1)
_n1 = collections.Counter(x["kind"] for x in B1)
eq((_n1["pitcher"], _n1["hitter"]), (25, 25),
   "🔴🔴 a slate with 1 positive-edge pitcher row shows 25 pitcher rows and 25 hitter rows")
ok, why = invariants(B1, A1, P1, H1, "one-beats")
ck(ok, "   every invariant holds", why)

# No pitchers at all: the hitters still stop at 25.
B2, A2 = C.select_board([], H1)
eq(collections.Counter(x["kind"] for x in B2)["hitter"], 25,
   "🔴 hitters never take an empty pitcher seat: 25 with no pitcher rows at all")

# A thin slate: 3 pitcher props (both sides each) and 10 hitters beating the price.
P3 = sum((both("pitcher", "g%d" % i, 200 + i, 58, 60, 50) for i in range(3)), [])
H3 = ([prop("hitter", "g%d" % i, 2000 + i, 80, 70) for i in range(10)]
      + [prop("hitter", "g%d" % i, 3000 + i, 60, 70) for i in range(30)])
B3, A3 = C.select_board(P3, H3)
_n3 = collections.Counter(x["kind"] for x in B3)
eq(_n3["pitcher"], 3, "a thin slate: every pitcher prop once, never both sides (3 props, 3 rows)")
ck(_n3["hitter"] <= 25 and len(B3) == C.BOARD_MIN,
   "   ...and the old thin-board top-up still fills to 25, inside the hitters' own seats",
   "%d rows" % len(B3))
ok, why = invariants(B3, A3, P3, H3, "thin")
ck(ok, "   every invariant holds", why)

# Both sides beating their prices (each side shopped at its own best book).
P4 = [prop("pitcher", "g1", 9, 55, 52, 5.5, "strikeouts", "over"),
      prop("pitcher", "g1", 9, 47, 44, 5.5, "strikeouts", "under")]
B4, _ = C.select_board(P4, [])
eq([(x["side"]) for x in B4], ["over"], "⛔ both sides beating the price: only the likelier side is shown")

# A doubleheader: the same prop in game 1 and game 2 is two wagers.
P5 = [prop("pitcher", "dh1", 7, 58, 55), prop("pitcher", "dh2", 7, 57, 55)]
B5, _ = C.select_board(P5, [])
eq(len(B5), 2, "✅ a doubleheader's game 2 is another prop, keyed by GAME ID, and may show")

# Random slates: the invariants, not one hand-picked case.
rnd = random.Random(20260925)
bad = []
for t in range(300):
    ps, hs = [], []
    for i in range(rnd.randint(0, 45)):
        ps += both("pitcher", "g%d" % rnd.randint(0, 14), 10000 + i, rnd.randint(30, 75),
                   rnd.randint(45, 75), rnd.randint(45, 75), rnd.choice(["outs", "strikeouts"]),
                   rnd.choice([3.5, 4.5, 5.5, 15.5, 17.5]))
    for i in range(rnd.randint(0, 90)):
        hs += both("hitter", "g%d" % rnd.randint(0, 14), 20000 + i, rnd.randint(40, 95),
                   rnd.randint(50, 90), rnd.randint(30, 60))
    b, a = C.select_board(ps, hs)
    ok, why = invariants(b, a, ps, hs, "slate %d" % t)
    if not ok:
        bad.append(why)
ck(not bad, "🔴 300 random slates: hitters never exceed 25, pitcher seats full when the slate "
   "allows, one side per prop, every label true", str(bad[:2]))

# ══════════════════════════════════════════════════════════════════════
section("4. THE PAGE SAYS SO: printed %, break-even and edge")
# ══════════════════════════════════════════════════════════════════════
PAGE = os.path.join(ROOT, "index.html")
_src = open(PAGE, encoding="utf-8").read()
_el = next(l for l in _src.splitlines() if l.startswith("const el = "))
DRIVER = r"""
const fs = require('fs');
function node(){ return {className: '', innerHTML: '', kids: [],
  append(...n){ this.kids.push(...n); },
  insertAdjacentHTML(_, h){ this.kids.push({innerHTML: h, kids: []}); } }; }
const document = {createElement: () => node()};
const text = n => (n.innerHTML || '') + ' ' + (n.kids || []).map(text).join(' ');
const S = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const stub = () => '';
const fn = new Function('document', 'confClass', 'headUrl', 'projChip', 'mark', 'ab', 'sgn',
  'bookChip', 'betControl', 'betLink', 'fbMark', 'fbAb', 'FBTEAMS', 'LEAGUE',
  S.el + '\n' + S.fn + '\nreturn pickCard;');
const pickCard = fn(document, stub, stub, stub, stub, stub, String, stub, stub, stub, stub, stub, {}, 'mlb');
process.stdout.write(JSON.stringify(S.rows.map(r => text(pickCard(r)).replace(/\s+/g, ' '))));
"""
_base = dict(kind="pitcher", pitcher="Trevor Rogers", game="MIA @ WSH", market="outs", side="over", line=17.5,
             price=-210, book="hardrockbet", confidence_basis="MODEL")
CARDS = [dict(_base, confidence=66, break_even=67.7, edge=-2.0, below_price=True),
         dict(_base, confidence=45, break_even=42.0, edge=3.0),
         dict(_base, confidence=66, break_even=67.7, edge=None, below_price=True)]
tmp = tempfile.mkdtemp(prefix="seats-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"el": _el, "fn": js_block("pickCard", PAGE), "rows": CARDS},
              open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=300)
    ck(r.returncode == 0, "⚠️ the page's own pickCard ran in node", (r.stderr or "")[-300:])
    T = json.loads(r.stdout) if r.returncode == 0 else ["", "", ""]
finally:
    shutil.rmtree(tmp, ignore_errors=True)
ck("Loses to its price" in T[0] and "66%" in T[0] and "67.7%" in T[0] and "-2%" in T[0]
   and "fill the board out" in T[0],
   "🔴 a row below its price says it loses to it, with the printed 66%, the 67.7% break-even "
   "and the -2 edge", T[0][-260:])
ck("Loses to its price" not in T[1] and "fill the board out" not in T[1],
   "   a row that beats its price carries no such label")
ck("fill the board out" in T[2] and "undefined" not in T[2] and "null" not in T[2],
   "   a row missing a number keeps the plain sentence, never 'undefined'", T[2][-300:])
note("⛔ WHAT THIS DOES NOT CLAIM: which pitcher rows the model SHOULD like. The "
     "corrected number (C2) is unchanged; this only decides who gets a seat. "
     "verify_card.py section 7c checks the same caps on every live card.")
