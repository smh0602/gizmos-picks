#!/usr/bin/env python3
"""🔴🔴 A RUN CAN BE RED FOR TWO REASONS AND MUST NAME BOTH.

`[measured 2026-09-19]` `collect.yml` ends with two gates:

    1194  - name: Fail if the tests failed      if: tests.rc != '0' …
    1200  - name: Fail if any pass failed       if: collect.rc != '0'

A step that `exit 1`s makes GitHub skip every later step that does not
say otherwise. So from the moment the suite went red — 2026-09-17T23:27,
and it has not been green since — **the converge gate has been skipped
on every single run**, and a collector failure could not reach the
Actions page at all. Confirmed on job 105631080959, where both gates
read `skipped`.

⛔ WHAT WAS HIDING IN THERE. nflverse answered `403 rate limit exceeded`
on every NFL pass for 47 hours. `players-2026.json.gz` held week 1 while
the schedule already recorded finals for weeks 1 and 2, and the NFL
possession artifact had never been written. The run was already red for
the tests, so nothing said so. I set out to group 68 red runs by failing
step and could not — because the log does not say.

✅ `!cancelled()` makes each gate run on its own merits.
⚠️ NOT `always()`: a CANCELLED run is the DESIGNED outcome for every
MLB-group heartbeat — 17 of them in the 29-hour audit window — and
neither gate should annotate one.

⛔ THIS FILE DOES NOT READ THE CONDITIONS, IT EVALUATES THEM. A check
that greps for `!cancelled()` is a check asserting its own prose
(rule 249). The expressions are parsed and run against a state matrix.

# @vacuity 🔴🔴 a gate that cannot be reached past the first is caught
#   file: .github/workflows/collect.yml
#   find:         if: ${{ !cancelled() && steps.collect.outputs.rc != '0' }}
#   with:         if: steps.collect.outputs.rc != '0'
#
# @vacuity 🔴 ...and a gate that fires on a cancelled run is caught too
#   file: .github/workflows/collect.yml
#   find:         if: ${{ !cancelled() && steps.tests.outputs.rc != '0' && steps.tests.outputs.rc != '' }}
#   with:         if: ${{ always() && steps.tests.outputs.rc != '0' && steps.tests.outputs.rc != '' }}
"""
import os
import re
import subprocess
import tempfile

import wfparse as W
from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(ROOT, ".github", "workflows", "collect.yml")
STEPS = W.steps(WF, "collect")
GATES = [s for s in STEPS if (s.name or "").startswith("Fail if")]


def evaluate(expr, outputs, cancelled=False, failed=False):
    """A tiny evaluator for the GitHub expression subset these gates use.

    Supports `${{ }}` wrapping, `!cancelled()`, `always()`, `success()`,
    `failure()`, `&&`, `||`, `!=`, `==` and single-quoted literals.
    ⛔ It raises on anything else rather than guessing — a silently
    mis-evaluated condition would make this whole file lie.
    """
    e = expr.strip()
    m = re.fullmatch(r"\$\{\{(.*)\}\}", e, re.S)
    if m:
        e = m.group(1).strip()

    def atom(tok):
        tok = tok.strip()
        if tok == "!cancelled()":
            return not cancelled
        if tok == "cancelled()":
            return cancelled
        if tok == "always()":
            return True
        if tok == "success()":
            return not failed and not cancelled
        if tok == "failure()":
            return failed
        cmp_ = re.fullmatch(r"(\S+)\s*(!=|==)\s*'([^']*)'", tok)
        if cmp_:
            ref, op, lit = cmp_.groups()
            k = re.fullmatch(r"steps\.([A-Za-z0-9_-]+)\.outputs\.([A-Za-z0-9_-]+)",
                             ref)
            if not k:
                raise ValueError("unsupported reference %r" % ref)
            val = outputs.get(k.group(1), {}).get(k.group(2), "")
            return (val != lit) if op == "!=" else (val == lit)
        raise ValueError("unsupported token %r" % tok)

    # `&&` binds tighter than `||`, which is all these gates need
    return any(all(atom(t) for t in part.split("&&"))
               for part in e.split("||"))


# ════════════════════════════════════════════════════════════════════════
section("1. 🔴 THE GATES ARE FOUND, AND THERE IS MORE THAN ONE")
# ════════════════════════════════════════════════════════════════════════
note("terminal gates: %s" % [(g.name, g.cond) for g in GATES])
ck("⚠️ both gates were read out of the deployed workflow",
   len(GATES) == 2 and all(g.cond for g in GATES),
   "⛔ rule 67 — with fewer than two there is nothing to prove about "
   "one hiding the other. found %s" % [(g.name, bool(g.cond)) for g in GATES])
ck("⚠️ ...and each still exits non-zero",
   all("exit 1" in (g.run or "") for g in GATES),
   "⛔ a gate that reports and passes is not a gate.")
_refused = False
try:
    evaluate("github.event_name == 'push'", {})
except ValueError:
    _refused = True
ck("⛔ the evaluator refuses what it does not understand",
   _refused,
   "🔴 an evaluator that silently returns False on a token it cannot "
   "read would make every row of the matrix below pass for the wrong "
   "reason — the emptiest possible guard.")
ck("⚠️ ...and it agrees with itself on the simple cases",
   evaluate("${{ !cancelled() }}", {}, cancelled=False) is True
   and evaluate("${{ !cancelled() }}", {}, cancelled=True) is False
   and evaluate("a.b != '0'".replace("a.b", "steps.x.outputs.rc"),
                {"x": {"rc": "1"}}) is True,
   "⛔ rule 244: a matcher that does not match is no matcher.")


# ════════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 THE STATE MATRIX — BOTH GATES SPEAK WHEN BOTH SHOULD")
# ════════════════════════════════════════════════════════════════════════
TESTS = next(g for g in GATES if "tests" in (g.name or ""))
CONV = next(g for g in GATES if g is not TESTS)


def fires(gate, tests_rc, collect_rc, cancelled=False):
    return evaluate(gate.cond,
                    {"tests": {"rc": tests_rc}, "collect": {"rc": collect_rc}},
                    cancelled=cancelled,
                    failed=(tests_rc not in ("", "0")
                            or collect_rc not in ("", "0")))


MATRIX = [
    # tests  collect  cancelled   tests-gate  converge-gate   why
    ("1", "0", False, True, False,
     "only the suite failed"),
    ("0", "1", False, False, True,
     "only a converge pass failed"),
    ("1", "1", False, True, True,
     "🔴🔴 BOTH — this is the row that was impossible before today"),
    ("0", "0", False, False, False,
     "a clean run annotates nothing"),
    ("", "0", False, False, False,
     "the suite never reported and nothing failed"),
    ("1", "1", True, False, False,
     "a CANCELLED run is the designed MLB heartbeat outcome, not a fault"),
]
for t_rc, c_rc, canc, want_t, want_c, why in MATRIX:
    got_t, got_c = fires(TESTS, t_rc, c_rc, canc), fires(CONV, t_rc, c_rc, canc)
    ck("%s tests=%r collect=%r%s" % (
        "🔴🔴" if (want_t and want_c) else "⚠️", t_rc, c_rc,
        " cancelled" if canc else ""),
       (got_t, got_c) == (want_t, want_c),
       "%s — wanted tests-gate=%s converge-gate=%s, got %s/%s"
       % (why, want_t, want_c, got_t, got_c))

ck("🔴🔴 ...and NEITHER gate depends on being reached",
   all(("!cancelled()" in (g.cond or "") or "always()" in (g.cond or ""))
       for g in GATES),
   "⛔ THE DEFECT ITSELF. Without one of these, GitHub skips every gate "
   "after the first that exits — which is why a 47-hour nflverse "
   "outage never reached the Actions page. conds=%s"
   % [g.cond for g in GATES])
ck("⛔ ...and neither fires on a cancelled run",
   not fires(TESTS, "1", "1", True) and not fires(CONV, "1", "1", True),
   "⛔ 17 of 94 collect runs in the audit window were cancelled BY "
   "DESIGN — the MLB heartbeat being replaced by a newer run. "
   "Annotating those is how an error annotation stops meaning anything.")

# ════════════════════════════════════════════════════════════════════════
section("3. ⚠️ AND THE CONVERGE GATE SAYS WHICH FAILURE IT IS")
# ════════════════════════════════════════════════════════════════════════
def run_gate(gate, subs):
    body = gate.run or ""
    for k, v in subs.items():
        body = body.replace("${{ %s }}" % k, v)
    body = re.sub(r"\$\{\{[^}]*\}\}", "", body)
    d = tempfile.mkdtemp(prefix="gate-")
    try:
        r = subprocess.run(["bash", "-c", body], cwd=d, capture_output=True,
                           text=True, timeout=60)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


rc, out = run_gate(CONV, {"steps.collect.outputs.rc": "1"})
ck("⚠️ a real converge failure says a pass failed, and exits 1",
   rc == 1 and "converge pass failed" in out,
   "out=%r rc=%s" % (out[-160:], rc))
rc, out = run_gate(CONV, {"steps.collect.outputs.rc": ""})
ck("🔴 an UNREPORTED converge step says so instead of blaming a pass",
   rc == 1 and "never reported" in out,
   "⛔ when the suite hard-fails on a push the converge step is skipped "
   "and its rc is empty. The old single message called that 'at least "
   "one converge pass failed', which was false every time. "
   "out=%r rc=%s" % (out[-200:], rc))
rc, out = run_gate(TESTS, {})
ck("⚠️ the tests gate still names the Tests step",
   rc == 1 and "test suite failed" in out,
   "out=%r rc=%s" % (out[-160:], rc))
