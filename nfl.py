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
import re
import gzip
import io
import json
import urllib.error
import urllib.request

GH_API = "https://api.github.com/repos/nflverse/nflverse-data/releases"


def _releases(log=print, max_pages=10):
    """EVERY nflverse release, not just the first page.

    🔴 `?per_page=100` RETURNS ONE PAGE. `[found 2026-08-28]` both the
    probe and the builder asked for a single page and then concluded, from
    that partial list, that **route participation is not published**. That
    conclusion was drawn from a TRUNCATED QUERY.
    ⛔ THIS PROJECT'S OLDEST AND MOST REPEATED FAILURE IS A FACT ABOUT A
    QUERY WRITTEN DOWN AS A FACT ABOUT THE WORLD -- five recorded
    instances before this one. **An absence in page one is not an absence
    in the world.**
    ➡️ Sam found `sumersports.com` publishing Routes Run, Targets/Route
    Run and YPRR -- proof the metric EXISTS. Before paying for it or
    scraping it, the free source has to be asked properly.
    """
    out, page = [], 1
    while page <= max_pages:
        got = _json(f"{GH_API}?per_page=100&page={page}")
        if not got:
            break
        out.extend(got)
        if len(got) < 100:
            break
        page += 1
    log(f"  nflverse releases: {len(out)} across {page} page(s)")
    return out
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
class SeasonNotStarted(RuntimeError):
    """The source publishes NOTHING for the requested year.

    🔴 Raised only when the release holds no asset mentioning that year
    at all -- not when a name is merely wrong. ⛔ It is a FACT ABOUT THE
    SOURCE, not a verdict: the caller decides whether it is forgivable,
    because only the caller knows whether this is the current season.
    """


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
    # 🔴 ROUTE PARTICIPATION. `[verified 2026-08-30 against the release
    # list itself]` `pbp_participation` publishes 2016-2025, csv/parquet,
    # 2025 refreshed 2026-02-10. ⚠️ ~47MB of csv a season.
    # ⛔ A `pbp_participation_old_2023` exists alongside the 2023 file --
    # the schema CHANGED. `_rows`' same-year-plus-shared-word fallback
    # will not silently take the `old` one, because "old" is a word the
    # requested name does not carry.
    "participation":  "pbp_participation_{y}.csv.gz",
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
        rels = _releases(log)
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
# Which nflverse asset each requested filename actually resolved to.
USED = {}


def _rows(seen, tag, fname, log):
    """Fetch one nflverse asset, by exact name and then by pattern.

    🔴 WHY THE FALLBACK EXISTS. `[measured 2026-08-28, run #205]` seasons
    2021, 2022 and 2023 all died on
    `weekly_rosters: asset 'roster_weekly_2021.csv.gz' not published`
    while 2024 and 2025 worked with the identical template. **nflverse's
    file naming is not stable across years** — the template is right for
    recent seasons and wrong for older ones.
    ⛔ AND THE OLD ERROR TOLD US NOTHING ABOUT WHAT *WAS* THERE, which is
    the only fact that could fix it. An error that does not name the
    alternatives is a dead end.

    ✅ So: try the exact name; then try any asset in the same release
    carrying the same year and a shared word; and either way **SAY WHICH
    NAME WAS USED** and, on failure, **LIST WHAT THE RELEASE ACTUALLY
    HOLDS** for that year.
    ⚠️ The fallback is deliberately narrow — same release, same year, and
    a word from the requested name. It will not silently substitute a
    different KIND of file, which is how `stats_player_reg` (season
    totals) nearly got fitted as if it were weekly.
    """
    assets = seen.get(tag, [])
    hit = [a for a in assets if a[0] == fname]

    if not hit:
        # 🔴 COMPRESSION IS NOT A SUBSTITUTION, AND THE LOOKUP MUST SAY SO
        # BEFORE THE WORD FALLBACK RUNS -- this function already applies
        # that rule when RECORDING a match, and did not apply it when
        # FINDING one.
        # `[measured 2026-09-01]` routes 2023 died on
        #   "asset 'pbp_participation_2023.csv.gz' not published, and 2
        #    candidates match -- refusing to guess between
        #    ['pbp_participation_2023.csv',
        #     'pbp_participation_old_2023.csv']"
        # ⛔ AND A COMMENT IN THIS FILE ASSERTED THAT COULD NOT HAPPEN:
        # "will not silently take the `old` one, because 'old' is a word
        # the requested name does not carry." **THAT REASONING WAS
        # BACKWARDS.** The fallback requires every word of the REQUESTED
        # name to appear in the CANDIDATE; an EXTRA word in the candidate
        # does not disqualify it. `pbp_participation_old_2023.csv`
        # carries every requested word plus one, so it matched too.
        # ✅ The ambiguity guard saved us -- ⚠️ but a comment claiming a
        # safety the code did not have is the more dangerous half.
        # ✅ THE FIX: an exact stem match, ignoring only `.gz`, is not a
        # guess. It also retires the routes debt where 2024/2025 were
        # resolving through the WORD FALLBACK rather than by name.
        _stem = fname[:-3] if fname.endswith(".gz") else fname
        exact = [a for a in assets
                 if (a[0][:-3] if a[0].endswith(".gz") else a[0]) == _stem]
        if len(exact) == 1:
            hit = exact
            log(f"  NOTE: '{fname}' published uncompressed as "
                f"'{exact[0][0]}' — same file, different packaging")

    if not hit:
        m = re.search(r"(\d{4})", fname)
        year = m.group(1) if m else None
        # 🔴 EVERY WORD MUST MATCH, NOT ANY. `[measured 2026-08-28,
        # run #206]` `any()` let `rosters_2021.csv.gz` (a SEASON roster,
        # one row per player) stand in for `roster_weekly_2021.csv.gz`
        # (one row per player PER WEEK). The build "succeeded" and the
        # bridge collapsed -- 2022 came out at **RB 75.0%, TE 70.8%,
        # WR 77.2%** against 2025's 99.6%.
        # ⛔ THAT IS EXACTLY THE SUBSTITUTION THIS FUNCTION'S OWN COMMENT
        # PROMISED IT WOULD NOT MAKE, and it made it on the first run.
        # ✅ `all()` means `roster_weekly_*` can only ever be satisfied by
        # an asset carrying BOTH "roster" AND "weekly".
        # 🔴 THE WORD MATCH MUST BE SYMMETRIC. `all(w in candidate)` asks
        # only that the candidate carries every REQUESTED word -- an
        # EXTRA word in the candidate does not disqualify it.
        # `[measured 2026-09-01, by test_assets.py]` with only
        # `pbp_participation_old_2023.csv` published, that rule resolves
        # `pbp_participation_2023.csv.gz` TO IT, silently, because one
        # candidate is not an ambiguity. ⛔ THE `old` FILE HAS A
        # DIFFERENT SCHEMA. That is precisely the substitution this
        # function's own comment promised it would never make -- the
        # same promise it already broke once, on `rosters_2021` standing
        # in for `roster_weekly_2021`.
        # ✅ SO COMPARE THE WORD SETS BOTH WAYS. A candidate with a word
        # the request does not carry is a DIFFERENT FILE.
        # ⚠️ The failure mode of being strict is a loud refusal that
        # names what it saw. The failure mode of being loose is a season
        # built from the wrong schema and nobody knowing.
        def _wordset(n):
            return {w for w in re.split(r"[_.]", n.lower())
                    if w and not w.isdigit() and w not in ("csv", "gz")}
        words = _wordset(fname)
        cand = [a for a in assets
                if year and year in a[0]
                and a[0].endswith((".csv", ".csv.gz"))
                and _wordset(a[0]) == words]
        if len(cand) == 1:
            log(f"  NOTE: '{fname}' not published; using '{cand[0][0]}' "
                f"from the same release (same year, matching name)")
            hit = cand
        elif cand:
            raise RuntimeError(
                f"{tag}: asset '{fname}' not published, and {len(cand)} "
                f"candidates match — refusing to guess between "
                f"{[c[0] for c in cand]}")

    if not hit:
        avail = sorted(a[0] for a in assets
                       if not year or year in a[0])[:20]
        # 🔴 DISTINGUISH "THE SOURCE HAS NOTHING FOR THIS YEAR AT ALL"
        # FROM "THE NAME IS WRONG". `[run #307, 2026-09-01]` the Tuesday
        # rebuild died on `stats_player_week_2026` before the 2026 season
        # had kicked off. ⛔ Nothing was broken; the season had not
        # happened. A red run every Tuesday until mid-September is noise,
        # and noise is how this project has lost real defects.
        # ⚠️ THE EXCEPTION ONLY CARRIES THE FACT. Whether it is FORGIVEN
        # is decided by the CALLER, which alone knows if this is the
        # current season -- see `freshness.current_football_season`.
        # ⛔ A missing 2019 raises the SAME class and is still fatal there.
        exc = SeasonNotStarted if (year and not avail) else RuntimeError
        raise exc(
            f"{tag}: asset '{fname}' not published. That release holds "
            f"{len(assets)} assets; those mentioning {year or 'any year'}: "
            f"{avail or 'NONE'}")

    # 🔴 RECORDED BEFORE THE DOWNLOAD, NOT AFTER. Which asset we RESOLVED
    # to is worth knowing even when fetching it then fails.
    # 🔴 REMEMBER WHICH FILE THIS ACTUALLY WAS. A season built from a
    # substituted asset must be able to SAY SO on its own face -- the
    # bridge collapse above was invisible in the output and only showed
    # up as a coverage number nobody would have questioned.
    # ⚠️ COMPRESSION IS NOT A SUBSTITUTION. nflverse publishes older
    # seasons UNCOMPRESSED (`roster_weekly_2021.csv`) and newer ones gzipped
    # (`roster_weekly_2025.csv.gz`). `[measured run #207]` that difference
    # alone made three good seasons fail the substitution check. ⛔ Record
    # it only when the STEM differs -- that is the case that can swap one
    # KIND of file for another.
    if hit[0][0].replace(".gz", "") != fname.replace(".gz", ""):
        USED[fname] = hit[0][0]

    blob = _raw(hit[0][2]).decode("utf-8", "replace")
    out = list(csv.DictReader(io.StringIO(blob)))
    log(f"  {hit[0][0]}: {len(out):,} rows")
    return out


def _num(v):
    if v in (None, "", "NA"):
        return 0.0
    try:
        return float(v)
    except ValueError:
        return 0.0


def build_routes(season, seen=None, log=print):
    """Pass snaps per receiver, from `pbp_participation`.

    🔴 WHY THIS IS NOT "ROUTES RUN", AND THE NAME SAYS SO. The file gives
    `offense_players` -- WHO WAS ON THE FIELD for each play. Joined to
    play-by-play's pass flag that is PASS SNAPS, which is the honest
    basis for a route rate. ⛔ A tight end who stayed in to block was on
    the field for that pass play. **Much closer than `tgt_per_snap`; not
    a charted route. Never label it one.**

    ⛔ PROBE-FIRST, LIKE THE CFB TARGET PARSE. I have not read a row of
    this file. So it reports its own columns and a coverage number, and
    writes NOTHING unless the join actually works. ⚠️ Tonight's CFB
    targets probe scored 53% against an 80% bar and was killed by a
    format nobody had looked at -- the identical risk lives here.
    """
    rep = {"season": season, "kind": "DIAGNOSTIC", "usable": False}
    if seen is None:
        # ⚠️ One extra release listing rather than threading state through
        # build_logs. ⛔ A caller that has to remember to pass the right
        # object is a caller that will eventually pass the wrong one.
        rels = _releases(log)
        seen = {r["tag_name"]: [(a_["name"], a_["size"],
                                a_["browser_download_url"])
                               for a_ in (r.get("assets") or [])]
                for r in rels}
        # 🔴 WRITE THE CANDIDATE LIST DOWN. build_logs has logged these
        # for days and an Actions log cannot be read from outside the
        # runner, so nobody has ever seen them.
        rep["release_tags_matching_participation"] = sorted(
            t for t in seen if "particip" in t.lower())
    # 🔴 THE LIST ENDPOINT EMBEDS ASSETS AND CAN COME BACK EMPTY.
    # `[measured 2026-09-01]` the `pbp_participation` release listed
    # ZERO assets through `/releases`, while other releases in the same
    # response listed theirs fine -- so the builder reported "not
    # published" for a release it had never actually opened.
    # ⛔ THAT IS THE SAME MISTAKE AS PAGE ONE OF A PAGINATED LIST, one
    # level down: I paginated the RELEASES and then trusted the ASSETS
    # embedded in them. On 2026-08-30 I told Sam this file publishes
    # 2016-2025. **THAT CLAIM CAME FROM THE SAME EMBEDDED LIST AND IS NOT
    # SAFE.**
    # ✅ So when a release looks empty, ASK IT DIRECTLY by tag and record
    # what it really holds -- including the YEARS, which is the fact that
    # decides whether this feature can exist at all.
    if not seen.get("participation"):
        try:
            one = _json(f"{GH_API}/tags/pbp_participation")
            assets = [(a_["name"], a_["size"], a_["browser_download_url"])
                      for a_ in (one.get("assets") or [])]
            seen["participation"] = assets
            rep["assets_via_tag_lookup"] = len(assets)
            yrs = sorted({m.group(1) for n, _, _ in assets
                          for m in [re.search(r"(\d{4})", n)] if m})
            rep["years_actually_published"] = yrs
            rep["asset_names"] = sorted(n for n, _, _ in assets)[:40]
            log(f"  direct tag lookup: {len(assets)} assets, years {yrs}")
        except Exception as e:
            rep["tag_lookup_error"] = f"{type(e).__name__}: {e}"
            log(f"  direct tag lookup failed: {rep['tag_lookup_error']}")

    try:
        part = _rows(seen, "participation",
                     FILES["participation"].format(y=season), log)
    except Exception as e:
        rep["error"] = f"{type(e).__name__}: {e}"
        log(f"  participation {season}: {rep['error']}")
        return None, rep
    if not part:
        rep["error"] = "no rows"
        return None, rep

    cols = sorted(part[0].keys())
    rep["columns"] = cols
    rep["rows"] = len(part)
    log(f"  participation {season}: {len(part):,} rows, {len(cols)} columns")
    # ⛔ NAME THE COLUMNS RATHER THAN ASSUMING THEM.
    idc = next((c for c in ("nflverse_game_id", "game_id", "old_game_id")
                if c in cols), None)
    plc = next((c for c in ("play_id", "nflverse_play_id") if c in cols), None)
    offc = next((c for c in ("offense_players", "offense_player_ids")
                 if c in cols), None)
    rep["id_columns"] = {"game": idc, "play": plc, "offense": offc}
    if not (idc and plc and offc):
        rep["error"] = ("the expected columns are absent; see `columns` "
                        "and map them before trying again")
        log(f"  ⛔ {rep['error']}")
        return None, rep

    filled = sum(1 for r in part if (r.get(offc) or "").strip())
    cov = round(100.0 * filled / max(1, len(part)), 2)
    rep["offense_players_filled_pct"] = cov
    log(f"  offense_players populated on {cov}% of plays")
    if cov < 80:
        rep["error"] = f"only {cov}% of plays list personnel"
        log(f"  ⛔ {rep['error']} -- nothing written")
        return None, rep

    # ── the pass flag comes from play-by-play, keyed on the same ids ──
    pbp = _rows(seen, "pbp", FILES["pbp"].format(y=season), log)
    pcols = set(pbp[0].keys()) if pbp else set()
    pidc = next((c for c in ("game_id", "nflverse_game_id", "old_game_id")
                 if c in pcols), None)
    ppc = next((c for c in ("play_id",) if c in pcols), None)
    passc = next((c for c in ("pass", "pass_attempt") if c in pcols), None)
    rep["pbp_columns_used"] = {"game": pidc, "play": ppc, "pass": passc}
    if not (pidc and ppc and passc):
        rep["error"] = "play-by-play lacks a usable pass flag"
        log(f"  ⛔ {rep['error']}")
        return None, rep
    ispass = {}
    for r in pbp:
        try:
            ispass[(r[pidc], str(int(float(r[ppc]))))] = \
                str(r.get(passc)).strip() in ("1", "1.0", "True", "true")
        except Exception:
            continue

    snaps = collections.defaultdict(lambda: {"snaps": 0, "pass_snaps": 0})
    joined = 0
    for r in part:
        try:
            k = (r[idc], str(int(float(r[plc]))))
        except Exception:
            continue
        p_ = ispass.get(k)
        if p_ is None:
            continue
        joined += 1
        for pid in (r.get(offc) or "").split(";"):
            pid = pid.strip()
            if not pid:
                continue
            s_ = snaps[(r[idc], pid)]
            s_["snaps"] += 1
            if p_:
                s_["pass_snaps"] += 1
    jcov = round(100.0 * joined / max(1, len(part)), 2)
    rep["play_join_pct"] = jcov
    log(f"  joined {jcov}% of participation rows to a pbp pass flag")
    if jcov < 80:
        rep["error"] = f"the play join only reached {jcov}%"
        log(f"  ⛔ {rep['error']} -- nothing written")
        return None, rep

    out = collections.defaultdict(dict)
    for (gid, pid), v in snaps.items():
        out[pid][gid] = [v["snaps"], v["pass_snaps"]]
    rep["usable"] = True
    rep["players"] = len(out)
    log(f"  ✅ pass snaps for {len(out):,} players")
    return {"season": season, "kind": "DESCRIPTIVE",
            "note": ("Per player per game: [snaps, pass_snaps] from "
                     "nflverse pbp_participation joined to the pbp pass "
                     "flag. ⛔ THIS IS NOT ROUTES RUN -- a tight end who "
                     "stayed in to block was on the field for that pass "
                     "play. It is much closer than tgt_per_snap and it "
                     "is not a charted route."),
            "join_coverage_pct": jcov,
            "by_player": {k: v for k, v in out.items()}}, rep


def build_def_epa(season, seen=None, log=print):
    """Defensive EPA per play allowed, per defence per game. **T48.**

    🔴 WHY THIS EXISTS AND WHY IT IS NOT A SIXTH BOX-SCORE CONSTRUCT.
    T42's pre-committed consequence, written before its result was seen:
    *"the NFL layer needs an EXTERNAL rating (an EPA- or DVOA-style
    measure), not another aggregate of the data we already hold."* T43
    repeated it -- four constructs, five measures, every one below the
    0.35 bar. ⛔ Another yards-allowed variant is the exact move the owed
    -tests register was created to forbid.

    ✅ EPA IS THE MEASURE T42 NAMED, and it is already inside a file this
    collector already downloads: nflverse `play_by_play_{y}`, which
    `build_routes` fetches for its pass flag. ⚠️ No new source, no new
    cost, no new vendor.

    ⚠️ WHY IT IS GENUINELY DIFFERENT. Yards allowed is a raw count. EPA
    conditions every play on down, distance, field position and game
    state -- a 4-yard gain on 3rd-and-3 and on 3rd-and-8 are opposite
    outcomes and yardage cannot tell them apart. ⛔ A reason to TEST it,
    not a reason to expect it to pass.

    🔴 SIGN CONVENTION, STATED HERE SO IT CANNOT BE FLIPPED LATER TO SUIT
    A RESULT: `epa` is signed from the OFFENCE's perspective, so for the
    defence **LOWER IS BETTER.**

    ⚠️ A PER-PLAY RATE BY CONSTRUCTION. T42 flagged that a team total is
    partly a measure of PACE -- a team whose own offence plays fast puts
    its defence on the field more. ✅ Dividing by plays is the fix T42
    demanded of any value test, built into the measure rather than bolted
    on afterwards.

    ⛔ FAIL-CLOSED. Columns are NAMED, not assumed, and nothing is written
    if the defence id, the epa or the play type is absent or thin. A
    probe report is written either way. ⚠️ This is the same discipline
    that made `routes` trustworthy -- and the reason the two seasons of
    routes could be believed was that the bars were declared first.
    """
    log(f"=== nfl: defensive EPA per play, {season} (T48) ===")
    rep = {"season": season, "kind": "DIAGNOSTIC", "usable": False,
           "test": "T48", "bar": "columns present on >= 80% of rows"}
    if seen is None:
        seen = {r["tag_name"]: [(a["name"], a["size"],
                                 a["browser_download_url"])
                                for a in (r.get("assets") or [])]
                for r in _releases(log)}
    try:
        pbp = _rows(seen, "pbp", FILES["pbp"].format(y=season), log)
    except Exception as e:
        rep["error"] = f"{type(e).__name__}: {e}"
        log(f"  ⛔ {rep['error']}")
        return None, rep
    if not pbp:
        rep["error"] = "no play-by-play rows"
        return None, rep
    cols = set(pbp[0].keys())
    rep["rows"] = len(pbp)

    # ⛔ NAME THE COLUMNS. The `stats_player_reg` season-totals trap and a
    # name join that matched 0 of 1,848 both came from assuming a schema.
    defc = next((c for c in ("defteam", "defensive_team") if c in cols), None)
    epac = "epa" if "epa" in cols else None
    gidc = next((c for c in ("game_id", "nflverse_game_id") if c in cols), None)
    wkc = next((c for c in ("week",) if c in cols), None)
    posc = "posteam" if "posteam" in cols else None
    passc = next((c for c in ("pass", "pass_attempt") if c in cols), None)
    rushc = next((c for c in ("rush", "rush_attempt") if c in cols), None)
    rep["columns_used"] = {"defence": defc, "epa": epac, "game": gidc,
                           "week": wkc, "offence": posc,
                           "pass": passc, "rush": rushc}
    missing = [k for k, v in rep["columns_used"].items() if not v]
    if missing:
        rep["error"] = f"play-by-play lacks: {missing}"
        rep["columns_available"] = sorted(cols)[:80]
        log(f"  ⛔ {rep['error']}")
        return None, rep

    def _f(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _flag(v):
        return str(v).strip() in ("1", "1.0", "True", "true")

    # ── measure ───────────────────────────────────────────────────────
    tbl = collections.defaultdict(lambda: {
        "week": None, "opp": None,
        "plays": 0, "epa": 0.0,
        "pass_plays": 0, "pass_epa": 0.0,
        "rush_plays": 0, "rush_epa": 0.0})
    kept = with_epa = 0
    for r in pbp:
        d_, g_ = (r.get(defc) or "").strip(), (r.get(gidc) or "").strip()
        if not d_ or not g_ or d_ in ("NA", "None"):
            continue
        p_, u_ = _flag(r.get(passc)), _flag(r.get(rushc))
        # ⚠️ Plays that are neither a pass nor a rush -- kicks, punts,
        # penalties with no play, timeouts, kneels flagged as neither --
        # are EXCLUDED. ⛔ Not a filter chosen after seeing a result: the
        # spec says "plays where the play is a pass or a rush", fixed
        # before any of this was written.
        if not (p_ or u_):
            continue
        kept += 1
        e_ = _f(r.get(epac))
        if e_ is None:
            continue
        with_epa += 1
        c_ = tbl[(d_, g_)]
        if c_["week"] is None:
            c_["week"] = _f(r.get(wkc))
            c_["opp"] = (r.get(posc) or "").strip()
        c_["plays"] += 1
        c_["epa"] += e_
        if p_:
            c_["pass_plays"] += 1
            c_["pass_epa"] += e_
        else:
            c_["rush_plays"] += 1
            c_["rush_epa"] += e_

    cov = round(100.0 * with_epa / max(1, kept), 2)
    rep["pass_or_rush_plays"] = kept
    rep["epa_populated_pct"] = cov
    rep["defences"] = len({d for d, _ in tbl})
    rep["team_games"] = len(tbl)
    log(f"  {kept:,} pass/rush plays, epa populated on {cov}%, "
        f"{rep['defences']} defences, {rep['team_games']} team-games")
    # ⛔ THE BAR, DECLARED IN T48 BEFORE THIS FUNCTION EXISTED.
    if cov < 80:
        rep["error"] = f"epa populated on only {cov}% of pass/rush plays"
        log(f"  ⛔ {rep['error']} -- writing NOTHING")
        return None, rep

    out = collections.defaultdict(dict)
    for (d_, g_), c_ in tbl.items():
        if not c_["plays"]:
            continue
        out[d_][g_] = {
            "week": c_["week"], "opp": c_["opp"], "plays": c_["plays"],
            "epa_per_play": round(c_["epa"] / c_["plays"], 5),
            "pass_plays": c_["pass_plays"],
            "pass_epa_per_play": (round(c_["pass_epa"] / c_["pass_plays"], 5)
                                  if c_["pass_plays"] else None),
            "rush_plays": c_["rush_plays"],
            "rush_epa_per_play": (round(c_["rush_epa"] / c_["rush_plays"], 5)
                                  if c_["rush_plays"] else None)}
    rep["usable"] = True
    # ⚠️ NO TIMESTAMP IS SET HERE. `collect.py`'s `write()` stamps
    # `written_at` on every artifact it writes and `pulled_at` at the call
    # site, exactly as it does for routes. ⛔ A second writer of the same
    # field is how the site ended up quoting two projections for one
    # pitcher (rule 66).
    return {"season": season,
            # ⚠️ DESCRIPTIVE until T48 passes reliability AND a value test
            # clears its pre-declared +0.005 Brier bar. ⛔ Rule 55: this
            # number never wears a Gizmo's confidence % on that basis
            # alone.
            "kind": "DESCRIPTIVE",
            "test": "T48",
            "note": ("Mean nflverse EPA allowed per pass-or-rush play, per "
                     "defence per game. EPA is signed from the OFFENCE's "
                     "perspective: LOWER IS BETTER FOR THE DEFENCE. A "
                     "per-play rate, so it is not a measure of pace."),
            "epa_populated_pct": cov,
            "by_team": dict(out)}, rep


def build_schedule(season, seen=None, log=print):
    """Schedule and final scores for one season. **Feeds the Scores tab.**

    ✅ FREE AND ALREADY DOWNLOADED. `games.csv.gz` is the same file
    `build_logs` reads for kickoff dates, and `[per this file's own
    note]` it is NOT year-partitioned -- one 512KB file covers every
    season, which is why a 2026 schedule can exist before a single 2026
    game has been played.

    🔴 THE SCORE COLUMNS ARE PROBED, NOT ASSUMED. `build_logs` reads
    season, week, gameday, game_id, home_team, away_team, roof, surface,
    temp and wind from this file -- and NO SCORE COLUMN. ⛔ So
    `home_score`/`away_score` are documentation until this function has
    seen them.

    ⚠️ A SEASON WITH A SCHEDULE AND NO SCORES IS THE NORMAL STATE in
    September. ⛔ It is not SeasonNotStarted, which is the source having
    nothing for the year at all.

    ✅ Returns a shape IDENTICAL to cfb.build_schedule so ONE renderer
    serves both leagues.
    """
    log(f"=== nfl: schedule {season} ===")
    rep = {"season": season, "kind": "DIAGNOSTIC", "usable": False}
    if seen is None:
        seen = {r["tag_name"]: [(a["name"], a["size"],
                                 a["browser_download_url"])
                                for a in (r.get("assets") or [])]
                for r in _releases(log)}
    try:
        sched = _rows(seen, "schedules", SCHEDULE_FILE, log)
    except Exception as e:
        rep["error"] = f"{type(e).__name__}: {e}"
        log(f"  ⛔ {rep['error']}")
        return None, rep
    if not sched:
        rep["error"] = "schedule file is empty"
        return None, rep

    cols = set(sched[0].keys())
    rep["columns_available"] = sorted(cols)[:80]
    hs = next((c for c in ("home_score", "home_points") if c in cols), None)
    aws = next((c for c in ("away_score", "away_points") if c in cols), None)
    gd = next((c for c in ("gameday", "game_date") if c in cols), None)
    gt = next((c for c in ("gametime",) if c in cols), None)
    rep["columns_used"] = {"home_score": hs, "away_score": aws,
                           "date": gd, "time": gt}
    if not (hs and aws):
        log(f"  ⚠️ no score columns -- schedule only. saw: {sorted(cols)[:20]}")

    def _i(v):
        # ⚠️ 0 is a REAL score. Never coerce it to missing.
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None

    out, finals = [], 0
    for g in sched:
        if str(g.get("season")) != str(season):
            continue
        h = _i(g.get(hs)) if hs else None
        a = _i(g.get(aws)) if aws else None
        done = h is not None and a is not None
        if done:
            finals += 1
        day = (g.get(gd) or "") if gd else ""
        tm = (g.get(gt) or "") if gt else ""
        out.append({
            "id": g.get("game_id"),
            "week": _i(g.get("week")),
            "season_type": g.get("game_type") or g.get("season_type") or "",
            # ⚠️ nflverse gives a LOCAL date and a LOCAL time in separate
            # columns and no timezone. ⛔ They are carried as-is and NOT
            # stitched into a fake UTC stamp -- an invented offset would
            # put a Sunday 1pm game on the wrong day for half the world.
            "start": (day + ("T" + tm if tm else "")) or None,
            "home": g.get("home_team"), "away": g.get("away_team"),
            # ⚠️ NULL ON PURPOSE, so both leagues emit the SAME KEYS.
            # The NFL has one division of 32 teams; there is nothing to
            # classify and nothing to filter out. ⛔ Omitting the keys
            # instead would break the one-renderer-serves-both contract.
            "home_conf": None, "away_conf": None,
            "home_class": None, "away_class": None,
            "neutral": str(g.get("location") or "").lower() == "neutral",
            "home_score": h, "away_score": a,
            # 🔴 NO LINE SCORES EXIST IN nflverse SCHEDULES. The probe
            # lists every column and there is no per-quarter field --
            # CFBD gives them free, nflverse does not. ⛔ The key is
            # emitted as None so BOTH leagues carry the same shape and the
            # one renderer can say "not available" instead of crashing.
            # ⚠️ Do not fabricate quarters from `result`.
            "home_line": None, "away_line": None,
            # ⚠️ nflverse ALREADY CARRIES these and we were dropping them.
            # They cost nothing extra -- same file, same call.
            "venue": g.get("stadium"),
            "roof": g.get("roof"), "surface": g.get("surface"),
            "temp": _i(g.get("temp")), "wind": _i(g.get("wind")),
            "overtime": bool(_i(g.get("overtime")) or 0),
            "div_game": bool(_i(g.get("div_game")) or 0),
            # 🔵 MARKET, from the schedule file itself. ⛔ These are
            # nflverse's CLOSING numbers, NOT our live board -- they are
            # labelled market_closing so nothing confuses them with the
            # prices on the Odds tab.
            "closing_ml_home": _i(g.get("home_moneyline")),
            "closing_ml_away": _i(g.get("away_moneyline")),
            "closing_spread": g.get("spread_line"),
            "closing_total": g.get("total_line"),
            "final": done,
        })
    out.sort(key=lambda r: (r["start"] or "", r["home"] or ""))
    rep["games"] = len(out)
    rep["final"] = finals
    if not out:
        rep["error"] = f"no {season} rows in the schedule file"
        log(f"  ⛔ {rep['error']}")
        return None, rep
    rep["usable"] = True
    log(f"  {len(out):,} games, {finals:,} final")
    return {"season": season, "kind": "DESCRIPTIVE",
            "note": ("Schedule and final scores from nflverse `games.csv.gz`. "
                     "DESCRIPTIVE -- these are results, not projections. "
                     "Kickoff is the LOCAL date/time the feed publishes; no "
                     "timezone is invented."),
            "columns_used": rep["columns_used"],
            "games": out}, rep


def build_logs(season, log=print):
    """Per-player point-in-time game logs for one season."""
    log(f"=== nfl: building {season} player logs ===")
    rels = _releases(log)
    seen = {r["tag_name"]: [(a["name"], a["size"], a["browser_download_url"])
                            for a in (r.get("assets") or [])] for r in rels}

    # 🔴 ROUTE PARTICIPATION — Sam's point 4, the one item of his framework
    # still missing. ⛔ NO COLLECTOR IS WRITTEN HERE, ON PURPOSE. nflverse
    # has carried route data in more than one place over the years (a
    # `participation` set that was discontinued, and PFR advanced stats),
    # and writing a parser against a remembered column name is exactly the
    # mistake that produced the `stats_player_reg` season-totals trap and a
    # name join that matched 0 of 1,848. **ASK THE SOURCE.**
    _cand = []
    for _tag, _assets in seen.items():
        for _name, _size, _u in _assets:
            _low = (_tag + "/" + _name).lower()
            if any(k in _low for k in ("particip", "advstat", "route",
                                       "pfr", "ngs", "snap", "ftn",
                                       "charting", "pbp_particip")):
                _cand.append(f"{_tag}/{_name} ({_size/1e6:.1f}MB)")
    log(f"  ROUTE-DATA CANDIDATES across {len(seen)} releases:")
    for c in sorted(_cand)[:40]:
        log(f"    {c}")
    log(f"    ({len(_cand)} candidate assets total)")
    # ⚠️ Say what the query covered, so the next reader knows what the
    # absence does and does not prove.
    log(f"    release tags searched: {sorted(seen)[:40]}")
    if not _cand:
        log("    NONE FOUND in the releases listed above. ⛔ That is a "
            "fact about THIS query, not about the world.")

    USED.clear()
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
    # 🔴 A THIN BRIDGE IS A HOLE IN THE MODEL, BUT REFUSING TO WRITE THE
    # SEASON IS NOT THE FIX — IT IS JUST A DIFFERENT HOLE.
    # `[measured 2026-08-28, run #205]` 2024 was REJECTED ENTIRELY on
    # FB 63.0%, RB 93.4%, TE 90.7%, WR 91.3% — so a season that is ~92%
    # usable produced NOTHING, and the season simply did not exist.
    # ⚠️ AND THE 9% THAT DOES NOT BRIDGE IS NOT RANDOM: it is players whose
    # PFR id changed, which skews toward mid-season signings and team
    # changes. **That is a real bias and it must travel WITH the data.**
    # ✅ So the season is written, the coverage is stored on the document,
    # and a consumer contract states the rule. ⛔ The bar has not moved —
    # what changed is that falling short now DEGRADES the season instead
    # of DELETING it, and says so on the file rather than in a lost log.
    bridge_ok = not thin
    bridge_cov = {pos: round(100.0 * have[pos] / (have[pos] + miss[pos]), 1)
                  for pos in sorted(PROP_POS)
                  if (have[pos] + miss[pos])}
    if thin:
        log(f"  ⚠️ BRIDGE BELOW {BRIDGE_MIN}% on: {', '.join(thin)}")
        log(f"     The season IS written and marked bridge_ok=false. "
            f"Unbridged players have NO snap data, so they fall below the "
            f"snap floor and never reach vs-position.")
        log(f"     ⛔ DO NOT FIT A MODEL on a season with bridge_ok=false "
            f"without saying so — the missing players are not a random "
            f"sample.")

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

    # 🔴 DIAGNOSTICS, ADDED 2026-08-28 BECAUSE `verify_nfl.py` FOUND BOTH
    # TRENCH COLUMNS CONSTANT-ZERO ON ALL 19,400 ROWS OF THE 2025 BUILD.
    # ⛔ THAT IS THE THIRD FOOTBALL COLUMN TO SHIP AS ZEROES ON A GREEN RUN.
    # The cause cannot be read off the OUTPUT -- a zero looks identical
    # whether nobody was hurt, the position codes did not match, or the
    # team lookup missed. So the run now SAYS WHICH.
    # ⚠️ This is logging, not a guessed fix: nothing here changes
    # behaviour, it only makes the next run answer the question.
    _no_pos = sum(1 for _g, _w in out_set if not pos_of.get(_g))
    _no_team = sum(1 for _g, _w in out_set if not team_of.get((_g, _w)))
    _pos_seen = collections.Counter(
        pos_of.get(_g) or "(no position on roster)" for _g, _w in out_set)
    _none = "NONE — the position codes do not match"
    log(f"  TRENCH DIAGNOSTIC — out_set has {len(out_set):,} player-weeks")
    log(f"    unresolved POSITION : {_no_pos:,}")
    log(f"    unresolved TEAM     : {_no_team:,}   <- these are skipped")
    log(f"    positions among OUT players: {dict(_pos_seen.most_common(18))}")
    log(f"    OL_POS this code looks for: {sorted(OL_POS)}")
    log(f"    DL_POS this code looks for: {sorted(DL_POS)}")
    log(f"    MATCHED OL codes: {sorted({p for p in _pos_seen if p in OL_POS}) or _none}")
    log(f"    MATCHED DL codes: {sorted({p for p in _pos_seen if p in DL_POS}) or _none}")
    if not ol_out and not dl_out:
        log("    BOTH TRENCH COLUMNS WILL BE CONSTANT ZERO. The lines above "
            "say whether the position codes are wrong, the team lookup "
            "missed, or nobody was actually out.")

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
        # 🔴 ROUTE PARTICIPATION IS NOT PUBLISHED. `[measured 2026-08-28,
        # run #205]` the nflverse releases carry only `pfr_rosters` and
        # `nextgen_stats` (passing/receiving/rushing) — **there is no
        # participation file and no routes-run column anywhere in them.**
        # ⛔ SO THIS IS NOT ROUTE PARTICIPATION AND MUST NEVER BE CALLED
        # THAT. It is TARGETS PER OFFENSIVE SNAP, which answers the
        # question Sam actually asked — *"whats his route run%, how often
        # is he utilized in the passing game"* — from data we have.
        # ✅ What it separates: a tight end on the field to BLOCK carries a
        # high snap count and almost no targets; one on the field to CATCH
        # carries the same snaps and a real target rate. That gap is the
        # thing worth seeing, and it does not need a routes column.
        # ⚠️ What it CANNOT do: distinguish a receiver who ran a route and
        # was not thrown to from one who stayed in to block. **A true
        # route rate would. This is a proxy and is labelled one.**
        for src, dst in STAT_COLS.items():
            row[dst] = _num(r.get(src))
        # ⛔ COMPUTED HERE AND NOT ONE LINE EARLIER. The first version of
        # this sat ABOVE the STAT_COLS loop and divided a `tgt` that did
        # not exist yet, so it was **0.0 on all 94,738 player-weeks across
        # five seasons** -- and every run was green. `verify_nfl.py`'s
        # constant-feature check caught it, which is the fourth football
        # column to ship as zeroes and the first one caught before Sam saw
        # it. 🔴 A DERIVED FIELD MUST BE COMPUTED AFTER ITS INPUTS.
        if row.get("snaps"):
            row["tgt_per_snap"] = round(row.get("tgt", 0.0) / row["snaps"], 4)
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
    return {"season": season, "source": "nflverse", "players": players,
            "source_assets": dict(USED),
            "substituted": {k: v for k, v in USED.items() if k != v},
            "bridge_ok": bridge_ok, "bridge_coverage": bridge_cov,
            "bridge_min": BRIDGE_MIN,
            "consumer_contract": (
                "REFUSE TO FIT A MODEL WHILE bridge_ok IS false, or say so "
                "explicitly. Unbridged players carry no snap counts, so "
                "they never clear the snap floor and never appear in "
                "vs-position -- and they are not a random sample of "
                "players.")}


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


# ══════════════════════════════════════════════════════════════════════
# ALLOWED-BY-POSITION — the defensive tracking table
# 🔴 DESCRIPTIVE (ledger rule 55). What a defence HAS ALLOWED per game by
# position. NO confidence number, not a model output.
# 📌 Sam, 2026-08-30: "i want you to track this data ... touchdowns
# allowed vs certain positions, yards allowed vs certain positions".
# ⛔ RANK 1 = ALLOWS THE MOST -- the question asked of it is "how soft is
# this defence", not "how good".
# ⚠️ THIS IS THE NFL TWIN OF `cfb.py`'s `build_allowed` AND THE TWO MUST
# STAY THE SAME SHAPE, because one page reads both. ⛔ The ONE column that
# is NOT comparable across the leagues is QB rushing: college charges SACK
# YARDAGE to rushing and the NFL charges it to passing. `[measured
# 2026-08-30]` CFB QB rushing reaches -73 with 23.5% of rows negative; the
# NFL bottoms at -10 with 11.6%.
# ══════════════════════════════════════════════════════════════════════
DEF_FIELDS = ("rec", "rec_yds", "rec_td", "car", "rush_yds", "rush_td",
              "att", "cmp", "pass_yds", "pass_td", "int")
DEF_POS = ("QB", "RB", "WR", "TE")
DEF_MIN_GAMES = 8


def build_allowed(doc, log=None):
    """⚠️ BACK-COMPAT. `build_side(doc, "def")` is the real entry point.
    Kept so any existing caller or test keeps working."""
    return build_side(doc, "def", log) if log else build_side(doc, "def")


def build_side(doc, side, log=print):
    """`side='def'` groups by the OPPONENT -- what a defence ALLOWED.
    `side='off'` groups by the TEAM -- what an offence PRODUCED.

    🔴 ONE FUNCTION, TWO SIDES, ON PURPOSE. Sam asked for an offensive
    trends board alongside the defensive one. ⛔ Writing a second
    aggregator would be two copies of one calculation, and this project
    has a documented history of two copies of a number drifting apart.
    The ONLY difference between the two boards is which key the rows are
    grouped under.
    ⚠️ RANK MEANS THE OPPOSITE THING ON EACH SIDE and the file says so:
    on DEFENCE rank 1 allows the most (softest); on OFFENCE rank 1
    produces the most (best). Same direction of sort, opposite meaning.
    """
    acc = collections.defaultdict(lambda: collections.defaultdict(float))
    games = collections.defaultdict(set)
    for pid, p in doc["players"].items():
        pos = p["pos"]
        if pos not in DEF_POS:
            continue
        for g in p["g"]:
            o = g.get("o") if side == "def" else g.get("team")
            if not o:
                continue
            games[o].add(g.get("game_id") or f'{g.get("week")}-{o}')
            a = acc[(o, pos)]
            for f in DEF_FIELDS:
                v = g.get(f)
                if v is not None:
                    a[f] += float(v)
    tbl = {}
    for (o, pos), a in acc.items():
        n = len(games[o])
        if n:
            tbl.setdefault(o, {})[pos] = {
                "games": n, **{f: round(a[f] / n, 3) for f in DEF_FIELDS}}
    # 🔴 THE RANK FLOOR TRACKS SEASON PROGRESS. Sam, 2026-09-01: the
    # board has to be useful "week by week, day by day", and a fixed
    # 8-game floor ranks NOBODY until November.
    # ⚠️ THREE STATISTICS WERE TRIED AND THE FIRST TWO WERE WRONG IN
    # OPPOSITE DIRECTIONS `[measured across a simulated 2025 season]`:
    #   max()    -- dragged UP by the few teams who played twice in week
    #               one; at week 1 it ranked 1 defence of 69.
    #   median() -- dragged DOWN by the long tail of G5/FCS defences a
    #               Power 4 offence faces exactly once; at full season it
    #               sat at 2 and ranked 102 of 186, letting one-game
    #               samples in beside a full schedule.
    #   p75      -- ✅ week 1 ranks 69/69; FULL SEASON lands on 8 and
    #               ranks exactly 68 -- the Power 4 set itself.
    # ⛔ The floor is written into the file so the page can SAY what a
    # rank is standing on. A rank off one game is honest only if the
    # reader can see it is one game.
    _played = sorted(v["games"] for t_ in tbl.values() for v in t_.values())
    _p75 = _played[int(0.75 * len(_played))] if _played else DEF_MIN_GAMES
    min_games = max(1, min(DEF_MIN_GAMES, _p75))
    for pos in DEF_POS:
        for f in DEF_FIELDS:
            rows = sorted(((o, t[pos][f]) for o, t in tbl.items()
                           if pos in t and t[pos]["games"] >= min_games),
                          key=lambda x: -x[1])
            for i, (o, _) in enumerate(rows):
                tbl[o][pos][f + "_rank"] = i + 1
                tbl[o][pos][f + "_pct"] = round(
                    100.0 * (len(rows) - i) / len(rows), 1)
    if not tbl:
        raise RuntimeError("allowed-by-position is EMPTY -- an opponent join "
                           "failure, not a finding")
    log(f"  {side}-by-position: {len(tbl)} teams")
    return {"season": doc["season"], "kind": "DESCRIPTIVE",
            "side": side,
            "rank_note": ("rank 1 = ALLOWS THE MOST; pct 100 = softest"
                          if side == "def" else
                          "rank 1 = PRODUCES THE MOST; pct 100 = best"),
            "min_games_for_rank": min_games,
            "rank_floor_is_full": min_games >= DEF_MIN_GAMES,
            "caveat_qb_rush": (
                "⛔ NOT COMPARABLE TO THE CFB COLUMN OF THE SAME NAME. The "
                "NFL charges sack yardage to PASSING; college charges it to "
                "RUSHING. CFB QB rushing allowed is therefore largely a "
                "pass-rush measure and this one is not."),
            ("defences" if side == "def" else "offences"): tbl}


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
