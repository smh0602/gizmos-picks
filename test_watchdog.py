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
import shutil
import sys
import tempfile

from tcheck import ck, note

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
ck("🔴 the watchdog runs nothing itself",
   "subprocess" not in src and "os.system" not in src,
   "⛔ it REPORTS a repair set and the runner executes it. A reporter "
   "that can also act is a reporter whose own bug can spend money")
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
ck("🔴 the MLB freeze is in CLAUDE.md, not only in Sam's project docs",
   "MLB IS CLOSED FOR WORK" in open(CM, encoding="utf-8").read(),
   "⛔ it lived only in the project docs until 2026-09-14, which meant "
   "the Claude Code GitHub Action — an agent working INSIDE this "
   "repository — could not see it at all. A rule the actor cannot read "
   "is not a rule, it is a hope")


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

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that the watchdog catches "
     "everything. It catches the four shapes that have actually bitten — "
     "a missing card, a refused card, a card that contradicts its own "
     "label, and a stale contract. ➡️ Every NEW failure shape earns a "
     "check here, and that is the maintenance cost of having one at all.")
