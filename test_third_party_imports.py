#!/usr/bin/env python3
"""🔴🔴 NO TEST MAY NEED A PACKAGE CI DOES NOT INSTALL.

`[measured 2026-09-19 on CI job 105862432594]`

    ═══ 6. 🔴🔴 AND THE GATE IS DRIVEN, NOT READ ═══
      ⚪ ⛔ could not extract the decide step:
           ModuleNotFoundError: No module named 'yaml'
      ❌ 10 of 41 checks FAILED

`test_watch_label.py` imported PyYAML to drive the deployed `decide`
step. It passed on every developer machine and was **red on every CI run
from the hour it merged** — one of the two files that have had
`collect.yml` red continuously since 2026-09-18T21:22.

⛔ THE REPOSITORY ALREADY KNEW AND IT DID NOT HELP.
`test_multileague.py:82`: *"PyYAML not installed here, so the hand-parse
was not cross-checked."* `test_watchdog.py:328`: *"⚠️ NO `import yaml`.
`test_multileague.py` already records that PyYAML is not guaranteed on
the runner and that a test which cannot import BLOCKS a push."* Two
files wrote the rule down in prose; the third did not read it. **Prose
is not a guard.**

✅ SO THE RULE IS MECHANICAL NOW. A third-party import in a `test_*.py`
is allowed only when the workflow that runs the file installs it, or
when the file degrades to a `note()` and still asks its question. §2
proves the degradation by DRIVING each file with the package made
unimportable — the CI condition, reproduced, not assumed.

# @vacuity 🔴🔴 an unguarded third-party import in a test is caught
#   file: test_watchdog.py
#   find: import os
#   with: import os, yaml
"""
import ast
import glob
import io
import os
import re
import subprocess
import sys
import tempfile

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
WF = sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")))
STD = set(sys.stdlib_module_names)
LOCAL = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ROOT, "*.py"))}


def installed_by_workflow():
    """{workflow: {packages it pip-installs}} — derived, never listed."""
    out = {}
    for f in WF:
        src = io.open(f, encoding="utf-8").read()
        pkgs = set()
        for m in re.finditer(r"pip install\s+((?:--?\S+\s+)*)([^\n|&;]+)", src):
            for tok in m.group(2).split():
                if tok.startswith("-"):
                    continue
                pkgs.add(re.split(r"[=<>\[]", tok)[0].strip().lower())
        out[os.path.basename(f)] = pkgs
    return out


def files_run_by(name):
    """The test files a workflow runs: an explicit list, or discovery."""
    src = io.open(os.path.join(ROOT, ".github", "workflows", name),
                  encoding="utf-8").read()
    named = set(re.findall(r'"(test_[a-z0-9_]+\.py)"', src))
    if named:
        return named
    if "for t in test_*.py" in src:
        return {os.path.basename(p)
                for p in glob.glob(os.path.join(ROOT, "test_*.py"))}
    return set()


def third_party(path):
    """[(module, lineno, guarded)] for every non-stdlib, non-local import."""
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    guarded = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Try):
            handles = any(
                (isinstance(h.type, ast.Name)
                 and h.type.id in ("ImportError", "ModuleNotFoundError",
                                   "Exception"))
                or (isinstance(h.type, ast.Tuple)
                    and any(getattr(e, "id", "") in
                            ("ImportError", "ModuleNotFoundError", "Exception")
                            for e in h.type.elts))
                or h.type is None
                for h in n.handlers)
            if handles:
                for c in ast.walk(n):
                    if isinstance(c, (ast.Import, ast.ImportFrom)):
                        guarded.add(id(c))
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods = [(a.name.split(".")[0], n) for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            mods = [(n.module.split(".")[0], n)]
        else:
            continue
        for m, node in mods:
            if m and m not in STD and m not in LOCAL:
                out.append((m, node.lineno, id(node) in guarded))
    return out


INSTALLS = installed_by_workflow()
RUNNERS = {name: files_run_by(name) for name in
           (os.path.basename(f) for f in WF)}

# ════════════════════════════════════════════════════════════════════════
section("1. 🔴 DERIVED: WHO RUNS WHAT, AND WHO INSTALLS WHAT")
# ════════════════════════════════════════════════════════════════════════
note("workflows that install a package: %s"
     % {k: sorted(v) for k, v in INSTALLS.items() if v})
note("workflows that run test files: %s"
     % {k: len(v) for k, v in RUNNERS.items() if v})
ck("⚠️ the discovery found the suite runner and the browser runner",
   len(RUNNERS.get("collect.yml") or ()) >= 50
   and len(RUNNERS.get("browser.yml") or ()) >= 3,
   "⛔ if this derivation breaks, every judgement below is made about an "
   "empty set (rule 67). collect=%d browser=%d"
   % (len(RUNNERS.get("collect.yml") or ()),
      len(RUNNERS.get("browser.yml") or ())))
ck("⚠️ ...and browser.yml really does install what it needs",
   "playwright" in (INSTALLS.get("browser.yml") or set()),
   "⛔ the five browser files are allowed an unguarded import ONLY "
   "because their runner installs it. got %s"
   % sorted(INSTALLS.get("browser.yml") or ()))

# ════════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 EVERY THIRD-PARTY IMPORT IS INSTALLED OR GUARDED")
# ════════════════════════════════════════════════════════════════════════
offenders, seen, by_mod = [], 0, {}
for path in sorted(glob.glob(os.path.join(ROOT, "test_*.py"))):
    base = os.path.basename(path)
    for mod, line, guard in third_party(path):
        seen += 1
        by_mod.setdefault(mod, set()).add(base)
        if guard:
            continue
        runners = [w for w, files in RUNNERS.items() if base in files]
        missing = [w for w in runners
                   if mod.lower() not in (INSTALLS.get(w) or set())]
        if missing:
            offenders.append("%s:%d imports %r unguarded, and %s run(s) it "
                             "without installing it"
                             % (base, line, mod, ", ".join(missing)))

note("third-party imports across the suite: %d — %s"
     % (seen, {k: len(v) for k, v in sorted(by_mod.items())}))
ck("⚠️ there are imports to judge",
   seen >= 6 and len(by_mod) >= 2,
   "⛔ rule 67. seen=%d modules=%s" % (seen, sorted(by_mod)))
ck("🔴🔴 no test needs a package its own runner does not install",
   not offenders,
   "⛔ THE DEFECT OF 2026-09-19. A file that cannot import does not fail "
   "one check — it fails the whole file, and on `collect.yml` that "
   "blocks the push. %s" % ("; ".join(offenders) or "none"))

# ════════════════════════════════════════════════════════════════════════
section("3. 🔴🔴 AND THE GUARDED ONES ARE DRIVEN WITHOUT THE PACKAGE")
# ════════════════════════════════════════════════════════════════════════
# ⛔ A `try: import yaml / except ImportError:` PROVES NOTHING ON ITS OWN.
#    The file can still reference the module later and die with a
#    NameError, which is the same red for a different reason. The only
#    honest check is to run it the way CI does.
YAML_USERS = sorted(b for b in by_mod.get("yaml", ()) )
blocked = tempfile.mkdtemp(prefix="nopkg-")
io.open(os.path.join(blocked, "yaml.py"), "w", encoding="utf-8").write(
    'raise ImportError("PyYAML is not installed on the CI runner")\n')
ck("⚠️ there are PyYAML users to drive",
   len(YAML_USERS) >= 2,
   "⛔ rule 67 — an empty drive list is a section that checks nothing. "
   "got %s" % YAML_USERS)
for base in YAML_USERS:
    r = subprocess.run([sys.executable, "-B", os.path.join(ROOT, base)],
                       cwd=ROOT, capture_output=True, text=True, timeout=600,
                       env=dict(os.environ, PYTHONPATH=blocked + os.pathsep
                                + os.environ.get("PYTHONPATH", "")))
    tail = ((r.stdout or "") + (r.stderr or ""))[-200:]
    ck("🔴 %s still passes with PyYAML unimportable" % base,
       r.returncode == 0,
       "⛔ this is the CI condition reproduced, not assumed. rc=%s tail=%r"
       % (r.returncode, tail))
ck("⚠️ ...and the block really did make it unimportable",
   subprocess.run([sys.executable, "-c", "import yaml"], cwd=ROOT,
                  capture_output=True,
                  env=dict(os.environ, PYTHONPATH=blocked)).returncode != 0,
   "⛔ if the stub is not on the path the drives above prove nothing — "
   "the same rule-67 trap that let the original bug through.")
