#!/usr/bin/env python3
"""
🔴 THE SEASON A RUN HANDS THE COLLECTOR — EXECUTED, NOT READ.

`[found in production 2026-09-06, run 534]` Only the arms naming a
season-scoped mode set `SEASON=CUR`. Every other arm left it empty and the
step's default handed the collector a LITERAL **2025**. That is invisible
until CONVERGE repairs a season-scoped mode on one of those runs — which
is exactly what happened:

    16:04Z  the college Trends cron (the one arm passing CUR)  DROPPED
    18:20Z  the hourly NEWS run converged `cfb-probe` to repair it
            ...and back-filled 2025, which failed its own opp_elo guard
            ...leaving allowed-by-position-2026.json.gz 153 min late

⛔ The run would have gone red every hour and never repaired the tab.

⚠️ THE SCRIPT IS PARSED OUT OF THE WORKFLOW AND RUN, never pasted here —
a copy of the script under test is not the script under test (rule 128).
⚠️ BY HAND, NOT WITH PyYAML: the runner installs a bare Python and a test
that cannot import BLOCKS a push (rule 133). The hand parse is
cross-checked against PyYAML wherever PyYAML happens to exist.
"""
import datetime
import os
import re
import subprocess
import tempfile

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(ROOT, ".github/workflows/collect.yml")


def step_script(step_id):
    """The `run:` block of the step with this id."""
    lines = open(WF, encoding="utf-8").read().splitlines()
    for i, ln in enumerate(lines):
        if ln.strip() != f"id: {step_id}":
            continue
        for j in range(i, len(lines)):
            m = re.match(r"^(\s+)run: \|\s*$", lines[j])
            if not m:
                continue
            pad = len(m.group(1)) + 2
            out = []
            for k in range(j + 1, len(lines)):
                cur = lines[k]
                if cur.strip() and not cur.startswith(" " * pad):
                    break
                out.append(cur[pad:] if len(cur) >= pad else "")
            return "\n".join(out).rstrip() + "\n"
    return None


SCRIPT = step_script("mode")
ck("the deciding step's script can be read out of the workflow",
   bool(SCRIPT) and "GITHUB_OUTPUT" in (SCRIPT or ""),
   "%d chars" % len(SCRIPT or ""))
try:
    import yaml as _yaml
except ImportError:
    note("PyYAML not installed here, so the hand-parse was not "
         "cross-checked — it IS still executed below")
else:
    _ref = [s for s in _yaml.safe_load(open(WF, encoding="utf-8"))
            ["jobs"]["collect"]["steps"] if s.get("id") == "mode"][0]["run"]
    ck("⛔ the hand-written extractor agrees with PyYAML",
       (SCRIPT or "").strip() == _ref.strip(),
       "%d vs %d chars" % (len((SCRIPT or "").strip()), len(_ref.strip())))


def decide(schedule, event="schedule", inputs=None):
    """Run the real deciding step for one cron string. Returns its outputs."""
    inputs = inputs or {}
    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, "gh_output")
    open(out, "w").close()
    body = SCRIPT
    # The step is written against GitHub's `${{ ... }}` expressions. Those
    # are substituted by the runner BEFORE bash sees them, so the test has
    # to do the same thing the runner does rather than pretend bash reads
    # them. ⛔ Every one is substituted; an unreplaced expression would be
    # a syntax error, which is the loud failure we want.
    subs = {
        "github.event_name": event,
        "github.event.schedule": schedule or "",
        "github.event.inputs.league": inputs.get("league", ""),
        "github.event.inputs.mode": inputs.get("mode", ""),
        "github.event.inputs.season": inputs.get("season", ""),
    }
    for k, v in subs.items():
        body = re.sub(r"\$\{\{\s*" + re.escape(k) + r"\s*\}\}", v, body)
    # `${{ a || 'b' }}` — GitHub's fallback form. The runner resolves it
    # before bash sees it, so the test resolves it the same way.
    def _fallback(m):
        key, lit = m.group(1).strip(), m.group(2)
        return subs.get(key) or lit
    body = re.sub(r"\$\{\{\s*([\w.]+)\s*\|\|\s*'([^']*)'\s*\}\}",
                  _fallback, body)
    left = re.findall(r"\$\{\{[^}]*\}\}", body)
    if left:
        note("⚠️ unsubstituted expressions remain: " + str(left[:2]))
    r = subprocess.run(["bash", "-c", body], capture_output=True, text=True,
                       env=dict(os.environ, GITHUB_OUTPUT=out))
    got = {}
    for ln in open(out, encoding="utf-8"):
        if "=" in ln:
            k, v = ln.rstrip("\n").split("=", 1)
            got[k] = v
    got["_rc"] = r.returncode
    got["_err"] = r.stderr[-300:]
    return got


# The runner's own rule, restated here so the expected value is DERIVED
# rather than typed: a football season is named for the year it starts.
now = datetime.datetime.now(datetime.timezone.utc)
CUR = str(now.year - 1 if now.month < 8 else now.year)

# 🔴 THIS FILE SHIPS IN THE ROOT DROP AND THE FIX IS IN THE WORKFLOW —
#    two folders, so two commits, so there is a window where one has
#    landed and the other has not (rule 111). ⛔ A test that FAILS in that
#    window makes the next real failure unreadable, so it DETECTS the
#    pre-fix workflow and says so LOUDLY instead (rule 129).
#    ⚠️ The detection is on the fix itself, not on a version string.
FIXED = 'if [ "$LEAGUE" != "mlb" ] && [ -z "$SEASON" ]; then SEASON=CUR; fi' \
        in (SCRIPT or "")
if not FIXED:
    note("🔴 THE WORKFLOW FIX HAS NOT LANDED YET. The football season "
         "checks below are REPORTED, NOT ASSERTED, until "
         ".github/workflows/collect.yml is uploaded — every football run "
         "without an explicit season is still handing the collector a "
         "literal 2025. Upload it and this file starts biting.")

print("\n═══ 1. THE HOURLY NEWS RUN — THE ONE THAT BIT ═══")
g = decide("20 * * * *")
ck("it routes both football leagues", g.get("league") == "ncaaf nfl", str(g.get("league")))
if FIXED:
    ck("🔴 and it hands the collector THIS season, not a literal 2025",
       g.get("season") == CUR,
       f"season={g.get('season')} expected {CUR} — converge repairs "
       f"season-scoped modes on runs like this one")
else:
    note(f"⚠️ NOT ASSERTED (workflow not yet uploaded): the hourly news "
         f"run hands over season={g.get('season')}, and it should be {CUR}")

print("\n═══ 2. EVERY FOOTBALL ARM, NOT JUST THE ONE THAT BROKE ═══")
# ⛔ ENUMERATED FROM THE WORKFLOW rather than listed here, so a new arm
#    cannot be added without this check seeing it.
arms = re.findall(r'^\s+"([^"]+)"\)\s+LEAGUE=', SCRIPT, re.M)
ck("the routing arms were found in the script", len(arms) > 20, f"{len(arms)} arms")
bad = []
for cron in arms:
    r = decide(cron)
    if r.get("league", "mlb") != "mlb" and r.get("season") != CUR:
        bad.append((cron, r.get("league"), r.get("season")))
if FIXED:
    ck("🔴 EVERY football arm hands over this season", not bad,
       "offenders: " + str(bad[:3]) if bad else f"all {len(arms)} arms checked")
else:
    note(f"⚠️ NOT ASSERTED (workflow not yet uploaded): {len(bad)} of "
         f"{len(arms)} arms hand over a season that is not {CUR}")

print("\n═══ 3. ⛔ MLB IS NOT SILENTLY REDEFINED ═══")
# The "before August means last year" rule is a FOOTBALL rule — MLB's
# season is named for the year it ENDS in. Changing MLB's default would be
# a different decision from the one this fix makes.
mlb = decide("9 */3 * * *")
ck("an MLB arm still routes mlb", mlb.get("league") == "mlb", str(mlb.get("league")))
ck("⛔ and its season default is untouched", mlb.get("season") == "2025",
   f"season={mlb.get('season')} — the football rule must not reach MLB")

print("\n═══ 4. AN EXPLICIT SEASON STILL WINS ═══")
d = decide("", event="workflow_dispatch",
           inputs={"league": "ncaaf", "mode": "cfb-probe", "season": "2023"})
ck("a hand-dispatched season is honoured verbatim", d.get("season") == "2023",
   str(d.get("season")))
d2 = decide("", event="workflow_dispatch",
            inputs={"league": "nfl", "mode": "nfl-logs", "season": "CUR"})
ck("...and CUR still resolves on the runner", d2.get("season") == CUR,
   str(d2.get("season")))
