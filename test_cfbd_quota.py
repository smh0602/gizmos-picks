#!/usr/bin/env python3
"""THE CFBD QUOTA MUST BE MEASURED, NOT ASSUMED — AND THE PLAN IS AN
ACCOUNT FACT, NOT A CONSTANT.

🔴🔴 WHAT WENT WRONG. `cfbd_budget.py` reads `CFBD_PLAN` from the
environment with a `1000` default and **no workflow set it**
(`grep -rn CFBD_PLAN .github/workflows/` returned nothing). So every
scheduled run printed *"906/month against a 1000 plan — 91%"* against a
plan that does not exist. The real tier is 3,000 and the same 906 is 30%.
⛔ The urgency was manufactured by a default nobody set.

🔴 AND OUR OWN DATA HAD ALREADY RULED 1000 OUT. A reading of **2,236
remaining** is not reachable on a 1,000/month plan, and it sat in
`data/ncaaf/latest/schedule-probe-2026.json` the whole time while the
tier was asked for five times. ➡️ Before asking for a fact, grep the
artifacts for it.

⛔ AND THE HEADER WAS BEING THROWN AWAY. `_record_quota()` has captured
it on every response — **including 429s** — since the module was written,
and `quota_report()` has returned it; it was only written into a couple
of PROBE artifacts, so all of history holds **two** readings. Two points
are a line, not a trend, and our own `calls_made` could not be
differenced against them because none of those artifacts is timestamped
inside it.

══════════════════════════════════════════════════════════════════════
⚠️ SO THIS FILE ASKS FOUR THINGS, AND NONE OF THEM COSTS A CALL
══════════════════════════════════════════════════════════════════════
  1. every workflow that runs the costing sets the plan — DERIVED from
     the workflow files, so the next one cannot inherit `1000`;
  2. every mode that can call CFBD records what it cost — DERIVED from
     `collect.py`, so the next mode cannot ship blind;
  3. a run that called nothing still records, and CFBD's silence
     survives into the artifact as a finding about CFBD;
  4. the plan is INFERRED from a reset when one has been seen, and
     reported UNKNOWN when it has not. ⛔ A plan invented from a partial
     series is exactly the mistake `1000` was.

⚠️ No network, no credits.
"""
import ast
import glob
import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section

import cfb
import cfbd_budget as B


# ══════════════════════════════════════════════════════════════════════
# @vacuity the quota block must be recorded on every CFBD-capable run
#   file: collect.py
#   find:             _cfbmod.record_quota(DATA, log)
#   with:             pass
# ══════════════════════════════════════════════════════════════════════

_WF = os.path.join(ROOT, ".github", "workflows")


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 EVERY WORKFLOW THAT PRICES CFBD SETS THE PLAN")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ DERIVED, NEVER LISTED. A hardcoded list is how the next workflow to
#    call this silently inherits the `1000` default and the false alarm
#    comes back.
# ⛔ AND IT FOLLOWS THE INDIRECTION: `cfbd.yml` does not name
#    `cfbd_budget.py`, it runs `cfbd_watch.py`, which runs the costing.
#    A check that only looked for the direct name would have found
#    nothing and passed.
# ⛔ A FILE THAT MENTIONS IT IS NOT A FILE THAT RUNS IT. A substring
#    scan pulled in `collect.py`, `vacuity.py`, `watchdog.py` and
#    `cfb.py` — every one of which only names `cfbd_budget.py` in PROSE —
#    and then flagged `collect.yml` and `vacuity.yml` for not setting a
#    plan they never read. ✅ Read the AST and require an actual CALL.
_RUNNERS = {"cfbd_budget.py"}
for _f in glob.glob(os.path.join(ROOT, "*.py")):
    if os.path.basename(_f).startswith("test_"):
        continue
    try:
        _tree = ast.parse(io.open(_f, encoding="utf-8").read())
    except Exception:
        continue
    if any("cfbd_budget" in ast.unparse(_n)
           for _n in ast.walk(_tree) if isinstance(_n, ast.Call)):
        _RUNNERS.add(os.path.basename(_f))

_uses = {}
for _f in sorted(glob.glob(os.path.join(_WF, "*.yml"))):
    _y = io.open(_f, encoding="utf-8").read()
    # ⛔ A COMMENT IS NOT A CALL. `cfbd.yml`'s header discusses
    #    `cfbd_budget.py` at length and runs `cfbd_watch.py`.
    _code = "\n".join(l for l in _y.split("\n") if not l.strip().startswith("#"))
    if any(("python %s" % r) in _code or ("python3 %s" % r) in _code
           for r in _RUNNERS):
        _uses[os.path.basename(_f)] = _y

ck("⚠️ the workflows that price CFBD were found",
   bool(_uses),
   "⛔ an empty set makes the check below pass having asked nothing — "
   "rule 67. runners=%s" % sorted(_RUNNERS))
for _name, _y in sorted(_uses.items()):
    ck("🔴 %s sets CFBD_PLAN" % _name,
       "CFBD_PLAN:" in _y,
       "⛔ without it `cfbd_budget.py` falls back to its `1000` default "
       "and prints 91%% against a plan that does not exist. ✅ The "
       "default STAYS as the 'nobody told me' value — a plan size is an "
       "account fact and does not belong in code.")
ck("⛔ ...and the 1000 default is still in the code, unchanged",
   'os.environ.get("CFBD_PLAN", "1000")' in io.open(
       os.path.join(ROOT, "cfbd_budget.py"), encoding="utf-8").read(),
   "🔴 moving the real number into the module would put an account fact "
   "back in a file, which is the defect — not the wrong default")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 EVERY MODE THAT CAN CALL CFBD RECORDS WHAT IT COST")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ DERIVED FROM `collect.py` ITSELF: anything that can reach CFBD must
#    import `cfb`, so the arms that import it ARE the set. ⛔ A list
#    typed here is how the next mode ships blind.
_CT = ast.parse(io.open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read())
_RUN = [n for n in ast.walk(_CT)
        if isinstance(n, ast.FunctionDef) and n.name == "run_mode"][0]
_cfb_modes = set()
for _n in ast.walk(_RUN):
    if isinstance(_n, ast.If) and ast.unparse(_n.test).startswith("mode == "):
        if "import cfb" in " ".join(ast.unparse(x) for x in _n.body):
            _cfb_modes.add(ast.unparse(_n.test).split("==")[1].strip().strip("'\""))

ck("⚠️ the CFBD-calling modes were derived from collect.py",
   len(_cfb_modes) >= 3,
   "⛔ rule 67 — an empty set proves nothing. found %s" % sorted(_cfb_modes))
note("modes whose arm imports cfb: %s" % sorted(_cfb_modes))

# 🔴 ONE CHOKE POINT COVERS THEM ALL, and it must be in a `finally`.
_try = [n for n in _RUN.body if isinstance(n, ast.Try)]
_final = " ".join(ast.unparse(x) for t in _try for x in t.finalbody)
ck("🔴🔴 the recorder runs in run_mode's `finally`",
   "record_quota" in _final,
   "⛔ ON THE SUCCESS PATH IT WOULD MISS THE 429s, which is the one "
   "reading that explains a dead run — and `_record_quota` captures the "
   "header on a 429 too. finalbody=%r" % _final[:120])
ck("⚠️ ...and it is reached by asking whether `cfb` LOADED, not by a list",
   "sys.modules.get(\"cfb\")" in _final or "sys.modules.get('cfb')" in _final,
   "⛔ a mode list in the collector is a second place to keep in step "
   "with the one in this test. Anything that can call CFBD must import "
   "`cfb`, so that IS the question. finalbody=%r" % _final[:160])
ck("⛔ ...and it is gated on the DESTINATION, not the league",
   # ⚠️ `ast.unparse` NORMALISES QUOTES — it emits `'ncaaf'` whatever the
   #    source wrote. Matching on a quoted literal is matching on the
   #    unparser's taste, not on the code.
   "os.path.basename(DATA.rstrip" in _final and "ncaaf" in _final,
   "🔴 `DATA` decides where the bytes land and `LEAGUE` is a second "
   "source for that fact — they disagreed once already and a test wrote "
   "the product into MLB's tree")

# ══════════════════════════════════════════════════════════════════════
section("3. ⛔ A RUN THAT CALLED NOTHING STILL RECORDS")
# ══════════════════════════════════════════════════════════════════════
# 🔴 AN ABSENT BLOCK IS INDISTINGUISHABLE FROM A RUN THAT NEVER HAPPENED.
_d = tempfile.mkdtemp(prefix="cfbdq-")
try:
    _doc = cfb.record_quota(_d, log=lambda *a, **k: None)
    _latest = json.load(io.open(os.path.join(_d, "latest", "cfbd-quota.json"),
                                encoding="utf-8"))
    _dated = glob.glob(os.path.join(_d, "*", "cfbd-quota", "*.json.gz"))
finally:
    shutil.rmtree(_d, ignore_errors=True)

ck("⛔ a zero-call run writes the block anyway",
   _latest.get("calls_made") == 0,
   "🔴 an absent block reads as 'no run', and a run that called nothing "
   "is a different fact. got %r" % _latest.get("calls_made"))
ck("🔴 ...and `quota_headers_seen: false` SURVIVES into the artifact",
   _latest.get("quota", {}).get("quota_headers_seen") is False,
   "⛔ 'CFBD sent no quota header' is a finding ABOUT CFBD — `cfb.py`'s "
   "own docstring says so — not an absence to drop. got %r"
   % _latest.get("quota"))
ck("🔴 ...and it carries its OWN timestamp",
   isinstance(_latest.get("recorded_at"), str)
   and _latest["recorded_at"].endswith("Z"),
   "⛔ THE GAP THAT MADE THE TWO HISTORICAL READINGS UNUSABLE. A reading "
   "with no time on it cannot be differenced against the next one. got "
   "%r" % _latest.get("recorded_at"))
ck("⚠️ ...and a DATED copy is archived beside it",
   len(_dated) == 1,
   "⛔ `latest/` is overwritten every run, so a series that lives only "
   "there holds exactly one point — which is how all of history came to "
   "hold two. got %s" % _dated)
ck("⛔ ...and `calls_made` and the quota sit in the SAME document",
   "calls_made" in _latest and "quota" in _latest,
   "🔴 our count and CFBD's only mean something together — that is the "
   "difference between a gap and an answer")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE PLAN IS INFERRED FROM A RESET, OR REPORTED UNKNOWN")
# ══════════════════════════════════════════════════════════════════════
def _series(vals):
    """A synthetic tree of readings. -> measured_plan() over it."""
    d = tempfile.mkdtemp(prefix="cfbdplan-")
    try:
        for i, v in enumerate(vals):
            doc = {"kind": "DIAGNOSTIC", "calls_made": 1,
                   "recorded_at": "2026-09-%02dT00:00:00Z" % (i + 1),
                   "quota": {"quota_headers_seen": True,
                             "headers": {"X-CallLimit-Remaining": str(v)},
                             "checked_at": "2026-09-%02dT00:00:00Z" % (i + 1)}}
            p = os.path.join(d, "2026-09-%02d" % (i + 1), "cfbd-quota")
            os.makedirs(p, exist_ok=True)
            with gzip.open(os.path.join(p, "0100.json.gz"), "wt",
                           encoding="utf-8") as fh:
                json.dump(doc, fh)
        return B.measured_plan(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)


_reset = _series([2800, 2400, 2100, 2950, 2700])     # spans a reset
_noreset = _series([2800, 2400, 2100, 1900])         # only ever falls

ck("⚠️ both synthetic series were read",
   _reset["readings"] == 5 and _noreset["readings"] == 4,
   "⛔ rule 67. reset=%s noreset=%s"
   % (_reset["readings"], _noreset["readings"]))
ck("🔴🔴 a series spanning a RESET infers the plan floor",
   _reset["resets"] == 1 and _reset["floor"] == 2950,
   "⛔ the ceiling is the value the header returns to. resets=%s floor=%s"
   % (_reset["resets"], _reset["floor"]))
ck("🔴🔴 a series with NO reset reports UNKNOWN rather than guessing",
   _noreset["resets"] == 0 and _noreset["floor"] is None
   and "no reset" in _noreset["why"],
   "⛔ A PLAN INVENTED FROM A PARTIAL SERIES IS THE DEFECT THIS "
   "REPLACES. `1000` was exactly that. got resets=%s floor=%s why=%r"
   % (_noreset["resets"], _noreset["floor"], _noreset["why"][:70]))
ck("⚠️ ...and the floor is labelled a floor, never a plan size",
   "floor" in _reset and "plan" not in [k for k in _reset if k == "plan"],
   "🔴 the reading after a reset has already had this month's first "
   "calls taken out of it, so it bounds the ceiling from below and "
   "nothing more. keys=%s" % sorted(_reset))

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴🔴 A READING ABOVE THE PLAN PROVES THE PLAN WRONG")
# ══════════════════════════════════════════════════════════════════════
# 🔴 THE CHECK THAT WOULD HAVE ANSWERED THIS WITHOUT ASKING SAM. You
#    cannot have more calls left than the plan holds, and 2,236 remaining
#    sat on disk for the whole of September.
# ⛔ AGAINST A SYNTHETIC RECORD, NEVER THE LIVE TREE. The live tree holds
#    no quota reading yet — `cfbd_budget.py` deliberately does NOT read
#    the probe artifacts that carry the two historical ones, because
#    `test_coaches_probe.py` refuses a probe becoming a product input and
#    that ceiling stays at zero. A check asserted on live data would also
#    go red the day the data moved, which is nobody's defect.
def _tree(vals):
    d = tempfile.mkdtemp(prefix="cfbdbud-")
    for i, v in enumerate(vals):
        doc = {"kind": "DIAGNOSTIC", "calls_made": 1,
               "recorded_at": "2026-09-%02dT00:00:00Z" % (i + 1),
               "quota": {"quota_headers_seen": True,
                         "headers": {"X-CallLimit-Remaining": str(v)},
                         "checked_at": "2026-09-%02dT00:00:00Z" % (i + 1)}}
        pth = os.path.join(d, "2026-09-%02d" % (i + 1), "cfbd-quota")
        os.makedirs(pth, exist_ok=True)
        with gzip.open(os.path.join(pth, "0100.json.gz"), "wt",
                       encoding="utf-8") as fh:
            json.dump(doc, fh)
    return d


def _budget(plan, data):
    env = dict(os.environ, CFBD_PLAN=str(plan), CFBD_DATA=data)
    return subprocess.run([sys.executable, "cfbd_budget.py"], cwd=ROOT,
                          capture_output=True, text=True, env=env).stdout


# the real readings, as evidence: 2374 then 2236
_T = _tree([2374, 2236])
try:
    _wrong, _right = _budget(1000, _T), _budget(3000, _T)
finally:
    shutil.rmtree(_T, ignore_errors=True)
ck("🔴🔴 a 1000 plan is CONTRADICTED by the stored readings",
   "THE CONFIGURED PLAN IS WRONG" in _wrong,
   "⛔ 2,374 remaining is not reachable on a 1,000/month plan, and that "
   "reading was on disk the whole time the tier was being asked about. "
   "output tail: %r" % _wrong[-200:])
ck("✅ ...and the real plan raises no contradiction",
   "THE CONFIGURED PLAN IS WRONG" not in _right,
   "⛔ a detector that fires on the correct value is the other failure. "
   "output tail: %r" % _right[-200:])
ck("⚠️ ...and the measured block is printed either way",
   "MEASURED" in _wrong and "MEASURED" in _right,
   "⛔ the readings are the evidence; printing them only when they "
   "disagree would hide the basis of the agreement")
ck("✅ the real plan reads 30%, not 91%",
   "against a 3000 plan — 30%" in _right
   and "against a 1000 plan — 91%" in _wrong,
   "⛔ the same 906 calls. The urgency was manufactured by a default "
   "nobody set.")
