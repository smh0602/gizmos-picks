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
#   find:         if len(out) >= n:
#   with:         if False:
#   ~~⚠️ ...and that mutation TIGHTENS rather than loosens (TOP_N 20 -> 19),
#      deliberately: one published card sits EXACTLY at 20~~ `[2026-10-09]` it
#      bit only while a real card sat at 20, a fact about the day's data. ✅ The
#      cap itself is removed instead, and the card the code builds from
#      TOP_N + 5 candidates (section 6) goes over it every time.
#
# @vacuity 🔴 a POSITIONAL join is caught even on a thin day: the planted archive lists a decoy FIRST
#   file: shadow_fb.py
#   find: got = sec.get(src["board_id"])
#   with: got = next(iter(sec.values()), None)
#   ⚠️ `[2026-09-28]` Under #196's fixture (a 1-game day, patterns that
#      repeat from game 8 on) this mutation stayed GREEN. Two decoy
#      dossiers and a unique pattern per entry give it a wrong answer to
#      pick on every day.
#
# @vacuity 🔴 the join reads the NEWEST archive of the day, and that is the fixture
#   file: shadow_fb.py
#   find: f = fs[-1]
#   with: f = fs[0]
#
# @vacuity 🔴 an archive that exists and omits a game says GAP, never "the calendar"
#   file: shadow_fb.py
#   find: no_arch or ("this game is not in %s's dossier — "
#   with: no_arch or ("%s: This is the calendar, not a failed join — "
#
# @vacuity ✅ a day with no archive says CALENDAR, never "gap"
#   file: shadow_fb.py
#   find: no_arch or ("this game is not in %s's dossier — "
#   with: ("this game is not in %s's dossier — "
#
# @vacuity ⛔ `card-fb converge-off` runs the mode ALONE and reaches no network
#   file: collect.py
#   find: if "converge-off" in args or not _fresh.has_contract(LEAGUE):
#   with: if not _fresh.has_contract(LEAGUE):
#   ⚠️ OFFLINE EVEN UNDER THE MUTATION: section 8's child refuses every
#      lookup and connect, so the converge this lets in is COUNTED, not
#      sent. The tree's news.json is stripped so that converge always has
#      a network mode to plan.
#
# 📌 WATCHED, NOT DECLARED — a test cannot mutate itself (its `find`
#    would occur twice, here and in the code). Each was run by hand on a
#    scratch copy of this file `[2026-09-28]` and went RED:
#      - section 7 without `wipe(_dd)`: the planted 2359 archive is read,
#        not the fixture (4 checks red);
#      - `_w` = the OLDEST snapshot window instead of `densest_when`:
#        86 graded rows over 1 game (4 rule-67 floors in 4 and 7 red);
#      - section 8's clock pin set to 2027-04-01: no shadow file (1 red);
#      - `_throwaway` returning True: the live-repo refusal (1 red);
#      - section 8 without `converge-off`: "ran ALONE" red, and the fence
#        counted 2 refused attempts (2 red);
#      - #156's `[:1]` (one other day wiped): 2 red — a real archive left
#        in place described 168 of the "calendar" rows.
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

from tcheck import ck, copy_module, fail, note, section, shown

ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("LEAGUE", "nfl")

import card_fb          # noqa: E402
import daystore         # noqa: E402
import record_fb        # noqa: E402
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
    """The clock that puts the NEWEST committed snapshot inside the lookback.

    ⚠️ Kept for the note in section 4 only. `[2026-09-28]` The newest
    window moves with the calendar: a week-1 window held 86 graded rows
    over 1 game, and a Super Bowl snapshot would pin it there all
    off-season — red on correct code. `densest_when` drives the checks."""
    days = snapshot_days(lg, root)
    if not days:
        return None
    last = datetime.datetime.strptime(days[-1], "%Y-%m-%d").replace(tzinfo=UTC)
    return last + datetime.timedelta(days=1, hours=12)


def pin_log(root, lg="nfl"):
    """Point `record_fb`'s player log at `root`'s copy.

    ⚠️ `record_fb.LATEST` is cwd-relative (`data/<lg>/latest`), so an
    in-process grade read the LIVE log from wherever the file was started,
    whatever tree it was handed. Pinned, every grade here reads the tree
    it claims to read, from any cwd."""
    record_fb.LATEST = os.path.join(root, "data", lg, "latest")


def windows(lg="nfl", root=None):
    """[(end day, graded games, graded rows, graded days)] — one row per
    committed snapshot day, for the LOOKBACK_DAYS window `build()` grades
    from end + 1d12h. ⛔ Graded by `shadow_fb.grade_day` itself, the one
    copy of "what can be graded", never re-derived here."""
    root = root or ROOT
    data = os.path.join(root, "data", lg)
    pin_log(root, lg)
    days, bk, per = snapshot_days(lg, root), shadow_fb.books(), {}
    for d in days:
        rows, _why = shadow_fb.grade_day(d, data, bk, log=lambda m: None)
        g = [r for r in rows if r.get("won") is not None]
        per[d] = ({r.get("board_id") for r in g}, len(g))
    out = []
    for end in days:
        e = datetime.date.fromisoformat(end)
        win = [d for d in days if 0 <= (e - datetime.date.fromisoformat(d)).days
               < shadow_fb.LOOKBACK_DAYS]
        out.append((end, len(set().union(*(per[d][0] for d in win))),
                    sum(per[d][1] for d in win),
                    len([d for d in win if per[d][1]])))
    return out


def densest_when(lg="nfl", root=None, w=None):
    """🔴 THE CLOCK THAT PUTS THE DENSEST COMMITTED WINDOW INSIDE THE LOOKBACK.

    `[2026-09-28]` The checks in sections 4 and 7 need at least 200 graded
    rows, 5 games and 2 graded days. The NEWEST window does not always
    hold them (week 1: 86 rows, 1 game; the Super Bowl: 1 game, then the
    whole off-season). ✅ The window with the most graded games wins, a tie
    going to the later day. ⛔ `data/` is append-only and the player log
    only grows, so this maximum can only rise: the floors get easier to
    meet as seasons are stored, never harder, and never on a calendar
    change. -> (when, (end, games, rows, days))"""
    w = windows(lg, root) if w is None else w
    if not w:
        return None, None
    best = max(w, key=lambda x: (x[1], x[0]))
    end = datetime.datetime.strptime(best[0], "%Y-%m-%d").replace(tzinfo=UTC)
    return end + datetime.timedelta(days=1, hours=12), best


def _inside(p, d):
    try:
        return os.path.commonpath([p, d]) == d
    except ValueError:          # different drives
        return False


def _throwaway(p):
    """⛔ True only for a path inside a mkdtemp copy: under the temp dir and
    outside the live repo. Section 7 deletes nothing anywhere else."""
    rp, tmp, root = (os.path.normcase(os.path.realpath(x))
                     for x in (p, tempfile.gettempdir(), ROOT))
    return _inside(rp, tmp) and rp != tmp and not _inside(rp, root)


def wipe(p):
    """rmtree, ONLY inside a throwaway copy. Anything else fails the file
    and stops it before one byte is deleted."""
    if not _throwaway(p):
        fail("⛔ REFUSED to delete %s — not inside a throwaway copy" % p,
             "the live repo is never a fixture")
        raise SystemExit(1)
    shutil.rmtree(p, ignore_errors=True)


# ⛔ THE CHILD CANNOT REACH THE NETWORK, BY CONSTRUCTION. `[2026-09-28]`
#    `collect.py card-fb` without `converge-off` converged the whole NFL
#    contract from this file: it fetched news from cbssports and
#    profootballtalk on every run, and it plans the PAID modes whenever
#    they are due (they died only because CI's Tests step has no key).
#    This runs the real collector with every lookup and connect refused
#    and COUNTED, so "it reached no network" is measured, not assumed.
OFFLINE = (
    "import atexit, runpy, socket, sys\n"
    "_refused = []\n"
    "def _refuse(*a, **k):\n"
    "    _refused.append(repr(a[:1]))\n"
    "    raise OSError('OFFLINE: a test may not reach the network')\n"
    "socket.getaddrinfo = _refuse\n"
    "socket.socket.connect = lambda self, *a, **k: _refuse(*a)\n"
    "atexit.register(lambda: print('OFFLINE FENCE: %d network attempt(s) "
    "refused %s' % (len(_refused), _refused[:3]), flush=True))\n"
    "#PIN\n"
    "sys.argv = ['collect.py'] + sys.argv[1:]\n"
    "runpy.run_path('collect.py', run_name='__main__')\n")


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
# 🔴 THE DENSEST COMMITTED WINDOW, NOT THE NEWEST. `[2026-09-28]` The
#    floors below (200 rows, 5 games, 2 graded days) were asked of
#    whatever the calendar's newest window held — 86 rows over 1 game in
#    week 1, and a Super Bowl snapshot would have pinned it red for the
#    whole off-season. ✅ The window is DERIVED from append-only data, so
#    its case can only grow; the newest window is reported beside it.
_win = windows("nfl")
_w, _dense = densest_when("nfl", w=_win)
_newest = (_win or [None])[-1]
note("   window under test ends %s: %s graded game(s), %s graded row(s) "
     "over %s day(s) (the densest committed); the NEWEST ends %s: %s "
     "game(s), %s row(s), %s day(s)"
     % ((_dense or (None,) * 4) + (_newest or (None,) * 4)))
_d4 = tree("nfl")
pin_log(_d4)
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
# ⚠️ SEPARATORS NORMALISED FIRST, THE PATTERN UNCHANGED. `[2026-09-28]`
#    On Windows `glob` returns `...\2026-09-29\shadow\1200.json.gz`, and
#    this check was red there on a correctly dated file (green on Linux).
_p = (_files[0] if _files else "").replace(os.sep, "/")
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
note("published cards swept: %d, the most top plays on one: %d"
     % (len(_tops), max([n for _n, n in _tops] or [0])))
# 🔴 `[Sam, 2026-10-09]` THE PRECONDITIONS ARE PLANTED; THE DEFECT CHECK STAYS LIVE.
#    "3 or more cards" and "one EXACTLY at the cap" were facts about picks/, so the
#    day's data could turn them red. The sweep now always holds a card the CODE
#    builds from TOP_N + 5 candidates in as many games: it sits at the cap
#    whatever main holds, and the bar below still reads every published card.
_cand = [{"player": "Plant %d" % i, "game_id": "plant-%d" % i, "price": -110,
          "confidence": 90.0 - i} for i in range(card_fb.TOP_N + 5)]
_tops.append(("planted (build_top_plays)", len(card_fb.build_top_plays(_cand, _cand)[0])))
ck(_tops[-1][1] == card_fb.TOP_N,
   "⚠️ the sweep holds a card EXACTLY at the cap: the code built %d top plays from "
   "%d candidates, so the bar below is a live comparison" % (_tops[-1][1], len(_cand)),
   "⛔ rule 67: a cap no card reaches is a cap nothing tests")
_over = [x for x in _tops if x[1] > card_fb.TOP_N]
ck(not _over,
   "   ⛔ ...and not one publishes more than TOP_N=%d top play(s)"
   % card_fb.TOP_N,
   "🔴 the shadow record grades the BOARD — 1,245 rows in one run — and "
   "the card still publishes its top %d. Over: %s"
   % (card_fb.TOP_N, _over[:4]))

section("7. ⛔ THE JOIN IS `board_id`, AND NOTHING ELSE")
# ⚠️ A SYNTHETIC DOSSIER ARCHIVE, because the join must be driven, not
#    hoped for.
# ══════════════════════════════════════════════════════════════════════
# 🔴 `[2026-09-28]` THE FIXTURE WAS SHADOWED; EVERY CASE BELOW NOW EXISTS
#    BY CONSTRUCTION. `sections_for` reads the NEWEST archive of a day,
#    and the fixture was `1200.json.gz` beside real archives written later
#    that day. From 2026-09-27 13:04Z a real one (1544 on 09-21, 1545 on
#    09-20) was the file read, and "THAT game's states" was red on every
#    collect run, on correct code.
#    ✅ A real-shaped archive is PLANTED later that day (2359), so the
#       shadowing case exists on every run, not only when production holds
#       one. The day's archives are then wiped — only ever inside the
#       throwaway copy — and the fixture is written with one OLDER planted
#       archive beside it, so "the newest archive is read" is asked too.
#    ✅ The fixture day is the graded day with the MOST games, and the
#       archive lists a decoy first and last and a unique state pattern
#       per entry: a positional or neighbour join has a wrong answer to
#       pick even on a thin day (#196's 1-game fixture let one through).
#    ✅ One graded game is LEFT OUT of the archive, so the "IS a gap"
#       branch is exercised (it never was).
#    ✅ EVERY other graded day's archives are wiped (#156 wiped one), so
#       "the reason is the CALENDAR" no longer asserts that production's
#       archives describe every priced game.
# ══════════════════════════════════════════════════════════════════════
_nfl4 = os.path.join(_d4, "data", "nfl")
ck(_throwaway(_d4) and not _throwaway(ROOT)
   and not _throwaway(os.path.join(ROOT, "data", "nfl")),
   "⛔ this section deletes only inside a throwaway copy, never the live "
   "repo",
   "🔴 it wipes whole dossier directories. copy=%s (throwaway=%s), "
   "repo=%s (throwaway=%s)" % (_d4, _throwaway(_d4), ROOT, _throwaway(ROOT)))
_gdays = {d: sorted({r["board_id"] for r in _rows if r.get("day") == d})
          for d in (_D.get("days") or [])}
_day = max(_gdays, key=lambda d: (len(_gdays[d]), d)) if _gdays else None
_ids = _gdays.get(_day) or []
ck(len(_ids) >= 2,
   "⚠️ the fixture day (%s) has %d game(s), so every game has a neighbour"
   % (_day, len(_ids)),
   "⛔ rule 67: on a 1-game day a positional join is indistinguishable from "
   "the right one. Days: %s" % {d: len(v) for d, v in _gdays.items()})
ck(len(_gdays) >= 2,
   "⚠️ ...and there is another graded day to leave undescribed (%d day(s))"
   % len(_gdays),
   "⛔ rule 67 — the calendar case below needs one")
if len(_ids) >= 2:
    _gap = _ids[-1]                 # 🔴 PLANTED GAP: in no dossier
    _desc = ["0000-decoy-first"] + [b for b in _ids if b != _gap] + [
        "zzzz-decoy-last"]
    # ⚠️ ENTRY i CARRIES THE BITS OF i+1 — unique for up to 255 entries,
    #    where `OK if n <= i` repeated itself from the eighth game on.
    _want = {b: {"S%d" % n: ("OK" if ((i + 1) >> (n - 1)) & 1
                             else "UNAVAILABLE") for n in range(1, 9)}
             for i, b in enumerate(_desc)}
    _dd = os.path.join(_nfl4, _day, "dossiers")

    def _plant(name, entries):
        with gzip.open(os.path.join(_dd, name), "wt") as _fh:
            json.dump({"dossiers": entries}, _fh)

    os.makedirs(_dd, exist_ok=True)
    # 🔴 A REAL ARCHIVE WRITTEN LATER THAT DAY — what shadowed the fixture
    #    from 2026-09-27. Planted, so the wipe below is needed EVERY run.
    _plant("2359.json.gz", [
        {"board_id": b, "sections": [{"n": n, "name": "REAL %d" % n,
                                      "state": "OK"} for n in range(1, 9)]}
        for b in _ids])
    wipe(_dd)                       # ⛔ the fixture is the newest archive (#196)
    os.makedirs(_dd)
    _plant("0600.json.gz", [
        {"board_id": b, "sections": [{"n": n, "name": "S%d" % n,
                                      "state": "STALE"} for n in range(1, 9)]}
        for b in _desc])
    _plant("1200.json.gz", [
        {"board_id": b, "home_name": "H", "away_name": "A",
         "sections": [{"n": n, "name": k, "state": v}
                      for n, (k, v) in enumerate(_want[b].items(), 1)]}
        for b in _desc])
    # 🔴 AND EVERY OTHER GRADED DAY WITH NO ARCHIVE, BUILT ON PURPOSE.
    # `[issue #156, 2026-09-24]` The "undescribed rows" below used to come
    #    from the CALENDAR — boards graded before the archive began. Once
    #    the real archive covered every graded day there were none, and
    #    the rule-67 guard (correctly) refused to pass on nothing. ✅ A
    #    check that waits for the calendar to supply its case is asking
    #    whether data EXISTS; this makes the case exist, every run.
    #    `[2026-09-28]` ~~`[:1]`~~ ALL of them: a day left in place asked
    #    whether production's archives describe every game it priced.
    for _od in _gdays:
        if _od != _day:
            wipe(os.path.join(_nfl4, _od, "dossiers"))
    for _f in glob.glob(os.path.join(_nfl4, "*", "shadow", "*.json.gz")):
        os.remove(_f)
    ck(sorted(os.listdir(_dd)) == ["0600.json.gz", "1200.json.gz"]
       and not [d for d in _gdays if d != _day
                and os.path.isdir(os.path.join(_nfl4, d, "dossiers"))],
       "⚠️ the fixture day holds ONLY the planted archives (the later 2359 "
       "is gone), and no other graded day holds one",
       "⛔ rule 67 on the fixture itself. %s" % sorted(os.listdir(_dd)))
    shadow_fb.build("nfl", data=_nfl4, root=_d4, log=lambda m: None, when=_w)
    _f7 = glob.glob(os.path.join(_nfl4, "*", "shadow", "*.json.gz"))
    _D7 = load(_f7[0]) if _f7 else {"rows": [], "per_day": []}
    _day7 = [r for r in _D7["rows"] if r.get("day") == _day]
    ck(bool(_day7)
       and all(r.get("sections_from") == "1200.json.gz" for r in _day7),
       "🔴 THE JOIN READ THE FIXTURE — the day's NEWEST archive, not an older "
       "one",
       "⛔ the reading closest to kickoff is the one a bettor saw. Read: %s"
       % sorted({str(r.get("sections_from")) for r in _day7}))
    _descr = [r for r in _day7 if r["board_id"] != _gap]
    _with = [r for r in _descr if r.get("sections")]
    ck(bool(_descr) and len(_with) == len(_descr),
       "🔴🔴 EVERY ROW OF A DESCRIBED GAME CARRIES ITS OWN GAME'S SECTIONS "
       "(%d)" % len(_with),
       "⛔ the join is `board_id` — the same key the dossier frame "
       "carries and the board's own id. %d of %d attached"
       % (len(_with), len(_descr)))
    # ⚠️ `.get`, so a row joined to an id outside the fixture FAILS here
    #    rather than killing the file.
    _wrong = [r["board_id"] for r in _with
              if r["sections"] != _want.get(r["board_id"])]
    ck(not _wrong,
       "   ⛔ ...and they are THAT game's states, not a neighbour's (%d "
       "distinct patterns, decoys first and last)"
       % len({json.dumps(v, sort_keys=True) for v in _want.values()}),
       "🔴 CLAUDE.md: two legs are in different games only if the GAME ID "
       "differs — a live MLB card shipped four impossible parlays off a "
       "name check, including its top recommendation. Wrong: %s"
       % _wrong[:3])
    ck(bool(_with) and {len(r["sections"]) for r in _with} == {8},
       "   ⚠️ ...all eight of them",
       "⛔ a partial join is a join that drops evidence silently")
    ck(not [r for r in _with if r.get("sections_absent")],
       "   ⛔ ...and a row that HAS its sections carries no excuse",
       "🔴 a reason beside data that is present is noise, and noise is "
       "what the clean-look rule is about")
    _gaprows = [r for r in _day7 if r["board_id"] == _gap]
    ck(bool(_gaprows)
       and all(not r.get("sections")
               and "IS a gap" in (r.get("sections_absent") or "")
               and "calendar" not in (r.get("sections_absent") or "")
               for r in _gaprows),
       "🔴 A GAME THE DAY'S ARCHIVE OMITS SAYS GAP, NEVER CALENDAR (%d "
       "row(s))" % len(_gaprows),
       "⛔ an archive that exists and does not describe a priced game is "
       "the defect this field is for; reading like the calendar would hide "
       "it. Got %s" % sorted({str(r.get("sections_absent"))
                              for r in _gaprows})[:2])
    # ══════════════════════════════════════════════════════════════
    # ⚠️ AND A ROW WITH NO SECTIONS SAYS WHICH ABSENCE IT IS.
    # `[2026-09-18]` `sections: null` reads identically whether the JOIN
    # MISSED or the dossier DID NOT EXIST, and those are opposite facts:
    # the first is a defect, the second is the calendar.
    # ══════════════════════════════════════════════════════════════
    _other = [r for r in _D7["rows"] if r.get("day") != _day]
    _blank = [r for r in _other if not r.get("sections")]
    ck(bool(_blank) and len(_blank) == len(_other),
       "⚠️ there are undescribed rows to explain (%d) — every row of every "
       "other graded day" % len(_blank),
       "⛔ rule 67 — nothing to check otherwise. %d of %d undescribed"
       % (len(_blank), len(_other)))
    ck(all(r.get("sections_absent") for r in _blank),
       "🔴 EVERY UNDESCRIBED ROW SAYS WHY IT IS UNDESCRIBED (%d of %d)"
       % (len([r for r in _blank if r.get("sections_absent")]), len(_blank)),
       "⛔ a bare null cannot tell a failed join from a calendar that "
       "has not reached the archive yet. Silent: %s"
       % [(r.get("day"), r.get("board_id"))
          for r in _blank if not r.get("sections_absent")][:3])
    ck(all("calendar, not a failed join" in (r.get("sections_absent") or "")
           for r in _blank),
       "   ✅ ...and a day with NO archive says the CALENDAR, not a defect",
       "🔴 a row whose game IS in the archive and still has no sections "
       "is a real gap, and it must not read the same. Got %s"
       % sorted({str(r.get("sections_absent")) for r in _blank})[:2])
    _dayblk = [d for d in _D7.get("per_day") or []
               if d["day"] != _day and not d.get("described")]
    ck(bool(_dayblk) and all(d.get("not_described_why") for d in _dayblk),
       "   ⚠️ ...and the day block says it too, so `described` climbing "
       "later is the signal it is meant to be",
       "⛔ if `described` never starts climbing once archived boards are "
       "graded, THAT is a real defect and this field is how anyone "
       "notices. Silent day(s): %s"
       % [d["day"] for d in _dayblk if not d.get("not_described_why")])
    # ⚪ THE REAL ARCHIVES, REPORTED: what production's newest archive of
    #    each graded day does not describe. A measurement, not a check (P2).
    _real = []
    for _od in sorted(_gdays):
        _sec, _src, _ = shadow_fb.sections_for(
            _od, os.path.join(ROOT, "data", "nfl"))
        _real.append("%s %s: %d of %d graded game(s) undescribed"
                     % (_od, _src, len([b for b in _gdays[_od]
                                        if b not in _sec]), len(_gdays[_od])))
    note("   real archives (live repo), per graded day: %s" % "; ".join(_real))
wipe(_d4)

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
# ══════════════════════════════════════════════════════════════════════
# 🔴 `[2026-09-28]` ~~`collect.py card-fb`~~ -> `card-fb converge-off`,
#    keys blanked, network fenced, shadow clock pinned to the tree.
#    ⛔ Without `converge-off` the mode converged the whole NFL contract:
#       news fetched from two outside hosts on every run, and the PAID
#       modes planned whenever due — refused only because CI's Tests step
#       has no key. A test must never be able to spend.
#    ⛔ And the shadow record looked back 8 REAL days: off-season, or in
#       the gap before the Super Bowl, nothing is gradable and the file is
#       never written (measured at a 2027-04-01 clock). Pinned to the same
#       tree-derived window as sections 4 and 7, it has its case every run.
#    ⚠️ news.json is stripped from the copy, so a converge that sneaks back
#       in ALWAYS has a network mode to plan — and the fence counts it.
# ══════════════════════════════════════════════════════════════════════
_d8 = tree("nfl")
_news8 = os.path.join(_d8, "data", "nfl", "latest", "news.json")
if os.path.exists(_news8):
    os.remove(_news8)
_pin8 = ("import datetime, functools, shadow_fb\n"
         "shadow_fb.build = functools.partial(shadow_fb.build, "
         "when=datetime.datetime.fromisoformat(%r))\n"
         % (_w or datetime.datetime.now(UTC)).isoformat())
_r8 = subprocess.run([sys.executable, "-c", OFFLINE.replace("#PIN\n", _pin8),
                      "card-fb", "converge-off"], cwd=_d8,
                     timeout=1800, capture_output=True, text=True,
                     env=dict(os.environ, LEAGUE="nfl", ODDS_API_KEY="",
                              CFBD_API_KEY=""))
_out8 = (_r8.stdout or "") + (_r8.stderr or "")
_made8 = glob.glob(os.path.join(_d8, "data/nfl/*/shadow/*.json.gz"))
ck(bool(_made8),
   "🔴🔴 RUNNING THE REAL `card-fb` MODE PRODUCES THE SHADOW RECORD",
   "⛔ a builder nothing runs is a builder that rots. rc=%s %s"
   % (_r8.returncode, shown(_out8[-400:])))
ck("shadow_fb[nfl]" in _out8,
   "   ...and the collector's own log says so",
   shown(_out8[-300:]))
ck("the CARD IS FINE" not in _out8.split("shadow record")[-1][:200],
   "   ⚠️ ...without the card having to be rescued from it",
   "⛔ a failure here must not lose the card, and it did not have to: %s"
   % shown(_out8[-300:]))
ck("FRESHNESS SURVEY" not in _out8 and "PLAN:" not in _out8,
   "⛔ ...and the mode ran ALONE: no converge pass, so no other mode, no "
   "network mode and no paid pull was planned",
   "🔴 `collect.py <mode>` without `converge-off` converges every overdue "
   "artifact. %s" % shown([ln for ln in _out8.splitlines()
                           if "PLAN:" in ln][:1]))
ck("OFFLINE FENCE: 0 network attempt(s) refused" in _out8,
   "⛔ ...and it made NO network attempt (every lookup and connect was "
   "fenced and counted)",
   "🔴 a test must not depend on the network. %s"
   % shown([ln for ln in _out8.splitlines() if "OFFLINE FENCE" in ln][:1]))
wipe(_d8)
note("⛔ WHAT THIS FILE DOES NOT CLAIM: that the dossier carries any "
     "signal. T60 answers that, it needs rows this file did not have "
     "before today, and its verdict reads AWAITING_PRE_REGISTERED_N "
     "until Sam supplies the minimum n. ➡️ What is claimed is that the "
     "rows now accumulate, honestly clustered, at a rate that makes the "
     "question answerable this season rather than next.")
