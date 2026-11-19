#!/usr/bin/env python3
"""test_fb_card_calibration.py — the football props card's calibration is
scored exactly as `research/fb_card_calibration_spec.md` fixes it
(Sam, 2026-09-24).

# @vacuity each week's mapping is fitted only on picks graded BEFORE that week
#   file: fb_card_calibration.py
#   find:         train = [p for p in picks if p["day"] < wk]
#   with:         train = [p for p in picks if F.monday(p["day"]) <= wk]
#
# @vacuity a void or ungradable pick is never scored
#   file: fb_card_calibration.py
#   find:                 if r.get("confidence") is None or r.get("won") not in (True, False):
#   with:                 if r.get("confidence") is None:
#
# @vacuity d = raw loss − calibrated loss, so d > 0 means the correction helped
#   file: fb_card_calibration.py
#   find:     d = [logloss(s["raw"], s["y"]) - logloss(s["cal"], s["y"]) for s in scored]
#   with:     d = [logloss(s["cal"], s["y"]) - logloss(s["raw"], s["y"]) for s in scored]
#
# @vacuity the paired test clusters by GAME
#   file: fb_card_calibration.py
#   find:     n, mean, t, p, G = mlb_refit.paired_test_clustered(d, [s["game"] for s in scored])
#   with:     n, mean, t, p, G = mlb_refit.paired_test_clustered(d, list(range(len(scored))))
#
# @vacuity under 500 scored picks the verdict is NOT YET MEASURABLE
#   file: fb_card_calibration.py
#   find:     if n < MIN_N:
#   with:     if n < 5:
#
# @vacuity the page's band flags are calibration.py's own verdicts
#   file: fb_card_calibration.py
#   find:              "actual": L(b["actual"], "DESCRIPTIVE"), "flag": b["state"]}
#   with:              "actual": L(b["actual"], "DESCRIPTIVE"), "flag": "OK"}
#
# @vacuity [Sam, 2026-10-01] the page shows NO band table or raw-numbers warning next to the card
#   file: index.html
#   find:   <p style="color:var(--mut);margin:0">${freshness(C.odds_pulled_at)}</p>
#   with:   <p style="color:var(--mut);margin:0">${freshness(C.odds_pulled_at)}</p>${fbCardCalHtml(CC)}
#
# @vacuity [Sam, 2026-10-01] the page no longer loads card-calibration.json at all (`[Sam, 2026-10-17]` put back at fbPicks' splitStarted line: ~~const AG = await fbAgLoad();~~ left fbPicks with the agreement record)
#   file: index.html
#   find:   const {list, nStarted, allDone} = splitStarted(C.picks);
#   with:   const {list, nStarted, allDone} = splitStarted(C.picks); const CC = await jget(`${LG_DATA[LEAGUE]}/latest/card-calibration.json`);
#
# @vacuity 🔴 [Sam, 2026-11-18] §3a: a "+game-<name>" suffix (the game model) never ends the arm
#   file: fb_card_calibration.py
#   find:     return m if i < 0 else m[:i]
#   with:     return m
#
# @vacuity 🔴 §3a: only games kicking off on or after the registration date count
#   file: fb_card_calibration.py
#   find:     return props_method(r.get("card_method")) == method and day is not None and day >= since
#   with:     return props_method(r.get("card_method")) == method
#
# @vacuity 🔴 §3a: ...and only the registered props method (a props switch's -last2 ends it)
#   file: fb_card_calibration.py
#   find:     return props_method(r.get("card_method")) == method and day is not None and day >= since
#   with:     return props_method(r.get("card_method")).startswith(method) and day is not None and day >= since
#
# @vacuity 🔴 §3a: the kickoff's day is its US Eastern day, never the UTC string's
#   file: fb_card_calibration.py
#   find:     day = card_fb.et_date(r.get("commence"))
#   with:     day = (r.get("commence") or "")[:10] or None
#
# @vacuity 🔴 §3a: the build scores the arm on `counts`, not on one exact method string
#   file: fb_card_calibration.py
#   find:     picks_rr = load_picks(root, keep=counts)
#   with:     picks_rr = load_picks(root, method=REREG_METHOD)
#
# @vacuity 🔴 §3a: the earlier arms are labelled superseded, with the section and its date
#   file: fb_card_calibration.py
#   find: SUPERSEDED = ("research/fb_card_calibration_spec.md §3a
#   with: SUPERSEDED = None and ("research/fb_card_calibration_spec.md §3a
#
# @vacuity 🔴 §3a: the earlier arms' numbers are pinned (the after-fix arm still reads only "season-blend")
#   file: fb_card_calibration.py
#   find:     picks_fx = load_picks(root, method="season-blend")
#   with:     picks_fx = load_picks(root, keep=lambda r: props_method(r.get("card_method")).startswith("season-blend"))
#
# @vacuity 🔴 the newest day of the arm's method is that method's, not any row's
#   file: fb_card_calibration.py
#   find:             if any(r.get("confidence") is not None and counts(r, method, since) for r in graded):
#   with:             if any(r.get("confidence") is not None for r in graded):
#
# @vacuity 🔴 [2026-11-19, review] ...and a row the arm COUNTS: its props method alone kept an arm that counts nothing silent
#   file: fb_card_calibration.py
#   find:             if any(r.get("confidence") is not None and counts(r, method, since) for r in graded):
#   with:             if any(r.get("confidence") is not None and props_method(r.get("card_method")) == method for r in graded):
#
# @vacuity 🔴 the watchdog: an arm its league stopped feeding for over 14 days is DEGRADED
#   file: watchdog.py
#   find:             if idle > CAL_STARVED_DAYS and fed:
#   with:             if idle > CAL_STARVED_DAYS * 100 and fed:
#
# @vacuity 🔴 ...and the off-season (the league graded nothing either) stays silent
#   file: watchdog.py
#   find:             if idle > CAL_STARVED_DAYS and fed:
#   with:             if idle > CAL_STARVED_DAYS:
#
# @vacuity 🔴 ...and a superseded arm is never reported
#   file: watchdog.py
#   find:             if arm.get("superseded_by"):
#   with:             if False:
#
# @vacuity 🔴 ...and the check is registered, so the real watchdog runs it
#   file: watchdog.py
#   find:           check_calibration_arm,
#   with:           # check_calibration_arm,
#
# @vacuity 🔴 ...and a file that is not an object is passed over, never a crash (a BROKEN finding)
#   file: watchdog.py
#   find:         for name, arm in sorted(doc.items() if isinstance(doc, dict) else []):
#   with:         for name, arm in sorted(doc.items()):
"""
import ast
import datetime
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import card_fb as C  # noqa: E402
import fb_card_calibration as K  # noqa: E402
import jsblock  # noqa: E402
import watchdog as W  # noqa: E402


def _pk(day, raw, y, game):
    return {"league": "nfl", "day": day, "raw": raw, "y": y, "game": game}


# ══════════════════════════════════════════════════════════════════════
# 1. WALK-FORWARD: a week's mapping never sees its own week
# ══════════════════════════════════════════════════════════════════════
_p = []
for i in range(200):                       # week of 09-07: 90% printed, half hit
    _p.append(_pk("2026-09-%02d" % (7 + i % 7), 0.9, i % 2, "g%d" % i))
for i in range(300):                       # week of 09-14: 90% printed, ALL hit
    _p.append(_pk("2026-09-%02d" % (14 + i % 7), 0.9, 1, "h%d" % i))
_scored, _maps = K.walk_forward(_p)
_w2 = [s for s in _scored if s["week"] == "2026-09-14"]
ck(_w2 and max(s["cal"] for s in _w2) < 0.6,
   "🔴🔴 week 2 is corrected from week 1 ONLY (half hit -> ~50%), never from its own results",
   "⛔ Sam: 'using only picks graded before each week'. got %r" % (max(s["cal"] for s in _w2) if _w2 else None))
ck(_maps["2026-09-07"] is None and not [s for s in _scored if s["week"] == "2026-09-07"],
   "   ✅ ...and the first week, with nothing earlier, is not scored at all")

# ══════════════════════════════════════════════════════════════════════
# 2. THE PICKS: graded, rated rows of the card's own record only
# ══════════════════════════════════════════════════════════════════════
_tmp = tempfile.mkdtemp()
try:
    for lg in ("nfl", "ncaaf"):
        os.makedirs(os.path.join(_tmp, "data", lg, "latest"))
        rows = [{"confidence": 84, "won": True, "game": "A @ B", "commence": "2026-09-13T17:00:00Z"},
                {"confidence": 90, "won": None, "game": "A @ B", "commence": "2026-09-13T17:00:00Z"},
                {"confidence": None, "won": False, "game": "A @ B", "commence": "2026-09-13T17:00:00Z"}]
        with gzip.open(os.path.join(_tmp, "data", lg, "latest", "record-detail.json.gz"), "wt",
                       encoding="utf-8") as fh:
            json.dump({"days": {"2026-09-13": rows}}, fh)
    _loaded = K.load_picks(_tmp)
finally:
    shutil.rmtree(_tmp, ignore_errors=True)
ck(len(_loaded) == 2 and all(p["raw"] == 0.84 and p["y"] == 1 for p in _loaded),
   "🔴 only graded, rated picks are scored — a void and an unrated row are left out, both leagues read",
   "got %r" % _loaded)

# ══════════════════════════════════════════════════════════════════════
# 3. THE DECISION: sign, clustering by game, the 500 floor
# ══════════════════════════════════════════════════════════════════════
_s = [dict(_pk("2026-09-14", 0.9, 0, "g%d" % (i // 3)), cal=0.5) for i in range(600)]
_d = K.decision(_s)
ck(_d["mean_d"] > 0, "🔴🔴 a correction that predicts better has d > 0", "got %r" % _d["mean_d"])
ck(_d["clusters"] == 200,
   "🔴🔴 clustered by GAME — three picks of one game are one cluster",
   "⛔ Sam: 'clustered by game'. got %r" % _d["clusters"])
ck(K.decision(_s[:300])["verdict"] == "NOT YET MEASURABLE",
   "🔴 under 500 scored picks the verdict is NOT YET MEASURABLE, never a pass")
ck(K.verdict(600, 0.1, 0.01) == "QUALIFIES" and K.verdict(600, 0.1, 0.2) == "DOES NOT QUALIFY"
   and K.verdict(600, -0.1, 0.01) == "DOES NOT QUALIFY",
   "✅ QUALIFIES needs n ≥ 500, a lower loss and one-sided p < 0.05")

# ══════════════════════════════════════════════════════════════════════
# 4. THE BANDS: calibration.py's verdicts, still written for the page;
#    `[Sam, 2026-10-01]` the page itself draws none of them
# ══════════════════════════════════════════════════════════════════════
_tmp = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(_tmp, "data", "nfl", "latest"))
    json.dump({"calibration": [{"bucket": "80-90%", "stated": 84.1, "w": 20, "n": 49},
                               {"bucket": "60-70%", "stated": 65.0, "w": 30, "n": 48}]},
              open(os.path.join(_tmp, "data", "nfl", "latest", "record.json"), "w"))
    _b = {b["bucket"]: b for b in K.page_bands("nfl", _tmp)}
finally:
    shutil.rmtree(_tmp, ignore_errors=True)
ck(_b["80-90%"]["flag"] == "UNDER" and _b["60-70%"]["flag"] == "OK"
   and _b["80-90%"]["actual"] == {"value": 40.8, "basis": "DESCRIPTIVE"},
   "🔴 the page's bands carry calibration.py's own per-band verdict, labelled DESCRIPTIVE",
   "got %r" % _b)
# `[Sam, 2026-10-01]` This USED TO REQUIRE the stated-vs-actual table per
#    band next to the football props card (`fbCardCalHtml`, after the
#    `fbCalNote` pop-up) and its "these are the card's raw numbers" warning
#    (Sam, 2026-09-24). Sam has since removed every confidence pop-up from
#    the page -- *"we have a track record for a reason"* -- so it now
#    requires that NEITHER is drawn, nor even loaded. ⛔ The bands are still
#    built and still carry calibration.py's verdicts (the check above, and
#    `research/fb_card_calibration_spec.md`'s test is unchanged).
_html = os.path.join(ROOT, "index.html")
_pk_js = jsblock.js_block("fbPicks", _html)
_blocks = jsblock.top_level_blocks(_html)
ck("fbCardCalHtml" not in _pk_js and "fbCalNote" not in _pk_js
   and not ({"fbCardCalHtml", "fbCardCalLoad", "fbCalNote"} & set(_blocks))
   and "card-calibration.json" not in jsblock.source(_html),
   "🔴 [Sam, 2026-10-01] the page shows NO stated-vs-actual band table and no raw-numbers warning next to "
   "the card, and loads nothing from card-calibration.json (both used to be required)",
   "⛔ Sam: 'we have a track record for a reason' -- the bands stay in the data, never on the page")

# ══════════════════════════════════════════════════════════════════════
# 5. 🔴 §3a `[Sam, 2026-11-18]`: RE-REGISTERED ON THE METHOD THE CARDS PRINT NOW
#    "Same test and same 500-pick bar, counting only picks from the new
#    registration date on." A planted tree; no production row is read.
# ══════════════════════════════════════════════════════════════════════
section("5. §3a: the re-registered arm, on a planted tree")
OWN, HC, GE = "season-blend+props-own", "season-blend+props-own+game-HC", "season-blend+props-own+game-E"


def _row(tag, i, day, method, ko=None, lg="nfl"):
    c = 55 + (i * 37) % 40                       # 55-94, spread over the bands
    r = {"player": "%s-%d" % (tag, i), "market": "player_rush_yds", "side": "over", "confidence": c,
         "won": ((i * 7919 + len(tag)) % 100) < c - 12, "game": "%s G%d" % (lg, i % 9),
         "commence": ko if ko is not None else day + "T17:00:00Z"}
    if method is not None:
        r["card_method"] = method
    return r


def _day(monday, i):
    return (datetime.date.fromisoformat(monday) + datetime.timedelta(days=i % 7)).isoformat()


def plant(root, arm=True):
    """Both leagues' record-detail.json.gz and an NFL record.json. Tags: OLD (2025-only, a third
    with no method), FIX (season-blend), PM (+props-model), PRE (today's method, games before the
    registration date), IN (§3a counts it), OUT (today's method left out by its kickoff or its
    row, or another props method)."""
    days = {"nfl": {}, "ncaaf": {}}

    def put(lg, day, r):
        days[lg].setdefault(day, []).append(r)

    for lg, n1, n2 in (("nfl", 100, 40), ("ncaaf", 80, 30)):
        for i in range(n1):
            put(lg, _day("2026-09-07", i), _row("OLD", i, _day("2026-09-07", i),
                                                None if i % 3 == 0 else "2025-only", lg=lg))
        for i in range(n2):
            put(lg, _day("2026-09-14", i), _row("OLD", 1000 + i, _day("2026-09-14", i), "2025-only", lg=lg))
    for lg, n1, n2 in (("nfl", 90, 30), ("ncaaf", 70, 20)):
        for i in range(n1):
            put(lg, _day("2026-09-21", i), _row("FIX", i, _day("2026-09-21", i), "season-blend", lg=lg))
        for i in range(n2):
            put(lg, _day("2026-09-28", i), _row("FIX", 1000 + i, _day("2026-09-28", i), "season-blend", lg=lg))
    for i in range(10):
        put("nfl", "2026-10-09", _row("PM", i, "2026-10-09", "season-blend+props-model"))
    put("nfl", "2026-09-15", dict(_row("OLD", 9001, "2026-09-15", "2025-only"), won=None))
    put("nfl", "2026-09-15", dict(_row("OLD", 9002, "2026-09-15", "2025-only"), confidence=None))
    if arm:
        for lg, m in (("nfl", OWN), ("ncaaf", HC)):
            for i in range(100):                 # enough to fit a mapping, were they read
                put(lg, _day("2026-11-09", i), _row("PRE", i, _day("2026-11-09", i), m, lg=lg))
            for i in range(90 if lg == "nfl" else 80):
                put(lg, _day("2026-11-23", i), _row("IN", i, _day("2026-11-23", i), m, lg=lg))
            for i in range(25):                  # 11-30 .. 12-03; a fifth of NFL's under "+game-E"
                d = _day("2026-11-30", i % 4)
                put(lg, d, _row("IN", 1000 + i, d, GE if (lg == "nfl" and i % 5 == 0) else m, lg=lg))
        # a Sunday card whose Monday-night game kicks off 2026-11-24T01:15Z, Monday 11-23 ET: IN
        put("nfl", "2026-11-22", _row("IN", 2000, "2026-11-22", OWN, ko="2026-11-24T01:15:00Z"))
        # a Sunday-night game at 2026-11-23T01:20Z is Sunday 11-22 ET: OUT
        put("nfl", "2026-11-22", _row("OUT", 1, "2026-11-22", OWN, ko="2026-11-23T01:20:00Z"))
        # other props methods after registration (a props switch, signal 9): OUT
        put("ncaaf", "2026-12-05", _row("OUT", 2, "2026-12-05", "season-blend+props-own-last2+game-HC", lg="ncaaf"))
        put("ncaaf", "2026-12-06", _row("OUT", 3, "2026-12-06", "season-blend+props-own-last2", lg="ncaaf"))
        put("nfl", "2026-12-03", _row("OUT", 4, "2026-12-03", "season-blend+signal9+props-own"))
        # no readable kickoff, a void, an unrated row: OUT
        put("nfl", "2026-12-01", dict(_row("OUT", 5, "2026-12-01", OWN), commence=None))
        put("nfl", "2026-12-01", dict(_row("OUT", 6, "2026-12-01", OWN), won=None))
        put("nfl", "2026-12-01", dict(_row("OUT", 7, "2026-12-01", OWN), confidence=None))
    for lg in ("nfl", "ncaaf"):
        os.makedirs(os.path.join(root, "data", lg, "latest"), exist_ok=True)
        with gzip.open(os.path.join(root, "data", lg, "latest", "record-detail.json.gz"), "wt",
                       encoding="utf-8") as fh:
            json.dump({"days": days[lg]}, fh)
    with open(os.path.join(root, "data", "nfl", "latest", "record.json"), "w", encoding="utf-8") as fh:
        json.dump({"calibration": [{"bucket": "80-90%", "stated": 84.1, "w": 20, "n": 49},
                                   {"bucket": "60-70%", "stated": 65.0, "w": 30, "n": 48}]}, fh)


def _r9(x):
    if isinstance(x, float):
        return round(x, 9)
    if isinstance(x, dict):
        return {k: _r9(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_r9(v) for v in x]
    return x


# Every key the build wrote before §3a (its clock aside). ⛔ PINNED from the code BEFORE §3a
#    (f17346b98) on this tree, at 9 decimals (a last-bit difference in a platform's math library
#    must not read as a change): the earlier arms and the page's bands are what they were.
#    Measured 2026-11-18: the base module (f17346b98) and this one write the same 11,856 bytes of
#    these keys on this tree unrounded (sorted JSON, `superseded_by` left out), and so this digest.
BASE_KEYS = ("league", "kind", "spec", "bands", "bands_before", "method_now", "test", "test_after_fix",
             "log_loss", "scored_bands", "mappings", "note")
BASE_DIGEST = "596a068c0c28c8ffa34f1c13d90b927d70b66212d1826ad995b908c4b493b7c2"


def _before(doc):
    out = {k: doc.get(k) for k in BASE_KEYS}
    for k in ("test", "test_after_fix"):
        out[k] = {a: b for a, b in (out[k] or {}).items() if a != "superseded_by"}
    return _r9(out)


def _builds(arm=True):
    t = tempfile.mkdtemp(prefix="cal-")
    try:
        plant(t, arm)
        got = {}
        for lg in ("nfl", "ncaaf"):
            p = os.path.join(t, "out-%s.json" % lg)
            K.build(lg, t, p)
            got[lg] = json.load(open(p, encoding="utf-8"))
        return got, K.load_picks(t, keep=K.counts), K.newest_graded(t)
    finally:
        shutil.rmtree(t, ignore_errors=True)


_docs, _arm, _newest = _builds()
_who = {p["player"] for p in _arm}
eq((sorted({w.split("-")[0] for w in _who}), len(_arm)), (["IN"], 90 + 80 + 25 + 25 + 1),
   "🔴🔴 the arm reads exactly the rows §3a counts: today's props method, kickoff on or after "
   "2026-11-23 ET; never one before it (PRE), another props method, a void, an unrated row or a row "
   "with no kickoff (OUT)")
eq((sum(p["league"] == "ncaaf" for p in _arm),
    sum(p["league"] == "nfl" and p["player"].startswith("IN-1") and len(p["player"]) == 7
        and int(p["player"][3:]) % 5 == 0 for p in _arm)),
   (105, 5),
   "🔴 ...a \"+game-HC\" card (college) and a \"+game-E\" card are the same props method: they count")
ck("IN-2000" in _who and "OUT-1" not in _who,
   "🔴 ...the kickoff's EASTERN day decides: Monday night 01:15Z counts, Sunday night 01:20Z does not")
_rr = _docs["nfl"][K.REREG_KEY]
eq((_rr["graded_picks"], _rr["n"], _rr["verdict"], _rr["min_n"], _rr["alpha"], _rr["method"],
    _rr["registered_from"]),
   (221, 50, "NOT YET MEASURABLE", 500, 0.05, OWN, "2026-11-23"),
   "🔴🔴 the walk-forward trains only on the arm's own picks: the 171 of its first weeks train, the 50 "
   "after are scored (the 200 earlier PRE rows would have given week one a mapping); §3's bar, unchanged")
ck(all(_docs[lg][k].get("superseded_by") == K.SUPERSEDED for lg in _docs for k in ("test", "test_after_fix"))
   and "§3a" in (K.SUPERSEDED or "") and "2026-11-18" in (K.SUPERSEDED or "")
   and not _rr.get("superseded_by"),
   "🔴 the earlier arms are still stored, labelled superseded by §3a with its date; the new arm is not",
   "got %r" % {lg: _docs[lg]["test"].get("superseded_by") for lg in _docs})
_dig = hashlib.sha256(json.dumps({lg: _before(_docs[lg]) for lg in ("nfl", "ncaaf")},
                                 sort_keys=True).encode()).hexdigest()
eq(_dig, BASE_DIGEST, "🔴🔴 every number the build wrote before §3a is unchanged: the 2025-only test, the "
   "after-fix arm, their bands, log loss and mappings, the page's band tables")
eq(sorted(set(_docs["nfl"]) - set(BASE_KEYS)), ["built_at", K.REREG_KEY],
   "   ...and the file gains only the new arm")
_docs0, _arm0, _ = _builds(arm=False)
_old = ("test", "test_after_fix", "log_loss", "scored_bands", "mappings")
ck(all(json.dumps({k: _docs[lg][k] for k in _old}, sort_keys=True)
       == json.dumps({k: _docs0[lg][k] for k in _old}, sort_keys=True) for lg in _docs)
   and not _arm0 and _docs0["nfl"][K.REREG_KEY]["graded_picks"] == 0,
   "🔴 the earlier arms are byte-identical with or without today's rows; with none, the new arm reads nothing")
eq(_newest, {"nfl": {"method": "2026-12-03", "any": "2026-12-03"},
             "ncaaf": {"method": "2026-12-03", "any": "2026-12-06"}},
   "🔴 each league's newest graded day of the arm's method, and of any method (what the watchdog reads)")
eq(_rr["newest_graded"], _newest, "   ...and the arm stores it")

# the spec and the code say the same thing
_spec = open(os.path.join(ROOT, "research", "fb_card_calibration_spec.md"), encoding="utf-8").read()
_3a = _spec[_spec.find("\n## 3a. "):_spec.find("\n## 4. ")]
_m = re.search(r"(?m)^\| The method \| `([^`]+)`", _3a)
_d = re.search(r"(?m)^\| The registration date \| \*\*(\d{4}-\d\d-\d\d)\*\*", _3a)
eq((_m and _m.group(1), _d and _d.group(1)), (K.REREG_METHOD, K.REREG_FROM),
   "🔴🔴 the code's registered method and date are §3a's own")
ck(K.F.monday(K.REREG_FROM) == K.REREG_FROM, "   ...and the date is a Monday (§3's weeks start on one)")

# ══════════════════════════════════════════════════════════════════════
# 6. 🔴 METHOD IDENTITY, DERIVED FROM card_fb, NEVER A HAND LIST
# ══════════════════════════════════════════════════════════════════════
section("6. §3a: a card's props method, from card_fb's own pieces")
# card_fb writes a card's method as ONE expression. §3a's rule needs the game model's part
# (game_method) to be the LAST piece of it, so that everything before it is the props method.
_src = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
_vals = [n.values[[getattr(k, "value", None) for k in n.keys].index("card_method")]
         for n in ast.walk(ast.parse(_src)) if isinstance(n, ast.Dict)
         and "card_method" in [getattr(k, "value", None) for k in n.keys]]
eq([isinstance(v, ast.BinOp) and isinstance(v.op, ast.Add) and isinstance(v.right, ast.Call)
    and getattr(v.right.func, "id", None) for v in _vals], ["game_method"],
   "🔴🔴 card_fb.py writes card_method in ONE place, and the game model's part is the last piece of it")
ck(sum(isinstance(n, ast.Call) and getattr(n.func, "id", None) == "game_method"
       for v in _vals for n in ast.walk(v)) == 1,
   "   ...and appears in it once, so nothing after it can be mistaken for the game model's")
_saved = dict(C.PROPS_SEASONS)
_combos = []
try:
    for base in (C.METHOD_FIXED, C.METHOD_FIXED_S9, C.METHOD_CURRENT):
        for seasons in ("all", C.LAST_TWO):
            C.PROPS_SEASONS["nfl"] = seasons
            for champ in (None, "HC", "E", "SMC"):
                props = base + C.METHOD_PROPS_MODEL + C.props_suffix("nfl")
                _combos.append((props + C.game_method({"champion": champ} if champ else {}), props))
finally:
    C.PROPS_SEASONS.clear()
    C.PROPS_SEASONS.update(_saved)
_bad = [(m, want, K.props_method(m)) for m, want in _combos if K.props_method(m) != want]
ck(not _bad and len(_combos) == 24,
   "🔴🔴 every method card_fb can build (base, signal 9, props switch, any champion) has as its "
   "props method itself less game_method's part", "got %r" % _bad[:3])
eq(sorted({m for m, _p in _combos if K.counts({"card_method": m, "commence": "2026-11-23T17:00:00Z"})}),
   sorted(C.METHOD_FIXED + C.METHOD_PROPS_MODEL + C.game_method({"champion": c} if c else {})
          for c in (None, "HC", "E", "SMC")),
   "🔴 ...so the arm counts today's props method under any game champion, and no other")
for _lg in ("nfl", "ncaaf"):
    _base = C.METHOD_FIXED_S9 if (C.CARD_METHOD == C.METHOD_FIXED and C.S9_CARD.get(_lg)) else C.CARD_METHOD
    note("this tree's card_fb prints %s cards' props method as %s (the arm's: %s)" % (
        _lg, _base + C.METHOD_PROPS_MODEL + C.props_suffix(_lg), K.REREG_METHOD))

# ══════════════════════════════════════════════════════════════════════
# 7. 🔴 THE WATCHDOG: AN ARM ITS LEAGUE STOPPED FEEDING IS SAID, THE OFF-SEASON IS NOT
# ══════════════════════════════════════════════════════════════════════
section("7. watchdog.check_calibration_arm, on planted files and a pinned clock")
NOW = datetime.datetime(2026, 12, 20, 15, 0, tzinfo=datetime.timezone.utc)       # 12-20 ET


def _watch(files, now=NOW):
    """{league: card-calibration.json} -> [(key, severity, repair)]."""
    t = tempfile.mkdtemp(prefix="calwd-")
    saved = W.ROOT
    try:
        for lg, doc in files.items():
            os.makedirs(os.path.join(t, "data", lg, "latest"))
            with open(os.path.join(t, "data", lg, "latest", "card-calibration.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(doc, fh)
        W.ROOT = t
        rep = W.Report()
        W.check_calibration_arm(rep, now)
        return [(i["key"], i["severity"], i["repair"]) for i in rep.items]
    finally:
        W.ROOT = saved
        shutil.rmtree(t, ignore_errors=True)


def _file(lg, seen, method=OWN, since="2026-11-23", superseded=None):
    arm = {"verdict": "NOT YET MEASURABLE", "n": 0, "method": method, "registered_from": since,
           "newest_graded": {lg: seen}}
    if superseded:
        arm["superseded_by"] = superseded
    return {K.REREG_KEY: arm}


_KEY = "calibration:%s:" + K.REREG_KEY
_starved = {"method": "2026-12-01", "any": "2026-12-19"}
eq(_watch({"nfl": _file("nfl", _starved),
           "ncaaf": _file("ncaaf", {"method": "2026-12-01", "any": "2026-12-01"})}),
   [(_KEY % "nfl", "DEGRADED", None)],
   "🔴🔴 NFL graded card rows yesterday but none of the arm's method for 19 days: DEGRADED, no repair; "
   "college graded nothing for 19 days either (the off-season): silent")
eq(_watch({"nfl": _file("nfl", {"method": "2026-12-18", "any": "2026-12-19"})}), [],
   "   ✅ an arm fed two days ago is silent")
eq((_watch({"nfl": _file("nfl", {"method": "2026-12-06", "any": "2026-12-19"})}),
    _watch({"nfl": _file("nfl", {"method": "2026-12-05", "any": "2026-12-19"})})),
   ([], [(_KEY % "nfl", "DEGRADED", None)]),
   "🔴 \"more than 14 days\": 14 days is silent, 15 is DEGRADED")
eq((_watch({"ncaaf": _file("ncaaf", {"method": None, "any": "2026-12-19"})}),
    _watch({"ncaaf": _file("ncaaf", {"method": None, "any": "2026-11-29"})},
           now=datetime.datetime(2026, 11, 30, 15, 0, tzinfo=datetime.timezone.utc))),
   ([(_KEY % "ncaaf", "DEGRADED", None)], []),
   "🔴 an arm whose method its league NEVER graded counts from registration: 27 days is DEGRADED, 7 is not")
eq(_watch({"nfl": _file("nfl", _starved, method="2025-only", since="2026-09-24", superseded=K.SUPERSEDED)}),
   [], "🔴 a superseded arm is never reported, however starved")
eq(_watch({}), [], "   ✅ no file, nothing said")
eq(_watch({"nfl": ["not", "an", "object"]}), [], "   ✅ a file that is not an object: nothing said, and no crash")
ck(W.check_calibration_arm in W.CHECKS, "🔴 the check is registered, so the real watchdog runs it")
# The writer's own files, read by the reader: the planted tree's build, a fortnight on.
eq(_watch({lg: _docs[lg] for lg in _docs},
          now=datetime.datetime(2026, 12, 19, 15, 0, tzinfo=datetime.timezone.utc)),
   [(_KEY % "ncaaf", "DEGRADED", None)],
   "🔴🔴 on the build's own files: college changed its props method on 12-05 and still grades rows, so it "
   "is DEGRADED 16 days after its last counted card; NFL went quiet that day, so it is silent; the "
   "superseded arms are never reported")

# `[2026-11-19, review]` THE ARM'S OWN RULE DECIDES WHETHER IT IS FED. Every row of today's method
#    after registration, but none the arm can count: NFL's kickoffs lack their seconds (et_date reads
#    none), college's have no kickoff at all. Both leagues keep grading them daily. A rule looser
#    than the arm's (its props method, any kickoff) read that as fed, and an arm stuck at 0 was
#    never reported.
def _plant_unreadable(root):
    days = {"nfl": {}, "ncaaf": {}}
    for k in range(28):                                   # cards 2026-11-23 .. 2026-12-20
        d = (datetime.date(2026, 11, 23) + datetime.timedelta(days=k)).isoformat()
        for i in range(6):
            days["nfl"].setdefault(d, []).append(_row("UNR", k * 6 + i, d, OWN, ko=d + "T18:00Z"))
            days["ncaaf"].setdefault(d, []).append(
                dict(_row("UNR", k * 6 + i, d, HC, lg="ncaaf"), commence=None))
    for lg in ("nfl", "ncaaf"):
        os.makedirs(os.path.join(root, "data", lg, "latest"), exist_ok=True)
        with gzip.open(os.path.join(root, "data", lg, "latest", "record-detail.json.gz"), "wt",
                       encoding="utf-8") as fh:
            json.dump({"days": days[lg]}, fh)


_tu = tempfile.mkdtemp(prefix="calunr-")
try:
    _plant_unreadable(_tu)
    _du = {}
    for _lg in ("nfl", "ncaaf"):
        _p = os.path.join(_tu, "out-%s.json" % _lg)
        K.build(_lg, _tu, _p)
        _du[_lg] = json.load(open(_p, encoding="utf-8"))
    _nu = K.newest_graded(_tu)
finally:
    shutil.rmtree(_tu, ignore_errors=True)
eq(([_du[lg][K.REREG_KEY]["graded_picks"] for lg in ("nfl", "ncaaf")], _nu),
   ([0, 0], {"nfl": {"method": None, "any": "2026-12-20"}, "ncaaf": {"method": None, "any": "2026-12-20"}}),
   "🔴🔴 28 days of today's method the arm cannot count (no readable kickoff): it reads 0, and so does "
   "its newest counted day, while both leagues graded rows yesterday")
eq(_watch({lg: _du[lg] for lg in _du}, now=datetime.datetime(2026, 12, 21, 15, 0, tzinfo=datetime.timezone.utc)),
   [(_KEY % "nfl", "DEGRADED", None), (_KEY % "ncaaf", "DEGRADED", None)],
   "🔴🔴 ...so the watchdog says it, in both leagues: DEGRADED 28 days after registration with nothing counted")
