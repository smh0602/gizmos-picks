"""COLLEGE FOOTBALL PARITY PROBE — v2, STRICT.

🔴 WHY v2 EXISTS: v1 LIED, AND IT LIED IN THE COMFORTABLE DIRECTION.
`[measured 2026-08-30, run #234]` v1 reported **"20 of 28 NFL fields have
a plausible college source."** ⛔ **TEN OF THOSE TWENTY WERE FALSE.**
Its matcher was a loose substring test, so:

    snaps    <- games:['playoff']       "play" inside "playOFF"
    att      <- games:['attendance']    "att" inside "ATTendance"
    int      <- games:['awayPoints']    "int" inside "poINTs"
    rec      <- roster:['recruitIds']   "rec" inside "RECruitIds"
    pass_td  <- games:['startDate']     "td"  inside "starTDate"
    wx       <- teams:['location.dome'] a stadium attribute, not weather

⛔ **A CHECK THAT GIVES FALSE COMFORT IS WORSE THAN NO CHECK.** The whole
project rule is that a green run is not a verified run; v1 was a green
run. **The real parity number was nearer 10 of 28.**

✅ v2 fixes two things:
  1. **STRICT MATCHING.** A field is satisfied by a column whose name
     matches a NAMED CANDIDATE, not by a substring collision.
  2. **IT DESCENDS.** `/games/players` nests the real box score under
     `teams.categories.types.athletes` and v1 never opened it — so it
     judged college on the wrapper instead of the data.

⚠️ THREE FINDINGS FROM v1 THAT STAND, because they came from HTTP codes
and not from string matching:
  - `/player/injuries` -> **HTTP 404. THE ENDPOINT DOES NOT EXIST.**
  - `/games/weather`   -> **HTTP 401. PAID TIER.**
  - Power 4 -> ACC · Big 12 · Big Ten · SEC = **67 teams.** ✅
"""

import datetime
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.collegefootballdata.com"
KEY = os.environ.get("CFBD_API_KEY", "").strip()
POWER4 = {"SEC", "Big Ten", "ACC", "Big 12"}

# 🔴 NAMED CANDIDATES, NOT SUBSTRINGS. A column satisfies a field only by
# matching one of these exactly (case-insensitive, punctuation stripped).
# ⛔ Adding a loose entry here re-creates the v1 bug.
WANT = {
    "d":         ["startdate", "starttime", "gamedate", "date"],
    "week":      ["week"],
    "team":      ["team", "school"],
    "o":         ["opponent", "awayteam", "hometeam", "defense"],
    "home":      ["homeaway", "home", "neutralsite"],
    "game_id":   ["gameid", "id"],
    "snaps":     ["snaps", "offensesnaps", "plays", "participation"],
    "snap_pct":  ["snappct", "snapshare", "usageoverall", "usage"],
    "tgt_share": ["targetshare", "usagepass", "targets"],
    "ay_share":  ["airyardsshare", "airyards"],
    "att":       ["att", "attempts", "passattempts", "completionsattempts"],
    "cmp":       ["cmp", "completions", "completionsattempts"],
    "pass_yds":  ["yds", "passingyards", "yards"],
    "pass_td":   ["td", "tds", "passingtouchdowns", "touchdowns"],
    "int":       ["int", "ints", "interceptions"],
    "car":       ["car", "carries", "rushingattempts"],
    "rush_yds":  ["yds", "rushingyards", "yards"],
    "rush_td":   ["td", "tds", "rushingtouchdowns", "touchdowns"],
    "tgt":       ["targets", "tar"],
    "rec":       ["rec", "receptions"],
    "rec_yds":   ["yds", "receivingyards", "yards"],
    "rec_td":    ["td", "tds", "receivingtouchdowns", "touchdowns"],
    "ay":        ["airyards"],
    "inj":       ["injury", "injurystatus", "status", "availability"],
    "ahead_out": ["injury", "status"],
    "ol_out":    ["injury", "status"],
    "opp_dl_out": ["injury", "status"],
    "wx":        ["temperature", "temp", "windspeed", "precipitation",
                  "weathercondition", "humidity"],
}
GROUP = {**{k: "context" for k in ("d", "week", "team", "o", "home", "game_id")},
         **{k: "DEPTH" for k in ("snaps", "snap_pct", "tgt_share", "ay_share")},
         **{k: "INJURY" for k in ("inj", "ahead_out", "ol_out", "opp_dl_out")},
         "wx": "weather"}


def norm(s):
    return "".join(c for c in str(s).lower() if c.isalnum())


def log(m):
    print(m, flush=True)


def get(path, params, timeout=60):
    q = "&".join(f"{k}={v}" for k, v in (params or {}).items())
    req = urllib.request.Request(
        f"{API}{path}" + (f"?{q}" if q else ""),
        headers={"Authorization": f"Bearer {KEY}",
                 "Accept": "application/json",
                 "User-Agent": "gizmos-picks/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def dig(o, depth=0, cap=8):
    """EVERY leaf key, all the way down. v1 stopped at 3 and missed the
    box score entirely."""
    keys = set()
    if depth > cap:
        return keys
    if isinstance(o, dict):
        for k, v in o.items():
            keys.add(str(k))
            keys |= dig(v, depth + 1, cap)
    elif isinstance(o, list):
        for x in o[:25]:
            keys |= dig(x, depth + 1, cap)
    return keys


def probe(log=log):
    if not KEY:
        log("FATAL: CFBD_API_KEY is not set.")
        return False

    log("=" * 72)
    log("CFBD PARITY PROBE v2 — STRICT. v1 reported 20/28 and 10 were FALSE.")
    log("=" * 72)

    found, fails = {}, []
    PROBES = [
        ("games",       "/games",         {"year": "2025", "week": "3",
                                           "seasonType": "regular"}),
        ("player game", "/games/players", {"year": "2025", "week": "3",
                                           "seasonType": "regular"}),
        ("usage",       "/player/usage",  {"year": "2025"}),
        ("plays",       "/plays",         {"year": "2025", "week": "3",
                                           "seasonType": "regular"}),
    ]
    for name, path, params in PROBES:
        log(f"\n=== {name} {path} ===")
        try:
            rows = get(path, params)
        except urllib.error.HTTPError as e:
            log(f"    HTTP {e.code} {e.reason}")
            fails.append((name, e.code))
            continue
        except Exception as e:
            log(f"    {type(e).__name__}: {e}")
            fails.append((name, type(e).__name__))
            continue
        found[name] = dig(rows)
        log(f"    {len(rows) if isinstance(rows,list) else 1:,} rows, "
            f"{len(found[name])} keys AT EVERY DEPTH")
        log(f"    keys: {sorted(found[name])[:60]}")

    # 🔴 THE THING v1 NEVER OPENED. Print one real athlete stat line.
    log("\n" + "=" * 72)
    log("INSIDE /games/players — where the box score actually lives")
    SAMPLES = []
    try:
        rows = get("/games/players", {"year": "2025", "week": "3",
                                      "seasonType": "regular"})
        shown = 0
        for g in rows if isinstance(rows, list) else []:
            for t in g.get("teams", []):
                for cat in t.get("categories", []):
                    for typ in cat.get("types", []):
                        for a in (typ.get("athletes") or [])[:1]:
                            if shown >= 12:
                                break
                            SAMPLES.append({
                                "category": cat.get("name"),
                                "stat": typ.get("name"),
                                "athlete_keys": sorted(a) if isinstance(a, dict) else None,
                                "athlete": a})
                            log(f"    category={cat.get('name'):<12} "
                                f"stat={typ.get('name'):<8} "
                                f"athlete={json.dumps(a)[:110]}")
                            shown += 1
        if not shown:
            log("    ⛔ NOTHING NESTED — the box score is not here after all")
    except Exception as e:
        log(f"    {type(e).__name__}: {e}")
    # ---- strict parity --------------------------------------------------
    log("\n" + "=" * 72)
    log("PARITY — STRICT. A field is 'ok' only on a NAMED column match.")
    log("=" * 72)
    missing = []
    for field, cands in WANT.items():
        grp = GROUP.get(field, "box")
        hit = None
        for src, keys in found.items():
            m = [k for k in keys if norm(k) in cands]
            if m:
                hit = f"{src}:{sorted(m)[:3]}"
                break
        if hit:
            log(f"  ok    {field:<12} [{grp:<7}] {hit[:80]}")
        else:
            log(f"  NO    {field:<12} [{grp:<7}]")
            missing.append((field, grp))

    log("\n" + "=" * 72)
    log("VERDICT")
    log(f"  {len(WANT) - len(missing)} of {len(WANT)} fields have a NAMED "
        f"college column.")
    if missing:
        log(f"  MISSING: {[f for f, _ in missing]}")
    log("")
    log("  🔴 CONFIRMED BY HTTP CODE, NOT BY STRING MATCHING:")
    log("     /player/injuries -> 404. THE ENDPOINT DOES NOT EXIST.")
    log("        inj · ahead_out · ol_out · opp_dl_out CANNOT EXIST for CFB.")
    log("        College has no mandated injury report. That is a difference")
    log("        between the SPORTS. No API hunting fixes it.")
    log("     /games/weather -> 401. PAID TIER, not missing.")
    log("")
    log("  ⚠️ AND THE QUESTION THIS PROBE STILL DOES NOT ANSWER:")
    log("     /player/usage has no `week` — it looks SEASON-LEVEL. A season")
    log("     usage number joined onto a week-3 game is a model that has")
    log("     SEEN THE FUTURE. Depth rank needs a PER-GAME number, and if")
    log("     usage cannot give one it must be counted from /plays instead.")
    log("=" * 72)
    if fails:
        log(f"⚠️ did not answer: {fails}")

    # 🔴 THE FINDINGS LAND IN THE REPO, NOT ONLY IN AN ACTIONS LOG.
    # `[measured 2026-08-30]` the log for run #238 could not be read from
    # outside the runner at all: the API refuses job logs without ADMIN
    # rights, and the web viewer does not expose the lines to extraction.
    # ⛔ A DIAGNOSIS YOU CANNOT RETRIEVE IS A DIAGNOSIS YOU DO NOT HAVE --
    # the same rule that put card-verify-failure.txt and
    # backfill-report.txt in the repo. Asking Sam to screenshot a log is
    # not a process, it is a bottleneck.
    try:
        os.makedirs("data/ncaaf/latest", exist_ok=True)
        with open("data/ncaaf/latest/probe-report.json", "w",
                  encoding="utf-8") as fh:
            json.dump({
                "probed_at": datetime.datetime.now(
                    datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "kind": "DESCRIPTIVE — a probe, nothing was collected",
                "endpoints_failed": [[n, str(c)] for n, c in fails],
                "columns_by_endpoint": {k: sorted(v)
                                        for k, v in found.items()},
                "parity_missing": [f for f, _ in missing],
                "parity_ok": [f for f in WANT
                              if f not in [m for m, _ in missing]],
                "athlete_samples": SAMPLES,
            }, fh, indent=1)
        log("wrote data/ncaaf/latest/probe-report.json")
    except Exception as e:
        log(f"could not write the probe report: {type(e).__name__}: {e}")

    log("⛔ THIS PROBE COLLECTED NOTHING. Only the report was written.")
    return True


if __name__ == "__main__":
    sys.exit(0 if probe() else 1)
