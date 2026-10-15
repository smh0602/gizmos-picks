#!/usr/bin/env python3
"""test_fb_new_data.py — NEW FOOTBALL DATA, STORED ONLY. `[Sam, 2026-10-14]`

NWS kickoff forecasts (fb_weather.py), CFBD venues / advanced stats / Elo / CFBD
weather (cfb.py), NFL injuries and starting QBs (nfl.py), and the freshness rows
behind them. Planted trees, a pinned clock, fake sources. ⛔ Reads no live data,
makes no network call, writes nothing under data/.

# @vacuity 🔴 a forecast pulled at or after kickoff never replaces "last"
#   file: fb_weather.py
#   find:     if new["pulled_at"] >= _iso(kick):
#   with:     if False:
#
# @vacuity 🔴 "first" is never overwritten
#   file: fb_weather.py
#   find:     entry.setdefault("first", new)
#   with:     entry["first"] = new
#
# @vacuity 🔴 a dome or closed roof makes no call
#   file: fb_weather.py
#   find:             if f.get("roof") in INDOOR_ROOFS:
#   with:             if False:
#
# @vacuity 🔴 a failed NWS call does not stop the run
#   file: fb_weather.py
#   find:                 e["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:160])
#   with:                 raise
#
# @vacuity 🔴 college forecasts are FBS vs FBS only
#   file: fb_weather.py
#   find:         if lg == "ncaaf" and not (g.get("home_class") == "fbs" and g.get("away_class") == "fbs"):
#   with:         if False:
#
# @vacuity 🔴 nflverse's Eastern wall time is read as daylight time in October
#   file: fb_weather.py
#   find:     return -4 if mar.replace(hour=2) <= naive < nov.replace(hour=2) else -5
#   with:     return -5
#
# @vacuity 🔴 a refused CFBD call fetches nothing (venues)
#   file: cfb.py
#   find:     if not _priced(1, "venues %d" % season, log):
#   with:     if False:
#
# @vacuity 🔴 a refused CFBD call fetches nothing (advanced stats, season to date)
#   file: cfb.py
#   find:         if not _priced(len(weeks), "advanced stats %d to date" % season, log):
#   with:         if False:
#
# @vacuity 🔴 a refused CFBD call fetches nothing (advanced stats, newest week)
#   file: cfb.py
#   find:         if not _priced(1, "advanced stats %d week %d" % (season, wk[1]), log):
#   with:         if False:
#
# @vacuity 🔴 a missing current-season file is pulled whole, once
#   file: cfb.py
#   find:             weeks = ["regular"] + (["postseason"] if wk[0] == "postseason" else [])
#   with:             weeks = ["regular", "postseason"]
#
# @vacuity 🔴 after that only the newest played week is pulled
#   file: cfb.py
#   find:     if not old:
#   with:     if not old or current:
#
# @vacuity 🔴 the current season's advanced stats are asked once a UTC day
#   file: cfb.py
#   find:         if (old.get("built_at") or "")[:10] == _stamp(now)[:10]:
#   with:         if False:
#
# @vacuity 🔴 CFBD weather only when /info says the tier has it
#   file: cfb.py
#   find:                  "patron_level": level, "weather_available": bool(level and level >= 1)}
#   with:                  "patron_level": level, "weather_available": True}
#
# @vacuity 🔴 the college schedule keeps CFBD's pregame Elo
#   file: cfb.py
#   find:             "home_elo": g.get("homePregameElo"), "away_elo": g.get("awayPregameElo"),
#   with:             "home_elo": None, "away_elo": None,
#
# @vacuity 🔴 the starting QB is the most pass attempts
#   file: nfl.py
#   find:             if att > 0 and key[0] and key[1] and (key not in best or att > best[key]["att"]):
#   with:             if att > 0 and key[0] and key[1] and (key not in best or att < best[key]["att"]):
#
# @vacuity 🔴 a season of injuries that fails never stops the others
#   file: nfl.py
#   find:             out[season] = "failed: %s: %s" % (type(e).__name__, str(e)[:200])
#   with:             raise
#
# @vacuity 🔴 a stale stored-only file is never a red run
#   file: freshness.py
#   find:         if stored_only(r):
#   with:         if False:
#
# @vacuity 🔴 a stale stored-only file never plans a run
#   file: freshness.py
#   find:     need = {r["mode"] for r in rows if r["stale"] and not stored_only(r)
#   with:     need = {r["mode"] for r in rows if r["stale"]
#
# @vacuity 🔴 every new file has a freshness row
#   file: freshness.py
#   find:     _store = [(f"weather-{season}", T["possession"])]
#   with:     _store = []
#
# @vacuity 🔴 the CFBD budget counts the daily advanced-stats call
#   file: cfbd_budget.py
#   find:     adv = 1 if "def fetch_adv(" in src else 0
#   with:     adv = 0
"""
import datetime
import gzip
import json
import os
import shutil
import sys
import tempfile
import urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import cfb  # noqa: E402
import cfbd_budget  # noqa: E402
import fb_weather as FW  # noqa: E402
import freshness as F  # noqa: E402
import nfl  # noqa: E402
from tcheck import ck, eq, section  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 10, 14, 12, 0, tzinfo=UTC)          # ⛔ the pinned clock
TREES = []


def tree():
    t = tempfile.mkdtemp(prefix="fbdata-")
    TREES.append(t)
    return t.replace("\\", "/")


def put(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with (gzip.open(path, "wt", encoding="utf-8") if path.endswith(".gz") else open(path, "w")) as fh:
        json.dump(doc, fh)


def jz(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def period(start, hours=1, wind="8 mph", gust=None, pop=20, temp=55):
    a = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
    return {"startTime": a.isoformat(), "endTime": (a + datetime.timedelta(hours=hours)).isoformat(),
            "windSpeed": wind, "windGust": gust, "probabilityOfPrecipitation": {"value": pop},
            "temperature": temp, "temperatureUnit": "F"}


try:
    # ══════════════════════════════════════════════════════════════════
    section("1. 🔴 NWS: \"first\" STAYS, \"last\" ONLY BEFORE KICKOFF")
    # ══════════════════════════════════════════════════════════════════
    kick = datetime.datetime(2026, 10, 18, 17, 0, tzinfo=UTC)
    e = {}
    FW.merge(e, {"pulled_at": "2026-10-14T07:14:00Z", "wind": 9}, kick)
    FW.merge(e, {"pulled_at": "2026-10-17T07:14:00Z", "wind": 14}, kick)
    eq((e["first"]["wind"], e["last"]["wind"]), (9, 14),
       "🔴 the first forecast stays \"first\"; a later one before kickoff becomes \"last\"")
    FW.merge(e, {"pulled_at": "2026-10-18T17:00:00Z", "wind": 30}, kick)
    FW.merge(e, {"pulled_at": "2026-10-18T19:00:00Z", "wind": 31}, kick)
    eq((e["first"]["wind"], e["last"]["wind"]), (9, 14),
       "🔴 a forecast pulled at or after kickoff never replaces \"last\"")
    eq(FW.kickoff_utc("2026-10-18T13:00"), datetime.datetime(2026, 10, 18, 17, 0, tzinfo=UTC),
       "🔴 nflverse's unzoned 1:00pm ET in October is 17:00Z (daylight time)")
    eq(FW.kickoff_utc("2026-11-08T13:00"), datetime.datetime(2026, 11, 8, 18, 0, tzinfo=UTC),
       "   ...and 18:00Z after the first Sunday of November")
    eq((FW._mph("5 to 12 mph"), FW._mph({"value": 32.2, "unitCode": "wmoUnit:km_h-1"}), FW._mph(None)),
       (12.0, 20.0, None), "   wind text and km/h objects read as mph")

    # ══════════════════════════════════════════════════════════════════
    section("2. 🔴 A DAILY PASS: INDOOR NO CALL, ABROAD SKIPPED, A FAILURE GOES ON")
    # ══════════════════════════════════════════════════════════════════
    T = tree()
    base = T + "/data/nfl/latest"
    games = [
        {"id": "g_dome", "start": "2026-10-18T13:00", "home": "DET", "away": "GB",
         "venue": "Ford Field", "roof": "dome"},
        {"id": "g_open", "start": "2026-10-18T13:00", "home": "BUF", "away": "MIA",
         "venue": "Highmark Stadium", "roof": "outdoors"},
        {"id": "g_bad", "start": "2026-10-18T16:25", "home": "SEA", "away": "LV",
         "venue": "Lumen Field", "roof": "outdoors"},
        {"id": "g_lon", "start": "2026-10-18T09:30", "home": "JAX", "away": "NE",
         "venue": "Wembley Stadium", "roof": "outdoors"},
        {"id": "g_far", "start": "2026-10-25T13:00", "home": "CHI", "away": "NYG",
         "venue": "Soldier Field", "roof": "outdoors"},
        {"id": "g_late", "start": "2026-10-18T20:20", "home": "PHI", "away": "DAL",
         "venue": "Lincoln Financial Field", "roof": "outdoors"}]
    put(base + "/schedule-2026.json.gz", {"season": 2026, "games": games})
    calls = []

    def fake_get(url):
        calls.append(url)
        if "/points/" in url:
            if url.endswith("47.5952,-122.3316"):
                raise urllib.error.HTTPError(url, 503, "down", {}, None)
            return {"properties": {"forecastHourly": "https://nws.test/fc/" + url.split("/")[-1]}}
        return {"properties": {"periods": [period("2026-10-18T17:00:00Z", wind="12 mph", gust="25 mph"),
                                           period("2026-10-19T00:00:00Z", temp=48)]}}

    doc = FW.run("nfl", root=T, now=NOW, get=fake_get, sleep=lambda s: None, log=lambda m: None, season=2026)
    G = (doc or {}).get("games") or {}
    ck(doc is not None and os.path.exists(base + "/weather-2026.json.gz"),
       "🔴 the pass wrote its file even though one NWS call failed")
    eq((G.get("g_dome") or {}).get("indoor"), True, "🔴 a dome is stored as indoor ...")
    ck(not any("42.34" in u for u in calls), "   ...with no call for it", calls)
    ck("skipped" in (G.get("g_lon") or {}) and not any("51." in u for u in calls),
       "🔴 a venue outside the US (not in the stadium table) is skipped, says so, and is never asked",
       G.get("g_lon"))
    eq(((G.get("g_open") or {}).get("first") or {}).get("wind"), 12.0,
       "🔴 an outdoor US game gets its kickoff hour: wind 12 ...")
    eq({k: G["g_open"]["first"][k] for k in ("gust", "precip_pct", "temp", "forecast_for", "pulled_at")},
       {"gust": 25.0, "precip_pct": 20, "temp": 55, "forecast_for": "2026-10-18T17:00:00Z",
        "pulled_at": "2026-10-14T12:00:00Z"}, "   ...gust, precipitation chance and temperature (F)")
    ck("error" in (G.get("g_bad") or {}) and ((G.get("g_late") or {}).get("first") or {}).get("temp") == 48,
       "🔴 a failed NWS call is written on its game and the games after it are still asked",
       (G.get("g_bad"), G.get("g_late")))
    ck("g_far" not in G, "   a game more than 7 days out is not asked yet")
    eq(sum(1 for u in calls if "/points/" in u), 3, "   one /points call per outdoor US venue (cached)")
    again = FW.run("nfl", root=T, now=NOW + datetime.timedelta(days=1), get=fake_get, sleep=lambda s: None,
                   log=lambda m: None, season=2026)
    eq(sum(1 for u in calls if "/points/" in u), 4,
       "   ...and the next day re-asks only the venue whose /points call failed")
    eq(again["games"]["g_open"]["first"]["pulled_at"], "2026-10-14T12:00:00Z",
       "   ...and the second day's forecast leaves \"first\" alone")

    C = tree()
    cbase = C + "/data/ncaaf/latest"
    put(cbase + "/schedule-2026.json.gz", {"season": 2026, "games": [
        {"id": 1, "start": "2026-10-17T19:30:00.000Z", "home": "Iowa", "away": "Ohio State",
         "venue": "Kinnick Stadium", "home_class": "fbs", "away_class": "fbs"},
        {"id": 2, "start": "2026-10-17T19:30:00.000Z", "home": "Montana", "away": "Idaho",
         "venue": "Washington-Grizzly Stadium", "home_class": "fcs", "away_class": "fcs"},
        {"id": 3, "start": "2026-10-17T16:00:00.000Z", "home": "Syracuse", "away": "Pitt",
         "venue": "JMA Wireless Dome", "home_class": "fbs", "away_class": "fbs"}]})
    ven = {"Kinnick Stadium": {"lat": 41.6586, "lon": -91.5511, "dome": False, "country": "US"},
           "Washington-Grizzly Stadium": {"lat": 46.86, "lon": -113.98, "dome": False, "country": "US"},
           "JMA Wireless Dome": {"lat": 43.036, "lon": -76.136, "dome": True, "country": "US"}}
    ccalls = []
    cdoc = FW.run("ncaaf", root=C, now=NOW, get=lambda u: (ccalls.append(u), fake_get(u))[1],
                  sleep=lambda s: None, log=lambda m: None, season=2026, venues=ven)
    eq(sorted((cdoc or {}).get("games") or {}), ["1", "3"],
       "🔴 college: FBS vs FBS only (Montana-Idaho is not asked)")
    ck(cdoc["games"]["3"].get("indoor") and not any("43.036" in u for u in ccalls),
       "   ...and a CFBD dome is indoor, with no call")

    # ══════════════════════════════════════════════════════════════════
    section("3. 🔴 CFBD: PRICED FIRST, A REFUSAL FETCHES NOTHING")
    # ══════════════════════════════════════════════════════════════════
    D = tree()
    out = D + "/data/ncaaf/latest"
    put(out + "/schedule-2026.json.gz", {"season": 2026, "games": [
        {"id": 7, "week": 6, "season_type": "regular", "start": "2026-10-10T19:00:00.000Z", "final": True,
         "home": "Iowa", "away": "Ohio State", "home_elo": 1600, "away_elo": 1800},
        {"id": 8, "week": 7, "season_type": "regular", "start": "2026-10-17T19:00:00.000Z", "final": False}]})
    put(out + "/schedule-2025.json.gz", {"season": 2025, "games": [{"id": 5, "home": "A", "away": "B"}]})
    _old = (cfb.OUT, cfb._counted_get, cbase_pre := cfbd_budget.preflight, cfb.get)
    asked = []
    cfb.OUT = out
    cfb._counted_get = lambda path, params: (asked.append((path, dict(params))), FAKE.get(path, []))[1]
    FAKE = {}
    allow = {"v": False}
    cfbd_budget.preflight = lambda calls, purpose, latest, root=None: {
        "allowed": allow["v"], "why": "planted", "purpose": purpose, "calls": calls}
    quiet = lambda m: None  # noqa: E731
    outcomes = [cfb.fetch_venues(2026, quiet, NOW), cfb.fetch_adv(2026, True, quiet, NOW),
                cfb.fetch_adv(2025, False, quiet, NOW), cfb.backfill_elo(2025, quiet),
                cfb.fetch_cfbd_weather([2025, 2026], quiet, NOW)]
    eq(outcomes, ["refused"] * 5, "🔴 every new CFBD pull is priced, and each refusal says so")
    ck(not asked and not any(os.path.exists(out + "/" + f) for f in
                             ("venues-2026.json.gz", "adv-2026.json.gz", "adv-2025.json.gz",
                              "cfbd-weather-probe.json")),
       "🔴 ...and a refused call fetches nothing and writes nothing", asked)
    allow["v"] = True
    FAKE.update({"/venues": [{"name": "Kinnick Stadium", "id": 1, "latitude": 41.66, "longitude": -91.55,
                              "dome": False, "countryCode": "US"}],
                 "/stats/game/advanced": [{"gameId": 7, "week": 6, "team": "Iowa", "opponent": "Ohio State",
                                           "offense": {"plays": 61, "successRate": 0.41, "explosiveness": 1.2,
                                                       "ppa": 0.18, "rushingPlays": {"ppa": 0.1}},
                                           "defense": {"plays": 70, "success_rate": 0.45,
                                                       "explosiveness": 1.3, "ppa": 0.22}}],
                 "/info": {"patronLevel": 0}})
    cfb.fetch_venues(2026, quiet, NOW)
    eq(jz(out + "/venues-2026.json.gz")["venues"]["Kinnick Stadium"]["lat"], 41.66,
       "   allowed: /venues stored with coordinates (one call)")
    del asked[:]
    cfb.fetch_adv(2026, True, quiet, NOW)
    A = jz(out + "/adv-2026.json.gz")
    # `[2026-10-14]` ~~the newest week only~~: that never held weeks 1 to 7 of 2026.
    eq((asked, A["games"]["7"]["Iowa"]["offense"], A["games"]["7"]["Iowa"]["defense"]["successRate"]),
       ([("/stats/game/advanced", {"year": "2026", "excludeGarbageTime": "true", "seasonType": "regular"})],
        {"plays": 61, "successRate": 0.41, "explosiveness": 1.2, "ppa": 0.18}, 0.45),
       "🔴 advanced stats, current season's file missing: exactly ONE whole-season pull (no week; no "
       "postseason before it starts), garbage time excluded, the four named fields per side")
    eq(cfb.fetch_adv(2026, True, quiet, NOW + datetime.timedelta(hours=3)), "already refreshed today",
       "🔴 ...asked once a UTC day")
    eq(len(asked), 1, "   ...so the second pass made no call")
    del asked[:]
    cfb.fetch_adv(2026, True, quiet, NOW + datetime.timedelta(days=1))
    eq(asked, [("/stats/game/advanced", {"year": "2026", "excludeGarbageTime": "true", "seasonType": "regular",
                                         "week": "6"})],
       "🔴 the next day's run pulls only the newest played week")
    del asked[:]
    allow["v"] = False
    eq((cfb.fetch_adv(2026, True, quiet, NOW + datetime.timedelta(days=2)), asked), ("refused", []),
       "🔴 ...and a refused newest-week pull fetches nothing")
    allow["v"] = True
    w = cfb.fetch_cfbd_weather([2025, 2026], quiet, NOW)
    ck(w.startswith("skipped") and [p for p, _ in asked] == ["/info"]
       and "patronLevel 0" in cfb.NOTES.get("cfbd weather", ""),
       "🔴 CFBD weather: /info says tier 0, so /games/weather is never asked and the quota record says why", w)
    eq(cfb.fetch_cfbd_weather([2025, 2026], quiet, NOW + datetime.timedelta(days=1))[:7], "skipped",
       "   ...and the tier is not asked again within the week")
    eq(len(asked), 1, "   (still one /info call)")
    os.remove(out + "/cfbd-weather-probe.json")
    FAKE.update({"/info": {"patronLevel": 1},
                 "/games/weather": [{"id": 7, "temperature": 51.0, "windSpeed": 9.0}]})
    cfb.fetch_cfbd_weather([2025, 2026], quiet, NOW)
    eq(jz(out + "/cfbd-weather-2026.json.gz")["games"]["7"]["windSpeed"], 9.0,
       "   tier 1: /games/weather is stored per game")

    cfb.get = lambda path, params, timeout=90, tries=4: [
        {"id": 9, "week": 1, "startDate": "2026-08-29T19:00:00.000Z", "homeTeam": "Iowa", "awayTeam": "UNI",
         "homePregameElo": 1612, "awayPregameElo": 1301, "homeClassification": "fbs",
         "awayClassification": "fcs", "completed": True, "homePoints": 34, "awayPoints": 7}
    ] if params.get("seasonType") == "regular" else []
    sched, _rep = cfb.build_schedule(2026, quiet)
    eq([(g["home_elo"], g["away_elo"]) for g in sched["games"]], [(1612, 1301)],
       "🔴 the college schedule keeps CFBD's PREGAME Elo from the same /games call")
    del asked[:]
    eq(cfb.backfill_elo(2025, quiet)[:7], "written", "   ...and 2025 is re-pulled once, priced")
    eq(cfb.backfill_elo(2025, quiet), "already stored", "   ...and never again")
    cfb.OUT, cfb._counted_get, cfbd_budget.preflight, cfb.get = _old

    # ══════════════════════════════════════════════════════════════════
    section("4. 🔴 NFL INJURIES AND THE STARTING QB")
    # ══════════════════════════════════════════════════════════════════
    INJ = [{"gsis_id": "p1", "full_name": "A One", "position": "WR", "team": "SEA", "week": "6",
            "report_status": "Out", "practice_status": "Did Not Participate In Practice",
            "date_modified": "2026-10-10T20:01:00Z"},
           {"gsis_id": "p2", "full_name": "B Two", "position": "T", "team": "SEA", "week": 6,
            "report_status": "", "practice_status": "Limited Participation in Practice",
            "date_modified": "2026-10-11T18:30:00Z"}]
    PL = {"players": {"q1": {"name": "Sam Starter", "g": [{"team": "SEA", "week": 6, "att": 34, "game_id": "x"}]},
                      "q2": {"name": "Ben Backup", "g": [{"team": "SEA", "week": 6, "att": 3, "game_id": "x"}]},
                      "w1": {"name": "No Throws", "g": [{"team": "SEA", "week": 6, "att": 0}]}}}
    I = nfl.injuries_doc(2026, INJ, PL, "2026-10-14T12:00:00Z")
    wk = I["teams"]["SEA"]["6"]
    eq(([p["position"] for p in wk["players"]], wk["players"][0]["practice_status"], wk["starting_qb"]["name"],
        I["nflverse_updated"], I["kind"]),
       (["WR", "T"], "Did Not Participate In Practice", "Sam Starter", "2026-10-11T18:30:00Z", "DESCRIPTIVE"),
       "🔴 per team per week: each listed player's position, report and practice status; the starting QB "
       "is the most pass attempts; the file says when nflverse last updated it")
    N = tree() + "/data/nfl/latest"
    put(N + "/players-2026.json.gz", PL)

    def rows_of(season):
        if season == 2025:
            raise RuntimeError("asset not published")
        return INJ
    res = nfl.store_injuries(N, [2025, 2026], log=lambda m: None, now=NOW, fetch_rows=rows_of)
    ck(res[2025].startswith("failed") and res[2026].startswith("written")
       and os.path.exists(N + "/injuries-2026.json.gz") and not os.path.exists(N + "/injuries-2025.json.gz"),
       "🔴 a season that fails is named and the other season is still written", res)

    # ══════════════════════════════════════════════════════════════════
    section("5. 🔴 FRESHNESS: A ROW EACH, A WARNING WHEN STALE, NEVER A RUN OR A RED")
    # ══════════════════════════════════════════════════════════════════
    want = {"nfl": {"weather-2026", "injuries-2025", "injuries-2026"},
            "ncaaf": {"weather-2026", "adv-2025", "adv-2026", "venues-2026"}}
    for lg, writer in (("nfl", "nfl-logs"), ("ncaaf", "cfb-probe")):
        P = tree()
        rows = F.contract(P + "/data/" + lg, P + "/picks", NOW)
        got = {r[1][1].split("/")[-1][:-8]: r[0] for r in rows
               if F.STORED_ONLY.search(r[1][1]) and "/history/" not in r[1][1]}   # T70's are test_fb_history's
        eq(got, {k: writer for k in want[lg]},
           "🔴 %s: every new file has a row, written by the league's daily %s run" % (lg, writer))
    put(P + "/data/ncaaf/latest/cfbd-weather-2026.json.gz", {"games": {}})
    ck(any("cfbd-weather-2026" in r[1][1] for r in F.contract(P + "/data/ncaaf", P + "/picks", NOW)),
       "   ...and CFBD weather gets its row once its file exists (only when the tier has it)")
    fake = [{"mode": "cfb-probe", "path": "x/data/ncaaf/latest/adv-2026.json.gz", "stale": True,
             "missing": True, "paid": False, "age_min": None},
            {"mode": "cfb-probe", "path": "x/data/ncaaf/latest/allowed-by-position-2026.json.gz",
             "stale": True, "missing": True, "paid": False, "age_min": None}]
    hard, soft = F.classify(fake, P + "/data/ncaaf", refused=False, block={"state": None})
    eq(([r["path"][-16:] for r in hard], [r["path"][-16:] for r in soft]),
       (["ition-2026.json.gz"[-16:]], ["adv-2026.json.gz"]),
       "🔴 a stale stored-only file is a warning (soft); the same writer's real artifact stays hard")
    _sv, _sm = F.survey, F.slate_moves
    try:
        F.survey = lambda data="data", picks="picks", now=None: [fake[0]]
        F.slate_moves = lambda data, picks, now: set()
        eq(F.plan(P + "/data/ncaaf", P + "/picks", NOW)[0], [],
           "🔴 ...and it never plans a run (no cfb-probe rebuild, 13+ CFBD calls, for a file nothing reads)")
        F.survey = lambda data="data", picks="picks", now=None: fake
        eq(F.plan(P + "/data/ncaaf", P + "/picks", NOW)[0], ["cfb-probe"],
           "   ...while a stale real artifact still does")
    finally:
        F.survey, F.slate_moves = _sv, _sm

    # ══════════════════════════════════════════════════════════════════
    section("6. 💰 THE CFBD BUDGET COUNTS THE DAILY ADVANCED-STATS CALL")
    # ══════════════════════════════════════════════════════════════════
    B = tree()
    src = open(os.path.join(ROOT, "cfb.py"), encoding="utf-8").read()
    open(B + "/cfb.py", "w", encoding="utf-8").write(src.replace("def fetch_adv(", "def _no_adv("))
    _root = cfbd_budget.ROOT
    try:
        with_adv = cfbd_budget.calls_per_build(3)["cfb-probe"]
        cfbd_budget.ROOT = B
        without = cfbd_budget.calls_per_build(3)["cfb-probe"]
    finally:
        cfbd_budget.ROOT = _root
    eq(with_adv - without, 1, "🔴 one call a build for the newest week's advanced stats (derived from cfb.py)")
finally:
    for t in TREES:
        shutil.rmtree(t, ignore_errors=True)
