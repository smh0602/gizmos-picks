#!/usr/bin/env python3
r"""test_year_turn.py — the site keeps working through the turn of the year and the MLB winter.

`[2026-10-27]` A sweep of every year-pinned season (R6) found what breaks between now and
the 2027 MLB opener, every one on a planted tree here, nothing read from production:
- 🔴 the football Track Record read a card's player log by its CALENDAR year, so every card
  dated January or February (NFL weeks 17-18, the playoffs, the bowls) asked for a 2027 log,
  was skipped, and never reached the Track Record; the unpublished shadow record lost the
  same days for good (§2). Nothing would have said so: the ungraded-card alarm was MLB only
  (§3);
- 🔴 the news flags found an NFL game's week in the kickoff's calendar-year schedule, so
  from 12-29 (week 17's Thursday game is 01:15Z on 01-01) to the Super Bowl no injury flag
  was written (32 of 2026's 272 games); and a Monday-night game read as the NEXT week (16
  games, 7 of them played by 10-27) (§4);
- 🔴 the MLB pitcher and hitter pulls asked statsapi for `now().year`: from 2027-01-01
  10:04Z an empty 2027 pool, our own RuntimeError, every MLB run red until a 2027 arm had
  20 IP (about mid-April) (§5);
- 🔴 a spring-training day owed an MLB card: from about 2027-02-19 every MLB pass red and
  the watchdog BROKEN for five weeks (§6);
- the MLB game model read only `data/2026-*` odds (no run line on any 2027 card), and built
  each team's usual nine from spring-training lineups (§7).
⚠️ ROOT CAUSE: every one was written inside one season, where the calendar year and the
season agree and the spring had already passed.

⛔ THE CLASS, NOT THE LINES (§1): every year a module takes from a date is named here per
function WITH ITS REASON, so a new one is a decision written down. What §1 reads: a `[:4]`
slice under int(), of str(), or in a %-format, a `+` or an f-string; a `.year` outside a
datetime/date constructor; a `strftime("%Y")`. ⚠️ What it does not read: a slice handed
straight to a call or a variable (syntax cannot tell it from a truncation), `split("-")[0]`,
and a LITERAL year (`data/2026-*`, `players-2026`, `(2025, 2026)`): those are guarded per
instance (§7's glob). The Python only; the page's season list is the August 2027 follow-up.
⚠️ A mutation of THIS file cannot be declared here (its `find` would occur twice), so §1's
scan branches were each proved red by hand `[review, 2026-10-27]`.

# @vacuity a January football card is graded from the season before
#   file: record_fb.py
#   find: season = fb_why.season_of(date)
#   with: season = int(str(date)[:4])
#
# @vacuity a January shadow day asks for the season before
#   file: shadow_fb.py
#   find: season = fb_why.season_of(day)
#   with: season = int(day[:4])
#
# @vacuity a new calendar-year season is found by the scan
#   file: fb_props_model.py
#   find: x = H.features(pid, fb_why.season_of(c), mk, ctx)
#   with: x = H.features(pid, int(c[:4]) - (1 if int(c[5:7]) < 3 else 0), mk, ctx)
#
# @vacuity the football leagues are asked the ungraded-card question
#   file: watchdog.py
#   find: _fb_ungraded(rep, lg, datetime.date.fromisoformat(_et_today(now)))
#   with: pass
#
# @vacuity a football day that settled nothing is not graded
#   file: watchdog.py
#   find: d and ((d.get("n") or 0) > 0 or (d.get("voids") or 0) > 0
#   with: d and (True
#
# @vacuity a football card whose rows can never settle is not an alarm
#   file: watchdog.py
#   find: or not d.get("pending", d.get("carded", 1)))):
#   with: )):
#
# @vacuity the grader says which rows still wait for the log
#   file: record_fb.py
#   find: "pending": sum(1 for r in rows if r["state"] == "not in the log yet"),
#   with: "pending": 0,
#
# @vacuity a January game's week is read from its season's schedule
#   file: fb_why.py
#   find: "schedule-%s.json.gz" % season_of(when)
#   with: "schedule-%s.json.gz" % str(when)[:4]
#
# @vacuity a Monday-night game is matched within a day of its UTC kickoff
#   file: fb_why.py
#   find: abs((gd - d).days) <= 1):
#   with: abs((gd - d).days) <= 0):
#
# @vacuity the news flags ask for THIS game's week
#   file: news_flags_fb.py
#   find: week_of = ((lambda r: fb_why.game_week(
#   with: week_of = ((lambda r: None and fb_why.game_week(
#
# @vacuity the MLB pulls take their season from the stored finals
#   file: collect.py
#   find: return yr, (yr - 1 if age <= NEW_SEASON_GRACE_D else None)
#   with: return now().year, None
#
# @vacuity the season before is pulled only inside the grace
#   file: collect.py
#   find: (yr - 1 if age <= NEW_SEASON_GRACE_D else None)
#   with: (yr - 1)
#
# @vacuity an empty or broken answer from a new season still raises (a row must carry the bar's field)
#   file: collect.py
#   find: (sp.get("stat") or {}).get(field) is not None for sp in got[0])
#   with: True for sp in [0])
#
# @vacuity a new season's pool with a domain violation still raises
#   file: collect.py
#   find: clean = not (len(got) > 2 and got[2]) and any(
#   with: clean = any(
#
# @vacuity a season never steps backwards once its file is stored
#   file: collect.py
#   find: and not (stored is not None and stored >= yr)):
#   with: ):
#
# @vacuity a scores store that stopped adding finals cannot hold the pulls on last season
#   file: collect.py
#   find: if before is None and yr < cal:
#   with: if False:
#
# @vacuity the pitcher pull reads the season rule
#   file: collect.py
#   find: season_pool("pitchers", _pitcher_pool, f"{PITCHER_MIN_IP} IP", "inningsPitched")
#   with: (now().year,) + _pitcher_pool(now().year)
#
# @vacuity the hitter pull reads the season rule
#   file: collect.py
#   find: season_pool("hitters", _hitter_pool, f"{HITTER_MIN_PA} PA", "plateAppearances")
#   with: (now().year,) + _hitter_pool(now().year)
#
# @vacuity a spring-training game owes no card
#   file: freshness.py
#   find: carded = lambda g: not (isinstance(g.get("gameType"), str) and g["gameType"] in skip)
#   with: carded = lambda g: True
#
# @vacuity a game type nobody has seen still owes a card (an exclusion list, never an allow-list)
#   file: freshness.py
#   find: carded = lambda g: not (isinstance(g.get("gameType"), str) and g["gameType"] in skip)
#   with: carded = lambda g: g.get("gameType") in ("R", "F", "D", "L", "W")
#
# @vacuity the codes that owe no card are read from mlb_game_model
#   file: freshness.py
#   find: vals = frozenset(_literal("mlb_game_model.py", name)) or None
#   with: vals = None
#
# @vacuity spring training is one of the codes that owe no card
#   file: mlb_game_model.py
#   find: NOT_CARDED = {"S", "E", "A", "I"}
#   with: NOT_CARDED = {"E", "A", "I"}
#
# @vacuity every year's odds pulls are read
#   file: mlb_game_model.py
#   find: "data", "[0-9][0-9][0-9][0-9]-*", "gamelines"
#   with: "data", "2026-*", "gamelines"
#
# @vacuity a spring-training lineup is not a team's usual nine
#   file: mlb_game_model.py
#   find: if len(lu) == 9 and team in played:
#   with: if len(lu) == 9:
"""
import ast
import contextlib
import datetime
import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
from tcheck import ck, eq, note, section  # noqa: E402

UTC = datetime.timezone.utc
TREES = []


def tree():
    t = tempfile.mkdtemp(prefix="yearturn-")
    TREES.append(t)
    return t


def put(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if path.endswith(".gz"):
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(doc, fh)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)


def Z(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)


try:
    # ═══ §1 every year taken from a date is a decision ═══════════════════════════
    section("§1 every year a module takes from a date is named, with its reason")
    MLB_YEAR = "an MLB season is the calendar year of its games (it plays inside one)"
    ALLOWED = {
        ("collect.py", "mlb_seasons"): (1, MLB_YEAR + ": the year of a stored final"),
        ("collect.py", "mlb_pull_season"): (1, "the calendar only when no stored final can be "
                                               "read, which raises in winter: the loud side"),
        ("collect.py", "season_pool"): (1, "the calendar's season is ASKED of statsapi only while "
                                           "the store's newest is older: an answer over the bar "
                                           "means the store is behind (never the calendar alone)"),
        ("collect.py", "collect_scores"): (2, "the store's fetch window opens 1 March of this "
                                              "year (no MLB game in January or February), and "
                                              "its unread `season` label"),
        ("collect.py", "collect_lineups"): (2, "the same window and label as collect_scores"),
        ("fb_why.py", "season_of"): (2, "THE rule: the season a football date belongs to "
                                        "(January and February are the season before)"),
        ("freshness.py", "current_football_season"): (2, "the season in progress NOW (1 August), "
                                                         "pinned to collect.yml's CUR"),
        ("freshness.py", "_us_eastern_offset"): (1, "the US daylight-time rule is a function of "
                                                    "the year, not of a season"),
        ("signal9.py", "week_of"): (1, "fb_signal9's pre-registered scoring reads it as it "
                                       "scored (a change is Sam's); the news flags do not"),
    }

    def year_uses(path):
        """[(function, line, what)] for every year taken from a date in a module's code:
        a [:4] or [0:4] slice under int(), of str(...), or in a %-format, a `+` or an
        f-string; a `.year` that is not the first argument of a datetime/date(x.year,
        x.month, ...) constructor; and a strftime("%Y"). Comments and strings are not
        code, so the parse skips them."""
        tr = ast.parse(open(path, encoding="utf-8").read())
        parent = {c: n for n in ast.walk(tr) for c in ast.iter_child_nodes(n)}

        def where(n):
            while n in parent:
                n = parent[n]
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    return n.name
            return "<module>"

        def four(s):
            return (isinstance(s, ast.Slice) and s.step is None and isinstance(s.upper, ast.Constant)
                    and s.upper.value == 4
                    and (s.lower is None or (isinstance(s.lower, ast.Constant) and s.lower.value == 0)))
        out = []
        for n in ast.walk(tr):
            p = parent.get(n)
            if isinstance(n, ast.Subscript) and four(n.slice):
                if ((isinstance(p, ast.Call) and getattr(p.func, "id", None) == "int" and n in p.args)
                        or (isinstance(n.value, ast.Call) and getattr(n.value.func, "id", None) == "str")
                        or (isinstance(p, ast.BinOp) and isinstance(p.op, (ast.Mod, ast.Add)))
                        or isinstance(p, ast.FormattedValue)):
                    out.append((where(n), n.lineno, "a year sliced off a date"))
            elif isinstance(n, ast.Attribute) and n.attr == "year":
                if not (isinstance(p, ast.Call) and len(p.args) > 1 and p.args[0] is n
                        and ast.unparse(p.func) in ("datetime", "date", "datetime.datetime", "datetime.date")
                        and isinstance(p.args[1], ast.Attribute) and p.args[1].attr == "month"):
                    out.append((where(n), n.lineno, ".year"))
            elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "strftime"
                  and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == "%Y"):
                out.append((where(n), n.lineno, 'strftime("%Y")'))
        return out

    found = {}
    for name in sorted(os.listdir(ROOT)):
        if name.endswith(".py") and not name.startswith("test_"):
            for fn, line, what in year_uses(os.path.join(ROOT, name)):
                found.setdefault((name, fn), []).append("%d %s" % (line, what))
    for key, hits in sorted(found.items()):
        want, why = ALLOWED.get(key, (0, None))
        ck(len(hits) == want, "%s %s(): %d year(s) taken from a date, %d named here"
           % (key[0], key[1], len(hits), want),
           ("why: " + why) if why and len(hits) == want else
           "%s. A football season comes from fb_why.season_of (a date) or "
           "freshness.current_football_season (now), an MLB one from the stored finals "
           "(collect.mlb_pull_season); or name it in ALLOWED with its reason" % ", ".join(hits)
           if len(hits) > want else "fewer than named: update ALLOWED so it stays the truth")
    for key in sorted(set(ALLOWED) - set(found)):
        ck(False, "%s %s() is named in ALLOWED and takes no year" % key, "remove it from ALLOWED")
    _probe = tree()
    with open(os.path.join(_probe, "probe.py"), "w", encoding="utf-8") as fh:
        fh.write("import datetime\n# int(x[:4]) in a comment is not code\n"
                 "def f(d):\n    return int(d[:4]), datetime.date(d.year, d.month, 1), str(d)[:4], 'x'[:4]\n"
                 "def h(d, g):\n    return (d.strftime('%Y'), 'p-%s' % d[:4], f'x{d[:4]}', 'x' + d[:4],\n"
                 "            g(d.year, d.month))\n")
    eq(sorted(w for _f, _l, w in year_uses(os.path.join(_probe, "probe.py"))),
       sorted(["a year sliced off a date"] * 5 + ['strftime("%Y")', ".year"]),
       "the scan sees int(d[:4]), str(d)[:4], a %-format, an f-string and a `+` of d[:4], "
       "strftime('%Y') and a .year handed to any call but a date constructor; it skips a comment, "
       "a datetime.date(d.year, d.month) and a plain slice")

    # ═══ §2 a January football card is graded from the season before ═════════════
    section("§2 the football Track Record grades January from the season before")
    import fb_why  # noqa: E402
    eq([fb_why.season_of(d) for d in ("2026-12-31", "2027-01-03", "2027-02-14", "2027-03-01", "2027-09-09")],
       [2026, 2026, 2026, 2027, 2027], "the one rule: January and February are the season before")
    T = tree()
    LAT = os.path.join(T, "data", "nfl", "latest")
    DAYS = ("2026-12-27", "2027-01-03", "2027-01-10")

    def gm(d, yds):
        return {"d": d, "week": 1, "rec": 5, "rec_yds": yds, "car": 0, "rush_yds": 0, "rec_td": 0,
                "rush_td": 0, "pass_yds": 0, "pass_td": 0, "att": 0, "snaps": 50, "snap_pct": 0.8,
                "team": "KC"}
    put(os.path.join(LAT, "players-2026.json.gz"), {"season": 2026, "players": {
        "p1": {"name": "Rec Alpha", "pos": "WR", "g": [gm(d, 60) for d in DAYS]}}})
    # the NEXT season's log exists too (August on): a January card must still read 2026's
    put(os.path.join(LAT, "players-2027.json.gz"), {"season": 2027, "players": {
        "q1": {"name": "Rec Alpha", "pos": "WR", "g": [gm("2027-09-12", 10)]}}})
    for d in DAYS:
        put(os.path.join(T, "picks", "fb-nfl-%s.json" % d), {"date": d, "league": "nfl", "picks": [
            {"player": "Rec Alpha", "market": "player_reception_yds", "side": "over", "line": 40.5,
             "price": -110, "book": "fanduel", "confidence": 60, "confidence_basis": "RECORD",
             "raw": "6 of 10", "commence": d + "T18:00:00Z", "game": "DEN @ KC"}]})
    p = subprocess.run([sys.executable, os.path.join(ROOT, "record_fb.py")], cwd=T,
                       env=dict(os.environ, LEAGUE="nfl", FB_RECORD_FROM="2026-09-01"),
                       capture_output=True, text=True, timeout=300)
    ck(p.returncode == 0, "record_fb.py ran on the planted tree", (p.stderr or p.stdout)[-400:])
    R = json.load(open(os.path.join(LAT, "record.json"), encoding="utf-8")) if p.returncode == 0 else {}
    eq([(d.get("date"), d.get("n"), d.get("w")) for d in R.get("by_day") or []],
       [(d, 1, 1) for d in DAYS],
       "🔴 the 12-27, 01-03 and 01-10 cards are each graded from players-2026 (a 60-yard game, over 40.5)")

    import watchdog as W  # noqa: E402

    def watch(root, now, lg="nfl"):
        old = W.ROOT
        try:
            W.ROOT = root
            rep = W.Report()
            W.check_record_ungraded(rep, now)
            return [i for i in rep.items if i["key"] == "record:%s:ungraded" % lg]
        finally:
            W.ROOT = old

    ck(not watch(T, Z("2027-01-20T15:00Z")), "   ...and the watchdog is quiet about that record on 01-20")

    import record_fb  # noqa: E402
    import shadow_fb as S  # noqa: E402
    _asked, _saved = [], (S.wagers, record_fb.load_log)
    try:
        S.wagers = lambda *a, **k: [{"player": "Rec Alpha", "market": "player_reception_yds",
                                     "side": "over", "line": 40.5, "commence": "2027-01-03T18:00:00Z"}]
        record_fb.load_log = lambda season: _asked.append(season) or ({}, {})
        _rows, _why = S.grade_day("2027-01-03")
    finally:
        S.wagers, record_fb.load_log = _saved
    eq((_asked, _why), ([2026], "no 2026 player log stored yet"),
       "🔴 the shadow record asks for the 2026 log for 2027-01-03 (it lost those days for good)")

    # ═══ §3 a football card missing from the record is BROKEN, like MLB's ════════
    section("§3 a football card older than 3 days and ungraded turns the watchdog red")

    def fb_tree(lg, cards, by_day, record_from="2026-09-07", skipped=()):
        t = tree()
        for name, doc in cards:
            put(os.path.join(t, "picks", name), doc)
        put(os.path.join(t, "data", lg, "latest", "record.json"),
            {"record_from": record_from, "by_day": by_day,
             "skipped": [{"date": a, "why": b} for a, b in skipped]})
        return t

    ROW = [{"player": "Rec Alpha", "market": "player_receptions", "side": "over", "line": 3.5}]
    jan = ("fb-nfl-2027-01-03.json", {"date": "2027-01-03", "league": "nfl", "liked": ROW})
    NOW = Z("2027-01-07T15:00Z")
    f = watch(fb_tree("nfl", [jan], [], skipped=[("2027-01-03", "no 2027 player log stored yet")]), NOW)
    ck(bool(f) and f[0]["severity"] == "BROKEN" and "2027-01-03" in f[0]["why"]
       and "no 2027 player log" in f[0]["why"] and f[0]["repair"] == "card-fb",
       "🔴 a 4-day-old NFL card missing from record.json is BROKEN, names the day and why, and "
       "names football's grader `card-fb` (`record` does nothing under nfl)",
       f and (f[0]["why"], f[0]["repair"]))
    f = watch(fb_tree("nfl", [jan], [{"date": "2027-01-03", "n": 0, "voids": 0, "carded": 1,
                                      "pending": 1}]), NOW)
    ck(bool(f) and "nothing on it settled" in f[0]["why"],
       "🔴 ...and so is one in by_day that settled nothing while a row waits for the log",
       f and f[0]["why"])
    f = watch(fb_tree("nfl", [jan], [{"date": "2027-01-03", "n": 0, "voids": 0, "carded": 1}]), NOW)
    ck(bool(f), "⛔ ...and one from a record written before `pending` existed (fails closed)",
       f and f[0]["why"])
    for what, cards, by_day, now, rf in (
            ("graded", [jan], [{"date": "2027-01-03", "n": 1, "voids": 0}], NOW, "2026-09-07"),
            ("all void", [jan], [{"date": "2027-01-03", "n": 0, "voids": 1}], NOW, "2026-09-07"),
            ("whose rows can never settle", [jan],
             [{"date": "2027-01-03", "n": 0, "voids": 0, "carded": 1, "pending": 0}], NOW, "2026-09-07"),
            ("exactly 3 days old", [jan], [], Z("2027-01-06T15:00Z"), "2026-09-07"),
            ("with an empty liked list", [(jan[0], dict(jan[1], liked=[], picks=ROW))], [], NOW, "2026-09-07"),
            ("dated before record_from", [jan], [], NOW, "2027-02-01"),
            ("another league's", [(jan[0], dict(jan[1], league="ncaaf"))], [], NOW, "2026-09-07")):
        ck(not watch(fb_tree("nfl", cards, by_day, rf), now), "✅ a card %s is silent" % what)
    _c = ("fb-ncaaf-2027-01-01.json", {"date": "2027-01-01", "league": "ncaaf", "picks": ROW})
    f = watch(fb_tree("ncaaf", [_c], []), NOW, "ncaaf")
    ck(bool(f) and "1 ncaaf card" in f[0]["what"], "🔴 college is asked the same question",
       f and f[0]["what"])
    ck(W.check_record_ungraded in W.CHECKS, "the check is in the watchdog's run list")
    # `[review, 2026-10-27]` DRIVEN THROUGH THE REAL GRADER: a one-game card (a Thursday
    #    night) whose player is in the log but not that week (an NFL inactive) is graded as
    #    it will stay, and must never be an alarm; a card past the log's coverage still is.
    PT = tree()
    put(os.path.join(PT, "data", "nfl", "latest", "players-2026.json.gz"), {"season": 2026, "players": {
        "p1": {"name": "Rec Beta", "pos": "WR", "g": [gm("2026-10-25", 60), gm("2026-11-15", 60)]}}})
    for d, kick in (("2026-11-05", "2026-11-06T01:15:00Z"), ("2026-11-20", "2026-11-21T01:15:00Z")):
        put(os.path.join(PT, "picks", "fb-nfl-%s.json" % d), {"date": d, "league": "nfl", "liked": [
            {"player": "Rec Beta", "market": "player_reception_yds", "side": "over", "line": 40.5,
             "price": -110, "book": "fanduel", "confidence": 60, "confidence_basis": "RECORD",
             "raw": "6 of 10", "commence": kick, "game": "DEN @ KC"}]})
    p = subprocess.run([sys.executable, os.path.join(ROOT, "record_fb.py")], cwd=PT,
                       env=dict(os.environ, LEAGUE="nfl", FB_RECORD_FROM="2026-09-01"),
                       capture_output=True, text=True, timeout=300)
    _pd = {d.get("date"): d for d in (json.load(open(os.path.join(PT, "data", "nfl", "latest", "record.json"),
                                                    encoding="utf-8")).get("by_day") or [])} \
        if p.returncode == 0 else {}
    eq([(d, (_pd.get(d) or {}).get("n"), (_pd.get(d) or {}).get("pending")) for d in ("2026-11-05", "2026-11-20")],
       [("2026-11-05", 0, 0), ("2026-11-20", 0, 1)],
       "record_fb: the 11-05 card's row is 'not in the log for that week' (pending 0), the 11-20 "
       "card's is past the log's coverage (pending 1)")
    ck(not [x for x in watch(PT, Z("2026-11-10T15:00Z")) + watch(PT, Z("2027-02-01T15:00Z"))
            if "2026-11-05" in x["why"]],
       "🔴 a one-game card whose rows can never settle is silent at 5 days and at 88 (it was BROKEN "
       "forever, and its repair could not change it)")
    f = watch(PT, Z("2026-11-25T15:00Z"))
    ck(bool(f) and "2026-11-20" in f[0]["why"] and "2026-11-05" not in f[0]["why"],
       "🔴 ...while a card whose row still waits for the log is BROKEN after 3 days", f and f[0]["why"])

    # ═══ §4 an NFL game's week is THIS game's own row ════════════════════════════
    section("§4 the news flags read THIS game's week, January and Monday night included")
    NT = tree()
    NL = os.path.join(NT, "data", "nfl", "latest")
    put(os.path.join(NL, "schedule-2026.json.gz"), {"season": 2026, "games": [
        {"week": 7, "home": "PHI", "away": "DAL", "start": "2026-10-26T20:15"},
        {"week": 8, "home": "PHI", "away": "NYG", "start": "2026-11-01T13:00"},
        {"week": 17, "home": "CIN", "away": "BAL", "start": "2026-12-31T20:15"},
        {"week": 17, "home": "KC", "away": "DEN", "start": "2027-01-03T13:00"},
        {"week": 18, "home": "BUF", "away": "NYJ", "start": "2027-01-10T13:00"}]})
    eq([fb_why.game_week(NL, h, a, c) for h, a, c in (
        ("PHI", "DAL", "2026-10-27T00:15:00Z"), ("CIN", "BAL", "2027-01-01T01:15:00Z"),
        ("KC", "DEN", "2027-01-03T18:00:00Z"), ("BUF", "NYJ", "2027-01-10T18:00:00Z"),
        ("PHI", "NYG", "2026-12-27T18:00:00Z"))],
       [7, 17, 17, 18, None],
       "🔴 Monday night is week 7 (not 8); the 12-31 game (01:15Z on 01-01) and 01-03 are week 17, "
       "01-10 is 18; a game the schedule does not hold has no week")
    import news_flags_fb as N  # noqa: E402
    put(os.path.join(NL, "props.json.gz"), {"games": [
        {"id": "n1", "commence": "2027-01-01T01:15:00Z", "home": "Cincinnati Bengals",
         "away": "Baltimore Ravens", "props": [{"player": "Joe Burrow"}]},
        {"id": "n2", "commence": "2026-10-27T00:15:00Z", "home": "Philadelphia Eagles",
         "away": "Dallas Cowboys", "props": [{"player": "Dak Prescott"}]}]})
    put(os.path.join(NL, "players-2026.json.gz"), {"season": 2026, "players": {}, "injury_report": [
        {"week": 17, "team": "CIN", "full_name": "Joe Burrow", "report_status": "Out"},
        {"week": 7, "team": "DAL", "full_name": "Dak Prescott", "report_status": "Doubtful"}]})
    os.makedirs(os.path.join(NT, "picks"), exist_ok=True)
    _logs = {2026: {"a": {"name": "Joe Burrow", "g": []}, "b": {"name": "Dak Prescott", "g": []}}}
    _d = N.build("nfl", root=NT, now=Z("2026-12-29T15:05Z"), log=lambda m: None, logs=_logs)
    eq(sorted((x["subject"], x["status"]) for x in _d["flags"] if x["source"] == "injury report"),
       [("Dak Prescott", "DOUBTFUL"), ("Joe Burrow", "OUT")],
       "🔴 the real build flags the week-17 Thursday game and the week-7 Monday-night game")

    # ═══ §5 the MLB pulls take their season from the stored finals ═══════════════
    section("§5 the MLB pitcher and hitter pulls never ask for a season not yet played")
    import collect as C  # noqa: E402

    def fake(pools):
        """statsapi, by season: pools[season] = [(id, outs or PA)]. Records every pool asked."""
        asked = []

        def get(url, timeout=30):
            s = int(url.split("season=")[1][:4]) if "season=" in url else None
            hit = "group=hitting" in url
            if "stats?stats=season" in url:
                asked.append(s)
                rows = pools.get(s, [])
                # n: outs or PA; a str is the raw inningsPitched; None leaves the field out
                if hit:
                    sp = [{"player": {"id": i, "fullName": "Bat %d" % i}, "team": {"name": "T"},
                           "stat": {} if n is None else {"plateAppearances": n}} for i, n in rows]
                else:
                    sp = [{"player": {"id": i, "fullName": "Arm %d" % i}, "team": {"name": "T"},
                           "stat": dict({} if n is None else {
                               "inningsPitched": n if isinstance(n, str) else "%d.%d" % (n // 3, n % 3)},
                               gamesStarted=3, era="3.00", whip="1.1", wins=1, losses=1)}
                          for i, n in rows]
                return {"stats": [{"splits": sp}]}, {}
            if "/people?personIds=" in url:
                return {"people": []}, {}
            row = ({"atBats": 4, "plateAppearances": 4, "hits": 1, "homeRuns": 0, "rbi": 0,
                    "totalBases": 1, "runs": 0, "baseOnBalls": 0, "strikeOuts": 1} if hit else
                   {"gamesStarted": 1, "inningsPitched": "6.0", "strikeOuts": 5, "earnedRuns": 2,
                    "hits": 5, "baseOnBalls": 1, "numberOfPitches": 90, "battersFaced": 24})
            return {"stats": [{"splits": [{"date": "%d-05-01" % s, "isHome": True,
                                           "opponent": {"name": "O"}, "stat": row}]}]}, {}
        return get, asked

    FINALS_2026 = {"2026-03-25": [{"gamePk": 1, "gameType": "R"}], "2026-10-31": [{"gamePk": 2, "gameType": "W"}]}

    def pull(kind, at, days, pools, scores_text=None, stored=None):
        """-> (seasons asked, the file's season, raised?, output). The collector on a planted
        latest/, its clock at `at`, statsapi faked; `stored` plants the kind's file of that season."""
        lat = os.path.join(tree(), "latest")
        os.makedirs(lat)
        if stored is not None:
            put(os.path.join(lat, "%s.json.gz" % kind), {"season": stored})
        if scores_text is not None:
            with open(os.path.join(lat, "scores.json.gz"), "w") as fh:
                fh.write(scores_text)
        elif days is not None:
            put(os.path.join(lat, "scores.json.gz"), {"schema": 2, "days": days})
        get, asked = fake(pools)
        saved = (C.get, C.LATEST, C.now)
        buf, err = io.StringIO(), None
        try:
            C.get, C.LATEST, C.now = get, lat, (lambda: at)
            with contextlib.redirect_stdout(buf):
                (C.collect_pitchers if kind == "pitchers" else C.collect_hitters)()
        except Exception as e:
            err = "%s: %s" % (type(e).__name__, e)
        finally:
            C.get, C.LATEST, C.now = saved
        f = os.path.join(lat, "%s.json.gz" % kind)
        season = json.load(gzip.open(f, "rt")).get("season") if os.path.exists(f) else None
        return asked, season, err, buf.getvalue()

    OK_P = {2026: [(1, 300)], 2027: [(9, 300)]}          # one arm over 20 IP each season
    THIN_P = {2026: [(1, 300)], 2027: [(9, 30)]}         # 2027's arms all under 20 IP
    WINTER_P = {2026: [(1, 300)]}                        # statsapi has no 2027 game yet
    a, s, e, o = pull("pitchers", Z("2027-01-01T10:10Z"), FINALS_2026, WINTER_P)
    eq((a[:2], s, e, "::warning::" in o), ([2027, 2026], 2026, None, False),
       "🔴 on 2027-01-01 the pitcher pull asks statsapi whether 2027 is under way (empty: no), "
       "then pulls 2026, the season played")
    spring = dict(FINALS_2026, **{"2027-03-02": [{"gamePk": 3, "gameType": "S"}]})
    a, s, e, _o = pull("pitchers", Z("2027-03-10T10:10Z"), spring, WINTER_P)
    eq((a[-1], s), (2026, 2026), "   ...spring training is not the season: still 2026 on 03-10")
    opener = dict(spring, **{"2027-03-26": [{"gamePk": 4, "gameType": "R"}]})
    a, s, e, o = pull("pitchers", Z("2027-04-01T10:10Z"), opener, THIN_P)
    ck(a[:1] == [2027] and s == 2026 and e is None and "::warning::pitchers: the 2027 season" in o,
       "🔴 six days after the opener, no 2027 arm at 20 IP: it SAYS so and pulls 2026",
       "asked %s, wrote %s, %s" % (a, s, e))
    a, s, e, _o = pull("pitchers", Z("2027-04-10T10:10Z"), opener, OK_P)
    eq((a[0], s, e), (2027, 2027, None), "   ...and once a 2027 arm has 20 IP, the pull is 2027's")
    a, s, e, _o = pull("pitchers", Z("2027-05-15T10:10Z"), opener, THIN_P)
    ck(e and "pitcher pool came back empty" in e and s is None,
       "🔴 50 days into the season with nobody at 20 IP is a failure, never an excuse", e)
    a, s, e, _o = pull("pitchers", Z("2027-05-10T10:10Z"), opener, THIN_P)
    eq((s, e), (2026, None), "   ...while day 45 is still inside the grace (an overseas opener runs a week early)")
    a, s, e, _o = pull("pitchers", Z("2027-04-01T10:10Z"), opener, {2026: [(1, 300)]})
    ck(e and "pitcher pool came back empty" in e and a == [2027],
       "🔴 a new season whose pool answers NOTHING raises: that is the endpoint, not the calendar",
       "asked %s, %s" % (a, e))
    a, s, e, _o = pull("pitchers", Z("2027-01-01T10:10Z"), None, OK_P, scores_text="not a gzip")
    ck(a[:1] == [2027], "⛔ a store that cannot be read falls back to the calendar (fails closed)", a)
    # `[review, 2026-10-27]` inside the grace, only a young season falls back:
    a, s, e, _o = pull("pitchers", Z("2027-04-25T10:10Z"), opener, THIN_P, stored=2027)
    ck(e and "pitcher pool came back empty" in e and s == 2027,
       "🔴 a season never steps backwards: with 2027's file stored, a pool gone thin raises and "
       "keeps the 2027 file", "wrote %s, %s" % (s, e))
    a, s, e, _o = pull("pitchers", Z("2027-04-01T10:10Z"), opener, {2026: [(1, 300)], 2027: [(9, "10.5")]})
    ck(e and "pitcher pool came back empty" in e and s is None,
       "🔴 a 2027 pool with an innings value outside thirds (fabricated data) raises, never falls back",
       "wrote %s, %s" % (s, e))
    a, s, e, _o = pull("pitchers", Z("2027-04-01T10:10Z"), opener, {2026: [(1, 300)], 2027: [(9, None)]})
    ck(e and "pitcher pool came back empty" in e and s is None,
       "🔴 ...and so does one whose rows carry no inningsPitched (a broken answer, not a young season)",
       "wrote %s, %s" % (s, e))
    a, s, e, o = pull("pitchers", Z("2027-06-01T10:10Z"), FINALS_2026, OK_P)
    ck(a[:1] == [2027] and 2026 not in a and s == 2027 and e is None
       and "::warning::pitchers: scores.json.gz holds no 2027 final" in o,
       "🔴 a scores store that stopped adding finals cannot keep June on 2026: statsapi has a 2027 "
       "arm over 20 IP, so 2027 is pulled and the store is named behind", "asked %s, wrote %s, %s" % (a, s, e))
    a, s, e, o = pull("pitchers", Z("2027-06-01T10:10Z"), FINALS_2026, WINTER_P)
    eq((s, e, "::warning::" in o), (2026, None, False),
       "   ...while a season with no game yet (a lockout) keeps the store's season, no red run")
    a, s, e, _o = pull("hitters", Z("2027-01-01T10:10Z"), FINALS_2026, {2026: [(5, 500)], 2027: []})
    eq((a[-1], s, e), (2026, 2026, None), "🔴 the hitter pull asks for 2026 on 2027-01-01")
    a, s, e, _o = pull("hitters", Z("2027-04-01T10:10Z"), opener, {2026: [(5, 500)], 2027: [(6, None)]})
    ck(e and "hitter pool came back empty" in e,
       "🔴 a 2027 hitter pool whose rows carry no plateAppearances raises", e)
    a, s, e, _o = pull("hitters", Z("2027-04-25T10:10Z"), opener, {2026: [(5, 500)], 2027: [(6, 20)]},
                       stored=2027)
    ck(e and "hitter pool came back empty" in e and s == 2027,
       "🔴 ...and with 2027's hitter file stored, a pool gone thin raises and keeps it", "wrote %s, %s" % (s, e))
    a, s, e, o = pull("hitters", Z("2027-04-01T10:10Z"), opener, {2026: [(5, 500)], 2027: [(6, 20)]})
    ck(s == 2026 and e is None and "::warning::hitters" in o,
       "🔴 ...and pulls 2026, saying so, while no 2027 bat has 80 PA", "wrote %s, %s" % (s, e))
    a, s, e, _o = pull("hitters", Z("2027-05-15T10:10Z"), opener, {2026: [(5, 500)], 2027: [(6, 20)]})
    ck(e and "hitter pool came back empty" in e, "   ...and raises once the grace is spent", e)

    # ═══ §6 every game owes an MLB card except the codes that owe none ═══════════
    section("§6 a spring-training or All-Star day owes no MLB card; any other game does")
    import freshness as F  # noqa: E402
    import mlb_game_model as G  # noqa: E402

    def day_of(games, total=None):
        t = tree()
        put(os.path.join(t, "2027-02-20", "schedule", "1404.json.gz"),
            {"pulled_at": "2027-02-20T14:04:00Z", "date": "2027-02-20", "schedule": {
                "totalGames": len(games) if total is None else total,
                "dates": [{"games": [dict(g, gamePk=i + 1) for i, g in enumerate(games)]}]}})
        return F.no_games_day("2027-02-20", data=t)
    eq((F._mlb_not_carded(), F._mlb_game_types()),
       (frozenset(G.NOT_CARDED) or None, frozenset(G.GAME_TYPES) or None),
       "the sets are mlb_game_model's own")
    ck(G.NOT_CARDED and G.GAME_TYPES and not (G.NOT_CARDED & G.GAME_TYPES),
       "   ...and no code both owes a card and owes none")
    _lit = F._literal
    try:
        F._literal = lambda m, n: {"X"} if (m, n) == ("mlb_game_model.py", "NOT_CARDED") else _lit(m, n)
        F._MLB_SETS.clear()
        eq(F._mlb_not_carded(), frozenset({"X"}), "   ...read from that file, never a copy")
    finally:
        F._literal = _lit
        F._MLB_SETS.clear()
    eq([day_of([{"gameType": "S"}] * 15), day_of([{"gameType": "E"}, {"gameType": "S"}]),
        day_of([{"gameType": "A"}]), day_of([{"gameType": "I"}])], [True, True, True, True],
       "🔴 a spring day, an exhibition day, an All-Star day and an intrasquad day owe nothing")
    eq([day_of([{"gameType": c}]) for c in "RFDLW"], [False] * 5,
       "⛔ a regular-season, wild-card, division, league-championship and World Series day each owe a card")
    eq([day_of([{"gameType": "S"}, {"gameType": "R"}]), day_of([{}]), day_of([{"gameType": "RS"}] * 15),
        day_of([{"gameType": ""}]), day_of([{"gameType": 7}])],
       [False] * 5, "🔴 ...and so do a day with one regular-season game, a game with no gameType, a code "
                    "nobody has seen, an empty code and a non-text one (an allow-list read them as "
                    "no games and silenced the card, results, relay and watchdog)")
    _t = F._mlb_not_carded
    try:
        F._mlb_not_carded = lambda: None
        ck(day_of([{"gameType": "S"}] * 2) is False, "⛔ when the list cannot be read, every game counts")
    finally:
        F._mlb_not_carded = _t

    # ═══ §7 the MLB game model: every year's odds, the season's own lineups ═══════
    section("§7 the MLB game model reads 2027's odds and no spring lineup")
    GT = tree()
    put(os.path.join(GT, "data", "2027-03-26", "gamelines", "1300.json.gz"), {
        "pulled_at": "2027-03-26T13:00:00Z", "games": [{
            "commence": "2027-03-26T23:05:00Z", "away": "Away Club", "home": "Home Club", "books": {
                "fanduel": {"h2h": {"Home Club": -150, "Away Club": 130},
                            "spreads": {"Home Club": {"pt": -1.5, "px": 120},
                                        "Away Club": {"pt": 1.5, "px": -140}}}}}]})
    _b = G.books(GT).get(("2027-03-26", "Away Club", "Home Club")) or {}
    ck(_b.get("rl_home_pt") == -1.5 and _b.get("win_home"),
       "🔴 a 2027 odds pull is read: the opener has a moneyline and a run line", _b)
    _nine = [str(i) for i in range(9)]
    _I = {"scores": {"2027-03-20": [
              {"gamePk": 1, "gameType": "S", "home": "Spring Home", "away": "Spring Away",
               "home_r": 3, "away_r": 2, "venue_id": 1},
              {"gamePk": 2, "gameType": "R", "home": "Real Home", "away": "Real Away",
               "home_r": 4, "away_r": 1, "venue_id": 2}]},
          "starts": {}, "hits": {},
          "lineups": {"2027-03-20": {"Spring Home": _nine, "Real Home": _nine}}}
    _st = G.State()
    G.advance(_st, _I, "2027-03-20")
    eq(sorted(k for k, v in _st.lineups.items() if v), ["Real Home"],
       "🔴 only the regular-season game's lineup joins a team's usual nine")
finally:
    for t in TREES:
        shutil.rmtree(t, ignore_errors=True)
