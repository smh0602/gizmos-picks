#!/usr/bin/env python3
r"""NO TEST FILE IS RUN BY TWO STEPS OF ONE JOB.

🔴 WHAT HAPPENED `[2026-11-21]`. browser.yml's render job ran its five render
files TWICE on every run: "Render tests", then "A skipped render check is a
failure in THIS workflow" ran all five again only to grep their output for
"NO BROWSER HERE". 406s + 402s of the job's 873s on run 44886195117 (400-405s
of re-run on each of the 20 runs to 11-21), and on a slow `--with-deps`
install the job reached 1273s of its 1500s clock (#252, health.json
`clock:browser` DEGRADED). pr-tests' render job, its line-for-line copy
(test_runner_image.py §5), did the same on every PR.

✅ THE CLASS, NOT THE INSTANCE: every workflow as it will be live
(`wfparse.effective_workflows`, a staged copy winning), every job, every step:
no test file may be run by two steps of one job. A second step that needs what
a test printed reads what the first step kept (browser.yml's RENDER_LOG), and
never runs the file again. `wfparse.step_tests` reads what a step RUNS, never
what it mentions (section 1 holds every case).
⚠️ WHAT THIS CANNOT SEE (wfparse's own note): a step that runs another step's
script (`bash -e "$loop"`, pr-tests' staged / offseason / champion jobs: one
test step each), a harness that runs tests itself (vacuity.py), a test started
from Python. ⚠️ Two steps whose `if:` conditions exclude each other would be
reported too; none exists today, and one step is the simpler shape anyway.
✅ Driven on every real workflow file on the day it was written (both
folders): it fired on browser.yml's render job (deployed and staged) and on
pr-tests.yml's render job, five files each, and on nothing else.

# @vacuity 🔴 the render job re-running a render file is caught (the 11-21 shape)
#   file: docs/upload/browser.yml
#   find: out=$(grep -c "NO BROWSER HERE" "$log" || true)
#   with: out=$(for t in test_box_live.py; do python "$t" 2>&1; done | grep -c "NO BROWSER HERE" || true)
#
# @vacuity 🔴 ...and a direct second run, in pr-tests' copy of the job
#   file: .github/workflows/pr-tests.yml
#   find: python -m pip install --quiet playwright
#   with: python -m pip install --quiet playwright && python test_league_switch.py
#
# @vacuity 🔴 a run by two steps is a finding, not only a run by three
#   file: wfparse.py
#   find:         out += [(jb.name, f, s) for f, s in sorted(by.items()) if len(s) > 1]
#   with:         out += [(jb.name, f, s) for f, s in sorted(by.items()) if len(s) > 2]
#
# @vacuity ⚠️ a loop's glob is matched against the test files that exist
#   file: wfparse.py
#   find:                 out.update(fnmatch.filter(files, w) if any(c in w for c in "*?[") else [w])
#   with:                 out.update([] if any(c in w for c in "*?[") else [w])
#
# @vacuity ⚠️ a `\` continuation is one line (the render loop spans two)
#   file: wfparse.py
#   find:     return live.replace("\\\n", " ")
#   with:     return live
#
# @vacuity ⚠️ a nested loop's `done` does not end the outer loop's body
#   file: wfparse.py
#   find:         depth += 1 if m.group(1) == "do" else -1
#   with:         depth -= 1
#
# @vacuity ⚠️ a comment line is not a command
#   file: wfparse.py
#   find:     live = "\n".join(l for l in (run or "").splitlines()
#   with:     live = "\n".join(l for l in (run or "").replace("# ", "").splitlines()
"""
import glob
import os
import shutil
import tempfile

import wfparse as W
from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
RENDER = ["test_box_live.py", "test_box_score.py", "test_league_switch.py",
          "test_live_scores.py", "test_nfl_opener.py"]


def test_files(root):
    """The test files a loop's glob can match: what the suite loops run."""
    return sorted(os.path.basename(p) for pat in ("test_*.py", "test_*.js")
                  for p in glob.glob(os.path.join(root, pat)))


# ══════════════════════════════════════════════════════════════════════
section("1. WHAT A STEP RUNS, NEVER WHAT IT MENTIONS (planted bodies)")
# ══════════════════════════════════════════════════════════════════════
F = ["test_a.py", "test_b.py", "test_c.js"]
for body, want, why in (
        ("python test_a.py\n", ["test_a.py"], "a direct run"),
        ("python -B test_a.py\ntimeout 60 python3 \"test_b.py\" 2>&1\nnode test_c.js\n",
         F, "   ...with flags, a wrapper, quotes, python3 and node"),
        ("REPO_WATCH_LIVE_REQUIRED=1 python test_a.py\n", ["test_a.py"],
         "   ...behind an environment assignment"),
        ("echo \"run test_a.py by hand\"\ngrep -c x test_b.py\ncat test_c.js\n"
         "python -m pip install test_a.py-helper\n", [],
         "🔴 a mention is not a run: echo, grep, cat, a module flag"),
        ("# python test_a.py\n  # for t in test_b.py; do python \"$t\"; done\n", [],
         "🔴 a comment line is not a command"),
        ("for t in test_a.py \\\n         test_b.py; do\n  python \"$t\"\ndone\n",
         ["test_a.py", "test_b.py"], "a loop over listed files, across a `\\` continuation"),
        ("for t in test_*.py; do\n  [ -e \"$t\" ] || continue\n  run_one python \"$t\"\ndone\n",
         ["test_a.py", "test_b.py"], "a glob loop: every test file it matches, through run_one"),
        ("for t in test_a.py\ndo\n  python \"${t}\"\ndone\n", ["test_a.py"],
         "   ...`do` on its own line, ${t} spelled with braces"),
        ("for t in test_a.py test_b.py; do\n  grep -qxF -- \"== $t\" \"$log\"\ndone\n", [],
         "🔴 a loop that only READS \"$t\" runs nothing (the new skipped-render check)"),
        ("for m in $MODES test_a.py; do python collect.py \"$m\"; done\n", [],
         "   ...nor one whose runner's argument is another file"),
        ("for t in test_a.py; do python x.py > \"$t.log\"; done\n", [],
         "   ...nor one that only names an output after \"$t\""),
        ("for t in test_a.py; do\n  for i in 1 2; do echo $i; done\n  python \"$t\"\ndone\n",
         ["test_a.py"], "⚠️ a nested loop's `done` does not end the outer body"),
        ("out=$(for t in test_a.py test_b.py; do\n        [ -e \"$t\" ] && python \"$t\" 2>&1\n"
         "      done | grep -c \"NO BROWSER HERE\" || true)\n",
         ["test_a.py", "test_b.py"], "🔴🔴 the 11-21 re-run shape is a run")):
    eq(W.step_tests(body, F), want, why)

_wf = ("on: push\njobs:\n"
       "  j:\n    runs-on: x\n    steps:\n"
       "      - name: First\n        run: python test_a.py\n"
       "      - id: second\n        run: |\n"
       "          for t in test_a.py test_b.py; do\n            python \"$t\"\n          done\n"
       "      - name: Reads only\n        run: grep -c x test_b.py\n"
       "  k:\n    runs-on: x\n    steps:\n"
       "      - name: Suite\n        run: |\n          for t in test_*.py; do python \"$t\"; done\n"
       "      - name: Not a test\n        run: python collect.py card\n"
       "  l:\n    runs-on: x\n    steps:\n"
       "      - name: Again, in another job\n        run: python test_a.py\n")
eq(W.rerun_tests(_wf, F), [("j", "test_a.py", ["First", "second"])],
   "🔴🔴 a file two steps of one job run is a finding (a step with no name by its id); "
   "one run per job, a mention, and the same file in another job are not")
_t = tempfile.mkdtemp(prefix="reruns-")
try:
    _p = os.path.join(_t, "w.yml")
    open(_p, "w", encoding="utf-8").write(_wf)
    eq(W.rerun_tests(_p, F), W.rerun_tests(_wf, F), "   ...read from a path the same as from text")
finally:
    shutil.rmtree(_t, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 EVERY WORKFLOW AS IT WILL BE LIVE: NO TEST FILE RUNS TWICE IN A JOB")
# ══════════════════════════════════════════════════════════════════════
FILES = test_files(ROOT)
EFF = W.effective_workflows(ROOT)
RUNS = {(f, j.name, s.name or s.id): W.step_tests(s.run, FILES)
        for f, p in sorted(EFF.items()) for j in W.jobs(p) for s in W.steps(p, j.name)}
# ⚠️ rule 67: a scanner that sees nothing passes everything. The steps known
#    to run tests must be seen running them.
ck(len(FILES) >= 100 and len(EFF) >= 10, "⚠️ the repo's test files and workflows were read",
   "%d test files, %d workflows" % (len(FILES), len(EFF)))
for key, want in ((("pr-tests.yml", "tests", "Tests"), FILES),
                  (("collect.yml", "collect", "Tests"), FILES),
                  (("browser.yml", "render", "Render tests"), RENDER),
                  (("pr-tests.yml", "render", "Render tests"), RENDER)):
    _got = RUNS.get(key) or []
    ck(_got == want, "⚠️ %s %s's %r is seen running %s" % (
        key[0], key[1], key[2], "every test file" if want is FILES else "the five render files"),
       "%d of %d; missing %s, extra %s" % (len(_got), len(want), sorted(set(want) - set(_got))[:5],
                                          sorted(set(_got) - set(want))[:5]))
ck("test_repo_watch.py" in RUNS.get(
       ("budget.yml", "repo", "The repository size check, on a repository that can answer it"), []),
   "⚠️ ...and budget.yml's direct `python test_repo_watch.py` is seen too")
BAD = [(f, job, t, st) for f, p in sorted(EFF.items()) for job, t, st in W.rerun_tests(p, FILES)]
ck(not BAD, "🔴🔴 no test file is run by two steps of one job, in any workflow",
   "\n".join("       %s :: job %s runs %s in %s" % (f, job, t, " AND ".join(st))
             for f, job, t, st in BAD))
note("%d steps scanned in %d workflows (staged copies winning); %d run a test file"
     % (len(RUNS), len(EFF), sum(1 for v in RUNS.values() if v)))
# ⚠️ An extra, never a check: the DEPLOYED copy of a pending upload is what
#    fires until Sam uploads it (runs_report flags one 48h after its PR merged).
for _f in W.pending_uploads(ROOT):
    _live = W.rerun_tests(os.path.join(ROOT, W.DEPLOYED_DIR, _f), FILES)
    if _live:
        note("deployed %s still runs %d file(s) twice in one job until Sam uploads the staged copy"
             % (_f, len(_live)))
