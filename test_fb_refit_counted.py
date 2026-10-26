#!/usr/bin/env python3
"""T73 — THE CONTEST COUNTS LAST SEASON AND THIS SEASON (research/fb_refit_spec.md §3g).

`[Sam, 2026-10-26]` *"instead of having it need 300 scored prediction can we just use games
from last season and the ones played this season for both cfb and nfl. id rather have it do
that and learn progressievley week after week than wait for 300 different scores"*.
§3g, frozen before any result under it: eighteen challengers count EVERY 2025-2026 walk-forward
prediction toward the verdict; the eight shaped on those games (fb_refit.SCORED_ONLY) still count
only the weeks from registration; the floor counts the predictions that differ from the
champion's; P and T's withdrawal window stays the weeks before 2026-10-19; one branch, to the
largest mean d; after a champion switch the eighteen do not restart and the eight do.

Planted predictions and a pinned clock only. ⛔ Reads no live data: no fb-refit.json, no
build_rows, no git; nothing is pushed (push_branch is replaced by a recorder).

# @vacuity 🔴 a challenger outside the eight counts every week, before its registration too
#   file: fb_refit.py
#   find:     counted = [] if out["withdrawn"] or not entered else scored if name in SCORED_ONLY else preds
#   with:     counted = [] if out["withdrawn"] or not entered else scored
#
# @vacuity 🔴 ...and one of the eight counts only the weeks from its registration
#   file: fb_refit.py
#   find:     counted = [] if out["withdrawn"] or not entered else scored if name in SCORED_ONLY else preds
#   with:     counted = [] if out["withdrawn"] or not entered else preds
#
# @vacuity 🔴 ...and nothing is counted before the registration Monday
#   file: fb_refit.py
#   find:     counted = [] if out["withdrawn"] or not entered else scored if name in SCORED_ONLY else preds
#   with:     counted = [] if out["withdrawn"] else scored if name in SCORED_ONLY else preds
#
# @vacuity 🔴 league() tells contest() whether the registration Monday has come
#   file: fb_refit.py
#   find:                            entered=bool(reg) and reg <= today,
#   with:                            entered=True,
#
# @vacuity 🔴 the floor counts only predictions that differ from the champion's
#   file: fb_refit.py
#   find:                 preds.append((wk, (loss(a[gid][0], y), loss(p_x, y), gid), p_x != a[gid][0]))
#   with:                 preds.append((wk, (loss(a[gid][0], y), loss(p_x, y), gid), True))
#
# @vacuity 🔴 ...while the test runs over every counted prediction, equal ones included
#   file: fb_refit.py
#   find:     out["counted"] = dict(test([pair for _wk, pair, _df in counted]),
#   with:     out["counted"] = dict(test([pair for _wk, pair, df in counted if df]),
#
# @vacuity 🔴 P and T's withdrawal window is the weeks before 2026-10-19, whatever a switch did to start
#   file: fb_refit.py
#   find:     h = test([pair for wk, pair, _df in preds if wk < WITHDRAW_BEFORE]) if c["withdrawable"] else None
#   with:     h = test([pair for wk, pair, _df in preds if wk < start]) if c["withdrawable"] else None
#
# @vacuity 🔴 ...and that date is §3g's own
#   file: fb_refit.py
#   find: WITHDRAW_BEFORE = "2026-10-19"
#   with: WITHDRAW_BEFORE = "2026-10-26"
#
# @vacuity 🔴 the eight are exactly §3g's list
#   file: fb_refit.py
#   find: SCORED_ONLY = ("S", "TS", "AV", "AVC", "AT", "ATC", "SM", "SMC")
#   with: SCORED_ONLY = ("S", "TS", "AV", "AVC", "AT", "ATC", "SM")
#
# @vacuity 🔴 the floor is §3g's 300
#   file: fb_refit.py
#   find: MIN_SCORED = 300
#   with: MIN_SCORED = 250
#
# @vacuity 🔴 the one branch goes to the WINS with the largest mean d
#   file: fb_refit.py
#   find:                   key=lambda x: (-x["counted"]["mean_d"], x["counted"]["p"], order.index(x["name"])))
#   with:                   key=lambda x: (x["counted"]["mean_d"], x["counted"]["p"], order.index(x["name"])))
#
# @vacuity 🔴 ...a tie on mean d, the smaller p
#   file: fb_refit.py
#   find:                   key=lambda x: (-x["counted"]["mean_d"], x["counted"]["p"], order.index(x["name"])))
#   with:                   key=lambda x: (-x["counted"]["mean_d"], -x["counted"]["p"], order.index(x["name"])))
#
# @vacuity 🔴 ...then the earlier name in fb_challengers.CHALLENGERS
#   file: fb_refit.py
#   find:                   key=lambda x: (-x["counted"]["mean_d"], x["counted"]["p"], order.index(x["name"])))
#   with:                   key=lambda x: (-x["counted"]["mean_d"], x["counted"]["p"], -order.index(x["name"])))
#
# @vacuity 🔴 weekly() pushes ONE branch a league, never one per WINS
#   file: fb_refit.py
#   find:                 if x is not wins[0]:          # §3g: every WINS is reported; ONE branch, to the first
#   with:                 if False:          # §3g: every WINS is reported; ONE branch, to the first
#
# @vacuity 🔴 after a champion switch the eight restart (and the eighteen do not)
#   file: fb_refit.py
#   find:         since = monday_on_or_after(today)          # §2: scored weeks restart at the next Monday
#   with:         since = since          # §2: scored weeks restart at the next Monday
#
# @vacuity 🔴 the Monday email says "counted predictions (last season and this season)" only for the eighteen
#   file: status.py
#   find:     return ("counted predictions (last season and this season)" if x.get("counts") == "all"
#   with:     return ("counted predictions (last season and this season)" if True
#
# @vacuity 🔴 ...and reads the floor from the report, never a number of its own
#   file: status.py
#   find:         " (%d needed)" % floor if isinstance(floor, int) else "")
#   with:         " (%d needed)" % 300 if isinstance(floor, int) else "")
#
# @vacuity 🔴 ...says a challenger not yet registered has nothing counted
#   file: status.py
#   find:     if x.get("registered") and x["registered"] > str(doc.get("built_at") or "")[:10]:
#   with:     if False:
#
# @vacuity 🔴 ...says which WINS the one branch went to
#   file: status.py
#   find:         if v == "WINS" and x.get("outranked_by"):
#   with:         if False:
#
# @vacuity 🔴 ...puts only the branch's WINS under "Needs you"
#   file: status.py
#   find:         if x.get("outranked_by"):            # `[Sam, 2026-10-26]` §3g: said under the winner it lost the branch to
#   with:         if False:            # `[Sam, 2026-10-26]` §3g: said under the winner it lost the branch to
#
# @vacuity 🔴 ...and names the other WINS beside it
#   file: status.py
#   find:         also = [y["name"] for y in doc.get("challengers") or [] if y.get("outranked_by") == x["name"]]
#   with:         also = []
"""
import atexit
import datetime
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
import fb_challengers as FC  # noqa: E402
import fb_inj_backtest as IB  # noqa: E402
import fb_model as FM  # noqa: E402
import fb_refit as R  # noqa: E402
import status as S  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 11, 2, 11, 17, tzinfo=UTC)          # a Monday, after the 09:47Z run
TREES = []
atexit.register(lambda: [shutil.rmtree(t, ignore_errors=True) for t in TREES])


def tree():
    t = tempfile.mkdtemp(prefix="fbcounted-")
    TREES.append(t)
    for lg in ("nfl", "ncaaf"):
        os.makedirs(os.path.join(t, "data", lg, "latest"))
    return t


class Planted:
    """Walk-forward predictions handed in: {market: {game: (p, y, Monday, row)}}."""

    def __init__(self, preds):
        self.preds = preds

    def predictions(self, mk, keep=None):
        return self.preds.get(mk, {})


ROW = {"pml": 0.5, "season": 2026}           # all league()'s scoreboard reads of a planted row
# Last season and this season before 2026-10-19 (history), and the two Mondays from it (scored).
HIST = ["2025-11-17", "2025-11-24", "2026-09-14", "2026-10-05", "2026-10-12"]
LIVE = ["2026-10-19", "2026-10-26"]
CHAMP_P = 0.6
GOOD = lambda y: 0.75 if y else 0.35  # noqa: E731
BAD = lambda y: 0.3 if y else 0.7  # noqa: E731
SAME = lambda y: CHAMP_P  # noqa: E731


def games(weeks, p, n, start=0):
    out = {}
    for i in range(n):
        y = 1 if (i * 7) % 10 < 6 else 0
        out["g%d" % (start + i)] = (p(y), y, weeks[i % len(weeks)], ROW)
    return out


def market_set(parts, markets=FM.MARKETS):
    """parts: [(weeks, p, n)] laid end to end, the same games in every market."""
    out = {mk: {} for mk in markets}
    at = 0
    for weeks, p, n in parts:
        for mk in markets:
            out[mk].update(games(weeks, p, n, at))
        at += n
    return out


CHAMP = Planted(market_set([(HIST, SAME, 200), (LIVE, SAME, 100)]))


def contest(name, fits, start="2026-10-19", entered=True):
    return R.contest([], CHAMP, name, start, "2026-10-19", fits=Planted(fits), entered=entered)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE CODE'S LISTS ARE §3g's OWN, READ FROM THE FROZEN TEXT")
# ══════════════════════════════════════════════════════════════════════
_spec = open(os.path.join(ROOT, "research", "fb_refit_spec.md"), encoding="utf-8").read()
_3g = _spec[_spec.find("\n## 3g. "):_spec.find("\n## 4. ")]


def names_in(pattern):
    m = re.search(pattern, _3g, re.S)
    txt = " ".join(m.group(1).split()) if m else ""
    return [n.strip() for n in re.split(r",| and ", txt) if n.strip()]


ALL18 = names_in(r"\*\*Counted weeks\.\*\* For (.*?) \(each defined")
EIGHT = names_in(r"\*\*Still only games after registration \(§2\):\*\* (.*?)\. Each")
_floor = re.search(r"\*\*The floor:\*\* at least (\d+) counted predictions", _3g)
_win = re.search(r"\*\*Withdrawal\*\* \(P and T\) is unchanged: §2's history window, the weeks before "
                 r"(\d{4}-\d\d-\d\d)\.", _3g)
ck(len(ALL18) == 18 and len(EIGHT) == 8, "§3g is in the spec and names eighteen and eight", (ALL18, EIGHT))
eq(R.SCORED_ONLY, tuple(EIGHT), "🔴 fb_refit.SCORED_ONLY is §3g's eight, in its order")
eq((sorted(ALL18 + EIGHT), len(set(ALL18) & set(EIGHT))), (sorted(FC.CHALLENGERS), 0),
   "🔴 the eighteen and the eight are every challenger, each exactly once")
eq(R.MIN_SCORED, int(_floor.group(1)) if _floor else None, "🔴 the floor is §3g's (300)")
eq(R.WITHDRAW_BEFORE, _win.group(1) if _win else None, "🔴 P and T's withdrawal window ends on §3g's date")
eq(sorted(n for n, c in FC.CHALLENGERS.items() if c["withdrawable"]), ["P", "T"],
   "   ...and only P and T can be withdrawn")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE EIGHTEEN COUNT LAST SEASON AND THIS SEASON; THE EIGHT ONLY FROM REGISTRATION")
# ══════════════════════════════════════════════════════════════════════
# E: 200 games before 2026-10-19 (last season and this one), better than the champion on every one.
E_HIST = market_set([(HIST, GOOD, 200)], ("spread", "moneyline"))
e = contest("E", E_HIST)
eq((e["counts"], e["history"]["predictions"], e["scored"]["predictions"], e["counted"]["predictions"],
    e["counted"]["differing"]), ("all", 400, 0, 400, 400),
   "🔴 E: 400 predictions, every one before its registration Monday, all counted toward the verdict")
v = R.verdicts([e])[0]
ck(v["verdict"] == "WINS" and v["counted"]["mean_d"] > 0 and v["counted"]["p"] < v["alpha"],
   "🔴 ...so with 400 history predictions that beat the bar it WINS now, not in a season's time",
   (v["verdict"], v["counted"]))
# The same 400, 299 of them EQUAL to the champion's (as WX before stored weather): 101 differ.
E_EQ = {"spread": dict(games(HIST, SAME, 150), **games(HIST, GOOD, 50, 150)),
        "moneyline": dict(games(HIST, SAME, 149), **games(HIST, GOOD, 51, 149))}
e2 = contest("E", E_EQ)
v2 = R.verdicts([e2])[0]
eq((e2["counted"]["predictions"], e2["counted"]["differing"], v2["verdict"]), (400, 101, "NOT YET MEASURABLE"),
   "🔴 400 counted with 299 equal to the champion's: only 101 differ, under the floor, NOT YET MEASURABLE")
_d101 = R.test([(R.loss(CHAMP_P, y), R.loss(p, y), g) for mk in E_EQ for g, (p, y, _w, _r) in E_EQ[mk].items()
                if p != CHAMP_P])["mean_d"]
ck(e2["counted"]["p"] < v2["alpha"] and abs(e2["counted"]["mean_d"] - _d101 * 101 / 400) < 1e-5,
   "🔴 ...although its p clears the bar: the test runs over all 400, the equal ones adding d = 0",
   (e2["counted"], _d101))
# S, one of the eight: the same planted shape on all three markets, history and scored weeks.
BOTH = market_set([(HIST, GOOD, 200), (LIVE, GOOD, 100)])
s_ = contest("S", BOTH)
e3 = contest("E", BOTH)
eq((s_["counts"], s_["history"]["predictions"], s_["counted"]["predictions"]), ("scored", 600, 300),
   "🔴 S (one of the eight): its 600 history predictions are reported, only its 300 scored ones counted")
eq((e3["counts"], e3["counted"]["predictions"]), ("all", 600),
   "🔴 ...while E counts all 600 of its own (two markets, history and scored alike)")
for n in R.SCORED_ONLY:
    c = contest(n, BOTH)
    ck(c["counts"] == "scored" and c["counted"]["predictions"] == c["scored"]["predictions"] > 0,
       "   %s counts only its scored weeks" % n, (c["counted"]["predictions"], c["scored"]["predictions"]))
_wide = [n for n in FC.CHALLENGERS if n not in R.SCORED_ONLY and not FC.CHALLENGERS[n]["withdrawable"]]
ck(all(contest(n, BOTH)["counted"]["predictions"] == 300 * len(FC.CHALLENGERS[n]["markets"]) for n in _wide),
   "🔴 every one of the eighteen (P and T below) counts every week on each of its markets", _wide)
c = contest("E", BOTH, entered=False)
eq((c["counted"]["predictions"], c["history"]["predictions"]), (0, 400),
   "🔴 before its registration Monday a challenger has not entered: nothing is counted (its history is still "
   "reported)")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 WITHDRAWAL (P AND T) READS THE WEEKS BEFORE 2026-10-19, WHATEVER A SWITCH DID")
# ══════════════════════════════════════════════════════════════════════
# Worse than the champion on 40 games before 2026-10-19, better on 120 games after it.
P_FITS = market_set([(HIST, BAD, 40), (LIVE, GOOD, 120)], ("spread", "moneyline"))
_p0 = contest("P", P_FITS)
_p1 = contest("P", P_FITS, start="2026-11-02")             # a champion switch moved scored_from
ck(_p0["withdrawn"] and _p1["withdrawn"] and _p0["withdrawal_window"] == _p1["withdrawal_window"]
   and _p1["withdrawal_window"]["predictions"] == 80 and _p1["withdrawal_window"]["before"] == "2026-10-19",
   "🔴 P is WITHDRAWN on the weeks before 2026-10-19 alone, with scored_from at 10-19 or moved to 11-02",
   (_p0["withdrawn"], _p1["withdrawn"], _p1["withdrawal_window"]))
ck(_p1["history"]["predictions"] == 320 and _p1["history"]["mean_d"] > 0,
   "   ...though the report's history (weeks before 11-02) now holds its good weeks too: a window that "
   "followed scored_from would have kept it", _p1["history"])
eq((_p1["counted"]["predictions"], _p1["scored"]["predictions"]), (0, 0),
   "🔴 ...and a withdrawn challenger is never counted or scored")
ck("withdrawal_window" not in contest("E", P_FITS), "   ...and only P and T carry a withdrawal window")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 league(): REGISTRATION DECIDES ENTRY AND k; A SWITCH RESTARTS ONLY THE EIGHT")
# ══════════════════════════════════════════════════════════════════════
T4 = tree()


def league(lg, now, prev=None, fits=None):
    saved = (R.Fits, R.challenger_fits, FC.attach)
    R.Fits = lambda rows, feat: CHAMP
    R.challenger_fits = lambda rows, n, lg, root=None: Planted((fits or {}).get(n, BOTH))
    FC.attach = lambda *a, **k: None
    try:
        doc = R.league(lg, T4, now, rows=[], prev=prev, added={n: "2025-01-01" for n in FC.CHALLENGERS})
    finally:
        R.Fits, R.challenger_fits, FC.attach = saved
    return doc, {x["name"]: x for x in doc["challengers"]}


_doc, _by = league("nfl", NOW)
eq((_doc["floor"], _doc["champion_since"]), (300, None), "the report carries the floor; no switch yet")
eq({n: (x["registered"], x["counts"], x["counted"]["predictions"]) for n, x in _by.items() if n in ("E", "S", "CL")},
   {"E": ("2026-10-19", "all", 600), "S": ("2026-10-19", "scored", 300), "CL": ("2026-11-02", "all", 900)},
   "🔴 on Monday 11-02: E and CL (registered 11-02, from §3f) count every week; S only its scored weeks")
_wed = datetime.datetime(2026, 10, 28, 12, 0, tzinfo=UTC)
_d2, _b2 = league("nfl", _wed)
eq((_b2["CL"]["counted"]["predictions"], _b2["CL"]["verdict"], _b2["E"]["counted"]["predictions"]),
   (0, "NOT YET MEASURABLE", 600),
   "🔴 a run on Wednesday 10-28 counts nothing for CL, which enters the contest on 11-02")
_k = sum(1 for x in _d2["challengers"] if x["registered"] and not x.get("withdrawn"))
ck(_k == 13 and all(x.get("alpha") == R.ALPHA / 13 for x in _d2["challengers"]),
   "🔴 k is unchanged (§2 to §3f): every registered, not withdrawn challenger, CL included, so 0.01 / 13",
   (_k, {x["name"]: x.get("alpha") for x in _d2["challengers"]}))
_d3, _b3 = league("nfl", NOW, prev={"champion": "E", "champion_since": None})
eq(_d3["champion_since"], "2026-11-02", "a champion switch is noticed: champion_since is 11-02")
eq({n: (_b3[n]["scored_from"], _b3[n]["counted"]["predictions"]) for n in ("CL", "AV", "S", "WL")},
   {"CL": ("2026-11-02", 900), "AV": ("2026-11-02", 0), "S": ("2026-11-02", 0), "WL": ("2026-11-02", 600)},
   "🔴 after the switch the eighteen keep every week (CL 900, WL 600) and the eight restart (AV, S: 0)")
_d4, _b4 = league("ncaaf", NOW, prev={"champion": "TS", "champion_since": None}, fits={"P": P_FITS})
ck(_b4["P"]["withdrawn"] and _b4["P"]["scored_from"] == "2026-11-02"
   and _b4["P"]["withdrawal_window"]["before"] == "2026-10-19" and _b4["P"]["verdict"] == "WITHDRAWN",
   "🔴 league(): P stays WITHDRAWN on the weeks before 2026-10-19 after a switch moved its scored_from",
   _b4["P"].get("withdrawal_window"))

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 MORE THAN ONE WINS: ALL REPORTED, ONE BRANCH, TO THE LARGEST MEAN d")
# ══════════════════════════════════════════════════════════════════════


def win(name, mean_d, p):
    return {"name": name, "what": "x", "verdict": "WINS", "alpha": 0.01 / 13, "counts": "all",
            "registered": "2026-10-19",
            "counted": {"predictions": 600, "differing": 600, "games": 300, "mean_d": mean_d, "p": p,
                        "champion_log_loss": 0.68, "challenger_log_loss": 0.67}}


eq([x["name"] for x in R.branch_order([win("E", 0.01, 1e-5), win("RS", 0.03, 1e-4), win("IN", 0.02, 1e-6),
                                       {"name": "S", "verdict": "NOT YET"}])],
   ["RS", "IN", "E"], "🔴 the order is by mean d, largest first (a NOT YET is not in it)")
eq([x["name"] for x in R.branch_order([win("RS", 0.02, 1e-4), win("IN", 0.02, 1e-6)])], ["IN", "RS"],
   "🔴 ...a tie on mean d goes to the smaller p")
eq([x["name"] for x in R.branch_order([win("WL", 0.02, 1e-4), win("E", 0.02, 1e-4), win("RS", 0.02, 1e-4)])],
   ["E", "RS", "WL"], "🔴 ...and a tie on both to the earlier name in fb_challengers.CHALLENGERS")
T5 = tree()
_pushed = []
_saved = (R.league, R.push_branch, IB.auto)
try:
    R.league = lambda lg, root, now, prev=None, added=None: {"league": lg, "challengers": (
        [win("E", 0.01, 1e-5), win("RS", 0.03, 1e-4), win("IN", 0.02, 1e-6),
         {"name": "S", "what": "fewer inputs", "verdict": "NOT YET"}] if lg == "nfl" else [])}
    R.push_branch = lambda lg, name, day, root=None, run=None: (
        _pushed.append((lg, name)) or ("fb/champion-%s-%s-%s" % (lg, name, day), True))
    IB.auto = lambda *a, **k: {"state": "waiting"}
    R.weekly(root=T5, now=NOW, run=None)
finally:
    R.league, R.push_branch, IB.auto = _saved
_w = {x["name"]: x for x in json.load(open(os.path.join(T5, "data", "nfl", "latest", "fb-refit.json"),
                                           encoding="utf-8"))["challengers"]}
eq(_pushed, [("nfl", "RS")], "🔴 weekly() pushes ONE branch, for RS (mean d 0.03), and none for the others")
eq({n: (_w[n].get("branch"), _w[n].get("branch_pushed"), _w[n].get("outranked_by"), _w[n]["verdict"])
    for n in ("E", "RS", "IN")},
   {"E": (None, False, "RS", "WINS"), "RS": ("fb/champion-nfl-RS-2026-11-02", True, None, "WINS"),
    "IN": (None, False, "RS", "WINS")},
   "🔴 ...and every WINS is reported: E and IN say the branch went to RS")

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 THE MONDAY EMAIL SAYS THE NEW RULE IN SAM'S WORDS, FLOOR FROM THE REPORT")
# ══════════════════════════════════════════════════════════════════════
DOC = {"built_at": "2026-11-02T09:50:00Z", "miss": {"games": 0}, "scoreboard": {}, "line_moves": {},
       "floor": 250, "challengers": [
           dict(R.verdicts([dict(e2)])[0], name="E", what="EPA"),
           {"name": "S", "what": "fewer inputs", "verdict": "NOT YET MEASURABLE", "counts": "scored",
            "registered": "2026-10-19", "counted": {"predictions": 42, "differing": 40}},
           {"name": "CL", "what": "class vs good teams", "verdict": "NOT YET MEASURABLE", "counts": "all",
            "registered": "2026-11-09", "counted": {"predictions": 0, "differing": 0}}]}
_sum = S.refit_summary(DOC, "NFL", NOW)
ck("Challenger E (EPA): 400 counted predictions (last season and this season), 101 of them different from "
   "the current model's (250 needed), not yet measurable." in _sum,
   "🔴 one of the eighteen: counted predictions (last season and this season), how many differ, the floor", _sum)
ck("Challenger S (fewer inputs): 42 predictions scored since registration, 40 of them different from the "
   "current model's (250 needed), not yet measurable." in _sum,
   "🔴 one of the eight: predictions scored since registration", _sum)
ck("Challenger CL (class vs good teams): it enters the contest on 2026-11-09, so nothing is counted yet, "
   "not yet measurable." in _sum, "🔴 one not yet registered says when it enters", _sum)
ck("300" not in _sum and "250 needed" in _sum,
   "🔴 the floor is the report's (fb_refit.MIN_SCORED, stored as `floor`), never a number in status.py", _sum)
_wd = {"built_at": "2026-11-02T09:50:00Z", "miss": {"games": 0}, "scoreboard": {}, "line_moves": {},
       "floor": 300, "challengers": list(_w.values())}
_sum = S.refit_summary(_wd, "NFL", NOW)
ck("Challenger E (x): 600 counted predictions (last season and this season), 600 of them different from the "
   "current model's (300 needed), it WINS; the one branch went to RS, which beat the current model by more." in _sum,
   "🔴 a WINS that did not get the branch says where it went", _sum)
_needs = S.refit_wins(_wd, "NFL")
ck(len(_needs) == 1, "🔴 only the branch's WINS goes under \"Needs you\" (one merge for Sam)",
   [w for w, _c in _needs])
ck(_needs and _needs[0][0].startswith("NFL challenger RS (x) beat the current game model: log loss 0.6700 against "
                                      "0.6800 over 600 counted predictions (last season and this season) in 300 "
                                      "games")
   and "(E, IN also won this week; the one branch goes to the biggest gain, RS)" in _needs[0][0]
   and "compare/main...fb/champion-nfl-RS-2026-11-02" in " ".join(_needs[0][1]),
   "🔴 ...naming the other winners, with the merge link to RS's own branch", _needs)
_s8 = dict(win("S", 0.02, 1e-6), counts="scored", branch="fb/champion-nfl-S-2026-11-02")
ck(S.refit_wins({"challengers": [_s8]}, "NFL")[0][0].endswith(
    "over 600 predictions scored since registration in 300 games, one-sided p = 1e-06 (it needed under 0.0007692)"),
   "🔴 one of the eight's WINS says its predictions were scored since registration",
   S.refit_wins({"challengers": [_s8]}, "NFL"))

# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 ON REAL FITS: AN INPUT THAT IS ALL ZEROS (WX BEFORE STORED WEATHER) DIFFERS NOWHERE")
# ══════════════════════════════════════════════════════════════════════
# §3g: "one equal to the champion's carries no evidence, e.g. WX and WXC before stored weather".
#    A planted league, fitted by fb_model.fit itself: WX's wind is missing (0) on every row it trains
#    on, so its predictions are the champion's to the last bit, even on the last week's rows that
#    do carry a forecast; E's EPA number is real on every row, so all of its predictions differ.
import random  # noqa: E402
_rng = random.Random(73)
_TM = ["T%d" % i for i in range(8)]
ROWS = []
for _w in range(22):
    _day = (datetime.date(2025, 9, 7) + datetime.timedelta(weeks=_w)).isoformat()
    for _j in range(8):
        _h, _a = _TM[_j], _TM[(_j + 1 + _w) % 8] if _TM[(_j + 1 + _w) % 8] != _TM[_j] else _TM[(_j + 2) % 8]
        _om, _ot = _rng.gauss(0, 6), _rng.gauss(45, 5)
        _hs = max(0, int(round(_ot / 2 + _om / 2 + _rng.gauss(0, 9))))
        _as = max(0, int(round(_ot / 2 - _om / 2 + _rng.gauss(0, 9))))
        ROWS.append({"id": "r%d_%d" % (_w, _j), "lg": "nfl", "season": 2025, "day": _day, "home": _h,
                     "away": _a, "final": True, "hs": _hs, "as": _as, "M": 2.5, "T": 44.5, "pml": 0.55,
                     "sig": {"neutral": 0.0, "dome": float(_j % 3 == 0), "own_m": _om, "own_t": _ot,
                             "h2h_m": None, "h2h_t": None, "form_m": _rng.gauss(0, 5), "form_t": None,
                             "def": None, "poss": _rng.gauss(0, 0.1), "out": None, "vac_h": None, "vac_a": None,
                             "epa_m": _om + _rng.gauss(0, 4), "wx_wind": 12.0 if _w == 21 else None}})
_T7 = tree()
_champ7 = R.Fits(ROWS, FM.features)
_wx = R.contest(ROWS, _champ7, "WX", "2026-10-19", "2026-10-19", fits=R.challenger_fits(ROWS, "WX", "nfl", _T7))
_e7 = R.contest(ROWS, _champ7, "E", "2026-10-19", "2026-10-19", fits=R.challenger_fits(ROWS, "E", "nfl", _T7))
ck(_wx["counted"]["predictions"] >= 16 and _wx["counted"]["differing"] == 0
   and any(r["sig"]["wx_wind"] for r in ROWS if FM.monday(r["day"]) in {w for (w, _m) in _champ7.models}),
   "🔴 WX trained on an all-zero wind column: every counted prediction equals the champion's (0 differ), "
   "a forecast on the row predicted included", _wx["counted"])
ck(_e7["counted"]["predictions"] >= 32 and _e7["counted"]["differing"] == _e7["counted"]["predictions"],
   "🔴 ...while E, whose input is real, differs on every one", _e7["counted"])
