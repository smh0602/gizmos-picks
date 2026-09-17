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
#   find: a["shares"].append(secs / float(tot))
#   with: a["shares"].append(secs / float(GAME_CLOCK_SECS))
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
ck(_npay is not None, "⚠️ the whole 2025 season derives a table",
   "rep=%s" % {k: _nrep.get(k) for k in ("teams", "error")})
ck(_nrep["regulation_games"] > 250 and _nrep["overtime_games"] > 5,
   "⚠️ ...over %d regulation and %d overtime games"
   % (_nrep["regulation_games"], _nrep["overtime_games"]),
   "⛔ without both, the two claims below prove nothing")
ck(_nrep["regulation_exact_pct"] >= 92.0,
   "🔴🔴 %d of %d REGULATION GAMES TILE THE CLOCK EXACTLY (%.2f pct)"
   % (_nrep["regulation_exact_3600"], _nrep["regulation_games"],
      _nrep["regulation_exact_pct"]),
   "⛔ THE BAR SITS BETWEEN TWO MEASURED NUMBERS, not at a round one: "
   "94.42 pct with the drive time read from the first row of the drive "
   "that PARSES, and 88.48 pct reading only the first row. A derivation "
   "bug moves this rate; a hard `== 3600` would instead redden on the "
   "15 real games whose source rows carry no time at all.")
ck(_nrep["overtime_over_3600"] == _nrep["overtime_games"],
   "🔴 ...and every one of the %d overtime games exceeds it"
   % _nrep["overtime_games"],
   "⛔ an overtime game that did NOT would mean the extra period was "
   "being dropped. Got %d of %d"
   % (_nrep["overtime_over_3600"], _nrep["overtime_games"]))
ck(_nrep["recovered_from_later_row"] > 0,
   "🔴🔴 %d DRIVES CARRY NO TIME ON THEIR FIRST ROW AND ONE ON A LATER "
   "ONE" % _nrep["recovered_from_later_row"],
   "⛔ THE BUG THIS FOUND: taking the first row dropped every one of "
   "them, and with them the whole drive. It cost 16 regulation games "
   "their exact tiling (238 of 269 against 254 of 269).")
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
_nd = [abs(_nraw[t] - _nshr[t]) for t in _nk]
_r_nfl = pearson([_nraw[t] for t in _nk], [_nshr[t] for t in _nk])
ck(max(_nd) <= 60 and _r_nfl >= 0.95,
   "✅ NFL raw vs share: max |diff| %.0fs, r %+.4f — INTERCHANGEABLE"
   % (max(_nd), _r_nfl),
   "⛔ the acceptance bar is max |diff| <= 60s AND r >= 0.95. NFL passes "
   "it; college fails it on both halves. Same unit, different quantity.")
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
   "🔴 ...and one per-team shape: %s" % sorted(next(iter(_ns))),
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
