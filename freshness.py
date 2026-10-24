"""THE FRESHNESS CONTRACT — what must be how current, and how age is measured.

🔴 WHY THIS FILE EXISTS, AND THE BUG THAT CAUSED IT (2026-08-28).

Until today the collector's design was CRON-OWNS-ARTIFACT: one scheduled
run produced one file. That design has a fatal property -- GitHub delivers
`schedule` events on a BEST-EFFORT basis and drops most of them under load.
`[measured 2026-08-28 from the repo's own commit log]` the hourly gamelines
cron should land 21 runs a day; it landed **7 on 8/25, 4 on 8/26, 1 on 8/27
and 2 on 8/28**. Under cron-owns-artifact a dropped run is not a delay, it
is a PERMANENTLY MISSING ARTIFACT, and the site silently serves yesterday.

⛔ AND THE WORKAROUND THAT WAS ALREADY HERE MADE IT WORSE, NOT BETTER.
`props_is_fresh()` decided "did a pull already land?" from
`os.path.getmtime`. **EVERY CI RUN IS A FRESH `git checkout`, WHICH SETS
EVERY FILE'S MTIME TO THE CHECKOUT TIME.** So on the second props run of
any day the guard measured an age of ~0 minutes against a 45-minute window,
declared the 02:20Z file fresh, and stood down "NOTHING SPENT" -- forever.
`[measured 2026-08-28]` today's `props-pitcher/0220.json.gz` was written at
02:20Z and carried an mtime of 16:47Z in a clean clone.

➡️ **THE PROPS WERE FROZEN AT THE FIRST PULL OF EACH DAY BY CONSTRUCTION.**
Not flaky, not load -- deterministic. Half the board had no props because
at 10:20 PM ET the night before, half the books had not posted a line.

## The two rules this file enforces

**1. AGE COMES FROM CONTENT, NEVER FROM THE FILESYSTEM.**
   An artifact's age is read from the timestamp INSIDE it (`pulled_at` /
   `built_at` / `generated_at`), or from the `HHMM` in a snapshot's own
   filename. ⛔ `os.path.getmtime` IS BANNED FOR FRESHNESS ANYWHERE IN THIS
   PROJECT. In CI it does not measure what you think it measures.

**2. EVERY RUN CONVERGES THE WHOLE SITE, NOT ITS OWN ARTIFACT.**
   Each artifact declares how stale it may be. Any run -- scheduled, push
   or manual, whatever mode it was asked for -- first reconciles everything
   against that contract and rebuilds exactly what is late. A dropped cron
   then costs LATENCY, NEVER DATA, and any single run that lands restores
   the entire site.

⚠️ Consequence worth stating: it is now correct and expected for a
`gamelines` cron to also refresh the card. That is the point. Modes are no
longer owners; they are hints.
"""

import glob
import json
import gzip
import os
import re
import datetime
import ast

UTC = datetime.timezone.utc

# The timestamp fields an artifact may carry, in priority order.
STAMP_FIELDS = ("pulled_at", "built_at", "generated_at", "written_at")

_SNAP = re.compile(r"/(\d{4}-\d{2}-\d{2})/[^/]+/(\d{4})\.json(\.gz)?$")

# A sentinel age meaning "no usable timestamp -- treat as infinitely old".
# ⛔ It must be larger than any max_age in the contract, and it must never
# be silently replaced by an mtime.
MISSING = 10 ** 9
_DOW = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _load(path):
    try:
        op = gzip.open if path.endswith(".gz") else open
        with op(path, "rt") as fh:
            return json.load(fh)
    except Exception:
        return None


def _parse(ts):
    if not isinstance(ts, str):
        return None
    t = ts.strip().replace("Z", "+00:00")
    try:
        d = datetime.datetime.fromisoformat(t)
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=UTC)


def stamp_of(path):
    """The moment this artifact was produced, read from its CONTENT.

    🔴 Never from the filesystem. Returns None when the file carries no
    usable timestamp -- callers must treat that as 'must rebuild', never as
    'assume fresh'.
    """
    if not os.path.exists(path):
        return None

    # A day-dir snapshot names its own minute: data/<date>/<kind>/HHMM.json
    # This is checked FIRST because it cannot be wrong -- the writer chose
    # the name from the clock, and a checkout cannot alter it.
    m = _SNAP.search("/" + path.replace(os.sep, "/").lstrip("/"))
    if m:
        day, hhmm = m.group(1), m.group(2)
        try:
            return datetime.datetime.strptime(
                f"{day}{hhmm}", "%Y-%m-%d%H%M").replace(tzinfo=UTC)
        except ValueError:
            pass

    doc = _load(path)
    if isinstance(doc, dict):
        for f in STAMP_FIELDS:
            got = _parse(doc.get(f))
            if got:
                return got
    return None


def age_minutes(path, now=None):
    """Minutes since this artifact was produced. MISSING when unknowable."""
    got = stamp_of(path)
    if got is None:
        return MISSING
    now = now or datetime.datetime.now(UTC)
    return max(0.0, (now - got).total_seconds() / 60.0)


def newest_age_minutes(directory, now=None):
    """Age of the FRESHEST snapshot across a day directory AND the one
    before it.

    🔴 THE DAY-ROLLOVER BUG THIS FIXES, found by the fault-injection suite
    on 2026-08-28 before it ever ran. Props snapshots live in
    `data/<UTC date>/props-*/`. Probing only TODAY's directory means that
    for the first hours after 00:00Z -- which is **8:00pm ET, mid-slate**
    -- the directory is empty, every props artifact reads as MISSING, and
    the converge pass buys a fresh pull it does not need. ⛔ That is a
    paid pull, every single night, caused by a calendar boundary.

    ✅ So the probe spans the previous UTC day too. The deadline logic
    still decides whether a rebuild is owed; this only stops the evidence
    from vanishing at midnight.
    """
    if not directory:
        return MISSING
    now = now or datetime.datetime.now(UTC)
    dirs = [directory]
    # data/<YYYY-MM-DD>/<kind>  ->  swap in yesterday's date
    parts = directory.replace(os.sep, "/").split("/")
    for i, seg in enumerate(parts):
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", seg):
            try:
                d = datetime.datetime.strptime(seg, "%Y-%m-%d").date()
            except ValueError:
                break
            y = list(parts)
            y[i] = (d - datetime.timedelta(days=1)).isoformat()
            dirs.append("/".join(y))
            break
    best = MISSING
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if not name.endswith((".json", ".json.gz")):
                continue
            best = min(best, age_minutes(os.path.join(d, name), now))
    return best


# ======================================================================
# THE CONTRACT — Sam's schedule, expressed as DEADLINES not triggers
# ======================================================================
# 🔴 THE DISTINCTION THAT MAKES THIS WORK, AND IT IS THE WHOLE DESIGN.
# Sam asked for fixed daily times: odds at 7am and 4pm, grading at 6am,
# the card at 10am. ⛔ THOSE CANNOT BE CRON TRIGGERS. GitHub delivers
# `schedule` on a best-effort basis and dropped 19 of 21 daily runs on
# 2026-08-27 -- a cron AT 7am is a cron that sometimes does not happen,
# which is exactly the failure this replaces.
#
# ✅ So each artifact declares WHEN IT IS DUE, and the converge pass --
# running continuously in the background -- builds anything whose due
# time has passed and which has not been rebuilt since. The times below
# are Sam's, exactly. What changes is the mechanism that meets them:
#
#   a cron AT 7am     -> happens at 7am, or NEVER
#   DUE at 7am        -> happens at 7am, or as soon after as a run lands
#
# ⚠️ SAID PLAINLY, BECAUSE HE ASKED FOR "WITHOUT FAILURE": nobody can
# promise GitHub fires at 07:00:00. What this DOES promise is that the
# 7am build is the first thing any later run does, that it cannot be
# skipped or lost, and that if it is late the page says so on its face.
# ⛔ A guarantee of punctuality would be a lie; a guarantee of delivery
# is not.
#
# All times below are ET (America/New_York, UTC-4 Mar-Nov).

def et_date(now=None):
    """Today's ET slate date. ⚠️ Fixed -4; ET is UTC-4 from Mar to Nov."""
    now = now or datetime.datetime.now(UTC)
    return (now - datetime.timedelta(hours=4)).strftime("%Y-%m-%d")


ET_OFFSET = datetime.timedelta(hours=4)


def slate_date(now=None):
    """The ET date of the slate `collect_results` last wrote.

    🔴 NOT `et_date`. `collect_results` writes to `data/<et_slate_date>/`,
    stepping back **ten** hours -- four for ET, six more so a 1am ET
    finish still belongs to the previous night's slate. The contract was
    probing `et_date`, four hours back, so between **04:00Z and 10:00Z**
    the two disagreed and the contract looked in a directory the writer
    had never used.
    ⛔ MEASURED CONSEQUENCE: `results` read as MISSING for six hours every
    night. Every converge pass in that window re-ran it and the freshness
    gate reported the site out of contract. It is a free mode, so it cost
    no credits -- it cost a NIGHTLY FALSE ALARM, which is worse, because
    an alarm that fires every night gets ignored.
    ⚠️ Found 2026-08-29 by `test_freshness.py`, but ONLY because the clock
    had crossed midnight UTC. **The same suite passed all day.** A date
    bug is invisible until you are standing inside its window.
    """
    now = now or datetime.datetime.now(UTC)
    return (now - datetime.timedelta(hours=10)).strftime("%Y-%m-%d")


def due_date(times_et, now=None):
    """The ET date of the SLATE WHOSE DEADLINE CURRENTLY GOVERNS.

    🔴 THE SECOND HALF OF THE `slate_date` BUG, AND IT SURVIVED THE FIRST
    FIX. `results` was corrected on 2026-08-29; the `card` row was not,
    and it had the same shape: its FILENAME came from the wall clock
    (`et_date`) while its DEADLINE came from the schedule (`last_due`).
    ⛔ MEASURED 2026-08-30 06:58Z: `et_date` had already rolled to 08-30
    while the governing deadline was still 08-29's 10:00 ET. The contract
    demanded `picks/2026-08-30.json` -- a card NOT DUE FOR ANOTHER SEVEN
    HOURS -- and reported it MISSING. `picks/2026-08-29.json` existed and
    was correct.
    ⛔ CONSEQUENCE: the site reported itself out of contract and the run
    went RED EVERY NIGHT between midnight and 10am ET. An alarm that
    fires every night is an alarm that gets ignored, which is exactly how
    the original staleness survived a whole day.
    ✅ THE RULE, STATED SO IT IS NOT RE-DERIVED A THIRD TIME:
    **AN ARTIFACT WHOSE PATH CARRIES A DATE MUST TAKE THAT DATE FROM ITS
    OWN DEADLINE, NEVER FROM THE WALL CLOCK.**
    """
    d = last_due(times_et, now)
    if d is None:
        return et_date(now)
    return (d - ET_OFFSET).strftime("%Y-%m-%d")


def no_games_day(day, data="data"):
    """True only when every stored MLB schedule reading for ET `day` says
    the league had NO games. ⛔ Fails closed: no reading, an unreadable
    one, a reading without `totalGames`, one whose game list does not add
    up to its `totalGames`, or any reading listing a game the league has
    not since DROPPED (`_still_listed`) means the day's card and results
    are still owed.

    `[2026-09-29]` ONE COPY: moved here from watchdog.py (#200), which
    imports it. The contract's MLB `card` and `results` rows are not due on
    such a day -- collect #1983 went red on 2026-09-28 (0 MLB games) for a
    card "never built" and a results directory nobody could write.
    ⚠️ A reading filed under the NEXT day's directory still counts: the
    schedule mode stores by UTC date, and an evening pull lands there.
    `[2026-10-23]` ~~any reading listing a game~~: 10-20's first 12 readings
    listed ALCS Game 7 (if necessary) until Game 6 ended the series, and the
    day owed a card and results through 10-22 (test_dropped_game.py).
    """
    nxt = (datetime.date.fromisoformat(day)
           + datetime.timedelta(days=1)).isoformat()
    reads = []
    for d in (day, nxt):
        for p in sorted(glob.glob(os.path.join(data, d, "schedule", "*.json.gz"))):
            try:
                s = json.load(gzip.open(p, "rt"))
            except Exception:
                return False          # unreadable: fail closed
            if not isinstance(s, dict) or s.get("date") != day:
                continue
            sc = s.get("schedule")
            if not isinstance(sc, dict) or "totalGames" not in sc:
                return False          # no totalGames: fail closed
            if "dates" in sc and _games(sc) is None:
                return False          # a game list that does not add up: fail closed
            reads.append((s.get("pulled_at"), sc))
    seen = _still_listed(reads)
    return bool(seen) and all(n == 0 for n in seen)


# `[2026-10-23]` How many readings pulled AFTER the last one listing an
#    if-necessary game must leave it out before it counts as dropped: one
#    odd reading never drops a game. 10-20 had 74.
DROPPED_AFTER = 2


def _games(sc):
    """A schedule body's games, or None when `dates` does not hold exactly
    `totalGames` games, each with a gamePk. A count-only body (no `dates`)
    names none: [] for 0 games, None otherwise."""
    dates = sc.get("dates", [])
    if not isinstance(dates, list) or not all(isinstance(d, dict) for d in dates):
        return None
    games = [g for d in dates for g in (d.get("games") or [])]
    if not all(isinstance(g, dict) and "gamePk" in g for g in games):
        return None
    return games if len(games) == sc.get("totalGames") else None


def _still_listed(reads):
    """Per reading [(pulled_at, schedule body)], how many games it lists that
    the league has not since DROPPED. A game is dropped only when every
    reading that lists it flags it `ifNecessary` "Y" (MLB's "If Necessary
    Game") and DROPPED_AFTER readings pulled after the last one that lists
    it leave it out: the series ended without it.
    ⛔ Fails closed (each reading keeps its `totalGames`): a reading with no
    pulled_at time, or one whose count names no games, drops nothing."""
    times = [_parse(ts) for ts, _ in reads]
    lists = [_games(sc) for _, sc in reads]
    if None in times or None in lists:
        return [sc["totalGames"] for _, sc in reads]
    last, flagged = {}, {}
    for t, games in zip(times, lists):
        for g in games:
            pk = g["gamePk"]
            last[pk] = max(last.get(pk, t), t)
            flagged[pk] = flagged.get(pk, True) and g.get("ifNecessary") == "Y"
    gone = {pk for pk, t in last.items()
            if flagged[pk] and sum(u > t for u in times) >= DROPPED_AFTER}
    return [sum(g["gamePk"] not in gone for g in games) for games in lists]


# ⛔ A SECOND COPY OF `collect.VOID_STATES`, ON PURPOSE (verify_record keeps
#    one too): importing collect runs its league and argv checks, which can
#    sys.exit in another process. test_slate_graded.py fails if they differ.
VOID_STATES = frozenset({"Postponed", "Cancelled"})


def results_settled(day, data="data"):
    """True only when ET `day`'s stored results would be GRADED: the file
    reads, lists games, and each is Final or VOID_STATES (the grader's
    `collect.slate_settled`). ⛔ Fails closed: missing or unreadable is not."""
    try:
        games = json.load(gzip.open(os.path.join(data, day, "results", "final.json.gz"),
                                    "rt")).get("games")
    except Exception:
        return False
    return bool(games) and all(isinstance(g, dict) and (g.get("state") == "Final"
                                                        or g.get("state") in VOID_STATES)
                               for g in games)


def last_due(times_et, now=None):
    """The most recent scheduled build time that has already passed.

    An artifact is stale when it was last written BEFORE this moment.
    Handles the wrap: at 3am ET the governing deadline is yesterday's
    last one, not today's first.

    🔴 A DEADLINE MAY NAME THE DAYS IT APPLIES ON, ADDED 2026-09-04 FOR
    FOOTBALL. `(hh, mm)` is unchanged and means EVERY DAY; `(hh, mm,
    {weekdays})` restricts it, using Python's Monday=0.
    ⛔ WHY IT WAS NEEDED: football is weekly. College props run Tue-Sat
    and the trends table rebuilds on one morning a week. Without days, a
    weekly artifact reads as **stale six days out of seven** and the
    staleness banner becomes noise that everyone learns to ignore --
    which is the exact failure this whole file exists to prevent.
    ⚠️ MLB's four constants carry no day set and are therefore untouched;
    `test_freshness.py` pins that.
    ⛔ LOOK BACK FAR ENOUGH TO FIND ONE. A weekly deadline can be six days
    behind, so the 2-day window that served daily MLB artifacts would
    return None and mark a perfectly fresh weekly file as never-due.
    """
    now = now or datetime.datetime.now(UTC)
    et = now - ET_OFFSET
    best = None
    for back in range(0, 8):
        d = (et - datetime.timedelta(days=back)).date()
        for t in times_et:
            hh, mm = t[0], t[1]
            days = t[2] if len(t) > 2 else None
            if days is not None and d.weekday() not in days:
                continue
            cand = datetime.datetime.combine(
                d, datetime.time(hh, mm), tzinfo=UTC)
            if cand <= et and (best is None or cand > best):
                best = cand
    return None if best is None else best + ET_OFFSET


def next_due(times_et, now=None):
    """The next scheduled build time strictly after `now` — `last_due`'s
    mirror, same day rules and the same fixed ET offset. None if none in a
    week. `[2026-09-24]` The alt-line pull buys each game at the LAST props
    deadline before its kickoff, so it asks whether another one comes first."""
    now = now or datetime.datetime.now(UTC)
    et = now - ET_OFFSET
    best = None
    for fwd in range(0, 8):
        d = (et + datetime.timedelta(days=fwd)).date()
        for t in times_et:
            days = t[2] if len(t) > 2 else None
            if days is not None and d.weekday() not in days:
                continue
            cand = datetime.datetime.combine(d, datetime.time(t[0], t[1]), tzinfo=UTC)
            if cand > et and (best is None or cand < best):
                best = cand
    return None if best is None else best + ET_OFFSET


# ── Sam's schedule, 2026-08-28 ────────────────────────────────────────
#   Scores & Matchups  live (the browser polls statsapi every 45s, free)
#   Odds               7:00am and 4:00pm
#   Trends             6:00am
#   Gizmo's Picks      10:00am
#   Parlays            same as Picks (same file)
#   Player Props       same as Odds
#   Track Record       same as Trends -- grades last night's slate
#   News               unchanged (3x daily)
GRADING  = [(6, 0)]                    # Trends + Track Record
ODDS     = [(7, 0), (16, 0)]           # Odds + Player Props
CARD     = [(10, 0)]                   # Gizmo's Picks + Parlays
NEWS     = [(9, 5), (15, 5), (21, 5)]  # unchanged


# ══════════════════════════════════════════════════════════════════════
# 🔴 FOOTBALL'S CONTRACT — ADDED 2026-09-04. UNTIL NOW THERE WAS NONE.
# `[measured 2026-09-04]` `survey()` returned **13 rows, every one MLB.**
# ⛔ So a football artifact could rot indefinitely and NOTHING noticed,
# nothing said so, and no run repaired it. **Three separate bugs got
# through that hole in four days** -- `cfb-teams` (a logo directory that
# existed only because one ad-hoc run wrote it), football `news` (feeds
# adopted, never collected) and `card-fb` (a board that only rebuilt
# inside a PAID pull, so the live college card was four days stale and
# still showed a +5000 top row).
# ✅ EVERY ONE OF THEM WOULD HAVE BEEN A LATE ROW HERE.
#
# ⚠️ THESE DEADLINES ARE SAM'S OWN SCHEDULE, 2026-09-04, AND THEY MUST
# TRACK THE CRONS. ⛔ A contract that disagrees with the workflow reports
# lateness that no run can clear, and a banner nobody can fix is a banner
# everybody ignores.
#
# 🔴 ONE ARTIFACT, ONE ROW (rule 66). Gizmo's Picks, Parlays and Track
# Record are all THE SAME FILE -- `picks/fb-<lg>-latest.json`. They get a
# single row whose deadlines are the UNION of the three, not three rows
# that could disagree about one file.
FB_TIMES = {
    "ncaaf": {
        "odds":   [(7, 0), (15, 0)],                     # 7am, 3pm daily
        # 🔴 EVERY DAY, NOT Tue-Sat. `[Sam, 2026-09-06: "gizmos picks/
        # player props/parlays tabs are all not updated, still has lines
        # from yesterdays games, it is already 1:30 with games starting in
        # a few hours. this needs to be an automated tab that updates
        # everyday consistently."]`
        # ⛔ THE OLD SET HAD NO SUNDAY AND NO MONDAY, so on a Sunday with
        # a real slate the contract had NOTHING TO SAY: the last deadline
        # was Saturday 3pm, the Saturday pull satisfied it, and `plan()`
        # returned an EMPTY LIST while the board went 22 hours old and the
        # card still showed Saturday's games. **Nothing failed. Every
        # verifier was green. The product was stale.**
        # ⚠️ THAT IS THE REAL LESSON: a contract that does not describe
        # the days games are PLAYED cannot notice that the product is out
        # of date, because being out of date is not a deadline it holds.
        # 💰 AND DAILY IS AFFORDABLE BECAUSE THE COST SCALES WITH THE
        # SLATE: props bill markets x regions x GAMES, so a three-game
        # Sunday costs a fraction of a forty-game Saturday. The window
        # check already spends nothing on a day with no games in range.
        "props":  [(8, 30), (15, 0)],                    # 8:30am, 3pm DAILY
        # picks 9:00 + parlays 9:30, daily
        "card":   [(9, 0), (9, 30)],
        # 🔴 TRENDS WAS WEEKLY BY SAM'S OWN SCHEDULE (Mon noon) and it was
        # NOT broken -- its last deadline was Monday and the file is newer
        # than that. ⚠️ But he asked for it fresher and it is FREE, so it
        # is daily now. ⛔ The old value is kept here rather than deleted:
        # ~~[(12, 0, {0})]  Mon noon~~
        # 🔴 3AM ET DAILY. Sam, 2026-09-06: *"i want the trends tab to
        # update everyday for college football at 3am — late enough to
        # update games from the previous day and early enough to provide
        # stats for the next day."*
        # ⛔ ~~noon~~ was mine, not his, and it was the wrong end of the
        # day: a noon rebuild gives the morning's card yesterday's table.
        # ⛔ ~~3am ET is 07:00Z, which is after even a west-coast night
        # game has finished and its box score has settled.~~ **I WROTE
        # THAT WITHOUT MEASURING IT AND IT IS FALSE.** `[measured
        # 2026-09-06]` across all 62 slate days on the 2026 schedule, two
        # finish AFTER their own 3am rebuild: 2026-09-12 and 2026-10-03,
        # both by 29 minutes, and both for the same reason -- **Hawai'i
        # kicks off at 5:59pm HST = 11:59pm ET**, so a 3h30m game ends at
        # 3:29am. That is the Pacific, not a defect, and no clock face
        # Sam would recognise as "3am" fixes it.
        # ✅ WHY 3AM STILL HOLDS: the question is not "same night?" but
        # "is the game in the table before the next board reads it?" Both
        # land in the NEXT morning's 3am pass and the following college
        # slate is 4-5 days later, so no card ever reads a table missing
        # them. `test_trends_schedule.py` asserts that stronger form
        # against the real schedule, and pins the REASON (a Hawai'i
        # kickoff) rather than the two dates -- a late slate for any
        # other reason must go red, not be absorbed.
        "trends": [(3, 0)],                              # 3am ET DAILY
        # ══════════════════════════════════════════════════════════
        # 🔴🔴 THE POSSESSION PROBE, AND IT IS NOT `trends`.
        # ══════════════════════════════════════════════════════════
        # `[measured 2026-09-18]` Both artifacts are written by the SAME
        # mode, and that is exactly why they need separate rows. `trends`
        # is pinned to when the defence-vs-position TABLE is rebuilt;
        # possession is written by EVERY run of that mode. For the NFL
        # those are weekly and daily respectively — so the trends row was
        # green all day while the possession artifact did not exist at
        # all, and `top-<season>` had NO contract entry of any kind.
        # ⛔ A row pointing at the wrong file is worse than no row: it
        # reports healthy about a file it is not watching.
        # ⚠️ 3AM ET, JUST BEFORE THE CRON AND NOT AFTER IT — the same rule
        # this file already learned the hard way for `scores`. The daily
        # arms fire at 07:04Z (`cfb-probe`) and 07:14Z (`nfl-logs`),
        # which is 03:04 and 03:14 ET.
        "possession": [(3, 0)],                          # 3am ET DAILY
        # 🔴 HOURLY. `[Sam: "news should be updating every hour i see that
        # it is 5 hours old, unacceptable"]` ⛔ One 8am deadline meant a
        # 5-hour-old file was INSIDE contract and nothing anywhere was
        # wrong. It is free; there was never a reason for it to be daily.
        "news":   [(h, 0) for h in range(24)],           # every hour
        # `[Sam, 2026-09-25]` the news-flag reviewer: ONCE a day, built by the
        #    hourly news run that follows this deadline (no new cron).
        "flags":  [(10, 5)],                              # 10:05am ET daily
        "teams":  [(10, 35, {6})],                       # Sun, with the rebuild
        # 🔴 SCORES ARE DUE ON THE DAY THE SPORT IS PLAYED. They live in
        # the schedule file, which rode the weekly rebuild -- so on
        # 2026-09-05, the first Saturday of the season, the Scores tab
        # showed 76 FBS games with no score at all. ⚠️ Two deadlines, not
        # ten: one mid-slate and one the morning after. Enough to catch a
        # refresher that has stopped, few enough not to become noise.
        # ⚠️ THE DEADLINE SITS JUST BEFORE A CRON, NOT JUST AFTER ONE.
        # `[2026-09-06]` These were Sat 8pm / Sun 9am, and the crons fire
        # at Sat 21:40 and Sun 09:40 ET -- so the contract went RED FOR
        # 100 MINUTES EVERY SATURDAY waiting for a builder that was always
        # going to be late. ⛔ A deadline is satisfied by a build AT OR
        # AFTER it; having one just BEFORE it proves nothing.
        # ══════════════════════════════════════════════════════════
        # 🔴🔴 DAILY. ~~[(21, 30, {5}), (9, 30, {6})]~~ — **A WEEKEND-SHAPED
        # DEADLINE ON A SPORT THAT IS NOT WEEKEND-SHAPED**, and it hid a
        # two-day-stale Scores tab behind a green verifier.
        # `[measured 2026-09-08]` `schedule-2026.json.gz` had not been
        # rebuilt since **2026-09-06 16:50Z**. The tab showed **6 games on
        # 9/6 and 1 on 9/7 with no score at all** — and NOTHING WAS RED,
        # because the last `scores` deadline that existed had already been
        # satisfied and the next one was days away. `plan()` saw nothing
        # stale; converge repaired nothing; every verifier passed.
        # ⚠️ THE SPORT DISAGREES WITH THE OLD SHAPE. Measured on the 2026
        # schedules: college plays **304 games off Saturday** (Mon 1 ·
        # Tue 19 · Wed 15 · Thu 143 · Fri 116 · Sun 10) and the NFL **44
        # off Sunday** (Mon 17 · Wed 2 · Thu 19 · Fri 4 · Sat 2).
        # ⛔ THIS IS RULE 137 A SECOND TIME. It was applied to props and
        # the card on 2026-09-06 and NOT to scores, because scores had
        # game-day crons and *looked* covered. A cron is not a contract:
        # a dropped cron with no deadline behind it is never repaired.
        # ✅ 4:00am ET DAILY, answered by the 3:54am `fb-scores` cron.
        # ⚠️ WHY 4AM AND NOT 3AM: a Hawai'i home game kicks at 11:59pm ET
        # and a 3h30m game ends ~3:29am (measured across all 62 college
        # slate days). 4:00am clears it; 3:00am does not.
        # ══════════════════════════════════════════════════════════
        "scores": [(4, 0)],                             # 4:00am ET DAILY
        # 🔴 GRADING FOLLOWS THE LOGS, NOT THE GAMES. The grader reads
        # `players-<season>.json.gz`, which `cfb-probe` rebuilds on MONDAY
        # NOON -- so a Saturday card CANNOT be graded on Sunday, whatever
        # anyone wants. ⛔ A deadline before its own input is a deadline
        # that fires every week on a correct system.
        # ⚠️ AND IT MUST ALSO FALL AFTER A REAL BUILDER. `[2026-09-06]` the
        # first version was due Mon 2pm -- but the grader is chained to
        # `card-fb`, which does not run on a Monday for college, so the
        # deadline had no builder before it. ⛔ A deadline nothing can
        # satisfy is an alarm, not a contract. The daily 8:06am ET card
        # run on Tuesday is the builder; the deadline sits an hour later.
        "grade":  [(9, 0, {1})],                         # Tue 9am ET
    },
    "nfl": {
        "odds":   [(8, 0), (14, 0)],                     # 8am, 2pm daily
        "props":  [(7, 0), (11, 0)],                     # 7am, 11am daily
        # picks 7:30 + 11:30 daily, parlays 9:00 daily, record Tue noon
        # ⚠️ 11:30, not 12:00, on the Tuesday. `[2026-09-06]` the Tuesday
        # entry read 12:00 and the last card cron before the next morning
        # is 11:34am ET -- so the moment NFL props land this would have
        # gone red for NINETEEN HOURS every Tuesday. It has not bitten yet
        # only because the contract drops card-fb until a props board
        # exists.
        "card":   [(7, 30), (9, 0), (11, 30), (11, 30, {1})],
        # ⚠️ NFL TRENDS STAYS WEEKLY, and that is a data fact rather than
        # a choice: `nfl-logs` rebuilds from nflverse's weekly stat drop,
        # so a daily deadline would be a deadline nothing can satisfy
        # (rule 112). College is daily because CFBD publishes daily.
        "trends": [(12, 0, {1})],                        # Tue noon
        # ══════════════════════════════════════════════════════════
        # 🔴🔴 THE POSSESSION PROBE, AND IT IS NOT `trends`.
        # ══════════════════════════════════════════════════════════
        # `[measured 2026-09-18]` Both artifacts are written by the SAME
        # mode, and that is exactly why they need separate rows. `trends`
        # is pinned to when the defence-vs-position TABLE is rebuilt;
        # possession is written by EVERY run of that mode. For the NFL
        # those are weekly and daily respectively — so the trends row was
        # green all day while the possession artifact did not exist at
        # all, and `top-<season>` had NO contract entry of any kind.
        # ⛔ A row pointing at the wrong file is worse than no row: it
        # reports healthy about a file it is not watching.
        # ⚠️ 3AM ET, JUST BEFORE THE CRON AND NOT AFTER IT — the same rule
        # this file already learned the hard way for `scores`. The daily
        # arms fire at 07:04Z (`cfb-probe`) and 07:14Z (`nfl-logs`),
        # which is 03:04 and 03:14 ET.
        "possession": [(3, 0)],                          # 3am ET DAILY
        # 🔴 HOURLY, same as college — Sam's complaint was about the news
        # tab and both leagues read the same builder.
        "news":   [(h, 0) for h in range(24)],           # every hour
        # `[Sam, 2026-09-25]` the news-flag reviewer: ONCE a day, built by the
        #    hourly news run that follows this deadline (no new cron).
        "flags":  [(10, 5)],                              # 10:05am ET daily
        "teams":  [],                                    # embedded in the page
        # ⚠️ The NFL's game days are Sunday, Monday and Thursday; its
        # schedule rode the TUESDAY rebuild.
        # ⚠️ Same fix, and the Monday one was worse: NO fb-scores cron runs
        # on a Monday MORNING at all, so a Mon 9am deadline could not be
        # met until Mon 9:45pm -- nearly 13 hours red, every week. The two
        # deadlines now sit on the Sunday slate and the Monday-night one.
        # ══════════════════════════════════════════════════════════
        # 🔴🔴 DAILY. ~~[(21, 30, {6}), (23, 30, {0})]~~ — **A WEEKEND-SHAPED
        # DEADLINE ON A SPORT THAT IS NOT WEEKEND-SHAPED**, and it hid a
        # two-day-stale Scores tab behind a green verifier.
        # `[measured 2026-09-08]` `schedule-2026.json.gz` had not been
        # rebuilt since **2026-09-06 16:50Z**. The tab showed **6 games on
        # 9/6 and 1 on 9/7 with no score at all** — and NOTHING WAS RED,
        # because the last `scores` deadline that existed had already been
        # satisfied and the next one was days away. `plan()` saw nothing
        # stale; converge repaired nothing; every verifier passed.
        # ⚠️ THE SPORT DISAGREES WITH THE OLD SHAPE. Measured on the 2026
        # schedules: college plays **304 games off Saturday** (Mon 1 ·
        # Tue 19 · Wed 15 · Thu 143 · Fri 116 · Sun 10) and the NFL **44
        # off Sunday** (Mon 17 · Wed 2 · Thu 19 · Fri 4 · Sat 2).
        # ⛔ THIS IS RULE 137 A SECOND TIME. It was applied to props and
        # the card on 2026-09-06 and NOT to scores, because scores had
        # game-day crons and *looked* covered. A cron is not a contract:
        # a dropped cron with no deadline behind it is never repaired.
        # ✅ 4:00am ET DAILY, answered by the 3:54am `fb-scores` cron.
        # ⚠️ WHY 4AM AND NOT 3AM: a Hawai'i home game kicks at 11:59pm ET
        # and a 3h30m game ends ~3:29am (measured across all 62 college
        # slate days). 4:00am clears it; 3:00am does not.
        # ══════════════════════════════════════════════════════════
        "scores": [(4, 0)],                             # 4:00am ET DAILY
        # ⚠️ Same rule, one day later: `nfl-logs` rebuilds Tuesday noon,
        # and the next card build after it is Wednesday 8:08am ET.
        "grade":  [(9, 0, {2})],                         # Wed 9am ET
    },
}


# ══════════════════════════════════════════════════════════════════════
# 🔴 THE PAID PROPS WINDOW LIVES HERE, NOT IN `collect.py`, BECAUSE THE
# CONTRACT AND THE COLLECTOR MUST AGREE ABOUT IT.
# `collect.py` reads it back as `FB_PROPS_WINDOW_H = _fresh.FB_PROPS_WINDOW_H`
# so there is still exactly ONE number (rule 66).
# ⛔ WHY IT MOVED. `[measured 2026-09-04]` the collector buys props only
# for games kicking off inside this window -- correct, and it makes a
# Friday afternoon buy NOTHING, because Saturday's college slate is 20+
# hours away. The contract knew nothing about the window, so it called
# that day's pull LATE. **A run cannot clear that, and a banner nobody
# can clear is a banner everybody ignores** -- the exact failure this
# file exists to prevent.
# ⚠️ IF THE PULL EVER GOES BACK TO ONCE A DAY THIS NUMBER MUST GO BACK UP;
# the argument is written out in full at its old home in `collect.py`.
FB_PROPS_WINDOW_H = 14
# 🔴 `[Sam, 2026-10-09]` NFL PROPS FOR THE NEXT SLATE, EVERY DAY ONCE IT IS
#    WITHIN 72 HOURS (Tue/Wed: Thursday's game; Fri/Sat: Sunday's games). The
#    14-hour window above left a Friday with nothing for Sunday's 13 games, and
#    the card showed Thursday's finished one for three days. ✅ One slate, the
#    ET day of the earliest unstarted kickoff, bought on the existing crons.
#    💰 Measured from the stored pulls' own credits_used (12 a game on a day's
#    first us,us2 pull, 6 on each us2 refresh): about +540 credits a week.
#    ⛔ College keeps the 14-hour window: its slates are daily and a 72-hour
#    window would buy 40-game Saturdays three times over.
FB_NEXT_SLATE_H = {"nfl": 72}


def _et_day(k):
    try:
        from zoneinfo import ZoneInfo
        return k.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    except Exception:
        return (k - ET_OFFSET).strftime("%Y-%m-%d")


def next_slate(kickoffs, now):
    """The next slate's UNSTARTED kickoffs: those on the ET day of the earliest
    one after `now`, sorted. [] when nothing is unstarted."""
    later = sorted(k for k in kickoffs if k > now)
    return [k for k in later if _et_day(k) == _et_day(later[0])] if later else []


# ══════════════════════════════════════════════════════════════════════
# 🔴 THE PROPS STAND-DOWN ASKS THE CONTRACT. `[2026-10-24]`
# ══════════════════════════════════════════════════════════════════════
# `collect.props_is_fresh` stood a pull down when ANY snapshot was under 45
# minutes old ~~(`PROPS_FRESH_MIN`)~~, while this contract counts a pull only
# for a deadline it was made AT OR AFTER. Two rules for one question, and they
# split both ways:
#   ⛔ a pull 23 minutes BEFORE the 11:00 ET deadline: converge planned the
#      next pull (owed), the stand-down refused it ("a pull landed 24 min
#      ago"), and the gate failed the run "6m past due" (collect 39137387911
#      on 10-18, 40103939010 on 10-24). The buy only moved to the first pass
#      after the 45 minutes, and every pass until then was red.
#   ⛔ a pull for the deadline in force, over 45 minutes old: a late cron
#      bought the same deadline again. 10-24's 14:37Z NFL pull was a second
#      7am pull (11:27Z had met it), and it is what tripped the 11am one.
# ✅ ONE ANSWER: the stand-down judges, through `survey`, the very row the
#    contract builds (`props_rows`: its directory and its `props_times`
#    deadlines). A pull already made for the deadline in force stands its
#    backup down (still free, still keyed on the storage directory); a pull
#    the contract owes is never refused.
# 💰 It never adds a pull: an owed pull the old window refused was bought by
#    the first pass past 45 minutes anyway, and a second pull for a deadline
#    already met is now refused. Every props cron fires after its deadline,
#    so an on-time cron still buys exactly once.
def props_times(league):
    """The deadlines a paid PROPS pull answers in this league."""
    return FB_TIMES[league]["props"] if league in FB_TIMES else ODDS


def props_rows(league, data, utc_day):
    """The league's paid props pull rows: the contract's own, and the rows
    `pull_owed` judges a stand-down on."""
    if league in FB_TIMES:
        return [("props-player", ("dir", f"{data}/{utc_day}/props-player"), props_times(league),
                 True, "Player Props — the paid pull")]
    return [("props-pitcher", ("dir", f"{data}/{utc_day}/props-pitcher"), props_times("mlb"),
             True, "Player Props — pitcher markets"),
            ("props-batter", ("dir", f"{data}/{utc_day}/props-batter"), props_times("mlb"),
             True, "Player Props — hitter markets")]


def pull_owed(league, data, mode, now=None):
    """The contract's verdict on ONE paid props pull -> its `survey` row.

    `stale` True: the contract owes a pull (none landed at or after the
    deadline in force). ⚠️ Judged even when the contract has dropped the row
    as not warranted: the collector then buys nothing anyway, and a pull it
    did make still stands its backup down. ⛔ A mode that is not one of the
    league's paid props pulls raises: there is no contract answer to give."""
    now = now or datetime.datetime.now(UTC)
    rows = [r for r in props_rows(league, data, now.strftime("%Y-%m-%d")) if r[0] == mode]
    if not rows:
        raise ValueError(f"{mode} is not a paid props pull in {league}'s contract")
    return survey(now=now, entries=rows)[0]


# ══════════════════════════════════════════════════════════════════════
# 🔴 HOW LONG A REFUSED CARD MAY STAY QUIET.
# `card_gate` lets an ACCEPTED failure keep the run green, and that is
# right for a decision already taken -- an alarm firing every fifteen
# minutes for a settled question gets ignored, and ignoring red is how
# the original staleness survived a whole day.
# ⛔ BUT IT IS NOT RIGHT FOREVER. `[the state on 2026-09-04]` Sam accepted
# T37, the run went green, and **the card is still refused every rebuild,
# so Gizmo's Picks does not update at all.** Green build, frozen product,
# no alarm -- the same failure this repo keeps learning about, pointing
# the other way.
# ✅ SO THE DOWNGRADE IS BOUNDED. An accepted failure buys quiet for a
# DECISION, not permanent silence about a board that has stopped moving.
# ⚠️ THE SIGNAL IS THE CARD'S OWN AGE, not the failure file's: that file
# is rewritten every pass, so it says when the LAST refusal happened and
# never when the FIRST one did. The card's age is exactly "how long since
# a card published", which is the thing that matters.
# 🔒 48 HOURS = TWO CONSECUTIVE MISSED CARD DEADLINES. Chosen with Sam,
# 2026-09-04, before it had ever fired. ⛔ Do not raise it to make a run
# go green -- that is the move this constant exists to prevent.
CARD_REFUSED_GRACE_MIN = 48 * 60


def _et_zone():
    """Real Eastern, when the platform has tzdata; None when it does not."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("America/New_York")
    except Exception:
        return None


def kickoffs_utc(league, path):
    """Every kickoff in a stored football schedule, as REAL UTC.

    🔴 THE TWO LEAGUES DO NOT AGREE ABOUT WHAT `start` MEANS, AND READING
    THEM THE SAME WAY IS A FOUR-HOUR ERROR ON A FOURTEEN-HOUR WINDOW.
        ncaaf   CFBD `startDate`   "2026-08-27T22:00:00.000Z"  -> real UTC
        nfl     nflverse gameday + gametime  "2026-09-13T13:00"
                -> LOCAL EASTERN, NO TIMEZONE. `nfl.py` carries it as-is
                   ON PURPOSE: *"an invented offset would put a Sunday 1pm
                   game on the wrong day for half the world."*
    ⛔ `[measured 2026-09-04]` `test_props_window.py` stamped BOTH with
    `tzinfo=utc`, which reads every NFL kickoff as FOUR HOURS EARLIER than
    it is. That is what produced "six London games at 5:30am ET" -- they
    kick at **9:30am ET**. The test was pessimistic, so it invented a gap
    rather than hiding one, **but a four-hour error is a four-hour error
    and it is fixed here, in one place, for every caller.**
    ⚠️ Winter matters: ET is UTC-5 from November, and the NFL plays into
    January. Real `zoneinfo` is used where it exists and the file's fixed
    -4 is the fallback, which is an hour off in the winter and SAID SO
    rather than assumed away.

    Returns aware UTC datetimes, or **None if the schedule cannot be read**
    -- and None means *cannot tell*, never *nothing to do*.
    """
    games = kickoff_games(league, path)
    return None if games is None else [k for k, _g in games]


def kickoff_games(league, path):
    """`kickoffs_utc`'s reading WITH each game's row: [(real UTC kickoff, game)],
    or None when the schedule cannot be read. ⛔ ONE copy of the reading (rule
    117): `[2026-10-17]` the college injury checks (`health`) also need each
    game's `final`, and a second reader would be a second chance to get the
    two leagues' `start` wrong."""
    if not os.path.exists(path):
        return None
    try:
        with gzip.open(path, "rt") as fh:
            doc = json.load(fh)
    except Exception:
        return None
    zone = _et_zone() if league == "nfl" else None
    out = []
    for g in doc.get("games") or []:
        s = (g.get("start") or "").strip()
        if not s:
            continue
        # ⚠️ COLLEGE PRICES FBS ONLY, so a D-II kickoff is not a reason to
        # buy anything. ⛔ Keep the game when EITHER side is FBS -- an
        # `!= "fcs"` test misses D-II and D-III entirely, which once put
        # 188 games in a cost model that should have held 46.
        if league == "ncaaf" and "fbs" not in (str(g.get("home_class")),
                                               str(g.get("away_class"))):
            continue
        utc = s.endswith("Z")
        try:
            t = datetime.datetime.fromisoformat(
                s.replace("Z", "").split(".")[0])
        except Exception:
            continue
        if utc:
            k = t.replace(tzinfo=UTC)
        elif zone is not None:
            k = t.replace(tzinfo=zone).astimezone(UTC)
        else:
            k = t.replace(tzinfo=UTC) + ET_OFFSET
        out.append((k, g))
    return out


def _props_warranted(league, latest, now):
    """Was a paid props pull worth making at the deadline that just passed?

    🔴 A PULL THAT CORRECTLY BUYS NOTHING IS NOT A LATE PULL. On a Friday
    the whole college slate is Saturday, 20+ hours out, so nothing is
    inside `FB_PROPS_WINDOW_H` and the collector spends nothing. ⛔ Marking
    that late asks for a repair no run can make.
    ⚠️ AND THE FAIL-SAFE POINTS THE OTHER WAY: **no readable schedule means
    CANNOT TELL, and cannot-tell keeps the row governed.** Absence of
    evidence must never be the thing that silences a check.
    """
    due = last_due(FB_TIMES[league]["props"], now)
    if due is None:
        return False
    ks = kickoffs_utc(league,
                      f"{latest}/schedule-{current_football_season(now)}.json.gz")
    if ks is None:
        return True
    if league in FB_NEXT_SLATE_H:
        ks = next_slate(ks, due)
        return bool(ks) and ks[0] <= due + datetime.timedelta(hours=FB_NEXT_SLATE_H[league])
    end = due + datetime.timedelta(hours=FB_PROPS_WINDOW_H)
    return any(due <= k <= end for k in ks)


def has_contract(league):
    """Does this league have freshness rows, and therefore a converge?

    ⛔ `collect.py` REFUSED TO CONVERGE ANY LEAGUE BUT MLB — the guard read
    `LEAGUE != "mlb"` and it was right when football had no contract.
    🔴 IT OUTLIVED THAT. Football runs were one-shot, so **a missed cron
    was never repaired**: the college card was built at 8:51am against a
    9:00am deadline, both 9am card crons were dropped by GitHub, and
    nothing rebuilt it for the rest of the day. The whole point of a
    contract is that the next run catches up.
    """
    return league == "mlb" or league in FB_TIMES


def _literal(module, name):
    """A module's top-level literal, PARSED (⛔ never imported: fb_model drags in
    card_fb, which exits under LEAGUE=mlb). A tree without the file names no champion."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), module)
    if not os.path.exists(p):
        return {}
    src = open(p, encoding="utf-8").read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


def champion_inputs(league, champion=None):
    """[(file pattern, deadline key)] behind fb_model.CHAMPION[league]; its writer is
    `nfl-logs` (NFL) or `cfb-probe` (college), the league's logs / CFBD run."""
    name = (champion or _literal("fb_model.py", "CHAMPION")).get(league)
    inp = _literal("fb_challengers.py", "CHALLENGERS")[name]["input"] if name else None
    return [inp] if inp else []          # T66's S reads no file of its own


def _football_contract(league, data, picks, now):
    """The same shape as MLB's, for one football league."""
    latest = f"{data}/latest"
    utc_day = (now or datetime.datetime.now(UTC)).strftime("%Y-%m-%d")
    T = FB_TIMES[league]
    season = current_football_season(now)
    rows = [
        ("gamelines", ("file", f"{latest}/board.json"), T["odds"], True,
         "Odds + Scores & Matchups — the football board"),
        *props_rows(league, data, utc_day),          # props-player, the paid pull
        ("props-board", ("file", f"{latest}/props.json.gz"), T["props"], False,
         "Player Props — the join that puts props on the board"),
        # 🔴 `[Sam, 2026-09-24]` THE ALT-LINE PULL, on the props deadlines and
        #    the props window. ⛔ Its own mode, planned by converge, so no cron
        #    changes: a missed deadline is repaired by the next run. A pull that
        #    correctly buys nothing still writes its snapshot, so it is not late.
        ("alt-lines", ("dir", f"{data}/{utc_day}/alt-lines"), T["props"], True,
         "Game Lines — the paid alt-line pull"),
    ]
    # 🔴 `[Sam, 2026-10-17]` COLLEGE INJURY REPORTS (cfb_injuries.py, design
    #    research/cfb_injuries_design.md §1 item 2): the conference availability
    #    reports, read on the college passes that already run. ⛔ NO CRON CHANGE:
    #    converge plans the mode from this row.
    #    ✅ THE ROW IS ON THE PROBE, which the reader writes on EVERY attempt. A
    #    stale probe means the reader did not run, which converge repairs.
    #    ✅ AND A READER THAT RAN BUT READ NOTHING IS STALE TOO (`health`): a
    #    source not confirmed within FETCH_MAX_AGE_H while a game is close, or
    #    a conference archive no longer refreshed in season, makes the row
    #    stale with its reason, so it is planned again and reaches Sam as a
    #    soft warning, freshness.json and the watchdog's `fresh:` finding.
    #    ⚠️ ITS DEADLINES ARE HOURLY, EVERY DAY: `T["news"]`, the list the hourly
    #    college cron already answers (test_fb_freshness §4 holds every
    #    FB_TIMES list to a cron). An hourly deadline is never built more than
    #    GRACE_MIN late, so a delayed cron leaves no `late:` finding.
    #    🔴 AND WED-SAT ET IT IS PLANNED ON EVERY COLLEGE PASS (`EVERY_PASS`),
    #    fresh or not: a report posted at 17:20Z must not wait for the next
    #    hour's pass while a card is built in this one. ⛔ Planned, never marked
    #    stale: a five-minute deadline would read stale at the end of any pass
    #    that ran longer than five minutes.
    #    ⛔ FIRST OF ALL THE ROWS (~~before the card rows~~): plan() runs modes in contract
    #    order, and the card is built by `props-player` as well as `card-fb`, so a card built
    #    in the same pass reads this pass's reports. `[2026-10-17, review]` placed before the
    #    card rows only, a props pass built the card on the previous pass's reports.
    #    ✅ SOFT (see SOFT): a failed read costs a why sentence, never a card.
    if league == "ncaaf":          # college only: the NFL's injuries ride nfl-logs
        rows.insert(0,
            ("cfb-injuries", ("file", f"{latest}/injuries-probe-{season}.json"), T["news"], False,
             "College injury reports — the reader's probe, written on every attempt"))
    rows += [
        # ⛔ ONE ROW FOR THE CARD FILE. Picks, Parlays and Track Record all
        # read it; three rows would be three chances to disagree.
        # 🔴 THE CARD PATH IS NOT `{picks}` AND MUST NOT BE. `card_fb.py`
        # writes to a HARDCODED `picks/fb-<league>-latest.json`, while
        # `collect.py` hands this function `PICKS`, which for football is
        # `picks/ncaaf` -- **a directory that does not exist.**
        # ⛔ `[caught 2026-09-04, before the gate was switched on]` probing
        # `{picks}/fb-...` reported the card MISSING FOREVER in production,
        # while reading FINE in a hand-run survey that passed `picks`.
        # ⚠️ A FACT ABOUT A QUERY IS NOT A FACT ABOUT THE WORLD: the
        # earlier survey was right about the argument it was given and
        # wrong about the argument the collector actually passes.
        # ✅ THE CONTRACT FOLLOWS THE WRITER. If `card_fb.py` ever moves
        # the file, this line moves with it -- `test_fb_freshness.py` pins
        # that this row is immune to the caller's `picks` argument.
        ("card-fb", ("file", f"picks/fb-{league}-latest.json"), T["card"], False,
         "Gizmo's Picks + Parlays + Track Record"),
        ("news", ("file", f"{latest}/news.json"), T["news"], False, "News"),
        # `[Sam, 2026-09-25]` the daily news flags on board rows — DESCRIPTIVE.
        ("news", ("file", f"{latest}/news-flags.json"), T["flags"], False,
         "News flags — injury status and headlines on board rows"),
        # ══════════════════════════════════════════════════════════════
        # 📰 THE DATED NEWS ARCHIVE, AND IT GETS A CONTRACT ENTRY IN THE
        #    SAME PR THAT CREATES IT.
        # ⛔ `top-<season>.json.gz` shipped with NO entry and the contract
        #    read `stale: False, ok: True` WHILE THE FILE DID NOT EXIST.
        #    An artifact nothing watches is an artifact that can stop
        #    being written and nobody finds out.
        # ⚠️ HOURLY, the same deadline as the pull it rides on — the
        #    archive is written in the same code path, immediately after
        #    `latest/news.json`, so the two can only diverge through a
        #    bug, which is exactly what this is here to surface.
        # ⛔ `dir`, not `file`: the archive is one file per pull, so the
        #    question is "when was the newest one written".
        # 🔴 THE MODE IS THE WRITER, `news`, LIKE EVERY OTHER ROW. Converge
        #    runs the mode a row names. This row named `news-archive`, which
        #    `run_mode` has no arm for, so every pass that found the archive
        #    stale printed "unknown mode: news-archive" and repaired nothing
        #    (collect runs #1766–#1835, 2026-09-26). The row was SOFT, so
        #    no run went red. Two rows under `news` are planned as ONE run.
        #    ✅ `test_contract_modes.py` fails on any contract mode, in any
        #    league, that `run_mode` does not dispatch.
        ("news", ("dir", f"{data}/{utc_day}/news"), T["news"], False,
         "News — the dated archive the line-movement question needs"),
    ]
    # ⚠️ TRENDS IS SEASON-STAMPED, so the probe names the season rather
    # than a generic file -- a 2025 table sitting where 2026 belongs is
    # exactly the drift this contract is for.
    # 🔴 BUT A SEASON THAT HAS NOT STARTED IS NOT LATE. `[the rule this
    # file already applies to the NFL back-fill]` The 2026 table cannot
    # exist until games have been played, and marking it stale every day
    # until then produces a banner NOBODY CAN CLEAR -- which is how a
    # staleness warning becomes noise everyone learns to ignore, the
    # exact failure this whole file exists to prevent.
    # ✅ So the probe falls back to the season the page is ACTUALLY
    # SERVING, and asks whether THAT is fresh.
    tpath = f"{latest}/allowed-by-position-{season}.json.gz"
    if not os.path.exists(tpath):
        prev = f"{latest}/allowed-by-position-{season - 1}.json.gz"
        if os.path.exists(prev):
            tpath = prev
    rows.append(
        (("cfb-probe" if league == "ncaaf" else "nfl-logs"),
         ("file", tpath), T["trends"], False,
         "Trends — defence-vs-position"))
    # ══════════════════════════════════════════════════════════════
    # 🔴🔴 THE *OFFENCE* SIDE IS A SECOND FILE AND IT HAD NO ROW.
    # ══════════════════════════════════════════════════════════════
    # `index.html`'s `fbPath()` picks the stem from the tab the reader is
    # on: `allowed-by-position-{season}` for defence, **`offense-by-
    # position-{season}` for offence.** One builder writes both — its own
    # comment says *"⛔ ONE FILE PER SIDE, BUILT BY ONE FUNCTION ON THE
    # COLLECTOR"* — so the row costs no cron and shares the deadline.
    # ⛔ WATCHING ONE OF TWO FILES IS THE SAME HOLE AS WATCHING NEITHER
    # for the half nobody watched. The Trends tab has two sides and the
    # contract described one of them.
    # ✅ Same season fallback as the defence row, for the same reason.
    opath = f"{latest}/offense-by-position-{season}.json.gz"
    if not os.path.exists(opath):
        oprev = f"{latest}/offense-by-position-{season - 1}.json.gz"
        if os.path.exists(oprev):
            opath = oprev
    rows.append(
        (("cfb-probe" if league == "ncaaf" else "nfl-logs"),
         ("file", opath), T["trends"], False,
         "Trends — offence-by-position"))
    # ══════════════════════════════════════════════════════════════
    # 🔴🔴 AND THE PLAYER LOGS, WHICH EVERY OTHER FOOTBALL TABLE IS MADE
    #      FROM — ALSO WITH NO ROW OF ANY KIND.
    # ══════════════════════════════════════════════════════════════
    # `jgetGz(`${LG_DATA[LEAGUE]}/latest/players-${season}.json.gz`)` is
    # read directly by the page, and the same job writes it as writes the
    # two tables above.
    # `[measured on origin/main 2026-09-19T17:25Z]`
    #
    #     data/nfl/latest/players-2026.json.gz    2026-09-17T07:34Z   57.9h
    #     data/ncaaf/latest/players-2026.json.gz  2026-09-19T07:53Z    9.5h
    #
    # ⚠️ AND IT IS NOT LATE EITHER, BY THIS CONTRACT'S OWN TERMS: the NFL
    # logs are a WEEKLY artifact (`T["trends"]`, Tue), and 57.9h has not
    # reached the next Tuesday. ⛔ So this row does not make today red,
    # and saying it would be false. What it does is make the file
    # ANSWERABLE — today the contract holds no row naming it at all, so
    # if the nflverse fetch stays broken past Tuesday nothing would say
    # so, and the two aggregate rows would not say it either: they are
    # rebuilt from the CACHED log when the fetch fails, so the input can
    # rot while its outputs keep a current timestamp.
    lpath = f"{latest}/players-{season}.json.gz"
    if not os.path.exists(lpath):
        lprev = f"{latest}/players-{season - 1}.json.gz"
        if os.path.exists(lprev):
            lpath = lprev
    rows.append(
        (("cfb-probe" if league == "ncaaf" else "nfl-logs"),
         ("file", lpath), T["trends"], False,
         "Trends + Dossier — the weekly player logs"))
    # ══════════════════════════════════════════════════════════════
    # 🔴🔴 AND SO DOES POSSESSION — RULE 78 AGAIN, AND IT ALREADY BIT.
    # ══════════════════════════════════════════════════════════════
    # `[measured 2026-09-18]` The first full production day of the college
    # path: the dossier landed in both leagues, and **section 6 was
    # UNAVAILABLE for all 32 NFL games** because `build_possession` never
    # ran — the daily `14 7 * * *` arm was DROPPED, which GitHub does and
    # this repo has measured repeatedly. ⛔ That is not a code defect.
    #
    # 🔴 THE DEFECT IS THAT NOTHING NOTICED. `top-<season>.json.gz` had no
    # contract entry of any kind, so the survey read `stale: False,
    # ok: True` while the artifact did not exist at all, and §6 would have
    # stayed UNAVAILABLE indefinitely with the contract reporting healthy.
    # ⚠️ That is the `t54.json` shape: an artifact nothing tracks is an
    # artifact nobody misses.
    #
    # ══════════════════════════════════════════════════════════════
    # ⛔ THE PROBE IS THE *PROBE*, NOT THE TABLE, AND THAT IS THE WHOLE
    #    DESIGN.
    # ══════════════════════════════════════════════════════════════
    # `top-{season}.json.gz` is written ONLY when the derivation holds
    # together. `top-probe-{season}.json` is written EITHER WAY — both
    # builders say so in as many words: *"⛔ THE PROBE IS WRITTEN EITHER
    # WAY. A diagnosis that exists only in an Actions log is a diagnosis
    # you do not have."*
    #
    # 🔴 SO THE TWO FILES ANSWER TWO DIFFERENT QUESTIONS, and only one of
    # them is this contract's business:
    #
    #    probe MISSING or STALE  ->  THE BUILDER DID NOT RUN. That is a
    #                                dropped arm, it is repairable, and
    #                                converge should rebuild it. ✅
    #    probe FRESH, table absent -> THE BUILDER RAN AND REFUSED. The
    #                                reason is in the probe and §6 says
    #                                it. ⛔ NOT late, and NOT this
    #                                contract's business.
    #
    # ⛔ A ROW ON THE TABLE WOULD CONFLATE THEM, and the cost is not
    # hypothetical: college's derivation is refusing RIGHT NOW over CFBD's
    # play ordering (36.28 pct anomaly against a 2.0 bar, and correctly).
    # A row on `top-{season}.json.gz` would mark the site stale on every
    # single run until that ordering question is settled — **a banner
    # nobody can clear**, which is the exact failure this file argues
    # against in four separate places and has already lived through once.
    # ✅ Probing the probe asks "did the builder run?", which is the
    # question a freshness contract exists to ask.
    rows.append(
        (("cfb-probe" if league == "ncaaf" else "nfl-logs"),
         ("file", f"{latest}/top-probe-{season}.json"), T["possession"],
         False, "Dossier §6 — time of possession"))
    # ⛔ AND THE SCORES REFRESHER GETS A ROW, because a builder nothing
    # watches runs approximately never (rule 78). The probe is the CURRENT
    # season's schedule -- the file `home_score`, `away_score` and `final`
    # actually live in.
    rows.append(
        ("fb-scores",
         ("file", f"{latest}/schedule-{season}.json.gz"), T["scores"], False,
         "Scores & Matchups — the day's results"))
    # ══════════════════════════════════════════════════════════════
    # 🔴🔴 THE DOSSIER FILE ITSELF — EIGHT SECTIONS, ZERO CONTRACT ROWS.
    # ══════════════════════════════════════════════════════════════
    # `dossiers.json.gz` is what `index.html` reads for **all eight** of
    # Sam's per-game checks. It had no row of any kind, and this file's
    # own `top-<season>` comment already says why that matters: *"an
    # artifact nothing tracks is an artifact nobody misses."*
    #
    # ⚠️ AND IT IS NOT LATE TODAY — SAID PLAINLY RATHER THAN DRESSED UP.
    # `[measured on origin/main 2026-09-19T17:25Z]`
    #
    #     data/ncaaf/latest/dossiers.json.gz   15:52:53Z    92 min
    #     data/nfl/latest/dossiers.json.gz     15:52:46Z    93 min
    #
    # ⛔ ~~"27h old on both leagues"~~ was measured on a two-day-old
    # checkout and is WRONG. It is struck rather than deleted because it
    # is the same mistake the row exists to prevent one level up: a fact
    # about the tree in front of you is not a fact about the product.
    # ✅ THE ROW IS STILL THE POINT. It adds no red today; what it adds
    # is the ability to go red at all. Until now the eight sections
    # Sam reads could have stopped being written and the contract would
    # have reported both leagues healthy, indefinitely.
    #
    # ✅ NO NEW CRON, AND NO NEW MODE. The dossier is built inside
    # `card-fb`, so this is a SECOND ROW under the mode that already
    # exists and already carries `T["card"]` — exactly the shape
    # `cfb-probe` and `nfl-logs` already use for their two files each.
    # That also means it inherits the existing repair path rather than
    # inventing one (`SAFE_REPAIRS` holds `card-fb` today).
    # ⚠️ GATED THE SAME WAY THE CARD IS. Before a league's first paid
    # pull there is no board, no card and no dossier; "cannot exist yet
    # is not late" (rule 86) governs all three, and the `props.json.gz`
    # filter below withdraws this row with the card it belongs to.
    rows.append(
        ("card-fb", ("file", f"{latest}/dossiers.json.gz"), T["card"], False,
         "Dossier — all eight per-game checks"))
    # 🔴 THE PICK MODEL'S FILE, IN THE SAME PR THAT CREATES IT (the rule the
    #    news archive row states). `[Sam, 2026-09-23]` It is rebuilt by the
    #    same `card-fb` run as the dossier, on the same deadlines.
    rows.append(
        ("card-fb", ("file", f"{latest}/fb-model.json"), T["card"], False,
         "Model picks + walk-forward record"))
    # `[Sam, 2026-10-15]` the score-first model's report, built by the same run.
    rows.append(
        ("card-fb", ("file", f"{latest}/fb-score-model.json"), T["card"], False,
         "Score model: predicted scores + backtest (report only)"))
    # `[Sam, 2026-10-12]` T65: once Sam names a game-model CHAMPION, the file
    #    behind its input is a row like the others (talent: once a season,
    #    so only a missing season's file is late).
    for fname, due in champion_inputs(league):
        rows.append((("nfl-logs" if league == "nfl" else "cfb-probe"),
                     ("file", f"{latest}/{fname.format(s=season)}"),
                     T[due] if due else [], False, CHAMPION_INPUT))
    # `[Sam, 2026-10-14]` NEW DATA, STORED ONLY (see STORED_ONLY): the daily
    #    NWS forecasts and, by league, injuries / advanced stats, venues and CFBD
    #    weather. History seasons and once-a-season files are late only when
    #    missing; CFBD weather has a row once its file exists (only when the
    #    key's tier has /games/weather).
    _yrs = sorted(set(FOOTBALL_HISTORY) | {season})
    _store = [(f"weather-{season}", T["possession"])]
    if league == "nfl":
        _store += [(f"injuries-{s}", T["possession"] if s == season else []) for s in _yrs]
    else:
        _store += [(f"adv-{s}", T["possession"] if s == season else []) for s in _yrs]
        _store += [(f"venues-{season}", [])]
        _store += [(f"cfbd-weather-{s}", []) for s in _yrs
                   if os.path.exists(f"{latest}/cfbd-weather-{s}.json.gz")]
    # `[Sam, 2026-10-15]` T70's history seasons, written once (late only when missing).
    _hist = ((2018, 2019, 2020, 2021, 2022, 2023, 2024), ("schedule",)) if league == "nfl" else \
        ((2023, 2024), ("schedule", "lines"))
    for _y in _hist[0]:
        for _k in _hist[1]:
            rows.append((("nfl-logs" if league == "nfl" else "cfb-probe"),
                         ("file", f"{data}/history/{_k}-{_y}.json.gz"), [], False,
                         "Stored only — older seasons for a challenger"))
    for _stem, _due in _store:
        rows.append((("nfl-logs" if league == "nfl" else "cfb-probe"),
                     ("file", f"{latest}/{_stem}.json.gz"), _due, False,
                     "Stored only — no tab or model reads it yet"))
    # `[Sam, 2026-10-17]` COLLEGE INJURIES' STORED FILES (STORED_ONLY; design §1):
    #    the conference archives (written by cfb-injuries) and CFBD's roster
    #    jerseys and defensive box score (written by cfb-probe, at no extra call;
    #    2025 is filled once). No model reads them unless §4's backtest passes.
    #    ⛔ NO DEADLINE, every season: each is rewritten only when its content
    #    changes, so its age says nothing (a quiet week, the off-season), and a
    #    clock deadline on it would be a warning nobody can clear.
    #    ✅ BUT A FILE THAT STOPPED CHANGING IS STILL CAUGHT, by what should
    #    have changed it, never by its age:
    #      defense-<season>  `health`: last written before the kickoff of the
    #                        newest final FBS game over DEFENSE_LAG_H old, so
    #                        that game's box scores never reached it.
    #      injury-archive    the probe row's `health`: a conference archive
    #                        that answered before and has not been refreshed
    #                        for 2 x ARCHIVE_REFRESH_H while the season is on.
    #      roster-<season>   ⚠️ NOT JUDGED (an accepted gap): a roster does not
    #                        change with a game, so nothing says when it should
    #                        have. It rides the same daily CFBD build as
    #                        defense-<season>, whose check proves that build
    #                        runs; a /roster call failing alone leaves it as it
    #                        was, which only cfb.py recording its own outcome
    #                        could tell apart from a roster that did not change.
    #    ⛔ NO ROW ON THE DATED SNAPSHOTS (data/ncaaf/<day>/injury-reports/), for
    #    the same reason: one is written only when a report changed, so a quiet
    #    Monday has none and a `dir` row would read MISSING. Their writer is
    #    watched by the probe row above, the probe records the newest
    #    snapshot's age, and a report whose source has not been confirmed
    #    recently is never shown (§2 (b)). STORED_ONLY still names them, so a
    #    row added later can never plan a run or turn one red.
    if league == "ncaaf":
        for _y in _yrs:
            rows.append(("cfb-injuries", ("file", f"{data}/history/injury-archive-{_y}.json.gz"), [], False,
                         "Stored only — the conference injury archives (no model reads them yet)"))
            for _k in ("roster", "defense"):
                rows.append(("cfb-probe", ("file", f"{latest}/{_k}-{_y}.json.gz"), [], False,
                             "Stored only — college injuries' CFBD inputs (no model reads them yet)"))
    # `[Sam, 2026-09-24]` the props model's file, rebuilt by the same run.
    rows.append(
        ("card-fb", ("file", f"{latest}/fb-props-model.json"), T["card"], False,
         "Prop model picks + walk-forward record"))
    # `[Sam, 2026-09-24]` the card's stated-vs-actual bands and its test.
    rows.append(
        ("card-fb", ("file", f"{latest}/card-calibration.json"), T["card"], False,
         "Card calibration — stated vs actual by band"))
    # `[Sam, 2026-09-24]` "What the model showed, graded".
    rows.append(
        ("card-fb", ("file", f"{latest}/model-ledger.json"), T["card"], False,
         "What the model showed, graded"))
    # `[Sam, 2026-09-24]` the alt ladders and their alt-rung record, rebuilt
    #    by the same run (and right after every alt-line pull). `[Sam,
    #    2026-10-01]` no longer drawn on the Game Lines tab; the card's
    #    alternate spreads still read the ladder.
    rows.append(
        ("card-fb", ("file", f"{latest}/game-lines.json.gz"), T["card"], False,
         "Gizmo's Picks — the alt ladders the card's alternate spreads read"))
    rows.append(
        ("card-fb", ("file", f"{latest}/game-lines-record.json"), T["card"], False,
         "Alt ladders — the alt-rung track record"))
    # `[Sam, 2026-10-01]` the Game Lines tab: the model's pick to win each
    #    game and its record (winners.py), rebuilt by the same run.
    rows.append(
        ("card-fb", ("file", f"{latest}/winners.json"), T["card"], False,
         "Game Lines — the model's pick to win each game"))
    # `[Sam, 2026-09-25]` card vs props-model agreement labels and their record.
    rows.append(
        ("card-fb", ("file", f"{latest}/agreement.json"), T["card"], False,
         "Card vs props model — agreement labels"))
    # ⛔ AND THE GRADER GETS ONE TOO, for the same reason (rule 78). The
    # probe is `record.json` -- the file the Track Record tab reads.
    # ⚠️ ONLY ONCE A CARD EXISTS TO GRADE. Before the first published card
    # there is nothing for it to produce, and "cannot exist yet is not
    # late" (rule 86) governs here exactly as it does for the card.
    # ══════════════════════════════════════════════════════════════
    # 🔴🔴 THE GLOB IS `picks/`, NOT `{picks}` — THE SAME CALLER BUG THE
    #      CARD ROW ABOVE ALREADY FIXED, LEFT IN THE LINE BELOW IT.
    # ══════════════════════════════════════════════════════════════
    # ~~`glob.glob(f"{picks}/fb-{league}-2*.json")`~~ **STRUCK
    # 2026-09-19.** `collect.py` passes `PICKS`, which for football is
    # `picks/nfl` / `picks/ncaaf` — **directories that do not exist** —
    # while `card_fb.py` writes every card to a HARDCODED `picks/`.
    # ⛔ So the glob matched NOTHING on every production run and this
    # row was WITHDRAWN every time. `[measured 2026-09-19]`
    #
    #     picks=picks        -> 5 nfl / 10 ncaaf cards   row PRESENT
    #     picks=picks/nfl    -> 0 cards                  row WITHDRAWN
    #     picks=picks/ncaaf  -> 0 cards                  row WITHDRAWN
    #
    # …and the middle two are what the collector actually passes. The
    # football grader has therefore been unwatched since the row was
    # added to watch it — rule 78, inside the fix for rule 78.
    # ⚠️ THE ROW ABOVE CARRIES THIS EXACT LESSON IN ITS OWN COMMENT
    # ("a fact about a query is not a fact about the world") and the
    # gate two lines below it was never brought along.
    # ✅ `test_fb_freshness.py` §8 now asks it of EVERY row rather than
    # only of `card-fb`, which is how this surfaced.
    if T.get("grade") and glob.glob(f"picks/fb-{league}-2*.json"):
        rows.append(
            ("fb-record", ("file", f"{latest}/record.json"), T["grade"], False,
             "Track Record — the board's own graded record"))
        # 🔴 `[2026-09-22]` THE PAGE READS THE DRILL-DOWN TOO, through a
        #    variable, so `test_page_contract.py`'s literal-argument scan
        #    never saw it. Same writer (`record_fb.py`), same deadline.
        rows.append(
            ("fb-record", ("file", f"{latest}/record-detail.json.gz"), T["grade"], False,
             "Track Record — the per-pick drill-down"))
    # ⛔ AND AN ARTIFACT THAT CANNOT EXIST YET IS NOT LATE EITHER. Before
    # a league's first paid pull there is no props board, so there is no
    # card either -- neither is a defect and neither is repairable by any
    # run. ⚠️ They rejoin the contract the moment the first board lands.
    if not os.path.exists(f"{latest}/props.json.gz"):
        rows = [r for r in rows if r[0] not in ("props-board", "card-fb")]
    # ⛔ AND THE SAME RULE FOR A PULL THAT CORRECTLY BOUGHT NOTHING. If no
    # game kicked off inside the window of the deadline that just passed,
    # the collector spent nothing and there is no newer board to join --
    # so neither the pull nor the join is late. ⚠️ THE CARD STAYS
    # GOVERNED: it is free, it rebuilds from whatever board exists, and a
    # dropped card cron is exactly what converge is now here to repair.
    if not _props_warranted(league, latest, now):
        rows = [r for r in rows if r[0] not in ("props-player", "props-board", "alt-lines")]
    if T["teams"]:
        rows.append(("cfb-teams", ("file", f"{latest}/teams.json"),
                     T["teams"], False, "team logos across every tab"))
    return rows


def contract(data="data", picks="picks", now=None):
    # 🔴 THE LEAGUE COMES FROM THE PATH, so no caller changes. `collect.py`
    # already passes its league-scoped DATA (`data`, `data/nfl`,
    # `data/ncaaf`), which means converge, the freshness report and
    # verify_freshness all become league-aware for free.
    _lg = data.rstrip("/").split("/")[-1]
    if _lg in FB_TIMES:
        return _football_contract(_lg, data, picks, now)
    latest = f"{data}/latest"
    day = et_date(now)
    utc_day = (now or datetime.datetime.now(UTC)).strftime("%Y-%m-%d")
    rows = [
        # mode              probe                                  due       paid  tab / why
        # ── 6:00am — grade last night, then rebuild what grading feeds
        ("scores",   ("file", f"{latest}/scores.json.gz"),         GRADING, False,
         "Track Record — last night's finals; self-healing, walks every missing date"),
        ("results",  ("file", f"{data}/{slate_date(now)}/results/final.json.gz"), GRADING, False,
         "Track Record — the finished slate the grader reads"),
        ("pitchers", ("file", f"{latest}/pitchers.json.gz"),       GRADING, False,
         "Trends — pitcher game logs, every model input"),
        # 🔴 `[2026-09-22]` the published pitcher and opponent tables.
        #    Same writer (`collect.py` pitchers mode chains `mlb_tables`),
        #    same deadline. ⚠️ A table failure is caught so it cannot lose
        #    the pull -- THESE rows are what make that failure loud.
        ("pitchers", ("file", f"{latest}/pitcher-table.json"),     GRADING, False,
         "MLB pitcher table — rebuilt from the pitcher logs"),
        ("pitchers", ("file", f"{latest}/opponent-table.json"),    GRADING, False,
         "MLB opponent table — rebuilt from the pitcher logs"),
        ("hitters",  ("file", f"{latest}/hitters.json.gz"),        GRADING, False,
         "Trends — hitter game logs"),
        ("record",   ("file", f"{latest}/record.json"),            GRADING, False,
         "Track Record — the graded record itself"),
        # 🔴 `[2026-09-22, MLB unfrozen]` the drill-down the Track Record
        #    tab opens. Same writer (`collect.py` record mode), same deadline.
        ("record",   ("file", f"{latest}/record-detail.json.gz"),  GRADING, False,
         "Track Record — the per-pick drill-down"),
        # ── 7:00am and 4:00pm — the paid pulls
        ("gamelines", ("file", f"{latest}/board.json"),            ODDS, True,
         "Odds + Scores & Matchups — moneylines, spreads, totals"),
        *props_rows("mlb", data, utc_day),           # props-pitcher, props-batter
        ("props-board", ("file", f"{latest}/props.json.gz"),       ODDS, False,
         "Player Props — the join that puts props on the board"),
        # 🔴 `[Sam, 2026-10-06]` THE GAME LINES TAB'S MODEL, ON ITS OWN DEADLINES.
        #    ~~built only inside the card~~ (one deadline a day): after a
        #    deploy nothing built it, and a starter named after 10:00 ET read
        #    "No pick yet" all day. Free; dropped on a no-games day below.
        ("game-model", ("file", f"{latest}/mlb-game-model.json"), ODDS, False,
         "Game Lines — the MLB game model's pick to win each game"),
        # ── 10:00am — the card
        ("lineups",  ("file", f"{latest}/lineups.json.gz"),        CARD, False,
         "Gizmo's Picks — confirmed lineups the card needs"),
        ("weather",  ("file", f"{latest}/weather.json.gz"),        CARD, False,
         "Gizmo's Picks — game-time conditions"),
        # 🔴 `due_date(CARD)`, NOT `day`. See due_date's docstring: the
        # wall clock rolls at midnight ET, the 10:00 deadline does not.
        ("card",     ("file", f"{picks}/{due_date(CARD, now)}.json"), CARD, False,
         "Gizmo's Picks + Parlays"),
        # ── unchanged
        ("news",     ("file", f"{latest}/news.json"),              NEWS, False,
         "News"),
    ] + runs_rows(latest)
    # 🔴 `[2026-09-29]` A DAY WITH NO MLB GAMES OWES NO CARD AND NO RESULTS.
    #    Each row is judged on ITS OWN date (the card's governing deadline,
    #    the results' slate), and only when every schedule reading for that
    #    date says 0 games -- fail closed otherwise (`no_games_day`).
    if no_games_day(due_date(CARD, now), data):
        rows = [r for r in rows if r[0] != "card"]
    # `[Sam, 2026-10-06]` the game model by the same rule, on its own deadline's day.
    if no_games_day(due_date(ODDS, now), data):
        rows = [r for r in rows if r[0] != "game-model"]
    if no_games_day(slate_date(now), data):
        # 🔴 `[Sam, 2026-10-02]` ...BUT `results` IS JUDGED ON THE SLATE IT
        #    GRADES. 10-02 had no games, the row went, and nothing re-pulled
        #    10-01, stored 14 hours before first pitch and never settled: 29
        #    picks off the Track Record. Owed while the previous slate had
        #    games (fail closed) and is not settled, probing THAT file.
        prev = (datetime.date.fromisoformat(slate_date(now))
                - datetime.timedelta(days=1)).isoformat()
        if no_games_day(prev, data) or results_settled(prev, data):
            rows = [r for r in rows if r[0] != "results"]
        else:
            rows = [r if r[0] != "results" else
                    ("results", ("file", f"{data}/{prev}/results/final.json.gz"), GRADING,
                     False, "Track Record — the previous slate, not settled yet")
                    for r in rows]
    return rows


# ══════════════════════════════════════════════════════════════════════
# 🔴 RUN STATUS — `data/latest/runs.json`. `[2026-09-25]`
# Sam: "Nobody can read run status reliably from outside GitHub." The
# hourly runs watcher (`runs.yml`, 41 past every hour UTC) writes the last
# 48h of every workflow through `collect.py runs`.
# ⚠️ AN HOURLY FILE GETS A MAXIMUM AGE, NOT AN HOURLY DEADLINE. GitHub
#    drops scheduled runs (29 of 70 hour-slots landed, 2026-08-26); an
#    hourly deadline would flap the watchdog's issue every time one did.
#    `LATE_GRACE_MIN` moves the deadline back: the row is stale only when
#    the newest file is older than the last top of the hour minus 100
#    minutes — TWO consecutive watcher runs missing, not one.
#    ⚠️ DERIVED, NOT PICKED: a run lands 44-58 minutes past the hour. One
#    miss must stay fresh (grace >= 120 - 44 = 76); two misses must go
#    stale (grace < 180 - 58 = 122). ~~150~~ was my first number and it
#    only fired after THREE misses — caught by test_runs_status.py §4.
# ⛔ NOT A TAB. `OFF_PAGE` keeps it off the reader's stale banner; it is
#    SOFT (a late run list misleads no bettor), so it reaches Sam through
#    the watchdog's issue, never through a red collect run.
# ⛔ AND IT EXISTS ONLY ONCE THE WATCHER WRITES IT. Until Sam uploads the
#    staged runs.yml (docs/upload/UPLOAD-runs.md) no job writes the file,
#    and a row would be red on a correct system — CLAUDE.md, "no red
#    window". The row switches itself on with the deployed workflow.
# ══════════════════════════════════════════════════════════════════════
RUNS_DUE = [(h, 0) for h in range(24)]
LATE_GRACE_MIN = {"runs": 100}
OFF_PAGE = {"runs"}
RUNS_WRITER = "python collect.py runs"
# ⛔ `[2026-10-07]` Rows another workflow builds: no collect run ever does, so
#    their age cannot say a league stopped (watchdog.check_stopped_league).
BUILT_ELSEWHERE = {"runs": "runs.yml"}


def runs_writer_deployed(root=None):
    """Does the DEPLOYED runs.yml run the writer? Read, never assumed."""
    root = root or os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(root, ".github", "workflows", "runs.yml"),
                  encoding="utf-8") as fh:
            return any(RUNS_WRITER in l and not l.lstrip().startswith("#")
                       for l in fh)
    except OSError:
        return False


def runs_rows(latest, root=None):
    if not runs_writer_deployed(root):
        return []
    return [("runs", ("file", f"{latest}/runs.json"), RUNS_DUE, False,
             "Run status — every workflow's last 48h (runs.yml, hourly)")]


# 🔴 SOFT ARTIFACTS — late, or failing, must not take the site down.
# ⛔ Converge made every mode's failure everyone's failure: before this,
# one dead news RSS feed turned the whole run red and, under the old
# workflow, could stop the commit. These three are things a reader can
# lose without being misled -- headlines, conditions, lineups. Odds, the
# card and the track record are NOT here and never should be: those are
# numbers someone bets on.
# ⚠️ THE NEWS ARCHIVE SHARES `news`'s FATE, AND THAT IS WHY IT IS SOFT.
#    Both are written by the same code path: when every RSS feed fails,
#    `collect_news` raises before either is written. ⛔ Making the archive
#    HARD would turn a third-party outage back into a red run — which is
#    the precise regression this set was created to stop, and which this
#    project has already lived through once.
#    ✅ Its contract row names its writer, `news`, so `news` here is what
#    keeps it soft. The separate `news-archive` entry named a mode no arm
#    of `run_mode` runs, and is gone with the row's old name
#    (`test_contract_modes.py` fails on an entry here that names no mode).
# 🔴 THE CONDITION THAT IS A REAL FAILURE IS **DIVERGENCE**, not absence:
#    `latest/news.json` fresh while the day's archive is empty means the
#    archive silently stopped. A staleness deadline cannot express "fresh
#    but only one of the two", so the CODE that decides divergence is
#    asserted as a CHECK (`test_news_archive.py`) rather than pretended
#    into a contract row. ~~asserted as a CHECK~~ on the live tree — struck
#    `[2026-09-28]`: that made the suite's verdict a fact about production
#    that day. The check now runs on planted trees pinned to the real
#    clock, and what the live tree shows is a note; in production this is
#    watched only by the soft dated-archive row. ⚠️ A hard production
#    alarm for divergence would be a contract change: Sam's call.
#    ⛔ Soft here is not quiet: the gate prints `::warning::` and the row
#    reads STALE.
SOFT = {"news", "weather", "lineups", "cfb-teams", "runs"}
# `[Sam, 2026-10-17]` THE COLLEGE INJURY READER (cfb_injuries.py). What a reader
#    loses when it fails is one why sentence about an opponent's injuries,
#    never a number they bet on: the card, its odds and its record stay hard.
#    `cfb_injuries.run` never raises; SOFT covers the rest (its import, the
#    arm), so a failed read is a `::warning::` and the pass goes on to the card.
SOFT |= {"cfb-injuries"}
# 🔴 STORED-ONLY DATA `[Sam, 2026-10-14]`: files no tab or model reads yet
#    (NWS forecasts, injuries, CFBD advanced stats / venues / weather). A stale
#    one is a `::warning::` (soft) and ⛔ NEVER PLANS A RUN: its writer is a
#    daily CFBD / nflverse mode, and re-running cfb-probe every pass for a file
#    nothing reads is how September's CFBD quota went (13+ calls a build).
#    `[Sam, 2026-10-17]` and college injuries' stored files (design §1): CFBD's
#    roster jerseys and defensive box score, the conference archives, and the
#    dated report snapshots. ⛔ NOT the reader's probe (`injuries-probe-<s>`):
#    that row exists to plan the reader.
STORED_ONLY = re.compile(r"/(weather|injuries|adv|venues|cfbd-weather|roster|defense)-\d{4}\.json\.gz$"
                         r"|/history/injury-archive-\d{4}\.json\.gz$"
                         r"|/\d{4}-\d{2}-\d{2}/injury-reports(/\d{4}\.json\.gz)?$"
                         r"|/history/(schedule|lines)-\d{4}\.json\.gz$")


def stored_only(r):
    """⛔ Not once a CHAMPION reads it (T68's WX): then it is an input like E's."""
    return bool(STORED_ONLY.search(r.get("path") or "")) and r.get("why") != CHAMPION_INPUT


CHAMPION_INPUT = "Game model champion's input"

# ══════════════════════════════════════════════════════════════════════
# 🔴 A FILE WRITTEN ON TIME CAN STILL BE A FILE THAT SAYS NOTHING NEW.
#    `[2026-10-17]` (college injuries, review of part P3)
# ══════════════════════════════════════════════════════════════════════
# The college injury reader writes its probe on EVERY attempt, so its row went
# fresh on a pass where every source failed, and nothing in the repo read the
# probe: a blocked HDI would have taken every injury line out of the college
# whys for weeks, with no alarm. ✅ `health(path, now)` asks what the CONTENT
# says. A reason makes the row stale (`survey`), with `late_min` left alone
# (it was built on time; nothing was late), so converge plans its writer
# again, the gate warns, freshness.json carries the reason and the watchdog's
# `fresh:` finding (DEGRADED) reaches health.json and the weekly status.
# ⛔ Only for the files named in HEALTH, and each judges a fact its writer
#    controls, never the age of a file written only on a change.
# ⛔ What it judges, it judges only while the season makes it matter, so the
#    off-season and a quiet week are never a warning nobody can clear.
# Read by `survey`; every row without a check reads None.
#
# The reader's limits, PARSED from cfb_injuries.py (⛔ one copy; never
# imported, the `_literal` rule), cached until the file changes.
_INJ_LIMITS = {}
# A box score reaches the next daily `cfb-probe` build (07:04Z, and Sunday
# 14:35Z); 48 hours is two daily builds, so ONE dropped or late run is not a
# warning and two in a row are.
DEFENSE_LAG_H = 48
# "The season is on" for the archives: a final FBS game in the last 8 days (a
# week of games and a day).
IN_SEASON_D = 8


def _injury_limits():
    """-> (FETCH_MAX_AGE_H, MAX_AGE_H, ARCHIVE_REFRESH_H, LEGACY_SEASON) from
    cfb_injuries.py, or None when the file or a name is missing."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cfb_injuries.py")
    try:
        st = os.stat(p)
    except OSError:
        return None
    key = (st.st_mtime_ns, st.st_size)
    if _INJ_LIMITS.get("key") != key:
        try:
            vals = tuple(_literal("cfb_injuries.py", n) for n in
                         ("FETCH_MAX_AGE_H", "MAX_AGE_H", "ARCHIVE_REFRESH_H", "LEGACY_SEASON"))
        except Exception:
            vals = None
        _INJ_LIMITS.clear()
        _INJ_LIMITS.update(key=key, vals=vals)
    return _INJ_LIMITS["vals"]


def _hours(td):
    return td.total_seconds() / 3600.0


def _injury_probe_health(path, now):
    """The college injury reader's probe (cfb_injuries._write_probe).
    🔴 LIVE SOURCES, while an FBS game kicks off within MAX_AGE_H (a report is
       shown only then): each source the probe lists must have been confirmed
       (`last_ok_at`) within FETCH_MAX_AGE_H, the age past which
       `cfb_injuries.report_for` stops showing its reports (design §2 (b)). So
       a source down this long has already taken its reports off the page.
    🔴 THE CURRENT SEASON'S ARCHIVES, while the season is on: a conference
       that answered before must have been refreshed within 2 x
       ARCHIVE_REFRESH_H (the reader refreshes once a day). ⛔ One that never
       answered is in the probe and is not judged: no clearable warning says
       "this conference has no archive".
    ⛔ No readable schedule is CANNOT TELL, and cannot-tell keeps both judged."""
    doc = _load(path)
    lim = _injury_limits()
    if not isinstance(doc, dict) or lim is None:
        return None                       # a missing probe already reads MISSING
    fetch_h, age_h, arch_h, legacy = lim
    season = doc.get("season")
    games = kickoff_games("ncaaf", os.path.join(os.path.dirname(path),
                                                f"schedule-{season}.json.gz"))
    bad = []
    if games is None or any(now < k <= now + datetime.timedelta(hours=age_h) for k, _g in games):
        src = doc.get("sources") if isinstance(doc.get("sources"), dict) else {}
        if not src:
            bad.append("no source was read (%s)" % (doc.get("error") or "the probe lists none"))
        for s, v in sorted(src.items()):
            ok = _parse(v.get("last_ok_at")) if isinstance(v, dict) else None
            if ok is None:
                bad.append(f"{s} has never been read")
            elif now - ok > datetime.timedelta(hours=fetch_h):
                bad.append(f"{s} not read for {_hours(now - ok):.0f}h")
    if str(season) != str(legacy) and (games is None or any(
            g.get("final") and now - datetime.timedelta(days=IN_SEASON_D) <= k <= now
            for k, g in games)):
        arch = doc.get("archives") if isinstance(doc.get("archives"), dict) else {}
        if arch.get("error"):
            bad.append("the archive step failed (%s)" % str(arch["error"])[:120])
        cur = arch.get(str(season)) if isinstance(arch.get(str(season)), dict) else {}
        for conf, v in sorted(cur.items()):
            c = _parse(v.get("checked_at")) if isinstance(v, dict) else None
            if c is not None and now - c > datetime.timedelta(hours=2 * arch_h):
                bad.append(f"the {season} {conf} archive not refreshed for {_hours(now - c):.0f}h")
    return ("college injury reports: " + "; ".join(bad)) if bad else None


def _defense_health(path, now):
    """CFBD's defensive box score (cfb.store_kept, written only on a change).
    🔴 Last written before the kickoff of the newest final FBS game that kicked
       off over DEFENSE_LAG_H ago: that game's box scores have not reached it,
       so the build that writes it has stopped (a failed /games/players week
       builds no defense doc at all). ⛔ The file's AGE is never the question:
       the off-season and a week between games ask nothing. No readable
       schedule leaves the row to its own deadline (missing only)."""
    built = stamp_of(path)
    m = re.search(r"defense-(\d{4})\.json\.gz$", path.replace(os.sep, "/"))
    if built is None or not m:
        return None
    games = kickoff_games("ncaaf", os.path.join(os.path.dirname(path),
                                                f"schedule-{m.group(1)}.json.gz")) or []
    edge = now - datetime.timedelta(hours=DEFENSE_LAG_H)
    due = max((k for k, g in games if g.get("final") and k <= edge), default=None)
    if due is not None and built < due:
        return (f"last written {built:%a %d %b %H:%MZ}, before the newest final FBS game it should "
                f"hold (kickoff {due:%a %d %b %H:%MZ}, over {DEFENSE_LAG_H}h ago): CFBD's box "
                f"scores have stopped reaching it")
    return None


HEALTH = ((re.compile(r"/ncaaf/latest/injuries-probe-\d{4}\.json$"), _injury_probe_health),
          (re.compile(r"/ncaaf/latest/defense-\d{4}\.json\.gz$"), _defense_health))


def health(path, now=None):
    """-> why a file that is on time is still not doing its job, or None.
    ⛔ A check that cannot run says so (visible, soft), never a silent None."""
    p = "/" + str(path).replace(os.sep, "/").lstrip("/")
    for rx, fn in HEALTH:
        if rx.search(p):
            try:
                return fn(path, now or datetime.datetime.now(UTC))
            except Exception as e:
                return f"its health check could not run ({type(e).__name__}: {str(e)[:120]})"
    return None

# ══════════════════════════════════════════════════════════════════════
# 🔴 A THIRD-PARTY SOURCE THAT WILL NOT SERVE US IS A KNOWN STATE.
# ══════════════════════════════════════════════════════════════════════
# `[2026-09-09 — Sam: "i keep getting emails saying the collect run is
# failing"]` **Every college run and every NFL run was red, on a loop.**
# Two causes, neither of them a defect in this repo:
#
#   ncaaf   CFBD answered 429 on every endpoint from 09-06. Its quota was
#           spent. Sam has already upgraded the key — there is nothing
#           further for anyone to do until the tier takes effect.
#   nfl     nflverse has **not published `stats_player_week_2026`** —
#           "that release holds 542 assets; those mentioning 2026: NONE".
#           The NFL season opened 2026-09-09. There is no week-1 data
#           because week 1 has not been played.
#
# ⛔ THIS FILE ALREADY MADE THIS ARGUMENT ONCE AND WON IT. See
# `CARD_REFUSED_GRACE_MIN` and `verify_freshness.py`: *"22 consecutive
# red runs for a decision that had already been made and recorded — AN
# ALARM THAT FIRES EVERY FIFTEEN MINUTES GETS IGNORED, AND IGNORING RED
# IS EXACTLY HOW THE ORIGINAL STALENESS SURVIVED A WHOLE DAY."*
# ✅ So this is not a new policy. It is the SAME policy, applied to the
# two other states this project can recognise, with the same shape:
# **downgrade to a warning, and BOUND IT** so a known state can never
# become permanent silence.
#
# ⚠️ THE EVIDENCE IS ALREADY ON DISK AND IS NOT WRITTEN BY THIS CODE —
# `backfill-report.txt` is produced by the builder itself and already
# separates the two: `failed   : [2026]` (the source refused) from
# `not yet  : [2026]   (season not started — not a failure)`.
# ⛔ Only a row that is BOTH stale AND explained is downgraded. A stale
# artifact with no recorded source problem still fails the run, exactly
# as before.
# ⚠️ SEVEN DAYS, and the number is argued rather than picked. A blown
# monthly quota can last until the 1st, so a short grace would spend most
# of an outage screaming at somebody who has already acted. A week is long
# enough to cover an upgrade taking effect and short enough that "we are
# waiting" turns back into "decide something" while the season is still on.
SOURCE_REFUSED_GRACE_MIN = int(
    os.environ.get("SOURCE_REFUSED_GRACE_MIN", str(7 * 24 * 60)))
# ⚠️ LONGER, because "the season has not started" resolves on the
# SPORT'S clock, not ours. nflverse publishes week 1 after week 1 is
# played. ⛔ But still bounded: if a fortnight of a season has gone by
# and the source still has nothing, that IS news.
SOURCE_NOT_YET_GRACE_MIN = int(
    os.environ.get("SOURCE_NOT_YET_GRACE_MIN", str(14 * 24 * 60)))

# Which artifacts come from a metered/third-party back-fill, and so can
# legitimately be blocked by it. ⛔ Keep this SMALL and explicit.
SOURCE_BACKED = {"cfb-probe", "nfl-logs", "fb-scores"}


def source_block(data="data", now=None):
    """What the league's own back-fill report says about its SOURCE.

    Returns `{"state": "refused"|"not_yet"|None, "detail", "age_min"}`.
    ⛔ READS THE REPORT THE BUILDER ALREADY WRITES. A second place to
    record "is the source up" would drift out of agreement with the
    first, which is the same argument that put `fb-scores` behind
    `cfb-probe`'s back-off rather than giving it its own.
    ⚠️ Unreadable or absent -> no block. An unknown must never excuse a
    stale artifact.
    """
    try:
        with open(f"{data}/latest/backfill-report.txt", encoding="utf-8") as fh:
            txt = fh.read()
    except Exception:
        return {"state": None, "detail": None, "age_min": None}

    def _listed(label):
        m = re.search(label + r"\s*:\s*\[([^\]]*)\]", txt)
        return bool(m and m.group(1).strip())

    when = None
    m = re.search(r"back-fill at ([0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9:.]+)", txt)
    if m:
        try:
            when = datetime.datetime.fromisoformat(m.group(1).replace(" ", "T"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=UTC)
        except Exception:
            when = None
    age = None
    if when is not None:
        age = ((now or datetime.datetime.now(UTC)) - when).total_seconds() / 60.0

    # 🔴 ORDER MATTERS. A report can say both; a REFUSAL is the stronger
    # claim and the one with a status code behind it.
    if _listed("failed"):
        # ══════════════════════════════════════════════════════════════
        # 🔴 "FAILED" IS NOT THE SAME AS "THE SOURCE REFUSED US", AND
        #    TREATING IT AS SUCH WOULD HAVE HIDDEN A REAL BUG FOR A WEEK.
        # `[caught 2026-09-10, before this ever shipped]` The very first
        # report this was pointed at read:
        #     failed   : [2026]
        #     RuntimeError: depth_rank is CONSTANT None across 1,848 rows
        # — **our own build refusing its own output**, with CFBD healthy
        # and `endpoints_failed: []`. The first draft of this function
        # called that "the source refused us" and would have downgraded
        # it to a warning for seven days.
        # ⛔ SO A REFUSAL NEEDS POSITIVE EVIDENCE FROM THE SOURCE: an HTTP
        #    status, or the typed `SourceUnavailable` the fetch layer
        #    raises. Anything else in `failed:` is OURS and stays hard.
        # ⚠️ This is the whole reason the downgrade is safe. A grace that
        #    can be claimed by any exception is not a grace, it is a mute
        #    button.
        # ══════════════════════════════════════════════════════════════
        code = re.search(r"HTTPError (\d{3})", txt)
        if code or "SourceUnavailable" in txt:
            return {"state": "refused", "age_min": age,
                    "detail": ("the source refused us"
                               + (f" (HTTP {code.group(1)})" if code else ""))}
        return {"state": None, "age_min": age,
                "detail": ("the back-fill failed, but NOT because the "
                           "source refused — this is ours and stays red")}
    if _listed("not yet"):
        why = re.search(r"not published\.[^\n]*", txt)
        return {"state": "not_yet", "age_min": age,
                "detail": ("the source has not published this season yet"
                           + (f" — {why.group(0)[:120]}" if why else ""))}
    return {"state": None, "detail": None, "age_min": None}


# ══════════════════════════════════════════════════════════════════════
# 🔴 A DEADLINE THAT PASSES AFTER THE PASS LOOKED IS THE NEXT PASS'S.
#    `[2026-10-24]`
# ══════════════════════════════════════════════════════════════════════
# collect 39271299253, 10-19: the NFL pass surveyed at 14:58:21Z, bought the
# 7am props (238 minutes late) at 14:58Z, wrote freshness.json at 14:59:59Z
# with every props row inside contract, and pushed. The gate ran at
# 15:00:01.9Z and failed "props-player MISSED its 7:00/11:00 ET build: last
# built 2m ago": the 11am deadline had passed 1.9 seconds earlier (no "past
# due", because 0.03 minutes printed as nothing). No pass could have met it,
# because no pass had looked since it passed.
# ✅ SO THE GATE ASKS THE PRECISE QUESTION: did the league's last survey leave
#    anything out of contract? A stale row is the NEXT pass's, not a miss, only
#    when ALL of these hold:
#      - this league's freshness.json (the converge pass's own final survey)
#        is readable, stamped, and not later than now;
#      - that survey recorded this row (same mode and path) inside contract;
#      - exactly ONE of the row's deadlines has passed since that survey;
#      - the row is late, not missing and not unhealthy.
#    The gate prints it as a ::warning:: naming the deadline and the survey.
# ⛔ NOTHING ELSE MOVES: a row the survey saw stale, a deadline the pass had
#    surveyed past, two deadlines since the survey, an unreadable
#    freshness.json are all red as before. The next pass surveys after the
#    deadline, so it is judged strictly, and its build is recorded in
#    lateness.json like any other.
def after_last_survey(rows, data="data", picks="picks", now=None):
    """-> {(mode, path): (survey time, deadline)} for the stale rows whose only
    missed deadline passed after the league's last recorded survey, which found
    them inside contract. {} when that survey cannot be read."""
    now = now or datetime.datetime.now(UTC)
    path = f"{data}/latest/freshness.json"
    look = stamp_of(path)
    doc = _load(path)
    if look is None or look > now or not isinstance(doc, dict):
        return {}
    seen = {(a.get("mode"), a.get("path")): a for a in (doc.get("artifacts") or [])
            if isinstance(a, dict)}
    times = {(m, p): t for m, (_k, p), t, _paid, _why in contract(data, picks, now)}
    out = {}
    for r in rows:
        key = (r["mode"], r["path"])
        rec, t = seen.get(key), times.get(key)
        if (not r["stale"] or r["missing"] or r.get("unhealthy") or not r.get("due_at")
                or not rec or rec.get("stale") is not False or not t):
            continue
        first = next_due(t, look)
        if first is not None and first.strftime("%Y-%m-%dT%H:%MZ") == r["due_at"]:
            out[key] = (look, first)
    return out


def classify(rows, data="data", refused=None, block=None, now=None):
    """The freshness gate's verdict on every STALE row -> (hard, soft).

    ⛔ ONE COPY. `verify_freshness.py` (the gate) and `collect.converge`
    (is a failed mode worth a red run?) both call this; the reasons for
    each branch are argued in verify_freshness.main.
    `refused`: the card was refused by verify_card (a known state).
    `block`: `source_block(data)` (a third-party source that will not serve).
    `now`: when `rows` were surveyed (`after_last_survey`).
    """
    if refused is None:
        refused = os.path.exists(f"{data}/latest/card-verify-failure.txt")
    if block is None:
        block = source_block(data)
    later = None
    hard, soft = [], []
    for r in rows:
        if not r["stale"]:
            continue
        if stored_only(r):
            soft.append(r)
            continue
        if (r["mode"] in SOURCE_BACKED and block["state"]
                and not r["missing"]):
            _grace = (SOURCE_REFUSED_GRACE_MIN if block["state"] == "refused"
                      else SOURCE_NOT_YET_GRACE_MIN)
            _age = r["age_min"]
            if _age is not None and _age <= _grace:
                soft.append(dict(r, _blocked=block, _grace=_grace))
                continue
            # 🔴 PAST THE GRACE IT IS NOT "WAITING" ANY MORE.
            hard.append(dict(r, _blocked=block, _grace=_grace, _stuck=True))
            continue
        if r["mode"] == "card" and refused:
            # 🔴 BOUNDED. A refusal is a KNOWN state for as long as somebody
            # is still acting on it. Past the grace it is a FROZEN BOARD,
            # and a frozen board with a green build is the worst state this
            # project has ever shipped. ⚠️ The card's own age is the signal:
            # `card-verify-failure.txt` is rewritten every pass and can only
            # say when the LAST refusal was, never the first.
            _age = r["age_min"]
            if r["missing"] or (_age is not None
                                and _age > CARD_REFUSED_GRACE_MIN):
                r = dict(r, _frozen=True)
                hard.append(r)
                continue
            soft.append(r)
            continue
        if r["mode"] not in SOFT:
            later = after_last_survey(rows, data, now=now) if later is None else later
            if (r["mode"], r["path"]) in later:
                soft.append(dict(r, _after_survey=later[(r["mode"], r["path"])]))
                continue
        (soft if r["mode"] in SOFT else hard).append(r)
    return hard, soft


def outside_source(exc):
    """Is this exception POSITIVE EVIDENCE that an outside source failed?
    -> a short description of that evidence, or None.

    ⛔ THE SAME RULE AS `source_block`: a refusal needs evidence from the
    source. A network or HTTP error, a timeout, a dropped connection, or
    the typed `SourceUnavailable` the fetch layer raises. Anything else --
    a TypeError, a KeyError, a RuntimeError our own build raises about its
    own output -- is OURS, and a grace any exception could claim "is not a
    grace, it is a mute button". The cause chain is read, so a fetch error
    re-raised inside our own wrapper still counts.
    `[measured 2026-09-26]` all seven football pass failures in the 48h
    before this were `TypeError: '<' not supported between instances of
    'dict' and 'int'` from props-board -- our code, while the annotation
    blamed the mode the cron had launched.
    """
    import http.client
    import ssl
    import urllib.error
    seen = 0
    while exc is not None and seen < 6:
        if isinstance(exc, urllib.error.HTTPError):
            return f"HTTP {exc.code} from the source"
        if isinstance(exc, (urllib.error.URLError, TimeoutError, ConnectionError,
                            http.client.HTTPException, ssl.SSLError)):
            return f"{type(exc).__name__} reaching the source"
        if type(exc).__name__ == "SourceUnavailable":
            return "the source refused us (SourceUnavailable)"
        exc = exc.__cause__ or exc.__context__
        seen += 1
    return None


def judge_failures(failed, rows, data="data"):
    """Which failed modes turn the run red? -> (red, warned).

    `[Sam, 2026-09-26]` "A single failed converge pass for an outside
    source ... turns the whole collect run red even when every artifact
    is still inside its freshness deadline." ✅ THE CONTRACT IS THE JUDGE
    of staleness, by the gate's own `classify`. A failure is a WARNING,
    naming its source, only when BOTH hold:
      - every artifact the mode writes is inside contract (or excused by
        the gate as a known state), and
      - the error is evidence that an OUTSIDE SOURCE failed
        (`outside_source`), not our own code.
    Everything else stays RED: an artifact left stale or missing, a mode no
    contract row can judge (fail closed), and every failure of our own code
    -- which the contract cannot see when the artifact was written before
    the crash (props-board, 2026-09-24/25).
    `failed`: converge's list of (mode, why, source-evidence-or-None).
    Each result is (mode, why, rows, verdict).
    ⛔ This decides the RUN's colour only. The failure is still logged, and
    the gate (`verify_freshness.py`) still fails the run the moment an
    artifact goes past due, whoever let it.
    """
    hard, _soft = classify(rows, data)
    hard_by = {}
    for r in hard:
        hard_by.setdefault(r["mode"], []).append(r)
    red, warned = [], []
    for mode, why, source in failed:
        own = [r for r in rows if r["mode"] == mode]
        if not own:
            red.append((mode, why, [], "no freshness row judges this mode"))
        elif mode in hard_by:
            red.append((mode, why, hard_by[mode], "it left an artifact out of contract"))
        elif not source:
            red.append((mode, why, own, "a failure in our own code, not an outside "
                        "source -- the contract cannot excuse a defect"))
        elif not any(r["stale"] for r in own):
            warned.append((mode, why, own, f"{source}, and every artifact it "
                           f"writes is inside its deadline"))
        else:
            # stale, but the gate itself excuses it (a source outage inside
            # its grace, or a refused card): the gate decides when it turns
            # red, and says so every pass
            warned.append((mode, why, own, f"{source}; its artifact is past due "
                           f"but the freshness gate excuses it as a known state"))
    return red, warned


# 🔴 CASCADES. Refreshing an input INVALIDATES what was derived from it.
# Without this a pass could pull brand-new props and still serve a card
# priced off the old ones -- ledger rule 66 arriving by a different door.
# ⚠️ Note gamelines/props do NOT cascade to the card here: the card is a
# 10am artifact by Sam's schedule, and the 4pm odds pull must not quietly
# rebuild it. The 10am card is the 10am card.
CASCADE = {
    "props-pitcher": ["props-board"],
    "props-batter":  ["props-board"],
    "gamelines":     ["props-board"],
    "results":       ["record"],
    "scores":        ["record"],
}


def survey(data="data", picks="picks", now=None, entries=None):
    """Age every artifact against its deadline. Pure -- no side effects.

    `entries`: contract rows to judge instead of the whole contract (`pull_owed`
    judges one paid pull this way, through this same loop)."""
    now = now or datetime.datetime.now(UTC)
    rows = []
    for mode, (kind, path), times, paid, why in (
            contract(data, picks, now) if entries is None else entries):
        age = (newest_age_minutes(path, now) if kind == "dir"
               else age_minutes(path, now))
        built = None if age >= MISSING else now - datetime.timedelta(minutes=age)
        due = last_due(times, now)
        if due is not None and mode in LATE_GRACE_MIN:
            due -= datetime.timedelta(minutes=LATE_GRACE_MIN[mode])
        stale = built is None or (due is not None and built < due)
        late = stale
        # `[2026-10-17]` ON TIME BUT SAYING NOTHING NEW (`health`): stale, with
        # its reason, and never LATE (it was built after its deadline).
        sick = None if late or kind != "file" else health(path, now)
        stale = late or bool(sick)
        rows.append({
            "mode": mode, "path": path, "kind": kind, "why": why,
            "age_min": None if age >= MISSING else round(age, 1),
            "due_at": None if due is None else due.strftime("%Y-%m-%dT%H:%MZ"),
            # ⚠️ A deadline may carry the days it applies on. The label
            # says so, because "12:00" and "Mon 12:00" are different
            # promises and a reader is entitled to know which.
            "due_et": "/".join(
                (f"{t[0]}:{t[1]:02d}" if len(t) < 3 else
                 f"{'/'.join(_DOW[d] for d in sorted(t[2]))} {t[0]}:{t[1]:02d}")
                for t in times),
            "late_min": (None if (built is None or due is None or not late)
                         else round((now - due).total_seconds() / 60.0, 1)),
            "paid": paid, "stale": stale, "missing": age >= MISSING,
            "unhealthy": sick,
            # ⛔ a row no tab reads stays off the reader's stale banner
            "page": mode not in OFF_PAGE,
        })
    return rows


# ══════════════════════════════════════════════════════════════════════
# 🔴 LATENESS LEAVES A RECORD (the audit's rule 301). `[Sam, 2026-10-06]`
# ══════════════════════════════════════════════════════════════════════
# The MLB card was due 14:00Z on 10-06 and built 16:02Z, and nothing said so:
# the run that built it repaired the staleness before the watchdog looked.
# ✅ Every converge pass writes, for each artifact with a deadline, the FIRST
#    build seen after that deadline: when it was due, when it was built (the
#    artifact's own stamp) and how many minutes late. A later rebuild for the
#    same deadline leaves the record alone (a same-day rebuild must not hide a
#    late card); the next deadline's build replaces it. The watchdog reports
#    DEGRADED (never BROKEN, no repair) while a last build was more than
#    GRACE_MIN late, so it clears on the next on-time build.
# ✅ `[Sam, 2026-10-07]` A build over GRACE_MIN late is also kept 8 days in
#    `late`: the weekly status (status.py) counts the week's, not the latest.
# 🔴 `[Sam, 2026-10-07]` A FIRST SIGHTING IS NOT A MEASUREMENT. An artifact seen
#    for the first time is recorded with its CURRENT stamp: NFL record.json read
#    9100 minutes late `[Cowork replay, 2026-10-07]`. An entry is `measured` only
#    when its artifact already had one; only a measured entry is reported, kept
#    in `late` or counted.
# ⚠️ GRACE_MIN is above one heartbeat sleep (15 min) plus a pass plus a cron's
#    usual 10-15 minute delay; 10-06's card was 122 minutes late.
# ⛔ A row whose deadline is a MAXIMUM AGE (`LATE_GRACE_MIN`: the hourly run
#    list) has no time it was due, so it is not recorded.
GRACE_MIN = 60
LATENESS_FILE = "lateness.json"


def record_builds(rows, path, now=None):
    """Update `path` from a survey's rows. -> the document written."""
    now = now or datetime.datetime.now(UTC)
    try:
        with open(path, encoding="utf-8") as fh:
            prev = json.load(fh)
        arts, late = prev.get("artifacts") or {}, prev.get("late") or []
    except (OSError, ValueError, AttributeError):
        arts, late = {}, []
    for r in rows:
        if (r.get("due_at") is None or r.get("stale") or r.get("age_min") is None
                or r.get("mode") in LATE_GRACE_MIN):
            continue
        key = re.sub(r"\d{4}-\d{2}-\d{2}", "{date}", r["path"])   # picks/{date}.json is ONE artifact
        old = arts.get(key) or {}
        if old.get("due_at") == r["due_at"]:
            continue                       # the first build for this deadline stands
        due = datetime.datetime.strptime(r["due_at"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)
        built = now - datetime.timedelta(minutes=r["age_min"])
        arts[key] = {"mode": r["mode"], "path": r["path"], "due_at": r["due_at"],
                           "built_at": built.strftime("%Y-%m-%dT%H:%MZ"),
                           "late_min": round(max(0.0, (built - due).total_seconds() / 60.0), 1),
                           "measured": bool(old)}
        if arts[key]["measured"] and arts[key]["late_min"] > GRACE_MIN:
            late.append(arts[key])
    week = (now - datetime.timedelta(days=8)).strftime("%Y-%m-%dT%H:%MZ")
    doc = {"written_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "grace_min": GRACE_MIN,
           "artifacts": arts, "late": [x for x in late if str(x.get("due_at")) >= week]}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    return doc


def _kickoffs_in(path, keys):
    try:
        d = json.load(gzip.open(path, "rt") if path.endswith(".gz") else open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for x in (y for k in keys for y in (d.get(k) or [])):
        try:
            out.append(datetime.datetime.strptime(x.get("commence") or "", "%Y-%m-%dT%H:%M:%SZ")
                       .replace(tzinfo=UTC))
        except ValueError:
            pass
    return out


def slate_moves(data="data", picks="picks", now=None):
    """`[Sam, 2026-10-09]` A FINISHED SLATE IS NEVER THE CURRENT CARD. -> the free
    modes that move the football board and card on: every game they hold has
    started and the odds board has one that has not. ⛔ PLANNED, NEVER MARKED
    STALE: a run that straddles a last kickoff cannot go red over it."""
    lg = data.rstrip("/").split("/")[-1]
    now = now or datetime.datetime.now(UTC)
    if lg not in FB_TIMES or not any(k > now for k in _kickoffs_in(f"{data}/latest/board.json", ("games",))):
        return set()
    return {mode for mode, path, keys in (
        ("props-board", f"{data}/latest/props.json.gz", ("games",)),
        ("card-fb", f"{picks}/fb-{lg}-latest.json", ("picks", "game_lines")))
        if (lambda ks: bool(ks) and max(ks) <= now)(_kickoffs_in(path, keys))}


# 🔴 `[Sam, 2026-10-17]` MODES PLANNED ON EVERY PASS ON THESE ET DAYS (Monday =
#    0, the contract's fixed offset), fresh or not. The college injury reader
#    (research/cfb_injuries_design.md §1 item 2: "converge runs the mode on
#    every college pass"): Wednesday to Saturday, when the reports for the
#    weekend's games are posted and replaced, a pass must read them before the
#    card it builds, not wait for the next hour (`[2026-10-17]` review of P3:
#    on Saturday 10-10 six college passes landed between 17:16Z and 17:55Z, and
#    an hourly row read the reports in the first only). Other days its hourly
#    row plans it.
#    ⛔ PLANNED, NEVER MARKED STALE, like `slate_moves`: a deadline every few
#    minutes would read stale at the end of any pass longer than that, and
#    warn on a reader that had just run. 💰 Free; no key, no Odds credit.
EVERY_PASS = {"ncaaf": {"cfb-injuries": frozenset({2, 3, 4, 5})}}     # Wed-Sat ET


def every_pass(data="data", now=None):
    """The modes `EVERY_PASS` plans for this league today (ET)."""
    lg = data.replace(os.sep, "/").rstrip("/").split("/")[-1]
    day = ((now or datetime.datetime.now(UTC)) - ET_OFFSET).weekday()
    return {m for m, days in (EVERY_PASS.get(lg) or {}).items() if day in days}


def plan(data="data", picks="picks", now=None, allow_paid=True):
    """The ordered list of modes needed to meet every deadline that has
    passed. Order is the contract's order, which is dependency order."""
    rows = survey(data, picks, now)
    # ⛔ ONE MODE, ONE ENTRY, EVEN WHEN IT OWNS TWO ROWS. A mode may
    #    legitimately appear in the contract more than once — `nfl-logs`
    #    writes both the defence-vs-position table and the possession
    #    probe, on different cadences — and without this a run where both
    #    are stale would execute that mode TWICE in one pass. For a free
    #    mode that is wasted minutes; for a paid one it would be wasted
    #    credits. ⚠️ `dict.fromkeys` keeps the contract's order, which is
    #    dependency order and is what the return relies on.
    order = list(dict.fromkeys(r["mode"] for r in rows))
    need = {r["mode"] for r in rows if r["stale"] and not stored_only(r)
            and (allow_paid or not r["paid"])} | slate_moves(data, picks, now) \
        | every_pass(data, now)
    changed = True
    while changed:
        changed = False
        for src in list(need):
            for dst in CASCADE.get(src, ()):
                if dst not in need:
                    need.add(dst); changed = True
    return [m for m in order if m in need], rows


# ══════════════════════════════════════════════════════════════════════
# 🔴 A SEASON THAT HAS NOT STARTED IS NOT LATE.
# `[measured 2026-09-01, run #307]` the Tuesday NFL rebuild fired with
# SEASON=CUR, which resolved to 2026, and died:
#     RuntimeError: stats_player: asset 'stats_player_week_2026.csv.gz'
#     not published. That release holds 542 assets; those mentioning
#     2026: NONE
# ⛔ NOTHING WAS BROKEN. The 2026 NFL season had not kicked off, so the
# source had nothing to give. The job went red anyway, and would have
# gone red EVERY TUESDAY until mid-September.
# 🔴 THAT IS THE `budget.py` LESSON IN A DIFFERENT COSTUME: a tool that
# cries wolf is a tool nobody reads, and this project has already lost
# real defects to days of ignored noise.
#
# ⚠️ THE RULE IS NARROW ON PURPOSE. Only the CURRENT season may be
# "not started". ⛔ A missing 2019 is still a hard failure -- somebody
# asked for a season that should exist, and silence there would hide a
# real break. Both halves matter.
#
# ⚠️ AND IT IS NEVER SILENT. The season is reported as NOT YET PUBLISHED
# in the back-fill report and warned in the log. It is a different
# STATUS, not a suppressed error.
# ══════════════════════════════════════════════════════════════════════
# 🔴 THE FOOTBALL HISTORY THE SIGNALS ARE BUILT OVER. `[Sam, 2026-09-23:
#    "History is 2025 and 2026 only. Do not add 2024."]` ⛔ One list, read
#    by both leagues' back-fills — never a second copy in nfl.py or cfb.py.
FOOTBALL_HISTORY = (2025, 2026)


def current_football_season(now=None):
    """The football season currently in progress or most recently played.

    ⚠️ A football season is NAMED FOR THE YEAR IT STARTS, so anything
    before August belongs to the previous year.
    🔴 THIS RULE ALSO LIVES IN `.github/workflows/collect.yml`, which
    resolves SEASON=CUR on the runner in bash. ⛔ TWO COPIES OF ONE RULE
    DRIFT -- `test_freshness.py` pins them to each other by parsing the
    workflow, so a change to either side fails the suite.
    """
    import datetime as _dt
    n = now or _dt.datetime.now(_dt.timezone.utc)
    return n.year - 1 if n.month < 8 else n.year
