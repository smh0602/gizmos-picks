#!/usr/bin/env python3
"""test_copy_module.py — `tcheck.copy_module` copies EVERY repo module its subject loads.

`[2026-10-15]` card_fb.py loaded fb_why.py through `__import__("fb_why")`. The
copier reads `import` statements only, so every isolated card tree
(test_top_plays, test_board_cap, test_fb_best_plays ...) started without
fb_why.py and the builder could not run: red for a reason that had nothing to
do with the thing under test. The class: a repo module loaded by a call with a
literal name (`__import__("x")`, `importlib.import_module("x")`). Planted files
only.

# @vacuity 🔴 a module loaded by `__import__("x")` / `import_module("x")` is copied
#   file: tcheck.py
#   find:                 names.append(n.args[0].value)
#   with:                 pass
"""
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from tcheck import copy_module, eq  # noqa: E402

T = tempfile.mkdtemp(prefix="copymod-")
SRC, DST = os.path.join(T, "src"), os.path.join(T, "dst")
os.makedirs(SRC)
os.makedirs(DST)
try:
    files = {
        "subject.py": 'import plain\nimport json\nX = __import__("dyn")\nY = __import__("json")\n'
                      'name = "notreal"\nZ = __import__(name)\n',
        "plain.py": "from fromimp import thing\n",
        "fromimp.py": "thing = 1\n",
        "dyn.py": 'import importlib\nW = importlib.import_module("viamod")\n',
        "viamod.py": "V = 1\n",
        "notreal.py": "N = 1\n",
        "unrelated.py": "U = 1\n",
    }
    for f, s in files.items():
        with open(os.path.join(SRC, f), "w", encoding="utf-8") as fh:
            fh.write(s)
    eq(copy_module("subject", DST, root=SRC), ["dyn.py", "fromimp.py", "plain.py", "subject.py", "viamod.py"],
       "🔴 copies the subject, its `import` / `from` modules, and the ones it loads by "
       "`__import__(\"x\")` or `importlib.import_module(\"x\")` (transitively); never a stdlib "
       "module, a name held in a variable, or a file nothing loads")
    eq(sorted(os.listdir(DST)), ["dyn.py", "fromimp.py", "plain.py", "subject.py", "viamod.py"],
       "   ...and the files really are there")
finally:
    shutil.rmtree(T, ignore_errors=True)
