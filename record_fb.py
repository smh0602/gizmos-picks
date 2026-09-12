#!/usr/bin/env python3
"""record_fb.py — THE FOOTBALL GRADER.

    LEAGUE=ncaaf python record_fb.py
    LEAGUE=nfl   python record_fb.py

Grades every published football card against the stored player game logs
and writes one file the Track Record tab reads. **Free — no API call.**

🔴 THE TAB HAS EXISTED SINCE 2026-09-03 AND HAS NEVER HAD A NUMBER IN IT.
It draws MLB's four stat boxes with an em-dash in every one, because
nothing graded football picks. This is that grader.

════════════════════════════════════════════════════════════════════════
🔴 THE THREE MEASUREMENTS THIS FILE IS BUILT ON. Each one would have
produced a WRONG RECORD if it had been assumed instead.
════════════════════════════════════════════════════════════════════════

**1. THE TWO LEAGUES USE OPPOSITE DATE CONVENTIONS.**
`[measured 2026-09-05]`

    college log `d` == the UTC date of kickoff       17 of 17 games
    college log `d` == the ET  date of kickoff       12 of 17
    NFL     log `d` == the schedule's naive-Eastern  285 of 285

⛔ So a Thursday 9pm ET college kickoff is logged as FRIDAY, while the
card is dated by its ET slate (ledger rule 60). **An exact-date join
would have silently dropped every night game** — about 30% of a college
slate, and not a random 30%: the marquee ones.
✅ **The join is a ±1 DAY WINDOW, and it is provably unambiguous:**
measured across the whole log, the most rows any single player has inside
a three-day window is **1**. Football is weekly, so a window join cannot
pick the wrong game. ➡️ This is ledger rule 85 arriving a third time —
two feeds disagreeing about a timestamp.

**2. AN NFL LOG ROW DOES NOT MEAN HE PLAYED.**
`[measured 2026-09-05 on 19,400 rows of the 2025 NFL log]`

    rows with snaps == 0        13,241 of 19,400  (68.3%)

⛔ nflverse writes a row for a rostered player who took NO SNAPS, and
every stat in it is zero. Grading those would hand a WIN to every UNDER
on a player who never took the field, and the under hit-rate would be
nonsense. **At a book that is a VOID.**
✅ So an NFL row with `snaps == 0` is a VOID, recorded and excluded from
every percentage — the same treatment MLB gives a hitter who never
batted. ⚠️ This is `SNAP_FLOOR` from `card_fb.py` arriving on the grading
side: the same defect, the same fix.

**3. COLLEGE OMITS A CATEGORY RATHER THAN WRITING A ZERO.**
`[measured 2026-09-05]`

                       key present   of those, == 0
    college  rec         12,880          20  (0.2%)
    college  car          9,088          12  (0.1%)
    NFL      rec         19,400      15,341 (79.1%)

⛔ CFBD lists a player in the receiving table when he caught something.
**So in college an ABSENT key is a real zero**, and in the NFL a zero is
written out. Reading college's absence as "unknown" would refuse to grade
most of the board; reading NFL's absence as zero would grade rows that do
not exist.

🔴 **AND THE ONE THING THIS GRADER CANNOT DO, STATED RATHER THAN HIDDEN.**
In college, a player who PLAYED AND RECORDED NOTHING has no game row at
all — identical, in the file, to a player who did not dress. ⛔ **Those
two cannot be told apart**, so those picks are UNRESOLVABLE: not a win,
not a loss, not a void, and excluded from every percentage.
⚠️ **THAT EXCLUSION IS BIASED AND THE BIAS HAS A DIRECTION.** A player who
did nothing is exactly the player an OVER loses on, so dropping him makes
the college OVER rate read HIGH. The count is published on the card and
on the page so the reader can see how big it is, and `over_bias_note`
says which way it points. ⛔ It is not corrected, because correcting it
would mean inventing an outcome.
"""
import glob
import gzip
import json
import os
import sys
from datetime import datetime, timedelta, timezone

LEAGUE = os.environ.get("LEAGUE", "ncaaf")
if LEAGUE not in ("nfl", "ncaaf"):
    print(f"FATAL: record_fb.py is football only, got LEAGUE={LEAGUE!r}")
    sys.exit(1)
DATA = f"data/{LEAGUE}"
LATEST = f"{DATA}/latest"
LG_NAME = {"nfl": "NFL", "ncaaf": "College Football"}[LEAGUE]

# ⚠️ ±1 DAY. See measurement 1 in the docstring. ⛔ Do not widen it: two
# days would start to reach a Thursday game from a Saturday card.
JOIN_WINDOW_DAYS = 1

# 🔴🔴 THE RECORD STARTS HERE. Sam, 2026-09-06: *"wipe the track record,
# dont get rid of the tab completley"* — and *"only football"*, so MLB's
# own record is untouched.
#
# ⛔ WHY, AND IT IS NOT TIDINESS. Every football card published before this
# date was built while the pipeline was still being repaired:
#   · the freshness contract had NO SUNDAY, so boards were a day stale
#     and Gizmo's Picks showed the previous day's lines
#   · a card mixed two slate days -- 31 picks for 09-03 and 19 for 09-04
#   · every football run without an explicit season handed the collector
#     a literal 2025, so Trends never rebuilt
#   · CFBD was rate-limiting us and the code called it "season not started"
# **A hit rate computed over those cards measures the outage, not the
# product.** ⛔ Publishing it as "the record" would be the clearest breach
# of rule 55 this project could commit: a number that looks like evidence
# and is not.
#
# ⚠️ THE CARDS ARE NOT DELETED. They stay in `picks/` exactly as
# published, so nothing is rewritten and the earlier period can be graded
# again by moving this one date.
# ✅ REVERSIBLE, AND THE TAB SAYS SO. `record.json` carries this date and
# the count of what it excluded, so the page states the reset rather than
# showing a bare 0-0 that reads as a broken tab.
RECORD_FROM = os.environ.get("FB_RECORD_FROM", "2026-09-07")

# 🔴 THE SAME READERS `card_fb.py` USES, and they are IMPORTED rather than
# retyped. The grader must read a stat the exact way the rate that
# produced the pick read it, or the record measures a different question
# from the card (ledger rule 66).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import card_fb  # noqa: E402


def log(m):
    print(f"[{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}] {m}", flush=True)


def stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _val(g, market):
    """The outcome of one market out of one game row.

    ⛔ COLLEGE ABSENCE IS A ZERO, NFL ABSENCE IS NOT POSSIBLE. See
    measurement 3. `card_fb.MARKETS` already reads every field with
    `or 0`, which is the college semantics; the NFL rows carry every key
    explicitly so the two agree there by construction.
    """
    reader = card_fb.MARKETS.get(market)
    if reader is None:
        return None
    try:
        return float(reader[0](g))
    except Exception:
        return None


def _won(val, line, side):
    """W / L / None. ⛔ None means UNGRADABLE, never a loss."""
    if val is None:
        return None
    if side == "yes":
        # ⚠️ An anytime-TD market has no line: the bet is "one or more".
        return val >= 1
    if line is None:
        return None
    return (val > line) if side == "over" else (val < line)


def _played(g):
    """Did he take the field? (played, why-not-if-not)

    🔴 NFL ONLY HAS AN ANSWER TO THIS, and it is measurement 2: a row with
    `snaps == 0` is a rostered player who did not play, and every stat in
    it is zero. ⛔ Grading it would hand a WIN to every UNDER on a man who
    never took the field.
    ⚠️ COLLEGE HAS NO SNAP COUNTS AT ALL — CFBD publishes none — so the
    question cannot be asked there. A college row exists because he DID
    something, which is its own weaker guarantee.
    """
    if LEAGUE != "nfl":
        return True, None
    sn = g.get("snaps")
    sp = g.get("snap_pct")
    if sn is not None and float(sn) == 0:
        return False, "on the roster but took no snaps"
    if sn is None and sp is not None and float(sp) == 0:
        return False, "on the roster but took no snaps"
    return True, None


def load_log(season):
    p = f"{LATEST}/players-{season}.json.gz"
    if not os.path.exists(p):
        return None, None
    d = json.load(gzip.open(p, "rt"))
    return d, d.get("players") or {}


def grade_card(card, P, idx, covers_through):
    """One card -> a list of graded rows, each carrying its own verdict."""
    rows = []
    for p in card.get("picks", []):
        mk, side, line = p.get("market"), p.get("side"), p.get("line")
        who = p.get("player")
        base = {
            "player": who, "market": mk, "market_label": p.get("market_label"),
            "side": side, "line": line, "price": p.get("price"),
            "book": p.get("book"), "confidence": p.get("confidence"),
            "confidence_basis": p.get("confidence_basis"),
            "implied": p.get("break_even"), "edge": p.get("edge"),
            "game": p.get("game"), "commence": p.get("commence"),
            "rank": p.get("rank"),
            # 🔴🔴 `own_mean` IS CARRIED BECAUSE T54 CANNOT BE ANSWERED
            #    WITHOUT IT, AND IT HAS BEEN OPEN SINCE 2026-09-04
            #    ACCUMULATING NOTHING.
            # `[measured 2026-09-12]` The published cards carry `own_mean`
            # on ALL 339 rated picks. The GRADED rows carried it on ZERO
            # of 200 — this function built its `base` without the field,
            # so the predictor T54 splits on was discarded at grading time
            # and the test's sample was permanently stuck at zero.
            # ⛔ THAT IS NOT "NOT YET MEASURABLE FOR LACK OF SAMPLE". It is
            #    a test that could never have become measurable, and it
            #    would have sat open indefinitely reporting a shortfall
            #    whose cause was in the grader rather than in the slate.
            # ✅ CARRIED, NOT COMPUTED. `stretch = line / own_mean` is
            #    derived by the CONSUMER (`t54.py`) exactly as T54
            #    specifies; this only stops throwing the input away.
            # ⚠️ AND THE HISTORY IS RECOVERABLE: every stored card still
            #    holds the field, so a re-grade replays it. Nothing is
            #    lost — but nothing would have accumulated either.
            "own_mean": p.get("own_mean"),
        }
        if mk not in card_fb.MARKETS:
            rows.append({**base, "won": None, "state": "unknown market",
                         "actual": None})
            continue

        pids = idx.get(card_fb.norm(who), [])
        if len(pids) > 1:
            rows.append({**base, "won": None, "state": "ambiguous name",
                         "actual": None})
            continue
        if not pids:
            rows.append({**base, "won": None, "state": "no log for this player",
                         "actual": None})
            continue

        # ── the ±1 day window join. See measurement 1. ──────────────
        day = (p.get("commence") or "")[:10]
        try:
            t = datetime.strptime(day, "%Y-%m-%d")
        except Exception:
            rows.append({**base, "won": None, "state": "pick has no kickoff",
                         "actual": None})
            continue
        hits = []
        for g in P[pids[0]].get("g") or []:
            try:
                gd = datetime.strptime(g["d"], "%Y-%m-%d")
            except Exception:
                continue
            if abs((gd - t).days) <= JOIN_WINDOW_DAYS:
                hits.append(g)

        if len(hits) > 1:
            # ⛔ MEASURED IMPOSSIBLE (max 1 row per player per 3 days) --
            # so if it ever happens, REFUSE rather than pick one.
            rows.append({**base, "won": None, "state": "two games in the window",
                         "actual": None})
            continue

        if not hits:
            # 🔴 THE TWO REASONS A ROW CAN BE MISSING, AND THEY ARE NOT THE
            # SAME FACT. Beyond the log's coverage = the game is not in the
            # file yet. Inside it = he played and recorded nothing, or did
            # not dress, and college cannot tell those apart.
            if covers_through and day > covers_through:
                st = "not in the log yet"
            else:
                st = ("played nothing recorded, or did not dress"
                      if LEAGUE != "nfl" else "not in the log for that week")
            rows.append({**base, "won": None, "state": st, "actual": None})
            continue

        g = hits[0]
        ok, why = _played(g)
        if not ok:
            rows.append({**base, "won": None, "state": "void — " + why,
                         "actual": None})
            continue

        val = _val(g, mk)
        w = _won(val, line, side)
        rows.append({**base, "actual": val,
                     "won": None if w is None else bool(w),
                     "state": "graded" if w is not None else "no value"})
    return rows


def tally(rows):
    n = len(rows)
    w = sum(1 for r in rows if r["won"])
    return {"w": w, "n": n, "pct": round(100 * w / n, 1) if n else None}


def main():
    cards = []
    for f in sorted(glob.glob(f"picks/fb-{LEAGUE}-*.json")):
        # ⛔ `-latest.json` IS A POINTER, NOT A CARD. It is a byte-for-byte
        # copy of the newest dated file, so grading both counts that day
        # twice. This is the football twin of the MLB grader's hand-built
        # card exclusion, and it is the first thing that would go wrong.
        if f.endswith("-latest.json"):
            continue
        try:
            cards.append((f, json.load(open(f))))
        except Exception as e:
            log(f"  unreadable: {f} ({type(e).__name__})")

    if not cards:
        log(f"record_fb[{LEAGUE}]: no {LG_NAME} cards published yet — "
            f"nothing to grade, and that is not a failure")

    # ⛔ APPLIED BEFORE ANYTHING IS GRADED, and COUNTED so the page can
    # say what was set aside rather than implying there was never anything.
    _before = []
    _kept = []
    for f, card in cards:
        _d = card.get("date") or os.path.basename(f)[:-5]
        (_kept if str(_d) >= RECORD_FROM else _before).append((f, card))
    if _before:
        log(f"record_fb[{LEAGUE}]: {len(_before)} card(s) dated before "
            f"{RECORD_FROM} are NOT graded — they were built while the "
            f"automatic updates were still being repaired. The files are "
            f"untouched in picks/.")
    cards = _kept

    logs, days, skipped = {}, [], []
    for f, card in cards:
        date = card.get("date") or os.path.basename(f)[:-5]
        # ⚠️ Keyed on the card's OWN league, never the filename -- the same
        # guard MLB's grader needed after football cards landed in picks/.
        if (card.get("league") or "").lower() != LEAGUE:
            continue
        season = int(str(date)[:4])
        if season not in logs:
            logs[season] = load_log(season)
        doc, P = logs[season]
        if not P:
            skipped.append((date, f"no {season} player log stored yet"))
            continue
        idx = card_fb.index_by_name(P)
        allrows = [g for pl in P.values() for g in (pl.get("g") or [])]
        covers = max((g.get("d") or "" for g in allrows), default="")

        rows = grade_card(card, P, idx, covers)
        graded = [r for r in rows if r["won"] is not None]
        if not graded:
            skipped.append((date, "nothing settled yet — the log does not "
                                  "reach this slate"))
        days.append({
            "date": date, "rows": rows, "graded": graded,
            "n": len(graded), "w": sum(1 for r in graded if r["won"]),
            "voids": sum(1 for r in rows if str(r["state"]).startswith("void")),
            "unresolved": sum(1 for r in rows if r["won"] is None
                              and not str(r["state"]).startswith("void")),
            "carded": len(rows),
            "log_covers_through": covers,
        })

    days = [d for d in days if d["carded"]]
    A = [r for d in days for r in d["graded"]]

    # 🔴 CALIBRATION BUCKETS ON THE CARD'S OWN CONFIDENCE, which on
    # football is a RECORD and never a MODEL number (ledger rule 55). The
    # bucket labels say so.
    buckets = {}
    for r in A:
        if r.get("confidence") is None:
            continue
        buckets.setdefault(int(r["confidence"] // 10) * 10, []).append(r)

    unresolved = sum(d["unresolved"] for d in days)
    voids = sum(d["voids"] for d in days)
    carded = sum(d["carded"] for d in days)

    doc = {
        "built_at": stamp(),
        "league": LEAGUE,
        "kind": "DESCRIPTIVE",
        "note": (f"Every {LG_NAME} row the board published, graded from the "
                 f"stored player game log — not from anyone's memory. "
                 f"Uncurated: it grades everything the board printed."),
        "basis": "RECORD",
        "no_model_note": (
            "⛔ No number here is a model output. Football has no model — "
            "three pre-registered specifications were tested and every one "
            "lost to a player's own season average — so the 'confidence' "
            "these rows are bucketed by is the player's OWN RECORD at that "
            "line, and this page measures how that did."),
        "overall": tally(A),
        "by_market": {m: tally([r for r in A if r["market"] == m])
                      for m in sorted({r["market"] for r in A})},
        "by_side": {s: tally([r for r in A if r["side"] == s])
                    for s in sorted({r["side"] for r in A})},
        "by_book": {b: tally([r for r in A if r["book"] == b])
                    for b in sorted({r["book"] for r in A if r.get("book")})},
        "calibration": [{"bucket": f"{b}-{b + 10}%",
                         "stated": round(sum(r["confidence"] for r in v) / len(v), 1),
                         **tally(v)} for b, v in sorted(buckets.items())],
        "by_day": [{"date": d["date"], "w": d["w"], "n": d["n"],
                    "carded": d["carded"], "voids": d["voids"],
                    "unresolved": d["unresolved"]} for d in days],
        "days_graded": sum(1 for d in days if d["n"]),
        "cards_seen": len(days),
        # 🔴 THE RESET, ON THE FILE, SO THE PAGE DOES NOT HAVE TO GUESS.
        # ⛔ Both numbers are COMPUTED here (rule 132); the tab prints them
        # rather than carrying a sentence of its own that could go stale.
        "record_from": RECORD_FROM,
        "cards_before_record_from": len(_before),
        "record_from_note": (
            f"Counting from {RECORD_FROM}. "
            + (f"{len(_before)} earlier card(s) were graded against a "
               f"pipeline that was still being repaired — stale boards, a "
               f"card that mixed two days, and a season default that "
               f"pointed at last year — so they are set aside rather than "
               f"carried forward. The cards themselves are untouched."
               if _before else
               "No earlier cards were set aside.")),
        # 🔴 HOW MANY PEOPLE ARE BEHIND THE NUMBER, NOT JUST HOW MANY ROWS.
        # `[measured on the first graded card]` 17 graded rows came from 11
        # players — six of them carded twice. ⛔ Seventeen rows off eleven
        # men is not seventeen observations, and a hit rate that does not
        # say so invites a reader to treat it as one. The MLB ledger states
        # this on every slate; football states it on the file.
        "distinct_players": len({r["player"] for r in A}),
        "distinct_games": len({r["game"] for r in A if r.get("game")}),
        "carded_rows": carded,
        "voids": voids,
        "unresolved": unresolved,
        # ══════════════════════════════════════════════════════════════
        # 🔴 THE HONEST LIMIT, ON THE FILE, IN A FIELD THE PAGE PRINTS.
        # ⛔ A record that quietly drops the rows it cannot settle is a
        # record that reads better than the board did.
        "coverage_note": (
            f"{len(A)} of {carded} published rows are graded. "
            f"{voids} are VOID — " +
            ("a rostered player who took no snaps, which is a refund at the "
             "book, not a win. " if LEAGUE == "nfl" else
             "excluded from every percentage. ") +
            f"{unresolved} could not be settled at all."),
        "over_bias_note": (
            "⚠️ THE UNSETTLED ROWS ARE NOT A RANDOM SAMPLE, AND THE BIAS HAS "
            "A DIRECTION. A player with no line in the box score is exactly "
            "the player an OVER loses on, so leaving those out makes the "
            "OVER hit rate read HIGH. It is not corrected — correcting it "
            "would mean inventing an outcome — and the count is published "
            "above so the size of it is visible."
            if LEAGUE != "nfl" else
            "⚠️ A VOID is a player who did not take a snap. Those are "
            "excluded rather than counted, which is what the book does."),
        "detail_file": f"{LATEST}/record-detail.json.gz",
        "skipped": [{"date": a, "why": b} for a, b in dict.fromkeys(skipped)],
        "join_note": (
            f"A pick is joined to a game log by player name and a "
            f"±{JOIN_WINDOW_DAYS}-day window around kickoff. The window is "
            f"there because the two leagues date a game differently — "
            f"college logs a kickoff on its UTC date, so a Thursday night "
            f"game lands on Friday, while the NFL logs the Eastern one — "
            f"and it is safe because a player has at most one game inside "
            f"any three-day window."),
    }
    os.makedirs(LATEST, exist_ok=True)
    with open(f"{LATEST}/record.json", "w") as fh:
        json.dump(doc, fh, indent=1)
    with gzip.open(f"{LATEST}/record-detail.json.gz", "wt") as fh:
        json.dump({"built_at": doc["built_at"], "league": LEAGUE,
                   "kind": "DESCRIPTIVE",
                   "note": ("Every published row with its verdict and the "
                            "actual number. `won` is null on anything not "
                            "settled, and those are in no percentage."),
                   "days": {d["date"]: d["rows"] for d in days}}, fh)

    log(f"record_fb[{LEAGUE}]: {len(days)} card(s), {len(A)}/{carded} rows "
        f"graded, {doc['overall']['w']}/{doc['overall']['n']} won, "
        f"{voids} void, {unresolved} unresolved")
    for s in doc["skipped"]:
        log(f"  skipped {s['date']}: {s['why']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
