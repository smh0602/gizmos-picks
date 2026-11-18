#!/usr/bin/env python3
"""🔴🔴 A PULL REQUEST'S SWEEP FAILS ON A GUARD THAT PROVES NOTHING. `[2026-11-18, #249]`

Four declared mutations stopped biting when the PRs merged 2026-10-16 and 10-17
masked them (a later filter, a later check), and every pr-tests sweep part passed
those PRs: `test_vacuity.py` asked only that the two CFBD mutations bite. The
nightly named the four every night from 11-02, in #249, which a full set of parts
with findings updates rather than turning a run red.

✅ `vacuity.gate` judges every row of a PR's share by `verdict()`'s own states: a
VACUOUS, RED_BOTH_WAYS or MALFORMED row fails it unless `vacuity.KNOWN_VACUOUS` names
that declaration in that state, with its reason and the issue it is reported in; a
row still owing its green fails whatever the list says. `test_vacuity.py` §4b runs it
on the share it swept. ⛔ The list only shrinks: this file holds the set as recorded.

⛔ This file is that gate's guard, driven on a planted repo with known answers (the
REAL harness sweeps it: one guard that bites, one VACUOUS, one MALFORMED, one red
either way). `test_vacuity.py` runs the real sweep and so can carry no declaration
(its own header says why); this file runs none, so it carries the gate's.

# @vacuity ⛔ a row still owing its green fails the gate, listed or not
#   file: vacuity.py
#   find:         owed = bool(r.get("green_owed"))
#   with:         owed = False
#
# @vacuity 🔴🔴 a finding fails the gate (verdict's own states)
#   file: vacuity.py
#   find:         elif verdict([r], True) == EXIT_VACUOUS:
#   with:         elif False:
#
# @vacuity 🔴 the list excuses a declaration only in the state it names
#   file: vacuity.py
#   find:             if entry.get("state") != r.get("state"):
#   with:             if not entry:
#
# @vacuity 🔴 a listed declaration that BITES again fails until it is taken off
#   file: vacuity.py
#   find:         elif k in known and r.get("state") == "BITES":
#   with:         elif False:
#
# @vacuity ✅ the gate reads KNOWN_VACUOUS when no list is passed
#   file: vacuity.py
#   find:     known = KNOWN_VACUOUS if known is None else known
#   with:     known = {} if known is None else known
#
# @vacuity 🔴 an entry names exactly one real declaration
#   file: vacuity.py
#   find:         if have.count(k) != 1:
#   with:         if False:
#
# @vacuity 🔴 an entry's state is a finding
#   file: vacuity.py
#   find:         if verdict([{"state": e.get("state")}], True) != EXIT_VACUOUS:
#   with:         if False:
#
# @vacuity 🔴 an entry gives its reason
#   file: vacuity.py
#   find:         if not str(e.get("why") or "").strip():
#   with:         if False:
#
# @vacuity 🔴 an entry names the issue it is reported in
#   file: vacuity.py
#   find:         if not re.fullmatch("#[0-9]+", str(e.get("issue") or "")):
#   with:         if False:
#
# @vacuity ✅ the list check reads KNOWN_VACUOUS when no list is passed
#   file: vacuity.py
#   find:     entries = KNOWN_VACUOUS if known is None else known
#   with:     entries = {} if known is None else known
#
# @vacuity 🔴🔴 THE LIST ONLY SHRINKS: a sound entry outside the recorded set still fails
#   file: vacuity.py
#   find: KNOWN_VACUOUS = {}
#   with: KNOWN_VACUOUS = {("test_vacuity_gate.py", "test_vacuity.py", "_GATE = V.gate(_real2)", "_GATE = []"): {"state": "VACUOUS", "why": "w", "issue": "#1"}}
#
# @vacuity 🔴🔴 test_vacuity.py runs the gate on the share it swept
#   file: test_vacuity.py
#   find: _GATE = V.gate(_real2)
#   with: _GATE = []
#
# @vacuity 🔴🔴 ...and fails on what it returns
#   file: test_vacuity.py
#   find:    not _GATE,
#   with:    True,
"""
import ast
import os
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import vacuity as V  # noqa: E402

# ══════════════════════════════════════════════════════════════════════
# ⛔ THE SET AS RECORDED. `[2026-11-18]` EMPTY: #249's four were strengthened in the
#    change that added the gate, and the nightlies 11-11 -> 11-18 named nothing else.
#    An entry may only ever be taken OFF `vacuity.KNOWN_VACUOUS`, and then off here.
#    ⛔ If this fails because you added one: make the test bite instead. Listing a
#    finding is reporting it, never fixing it, and it needs its issue (#N) first.
# ══════════════════════════════════════════════════════════════════════
RECORDED = frozenset()

_DECL = "# @vacuity %s\n#   file: %s\n#   find: %s\n#   with: %s\n"
TREES = []


def git(d, *a):
    return subprocess.run(["git", "-c", "user.name=vgate",
                           "-c", "user.email=vgate@example.invalid", *a],
                          cwd=d, capture_output=True, text=True, timeout=120)


def plant():
    """A committed repo with one guard of each kind the gate must tell apart."""
    d = tempfile.mkdtemp(prefix="vgate-")
    TREES.append(d)
    w = lambda n, s: open(os.path.join(d, n), "w", encoding="utf-8").write(s)  # noqa: E731
    w("subject.py", "A = 1\nX = 1\n")
    w("test_ok.py", _DECL % ("bites", "subject.py", "A = 1", "A = 9")
      + "import sys, subject\nsys.exit(0 if subject.A == 1 else 1)\n")
    w("test_hollow.py", _DECL % ("never reads X", "subject.py", "X = 1", "X = 2")
      + "import sys, subject\nsys.exit(0 if subject.A == 1 else 1)\n")
    w("test_bad.py", _DECL % ("points at nothing", "subject.py", "Z = 1", "Z = 2")
      + "import sys\nsys.exit(0)\n")
    w("test_red.py", _DECL % ("red either way", "subject.py", "A = 1", "A = 8")
      + "import sys\nsys.exit(1)\n")
    git(d, "init", "-q")
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "plant")
    return d


def entry(r, state=None, why="planted", issue="#249"):
    return {V.known_key(r): {"state": state or r["state"], "why": why, "issue": issue}}


try:
    # ════════════════════════════════════════════════════════════════════
    section("1. ⚠️ THE REAL HARNESS SWEEPS THE PLANTED REPO: ONE OF EACH")
    # ════════════════════════════════════════════════════════════════════
    _d = plant()
    _leaks = []
    _rows = V.tier2(_d, jobs=2, leaks=_leaks)
    _by = {r["test"]: r for r in _rows}
    eq({t: r["state"] for t, r in _by.items()},
       {"test_ok.py": "BITES", "test_hollow.py": "VACUOUS", "test_bad.py": "MALFORMED",
        "test_red.py": "RED_BOTH_WAYS"},
       "⚠️ one guard that bites, one VACUOUS, one MALFORMED, one red either way (rule 67: "
       "without all four the checks below ask about states nobody produced)")
    ck("⚠️ ...no row owes its green and no worker tree leaked",
       not any(r.get("green_owed") for r in _rows) and not _leaks, "leaks=%r" % _leaks)
    OK, HOLLOW, BAD, RED = (_by.get(t, {"test": t, "state": "?"}) for t in
                            ("test_ok.py", "test_hollow.py", "test_bad.py", "test_red.py"))
    ALL = {}
    for _r in (HOLLOW, BAD, RED):
        ALL.update(entry(_r))

    # ════════════════════════════════════════════════════════════════════
    section("2. 🔴🔴 RED WHEN A FINDING IS NOT ON THE LIST, GREEN WHEN IT IS")
    # ════════════════════════════════════════════════════════════════════
    _g = V.gate(_rows, known={})
    eq(sorted(t for t in _by if any(t in g for g in _g)),
       ["test_bad.py", "test_hollow.py", "test_red.py"],
       "🔴🔴 off the list: the VACUOUS, the MALFORMED and the red-either-way guard each fail "
       "the share, and the one that bites does not")
    eq(len(_g), 3, "   ...one line each")
    eq(V.gate(_rows, known=ALL), [],
       "✅ each named on the list, in its own state, with its reason and issue: the share passes")
    _ws = V.gate(_rows, known={**ALL, **entry(HOLLOW, state="RED_BOTH_WAYS")})
    ck("🔴 the list excuses a declaration only in the state it names (VACUOUS listed as "
       "RED_BOTH_WAYS fails)", len(_ws) == 1 and "test_hollow.py" in _ws[0], str(_ws))
    _st = V.gate(_rows, known={**ALL, **entry(OK, state="VACUOUS")})
    ck("🔴 a listed declaration that BITES again fails until it is taken off the list",
       len(_st) == 1 and "test_ok.py" in _st[0] and "BITES now" in _st[0], str(_st))
    _real = V.KNOWN_VACUOUS
    try:
        V.KNOWN_VACUOUS = ALL
        _dflt_on = V.gate(_rows)
        V.KNOWN_VACUOUS = {}
        _dflt_off = V.gate(_rows)
    finally:
        V.KNOWN_VACUOUS = _real
    ck("✅ with no list passed, the gate reads vacuity.KNOWN_VACUOUS (the one a PR is judged by)",
       _dflt_on == [] and len(_dflt_off) == 3, "on %s; off %s" % (_dflt_on, _dflt_off))

    # ════════════════════════════════════════════════════════════════════
    section("3. ⛔ A ROW STILL OWING ITS GREEN FAILS, LISTED OR NOT")
    # ════════════════════════════════════════════════════════════════════
    # `[2026-11-17, #357]` `_tier2_one` returns RED_BOTH_WAYS + `green_owed` until the
    #    sweep's end runs the green. One still owing it was never resolved.
    _owed = [dict(RED, green_owed=True), dict(OK, green_owed=True)]
    _go = V.gate(_owed, known=ALL)
    ck("⛔ a row owing its green fails though the list names it, and so does one that "
       "claims BITES", len(_go) == 2 and all("owes its green" in g for g in _go), str(_go))

    # ════════════════════════════════════════════════════════════════════
    section("4. 🔴 AN ENTRY IS A REASONED, REPORTED FINDING ON A DECLARATION THAT EXISTS")
    # ════════════════════════════════════════════════════════════════════
    eq(V.known_problems(_d, known=ALL), [], "✅ the three planted entries are sound")
    _nope = {("test_ok.py", "subject.py", "Q = 1", "Q = 2"):
             {"state": "VACUOUS", "why": "w", "issue": "#1"}}
    for _name, _bad, _word in (
            ("names no declaration", _nope, "not exactly one"),
            ("is not a finding (BITES)", entry(HOLLOW, state="BITES"), "not a finding"),
            ("gives no reason", entry(HOLLOW, why="  "), "no reason"),
            ("names no issue", entry(HOLLOW, issue="249"), "no issue")):
        _p = V.known_problems(_d, known=_bad)
        ck("🔴 an entry that %s is named" % _name, len(_p) == 1 and _word in _p[0], str(_p))
    _real = V.KNOWN_VACUOUS
    try:
        V.KNOWN_VACUOUS = _nope
        _dp = V.known_problems(_d)
    finally:
        V.KNOWN_VACUOUS = _real
    ck("✅ with no list passed, the check reads vacuity.KNOWN_VACUOUS", len(_dp) == 1, str(_dp))
finally:
    for _t in TREES:
        git(_t, "worktree", "prune")
        shutil.rmtree(_t, ignore_errors=True)

# ════════════════════════════════════════════════════════════════════════
section("5. 🔴🔴 THE REAL LIST: SOUND, AND ONLY EVER SMALLER")
# ════════════════════════════════════════════════════════════════════════
_kp = V.known_problems(ROOT)
eq(_kp, [], "🔴 every KNOWN_VACUOUS entry names one real declaration, a finding, a reason and an issue")
_grew = sorted(set(V.KNOWN_VACUOUS) - RECORDED)
ck("🔴🔴 KNOWN_VACUOUS HAS NOT GROWN (%d entr%s; recorded %d)"
   % (len(V.KNOWN_VACUOUS), "y" if len(V.KNOWN_VACUOUS) == 1 else "ies", len(RECORDED)),
   not _grew,
   "⛔ make the test bite instead: listing a finding reports it, it never fixes it. New: %s"
   % [k[:2] for k in _grew])
note("KNOWN_VACUOUS holds %d entr%s%s" % (
    len(V.KNOWN_VACUOUS), "y" if len(V.KNOWN_VACUOUS) == 1 else "ies",
    "".join("\n       %s:%s %s (%s)" % (k[0], k[1], e.get("state"), e.get("issue"))
            for k, e in sorted(V.KNOWN_VACUOUS.items()))))

# ════════════════════════════════════════════════════════════════════════
section("6. 🔴🔴 test_vacuity.py RUNS THE GATE ON THE SHARE IT SWEPT, AND FAILS ON IT")
# ════════════════════════════════════════════════════════════════════════
# ⚠️ Read from its source, never run: running it is the real sweep. `_real2` is that
#    sweep's result (test_vacuity.py asserts it is exactly the share), `_GATE` must be
#    `V.gate(_real2)` and some `ck(...)` must take `not _GATE` as its condition.
_TV = ast.parse(open(os.path.join(ROOT, "test_vacuity.py"), encoding="utf-8").read())
_calls = [n for n in ast.walk(_TV) if isinstance(n, ast.Assign)
          and [t.id for t in n.targets if isinstance(t, ast.Name)] == ["_GATE"]]
_runs = [n for n in _calls if isinstance(n.value, ast.Call)
         and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == "gate"
         and isinstance(n.value.func.value, ast.Name) and n.value.func.value.id == "V"
         and [a.id for a in n.value.args if isinstance(a, ast.Name)] == ["_real2"]
         and not n.value.keywords]
_fails = [n for n in ast.walk(_TV) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
          and n.func.id == "ck" and any(isinstance(a, ast.UnaryOp) and isinstance(a.op, ast.Not)
                                        and isinstance(a.operand, ast.Name) and a.operand.id == "_GATE"
                                        for a in n.args)]
ck("🔴🔴 test_vacuity.py assigns `_GATE = V.gate(_real2)` once, with the default list",
   len(_calls) == 1 and len(_runs) == 1, "%d assignment(s), %d of them the gate" % (len(_calls), len(_runs)))
ck("🔴🔴 ...and a check fails on `not _GATE`",
   len(_fails) == 1, "%d check(s)" % len(_fails))
