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
      stores exactly the document, and dumps it as before on any difference;
      write-once and the picks/ refusal are unchanged.
  §2  the CLASS: every function in this repo that writes a document to a
      latest/ gzip AND archives that same document passes `same_as`. A new
      one is red until it does (the dossier is the only one today).

⛔ A TEST ASKS THE CODE: every tree here is planted.

# @vacuity 🔴 the archive copies latest's bytes (the dossier was stored twice)
#   file: daystore.py
#   find:     buf = same_bytes(same_as, doc) if same_as else None
#   with:     buf = None
#
# @vacuity 🔴 a latest file that stores another document is not copied
#   file: daystore.py
#   find:         if json.loads(gzip.decompress(buf).decode("utf-8")) == json.loads(json.dumps(doc)):
#   with:         if True:
#
# @vacuity 🔴 the census finds a latest/ write beside an archive of the same document
#   file: dossier_fb.py
#   find:     arch, _wrote = daystore.archive(doc, data, "dossiers", log=log, same_as=p)
#   with:     arch, _wrote = daystore.archive(doc, data, "dossiers", log=log)
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

_r3 = os.path.join(TMP, "other")
_lp3 = latest(_r3, dict(DOC, built_at="2026-11-04T16:00:00Z"))
_ap3, _ = D.archive(DOC, _r3, "dossiers", log=lambda *a: None, when=WHEN, same_as=_lp3)
eq(json.load(gzip.open(_ap3, "rt")), json.loads(json.dumps(DOC)),
   "🔴 a latest file that stores ANOTHER document (a stamp apart) is not copied: the archive is this doc")
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

shutil.rmtree(TMP, ignore_errors=True)
