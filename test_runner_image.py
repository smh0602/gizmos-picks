#!/usr/bin/env python3
r"""test_runner_image.py — nothing a workflow runs on may move under it.

`[added 2026-09-24]` Two changes GitHub makes FOR us, on its own clock:

  1. `ubuntu-latest` moves from Ubuntu 24.04 to Ubuntu 26.04, rolling out
     2026-10-19 → 2026-11-19. The image's own `python` goes 3.12 → 3.14,
     its `node` 20 → 24, and its apt package names change (the thing
     `playwright install --with-deps` depends on).
  2. Node 20 is being retired as an action runtime. `actions/checkout@v4`
     and `actions/setup-python@v5` run on Node 20 and are already being
     forced onto Node 24.

⛔ Either one would change what a scheduled job runs on with no edit in
this repo, no PR, and no red test — the same shape as every "it changed
under us" failure in the ledger. So the CLASS is guarded, not the day:

  - every job runs on a PINNED image label, never a floating `-latest`;
  - every action is at a major known to run on Node 24, and an action this
    file does not know FAILS until someone checks its runtime and adds it;
  - every job that runs Python (or hands a shell to an agent) pins its
    Python with setup-python BEFORE it runs any, never the image's;
  - `pr-tests` runs on every image any workflow is pinned to, so a move to
    a new image is tested on a PR before a schedule depends on it;
  - pr-tests' render job is browser.yml's steps, line for line (rule 117).

⚠️ EVERY WORKFLOW IS READ AS IT WILL BE LIVE — the staged copy in
`docs/upload/` when one exists (`wfparse.effective_workflows`). Reading
only `.github/workflows/` would be red from the moment this merges until
Sam uploads; `runs_report` already flags an upload left 48h.

# @vacuity 🔴 a floating `-latest` runner label is caught
#   file: docs/upload/collect.yml
#   find:     runs-on: ubuntu-24.04
#   with:     runs-on: ubuntu-latest
#
# @vacuity 🔴 an action still on a Node 20 major is caught
#   file: docs/upload/t60r.yml
#   find:       - uses: actions/checkout@v5
#   with:       - uses: actions/checkout@v4
#
# @vacuity 🔴 a job that runs Python on the IMAGE's Python is caught
#   file: docs/upload/calibration.yml
#   find:       - uses: actions/setup-python@v6
#   with:       - run: true
#
# @vacuity 🔴 the check reads the STAGED copy, which is what will be live
#   file: wfparse.py
#   find:     for sub in (DEPLOYED_DIR, STAGED_DIR):   # staged read second, so it wins
#   with:     for sub in (STAGED_DIR, DEPLOYED_DIR):   # staged read second, so it wins
#
# @vacuity 🔴 pr-tests' render job drifting from browser.yml is caught
#   file: .github/workflows/pr-tests.yml
#   find:           python -m playwright install --with-deps chromium
#   with:           python -m playwright install chromium
#
# @vacuity 🔴 an image a workflow is pinned to but pr-tests never runs on is caught
#   file: docs/upload/browser.yml
#   find:     runs-on: ubuntu-24.04
#   with:     runs-on: ubuntu-22.04
"""
import os
import re
import shutil
import sys
import tempfile

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import wfparse as W  # noqa: E402

# ══════════════════════════════════════════════════════════════════════
# THE NODE 24 TABLE. {action: lowest major that runs on Node 24}.
# ⛔ An action NOT in this table fails. Add one only after reading its
#    `action.yml` at that major: `runs.using` must be `node24`, or
#    `composite` / `docker` (no Node runtime of its own), in which case
#    write 1 and say so.
#    actions/checkout      v5 = node24 (v4 = node20)
#    actions/setup-python  v6 = node24 (v5 = node20)
#    anthropics/claude-code-action  composite — no Node runtime of its own
# ══════════════════════════════════════════════════════════════════════
NODE24_MIN = {
    "actions/checkout": 5,
    "actions/setup-python": 6,
    "anthropics/claude-code-action": 1,
}
PINNED = re.compile(r"^ubuntu-\d{2}\.\d{2}(-arm)?$")
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*([^\s#]+)")
PY_USE = re.compile(r"\bpython3?\b(?!-)")
AGENT = "anthropics/claude-code-action"


def _code(text):
    """Text with whole-line comments dropped — prose is not a runtime."""
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


def job_facts(path):
    """[{job, runs_on: [labels] or None, steps: [{uses, text, name, run, cond}]}]"""
    src = W.read(path)
    lines = src.splitlines()
    out = []
    for jb in W.jobs(src):
        body = _code("\n".join(lines[jb.start:jb.end]))
        m = re.search(r"(?m)^    runs-on:\s*(.+?)\s*$", body)
        labels = None
        if m:
            v = m.group(1).strip().strip('"').strip("'")
            mx = re.fullmatch(r"\$\{\{\s*matrix\.(\w+)\s*\}\}", v)
            if mx:
                ml = re.search(r"(?m)^\s+%s:\s*\[(.*)\]\s*$" % mx.group(1), body)
                labels = ([x.strip().strip('"').strip("'") for x in ml.group(1).split(",")]
                          if ml else [v])
            else:
                labels = [v]
        steps = []
        for st in W.steps(src, jb.name):
            text = _code("\n".join(lines[st.start:st.end]))
            u = next((USES.match(l).group(1) for l in text.splitlines() if USES.match(l)), None)
            steps.append({"uses": u, "text": text, "name": st.name,
                          "run": st.run, "cond": st.cond})
        out.append({"job": jb.name, "runs_on": labels, "steps": steps})
    return out


def floating(path):
    """['job: label'] for every job not on a pinned image label."""
    return ["%s: %s" % (j["job"], l) for j in job_facts(path)
            for l in (j["runs_on"] or ["<none>"]) if not PINNED.match(l)]


def old_actions(path):
    """['job: action@ref — why'] for every action not known to run on Node 24."""
    bad = []
    for j in job_facts(path):
        for s in j["steps"]:
            u = s["uses"]
            if not u or u.startswith("./"):
                continue
            name, _, ref = u.partition("@")
            m = re.fullmatch(r"v(\d+)(?:\.\d+)*", ref)
            if name not in NODE24_MIN:
                bad.append("%s: %s — not in the Node 24 table" % (j["job"], u))
            elif not m:
                bad.append("%s: %s — not a version tag" % (j["job"], u))
            elif int(m.group(1)) < NODE24_MIN[name]:
                bad.append("%s: %s — Node 20 major (need v%d+)"
                           % (j["job"], u, NODE24_MIN[name]))
    return bad


def image_python(path):
    """['job — why'] for every job that runs Python without pinning it first."""
    bad = []
    for j in job_facts(path):
        pin = None
        for k, s in enumerate(j["steps"]):
            if (s["uses"] or "").startswith("actions/setup-python@"):
                if re.search(r"(?m)^\s+python-version:\s*[\"']?3\.\d+", s["text"]):
                    pin = k if pin is None else pin
                continue
            needs = (s["uses"] or "").startswith(AGENT + "@") or (
                s["run"] is not None and PY_USE.search(_code(s["run"])))
            if needs and pin is None:
                bad.append("%s — step %r runs Python before any setup-python "
                           "with an explicit python-version"
                           % (j["job"], s["name"] or s["uses"]))
                break
    return bad


# ══════════════════════════════════════════════════════════════════════
section("1. THE STAGED COPY IS WHAT WILL BE LIVE, SO IT IS WHAT IS READ")
_trees = []


def T(deployed=None, staged=None):
    d = tempfile.mkdtemp(prefix="img-")
    _trees.append(d)
    for sub, files in ((W.DEPLOYED_DIR, deployed or {}), (W.STAGED_DIR, staged or {})):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
        for n, t in files.items():
            with open(os.path.join(d, sub, n), "w", encoding="utf-8") as fh:
                fh.write(t)
    return d


_OLD = "jobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo\n"
_NEW = _OLD.replace("ubuntu-latest", "ubuntu-24.04")
_t = T(deployed={"a.yml": _OLD, "b.yml": _NEW}, staged={"a.yml": _NEW, "c.yml": _NEW})
_eff = W.effective_workflows(_t)
ck(sorted(_eff) == ["a.yml", "b.yml", "c.yml"],
   "🔴 every workflow in EITHER folder is read, once per name", "got %r" % sorted(_eff))
ck(_eff.get("a.yml", "").startswith(os.path.join(_t, W.STAGED_DIR))
   and floating(_eff["a.yml"]) == [],
   "🔴🔴 a pending update is read at its STAGED copy — what fires once Sam uploads",
   "⛔ reading the deployed copy would be red from merge until upload. got %r"
   % _eff.get("a.yml"))
ck(_eff.get("b.yml", "").startswith(os.path.join(_t, W.DEPLOYED_DIR)),
   "   ✅ ...and a workflow with no staged copy is read where it is deployed")

section("2. EACH QUESTION BITES ON A FIXTURE BEFORE IT IS ASKED OF THE REPO")
_F = T(deployed={
    "latest.yml": _OLD,
    "matrix.yml": ("jobs:\n  a:\n    strategy:\n      matrix:\n"
                   "        os: [ubuntu-24.04, ubuntu-latest]\n"
                   "    runs-on: ${{ matrix.os }}\n    steps:\n      - run: echo\n"),
    "node20.yml": ("jobs:\n  a:\n    runs-on: ubuntu-24.04\n    steps:\n"
                   "      - uses: actions/checkout@v4\n      - uses: someone/new-thing@v9\n"
                   "      - uses: actions/setup-python@main\n"),
    "imgpy.yml": ("jobs:\n  a:\n    runs-on: ubuntu-24.04\n    steps:\n"
                  "      - uses: actions/checkout@v5\n"
                  "      - name: go\n        run: |\n          python x.py\n"
                  "      - uses: actions/setup-python@v6\n        with:\n"
                  "          python-version: \"3.12\"\n"),
    "agent.yml": ("jobs:\n  a:\n    runs-on: ubuntu-24.04\n    steps:\n"
                  "      - uses: anthropics/claude-code-action@v1\n"),
    "good.yml": ("jobs:\n  a:\n    runs-on: ubuntu-24.04\n    steps:\n"
                 "      - uses: actions/checkout@v5\n"
                 "      # python in a comment is not a runtime\n"
                 "      - uses: actions/setup-python@v6\n        with:\n"
                 "          python-version: \"3.12\"\n"
                 "      - name: go\n        run: |\n          python x.py\n"),
})
_P = lambda n: os.path.join(_F, W.DEPLOYED_DIR, n)   # noqa: E731
ck(floating(_P("latest.yml")) == ["a: ubuntu-latest"],
   "🔴 `ubuntu-latest` is a floating label", "got %r" % floating(_P("latest.yml")))
ck(floating(_P("matrix.yml")) == ["a: ubuntu-latest"],
   "🔴 ...and so is a `-latest` hiding in a matrix", "got %r" % floating(_P("matrix.yml")))
_o = old_actions(_P("node20.yml"))
ck(len(_o) == 3 and "Node 20" in _o[0] and "not in the Node 24 table" in _o[1]
   and "not a version tag" in _o[2],
   "🔴 a Node 20 major, an UNKNOWN action and a branch ref are all caught", "got %r" % _o)
ck(image_python(_P("imgpy.yml")) and image_python(_P("agent.yml")),
   "🔴 Python run BEFORE setup-python is caught, and so is an agent with no pin",
   "got %r / %r" % (image_python(_P("imgpy.yml")), image_python(_P("agent.yml"))))
ck(floating(_P("good.yml")) == [] and old_actions(_P("good.yml")) == []
   and image_python(_P("good.yml")) == [],
   "   ✅ ...and a correct workflow passes all three — a guard that fires on "
   "correct code is the other failure",
   "got %r %r %r" % (floating(_P("good.yml")), old_actions(_P("good.yml")),
                     image_python(_P("good.yml"))))

section("3. THE REAL WORKFLOWS, AS THEY WILL BE LIVE")
EFF = W.effective_workflows(ROOT)
ck(len(EFF) >= 13 and "collect.yml" in EFF and "pr-tests.yml" in EFF,
   "⚠️ the workflows were actually found", "⛔ an empty set passes everything. got %r"
   % sorted(EFF))
_jobs = sum(len(job_facts(p)) for p in EFF.values())
ck(_jobs >= 15, "⚠️ ...and their jobs were parsed", "got %d job(s)" % _jobs)
_fl = {f: floating(p) for f, p in EFF.items() if floating(p)}
ck(not _fl, "🔴🔴 every job runs on a PINNED image — nothing moves when GitHub moves `-latest`",
   "floating: %r" % _fl)
_na = {f: old_actions(p) for f, p in EFF.items() if old_actions(p)}
ck(not _na, "🔴🔴 every action is at a major that runs on Node 24", "%r" % _na)
_ip = {f: image_python(p) for f, p in EFF.items() if image_python(p)}
ck(not _ip, "🔴🔴 every job that runs Python pins it — never the image's own "
   "(3.12 on 24.04, 3.14 on 26.04)", "%r" % _ip)

section("4. PR-TESTS RUNS ON EVERY IMAGE A WORKFLOW IS PINNED TO")
_pr = {j["job"]: j for j in job_facts(EFF["pr-tests.yml"])}
_pinned = sorted({l for f, p in EFF.items() if f != "pr-tests.yml"
                  for j in job_facts(p) for l in (j["runs_on"] or [])})
for _name in ("tests", "render"):
    _cov = set((_pr.get(_name) or {}).get("runs_on") or [])
    ck(_cov and set(_pinned) <= _cov,
       "🔴 pr-tests `%s` covers every pinned image %s" % (_name, _pinned),
       "⛔ a schedule on an image no PR ever tested is the move this file exists "
       "to prevent. pr-tests runs on %r" % sorted(_cov))
note("pr-tests also runs on %s — the images no schedule uses yet. Green there "
     "on a PR is the evidence to move a workflow's pin."
     % sorted(set((_pr.get("tests") or {}).get("runs_on") or []) - set(_pinned)))

section("5. PR-TESTS' RENDER JOB IS browser.yml's, LINE FOR LINE")
_br = {s["name"]: s for j in job_facts(EFF["browser.yml"]) for s in j["steps"] if s["run"]}
_rend = _pr.get("render") or {"steps": [], "runs_on": None}
_rj = {s["name"]: s for s in _rend["steps"] if s["run"]}
ck(len(_br) >= 4, "⚠️ browser.yml's run steps were found", "got %r" % sorted(_br))
ck(sorted(_rj) == sorted(_br),
   "🔴 the same run steps, by name", "pr-tests %r vs browser %r" % (sorted(_rj), sorted(_br)))
_diff = [n for n in _br if n in _rj and (_rj[n]["run"], _rj[n]["cond"]) != (_br[n]["run"], _br[n]["cond"])]
ck(not _diff, "🔴🔴 ...with the same scripts and conditions — rule 117",
   "⛔ a PR that passes a weaker render check than the one on main. differ: %r" % _diff)
_py = lambda j: [s["text"] for s in j["steps"] if (s["uses"] or "").startswith("actions/setup-python@")]  # noqa: E731
_bpy = [re.search(r"python-version:\s*(\S+)", t).group(1) for t in _py(job_facts(EFF["browser.yml"])[0])]
_rpy = [re.search(r"python-version:\s*(\S+)", t).group(1) for t in _py(_rend)]
ck(_bpy and _bpy == _rpy, "   ✅ ...on the same Python", "browser %r vs pr-tests %r" % (_bpy, _rpy))

for _d in _trees:
    shutil.rmtree(_d, ignore_errors=True)
