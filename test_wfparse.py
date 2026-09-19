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
"""
import glob
import io
import os

import wfparse as W
from tcheck import ck, note, section

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
