"""DID THE CARD FAIL FOR A REASON SAM HAS ALREADY ACCEPTED?

🔴 WHY THIS EXISTS. `verify_card` refuses to publish a card that fails its
own checks, and that rule is not negotiable. But on 2026-08-29 Sam looked
at T37 — hitter projections contradicting the market on 5.4% of
high-confidence rows against a pre-registered 5.0% bar — and decided,
deliberately, to LEAVE THE BAR ALONE. **The card therefore stays blocked,
and every single run went red for a decision that had already been made.**

⛔ AN ALARM THAT FIRES EVERY FIFTEEN MINUTES GETS IGNORED, AND IGNORING
RED IS EXACTLY HOW THE ORIGINAL STALENESS SURVIVED A WHOLE DAY. Sam had
to notice the site was wrong and ask.

✅ SO A FAILURE CAN BE **ACCEPTED**, AND ONLY BY SAM, IN WRITING, IN THE
REPO. `card-accepted.txt` lists the check IDs he has looked at and chosen
to live with. If EVERY failing check is on that list, the run stays green
and says loudly what it is carrying. **If ANYTHING ELSE fails — a new
check, or a new reason — the run goes red as before.**

⛔ WHAT THIS IS NOT: it does not move a bar, it does not publish a bad
card, and it does not let ME decide anything. **The card is still
reverted either way.** The only thing that changes is whether the run
SCREAMS about a decision already taken.
⚠️ AND IT IS DELIBERATELY DUMB: an exact prefix match on the check ID. No
pattern matching, no fuzziness — if the wording of a failure changes, it
stops being accepted and the run goes red until a human looks again.

Usage:  python card_gate.py /tmp/vc.txt
        exit 0 -> every failure is accepted (warn, stay green)
        exit 1 -> something is NOT accepted (fail the run)
        exit 2 -> could not tell (fail the run; never guess)
"""
import os
import re
import sys

ACCEPTED_FILE = "card-accepted.txt"


def load_accepted():
    """{check id: reason}. Blank lines and # comments ignored."""
    out = {}
    if not os.path.exists(ACCEPTED_FILE):
        return out
    with open(ACCEPTED_FILE, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            cid, _, why = line.partition("|")
            cid = cid.strip()
            if cid:
                out[cid] = why.strip() or "(no reason recorded)"
    return out


def commented_out():
    """{check id: the commented line}. 🔴 AN ACCEPTANCE THAT LOOKS WRITTEN
    BUT IS COMMENTED OUT IS THE WORST OF BOTH WORLDS.

    `[measured 2026-09-04]` Sam accepted T37 and typed the entry onto the
    end of the file's last line -- which is a bare `#` separator. The
    result was `#T37 | ...`: a perfectly formed entry, in the file, in the
    commit, **and invisible to `load_accepted`.** The run stayed red and
    said only *"NOT an accepted failure -- this is new, look at it"*, which
    is the one thing it was NOT.
    ⛔ THE ENTRY IS STILL NOT HONOURED -- a commented line means disabled,
    and guessing otherwise would let a stray `#` accept a card failure
    nobody signed off. ✅ But the gate now SAYS the entry is sitting there
    commented out, at the exact moment the operator is looking at the
    failure.
    """
    out = {}
    if not os.path.exists(ACCEPTED_FILE):
        return out
    with open(ACCEPTED_FILE, encoding="utf-8") as fh:
        for line in fh:
            body = line.strip().lstrip("#").strip()
            if not line.strip().startswith("#") or "|" not in body:
                continue
            cid = body.partition("|")[0].strip()
            if re.fullmatch(r"T\d+[a-z]?", cid):
                out[cid] = line.strip()
    return out


def failing_checks(path):
    """The check IDs verify_card reported as failing."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except Exception as e:
        print(f"::error::card_gate could not read {path}: {e}")
        return None
    # verify_card prints a final `FAILURES: a, b, c` line
    lines = [l for l in text.splitlines() if l.startswith("FAILURES:")]
    if not lines:
        print("::error::card_gate found no FAILURES: line — refusing to "
              "guess which checks failed")
        return None
    body = lines[-1][len("FAILURES:"):].strip()
    # each failure starts with its check id, e.g. "T37: ..." or "T37 canary: ..."
    ids = re.findall(r"\b(T\d+[a-z]?)\b", body)
    return sorted(set(ids)), body


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/vc.txt"
    got = failing_checks(path)
    if got is None:
        return 2
    ids, body = got
    if not ids:
        print(f"::error::card_gate could not identify a check id in: {body}")
        return 2

    accepted = load_accepted()
    unaccepted = [i for i in ids if i not in accepted]

    print(f"card_gate: failing checks {ids}")
    print(f"card_gate: accepted      {sorted(accepted) or '(none)'}")

    if unaccepted:
        # ⚠️ BEFORE CALLING IT NEW, CHECK WHETHER SOMEBODY ALREADY WROTE IT
        # AND IT IS COMMENTED OUT. Saying "this is new, look at it" about a
        # decision already taken and typed into the file is the most
        # misleading thing this tool can do.
        _hidden = commented_out()
        for i in unaccepted:
            if i in _hidden:
                print(f"::error::{i} IS in {ACCEPTED_FILE} but the line is "
                      f"COMMENTED OUT, so it is not in force. Remove the "
                      f"leading '#' to accept it.")
                print(f"::error::  the line reads: {_hidden[i][:120]}")
        print(f"::error::the card failed on {unaccepted}, which is NOT an "
              f"accepted failure — "
              + ("see the commented-out entr(y/ies) above"
                 if any(i in _hidden for i in unaccepted)
                 else "this is new, look at it"))
        return 1

    for i in ids:
        print(f"::warning::the card is blocked by {i}, an ACCEPTED failure "
              f"— {accepted[i]}")
    print("::warning::the card was NOT published and the page says so. The "
          "run stays green because this decision is already recorded in "
          "card-accepted.txt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
