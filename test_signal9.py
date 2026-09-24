#!/usr/bin/env python3
"""test_signal9.py — signal 9, "Opportunity change", keeps the rules in
`research/fb_signal9_spec.md` (Sam, 2026-09-24).

# @vacuity a player on injured reserve counts as vacated while he is out
#   file: nfl.py
#   find: OPP_AVAILABLE = ("ACT", "INA")            # ⛔ IR (RES) is NOT available: vacated while out (Sam)
#   with: OPP_AVAILABLE = ("ACT", "INA", "RES")
#
# @vacuity only regular-season volume counts (weeks 1-18)
#   file: nfl.py
#   find:             if not isinstance(wk, int) or wk > 18 or not g.get("team"):
#   with:             if not isinstance(wk, int) or not g.get("team"):
#
# @vacuity the combined share is targets + carries over their combined total
#   file: nfl.py
#   find:             _den = dict(tot, combined=comb(tot))   # ⛔ the combined total is targets + carries
#   with:             _den = dict(tot)
#
# @vacuity inside-10 targets are passes to a receiver at or inside the 10
#   file: nfl.py
#   find:         if yl <= 10:
#   with:         if yl <= 20:
#
# @vacuity returning players absorb vacated volume: s_adj = s25 / (1 - v)
#   file: signal9.py
#   find:     return min(1.0, s25 / (1.0 - v)), s25, False
#   with:     return s25, s25, False
#
# @vacuity each 2026 game pulls the share: E = (4·s_adj + Σ obs) / (4 + n)
#   file: signal9.py
#   find:     return (K * adj + sum(obs)) / (K + len(obs))
#   with:     return adj
#
# @vacuity a card reads the roster of ITS week, never a later one
#   file: signal9.py
#   find:     later = [w for w, s in last.items() if s >= str(day)[:10]]
#   with:     later = [max(last)] if last else []
#
# @vacuity a use is kept only if it does not make log loss worse
#   file: fb_signal9.py
#   find:     return {"n": n, "mean_d": mean, "t": t, "p": p, "clusters": G, "keep": mean >= 0,
#   with:     return {"n": n, "mean_d": mean, "t": t, "p": p, "clusters": G, "keep": True,
#
# @vacuity the game model's signal 9 input is switched PER LEAGUE
#   file: fb_model.py
#   find:     s9 = (lambda x: [x] if S9_GAME.get(r.get("lg")) else [])  # noqa: E731
#   with:     s9 = (lambda x: [x] if any(S9_GAME.values()) else [])  # noqa: E731
#
# @vacuity section 9 refuses by name when one side is unknown
#   file: dossier_fb.py
#   find:         return no_opponent(9, "Opportunity change", missing)
#   with:         pass
#
# @vacuity a refused CFBD price fetches nothing and writes nothing
#   file: cfb.py
#   find:         if not quote["allowed"]:
#   with:         if False:
"""
import glob
import gzip
import json
import os
import shutil
import sys
import tempfile

from tcheck import ck

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import card_fb  # noqa: E402
import cfb  # noqa: E402
import cfbd_budget  # noqa: E402
import dossier_fb as D  # noqa: E402
import fb_model as F  # noqa: E402
import fb_props_model as M  # noqa: E402
import fb_signal9 as Z  # noqa: E402
import nfl  # noqa: E402
import signal9 as S  # noqa: E402


def _g(team, wk, tgt=0, car=0, ay=0):
    return {"team": team, "week": wk, "tgt": tgt, "car": car, "ay": ay}


# ══════════════════════════════════════════════════════════════════════
# 1. THE NFL TABLE (fixture: one team, three pass-catchers)
# ══════════════════════════════════════════════════════════════════════
_prior = {"a": {"name": "Gone Guy", "g": [_g("MIA", 1, tgt=50, ay=500), _g("MIA", 19, tgt=40)]},
          "b": {"name": "Hurt Guy", "g": [_g("MIA", 1, tgt=30, car=10)]},
          "c": {"name": "Stays Guy", "g": [_g("MIA", 1, tgt=20, car=90)]},
          "d": {"name": "Moved Guy", "g": [_g("BUF", 1, tgt=40)]}}
_rost = [{"week": "1", "team": "MIA", "gsis_id": "b", "status": "RES"},
         {"week": "1", "team": "MIA", "gsis_id": "c", "status": "ACT"},
         {"week": "1", "team": "MIA", "gsis_id": "d", "status": "ACT"},
         {"week": "2", "team": "MIA", "gsis_id": "b", "status": "ACT"},
         {"week": "2", "team": "MIA", "gsis_id": "c", "status": "ACT"}]
_opp, _rep = nfl.opportunity_from_rows(_rost, _prior, 2026)
_w1 = _opp["teams"]["MIA"]["weeks"]["1"]
ck(abs(_w1["tgt"]["share"] - 0.8) < 1e-9 and _w1["tgt"]["count"] == 80,
   "🔴🔴 IR counts as vacated while out: the gone player (50) + the IR player (30) of 100 targets = 80%",
   "⛔ Sam: 'Players on injured reserve count as vacated while they are out'. got %r" % _w1["tgt"])
ck(abs(_opp["teams"]["MIA"]["weeks"]["2"]["tgt"]["share"] - 0.5) < 1e-9,
   "🔴 ...and back when he returns: week 2 is only the gone player's 50%",
   "got %r" % _opp["teams"]["MIA"]["weeks"]["2"]["tgt"])
ck(abs(_opp["teams"]["MIA"]["off_roster"]["tgt"] - 0.5) < 1e-9,
   "   ✅ the off-roster-only figure (the definition Sam's check matches) leaves IR on the roster: 50%")
ck(_opp["teams"]["MIA"]["totals"]["tgt"] == 100,
   "🔴 only the regular season counts: the week-19 playoff targets are left out")
ck(abs(_w1["combined"]["share"] - (50 + 40) / 200.0) < 1e-9,
   "🔴 the combined share is (targets + carries) vacated over (targets + carries): 90 of 200",
   "got %r" % _w1.get("combined"))
ck(_opp["players"]["d"]["changed"] is True and _opp["players"]["c"]["changed"] is False
   and abs(_opp["players"]["c"]["share25"]["tgt"] - 0.2) < 1e-9,
   "🔴 per player: his 2025 share (20% of targets) and whether he changed teams (BUF -> MIA)")
_i10 = nfl.inside10_from_rows([
    {"season_type": "REG", "receiver_player_id": "c", "posteam": "MIA", "pass_attempt": "1", "yardline_100": "8"},
    {"season_type": "REG", "receiver_player_id": "c", "posteam": "MIA", "pass_attempt": "1", "yardline_100": "15"},
    {"season_type": "POST", "receiver_player_id": "c", "posteam": "MIA", "pass_attempt": "1", "yardline_100": "3"}])
ck(_i10 == {"c": {"MIA": 1}},
   "🔴 inside-10 targets: regular-season passes to a receiver at or inside the 10 (not the 15, not the playoffs)",
   "got %r" % _i10)

# ══════════════════════════════════════════════════════════════════════
# 2. THE ONE FORMULA
# ══════════════════════════════════════════════════════════════════════
_a = S.s_adj(_opp, "c", "MIA", 1, "tgt")
ck(abs(_a[0] - 0.2 / (1 - 0.8)) < 1e-9 or abs(_a[0] - 1.0) < 1e-9,
   "🔴🔴 returning players absorb the vacated volume: 20% / (1 − 80%) = 100% (capped at 1)",
   "got %r" % (_a,))
_a2 = S.s_adj(_opp, "c", "MIA", 2, "tgt")
ck(abs(_a2[0] - 0.4) < 1e-9, "   ✅ ...and in week 2 (50% vacated): 20% / 50% = 40%", "got %r" % (_a2,))
ck(abs(S.e_share(0.4, [0.1, 0.1, 0.1, 0.1]) - (4 * 0.4 + 0.4) / 8) < 1e-12,
   "🔴🔴 each 2026 game pulls toward his real role: four games at 10% pull 40% halfway, to 25%")
ck(S.s_adj(_opp, "d", "MIA", 1, "tgt")[0] == S.s_adj(_opp, "d", "MIA", 1, "tgt")[1],
   "   ✅ a player who changed teams keeps his old share, unadjusted")
ck(abs(S.card_scale(_opp, "c", "MIA", 2, "player_receptions") - 2.0) < 1e-9
   and S.card_scale(_opp, "c", "MIA", 2, "player_pass_yds") == 1.0,
   "🔴 the card scales a 2025 value by s_adj / s25 (40% / 20% = 2) on volume markets only")
ck(S.week_of("nfl", "2026-09-13") == 1 and S.week_of("nfl", "2026-09-20") == 2,
   "🔴 a card reads the roster of ITS week: 09-13 is week 1, 09-20 is week 2 — never a later week",
   "got %r / %r" % (S.week_of("nfl", "2026-09-13"), S.week_of("nfl", "2026-09-20")))

# ══════════════════════════════════════════════════════════════════════
# 3. THE KEEP RULE, AND THE SWITCHES MATCH THE RECORD
# ══════════════════════════════════════════════════════════════════════
ck(Z.keep_rule([(0.70, 0.70, "g%d" % i) for i in range(10)])["keep"] is True,
   "🔴 a use that is not worse (mean d = 0) is kept")
ck(Z.keep_rule([(0.69, 0.70, "g%d" % i) for i in range(10)])["keep"] is False,
   "🔴🔴 a use that makes log loss worse (mean d < 0) is dropped")
ck(Z.keep_rule([])["keep"] is False, "🔴 a use with nothing to score stays OFF")
_run = json.load(open(sorted(glob.glob(os.path.join(ROOT, "research", "fb_signal9_run_*.json")))[-1],
                      encoding="utf-8"))
_u = _run["uses"]
ck(F.S9_GAME["nfl"] == _u["game"]["keep_rule"]["keep"]
   and M.S9_PROPS["nfl"] == _u["props"]["keep_rule"]["keep"]
   and card_fb.S9_CARD["nfl"] == _u["card"]["keep_rule"]["keep"],
   "🔴🔴 every NFL switch is exactly what the recorded keep-rule result says",
   "⛔ the walk-forward decides, never a hand edit. switches %r / %r / %r"
   % (F.S9_GAME, M.S9_PROPS, card_fb.S9_CARD))
ck(not F.S9_GAME["ncaaf"] and not M.S9_PROPS["ncaaf"] and not card_fb.S9_CARD["ncaaf"],
   "🔴 college stays OFF in all three uses until its data is stored and scored")
_rows = [{"lg": "ncaaf", "M": 3.0, "T": 50.0, "pml": 0.5,
          "sig": {"h2h_m": None, "h2h_t": None, "form_m": None, "form_t": None, "def": None, "poss": None,
                  "out": None, "neutral": 0.0, "dome": 0.0, "vac_h": 0.4, "vac_a": 0.1}}]
_old = dict(F.S9_GAME)
F.S9_GAME.update({"nfl": True, "ncaaf": False})
try:
    _n_col = len(F.features(_rows[0], "spread"))
    _n_nfl = len(F.features(dict(_rows[0], lg="nfl"), "spread"))
finally:
    F.S9_GAME.clear()
    F.S9_GAME.update(_old)
ck(_n_col == 7 and _n_nfl == 8,
   "🔴 the switch is PER LEAGUE: NFL on adds the input, college stays without it",
   "got college %d, nfl %d inputs" % (_n_col, _n_nfl))

# ══════════════════════════════════════════════════════════════════════
# 4. COLLEGE: priced first, fetched once, refusal fetches nothing
# ══════════════════════════════════════════════════════════════════════
ck(set(cfbd_budget.signal9_one_time()["endpoints"]) == {"/player/returning", "/player/portal"},
   "🔴 cfbd_budget prices both college endpoints, read off cfb.py")
_tmp = tempfile.mkdtemp()
_oldout, _oldpre, _oldget = cfb.OUT, cfbd_budget.preflight, cfb.get
_calls = []
try:
    cfb.OUT = _tmp
    cfbd_budget.preflight = lambda *a, **k: {"allowed": False, "purpose": "x", "why": "test refusal"}
    cfb.get = lambda path, params, **k: (_calls.append(path) or [{"team": "X"}])
    _res = cfb.fetch_signal9(2026, log=lambda m: None)
finally:
    cfb.OUT, cfbd_budget.preflight, cfb.get = _oldout, _oldpre, _oldget
_wrote = os.listdir(_tmp)
shutil.rmtree(_tmp, ignore_errors=True)
ck(not _calls and not _wrote and set(_res.values()) == {"refused"},
   "🔴🔴 a refused CFBD price fetches NOTHING and writes nothing, so it is retried next run",
   "got calls %r, files %r, %r" % (_calls, _wrote, _res))

# ══════════════════════════════════════════════════════════════════════
# 5. THE DOSSIER: section 9, DESCRIPTIVE, refusing by name
# ══════════════════════════════════════════════════════════════════════
S.OVERRIDE[("nfl", 2026)] = _opp
try:
    _s9 = D.s_opportunity("MIA", "BUF", 2026, 1, "nfl")
    _s9m = D.s_opportunity("MIA", "BUF", 2026, 1, "nfl", missing="Some FCS U")
finally:
    S.OVERRIDE.pop(("nfl", 2026), None)
ck(_s9["n"] == 9 and _s9["name"] == "Opportunity change" and _s9["basis"] == D.DESC
   and "80.0%" in _s9["why"],
   "🔴 section 9 shows each team's vacated share, labelled DESCRIPTIVE", "got %r" % _s9.get("why"))
ck(_s9m["state"] == "UNAVAILABLE" and "Some FCS U" in _s9m["why"],
   "🔴 ...and refuses by name when one side is unknown (a pair section)")
ck(D.SECTIONS_DECLARED == 9, "   ✅ every dossier now declares nine sections")
