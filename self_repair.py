#!/usr/bin/env python3
"""SELF-REPAIR TRIAGE: which watcher issue, if any, the repair agent gets.

🔴 WHY THIS IS A MODULE `[2026-09-26]`. runs.json showed self-repair red
five times in 48 hours (#45, #47, #48, #49, #52), every one "Reached
maximum number of turns (40)". Read from the job logs: ALL EIGHT passes in
that window were handed issue #42, "T58 and T59 are accumulating", whose
own body says *"until then this is a counter, not a finding"*. The agent
was told "Something this repo watches is broken" and to fix it with a
guard; there was nothing broken, so it searched until the turns ran out
(five times) or gave up empty-handed (three times, 19-39 turns). And the
step that should have skipped #42 on the next pass never recorded
anything: its push failed after the agent's step every time.

✅ The fix is at the task, not the turn count:
  - a watcher issue that is a COUNTER says so in its body
    (`COUNTER`, written by the watcher: `t58_t59.py`), and triage never
    hands one to the agent -- a queue holding only counters stands down;
  - the queue order is the caller's (oldest first, `sort_by(.createdAt)`),
    and the one issue the last pass could not diagnose is still skipped
    for that one pass only (rule 238: a permanent skip list is a filtered
    alert).
⛔ Absent the marker an issue IS actionable. Only its writer may declare
it a counter; nothing here guesses from a title or from prose.

Usage (self-repair.yml's triage step, with the queue JSON on stdin):
    python self_repair.py count           -> actionable issues in the queue
    python self_repair.py pick <last>     -> the issue to work, as JSON, or ""
"""
import json
import sys

# ⛔ ONE COPY. The watcher writes it (`t58_t59.render`), triage reads it.
COUNTER = "<!-- gizmo-kind: counter -->"


def is_counter(issue):
    """A progress counter, not a finding: nothing for an agent to repair."""
    return COUNTER in ((issue or {}).get("body") or "")


def actionable(queue):
    """The queue without its counters, in the order given."""
    return [it for it in (queue or []) if not is_counter(it)]


def pick(queue, last=""):
    """The first actionable issue that is not the one the last pass could
    not diagnose. -> the issue dict, or None."""
    skip = str(last or "").strip()
    for it in actionable(queue):
        if skip and str(it.get("number")) == skip:
            continue
        return it
    return None


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else ""
    queue = json.loads(sys.stdin.read() or "[]")
    if cmd == "count":
        print(len(actionable(queue)))
        return 0
    if cmd == "pick":
        it = pick(queue, argv[1] if len(argv) > 1 else "")
        print(json.dumps(it) if it else "")
        return 0
    print("usage: self_repair.py count|pick [last]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
