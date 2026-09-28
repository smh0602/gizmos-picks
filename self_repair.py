#!/usr/bin/env python3
"""SELF-REPAIR TRIAGE: which watcher issue, if any, the repair agent gets --
and when the agent is not started at all.

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

🔴🔴 AND THEN IT HAPPENED AGAIN, WITH REAL FINDINGS `[2026-09-28]`.
self-repair #55-#62: eight passes in 48 hours, every one "Reached maximum
number of turns (40)" after 41 turns, 0 PRs. The one-pass skip worked, so
the agent alternated between #44 (crons that did not fire) and #188 (a
guard red even unmutated), and none of the open issues can be finished by
an agent in 40 turns. Each pass spends Sam's subscription, about 4 a day.
✅ The class, not the instance:
  - STAND DOWN. After `STAND_DOWN_AFTER` passes in a row that end at the
    turn cap, or run to the end and open no PR, triage does not start the
    agent again. Each issue those passes tried gets ONE comment
    (`NEEDS_PERSON`). It stays down until a pull request merges to main
    or the set of issues the agent could be handed changes. The state is
    `data/latest/self-repair-last.json`, landed through push_retry.sh.
  - NOT AGENT-REPAIRABLE. A watcher whose issue no code change can clear
    on its own (cron lateness: `runs_report.py`; the board's delivered
    rate: `calibration.py`) writes `NOT_REPAIRABLE` in its body, and
    triage never hands it to the agent, exactly as with a counter.

Usage (self-repair.yml, with the queue JSON on stdin where it is read):
    python self_repair.py count             -> actionable issues in the queue
    python self_repair.py pick <last>       -> the issue to work, as JSON, or ""
    python self_repair.py key               -> the actionable issue numbers, JSON
    python self_repair.py down-since        -> when the stand-down began, or ""
    python self_repair.py still-down <merged-json>
                                            -> why it stays down, or "" (re-armed)
    python self_repair.py record <issue> <opened> <agent-outcome> <result-file> <key-json>
                                            -> writes the record; prints the
                                               outcome, then the issues to tell
    python self_repair.py tell-body         -> the comment those issues get
"""
import datetime
import json
import os
import sys

# ⛔ ONE COPY EACH. The watcher writes it, triage reads it.
COUNTER = "<!-- gizmo-kind: counter -->"                   # t58_t59.render
NOT_REPAIRABLE = "<!-- gizmo-kind: not agent-repairable -->"  # runs_report, calibration

STATE = os.path.join("data", "latest", "self-repair-last.json")

# 🔴 Sam's numbers `[2026-09-28]`: two passes that could not finish, then
#    stand down. ⛔ The turn cap itself lives in self-repair.yml
#    (`--max-turns`); test_self_repair.py fails if NEEDS_PERSON disagrees.
STAND_DOWN_AFTER = 2
TURNS = 40
NEEDS_PERSON = ("self-repair could not fix this in %d turns; it needs a person."
                % TURNS)

# How a pass ended. Only the two FAILED outcomes count toward a stand-down;
# a PR resets it; an ERROR (the agent never ran, or crashed) changes nothing
# -- that is a different defect and stays a red run.
TURN_CAP, NO_PR, OPENED_PR, ERROR = "turn_cap", "no_pr", "opened_pr", "error"
FAILED = (TURN_CAP, NO_PR)


def is_counter(issue):
    """A progress counter, not a finding: nothing for an agent to repair."""
    return COUNTER in ((issue or {}).get("body") or "")


def is_not_repairable(issue):
    """Its watcher says no code change can clear it on its own."""
    return NOT_REPAIRABLE in ((issue or {}).get("body") or "")


def actionable(queue):
    """The queue without its counters and not-agent-repairable issues, in
    the order given."""
    return [it for it in (queue or [])
            if not is_counter(it) and not is_not_repairable(it)]


def pick(queue, last=""):
    """The first actionable issue that is not the one the last pass could
    not diagnose. -> the issue dict, or None."""
    skip = str(last or "").strip()
    for it in actionable(queue):
        if skip and str(it.get("number")) == skip:
            continue
        return it
    return None


def key(queue):
    """The set of issues the agent could be handed, as sorted numbers.
    ⚠️ A counter or a not-agent-repairable issue opening or closing does not
    change it: the agent would never be handed either, so it re-arms
    nothing."""
    return sorted({int(it["number"]) for it in actionable(queue)})


def load(path=STATE):
    """The record, or {} when there is none yet. ⛔ A file that exists and
    cannot be read raises: "I could not look" is not "never stood down"."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def down_since(state):
    return (state or {}).get("down_since") or ""


def still_down(state, queue, merged):
    """-> why triage stays down (str), or "" when it is armed or re-armed.
    `merged`: [{"number", "mergedAt"}] from `gh pr list --state merged`."""
    since = down_since(state)
    if not since:
        return ""
    if any((m or {}).get("mergedAt") and m["mergedAt"] > since for m in (merged or [])):
        return ""
    if key(queue) != sorted(int(n) for n in (state.get("queue") or [])):
        return ""
    tried = ", ".join("#%s" % n for n in state.get("tried") or []) or "health.json findings"
    return ("standing down since %s: %d passes in a row could not finish (%s). "
            "It starts again when a pull request merges to main or the set of "
            "open watcher issues changes." % (since, state.get("streak", 0), tried))


def outcome(opened, agent, result=None):
    """How this pass ended. `opened`: PRs this pass opened; `agent`: the
    agent step's outcome (success/failure/cancelled/skipped); `result`: the
    agent's execution file, whose last `result` message says why it stopped."""
    if int(opened or 0) > 0:
        return OPENED_PR
    sub = ""
    try:
        with open(result or "", encoding="utf-8") as fh:
            msgs = json.load(fh)
        for m in reversed(msgs if isinstance(msgs, list) else [msgs]):
            if isinstance(m, dict) and m.get("type") == "result":
                sub = m.get("subtype") or ""
                break
    except (OSError, ValueError):
        pass
    if sub == "error_max_turns":
        return TURN_CAP
    if sub == "success" or (not sub and agent == "success"):
        return NO_PR          # it ran to the end and opened nothing
    return ERROR


def advance(prev, issue, how, queue_key, now):
    """-> (the new record, the issues to tell they need a person).
    ⚠️ The agent only runs while armed, so a previous record that was DOWN
    means triage re-armed this pass: the streak starts again from zero."""
    prev = dict(prev or {})
    if down_since(prev):
        prev.update(streak=0, tried=[], down_since=None)
    streak, tried = int(prev.get("streak") or 0), list(prev.get("tried") or [])
    told = [int(n) for n in prev.get("told") or []]
    if how == OPENED_PR:
        streak, tried = 0, []
    elif how in FAILED:
        streak += 1
        if issue and int(issue) not in tried:
            tried.append(int(issue))
    new = {"issue": int(issue) if issue else None,
           "opened_pr": how == OPENED_PR,
           "outcome": how,
           "at": now,
           "streak": streak,
           "tried": tried,
           "queue": sorted(int(n) for n in queue_key or []),
           "down_since": None,
           "told": told,
           "note": ("⛔ The next pass skips `issue` ONLY if opened_pr is false, "
                    "and only for that one pass (rule 238). After %d passes in "
                    "a row that could not finish, `down_since` is set and the "
                    "agent is not started until a PR merges to main or `queue` "
                    "changes." % STAND_DOWN_AFTER)}
    tell = []
    if streak >= STAND_DOWN_AFTER:
        new["down_since"] = now
        tell = [n for n in tried if n not in told]
        new["told"] = told + tell
    return new, tell


def tell_body(state):
    """The ONE comment each tried issue gets when the stand-down begins."""
    return ("%s\n\nIts agent ended %d passes in a row without a pull request "
            "(the last at %s), so self-repair has stopped starting it. It starts "
            "again when a pull request merges to main or the set of open watcher "
            "issues changes. _From `self_repair.py`; this is the only comment it "
            "posts here._" % (NEEDS_PERSON, (state or {}).get("streak", 0),
                              (state or {}).get("at", "?")))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else ""
    if cmd == "down-since":
        print(down_since(load()))
        return 0
    if cmd == "tell-body":
        print(tell_body(load()))
        return 0
    if cmd == "record":
        issue, opened, agent, result, qk = (argv[1:6] + [""] * 5)[:5]
        how = outcome(opened, agent, result)
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        new, tell = advance(load(), issue, how, json.loads(qk or "[]"), now)
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(new, fh, indent=1)
        print(how)
        print(" ".join(str(n) for n in tell))
        return 0
    queue = json.loads(sys.stdin.read() or "[]")
    if cmd == "count":
        print(len(actionable(queue)))
        return 0
    if cmd == "pick":
        it = pick(queue, argv[1] if len(argv) > 1 else "")
        print(json.dumps(it) if it else "")
        return 0
    if cmd == "key":
        print(json.dumps(key(queue)))
        return 0
    if cmd == "still-down":
        print(still_down(load(), queue, json.loads(argv[1] if len(argv) > 1 else "[]")))
        return 0
    print("usage: self_repair.py count|pick|key|down-since|still-down|record|tell-body",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
