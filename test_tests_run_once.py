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
✅ `[2026-11-21, review]` IT READS THE STEP AS BASH DOES (~~a pattern over the
text~~). The first form matched `python test_x.py` anywhere: a step that only
PRINTS how to rerun a file (`echo "::error::python test_a.py failed"`, a
summary heredoc, a trailing `# python test_a.py` comment) counted as running
it, so a correct job could go red; and a `done` inside a string ended a loop,
so a real second run could be missed. It also missed `python ./test_x.py`,
`python -X utf8 test_x.py`, `python3.11 test_x.py`, a `while read` or `xargs`
fed by a pipe, and a `for` over `$(ls GLOB)`. Section 1 holds each of those;
wfparse's note says what a runner, a command start and a loop are.
✅ `[2026-11-21, review 2]` `node --check test_x.js` (`-c`) only parses the
file; the reader had counted it as a run, so a correct job that syntax-checks
its .js tests in one step and runs them in the next would have gone red. No
workflow had that shape (all 28 files driven); section 1 plants it.
⚠️ WHAT THIS CANNOT SEE (wfparse's own note, in full): a script handed to
another shell or runner as a string or on stdin (`bash -e "$loop"`, pr-tests'
staged / offseason / champion jobs: one test step each; `bash -c`, `bash
<<EOF`), a file name kept in a variable outside a loop or built from pieces,
an array loop, a loop fed by a redirection, `find -exec`, a function that runs
its own argument, pytest, a harness that runs tests itself (vacuity.py), a
test started from Python. The instance does not rest on this list:
test_render_once.py counts the render files' real executions in both render
jobs. ⚠️ Two steps whose `if:` conditions exclude each other would be
reported too; none exists today, and one step is the simpler shape anyway.
✅ Driven on every real workflow file on the day it was written (both
folders, base 85c434f01 and this branch, both forms of the reader giving the
same answer on every step): it fired on browser.yml's render job (deployed
and staged) and on pr-tests.yml's render job, five files each, and on
nothing else.

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
#   find: self.out.update(fnmatch.filter(self.files, w) if any(c in w for c in "*?[") else [w])
#   with: self.out.update([] if any(c in w for c in "*?[") else [w])
#
# @vacuity ⚠️ a `\` continuation is one line
#   file: wfparse.py
#   find: if s.startswith("\\\n", i):
#   with: if False:
#
# @vacuity ⚠️ a nested loop's `done` does not end the outer loop's body
#   file: wfparse.py
#   find: loop = self.loops.pop()
#   with: loop = self.loops.pop(0)
#
# @vacuity 🔴 a comment is not a command, and an apostrophe in one opens no quote
#   file: wfparse.py
#   find: elif c == "#" and word is None:
#   with: elif c == "#" and word is None and False:
#
# @vacuity 🔴 a runner counts only where a command starts (review: `echo python test_a.py`)
#   file: wfparse.py
#   find: target = _target(w)
#   with: target = next((x for x in map(_target, (w[k:] for k in range(len(w)))) if x), None)
#
# @vacuity 🔴 a command inside a quoted string is text (review: `echo "a; python test_a.py"`)
#   file: wfparse.py
#   find: elif c == '"':
#   with: elif c == '"' and False:
#
# @vacuity 🔴 a heredoc's body is text, never commands (review: a summary heredoc)
#   file: wfparse.py
#   find: heredocs.append(delim)
#   with: heredocs.append(delim) if False else None
#
# @vacuity 🔴 a `done` that is an argument does not end the loop (review: a real run missed)
#   file: wfparse.py
#   find: elif cmd or tk[1] not in _KEYWORDS | _LOOP_WORDS:
#   with: elif tk[1] not in _KEYWORDS | _LOOP_WORDS:
#
# @vacuity ⚠️ a path in front of the file is cut off (review: `python ./test_a.py`)
#   file: wfparse.py
#   find: base = target.rsplit("/", 1)[-1]
#   with: base = target
#
# @vacuity ⚠️ python's -X and -W take a value (review: `python -X utf8 test_a.py`)
#   file: wfparse.py
#   find: if c in "XW":
#   with: if c in "":
#
# @vacuity ⚠️ python3.N is a runner (review: `python3.11 test_a.py`)
#   file: wfparse.py
#   find: python(?:\d+(?:\.\d+)?)?
#   with: python(?:\d+)?
#
# @vacuity 🔴 `node --check` (-c) only parses its file (review: a syntax-check step)
#   file: wfparse.py
#   find: "--print", "-c", "--check")
#   with: "--print")
#
# @vacuity ⚠️ -m test_a runs test_a.py
#   file: wfparse.py
#   find: return (a[j:] or (w[i + 1] if i + 1 < len(w) else "")).replace(".", "/") + ".py"
#   with: return None
#
# @vacuity ⚠️ a `while read VAR` fed by a pipe runs what is piped in (review)
#   file: wfparse.py
#   find: if w[:1] == ["read"] and
#   with: if w[:1] == ["read_"] and
#
# @vacuity ⚠️ a `for` over `$(ls GLOB)` runs the files the glob matches (review)
#   file: wfparse.py
#   find: out += self.names(sub)
#   with: out += []
#
# @vacuity ⚠️ an xargs fed by a pipe runs what is piped in (review)
#   file: wfparse.py
#   find: xargs = w[:1] == ["xargs"]
#   with: xargs = w[:1] == ["xargs_"]
#
# @vacuity ⚠️ a function of the step in front of a runner runs it (the suite's run_one)
#   file: wfparse.py
#   find: if w[0] in funcs:
#   with: if False:
#
# @vacuity 🔴 ...only a function whose body runs its own argument (`say() { echo "$@"; }` does not)
#   file: wfparse.py
#   find: if _runs_its_argument(body, out):
#   with: if True:
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
AB = ["test_a.py", "test_b.py"]
for body, want, why in (
        ("python test_a.py\n", ["test_a.py"], "a direct run"),
        ("python -B test_a.py\ntimeout 60 python3 \"test_b.py\" 2>&1\nnode test_c.js\n",
         F, "   ...with flags, a wrapper, quotes, python3 and node"),
        ("REPO_WATCH_LIVE_REQUIRED=1 python test_a.py\n", ["test_a.py"],
         "   ...behind an environment assignment"),
        ("echo \"run test_a.py by hand\"\ngrep -c x test_b.py\ncat test_c.js\n"
         "python -m pip install test_a.py-helper\n", [],
         "🔴 a mention is not a run: echo, grep, cat, a module flag"),
        # `[2026-11-21, review]` mentions that name the runner as well
        ("echo \"::error::reproduce with: python test_a.py\"\necho python test_b.py\n"
         "grep -q \"python test_a.py\" log\n", [],
         "🔴 ...nor one that names the runner too: a runner counts only where a command starts"),
        ("echo \"step 1; python test_a.py next\"\n", [],
         "🔴 ...nor a command written inside a quoted string"),
        ("run_it  # same as; python test_a.py\n# python test_a.py\n"
         "  # for t in test_b.py; do python \"$t\"; done\n", [],
         "🔴 a comment is not a command, after a command or on a line of its own"),
        ("# the step's own loop\npython test_a.py\n", ["test_a.py"],
         "   ...and an apostrophe in a comment opens no quote"),
        ("cat >> \"$GITHUB_STEP_SUMMARY\" <<EOF\nRun it locally:\n  python test_a.py\nEOF\n"
         "python test_b.py\n", ["test_b.py"],
         "🔴 a heredoc's body is text, never commands; the line after it is a command"),
        ("echo \"out: $(python test_a.py)\"\n", ["test_a.py"],
         "   ...while a $(...) inside a quoted string IS a command"),
        ("python ./test_a.py\npython \"$GITHUB_WORKSPACE/test_b.py\"\n", AB,
         "a path in front of the file"),
        ("python -X utf8 test_a.py\npython -W ignore test_b.py\n", AB,
         "   ...python's -X and -W take a value"),
        ("python -X test_a.py other.py\n", [], "   ...so the word after -X is not the file"),
        ("python3.11 test_a.py\n", ["test_a.py"], "   ...python3.N is a runner"),
        ("python -m test_a\n", ["test_a.py"], "   ...-m test_a runs test_a.py"),
        # `[2026-11-21, review]` node's check mode parses a file and runs none of it
        ("node --check test_c.js\nnode -c test_c.js\n"
         "for t in test_*.js; do node --check \"$t\"; done\n", [],
         "🔴 `node --check` (-c) only parses its file: no run"),
        ("node test_c.js -c\n", ["test_c.js"], "   ...while a -c after the file is the file's own"),
        ("python \\\n  test_a.py\n", ["test_a.py"], "   ...across a `\\` continuation"),
        ("for t in test_a.py \\\n         test_b.py; do\n  python \"$t\"\ndone\n",
         AB, "a loop over listed files, across a `\\` continuation"),
        ("run_one() {   # $1 = runner, $2 = file\n  timeout -k 15 60 \"$1\" \"$2\"\n}\n"
         "for t in test_*.py; do\n  [ -e \"$t\" ] || continue\n  run_one python \"$t\"\ndone\n",
         AB, "a glob loop: every test file it matches, through a function of the step (run_one)"),
        ("say() { echo \"::notice::$*\"; }\nsay python test_a.py\n"
         "for t in test_b.py; do say python \"$t\"; done\n", [],
         "🔴 ...but a function that only PRINTS its arguments runs nothing"),
        ("for t in test_a.py\ndo\n  python \"${t}\"\ndone\n", ["test_a.py"],
         "   ...`do` on its own line, ${t} spelled with braces"),
        ("for t in $(ls test_*.py); do python \"$t\"; done\n", AB, "   ...over a $(ls GLOB)"),
        ("ls test_*.py | while read -r t; do python \"$t\"; done\n", AB,
         "a `while read` fed by a pipe runs what is piped in"),
        ("ls test_*.py | xargs -n1 python\nprintf '%s\\n' test_c.js | xargs -I{} node {}\n", F,
         "an xargs fed by a pipe runs what is piped in"),
        ("for t in test_a.py test_b.py; do\n  grep -qxF -- \"== $t\" \"$log\"\ndone\n", [],
         "🔴 a loop that only READS \"$t\" runs nothing (the new skipped-render check)"),
        ("for t in test_a.py; do echo \"would run: python $t\"; done\n", [],
         "   ...nor one that only prints the command"),
        ("for m in $MODES test_a.py; do python collect.py \"$m\"; done\n", [],
         "   ...nor one whose runner's argument is another file"),
        ("for t in test_a.py; do python x.py > \"$t.log\"; done\n", [],
         "   ...nor one that only names an output after \"$t\""),
        ("for t in test_a.py test_b.py; do\n  echo \"not done yet: $t\"\n  echo done\n"
         "  python \"$t\"\ndone\n", AB,
         "🔴 a `done` in a string or as an argument does not end the loop"),
        ("for t in test_a.py; do\n  for i in 1 2; do echo $i; done\n  python \"$t\"\ndone\n",
         ["test_a.py"], "⚠️ a nested loop's `done` does not end the outer body"),
        ("out=$(for t in test_a.py test_b.py; do\n        [ -e \"$t\" ] && python \"$t\" 2>&1\n"
         "      done | grep -c \"NO BROWSER HERE\" || true)\n",
         AB, "🔴🔴 the 11-21 re-run shape is a run")):
    eq(W.step_tests(body, F), want, why)

_hint = ("on: push\njobs:\n  j:\n    runs-on: x\n    steps:\n"
         "      - name: Tests\n        run: |\n"
         "          for t in test_*.py; do python \"$t\"; done\n"
         "      - name: Tell\n        if: failure()\n        run: |\n"
         "          echo \"::error::reproduce with: python test_a.py\"\n"
         "          cat >> \"$GITHUB_STEP_SUMMARY\" <<EOF\n"
         "          python test_b.py\n"
         "          EOF\n")
eq(W.rerun_tests(_hint, F), [],
   "🔴 a suite step, then a step that only PRINTS how to rerun a file, is no finding (review)")
_syntax = ("on: push\njobs:\n  j:\n    runs-on: x\n    steps:\n"
           "      - name: Syntax check the js tests\n        run: |\n"
           "          for t in test_*.js; do node --check \"$t\"; done\n"
           "      - name: Tests\n        run: |\n"
           "          for t in test_*.js; do node \"$t\"; done\n")
eq(W.rerun_tests(_syntax, F), [],
   "🔴 a `node --check` step, then the step that runs the files, is no finding (review)")

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
