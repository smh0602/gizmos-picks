#!/usr/bin/env python3
"""💾 A DATED ARCHIVE OF A latest/ FILE IS THAT FILE'S BYTES, SO GIT STORES IT ONCE.
`[2026-11-08]`

The defect: `dossier_fb.build` writes `latest/dossiers.json.gz`, then
`daystore.archive` dumps the SAME document again to
`<date>/dossiers/<HHMM>.json.gz`. A gzip's header carries its write time and
its temporary file name, so the second dump is a second, different blob, and
git cannot delta a gzip: every `card-fb` run stored the dossier twice. Measured
on origin/main, 2026-10-25 to 11-08: 267 archives, 63.8 MB of new gzip; every
one of 27 sampled equal in content to its own commit's latest file.

  §1  daystore.archive(..., same_as=latest) copies latest's BYTES when that file
      stores the document (~~exactly~~ `[2026-11-10]` apart from its top-level
      stamps), and dumps it as before on any other difference; write-once and the
      picks/ refusal are unchanged.
  §2  the CLASS: every function in this repo that writes a document to a
      latest/ gzip AND archives that same document passes `same_as`. A new
      one is red until it does (the dossier is the only one today).
  §3  `[2026-11-17]` a same_as copy the DAY already holds is not written again: a
      stamp-only pass kept latest's bytes, so its copy was the previous archive's
      bytes under a new HHMM name (one blob in git, a full file in the working tree
      and on the Pages site: 63 dossier copies, 16.5 MB, measured on origin/main
      2026-11-17). Only the same_as copy, only within one day, only against the
      reading just before; every reader of a day finds the same bytes it read before.

⛔ A TEST ASKS THE CODE: every tree here is planted.

# @vacuity 🔴 the archive copies latest's bytes (the dossier was stored twice)
#   file: daystore.py
#   find:     buf = same_bytes(same_as, doc) if same_as else None
#   with:     buf = None
#
# @vacuity 🔴 a latest file that stores another document is not copied
#   file: daystore.py
#   find:         if stored == json.loads(json.dumps(doc)) or (
#   with:         if True or (
#
# @vacuity 🔴 [2026-11-10] a latest file that differs only in its stamps is copied (a stamp-only run)
#   file: daystore.py
#   find:                 isinstance(stored, dict) and isinstance(doc, dict) and _F.same_but_stamps(stored, doc)):
#   with:                 False):
#
# @vacuity 🔴 the census finds a latest/ write beside an archive of the same document
#   file: dossier_fb.py
#   find:     arch, _wrote = daystore.archive(doc, data, "dossiers", log=log, same_as=p)
#   with:     arch, _wrote = daystore.archive(doc, data, "dossiers", log=log)
#
# @vacuity 🔴 [2026-11-17] a stamp-only pass writes no second copy of the day's previous archive
#   file: daystore.py
#   find:         if prev and _bytes(prev) == buf:
#   with:         if False:
#
# @vacuity 🔴 [2026-11-17] the skip never reaches into another day: the next day's first pass writes
#   file: daystore.py
#   find:     return os.path.join(d, names[-1]) if names else None
#   with:     return os.path.join(d, names[-1]) if names else next(iter(sorted(__import__("glob").glob(os.path.join(os.path.dirname(os.path.dirname(d)), "*", os.path.basename(d), "*.json.gz")), reverse=True)), None)
#
# @vacuity 🔴 [2026-11-17] it compares with the reading just before, never an earlier one (A, B, A is three)
#   file: daystore.py
#   find:     return os.path.join(d, names[-1]) if names else None
#   with:     return os.path.join(d, names[0]) if names else None
#
# @vacuity 🔴 [2026-11-17] a dump is never skipped: one file per pass (the news archive's freshness row)
#   file: daystore.py
#   find:     if os.path.exists(p):
#   with:     if os.listdir(os.path.dirname(p)):
"""
import ast
import datetime
import glob
import gzip
import json
import os
import shutil
import sys
import tempfile
import warnings

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, eq, section  # noqa: E402

import daystore as D  # noqa: E402

UTC = datetime.timezone.utc
WHEN = datetime.datetime(2026, 11, 4, 17, 10, tzinfo=UTC)     # ⛔ the pinned clock
TMP = tempfile.mkdtemp(prefix="archive-bytes-")
DOC = {"league": "nfl", "built_at": "2026-11-04T17:10:00Z", "dossiers": [{"board_id": 7, "sections": []}],
       "by_id": {7: "int keys read back as strings"}}


def latest(root, doc):
    """latest/x.json.gz written the way dossier_fb writes it (a real header)."""
    p = os.path.join(root, "latest", "x.json.gz")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with gzip.open(p, "wt") as fh:
        json.dump(doc, fh)
    return p


def blob(p):
    with open(p, "rb") as fh:
        return fh.read()


# ══════════════════════════════════════════════════════════════════════
section("1. daystore.archive(same_as=): THE LATEST FILE'S BYTES, OR A DUMP AS BEFORE")
# ══════════════════════════════════════════════════════════════════════
_r = os.path.join(TMP, "same")
_lp = latest(_r, DOC)
_ap, _w = D.archive(DOC, _r, "dossiers", log=lambda *a: None, when=WHEN, same_as=_lp)
eq((_w, os.path.relpath(_ap, _r).replace(os.sep, "/")), (True, "2026-11-04/dossiers/1710.json.gz"),
   "the archive is written at its dated path")
ck(blob(_ap) == blob(_lp), "🔴 ...as latest's exact bytes: one blob for git, not two",
   "%d vs %d bytes" % (len(blob(_ap)), len(blob(_lp))))
_r2 = os.path.join(TMP, "dump")
_ap2, _ = D.archive(DOC, _r2, "dossiers", log=lambda *a: None, when=WHEN)
ck(blob(_ap2) != blob(_lp) and json.load(gzip.open(_ap2, "rt")) == json.load(gzip.open(_lp, "rt")),
   "   (control) the same document dumped again is a DIFFERENT blob: the defect, measured here",
   "if this ever passes as equal bytes, the check above proves nothing")

# `[2026-11-10]` ~~a stamp apart is ANOTHER document, not copied~~. #343's exact-match rule is
#    RELAXED for top-level stamps, on purpose (my rule of 11-08, not one Sam set; the PR puts the
#    choice to him): the latest file is now collect.write's, which adds `written_at`, and keeps its
#    bytes on a run that moved only its stamps (its heartbeat carries them). Compared exactly,
#    EVERY run would dump a second full gzip again. ⚠️ What is given up: a stamp-only run's
#    archive carries the built_at / written_at of that content's first build, which can be days
#    before its dated path. Nothing reads a stamp from a dossier archive (shadow_fb picks by file
#    name and reads `dossiers`); §2 holds the dossier to being the only such caller. The content
#    rule is unchanged: any difference below the top-level stamps still dumps.
_r3 = os.path.join(TMP, "stamps")
_lp3 = latest(_r3, dict(DOC, built_at="2026-11-04T16:00:00Z", written_at="2026-11-04T16:00:05Z"))
_ap3, _ = D.archive(DOC, _r3, "dossiers", log=lambda *a: None, when=WHEN, same_as=_lp3)
ck(blob(_ap3) == blob(_lp3),
   "🔴 a latest file that stores this document APART FROM ITS STAMPS is copied: one blob (a stamp-only "
   "run, and collect.write's written_at)")
for _i, (_what, _other) in enumerate((
        ("a top-level field", dict(DOC, league="ncaaf")),
        ("a value inside a section", dict(DOC, dossiers=[{"board_id": 7, "sections": [1]}])),
        ("a key it lacks", dict(DOC, extra=1)),
        ("a stamp-named key BELOW the top", dict(DOC, dossiers=[{"board_id": 7, "sections": [],
                                                              "built_at": "2026-11-04T16:00:00Z"}])))):
    _ro = os.path.join(TMP, "other-%d" % _i)
    _lpo = latest(_ro, _other)
    _apo, _ = D.archive(DOC, _ro, "dossiers", log=lambda *a: None, when=WHEN, same_as=_lpo)
    eq(json.load(gzip.open(_apo, "rt")), json.loads(json.dumps(DOC)),
       "🔴 a latest file whose CONTENT differs (%s) is not copied: the archive is this doc" % _what)

# ...and the run it is for: collect.write keeps latest on a stamp-only run, and the archive of
#    that run is the same blob, so the run adds no gzip at all
import collect as _C  # noqa: E402
import freshness as _F  # noqa: E402
_r5 = os.path.join(TMP, "kept")
_lp5 = os.path.join(_r5, "latest", "dossiers.json.gz")
_C.write(_lp5, dict(DOC, built_at="2026-11-04T16:00:00Z"), compress=True, heartbeat=True)
_first = blob(_lp5)
_C.write(_lp5, dict(DOC, built_at="2026-11-04T17:10:00Z"), compress=True, heartbeat=True)
ck(blob(_lp5) == _first and os.path.exists(_F.heartbeat_path(_lp5)),
   "(a stamp-only run through collect.write: latest kept, its heartbeat written)")
_ap5, _ = D.archive(dict(DOC, built_at="2026-11-04T17:10:00Z"), _r5, "dossiers", log=lambda *a: None,
                    when=WHEN, same_as=_lp5)
ck(blob(_ap5) == blob(_lp5), "🔴🔴 ...and that run's archive is latest's bytes: the run adds no new blob")
for _name, _make in (("missing", None), ("corrupt", b"not a gzip"), ("truncated", None)):
    _rr = os.path.join(TMP, _name)
    os.makedirs(os.path.join(_rr, "latest"))
    _pp = os.path.join(_rr, "latest", "x.json.gz")
    if _name == "corrupt":
        open(_pp, "wb").write(_make)
    elif _name == "truncated":
        open(_pp, "wb").write(blob(_lp)[:40])
    _aa, _ww = D.archive(DOC, _rr, "dossiers", log=lambda *a: None, when=WHEN, same_as=_pp)
    ck(_ww and json.load(gzip.open(_aa, "rt")) == json.loads(json.dumps(DOC)),
       "   a %s latest file: the document is dumped as before, never an error" % _name)

_seen = []
_ap4, _w4 = D.archive(dict(DOC, built_at="later"), _r, "dossiers", log=_seen.append, when=WHEN, same_as=_lp)
ck(not _w4 and blob(_ap4) == blob(_lp) and "already exists" in " ".join(_seen),
   "🔴 write-once is unchanged: a second run in the same minute leaves the earlier reading alone")
try:
    D.archive(DOC, os.path.join(TMP, "picks"), "dossiers", when=WHEN, same_as=_lp)
    _refused = False
except ValueError:
    _refused = True
ck(_refused, "   ...and picks/ is still refused")


# ══════════════════════════════════════════════════════════════════════
section("2. THE CLASS: A latest/ WRITE AND AN ARCHIVE OF THE SAME DOCUMENT PASS same_as")
# ══════════════════════════════════════════════════════════════════════
def _consts(node):
    return [c.value for c in ast.walk(node) if isinstance(c, ast.Constant) and isinstance(c.value, str)]


def _names_latest(node, env, depth=0):
    """Does the path expression `node` name a latest/ file (a literal, or a
    name this function or the module bound to one)?"""
    if any("latest" in c for c in _consts(node)):
        return True
    return depth < 4 and any(_names_latest(v, env, depth + 1)
                             for n in ast.walk(node) if isinstance(n, ast.Name)
                             for v in env.get(n.id, ()) if v is not node)


def _env(nodes):
    out = {}
    for n in nodes:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out.setdefault(t.id, []).append(n.value)
    return out


def census(root):
    """-> (members, flagged): every (module, function) that writes document X to a
    latest/ gzip AND archives X through daystore; those without `same_as`."""
    members, flagged = [], []
    for f in sorted(glob.glob(os.path.join(root, "*.py")) + glob.glob(os.path.join(root, "research", "*.py"))):
        rel = os.path.relpath(f, root).replace(os.sep, "/")
        if os.path.basename(f).startswith("test_") or rel == "daystore.py":
            continue
        src = open(f, encoding="utf-8").read()
        if "daystore" not in src:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(src)
        alias = {a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.Import)
                 for a in n.names if a.name == "daystore"}
        bare = {a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
                and n.module == "daystore" for a in n.names if a.name == "archive"}
        menv = _env(tree.body)
        for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            nodes = list(ast.walk(fn))
            env = dict(menv, **_env(nodes))
            arcs = [n for n in nodes if isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.Name)
                    and ((isinstance(n.func, ast.Attribute) and n.func.attr == "archive"
                          and isinstance(n.func.value, ast.Name) and n.func.value.id in alias)
                         or (isinstance(n.func, ast.Name) and n.func.id in bare))]
            if not arcs:
                continue
            # the documents this function dumps into a latest/ gzip: json.dump(X, fh) inside
            # `with gzip.open(<latest path>) as fh`, or write(<latest path>, X, compress=True)
            to_latest = set()
            for w in nodes:
                if isinstance(w, (ast.With, ast.AsyncWith)):
                    gz = [it for it in w.items if isinstance(it.context_expr, ast.Call)
                          and getattr(it.context_expr.func, "attr", None) == "open"
                          and getattr(it.context_expr.func.value, "id", None) == "gzip"
                          and it.context_expr.args and _names_latest(it.context_expr.args[0], env)]
                    if gz:
                        for d in ast.walk(w):
                            if isinstance(d, ast.Call) and getattr(d.func, "attr", None) == "dump" \
                                    and d.args and isinstance(d.args[0], ast.Name):
                                to_latest.add(d.args[0].id)
                if isinstance(w, ast.Call) and (getattr(w.func, "attr", None) or getattr(w.func, "id", None)) \
                        == "write" and len(w.args) > 1 and isinstance(w.args[1], ast.Name) \
                        and _names_latest(w.args[0], env) \
                        and any(k.arg == "compress" and getattr(k.value, "value", None) is True for k in w.keywords):
                    to_latest.add(w.args[1].id)
            for a in arcs:
                if a.args[0].id in to_latest:
                    key = "%s:%s line %d" % (rel, fn.name, a.lineno)
                    members.append(key)
                    if not any(k.arg == "same_as" for k in a.keywords):
                        flagged.append(key)
    return members, flagged


_mem, _flag = census(ROOT)
ck(any(m.startswith("dossier_fb.py:build ") for m in _mem),
   "⚠️ the census finds the dossier's latest write and its archive (%s)" % _mem,
   "⛔ if it finds nothing, 'none flagged' below checks nothing (rule 67)")
eq(_flag, [], "🔴🔴 every latest/ gzip that is also archived is archived as its own bytes (same_as)")
# `[2026-11-10]` ...and the dossier is the ONLY such caller: its archive carries latest's stamps when
#    only they moved, which is safe because no reader takes a stamp from a dossier archive. Other
#    kinds' archives are read for `pulled_at` (props snapshots, the alt-line units), so a new
#    caller is a decision: name it here, with who reads its archive's stamps.
eq(sorted({m.split(" ")[0] for m in _mem}), ["dossier_fb.py:build"],
   "⛔ the only latest/ gzip archived through same_as is the dossier (a new one says who reads "
   "its archive's stamps)")

# rule 67: the census bites on planted modules
_pl = os.path.join(TMP, "census")
os.makedirs(os.path.join(_pl, "research"))
with open(os.path.join(_pl, "bad.py"), "w", encoding="utf-8") as fh:
    fh.write("import gzip, json, os, daystore\n\ndef build(data, doc):\n"
             "    p = os.path.join(data, 'latest', 'x.json.gz')\n"
             "    with gzip.open(p, 'wt') as fh:\n        json.dump(doc, fh)\n"
             "    daystore.archive(doc, data, 'x')\n")
with open(os.path.join(_pl, "aliased.py"), "w", encoding="utf-8") as fh:
    fh.write("import collect\nimport daystore as _day\nLATEST = 'data/latest/y.json.gz'\n\n"
             "def build(data, doc):\n    collect.write(LATEST, doc, compress=True)\n"
             "    return _day.archive(doc, data, 'y', log=print)\n")
with open(os.path.join(_pl, "research", "bare.py"), "w", encoding="utf-8") as fh:
    fh.write("import gzip, json\nfrom daystore import archive\n\ndef build(data, doc):\n"
             "    with gzip.open(f'{data}/latest/z.json.gz', 'wt') as fh:\n        json.dump(doc, fh)\n"
             "    archive(doc, data, 'z')\n")
with open(os.path.join(_pl, "fine.py"), "w", encoding="utf-8") as fh:
    fh.write("import gzip, json, os, daystore\n\ndef build(data, doc):\n"
             "    p = os.path.join(data, 'latest', 'x.json.gz')\n"
             "    with gzip.open(p, 'wt') as fh:\n        json.dump(doc, fh)\n"
             "    daystore.archive(doc, data, 'x', same_as=p)\n")
with open(os.path.join(_pl, "snapshot.py"), "w", encoding="utf-8") as fh:   # an archive of its own doc
    fh.write("import gzip, json, os, daystore\n\ndef build(data, doc, snap):\n"
             "    with gzip.open(os.path.join(data, 'latest', 'x.json.gz'), 'wt') as fh:\n"
             "        json.dump(doc, fh)\n    daystore.archive(snap, data, 'snap')\n")
_pm, _pf = census(_pl)
eq(_pf, ["aliased.py:build line 7", "bad.py:build line 7", "research/bare.py:build line 7"],
   "   (planted) a dump or a collect.write to latest/ beside an archive of the same doc is flagged, "
   "through an alias, a module-level path, a bare import and in research/; with same_as, or an "
   "archive of another document, it is not")
eq(sorted(_pm), ["aliased.py:build line 7", "bad.py:build line 7", "fine.py:build line 7",
                 "research/bare.py:build line 7"], "   ...and the fine one is still counted as a member")


# ══════════════════════════════════════════════════════════════════════
section("3. `[2026-11-17]` A COPY THE DAY ALREADY HOLDS IS NOT WRITTEN AGAIN")
# ══════════════════════════════════════════════════════════════════════
def dossier(state, built):
    return {"league": "nfl", "built_at": built,
            "dossiers": [{"board_id": 7, "sections": [{"n": 1, "name": "Weather", "state": state}]}]}


def files(root):
    """{day: [HHMM.json.gz, ...]} of the planted tree's dossier archives."""
    out = {}
    for f in sorted(glob.glob(os.path.join(root, "*", "dossiers", "*.json.gz"))):
        out.setdefault(os.path.basename(os.path.dirname(os.path.dirname(f))), []).append(os.path.basename(f))
    return out


# The passes dossier_fb.build makes: collect.write(heartbeat) to latest/, then the same_as archive.
# OK is one content, UNAVAILABLE another; every other pass moves only the stamps.
_rp = os.path.join(TMP, "passes")
_lat = os.path.join(_rp, "latest", "dossiers.json.gz")
_PASSES = [(datetime.datetime(2026, 11, 4, 10, 5, tzinfo=UTC), "OK"),
           (datetime.datetime(2026, 11, 4, 11, 5, tzinfo=UTC), "OK"),
           (datetime.datetime(2026, 11, 4, 12, 5, tzinfo=UTC), "OK"),
           (datetime.datetime(2026, 11, 4, 13, 5, tzinfo=UTC), "UNAVAILABLE"),
           (datetime.datetime(2026, 11, 4, 14, 5, tzinfo=UTC), "UNAVAILABLE"),
           (datetime.datetime(2026, 11, 5, 0, 5, tzinfo=UTC), "UNAVAILABLE"),     # the next UTC day
           (datetime.datetime(2026, 11, 5, 1, 5, tzinfo=UTC), "UNAVAILABLE")]
_ran, _said, _after2, _said1 = [], [], None, []
for _i, (_wh, _state) in enumerate(_PASSES):
    _doc = dossier(_state, _wh.strftime("%Y-%m-%dT%H:%M:%SZ"))
    _C.write(_lat, _doc, compress=True, heartbeat=True)
    _got, _wrote = D.archive(_doc, _rp, "dossiers", log=_said.append, when=_wh, same_as=_lat)
    _ran.append((_wh, blob(_lat), _got, _wrote))
    if _i == 1:
        _after2, _said1 = files(_rp), list(_said)
eq(_after2, {"2026-11-04": ["1005.json.gz"]},
   "🔴🔴 a pass whose document moved only its stamps writes NO second copy of the day's previous "
   "archive (the defect: the same bytes under a new HHMM name, a full file on the site)")
ck(not _ran[1][3] and os.path.basename(_ran[1][2]) == "1005.json.gz"
   and any("not written" in m and "1005.json.gz" in m for m in _said1),
   "   ...it returns the archive that holds those bytes (wrote False) and says so in the log",
   "returned %s wrote=%s; log %s" % (os.path.basename(_ran[1][2]), _ran[1][3], _said1[-1:]))
ck(_ran[3][3] and blob(_ran[3][2]) == _ran[3][1]
   and json.load(gzip.open(_ran[3][2], "rt"))["dossiers"][0]["sections"][0]["state"] == "UNAVAILABLE",
   "🔴 a CHANGED document is written: a second file, holding the new reading")
ck(_ran[5][3] and os.path.basename(_ran[5][2]) == "0005.json.gz"
   and os.path.basename(os.path.dirname(os.path.dirname(_ran[5][2]))) == "2026-11-05",
   "🔴 ...and the next UTC day's first pass writes its copy, the same bytes as yesterday's last: a "
   "reader of ONE day (shadow_fb reads the newest archive of that day) finds every day a pass ran",
   "returned %s wrote=%s" % (_ran[5][2], _ran[5][3]))
eq(files(_rp), {"2026-11-04": ["1005.json.gz", "1305.json.gz"], "2026-11-05": ["0005.json.gz"]},
   "   7 passes, 2 readings, 2 days: 3 files (it was 7)")
# Every reader's answer is unchanged: at every pass, the day's newest archive at or before that pass
#    holds exactly the bytes that pass would have archived (the question a reader of "the reading in
#    force at time T" asks; shadow_fb's "newest of the day" is the day's last pass).
_wrong = []
for _wh, _lb, _g, _w in _ran:
    _day, _hm = _wh.strftime("%Y-%m-%d"), _wh.strftime("%H%M") + ".json.gz"
    _have = [n for n in files(_rp).get(_day, []) if n <= _hm]
    if not _have or blob(os.path.join(_rp, _day, "dossiers", _have[-1])) != _lb:
        _wrong.append((_day, _hm, _have[-1:] or None))
eq(_wrong, [], "🔴🔴 at every pass, the day's newest archive at or before it holds the bytes that pass "
               "would have written: no reader of a day, or of a moment, reads a different reading")
os.environ.setdefault("LEAGUE", "nfl")
import shadow_fb  # noqa: E402  (the one reader of dossier archives)
_sec = {}
for _day in ("2026-11-04", "2026-11-05"):
    _last = [r for r in _ran if r[0].strftime("%Y-%m-%d") == _day][-1]
    _out, _from, _none = shadow_fb.sections_for(_day, _rp)
    _want = json.loads(gzip.decompress(_last[1]).decode("utf-8"))["dossiers"][0]["sections"][0]["state"]
    _sec[_day] = (_out.get(7), _want, _from and blob(os.path.join(_rp, _day, "dossiers", _from)) == _last[1])
ck(all(v[0] == {"Weather": v[1]} and v[2] for v in _sec.values()),
   "🔴 shadow_fb.sections_for, the one reader of dossier archives, reads each day's last reading, from a "
   "file holding exactly its bytes", "%s" % _sec)

# A, B, A: a return to an earlier reading is a new reading. Deterministic gzips (mtime 0), so the
#    third latest is byte-for-byte the first; only the reading JUST BEFORE decides.
_ra = os.path.join(TMP, "aba")
_la = os.path.join(_ra, "latest", "x.json.gz")
os.makedirs(os.path.dirname(_la))
for _hh, _state in ((10, "OK"), (11, "UNAVAILABLE"), (12, "OK")):
    _dd = dossier(_state, "2026-11-04T%02d:05:00Z" % _hh)
    with open(_la, "wb") as fh:
        fh.write(gzip.compress(json.dumps(dossier(_state, "2026-11-04T10:05:00Z")).encode("utf-8"), mtime=0))
    D.archive(_dd, _ra, "dossiers", log=lambda *a: None,
              when=datetime.datetime(2026, 11, 4, _hh, 5, tzinfo=UTC), same_as=_la)
eq(files(_ra), {"2026-11-04": ["1005.json.gz", "1105.json.gz", "1205.json.gz"]},
   "🔴 OK, UNAVAILABLE, OK is three readings: the copy is compared with the reading JUST BEFORE it, "
   "never with any earlier one (else the 12:05 reading would read as UNAVAILABLE)")

# A dump is never skipped, so a caller that wants one file per pass keeps it: the news archive's
#    freshness row asks when the newest file in TODAY's directory was written.
_rd = os.path.join(TMP, "dumps")
for _hh in (10, 11):
    D.archive({"items": ["same"]}, _rd, "news", log=lambda *a: None,
              when=datetime.datetime(2026, 11, 4, _hh, 5, tzinfo=UTC))
eq(sorted(os.listdir(os.path.join(_rd, "2026-11-04", "news"))), ["1005.json.gz", "1105.json.gz"],
   "🔴 the same document DUMPED twice (no same_as) is two files: one per pass, as before")

shutil.rmtree(TMP, ignore_errors=True)
