#!/usr/bin/env python3
"""test_news_flags_fb.py — the news-flag reviewer flags, never picks, and
matches names on the EXACT full name — proven on the REAL stored strings.

# @vacuity a name matches as the whole full name, never as a substring
#   file: news_flags_fb.py
#   find:     return re.search(r"(?<![\w'])" + re.escape(clean(name)) + r"(?![\w])", clean(text)) is not None
#   with:     return clean(name) in clean(text)
#
# @vacuity a status word matches as a whole word ("unlimited" is not "limited")
#   file: news_flags_fb.py
#   find:         if re.search(r"(?<![\w])" + re.escape(w) + r"(?![\w])", low):
#   with:         if w in low:
#
# @vacuity an injury row attaches only when its team is in that player's game
#   file: news_flags_fb.py
#   find:                 if str(r.get("week")) != str(wk) or r.get("team") not in (home_c, away_c):
#   with:                 if str(r.get("week")) != str(wk):
#
# @vacuity a name two players share attaches only when the headline names the team
#   file: news_flags_fb.py
#   find:             if n_shared > 1 and not (names_in(s["home"], title) or names_in(s["away"], title)):
#   with:             if False:
#
# @vacuity no game row counts as 'did not play' only once the logs run past the game
#   file: news_flags_fb.py
#   find:             if not day or through < day:
#   with:             if not day:
#
# @vacuity first_seen is the FIRST time the reviewer saw the flag
#   file: news_flags_fb.py
#   find:             out.setdefault(f["key"], d.get("taken_at"))
#   with:             out[f["key"]] = d.get("taken_at")
"""
import datetime
import glob
import gzip
import json
import os
import shutil
import sys
import tempfile

from tcheck import ck, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import news_flags_fb as N  # noqa: E402

UTC = datetime.timezone.utc

section("1. EXACT FULL NAMES, WHOLE STATUS WORDS")
ck(N.names_in("Josh Allen", "Josh Allen ruled out") and N.names_in("Josh Allen", "Josh Allen's knee")
   and not N.names_in("Josh Allen", "Josh Allensworth limited") and not N.names_in("Josh Allen", "Bo Josh Allen2")
   and not N.names_in("Josh Allen", "josh allen ruled out"),
   "🔴🔴 the exact full name as a whole phrase, as written — never inside a longer name")
ck(N.names_in("Ja'Marr Chase", "Ja&#39;Marr Chase questionable") and N.names_in("Ja'Marr Chase", "Ja’Marr Chase out"),
   "   ✅ stored headlines' HTML entities and curly quotes are read as the plain characters")
ck(N.status_in("Tua Tagovailoa doubtful for Week 2") == "doubtful" and N.status_in("an unlimited role") is None
   and N.status_in("Deal ruled out") == "ruled out" and N.status_in("He is out") is None,
   "🔴 only Sam's status words, whole words ('unlimited' is not 'limited'; bare 'out' is not one)")

section("2. 🔴🔴 PROVEN ON THE REAL STORED STRINGS — boards and news, both leagues")
now = datetime.datetime(2026, 9, 25, tzinfo=UTC)
for lg, least in (("nfl", 100), ("ncaaf", 100)):
    names = set()
    for p in glob.glob(os.path.join(ROOT, "data", lg, "20*", "props-player", "*.json.gz")):
        try:
            d = json.load(gzip.open(p, "rt"))
        except (OSError, ValueError, EOFError):
            continue
        for ev in d.get("events") or []:
            for b in ev.get("bookmakers") or []:
                for m in b.get("markets") or []:
                    names.update(o["description"] for o in m.get("outcomes") or [] if o.get("description"))
    heads = [N.clean(h["title"]) for h in N.headlines(lg, now=now, days=40)]
    exact, refused_ok, cut, cuttable = 0, 0, 0, 0
    for n in names:
        for t in heads:
            if n not in t:
                continue
            if N.names_in(n, t):
                exact += 1
                if not n[-1].isalnum():
                    continue                   # "…Jr." cut to "…Jr" is still a whole phrase
                cuttable += 1
                short = n[:-1]                 # a real name cut short inside the SAME real headline
                if short in t and not N.names_in(short, t):
                    cut += 1
            else:
                refused_ok += 1
    ck(exact >= least and cuttable >= least and cut == cuttable,
       "🔴 %s: %d real board names x %d real headlines — %d exact full-name hits, and every one of "
       "those names cut short by a letter is REFUSED in the same headline (%d/%d) though a plain "
       "substring search would take it" % (lg, len(names), len(heads), exact, cut, cuttable),
       "⛔ a proof on no real hits proves nothing")

section("3. THE FLAGS: injury report + headlines, DESCRIPTIVE")
KICK = "2026-09-27T17:00:00Z"
players = [{"name": "Chris Olave", "game_id": "g1", "commence": KICK, "home": "New Orleans Saints", "away": "Baltimore Ravens"},
           {"name": "Josh Allen", "game_id": "g2", "commence": KICK, "home": "Buffalo Bills", "away": "Miami Dolphins"},
           {"name": "Brian Robinson Jr.", "game_id": "g3", "commence": KICK, "home": "Washington Commanders", "away": "Dallas Cowboys"}]
teams = [{"name": "Buffalo Bills", "game_id": "g2", "commence": KICK, "home": "Buffalo Bills", "away": "Miami Dolphins"}]
news = [{"title": "Chris Olave, Chase Young questionable to face Ravens", "link": "L1", "published": "2026-09-24T12:00:00Z"},
        {"title": "Josh Allen ruled out with ankle injury", "link": "L2"},
        {"title": "Bills: Josh Allen limited in practice", "link": "L3"},
        {"title": "Buffalo Bills place Josh Allen on reserve, receiver released", "link": "L4"}]
code = {"New Orleans Saints": "NO", "Baltimore Ravens": "BAL", "Buffalo Bills": "BUF", "Miami Dolphins": "MIA",
        "Washington Commanders": "WAS", "Dallas Cowboys": "DAL"}
inj = [{"full_name": "Chris Olave", "team": "NO", "week": 4, "report_status": "Questionable"},
       {"full_name": "Chris Olave", "team": "NO", "week": 3, "report_status": "Out"},
       {"full_name": "Brian Robinson", "team": "WAS", "week": 4, "report_status": "Out"},
       {"full_name": "Josh Allen", "team": "JAX", "week": 4, "report_status": "Out"},
       {"full_name": "Zed Bills", "team": "BUF", "week": 4, "report_status": "Doubtful"}]
import card_fb  # noqa: E402
fl, rep = N.flags("nfl", players, teams, news, inj, {card_fb.norm("Josh Allen"): 2}, {}, code.get, lambda c: 4)
by = {}
for f in fl:
    by.setdefault((f["kind"], f["subject"]), []).append((f["source"], f["status"]))
ck(("injury report", "QUESTIONABLE") in by[("player", "Chris Olave")]
   and ("injury report", "OUT") not in by[("player", "Chris Olave")]
   and ("headline", "questionable") in by[("player", "Chris Olave")],
   "🔴 this week's injury status and a headline naming him with a status word — last week's OUT is not this week's")
ck(("injury report", "OUT") in by.get(("player", "Brian Robinson Jr."), []),
   "   ✅ the card's own name folding bridges 'Brian Robinson' / 'Brian Robinson Jr.' — same team only")
ck(("injury report", "OUT") not in by.get(("player", "Josh Allen"), []),
   "🔴🔴 an injury row for a player of the same name on ANOTHER team (JAX) never attaches")
ck(by.get(("player", "Josh Allen")) == [("headline", "released")] and rep["ambiguous_skipped"] == 2,
   "🔴 a name two players share attaches only from a headline that also names his team, in full "
   "('Bills:' is not 'Buffalo Bills')",
   "got %r, skipped %s" % (by.get(("player", "Josh Allen")), rep["ambiguous_skipped"]))
ck(("injury report", "DOUBTFUL") in by[("team", "Buffalo Bills")]
   and ("headline", "released") in by[("team", "Buffalo Bills")],
   "   ✅ a Game Lines team is flagged from its injury report and from headlines naming it")
ck(all(f["basis"] == "DESCRIPTIVE" for f in fl) and not any(k in f for f in fl for k in ("rank", "price", "confidence")),
   "🔴 every flag is DESCRIPTIVE and carries nothing that could re-rank or re-price a row")
fl_c, _r = N.flags("ncaaf", players[:1], [], news, [], {}, {}, code.get, lambda c: None)
ck({f["source"] for f in fl_c} == {"headline"},
   "🔴 college: headlines only — there is no injury report to read")

section("4. FROZEN, FIRST SEEN, GRADED ONCE")
root = tempfile.mkdtemp(prefix="nf-")
try:
    lat = os.path.join(root, "data", "ncaaf", "latest")
    os.makedirs(lat)
    os.makedirs(os.path.join(root, "picks"))
    json.dump({"items": [{"title": "Sam Leavitt questionable for Ole Miss game", "link": "LL"},
                         {"title": "Tre Harris ruled out vs. LSU", "link": "LT"}]},
              open(os.path.join(lat, "news.json"), "w"))
    with gzip.open(os.path.join(lat, "props.json.gz"), "wt") as fh:
        json.dump({"games": [{"id": "c1", "commence": KICK, "home": "LSU Tigers", "away": "Ole Miss Rebels",
                              "props": [{"player": "Sam Leavitt"}, {"player": "Tre Harris"}]}]}, fh)
    logs = {2026: {"p1": {"name": "Sam Leavitt", "g": [{"d": "2026-09-20"}]},
                   "p2": {"name": "Tre Harris", "g": [{"d": "2026-09-20"}]}}}
    t0 = datetime.datetime(2026, 9, 26, 15, 0, tzinfo=UTC)
    d1 = N.build("ncaaf", root=root, now=t0, log=lambda m: None, logs=logs)
    # a new headline changes the flag set, so a SECOND copy is frozen holding both old flags again
    _n = json.load(open(os.path.join(lat, "news.json")))
    _n["items"].append({"title": "Tre Harris suspended for first half", "link": "LS"})
    json.dump(_n, open(os.path.join(lat, "news.json"), "w"))
    d2 = N.build("ncaaf", root=root, now=t0 + datetime.timedelta(hours=20), log=lambda m: None, logs=logs)
    _fs = {f["link"]: f["first_seen"] for f in d2["flags"]}
    ck(len(d1["flags"]) == 2 and len(glob.glob(os.path.join(root, "data", "ncaaf", "*", "news-flags", "*.json.gz"))) == 2
       and _fs["LL"] == _fs["LT"] == "2026-09-26T15:00:00Z" and _fs["LS"] == "2026-09-27T11:00:00Z",
       "🔴 every flag is frozen with its time, and first_seen stays the FIRST time it was seen",
       "got %r" % _fs)
    ck(d1["college_note"] and "headlines only" in d1["college_note"], "   ✅ the college file says it is headlines only")
    d3 = N.build("ncaaf", root=root, now=t0 + datetime.timedelta(days=2), log=lambda m: None, logs=logs)
    ck(d3["record"]["absence"]["graded"] == 0,
       "🔴 no game row yet, but the logs have not reached the game: left PENDING, not 'did not play'")
    logs[2026]["p1"]["g"].append({"d": "2026-09-27"})
    d4 = N.build("ncaaf", root=root, now=t0 + datetime.timedelta(days=3), log=lambda m: None, logs=logs)
    ck(d4["record"]["absence"] == dict(d4["record"]["absence"], graded=2, did_not_play=2, right_pct=100.0)
       and d4["record"]["caution"]["played"] == 1,
       "🔴 graded once the logs pass the game: 'ruled out' and he sat = right; 'questionable' shown as played",
       "got %r" % d4["record"])
    ck({f["link"]: f["first_seen"] for f in d4["flags"]}.get("LL") == "2026-09-26T15:00:00Z",
       "🔴 ...and still the first sighting once a LATER frozen copy also holds that flag")
    ck(N.due("ncaaf", root, now=t0 + datetime.timedelta(days=3, minutes=1)) is False,
       "   ✅ once a day: a file built after today's deadline is not rebuilt")
finally:
    shutil.rmtree(root, ignore_errors=True)

_nfl = open(os.path.join(ROOT, "nfl.py"), encoding="utf-8").read()
_col = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
_news = _col[_col.index('elif mode == "news":'):_col.index('elif mode == "nfl-teams":')]
ck('"injury_report": inj_rows,' in _nfl and "_nf.due(LEAGUE)" in _news and "_nf.build(LEAGUE)" in _news,
   "🔴 the injury rows signal 7 downloads are stored, and the reviewer rides the existing news run")
