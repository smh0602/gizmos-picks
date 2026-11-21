#!/usr/bin/env python3
r"""THE RENDER JOB RUNS EACH RENDER FILE ONCE, AND ITS SKIP CHECK STILL BITES.

🔴 WHAT HAPPENED `[2026-11-21]`. browser.yml's "A skipped render check is a
failure in THIS workflow" ran all five render files AGAIN, only to grep what
they printed for "NO BROWSER HERE": 400-405s of re-run on each of the 20 runs
to 11-21 (402s of 873s on run 44886195117), and with a slow `--with-deps`
install the job used 1273s of its 1500s clock (#252). ✅ Now "Render tests"
keeps what the files print in a log of its own (mktemp, RENDER_LOG through
GITHUB_ENV) and the skip check reads that log and runs nothing.

✅ DRIVEN, NEVER QUOTED: both steps' REAL bodies, read out of browser.yml as
it will be live (the staged copy wins) and out of pr-tests.yml's render job
(its line-for-line copy, test_runner_image.py §5), run with `bash -e` as the
runner runs them, in a planted tree whose five render files are stubs that
record every run, with a private RUNNER_TEMP / TMPDIR and planted GITHUB_ENV /
GITHUB_OUTPUT (test_step_tmp.py's rule for a driven step). The runner's
GITHUB_ENV hand-off is replayed between the two steps.
⛔ A check that cannot see its input FAILS: no log (Render tests never ran),
an empty log, a missing file, or a render file the log never saw.
The class (no test file run by two steps of one job, every workflow) is
test_tests_run_once.py.

# @vacuity 🔴🔴 the skip check running the render files again is caught
#   file: docs/upload/browser.yml
#   find: out=$(grep -c "NO BROWSER HERE" "$log" || true)
#   with: out=$(for t in test_*.py; do python "$t" 2>&1; done | grep -c "NO BROWSER HERE" || true)
#
# @vacuity 🔴 a NO BROWSER line in the log fails the skip check
#   file: docs/upload/browser.yml
#   find: out=$(grep -c "NO BROWSER HERE" "$log" || true)
#   with: out=0
#
# @vacuity 🔴🔴 a missing or empty log fails, never passes
#   file: docs/upload/browser.yml
#   find: if [ -z "$log" ] || [ ! -s "$log" ]; then
#   with: if [ -z "$log" ] || [ ! -s "$log" ]; then echo no log; exit 0; fi; if false; then
#
# @vacuity 🔴 a render file the log never saw fails (a step stopped part way)
#   file: docs/upload/browser.yml
#   find: if [ -e "$t" ] && ! grep -qxF -- "── $t" "$log"; then
#   with: if false; then
#
# @vacuity 🔴 what a file prints on stderr reaches the log too
#   file: docs/upload/browser.yml
#   find: python "$t" 2>&1 | tee -a "$log" || { rc=1; echo "::error::$t FAILED"; }
#   with: python "$t" | tee -a "$log" || { rc=1; echo "::error::$t FAILED"; }
#
# @vacuity 🔴🔴 a failing render file still fails Render tests through the pipe
#   file: docs/upload/browser.yml
#   find: set -o pipefail
#   with: set +o pipefail
#
# @vacuity 🔴 the log's path reaches the next step
#   file: docs/upload/browser.yml
#   find: echo "RENDER_LOG=$log" >> "$GITHUB_ENV"
#   with: echo "RENDER_LOG=" >> "$GITHUB_ENV"
#
# @vacuity 🔴 the log is a file of its own, never a fixed name
#   file: docs/upload/browser.yml
#   find: log=$(mktemp "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/render.XXXXXX")
#   with: log="${RUNNER_TEMP:-/tmp}/render.log"; : > "$log"
#
# @vacuity 🔴 fewer than five render files still fails Render tests
#   file: docs/upload/browser.yml
#   find: if [ "$ran" -lt 5 ]; then
#   with: if [ "$ran" -lt 4 ]; then
#
# @vacuity 🔴 pr-tests' copy of the job is driven too, not only browser.yml's
#   file: .github/workflows/pr-tests.yml
#   find: set -o pipefail
#   with: set +o pipefail
"""
import json
import os
import shutil
import subprocess
import tempfile

import wfparse as W
from tcheck import ck, eq, note, section, shown

ROOT = os.path.dirname(os.path.abspath(__file__))
RENDER = ["test_box_live.py", "test_box_score.py", "test_live_scores.py",
          "test_nfl_opener.py", "test_league_switch.py"]
RUN_NAME = "Render tests"
SKIP_NAME = "A skipped render check is a failure in THIS workflow"
EFF = W.effective_workflows(ROOT)
COPIES = (("browser.yml", EFF["browser.yml"], "render"),
          ("pr-tests.yml", EFF["pr-tests.yml"], "render"))

# ══════════════════════════════════════════════════════════════════════
section("1. BOTH COPIES OF THE JOB HAVE THE TWO STEPS")
# ══════════════════════════════════════════════════════════════════════
STEPS = {}
for _label, _path, _job in COPIES:
    _st = {s.name: s for s in W.steps(_path, _job) if s.name}
    _run, _skip = _st.get(RUN_NAME), _st.get(SKIP_NAME)
    ck(bool(_run and _run.run and _skip and _skip.run),
       "%s's %s job has %r and %r" % (_label, _job, RUN_NAME, SKIP_NAME), str(sorted(_st)))
    eq(_skip and _skip.cond, "always()",
       "   ...and the skip check runs whatever came before it (`if: always()`)")
    STEPS[_label] = (_run.run if _run else "", _skip.run if _skip else "")

# ══════════════════════════════════════════════════════════════════════
# The planted tree: five stubs that record each run and act as told.
# ══════════════════════════════════════════════════════════════════════
STUB = r'''import json, os, sys
name = os.path.basename(__file__)
with open(os.environ["STUB_LEDGER"], "a") as fh:
    fh.write(name + "\n")
mode = json.loads(os.environ.get("STUB_MODES") or "{}").get(name, "ok")
print("stub output of " + name)
if mode == "nobrowser":
    print("  (note) NO BROWSER HERE - the render checks did not run.")
elif mode == "nobrowser-stderr":
    sys.stderr.write("NO BROWSER HERE on stderr\n")
elif mode == "fail":
    print("  a check failed")
    raise SystemExit(1)
'''
_trash = []


def private():
    d = tempfile.mkdtemp(prefix="render-once-")
    _trash.append(d)
    return d.replace("\\", "/")          # Git Bash reads C:/x, never C:\x


def at(*parts):
    return os.path.join(*parts).replace("\\", "/")


def tree(drop=()):
    d = private()
    for t in RENDER:
        if t not in drop:
            open(at(d, t), "w", encoding="utf-8").write(STUB)
    return d


def bash(d, body, env):
    """One step's body, as the runner runs it (`bash -e`, from a file)."""
    sd = private()
    step = at(sd, "step.sh")
    open(step, "w", encoding="utf-8", newline="\n").write(body)
    p = subprocess.run(["bash", "-e", step], cwd=d, env=env,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300)
    return p.returncode, p.stdout + p.stderr


def job(copy, modes=None, drop=(), render=True, env_extra=None, runner_temp=None,
        no_runner_temp=False):
    """Both steps, the GITHUB_ENV hand-off between them replayed.
    -> dict(rc1, out1, rc2, out2, runs={file: count}, log=RENDER_LOG or None)"""
    run_body, skip_body = STEPS[copy]
    d = tree(drop)
    gh = private()
    genv, gout, ledger = (at(gh, n) for n in ("env", "output", "ledger"))
    for f in (genv, gout, ledger):
        open(f, "w").close()
    tmp = private()
    env = dict(os.environ, TMPDIR=tmp, TEMP=tmp, TMP=tmp,
               RUNNER_TEMP=runner_temp or private(), GITHUB_ENV=genv,
               GITHUB_OUTPUT=gout, STUB_LEDGER=ledger,
               STUB_MODES=json.dumps(modes or {}), PYTHONIOENCODING="utf-8")
    env.pop("RENDER_LOG", None)
    if no_runner_temp:
        env.pop("RUNNER_TEMP")
    rc1 = out1 = None
    if render:
        rc1, out1 = bash(d, run_body, env)
    # ⚠️ the runner reads GITHUB_ENV after a step and sets it for the next
    for line in open(genv, encoding="utf-8").read().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env[k] = v
    env.update(env_extra or {})
    rc2, out2 = bash(d, skip_body, env)
    runs = {}
    for line in open(ledger).read().split():
        runs[line] = runs.get(line, 0) + 1
    return dict(rc1=rc1, out1=out1 or "", rc2=rc2, out2=out2, runs=runs,
                log=env.get("RENDER_LOG") or None, tmp=tmp, runner_temp=env.get("RUNNER_TEMP"))


def once(r, want=RENDER):
    return r["runs"] == {t: 1 for t in want}


try:
    for COPY in ("browser.yml", "pr-tests.yml"):
        # ══════════════════════════════════════════════════════════════
        section("2. %s: A CLEAN RUN — EACH FILE ONCE, AND THE SKIP CHECK PASSES" % COPY)
        # ══════════════════════════════════════════════════════════════
        r = job(COPY)
        ck(once(r), "🔴🔴 each of the five render files ran EXACTLY ONCE across the job",
           "runs %r" % r["runs"])
        ck(r["rc1"] == 0 and "ran 5 render test file(s)" in r["out1"],
           "   Render tests is green and ran five files", shown(r["out1"][-200:]))
        ck(all("stub output of " + t in r["out1"] for t in RENDER),
           "   ...and the job's log still shows what each file printed")
        ck(r["rc2"] == 0 and "every render file had a browser" in r["out2"],
           "✅ the skip check is green on a clean log", shown(r["out2"][-200:]))
        _log = r["log"] or ""
        ck(bool(_log and os.path.dirname(_log) == r["runner_temp"]
           and os.path.basename(_log).startswith("render.")),
           "   the log is a mktemp file in RUNNER_TEMP", "RENDER_LOG=%r" % _log)
        ck(bool(_log and os.path.exists(_log)
           and all("stub output of " + t in open(_log, encoding="utf-8").read() for t in RENDER)),
           "   ...holding what every file printed", _log)

        # ══════════════════════════════════════════════════════════════
        section("3. %s: A SKIP FAILS THE SKIP CHECK, ON STDOUT OR STDERR" % COPY)
        # ══════════════════════════════════════════════════════════════
        r = job(COPY, {"test_live_scores.py": "nobrowser"})
        ck(once(r), "🔴 each file still ran exactly once", "runs %r" % r["runs"])
        ck(r["rc1"] == 0, "   Render tests is green (a skip is a note, not a failure)",
           shown(r["out1"][-200:]))
        ck(r["rc2"] != 0 and "::error::1 file(s) reported NO BROWSER" in r["out2"],
           "🔴🔴 ...and the skip check FAILS on the NO BROWSER line it read in the log",
           shown(r["out2"][-200:]))
        r = job(COPY, {"test_nfl_opener.py": "nobrowser-stderr"})
        ck(r["rc2"] != 0 and "NO BROWSER" in r["out2"],
           "🔴 ...and on one a file wrote to stderr", shown(r["out2"][-200:]))

        # ══════════════════════════════════════════════════════════════
        section("4. %s: A FAILING FILE STILL FAILS RENDER TESTS, AND THE REST STILL RUN" % COPY)
        # ══════════════════════════════════════════════════════════════
        r = job(COPY, {"test_box_score.py": "fail"})
        ck(r["rc1"] != 0 and "::error::test_box_score.py FAILED" in r["out1"],
           "🔴🔴 Render tests is RED and names the file (the pipe keeps its exit code)",
           shown(r["out1"][-200:]))
        ck(once(r), "   ...every other file still ran, each once", "runs %r" % r["runs"])
        ck(r["rc2"] == 0, "   the skip check judges only skips: nothing skipped, green",
           shown(r["out2"][-200:]))
        r = job(COPY, {"test_league_switch.py": "fail"})
        ck(r["rc1"] != 0 and "::error::test_league_switch.py FAILED" in r["out1"],
           "   ...the last file failing too", shown(r["out1"][-200:]))

        # ══════════════════════════════════════════════════════════════
        section("5. %s: FEWER THAN FIVE FILES STILL FAILS" % COPY)
        # ══════════════════════════════════════════════════════════════
        r = job(COPY, drop=("test_nfl_opener.py",))
        ck(r["rc1"] != 0 and "::error::only 4 render file(s) found" in r["out1"],
           "🔴 Render tests is RED when the set has shrunk", shown(r["out1"][-200:]))
        ck(once(r, [t for t in RENDER if t != "test_nfl_opener.py"]),
           "   ...and the four that exist ran once each", "runs %r" % r["runs"])

        # ══════════════════════════════════════════════════════════════
        section("6. %s: ⛔ A LOG THE SKIP CHECK CANNOT READ IS A FAILURE" % COPY)
        # ══════════════════════════════════════════════════════════════
        r = job(COPY, render=False)
        ck(r["rc2"] != 0 and "::error::Render tests left no output to read" in r["out2"],
           "🔴🔴 Render tests never ran (no RENDER_LOG): the skip check FAILS",
           shown(r["out2"][-200:]))
        ck(r["runs"] == {}, "   ...and it ran no render file itself", "runs %r" % r["runs"])
        _empty = at(private(), "empty.log")
        open(_empty, "w").close()
        r = job(COPY, render=False, env_extra={"RENDER_LOG": _empty})
        ck(r["rc2"] != 0 and "::error::Render tests left no output to read" in r["out2"],
           "🔴 an EMPTY log fails", shown(r["out2"][-200:]))
        r = job(COPY, render=False, env_extra={"RENDER_LOG": _empty + ".gone"})
        ck(r["rc2"] != 0 and "::error::" in r["out2"], "🔴 a log that is not there fails",
           shown(r["out2"][-200:]))
        _part = at(private(), "partial.log")
        open(_part, "w", encoding="utf-8", newline="\n").write(
            "\n── test_box_live.py\nstub output\n\n── test_box_score.py\nstub output\n")
        r = job(COPY, render=False, env_extra={"RENDER_LOG": _part})
        ck(r["rc2"] != 0 and "::error::Render tests never ran test_live_scores.py "
           "test_nfl_opener.py test_league_switch.py" in r["out2"],
           "🔴 a log that stops part way fails, naming the files it never saw",
           shown(r["out2"][-200:]))

        # ══════════════════════════════════════════════════════════════
        section("7. %s: THE LOG IS A FILE OF ITS OWN" % COPY)
        # ══════════════════════════════════════════════════════════════
        _shared = private()
        a, b = job(COPY, runner_temp=_shared), job(COPY, runner_temp=_shared)
        ck(bool(a["log"] and b["log"] and a["log"] != b["log"]
           and a["rc2"] == 0 and b["rc2"] == 0),
           "🔴 two copies sharing one RUNNER_TEMP get two logs (mktemp, never a fixed name)",
           "%r vs %r" % (a["log"], b["log"]))
        r = job(COPY, no_runner_temp=True)
        # ⚠️ compared by the private folder's own (random) name: Git Bash hands
        #    TMPDIR to mktemp as /tmp/..., the same folder in its own spelling
        ck(bool(r["log"] and os.path.basename(os.path.dirname(r["log"])) == os.path.basename(r["tmp"])
           and os.path.basename(r["log"]).startswith("render.") and r["rc2"] == 0),
           "   ...and with no RUNNER_TEMP it falls back to TMPDIR, never a fixed /tmp path",
           "RENDER_LOG=%r TMPDIR=%r" % (r["log"], r["tmp"]))
finally:
    for _d in _trash:
        shutil.rmtree(_d, ignore_errors=True)
note("both copies driven: browser.yml as it will be live (%s) and pr-tests.yml's render job"
     % os.path.relpath(EFF["browser.yml"], ROOT).replace("\\", "/"))
