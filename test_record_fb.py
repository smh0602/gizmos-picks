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
import glob
import gzip
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta
from tcheck import ck, note   # the shared gate — see tcheck.py

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
ck("it writes both the totals and the per-row detail",
   bool(R.get("overall")) and bool(D.get("days")))
ck("the record is labelled DESCRIPTIVE and RECORD, never MODEL",
   R["kind"] == "DESCRIPTIVE" and R["basis"] == "RECORD"
   and "MODEL" not in json.dumps(R["calibration"]).upper(),
   "ledger rule 55 — football has no model to calibrate")
ck("the calibration column is headed `stated`, not `predicted`",
   all("stated" in c for c in R["calibration"]) if R["calibration"] else True,
   "a record is not a forecast")

# ⛔ THE POINTER FILE MUST NOT BE GRADED TWICE.
have = sorted(os.path.basename(f) for f in glob.glob(f"{ROOT}/picks/fb-ncaaf-*.json"))
ck("`-latest.json` exists and is NOT counted as its own card",
   "fb-ncaaf-latest.json" in have
   and R["cards_seen"] == len([h for h in have if not h.endswith("-latest.json")]),
   "%d cards seen, %d dated files on disk"
   % (R["cards_seen"], len([h for h in have if not h.endswith("-latest.json")])))

# ───────────────────────────────────────────────────────────────
print("\n═══ 3. THE CONTROL — EVERY GRADED ROW RE-DERIVED BY HAND ═══")
# ⛔ Deliberately NOT through card_fb.MARKETS or record_fb. If the reader
#    is wrong, both the grader and a test that reuses it are wrong together.


def hand_norm(n):
    n = unicodedata.normalize("NFKD", str(n or ""))
    n = "".join(c for c in n if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", n.lower())


HAND = {
    "player_pass_yds":      lambda g: (g.get("pass_yds") or 0),
    "player_pass_tds":      lambda g: (g.get("pass_td") or 0),
    "player_rush_yds":      lambda g: (g.get("rush_yds") or 0),
    "player_reception_yds": lambda g: (g.get("rec_yds") or 0),
    "player_receptions":    lambda g: (g.get("rec") or 0),
    "player_anytime_td":    lambda g: (g.get("rec_td") or 0) + (g.get("rush_td") or 0),
}

agree = dis = 0
mismatch = []
for date, rows in D["days"].items():
    season = int(date[:4])
    P = load(f"{ROOT}/data/ncaaf/latest/players-{season}.json.gz")["players"]
    byname = {}
    for pl in P.values():
        byname.setdefault(hand_norm(pl.get("name")), []).append(pl)
    for r in rows:
        if r["won"] is None:
            continue
        cands = byname.get(hand_norm(r["player"]), [])
        if len(cands) != 1:
            mismatch.append((r["player"], "name not unique by hand"))
            dis += 1
            continue
        t = datetime.strptime(r["commence"][:10], "%Y-%m-%d")
        hits = [g for g in cands[0]["g"]
                if abs((datetime.strptime(g["d"], "%Y-%m-%d") - t).days) <= 1]
        if len(hits) != 1:
            mismatch.append((r["player"], "%d games in the window" % len(hits)))
            dis += 1
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

ck("every graded row re-derives identically by hand",
   dis == 0 and agree > 0, "%d agree, %d disagree" % (agree, dis))
for m in mismatch[:6]:
    note("🔴 " + str(m))

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
ck("the calibration buckets hold every graded row that has a confidence",
   sum(c["n"] for c in R["calibration"])
   == len([r for r in graded if r.get("confidence") is not None]))

# 🔴 THE HONEST LIMIT MUST BE ON THE FILE, NOT ONLY IN A DOCSTRING.
ck("the file states which way the unsettled rows bias the number",
   "read HIGH" in R["over_bias_note"] or "VOID" in R["over_bias_note"],
   "an exclusion with a direction has to say the direction")
ck("and it says how many rows it could not settle",
   str(R["unresolved"]) in R["coverage_note"])
ck("the sample's concentration is published",
   R["distinct_players"] <= R["overall"]["n"] and R["distinct_players"] > 0,
   "%d graded rows from %d players across %d games"
   % (R["overall"]["n"], R["distinct_players"], R["distinct_games"]))

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
ck("the grading deadline falls AFTER the log rebuild that feeds it",
   min(d[0] for d in grade_due if d[2] == trend_due[0][2]) > trend_due[0][0]
   if any(d[2] == trend_due[0][2] for d in grade_due) else True,
   "logs rebuild %s, grading due %s" % (trend_due, grade_due))

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
ck("the page prints the builder's own coverage sentence, not its own",
   "R.coverage_note" in h and "R.over_bias_note" in h)
ck("the page prints the concentration warning", "distinct_players" in h)
ck("an em-dash is still used for 'nothing graded'",
   "nothing graded yet" in h,
   "'nothing graded' and 'graded 0%' are different facts")

# ───────────────────────────────────────────────────────────────
# 🔴 THE FAILURE GATE IS THE LAST THING IN THIS FILE. Rule 97.
