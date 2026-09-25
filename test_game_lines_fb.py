#!/usr/bin/env python3
"""test_game_lines_fb.py — the Game Lines tab, its paid pull, its check and
its record keep Sam's rules (2026-09-24).

# @vacuity each game is bought at the LAST props deadline before kickoff
#   file: collect.py
#   find:         elif nd is not None and nd <= kick - timedelta(minutes=FB_ALT_LEAD_MIN):
#   with:         elif False:
#
# @vacuity a game is never bought twice
#   file: collect.py
#   find:         elif eid in bought:
#   with:         elif False:
#
# @vacuity a call that bills above the budgeted worst case stops the pull
#   file: collect.py
#   find:         if used > worst:
#   with:         if False:
#
# @vacuity the pull refuses to buy past Sam's monthly cap and the daily allowance
#   file: collect.py
#   find:     fit = max(0, min(len(buy), room_m // per_game, room_d // per_game))
#   with:     fit = len(buy)
#
# @vacuity a price is keyed on its EXACT signed point, never the bare number
#   file: game_lines_fb.py
#   find:                     out[m].setdefault((side, float(pt)), {})[name] = px
#   with:                     out[m].setdefault((side, abs(float(pt))), {})[name] = px
#
# @vacuity the record grades the last copy frozen BEFORE kickoff
#   file: game_lines_fb.py
#   find:             if d.get("taken_at", "") < (g.get("commence") or ""):
#   with:             if True:
#
# @vacuity a rung graded once is never re-graded
#   file: game_lines_fb.py
#   find:             out.setdefault(g["key"], g)          # ⛔ the FIRST stored grade stands
#   with:             out[g["key"]] = g
#
# @vacuity the check's market baseline is fitted on EARLIER weeks only
#   file: fb_alt_lines.py
#   find:         train = [r for r in rows if r["day"] < wk]
#   with:         train = list(rows)
#
# @vacuity the check passes only when the model is not worse than the baseline
#   file: fb_alt_lines.py
#   find:     state = ("NOT YET MEASURABLE" if n < MIN_N else "PASS" if mean >= 0 else "FAIL")
#   with:     state = "PASS"
"""
import copy
import datetime
import glob
import gzip
import json
import os
import random
import shutil
import sys
import tempfile

from tcheck import ck, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import collect as K  # noqa: E402
import card_fb  # noqa: E402
import fb_alt_lines as A  # noqa: E402
import fb_model as F  # noqa: E402
import freshness as FR  # noqa: E402
import game_lines_fb as G  # noqa: E402

UTC = datetime.timezone.utc


def T(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def wgz(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(obj, fh)


def wjs(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)


BUF, LAC, DET, NYJ, KC, DEN, NYG, DAL = ("Buffalo Bills", "Los Angeles Chargers", "Detroit Lions",
                                          "New York Jets", "Kansas City Chiefs", "Denver Broncos",
                                          "New York Giants", "Dallas Cowboys")
GAMES = [("g1", "2026-09-27T17:00:00Z", BUF, LAC), ("g2", "2026-09-27T20:25:00Z", DET, NYJ),
         ("g3", "2026-09-27T23:30:00Z", KC, DEN), ("g4", "2026-09-29T00:15:00Z", DAL, NYG)]


def board_game(gid, commence, home, away):
    bk = lambda sp, to, mh, ma: {"spreads": {home: {"pt": sp, "px": -110}, away: {"pt": -sp, "px": -110}},  # noqa: E731
                                 "totals": {"Over": {"pt": to, "px": -110}, "Under": {"pt": to, "px": -110}},
                                 "h2h": {home: mh, away: ma}}
    return {"id": gid, "commence": commence, "home": home, "away": away,
            "books": {"hardrockbet": bk(-6.5, 47.5, -280, 230), "draftkings": bk(-6.5, 47.5, -275, 225),
                      "fanduel": bk(-7.0, 47.5, -290, 235), "betmgm": bk(-9.5, 50.5, -400, 300)}}


# ══════════════════════════════════════════════════════════════════════
section("1. THE PAID PULL: one pull per game, never twice, never past the caps")
# ══════════════════════════════════════════════════════════════════════
_tmp = tempfile.mkdtemp(prefix="alt-")
_saved = {k: getattr(K, k) for k in ("LEAGUE", "DATA", "LATEST", "SPORT", "now", "odds_get",
                                     "daily_allowance", "daily_spend", "LEAGUES")}
_calls = []
_bill = {"used": 2}


def _fake_odds(path, params):
    _calls.append((path, dict(params)))
    body = {"bookmakers": [{"key": "hardrockbet", "markets": []}, {"key": "betmgm", "markets": []}]}
    return body, _bill["used"], 10000


try:
    K.LEAGUE, K.SPORT = "nfl", "americanfootball_nfl"
    K.DATA = os.path.join(_tmp, "data", "nfl")
    K.LATEST = K.DATA + "/latest"
    K.LEAGUES = copy.deepcopy(K.LEAGUES)
    K.LEAGUES["nfl"]["data"] = K.DATA
    K.LEAGUES["ncaaf"]["data"] = os.path.join(_tmp, "data", "ncaaf")
    K.odds_get = _fake_odds
    K.daily_allowance = lambda: 600
    K.daily_spend = lambda: 0
    wgz(os.path.join(K.DATA, "2026-09-27", "gamelines", "1030.json.gz"),
        {"pulled_at": "2026-09-27T10:30:00Z", "games": [board_game(*g) for g in GAMES]})

    def pull(at):
        K.now = lambda: T(at)
        err = None
        try:
            K.collect_alt_lines()
        except RuntimeError as e:
            err = str(e)
        snaps = sorted(glob.glob(os.path.join(K.DATA, "*", "alt-lines", "*.json.gz")))
        return json.load(gzip.open(snaps[-1], "rt")), err

    # 07:05 ET Sunday: the 11:00 ET deadline still precedes every Sunday kickoff
    d1, e1 = pull("2026-09-27T11:05:00Z")
    held = dict(tuple(h) for h in d1["held"])
    ck(d1["bought"] == [] and "held for" in held.get("g1", "") and "held for" in held.get("g3", ""),
       "🔴🔴 at 7am a game is HELD for the 11am deadline that still precedes its kickoff",
       "got bought %r held %r" % (d1["bought"], held))
    ck("outside the" in held.get("g4", ""), "   ✅ Monday night is outside the window at 7am Sunday")
    ck(d1["credits_used"] == 0 and os.path.exists(os.path.join(K.DATA, "2026-09-27", "alt-lines")),
       "🔴 a pull that correctly buys nothing still writes its snapshot, so it is never 'late'")
    # 11:05 ET: the last deadline before kickoff — buy the three Sunday games
    d2, e2 = pull("2026-09-27T15:05:00Z")
    ck(sorted(d2["bought"]) == ["g1", "g2", "g3"] and d2["credits_used"] == 6,
       "🔴🔴 at the last deadline before kickoff every Sunday game is bought, once (3 x 2 credits)",
       "got %r spent %s" % (d2["bought"], d2["credits_used"]))
    _p = _calls[-1][1]
    ck(_p.get("bookmakers") == ",".join(K.FB_BOOK_KEYS) and "regions" not in _p
       and _p.get("markets") == "alternate_spreads,alternate_totals",
       "🔴 it asks Sam's three books by `bookmakers=` for the two alt markets",
       "got %r" % _p)
    ck(not any(c[0].endswith("/events") for c in _calls),
       "🔴 no events call: ids and kickoffs come from the stored gamelines pull")
    ck(all(b["key"] != "betmgm" for ev in d2["events"] for b in ev["bookmakers"]),
       "   ✅ only football's three books are stored")
    ck(d2["measured_units"] == 1.0 and d2["billed_per_event"] == [2, 2, 2],
       "🔴 the bill is MEASURED from x-requests-last and stored (1 unit x 2 markets)")
    d3, _e3 = pull("2026-09-27T15:20:00Z")
    held3 = dict(tuple(h) for h in d3["held"])
    ck(d3["bought"] == [] and held3.get("g1") == "already bought",
       "🔴🔴 a second run never buys a game twice", "got %r %r" % (d3["bought"], held3))
    d4, _e4 = pull("2026-09-27T17:30:00Z")
    ck(dict(tuple(h) for h in d4["held"]).get("g1") == "kicked off",
       "   ✅ never after kickoff (those prices would be live)")
    ck(K.alt_billing(K._alt_snaps()) == ("bookmakers", 1.0),
       "🔴 the next pull budgets the MEASURED bill, not the worst case")
    ck(K.alt_billing([("x", {"request": "bookmakers", "measured_units": 2.0})]) == ("regions", 2)
       and K.alt_billing([]) == ("bookmakers", K.FB_ALT_WORST_UNITS),
       "🔴 `bookmakers=` only while it bills LESS than two regions; unmeasured = the worst case")

    # the bill guard: Monday night game, one call bills above the worst case
    _bill["used"] = 5
    d5, e5 = pull("2026-09-28T15:05:00Z")
    ck(bool(e5 and "above the worst case" in e5 and len(d5["bought"]) == 1 and d5["stopped"]),
       "🔴🔴 a call billing above the budgeted worst case stops the pull AND fails the run",
       "got err %r bought %r" % (e5, d5["bought"]))
    _bill["used"] = 2

    # the caps: Sam's 1,500 a month (BOTH leagues) and the account's day
    for f in glob.glob(os.path.join(K.DATA, "*", "alt-lines", "*.json.gz")):
        os.remove(f)
    wgz(os.path.join(K.LEAGUES["ncaaf"]["data"], "2026-09-26", "alt-lines", "1900.json.gz"),
        {"pulled_at": "2026-09-26T19:00:00Z", "credits_used": 1499})
    n0 = len(_calls)
    d6, _e6 = pull("2026-09-27T15:05:00Z")
    ck(d6["bought"] == [] and sorted(d6["not_bought_budget"]) == ["g1", "g2", "g3"] and len(_calls) == n0,
       "🔴🔴 past Sam's 1,500 a month (college's spend counts too) NOTHING is bought",
       "got bought %r refused %r" % (d6["bought"], d6["not_bought_budget"]))
    for f in glob.glob(os.path.join(_tmp, "data", "*", "*", "alt-lines", "*.json.gz")):
        os.remove(f)
    K.daily_allowance, K.daily_spend = (lambda: 600), (lambda: 595)
    d7, _e7 = pull("2026-09-27T15:05:00Z")
    ck(len(d7["bought"]) == 1 and len(d7["not_bought_budget"]) == 2,
       "🔴 and never past the account's daily allowance (5 credits of room at the unmeasured 4 a game = 1 game)",
       "got %r" % d7["bought"])
finally:
    for k, v in _saved.items():
        setattr(K, k, v)
    shutil.rmtree(_tmp, ignore_errors=True)

_src = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
_pp = _src[_src.index('elif mode == "props-player":'):_src.index('elif mode == "props-pitcher-hr":')]
ck("collect_alt_lines()" in _pp and 'elif mode == "alt-lines":' in _src,
   "🔴 the pull rides the SCHEDULED props pull and has its own arm for converge's repair",
   "⛔ a contract row whose mode nothing runs is late for ever (rule 78)")
_nd = FR.next_due(FR.FB_TIMES["nfl"]["props"], T("2026-09-27T15:05:00Z"))
ck(_nd == T("2026-09-28T11:00:00Z"), "   ✅ next_due: after 11am ET Sunday the next props deadline is 7am Monday",
   "got %r" % _nd)

# ══════════════════════════════════════════════════════════════════════
section("2. THE CHECK: earlier weeks only, the bar, the label")
# ══════════════════════════════════════════════════════════════════════
random.seed(7)


def synth(n_weeks=24, per=12, later_noise=None):
    rows, d0 = [], datetime.date(2025, 9, 1)
    for w in range(n_weeks):
        for i in range(per):
            M, Tt = random.choice([-7, -3, 1, 3, 6, 10]), random.choice([41, 44, 47, 50])
            noise = (later_noise if (later_noise and w >= n_weeks - 2) else 13.0)
            margin, tot = round(M + random.gauss(0, noise)), round(Tt + random.gauss(0, noise))
            rows.append({"id": "s%d-%d" % (w, i), "lg": "nfl", "season": 2025,
                         "day": (d0 + datetime.timedelta(days=7 * w)).isoformat(), "final": True,
                         "hs": max(0, margin + 20), "as": 20, "M": M + 0.5, "T": Tt + 0.5, "pml": 0.5,
                         "sig": {"h2h_m": None, "h2h_t": None, "form_m": None, "form_t": None,
                                 "def": None, "poss": None, "out": None, "vac_h": None, "vac_a": None,
                                 "neutral": 0.0, "dome": 0.0}})
            rows[-1]["hs"], rows[-1]["as"] = (20 + margin, 20) if margin >= 0 else (20, 20 - margin)
            rows[-1]["as"] = rows[-1]["as"] + 0
            rows[-1]["hs"] = rows[-1]["hs"]
            rows[-1]["tot_target"] = tot
    return rows


_rows = synth()
_u1 = A.score(_rows)
_rows2 = synth()
random.seed(7)
_rows2 = synth(later_noise=40.0)
_u2 = A.score(_rows2)
_early = lambda us: [round(u["p_base"], 9) for u in us if u["game"].startswith(("s12-", "s13-"))]  # noqa: E731
ck(bool(_u1) and _early(_u1) == _early(_u2),
   "🔴🔴 the baseline's spread is fitted on EARLIER weeks only: changing the last two weeks "
   "leaves every earlier week's baseline untouched")
ck(A.verdict([{"d": 0.01, "game": "g%d" % i} for i in range(120)])["state"] == "PASS"
   and A.verdict([{"d": -0.01, "game": "g%d" % i} for i in range(120)])["state"] == "FAIL"
   and A.verdict([{"d": 0.5, "game": "g%d" % i} for i in range(40)])["state"] == "NOT YET MEASURABLE",
   "🔴 PASS iff not worse than the baseline; FAIL if worse; under 100 units NOT YET MEASURABLE")
_chk = {"markets": {"spread": {"state": "PASS", "bands": [{"bucket": "70-80%", "state": "UNDER"}]},
                    "total": {"state": "FAIL", "bands": []}}}
ck(A.label(_chk, "spread", 0.55, 3.0) == (True, None)
   and A.label(_chk, "spread", 0.75, 3.0)[0] is False
   and A.label(_chk, "spread", 0.55, 10.5)[0] is False
   and A.label(_chk, "total", 0.55, 3.0)[0] is False
   and A.label(None, "total", 0.55, 3.0)[1].startswith(A.WARNING),
   "🔴 plain MODEL only when the market PASSED, within 10 points, in a band that did not run under")

# ══════════════════════════════════════════════════════════════════════
section("3. THE TAB: every rung, exact signed prices, the label, the slate")
# ══════════════════════════════════════════════════════════════════════
_r = tempfile.mkdtemp(prefix="gl-")
_lg = os.path.join(_r, "data", "nfl")
_sig = {"h2h_m": None, "h2h_t": None, "form_m": None, "form_t": None, "def": None, "poss": None,
        "out": None, "vac_h": None, "vac_a": None, "neutral": 0.0, "dome": 0.0}


def _prow(gid, sid, commence, home, away):
    return {"id": sid, "lg": "nfl", "season": 2026, "day": commence[:10], "kick": commence, "week": 4,
            "home": home, "away": away, "M": 6.5, "T": 47.5, "pml": 0.7, "sig": dict(_sig),
            "names": [home, away], "commence": commence}


_k_sp = len(F.features(_prow("g1", "S1", GAMES[0][1], BUF, LAC), "spread"))
_k_to = len(F.features(_prow("g1", "S1", GAMES[0][1], BUF, LAC), "total"))
_models = {"spread": {"mu": [0.0] * _k_sp, "sd": [1.0] * _k_sp, "w": [0.0, -1.0] + [0.0] * (_k_sp - 1)},
           "total": {"mu": [0.0] * _k_to, "sd": [1.0] * _k_to, "w": [0.0, -1.0] + [0.0] * (_k_to - 1)}}
wjs(os.path.join(_lg, "latest", "fb-model.json"),
    {"pricing": {"models": _models, "games": [_prow(g[0], "S" + g[0][1:], g[1], g[2], g[3]) for g in GAMES]}})
wjs(os.path.join(_lg, "latest", "alt-lines-check.json"), _chk)
wgz(os.path.join(_lg, "latest", "schedule-2026.json.gz"),
    {"games": [{"id": "S" + g[0][1:], "home": g[2], "away": g[3], "final": False} for g in GAMES]})
wgz(os.path.join(_lg, "2026-09-26", "gamelines", "1400.json.gz"),
    {"pulled_at": "2026-09-26T14:00:00Z", "games": [board_game(*g) for g in GAMES]})


def alt_ev(gid, home, away, extra=None):
    o = lambda n, pt, px: {"name": n, "point": pt, "price": px}  # noqa: E731
    bks = [{"key": "hardrockbet", "markets": [
               {"key": "alternate_spreads", "outcomes": [o(home, -3.5, -150), o(away, 3.5, 125),
                                                         o(home, -7.0, 105), o(away, 7.0, -125),
                                                         o(home, -10.5, 250), o(away, 20.5, -1400)]},
               {"key": "alternate_totals", "outcomes": [o("Over", 45.5, -140), o("Under", 45.5, 115)]}]},
           {"key": "hardrockbet_oh", "markets": [
               {"key": "alternate_spreads", "outcomes": [o(home, -3.5, -900)]}]},
           {"key": "draftkings", "markets": [
               {"key": "alternate_spreads", "outcomes": [o(home, -3.5, -145), o(away, 3.5, 120),
                                                         o(home, 3.5, 130)]}]},
           {"key": "fanduel", "markets": [
               {"key": "alternate_totals", "outcomes": [o("Over", 45.5, -135)] + (extra or [])}]}]
    return {"id": gid, "commence": dict((g[0], g[1]) for g in GAMES)[gid], "home": home, "away": away,
            "bookmakers": bks}


def write_alt(hhmm, events, day="2026-09-26"):
    wgz(os.path.join(_lg, day, "alt-lines", "%s.json.gz" % hhmm),
        {"pulled_at": "%sT%s:%s:00Z" % (day, hhmm[:2], hhmm[2:]), "events": events})


write_alt("1500", [alt_ev("g1", BUF, LAC), alt_ev("g2", DET, NYJ)])
NOW = T("2026-09-26T16:00:00Z")
try:
    doc = G.build("nfl", root=_r, now=NOW, log=lambda m: None)
    ids = [g["id"] for g in doc["games"]]
    ck(ids == ["g1", "g2", "g3"] and doc["slate_date"] == "2026-09-27",
       "🔴 one slate: Sunday's three games (Sunday night included), Monday night is not on it",
       "got %r on %s" % (ids, doc["slate_date"]))
    g1 = doc["games"][0]
    sp = {(r["side"], r["pt"]): r for r in g1["spread"]}
    ck(len(g1["spread"]) == 7 and len(g1["total"]) == 2 and doc["n_rungs"] == 18,
       "🔴🔴 every rung the three books post is on the tab — none capped, none filtered",
       "got %d spread / %d total, %d in all" % (len(g1["spread"]), len(g1["total"]), doc["n_rungs"]))
    ck(("home", 3.5) in sp and ("home", -3.5) in sp and "Hard Rock" not in sp[("home", 3.5)]["prices"],
       "🔴🔴 Bills +3.5 and Bills -3.5 are DIFFERENT wagers and are never merged",
       "got %r" % sorted(sp))
    r = sp[("home", -3.5)]
    ck(r["prices"] == {"Hard Rock": -150, "DraftKings": -145} and r["best"] == -145
       and r["book"] == "DraftKings" and r["be"] == round(100 / F.decimal(-145), 1),
       "🔴 each book's price, the best of them and its break-even (Hard Rock's Ohio skin never counted twice)",
       "got %r" % r)
    _p = F.predict(_models["spread"], F.features(_prow("g1", "S1", GAMES[0][1], BUF, LAC), "spread", M=3.5))
    ck(r["p"] == round(100 * _p, 1) and r["edge"] == round(100 * (_p * F.decimal(-145) - 1.0), 1),
       "🔴 the model's % is the LIVE model at that exact line, and the edge is priced at the best price")
    ck(r["cal"] is True and sp[("home", -10.5)]["dist"] == 4.0
       and doc["games"][0]["total"][0]["cal"] is False
       and doc["games"][0]["total"][0]["warn"].startswith(A.WARNING),
       "🔴 the label comes from the check: a failed market is SHOWN with the warning, never hidden")
    ck(sp[("away", 20.5)]["floor"] is False and sp[("away", 20.5)]["p"] is not None,
       "   ✅ a rung below -700 is shown (never starred, never paired)")
    ck(set(G.BASES) >= {"pt", "prices", "best", "be", "p", "edge", "dist"}
       and G.BASES["p"] == "MODEL" and G.BASES["be"] == "MARKET" and G.BASES["prices"] == "MARKET",
       "🔴 rule 55: every number on a rung names its basis; a price never wears a model %")
    ck(g1["fair_spread"] == 0.0 and doc["games"][0]["main"]["Hard Rock"]["moneyline"] == {"home": -280, "away": 230}
       and "BetMGM" not in doc["games"][0]["main"],
       "   ✅ the fair line is where the model says 50%, and the main lines are the three books only")

    # parlays — the card's builder and the card's rules
    P = doc["parlays"]
    legs2 = P.get("2") or []
    ck(bool(legs2) and all(len(set(p["game_ids"])) == len(p["game_ids"]) for s in P.values() for p in s)
       and all(p["multiplier"] >= 1.8 for p in legs2) and all(p["joint_basis"] == "MODEL" for p in legs2),
       "🔴 alt-line parlays: different games, 1.8x or more, joint labelled MODEL",
       "got %r" % [(p["legs"], p["multiplier"]) for p in legs2][:3])
    ck(not any("+20.5" in t for s in P.values() for p in s for t in p["legs"]),
       "🔴 a rung below -700 is never paired")
    ck(all(p["warning"] == A.WARNING for s in P.values() for p in s if any("Over" in t for t in p["legs"])),
       "   ✅ a parlay with an uncalibrated leg carries the warning")
    _rows_card = [{"confidence": 70, "price": -150, "clears_price_floor": True, "game_id": "a", "book": "X",
                   "player": "P1", "game": "A", "side": "over", "line": 50.5, "market": "player_pass_yds"},
                  {"confidence": 70, "price": -150, "clears_price_floor": True, "game_id": "b", "book": "X",
                   "player": "P2", "game": "B", "side": "over", "line": 50.5, "market": "player_pass_yds"}]
    ck(card_fb.build_parlays_fb(_rows_card)[0]["2"][0]["joint_basis"] == "RECORD",
       "   ✅ the card's own parlays are unchanged: RECORD, not MODEL")

    # ══════════════════════════════════════════════════════════════════
    section("4. THE RECORD: frozen before kickoff, graded once, apart from the rest")
    # ══════════════════════════════════════════════════════════════════
    arch = lambda: sorted(glob.glob(os.path.join(_lg, "*", "game-lines", "*.json.gz")))  # noqa: E731
    ck(len(arch()) == 1, "🔴 what the tab showed is frozen when built (daystore, write-once)")
    G.build("nfl", root=_r, now=NOW + datetime.timedelta(minutes=5), log=lambda m: None)
    ck(len(arch()) == 1, "   ✅ an unchanged tab is not frozen again")
    write_alt("1510", [alt_ev("g1", BUF, LAC, extra=[{"name": "Over", "point": 51.5, "price": 150}]),
                       alt_ev("g2", DET, NYJ)])
    G.build("nfl", root=_r, now=NOW + datetime.timedelta(minutes=12), log=lambda m: None)
    ck(len(arch()) == 2, "🔴 a changed price is frozen as a NEW copy; the old one is never edited")
    # a copy taken AFTER kickoff (live prices) must never be graded
    wgz(os.path.join(_lg, "2026-09-27", "game-lines", "1800.json.gz"),
        {"taken_at": "2026-09-27T18:00:00Z", "games": [{"id": "g1", "sched_id": "S1",
         "commence": GAMES[0][1], "rungs": [{"m": "total", "side": "over", "pt": 60.5, "prices": {},
                                              "best": 100, "book": "X", "be": 50.0, "p": 50.0,
                                              "edge": 0.0, "cal": False}]}]})
    wgz(os.path.join(_lg, "latest", "schedule-2026.json.gz"),
        {"games": [{"id": "S1", "home": BUF, "away": LAC, "final": True, "home_score": 27, "away_score": 20}]
         + [{"id": "S" + g[0][1:], "final": False} for g in GAMES[1:]]})
    AFTER = T("2026-09-27T23:00:00Z")
    G.build("nfl", root=_r, now=AFTER, log=lambda m: None)
    grades = G.stored_grades("nfl", _r)
    gk = lambda m, s, pt: grades.get("g1|%s|%s|%s" % (m, s, pt))  # noqa: E731
    ck(gk("spread", "home", -3.5)["won"] is True and gk("spread", "away", 3.5)["won"] is False
       and gk("spread", "home", -10.5)["won"] is False and gk("total", "over", 45.5)["won"] is True,
       "🔴 graded from the final score: 27-20 covers -3.5, not -10.5; 47 goes over 45.5")
    ck(gk("spread", "home", -7.0)["state"] == "void" and gk("total", "over", 51.5)["won"] is False,
       "   ✅ a push is void, and the rung added before kickoff is graded too")
    ck(gk("total", "over", 60.5) is None,
       "🔴🔴 a copy frozen AFTER kickoff is never the one graded")
    wgz(os.path.join(_lg, "latest", "schedule-2026.json.gz"),
        {"games": [{"id": "S1", "home": BUF, "away": LAC, "final": True, "home_score": 3, "away_score": 20}]})
    G.build("nfl", root=_r, now=AFTER + datetime.timedelta(hours=1), log=lambda m: None)
    ck(G.stored_grades("nfl", _r)["g1|spread|home|-3.5"]["won"] is True
       and len(glob.glob(os.path.join(_lg, "*", "game-lines-grades", "*.json.gz"))) == 1,
       "🔴🔴 a rung graded once is never re-graded, whatever changes later (no second grade written)")
    # ...and if two stored grades ever disagree, the FIRST one stands
    wgz(os.path.join(_lg, "2026-09-30", "game-lines-grades", "0900.json.gz"),
        {"grades": [{"key": "g1|spread|home|-3.5", "state": "graded", "won": False}]})
    ck(G.stored_grades("nfl", _r)["g1|spread|home|-3.5"]["won"] is True,
       "🔴 two stored grades for one rung: the FIRST stands, a later file never overrides it")
    rec = json.load(open(os.path.join(_lg, "latest", "game-lines-record.json"), encoding="utf-8"))
    ck(rec["kind"] == "DESCRIPTIVE" and rec["markets"]["spread"]["graded"] == 5
       and rec["markets"]["spread"]["voids"] == 2 and "clustered by game" in rec["note"],
       "🔴 its own record file, graded per game, apart from every other record",
       "got %r" % {m: (x["graded"], x["voids"]) for m, x in rec["markets"].items()})
finally:
    shutil.rmtree(_r, ignore_errors=True)
