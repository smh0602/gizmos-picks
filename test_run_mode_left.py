#!/usr/bin/env python3
"""`left` IN `run_mode` IS A CREDIT COUNT, AND NOTHING ELSE MAY BE PUT IN IT.

🔴 WHAT HAPPENED `[measured 2026-09-26 from the logs of collect runs #1766,
#1767, #1770, #1781, #1786, #1816 and #1835]`. Every football converge pass
that planned `props-board` ended in

    ERROR in props-board: TypeError: '<' not supported between instances
    of 'dict' and 'int'

`run_mode` stored the football builder's return value -- its BOARD, a
dict -- in `left`, and `left < RESERVE` compares a credit count. The board
had already been written, so the freshness contract saw nothing stale, and
the workflow blamed whichever mode the cron had launched ("mode 'news'
failed for ncaaf", cfb-probe, card-fb, nfl-logs). Introduced 6491668,
2026-09-21.

✅ THE CLASS, NOT THE INSTANCE: every `left = ...` in `run_mode` must be
`None` or a call to a function whose own `return`s are all `None` or its
credit count (`left`). A builder that returns anything else -- a board, a
report, a tuple -- fails here before it can reach the comparison.
➕ And the instance is driven end to end: the football props-board mode in
a sandbox, through the real `collect.py`.

# @vacuity 🔴 the football board is never stored as a credit count
#   file: collect.py
#   find:                 collect_props_board_fb()        # the BOARD, not a credit count
#   with:                 left = collect_props_board_fb()
"""
import ast
import datetime
import glob
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, eq, note, section  # noqa: E402

SRC = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
TREE = ast.parse(SRC)
FNS = {n.name: n for n in TREE.body if isinstance(n, ast.FunctionDef)}


def own_returns(fn):
    """The function's OWN return expressions -- nested defs and lambdas
    have returns of their own and do not count."""
    out, stack = [], list(fn.body)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(n, ast.Return):
            out.append(n.value)
        stack.extend(ast.iter_child_nodes(n))
    return out


def credit_like(expr):
    """A return value that is a credit count or nothing."""
    return (expr is None
            or (isinstance(expr, ast.Constant) and expr.value is None)
            or (isinstance(expr, ast.Name) and expr.id == "left"))


def bad_values(expr):
    """Why this right-hand side can put a non-credit value into `left`."""
    if isinstance(expr, ast.Constant) and expr.value is None:
        return []
    if isinstance(expr, ast.IfExp):
        return bad_values(expr.body) + bad_values(expr.orelse)
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
        fn = FNS.get(expr.func.id)
        if fn is None:
            return [f"{expr.func.id}() is not a collect.py function -- its return is unknown"]
        wrong = [ast.unparse(r) for r in own_returns(fn) if not credit_like(r)]
        return [f"{expr.func.id}() returns {w}" for w in wrong]
    return [f"`{ast.unparse(expr)}` is not None or a credit-returning call"]


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 EVERY `left = ...` IN run_mode IS A CREDIT COUNT OR NONE")
# ══════════════════════════════════════════════════════════════════════
RUN = FNS["run_mode"]
assigns = [n for n in ast.walk(RUN) if isinstance(n, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == "left" for t in n.targets)]
ck(len(assigns) >= 20, f"the check sees run_mode's assignments ({len(assigns)})",
   "rule 67: a scan that finds nothing passes forever")
calls = [a for a in assigns if isinstance(a.value, (ast.Call, ast.IfExp))]
ck(len(calls) >= 10, f"   ...including the calls whose return lands in it ({len(calls)})")
bad = [(a.lineno, why) for a in assigns for why in bad_values(a.value)]
ck(not bad, "🔴🔴 no builder's board, report or tuple can reach `left < RESERVE`",
   str(bad[:4]))
ck(any(credit_like(r) and isinstance(r, ast.Name) for r in own_returns(FNS["collect_props"])),
   "   ✅ the paid pulls do return their credit count (the check can tell the two apart)")
ck(not all(credit_like(r) for r in own_returns(FNS["collect_props_board_fb"])),
   "   ⚠️ ...and the football board builder returns its board, which is why it must not "
   "be stored there")

# ══════════════════════════════════════════════════════════════════════
section("2. DRIVEN: THE FOOTBALL PROPS-BOARD MODE, END TO END")
# ══════════════════════════════════════════════════════════════════════
d = tempfile.mkdtemp(prefix="pboard-")
try:
    for f in glob.glob(os.path.join(ROOT, "*.py")) + glob.glob(os.path.join(ROOT, "*.sh")):
        shutil.copy2(f, d)
    day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    snap = os.path.join(d, "data", "nfl", day, "props-player")
    os.makedirs(snap)
    os.makedirs(os.path.join(d, "picks"))
    kick = (datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with gzip.open(os.path.join(snap, "1208.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump({"pulled_at": datetime.datetime.now(datetime.timezone.utc)
                   .strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "events": [{"id": "e1", "home_team": "Home", "away_team": "Away",
                               "commence_time": kick,
                               "bookmakers": [{"key": "hardrockbet", "markets": [
                                   {"key": "player_pass_yds", "outcomes": [
                                       {"name": "Over", "description": "A Passer",
                                        "point": 250.5, "price": -110},
                                       {"name": "Under", "description": "A Passer",
                                        "point": 250.5, "price": -110}]}]}]}]}, fh)
    env = dict(os.environ, LEAGUE="nfl")
    env.pop("ODDS_API_KEY", None)
    p = subprocess.run([sys.executable, "collect.py", "props-board", "converge-off"],
                       cwd=d, env=env, capture_output=True, text=True, timeout=300)
    log = p.stdout + p.stderr
    ck(p.returncode == 0, "🔴 football props-board exits 0", log[-400:])
    ck("TypeError" not in log, "   ...with no TypeError", log[-300:])
    out = os.path.join(d, "data", "nfl", "latest", "props.json.gz")
    doc = json.load(gzip.open(out, "rt")) if os.path.exists(out) else {}
    eq((doc.get("n_games"), doc.get("n_props")), (1, 1),
       "   ...and the board it wrote holds the snapshot's game and rung")
finally:
    shutil.rmtree(d, ignore_errors=True)

note("⛔ WHAT THIS DOES NOT CLAIM: that `left` is the right credit count -- "
     "only that nothing but a credit count or None can be compared against "
     "RESERVE. budget.py and test_budget.py own the spend.")
