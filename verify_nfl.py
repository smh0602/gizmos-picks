"""VERIFY THE FOOTBALL DATA LAYER — the checks MLB has and football did not.

🔴 WHY THIS EXISTS. MLB has four verifiers and between them they caught a
projection incoherence, a fabricated innings value, a miscounted market
split and a whole day of stale props. **Football had NONE, and it had
already shipped a CONSTANT-ZERO COLUMN ON A GREEN RUN** — `ahead_out` was
0 on all 19,400 player-weeks because a player who is OUT has no stat row
for his injury to attach to. Nothing failed. Nothing warned.

⛔ THE RULE: A GREEN RUN IS NOT A VERIFIED RUN.

Usage:  python verify_nfl.py [season ...]
"""
import collections, glob, gzip, json, os, re, sys

FAIL, WARN, PASS, NYM = [], [], [], []
BASE = "data/nfl/latest"
PROP_POS = {"QB", "RB", "WR", "TE", "FB"}
SNAP_FLOOR = {"QB": 0.60, "RB": 0.30, "WR": 0.50, "TE": 0.40, "FB": 0.30}
VS_DEPTH = {"QB": 1, "RB": 2, "WR": 3, "TE": 2}


def ok(m, x=""):   PASS.append(m); print(f"  PASS  {m}  {x}")
def bad(m, x=""):  FAIL.append(m); print(f"  FAIL  {m}  {x}")
def warn(m, x=""): WARN.append(m); print(f"  WARN  {m}  {x}")


# 🔴🔴 THE THIRD VERDICT, AND IT IS NOT A PASS.
# `[measured 2026-09-19]` three of this file's five failures were FALSE,
# and all three were the same mistake: a constancy test read in the
# second week of a season.
#   · `week` is CONSTANT [only value 1]  — one week has been played
#   · `ahead_out` is CONSTANT [only 0]   — measured on 2025, ahead_out
#     is 0-or-None across ALL 1,071 week-1 rows and only becomes
#     non-zero from week 2, because it reads last week's depth chart
#   · `vs-position has no defences`      — depth rank is TRAILING snap
#     share, so there is nothing to rank on after one week
# ⛔ A GUARD THAT FIRES ON CORRECT CODE IS THE OTHER FAILURE, and a
# verifier that cries wolf gets switched off — this file's own
# `ahead_out` comment says exactly that about an earlier version of
# itself.
# ✅ So a question that cannot be read yet reports NOT YET MEASURABLE,
# the same third state `verify_card.py`'s T37 bar uses. Not a pass, not
# a fail, and it never clears an issue.
# ⛔ AND THE BAR IS NOT LOWERED: the NEW question — "do the logs cover
# every week the schedule says is final" — is strictly harder, true in
# week 1 of every season, and RED on this tree today.
def nym(m, x=""):  NYM.append(m); print(f"  ----  {m}  {x}   NOT YET MEASURABLE")


def final_weeks(season):
    """Weeks the SCHEDULE says are finished. ⛔ Read from the artifact the
    collector already writes, never from the clock."""
    p = f"{BASE}/schedule-{season}.json.gz"
    if not os.path.exists(p):
        return None
    try:
        games = load(p).get("games") or []
    except Exception:
        return None
    return {g.get("week") for g in games
            if g.get("final") and isinstance(g.get("week"), int)}


def load(p):
    with gzip.open(p, "rt") as fh:
        return json.load(fh)


def check_logs(path):
    doc = load(path)
    season, players = doc.get("season"), doc.get("players") or {}
    rows = [(pid, p, g) for pid, p in players.items() for g in p.get("g", [])]
    print(f"\n=== {os.path.basename(path)} — season {season}, "
          f"{len(players):,} players, {len(rows):,} player-weeks ===")
    if not rows:
        bad(f"{season}: no player-weeks at all"); return None

    # 🔴 THE BRIDGE, AND WHY IT IS THE FIRST THING REPORTED.
    # A season can pass every other check and still be quietly missing 9%
    # of its wide receivers — and those are not a random 9%.
    # 🔴 A SEASON BUILT FROM A SUBSTITUTED ASSET MUST SAY SO.
    # `[measured run #206]` `rosters_2021.csv.gz` silently stood in for
    # `roster_weekly_2021.csv.gz` and the bridge collapsed to 75% on RBs.
    # The output looked normal; only the coverage number gave it away, and
    # nobody would have questioned it.
    sub = doc.get("substituted") or {}
    if sub:
        bad(f"season {season} was built from SUBSTITUTED assets",
            f"{sub} — a different KIND of file may have stood in for the "
            f"one requested")
    elif doc.get("source_assets"):
        ok(f"season {season} used the exact assets requested")

    if doc.get("bridge_ok") is False:
        warn(f"season {season} has bridge_ok=FALSE",
             f"{doc.get('bridge_coverage')} — unbridged players carry no "
             f"snap data, never clear the snap floor, and never reach "
             f"vs-position. ⛔ Say so before fitting anything on it.")
    elif doc.get("bridge_ok") is True:
        ok(f"season {season} bridge coverage clears "
           f"{doc.get('bridge_min')}%", f"{doc.get('bridge_coverage')}")

    undated = [g for _, _, g in rows if not g.get("d")]
    (ok if not undated else bad)("every player-week carries a date",
                                 f"[{len(undated)} undated]")

    # 🔴 THE CHECK THAT WOULD HAVE CAUGHT `ahead_out`. A column with ONE
    # distinct value across 19,000 rows is not a weak feature — it is a
    # BROKEN JOIN wearing a feature's clothes.
    numeric = collections.defaultdict(set)
    for _, _, g in rows:
        for k, v in g.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                numeric[k].add(v)
    log_weeks = {g.get("week") for _, _, g in rows
                 if isinstance(g.get("week"), int)}
    # ══════════════════════════════════════════════════════════════════
    # 🔴🔴 THE HARDER QUESTION, AND IT IS RED ON THIS TREE TODAY.
    # "Is this column constant" cannot be read in week 1. "Do the logs
    # cover every week the SCHEDULE says has finished" can, it is true
    # in week 1 of every season, and it catches the real defect a
    # constancy test only stumbled onto: `[measured 2026-09-19]`
    # `players-2026.json.gz` holds week 1 while `schedule-2026.json.gz`
    # already records finals for weeks 1 AND 2 — 47 hours of nflverse
    # 403s, and nothing said so.
    # ══════════════════════════════════════════════════════════════════
    fw = final_weeks(season)
    if fw is None:
        nym(f"{season}: the logs cover every finished week",
            "— no schedule artifact to compare against")
    elif not fw:
        nym(f"{season}: the logs cover every finished week",
            "— the schedule records no finished week yet")
    else:
        behind = sorted(fw - log_weeks)
        (ok if not behind else bad)(
            f"{season}: the logs cover every week the schedule calls final",
            f"[logs {sorted(log_weeks)} vs final {sorted(fw)}]" if not behind
            else f"⛔ MISSING WEEK(S) {behind} — the schedule has finals for "
                 f"{sorted(fw)} and the logs stop at {sorted(log_weeks)}")

    # ⚠️ A CONSTANCY TEST NEEDS MORE THAN ONE WEEK TO MEAN ANYTHING.
    if len(log_weeks) < 2:
        nym(f"{season}: columns are not constant",
            f"— only week(s) {sorted(log_weeks)} are in the logs, and a "
            f"column measured over one week is not a column")
    else:
        for k in sorted(numeric):
            if len(numeric[k]) <= 1:
                bad(f"`{k}` is CONSTANT across {len(rows):,} rows",
                    f"[only value {next(iter(numeric[k]))}] — a join "
                    f"failure, not a result")

    # ⚠️ AN EARLIER VERSION OF THIS CHECK WAS WRONG AND IS RECORDED RATHER
    # THAN QUIETLY DELETED. It flagged `ahead_out` on a player's FIRST game
    # as lookahead — 84 of them. It is not: a player signed in week 5 has
    # no prior weeks, but his TEAMMATES do, and that is whose share
    # ahead_out reads. ⛔ It was measuring the wrong player, and a verifier
    # that cries wolf gets switched off.
    absurd = [(p.get("name"), g.get("week"), g["ahead_out"])
              for _, p, g in rows if g.get("ahead_out", 0) > 12]
    (ok if not absurd else bad)(
        "ahead_out never exceeds a plausible position group",
        f"[{len(absurd)}{': ' + str(absurd[:3]) if absurd else ''}]")

    unsorted_ = sum(1 for p in players.values()
                    if [x.get("week") for x in p["g"]
                        if isinstance(x.get("week"), int)]
                    != sorted(x.get("week") for x in p["g"]
                              if isinstance(x.get("week"), int)))
    (ok if not unsorted_ else bad)("every player's games are in week order",
                                   f"[{unsorted_} out of order]")

    weeks = {g.get("week") for _, _, g in rows if isinstance(g.get("week"), int)}
    (bad if (weeks and (min(weeks) < 1 or max(weeks) > 23)) else ok)(
        "week numbers are in range", f"[{min(weeks)}..{max(weeks)}]")

    sf = sum(1 for _, _, g in rows
             if g.get("o") and g.get("team") and g["o"] == g["team"])
    (ok if not sf else bad)("no player faces his own team", f"[{sf} rows]")

    prop_rows = [(i, p, g) for i, p, g in rows if p.get("pos") in PROP_POS]
    frac = (sum(1 for _, _, g in prop_rows if "snap_pct" in g)
            / len(prop_rows)) if prop_rows else 0
    (ok if frac >= 0.80 else bad)("snap coverage on QB/RB/WR/TE",
        f"[{frac:.1%} of {len(prop_rows):,} — the depth-rank system rests "
        f"on this]")

    badpct = [g for _, _, g in rows
              if "snap_pct" in g and not 0.0 <= g["snap_pct"] <= 1.0]
    (ok if not badpct else bad)("every snap_pct is a fraction 0..1",
                                f"[{len(badpct)} outside range]")

    # ⚠️ SKILL POSITIONS ONLY, and the reason is a real finding: the first
    # run flagged **Braden Mann, a PUNTER, at −34 rushing yards on one
    # carry** — a botched punt, genuine football, not a data fault.
    # ⛔ Widening the range for everyone would blind the check for the
    # players it exists to protect.
    domain = {"rec": (0, 25), "tgt": (0, 30), "rec_yds": (-20, 350),
              "car": (0, 50), "rush_yds": (-30, 350), "att": (0, 75),
              "cmp": (0, 60), "pass_yds": (-20, 600), "pass_td": (0, 9),
              "int": (0, 8), "rec_td": (0, 5), "rush_td": (0, 6)}
    viol = [(p.get("name"), g.get("week"), k, g[k])
            for _, p, g in rows if p.get("pos") in PROP_POS
            for k, (lo, hi) in domain.items()
            if isinstance(g.get(k), (int, float)) and not lo <= g[k] <= hi]
    (ok if not viol else bad)(
        "every stat is inside what its field can physically hold",
        f"[{len(viol)}{': ' + str(viol[:3]) if viol else ''}]")

    ca = [(p.get("name"), g.get("week")) for _, p, g in rows
          if isinstance(g.get("cmp"), (int, float))
          and isinstance(g.get("att"), (int, float)) and g["cmp"] > g["att"]]
    (ok if not ca else bad)("completions never exceed attempts", f"[{len(ca)}]")

    rt = [(p.get("name"), g.get("week")) for _, p, g in rows
          if isinstance(g.get("rec"), (int, float))
          and isinstance(g.get("tgt"), (int, float)) and g["rec"] > g["tgt"]]
    (ok if not rt else bad)("receptions never exceed targets", f"[{len(rt)}]")

    for k, label in (("ol_out", "his own line"),
                     ("opp_dl_out", "the opposing line")):
        nz = sum(1 for _, _, g in rows if g.get(k))
        (bad if nz == 0 else ok)(
            f"`{k}` ({label}) resolves",
            "— ZERO ON EVERY ROW; the injury join did not reach it"
            if nz == 0 else f"[{nz:,} of {len(rows):,} rows]")

    nz = sum(1 for _, _, g in rows if g.get("ahead_out"))
    if len(log_weeks) < 2:
        # ⚠️ MEASURED ON 2025: `ahead_out` is 0-or-None across ALL 1,071
        #    week-1 rows and only becomes non-zero from week 2, because
        #    it reads LAST week's depth chart. Failing here would fail
        #    every season in its first week.
        nym("`ahead_out` resolves",
            "— one week of logs; ahead_out reads last week's chart and is "
            "0 across all of week 1 in 2025 too")
    else:
        (bad if nz == 0 else ok)(
            "`ahead_out` resolves",
            "⛔ ZERO ON EVERY ROW — THIS EXACT DEFECT SHIPPED GREEN "
            "2026-08-28"
            if nz == 0 else f"[{nz:,} rows have a higher-usage teammate out]")

    wx = sum(1 for _, _, g in rows if g.get("wx"))
    (ok if wx else warn)("weather resolved on some rows",
                         f"[{wx:,} of {len(rows):,}]")
    return doc


def check_vs_position(path, logs_doc):
    doc = load(path)
    print(f"\n=== {os.path.basename(path)} ===")
    defs = doc.get("defences") or {}
    if not defs:
        _w = {g.get("week") for g in ((logs_doc or {}).get("rows") or [])
              if isinstance(g.get("week"), int)} if logs_doc else set()
        if len(_w) < 2:
            # ⚠️ Depth rank is a TRAILING snap-share window. After one
            #    week there is nothing to rank on, so an empty table is
            #    the correct output rather than a break.
            nym("vs-position has defences",
                f"— the logs hold week(s) {sorted(_w) or 'none'}; depth "
                f"rank is a trailing window")
        else:
            bad("vs-position has no defences at all")
        return

    if (doc.get("snap_floor") or {}) != SNAP_FLOOR:
        warn("stored snap_floor differs from this verifier's copy",
             f"[stored {doc.get('snap_floor')}]")
    (ok if len(defs) == 32 else warn)("32 defences present", f"[{len(defs)}]")

    lowsnap = deep = total = 0
    for byteam in defs.values():
        for pos, slots in byteam.items():
            for slot, perfs in (slots or {}).items():
                try: r = int(slot)
                except (TypeError, ValueError): continue
                if pos in VS_DEPTH and r > VS_DEPTH[pos]:
                    deep += 1
                for x in (perfs or []):
                    total += 1
                    sp = x.get("snap_pct")
                    if sp is not None and sp < SNAP_FLOOR.get(pos, 0.0):
                        lowsnap += 1
    (ok if not lowsnap else bad)(
        "every performance clears its position's snap floor",
        f"[{lowsnap} below floor, of {total:,}]")
    (ok if not deep else bad)("no depth slot deeper than VS_DEPTH allows",
                              f"[{deep} too deep]")

    if logs_doc:
        elig = sum(1 for p in (logs_doc.get("players") or {}).values()
                   if p.get("pos") in VS_DEPTH
                   for g in p.get("g", [])
                   if g.get("snap_pct") is not None
                   and g["snap_pct"] >= SNAP_FLOOR.get(p["pos"], 0.0))
        (bad if total > elig else ok)(
            "vs-position is a subset of its source logs",
            f"[{total:,} of {elig:,} eligible]" if total <= elig else
            f"[{total:,} vs {elig:,}] — it cannot hold MORE than its source")


def main():
    want = sys.argv[1:]
    # 🔴 `--current` IS WHAT THE COLLECTOR RUNS. A pass verifies what it
    # just produced; a whole-history sweep is a hand tool. `[2026-09-19]`
    # 2022's snap coverage is 78.3% — a real historical gap, reported by
    # a bare run and deliberately NOT gating today's football job, which
    # did not create it and cannot repair it.
    if "--current" in want:
        want = [w for w in want if w != "--current"]
        try:
            import freshness as _f
            want.append(str(_f.current_football_season()))
        except Exception as _e:              # pragma: no cover
            print(f"::error::cannot resolve the current season: {_e}")
            return 1
    paths = sorted(glob.glob(f"{BASE}/players-*.json.gz"))
    if want:
        paths = [p for p in paths if any(s in os.path.basename(p) for s in want)]
    if not paths:
        print(f"::error::no players-*.json.gz in {BASE}/ — run "
              f"`nfl-logs converge-off` first")
        return 1

    print("=" * 70); print("VERIFY NFL — the football data layer"); print("=" * 70)
    for p in paths:
        logs = check_logs(p)
        yr = re.search(r"players-(\d{4})", p)
        y = yr.group(1) if yr else "?"
        vs = f"{BASE}/vs-position-{y}.json.gz"
        if os.path.exists(vs):
            check_vs_position(vs, logs)
        else:
            bad(f"vs-position-{y}.json.gz is MISSING",
                "— the matchup tables are the whole point of the framework")

    print("\n" + "=" * 70)
    print(f"{len(PASS)} passed, {len(NYM)} not yet measurable, "
          f"{len(WARN)} warnings, {len(FAIL)} FAILED")
    for n in NYM:   print(f"  ----  {n}")
    for f in FAIL:  print(f"::error::{f}")
    for w in WARN:  print(f"::warning::{w}")
    print("=" * 70)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
