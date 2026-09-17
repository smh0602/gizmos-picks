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

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUE = os.environ.get("LEAGUE", "nfl")
DATA = os.path.join(ROOT, "data", LEAGUE)

MARKET, DESC = "MARKET", "DESCRIPTIVE"
H2H_DAYS = 365          # ⚠️ "within 1 year" — the brief's own bound
MAX_PLAYERS = 8         # per team, by trailing snap share. Capped and SAID.


def log(m):
    print("[%s] %s" % (datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"), m))


def _jz(path):
    try:
        return json.load(gzip.open(path, "rt"))
    except Exception:
        return None


def team_codes():
    """Full team name -> nflverse abbreviation.

    ⛔ READ OUT OF `collect.py`'s SOURCE, never retyped. That file's own
    comment says "if you edit one side, edit both", and a second copy of a
    32-row table is a second thing to drift (rule 66). ⚠️ Parsed rather
    than imported: importing the collector runs its module-level league
    handling, and a reporting tool must not be able to trip that.
    """
    src = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
    for n in ast.parse(src).body:
        if (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "")
                == "NFL_TEAMS"):
            return ast.literal_eval(n.value)
    return {}


def seasons(kind):
    """{season: payload} for every `<kind>-<year>.json.gz` on disk."""
    out = {}
    for p in sorted(glob.glob(os.path.join(DATA, "latest",
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
def s_h2h(home, away, kick, sched):
    """Prior meetings inside one year. ⚠️ n is 1-2 and it says so."""
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
def s_time_of_year(teams, week, players, this_season):
    """What these teams and players did in THIS week number before."""
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
    return {"n": 3, "name": "Time of year", "state": "OK", "basis": DESC,
            "week": week, "by_team": per_team, "by_player": per_player,
            "why": ("Week %d in earlier seasons, from the same player-game "
                    "rows the board is built on. ⚠️ Capped at %d players a "
                    "team by row count — it is a sample of the week, not a "
                    "roster." % (week, MAX_PLAYERS))}


# ──────────────────────────────────────────────── 4. THIS SEASON
def s_this_season(teams, players, this_season, week):
    """Trailing form — the same rows the model already reads."""
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
    return {"n": 4, "name": "This season", "state": "OK", "basis": DESC,
            "season": this_season, "through_week": week, "by_team": out,
            "why": ("The last four games each, by trailing snap share. "
                    "⚠️ This is the model's own input shown as a record; "
                    "it is not a second estimate of anything.")}


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


def s_vs_position(home, away, allowed, this_season):
    j = allowed.get(this_season) or allowed.get(this_season - 1)
    if not j:
        return unavailable(5, "Versus position",
                           "No allowed-by-position file on disk.",
                           "the collector's `nfl-logs` mode writes it")
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
def s_possession(home, away, this_season):
    """⚠️ PROBED, NOT ASSUMED. See the module header."""
    top = _jz(os.path.join(DATA, "latest", "top-%d.json.gz" % this_season))
    if not top:
        return unavailable(
            6, "Time of possession",
            "PROBED 2026-09-17 and the column EXISTS: "
            "`drive_time_of_possession` is one of 372 columns in "
            "`play_by_play_2025.csv.gz`, populated on 2457 of 2491 "
            "sampled plays, formatted M:SS. ⛔ But that file is "
            "downloaded by the collector and discarded — nothing under "
            "`data/` carries possession, so there is nothing to report "
            "from here. The field is confirmed; the artifact is not.",
            "persist a per-team `top-<season>.json.gz` from the "
            "play-by-play the collector already downloads")
    by = top.get("teams") or {}
    out = {t: by[t] for t in (home, away) if t in by}
    if not out:
        return unavailable(6, "Time of possession",
                           "A possession file exists but carries neither "
                           "%s nor %s." % (home, away))
    return {"n": 6, "name": "Time of possession", "state": "OK",
            "basis": DESC, "by_team": out,
            "why": "Mean drive time of possession, from the play-by-play."}


# ─────────────────────────────────────────────── 7. PERSONNEL
def s_personnel(teams, players, this_season):
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
    return {"n": 7, "name": "Personnel", "state": "OK", "basis": DESC,
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


# ─────────────────────────────────────────────────── 8. VENUE
VENUE_COVERAGE = (
    "⚠️ THE APPARENT GAP IS NOT ONE. Measured 2026-09-17 across 285 "
    "distinct 2025 games: 193 were outdoors and 189 of those carry BOTH "
    "temperature and wind. The other 92 are domes and closed roofs, where "
    "weather is not missing — it is meaningless.")


def s_venue(home, away, sched_row, players, this_season):
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
def build():
    if LEAGUE != "nfl":
        # ⛔ NFL FIRST, and a half-built college dossier is worse than
        #    none: it would look complete and describe a different sport's
        #    data shape. Explicit, not silent.
        log("dossier_fb: %s is not built yet — NFL only. Nothing written."
            % LEAGUE)
        return 0
    board = None
    try:
        board = json.load(open(os.path.join(DATA, "latest", "board.json"),
                               encoding="utf-8"))
    except Exception as e:
        log("dossier_fb: no board to describe: %s" % e)
        return 1
    codes = team_codes()
    sched = seasons("schedule")
    players = seasons("players")
    allowed = seasons("allowed-by-position")
    this_season = max(sched) if sched else None
    srows = {}
    for season, j in sched.items():
        for x in (j.get("games") or []):
            srows[(x.get("home"), x.get("away"), (x.get("start") or "")[:10])] = x

    out, skipped = [], []
    for g in (board.get("games") or []):
        home, away = codes.get(g.get("home")), codes.get(g.get("away"))
        if not home or not away:
            # ⚠️ NAMED, NEVER DROPPED. A game missing from the output and a
            #    game with nothing to say are different facts.
            skipped.append(_skip(g, "team name not in the code table"))
            continue
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
        teams = [home, away]
        out.append({
            "game_id": (row or {}).get("id"),
            "away": away, "home": home,
            "away_name": g.get("away"), "home_name": g.get("home"),
            "commence": g.get("commence"), "week": week,
            "season": this_season,
            "kind": "DOSSIER",
            "note": ("Eight checks, run in order, for every game on the "
                     "board. ⛔ Nothing here is combined, ranked or "
                     "scored — that would be a model, and a model needs a "
                     "pre-registered test. Every number is labelled "
                     "MARKET or DESCRIPTIVE; none is MODEL."),
            "sections": [
                s_market(g, row),
                s_h2h(home, away, kick, sched),
                s_time_of_year(teams, week, players, this_season),
                s_this_season(teams, players, this_season, week),
                s_vs_position(home, away, allowed, this_season),
                s_possession(home, away, this_season),
                s_personnel(teams, players, this_season),
                s_venue(home, away, row, players, this_season),
            ]})

    doc = {"kind": "DOSSIER", "league": LEAGUE, "season": this_season,
           "built_at": datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "n_board_games": len(board.get("games") or []),
           "n_dossiers": len(out),
           "skipped": skipped,
           "sections_declared": 8,
           "note": ("⛔ A REPORT, NOT A MODEL. No combined score, no "
                    "ranking, no confidence. Every section is present or "
                    "explicitly UNAVAILABLE with its reason."),
           "dossiers": out}
    p = os.path.join(DATA, "latest", "dossiers.json.gz")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with gzip.open(p, "wt") as fh:
        json.dump(doc, fh)
    un = collections.Counter(
        s["name"] for d in out for s in d["sections"]
        if s["state"] == "UNAVAILABLE")
    log("dossier_fb[%s]: %d of %d board game(s) -> %s%s"
        % (LEAGUE, len(out), doc["n_board_games"], p,
           ("; unavailable sections: %s" % dict(un)) if un else ""))
    if skipped:
        log("  ⚠️ %d game(s) skipped and named in the file: %s"
            % (len(skipped), [s["home"] for s in skipped]))
    return 0


if __name__ == "__main__":
    sys.exit(build())
