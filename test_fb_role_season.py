#!/usr/bin/env python3
r"""test_fb_role_season.py — an NFL row's role is THIS season's, for every player.

`[Sam, 2026-10-15]` "we can't be betting on guys like tory horton because he's had 2 good
games ... he's a wr4" set the role check (#270). `[2026-10-16]` An independent recheck of
the live NFL card found three gaps in it: a ROOKIE (no rated-season log) got no role, so an
over on him skipped the check (4 of 25 liked props had none); a player with NO game this
season got last season's (Tanner McKee printed 2025's 44% of snaps); and a share stored at
3 decimals was rounded twice (Jalen Royals' 5.47% of targets printed 6%). Planted logs and
a planted card build; ⛔ reads nothing live.

# @vacuity 🔴 a share is rounded once, on the page
#   file: card_fb.py
#   find:     return {"snap": round(m("snap_pct"), 4), "tgt_share": round(m("tgt_share"), 4), "car": round(m("car"), 1),
#   with:     return {"snap": round(m("snap_pct"), 3), "tgt_share": round(m("tgt_share"), 3), "car": round(m("car"), 1),
#
# @vacuity 🔴 a veteran's role is this season's log, found by his id
#   file: card_fb.py
#   find:         return role_of(CUR_P[pids[0]])
#   with:         return role_of(plog)
#
# ~~@vacuity 🔴 a rookie's role is found by a unique name in this season's log~~ (find `if len(cur) == 1:`)
#   and ~~@vacuity 🔴 an ambiguous name gets no role, never a guess~~ (find `if len(cur) > 1:`):
#   `[2026-10-27, review 2]` the unique-name fallback is gone. It had no team check, so the Titans' RB
#   Michael Carter's TD row (his name ambiguous) carried the Eagles CB's 0% of offensive snaps. A rookie
#   is matched in this season's log now (card_fb.match_player) and found by his id, the veteran's line
#   above; an ambiguous or unmatched match has no role:
# @vacuity 🔴 an ambiguous match gets no role, never the first holder's
#   file: card_fb.py
#   find:     if len(pids) != 1:
#   with:     if not pids:
#
# @vacuity 🔴 ...and no namesake lends his role by name (the removed fallback, put back)
#   file: card_fb.py
#   find:         return None                          # ⛔ ambiguous or unmatched: never a namesake's role
#   with:         return (lambda c: role_of(CUR_P[c[0]]) if len(c) == 1 else None)([q for q in CUR_P if norm(CUR_P[q].get("name")) == norm(who)])
#
# @vacuity 🔴 a player with no game this season has no role this season (his over fails the check)
#   file: card_fb.py
#   find:     return {"snap": 0.0, "tgt_share": 0.0, "car": 0.0, "n": 0} if plog is not None else None
#   with:     return role_of(plog)
#
# ~~@vacuity 🔴 the card sets a role for a player with no rated-season log~~ (its mutation: a role only
#   when `plog is not None`). `[review, 2026-10-26]` VACUOUS since T73's review fix: card_fb.match_player
#   finds a rookie in this season's log, so his `plog` is that log and the old mutation left his role in
#   place (the vacuity sweep caught it). The same defect, a role only for a player with a LAST-season
#   log, in the new code's terms:
# @vacuity 🔴 the card sets a role for a player with no rated-season log
#   file: card_fb.py
#   find:                 if LEAGUE == "nfl" and not TEAM_UNIT.search(who):        # never a team defense
#   with:                 if LEAGUE == "nfl" and plog is not None and plog_season == season:        # never a team defense
"""
import datetime
import gzip
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
import card_fb as CF  # noqa: E402
import fb_why as W  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

UTC = datetime.timezone.utc


def g(d, snap, tgt=0.0, car=0.0, **k):
    return dict({"d": d, "snap_pct": snap, "tgt_share": tgt, "car": car, "team": "SEA"}, **k)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 A SHARE IS ROUNDED ONCE")
# ══════════════════════════════════════════════════════════════════════
_royals = CF.role_of({"g": [g("2026-10-01", 0.33, 0.046512), g("2026-10-05", 0.31, 0.043478),
                            g("2026-10-11", 0.33, 0.074074)]})
eq(W.prop_why({"player": "Nobody", "market": "player_receptions", "side": "under", "role": _royals},
              type("X", (), {"lg": "nfl", "log_of": lambda s, w: None, "resolve": lambda s, n: None})())[0],
   "Over his last 3 games he has played 32% of the snaps and 5% of the team's targets.",
   "🔴 Jalen Royals' 5.47% of targets reads 5%, never 6% (stored at 4 decimals, rounded once)")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THIS SEASON'S ROLE, FOR A VETERAN, A ROOKIE AND A PLAYER WITH NO GAME")
# ══════════════════════════════════════════════════════════════════════
VET = {"name": "Vet Receiver", "pos": "WR", "g": [g("2025-12-%02d" % d, 0.95, 0.30) for d in (14, 21, 28)]}
GONE = {"name": "Backup Quarterback", "pos": "QB", "g": [g("2025-12-%02d" % d, 1.0, 0.0, 2.0) for d in (14, 21, 28)]}
TWIN25 = {"name": "Same Name", "pos": "WR", "g": [g("2025-12-28", 0.9, 0.2)]}
CUR = {"v1": {"name": "Vet Receiver", "pos": "WR", "g": [g("2026-10-%02d" % d, 0.40, 0.10) for d in (4, 11)]},
       "r1": {"name": "Rook Receiver", "pos": "WR", "g": [g("2026-10-%02d" % d, s, t) for d, s, t in
                                                         ((4, 0.10, 0.03), (11, 0.20, 0.05))]},
       "t1": {"name": "Same Name", "pos": "WR", "g": [g("2026-10-04", 0.5, 0.1)]},
       "t2": {"name": "Same Name", "pos": "RB", "g": [g("2026-10-04", 0.6, 0.0, 9.0)]},
       # `[2026-10-27, review 2]` an Eagles CB: 2025 held his name twice (him and a Titans RB), 2026 once
       "cb": {"name": "Twin Back", "pos": "CB", "g": [g("2026-10-%02d" % d, 0.0, 0.0, team="PHI") for d in (4, 11)]}}
_old = (CF.CUR_P, CF.CUR_SEASON)
try:
    CF.CUR_P, CF.CUR_SEASON = CUR, 2026
    R = {"vet": CF.current_role("Vet Receiver", ["v1"], VET, 2025),
         # ~~"rookie": CF.current_role("Rook Receiver", [], None, 2025)~~ (found by his unique name):
         #    `[2026-10-27, review 2]` card_fb.match_player matches a rookie in this season's log, so the
         #    card hands his id and his this-season log
         "rookie": CF.current_role("Rook Receiver", ["r1"], CUR["r1"], 2025),
         "gone": CF.current_role("Backup Quarterback", ["q9"], GONE, 2025),
         # ~~"twin": CF.current_role("Same Name", ["z9"], TWIN25, 2025)~~ (ambiguous by the name index):
         #    the match decides ambiguity now; two ids are ambiguous
         "twin": CF.current_role("Same Name", ["t1", "t2"], None, 2025),
         "nobody": CF.current_role("Never Logged", [], None, 2025),
         # `[2026-10-27, review 2]` no namesake lends his role: an unmatched name one 2026 player holds, and
         # Michael Carter's shape (ambiguous; the CB the one who has played)
         "unmatched": CF.current_role("Rook Receiver", [], None, 2025),
         "namesake": CF.current_role("Twin Back", ["cb", "rb"], None, 2025),
         # ...and the matched player with no game this season keeps HIS zero role while two namesakes play
         "z9": CF.current_role("Same Name", ["z9"], TWIN25, 2025)}
    CF.CUR_P, CF.CUR_SEASON = {"v1": VET}, 2025
    R["same"] = CF.current_role("Vet Receiver", ["v1"], VET, 2025)
finally:
    CF.CUR_P, CF.CUR_SEASON = _old
eq(R["vet"], {"snap": 0.4, "tgt_share": 0.1, "car": 0.0, "n": 2},
   "🔴 a veteran: THIS season's 40% of snaps (his id in this season's log), never 2025's 95%")
eq(R["rookie"], {"snap": 0.15, "tgt_share": 0.04, "car": 0.0, "n": 2},
   "🔴 a rookie (no 2025 log): his own 2026 role, found by ~~his unique name~~ his matched id")
eq(R["gone"], {"snap": 0.0, "tgt_share": 0.0, "car": 0.0, "n": 0},
   "🔴 a player with no game this season: no role this season (Tanner McKee's 2025 starts never stand in)")
eq((R["twin"], R["nobody"]), (None, None),
   "🔴 an ambiguous match gets no role (never a guess); a player logged nowhere, none")
eq((R["unmatched"], R["namesake"], R["z9"]), (None, None, {"snap": 0.0, "tgt_share": 0.0, "car": 0.0, "n": 0}),
   "🔴 no namesake lends his role: an unmatched name one 2026 player holds gets none, and so does Michael "
   "Carter's shape (the Titans RB's TD row carried the Eagles CB's 0% of offensive snaps); the matched player "
   "with no 2026 game keeps his own zero role, never his namesakes'")
eq(R["same"], CF.role_of(VET), "   the rated season IS this season: his rated log")
_over = lambda role, mk="player_reception_yds": {"side": "over", "market": mk, "role": role}  # noqa: E731
eq([CF.role_ok(_over(R["gone"])), CF.role_ok(dict(_over(R["gone"]), side="under")), CF.role_ok(_over(R["rookie"]))],
   [False, True, False],
   "🔴 the role check: the no-game player's over FAILS (it used to pass on 2025's snaps), his under is never "
   "blocked, and the rookie's over at 15% of snaps fails too (it used to skip the check)")
eq(W.prop_why({"player": "Backup Quarterback", "market": "player_pass_yds", "side": "under", "role": R["gone"]},
              type("X", (), {"lg": "nfl", "log_of": lambda s, w: None, "resolve": lambda s, n: None})()), [],
   "🔴 ...and his why prints no snaps sentence (n 0)")

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 THE REAL CARD SETS IT FOR EVERY PLAYER ON THE BOARD")
# ══════════════════════════════════════════════════════════════════════
_n = datetime.datetime.now(UTC)
_K = (_n + datetime.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
_T = tempfile.mkdtemp(prefix="roleseason-")


def put(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with (gzip.open(path, "wt", encoding="utf-8") if path.endswith(".gz") else open(path, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)


_vets = ["Vet One", "Vet Two", "Vet Three", "Backup Quarterback"]
try:
    _L = os.path.join(_T, "data", "nfl", "latest")
    put(os.path.join(_L, "props.json.gz"), {"pulled_at": (_n - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "games": [{"id": "ev1", "away": "Seattle Seahawks", "home": "Denver Broncos", "commence": _K, "props": [
            {"player": w, "market": "player_receptions", "line": 3.5,
             "sides": {"over": {"price": -110, "book": "fanduel", "n_books": 3}}}
            for w in _vets + ["Rook Receiver", "Twin Back"]]}]})
    # `[2026-10-27, review 2]` Twin Back is Michael Carter's shape: 2025 held the name twice (an Eagles CB
    #    and a Cardinals RB), 2026 once (the CB); neither plays for Seattle or Denver
    put(os.path.join(_L, "players-2025.json.gz"), {"season": 2025, "players": dict({
        "p%d" % i: {"name": w, "pos": "WR", "g": [g("2025-09-%02d" % (j + 7), 0.9, 0.25, rec=5) for j in range(10)]}
        for i, w in enumerate(_vets)},
        tb1={"name": "Twin Back", "pos": "CB", "g": [g("2025-09-%02d" % (j + 7), 0.0, team="PHI") for j in range(10)]},
        tb2={"name": "Twin Back", "pos": "RB", "g": [g("2025-09-%02d" % (j + 7), 0.6, 0.1, 9.0, team="ARI", rec=2)
                                                    for j in range(10)]})})
    # this season: the three veterans and the rookie have played; the backup has not
    put(os.path.join(_L, "players-2026.json.gz"), {"season": 2026, "players": dict(
        {"p%d" % i: {"name": w, "pos": "WR", "g": [g("2026-10-%02d" % d, 0.7, 0.2, rec=4) for d in (4, 11)]}
         for i, w in enumerate(_vets[:3])},
        r1={"name": "Rook Receiver", "pos": "WR", "g": [g("2026-10-%02d" % d, 0.12, 0.04, rec=1) for d in (4, 11)]},
        tb1={"name": "Twin Back", "pos": "CB", "g": [g("2026-10-%02d" % d, 0.0, team="PHI") for d in (4, 11)]})})
    _cwd = os.getcwd()
    try:
        os.chdir(_T)
        CF.main()
        CARD = json.load(open(os.path.join("picks", "fb-nfl-latest.json"), encoding="utf-8"))
    finally:
        os.chdir(_cwd)
finally:
    shutil.rmtree(_T, ignore_errors=True)
_role = {r["player"]: r.get("role") for r in CARD.get("picks") or []}
ck(set(_role) >= set(_vets) | {"Rook Receiver"}, "⚠️ the planted board's five players are on the built card",
   str(sorted(_role)))
eq((_role.get("Vet One"), _role.get("Rook Receiver"), _role.get("Backup Quarterback")),
   ({"snap": 0.7, "tgt_share": 0.2, "car": 0.0, "n": 2}, {"snap": 0.12, "tgt_share": 0.04, "car": 0.0, "n": 2},
    {"snap": 0.0, "tgt_share": 0.0, "car": 0.0, "n": 0}),
   "🔴 the REAL card_fb.main: a veteran's role is 2026's (70%, not 2025's 90%), the rookie HAS one, and the "
   "backup who has not played this season has a zero role")
ck(not any(r["player"] in ("Rook Receiver", "Backup Quarterback") for r in CARD.get("liked") or []),
   "🔴 ...so neither the rookie's nor the backup's over is ever a liked pick")
ck("Twin Back" in _role and _role["Twin Back"] is None,
   "🔴 a name the game's teams cannot settle (Michael Carter's shape) gets NO role on the real card, never the "
   "Eagles CB's 0% of offensive snaps (`[2026-10-27, review 2]`: card_fb.match_player, current_role)",
   _role.get("Twin Back", "not on the card"))
