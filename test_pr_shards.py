#!/usr/bin/env python3
"""🔴🔴 THE SUITE IS SPLIT ACROSS PARALLEL JOBS — AND NOTHING FALLS BETWEEN THEM.

`[2026-09-25]` pr-tests took 25-45 minutes: on PR #163's last run 37m25s
(24.04) and 39m25s (26.04), of which `test_vacuity.py`'s sweep was 1,883s
and 1,960s. The sweep already fills every core of one runner, so pr-tests
now runs each image as five jobs: `rest` (every file but the sweep) and
`sweep 1/4` .. `sweep 4/4` (the one sweep, dealt round-robin).

⛔ A SPLIT IS ONLY A SPEED-UP IF THE PIECES STILL ADD UP TO THE WHOLE. A
part missing from the matrix, a selector that drops a file, or a partition
that repeats one declaration and loses another would each go GREEN while
checking less, and no single job could see it. So this file asks, of the
REAL workflows and the REAL declarations:
  1. pr-tests runs `rest` and parts 1..N of ONE N, each exactly once, on
     every image;
  2. the Tests loop — driven, not read — runs rest + sweep = every file,
     none twice, refuses an unknown shard and a shard that ran nothing;
  1b. `[2026-11-01]` the nightly's `vacuity.yml` runs parts 1..N of ONE N too;
  3. the N parts cover every declared mutation, and every tier 1 pair, exactly
     once;
  4. `vacuity.tier2` and `tier1` really sweep only their part (driven on a
     planted tree);
  4b. `[Sam, 2026-10-02]` collect runs the `rest` share and NOT the sweep (it
     checks the tests, not the data, and held every pull back 33+ minutes),
     while the nightly `vacuity.yml` still sweeps everything (its step is
     read in test_vacuity_pool.py: a step this file names counts as driven).
     ~~main() takes no part~~ `[2026-11-01]` main() hands VACUITY_PART to both
     tiers, and sweeps everything when it is unset.

# @vacuity 🔴🔴 collect's Tests step skips the sweep
#   file: docs/upload/collect.yml
#   find:           SUITE_SHARD: rest
#   with:           SUITE_SHARD: all
#
# @vacuity 🔴 vacuity.main() hands its part to tier 2, and unset stays whole
#   file: vacuity.py
#   find:     t2 = tier2(leaks=wleaks, part=part)
#   with:     t2 = tier2(leaks=wleaks, part=(1, 4))
#
# @vacuity 🔴 vacuity.main() hands its part to tier 1 too
#   file: vacuity.py
#   find:     t1 = tier1(leaks=wleaks, part=part)
#   with:     t1 = tier1(leaks=wleaks)
#
# @vacuity 🔴 vacuity.main() reads VACUITY_PART at all
#   file: vacuity.py
#   find:     part = parse_part(os.environ.get("VACUITY_PART"))
#   with:     part = None
#
# @vacuity 🔴🔴 tier1 ignoring its part is caught
#   file: vacuity.py
#   find:     return _pool(root, JOBS if jobs is None else jobs, part_of(pairs, part),
#   with:     return _pool(root, JOBS if jobs is None else jobs, pairs,
#
# @vacuity 🔴🔴 a nightly part missing from the matrix is caught
#   file: docs/upload/vacuity.yml
#   find:         part: [1, 2, 3, 4]
#   with:         part: [1, 2, 3]

# @vacuity 🔴🔴 a sweep part missing from the matrix is caught
#   file: .github/workflows/pr-tests.yml
#   find:         shard: [rest, 1/4, 2/4, 3/4, 4/4]
#   with:         shard: [rest, 1/4, 2/4, 3/4]
#
# @vacuity 🔴🔴 a rest shard that also runs the sweep is caught
#   file: .github/workflows/pr-tests.yml
#   find:               rest)  [ "$1" != test_vacuity.py ] ;;
#   with:               rest)  return 0 ;;
#
# @vacuity 🔴 a shard that ran nothing is a failure
#   file: .github/workflows/pr-tests.yml
#   find:           if [ "$ran" -lt 1 ] || { [ "$shard" = all ] && [ "$ran" != "$found" ]; }; then
#   with:           if false; then
#
# @vacuity 🔴 an unknown shard is refused, in the loop collect.yml will run
#   file: docs/upload/collect.yml
#   find:             *) echo "::error::unknown SUITE_SHARD=$shard"; exit 1 ;;
#   with:             *) ;;
#
# @vacuity 🔴🔴 a partition that loses declarations is caught
#   file: vacuity.py
#   find:     return [x for i, x in enumerate(items) if i % n == k - 1]
#   with:     return [x for i, x in enumerate(items) if i % n == 0]
#
# @vacuity 🔴🔴 tier2 ignoring its part is caught
#   file: vacuity.py
#   find:     return _pool(root, JOBS if jobs is None else jobs, part_of(ds, part),
#   with:     return _pool(root, JOBS if jobs is None else jobs, ds,
#
# @vacuity 🔴 stub output is printed neutralised, never as a workflow command
#   file: tcheck.py
#   find: DEFUSED = ": :"
#   with: DEFUSED = "::"
# ⚠️ Re-pointed 2026-09-26 from `shown()`'s own line: tcheck now also
#    defuses every line it prints, so breaking `shown()` alone left this
#    file green (VACUOUS, pr-tests sweep 1/4 on PR #187). `DEFUSED` is
#    the one spelling both read, so this still breaks what protects §5.
"""
import contextlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

import vacuity as V
import wfparse as W
from tcheck import ck, note, section, shown

ROOT = os.path.dirname(os.path.abspath(__file__))
PR_PATH = os.path.join(ROOT, ".github", "workflows", "pr-tests.yml")
PR = open(PR_PATH, encoding="utf-8").read()

# ════════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 PR-TESTS RUNS `rest` AND EVERY SWEEP PART, ON EVERY IMAGE")
# ════════════════════════════════════════════════════════════════════════
_job = re.search(r"(?ms)^  tests:\n(.*?)(?=^  [a-z][\w-]*:\n)", PR)
_job = _job.group(1) if _job else ""
ck("⚠️ the tests job was found", len(_job) > 200,
   "⛔ every check below reads it (rule 67). got %d chars" % len(_job))
_sh = re.findall(r"(?m)^        shard: \[(.*)\]\s*$", _job)
SHARDS = [x.strip() for x in _sh[0].split(",")] if len(_sh) == 1 else []
ck("⚠️ ...with exactly one shard list", len(_sh) == 1 and SHARDS,
   "got %r" % _sh)
ck("🔴 `rest` is in it exactly once", SHARDS.count("rest") == 1,
   "⛔ without it every file but the sweep runs nowhere. got %r" % SHARDS)
_parts = [x for x in SHARDS if x != "rest"]
try:
    PARTS = [V.parse_part(x) for x in _parts]
except ValueError as e:
    PARTS = []
    ck("🔴 every other entry is a sweep part `k/n`", False, str(e))
N = PARTS[0][1] if PARTS else 0
ck("🔴🔴 the sweep parts are 1..N of ONE N, each exactly once",
   N >= 1 and sorted(PARTS) == [(k, N) for k in range(1, N + 1)],
   "⛔ a missing part is a quarter of the sweep that runs nowhere, and "
   "every other job still goes green. got %r" % _parts)
ck("⛔ ...and no image is left out of any shard",
   "include:" not in _job and "exclude:" not in _job
   and re.search(r"(?m)^        os: \[ubuntu-24\.04, ubuntu-26\.04\]\s*$", _job),
   "⛔ the matrix must be the full cross product: every shard on every image")
_env = {k: v.strip() for k, v in
        re.findall(r"(?m)^      (SUITE_SHARD|VACUITY_PART): (.*)$", _job)}
ck("🔴 each job is told its shard and its part",
   _env.get("SUITE_SHARD") == "${{ matrix.shard == 'rest' && 'rest' || 'sweep' }}"
   and _env.get("VACUITY_PART") == "${{ matrix.shard != 'rest' && matrix.shard || '' }}",
   "⛔ a job that is not told its part sweeps EVERYTHING (slow, never "
   "wrong); one told the wrong part sweeps another's share. got %r" % _env)
note("pr-tests: %d job(s) per image (%s)" % (len(SHARDS), ", ".join(SHARDS)))

# 🔴 `[2026-11-01]` THE NIGHTLY'S MATRIX IS HELD TO THE SAME BAR, as it will be
#    live. Its step is told `matrix.part` (test_vacuity_pool.py) and its report
#    wants every part (test_vacuity_merge.py).
_ntext = W.read(W.effective_workflows(ROOT)["vacuity.yml"])
_nm = re.findall(r"(?m)^        part: \[(.*)\]\s*$", _ntext)
NPARTS = [x.strip() for x in _nm[0].split(",")] if len(_nm) == 1 else []
# ⚠️ N IS WHAT THE JOBS ARE TOLD, never the matrix's own length: [1, 2, 3] is a
#    fine list of itself, and with `/4` it leaves part 4/4 swept by nobody.
_ndiv = re.findall(r"(?m)^\s+VACUITY_PART: \$\{\{ matrix\.part \}\}/(\d+)\s*$", _ntext)
NN = int(_ndiv[0]) if len(_ndiv) == 1 else 0
ck("🔴🔴 the nightly's parts are 1..N of ONE N, each exactly once",
   NN >= 2 and NPARTS == [str(k) for k in range(1, NN + 1)],
   "⛔ a missing part is a quarter of the sweep that runs nowhere, every night, "
   "and only a part that RAN can say so. matrix %r, told /%r" % (_nm, _ndiv))
note("nightly: %d part(s)" % NN)

# ════════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 THE TESTS LOOP, DRIVEN: REST + SWEEP = EVERY FILE, ONCE")
# ════════════════════════════════════════════════════════════════════════
# ⛔ Not read and agreed with — the real step body is executed under the
#    shell GitHub uses, with `python` and `node` replaced by a recorder.
FIX = ["test_a.py", "test_b.py", "test_vacuity.py", "test_c.js", "test_d.js"]
SHIM = '#!/bin/sh\necho "$1" >> "$RAN_LOG"\nexit 0\n'


def drive(body, shard, files=FIX):
    """-> (rc, [files the step ran], output)."""
    d = tempfile.mkdtemp(prefix="shards-")
    try:
        b = os.path.join(d, "bin")
        os.makedirs(b)
        for exe in ("python", "node"):
            with open(os.path.join(b, exe), "w") as fh:
                fh.write(SHIM)
            os.chmod(os.path.join(b, exe), 0o755)
        for f in files:
            open(os.path.join(d, f), "w").write("")
        env = dict(os.environ, PATH=b + os.pathsep + os.environ["PATH"],
                   RAN_LOG=os.path.join(d, "ran.log"),
                   GITHUB_OUTPUT=os.path.join(d, "out"))
        env.pop("SUITE_SHARD", None)
        if shard is not None:
            env["SUITE_SHARD"] = shard
        p = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail",
                            "-c", body], cwd=d, env=env, capture_output=True,
                           text=True, timeout=120)
        log = os.path.join(d, "ran.log")
        ran = open(log).read().split() if os.path.exists(log) else []
        return p.returncode, ran, p.stdout + p.stderr
    finally:
        shutil.rmtree(d, ignore_errors=True)


_bodies = {"pr-tests.yml": W.step_run(PR_PATH, step_name="Tests"),
           "collect.yml (as it will be live)":
               W.step_run(W.effective_workflows(ROOT)["collect.yml"],
                          step_name="Tests")}
for _name, _body in _bodies.items():
    ck("⚠️ %s: the Tests step was read" % _name,
       bool(_body) and "in_shard" in (_body or ""),
       "⛔ rule 67: nothing below is driven without it")
    if not _body:
        continue
    rc_all, ran_all, o_all = drive(_body, None)
    ck("🔴 %s: unset runs EVERY file, as before the split" % _name,
       rc_all == 0 and sorted(ran_all) == sorted(FIX),
       "⛔ unset is the loop's whole suite (a laptop, `all`); collect runs "
       "`rest` since 2026-10-02 (section 4b). "
       "rc=%s ran=%r %s" % (rc_all, ran_all, shown(o_all[-200:])))
    rc_r, ran_r, o_r = drive(_body, "rest")
    rc_s, ran_s, o_s = drive(_body, "sweep")
    ck("🔴🔴 %s: rest + sweep = every file" % _name,
       sorted(ran_r + ran_s) == sorted(FIX) and rc_r == 0 and rc_s == 0,
       "⛔ a file in neither shard is a test that runs nowhere. "
       "rest=%r sweep=%r" % (ran_r, ran_s))
    ck("🔴🔴 %s: ...and no file in both" % _name,
       not (set(ran_r) & set(ran_s)) and ran_s == ["test_vacuity.py"],
       "⛔ the sweep twice is the 40-minute job this split removes. "
       "rest=%r sweep=%r" % (ran_r, ran_s))
    ck("   %s: every shard still counts the WHOLE suite" % _name,
       all("of 5 test file(s)" in o for o in (o_all, o_r, o_s)),
       "⛔ the shrink check must see every file in every shard")
    rc_u, ran_u, o_u = drive(_body, "bogus")
    ck("🔴 %s: an unknown shard is REFUSED, and runs nothing" % _name,
       rc_u != 0 and ran_u == [] and "unknown SUITE_SHARD" in o_u,
       "⛔ a typo in a shard name must be red, never a silent pass. "
       "rc=%s ran=%r" % (rc_u, ran_u))
    rc_e, ran_e, o_e = drive(_body, "sweep",
                             [f for f in FIX if f != "test_vacuity.py"])
    ck("🔴 %s: a shard that ran NOTHING is red" % _name,
       rc_e != 0 and ran_e == [],
       "⛔ rename test_vacuity.py and the sweep jobs would pass having run "
       "nothing. rc=%s %s" % (rc_e, shown(o_e[-200:])))

# ════════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 THE PARTS COVER EVERY DECLARED MUTATION, EACH EXACTLY ONCE")
# ════════════════════════════════════════════════════════════════════════
DECLS = [(d["test"], d["line"]) for d in V.declarations(ROOT)]
ck("⚠️ there are declarations to partition", len(DECLS) >= 100,
   "⛔ a partition of nothing covers everything (rule 67). got %d" % len(DECLS))
if N:
    _got = [V.part_of(DECLS, (k, N)) for k in range(1, N + 1)]
    _flat = [x for g in _got for x in g]
    ck("🔴🔴 the %d parts together are every declaration" % N,
       sorted(_flat) == sorted(DECLS),
       "⛔ a declaration in no part is a guard nobody proves bites. "
       "%d swept of %d" % (len(_flat), len(DECLS)))
    ck("🔴 ...none of them in two parts", len(_flat) == len(set(_flat)),
       "⛔ %d applied twice" % (len(_flat) - len(set(_flat))))
    ck("   ...and the parts are the same size, give or take one",
       max(map(len, _got)) - min(map(len, _got)) <= 1,
       "sizes %r" % [len(g) for g in _got])
    note("%d declarations over %d parts: %s"
         % (len(DECLS), N, [len(g) for g in _got]))
# `[2026-11-01]` The nightly sweeps tier 1 as well, on its own N.
PAIRS = sorted(V.name_map(ROOT).items())
ck("⚠️ there are tier 1 pairs to partition", len(PAIRS) >= 10,
   "⛔ rule 67. got %d" % len(PAIRS))
if NN:
    for _name, _items in (("declaration", DECLS), ("tier 1 pair", PAIRS)):
        _got = [V.part_of(_items, (k, NN)) for k in range(1, NN + 1)]
        _flat = [x for g in _got for x in g]
        ck("🔴🔴 the nightly's %d parts together are every %s, each once" % (NN, _name),
           sorted(_flat) == sorted(_items) and len(_flat) == len(set(_flat)),
           "⛔ %d swept of %d" % (len(_flat), len(_items)))
ck("✅ unset means everything", V.part_of(DECLS, None) == DECLS)
_bad = []
for _s in ("0/4", "5/4", "1/0", "x", "2", "-1/4"):
    try:
        V.parse_part(_s)
        _bad.append(_s)
    except ValueError:
        pass
ck("🔴 a malformed part RAISES rather than sweeping some other share",
   not _bad and V.parse_part("") is None and V.parse_part("3/4") == (3, 4),
   "accepted: %r" % _bad)

# ════════════════════════════════════════════════════════════════════════
section("4. 🔴🔴 tier2 REALLY SWEEPS ONLY ITS PART — driven on a planted tree")
# ════════════════════════════════════════════════════════════════════════
_d = tempfile.mkdtemp(prefix="shards-plant-")
try:
    open(os.path.join(_d, "subject.py"), "w").write("X = 1\n")
    for _i in range(3):
        open(os.path.join(_d, "test_p%d.py" % _i), "w").write(
            "# @vacuity planted %d\n#   file: subject.py\n#   find: X = 1\n"
            "#   with: X = 2\nimport sys, subject\n"
            "sys.exit(0 if subject.X == 1 else 1)\n" % _i)
    _seen = []
    for _k in (1, 2, 3):
        _r = V.tier2(_d, jobs=1, part=(_k, 3))
        ck("🔴 part %d/3 swept exactly one planted declaration, and it bit" % _k,
           len(_r) == 1 and _r[0]["state"] == "BITES",
           "⛔ got %r" % [(r["test"], r["state"]) for r in _r])
        _seen += [r["test"] for r in _r]
    ck("🔴🔴 ...and the three parts swept all three, once each",
       sorted(_seen) == ["test_p0.py", "test_p1.py", "test_p2.py"],
       "got %r" % _seen)
    ck("✅ ...while no part sweeps all three",
       len(V.tier2(_d, jobs=1)) == 3,
       "⛔ the unsplit sweep is the baseline the parts must add up to")
    # `[2026-11-01]` Tier 1 the same way: each planted subject has its own test.
    for _i in range(3):
        open(os.path.join(_d, "mod%d.py" % _i), "w").write("def f():\n    return 1\n")
        open(os.path.join(_d, "test_mod%d.py" % _i), "w").write(
            "import sys, mod%d\nsys.exit(0 if mod%d.f() == 1 else 1)\n" % (_i, _i))
    _pairs = [V.tier1(_d, jobs=1, part=(_k, 3)) for _k in (1, 2, 3)]
    ck("🔴🔴 tier 1's parts swept the three pairs, once each, and all three bit",
       [[r["test"] for r in p] for p in _pairs]
       == [["test_mod0.py"], ["test_mod1.py"], ["test_mod2.py"]]
       and all(p[0]["state"] == "BITES" for p in _pairs),
       "⛔ the nightly sweeps tier 1 in parts too. got %r"
       % [[(r["test"], r["state"]) for r in p] for p in _pairs])
    ck("✅ ...while unsplit it sweeps all three", len(V.tier1(_d, jobs=1)) == 3,
       "⛔ the baseline the parts must add up to")
finally:
    shutil.rmtree(_d, ignore_errors=True)

# ════════════════════════════════════════════════════════════════════════
section("4b. 🔴🔴 COLLECT SKIPS THE SWEEP; EVERY PR AND EVERY NIGHT STILL RUN IT")
# ════════════════════════════════════════════════════════════════════════
# `[Sam, 2026-10-02]` collect's Tests step runs before "Decide what this run
# collects", and test_vacuity.py's sweep took 33m06s of it in #2092 (timed
# out at 2400s in #2093): every pull started 35+ minutes late. The sweep is
# a check on the TESTS, not the data. Sections 1 and 3 hold every PR to all
# of it; this holds collect to the rest and the nightly to the whole.
_wf = W.effective_workflows(ROOT)
_cenv = W.step_env(_wf["collect.yml"], step_name="Tests") or {}
_cbody = _bodies["collect.yml (as it will be live)"] or ""
rc_c, ran_c, o_c = drive(_cbody, _cenv.get("SUITE_SHARD"))
ck("🔴🔴 collect's Tests step, with its own env, runs every file but test_vacuity.py",
   rc_c == 0 and sorted(ran_c) == sorted(f for f in FIX if f != "test_vacuity.py"),
   "⛔ the sweep in collect holds every data pull back by its whole length. "
   "env=%r ran=%r %s" % (_cenv, ran_c, shown(o_c[-200:])))


def _main_calls(part):
    """What `vacuity.main()` asks of its tiers. -> [(tier, args, kwargs)].

    ⛔ The env is set, never inherited: pr-tests runs this file with
    VACUITY_PART set for its sweep jobs, and its sweep runs it as a child.
    """
    calls, keep = [], (V._porcelain, V.tier1, V.tier2, V.leaked)
    saved = {k: os.environ.pop(k, None) for k in ("VACUITY_PART", "VACUITY_OUT")}
    try:
        if part is not None:
            os.environ["VACUITY_PART"] = part
        V._porcelain, V.leaked = (lambda *a, **k: ""), (lambda *a, **k: (True, ""))
        V.tier1 = lambda *a, **k: calls.append(("tier1", a, {x: y for x, y in k.items() if x != "leaks"})) or []
        V.tier2 = lambda *a, **k: calls.append(("tier2", a, {x: y for x, y in k.items() if x != "leaks"})) or []
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            V.main()
    finally:
        V._porcelain, V.tier1, V.tier2, V.leaked = keep
        os.environ.pop("VACUITY_PART", None)
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
    return calls


# 🔴 `[2026-11-01]` ~~sweeps both tiers whole: no part, no subset~~: REWRITTEN,
#    STRICTER. main() now takes its part from the env, so the question has two
#    halves, and the old form asked one: unset it is the whole sweep (the deployed
#    nightly, until Sam's upload), and set, BOTH tiers get that part and nothing
#    else (a part that swept all of tier 1 would run it four times over).
_u = _main_calls(None)
ck("🔴 unset, vacuity.main() sweeps both tiers whole: no part, no subset",
   [c[0] for c in _u] == ["tier1", "tier2"]
   and all(not a and not k.get("part") and set(k) <= {"jobs", "part"} for _t, a, k in _u),
   "⛔ what the deployed nightly does until Sam's upload. got %r" % _u)
for _spec, _want in (("2/4", (2, 4)), ("4/4", (4, 4))):
    _s = _main_calls(_spec)
    ck("🔴🔴 with VACUITY_PART=%s, main() gives both tiers that part and only that" % _spec,
       [c[0] for c in _s] == ["tier1", "tier2"]
       and all(not a and k.get("part") == _want and set(k) <= {"jobs", "part"}
               for _t, a, k in _s),
       "⛔ a tier that ignores its part is swept whole by all four jobs; one with "
       "the wrong part leaves a share nobody sweeps. got %r" % _s)

# ════════════════════════════════════════════════════════════════════════
section("5. 🔴 A GREEN RUN OF THIS FILE PRINTS NO ERROR COMMAND")
# ════════════════════════════════════════════════════════════════════════
# ⛔ Checked on the REAL output: this file is run again as a child (which
#    skips only this section, so it cannot recurse) and everything it
#    printed is searched. `[2026-09-25]` 4 error annotations on a green
#    pr-tests run came from here.
_CHILD = "TEST_PR_SHARDS_CHILD"
if not os.environ.get(_CHILD):
    _p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__)],
                        cwd=ROOT, capture_output=True, text=True, timeout=300,
                        env=dict(os.environ, **{_CHILD: "1"}))
    _txt = (_p.stdout or "") + (_p.stderr or "")
    ck("⚠️ the child run passed and printed its checks",
       _p.returncode == 0 and "checks passed" in _txt,
       "⛔ an empty or failed run contains no error command and proves "
       "nothing (rule 67). rc=%s, %d chars" % (_p.returncode, len(_txt)))
    _ERR = "::" + "error::"      # spelled apart so this file's own text never matches
    _hits = [l for l in _txt.splitlines() if _ERR in l]
    ck("🔴 ...and NOTHING it printed contains the error command",
       not _hits,
       "⛔ GitHub makes each such line an error annotation on a green run. "
       "%d line(s), first: %s" % (len(_hits), shown(_hits[0][:160]) if _hits else ""))
