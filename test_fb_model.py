#!/usr/bin/env python3
"""test_fb_model.py — the football pick model keeps the promises in
`research/fb_model_design.md` (Sam, 2026-09-23).

# @vacuity a snapshot pulled after kickoff is never a price
#   file: fb_model.py
#   find:             if not pulled or not commence or pulled >= commence:
#   with:             if not pulled or not commence:
#
# @vacuity only Hard Rock, FanDuel and DraftKings prices are used
#   file: fb_model.py
#   find:             bk = {k: v for k, v in (g.get("books") or {}).items() if k in ok}
#   with:             bk = dict(g.get("books") or {})
#
# @vacuity the walk-forward trains only on games before the week
#   file: fb_model.py
#   find:         train = [r for r in rows if r["day"] < wk]
#   with:         train = list(rows)
#
# @vacuity a pick needs a positive expected value at the best price
#   file: fb_model.py
#   find:     return best if best and best["ev"] > 0 else None
#   with:     return best
#
# @vacuity the record's uncertainty is clustered by GAME
#   file: fb_model.py
#   find:     c = shadow_fb.cluster(picks, key="game_id")
#   with:     c = shadow_fb.cluster([dict(p, _row=i) for i, p in enumerate(picks)], key="_row")
#
# @vacuity players out are read from a week BEFORE the game
#   file: fb_model.py
#   find:                                      if w < int(wk)), default=(None, None))[1]
#   with:                                      if w <= int(wk)), default=(None, None))[1]
#
# @vacuity a book's spread is used only if its own moneyline agrees on the favourite
#   file: fb_model.py
#   find:     return (M > 0) == home_fav
#   with:     return True
#
# @vacuity every number the page shows carries MODEL, MARKET or DESCRIPTIVE
#   file: fb_model.py
#   find:             "hit_rate": L(round(100 * rate, 1) if rate is not None else None, "DESCRIPTIVE"),
#   with:             "hit_rate": round(100 * rate, 1) if rate is not None else None,
"""
import datetime
import os
import sys

from tcheck import ck

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import fb_model as F  # noqa: E402

# ══════════════════════════════════════════════════════════════════════
# 1. PRICES: only the three books, only before kickoff, never invented
# ══════════════════════════════════════════════════════════════════════
_snapdoc = {"pulled_at": "2026-09-20T12:00:00Z", "games": [
    {"id": "g1", "commence": "2026-09-20T17:00:00Z", "home": "Home FC", "away": "Away FC",
     "books": {"draftkings": {"h2h": {"Home FC": -150, "Away FC": 130},
                              "spreads": {"Home FC": {"pt": -3.0, "px": -110},
                                          "Away FC": {"pt": 3.0, "px": -110}},
                              "totals": {"Over": {"pt": 44.5, "px": -110},
                                         "Under": {"pt": 44.5, "px": -110}}},
               "betmgm": {"h2h": {"Home FC": -120, "Away FC": 900}}}},
    {"id": "g2", "commence": "2026-09-20T11:00:00Z", "home": "Home FC", "away": "Other FC",
     "books": {"fanduel": {"h2h": {"Home FC": -200, "Other FC": 170}}}},
]}


class _Glob:
    def __init__(self, docs):
        self.docs = docs

    def __enter__(self):
        self.g, self.j = F.glob.glob, F.jz
        F.glob.glob = lambda pat: list(self.docs)
        F.jz = lambda p: self.docs[p]
        return self

    def __exit__(self, *a):
        F.glob.glob, F.jz = self.g, self.j


_res = {"Home FC": "HOM", "Away FC": "AWY", "Other FC": "OTH"}.get
with _Glob({"snap1": _snapdoc}):
    _bp = F.board_prices("nfl", _res)
_k1 = ("HOM", "AWY", "2026-09-20")
ck(_k1 in _bp and set(_bp[_k1]["books"]) == {"draftkings"},
   "🔴🔴 only Hard Rock, FanDuel and DraftKings prices are kept",
   "⛔ Sam: 'Hard Rock, FanDuel and DraftKings only'. BetMGM's +900 must not "
   "exist here. got %r" % (sorted(_bp[_k1]["books"]) if _k1 in _bp else None))
ck(("HOM", "OTH", "2026-09-20") not in _bp,
   "🔴 a snapshot pulled AFTER kickoff is never used as a price",
   "⛔ g2 kicked off at 11:00, the snapshot is 12:00 — that is a live price")

# design §3 / CLAUDE.md run_line: the favourite lays the points, per book.
_inv = {"pulled_at": "x", "commence": "y", "names": ("Home FC", "Away FC"), "books": {
    "fanduel": {"h2h": {"Home FC": -200, "Away FC": 170},
                "spreads": {"Home FC": {"pt": 4.5, "px": -110}, "Away FC": {"pt": -4.5, "px": -110}}},
    "draftkings": {"h2h": {"Home FC": -200, "Away FC": 170},
                   "spreads": {"Home FC": {"pt": -4.5, "px": -110}, "Away FC": {"pt": 4.5, "px": -110}}},
    "hardrockbet": {"spreads": {"Home FC": {"pt": -3.0, "px": -110}, "Away FC": {"pt": 3.0, "px": -110}}}}}
_sp = F.book_lines(_inv)["spread"]
ck([b for b, *_ in _sp] == ["draftkings"],
   "🔴🔴 a book's spread that contradicts its own moneyline is never used",
   "⛔ FanDuel has the -200 favourite GETTING 4.5 — an inverted label; Hard Rock has no "
   "moneyline to orient it. Only DraftKings may survive. got %r" % _sp)
ck(F.spread_oriented(0.0, None, None),
   "   ✅ ...and a pick'em spread (0) needs no orientation")

_row = {"id": "g1", "final": True, "hs": 24, "as": 20, "M": 3.0, "T": 44.5, "pml": 0.58,
        "snap": None, "dk_ml": None, "day": "2026-09-20",
        "sig": {"h2h_m": None, "h2h_t": None, "form_m": None, "form_t": None, "def": None,
                "poss": None, "out": None, "neutral": 0.0, "dome": 0.0}}
_fake_model = {"mu": [0.0] * 7, "sd": [1.0] * 7, "w": [2.0] + [0.0] * 7}   # p ~ 0.88
ck(F.best_pick(_row, "spread", _fake_model) is None,
   "🔴🔴 a game with no price at the three books gets NO pick — no price is invented",
   "⛔ CLAUDE.md: never invent a price")
_row_p = dict(_row, snap=dict(_bp[_k1]))
_pk = F.best_pick(_row_p, "moneyline", _fake_model)
ck(_pk and _pk["book"] == "draftkings" and _pk["price"] == -150 and _pk["ev"] > 0,
   "✅ with a real DraftKings price it picks, at that price",
   "got %r" % _pk)
# ⚠️ At p = 0.5 a +130 moneyline IS positive EV (0.5 x 2.30 - 1 = +0.15) —
#    the first draft of this check wrongly expected no pick there. The spread
#    is -110 both sides: 0.5 x 1.909 - 1 = -0.045 on each, so no pick.
_pk2 = F.best_pick(_row_p, "spread", {"mu": [0.0] * 7, "sd": [1.0] * 7, "w": [0.0] * 8})
ck(_pk2 is None,
   "🔴 a coin-flip model never picks into the vig — EV must be above zero",
   "at p=0.5 both sides of a -110/-110 spread lose 4.5%%. got %r" % _pk2)
_pk3 = F.best_pick(_row_p, "moneyline", {"mu": [0.0] * 7, "sd": [1.0] * 7, "w": [0.0] * 8})
ck(_pk3 and _pk3["side"] == "away" and abs(_pk3["ev"] - 0.15) < 1e-9,
   "   ✅ ...while the same coin flip DOES pick +130 — it is positive EV",
   "got %r" % _pk3)

# ══════════════════════════════════════════════════════════════════════
# 2. THE WALK-FORWARD NEVER TRAINS ON THE WEEK IT PREDICTS
# ══════════════════════════════════════════════════════════════════════
_seen = []
_fit = F.fit
try:
    F.fit = lambda X, y, **k: None
    _rows = []
    for i in range(40):
        d = (datetime.date(2025, 9, 1) + datetime.timedelta(days=3 * i)).isoformat()
        _rows.append(dict(_row, id="x%d" % i, day=d))
    _orig_label = F.label
    F.label = lambda r, mk, M=None, T=None: (_seen.append((r["day"], mk)) or 1)
    _wk_first_days = {}
    F.walk_forward(_rows)
finally:
    F.fit = _fit
    F.label = _orig_label
# every labelled training row F.label saw during a week must predate that week;
# walk_forward labels only `train` rows, so rebuild the week of each call.
_bad = []
_mondays = sorted({F.monday(r["day"]) for r in _rows})
_i = 0
for wk in _mondays:
    n_train = sum(1 for r in _rows if r["day"] < wk) * len(F.MARKETS)
    chunk = _seen[_i:_i + n_train]
    _i += n_train
    _bad += [d for d, _mk in chunk if d >= wk]
ck(_seen and not _bad,
   "🔴🔴 each week is predicted by a model trained only on games before its Monday",
   "⛔ Sam: 'for each week, train only on games before that week'. leaked: %s" % _bad[:3])

# ══════════════════════════════════════════════════════════════════════
# 3. THE RECORD: clustered by game, labelled for the page
# ══════════════════════════════════════════════════════════════════════
_picks = [{"game_id": "A", "won": True, "state": "graded", "break_even": 0.52},
          {"game_id": "A", "won": True, "state": "graded", "break_even": 0.52},
          {"game_id": "A", "won": True, "state": "graded", "break_even": 0.52},
          {"game_id": "B", "won": False, "state": "graded", "break_even": 0.52}]
_rec = F.record(_picks)
ck(_rec["effective_n"]["value"] <= 2.0,
   "🔴🔴 three picks from ONE game do not count as three results",
   "⛔ Sam: 'Any uncertainty you show is clustered by game'. effective n %r from "
   "2 games" % _rec["effective_n"]["value"])
_bare = [k for k, v in _rec.items() if not (isinstance(v, dict) and v.get("basis") in F.BASES)]
ck(not _bare,
   "🔴 every number in the record carries MODEL, MARKET or DESCRIPTIVE",
   "⛔ rule 55. unlabelled: %s" % _bare)
ck(_rec["break_even"]["basis"] == "MARKET" and _rec["hit_rate"]["basis"] == "DESCRIPTIVE",
   "   ⚠️ ...a break-even is the books' number, a hit rate is our record")

# ══════════════════════════════════════════════════════════════════════
# 4. PLAYERS OUT COME FROM A WEEK BEFORE THE GAME
# ══════════════════════════════════════════════════════════════════════
_tbl = {(2026, "HOM"): {1: 2, 3: 9}, (2026, "AWY"): {1: 5, 3: 0}}
_orig_tot = F.team_out_table
_orig_sched, _orig_bp, _orig_hist = F.schedule_games, F.board_prices, F.t60r.history
_orig_allowed = F.t60r.Allowed
try:
    F.team_out_table = lambda lg, root=None, extra=None: _tbl
    F.schedule_games = lambda lg, root=None: [{"id": "w3", "start": "2026-09-20T17:00",
                                               "home": "HOM", "away": "AWY", "week": 3,
                                               "season": 2026, "final": False}]
    F.board_prices = lambda lg, resolve, root=None: {}
    F.t60r.history = lambda lg: []

    class _A:
        def __init__(self, lg):
            pass

        def fraction(self, g):
            return None
    F.t60r.Allowed = _A
    _r3 = F.build_rows("nfl", board={})[0]
finally:
    F.team_out_table = _orig_tot
    F.schedule_games, F.board_prices, F.t60r.history = _orig_sched, _orig_bp, _orig_hist
    F.t60r.Allowed = _orig_allowed
ck(_r3["sig"]["out"] == 5 - 2,
   "🔴 a week-3 game reads players out from week 1 (the latest EARLIER week), not week 3",
   "⛔ week 3's own list would be read before it exists. got %r" % _r3["sig"]["out"])
