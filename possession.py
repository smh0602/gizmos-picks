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
        # ⛔ THE GAME IS WITHHELD, NOT THE TEAM. See the header.
        if tot <= 0 or tot / float(GAME_CLOCK_SECS) < COVERAGE_MIN:
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
            a["shares"].append(secs / float(tot))
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
