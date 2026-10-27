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
`[Sam, 2026-10-27]` §3h, *"Yes: keep 'differs' exact, and make P and T's withdrawal permanent."*:
a challenger withdrawn once stays withdrawn in every later report (§8).

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
# @vacuity 🔴 ...and for one of the eight only its differing SCORED predictions (review, 2026-10-26)
#   file: fb_refit.py
#   find:                           differing=sum(1 for _wk, _pair, df in counted if df))
#   with:                           differing=sum(1 for _wk, _pair, df in (preds if counted else []) if df))
#
# @vacuity 🔴 ...while the test runs over every counted prediction, equal ones included
#   file: fb_refit.py
#   find:     out["counted"] = dict(test([pair for _wk, pair, _df in counted], exact=True),
#   with:     out["counted"] = dict(test([pair for _wk, pair, df in counted if df], exact=True),
#
# @vacuity 🔴 ...and keeps its unrounded mean d and p for §3g's order (review 2, 2026-10-27)
#   file: fb_refit.py
#   find:     out["counted"] = dict(test([pair for _wk, pair, _df in counted], exact=True),
#   with:     out["counted"] = dict(test([pair for _wk, pair, _df in counted], exact=False),
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
#   find:         return (-c.get("mean_d_exact", c["mean_d"]), c.get("p_exact", c["p"]), order.index(x["name"]))
#   with:         return (c.get("mean_d_exact", c["mean_d"]), c.get("p_exact", c["p"]), order.index(x["name"]))
#
# @vacuity 🔴 ...a tie on mean d, the smaller p
#   file: fb_refit.py
#   find:         return (-c.get("mean_d_exact", c["mean_d"]), c.get("p_exact", c["p"]), order.index(x["name"]))
#   with:         return (-c.get("mean_d_exact", c["mean_d"]), -c.get("p_exact", c["p"]), order.index(x["name"]))
#
# @vacuity 🔴 ...then the earlier name in fb_challengers.CHALLENGERS
#   file: fb_refit.py
#   find:         return (-c.get("mean_d_exact", c["mean_d"]), c.get("p_exact", c["p"]), order.index(x["name"]))
#   with:         return (-c.get("mean_d_exact", c["mean_d"]), c.get("p_exact", c["p"]), -order.index(x["name"]))
#
# @vacuity 🔴 ...on the UNROUNDED mean d and p, never the 6 decimals the report prints (review 2, 2026-10-27)
#   file: fb_refit.py
#   find:         return (-c.get("mean_d_exact", c["mean_d"]), c.get("p_exact", c["p"]), order.index(x["name"]))
#   with:         return (-c["mean_d"], c["p"], order.index(x["name"]))
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
# @vacuity 🔴 ...and one registered on the report's own day has entered (league() counts it)
#   file: status.py
#   find:     if x.get("registered") and x["registered"] > str(doc.get("built_at") or "")[:10]:
#   with:     if x.get("registered") and x["registered"] >= str(doc.get("built_at") or "")[:10]:
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
#
# @vacuity 🔴 ...says "went to" only when the winner holds its own branch (review, 2026-10-26)
#   file: status.py
#   find:             if own_branch(br, t):
#   with:             if True:
#
# @vacuity 🔴 ...with a champion named, says so, never "the league's one switch is X's" (review 2, 2026-10-27)
#   file: status.py
#   find:             elif not br:                      # fb_refit pushes nothing while the league names a champion
#   with:             elif False:                      # fb_refit pushes nothing while the league names a champion
#
# @vacuity 🔴 ...and says when the older branch on GitHub is the outranked challenger's own (review 2)
#   file: status.py
#   find:             elif own_branch(br, x["name"]):
#   with:             elif False:
#
# @vacuity 🔴 ...the "Needs you" line says "the one branch goes to" only when it went (review 2)
#   file: status.py
#   find:             if not own_branch(x.get("branch"), x["name"]):
#   with:             if False:
#
# @vacuity 🔴 ...and "the biggest gain" only when it was, never on a tie (review 2)
#   file: status.py
#   find:             elif why == "beat the current model by more":
#   with:             elif True:
#
# @vacuity 🔴 ...a tie on gain names the smaller p as the reason (review 2)
#   file: status.py
#   find:     if p1 is not None and p2 is not None and p1 < p2:
#   with:     if False:
#
# @vacuity 🔴 ...and a lead only past the printed decimals is said to be one (review 2)
#   file: status.py
#   find:             " (by less than the 6 decimals the report prints)" if c1.get("mean_d") == c2.get("mean_d") else "")
#   with:             "" if True else "")
#
# @vacuity 🔴 one of the eight, after a champion switch, counts "since <the restart>", never "since registration"
#   file: status.py
#   find:     if x.get("counts") != "all" and (x.get("scored_from") or "") > (x.get("registered") or "9"):
#   with:     if False:
#
# @vacuity 🔴 ...and the "Needs you" line prints the COUNTED numbers, never the scored ones
#   file: status.py
#   find:         s = x.get("counted") or x["scored"]
#   with:         s = x.get("scored") or x["counted"]
#
# @vacuity 🔴 §3h [Sam, 2026-10-27]: a carried withdrawal is never counted or scored
#   file: fb_refit.py
#   find:     if c["withdrawable"] and withdrawn_since:        # §3h: withdrawn once, withdrawn for good
#   with:     if c["withdrawable"] and withdrawn_since and False:
#
# @vacuity 🔴 §3h: ...and keeps the day it was first withdrawn
#   file: fb_refit.py
#   find:         if n in gone:                                 # kept on a week it could not be built too
#   with:         if False:
#
# @vacuity 🔴 §3h: a first withdrawal is dated the report's own day
#   file: fb_refit.py
#   find:             x["withdrawn_since"] = today              # §3h: first withdrawn in this report
#   with:             pass
#
# @vacuity 🔴 §3h: a withdrawal from a report before §3h (no day) is carried, dated that report's day
#   file: fb_refit.py
#   find:             out[x["name"]] = x.get("withdrawn_since") or day
#   with:             out[x["name"]] = x.get("withdrawn_since")
#
# @vacuity 🔴 §3h: only P and T are carried
#   file: fb_refit.py
#   find:         if c and c["league"] == lg and c["withdrawable"] and x.get("withdrawn") is True:
#   with:         if c and c["league"] == lg and x.get("withdrawn") is True:
#
# @vacuity 🔴 §3h: never from another league's report
#   file: fb_refit.py
#   find:     if not isinstance(prev, dict) or prev.get("league") not in (None, lg):
#   with:     if not isinstance(prev, dict):
#
# @vacuity 🔴 §3h: the email says a withdrawal is for good, and since when
#   file: status.py
#   find:             "WITHDRAWN": ("withdrawn for good on %s, it was worse on past games" % x["withdrawn_since"]
#   with:             "WITHDRAWN": ("withdrawn, it was worse on past games"
#
# @vacuity 🔴 §3h: "differs" stays exact, with no minimum size
#   file: fb_refit.py
#   find:                 preds.append((wk, (loss(a[gid][0], y), loss(p_x, y), gid), p_x != a[gid][0]))
#   with:                 preds.append((wk, (loss(a[gid][0], y), loss(p_x, y), gid), abs(p_x - a[gid][0]) > 1e-6))
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
# `[review, 2026-10-26]` §3g's floor for one of the eight counts its differing SCORED predictions
#    only: S with 600 history and 150 scored predictions, every one better than the champion's and
#    different from it, is NOT YET MEASURABLE (150 < 300), never a WINS on its history's count.
FLUKE = market_set([(HIST, GOOD, 200), (LIVE, GOOD, 50)])
_sf = R.verdicts([contest("S", FLUKE)])[0]
eq((_sf["history"]["predictions"], _sf["counted"]["predictions"], _sf["counted"]["differing"], _sf["verdict"]),
   (600, 150, 150, "NOT YET MEASURABLE"),
   "🔴 S (one of the eight), 600 history + 150 scored predictions all differing: the floor counts the 150, "
   "NOT YET MEASURABLE")
_ef = R.verdicts([contest("E", FLUKE)])[0]
eq((_ef["counted"]["predictions"], _ef["counted"]["differing"], _ef["verdict"]), (500, 500, "WINS"),
   "   ...while E on the same games (its two markets) counts all 500 and WINS")
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
# `[review, 2026-10-26]` the email says what league() did: CL registers 2026-11-02 and the report
#    is built that morning, so it has entered and its 900 are counted (never "enters on 11-02").
_cl = S.refit_summary(_doc, "NFL", NOW)
ck(_doc["built_at"][:10] == "2026-11-02"
   and ("Challenger CL (%s): 900 counted predictions (last season and this season), 900 of them different "
        "from the current model's (300 needed)" % FC.CHALLENGERS["CL"]["what"]) in _cl
   and "enters the contest on 2026-11-02" not in _cl,
   "🔴 the email agrees with league(): CL, registered on the report's own day, has entered (900 counted)", _cl)
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
# `[review, 2026-10-26]` A league that already names a CHAMPION pushes no branch at all (the real
#    push_branch, which returns before any git): E is still outranked by RS, and nobody holds a branch.
T5b = tree()
_saved = (R.league, IB.auto, dict(FM.CHAMPION))
try:
    R.league = lambda lg, root, now, prev=None, added=None: {"league": lg, "challengers": (
        [win("E", 0.01, 1e-5), win("RS", 0.03, 1e-4)] if lg == "nfl" else [])}
    IB.auto = lambda *a, **k: {"state": "waiting"}
    FM.CHAMPION["nfl"] = "IN"
    R.weekly(root=T5b, now=NOW, run=None)
finally:
    R.league, IB.auto = _saved[0], _saved[1]
    FM.CHAMPION.clear()
    FM.CHAMPION.update(_saved[2])
_wc = {x["name"]: x for x in json.load(open(os.path.join(T5b, "data", "nfl", "latest", "fb-refit.json"),
                                            encoding="utf-8"))["challengers"]}
eq({n: (_wc[n].get("branch"), _wc[n].get("outranked_by"), bool(_wc[n].get("needs_sam"))) for n in ("E", "RS")},
   {"E": (None, "RS", False), "RS": (None, None, True)},
   "🔴 a league that already names a champion: no branch for anyone; RS (the larger gain) carries NEEDS SAM")

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
# `[review, 2026-10-26]` "the one branch went to RS" only when RS holds its own branch. With a
#    champion already named (weekly() above) or an older champion branch on GitHub, none was pushed.
_nb = S.refit_summary(dict(_wd, challengers=list(_wc.values())), "NFL", NOW)
# `[2026-10-27, review 2]` ~~"RS beat the current model by more, so the league's one switch is RS's, and no
#    branch was pushed for it this week."~~: with a champion named no switch to RS can happen.
ck("it WINS; RS beat the current model by more and ranks first, but no branch was pushed: the league already "
   "has a champion." in _nb and "went to RS" not in _nb and "one switch" not in _nb,
   "🔴 a named champion pushed no branch: the email never says the branch went to RS, nor that the league's "
   "one switch is RS's", _nb)
_nw = S.refit_wins(dict(_wd, challengers=list(_wc.values())), "NFL")
ck(len(_nw) == 1 and "(E also won this week; RS beat the current model by more, and no branch was pushed). "
   "NEEDS SAM: IN is already the NFL champion" in _nw[0][0] and "the one branch goes to" not in _nw[0][0],
   "🔴 ...and its \"Needs you\" line never says \"the one branch goes to\" RS (review 2, 2026-10-27)", _nw)
_older = [dict(win("E", 0.01, 1e-5), branch=None, branch_pushed=False, outranked_by="RS"),
          dict(win("RS", 0.03, 1e-4), branch="fb/champion-nfl-WX-2026-10-26", branch_pushed=False)]
_ob = S.refit_summary(dict(_wd, challengers=_older), "NFL", NOW)
ck("it WINS; RS beat the current model by more and ranks first, but no branch was pushed for it: an older "
   "champion branch, fb/champion-nfl-WX-2026-10-26, is still on GitHub." in _ob
   and "went to RS" not in _ob and "one switch" not in _ob,
   "🔴 ...nor when an older champion branch (WX's) is still on GitHub", _ob)
_ow = S.refit_wins(dict(_wd, challengers=_older), "NFL")
ck(len(_ow) == 1 and "(E also won this week; RS beat the current model by more, and no branch was pushed), "
   "but an older champion branch, fb/champion-nfl-WX-2026-10-26, is still on GitHub" in _ow[0][0]
   and "the one branch goes to" not in _ow[0][0],
   "🔴 ...and its \"Needs you\" line never says the branch goes to RS (review 2, 2026-10-27)", _ow)
# `[2026-10-27, review 2]` the older branch is the OUTRANKED challenger's own (E's from last Monday): the
#    email says so, never that the league's one switch is RS's while its clicks offer E's branch
_olde = [dict(_older[0]), dict(_older[1], branch="fb/champion-nfl-E-2026-10-26")]
_oe = S.refit_summary(dict(_wd, challengers=_olde), "NFL", NOW)
ck("it WINS; RS beat the current model by more and ranks first this week, so no branch was pushed for it: E's "
   "own branch from an earlier Monday, fb/champion-nfl-E-2026-10-26, is still on GitHub." in _oe
   and "one switch" not in _oe,
   "🔴 the older branch on GitHub is E's own: E's line says so", _oe)
_mine = [_older[0], dict(_older[1], branch="fb/champion-nfl-RS-2026-10-26")]
ck("it WINS; the one branch went to RS, which beat the current model by more."
   in S.refit_summary(dict(_wd, challengers=_mine), "NFL", NOW),
   "   ...and RS's own branch from an earlier Monday, still unmerged, is where it went")
# `[2026-10-27, review 2]` a tie on gain: the branch goes to the smaller p, and the email says THAT, never
#    "by more" or "the biggest gain"
_tie = [dict(win("E", 0.02, 1e-4), branch=None, branch_pushed=False, outranked_by="RS"),
        dict(win("RS", 0.02, 1e-6), branch="fb/champion-nfl-RS-2026-11-02", branch_pushed=True)]
eq([x["name"] for x in R.branch_order([dict(x, verdict="WINS") for x in _tie])], ["RS", "E"],
   "   (a tie on mean d: fb_refit orders RS, the smaller p, first)")
_ts = S.refit_summary(dict(_wd, challengers=_tie), "NFL", NOW)
_tw = S.refit_wins(dict(_wd, challengers=_tie), "NFL")
ck("it WINS; the one branch went to RS, which beat the current model by the same amount, with the smaller p."
   in _ts and "by more" not in _ts
   and "(E also won this week; the one branch goes to RS, which beat the current model by the same amount, "
       "with the smaller p)" in _tw[0][0] and "biggest gain" not in _tw[0][0],
   "🔴 a tie on gain says the smaller p decided, never \"by more\" or \"the biggest gain\"", (_ts, _tw))
# `[2026-10-27, review 2]` mean d's that print the same (0.02) but differ unrounded: §3g's "largest mean d"
#    is the unrounded one (fb_refit.branch_order reads `mean_d_exact`), and the email says the lead is real
#    but smaller than the printed decimals
_ex = [dict(win("E", 0.02, 0.0), branch=None, branch_pushed=False, outranked_by="RS"),
       dict(win("RS", 0.02, 0.0), branch="fb/champion-nfl-RS-2026-11-02", branch_pushed=True)]
_ex[0]["counted"].update(mean_d_exact=0.0199996, p_exact=0.0)
_ex[1]["counted"].update(mean_d_exact=0.0200004, p_exact=0.0)
eq([x["name"] for x in R.branch_order([dict(x, verdict="WINS") for x in _ex])], ["RS", "E"],
   "🔴 fb_refit: RS's unrounded mean d (0.0200004) beats E's (0.0199996) though both print 0.02 (by the "
   "rounded ones E's earlier name took the branch)")
ck("the one branch went to RS, which beat the current model by more (by less than the 6 decimals the report "
   "prints)." in S.refit_summary(dict(_wd, challengers=_ex), "NFL", NOW),
   "🔴 ...and the email says the lead is past the printed decimals",
   S.refit_summary(dict(_wd, challengers=_ex), "NFL", NOW))
_ce = contest("E", market_set([(HIST, GOOD, 200), (LIVE, GOOD, 100)]))["counted"]
ck(_ce.get("mean_d_exact") is not None and round(_ce["mean_d_exact"], 6) == _ce["mean_d"]
   and _ce["mean_d_exact"] != _ce["mean_d"] and _ce.get("p_exact") is not None,
   "🔴 contest() stores the counted mean d and p unrounded beside the printed ones (the order's input)", _ce)
# `[2026-10-27, review 2]` after a champion switch one of the eight counts from the restart, and says so
_sw = dict(win("S", 0.02, 1e-6), counts="scored", scored_from="2026-10-26", branch="fb/champion-nfl-S-2026-11-02")
_sws = S.refit_summary(dict(_wd, challengers=[_sw]), "NFL", NOW)
ck("600 predictions scored since 2026-10-26 (the count restarted with the new champion)" in _sws
   and "since registration" not in _sws
   and "over 600 predictions scored since 2026-10-26 (the count restarted with the new champion) in 300 games"
   in S.refit_wins({"challengers": [_sw]}, "NFL")[0][0],
   "🔴 S after a champion switch: \"scored since 2026-10-26\", never \"since registration\" (registered "
   "2026-10-19; the weeks between were not counted)", _sws)
# `[review, 2026-10-26]` the "Needs you" line prints the COUNTED predictions and their p, never the
#    scored ones a real report also carries (here 40 at p 0.3).
_cs = dict(win("E", 0.02, 1e-4), branch="fb/champion-nfl-E-2026-11-02",
           scored={"predictions": 40, "games": 20, "mean_d": 0.01, "p": 0.3, "p_wrong_way": 0.7,
                   "champion_log_loss": 0.69, "challenger_log_loss": 0.70})
_cl6 = S.refit_wins({"challengers": [_cs]}, "NFL")
ck(_cl6 and "log loss 0.6700 against 0.6800 over 600 counted predictions (last season and this season) in 300 "
            "games, one-sided p = 0.0001 (it needed under 0.0007692)" in _cl6[0][0],
   "🔴 a WINS with both blocks: the line reads the 600 counted at p 0.0001, not the 40 scored at p 0.3", _cl6)

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

# ══════════════════════════════════════════════════════════════════════
section("8. 🔴 §3h [Sam, 2026-10-27]: A WITHDRAWAL IS PERMANENT; \"DIFFERS\" STAYS EXACT")
# ══════════════════════════════════════════════════════════════════════
# *"Yes: keep 'differs' exact, and make P and T's withdrawal permanent."* Recomputed each Monday
#    against the champion of the day, a P withdrawn today came back after a switch to a champion
#    that did worse on those weeks, and was counted on the very weeks that withdrew it (review 2).
_sec3h = re.sub(r"\s+", " ", _spec[_spec.find("\n## 3h. "):_spec.find("\n## 4. ")])
ck("stays WITHDRAWN in every later weekly report of that league, whoever the champion is" in _sec3h
   and "by any amount. There is no minimum size." in _sec3h,
   "§3h is in the frozen spec: a withdrawal stays for good, and \"differs\" is exact", _sec3h[:300])
NEXT = NOW + datetime.timedelta(days=7)                        # Monday 11-09
GOOD_P = market_set([(HIST, GOOD, 40), (LIVE, GOOD, 120)], ("spread", "moneyline"))
_a8, _ba8 = league("ncaaf", NOW, fits={"P": P_FITS})
eq((_ba8["P"]["verdict"], _ba8["P"].get("withdrawn_since")), ("WITHDRAWN", "2026-11-02"),
   "🔴 a first withdrawal is dated the report's own day")
ck("withdrawn_since" not in _ba8["T"] and not _ba8["T"]["withdrawn"],
   "   ...and a challenger never withdrawn carries no day", _ba8["T"])
_c8, _bc8 = league("ncaaf", NEXT, fits={"P": GOOD_P})
ck(not _bc8["P"]["withdrawn"] and _bc8["P"]["counted"]["predictions"] > 0,
   "   (control: judged afresh, the same P with good weeks before 10-19 is not withdrawn)", _bc8["P"])
_n8, _bn8 = league("ncaaf", NEXT, prev=_a8, fits={"P": GOOD_P})
eq((_bn8["P"]["withdrawn"], _bn8["P"]["verdict"], _bn8["P"].get("withdrawn_since"),
    _bn8["P"]["counted"]["predictions"], _bn8["P"]["scored"]["predictions"]),
   (True, "WITHDRAWN", "2026-11-02", 0, 0),
   "🔴 the next Monday reads last week's report: P stays WITHDRAWN from 11-02, never counted or scored, "
   "though this week's window alone would have kept it")
ck(_bn8["P"]["withdrawal_window"]["mean_d"] > 0,
   "   ...and this week's window is still reported, for information", _bn8["P"]["withdrawal_window"])
_k8 = sum(1 for x in _n8["challengers"] if x["registered"] and not x.get("withdrawn"))
ck(_k8 == sum(1 for x in _c8["challengers"] if x["registered"] and not x.get("withdrawn")) - 1
   and all(x.get("alpha") == R.ALPHA / _k8 for x in _n8["challengers"] if x["registered"]),
   "🔴 ...and never again in k: every bar is 0.01 / one fewer", (_k8, [x.get("alpha") for x in _n8["challengers"]]))
_s8, _bs8 = league("ncaaf", NEXT, prev=dict(_a8, champion="TS"), fits={"P": GOOD_P})
eq((_s8["champion_since"], _bs8["P"]["verdict"], _bs8["P"].get("withdrawn_since"), _bs8["P"]["counted"]["predictions"]),
   ("2026-11-09", "WITHDRAWN", "2026-11-02", 0),
   "🔴 review 2's case: after a champion switch, a withdrawn P does not come back")
_o8, _bo8 = league("ncaaf", NEXT, fits={"P": GOOD_P}, prev={
    "league": "ncaaf", "built_at": "2026-10-26T09:58:41Z", "champion": None, "champion_since": None,
    "challengers": [{"name": "P", "registered": "2026-10-19", "withdrawn": True, "verdict": "WITHDRAWN"}]})
eq((_bo8["P"]["verdict"], _bo8["P"].get("withdrawn_since")), ("WITHDRAWN", "2026-10-26"),
   "🔴 a withdrawal in a report from before §3h (no day of its own) is carried, dated that report's day")
_x8, _bx8 = league("ncaaf", NEXT, fits={"P": GOOD_P}, prev={
    "league": "nfl", "built_at": "2026-10-26T09:50:00Z", "challengers": [{"name": "P", "withdrawn": True}]})
ck(not _bx8["P"]["withdrawn"], "   ...but never from another league's report", _bx8["P"])
_e8, _be8 = league("nfl", NEXT, prev={
    "league": "nfl", "built_at": "2026-10-26T09:50:00Z", "challengers": [{"name": "E", "withdrawn": True}]})
ck(not _be8["E"]["withdrawn"] and "withdrawn_since" not in _be8["E"] and _be8["E"]["counted"]["predictions"] > 0,
   "   ...and only P and T can be carried (E has no withdrawal rule)", _be8["E"])
# A week P cannot be built (NOT APPLICABLE against some champion) never drops the withdrawal.
_saved8 = (R.Fits, R.challenger_fits, FC.attach, FC.applies, R.misses, R.line_moves, R.snapshots)
R.Fits = lambda rows, feat: CHAMP
R.challenger_fits = lambda rows, n, lg, root=None: Planted(GOOD_P if n == "P" else BOTH)
FC.attach = lambda *a, **k: None
FC.applies = lambda n, row: n != "P"
R.misses, R.line_moves, R.snapshots = (lambda rows: {}), (lambda rows, champ, snaps: {}), (lambda lg, root: {})
try:
    _na8 = R.league("ncaaf", T4, NEXT, rows=[{"season": 2025}], prev=_a8,
                    added={n: "2025-01-01" for n in FC.CHALLENGERS})
finally:
    R.Fits, R.challenger_fits, FC.attach, FC.applies, R.misses, R.line_moves, R.snapshots = _saved8
_pa8 = next(x for x in _na8["challengers"] if x["name"] == "P")
eq((_pa8["verdict"], _pa8["withdrawn"], _pa8.get("withdrawn_since")), ("NOT APPLICABLE", True, "2026-11-02"),
   "🔴 a NOT APPLICABLE week keeps the withdrawal and its day, outside k")
_after8, _baf8 = league("ncaaf", NEXT + datetime.timedelta(days=7), prev=_na8, fits={"P": GOOD_P})
eq((_baf8["P"]["verdict"], _baf8["P"].get("withdrawn_since")), ("WITHDRAWN", "2026-11-02"),
   "🔴 ...so the Monday after it is still WITHDRAWN from 11-02")
_em8 = S.refit_summary(_n8, "College", NEXT)
ck("Challenger P (%s): withdrawn for good on 2026-11-02, it was worse on past games." % FC.CHALLENGERS["P"]["what"]
   in _em8, "🔴 the Monday email says a withdrawal is for good, and since when", _em8)
# "Differs" stays exact: a prediction one part in a billion from the champion's differs.
_tiny = {mk: {g: (p + 1e-9, y, wk, r) for g, (p, y, wk, r) in v.items()} for mk, v in CHAMP.preds.items()}
_ty = contest("E", _tiny)
eq((_ty["counted"]["differing"], _ty["counted"]["predictions"]), (600, 600),
   "🔴 \"differs\" is exact: 600 predictions 1e-9 away from the champion's all differ (no minimum size)")
