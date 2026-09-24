#!/usr/bin/env python3
"""test_signals_67.py — signal 6 per game and signal 7 players ruled out.

`[Sam, 2026-09-23]` "Build these football data fixes. Each gets a test that
goes red under its own mutation." Each block below names its fix, and the
declarations are what `vacuity.py` drives:

# @vacuity signal 6: a game ON the kickoff date is never "before kickoff"
#   file: possession.py
#   find:         if str(d)[:10] >= k:
#   with:         if str(d)[:10] > k:
#
# @vacuity signal 6: the dossier reads the pre-kickoff share, not the season table
#   file: dossier_fb.py
#   find:         if games is not None and kickoff:
#   with:         if False:
#
# @vacuity signal 6: an NFL game with no play-by-play date is dated from the schedule
#   file: nfl.py
#   find:             dates[_g] = _sched[str(_g)]
#   with:             pass
#
# @vacuity signal 7: questionable is NOT ruled out
#   file: nfl.py
#   find:         if INJ_RANK.get(st, 1 if st else 0) < 2:
#   with:         if INJ_RANK.get(st, 1 if st else 0) < 1:
#
# @vacuity signal 7: the dossier reads players RULED OUT, not stat-row flags
#   file: dossier_fb.py
#   find:     tout = j.get("team_out")
#   with:     tout = {}
#
# @vacuity every CFBD back-fill call is priced first, and a refusal fetches nothing
#   file: cfb.py
#   find:     if not price["allowed"]:
#   with:     if False:

# @vacuity a past season whose schedule lacks a field the builder now writes is rebuilt
#   file: nfl.py
#   find:     missing = sorted(k for k in want if games and any(k not in g for g in games))
#   with:     missing = []
"""
import gzip
import json
import os
import shutil
import sys
import tempfile

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import possession as P  # noqa: E402
import nfl  # noqa: E402
import cfb  # noqa: E402
import cfbd_budget as B  # noqa: E402
import dossier_fb as D  # noqa: E402
import freshness as F  # noqa: E402

Q = lambda *a, **k: None          # noqa: E731

# ══════════════════════════════════════════════════════════════════════
# 1. SIGNAL 6 — "before kickoff" means STRICTLY EARLIER GAMES
# ══════════════════════════════════════════════════════════════════════
G = {
    "g1": {"date": "2025-09-07", "withheld": False,
           "teams": {"X": {"share": 0.60}, "Y": {"share": 0.40}}},
    "g2": {"date": "2025-09-14", "withheld": False,
           "teams": {"X": {"share": 0.40}, "Z": {"share": 0.60}}},
    "g3": {"date": "2025-09-21", "withheld": False,      # the game itself
           "teams": {"X": {"share": 0.95}, "Y": {"share": 0.05}}},
    "g4": {"date": "2025-09-28", "withheld": False,      # after it
           "teams": {"X": {"share": 0.99}, "Z": {"share": 0.01}}},
    "g5": {"date": "2025-09-10", "withheld": True,
           "teams": {"X": {"share": None}, "W": {"share": None}}},
    "g6": {"date": None, "withheld": False,
           "teams": {"X": {"share": 0.10}, "V": {"share": 0.90}}},
}
b = P.share_before(G, "X", "2025-09-21")
ck(b["share"] == 0.5 and b["games"] == 2,
   "🔴🔴 signal 6 before kickoff uses ONLY the team's earlier games",
   "⛔ Sam: 'built only from that team's earlier games'. The game on the "
   "kickoff date (0.95) and the one after (0.99) must not count. got %r" % b)
ck(b["withheld"] == 1 and b["undated"] == 1,
   "   ⚠️ ...a withheld game and an undated game are counted as skipped, "
   "never averaged in", "got %r" % b)
ck(P.share_before(G, "X", "2025-09-07")["share"] is None
   and P.share_before(G, "X", None)["share"] is None,
   "   ⛔ ...and with nothing earlier (or no kickoff) the answer is None, "
   "never a number that saw the future")

# ── driven on the REAL 2025 NFL season (committed drive-level sample) ──
_s = json.load(gzip.open(os.path.join(ROOT, "research",
                                      "pbp_possession_sample_2025.json.gz"), "rt"))
_pay, _rep = nfl.possession_from_rows(_s["rows"], 2025, log=Q)
_g = (_pay or {}).get("games") or {}
ck(_pay and len(_g) == 285,
   "🔴 NFL 2025: every game's per-team share is stored (%d of 285)" % len(_g),
   "⛔ one row per game already played. rep=%r" % {k: _rep.get(k) for k in
                                                    ("usable", "error", "games_stored")})
ck(_rep.get("games_undated") == 0,
   "   ⚠️ ...and every one is DATED (the sample has no `game_date`, so this "
   "proves the schedule fallback)", "undated=%r" % _rep.get("games_undated"))
_off = [t for t, v in (_pay or {}).get("teams", {}).items()
        if abs(v["share"] - round(sum(x["teams"][t]["share"] for x in _g.values()
                                      if t in x["teams"] and not x["withheld"])
                                  / v["games"], 4)) > 1e-4]
ck(_pay and not _off,
   "   🔴 ...and each team's season share IS the mean of its per-game rows",
   "⛔ one formula, two views — they cannot disagree (rule 66). off: %s" % _off)

# ── college: the same shape through the same formula ──────────────────
_c = json.load(gzip.open(os.path.join(ROOT, "research",
                                      "cfb_clock_sample_2019.json.gz"), "rt"))
_ids = sorted({str(p["gameId"]) for p in _c["plays"]})
_cpay, _crep = cfb.possession_from_plays(
    _c["plays"], 2019, log=Q, dates={i: "2019-09-%02d" % (1 + n % 28)
                                     for n, i in enumerate(_ids)})
_cg = (_cpay or {}).get("games") or {}
ck(_cpay and _cg and _crep.get("games_undated") == 0
   and sum(1 for x in _cg.values() if not x["withheld"]) == _crep.get("games_used"),
   "🔴 college stores the same per-game shape, and its kept games are "
   "exactly the table's (%d kept of %d)" % (
       sum(1 for x in _cg.values() if not x["withheld"]), len(_cg)),
   "⛔ NFL and college must be built the same (Sam's rule 6). rep=%r"
   % {k: _crep.get(k) for k in ("games_used", "games_withheld", "games_undated")})

# ── the dossier reads the pre-kickoff number ───────────────────────────
_d = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(_d, "latest"))
    with gzip.open(os.path.join(_d, "latest", "top-2025.json.gz"), "wt",
                   encoding="utf-8") as fh:
        json.dump({"teams": {"X": {"share": 0.9, "games": 9},
                             "Y": {"share": 0.1, "games": 9}},
                   "games": G}, fh)
    _sec = D.s_possession("X", "Y", 2025, data=_d, kickoff="2025-09-21")
    ck((_sec.get("by_team") or {}).get("X", {}).get("share") == 0.5,
       "🔴🔴 the dossier's §6 is the pre-kickoff share, not the season table",
       "⛔ the season table (0.9) includes games after kickoff. got %r"
       % (_sec.get("by_team") or {}).get("X"))
finally:
    shutil.rmtree(_d, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
# 2. SIGNAL 7 — players RULED OUT, never "questionable and played"
# ══════════════════════════════════════════════════════════════════════
INJ = [{"gsis_id": "a", "week": 3, "team": "PHI", "full_name": "A Out", "report_status": "Out"},
       {"gsis_id": "b", "week": 3, "team": "PHI", "full_name": "B Quest", "report_status": "Questionable"},
       {"gsis_id": "c", "week": 3, "team": "PHI", "full_name": "C Doubt", "report_status": "Doubtful"}]
ROS = [{"gsis_id": "a", "week": 3, "team": "PHI", "full_name": "A Out", "status": "INA"},
       {"gsis_id": "d", "week": 3, "team": "PHI", "full_name": "D Reserve", "status": "RES"},
       {"gsis_id": "e", "week": 3, "team": "PHI", "full_name": "E Active", "status": "ACT"}]
_o, _r = nfl.team_out_from_rows(INJ, ROS)
_cell = ((_o or {}).get("PHI") or {}).get("3") or {}
_names = [p["name"] for p in _cell.get("players", [])]
ck(_names == ["A Out", "C Doubt", "D Reserve"],
   "🔴🔴 out, doubtful, IR/reserve and inactive count; questionable and "
   "active do not", "⛔ Sam: 'Fix the bug where signal 7 counts "
   "questionable and played.' got %r" % _names)
ck(_cell.get("out") == 3 and _cell.get("injury_report") == 2
   and _cell.get("roster_status") == 2,
   "   ⚠️ ...a player named by BOTH files counts once, and says which "
   "files named him", "got %r" % {k: _cell.get(k) for k in
                                  ("out", "injury_report", "roster_status")})
_o2, _r2 = nfl.team_out_from_rows(INJ, [dict(x, status="ACT") for x in ROS])
ck(_o2 is None and "never matches" in (_r2.get("error") or ""),
   "   ⛔ ...and roster codes that never match REFUSE, never write zeros",
   "🔴 the trench-column failure shipped as constant zeros once. got %r" % _r2)

# ── the dossier shows who is out, and college says it is NFL-only ──────
_players = {2025: {"players": {"q": {"name": "B Quest", "g": [
    {"team": "PHI", "week": 3, "inj": 1}]}},
    "team_out": _o, "team_out_report": _r}}
_s7 = D.s_personnel(["PHI"], _players, 2025, None, 4, "nfl")
_v = (_s7.get("by_team") or {}).get("PHI") or {}
ck(_s7.get("state") == "OK" and _v.get("week") == 3
   and _v.get("players") == ["A Out", "C Doubt", "D Reserve"]
   and _s7.get("flagged") == 3,
   "🔴🔴 the page's §7 lists the players ruled out for the latest week",
   "⛔ never the questionable player who played ('B Quest'). got %r" % _v)
_c7 = D.s_personnel(["Georgia"], {2025: {"players": {}}}, 2025, None, 4, "ncaaf")
ck(_c7.get("state") == "UNAVAILABLE" and "NFL games only" in (_c7.get("why") or ""),
   "🔴 college §7 says in words that it covers NFL games only",
   "⛔ Sam: 'Otherwise signal 7 is NFL-only, and the page says so.' got %r"
   % _c7.get("why"))
_page = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
ck("ruled out for week" in _page and "li('Players carrying a flag'" not in _page,
   "   ⚠️ ...and the page draws the new §7, not the old flag count")

# ══════════════════════════════════════════════════════════════════════
# 3. HISTORY IS 2025 AND 2026, AND A GAP IS DECIDED BY THE PROBES
# ══════════════════════════════════════════════════════════════════════
ck(F.FOOTBALL_HISTORY == (2025, 2026),
   "🔴 football history is 2025 and 2026 only",
   "⛔ Sam: 'History is 2025 and 2026 only. Do not add 2024.'")


def _tree(files):
    d = tempfile.mkdtemp()
    for name, obj in files.items():
        p = os.path.join(d, name)
        if name.endswith(".gz"):
            with gzip.open(p, "wt", encoding="utf-8") as fh:
                json.dump(obj, fh)
        else:
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
    return d


# ✅ A COMPLETE stored schedule carries every key the builder emits today
#    (read off the builder, not listed here). One game is enough.
_sched_ok = {"games": [{k: None for k in nfl.schedule_keys()}]}
_sched_old = {"games": [{k: None for k in nfl.schedule_keys() if k != "closing_over_odds"}]}
_cases = [
    ({}, True, "nothing stored"),
    ({"top-probe-2025.json": {}, "top-2025.json.gz": {"teams": {}},
      "players-2025.json.gz": {"team_out_report": {}}}, True, "table predates per-game"),
    ({"top-probe-2025.json": {}, "top-2025.json.gz": {"games": {}},
      "players-2025.json.gz": {}}, True, "players predate the out count"),
    ({"top-probe-2025.json": {"error": "refused"},
      "players-2025.json.gz": {"team_out_report": {}},
      "schedule-2025.json.gz": _sched_ok}, False, "builder REFUSED"),
    ({"top-probe-2025.json": {}, "top-2025.json.gz": {"games": {}},
      "players-2025.json.gz": {"team_out_report": {}},
      "schedule-2025.json.gz": _sched_ok}, False, "complete"),
    # 🔴 a stored schedule missing a field the builder now writes (the
    #    closing prices, 2026-09-24) is rebuilt — or 2025 never gets it
    ({"top-probe-2025.json": {}, "top-2025.json.gz": {"games": {}},
      "players-2025.json.gz": {"team_out_report": {}},
      "schedule-2025.json.gz": _sched_old}, True, "schedule predates a builder field"),
    ({"top-probe-2025.json": {}, "top-2025.json.gz": {"games": {}},
      "players-2025.json.gz": {"team_out_report": {}}}, True, "no stored schedule"),
]
_wrong = []
for files, want, label in _cases:
    _t = _tree(files)
    try:
        if bool(nfl.history_gap(_t, 2025)) != want:
            _wrong.append(label)
    finally:
        shutil.rmtree(_t, ignore_errors=True)
ck(not _wrong,
   "🔴 NFL back-fills a history season exactly while it is missing a signal",
   "⛔ and NOT when the builder refused — re-downloading to be refused "
   "again is the retry storm nfl-logs backs off from. wrong: %s" % _wrong)

# ══════════════════════════════════════════════════════════════════════
# 4. EVERY CFBD BACK-FILL CALL IS PRICED BEFORE IT IS MADE
# ══════════════════════════════════════════════════════════════════════
ck(B.plays_sweep_max() == 32,
   "💰 the sweep's price ceiling is read off build_pace's own loop (32)",
   "⛔ 2 season types x range(1, 17), no early stop assumed. got %r"
   % B.plays_sweep_max())
_old_out, _old_get, _old_bp = cfb.OUT, cfb.get, cfb.build_pace
_calls = []


def _no_call(*a, **k):
    _calls.append(a)
    raise AssertionError("a CFBD call was made")


try:
    for remaining, want_allowed in ((None, False), (100, False), (5000, True)):
        _t = tempfile.mkdtemp()
        cfb.OUT = _t
        if remaining is not None:
            with open(os.path.join(_t, "cfbd-quota.json"), "w") as fh:
                json.dump({"quota": {"headers": {"X-CallLimit-Remaining": str(remaining)}}}, fh)
        _calls.clear()
        cfb.get = _no_call
        cfb.build_pace = (lambda season, log=None:
                          (None, None, ({"teams": {}, "games": {}}, {"usable": True})))
        res = cfb.backfill_possession(2025, log=Q)
        probe = os.path.exists(os.path.join(_t, "top-probe-2025.json"))
        if want_allowed:
            ck(res.get("written") and probe and res["price"]["allowed"],
               "✅ with room to spare the back-fill is priced, ALLOWED and writes",
               "got %r" % res)
        else:
            ck("refused" in res and not _calls and not probe,
               "🔴🔴 %s -> REFUSED before any call, and nothing written"
               % ("no quota reading" if remaining is None else
                  "%d remaining against 32 + a week reserved" % remaining),
               "⛔ Sam: 'No paid tiers and no new spend. price every CFBD call "
               "before it is made.' got %r calls=%d probe=%s"
               % (res, len(_calls), probe))
        shutil.rmtree(_t, ignore_errors=True)
finally:
    cfb.OUT, cfb.get, cfb.build_pace = _old_out, _old_get, _old_bp

note("⚠️ WHAT THIS DOES NOT PROVE: that nflverse's live roster file uses "
     "`INA`/`RES`. Its dictionary does not list the codes. The builder "
     "records every code it sees and refuses to write zeros if neither "
     "appears, so a wrong guess shows up as a refusal with the real codes "
     "beside it, never as a quiet column of zeros.")
