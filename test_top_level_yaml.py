#!/usr/bin/env python3
r"""test_top_level_yaml.py — no .yml or .yaml file in the repo's top level.

`[2026-09-25]` 103c7ac uploaded eleven workflow copies into the repo's TOP
LEVEL instead of `.github/workflows/` (runs.yml's copy first from
251d4c65, 2026-09-14). GitHub runs a workflow only from
`.github/workflows/`, so none of them ever fired and nothing went red: the
upload that was meant to change the workflows simply did not happen until
Sam re-uploaded into the right folder (eb5bc2a). The strays sat beside
the real files as byte-identical dead copies.
⚠️ ROOT CAUSE: the upload was made from the repo's front page, where
"Add file → Upload files" puts files in the top level. The instructions
(`docs/upload/UPLOAD-runner-image.md`) named the right folder and its
breadcrumb; nothing CHECKED where the files landed.
✅ Deleted on 2026-09-25. This file fails if one ever comes back.

⛔ THE CLASS, NOT THE ELEVEN NAMES. The top level holds no YAML of its
own, so ANY .yml/.yaml there fails, whatever it is called or contains.
If one is ever needed there on purpose, that is a decision to write down
here, never a name to skip quietly.

# @vacuity a stray workflow is found whatever the case of its name
#   file: wfparse.py
#   find:                   if f.lower().endswith(TOP_LEVEL_YAML))
#   with:                   if f.endswith(TOP_LEVEL_YAML))
#
# @vacuity a stray spelled .yaml is found, not only .yml
#   file: wfparse.py
#   find: TOP_LEVEL_YAML = (".yml", ".yaml")
#   with: TOP_LEVEL_YAML = (".yml",)
#
# @vacuity the real repo's check goes red on real workflow files
#   file: wfparse.py
#   find:     return sorted(f for f in os.listdir(root)
#   with:     return sorted(f for f in os.listdir(os.path.join(root, DEPLOYED_DIR))
#
# @vacuity the scan is of the folder the workflows sit beside
#   file: wfparse.py
#   find: DEPLOYED_DIR = os.path.join(".github", "workflows")
#   with: DEPLOYED_DIR = os.path.join(".github", "workflowz")
"""
import os
import shutil
import sys
import tempfile

from tcheck import ck, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import wfparse as W  # noqa: E402

CAUSE = "uploaded to the wrong folder; workflows belong in .github/workflows/"


def why(names):
    """The failure detail: every stray by name, each with its likely cause."""
    return "\n".join(["%d stray file(s) in the top level:" % len(names)]
                     + ["     ⛔ %s — %s" % (n, CAUSE) for n in names]
                     + ["     ➡️ if .github/workflows/ already holds the same "
                        "file, delete the stray; a copy staged for Sam belongs "
                        "in docs/upload/"])


_trees = []


def tree(files):
    """A throwaway repo holding `files` ({relative path: text})."""
    d = tempfile.mkdtemp(prefix="toplevel-yaml-")
    _trees.append(d)
    for rel, text in files.items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
    return d


_WF = 'name: x\non:\n  schedule:\n    - cron: "7 7 * * *"\njobs: {}\n'

section("1. 🔴🔴 THE REAL REPO — NOTHING IN THE TOP LEVEL THAT BELONGS IN A WORKFLOW FOLDER")
_dep = os.path.join(ROOT, W.DEPLOYED_DIR)
_live = sorted(f for f in os.listdir(_dep) if f.endswith(".yml")) if os.path.isdir(_dep) else []
ck(len(_live) >= 1,
   "⚠️ the scan is of the REPO's top level: %s/ is beside it and holds %d "
   "workflow(s)" % (W.DEPLOYED_DIR, len(_live)),
   "⛔ scanning some other folder would pass having checked nothing (rule 67)")
_stray = W.top_level_yaml(ROOT)
ck(not _stray, "🔴🔴 no .yml or .yaml file in the repo's top level",
   why(_stray) if _stray else "")

section("2. 🔴 THE CHECK BITES ON THE SHAPE OF 103c7ac, AND ONLY ON THAT")
_planted = tree({
    # the defect: copies in the top level, one of them a .yaml, one SHOUTED
    "collect.yml": _WF, "vacuity.yml": _WF, "other.yaml": _WF,
    "LOUD.YAML": _WF,
    # and what must NOT be caught, around it
    ".github/workflows/collect.yml": _WF,
    "docs/upload/vacuity.yml": _WF,
    "docs/upload/UPLOAD-vacuity.md": "x",
    "card.py": "x", "README.md": "x", "collect.yml.md": "x",
})
_want = ["LOUD.YAML", "collect.yml", "other.yaml", "vacuity.yml"]
_got = W.top_level_yaml(_planted)
ck(_got == _want,
   "🔴 every stray is found — .yml, .yaml, any case — and nothing else",
   "want %s, got %s" % (_want, _got))
_msg = why(_got)
_named = all(("%s — %s" % (n, CAUSE)) in _msg for n in _want)
ck(_named, "🔴 the failure names EVERY stray file, each with its likely cause",
   "" if _named else "\n" + _msg)
_clean = tree({
    ".github/workflows/a.yml": _WF,
    "docs/upload/a.yml": _WF,
    "docs/upload/UPLOAD-a.md": "x",
    "card.py": "x", "README.md": "x",
})
ck(W.top_level_yaml(_clean) == [],
   "✅ a correct layout — workflows deployed and staged, no YAML on top — is clean",
   "⛔ a guard that fires on correct code is the other failure. got %s"
   % W.top_level_yaml(_clean))

for _d in _trees:
    shutil.rmtree(_d, ignore_errors=True)
