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

import json
import gzip
import os
import re
import datetime

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
        "props":  [(8, 30, {1, 2, 3, 4, 5}),             # 8:30am Tue-Sat
                   (15, 0, {1, 2, 3, 4, 5})],            # 3pm   Tue-Sat
        # picks 9:00 + parlays 9:30 (Tue-Sat) + track record Tue 8:00
        "card":   [(9, 0, {1, 2, 3, 4, 5}),
                   (9, 30, {1, 2, 3, 4, 5}),
                   (8, 0, {1})],
        "trends": [(12, 0, {0})],                        # Mon noon
        "news":   [(8, 0)],                              # 8am daily
        "teams":  [(10, 35, {6})],                       # Sun, with the rebuild
    },
    "nfl": {
        "odds":   [(8, 0), (14, 0)],                     # 8am, 2pm daily
        "props":  [(7, 0), (11, 0)],                     # 7am, 11am daily
        # picks 7:30 + 11:30 daily, parlays 9:00 daily, record Tue noon
        "card":   [(7, 30), (9, 0), (11, 30), (12, 0, {1})],
        "trends": [(12, 0, {1})],                        # Tue noon
        "news":   [(8, 0)],
        "teams":  [],                                    # embedded in the page
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
            out.append(t.replace(tzinfo=UTC))
        elif zone is not None:
            out.append(t.replace(tzinfo=zone).astimezone(UTC))
        else:
            out.append(t.replace(tzinfo=UTC) + ET_OFFSET)
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


def _football_contract(league, data, picks, now):
    """The same shape as MLB's, for one football league."""
    latest = f"{data}/latest"
    utc_day = (now or datetime.datetime.now(UTC)).strftime("%Y-%m-%d")
    T = FB_TIMES[league]
    season = current_football_season(now)
    rows = [
        ("gamelines", ("file", f"{latest}/board.json"), T["odds"], True,
         "Odds + Scores & Matchups — the football board"),
        ("props-player", ("dir", f"{data}/{utc_day}/props-player"), T["props"], True,
         "Player Props — the paid pull"),
        ("props-board", ("file", f"{latest}/props.json.gz"), T["props"], False,
         "Player Props — the join that puts props on the board"),
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
        rows = [r for r in rows if r[0] not in ("props-player", "props-board")]
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
    return [
        # mode              probe                                  due       paid  tab / why
        # ── 6:00am — grade last night, then rebuild what grading feeds
        ("scores",   ("file", f"{latest}/scores.json.gz"),         GRADING, False,
         "Track Record — last night's finals; self-healing, walks every missing date"),
        ("results",  ("file", f"{data}/{slate_date(now)}/results/final.json.gz"), GRADING, False,
         "Track Record — the finished slate the grader reads"),
        ("pitchers", ("file", f"{latest}/pitchers.json.gz"),       GRADING, False,
         "Trends — pitcher game logs, every model input"),
        ("hitters",  ("file", f"{latest}/hitters.json.gz"),        GRADING, False,
         "Trends — hitter game logs"),
        ("record",   ("file", f"{latest}/record.json"),            GRADING, False,
         "Track Record — the graded record itself"),
        # ── 7:00am and 4:00pm — the paid pulls
        ("gamelines", ("file", f"{latest}/board.json"),            ODDS, True,
         "Odds + Scores & Matchups — moneylines, spreads, totals"),
        ("props-pitcher", ("dir", f"{data}/{utc_day}/props-pitcher"), ODDS, True,
         "Player Props — pitcher markets"),
        ("props-batter",  ("dir", f"{data}/{utc_day}/props-batter"),  ODDS, True,
         "Player Props — hitter markets"),
        ("props-board", ("file", f"{latest}/props.json.gz"),       ODDS, False,
         "Player Props — the join that puts props on the board"),
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
    ]


# 🔴 SOFT ARTIFACTS — late, or failing, must not take the site down.
# ⛔ Converge made every mode's failure everyone's failure: before this,
# one dead news RSS feed turned the whole run red and, under the old
# workflow, could stop the commit. These three are things a reader can
# lose without being misled -- headlines, conditions, lineups. Odds, the
# card and the track record are NOT here and never should be: those are
# numbers someone bets on.
SOFT = {"news", "weather", "lineups", "cfb-teams"}


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


def survey(data="data", picks="picks", now=None):
    """Age every artifact against its deadline. Pure -- no side effects."""
    now = now or datetime.datetime.now(UTC)
    rows = []
    for mode, (kind, path), times, paid, why in contract(data, picks, now):
        age = (newest_age_minutes(path, now) if kind == "dir"
               else age_minutes(path, now))
        built = None if age >= MISSING else now - datetime.timedelta(minutes=age)
        due = last_due(times, now)
        stale = built is None or (due is not None and built < due)
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
            "late_min": (None if (built is None or due is None or not stale)
                         else round((now - due).total_seconds() / 60.0, 1)),
            "paid": paid, "stale": stale, "missing": age >= MISSING,
        })
    return rows


def plan(data="data", picks="picks", now=None, allow_paid=True):
    """The ordered list of modes needed to meet every deadline that has
    passed. Order is the contract's order, which is dependency order."""
    rows = survey(data, picks, now)
    order = [r["mode"] for r in rows]
    need = {r["mode"] for r in rows if r["stale"]
            and (allow_paid or not r["paid"])}
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
