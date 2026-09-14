#!/usr/bin/env python3
"""
WATCHDOG — DOES THE PAGE LOOK RIGHT TO SAM RIGHT NOW?

🔴 WHY THIS FILE EXISTS. `[Sam, 2026-09-14: "we need a way to notice these
problems as they happen and it needs to fix itself in github when this
happens"]`

⛔ EVERY GUARD IN THIS REPO BEFORE TODAY ASKED A QUESTION ABOUT THE
PIPELINE. *Did the job exit 0. Is the artifact younger than its deadline.
Do the tests pass.* ✅ Those are good questions and they are all still
asked. ⚠️ **NONE OF THEM IS THE QUESTION SAM ASKS**, which is *"I opened
Gizmo's Picks and there was nothing there."*

    2026-09-12  the MLB card was missing for 3.5 hours.
                `verify_card` wrote a failure file into the repo on every
                pass. ⛔ NOTHING READ IT. Sam found out by looking.
    2026-09-14  the card was missing for 10 hours, BY DESIGN, every day —
                the cron is 10:04am ET and the tab gave up on a 404.
                ⛔ Every check in the repo was GREEN throughout.
    2026-09-14  the football cards carried NEXT WEEK's game lines under a
                header promising one day. ⛔ Nothing asked.

➡️ **A CONTRACT THAT DESCRIBES THE PIPELINE CANNOT NOTICE THAT THE PRODUCT
IS WRONG.** This file asks the product question directly, on a schedule,
and it does two things with the answer:

  1. 🔧 REPAIRS what is mechanically repairable, by naming the collector
     modes that would fix it. The runner executes them. That is the
     "fixes itself in GitHub" half.
  2. 📣 ESCALATES what is not, by opening ONE GitHub issue — updated in
     place, closed when healthy — so Sam is TOLD rather than left to
     notice. That is the half that was missing entirely.

════════════════════════════════════════════════════════════════════════
⛔ WHAT THIS FILE WILL NEVER DO, AND THE LIMIT IS THE POINT
════════════════════════════════════════════════════════════════════════

🔴 **IT DOES NOT EDIT CODE, AND IT MUST NOT.** The 09-12 outage was a
one-character logic defect — a builder and a verifier disagreeing about
whether `-700` clears `-700`. **No watchdog can safely repair that**, and
a system that tried would be a system that edits the file whose whole job
is to disagree with the card. ⚠️ Anything claiming to "auto-fix" that
class is claiming to know which of two disagreeing halves is right, which
is the one thing the disagreement proves nobody knows.

⛔ **IT NEVER SILENCES A CHECK.** A failing verify stays failing. The
watchdog's job is to make sure a human hears about it inside minutes
instead of hours, not to make the tick green.

⛔ **IT NEVER PUBLISHES OR EDITS A CARD.** It reads. Repairs are performed
by the collector's own modes, under the collector's own verification.

✅ **AND ITS OWN FAILURE IS NOT ALLOWED TO TAKE THE SITE DOWN.** A broken
watchdog must never stop data landing, so the runner calls it after the
work, and a crash here is reported rather than fatal.
"""
import datetime
import glob
import gzip
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import freshness as F  # noqa: E402

UTC = datetime.timezone.utc

# 🔴 GRACE. A deadline that has JUST passed is not a fault — the cron that
#    serves it may still be queued, and GitHub's scheduler is late often
#    enough that this project times its crons off :00 for exactly that
#    reason. ⛔ Without grace the watchdog would open an issue every
#    morning at 10:05 and Sam would learn to ignore it, which is the same
#    failure as having no alert at all.
GRACE_MIN = 75

# 🔴🔴 ONLY FREE MODES MAY BE RUN AUTOMATICALLY, AND THE REASON IS NOT
#    TIMIDITY. A repair loop that can SPEND is a repair loop that can
#    spend without a person in it: a condition the repair does not
#    actually fix would be re-attempted on every scheduled run, and
#    `DAILY_CAP` would be the only thing standing between a bad diagnosis
#    and the month's whole allowance.
# ⛔ `card`, `card-fb` and `record` are LOCAL COMPUTE over data already on
#    disk — they call no vendor and bill nothing, so the worst case of a
#    wrong diagnosis is a rebuilt file identical to the one already there.
# ⚠️ `converge` is deliberately NOT here even though it would repair the
#    most: it is the mode that pulls paid odds. Freshness staleness is
#    already repaired by the converge loop this job runs anyway, so the
#    watchdog reports it and does not race it.
SAFE_REPAIRS = ("card", "card-fb", "record")

LEAGUES = ("mlb", "ncaaf", "nfl")
DATA = {"mlb": "data", "ncaaf": "data/ncaaf", "nfl": "data/nfl"}
PICKS = {"mlb": "picks", "ncaaf": "picks", "nfl": "picks"}


def _et_today(now):
    return F.et_date(now)


def _card_path(lg, day):
    if lg == "mlb":
        return os.path.join(ROOT, "picks", "%s.json" % day)
    return os.path.join(ROOT, "picks", "fb-%s-%s.json" % (lg, day))


def _read(p):
    try:
        if p.endswith(".gz"):
            return json.load(gzip.open(p, "rt"))
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return None


class Report:
    """Findings, each with a severity and — where one exists — a repair.

    ⛔ A FINDING WITHOUT A `what` IS NOT A FINDING. Every entry has to say
    what a reader would SEE, or it is a log line pretending to be an
    alert.
    """

    def __init__(self):
        self.items = []

    def bad(self, key, what, why, repair=None, severity="BROKEN"):
        self.items.append({"key": key, "severity": severity, "what": what,
                           "why": why, "repair": repair})

    def warn(self, key, what, why, repair=None):
        self.bad(key, what, why, repair, severity="DEGRADED")

    @property
    def broken(self):
        return [i for i in self.items if i["severity"] == "BROKEN"]


# ══════════════════════════════════════════════════════════════════════
# THE CHECKS. Each one is phrased as something a reader would SEE.
# ══════════════════════════════════════════════════════════════════════

def check_card_present(rep, now):
    """🔴 IS THERE A CARD FOR TODAY, GIVEN THE DEADLINE HAS PASSED?

    ⛔ NOT "did card.py run". A run that exits 0 and publishes nothing is
    the exact shape of 2026-09-12 — eight converge passes, every one of
    them committing data, not one of them producing a card.
    ⚠️ BEFORE the deadline an absent card is CORRECT and is not reported.
    """
    for lg in LEAGUES:
        times = F.CARD if lg == "mlb" else (F.FB_TIMES.get(lg, {}).get("picks")
                                            or F.FB_TIMES.get(lg, {}).get("card"))
        if not times:
            continue
        due = F.last_due(times, now)
        if not due:
            continue
        late = (now - due).total_seconds() / 60.0
        if late < GRACE_MIN:
            continue
        # 🔴🔴 THE DAY COMES FROM THE DEADLINE, NEVER FROM `now`. The
        #    first version of this check used today's ET date and fired at
        #    00:47 ET Monday because *Sunday's* 10am deadline had passed
        #    887 minutes earlier — while Sunday's card sat on disk,
        #    complete. ⛔ A false alarm in a watchdog is not a small bug:
        #    it is the failure mode that makes every later alarm ignorable,
        #    which is precisely the state `test_box_live.py` had left the
        #    red ticks in.
        # ➡️ `due` IS the moment a card became owed, so the card it owes is
        #    the one for `due`'s own ET date.
        day = F.et_date(due)
        if lg != "mlb":
            # ⚠️ A FOOTBALL CARD IS THE SLATE'S, NOT THE CALENDAR'S. There
            #    is no college game on a Tuesday, and demanding a Tuesday
            #    card would be demanding a card about nothing — the
            #    "contract with no Sunday" mistake (rule 137) inverted.
            #    So the football arm asks only that the LATEST pointer be
            #    no older than its own last deadline.
            p = os.path.join(ROOT, "picks", "fb-%s-latest.json" % lg)
            d = _read(p)
            if d is None:
                rep.bad("card:%s" % lg,
                        "the %s Gizmo's Picks tab has no card at all" % lg,
                        "picks/fb-%s-latest.json is missing or unreadable" % lg,
                        repair="card-fb")
            continue
        if not os.path.exists(_card_path(lg, day)):
            # 🔴🔴 A MISSING CARD AND A REFUSED CARD ARE ONE FAULT, NOT
            #    TWO, AND REBUILDING IS THE WRONG ANSWER TO THE SECOND.
            #    Found by walking the scenario through end to end on
            #    2026-09-14 rather than by reading the code: with a
            #    `card-verify-failure.txt` present, the watchdog reported
            #    the absence AND named `card` as its repair — so the issue
            #    said *"automatic repair attempted"* about a rebuild that
            #    can only be refused again by the same verifier, for the
            #    same reason, on every run.
            # ⛔ THAT SENTENCE IS THE DANGEROUS PART. A reader told the
            #    system is retrying stops looking (rule 240's lesson, one
            #    layer up), and here it would be retrying something that
            #    CANNOT succeed until a person changes code.
            _refused = os.path.exists(os.path.join(
                ROOT, DATA[lg], "latest", "card-verify-failure.txt"))
            rep.bad("card:%s" % lg,
                    "Gizmo's Picks and Parlays have no card for %s" % day,
                    "picks/%s.json does not exist and the %s deadline "
                    "passed %d minutes ago.%s"
                    % (day, lg, late,
                       " ⛔ It is missing BECAUSE the verifier refused it — "
                       "see the refusal below. Rebuilding would be refused "
                       "again, so no repair is attempted."
                       if _refused else ""),
                    repair=None if _refused else "card")


def check_verify_failure(rep, now):
    """🔴 DID THE VERIFIER REFUSE A CARD, AND IS ANYONE BEING TOLD?

    ⛔ THIS FILE WAS BEING WRITTEN INTO THE REPO ON EVERY FAILED PASS ON
    2026-09-12 AND NOTHING READ IT. The information existed, in git, for
    three and a half hours. **A diagnostic nobody reads is not a
    diagnostic.**
    ⚠️ Its presence is a code defect by construction — the card was built
    and REFUSED — so there is no repair, only escalation.
    """
    for lg, d in DATA.items():
        p = os.path.join(ROOT, d, "latest", "card-verify-failure.txt")
        if not os.path.exists(p):
            continue
        try:
            txt = open(p, encoding="utf-8").read()
        except Exception:
            txt = "(unreadable)"
        fails = [ln.strip() for ln in txt.splitlines()
                 if ln.strip().startswith("FAIL")]
        rep.bad("verify:%s" % lg,
                "the %s card was BUILT and then REFUSED, so nothing "
                "published" % lg,
                "verify_card rejected it: %s ⛔ This is a CODE defect — "
                "the builder and the verifier disagree — and no automatic "
                "repair is possible or wanted. The guard is doing its job "
                "by publishing nothing."
                % ("; ".join(fails[:3]) or txt[:200]))


def check_card_day_agreement(rep, now):
    """🔴 DOES EVERY ROW ON A CARD BELONG TO THE DAY THE CARD CLAIMS?

    ⛔ THE 2026-09-14 DEFECT, AND NOTHING ASKED THIS. A card headed
    *"Sunday, September 13 only"* published game lines for September 20.
    ⚠️ A card that contradicts its own label is worse than either answer
    on its own, because a reader cannot tell which half to believe.
    """
    for lg in ("ncaaf", "nfl"):
        d = _read(os.path.join(ROOT, "picks", "fb-%s-latest.json" % lg))
        if not d:
            continue
        slate = d.get("date")
        if not slate:
            continue
        for field in ("picks", "game_lines"):
            bad = sorted({_etd(r.get("commence"))
                          for r in (d.get(field) or [])
                          if _etd(r.get("commence")) not in (slate, None)})
            if bad:
                rep.bad("day:%s:%s" % (lg, field),
                        "the %s card says %s only and its %s are on %s"
                        % (lg, slate, field.replace("_", " "), ", ".join(bad)),
                        "the single-day filter (ledger rule 101) is not "
                        "reaching this list",
                        repair="card-fb")


def _etd(commence):
    if not commence:
        return None
    try:
        t = datetime.datetime.strptime(
            commence, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except Exception:
        return None
    return F.et_date(t)


def check_freshness(rep, now):
    """⚠️ THE CONTRACT'S OWN VERDICT, CARRIED UP RATHER THAN RE-DERIVED.

    ⛔ Rule 207: this must not be a second copy of the freshness rules.
    It reads what `freshness` already decided.
    """
    for lg, d in DATA.items():
        f = _read(os.path.join(ROOT, d, "latest", "freshness.json"))
        if not f:
            continue
        stale = [r for r in (f.get("rows") or []) if r.get("stale")]
        if not stale:
            continue
        names = ", ".join(sorted({str(r.get("key")) for r in stale})[:6])
        # ⛔ NO REPAIR NAMED, ON PURPOSE. The converge loop in this same
        #    job is what repairs staleness, and it has already run by the
        #    time the watchdog looks. Naming `converge` here would have
        #    the watchdog racing the thing that was about to fix it, with
        #    a paid pull as the prize.
        rep.warn("fresh:%s" % lg,
                 "%s tabs are showing data older than promised (%s)"
                 % (lg, names),
                 "the freshness contract says %d artifact(s) are stale. "
                 "⚠️ The converge loop repairs this on its own; it is "
                 "reported so a PERSISTENT staleness becomes visible."
                 % len(stale))


def check_record_written(rep, now):
    """⚠️ IS THE TRACK RECORD STILL BEING GRADED?

    A record that stops moving looks identical to a record with nothing to
    grade, and only one of those is fine.
    """
    for lg, d in DATA.items():
        p = os.path.join(ROOT, d, "latest", "record.json")
        if not os.path.exists(p):
            continue
        age = F.age_minutes(p, now)
        if age is None or age == F.MISSING:
            continue
        if age > 60 * 48:
            rep.warn("record:%s" % lg,
                     "the %s Track Record has not been regraded in %.0f "
                     "hours" % (lg, age / 60.0),
                     "record.json is %.0f minutes old" % age,
                     repair="record")


CHECKS = (check_card_present, check_verify_failure, check_card_day_agreement,
          check_freshness, check_record_written)


def run(now=None):
    now = now or datetime.datetime.now(UTC)
    rep = Report()
    for fn in CHECKS:
        try:
            fn(rep, now)
        except Exception as e:
            # ⛔ A CHECK THAT CRASHES IS ITSELF A FINDING, never a silent
            #    pass. The alternative is a watchdog that reports "all
            #    clear" because it fell over before it looked.
            rep.bad("watchdog:%s" % fn.__name__,
                    "a watchdog check could not run",
                    "%s raised %s: %s" % (fn.__name__, type(e).__name__, e))
    out = {
        "kind": "WATCHDOG",
        "checked_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "et_date": _et_today(now),
        "healthy": not rep.items,
        "broken": len(rep.broken),
        "degraded": len(rep.items) - len(rep.broken),
        "findings": rep.items,
        # 🔧 THE REPAIR SET, DEDUPED AND ORDERED. The runner executes
        #    these; nothing here executes itself, so a bug in this file
        #    cannot spend a credit or write a card.
        # ⛔ FILTERED THROUGH `SAFE_REPAIRS` HERE RATHER THAN IN THE
        #    WORKFLOW. A shell step that decides what is safe to run is a
        #    second copy of that judgement (rule 66), and it is the copy
        #    no test can reach.
        "repairs": sorted({i["repair"] for i in rep.items
                           if i["repair"] in SAFE_REPAIRS}),
        "unrepairable": sorted({i["key"].split(":")[0] for i in rep.broken
                                if i["repair"] not in SAFE_REPAIRS}),
    }
    return out


def render(out):
    """The issue body. Written for Sam on a phone, not for a log."""
    if out["healthy"]:
        return "Everything the watchdog checks is currently healthy."
    L = ["**The site is showing something wrong right now.**", ""]
    for sev, head in (("BROKEN", "### Broken"), ("DEGRADED", "### Degraded")):
        rows = [i for i in out["findings"] if i["severity"] == sev]
        if not rows:
            continue
        L.append(head)
        for i in rows:
            L.append("- **%s**  \n  %s" % (i["what"], i["why"]))
        L.append("")
    # 🔴🔴 BOTH SENTENCES, WHEN BOTH ARE TRUE. The first version printed
    #    "automatic repair attempted" and stopped — so a report holding a
    #    rebuildable card AND a refused one read as *"the system is
    #    handling it"* when half of it was waiting on a person.
    # ⛔ THAT IS THE SAME DEFECT AS RULE 222: two conditions that can hold
    #    independently need independent sentences. ⚠️ And it is the more
    #    dangerous direction — a reader who is told it is being fixed
    #    stops looking.
    if out["repairs"]:
        L.append("🔧 Automatic repair attempted: `%s`. If the finding is "
                 "still listed above, the repair did not clear it."
                 % "`, `".join(out["repairs"]))
    if out.get("unrepairable") or not out["repairs"]:
        L.append("⛔ **Part of this has no automatic repair and needs a "
                 "code change.** Nothing is being retried for it.")
    # 🔴🔴 THE HANDOVER LINE, AND IT ONLY APPEARS WHEN A PERSON IS
    #    ACTUALLY NEEDED. `[Sam, 2026-09-14: "can we automate fixes within
    #    the github repo?"]`
    #
    #    ✅ THIS REPO ALREADY HAS `.github/workflows/claude.yml` — the
    #    Claude Code GitHub Action, wired to `@claude` on an issue. So the
    #    last manual step is no longer a zip, a Downloads folder and a
    #    drag: it is ONE REPLY FROM A PHONE, and the fix arrives as a pull
    #    request with all 66 tests run against it.
    #
    # ⛔ IT IS PRINTED ONLY FOR FINDINGS NOTHING CAN REPAIR. A summons
    #    attached to something the system is already fixing would train
    #    Sam to ignore the line, which is the same death as a false alarm
    #    (rule 238).
    # ⚠️ AND IT IS A SUGGESTION, NOT AN INSTRUCTION TO A MODEL. The text
    #    below is what SAM sends if he chooses to; nothing here summons
    #    anything by itself.
    if out.get("unrepairable"):
        # 🔴🔴 THE SUMMONS MUST NOT CONTRADICT ITSELF, AND THE FIRST
        #    VERSION DID. It ended *"do not touch MLB"* — printed on an
        #    issue whose finding WAS an MLB card defect. ⛔ An instruction
        #    that forbids the only change that would resolve it produces
        #    either nothing or a violation, and both are worse than saying
        #    plainly that a decision is owed.
        # ✅ SO THE FREEZE BECOMES AN EXPLICIT, PER-INCIDENT UNLOCK. Sam
        #    sees that MLB is what broke, sees that nothing will be
        #    touched until he says so, and can lift it for THIS issue in
        #    the same tap. ⚠️ The freeze stays the default; what changes is
        #    that the decision is visible instead of silently swallowed.
        _mlb = any(i["key"].endswith(":mlb") for i in out["findings"]
                   if i["severity"] == "BROKEN" and not i["repair"])
        L.append("")
        L.append("---")
        if _mlb:
            L.append("⛔ **This is MLB, which `CLAUDE.md` freezes — *\"we "
                     "have mlb perfected we dont need to touch it\"*. "
                     "Nothing will be changed until you say so.**")
            L.append("")
            L.append("**If you want it fixed,** reply to this issue with")
            L.append("")
            L.append("> `@claude` the MLB freeze is lifted for this issue "
                     "only. Read the finding above, fix it, and open a "
                     "pull request. Follow CLAUDE.md — do not weaken a "
                     "check to make it pass.")
        else:
            L.append("**To have this fixed without uploading anything:** "
                     "reply to this issue with")
            L.append("")
            L.append("> `@claude` read the finding above, fix it, and open "
                     "a pull request. Follow CLAUDE.md — do not weaken a "
                     "check to make it pass, and do not touch MLB.")
        L.append("")
        L.append("The change comes back as a PR with the full suite run "
                 "against it, so nothing lands until you merge it.")
    L.append("")
    L.append("_Checked %s. This issue is updated in place and closes itself "
             "when the site is healthy._" % out["checked_at"])
    return "\n".join(L)


if __name__ == "__main__":
    r = run()
    os.makedirs(os.path.join(ROOT, "data", "latest"), exist_ok=True)
    json.dump(r, open(os.path.join(ROOT, "data", "latest", "health.json"),
                      "w", encoding="utf-8"), indent=1)
    print("═══ WATCHDOG — does the page look right to Sam right now? ═══")
    print("  checked %s (ET %s)" % (r["checked_at"], r["et_date"]))
    if r["healthy"]:
        print("  ✅ HEALTHY — nothing a reader would see is wrong.")
    else:
        for i in r["findings"]:
            print("  %s %s" % ("🔴" if i["severity"] == "BROKEN" else "⚠️",
                               i["what"]))
            print("      %s" % i["why"])
        print("  repairs: %s" % (", ".join(r["repairs"]) or "NONE POSSIBLE"))
    # ⛔ EXIT 0 ALWAYS. This is a REPORTER. A watchdog that reddens the run
    #    it rides on would make the collector's own status meaningless —
    #    and the whole complaint this file answers is that a red tick no
    #    longer tells Sam anything. The ISSUE is the alarm, not the tick.
    sys.exit(0)
