#!/usr/bin/env python3
r"""T75 — THE BACKUP-QB BACKGROUND CHECK (research/fb_refit_spec.md §3k). `[Sam, 2026-11-10]`

*"the model finds the backup who is starting and does a "backggriudn check" ... seeing how theyve
performed in other starts from either that year or previous years"*; his answers: "All past weeks
too", "Yes, require it", "Add the second one", "Use what's stored now".

  §1  fb_qb.Book on a planted league: the starter of record, the usual starter, each start's mark,
      the prior (per team's first stored season, every earlier season), a QB's grade and the
      rating's QB mix (only the games the champion's rating reads), each recomputed from §3k's words
  §2  the expected starter: the last starter, a listed-out last starter's replacement, the usual
      starter returning (even when the fill-in is listed out), no rated game, no earlier start
  §3  POINT IN TIME: results and starts dated on or after the cut change nothing
  §4  fb_challengers: rated_games, attach (the NFL reports, the college reports) and extend
  §5  fb_refit: the direction rule, wired through contest(), and the Monday email says why
  §6  the registry, the counts, registration and §3k's frozen numbers in the code

The planted league: AAA, BBB, CCC, DDD stored from 2024 (2024's schedule in history/, as the NFL's
2021-2024 are), EEE and FFF first stored in 2025 (as college's Group of 5 teams are).

⛔ A TEST ASKS THE CODE: every tree is planted, every date fixed. Nothing here reads a game result
to judge the challengers (rule 13): the planted scores exist only so the marks have numbers.

# @vacuity 🔴 a QB's grade is shrunk toward the prior with K starts
#   file: fb_qb.py
#   find: return (cum[i] + K * p) / (n[i] + K)
#   with: return cum[i] / max(1, n[i])
#
# @vacuity 🔴🔴 a start dated ON the cut is not read (point in time)
#   file: fb_qb.py
#   find: i = bisect.bisect_left(days, cut)
#   with: i = bisect.bisect_right(days, cut)
#
# @vacuity 🔴 the starter of record is a QB when one threw
#   file: fb_qb.py
#   find: qbs = [(a, pid) for pid, a in by.items() if self.pos.get(pid) == "QB"]
#   with: qbs = [(a, pid) for pid, a in by.items()]
#
# @vacuity 🔴 a tie for the most attempts goes to the larger player id
#   file: fb_qb.py
#   find: best = max(qbs or [(a, pid) for pid, a in by.items()])
#   with: best = min(qbs or [(a, pid) for pid, a in by.items()], key=lambda x: (-x[0], x[1]))
#
# @vacuity 🔴 ...and so does a tie for the replacement
#   file: fb_qb.py
#   find: return max(tot.items(), key=lambda kv: (kv[1], kv[0]))[0]
#   with: return min(tot.items(), key=lambda kv: (-kv[1], kv[0]))[0]
#
# @vacuity 🔴 ...else the top passer of any position
#   file: fb_qb.py
#   find: best = max(qbs or [(a, pid) for pid, a in by.items()])
#   with: best = max(qbs or [(0, None)])
#
# @vacuity 🔴 an AWAY start's mark: points minus (total - margin) / 2
#   file: fb_qb.py
#   find: marks[(t, d)] = pts - ((tot + m) / 2.0 if home else (tot - m) / 2.0)
#   with: marks[(t, d)] = pts - ((tot + m) / 2.0 if home else (tot + m) / 2.0)
#
# @vacuity 🔴 the grade divides by his MARKED starts (an unmarked start adds to neither sum)
#   file: fb_qb.py
#   find: n.append(n[-1] + (0 if mk is None else 1))
#   with: n.append(n[-1] + 1)
#
# @vacuity 🔴 ...but "3 or fewer prior stored starts" counts every stored start, marked or not
#   file: fb_qb.py
#   find: if new and mk is not None and i <= PRIOR_MAX and s is not None:
#   with: if new and mk is not None and n[-1] - 1 <= PRIOR_MAX and s is not None:
#
# @vacuity 🔴 the prior reads EARLIER seasons only
#   file: fb_qb.py
#   find: pool = [m for s, v in self._early.items() if s < season for m in v]
#   with: pool = [m for s, v in self._early.items() if s <= season for m in v]
#
# @vacuity 🔴 the prior for a season with no logs stored yet still reads every earlier season
#   file: fb_qb.py
#   find: if season is None:
#   with: if season is None or season not in set(self.season.values()):
#
# @vacuity 🔴🔴 a team's first stored season's starters are no replacement level (judged per team)
#   file: fb_qb.py
#   find: new = s0 is not None and team_first.get(t0) is not None and s0 > team_first[t0]
#   with: new = s0 is not None and s0 > min(team_first.values())
#
# @vacuity 🔴 replacement level: starts with 3 or FEWER stored before
#   file: fb_qb.py
#   find: if new and mk is not None and i <= PRIOR_MAX and s is not None:
#   with: if new and mk is not None and i < PRIOR_MAX and s is not None:
#
# @vacuity 🔴 the usual starter's window is 8 games
#   file: fb_qb.py
#   find: last = self.before(team, cut)[-USUAL_GAMES:]
#   with: last = self.before(team, cut)[-(USUAL_GAMES - 1):]
#
# @vacuity 🔴 the usual starter: a tie goes to the most recent
#   file: fb_qb.py
#   find: return next(self.starter[(team, d)] for d in reversed(last) if c[self.starter[(team, d)]] == top)
#   with: return next(self.starter[(team, d)] for d in last if c[self.starter[(team, d)]] == top)
#
# @vacuity 🔴🔴 a listed-out last starter is replaced
#   file: fb_qb.py
#   find: if last in out_now:
#   with: if False:
#
# @vacuity 🔴 the usual starter returns when he was the one listed out
#   file: fb_qb.py
#   find: if u is not None and u != last and u not in out_now and u in out_at(team, prev[-1]):
#   with: if False:
#
# @vacuity 🔴 the usual starter returns only if he is not listed out now
#   file: fb_qb.py
#   find: if u is not None and u != last and u not in out_now and u in out_at(team, prev[-1]):
#   with: if u is not None and u != last and u in out_at(team, prev[-1]):
#
# @vacuity 🔴 ...even when the fill-in is listed out now
#   file: fb_qb.py
#   find: if u is not None and u != last and u not in out_now and u in out_at(team, prev[-1]):
#   with: if u is not None and u != last and u not in out_now and u in out_at(team, prev[-1]) and last not in out_now:
#
# @vacuity 🔴🔴 the mix reads only the games the champion's rating reads
#   file: fb_qb.py
#   find: if (team, d) not in self.rated:
#   with: if False:
#
# @vacuity 🔴 the rating's mix is weighted as the rating weighs its games
#   file: fb_qb.py
#   find: HALF_LIFE = FM.RATING_HALF_LIFE
#   with: HALF_LIFE = 15.0
#
# @vacuity 🔴 attach_qb's marks read every stored schedule, the history seasons too
#   file: fb_challengers.py
#   find: G = sorted(set(FM.rating_games(lg, root)).union(history_rating_games(lg, root)))
#   with: G = sorted(set(FM.rating_games(lg, root)))
#
# @vacuity 🔴 today's model's rating reads latest/ only; the history seasons only for H or HC
#   file: fb_challengers.py
#   find: if FM.CHAMPION.get(lg) in HIST:
#   with: if True:
#
# @vacuity 🔴 rated_games keys both teams of a game
#   file: fb_challengers.py
#   find: return {(t, g[0]) for g in G for t in (g[1], g[2])}
#   with: return {(t, g[0]) for g in G for t in (g[1],)}
#
# @vacuity 🔴 college reads its reports at cfb_injuries' 9:00 ET pick time (now None)
#   file: fb_challengers.py
#   find: cache[s] = (cfb_injuries.pick_time_outs(s, root), cfb_injuries.Roles(s, root)) \
#   with: cache[s] = (cfb_injuries.pick_time_outs(s, root, now="2000-01-01T00:00:00Z"), cfb_injuries.Roles(s, root)) \
#
# @vacuity 🔴 the NFL reading is THIS game's week's report
#   file: fb_challengers.py
#   find: rep_now = {p.get("gsis_id") for p in listed(r["season"], team, r.get("week")) if p.get("gsis_id")}
#   with: rep_now = {p.get("gsis_id") for p in listed(r["season"], team, None) if p.get("gsis_id")}
#
# @vacuity 🔴 the NFL reading of an earlier game is THAT game's week's report
#   file: fb_challengers.py
#   find: rep_at = {p.get("gsis_id") for p in listed(s, team, w) if p.get("gsis_id")}
#   with: rep_at = {p.get("gsis_id") for p in listed(s, team, None) if p.get("gsis_id")}
#
# @vacuity 🔴🔴 an NFL starter on the reserve list (absent from the report) is listed out
#   file: fb_challengers.py
#   find: return rep_now | on_reserve(r["season"], team, r.get("week"), r["day"])
#   with: return rep_now
#
# @vacuity 🔴 ...and a usual starter on it at the fill-in's game returns when he is off it
#   file: fb_challengers.py
#   find: return rep_at | on_reserve(s, team, w, day)
#   with: return rep_at
#
# @vacuity 🔴 a reserve-list name two of the team's players share is not listed
#   file: fb_challengers.py
#   find: if len(ids) == 1 and book.pos.get(next(iter(ids))) == "QB":
#   with: if ids:
#
# @vacuity 🔴 ...and one held by a non-QB is never a QB listing
#   file: fb_challengers.py
#   find: if len(ids) == 1 and book.pos.get(next(iter(ids))) == "QB":
#   with: if len(ids) == 1:
#
# @vacuity 🔴 ...the ambiguity is judged among EVERY logged teammate, not the QBs alone
#   file: fb_challengers.py
#   find: by_name[(t, name_key(book.name.get(pid)))].add(pid)
#   with: by_name[(t, name_key(book.name.get(pid)))].update([pid] if book.pos.get(pid) == "QB" else [])
#
# @vacuity 🔴🔴 ...among those logged for the team BEFORE the game (point in time)
#   file: fb_challengers.py
#   find: ids = {p for p in by_name.get((team, name_key(nm))) or () if book.first[(team, p)] < cut}
#   with: ids = set(by_name.get((team, name_key(nm))) or ())
#
# @vacuity 🔴🔴 ...before the game, never on its own day (a debut's row is known only after it)
#   file: fb_challengers.py
#   find: if book.first[(team, p)] < cut}
#   with: if book.first[(team, p)] <= cut}
#
# @vacuity 🔴🔴 ...and at the fill-in's game, among those logged before THAT game
#   file: fb_challengers.py
#   find: return rep_at | on_reserve(s, team, w, day)
#   with: return rep_at | on_reserve(s, team, w, "9999")
#
# @vacuity 🔴 ...and on THIS team only
#   file: fb_challengers.py
#   find: ids = {p for p in by_name.get((team, name_key(nm))) or () if book.first[(team, p)] < cut}
#   with: ids = {p for (t2, n2), v in by_name.items() if n2 == name_key(nm) for p in v}
#
# @vacuity 🔴 a name is compared bar case
#   file: fb_challengers.py
#   find: return " ".join(str(name or "").split()).casefold()
#   with: return " ".join(str(name or "").split())
#
# @vacuity 🔴 ...and bar spacing
#   file: fb_challengers.py
#   find: return " ".join(str(name or "").split()).casefold()
#   with: return str(name or "").casefold()
#
# @vacuity 🔴 the reserve list only: never the inactive list
#   file: fb_challengers.py
#   find: if p.get("name") and any(str(w).startswith(RESERVE) for w in p.get("why") or [])]
#   with: if p.get("name")]
#
# @vacuity 🔴 the college reading of an earlier game is that game's report
#   file: fb_challengers.py
#   find: return listed_gid(book.season.get((team, day)), book.gid.get((team, day)), team)
#   with: return set()
#
# @vacuity 🔴 college lists only Out, Out for Season and Doubtful
#   file: fb_challengers.py
#   find: if (p.get("status") or "").strip().lower() in cfb_injuries.OUT_STATUSES}
#   with: if True}
#
# @vacuity 🔴 QP reads IN's offence and defence shares out
#   file: fb_challengers.py
#   find: r["sig"]["qp"] = {"off": (h[1], a[1]), "ol": ol, "def": (h[2], a[2])}
#   with: r["sig"]["qp"] = {"off": (h[0], a[0]), "ol": ol, "def": (h[0], a[0])}
#
# @vacuity 🔴 spread and moneyline read away - home
#   file: fb_challengers.py
#   find: add = [h + a] if market == "total" else [a - h]
#   with: add = [h + a] if market == "total" else [h - a]
#
# @vacuity 🔴 QP adds the linemen, counted
#   file: fb_challengers.py
#   find: for part in (("off", "ol", "def") if name == "QP" else ("off", "def")):
#   with: for part in (("off", "def") if name == "QP" else ("off", "def")):
#
# @vacuity 🔴🔴 contest() hands the direction rule its fits
#   file: fb_refit.py
#   find: out["direction"] = direction(fits, latest)
#   with: pass
#
# @vacuity 🔴🔴 ...the LATEST Monday each market priced
#   file: fb_refit.py
#   find: if wk >= latest.get(mk, ("", None))[0]:
#   with: if mk not in latest:
#
# @vacuity 🔴🔴 the direction reads the QB delta's own weight (after the champion's inputs)
#   file: fb_refit.py
#   find: i = 1 + len(FM.features(row, mk))
#   with: i = len(FM.features(row, mk))
#
# @vacuity 🔴🔴 a weight that points the wrong way is not ok
#   file: fb_refit.py
#   find: "ok": w is not None and w * DIRECTION[mk] > 0}
#   with: "ok": w is not None}
#
# @vacuity 🔴🔴 a T75 WINS needs the direction
#   file: fb_refit.py
#   find: if x["name"] in FC.T75 and not (d and all(v["ok"] for v in d.values())):
#   with: if False:
#
# @vacuity 🔴 the email says why a T75 score that beat the model is no win
#   file: status.py
#   find: if v == "NOT YET" and x.get("why"):
#   with: if False:
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

import fb_model as FM  # noqa: E402
import fb_challengers as FC  # noqa: E402
import fb_qb as Q  # noqa: E402
import fb_refit as R  # noqa: E402
import status as S  # noqa: E402
from tcheck import ck, eq, note, section  # noqa: E402

FM.CHAMPION.update(nfl=None, ncaaf=None)           # pr-tests' champion job names some: the code's own here
TMP = tempfile.mkdtemp(prefix="t75-")
UTC = datetime.timezone.utc


def put(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(doc, fh)


def sundays(first, n):
    d = datetime.date.fromisoformat(first)
    return [(d + datetime.timedelta(days=7 * i)).isoformat() for i in range(n)]


D24, D25, D26 = sundays("2024-09-08", 10), sundays("2025-09-07", 10), sundays("2026-09-13", 10)
DAYS = {2024: D24, 2025: D25, 2026: D26}
POS = {"r1": "RB", "w1": "WR", "k1": "CB", "t1": "TE", "y1": "LB"}
NAMES = {"e2": "E1", "a3": "D2", "y1": "B1"}     # names shared: within EEE, across teams, a QB and an LB


def passers(t, season, i, d, swap):
    """(player, attempts, extra log fields) for team `t`'s game `i` of `season`.
    AAA: a1; a2 on weeks 7-8 of 2025 (a1 listed out) and from week 4 of 2026; a3 throws 3 in relief;
         a WR (w1) and a CB (k1) with snap rows in 2026 (QP's shares).
    BBB: b1, with b2 and b3 throwing 3 each in relief on weeks 1-3 of 2026 (a tied replacement); a
         linebacker (y1) stored as "B1" too, logged every game, on the reserve list in week 5 of 2026;
         a running back (r1) throws 40 once (2025 week 1): the starter of record stays b1; from
         week 7 of 2026 g9, whose first stored start (a Wednesday, no scheduled game) has no mark.
    CCC: c1; c2 fills in on weeks 1-3 of 2026 with c3 in relief (c1 listed out), then c1 is back.
    DDD: d1; d2 on weeks 2-5 of 2026 (the 8-game window: d1 d2 d2 d2 d2 d1 d1 d1); d1 on the reserve
         list in week 2 of 2026, d2 in week 6 (as "  d2 "; AAA's a3 is stored as "D2" too).
    EEE: e1; e2 from week 6 of 2026, who holds the same stored name as e1 ("E1"); "E1" on the reserve
         list in weeks 3 and 6 (e1 alone then: e2's first log row is week 6's own game) and week 7
         (both). FFF: f1; a TE (t1) the only passer once (2025
         week 3), on the reserve list in week 4 of 2025; f1 inactive in week 4 of 2026; f1
         and f2 tied on attempts in week 10 of 2026. EEE and FFF are first stored in 2025."""
    if t == "AAA":
        if season == 2025:
            qb = "a2" if i in (6, 7) else "a1"
        elif season == 2026:
            qb = "a2" if i >= 3 else "a1"
        else:
            qb = "a1"
        qb = "a3" if swap and d >= swap else qb
        out = [(qb, 30, {}), ("a3" if qb != "a3" else "a1", 3, {})]
        if season == 2026:
            out += [("w1", 0, {"snap_pct": 0.8}), ("k1", 0, {"def_pct": 0.9})]
        return out
    if t == "BBB":
        if season == 2026 and i >= 6:
            out = [("g9", 30, {})]
        elif season == 2026 and i < 3:
            out = [("b1", 30, {}), ("b2", 3, {}), ("b3", 3, {})]
        else:
            out = [("b1", 30, {})] + ([("r1", 40, {})] if (season, i) == (2025, 0) else [])
        return out + [("y1", 0, {})]
    if t == "CCC":
        if season == 2026:
            return [("c2", 30, {}), ("c3", 3, {})] if i < 3 else [("c1", 30, {}), ("c3", 3, {})]
        return [("c1", 30, {})]
    if t == "DDD":
        return [("d2" if season == 2026 and 1 <= i <= 4 else "d1", 30, {})]
    if t == "EEE":
        return [("e2" if season == 2026 and i >= 5 else "e1", 30, {})]
    if (season, i) == (2026, 9):
        return [("f1", 15, {}), ("f2", 15, {})]
    return [("t1", 30, {})] if (season, i) == (2025, 2) else [("f1", 30, {})]


RES = ["roster: reserve list (injured reserve and similar)"]
TEAM_OUT = {2025: {"FFF": {"4": {"players": [{"name": "T1", "why": RES}]}}},
            2026: {"BBB": {"5": {"players": [{"name": "B1", "why": RES}]}},
                   "DDD": {"2": {"players": [{"name": "D1", "why": RES}]},
                           "6": {"players": [{"name": "  d2 ", "why": RES}]}},
                   "EEE": {"3": {"players": [{"name": "E1", "why": RES}]}, "6": {"players": [{"name": "E1", "why": RES}]},
                           "7": {"players": [{"name": "E1", "why": RES}]}},
                   "FFF": {"4": {"players": [{"name": "F1", "why": ["roster: inactive"]}]}}}}


WED = (datetime.date.fromisoformat(D26[5]) + datetime.timedelta(days=3)).isoformat()   # no game that day


def build(root, bump=None, swap=None):
    """The planted NFL league. `bump`: games dated on or after it score 10 more at home; `swap`:
    from it on, a3 starts for AAA."""
    for season, days in DAYS.items():
        games, players = [], {}
        for i, d in enumerate(days):
            pairs = [("AAA", "BBB"), ("CCC", "DDD")] if i % 2 == 0 else [("AAA", "CCC"), ("BBB", "DDD")]
            if season >= 2025:
                pairs.append(("EEE", "FFF") if i % 2 == 0 else ("FFF", "EEE"))
            for j, (h, a) in enumerate(pairs):
                hs, as_ = 20 + (i * 7 + j * 3 + season) % 11, 17 + (i * 5 + j * 2 + season) % 9
                if bump and d >= bump:
                    hs += 10
                gid = "%d_%02d_%s_%s" % (season, i + 1, a, h)
                games.append({"id": gid, "start": d + "T17:00:00Z", "home": h, "away": a, "final": True,
                              "home_score": hs, "away_score": as_, "neutral": False})
                for t in (h, a):
                    for pid, att, extra in passers(t, season, i, d, swap):
                        p = players.setdefault(pid, {"name": NAMES.get(pid, pid.upper()),
                                                     "pos": POS.get(pid, "QB"), "team": t, "g": []})
                        p["g"].append(dict({"d": d, "team": t, "att": att, "week": i + 1, "game_id": gid}, **extra))
        if season == 2026:                # g9's first stored start: a log row with no scheduled game
            players.setdefault("g9", {"name": "G9", "pos": "QB", "team": "BBB", "g": []})["g"].append(
                {"d": WED, "team": "BBB", "att": 30, "week": 6, "game_id": "x"})
        where = "history" if season == 2024 else "latest"
        put(os.path.join(root, "data", "nfl", where, "schedule-%d.json.gz" % season), {"season": season, "games": games})
        put(os.path.join(root, "data", "nfl", "latest", "players-%d.json.gz" % season),
            dict({"season": season, "players": players}, **({"team_out": TEAM_OUT[season]} if season in TEAM_OUT else {})))
    return root


def book(root, lg="nfl"):
    """The book exactly as attach_qb builds it."""
    G = sorted(set(FM.rating_games(lg, root)) | set(FC.history_rating_games(lg, root)))
    return Q.Book(lg, G, root, rated=FC.rated_games(lg, root))


def wt(wk, d):
    return 0.5 ** ((datetime.date.fromisoformat(wk) - datetime.date.fromisoformat(d)).days / 150.0)


T1 = build(os.path.join(TMP, "one"))
B = book(T1)
_none = lambda team, day: set()      # noqa: E731
_c_out = lambda team, day: {"c1"} if (team, day) == ("CCC", D26[2]) else set()      # noqa: E731
RATED = D25 + D26                   # the games today's model's rating reads (latest/)

try:
    # ══════════════════════════════════════════════════════════════════
    section("1. THE BOOK: STARTER OF RECORD, USUAL STARTER, MARKS, THE PRIOR, A GRADE, THE MIX (§3k's words)")
    # ══════════════════════════════════════════════════════════════════
    eq(B.starter[("AAA", D25[6])], "a2", "the starter of record is the QB with the most attempts (a2 over a3's relief)")
    eq(B.starter[("BBB", D25[0])], "b1", "🔴 ...a QB, even when a running back threw more (r1, 40 to 30)")
    eq(B.starter[("FFF", D25[2])], "t1", "🔴 ...else the top passer of any position (a TE, the only passer)")
    eq(B.starter[("FFF", D26[9])], "f2", "🔴 ...a tie for the most attempts (15 and 15) goes to the larger player id")
    ck("a3" not in set(B.starter.values()) and "c3" not in set(B.starter.values()),
       "   a relief appearance is never a start")
    eq(B.usual("AAA", D25[8]), "a1", "the usual starter: most starts in the previous 8 games (a1 6, a2 2)")
    eq(B.usual("AAA", D26[7]), "a2", "🔴 ...a tie (a1 4, a2 4) goes to the most recent (a2); 9 games would say a1")
    eq(B.usual("AAA", D26[9]), "a2", "   ...and a2 once he has the most of the last 8 (6 of 8)")
    eq(B.usual("DDD", D26[8]), "d1", "🔴 the window is 8 games: d1 d2 d2 d2 d2 d1 d1 d1 ties, the most recent wins "
                                     "(7 games would say d2)")
    ck(len(B.marks) > 150, "every start whose two teams the ratings know has a mark (%d)" % len(B.marks))
    # a mark, recomputed: points minus the ratings' expected points at that game's own Monday, the ratings
    #    solved on every stored schedule (latest and history)
    _G = sorted(set(FM.rating_games("nfl", T1)) | set(FC.history_rating_games("nfl", T1)))
    ck(min(g[0] for g in _G) == D24[0], "   (the history schedule is read for the marks)")
    _d, _h, _a, _hf, _hs, _as = next(g for g in _G if g[0] == D25[6] and "AAA" in (g[1], g[2]))
    _own = FM.own_ratings(_G, {FM.monday(_d)})[FM.monday(_d)]
    _m, _t = FM.own_numbers(_own, _h, _a, _hf == 0.0)
    _want = (_hs - (_t + _m) / 2.0) if _h == "AAA" else (_as - (_t - _m) / 2.0)
    ck(abs(B.marks[("AAA", D25[6])] - _want) < 1e-9,
       "🔴 a start's mark is the team's points minus what the ratings of that game's Monday expected",
       (B.marks[("AAA", D25[6])], _want))
    _d, _h, _a, _hf, _hs, _as = next(g for g in _G if g[0] == D25[1] and "CCC" in (g[1], g[2]))
    _own = FM.own_ratings(_G, {FM.monday(_d)})[FM.monday(_d)]
    _m, _t = FM.own_numbers(_own, _h, _a, _hf == 0.0)
    ck(_a == "CCC" and abs(B.marks[("CCC", D25[1])] - (_as - (_t - _m) / 2.0)) < 1e-9,
       "🔴 ...an AWAY start's: its points minus (total - margin) / 2", (_h, _a, B.marks.get(("CCC", D25[1]))))
    # the prior: early-career starts (3 or fewer stored before) by QBs first seen starting after their
    #    TEAM's first stored season, in every EARLIER season
    _a2_25 = [B.marks[("AAA", d)] for d in (D25[6], D25[7])]
    eq((B.prior(2024), B.prior(2025)), (0.0, 0.0),
       "🔴 2024 (the first stored season) has no earlier season, and its starters are no replacement level: "
       "the 2025 prior is 0 too")
    ck(abs(B.prior(2026) - sum(_a2_25) / 2.0) < 1e-12,
       "🔴🔴 the 2026 prior is a2's two 2025 starts only: EEE's and FFF's 2025 starters are in their teams' first "
       "stored season (veterans whose careers are not stored), and 2026's own starts are not earlier",
       (B.prior(2026), _a2_25))
    _early = ([("AAA", d) for d in (D25[6], D25[7], D26[3], D26[4])] + [("CCC", d) for d in D26[0:3]]
              + [("DDD", d) for d in D26[1:5]] + [("EEE", d) for d in D26[5:9]]
              + [("BBB", d) for d in D26[6:9]]      # g9: his unmarked first start is one of the 4
              + [("FFF", D26[9])])
    ck(all(k in B.marks for k in _early)
       and abs(B.prior(2027) - sum(B.marks[k] for k in _early) / len(_early)) < 1e-12,
       "🔴 2027 (no logs stored yet) reads every earlier season: the first 4 starts (3 or fewer stored before) "
       "of a2, c2, d2, e2, g9 and f2, not a 5th (g9's unmarked first start counts as one of his 4)",
       (B.prior(2027), len(_early)))
    # a grade, recomputed: (his marks + 8 x the prior) / (his starts + 8), every start before the cut
    _cut = D26[4]                                    # a2 starts that day: it must not count
    _mk = [B.marks[("AAA", d)] for d in D24 + D25 + D26 if d < _cut and B.starter.get(("AAA", d)) == "a2"]
    _g = (sum(_mk) + 8.0 * B.prior(2026)) / (len(_mk) + 8.0)
    ck(len(_mk) == 3 and abs(B.grade("a2", _cut, 2026) - _g) < 1e-9,
       "🔴 a QB's grade is (his marks + 8 x the prior) / (his starts + 8), the starts before the cut (3, not "
       "the one on it)", (B.grade("a2", _cut, 2026), _g, len(_mk)))
    _c3 = D26[3]
    _a1 = [d for d in D24 + D25 + D26 if d < _c3 and B.starter.get(("AAA", d)) == "a1"]
    _mk1 = [B.marks[("AAA", d)] for d in _a1 if ("AAA", d) in B.marks]
    ck(("AAA", D24[0]) not in B.marks and len(_a1) == len(_mk1) + 1
       and abs(B.grade("a1", _c3, 2026) - (sum(_mk1) + 8.0 * B.prior(2026)) / (len(_mk1) + 8.0)) < 1e-9,
       "🔴 ...over his MARKED starts: a1's unmarked 2024 opener (no earlier game for the ratings) adds to neither "
       "sum", (len(_a1), len(_mk1)))
    eq(B.grade("zz", _cut, 2026), B.prior(2026), "   a QB with no stored start (or an unknown backup) gets the prior")
    eq(B.grade(None, _cut, 2026), B.prior(2026), "   ...and so does None")
    # the mix: the team's starters' grades over the games the CHAMPION's rating reads (latest/ for
    #    today's model: 2025-2026, never 2024's history games), 0.5 ** (days / 150) from the Monday
    _wk = FM.monday(_cut)
    _w = [(wt(_wk, d), B.grade(B.starter[("AAA", d)], _cut, 2026)) for d in RATED if d < _wk]
    ck(abs(B.mix("AAA", _cut, 2026) - sum(w * g for w, g in _w) / sum(w for w, _x in _w)) < 1e-12,
       "🔴🔴 the QB mix: the games today's model's rating reads (2025-26, not 2024's history), weighted "
       "0.5 ** (days / 150) from the Monday")
    _wc = [(wt(_wk, d), B.grade(B.starter[("CCC", d)], _cut, 2026)) for d in RATED if d < _wk]
    ck(abs(B.mix("CCC", _cut, 2026) - sum(w * g for w, g in _wc) / sum(w for w, _x in _wc)) < 1e-12,
       "   ...a team away half the time too (CCC)")

    # ══════════════════════════════════════════════════════════════════
    section("2. THE EXPECTED STARTER: LAST STARTER, REPLACEMENT, RETURNING STARTER, NO READING")
    # ══════════════════════════════════════════════════════════════════
    eq(B.expected("AAA", D26[2], 2026, set(), _none), ("a1", "last starter"), "no report: the last game's starter")
    eq(B.expected("AAA", D26[3], 2026, {"a1"}, _none), ("a3", "last starter listed out"),
       "🔴🔴 the last starter listed out: the other QB with the most attempts this season (a3, a2 has none yet)")
    eq(B.expected("AAA", D26[3], 2026, {"a1", "a3"}, _none), ("a2", "last starter listed out"),
       "   ...not listed out himself: then last season's (a2)")
    eq(B.expected("AAA", D26[3], 2026, {"a1", "a2", "a3"}, _none), (None, "last starter listed out"),
       "   ...none left: an unknown backup (graded at the prior)")
    eq(B.expected("BBB", D26[3], 2026, {"b1"}, _none), ("b3", "last starter listed out"),
       "🔴 ...a tie in attempts (b2 9, b3 9) goes to the larger player id")
    _was_out = lambda team, day: {"a1"} if day == D25[7] else set()      # noqa: E731
    eq(B.expected("AAA", D25[8], 2025, set(), _was_out), ("a1", "usual starter returns"),
       "🔴 the usual starter, listed out at the fill-in's game and not now: he returns")
    eq(B.expected("AAA", D25[8], 2025, set(), _none), ("a2", "last starter"),
       "   ...without that listing it stays the last starter")
    eq(B.expected("AAA", D25[8], 2025, {"a1"}, _was_out), ("a2", "last starter"),
       "🔴 ...and while he is listed out NOW as well, the fill-in stays")
    eq(B.expected("CCC", D26[3], 2026, {"c2"}, _c_out), ("c1", "usual starter returns"),
       "🔴 ...and when the fill-in (c2) is listed out now too, the usual starter (c1) returns: not c3, who has "
       "more attempts this season")
    eq(B.expected("CCC", D26[3], 2026, {"c2"}, _none), ("c3", "last starter listed out"),
       "   (without that earlier listing it is the replacement by this season's attempts, c3)")
    eq((B.expected("AAA", D25[0], 2025, set(), _none), B.delta("AAA", D25[0], 2025, set(), _none)),
       (("a1", "last starter"), None),
       "🔴🔴 2025 week 1: a last starter (2024's logs), but no game the rating reads yet: no reading")
    eq(B.expected("AAA", D24[0], 2024, set(), _none), (None, "no earlier start"), "no earlier start: no reading")
    eq(B.delta("AAA", D24[0], 2024, set(), _none), None, "   ...and no delta")
    _dl = B.delta("AAA", D26[3], 2026, {"a1", "a3"}, _none)
    ck(_dl is not None and abs(_dl - (B.grade("a2", D26[3], 2026) - B.mix("AAA", D26[3], 2026))) < 1e-12,
       "🔴 the delta is grade(expected starter) minus the rating's QB mix", _dl)

    # ══════════════════════════════════════════════════════════════════
    section("3. 🔴🔴 POINT IN TIME: NOTHING DATED ON OR AFTER THE CUT IS READ")
    # ══════════════════════════════════════════════════════════════════
    _c = D26[3]
    B2 = book(build(os.path.join(TMP, "two"), bump=_c, swap=D26[5]))
    _ask = lambda b: (b.grade("a2", _c, 2026), b.grade("a3", _c, 2026), b.mix("AAA", _c, 2026),  # noqa: E731
                      b.expected("AAA", _c, 2026, {"a1"}, _none), b.delta("AAA", _c, 2026, {"a1"}, _none),
                      b.usual("AAA", _c), b.prior(2026))
    eq(_ask(B2), _ask(B),
       "🔴🔴 other results on and after the cut (10 more points at home) and another starter after it change no "
       "grade, mix, expected starter, delta, usual starter or prior")
    ck(B2.marks[("AAA", _c)] != B.marks[("AAA", _c)],
       "   (and the planted change is real: the cut day's own mark moved)")

    # ══════════════════════════════════════════════════════════════════
    section("4. fb_challengers: rated_games, ATTACH (THE NFL REPORTS, THE COLLEGE REPORTS) AND EXTEND")
    # ══════════════════════════════════════════════════════════════════
    _rg = FC.rated_games("nfl", T1)
    ck(("AAA", D25[0]) in _rg and ("AAA", D24[0]) not in _rg and ("CCC", D25[1]) in _rg,
       "🔴 today's model's rating reads latest/ (2025-26), not the history seasons; both teams of a game")
    _was = FM.CHAMPION["nfl"]
    try:
        FM.CHAMPION["nfl"] = "H"
        ck(("AAA", D24[0]) in FC.rated_games("nfl", T1), "   ...H (or HC) as champion reads the history seasons too")
    finally:
        FM.CHAMPION["nfl"] = _was
    put(os.path.join(T1, "data", "nfl", "latest", "injuries-2026.json.gz"),
        {"season": 2026, "teams": {
            "AAA": {"4": {"players": [
                {"gsis_id": "a1", "full_name": "A1", "position": "QB", "report_status": "Out"},
                {"gsis_id": "o1", "full_name": "O1", "position": "T", "report_status": "Doubtful"},
                {"gsis_id": "o2", "full_name": "O2", "position": "G", "report_status": "Out"},
                {"gsis_id": "o3", "full_name": "O3", "position": "C", "report_status": "Questionable"},
                {"gsis_id": "w1", "full_name": "W1", "position": "WR", "report_status": "Out"},
                {"gsis_id": "k1", "full_name": "K1", "position": "CB", "report_status": "Out"}]}},
            "CCC": {"3": {"players": [{"gsis_id": "c1", "full_name": "C1", "position": "QB", "report_status": "Out"}]},
                    "4": {"players": [{"gsis_id": "c2", "full_name": "C2", "position": "QB",
                                       "report_status": "Doubtful"}]}}}})
    _row = {"id": "g", "lg": "nfl", "season": 2026, "week": 4, "day": D26[3], "home": "AAA", "away": "CCC",
            "final": False, "hs": None, "as": None, "M": -3.0, "T": 44.0, "pml": 0.5,
            "sig": {"neutral": 0.0, "dome": 0.0}}
    _row1 = dict(_row, id="g1", season=2025, week=1, day=D25[0], away="BBB", sig={"neutral": 0.0, "dome": 0.0})
    FC.attach("QB", "nfl", [_row, _row1], T1)
    _hd = B.delta("AAA", D26[3], 2026, {"a1"}, _none)
    _ad = B.delta("CCC", D26[3], 2026, {"c2"}, _c_out)
    ck(abs(_row["sig"]["qb_d"][0] - _hd) < 1e-12 and _hd != B.delta("AAA", D26[3], 2026, set(), _none),
       "🔴 attach reads THIS game's week's report: AAA's a1 listed Out, its delta is the replacement's",
       _row["sig"]["qb_d"])
    ck(abs(_row["sig"]["qb_d"][1] - _ad) < 1e-12 and _ad != B.delta("CCC", D26[3], 2026, {"c2"}, _none),
       "🔴 ...and the earlier game's week's report: c1 was listed out at c2's last start, so c1 returns",
       _row["sig"]["qb_d"])
    eq(_row1["sig"]["qb_d"], (None, None), "a 2025 week-1 row (no game the rating reads yet): no reading")
    eq(FC.reserve_lists(T1), {(2025, "FFF", "4"): ["T1"], (2026, "BBB", "5"): ["B1"], (2026, "DDD", "2"): ["D1"],
                              (2026, "DDD", "6"): ["  d2 "], (2026, "EEE", "3"): ["E1"], (2026, "EEE", "6"): ["E1"],
                              (2026, "EEE", "7"): ["E1"]},
       "🔴 the stored reserve list, by season, team and week; never the inactive list (FFF's F1)")
    _sig = lambda: {"neutral": 0.0, "dome": 0.0}        # noqa: E731
    _r1 = dict(_row, id="r1", week=6, day=D26[5], home="DDD", away="FFF", sig=_sig())
    _r2 = dict(_row, id="r2", week=3, day=D26[2], home="DDD", away="EEE", sig=_sig())
    _r3 = dict(_row, id="r3", week=7, day=D26[6], home="EEE", away="FFF", sig=_sig())
    _r4 = dict(_row, id="r4", week=4, day=D26[3], home="FFF", away="EEE", sig=_sig())
    _r5 = dict(_row, id="r5", week=3, day=D26[2], home="EEE", away="FFF", sig=_sig())
    _r6 = dict(_row, id="r6", week=5, day=D26[4], home="BBB", away="DDD", sig=_sig())
    _r7 = dict(_row, id="r7", season=2025, week=4, day=D25[3], home="FFF", away="EEE", sig=_sig())
    _r8 = dict(_row, id="r8", week=6, day=D26[5], home="EEE", away="DDD", sig=_sig())
    FC.attach("QB", "nfl", [_r1, _r2, _r3, _r4, _r5, _r6, _r7, _r8], T1)
    _d_out = lambda team, day: {"d1"} if (team, day) == ("DDD", D26[1]) else set()      # noqa: E731
    _x1 = B.delta("DDD", D26[5], 2026, {"d2"}, _none)
    ck(B.expected("DDD", D26[5], 2026, {"d2"}, _none) == ("d1", "last starter listed out")
       and abs(_r1["sig"]["qb_d"][0] - _x1) < 1e-12 and _x1 != B.delta("DDD", D26[5], 2026, set(), _none),
       "🔴🔴 an NFL starter on the reserve list (absent from the report) is listed out: d2, so d1 is graded "
       "(\"  d2 \" matched bar case and spacing, on DDD only: AAA's a3 is stored as D2 too)",
       _r1["sig"]["qb_d"])
    _x2 = B.delta("DDD", D26[2], 2026, set(), _d_out)
    ck(B.expected("DDD", D26[2], 2026, set(), _d_out) == ("d1", "usual starter returns")
       and abs(_r2["sig"]["qb_d"][0] - _x2) < 1e-12 and _x2 != B.delta("DDD", D26[2], 2026, set(), _none),
       "🔴 ...and the usual starter, on it at the fill-in's game and off it now, returns (d1)", _r2["sig"]["qb_d"])
    _e_at = lambda team, day: {"e1"} if (team, day) == ("EEE", D26[5]) else set()      # noqa: E731
    _x3 = B.delta("EEE", D26[6], 2026, set(), _e_at)
    ck(B.expected("EEE", D26[6], 2026, set(), _e_at) == ("e1", "usual starter returns")
       and abs(_r3["sig"]["qb_d"][0] - _x3) < 1e-12 and _x3 != B.delta("EEE", D26[6], 2026, {"e1", "e2"}, _e_at)
       and _x3 != B.delta("EEE", D26[6], 2026, set(), _none),
       "🔴🔴 a name two of the team's QBs share (E1: e1 and e2) is not listed now (week 7), while at the fill-in's "
       "week-6 game only e1 had logged as E1 before it: the usual starter returns", _r3["sig"]["qb_d"])
    _x4 = B.delta("FFF", D26[3], 2026, set(), _none)
    ck(abs(_r4["sig"]["qb_d"][0] - _x4) < 1e-12 and _x4 != B.delta("FFF", D26[3], 2026, {"f1"}, _none),
       "🔴 the inactive list is not read (f1 stays the expected starter)", _r4["sig"]["qb_d"])
    _x5 = B.delta("EEE", D26[2], 2026, {"e1"}, _none)
    ck(B.expected("EEE", D26[2], 2026, {"e1"}, _none) == (None, "last starter listed out")
       and abs(_r5["sig"]["qb_d"][0] - _x5) < 1e-12 and _x5 != B.delta("EEE", D26[2], 2026, set(), _none),
       "🔴🔴 point in time: in week 3 only e1 had logged for EEE as \"E1\" (e2 first logs in week 6), so e1 is listed",
       _r5["sig"]["qb_d"])
    _x8 = B.delta("EEE", D26[5], 2026, {"e1"}, _none)
    ck(B.expected("EEE", D26[5], 2026, {"e1"}, _none) == (None, "last starter listed out")
       and abs(_r8["sig"]["qb_d"][0] - _x8) < 1e-12 and _x8 != B.delta("EEE", D26[5], 2026, set(), _none),
       "🔴🔴 ...e2's debut that very day is no earlier log row: \"E1\" is e1 alone, listed out", _r8["sig"]["qb_d"])
    _x6 = B.delta("BBB", D26[4], 2026, set(), _none)
    ck(abs(_r6["sig"]["qb_d"][0] - _x6) < 1e-12 and _x6 != B.delta("BBB", D26[4], 2026, {"b1"}, _none),
       "🔴 a name a QB and a logged linebacker share (B1) is ambiguous: the starter is not listed", _r6["sig"]["qb_d"])
    _x7 = B.delta("FFF", D25[3], 2025, set(), _none)
    ck(B.expected("FFF", D25[3], 2025, set(), _none) == ("t1", "last starter")
       and abs(_r7["sig"]["qb_d"][0] - _x7) < 1e-12 and _x7 != B.delta("FFF", D25[3], 2025, {"t1"}, _none),
       "🔴 a reserve-list name held by a non-QB alone (t1, a TE) is no QB listing", _r7["sig"]["qb_d"])
    FC.attach("QP", "nfl", [_row], T1)
    _tq = FC.team_out(*FC.injury_tables(T1), lambda team, day: None, 2026, "AAA", 4, D26[3])
    eq(_row["sig"]["qp"]["ol"], (2.0, 0.0), "🔴 QP counts the linemen listed Out or Doubtful (not Questionable)")
    ck(_row["sig"]["qp"]["off"] == (_tq[1], 0.0) and _row["sig"]["qp"]["def"] == (_tq[2], 0.0)
       and abs(_tq[1] - 0.8) < 1e-12 and abs(_tq[2] - 0.9) < 1e-12,
       "🔴 ...and IN's offence and defence shares out: w1's 0.8 of the snaps, k1's 0.9 of the defensive snaps",
       _row["sig"]["qp"])
    _x = [0.1, 0.2]

    def close(got, want):
        """§3k's arithmetic, to 1e-12: the code may round in another order (a / 10 - h / 10)."""
        return len(got) == len(want) and all(abs(g - w) < 1e-12 for g, w in zip(got, want))
    h, a = _row["sig"]["qb_d"]
    ck(close(FC.extend("QB", _row, "spread", _x), _x + [(a - h) / 10.0]), "QB on spread: away - home, / 10")
    ck(close(FC.extend("QB", _row, "moneyline", _x), _x + [(a - h) / 10.0]), "   ...and on moneyline")
    ck(close(FC.extend("QB", _row, "total", _x), _x + [(h + a) / 10.0]), "   ...and home + away on totals")
    q = _row["sig"]["qp"]
    ck(close(FC.extend("QP", _row, "spread", _x),
             _x + [(a - h) / 10.0] + [q[k][1] - q[k][0] for k in ("off", "ol", "def")]),
       "QP adds offence, linemen and defence, away - home")
    ck(close(FC.extend("QP", _row, "total", _x),
             _x + [(h + a) / 10.0] + [q[k][0] + q[k][1] for k in ("off", "ol", "def")]),
       "   ...their sums on totals")
    _tr = dict(_row, sig={"qb_d": (1.0, -2.216080535810077)})       # rounds differently in the two orders
    ck((-2.216080535810077 - 1.0) / 10.0 != -2.216080535810077 / 10.0 - 1.0 / 10.0
       and close(FC.extend("QB", _tr, "spread", _x), _x + [(-2.216080535810077 - 1.0) / 10.0])
       and close(FC.extend("QB", _tr, "total", _x), _x + [(1.0 - 2.216080535810077) / 10.0]),
       "   (checked to 1e-12, never bit for bit: a pair whose two roundings differ still passes)")
    eq(FC.extend("QB", _row1, "spread", _x), _x + [0.0], "no reading: an input of 0")
    # college: the 9:00 reports through cfb_injuries (planted), QBs only, Out / Doubtful only
    import cfb_injuries as CI
    TC = os.path.join(TMP, "college")
    for s in DAYS:
        for where, f in (("history" if s == 2024 else "latest", "schedule-%d.json.gz" % s),
                         ("latest", "players-%d.json.gz" % s)):
            os.makedirs(os.path.join(TC, "data", "ncaaf", where), exist_ok=True)
            shutil.copy(os.path.join(T1, "data", "nfl", where, f), os.path.join(TC, "data", "ncaaf", where, f))
    BC = book(TC, "ncaaf")
    _cgid = BC.gid[("CCC", D26[2])]
    _keep = CI.pick_time_outs, CI.Roles, CI.attach

    class _Roles:
        def __init__(self, season, root=None):
            pass

        def match(self, team, player):
            return player.get("pid")
    try:
        _calls = []

        def _record(s, root=None, now=None, at=None):
            _calls.append((now, at))
            return _outs(s)
        _outs = lambda s: {      # noqa: E731
            "cg1": {"AAA": [{"pid": "a1", "status": "Out"}, {"pid": "w9", "status": "Out"}],
                    "CCC": [{"pid": "c2", "status": "Doubtful"}]},
            _cgid: {"CCC": [{"pid": "c1", "status": "Out for Season"}]},
            "cg2": {"BBB": [{"pid": "b1", "status": "Questionable"}]}} if s == 2026 else {}
        CI.pick_time_outs = _record
        CI.Roles = _Roles
        CI.attach = lambda rows, root=None, now=None, shown_at=None: [
            r["sig"].__setitem__("inj", {"qb": (1.0, 0.0), "off": (0.25, 0.0), "def": (0.0, 0.5)}) for r in rows]
        _cr = dict(_row, id="cg1", lg="ncaaf", sig={"neutral": 0.0, "dome": 0.0})
        _cr2 = dict(_row, id="cg2", lg="ncaaf", home="BBB", away="DDD", sig={"neutral": 0.0, "dome": 0.0})
        FC.attach("QBC", "ncaaf", [_cr, _cr2], TC)
        _ca, _cc = BC.delta("AAA", D26[3], 2026, {"a1"}, _none), BC.delta("CCC", D26[3], 2026, {"c2"}, _c_out)
        ck(abs(_cr["sig"]["qb_d"][0] - _ca) < 1e-12 and _ca != BC.delta("AAA", D26[3], 2026, set(), _none),
           "🔴 college reads its game's report through Roles.match: a1 listed Out, his replacement graded",
           _cr["sig"]["qb_d"])
        ck(abs(_cr["sig"]["qb_d"][1] - _cc) < 1e-12 and _cc != BC.delta("CCC", D26[3], 2026, {"c2"}, _none),
           "🔴 ...and the earlier game's report (by its game id): c1 listed out there, so he returns",
           _cr["sig"]["qb_d"])
        ck(_calls and all(c == (None, None) for c in _calls),
           "🔴 college reads its reports at cfb_injuries' 9:00 ET pick time on the game's own day (now None)",
           _calls)
        _cb = BC.delta("BBB", D26[3], 2026, set(), _none)
        ck(abs(_cr2["sig"]["qb_d"][0] - _cb) < 1e-12 and _cb != BC.delta("BBB", D26[3], 2026, {"b1"}, _none),
           "🔴 Questionable is not listed out: b1 stays the expected starter", _cr2["sig"]["qb_d"])
        FC.attach("QPC", "ncaaf", [_cr], TC)
        eq(_cr["sig"]["qp"], {"off": (0.25, 0.0), "def": (0.0, 0.5)}, "QPC reads college's own shares out")
        eq(len(FC.extend("QPC", _cr, "spread", _x)), len(_x) + 3, "   ...QB delta, offence and defence appended")
    finally:
        CI.pick_time_outs, CI.Roles, CI.attach = _keep

    # ══════════════════════════════════════════════════════════════════
    section("5. 🔴🔴 THE DIRECTION RULE: A WINS WHOSE QB WEIGHT POINTS THE WRONG WAY IS NOT YET")
    # ══════════════════════════════════════════════════════════════════
    _frow = dict(_row, sig=dict({k: None for k in ("h2h_m", "form_m", "poss", "out", "h2h_t", "form_t", "def")},
                                neutral=0.0, dome=0.0))         # the champion's own inputs: none read

    class _Fits:
        """A fit per market whose weights are 0 except the QB delta's (the first input after the
        champion's, w[0] being the intercept) and an opposite decoy on the input before it."""

        def __init__(self, w):
            self.w = w

        def model(self, wk, mk):
            n = len(FM.features(_frow, mk))
            return {"w": [0.0] * n + [-self.w[mk], self.w[mk]]}
    _latest = {mk: ("2026-10-05", _frow) for mk in ("spread", "moneyline", "total")}
    _ok = R.direction(_Fits({"spread": -0.3, "moneyline": -0.2, "total": 0.4}), _latest)
    _bad = R.direction(_Fits({"spread": 0.3, "moneyline": -0.2, "total": 0.4}), _latest)
    ck(all(v["ok"] for v in _ok.values()) and {v["weight"] for v in _ok.values()} == {-0.3, -0.2, 0.4},
       "the expected way: negative on spread and moneyline, positive on totals (the QB delta's own weight)", _ok)
    eq(sorted(mk for mk, v in _bad.items() if not v["ok"]), ["spread"], "   ...a positive spread weight is the wrong way")

    # contest() itself: two Mondays priced, the weight the wrong way on the earlier and the right way on
    #    the later; the rule reads the LATER (the latest weekly fit)
    class _Champ:
        def predictions(self, mk):
            return {"g1": (0.5, 1, "2026-10-05", _frow), "g2": (0.5, 0, "2026-10-12", _frow)}

    class _TwoWeeks:
        def predictions(self, mk, keep=None):
            return {"g1": (0.6, 1, "2026-10-05", _frow), "g2": (0.4, 0, "2026-10-12", _frow)}

        def model(self, wk, mk):
            s = R.DIRECTION[mk] * (0.5 if wk == "2026-10-12" else -0.5)
            return {"w": [0.0] * (1 + len(FM.features(_frow, mk))) + [s]}
    _cd = R.contest([], _Champ(), "QB", "2026-10-05", "2026-10-05", fits=_TwoWeeks()).get("direction") or {}
    eq({mk: (v["monday"], v["ok"]) for mk, v in _cd.items()},
       {mk: ("2026-10-12", True) for mk in ("spread", "total", "moneyline")},
       "🔴🔴 contest() hands the rule each market's LATEST Monday's fit (the earlier one pointed the wrong way)")

    def judged(d, name="QB"):
        x = {"name": name, "what": FC.CHALLENGERS[name]["what"], "registered": "2026-11-16", "withdrawn": False,
             "direction": d, "counts": "all",
             "counted": {"predictions": 400, "differing": 400, "mean_d": 0.01, "p": 1e-9, "games": 200,
                         "champion_log_loss": 0.68, "challenger_log_loss": 0.67}}
        return R.verdicts([x])[0]
    eq(judged(_ok)["verdict"], "WINS", "a winning score with the expected direction WINS")
    eq(judged(_cd)["verdict"], "WINS", "   ...and so does one with contest()'s own direction")
    _no = judged(_bad)
    eq((_no["verdict"], "spread" in _no.get("why", "")), ("NOT YET", True),
       "🔴🔴 ...the same score with the QB weight the wrong way is NOT YET, and says which market")
    eq(judged({})["verdict"], "NOT YET", "   ...and so is one with no fitted market at all")
    _other = R.verdicts([{"name": "CL", "registered": "2026-11-02", "withdrawn": False,
                          "counted": {"differing": 400, "mean_d": 0.01, "p": 1e-9}}])[0]
    eq(_other["verdict"], "WINS", "   (the rule is T75's only: another challenger needs no direction)")
    _now = datetime.datetime(2026, 11, 23, 12, 0, tzinfo=UTC)
    _mail = S.refit_summary({"built_at": "2026-11-23T10:00:00Z", "floor": 300, "challengers": [_no]}, "NFL", _now)
    ck("not a win: it beat the current model on the numbers, but its QB number pulls the wrong way in spread" in _mail
       and "not better yet" not in _mail,
       "🔴 the Monday email says why, never \"not better yet\" for a score that beat the model", _mail)

    # ══════════════════════════════════════════════════════════════════
    section("6. THE REGISTRY, THE COUNTS, REGISTRATION AND §3k's NUMBERS")
    # ══════════════════════════════════════════════════════════════════
    eq({n: (FC.CHALLENGERS[n]["league"], FC.CHALLENGERS[n]["markets"], FC.CHALLENGERS[n]["registered_from"],
            FC.CHALLENGERS[n].get("on_merge"), FC.CHALLENGERS[n]["withdrawable"]) for n in FC.T75},
       {"QB": ("nfl", ("spread", "total", "moneyline"), "2026-11-16", True, False),
        "QBC": ("ncaaf", ("spread", "total", "moneyline"), "2026-11-16", True, False),
        "QP": ("nfl", ("spread", "total", "moneyline"), "2026-11-16", True, False),
        "QPC": ("ncaaf", ("spread", "total", "moneyline"), "2026-11-16", True, False)},
       "the four entries: their league, every market, registered from 2026-11-16 on merge, no withdrawal")
    eq({lg: sum(1 for c in FC.CHALLENGERS.values() if c["league"] == lg) for lg in ("nfl", "ncaaf")},
       {"nfl": 15, "ncaaf": 15}, "fifteen challengers a league")
    ck(all(n in FC.APPEND_ONLY for n in FC.T75) and all(n not in R.SCORED_ONLY for n in FC.T75),
       "they only append (APPEND_ONLY) and count every past week (not SCORED_ONLY): §3k")
    ck(all(FC.applies(n, {"lg": FC.CHALLENGERS[n]["league"]}) for n in FC.T75),
       "   ...so they build against any champion")
    eq([R.registration("QB", T1, {"QB": d}) for d in ("2026-11-10", "2026-11-15", "2026-11-16", "2026-11-23")],
       ["2026-11-16", "2026-11-16", "2026-11-23", "2026-11-30"],
       "registration: the first Monday AFTER the merge day, no earlier than 2026-11-16")
    _spec = open(os.path.join(ROOT, "research", "fb_refit_spec.md"), encoding="utf-8").read()
    _3k = _spec[_spec.find("\n## 3k. "):_spec.find("\n## 4. ")]
    ck(_3k.startswith("\n## 3k. T75"), "§3k is in the spec, before §4")
    eq((Q.K, Q.PRIOR_MAX, Q.USUAL_GAMES, Q.HALF_LIFE), (8.0, 3, 8, 150.0),
       "the code's constants are §3k's: 8 starts, 3 or fewer, 8 games, 150 days")
    ck("+ 8 × the prior) / (his marked starts + 8)" in _3k and "3 or fewer prior stored starts" in _3k
       and "adds to neither sum" in _3k and "9:00 ET pick time" in _3k
       and _3k.count("a tie goes to the larger player id, compared as text") == 1
       and "the larger player id, compared as text); none" in _3k
       and "or on the team's reserve list that week" in _3k and "the inactive list is not read" in _3k
       and "exactly one player with a stored log row for the team dated before the game has it" in _3k
       and "and he is a QB" in _3k
       and "after the first stored season of his team's logs" in _3k and "previous 8 games" in _3k
       and "0.5 ^ (days / 150)" in _3k and "the games the champion's own rating reads" in _3k
       and "whether or not L is listed out now" in _3k and "every earlier season" in _3k,
       "   ...as §3k writes them, and its rules")
    _ns = next((ln for ln in _3k.split("\n") if "NEEDS SAM" in ln), "")
    ck("push_branch" in _ns and "(§3j)" not in _ns,
       "§3k credits NEEDS SAM to fb_refit.push_branch's rule (§4), not to §3j, which has no such rule", _ns[:200])
    eq(R.DIRECTION, {"spread": -1, "moneyline": -1, "total": 1}, "the direction rule's signs")
    ck("negative on spread and moneyline" in _3k and "positive on totals" in _3k, "   ...as §3k writes them")
    note("⛔ rule 13: nothing here was fitted on, or compared with, a real game's result; the Monday contest "
         "is the test, and a WINS is only ever a branch for Sam")
finally:
    shutil.rmtree(TMP, ignore_errors=True)
