#!/usr/bin/env python3
"""
DOES EACH GUARD ACTUALLY BITE? NOTHING IN THIS REPO HAS EVER ASKED.

🔴🔴 THE DEFECT IS THIS REPO'S MOST REPEATED ONE, AND IT IS IN THE
LEDGER AT LEAST SEVEN TIMES: a guard that passes while proving nothing.
An empty match, a stripped comment, a fixture missing the file under
test, a check asserting its own prose (rules 67, 244, 249).

⛔ AND IT IS NOT HISTORY. `[2026-09-15]` **four new guards shipped in one
day and TWO were vacuous** — the CFBD bar that never read
`cfbd_budget.py`, and the one-issue-in-place check that did not exist at
all. Both were found by **a human mutating them by hand.** That is the
only reason anyone knows. A defect whose only detector is Sam's patience
is a defect with no detector.

✅ SO MAKE IT MECHANICAL. `CLAUDE.md` already says *a guard that cannot
fail is not a guard* and *prove it bites before you call it done*. This
turns that sentence into a nightly job.

══════════════════════════════════════════════════════════════════════
TWO TIERS, AND THEY CATCH DIFFERENT THINGS.

  TIER 1 — GENERIC, needs no authoring. For `test_X.py` / `X.py`, gut
           every function body in `X.py` and assert the test goes RED. A
           test that still passes with its subject gutted does not depend
           on its subject.
  TIER 2 — DECLARED, and this is the one that catches the SUBTLE kind.
           A guard names, in its own file, the exact edit that must turn
           it red. The harness applies it, asserts RED, reverts, asserts
           GREEN. ⛔ Tier 1 would never have caught either of today's
           two: `cfbd_watch.py` was not gutted in the CFBD bar case — the
           *other* file's constant was what mattered.

🔴 TIER 1 MAPS BY NAME ONLY, AND THAT IS A MEASURED DECISION, NOT
   TIMIDITY. `[measured 2026-09-15]` A looser rule — "the one non-test
   module this file imports" — produced **four accusations and all four
   were wrong**: `test_scores_live.py` tests `index.html`, `collect.py`
   and `cfb.py` and merely imports `freshness`; `test_card_revert.py`
   tests a WORKFLOW file; `test_names.py` sweeps every `.py` in the repo;
   `test_tcheck_guard.py`'s subject is `tcheck.py`. ⛔ **A vacuity
   detector that cries wolf is worse than none** — it is rule 238 aimed
   at the one channel that is supposed to be trustworthy.
➡️ So an unclear mapping is REPORTED AS UNMAPPED, never guessed. The
   unmapped list is printed every run, because an unmapped file silently
   skipped is the same vacuity one level up.

══════════════════════════════════════════════════════════════════════
⛔ IT REPORTS. IT NEVER EDITS — BUT IT DOES MUTATE WHILE IT RUNS.

🔴🔴 SO NOTHING ELSE MAY WRITE TO THIS REPO WHILE IT IS RUNNING, AND
THAT IS NOT THEORETICAL. `[2026-09-17]` An editor read `vacuity.py` while
this harness had one of its own declared mutations applied to it, changed
a different line, and wrote the file back — **baking `blind()` down to
`return []` permanently.** The harness reverted its copy in the `finally:`
and the corruption survived, because the revert restores what the harness
read, not what is on disk now.
⚠️ The read-modify-write is the hazard, not the harness: the same thing
happens with any concurrent editor, and the window is the whole sweep.
✅ It was caught immediately, by the ratchet below — a `blind()` that
returns nothing fails its own "the set is DERIVED" check. ⛔ That is the
only reason it is a paragraph here rather than a silent hole.

A guard this finds is NOT deleted and NOT weakened — `CLAUDE.md` forbids
removing a check outright, and a weak guard removed is strictly worse
than a weak guard reported. Sam decides what happens to each one. Every
mutation this applies is reverted in a `finally:`, and the run ends by
asking git whether the tree is clean.
"""
import ast
import glob
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))

EXIT_OK, EXIT_VACUOUS, EXIT_UNREADABLE = 0, 1, 2

# ⚠️ CI gives every test file 600s. Matching it means this cannot invent a
#    failure a real run would not see.
PER_TEST = 600

# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 THE SWEEP RAN ONE MUTATION AT A TIME, SO ITS COST WAS THE SERIAL
#      SUM OF EVERY DECLARATION, AND THAT SUM OUTGREW EVERY CLOCK.
# `[measured 2026-09-23]` 188 declarations across 51 test files, each run
# twice (red, then green): `test_vacuity.py` took 1448s, 2240s and then
# 2401s = TIMEOUT against its 2400s clock in pr-tests, on the same code —
# runner speed alone. `vacuity.yml` was CANCELLED at its 30-minute limit
# on 2026-09-22 and 2026-09-23. `test_dossier_fb.py` (17 declarations x a
# full dossier build) and `test_mlb_tables.py` (12) were ~60% of it.
# ✅ SO THE SAME SWEEP RUNS IN `JOBS` TREES AT ONCE. Every declaration is
# still applied, still run red, still reverted, still run green — in a
# tree of its own, which no other mutation can see. ⛔ Nothing is sampled
# or skipped; only the wall clock changes.
# ⚠️ Capped at 8: each extra tree is a full checkout (~80 MB), and GitHub's
# runner has 4 cores, so more would buy nothing there.
# ══════════════════════════════════════════════════════════════════════
JOBS = max(1, min(8, os.cpu_count() or 1))

# ⚠️ `tcheck.py` is every test's harness, not any test's subject — except
#    for `test_tcheck_guard.py`, which name-maps to it correctly.
DECL = re.compile(r"^\s*#\s*@vacuity\b\s*(.*)$")
FIELD = re.compile(r"^\s*#\s{2,}(file|find|with):\s*(.*)$")


def tests(root=ROOT):
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(root, "test_*.py")))


def subjects(root=ROOT):
    return ({os.path.basename(p) for p in glob.glob(os.path.join(root, "*.py"))}
            - set(tests(root)) - {"vacuity.py"})


def name_map(root=ROOT):
    """`test_X.py` -> `X.py`. ⛔ THE ONLY MAPPING THIS TRUSTS. See header."""
    s = subjects(root)
    return {t: t[5:-3] + ".py" for t in tests(root) if t[5:-3] + ".py" in s}


def unmapped(root=ROOT):
    m = name_map(root)
    return sorted([t for t in tests(root) if t not in m]
                  + [os.path.basename(p)
                     for p in glob.glob(os.path.join(root, "test_*.js"))])


# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 THE THIRD HOLE, AND NOTHING WAS LOOKING AT IT.
#
# Tier 1 reports the files it cannot NAME-MAP. Tier 2 reports the
# mutations it was TOLD about. ⛔ Neither reports the files that are in
# NEITHER — a test with no name-mapped subject AND no declared mutation
# is checked by nothing at all, and `CLAUDE.md` is explicit that every
# guard ships with the mutation that proves it.
#
# `[measured 2026-09-17]` **59 of 81 test files were in that set** and no
# number anywhere in this repo said so. The harness printed "(65
# unmapped)" every night, which reads like the whole gap and is not:
# 18 of those unmapped files DO carry declarations, and 59 carry nothing.
#
# ⚠️ THE CEILING IS A RATCHET, NOT A TARGET. It exists so the set cannot
# grow quietly while somebody works on something else. ⛔ If a new test
# pushes it over, DECLARE A MUTATION for that test — do not raise the
# number. Lowering it is the only edit that is automatically right.
# ⚠️ And it is a number written down, so rule 166 applies: the count is
# DERIVED here and `test_vacuity.py` compares it against this constant,
# exactly as `test_watchdog.py` does for the cron total.
# ══════════════════════════════════════════════════════════════════════
# `[2026-09-17]` 59 when this was first measured. Three came down the same
# day — `test_epa.py`, `test_fbs_gate.py`, `test_harness.py`.
# ⛔ `test_vacuity.py` STAYS IN THE SET ON PURPOSE and cannot leave it: a
# declaration naming it would make this sweep run that file, which runs
# this sweep, without bound. Its own header records the measurement.
BLIND_CEILING = 56


def blind(root=ROOT):
    """Test files with NO tier-1 subject and NO tier-2 declaration.

    ⛔ These are not "probably fine". They are the files about which this
    harness has no opinion whatsoever, which is the state it exists to
    make impossible.
    """
    declared = {d["test"] for d in declarations(root)}
    mapped = set(name_map(root))
    return sorted(set(tests(root)) - declared - mapped)


class _Gut(ast.NodeTransformer):
    def __init__(self):
        self.n = 0

    def _gut(self, node):
        self.generic_visit(node)
        doc = ast.get_docstring(node)
        node.body = ([ast.Expr(ast.Constant(doc))] if doc else []) + [
            ast.Return(ast.Constant(None))]
        self.n += 1
        return node

    visit_FunctionDef = _gut
    visit_AsyncFunctionDef = _gut


def neuter(src):
    """Every function body -> `return None`. -> (source, functions gutted).

    ⚠️ MODULE-LEVEL CODE SURVIVES, deliberately: rewriting it would break
    the import and turn a vacuity check into a crash, which is a different
    finding wearing the same colour. ⛔ It also means this is a WEAK
    mutation against a module that does its work at import time — which is
    reported as `no functions` rather than passed off as a clean result.
    """
    tree = ast.parse(src)
    g = _Gut()
    tree = g.visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree), g.n


def _purge_pycache(root=ROOT):
    """Delete every `__pycache__` under `root`."""
    import shutil
    for d, dirs, _ in os.walk(root):
        for x in list(dirs):
            if x == "__pycache__":
                shutil.rmtree(os.path.join(d, x), ignore_errors=True)
                dirs.remove(x)


def run_test(t, root=ROOT, red=False):
    """-> returncode, or None if it never answered.

    `red=True` is a run under a mutation: it only has to answer "did it
    go red", so tcheck stops at the first failed check (TCHECK_FAIL_FAST,
    see tcheck.py). ⛔ Never for the green-on-revert run.

    ══════════════════════════════════════════════════════════════════
    🔴🔴 `-B` AND A PURGED `__pycache__`, AND THIS IS THE WHOLE HARNESS.
    `[found 2026-09-15 by the planted-guard self-test, before this file
     was ever committed]`

    ⛔ WITHOUT THEM THIS FILE WAS VACUOUS IN EXACTLY THE WAY IT EXISTS TO
    DETECT. Python invalidates a `.pyc` on source **mtime (whole
    seconds) and size**. A tier-2 mutation is typically the SAME LENGTH
    as what it replaces — `return 42` -> `return 43`, `>= 80` -> `>= 95`
    — and the harness rewrites, runs and reverts inside one second. So
    the stale bytecode was reused and **the mutated run returned 0 with
    the mutation never taking effect**:

        clean 0   mutated 0   restored 0      <- no -B, verdict is noise
        clean 0   mutated 1   restored 0      <- with -B, correct

    🔴 A HARNESS THAT REPORTS A VERDICT ABOUT AN EDIT THAT NEVER HAPPENED
    IS RULE 274 — the fire alarm that cannot report a fire — and it would
    have been the most expensive version of it, because everything
    downstream would then have been trusted.
    ⚠️ `-B` alone is not enough: it stops WRITING bytecode, not READING a
    `.pyc` that was already there. Both, every run.
    ══════════════════════════════════════════════════════════════════
    """
    _purge_pycache(root)
    try:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        env.pop("TCHECK_FAIL_FAST", None)
        if red:
            env["TCHECK_FAIL_FAST"] = "1"
        p = subprocess.run([sys.executable, "-B", t], cwd=root,
                           capture_output=True, text=True, timeout=PER_TEST,
                           env=env)
        return p.returncode
    except subprocess.TimeoutExpired:
        return None


def _swap(path, new):
    """Write `new`, hand back the original bytes. Caller MUST restore."""
    orig = open(path, "rb").read()
    open(path, "w", encoding="utf-8").write(new)
    return orig


def _tier1_one(pair, root):
    """Gut one name-mapped subject in `root` and run its test once."""
    t, s = pair
    sp = os.path.join(root, s)
    try:
        stub, nfun = neuter(open(sp, encoding="utf-8").read())
    except (OSError, SyntaxError, ValueError) as e:
        return {"tier": 1, "test": t, "subject": s, "state": "UNREADABLE",
                "why": "cannot gut %s: %s" % (s, e)}
    if nfun == 0:
        # ⛔ NOT REPORTED AS CLEAN. A module with no functions is one
        #    this mutation cannot speak about at all.
        return {"tier": 1, "test": t, "subject": s, "state": "NO_FUNCS",
                "why": "%s defines no functions — gutting it is not a "
                       "mutation, so this pair is UNTESTED" % s}
    t0 = time.time()
    orig = _swap(sp, stub)
    try:
        rc = run_test(t, root, red=True)
    finally:
        open(sp, "wb").write(orig)
    secs = round(time.time() - t0, 1)
    if rc is None:
        return {"tier": 1, "test": t, "subject": s, "state": "TIMEOUT",
                "secs": secs,
                "why": "%s never answered in %ds with %s gutted"
                       % (t, PER_TEST, s)}
    if rc == 0:
        return {"tier": 1, "test": t, "subject": s, "state": "VACUOUS",
                "secs": secs,
                "why": "%s passes with every function in %s gutted — "
                       "it does not depend on its subject" % (t, s)}
    return {"tier": 1, "test": t, "subject": s, "state": "BITES",
            "secs": secs, "why": "goes red when %s is gutted" % s}


def tier1(root=ROOT, only=None, jobs=None, leaks=None):
    """Gut each name-mapped subject; the test must go RED."""
    pairs = [(t, s) for t, s in sorted(name_map(root).items())
             if not (only and t not in only)]
    return _pool(root, JOBS if jobs is None else jobs, pairs, _tier1_one,
                 leaks)


def declarations(root=ROOT):
    """Every `@vacuity` block a test declares about itself.

    ⛔ A DECLARATION THAT DOES NOT PARSE IS A FINDING, not a skip. The
    whole failure mode this file exists for is a check quietly not being
    there, and a malformed declaration is exactly that.
    """
    out = []
    for t in tests(root):
        lines = open(os.path.join(root, t), encoding="utf-8").read().splitlines()
        i = 0
        while i < len(lines):
            m = DECL.match(lines[i])
            if not m:
                i += 1
                continue
            d = {"tier": 2, "test": t, "why_declared": m.group(1).strip(),
                 "line": i + 1}
            i += 1
            while i < len(lines):
                f = FIELD.match(lines[i])
                if not f:
                    break
                d[f.group(1)] = f.group(2)
                i += 1
            out.append(d)
    return out


def rotted(root=ROOT):
    """Every declaration whose `find` would not mutate exactly one line.

    -> [(test, file, why)]. A `find` that matches nothing mutates nothing,
    and the test it belongs to then "passes" having been asked nothing.

    🔴 AND IN THE STAGED COPY THAT WILL REPLACE ITS FILE. `[2026-09-26]`
    #184 staged a `self-repair.yml` that moved its triage Python into
    `self_repair.py`, while `test_workflow_python.py` still declared a
    mutation on the live file's `skip = sys.argv[1].strip()`. Every check
    passed until Sam uploaded the file; the next collect run (#1856) went
    red here. A declaration naming a workflow with a pending upload must
    resolve in BOTH copies: the one swept today and the one Sam will make
    live. (`wfparse.staged_changes`: new or different, line endings aside.)
    """
    import wfparse
    pending = set(wfparse.staged_changes(root))
    out = []
    for d in declarations(root):
        miss = [k for k in ("file", "find", "with") if not d.get(k)]
        if miss:
            out.append((d.get("test"), d.get("file"), "missing " + ",".join(miss)))
            continue
        copies = [d["file"]]
        base = os.path.basename(d["file"])
        if d["file"].replace(os.sep, "/").startswith(".github/workflows/") \
                and base in pending:
            copies.append("docs/upload/" + base)
        for f in copies:
            try:
                src = open(os.path.join(root, f), encoding="utf-8").read()
            except OSError as e:
                out.append((d["test"], f, "unreadable: %s" % e))
                continue
            n = src.count(d["find"])
            if n != 1:
                out.append((d["test"], f, "`find` occurs %d time(s)%s: %r" % (
                    n, " in the STAGED copy Sam will upload" if f != d["file"] else "",
                    d["find"][:70])))
    return out


def _tier2_one(d, root):
    """Apply one declared mutation in `root`: RED, revert, GREEN."""
    t = d["test"]
    miss = [k for k in ("file", "find", "with") if not d.get(k)]
    if miss:
        return {**d, "state": "MALFORMED",
                "why": "declaration at %s:%d is missing %s"
                       % (t, d["line"], ", ".join(miss))}
    p = os.path.join(root, d["file"])
    try:
        src = open(p, encoding="utf-8").read()
    except OSError as e:
        return {**d, "state": "MALFORMED",
                "why": "declared file %s: %s" % (d["file"], e)}
    n = src.count(d["find"])
    if n != 1:
        # ⛔ THE STRIPPED-COMMENT FAILURE, ONE LEVEL UP. A `find` that
        #    matches nothing would make the mutation a no-op and the
        #    check would "pass" having changed nothing at all.
        return {**d, "state": "MALFORMED",
                "why": "`find` occurs %d times in %s — a mutation "
                       "that matches 0 or many is not a mutation"
                       % (n, d["file"])}
    t0 = time.time()
    orig = _swap(p, src.replace(d["find"], d["with"]))
    try:
        red = run_test(t, root, red=True)
    finally:
        open(p, "wb").write(orig)
    if red is None:
        return {**d, "state": "TIMEOUT", "secs": round(time.time() - t0, 1),
                "why": "%s never answered under its own mutation" % t}
    if red == 0:
        return {**d, "state": "VACUOUS", "secs": round(time.time() - t0, 1),
                "why": "%s still PASSES under the mutation it declares "
                       "(%s: `%s` -> `%s`)"
                       % (t, d["file"], d["find"], d["with"])}
    # ✅ AND GREEN ON THE REVERT. Red under mutation is only half the
    #    claim: a test that is red either way proves nothing either.
    green = run_test(t, root)
    secs = round(time.time() - t0, 1)
    if green != 0:
        return {**d, "state": "RED_BOTH_WAYS", "secs": secs,
                "why": "%s is RED even unmutated — its mutation result "
                       "says nothing" % t}
    return {**d, "state": "BITES", "secs": secs,
            "why": "red under `%s` -> `%s`, green on revert"
                   % (d["find"], d["with"])}


def tier2(root=ROOT, only=None, jobs=None, leaks=None, part=None):
    """Apply each declared mutation: must go RED, then GREEN on revert.

    `part` = (k, n) sweeps only this runner's share (`part_of`); None, the
    default and what `main()` and `collect.yml` use, sweeps everything.
    """
    ds = [d for d in declarations(root) if not (only and d["test"] not in only)]
    return _pool(root, JOBS if jobs is None else jobs, part_of(ds, part),
                 _tier2_one, leaks)


# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 ONE SWEEP, SPLIT ACROSS RUNNERS — NEVER SAMPLED. `[2026-09-25]`
# ══════════════════════════════════════════════════════════════════════
# `[measured, PR #163's last pr-tests run]` 292 declarations cost 7,829
# test-seconds; four trees on a 4-core runner made that 1,960s wall
# against a 2,400s clock, and the tests job took 39m30s. The pool above
# already fills every core ONE runner has. ➡️ So pr-tests runs the same
# sweep as N jobs; job k applies declaration i when `i % n == k - 1`.
# ⛔ NOTHING IS DROPPED: `test_pr_shards.py` proves the N parts cover every
#    declaration exactly once, and that pr-tests.yml runs every part.
# ⚠️ ROUND-ROBIN IN DECLARATION ORDER, on purpose: one file's declarations
#    are adjacent, so the costly ones (test_dossier_fb.py, 17 of them) are
#    dealt across the parts instead of piling into one.
# ✅ Unset (`VACUITY_PART` empty), everything is swept in one run, as before.
def parse_part(spec):
    """'k/n' -> (k, n); '' or None -> None. ⛔ Anything else RAISES.

    A malformed spec must never read as "no part" (that would sweep all,
    harmless) or as some other part (that would silently sweep the wrong
    share while another part is swept twice and one not at all).
    """
    if spec is None or str(spec).strip() == "":
        return None
    m = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s*", str(spec))
    if not m:
        raise ValueError("VACUITY_PART must be 'k/n', got %r" % (spec,))
    k, n = int(m.group(1)), int(m.group(2))
    if not 1 <= k <= n:
        raise ValueError("VACUITY_PART %r: need 1 <= k <= n" % (spec,))
    return (k, n)


def part_of(items, part):
    """This part's share of `items`, in order. `part` None -> all of them."""
    if part is None:
        return list(items)
    k, n = part
    return [x for i, x in enumerate(items) if i % n == k - 1]


# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 THE POOL. ONE MUTATION PER TREE AT A TIME, NEVER TWO IN ONE TREE.
# ══════════════════════════════════════════════════════════════════════
# ⛔ The header's rule is "nothing else may write to this repo while it is
#    running", because a second writer in the SAME tree bakes a mutation
#    in. That rule is unchanged: each extra worker gets a DETACHED GIT
#    WORKTREE of its own, and a tree is handed to exactly one worker at a
#    time. No two mutations ever share a tree.
# 🔴 AND IT IS REFUSED ON A DIRTY TREE. A worktree is HEAD, not what is on
#    disk; if `root` differs from HEAD the extra trees would sweep code
#    other than the code asked about. So a dirty `root` runs serially in
#    `root`, exactly as before — slower, never a different answer.
# ⚠️ The trees are named `vacuity-sweep-<pid>-w<k>-*` so the orphan reaper
#    in `test_vacuity.py` releases them if a SIGKILL skips the `finally`.
def _extra_trees(root, n):
    """Up to `n` detached worktrees of `root`'s HEAD. -> list of paths.

    ⚠️ Best effort: a tree that cannot be made means fewer workers, never
    a different result.
    """
    out = []
    for k in range(n):
        d = None
        try:
            d = tempfile.mkdtemp(prefix="vacuity-sweep-%d-w%d-"
                                 % (os.getpid(), k))
            subprocess.run(["git", "worktree", "add", "--detach", d, "HEAD"],
                           cwd=root, check=True, capture_output=True,
                           timeout=600)
            out.append(d)
        except (OSError, subprocess.SubprocessError):
            if d:
                shutil.rmtree(d, ignore_errors=True)
            break
    return out


def _drop_tree(root, d):
    subprocess.run(["git", "worktree", "remove", "--force", d], cwd=root,
                   check=False, capture_output=True)
    shutil.rmtree(d, ignore_errors=True)


def _pool(root, jobs, tasks, work, leaks=None):
    """`work(task, tree)` for every task, in task order, over `jobs` trees.

    🔴 A WORKER TREE LEFT MODIFIED IS A LEAK, and it FAILS CLOSED: it is
    appended to `leaks` for the caller to fold into its own leak verdict,
    and with no list to report into it RAISES. A mutation left behind in a
    tree would have been read by every later mutation in that tree.
    """
    extra = []
    if jobs > 1 and len(tasks) > 1 and _porcelain(root) == set():
        extra = _extra_trees(root, min(jobs, len(tasks)) - 1)
    if not extra:
        return [work(t, root) for t in tasks]
    free = queue.Queue()
    for tr in [root] + extra:
        free.put(tr)

    def one(task):
        tr = free.get()
        try:
            return work(task, tr)
        finally:
            free.put(tr)

    dirty = []
    try:
        with ThreadPoolExecutor(len(extra) + 1) as ex:
            return list(ex.map(one, tasks))
    finally:
        for d in extra:
            left = _porcelain(d)
            if left != set():
                dirty.append("%s: %s" % (d, sorted(left or ["git unavailable"])))
            _drop_tree(root, d)
        subprocess.run(["git", "worktree", "prune"], cwd=root, check=False,
                       capture_output=True)
        if dirty:
            if leaks is None:
                raise RuntimeError("a sweep worker tree was left modified: %s"
                                   % dirty)
            leaks.extend(dirty)


def render(t1, t2, unmapped_files):
    bad1 = [r for r in t1 if r["state"] in ("VACUOUS",)]
    bad2 = [r for r in t2 if r["state"] in ("VACUOUS", "RED_BOTH_WAYS",
                                            "MALFORMED")]
    odd = [r for r in t1 + t2 if r["state"] in ("NO_FUNCS", "TIMEOUT",
                                                "UNREADABLE")]
    o = []
    if bad1 or bad2:
        o.append("**These guards pass while proving nothing.**\n")
        for r in bad1 + bad2:
            o.append("- **`%s`** (tier %d) — %s" % (r["test"], r["tier"],
                                                    r["why"]))
        o.append("")
        o.append("⛔ **DO NOT DELETE OR WEAKEN ANY OF THEM.** `CLAUDE.md`: a "
                 "check may only change when it asks the WRONG QUESTION, and "
                 "the replacement must be harder to pass. A weak guard "
                 "removed is a check removed, which is strictly worse than a "
                 "weak guard reported. **Sam decides what happens to each.**")
        o.append("")
    if odd:
        o.append("⚠️ **Could not speak about these** — not a pass and not a "
                 "fail:\n")
        for r in odd:
            o.append("- `%s` — %s" % (r["test"], r["why"]))
        o.append("")
    o.append("_Tier 1 checked %d name-mapped pair(s); tier 2 applied %d "
             "declared mutation(s)._" % (len(t1), len(t2)))
    o.append("")
    o.append("⚠️ **%d test file(s) are UNMAPPED and tier 1 says nothing about "
             "them.** That is deliberate — a looser mapping produced four "
             "accusations and all four were wrong — but it is printed every "
             "run because an unmapped file silently skipped is the same "
             "vacuity one level up. Give one a `@vacuity` block and tier 2 "
             "covers it: %s"
             % (len(unmapped_files),
                ", ".join("`%s`" % u for u in unmapped_files[:8])
                + (" …" if len(unmapped_files) > 8 else "")))
    o.append("")
    o.append("_One issue, updated in place, closed by itself when every guard "
             "bites. Free: it runs the repo's own tests and calls no API._")
    return "\n".join(o)


def _porcelain(root=ROOT):
    try:
        p = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                           capture_output=True, text=True, timeout=120)
        return (set(p.stdout.splitlines()) if p.returncode == 0 else None)
    except (OSError, subprocess.SubprocessError):
        return None


def leaked(before, root=ROOT):
    """Did the harness leave a mutation behind? -> (ok, what).

    ⚠️ COMPARED AGAINST A SNAPSHOT TAKEN BEFORE THE RUN, not against
    "clean". ⛔ Asking whether the tree is clean would fail on a developer
    with unrelated edits and pass on nothing extra — a false alarm on
    correct behaviour, which `CLAUDE.md` calls the other failure. What
    matters is only what THIS RUN added.
    🔴 AND IT FAILS CLOSED: if git cannot answer, the run is UNREADABLE
    rather than clean. The harness rewrites source files; an unverifiable
    restore is not a restore.
    """
    after = _porcelain(root)
    if before is None or after is None:
        return (False, "git could not be asked before or after the run")
    new_dirt = sorted(after - before)
    return (not new_dirt, "\n".join(new_dirt))


def verdict(results, leak_ok):
    """The sweep -> the exit code. ⛔ NOTHING ELSE MAY DECIDE IT.

    🔴🔴 EXTRACTED BECAUSE `main()` IS THE WHOLE INTERFACE AND
    NOTHING COULD REACH IT. `vacuity.yml` branches on this number and on
    nothing else, so a classification inlined in `main()` is a judgement
    no test can drive. `[found by Sam, 2026-09-15]` Dropping two of the
    three bad states from the tuple that used to live there left
    `test_vacuity.py` GREEN while the harness printed *all bite* with a
    planted vacuous guard sitting in the repo. It went totally blind and
    its own self-proof did not notice.
    ⛔ THAT IS RULE 274 ONE LEVEL UP — the same shape as the stale-`.pyc`
    defect in `run_test`, in the classification layer instead of the
    execution one: an alarm that detects the fire and reports OK.
    ✅ SO IT IS A FUNCTION, exactly like `verdict()` in `runs_report.py`
    and for exactly that reason: `test_runs_report.py` drives that one,
    and `test_vacuity.py` drives this one.

    ⚠️ ORDER MATTERS AND IS EXPLICIT. An unverifiable restore outranks
    every finding: the harness rewrites source files, so if the tree
    cannot be shown clean, nothing it found may be reported as a pass.
    """
    if not leak_ok:
        return EXIT_UNREADABLE
    if not results:
        # ⛔ NOT A PASS. A sweep that checked nothing is "I could not
        #    look", and CLAUDE.md's watcher family never closes on that.
        return EXIT_UNREADABLE
    if any(r["state"] in ("VACUOUS", "RED_BOTH_WAYS", "MALFORMED")
           for r in results):
        return EXIT_VACUOUS
    return EXIT_OK


def main():
    before = _porcelain()
    wleaks = []
    t1 = tier1(leaks=wleaks)
    t2 = tier2(leaks=wleaks)
    ok, dirty = leaked(before)
    # ⛔ A WORKER TREE LEFT MODIFIED COUNTS EXACTLY LIKE `root` LEFT
    #    MODIFIED: every result that tree produced after it is suspect.
    dirty = "\n".join(x for x in [dirty] + wleaks if x)
    leak_ok = bool(ok) and not dirty
    # ⛔ EVERY RETURN BELOW IS THIS NUMBER. main() chooses what to SAY;
    #    it no longer chooses what to REPORT.
    rc = verdict(t1 + t2, leak_ok)
    if not leak_ok:
        # 🔴 THE HARNESS MUTATES THE WORKING TREE. If anything is left
        #    behind, every result above is suspect and NOTHING is reported
        #    as clean.
        sys.stderr.write("the harness left changes behind: %s\n" % (dirty or "?"))
        print("⚠️ **COULD NOT LOOK** — the harness left its own mutations in "
              "the working tree, so every result above is suspect:\n\n"
              "```\n%s\n```" % (dirty or "git unavailable"))
    elif not t1 and not t2:
        sys.stderr.write("nothing to check\n")
    elif rc == EXIT_OK:
        _b = blind()
        print("OK  tier1 %d pair(s), tier2 %d mutation(s), all bite  "
              "(%d unmapped, %d BLIND of %d test file(s); ceiling %d)"
              % (len(t1), len(t2), len(unmapped()), len(_b), len(tests()),
                 BLIND_CEILING))
        if len(_b) > BLIND_CEILING:
            # ⛔ REPORTED, NOT ENFORCED HERE. `vacuity.yml` branches on the
            # exit code and this is not a vacuous guard — it is an
            # UNPROVEN one. The ratchet that fails lives in
            # `test_vacuity.py`, where the contributor who added the file
            # is standing.
            print("⚠️ THE BLIND SET GREW: %d over the ceiling of %d. "
                  "Declare a mutation for the new test rather than "
                  "raising the number.\n   %s"
                  % (len(_b) - BLIND_CEILING, BLIND_CEILING,
                     ", ".join(_b[-6:])))
    else:
        print(render(t1, t2, unmapped()))
    return rc


if __name__ == "__main__":
    sys.exit(main())
