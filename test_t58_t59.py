#!/usr/bin/env python3
"""
THE COUNTER MUST NOT LEAK THE ANSWER, AND MUST FIRE WHEN THE BAR IS MET.

🔴🔴 THE CHECK THAT MATTERS MOST IS THE FIRST ONE: under the bar, driven
against the REAL record, NOT ONE STATISTIC MAY APPEAR. A pre-registration
you have been watching is not a pre-registration — and the leak that
matters is the quiet one, a percentage in a progress line that nobody
reads as a result until the day it becomes one.

⚠️ AND BOTH HALVES ARE DRIVEN. A checker that finds no statistic in an
empty string is rule 67: the same words are asserted PRESENT on a
synthetic record that meets the bar, so "absent" means something.
"""
import gzip
import json
import os
import sys
import tempfile

from tcheck import ck, eq, note, section

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t58_t59 as T  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════════════
# @vacuity under the bar NOT ONE STATISTIC may reach the page
#   file: t58_t59.py
#   find: if len(nfl) < MIN_FRESH or len(weeks) < MIN_WEEKS:
#   with: if False:
#
# @vacuity fresh means AFTER 2026-09-15, never on it
#   file: t58_t59.py
#   find: if not (day > FRESH_AFTER):
#   with: if not (day >= FRESH_AFTER):
#
# @vacuity the WEEKS bar is a bar of its own — rows never buy it
#   file: t58_t59.py
#   find: if len(nfl) < MIN_FRESH or len(weeks) < MIN_WEEKS:
#   with: if len(nfl) < MIN_FRESH:
#
# @vacuity a shrinking sample is a FINDING, never a smaller number
#   file: t58_t59.py
#   find: if isinstance(was, int) and len(nfl) < was:
#   with: if False:
#
# @vacuity the week bar is real — rows alone do not meet it
#   file: t58_t59.py
#   find: MIN_WEEKS = 3
#   with: MIN_WEEKS = 0
#
# @vacuity T59 VOIDs when either band is thin
#   file: t58_t59.py
#   find: if hn < T59_MIN_BAND or ln < T59_MIN_BAND:
#   with: if False:
#
# @vacuity T58's VOID reads the CFB control BEFORE calling a result
#   file: t58_t59.py
#   find: if cfb_st is not None and abs(cfb_st[0]) > T58_VOID_CFB:
#   with: if False:
#
# @vacuity the exit code is the interface and comes from verdict()
#   file: t58_t59.py
#   find: "ANSWERED": EXIT_ANSWERED}.get(rep.get("state"), EXIT_PROGRESS)
#   with: "ANSWERED": EXIT_PROGRESS}.get(rep.get("state"), EXIT_PROGRESS)
# ══════════════════════════════════════════════════════════════════════


def mkrepo(nfl_days, cfb_days, sched):
    """A repo-shaped tree. `*_days` is {day: [row, ...]}, `sched` {date: week}."""
    d = tempfile.mkdtemp(prefix="t5859-")
    for lg, days in (("nfl", nfl_days), ("ncaaf", cfb_days)):
        p = os.path.join(d, "data", lg, "latest")
        os.makedirs(p)
        with gzip.open(os.path.join(p, "record-detail.json.gz"), "wt") as fh:
            json.dump({"days": days}, fh)
    with gzip.open(os.path.join(d, "data/nfl/latest/schedule-2026.json.gz"),
                   "wt") as fh:
        json.dump({"season": 2026,
                   "games": [{"start": k + "T13:00", "week": v}
                             for k, v in sched.items()]}, fh)
    return d


def row(side, conf, won, day):
    """⚠️ 17:00Z is 13:00 ET the SAME day, so the week join is unambiguous."""
    return {"side": side, "confidence": conf, "won": won,
            "commence": day + "T17:00:00Z"}


def at_the_bar():
    """EXACTLY 120 fresh NFL rows, 3 weeks, and EXACTLY 40 in the low band.

    ⚠️ ON the bar, not over it. A fixture that clears every minimum by a
    comfortable margin never shows whether the comparison is `>=` or `>`.
      over   60 rows, 12 won   under  60 rows, 42 won
      <60    40 rows,  4 won   >=60   80 rows, 50 won
    """
    days = {}
    D = ["2026-09-17", "2026-09-24", "2026-10-01"]
    rows = []
    rows += [row("over", 50, False, D[0]) for _ in range(20)]          # 0/20
    rows += [row("over", 80, i < 12, D[1]) for i in range(40)]         # 12/40
    rows += [row("under", 50, i < 4, D[2]) for i in range(20)]         # 4/20
    rows += [row("under", 80, i < 38, D[0]) for i in range(40)]        # 38/40
    for r in rows:
        days.setdefault(r["commence"][:10], []).append(r)
    return days, {D[0]: 2, D[1]: 3, D[2]: 4}


section("1. 🔴🔴 UNDER THE BAR, AGAINST THE REAL RECORD: NO STATISTIC")
_real = T.run(ROOT)
eq(_real["state"], "PROGRESS",
   "⚠️ the real record is UNDER the bar today — so this check is live")
_txt = T.render(_real)
_leak = [w for w in T.STAT_WORDS if w in _txt.lower()]
ck(not _leak,
   "🔴🔴 NOT ONE STATISTIC WORD REACHES THE PAGE",
   "⛔ THIS IS THE WHOLE DESIGN. A number on screen every morning makes "
   "the decision to keep waiting stop being neutral, which is choosing "
   "the cutoff after seeing the data one step earlier. Leaked: %s" % _leak)
for _k in ("gap", "p", "t58", "t59", "cfb_gap"):
    ck(_k not in _real,
       "   ⛔ ...and `%s` is not even COMPUTED" % _k,
       "🔴 a statistic that exists in the report but is not printed is "
       "one `render()` change away from being printed. The bar gates the "
       "COMPUTATION, not the formatting")
ck("fresh graded NFL rows" in _txt and "distinct NFL weeks" in _txt,
   "✅ ...while the counts Sam asked for ARE printed",
   "⛔ a counter that prints nothing is not a counter — the point is that "
   "neither of us has to remember this test exists")

section("2. ⚠️ AND THE LEAK-CHECK CAN ACTUALLY FAIL")
_d_bar, _s_bar = at_the_bar()
_repo = mkrepo(_d_bar, {}, _s_bar)
_ans = T.run(_repo)
_atxt = T.render(_ans)
_found = [w for w in T.STAT_WORDS if w in _atxt.lower()]
ck("p=" in _atxt and "points" in _atxt,
   "🔴 the SAME words appear in an at-the-bar report",
   "⛔ RULE 67: if these words never appear anywhere, section 1 proves "
   "nothing — it would pass on a renderer that prints an empty string. "
   "Found: %s" % _found)
ck(bool(_found),
   "   ...so `STAT_WORDS` is a list that can actually match",
   "⛔ a forbidden-word list that matches nothing forbids nothing")

section("3. ✅ AT THE BAR THE VERDICT FIRES, ONCE, AS PRE-REGISTERED")
eq(_ans["state"], "ANSWERED", "   exactly 120 rows / 3 weeks meets the bar")
eq(_ans["fresh_nfl"], 120, "   ...on exactly 120 fresh NFL rows")
eq(_ans["weeks"], 3, "   ...across exactly 3 distinct NFL weeks")
eq(_ans["band_low"], 40, "   ...with EXACTLY 40 rows in the thin band")
eq(_ans["week_unresolved"], 0, "   every row matched a week")
ck(_ans["weeks"] >= T.MIN_WEEKS and _ans["weeks"] > 0,
   "   ⛔ ...and a verdict may never be reached on weeks=0",
   "🔴 WEEKS=0 REACHING A VERDICT IS THE VERSION OF THIS THAT LOOKS LIKE "
   "ARITHMETIC RATHER THAN A BUG — zero distinct weeks is not a small "
   "number of weeks, it is no week map at all. Got %s" % _ans["weeks"])
eq(_ans["t58"]["verdict"], "PASS",
   "🔴 T58: over 12/60 vs under 42/60 is -50 points, past the -15 bar")
eq(_ans["t59"]["verdict"], "PASS",
   "🔴 T59: >=60 band 50/80 vs <60 band 4/40, past the +10 bar")
ck(_ans["t58"]["p"] < T.T58_P and _ans["t59"]["p"] < T.T59_P,
   "   ...and both clear p < 0.01 two-sided",
   "p58=%s p59=%s" % (_ans["t58"]["p"], _ans["t59"]["p"]))
ck("closes itself" in _atxt and "not re-decided now" in _atxt,
   "   the report says the thresholds are not re-decided",
   "⛔ re-running with a different bar after seeing the split is the one "
   "thing the register exists to stop")

section("4. ⛔ ONE ROW SHORT, OR ONE WEEK SHORT, IS STILL SILENCE")
_short = {k: (v[:-1] if k == "2026-10-01" else v) for k, v in _d_bar.items()}
_r_short = T.run(mkrepo(_short, {}, _s_bar))
eq(_r_short["fresh_nfl"], 119, "   119 rows")
eq(_r_short["state"], "PROGRESS", "   🔴 ONE row short and nothing is read")
ck(not [w for w in T.STAT_WORDS if w in T.render(_r_short).lower()],
   "   ...and still not one statistic",
   "⛔ 119 of 120 is the moment the bar is most tempting")
_two = {k: v for k, v in _d_bar.items() if k != "2026-10-01"}
_r_2w = T.run(mkrepo(_two, {}, _s_bar))
eq(_r_2w["weeks"], 2, "   2 weeks")
eq(_r_2w["state"], "PROGRESS",
   "   100 rows over 2 weeks — ⚠️ BOTH bars are short here, so this one "
   "says nothing about the weeks bar on its own. Section 4a is the one "
   "that isolates it.")

section("4a. 🔴🔴 THE WEEKS BAR IS A BAR OF ITS OWN, AND ROWS NEVER BUY IT")
# ⛔ THIS IS THE MINIMUM THAT MATTERS MOST, AND IT WAS UNGUARDED UNTIL
#    2026-09-16. The rows bar protects sample SIZE; the weeks bar protects
#    INDEPENDENCE, and T58's own spec says why: "Not 3 days — the current
#    sample is 3 days inside 2 weeks, which is far less independent than
#    it looks."
# 🔴 THE GAP WAS IN THE FIXTURE, NOT THE LOGIC. Section 4's two-week case
#    holds 100 rows, so `100 < 120` already forced PROGRESS and the weeks
#    half of the gate never decided anything. Dropping `or len(weeks) <
#    MIN_WEEKS` left this file GREEN at 57 of 57, and 130 rows on ONE date
#    then returned ANSWERED and published both p-values. `[found by Sam,
#    by mutation; reproduced here before this section was written]`
# ✅ SO THE ROWS BAR IS CLEARED AND ONLY THE WEEKS BAR IS SHORT.


def one_week(n=130, day="2026-09-17"):
    """`n` fresh rows, all on ONE date — over the rows bar, under weeks."""
    return {day: [row("over" if i % 2 else "under", 80 if i % 3 else 50,
                       i % 2 == 0, day) for i in range(n)]}


_1w = T.run(mkrepo(one_week(), {}, {"2026-09-17": 2}))
ck(_1w["fresh_nfl"] >= T.MIN_FRESH,
   "⚠️ the ROWS bar is cleared — %d of %d" % (_1w["fresh_nfl"], T.MIN_FRESH),
   "⛔ if the rows bar is also short this section proves nothing about "
   "weeks, which is exactly how the gap got here")
eq(_1w["weeks"], 1, "   ...and exactly 1 distinct NFL week")
eq(_1w["state"], "PROGRESS",
   "🔴🔴 130 ROWS ON ONE WEEK IS NOT THREE WEEKS, and no row count "
   "changes that")
ck(not [w for w in T.STAT_WORDS if w in T.render(_1w).lower()],
   "   ⛔ ...and not one statistic is emitted",
   "🔴 130 rows feels like a sample. Independence is what is missing, and "
   "a p-value computed across one slate would not say so")
for _k in ("t58", "t59", "gap", "p"):
    ck(_k not in _1w, "   ⛔ ...nor computed (`%s`)" % _k,
       "the bar gates the COMPUTATION, not the formatting")

# ⚠️ AND THE weeks=0 CASE, which is the one that looks like arithmetic.
_0w = T.run(mkrepo(one_week(), {}, {}))
eq(_0w["weeks"], 0, "   a record with NO schedule map resolves 0 weeks")
eq(_0w["week_unresolved"], 130, "   ...and says all 130 are unmatched")
eq(_0w["state"], "PROGRESS",
   "⛔ zero distinct weeks is not a small number of weeks — it is no week "
   "map at all, and it must never read as a cleared bar")
ck("could not be matched to an NFL week" in T.render(_0w),
   "   ⚠️ ...and the report says so out loud",
   "🔴 a silent unknown is the shape of every calibration bug here")

section("5. 🔴 FRESH MEANS PUBLISHED AFTER 2026-09-15 — DRIVEN BOTH WAYS")
_on = {"2026-09-15": [row("over", 70, True, "2026-09-15")]}
_af = {"2026-09-16": [row("over", 70, True, "2026-09-16")]}
eq(T.run(mkrepo(_on, {}, {}))["fresh_nfl"], 0,
   "⛔ a row dated 2026-09-15 is NEVER counted")
eq(T.run(mkrepo(_af, {}, {}))["fresh_nfl"], 1,
   "✅ ...and 2026-09-16 is")
eq(T.FRESH_AFTER, "2026-09-15", "   the cutoff is the register's own date")
_stale = {"2026-09-14": [row("over", 70, True, "2026-09-14")] * 500}
eq(T.run(mkrepo(_stale, {}, {}))["fresh_nfl"], 0,
   "⛔ 500 pre-cutoff rows do not move the counter one place",
   )

section("6. 🔴🔴 A SHRINKING SAMPLE IS A FINDING, NOT A SMALLER NUMBER")
_repo2 = mkrepo(_af, {}, {})
eq(T.run(_repo2, prior={"fresh_nfl": 1})["state"], "PROGRESS",
   "   holding steady is not a finding")
_sh = T.run(_repo2, prior={"fresh_nfl": 9})
eq(_sh["state"], "SHRANK", "🔴🔴 9 rows became 1 and the counter SAYS SO")
ck("FELL from 9 rows to 1" in T.render(_sh),
   "   ...naming both numbers",
   "⛔ a sample that quietly shrinks is how a test gets answered on rows "
   "nobody chose")
ck("re-baseline" in T.render(_sh),
   "   ...and refusing to re-baseline it away",
   "🔴 writing the smaller number down as the new normal is the failure")
eq(T.run(_repo2, prior=None)["state"], "PROGRESS",
   "   ⚠️ a FIRST run has no prior and must not cry shrink")
eq(T.prior_of(T.render(T.run(_repo2)))["fresh_nfl"], 1,
   "   🔴 the marker round-trips: what it writes, it can read back")
eq(T.prior_of("no marker here"), None,
   "   ⛔ ...and an unparseable body is None, never a guessed zero")

section("7. ⛔ THE EXIT CODE IS THE INTERFACE, SO IT IS DRIVEN")
eq(T.verdict({"state": "PROGRESS"}), T.EXIT_PROGRESS, "   PROGRESS -> 0")
eq(T.verdict({"state": "SHRANK"}), T.EXIT_SHRANK, "   SHRANK -> 1")
eq(T.verdict({"state": "UNREADABLE"}), T.EXIT_UNREADABLE, "   UNREADABLE -> 2")
eq(T.verdict({"state": "ANSWERED"}), T.EXIT_ANSWERED, "   ANSWERED -> 3")
eq(T.verdict({}), T.EXIT_PROGRESS, "   ⚠️ an unknown state never reads as a verdict")
_unread = T.run(tempfile.mkdtemp(prefix="t5859-empty-"))
eq(_unread["state"], "UNREADABLE", "⛔ a missing record is UNREADABLE...")
ck("COULD NOT LOOK" in T.render(_unread) and "never closes" in T.render(_unread),
   "   ...and says it never closes this issue",
   "🔴 'I could not look' is not 'the sample is fine'")

section("8. 🔒 THE REGISTER IS REPRODUCED VERBATIM AND NOT RE-DECIDED")
_SRC = open(os.path.join(ROOT, "t58_t59.py"), encoding="utf-8").read()
for _n, _v in (("MIN_FRESH", 120), ("MIN_WEEKS", 3), ("T58_GAP", -15.0),
               ("T58_P", 0.01), ("T58_VOID_CFB", 10.0), ("T59_SPLIT", 60),
               ("T59_GAP", 10.0), ("T59_P", 0.01), ("T59_MIN_BAND", 40)):
    eq(getattr(T, _n), _v, "   %s is the register's own number" % _n)
for _q in ("over-minus-under gap <= -15 points AND p < 0.01 two-sided",
           ">=60 band beats <60 band by >= 10 points AND p < 0.01",
           "n >= 120 fresh graded NFL rows across >= 3 distinct NFL WEEKS"):
    ck(_q in _SRC, "   the spec is quoted, not paraphrased: %r" % _q[:40],
       "⛔ a paraphrase is a re-decision nobody notices")

section("9. ⚠️ T59 VOIDS ON A THIN BAND, T58 VOIDS ON THE CFB CONTROL")
_thin = dict(_d_bar)
_thin["2026-09-17"] = [r for r in _thin["2026-09-17"]
                       if r["confidence"] >= 60] + \
                      [row("over", 80, False, "2026-09-17")] * 20
_r_thin = T.run(mkrepo(_thin, {}, _s_bar))
if _r_thin["state"] == "ANSWERED":
    eq(_r_thin["t59"]["verdict"], "VOID",
       "   <60 band holds %d rows -> VOID" % _r_thin["band_low"])
    ck(_r_thin["band_low"] < T.T59_MIN_BAND, "   ...and it is under 40",
       str(_r_thin["band_low"]))
_cfb = {"2026-09-17": [row("over", 70, False, "2026-09-17")] * 40
                      + [row("under", 70, True, "2026-09-17")] * 40}
_r_void = T.run(mkrepo(_d_bar, _cfb, _s_bar))
eq(_r_void["t58"]["verdict"], "VOID",
   "🔴 CFB showing the same split VOIDS T58 — the control decides first")
note("⚠️ THE CFB CONTROL IS READ ONLY INSIDE `t58()`, which the bar gates. "
     "Under the bar no CFB statistic is computed at all — peeking at a "
     "control is the same offence as peeking at the treatment.")
