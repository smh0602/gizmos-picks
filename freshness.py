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


def last_due(times_et, now=None):
    """The most recent scheduled build time that has already passed.

    An artifact is stale when it was last written BEFORE this moment.
    Handles the wrap: at 3am ET the governing deadline is yesterday's
    last one, not today's first.
    """
    now = now or datetime.datetime.now(UTC)
    et = now - ET_OFFSET
    best = None
    for back in (0, 1):
        d = (et - datetime.timedelta(days=back)).date()
        for hh, mm in times_et:
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


def contract(data="data", picks="picks", now=None):
    latest = f"{data}/latest"
    day = et_date(now)
    utc_day = (now or datetime.datetime.now(UTC)).strftime("%Y-%m-%d")
    return [
        # mode              probe                                  due       paid  tab / why
        # ── 6:00am — grade last night, then rebuild what grading feeds
        ("scores",   ("file", f"{latest}/scores.json.gz"),         GRADING, False,
         "Track Record — last night's finals; self-healing, walks every missing date"),
        ("results",  ("file", f"{data}/{day}/results/final.json.gz"), GRADING, False,
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
        ("card",     ("file", f"{picks}/{day}.json"),              CARD, False,
         "Gizmo's Picks + Parlays"),
        # ── unchanged
        ("news",     ("file", f"{latest}/news.json"),              NEWS, False,
         "News"),
    ]


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
            "due_et": "/".join(f"{h}:{m:02d}" for h, m in times),
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
