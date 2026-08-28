#!/usr/bin/env python3
"""NFL ingestion — nflverse.

🔴 STDLIB ONLY. The Actions runner installs Python and nothing else; there
is no pip step in the workflow and adding one costs a minute on every run.
That rules out pandas and pyarrow, so every file here is read as CSV with
the `csv` module. ⛔ Do not introduce a dependency without also adding the
install step and re-costing the schedule.

⚠️ NOTHING IN THIS FILE HAS BEEN RUN AGAINST THE REAL SOURCE YET. The Claude
container is barred from fetching URLs, so the file layout below is written
from documentation and MUST be confirmed by `probe()` on the runner before
any collector is scheduled. That is the same discipline the NBA source gets,
and it exists because this project has twice written down "the feed has X"
and been wrong.
"""
import collections
import csv
import gzip
import io
import json
import urllib.error
import urllib.request

GH_API = "https://api.github.com/repos/nflverse/nflverse-data/releases"
UA = {"User-Agent": "gizmos-picks/0.1"}

# What the model needs, and why. See claude/multi-league-spec.md.
#   usage  -> forecastable, carries the model
#   effic. -> high variance, regressed hard toward position baselines
WANT = {
    "stats_player":   "weekly player stats — the TARGET and the trailing-form input",
    "snap_counts":    "USAGE. the best single predictor of next week's usage",
    "depth_charts":   "the lineup-slot analogue MLB's hitter model never had",
    "injuries":       "a WR2 becomes a WR1 the moment WR1 sits",
    "weekly_rosters": "who was actually active, point-in-time",
    "schedules":      "opponent, home/away, game id, kickoff",
    "pbp":            "target share, air yards, red-zone usage",
}


# ✅ CONFIRMED ON THE RUNNER 2026-08-28, collect run #187 — these are the
# real asset names, not a pattern anyone inferred. ⛔ Do not "tidy" them
# into an f-string template: nflverse names are irregular on purpose
# (`stats_player_reg_YYYY` but `roster_weekly_YYYY`), and a template is how
# a collector silently fetches nothing.
FILES = {
    # ✅ WEEKLY, CONFIRMED run #189: 19,422 rows for 2025. ⛔ NOT
    # `stats_player_reg_{y}` -- that is 2,020 rows of SEASON TOTALS and
    # carries a `games` column. Using it would feed one season aggregate
    # in as every week's trailing form and the model would look fitted.
    "stats_player":   "stats_player_week_{y}.csv.gz",
    "snap_counts":    "snap_counts_{y}.csv.gz",
    "depth_charts":   "depth_charts_{y}.csv.gz",
    "injuries":       "injuries_{y}.csv.gz",
    "weekly_rosters": "roster_weekly_{y}.csv.gz",
    "pbp":            "play_by_play_{y}.csv.gz",
}
# ✅ `schedules` is NOT year-partitioned: one `games.csv.gz` (512KB) covers
# every season. The probe's "NONE" was the FILTER being wrong, not the data
# being absent -- which is exactly the "an absence in a response is evidence
# about the response" rule this project already has.
SCHEDULE_FILE = "games.csv.gz"

# ✅ THE JOIN, MEASURED run #189 -- not assumed:
#   stats_player.player_id IS gsis_id      overlap 2,024 / 2,024  (100%)
#   depth_charts / injuries               keyed on gsis_id
#   snap_counts                           keyed on pfr_player_id ONLY
#   weekly_rosters                        carries BOTH -> it is the bridge
# ⚠️ 1,783 of snap_counts' 2,189 pfr ids bridge to a gsis_id (81.5%). The
# collector reports the gap BY POSITION and fails loud if a prop-relevant
# position is thin -- an unbridged left guard costs us nothing, an
# unbridged WR1 is a silent hole in the model.
# ⛔ NEVER JOIN ON NAME. depth_charts x stats_player on `player_name`
# matched 0 of 1,848 rows. A name join here returns an empty model that
# reads as "football does not model" rather than "the plumbing is broken".
#
# ⚠️ 2026 FILES ALREADY EXIST for depth_charts and weekly_rosters; the
# stat and snap files appear once week 1 has been played.
#
# 🔴 `player_stats` (1,822 assets) IS A DIFFERENT, OLDER TAG from
# `stats_player` (542). nflverse migrated. Use `stats_player`.


def _raw(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        blob = r.read()
    if url.endswith(".gz") or blob[:2] == b"\x1f\x8b":
        blob = gzip.decompress(blob)
    return blob


def _json(url, timeout=60):
    return json.loads(_raw(url, timeout).decode())


def probe(log=print):
    """Ask the source what it actually publishes. Writes nothing.

    🔴 RUN THIS BEFORE WRITING A SINGLE COLLECTOR AGAINST A GUESSED URL.
    The GitHub releases API returns every tag with its exact asset names,
    so there is no need to guess a filename pattern at all -- and guessing
    one is how a collector ends up silently fetching nothing.
    """
    log("=== nflverse: what is actually published ===")
    try:
        rels = _json(GH_API + "?per_page=100")
    except Exception as e:
        log(f"🔴 CANNOT REACH THE RELEASES API: {type(e).__name__}: {e}")
        log("   If this fails on the RUNNER, the whole NFL plan changes shape.")
        return False

    log(f"{len(rels)} release tags\n")
    seen = {}
    for r in rels:
        tag = r.get("tag_name")
        assets = [(a["name"], a["size"], a["browser_download_url"])
                  for a in (r.get("assets") or [])]
        seen[tag] = assets
        mark = "  <-- WANTED" if tag in WANT else ""
        log(f"  {tag:22s} {len(assets):>4} assets{mark}")

    log("\n=== the tags this model needs ===")
    ok = True
    for tag, why in WANT.items():
        if tag not in seen:
            log(f"🔴 MISSING TAG '{tag}' — {why}")
            ok = False
            continue
        csvs = [a for a in seen[tag] if a[0].endswith((".csv", ".csv.gz"))]
        recent = sorted(a[0] for a in csvs if "2025" in a[0] or "2026" in a[0])
        log(f"\n  {tag}  ({why})")
        log(f"    {len(csvs)} csv asset(s); 2025/2026: {recent[:6] or 'NONE'}")
        if not csvs:
            log(f"    🔴 NO CSV FORM — stdlib cannot read this tag's format.")
            ok = False

    # 🔴 TWO THINGS RUN #188 EXPOSED, BOTH FATAL IF UNCHECKED:
    #   1. `stats_player_reg_2025` is 2,020 rows. A season has ~18 weeks x
    #      ~1,700 active players ~= 30,000 player-WEEKS, and the file
    #      carries a `games` column -- so it is SEASON TOTALS, not weekly.
    #      Building trailing form off it would have silently used a single
    #      season aggregate as every week's input.
    #   2. `player_name` joins depth_charts to stats_player 0 of 1,848
    #      times. ZERO. The name formats differ, and a name join would have
    #      produced an empty model that looked like a modelling failure
    #      rather than a plumbing one. This is MLB's shared-name bug with a
    #      new face.
    log("\n=== 1. is there a WEEKLY stats file? ===")
    allsp = sorted(a[0] for a in seen.get("stats_player", [])
                   if a[0].endswith(".csv.gz"))
    log(f"  {len(allsp)} gz assets under stats_player")
    for pat in ("week", "reg", "post", "2025", "2026"):
        hit = [n for n in allsp if pat in n]
        log(f"    contains '{pat}': {len(hit)} -> {hit[:8]}")

    log("\n=== 2. is stats_player.player_id the same namespace as gsis_id? ===")
    ids = {}
    for tag, fname, col in (("stats_player", None, "player_id"),
                            ("weekly_rosters", FILES["weekly_rosters"].format(y=2025), "gsis_id")):
        if fname is None:
            cand = [n for n in allsp if "week" in n and "2025" in n] or \
                   [n for n in allsp if "reg_2025" in n]
            fname = cand[0] if cand else None
        hit = [a for a in seen.get(tag, []) if a[0] == fname]
        if not hit:
            log(f"  🔴 {tag}: '{fname}' not found")
            continue
        rows = list(csv.DictReader(
            io.StringIO(_raw(hit[0][2]).decode("utf-8", "replace"))))
        vals = [r[col] for r in rows if r.get(col)]
        ids[tag] = set(vals)
        log(f"  {fname}: {len(rows):,} rows, {col} sample {vals[:3]}")
    if len(ids) == 2:
        a, b = ids["stats_player"], ids["weekly_rosters"]
        log(f"  OVERLAP stats_player.player_id n weekly_rosters.gsis_id = "
            f"{len(a & b):,} / {min(len(a), len(b)):,}")

    log("\n=== 3. does weekly_rosters bridge pfr -> gsis? ===")
    hit = [a for a in seen["weekly_rosters"]
           if a[0] == FILES["weekly_rosters"].format(y=2025)]
    rows = list(csv.DictReader(
        io.StringIO(_raw(hit[0][2]).decode("utf-8", "replace"))))
    both = [r for r in rows if r.get("gsis_id") and r.get("pfr_id")]
    log(f"  {len(rows):,} roster rows; {len(both):,} carry BOTH gsis_id and pfr_id")
    snap = [a for a in seen["snap_counts"]
            if a[0] == FILES["snap_counts"].format(y=2025)]
    srows = list(csv.DictReader(
        io.StringIO(_raw(snap[0][2]).decode("utf-8", "replace"))))
    spfr = {r["pfr_player_id"] for r in srows if r.get("pfr_player_id")}
    bridge = {r["pfr_id"] for r in both}
    log(f"  snap_counts has {len(spfr):,} distinct pfr ids; "
        f"{len(spfr & bridge):,} of them bridge to a gsis_id "
        f"({100.0 * len(spfr & bridge) / max(1, len(spfr)):.1f}%)")

    log("\n=== 3b. WHAT DOES THE INJURY FILE ACTUALLY SAY? ===")
    # 🔴 RUN #194 BUILT `ahead_out` AS CONSTANT ZERO ON ALL 19,400 ROWS AND
    # WENT GREEN. The mapping assumed report_status values like "Out" and
    # "Doubtful"; only 620 of 19,400 rows got ANY designation. A constant
    # feature is not a null result about football -- it is a broken join
    # wearing one. Ask the file instead of assuming.
    ih = [a for a in seen.get("injuries", []) if a[0] == FILES["injuries"].format(y=2025)]
    if ih:
        irows = list(csv.DictReader(
            io.StringIO(_raw(ih[0][2]).decode("utf-8", "replace"))))
        log(f"  {len(irows):,} injury rows")
        for col in ("report_status", "practice_status", "game_type"):
            c = collections.Counter((r.get(col) or "<empty>") for r in irows)
            log(f"  {col}: {dict(c.most_common(8))}")
        wk = collections.Counter(str(r.get("week")) for r in irows)
        log(f"  weeks: {sorted(wk, key=lambda x: (len(x), x))[:8]}")
        gid = {r.get("gsis_id") for r in irows if r.get("gsis_id")}
        log(f"  distinct gsis_id in injuries: {len(gid):,}")

    log("\n=== 4. what is actually under `schedules`? ===")
    for n, sz, _ in seen.get("schedules", []):
        log(f"  {n}  {sz:,}B")

    log("\n✅ PROBE COMPLETE — nothing was written.")
    return ok


# ======================================================================
# THE COLLECTOR
# ======================================================================
# 🔴 EVERY ROW IS POINT-IN-TIME BY CONSTRUCTION. Each game log entry
# carries the KICKOFF DATE from the schedule, so the model filters
# `d < slate_date` exactly the way the MLB pitcher log does. ⛔ Never join
# a season-total column onto a week-3 game: that is a model that has seen
# the future, and it is the single easiest way to fake a good backtest.

# What the model actually reads off a player-week. Usage first, because
# usage is what forecasts; efficiency is regressed toward baselines.
STAT_COLS = {
    "targets": "tgt", "receptions": "rec", "receiving_yards": "rec_yds",
    "receiving_tds": "rec_td", "target_share": "tgt_share",
    "air_yards_share": "ay_share", "receiving_air_yards": "ay",
    "carries": "car", "rushing_yards": "rush_yds", "rushing_tds": "rush_td",
    "attempts": "att", "completions": "cmp", "passing_yards": "pass_yds",
    "passing_tds": "pass_td", "passing_interceptions": "int",
}
# Positions whose props we will actually card. The bridge-coverage check
# below is enforced ON THESE ONLY -- an unbridged offensive lineman is
# irrelevant, an unbridged WR1 is a hole.
PROP_POS = {"QB", "RB", "WR", "TE", "FB"}
# 🔴 THE TRENCHES MOVE THE SKILL POSITIONS. Sam, 2026-08-28: "injuries to
# offensive lineman and/or defensive lineman on opposing teams can effect
# how a qb, rb, wr outcome will be." A quarterback behind two backup
# tackles is a different quarterback. ⚠️ These are COUNTS OF ABSENT
# STARTERS, not a line-quality rating -- we have no such rating and will
# not invent one.
OL_POS = {"T", "G", "C", "OT", "OG", "OL"}
DL_POS = {"DE", "DT", "NT", "DL", "EDGE"}
# 🔴 SNAP FLOORS. MLB counts STARTS ONLY -- a reliever's two-out cameo is
# not evidence about a starter. Measured 2026-08-28: Joe Flacco played 17%
# of snaps against ARI and threw for 24 yards; counted as "a QB1 vs
# Arizona" it moved that defence's mean by 16 yards. ⛔ Do not lower these
# to grow a sample. A cameo is not a start in any sport.
SNAP_FLOOR = {"QB": 0.60, "RB": 0.30, "WR": 0.50, "TE": 0.40, "FB": 0.30}
# 🔴 INJURY STATUS IS THE ONE INPUT A SEASON AVERAGE CANNOT CONTAIN, which
# is the entire premise of T41. See research/t41_spec.md.
# ⛔ Graded, not boolean: "Questionable" plays most weeks, "Out" never does.
INJ_RANK = {"": 0, "questionable": 1, "doubtful": 2, "out": 2,
            "injured reserve": 2, "reserve/injured": 2}
BRIDGE_MIN = 95.0          # % of prop-position snap rows that must bridge


def _rows(seen, tag, fname, log):
    hit = [a for a in seen.get(tag, []) if a[0] == fname]
    if not hit:
        raise RuntimeError(f"{tag}: asset '{fname}' not published")
    blob = _raw(hit[0][2]).decode("utf-8", "replace")
    out = list(csv.DictReader(io.StringIO(blob)))
    log(f"  {fname}: {len(out):,} rows")
    return out


def _num(v):
    if v in (None, "", "NA"):
        return 0.0
    try:
        return float(v)
    except ValueError:
        return 0.0


def build_logs(season, log=print):
    """Per-player point-in-time game logs for one season."""
    log(f"=== nfl: building {season} player logs ===")
    rels = _json(GH_API + "?per_page=100")
    seen = {r["tag_name"]: [(a["name"], a["size"], a["browser_download_url"])
                            for a in (r.get("assets") or [])] for r in rels}

    sched = _rows(seen, "schedules", SCHEDULE_FILE, log)
    stats = _rows(seen, "stats_player", FILES["stats_player"].format(y=season), log)
    snaps = _rows(seen, "snap_counts", FILES["snap_counts"].format(y=season), log)
    rost = _rows(seen, "weekly_rosters", FILES["weekly_rosters"].format(y=season), log)

    # -- the bridge. pfr_id -> gsis_id, from the roster that carries both.
    bridge = {r["pfr_id"]: r["gsis_id"] for r in rost
              if r.get("pfr_id") and r.get("gsis_id")}
    log(f"  bridge: {len(bridge):,} pfr->gsis pairs")

    # -- kickoff date and home/away, per (season, week, team).
    when, wx = {}, {}
    for g in sched:
        if str(g.get("season")) != str(season):
            continue
        wk, day, gid = g.get("week"), g.get("gameday"), g.get("game_id")
        for side, opp, home in (("home_team", "away_team", 1),
                                ("away_team", "home_team", 0)):
            if g.get(side):
                when[(str(wk), g[side])] = (day, g.get(opp), home, gid)
                # 🔴 WEATHER. Sam, 2026-08-28: snow and rain change games.
                # ⚠️ Read defensively -- these columns are logged, never
                # assumed. MLB found PARK and TEMPERATURE real and WIND
                # SPEED ALONE a null (T31-T33); football will differ and
                # must be measured separately, not inherited.
                wx[(str(wk), g[side])] = {
                    k: g.get(k) for k in ("roof", "surface", "temp", "wind")
                    if g.get(k) not in (None, "")}
    log(f"  schedule: {len(when):,} team-weeks in {season}")
    _wxk = collections.Counter(k for v in wx.values() for k in v)
    log(f"  weather columns present: {dict(_wxk) or 'NONE — schedule carries no weather'}")

    # -- snap counts, bridged onto gsis, keyed by (gsis, week).
    snap_by = {}
    miss = collections.Counter()
    have = collections.Counter()
    for r in snaps:
        pos = (r.get("position") or "").upper()
        gid = bridge.get(r.get("pfr_player_id"))
        (have if gid else miss)[pos] += 1
        if gid:
            snap_by[(gid, str(r.get("week")))] = r

    thin = []
    for pos in sorted(PROP_POS):
        h, m = have[pos], miss[pos]
        pct = 100.0 * h / (h + m) if (h + m) else 100.0
        log(f"  bridge coverage {pos:3s}: {h:>6,} of {h + m:>6,}  {pct:5.1f}%")
        if (h + m) and pct < BRIDGE_MIN:
            thin.append(f"{pos} {pct:.1f}%")
    if thin:
        # 🔴 FAIL LOUD. A thin bridge on a prop position is a silent hole in
        # the model, and a silent hole looks like a modelling result.
        raise RuntimeError(f"bridge below {BRIDGE_MIN}% on: {', '.join(thin)}")

    # -- injury report, per (gsis, week). ⚠️ A player ABSENT from the report
    # is healthy: the file lists only players with a designation, so a
    # missing row is information, not a gap.
    # 🔴 THE OUT SET IS KEPT SEPARATE FROM THE JOINED ROWS, AND THAT IS THE
    # WHOLE FIX. Run #194 built ahead_out as constant zero. The mapping was
    # right and the file was right -- `report_status` really does contain
    # Out (1,396), Questionable (1,281), Doubtful (106).
    # ⛔ THE BUG: A PLAYER WHO IS *OUT* HAS NO STAT ROW THAT WEEK. He did not
    # play, so `stats_player_week` never lists him, so his inj=2 had nothing
    # to attach to -- and `ahead_out`, which read teammates' inj off the
    # JOINED rows, could never see a single one. The absence of a row IS the
    # signal, and it was being looked for in the one place it cannot appear.
    inj, out_set = {}, set()
    try:
        for r in _rows(seen, "injuries", FILES["injuries"].format(y=season), log):
            st = (r.get("report_status") or "").strip().lower()
            rank = INJ_RANK.get(st, 1 if st else 0)
            key = (r.get("gsis_id"), str(r.get("week")))
            inj[key] = max(inj.get(key, 0), rank)
            if rank >= 2:
                out_set.add(key)
        log(f"  injuries: {len(inj):,} player-weeks designated, "
            f"{len(out_set):,} of them OUT/DOUBTFUL")
    except Exception as e:
        # ⛔ FAIL LOUD. Silently modelling without the input the test exists
        # to measure would produce a null result about the wrong thing.
        raise RuntimeError(f"injuries unavailable: {e}")

    # -- absent linemen, per (team, week). ⚠️ Position comes from the
    # ROSTER, because the injury file's own position field is sparser.
    pos_of, team_of = {}, {}
    for r in rost:
        g = r.get("gsis_id")
        if not g:
            continue
        pos_of[g] = (r.get("position") or "").upper()
        team_of[(g, str(r.get("week")))] = r.get("team")
    ol_out, dl_out = collections.Counter(), collections.Counter()
    for gid, wk in out_set:
        pos, tm = pos_of.get(gid), team_of.get((gid, wk))
        if not tm:
            continue
        if pos in OL_POS:
            ol_out[(tm, wk)] += 1
        elif pos in DL_POS:
            dl_out[(tm, wk)] += 1
    log(f"  trench absences: {sum(ol_out.values()):,} OL, "
        f"{sum(dl_out.values()):,} DL across the season")

    players = {}
    for r in stats:
        pid = r.get("player_id")
        if not pid:
            continue
        wk, team = str(r.get("week")), r.get("recent_team") or r.get("team")
        day, opp, home, gid = when.get((wk, team), (None, None, None, None))
        p = players.setdefault(pid, {
            "name": r.get("player_display_name") or r.get("player_name"),
            "pos": (r.get("position") or "").upper(), "team": team, "g": [],
        })
        row = {"d": day, "week": int(wk) if str(wk).isdigit() else wk,
               "team": team, "o": opp, "home": home, "game_id": gid}
        # 🔴 HIS OWN LINE, AND THE LINE HE IS PLAYING AGAINST.
        row["ol_out"] = ol_out.get((team, wk), 0)        # his blockers missing
        row["opp_dl_out"] = dl_out.get((opp, wk), 0)     # their rushers missing
        w = wx.get((wk, team))
        if w:
            row["wx"] = w
        sn = snap_by.get((pid, wk))
        if sn:
            row["snaps"] = int(_num(sn.get("offense_snaps")))
            row["snap_pct"] = round(_num(sn.get("offense_pct")), 3)
        row["inj"] = inj.get((pid, wk), 0)
        for src, dst in STAT_COLS.items():
            row[dst] = _num(r.get(src))
        p["g"].append(row)

    for p in players.values():
        p["g"].sort(key=lambda x: (x["d"] or "", x["week"]))

    # -- ahead_out: how many same-team, same-position players with a HIGHER
    # TRAILING snap share are OUT this week.
    # 🔴 DEPTH IS DERIVED FROM WHAT ACTUALLY HAPPENED, not the published
    # depth chart. Declared in t41_spec.md before any fit: the depth-chart
    # file is 554k timestamped snapshots (a large surface for a silent
    # point-in-time bug) and teams game it, whereas snap share is fact.
    # ⛔ STRICTLY POINT-IN-TIME: the ranking uses games BEFORE this one.
    # -- squad membership: who belongs to a (team, position) at all, and
    # what their snap share was BEFORE a given week. ⚠️ Built across the
    # whole season because a teammate who is OUT has no row in the week we
    # are asking about -- that is precisely the case being detected.
    squad = collections.defaultdict(set)
    weeks_of = {}
    for pid, p in players.items():
        if p["pos"] not in PROP_POS:
            continue
        for g in p["g"]:
            squad[(g["team"], p["pos"])].add(pid)
        weeks_of[pid] = {g["week"]: i for i, g in enumerate(p["g"])}

    def share_before(pid, week):
        gs = players[pid]["g"]
        prior = [g for g in gs if g["week"] < week][-8:]
        vals = [g.get("snap_pct", 0.0) for g in prior]
        return (sum(vals) / len(vals)) if vals else 0.0

    for pid, p in players.items():
        if p["pos"] not in PROP_POS:
            continue
        for i, g in enumerate(p["g"]):
            mine = share_before(pid, g["week"])
            n = 0
            for q in squad[(g["team"], p["pos"])]:
                if q == pid:
                    continue
                if (q, str(g["week"])) not in out_set:
                    continue
                if share_before(q, g["week"]) > mine:
                    n += 1
            g["ahead_out"] = n
    n_ao = sum(1 for p in players.values() for g in p["g"] if g.get("ahead_out"))
    n_rows = sum(len(p["g"]) for p in players.values())
    log(f"  ahead_out: {n_ao:,} player-weeks have a higher-usage teammate OUT")
    # 🔴 A CONSTANT FEATURE IS A BROKEN JOIN, NOT A FINDING. Run #194 emitted
    # ahead_out = 0 on all 19,400 rows and went GREEN; fitting on that would
    # have produced "the mechanism is dead" when the column was never
    # populated -- the most expensive kind of wrong answer, because it looks
    # like science.
    # ⛔ THE GUARD CHECKS `ahead_out` AND THE UPSTREAM `out_set`. IT MUST NOT
    # CHECK `inj>=2` ON THE JOINED ROWS. Run #196 proved why: that count is
    # CORRECTLY ZERO on every joined row, because a player who is OUT has no
    # stat line that week -- which is the entire insight behind the fix. The
    # first version of this guard failed a run whose data was perfectly good.
    if not out_set:
        raise RuntimeError(
            "the injury file yielded NO OUT/DOUBTFUL players -- a parse or "
            "mapping failure. Run nfl-probe and read section 3b.")
    if n_ao == 0:
        raise RuntimeError(
            f"ahead_out is CONSTANT ZERO across {n_rows:,} player-weeks. "
            f"That is a join failure, not a result. Run nfl-probe and read "
            f"section 3b before fitting anything on it.")


    undated = sum(1 for p in players.values() for x in p["g"] if not x["d"])
    withsnap = sum(1 for p in players.values() for x in p["g"] if "snaps" in x)
    total = sum(len(p["g"]) for p in players.values())
    log(f"  {len(players):,} players, {total:,} player-weeks")
    log(f"  {withsnap:,} carry snap counts ({100.0 * withsnap / max(1, total):.1f}%)")
    if undated:
        # ⛔ A row with no kickoff date cannot be filtered point-in-time, so
        # it can never be used safely. Refuse rather than silently include.
        raise RuntimeError(f"{undated} player-weeks have no kickoff date")
    return {"season": season, "source": "nflverse", "players": players}


# ======================================================================
# DEFENCE VERSUS POSITION — the football version of MLB's opponent block
# ======================================================================
# 🔴 DESCRIPTIVE. Sam, 2026-08-28: "i look up cardinals vs starting qbs
# game log, id view the other qbs throughout the season vs the cardinals."
# That is this, for every defence and every depth slot.
# ⛔ NO MODEL AND NO CONFIDENCE NUMBER. These are the games that happened,
# which is exactly why they can ship without a pre-registered test — the
# same footing as the opponent block on the MLB pitcher rows.
VS_DEPTH = {"QB": 1, "RB": 2, "WR": 3, "TE": 2}   # how many slots to keep
VS_STATS = ("pass_yds", "rush_yds", "rec_yds", "rec", "tgt", "tgt_share",
            "pass_td", "rush_td", "rec_td", "snap_pct")


def build_vs_position(doc, log=print):
    """defence -> position -> depth slot -> the opposing performances.

    🔴 DEPTH RANK IS TRAILING SNAP SHARE, POINT-IN-TIME — what the coach
    actually did before this game, not a published depth chart teams game.
    ⛔ Ranking on the season would let a week-3 row know about week 14.
    """
    P = doc["players"]
    share = collections.defaultdict(lambda: collections.defaultdict(list))
    for pid, p in P.items():
        if p["pos"] not in VS_DEPTH:
            continue
        for g in p["g"]:
            share[(g["team"], p["pos"], g["week"])]  # touch so key exists
    # trailing snap share for every (team,pos) as of each week
    hist = collections.defaultdict(lambda: collections.defaultdict(list))
    for pid, p in P.items():
        if p["pos"] not in VS_DEPTH:
            continue
        for g in p["g"]:
            hist[(g["team"], p["pos"])][pid].append((g["week"], g.get("snap_pct", 0.0)))

    def rank_of(pid, team, pos, week):
        d = hist.get((team, pos)) or {}
        avg = {}
        for q, rows in d.items():
            v = [s for w, s in rows if w < week]
            if v:
                avg[q] = sum(v) / len(v)
        order = [q for q, _ in sorted(avg.items(), key=lambda kv: -kv[1])]
        return order.index(pid) + 1 if pid in order else None

    out, kept, dropped = {}, 0, collections.Counter()
    for pid, p in P.items():
        pos = p["pos"]
        if pos not in VS_DEPTH:
            continue
        for g in p["g"]:
            if not g["o"]:
                continue
            sp = g.get("snap_pct")
            if sp is None or sp < SNAP_FLOOR.get(pos, 0.0):
                dropped["below the snap floor"] += 1
                continue
            r = rank_of(pid, g["team"], pos, g["week"])
            if r is None or r > VS_DEPTH[pos]:
                dropped["no rank yet, or deeper than we keep"] += 1
                continue
            row = {"pid": pid, "name": p["name"], "team": g["team"],
                   "week": g["week"], "d": g["d"],
                   "ol_out": g.get("ol_out", 0), "opp_dl_out": g.get("opp_dl_out", 0)}
            if g.get("wx"):
                row["wx"] = g["wx"]
            for k in VS_STATS:
                if g.get(k) is not None:
                    row[k] = g[k]
            out.setdefault(g["o"], {}).setdefault(pos, {}).setdefault(str(r), []).append(row)
            kept += 1
    for d in out.values():
        for pos in d:
            for r in d[pos]:
                d[pos][r].sort(key=lambda x: x["week"])
    log(f"  vs-position: {kept:,} performances kept across {len(out)} defences")
    for k, v in dropped.items():
        log(f"    dropped {v:,} — {k}")
    if kept == 0:
        raise RuntimeError("vs-position is EMPTY. That is a rank or snap-floor "
                           "failure, not a finding.")
    return {"season": doc["season"], "kind": "DESCRIPTIVE",
            "note": ("Every performance a defence has allowed, by depth slot. "
                     "Depth rank is trailing snap share, point-in-time. Rows "
                     "below the position's snap floor are excluded so a cameo "
                     "never counts as a start. No model, no confidence rating."),
            "snap_floor": SNAP_FLOOR, "defences": out}
