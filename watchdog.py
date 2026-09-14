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
import re
import sys
import tempfile

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

# 🔴🔴 A REPAIR THAT NEVER WORKS IS A FINDING NOBODY IS COMING TO FIX.
# `[measured 2026-09-14: 35 pointless rebuilds over 9½ hours]`
#
# ⛔ THE HOLE THIS CLOSES IS THE WORST ONE IN THE WHOLE DESIGN. Tier 3
# (`self-repair.yml`) is gated on the `unrepairable` list. A finding that
# NAMES a repair is never unrepairable — so if that repair cannot
# possibly fix it, the loop runs forever, `unrepairable` stays empty, and
# **the agent that exists for exactly this defect class is never woken.**
# ⚠️ The louder the system looks (repairs running every cycle!) the more
# certain it is that nothing is happening.
#
# ✅ So a repair gets a FIXED NUMBER OF TRIES against the same finding.
# After that the repair is withdrawn and the finding escalates. ⛔ Three,
# not one: the workflow re-checks immediately after repairing, and a
# rebuild whose effect lands on the next collector cycle would otherwise
# escalate on a success.
REPAIR_ATTEMPTS_BEFORE_ESCALATION = 3
HEALTH = "data/latest/health.json"

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


def _dated_lists(doc):
    """Every top-level list on a card whose rows carry a kickoff.

    🔴🔴 DISCOVERED, NEVER NAMED, AND THAT IS THE WHOLE POINT. The first
    version of this check swept a hardcoded `("picks", "game_lines")` —
    which is the SAME SHAPE AS THE BUG IT WAS WRITTEN FOR. `game_lines`
    fell through rule 101 because the day filter named its surfaces
    instead of finding them, and a check that also names them inherits
    the defect: it covers exactly the surfaces somebody remembered.
    ⛔ `top_plays` was already uncovered when this was written, on a card
    that carries THREE dated lists. The fourth would have been missed
    too.
    ➡️ SO THE SURFACE SET IS DERIVED FROM THE CARD ITSELF. A new dated
    list is covered the day it ships, by nobody doing anything.
    """
    out = {}
    for k, v in (doc or {}).items():
        if not isinstance(v, list) or not v:
            continue
        if any(isinstance(r, dict) and r.get("commence") for r in v):
            out[k] = v
    return out


def _declared_slate(doc, field):
    """The day a list DECLARES it covers, and whether that was deliberate.

    Returns `(slate, is_next, has_meta)`.

    🔴🔴 THE CARD'S DATE IS NOT EVERY LIST'S DATE, AND ASSUMING IT WAS
    COST 9½ HOURS OF FALSE ALARM. `[measured 2026-09-14 21:19Z]`
    `card_fb.build_game_lines()` deliberately FALLS FORWARD to the next
    day that still has unstarted games, so the list is never empty
    between slates — and it records that in `game_lines_meta`
    (`slate`, `card_slate`, `is_next_slate`). The card says so in words,
    and `index.html` renders the sentence.
    ⛔ This check read `doc["date"]` for every list, so it called a
    labelled, intended, reader-visible design a rule-101 leak — **on a
    Saturday card whose next games are Thursday.** Two halves of my own
    work disagreeing, which is the exact shape of the 09-12 outage.
    ➡️ **Ledger rule 255.**
    """
    meta = (doc or {}).get("%s_meta" % field)
    if isinstance(meta, dict) and meta.get("slate"):
        return meta.get("slate"), bool(meta.get("is_next_slate")), True
    return (doc or {}).get("date"), False, False


def check_card_day_agreement(rep, now):
    """🔴 DOES EVERY ROW BELONG TO THE DAY ITS OWN LIST CLAIMS?

    ⛔ THE 2026-09-14 DEFECT, AND NOTHING ASKED THIS. A card headed
    *"Sunday, September 13 only"* published game lines for September 20.
    ⚠️ A card that contradicts its own label is worse than either answer
    on its own, because a reader cannot tell which half to believe.

    ══════════════════════════════════════════════════════════════════
    ⚠️ THE QUESTION CHANGED 2026-09-14, AND IT IS STRICTLY HARDER.
    ~~"does every row match the CARD's date"~~ — that form fired on a
    correct card for 9½ hours (rule 255). CLAUDE.md permits changing a
    check only when it asks the WRONG QUESTION, and only for a harder
    one. **This asks three things where the old form asked one:**

      1. every row matches the day ITS LIST declares  — the old check,
         still enforced for any list with no meta of its own;
      2. a list that declares a DIFFERENT day than the card must say so
         deliberately (`is_next_slate`) and must look FORWARD, never
         back — ⛔ the old check could not see this at all, and would
         have passed a list silently relabelled to yesterday;
      3. a declared slate must still match its own rows — ⛔ the old
         check passed any list whose rows happened to sit on the card's
         date even while its meta claimed another day.

    ➡️ It fails on everything the old form failed on, plus two shapes
    the old form called clean.
    """
    cards = [("ncaaf", os.path.join(ROOT, "picks", "fb-ncaaf-latest.json"), "card-fb"),
             ("nfl", os.path.join(ROOT, "picks", "fb-nfl-latest.json"), "card-fb")]
    for lg in ("mlb",):
        due = F.last_due(F.CARD, now)
        if due:
            cards.append((lg, os.path.join(ROOT, "picks", "%s.json"
                                           % F.et_date(due)), "card"))
    for lg, path, repair in cards:
        d = _read(path)
        if not d:
            continue
        card_day = d.get("date")
        if not card_day:
            continue
        for field, rows in sorted(_dated_lists(d).items()):
            slate, is_next, has_meta = _declared_slate(d, field)
            if not slate:
                continue
            label = field.replace("_", " ")

            # 2. A LIST THAT MOVES OFF THE CARD'S DAY MUST SAY IT MEANT TO.
            if slate != card_day and not is_next:
                rep.bad("day:%s:%s" % (lg, field),
                        "the %s card says %s and its %s claim %s, with "
                        "nothing saying that was deliberate"
                        % (lg, card_day, label, slate),
                        "a list may follow the NEXT slate, but only when "
                        "it records `is_next_slate` — an unannounced "
                        "relabel is indistinguishable from rule 101 "
                        "leaking again",
                        repair=repair)
                continue
            # ...and forward only. A list cannot 'fall forward' to the past.
            if slate != card_day and slate < card_day:
                rep.bad("day:%s:%s" % (lg, field),
                        "the %s card says %s and its %s fell BACKWARD to %s"
                        % (lg, card_day, label, slate),
                        "the next slate is always later than the card's; "
                        "an earlier one means the slate was computed from "
                        "stale rows",
                        repair=repair)
                continue

            # 1 & 3. THE ROWS MUST MATCH WHATEVER DAY WAS DECLARED.
            bad = sorted({_etd(r.get("commence")) for r in rows
                          if isinstance(r, dict)
                          and _etd(r.get("commence")) not in (slate, None)})
            if bad:
                rep.bad("day:%s:%s" % (lg, field),
                        "the %s %s say %s and carry rows on %s"
                        % (lg, label, slate, ", ".join(bad)),
                        "the single-day filter (ledger rule 101) is not "
                        "reaching this list"
                        if not has_meta else
                        "this list declares its own slate and then "
                        "contradicts it — the declaration is what the "
                        "page shows the reader",
                        repair=repair)


def check_page_renders(rep, now):
    """🔴🔴 DOES THE PAGE RUN AT ALL?

    ⛔ THE WORST FAILURE THIS PRODUCT HAS, AND NOTHING ASKED IT. On
    2026-09-11 a BACKTICK inside a struck comment, inside a JavaScript
    template literal, closed the string early and deleted `setLeague()`.
    **The page rendered blank. Every source check in the repo passed.**
    That is ledger rule 221, and the only thing that caught it was a
    human loading the page.

    ⚠️ `index.html` IS THE WHOLE PRODUCT — one file, no build step. A
    syntax error in it is not a degraded tab, it is every tab on every
    league, instantly, for everyone.

    ⛔ THE CHECK IS A PARSE, NOT A GREP. A grep for a function name
    passes on a file that cannot run; only parsing the script answers the
    question a reader is asking. ✅ `node --check` is a real parser, it
    reaches no network and spends nothing, and the runner already has
    node because the suite runs `test_*.js` with it.
    """
    p = os.path.join(ROOT, "index.html")
    if not os.path.exists(p):
        rep.bad("page:missing", "the site has no index.html at all",
                "index.html is not in the repo")
        return
    try:
        html = open(p, encoding="utf-8").read()
    except Exception as e:
        rep.bad("page:unreadable", "the site's page cannot be read",
                "%s: %s" % (type(e).__name__, e))
        return
    blocks = re.findall(r"<script\b[^>]*>(.*?)</script>", html, re.S)
    if not blocks:
        rep.bad("page:noscript", "the site's page has no script at all",
                "no <script> block in index.html — every tab is inert")
        return
    for i, body in enumerate(blocks):
        if not body.strip():
            continue
        ok, err = _js_parses(body)
        if not ok:
            rep.bad("page:syntax",
                    "THE WHOLE SITE IS BLANK — the page does not parse",
                    "script block %d of %d fails to parse: %s ⛔ One file, "
                    "no build step, so this is every tab on every league "
                    "at once. A backtick inside a comment inside a "
                    "template literal has done exactly this before "
                    "(ledger rule 221)." % (i + 1, len(blocks), err))
            return


def _js_parses(body):
    """`node --check` on one script block. (ok, error-or-None).

    ⚠️ NO NODE IS NOT A PASS. If the parser is unavailable the check has
    not run, and rule 144 says a check that could not run did not pass —
    so it is reported as a finding rather than silently skipped.
    """
    import subprocess
    fd, path = tempfile.mkstemp(suffix=".js")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(body)
        r = subprocess.run(["node", "--check", path],
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return True, None
        return False, (r.stderr or r.stdout).strip().splitlines()[-1][:200]
    except FileNotFoundError:
        return False, ("node is not installed on this runner, so the page "
                       "could NOT be parsed — this is 'not checked', not "
                       "'checked and fine'")
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, e)
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def check_card_readable(rep, now):
    """🔴 A CARD THAT DOES NOT PARSE, AND A CARD THAT LOST ITS PROJECTIONS.

    ⛔ `check_card_present` asked only whether the FILE EXISTS. A card
    truncated by a half-finished write exists and blanks the tab exactly
    as a missing one does — and the page's own fallback walks PAST it to
    an older card, so the reader sees stale rows and no error at all.

    🔴 THE PROJECTION HALF IS SAM'S OWN REPORT, 2026-09-14: *"did not
    deliver any picks for the mlb slate as well as didnt provide
    projections."* A card carrying rows but no projections renders a
    board with the PROJ chip missing from every row — ⚠️ which looks like
    a styling problem rather than a data one, and is the reason it went
    unreported for as long as it did.
    """
    due = F.last_due(F.CARD, now)
    if not due:
        return
    day = F.et_date(due)
    for lg, path, repair in (
            ("mlb", os.path.join(ROOT, "picks", "%s.json" % day), "card"),
            ("ncaaf", os.path.join(ROOT, "picks", "fb-ncaaf-latest.json"), "card-fb"),
            ("nfl", os.path.join(ROOT, "picks", "fb-nfl-latest.json"), "card-fb")):
        if not os.path.exists(path):
            continue            # absence is `check_card_present`'s question
        if _read(path) is None:
            rep.bad("cardfile:%s" % lg,
                    "the %s card file is corrupt and the tab cannot load it"
                    % lg,
                    "%s exists but is not readable JSON. ⚠️ The page's "
                    "fallback walks PAST it to an older card, so a reader "
                    "sees stale rows and no error."
                    % os.path.relpath(path, ROOT),
                    repair=repair)
            continue
        d = _read(path)
        # ⚠️ ONLY WHEN THERE ARE ROWS TO PROJECT. An empty board is a
        #    legitimate state (rule 86) and must not raise an alarm.
        if lg == "mlb" and (d.get("picks") or []) and not (d.get("projections") or {}):
            rep.bad("proj:%s" % lg,
                    "the %s board has rows but NO projections — every "
                    "PROJ number is missing from Player Props" % lg,
                    "the card carries %d pick(s) and an empty "
                    "`projections` map. `apply_projections()` is the only "
                    "writer of that field." % len(d["picks"]),
                    repair=repair)


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


def _published(lg):
    """How many cards this league has published — the evidence that a
    Track Record is OWED.

    ⛔ COUNTED FROM THE REPO, NEVER ASSUMED. A league with nothing
    published has no record to grade and a missing `record.json` is
    correct; a league with 24 published cards and no record file is a dead
    tab. **The difference is a fact about the repo, so it is read from the
    repo.**
    """
    # 🔴 DATED CARDS ONLY. `picks/fb-<lg>-latest.json` is the CURRENT card
    #    pointer, not published history — and my first version globbed
    #    `fb-<lg>-*.json`, which matched it. ⛔ THAT FALSE-ALARMED ON THREE
    #    EXISTING CHECKS INSIDE A MINUTE: every fixture writing a `-latest`
    #    card suddenly owed a Track Record, including the clean-tree test
    #    whose entire job is to prove the watchdog can be quiet.
    # ⚠️ Caught only because the suite drove it. **Fifth check of mine this
    #    week to fire on correct state** (rules 257, 260, 262) — and the
    #    first one a test caught before Sam did.
    pat = ("picks/20*.json" if lg == "mlb" else "picks/fb-%s-20*.json" % lg)
    return len(glob.glob(os.path.join(ROOT, pat)))


def check_record_written(rep, now):
    """⚠️ IS THE TRACK RECORD STILL BEING GRADED?

    A record that stops moving looks identical to a record with nothing to
    grade, and only one of those is fine.
    """
    for lg, d in DATA.items():
        p = os.path.join(ROOT, d, "latest", "record.json")
        if not os.path.exists(p):
            # 🔴🔴 A MISSING FILE WAS SILENTLY SKIPPED, AND THAT IS THE
            #    MOST COMPLETE FORM OF THE FAILURE THIS CHECK EXISTS FOR.
            # `[found 2026-09-14 by DELETING it and watching nothing
            #   happen — the watchdog reported healthy: true]`
            # ⛔ "The Track Record stopped being graded" was checked by
            #    AGE only, so a record.json that vanished entirely — the
            #    page's whole Track Record tab — produced no finding at
            #    all. **An absence read as "nothing to say" is this
            #    project's oldest recurring error.**
            # ⚠️ THE `continue` WAS NOT WRONG, IT WAS UNCONDITIONAL. A
            #    league with nothing published yet has no record to grade
            #    and must stay silent, which is why it was there. ✅ So the
            #    question is now "is it missing DESPITE published cards?"
            #    — measured from the repo, not assumed.
            if _published(lg):
                rep.bad("record:%s" % lg,
                        "the %s Track Record file is gone" % lg,
                        "record.json does not exist, and %d published "
                        "card(s) exist to grade — the page has nothing to "
                        "show on that tab" % _published(lg),
                        repair="record")
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


def check_board_not_empty(rep, now):
    """⚠️ THE BUILDER HAD CANDIDATES AND CARDED NONE OF THEM.

    🔴 A BOARD WITH NO ROWS IS NOT AUTOMATICALLY A FAULT — an empty
    artifact from a correct build is a legitimate state and the page says
    so (ledger rule 86). A thin Tuesday is not breakage, and alarming on
    one is how the channel gets muted.
    ⛔ SO THE QUESTION IS NARROWER AND IT IS NOT "IS IT EMPTY": it is
    **did the builder have a pool and reject all of it.** `n_priced` on a
    football card, and `coverage_detail.skipped` on MLB, are the
    builder's own count of what it looked at — so a zero board beneath a
    non-zero pool is the card saying it threw everything away.
    ⚠️ DEGRADED, NOT BROKEN, and deliberately. It is one number's
    distance from a legitimately quiet day, and the honest report is
    "this looks wrong", not "this is wrong".
    """
    due = F.last_due(F.CARD, now)
    for lg, path in (("mlb", os.path.join(ROOT, "picks", "%s.json"
                                          % F.et_date(due)) if due else None),
                     ("ncaaf", os.path.join(ROOT, "picks", "fb-ncaaf-latest.json")),
                     ("nfl", os.path.join(ROOT, "picks", "fb-nfl-latest.json"))):
        if not path:
            continue
        d = _read(path)
        if not d or (d.get("picks") or []):
            continue
        # the builder's own count of what it had to choose from
        pool = d.get("n_priced")
        if pool is None:
            cd = d.get("coverage_detail") or {}
            sk = cd.get("skipped")
            pool = sum(sk.values()) if isinstance(sk, dict) else None
        if not pool:
            continue            # genuinely nothing to card — correct, quiet
        rep.warn("empty:%s" % lg,
                 "the %s board is EMPTY on a day the builder had %d row(s) "
                 "to choose from" % (lg, pool),
                 "the card carries zero picks beneath a non-zero pool, so "
                 "every candidate was rejected. ⚠️ That can be legitimate "
                 "on a bad slate — it is reported, not called broken — but "
                 "a reader opening the tab sees nothing at all.")


def check_record_sane(rep, now):
    """⚠️ A PERCENTAGE THAT CANNOT BE A PERCENTAGE.

    ⛔ DELIBERATELY SHALLOW, AND THE SHALLOWNESS IS THE DESIGN.
    `verify_record.py` already re-grades every published pick a second
    way and reconciles the whole file — that is the real check, and
    duplicating any part of it here would be a SECOND COPY of the
    specification, which is ledger rule 207 and the precise defect that
    took the card down on 09-12.
    ✅ What this asks instead is a question `verify_record` cannot be
    asked to answer about itself: **is the file the page is reading
    internally impossible**, on a run where the record job did not
    happen to execute. Wins above plays, or a rate outside 0-100, is a
    corrupt file whatever produced it.
    """
    for lg, d_ in DATA.items():
        r = _read(os.path.join(ROOT, d_, "latest", "record.json"))
        if not r:
            continue
        bad = []
        ov = r.get("overall") or {}
        w_, n_, pct = ov.get("w"), ov.get("n"), ov.get("pct")
        if isinstance(w_, int) and isinstance(n_, int):
            if n_ < 0 or w_ < 0:
                bad.append("negative counts (w=%s n=%s)" % (w_, n_))
            if n_ and w_ > n_:
                bad.append("more wins than graded rows (%d of %d)" % (w_, n_))
        if isinstance(pct, (int, float)) and not (0.0 <= pct <= 100.0):
            bad.append("an overall rate of %.1f%%" % pct)
        for bucket in (r.get("calibration") or []):
            p = bucket.get("pct")
            if isinstance(p, (int, float)) and not (0.0 <= p <= 100.0):
                bad.append("bucket %s at %.1f%%" % (bucket.get("bucket"), p))
        if bad:
            rep.bad("record:%s:sane" % lg,
                    "the %s Track Record shows a number that cannot be "
                    "true" % lg,
                    "; ".join(bad) + ". ⛔ `record.json` is what the tab "
                    "renders, so this is on the page now.")


# 🔴🔴 ONE THING THIS FILE DELIBERATELY DOES NOT CHECK, AND THE REASON
#    MATTERS MORE THAN THE CHECK WOULD.
#
#    A parlay carrying a leg below the -700 price floor is a real way the
#    page can be wrong, and the coverage matrix records it as a MISS.
#    ⛔ IT IS NOT ADDED ON PURPOSE. `verify_card.py` already owns that
#    rule and refuses to publish a card that breaks it, and writing the
#    floor into this file too would be a THIRD copy of Sam's number.
#    ⚠️ The second copy is what failed on 2026-09-12: the builder said
#    `>=` and the verifier said `>`, they disagreed for two days, and the
#    card stopped publishing. **Adding a third reader of that constant to
#    catch the failure caused by having two is the wrong direction**, and
#    a watchdog that quietly re-implements the verifier is a watchdog
#    that can disagree with it.
#    ➡️ THE COVER FOR THAT CLASS IS `check_verify_failure`: if the floor
#    is ever broken, the verifier refuses the card and this file reports
#    the refusal within one collector run.

CHECKS = (check_page_renders, check_card_present, check_card_readable,
          check_verify_failure, check_card_day_agreement,
          check_board_not_empty, check_record_sane,
          check_freshness, check_record_written)


def _previous():
    """The last health report this repo committed, or `{}`.

    ⛔ READ, NEVER WRITTEN, HERE. `watchdog.py` returns a dict; the
    workflow writes the file. Keeping the write out of this module is
    what makes rule 243 hold — a bug in this file cannot spend a credit
    or overwrite a record.
    """
    return _read(os.path.join(ROOT, HEALTH)) or {}


def _escalate_stuck_repairs(items, prev):
    """⛔ WITHDRAW A REPAIR THAT HAS ALREADY FAILED ITS ALLOWANCE.

    A finding counts an attempt only when the PREVIOUS report both named
    it and actually listed its repair for execution. ⚠️ That distinction
    matters: a finding whose repair was filtered out by `SAFE_REPAIRS`
    was never tried, and charging it an attempt would escalate something
    nothing has yet attempted to fix.
    """
    was = {i.get("key"): i for i in (prev.get("findings") or [])}
    ran = set(prev.get("repairs") or [])
    for it in items:
        if not it.get("repair"):
            continue
        before = was.get(it["key"])
        # 🔴🔴 A WITHDRAWAL IS PERMANENT WHILE THE FINDING PERSISTS, AND
        #    THE FIRST VERSION OSCILLATED. `[found 2026-09-14 by driving
        #    four cycles instead of three]`
        # ⛔ Once the repair is withdrawn the report lists no repair, so on
        #    the NEXT run `tried` was False, the counter reset to 1 and the
        #    repair came back. **Escalate, un-escalate, escalate — a
        #    four-cycle loop in which `unrepairable` is non-empty only one
        #    run in four**, so Tier 3 sees the finding a quarter of the
        #    time and the useless repair keeps running forever anyway,
        #    which is the entire waste this was written to stop.
        # ⚠️ THREE CYCLES LOOKED CORRECT. The defect only appears on the
        #    fourth, which is why it survived being tested at all.
        if before and before.get("repair_withdrawn"):
            it["repair_attempts"] = before.get("repair_attempts") or \
                REPAIR_ATTEMPTS_BEFORE_ESCALATION
            it["repair_withdrawn"] = before["repair_withdrawn"]
            it["repair"] = None
            it["why"] = ("%s ⛔ `%s` was withdrawn after %d failed "
                         "attempt(s) and stays withdrawn while this "
                         "finding persists."
                         % (it["why"], it["repair_withdrawn"],
                            it["repair_attempts"]))
            continue
        tried = bool(before) and before.get("repair") in ran
        it["repair_attempts"] = (
            (before.get("repair_attempts") or 0) + 1 if tried else 1)
        if it["repair_attempts"] >= REPAIR_ATTEMPTS_BEFORE_ESCALATION:
            it["repair_withdrawn"] = it["repair"]
            it["repair"] = None
            it["why"] = (
                "%s ⛔ `%s` has now been run %d times against this exact "
                "finding without clearing it, so it is withdrawn: a "
                "repair that cannot fix something must not keep the "
                "finding out of the escalation list."
                % (it["why"], it["repair_withdrawn"], it["repair_attempts"]))
    return items


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
    _escalate_stuck_repairs(rep.items, _previous())
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
