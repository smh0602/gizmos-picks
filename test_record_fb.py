#!/usr/bin/env python3
"""
THE FOOTBALL GRADER.

`claude/football-todo.md` had carried this since 2026-09-04: *"it will
not do what the name implies until football picks are being GRADED — and
nothing grades them yet. A football grader is owed."*

🔴 THIS TEST RUNS THE REAL GRADER AND RE-DERIVES ITS ANSWERS BY HAND.
Every graded row is recomputed straight out of the raw log — not through
`card_fb.MARKETS`, not through `record_fb` — and the two must agree on
BOTH the actual number and the verdict. ⛔ A grader checked only against
itself is a grader that cannot be wrong.

The three measurements the grader is built on are re-measured here rather
than trusted from its docstring, because each one is a claim about a FEED
and a feed can change:
  1. the two leagues date a game differently (college UTC, NFL Eastern)
  2. an NFL log row does NOT mean he played (68% have zero snaps)
  3. college omits a category instead of writing a zero
"""
# ══════════════════════════════════════════════════════════════════════
# @vacuity every graded row lands in its method's buckets — none dropped
#   file: record_fb.py
#   find: for m, bk in per.items()}
#   with: for m, bk in per.items() if m == current}
#
# @vacuity `calibration` is the CURRENT method's buckets, not another's
#   file: record_fb.py
#   find: return out.get(current, []), out
#   with: return out.get(METHOD_BEFORE, []), out
#
# @vacuity 🔴🔴 PLANTED: a rated row reaches the record WITH its n_games
#   file: record_fb.py
#   find: "n_games": _n_games,
#   with: "n_games": None,
#
# @vacuity ⛔ PLANTED: the denominator is an INTEGER, never a string
#   file: record_fb.py
#   find: "n_games": _n_games,
#   with: "n_games": str(_n_games) if _n_games is not None else None,
#
# @vacuity 🔴🔴 PLANTED: logs_season is CARRIED from the card
#   file: record_fb.py
#   find: "logs_season": card.get("logs_season"),
#   with: "logs_season": None,
#
# @vacuity 🔴 PLANTED: the grader's verdicts are the known ones (the hand control disagrees otherwise)
#   file: record_fb.py
#   find: return (val > line) if side == "over" else (val < line)
#   with: return (val < line) if side == "over" else (val > line)
#
# @vacuity 🔴 PLANTED: the `-latest.json` pointer is never graded as a card
#   file: record_fb.py
#   find: if f.endswith("-latest.json"):
#   with: if False:
#
# @vacuity every market the grader can grade has an independent hand reader
#   file: card_fb.py
#   find: "player_pass_tds":      (lambda g: float(g.get("pass_td") or 0),  "pass TD"),
#   with: "player_pass_tdz":      (lambda g: float(g.get("pass_td") or 0),  "pass TD"),
#
# @vacuity [Sam, 2026-10-01] the record tab prints no coverage sentence
#   file: index.html
#   find: <tbody>${dayRows}</tbody></table>`);
#   with: <tbody>${dayRows}</tbody></table>${R && R.coverage_note ? `<div class="fnote"><b>What is and is not counted.</b> ${R.coverage_note}<br><br>${R.over_bias_note || ''}</div>` : ''}`);
#
# @vacuity [Sam, 2026-10-01] ...and no concentration warning
#   file: index.html
#   find: ${hero}
#   with: ${hero}${graded && R.distinct_players ? `<div class="fnote"><b>${O.n} graded rows came from ${R.distinct_players} players.</b></div>` : ''}
# ══════════════════════════════════════════════════════════════════════
import glob
import gzip
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta
from tcheck import ck, note, copy_module  # ⚠️ copies the SUBJECT'S OWN IMPORTS too — a hand-listed
#                                 fixture went red on all four harnesses at once
#                                 the day card_fb.py gained one import

ROOT = os.path.dirname(os.path.abspath(__file__))
FAIL = []


def load(p):
    return json.load(gzip.open(p, "rt")) if p.endswith(".gz") else json.load(open(p))


# ───────────────────────────────────────────────────────────────
print("\n═══ 1. THE THREE FEED FACTS, RE-MEASURED ═══")

L25 = load(f"{ROOT}/data/ncaaf/latest/players-2025.json.gz")
N25 = load(f"{ROOT}/data/nfl/latest/players-2025.json.gz")
crows = [g for pl in L25["players"].values() for g in (pl.get("g") or [])]
nrows = [g for pl in N25["players"].values() for g in (pl.get("g") or [])]

# (3) college omits a category; the NFL writes the zero
cpres = [g["rec"] for g in crows if "rec" in g]
npres = [g["rec"] for g in nrows if "rec" in g]
czero = sum(1 for v in cpres if v == 0) / len(cpres)
nzero = sum(1 for v in npres if v == 0) / len(npres)
ck("college essentially never writes an explicit zero",
   czero < 0.02, "rec == 0 in %.1f%% of the rows that have it" % (100 * czero))
ck("the NFL writes zeros constantly",
   nzero > 0.5, "rec == 0 in %.1f%%" % (100 * nzero))
ck("every NFL row carries every market field",
   all(k in nrows[0] for k in ("rec", "rec_yds", "rush_yds", "pass_yds")),
   "so an absent key there would be a real absence, not a zero")
note("⛔ that asymmetry is why absence means ZERO in college and cannot "
     "happen in the NFL — read either one the other way and the record is wrong")

# (2) an NFL log row does not mean he played
zsnap = sum(1 for g in nrows if (g.get("snaps") or 0) == 0)
ck("an NFL log row does NOT imply he took a snap",
   zsnap / len(nrows) > 0.5,
   "%d of %d rows have snaps == 0 — grading those would hand a WIN to "
   "every UNDER on a man who never played" % (zsnap, len(nrows)))

# (1) the date conventions, measured against each league's own schedule
def date_agreement(lg, season):
    S = load(f"{ROOT}/data/{lg}/latest/schedule-{season}.json.gz")
    sched = {str(g.get("id") or g.get("game_id")): g for g in S["games"]}
    P = load(f"{ROOT}/data/{lg}/latest/players-{season}.json.gz")["players"]
    seen, utc, et = set(), 0, 0
    from datetime import timezone
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
    for pl in P.values():
        for g in pl.get("g") or []:
            gid = str(g.get("game_id"))
            if gid in seen or gid not in sched:
                continue
            seen.add(gid)
            st = sched[gid].get("start") or ""
            if g.get("d") == st[:10]:
                utc += 1
            if st.endswith("Z"):
                try:
                    t = datetime.strptime(st.replace(".000Z", "Z"),
                                          "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    if g.get("d") == t.astimezone(ET).strftime("%Y-%m-%d"):
                        et += 1
                except Exception:
                    pass
    return len(seen), utc, et


n, utc, et = date_agreement("ncaaf", 2026)
ck("the college log dates a game by its raw feed timestamp, not ET",
   n and utc == n and et < n,
   "%d games: %d match the feed's own date, only %d match ET — a Thursday "
   "9pm ET kickoff logs as FRIDAY" % (n, utc, et))
n2, utc2, _ = date_agreement("nfl", 2025)
ck("the NFL log dates a game by its schedule's (Eastern) date",
   n2 and utc2 == n2, "%d of %d games" % (utc2, n2))
note("⛔ the two conventions differ, so an exact-date join is wrong in one "
     "league — the grader uses a ±1 day window instead")

# ⛔ AND THE WINDOW IS ONLY SAFE IF A PLAYER CANNOT HAVE TWO GAMES IN IT.
worst = 0
for pl in list(L25["players"].values()) + list(N25["players"].values()):
    ds = sorted(datetime.strptime(g["d"], "%Y-%m-%d")
                for g in (pl.get("g") or []) if g.get("d"))
    for i, a in enumerate(ds):
        worst = max(worst, sum(1 for b in ds if abs((b - a).days) <= 1))
ck("no player has two games inside any three-day window",
   worst == 1,
   "max %d — football is weekly, so the window join cannot pick the wrong "
   "game" % worst)

# ───────────────────────────────────────────────────────────────
print("\n═══ 2. THE GRADER RUNS, AND THE PAGE READS WHAT IT WRITES ═══")
os.environ["LEAGUE"] = "ncaaf"
sys.path.insert(0, ROOT)
import record_fb  # noqa: E402

# 🔴 IN A THROWAWAY COPY, NOT THE REPO. `[fixed 2026-09-06]`
# ⛔ THIS USED TO RUN THE GRADER IN THE REPO ROOT, so every CI run
# rewrote `data/ncaaf/latest/record.json` — and the tests run in the SAME
# JOB that later does `git add data/ picks/`, so the file was being
# COMMITTED by every collect run of every league, MLB included. Measured
# on live main: `built_at` 04:16:46Z inside a `collect[mlb]` commit.
# 🔴 THE CONTENT WAS FINE; THE MONITOR WAS NOT. The freshness contract
# watches that file's age to prove THE GRADER ran, and a test rewriting
# it hourly makes that row permanently green — a check that can no longer
# fail. `tcheck.py` now refuses any test that writes under data/ or
# picks/, which is the shape fix rather than a rule.
import shutil      # noqa: E402
import tempfile    # noqa: E402
_tmp = tempfile.mkdtemp()
shutil.copytree(f"{ROOT}/data/ncaaf", f"{_tmp}/data/ncaaf")
shutil.copytree(f"{ROOT}/picks", f"{_tmp}/picks")
_cwd = os.getcwd()
try:
    os.chdir(_tmp)
    rc = record_fb.main()
finally:
    os.chdir(_cwd)
ck("record_fb exits clean", rc == 0)
R = load(f"{_tmp}/data/ncaaf/latest/record.json")
D = load(f"{_tmp}/data/ncaaf/latest/record-detail.json.gz")
# ⛔ THE INVARIANT IS THAT BOTH FILES ARE WRITTEN WITH THE RIGHT SHAPE,
#    not that either has rows in it. `bool(D["days"])` failed the moment
#    the record was wiped — an empty day map is a legitimate state and an
#    artifact that correctly did nothing must still exist (rule 86).
ck("it writes both the totals and the per-row detail",
   isinstance(R.get("overall"), dict) and isinstance(D.get("days"), dict),
   "overall=%s days=%d" % (R.get("overall"), len(D.get("days") or {})))
if not D.get("days"):
    note("⚠️ the detail file is EMPTY — expected while the record counts "
         "from " + str(R.get("record_from", "its start date")))
ck("the record is labelled DESCRIPTIVE and RECORD, never MODEL",
   R["kind"] == "DESCRIPTIVE" and R["basis"] == "RECORD"
   and "MODEL" not in json.dumps(R.get("calibration_by_method")).upper(),
   "ledger rule 55 — football has no model to calibrate")
ck("the calibration column is headed `stated`, not `predicted`",
   all("stated" in c for v in (R.get("calibration_by_method") or {}).values()
       for c in v),
   "a record is not a forecast")

# ⛔ THE POINTER FILE MUST NOT BE GRADED TWICE.
have = sorted(os.path.basename(f) for f in glob.glob(f"{ROOT}/picks/fb-ncaaf-*.json"))
# ⚠️ THE RECORD FLOOR CHANGES WHAT "ALL THE CARDS" MEANS. Since
#    2026-09-06 the grader sets aside cards dated before `RECORD_FROM`
#    (Sam: "wipe the track record"), so the count to compare against is
#    the dated files ON OR AFTER that date — not every file on disk.
_dated = [h for h in have if not h.endswith("-latest.json")]
import record_fb as _rfb  # noqa: E402
_eligible = [h for h in _dated if h[len("fb-ncaaf-"):-len(".json")]
             >= _rfb.RECORD_FROM]
# 🔴 AND A CARD WITH NO ROWS IS NOT A CARD THE GRADER SEES. `[2026-09-10]`
#    The college card for that Thursday held **zero picks** — nothing was
#    priced — and `record_fb` drops it deliberately:
#    `days = [d for d in days if d["carded"]]`. So `cards_seen` read 1
#    against 2 eligible files and this check went red on a grader that was
#    behaving exactly as written.
# ⛔ THE CHECK'S REAL QUESTION IS UNCHANGED AND STILL SHARP: is the
#    POINTER FILE being graded as a card of its own? If it were,
#    `cards_seen` would be one HIGHER than the carded dated files — which
#    this still catches. What is removed is a second, accidental claim
#    that every dated file carries rows.
_carded = []
for _h in _eligible:
    try:
        with open(os.path.join(ROOT, "picks", _h)) as _fh:
            if json.load(_fh).get("picks"):
                _carded.append(_h)
    except Exception:
        _carded.append(_h)      # unreadable -> count it, never hide it
# 🔴 `[2026-09-28]` ASKED OF THE LIVE TREE ONLY WHEN IT HOLDS THE CASE. The
#    pointer question bites only if the pointer itself carries rows (a
#    grader that graded an EMPTY pointer would drop it again), and a card
#    whose season log is not stored yet (the first card of a new season)
#    is skipped by the grader while this count kept it — red on correct
#    code at every season rollover. ✅ The planted tree in §3b asks it every
#    run; here the count is cards the grader CAN grade, derived from the
#    tree (the log file exists), never from the grader's own skip list.
_carded = [h for h in _carded
           if os.path.exists(f"{ROOT}/data/ncaaf/latest/players-%s.json.gz"
                             % h[len("fb-ncaaf-"):len("fb-ncaaf-") + 4])]
_ptr = f"{ROOT}/picks/fb-ncaaf-latest.json"
_ptr_rows = bool(os.path.exists(_ptr) and (load(_ptr).get("picks") or []))
if _ptr_rows:
    ck("`-latest.json` exists and is NOT counted as its own card",
       "fb-ncaaf-latest.json" in have and R["cards_seen"] == len(_carded),
       "%d cards seen, %d dated file(s) on disk, %d on or after the record "
       "floor %s, %d of those carrying rows with a stored log"
       % (R["cards_seen"], len(_dated), len(_eligible), _rfb.RECORD_FROM,
          len(_carded)))
else:
    note("⚠️ NOT EXERCISED ON THE LIVE TREE: the college pointer %s — a "
         "grader that counted it would not show. §3b's planted pointer asks it."
         % ("holds no rows" if os.path.exists(_ptr) else "is not on disk"))
if len(_carded) < len(_eligible):
    note("⚠️ %d eligible card(s) hold ZERO rows, or have no stored season "
         "log yet, and are not graded — a day with nothing priced is a "
         "legitimate empty (rule 144), and the file still exists on disk "
         "(rule 86)."
         % (len(_eligible) - len(_carded)))
if len(_eligible) < len(_dated):
    note(f"⚠️ {len(_dated) - len(_eligible)} card(s) predate the floor and "
         f"are deliberately not graded — the files are untouched")

# ───────────────────────────────────────────────────────────────
print("\n═══ 3. THE CONTROL — EVERY GRADED ROW RE-DERIVED BY HAND ═══")
# ⛔ Deliberately NOT through card_fb.MARKETS or record_fb. If the reader
#    is wrong, both the grader and a test that reuses it are wrong together.


def hand_norm(n):
    """Fold a name INDEPENDENTLY of the grader, but not more crudely.

    🔴 THIS DROPPED SEVEN ROWS AND BLAMED THE RECORD FOR IT.
    `[2026-09-10]` The control reported *"40 agree, 7 disagree"* the hour
    the college log was rebuilt. **None of the seven was a grading
    error.** The card writes `Samuel Singleton Jr.`; the stats feed
    writes `Samuel Singleton`. This function kept `jr` as part of the
    name, so it looked up `samuelsingletonjr`, found nothing, and counted
    a MISS as a DISAGREEMENT.
    ⛔ A generational suffix differing between two feeds is a fact about
    NAMES, not a fact about this repo's grader — so handling it here is
    still an independent re-derivation, not a copy of `card_fb.norm()`.
    The control keeps its whole point: it computes every VALUE from the
    log itself and can still disagree with the grader about any of them.
    ⚠️ What it must NOT do is silently become easier. It did not: the
    value comparison below is untouched, and a row this function cannot
    resolve is now counted and BOUNDED rather than folded into the
    disagreement total, where it was misreported as "name not unique".
    """
    n = unicodedata.normalize("NFKD", str(n or ""))
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower()
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", " ", n)
    return re.sub(r"[^a-z]", "", n)


HAND = {
    "player_pass_yds":      lambda g: (g.get("pass_yds") or 0),
    "player_pass_tds":      lambda g: (g.get("pass_td") or 0),
    "player_rush_yds":      lambda g: (g.get("rush_yds") or 0),
    "player_reception_yds": lambda g: (g.get("rec_yds") or 0),
    "player_receptions":    lambda g: (g.get("rec") or 0),
    "player_anytime_td":    lambda g: (g.get("rec_td") or 0) + (g.get("rush_td") or 0),
}

# ⛔ EVERY MARKET THE GRADER CAN GRADE HAS AN INDEPENDENT HAND READER.
#    `[2026-09-28]` A market added to `card_fb.MARKETS` without one used to
#    surface as a KeyError the day the first card carrying it was graded —
#    on production's timing, not in the PR that added it.
ck("every market the grader can grade has a hand reader here",
   set(record_fb.card_fb.MARKETS) <= set(HAND),
   "missing: %s" % sorted(set(record_fb.card_fb.MARKETS) - set(HAND)))


def hand_control(days, players_of):
    """Every graded row re-derived from the raw log. -> (agree, dis,
    mismatch, unverifiable). ⛔ ONE copy, run on the live record AND on the
    planted trees below."""
    agree = dis = 0
    mismatch = []
    unverifiable = []
    for date, rows in days.items():
        P = players_of(int(date[:4]))
        byname = {}
        for pl in P.values():
            byname.setdefault(hand_norm(pl.get("name")), []).append(pl)
        for r in rows:
            if r["won"] is None:
                continue
            # 🔴 "NOT IN THE LOG" AND "AMBIGUOUS" ARE DIFFERENT FACTS, AND
            #    THIS REPORTED BOTH AS "name not unique by hand".
            #    `[2026-09-10]` `len(cands) != 1` is true for ZERO matches as
            #    well as two, so a player the hand lookup simply could not
            #    find was announced as a duplicate — the wrong cause, which
            #    is the failure mode this project keeps paying for.
            # ⚠️ Neither is a grading disagreement: the control could not
            #    RUN on that row. Counted separately and bounded below, so it
            #    can never quietly stop verifying.
            cands = byname.get(hand_norm(r["player"]), [])
            if len(cands) == 0:
                unverifiable.append((r["player"], "not found in the log"))
                continue
            if len(cands) > 1:
                unverifiable.append((r["player"],
                                     "%d players share this name — the "
                                     "grader disambiguates by game, the hand "
                                     "check cannot" % len(cands)))
                continue
            t = datetime.strptime(r["commence"][:10], "%Y-%m-%d")
            hits = [g for g in cands[0]["g"]
                    if abs((datetime.strptime(g["d"], "%Y-%m-%d") - t).days) <= 1]
            if len(hits) != 1:
                # ⚠️ Also a control that could not run, not a wrong grade.
                unverifiable.append((r["player"],
                                     "%d games in the +/-1 day window" % len(hits)))
                continue
            v = float(HAND[r["market"]](hits[0]))
            if r["side"] == "yes":
                w = v >= 1
            elif r["side"] == "over":
                w = v > r["line"]
            else:
                w = v < r["line"]
            if v == r["actual"] and bool(w) == r["won"]:
                agree += 1
            else:
                dis += 1
                mismatch.append((r["player"], r["market"], "grader", r["actual"],
                                 r["won"], "hand", v, w))
    return agree, dis, mismatch, unverifiable


agree, dis, mismatch, unverifiable = hand_control(
    D["days"], lambda s: load(f"{ROOT}/data/ncaaf/latest/players-{s}.json.gz")["players"])

# 🔴 THREE OUTCOMES, NOT TWO — the same split the concentration check
#    needed. A disagreement is a FAILURE; agreement on a real sample is a
#    PASS; and a record with nothing in it is NOT EXERCISED, which is a
#    legitimate state since the wipe and must not read as either.
ck("no graded row disagrees with a hand re-derivation", dis == 0,
   "%d agree, %d disagree, %d unverifiable"
   % (agree, dis, len(unverifiable)))
# ⛔ ~~if agree: ck("...and the control ran on a real sample", agree > 0)~~
#    `[2026-09-28]` could not fail — it was asked only when true. Replaced
#    by an EXACT count on the planted trees in §3b (every planted graded
#    row re-derived, with literal expected values), which can.
if agree:
    note("the hand control re-derived %d live row(s)" % agree)
else:
    note("⚠️ NOT EXERCISED ON THE LIVE RECORD: no graded rows, so the hand "
         "control had nothing to check here (the record counts from "
         + str(R.get("record_from", "its start date"))
         + "). The planted trees in §3b ran it.")

# ══════════════════════════════════════════════════════════════════════
# ⛔ A CONTROL THAT STOPS VERIFYING MUST FAIL, NOT GO QUIET.
# Rows the hand check cannot resolve are no longer counted as
# disagreements — but if they grow, the control is measuring less and
# less while still printing a tick. **BOUND THEM.** A fifth of the
# sample unverifiable means the re-derivation has stopped being a
# control, whatever the agreement count says.
_tot = agree + dis + len(unverifiable)
if unverifiable:
    ck("⚠️ the hand control still resolves most of the sample",
       len(unverifiable) <= max(2, 0.2 * _tot),
       "%d of %d row(s) unverifiable — over a fifth means this is no "
       "longer a control" % (len(unverifiable), _tot))
    for u in unverifiable[:4]:
        note("⚠️ NOT VERIFIABLE BY HAND: " + str(u))
    note("⛔ these are rows the CONTROL could not run on, NOT rows the "
         "grader got wrong. The distinction is the whole point: the old "
         "form counted them as disagreements and reported the cause as "
         "'name not unique', which was wrong on both halves.")
for m in mismatch[:6]:
    note("🔴 " + str(m))

# ───────────────────────────────────────────────────────────────
print("\n═══ 3b. 🔴 THE SAME QUESTIONS ON A PLANTED TREE, BOTH LEAGUES ═══")
# 🔴 `[2026-09-28]` Everything above grades a copy of the LIVE cards, so its
#    cases existed only while production held graded rows (pattern P3):
#    after a record reset (Sam has done one), at a new season's floor, or on
#    a day the newest card held no rows, "has graded rows" went RED on
#    correct code and the n_games / pointer / hand-control / per-method
#    checks passed over nothing. ✅ Each is ALSO asked, every run, of a
#    tree this file writes — the e4b04844 (#156) shape: two graded cards
#    under two methods, an empty card, the `-latest.json` pointer, and a
#    log whose values are known before the grader runs. The floor is pinned
#    below the planted dates, so a moved `RECORD_FROM` cannot empty it.
_PL_DATES = ("2026-09-12", "2026-09-19")
_PL_NAMES = ("Plant Alpha", "Plant Bravo", "Plant Charlie")


def plant_fb(lg, root):
    """Write the planted tree. -> {date: card}. Rec yds: Alpha 30, Bravo 50,
    Charlie 70; every rated row is over 40.5, the unrated one under 3.5 rec."""
    lat = os.path.join(root, "data", lg, "latest")
    os.makedirs(lat)
    os.makedirs(os.path.join(root, "picks"))
    players = {"p%d" % k: {"name": nm, "pos": "WR", "g": [
        {"d": d, "week": i + 1, "rec": 3 + k, "rec_yds": 30 + 20 * k, "car": 1,
         "rush_yds": 5, "rec_td": 0, "rush_td": 0, "pass_yds": 0, "pass_td": 0,
         "att": 0, "snaps": 40, "snap_pct": 0.8, "team": "T%d" % k}
        for i, d in enumerate(_PL_DATES)]} for k, nm in enumerate(_PL_NAMES)}
    with gzip.open(os.path.join(lat, "players-2026.json.gz"), "wt") as fh:
        json.dump({"season": 2026, "players": players}, fh)
    cards = {}
    for d in _PL_DATES:
        picks = [{"player": nm, "market": "player_reception_yds", "side": "over",
                  "line": 40.5, "price": -110, "book": "fanduel",
                  "confidence": 60 + 5 * k, "confidence_basis": "RECORD",
                  "raw": "%d of 10" % (5 + k), "commence": d + "T17:00:00Z",
                  "game": "A%d @ H%d" % (k, k)} for k, nm in enumerate(_PL_NAMES)]
        picks.append({"player": _PL_NAMES[0], "market": "player_receptions",
                      "side": "under", "line": 3.5, "price": -120, "book": "fanduel",
                      "confidence_basis": "MARKET", "commence": d + "T17:00:00Z",
                      "game": "A0 @ H0"})
        cards[d] = {"date": d, "league": lg, "logs_season": 2025, "picks": picks}
        if d == _PL_DATES[-1]:
            cards[d]["card_method"] = "season-blend"
    # ⚠️ a card with NO rows is not a card the grader sees
    cards["2026-09-20"] = {"date": "2026-09-20", "league": lg, "logs_season": 2025,
                           "picks": []}
    for d, c in cards.items():
        json.dump(c, open(os.path.join(root, "picks", "fb-%s-%s.json" % (lg, d)),
                          "w", encoding="utf-8"))
    # ⛔ THE POINTER: byte-for-byte the newest card WITH rows.
    shutil.copy(os.path.join(root, "picks", "fb-%s-%s.json" % (lg, _PL_DATES[-1])),
                os.path.join(root, "picks", "fb-%s-latest.json" % lg))
    return cards


def graded_planted(lg):
    """record_fb.py over the planted tree. -> (rc, R, D, cards, players)."""
    t = tempfile.mkdtemp(prefix="recfb-plant-")
    try:
        cards = plant_fb(lg, t)
        p = subprocess.run([sys.executable, os.path.join(ROOT, "record_fb.py")],
                           cwd=t, env=dict(os.environ, LEAGUE=lg,
                                           FB_RECORD_FROM="2026-09-01"),
                           capture_output=True, text=True, timeout=300)
        lat = os.path.join(t, "data", lg, "latest")
        Rp = load(os.path.join(lat, "record.json")) if os.path.exists(os.path.join(lat, "record.json")) else {}
        Dp = (load(os.path.join(lat, "record-detail.json.gz"))
              if os.path.exists(os.path.join(lat, "record-detail.json.gz")) else {})
        Pp = load(os.path.join(lat, "players-2026.json.gz"))["players"]
        return p.returncode, Rp, Dp, cards, Pp
    finally:
        shutil.rmtree(t, ignore_errors=True)


import subprocess  # noqa: E402
_RAWRE_PL = re.compile(r"^\s*(\d+)\s+of\s+(\d+)\s*$")
_PL_SEEN = {}
for _lg in ("ncaaf", "nfl"):
    _prc, _PR, _PD, _PC, _PP = graded_planted(_lg)
    _prows = [r for day in (_PD.get("days") or {}).values() for r in day]
    _prated = [r for r in _prows if r.get("confidence") is not None]
    ck("🔴 %s PLANTED: the grader ran and graded both carded days" % _lg,
       _prc == 0 and sorted((_PD.get("days") or {})) == list(_PL_DATES)
       and len(_prows) == 8 and len(_prated) == 6,
       "rc=%s days=%s rows=%d rated=%d" % (_prc, sorted(_PD.get("days") or {}),
                                           len(_prows), len(_prated)))
    ck("🔴 %s PLANTED: `-latest.json` is NOT a card, and neither is an empty one" % _lg,
       _PR.get("cards_seen") == 2,
       "⛔ the pointer is byte-for-byte the newest card; grading it would count "
       "that day twice. cards_seen=%s of 2 carded dated files (+1 empty, +1 "
       "pointer on disk)" % _PR.get("cards_seen"))
    _pbad = [(r.get("player"), r.get("market")) for r in _prated
             if not isinstance(r.get("n_games"), int) or isinstance(r.get("n_games"), bool)]
    ck("🔴🔴 %s PLANTED: every rated row carries an INTEGER `n_games`" % _lg,
       bool(_prated) and not _pbad,
       "⛔ the `own_mean` failure in a new costume. Offenders: %s" % _pbad)
    _pdrift = []
    for _day, _rs in (_PD.get("days") or {}).items():
        _by = {(p.get("player"), p.get("market"), p.get("side"), p.get("line")): p
               for p in _PC[_day]["picks"]}
        for _r in _rs:
            _p = _by[(_r.get("player"), _r.get("market"), _r.get("side"), _r.get("line"))]
            _m = _RAWRE_PL.match(str(_p.get("raw") or "")) if _p.get("raw") else None
            if (_r.get("n_games"), _r.get("hits")) != ((int(_m.group(2)), int(_m.group(1)))
                                                       if _m else (None, None)):
                _pdrift.append((_day, _r.get("player"), _p.get("raw"), _r.get("n_games")))
            if _r.get("logs_season") != _PC[_day]["logs_season"]:
                _pdrift.append((_day, _r.get("player"), "logs_season", _r.get("logs_season")))
    ck("🔴🔴 %s PLANTED: n_games, hits and logs_season EQUAL the card's own — "
       "and the unrated row carries none" % _lg,
       bool(_prows) and not _pdrift,
       "⛔ CARRIED, NOT COMPUTED. Drift: %s" % _pdrift[:5])
    _pa, _pdis, _pmis, _punv = hand_control(_PD.get("days") or {}, lambda s: _PP)
    ck("🔴 %s PLANTED: the hand control re-derives EVERY graded row, and agrees" % _lg,
       _pa == 8 and _pdis == 0 and not _punv,
       "%d agree (of 8), %d disagree %s, %d unverifiable %s"
       % (_pa, _pdis, _pmis[:2], len(_punv), _punv[:2]))
    _bravo = [r for r in _prows if r["player"] == "Plant Bravo"]
    _alpha = [r for r in _prows if r["player"] == "Plant Alpha"
              and r["market"] == "player_reception_yds"]
    ck("🔴 %s PLANTED: the grader's answers are the KNOWN ones" % _lg,
       len(_bravo) == 2 and all(r["actual"] == 50.0 and r["won"] is True for r in _bravo)
       and len(_alpha) == 2 and all(r["actual"] == 30.0 and r["won"] is False for r in _alpha),
       "Bravo over 40.5 on 50 yds must WIN, Alpha on 30 must LOSE. got %s / %s"
       % ([(r["actual"], r["won"]) for r in _bravo], [(r["actual"], r["won"]) for r in _alpha]))
    _PL_SEEN[_lg] = len(_prated)
ck("🔴 PLANTED: the denominator reached EACH league, not a total across them",
   all(_PL_SEEN.get(lg) == 6 for lg in ("ncaaf", "nfl")),
   "⛔ Sam's standing rule: everything we do for cfb we do for nfl. %s" % _PL_SEEN)

# ⚠️ THE PER-METHOD BUCKETS, ON PLANTED ROWS: two methods whose buckets
#    differ, so pooling them, dropping one, or handing back the wrong one
#    as `calibration` each changes the answer — whatever the live record
#    holds today (it holds one method after a reset).
_cm_rows = ([{"confidence": c, "won": w} for c, w in ((72, True), (75, False), (78, True))]
            + [{"confidence": c, "won": w, "card_method": "season-blend"}
               for c, w in ((85, True), (88, True))]
            + [{"confidence": None, "won": True, "card_method": "season-blend"}])
_cm_now, _cm_by = record_fb.calibration_by_method(_cm_rows, "season-blend")
ck("🔴 PLANTED: every row with a confidence is in exactly its OWN method's buckets",
   {m: sum(c["n"] for c in v) for m, v in _cm_by.items()}
   == {record_fb.METHOD_BEFORE: 3, "season-blend": 2},
   "got %s" % {m: sum(c["n"] for c in v) for m, v in _cm_by.items()})
ck("🔴 PLANTED: `calibration` is the CURRENT method's buckets, not another's",
   _cm_now == _cm_by.get("season-blend") and _cm_now != _cm_by.get(record_fb.METHOD_BEFORE)
   and [c["bucket"] for c in _cm_now] == ["80-90%"],
   "got %s" % _cm_now)

# ───────────────────────────────────────────────────────────────
print("\n═══ 4. NOTHING UNSETTLED LEAKS INTO A PERCENTAGE ═══")
allrows = [r for rows in D["days"].values() for r in rows]
graded = [r for r in allrows if r["won"] is not None]
ck("the overall tally equals the graded rows, and nothing else",
   R["overall"]["n"] == len(graded)
   and R["overall"]["w"] == sum(1 for r in graded if r["won"]),
   "%d/%d" % (R["overall"]["w"], R["overall"]["n"]))
ck("carded rows = graded + void + unresolved, exactly",
   R["carded_rows"] == len(allrows)
   and R["carded_rows"] == R["overall"]["n"] + R["voids"] + R["unresolved"],
   "%d = %d + %d + %d" % (R["carded_rows"], R["overall"]["n"], R["voids"],
                          R["unresolved"]))
ck("every by_market tally reconciles against the detail rows",
   all(t["n"] == len([r for r in graded if r["market"] == m])
       for m, t in R["by_market"].items()))
ck("every by_day tally reconciles too",
   all(d["n"] == len([r for r in D["days"][d["date"]] if r["won"] is not None])
       for d in R["by_day"]))
# 🔴 ONE METHOD'S BUCKETS PER ROW, EVERY ROW IN EXACTLY ONE. `[2026-09-24]`
# ⛔ THIS USED TO SUM `calibration` ALONE. The day the card switched
#    method (PR #158) `calibration` became the NEW method's buckets — empty
#    until its first slate is graded — and this went red on a correct
#    record. The question is unchanged and now asked of every method:
#    each graded row with a confidence lands in its OWN method's buckets,
#    so the per-method counts match the detail rows method by method.
_CAL = R.get("calibration_by_method") or {}
_conf = [r for r in graded if r.get("confidence") is not None]
_want = {}
for _r in _conf:
    _m = _r.get("card_method") or record_fb.METHOD_BEFORE
    _want[_m] = _want.get(_m, 0) + 1
_got = {m: sum(c["n"] for c in v) for m, v in _CAL.items()}
ck("every graded row with a confidence is in exactly one method's buckets",
   _got == _want and sum(_got.values()) == len(_conf),
   "per method, buckets %s vs detail rows %s (of %d)"
   % (_got, _want, len(_conf)))
ck("`calibration` is exactly the CURRENT method's buckets, never a pool",
   R["calibration"] == _CAL.get(R.get("card_method_current"), []),
   "current=%s" % R.get("card_method_current"))
for _m in [R.get("card_method_current")] + [m for m in _CAL if m != R.get("card_method_current")]:
    if not _CAL.get(_m):
        note("⚠️ method %r has no graded rows yet — reported, not failed: a "
             "method that has just gone live has graded nothing" % _m)

# 🔴 THE HONEST LIMIT MUST BE ON THE FILE, NOT ONLY IN A DOCSTRING.
ck("the file states which way the unsettled rows bias the number",
   "read HIGH" in R["over_bias_note"] or "VOID" in R["over_bias_note"],
   "an exclusion with a direction has to say the direction")
ck("and it says how many rows it could not settle",
   str(R["unresolved"]) in R["coverage_note"])
# 🔴 THREE OUTCOMES, NOT TWO. `[2026-09-06]` This read
#    `distinct_players <= n AND distinct_players > 0`, so it FAILED the
#    moment Sam had the football record wiped — on a correct product with
#    nothing graded yet. That is rule 139's shape, and dropping the
#    `> 0` would leave a check that is true of an empty file, which is
#    rule 142's. So: a graded record must publish its concentration, an
#    empty one is reported NOT EXERCISED, and an impossible one still
#    fails.
ck("the concentration never exceeds the row count",
   R["distinct_players"] <= R["overall"]["n"],
   "%d players cannot come from %d rows"
   % (R["distinct_players"], R["overall"]["n"]))
if R["overall"]["n"]:
    ck("...and a graded record publishes it",
       R["distinct_players"] > 0,
       "%d graded rows from %d players across %d games"
       % (R["overall"]["n"], R["distinct_players"], R["distinct_games"]))
else:
    note("⚠️ NOT EXERCISED: nothing is graded, so concentration was not "
         "observed" + (
             f" — the record was RESET and counts from "
             f"{R.get('record_from')}, with "
             f"{R.get('cards_before_record_from', 0)} earlier card(s) set "
             f"aside" if R.get("record_from") else ""))

# ───────────────────────────────────────────────────────────────
print("\n═══ 5. IT IS GOVERNED, AND THE PAGE PRINTS IT ═══")
import freshness as _f  # noqa: E402
rows = _f.contract(data="data/ncaaf", picks="picks")
modes = [r[0] for r in rows]
ck("fb-record has a freshness contract row (rule 78)", "fb-record" in modes,
   "a builder nothing watches runs approximately never")
row = [r for r in rows if r[0] == "fb-record"][0]
ck("it probes record.json itself", row[1][1].endswith("record.json"))
ck("it is free", row[3] is False)
# ⛔ A deadline before its own input fires every week on a correct system.
grade_due = _f.FB_TIMES["ncaaf"]["grade"]
trend_due = _f.FB_TIMES["ncaaf"]["trends"]
# ⚠️ A DEADLINE TUPLE IS `(hh, mm)` OR `(hh, mm, {days})`, and this
#    crashed with an IndexError the moment college trends went DAILY —
#    `(12, 0)` has no third element. ⛔ Reading `d[2]` without asking
#    whether it exists is the same shape as assuming a schema (rule 121):
#    the two-tuple form was always legal and simply had not been used
#    here yet.
def _days(d):
    """The weekdays a deadline fires on. A 2-tuple fires EVERY day."""
    return d[2] if len(d) > 2 else set(range(7))


# 🔴 AND THE RULE ITSELF HAD TO BE RESTATED WHEN THE REBUILD WENT DAILY.
# ⛔ The constraint is "grading must read logs that already exist". With a
#    WEEKLY rebuild that means the hours have to be ordered on the shared
#    day — grade at 9am on a Tuesday whose logs land at noon reads LAST
#    week's logs, which is the defect this check was written for.
# ✅ With a DAILY rebuild the constraint cannot be violated by more than a
#    day: whatever hour grading runs, a rebuild finished within the last
#    24 hours. That is not the check being loosened, it is the check being
#    true — and the weekly case is still enforced exactly as before.
_daily = [t_ for t_ in trend_due if len(t_) == 2]
if _daily:
    ck("the log rebuild is DAILY, so grading always has fresh logs",
       True, "rebuild %s — no ordering constraint left to violate" % (_daily,))
else:
    _shared = [(g, t_) for g in grade_due for t_ in trend_due
               if _days(g) & _days(t_)]
    ck("the grading deadline falls AFTER the log rebuild that feeds it",
       all(g[0] > t_[0] for g, t_ in _shared) if _shared else True,
       "logs rebuild %s, grading due %s%s" % (
           trend_due, grade_due,
           "" if _shared else " — they share no day, so nothing to order"))

# 🔴 CONVERGE IS THE MECHANISM HERE, NOT A CRON, AND THAT IS DELIBERATE.
# `[measured 2026-09-05]` this repo LOSES scheduled runs -- 29 of 70
# gamelines slots in one week -- which is why football converge was built
# on 09-04. A contract row plus converge repairs a missed build; a cron
# alone does not. ⛔ So the thing to assert is that converge can actually
# REACH this mode, which is two claims: the contract names it, and
# `collect.py` can run the name the contract uses.
# ⚠️ THE SECOND HALF IS THE ONE THAT BITES (ledger rule 84 -- the argument
# the caller passes is part of the query). A contract row naming a mode
# the collector does not have is a row that turns every run red and
# repairs nothing.
cy = open(f"{ROOT}/collect.py").read()
ck("collect.py has an `fb-record` arm to run", 'mode == "fb-record"' in cy)
ck("fb-record is registered as a FREE mode",
   "fb-record" in cy.split("FREE = (")[1].split(")")[0],
   "it reads published cards and stored logs — no API call")

# ══════════════════════════════════════════════════════════════════
# 🔴 THE CHAIN IS THE THING `test_fb_freshness.py` TRUSTS, SO IT IS
# ASSERTED HERE. That file's `drivers` map excuses fb-record from needing
# its own cron on the grounds that `card-fb` builds it. ⛔ If this chain
# is ever deleted, THIS must fail — otherwise the excuse outlives the
# thing it was excusing, which is ledger rule 83 exactly.
# ⚠️ Position matters: the call has to sit INSIDE the card-fb arm, after
# the card is built, not somewhere else in the file that happens to
# mention both names.
arm = cy[cy.index('elif mode == "card-fb":'):]
arm = arm[:arm.index("\n        elif mode ==")]
ck("the grader is chained INSIDE the card-fb arm",
   "build_record_fb()" in arm,
   "so every card build regrades — card-fb runs daily in both leagues")
ck("and it runs AFTER the card is built, not before",
   arm.index("build_card_fb()") < arm.index("build_record_fb()"),
   "grading a card that does not exist yet would grade the previous one")
ck("a grading failure cannot lose the card that was just built",
   "try:" in arm and "except Exception" in arm,
   "the card is the product; the record is a report on it")
ck("it is never chained to a PAID mode (rule 78 in reverse)",
   "build_record_fb()" not in cy[cy.index('elif mode == "props-player"'):
                                 cy.index('elif mode == "props-player"') + 2000]
   if 'elif mode == "props-player"' in cy else True)

# ══════════════════════════════════════════════════════════════════
# 🔴 THE DEADLINE MUST HAVE A BUILDER THAT RAN AFTER ITS INPUT.
# `[2026-09-06]` The first version was due Mon 2pm ET for college. A
# naive "is there a builder that day" check PASSES that — `card-fb` runs
# every morning — and it would still have been wrong, because the Monday
# card build fires at 8:06am ET and the LOG REBUILD it grades from does
# not happen until 12:06pm. ⛔ Grading at 8am Monday reads last week's
# logs; nothing then rebuilds the record before a 2pm deadline.
# ➡️ SO THE CHECK IS ORDERED, IN MINUTES-OF-WEEK: log rebuild →
# card build → deadline. A same-day check would have been decoration.
import re as _re
_wf = open(f"{ROOT}/.github/workflows/collect.yml").read()
from wfroutes import parse_routes as _parse_routes    # noqa: E402
_routes = _parse_routes(_wf)


def _mow_from_cron(c, mode, lg):
    """Every (day, minute-of-week) a cron fires, in ET, 0 = Monday 00:00.

    ⚠️ Crons are UTC and this project is on EDT (UTC-4); `FB_TIMES` is ET.
    Cron day-of-week is 0=Sunday, FB_TIMES is 0=Monday."""
    out = []
    mi, hh, _dom, _mon, dow = c.split()
    days = ({0, 1, 2, 3, 4, 5, 6} if dow == "*" else
            {d for part in dow.split(",")
             for d in (range(int(part.split("-")[0]), int(part.split("-")[1]) + 1)
                       if "-" in part else [int(part)])})
    for h in ([int(x) for x in hh.split(",")] if hh != "*" else range(24)):
        for m in ([int(x) for x in mi.split(",")] if mi != "*" else [0]):
            for d in days:
                et_h = h - 4                      # EDT
                d_et, hh_et = d, et_h
                if et_h < 0:
                    hh_et += 24
                    d_et = (d - 1) % 7
                out.append(((d_et - 1) % 7, ((d_et - 1) % 7) * 1440 + hh_et * 60 + m))
    return out


def _fires(lg, mode):
    out = []
    for c, l, ms in _routes:
        if l == lg and mode in ms.split():
            out += _mow_from_cron(c, mode, lg)
    return sorted(out, key=lambda x: x[1])


for _lg, _logmode in (("ncaaf", "cfb-probe"), ("nfl", "nfl-logs")):
    _logs = _fires(_lg, _logmode)
    _cards = _fires(_lg, "card-fb")
    _ok, _why = True, []
    for _t in _f.FB_TIMES[_lg]["grade"]:
        _h, _m = _t[0], _t[1]
        _dset = _t[2] if len(_t) > 2 else {0, 1, 2, 3, 4, 5, 6}
        for _d in _dset:
            _due = _d * 1440 + _h * 60 + _m
            # the newest log rebuild strictly before the deadline
            _lastlog = max([x[1] for x in _logs if x[1] < _due], default=None)
            # a card build after that rebuild and before the deadline
            _has = any(_lastlog is not None and _lastlog < x[1] < _due for x in _cards)
            if not _has:
                _ok = False
                _why.append("due %s, last %s rebuild %s, no card build between"
                            % (_due, _logmode, _lastlog))
    ck("%s: the grading deadline has a card build between the log rebuild "
       "and itself" % _lg, _ok,
       "; ".join(_why) if _why else
       "%d log rebuild(s), %d card build(s) a week" % (len(_logs), len(_cards)))

h = open(f"{ROOT}/index.html").read()
ck("the page reads record.json", "latest/record.json" in h)
# 🔴 `[Sam, 2026-10-01]` ~~ck("the page prints the builder's own coverage
#    sentence, not its own", "R.coverage_note" in h and "R.over_bias_note" in
#    h)~~ and ~~ck("the page prints the concentration warning",
#    "distinct_players" in h)~~. The football record tab printed record_fb.py's
#    coverage and over-bias sentences, and an "N rows came from M players"
#    warning, in footnote boxes. Sam: no explanation, caveat or warning box on
#    any tab ("i just want what's supposed to be in each tab to be in each
#    tab"; asked what stays, he chose: remove everything). So both are
#    required ABSENT, asked of the page the same way. ⚠️ record_fb.py still
#    WRITES coverage_note, over_bias_note and distinct_players, and the checks
#    above still assert them on the grader's own sandbox output, unchanged;
#    only the page stopped printing them.
ck("⛔ [Sam, 2026-10-01] the page prints no coverage sentence — not the "
   "builder's, not one of its own",
   "coverage_note" not in h and "over_bias_note" not in h
   and "What is and is not counted" not in h)
ck("⛔ [Sam, 2026-10-01] ...and no concentration warning",
   "distinct_players" not in h)
ck("an em-dash is still used for 'nothing graded'",
   "nothing graded yet" in h,
   "'nothing graded' and 'graded 0%' are different facts")

# ───────────────────────────────────────────────────────────────
# 🔴 THE FAILURE GATE IS THE LAST THING IN THIS FILE. Rule 97.


# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 THE DENOMINATOR REACHES THE RECORD, ON BOTH LEAGUES.
#
# `[added 2026-09-15]` `n_games`, `hits` and `logs_season` are CARRIED
# onto every graded row for exactly the reason `own_mean` is — and the
# ORDERING is the lesson, not the fields.
#
# ⛔ THE DOCS SAID TO ADD THESE "IF T58 PASSES". **That ordering is the
#    error.** T57 lost an entire pre-registered arm because card-time
#    lines were never archived: by the time the test needed them, the
#    history did not exist and no amount of waiting could bring it back.
# ✅ Recording a field decides nothing and costs nothing. NOT recording
#    it is the irreversible move.
#
# 🔴 AND THE SHAPE OF THE FAILURE IS ALREADY WRITTEN DOWN HERE: `own_mean`
#    sat at **0 of 200 graded rows while appearing to work**, because the
#    cards carried it and the grader silently did not. A field absent on
#    half the rows is worse than no field. ➡️ So this does not ask
#    "does the key exist" — it asks **how many rows have it, on BOTH
#    leagues**, and refuses any row that carries a confidence without one.
# ══════════════════════════════════════════════════════════════════════
import shutil as _sh          # noqa: E402
import subprocess as _sp      # noqa: E402
import tempfile as _tf        # noqa: E402

_RAWRE = re.compile(r"^\s*(\d+)\s+of\s+(\d+)\s*$")
_HELPERS = ("record_fb.py", "card_fb.py", "cfb.py", "nfl.py", "ranking.py",
            "freshness.py", "jsblock.py", "wfroutes.py", "tcheck.py")


def _regrade(lg):
    """Grade one league in an ISOLATED tree. -> (rc, detail, cards).

    ⛔ NEVER IN THE REPO ROOT. `tcheck.py` refuses a test that writes
    under data/ or picks/, and the reason is in its header: this file
    used to rewrite `data/ncaaf/latest/record.json` on every CI run,
    which the freshness contract then read as proof the grader had run.
    ⚠️ `LEAGUE`, not `FB_LEAGUE` — I got that wrong once while measuring
    this change and read a stale copied file as though it were output
    (rule 202: read the OUTPUT, not the exit code).
    """
    d = _tf.mkdtemp(prefix="recfb-%s-" % lg)
    _sh.copytree("%s/data/%s" % (ROOT, lg), "%s/data/%s" % (d, lg))
    _sh.copytree("%s/picks" % ROOT, "%s/picks" % d)
    # ⚠️ `_HELPERS` IS NOW A SEED LIST, NOT A DEPENDENCY LIST. Each
    #    entry arrives WITH the repo-local modules it imports, so the day a
    #    subject gains an import this tree gets it too. `[2026-09-16: it
    #    did — card_fb.py imported calibration.py and this list, and three
    #    more like it, all went stale in the same commit]`
    for f in _HELPERS:
        copy_module(f, d)
    p = _sp.run([sys.executable, "record_fb.py"], cwd=d, timeout=300,
                env=dict(os.environ, LEAGUE=lg),
                capture_output=True, text=True)
    det = load("%s/data/%s/latest/record-detail.json.gz" % (d, lg))
    cards = {}
    for f in sorted(glob.glob("%s/picks/fb-%s-*.json" % (ROOT, lg))):
        if f.endswith("-latest.json"):
            continue
        c = json.load(open(f, encoding="utf-8"))
        cards[str(c.get("date") or os.path.basename(f)[:-5])] = c
    return p.returncode, det, cards


# 🔴 `[2026-09-28]` THE LIVE REGRADE IS NOW THE EXTRA, NOT THE ONLY CASE.
#    Every question in this section is asked of the planted trees in §3b on
#    every run. Here, "has graded rows" is asserted only when the live INPUT
#    can produce them — a carded card on or after the floor whose season log
#    is stored — so a record reset or a new season's floor is REPORTED
#    instead of turning the suite red; and a grader that silently produces
#    nothing from a gradeable card still fails.
_seen_any = {}
for _lg in ("ncaaf", "nfl"):
    _rc, _det, _cards = _regrade(_lg)
    ck("⚠️ %s regrades clean in an isolated tree" % _lg, _rc == 0,
       "⛔ every check below reads its output. rc=%s" % _rc)
    _rows = [r for day in (_det.get("days") or {}).values() for r in day]
    _rated = [r for r in _rows if r.get("confidence") is not None]
    _withn = [r for r in _rated if r.get("n_games") is not None]
    _seen_any[_lg] = len(_withn)
    _gradeable = [d for d, c in _cards.items()
                  if str(d) >= record_fb.RECORD_FROM and (c.get("league") or "") == _lg
                  and c.get("picks")
                  and os.path.exists("%s/data/%s/latest/players-%s.json.gz"
                                     % (ROOT, _lg, str(d)[:4]))]
    if _gradeable:
        ck("⚠️ %s has graded rows to check at all" % _lg, bool(_rows),
           "⛔ a check over an empty set passes and proves nothing — rule 67. "
           "%d gradeable live card(s), got %d row(s)" % (len(_gradeable), len(_rows)))
    else:
        note("⚠️ NOT EXERCISED ON THE LIVE %s RECORD: no carded card on or after "
             "%s has its season log stored — a reset or a new season. §3b's "
             "planted tree asked every question below." % (_lg, record_fb.RECORD_FROM))
        continue
    # 🔴🔴 THE GUARD SAM ASKED FOR.
    _bad = [(r.get("player"), r.get("market")) for r in _rated
            if r.get("n_games") is None]
    ck("🔴🔴 %s: NO graded row carries a confidence without an `n_games`"
       % _lg,
       not _bad,
       "⛔ THIS IS THE `own_mean` FAILURE IN A NEW COSTUME — that field "
       "sat at 0 of 200 graded rows while the cards carried it on all "
       "339. A denominator missing from the rows that have a confidence "
       "is a denominator no test can ever use. Offenders: %s"
       % _bad[:5])
    note("%s: %d of %d graded rows carry a denominator (%d rows carry no "
         "confidence and correctly carry none)"
         % (_lg, len(_withn), len(_rated), len(_rows) - len(_rated)))
    # ⛔ AN INTEGER, because the consumer divides by it. A string "8"
    #    would pass a presence check and fail the first test that used it.
    ck("⛔ %s: the denominator is an INTEGER, never a string" % _lg,
       all(isinstance(r["n_games"], int) and not isinstance(r["n_games"], bool)
           for r in _withn),
       "🔴 `raw` is prose — '8 of 8'. If the parse leaks the string "
       "through, every consumer breaks on the first arithmetic. Got %s"
       % sorted({type(r["n_games"]).__name__ for r in _withn}))
    ck("⛔ %s: hits never exceeds the denominator" % _lg,
       all(r["hits"] <= r["n_games"] for r in _withn
           if r.get("hits") is not None),
       "🔴 a carried field that is arithmetic nonsense is worse than an "
       "absent one — it enters the permanent record looking measured")
    # 🔴🔴 CARRIED, NOT COMPUTED — asserted against the CARD ITSELF, so a
    #    future 'improvement' that recomputes the denominator from a log
    #    goes red here rather than silently re-writing history.
    _drift = []
    for _day, _rs in (_det.get("days") or {}).items():
        _card = _cards.get(_day)
        if not _card:
            continue
        _by = {}
        for _p in _card.get("picks") or []:
            _by[(_p.get("player"), _p.get("market"), _p.get("side"),
                 _p.get("line"))] = _p
        for _r in _rs:
            _p = _by.get((_r.get("player"), _r.get("market"), _r.get("side"),
                          _r.get("line")))
            if not _p:
                continue
            _m = _RAWRE.match(str(_p.get("raw") or ""))
            _want = int(_m.group(2)) if _m else None
            if _r.get("n_games") != _want:
                _drift.append((_day, _r.get("player"), _p.get("raw"),
                               _r.get("n_games")))
            if _r.get("logs_season") != _card.get("logs_season"):
                _drift.append((_day, _r.get("player"), "logs_season",
                               _r.get("logs_season")))
    ck("🔴🔴 %s: every carried value EQUALS the card's own" % _lg,
       not _drift,
       "⛔ CARRIED, NOT COMPUTED — `own_mean`'s shape exactly. The moment "
       "this is derived rather than copied it stops being what the board "
       "published, and the record silently disagrees with the cards it "
       "was built from. Drift: %s" % _drift[:5])
    ck("⚠️ %s: `logs_season` reached the rows at all" % _lg,
       any(r.get("logs_season") is not None for r in _rows),
       "⛔ the check above is vacuously true if the field is absent "
       "everywhere AND the cards also lack it — this pins that it is "
       "really being carried")

# ⛔ ~~ck("the denominator reached BOTH leagues", _seen_any > 0)~~ — a TOTAL
#    across both leagues, so one league at zero still passed its label, and
#    an empty live record reddened it on correct code. `[2026-09-28]` The
#    per-league form is asserted on the planted trees in §3b ("reached EACH
#    league"); the live counts are reported.
note("the denominator on the live records, per league: %s" % _seen_any)

note("⛔ WHAT THIS DOES NOT CLAIM: that `n_games` is right to use, or "
     "that any test should split on it. It claims the number the board "
     "PUBLISHED is now in the permanent record instead of being thrown "
     "away at grading time. ➡️ Recording decides nothing; not recording "
     "is the irreversible move.")
