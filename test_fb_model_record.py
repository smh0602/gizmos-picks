#!/usr/bin/env python3
"""test_fb_model_record.py — the Model picks record grades exactly the picks the site shows.

`[Sam, 2026-10-16]` Asked whether the record should keep grading the old spread / total fits
and every moneyline (underdogs included), Sam said "lets do both" (switch it, and backtest the
score-based picks) and: "i want whatever the models score predictions are to directly
correlate with any gameline picks the model chooses". So `fb_model.walk_forward` (the Model
picks record, its closing-line record and the verdict) replays the ONE rule the live list
uses, `fb_model.shown_pick`: spreads and totals FROM that week's predicted score, a moneyline
only on its expected winner, with the score's spread from that week's TRAINING games only.
Planted rows, the real walk_forward, current_picks, build, predicted_score and score_sigma;
⛔ reads nothing live.

# @vacuity 🔴 the record replays the rule the site shows, never each fit's own pick
#   file: fb_model.py
#   find:                           else shown_pick(r, mk, models, sigma, sigma_t, quotes))
#   with:                           else best_pick(r, mk, models[mk], quotes))
#
# @vacuity 🔴 ...with the score's spread from that week's training games only (no lookahead)
#   file: fb_model.py
#   find:         sigma, sigma_t = score_sigma(train), total_sigma(train)      # ⛔ training games only
#   with:         sigma, sigma_t = score_sigma(rows), total_sigma(rows)
#
# @vacuity 🔴 ...a spread pick needs the win chance (the score), never the spread fit
#   file: fb_model.py
#   find:             if not models[mk if rule == "fits" else "moneyline"]:     # the score needs the win chance
#   with:             if not models[mk]:
#
# @vacuity 🔴 a moneyline is shown and graded only on the expected winner
#   file: fb_model.py
#   find:     return pk if pk and pk["side"] == one_side.expected_side(ph) else None
#   with:     return pk
#
# @vacuity 🔴 the built file's record and verdict use the shown rule
#   file: fb_model.py
#   find:     wf = walk_forward(rows)
#   with:     wf = walk_forward(rows, rule="fits")
#
# @vacuity 🔴 ...which is the default
#   file: fb_model.py
#   find: def walk_forward(rows, rule="shown"):
#   with: def walk_forward(rows, rule="fits"):
#
# @vacuity 🔴 the pre-registered signal-9 report keeps the fits' own picks
#   file: fb_signal9.py
#   find:         wf = _with_flag(F, "S9_GAME", flag, lambda: F.walk_forward(rows, rule="fits"), lg)
#   with:         wf = _with_flag(F, "S9_GAME", flag, lambda: F.walk_forward(rows), lg)
#
# @vacuity 🔴 [2026-10-26, review] a played college game is replayed with the injury report the site showed
#   file: fb_model.py
#   find:                     r = as_shown(r)                   # the report the site showed it with
#   with:                     pass
#
# @vacuity ⛔ ...while every fit, the injury fit included, still trains on §3's 9:00 reading
#   file: fb_model.py
#   find:     return dict(r, sig=dict(s, inj=s["inj_shown"]))
#   with:     r["sig"] = dict(s, inj=s["inj_shown"]); return r
"""
import copy
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "ncaaf")
import fb_model as FM  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

PUR, WASH, TEX, FLA = "Purdue Boilermakers", "Washington Huskies", "Texas Longhorns", "Florida Gators"
NOW, KICK, DAY = "2026-10-16T08:00:00Z", "2026-10-17T19:30:00Z", "2026-10-17"
FIN = [{"id": "f%d" % i, "day": "2026-10-06", "final": True, "hs": hs, "as": as_, "T": None, "M": None,
        "home": "H%d" % i, "away": "A%d" % i, "sig": {"own_m": 0.0, "own_t": 45.0}, "snap": None}
       for i, (hs, as_) in enumerate(((31, 15), (15, 31), (35, 24), (24, 35)))]


def game(gid, names, T, own_t):
    return {"id": gid, "day": DAY, "final": False, "hs": None, "as": None, "T": T, "M": None,
            "home": names[0], "away": names[1], "sig": {"own_t": own_t},
            "snap": {"commence": KICK, "names": names, "pulled_at": NOW}}


UPCOMING = [game("g1", (PUR, WASH), 47.5, 47.0), game("g2", (TEX, FLA), 44.5, 46.0),
            game("g3", ("Home Three", "Road Three"), 45.5, 45.0), game("g4", ("Home Four", "Road Four"), 45.5, 45.0)]
# each fit's own chance for the HOME side / Over; the spread fit leans the OTHER way on purpose
P_FIT = {("g1", "moneyline"): 0.529, ("g1", "total"): 0.55, ("g1", "spread"): 0.8,
         ("g2", "moneyline"): 0.75, ("g2", "total"): 0.60, ("g2", "spread"): 0.2,
         ("g3", "moneyline"): 0.25, ("g3", "total"): 0.5, ("g3", "spread"): 0.8,
         ("g4", "moneyline"): 0.25, ("g4", "total"): 0.5, ("g4", "spread"): 0.2}
# the books (a spread's line is M on the HOME margin). Texas is the expected winner at 75%, but
# its moneyline's best VALUE is Florida's +350: the fits' rule picks that underdog, the site never
QUOTES = {("g1", "moneyline"): [("fanduel", None, 110, -130, False)],
          ("g1", "spread"): [("fanduel", 3.5, -110, -110, False)],
          ("g1", "total"): [("fanduel", 47.5, -110, -110, False)],
          ("g2", "moneyline"): [("fanduel", None, -400, 350, False)],
          ("g2", "spread"): [("fanduel", 6.5, -110, -110, False), ("draftkings", 11.5, -110, -110, False)],
          ("g3", "spread"): [("fanduel", -6.5, -110, -110, False)],
          ("g4", "spread"): [("fanduel", -12.5, -110, -110, False)]}
CLOSING = {("g3", "spread"): [("closing", -6.5, -110, -110, True)]}


def finished(rows):
    """The same games, played: what the record grades after the fact."""
    out = copy.deepcopy(rows)
    for r in out:
        if r["id"].startswith("g"):
            r.update(final=True, hs=24, **{"as": 20})
    return out


_saved = {n: getattr(FM, n) for n in ("features", "label", "fit", "predict", "book_quotes", "RECORDS")}


def patched(fn):
    try:
        FM.features = lambda r, mk, **k: (r["id"], mk)
        FM.label = lambda r, mk, **k: 1 if r["final"] else None
        # ⚠️ the SPREAD fit never exists here: a spread pick must not need it
        FM.fit = lambda xs, ys, **k: None if xs and xs[0][1] == "spread" else {"n": len(xs)}
        FM.predict = lambda m, x: P_FIT.get(x, 0.5)
        FM.book_quotes = lambda r, mk: QUOTES.get((r["id"], mk), [])
        FM.RECORDS = (("books", FM.book_quotes), ("closing", lambda r, mk: CLOSING.get((r["id"], mk), [])))
        return fn()
    finally:
        for n, f in _saved.items():
            setattr(FM, n, f)


def key(p):
    v = lambda x: x.get("value") if isinstance(x, dict) else x  # noqa: E731
    pr = v(p.get("model_probability")) if "model_probability" in p else round(100 * p["p"], 1)
    return (p["game_id"], p["market"], p["side"], v(p["line"]), pr)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE RECORD GRADES EXACTLY THE PICKS THE SITE SHOWED")
# ══════════════════════════════════════════════════════════════════════
CUR = patched(lambda: FM.current_picks("ncaaf", FIN + UPCOMING, now=NOW))
WF = patched(lambda: FM.walk_forward(finished(FIN + UPCOMING)))
FITS = patched(lambda: FM.walk_forward(finished(FIN + UPCOMING), rule="fits"))
_wf = sorted(key(dict(p, market=mk)) for mk in FM.MARKETS for p in WF["books"][mk] if p["game_id"].startswith("g"))
ck(len(CUR) >= 5, "⚠️ the case exists: the live list holds picks in every market", str(CUR))
eq(_wf, sorted(key(p) for p in CUR),
   "🔴🔴 the same games, once upcoming (the live list) and once played (the record): the same side, line "
   "and chance in every market. The record grades what the site showed, by the one rule (`shown_pick`)")
eq(sorted((p["game_id"], p["market"], p["side"]) for p in CUR),
   sorted([("g1", "moneyline", "home"), ("g1", "spread", "away"), ("g1", "total", "over"),
           ("g2", "spread", "home"), ("g3", "spread", "away"), ("g4", "spread", "home")]),
   "🔴 ...and that rule is Sam's: Purdue to win (the expected winner), WASHINGTON +3.5 and the Over (the "
   "predicted score), Texas -6.5, the road favourite -6.5, the home +12.5; no Florida moneyline")

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 NO UNDERDOG MONEYLINE, NO SPREAD FIT, IN EITHER RECORD")
# ══════════════════════════════════════════════════════════════════════
_mls = {(p["game_id"], p["side"]) for p in WF["books"]["moneyline"]}
_mlf = {(p["game_id"], p["side"]) for p in FITS["books"]["moneyline"]}
ck(("g2", "away") in _mlf,
   "⚠️ the case exists: the fits' own rule picks Florida's +350 (the best value) against a 75% Texas", str(_mlf))
eq(sorted(_mls), [("g1", "home")],
   "🔴 the record's moneyline is only the expected winner's (Purdue); Florida, the underdog the score has "
   "losing by 9, is never graded (`[Sam, 2026-10-16]` ~~every moneyline, both sides~~)")
eq([(p["game_id"], p["side"], p["line"]) for p in WF["closing"]["spread"]], [("g3", "away", -6.5)],
   "🔴 the closing-line record (the verdict's evidence) uses the same rule: the road favourite -6.5 the "
   "score covers, never the home side the spread fit leans to")
ck(not FITS["books"]["spread"],
   "   ...and the fits' rule has NO spread pick here (the spread fit is missing on purpose): every spread "
   "in the record came from the predicted score", str(FITS["books"]["spread"]))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 NO LOOKAHEAD: THE SCORE'S SPREAD IS FROM EARLIER GAMES ONLY")
# ══════════════════════════════════════════════════════════════════════
LATE = [{"id": "z1", "day": "2026-10-28", "final": True, "hs": 80, "as": 0, "T": None, "M": None,
         "home": "ZH", "away": "ZA", "sig": {"own_m": 0.0, "own_t": 30.0}, "snap": None}]
WF2 = patched(lambda: FM.walk_forward(finished(FIN + UPCOMING) + LATE))
_w2 = sorted(key(dict(p, market=mk)) for mk in FM.MARKETS for p in WF2["books"][mk] if p["game_id"].startswith("g"))
ck(FM.score_sigma(FIN + LATE) > 1.5 * FM.score_sigma(FIN),
   "⚠️ the case exists: a later 80-0 game would widen the score's spread a lot",
   (FM.score_sigma(FIN), FM.score_sigma(FIN + LATE)))
eq(_w2, _wf, "🔴 a game played AFTER the week changes nothing about that week's graded picks or chances")

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 THE BUILT FILE: RECORD AND VERDICT ON THE SHOWN RULE; SIGNAL 9 ON THE FITS")
# ══════════════════════════════════════════════════════════════════════
_orig = (FM.build_rows, FM.log)
_tmp = os.path.join(tempfile.mkdtemp(), "fb-model.json")
try:
    FM.build_rows = lambda *a, **k: finished(FIN + UPCOMING)
    FM.log = lambda m: None
    DOC = patched(lambda: FM.build("ncaaf", out=_tmp))
finally:
    FM.build_rows, FM.log = _orig
eq(sorted((p["game_id"], p["side"]) for p in DOC["graded"]["moneyline"] if p["game_id"].startswith("g")),
   [("g1", "home")], "🔴 fb-model.json's graded moneylines are the shown rule's (no Florida underdog)")
eq(sorted((p["game_id"], p["side"], p["line"]) for p in DOC["graded"]["spread"]),
   sorted([("g1", "away", 3.5), ("g2", "home", 6.5), ("g3", "away", -6.5), ("g4", "home", -12.5)]),
   "🔴 ...its graded spreads are the predicted score's, and its record counts exactly those")
ck(DOC["record"]["spread"]["picks"]["value"] == 4 and DOC["closing_record"]["spread"]["picks"]["value"] == 1,
   "   ...the record's counts are those picks (4 at the books, 1 at closing)",
   (DOC["record"]["spread"]["picks"], DOC["closing_record"]["spread"]["picks"]))
_s9 = open(os.path.join(ROOT, "fb_signal9.py"), encoding="utf-8").read()
ck('F.walk_forward(rows, rule="fits")' in _s9 and "F.walk_forward(rows)" not in _s9,
   "🔴 the pre-registered signal-9 report still scores the fits' own picks (rule \"fits\"), as when it was "
   "run: Sam switched the Model picks record, not that test")

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 COLLEGE INJURIES: THE RECORD READS THE REPORT THE SITE SHOWED `[2026-10-26, review]`")
# ══════════════════════════════════════════════════════════════════════
# Sam, "do 9am, 12pm, 7pm": a college game still to start reads the newest injury report at each
# build. Purdue's QB was Out on the 7:30 am report and cleared at 12:30 pm, so the 1:00 pm build
# (the last before kickoff) showed Purdue's picks with the QB playing. Once the game is played, its
# row reads §3's 9:00 cut (QB Out) for TRAINING, and `inj_shown` (cleared) for the record's replay.
CLEARED = {"qb": (0.0, 0.0), "off": (0.0, 0.0), "def": (0.0, 0.0)}
QB_OUT = {"qb": (1.0, 0.0), "off": (0.0, 0.0), "def": (0.0, 0.0)}
UP = copy.deepcopy(FIN + UPCOMING)
for _r in UP:
    _r["lg"] = "ncaaf"
    if _r["id"] == "g1":
        _r["sig"]["inj"] = dict(CLEARED)               # the 1:00 pm build: the 12:30 pm report
PLAYED = finished(UP)
for _r in PLAYED:
    if _r["id"] == "g1":
        _r["sig"].update(inj=dict(QB_OUT), inj_shown=dict(CLEARED))
NINE = copy.deepcopy(PLAYED)
for _r in NINE:
    _r["sig"].pop("inj_shown", None)
TRAINED = []
_injf, _on = FM.injury_fit, dict(FM.INJURIES)


def fixed_fit(train):
    TRAINED.extend((r["id"], (r["sig"].get("inj") or {}).get("qb")) for r in train if r["id"] == "g1")
    return [-10.0, 0.0, 0.0]                          # a starting QB out: 10 points


try:
    FM.injury_fit, FM.INJURIES["ncaaf"] = fixed_fit, True
    CUR5 = patched(lambda: FM.current_picks("ncaaf", UP, now=NOW))
    WF5 = patched(lambda: FM.walk_forward(PLAYED))
    WF9 = patched(lambda: FM.walk_forward(NINE))
    LATE5 = [{"id": "z9", "day": "2026-10-26", "final": True, "hs": 20, "as": 17, "T": None, "M": None, "lg": "ncaaf",
              "home": "ZH", "away": "ZA", "sig": {"own_m": 0.0, "own_t": 40.0}, "snap": None}]
    del TRAINED[:]
    patched(lambda: FM.walk_forward(PLAYED + LATE5))
finally:
    FM.injury_fit = _injf
    FM.INJURIES.clear()
    FM.INJURIES.update(_on)


def g1(picks):
    return sorted(k for k in picks if k[0] == "g1")


_cur5 = g1(key(p) for p in CUR5)
_rec5 = g1(key(dict(p, market=mk)) for mk in FM.MARKETS for p in WF5["books"][mk])
_nine5 = g1(key(dict(p, market=mk)) for mk in FM.MARKETS for p in WF9["books"][mk])
ck(_cur5 and _nine5 != _cur5,
   "⚠️ the case exists: replayed at §3's 9:00 reading (QB Out), the record would grade a Purdue pick the site "
   "never showed", (_cur5, _nine5))
eq(_rec5, _cur5,
   "🔴🔴 the record replays g1 with the report its last pre-kickoff build read (`inj_shown`): the same side, "
   "line and chance as the live list showed. The record grades what the site showed")
ck(TRAINED and all(qb == (1.0, 0.0) for _g, qb in TRAINED),
   "⛔ ...and the injury fit of a later week TRAINS on g1's 9:00 reading (QB Out), §3's tested cut, never "
   "the shown one", TRAINED)
eq([(r["sig"]["inj"], r["sig"]["inj_shown"]) for r in PLAYED if r["id"] == "g1"], [(QB_OUT, CLEARED)],
   "   (the replay never edits the row: g1 still carries both readings, 9:00's and the shown one)")
