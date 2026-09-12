#!/usr/bin/env python3
"""
🔴 5,613 OF 6,116 PUBLISHED RANKS BROKE A TIE ARBITRARILY. 92%.

`[measured 2026-09-11 against the live college board]` Both builders
ranked with a bare ordinal:

    for i, (o, _) in enumerate(rows):
        tbl[o][pos][f + "_rank"] = i + 1

**So equal values came out of `sorted()` in whatever order the dict
yielded them, and each was handed a DIFFERENT rank.**

⛔ **THE WORST CASES ARE NOT EDGE CASES — THEY ARE WHOLE COLUMNS:**

    RB  interceptions allowed   142 defences ALL at 0.0  ->  ranked 1-142
    WR  passing touchdowns      142 defences ALL at 0.0  ->  ranked 1-142
    TE  rushing touchdowns      130 defences ALL at 0.0  ->  ranked 1-130

**One team was told it was best in the country and another worst at a
statistic where they are identical.** ⚠️ And it was not confined to the
junk columns: **QB rushing yards had 93 rows tied-but-differently-ranked,
RB rushing yards 53, WR receiving yards 50** — columns a reader reads.

✅ **THE VALUES WERE NEVER WRONG, AND THAT WAS MEASURED FIRST.** All
**6,116** stat cells reproduce the player log exactly across all eleven
stats. ⛔ **This file therefore also asserts that no stat value moved** —
a "fix" that quietly changed a number would be a far worse bug than the
one being fixed.

⚠️ **AND THE PAGE HELD A SECOND COPY.** `index.html` ranked again in
JavaScript, with the same ordinal and the same defect, so fixing only the
builder would have left the reader looking at the bug. The page now reads
the file's rank. **Rule 66: one number per fact, the same everywhere.**

⛔ **NOTHING HERE PINS THE CALENDAR.** `test_drop16_fixes.py` asserted
"only ONE college week has completed games", went red the moment week 2
finished, and reddened three runs (rule 192). Every check below is about
the RELATIONSHIP between values and ranks, which no date can falsify.
"""
import collections
import gzip
import re
import json
import os
import sys

from tcheck import ck, eq, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import ranking  # noqa: E402

POS = ("QB", "RB", "WR", "TE")
STATS = ("rec", "rec_yds", "rec_td", "car", "rush_yds", "rush_td",
         "att", "cmp", "pass_yds", "pass_td", "int")

print("\n═══ 1. 🔴 TIES SHARE THE BEST RANK ═══")
r = ranking.competition_ranks([("a", 100), ("b", 90), ("c", 90), ("d", 80)])
eq((r["a"][0], r["b"][0], r["c"][0], r["d"][0]), (1, 2, 2, 4),
   "🔴 [100, 90, 90, 80] ranks 1, 2, 2, 4")
note("⛔ NOT 1,2,3,4 — that is the bug. NOT 1,2,2,3 ('dense') — that "
     "would misreport how many teams are genuinely ahead of you.")
eq(r["b"][1], r["c"][1],
   "🔴 ...and tied teams share the PERCENTILE too")
note("⛔ A shared rank beside two different percentiles just moves the "
     "contradiction somewhere quieter.")
ck("✅ order of the input does not change the answer",
   ranking.competition_ranks([("c", 90), ("d", 80), ("a", 100), ("b", 90)])
   == r,
   "⛔ THE ORIGINAL BUG WAS EXACTLY AN ORDER DEPENDENCE — equal values "
   "ranked by whatever order the dict yielded them")

print("\n═══ 2. 🔴 A COLUMN WITH NO SPREAD PUBLISHES NOTHING ═══")
ck("🔴 every value identical -> NO rank at all",
   ranking.competition_ranks([("a", 0.0), ("b", 0.0), ("c", 0.0)]) == {},
   "⛔ not rank 1, not rank N, not a shared rank — nothing, so the page "
   "renders a dash. 142 defences at 0.0 interceptions allowed to RBs is "
   "not a leaderboard")
ck("...and that holds for a non-zero constant too",
   ranking.competition_ranks([("a", 7.0), ("b", 7.0)]) == {},
   "the rule is NO SPREAD, not 'all zero' — it is derived from the data, "
   "never from a hard-coded list of impossible football")
note("🔴 THE ALTERNATIVE WAS A HARD-CODED LIST — running backs do not "
     "throw, receivers do not intercept. ⛔ That list would be a second "
     "source of truth about the sport, wrong the first time a running "
     "back throws a touchdown, and blind to any column that goes "
     "degenerate for a reason nobody predicted.")

print("\n═══ 3. ⚠️ A MOSTLY-ZERO COLUMN STILL RANKS ═══")
r = ranking.competition_ranks([("a", 3), ("b", 0), ("c", 0), ("d", 0)])
eq((r["a"][0], r["b"][0], r["c"][0], r["d"][0]), (1, 2, 2, 2),
   "⚠️ RB carries allowed is 99% zeros — those defences are genuinely "
   "TIED, and one shared rank is the honest answer")
ck("⛔ a None value is excluded rather than treated as zero",
   ranking.competition_ranks([("a", None), ("b", 5), ("c", 1)]).get("a")
   is None,
   "a missing measurement is not a measurement of zero")

print("\n═══ 4. ⛔ apply_ranks REMOVES A RANK IT CANNOT JUSTIFY ═══")
tbl = {"X": {"QB": {"games": 9, "v": 5.0, "v_rank": 1, "v_pct": 100.0}},
       "Y": {"QB": {"games": 9, "v": 5.0, "v_rank": 2, "v_pct": 50.0}}}
blank = ranking.apply_ranks(tbl, ("QB",), ("v",), lambda c: c["games"] >= 1)
ck("🔴 a stale rank from an earlier build is DELETED, not left behind",
   "v_rank" not in tbl["X"]["QB"] and "v_pct" not in tbl["Y"]["QB"],
   "⛔ X and Y are tied at 5.0 so the column has no spread. A leftover "
   "`v_rank: 1` would be read by the page as a real rank — absence is "
   "the only unambiguous way to say 'this cannot be ranked'")
eq(blank, 1, "...and the caller is told how many columns went blank")

print("\n═══ 5. 🔴 THE LIVE TABLES, REBUILT WITH THE REAL BUILDERS ═══")
# ⚠️ NO CALENDAR ANYWHERE HERE. This asserts a RELATIONSHIP — that no
#    published rank contradicts another rank in its own column — which is
#    true in week 1 and in week 15 alike.
import cfb   # noqa: E402


def arbitrary_ties(tbl, fields):
    """Rows sharing a value but NOT sharing a rank. Must be zero."""
    bad = 0
    for pos in POS:
        for f in fields:
            byval = collections.defaultdict(set)
            for row in tbl.values():
                cell = row.get(pos)
                if not cell or cell.get(f) is None:
                    continue
                rk = cell.get(f + "_rank")
                if rk is not None:
                    byval[cell[f]].add(rk)
            bad += sum(len(v) - 1 for v in byval.values() if len(v) > 1)
    return bad


LOG = "data/ncaaf/latest/players-2026.json.gz"
if not os.path.exists(LOG):
    note("⚠️ NOT EXERCISED: the college player log is not on this "
         "machine, so the live-table checks cannot run here. ⛔ Sections "
         "1-4 drive the real ranker and still ran.")
else:
    P = json.load(gzip.open(LOG, "rt"))
    built = cfb.build_side(P, "def", log=lambda m: None)
    new = built["defences"]
    old = json.load(gzip.open(
        "data/ncaaf/latest/allowed-by-position-2026.json.gz", "rt"))["defences"]

    eq(arbitrary_ties(new, STATS + ("total_yds", "total_td")), 0,
       "🔴 ZERO published ranks contradict a tie")
    note("⚠️ THE SAME COUNT ON THE DEPLOYED FILE IS THE MEASUREMENT THIS "
         "FIX EXISTS FOR: %d." % arbitrary_ties(old, STATS))

    # 🔴🔴 THE CHECK THAT MATTERS MOST: no STAT VALUE moved.
    moved = [(t, pos, s, old[t][pos].get(s), (new.get(t) or {}).get(pos, {}).get(s))
             for t in old for pos in POS if old[t].get(pos)
             for s in STATS
             if abs((old[t][pos].get(s) or 0)
                    - (((new.get(t) or {}).get(pos) or {}).get(s) or 0)) > 1e-9]
    ck("🔴 NOT ONE STAT VALUE MOVED — this changes ranks only",
       not moved,
       "⛔ all 6,116 cells reproduced the player log BEFORE this change "
       "and must still. Moved: %s" % moved[:3])

    # total yards is derived, and the arithmetic is checked on every row
    bad = [(t, pos) for t, row in new.items() for pos in POS if row.get(pos)
           for c in [row[pos]]
           if abs(c["total_yds"] - (c["pass_yds"] + c["rush_yds"]
                                    + c["rec_yds"])) > 0.01]
    ck("✅ total_yds = passing + rushing + receiving, on every row",
       not bad,
       "⚠️ a QB row is much larger than the others because it INCLUDES "
       "his passing yards — that is the definition, not a bug. Bad: %s"
       % bad[:3])
    note("⛔ total_yds is computed in the BUILDER and stored. The page "
         "must never add it up itself — rule 66, and a page that summed "
         "its own total could disagree with the one the file ranks.")

    # 🔴 THE SAME ARITHMETIC, ASKED OF THE NEW COLUMN. Sam, 2026-09-11:
    #    "add a total touchdowns before rushing touchdowns as well."
    # ⛔ IT IS CHECKED AGAINST THE SAME THREE PARTS AS total_yds ON
    #    PURPOSE. Two columns on one screen both called "Total" must not
    #    mean two different sums, and the only way to own that is to
    #    assert the definition rather than describe it in a comment.
    badtd = [(t, pos) for t, row in new.items() for pos in POS if row.get(pos)
             for c in [row[pos]]
             if abs(c["total_td"] - (c["pass_td"] + c["rush_td"]
                                     + c["rec_td"])) > 0.01]
    ck("✅ total_td = passing + rushing + receiving, on every row",
       not badtd,
       "⚠️ a QB row counts the touchdowns he THREW, exactly as the yards "
       "column counts the yards he threw for. Bad: %s" % badtd[:3])
    ck("🔴 cfb.py and nfl.py define total_td from the SAME three parts",
       (re.search(r'TD_PARTS\s*=\s*\("pass_td",\s*"rush_td",\s*"rec_td"\)',
                  open("cfb.py", encoding="utf-8").read()) is not None
        and re.search(r'TD_PARTS\s*=\s*\("pass_td",\s*"rush_td",\s*"rec_td"\)',
                      open("nfl.py", encoding="utf-8").read()) is not None),
       "⛔ one page reads both leagues' files, so a column that means "
       "something different in each is worse than a missing column")

print("\n═══ 6. ⚠️ THE PAGE MUST NOT RANK AGAIN ═══")
html = open("index.html", encoding="utf-8").read()
# ⛔ ASK THE QUESTION, DO NOT SUBSTRING-MATCH THE SOURCE. The first form
#    of this check read a needle with spaces in it against a haystack it
#    had stripped the spaces OUT of, and failed on correct code. This
#    repo has three dead comment-strippers and a `"<= TARGET" not in src`
#    to show for the same instinct.
import re  # noqa: E402
_reads_file_rank = re.search(
    r"rank\s*:\s*e\[\s*fbMetric\s*\+\s*['\"]_rank['\"]\s*\]", html)
ck("🔴 index.html reads the file's rank instead of computing one",
   bool(_reads_file_rank),
   "⛔ the page held a SECOND COPY of the ranking with the same ordinal "
   "bug, so fixing only the builder would have left the reader looking "
   "at it")
ck("⛔ ...and the old JavaScript ordinal is gone",
   "rankedAll.map((r, i) => [r.team, i + 1])" not in html,
   "`.sort()` then `i + 1` is the exact defect, in JavaScript")
# 🔴🔴 AND THE DROPDOWN MUST READ THAT SAME LIST.
# `[caught 2026-09-11 by rendering the deployed page headless, AFTER this
#   file was already green]` The filter below was real and correct, and
#   "Total yards" STILL appeared in the picker hours before any table
#   carried the column — because `fbControls()` built its OWN
#   `fbMetricsFor(fbPos)` and never saw the filter.
# ⛔ A SECOND COPY OF THE LIST, IN THE SAME DROP THAT FIXED A SECOND COPY
#   OF THE RANKING. Asserting the filter EXISTS is not asserting that
#   anything USES it — which is the same gap as "is anything there?" vs
#   "is anything wrong?" (rule 178).
_ctl = html[html.index("function fbControls("):]
_ctl = _ctl[:_ctl.index("\nfunction ")]
ck("🔴 fbControls RECEIVES the metric list instead of building one",
   "function fbControls(avail, mets)" in html,
   "⛔ it used to call `fbMetricsFor(fbPos)` itself, so a caller that "
   "filtered the list changed the TABLE and not the PICKER")
# ⛔ EXCLUDE THE DEFINITION LINE. The first form of this counted
#    `fbControls(avail, mets)` across the whole file and found TWO —
#    because `function fbControls(avail, mets){` contains the same
#    substring. A bare substring search over source reads the
#    DECLARATION as if it were a CALL, which is the trap this repo has
#    three dead comment-strippers to show for.
_calls = [m for m in re.findall(r"(?<!function )fbControls\(([^)]*)\)", html)]
ck("⛔ ...and every render call site passes a list, or null on purpose",
   len(_calls) == 2 and all("," in c for c in _calls),
   "the no-doc branch passes null DELIBERATELY — there is no table to "
   "filter against and the picker should still work. Found: %s" % _calls)
# 🔴 THE DROPDOWN ORDER IS SAM'S, AND IT IS ASSERTED RATHER THAN
#    DESCRIBED. 2026-09-11: "i want the allowed dropdown to be formatted
#    like this from top to bottom, total yards, rushing yards,
#    recieibing yards, carries, receptions, rushing touchdowns,
#    receiving touchdowns; add a total touchdowns before rushing
#    touchdowns as well."
# ⛔ THE ORDER IS A PROPERTY OF FB_METRICS AND OF NOTHING ELSE. The old
#    `fbMetricsFor` re-sorted by where the position sat in each row's
#    `pos` list, which produced a DIFFERENT order for QB, RB, WR and TE —
#    so any order written into the array could hold for at most one of
#    them. This checks the array AND that nothing re-sorts it.
_arr = html[html.index("const FB_METRICS = ["):]
_arr = _arr[:_arr.index("\n];")]
_order = re.findall(r"\{\s*k\s*:\s*'([a-z_]+)'", _arr)
_want = ["total_yds", "rush_yds", "rec_yds", "car", "rec",
         "total_td", "rush_td", "rec_td"]
ck("🔴 FB_METRICS opens in exactly the order Sam specified",
   _order[:len(_want)] == _want,
   "⛔ the three QB-only columns follow; he did not place them and "
   "guessing a slot inside his list would be inventing an instruction. "
   "Got: %s" % _order[:len(_want)])
# ⛔ ASKED OF THE FUNCTION BODY, NOT OF THE FILE. The first form of this
#    check searched the whole of index.html for the old sort expression
#    and FAILED ON CORRECT CODE, because the struck comment directly
#    above `fbMetricsFor` quotes that expression verbatim so the record
#    of what was removed survives. A source check that reads its own
#    documentation as an instance of the bug is the same defect this
#    file already carries a note about, in the same drop.
_mf = html[html.index("function fbMetricsFor(pos){"):]
_mf = _mf[:_mf.index("\n}")]
ck("⛔ ...and fbMetricsFor no longer re-sorts that order",
   ".sort(" not in _mf,
   "a per-position sort makes the specified order unreachable for three "
   "of the four positions. Body: %s" % _mf.replace("\n", " "))
ck("✅ Total touchdowns is offered on every position, like Total yards",
   "{ k:'total_td', l:'Total touchdowns',     pos:['QB','RB','WR','TE'] }"
   in html,
   "it is the twin of total_yds and must not be narrower than it")
ck("✅ the metric picker is derived from the loaded data",
   "_probe[m.k] !== undefined" in html,
   "⚠️ the builder and the page do NOT arrive together — the page ships "
   "on upload, the table on the next scheduled run. Deriving the picker "
   "means `total_yds` appears when the data does, with no ordering to "
   "get right (rule 191)")

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that any rank is PREDICTIVE. "
     "These tables are DESCRIPTIVE and carry no confidence number — "
     "strength-of-schedule adjustment was tested on this data and made "
     "player projections WORSE in both sports. What is owned here is "
     "only that a rank means the same thing for every row in its column.")
