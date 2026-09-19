#!/usr/bin/env python3
"""🔴 A WATCHER MAY NOT STATE A FACT IT CANNOT SEE.

`[measured 2026-09-19]` two watcher bodies carried this, as a literal:

    calibration.py:168   "...a MONEY finding, not a pipeline one —
                          every job is green."
    budget_watch.py:258  "...not a pipeline one — every job is green
                          and every cap is holding."

`calibration.py` reads `record.json`. `budget_watch.py` reads
`budget.py`'s output and the stored credit readings. **Neither has ever
been able to see a workflow run.** Both printed that sentence into live
issues (#16, #31) while `collect.yml` was red on 68 consecutive runs and
had not been green for 32 hours.

⛔ Rule 166/293: a status written down is a claim about the world, and
it goes stale — or, as here, was never true. The DISTINCTION those
sentences were drawing is real and worth keeping ("this is about the
money, not the plumbing"); what is gone is the part that asserted
somebody else's health.

✅ THE RULE: a module whose stdout becomes an issue body may only claim
the state of the workflow runs if it can read them — which in this repo
means `runs_report`. The list of such modules is DERIVED from the
workflows, never typed here, so a watcher added tomorrow is covered.

# @vacuity 🔴 a watcher claiming green without reading the runs is caught
#   file: calibration.py
#   find:                    "the board DELIVERS against what it printed, not "
#   with:                    "the board DELIVERS — every job is green, not "
"""
import ast
import glob
import io
import os
import re

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
WF = sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")))

# ⛔ The claim shapes. Each is about ANOTHER subsystem's health — the one
#    thing a watcher reading its own artifact cannot know.
CLAIMS = re.compile(
    r"every (job|run|workflow)\w* (is|are) green"
    r"|(jobs|runs|workflows) are green"
    r"|nothing is failing"
    r"|every job is green"
    r"|the pipeline is (fine|green|healthy)",
    re.I)
SEES_RUNS = ("runs_report",)


def body_producers():
    """{module: [workflows]} for every `python X.py > /tmp/*.md`."""
    out = {}
    for f in WF:
        src = io.open(f, encoding="utf-8").read()
        for m in re.finditer(r"python3?\s+([a-z_0-9]+)\.py[^\n]*>\s*/tmp/[^\s]+\.md", src):
            out.setdefault(m.group(1) + ".py", []).append(os.path.basename(f))
    return out


def literals(path):
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    return [(n.value, getattr(n, "lineno", 0)) for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def imports(path):
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    got = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            got |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            got.add(n.module.split(".")[0])
    return got


PROD = body_producers()

# ════════════════════════════════════════════════════════════════════════
section("1. 🔴 THE WATCHERS ARE DERIVED FROM THE WORKFLOWS")
# ════════════════════════════════════════════════════════════════════════
note("modules whose stdout becomes an issue body: %s"
     % {k: v for k, v in sorted(PROD.items())})
ck("⚠️ the derivation found the watchers",
   len(PROD) >= 4,
   "⛔ a hardcoded list goes stale the first time a watcher is added — "
   "and a new watcher is the one most likely to repeat this. found %s"
   % sorted(PROD))
ck("⚠️ ...including the two that carried the claim",
   "calibration.py" in PROD and "budget_watch.py" in PROD,
   "⛔ rule 67: if the derivation misses them, the check below judges "
   "nothing. found %s" % sorted(PROD))

# ════════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 AND NONE OF THEM CLAIMS A HEALTH IT CANNOT READ")
# ════════════════════════════════════════════════════════════════════════
offenders, scanned = [], 0
for mod in sorted(PROD):
    p = os.path.join(ROOT, mod)
    if not os.path.exists(p):               # pragma: no cover
        continue
    can_see = bool(imports(p) & set(SEES_RUNS))
    for text, line in literals(p):
        scanned += 1
        m = CLAIMS.search(text)
        if m and not can_see:
            offenders.append("%s:%d says %r and reads no run status"
                             % (mod, line, m.group(0)))
ck("⚠️ there were strings to scan",
   scanned >= 200,
   "⛔ rule 67 — an AST walk that returns nothing makes this green on "
   "an empty set. scanned=%d" % scanned)
ck("🔴🔴 no watcher asserts the health of the jobs",
   not offenders,
   "⛔ `calibration.py` printed 'every job is green' into issue #16 "
   "while collect.yml was red on 68 consecutive runs. A watcher that "
   "is wrong about the thing it is not measuring teaches the reader to "
   "discount the thing it IS measuring. %s"
   % ("; ".join(offenders) or "none"))

# ⚠️ AND THE ONE MODULE THAT MAY SAY IT, MAY STILL SAY IT.
runs = os.path.join(ROOT, "runs_report.py")
ck("✅ `runs_report.py` is exempt because it READS the runs",
   os.path.exists(runs) and (
       "runs_report" in SEES_RUNS),
   "⛔ the rule is 'measure it or drop it', never 'never say it'. The "
   "module that collects run conclusions is the one allowed to report "
   "on them, and runs.yml's own close message still does.")
ck("⛔ ...and the pattern would have caught the real sentences",
   bool(CLAIMS.search("This is a MONEY finding, not a pipeline one — "
                      "every job is green."))
   and bool(CLAIMS.search("every job is green and every cap is holding")),
   "🔴 a matcher that does not match the defect it was written for is "
   "the emptiest kind of guard (rule 244).")
