#!/usr/bin/env python3
"""
POSSESSION IS A SHARE, NOT A COUNT OF SECONDS. ONE IMPLEMENTATION, BOTH
LEAGUES.

🔴🔴 THE DEFECT THIS EXISTS FOR `[measured 2026-09-17]`. The first CFB
builder emitted RAW DERIVED SECONDS per team. ⛔ Raw seconds are not
comparable between games, because the derivation observes a different
FRACTION of each game's clock. Measured over the whole 2019 season in
`research/cfb_clock_sample_2019.json.gz`, 887 games:

    CLOCK COVERAGE per game (two-team derived total / 3600)
      min 0.30   p10 0.68   p25 0.75   median 0.87   p90 0.99   max 1.01

That spread lands straight on the per-team number:

    217 teams          raw seconds   league mean 24:56   <- should be 30:00
                       share x 3600  league mean 29:51   <- right by construction
      mean |raw - share|  295s      max 1053s
      teams differing by > 60s      202 of 217
      correlation raw vs share      r = +0.6426

⛔ IT DOES NOT ADD NOISE, IT INVERTS RANKINGS. Nicholls reads 21:00 in raw
seconds — near the bottom of the board — against a real share of 38:33,
near the very top. Towson 10:43 against 26:30. Monmouth 19:20 against
34:21.

✅ **SHARE IS IMMUNE TO COVERAGE BY CONSTRUCTION.** Whatever fraction of
the clock a game exposes, the two teams' shares of that fraction still sum
to 1. So the quantity the page and any future model read is the share, and
seconds stay in the payload as the honest raw material they are.

⚠️ AND THE SHARE IS AVERAGED PER GAME, NOT SEASON-TOTAL ÷ SEASON-TOTAL.
A season-total ratio re-imports the same weighting: a team's well-observed
games would count for more than its poorly-observed ones, which is the
bias this whole module exists to remove, one level up.

══════════════════════════════════════════════════════════════════════
🔴 WHY 0.90, AND WHY IT IS A DERIVATION RATHER THAN A TASTE
══════════════════════════════════════════════════════════════════════
A share estimated from a fraction `c` of the clock has a WORST-CASE error
of `1 - c`: every unobserved second could belong to either team. So the
floor is not chosen, it is read off the error you are willing to carry —

    worst-case share error  <=  0.10   ->   coverage floor 0.90
    0.10 of a share is +/- 3:00 of a 60:00 game.

⛔ AND IT WITHHOLDS A GAME, NOT A TEAM. Dropping a team keeps the games it
played in and silently reweights its opponent; dropping the game removes
both sides of one observation, which is what "this game was not observed
well enough" actually means.

⚠️ WHAT IT COSTS, MEASURED, so nobody has to guess later:
    CFB 2019   403 of 887 games kept (45 pct), 160 teams still covered
    NFL 2025   269 of 269 regulation games kept — the floor removes
               NOTHING there, because recorded drive times cover the
               whole clock. ✅ One rule, and it only bites where the
               data actually is thin.

⛔ THERE IS NO CEILING, AND THAT IS DELIBERATE. A game whose parts sum to
slightly MORE than the clock (CFB max 1.01, one NFL game at 3908s) is an
over-count in the source — but share is scale-free, so it moves the answer
by nothing. A ceiling would throw away a usable observation to guard
against an error it does not cause.
"""

GAME_CLOCK_SECS = 3600          # four periods of fifteen minutes, both codes
COVERAGE_MIN = 0.90             # derived above; do not round it off
MIN_GAMES_PER_TEAM = 1          # a team with no eligible game is absent, not zero


def coverage(per_team_seconds):
    """Two-team derived total / the game clock. ⚠️ May exceed 1.0."""
    return sum(per_team_seconds.values()) / float(GAME_CLOCK_SECS)


def game_shares(per_team_seconds):
    """{team: secs} for ONE game -> {team: share}, or None if withheld.

    ✅ THE ONE PER-GAME FORMULA. `share_table` averages these and
    `per_game_rows` stores them, and both call HERE, so the season table
    and the per-game history cannot disagree about a single game (rule 66:
    two routes to one number is two numbers).
    """
    tot = sum((per_team_seconds or {}).values())
    # ⛔ THE GAME IS WITHHELD, NOT THE TEAM. See the header.
    if tot <= 0 or tot / float(GAME_CLOCK_SECS) < COVERAGE_MIN:
        return None
    return {team: secs / float(tot) for team, secs in per_team_seconds.items()}


# ══════════════════════════════════════════════════════════════════════
# 🔴 SIGNAL 6, PER GAME — AND "BEFORE KICKOFF" IS ENFORCED HERE, ONCE.
# ══════════════════════════════════════════════════════════════════════
# `[Sam, 2026-09-23]` "store every team's time-of-possession share for each
# game already played ... A game's 'share before kickoff' must be built
# only from that team's earlier games."
# ⛔ The season table (`share_table`) is a season-to-date number: read for a
#    game INSIDE that season it contains games played AFTER that kickoff,
#    which is lookahead. That is why T60R had to leave signal 6 switched off
#    (research/t60r_investigation.md, section 1). The per-game rows below
#    are the missing source, and `share_before` is the only reader that may
#    turn them into a pre-kickoff number.
def per_game_rows(per_game, drives_per_game, dates):
    """-> {gid: {"date", "coverage", "withheld", "teams": {team: {...}}}}.

    ⚠️ A WITHHELD GAME IS KEPT, MARKED, WITH NO SHARES: it happened, and
    dropping it would make "no possession stored" and "never played" look
    the same. ⚠️ An UNDATED game is kept with `date: None`; `share_before`
    cannot place it in time and therefore never uses it.
    """
    out = {}
    for gid, tt in per_game.items():
        if not tt:
            continue
        sh = game_shares(tt)
        out[str(gid)] = {
            "date": (dates or {}).get(gid) or (dates or {}).get(str(gid)),
            "coverage": round(coverage(tt), 4),
            "withheld": sh is None,
            "teams": {team: {"share": (round(sh[team], 4) if sh else None),
                             "seconds": int(secs),
                             "drives": int((drives_per_game.get(gid) or {})
                                           .get(team, 0))}
                      for team, secs in sorted(tt.items())},
        }
    return out


def share_before(games, team, kickoff_date):
    """The team's mean per-game share over games dated BEFORE kickoff.

    -> {"share": float|None, "games": n, "withheld": w, "undated": u}

    ⛔ STRICTLY EARLIER, by calendar date. A team does not play twice in a
    day, so `date < kickoff_date` is exactly "its earlier games" — and a
    game on the kickoff date itself (the game being asked about) can never
    be counted. ⛔ No fallback to the season table: if nothing earlier is
    stored the answer is None, never a number that saw the future.
    """
    k = str(kickoff_date or "")[:10]
    shares, withheld, undated = [], 0, 0
    if not k:
        return {"share": None, "games": 0, "withheld": 0, "undated": 0}
    for g in (games or {}).values():
        t = (g.get("teams") or {}).get(team)
        if t is None:
            continue
        d = g.get("date")
        if not d:
            undated += 1
            continue
        if str(d)[:10] >= k:
            continue
        if g.get("withheld") or t.get("share") is None:
            withheld += 1
            continue
        shares.append(t["share"])
    return {"share": (round(sum(shares) / len(shares), 4) if shares else None),
            "games": len(shares), "withheld": withheld, "undated": undated}


def share_table(per_game, drives_per_game, log=print):
    """{gid: {team: secs}} + {gid: {team: drives}} -> (teams, report).

    ✅ THE ONE PLACE EITHER LEAGUE TURNS OBSERVED SECONDS INTO A NUMBER
    ANYTHING MAY READ. ⛔ Not copied into `nfl.py` and `cfb.py` — rule
    117: a helper duplicated breaks in the file you did not edit, and
    "both leagues emit the same shape" should be true BY CONSTRUCTION
    rather than by a test that compares two separate implementations.
    """
    rep = {"games_seen": len(per_game), "games_withheld": 0,
           "coverage_min": None, "coverage_p10": None,
           "coverage_median": None, "coverage_max": None,
           "coverage_floor": COVERAGE_MIN}
    covs = sorted(coverage(t) for t in per_game.values() if t)
    if covs:
        def q(p):
            return round(covs[int(p * (len(covs) - 1))], 4)
        rep.update({"coverage_min": round(covs[0], 4), "coverage_p10": q(0.10),
                    "coverage_median": q(0.50),
                    "coverage_max": round(covs[-1], 4)})

    agg = {}
    for gid, tt in per_game.items():
        if not tt:
            continue
        tot = sum(tt.values())
        # ⛔ THE GAME IS WITHHELD, NOT THE TEAM — decided by `game_shares`,
        #    the one per-game formula, so this table and the per-game rows
        #    cannot disagree about which games count.
        sh = game_shares(tt)
        if sh is None:
            rep["games_withheld"] += 1
            continue
        for team, secs in tt.items():
            a = agg.setdefault(team, {"games": 0, "seconds": 0, "drives": 0,
                                      "clock": 0, "shares": []})
            a["games"] += 1
            a["seconds"] += secs
            # ⚠️ THE TEAM'S OBSERVED CLOCK, kept so the season-total ratio
            # can be REPORTED beside the per-game mean rather than argued
            # about. ⛔ It is not what `share` is computed from.
            a["clock"] += tot
            a["drives"] += (drives_per_game.get(gid) or {}).get(team, 0)
            # ⚠️ ONE SHARE PER GAME, AVERAGED BELOW. Never a ratio of the
            # season totals — see the header.
            a["shares"].append(sh[team])
    rep["games_used"] = rep["games_seen"] - rep["games_withheld"]

    teams = {}
    for team, a in sorted(agg.items()):
        if a["games"] < MIN_GAMES_PER_TEAM or not a["shares"]:
            continue
        # ⚠️ ROUNDED ONCE, HERE. `seconds_per_game` is derived from the
        # rounded value so the two can never disagree — rule 66: two
        # routes to one number is two numbers.
        share = round(sum(a["shares"]) / len(a["shares"]), 4)
        teams[team] = {
            # ✅ THE FIELD ANYTHING READS.
            "share": share,
            "seconds_per_game": int(round(share * GAME_CLOCK_SECS)),
            # ⚠️ DIAGNOSTICS, AND HONEST RAW MATERIAL — but not comparable
            # between teams, because each team's games were observed to a
            # different depth. ⛔ Nothing on the page reads these.
            "games": int(a["games"]),
            "drives": int(a["drives"]),
            "seconds": int(a["seconds"]),
            "seconds_per_drive": (int(round(a["seconds"] / a["drives"]))
                                  if a["drives"] else 0),
        }
    rep["teams"] = len(teams)
    # ⚠️ REPORTED SO THE CHOICE IS VISIBLE, NEVER USED. `share` above is
    # the mean of the per-game shares; this is what season-total ÷
    # season-total would have given. They differ whenever a team's games
    # were observed to different depths, which is the whole reason the
    # per-game mean is the one that ships.
    _pooled = {t: (agg[t]["seconds"] / float(agg[t]["clock"]))
               for t in teams if agg[t]["clock"]}
    if _pooled:
        _d = [abs(teams[t]["share"] - _pooled[t]) for t in _pooled]
        rep["pooled_vs_per_game_max_diff"] = round(max(_d), 4)
        rep["pooled_vs_per_game_mean_diff"] = round(sum(_d) / len(_d), 4)
    return teams, rep
