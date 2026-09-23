#!/usr/bin/env python3
"""
THE WATCHDOG MUST FIRE ON WHAT SAM SAW, AND ON NOTHING ELSE.

🔴 IT IS THE ONLY GUARD IN THIS REPO THAT ASKS A QUESTION ABOUT THE
PRODUCT. Everything else asks about the pipeline — did the job exit 0, is
the artifact younger than its deadline, do the tests pass — and all three
of the failures Sam reported on 2026-09-14 happened with every one of
those GREEN:

    the MLB card missing 10 hours a day, by design
    the football cards carrying NEXT WEEK's game lines
    a check that reddened every run because the product IMPROVED

⛔ SO A WATCHDOG THAT IS WRONG IS WORSE THAN NO WATCHDOG. Two ways, and
this file covers both:

  1. **A MISS** leaves Sam finding out by looking, which is the status quo
     it was written to end.
  2. **A FALSE ALARM** is the one that actually kills it. An alert that
     fires when nothing is wrong gets filtered, and a filtered alert is
     indistinguishable from no alert — which is exactly what
     `test_box_live.py` had already done to the red tick.

🔴 THE FIRST VERSION OF `check_card_present` WAS A FALSE ALARM, CAUGHT BY
DRIVING IT. At 00:47 ET Monday it reported *"no card for 2026-09-14, the
deadline passed 887 minutes ago"* — because it took the day from `now` and
the deadline from `last_due`, and at that hour those are DIFFERENT DAYS.
Sunday's card was on disk, complete. ✅ The day now comes from the deadline
itself, and section 2 drives that exact clock.
"""
import datetime
import json
import os
import re
import shutil
import sys
import tempfile

from tcheck import ck, eq, note

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import watchdog as W  # noqa: E402
import freshness as F  # noqa: E402

UTC = datetime.timezone.utc


class Tree:
    """A temp repo root the watchdog can be pointed at.

    ⛔ `watchdog.ROOT` is module state, so it is swapped and RESTORED
    rather than monkey-patched and left — a test that leaks its fixture
    into the next test file is how a suite starts lying (rule 123).
    """

    def __init__(self):
        self.d = tempfile.mkdtemp()
        for p in ("picks", "data/latest", "data/ncaaf/latest",
                  "data/nfl/latest"):
            os.makedirs(os.path.join(self.d, p), exist_ok=True)
        # 🔴 THE REAL PAGE, OR `page:missing` FIRES ON EVERY FIXTURE —
        #    including the clean one — and section 1 below stops meaning
        #    anything. `test_watchdog_coverage.py` made exactly this
        #    mistake and scored 100%% coverage on it.
        shutil.copy(os.path.join(ROOT, "index.html"),
                    os.path.join(self.d, "index.html"))
        self._old = W.ROOT

    def __enter__(self):
        W.ROOT = self.d
        return self

    def __exit__(self, *a):
        W.ROOT = self._old
        shutil.rmtree(self.d, ignore_errors=True)

    def write(self, rel, obj):
        p = os.path.join(self.d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if isinstance(obj, str):
            open(p, "w", encoding="utf-8").write(obj)
        else:
            json.dump(obj, open(p, "w", encoding="utf-8"))


def keys(out):
    return {i["key"] for i in out["findings"]}


def flat(text):
    """Collapse every run of whitespace, and strip markdown emphasis.

    🔴🔴 FOUR OF MY OWN CHECKS HAVE NOW FIRED ON CORRECT CODE BY SEARCHING
    WRAPPED PROSE RAW. `[2026-09-14, four occurrences in one week]` A
    sentence in a YAML block scalar, a Markdown paragraph or a comment is
    broken by a newline and indentation wherever it happens to wrap — so
    `"Do not merge" in text` is FALSE for a file that says exactly that,
    and `**It must fail on the\\n   defect**` matches nothing at all.
    ⛔ EVERY prose assertion in this file goes through here, so the class
    cannot come back one careless check at a time. ➡️ Ledger rule 257.
    """
    return re.sub(r"\s+", " ", (text or "").replace("*", "").replace("`", ""))


# ══════════════════════════════════════════════════════════════════════
print("═══ 1. 🔴 A CLEAN TREE IS SILENT ═══")
# ⛔ THE FIRST THING TO PROVE, BEFORE ANY DETECTION. A watchdog that
#    cannot be quiet will be muted, and then it detects nothing at all.
with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 4, 47, tzinfo=UTC)   # 00:47 ET Mon
    due = F.last_due(F.CARD, now)
    t.write("picks/%s.json" % F.et_date(due), {"date": F.et_date(due),
                                               "picks": []})
    for lg in ("ncaaf", "nfl"):
        t.write("picks/fb-%s-latest.json" % lg,
                {"date": "2026-09-13", "picks": [], "game_lines": []})
    # ⛔ A DATED CARD OWES A TRACK RECORD, so a "clean" tree must carry
    #    one. The fixture was always incomplete here — it simply did not
    #    matter until a check asked (section 17). A fixture that omits
    #    what the product requires is not a clean tree, it is a broken one
    #    nobody had measured.
    t.write("data/latest/record.json", {"plays": 10, "wins": 6})
    out = W.run(now)
    ck("🔴 nothing is reported when nothing is wrong",
       out["healthy"],
       "⛔ A FALSE ALARM IS THE FAILURE THAT KILLS A WATCHDOG — it gets "
       "filtered, and a filtered alert is no alert. Reported: %s"
       % [i["what"] for i in out["findings"]])

print("\n═══ 2. 🔴🔴 THE CLOCK THAT PRODUCED THE FIRST FALSE ALARM ═══")
# 🔴 00:47 ET MONDAY. The last MLB card deadline that has passed is
#    SUNDAY 10:00 ET — 887 minutes earlier — and the card it owes is
#    SUNDAY'S. Taking the day from `now` demands a Monday card that is not
#    due for another nine hours, and reports its absence as breakage.
with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 4, 47, tzinfo=UTC)
    t.write("picks/2026-09-13.json", {"date": "2026-09-13", "picks": []})
    out = W.run(now)
    ck("🔴 Sunday's card satisfies Sunday's deadline at 00:47 ET Monday",
       "card:mlb" not in keys(out),
       "⛔ THIS IS THE FALSE ALARM THE FIRST VERSION RAISED. The day must "
       "come from the DEADLINE, not from the wall clock. Reported: %s"
       % [i["why"] for i in out["findings"]])
    # ...and the real absence still fires.
with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 4, 47, tzinfo=UTC)
    out = W.run(now)
    ck("✅ ...and a genuinely missing Sunday card DOES fire",
       "card:mlb" in keys(out),
       "the fix must not have bought its silence by never firing. "
       "Reported: %s" % sorted(keys(out)))

print("\n═══ 3. ⏳ BEFORE THE DEADLINE, ABSENCE IS CORRECT ═══")
# ⚠️ GRACE IS NOT LENIENCE. GitHub drops scheduled runs often enough that
#    this project times its crons off :00 for it, so a deadline that
#    passed four minutes ago is not evidence of anything.
with Tree() as t:
    due = F.last_due(F.CARD, datetime.datetime(2026, 9, 14, 18, 0, tzinfo=UTC))
    just_after = due + datetime.timedelta(minutes=5)
    out = W.run(just_after)
    ck("⏳ five minutes past the deadline is NOT an alarm",
       "card:mlb" not in keys(out),
       "⛔ an alarm at 10:05 every morning is an alarm nobody reads by "
       "10:06. Grace is %d minutes. Reported: %s"
       % (W.GRACE_MIN, sorted(keys(out))))
    out = W.run(due + datetime.timedelta(minutes=W.GRACE_MIN + 5))
    ck("🔴 ...and past the grace window it IS",
       "card:mlb" in keys(out),
       "grace that never expires is not grace, it is a disabled check")

print("\n═══ 4. 🔴 THE 2026-09-12 OUTAGE — A REFUSED CARD IS ESCALATED ═══")
# ⛔ `card-verify-failure.txt` WAS BEING WRITTEN INTO THE REPO ON EVERY
#    FAILED PASS FOR THREE AND A HALF HOURS AND NOTHING READ IT. The
#    information was in git the whole time.
with Tree() as t:
    now = datetime.datetime(2026, 9, 12, 18, 0, tzinfo=UTC)
    t.write("picks/%s.json" % F.et_date(F.last_due(F.CARD, now)),
            {"date": "x", "picks": []})
    t.write("data/latest/card-verify-failure.txt",
            "verify_card FAILED at 2026-09-12T16:50:52Z\npass 7 of run 938\n"
            "  FAIL no parlay leg is shorter than the -700 floor\n")
    out = W.run(now)
    f = [i for i in out["findings"] if i["key"] == "verify:mlb"]
    ck("🔴 a refused card is detected",
       bool(f),
       "⛔ THE FILE EXISTED IN GIT FOR 3.5 HOURS AND NOTHING READ IT. "
       "Reported: %s" % sorted(keys(out)))
    ck("🔴 ...and the failing check is quoted, not summarised",
       f and "-700 floor" in f[0]["why"],
       "Sam has to be able to tell a boundary defect from a data outage "
       "from the notification alone. Got: %r"
       % (f[0]["why"][:120] if f else None))
    ck("⛔ ...and NO automatic repair is offered for it",
       f and not f[0]["repair"],
       "🔴 THIS IS THE LIMIT AND IT IS THE POINT. A refused card means "
       "the builder and the verifier DISAGREE, and 'repairing' that means "
       "choosing which half is right — the one thing the disagreement "
       "proves nobody knows. Got repair=%r" % (f[0]["repair"] if f else None))

print("\n═══ 5. 🔴 THE 2026-09-14 DEFECT — A CARD THAT CONTRADICTS ITSELF ═══")
with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 18, 0, tzinfo=UTC)
    t.write("picks/%s.json" % F.et_date(F.last_due(F.CARD, now)),
            {"date": "x", "picks": []})
    t.write("picks/fb-nfl-latest.json", {
        "date": "2026-09-13",
        "picks": [{"commence": "2026-09-13T17:00:00Z"}],
        "game_lines": [{"commence": "2026-09-20T17:00:00Z"}]})
    t.write("picks/fb-ncaaf-latest.json", {"date": "2026-09-12",
                                           "picks": [], "game_lines": []})
    out = W.run(now)
    f = [i for i in out["findings"] if i["key"] == "day:nfl:game_lines"]
    ck("🔴 next week's game lines on a one-day card are detected",
       bool(f),
       "⛔ the card's header promises one day. Nothing in the repo asked "
       "this until today. Reported: %s" % sorted(keys(out)))
    ck("✅ ...and the finding names the day and the offending date",
       f and "2026-09-13" in f[0]["what"] and "2026-09-20" in f[0]["what"],
       "a notification that says 'something is wrong' costs a reader the "
       "whole investigation. Got: %r" % (f[0]["what"] if f else None))
    ck("🔧 ...and it IS repairable, by rebuilding the card",
       f and f[0]["repair"] == "card-fb",
       "unlike a refused card, a stale card built by a fixed builder is "
       "repaired by rebuilding it. Got %r" % (f[0]["repair"] if f else None))

print("\n═══ 6. 🔴🔴 A REPAIR MAY NEVER SPEND ═══")
# 🔴 THE GUARD ON THE GUARD. The repair set is executed unattended on a
#    schedule, so a wrong diagnosis that names a PAID mode is a wrong
#    diagnosis that bills Sam on every run until somebody notices.
# ⛔ `DAILY_CAP` would be the only thing between it and the month.
for m in W.SAFE_REPAIRS:
    ck("🔒 `%s` is a FREE mode" % m,
       m in ("card", "card-fb", "record"),
       "⛔ only local compute over data already on disk may be run by an "
       "unattended repair loop")
ck("🔴 `converge` is NOT in the repair set",
   "converge" not in W.SAFE_REPAIRS,
   "⛔ it is the mode that pulls PAID odds, and the converge loop in the "
   "same job already repairs staleness — naming it here would have the "
   "watchdog racing the thing that was about to fix it, with a paid pull "
   "as the prize")
src = open(os.path.join(ROOT, "watchdog.py"), encoding="utf-8").read()
# 🔴 ~~ck("the watchdog runs nothing itself", "subprocess" not in src ...)~~
#    STRUCK 2026-09-14, and the argument CLAUDE.md requires is this: the
#    check asked the WRONG QUESTION. Its purpose was never "no
#    subprocess" — it was **a reporter's own bug must not be able to
#    spend Sam's money**. `node --check`, which the page-renders check
#    needs, cannot spend anything; meanwhile the old form would have
#    passed a file that called the Odds API through `urllib`.
# ✅ THE REPLACEMENT IS STRICTLY HARDER: it forbids every network
#    primitive outright, forbids the credential by name, and allows
#    subprocess ONLY for parsers on a fixed allowlist. The old check
#    covered one of those three.
for _net in ("urllib", "requests", "http.client", "socket", "httpx"):
    ck("🔒 the watchdog cannot reach the network (%s)" % _net,
       _net not in src,
       "⛔ a reporter that can fetch is a reporter whose bug can BILL. "
       "The old form allowed this and forbade `node --check`, which "
       "bills nothing")
ck("🔒 ...and never touches the API key",
   "ODDS_API_KEY" not in src,
   "⛔ a test must never be able to spend (rule 213); neither must a "
   "watchdog")
_cmds = re.findall(r"subprocess\.run\(\s*\[([^\]]*)\]", src)
_first = [c.split(",")[0].strip().strip('"\'') for c in _cmds]
ck("🔒 ...and every subprocess it runs is a PARSER on the allowlist",
   all(c in ("node",) for c in _first),
   "⛔ the only shelling out permitted here is syntax-checking the page. "
   "Anything else is the watchdog acting instead of reporting. Found: %s"
   % _first)
ck("⛔ ...and the safe list is filtered HERE, not in the workflow",
   "SAFE_REPAIRS" in src and 'i["repair"] in SAFE_REPAIRS' in src,
   "a shell step that decides what is safe to run is a second copy of "
   "that judgement (rule 66) — and it is the copy no test can reach")

print("\n═══ 7. ⛔ A CRASHING CHECK IS A FINDING, NOT A PASS ═══")
# 🔴 THE FAILURE MODE THAT LOOKS EXACTLY LIKE HEALTH. A watchdog that
#    falls over before it looks reports "all clear" — which is the single
#    most dangerous thing it could say.
_orig = W.CHECKS


def _boom(rep, now):
    raise RuntimeError("deliberate")


try:
    W.CHECKS = (_boom,)
    with Tree():
        out = W.run(datetime.datetime(2026, 9, 14, 18, 0, tzinfo=UTC))
    ck("🔴 a check that raises is reported as BROKEN",
       not out["healthy"] and any("watchdog:" in k for k in keys(out)),
       "⛔ 'all clear' from a watchdog that crashed before looking is the "
       "worst output in this repo. Got %r" % out["healthy"])
finally:
    W.CHECKS = _orig

print("\n═══ 8. 📣 THE MESSAGE IS WRITTEN FOR SAM, ON A PHONE ═══")
with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 18, 0, tzinfo=UTC)
    t.write("data/latest/card-verify-failure.txt",
            "FAIL no parlay leg is shorter than the -700 floor\n")
    out = W.run(now)
    body = W.render(out)
ck("📣 the body leads with what a READER would see",
   body.startswith("**The site is showing something wrong right now.**"),
   "not with a stack trace, a job name or an exit code")
ck("⛔ an unrepairable finding says so in words",
   "needs a code change" in body,
   "⚠️ Sam must be able to tell 'the system is retrying' from 'this is "
   "waiting on you' without opening anything. Got: %r" % body[-300:])
ck("✅ ...and the issue states that it closes itself",
   "closes itself when the site is healthy" in body,
   "an issue that has to be tidied by hand is a chore, and chores get "
   "skipped until the tracker is noise")
print("\n═══ 9. 🔴🔴 THE WORKFLOW THAT RUNS IT MUST STILL PARSE ═══")
# 🔴 I BROKE THIS FILE WHILE WRITING THIS FEATURE. A `<<'PY'` heredoc
#    inside the step's YAML block scalar needs its terminator at column 0
#    for bash and inside the block for YAML — it cannot be both — and the
#    whole workflow stopped parsing.
# ⛔ THE BLAST RADIUS IS THE ENTIRE PRODUCT. GitHub does not run a
#    workflow it cannot parse, so every cron in this repo would have gone
#    silent: no odds, no cards, no grading, and NO WATCHDOG TO SAY SO.
#    ⚠️ It is the one failure this watchdog structurally cannot report,
#    which is exactly why it is asserted here instead.
# ⚠️ NO `import yaml`. `test_multileague.py` already records that PyYAML
#    is not guaranteed on the runner and that a test which cannot import
#    blocks every push. So the invariant is checked structurally.
WF = os.path.join(ROOT, ".github", "workflows", "collect.yml")
wf = open(WF, encoding="utf-8").read()
_lines = wf.splitlines()
_jobs = next((i for i, l in enumerate(_lines) if l.rstrip() == "jobs:"), None)
ck("🔴 the workflow has a `jobs:` key at the top level",
   _jobs is not None,
   "if this moved, the check below is measuring the wrong region")
_col0 = [(i + 1, l) for i, l in enumerate(_lines[(_jobs or 0) + 1:], start=_jobs or 0)
         if l and not l.startswith((" ", "#"))]
ck("🔴 nothing after `jobs:` starts at column 0",
   not _col0,
   "⛔ EVERY line below `jobs:` belongs to the job mapping and must be "
   "indented. A column-0 line ends the block scalar it is sitting in and "
   "the file stops being YAML — which is how a shell heredoc terminator "
   "silenced every cron in this repo for the length of one edit. "
   "Found: %s" % _col0[:3])

for step in ("Watchdog", "Commit the repair", "Tell Sam"):
    ck("✅ the `%s` step is present" % step,
       ("- name: %s" % step) in wf,
       "⛔ the alert half is the half that was missing entirely before "
       "2026-09-14; a watchdog nobody hears from is rule 217 again")

# 🔴 `if: always()` ON ALL THREE. The run the watchdog rides on may have
#    ALREADY FAILED — that is precisely the run where Sam most needs to
#    be told what a reader would see. A step that skips on failure is a
#    smoke alarm wired to the light switch.
_tail = wf[wf.index("- name: Watchdog"):]
ck("🔴 every watchdog step runs even when the job has already failed",
   _tail.count("if: always()") >= 3,
   "⛔ the failing run is the one that needs the alert. Found %d "
   "`if: always()` after the watchdog step" % _tail.count("if: always()"))
ck("🔴 the job may write issues",
   "issues: write" in wf,
   "⛔ without it `gh issue create` returns 403, `continue-on-error` "
   "swallows it, and the result is a watchdog that LOOKS installed and "
   "tells nobody anything — worse than not having one, because it is "
   "believed")
ck("⛔ ...and the watchdog cannot redden the run it rides on",
   "sys.exit(0)" in src,
   "⚠️ the ISSUE is the alarm, not the tick. A reporter that fails the "
   "job makes the collector's own status mean two different things")

print("\n═══ 10. 🔧 THE LAST MANUAL STEP IS ONE REPLY, NOT AN UPLOAD ═══")
# 🔴 `[Sam, 2026-09-14: "can we automate fixes within the github repo?"]`
#    The repo already carries `.github/workflows/claude.yml`, so a code
#    defect no longer needs a zip, a Downloads folder and a drag — it
#    needs one reply from a phone, and the fix arrives as a PR with the
#    whole suite run against it.
# ⛔ BUT THE SUMMONS MUST APPEAR ONLY WHERE A PERSON IS ACTUALLY NEEDED.
#    Printed on a finding the system is already repairing, it trains Sam
#    to skip the line — the same death as a false alarm (rule 238).
with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 18, 0, tzinfo=UTC)
    # ⛔ A FOOTBALL refusal, and MLB left healthy. The fixture has to
    #    isolate ONE fault or the body is a mix and the assertion below
    #    cannot say which half produced the sentence it found.
    t.write("picks/%s.json" % F.et_date(F.last_due(F.CARD, now)), {"picks": []})
    t.write("picks/fb-nfl-latest.json", {"date": "2026-09-13"})
    t.write("picks/fb-ncaaf-latest.json", {"date": "2026-09-12"})
    t.write("data/ncaaf/latest/card-verify-failure.txt", "  FAIL something\n")
    body_unrepairable = W.render(W.run(now))
ck("🔧 an UNREPAIRABLE finding offers the one-reply route",
   "@claude" in body_unrepairable and "pull request" in body_unrepairable,
   "⛔ this is the difference between 'Sam has to build and upload a "
   "drop' and 'Sam taps reply'. Got: %r" % body_unrepairable[-300:])
ck("🔴 ...and it repeats the two rules that must not be broken",
   "do not weaken a check" in body_unrepairable
   and "do not touch MLB" in body_unrepairable,
   "⚠️ the agent that answers reads CLAUDE.md, but the summons is the "
   "prompt and a prompt that omits the constraints is a prompt that "
   "invites breaking them")

with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 18, 0, tzinfo=UTC)
    t.write("picks/%s.json" % F.et_date(F.last_due(F.CARD, now)),
            {"date": "x", "picks": []})
    t.write("picks/fb-nfl-latest.json", {
        "date": "2026-09-13", "picks": [],
        "game_lines": [{"commence": "2026-09-20T17:00:00Z"}]})
    t.write("picks/fb-ncaaf-latest.json", {"date": "2026-09-12",
                                           "picks": [], "game_lines": []})
    out_rep = W.run(now)
    body_rep = W.render(out_rep)
ck("⛔ a REPAIRABLE finding does NOT summon anybody",
   out_rep["repairs"] and "@claude" not in body_rep,
   "⚠️ the system is already rebuilding this card. A summons here is an "
   "interruption for something that fixes itself, and interruptions that "
   "turn out to be nothing are how the channel dies. repairs=%s"
   % out_rep["repairs"])

# 🔴 THE SEAM, ASSERTED IN THE WORKFLOW THAT OWNS IT. Without
#    `allowed_bots` the action refuses a `github-actions[bot]` actor, so a
#    watchdog issue could never reach Claude at all.
# ⚠️ ASSERTED AS PRESENT, NOT AS WORKING — upstream issue #900 reports the
#    bot check running BEFORE this input is consulted, and this repo
#    cannot test somebody else's action. ⛔ So the check owns the thing it
#    can actually own: that the line is there and the reason is written
#    down beside it.
CY = os.path.join(ROOT, ".github", "workflows", "claude.yml")
if os.path.exists(CY):
    cy = open(CY, encoding="utf-8").read()
    ck("🔧 claude.yml names the bot the watchdog posts as",
       "allowed_bots" in cy and "github-actions[bot]" in cy,
       "⛔ the action rejects bot actors outright unless they are named, "
       "so without this a detected fault can never reach Claude on its "
       "own")
    ck("⚠️ ...and it is labelled as unverified rather than promised",
       "may simply not work" in cy.lower() or "900" in cy,
       "🔴 upstream issue #900: the bot check may run before "
       "`allowed_bots` is read. Claiming this works when it might not is "
       "the same error as a false green")
    ck("⛔ ...and the issue trigger it depends on is wired",
       "issues:" in cy and "opened" in cy,
       "the watchdog OPENS an issue; if the workflow only listens to "
       "comments, the automatic arm is dead on arrival")
else:
    note("⚠️ NOT EXERCISED: no .github/workflows/claude.yml in this tree.")

# 🔴 AND THE FREEZE HAS TO BE VISIBLE TO AN AGENT INSIDE THE REPO.
CM = os.path.join(ROOT, "CLAUDE.md")
# `[rewritten 2026-09-22 — Sam lifted the freeze: "unfreeze all mlb"]`
# ⛔ THE OLD CHECK ASKED "IS THE FREEZE IN CLAUDE.md?" — THE WRONG QUESTION
#    once Sam lifted it. The thing that must hold is that the CURRENT MLB
#    policy is readable inside the repo, is cited to Sam, and that the
#    self-repair prompt says the SAME thing. The new check is harder: the
#    old one never noticed the prompt and CLAUDE.md disagreeing.
_cmf = flat(open(CM, encoding="utf-8").read())
_closed = "MLB IS CLOSED FOR WORK" in _cmf and "SUPERSEDED" not in _cmf.split("MLB IS CLOSED FOR WORK")[1][:400]
_open = "MLB IS OPEN FOR WORK" in _cmf
ck("🔴 the CURRENT MLB policy is in CLAUDE.md, not only in Sam's project docs",
   _closed != _open,
   "⛔ it lived only in the project docs until 2026-09-14, which meant "
   "the Claude Code GitHub Action — an agent working INSIDE this "
   "repository — could not see it at all. A rule the actor cannot read "
   "is not a rule, it is a hope. Exactly one of closed/open must be live")
ck("⛔ ...and the policy is cited to Sam, with a date",
   re.search(r"MLB IS (?:OPEN|CLOSED) FOR WORK[^\n]{0,40}\[Sam, 20\d\d-\d\d-\d\d\]", _cmf) is not None,
   "a policy nobody can trace to Sam is a policy an agent may argue with")
_SRP = os.path.join(ROOT, ".github", "workflows", "self-repair.yml")
if os.path.exists(_SRP):
    _sr = open(_SRP, encoding="utf-8").read()
    ck("🔴🔴 ...and the self-repair prompt states the SAME MLB policy",
       ("MLB IS FROZEN" in _sr) == _closed and ("MLB IS OPEN FOR REPAIR" in _sr) == _open,
       "⛔ an agent reads BOTH. If CLAUDE.md says open and the prompt says "
       "frozen, every MLB finding is silently left; the reverse lets an "
       "agent edit a frozen file. Sam hand-uploads self-repair.yml")

# 🔴🔴 AND SO IS THE RULE THAT EVERY FIX SHIPS WITH A GUARD — which this
#    assertion is itself an instance of. `[Sam, 2026-09-14: "from now on
#    when you notice a problem not only do we need a fix to it now, but we
#    also need a automated fix for said problem."]`
# ⛔ A PROCESS RULE THAT LIVES ONLY IN A CHAT IS THE WEAKEST KIND. The
#    agent that opens self-repair PRs reads CLAUDE.md and nothing else of
#    Sam's, so a standing instruction absent from that file binds nobody
#    at 3am — which is precisely when it is needed.
_cm = flat(open(CM, encoding="utf-8").read())
ck("🔴 the every-fix-ships-with-a-guard rule is in CLAUDE.md too",
   "EVERY FIX SHIPS WITH A GUARD" in _cm,
   "⛔ the Tier 3 agent reads CLAUDE.md. A rule it cannot read is a rule "
   "that stops existing the moment nobody is watching")
# 🔴🔴 AND NOW THE RULE THAT ONLY STARTED MATTERING ON 2026-09-15, THE
#    DAY A SESSION COULD PUSH HERE. `[rule 276]` ⛔ The session that built
#    most of this could NOT push — a human read every file on its way in.
#    A session that can push has no such reader, and **the project docs
#    that carry all the reasoning are not in this repo and it cannot read
#    them.** So the constraint has to live where it CAN read it.
ck("🔴🔴 the push-era rules are in CLAUDE.md, where a repo-only session sees them",
   "IF YOU CAN PUSH TO THIS REPO" in _cm,
   "⛔ a repo-connected session has CLAUDE.md and nothing else of Sam's. "
   "Rule 276 lives here or it binds nobody")
ck("⛔ ...and the cron-block exception is stated, not implied",
   "cron:" in _cm and "by hand" in _cm.lower(),
   "🔴 RULE 253, THE SUICIDE PATH: GitHub attributes a scheduled run to "
   "whoever last changed the cron block. If that becomes a bot, every "
   "cron stops firing silently and the watchdog cannot report it — "
   "because the watchdog is what summons the agent")
# 🔴🔴 ~~`"50 crons" in _cm`~~ — **STRUCK. IT PINNED A NUMBER THAT WAS
#    ALREADY WRONG WHEN I WROTE IT.** The real total was 51 the moment
#    `calibration.yml` landed, and this assertion would have gone RED on
#    anyone who corrected the prose — a guard firing on a fix.
# ⛔ RULE 166: A NUMBER WRITTEN DOWN IS A CLAIM ABOUT THE WORLD, AND IT
#    GOES STALE. `[caught 2026-09-15 by the repo-connected session, which
#    noticed the count was 51 and correctly refused to edit the prose
#    because a test asserted the literal string.]`
# ✅ DERIVED INSTEAD, copying `test_cron_wiring.py`'s existing pattern for
#    collect.yml's own header — the count is read from the workflows and
#    the doc must agree with it.
# 🔴 `[2026-09-23, Sam]` ~~deployed folder only~~ — COUNTED ACROSS
#    `.github/workflows/` AND `docs/upload/`, deduplicated by file name, by
#    the ONE counter in `wfparse.py`. The total now reads the same before
#    and after Sam's hand upload, so a staged cron no longer turns the
#    suite red in between. ⛔ Not looser: the copies must be identical
#    (`wfparse.staged_mismatches`, checked in test_runs_report.py).
import wfparse as _wfp  # noqa: E402
_total = _wfp.cron_total(ROOT)
_claim = re.search(r"<!--\s*CRON TOTAL:\s*(\d+)\s*-->",
                   open(CM, encoding="utf-8").read())
ck("🔴 CLAUDE.md states its cron total in a machine-readable form",
   bool(_claim),
   "⛔ expected `<!-- CRON TOTAL: <n> -->`. Without it the number goes "
   "back to being folklore, which is how it was wrong on arrival")
if _claim:
    eq(int(_claim.group(1)), _total,
       "🔴 ...and the stated total matches the crons actually scheduled")
note("⚠️ %d IS NOT ENDORSED BY THIS CHECK. It pins the doc to the "
     "workflows, nothing more. ⛔ If it fails, do not edit the number to "
     "match — ask whether a cron was added or lost on purpose." % _total)
ck("⚠️ ...and it separates what was measured from what was not",
   "measured" in _cm.lower() and "not measured" in _cm.lower(),
   "⛔ the push and the scope were MEASURED; whether a cron-block change "
   "under that author kills scheduled runs was NOT, and the test is "
   "destructive. Collapsing those two into one confident sentence is "
   "how this session got three causes wrong in one night")
ck("⛔ ...and it tells a repo-only session to ASK rather than infer",
   "do not infer" in _cm.lower(),
   "🔴 the claude/ docs do not exist in this repo. A session that "
   "guesses what they said is a session acting on invented context")
ck("⛔ ...and it demands the guard be PROVEN to fail, not merely written",
   "must fail on the defect and pass after the fix" in _cm.lower(),
   "🔴 an unproven guard is the failure mode this repo keeps shipping: "
   "an empty match, a stripped comment, a fixture missing the file under "
   "test, a check asserting its own prose (rules 67, 244, 249)")
ck("⛔ ...and `flat()` actually collapses a wrapped sentence",
   "a b c" == flat("a\n   b\n\tc") and "x" == flat("**x**"),
   "🔴 IF THIS FAILS THE TWO CHECKS ABOVE ARE VACUOUS — they would pass "
   "on prose that says nothing, which is rule 67 in the helper rather "
   "than in the assertion. Got %r" % flat("a\n   b\n\tc"))

# 🔴🔴 SAM'S STANDING RULES MUST STAY IN CLAUDE.md, WHOLE.
#    `[Sam, 2026-09-22: "Also add a check in test_watchdog.py that fails if
#    this section or its money rule is ever removed from CLAUDE.md."]`
# ✅ GUARDS THE CLASS, NOT ONE LINE: the section must exist, sit ABOVE
#    every other section, and carry an unbroken run of rules 1..16+ —
#    so dropping ANY rule fails, not only the money one. The money rule
#    is then checked by content, because a rule gutted to its label is
#    a rule removed.
# ⚠️ PROVEN TO BITE below, on mutated copies of the real file, every run.
_SAM_HEAD = "## WORKING WITH SAM — standing rules [Sam, 2026-09-22]"
_MONEY = ("Never buy, subscribe to, upgrade, or sign up for any paid",
          "Never enter payment details",
          "exact added credits per day from budget.py",
          "waits for his yes")


def sam_rules_problems(text):
    """Return what is wrong with the standing-rules section (empty = ok)."""
    i = text.find(_SAM_HEAD)
    if i < 0:
        return ["section heading missing"]
    out = []
    first = re.search(r"(?m)^## ", text)
    if first and first.start() != i:
        out.append("section is not the first section of CLAUDE.md")
    body = text[i + len(_SAM_HEAD):]
    end = re.search(r"(?m)^(?:---\s*$|## )", body)
    body = body[:end.start()] if end else body
    nums = [int(n) for n in re.findall(r"(?m)^(\d+)\. ", body)]
    if nums != list(range(1, len(nums) + 1)) or len(nums) < 16:
        out.append("rules are not an unbroken 1..16+ run: %r" % nums)
    m = re.search(r"(?ms)^1\. (.*?)(?=^2\. |\Z)", body)
    money = flat(m.group(1)) if m else ""
    if not money.startswith("MONEY:"):
        out.append("rule 1 is not the MONEY rule")
    out += ["money rule lost %r" % p for p in _MONEY if p not in money]
    return out


_cmraw = open(CM, encoding="utf-8").read()
_p = sam_rules_problems(_cmraw)
ck("🔴🔴 Sam's standing rules are in CLAUDE.md, whole, money rule first",
   not _p,
   "⛔ a rule an agent cannot read binds nobody. Problems: %r" % _p)
_sec = _cmraw[_cmraw.find(_SAM_HEAD):]
_muts = {
    "section removed": _cmraw.replace(_SAM_HEAD, "## something else"),
    "money rule removed": _cmraw.replace(_sec[:_sec.find("\n2. ")], _SAM_HEAD + "\n"),
    "money rule gutted": _cmraw.replace("exact added credits per day from budget.py", "a rough idea"),
    "rule 7 removed": _cmraw.replace("\n7. Sam gets", "\nSam gets"),
    "section moved down": _cmraw.replace(_SAM_HEAD, "## a\n\n" + _SAM_HEAD, 1),
}
_blind = [k for k, v in _muts.items() if v == _cmraw or not sam_rules_problems(v)]
ck("⛔ ...and that check FAILS on every way of removing them",
   not _blind,
   "🔴 a guard that cannot fail is not a guard. Passed on: %r" % _blind)


print("\n═══ 11. 🔴 A MISSING CARD AND A REFUSED CARD ARE ONE FAULT ═══")
# 🔴 FOUND BY WALKING THE SCENARIO END TO END, NOT BY READING THE CODE.
#    With a refusal file present the watchdog reported the absence AND
#    named `card` as its repair — so the issue said "automatic repair
#    attempted" about a rebuild the same verifier refuses again, for the
#    same reason, on every run.
# ⛔ THE SENTENCE IS THE DANGEROUS PART, not the wasted rebuild: a reader
#    told the system is retrying stops looking.
with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 15, 30, tzinfo=UTC)
    t.write("picks/fb-nfl-latest.json", {"date": "2026-09-13"})
    t.write("picks/fb-ncaaf-latest.json", {"date": "2026-09-12"})
    t.write("data/latest/card-verify-failure.txt", "  FAIL something\n")
    out = W.run(now)
    card = [i for i in out["findings"] if i["key"] == "card:mlb"]
    ck("🔴 a card missing BECAUSE it was refused offers no repair",
       card and card[0]["repair"] is None,
       "⛔ rebuilding it can only be refused again. Got repair=%r"
       % (card[0]["repair"] if card else None))
    ck("✅ ...and it says WHY no repair is attempted",
       card and "refused it" in card[0]["why"],
       "an absent repair with no reason reads as an oversight")
    ck("⛔ ...so nothing claims a retry is under way",
       "Automatic repair attempted" not in W.render(out),
       "🔴 the issue must not tell Sam the system is handling something "
       "that cannot be handled without him")
with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 15, 30, tzinfo=UTC)
    out = W.run(now)
    card = [i for i in out["findings"] if i["key"] == "card:mlb"]
    ck("✅ a card missing with NO refusal still offers the rebuild",
       card and card[0]["repair"] == "card",
       "⛔ the suppression must be caused by the refusal, not by the "
       "check having quietly stopped naming a repair at all. Got %r"
       % (card[0]["repair"] if card else None))

print("\n═══ 12. 🔴🔴 THE SUMMONS MUST NOT CONTRADICT ITSELF ═══")
# 🔴 THE FIRST VERSION ENDED "do not touch MLB" — ON AN ISSUE WHOSE
#    FINDING WAS AN MLB CARD DEFECT. An instruction that forbids the only
#    change that would resolve it produces either nothing or a violation.
# ✅ The freeze becomes an explicit PER-INCIDENT UNLOCK: Sam sees MLB is
#    what broke, sees nothing will be touched until he says so, and can
#    lift it for that one issue in the same tap.
with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 15, 30, tzinfo=UTC)
    t.write("picks/fb-nfl-latest.json", {"date": "2026-09-13"})
    t.write("picks/fb-ncaaf-latest.json", {"date": "2026-09-12"})
    t.write("data/latest/card-verify-failure.txt", "  FAIL something\n")
    body = W.render(W.run(now))
ck("🔴 an MLB finding does NOT tell the fixer to leave MLB alone",
   "do not touch MLB" not in body,
   "⛔ it is the one instruction that cannot be followed here. Got: %r"
   % body[-400:])
ck("✅ ...it states the freeze and asks Sam to lift it for this issue",
   "freeze is lifted for this issue only" in body
   and "Nothing will be changed until you say so" in body,
   "the freeze stays the default; what changes is that the decision is "
   "VISIBLE rather than silently swallowed")
with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 15, 30, tzinfo=UTC)
    t.write("picks/%s.json" % F.et_date(F.last_due(F.CARD, now)), {"picks": []})
    t.write("picks/fb-nfl-latest.json", {"date": "2026-09-13"})
    t.write("picks/fb-ncaaf-latest.json", {"date": "2026-09-12"})
    t.write("data/ncaaf/latest/card-verify-failure.txt", "  FAIL x\n")
    body = W.render(W.run(now))
ck("⛔ a NON-MLB finding still carries the plain do-not-touch-MLB rule",
   "do not touch MLB" in body and "freeze is lifted" not in body,
   "the unlock is per-incident and must not leak onto football issues. "
   "Got: %r" % body[-300:])


print("\n═══ 14. 🔴🔴 A LIST MAY DECLARE ITS OWN SLATE — AND MUST JUSTIFY IT ═══")
# 🔴 THE 9½-HOUR FALSE ALARM OF 2026-09-14 (rule 255). `card_fb` falls
#    forward to the next day with unstarted games so the list is never
#    empty between slates, records `is_next_slate`, and the page prints
#    the sentence. ⛔ The old check read the CARD's date for every list
#    and called that a rule-101 leak — on a correct Saturday card whose
#    next games were Thursday. 35 pointless rebuilds, and it never
#    escalated because it always named a repair.
_CARD = "picks/fb-ncaaf-latest.json"
_NOW = datetime.datetime(2026, 9, 14, 18, 0, tzinfo=UTC)


def _ncaaf(gl_rows, meta=None, card_day="2026-09-12"):
    """A tree holding one ncaaf card; returns the day:ncaaf:game_lines findings."""
    t = Tree()
    t.__enter__()
    try:
        t.write("picks/%s.json" % F.et_date(F.last_due(F.CARD, _NOW)),
                {"date": "x", "picks": []})
        t.write("picks/fb-nfl-latest.json", {"date": card_day,
                                             "picks": [], "game_lines": []})
        doc = {"date": card_day, "picks": [], "game_lines": gl_rows}
        if meta is not None:
            doc["game_lines_meta"] = meta
        t.write(_CARD, doc)
        out = W.run(_NOW)
        return [i for i in out["findings"] if i["key"] == "day:ncaaf:game_lines"]
    finally:
        t.__exit__()


# ✅ THE LIVE SHAPE THAT WAS FALSELY ALARMING — must now be SILENT.
_ok = _ncaaf([{"commence": "2026-09-17T23:00:00Z"}],
             {"slate": "2026-09-17", "card_slate": "2026-09-12",
              "is_next_slate": True})
ck("✅ a list that DECLARES the next slate and matches it is silent",
   not _ok,
   "🔴 this is the exact live card from 2026-09-14 21:19Z: a Saturday "
   "card whose next games are Thursday, labelled `is_next_slate`, with "
   "the sentence rendered on the page. It alarmed for 9½ hours. "
   "Got: %r" % ([i['what'] for i in _ok]))

# ⛔ AND THE CHECK MUST STILL BITE — silence is also what a broken check
#    returns. Each of these four was either caught before and must stay
#    caught, or is a shape the OLD form could not see at all.
_leak = _ncaaf([{"commence": "2026-09-20T17:00:00Z"}])
ck("🔴 rule 241 STILL FIRES — no meta, rows off the card's day",
   bool(_leak),
   "⛔ the original defect: a one-day card publishing next week's lines "
   "with nothing declaring it. If this is silent the whole check is "
   "decoration")

_unannounced = _ncaaf([{"commence": "2026-09-17T23:00:00Z"}],
                      {"slate": "2026-09-17", "card_slate": "2026-09-12"})
ck("🆕 a list that moves day WITHOUT `is_next_slate` is caught",
   bool(_unannounced) and "is_next_slate" in _unannounced[0]["why"],
   "⛔ THE OLD FORM COULD NOT SEE THIS. An unannounced relabel is "
   "indistinguishable from rule 101 leaking again — the flag is the "
   "only thing separating design from defect. Got: %r" % (_unannounced or None))

_backward = _ncaaf([{"commence": "2026-09-05T23:00:00Z"}],
                   {"slate": "2026-09-05", "card_slate": "2026-09-12",
                    "is_next_slate": True})
ck("🆕 a list that falls BACKWARD is caught even when it claims to be next",
   bool(_backward) and "BACKWARD" in _backward[0]["what"],
   "⛔ THE OLD FORM COULD NOT SEE THIS EITHER. 'The next slate' is "
   "always later; an earlier one means the slate was computed from "
   "stale rows, and the flag would have laundered it. Got: %r"
   % (_backward or None))

_liar = _ncaaf([{"commence": "2026-09-12T23:00:00Z"}],
               {"slate": "2026-09-17", "card_slate": "2026-09-12",
                "is_next_slate": True})
ck("🆕 a list that declares a slate and then contradicts it is caught",
   bool(_liar),
   "🔴 THE STRICTLY-HARDER CASE: these rows sit on the CARD's own date, "
   "so the OLD check called them clean — while the meta the page shows "
   "the reader says 2026-09-17. The declaration is what is published. "
   "Got: %r" % (_liar or None))


print("\n═══ 15. 🔴🔴 A REPAIR THAT NEVER WORKS MUST ESCALATE ═══")
# ⛔ THE WORST HOLE IN THE DESIGN, FOUND BY LIVING THROUGH IT. Tier 3 is
#    gated on `unrepairable`. A finding that NAMES a repair is never
#    unrepairable — so a repair that cannot possibly fix it loops
#    forever, the escalation list stays empty, and the agent that exists
#    for exactly this class is never woken. `[measured: 35 rebuilds, 9½
#    hours, zero escalations]`
_STUCK = {"key": "day:ncaaf:game_lines", "severity": "BROKEN",
          "what": "w", "why": "y", "repair": "card-fb"}


def _attempts(prev_attempts, repair_ran=True):
    it = dict(_STUCK)
    prev = {"findings": [dict(_STUCK, repair_attempts=prev_attempts)],
            "repairs": ["card-fb"] if repair_ran else []}
    W._escalate_stuck_repairs([it], prev)
    return it


ck("🔧 a first failure keeps its repair — one miss is not a stuck loop",
   _attempts(0)["repair"] == "card-fb" and _attempts(0)["repair_attempts"] == 1,
   "⛔ the workflow re-checks IMMEDIATELY after repairing, and a rebuild "
   "whose effect lands next cycle would otherwise escalate on a success")
ck("🔧 a second failure still keeps it",
   _attempts(1)["repair"] == "card-fb",
   "three tries, not one — see above")
_esc = _attempts(2)
ck("🔴🔴 the THIRD failure WITHDRAWS the repair",
   _esc["repair"] is None and _esc["repair_withdrawn"] == "card-fb",
   "⛔ this is the line that turns an infinite free loop into something "
   "a human hears about. Got %r" % _esc)
ck("✅ ...and it says why, naming the repair and the count",
   "card-fb" in _esc["why"] and "3 times" in _esc["why"],
   "a withdrawn repair with no explanation reads as the watchdog giving "
   "up. Got: %r" % _esc["why"])
ck("🔴 ...so it now reaches the ESCALATION list that wakes Tier 3",
   _esc["repair"] not in W.SAFE_REPAIRS,
   "⛔ `unrepairable` is built from findings whose repair is not in "
   "SAFE_REPAIRS. That is the whole point of withdrawing it")
ck("⛔ an attempt is NOT charged when the repair was never actually run",
   _attempts(2, repair_ran=False)["repair"] == "card-fb",
   "🔴 a finding whose repair was filtered out by SAFE_REPAIRS was never "
   "tried. Charging it an attempt escalates something nothing has yet "
   "attempted to fix — a false escalation, which is rule 238 wearing a "
   "more expensive coat")
# 🔴🔴 AND THE WITHDRAWAL MUST BE PERMANENT WHILE THE FINDING PERSISTS.
#    `[found 2026-09-14 by driving FOUR cycles instead of three]` Once the
#    repair is withdrawn the report lists no repair, so on the next run
#    `tried` was False, the counter reset to 1 and the repair came back.
# ⛔ ESCALATE, UN-ESCALATE, ESCALATE — a four-cycle loop in which
#    `unrepairable` is non-empty only ONE RUN IN FOUR, so Tier 3 sees the
#    finding a quarter of the time and the useless repair keeps running
#    forever anyway, which is the entire waste this exists to stop.
# ⚠️ THREE CYCLES LOOKED PERFECT. The defect appears only on the fourth.
_after = dict(_STUCK)
_prev_withdrawn = {"findings": [dict(_STUCK, repair=None,
                                     repair_attempts=3,
                                     repair_withdrawn="card-fb")],
                   "repairs": []}
W._escalate_stuck_repairs([_after], _prev_withdrawn)
ck("🔴🔴 a withdrawn repair STAYS withdrawn on the next cycle",
   _after["repair"] is None and _after["repair_withdrawn"] == "card-fb",
   "⛔ THE FIRST VERSION OSCILLATED. A withdrawal that lapses is not an "
   "escalation, it is a pause — and Tier 3 would see the finding one run "
   "in four while the dead repair ran on every one. Got %r" % _after)
ck("✅ ...and the attempt count is carried, not reset",
   _after["repair_attempts"] >= W.REPAIR_ATTEMPTS_BEFORE_ESCALATION,
   "🔴 a reset counter is what let the repair come back. Got %r"
   % _after.get("repair_attempts"))
ck("⛔ ...and it says the withdrawal is standing, not freshly decided",
   "stays withdrawn" in _after["why"],
   "a reader seeing the same finding for the tenth time needs to know "
   "the system already gave up on repairing it, not that it just did")

ck("✅ a finding with NO repair is left alone entirely",
   (lambda i: (W._escalate_stuck_repairs([i], {"findings": [], "repairs": []}),
               "repair_attempts" not in i)[1])(
       {"key": "verify:mlb", "severity": "BROKEN", "what": "w", "why": "y",
        "repair": None}),
   "⛔ a refused card is already unrepairable; counting attempts against "
   "it would be counting nothing")

print("\n═══ 16. 🔴🔴 A FAILING TEST MUST REACH SAM, NOT JUST THE RUN PAGE ═══")
# ⛔ MEASURED 2026-09-14. `test_board_match.js` went red at 20:08Z when a
#    gamelines pull advanced the board past a date literal the test had
#    written down. EVERY collector run for the next 2h25m was red, and
#    THE ONLY ALARM WAS SAM OPENING THE ACTIONS TAB.
# 🔴 The "Tell Sam" step reads `health.json` and nothing else, so a test
#    failure produced a red tick and NO issue, NO email, and nothing the
#    watchdog could see — it asks PRODUCT questions, and a stale test is
#    not a product question. ➡️ Ledger rule 261.
CY = os.path.join(ROOT, ".github", "workflows", "collect.yml")
if not os.path.exists(CY):
    note("⚠️ NOT EXERCISED: collect.yml is not in this tree.")
else:
    _raw = open(CY, encoding="utf-8").read()
    cy = flat(_raw)
    ck("🔴🔴 a failing test opens an issue, not just a red tick",
       "Tell Sam the tests are failing" in cy,
       "⛔ a red run page is not an alert. 47 consecutive red runs "
       "produced zero notifications — the alert channel read health.json "
       "and a test failure never reaches health.json")
    ck("🔴 it is gated on the TEST result, not on the watchdog's",
       "steps.tests.outputs.rc" in cy,
       "⛔ the watchdog's issue is driven by health.json. If this step "
       "keyed on the same thing it would be a second copy of that alarm "
       "and still blind to the suite")
    ck("⛔ the failing FILE NAMES are recorded, not only annotated",
       "steps.tests.outputs.failed" in cy and 'echo "failed=' in _raw,
       "🔴 `::error::` reaches the run page and nowhere else — the exact "
       "surface nobody is watching. An issue that says 'a test failed' "
       "without saying WHICH costs the reader the whole investigation")
    ck("⚠️ it is a DIFFERENT issue from the watchdog's",
       "the test suite is failing" in cy and "the watchdog says the site is wrong" in cy,
       "⛔ 'the site is wrong' and 'a test is failing' are different "
       "problems with different fixes. Merging them hides whichever "
       "arrived second")
    ck("✅ ...and it closes itself when the suite goes green",
       "the suite is green again" in cy and "gh issue close" in cy,
       "an alert that must be closed by hand is an alert that stays open "
       "and stops meaning anything (rule 238's cousin)")
    ck("🔴 it can NEVER take the data down with it",
       "- name: Tell Sam the tests are failing if: always() continue-on-error: true"
       in cy.replace("  ", " ").replace("  ", " "),
       "⛔ the collector's job is to land data on time. An alerting step "
       "that can fail the job would turn a notification bug into an "
       "outage — and this repo has already shipped a workflow that "
       "stopped parsing (rule 242)")
    ck("⛔ ...and it runs BEFORE the deferred failure, or it never runs at all",
       cy.index("Tell Sam the tests are failing") < cy.index("Fail if the tests failed"),
       "🔴 the deferred-failure step exits 1. Anything after it that is "
       "not `always()` is dead code, and putting the alert there would "
       "mean the alert fires only when there is nothing to alert about")
    ck("⚠️ the issue body refuses the weakening fix in advance",
       "do not fix this by weakening the check" in cy.lower(),
       "🔴 CLAUDE.md's first rule, said at the moment somebody is most "
       "tempted: staring at a red tick they want gone")

print("\n═══ 17. 🔴🔴 A MISSING TRACK RECORD WAS SILENTLY SKIPPED ═══")
# ⛔ FOUND 2026-09-14 BY DELETING IT AND WATCHING NOTHING HAPPEN. The
#    watchdog reported `healthy: true` with the page's whole Track Record
#    tab gone. `check_record_written` opened with `if not exists: continue`
#    — so the check written to notice "the record stopped being graded"
#    treated THE FILE BEING GONE ENTIRELY, the most complete form of that
#    failure, as nothing to say. ➡️ An absence read as silence is this
#    project's oldest recurring error. Ledger rule 265.
# ⚠️ AND THE `continue` WAS NOT WRONG, IT WAS UNCONDITIONAL — a league
#    with nothing published has no record to grade and MUST stay quiet.
with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 18, 0, tzinfo=UTC)
    t.write("picks/%s.json" % F.et_date(F.last_due(F.CARD, now)),
            {"date": "x", "picks": []})
    for lg in ("ncaaf", "nfl"):
        t.write("picks/fb-%s-latest.json" % lg,
                {"date": "2026-09-13", "picks": [], "game_lines": []})
    t.write("picks/2026-09-13.json", {"date": "2026-09-13", "picks": []})
    # mlb has a DATED published card; no record.json anywhere in this fixture.
    out = W.run(now)
    f = [i for i in out["findings"] if i["key"] == "record:mlb"]
    ck("🔴🔴 a record.json that is GONE is reported, not skipped",
       bool(f),
       "⛔ THE WATCHDOG SAID `healthy: true` WITH THE TAB DEAD. Deleting "
       "the file was the one case the age check could never see. "
       "Reported: %s" % sorted(keys(out)))
    ck("🔧 ...and it offers the `record` repair, which is proven to rebuild it",
       f and f[0]["repair"] == "record",
       "⛔ this is not a code defect — the file is regenerated from the "
       "stored box scores. Driven end to end 2026-09-14: deleted all "
       "three, `collect.py record` restored all three. Got %r"
       % (f[0]["repair"] if f else None))
    ck("✅ ...and it says WHY it is owed, with the card count",
       f and "published" in f[0]["why"],
       "a missing file is only wrong if something was owed. The finding "
       "has to carry that evidence or it reads as a guess. Got: %r"
       % (f[0]["why"] if f else None))
    ck("⛔ ...and the football leagues, which have only a `-latest` card, "
       "stay SILENT in the same tree",
       not [i for i in out["findings"]
            if i["key"] in ("record:ncaaf", "record:nfl")],
       "🔴 `fb-<lg>-latest.json` is the CURRENT card pointer, not "
       "published history. My first `_published` globbed it and "
       "false-alarmed on three existing checks inside a minute — "
       "including the clean-tree test whose whole job is proving the "
       "watchdog can be quiet. Reported: %s" % sorted(keys(out)))

# ⛔ AND THE QUIET HALF, WHICH IS WHAT THE ORIGINAL `continue` PROTECTED.
with Tree() as t:
    now = datetime.datetime(2026, 9, 14, 18, 0, tzinfo=UTC)
    t.write("picks/%s.json" % F.et_date(F.last_due(F.CARD, now)),
            {"date": "x", "picks": []})
    t.write("data/latest/record.json", {"plays": 1, "wins": 1})
    for lg in ("ncaaf", "nfl"):
        t.write("picks/fb-%s-latest.json" % lg,
                {"date": "2026-09-13", "picks": [], "game_lines": []})
    out = W.run(now)
    ck("⛔ a league with NOTHING published stays silent about its record",
       not [i for i in out["findings"] if i["key"] in ("record:ncaaf", "record:nfl")],
       "🔴 `picks/fb-<lg>-latest.json` is not a dated published card. A "
       "league with no graded history owes no record, and alarming on it "
       "would be rule 238 — the false alarm that gets the channel "
       "filtered. Reported: %s" % sorted(keys(out)))
    ck("✅ ...and `_published` counts the evidence rather than assuming it",
       W._published("nfl") >= 0 and isinstance(W._published("mlb"), int),
       "the difference between 'owed' and 'not owed' is a fact about the "
       "repo, so it is READ from the repo")

print("\n═══ 13. 🔧 TIER 3 SELF-REPAIR — THE GATE AND ITS GUARDS ═══")
# 🔴 `[Sam, 2026-09-14: "make tier 3 be able to self repair"]` — the
#    findings nothing mechanical can fix. `self-repair.yml` runs the
#    Claude Code GitHub Action on a SCHEDULE, which is the seam that
#    makes it work at all: the action rejects bot actors, the watchdog
#    posts as `github-actions[bot]`, and `allowed_bots` is unreliable
#    (upstream #900).
#
# ⚠️⚠️ **THE STATED REASON WAS WRONG AND IS REPLACED HERE (2026-09-14).**
#    ~~"a schedule has NO EXTERNAL ACTOR, so both checks are bypassed"~~ —
#    that is `docs/security.md`, but **Anthropic's product docs say the
#    bot check DOES apply to scheduled runs**, attributing them to *"the
#    [user] who last changed the workflow's `cron` schedule"*. ⛔ Two
#    Anthropic sources disagree, so the QUESTION changes: not *"is the
#    actor exempt?"* (unanswerable from here) but *"does this workflow
#    survive the check applying?"* — which is testable, and which the old
#    assertion never asked. **Strictly harder: it now demands a guard the
#    old version did not require to exist at all.**
SR = os.path.join(ROOT, ".github", "workflows", "self-repair.yml")
if not os.path.exists(SR):
    note("⚠️ NOT EXERCISED: self-repair.yml is not in this tree.")
else:
    sr = open(SR, encoding="utf-8").read()
    # ⚠️ WHITESPACE NORMALISED BEFORE SEARCHING. The prompt is wrapped
    #    prose inside a YAML block scalar, so "Do not merge" is split
    #    across a newline and thirteen spaces of indentation. My first
    #    version searched the raw text and failed on two assertions that
    #    were factually TRUE — a check that fails on correct code, which
    #    is the other way to be useless (rule 249).
    srn = " ".join(sr.split())
    ck("🔴 it is triggered by a SCHEDULE, not by the watchdog's bot",
       "schedule:" in sr and "cron:" in sr,
       "⛔ triggering off the bot's own issue depends on `allowed_bots`, "
       "which upstream #900 says may never be consulted. A schedule does "
       "not need it: the write-access check is exempt for `schedule`, "
       "and the actor is whoever last committed the cron block")
    # 🔴🔴 THE CHECK THE OLD ONE SHOULD HAVE BEEN. GitHub attributes a
    #    scheduled run to the user who last changed the `cron:` block. If
    #    a merged self-repair PR ever edits this file, that user becomes
    #    the Claude GitHub App — a BOT — and the action's own actor check
    #    starts rejecting the run. ⛔ It fails SILENT: no red run, no
    #    alert, and the only symptom is a repair that stops happening.
    ck("🔴🔴 the prompt forbids the agent from editing self-repair.yml "
       "itself",
       "DO NOT MODIFY `.github/workflows/self-repair.yml`" in srn,
       "⛔ GitHub attributes a scheduled run to whoever last changed the "
       "cron schedule. An agent that edits this file makes a BOT that "
       "user, and the action's actor check then rejects every future "
       "run — with no red run and no alert. Sam uploads this file by "
       "hand, which is what keeps the actor human; nothing else does")
    ck("⛔ ...and the file says WHY, so the next reader cannot delete the "
       "line as noise",
       "attributes a scheduled run to the user who last changed" in srn,
       "🔴 a bare prohibition with no reason is the first thing removed "
       "in a cleanup. The reason IS the guard")
    ck("⚠️ the two disagreeing Anthropic sources are both named in the "
       "file, not silently picked between",
       "code.claude.com" in sr and "security.md" in sr.replace(
           "docs/security.md", "security.md"),
       "⛔ this repo's founding lesson is that a fact about a QUERY is "
       "not a fact about the world. Two Anthropic docs contradict each "
       "other here; recording only the convenient one is how the wrong "
       "one gets trusted later")
    ck("🔴🔴 it opens a PULL REQUEST and never merges",
       "PULL REQUEST" in srn and "Do not merge" in srn
       and "Do not push to main" in srn,
       "⛔ THIS IS THE LINE THAT MATTERS. An agent that can write the fix "
       "AND merge it can make a failing check green by deleting it, with "
       "nobody reading the diff. Automatic to the PR; a human merges")
    ck("🔴 the prompt states the MLB policy and the never-weaken rule",
       ("MLB IS FROZEN" in sr or "MLB IS OPEN FOR REPAIR" in sr) and "NEVER WEAKEN A CHECK" in sr,
       "⚠️ CLAUDE.md carries both and the agent reads it — but a prompt "
       "silent about the constraint most likely to be violated is a "
       "prompt inviting the violation")
    ck("⛔ it requires a FAILING TEST before the fix",
       "FAILS on the defect before your fix" in srn,
       "a fix with no failing test is a guess (rule 202)")
    ck("🔴 it does not summon anybody when the system is already repairing",
       "unrepairable" in sr and "not `healthy`" in sr.replace("NOT `healthy`", "not `healthy`"),
       "⛔ the gate is the UNREPAIRABLE count, not the healthy flag. A "
       "finding the watchdog is already rebuilding must never wake an "
       "agent — that is rule 238's lesson applied to a costlier alarm")
    ck("⛔ ...and one PR per problem, never one per run",
       "self-repair/" in sr and "already open" in sr,
       "a workflow that opens a fresh PR every four hours is one whose "
       "PRs get ignored — the same death as a filtered alert")
    # 🔴🔴 THE FIRE DRILL. `[Sam, 2026-09-14: "create a mock tier 3
    #    problem and test it"]` — the agent is the ONLY path in this
    #    architecture that has never executed, and a mode whose first run
    #    is in production is a mode nothing drove (rule 235).
    ck("🔴🔴 a manual DRILL can fire the agent without a real defect",
       "inputs" in srn and "drill" in srn,
       "⛔ everything up to the agent is now proven by driving it. The "
       "agent itself cannot be invoked from outside GitHub, so the only "
       "way to prove that path is a button")
    ck("⛔ ...and ONLY a manual dispatch can set it",
       "github.event.inputs.drill" in srn,
       "🔴 `inputs.drill` does not exist on a `schedule` event, so a "
       "scheduled run can never take the drill branch. A bypass that a "
       "cron could trigger is not a bypass, it is a hole")
    ck("⛔ ...and the drill still may not touch anything real",
       "Change NOTHING else" in srn and "self-repair/drill" in srn,
       "🔴 a drill that edits code proves the path by risking the "
       "product. The task is deliberately trivial because the QUESTION "
       "is whether the path works, not whether the agent is clever")
    ck("⚠️ ...and it still opens a PR rather than pushing",
       srn.count("Do not push to main") >= 2
       and srn.count("Do not merge") >= 2,
       "⛔ the drill must exercise the SAME guards as the real thing, or "
       "it proves a path that does not exist. Got push=%d merge=%d"
       % (srn.count("Do not push to main"), srn.count("Do not merge")))
    ck("✅ ...and it makes the agent prove it read CLAUDE.md",
       "what CLAUDE.md says about MLB" in srn,
       "🔴 the freeze is the constraint most likely to be violated. A "
       "drill that does not check the agent can SEE it proves the "
       "plumbing and nothing about the guardrails")

    ck("⚠️ the triage job cannot write anything",
       "contents: read" in sr,
       "🔴 the job that DECIDES whether to wake an agent must not be able "
       "to change the thing it is deciding about")

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that the watchdog catches "
     "everything. It catches the four shapes that have actually bitten — "
     "a missing card, a refused card, a card that contradicts its own "
     "label, and a stale contract. ➡️ Every NEW failure shape earns a "
     "check here, and that is the maintenance cost of having one at all.")
