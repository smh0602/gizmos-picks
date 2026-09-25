#!/usr/bin/env python3
"""
dossier_fb.py — SAM'S EIGHT CHECKS, RUN FOR EVERY GAME ON THE BOARD.

    LEAGUE=nfl python dossier_fb.py

🔴 THIS IS A REPORTING ARTIFACT AND IT MAKES NO PREDICTION. It ships
without a pre-registered test because there is nothing to pre-register:
it combines nothing, ranks nothing, and scores nothing. ⛔ NO COMBINED
NUMBER, NO "BET THIS" ORDER, NO CONFIDENCE %. Any of those would be a
model, and a model in this project needs a test fixed before the fit.

⛔ AND IT MOVES NO PROJECTION. `card_fb.py` does not import this file and
never will; the proof is a card built before and after and diffed, in
`test_dossier_fb.py`.

⚠️ EVERY SECTION IS PRESENT OR EXPLICITLY UNAVAILABLE. An absent section
is indistinguishable from a section that found nothing, and this repo has
shipped that shape before (`own_mean` sat at 0 of 200 graded rows while
the cards carried it on all 339, and nothing said so). So each of the
eight always appears, carrying `state` and — when it cannot answer — the
reason and what would fix it.

🔒 EVERY NUMBER CARRIES ITS PROVENANCE, rule 55: MARKET (the books'),
DESCRIPTIVE (a record, ours or the league's), MODEL (a Gizmo's output).
⛔ Nothing here is MODEL. That is not an oversight; it is the point.

══════════════════════════════════════════════════════════════════════
MEASURED BEFORE BUILDING `[2026-09-17]`, and two of the brief's own
numbers came back different. Both are recorded here rather than quietly
adopted:

  1. MARKET  `closing_spread/total/ml` is 285/285 on **schedule-2025**, a
     COMPLETED season. On 2026 it is 48 of 272 — 16 of 16 finals and 32
     of 256 upcoming. ⛔ For a game that has not kicked off, a closing
     line does not exist YET; reporting its absence as a gap would be
     reporting the calendar. The live market for a board game is
     `board.json`, and that is what section 1 reads.
     ⛔ FIRST-HALF MARKETS ARE GENUINELY ABSENT — zero fields matching
     `half`/`1h` anywhere in the schedule. Recorded as a known gap.
  8. VENUE  285 distinct 2025 games: **193 outdoors, 189 of them carrying
     BOTH temp and wind**, and 92 dome-or-closed (the brief said 91 — one
     game's difference, and the measurement is what ships). ⚠️ So the
     apparent 66% coverage is not a gap: weather is missing where weather
     is meaningless.
  6. TIME OF POSSESSION  PROBED FIRST, as instructed. `drive_time_of_
     possession` **EXISTS** in `play_by_play_2025.csv.gz` — 372 columns,
     read from the real header — populated on 2457 of 2491 sampled plays,
     formatted `M:SS`, beside `fixed_drive` and `game_id`.
     ⛔ BUT THE FILE IS NOT COMMITTED. The collector downloads it, uses
     it, and discards it; nothing under `data/` carries possession. So
     this section is UNAVAILABLE with the remedy named, rather than
     claimed. ⚠️ It reads `top-<season>.json.gz` if one ever appears.
══════════════════════════════════════════════════════════════════════
"""
import ast
import collections
import datetime
import glob
import gzip
import json
import os
import re
import sys
import unicodedata

import daystore
import possession as _poss

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUE = os.environ.get("LEAGUE", "nfl")
DATA = os.path.join(ROOT, "data", LEAGUE)

MARKET, DESC = "MARKET", "DESCRIPTIVE"
H2H_DAYS = 365          # ⚠️ "within 1 year" — the brief's own bound
MAX_PLAYERS = 8         # per team, by trailing snap share. Capped and SAID.


# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 THE ONE BOUNDARY THIS FILE EXISTS TO HOLD, AND NOTHING HELD IT.
# ══════════════════════════════════════════════════════════════════════
# `[Sam, 2026-09-17]` The docstring said "combines nothing, ranks nothing,
# scores nothing" and that was the whole enforcement. Adding
# `"score": 0.73, "confidence": 88` beside the sections list put both
# the PUBLISHED `dossiers.json.gz` with the suite fully green — confirmed
# end to end, not argued about. The test walked `sections` and never
# looked at the dossier's own frame.
#
# ⛔ SO THE GATE IS IN THE BUILDER, NOT ONLY IN THE TEST. A test catches
# it in CI; this refuses to WRITE the file at all. Publishing a verdict is
# the forbidden act, and not publishing is the safe direction.
#
# ⚠️ A CLASS, NOT A BLOCKLIST OF THREE NAMES. The next synonym — `rating`,
# `tier`, `signal`, `priority` — would walk straight past a list of
# `score`/`rank`/`confidence`. The rule is: any NUMERIC field whose NAME
# carries a judgement token.
#
# ⛔ AND IT MUST NOT FIRE ON CORRECT DATA. Carried source payloads
# legitimately contain `home_score` (a game that happened), `rec_yds_rank`
# (the league's own ranking) and `best_spread` (a book's price). Those are
# FACTS THIS FILE COPIED, not judgements it formed. So the walk descends
# everywhere EXCEPT the subtrees named below, each of which is verbatim
# source data.
#
# 🔴🔴 ~~"`audit()` refuses to run if one of those names has stopped
# appearing, so the exception surface cannot be padded with junk"~~
# **STRUCK 2026-09-19 — IT WAS A GUARD FIRING ON CORRECT DATA, AND IT
# FAILED CLOSED.** Whether `meetings` appears is a property of the SLATE,
# not of the walk: it is there only if some game on the board has a prior
# meeting inside 365 days. On a board where none does, the whole dossier
# refused to write and the football tabs got nothing.
# `[measured 2026-09-19]` `test_dossier_coverage.py` passed 42/42 against
# `main` at 10:11Z and failed 4 of 42 against `main` at 16:04Z **with no
# code change to this file or that test** — the only difference was 72
# files the collector had committed under `data/`. The verdict of a
# product guard was being decided by which two games the board happened
# to hold.
# ✅ **THE ANTI-PADDING QUESTION IS ANSWERED STATICALLY INSTEAD, AND IT IS
# STRICTLY HARDER:** every name in `CARRIED` must be a dict key THIS
# MODULE EMITS, checked against this file's own AST by
# `test_dossier_coverage.py` on every run. A junk name fails that on a
# quiet Tuesday as surely as on a full Saturday — where the old check
# could be satisfied by nothing more than a busy slate.
# ⚠️ A name that is absent from a given slate is now REPORTED on the
# document as `carried_absent`, never a refusal.
VERDICT_TOKENS = ("score", "conf", "rank", "rating", "grade", "edge",
                  "pick", "lean", "bet", "recommend", "verdict", "tier",
                  "star", "weight", "index", "prob", "likelihood",
                  "chance", "ev", "odds", "strength", "signal",
                  "priority", "best", "top", "value")

# The keys whose SUBTREES are copied from a source, verbatim.
CARRIED = ("live", "closing", "meetings", "by_team", "by_player",
           "by_defence", "weather")


def _verdicty(key):
    k = str(key).lower()
    return any(t in k for t in VERDICT_TOKENS)


def audit(doc):
    """Every numeric judgement-shaped field the dossier itself emits.

    -> [(path, key, value)]  ⛔ empty is the only acceptable answer.

    ⚠️ BOOLEANS ARE NUMBERS IN PYTHON and a `True` here would be a verdict
    too, so `isinstance(v, bool)` is NOT excused.
    """
    found, seen_carried = [], set()

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in CARRIED:
                    seen_carried.add(k)
                    continue          # ⛔ copied source data, not ours
                if isinstance(v, (int, float)) and _verdicty(k):
                    found.append(("%s.%s" % (path, k), k, v))
                walk(v, "%s.%s" % (path, k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, "%s[%d]" % (path, i))

    walk(doc, "")
    # ⚠️ ABSENT, NOT MISSING — the word matters. A `CARRIED` name this
    #    slate does not happen to carry is a fact about the slate. The
    #    caller REPORTS it; it must never refuse on it. See the struck
    #    paragraph beside `CARRIED`.
    absent = [c for c in CARRIED if c not in seen_carried]
    return found, absent


def log(m):
    print("[%s] %s" % (datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"), m))


def _jz(path):
    try:
        return json.load(gzip.open(path, "rt"))
    except Exception:
        return None


def _j(path):
    """The same, for a file that is NOT gzipped. ⚠️ The probes are plain
    JSON on purpose — they exist to be READ, and a gzipped diagnostic is
    a diagnostic nobody opens."""
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════
# 🔴 THE LEAGUES THIS BUILDS. `[ncaaf added 2026-09-17]`
# ⛔ The college board carried **88 games with no signals 1-8 at all** —
# the biggest slate of the week — because `build()` opened with
# `if lg != "nfl": return 0`. **`return 0` IS SUCCESS**: the card built,
# the chained call ran, nothing raised, and every check passed.
# ➡️ AN UNIMPLEMENTED BRANCH MUST RETURN A STATE THE WATCHERS CAN SEE, OR
# IT IS INDISTINGUISHABLE FROM A WORKING ONE.
# ⚠️ The refusal's REASONING was right — "a half-built college dossier is
# worse than none: it would look complete and describe a different
# sport's data shape" — and that is the thing engineered against below,
# not a reason to keep refusing.
# ══════════════════════════════════════════════════════════════════════
LEAGUES_BUILT = ("nfl", "ncaaf")

# ⛔ VERIFIED ONE BY ONE AGAINST `teams.json`, NEVER FUZZY-MATCHED. The
# college board names a school plus its mascot ("Syracuse Orange") while
# every college artifact keys on the school alone ("Syracuse"), so the
# join is a prefix match — and three FBS schools are spelled differently
# on the two sides. ⚠️ `difflib` was tried and REFUSED: it maps "East
# Texas A&M Lions" onto "Texas A&M", "Portland State" onto "Colorado
# State" and "South Dakota" onto "North Dakota State" — different
# schools. That is `resolve()`'s rule (CLAUDE.md): refuse to guess.
CFB_ALIAS = {"appalachianstate": "App State",
             "southernmississippi": "Southern Miss",
             "umass": "Massachusetts"}


def _norm_school(s):
    """Fold case, accents and punctuation. ⚠️ `San José State` and `San
    Jose State` are one school; `Hawai'i` and `Hawaii` are one school."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def team_codes(lg=None):
    """A RESOLVER: board team name -> the key that league's files use.

    ⚠️ IT RETURNS A FUNCTION, not a dict, because the two leagues join
    differently. NFL board names are exact keys of a 32-row table;
    college names need folding and a longest-prefix match.

    ⛔ NFL's TABLE IS READ OUT OF `collect.py`'s SOURCE, never retyped.
    That file's own comment says "if you edit one side, edit both", and a
    second copy of a 32-row table is a second thing to drift (rule 66).
    ⚠️ Parsed rather than imported: importing the collector runs its
    module-level league handling, and a reporting tool must not be able
    to trip that.

    ⛔ AND IT RETURNS None RATHER THAN A GUESS. 16 of the 88 college
    board sides are FCS schools absent from the FBS `teams.json` — a
    correct absence, not a failure, and naming it is the only honest
    answer.
    """
    lg = (lg or LEAGUE or "nfl").strip().lower()
    if lg == "nfl":
        src = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
        for n in ast.parse(src).body:
            if (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "")
                    == "NFL_TEAMS"):
                return ast.literal_eval(n.value).get
        return {}.get
    # ── college ──────────────────────────────────────────────────────
    try:
        raw = json.load(open(os.path.join(ROOT, "data", lg, "latest",
                                          "teams.json"), encoding="utf-8"))
        schools = list((raw.get("teams") or {}))
    except Exception:
        schools = []
    idx = {}
    for t in schools:
        idx.setdefault(_norm_school(t), t)
    # ⚠️ LONGEST FIRST, so "Miami (OH) RedHawks" resolves to `Miami (OH)`
    #    and not to `Miami`.
    order = sorted(idx, key=len, reverse=True)

    def resolve(name):
        n = _norm_school(name)
        if not n:
            return None
        for a, t in CFB_ALIAS.items():
            if n.startswith(a):
                return t
        for k in order:
            if n == k or n.startswith(k):
                return idx[k]
        return None
    return resolve


def _near(d, kick, days=1):
    """Is schedule date `d` within `days` of the board's kickoff date?

    ⚠️ AND THE TWO SIDES ARE NOT THE SAME CONVENTION, WHICH IS WHY THE
    WINDOW EXISTS. `[measured 2026-09-18]` The board's `commence` is UTC.
    The COLLEGE schedule stores `start` with a `Z` and agrees with it;
    the NFL schedule stores `2026-09-09T20:20` with NO ZONE MARKER at
    all, so a Sunday-night kickoff files under 09-13 there and 09-14 on
    the board. ⛔ So `days=1` is load-bearing rather than slack, and
    tightening it to an exact match would silently drop every NFL night
    game. ✅ It is safe to widen this far because the key is checked for
    uniqueness: measured across 4 stored schedules, 8,063 of 8,065
    (team, date ±1) keys hold exactly one game."""
    if not (d and kick):
        return False
    try:
        return abs((datetime.datetime.strptime(d, "%Y-%m-%d")
                    - kick).days) <= days
    except ValueError:
        return False


def week_calendar(sched):
    """{UTC date: week} for every date the stored schedule places.

    ══════════════════════════════════════════════════════════════════
    ⚠️ DERIVED FROM THE CALENDAR, NEVER GUESSED FROM A DATE. `[2026-09-18]`
    A week number is a fact about the season the schedule already
    defines: measured on `schedule-2026.json.gz`, 67 distinct dates and
    **not one of them maps to two different weeks**, so the mapping is a
    function rather than a judgement.
    ⛔ AND IT FAILS CLOSED. The weeks do not tile the calendar — week 1
    ends 09-07 and week 2 opens 09-10, week 14 is absent entirely — so a
    date in a gap, before the first week or after the last, IS NOT
    PLACED. It is refused, and the reason names the date.
    ⛔ A date that somehow reached two weeks would be dropped rather than
    resolved to either: this project does not pick the first match.
    ══════════════════════════════════════════════════════════════════
    """
    seen = collections.defaultdict(set)
    for _season, j in sorted(sched.items()):
        for x in (j.get("games") or []):
            d, w = (x.get("start") or "")[:10], x.get("week")
            if d and w is not None:
                seen[d].add(w)
    return {d: next(iter(w)) for d, w in seen.items() if len(w) == 1}


def seasons(kind, data=None):
    """{season: payload} for every `<kind>-<year>.json.gz` on disk."""
    out = {}
    for p in sorted(glob.glob(os.path.join(data or DATA, "latest",
                                           "%s-*.json.gz" % kind))):
        m = re.search(r"-(\d{4})\.json\.gz$", p)
        j = _jz(p)
        if m and j is not None:
            out[int(m.group(1))] = j
    return out


def _skip(g, why):
    """A board game this builder could not describe, NAMED not dropped.

    ⚠️ ONE LINE ON PURPOSE. `test_dossier_fb.py` declares a mutation
    against this call site, and a mutation that has to span two lines
    lands as a SyntaxError — which goes red for the WRONG reason and is
    indistinguishable from a working guard.
    """
    return {"away": g.get("away"), "home": g.get("home"), "why": why}


def unavailable(n, name, why, remedy=None):
    """⚠️ THE SHAPE THAT MAKES A GAP VISIBLE. A section that cannot answer
    says so, says why, and says what would change it."""
    d = {"n": n, "name": name, "state": "UNAVAILABLE", "basis": None,
         "why": why}
    if remedy:
        d["remedy"] = remedy
    return d


# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 ONE REFUSAL FOR A GAME WHOSE OPPONENT WE CANNOT IDENTIFY, AND IT
# IS WRITTEN ONCE (rule 117).
# ⛔ `[2026-09-17 — 19 of 88 college rows published a null opponent and
# five sections still read OK.]` The board is a SUPERSET of the
# top-division team list by construction, because books price
# top-division-vs-lower-division games. So a name that does not resolve
# is a DATA CLASS, not an edge case.
# 🔴 AND THE WORST OF IT WAS NOT THE NULL. Head-to-head said "No meeting
# between these two inside 365 days" — a statement about a comparison
# THAT WAS NEVER ATTEMPTED, because there is no "these two". A reader
# takes that as "they have not played recently". The truth is "we do not
# know who the opponent is". ⛔ A fact about a query is not a fact about
# the world, and that is this project's founding error wearing college
# colours.
# ⚠️ WRITTEN FOR A READER. `verify_card.py`'s jargon list is the
# standard, and "top-division" is said instead of an acronym.
#
# 🔴🔴 AND IT SAYS WHAT WE DO NOT HAVE, NOT WHAT THE WORLD IS. The first
# draft of this sentence read "X is not a top-division team" — which is
# an assertion about the WORLD inferred from a FAILED LOOKUP, and every
# one of those today happens to be true only because all 16 really are
# lower-division schools. ⛔ A name can also fail to resolve because our
# own matching missed a real top-division school, and then that sentence
# is simply false on a page Sam bets from. ➡️ So it reports the state of
# our records, which is true either way — the same distinction the
# head-to-head sentence got wrong.
# ══════════════════════════════════════════════════════════════════════
def no_opponent(n, name, who):
    """⛔ UNAVAILABLE, never OK and never a blank. `who` is the board's
    own name for the side that does not resolve — the board always has
    it, so nothing here ever reads `None`."""
    return unavailable(
        n, name,
        "We hold no season record for %s — the team list this page is "
        "built from covers top-division sides only, and that name is not "
        "in it. The price above is real; this comparison is not "
        "available." % (who or "the opponent"),
        "nothing to run on our side — this is a team the season files do "
        "not cover, not a file that is late")


# ⚠️ SAID ONCE TOO, for the per-team sections that keep the half they do
#    have. ⛔ They stay OK because what they show is real — but a section
#    covering one team of two and saying nothing about it is the same
#    "looks complete" failure one step quieter.
def one_side_only(who):
    return ("Nothing is shown for %s — we hold no season record for them, "
            "because that name is not in the top-division team list this "
            "page is built from." % (who or "the opponent"))


# ───────────────────────────────────────────────────── 1. MARKET
def s_market(g, sched_row):
    """The books' own numbers. ⛔ MARKET, never ours."""
    d = {"n": 1, "name": "Market", "state": "OK", "basis": MARKET,
         "live": {"total": g.get("total"), "run_line": g.get("run_line"),
                  "run_line_team": g.get("run_line_team"),
                  "best_spread": g.get("best_spread"),
                  "best_total": g.get("best_total"),
                  "best_ml": g.get("best_ml"),
                  "n_books": g.get("n_books"),
                  "vig_pct": g.get("vig_pct")},
         "why": ("The live board — every figure is a price a book is "
                 "showing, not an estimate of ours.")}
    # ⚠️ A CLOSING LINE EXISTS ONLY AFTER THE GAME. Absent before kickoff
    #    is the calendar, not a gap, and the two are labelled apart.
    if sched_row and sched_row.get("closing_spread") not in (None, "", "NA"):
        d["closing"] = {k: sched_row.get(k) for k in
                        ("closing_spread", "closing_total",
                         "closing_ml_home", "closing_ml_away")}
    else:
        d["closing"] = None
        d["closing_note"] = ("No closing line yet — the schedule carries "
                             "one only once the game is final. Measured "
                             "2026-09-17: 285 of 285 on the completed "
                             "2025 season, 16 of 16 finals in 2026.")
    # ══════════════════════════════════════════════════════════════════
    # 🔴 THE FIRST-HALF TOTAL — ONE BOOK, AND IT SAYS SO.
    # ══════════════════════════════════════════════════════════════════
    # `[Sam, 2026-09-18]` The live pull asks ONE market in ONE region,
    # and `us2` is the region Hard Rock lives in. So this figure is Hard
    # Rock's own number, not a best price across five books.
    # ⛔ IT MUST NOT INHERIT THE CONSENSUS WORDING THE FULL-GAME ROWS
    # USE. Every other price in this section is the best of five books;
    # this one is one book's line, and a reader who cannot tell them
    # apart has been told something false about how hard it was shopped.
    # ⚠️ ~~"FIRST-HALF MARKETS ARE NOT HELD"~~ — the TOTAL is held now.
    # The MONEYLINE still is not, and that half stays a stated gap
    # rather than a silence.
    fh = g.get("first_half_total")
    if fh:
        d["first_half"] = {
            "total": fh.get("point"),
            "over": fh.get("over"), "under": fh.get("under"),
            "book": fh.get("book"),
            "n_books": fh.get("n_books"),
            # 🔴 RULE 55 ON THE SURFACE: the label travels with the
            #    number, so the page cannot show one without the other.
            "shopping": "ONE BOOK",
            "why": ("The first-half total is %s, priced by %s alone. "
                    "Every other number in this section is the best of "
                    "%s books; this one is not shopped, so it is that "
                    "book's own line and may not be the best available."
                    % (fh.get("point"), fh.get("book") or "one book",
                       g.get("n_books") if g.get("n_books") else "several")),
        }
    else:
        d["first_half"] = None
        d["first_half_note"] = (
            "No first-half total for this game yet. It is bought only for "
            "games kicking off soon, from one book, so an absence here is "
            "about what we asked for and not about what the book is "
            "offering.")
    # 🔴 READER ENGLISH, IN THE BUILDER. `[rule 132]` The page prints
    #    this string VERBATIM — it does not sentence-case it, trim it or
    #    reword it — so the register has to be right here. ⛔ No jargon,
    #    no shouting, and every sentence carries a number.
    d["known_gap"] = (
        "There is no first-half moneyline or spread. The half total is "
        "the only one of the three we buy, and the stored schedule holds "
        "no first-half figures at all, so none is filled in from "
        "anywhere else.")
    d["known_gap_remedy"] = (
        "adding one would mean a second market on the same per-game "
        "pull, which is a spending decision rather than an oversight")
    return d


# ─────────────────────────────────────────────── 2. HEAD-TO-HEAD
def s_h2h(home, away, kick, sched, missing=None):
    """Prior meetings inside one year. ⚠️ n is 1-2 and it says so.

    ⛔ IT REFUSES BEFORE IT SEARCHES when one side does not resolve. The
    search itself would `pair != {home, None}` on every row and report
    "no meeting between these two" — a false statement about a check
    that never ran. See `no_opponent`.
    """
    if missing or not (home and away):
        return no_opponent(2, "Head to head", missing)
    met = []
    for season, j in sorted(sched.items()):
        for x in (j.get("games") or []):
            if not x.get("final"):
                continue
            pair = {x.get("home"), x.get("away")}
            if pair != {home, away}:
                continue
            st = (x.get("start") or "")[:10]
            try:
                when = datetime.datetime.strptime(st, "%Y-%m-%d")
            except ValueError:
                continue
            if kick and (kick - when).days > H2H_DAYS:
                continue
            met.append({"season": season, "week": x.get("week"),
                        "date": st, "home": x.get("home"),
                        "away": x.get("away"),
                        "home_score": x.get("home_score"),
                        "away_score": x.get("away_score")})
    if not met:
        return unavailable(2, "Head to head",
                           "No meeting between these two inside %d days."
                           % H2H_DAYS)
    return {"n": 2, "name": "Head to head", "state": "OK", "basis": DESC,
            "meetings": met, "n_meetings": len(met),
            "why": ("%d prior meeting%s inside one year. ⚠️ That is a "
                    "sample of %d, with roster and coaching turnover "
                    "between then and now — it is history, not a rate."
                    % (len(met), "" if len(met) == 1 else "s", len(met)))}


# ──────────────────────────────────────────────── 3. TIME OF YEAR
def s_time_of_year(teams, week, players, this_season, missing=None,
                   kick_date=None):
    """What these teams and players did in THIS week number before.

    ⚠️ PER TEAM, so one resolvable side is a real half-answer — but it
    SAYS which half is missing. ⛔ And `teams` never carries a None:
    `build()` filters it, because a None in this list published a
    literal `"null"` key inside `by_team` on 19 college rows.
    """
    if not week:
        # ⛔ AND IT NAMES THE DATE IT COULD NOT PLACE. `[2026-09-18]`
        #    "the schedule does not give this game a week number" is true
        #    and unactionable: it does not say WHICH date the season
        #    calendar failed on, so nobody can check whether the calendar
        #    is short or the date is wrong. ⚠️ The weeks do not tile the
        #    year — week 1 ends 09-07 and week 2 opens 09-10 — so a date
        #    landing in a gap is a real and recognisable state.
        return unavailable(3, "Time of year",
                           "We cannot place %s in the season's weeks, so "
                           "there is nothing to compare this game "
                           "against."
                           % (kick_date or "this game's date"))
    per_team, per_player = {}, {}
    for t in teams:
        games, pl = [], collections.defaultdict(list)
        for season, j in sorted(players.items()):
            if season >= this_season:
                continue          # ⛔ prior seasons only
            for pid, v in (j.get("players") or {}).items():
                for row in (v.get("g") or []):
                    if row.get("week") != week or row.get("team") != t:
                        continue
                    pl[v.get("name") or pid].append({
                        "season": season, "opp": row.get("o"),
                        "rec_yds": row.get("rec_yds"),
                        "rush_yds": row.get("rush_yds"),
                        "pass_yds": row.get("pass_yds"),
                        "snap_pct": row.get("snap_pct")})
                    games.append(row.get("game_id"))
        per_team[t] = {"prior_seasons_with_this_week":
                       len(sorted({g for g in games if g})),
                       "player_rows": sum(len(v) for v in pl.values())}
        per_player[t] = dict(sorted(pl.items(),
                                    key=lambda kv: -len(kv[1]))[:MAX_PLAYERS])
    if not any(v["player_rows"] for v in per_team.values()):
        return unavailable(3, "Time of year",
                           "No prior-season rows exist for week %d for "
                           "either team." % week)
    d = {"n": 3, "name": "Time of year", "state": "OK", "basis": DESC,
         "week": week, "by_team": per_team, "by_player": per_player,
         "why": ("Week %d in earlier seasons, from the same player-game "
                 "rows the board is built on. ⚠️ Capped at %d players a "
                 "team by row count — it is a sample of the week, not a "
                 "roster." % (week, MAX_PLAYERS))}
    if missing:
        d["not_covered"] = missing
        d["why"] += " " + one_side_only(missing)
    return d


# ──────────────────────────────────────────────── 4. THIS SEASON
def s_this_season(teams, players, this_season, week, missing=None):
    """Trailing form — the same rows the model already reads.

    ⚠️ PER TEAM, and it names the side it covers nothing for."""
    j = players.get(this_season)
    if not j:
        return unavailable(4, "This season",
                           "No player file for %d yet." % this_season)
    out = {}
    for t in teams:
        pl = {}
        for pid, v in (j.get("players") or {}).items():
            rows = [r for r in (v.get("g") or []) if r.get("team") == t]
            if not rows:
                continue
            rows = sorted(rows, key=lambda r: r.get("week") or 0)[-4:]
            pl[v.get("name") or pid] = {
                "pos": v.get("pos"), "last": rows,
                "games": len(rows)}
        out[t] = dict(sorted(pl.items(),
                             key=lambda kv: -(kv[1]["last"][-1].get("snap_pct")
                                              or 0))[:MAX_PLAYERS])
    if not any(out.values()):
        return unavailable(4, "This season",
                           "No %d rows for either team yet." % this_season)
    d = {"n": 4, "name": "This season", "state": "OK", "basis": DESC,
         "season": this_season, "through_week": week, "by_team": out,
         "why": ("The last four games each, by trailing snap share. "
                 "⚠️ This is the model's own input shown as a record; "
                 "it is not a second estimate of anything.")}
    if missing:
        d["not_covered"] = missing
        d["why"] += " " + one_side_only(missing)
    return d


# ─────────────────────────────────────────────── 5. VS POSITION
# 🔴 THE VERDICT TRAVELS WITH THE NUMBER, ALWAYS. It was dropped in both
#    sports once, and a rank with no scale beside it reads as a reason to
#    bet. ⛔ It may not move a projection and it does not.
VS_VERDICT = (
    "⛔ DISPLAYED, NOT APPLIED. A one-standard-deviation swing in "
    "defensive quality is worth about 4.4 rushing yards, against roughly "
    "27 yards of held-out error on the same prediction — so this ranking "
    "is real and it is far smaller than the noise it sits inside. It "
    "moves no projection on this page, and a rank shown without that "
    "sentence reads as a reason to bet.")


# ══════════════════════════════════════════════════════════════════════
# 🔴 SAM'S FOUR, FIXED, IN HIS OWN ORDER.
# ══════════════════════════════════════════════════════════════════════
# `[Sam, 2026-09-18: "for player props i only want qb,rb,wr,te"]`
#
# ⛔ NOT A SORT, NOT THE BIGGEST GAPS, NOT THE WORST. The four are chosen
# because they carry the props he bets — his call, already made — so this
# requires NO JUDGEMENT of the builder and offers none. ⛔ They are never
# ranked against each other; the order below is the order he typed them
# in and means nothing else.
#
# 🔴 AND IT WAS ALREADY TRUE BY ACCIDENT, WHICH IS THE PART WORTH FIXING.
# `[measured 2026-09-18]` `allowed-by-position-2026.json.gz` holds exactly
# QB, RB, TE and WR — 217 college defences and 32 NFL ones, no fifth
# position anywhere. So iterating the FILE's keys gave the right answer
# today. ⛔ But `PROP_POS` in BOTH `cfb.py` and `nfl.py` is
# `{"QB", "RB", "WR", "TE", "FB"}` — **five** — so the collectors are
# already scoped to gather a fullback, and the first FB row to appear
# would put a fifth position on the page with nobody deciding.
# ⚠️ "It happens to agree" is what this project stops trusting — §6's own
# comment says so in those words.
VS_POSITIONS = ("QB", "RB", "WR", "TE")


def no_position(team, pos, whole_team=False):
    """ONE REFUSAL FOR A POSITION WE HOLD NO NUMBERS FOR (rule 117).

    ⛔ IT STATES A CLAIM ABOUT OUR RECORDS, NEVER ABOUT THE WORLD. "We
    hold nothing for X against the running back" is true; "X has faced no
    running backs" is a sentence about football that this file cannot
    support, and the same slip has been corrected twice in this repo.
    """
    return {
        "state": "UNAVAILABLE",
        "why": ("We hold no numbers for %s against the %s%s."
                % (team, _POS_WORDS.get(pos, pos),
                   " — we hold nothing for that defence at all"
                   if whole_team else "")),
        "remedy": ("it fills in once the season back-fill covers that "
                   "defence"),
    }


# ⚠️ READER ENGLISH FOR EACH CODE. `verify_card.py` fails the MLB build on
#    a jargon list and the same standard governs this page: a casual
#    reader knows "quarterback", not necessarily "QB" beside a refusal.
_POS_WORDS = {"QB": "quarterback", "RB": "running back",
              "WR": "wide receivers", "TE": "tight end"}


def s_vs_position(home, away, allowed, this_season, missing=None):
    """⛔ THE SUBJECT IS THE OPPOSING DEFENCE, so an unidentified
    opponent is not a thin answer — it is no answer. This read OK with
    one defence in it on 19 college rows."""
    if missing or not (home and away):
        return no_opponent(5, "Versus position", missing)
    j = allowed.get(this_season) or allowed.get(this_season - 1)
    if not j:
        return unavailable(5, "Versus position",
                           "No allowed-by-position file on disk.",
                           "the season back-fill writes it (`nfl-logs` "
                           "for NFL, `cfb-probe` for college)")
    defs = j.get("defences") or {}
    out, not_held, dropped = {}, {}, set()
    for t in (home, away):
        d = defs.get(t)
        if d is None:
            # ⛔ A DEFENCE WE HOLD NOTHING FOR REFUSES ON ALL FOUR, BY
            #    NAME. Leaving the team out entirely is the shape that
            #    let 19 college rows read OK with one defence in them.
            not_held[t] = {pos: no_position(t, pos, whole_team=True)
                           for pos in VS_POSITIONS}
            continue
        # ⚠️ ANYTHING THE FILE HOLDS BEYOND THE FOUR IS DROPPED — AND
        #    SAID SO. Silently discarding a position would be the same
        #    class of quiet as silently showing one.
        dropped |= {p for p in d if p not in VS_POSITIONS}
        kept, miss = {}, {}
        # 🔴 THE DECLARED FOUR, IN ORDER — NEVER THE FILE'S OWN KEYS.
        for pos in VS_POSITIONS:
            row = {k: v for k, v in (d.get(pos) or {}).items()
                   if k.endswith("_rank") or k.endswith("_pct")
                   or k == "games"}
            if row:
                kept[pos] = row
            else:
                # ⛔ NOT A ZERO AND NOT A BLANK. A missing position is
                #    the same shape as an unresolved opponent one level
                #    up: it refuses, it names itself, and it says the
                #    claim is about OUR RECORDS and not about the team.
                miss[pos] = no_position(t, pos)
        if kept:
            out[t] = kept
        if miss:
            not_held[t] = miss
    if not out and not not_held:
        return unavailable(5, "Versus position",
                           "Neither %s nor %s appears in the "
                           "allowed-by-position file." % (home, away))
    if not out:
        return unavailable(
            5, "Versus position",
            "We hold no numbers for either defence in this game, so there "
            "is nothing to compare the four positions against.",
            "it fills in once the season back-fill covers both teams")
    d = {"n": 5, "name": "Versus position", "state": "OK", "basis": DESC,
         "season": j.get("season"), "by_defence": out,
         # 🔴 THE DECLARED LIST TRAVELS WITH THE DATA, so the page
         #    iterates WHAT WAS DECIDED rather than what happened to be
         #    on disk. ⛔ That is what stops a fifth position appearing
         #    on the page the day a fullback row does.
         "positions": list(VS_POSITIONS),
         "positions_note": ("These four because they carry the player "
                            "props on this site. They are not ordered "
                            "against each other."),
         "scale": j.get("rank_note") or "rank 1 = ALLOWS THE MOST",
         "verdict": VS_VERDICT,
         "why": ("How each defence has been scored on by position, "
                 "ranked across the league. " + VS_VERDICT)}
    if not_held:
        d["not_held"] = not_held
    if dropped:
        d["positions_not_shown"] = sorted(dropped)
        d["positions_not_shown_note"] = (
            "The file also holds %s, which this page does not show."
            % ", ".join(sorted(dropped)))
    return d


# ──────────────────────────────────────── 6. TIME OF POSSESSION
def s_possession(home, away, this_season, data=None, missing=None,
                 kickoff=None):
    """⚠️ PROBED, NOT ASSUMED. See the module header.

    ⚠️ THE OPPONENT GATE COMES FIRST, and deliberately: "we do not know
    who is playing" outranks "we do not have the numbers yet". Both are
    true on those rows and only the first tells the reader why no
    later run will fill it in.
    """
    if missing or not (home and away):
        return no_opponent(6, "Time of possession", missing)
    top = _jz(os.path.join(data or DATA, "latest",
                           "top-%d.json.gz" % this_season))
    if not top:
        # ⚠️ WRITTEN FOR A READER, NOT FOR THE LEDGER. `verify_card.py`'s
        # jargon list is the standard: no "coverage", no "0.90", no
        # "p10". ✅ Every sentence still carries a number — the stats are
        # the argument.
        # ⛔ THE LEAGUE COMES FROM THE PATH THE CALLER THREADED, NEVER
        # FROM THE ENVIRONMENT. `build(league)` takes a league and hands
        # every section the matching `data` root; reading the module
        # global here would let the SECTION answer about one league while
        # the DOCUMENT is about another the moment the two disagree — a
        # second source for one fact (rule 66). They happen to agree in
        # production because the workflow sets `LEAGUE` on every arm, and
        # "it happens to agree" is what this repo stops trusting.
        _lg = os.path.basename((data or DATA).rstrip(os.sep)).strip().lower()
        if _lg != "nfl":
            # ══════════════════════════════════════════════════════
            # 🔴🔴 ~~"Not enough college games have been played yet...
            # roughly the fourth week of the season, and this is the
            # third."~~ REWRITTEN `[2026-09-19]`
            # ══════════════════════════════════════════════════════
            # ⛔ IT NAMED A CAUSE THAT WAS NOT THE CAUSE. `[measured
            # 2026-09-18]` 336 games' worth of plays were fetched and
            # parsed — 10,132 drives, 299 teams, nothing unparsed. The
            # derivation REFUSED, over a play-ordering anomaly. The
            # coverage floor was never the binding constraint and the
            # week-4 estimate had been struck from the validation notes
            # the day before.
            # ⛔ AND IT WAS A CONSTANT ON `if _lg != "nfl"`, reading no
            # data at all, so it could never become true or false. In
            # week 10 it would still have said "this is the third".
            # ➡️ A sentence that cannot be wrong cannot be right either.
            # It is not a measurement, it is a caption.
            # ✅ THE PROBE IS ALREADY ON DISK AND ALREADY DISTINGUISHES
            # THE CASES, so this is derived. It is written in the voice
            # the NFL branch below was rewritten into on 2026-09-17,
            # which exists for exactly this class of mistake.
            # ⛔ AND THE REFUSAL TEXT DOES NOT NAME WHICH CHECK REFUSED.
            # Today it is the play ordering; tomorrow it could be the
            # coverage floor, and a string asserting one of them is the
            # defect above wearing a newer coat. The probe's OWN words
            # go in `remedy`, which the page does not print.
            _probe = _j(os.path.join(data or DATA, "latest",
                                     "top-probe-%d.json" % this_season))
            if _probe is None:
                # ⚠️ SAME SITUATION AS THE NFL BRANCH, so the same
                #    sentence: nothing ran, or the clock was too thin,
                #    and we do not claim to know which.
                return unavailable(
                    6, "Time of possession",
                    "No time-of-possession figures are stored for the %d "
                    "college season yet. They are worked out from the game "
                    "clock rather than read off a stat sheet, and a table "
                    "is only kept when enough of the clock could be read — "
                    "so this is either a build that has not run or a season "
                    "whose clock is too patchy to use, and we are not "
                    "claiming to know which." % this_season,
                    "run the college log build; the possession probe beside "
                    "the table says whether the job never ran or the clock "
                    "was too thin")
            if not _probe.get("usable"):
                # ✅ THE REFUSAL IS DELIBERATE AND READS LIKE IT. A blank
                #    section looks broken; a guard that declined to
                #    publish a number it could not stand behind is a
                #    feature, and the reader is entitled to know that is
                #    what happened.
                return unavailable(
                    6, "Time of possession",
                    "This season's college games have been read, and a "
                    "check this build runs before publishing turned the "
                    "result down — the timings it works from did not hold "
                    "together well enough to trust. Nothing is shown here "
                    "rather than a number we would not stand behind, which "
                    "is that check doing its job.",
                    "the possession probe for %d records the refusal and "
                    "its reason: %s"
                    % (this_season,
                       (_probe.get("error") or "no reason recorded")))
            # ⚠️ THE PROBE SAYS THE TABLE WAS USABLE AND THERE IS NO
            #    TABLE. That is a gap in the build, not in the data, and
            #    saying so is different from both cases above.
            return unavailable(
                6, "Time of possession",
                "Time-of-possession figures were worked out for the %d "
                "college season but have not reached this page. That is a "
                "gap in how the numbers are moved around rather than a gap "
                "in the numbers themselves, and we would rather say so "
                "than leave the section looking empty." % this_season,
                "the probe reports a usable table but none is stored "
                "beside it — check the write step of the college log build")
        # ══════════════════════════════════════════════════════════
        # 🔴 ~~"No `top-2026.json.gz` under `data/` yet..."~~ REWRITTEN
        # `[2026-09-17, when the page started printing these]`
        # ⛔ THAT SENTENCE WAS FOR AN OPERATOR AND IT WENT TO A READER.
        # It named a filename, a directory and a probe file, and it was
        # the §6 text on all 32 NFL games the moment the panel shipped.
        # Sam, 2026-08-26: "all of these things that a casual fine wont
        # know about has to go."
        # ✅ THE HONESTY IS KEPT, NOT SOFTENED: the old string's real
        # content was that an absent table is AMBIGUOUS between "the job
        # has not run" and "too little of the clock could be read", and
        # that ambiguity is still stated — in English, and still refusing
        # to claim which. ➡️ The filenames move to `remedy`, which is
        # where an operator looks and which the page does not print.
        # ══════════════════════════════════════════════════════════
        return unavailable(
            6, "Time of possession",
            "No time-of-possession figures are stored for the %d season "
            "yet. They are worked out from the game clock rather than "
            "read off a stat sheet, and a table is only kept when enough "
            "of the clock could be read — so this is either a build that "
            "has not run or a season whose clock is too patchy to use, "
            "and we are not claiming to know which."
            % this_season,
            "run the season's log build (`nfl-logs` writes "
            "`top-%d.json.gz`); `top-probe-%d.json` beside it says "
            "whether the job never ran or the clock was too thin"
            % (this_season, this_season))
    by = top.get("teams") or {}
    # ══════════════════════════════════════════════════════════════════
    # 🔴🔴 THE SECTION READS THE SHARE, AND ONLY THE SHARE.
    # ⛔ `seconds`, `drives` and `seconds_per_drive` stay in the artifact
    # as honest raw material and DO NOT COME OUT HERE. They are not
    # comparable between teams: the derivation observes a different
    # fraction of each game's clock, and on the college side that spread
    # runs from 30 pct to 101 pct. Reading raw seconds off it moved 202
    # of 217 teams by more than a minute and INVERTED the ranking —
    # Nicholls 21:00 raw against 38:33 real. `possession.py` has the
    # measurement.
    # ⚠️ `minutes` here is the SHARE expressed on a 60-minute clock, not
    # a second source for the same quantity (rule 66).
    # ══════════════════════════════════════════════════════════════════
    out = {}
    # 🔴 SIGNAL 6 BEFORE KICKOFF. `[Sam, 2026-09-23]` When the file carries
    #    per-game rows, each team's number is `possession.share_before` —
    #    its games dated BEFORE this kickoff and nothing else. ⛔ The season
    #    table is read only from a file built before per-game rows existed,
    #    and the next build of that season replaces it.
    games = top.get("games")
    for t in (home, away):
        if games is not None and kickoff:
            b = _poss.share_before(games, t, kickoff)
            if b["share"] is None:
                continue
            v = {"share": b["share"], "games": b["games"]}
        else:
            v = by.get(t)
            if not v or v.get("share") is None:
                continue
        spg = int(round(v["share"] * 3600))
        out[t] = {"share": v["share"], "seconds_per_game": spg,
                  "minutes": "%d:%02d" % divmod(spg, 60),
                  "games": v.get("games")}
    if not out:
        return unavailable(6, "Time of possession",
                           "A possession file exists but carries neither "
                           "%s nor %s with a readable share." % (home, away))
    return {"n": 6, "name": "Time of possession", "state": "OK",
            "basis": DESC, "by_team": out,
            "why": ("Share of the game clock each team held, averaged per "
                    "game and shown on a 60-minute clock. Games where too "
                    "little of the clock could be read are left out "
                    "rather than counted short.")}


# ─────────────────────────────────────────────── 7. PERSONNEL
# ⛔ COLLEGE HAS NO SOURCE WE MAY USE, AND THE PAGE SAYS SO IN WORDS.
#    `[probed 2026-09-23]` The SEC, Big Ten and ACC do publish availability
#    reports for conference games, but every one of their sites limits its
#    content to personal, non-commercial use and forbids copying or
#    republishing it (Big Ten, ACC/SIDEARM), or forbids automated access
#    outright (SEC, under ESPN/Disney's terms). Sam: "Build it only if it
#    is free and allowed by those sites' terms. Otherwise signal 7 is
#    NFL-only, and the page says so."
PERSONNEL_COLLEGE = (
    "Not covered for college games. The SEC, Big Ten and ACC publish "
    "injury reports for conference games, but their websites only allow "
    "personal use and do not allow the reports to be copied onto another "
    "site, so we don't collect them. This check covers NFL games only.")


def s_personnel(teams, players, this_season, missing=None, week=None,
                league=None):
    """⚠️ PER TEAM, and it names the side it covers nothing for.

    🔴 IT COUNTS PLAYERS RULED OUT. `[Sam, 2026-09-23]` It used to show
    the injury flag on each player's most recent STAT row — and a player
    who was out has no stat row, so it could only ever show "questionable
    and played". ✅ It now reads `team_out`, built by `nfl.py` from the
    injury report and the weekly roster: out, doubtful, injured reserve,
    inactive.
    """
    if league and league != "nfl":
        return unavailable(7, "Personnel", PERSONNEL_COLLEGE)
    j = players.get(this_season)
    if not j:
        return unavailable(7, "Personnel",
                           "No player file for %d yet." % this_season)
    tout = j.get("team_out")
    if tout is None:
        rep = j.get("team_out_report")
        return unavailable(
            7, "Personnel",
            "We don't have a list of players ruled out for this season yet.",
            ("the players-out count was built and turned down: %s"
             % rep.get("error")) if rep else
            ("the next NFL log build adds it to players-%d" % this_season))
    out = {}
    for t in teams:
        wks = sorted((int(w) for w in (tout.get(t) or {})
                      if str(w).isdigit() and (week is None or int(w) <= int(week))))
        if not wks:
            out[t] = {"week": None, "out": 0, "players": []}
            continue
        c = tout[t][str(wks[-1])]
        out[t] = {"week": wks[-1], "out": c.get("out", 0),
                  "players": [p.get("name") for p in (c.get("players") or [])]}
    d = {"n": 7, "name": "Personnel", "state": "OK", "basis": DESC,
         "by_team": out,
         "flagged": sum(v["out"] for v in out.values()),
         "why": ("Players ruled out for each team's latest reported week: "
                 "listed out or doubtful on the injury report, on injured "
                 "reserve, or inactive. Players listed as questionable are "
                 "not counted, because most of them play."),
         "open_gap": ("⛔ COACHING CHANGES HAVE NO SOURCE IN THIS "
                      "STACK. Not approximated, not inferred from "
                      "results — recorded as missing. Nothing here "
                      "knows whether a coordinator changed.")}
    if missing:
        d["not_covered"] = missing
        d["why"] += " " + one_side_only(missing)
    return d


# ─────────────────────────────────────────────────── 8. VENUE
VENUE_COVERAGE = (
    "⚠️ THE APPARENT GAP IS NOT ONE. Measured 2026-09-17 across 285 "
    "distinct 2025 games: 193 were outdoors and 189 of those carry BOTH "
    "temperature and wind. The other 92 are domes and closed roofs, where "
    "weather is not missing — it is meaningless.")


# 🔴 SIGNAL 9 — "OPPORTUNITY CHANGE" `[Sam, 2026-09-24]` — section 9,
#    DESCRIPTIVE (research/fb_signal9_spec.md §3). The dossier combines
#    nothing: it shows what left each team and how much of it.
SECTIONS_DECLARED = 9


def _pct(x):
    return None if x is None else round(100.0 * x, 1)


def s_opportunity(home, away, this_season, week, lg, data=None, missing=None):
    import signal9
    if missing:
        # ⛔ A PAIR SECTION: with one side unknown it cannot answer at all
        return no_opponent(9, "Opportunity change", missing)
    if lg == "nfl":
        opp = signal9.load("nfl", this_season)
        if not opp:
            return unavailable(
                9, "Opportunity change",
                "The opportunity table for this season is not stored yet, so "
                "we cannot say how much of last season's work has left.",
                "it is built by the next NFL data run, which also refreshes rosters")
        wk = signal9._week(opp, week)
        teams, parts = {}, []
        for t in (home, away):
            e = (opp.get("teams") or {}).get(t)
            if not e:
                continue
            w = (e.get("weeks") or {}).get(wk) or {}
            teams[t] = {c: {"share": _pct((w.get(c) or {}).get("share")),
                            "count": (w.get(c) or {}).get("count")}
                        for c in ("tgt", "ay", "car", "i10", "combined") if c in w}
            teams[t]["off_roster_targets"] = _pct((e.get("off_roster") or {}).get("tgt"))
            teams[t]["departed"] = (e.get("departed") or [])[:3]
            teams[t]["arrivals_changed_teams"] = e.get("arrivals_changed_teams")
            tg, ca = teams[t].get("tgt") or {}, teams[t].get("car") or {}
            parts.append("%s has lost %s%% of last season's targets (%s) and %s%% of its "
                         "carries (%s)" % (t, tg.get("share"), round(tg.get("count") or 0),
                                           ca.get("share"), round(ca.get("count") or 0)))
        if not teams:
            return unavailable(9, "Opportunity change",
                               "Neither team appears in the opportunity table.", None)
        gone = [d["player"] for t in teams for d in teams[t]["departed"] if d.get("player")][:4]
        return {"n": 9, "name": "Opportunity change", "state": "OK", "basis": DESC,
                "week": wk, "teams": teams,
                "why": ("; ".join(parts) + "." + (" The biggest departures: %s." % ", ".join(gone) if gone else "")
                        + " A player on injured reserve counts as gone while he is out.")}
    # college: CFBD returning production, once stored (spec §1)
    ret = _jz(os.path.join(data or ("data/" + lg), "latest", "returning-%s.json.gz" % this_season)) or {}
    rows = {r.get("team"): r for r in ret.get("rows") or [] if isinstance(r, dict)}
    if not rows:
        return unavailable(
            9, "Opportunity change",
            "College returning production is not stored yet, so we cannot say "
            "how much of last season's work each team kept.",
            "it is fetched once per season by the next college data run, if "
            "the data service's free quota allows")
    teams, parts = {}, []
    for t in (home, away):
        r = rows.get(t)
        if not r:
            continue
        kept = {k: _pct(r.get(k)) for k in ("usage", "passingUsage", "receivingUsage", "rushingUsage")}
        teams[t] = {"returning_usage": kept}
        parts.append("%s brings back %s%% of last season's receiving work and %s%% of its "
                     "rushing" % (t, kept.get("receivingUsage"), kept.get("rushingUsage")))
    if not teams:
        return unavailable(9, "Opportunity change",
                           "Neither team appears in the returning-production table.", None)
    return {"n": 9, "name": "Opportunity change", "state": "OK", "basis": DESC,
            "teams": teams, "why": "; ".join(parts) + "."}


def s_venue(home, away, sched_row, players, this_season):
    """⛔ IT REFUSES WHEN THERE IS NO SCHEDULE ROW. `[2026-09-17]` It used
    to read OK with `venue`, `roof`, `surface`, `neutral` and `weather`
    ALL null on 19 college rows — a section that knows nothing and says
    it is fine, which is the same failure as the head-to-head sentence
    one section up. ⚠️ NFL cannot reach this: every NFL board game joins
    a schedule row (0 of 32 missing, measured), which is exactly why
    nothing caught it."""
    if not sched_row:
        return unavailable(
            8, "Venue",
            "The schedule has no row for this game yet, so we do not "
            "know where it is played or what the roof and surface are.",
            "it fills in once the game appears in the season schedule "
            "file")
    wx = None
    j = players.get(this_season)
    if j and sched_row:
        for v in (j.get("players") or {}).values():
            for r in (v.get("g") or []):
                if r.get("game_id") == sched_row.get("id"):
                    wx = r.get("wx")
                    break
            if wx:
                break
    d = {"n": 8, "name": "Venue", "state": "OK", "basis": DESC,
         "venue": (sched_row or {}).get("venue"),
         "neutral": (sched_row or {}).get("neutral"),
         "roof": (sched_row or {}).get("roof"),
         "surface": (sched_row or {}).get("surface"),
         "weather": wx,
         "coverage_note": VENUE_COVERAGE}
    indoors = (d["roof"] or (wx or {}).get("roof") or "") in ("dome", "closed")
    if wx is None and not indoors:
        d["weather_note"] = ("No weather row for this game yet — it is "
                             "carried on played games, so an upcoming "
                             "outdoor game has none until it is played.")
    elif indoors:
        d["weather_note"] = ("Indoors. Temperature and wind are not "
                             "recorded because they do not apply.")
    d["why"] = "Where it is played, and what the air was doing if outdoors."
    return d


# ───────────────────────────────────────────────────────── build
def build(league=None):
    """-> 0 on a clean write, 1 on a refusal or a missing board.

    ⚠️ THE LEAGUE IS RESOLVED AT CALL TIME, not bound at import. The
    collector runs one league per process (`LEAGUE=$lg python collect.py`),
    so the module-level default is already right — but a caller that
    imports this once and builds twice would otherwise get the first
    league's data under the second league's name, silently and looking
    correct. That is the shape `fbDetailLoad` was fixed for one file over.
    """
    lg = (league or LEAGUE or "nfl").strip().lower()
    data = os.path.join(ROOT, "data", lg)
    if lg not in LEAGUES_BUILT:
        # ⛔ AND THIS RETURNS NON-ZERO, unlike the refusal it replaces. A
        #    league nothing describes is a product hole, and a hole that
        #    exits 0 is invisible to every watcher (see LEAGUES_BUILT).
        log("dossier_fb: %s is not one of %s — nothing written, and this "
            "run FAILS so it is visible." % (lg, ", ".join(LEAGUES_BUILT)))
        return 1
    board = None
    try:
        board = json.load(open(os.path.join(data, "latest", "board.json"),
                               encoding="utf-8"))
    except Exception as e:
        log("dossier_fb: no board to describe: %s" % e)
        return 1
    resolve = team_codes(lg)
    sched = seasons("schedule", data)
    players = seasons("players", data)
    allowed = seasons("allowed-by-position", data)
    this_season = max(sched) if sched else None
    srows, sideidx = {}, {}
    for season, j in sched.items():
        for x in (j.get("games") or []):
            d = (x.get("start") or "")[:10]
            srows[(x.get("home"), x.get("away"), d)] = x
            # ⚠️ A LIST PER KEY, not a last-one-wins dict — the whole
            #    point is to SEE a second candidate rather than
            #    silently overwrite the first with it.
            for side in ("home", "away"):
                if x.get(side):
                    # ⛔ A LIST, NOT LAST-ONE-WINS. `setdefault(k, x)`
                    #    silently DISCARDS a second candidate, which is
                    #    exactly the ambiguity the refusal below exists
                    #    to notice — the guard would never have fired.
                    sideidx.setdefault((side, x[side], d), []).append(x)
    wkcal = week_calendar(sched)

    out, skipped, unresolved = [], [], []
    for g in (board.get("games") or []):
        home, away = resolve(g.get("home")), resolve(g.get("away"))
        if not home and not away:
            # ⚠️ NAMED, NEVER DROPPED. A game missing from the output and a
            #    game with nothing to say are different facts.
            skipped.append(_skip(g, "neither team name is in the code table"))
            continue
        # ══════════════════════════════════════════════════════════════
        # ⚠️ ONE SIDE IS ENOUGH TO DESCRIBE A GAME, AND ON THE COLLEGE
        # BOARD THAT IS 16 OF 88 GAMES. `teams.json` is the FBS list, so
        # an FCS opponent is absent from it — a CORRECT absence, not a
        # failure. ⛔ Dropping those games would lose 18 pct of the
        # Saturday board, and they are real games people bet.
        # ✅ So the game IS described, the unresolvable side is NAMED, and
        # the sections that need both sides report what they have and
        # nothing they do not. ⛔ The name is never guessed at.
        # ══════════════════════════════════════════════════════════════
        # ⛔ THE BOARD'S OWN NAME FOR THE SIDE THAT DOES NOT RESOLVE.
        #    The board is complete — 0 missing home, away or id across
        #    all 88 — so this is never None, and every section that
        #    declines can say WHO it declined over.
        missing = None
        if not (home and away):
            missing = g.get("home") if not home else g.get("away")
            unresolved.append({"away": g.get("away"), "home": g.get("home"),
                               "not_in_table": missing})
        kick = None
        try:
            kick = datetime.datetime.strptime((g.get("commence") or "")[:10],
                                              "%Y-%m-%d")
        except ValueError:
            pass
        # ══════════════════════════════════════════════════════════════
        # 🔴🔴 THE 19 GAMES WITH "NO SCHEDULE ROW" WERE A FAILED JOIN, NOT
        # AN ABSENT ROW. `[measured 2026-09-18]` 17 of the 19 ARE in
        # `schedule-2026.json.gz`, carrying their week, venue, roof and
        # surface — and the pair key could never match them, because it
        # is built from the RESOLVED code on both sides and the away side
        # is an FCS school that resolves to `None`.
        # ⚠️ The schedule holds that school's name perfectly well
        # ("Portland State", "Mercer", "Maine"). It is the FBS-only TEAM
        # LIST that does not — the same reference-set-narrower-than-the-
        # board class task 27 fixed for the opponent, one join over.
        # ✅ SO: the exact pair first, then ONE SIDE PLUS THE DATE.
        # ⛔ UNIQUE OR NOTHING. Measured across 4 stored schedules, 8,063
        # of 8,065 (team, date) keys hold exactly one game and the two
        # that do not are a Division III fixture duplicated under two
        # ids. A key that is unique 99.98% of the time is not a key you
        # may assume, so a second candidate REFUSES rather than picking
        # one — `resolve()`'s rule, one file over.
        # ══════════════════════════════════════════════════════════════
        row, row_basis = None, None
        for (h, a, d), x in srows.items():
            if h == home and a == away and _near(d, kick):
                row, row_basis = x, "the home team, the away team and the date"
                break
        if row is None and kick:
            for side, code in (("home", home), ("away", away)):
                if not code:
                    continue
                cand = [x for (k, c, d), v in sideidx.items()
                        if k == side and c == code and _near(d, kick)
                        for x in v]
                if len(cand) == 1:
                    row = cand[0]
                    row_basis = ("the %s team and the date — the other "
                                 "side is not in the top-division team "
                                 "list, so the pair could not be matched"
                                 % side)
                    break
                if len(cand) > 1:
                    row_basis = ("REFUSED: %d schedule rows share this %s "
                                 "team and date, and this project does "
                                 "not pick the first match"
                                 % (len(cand), side))
                    break
        week = (row or {}).get("week")
        # ⚠️ AND WHEN THERE IS STILL NO ROW, THE WEEK IS DERIVED FROM THE
        #    SEASON CALENDAR — which places a date or refuses to.
        week_basis = "the schedule row for this game" if week is not None else None
        if week is None and kick:
            week = wkcal.get(kick.strftime("%Y-%m-%d"))
            if week is not None:
                week_basis = ("the season calendar — this game has no "
                              "schedule row, and the stored schedule "
                              "places %s in week %d"
                              % (kick.strftime("%Y-%m-%d"), week))
        # ⛔ NO None IN THE TEAM LIST. It published a literal `"null"` key
        #    inside `by_team` on 19 college rows.
        teams = [t for t in (home, away) if t]
        out.append({
            # ══════════════════════════════════════════════════════════
            # 🔴🔴 TWO IDS, EACH NAMED FOR WHERE IT CAME FROM.
            # ⛔ THEY ARE DIFFERENT NAMESPACES AND NEITHER IS THE OTHER.
            # `game_id` is the SEASON SCHEDULE's id — nflverse
            # `2026_02_DET_BUF` for NFL, a CFBD integer for college — and
            # sections 2, 3 and 4 are built from it. `board_id` is the
            # ODDS FEED's own hash, e.g. `0283a29e1b38ef78b29b904fd56a16dd`.
            # ⚠️ MEASURED 2026-09-17 on the live NFL artifact: **0 of 32**
            # dossier `game_id`s appear anywhere in `board.json`. A page
            # given only `game_id` cannot join to the board at all.
            # ⛔ AND IT MUST NEVER JOIN ON TEAM NAMES OR ON KICKOFF TIME.
            # CLAUDE.md: "Two legs are in different games only if the GAME
            # ID differs. Never compare opponent names" — a live MLB card
            # shipped four impossible parlays that way. Matching on time
            # is `boardFor()`'s nearest-first-pitch problem, and doing it
            # in JavaScript would be a second copy of it in a second
            # language, which is exactly how the wrong-game bug shipped.
            # ✅ SO THE JOIN KEY IS PUT HERE, IN THE BUILDER, which already
            # holds the board row. The page then joins on one exact key
            # and infers nothing.
            # ══════════════════════════════════════════════════════════
            "board_id": g.get("id"),
            "game_id": (row or {}).get("id"),
            # ⚠️ WHERE EACH CAME FROM, SAID ON THE ROW. `[2026-09-18]`
            # A week matched off a schedule row and a week placed by the
            # season calendar are both correct and they are not the same
            # claim, and a row joined on ONE side plus the date is a
            # weaker join than one matched on the pair. ⛔ A number with
            # no provenance beside it gets read as the strongest reading
            # available — rule 55's habit, applied to a join.
            "row_basis": row_basis,
            "week_basis": week_basis,
            "away": away, "home": home,
            # ⛔ ALWAYS THE BOARD'S OWN STRINGS, resolved or not. A game
            #    the reader can name must never render as None.
            "away_name": g.get("away"), "home_name": g.get("home"),
            # ⚠️ AND THE GAP IS ON THE FRAME, not only in the document's
            #    `one_sided` list — a consumer reading one row must not
            #    have to cross-reference another key to learn that half
            #    of it is missing.
            "unresolved_side": missing,
            "commence": g.get("commence"), "week": week,
            "season": this_season,
            "kind": "DOSSIER",
            "note": ("Nine checks, run in order, for every game on the "
                     "board. ⛔ Nothing here is combined, ranked or "
                     "scored — that would be a model, and a model needs a "
                     "pre-registered test. Every number is labelled "
                     "MARKET or DESCRIPTIVE; none is MODEL."),
            # ⚠️ §1 STAYS OK ON THESE ROWS, deliberately. The market is
            #    real, it is the one thing we genuinely know, and the
            #    game is on the board for Sam to bet. ⛔ The refusal is
            #    per SECTION, never the whole game.
            "sections": [
                s_market(g, row),
                s_h2h(home, away, kick, sched, missing),
                s_time_of_year(teams, week, players, this_season, missing,
                               kick.strftime("%Y-%m-%d") if kick else None),
                s_this_season(teams, players, this_season, week, missing),
                s_vs_position(home, away, allowed, this_season, missing),
                s_possession(home, away, this_season, data, missing,
                             kick.strftime("%Y-%m-%d") if kick else None),
                s_personnel(teams, players, this_season, missing, week, lg),
                s_venue(home, away, row, players, this_season),
                s_opportunity(home, away, this_season, week, lg, data, missing),
            ]})

    doc = {"kind": "DOSSIER", "league": lg, "season": this_season,
           "built_at": datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "n_board_games": len(board.get("games") or []),
           # ══════════════════════════════════════════════════════════
           # ⚠️ WHAT THESE TWO NUMBERS MEAN, SAID OUT LOUD.
           # `n_dossiers` = games this file DESCRIBES. It is not a
           # coverage claim: "88 of 88" read as full coverage while 19
           # of those rows had no identified opponent, which is the
           # defect this comment exists because of. `n_partial` is the
           # subset where one side does not resolve — described, with
           # every pair-wise section refusing by name.
           # ══════════════════════════════════════════════════════════
           "n_dossiers": len(out),
           "n_partial": len(unresolved),
           "counts_note": ("`n_dossiers` counts games DESCRIBED, not "
                           "games fully answered. `n_partial` of them "
                           "have one side the season files do not cover, "
                           "so every section comparing the two reads "
                           "UNAVAILABLE and says which side is missing."),
           "skipped": skipped,
           # ⚠️ REPORTED, NOT HIDDEN. These games ARE described; one side
           # is a lower-division school absent from the top-division
           # table, so the sections needing both sides REFUSE BY NAME.
           # Naming them is how a reader knows which half is missing.
           "one_sided": unresolved,
           "sections_declared": SECTIONS_DECLARED,   # was a literal 8; derived since section 9 (2026-09-24)
           "note": ("⛔ A REPORT, NOT A MODEL. No combined score, no "
                    "ranking, no confidence. Every section is present or "
                    "explicitly UNAVAILABLE with its reason."),
           "dossiers": out}
    # 🔴🔴 THE GATE. ⛔ NOTHING IS WRITTEN IF THE DOCUMENT CARRIES A
    #    JUDGEMENT. A report that scores a game is a model, and a model
    #    needs a pre-registered test this artifact does not have.
    bad, carried_absent = audit(doc)
    if carried_absent:
        # ⚠️ REPORTED, NOT REFUSED. ~~`return 1`~~ STRUCK 2026-09-19: a
        #    `CARRIED` name is absent when the SLATE has nothing of that
        #    kind — no prior meeting, no live game, no weather indoors —
        #    and refusing on it wrote NOTHING to the football tabs on a
        #    board that was entirely fine.
        # ✅ It goes ON THE DOCUMENT so a reader can see which source
        #    subtrees this slate carried, and `test_dossier_coverage.py`
        #    checks the exception surface against this file's own AST,
        #    which is the question the refusal was reaching for.
        doc["carried_absent"] = carried_absent
        log("dossier_fb: ⚠️ this slate carries no %s subtree — reported "
            "on the document, not a refusal" % carried_absent)
    if bad:
        log("dossier_fb: ⛔ REFUSING TO WRITE — the document carries %d "
            "numeric judgement field(s), and this artifact combines, "
            "ranks and scores NOTHING: %s"
            % (len(bad), [(p_, v) for p_, _k, v in bad[:6]]))
        return 1
    p = os.path.join(data, "latest", "dossiers.json.gz")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with gzip.open(p, "wt") as fh:
        json.dump(doc, fh)
    # ══════════════════════════════════════════════════════════════════
    # 🔴🔴 AND A DATED, WRITE-ONCE COPY. `[2026-09-17]`
    # ⛔ `latest/` IS OVERWRITTEN ON EVERY ONE OF THE EIGHT DAILY
    # `card-fb` ARMS, so until this existed the file kept NO history at
    # all and every day that passed was observations nobody could ever
    # recover.
    # ⚠️ EVERY SECTION HERE IS A POINT-IN-TIME READING — the market's
    # numbers move, the season-to-date rows grow, a section flips from
    # UNAVAILABLE to OK. A report with no archive cannot be checked
    # against what actually happened.
    #
    # 🔴 THE WRITER ITSELF NOW LIVES IN `daystore.py`. `[moved 2026-09-17]`
    # ⛔ `shadow_fb.py` needs exactly this behaviour the next day, and a
    # second copy of a write-once rule is a second thing to drift — rule
    # 117, which this repo has paid for five times. The measurement that
    # justifies dated-over-cumulative (560x, ledger rule 285) travels
    # with the code rather than being restated here.
    # ══════════════════════════════════════════════════════════════════
    arch, _wrote = daystore.archive(doc, data, "dossiers", log=log)
    un = collections.Counter(
        s["name"] for d in out for s in d["sections"]
        if s["state"] == "UNAVAILABLE")
    # ⛔ THE PARTIAL COUNT RIDES IN THE SAME LINE AS THE TOTAL.
    #    "88 of 88" on its own reads as full coverage, and on the day
    #    this was found 19 of those 88 had no identified opponent. A
    #    number that overstates what was answered is worse in a log than
    #    in a file, because the log is what a watcher reads.
    log("dossier_fb[%s]: %d of %d board game(s) described%s -> %s "
        "(archived %s)%s"
        % (lg, len(out), doc["n_board_games"],
           (", %d of them PARTIAL (opponent not in the top-division "
            "team list: %s)"
            % (len(unresolved),
               ", ".join(sorted(x["not_in_table"] for x in unresolved)[:4])
               + (" +%d more" % (len(unresolved) - 4)
                  if len(unresolved) > 4 else "")))
           if unresolved else "",
           p, arch,
           ("; unavailable sections: %s" % dict(un)) if un else ""))
    if skipped:
        log("  ⚠️ %d game(s) skipped and named in the file: %s"
            % (len(skipped), [s["home"] for s in skipped]))
    return 0


if __name__ == "__main__":
    sys.exit(build())
