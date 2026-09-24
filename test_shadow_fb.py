#!/usr/bin/env python3
"""
🔴🔴 THE SEASON DOES NOT CONTAIN ENOUGH ROWS, AND THE RATE IS A DISPLAY
CAP RATHER THAN A DATA LIMIT.

Break-even at -110 is 52.38%; a 3-point edge at p < 0.01 needs ~2,774
graded rows. The card grades ~111 a week — 25 weeks, finishing in the
2027 season. The BOARD prices 2,081 distinct combinations on one NFL day,
all of them already bought.

✅ MEASURED ON THIS BRANCH: one run grades **2,923** rows (1,331 NFL over
4 days, 1,592 college over 2) against **222** in the entire published
record. ⛔ For zero additional credits: a stored snapshot joined to box
scores the collector already fetches.

🔴 AND NOTHING REACHES THE PAGE. `carried` is the precedent — computed,
stored, never displayed.

⛔ WHAT THIS FILE REFUSES ABOVE EVERYTHING ELSE: a p-value on the raw row
count. The same player appears across six markets and the same game
across dozens of players, so correlated rows inflate significance — and
a naive p-value reports an edge that is not there, convincingly. That is
a pre-registration condition of T60, not a refinement.
"""

# ══════════════════════════════════════════════════════════════════════
# @vacuity the shadow record is never published where a reader can see it
#   file: daystore.py
#   find: FORBIDDEN = ("picks",)
#   with: FORBIDDEN = ()
#
# @vacuity the archive is DATED, never one cumulative file
#   file: daystore.py
#   find: day, hhmm = stamp(when)
#   with: day, hhmm = "all", "all"
#
# @vacuity the p-value is computed on the CLUSTERED n, never the raw n
#   file: shadow_fb.py
#   find: "p_value": one_sided_p(c["eff_wins"], c["eff_n"], BREAK_EVEN),
#   with: "p_value": one_sided_p(c["wins"], c["n"], BREAK_EVEN),
#
# @vacuity the dossier join is on `board_id`, never on a team name
#   file: shadow_fb.py
#   find: got = sec.get(src["board_id"])
#   with: got = sec.get(src["game"])
#   ⚠️ repointed 2026-09-18: the lookup moved to its own line when the
#      row gained `sections_absent`, and the harness said MALFORMED the
#      moment the old `find` stopped matching — exactly its job.
#
# @vacuity a complementary pair collapses to ONE observation
#   file: shadow_fb.py
#   find: return {"bound": len(rows) - doubled + pairs,
#   with: return {"bound": len(rows),
#
# @vacuity the pre-registered minimum n is EXACTLY the one Sam supplied
#   file: shadow_fb.py
#   find: T60_MIN_EFF_N = 2774
#   with: T60_MIN_EFF_N = 400
#
# @vacuity an UNGRADED wager is never counted as a loss
#   file: shadow_fb.py
#   find: rows = [r for r in rows if r.get("won") is not None]
#   with: rows = list(rows)   # voids and no-logs back in the denominator
#
# @vacuity the published card is still capped at TOP_N top plays
#   file: card_fb.py
#   find: TOP_N = 20
#   with: TOP_N = 19
#   ⚠️ ...and that mutation TIGHTENS rather than loosens, deliberately.
#      One published card sits EXACTLY at 20, so lowering the bar is the
#      only edit that can prove the comparison is live against the real
#      cards. ⛔ Loosening it could not: there is no committed card above
#      20 for a bigger cap to admit, so a raised bar would change
#      nothing and the "mutation" would prove nothing (rule 244).
# ══════════════════════════════════════════════════════════════════════

import datetime
import glob
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, copy_module, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("LEAGUE", "nfl")

import card_fb          # noqa: E402
import daystore         # noqa: E402
import shadow_fb        # noqa: E402

UTC = datetime.timezone.utc


def tree(lg="nfl"):
    """A throwaway repo carrying one league's data and the modules."""
    d = tempfile.mkdtemp(prefix="shadow-")
    shutil.copytree(os.path.join(ROOT, "data", lg), os.path.join(d, "data", lg))
    os.makedirs(os.path.join(d, "picks"), exist_ok=True)
    for f in glob.glob(os.path.join(ROOT, "picks", "fb-%s-*.json" % lg)):
        shutil.copy(f, os.path.join(d, "picks"))
    # ⛔ STRIPPED, so "a shadow file appeared" means THIS run made it.
    for p in glob.glob(os.path.join(d, "data", lg, "*", "shadow", "*")):
        os.remove(p)
    for m in ("shadow_fb", "daystore", "record_fb", "card_fb", "dossier_fb",
              "collect"):
        copy_module(m, d)
    return d


def snapshot_days(lg="nfl", root=None):
    """⚠️ DERIVED FROM THE ARTIFACT, never a literal date. The committed
    snapshots age, and a hard-coded day would redden this file on a
    calendar change rather than on a defect — the trap #51 fixed."""
    root = root or ROOT
    return sorted({p.split(os.sep)[-3] for p in
                   glob.glob(os.path.join(root, "data", lg, "*",
                                          "props-player", "*.json.gz"))})


def when_for(lg="nfl", root=None):
    """The clock that puts the committed snapshots inside the lookback."""
    days = snapshot_days(lg, root)
    if not days:
        return None
    last = datetime.datetime.strptime(days[-1], "%Y-%m-%d").replace(tzinfo=UTC)
    return last + datetime.timedelta(days=1, hours=12)


def load(p):
    return json.load(gzip.open(p, "rt"))


section("1. ⚠️ THE CLUSTERING IS THE POINT, SO IT IS DRIVEN FIRST")
# 🔴🔴 THE CASE THE BRIEF NAMES: a day where every row is the same game
#    must report an effective n near 1, NOT near the row count.
_one = [{"board_id": "g", "market": "m", "player": "p%d" % i, "line": 10,
         "side": "over", "won": i % 2 == 0} for i in range(60)]
_c1 = shadow_fb.cluster(_one)
ck(_c1["n"] == 60 and _c1["games"] == 1,
   "⚠️ the fixture really is 60 rows in one game", "Got %s" % _c1)
ck(_c1["eff_n"] <= 1,
   "🔴🔴 60 ROWS IN ONE GAME CARRY AN EFFECTIVE n OF %s, NOT 60"
   % _c1["eff_n"],
   "⛔ correlated rows inflate significance, and a p-value on 60 would "
   "report an edge that is not there. %s" % _c1["eff_basis"])
_many = [{"board_id": "g%d" % i, "market": "m", "player": "p", "line": None,
          "side": "yes", "won": i % 2 == 0} for i in range(60)]
_c2 = shadow_fb.cluster(_many)
ck(_c2["eff_n"] >= 55,
   "   ⚠️ ...while 60 rows in 60 games keep %s of them" % _c2["eff_n"],
   "⛔ AND THIS IS THE OTHER FAILURE. A correction that always shrinks is "
   "a correction that makes every question unanswerable. deff=%s"
   % _c2["deff"])
_pairs = ([{"board_id": "g%d" % i, "market": "m", "player": "p", "line": 10,
            "side": "over", "won": True} for i in range(30)]
          + [{"board_id": "g%d" % i, "market": "m", "player": "p",
              "line": 10, "side": "under", "won": False} for i in range(30)])
_c3 = shadow_fb.cluster(_pairs)
ck(_c3["complementary_pairs"] == 30 and _c3["pair_bound"] == 30,
   "🔴 30 Over/Under PAIRS carry 30 observations, not 60",
   "⛔ Over 60.5 and Under 60.5 on one player in one game are ONE coin "
   "flip read twice. Got %s pair(s), bound %s"
   % (_c3["complementary_pairs"], _c3["pair_bound"]))
ck(_c3["eff_n"] <= 30,
   "   ⛔ ...and the effective n is capped by that bound (%s)"
   % _c3["eff_n"],
   "🔴 FOUND BY DRIVING THE REAL BOARD: the variance estimator alone "
   "returned an effective n ABOVE the raw count, because both sides of "
   "every line pin each game's rate. A variance-only answer would have "
   "let a p-value run on raw n. Basis: %s" % _c3["eff_basis"])

section("2. ⛔⛔ NO p-VALUE IS EVER COMPUTED ON THE RAW n")
# ⚠️ DRIVEN ON A FIXTURE WHERE THE TWO ANSWERS DIFFER ENORMOUSLY, because
#    a fixture where they agree cannot tell them apart.
_hot = [{"board_id": "g%d" % (i // 40), "market": "m", "player": "p%d" % i,
         "line": 10, "side": "over", "won": i % 100 < 62} for i in range(400)]
_t = shadow_fb.t60(_hot, min_eff_n=1)
_raw = shadow_fb.one_sided_p(sum(1 for r in _hot if r["won"]), len(_hot),
                             shadow_fb.BREAK_EVEN)
_clu = shadow_fb.one_sided_p(_t["eff_wins"], _t["eff_n"],
                             shadow_fb.BREAK_EVEN)
ck(_raw is not None and _clu is not None and _raw < _clu / 10,
   "⚠️ the fixture separates the two answers (raw p=%.3g vs clustered "
   "p=%.3g)" % (_raw, _clu),
   "⛔ rule 67: a fixture where both p-values agree could not tell which "
   "one was reported")
ck(abs(_t["p_value"] - _clu) < 1e-12,
   "🔴🔴 THE REPORTED p IS THE CLUSTERED ONE (%.4g)" % _t["p_value"],
   "⛔ THIS IS THE PRE-REGISTRATION CONDITION. A p-value on the raw row "
   "count reports an edge that is not there and reports it "
   "convincingly. Got %.4g, raw would be %.4g" % (_t["p_value"], _raw))
ck(_t["p_value"] != _raw,
   "   ⛔ ...and it is NOT the raw-n one",
   "🔴 %.4g == the raw answer" % _t["p_value"])
ck(_t.get("p_value_on_raw_n") is None and bool(_t.get("p_value_on_raw_n_note")),
   "   ⚠️ ...and the document says out loud that the raw-n figure is "
   "absent on purpose",
   "⛔ an absent field reads as an oversight; a named absent field reads "
   "as a decision")

section("3. 🔴 T60's BAR IS NOT RE-DECIDED HERE")
ck(shadow_fb.T60_RATE == 0.554 and shadow_fb.T60_P == 0.01,
   "   the rate and alpha are the pre-registered ones (%.3f, %.2f)"
   % (shadow_fb.T60_RATE, shadow_fb.T60_P),
   "⛔ a bar re-decided after seeing data is not a pre-registered test")
# 🔴 SUPPLIED BY SAM ON 2026-09-18, NOT DERIVED HERE — one-sided,
#    α = 0.01, power 0.80, p0 = 0.5238, p1 = 0.554. ⛔ The check is on
#    the EXACT figure, so filling it in with anything else fails, and so
#    does emptying it back to None.
ck(shadow_fb.T60_MIN_EFF_N == 2774,
   "🔴🔴 ...AND THE MINIMUM n IS EXACTLY THE PRE-REGISTERED 2774",
   "⛔ a bar edited after seeing data is not a pre-registered test. It "
   "came from `claude/owed-tests.md`, which this repo does not contain, "
   "and was ASKED FOR rather than inferred. Got %r"
   % (shadow_fb.T60_MIN_EFF_N,))
_aw = shadow_fb.t60(_hot)
ck(_aw["verdict"] == "NOT YET MEASURABLE" and _aw["min_eff_n"] == 2774,
   "   ⛔ ...and a sample under it is NOT YET MEASURABLE — not a pass, "
   "not a fail",
   "🔴 %s at eff_n %s against %s"
   % (_aw["verdict"], _aw["eff_n"], _aw["min_eff_n"]))
ck(shadow_fb.t60(_hot, min_eff_n=1)["verdict"] in ("PASS", "FAIL"),
   "   ⚠️ ...and the verdict machinery still works once the floor is "
   "cleared",
   "⛔ rule 67: a verdict that can only ever say one thing proves nothing")
ck(shadow_fb.t60(_hot, min_eff_n=1)["eff_n"] <= len(_hot),
   "   ⛔ ...and the floor is compared against the EFFECTIVE n",
   "🔴 the power calculation assumes independent observations, which is "
   "what `eff_n` estimates. Comparing 2774 to the RAW count would be "
   "comparing a number to a different number that shares a name")

section("3a. 🔴🔴 AN UNGRADED WAGER IS NEVER COUNTED AS A LOSS")
# ══════════════════════════════════════════════════════════════════════
# ⛔ `this_reading` DIVIDED 541 WINS BY 1,374 WAGERS AND REPORTED 39.37%
# WHILE `pooled_all_rows` DIVIDED THE SAME WINS BY 1,245 GRADED ROWS AND
# REPORTED 43.45%. `[found in review, 2026-09-18]` Two blocks of one
# document, 4.1 points apart, about the same rows — because one counted
# every ungraded wager as a loss.
# 🔴 AND 14 OF THEM WERE VOIDS. CLAUDE.md, on `verify_record.py`: "Voids
# stay out of every denominator." The MLB grader enforces it; this file
# broke the same rule in a new place.
# ⚠️ A "no log for this player" row is not a loss either — it is a row we
# could not grade, and telling those apart is the whole reason `state`
# exists rather than a bare boolean.
# ✅ AND THE FILTER IS IN `cluster()`, NOT IN ITS CALLERS, so one block
# cannot be right while another is wrong. That is the class; the two
# call sites were the instance.
# ══════════════════════════════════════════════════════════════════════
_base = [{"board_id": "g%d" % (i // 4), "market": "m", "player": "p%d" % i,
          "line": 1, "side": "over", "won": i % 2 == 0, "state": "graded"}
         for i in range(40)]
_dirt = _base + [
    {"board_id": "gV", "market": "m", "player": "v", "line": 1,
     "side": "over", "won": None,
     "state": "void — on the roster but took no snaps"},
    {"board_id": "gN", "market": "m", "player": "n", "line": 1,
     "side": "over", "won": None, "state": "no log for this player"}]
_cb, _cd = shadow_fb.cluster(_base), shadow_fb.cluster(_dirt)
ck(_cb["n"] == 40 and _cb["rate"] == 0.5,
   "⚠️ the clean fixture is 40 graded rows at 50 pct", "Got %s" % _cb)
ck(_cd["n"] == _cb["n"],
   "🔴🔴 A VOID AND A NO-LOG ROW MOVE THE DENOMINATOR BY ZERO (%d -> %d)"
   % (_cb["n"], _cd["n"]),
   "⛔ THIS IS THE DEFECT. An ungraded wager is not a lost wager, and a "
   "VOID is barred from every denominator by CLAUDE.md")
ck(_cd["rate"] == _cb["rate"],
   "   ⛔ ...and the rate does not move either (%.5f)" % _cd["rate"],
   "🔴 counting 2 ungraded rows as losses drops 50.0%% to %.5f"
   % (_cb["wins"] / len(_dirt)))
ck(_cd.get("ungraded_excluded") == 2
   and set(_cd.get("ungraded_by_state") or {}) == {
       "void — on the roster but took no snaps",
       "no log for this player"},
   "   ⚠️ ...and what was dropped is NAMED, by state",
   "⛔ \"n went down\" with no reason beside it is how a denominator "
   "change gets mistaken for a data loss. ⚠️ `.get`-style on purpose: a "
   "guard that DIES reports \"an unknown number never ran\", which is "
   "strictly less than a guard that fails. Got %s"
   % _cd.get("ungraded_by_state"))
ck(_cd["games"] == _cb["games"],
   "   ⛔ ...and the ungraded rows do not add phantom clusters (%d)"
   % _cd["games"],
   "🔴 two rows in two new games would inflate the cluster count and "
   "therefore the effective n. Got %d vs %d"
   % (_cd["games"], _cb["games"]))

section("4. 🔴🔴 IT GRADES THE BOARD, ON REAL STORED DATA")
_days = snapshot_days("nfl")
ck(len(_days) >= 2,
   "⚠️ the repo carries props snapshots to grade (%d day(s))" % len(_days),
   "⛔ rule 67: every check below would pass over nothing. Days: %s"
   % _days)
_w = when_for("nfl")
_d4 = tree("nfl")
_rc4 = shadow_fb.build("nfl", data=os.path.join(_d4, "data", "nfl"),
                       root=_d4, log=lambda m: None, when=_w)
_files = glob.glob(os.path.join(_d4, "data/nfl/*/shadow/*.json.gz"))
ck(_rc4 == 0 and len(_files) == 1,
   "🔴 one run wrote ONE dated shadow file (rc=%s)" % _rc4,
   "⛔ Found %s" % [os.path.relpath(f, _d4) for f in _files])
_D = load(_files[0]) if _files else {}
_rows = _D.get("rows") or []
_graded = [r for r in _rows if r.get("won") is not None]
ck(len(_graded) >= 200,
   "🔴🔴 %d GRADED ROWS FROM ONE RUN — the card's whole record is 222"
   % len(_graded),
   "⛔ THIS IS THE POINT OF THE TASK. If the board stops yielding rows "
   "the backtest goes back to 25 weeks. Got %d of %d wager(s)"
   % (len(_graded), len(_rows)))
ck(_D.get("n_rows") == len(_rows),
   "   ⚠️ the document's own count matches its rows (%s)"
   % _D.get("n_rows"),
   "⛔ a stored count that disagrees with the thing it counts is the "
   "shape rule 166 is about")
_sum = sum(d["graded"] for d in _D.get("per_day") or [])
ck(_sum == len(_graded),
   "   ⚠️ ...and the per-day tallies reconcile (%d)" % _sum,
   "⛔ %d per-day vs %d rows" % (_sum, len(_graded)))
_games = len({r.get("board_id") for r in _graded})
ck(_games >= 5,
   "   ⚠️ ...across %d distinct game(s), so the clustering has clusters"
   % _games,
   "⛔ rule 67 — one game would make every clustered figure trivial")
_tr, _po = _D.get("this_reading") or {}, _D.get("pooled_all_rows") or {}
ck(_tr.get("n") == len(_graded) and _po.get("n") == len(_graded),
   "🔴🔴 BOTH BLOCKS COUNT THE GRADED ROWS, NOT THE WAGERS (%s / %s of "
   "%d)" % (_tr.get("n"), _po.get("n"), len(_graded)),
   "⛔ they disagreed by 4.1 points on the real artifact — 541/1374 "
   "against 541/1245 — because one counted every ungraded wager as a "
   "loss. %d wager(s) were handed in" % len(_rows))
ck(_tr.get("rate") == _po.get("rate"),
   "   ⛔ ...so they report the SAME rate (%.5f)" % (_tr.get("rate") or 0),
   "🔴 %s vs %s" % (_tr.get("rate"), _po.get("rate")))
ck(_tr.get("ungraded_excluded") == len(_rows) - len(_graded),
   "   ⚠️ ...and the excluded count reconciles (%s of %d wagers)"
   % (_tr.get("ungraded_excluded"), len(_rows)),
   "⛔ %s excluded vs %d ungraded"
   % (_tr.get("ungraded_excluded"), len(_rows) - len(_graded)))
note("   graded %d row(s) over %d game(s); effective n %s (%s)"
     % (len(_graded), _games, _po.get("eff_n"), _po.get("eff_basis")))
note("   excluded, by state: %s" % _tr.get("ungraded_by_state"))

section("5. ⛔ DATED AND WRITE-ONCE, AND NEVER INTO `picks/`")
_p = _files[0] if _files else ""
ck(re.search(r"/\d{4}-\d{2}-\d{2}/shadow/\d{4}\.json\.gz$", _p),
   "🔴 the path is `<date>/shadow/<HHMM>.json.gz`",
   "⛔ NEVER ONE CUMULATIVE FILE. Ledger rule 285: git cannot "
   "delta-compress a gzip, so a cumulative archive rewritten eight times "
   "a day costs 2,896 MiB a season against 5.17 MiB dated — 560x. "
   "Got %s" % _p)
_rc4b = shadow_fb.build("nfl", data=os.path.join(_d4, "data", "nfl"),
                        root=_d4, log=lambda m: None, when=_w)
_again = glob.glob(os.path.join(_d4, "data/nfl/*/shadow/*.json.gz"))
ck(len(_again) == 1 and load(_again[0])["built_at"] == _D["built_at"],
   "🔴🔴 ...AND A SECOND RUN LEAVES THE EARLIER READING EXACTLY AS IT WAS",
   "⛔ WRITE-ONCE. An archive a later run can rewrite is not an archive; "
   "it is `latest/` with a longer name. Found %s"
   % [os.path.relpath(f, _d4) for f in _again])
ck(not glob.glob(os.path.join(_d4, "picks", "**", "shadow*"),
                 recursive=True)
   and not glob.glob(os.path.join(_d4, "picks", "*shadow*")),
   "⛔ ...and nothing was written under `picks/`",
   "🔴 `picks/` is a permanent published record of what was ADVERTISED. "
   "A report about it is not one of them")
try:
    daystore.archive({}, os.path.join(_d4, "picks"), "shadow",
                     log=lambda m: None)
    _refused = False
except ValueError:
    _refused = True
ck(_refused,
   "   ⛔ ...and the writer REFUSES that path rather than relocating",
   "🔴 a tool that silently writes somewhere else is a tool nobody can "
   "audit")

section("6. 🔴 THE PAGE DOES NOT CHANGE")
_PAGE = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
# ⚠️ THE ARTIFACT PATH, NOT THE WORD. A first draft searched for
#    "shadow" and reddened on `box-shadow` — a check that fires on a CSS
#    property is a check that gets deleted rather than read.
_leak = sorted({m for m in re.findall(r"[\w./-]*shadow[\w./-]*", _PAGE)
                if m.lower() not in ("shadow", "box-shadow", "text-shadow",
                                     "--shadow", "var(--shadow")
                and not m.startswith("--")})
ck(not _leak,
   "🔴🔴 `index.html` DOES NOT READ THE SHADOW RECORD AT ALL (%d CSS "
   "shadow token(s) ignored)" % len(re.findall(r"box-shadow", _PAGE)),
   "⛔ Sam, 2026-08-26: \"we have to advertise a clean look to the "
   "website that doesnt include nonsense users dont need to read and "
   "cant understand.\" The absence IS the guard — `carried` is the "
   "precedent, computed and stored and never displayed. Found %s" % _leak)
_cards = sorted(glob.glob(os.path.join(ROOT, "picks", "fb-*-*.json")))
# ⚠️ `TOP_N` CAPS THE TOP-PLAYS LIST, not the board — measured across the
#    13 published cards: picks run 0-50 while top plays run 0-20, and one
#    card sits EXACTLY at 20. A first draft of this checked the rated
#    picks against `TOP_N` and reddened on four perfectly good cards.
_tops = []
for _f in _cards:
    if _f.endswith("-latest.json"):
        continue
    try:
        _c = json.load(open(_f, encoding="utf-8"))
    except Exception:
        continue
    _tops.append((os.path.basename(_f), len(_c.get("top_plays") or [])))
ck(len(_tops) >= 3,
   "⚠️ published cards to check (%d)" % len(_tops),
   "⛔ rule 67 — a sweep over no cards proves nothing")
ck(max([n for _n, n in _tops] or [0]) >= card_fb.TOP_N,
   "   ⚠️ ...and one of them sits EXACTLY at the cap (%d), so the bar "
   "below is a live comparison" % max([n for _n, n in _tops] or [0]),
   "⛔ rule 67 again: a cap no card approaches is a cap nothing tests")
_over = [x for x in _tops if x[1] > card_fb.TOP_N]
ck(not _over,
   "   ⛔ ...and not one publishes more than TOP_N=%d top play(s)"
   % card_fb.TOP_N,
   "🔴 the shadow record grades the BOARD — 1,245 rows in one run — and "
   "the card still publishes its top %d. Over: %s"
   % (card_fb.TOP_N, _over[:4]))

section("7. ⛔ THE JOIN IS `board_id`, AND NOTHING ELSE")
# ⚠️ A SYNTHETIC DOSSIER ARCHIVE, because the real ones only start the day
#    the panel shipped — and the join must be driven, not hoped for.
_day = (_D.get("days") or [None])[0]
ck(bool(_day), "⚠️ there is a graded day to attach sections to",
   "⛔ rule 67. Days: %s" % (_D.get("days"),))
if _day:
    _ids = sorted({r["board_id"] for r in _rows if r.get("day") == _day})
    _arch = os.path.join(_d4, "data/nfl", _day, "dossiers", "1200.json.gz")
    os.makedirs(os.path.dirname(_arch), exist_ok=True)
    with gzip.open(_arch, "wt") as _fh:
        json.dump({"dossiers": [
            {"board_id": _b, "home_name": "H%d" % _i, "away_name": "A%d" % _i,
             "sections": [{"n": _n, "name": "S%d" % _n,
                           "state": "OK" if _n <= _i else "UNAVAILABLE"}
                          for _n in range(1, 9)]}
            for _i, _b in enumerate(_ids)]}, _fh)
    for _f in glob.glob(os.path.join(_d4, "data/nfl/*/shadow/*.json.gz")):
        os.remove(_f)
    # 🔴 AND ONE OTHER GRADED DAY WITH NO ARCHIVE, BUILT ON PURPOSE.
    # `[issue #156, 2026-09-24]` The "undescribed rows" below used to come
    #    from the CALENDAR — boards graded before the archive began. Once
    #    the real archive covered every graded day there were none, and
    #    the rule-67 guard (correctly) refused to pass on nothing. ✅ A
    #    check that waits for the calendar to supply its case is asking
    #    whether data EXISTS; this makes the case exist, every run, so the
    #    reason-text checks below always have a row to read.
    for _od in [x for x in (_D.get("days") or []) if x != _day][:1]:
        shutil.rmtree(os.path.join(_d4, "data/nfl", _od, "dossiers"), ignore_errors=True)
    shadow_fb.build("nfl", data=os.path.join(_d4, "data", "nfl"), root=_d4,
                    log=lambda m: None, when=_w)
    _D7 = load(glob.glob(os.path.join(_d4, "data/nfl/*/shadow/*.json.gz"))[0])
    _day7 = [r for r in _D7["rows"] if r.get("day") == _day]
    _with = [r for r in _day7 if r.get("sections")]
    ck(bool(_day7) and len(_with) == len(_day7),
       "🔴🔴 EVERY ROW OF THAT DAY CARRIES ITS OWN GAME'S SECTIONS (%d)"
       % len(_with),
       "⛔ the join is `board_id` — the same key the dossier frame "
       "carries and the board's own id. %d of %d attached"
       % (len(_with), len(_day7)))
    _wrong = [r["board_id"] for r in _with
              if r["sections"] != {"S%d" % n: ("OK" if n <= _ids.index(r["board_id"])
                                               else "UNAVAILABLE")
                                   for n in range(1, 9)}]
    ck(not _wrong,
       "   ⛔ ...and they are THAT game's states, not a neighbour's",
       "🔴 CLAUDE.md: two legs are in different games only if the GAME ID "
       "differs — a live MLB card shipped four impossible parlays off a "
       "name check, including its top recommendation. Wrong: %s"
       % _wrong[:3])
    ck(len({len(r["sections"]) for r in _with}) == 1
       and next(iter({len(r["sections"]) for r in _with})) == 8,
       "   ⚠️ ...all eight of them",
       "⛔ a partial join is a join that drops evidence silently")
    ck(not [r for r in _with if r.get("sections_absent")],
       "   ⛔ ...and a row that HAS its sections carries no excuse",
       "🔴 a reason beside data that is present is noise, and noise is "
       "what the clean-look rule is about")
    # ══════════════════════════════════════════════════════════════
    # ⚠️ AND A ROW WITH NO SECTIONS SAYS WHICH ABSENCE IT IS.
    # `[2026-09-18]` `sections: null` reads identically whether the JOIN
    # MISSED or the dossier DID NOT EXIST, and those are opposite facts:
    # the first is a defect, the second is the calendar. Today every one
    # of the 1,374 rows is the second — the graded boards predate the
    # archive — which is correct, self-resolving, and unreadable unless
    # it is said.
    # ══════════════════════════════════════════════════════════════
    _other = [r for r in _D7["rows"] if r.get("day") != _day]
    _blank = [r for r in _other if not r.get("sections")]
    ck(bool(_blank), "⚠️ there are undescribed rows to explain (%d)"
       % len(_blank), "⛔ rule 67 — nothing to check otherwise")
    ck(all(r.get("sections_absent") for r in _blank),
       "🔴 EVERY UNDESCRIBED ROW SAYS WHY IT IS UNDESCRIBED (%d of %d)"
       % (len([r for r in _blank if r.get("sections_absent")]), len(_blank)),
       "⛔ a bare null cannot tell a failed join from a calendar that "
       "has not reached the archive yet. Silent: %s"
       % [(r.get("day"), r.get("board_id"))
          for r in _blank if not r.get("sections_absent")][:3])
    ck(all("calendar, not a failed join" in (r.get("sections_absent") or "")
           for r in _blank),
       "   ✅ ...and today that reason is the CALENDAR, not a defect",
       "🔴 a row whose game IS in the archive and still has no sections "
       "is a real gap, and it must not read the same. Got %s"
       % sorted({r.get("sections_absent") for r in _blank})[:2])
    _dayblk = [d for d in _D7.get("per_day") or []
               if d["day"] != _day and not d.get("described")]
    ck(all(d.get("not_described_why") for d in _dayblk),
       "   ⚠️ ...and the day block says it too, so `described` climbing "
       "later is the signal it is meant to be",
       "⛔ if `described` never starts climbing once archived boards are "
       "graded, THAT is a real defect and this field is how anyone "
       "notices. Silent day(s): %s"
       % [d["day"] for d in _dayblk if not d.get("not_described_why")])
shutil.rmtree(_d4, ignore_errors=True)

section("8. 🔴🔴 IT RUNS ON A MODE A CRON ACTUALLY REACHES")
# ⛔ "IT IS WIRED" IS NOT ENOUGH — `t54.py`'s counter is wired into the
#    `fb-record` branch, which NO cron routes to, so `t54.json` had never
#    been written once. ✅ So the REAL `card-fb` mode is executed and the
#    artifact is looked for: a source string cannot tell a live call from
#    a commented-out one.
import wfroutes  # noqa: E402
_WF = open(os.path.join(ROOT, ".github/workflows/collect.yml"),
           encoding="utf-8").read()
# ⚠️ `parse_routes` yields the mode as a STRING, not a list. Iterating
#    it character by character counted zero `card-fb` arms and the check
#    reddened on correct wiring — found by running it.
_arms = [ms for _c, _lg, ms in wfroutes.parse_routes(_WF)]
ck(_arms.count("card-fb") >= 4,
   "⚠️ `card-fb` is reached by %d cron arm(s)" % _arms.count("card-fb"),
   "⛔ THE WHOLE REASON IT HANGS HERE. `fb-record` is reached by NONE")
_d8 = tree("nfl")
_r8 = subprocess.run([sys.executable, "collect.py", "card-fb"], cwd=_d8,
                     timeout=1800, capture_output=True, text=True,
                     env=dict(os.environ, LEAGUE="nfl"))
_out8 = (_r8.stdout or "") + (_r8.stderr or "")
_made8 = glob.glob(os.path.join(_d8, "data/nfl/*/shadow/*.json.gz"))
ck(bool(_made8),
   "🔴🔴 RUNNING THE REAL `card-fb` MODE PRODUCES THE SHADOW RECORD",
   "⛔ a builder nothing runs is a builder that rots. rc=%s %s"
   % (_r8.returncode, _out8[-400:]))
ck("shadow_fb[nfl]" in _out8,
   "   ...and the collector's own log says so",
   _out8[-300:])
ck("the CARD IS FINE" not in _out8.split("shadow record")[-1][:200],
   "   ⚠️ ...without the card having to be rescued from it",
   "⛔ a failure here must not lose the card, and it did not have to: %s"
   % _out8[-300:])
shutil.rmtree(_d8, ignore_errors=True)
note("⛔ WHAT THIS FILE DOES NOT CLAIM: that the dossier carries any "
     "signal. T60 answers that, it needs rows this file did not have "
     "before today, and its verdict reads AWAITING_PRE_REGISTERED_N "
     "until Sam supplies the minimum n. ➡️ What is claimed is that the "
     "rows now accumulate, honestly clustered, at a rate that makes the "
     "question answerable this season rather than next.")
