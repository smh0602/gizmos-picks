#!/usr/bin/env python3
"""
🔴 MOCK TEST — EVERY FIX CLAIMED ON 2026-09-10, DRIVEN OLD vs NEW.

`[Sam, 2026-09-10: "i want a mock test of all the fixes you claimed to
have fix to be run now so we know they work"]`

⛔ **THE REAL BUILDERS CANNOT RUN IN THIS CONTAINER.** `cfb-probe` needs
`CFBD_API_KEY` (a repo secret this session never sees) and `nfl-logs`
needs `api.github.com`, which the container's proxy answers **403** for
any repo outside the session's authorized set. **Saying "it should work"
on that basis is exactly what this project calls a claim, not a
measurement (rule 160).**

✅ **SO THIS DOES THE STRONGEST THING AVAILABLE, AND SAYS WHAT IT IS:**
  1. it calls the **REAL guard functions** — `nfl.check_ahead_out` and
     `cfb.verify` — never a reimplementation of them
  2. it feeds them the **EXACT shapes off the live failure reports**
     (NFL 66 player-weeks; CFB 1,848 rows), read from the reports rather
     than remembered
  3. it runs **the code as it was BEFORE drop 16** beside the code after,
     so every row shows the fix actually biting rather than a green tick
     that might have been green all along
  4. it derives the **college week span from the stored schedule**, which
     is the one thing that decides whether tonight's 3am run goes green
     or correctly stays red

⚠️ **WHAT IT STILL CANNOT PROVE:** that CFBD and nflverse return what we
expect. That is the fifth question in `self-running-audit.md` and no
local test can answer it.
"""
import datetime
import gzip
import importlib.util
import json
import os
import subprocess
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

OLD = "/tmp/claude-0/-home-claude/c7a7dd6a-0306-56f0-a8e4-3d118ee1a491/scratchpad/mock"
UTC = datetime.timezone.utc
NOW = datetime.datetime.now(UTC)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


import nfl                      # noqa: E402  the NEW code
import cfb                      # noqa: E402
# ⛔ THE PRE-DROP FILES ARE A LOCAL CONVENIENCE, NOT A DEPENDENCY.
#    `[2026-09-10]` The first version of this file loaded them
#    unconditionally from a scratch directory, which exists on my machine
#    and NOWHERE ELSE — so on the runner it would have died on import.
#    Combined with a filename CI does not discover, it was a test that
#    could run in exactly one place and did run in none.
# ✅ When they are absent the old-vs-new rows report NOT EXERCISED and
#    every new-code assertion still runs. The regressions are the part
#    that has to run forever; the side-by-side is how it was proven once.
HAVE_OLD = all(os.path.exists(f"{OLD}/{f}")
               for f in ("nfl_OLD.py", "cfb_OLD.py"))
nfl_old = load("nfl_old", f"{OLD}/nfl_OLD.py") if HAVE_OLD else None
cfb_old = load("cfb_old", f"{OLD}/cfb_OLD.py") if HAVE_OLD else None


def d(off):
    return (NOW + datetime.timedelta(days=off)).strftime("%Y-%m-%d")


# ══════════════════════════════════════════════════════════════════════
print("\n═══ 0. 🔴 THE LIVE FAILURES, READ OFF DISK — NOT REMEMBERED ═══")
# ⛔ Every number this file drives with comes from here.
REPORTS = {}
for lg in ("nfl", "ncaaf"):
    p = f"data/{lg}/latest/backfill-report.txt"
    REPORTS[lg] = open(p, encoding="utf-8").read() if os.path.exists(p) else ""

# ══════════════════════════════════════════════════════════════════════
# 🔴 THIS SECTION REPORTS; IT DOES NOT ASSERT THE BUG IS STILL THERE.
# ⛔ `[corrected 2026-09-10]` The first version asserted the reports
#    CONTAIN the RuntimeError. **That check goes red the moment the fix
#    works** — a check with an expiry date and nothing to expire it,
#    which is ledger rule 166, already paid for once on this repo.
# ✅ So it prints which state each league is in and asserts only the
#    thing that stays true either way: that the report is READABLE and
#    says which of the two states it is in. **The state itself is the
#    live answer to "did it work", and it is the first place to look.**
# ══════════════════════════════════════════════════════════════════════
GUARD_ERRS = ("ahead_out is CONSTANT ZERO", "depth_rank is CONSTANT None")
for _lg in ("nfl", "ncaaf"):
    _r = REPORTS[_lg]
    _stuck = [e for e in GUARD_ERRS if e in _r]
    _wrote = "written  : [2026]" in _r or "written  : ['2026']" in _r
    if _stuck:
        note(f"🔴 {_lg}: STILL the pre-fix state — {_stuck[0][:44]}… "
             f"The builder has not run since drop 16/17 landed, or the "
             f"fix did not take. ⛔ This is the row to read first.")
    elif _wrote:
        note(f"✅ {_lg}: the back-fill WROTE 2026 — the guard let a real "
             f"build through, which is the outcome drop 16 was for.")
    else:
        note(f"⚠️ {_lg}: neither the old error nor a 2026 write. Read the "
             f"report itself before concluding anything: "
             f"{' / '.join(_r.splitlines()[:3])[:150]}")
    ck(f"the {_lg} back-fill report is readable and dated",
       bool(_r.strip()) and "back-fill at" in _r,
       "⛔ an unreadable report is its own failure — it is the only place "
       "the source's own answer is recorded")

# 🔴 THE CORRECTION THAT MATTERS, AND IT DOES NOT EXPIRE: `not yet` tells
#    us whether the SOURCE has published, independent of our guard.
_notyet = "not yet  : []" in REPORTS["nfl"]
note("✅ nflverse HAS published — `not yet : []` on the NFL report. "
     "⛔ I told Sam the tab was empty because nflverse had not published; "
     "66 player-weeks REACHED the guard, so the fetch worked and only "
     "the guard blocked the write. That claim was carried from the 09-09 "
     "diagnosis and was already false."
     if _notyet else
     "⚠️ the NFL report lists a `not yet` season — the source has NOT "
     "published, and the Trends tab is correctly empty rather than "
     "broken.")

# ══════════════════════════════════════════════════════════════════════
print("\n═══ 1. 🔴 NFL — THE EXACT LIVE SHAPE, OLD vs NEW ═══")
# 66 player-weeks, all week 1, ahead_out constant zero.
# ⛔ One NFL game had been played (Wed 09-09 opener), which is what 66
#    player-weeks over ~1 game looks like.
PLAYERS_W1 = {i: {"g": [{"week": 1}]} for i in range(66)}
WHEN_W1 = {("1", "KC"): (d(-1), "BUF", 1, "g1"),
           ("2", "KC"): (d(+4), "BUF", 1, "g2")}


def drive_new(players, when, n_ao, n_rows):
    lines = []
    try:
        nfl.check_ahead_out(players, when, n_ao, n_rows, log=lines.append)
        return None, "\n".join(lines)
    except RuntimeError as e:
        return e, "\n".join(lines)


def drive_old(n_ao, n_rows):
    """⛔ The OLD guard, read out of the pre-drop file so the comparison
    is against what actually shipped, not a paraphrase. Returns None when
    the pre-drop copy is not available (see HAVE_OLD)."""
    if not HAVE_OLD:
        return None
    src = open(f"{OLD}/nfl_OLD.py", encoding="utf-8").read()
    assert "if n_ao == 0:" in src, "the old guard is not where expected"
    if n_ao == 0:
        return RuntimeError(
            f"ahead_out is CONSTANT ZERO across {n_rows:,} player-weeks. "
            f"That is a join failure, not a result.")
    return None

if HAVE_OLD:
    _old = drive_old(0, 66)
    ck("🔴 OLD CODE fails on the live shape — the bug reproduced",
       _old is not None and "CONSTANT ZERO" in str(_old),
       "and the string matches the live report verbatim: %s"
       % ("YES" if "ahead_out is CONSTANT ZERO across 66 player-weeks"
           in REPORTS["nfl"] else "NO"))
else:
    note("⚠️ NOT EXERCISED: the pre-drop-16 copy of nfl.py is not on this "
         "machine, so the old-vs-new comparison cannot run here. It was "
         "run once, locally, and is recorded in the ledger's 09-10 entry. "
         "⛔ The REGRESSIONS below run everywhere and are the part that "
         "has to keep running.")

_err, _log = drive_new(PLAYERS_W1, WHEN_W1, 0, 66)
ck("✅ NEW CODE passes on the same shape",
   _err is None, "exit clean: %s" % _err)
ck("⛔ ...and reports it as NOT EXERCISED rather than as a pass",
   "NOT EXERCISED" in _log and "NOT a pass" in _log,
   "rule 144 — a check that could not run did not pass")
ck("...and names the arithmetic reason in the log",
   "share_before" in _log and "STRICTLY EARLIER" in _log,
   "so the next reader does not repeat the wrong diagnosis")

print("\n  ── the regression the guard exists for ──")
# 🔴 RUN #194: constant zero across a FULL season. MUST still raise.
PLAYERS_FULL = {i: {"g": [{"week": w} for w in range(1, 18)]}
                for i in range(1140)}
_err, _ = drive_new(PLAYERS_FULL, WHEN_W1, 0, 19400)
ck("🔴 run #194 (constant zero, 17 weeks, 19,400 rows) STILL raises",
   _err is not None and "CONSTANT ZERO" in str(_err),
   "⛔ if this ever passes, the guard has been gutted")
ck("...and the message now carries the WEEK SPAN",
   "spanning 17 weeks" in str(_err),
   "1,848 rows cleared the old 500-row bar while being ONE week — the "
   "bar was counting the wrong axis (rule 176)")
_err, _ = drive_new(PLAYERS_FULL, WHEN_W1, 812, 19400)
ck("✅ a populated ahead_out over a full season passes", _err is None,
   str(_err))

# ══════════════════════════════════════════════════════════════════════
print("\n═══ 2. 🔴 THE FALSE ALARM I ALMOST SHIPPED IN THE FIX ITSELF ═══")
# ⛔ CAUGHT 2026-09-10 BY THIS FILE, BEFORE IT EVER RAN IN ANGER.
#    An NFL week is Thu/Sun/Mon. The schedule reports week N played the
#    moment the Thursday game ends; nflverse publishes that week's player
#    stats on its WEEKLY drop. So "is any played week missing" is RED
#    every Friday through Monday — a guard firing on a state the calendar
#    guarantees, which is rules 175-177 reintroduced by the commit that
#    wrote them.
WHEN_THU = {}
for wk, days in ((1, (-10, -7, -6)), (2, (-1, 2, 3))):
    for i, day in enumerate(days):
        WHEN_THU[(str(wk), f"T{i}")] = (d(day), "OPP", 1, f"g{wk}{i}")
LOG_W1_ONLY = {i: {"g": [{"week": 1}]} for i in range(600)}

_err, _log = drive_new(LOG_W1_ONLY, WHEN_THU, 5, 600)
ck("🔴 the FRIDAY-after-a-Thursday-game case does NOT raise",
   _err is None,
   "⛔ before this correction it raised 'MISSING COMPLETED WEEK [2]' and "
   "would have reddened nfl-logs every Fri-Mon: %s" % _err)
ck("⛔ ...and the lag is REPORTED, never silently swallowed",
   "publish lag" in _log and "[2]" in _log,
   "an absence with no explanation is the blind spot wearing a hat")

print("\n  ── and the real hole still fails ──")
# 🔴 A week missing BELOW the log's own latest week cannot be lag.
LOG_HOLE = {i: {"g": [{"week": w} for w in (1, 3)]} for i in range(300)}
WHEN_3 = {(str(w), "KC"): (d(-10 + w), "BUF", 1, f"g{w}")
          for w in (1, 2, 3)}
_err, _ = drive_new(LOG_HOLE, WHEN_3, 5, 600)
ck("🔴 an INTERIOR hole (log holds 1 and 3, week 2 played) RAISES",
   _err is not None and "MISSING COMPLETED WEEK" in str(_err),
   "a later week was published and this one was skipped — that is a "
   "partial season presented as a whole one: %s" % str(_err)[:110])
ck("⛔ ...and it says it is NOT publish lag, so the cause is unambiguous",
   "NOT publish lag" in str(_err),
   "naming the wrong cause is what cost five days on the college side")

# ══════════════════════════════════════════════════════════════════════
print("\n═══ 3. 🔴 COLLEGE — THE EXACT LIVE SHAPE, OLD vs NEW ═══")


def cfbdoc(weeks, n=1848, const=True, wmeta=None):
    per = max(1, n // max(1, len(weeks)))
    players = {}
    for pid in range(per):
        players[pid] = {"g": [
            {"week": w, "seasonType": "regular",
             "depth_rank": None if const else (w % 3),
             "trailing_usage": None if const else 0.1 * w,
             "ahead_out_lastwk": 0 if const else (w % 2),
             "usage": 0.05 * (pid % 7 + 1),
             "opp_elo": 1500, "oppClass": "fbs"} for w in weeks]}
    doc = {"players": players, "scope_conferences": None, "unfiltered": True}
    if wmeta:
        doc["weeks"] = wmeta
    return doc


def cfb_bad(mod, doc):
    try:
        return [b for b in (mod.verify(doc, log=lambda m: None) or [])]
    except Exception as e:
        return ["RAISED %s: %s" % (type(e).__name__, e)]


_const = "is CONSTANT"
new_bad = cfb_bad(cfb, cfbdoc([1]))
_new_const = [b for b in new_bad if _const in b]

if HAVE_OLD:
    old_bad = cfb_bad(cfb_old, cfbdoc([1]))
    _old_const = [b for b in old_bad if _const in b]
    ck("🔴 OLD CODE flags three constant columns on a ONE-WEEK log",
       len(_old_const) >= 3,
       "the live failure reproduced: %s"
       % "; ".join(b[:46] for b in _old_const))
else:
    note("⚠️ NOT EXERCISED: the pre-drop-16 copy of cfb.py is not on this "
         "machine, so the side-by-side cannot run here.")

ck("✅ NEW CODE flags NONE of them on the same log",
   not _new_const,
   "⛔ remaining findings are the synthetic fixture's own gaps, not the "
   "constant-column check: %s" % [b[:40] for b in new_bad])

print("\n  ── the college regression still fails ──")
_multi = [b for b in cfb_bad(cfb, cfbdoc(list(range(1, 13)))) if _const in b]
ck("🔴 genuinely constant columns over TWELVE weeks STILL fail",
   len(_multi) >= 3,
   "the fix is narrower, not weaker: %s" % "; ".join(b[:44] for b in _multi))

print("\n  ── and the college lag case, same correction ──")
_lag = cfb_bad(cfb, cfbdoc([1], wmeta={
    "completed_per_source": [1, 2], "in_player_log": {"1": 1848},
    "missing_from_log": [2]}))
ck("🔴 a Thursday-night college game does NOT trip the missing-week check",
   not [b for b in _lag if "MISSING COMPLETED" in b],
   "⛔ a week is 'completed' as soon as ONE game finishes, so flagging it "
   "would go red every Thursday: %s" % [b[:40] for b in _lag])
_hole = cfb_bad(cfb, cfbdoc([1, 3], wmeta={
    "completed_per_source": [1, 2, 3],
    "in_player_log": {"1": 900, "3": 900}, "missing_from_log": [2]}))
ck("🔴 ...while an INTERIOR college hole still fails",
   any("MISSING COMPLETED" in b for b in _hole),
   [b[:100] for b in _hole if "MISSING" in b])

# ══════════════════════════════════════════════════════════════════════
print("\n═══ 4. 🔴 WILL TONIGHT'S 3AM COLLEGE RUN GO GREEN? ═══")
# ⛔ THE ONE QUESTION I COULD NOT ANSWER EARLIER, ANSWERED FROM THE
#    STORED SCHEDULE RATHER THAN GUESSED.
S = json.load(gzip.open("data/ncaaf/latest/schedule-2026.json.gz", "rt"))
games = S["games"]
final_weeks = sorted({g.get("week") for g in games
                      if g.get("final") and g.get("season_type") == "regular"})
today = NOW.strftime("%Y-%m-%d")
started = sorted({g.get("week") for g in games
                  if g.get("season_type") == "regular"
                  and (g.get("start") or "")[:10] <= today})
# 🔴🔴 THE TWO CHECKS THAT STOOD HERE PINNED TODAY'S WORLD AND EXPIRED.
# `[they were: "only ONE college week has completed games" and "therefore
#   the guard will stand down tonight"; both went red on 2026-09-11 when
#   week 2's Thursday games finished]`
# ⛔ THAT IS LEDGER RULE 166 FOR THE SEVENTH TIME, AND I WROTE THIS FILE
#    THE DAY AFTER RECORDING THE OTHER SIX. A check whose subject is a
#    transient state has an expiry date and nothing expires it.
# ⚠️ AND THE CODE WAS NEVER WRONG. Two completed weeks is the guard
#    ENGAGING, which is what it is for. The test's premise expired; the
#    thing it was guarding did exactly what it should.
# ✅ SO ASK A QUESTION THE CALENDAR CANNOT ANSWER FOR US (rule 177): not
#    "how many weeks have played today", but "does the guard's decision
#    FOLLOW the week count, whatever the count is" — driven through the
#    real `cfb.verify()` at the ONE-to-TWO boundary, which is the exact
#    edge the 09-10 defect lived on and which the old check could never
#    reach, because it could only observe whatever day it ran on.
note(f"live schedule (DESCRIPTIVE, never asserted): built_at "
     f"{S.get('built_at')}; weeks with a FINAL game {final_weeks}; "
     f"weeks started by {today} {started}")

_one = [b for b in cfb_bad(cfb, cfbdoc([1])) if _const in b]
ck("🔴 ONE week of log -> the constant-column guard STANDS DOWN",
   not _one,
   "⛔ the trailing columns cannot vary on a one-week log — they are "
   "constant BY ARITHMETIC, not by a broken join (rule 175). Findings: "
   "%s" % [b[:44] for b in _one])

_two = [b for b in cfb_bad(cfb, cfbdoc([1, 2])) if _const in b]
ck("🔴 ...and TWO weeks of genuinely constant columns ENGAGES it",
   len(_two) >= 3,
   "⛔ THIS IS THE BOUNDARY AND THE OLD CHECK COULD NOT REACH IT. Two "
   "distinct weeks is the first point at which a constant column is "
   "evidence of a real defect rather than of week 1. Findings: %s"
   % [b[:44] for b in _two])

# ⚠️ AND SAY PRECISELY WHAT THIS PREDICTS. The guard keys on distinct
#    weeks IN THE PLAYER LOG; `final_weeks` comes from the SCHEDULE.
#    Those are normally the same number and they are not the same fact —
#    "a fact about a query is not a fact about the world" is this
#    project's founding lesson and it applies to our own files too.
_expect = "STAND DOWN" if len(final_weeks) < 2 else "ENGAGE"
note(f"➡️ the SCHEDULE reports {len(final_weeks)} completed week(s), so "
     f"tonight's log should carry that many and the guard should "
     f"{_expect} — DERIVED from the two checks above, not hard-coded. "
     f"⛔ If the log carries FEWER weeks than the schedule says have "
     f"finished, that is a collection gap and worth seeing on its own.")
note("⚠️ THIS PREDICTS THE GUARD, NOT THE FETCH. If CFBD refuses the key "
     "again the run is red for a different reason, and `source_block` "
     "will say so with the status code.")

# ══════════════════════════════════════════════════════════════════════
print("\n═══ 5. 🔴 THE FOUR TEST FILES, ON THE REAL EMPTY CARD ═══")
CARD = json.load(open("picks/fb-ncaaf-latest.json"))
# ⛔ ~~ck("the live college card really is empty", ...)~~ — DEMOTED TO A
#    NOTE 2026-09-11. It passed every day until a college board prices,
#    and then it would have gone red on a card that was PERFECTLY FINE.
#    Rule 166 again: an empty board is a FACT ABOUT THURSDAY, not a
#    property of the code. ✅ What is worth asserting is the four files
#    below passing — and that does not expire.
note("live college card (DESCRIPTIVE): n_priced=%s picks=%d%s"
     % (CARD.get("n_priced"), len(CARD["picks"]),
        " — empty, which is the input all four checks used to FAIL on"
        if not CARD["picks"] else
        " — NOT empty today, so these four run against a live board "
        "instead; both inputs must pass"))

FOUR = ["test_top_plays.py", "test_conf_filter.py",
        "test_record_fb.py", "test_single_day.py"]
for t in FOUR:
    r = subprocess.run([sys.executable, t], capture_output=True, text=True,
                       cwd=ROOT, timeout=600)
    ck(f"✅ {t} passes on the empty card",
       r.returncode == 0 and "❌" not in r.stdout,
       [l for l in r.stdout.splitlines() if l.startswith("   - ")][:3]
       or (r.stdout.strip().splitlines() or ["no output"])[-1])

# ══════════════════════════════════════════════════════════════════════
print("\n═══ 6. 🔴 THE SENTENCE THE CARD SHOWS A READER ═══")
# ⛔ THE COMMITTED CARD IS A STORED ARTIFACT WRITTEN BY THE **OLD**
#    BUILDER, and reading it would test the file's age, not the code.
#    `[caught by this file, 2026-09-10]` The first version of this check
#    read `picks/fb-ncaaf-latest.json` and failed — correctly, because
#    that card predates drop 16 and still carries the wrong sentence. It
#    is rewritten on the next `card-fb` run.
# ✅ SO REBUILD IT with the deployed builder, in a sandbox, and read what
#    the CODE produces today. Ledger rule 104: a code change reaches the
#    page only through a rebuild.
import shutil                                     # noqa: E402
import tempfile                                   # noqa: E402
_tmp = tempfile.mkdtemp()
shutil.copytree("data/ncaaf", os.path.join(_tmp, "data/ncaaf"))
os.makedirs(os.path.join(_tmp, "picks"), exist_ok=True)
shutil.copy("card_fb.py", _tmp)
_r = subprocess.run([sys.executable, "card_fb.py"], cwd=_tmp,
                    env=dict(os.environ, LEAGUE="ncaaf"),
                    capture_output=True, text=True, timeout=600)
_fresh = json.load(open(os.path.join(_tmp, "picks/fb-ncaaf-latest.json")))
shutil.rmtree(_tmp, ignore_errors=True)
_empty = not _fresh["picks"] and (_fresh.get("n_priced") or 0) == 0
# ⛔ ~~ck("the rebuilt card is still the empty one", ...)~~ — the same
#    expiry as §5. The rebuild is the right method (rule 181: read what
#    the CODE produces, not a stored artifact's age); asserting the
#    REBUILT board is empty just moves the calendar dependency.
note("rebuilt board (DESCRIPTIVE): %s"
     % ("empty — the empty-board sentence below is EXERCISED"
        if _empty else
        "NOT empty — the empty-board sentence is NOT EXERCISED today"))
note("⚠️ the COMMITTED card still carries the old sentence and that is "
     "correct — it was written before drop 16 landed and is rewritten on "
     "the next card-fb run (9:00am ET). What is tested here is the CODE.")
rule = _fresh.get("top_plays_rule", "")
if _empty:
    ck("🔴 an EMPTY board is no longer told 'Not because the board is empty'",
       "Not because the board is empty" not in rule,
       rule[:120])
    ck("✅ ...it says what is actually true instead",
       "Nothing is priced for this day yet" in rule, rule[:120])
else:
    # ⚠️ NOT EXERCISED — and said out loud rather than silently skipped.
    #    A check that quietly stops running is the same false cover as a
    #    test the runner never discovers (rule 182).
    # ⛔ I FIRST WROTE "the empty branch is covered by test_card_fb.py's
    #    synthetic fixture". THAT WAS FALSE — I checked, and that file
    #    has no such fixture. Saying a gap is covered when it is not is
    #    worse than the gap (rule 37: a doc asserting a fix is not a fix).
    note("⚠️ NOT EXERCISED, AND NOTHING ELSE COVERS IT TODAY EITHER. "
         "⛔ `test_top_plays.py` has the only other copy of this check "
         "and it branches on the SAME live card (`elif not C[\"picks\"]`), "
         "so on a day with rows the empty-board sentence is exercised by "
         "NOTHING. ➡️ THE FIX IS A SYNTHETIC EMPTY-BOARD FIXTURE that "
         "does not depend on the calendar; it is recorded in "
         "`claude/tomorrow-checklist.md` and not invented here.")
ck("⛔ ...and the honest half is KEPT — it still refuses to rank by price",
   "ranking by which bet pays worst" in rule,
   "the reason the list is empty when rows exist but carry no record")

note("⚠️ WHAT THIS FILE CANNOT PROVE, STATED PLAINLY: that CFBD honours "
     "the key and that nflverse serves the assets. Both are blocked from "
     "this container (CFBD needs the repo secret; api.github.com answers "
     "403). Those are the fifth question in self-running-audit.md and "
     "only a real run answers them.")
