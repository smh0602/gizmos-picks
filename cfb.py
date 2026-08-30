"""COLLEGE FOOTBALL — PROBE, BACK-FILL AND VERIFY, IN ONE DISPATCH.

Sam, 2026-08-30: *"is it possible for us to kill all birds with one
stone"*. ✅ Yes. This file now does the schema probe, the five-season
back-fill and the verification in a single `cfb-probe` run, because the
upload-dispatch-read loop was costing a round trip per question.

⚠️ NO `collect.py` CHANGE IS NEEDED and that is deliberate — `collect.py`
sits in the workflow's `push:` filter, so editing it starts an MLB
converge and puts the baseball site at risk for a football change.

════════════════════════════════════════════════════════════════════════
🔴 THE PARITY NUMBER HAS NOW BEEN WRONG TWICE, IN BOTH DIRECTIONS.
  v1 said **20 of 28** — a loose substring test: `td` inside `starTDate`,
     `int` inside `poINTs`, `snaps` inside `playOFF`.
  v3 said **7 of 28** — it searched **KEYS**, but in this API a stat name
     is a **VALUE** (`types[i]["name"] == "TD"`). Its own athlete samples,
     printed twelve lines above its verdict, contained
     `passing C/ATT 20/32`, `passing YDS 293`, `passing TD 1`,
     `rushing CAR 23`, `receiving REC 4` — every one of them a field it
     had just declared MISSING.
📌 **EIGHTH INSTANCE OF ONE FAILURE FAMILY: A FACT ABOUT A QUERY IS NOT A
FACT ABOUT THE WORLD.** ⛔ Neither number was about college football.
Both were about my own matcher.
════════════════════════════════════════════════════════════════════════

🔴 WHAT COLLEGE CANNOT GIVE, VERIFIED, NOT ASSUMED:
  - **THERE IS NO SNAP COUNT. AT ALL.** `[verified 2026-08-30 04:47Z]`
    `/plays` returns 29 keys and **not one names a player** — no
    `player`, `athlete`, `participant` or `personnel` field. The only
    player reference is inside `playText`, free prose, which names only
    who was INVOLVED in the play. ⛔ **A receiver who ran a route and was
    not targeted is invisible.** So the data yields **TOUCHES, NEVER
    SNAPS** — and that difference is the whole point of a snap share.
    ➡️ `snaps`, `snap_pct`, `tgt_share`, `ay_share` **cannot be built.**
    ➡️ Depth rank comes from **trailing TOUCHES** and is **named for what
    it is**. It is not a snap share and must never be labelled one.
  - `/player/injuries` → **404, the endpoint does not exist.**
  - `/games/weather` → **401, paid tier.**
  - `/player/usage` has `season` and **no `week`** — SEASON-LEVEL. ⛔ Not
    used anywhere in this file. Joined to a week-3 game it is a model
    that has seen the future.

🟢 WHAT COLLEGE GIVES THAT THE NFL LAYER DOES NOT:
  `homePregameElo` / `awayPregameElo` — explicitly **PREGAME**, so
  point-in-time legal, free, and a ready-made opponent-strength control.
  ⚠️ It matters MORE here than it would in the NFL: the talent gap
  between Power 4 teams is enormous, so a defence's raw numbers are
  partly a fact about who it scheduled.
  ⛔ `excitementIndex` and every `postgame*` field are POSTGAME. BANNED.

⛔ NO SNAP FLOOR AND NO TOUCH FLOOR IS APPLIED HERE, ON PURPOSE.
**T37-CFB** pre-registers that the floor is set ONCE from the college
distribution, never tuned against model performance. So this file emits
the **usage distribution** for the floor to be set from, and emits every
row unfiltered. ⛔ Picking a floor here would be answering a
pre-registered question with the data in front of me.
"""

import collections
import datetime
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.collegefootballdata.com"
KEY = os.environ.get("CFBD_API_KEY", "").strip()
OUT = "data/ncaaf/latest"

POWER4 = {"ACC", "Big 12", "Big Ten", "SEC"}
REG_WEEKS = range(1, 16)
PROP_POS = {"QB", "RB", "WR", "TE", "FB"}
VS_DEPTH = {"QB": 1, "RB": 2, "WR": 3, "TE": 2}
VS_STATS = ("pass_yds", "rush_yds", "rec_yds", "rec", "tgt",
            "pass_td", "rush_td", "rec_td", "car", "att", "cmp", "int",
            "usage")

# (category, stat) -> our field. Anything NOT in here is reported as
# UNMAPPED with a count, never silently dropped.
MAP = {
    ("passing", "yds"): "pass_yds",
    ("passing", "td"): "pass_td",
    ("passing", "int"): "int",
    ("rushing", "car"): "car",
    ("rushing", "yds"): "rush_yds",
    ("rushing", "td"): "rush_td",
    ("receiving", "rec"): "rec",
    ("receiving", "yds"): "rec_yds",
    ("receiving", "td"): "rec_td",
    ("receiving", "tgt"): "tgt",
    ("receiving", "tar"): "tgt",
}
# 🔴 `C/ATT` ARRIVES AS ONE STRING, "20/32". Two fields in one cell.
SPLIT = {("passing", "c/att"): ("cmp", "att"),
         ("passing", "comp/att"): ("cmp", "att")}
IGNORE = {("passing", "avg"), ("passing", "qbr"), ("rushing", "avg"),
          ("rushing", "long"), ("receiving", "avg"), ("receiving", "long")}


def log(m):
    print(m, flush=True)


def norm(s):
    return str(s).strip().lower()


def get(path, params, timeout=90, tries=4):
    q = "&".join(f"{k}={v}" for k, v in (params or {}).items())
    url = f"{API}{path}" + (f"?{q}" if q else "")
    last = None
    for i in range(tries):
        req = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {KEY}",
                          "Accept": "application/json",
                          "User-Agent": "gizmos-picks/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last = e
            # ⚠️ 429 and 5xx are worth another go. 4xx is not -- retrying a
            # 404 just wastes the runner's time and hides the real answer.
            if e.code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(2 * (i + 1))
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last


def dig(o, depth=0, cap=8):
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


def num(s):
    try:
        return float(s) if "." in str(s) else int(s)
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════
# 1. PROBE
# ══════════════════════════════════════════════════════════════════════
def run_probe(log=log):
    """Enumerate the schema. ⛔ UNCAPPED -- v3 printed twelve rows from
    ONE game and drew a conclusion about the sport from them, which is
    the same shape as reading page one of a paginated release list."""
    report = {"probe_version": 5}
    found, fails, raw = {}, [], {}
    PROBES = [
        ("games",       "/games",         {"year": "2025", "week": "3",
                                           "seasonType": "regular"}),
        ("player game", "/games/players", {"year": "2025", "week": "3",
                                           "seasonType": "regular"}),
        ("plays",       "/plays",         {"year": "2025", "week": "3",
                                           "seasonType": "regular"}),
        ("roster",      "/roster",        {"year": "2025"}),
    ]
    for name, path, params in PROBES:
        try:
            rows = get(path, params)
        except Exception as e:
            code = getattr(e, "code", type(e).__name__)
            log(f"  {name}: FAILED {code}")
            fails.append((name, code))
            continue
        raw[name] = rows
        found[name] = dig(rows)
        log(f"  {name}: {len(rows) if isinstance(rows, list) else 1:,} rows, "
            f"{len(found[name])} keys at every depth")

    pairs = collections.Counter()
    examples = {}
    for g in raw.get("player game", []) or []:
        for t in g.get("teams", []) or []:
            for cat in t.get("categories", []) or []:
                for typ in cat.get("types", []) or []:
                    k = (cat.get("name"), typ.get("name"))
                    ath = typ.get("athletes") or []
                    pairs[k] += len(ath)
                    if k not in examples and ath:
                        examples[k] = ath[0]

    log("\n  EVERY (category, stat) PAIR IN WEEK 3 — uncapped:")
    for (c, s), n in sorted(pairs.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        known = ((norm(c), norm(s)) in MAP or (norm(c), norm(s)) in SPLIT
                 or (norm(c), norm(s)) in IGNORE)
        ex = examples.get((c, s), {})
        log(f"    {'✓' if known else '🔴 UNMAPPED'}  {str(c):<12} {str(s):<9} "
            f"{n:>6,} rows   e.g. {ex.get('name','?')} = {ex.get('stat','?')}")

    unmapped = [[c, s, n] for (c, s), n in pairs.items()
                if (norm(c), norm(s)) not in MAP
                and (norm(c), norm(s)) not in SPLIT
                and (norm(c), norm(s)) not in IGNORE]
    tgt = [1 for (c, s) in pairs if norm(c) == "receiving"
           and norm(s) in ("tgt", "tar", "targets")]
    log(f"\n  🔴 TARGETS PRESENT IN THE COLLEGE BOX SCORE? "
        f"{'YES' if tgt else 'NO'}")
    if not tgt:
        log("     ⛔ Then `tgt`, `tgt_share` and every air-yards field die")
        log("        alongside `snaps`. Say so; do not substitute receptions")
        log("        for targets and call it usage.")

    pk = found.get("plays", set())
    named = [k for k in pk if any(w in k.lower() for w in
             ("player", "athlete", "name", "participant", "personnel"))]
    log(f"  /plays keys naming a player: {named or 'NONE — snaps impossible'}")

    report.update({
        "endpoints_failed": [[n, str(c)] for n, c in fails],
        "columns_by_endpoint": {k: sorted(v) for k, v in found.items()},
        "box_pairs": [{"category": c, "stat": s, "athlete_rows": n,
                       "example": examples.get((c, s))}
                      for (c, s), n in sorted(pairs.items(),
                                              key=lambda kv: str(kv[0]))],
        "unmapped_stats": unmapped,
        "targets_present": bool(tgt),
        "plays_player_keys": named,
    })
    return report


# ══════════════════════════════════════════════════════════════════════
# 2. BUILD
# ══════════════════════════════════════════════════════════════════════
def positions(season, log=log):
    """Listed position per player id.
    ⚠️ A position is a static ATTRIBUTE, not a performance outcome, so
    taking it season-wide is not lookahead. ⛔ A season STAT would be."""
    pos = {}
    try:
        for r in get("/roster", {"year": str(season)}) or []:
            p = (r.get("position") or "").upper()
            if r.get("id") is not None and p:
                pos[str(r["id"])] = p
    except Exception as e:
        log(f"    roster {season}: {type(e).__name__} — positions unavailable")
    return pos


def usage_of(row, pos):
    """TOUCHES, and the name is the honest one. ⛔ NOT a snap share."""
    if pos == "QB":
        return (row.get("att") or 0) + (row.get("car") or 0)
    return ((row.get("car") or 0)
            + (row.get("tgt") if row.get("tgt") is not None
               else (row.get("rec") or 0)))


def build_season(season, log=log):
    meta, weeks_seen = {}, set()
    for st in ("regular", "postseason"):
        try:
            games = get("/games", {"year": str(season), "seasonType": st})
        except Exception as e:
            log(f"    /games {season} {st}: {type(e).__name__}")
            continue
        for g in games or []:
            meta[str(g.get("id"))] = {
                "week": g.get("week"),
                "seasonType": st,
                "d": (g.get("startDate") or "")[:10],
                "home": g.get("homeTeam"), "away": g.get("awayTeam"),
                "homeConf": g.get("homeConference"),
                "awayConf": g.get("awayConference"),
                "neutral": bool(g.get("neutralSite")),
                # 🟢 PREGAME. Point-in-time legal. ⛔ postgame* is banned.
                "homeElo": g.get("homePregameElo"),
                "awayElo": g.get("awayPregameElo"),
            }
            if st == "regular" and g.get("week"):
                weeks_seen.add(g["week"])
    if not meta:
        raise RuntimeError(f"no games returned for {season}")
    log(f"    {len(meta):,} games, regular weeks {min(weeks_seen)}–{max(weeks_seen)}")

    pos_of = positions(season, log)
    rows = collections.defaultdict(dict)   # (pid, gameid) -> row
    names, unmapped = {}, collections.Counter()

    plan = [("regular", w) for w in sorted(weeks_seen)] + [("postseason", 1)]
    for st, wk in plan:
        try:
            box = get("/games/players", {"year": str(season), "week": str(wk),
                                         "seasonType": st})
        except Exception as e:
            log(f"    box {season} {st} wk{wk}: {type(e).__name__} — skipped")
            continue
        for g in box or []:
            gid = str(g.get("id"))
            m = meta.get(gid)
            if not m:
                continue
            for t in g.get("teams", []) or []:
                team = t.get("team")
                opp = m["away"] if team == m["home"] else m["home"]
                is_home = team == m["home"]
                for cat in t.get("categories", []) or []:
                    c = norm(cat.get("name"))
                    for typ in cat.get("types", []) or []:
                        s = norm(typ.get("name"))
                        if (c, s) in IGNORE:
                            continue
                        dest = MAP.get((c, s))
                        pair = SPLIT.get((c, s))
                        if not dest and not pair:
                            unmapped[(c, s)] += len(typ.get("athletes") or [])
                            continue
                        for a in typ.get("athletes") or []:
                            pid = str(a.get("id"))
                            names[pid] = a.get("name")
                            r = rows[(pid, gid)]
                            r.setdefault("pid", pid)
                            r.setdefault("team", team)
                            r.setdefault("o", opp)
                            r.setdefault("home", is_home)
                            r.setdefault("week", m["week"])
                            # 🔴 A MONOTONIC WEEK INDEX. Postseason week 1
                            # and regular week 1 are DIFFERENT POINTS IN
                            # TIME; keying trailing form on the raw week
                            # would let a bowl game inform week 1.
                            r.setdefault("wk_i", (m["week"] or 0)
                                         + (100 if st == "postseason" else 0))
                            r.setdefault("d", m["d"])
                            r.setdefault("game_id", gid)
                            r.setdefault("seasonType", st)
                            r.setdefault("neutral", m["neutral"])
                            r.setdefault(
                                "elo", m["homeElo"] if is_home else m["awayElo"])
                            r.setdefault(
                                "opp_elo", m["awayElo"] if is_home else m["homeElo"])
                            r.setdefault(
                                "conf", m["homeConf"] if is_home else m["awayConf"])
                            r.setdefault(
                                "opp_conf", m["awayConf"] if is_home else m["homeConf"])
                            v = a.get("stat")
                            if pair:
                                bits = str(v).split("/")
                                if len(bits) == 2:
                                    r[pair[0]] = num(bits[0])
                                    r[pair[1]] = num(bits[1])
                            else:
                                n = num(v)
                                if n is not None:
                                    r[dest] = n
        time.sleep(0.35)

    # ── Power 4 only, and the position must be known ──────────────────
    players = collections.defaultdict(lambda: {"g": []})
    dropped = collections.Counter()
    for (pid, gid), r in rows.items():
        if r.get("conf") not in POWER4:
            dropped["not Power 4"] += 1
            continue
        p = pos_of.get(pid)
        if p not in PROP_POS:
            dropped["position unknown or not a prop position"] += 1
            continue
        r["pos"] = p
        r["usage"] = usage_of(r, p)
        players[pid]["pos"] = p
        players[pid]["name"] = names.get(pid)
        players[pid]["g"].append(r)
    for p in players.values():
        p["g"].sort(key=lambda x: (x["seasonType"] != "regular", x["week"] or 0))

    rank_and_cascade(players)

    doc = {
        "season": season, "kind": "DESCRIPTIVE",
        "built_at": datetime.datetime.now(datetime.timezone.utc)
                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope": "Power 4 only (ACC, Big 12, Big Ten, SEC)",
        "consumer_contract": [
            "NO SNAP DATA EXISTS FOR COLLEGE FOOTBALL. depth_rank and "
            "trailing_usage are built from TOUCHES, not snaps, and are not "
            "comparable to the NFL layer's snap-share depth rank.",
            "ahead_out_lastwk is LAGGED and cannot distinguish a player who "
            "was absent from one who played and did not touch the ball.",
            "elo/opp_elo are PREGAME and point-in-time legal. No postgame "
            "field from /games is carried here.",
            "NO usage floor has been applied. T37-CFB sets it once, from "
            "the distribution emitted in the probe report.",
            "tgt_share, ay_share, snaps, snap_pct, inj, ol_out and "
            "opp_dl_out DO NOT EXIST for CFB and are absent, not null.",
        ],
        "players": {pid: {"name": p["name"], "pos": p["pos"], "g": p["g"]}
                    for pid, p in players.items()},
    }
    n = sum(len(p["g"]) for p in players.values())
    log(f"    {len(players):,} players, {n:,} player-weeks kept")
    for k, v in dropped.items():
        log(f"      dropped {v:,} — {k}")
    if unmapped:
        for (c, s), v in unmapped.most_common():
            log(f"      🔴 UNMAPPED STAT {c}/{s}: {v:,} rows NOT collected")
    return doc, dict(unmapped), n


def rank_and_cascade(players):
    """Depth rank + the lagged injury cascade, BOTH POINT-IN-TIME.
    🔴 Extracted so it can be TESTED WITHOUT THE API. `verify_nfl.py`
    caught four defects; the ones it missed were in code no test could
    reach. ⛔ A function only the network can call is a function nobody
    checks."""
    # 🔴 `w < week` — STRICTLY PRIOR WEEKS, the rule nfl.py uses.
    # ⛔ A season aggregate joined to a week-3 game is a model that has
    # seen the future, and Sam's point makes that WORSE, not milder: role
    # change is an EVENT, so the error is large, structured, and
    # concentrated on exactly the injury-driven spots we want to bet.
    hist = collections.defaultdict(lambda: collections.defaultdict(list))
    played = collections.defaultdict(set)
    for pid, p in players.items():
        for g in p["g"]:
            hist[(g["team"], p["pos"])][pid].append((g["wk_i"], g["usage"]))
            played[(pid, g["wk_i"])].add(g["team"])

    def trailing(pid, team, pos, week):
        # `w < week` — STRICTLY EARLIER. This one comparison IS the
        # point-in-time guarantee; verify() asserts it on week-1 rows.
        v = [u for w, u in hist[(team, pos)].get(pid, []) if w and w < week]
        return sum(v) / len(v) if v else None

    for pid, p in players.items():
        pos = p["pos"]
        for g in p["g"]:
            wk = g["wk_i"]
            mine = trailing(pid, g["team"], pos, wk)
            ahead = []
            for q in hist[(g["team"], pos)]:
                if q == pid:
                    continue
                tq = trailing(q, g["team"], pos, wk)
                if tq is not None and (mine is None or tq > mine):
                    ahead.append(q)
            g["depth_rank"] = len(ahead) + 1 if mine is not None else None
            g["trailing_usage"] = round(mine, 3) if mine is not None else None
            # ⚠️ `ahead_out_lastwk` — T36, RE-SPECIFIED 2026-08-30: its
            # original mechanism ("zero snaps last week") DOES NOT EXIST,
            # because college publishes no snap data at all.
            # ⛔ STRICTLY WEAKER THAN THE NFL'S `ahead_out`: a healthy
            # receiver who drew no targets is INDISTINGUISHABLE from one
            # who did not dress. Clean for QB and RB, weak for WR and TE.
            # NEVER compare its result to the NFL's.
            g["ahead_out_lastwk"] = sum(
                1 for q in ahead if (q, wk - 1) not in played) if wk > 1 else 0
    return players


def build_vs_position(doc, log=log):
    out = collections.defaultdict(
        lambda: collections.defaultdict(lambda: collections.defaultdict(list)))
    kept = 0
    for pid, p in doc["players"].items():
        pos = p["pos"]
        if pos not in VS_DEPTH:
            continue
        for g in p["g"]:
            r = g.get("depth_rank")
            if r is None or r > VS_DEPTH[pos] or not g.get("o"):
                continue
            row = {"pid": pid, "name": p["name"], "team": g["team"],
                   "week": g["week"], "d": g["d"],
                   "ahead_out_lastwk": g.get("ahead_out_lastwk", 0),
                   "opp_elo": g.get("opp_elo")}
            for k in VS_STATS:
                if g.get(k) is not None:
                    row[k] = g[k]
            out[g["o"]][pos][str(r)].append(row)
            kept += 1
    log(f"    vs-position: {kept:,} performances across {len(out)} defences")
    return {"season": doc["season"], "kind": "DESCRIPTIVE",
            "built_at": doc["built_at"], "depth_kept": VS_DEPTH,
            "note": ("Every performance a defence allowed, by DEPTH SLOT. "
                     "⛔ Depth is TOUCH-based, not snap-based — college "
                     "publishes no snap data. NO usage floor applied; see "
                     "T37-CFB."),
            "defences": {k: {p: dict(v) for p, v in d.items()}
                         for k, d in out.items()}}, kept


# ══════════════════════════════════════════════════════════════════════
# 3. VERIFY — 🔴 IN THIS FILE, SO IT ACTUALLY RUNS.
# `verify_nfl.py` caught four real defects, two before Sam saw them,
# including `tgt_per_snap` = 0.0 on 94,738 rows. ⛔ A build with no
# verifier is a green run, and a green run is not a verified run.
# ══════════════════════════════════════════════════════════════════════
def verify(doc, log=log):
    bad = []
    gs = [g for p in doc["players"].values() for g in p["g"]]
    if not gs:
        return ["the season produced NO player-weeks at all"]

    # 🔴 A CONSTANT FEATURE IS A BROKEN JOIN, NOT A FINDING. `[recorded]`
    # the NFL build emitted `ahead_out` = 0 on all 19,400 rows and went
    # GREEN; fitting on that yields "the mechanism is dead" when the
    # column was never populated — the most expensive kind of wrong
    # answer, because it looks like science.
    # ⚠️ ONLY ON A REAL SEASON. On a handful of rows "constant" is not
    # evidence of anything: a five-row fixture in which nobody happened to
    # miss a game has a legitimately constant cascade. A Power 4 season is
    # tens of thousands of player-weeks, so this bar is never near the
    # real path — it exists so a degenerate slice cannot fail a good build.
    CONST_MIN = 500
    if len(gs) >= CONST_MIN:
        for f in ("depth_rank", "trailing_usage", "usage", "ahead_out_lastwk"):
            vals = {g.get(f) for g in gs}
            if len(vals) == 1:
                bad.append(f"{f} is CONSTANT {vals.pop()!r} across "
                           f"{len(gs):,} rows — a join failure, not a result")
    else:
        log(f"    ⚠️ only {len(gs):,} rows — the constant-feature check needs "
            f"{CONST_MIN}+ to mean anything and was SKIPPED, not passed")

    # ⛔ THE LOOKAHEAD ASSERTION. Every trailing number must be computable
    # from STRICTLY EARLIER weeks. A week-1 row cannot have one.
    w1 = [g for g in gs if g.get("week") == 1 and g.get("seasonType") == "regular"]
    leak = [g for g in w1 if g.get("trailing_usage") is not None]
    if leak:
        bad.append(f"{len(leak):,} WEEK-1 rows carry a trailing_usage — "
                   f"that number cannot exist before any week has been "
                   f"played. THE POINT-IN-TIME JOIN IS LEAKING.")

    # Domain checks.
    for f, lo, hi in (("rec", 0, 30), ("car", 0, 60), ("att", 0, 80),
                      ("cmp", 0, 80), ("pass_yds", -50, 800),
                      ("rush_yds", -100, 500), ("rec_yds", -50, 500),
                      ("int", 0, 8), ("depth_rank", 1, 200)):
        off = [g[f] for g in gs if isinstance(g.get(f), (int, float))
               and not (lo <= g[f] <= hi)]
        if off:
            bad.append(f"{f}: {len(off):,} rows outside [{lo},{hi}] "
                       f"e.g. {off[:5]}")

    # cmp must never exceed att.
    n = sum(1 for g in gs if g.get("cmp") is not None
            and g.get("att") is not None and g["cmp"] > g["att"])
    if n:
        bad.append(f"{n:,} rows have cmp > att — the C/ATT split is wrong")

    # Anything that cannot exist for college must be ABSENT, not null.
    for f in ("snaps", "snap_pct", "tgt_share", "ay_share", "inj",
              "ahead_out", "ol_out", "opp_dl_out", "wx"):
        if any(f in g for g in gs):
            bad.append(f"{f} is present on CFB rows — it cannot exist for "
                       f"college and must be ABSENT, not null")

    # Scope.
    if any(g.get("conf") not in POWER4 for g in gs):
        bad.append("non-Power-4 rows leaked past the scope filter")
    return bad


# ══════════════════════════════════════════════════════════════════════
def probe(log=log):
    if not KEY:
        log("FATAL: CFBD_API_KEY is not set.")
        return False

    log("=" * 72)
    log("CFB — PROBE + BACK-FILL + VERIFY, one dispatch")
    log("=" * 72)

    # 🔴 THE TESTS RUN FIRST, ON THE RUNNER, BEFORE A SINGLE CALL.
    # ⛔ A TEST SUITE THAT LIVES ON A LAPTOP IS A TEST SUITE THAT NEVER
    # RUNS — the workflow already says exactly this about the MLB tests.
    # These two caught real defects before this file ever shipped: the
    # cascade returned 0 when a starter was absent, and the
    # constant-feature guard failed a legitimate build on a small slice.
    # ⚠️ Run as a SUBPROCESS because test_cfb.py imports this module.
    tf = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "test_cfb.py")
    if os.path.exists(tf):
        import subprocess
        r = subprocess.run([sys.executable, tf], capture_output=True, text=True)
        log(r.stdout.rstrip())
        if r.returncode != 0:
            log(r.stderr.rstrip())
            log("⛔ cfb self-tests FAILED — nothing collected, nothing written.")
            return False
    else:
        log("⚠️ test_cfb.py is not in the repo — the point-in-time join is")
        log("   going UNTESTED. That is a hole, not a clean run.")

    report = run_probe(log)

    raw = os.environ.get("SEASON", "2021-2025").strip()
    if "-" in raw:
        a, b = raw.split("-", 1)
        seasons = list(range(int(a), int(b) + 1))
    else:
        seasons = [int(x) for x in raw.replace(",", " ").split()]
    log(f"\nBACK-FILL: {seasons}")

    os.makedirs(OUT, exist_ok=True)
    done, failed, dist = [], [], []
    for season in seasons:
        log(f"\n=== {season} ===")
        try:
            doc, unmapped, n = build_season(season, log)
            bad = verify(doc, log)
            if bad:
                # 🔴 THE SEASON IS NOT WRITTEN. Bad data on disk is worse
                # than no data, because the next run treats it as fact.
                for b in bad:
                    log(f"    ⛔ VERIFY: {b}")
                raise RuntimeError("; ".join(bad)[:800])
            vs, kept = build_vs_position(doc, log)
            for f, o in ((f"players-{season}.json.gz", doc),
                         (f"vs-position-{season}.json.gz", vs)):
                with gzip.open(f"{OUT}/{f}", "wt", encoding="utf-8") as fh:
                    json.dump(o, fh)
                log(f"    wrote {OUT}/{f}")
            done.append(season)
            dist.append({"season": season, "player_weeks": n,
                         "vs_position_rows": kept,
                         "usage_quantiles": _q([g["usage"] for p in
                                                doc["players"].values()
                                                for g in p["g"]]),
                         "unmapped": [[c, s, v] for (c, s), v
                                      in unmapped.items()]})
        except Exception as e:
            # 🔴 ONE BAD SEASON MUST NOT DESTROY THE WHOLE BACK-FILL.
            log(f"    SEASON {season} FAILED: {type(e).__name__}: {e}")
            failed.append((season, f"{type(e).__name__}: {e}"))

    with open(f"{OUT}/backfill-report.txt", "w", encoding="utf-8") as fh:
        fh.write(f"cfb back-fill at {datetime.datetime.now(datetime.timezone.utc)}\n")
        fh.write(f"requested: {seasons}\nwritten  : {done}\n")
        fh.write(f"failed   : {[y for y, _ in failed]}\n\n")
        for y, why in failed:
            fh.write(f"--- {y} ---\n{why}\n\n")

    report["seasons_written"] = done
    report["seasons_failed"] = [[y, w] for y, w in failed]
    report["per_season"] = dist
    report["probed_at"] = (datetime.datetime.now(datetime.timezone.utc)
                           .strftime("%Y-%m-%dT%H:%M:%SZ"))
    with open(f"{OUT}/probe-report.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    log(f"\nwrote {OUT}/probe-report.json")

    if failed:
        log(f"⛔ {len(failed)} season(s) failed — see backfill-report.txt")
        return False
    return True


def _q(v):
    """The usage distribution T37-CFB needs. ⛔ The floor is NOT set here."""
    v = sorted(x for x in v if isinstance(x, (int, float)))
    if not v:
        return {}
    def at(p):
        return v[min(len(v) - 1, int(p * len(v)))]
    return {"n": len(v), "p10": at(.10), "p25": at(.25), "p50": at(.50),
            "p75": at(.75), "p90": at(.90), "max": v[-1]}


if __name__ == "__main__":
    sys.exit(0 if probe() else 1)
