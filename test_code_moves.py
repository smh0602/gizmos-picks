#!/usr/bin/env python3
r"""🔴🔴 A MERGED MODEL CHANGE IS LIVE AT THE NEXT PASS, NOT AT THE NEXT DEADLINE. `[Sam, 2026-11-10]`

Asked "Should a model change go live at the next hourly pass instead of the next morning's build?",
Sam: "Yes, build it". fb-model.json is rebuilt only by `card-fb`, due once a morning. College's
switch to HC (#339) merged 11-10 01:18Z. GitHub was starting that evening's crons 6-10 hours late,
so it was still not live at 02:40Z and would not be before 13:30Z. Meanwhile the card's game lines
were the old model's, and the ladder refused the old fits (#345, working as built).

✅ THE CLASS: a file built by code that has since changed. fb_model.stamp writes `built_by`,
   record_grader's fingerprint of `fb_model.build` and every name it reaches in every module
   (`fb_model_fingerprint`, the ONE recipe). freshness.code_moves plans `card-fb` for a football
   league whose file names other code: planned, never marked stale (the deadline is unchanged).
   §1 the fingerprint follows a module's import read THROUGH it (`FM.t60r.kick`), which used to
      raise "defines no build";
   §2 one recipe, the same in the builder, its stamp and the planner;
   §3 it changes with what the model DOES (a pick rule the input stamp cannot see, a constant, a
      followed module, the chain) and not with a comment or a name build never reaches;
   §4 code_moves on planted trees; §5 plan() plans it and the survey marks nothing stale.

⛔ A TEST ASKS THE CODE: planted trees and planted source only, no live data.

# @vacuity 🔴🔴 a football league whose fb-model.json names other code gets card-fb
#   file: freshness.py
#   find:         if made != code:
#   with:         if False:
#
# @vacuity 🔴🔴 the planner plans what code_moves names
#   file: freshness.py
#   find:         | code_moves(data)
#   with:         | set()
#
# @vacuity 🔴 a file whose stamp cannot be read was not built by this code
#   file: freshness.py
#   find:             made = None
#   with:             made = code
#
# @vacuity 🔴 MLB builds no football model file
#   file: freshness.py
#   find:     if lg not in FB_TIMES:               # MLB builds no football model file
#   with:     if False:
#
# @vacuity ⛔ a sandbox holding freshness.py alone imports nothing
#   file: freshness.py
#   find:         if not os.path.exists(path) or not os.path.exists(os.path.join(here, module)):
#   with:         if not os.path.exists(path):
#
# @vacuity 🔴 stamp writes the code that built the file
#   file: fb_model.py
#   find:     doc["built_by"] = builder_fingerprint()
#   with:     pass
#
# @vacuity 🔴🔴 the recipe follows the other modules build reaches
#   file: record_grader.py
#   find:     return fingerprint(path, FB_MODEL, follow=True)
#   with:     return fingerprint(path, FB_MODEL, follow=False)
#
# @vacuity 🔴 the fingerprint reads M.a.b through a module M imports
#   file: record_grader.py
#   find:                     hit, then = ((b[0], n.value.attr), n.attr) if b and not b[1] else (None, None)
#   with:                     hit, then = None, None
#
# @vacuity 🔴 ...and follows a name a module imports into that module
#   file: record_grader.py
#   find:             if follow and imp:
#   with:             if False:
#
# @vacuity 🔴🔴 only a missing ENTRY raises, never a name read through the entry's file
#   file: record_grader.py
#   find:             if p == top and start == entry and then is None:
#   with:             if p == top:
"""
import ast
import contextlib
import glob
import gzip
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import fb_model as F  # noqa: E402
import freshness as FR  # noqa: E402
import record_grader as RG  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def attempt(fn, *a, **k):
    """-> (value, None) or (None, the exception's name and message)."""
    try:
        return fn(*a, **k), None
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


TMP = []


def mktree(prefix):
    d = tempfile.mkdtemp(prefix=prefix)
    TMP.append(d)
    return d


try:
    # ══════════════════════════════════════════════════════════════════
    section("1. 🔴 THE FINGERPRINT FOLLOWS A MODULE'S IMPORT READ THROUGH IT")
    # ══════════════════════════════════════════════════════════════════
    # top imports aux (and one of its names); mid reads aux THROUGH top, as fb_challengers reads
    # `FM.t60r.kick` through fb_model. Fingerprinting top.build used to raise "defines no build".
    _P = mktree("codemoves-rg-")
    write(os.path.join(_P, "top.py"), "import aux\nimport mid\nfrom aux import shared\n\n\n"
          "def g():\n    return 1\n\n\ndef build():\n    return mid.go()\n")
    write(os.path.join(_P, "mid.py"), "import top as T\n\n\n"
          "def go():\n    return T.aux.helper() + T.g() + T.shared()\n")
    write(os.path.join(_P, "aux.py"), "def helper():\n    return 2\n\n\ndef shared():\n    return 3\n\n\n"
          "def unrelated():\n    return 4\n")
    _TOP, _AUX = os.path.join(_P, "top.py"), os.path.join(_P, "aux.py")
    _c, _err = attempt(RG.closure, _TOP, "build", follow=True)
    ck(_err is None, "🔴🔴 a name read through the entry's own file (T.aux) no longer raises", _err)
    _c = _c or {}
    ck({"build", "g", "mid.go", "aux.helper", "aux.shared"} <= set(_c),
       "🔴 ...and is followed: T.aux.helper -> aux.helper, T.shared (top's `from aux import`) -> "
       "aux.shared, T.g -> top's own g", sorted(_c))
    ck("aux.unrelated" not in _c, "   ...and nothing build never reaches", sorted(_c))
    _fp0, _ = attempt(RG.fingerprint, _TOP, "build", follow=True)
    _src = open(_AUX, encoding="utf-8").read()
    write(_AUX, _src.replace("return 2", "return 20"))
    _fp1, _ = attempt(RG.fingerprint, _TOP, "build", follow=True)
    write(_AUX, _src.replace("return 4", "return 40"))
    _fp2, _ = attempt(RG.fingerprint, _TOP, "build", follow=True)
    write(_AUX, _src)
    ck(_fp0 and _fp1 and _fp0 != _fp1, "🔴 a change to aux.helper, reached only through T.aux, changes it",
       (_fp0, _fp1))
    ck(_fp0 and _fp2 == _fp0, "   ✅ a change to aux.unrelated does not", (_fp0, _fp2))
    _, _err = attempt(RG.fingerprint, _TOP, "nothing_here", follow=True)
    ck(_err is not None and _err.startswith("LookupError") and "defines no nothing_here" in _err,
       "⛔ a file without the entry still raises: 'I could not tell which code' never reads as a match",
       _err)
    write(os.path.join(_P, "top.py"), "import mid\nimport not_a_module_anywhere as ext\n\n\n"
          "def build():\n    return mid.go()\n")
    write(os.path.join(_P, "mid.py"), "import top as T\n\n\ndef go():\n    return T.ext.f()\n")
    _, _err = attempt(RG.fingerprint, _TOP, "build", follow=True)
    ck(_err is not None and "neither beside it nor in the standard library" in _err,
       "⛔ ...and a module read through the chain that is neither beside it nor the standard library "
       "raises (record_grader's existing rule)", _err)

    # ══════════════════════════════════════════════════════════════════
    section("2. ONE RECIPE: THE BUILDER, ITS STAMP AND THE PLANNER AGREE")
    # ══════════════════════════════════════════════════════════════════
    _CODE, _err = attempt(RG.fb_model_fingerprint, F.__file__)
    ck(_err is None and isinstance(_CODE, str) and len(_CODE) == 16,
       "🔴🔴 the real fb_model.build fingerprints (the planner's fallback is only for a break)", _err)
    eq(F.builder_fingerprint(), _CODE, "fb_model.builder_fingerprint is the recipe")
    eq(FR.code_fingerprint("fb_model.py", "fb_model_fingerprint"), _CODE,
       "🔴 freshness, which never imports fb_model, computes the same")
    _st = F.stamp({"pricing": {}}, "nfl")
    eq(_st.get("built_by"), _CODE, "🔴 fb_model.stamp writes it as `built_by`")
    eq([(m, f, mod, r) for m, f, mod, r in FR.CODE_BUILT if f == "fb-model.json"],
       [("card-fb", "fb-model.json", "fb_model.py", "fb_model_fingerprint")],
       "the planner reads fb-model.json's stamp and rebuilds it with card-fb, its only builder")


    def recipe_callers(path):
        """Files that call record_grader's fingerprint on fb_model's `build` OUTSIDE its recipe."""
        tree = ast.parse(open(path, encoding="utf-8").read())
        out = []
        for n in ast.walk(tree):
            if (isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", None)) in
                    ("fingerprint", "closure")
                    and any(isinstance(a, ast.Constant) and a.value == RG.FB_MODEL for a in n.args)):
                out.append(n.lineno)
        return out
    _bad = {os.path.basename(p): recipe_callers(p) for p in glob.glob(os.path.join(ROOT, "*.py"))
            if not os.path.basename(p).startswith("test_")}
    eq({k: v for k, v in _bad.items() if v}, {},
       "⛔ no module spells the recipe itself (fingerprint(..., \"build\", ...)): ONE copy, record_grader's")
    _p = os.path.join(mktree("codemoves-census-"), "x.py")
    write(_p, "import record_grader as RG\nFP = RG.fingerprint('fb_model.py', 'build', follow=True)\n")
    ck(recipe_callers(_p), "   (the census sees a planted second copy)")

    # ══════════════════════════════════════════════════════════════════
    section("3. 🔴 IT CHANGES WITH WHAT THE MODEL DOES, AND ONLY THAT")
    # ══════════════════════════════════════════════════════════════════
    _T = mktree("codemoves-code-")
    for p in glob.glob(os.path.join(ROOT, "*.py")):
        if not os.path.basename(p).startswith("test_"):
            shutil.copy(p, _T)
    _FM = os.path.join(_T, "fb_model.py")

    def fp():
        return RG.fb_model_fingerprint(_FM)

    def inputs():
        return RG.fingerprint(_FM, "features", follow=True) + RG.fingerprint(_FM, "predict", follow=True)

    def fp_with(module, old, new, also=None):
        path = os.path.join(_T, module)
        src = open(path, encoding="utf-8").read()
        assert src.count(old) == 1, (module, old)
        write(path, src.replace(old, new))
        try:
            return fp(), (also() if also else None)
        finally:
            write(path, src)

    eq(fp(), _CODE, "the planted copy fingerprints as this code")
    _IN = inputs()
    _b, _i = fp_with("fb_model.py", "    if market in (\"spread\", \"total\"):\n        if SIM.get(r.get(\"lg\")):",
                     "    if market in (\"spread\",):\n        if SIM.get(r.get(\"lg\")):", inputs)
    ck(_b != _CODE and _i == _IN,
       "🔴🔴 a change to the PICK RULE (shown_pick) changes it, where the input stamp (#345) cannot see "
       "it: why the file names its whole builder", (_b, _i == _IN))
    ck(fp_with("fb_model.py", "RIDGE = 1.0 ", "RIDGE = 2.0 ")[0] != _CODE,
       "🔴 ...so does a constant the fits read (RIDGE)")
    ck(fp_with("one_side.py", '    return "home" if p_home >= 100 - p_home else "away"',
               '    return "home" if p_home > 100 - p_home else "away"')[0] != _CODE,
       "🔴 ...and a followed module's rule (one_side.expected_side: one team per game)")
    ck(fp_with("t60r.py", '    s = (g.get("start") or "")[:10]', '    s = (g.get("start") or "")[:7]')[0] != _CODE,
       "🔴 ...and code reached through another module's import (t60r.kick, read as FM.t60r.kick too)")
    ck(fp_with("fb_model.py", "def build(lg=None, root=None, out=None, extra_top=None, extra_players=None, now=None):",
               "def build(lg=None, root=None, out=None, extra_top=None, extra_players=None, now=None):\n"
               "    # a comment changes nothing")[0] == _CODE,
       "   ✅ a comment edit does not (no needless rebuild)")
    ck(fp_with("fb_model.py", '    "spread": ["own_margin", "h2h", "form", "possession", "personnel", "neutral", "dome"],',
               '    "spread": ["own_margin", "h2h"],')[0] == _CODE,
       "   ✅ nor does a name build never reaches (FEATURES, a label list)")

    # ══════════════════════════════════════════════════════════════════
    section("4. 🔴🔴 code_moves: A FOOTBALL FILE BUILT BY OTHER CODE GETS card-fb")
    # ══════════════════════════════════════════════════════════════════
    _D = mktree("codemoves-tree-").replace("\\", "/")

    def tree(lg, doc=None, raw=None):
        d = "%s/%s/data/%s" % (_D, lg, lg) if lg != "mlb" else "%s/mlb/data" % _D
        shutil.rmtree(os.path.dirname(d) if lg != "mlb" else d, ignore_errors=True)
        os.makedirs(d + "/latest", exist_ok=True)
        if doc is not None or raw is not None:
            write(d + "/latest/fb-model.json", raw if raw is not None else json.dumps(doc))
        return d

    eq(FR.code_moves(tree("nfl", {"built_by": _CODE, "pricing": {}})), set(),
       "✅ NFL, built by this code: nothing planned")
    eq(FR.code_moves(tree("nfl", {"built_by": "0" * 16})), {"card-fb"},
       "🔴🔴 NFL, built by other code: card-fb at the next pass")
    eq(FR.code_moves(tree("ncaaf", {"built_by": "f" * 16, "champion": "HC"})), {"card-fb"},
       "🔴🔴 college too (rule 6)")
    eq(FR.code_moves(tree("ncaaf", {"built_by": _CODE})), set(), "   ✅ ...and nothing when it matches")
    eq(FR.code_moves(tree("ncaaf", {"pricing": {"inputs": "x"}})), {"card-fb"},
       "🔴 a file from before the stamp existed (every file on main the day this merges) is rebuilt once")
    eq(FR.code_moves(tree("nfl", raw="{\"built_by\": ")), {"card-fb"},
       "🔴 a file whose stamp cannot be read was not built by this code: rebuilt")
    eq(FR.code_moves(tree("nfl", raw="[1, 2]")), {"card-fb"}, "   ...nor one that is not an object")
    eq(FR.code_moves(tree("nfl")), set(), "   a missing file is its own row's business (stale already)")
    eq(FR.code_moves(tree("mlb", {"built_by": "0" * 16})), set(), "⛔ MLB builds no football model file")
    eq(FR.code_moves(tree("nfl", {"built_by": "0" * 16}).replace("/", os.sep)), {"card-fb"},
       "   the league comes from the path, either separator")
    _alone = mktree("codemoves-alone-")
    _buf = io.StringIO()
    with contextlib.redirect_stdout(_buf):
        _got, _err = attempt(FR.code_moves, tree("nfl", {"built_by": "0" * 16}), root=_alone)
    ck(_err is None and _got == set() and _buf.getvalue() == "",
       "⛔ a sandbox holding freshness.py alone (no fb_model.py beside it) plans nothing, imports "
       "nothing and says nothing", (_got, _err, _buf.getvalue()))
    _bare = mktree("codemoves-nobuild-")
    write(os.path.join(_bare, "fb_model.py"), "def other():\n    return 1\n")
    _got, _err = attempt(FR.code_moves, tree("nfl", {"built_by": "0" * 16}), root=_bare)
    ck(_err is None and _got == set(),
       "⛔ code that cannot be fingerprinted plans nothing (it waits for its deadline) and never raises "
       "into converge", (_got, _err))

    # ══════════════════════════════════════════════════════════════════
    section("5. 🔴 plan() PLANS IT, AND THE SURVEY MARKS NOTHING STALE FOR IT")
    # ══════════════════════════════════════════════════════════════════
    _fresh = [{"mode": m, "path": p, "stale": False, "paid": False, "unhealthy": None, "missing": False}
              for m, p in (("props-board", "props.json.gz"), ("card-fb", "fb-model.json"))]
    _keep = FR.survey, FR.slate_moves, FR.every_pass, FR.injury_retry
    try:
        FR.survey = lambda data, picks, now: [dict(r) for r in _fresh]
        FR.slate_moves = lambda data, picks, now: set()
        FR.every_pass = lambda data, now: set()
        FR.injury_retry = lambda data, now: set()
        eq(FR.plan(tree("nfl", {"built_by": "0" * 16}), _D + "/picks")[0], ["card-fb"],
           "🔴🔴 every row fresh, the file built by other code: the pass runs card-fb")
        eq(FR.plan(tree("nfl", {"built_by": _CODE}), _D + "/picks")[0], [],
           "   ✅ ...and nothing when this code built it")
    finally:
        FR.survey, FR.slate_moves, FR.every_pass, FR.injury_retry = _keep
    import datetime
    _now = datetime.datetime(2026, 11, 10, 3, 0, tzinfo=datetime.timezone.utc)

    def row(doc):
        d = tree("ncaaf", doc)
        # the card's rows exist once the league has a props board ("cannot exist yet is not late")
        with gzip.open(d + "/latest/props.json.gz", "wt", encoding="utf-8") as fh:
            json.dump({"built_at": "2026-11-10T00:10:00Z", "games": []}, fh)
        rows = FR.survey(d, _D + "/picks", _now)
        return [r for r in rows if r["path"].replace("\\", "/").endswith("/latest/fb-model.json")]
    _match = row({"built_by": _CODE, "built_at": "2026-11-10T00:18:12Z"})
    _other = row({"built_by": "0" * 16, "built_at": "2026-11-10T00:18:12Z"})
    ck(_match and [{k: v for k, v in r.items() if k != "path"} for r in _match]
       == [{k: v for k, v in r.items() if k != "path"} for r in _other],
       "⛔ planned, NEVER MARKED STALE: the survey's fb-model.json row is the same either way (the gate, "
       "the watchdog and the page see no change; the deadline is unchanged)", (_match, _other))
    ck(_match and not _match[0]["stale"] and not _match[0]["unhealthy"],
       "   (built 00:18Z, after the last 13:30Z deadline: on time and healthy)", _match)
finally:
    for _d in TMP:
        shutil.rmtree(_d, ignore_errors=True)
