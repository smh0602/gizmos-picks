#!/usr/bin/env python3
"""🔴 EVERY MODE THE FRESHNESS CONTRACT NAMES IS A MODE THE COLLECTOR RUNS.

`[measured 2026-09-26, collect runs #1766 #1767 #1770 #1781 #1786 #1816
#1835]` every football converge pass that planned `news-archive` printed

    unknown mode: news-archive
    WARNING: news-archive failed (exit 1). It is a SOFT artifact — ...

`freshness.py` had a contract row whose MODE was `news-archive`, and
`collect.py`'s `run_mode` has no arm by that name. Converge runs the mode a
row names, so a stale archive planned a repair that could never run. The
row is SOFT, so the failure turned nothing red and hid for days.

⛔ `test_page_contract.py` already asked this question and passed: it
compared the contract against a HAND-WRITTEN list of "known" modes, and
`news-archive` was on the list. A list typed by the same hand that wrote
the row checks nothing.

✅ THE CLASS, NOT THE INSTANCE. The dispatched modes are READ OFF
`collect.py` with `ast` (the `if/elif mode == "..."` chain in `run_mode`
that ends in "unknown mode"). Against them, for every league:
  1. every mode `freshness.contract(...)` returns for mlb, nfl and ncaaf;
  2. every mode named by a row-shaped tuple anywhere in `freshness.py`'s
     source, so a row that today's tree filters out (a props row before a
     props board exists, a season not started) is covered too;
  3. every mode-keyed table converge and the gate consult — `SOFT`,
     `OFF_PAGE`, `LATE_GRACE_MIN`, `CASCADE`, `SOURCE_BACKED` — and the
     key-free `FREE` tuple inside `run_mode`. A table entry naming no mode
     is dead: it looks like a decision and governs nothing.

⚠️ WHAT THIS DOES NOT CATCH: a mode that IS dispatched but refuses the
league it is asked for (`props-player` exits under `LEAGUE=mlb`). That is a
different question and `ast` cannot answer it honestly.

# @vacuity 🔴 the live defect: an archive row naming a mode nobody runs
#   file: freshness.py
#   find:         ("news", ("dir", f"{data}/{utc_day}/news"), T["news"], False,
#   with:         ("news-archive", ("dir", f"{data}/{utc_day}/news"), T["news"], False,
#
# @vacuity ⛔ the dispatched set is READ from collect.py, never typed
#   file: collect.py
#   find:         elif mode == "news":
#   with:         elif mode == "news-DISABLED":
#
# @vacuity a mode-keyed table naming a mode nobody runs is dead config
#   file: freshness.py
#   find: SOFT = {"news", "weather", "lineups", "cfb-teams", "runs"}
#   with: SOFT = {"news", "weather", "lineups", "cfb-teams", "runs", "news-archive"}
"""
import ast
import datetime
import io
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from tcheck import ck, note, section                     # noqa: E402

import freshness as F                                    # noqa: E402

UTC = datetime.timezone.utc
LEAGUE_DATA = ("data", "data/nfl", "data/ncaaf")          # mlb, nfl, ncaaf


def _read(name):
    return io.open(os.path.join(ROOT, name), encoding="utf-8").read()


# ══════════════════════════════════════════════════════════════════════
# THE PARSERS. ⛔ Each one FAILS on a shape it cannot read, never skips it:
#    a parser that quietly reads less is how a guard goes blind.
# ══════════════════════════════════════════════════════════════════════
def _mode_names(test):
    """The mode names an arm's test selects, or None if unreadable.

    Readable: `mode == "x"` and `mode in ("x", "y")`.
    """
    if not (isinstance(test, ast.Compare) and len(test.ops) == 1
            and isinstance(test.left, ast.Name) and test.left.id == "mode"):
        return None
    op, rhs = test.ops[0], test.comparators[0]
    if isinstance(op, ast.Eq):
        if isinstance(rhs, ast.Constant) and isinstance(rhs.value, str):
            return [rhs.value]
        return None
    if isinstance(op, ast.In) and isinstance(rhs, (ast.Tuple, ast.List, ast.Set)):
        out = [e.value for e in rhs.elts
               if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        return out if len(out) == len(rhs.elts) else None
    return None


def _says_unknown_mode(stmts):
    for s in stmts:
        for n in ast.walk(s):
            if (isinstance(n, ast.Constant) and isinstance(n.value, str)
                    and "unknown mode" in n.value):
                return True
    return False


def dispatched(src):
    """-> (modes, unreadable, free). Read off `run_mode`, never typed.

    `modes`      every name an arm of the dispatch chain selects
    `unreadable` arms whose test this parser cannot read (a finding)
    `free`       the `FREE` tuple inside `run_mode`, or None if absent
    The dispatch chain is the `if/elif` chain whose final `else` says
    "unknown mode" — the branch the live runs printed.
    """
    fns = [n for n in ast.walk(ast.parse(src))
           if isinstance(n, ast.FunctionDef) and n.name == "run_mode"]
    if len(fns) != 1:
        raise ValueError("expected ONE run_mode, found %d" % len(fns))
    fn = fns[0]
    best = None
    for head in ast.walk(fn):
        if not isinstance(head, ast.If):
            continue
        chain, cur = [], head
        while True:
            chain.append(cur)
            if len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
                cur = cur.orelse[0]
                continue
            break
        if _says_unknown_mode(cur.orelse) and (best is None
                                               or len(chain) > len(best)):
            best = chain
    if best is None:
        raise ValueError("no if/elif chain in run_mode ends in 'unknown mode'")
    modes, unreadable = set(), []
    for arm in best:
        names = _mode_names(arm.test)
        if names is None:
            unreadable.append("line %d: %s" % (arm.lineno,
                                                ast.unparse(arm.test)))
        else:
            modes |= set(names)
    free = None
    for n in ast.walk(fn):
        if (isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id == "FREE"
                and isinstance(n.value, (ast.Tuple, ast.List, ast.Set))):
            free = [e.value for e in n.value.elts
                    if isinstance(e, ast.Constant)]
    return modes, unreadable, free


def _row_mode(node):
    """A row's mode node -> its names, or None. Handles `"a" if c else "b"`."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.IfExp):
        a, b = _row_mode(node.body), _row_mode(node.orelse)
        return None if a is None or b is None else a + b
    return None


def source_rows(src):
    """-> (modes, n_rows, unreadable) for every contract-row-shaped tuple.

    A row is `(mode, ("file"|"dir", path), due, paid, why)`.
    """
    modes, n, bad = set(), 0, []
    for t in ast.walk(ast.parse(src)):
        if not (isinstance(t, ast.Tuple) and len(t.elts) == 5
                and isinstance(t.elts[1], ast.Tuple)
                and len(t.elts[1].elts) == 2
                and isinstance(t.elts[1].elts[0], ast.Constant)
                and t.elts[1].elts[0].value in ("file", "dir")):
            continue
        n += 1
        names = _row_mode(t.elts[0])
        if names is None:
            bad.append("line %d: %s" % (t.lineno, ast.unparse(t.elts[0])))
        else:
            modes |= set(names)
    return modes, n, bad


# ══════════════════════════════════════════════════════════════════════
section("1. THE PARSERS READ WHAT THEY CLAIM, AND REFUSE WHAT THEY CANNOT")
# ══════════════════════════════════════════════════════════════════════
_FIX = '''
def run_mode(mode):
    FREE = ("a", "c")
    if LEAGUE == "x" and mode != "zzz":
        pass
    try:
        if mode == "a":
            pass
        elif mode in ("b", "c"):
            pass
        else:
            log(f"unknown mode: {mode}")
    finally:
        pass
'''
_m, _u, _f = dispatched(_FIX)
ck("the chain's arms are read, `==` and `in` alike",
   _m == {"a", "b", "c"} and not _u, "modes=%s unreadable=%s" % (_m, _u))
ck("...and a `mode != ...` guard outside the chain is NOT an arm",
   "zzz" not in _m, "modes=%s" % (_m,))
ck("...and the FREE tuple is read", _f == ["a", "c"], "free=%s" % (_f,))
_m, _u, _f = dispatched(_FIX.replace('mode in ("b", "c")',
                                     'mode.startswith("b")'))
ck("⛔ an arm the parser cannot read is REPORTED, not skipped",
   _u and "b" not in _m, "unreadable=%s" % (_u,))
try:
    dispatched(_FIX.replace("unknown mode", "something else"))
    _raised = False
except ValueError:
    _raised = True
ck("⛔ no 'unknown mode' chain is an error, never an empty set", _raised,
   "an empty set would make every contract mode look undispatched — or, "
   "worse, a parser that found the wrong chain would pass quietly")

_rm, _rn, _rb = source_rows('rows = [("a", ("file", p), T, False, "w"), '
                            '(("b" if lg else "c"), ("dir", p), T, True, "w"), '
                            '(name, ("file", p), T, False, "w"), '
                            '("not-a-row", ("x", p), T, False, "w")]')
ck("the row sweep reads constants and `a if c else b`, and counts rows",
   _rm == {"a", "b", "c"} and _rn == 3, "modes=%s rows=%d" % (_rm, _rn))
ck("⛔ a row whose mode the sweep cannot read is REPORTED",
   len(_rb) == 1 and "name" in _rb[0], "unreadable=%s" % (_rb,))


# ══════════════════════════════════════════════════════════════════════
section("2. THE COLLECTOR'S DISPATCHED MODES, READ FROM ITS OWN SOURCE")
# ══════════════════════════════════════════════════════════════════════
DISPATCHED, _UNREAD, FREE = dispatched(_read("collect.py"))
note("run_mode dispatches %d modes: %s" % (len(DISPATCHED),
                                            " ".join(sorted(DISPATCHED))))
ck("⛔ every arm of run_mode's dispatch chain is readable", not _UNREAD,
   "teach `_mode_names` the new shape — never skip an arm: %s" % (_UNREAD,))
ck("the FREE tuple was found inside run_mode", bool(FREE),
   "⛔ it is the cross-check below that the chain was read whole")
_free_bad = sorted(set(FREE or ()) - DISPATCHED)
ck("🔴 every FREE mode is a dispatched mode", not _free_bad,
   "a FREE entry with no arm is dead config — or the parser read a "
   "partial chain. not dispatched: %s" % (_free_bad,))


# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 EVERY MODE THE CONTRACT NAMES, EVERY LEAGUE, IS DISPATCHED")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ Rows are filtered by what is on disk and by the clock (a props row
#    before a props board, a season not started), so the contract is read
#    at today and at seven fixed instants across a week, and section 4
#    sweeps the source for the rows none of them returned.
_INSTANTS = [None] + [datetime.datetime(2026, 9, 26, 17, 0, tzinfo=UTC)
                      + datetime.timedelta(days=d) for d in range(7)]
RUNTIME = set()
for _d in LEAGUE_DATA:
    _lg = "mlb" if _d == "data" else _d.split("/")[-1]
    _modes, _rows = set(), 0
    for _t in _INSTANTS:
        _c = F.contract(data=_d, picks="picks", now=_t)
        _rows = max(_rows, len(_c))
        _modes |= {r[0] for r in _c}
    RUNTIME |= _modes
    ck("%s: the contract returned rows to check" % _lg, _rows > 0,
       "⛔ an empty contract makes every mode 'dispatched'. rows=%d" % _rows)
    _bad = sorted(_modes - DISPATCHED)
    ck("🔴 %s: every mode freshness.contract() names is one run_mode runs"
       % _lg, not _bad,
       "⛔ converge runs the mode a row names; a name with no arm prints "
       "'unknown mode' on every pass, and on a SOFT row nothing turns "
       "red. Name the WRITER. not dispatched: %s" % (_bad,))


# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 ...AND EVERY ROW IN THE SOURCE, INCLUDING ROWS FILTERED OUT")
# ══════════════════════════════════════════════════════════════════════
SOURCE, _NROWS, _RBAD = source_rows(_read("freshness.py"))
note("freshness.py holds %d row-shaped tuples naming %d modes"
     % (_NROWS, len(SOURCE)))
ck("⛔ every row's mode is readable", not _RBAD,
   "teach `_row_mode` the new shape — never skip a row: %s" % (_RBAD,))
_missed = sorted(RUNTIME - SOURCE)
ck("⛔ the source sweep sees every mode the live contract returned",
   not _missed,
   "the sweep has gone blind to a row shape; it would then pass on rows "
   "it never read. seen live but not in source: %s" % (_missed,))
_bad = sorted(SOURCE - DISPATCHED)
ck("🔴 every contract row in freshness.py names a mode run_mode runs",
   not _bad, "not dispatched: %s" % (_bad,))


# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE MODE-KEYED TABLES NAME ONLY MODES THAT EXIST")
# ══════════════════════════════════════════════════════════════════════
_TABLES = {
    "SOFT": set(F.SOFT),
    "OFF_PAGE": set(F.OFF_PAGE),
    "LATE_GRACE_MIN": set(F.LATE_GRACE_MIN),
    "CASCADE": set(F.CASCADE) | {m for v in F.CASCADE.values() for m in v},
    "SOURCE_BACKED": set(F.SOURCE_BACKED),
}
for _name, _set in sorted(_TABLES.items()):
    _bad = sorted(_set - DISPATCHED)
    ck("🔴 freshness.%s names only dispatched modes" % _name, not _bad,
       "⛔ an entry naming no mode looks like a decision and governs "
       "nothing — SOFT's `news-archive` was one. not dispatched: %s"
       % (_bad,))
