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
# source data — and `audit()` refuses to run if one of those names has
# stopped appearing, so the exception surface cannot be padded with junk
# to silence a finding.
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
    missing = [c for c in CARRIED if c not in seen_carried]
    return found, missing


def log(m):
    print("[%s] %s" % (datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"), m))


def _jz(path):
    try:
        return json.load(gzip.open(path, "rt"))
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
    d["known_gap"] = ("FIRST-HALF MARKETS ARE NOT HELD. No field matching "
                      "`half` or `1h` exists anywhere in the stored "
                      "schedule, and none is invented here.")
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
def s_time_of_year(teams, week, players, this_season, missing=None):
    """What these teams and players did in THIS week number before.

    ⚠️ PER TEAM, so one resolvable side is a real half-answer — but it
    SAYS which half is missing. ⛔ And `teams` never carries a None:
    `build()` filters it, because a None in this list published a
    literal `"null"` key inside `by_team` on 19 college rows.
    """
    if not week:
        return unavailable(3, "Time of year",
                           "The schedule does not give this game a week "
                           "number, so there is nothing to compare against.")
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
    out = {}
    for t in (home, away):
        d = defs.get(t)
        if not d:
            continue
        out[t] = {pos: {k: v for k, v in (d.get(pos) or {}).items()
                        if k.endswith("_rank") or k.endswith("_pct")
                        or k == "games"}
                  for pos in sorted(d)}
    if not out:
        return unavailable(5, "Versus position",
                           "Neither %s nor %s appears in the "
                           "allowed-by-position file." % (home, away))
    return {"n": 5, "name": "Versus position", "state": "OK", "basis": DESC,
            "season": j.get("season"), "by_defence": out,
            "scale": j.get("rank_note") or "rank 1 = ALLOWS THE MOST",
            "verdict": VS_VERDICT,
            "why": ("How each defence has been scored on by position, "
                    "ranked across the league. " + VS_VERDICT)}


# ──────────────────────────────────────── 6. TIME OF POSSESSION
def s_possession(home, away, this_season, data=None, missing=None):
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
            return unavailable(
                6, "Time of possession",
                "Not enough college games have been played yet. College "
                "possession is worked out from the game clock rather than "
                "read off a stat sheet, and it needs about 80 teams' worth "
                "of well-timed games before it is worth showing — that is "
                "roughly the fourth week of the season, and this is the "
                "third.",
                "it starts filling in on its own once a few more weekends "
                "have been played")
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
    for t in (home, away):
        v = by.get(t)
        if not v or v.get("share") is None:
            continue
        spg = int(v.get("seconds_per_game") or round(v["share"] * 3600))
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
def s_personnel(teams, players, this_season, missing=None):
    """⚠️ PER TEAM, and it names the side it covers nothing for."""
    j = players.get(this_season)
    if not j:
        return unavailable(7, "Personnel",
                           "No player file for %d yet." % this_season)
    out = {}
    for t in teams:
        latest = {}
        for pid, v in (j.get("players") or {}).items():
            rows = [r for r in (v.get("g") or []) if r.get("team") == t]
            if not rows:
                continue
            r = sorted(rows, key=lambda x: x.get("week") or 0)[-1]
            if any(r.get(k) for k in ("inj", "ol_out", "opp_dl_out",
                                      "ahead_out")):
                latest[v.get("name") or pid] = {
                    "week": r.get("week"), "inj": r.get("inj"),
                    "ol_out": r.get("ol_out"),
                    "opp_dl_out": r.get("opp_dl_out"),
                    "ahead_out": r.get("ahead_out")}
        out[t] = latest
    d = {"n": 7, "name": "Personnel", "state": "OK", "basis": DESC,
         "by_team": out,
         "flagged": sum(len(v) for v in out.values()),
         "why": ("Availability flags carried on each player's most "
                 "recent game row: his own injury designation, line "
                 "absences, opposing line absences, and whether the "
                 "man ahead of him was out."),
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
    srows = {}
    for season, j in sched.items():
        for x in (j.get("games") or []):
            srows[(x.get("home"), x.get("away"), (x.get("start") or "")[:10])] = x

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
        row = None
        for (h, a, d), x in srows.items():
            if h == home and a == away and kick and abs(
                    (datetime.datetime.strptime(d, "%Y-%m-%d")
                     - kick).days) <= 1:
                row = x
                break
        week = (row or {}).get("week")
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
            "note": ("Eight checks, run in order, for every game on the "
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
                s_time_of_year(teams, week, players, this_season, missing),
                s_this_season(teams, players, this_season, week, missing),
                s_vs_position(home, away, allowed, this_season, missing),
                s_possession(home, away, this_season, data, missing),
                s_personnel(teams, players, this_season, missing),
                s_venue(home, away, row, players, this_season),
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
           "sections_declared": 8,
           "note": ("⛔ A REPORT, NOT A MODEL. No combined score, no "
                    "ranking, no confidence. Every section is present or "
                    "explicitly UNAVAILABLE with its reason."),
           "dossiers": out}
    # 🔴🔴 THE GATE. ⛔ NOTHING IS WRITTEN IF THE DOCUMENT CARRIES A
    #    JUDGEMENT. A report that scores a game is a model, and a model
    #    needs a pre-registered test this artifact does not have.
    bad, missing_carried = audit(doc)
    if missing_carried:
        # ⚠️ THE EXCEPTION SURFACE HAS TO BE REAL. If a name in `CARRIED`
        #    no longer appears, the walk is skipping a subtree that is not
        #    there — which means it could be skipping one that is.
        log("dossier_fb: ⛔ REFUSING TO WRITE — these carried-subtree "
            "names no longer appear in the output, so the audit's "
            "exception list is stale: %s" % missing_carried)
        return 1
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
