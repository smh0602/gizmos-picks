#!/usr/bin/env python3
"""A MODIFIER WORD RIDES WITH EVERY MODE IT WAS GIVEN WITH.

🔴 WHAT HAPPENED `[measured 2026-11-11]`. collect.yml's dispatch form says
"add `converge-off` after it to run that one mode ALONE (used for
nfl-logs)". It never did. The converge step ran `for m in $MODES; do python
collect.py "$m"`, so "card-fb converge-off" became two calls:
`collect.py card-fb`, which converged everything overdue (collect.py's
`main()` honours `converge-off` only in the SAME argv), and `collect.py
converge-off`, which did nothing. Dispatched college run 42976627011 asked
for card-fb alone and logged "PLAN: cfb-injuries cfb-probe card-fb". It only
ever did work the contract owed, so it cost nothing, but two Claude notes
relied on the form's promise.

✅ THE CLASS, NOT THE INSTANCE. A modifier word is any word `main()` reads
as an instruction about the OTHER words rather than as a mode to run.
⛔ The list is never written down here: `main()` is ASKED. Every word-shaped
string constant in collect.py is handed to `main()` beside a mode (both
orders), with `run_mode` and `converge` replaced by recorders, and the words
that make the mode run alone without being run themselves are the
modifiers. Then the REAL converge step, read out of collect.yml as it will
be live (`wfparse.effective_workflows`: a staged copy wins), is run under
bash with a stub `python` that records each call's argv, and:
  1. each modifier reaches `collect.py` in the SAME call as each mode, for
     every league, whatever order the words came in; the calls, handed back
     to `main()`, run exactly the modes asked for and converge nothing;
  2. a list with no modifier makes exactly the calls it always made, for
     every MODES list the routing table schedules, `converge`, and every
     other word `main()` names (the step must not swallow a mode);
  3. a failing call that carries a modifier still turns the run red.
A new modifier in `main()` fails (1) until the step passes it on.

⚠️ WHAT IT CANNOT SEE: a modifier `main()` builds from a string that is not
a constant in collect.py (a computed word); the dispatch form's own text
(the step is what runs); and the workflow file as DEPLOYED while an upload
is pending (it reads the staged copy; `runs_report` flags an upload left
too long).

# @vacuity 🔴🔴 the step handing a modifier to its own call again is caught (11-11's defect)
#   file: docs/upload/collect.yml
#   find: if ! python collect.py "$m" $MODE_ARGS; then
#   with: if ! python collect.py "$m"; then
#
# @vacuity 🔴 the step swallowing a real mode as a modifier is caught
#   file: docs/upload/collect.yml
#   find: converge-off) MODE_ARGS="$MODE_ARGS $_w" ;;
#   with: converge-off|news) MODE_ARGS="$MODE_ARGS $_w" ;;
#
# @vacuity 🔴 a NEW modifier in main() that the step does not know is caught
#   file: collect.py
#   find: args = [a for a in sys.argv[1:] if a]
#   with: args = [("converge-off" if a == "one-shot" else a) for a in sys.argv[1:] if a]
#
# @vacuity 🔴 a failing call that carries a modifier still turns the run red
#   file: docs/upload/collect.yml
#   find: echo "::error::mode '$m' failed for $LG on pass $PASS"
#   with: rc=0; pass_rc=0
"""
import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import wfparse as W                      # noqa: E402  the one workflow parser
from wfroutes import parse_arms          # noqa: E402
from tcheck import ck, eq, note, section  # noqa: E402

import collect as C                      # noqa: E402  asked, never run

SEP = "\x1f"


# ══════════════════════════════════════════════════════════════════════
section("0. 🔴 WHAT collect.py's main() DOES WITH A LIST OF WORDS")
# ══════════════════════════════════════════════════════════════════════
def main_does(argv):
    """{"run": [modes run alone], "converge": [explicit lists]} for one call.

    ⛔ Nothing runs: `run_mode` and `converge` are recorders, and every
    league is treated as one with a contract (every league has one today;
    a league without one runs every word alone, which hides a modifier)."""
    got = {"run": [], "converge": []}
    saved = (C.run_mode, C.converge, C._fresh.has_contract, sys.argv)

    def _conv(*a, **k):
        got["converge"].append(list(k.get("explicit") or (a[0] if a else None) or []))
        return 0

    C.run_mode = lambda m, *a, **k: got["run"].append(m)
    C.converge = _conv
    C._fresh.has_contract = lambda lg: True
    sys.argv = ["collect.py"] + list(argv)
    try:
        C.main()
    except SystemExit:
        pass
    finally:
        C.run_mode, C.converge, C._fresh.has_contract, sys.argv = saved
    return got


ALONE = {"run": ["card-fb"], "converge": []}
eq(main_does(["card-fb"]), {"run": [], "converge": [["card-fb"]]},
   "⚠️ the premise: a mode named on its own converges everything overdue "
   "(so a modifier lost from its call is a real difference)")
eq(main_does(["card-fb", "converge-off"]), ALONE,
   "⚠️ ...and with `converge-off` in the SAME argv it runs alone")

_tree = ast.parse(open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read())
_WORD = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
WORDS = sorted({n.value for n in ast.walk(_tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and _WORD.match(n.value)} - {"card-fb"})
MODIFIERS = [w for w in WORDS
             if main_does(["card-fb", w]) == ALONE or main_does([w, "card-fb"]) == ALONE]
_main = next(n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
MAIN_WORDS = sorted({n.value for n in ast.walk(_main)
                     if isinstance(n, ast.Constant) and isinstance(n.value, str)
                     and _WORD.match(n.value)})
ck(len(WORDS) > 100 and "converge-off" in MODIFIERS,
   "⚠️ the modifiers were found by asking main() (rule 67: an empty list "
   "would drive nothing)",
   "%d candidate words; modifiers %s" % (len(WORDS), MODIFIERS))
note("words main() itself names: %s; modifiers: %s" % (MAIN_WORDS, MODIFIERS))


# ══════════════════════════════════════════════════════════════════════
section("1. THE REAL STEP, AS IT WILL BE LIVE")
# ══════════════════════════════════════════════════════════════════════
WF = W.effective_workflows(ROOT).get("collect.yml")
SCRIPT = W.step_run(WF, step_id="collect") if WF else None
ck(bool(SCRIPT) and "$MODES" in SCRIPT and "collect.py" in SCRIPT,
   "the converge step's script is read out of %s"
   % os.path.relpath(WF or "?", ROOT).replace(os.sep, "/"),
   "%d chars" % len(SCRIPT or ""))

# The stub records each `collect.py` call: the league, then every argument,
# separated so "card-fb converge-off" as ONE argument and as two differ.
STUB = (
    '#!/bin/sh\n'
    'if [ "$1" = "collect.py" ]; then\n'
    '  shift\n'
    '  printf "%s" "${LEAGUE:-}" >> "$CALLS"\n'
    '  for a in "$@"; do printf "\\037%s" "$a" >> "$CALLS"; done\n'
    '  printf "\\n" >> "$CALLS"\n'
    '  [ -n "$FAIL_MODE" ] && [ "$1" = "$FAIL_MODE" ] && exit 1\n'
    'fi\n'
    'exit 0\n')


def drive(leagues, modes, fail_mode=""):
    """Run the real step. -> ([(league, argv)], rc line, stderr)."""
    tmp = tempfile.mkdtemp(prefix="mode-mods-")
    try:
        bin_ = os.path.join(tmp, "bin")
        os.makedirs(bin_)
        with open(os.path.join(bin_, "python"), "w", newline="\n") as fh:
            fh.write(STUB)
        with open(os.path.join(bin_, "git"), "w", newline="\n") as fh:
            fh.write("#!/bin/sh\nexit 0\n")
        for f in ("python", "git"):
            os.chmod(os.path.join(bin_, f), 0o755)
        log, out = os.path.join(tmp, "calls.log"), os.path.join(tmp, "gh_output")
        env = dict(os.environ, PATH=bin_ + os.pathsep + os.environ["PATH"],
                   CALLS=log, FAIL_MODE=fail_mode, LEAGUES=leagues,
                   LEAGUE=leagues.split()[0], MODES=modes, SEASON="2026",
                   LOOP_MINUTES="0", GITHUB_RUN_NUMBER="1", GITHUB_OUTPUT=out,
                   ODDS_API_KEY="", CFBD_API_KEY="")
        # ⚠️ FROM A FILE, NOT `bash -c`: on Windows a `bash -c` script past
        #    about 8K characters is cut short with no error.
        step = os.path.join(tmp, "step.sh")
        with open(step, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(SCRIPT)
        r = subprocess.run(["bash", step], cwd=tmp, env=env,
                           capture_output=True, text=True, timeout=120)
        calls = []
        if os.path.exists(log):
            for line in open(log, encoding="utf-8").read().splitlines():
                lg, *argv = line.split(SEP)
                calls.append((lg, argv))
        rc = open(out).read() if os.path.exists(out) else ""
        return calls, rc, r.stderr or ""
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def composed(calls, league):
    """What main() does across every call the step made for one league."""
    total = {"run": [], "converge": []}
    for lg, argv in calls:
        if lg == league:
            got = main_does(argv)
            total["run"] += got["run"]
            total["converge"] += got["converge"]
    return total


# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 EVERY MODIFIER REACHES collect.py IN THE SAME CALL AS EACH MODE")
# ══════════════════════════════════════════════════════════════════════
for w in MODIFIERS:
    _c, _rc, _err = drive("ncaaf", "card-fb %s" % w)
    eq(_c, [("ncaaf", ["card-fb", w])],
       "🔴🔴 \"card-fb %s\": collect.py receives `card-fb %s` in ONE call" % (w, w))
    eq(composed(_c, "ncaaf"), ALONE,
       "🔴🔴 ...so main() runs card-fb ALONE and converges nothing")
    ck("rc=0" in _rc, "   ...and the run is clean", (_rc.strip() or _err[-300:]))

    _c, _rc, _err = drive("ncaaf", "%s nfl-logs" % w)
    eq(_c, [("ncaaf", ["nfl-logs", w])],
       "🔴 \"%s nfl-logs\": the word order does not matter" % w)

    _c, _rc, _err = drive("ncaaf nfl", "news card-fb %s" % w)
    eq(_c, [("ncaaf", ["news", w]), ("ncaaf", ["card-fb", w]),
            ("nfl", ["news", w]), ("nfl", ["card-fb", w])],
       "🔴 \"news card-fb %s\" for two leagues: every mode, every league, each "
       "call carrying the modifier" % w)
    for lg in ("ncaaf", "nfl"):
        eq(composed(_c, lg), {"run": ["news", "card-fb"], "converge": []},
           "   ...and main() runs exactly news and card-fb for %s, nothing "
           "converged" % lg)
    ck(not [a for _lg, a in _c if a and a[0] in MODIFIERS],
       "⛔ no call names a modifier where its mode belongs", "%r" % _c)


# ══════════════════════════════════════════════════════════════════════
section("3. A LIST WITH NO MODIFIER MAKES EXACTLY THE CALLS IT ALWAYS MADE")
# ══════════════════════════════════════════════════════════════════════
_routed = sorted({m for _cron, _lg, m in parse_arms(open(WF, encoding="utf-8").read())})
ck(len(_routed) >= 5, "⚠️ the routing table's MODES lists were read (rule 67)",
   "%r" % _routed)
_plain = _routed + ["converge"] + ["card-fb %s" % w for w in MAIN_WORDS
                                   if w not in MODIFIERS]
_bad = []
for modes in _plain:
    _c, _rc, _err = drive("ncaaf", modes)
    want = [("ncaaf", [m]) for m in modes.split()]
    if _c != want or "rc=0" not in _rc:
        _bad.append("%r -> %r (%s)" % (modes, _c, _rc.strip() or _err[-200:]))
ck(not _bad, "🔴 every scheduled MODES list, `converge`, and every other word "
   "main() names is run as its own mode, one call each, nothing added",
   "%d lists driven%s" % (len(_plain), "".join("\n       " + b for b in _bad)))


# ══════════════════════════════════════════════════════════════════════
section("4. A FAILING CALL THAT CARRIES A MODIFIER STILL TURNS THE RUN RED")
# ══════════════════════════════════════════════════════════════════════
for w in MODIFIERS:
    _c, _rc, _err = drive("ncaaf nfl", "card-fb %s" % w, fail_mode="card-fb")
    eq([a for _lg, a in _c], [["card-fb", w], ["card-fb", w]],
       "nfl still runs after ncaaf's \"card-fb %s\" failed" % w)
    ck("rc=1" in _rc, "🔴 ...and the step reports the failure (rc=1)",
       _rc.strip() or _err[-300:])
