#!/usr/bin/env python3
r"""🔴🔴 A MERGED MODEL CHANGE IS LIVE AT THE NEXT PASS, NOT AT THE NEXT DEADLINE. `[Sam, 2026-11-10]`

Asked "Should a model change go live at the next hourly pass instead of the next morning's build?",
Sam: "Yes, build it". fb-model.json is rebuilt only by `card-fb`, due once a morning. College's
switch to HC (#339) merged 11-10 01:18Z. GitHub was starting that evening's crons 6-10 hours late,
so it was still not live at 02:40Z and would not be before 13:30Z. Meanwhile the card's game lines
were the old model's, and the ladder refused the old fits (#345, working as built).

✅ THE CLASS: a football model file built by code that has since changed. Each model's build
   stamps `built_by`, record_grader.builder_fingerprint of its module's `build` and every name it
   reaches in every module (the ONE recipe): the game model (fb-model.json) and the props model
   (fb-props-model.json, which sets the card's confidence; T74's season switch is in its reach).
   freshness.code_moves plans `card-fb` for a football league whose file names other code:
   planned, never marked stale (the deadline is unchanged). CODE_BUILT is the table; §2's census
   fails a module that writes `built_by` and is not in it.
   §1 the fingerprint follows a module's import read THROUGH it (`FM.t60r.kick`), which used to
      raise "defines no build", in every spelling the review found;
   §2 one recipe, the same in each builder, its stamp and the planner; the censuses;
   §2b the stamp never costs the file;
   §3 it changes with what a model DOES and not with a comment or a name its build never reaches;
   §4 code_moves on planted trees; §4b freshness's one repo import, lazy, and its sandbox;
   §5 plan() plans it and the survey marks nothing stale.

⛔ A TEST ASKS THE CODE: planted trees and planted source only, no live data.

# @vacuity 🔴🔴 a football league whose model file names other code gets card-fb
#   file: freshness.py
#   find:         if made != code:
#   with:         if False:
#
# @vacuity 🔴🔴 the planner plans what code_moves names
#   file: freshness.py
#   find:         | code_moves(data)
#   with:         | set()
#
# @vacuity 🔴🔴 the props model's file is a row of the table too (a merged props switch)
#   file: freshness.py
#   find:               ("card-fb", "fb-props-model.json", "fb_props_model.py"))
#   with:               )
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
# @vacuity 🔴 code that cannot be fingerprinted is said, not silent
#   file: freshness.py
#   find:             print(f"⚠️ {name}: the code that builds it could not be fingerprinted "
#   with:             (f"⚠️ {name}: the code that builds it could not be fingerprinted "
#
# @vacuity 🔴 stamp writes the code that built the file
#   file: fb_model.py
#   find:     doc["built_by"] = builder_fingerprint()
#   with:     pass
#
# @vacuity 🔴🔴 the stamp never costs the file: a fingerprint that raises is None
#   file: record_grader.py
#   find:     except Exception as e:                       # ⛔ the stamp never costs the file
#   with:     except ArithmeticError as e:
#
# @vacuity 🔴🔴 the recipe follows the other modules build reaches
#   file: record_grader.py
#   find:     return fingerprint(path, BUILDER, follow=True)
#   with:     return fingerprint(path, BUILDER, follow=False)
#
# @vacuity 🔴 the fingerprint reads M.a.b through a module M imports
#   file: record_grader.py
#   find:                     hit, then = ((b[0], n.value.attr), n.attr) if b and not b[1] else (None, None)
#   with:                     hit, then = None, None
#
# @vacuity 🔴 ...and X.f where X was imported FROM a module that imports X
#   file: record_grader.py
#   find:                         hit, then = (b[0], b[1]), n.attr
#   with:                         hit, then = (b[0], b[1]), None
#
# @vacuity 🔴 ...and keeps what is read through a name imported from another module
#   file: record_grader.py
#   find:                     queue.append((f, attr, then if imp[1] else None))
#   with:                     queue.append((f, attr, None))
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
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import fb_model as F  # noqa: E402
import fb_props_model as PM  # noqa: E402
import freshness as FR  # noqa: E402
import record_grader as RG  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

BUILDERS = {"fb_model.py": F, "fb_props_model.py": PM}


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

    # the review's two other spellings (11-10): `from top import aux; aux.helper()` (aux a module
    #    top imports), and `from hub import a` where hub does `import aux as a`, read as T.a.helper
    write(os.path.join(_P, "hub.py"), "import aux as a\n")
    write(os.path.join(_P, "top.py"), "import mid\nimport mid2\nfrom hub import a\nimport aux\n\n\n"
          "def build():\n    return mid.go() + mid2.go()\n")
    write(os.path.join(_P, "mid.py"), "from top import aux\n\n\ndef go():\n    return aux.helper()\n")
    write(os.path.join(_P, "mid2.py"), "import top as T\n\n\ndef go():\n    return T.a.shared()\n")
    _c2, _err = attempt(RG.closure, _TOP, "build", follow=True)
    ck(_err is None and {"aux.helper", "aux.shared"} <= set(_c2 or {}),
       "🔴 `from top import aux; aux.helper()` -> aux.helper, and T.a.shared through hub's "
       "`import aux as a` -> aux.shared (both were dropped without a word)", (sorted(_c2 or {}), _err))

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
    section("2. ONE RECIPE: EACH BUILDER, ITS STAMP AND THE PLANNER AGREE")
    # ══════════════════════════════════════════════════════════════════
    eq(sorted((m, f, mod) for m, f, mod in FR.CODE_BUILT),
       [("card-fb", "fb-model.json", "fb_model.py"), ("card-fb", "fb-props-model.json", "fb_props_model.py")],
       "🔴 the table: both football models, each rebuilt by card-fb (which rebuilds both, the card and "
       "its whys)")
    _CODE = {}
    for _mod, _M in sorted(BUILDERS.items()):
        _CODE[_mod], _err = attempt(RG.builder_fingerprint, _M.__file__)
        ck(_err is None and isinstance(_CODE[_mod], str) and len(_CODE[_mod]) == 16,
           "🔴🔴 %s's real build fingerprints" % _mod, _err)
        eq(_M.builder_fingerprint(), _CODE[_mod], "   %s.builder_fingerprint is the recipe" % _mod[:-3])
        eq(FR.code_fingerprint(_mod), _CODE[_mod],
           "🔴 freshness, which never imports %s, computes the same" % _mod[:-3])
    ck(_CODE["fb_model.py"] != _CODE["fb_props_model.py"], "   two builders, two fingerprints")
    eq(F.stamp({"pricing": {}}, "nfl").get("built_by"), _CODE["fb_model.py"],
       "🔴 fb_model.stamp writes it as `built_by` (the props model's build: test_fb_props_model.py)")


    def built_by_writers(path):
        """Lines of `path` that write a `built_by` key (doc["built_by"] = ..., or a dict literal)."""
        out = []
        for n in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
            if (isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Store)
                    and isinstance(n.slice, ast.Constant) and n.slice.value == "built_by"):
                out.append(n.lineno)
            elif isinstance(n, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "built_by"
                                                 for k in n.keys):
                out.append(n.lineno)
        return out
    _mods = [p for p in glob.glob(os.path.join(ROOT, "*.py")) if not os.path.basename(p).startswith("test_")]
    _writers = sorted(os.path.basename(p) for p in _mods if built_by_writers(p))
    eq(_writers, sorted(mod for _m, _f, mod in FR.CODE_BUILT),
       "🔴🔴 THE CLASS: every module that stamps `built_by` is a row of CODE_BUILT, and every row's "
       "module stamps it (a new model file that names its builder is rebuilt at the next pass)")
    _p = os.path.join(mktree("codemoves-census-"), "x.py")
    write(_p, "def build(doc):\n    doc['built_by'] = 'x'\n    return {'built_by': 'y'}\n")
    eq(built_by_writers(_p), [2, 3], "   (the census sees a planted writer, both spellings)")

    _dt = mktree("codemoves-rows-").replace("\\", "/")
    for _lg in ("nfl", "ncaaf"):
        _d = "%s/data/%s" % (_dt, _lg)
        os.makedirs(_d + "/latest", exist_ok=True)
        open(_d + "/latest/props.json.gz", "wb").close()        # the card rows exist
        _rows = {(m, p.replace("\\", "/").split("/latest/")[-1]) for m, (_k, p), *_ in FR.contract(_d, _dt + "/picks")}
        ck(all((m, f) in _rows for m, f, _mod in FR.CODE_BUILT),
           "🔴 %s: each table row is a contract row of the mode that rebuilds it" % _lg,
           sorted(r for r in _rows if r[0] == "card-fb"))


    def recipe_callers(path):
        """Calls of record_grader's fingerprint / closure on a module's `build` outside its recipe
        (record_grader.builder_fingerprint's own body)."""
        tree_ = ast.parse(open(path, encoding="utf-8").read())
        own = {id(c) for f in ast.walk(tree_) if isinstance(f, ast.FunctionDef)
               and f.name == "builder_fingerprint" and os.path.basename(path) == "record_grader.py"
               for c in ast.walk(f)}
        out = []
        for n in ast.walk(tree_):
            if id(n) in own:
                continue
            if not (isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", None))
                    in ("fingerprint", "closure")):
                continue
            args = list(n.args) + [k.value for k in n.keywords if k.arg == "entry"]
            if any((isinstance(a, ast.Constant) and a.value == RG.BUILDER)
                   or getattr(a, "attr", getattr(a, "id", None)) == "BUILDER" for a in args):
                out.append(n.lineno)
        return out
    _bad = {os.path.basename(p): recipe_callers(p) for p in _mods}
    eq({k: v for k, v in _bad.items() if v}, {},
       "⛔ no module spells the recipe itself (fingerprint(..., \"build\" / BUILDER, ...)): ONE copy")
    write(_p, "import record_grader as RG\nA = RG.fingerprint('m.py', 'build', follow=True)\n"
          "B = RG.fingerprint('m.py', entry=RG.BUILDER)\n")
    eq(recipe_callers(_p), [2, 3], "   (the census sees a planted second copy, positional and by keyword)")

    # ══════════════════════════════════════════════════════════════════
    section("2b. 🔴🔴 THE STAMP NEVER COSTS THE FILE")
    # ══════════════════════════════════════════════════════════════════
    # A fingerprint that cannot be computed must not stop the model building: fb_model.build stamps
    # before it writes, and run_mode would build the card from the old file at the deadline too.
    _keep = RG.builder_fingerprint
    _buf = io.StringIO()
    try:
        def _boom(path):
            raise LookupError("planted: cannot tell which code")
        RG.builder_fingerprint = _boom
        F.builder_fingerprint.cache_clear()
        with contextlib.redirect_stdout(_buf):
            _bb, _err = attempt(RG.built_by, F.__file__)
            _st, _err2 = attempt(F.stamp, {"pricing": {}}, "nfl")
    finally:
        RG.builder_fingerprint = _keep
        F.builder_fingerprint.cache_clear()
    ck(_err is None and _bb is None and "could not be fingerprinted" in _buf.getvalue(),
       "🔴🔴 record_grader.built_by: a fingerprint that raises is None (never a match), and is printed",
       (_bb, _err, _buf.getvalue()[:200]))
    ck(_err2 is None and _st is not None and _st.get("built_by") is None
       and (_st.get("pricing") or {}).get("inputs") == F.inputs_fingerprint(),
       "🔴 ...so fb_model.stamp still returns the document (built_by None, the input stamp written): "
       "the file is written, and its deadline rebuilds it", (_st, _err2))
    eq(F.builder_fingerprint(), _CODE["fb_model.py"], "   (restored)")

    # ══════════════════════════════════════════════════════════════════
    section("3. 🔴 IT CHANGES WITH WHAT A MODEL DOES, AND ONLY THAT")
    # ══════════════════════════════════════════════════════════════════
    _T = mktree("codemoves-code-")
    for p in _mods:
        shutil.copy(p, _T)
    _FM, _PMF = os.path.join(_T, "fb_model.py"), os.path.join(_T, "fb_props_model.py")

    def fp(path=None):
        return RG.builder_fingerprint(path or _FM)

    def inputs():
        return RG.fingerprint(_FM, "features", follow=True) + RG.fingerprint(_FM, "predict", follow=True)

    def fp_with(module, old, new, also=None, of=None):
        path = os.path.join(_T, module)
        src = open(path, encoding="utf-8").read()
        assert src.count(old) == 1, (module, old)
        write(path, src.replace(old, new))
        try:
            return fp(of), (also() if also else None)
        finally:
            write(path, src)

    eq(fp(), _CODE["fb_model.py"], "the planted copy fingerprints as this code")
    eq(fp(_PMF), _CODE["fb_props_model.py"], "   ...both builders")
    _IN = inputs()
    _b, _i = fp_with("fb_model.py", "    if market in (\"spread\", \"total\"):\n        if SIM.get(r.get(\"lg\")):",
                     "    if market in (\"spread\",):\n        if SIM.get(r.get(\"lg\")):", inputs)
    ck(_b != _CODE["fb_model.py"] and _i == _IN,
       "🔴🔴 a change to the PICK RULE (shown_pick) changes it, where the input stamp (#345) cannot see "
       "it: why the file names its whole builder", (_b, _i == _IN))
    ck(fp_with("fb_model.py", "RIDGE = 1.0 ", "RIDGE = 2.0 ")[0] != _CODE["fb_model.py"],
       "🔴 ...so does a constant the fits read (RIDGE)")
    ck(fp_with("one_side.py", '    return "home" if p_home >= 100 - p_home else "away"',
               '    return "home" if p_home > 100 - p_home else "away"')[0] != _CODE["fb_model.py"],
       "🔴 ...and a followed module's rule (one_side.expected_side: one team per game)")
    ck(fp_with("t60r.py", '    s = (g.get("start") or "")[:10]', '    s = (g.get("start") or "")[:7]')[0]
       != _CODE["fb_model.py"],
       "🔴 ...and code reached through another module's import (t60r.kick, read as FM.t60r.kick too)")
    # ⛔ whatever the switch holds (test_props_switch_branch.py runs this file on a switched branch too)
    ck(fp_with("card_fb.py", "PROPS_SEASONS = {", 'PROPS_SEASONS = {"planted": "a changed switch",',
               of=_PMF)[0] != _CODE["fb_props_model.py"],
       "🔴🔴 a merged PROPS switch (T74: card_fb.PROPS_SEASONS) changes the props model's")
    ck(fp_with("fb_model.py", "def build(lg=None, root=None, out=None, extra_top=None, extra_players=None, now=None):",
               "def build(lg=None, root=None, out=None, extra_top=None, extra_players=None, now=None):\n"
               "    # a comment changes nothing")[0] == _CODE["fb_model.py"],
       "   ✅ a comment edit does not (no needless rebuild)")
    ck(fp_with("fb_model.py", '    "spread": ["own_margin", "h2h", "form", "possession", "personnel", "neutral", "dome"],',
               '    "spread": ["own_margin", "h2h"],')[0] == _CODE["fb_model.py"],
       "   ✅ nor does a name build never reaches (FEATURES, a label list)")

    # ══════════════════════════════════════════════════════════════════
    section("4. 🔴🔴 code_moves: A FOOTBALL MODEL FILE BUILT BY OTHER CODE GETS card-fb")
    # ══════════════════════════════════════════════════════════════════
    _D = mktree("codemoves-tree-").replace("\\", "/")
    _OK = {"fb-model.json": {"built_by": _CODE["fb_model.py"]},
           "fb-props-model.json": {"built_by": _CODE["fb_props_model.py"]}}

    def tree(lg, doc=None, raw=None, props=_OK["fb-props-model.json"]):
        """A league's latest/ with fb-model.json (`doc` or `raw`) and fb-props-model.json (`props`)."""
        d = "%s/%s/data/%s" % (_D, lg, lg) if lg != "mlb" else "%s/mlb/data" % _D
        shutil.rmtree(os.path.dirname(d) if lg != "mlb" else d, ignore_errors=True)
        os.makedirs(d + "/latest", exist_ok=True)
        if doc is not None or raw is not None:
            write(d + "/latest/fb-model.json", raw if raw is not None else json.dumps(doc))
        if props is not None:
            write(d + "/latest/fb-props-model.json", json.dumps(props))
        return d

    eq(FR.code_moves(tree("nfl", _OK["fb-model.json"])), set(),
       "✅ NFL, both files built by this code: nothing planned")
    eq(FR.code_moves(tree("nfl", {"built_by": "0" * 16})), {"card-fb"},
       "🔴🔴 NFL, the game model built by other code: card-fb at the next pass")
    eq(FR.code_moves(tree("nfl", _OK["fb-model.json"], props={"built_by": "0" * 16})), {"card-fb"},
       "🔴🔴 NFL, the PROPS model built by other code (a merged props switch): card-fb too")
    eq(FR.code_moves(tree("ncaaf", {"built_by": "f" * 16, "champion": "HC"})), {"card-fb"},
       "🔴🔴 college too (rule 6)")
    eq(FR.code_moves(tree("ncaaf", _OK["fb-model.json"])), set(), "   ✅ ...and nothing when both match")
    eq(FR.code_moves(tree("ncaaf", {"pricing": {"inputs": "x"}}, props={"picks": []})), {"card-fb"},
       "🔴 files from before the stamp existed (every file on main the day this merges) are rebuilt once")
    eq(FR.code_moves(tree("nfl", raw="{\"built_by\": ")), {"card-fb"},
       "🔴 a file whose stamp cannot be read was not built by this code: rebuilt")
    eq(FR.code_moves(tree("nfl", raw="[1, 2]")), {"card-fb"}, "   ...nor one that is not an object")
    eq(FR.code_moves(tree("nfl", props=None)), set(), "   missing files are their own rows' business (stale already)")
    eq(FR.code_moves(tree("mlb", {"built_by": "0" * 16})), set(), "⛔ MLB builds no football model file")
    eq(FR.code_moves(tree("nfl", {"built_by": "0" * 16}).replace("/", os.sep)), {"card-fb"},
       "   the league comes from the path, either separator")
    _alone = mktree("codemoves-alone-")
    _buf = io.StringIO()
    with contextlib.redirect_stdout(_buf):
        _got, _err = attempt(FR.code_moves, tree("nfl", {"built_by": "0" * 16}), root=_alone)
    ck(_err is None and _got == set() and _buf.getvalue() == "",
       "⛔ a sandbox holding freshness.py alone (no model file beside it) plans nothing, imports "
       "nothing and says nothing", (_got, _err, _buf.getvalue()))
    _bare = mktree("codemoves-nobuild-")
    write(os.path.join(_bare, "fb_model.py"), "def other():\n    return 1\n")
    _buf = io.StringIO()
    with contextlib.redirect_stdout(_buf):
        _got, _err = attempt(FR.code_moves, tree("nfl", {"built_by": "0" * 16}), root=_bare)
    ck(_err is None and _got == set() and "fb-model.json: the code that builds it could not be fingerprinted"
       in _buf.getvalue(),
       "⛔ code that cannot be fingerprinted plans nothing, never raises into converge, and SAYS so "
       "(the model's own stamp is then None: §2b)", (_got, _err, _buf.getvalue()[:200]))

    # ══════════════════════════════════════════════════════════════════
    section("4b. ⛔ freshness.py's ONE REPO IMPORT: record_grader, LAZY, BESIDE A MODEL ONLY")
    # ══════════════════════════════════════════════════════════════════
    _fsrc = ast.parse(open(FR.__file__, encoding="utf-8").read())
    _beside = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ROOT, "*.py"))}
    _top_imp = [a.name.split(".")[0] for s in _fsrc.body if isinstance(s, ast.Import) for a in s.names]         + [s.module.split(".")[0] for s in _fsrc.body if isinstance(s, ast.ImportFrom) and s.module]
    eq(sorted(set(_top_imp) & _beside), [], "⛔ at load freshness.py imports no repo module (sandboxes copy it alone)")
    _inner = []
    for _fn in (n for n in ast.walk(_fsrc) if isinstance(n, ast.FunctionDef)):
        for s in ast.walk(_fn):
            if isinstance(s, (ast.Import, ast.ImportFrom)):
                for nm in ([a.name for a in s.names] if isinstance(s, ast.Import) else [s.module or ""]):
                    if nm.split(".")[0] in _beside:
                        _inner.append((_fn.name, nm))
    eq(_inner, [("code_fingerprint", "record_grader")],
       "⛔ ...and inside a function only record_grader, only in code_fingerprint")
    _sb = mktree("codemoves-sandbox-")
    for _f in ("freshness.py", "fb_model.py"):
        shutil.copy(os.path.join(ROOT, _f), _sb)
    _tr = tree("nfl", {"built_by": "0" * 16})
    _r = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c",
                         "import sys; sys.path.insert(0, sys.argv[1]); import freshness as F; "
                         "print('MOVES', sorted(F.code_moves(sys.argv[2])))", _sb, _tr],
                        capture_output=True, text=True, encoding="utf-8", timeout=120,
                        env=dict(os.environ, PYTHONUTF8="1"))
    ck(_r.returncode == 0 and "MOVES []" in _r.stdout and "could not be fingerprinted" in _r.stdout,
       "⛔ a sandbox with freshness.py and fb_model.py but no record_grader.py: the planner runs, plans "
       "nothing and says why", (_r.returncode, _r.stdout[-300:], _r.stderr[-300:]))

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
           "🔴🔴 every row fresh, a model file built by other code: the pass runs card-fb")
        eq(FR.plan(tree("nfl", _OK["fb-model.json"]), _D + "/picks")[0], [],
           "   ✅ ...and nothing when this code built both")
    finally:
        FR.survey, FR.slate_moves, FR.every_pass, FR.injury_retry = _keep
    import datetime
    _now = datetime.datetime(2026, 11, 10, 3, 0, tzinfo=datetime.timezone.utc)

    def row(doc, props):
        d = tree("ncaaf", doc, props=props)
        # the card's rows exist once the league has a props board ("cannot exist yet is not late")
        with gzip.open(d + "/latest/props.json.gz", "wt", encoding="utf-8") as fh:
            json.dump({"built_at": "2026-11-10T00:10:00Z", "games": []}, fh)
        rows = FR.survey(d, _D + "/picks", _now)
        return [{k: v for k, v in r.items() if k != "path"} for r in rows
                if r["path"].replace("\\", "/").split("/latest/")[-1] in ("fb-model.json", "fb-props-model.json")]
    _at = "2026-11-10T00:18:12Z"
    _match = row(dict(_OK["fb-model.json"], built_at=_at), dict(_OK["fb-props-model.json"], built_at=_at))
    _other = row({"built_by": "0" * 16, "built_at": _at}, {"built_by": "1" * 16, "built_at": _at})
    ck(len(_match) == 2 and _match == _other,
       "⛔ planned, NEVER MARKED STALE: the survey's two model-file rows are the same either way (the "
       "gate, the watchdog and the page see no change; the deadline is unchanged)", (_match, _other))
    ck(_match and not any(r["stale"] or r["unhealthy"] for r in _match),
       "   (built 00:18Z, after the last 13:30Z deadline: on time and healthy)", _match)
finally:
    for _d in TMP:
        shutil.rmtree(_d, ignore_errors=True)
