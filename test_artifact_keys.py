#!/usr/bin/env python3
"""🔴🔴 A KEY A MODULE READS MUST BE A KEY THE ARTIFACT HAS.

`[measured 2026-09-19]` `watchdog.py` read the staleness rows like this:

    stale = [r for r in (f.get("rows") or []) if r.get("stale")]

…and `collect.py:4851` writes that file with the key **`artifacts`**. So
`stale` was `[]` on every league on every pass, `check_freshness()`
`continue`d every time, and **the staleness check had never once run**.
The result is the headline of the whole audit:

    health.json   healthy: true, 0 findings
    verify_freshness.py (nfl)   FAIL — 2 artifact(s) past due

Two graders of one question disagreeing, and the one that summons the
repair agent is the one saying healthy. ⛔ Rule 67, shipped and live.

🔴 THERE WAS A SECOND BUG BEHIND THE FIRST. The message reads
`r.get("key")` and the rows carry **`mode`** — so even a corrected
container would have printed *"None tabs are showing data older than
promised"*. A guard that fixed only the container would have left that
standing, which is why §1 checks the ROWS as well.

⛔ AND THE INSTANCE IS NOT THE POINT. `CLAUDE.md`: guard the CLASS where
the class is answerable. It is: every module in this repo that loads a
JSON artifact it also writes can be asked, statically, whether the keys
it reads exist in the artifact actually on disk. §1 asks that of every
module and every artifact, today and for whatever is added next.

⚠️ THE SCANNER IS SCOPE-CORRECT ON PURPOSE. Its first draft walked a
module into its own functions, collapsed every local of the same name
into one set, and accused `watchdog.py` of reading eight keys off
`record.json` that it reads off other files. **A guard that fires on
correct code is the other failure, not a safe one** — so it is driven
against the real tree and must be SILENT on everything but the defect.

# @vacuity 🔴🔴 a reader keying on a field the writer does not emit is caught
#   file: watchdog.py
#   find:         stale = [r for r in (f.get("artifacts") or []) if r.get("stale")]
#   with:         stale = [r for r in (f.get("rows") or []) if r.get("stale")]
#
# @vacuity 🔴 ...and the row-level key too
#   file: watchdog.py
#   find:         names = ", ".join(sorted({str(r.get("mode")) for r in stale})[:6])
#   with:         names = ", ".join(sorted({str(r.get("key")) for r in stale})[:6])
"""
import ast
import datetime
import glob
import gzip
import io
import json
import os
import shutil
import tempfile

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
LOADERS = {"_read", "_j", "load", "_load"}


def walk_scope(fn):
    """Nodes in THIS scope only — never descending into a nested def."""
    out, stack = [], list(ast.iter_child_nodes(fn))
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        out.append(n)
        stack.extend(ast.iter_child_nodes(n))
    return out


def _lit(n):
    return n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None


def reads_on(name, nodes):
    """Every `name.get("k")` and `name["k"]` string key in these nodes."""
    out = set()
    for node in nodes:
        for n in ast.walk(node):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
               and n.func.attr == "get" and isinstance(n.func.value, ast.Name) \
               and n.func.value.id == name and n.args and _lit(n.args[0]):
                out.add(_lit(n.args[0]))
            if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) \
               and n.value.id == name and _lit(n.slice):
                out.add(_lit(n.slice))
    return out


def keyed_on(var, node):
    """The single key `var` is indexed with inside `node`, if any."""
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
           and n.func.attr == "get" and isinstance(n.func.value, ast.Name) \
           and n.func.value.id == var and n.args and _lit(n.args[0]):
            return _lit(n.args[0])
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) \
           and n.value.id == var and _lit(n.slice):
            return _lit(n.slice)
    return None


def artifact_files(basename):
    hits = glob.glob(os.path.join(ROOT, "data", "**", basename), recursive=True)
    hits += glob.glob(os.path.join(ROOT, "picks", basename))
    return sorted(hits)[:40]


def _doc(p):
    try:
        op = gzip.open if p.endswith(".gz") else io.open
        with op(p, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 EVERY KEY READ OFF AN ARTIFACT EXISTS IN THAT ARTIFACT")
# ════════════════════════════════════════════════════════════════════════
findings, surveyed, arts = [], 0, set()
for mod in sorted(glob.glob(os.path.join(ROOT, "*.py"))):
    base = os.path.basename(mod)
    if base.startswith("test_"):
        continue
    try:
        tree = ast.parse(io.open(mod, encoding="utf-8").read())
    except SyntaxError:                       # pragma: no cover
        continue
    scopes = [tree] + [n for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for fn in scopes:
        nodes = walk_scope(fn)
        for st in nodes:
            if not isinstance(st, ast.Assign) or len(st.targets) != 1:
                continue
            tgt = st.targets[0]
            if not isinstance(tgt, ast.Name) or not isinstance(st.value, ast.Call):
                continue
            nm = getattr(st.value.func, "id", None) or \
                getattr(st.value.func, "attr", None)
            if nm not in LOADERS:
                continue
            names = [_lit(n) for n in ast.walk(st.value)]
            names = [n for n in names
                     if n and (n.endswith(".json") or n.endswith(".json.gz"))]
            if not names:
                continue
            bn = names[-1]
            files = artifact_files(bn)
            if not files:
                continue
            arts.add(bn)
            where = "%s:%s" % (base, getattr(fn, "name", "<module>"))
            present = set()
            for f in files:
                d = _doc(f)
                if isinstance(d, dict):
                    present |= set(d.keys())
            want = reads_on(tgt.id, nodes)
            if want:
                surveyed += 1
                miss = sorted(k for k in want if k not in present)
                if miss:
                    findings.append("%s reads %s off %s — no such key in "
                                    "%d file(s) on disk"
                                    % (where, miss, bn, len(files)))
            # ── and one level down, into the rows of a list it iterates
            for n in nodes:
                gens = []
                if isinstance(n, ast.For) and isinstance(n.target, ast.Name):
                    gens.append((n.target.id, n.iter, n))
                for g in getattr(n, "generators", []) or []:
                    if isinstance(g.target, ast.Name):
                        gens.append((g.target.id, g.iter, n))
                for lv, it, node in gens:
                    cont = keyed_on(tgt.id, it)
                    if not cont:
                        continue
                    rk = set()
                    for f in files:
                        d = _doc(f)
                        v = (d or {}).get(cont)
                        if isinstance(v, list):
                            for row in v[:50]:
                                if isinstance(row, dict):
                                    rk |= set(row.keys())
                    if not rk:
                        continue
                    surveyed += 1
                    rr = reads_on(lv, [node])
                    rmiss = sorted(k for k in rr if k not in rk)
                    if rmiss:
                        findings.append(
                            "%s reads %s off a row of %s[%s] — no such key "
                            "in %d file(s) on disk"
                            % (where, rmiss, bn, cont, len(files)))

note("bindings surveyed: %d, across artifacts %s" % (surveyed, sorted(arts)))
ck("⚠️ the scanner found bindings to judge at all",
   surveyed >= 4 and len(arts) >= 3,
   "⛔ rule 67 — if the AST walk breaks, this file must go RED rather "
   "than green on nothing. surveyed=%d artifacts=%s" % (surveyed, sorted(arts)))
ck("🔴🔴 no module reads a key its artifact does not have",
   not findings,
   "⛔ THIS IS THE DEFECT OF 2026-09-19. A reader keyed on a name the "
   "writer never emits gets an empty container, and an empty container "
   "reads as 'nothing to report'. %s" % ("; ".join(findings) or "none"))

# ════════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 AND THE STALENESS CHECK IS DRIVEN, NOT READ")
# ════════════════════════════════════════════════════════════════════════
import watchdog as W                                            # noqa: E402

NOW = datetime.datetime(2026, 9, 19, 12, 0, tzinfo=datetime.timezone.utc)


def drive(per_league):
    """Run the real check against a synthetic tree; return its findings."""
    d = tempfile.mkdtemp(prefix="artkeys-")
    old = W.ROOT
    try:
        for lg, sub in W.DATA.items():
            doc = per_league.get(lg)
            if doc is None:
                continue
            p = os.path.join(d, sub, "latest")
            os.makedirs(p, exist_ok=True)
            with io.open(os.path.join(p, "freshness.json"), "w",
                         encoding="utf-8") as fh:
                json.dump(doc, fh)
        W.ROOT = d
        rep = W.Report()
        W.check_freshness(rep, NOW)
        return rep.items
    finally:
        W.ROOT = old
        shutil.rmtree(d, ignore_errors=True)


_STALE = {"ok": False, "built_at": "2026-09-19T07:38:29Z", "artifacts": [
    {"mode": "nfl-logs", "stale": True, "missing": True, "why": "possession"},
    {"mode": "fb-scores", "stale": False, "why": "the day's results"}]}
_FRESH = {"ok": True, "built_at": "2026-09-19T07:38:29Z", "artifacts": [
    {"mode": "gamelines", "stale": False, "why": "the board"}]}

hit = drive({"nfl": _STALE, "mlb": _FRESH, "ncaaf": _FRESH})
ck("🔴🔴 a stale artifact becomes a finding",
   len(hit) == 1,
   "⛔ THE WHOLE POINT. For as long as this check read the wrong key it "
   "produced nothing, on every league, on every pass — while "
   "verify_freshness.py was failing the same build. got %r" % (hit,))
ck("🔴 ...and the finding NAMES the artifact, not `None`",
   bool(hit) and "nfl-logs" in hit[0]["what"] and "None" not in hit[0]["what"],
   "⛔ the rows carry `mode`; the message used to ask for `key`. A "
   "finding that says 'None tabs are showing data older than promised' "
   "sends the reader nowhere. got %r" % (hit[0]["what"] if hit else None,))
ck("⚠️ ...and it is a DEGRADED warning, not a BROKEN finding",
   bool(hit) and hit[0]["severity"] == "DEGRADED"
   and hit[0]["repair"] is None,
   "⛔ the converge loop repairs staleness on its own and has already "
   "run by the time the watchdog looks; naming a repair here would have "
   "the watchdog racing it with a paid pull as the prize. That reasoning "
   "is unchanged by this fix. got %r" % (hit[0] if hit else None,))

quiet = drive({"nfl": _FRESH, "mlb": _FRESH, "ncaaf": _FRESH})
ck("✅ a contract with nothing stale says NOTHING",
   quiet == [],
   "⛔ THE OTHER FAILURE, and the more expensive one: a watchdog that "
   "warns every pass is a watchdog nobody reads. got %r" % (quiet,))

none_at_all = drive({})
ck("⚠️ a missing freshness.json is silence, not a finding",
   none_at_all == [],
   "⛔ a league that has not written a contract yet is a claim about our "
   "records, not about the product. got %r" % (none_at_all,))

legacy = drive({"nfl": {"ok": False, "rows": _STALE["artifacts"]}})
ck("⛔ ...and the OLD key name is not quietly accepted either",
   legacy == [],
   "🔴 this looks backwards and is deliberate. `rows` is a key NOTHING "
   "writes. If a future edit made the reader accept both, the static "
   "check in §1 would stop being able to tell which one the writer "
   "actually emits — and that ambiguity is what hid this bug for good. "
   "One writer, one key. got %r" % (legacy,))
