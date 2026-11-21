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
import fnmatch
import os
import re

__all__ = ["read", "jobs", "steps", "step_run", "permissions", "Job", "Step",
           "effective_workflows", "top_level_yaml", "step_tests", "rerun_tests"]

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
        # ⚠️ `[2026-11-17, the review]` the indicator is read with its comment cut, like
        #    every other value: `run: |   # the script` is a block scalar (legal YAML),
        #    and ~~`_BLOCK.match(val)`~~ read it as the one-line value "|   # the
        #    script", then its body as keys (test_wfparse.py §3).
        if not _BLOCK.match(_uncomment(val)):
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
        out[key] = _value(val)   # a scope's level
    return out


# ══════════════════════════════════════════════════════════════════════
# 🔴 A VALUE IS READ AS YAML MEANS IT: ITS ` # comment` IS NOT PART OF IT.
#    `[2026-11-13]` job_names and job_env already cut it; job_timeouts did not,
#    so `timeout-minutes: 45   # the clock` read as "no clock" (int() failed and
#    was swallowed): runs_report.job_clocks then gave that job GitHub's 360, a run
#    its own 45-minute clock stopped stayed `cancelled`, and the timed-out-run
#    alarm (#333/#334) never fired. The step name / id / if, a step's env and a
#    permissions block kept the comment too. ✅ ONE reader for every scalar
#    value, so the class is fixed in one place; test_wfparse.py §3 sweeps every
#    value of every workflow (deployed and staged) for a comment left in.
# ══════════════════════════════════════════════════════════════════════
def _uncomment(val):
    """A scalar value with its trailing ` # comment` cut, as YAML cuts it. A `#`
    with no space before it, or inside a value that is quoted whole, stays."""
    return _JOB_NAME.match((val or "").strip()).group(1).strip()


def _value(val):
    """A scalar value as YAML means it: the comment cut (`_uncomment`), then the
    quotes."""
    return _uncomment(val).strip("\"'")


class _Unreadable(str):
    """A `timeout-minutes` that is set but is not a whole number: an expression,
    a typo. ⛔ NOT "no clock": a caller that read it as None would give the job
    GitHub's 360 minutes and miss the run its real clock stopped."""


UNREADABLE = _Unreadable("unreadable")


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
                    name = _value(val)
                elif key == "id" and sid is None:
                    sid = _value(val)
                elif key == "run" and run is None:
                    run = body if body is not None else val
                elif key == "if" and cond is None:
                    # ⚠️ the comment cut, never the quotes: `x != '0'` keeps its own
                    cond = body.strip() if body is not None else _uncomment(val)
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


def step_env(src, step_id=None, step_name=None, job=None):
    """One step's OWN `env:` block as {name: value}, found like `step_run`.

    ⛔ Only the step's block: a job- or workflow-level `env:` is not merged
    in. Returns None when the step is not found, {} when it has no `env:`.
    The child column is derived from the first entry, never assumed.
    """
    lines = read(src).splitlines()
    want = [st for st in steps(src, job) if step_id is not None and st.id == step_id]         or [st for st in steps(src, job) if step_name is not None and st.name == step_name]
    if not want:
        return None
    st = want[0]
    entries = [e for e in _scan(lines) if st.start <= e[0] < st.end]
    col, out, inside, child = entries[0][1], {}, False, None
    for _ln, indent, key, val, _body in entries:
        if indent <= col:
            inside, child = (indent == col and key == "env"), None
        elif inside:
            child = indent if child is None else child
            if indent == child:
                out[key] = _value(val)   # a step's own env value
    return out


# `[R1, 2026-10-18]` What a workflow COMMITS and how long its jobs may run:
#    the watchdog's landing check (`watchdog.learners`) derives its class from
#    these, so a new scheduled learner is covered the day it ships (rule 246).
_GIT_ADD = re.compile(r"(?:^|[;&|(]\s*)git\s+add\s+([^;&|#]*)")


def git_adds(src):
    """Every path a `git add` in any step's `run:` body names, in order, once.
    ⛔ Shell comments are not commands; flags and redirections are not paths."""
    out = []
    for st in steps(src):
        for line in (st.run or "").splitlines():
            s = line.strip()
            if s.startswith("#"):
                continue
            for m in _GIT_ADD.finditer(s):
                for tok in m.group(1).split():
                    tok = tok.strip("\"'")
                    if tok and not tok.startswith("-") and not any(ch in tok for ch in "<>$") \
                            and tok not in out:
                        out.append(tok)
    return out


def job_timeouts(src):
    """{job: its `timeout-minutes` as an int, None when the job sets none, or
    `UNREADABLE` when it sets one that is not a whole number (an expression).
    `[2026-11-13]` The comment is cut first (`_value`); ~~an unreadable value
    was None~~, which every caller took for "no clock"."""
    lines = read(src).splitlines()
    out = {}
    for jb in jobs(src):
        out[jb.name] = None
        for lineno, indent, key, val, _b in _scan(lines):
            if jb.start <= lineno < jb.end and indent == 4 and key == "timeout-minutes":
                try:
                    out[jb.name] = int(_value(val))
                except ValueError:
                    out[jb.name] = UNREADABLE
    return out


# A value as YAML means it: a quoted string, or text up to a ` # comment`.
_JOB_NAME = re.compile(r'''^("[^"]*"|'[^']*'|.*?)(?:\s+#.*)?$''')


def job_env(src):
    """{job: {name: value}}: each job's OWN job-level `env:` block, never a step's and never the
    next job's. `[2026-11-08]` Three tests had read a job's env as the text from its header down to
    the `render:` job; pr-tests' new `champion` job then sat inside the `offseason` span, and its
    SUITE_SHARD would have passed that check for a job that had lost its own (the review of PR §3j)."""
    lines = read(src).splitlines()
    out = {}
    for jb in jobs(src):
        env, inside = {}, False
        for lineno, indent, key, val, _b in _scan(lines):
            if not jb.start <= lineno < jb.end:
                continue
            if indent <= 4:
                inside = indent == 4 and key == "env"
            elif inside and indent == 6:
                env[key] = _JOB_NAME.match(val).group(1).strip("\"'")
        out[jb.name] = env
    return out


def job_names(src):
    """{job: its own `name:` as written, or None when GitHub lists it by id}."""
    lines = read(src).splitlines()
    out = {}
    for jb in jobs(src):
        out[jb.name] = None
        for lineno, indent, key, val, _b in _scan(lines):
            if jb.start <= lineno < jb.end and indent == 4 and key == "name":
                out[jb.name] = _JOB_NAME.match(val).group(1).strip("\"'") or None
    return out


# ══════════════════════════════════════════════════════════════════════
# 🔴 WHICH TEST FILES A STEP RUNS. `[2026-11-21]`
# ══════════════════════════════════════════════════════════════════════
# browser.yml's render job ran its five render files TWICE: "Render tests",
# then "A skipped render check is a failure in THIS workflow" ran all five
# again only to grep their output for NO BROWSER (402s of the job's 873s on
# run 44886195117; with a slow install, 1273s of its 1500s clock on #252).
# `test_tests_run_once.py` asks it of every workflow as it will be live: no
# test file is run by two steps of one job.
# ⚠️ What a step RUNS, never what it mentions. `[2026-11-21, review]` The
#    body is split into words the way bash splits it (~~a pattern over the
#    text: `echo "python test_a.py failed"` counted as a run, and a `done`
#    inside a string ended a loop early~~): quotes, `\` continuations, `#`
#    comments and heredoc bodies are text, never commands; `$(...)`,
#    backticks and `<(...)` are commands, even inside "...".
#    ✅ A runner counts only where a COMMAND starts (a line's start, after
#    ; && || | & ( ) if then elif else do ! {), after any VAR=value words
#    and any wrapper: timeout, env, nice, nohup, time, command, exec,
#    stdbuf, xvfb-run, or a function the step defines that runs its own
#    first argument as a command (run_one's `timeout ... "$1" "$2"`, so
#    `run_one python "$t"`); one that only prints them (`say() { echo
#    "$@"; }`) is no wrapper.
#    A runner is python, python3, python3.N or node, any path in front; its
#    file is its first word after its own options (python's -X and -W take
#    a value; -c and - run no file; -m test_x runs test_x.py), any path in
#    front. A loop runs its words when its body runs "$VAR" that way:
#    `for VAR in WORDS` (a glob, or the globs in a `$(ls GLOB)`, matched
#    against `files`, the test files that exist), and `... | while read
#    VAR` or `... | xargs [-I R] RUNNER [R]`, read as yielding every test
#    file the commands piped in name.
# ⛔ It cannot see: a script handed to another shell or runner as a string
#    or on stdin (`bash -e "$loop"`: pr-tests' staged, offseason and
#    champion jobs; `bash -c "..."`; `bash <<EOF`; `python - < test_x.py`);
#    a file name kept in a variable outside a loop, or built from pieces
#    (`T=test_a.py; python "$T"`, `python "test_$x.py"`); an array loop
#    (`"${files[@]}"`); a loop fed by a redirection (`done < list`); `find
#    -exec`; a function that runs its own argument (`f() { python "$1"; };
#    f test_a.py`); a test runner such as pytest; a harness that runs tests
#    itself (vacuity.py); a test started from Python.
_TEST_WORD = re.compile(r"^test_[\w.*?\[\]-]*\.(?:py|js)$")
_TEST_FILE = re.compile(r"^test_[\w.-]*\.(?:py|js)$")
_RUNNER_WORD = re.compile(r"^(?:python(?:\d+(?:\.\d+)?)?|node(?:js)?)$")
_VAR_REF = re.compile(r"^\$(?:\{([A-Za-z_]\w*)\}|([A-Za-z_]\w*))$")
_ASSIGN = re.compile(r"^[A-Za-z_]\w*(?:\[[^\]]*\])?\+?=")
_FUNC_NAME = re.compile(r"^[A-Za-z_][\w-]*$")
_SUB = "\x00"        # where a `$(...)` stood in a word: never part of a file name
_OPS = ("<<<", "<<-", "&>>", "<<", ">>", "<&", ">&", "&>", "<>", ">|", "&&", "||",
        ";;", "|&", ";", "&", "|", "(", ")", "<", ">")
_REDIRS = {"<<<", "&>>", ">>", "<&", ">&", "&>", "<>", ">|", "<", ">"}   # each takes a word
_KEYWORDS = {"then", "else", "elif", "if", "fi", "!", "{", "}", "esac"}
_LOOP_WORDS = {"for", "while", "until", "do", "done"}
_ARG_CMD = {"$1", "${1}", "$@", "${@}", "$*", "${*}"}   # a function running its argument
# A wrapper runs the command after it -> its own options that take a value.
_WRAPPERS = {"timeout": {"-k", "-s", "--kill-after", "--signal"},
             "env": {"-u", "--unset", "-C", "--chdir"}, "nice": {"-n", "--adjustment"},
             "nohup": set(), "time": set(), "command": set(), "exec": {"-a"},
             "stdbuf": {"-i", "-o", "-e"}, "xvfb-run": {"-n", "-s", "-e", "-f", "-p", "-w"}}
_NODE_ARG = {"-r", "--require", "--import", "--loader", "--experimental-loader",
             "-C", "--conditions"}
_XARGS_ARG = {"-n", "-L", "-P", "-d", "-E", "-s", "-a", "-I"}
_READ_ARG = {"-d", "-n", "-N", "-p", "-t", "-u", "-a", "-i"}


def _close_of(s, i, opener, closer, depth=1):
    """The index just past the `closer` that balances `depth` open `opener`s."""
    while i < len(s) and depth:
        if s[i] == "\\":
            i += 1
        elif s[i] == opener:
            depth += 1
        elif s[i] == closer:
            depth -= 1
        i += 1
    return i


def _backtick(s, i):
    """The index of the backtick that closes one opened just before `i`."""
    while i < len(s) and s[i] != "`":
        i += 2 if s[i] == "\\" else 1
    return i


def _dollar(s, i, add, subs, quoted=False):
    """A `$` expansion at `i` -> the index after it. A `$(...)` is commands
    (its tokens join `subs`); `$((...))` is arithmetic; `${...}` is kept."""
    if s.startswith("$((", i):
        add(_SUB)
        return _close_of(s, i + 3, "(", ")", 2)
    if s.startswith("$(", i):
        toks, j = _lex(s, i + 2, close=True)
        subs.append(toks)
        add(_SUB)
        return j
    if s.startswith("${", i):
        j = _close_of(s, i + 2, "{", "}")
        add(s[i:j])
        return j
    if not quoted and s.startswith("$'", i):
        j = i + 2
        while j < len(s) and s[j] != "'":
            j += 2 if s[j] == "\\" else 1
        add(s[i + 2:j])
        return j + 1
    if not quoted and s.startswith('$"', i):
        return _dquote(s, i + 2, add, subs)
    add("$")
    return i + 1


def _dquote(s, i, add, subs):
    """A "..." string from `i` (just past its quote) -> the index after it.
    Its text is part of one word; a `$(...)` or backtick in it is commands."""
    add("")
    while i < len(s) and s[i] != '"':
        c = s[i]
        if c == "\\" and s[i + 1:i + 2] in ('"', "\\", "$", "`", "\n"):
            add(s[i + 1] if s[i + 1] != "\n" else "")
            i += 2
        elif c == "$":
            i = _dollar(s, i, add, subs, quoted=True)
        elif c == "`":
            j = _backtick(s, i + 1)
            subs.append(_lex(s[i + 1:j].replace("\\`", "`"))[0])
            add(_SUB)
            i = j + 1
        else:
            add(c)
            i += 1
    return i + 1


def _heredoc_word(s, i):
    """A heredoc's delimiter after `<<` -> (the index after it, the word
    with its quotes taken off)."""
    while i < len(s) and s[i] in " \t":
        i += 1
    j = i
    while j < len(s) and s[j] not in " \t\n;&|()<>":
        j += 1
    return j, re.sub(r"[\"'\\]", "", s[i:j])


def _heredoc_end(s, i, delim):
    """The index just past a heredoc body that starts at `i`, its closing
    line included."""
    while i < len(s):
        j = s.find("\n", i)
        j = len(s) if j < 0 else j
        line, i = s[i:j], j + 1
        if line.strip() == delim:
            break
    return i


def _lex(s, i=0, close=False):
    """The shell tokens of `s` from `i` (to the `)` that ends a `$(` when
    `close`) -> (tokens, the index after). A token is ("w", word, subs): the
    word with its quotes taken off, each `$(...)` in it as _SUB and its own
    tokens in `subs`; or ("op", text)."""
    toks, heredocs, depth, n = [], [], 0, len(s)
    word, subs = None, []          # None: between words

    def add(text):
        nonlocal word
        word = (word or []) + [text]

    def flush():
        nonlocal word, subs
        if word is not None:
            toks.append(("w", "".join(word), subs))
        word, subs = None, []

    while i < n:
        c = s[i]
        if c == "\\":
            if s.startswith("\\\n", i):   # a `\` continuation: one line
                i += 2
                continue
            add(s[i + 1:i + 2])
            i += 2
        elif c == "'":
            j = s.find("'", i + 1)
            j = n if j < 0 else j
            add(s[i + 1:j])
            i = j + 1
        elif c == '"':
            i = _dquote(s, i + 1, add, subs)
        elif c == "`":
            j = _backtick(s, i + 1)
            subs.append(_lex(s[i + 1:j].replace("\\`", "`"))[0])
            add(_SUB)
            i = j + 1
        elif c == "$":
            i = _dollar(s, i, add, subs)
        elif word is None and c in "<>" and s.startswith("(", i + 1):   # <(...) >(...)
            sub, i = _lex(s, i + 2, close=True)
            subs.append(sub)
            add(_SUB)
        elif word is None and s.startswith("((", i):                  # (( arithmetic ))
            i = _close_of(s, i + 2, "(", ")", 2)
        elif c == "#" and word is None:                                # a comment, to the line's end
            j = s.find("\n", i)
            i = n if j < 0 else j
        elif c in " \t\r":
            flush()
            i += 1
        elif c == "\n":
            flush()
            toks.append(("op", "\n"))
            i += 1
            for delim in heredocs:          # their bodies start on the next line
                i = _heredoc_end(s, i, delim)
            heredocs = []
        elif close and c == ")" and depth == 0:
            flush()
            return toks, i + 1
        elif c in ";&|()<>":
            if c in "<>" and word is not None and "".join(word).isdigit() and not subs:
                word = None                 # `2>&1`: the 2 belongs to the redirection
            flush()
            op = next(o for o in _OPS if s.startswith(o, i))
            i += len(op)
            depth += (op == "(") - (op == ")" and depth > 0)
            if op in ("<<", "<<-"):         # a heredoc: its body is text, never commands
                i, delim = _heredoc_word(s, i)
                heredocs.append(delim)
            toks.append(("op", op))
        else:
            add(c)
            i += 1
    flush()
    return toks, i


def _unwrap(w, funcs=()):
    """A command's words with the wrappers in front of its runner taken off."""
    while w:
        if w[0] in funcs:                 # a function of this step that runs the command after it
            w = w[1:]
            continue
        takes = _WRAPPERS.get(w[0])
        if takes is None:
            return w
        head, w = w[0], w[1:]
        while w and (w[0].startswith("-") or _ASSIGN.match(w[0])):
            w = w[2:] if w[0] in takes else w[1:]
        if head == "timeout":
            w = w[1:]                     # its duration
    return w


def _runs_arg(w, funcs):
    """Is this command (its words) the function's own first argument, run?"""
    while w and _ASSIGN.match(w[0]):
        w = w[1:]
    return (_unwrap(w, funcs)[:1] or [""])[0] in _ARG_CMD


def _runs_its_argument(body, funcs):
    """Does a function's body (the tokens after `name()`, to its closing
    `}`) run its own first argument as a command: `"$1" "$2"`, `"$@"`,
    after any wrapper or a function already known to be one?"""
    depth, cmd, skip = 0, [], False
    for t in body:
        if t[0] == "op":
            skip = t[1] in _REDIRS
            if not skip:
                if _runs_arg(cmd, funcs):
                    return True
                cmd = []
        elif skip:                        # a redirection's word
            skip = False
        elif not cmd and t[1] in ("{", "}"):
            depth += 1 if t[1] == "{" else -1
            if depth <= 0:
                break
        elif cmd or t[1] not in _KEYWORDS | _LOOP_WORDS:
            cmd.append(t[1])
    return _runs_arg(cmd, funcs)


def _functions(toks, out):
    """`out` with the shell functions `toks` define (`name() {`, `function
    name`) that run their own first argument as a command added: wrappers,
    as `timeout` is."""
    for k, t in enumerate(toks):
        if t[0] != "w":
            continue
        for sub in t[2]:
            _functions(sub, out)
        if k and toks[k - 1][0] != "op":
            continue
        if toks[k + 1:k + 3] == [("op", "("), ("op", ")")] and _FUNC_NAME.match(t[1]):
            name, body = t[1], toks[k + 3:]
        elif t[1] == "function" and k + 1 < len(toks) and toks[k + 1][0] == "w":
            name, body = toks[k + 1][1], toks[k + 2:]
        else:
            continue
        if _runs_its_argument(body, out):
            out.add(name)
    return out


def _target(w):
    """The file a runner command runs: its first word after its own options;
    "" when it names none (xargs supplies it); None when it is no runner, or
    runs code (-c, -e) or stdin (-)."""
    if not w or not _RUNNER_WORD.match(w[0].rsplit("/", 1)[-1]):
        return None
    node = w[0].rsplit("/", 1)[-1].startswith("node")
    i = 1
    while i < len(w):
        a = w[i]
        if a == "--":
            return w[i + 1] if i + 1 < len(w) else ""
        if a == "-" or (node and a in ("-e", "--eval", "-p", "--print")):
            return None
        if not a.startswith("-"):
            return a
        if node or a.startswith("--"):
            i += 2 if a in _NODE_ARG else 1
            continue
        for j, c in enumerate(a[1:], 2):  # python's short options, grouped as getopt reads them
            if c == "c":
                return None
            if c == "m":                  # -m test_x runs test_x.py
                return (a[j:] or (w[i + 1] if i + 1 < len(w) else "")).replace(".", "/") + ".py"
            if c in "XW":                 # -X utf8, -W ignore: an option with a value
                i += j == len(a)
                break
        i += 1
    return ""


def _xargs(w):
    """xargs's own options off its words -> (the command it runs, the word
    its input stands in for: "" when none, appended at the end)."""
    rep, i = "", 0
    while i < len(w) and w[i].startswith("-"):
        if w[i] in _XARGS_ARG:
            rep = w[i + 1] if w[i] == "-I" and i + 1 < len(w) else rep
            i += 2
            continue
        rep = w[i][2:] if w[i].startswith("-I") else rep
        i += 1
    return w[i:], rep


def _read_vars(w):
    """The variables a `read` command fills."""
    out, i = set(), 0
    while i < len(w):
        if w[i] in _READ_ARG:
            i += 2
            continue
        if not w[i].startswith("-"):
            out.add(w[i])
        i += 1
    return out


class _Runs:
    """What one step's tokens run: `out`, the test files, once walked."""

    def __init__(self, files, funcs):
        self.files, self.funcs, self.out, self.loops = files, funcs, set(), []

    def names(self, toks):
        """The test-file words (globs too) among `toks` and their `$(...)`s,
        any path cut off."""
        out = []
        for t in toks:
            if t[0] != "w":
                continue
            base = t[1].rsplit("/", 1)[-1]
            if _TEST_WORD.match(base):
                out.append(base)
            for sub in t[2]:
                out += self.names(sub)
        return out

    def expand(self, names):
        for w in names:
            self.out.update(fnmatch.filter(self.files, w) if any(c in w for c in "*?[") else [w])

    def done(self):
        if self.loops:
            loop = self.loops.pop()
            if loop["runs"]:
                self.expand(loop["items"])

    def command(self, cmd, pipe):
        """One simple command (its word tokens) and the commands piped into it."""
        w = [t[1] for t in cmd]
        while w and _ASSIGN.match(w[0]):
            w = w[1:]
        if w[:1] == ["read"] and self.loops and not self.loops[-1]["open"]:
            self.loops[-1]["vars"].update(_read_vars(w[1:]))
            return
        w = _unwrap(w, self.funcs)
        xargs = w[:1] == ["xargs"]
        rep = None
        if xargs:
            w, rep = _xargs(w[1:])
            w = _unwrap(w, self.funcs)
        target = _target(w)
        if target is None:
            return
        if xargs and target == rep:       # what is piped in is the file
            self.expand(self.names(t for c in pipe for t in c))
            return
        base = target.rsplit("/", 1)[-1]
        if _TEST_FILE.match(base):
            self.out.add(base)
            return
        m = _VAR_REF.match(base)
        for loop in (reversed(self.loops) if m else ()):
            if (m.group(1) or m.group(2)) in loop["vars"]:
                loop["runs"] = True
                break

    def walk(self, toks):
        cmd, pipe, head, skip = [], [], None, False
        for tk in toks:
            if tk[0] == "w":
                for sub in tk[2]:
                    self.walk(sub)
                if skip:                  # a redirection's word
                    skip = False
                elif head is not None:    # for VAR in WORDS
                    if head["var"] is None:
                        head["var"] = tk[1]
                    elif tk[1] == "in" and not head["in"]:
                        head["in"] = True
                    elif head["in"]:
                        head["items"] += self.names([tk])
                elif cmd or tk[1] not in _KEYWORDS | _LOOP_WORDS:
                    cmd.append(tk)
                elif tk[1] == "for":
                    head = {"var": None, "in": False, "items": []}
                elif tk[1] in ("while", "until"):
                    self.loops.append({"vars": set(), "runs": False, "open": False,
                                       "items": self.names(t for c in pipe for t in c)})
                elif tk[1] == "do":
                    if self.loops:
                        self.loops[-1]["open"] = True
                elif tk[1] == "done":
                    self.done()
                continue
            if tk[1] in _REDIRS:
                skip = True
                continue
            if tk[1] in ("<<", "<<-"):
                continue
            if head is not None:          # the loop's words end at ; or a new line
                self.loops.append({"vars": {head["var"]}, "items": head["items"],
                                   "runs": False, "open": False})
                head, pipe = None, []
                continue
            self.command(cmd, pipe)
            pipe = pipe + [cmd] if tk[1] in ("|", "|&") else []
            cmd = []
        if head is not None:
            self.loops.append({"vars": {head["var"]}, "items": head["items"],
                               "runs": False, "open": False})
        self.command(cmd, pipe)


def step_tests(run, files):
    """Every test file one step's `run:` body executes, sorted. `files`: the
    test files that exist, which a loop's glob is matched against."""
    toks = _lex(run or "")[0]
    r = _Runs(files, _functions(toks, set()))
    r.walk(toks)
    while r.loops:                        # a loop with no `done` runs to the end
        r.done()
    return sorted(r.out)


def rerun_tests(src, files):
    """[(job, test file, [the steps that run it])] for every test file two or
    more steps of ONE job run. Should be none."""
    out = []
    for jb in jobs(src):
        by = {}
        for st in steps(src, jb.name):
            for f in step_tests(st.run, files):
                by.setdefault(f, []).append(st.name or st.id or "line %d" % (st.start + 1))
        out += [(jb.name, f, s) for f, s in sorted(by.items()) if len(s) > 1]
    return out


# ══════════════════════════════════════════════════════════════════════
# 🔴 THE CRON TOTAL COUNTS STAGED UPLOADS TOO — SO IT NEVER GOES RED IN
#    THE GAP BETWEEN A PR MERGING AND SAM UPLOADING. `[Sam, 2026-09-23]`
# ══════════════════════════════════════════════════════════════════════
# A cron workflow reaches `.github/workflows/` only by Sam's hand, so it is
# STAGED in `docs/upload/` first. Counting only the deployed folder made
# CLAUDE.md's `CRON TOTAL` wrong for the hours between merge and upload —
# twice on 2026-09-22 (t60r). ✅ Counted across BOTH folders, deduplicated
# by FILE NAME, the total is the same before and after the upload.
# 🔴 `[Sam, 2026-09-23, on PR #145]` ~~the two copies must be identical~~ —
#    A STAGED COPY THAT DIFFERS FROM THE DEPLOYED ONE IS A PENDING UPLOAD,
#    NOT A FAILURE: it is exactly what an update to an existing cron
#    workflow looks like between its PR merging and Sam uploading it. For a
#    pending pair the total counts the STAGED version, because that is what
#    will be live. ⛔ Still strict: `runs_report.stale_uploads` flags a
#    pending upload 48 hours after its PR merged, the same clock as a new
#    staged file — so a wrong upload, which stays pending, is caught too.
# ⛔ ONE COPY (rule 117): test_watchdog.py and test_cfbd_watch.py both read
#    the total from here.
CRON_LINE = re.compile(r"(?m)^\s*-\s*cron:")
DEPLOYED_DIR = os.path.join(".github", "workflows")
STAGED_DIR = os.path.join("docs", "upload")


def _same(root, f):
    """The two copies of `f` are the same file. ⚠️ Line endings ignored and
    nothing else: a file uploaded from a Windows checkout arrives CRLF."""
    a, b = (open(os.path.join(root, sub, f), encoding="utf-8").read().replace("\r", "")
            for sub in (DEPLOYED_DIR, STAGED_DIR))
    return a == b


def cron_files(root="."):
    """{file name: {"crons", "deployed", "staged", "pending"}} for every
    workflow file, in either folder, that declares at least one cron.
    `pending`: staged AND deployed AND different — an update Sam has not
    uploaded yet. Its `crons` is the STAGED count."""
    out, staged_n = {}, {}
    for where, sub in (("deployed", DEPLOYED_DIR), ("staged", STAGED_DIR)):
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".yml"):
                continue
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                n = len(CRON_LINE.findall(fh.read()))
            if not n:
                continue
            e = out.setdefault(f, {"crons": n, "deployed": False, "staged": False})
            e[where] = True
            if where == "deployed":
                e["crons"] = n          # the live file is the one that fires
            else:
                staged_n[f] = n
    for f, e in out.items():
        e["pending"] = bool(e["deployed"] and e["staged"] and not _same(root, f))
        if e["pending"]:
            e["crons"] = staged_n[f]     # what WILL be live once Sam uploads
    return out


def cron_total(root="."):
    """Crons declared across deployed and staged workflows, one per name."""
    return sum(v["crons"] for v in cron_files(root).values())


def pending_uploads(root="."):
    """Names staged AND deployed whose contents differ — updates waiting for
    Sam's hand upload. ⛔ Not a failure by itself; `runs_report` times them."""
    return sorted(f for f, v in cron_files(root).items() if v["pending"])


# ══════════════════════════════════════════════════════════════════════
# 🔴 EVERY WORKFLOW AS IT WILL BE LIVE. `[added 2026-09-24]`
# ══════════════════════════════════════════════════════════════════════
# A check about what the workflows RUN ON (test_runner_image.py) must read
# the file that will fire once Sam's pending uploads land — the staged copy
# when there is one — or it is red for the whole window between a PR
# merging and his upload, which is the red window cron_total() was fixed
# to avoid. ⚠️ A pending upload left too long is still caught: runs_report
# flags it 48h after its PR merged.
def effective_workflows(root="."):
    """{file name: path} for every workflow, the STAGED copy winning."""
    out = {}
    for sub in (DEPLOYED_DIR, STAGED_DIR):   # staged read second, so it wins
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".yml"):
                out[f] = os.path.join(d, f)
    return out


# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 THE SUITE AS IT WILL RUN ONCE SAM UPLOADS. `[added 2026-09-25]`
# ══════════════════════════════════════════════════════════════════════
# `[measured, collect run #1839]` PR #174 staged a new runs.yml; every
# pr-tests job was green; Sam uploaded it and the very next collect run
# went RED — `test_fb_freshness.py` pinned MLB's contract at 16 rows and
# the uploaded watcher switched on a 17th. pr-tests had tested the repo
# as it was, never as it would be. ✅ pr-tests' `staged` job applies these
# files locally and runs the same suite, so a staged upload that would
# turn the suite red is red on the PR, before Sam's hands are involved.
def staged_changes(root="."):
    """Staged workflow names that are NEW or DIFFER (line endings aside)
    from the deployed copy — what Sam's next uploads will change."""
    d = os.path.join(root, STAGED_DIR)
    if not os.path.isdir(d):
        return []
    changed = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".yml"):
            continue
        live = os.path.join(root, DEPLOYED_DIR, f)
        if not os.path.exists(live) or not _same(root, f):
            changed.append(f)
    return changed


def apply_staged(root="."):
    """Copy every staged change over the deployed folder. -> the names.
    ⛔ For a THROWAWAY checkout only (pr-tests' `staged` job): the real
    upload is Sam's, by hand (CLAUDE.md)."""
    names = staged_changes(root)
    os.makedirs(os.path.join(root, DEPLOYED_DIR), exist_ok=True)
    for f in names:
        with open(os.path.join(root, STAGED_DIR, f), "rb") as src, \
                open(os.path.join(root, DEPLOYED_DIR, f), "wb") as dst:
            dst.write(src.read())
    return names


# ══════════════════════════════════════════════════════════════════════
# 🔴 A WORKFLOW UPLOADED TO THE WRONG FOLDER. `[added 2026-09-25]`
# ══════════════════════════════════════════════════════════════════════
# GitHub runs a workflow only from `.github/workflows/`. A copy anywhere
# else never fires, and nothing errors: the upload simply did not happen.
# `[measured 2026-09-25]` 103c7ac put ELEVEN workflow copies in the repo's
# top level (runs.yml's first from 251d4c65, 09-14). They sat there as
# dead duplicates of the real files, one wrong edit away from being the
# copy somebody changed. ⛔ The top level holds no YAML of its own, so ANY
# .yml/.yaml there is a stray — case-blind, since `COLLECT.YML` is the
# same mistake as `collect.yml`.
TOP_LEVEL_YAML = (".yml", ".yaml")


def top_level_yaml(root="."):
    """Every .yml/.yaml directly in `root`, sorted. Should be none."""
    return sorted(f for f in os.listdir(root)
                  if f.lower().endswith(TOP_LEVEL_YAML))
