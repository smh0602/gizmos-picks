#!/usr/bin/env python3
"""A MODE IS NOT A ROW. EVERY STALE ROW MUST REACH `ok` AND THE LOG.

🔴 THE DEFECT `[found 2026-09-26 by an adversarial read-only review]`
`collect.converge()` ended with

    after = {r["mode"]: r for r in rows2}
    still = [m for m, r in after.items() if r["stale"]]

A mode may own SEVERAL contract rows — MLB `pitchers` owns three,
`record` two; football `card-fb` nine, `news` two, `nfl-logs` /
`cfb-probe` four. Keyed by mode, only each mode's LAST row survived, so a
stale row ahead of a fresh one vanished: `freshness.json` could publish
`"ok": true` over it and the log printed "every artifact is inside
contract". `[measured 2026-09-26 00:45Z]` `news.json` was stale in BOTH
football trees behind a fresh `news-flags.json`, and the lossy map
dropped it. The same shape sat in `test_news_archive.py` (#170's second
`news` row), where it fired a false alarm every night.

✅ THE CLASS, NOT THE LINE:
  1. the reported scenario, through the REAL `converge()`;
  2. every row of every league's REAL contract, left stale alone, must
     reach `ok`, the published rows and the log — and a pass that repairs
     it must read clean, so the check cannot pass by always crying stale;
  3. no tracked Python file and no page script may build a map keyed by a
     row's `mode` alone. ⚠️ Type-blind on purpose: a mode is not a unique
     key anywhere in this repo (the contract, and the routing table where
     one mode rides several crons). Group per mode, or key by
     (mode, path).
⛔ Nothing here bills the account: `run_mode` is stubbed in-process and
   the key is blanked.

# @vacuity 🔴🔴 the original defect, back in the one helper
#   file: collect.py
#   find: return sorted({r["mode"] for r in rows if r["stale"]})
#   with: return sorted(m for m, r in {r["mode"]: r for r in rows}.items() if r["stale"])
#
# @vacuity 🔴 FIRST row per mode is as lossy as the last (no dict: section 2 alone)
#   file: collect.py
#   find: return sorted({r["mode"] for r in rows if r["stale"]})
#   with: return sorted(m for m in dict.fromkeys(r["mode"] for r in rows) if next(r for r in rows if r["mode"] == m)["stale"])
#
# @vacuity 🔴 `ok` itself is read off the published file, not assumed
#   file: collect.py
#   find: "ok": not still,
#   with: "ok": True,
#
# @vacuity 🔴 the LOG line is checked on its own: a report that is right beside a log that lies
#   file: collect.py
#   find: still = _stale_modes(rows2)
#   with: still = _stale_modes(rows2[-1:])
#
# @vacuity 🔴 a mode-keyed map in ANOTHER reader (the watchdog) is caught
#   file: watchdog.py
#   find: stale = [r for r in (f.get("artifacts") or []) if r.get("stale")]
#   with: stale = [r for r in {r.get("mode"): r for r in (f.get("artifacts") or [])}.values() if r.get("stale")]
#
# @vacuity 🔴 ...in the PAGE's own script
#   file: index.html
#   find: const bad = FRESH.artifacts.filter(a => a.stale && a.page !== false);
#   with: const bad = Object.values(Object.fromEntries(FRESH.artifacts.map(a => [a.mode, a]))).filter(a => a.stale && a.page !== false);
#
# @vacuity 🔴 ...and in a TEST file, where the second copy of it lived
#   file: test_news_archive.py
#   find: _all = F.survey("data/%s" % _lg, "picks")
#   with: _all = list({r["mode"]: r for r in F.survey("data/%s" % _lg, "picks")}.values())
"""
import ast
import glob
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import warnings

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import freshness as F  # noqa: E402

LEAGUES = (("mlb", "data"), ("nfl", "data/nfl"), ("ncaaf", "data/ncaaf"))
_LOADED = [None]


def drive(league, data, rows_of, repair=None):
    """Run the REAL `collect.converge()` for `league` in a scratch tree.

    `rows_of()` is what the survey sees (before AND after the pass);
    `repair(mode)` is what `run_mode` does. -> (report, log lines, code).
    """
    env0 = {k: os.environ.get(k) for k in ("LEAGUE", "ODDS_API_KEY")}
    tmp = tempfile.mkdtemp()
    real = F.survey
    try:
        os.environ["LEAGUE"], os.environ["ODDS_API_KEY"] = league, ""
        os.chdir(tmp)
        import collect
        # ⚠️ `collect` reads LEAGUE at import: reloaded once per league.
        if _LOADED[0] != league:
            importlib.reload(collect)
            _LOADED[0] = league
        lines = []
        collect.log = lambda m: lines.append(str(m))
        collect.daily_spend = lambda: 0
        collect.run_mode = repair or (lambda m: None)
        F.survey = lambda data=None, picks=None, now=None: rows_of()
        code = collect.converge()
        p = os.path.join(tmp, data, "latest", "freshness.json")
        rep = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
        return rep, lines, code
    finally:
        F.survey = real
        os.chdir(ROOT)
        for k, v in env0.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)


def scenario(base, stale_at):
    """`base` rows, all fresh except index `stale_at` (None = all fresh)."""
    out = []
    for j, r in enumerate(base):
        s = j == stale_at
        out.append(dict(r, stale=s, missing=False, late_min=5.0 if s else None,
                        age_min=r["age_min"] if r["age_min"] is not None else 1.0))
    return out


def still_line(lines):
    return next((l for l in lines if l.startswith("STILL OUT OF CONTRACT:")), "")


def judge(rep, lines, mode, path):
    """(the report and the log both carry this stale row, detail)."""
    arts = (rep or {}).get("artifacts") or []
    row = [a for a in arts if a.get("mode") == mode and a.get("path") == path]
    named = mode in still_line(lines).split(":", 1)[-1].split()
    clean = any("every artifact is inside contract" in l for l in lines)
    good = (rep is not None and rep.get("ok") is False and len(row) == 1
            and row[0].get("stale") is True and named and not clean)
    return good, ("ok=%s row_stale=%s log=%r clean_line=%s"
                  % ((rep or {}).get("ok"), [a.get("stale") for a in row],
                     still_line(lines), clean))


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE REPORTED CASE: one mode, two rows, the FIRST stale")
# ══════════════════════════════════════════════════════════════════════
_two = [
    {"mode": "alpha", "path": "data/latest/alpha-1.json", "kind": "file",
     "why": "t", "age_min": 900.0, "due_at": None, "due_et": "6:00",
     "late_min": 5.0, "paid": False, "stale": True, "missing": False,
     "page": True},
    {"mode": "alpha", "path": "data/latest/alpha-2.json", "kind": "file",
     "why": "t", "age_min": 1.0, "due_at": None, "due_et": "6:00",
     "late_min": None, "paid": False, "stale": False, "missing": False,
     "page": True},
    {"mode": "beta", "path": "data/latest/beta.json", "kind": "file",
     "why": "t", "age_min": 1.0, "due_at": None, "due_et": "6:00",
     "late_min": None, "paid": False, "stale": False, "missing": False,
     "page": True},
]
_rep, _lines, _code = drive("mlb", "data", lambda: [dict(r) for r in _two])
_ok, _why = judge(_rep, _lines, "alpha", "data/latest/alpha-1.json")
ck("🔴 converge reports `alpha` stale and publishes ok:false when its FIRST "
   "row is stale and its LAST is fresh", _ok, _why)
ck("   ...and the fresh mode is not named", "beta" not in still_line(_lines),
   still_line(_lines))
ck("   ...and every row is published, not one per mode",
   len((_rep or {}).get("artifacts") or []) == len(_two),
   "%d of %d" % (len((_rep or {}).get("artifacts") or []), len(_two)))


# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 EVERY ROW OF EVERY LEAGUE'S REAL CONTRACT, stale alone")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ The rows are the real survey's — real modes, real paths, real order;
#    only the stale flags are set per scenario. `converge`, `write_freshness`
#    and the log are the real code.
_multi_total = 0
for _lg, _data in LEAGUES:
    _base = F.survey(data=_data, picks="picks")
    _by = {}
    for _r in _base:
        _by.setdefault(_r["mode"], []).append(_r)
    _multi = {m: len(rs) for m, rs in _by.items() if len(rs) > 1}
    _multi_total += len(_multi)
    note("%s: %d rows, %d modes; several rows: %s" % (
        _lg, len(_base), len(_by),
        ", ".join("%s x%d" % kv for kv in sorted(_multi.items())) or "none"))
    _missed, _false = [], []
    for _i, _r in enumerate(_base):
        _rep, _lines, _ = drive(_lg, _data, lambda i=_i: scenario(_base, i))
        _ok, _why = judge(_rep, _lines, _r["mode"], _r["path"])
        if not _ok:
            _missed.append("%s #%d %s: %s" % (_r["mode"], _i, _r["path"], _why))
        # ✅ THE CONTROL: the pass repairs that row. It must read clean, or
        #    a check that always says "stale" would pass the half above.
        _state = {"i": _i}

        def _fix(m, st=_state, mode=_r["mode"]):
            if m == mode:
                st["i"] = None
        _rep, _lines, _ = drive(_lg, _data,
                                lambda st=_state: scenario(_base, st["i"]),
                                repair=_fix)
        if not (_rep and _rep.get("ok") is True
                and any("every artifact is inside contract" in l for l in _lines)
                and not still_line(_lines)):
            _false.append("%s #%d: ok=%s log=%r" % (
                _r["mode"], _i, (_rep or {}).get("ok"), still_line(_lines)))
    ck("🔴 %s: each of the %d rows, left stale alone, reaches `ok`, the "
       "published rows and the log" % (_lg, len(_base)),
       _base and not _missed, "; ".join(_missed[:4]) or "none missed")
    ck("   ✅ %s: ...and a pass that repairs it reads clean" % _lg,
       _base and not _false, "; ".join(_false[:4]) or "none wrong")
note("modes owning several rows across the three leagues: %d — the case "
     "section 1 plants whatever the contract holds" % _multi_total)


# ══════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 NO MAP KEYED BY A ROW'S `mode` ALONE, ANYWHERE")
# ══════════════════════════════════════════════════════════════════════
def _is_mode(n):
    """`x["mode"]` or `x.get("mode"[, d])`."""
    if (isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)
            and n.slice.value == "mode"):
        return True
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "get" and n.args
            and isinstance(n.args[0], ast.Constant) and n.args[0].value == "mode")


def _names(n):
    return {x.id for x in ast.walk(n) if isinstance(x, ast.Name)}


def py_hits(src):
    """Line numbers where a Python map is keyed by a row's mode alone."""
    out = []
    with warnings.catch_warnings():
        # ⚠️ another file's `"\w"` is that file's business, not this scan's
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.DictComp) and _is_mode(n.key):
            out.append(n.lineno)
        elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id == "dict" and n.args
              and isinstance(n.args[0], (ast.GeneratorExp, ast.ListComp))
              and isinstance(n.args[0].elt, ast.Tuple) and n.args[0].elt.elts
              and _is_mode(n.args[0].elt.elts[0])):
            out.append(n.lineno)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                # ⚠️ `d[r["mode"]] = r` overwrites; `d[k] = d.get(k) or ...`
                #    aggregates, and reads its own map — that one is fine.
                if (isinstance(t, ast.Subscript) and _is_mode(t.slice)
                        and not (_names(t.value) & _names(n.value))):
                    out.append(n.lineno)
    return out


_JS_COMMENT = re.compile(r"/\*.*?\*/|<!--.*?-->|^\s*//[^\n]*", re.S | re.M)
_JS_PAIR = re.compile(r"(?:fromEntries|new\s+Map)\s*\([^;]*?\[\s*\w+\.mode\s*,")
_JS_SET = re.compile(r"(\w+)\s*\[\s*\w+\.mode\s*\]\s*=(?![=>])([^;\n]*)")


def js_hits(src):
    """Line numbers where page script keys a map by a row's mode alone."""
    code = _JS_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), src)
    out = [code.count("\n", 0, m.start()) + 1 for m in _JS_PAIR.finditer(code)]
    out += [code.count("\n", 0, m.start()) + 1 for m in _JS_SET.finditer(code)
            if not re.search(r"\b%s\b" % re.escape(m.group(1)), m.group(2))]
    return sorted(out)


# ✅ THE SCANNER, DRIVEN ON PLANTED CODE FIRST: each lossy shape must be
#    caught and each correct one left alone, or section 3 proves nothing.
_PLANT_BAD_PY = {
    "the converge line": 'after = {r["mode"]: r for r in rows2}',
    ".get form": 'a = {r.get("mode"): r["stale"] for r in rows}',
    "dict(pairs)": 'a = dict((r["mode"], r) for r in rows)',
    "loop overwrite": 'for r in rows:\n    d[r["mode"]] = r',
}
_PLANT_OK_PY = {
    "a set of modes": 'still = sorted({r["mode"] for r in rows if r["stale"]})',
    "grouped per mode": 'for r in rows:\n    by.setdefault(r["mode"], []).append(r)',
    "aggregated in place": 'for r in rows:\n    d[r["mode"]] = d.get(r["mode"], False) or r["stale"]',
    "keyed by mode AND path": 'a = {(r["mode"], r["path"]): r for r in rows}',
}
_PLANT_BAD_JS = {
    "fromEntries": "const m = Object.fromEntries(rows.map(a => [a.mode, a]));",
    "new Map": "const m = new Map(rows.map(a => [a.mode, a]));",
    "loop overwrite": "rows.forEach(a => { m[a.mode] = a; });",
}
_PLANT_OK_JS = {
    "a read": "const t = TAB_OF[a.mode] || a.mode;",
    "a comparison": "if (m[a.mode] === a) x();",
    "aggregated in place": "m[a.mode] = (m[a.mode] || []).concat([a]);",
    "a comment": "/* Object.fromEntries(rows.map(a => [a.mode, a])) */ x();",
}
ck("🔴 the scanner catches every planted lossy Python shape",
   all(py_hits(s) for s in _PLANT_BAD_PY.values()),
   "missed: %s" % [k for k, s in _PLANT_BAD_PY.items() if not py_hits(s)])
ck("   ✅ ...and leaves every correct one alone",
   not any(py_hits(s) for s in _PLANT_OK_PY.values()),
   "fired on: %s" % [k for k, s in _PLANT_OK_PY.items() if py_hits(s)])
ck("🔴 the scanner catches every planted lossy page-script shape",
   all(js_hits(s) for s in _PLANT_BAD_JS.values()),
   "missed: %s" % [k for k, s in _PLANT_BAD_JS.items() if not js_hits(s)])
ck("   ✅ ...and leaves every correct one alone",
   not any(js_hits(s) for s in _PLANT_OK_JS.values()),
   "fired on: %s" % [k for k, s in _PLANT_OK_JS.items() if js_hits(s)])


def tracked(*globs):
    """Every tracked file matching `globs`, from git — ⛔ never the working
    tree's stray copies (`.claude/worktrees/` holds whole old checkouts)."""
    try:
        out = subprocess.run(["git", "ls-files", "--", *globs], cwd=ROOT,
                             capture_output=True, text=True, timeout=60)
        files = out.stdout.split() if out.returncode == 0 else []
    except (OSError, subprocess.SubprocessError):
        files = []
    # ⚠️ No git (a bare copy of the tree): the top level is where every
    #    module and test lives, so that is what is read.
    return files or sorted({os.path.basename(p) for g in globs
                            for p in glob.glob(os.path.join(ROOT, g))})


_py = [p for p in tracked("*.py") if os.path.exists(os.path.join(ROOT, p))]
_js = [p for p in tracked("*.html", "*.js")
       if os.path.exists(os.path.join(ROOT, p))]
_found, _unparsed = [], []
for _p in _py:
    try:
        _src = open(os.path.join(ROOT, _p), encoding="utf-8").read()
        _found += ["%s:%d" % (_p, ln) for ln in py_hits(_src)]
    except (SyntaxError, UnicodeDecodeError) as _e:
        _unparsed.append("%s (%s)" % (_p, type(_e).__name__))
for _p in _js:
    _src = open(os.path.join(ROOT, _p), encoding="utf-8", errors="replace").read()
    _found += ["%s:%d" % (_p, ln) for ln in js_hits(_src)]
# ⛔ AN EMPTY SCAN IS NOT A CLEAN ONE: the files the class has lived in
#    and is read by must actually have been read.
_must = {"collect.py", "freshness.py", "watchdog.py", "verify_freshness.py",
         "test_news_archive.py", "index.html"}
ck("the scan read every file this defect has lived in or is read by "
   "(%d Python, %d page)" % (len(_py), len(_js)),
   _must <= set(_py) | set(_js),
   "not read: %s" % sorted(_must - set(_py) - set(_js)))
ck("every tracked Python file parsed", not _unparsed, "; ".join(_unparsed))
ck("🔴🔴 no tracked file keys rows by `mode` alone — group per mode, or "
   "key by (mode, path)", not _found, "; ".join(_found[:8]))
