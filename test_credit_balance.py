#!/usr/bin/env python3
"""💰 THE CREDIT BALANCE WATCHER.

🔴 THE RESERVE GUARD WAS REAL AND NOTHING EVER SAID SO.
`collect.py:409` and `:1462` refuse to spend past `RESERVE = 750`, and
`credits_remaining` — the API's own `x-requests-remaining` — is written
into every paid snapshot. MEASURED on origin/main before this: `watchdog.py`
and `runs_report.py` mentioned it **zero times**.

⛔ SO THE FIRST VISIBLE SYMPTOM OF A QUOTA PROBLEM WAS PULLS QUIETLY
STANDING DOWN, which is indistinguishable from missing data, a dropped
cron or a dead feed. The one failure mode that hands you a plausible
wrong explanation.

⚠️ THE STALE CASE IS THE ONE THAT MATTERS. A watcher that reads a
three-day-old balance and reports HEALTHY is worse than no watcher: it
ACTIVELY ARGUES AGAINST the correct diagnosis while pulls stand down. A
guard that only drives the healthy and critical ends never asks it.

⛔ AND EVERY EXPECTATION HERE IS DERIVED FROM THE SYNTHETIC TREE IT
BUILDS, never from a literal count of the live repo. The boards move
under these tests and a hard-coded number reddens on correct code —
the trap #51 fixed.

# ⚠️ NO BACKSLASHES IN A DECLARED `find`. The harness reads this file as
#    TEXT while Python reads this docstring as a STRING, so `\\s` here is
#    `\\\\s` on disk and never matches the single-escaped regex in
#    watchdog.py — the harness called it MALFORMED, correctly. The
#    mutation below targets the RETURN instead, which is the same defect
#    (a floor that ignores collect.py) with no escaping to get wrong.
# @vacuity ⛔ RESERVE is READ from collect.py, never copied as a literal
#   file: watchdog.py
#   find:     return int(m.group(1)) if m else None
#   with:     return 750
#
# @vacuity 🔴 the two copies of the spend floor must AGREE
#   file: budget.py
#   find: PLAN, RESERVE, GAMES = 20000, 750, 15
#   with: PLAN, RESERVE, GAMES = 20000, 900, 15
#
# @vacuity ⛔ the balance is the STORED READING, not budget.py's PLAN
#   file: watchdog.py
#   find:     readings = _paid_readings()
#   with:     readings = [("2026-01-01T00:00:00Z", int(re.search(r"^PLAN = (\\d+)", open(os.path.join(SRCDIR, "budget.py"), encoding="utf-8").read(), re.M).group(1)), "budget.py")]
#
# @vacuity 🔴 a reading older than the newest paid pull reports STALE
#   file: watchdog.py
#   find:     stale = bool(newest_pull and at and newest_pull > at)
#   with:     stale = False
#
# @vacuity at or under the floor it ESCALATES, it does not merely warn
#   file: watchdog.py
#   find:     state = ("CRITICAL" if bal <= reserve else
#   with:     state = ("LOW" if bal <= reserve else
#
# @vacuity the reading is reported even when it is not a finding
#   file: watchdog.py
#   find:     if getattr(rep, "note_credits", None):
#   with:     if getattr(rep, "note_credits", None) and rep.items:
#
# @vacuity ⛔ a snapshot with no balance is not read as a balance of None
#   file: credits.py
#   find:     have = [r for r in rows if isinstance(r[1], int) and r[0]]
#   with:     have = [r for r in rows if r[0]]
#
# @vacuity ⚠️ rule 67: 6a's healthy tree really is JUDGED by the reconciliation
#   file: watchdog.py
#   find: RECON_WINDOW_H = 24
#   with: RECON_WINDOW_H = 0
#
# @vacuity 🔴 the reconciliation is SILENT on a tree where every credit is on a snapshot
#   file: watchdog.py
#   find: RECON_WARN, RECON_BROKEN = 30, 200
#   with: RECON_WARN, RECON_BROKEN = -1, 200
#
# @vacuity 🔴 ...and a reconciliation that ignores what each pull spent fires on it
#   file: watchdog.py
#   find:         residue = prev[1] - cur[2] - cur[1]
#   with:         residue = prev[1] - cur[1]
#
# @vacuity the report's keys are asked on the tree that always holds a reading
#   file: watchdog.py
#   find:         "newest_paid_pull": newest_pull,
#   with:         "newest_pull": newest_pull,
#
# @vacuity ⛔ the live tree is judged at the REAL clock, never a frozen one
#   file: watchdog.py
#   find:     now = now or datetime.datetime.now(UTC)
#   with:     now = now or datetime.datetime(2026, 9, 18, 12, 0, tzinfo=UTC)
#
# @vacuity ⚠️ rule 67: section 8's planted finding is SEEN on the live tree
#   file: watchdog.py
#   find:     sev("credits:unrecorded",
#   with:     sev("recon:unrecorded",
#
# @vacuity 🔴 section 8 reads the planted child's verdict, not just its output
#   file: watchdog.py
#   find:     worst = sorted((r for r in steps if r[4] > 0), key=lambda r: -r[4])[:3]
#   with:     worst = sorted((r for r in steps if r[4] > 0), key=lambda r: -r[4])[:3]; rep.note_credits = None if gap > 10 ** 5 else getattr(rep, 'note_credits', None)
"""
import datetime
import gzip
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section, shown

import watchdog as W          # noqa: E402

WSRC = io.open(os.path.join(ROOT, "watchdog.py"), encoding="utf-8").read()
UTC = datetime.timezone.utc
FMT = "%Y-%m-%dT%H:%M:%SZ"

# ══════════════════════════════════════════════════════════════════════
# 🔴 THE STAY-GREEN PLANT (section 8). A credits finding on the LIVE repo
#    tree is production's news, not this file's failure. Section 8 re-runs
#    this whole file as a child with PLANT_ENV set; in that child `W` is
#    watchdog.py with ONE line changed, so the reconciliation reports a
#    huge unrecorded spend on a tree that holds CLAUDE.md (the live repo,
#    or a vacuity tree's full checkout) and on no synthetic Tree (a temp
#    dir holding only collect.py and data/). ⛔ Popped, never read, so a
#    grandchild cannot inherit it. The plant is applied in memory: nothing
#    on disk changes, so a parallel sweep cannot see it.
# ══════════════════════════════════════════════════════════════════════
PLANT_ENV = "TEST_CREDIT_BALANCE_PLANT"
PLANT_FIND = "    gap = sum(r[4] for r in steps if r[4] > 0)"
PLANT_WITH = ("    gap = sum(r[4] for r in steps if r[4] > 0) + (10 ** 6 if "
              "os.path.isfile(os.path.join(ROOT, \"CLAUDE.md\")) else 0)")
PLANTED = os.environ.pop(PLANT_ENV, "") == "1"
if PLANTED:
    import types
    if WSRC.count(PLANT_FIND) != 1:
        # ⛔ A plant that changes nothing is rule 67 one level up.
        print("PLANT DID NOT APPLY: %d match(es) in watchdog.py"
              % WSRC.count(PLANT_FIND))
        sys.exit(3)
    W = types.ModuleType("watchdog_planted")
    W.__file__ = os.path.join(ROOT, "watchdog.py")
    exec(compile(WSRC.replace(PLANT_FIND, PLANT_WITH), W.__file__, "exec"),
         W.__dict__)


class Tree:
    """A synthetic data tree plus a synthetic `collect.py`.

    ⛔ `W.ROOT` and `W.SRCDIR` are module state, so both are swapped and
    RESTORED — the same contract `test_watchdog.py` already uses.
    """

    def __init__(self, reserve=750):
        self.d = tempfile.mkdtemp()
        self.reserve = reserve
        io.open(os.path.join(self.d, "collect.py"), "w",
                encoding="utf-8").write(
            "# synthetic\nRESERVE = %d\n" % reserve)

    def pull(self, when, balance, kind="gamelines", field=True, used=None):
        """Write one paid snapshot. `when` is a datetime."""
        day = when.strftime("%Y-%m-%d")
        hhmm = when.strftime("%H%M")
        p = os.path.join(self.d, "data", day, kind)
        os.makedirs(p, exist_ok=True)
        doc = {"pulled_at": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
               "endpoint": "bulk", "n_games": 1, "games": []}
        if field:
            doc["credits_remaining"] = balance
        if used is not None:
            doc["credits_used"] = used
        with gzip.open(os.path.join(p, "%s.json.gz" % hhmm), "wt") as fh:
            json.dump(doc, fh)
        return self

    def __enter__(self):
        self._r, self._s = W.ROOT, W.SRCDIR
        W.ROOT, W.SRCDIR = self.d, self.d
        return self

    def __exit__(self, *a):
        W.ROOT, W.SRCDIR = self._r, self._s
        shutil.rmtree(self.d, ignore_errors=True)


def one(items, key=None, prefix=None):
    """The matching finding, or an EMPTY dict.

    ⛔ NEVER `[0]`. Under a mutation that removes the finding, a bare
    subscript raises IndexError and this FILE DIES — `tcheck` correctly
    refuses to call that a pass, but every check below the crash never
    runs, so the mutation is reported by a stack trace instead of by the
    checks written to catch it. A guard must FAIL, not crash.
    """
    for i in items:
        if key and i.get("key") == key:
            return i
        if prefix and str(i.get("key", "")).startswith(prefix):
            return i
    return {}


NOW = datetime.datetime(2026, 9, 18, 12, 0, tzinfo=UTC)


def run(tree, now=NOW):
    """Drive ONLY the credit check and return (findings, credits block).

    ⚠️ THE `try` MIRRORS PRODUCTION. `watchdog.run()` wraps every check so
    that a crashing check becomes a FINDING rather than a silent pass —
    and a harness without that wrapper turns any raising mutation into a
    dead test file instead of a named failure. ⛔ Driving the check
    differently from the way it runs is its own kind of wrong answer.
    """
    rep = W.Report()
    try:
        W.check_credit_balance(rep, now)
    except Exception as e:
        rep.bad("watchdog:check_credit_balance",
                "a watchdog check could not run",
                "%s: %s" % (type(e).__name__, e))
    return rep.items, getattr(rep, "note_credits", None)


def hours_ago(h):
    return NOW - datetime.timedelta(hours=h)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 AT OR UNDER THE FLOOR IT ESCALATES")
# ══════════════════════════════════════════════════════════════════════
with Tree(reserve=750) as t:
    t.pull(hours_ago(1), 700)
    items, cr = run(t)
    ck("the state is CRITICAL", (cr or {}).get("state") == "CRITICAL",
       "credits=%s" % (cr,))
    ck("🔴 ...and it ESCALATES, not merely warns",
       any(i["severity"] == "BROKEN" and i["key"].startswith("credits")
           for i in items),
       "⛔ pulls ARE standing down at this point. items=%s" % (items,))
    _f = one(items, prefix="credits")
    ck("...and it says missing prices now have an explanation",
       "explanation" in _f.get("what", ""),
       "⛔ the whole point: the symptom arrives WITH its cause. what=%r"
       % (_f.get("what"),))
    ck("...naming the balance, the floor and the date it was read",
       all(x in _f.get("why", "") for x in ("700", "750", "2026-09-18")),
       "why=%r" % (_f.get("why"),))
    ck("⚠️ ...and it claims about OUR RECORDS, not about the account",
       "we hold no reading newer than" in _f.get("why", "").lower(),
       "⛔ \"the account has N credits\" is a sentence a stored file "
       "cannot support. why=%r" % (_f.get("why"),))
    ck("...and it says what stands down first",
       "props" in _f.get("why", "").lower(),
       "a props pull is priced per game, so it cannot afford to run "
       "first. why=%r" % (_f.get("why"),))

# ⛔ EXACTLY AT the floor is still standing down -- `collect.py` refuses
#    when `left - need < RESERVE`, so being AT it leaves nothing to spend.
with Tree(reserve=750) as t:
    t.pull(hours_ago(1), 750)
    items, cr = run(t)
    ck("exactly AT the floor is CRITICAL too, not merely LOW",
       (cr or {}).get("state") == "CRITICAL",
       "⛔ at the floor there is nothing left to spend. credits=%s" % (cr,))


# ══════════════════════════════════════════════════════════════════════
section("2. WITHIN 3x THE FLOOR IT WARNS, IT DOES NOT ESCALATE")
# ══════════════════════════════════════════════════════════════════════
with Tree(reserve=750) as t:
    t.pull(hours_ago(1), 2000)
    items, cr = run(t)
    ck("the state is LOW", (cr or {}).get("state") == "LOW",
       "credits=%s" % (cr,))
    ck("🔴 it WARNS and does NOT escalate",
       items and all(i["severity"] == "DEGRADED" for i in items),
       "⛔ nothing is standing down yet; escalating here is how the "
       "channel gets muted (rule 238). items=%s" % (items,))
    # ⛔ THE THRESHOLD IS DERIVED FROM THE TREE'S OWN RESERVE, never 2250.
    ck("...and the warn line is three times the floor it read",
       (cr or {}).get("warn_at") == t.reserve * 3,
       "warn_at=%s reserve=%s" % ((cr or {}).get("warn_at"), t.reserve))

with Tree(reserve=750) as t:
    t.pull(hours_ago(1), 12605)
    items, cr = run(t)
    ck("a comfortable balance is HEALTHY and SILENT",
       (cr or {}).get("state") == "HEALTHY" and not items,
       "credits=%s items=%s" % (cr, items))
    ck("...and the number is reported anyway",
       (cr or {}).get("balance") == 12605,
       "⛔ a balance that only appears once it is a problem cannot be "
       "watched CLOSING. credits=%s" % (cr,))


# ══════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 STALE — THE CASE THAT CANNOT BE SKIPPED")
# ══════════════════════════════════════════════════════════════════════
# ⛔ A PAID PULL RAN AFTER THE LAST BALANCE WE HOLD. Money was spent and
#    the number we have does not reflect it, so reporting it as current
#    argues against the correct diagnosis.
with Tree(reserve=750) as t:
    t.pull(hours_ago(72), 12605)                    # the last real reading
    t.pull(hours_ago(1), None, kind="props-batter", field=False)   # spent, no number
    items, cr = run(t)
    ck("🔴 a reading 72 hours behind the newest paid pull is STALE",
       (cr or {}).get("state") == "STALE",
       "⛔ NOT healthy. A three-day-old balance reported as current is "
       "worse than no watcher. credits=%s" % (cr,))
    ck("⛔ ...and it is NOT reported as HEALTHY",
       (cr or {}).get("state") != "HEALTHY", "credits=%s" % (cr,))
    ck("...it warns", any(i["key"] == "credits:stale" for i in items),
       "items=%s" % (items,))
    _s = one(items, key="credits:stale")
    ck("...and it says the balance is NOT CURRENT rather than quoting it "
       "as fact",
       "not current" in _s.get("what", "")
       and "unknown" in _s.get("what", ""),
       "what=%r" % (_s.get("what"),))
    ck("⚠️ ...and states it as a claim about our records",
       "we hold no reading newer than" in _s.get("why", "").lower(),
       "why=%r" % (_s.get("why"),))
    # ⛔ THE GAP IS MEASURED, and derived from the tree rather than typed.
    ck("...and the gap it reports is the gap the tree built",
       abs((cr or {}).get("behind_newest_pull_hours", 0) - 71.0) < 2.0,
       "⛔ 72h back, 1h back -> ~71h behind. reported=%s"
       % ((cr or {}).get("behind_newest_pull_hours"),))
    ck("...and it still names the last number it does hold",
       (cr or {}).get("balance") == 12605
       and "12605" in _s.get("why", ""),
       "the floor argument needs the figure. credits=%s" % (cr,))

# 🔴 STALE **AND** UNDER THE FLOOR STILL ESCALATES. Spending only goes
#    one way inside a billing month, so a stale low reading is a FLOOR on
#    the problem, not a reason to downgrade it.
with Tree(reserve=750) as t:
    t.pull(hours_ago(72), 600)
    t.pull(hours_ago(1), None, kind="props-player", field=False)
    items, cr = run(t)
    ck("🔴 a STALE reading that is already under the floor escalates",
       (cr or {}).get("state") == "CRITICAL"
       and any(i["severity"] == "BROKEN" for i in items),
       "⛔ a stale low reading is a floor on the problem. credits=%s "
       "items=%s" % (cr, items))

# ✅ AND THE SAME-PULL CASE IS NOT STALE — or the check would cry wolf on
#    every healthy run, which is the other failure.
with Tree(reserve=750) as t:
    t.pull(hours_ago(1), 12000)
    t.pull(hours_ago(1) + datetime.timedelta(minutes=1), 11990,
           kind="props-batter")
    items, cr = run(t)
    ck("⛔ the newest pull CARRYING the number is not called stale",
       (cr or {}).get("state") == "HEALTHY" and not items,
       "⛔ a guard that fires on correct code is the other failure. "
       "credits=%s items=%s" % (cr, items))
    ck("...and the newest of the two readings is the one reported",
       (cr or {}).get("balance") == 11990, "credits=%s" % (cr,))

# 🔴 `[2026-09-30]` #203: A PULL THAT BOUGHT NOTHING IS NOT SPENDING. An
#    alt-lines run that held every game wrote credits_used 0 and no balance;
#    the watchdog called the last real reading stale against it.
with Tree(reserve=750) as t:
    t.pull(hours_ago(2), 3545)
    t.pull(hours_ago(1), None, kind="alt-lines", field=False, used=0)
    items, cr = run(t)
    ck("⛔ a newer pull that spent 0 credits does not make the balance STALE",
       (cr or {}).get("state") == "HEALTHY" and not items,
       "credits=%s items=%s" % (cr, items))
with Tree(reserve=750) as t:
    t.pull(hours_ago(2), 3545)
    t.pull(hours_ago(1), None, kind="alt-lines", field=False, used=8)
    items, cr = run(t)
    ck("🔴 ...but a newer pull that DID spend still does",
       (cr or {}).get("state") == "STALE", "credits=%s" % (cr,))


# ══════════════════════════════════════════════════════════════════════
section("4. ⛔ RESERVE IS READ FROM collect.py, NEVER COPIED")
# ══════════════════════════════════════════════════════════════════════
# 🔴 DRIVEN BY MOVING THE FLOOR. A literal 750 here would silently stop
#    describing the thing it is named after.
with Tree(reserve=5000) as t:
    t.pull(hours_ago(1), 4000)
    items, cr = run(t)
    ck("🔴 the floor it reports is the floor collect.py declares",
       (cr or {}).get("reserve") == 5000,
       "⛔ a hard-coded 750 would report 750 here. credits=%s" % (cr,))
    ck("...and 4,000 against a floor of 5,000 is CRITICAL",
       (cr or {}).get("state") == "CRITICAL",
       "⛔ with a literal 750 this would have read HEALTHY — the exact "
       "failure. credits=%s" % (cr,))
ck("⚠️ and the live repo's floor is read, not guessed",
   W._reserve() == int(re.search(
       r"^RESERVE\s*=\s*(\d+)",
       io.open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read(),
       re.M).group(1)),
   "_reserve()=%s" % (W._reserve(),))
# 🔴🔴 AND THE FLOOR IS WRITTEN DOWN TWICE, WHICH NOTHING CHECKED.
# `[measured 2026-09-18]` `collect.py:91` has `RESERVE = 750` — the one
# the collector actually enforces — and `budget.py:23` has a SECOND copy
# in `PLAN, RESERVE, GAMES = 20000, 750, 15`. They agree today, and
# **nothing asserted that they do**.
# ⚠️ This check adds no behaviour and changes neither number. It exists
#    because this watcher's whole premise is that the floor is DERIVED,
#    and a floor duplicated is a floor that drifts in the file you did
#    not edit (rules 117, 166).
_c_res = int(re.search(
    r"^RESERVE\s*=\s*(\d+)",
    io.open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read(),
    re.M).group(1))
_b = re.search(
    r"^PLAN, RESERVE, GAMES = \d+, (\d+),",
    io.open(os.path.join(ROOT, "budget.py"), encoding="utf-8").read(), re.M)
ck("⚠️ budget.py's second copy of the floor is found",
   bool(_b), "if this stops matching, the check below is guarding nothing")
ck("🔴 the two copies of the spend floor AGREE",
   bool(_b) and int(_b.group(1)) == _c_res,
   "⛔ collect.py enforces %s and budget.py prices against %s. The "
   "collector's value is the real one; a budget priced against a "
   "different floor is wrong about when pulls stop."
   % (_c_res, _b.group(1) if _b else "?"))

ck("⛔ no literal reserve value is written into watchdog.py",
   not re.search(r"(reserve|RESERVE)\s*=\s*\d+", WSRC),
   "found a hard-coded floor")

# ⛔ AN UNREADABLE FLOOR IS A FINDING, NOT A DEFAULT.
with Tree(reserve=750) as t:
    os.remove(os.path.join(t.d, "collect.py"))
    t.pull(hours_ago(1), 100)
    items, cr = run(t)
    ck("🔴 with no floor to read, it says so instead of inventing one",
       any(i["key"] == "credits:reserve" for i in items) and cr is None,
       "⛔ a watcher that invents the floor it watches is worse than one "
       "that says it cannot see it. items=%s" % (items,))


# ══════════════════════════════════════════════════════════════════════
section("5. ⛔ IT SPENDS NOTHING, AND READS NO PLAN SIZE")
# ══════════════════════════════════════════════════════════════════════
# ⛔ THE **CODE**, NOT THE COMMENTS. My first two checks here searched the
#    raw source and went RED on my own prose: the docstring says "NOT
#    budget.py's projection" and a comment says "never by mtime", so
#    scanning text found the very words the check forbids. That is the
#    fourth time in this session a guard has read a comment as code.
# ✅ `ast.unparse` of the parsed function drops comments by construction —
#    they are not in the tree — and the docstring is removed explicitly.
#    Strictly more correct than stripping text with a regex.
import ast                                                   # noqa: E402

_TREE = ast.parse(WSRC)


def _code(name):
    for _n in ast.walk(_TREE):
        if isinstance(_n, ast.FunctionDef) and _n.name == name:
            body = list(_n.body)
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                body = body[1:]          # ⛔ drop the docstring
            return "\n".join(ast.unparse(x) for x in body)
    raise AssertionError("no such function: %s" % name)


_all = "\n".join(_code(n) for n in
                 ("check_credit_balance", "_reserve", "_paid_readings"))
note("scanning %d chars of CODE (comments and docstrings removed)"
     % len(_all))
for _forbidden in ("odds_get", "urlopen", "requests.", "urllib",
                   "api.the-odds-api", "collegefootballdata"):
    ck("⛔ the check never reaches the network: %r absent" % _forbidden,
       _forbidden not in _all,
       "every figure is already on disk")
# 🔴 THE QUESTION IS WHETHER IT *READS* A PLAN SIZE, not whether the word
#    appears. The `basis` string deliberately SAYS "NOT a plan size", and
#    a check that forbade the word would forbid the disclaimer.
ck("⛔ it never opens or imports budget.py",
   not re.search(r"budget\.py", _all.replace("budget.py's", ""))
   and "import budget" not in _all,
   "⚠️ budget.py hard-codes PLAN = 20000 and cfbd_budget.py 1000, "
   "neither read from an API. A plan size is a claim; this reports a "
   "measurement.")
ck("⛔ ...and no PLAN symbol is read",
   not re.search(r"\bPLAN\b", _all), "code=%r" % (_all[:160],))
ck("✅ ...and it does read the API's own field",
   "credits_remaining" in _all,
   "x-requests-remaining, as the collector stored it")
ck("⚠️ the snapshots are ordered by the PATH's date, never by mtime",
   not re.search(r"\bgetmtime\b|\bst_mtime\b", _all),
   "⛔ a fresh checkout rewrites every mtime, so on the runner mtime is "
   "when CI cloned the repo")


# ══════════════════════════════════════════════════════════════════════
section("6. THE OPERATOR'S SURFACE — health.json, NOT THE PAGE")
# ══════════════════════════════════════════════════════════════════════
ck("the check is registered in CHECKS",
   W.check_credit_balance in W.CHECKS,
   "⛔ an unregistered check never runs. CHECKS=%s"
   % ([f.__name__ for f in W.CHECKS],))
ck("⚠️ ...and it is the tenth, not a second reporting channel",
   len(W.CHECKS) == len({f.__name__ for f in W.CHECKS}),
   "one report, one issue")

# ═══════════════════════════════════════════════════════════════════════
# 🔴🔴 6a. SILENT ON A HEALTHY TREE — BUILT, NOT OBSERVED.
# ═══════════════════════════════════════════════════════════════════════
# ⛔ THIS WAS "it is SILENT on the live repo today", driven by
#    `W.run(NOW)` on the LIVE tree with NOW frozen at 2026-09-18. Two
#    wrong answers in one line `[measured 2026-09-28]`:
#    1. A FROZEN CLOCK AGAINST A LIVE TREE. `check_credit_reconciliation`
#       judges `max(now - 24h, RECON_SINCE)` onward, so a `now` in the past
#       widened its window to everything since 2026-09-22: 114 steps and
#       190 unrecorded credits, where the real clock sees 15 steps and 4.
#       `reading_age_hours` read -251.6. Collect was red from 09-26 16:16Z.
#    2. A SILENCE ASSERTED ON PRODUCTION DATA. Whether a neighbouring
#       guard fires on the live tree is a fact about production, and the
#       watchdog reports it through health.json. On 09-28 the live balance
#       was 3,705 and falling ~400-800 a day against a warn line of 2,250,
#       so `credits:low` on the live tree was days away, on correct code.
# ✅ So the healthy case is BUILT: a tree pinned to its own `now`, inside
#    the reconciliation window, every credit spent on a snapshot, and BOTH
#    credits-family checks run through `run()`. The live tree is still
#    read (6c), at the real clock, and what it says is a note().
# ⚠️ NOW_R IS DERIVED FROM RECON_SINCE, not typed: three days after it, at
#    its own 12:00Z, so the pulls at 09:00-11:00 are always in the window
#    and in one billing month. The fixed NOW above sits BEFORE RECON_SINCE,
#    where the reconciliation judges nothing, which is why it cannot drive
#    this.
NOW_R = (datetime.datetime.strptime(W.RECON_SINCE, FMT).replace(tzinfo=UTC)
         + datetime.timedelta(days=3))
_CREDIT_CHECKS = tuple(f for f in W.CHECKS
                       if f.__name__.startswith("check_credit"))
ck("both credits-family checks are found in CHECKS",
   {f.__name__ for f in _CREDIT_CHECKS}
   >= {"check_credit_balance", "check_credit_reconciliation"},
   "found=%s" % ([f.__name__ for f in _CREDIT_CHECKS],))
_SAVED_CHECKS = W.CHECKS
with Tree(reserve=750) as t:
    for _h, _left, _kind in ((3, 12000, "gamelines"),
                             (2, 11960, "props-batter"),
                             (1, 11920, "gamelines")):
        t.pull(NOW_R - datetime.timedelta(hours=_h), _left, kind=_kind,
               used=40)
    _rrep = W.Report()
    try:
        W.check_credit_reconciliation(_rrep, NOW_R)
    except Exception as e:
        _rrep.note_reconciliation = {"error": "%s: %s" % (type(e).__name__, e)}
    _recon = getattr(_rrep, "note_reconciliation", None) or {}
    try:
        W.CHECKS = _CREDIT_CHECKS
        _hout = W.run(NOW_R)
    finally:
        W.CHECKS = _SAVED_CHECKS
_hcr = _hout.get("credits") or {}
ck("⚠️ rule 67: the reconciliation JUDGED the healthy tree (2 steps, "
   "0 unrecorded)",
   _recon.get("steps") == 2 and _recon.get("unrecorded") == 0,
   "⛔ with no step in its window the silence below proves nothing. "
   "reconciliation=%s" % (_recon,))
ck("...and the balance check read it as HEALTHY",
   _hcr.get("state") == "HEALTHY" and _hcr.get("balance") == 11920,
   "credits=%s" % (_hcr,))
ck("🔴 BOTH credits-family checks are SILENT on a healthy tree",
   _hout.get("healthy") is True and not _hout.get("findings"),
   "⛔ a guard that fires on correct code is not a safe guard. "
   "findings=%s" % (_hout.get("findings"),))
ck("⚠️ ...and CHECKS was put back",
   W.CHECKS is _SAVED_CHECKS and len(W.CHECKS) > len(_CREDIT_CHECKS),
   "len=%d" % len(W.CHECKS))

# ⛔ THE REPORT'S SHAPE IS ASSERTED ON THE TREE THAT ALWAYS HAS A READING.
#    A tree holding no numeric reading reports NO_READING, which carries
#    none of these keys, so asking only the live tree made the question
#    depend on what production held.
_KEYS = ("state", "balance", "pulled_at", "reserve", "reading_age_hours",
         "newest_paid_pull", "source", "basis")
ck("`run()` puts the reading into the report",
   isinstance(_hout.get("credits"), dict), "credits=%s" % (_hout.get("credits"),))
for _k in _KEYS:
    ck("health.json carries %r" % _k, _k in _hcr, "keys=%s" % (sorted(_hcr),))
ck("⛔ the basis says it is NOT a plan size and NOT a projection",
   "NOT a plan size" in _hcr.get("basis", ""), "basis=%r" % (_hcr.get("basis"),))

# ⛔ NOT ON THE PUBLIC PAGE. Operational, not a fact about a game.
_html = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
for _t in ("credits_remaining", "credit balance", "x-requests-remaining"):
    ck("⛔ %r does not appear on the public page" % _t,
       _t.lower() not in _html.lower(),
       "rule 55 governs what sits beside a price")

# ═══════════════════════════════════════════════════════════════════════
# 🔴🔴 6b. "REPORTED EVEN WHEN IT IS NOT A FINDING" — DRIVEN ON A REPORT
#      THAT GENUINELY HAS NO FINDINGS, NOT ON TODAY'S LIVE TREE.
# ═══════════════════════════════════════════════════════════════════════
# ⛔ THIS FILE'S OWN DECLARED MUTATION WENT **VACUOUS** ON 2026-09-19,
#    AND NOTHING IN IT WAS EDITED. `[measured]` the declaration
#
#        find:     if getattr(rep, "note_credits", None):
#        with:     if getattr(rep, "note_credits", None) and rep.items:
#
#    dropped the reading from `run()`'s report **only when the report
#    carries no findings** — so it turned this file red only because
#    `_out = W.run(NOW)` above was measuring a LIVE REPO that happened to
#    be finding-free. The watchdog's freshness check was reading a key
#    nothing writes, so it reported nothing; the moment that was fixed
#    the live tree carried a real DEGRADED row, `rep.items` was truthy,
#    and the mutation stopped changing anything.
#
# 🔴 THE GUARD'S BITE DEPENDED ON THE STATE OF PRODUCTION DATA. It
#    would have gone vacuous the first time anything on the real tree
#    went stale — no code change required, and nothing would have said
#    so except `vacuity.py`, which is where it did say so.
#
# ✅ SO THE CONDITION IS BUILT, NOT WAITED FOR: a synthetic tree with one
#    healthy reading, and `CHECKS` narrowed to the credit check alone so
#    the report has zero findings BY CONSTRUCTION. ⛔ This is strictly
#    harder than what it replaces — the old form could only ask the
#    question on days the repo happened to be clean; this one asks it
#    every day. The live-repo checks above are KEPT, as an observation
#    about today rather than as this guard's driver.
_SAVED_CHECKS = W.CHECKS
with Tree(reserve=750) as t:
    t.pull(hours_ago(1), 12000)
    try:
        W.CHECKS = [W.check_credit_balance]
        _sout = W.run(NOW)
    finally:
        W.CHECKS = _SAVED_CHECKS
ck("⚠️ the synthetic report really does carry NO findings",
   _sout.get("healthy") is True and not _sout.get("findings"),
   "⛔ rule 67 — with a finding present the mutation below changes "
   "nothing and the check proves nothing, which is exactly how this "
   "went vacuous. findings=%s" % (_sout.get("findings"),))
ck("🔴🔴 ...and the READING IS IN THE REPORT ANYWAY",
   isinstance(_sout.get("credits"), dict)
   and _sout["credits"].get("balance") == 12000,
   "⛔ a balance that only appears once it is already a problem cannot "
   "be watched CLOSING. credits=%s" % (_sout.get("credits"),))
ck("⚠️ ...and CHECKS was put back, so nothing below reads a stub",
   W.CHECKS is _SAVED_CHECKS and len(W.CHECKS) > 1,
   "⛔ module state left swapped is a fixture leaking into every later "
   "check. len=%d" % len(W.CHECKS))



# ═══════════════════════════════════════════════════════════════════════
# 6c. THE LIVE REPO — AT THE REAL CLOCK, AND ONLY ITS SHAPE IS ASSERTED.
# ═══════════════════════════════════════════════════════════════════════
# ⛔ `run()` WITH NO CLOCK, the call production makes. A fixture clock
#    against the live tree is the defect 6a records; the bracket below
#    fails if any clock but this machine's reaches the live run. ✅ Both
#    ends come from the clock `run()` reads, so runner skew cannot fail it.
# ⚠️ WHAT THE LIVE TREE SAYS IS A NOTE. The watchdog reports production;
#    this file tests the watchdog. Section 8 plants a finding here and
#    proves the file stays green.
_t0 = datetime.datetime.now(UTC).strftime(FMT)
_live = W.run()
_t1 = datetime.datetime.now(UTC).strftime(FMT)
ck("⛔ the live tree is judged at the REAL clock, never the fixture's",
   _t0 <= str(_live.get("checked_at")) <= _t1,
   "t0=%s checked_at=%s t1=%s" % (_t0, _live.get("checked_at"), _t1))
_lcr = _live.get("credits") or {}
ck("the live report carries the reading block",
   isinstance(_live.get("credits"), dict), "credits=%s" % (_live.get("credits"),))
ck("...in one of the named states",
   _lcr.get("state") in ("HEALTHY", "LOW", "STALE", "CRITICAL", "NO_READING"),
   "state=%r" % (_lcr.get("state"),))
if _lcr.get("state") in ("HEALTHY", "LOW", "STALE", "CRITICAL"):
    # ✅ AN EXTRA, when the live tree holds the case. 6a is the twin that
    #    always asks.
    ck("the live block carries every key 6a asserts",
       all(_k in _lcr for _k in _KEYS),
       "missing=%s" % ([_k for _k in _KEYS if _k not in _lcr],))
else:
    note("the live tree holds no numeric reading (%s); the key checks ran "
         "on 6a's tree only" % (_lcr.get("state"),))
_lk = sorted({str(i.get("key")) for i in _live.get("findings") or []
              if str(i.get("key", "")).startswith("credits")})
note("live credits findings (reported, not asserted): %s"
     % (", ".join(_lk) or "none"))
note("live reading: %s left as of %s, floor %s, state %s, %s h old"
     % (_lcr.get("balance"), _lcr.get("pulled_at"), _lcr.get("reserve"),
        _lcr.get("state"), _lcr.get("reading_age_hours")))


# ══════════════════════════════════════════════════════════════════════
section("7. ⛔ A SNAPSHOT WITH NO NUMBER IS NOT A BALANCE OF NONE")
# ══════════════════════════════════════════════════════════════════════
with Tree(reserve=750) as t:
    t.pull(hours_ago(1), None, field=False)
    items, cr = run(t)
    ck("🔴 with no stored balance anywhere it says so",
       any(i["key"] == "credits:unreadable" for i in items),
       "⛔ never a balance of None reported as a number. items=%s"
       % (items,))
    ck("...and names how many snapshots it looked at",
       any(str(1) in i["why"] for i in items), "items=%s" % (items,))

with Tree(reserve=750) as t:
    items, cr = run(t)
    ck("an EMPTY tree is NO_READING, and it is not a finding",
       (cr or {}).get("state") == "NO_READING" and not items,
       "⛔ a fresh tree with no paid pull is a legitimate state, and "
       "alarming on it is how the channel gets muted. credits=%s items=%s"
       % (cr, items))
    ck("...and it still says WHY there is nothing",
       "no paid snapshot" in (cr or {}).get("why", "").lower(),
       "credits=%s" % (cr,))


# ══════════════════════════════════════════════════════════════════════
section("8. ⛔ A CREDITS FINDING ON THE LIVE TREE DOES NOT TURN THIS FILE RED")
# ══════════════════════════════════════════════════════════════════════
# 🔴 THE MUTATION THAT MUST STAY GREEN. `vacuity.py` only asks "red under
#    the mutation"; this asks the opposite, so the file asks it itself:
#    the whole file again, as a child, with PLANT_FIND -> PLANT_WITH
#    applied to watchdog.py in memory (see the top of this file).
# ⚠️ Two checks, because either alone proves nothing: rc 0 with the plant
#    unseen is a plant that did not fire (rule 67).
if PLANTED:
    note("planted child: section 8 does not recurse")
else:
    _p = subprocess.run(
        [sys.executable, "-B", os.path.abspath(__file__)], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=600,
        env=dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1",
                 **{PLANT_ENV: "1"}))
    _o = (_p.stdout or "") + (_p.stderr or "")
    _seen = re.search(r"live credits findings \(reported, not asserted\): "
                      r"[^\n]*credits:unrecorded", _o)
    ck("⚠️ rule 67: the planted finding was SEEN on the live tree",
       bool(_seen),
       "" if _seen else "rc=%s %s" % (_p.returncode, shown(_o[-800:])))
    ck("🔴 ...and the whole file stays GREEN with it",
       _p.returncode == 0,
       "" if _p.returncode == 0 else "rc=%s %s"
       % (_p.returncode, shown(_o[-800:])))
