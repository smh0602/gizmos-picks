#!/usr/bin/env python3
"""fb_weather.py — NWS FORECASTS BEFORE EVERY FOOTBALL GAME. STORED ONLY.

`[Sam, 2026-10-14]` "look at every aspect ... and your only goal is to do
anything to make it better". Cowork asked for the data first: ⛔ NO FIT, INPUT,
PICK OR CHANCE READS THIS FILE YET. Cowork tests it on past games once it lands,
and only what helps becomes a challenger (T65's contest).

Once a day, inside the league's existing daily run (`nfl-logs` for the NFL,
`cfb-probe` for college), for every NFL game and every FBS-vs-FBS college game
kicking off within the next 7 days at an outdoor US venue: the US National
Weather Service (api.weather.gov, free for any use) is asked
`/points/{lat},{lon}` (cached per venue) and then its `forecastHourly` link, and
the kickoff hour's wind, gust (mph), precipitation chance and temperature (F)
are stored in data/<lg>/latest/weather-<season>.json.gz, keyed by game id:

    {"venue", "lat", "lon", "first": {...}, "last": {...}}
    each {pulled_at, forecast_for, wind, gust, precip_pct, temp}

⛔ "first" is never overwritten; "last" is only ever replaced by a forecast
pulled BEFORE kickoff. A dome or closed roof is stored as indoor with no call; a
venue outside the US (or not in the stadium table) is skipped and says so.
⛔ NEVER RAISES: requests are capped per run and back off on errors, and a
failure is written into the file, never into the run's exit code.
Stdlib only.
"""
import datetime
import gzip
import json
import os
import re
import time
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
UA = "gizmos-picks (https://github.com/smh0602/gizmos-picks)"   # NWS asks for one
API = "https://api.weather.gov"
HORIZON_DAYS = 7
MAX_CALLS = 160              # per run; a college Saturday is ~60 venues + points
MAX_FAILS = 6                # consecutive failures before the run's pass stops
UTC = datetime.timezone.utc

# The NFL's stadiums, keyed by the venue name nflverse writes (older names
# kept, so 2025's rows match). (lat, lon). ⛔ A venue not here (London, Munich,
# Madrid, Mexico City, Melbourne, Rio...) is skipped, never guessed.
NFL_STADIUMS = {
    "State Farm Stadium": (33.5276, -112.2626), "Mercedes-Benz Stadium": (33.7554, -84.4008),
    "M&T Bank Stadium": (39.2780, -76.6227), "Highmark Stadium": (42.7738, -78.7870),
    "New Era Field": (42.7738, -78.7870), "Bank of America Stadium": (35.2258, -80.8528),
    "Soldier Field": (41.8623, -87.6167), "Paycor Stadium": (39.0955, -84.5161),
    "FirstEnergy Stadium": (41.5061, -81.6995), "Huntington Bank Field": (41.5061, -81.6995),
    "AT&T Stadium": (32.7473, -97.0945), "Empower Field at Mile High": (39.7439, -105.0201),
    "Ford Field": (42.3400, -83.0456), "Lambeau Field": (44.5013, -88.0622),
    "NRG Stadium": (29.6847, -95.4107), "Reliant Stadium": (29.6847, -95.4107),
    "Lucas Oil Stadium": (39.7601, -86.1639), "EverBank Stadium": (30.3239, -81.6373),
    "TIAA Bank Stadium": (30.3239, -81.6373), "GEHA Field at Arrowhead Stadium": (39.0489, -94.4839),
    "Arrowhead Stadium": (39.0489, -94.4839), "SoFi Stadium": (33.9535, -118.3392),
    "Allegiant Stadium": (36.0909, -115.1833), "Hard Rock Stadium": (25.9580, -80.2389),
    "U.S. Bank Stadium": (44.9737, -93.2577), "Gillette Stadium": (42.0909, -71.2643),
    "Caesars Superdome": (29.9511, -90.0812), "Mercedes-Benz Superdome": (29.9511, -90.0812),
    "MetLife Stadium": (40.8135, -74.0745), "Lincoln Financial Field": (39.9008, -75.1675),
    "Acrisure Stadium": (40.4468, -80.0158), "Lumen Field": (47.5952, -122.3316),
    "Levi's Stadium": (37.4030, -121.9700), "Raymond James Stadium": (27.9759, -82.5033),
    "Nissan Stadium": (36.1665, -86.7713), "FedExField": (38.9078, -76.8645),
    "Northwest Stadium": (38.9078, -76.8645),
}
INDOOR_ROOFS = {"dome", "closed"}


def log(m):
    print(m, flush=True)


def latest(lg, root=None):
    return os.path.join(root or ROOT, "data", lg, "latest")


def _iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


# `[2026-10-26]` ⛔ ONE COPY (rule 117): the US Eastern daylight-time rule moved, unchanged, to
#    freshness.py, which must stand alone (sandboxes copy it by itself) and now needs it for the
#    game-day injury check. Read from there; freshness.py is stdlib only too. cfb_injuries keeps
#    importing it from here. `[2026-10-26, review]` and so is the wall-time -> UTC step
#    (`et_wall_utc`), which `kickoff_utc` below had as its own copy of the same expression.
from freshness import _us_eastern_offset, et_wall_utc  # noqa: E402,F401


def kickoff_utc(start):
    """A schedule row's kickoff in UTC. College rows carry a zone (Z); nflverse
    writes Eastern wall time with none. None when there is no time of day."""
    s = (start or "").strip()
    if len(s) < 16:
        return None
    if s.endswith("Z") or re.search(r"[+-]\d\d:?\d\d$", s):
        try:
            return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            return None
    try:
        naive = datetime.datetime.strptime(s[:16], "%Y-%m-%dT%H:%M")
    except ValueError:
        return None
    return et_wall_utc(naive)


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/geo+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _mph(v):
    """'10 mph', '5 to 10 mph' (the top), {'value': kmh, 'unitCode': ...} -> mph."""
    if v is None:
        return None
    if isinstance(v, dict):
        x = v.get("value")
        if x is None:
            return None
        return round(float(x) / 1.609344, 1) if "km_h" in str(v.get("unitCode")) else round(float(x), 1)
    nums = re.findall(r"\d+(?:\.\d+)?", str(v))
    return float(nums[-1]) if nums else None


def kickoff_period(periods, kick):
    """The forecastHourly period whose hour holds the kickoff, or None."""
    for p in periods or []:
        try:
            a = datetime.datetime.fromisoformat(p["startTime"]).astimezone(UTC)
            b = datetime.datetime.fromisoformat(p["endTime"]).astimezone(UTC)
        except (KeyError, ValueError, TypeError):
            continue
        if a <= kick < b:
            return p
    return None


def reading(period, pulled_at, kick):
    temp = period.get("temperature")
    if isinstance(temp, dict):
        temp = temp.get("value")
    if temp is not None and str(period.get("temperatureUnit") or "F").upper() == "C":
        temp = round(float(temp) * 9 / 5 + 32, 1)
    pop = period.get("probabilityOfPrecipitation")
    return {"pulled_at": pulled_at, "forecast_for": _iso(kick), "wind": _mph(period.get("windSpeed")),
            "gust": _mph(period.get("windGust")),
            "precip_pct": pop.get("value") if isinstance(pop, dict) else pop, "temp": temp}


def merge(entry, new, kick):
    """⛔ "first" is never overwritten; "last" only by a forecast pulled before
    kickoff. Returns the entry."""
    if new["pulled_at"] >= _iso(kick):
        return entry
    entry.setdefault("first", new)
    entry["last"] = new
    return entry


def nfl_venues(games):
    """{game id: venue facts} from nflverse's schedule rows and the stadium table."""
    out = {}
    for g in games:
        v, roof = g.get("venue"), (g.get("roof") or "").lower()
        ll = NFL_STADIUMS.get(v)
        out[str(g["id"])] = ({"venue": v, "lat": ll[0], "lon": ll[1], "roof": roof or None} if ll else
                             {"venue": v, "skipped": "venue not in the 32-stadium table (an international "
                                                     "or neutral site, outside NWS coverage or unknown)"})
    return out


def college_venues(games, venues):
    """{game id: venue facts} from the schedule's venue name and CFBD /venues."""
    out = {}
    for g in games:
        v = venues.get(g.get("venue") or "")
        if not v or v.get("lat") is None or v.get("lon") is None:
            out[str(g["id"])] = {"venue": g.get("venue"), "skipped": "venue not in CFBD /venues with coordinates"}
        elif (v.get("country") or "US") != "US":
            out[str(g["id"])] = {"venue": g.get("venue"), "skipped": "outside the US: NWS covers US venues only"}
        else:
            out[str(g["id"])] = {"venue": g.get("venue"), "lat": v["lat"], "lon": v["lon"],
                                 "roof": "dome" if v.get("dome") else None}
    return out


def eligible(lg, games, now):
    """NFL games, and FBS-vs-FBS college games, kicking off within HORIZON_DAYS."""
    end = now + datetime.timedelta(days=HORIZON_DAYS)
    out = []
    for g in games:
        k = kickoff_utc(g.get("start"))
        if k is None or not (now < k <= end) or g.get("final"):
            continue
        if lg == "ncaaf" and not (g.get("home_class") == "fbs" and g.get("away_class") == "fbs"):
            continue
        out.append((g, k))
    return out


def _jz(p):
    try:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def run(lg, root=None, now=None, get=_get, sleep=time.sleep, log=log, season=None, venues=None, base=None):
    """One daily pass for league `lg`. -> the document written. ⛔ Never raises.
    `base`: the league's latest/ directory as the caller writes it (collect.py's
    relative path), so a run from another tree writes into that tree."""
    now = now or datetime.datetime.now(UTC)
    try:
        import freshness as _fr
        season = season or _fr.current_football_season(now)
        base = base or latest(lg, root)
        path = os.path.join(base, "weather-%d.json.gz" % season)
        doc = _jz(path) or {}
        games = (_jz(os.path.join(base, "schedule-%d.json.gz" % season)) or {}).get("games") or []
        todo = eligible(lg, games, now)
        if lg == "nfl":
            facts = nfl_venues([g for g, _k in todo])
        else:
            if venues is None:
                venues = (_jz(os.path.join(base, "venues-%d.json.gz" % season)) or {}).get("venues") or {}
            facts = college_venues([g for g, _k in todo], venues)
        store, points = doc.get("games") or {}, doc.get("points") or {}
        calls = fails = 0
        tally = {"forecast": 0, "indoor": 0, "skipped": 0, "failed": 0, "not_reached": 0}
        for g, kick in todo:
            gid = str(g["id"])
            f = facts[gid]
            e = store.setdefault(gid, {})
            e.update({k: f[k] for k in ("venue", "lat", "lon") if k in f})
            e["kickoff"] = _iso(kick)
            if "skipped" in f:
                e["skipped"] = f["skipped"]
                tally["skipped"] += 1
                continue
            if f.get("roof") in INDOOR_ROOFS:
                e["indoor"] = True                       # ⛔ no call for a dome or a closed roof
                tally["indoor"] += 1
                continue
            if calls >= MAX_CALLS or fails >= MAX_FAILS:
                tally["not_reached"] += 1
                continue
            key = "%.4f,%.4f" % (f["lat"], f["lon"])
            try:
                if key not in points:
                    calls += 1
                    points[key] = get("%s/points/%s" % (API, key))["properties"]["forecastHourly"]
                calls += 1
                fc = get(points[key])
                p = kickoff_period((fc.get("properties") or {}).get("periods"), kick)
                if p is None:
                    e["note"] = "the hourly forecast does not reach kickoff yet"
                    continue
                merge(e, reading(p, _iso(now), kick), kick)
                e.pop("error", None)
                tally["forecast"] += 1
                fails = 0
            except Exception as ex:                      # ⛔ a failure never stops the run
                fails += 1
                tally["failed"] += 1
                e["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:160])
                sleep(min(30, 2 ** fails))
        out = {"league": lg, "season": season, "kind": "DESCRIPTIVE", "source": API,
               "built_at": _iso(now), "games": store, "points": points,
               "last_run": dict(tally, calls=calls, games_in_window=len(todo)),
               "note": ("NWS hourly forecasts for the kickoff hour. STORED ONLY: no model "
                        "reads this file. 'first' is never overwritten; 'last' is only ever "
                        "replaced by a forecast pulled before kickoff.")}
        os.makedirs(base, exist_ok=True)
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(out, fh, separators=(",", ":"))
        log("    weather %s %d: %d game(s) in the window, %s" % (lg, season, len(todo), out["last_run"]))
        return out
    except Exception as ex:
        log("    ⚠️ weather %s did not run: %s: %s" % (lg, type(ex).__name__, ex))
        return None
