#!/usr/bin/env python3
"""
THE FOOTBALL RECORD, REBUILT FROM THIS CHECKOUT'S OWN CODE — THEN CHECKED.

🔴🔴 THE GAP THIS CLOSES. `[2026-09-24]` PR #158 split the football
record's calibration by card method. It passed pr-tests, merged, and main
went red at the 21:50Z rebuild: `calibration` was now the NEW method's
buckets, empty until its first slate is graded, and the Track Record tab
drew no football bands at all.
⛔ pr-tests could not see it because every record check read the
COMMITTED `data/<lg>/latest/record.json` — a file written by the code on
`main`, not by the PR. A PR that changes the record's shape is tested
against the old shape, and the new shape first meets a check after merge.

✅ SO THIS FILE NEVER READS THE COMMITTED RECORD. It runs this checkout's
`record_fb.py` over a throwaway copy of the stored cards and player logs,
for BOTH leagues, and asks the record and the page's own renderer the
questions `test_record_fb.py` and `test_fb_record.py` ask:
  1. every graded row with a confidence is in exactly one method's buckets
  2. `calibration` is the current method's buckets, never a pool
  3. ~~the tab draws one labelled table per method, current first~~
     the tab draws three hit rates, Board / Player props / Game lines, each
     the rebuilt record's own (Board = every graded pick: props AND lines)
  4. ~~no band on any table says "we said"~~ no band, no "Was the record
     right?" and no method table on the tab at all; below the boxes only
     the two by-date lists, each opening exactly the record's graded days
  5. ~~a method with nothing graded is REPORTED and says so on the page~~
     a method with nothing graded is still REPORTED (the record keeps its
     buckets); on the page a box with nothing graded says so, never 0%

`[Sam, 2026-10-17]` Questions 3-5 were rewritten to Sam's new Track Record,
in all three leagues: *"in track record we should have a game lines tracker
so we an track how the model does for game lines. lose the was the record
right? section of it. i only want the board hit % to be shown(this is the 25
player props and all the game lines hit %) and i want both hit % to be
shown ... all in all wed have 3 different hit rate % shows at the top of the
track record tab, board(all picks), player props(only player props), and
game line(only game lines)"*; below the three he chose "Just the by-date
lists". ⚠️ The DATA is unchanged and still checked: every method's buckets
(questions 1-2) are still built and kept apart; only the page stopped
drawing them. And the planted tree now carries game lines too, so the
game-lines tracker is asked on every run, not only when the stored cards
hold graded lines.

⚠️ THREE STATES OF THE STORED DATA, because the defect lived in a state
the stored data was not in when the PR was tested:
  STORED       — the cards exactly as they are on disk
  NEXT METHOD  — plus tomorrow's card under a method nothing has graded:
                 the state main was in the night #158 merged
  TWO GRADED   — one graded card re-stamped with a second method, so two
                 methods BOTH hold graded rows and a pool would show
⛔ The re-stamped cards are FIXTURES in a temp directory. Nothing under
`data/` or `picks/` is written.

# @vacuity the YEAR TURN probe (01-02) is graded from the season before
#   file: record_fb.py
#   find: season = fb_why.season_of(date)
#   with: season = int(str(date)[:4])
"""
import glob
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

from tcheck import ck, copy_module, eq, note, section

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsblock import js_block  # noqa: E402
import fb_why  # noqa: E402  (season_of: the season the grader reads a card's log by)

ROOT = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(ROOT, "index.html")
BEFORE = "2025-only"
PROBE_NEXT = "probe-next-method"
PROBE_GRADED = "probe-second-method"


# ══════════════════════════════════════════════════════════════════════
# @vacuity two methods' graded rows must never be pooled into one
#   file: record_fb.py
#   find: per.setdefault(r.get("card_method") or METHOD_BEFORE, {}).setdefault(
#   with: per.setdefault(METHOD_BEFORE, {}).setdefault(
#
# @vacuity a method that is not current must keep its buckets
#   file: record_fb.py
#   find: for m, bk in per.items()}
#   with: for m, bk in per.items() if m == current}
#
# @vacuity the current method is the NEWEST card's, not the first one's
#   file: record_fb.py
#   find: _current = next((r.get("card_method") for d in reversed(days) for r in d["rows"]
#   with: _current = next((r.get("card_method") for d in days for r in d["rows"]
#
# `[Sam, 2026-10-17]` ~~the page must draw every method, not `calibration`
#    alone (`const order = [cur]`)~~ and ~~an empty method says so on the page
#    (`fb-cal-empty`)~~: fbCalMethods and fbCalBlock left the page with "Was the
#    record right?". Both declarations are re-aimed at the boxes that replaced it.
# @vacuity 🔴 [Sam, 2026-10-17] the Board box reads the BOARD (props + game lines), not the props alone
#   file: index.html
#   find: const hero = `<div class="tr-hero">${trBox('Board', R && R.board)}${trBox('Player props', R && R.overall)}${
#   with: const hero = `<div class="tr-hero">${trBox('Board', R && R.overall)}${trBox('Player props', R && R.overall)}${
#
# @vacuity [Sam, 2026-10-17] a box with nothing graded says so, never "0 of 0"
#   file: index.html
#   find: <div class="s">${t && t.n ? `${t.w} of ${t.n} graded` : 'nothing graded yet'}</div></div>`;
#   with: <div class="s">${t && t.n ? `${t.w} of ${t.n} graded` : '0 of 0 graded'}</div></div>`;
#
# @vacuity 🔴 [Sam, 2026-10-17] the record's board counts the game lines as well as the props
#   file: record_fb.py
#   find: "board": tally(A + _gl_graded),
#   with: "board": tally(A),
#
# @vacuity [Sam, 2026-10-17] the planted game lines are the ones the card SHOWED (its liked list)
#   file: record_fb.py
#   find: if "game_lines_liked" in card:
#   with: if False:
#
# @vacuity 🔴 rule 67 on the planted tree: its three cards really are graded (the join settles them)
#   file: record_fb.py
#   find: hits.append(g)
#   with: pass
# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# 🔴 THE PLANTED TREE. `[2026-09-28]` The three states were built only
#    from the STORED cards, so NEXT METHOD needed stored graded rows and
#    TWO GRADED needed two stored graded cards (pattern P3): after a record
#    reset (`RECORD_FROM` moved), at a new lane, or on a slim tree, the
#    rule-67 check went red on correct code — and every declared mutation
#    above, which bites only through those states, went quiet with it.
# ✅ So all three states are ALSO built from a tree this file writes:
#    three graded cards (two under the method before the split, one under
#    the fixed method) and a players log that settles them, with the floor
#    pinned below them. The stored data is rebuilt as well, as an extra.
# ══════════════════════════════════════════════════════════════════════
PLANT_DATES = ("2026-09-12", "2026-09-19", "2026-09-26")
PLANT_METHOD = {"2026-09-26": "season-blend"}
PLANT_FLOOR = "2026-09-01"
PLANT_NAMES = ("Plant Alpha", "Plant Bravo", "Plant Charlie")

# `[Sam, 2026-10-17]` THE PLANTED GAME LINES, for the game-lines tracker Sam asked for. Three
#    final games in a planted schedule (schedule id -> away, home, kickoff, away pts, home pts)
#    and the rows the first two cards showed, each with the result a hand reads off the final:
#    True a hit, False a miss, None a push (void), "unshown" a row on the card's full list that
#    its liked list (the page's) left out, which is never graded.
PLANT_GAMES = {"PL1": ("Line Away 1", "Line Home 1", "2026-09-12T20:00:00Z", 20, 27),
               "PL2": ("Line Away 2", "Line Home 2", "2026-09-19T20:00:00Z", 17, 21),
               "PL3": ("Line Away 3", "Line Home 3", "2026-09-19T23:30:00Z", 20, 24)}
PLANT_LINES = (
    # card date,   game,  market,             side,   line, the result off the final
    ("2026-09-12", "PL1", "moneyline",        "home", None, True),       # 27-20, home wins
    ("2026-09-12", "PL1", "total",            "over", 44.5, True),       # 47 > 44.5
    ("2026-09-19", "PL2", "spread",           "away", 3.5,  False),      # away by -4, +3.5 short
    ("2026-09-19", "PL2", "alternate_spread", "home", -2.5, True),       # home by 4 covers -2.5
    ("2026-09-19", "PL3", "total",            "over", 44.0, None),       # 44 on 44: a push
    ("2026-09-19", "PL2", "moneyline",        "away", None, "unshown"),  # not on the liked list
)
PLANT_LIKED = "2026-09-19"          # the card whose game lines come from `game_lines_liked`


def plant_line(lg, gid, mk, side, line):
    away, home, ko = PLANT_GAMES[gid][:3]
    row = {"kind": "fb-line", "league": lg, "market": mk, "market_label": mk.replace("_", " "),
           "player": (home if side == "home" else away) if side in ("home", "away")
           else side.title(), "side": side, "line": line, "game": "%s @ %s" % (away, home),
           "away": away, "home": home, "commence": ko, "book": "fanduel", "price": -110,
           "confidence": 60, "confidence_basis": "MODEL", "break_even": 52.4}
    if mk == "alternate_spread":
        row["sched_id"] = gid          # as a stored card's alternate spread carries it
    return row


def plant_lines_want():
    """The planted game lines' hand-read record: (won, graded, voids)."""
    res = [x[5] for x in PLANT_LINES if x[5] != "unshown"]
    return (sum(1 for r in res if r is True), sum(1 for r in res if r is not None),
            sum(1 for r in res if r is None))


def plant(lg, tmp):
    """Write the planted cards and the log that grades them into `tmp`."""
    lat = os.path.join(tmp, "data", lg, "latest")
    os.makedirs(lat)
    os.makedirs(os.path.join(tmp, "picks"))
    # `[Sam, 2026-10-17]` the schedule that settles the planted game lines, and the model's
    #    snapshot that names each game's schedule id (`record_fb.line_ids`), as the stored
    #    tree has them.
    with gzip.open(os.path.join(lat, "schedule-2026.json.gz"), "wt") as fh:
        json.dump({"season": 2026, "games": [
            {"id": gid, "away": a, "home": h, "start": ko, "final": True,
             "away_score": ap, "home_score": hp}
            for gid, (a, h, ko, ap, hp) in PLANT_GAMES.items()]}, fh)
    snap = os.path.join(tmp, "data", lg, PLANT_DATES[0], "model-picks")
    os.makedirs(snap)
    with gzip.open(os.path.join(snap, "plant.json.gz"), "wt") as fh:
        json.dump({"game_model": [{"away": a, "home": h, "game_id": gid, "commence": ko}
                                  for gid, (a, h, ko, _ap, _hp) in PLANT_GAMES.items()]}, fh)
    players = {"p%d" % k: {"name": nm, "pos": "WR", "g": [
        {"d": d, "week": i + 1, "rec": 3 + k, "rec_yds": 30 + 20 * k, "car": 1,
         "rush_yds": 5, "rec_td": 0, "rush_td": 0, "pass_yds": 0, "pass_td": 0,
         "att": 0, "snaps": 40, "snap_pct": 0.8, "team": "T%d" % k}
        for i, d in enumerate(PLANT_DATES)]} for k, nm in enumerate(PLANT_NAMES)}
    with gzip.open(os.path.join(lat, "players-2026.json.gz"), "wt") as fh:
        json.dump({"season": 2026, "players": players}, fh)
    for d in PLANT_DATES:
        picks = [{"player": nm, "market": "player_reception_yds", "side": "over",
                  "line": 40.5, "price": -110, "book": "fanduel",
                  "confidence": 60 + 5 * k, "confidence_basis": "RECORD",
                  "raw": "%d of 10" % (5 + k), "commence": d + "T17:00:00Z",
                  "game": "A%d @ H%d" % (k, k), "break_even": 52.4}
                 for k, nm in enumerate(PLANT_NAMES)]
        # ⚠️ AND ONE UNRATED ROW: graded, but in no method's buckets.
        picks.append({"player": PLANT_NAMES[0], "market": "player_receptions",
                      "side": "under", "line": 3.5, "price": -120,
                      "book": "fanduel", "confidence_basis": "MARKET",
                      "commence": d + "T17:00:00Z", "game": "A0 @ H0"})
        card = {"date": d, "league": lg, "logs_season": 2025, "picks": picks}
        lines = [(plant_line(lg, gid, mk, side, ln), res)
                 for cd, gid, mk, side, ln, res in PLANT_LINES if cd == d]
        if lines:
            # `[Sam, 2026-10-17]` the card's full list, and on PLANT_LIKED the liked list the
            #    page shows (every card has one since #267), which leaves the "unshown" row out.
            card["game_lines"] = [r for r, _res in lines]
            if d == PLANT_LIKED:
                card["game_lines_liked"] = [dict(r) for r, res in lines if res != "unshown"]
        if d in PLANT_METHOD:
            card["card_method"] = PLANT_METHOD[d]
            # `[2026-10-16]` the newest planted card carries a `liked` list, as every card has
            #    since #267 (record_fb grades it in place of `picks`): the list the NEXT METHOD
            #    probe once left settle-able (collect went red 10-16).
            card["liked"] = [dict(x) for x in picks if x.get("confidence") is not None]
        json.dump(card, open(os.path.join(tmp, "picks", "fb-%s-%s.json" % (lg, d)),
                             "w", encoding="utf-8"))


def rebuild(lg, mutate=None, planted=False, src=ROOT):
    """Run THIS checkout's record_fb.py on a temp copy — of the stored data
    (`src`, the repo unless a guard below hands it a tree of its own), or of
    the planted tree. -> (R, D, rc, log)."""
    tmp = tempfile.mkdtemp(prefix="recfb-rebuild-")
    if planted:
        plant(lg, tmp)
    else:
        shutil.copytree(os.path.join(src, "data", lg),
                        os.path.join(tmp, "data", lg))
        os.makedirs(os.path.join(tmp, "picks"))
        for f in glob.glob(os.path.join(src, "picks", "fb-%s-*.json" % lg)):
            shutil.copy(f, os.path.join(tmp, "picks"))
    # ⛔ THE COMMITTED OUTPUT IS REMOVED FIRST, so a run that writes
    #    nothing cannot be read as a run that wrote the old file.
    for f in ("record.json", "record-detail.json.gz"):
        p = os.path.join(tmp, "data", lg, "latest", f)
        if os.path.exists(p):
            os.remove(p)
    if mutate:
        mutate(os.path.join(tmp, "picks"))
    env = dict(os.environ, LEAGUE=lg)
    if planted:
        # ⛔ the planted cards are graded whatever the source's floor is set to
        env["FB_RECORD_FROM"] = PLANT_FLOOR
    # 🔴 `[2026-10-17]` THE CODE SITS IN THE TREE IT GRADES. ~~ROOT's record_fb.py run with
    #    cwd=tmp~~: record_fb reads the cards and logs from its working directory, but the game
    #    lines' schedule through `game_lines_fb.schedule_by_id`, which reads beside its OWN
    #    file. Run from ROOT, the planted game lines were looked up in the checkout's stored
    #    schedule (production) and found no game. ✅ This checkout's record_fb.py and every
    #    repo-local module it imports are COPIED into the tree (`copy_module`, the harness
    #    test_record_fb.py uses), so the same code reads only this tree, as it does in the repo.
    copy_module("record_fb.py", tmp)
    p = subprocess.run([sys.executable, os.path.join(tmp, "record_fb.py")],
                       cwd=tmp, env=env, capture_output=True, text=True,
                       timeout=900)
    R = D = None
    rp = os.path.join(tmp, "data", lg, "latest", "record.json")
    dp = os.path.join(tmp, "data", lg, "latest", "record-detail.json.gz")
    if os.path.exists(rp):
        R = json.load(open(rp, encoding="utf-8"))
    if os.path.exists(dp):
        D = json.load(gzip.open(dp, "rt"))
    shutil.rmtree(tmp, ignore_errors=True)
    return R, D, p.returncode, (p.stdout or "") + (p.stderr or "")


def dated_cards(pdir, lg):
    return sorted(f for f in glob.glob(os.path.join(pdir, "fb-%s-*.json" % lg))
                  if not f.endswith("-latest.json"))


def graded_list(card):
    """The list record_fb grades a card on: `[Sam, 2026-10-15]` what it SHOWS, its
    `liked` list whenever it has one, else its `picks`."""
    return (card.get("liked") if "liked" in card else card.get("picks")) or []


def probe_blocked(root, lg):
    """Why the NEXT METHOD probe could not become current on this tree, or None.
    ⛔ `[2026-10-18]` A TEST ASKS THE CODE, NEVER PRODUCTION. On the stored data the
    probe borrows the newest card with rows and is dated two days after the newest
    card. Two correct trees leave it nothing the grader can grade: no stored card
    with rows in the list it is graded on, and a probe dated in a season whose log
    is not stored. ~~(record_fb reads the log of the card's calendar year, so from
    12-30 the probe lands in a 2027 nobody has a log for until August)~~ `[2026-10-27]`
    record_fb reads the log of the card's FOOTBALL season (fb_why.season_of), so a
    probe dated 01-02 is graded from the season before. The planted tree asks the
    question every run either way."""
    fs = dated_cards(os.path.join(root, "picks"), lg)
    if not fs or not any(graded_list(json.load(open(f, encoding="utf-8"))) for f in fs):
        return "no stored card carries rows in the list it is graded on"
    last = datetime.strptime(os.path.basename(fs[-1])[len("fb-%s-" % lg):-5], "%Y-%m-%d")
    season = fb_why.season_of((last + timedelta(days=2)).strftime("%Y-%m-%d"))
    lp = os.path.join(root, "data", lg, "latest", "players-%d.json.gz" % season)
    if not (os.path.exists(lp) and json.load(gzip.open(lp, "rt")).get("players")):
        return ("the probe would be dated %s, and no %d log is stored to grade it"
                % ((last + timedelta(days=2)).strftime("%Y-%m-%d"), season))
    return None


UNSETTLED = "2099-12-31T00:00:00Z"


def unsettled(card):
    """`card` with every row of EVERY list kicking off beyond any log, so nothing on it can
    settle. `[2026-10-16]` ~~only `picks`~~: since #267 record_fb grades a card's `liked`
    list, and the copy's liked props (Thursday's, settled by the 07:29Z log) were graded
    under the new method, so its record was no longer empty (collect red 10-16).
    `[2026-10-17]` and with no schedule id: record_fb now grades the game lines a card
    showed, and an alternate spread's `sched_id` settles it from the final score whatever
    its kickoff says."""
    def off(r):
        r = dict(r, commence=UNSETTLED)
        if "sched_id" in r:
            r["sched_id"] = None
        return r
    return {k: ([off(r) if isinstance(r, dict) and "commence" in r else r for r in v]
                if isinstance(v, list) else v) for k, v in card.items()}


def add_next_method_card(lg):
    """The night a new method goes live: a card dated after every other one,
    under a method nothing has graded yet.
    ⚠️ `[2026-10-09]` BUILT, NOT BORROWED. It was a copy of the newest stored
    card, and ncaaf's 10-08 card held 0 picks (10 game lines): the copy had no
    rows, the record dropped it, the new method never became current, and
    collect went red 10-08 -> 10-09. So a games-only card is ALWAYS planted
    newest first, and the new card takes the picks of the newest card that
    has some. Nothing here reads a clock: record_fb grades on the stored logs."""
    def m(pdir):
        fs = dated_cards(pdir, lg)
        last = datetime.strptime(os.path.basename(fs[-1])[len("fb-%s-" % lg):-5], "%Y-%m-%d")

        def put(k, card):
            d = (last + timedelta(days=k)).strftime("%Y-%m-%d")
            json.dump(dict(card, date=d), open(os.path.join(pdir, "fb-%s-%s.json" % (lg, d)),
                                               "w", encoding="utf-8"))
        put(1, dict(json.load(open(fs[-1], encoding="utf-8")), picks=[], liked=[]))     # games only
        # `[2026-10-18]` ~~the newest card with `picks`~~: the newest with rows in the
        #    list record_fb GRADES. A card with 25 picks and an empty liked list
        #    (`best_liked`: "fewer is fine") gave the probe no row, so it never became
        #    current and the checks below went red on correct code.
        src = [c for c in (json.load(open(f, encoding="utf-8")) for f in dated_cards(pdir, lg))
               if graded_list(c)][-1]
        # ⚠️ Kickoffs beyond any log, so nothing on it can settle — the
        #    state of a card the night it is published.
        put(2, dict(unsettled(src), card_method=PROBE_NEXT))
    return m


def restamp_graded_card(lg, date):
    """One card that HAS graded rows, re-stamped with a second method."""
    def m(pdir):
        f = os.path.join(pdir, "fb-%s-%s.json" % (lg, date))
        card = json.load(open(f, encoding="utf-8"))
        card["card_method"] = PROBE_GRADED
        json.dump(card, open(f, "w", encoding="utf-8"))
    return m


BOX = re.compile(r'<div class="tr-box"><div class="k">([^<]*)</div>\s*'
                 r'<div class="v">([^<]*)</div>\s*<div class="s">([^<]*)</div></div>')
# `[Sam, 2026-10-17]` what the old tab drew and the new one must not: the bands, their
#    heading and every method's label (fbCalMethods / fbCalBlock / bandRow are gone).
GONE = ("Was the record right?", 'class="band"', "we said", "the record claimed",
        "fb-cal-empty", "current method", "earlier method", "2025-only method")


def page(R, lg="nfl"):
    """The tab's own `fbRecord`, run under node on record `R` (None: no record file yet).
    `[Sam, 2026-10-17]` ~~`fbCalMethods` alone~~: the whole tab, three hit rates and two
    by-date lists. Only the loader, the shell and the DOM are stubbed; `trBox`, `fbDayRows`,
    `fbLineDayRows` and `fbRecord` are the page's own. -> what it drew."""
    src = "\n".join(js_block(n, IDX) for n in ("trBox", "fbDayRows", "fbLineDayRows",
                                               "fbRecord"))
    decl = re.search(r"^const LG_NAME\s*=\s*\{[^\n]*\};",
                     open(IDX, encoding="utf-8").read(), re.M)
    assert decl, "index.html no longer declares LG_NAME"
    prog = (decl.group(0) + "\n"
            "const LEAGUE = " + json.dumps(lg) + ";\n"
            "const VIEW = {innerHTML: ''};\n"
            "const $ = s => (s === '#fbview' ? VIEW : null);\n"
            "const fbShell = x => x, fbWire = () => {}, fbWireDayRows = () => {};\n"
            "const freshness = s => String(s);\n"
            + src + "\nconst REC = " + json.dumps(R) + ";\n"
            "const fbRecordLoad = async () => REC;\n"
            "fbRecord().then(() => console.log(JSON.stringify({h: VIEW.innerHTML})),"
            " e => console.log(JSON.stringify({err: String(e)})));")
    d = tempfile.mkdtemp(prefix="recfb-page-")
    f = os.path.join(d, "probe.js")
    open(f, "w", encoding="utf-8").write(prog)
    p = subprocess.run(["node", f], capture_output=True, text=True, timeout=120)
    shutil.rmtree(d, ignore_errors=True)
    out = next((json.loads(x) for x in (p.stdout or "").splitlines() if x.startswith("{")), None)
    if not out or "h" not in out:
        return {"__rc": p.returncode, "__out": (out or {}).get("err")
                or ((p.stdout or "") + (p.stderr or ""))[-400:]}
    h = out["h"]
    return {"boxes": [list(m) for m in BOX.findall(h)],
            "heads": re.findall(r"<h3[^>]*>([^<]*)</h3>", h),
            "tables": h.count("<table"),
            "dates": re.findall(r'data-date="([^"]*)"', h),
            "gldates": re.findall(r'data-gldate="([^"]*)"', h),
            "gone": [g for g in GONE if g in h]}


def box(k, rows):
    """The box the tab must draw for `rows` (graded detail rows): the grader's numbers."""
    n, w = len(rows), sum(1 for r in rows if r["won"])
    return ([k, "%.1f%%" % round(100 * w / n, 1), "%d of %d graded" % (w, n)] if n
            else [k, "&mdash;", "nothing graded yet"])


def check(lg, tag, R, D, rc, log, expect_methods=None, expect_current=None,
          expect_lines=None):
    """The record and the page questions, asked of one rebuilt record."""
    ok = rc == 0 and R is not None and D is not None
    ck(ok, "%s %s: this checkout's record_fb.py rebuilt both files" % (lg, tag),
       "rc=%s %s" % (rc, log[-300:]))
    if not ok:
        return
    by = R.get("calibration_by_method")
    cur = R.get("card_method_current")
    ck(isinstance(by, dict) and isinstance(cur, str),
       "   %s: the record carries `calibration_by_method` and its current method" % tag,
       "current=%r" % cur)
    by = by or {}
    graded = [r for rows in (D.get("days") or {}).values() for r in rows
              if r.get("won") is not None and r.get("confidence") is not None]
    want = {}
    for r in graded:
        m = r.get("card_method") or BEFORE
        want[m] = want.get(m, 0) + 1
    got = {m: sum(c["n"] for c in v) for m, v in by.items()}
    ck(got == want and sum(got.values()) == len(graded),
       "🔴🔴 %s %s: every graded row with a confidence is in exactly one "
       "method's buckets" % (lg, tag),
       "buckets %s vs detail rows %s (of %d)" % (got, want, len(graded)))
    ck(R.get("calibration") == by.get(cur, []),
       "   %s: `calibration` is the current method's buckets, never a pool" % tag,
       "current=%r" % cur)
    if expect_current is not None:
        eq(cur, expect_current,
           "   %s: the current method is the NEWEST card's" % tag)
    if expect_methods is not None:
        eq(sorted(got), sorted(expect_methods),
           "   %s: the methods holding graded rows are the ones stamped" % tag)
    for m in [cur] + [m for m in by if m != cur]:
        if not by.get(m):
            note("⚠️ %s %s: method %r has no graded picks yet — reported, "
                 "not failed (the record keeps its buckets; the tab no longer "
                 "draws them)" % (lg, tag, m))

    # 🔴 `[Sam, 2026-10-17]` THE BOARD AND THE GAME-LINES TRACKER, asked of the DETAIL rows
    #    the grader wrote, never of its own summary: "board(all picks), player props(only
    #    player props), and game line(only game lines)".
    props = [r for rows in (D.get("days") or {}).values() for r in rows
             if r.get("won") is not None]
    gld = D.get("game_lines")
    ck(isinstance(gld, dict),
       "   %s: the detail file carries the game lines by day" % tag,
       "got %s" % type(gld).__name__)
    gld = gld if isinstance(gld, dict) else {}
    lines = [r for rows in gld.values() for r in rows if r.get("won") is not None]
    B = R.get("board") or {}
    eq((B.get("w"), B.get("n")),
       (sum(1 for r in props + lines if r["won"]), len(props) + len(lines)),
       "🔴 %s %s: the record's board is every graded pick, its player props AND its "
       "game lines" % (lg, tag))
    G = R.get("game_lines") or {}
    eq({d.get("date"): (d.get("w"), d.get("n")) for d in G.get("by_day") or []},
       {d: (sum(1 for r in rows if r.get("won")),
            sum(1 for r in rows if r.get("won") is not None)) for d, rows in gld.items()},
       "   %s: the game lines' days reconcile with the detail rows, day by day" % tag)
    if expect_lines is not None:
        eq((sum(1 for r in lines if r["won"]), len(lines),
            sum(1 for rows in gld.values() for r in rows if r.get("state") == "void")),
           expect_lines,
           "🔴 %s %s: the planted game lines grade as a hand reads the finals "
           "(won, graded, void), the liked list's rows only" % (lg, tag))

    P = page(R, lg)
    eq(P.get("boxes"),
       [box("Board", props + lines), box("Player props", props), box("Game lines", lines)],
       "🔴🔴 %s %s: [Sam, 2026-10-17] the tab draws three hit rates, Board / Player "
       "props / Game lines, each the rebuilt record's own (~~one band table per "
       "method~~)" % (lg, tag))
    eq(P.get("gone"), [],
       "🔴🔴 %s %s: [Sam, 2026-10-17] NO band, no \"Was the record right?\" and no "
       "method table on the tab (~~no band says \"we said\"~~)" % (lg, tag))
    eq((P.get("heads"), P.get("tables")),
       (["Player props by day", "Game lines by day"], 2),
       "   %s: below the boxes only the two by-date lists (his choice)" % tag)
    eq(P.get("dates"), [d["date"] for d in reversed(R.get("by_day") or []) if d.get("n")],
       "   %s: the props list opens exactly the record's graded days, newest first" % tag)
    eq(P.get("gldates"),
       [d["date"] for d in reversed(G.get("by_day") or [])
        if d.get("n") or d.get("voids")],
       "   %s: the game-lines list opens exactly the record's graded days, newest first"
       % tag)


def graded_dates_of(D):
    """Card dates holding a graded row with a confidence, from a detail file."""
    return sorted(d for d, rows in ((D or {}).get("days") or {}).items()
                  if any(r.get("won") is not None
                         and r.get("confidence") is not None for r in rows))


def three_states(lg, planted, root=ROOT):
    """STORED, NEXT METHOD and TWO GRADED, on the planted tree or the stored data
    (`root`'s; the guards below hand it trees of their own)."""
    src = "PLANTED" if planted else "STORED DATA"
    R, D, rc, log = rebuild(lg, planted=planted, src=root)
    # `[Sam, 2026-10-17]` every planted state holds the planted game lines unchanged
    lines = plant_lines_want() if planted else None
    check(lg, "%s" % src, R, D, rc, log,
          expect_methods=(sorted({BEFORE, "season-blend"}) if planted else None),
          expect_current=("season-blend" if planted else None), expect_lines=lines)
    graded_dates = graded_dates_of(D)
    if planted:
        # ⚠️ RULE 67, ON THE TREE THIS FILE WROTE: the case must exist.
        if not ck(graded_dates == list(PLANT_DATES),
                  "   %s PLANTED: all three planted cards hold graded rows" % lg,
                  "⛔ with fewer, TWO GRADED cannot hold two graded methods and "
                  "would prove nothing. got %s" % graded_dates):
            return
    elif len(graded_dates) < 2:
        note("⚠️ NOT EXERCISED ON THE STORED DATA (%s): %d stored card(s) hold "
             "graded rows — a record reset or a new lane. The planted tree "
             "asked every question." % (lg, len(graded_dates)))
        return
    _why = None if planted else probe_blocked(root, lg)
    if _why:
        note("⚠️ NEXT METHOD NOT EXERCISED ON THE STORED DATA (%s): %s. The planted "
             "tree asked it." % (lg, _why))
    else:
        R2, D2, rc2, log2 = rebuild(lg, add_next_method_card(lg), planted=planted, src=root)
        check(lg, "%s + NEXT METHOD" % src, R2, D2, rc2, log2, expect_current=PROBE_NEXT,
              expect_lines=lines)
        if R2 is not None:
            ck(R2.get("calibration") == [] and any(
                   v for v in (R2.get("calibration_by_method") or {}).values()),
               "   %s %s NEXT METHOD: the new method is empty while earlier ones are "
               "graded — the exact state main was in when #158 merged" % (lg, src),
               "⛔ if this is not the state, the section above did not test it")
    R3, D3, rc3, log3 = rebuild(lg, restamp_graded_card(lg, graded_dates[-1]),
                                planted=planted, src=root)
    before = sorted({(r.get("card_method") or BEFORE)
                     for d, rows in D["days"].items()
                     if d != graded_dates[-1] for r in rows
                     if r.get("won") is not None
                     and r.get("confidence") is not None})
    check(lg, "%s + TWO GRADED" % src, R3, D3, rc3, log3,
          expect_methods=sorted(set(before) | {PROBE_GRADED}), expect_lines=lines)


section("THE TAB BEFORE ANYTHING IS GRADED")
# `[Sam, 2026-10-17]` ~~a method with nothing graded says so on the page~~: no method is
#    drawn now. The empty state that is left is a box with nothing behind it, the night a
#    league has no record file yet (the loader returns null): "nothing graded" and "graded
#    0%" are different facts, so every box reads em-dash and says so.
for lg in ("nfl", "ncaaf"):
    P0 = page(None, lg)
    eq(P0.get("boxes"), [box(k, []) for k in ("Board", "Player props", "Game lines")],
       "🔴 %s: [Sam, 2026-10-17] with no record, each of the three boxes says nothing is "
       "graded, never 0%%" % lg)
    eq((P0.get("gone"), P0.get("dates"), P0.get("gldates")), ([], [], []),
       "   %s: ...and draws no band and no clickable day" % lg)

for lg in ("nfl", "ncaaf"):
    section("%s — REBUILT FROM THIS CHECKOUT'S record_fb.py" % lg.upper())
    three_states(lg, planted=True)
    three_states(lg, planted=False)

section("THE STORED-DATA PROBE ON TWO CORRECT TREES IT ONCE FAILED")
# `[2026-10-18]` The guards for `probe_blocked` and the probe's source, built here
# rather than waited for from picks/: the planted tree run as STORED DATA, plus one
# card. (1) A newest card dated 12-31 puts the probe on 01-02: ~~in 2027, with no 2027
# log: the stored path must note and add no failure~~ `[2026-10-27]` the grader reads
# that probe's log by its football season, 2026, so NEXT METHOD runs and passes (read
# by the calendar year it was skipped, and this is red). (2) A newest card with 25-style picks and
# an EMPTY liked list: the probe must take the last card with rows in its graded list,
# so NEXT METHOD runs and passes (taken by `picks`, it graded nothing and went red).
import tcheck as _TC  # noqa: E402


def _guard_tree(lg, date, liked_empty):
    g = tempfile.mkdtemp(prefix="recfb-guard-")
    plant(lg, g)
    newest = json.load(open(os.path.join(g, "picks", "fb-%s-%s.json" % (lg, PLANT_DATES[-1])),
                            encoding="utf-8"))
    card = {k: v for k, v in unsettled(newest).items()
            if k not in ("game_lines", "game_lines_liked")}
    card["date"] = date
    if liked_empty:
        card["liked"] = []
    json.dump(card, open(os.path.join(g, "picks", "fb-%s-%s.json" % (lg, date)), "w",
                         encoding="utf-8"))
    return g


for _tag, _date, _empty, _want_note in (("YEAR TURN", "2026-12-31", False, False),
                                         ("LIKED EMPTY", "2026-09-27", True, False)):
    _g = _guard_tree("nfl", _date, _empty)
    _nf0, _nn0 = len(_TC.FAILURES), len(_TC._NOTES)
    try:
        three_states("nfl", planted=False, root=_g)
    finally:
        shutil.rmtree(_g, ignore_errors=True)
    _noted = any("NEXT METHOD NOT EXERCISED" in str(n) for n in _TC._NOTES[_nn0:])
    ck(len(_TC.FAILURES) == _nf0 and _noted == _want_note,
       "🔴 %s: a newest stored card dated %s%s %s, never a failure" % (
           _tag, _date, " with an empty liked list" if _empty else "",
           "NOTES the probe as not exercised" if _want_note else "still runs NEXT METHOD"),
       "failures added %d, noted %s" % (len(_TC.FAILURES) - _nf0, _noted))

note("⛔ WHAT THIS DOES NOT CLAIM: that the stored data is correct, or that "
     "the tab LOOKS right in a browser. It claims the record this "
     "checkout's code WOULD write — today, the night a new method goes "
     "live, and once two methods both hold graded rows — keeps every "
     "method apart, ~~and that the tab draws each one under its own label~~ "
     "[Sam, 2026-10-17] and that the tab draws the three hit rates (Board, "
     "Player props, Game lines) from it and no method's bands.")
