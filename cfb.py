"""COLLEGE FOOTBALL — CAN CFBD GIVE US THE SAME 29 FIELDS AS THE NFL?

🔴 THIS FILE WRITES NO DATA. It is a PARITY CHECK.

Sam, 2026-08-30: *"i want the SAME EXACT stats and data pulled for cfb as
we did for the nfl."* ✅ That is the right requirement — a football board
that means one thing for the NFL and something else for college is worse
than no board. **So this probe does not ask "what does CFBD have?" It
asks, field by field, "does CFBD have THIS?"** and reports every gap.

⛔ IT DOES NOT GUESS. Every football bug this project shipped came from
parsing a REMEMBERED schema instead of a measured one:
  - `stats_player_reg` (season TOTALS) nearly fitted as weekly
  - a name join matching **0 of 1,848** players
  - `ahead_out` **constant zero on 19,400 rows**, on a green run
  - "route participation is not published" — from page ONE of a
    paginated list. It is published, for every season we have.

⚠️ AND THE LIKELIEST FINDING, STATED BEFORE THE RUN SO IT CANNOT BE
DRESSED UP AFTERWARDS: **college football has no mandated injury
report.** The NFL requires one; the NCAA does not. If that holds, FOUR of
our fields -- `inj`, `ahead_out`, `ol_out`, `opp_dl_out` -- have no
college equivalent at all. **That is a structural difference between the
sports, not a sourcing problem, and no amount of API hunting fixes it.**
🔴 **If it is true, the CFB board must SAY it is missing them rather than
quietly showing a thinner product that looks the same.**
"""

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.collegefootballdata.com"
KEY = os.environ.get("CFBD_API_KEY", "").strip()
POWER4 = {"SEC", "Big Ten", "ACC", "Big 12"}

# 🔴 THE TARGET. Every per-game field the NFL layer produces, and what it
# is for. ⛔ Do not trim this list to make the result look better.
#   (field, group, what it is)
TARGET = [
    ("d",            "context", "game date"),
    ("week",         "context", "week number"),
    ("team",         "context", "his team"),
    ("o",            "context", "opponent"),
    ("home",         "context", "home or away"),
    ("game_id",      "context", "join key"),
    ("snaps",        "DEPTH",   "offensive snaps -- the depth-rank foundation"),
    ("snap_pct",     "DEPTH",   "share of his team's snaps"),
    ("tgt_share",    "DEPTH",   "share of team targets"),
    ("ay_share",     "DEPTH",   "share of team air yards"),
    ("att",          "box",     "pass attempts"),
    ("cmp",          "box",     "completions"),
    ("pass_yds",     "box",     "passing yards"),
    ("pass_td",      "box",     "passing TDs"),
    ("int",          "box",     "interceptions"),
    ("car",          "box",     "carries"),
    ("rush_yds",     "box",     "rushing yards"),
    ("rush_td",      "box",     "rushing TDs"),
    ("tgt",          "box",     "targets"),
    ("rec",          "box",     "receptions"),
    ("rec_yds",      "box",     "receiving yards"),
    ("rec_td",       "box",     "receiving TDs"),
    ("ay",           "box",     "air yards"),
    ("inj",          "INJURY",  "injury designation"),
    ("ahead_out",    "INJURY",  "a higher-usage teammate is OUT"),
    ("ol_out",       "INJURY",  "his own linemen missing"),
    ("opp_dl_out",   "INJURY",  "opposing rushers missing"),
    ("wx",           "weather", "roof / surface / temp / wind"),
]

# Words that would satisfy each field, matched against real column names.
WORDS = {
    "d": ("date", "start"), "week": ("week",), "team": ("team", "school"),
    "o": ("opponent", "defense", "away", "home"), "home": ("home", "site"),
    "game_id": ("game", "id"),
    "snaps": ("snap", "play", "participation"),
    "snap_pct": ("snap", "usage", "percent", "share", "overall"),
    "tgt_share": ("target", "usage", "share"),
    "ay_share": ("air", "share"),
    "att": ("attempt", "att"), "cmp": ("completion", "cmp"),
    "pass_yds": ("passing", "pass"), "pass_td": ("td", "touchdown"),
    "int": ("int", "interception"),
    "car": ("carr", "rushing", "att"), "rush_yds": ("rushing", "rush"),
    "rush_td": ("td", "touchdown"),
    "tgt": ("target",), "rec": ("rec", "reception"),
    "rec_yds": ("receiving", "rec"), "rec_td": ("td", "touchdown"),
    "ay": ("air",),
    "inj": ("injur", "status", "availab"),
    "ahead_out": ("injur", "status"), "ol_out": ("injur", "status"),
    "opp_dl_out": ("injur", "status"),
    "wx": ("weather", "temp", "wind", "precip", "dome", "surface"),
}

PROBES = [
    ("teams",         "/teams/fbs",           {"year": "2025"}),
    ("games",         "/games",               {"year": "2025", "week": "3",
                                               "seasonType": "regular"}),
    ("weather",       "/games/weather",       {"year": "2025", "week": "3"}),
    ("player game",   "/games/players",       {"year": "2025", "week": "3",
                                               "seasonType": "regular"}),
    ("player usage",  "/player/usage",        {"year": "2025"}),
    ("season stats",  "/stats/player/season", {"year": "2025",
                                               "category": "receiving"}),
    ("play by play",  "/plays",               {"year": "2025", "week": "3",
                                               "seasonType": "regular"}),
    ("injuries?",     "/player/injuries",     {"year": "2025"}),
    ("roster",        "/roster",              {"year": "2025",
                                               "team": "Alabama"}),
]


def log(m):
    print(m, flush=True)


def get(path, params, timeout=60):
    q = "&".join(f"{k}={v}" for k, v in (params or {}).items())
    url = f"{API}{path}" + (f"?{q}" if q else "")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {KEY}",
        "Accept": "application/json",
        "User-Agent": "gizmos-picks/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def flat_keys(rows, depth=0):
    """Column names, descending one level into nested lists/dicts --
    CFBD nests player stats inside teams inside categories."""
    keys = set()
    if isinstance(rows, dict):
        rows = [rows]
    for r in (rows or [])[:40]:
        if not isinstance(r, dict):
            continue
        for k, v in r.items():
            keys.add(k)
            if depth < 3 and isinstance(v, (list, dict)):
                keys |= {f"{k}.{s}" for s in flat_keys(v, depth + 1)}
    return keys


def probe(log=log):
    if not KEY:
        log("FATAL: CFBD_API_KEY is not set. Add it as a repository secret.")
        return False

    log("=" * 72)
    log("CFBD PARITY PROBE — can college give us the SAME 29 NFL fields?")
    log("=" * 72)

    found, failures = {}, []
    for name, path, params in PROBES:
        log(f"\n=== {name}  {path}  {params} ===")
        try:
            rows = get(path, params)
        except urllib.error.HTTPError as e:
            log(f"    HTTP {e.code} {e.reason}"
                + ("   <- endpoint does not exist or needs a paid tier"
                   if e.code in (401, 403, 404) else ""))
            failures.append((name, f"HTTP {e.code}"))
            continue
        except Exception as e:
            log(f"    {type(e).__name__}: {e}")
            failures.append((name, type(e).__name__))
            continue
        n = len(rows) if isinstance(rows, list) else 1
        keys = flat_keys(rows)
        found[name] = keys
        log(f"    {n:,} rows, {len(keys)} distinct columns")
        log(f"    columns: {sorted(keys)[:45]}")
        if not n:
            log("    ⛔ EMPTY — a fact about THIS query (year/week), not "
                "proof the endpoint has nothing")

    # ---- FIELD BY FIELD -------------------------------------------------
    log("\n" + "=" * 72)
    log("PARITY — every NFL field, and where college would get it")
    log("=" * 72)
    missing, weak = [], []
    for field, group, what in TARGET:
        words = WORDS.get(field, (field,))
        hits = []
        for src, keys in found.items():
            m = [k for k in keys
                 if any(w in k.lower() for w in words)]
            if m:
                hits.append(f"{src}:{sorted(m)[:3]}")
        if hits:
            log(f"  ok    {field:<12} [{group:<7}] {hits[0][:88]}")
        else:
            log(f"  ⛔ NO  {field:<12} [{group:<7}] {what}")
            missing.append((field, group, what))

    # ---- THE VERDICT ----------------------------------------------------
    log("\n" + "=" * 72)
    log("VERDICT")
    depth_missing = [f for f, g, _ in missing if g == "DEPTH"]
    inj_missing = [f for f, g, _ in missing if g == "INJURY"]

    if depth_missing:
        log(f"  🔴 DEPTH RANK IS AT RISK — missing {depth_missing}")
        log("     The NFL WR1/WR2/WR3 split rests on SNAP SHARE. Without a")
        log("     per-game snap number, depth rank must come from TARGETS or")
        log("     CARRIES per game, which is a WEAKER signal, and every")
        log("     surface using it must say so.")
    else:
        log("  ✅ something snap-like exists — but check whether it is")
        log("     PER-GAME or a SEASON TOTAL. A season total is lookahead.")

    if inj_missing:
        log(f"  🔴 NO INJURY DATA — missing {inj_missing}")
        log("     College football has no mandated injury report. If that is")
        log("     what this shows, the injury cascade, the trench-injury")
        log("     counts and `ahead_out` CANNOT EXIST for CFB.")
        log("     ⛔ The board must SAY it is missing them, not quietly ship")
        log("        a thinner product that looks the same as the NFL one.")

    log(f"\n  {len(TARGET) - len(missing)} of {len(TARGET)} NFL fields have "
        f"a plausible college source.")
    if missing:
        log(f"  MISSING: {[f for f, _, _ in missing]}")

    # ---- Power 4 --------------------------------------------------------
    log("\n" + "=" * 72)
    try:
        teams = get("/teams/fbs", {"year": "2025"})
        confs = {}
        for t in teams if isinstance(teams, list) else []:
            confs.setdefault(t.get("conference"), []).append(t.get("school"))
        log(f"POWER 4 — conferences in the feed: {sorted(c for c in confs if c)}")
        p4 = {c: v for c, v in confs.items() if c in POWER4}
        log(f"  matched {sorted(p4)}: {sum(len(v) for v in p4.values())} teams")
        if not p4:
            log("  ⛔ NO POWER-4 NAME MATCHED. Read the list above and fix "
                "POWER4 before filtering anything.")
    except Exception as e:
        log(f"  could not read teams: {type(e).__name__}: {e}")

    if failures:
        log(f"\n⚠️ endpoints that did not answer: {failures}")
    log("\n⛔ THIS PROBE WROTE NOTHING. No CFB collector exists yet.")
    log("=" * 72)
    return True


if __name__ == "__main__":
    sys.exit(0 if probe() else 1)
