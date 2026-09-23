#!/usr/bin/env python3
"""
POSSESSION IS A SHARE. RAW SECONDS ARE BIASED BY HOW MUCH OF THE CLOCK
THE DERIVATION HAPPENED TO SEE.

🔴🔴 THE DEFECT, MEASURED 2026-09-17 over the WHOLE 2019 college season
(887 games) and the WHOLE 2025 NFL season (285 games). The first CFB
builder emitted raw derived seconds per team. ⛔ Raw seconds are not
comparable between games, because the derivation observes a different
FRACTION of each game's clock:

    CFB clock coverage   min 0.30  p10 0.68  median 0.87  max 1.01
    NFL clock coverage   min 0.91  p10 1.00  median 1.00  max 1.19

⛔ IT DOES NOT ADD NOISE, IT INVERTS RANKINGS. Nicholls read 21:00 in raw
seconds — bottom of the board — against a real share of 38:33, near the
top. 202 of 217 college teams moved by more than a minute; r between the
two quantities is +0.6426, nowhere near interchangeable.

✅ NFL IS THE CONTROL AND IT PASSES THE SAME BAR: max |raw − share| 36s,
r +0.9876. ⚠️ So this is not a claim that raw seconds are always wrong —
it is a claim that they are only right when coverage is near-total, which
is exactly what cannot be assumed of a DERIVED clock.

📌 WHAT THIS FILE OWNS: `possession.py`, the one implementation of the
coverage and share maths that both leagues call. `test_cfb_possession.py`
owns the college derivation that produces the seconds in the first place.
"""
import collections
import copy
import gzip
import json
import math
import os
import sys

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import possession as P  # noqa: E402
import cfb  # noqa: E402
import nfl  # noqa: E402


# ══════════════════════════════════════════════════════════════════════
# @vacuity the emitted number is the SHARE, never raw seconds
#   file: possession.py
#   find: return {team: secs / float(tot) for team, secs in per_team_seconds.items()}
#   with: return {team: secs / float(GAME_CLOCK_SECS) for team, secs in per_team_seconds.items()}
#
# @vacuity the share is averaged PER GAME, not season-total over season-total
#   file: possession.py
#   find: share = round(sum(a["shares"]) / len(a["shares"]), 4)
#   with: share = round(a["seconds"] / float(a["clock"]), 4)
#
# @vacuity a game whose clock is too thinly observed is WITHHELD
#   file: possession.py
#   find: if tot <= 0 or tot / float(GAME_CLOCK_SECS) < COVERAGE_MIN:
#   with: if tot <= 0:
#
# @vacuity possession is keyed to `drive`, never to `fixed_drive`
#   file: nfl.py
#   find: drvc = next((c for c in ("drive", "fixed_drive") if c in cols), None)
#   with: drvc = next((c for c in ("fixed_drive", "drive") if c in cols), None)
#
# @vacuity a diagnostic that cannot be computed is NOT reported instead
#   file: nfl.py
#   find: if qtrc is None or not periods:
#   with: if False:
#
# @vacuity the drive's time is the first that PARSES, not the first row's
#   file: nfl.py
#   find: best = next((v for v in (_mmss(x[1]) for x in rows) if v is not None),
#   with: best = next((v for v in (_mmss(x[1]) for x in rows[:1]) if v is not None),
# ══════════════════════════════════════════════════════════════════════

_QUIET = lambda *a, **k: None          # noqa: E731


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


section("1. ✅ ONE IMPLEMENTATION, NOT TWO THAT LOOK ALIKE")
# 🔴 RULE 117: a helper duplicated breaks in the file you did not edit.
#    "Both leagues emit the same shape" should be true BY CONSTRUCTION,
#    not by a test comparing two separate copies of the same arithmetic.
_N = open(os.path.join(ROOT, "nfl.py"), encoding="utf-8").read()
_C = open(os.path.join(ROOT, "cfb.py"), encoding="utf-8").read()
ck("_poss.share_table(" in _N and "_poss.share_table(" in _C,
   "🔴 both leagues call `possession.share_table`",
   "⛔ two copies of the share maths is rule 117 waiting to happen")
ck("shares" not in _N.split("def possession_from_rows")[1].split("\ndef ")[0]
   .replace("share_table", ""),
   "   ...and neither re-implements the averaging itself",
   "⛔ a second copy is how the two leagues drift apart silently")


section("2. 🔴 THE COVERAGE FLOOR IS DERIVED, NOT CHOSEN")
# A share read off a fraction `c` of the clock has a WORST-CASE error of
# `1 - c`: every unobserved second could have belonged to either team.
# So the floor is not a taste, it is the error you accept, inverted.
_P = open(os.path.join(ROOT, "possession.py"), encoding="utf-8").read()
ck(abs(P.COVERAGE_MIN - 0.90) < 1e-9,
   "🔴 the floor is %.2f — worst-case share error 0.10, ±3:00 of 60:00"
   % P.COVERAGE_MIN,
   "⛔ rule 166: the number and the reason travel together or the number "
   "goes stale")
ck("worst-case" in _P and "1 - c" in _P,
   "   ...and the derivation is written down beside it",
   "⛔ a floor with no stated reason is a floor nobody can revise")
# ⚠️ ASKED OF THE ASSIGNMENT, NOT THE NAME. `cfb.py` keeps a struck-
#    through comment saying what was removed and why, on purpose — rule
#    249, a check that trips over its own explanation.
ck("CFB_GAME_SECS_LO =" not in _C and "CFB_GAME_SECS_HI =" not in _C
   and not hasattr(cfb, "CFB_GAME_SECS_LO"),
   "⛔ ...and the band it REPLACED is gone (1800..3900)",
   "🔴 that band was on the SEASON's mean and accepted 887 of 887 real "
   "games, including one that exposed 30 pct of its clock. A bar that "
   "accepts everything it has ever seen is not a bar.")


section("3. ⛔ A GAME AT HALF COVERAGE IS WITHHELD — DRIVEN BOTH WAYS")
# ⚠️ CONSTRUCTED INPUT, and said so: this is a claim about arithmetic,
#    not about football, and a real game at exactly 0.50 is not on hand.
_half = {"g_ok": {"A": 1800, "B": 1800},          # coverage 1.00
         "g_half": {"A": 1500, "B": 300}}         # coverage 0.50
_t, _r = P.share_table(_half, {"g_ok": {"A": 10, "B": 10},
                               "g_half": {"A": 8, "B": 2}}, _QUIET)
ck(_r["games_withheld"] == 1 and _r["games_used"] == 1,
   "🔴🔴 THE 0.50 GAME IS WITHHELD AND THE 1.00 GAME IS KEPT",
   "⛔ at coverage 0.50 half the clock is unobserved, so the share read "
   "off the other half can be wrong by up to 0.50. Got withheld=%s "
   "used=%s" % (_r["games_withheld"], _r["games_used"]))
ck(abs(_t["A"]["share"] - 0.5) < 1e-9,
   "   ...so A reads 0.500 from the game that was observed",
   "⛔ not 0.708, the mean it would have had with the half-game in. "
   "Got %s" % _t["A"]["share"])
ck(_r["coverage_min"] == 0.5 and _r["coverage_floor"] == P.COVERAGE_MIN,
   "   ...and the report says what it saw and what it required",
   "a withholding that is silent about withholding cannot be audited: %s"
   % {k: _r[k] for k in ("coverage_min", "coverage_floor")})
# 🔴 AND ON REAL DATA: the worst-covered real college game is not used.
_S = json.load(gzip.open(os.path.join(
    ROOT, "research", "cfb_clock_sample_2019.json.gz"), "rt"))
_cpay, _crep = cfb.possession_from_plays(_S["plays"], 2019, log=_QUIET)
ck(_crep["coverage_min"] < 0.50 < P.COVERAGE_MIN,
   "🔴 a REAL college game exposes only %.0f pct of its clock"
   % (100 * _crep["coverage_min"]),
   "⛔ this is not a hypothetical: it is the worst of 887 real games")
ck(_crep["games_withheld"] == 484 and _crep["games_used"] == 403,
   "🔴🔴 ...and %d of %d real games are WITHHELD, %d used"
   % (_crep["games_withheld"], _crep["games_seen"], _crep["games_used"]),
   "⛔ THE OLD BAND WITHHELD NONE OF THEM. Withheld %s"
   % _crep["games_withheld"])
note("   CFB coverage  min %.2f  p10 %.2f  median %.2f  max %.2f"
     % (_crep["coverage_min"], _crep["coverage_p10"],
        _crep["coverage_median"], _crep["coverage_max"]))


section("4. 🔴🔴 THE EMITTED NUMBER IS THE SHARE, AND IT MATTERS")
_teams = _cpay["teams"]
_raw_pg = {t: v["seconds"] / float(v["games"]) for t, v in _teams.items()}
_shr_pg = {t: v["seconds_per_game"] for t, v in _teams.items()}
_keys = sorted(_teams)
_d = [abs(_raw_pg[t] - _shr_pg[t]) for t in _keys]
ck(len(_keys) > 100, "⚠️ over %d real college teams" % len(_keys),
   "⛔ a handful would make the comparison below meaningless")
ck(max(_d) > 60 and sum(1 for x in _d if x > 60) > 20,
   "🔴🔴 RAW AND SHARE ARE NOT INTERCHANGEABLE: max |diff| %.0fs, %d of "
   "%d teams differ by over a minute" % (max(_d), sum(1 for x in _d if x > 60),
                                         len(_keys)),
   "⛔ IF THIS EVER PASSES TRIVIALLY the emitted field has been swapped "
   "back to raw seconds and the two quantities have become the same one")
ck(all(abs(v["seconds_per_game"] - v["share"] * P.GAME_CLOCK_SECS) <= 0.5
       for v in _teams.values()),
   "   ...and the displayed seconds are DERIVED from the share",
   "⛔ rule 66: two routes to one number is two numbers")
note("   ⚠️ 183s and 72 of 160 are the residual AFTER the floor. The "
     "figures in this file's header — max 1053s, 202 of 217, r +0.6426 — "
     "are over all 887 games with no floor at all, which is what the "
     "builder used to emit. Both are measured; they are not the same "
     "quantity and neither is a correction of the other.")
_mean = sum(v["share"] for v in _teams.values()) / len(_teams)
ck(abs(_mean - 0.5) < 0.02,
   "🔴 the league mean share is %.4f — 0.5 by construction" % _mean,
   "⛔ raw seconds average 24:56 against a true 30:00, and that gap is "
   "the bias. A share cannot drift from 0.5 unless the maths is wrong.")


section("5. ⛔ AVERAGED PER GAME, NOT SEASON-TOTAL OVER SEASON-TOTAL")
# 🔴 A pooled ratio re-imports the weighting this exists to remove: a
#    team's better-observed games would count for more.
# ⚠️ CONSTRUCTED INPUT AGAIN, and it has to be: after the floor the two
#    agree on real data to 0.0035 of a share (12 seconds), because the
#    floor already removes the games where coverage varies most. That is
#    a fact worth stating — this is defence in depth, not the load-
#    bearing guard — and it is why the arithmetic is proven here instead.
_mix = {"g1": {"A": 1800, "B": 1800},      # coverage 1.00, A share 0.500
        "g2": {"A": 7000, "B": 200}}       # coverage 2.00, A share 0.972
_t2, _r2 = P.share_table(_mix, {"g1": {"A": 10, "B": 10},
                                "g2": {"A": 20, "B": 2}}, _QUIET)
_per_game = (0.5 + 7000 / 7200.0) / 2
_pooled = 8800 / 10800.0
ck(_r2["games_used"] == 2,
   "⚠️ both constructed games clear the floor (no ceiling, by design)",
   "⛔ a game that summed to MORE than the clock is an over-count in the "
   "source, and share is scale-free, so it is not thrown away")
ck(abs(_t2["A"]["share"] - _per_game) < 5e-4,
   "🔴🔴 A READS %.4f — THE MEAN OF ITS PER-GAME SHARES"
   % _t2["A"]["share"],
   "⛔ season-total ÷ season-total gives %.4f, and the gap is the "
   "weighting by coverage this exists to remove" % _pooled)
ck(abs(_t2["A"]["share"] - _pooled) > 0.05,
   "   ...and that is %.4f away from the pooled ratio"
   % abs(_t2["A"]["share"] - _pooled),
   "⛔ if these two were close the check above would prove nothing")
ck(_crep.get("pooled_vs_per_game_max_diff") is not None,
   "   ⚠️ ...and the real-data gap is REPORTED, not hidden (max %.4f)"
   % (_crep.get("pooled_vs_per_game_max_diff") or -1),
   "a choice nobody can see the cost of is a choice nobody can revisit")


section("6. 🔴 NFL IS THE CONTROL — RECORDED CLOCK, AND IT TILES THE GAME")
_NS = json.load(gzip.open(os.path.join(
    ROOT, "research", "pbp_possession_sample_2025.json.gz"), "rt"))
_npay, _nrep = nfl.possession_from_rows(_NS["rows"], 2025, _QUIET)
# ⚠️ READ DEFENSIVELY FROM HERE. The identity is now a REFUSAL, so a
#    mis-tiled season returns before the share maths runs and the report
#    carries no `games_*` keys at all. A KeyError here would cost every
#    check below — the checks must go RED and say so, not die.
for _k in ("games_withheld", "games_seen", "games_used",
           "games_no_possession", "unparsed", "recovered_from_later_row",
           "coverage_min", "coverage_median", "coverage_max"):
    _nrep.setdefault(_k, -1)
ck(_npay is not None, "⚠️ the whole 2025 season derives a table",
   "rep=%s" % {k: _nrep.get(k) for k in ("teams", "error")})
# ⚠️ ...and only NOW is it coerced, so the check above still sees the real
#    answer while nothing below dies on a None.
_npay = _npay or {"teams": {}, "unit": None}
ck(_nrep["regulation_games"] > 250 and _nrep["overtime_games"] > 5,
   "⚠️ ...over %d regulation and %d overtime games"
   % (_nrep["regulation_games"], _nrep["overtime_games"]),
   "⛔ without both, the two claims below prove nothing")
ck(_nrep["regulation_exact_3600"] == _nrep["regulation_games"],
   "🔴🔴 EVERY REGULATION GAME TILES THE CLOCK EXACTLY (%d of %d, zero "
   "seconds of deviation)"
   % (_nrep["regulation_exact_3600"], _nrep["regulation_games"]),
   "⛔ EQUALITY, NOT A RATE. ~~A 92 pct bar~~ stood here and it was WRONG: "
   "it existed only because this keyed on `fixed_drive`, which mis-tiled "
   "15 games and made the identity look like it held 94.42 pct of the "
   "time. A rate bar passes a regression that breaks up to 8 pct of "
   "games; equality catches the first one. Off-identity: %s"
   % _nrep.get("regulation_off_identity"))
ck(_nrep["overtime_over_3600"] == _nrep["overtime_games"],
   "🔴 ...and every one of the %d overtime games exceeds it"
   % _nrep["overtime_games"],
   "⛔ an overtime game that did NOT would mean the extra period was "
   "being dropped. Got %d of %d"
   % (_nrep["overtime_over_3600"], _nrep["overtime_games"]))
ck(_nrep["recovered_from_later_row"] == 0 and _nrep["unparsed"] == 0,
   "⚠️ the later-row recovery fires ZERO times on real data (%d), and no "
   "drive is unparsed (%d)"
   % (_nrep["recovered_from_later_row"], _nrep["unparsed"]),
   "⛔ SAID OUT LOUD SO A DEAD BRANCH DOES NOT LOOK LOAD-BEARING. It was "
   "written when this keyed on `fixed_drive`, where it 'recovered' 18 "
   "drives — an artifact of the wrong grouping, not a source quirk. "
   "Every real drive carries its time on its first row.")

# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 AND THAT DEAD BRANCH IS NOW DRIVEN, BECAUSE SAYING IT IS DEAD IS
#      NOT THE SAME AS KNOWING IT WORKS.
# ══════════════════════════════════════════════════════════════════════
# `vacuity.py` has reported this file since 2026-09-16:
#
#   test_possession.py still PASSES under the mutation it declares
#   (nfl.py: `... for x in rows)` -> `... for x in rows[:1])`)
#
# ⛔ And it was right. The check above asserts the counter is ZERO on
# clean data, which is true whether the scan reads every row of a drive
# or only the first. **A branch nothing exercises is a branch that will
# be wrong the day it matters** — and the day it matters is the day
# nflverse ships a drive whose first row has no time on it.
# ⛔ STRENGTHENED, NEVER DELETED: `vacuity.py` says Sam decides what
#    happens to a weak guard, and the only automatically-right edit is a
#    harder one.
# ✅ Three real drives have the time blanked on their FIRST row only.
#    The later rows still carry it, so a scan that reads the whole drive
#    recovers all three and loses nothing; a scan that reads `rows[:1]`
#    reports three unparsed drives and zero recoveries.
_GAP = copy.deepcopy(_NS["rows"])
_bydrv = {}
for _i, _r in enumerate(_GAP):
    if _r.get("drive_time_of_possession"):
        _bydrv.setdefault(
            (_r.get("game_id"), _r.get("fixed_drive") or _r.get("drive")),
            []).append(_i)
_multi = [_ix for _ix in _bydrv.values() if len(_ix) >= 2][:3]
for _ix in _multi:
    _GAP[_ix[0]]["drive_time_of_possession"] = ""
ck(len(_multi) == 3,
   "⚠️ three real drives were found with a time on more than one row",
   "⛔ rule 67 — with nothing blanked the drive below asserts nothing. "
   "found %d" % len(_multi))
_gpay, _grep = nfl.possession_from_rows(_GAP, 2025, _QUIET)
ck(_grep.get("recovered_from_later_row") == 3,
   "🔴🔴 a drive whose FIRST row lost its time is recovered from a later one",
   "⛔ THIS IS THE CHECK THAT MAKES THE BRANCH REAL. Reading only the "
   "first row of a drive would report these three as unparsed and "
   "silently drop their seconds out of the team's possession. Got "
   "recovered=%s unparsed=%s"
   % (_grep.get("recovered_from_later_row"), _grep.get("unparsed")))
ck(_grep.get("unparsed") == 0,
   "   ...and NOTHING is dropped as unparsed",
   "⛔ a recovered drive that is also counted unparsed would mean the "
   "seconds were lost anyway. Got %s" % _grep.get("unparsed"))
ck(_gpay is not None and len(_gpay.get("teams") or {}) ==
   len((_npay or {}).get("teams") or {}),
   "   ...and the table still covers every team it did before",
   "⛔ three blanked rows must not cost a team its row. %s vs %s"
   % (len((_gpay or {}).get("teams") or {}),
      len((_npay or {}).get("teams") or {})))
ck(_nrep["games_withheld"] == 0,
   "✅ ...and the coverage floor withholds NOTHING here (%d of %d)"
   % (_nrep["games_withheld"], _nrep["games_seen"]),
   "🔴 ONE RULE, AND IT ONLY BITES WHERE THE DATA IS THIN. A floor that "
   "removed NFL games too would be a floor priced for the wrong league.")

# ⛔ AND NFL PASSES THE BAR CFB FAILS — which is what makes the CFB
#    finding a finding rather than a preference.
_nraw = {t: v["seconds"] / float(v["games"]) for t, v in _npay["teams"].items()}
_nshr = {t: v["seconds_per_game"] for t, v in _npay["teams"].items()}
_nk = sorted(_npay["teams"])
# ⚠️ AND THIS BLOCK SURVIVES A REFUSAL TOO. With no teams there is no
#    correlation to take, and `pearson` would divide by zero — which
#    would cost every check below for the wrong reason.
_nd = [abs(_nraw[t] - _nshr[t]) for t in _nk] or [9999.0]
_r_nfl = (pearson([_nraw[t] for t in _nk], [_nshr[t] for t in _nk])
          if len(_nk) > 2 else 0.0)
ck(max(_nd) <= 60 and _r_nfl >= 0.95,
   "✅ NFL raw vs share: max |diff| %.0fs, r %+.4f — INTERCHANGEABLE"
   % (max(_nd), _r_nfl),
   "⛔ the acceptance bar is max |diff| <= 60s AND r >= 0.95. NFL passes "
   "it; college fails it on both halves. Same unit, different quantity.")
# ══════════════════════════════════════════════════════════════════════
# ⛔⛔ AND THE IDENTITY IS NOT CLAIMED WITHOUT THE COLUMN IT NEEDS.
# `[measured 2026-09-17, and this was a defect in the first draft of this
# very change]` Defaulting an unknown period to regulation folded all 16
# overtime games into the denominator and reported **285 regulation games
# at 89.12 pct** — a number that reads exactly like the real 94.42 pct,
# sits below the bar above, and is simply false.
# ⚠️ "An absence in an API response is evidence about the API, never
# about the sportsbook" — the same rule, one field over.
_noq = [{k: v for k, v in r.items() if k != "qtr"} for r in _NS["rows"]]
_nopay, _norep = nfl.possession_from_rows(_noq, 2025, _QUIET)
ck(_nopay is not None,
   "⚠️ the rows still derive a table without the period column",
   "⛔ if they did not, the claim below would be about nothing")
ck(_norep["regulation_exact_pct"] is None
   and _norep["regulation_games"] is None
   and _norep["overtime_games"] is None,
   "🔴🔴 WITH NO PERIOD COLUMN THE IDENTITY IS NOT REPORTED AT ALL",
   "⛔ NOT REPORTED WRONG. Defaulting to regulation gave %s regulation "
   "games at %s pct against the real 269 and 94.42 — a plausible number "
   "is worse than a missing one."
   % (_norep.get("regulation_games"), _norep.get("regulation_exact_pct")))
ck("no period column" in (_norep.get("identity_not_measurable") or ""),
   "   ...and it names the column it wanted",
   "⛔ a diagnostic that goes quiet without saying why is a diagnostic "
   "nobody can repair. Got %r" % _norep.get("identity_not_measurable"))
ck((_nrep["games_used"] + _nrep["games_withheld"]
    + _nrep["games_no_possession"]) == _nrep["games_seen"] + 0
   and _crep["games_used"] + _crep["games_withheld"]
   + _crep["games_no_possession"] == _crep["games_seen"],
   "⚠️ ...and the game accounting closes in both leagues",
   "⛔ a game that produced no possession at all is neither used nor "
   "withheld; numbers that do not add up invite the reader to assume "
   "the missing ones are fine. nfl %s ; cfb %s"
   % ({k: _nrep[k] for k in ("games_seen", "games_used", "games_withheld",
                             "games_no_possession")},
      {k: _crep[k] for k in ("games_seen", "games_used", "games_withheld",
                             "games_no_possession")}))

note("   NFL coverage  min %.3f  median %.3f  max %.3f  — %d of %d games "
     "tile exactly" % (_nrep["coverage_min"], _nrep["coverage_median"],
                       _nrep["coverage_max"], _nrep["regulation_exact_3600"],
                       _nrep["regulation_games"]))


section("7. ✅ BOTH LEAGUES, ONE SHAPE AND ONE UNIT — BY CONSTRUCTION")
_TOP = {"season", "kind", "unit", "column", "note", "drives", "teams"}
ck(_TOP <= set(_npay) and _TOP <= set(_cpay),
   "🔴 the same top-level keys in both",
   "nfl missing %s ; cfb missing %s"
   % (sorted(_TOP - set(_npay)), sorted(_TOP - set(_cpay))))
ck(_npay["unit"] == _cpay["unit"] == "share_of_game_clock",
   "🔴🔴 ONE UNIT, AND IT NAMES THE QUANTITY: %r" % _npay["unit"],
   "⛔ `seconds` was the same UNIT and a different QUANTITY on the two "
   "sides — that is exactly how this defect hid. Got %r / %r"
   % (_npay.get("unit"), _cpay.get("unit")))
_ns = {frozenset(v) for v in _npay["teams"].values()}
_cs = {frozenset(v) for v in _cpay["teams"].values()}
ck(_ns == _cs and len(_ns) == 1,
   "🔴 ...and one per-team shape: %s"
   % (sorted(next(iter(_ns))) if _ns else "— no NFL teams at all"),
   "nfl %s ; cfb %s" % ([sorted(x) for x in _ns], [sorted(x) for x in _cs]))
_bad = [(t, k, v) for pay in (_npay, _cpay)
        for t, d in pay["teams"].items() for k, v in d.items()
        if k != "share" and (not isinstance(v, int) or isinstance(v, bool))]
ck(not _bad,
   "🔴 every field but the share is an INT in both leagues",
   "⛔ `\"7:42\" + \"3:10\"` does not raise, it concatenates. Offenders: %s"
   % _bad[:4])
ck(all(0.0 < v["share"] < 1.0 for pay in (_npay, _cpay)
       for v in pay["teams"].values()),
   "   ...and every share is a real fraction of one game",
   "⛔ a share outside (0, 1) is not a share")
