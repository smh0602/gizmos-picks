#!/usr/bin/env python3
"""THE ONE HAND PARSER FOR A GITHUB WORKFLOW FILE.

🔴🔴 WHY THIS IS HAND-WRITTEN AND NOT `yaml.safe_load`.
`[measured 2026-09-19 on CI job 105862432594]` The runner installs a bare
Python and **PyYAML is not on it**:

    ⛔ could not extract the decide step: ModuleNotFoundError: No module named 'yaml'
    ❌ 10 of 41 checks FAILED

`test_watch_label.py` imported `yaml` to drive the deployed `decide` step,
which made it **red on every CI run from the hour it merged** while passing
on every developer machine. `test_multileague.py` and `test_watchdog.py`
had already written the rule down in as many words; the third file did not
read them. ⛔ **Nothing in this repository may need a package CI does not
install in order to ask its question.**

🔴 AND IT IS ONE COPY, NOT THREE. Rule 117: a helper duplicated breaks in
the file you did not edit. The `run:`-block extractor existed **twice**
already — `test_multileague.py:49` and `test_season_default.py:38` — byte
for byte the same loop with a different `id:` hardcoded in it. Both now
call this.

⚠️ WHAT THIS IS NOT. It is not a YAML implementation and must never grow
into one. It answers the four questions this repo actually asks of a
workflow file:

    jobs(src)          -> every job, with its own `permissions:` block
    steps(src, job)    -> every step of a job, with its `run:` body
    step_run(src, id)  -> one step's script, by `id:` or by `name:`
    permissions(src)   -> the workflow-level `permissions:` block

⛔ Anything a block scalar contains is TEXT, never structure. A `run: |`
body in this repo contains the literal lines `permissions:`, `- cron:` and
`jobs:` inside agent prompts and comments, and a scanner that reads them as
keys reports a workflow that does not exist. The scanner below consumes
every block scalar whole, which is the only reason it can be trusted.
"""
import io
import os
import re

__all__ = ["read", "jobs", "steps", "step_run", "permissions", "Job", "Step"]

# A mapping key at some indent: `foo:`, `foo: bar`, `foo: |`, `- foo: bar`.
_KEY = re.compile(r"^(\s*)(-\s+)?([A-Za-z_][A-Za-z0-9_.-]*):\s?(.*?)\s*$")
_BLOCK = re.compile(r"^[|>][-+]?\d*$")


def read(src):
    """`src` is a path if one exists by that name, otherwise it IS the text.

    ⚠️ Checked with `os.path.exists` and never by guessing from a newline —
    a one-line workflow is legal and a path with a newline in it is not.
    """
    try:
        if src and os.path.exists(src):
            return io.open(src, encoding="utf-8").read()
    except (OSError, ValueError):          # pragma: no cover - long/odd paths
        pass
    return src or ""


class Step(object):
    def __init__(self, name, sid, run, start, end, cond=None):
        self.name, self.id, self.run = name, sid, run
        self.start, self.end = start, end
        # ⚠️ `if:` IS PART OF THE STEP, and for a gate it is the whole
        #    step. `test_collect_gates.py` evaluates these, because two
        #    gates whose conditions are both true must BOTH run — and
        #    until 2026-09-19 the second one never did.
        self.cond = cond

    def __repr__(self):                     # pragma: no cover - debugging only
        return "<Step %r id=%r %d-%d>" % (self.name, self.id, self.start,
                                          self.end)


class Job(object):
    def __init__(self, name, start, end, perms):
        self.name, self.start, self.end = name, start, end
        self.permissions = perms

    def __repr__(self):                     # pragma: no cover - debugging only
        return "<Job %r %d-%d perms=%r>" % (self.name, self.start, self.end,
                                            self.permissions)


def _scan(lines):
    """Yield (lineno, indent, key, value, body) for every key OUTSIDE a block.

    `indent` is the column the KEY starts at, so `      - name: x` reports
    the same indent as `        name: x` — which is what YAML means by it.
    `body` is the dedented block scalar when the value was `|` or `>`, else
    None. Block scalars are consumed here and never re-scanned.
    """
    i, n = 0, len(lines)
    while i < n:
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        m = _KEY.match(raw)
        if not m:
            i += 1
            continue
        pad, dash, key, val = m.group(1), m.group(2) or "", m.group(3), m.group(4)
        indent = len(pad) + len(dash)
        if not _BLOCK.match(val):
            yield (i, indent, key, val, None)
            i += 1
            continue
        # ── a block scalar: everything more indented than the key is TEXT
        body, j, inner = [], i + 1, None
        while j < n:
            cur = lines[j]
            if not cur.strip():
                body.append("")
                j += 1
                continue
            cur_pad = len(cur) - len(cur.lstrip())
            if inner is None:
                if cur_pad <= indent:
                    break
                inner = cur_pad
            if cur_pad < inner:
                break
            body.append(cur[inner:])
            j += 1
        while body and not body[-1].strip():
            body.pop()
        yield (i, indent, key, val, "\n".join(body) + ("\n" if body else ""))
        i = j


def permissions(src):
    """The WORKFLOW-level `permissions:` block, {scope: level}.

    ⚠️ An empty dict means the key is absent, which is not the same as
    `permissions: {}`. Callers that care must ask `has_workflow_permissions`.
    """
    lines = read(src).splitlines()
    return _perm_block(lines, 0)


def has_workflow_permissions(src):
    lines = read(src).splitlines()
    for _, indent, key, _v, _b in _scan(lines):
        if indent == 0 and key == "permissions":
            return True
    return False


def _perm_block(lines, at_indent, start=0, stop=None):
    """Read the `permissions:` mapping that sits at `at_indent` in a range."""
    stop = len(lines) if stop is None else stop
    out, want, base = {}, False, None
    for lineno, indent, key, val, _b in _scan(lines):
        if lineno < start or lineno >= stop:
            continue
        if not want:
            if indent == at_indent and key == "permissions":
                want, base = True, None
            continue
        if base is None:
            if indent <= at_indent:
                break
            base = indent
        if indent != base:
            break
        out[key] = val.strip().strip('"').strip("'")
    return out


def jobs(src):
    """Every job in the file, in order, each with its own permissions."""
    lines = read(src).splitlines()
    heads = []
    in_jobs = False
    for lineno, indent, key, _val, _b in _scan(lines):
        if indent == 0:
            in_jobs = (key == "jobs")
            continue
        if in_jobs and indent == 2:
            heads.append((lineno, key))
    out = []
    for k, (lineno, name) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        out.append(Job(name, lineno, end, _perm_block(lines, 4, lineno, end)))
    return out


def steps(src, job=None):
    """Every step of `job` (or of every job when it is None).

    ⛔ THE STEP INDENT IS DERIVED FROM `steps:`, NEVER ASSUMED. YAML lets a
    sequence sit at the parent's own column or two past it, and both are
    legal in a workflow. A hardcoded column is a parser that works on this
    repo's files until somebody reformats one — rule 293.
    """
    lines = read(src).splitlines()
    want = [j for j in jobs(src) if job in (None, j.name)]
    out = []
    for jb in want:
        entries = [e for e in _scan(lines) if jb.start <= e[0] < jb.end]
        anchor = next((e for e in entries if e[1] == 4 and e[2] == "steps"),
                      None)
        if anchor is None:
            continue
        dashes = [e for e in entries
                  if e[0] > anchor[0] and lines[e[0]].lstrip().startswith("- ")]
        if not dashes:
            continue
        col = min(e[1] for e in dashes)
        heads = [e[0] for e in dashes if e[1] == col]
        for k, start in enumerate(heads):
            end = heads[k + 1] if k + 1 < len(heads) else jb.end
            name = sid = run = cond = None
            for lineno, indent, key, val, body in entries:
                if not (start <= lineno < end) or indent != col:
                    continue
                if key == "name" and name is None:
                    name = val.strip().strip('"').strip("'")
                elif key == "id" and sid is None:
                    sid = val.strip().strip('"').strip("'")
                elif key == "run" and run is None:
                    run = body if body is not None else val
                elif key == "if" and cond is None:
                    cond = (body if body is not None else val).strip()
            out.append(Step(name, sid, run, start, end, cond))
    return out


def step_run(src, step_id=None, step_name=None, job=None):
    """One step's `run:` body, found by `id:` first and then by `name:`.

    ⛔ Returns None rather than guessing. Every caller checks — a silent
    None here is the shape of rule 67 (a drive that checks nothing).
    """
    for st in steps(src, job):
        if step_id is not None and st.id == step_id:
            return st.run
    if step_name is not None:
        for st in steps(src, job):
            if st.name == step_name:
                return st.run
    return None
