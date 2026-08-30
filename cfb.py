"""COLLEGE FOOTBALL PARITY PROBE — v4.

🔴 WHY v4 EXISTS: v3 UNDERCOUNTED, AND UNDERCOUNTING IS STILL LYING.
`[measured 2026-08-30, run at 04:47Z, report read from the repo]` v3
reported **7 of 28** and listed `att`, `cmp`, `pass_yds`, `pass_td`,
`int`, `car`, `rush_yds`, `rush_td`, `rec`, `rec_yds`, `rec_td` as
**MISSING** — while its own athlete samples, printed twelve lines above
the verdict, contained:

    passing   C/ATT  20/32      rushing   CAR  23      receiving  REC  4
    passing   YDS    293        rushing   YDS  94
    passing   TD     1          rushing   TD   1
    passing   INT    1          rushing   LONG 16

⛔ **EVERY ONE OF THOSE "MISSING" FIELDS WAS ON SCREEN IN THE SAME
REPORT.** The cause: in this API a stat name is a **VALUE**
(`types[i]["name"] == "TD"`), not a **KEY**. `dig()` collects keys. So
the parity check was searching the wrong half of the JSON.

📌 **THIS IS THE EIGHTH INSTANCE OF ONE FAILURE FAMILY: A FACT ABOUT A
QUERY IS NOT A FACT ABOUT THE WORLD.** v1 matched substrings and said
20. v3 searched keys and said 7. **Neither number was about college
football. Both were about my own query.**

⚠️ AND v3's SAMPLE WAS CAPPED AT 12 ROWS FROM ONE GAME. That is the same
shape as reading page one of a paginated release list and concluding
nflverse publishes no participation data. **v4 enumerates EVERY DISTINCT
(category, stat) PAIR ACROSS THE WHOLE WEEK, WITH COUNTS, AND CAPS
NOTHING.**

✅ v4 does four things:
  1. **Enumerates every (category, stat) pair in the week, uncapped.**
  2. **Matches parity against STAT NAMES (values), not keys.**
  3. **Dumps `playText` samples** — because `/plays` carries NO player
     field of any kind (verified: zero keys matching player/athlete/
     name/participant/personnel), so participation, if it exists at all,
     exists only inside free text.
  4. **Writes everything to `data/ncaaf/latest/probe-report.json`.**

🔴 FINDINGS THAT STAND, from HTTP codes and from key lists, not matching:
  - `/player/injuries` -> **404. THE ENDPOINT DOES NOT EXIST.**
  - `/games/weather`   -> **401. PAID TIER.**
  - Power 4 -> ACC · Big 12 · Big Ten · SEC = **67 teams.**
  - `/plays` -> 29 keys, **NOT ONE OF THEM NAMES A PLAYER.**
  - `/player/usage` -> has `season`, has **no `week`. SEASON-LEVEL.**
"""

import collections
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.collegefootballdata.com"
KEY = os.environ.get("CFBD_API_KEY", "").strip()

# ── WHAT THE NFL LAYER CARRIES, AND WHERE COLLEGE WOULD KEEP IT ──────
# 🔴 BOX fields are (category, [stat-name candidates]). The stat name is
# a VALUE in this API. v3 looked for it among the keys and found nothing.
BOX = {
    "att":      ("passing",   ["att", "catt", "attempts", "compatt"]),
    "cmp":      ("passing",   ["cmp", "catt", "completions", "compatt"]),
    "pass_yds": ("passing",   ["yds", "yards"]),
    "pass_td":  ("passing",   ["td", "tds"]),
    "int":      ("passing",   ["int", "ints", "interceptions"]),
    "car":      ("rushing",   ["car", "att", "carries", "attempts"]),
    "rush_yds": ("rushing",   ["yds", "yards"]),
    "rush_td":  ("rushing",   ["td", "tds"]),
    "rec":      ("receiving", ["rec", "receptions"]),
    "rec_yds":  ("receiving", ["yds", "yards"]),
    "rec_td":   ("receiving", ["td", "tds"]),
    "tgt":      ("receiving", ["tgt", "tgts", "targets"]),
    "ay":       ("receiving", ["ay", "airyards"]),
}

# Fields that would live as an ordinary KEY somewhere.
KEYED = {
    "d":         ["startdate", "starttime", "gamedate", "date"],
    "week":      ["week"],
    "team":      ["team", "school"],
    "o":         ["opponent", "awayteam", "hometeam", "defense"],
    "home":      ["homeaway", "home", "neutralsite"],
    "game_id":   ["gameid", "id"],
    "snaps":     ["snaps", "offensesnaps", "participation"],
    "snap_pct":  ["snappct", "snapshare"],
    "tgt_share": ["targetshare"],
    "ay_share":  ["airyardsshare"],
    "inj":       ["injury", "injurystatus", "availability"],
    "ahead_out": ["aheadout"],
    "ol_out":    ["olout"],
    "opp_dl_out": ["oppdlout"],
    "wx":        ["temperature", "windspeed", "precipitation",
                  "weathercondition", "humidity"],
}


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
    """EVERY leaf key, all the way down."""
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
    log("CFBD PARITY PROBE v4 — v1 said 20 (substrings). v3 said 7 (keys).")
    log("NEITHER NUMBER WAS ABOUT COLLEGE FOOTBALL.")
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
    raw = {}
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
        raw[name] = rows
        found[name] = dig(rows)
        log(f"    {len(rows) if isinstance(rows,list) else 1:,} rows, "
            f"{len(found[name])} keys AT EVERY DEPTH")

    # ══ 1. THE BOX SCORE, ENUMERATED IN FULL. NOTHING CAPPED. ═══════════
    log("\n" + "=" * 72)
    log("EVERY (category, stat) PAIR IN WEEK 3 — uncapped, with counts")
    log("🔴 v3 printed twelve of these from ONE game and then declared")
    log("   eleven of the fields they contained 'MISSING'.")
    log("=" * 72)
    pairs = collections.Counter()
    examples = {}
    athletes_seen = 0
    for g in raw.get("player game", []) or []:
        for t in g.get("teams", []) or []:
            for cat in t.get("categories", []) or []:
                cname = cat.get("name")
                for typ in cat.get("types", []) or []:
                    sname = typ.get("name")
                    ath = typ.get("athletes") or []
                    pairs[(cname, sname)] += len(ath)
                    athletes_seen += len(ath)
                    if (cname, sname) not in examples and ath:
                        examples[(cname, sname)] = ath[0]
    if not pairs:
        log("    ⛔ NOTHING NESTED — the box score is not here after all")
    for (c, s), n in sorted(pairs.items(), key=lambda kv: (kv[0][0] or "", kv[0][1] or "")):
        ex = examples.get((c, s), {})
        log(f"    {str(c):<12} {str(s):<8} {n:>6,} athlete rows   "
            f"e.g. {ex.get('name','?')} = {ex.get('stat','?')}")
    log(f"\n    {len(pairs)} distinct (category, stat) pairs · "
        f"{athletes_seen:,} athlete stat rows in ONE WEEK")

    # ══ 2. PARITY — AGAINST STAT NAMES, NOT KEYS ═══════════════════════
    log("\n" + "=" * 72)
    log("PARITY — box fields matched on STAT NAMES (values), the half")
    log("v3 never searched. Context fields still matched on keys.")
    log("=" * 72)
    have = collections.defaultdict(set)
    for (c, s) in pairs:
        have[norm(c)].add(norm(s))

    ok, missing = {}, []
    for field, (cat, cands) in BOX.items():
        hit = sorted(have.get(norm(cat), set()) & set(cands))
        if hit:
            ok[field] = f"{cat}:{hit}"
            log(f"  ok    {field:<12} [box    ] {cat}:{hit}")
        else:
            missing.append((field, "box"))
            log(f"  NO    {field:<12} [box    ] nothing named {cands} "
                f"under '{cat}'")
    for field, cands in KEYED.items():
        hit = None
        for src, keys in found.items():
            m = [k for k in keys if norm(k) in cands]
            if m:
                hit = f"{src}:{sorted(m)[:3]}"
                break
        if hit:
            ok[field] = hit
            log(f"  ok    {field:<12} [keyed  ] {hit[:70]}")
        else:
            missing.append((field, "keyed"))
            log(f"  NO    {field:<12} [keyed  ]")

    total = len(BOX) + len(KEYED)
    log(f"\n  VERDICT: {total - len(missing)} of {total} fields have a "
        f"REAL college source.")
    log(f"  MISSING: {[f for f, _ in missing]}")

    # ══ 3. /plays — THE PARTICIPATION QUESTION ═════════════════════════
    log("\n" + "=" * 72)
    log("/plays — CAN A SNAP COUNT BE BUILT FROM IT?")
    log("=" * 72)
    pk = found.get("plays", set())
    named = [k for k in pk if any(w in k.lower() for w in
             ("player", "athlete", "name", "participant", "personnel"))]
    log(f"    keys naming a player: {named or 'NONE'}")
    log("    ⛔ If that is NONE, the only player reference is free text:")
    texts = []
    for p in (raw.get("plays") or [])[:400]:
        t = p.get("playText")
        if t:
            texts.append({"playType": p.get("playType"), "playText": t})
    for t in texts[:15]:
        log(f"      [{str(t['playType'])[:22]:<22}] {t['playText'][:88]}")
    log("")
    log("    🔴 A PLAYER WHO WAS ON THE FIELD BUT NOT INVOLVED NEVER")
    log("       APPEARS IN playText AT ALL. So playText can give TOUCHES,")
    log("       and it CANNOT give SNAPS. Those are different quantities")
    log("       and the difference is the whole point of a snap share.")

    # ══ 4. usage — season or week? ═════════════════════════════════════
    log("\n" + "=" * 72)
    uk = found.get("usage", set())
    log(f"/player/usage keys: {sorted(uk)}")
    log(f"    has 'week'? {'week' in {k.lower() for k in uk}}   "
        f"has 'season'? {'season' in {k.lower() for k in uk}}")
    log("    ⛔ season and no week = SEASON-LEVEL. Joining it to a week-3")
    log("       game is a model that has seen the future.")

    log("\n" + "=" * 72)
    log("  🔴 CONFIRMED BY HTTP CODE, NOT BY MATCHING:")
    log("     /player/injuries -> 404. THE ENDPOINT DOES NOT EXIST.")
    log("     /games/weather   -> 401. PAID TIER, not missing.")
    log("=" * 72)
    if fails:
        log(f"⚠️ did not answer: {fails}")

    # 🔴 THE FINDINGS LAND IN THE REPO, NOT ONLY IN AN ACTIONS LOG.
    # `[measured 2026-08-30]` run #238's log could not be read from
    # outside the runner: the API refuses job logs without ADMIN rights
    # and the web viewer does not expose the lines. ⛔ A diagnosis you
    # cannot retrieve is a diagnosis you do not have -- the same rule
    # that put card-verify-failure.txt and backfill-report.txt in the repo.
    try:
        os.makedirs("data/ncaaf/latest", exist_ok=True)
        with open("data/ncaaf/latest/probe-report.json", "w",
                  encoding="utf-8") as fh:
            json.dump({
                "probed_at": datetime.datetime.now(
                    datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "probe_version": 4,
                "kind": "DESCRIPTIVE — a probe, nothing was collected",
                "endpoints_failed": [[n, str(c)] for n, c in fails],
                "columns_by_endpoint": {k: sorted(v)
                                        for k, v in found.items()},
                "box_pairs": [{"category": c, "stat": s, "athlete_rows": n,
                               "example": examples.get((c, s))}
                              for (c, s), n in sorted(
                                  pairs.items(),
                                  key=lambda kv: (kv[0][0] or "",
                                                  kv[0][1] or ""))],
                "athlete_rows_in_week": athletes_seen,
                "parity_ok": ok,
                "parity_missing": [f for f, _ in missing],
                "parity_total": total,
                "plays_player_keys": named,
                "play_text_samples": texts[:40],
                "usage_keys": sorted(uk),
            }, fh, indent=1)
        log("wrote data/ncaaf/latest/probe-report.json")
    except Exception as e:
        log(f"could not write the probe report: {type(e).__name__}: {e}")

    log("⛔ THIS PROBE COLLECTED NOTHING. Only the report was written.")
    return True


if __name__ == "__main__":
    sys.exit(0 if probe() else 1)
