#!/usr/bin/env python3
"""🔴 THE HAND PARSER IS CROSS-CHECKED AGAINST PyYAML, AND DRIVEN WITHOUT IT.

`wfparse.py` exists because **PyYAML is not installed on the CI runner**
(measured 2026-09-19, job 105862432594 — `ModuleNotFoundError: No module
named 'yaml'` turned `test_watch_label.py` red on every CI run from the
hour it merged). Four checks in this repo now parse a workflow through it,
so a quiet parser bug would take all four down at once — or worse, leave
them green on nothing.

✅ SO IT IS MEASURED TWO WAYS.
  §1 drives it against **synthetic files whose answer is known**, and runs
     everywhere including CI.
  §2 compares it to **PyYAML on all ten real workflows**, wherever PyYAML
     happens to exist, and says so out loud when it does not.

⛔ §2 CANNOT BE THE ONLY HALF. That is the mistake `test_multileague.py`
and `test_season_default.py` both make: their cross-check is skipped on the
runner, so on the machine that matters they assert nothing about the parse.
§1 is the half that runs where it counts.

# @vacuity 🔴 a block scalar read as structure is caught
#   file: wfparse.py
#   find:         if not _BLOCK.match(val):
#   with:         if True:
#
# @vacuity ⚠️ a hardcoded step column is caught
#   file: wfparse.py
#   find:         col = min(e[1] for e in dashes)
#   with:         col = 8
#
# @vacuity 🔴 a job's env is its own, never the next job's (the §3j review)
#   file: wfparse.py
#   find:             if not jb.start <= lineno < jb.end:
#   with:             if not jb.start <= lineno:
#
# §3 `[2026-11-13]` A TRAILING COMMENT IS NOT PART OF A VALUE, AND A CLOCK NOBODY
# CAN READ IS NOT "NO CLOCK" (every reader, every workflow, deployed and staged):
# @vacuity 🔴🔴 `timeout-minutes: 45   # the clock` is a 45-minute clock
#   file: wfparse.py
#   find:                     out[jb.name] = int(_value(val))
#   with:                     out[jb.name] = int(val.strip().strip('"').strip("'"))
#
# @vacuity 🔴 a clock set to something that is not a number is UNREADABLE, never None
#   file: wfparse.py
#   find:                     out[jb.name] = UNREADABLE
#   with:                     pass
#
# @vacuity ⚠️ a permission's level loses its comment
#   file: wfparse.py
#   find:         out[key] = _value(val)   # a scope's level
#   with:         out[key] = val.strip().strip('"').strip("'")
#
# @vacuity ⚠️ a step's name loses its comment
#   file: wfparse.py
#   find:                     name = _value(val)
#   with:                     name = val.strip().strip('"').strip("'")
#
# @vacuity ⚠️ a step's id loses its comment
#   file: wfparse.py
#   find:                     sid = _value(val)
#   with:                     sid = val.strip().strip('"').strip("'")
#
# @vacuity ⚠️ a step's `if:` loses its comment and keeps its own quotes
#   file: wfparse.py
#   find:                     cond = body.strip() if body is not None else _uncomment(val)
#   with:                     cond = body.strip() if body is not None else val.strip()
#
# @vacuity ⚠️ a step's env value loses its comment
#   file: wfparse.py
#   find:                 out[key] = _value(val)   # a step's own env value
#   with:                 out[key] = val.strip().strip('"').strip("'")
#
# @vacuity 🔴 the timed-out alarm holds an unreadable clock to 0, never GitHub's 360
#   file: runs_report.py
#   find:             mins = UNREADABLE_CLOCK if mins is wfparse.UNREADABLE else mins
#   with:             mins = DEFAULT_CLOCK if mins is wfparse.UNREADABLE else mins
#
# @vacuity ⚠️ the landing check reads an unreadable clock as GitHub's ceiling, and does not crash
#   file: watchdog.py
#   find:         lim = [LANDING_TIMEOUT_DEFAULT if m is wfparse.UNREADABLE else (m or LANDING_TIMEOUT_DEFAULT)
#   with:         lim = [m if m is wfparse.UNREADABLE else (m or LANDING_TIMEOUT_DEFAULT)
"""
import glob
import io
import os
import re
import shutil
import tempfile

import wfparse as W
from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
FILES = sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")))

# ════════════════════════════════════════════════════════════════════════
section("1. 🔴 DRIVEN ON KNOWN ANSWERS — THIS HALF RUNS ON THE RUNNER")
# ════════════════════════════════════════════════════════════════════════
SYN = """\
name: demo
on:
  schedule:
    - cron: "5 * * * *"
permissions:
  contents: read
jobs:
  alpha:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    steps:
      - uses: actions/checkout@v4
      - name: talk
        id: talk
        run: |
          # jobs:
          #   beta:
          #     permissions:
          #       issues: write
          echo "permissions:"
          gh issue list
      - name: quiet
        run: echo one-liner
  beta:
    runs-on: ubuntu-latest
    steps:
      - name: nothing
        run: |
          echo hi
"""
jbs = W.jobs(SYN)
ck("🔴 the jobs are the jobs, and a block scalar is not structure",
   [j.name for j in jbs] == ["alpha", "beta"],
   "⛔ the `run:` body above contains the literal lines `jobs:`, `beta:` "
   "and `permissions:`. A scanner that reads a block scalar as YAML "
   "reports a workflow that does not exist — and this repo's agent "
   "prompts are full of exactly that text. got %s"
   % [j.name for j in jbs])
ck("⛔ a job's OWN permissions block is read, not the file's",
   jbs[0].permissions == {"contents": "read", "issues": "write"},
   "🔴 the whole point of test_gh_permissions.py is the per-JOB grant. "
   "got %r" % (jbs[0].permissions,))
ck("⚠️ ...and a job that declares none reports none, rather than the file's",
   jbs[1].permissions == {},
   "⛔ inheriting silently is how a job with no grant looks compliant. "
   "got %r" % (jbs[1].permissions,))
ck("✅ the workflow-level block is still readable on its own",
   W.permissions(SYN) == {"contents": "read"},
   "got %r" % (W.permissions(SYN),))
ck("⚠️ ...and the commented `permissions:` INSIDE the run body is not it",
   "issues" not in W.permissions(SYN),
   "⛔ rule 244's cousin: a parser that matches prose reports a grant that "
   "does not exist, which is worse than reporting none. got %r"
   % (W.permissions(SYN),))

sts = W.steps(SYN, "alpha")
ck("🔴 every step of the job is found, uses: and run: alike",
   [s.name for s in sts] == [None, "talk", "quiet"],
   "⛔ a step skipped is a `gh` call nothing judges. got %s"
   % [s.name for s in sts])
ck("⚠️ a one-line `run:` is a run, not a miss",
   sts[2].run == "echo one-liner",
   "⛔ `run: echo x` is legal and common. got %r" % (sts[2].run,))
ck("🔴 the block body is dedented and complete",
   (W.step_run(SYN, step_id="talk") or "").endswith("gh issue list\n")
   and (W.step_run(SYN, step_id="talk") or "").startswith("# jobs:"),
   "⛔ a truncated body is a drive that checks less than it claims. "
   "got %r" % (W.step_run(SYN, step_id="talk"),))
# ⚠️ ASKED AGAINST `beta`, WHOSE FIRST STEP HAS A REAL `run:`. Asked
#    against `alpha` this check was VACUOUS and the sweep said so: alpha's
#    first step is a bare `uses:`, so a parser that wrongly returned step
#    ONE still returned None and the check passed under the mutation.
ck("⛔ an id that does not exist returns None, it does not guess",
   W.step_run(SYN, step_id="nope", job="beta") is None
   and W.step_run(SYN, step_id="nope") is None,
   "🔴 every caller checks for None; a parser that returned the FIRST step "
   "instead would make every drive silently test the wrong script. "
   "beta's first step is `echo hi`, so a guesser is visible here. got %r"
   % (W.step_run(SYN, step_id="nope", job="beta"),))
ck("⚠️ a step can also be found by name when it carries no id",
   W.step_run(SYN, step_name="quiet") == "echo one-liner",
   "⛔ most steps in this repo have a name and no id.")

_IND = SYN.replace("    steps:\n      - uses:", "    steps:\n    - uses:")
_IND = _IND.replace("      - name: talk", "    - name: talk")
_IND = _IND.replace("        id: talk", "      id: talk")
_IND = _IND.replace("        run: |", "      run: |")
_IND = _IND.replace("          # jobs:", "        # jobs:")
ck("⚠️ the step column is DERIVED, so a legally re-indented list still parses",
   len(W.steps(_IND, "alpha")) >= 2,
   "⛔ rule 293: a column hardcoded from today's formatting is a claim "
   "about the world. got %d step(s)" % len(W.steps(_IND, "alpha")))

# `[2026-11-08]` job_env: a job's own job-level env, never a step's and never the next job's. Three
#    tests read pr-tests' `offseason` / `staged` env as the text down to the `render:` job; a new job in
#    between carried its own SUITE_SHARD, which passed the check for a job that had lost its own.
_ENV = ("jobs:\n"
        "  first:\n    runs-on: x\n    env:\n      SUITE_SHARD: rest\n      OTHER: \"1\"\n"
        "    steps:\n      - run: echo a\n        env:\n          STEP_ONLY: x\n"
        "  second:\n    runs-on: x\n    steps:\n      - run: echo b\n"
        "  third:\n    runs-on: x\n    env:\n      SUITE_SHARD: rest\n    steps:\n      - run: echo c\n")
ck("🔴 job_env reads each job's own env block, and a step's env is not the job's",
   W.job_env(_ENV) == {"first": {"SUITE_SHARD": "rest", "OTHER": "1"}, "second": {}, "third": {"SUITE_SHARD": "rest"}},
   "got %r" % (W.job_env(_ENV),))
_LOST = _ENV.replace("    env:\n      SUITE_SHARD: rest\n      OTHER: \"1\"\n", "")
ck("🔴 ...so a job that LOSES its env reads empty, though a later job still carries the same line",
   W.job_env(_LOST)["first"] == {} and W.job_env(_LOST)["third"] == {"SUITE_SHARD": "rest"},
   "got %r" % (W.job_env(_LOST),))

# ════════════════════════════════════════════════════════════════════════
section("2. ✅ AND COMPARED TO PyYAML ON THE REAL FILES, WHERE IT EXISTS")
# ════════════════════════════════════════════════════════════════════════
try:
    import yaml as _yaml
except ImportError:
    _yaml = None
    note("⚠️ PyYAML is not installed here — which is the normal state on the "
         "CI runner and the reason wfparse.py exists. §1 above is the half "
         "that just ran; this cross-check did not.")

if _yaml is not None:
    njobs = nsteps = nperms = 0
    bad = []
    for f in FILES:
        doc = _yaml.safe_load(io.open(f, encoding="utf-8")) or {}
        mine = {j.name: j for j in W.jobs(f)}
        ref = list((doc.get("jobs") or {}).keys())
        if list(mine) != ref:
            bad.append("%s jobs %s != %s" % (f, list(mine), ref))
            continue
        njobs += len(ref)
        wl = {k: str(v) for k, v in (doc.get("permissions") or {}).items()}
        if wl != W.permissions(f):
            bad.append("%s workflow permissions" % f)
        for jn in ref:
            nperms += 1
            want = {k: str(v)
                    for k, v in (doc["jobs"][jn].get("permissions") or {}).items()}
            if want != mine[jn].permissions:
                bad.append("%s/%s permissions %r != %r"
                           % (f, jn, mine[jn].permissions, want))
            rsteps = doc["jobs"][jn].get("steps") or []
            hsteps = W.steps(f, jn)
            if len(rsteps) != len(hsteps):
                bad.append("%s/%s step count %d != %d"
                           % (f, jn, len(hsteps), len(rsteps)))
                continue
            for a, b in zip(rsteps, hsteps):
                nsteps += 1
                if (a.get("name") or None) != b.name:
                    bad.append("%s/%s name %r != %r" % (f, jn, b.name, a.get("name")))
                if (a.get("id") or None) != b.id:
                    bad.append("%s/%s id %r != %r" % (f, jn, b.id, a.get("id")))
                if (a.get("run") or "").rstrip() != (b.run or "").rstrip():
                    bad.append("%s/%s run body of %r" % (f, jn, a.get("name")))
    ck("🔴🔴 the hand parse equals PyYAML on every real workflow",
       not bad,
       "⛔ if these two ever disagree, four checks are reading a workflow "
       "that is not the deployed one. differences: %s" % (bad[:6] or "none"))
    ck("⚠️ ...and it really compared something",
       njobs >= 10 and nsteps >= 40 and nperms >= 10,
       "⛔ rule 67. jobs=%d steps=%d permission blocks=%d"
       % (njobs, nsteps, nperms))
    note("cross-checked %d job(s), %d step(s), %d permission block(s) across "
         "%d workflow file(s)" % (njobs, nsteps, nperms, len(FILES)))

# ════════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 A TRAILING COMMENT IS NOT PART OF A VALUE, AND AN UNREADABLE CLOCK IS NOT \"NO CLOCK\"")
# ════════════════════════════════════════════════════════════════════════
# `[2026-11-13]` job_timeouts read `timeout-minutes: 45   # the clock` as None:
# int() failed and was swallowed. runs_report.job_clocks then gave the job GitHub's
# 360, a run its 45-minute clock stopped stayed `cancelled`, and the timed-out-run
# alarm never fired. The step name / id / if, a step's env and a permissions block
# kept a trailing comment too. 0 of 40 real clock lines carried one that day: this
# section guards the class, every reader on every workflow, not the one instance.
import runs_report as RR  # noqa: E402
import watchdog as WD  # noqa: E402

_COMMENTED = """\
name: demo
on:
  schedule:
    - cron: "17 3 * * 1"
jobs:
  learn:
    runs-on: ubuntu-24.04
    timeout-minutes: 45   # the clock
    permissions:
      contents: write   # it commits
    steps:
      - name: Tell Sam   # the report
        id: tell # its id
        if: steps.a.outputs.n != '0'   # only when staged
        env:
          STATE: ok   # the state
          HASH: a#b
          QUOTED: "a # b"
        run: |
          git add data/demo
  quoted:
    runs-on: ubuntu-24.04
    timeout-minutes: "45" # quoted with comment
    steps:
      - run: echo q
  plain:
    runs-on: ubuntu-24.04
    timeout-minutes: 45
    steps:
      - run: echo p
  expr:
    runs-on: ubuntu-24.04
    timeout-minutes: ${{ inputs.minutes }}
    steps:
      - run: echo e
  none:
    runs-on: ubuntu-24.04
    steps:
      - run: echo n
"""
_jt = W.job_timeouts(_COMMENTED)
eq({k: v for k, v in _jt.items() if k != "expr"}, {"learn": 45, "quoted": 45, "plain": 45, "none": None},
   "🔴🔴 a commented, a quoted-and-commented and a plain clock all read 45; only the job with none reads None")
ck("🔴 a clock set to an expression is UNREADABLE, never None (\"no clock\")",
   _jt.get("expr") is W.UNREADABLE, "got %r" % (_jt.get("expr"),))
_st = W.steps(_COMMENTED, "learn")[0]
eq((_st.name, _st.id, _st.cond), ("Tell Sam", "tell", "steps.a.outputs.n != '0'"),
   "⚠️ a step's name, id and `if:` lose their comment, and the `if:` keeps its own quotes")
eq(W.step_env(_COMMENTED, step_name="Tell Sam"), {"STATE": "ok", "HASH": "a#b", "QUOTED": "a # b"},
   "⚠️ a step's env loses its comment; `a#b` and a quoted `a # b` are values, as in YAML")
eq(W.jobs(_COMMENTED)[0].permissions, {"contents": "write"},
   "⚠️ a permission's level loses its comment")

# ── end to end: the two callers that read a clock ──
_R = tempfile.mkdtemp(prefix="wfparse-clock-")
try:
    os.makedirs(os.path.join(_R, ".github", "workflows"))
    with io.open(os.path.join(_R, ".github", "workflows", "demo.yml"), "w", encoding="utf-8") as _fh:
        _fh.write(_COMMENTED)
    _jc = RR.job_clocks(_R).get(".github/workflows/demo.yml") or {}
    eq((_jc.get("learn"), _jc.get("none"), _jc.get("expr")), (45, RR.DEFAULT_CLOCK, RR.UNREADABLE_CLOCK),
       "🔴🔴 the timed-out alarm reads the commented clock as 45 (not GitHub's 360) and an "
       "unreadable one as 0, erring toward a report")
    try:
        _lr = [x for x in WD.learners(_R) if x["file"] == "demo.yml"]
        _lim = _lr[0]["timeout_min"] if _lr else "demo.yml is not a learner here"
    except Exception as _e:  # noqa: BLE001 - the failure under test
        _lim = "raised %s: %s" % (type(_e).__name__, _e)
    eq(_lim, WD.LANDING_TIMEOUT_DEFAULT,
       "⚠️ the landing check takes GitHub's ceiling for the unreadable clock, the longest a job can run")
finally:
    shutil.rmtree(_R, ignore_errors=True)


def value_problems(path):
    """[why] for one workflow: a job whose `timeout-minutes` line the parser does not
    read as a number (or reads one with no such line), or any value a reader returns
    that still holds a ` #` comment."""
    txt = W.read(path)
    lines, out = txt.splitlines(), []
    jt = W.job_timeouts(txt)
    for jb in W.jobs(txt):
        n = sum(1 for ln in lines[jb.start:jb.end] if re.match(r"^    timeout-minutes:", ln))
        got = jt.get(jb.name)
        if n and (not isinstance(got, int) or got is W.UNREADABLE):
            out.append("%s: its timeout-minutes line reads %r" % (jb.name, got))
        if not n and got is not None:
            out.append("%s: no timeout-minutes line, but %r" % (jb.name, got))
        out += ["%s permission %s = %r" % (jb.name, k, v)
                for k, v in (jb.permissions or {}).items() if " #" in str(v)]
    vals = [("workflow permission " + k, v) for k, v in W.permissions(txt).items()]
    for st in W.steps(txt):
        vals += [("step name", st.name), ("step id", st.id), ("step if", st.cond)]
        if st.name:
            vals += [("step env " + k, v) for k, v in (W.step_env(txt, step_name=st.name) or {}).items()]
    for j, env in W.job_env(txt).items():
        vals += [("%s env %s" % (j, k), v) for k, v in env.items()]
    vals += [("%s name" % j, v) for j, v in W.job_names(txt).items()]
    out += ["%s = %r" % (w, v) for w, v in vals if v and " #" in str(v)]
    return out


_ALL = sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))
              + glob.glob(os.path.join(ROOT, "docs", "upload", "*.yml")))
_bad = {os.path.relpath(f, ROOT): value_problems(f) for f in _ALL}
_bad = {f: v for f, v in _bad.items() if v}
_lines = sum(1 for f in _ALL for ln in W.read(f).splitlines() if re.match(r"^    timeout-minutes:", ln))
ck("🔴🔴 every clock line of every workflow, deployed and staged, reads as a number, and no "
   "value any reader returns keeps a comment (%d files, %d clock lines)" % (len(_ALL), _lines),
   not _bad and len(_ALL) >= 20 and _lines >= 30,
   "⛔ a clock read as None is GitHub's 360 to the timed-out alarm; a kept comment is a "
   "value no workflow has (rule 67: files=%d lines=%d). %s" % (len(_ALL), _lines, _bad))
# ⚠️ AND THE SAME SWEEP ON A REAL WORKFLOW WITH COMMENTS WRITTEN IN, so it is never only
#    a sweep of a tree that happens to hold none (0 of 40 real lines did on 2026-11-13).
_t60 = W.read(os.path.join(ROOT, ".github", "workflows", "t60r.yml"))
_pl = re.sub(r"(?m)^(    timeout-minutes: \d+)$", r"\1   # the grade's clock", _t60, count=1)
_pl = re.sub(r"(?m)^(      - name: [^\n#]+)$", r"\1   # a step", _pl, count=1)
_pl = re.sub(r"(?m)^( +contents: \w+)$", r"\1   # its scope", _pl, count=1)
ck("⚠️ the planted copy of t60r.yml really carries the comments",
   _pl.count("   # the grade's clock") == 1 and _pl.count("   # a step") == 1
   and _pl.count("   # its scope") == 1,
   "⛔ a planted case with nothing planted proves nothing (rule 67)")
eq(value_problems(_pl), [], "🔴🔴 ...and the sweep finds no clock lost and no comment kept in it")
eq(W.job_timeouts(_pl), W.job_timeouts(_t60), "   ...and its clocks are the uncommented file's")
