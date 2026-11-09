#!/usr/bin/env python3
r"""🔴🔴 A FIT ANSWERS ONLY THE QUESTION IT WAS FITTED ON. `[2026-11-09]`

Found while scoping college's first champion switch (HC, PR #339): `game_lines_fb` prices the alt
ladders from the fits STORED in fb-model.json, asked with THIS code's inputs (`fb_model.features`).
In the hours between Sam's merge and the next `card-fb` (which rebuilds fb-model.json), the
`props-player` and `alt-lines` passes rebuild that tab from the OLD file. HC gives 3 inputs; the
stored college fits take 7 (spread) and 6 (total). `fb_model.predict` lined the two up with
`range(len(x))` and `zip`, without a word. Measured on stored data (Kent State @ Bowling Green
-5.5): 0.516 in the window, against 0.493 before and 0.501 rebuilt. No switch had merged yet; had
one, every college rung's % and edge would have been wrong, frozen and later graded. And a change
that keeps the inputs' NUMBER but not their meaning (2026-10-11: the first input became the
model's own margin) would have done the same with no length to notice.

✅ THE CLASS, three ways a stored fit can be asked the wrong question, each refused:
   1. another champion: fb-model.json's `champion` (fb_model.stamp) against the one named;
   2. other input code: `pricing.inputs`, the fingerprint of `features` (and all it reaches) and
      `predict`, against this code's (`fb_model.inputs_fingerprint`); a comment edit is not one;
   3. another length: `fb_model.predict` and the props model's `s1_mean` raise.
   `game_lines_fb.stored_fits` is the ONE reader of the stored fits (the census below) and checks
   1 and 2; refused, the rungs carry no model % until fb-model.json is rebuilt
   (test_game_lines_fb.py §3 drives the tab; test_fb_model.py, that build writes both stamps).

⛔ A TEST ASKS THE CODE: planted fits and planted source only, no live data.

# @vacuity 🔴🔴 fb_model.predict refuses a vector of another length
#   file: fb_model.py
#   find:     if not (len(x) == len(m["mu"]) == len(m["sd"]) == len(m["w"]) - 1):
#   with:     if False:
#
# @vacuity 🔴 the props model's predictor refuses one too
#   file: fb_props_model.py
#   find:     if not (len(x) == len(m["mu"]) == len(m["sd"]) == len(m["w"])):    # ⛔ fb_model.predict's rule
#   with:     if False:
#
# @vacuity 🔴🔴 stored fits made for another champion are not used
#   file: game_lines_fb.py
#   find:     if fits and made != names:
#   with:     if False:
#
# @vacuity 🔴🔴 stored fits made by other input code are not used
#   file: game_lines_fb.py
#   find:     if fits and pricing.get("inputs") != F.inputs_fingerprint():
#   with:     if False:
#
# @vacuity 🔴 stamp writes the input code's fingerprint
#   file: fb_model.py
#   find:     doc["pricing"]["inputs"] = inputs_fingerprint()
#   with:     pass
#
# @vacuity 🔴 stamp writes the champion that fitted them
#   file: fb_model.py
#   find:         doc["champion"] = CHAMPION[lg]
#   with:         pass
#
# @vacuity 🔴 the fingerprint covers the code that ASKS a fit too
#   file: fb_model.py
#   find:             + record_grader.fingerprint(here, "predict", follow=True))
#   with:             + "")
"""
import ast
import glob
import math
import os
import random
import re
import shutil
import tempfile
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import fb_challengers as FC  # noqa: E402
import fb_model as F  # noqa: E402
import fb_props_model as PM  # noqa: E402
import game_lines_fb as G  # noqa: E402
import record_grader as RG  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402


def raises(fn, *a):
    try:
        fn(*a)
    except ValueError:
        return True
    return False


# ══════════════════════════════════════════════════════════════════════
section("1. fb_model.predict: THE LENGTH IT WAS FITTED ON, OR IT RAISES")
# ══════════════════════════════════════════════════════════════════════
_rng = random.Random(7)
_X = [[_rng.gauss(0, 1) for _ in range(3)] for _ in range(max(F.MIN_TRAIN, 60) + 20)]
_y = [1 if x[0] + 0.5 * x[1] + _rng.gauss(0, 1) > 0 else 0 for x in _X]
m3 = F.fit(_X, _y, zmax=F.ZMAX)
ck(m3 is not None and len(m3["mu"]) == 3 and len(m3["w"]) == 4, "a planted 3-input fit", m3)
_x = [0.4, -0.2, 1.1]
_z = [1.0] + [max(-F.ZMAX, min(F.ZMAX, (_x[j] - m3["mu"][j]) / m3["sd"][j])) for j in range(3)]
_want = 1.0 / (1.0 + math.exp(-sum(a * b for a, b in zip(m3["w"], _z))))
ck(abs(F.predict(m3, _x) - _want) < 1e-12, "✅ asked about 3 inputs it answers, as before", (F.predict(m3, _x), _want))
ck(raises(F.predict, m3, _x[:2]), "🔴🔴 asked about 2 inputs (a champion with fewer) it RAISES, never a quiet %")
ck(raises(F.predict, m3, _x + [0.0, 0.0]), "🔴 asked about 5 it raises too")
ck(raises(F.predict, dict(m3, w=m3["w"][:3]), _x), "   ...and a fit whose weights do not match its inputs raises")
ck(raises(F.predict, dict(m3, sd=m3["sd"][:2]), _x), "   ...as does one whose spreads do not")

# ══════════════════════════════════════════════════════════════════════
section("2. THE PROPS MODEL'S PREDICTOR (s1_mean): THE SAME RULE")
# ══════════════════════════════════════════════════════════════════════
_s = PM.Sums(k=2)
for _ in range(80):
    a, b = _rng.gauss(0, 1), _rng.gauss(0, 1)
    _s.add([a, b], 3.0 + a - 0.5 * b + _rng.gauss(0, 0.3))
ms = _s.solve()
ck(ms is not None and len(ms["mu"]) == 2 and len(ms["w"]) == 2, "a planted 2-input props fit", ms)
_v = ms["ybar"] + sum(ms["w"][j] * (([0.3, -1.0])[j] - ms["mu"][j]) / ms["sd"][j] for j in range(2))
ck(abs(PM.s1_mean(ms, [0.3, -1.0]) - _v) < 1e-12, "✅ asked about 2 inputs it answers, as before")
ck(raises(PM.s1_mean, ms, [0.3]), "🔴 asked about 1 it RAISES (it used to read the first weight alone)")
ck(raises(PM.s1_mean, ms, [0.3, -1.0, 2.0]), "   ...asked about 3 it raises (no IndexError, the one error)")

# ══════════════════════════════════════════════════════════════════════
section("3. game_lines_fb.stored_fits: ONLY THE CHAMPION THAT FITTED THEM")
# ══════════════════════════════════════════════════════════════════════
_fits = {"spread": m3, "total": m3}
_name = next(n for n in sorted(FC.CHALLENGERS) if FC.CHALLENGERS[n]["league"] == "ncaaf")
_other = next(n for n in sorted(FC.CHALLENGERS) if FC.CHALLENGERS[n]["league"] == "ncaaf" and n != _name)
_was = F.CHAMPION.get("ncaaf")


_IN = F.inputs_fingerprint()


def ask(made, names, inputs=_IN):
    fm = ({"pricing": {"models": _fits, "games": []} | ({"inputs": inputs} if inputs else {})}
          | ({"champion": made} if made else {}))
    F.CHAMPION["ncaaf"] = names
    try:
        return G.stored_fits(fm, "ncaaf")
    finally:
        F.CHAMPION["ncaaf"] = _was


ck(ask(None, None) == (_fits, None), "✅ today's model's file, read by today's model: used")
ck(ask(_name, _name) == (_fits, None), "✅ %s's file, read with %s named: used" % (_name, _name))
_r = ask(None, _name)
ck(_r[0] == {} and "fitted for champion None; this code names %s" % _name in (_r[1] or ""),
   "🔴🔴 the hour after a switch: today's model's file, read with %s named, is NOT used, and says why" % _name, _r)
_r = ask(_name, None)
ck(_r[0] == {} and bool(_r[1]), "🔴 a file fitted by %s, read once no champion is named (a switch undone): not used" % _name, _r)
_r = ask(_name, _other)
ck(_r[0] == {} and bool(_r[1]), "🔴 one champion's file read by another: not used", _r)
_r = ask(None, None, inputs="0" * 32)
ck(_r[0] == {} and "made by other input code" in (_r[1] or ""),
   "🔴🔴 the same champion, but the fits were made by other input code (a same-length change): not used", _r)
_r = ask(None, None, inputs=None)
ck(_r[0] == {} and "made by other input code" in (_r[1] or ""),
   "🔴 a file with no input stamp (written before the stamp existed) is not trusted either", _r)
eq(G.stored_fits({}, "ncaaf"), ({}, None), "   no file, no fits, nothing to refuse")
eq(G.stored_fits({"pricing": {}}, "ncaaf"), ({}, None), "   a file with no fits: nothing to refuse")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 CENSUS: stored_fits IS THE ONE READER OF THE STORED FITS")
# ══════════════════════════════════════════════════════════════════════
READ = re.compile(r"""(?:\.get\(\s*|\[\s*)['"]models['"]""")


def readers(src):
    """-> [(function, line)] for every read of a "models" key outside game_lines_fb.stored_fits."""
    tree = ast.parse(src)
    spans = [(n.name, n.lineno, n.end_lineno) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        code = line.split("#", 1)[0]
        if READ.search(code):
            inner = [s for s in spans if s[1] <= i <= s[2]]
            fn = min(inner, key=lambda s: s[2] - s[1])[0] if inner else "<module>"
            out.append((fn, i))
    return out


ck(readers("def stored_fits(fm, lg):\n    return fm.get('pricing', {}).get('models')\n") == [("stored_fits", 2)],
   "the census sees a read (planted)")
ck(readers("def curve(fm):\n    m = fm['pricing']['models']['spread']\n") == [("curve", 2)],
   "   ...in either spelling (planted)")
ck(readers("x = 1  # pricing.get('models')\n") == [], "   ...and never a comment (planted)")
_bad = []
for path in sorted(glob.glob(os.path.join(ROOT, "*.py"))):
    base = os.path.basename(path)
    if base.startswith("test_"):
        continue
    for fn, line in readers(open(path, encoding="utf-8").read()):
        if (base, fn) != ("game_lines_fb.py", "stored_fits"):
            _bad.append("%s:%d (%s)" % (base, line, fn))
ck(not _bad, "🔴🔴 no module reads fb-model.json's stored fits except through game_lines_fb.stored_fits "
   "(a second reader would ask an old champion's fit again)", _bad)
_src = open(os.path.join(ROOT, "game_lines_fb.py"), encoding="utf-8").read()
ck(("stored_fits", ) == tuple(sorted({fn for fn, _l in readers(_src)})),
   "   ...and stored_fits itself still reads them (the census is not empty)", readers(_src))

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE STAMPS: fb_model.stamp WRITES BOTH, AND THE FINGERPRINT FOLLOWS THE INPUT CODE")
# ══════════════════════════════════════════════════════════════════════
try:
    F.CHAMPION["ncaaf"] = None
    _d0 = F.stamp({"pricing": {"models": _fits}}, "ncaaf")
    F.CHAMPION["ncaaf"] = _name
    _d1 = F.stamp({"pricing": {"models": _fits}}, "ncaaf")
finally:
    F.CHAMPION["ncaaf"] = _was
ck("champion" not in _d0 and _d0["pricing"]["inputs"] == _IN and len(_IN) == 32,
   "🔴 no champion named: no `champion` key, and the input code's fingerprint in `pricing.inputs`", _d0)
ck(_d1.get("champion") == _name and _d1["pricing"]["inputs"] == _IN,
   "🔴 %s named: `champion` says so" % _name, {k: _d1.get(k) for k in ("champion",)})
ck(G.stored_fits(_d0, "ncaaf") == (_fits, None), "   ✅ a file stamped by this code is read back as used")

_T = tempfile.mkdtemp(prefix="fitshape-")
try:
    for p in glob.glob(os.path.join(ROOT, "*.py")):
        if not os.path.basename(p).startswith("test_"):
            shutil.copy(p, _T)
    _FM = os.path.join(_T, "fb_model.py")

    def fp():
        return RG.fingerprint(_FM, "features", follow=True) + RG.fingerprint(_FM, "predict", follow=True)

    def fp_with(path, old, new):
        src = open(path, encoding="utf-8").read()
        assert src.count(old) == 1, (path, old)
        open(path, "w", encoding="utf-8").write(src.replace(old, new))
        try:
            return fp()
        finally:
            open(path, "w", encoding="utf-8").write(src)

    eq(fp(), _IN, "the planted copy fingerprints as this code")
    ck(fp_with(_FM, "return [z(None if om is None or M is None else om - M) / 10.0,",
               "return [z(None if om is None or M is None else om - M) / 7.0,") != _IN,
       "🔴🔴 a SAME-LENGTH change to an input's meaning changes the stamp (the 2026-10-11 kind)")
    ck(fp_with(os.path.join(_T, "fb_challengers.py"), "def extend(",
               "def extend(*_a, **_k):\n    return None\n\n\ndef _was_extend(") != _IN,
       "🔴 ...so does a change to a challenger's inputs (fb_challengers.extend, reached from features)")
    ck(fp_with(_FM, '    zmax = m.get("zmax")', '    zmax = None') != _IN,
       "🔴 ...and a change to how a fit is ASKED (predict)")
    ck(fp_with(_FM, "def features(r, market, M=None, T=None):",
               "def features(r, market, M=None, T=None):\n    # a comment changes nothing") == _IN,
       "   ✅ a comment edit does not (no needless refusal)")
finally:
    shutil.rmtree(_T, ignore_errors=True)
