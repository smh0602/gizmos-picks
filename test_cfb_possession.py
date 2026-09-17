#!/usr/bin/env python3
"""
COLLEGE TIME OF POSSESSION — DERIVED, FREE, AND REFUSED WHEN IT CANNOT BE.

Sam's standing rule: everything we do for CFB we do for NFL and back. The
NFL side reads `drive_time_of_possession` out of the play-by-play. ⛔ CFBD
HAS NO SUCH COLUMN — the 29 `/plays` really returns are measured in
`data/ncaaf/latest/probe-report.json` — so college possession has to be
DERIVED from the game clock, and the derivation has two traps in it.

🔴 TRAP 1: `wallclock` IS REAL-WORLD TIME. It is in the column list and it
looks exactly right. Summing it measures TV timeouts and replay reviews.

🔴 TRAP 2: THE GAME CLOCK COUNTS DOWN WITHIN A PERIOD, so elapsed is
`clock[n] - clock[n+1]` and goes NEGATIVE at every period boundary. A
naive sum produces a plausible wrong number, which is worse than a
missing one.

⚠️ AND COLLEGE OVERTIME HAS NO CLOCK AT ALL — MEASURED, not assumed:
every play in periods 5, 6 and 7 of the real slice below reads `0:00`.

💰 THE HARD CONSTRAINT: a second `/plays` sweep costs +520 CFBD calls a
month against a quota already at 906/1000 (91%) — 1426/1000, 143%, blown.
So possession is derived INSIDE `build_pace`, from rows already in hand,
and section 1 counts the calls to prove it.

📌 THE FIXTURE IS REAL COLLEGE FOOTBALL. `research/cfb_clock_sample_2019.
json.gz` is 56 real 2019 games — 5 of them into overtime, 111 teams, 1,470
drives — taken from `sportsdataverse/cfbfastR-data` and re-keyed onto the
CFBD column names the probe measured. ⛔ The clock values, the drive ids
and their order are the source's, unedited. CFBD itself needs a key this
session does not hold, and inventing a clock sequence would test the
arithmetic against my own expectation of it rather than against football.
"""
import gzip
import json
import os
import sys

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import cfb  # noqa: E402
import nfl  # noqa: E402
import dossier_fb as DF  # noqa: E402


# ══════════════════════════════════════════════════════════════════════
# @vacuity possession must cost ZERO additional CFBD calls
#   file: cfb.py
#   find: top, toprep = possession_from_plays(poss_rows, season, log)
#   with: top, toprep = possession_from_plays(poss_rows + get("/plays", {"year": str(season)}), season, log)
#
# @vacuity no pair may be taken across a period boundary
#   file: cfb.py
#   find: buckets[(gid, int(per_))].append(
#   with: buckets[(gid, 0)].append(
#
# @vacuity overtime is untimed and must be excluded
#   file: cfb.py
#   find: if int(per_) > CFB_REG_PERIODS:
#   with: if False:
#
# @vacuity wallclock is never the source of a possession number
#   file: cfb.py
#   find: c = p.get("clock") or {}
#   with: c = p.get("clock") or {"minutes": len(str(p.get("wallclock") or "")), "seconds": 0}
#
# @vacuity both leagues emit the same per-team shape
#   file: cfb.py
#   find: teams[t] = {"drives": int(n),
#   with: teams[t] = {"drive_count": int(n),
#
# @vacuity a season that cannot be covered writes no artifact
#   file: cfb.py
#   find: if len(agg) < CFB_TOP_MIN_TEAMS:
#   with: if False:
# ══════════════════════════════════════════════════════════════════════

_SAMPLE = json.load(gzip.open(
    os.path.join(ROOT, "research", "cfb_clock_sample_2019.json.gz"), "rt"))
PLAYS = _SAMPLE["plays"]
_QUIET = lambda *a, **k: None          # noqa: E731


section("0. ⚠️ THE FIXTURE IS REAL, AND CARRIES WHAT THE PROBE MEASURED")
_PROBE = json.load(open(
    os.path.join(ROOT, "data/ncaaf/latest/probe-report.json"), encoding="utf-8"))
_COLS = set(_PROBE["columns_by_endpoint"]["plays"])
ck(len(_COLS) >= 25,
   "⚠️ the real /plays column list is read from the probe (%d columns)"
   % len(_COLS),
   "⛔ every claim below about a column name is measured against this, "
   "not against a name somebody remembered")
_used = {"gameId", "period", "playNumber", "offense", "driveId",
         "clock", "minutes", "seconds"}
ck(_used <= _COLS,
   "🔴 every field the derivation reads is one CFBD really returns",
   "⛔ a derivation built on a column that does not exist passes on a "
   "fixture and dies in production. Missing: %s" % sorted(_used - _COLS))
ck("wallclock" in _COLS,
   "⚠️ ...and `wallclock` really is there to be reached for",
   "🔴 the trap is only a trap because the field exists and looks right")
ck(_SAMPLE["overtime_games"] >= 3 and _SAMPLE["games"] >= 40,
   "⚠️ %d real games, %d into OVERTIME, %d teams, %d drives"
   % (_SAMPLE["games"], _SAMPLE["overtime_games"], _SAMPLE["teams"],
      _SAMPLE["drives"]),
   "⛔ without real overtime and real period boundaries this file would "
   "be testing arithmetic against my own expectation of it")
_ot = [p for p in PLAYS if (p.get("period") or 0) > cfb.CFB_REG_PERIODS]
ck(_ot and all((p.get("minutes"), p.get("seconds")) == (0, 0) for p in _ot),
   "🔴🔴 MEASURED: all %d overtime plays read 0:00 — college OT is UNTIMED"
   % len(_ot),
   "⛔ THIS IS WHY OT IS EXCLUDED, and it is a fact about the sport read "
   "off real data, not a rule I assumed")


section("1. 💰 ZERO ADDITIONAL CFBD CALLS — COUNTED, NOT ASSERTED")
# ⛔ A second /plays sweep is +520 calls a month on a quota at 91%.
_calls = []


def _fake_get(path, params=None, **kw):
    _calls.append((path, dict(params or {})))
    wk = int((params or {}).get("week") or 0)
    if (params or {}).get("seasonType") != "regular" or wk > 2:
        return []
    half = len(PLAYS) // 2
    return PLAYS[:half] if wk == 1 else PLAYS[half:]


_real = cfb.get
try:
    cfb.get = _fake_get
    _pace, _tgt, (_top, _rep) = cfb.build_pace(2019, log=_QUIET)
finally:
    cfb.get = _real
_plays_calls = [c for c in _calls if c[0] == "/plays"]
ck(len(_plays_calls) >= 4,
   "⚠️ the sweep really ran (%d /plays call(s))" % len(_plays_calls),
   "⛔ zero calls would make the count below vacuous (rule 67)")
ck(_top is not None,
   "⚠️ ...and possession really came out of it",
   "⛔ a derivation that produced nothing would spend nothing too, and "
   "prove nothing. rep=%s" % {k: _rep.get(k) for k in ("teams", "error")})
ck(len(_calls) == _pace["cfbd_calls"],
   "🔴🔴 POSSESSION COSTS NOTHING — every CFBD call is one `build_pace` "
   "already made (%d of %d)" % (_pace["cfbd_calls"], len(_calls)),
   "💰 +520 calls a month would take the schedule from 906/1000 (91 pct) "
   "to 1426/1000 (143 pct). ⛔ QUOTA BLOWN. Calls made: %s"
   % [c[1] for c in _calls][:8])
ck(_rep.get("cfbd_calls_for_possession") == 0,
   "   ...and the probe records the spend as 0, on disk",
   "a number nobody can re-read is a number nobody can check")
note("   pace spent %d call(s); possession added %d"
     % (_pace["cfbd_calls"], len(_calls) - _pace["cfbd_calls"]))


section("2. 🔴 THE PERIOD BOUNDARY AND OVERTIME PRODUCE NO PHANTOM TIME")
_pay, _r = cfb.possession_from_plays(PLAYS, 2019, log=_QUIET)
ck(_pay is not None, "⚠️ the real slice derives a table", "rep=%s" % _r)
ck(_r["pairs"] > 5000,
   "⚠️ ...over %d in-period play pairs" % _r["pairs"],
   "⛔ a handful of pairs would make the rate below meaningless")
ck(_r["negative"] * 100.0 / max(1, _r["pairs"]) < 1.0,
   "🔴🔴 %d of %d pairs RAN BACKWARDS (%.2f%%) — the clock counts DOWN, "
   "and no pair crosses a period"
   % (_r["negative"], _r["pairs"], 100.0 * _r["negative"] / _r["pairs"]),
   "⛔ bucketing by GAME instead of by (GAME, PERIOD) books a whole "
   "period of phantom time at every boundary, and the number that comes "
   "out still looks like a number")
ck(_r["buckets"] >= _r["games"] * cfb.CFB_REG_PERIODS * 0.9,
   "🔴🔴 THE PAIRING RAN INSIDE %d (GAME, PERIOD) BUCKETS, NOT %d GAMES"
   % (_r["buckets"], _r["games"]),
   "⛔ ASKED STRUCTURALLY, because the anomaly rate barely moves: a "
   "period boundary is 3 pairs in ~175, so dropping the period from the "
   "key shifts it by a point or two and can sit under any bar you pick. "
   "The bucket count cannot be wrong quietly.")
ck(_r["overtime_plays_seen"] > 0,
   "🔴 %d overtime plays were SEEN and EXCLUDED" % _r["overtime_plays_seen"],
   "⛔ college OT is untimed — every clock in it reads 0:00, so diffing "
   "across the 4→5 boundary books a phantom period")
_max_game_secs = cfb.CFB_REG_PERIODS * cfb.CFB_PERIOD_SECS
ck(0 < _r["seconds_per_game"] <= _max_game_secs * 1.05,
   "🔴🔴 TWO TEAMS SHARE ONE PERIOD CLOCK (%.0fs per game against %ds)"
   % (_r["seconds_per_game"], _max_game_secs),
   "⛔ THIS IS WHAT CATCHES A CROSS-PERIOD SUM. Per-drive means stay "
   "plausible under it; the per-game total does not.")
# ⚠️ READ DEFENSIVELY. A refusal above leaves `_pay` None, and a
#    TypeError here would cost every check in the three sections below.
_spd = ([t["seconds_per_drive"] for t in (_pay or {}).get("teams", {}).values()]
        or [0])
ck(all(40 <= v <= 400 for v in _spd),
   "🔴 ...and a drive lasts a plausible number of seconds (%d-%d)"
   % (min(_spd), max(_spd)),
   "⛔ `drives` must be a COUNT OF DRIVES. A snap count wearing that name "
   "reads ~15s and would make both leagues' section 6 look alike while "
   "meaning different things. Got %s" % sorted(_spd)[:5])
note("   %d team(s), %d drive(s), %.1fs per game, %.3f%% anomalies, "
     "%d bucket(s)" % (_r["teams"], _r["drives"], _r["seconds_per_game"],
                       _r["anomaly_pct"], _r["buckets"]))


section("3. ⛔ `wallclock` IS NOT THE SOURCE — ASKED TWO WAYS")
# 🔴 THE BEHAVIOURAL ONE FIRST: strip the field the trap lives in and the
#    answer must not move by a single second.
_stripped = [{k: v for k, v in p.items() if k != "wallclock"} for p in PLAYS]
_pay2, _r2 = cfb.possession_from_plays(_stripped, 2019, log=_QUIET)
ck(any("wallclock" in p for p in PLAYS),
   "⚠️ the fixture really carries `wallclock` to be reached for (%d rows)"
   % sum(1 for p in PLAYS if p.get("wallclock")),
   "⛔ stripping a field nothing has proves nothing (rule 67)")
ck(_pay2 == _pay,
   "🔴🔴 REMOVING `wallclock` CHANGES NOTHING — it is real-world time, "
   "not game time",
   "⛔ summing it measures TV timeouts and replay reviews. It is the "
   "field that looks right and is not.")
# ⛔ AND THE SOURCE ONE, ASKED OF THE SYNTAX TREE, NOT OF THE TEXT.
#    A substring search fails on the derivation's own docstring and on
#    the sentence in the payload that tells a reader the field is not
#    used — rule 249, a check that trips over its own explanation. So the
#    question is narrower and exact: does any node READ the field?
import ast  # noqa: E402

_SRC = open(os.path.join(ROOT, "cfb.py"), encoding="utf-8").read()
_i = _SRC.index("def _clock_secs(")
_deriv = _SRC[_i:_SRC.index("\ndef build_pace(", _i)]


def _reads(src, field):
    """Lines where `src` actually READS `field` — `x.get("f")` or `x["f"]`.

    ⛔ A mention is not a read. A name in a comment, a docstring or a
    list of fields this deliberately does NOT use is prose.
    """
    out = []
    for node in ast.walk(ast.parse(src)):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get" and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == field):
            out.append(getattr(node, "lineno", 0))
        if (isinstance(node, ast.Subscript)
                and isinstance(node.slice, ast.Constant)
                and node.slice.value == field):
            out.append(getattr(node, "lineno", 0))
    return sorted(set(out))


# ⚠️ THE DETECTOR IS PROVEN TO BITE BEFORE IT IS BELIEVED. A reader that
#    finds nothing would pass on any source at all (rule 67).
ck(_reads('x = p.get("wallclock")\ny = q["wallclock"]\n', "wallclock")
   == [1, 2],
   "⚠️ the reader really does find a read, both ways it can be written",
   "⛔ otherwise the claim below is a search that matches nothing")
ck(_reads(_deriv, "clock") or _reads(_deriv, "minutes"),
   "⚠️ ...and it finds the fields the derivation DOES read",
   "⛔ a reader blind to every field would also be blind to wallclock")
ck(not _reads(_deriv, "wallclock"),
   "🔴 ...and the derivation READS `wallclock` on no line at all",
   "⛔ it names the field twice in prose, on purpose — that is not a "
   "read. Reads found at line(s): %s" % _reads(_deriv, "wallclock"))


section("4. ✅ BOTH LEAGUES' SECTION 6 READS ONE SHAPE AND ONE UNIT")
_N = json.load(gzip.open(os.path.join(
    ROOT, "research", "pbp_possession_sample_2025.json.gz"), "rt"))
_npay, _nrep = nfl.possession_from_rows(_N["rows"], 2025, _QUIET)
ck(_npay is not None and _pay is not None,
   "⚠️ both leagues produced a table to compare",
   "⛔ comparing one table against nothing is rule 67")
# ⚠️ AND READ DEFENSIVELY FROM HERE DOWN. If either league refused above,
#    the comparisons must go RED and say so — never die and take the two
#    sections below with them.
_npay = _npay or {"teams": {}}
_pay = _pay or {"teams": {}}
_TOP = {"season", "kind", "unit", "column", "note", "drives", "teams"}
ck(_TOP <= set(_npay) and _TOP <= set(_pay),
   "🔴 the same top-level keys in both",
   "nfl missing %s ; cfb missing %s"
   % (sorted(_TOP - set(_npay)), sorted(_TOP - set(_pay))))
ck(_npay.get("unit") == _pay.get("unit") == "seconds",
   "🔴🔴 ONE UNIT: seconds, declared on both",
   "⛔ a page reading one league's minutes as the other's seconds is a "
   "60x error that renders. Got %r / %r"
   % (_npay.get("unit"), _pay.get("unit")))
_nk = {frozenset(v) for v in _npay["teams"].values()}
_ck_ = {frozenset(v) for v in _pay["teams"].values()}
ck(_nk == _ck_ and len(_nk) == 1,
   "🔴 ...and one per-team shape: %s" % sorted(next(iter(_nk))),
   "nfl %s ; cfb %s" % ([sorted(x) for x in _nk], [sorted(x) for x in _ck_]))
_bad = [(t, k, v) for pay in (_npay, _pay)
        for t, d in pay["teams"].items() for k, v in d.items()
        if not isinstance(v, int) or isinstance(v, bool)]
ck(not _bad,
   "🔴🔴 EVERY VALUE IS AN INT IN BOTH — NO `M:SS`, NO `15:00`, NO STRING",
   "⛔ `\"7:42\" + \"3:10\"` does not raise, it produces `\"7:423:10\"`. "
   "Offenders: %s" % _bad[:4])
# ✅ AND THE RENDERER IS DRIVEN ON THE COLLEGE ARTIFACT, not just on the
#    NFL one it was written against.
import shutil  # noqa: E402
import tempfile  # noqa: E402

_d = tempfile.mkdtemp(prefix="cfbtop-")
os.makedirs(os.path.join(_d, "latest"))
with gzip.open(os.path.join(_d, "latest", "top-2019.json.gz"), "wt") as fh:
    json.dump(_pay, fh)
_t0, _t1 = (sorted(_pay["teams"]) + ["_a", "_b"])[:2]
_s6 = DF.s_possession(_t0, _t1, 2019, data=_d)
ck(_s6["state"] == "OK" and _t0 in (_s6.get("by_team") or {}),
   "🔴🔴 SECTION 6 READS THE COLLEGE ARTIFACT WITH NO CHANGE TO IT",
   "⛔ one shape is only one shape if the reader agrees. Got %s"
   % str(_s6)[:200])
ck(_s6.get("basis") == "DESCRIPTIVE",
   "   ...and it is labelled DESCRIPTIVE, rule 55",
   "⛔ possession is not a model output and must never read as one")
shutil.rmtree(_d, ignore_errors=True)


section("5. ⛔ UNUSABLE CLOCK DATA WRITES NO ARTIFACT AT ALL")
# 🔴 A PARTIAL POSSESSION TABLE IS MISSINGNESS CLUSTERED BY TEAM — real
#    numbers for some teams, silence for the rest. That is the shape that
#    killed CFB targets, and it is worse than having nothing.
_noclock = [{k: v for k, v in p.items()
             if k not in ("clock", "minutes", "seconds")} for p in PLAYS]
_p3, _r3 = cfb.possession_from_plays(_noclock, 2019, log=_QUIET)
ck(_p3 is None,
   "🔴 a season with NO CLOCK FIELDS writes NOTHING",
   "⛔ rather than a table nobody can trust. Got %s" % str(_p3)[:120])
ck("usable game clock" in (_r3.get("error") or ""),
   "   ...and the probe says which fields were missing", str(_r3)[:200])
_two = sorted({p["offense"] for p in PLAYS if p["offense"]})[:2]
_few = [p for p in PLAYS if p.get("offense") in _two]
_p4, _r4 = cfb.possession_from_plays(_few, 2019, log=_QUIET)
ck(_p4 is None,
   "🔴🔴 ...AND A TWO-TEAM TABLE IS REFUSED TOO",
   "⛔ THE PARTIAL CASE IS THE DANGEROUS ONE — it looks like data. Got %s"
   % str(_p4)[:120])
ck("writing NOTHING" in (_r4.get("error") or ""),
   "   ...saying it chose to write nothing", str(_r4.get("error"))[:160])
# ⛔ AND A CLOCK OUTSIDE ITS OWN DOMAIN IS FABRICATED DATA, not something
#    to round. Same rule as `outs_of()` and an inningsPitched `.3`.
_wrecked = [dict(p, clock=None, minutes=99, seconds=99) for p in PLAYS]
_p5, _r5 = cfb.possession_from_plays(_wrecked, 2019, log=_QUIET)
ck(_p5 is None,
   "🔴 a clock outside 0:00–15:59 is refused, not rounded",
   "⛔ `outs_of()` raises on an inningsPitched `.3` for the same reason. "
   "Got %s" % str(_p5)[:120])
ck(_r5.get("no_clock", 0) > 0,
   "   ...and the probe counts the rows it could not read (%s)"
   % _r5.get("no_clock"),
   "a refusal that does not say how much it refused is not a diagnosis")

# ⛔ THE PROBE IS WRITTEN EITHER WAY. A diagnosis that exists only in an
#    Actions log is a diagnosis you do not have.
ck('f"top-probe-{season}.json", toprep' in _SRC
   and 'f"top-{season}.json.gz", top' in _SRC,
   "🔴 the collector writes the PROBE always and the TABLE only if usable",
   "⛔ otherwise section 6 goes UNAVAILABLE with no reason attached")
note("📌 `build_pace` is reached by the CFB rebuild, which a cron routes "
     "to — `test_accumulators.py` is what holds that, on the class.")
