#!/usr/bin/env python3
"""tcheck.py — the one check harness every test file uses.

    from tcheck import ck, note, section

That is the whole API. ⛔ **There is no gate to write and none to
forget**: the failure gate is an `atexit` hook this module registers when
it is imported, so it runs after the last line of your file whatever that
line is.

════════════════════════════════════════════════════════════════════════
🔴 THIS EXISTS BECAUSE TWO DEFECTS KEPT SHIPPING, AND BOTH ARE STRUCTURAL
════════════════════════════════════════════════════════════════════════

**1. A SECTION APPENDED AFTER THE FAILURE GATE CANNOT FAIL.** Ledger rule
97. Checks were appended below a file's `if fails: sys.exit(1)`; they
printed 🔴 and the file still exited 0. ⛔ **It happened TWICE IN ONE DAY,
hours apart, by the person who wrote the rule** — which says the problem
is the SHAPE, not the discipline.
✅ **`atexit` makes it impossible.** There is no "after" in a file whose
gate runs at interpreter shutdown; anything appended runs BEFORE it.

**2. FOUR DIFFERENT `ck` SIGNATURES, AND ELEVEN FILES SILENTLY PASSED ON
A SWAP.** `[measured 2026-09-06 across the whole suite]`

    def ck(cond, label, detail="")    11 files   condition FIRST
    def ck(name, cond, extra="")       5 files   name FIRST
    def ck(n, ok, d="")                1 file
    def ck(name, ok, detail="")        1 file

⛔ Calling a condition-first `ck` the other way round passes **a non-empty
string as the condition**, which is TRUTHY. **Measured: 11 of 11 such
files printed a tick, recorded no failure, and never evaluated the real
condition at all.** A check that cannot fail is rule 67 in its purest
form, and eleven files were one habit away from it.
⚠️ It had already cost a live TypeError in `test_cfb.py` — that was the
LOUD version of the same mistake, and the loud version is the lucky one.

✅ **SO THIS `ck` READS THE TYPES, NOT THE POSITIONS.** Exactly one
argument must be a `str` (the name); the other is the condition. Both
orders are accepted and neither can be misread. ⛔ Ambiguity — two
strings, or no string — RAISES, because guessing is how this started.
"""
import atexit
import os
import subprocess
import sys
import threading

FAILURES = []
_CHECKS = [0]
_NOTES = []

# ══════════════════════════════════════════════════════════════════════
# ⚠️ STOP AT THE FIRST FAILURE — ONLY WHEN THE VACUITY SWEEP ASKS.
# `[2026-09-26]` The sweep runs a test under each declared mutation and
# reads ONE thing from that run: is the exit code non-zero. A failed check
# is final (nothing un-records one, and the gate turns any failure into
# exit 1), so the rest of that run can only confirm what the first failure
# already decided. `vacuity.run_test(..., red=True)` sets this for the RED
# run alone; the green-on-revert run is always a full run.
# ⛔ POPPED, NOT READ: a test that drives planted files or harness copies
#    in child processes must never hand them this mode.
# ⚠️ `SystemExit`, not `os._exit`: `finally` blocks still clean up, and
#    the gate still runs (and still exits 1).
FAIL_FAST = os.environ.pop("TCHECK_FAIL_FAST", "") == "1"

# ══════════════════════════════════════════════════════════════════════
# 🔴 AND THE THIRD DEFECT, FOUND ON 2026-09-06 AND LIVE IN PRODUCTION:
#    TWO TEST FILES WERE WRITING THE PRODUCT'S OWN PUBLISHED ARTIFACTS.
# ══════════════════════════════════════════════════════════════════════
# `test_record_fb.py` called `record_fb.main()` in the repo root, and
# `test_p4.py` drove the Power-4 gate into its fail-closed branch, which
# writes a diagnostic file. ⛔ THE TESTS RUN IN THE SAME CI JOB THAT
# LATER RUNS `git add data/ picks/` — so `data/ncaaf/latest/record.json`
# was being rewritten and COMMITTED by every collect run of every league,
# including MLB's.
# 🔴 THE REAL DAMAGE IS NOT THE CONTENT, IT IS THE MONITOR. The freshness
# contract watches that file's age to prove the GRADER ran. A test that
# rewrites it every hour makes that row permanently green — a check that
# can no longer fail, which is rule 67 wearing an artifact for a costume.
# ✅ So the guard lives HERE, where every test file already imports it,
# rather than in a rule nobody can enforce.
# ⚠️ (path, size, mtime), not content hashes: 1,066 files in 19ms.
_WATCH = ("data", "picks")


def copy_module(name, dst, root=None):
    """Copy repo module `name` into `dst` WITH the repo-local modules it
    imports, transitively. -> the basenames copied, sorted.

    🔴🔴 A FIXTURE MISSING A FILE ITS SUBJECT NEEDS IS RULE 67 WEARING A
    GREEN TICK — except here it does not even go green, it goes red for a
    reason that has nothing to do with the thing under test.
    `[measured 2026-09-16]` FOUR isolated-tree harnesses each hand-listed
    the files to copy — three spelled `shutil.copy("card_fb.py", tmp)` and
    one kept a `_HELPERS` tuple. The day `card_fb.py` gained ONE
    repo-local import, all four went red at once and the builder they
    exist to test could not start.
    ⛔ A DEPENDENCY LIST WRITTEN BY HAND IS A LIST NOBODY CAN AUTO-UPDATE
    — the rule `collect.yml` already follows by DISCOVERING test files
    instead of naming them, and `budget.py` by deriving the schedule
    instead of quoting it.
    ⚠️ REPO-LOCAL ONLY. A name is followed only when `<root>/<name>.py`
    exists, so stdlib and third-party imports are left alone.
    """
    import shutil
    root = root or os.path.dirname(os.path.abspath(__file__))
    todo = [name if name.endswith(".py") else name + ".py"]
    seen, out = set(), []
    while todo:
        f = todo.pop()
        if f in seen:
            continue
        seen.add(f)
        src = os.path.join(root, f)
        if not os.path.exists(src):
            continue
        shutil.copy(src, dst)
        out.append(f)
        for m in _imports_of(src):
            cand = m.split(".")[0] + ".py"
            if os.path.exists(os.path.join(root, cand)):
                todo.append(cand)
    return sorted(out)


# ⚠️ PARSED ONCE PER FILE VERSION, NOT ONCE PER CALL. `[measured
#    2026-09-26]` `test_dossier_fb.py` calls `copy_module` 38 times and
#    spent 12s of its 62s re-parsing the same modules (2.5M AST nodes), in
#    a file the vacuity sweep runs 34 times. Keyed on (path, mtime, size),
#    so a file that changes mid-process is parsed again; the answer is the
#    same list the walk always produced.
_IMPORTS = {}


def _imports_of(src):
    """Every module name `src` imports, absolute imports only, in AST order."""
    import ast
    try:
        st = os.stat(src)
    except OSError:
        return []
    key = (os.path.abspath(src), st.st_mtime_ns, st.st_size)
    if key not in _IMPORTS:
        names = []
        try:
            tree = ast.parse(open(src, encoding="utf-8").read())
        except (OSError, SyntaxError):
            tree = None
        for n in ast.walk(tree) if tree is not None else ():
            if isinstance(n, ast.Import):
                names.extend(a.name for a in n.names)
            elif isinstance(n, ast.ImportFrom) and not n.level and n.module:
                names.append(n.module)
        _IMPORTS[key] = names
    return _IMPORTS[key]


def _snapshot():
    seen = {}
    for root in _WATCH:
        for d, _, fs in os.walk(root):
            for f in fs:
                p = os.path.join(d, f)
                try:
                    s = os.stat(p)
                    seen[p] = (s.st_size, s.st_mtime_ns)
                except OSError:
                    pass
    return seen


# ⚠️ TAKEN AT IMPORT, from whatever directory the test was started in. A
# file run from somewhere with no data/ simply watches nothing, which is
# the correct behaviour for a fixture tree, not a reason to fail.
_BEFORE = _snapshot()


def _order(a, b):
    """(name, cond) from either order. ⛔ Raises rather than guessing."""
    a_s, b_s = isinstance(a, str), isinstance(b, str)
    if a_s and not b_s:
        return a, b
    if b_s and not a_s:
        return b, a
    if a_s and b_s:
        raise TypeError(
            "ck() got two strings — one of them has to be the condition. "
            f"Got {a!r} and {b!r}. ⛔ This is not guessed: a condition that "
            "is a string is exactly the bug this harness exists to stop.")
    raise TypeError(
        "ck() got no string — one of the two arguments has to be the "
        f"check's NAME. Got {a!r} and {b!r}.")


def ck(a, b, extra=""):
    """Record one check. Name and condition in either order.

    ⚠️ The condition may be any truthy value — a bool, a count, a list.
    It just may not be a `str`, because a string condition is always
    truthy and is the failure mode this harness was built for.
    """
    name, cond = _order(a, b)
    _CHECKS[0] += 1
    ok = bool(cond)
    _say(("  ✅ " if ok else "  ❌ ") + name + (f"  — {extra}" if extra else ""))
    if not ok:
        FAILURES.append(name)
        if FAIL_FAST:
            print("  ⏹ stopped at the first failure (TCHECK_FAIL_FAST, the "
                  "vacuity sweep's red run)")
            raise SystemExit(1)
    return ok


def note(s):
    """Something worth printing that is NOT a pass/fail claim.

    ⛔ Use this for anything REPORTED rather than asserted — a measurement
    of the world that a test may not turn red on (ledger rule 76).
    """
    _NOTES.append(s)
    _say("  ⚪ " + str(s))


def section(title):
    _say("\n═══ " + str(title) + " ═══")


def shown(s):
    """Captured output made safe to PRINT inside a check's detail.

    ⛔ GitHub turns any printed line starting `::error::` (or `::warning::`,
    any `::command::`) into an annotation on the run. A test that echoes a
    driven workflow's output would put ERROR annotations on a GREEN run —
    4 of them on PR #167 `[2026-09-25]`. Assert on the raw text; print this.
    """
    return str(s).replace("::", ": :")


# ══════════════════════════════════════════════════════════════════════
# 🔴 A TEST'S OUTPUT IS READ BY GITHUB, NOT ONLY BY PEOPLE. `[2026-09-26]`
# ══════════════════════════════════════════════════════════════════════
# The runner parses every line a step prints. A line that starts (after
# leading whitespace) `::error::`, `::warning::`, ... is an annotation on
# the run. ⛔ `shown()` above was OPT-IN, and three files did not opt in:
# every collect run, green ones included (#1852), carried two
# "test_live.py FAILED" errors that were `test_pr_staged.py` echoing the
# planted suite it drives, and after #184 two more (`test_self_repair.py`
# echoing a driven record step, `test_freshness.py` running converge
# in-process). An alarm that is false on every run is an alarm nobody
# reads (rule 238).
# ✅ So every line this process writes to `sys.stdout` or `sys.stderr`
#    passes through `_Watched`: a line GitHub would read as a command is
#    written DEFUSED (its leading `::` becomes `: :`), so it cannot reach
#    the run as an annotation, and it is RECORDED, so the gate fails the
#    file and names it. ⛔ A deliberate annotation goes through
#    `annotate()` and nothing else.
# ⚠️ WHAT THIS CANNOT SEE: a child process writing to the descriptor it
#    inherited. `test_workflow_commands.py` fails any test file that starts
#    one without capturing both of its streams.
LEAKS = []


def command_of(line):
    """The workflow command GitHub's runner would read in `line`, or None.

    Mirrors the runner's own parse: leading whitespace is skipped, the
    line must start `::`, and the command runs to the NEXT `::`. ⚠️ Any
    name counts, not only the registered ones: `::stop-commands::` makes
    an arbitrary `::<token>::` a command, so no name is safe to allow.
    """
    s = str(line).lstrip()
    if not s.startswith("::"):
        return None
    end = s.find("::", 2)
    if end < 0:
        return None
    return s[2:end].split(" ", 1)[0] or None


def _defuse_start(text):
    """`text` with a line-leading `::` (after whitespace) made `: :`."""
    i = len(text) - len(text.lstrip())
    if text[i:i + 2] == "::":
        return text[:i] + ": :" + text[i + 2:]
    return text


def _say(text):
    """Print what the HARNESS prints — a check, a note, a section — defused.

    ⚠️ A check's detail is where captured output is SHOWN, on purpose, and
    what it holds can depend on the machine: `test_accumulators.py` prints
    the tail of a collector run whose `::warning::` lines exist only where
    the news feeds fail. Failing the file for it would be a red run that
    comes and goes with the network. So the harness defuses its own lines,
    and the watcher fails only what bypasses it.
    """
    print("\n".join(_defuse_start(ln) for ln in str(text).split("\n")))


class _Watched:
    """A stream every write passes through, one LINE START at a time.

    ⚠️ Only a line's START can make it a command, so everything is written
    straight through except a fragment that could still become `::` — a
    line that so far holds only whitespace, or whitespace and one `:`.
    That fragment waits for the next write (at most two characters plus
    indentation), and `finish()` releases it at exit.
    """

    def __init__(self, stream):
        self._s = stream
        self._held = ""     # a line start that cannot be judged yet
        self._line = ""     # the current line, as the caller wrote it
        self._mid = False   # this line's start has been judged
        self._lock = threading.RLock()     # tests print from worker threads

    def write(self, text):
        if not isinstance(text, str):
            return self._s.write(text)      # the stream's own TypeError
        with self._lock:
            return self._write(text)

    def _write(self, text):
        out = []
        chunks = text.split("\n")
        for i, c in enumerate(chunks):
            last = i == len(chunks) - 1
            self._line += c
            if self._mid:
                out.append(c)
            else:
                self._held += c
                s = self._held.lstrip()
                if not (last and len(s) < 2 and "::".startswith(s)):
                    out.append(_defuse_start(self._held))
                    self._held, self._mid = "", True
            if not last:
                out.append("\n")
                self._judge()
        self._s.write("".join(out))
        return len(text)

    def writelines(self, lines):
        for ln in lines:
            self.write(ln)

    def _judge(self):
        if command_of(self._line):
            LEAKS.append(self._line)
        self._line, self._held, self._mid = "", "", False

    def raw(self, line):
        """Write one line UNWATCHED, on a line of its own. `annotate()` only."""
        with self._lock:
            if self._line or self._held:
                self._write("\n")
            self._s.write(line + "\n")
            self._s.flush()

    def finish(self):
        """Release a held fragment and judge an unfinished last line."""
        with self._lock:
            if self._held:
                self._s.write(self._held)
            if self._line:
                self._judge()
            self._held = ""

    def __getattr__(self, name):
        return getattr(self._s, name)


def annotate(level, message):
    """Put an annotation on the run ON PURPOSE. -> the line written.

    ⛔ The only sanctioned way: any other line that GitHub would read as a
    command fails the file (`LEAKS`). The message is escaped the way the
    runner reads it (`%`, CR, LF), so it stays on one line.
    """
    if level not in ("error", "warning", "notice"):
        raise ValueError("annotate() level must be error, warning or notice, "
                         "got %r" % (level,))
    msg = (str(message).replace("%", "%25").replace("\r", "%0D")
           .replace("\n", "%0A"))
    line = "::%s::%s" % (level, msg)
    out = sys.stdout
    if isinstance(out, _Watched):
        out.raw(line)
    else:
        print(line, flush=True)
    return line


_WATCHERS = []


def _watch():
    for name in ("stdout", "stderr"):
        cur = getattr(sys, name)
        if cur is not None and not isinstance(cur, _Watched):
            w = _Watched(cur)
            _WATCHERS.append(w)
            setattr(sys, name, w)


def _finish_watch():
    for w in _WATCHERS:
        w.finish()


_watch()   # every test process, from the moment it imports tcheck


def eq(got, want, name):
    """`got == want`, with both values printed on the row.

    ⚠️ SEVEN FILES CARRIED A BYTE-IDENTICAL COPY OF THIS before the
    harness existed, each appending to its own `fails` list. ⛔ Seven
    copies of a helper is seven places for a gate to be forgotten.
    """
    return ck(name, got == want, f"got {got!r}, want {want!r}")


def fail(name, extra=""):
    """Record a failure with no condition to evaluate."""
    return ck(name, False, extra)


# 🔴 THE CRASH FLAG. `sys.last_value` is only set in interactive mode,
#    so the only reliable way for an `atexit` hook to know the process is
#    unwinding from an unhandled exception is to have seen it go past.
# ⛔ THE ORIGINAL HOOK IS CHAINED, NEVER REPLACED — swallowing the
#    traceback would trade one blind spot for a worse one.
_CRASHED = []
_PREV_HOOK = sys.excepthook


def _note_crash(etype, value, tb):
    if etype is not SystemExit:
        _CRASHED.append("%s: %s" % (etype.__name__, value))
    _PREV_HOOK(etype, value, tb)


sys.excepthook = _note_crash


@atexit.register
def _gate():
    """🔴 THE GATE. Registered at import, runs at interpreter exit.

    ⛔ **Nothing can be appended past this**, which is the entire point:
    a check written at the bottom of a test file runs BEFORE this, not
    after it. Ledger rule 97 becomes unwritable rather than merely
    forbidden.

    ⚠️ `os._exit` AFTER AN EXPLICIT FLUSH. `sys.exit` inside an atexit
    hook raises SystemExit, which Python reports and then ignores for the
    process's status — the run would print a failure and exit 0, which is
    the very defect this file is here to prevent. `os._exit` skips the
    remaining hooks and buffers, so the flush is done by hand first.
    """
    try:
        # 🔴 DID THIS FILE PRINT A WORKFLOW COMMAND? Every one was written
        # defused already; this makes it a failure, named, so it is fixed
        # rather than carried (see `_Watched`).
        _finish_watch()
        if LEAKS:
            _CHECKS[0] += 1
            name = ("🔴 this file printed %d line(s) GitHub reads as a "
                    "workflow command — each would be an annotation on the run"
                    % len(LEAKS))
            print("  ❌ " + name)
            for ln in LEAKS[:5]:
                print("     - " + shown(ln.strip())[:200])
            print("     ⛔ Print captured output through tcheck.shown(), and "
                  "annotate on purpose only with tcheck.annotate().")
            FAILURES.append(name)
        # 🔴 DID THIS FILE WRITE THE PRODUCT? Checked BEFORE the summary,
        # so a side effect is a failure like any other and cannot hide
        # behind a green count.
        after = _snapshot()
        touched = sorted(p for p in set(_BEFORE) | set(after)
                         if _BEFORE.get(p) != after.get(p))
        # ══════════════════════════════════════════════════════════════
        # 🔴 AN mtime THAT MOVED IS NOT A PRODUCT THAT CHANGED, AND THIS
        #    REDDENED A RUN FOR ONE. `[2026-09-08, never reproduced]`
        #    `test_conf_filter.py` was reported as having MODIFIED
        #    `data/ncaaf/latest/teams.json`. It cannot have: it imports
        #    nothing but stdlib and `tcheck`, it only READS that file,
        #    and its one write is a JS harness inside a tempdir. Three
        #    full sweeps since have never reproduced it.
        # ⛔ THE SNAPSHOT IS `(size, mtime_ns)` FOR SPEED — 1,066 files in
        #    19ms — so a file whose mtime moves while its BYTES are
        #    identical is indistinguishable from one that was rewritten.
        # ⚠️ AND AN mtime-ONLY TOUCH HARMS NEITHER THING THIS GUARD
        #    PROTECTS: `git add` stages CONTENT, so nothing would be
        #    committed; and `freshness.py` BANS `os.path.getmtime`
        #    outright, reading the `built_at` stamp inside the file — so
        #    no freshness row can be held green by it either.
        # ✅ SO ASK GIT, WHICH IS THE AUTHORITY THAT WOULD COMMIT IT, and
        #    is the exact question rule 123 cares about. The fast stat
        #    walk stays the DETECTOR; git adjudicates only the handful it
        #    flags, so this costs nothing on a clean run.
        # ⛔ NOT WEAKER: every content change is still caught, including
        #    an ADDED file (git reports it as `??`) and a DELETED one.
        #    What stops failing is the case where nothing changed at all.
        #    ⚠️ If git cannot answer — no repo, no binary, an error — the
        #    old behaviour stands and the run fails. An unverifiable
        #    change is still a change.
        # ══════════════════════════════════════════════════════════════
        if touched:
            try:
                _g = subprocess.run(
                    ["git", "status", "--porcelain", "--"] + list(_WATCH),
                    capture_output=True, text=True, timeout=60)
                if _g.returncode == 0:
                    _dirty = {ln[3:].strip().strip('"')
                              for ln in _g.stdout.splitlines() if ln[3:].strip()}
                    _real = [p for p in touched
                             if any(p == d or p.startswith(d.rstrip("/") + "/")
                                    or d.startswith(p) for d in _dirty)]
                    if not _real:
                        print("  ⚪ ⚠️ %d file(s) under data/ or picks/ changed "
                              "mtime but NOT content — git reports nothing to "
                              "commit, so the product is untouched. Reported, "
                              "not failed." % len(touched))
                        for _p in touched[:4]:
                            print(f"     - {_p}  (mtime only)")
                        touched = []
                    else:
                        touched = _real
            except Exception as _e:
                print("  ⚠️ could not ask git whether the content changed "
                      "(%s) — failing on the stat difference, because an "
                      "unverifiable change is still a change" % type(_e).__name__)
        if touched:
            _CHECKS[0] += 1
            name = ("🔴 this test MODIFIED %d file(s) under data/ or picks/ "
                    "— a test must not write the product" % len(touched))
            print("  ❌ " + name)
            for p in touched[:8]:
                kind = ("added" if p not in _BEFORE else
                        "deleted" if p not in after else "rewritten")
                print(f"     - {p}  ({kind})")
            print("     ⛔ Run it in a temp tree instead. These files are "
                  "committed by the same CI job that runs the tests, and an "
                  "artifact a test keeps fresh is a freshness row that can "
                  "never go red.")
            FAILURES.append(name)
        # 🔴🔴 A FILE THAT DIED HALFWAY THROUGH HAS NOT PASSED, AND IT WAS
        #    PRINTING A GREEN BANNER. `[found 2026-09-14 by crashing one
        #    on purpose]` A `NameError` on line 244 of a 430-line test
        #    file produced a traceback followed immediately by
        #    **`✅ all 21 checks passed`** — for a file whose remaining 22
        #    checks never ran.
        # ⚠️ THE EXIT CODE WAS CORRECT (1), so CI caught it. That is
        #    exactly what makes it dangerous: the log a human reads said
        #    GREEN, in this repo's own house style, directly under the
        #    stack trace that says otherwise. ⛔ Rule 144 — a check that
        #    could not run did not pass — applied to a whole FILE rather
        #    than to one check.
        # ✅ `_CRASHED` is set by an excepthook installed at import, so
        #    the banner can tell "finished and passed" from "stopped".
        if _CRASHED:
            print(f"\n❌ this file DIED before finishing — {_CHECKS[0]} "
                  f"check(s) ran and an unknown number never did. "
                  f"⛔ NOT A PASS: {_CRASHED[0]}")
            FAILURES.append("the file raised before completing")
        elif FAILURES:
            print(f"\n❌ {len(FAILURES)} of {_CHECKS[0]} checks FAILED")
            for f in FAILURES:
                print("   - " + f)
        elif _CHECKS[0]:
            print(f"\n✅ all {_CHECKS[0]} checks passed")
        else:
            # ⛔ A FILE THAT CHECKED NOTHING IS NOT A PASSING FILE. A test
            # that silently stops asserting is indistinguishable from a
            # deleted one, and CI would go green either way.
            print("\n❌ this file recorded NO checks at all — a test that "
                  "asserts nothing cannot pass")
            FAILURES.append("no checks recorded")
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
    if FAILURES:
        os._exit(1)
