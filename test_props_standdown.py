#!/usr/bin/env python3
"""ONE ANSWER TO "IS THIS PROPS PULL OWED?", AND A DEADLINE THAT PASSES AFTER
THE PASS LOOKED IS THE NEXT PASS'S.

`[2026-10-24]` collect went red near 15:00Z three times in a week, each time
"props-player MISSED its 7:00/11:00 ET build ... nfl is out of contract":
  - 10-18 (39137387911) and 10-24 (40103939010): an NFL props pull landed 23
    minutes before the 11:00 ET (15:00Z) deadline. The next pass's plan owed a
    pull; `collect.props_is_fresh` refused it ("a pull landed 24 min ago
    (window 45 min). Standing down, NOTHING SPENT."), and the gate failed the
    run "last built 29m ago, 6m past due". That 14:37Z pull was itself a
    second pull for the 7am deadline (11:27Z had met it), bought by a cron
    3.5 hours late.
  - 10-19 (39271299253): the pass bought the 7am pull at 14:58Z, its last
    survey (freshness.json, 14:59:59Z) had every props row inside contract,
    and the gate ran at 15:00:01.9Z: "MISSED ... last built 2m ago", 1.9 s
    after the 11am deadline, with no "past due" at all.
Every case is planted in a throwaway tree, and BOTH clocks (collect's `now` and
freshness's) are pinned to the case's own minute, so today's code is replayed
as it ran. Nothing reads production data.

# @vacuity 🔴🔴 the stand-down judges its pull through the contract
#   file: collect.py
#   find:     r = _fresh.pull_owed(LEAGUE, DATA, "props-" + kind, now())
#   with:     r = dict(_fresh.pull_owed(LEAGUE, DATA, "props-" + kind, now()), stale=False)
#
# @vacuity 🔴🔴 an owed pull is never refused for being under 45 minutes old
#   file: collect.py
#   find:     if r["stale"]:
#   with:     if r["stale"] and (r["age_min"] is None or r["age_min"] > 45):
#
# @vacuity 🔴 a deadline already met is not bought twice
#   file: collect.py
#   find:     if r["stale"]:
#   with:     if r["stale"] or (r["age_min"] or 0) > 45:
#
# @vacuity 🔴 the stand-down judges ONE pull, not the first row of the contract
#   file: freshness.py
#   find:             contract(data, picks, now) if entries is None else entries):
#   with:             contract(data, picks, now)):
#
# @vacuity 🔴 football props answer football's deadlines
#   file: freshness.py
#   find:     return FB_TIMES[league]["props"] if league in FB_TIMES else ODDS
#   with:     return ODDS
#
# @vacuity 🔴🔴 the gate leaves a deadline that passed after the last survey to the next pass
#   file: freshness.py
#   find:             if (r["mode"], r["path"]) in later:
#   with:             if False:
#
# @vacuity 🔴 ...only ONE deadline since that survey
#   file: freshness.py
#   find:         if first is not None and first.strftime("%Y-%m-%dT%H:%MZ") == r["due_at"]:
#   with:         if first is not None:
#
# @vacuity 🔴 ...only for a row that survey found inside contract
#   file: freshness.py
#   find:                 or not rec or rec.get("stale") is not False or not t):
#   with:                 or not rec or not t):
#
# @vacuity 🔴 the gate says so in words
#   file: verify_freshness.py
#   find:         if r.get("_after_survey"):
#   with:         if False:
#
# @vacuity ⚠️ a miss under a minute still says how far past due it is
#   file: verify_freshness.py
#   find:         late = f", {int(r['late_min'])}m past due" if r["late_min"] is not None else ""
#   with:         late = f", {int(r['late_min'])}m past due" if r["late_min"] else ""
"""
import contextlib
import datetime
import gzip
import io
import json
import os
import shutil
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import collect as C  # noqa: E402
import freshness as F  # noqa: E402
import verify_freshness as VF  # noqa: E402
from tcheck import ck, eq, note, section, shown  # noqa: E402

UTC = datetime.timezone.utc
PIN = [None]
LOGS = []
TREES = []


class _Clock(datetime.datetime):
    """freshness's clock, pinned to PIN[0]. ⚠️ Today's `props_is_fresh` aged its
    snapshot with freshness's own `datetime.now`, not collect's `now()`, so a
    replay pinning only collect would run today's code on the real clock."""
    @classmethod
    def now(cls, tz=None):
        return PIN[0] if tz else PIN[0].replace(tzinfo=None)


F.datetime = types.SimpleNamespace(datetime=_Clock, date=datetime.date, time=datetime.time,
                                   timedelta=datetime.timedelta, timezone=datetime.timezone)
C.log = lambda *a, **k: LOGS.append(" ".join(str(x) for x in a))


def at(s):
    """'2026-10-24T15:00:51Z', or with a fraction ('...15:00:01.9Z')."""
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def clock(t):
    PIN[0] = t
    C.now = lambda: t


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def put(path, doc):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with (gzip.open(path, "wt") if path.endswith(".gz") else open(path, "w", encoding="utf-8")) as fh:
        json.dump(doc, fh)
    return path


def league(lg):
    """Point collect at one league, as its own run would be."""
    C.LEAGUE, C.SPORT = lg, C.LEAGUES[lg]["sport"]
    C.DATA, C.PICKS = C.LEAGUES[lg]["data"], C.LEAGUES[lg]["picks"]
    C.LATEST = f"{C.DATA}/latest"
    return C.DATA


@contextlib.contextmanager
def tree():
    d = tempfile.mkdtemp(prefix="standdown-")
    TREES.append(d)
    here = os.getcwd()
    os.chdir(d)
    try:
        yield d
    finally:
        os.chdir(here)


# The NFL's next slate on 10-24: twelve Sunday games, 26 hours out.
GAMES = [{"id": f"ev{i:02d}", "home_team": f"Home {i}", "away_team": f"Away {i}",
          "commence_time": "2026-10-25T17:00:00Z"} for i in range(12)]


def snapshot(data, kind, t, regions, games=GAMES):
    """A paid props snapshot as `collect_props` writes it, named by its minute."""
    return put(f"{data}/{t:%Y-%m-%d}/{kind}/{t:%H%M}.json.gz", {
        "pulled_at": iso(t), "endpoint": "per-event", "regions": regions,
        "credits_used": 6 * len(regions.split(",")) * len(games), "credits_remaining": 19000,
        "n_events": len(games), "events": [dict(g, bookmakers=[BOOK]) for g in games]})


BOOK = {"key": "hardrockbet", "markets": [{"key": "player_reception_yds", "outcomes": [
    {"name": "Over", "description": "A Receiver", "point": 55.5, "price": -110},
    {"name": "Under", "description": "A Receiver", "point": 55.5, "price": -110}]}]}


def healthy(data, t, start="2026-10-25T13:00", skip=("props-player", "props-board", "alt-lines")):
    """Every other row of the league's contract, built at `t`: the gate's verdict
    is then about the props rows alone. `start`: the next NFL kickoff (ET), which
    the schedule row carries, so the contract holds the props rows as warranted."""
    for mode, (kind, path), _times, _paid, _why in F.contract(data, "picks", t):
        if mode in skip:
            continue
        if kind == "dir":
            put(f"{path}/{t:%H%M}.json.gz", {})
        else:
            put(path, {"built_at": iso(t), "games": [{"start": start}]})


def buy(t):
    """The REAL NFL props pull at `t`, the API stubbed. -> per-game calls made."""
    calls, old = [], C.odds_get
    clock(t)

    def _get(path, params=None):
        calls.append(path)
        if path.endswith("/events"):
            return [dict(g) for g in GAMES], 0, 19000
        eid = path.split("/")[-2]
        return dict(next(g for g in GAMES if g["id"] == eid), bookmakers=[BOOK]), 6, 18900
    C.odds_get = _get
    try:
        C.collect_props("player", C.REGIONS_CHEAP)
    finally:
        C.odds_get = old
    return [c for c in calls if not c.endswith("/events")]


def join(t):
    clock(t)
    C.collect_props_board_fb()


def last_survey(t):
    """The converge pass's own final survey, written by the REAL writer."""
    clock(t)
    C.write_freshness(F.survey(C.DATA, "picks", t))


def gate(t):
    """The REAL gate at `t` -> (exit code, what it printed)."""
    clock(t)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = VF.main()
    return rc, out.getvalue()


def standdown(t, kind="player"):
    clock(t)
    del LOGS[:]
    return C.props_is_fresh(kind)


def errors(text):
    return [l for l in text.splitlines() if "MISSED" in l]


VF._DATA = league("nfl")
try:
    # ══════════════════════════════════════════════════════════════════
    section("1. 🔴🔴 10-24, REPLAYED: A PULL 23 MINUTES BEFORE THE DEADLINE NO LONGER BLOCKS IT")
    # ══════════════════════════════════════════════════════════════════
    with tree():
        data = C.DATA
        snapshot(data, "props-player", at("2026-10-24T11:27:46Z"), "us,us2")
        ck(standdown(at("2026-10-24T14:37:50Z")),
           "💰 14:37:50Z, the 7am cron 3.5 hours late: the 11:27Z pull already met the 7am "
           "deadline, so it stands down (10-24 bought it again, 72 credits)", shown(LOGS))
        # ⚠️ What follows is the deadline that second pull tripped, so it is
        #    planted as it happened.
        snapshot(data, "props-player", at("2026-10-24T14:37:50Z"), "us2")
        join(at("2026-10-24T14:37:55Z"))
        put(f"{data}/2026-10-24/alt-lines/1500.json.gz", {})      # the pass's own, bought 0
        healthy(data, at("2026-10-24T15:00:30Z"))
        clock(at("2026-10-24T15:00:40Z"))
        plan, _rows = F.plan(data, "picks", at("2026-10-24T15:00:40Z"))
        ck("props-player" in plan, "the 15:00:40Z plan owes props-player, as 10-24's did", plan)
        ck(not standdown(at("2026-10-24T15:00:51Z")),
           "🔴🔴 15:00:51Z: the contract owes the pull and the stand-down does not refuse it "
           "(10-24: 'a pull landed 24 min ago (window 45 min). Standing down')", shown(LOGS))
        eq(len(buy(at("2026-10-24T15:00:51Z"))), 12,
           "🔴 ...so the real pull buys the twelve games")
        join(at("2026-10-24T15:01:04Z"))
        last_survey(at("2026-10-24T15:01:44Z"))
        rc, out = gate(at("2026-10-24T15:06:24Z"))
        ck(rc == 0 and not errors(out),
           "🔴🔴 the real gate at 15:06:24Z passes (10-24: props-player and props-board "
           "MISSED, 6m past due)", f"rc={rc} " + shown(errors(out)))
        ck(standdown(at("2026-10-24T16:01:50Z")),
           "💰 16:01:50Z, the 11am cron late: 15:00:51Z met the 11am deadline, so it stands "
           "down (10-24 bought this one, 72 credits)", shown(LOGS))

    # ══════════════════════════════════════════════════════════════════
    section("2. 🔴🔴 10-19, REPLAYED: A DEADLINE THAT PASSED AFTER THE PASS LOOKED IS THE NEXT PASS'S")
    # ══════════════════════════════════════════════════════════════════
    ONE = GAMES[:1]
    MNF = "2026-10-19T20:15"          # 10-19's one game: Monday night, 8:15pm ET

    def straddle(survey_at):
        snapshot(C.DATA, "props-player", at("2026-10-19T14:58:33Z"), "us,us2", ONE)
        join(at("2026-10-19T14:58:48Z"))
        put(f"{C.DATA}/2026-10-19/alt-lines/1458.json.gz", {})
        healthy(C.DATA, at("2026-10-19T14:58:00Z"), MNF)
        if survey_at:
            last_survey(at(survey_at))

    with tree():
        straddle("2026-10-19T14:59:59Z")
        rec = {r["mode"]: r for r in json.load(open(f"{C.LATEST}/freshness.json"))["artifacts"]}
        eq([rec[m]["stale"] for m in ("props-player", "props-board", "alt-lines")], [False] * 3,
           "the pass's last survey, 14:59:59Z, had every props row inside contract (as 10-19's did)")
        rc, out = gate(at("2026-10-19T15:00:01.9Z"))
        ck(rc == 0 and not errors(out),
           "🔴🔴 the real gate 1.9 s after the 11am deadline passes (10-19: 'props-player MISSED "
           "its 7:00/11:00 ET build: last built 2m ago')", f"rc={rc} " + shown(errors(out)))
        ck("::warning::props-player is due for its 15:00Z deadline, which passed after this "
           "league's last survey (14:59:59Z)" in out,
           "🔴 ...and says why, in words, as a warning",
           shown([l for l in out.splitlines() if "props-player" in l and "::" in l]))
        ck(not standdown(at("2026-10-19T15:10:00Z")),
           "🔴 the next pass, 15:10Z, buys the 11am pull (today's window stood it down until "
           "15:43Z, red every pass)", shown(LOGS))
        last_survey(at("2026-10-19T15:10:30Z"))
        rc, out = gate(at("2026-10-19T15:11:00Z"))
        ck(rc == 1 and any(l.startswith("::error::props-player MISSED") for l in out.splitlines()),
           "⛔ CONTROL: a pass that surveyed past the deadline and built nothing is still red",
           shown(errors(out)))

    with tree():
        straddle("2026-10-19T14:59:59Z")
        doc = json.load(open(f"{C.LATEST}/freshness.json"))
        for a in doc["artifacts"]:
            if a["mode"] == "props-player":
                a["stale"] = True
        put(f"{C.LATEST}/freshness.json", doc)
        rc, out = gate(at("2026-10-19T15:00:01.9Z"))
        ck(rc == 1 and errors(out), "⛔ CONTROL: a row that last survey already saw stale is "
           "still red", shown(errors(out)))

    with tree():
        snapshot(C.DATA, "props-player", at("2026-10-19T10:58:00Z"), "us,us2", ONE)
        join(at("2026-10-19T10:58:10Z"))
        put(f"{C.DATA}/2026-10-19/alt-lines/1458.json.gz", {})
        healthy(C.DATA, at("2026-10-19T14:58:00Z"), MNF)
        last_survey(at("2026-10-19T10:59:00Z"))
        rc, out = gate(at("2026-10-19T15:00:01.9Z"))
        ck(rc == 1 and errors(out), "⛔ CONTROL: two deadlines since the last survey (11:00Z "
           "and 15:00Z) are red", shown(errors(out)))

    with tree():
        straddle(None)
        rc, out = gate(at("2026-10-19T15:00:01.9Z"))
        ck(rc == 1 and errors(out), "⛔ CONTROL: with no recorded survey the gate is as "
           "strict as before", shown(errors(out)))
        ck(any("props-player MISSED" in l and "0m past due" in l for l in out.splitlines()),
           "⚠️ ...and a miss 1.9 s old says '0m past due' (10-19's line said nothing)",
           shown(errors(out)))

    # ══════════════════════════════════════════════════════════════════
    section("3. 🔴🔴 THE CLASS: THE STAND-DOWN AND THE CONTRACT GIVE ONE ANSWER, EVERY LEAGUE")
    # ══════════════════════════════════════════════════════════════════
    # Every paid props kind, around both of its deadlines: a pull at each
    # offset, checked at each later minute. The stand-down must stand down
    # exactly when the contract (the survey `plan()` and the gate read) says
    # the pull is not owed.
    PULLS = (-180, -46, -45, -44, -23, -2, 0, 1, 8, 44, 46, 190)
    CHECKS = (-60, -1, 0, 1, 6, 15, 24, 44, 46, 61, 90, 200)
    split, judged, absent = [], 0, 0
    for lg, kinds in (("mlb", ("pitcher", "batter")), ("nfl", ("player",)), ("ncaaf", ("player",))):
        data = league(lg)
        for kind in kinds:
            # the deadlines are the CONTRACT ROW's own (the reference), not
            # the list the stand-down reads
            with tree():
                times = {m: tm for m, _p, tm, _paid, _w in
                         F.contract(data, "picks", at("2026-10-21T12:00:00Z"))}[f"props-{kind}"]
            for hh, mm in times:
                due = datetime.datetime(2026, 10, 21, hh, mm, tzinfo=UTC) + F.ET_OFFSET
                for b in PULLS:
                    with tree():
                        snapshot(data, f"props-{kind}", due + datetime.timedelta(minutes=b), "us2")
                        for c in CHECKS:
                            if c < b:
                                continue
                            t = due + datetime.timedelta(minutes=c, seconds=30)
                            clock(t)
                            row = [r for r in F.survey(data, "picks", t)
                                   if r["mode"] == f"props-{kind}"]
                            if not row:
                                absent += 1
                                continue
                            judged += 1
                            if standdown(t, kind) == row[0]["stale"]:
                                split.append(f"{lg} {kind} due {due:%H:%MZ}: pull {b:+d} min, "
                                             f"asked {c:+d} min: contract owed={row[0]['stale']}")
    ck(judged > 400, "the sweep judged every league and kind", judged)
    eq(absent, 0, "...and the contract held the row every time")
    ck(not split, "🔴🔴 the stand-down stands down exactly when the contract says the pull is "
       "not owed: never refuses an owed pull, never buys a met deadline twice",
       f"{len(split)} disagreement(s): {split[:8]}")
    league("nfl")

    # ══════════════════════════════════════════════════════════════════
    section("4. 🔴 ONE LIST OF DEADLINES: THE CONTRACT'S ROW AND THE STAND-DOWN READ THE SAME ONE")
    # ══════════════════════════════════════════════════════════════════
    PT = getattr(F, "props_times", None)
    ck(callable(PT), "freshness.props_times exists")
    if callable(PT):
        with tree():
            t = at("2026-10-21T15:30:00Z")
            for lg, modes in (("mlb", ("props-pitcher", "props-batter")),
                              ("nfl", ("props-player",)), ("ncaaf", ("props-player",))):
                rows = {m: tm for m, _p, tm, _paid, _w in F.contract(C.LEAGUES[lg]["data"], "picks", t)}
                for m in modes:
                    ck(rows.get(m) is PT(lg), f"{lg} {m}: the contract row's deadlines are "
                       f"props_times('{lg}')", (rows.get(m), PT(lg)))

    # ══════════════════════════════════════════════════════════════════
    section("5. ✅ STILL TRUE: THE BACKUP COSTS NOTHING, KEYED ON THE STORAGE DIRECTORY")
    # ══════════════════════════════════════════════════════════════════
    with tree():
        data = league("nfl")
        snapshot(data, "props-player", at("2026-10-21T15:08:00Z"), "us,us2")
        ck(standdown(at("2026-10-21T15:23:00Z")),
           "✅ NFL: the 15:08Z primary landed, so the backup 15 minutes later stands down",
           shown(LOGS))
    with tree():
        data = league("mlb")
        snapshot(data, "props-pitcher", at("2026-10-21T11:04:00Z"), "us,us2")
        ck(standdown(at("2026-10-21T11:19:00Z"), "pitcher"),
           "✅ MLB: a cheap us2 backup stands down behind the full us,us2 primary", shown(LOGS))
        ck(not standdown(at("2026-10-21T11:19:00Z"), "batter"),
           "✅ ...and the batter kind reads only its own directory", shown(LOGS))
    league("nfl")
    note("💰 the spend: no pull is added. An owed pull the old 45-minute window refused was "
         "bought by the first pass after the 45 minutes anyway; a pull for a deadline already "
         "met is now refused (sections 1 and 3).")
finally:
    for d in TREES:
        shutil.rmtree(d, ignore_errors=True)
