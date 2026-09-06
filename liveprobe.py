#!/usr/bin/env python3
"""liveprobe.py — CAN THE FOOTBALL SCORES TAB EVER BE LIVE?

    LEAGUE=ncaaf python liveprobe.py
    LEAGUE=nfl   python liveprobe.py

🔴 THIS IS A PROBE. IT WRITES A REPORT AND CHANGES NOTHING ELSE. Same
contract as `news-probe`: a probe that ships its own findings is not a
probe, it is an unreviewed deploy. ⛔ It must never write
`schedule-<season>.json.gz`, a board, or a card.

════════════════════════════════════════════════════════════════════════
⚠️ WHY THIS FILE EXISTS AT ALL — AND IT IS NOT A GOOD REASON
════════════════════════════════════════════════════════════════════════
`claude/football-todo.md` said, from 2026-09-04 onward, that *"the
`live-probe` mode is built and waiting on one free run from Sam."*
🔴 **THAT WAS FALSE. THE MODE HAD NEVER EXISTED.** `live-probe` appeared
exactly once in the entire repository — inside a COMMENT — and was
repeated as fact across five separate messages without once being
checked. Sam tried to dispatch it on 2026-09-06 and the run failed,
because there was nothing to dispatch.
⛔ **This is ledger rules 25–27 exactly: a claim written down, restated,
and surviving a doc audit because nobody re-derived it.** The lesson is
not "build the probe" — it is **never restate a doc's claim about what
EXISTS without grepping for it.**

════════════════════════════════════════════════════════════════════════
🔴 THE QUESTION THIS ANSWERS
════════════════════════════════════════════════════════════════════════
The football Scores tab shows the schedule plus FINAL scores. MLB's tab
is live because `statsapi.mlb.com` is free and carries in-game state.
**CFBD and nflverse publish no live feed we hold.** ESPN's public
scoreboard does — the question is whether we can USE it, and that is
four separate questions, each of which this measures rather than assumes:

  1. **Is it reachable and free?** No key, no quota.
  2. **Does it carry live state?** A clock, a period, a score that moves.
  3. 🔴 **DOES IT JOIN TO THE SCHEDULE WE ALREADY STORE?** This is the
     one that decides the whole thing. A live feed we cannot line up
     against our own games is a second scoreboard, not a live tab.
     ⚠️ THERE IS A REAL HYPOTHESIS TO TEST HERE: CFBD's game ids look
     like ESPN event ids (both are 9-digit numbers in the 4018xxxxx
     range). **If they are the same ids the join is exact and free.**
     ⛔ It is a HYPOTHESIS. This probe measures the overlap; it does not
     assume it.
  4. **How stale is a single pull?** Reported honestly: one shot cannot
     measure a refresh rate, and this says so rather than guessing.

════════════════════════════════════════════════════════════════════════
✅ WHAT RUN 1 ANSWERED (2026-09-06, Sam's dispatch) — AND THE HOLE IT LEFT
════════════════════════════════════════════════════════════════════════
✅ **Reachable, free, HTTP 200. Every field this parser needs was
present in both leagues.** Five college games were in progress and all
five carried a clock, a period and both scores.
✅ 🔴 **THE JOIN IS EXACT FOR COLLEGE: 25 of 25.** CFBD's game id IS
ESPN's event id. A live college tab needs **no matcher at all**.
⛔ **The NFL join was 0 of 16** — our stored NFL id is nflverse's
`2026_01_NE_SEA`, a different id space entirely. ✅ **But nflverse's own
`games.csv` carries an `espn` column, populated for 272 of 272 games of
2026, and it holds exactly the ids ESPN returned** (401872656 = NE@SEA,
verified against the four the report published). ➡️ **So the NFL fix is
to CARRY A COLUMN WE ALREADY DOWNLOAD, not to build a matcher.**

🔴 **THE HOLE, AND IT IS THE ONE THAT DECIDES THE FEATURE NOW:
ESPN RETURNED 25 EVENTS WHILE OUR SCHEDULE HELD 206 COLLEGE GAMES THAT
DAY.** ⛔ The run reported *"100% of ESPN events matched"* — which is
true, and is **the wrong direction**. A tab that goes live for 25 of 206
games and silently leaves 181 looking unstarted is worse than one that is
honestly not live (rules 88 and 109: a check that enumerates what is
PRESENT cannot see what is ABSENT, and an exclusion with a direction must
publish the direction).
➡️ **So this version sweeps the endpoint's PARAMETERS and measures
coverage in BOTH directions.** `groups`, `dates` and `limit` are the
three candidates for why a Saturday came back as 25 games.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

LEAGUE = os.environ.get("LEAGUE", "ncaaf")
if LEAGUE not in ("nfl", "ncaaf"):
    print(f"FATAL: liveprobe.py is football only, got LEAGUE={LEAGUE!r}")
    sys.exit(1)

# 💰 FREE, NO KEY. ESPN's public site API — the same one every scoreboard
# widget on the internet uses. ⛔ If it ever needs a key it stops being an
# option and this probe should say so rather than acquire one.
PATH = {"ncaaf": "football/college-football", "nfl": "football/nfl"}[LEAGUE]
BASE = f"https://site.api.espn.com/apis/site/v2/sports/{PATH}/scoreboard"
URL = f"{BASE}?limit=400"
DATA = f"data/{LEAGUE}"
LATEST = f"{DATA}/latest"
UA = "gizmos-picks/1.0 (+https://github.com/smh0602/gizmos-picks)"

# ⚠️ `groups=80` IS ESPN'S FBS GROUP. It is a hypothesis about why 25
# came back, not a fact — which is why the sweep REPORTS every variant's
# count instead of just adopting one.
GROUP_FBS = "80"

# ⏱️ HOW LONG TO WAIT BEFORE THE SECOND PULL. ⚠️ Overridable so the tests
# do not sit for a minute — but the DEFAULT is what a real run uses, and
# a live game clock moves plainly in 45 seconds.
RECHECK_S = int(os.environ.get("LIVE_PROBE_RECHECK_S", "45"))


def log(m):
    print(f"[{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}] {m}", flush=True)


def stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def et(dt):
    """UTC -> US Eastern. ⚠️ zoneinfo, never a fixed offset — a hardcoded
    -5 is wrong for most of a football season."""
    try:
        from zoneinfo import ZoneInfo
        return dt.astimezone(ZoneInfo("America/New_York"))
    except Exception:
        return dt


def et_date(iso):
    """An ISO UTC stamp -> its ET calendar date. ⛔ THE SLATE DAY IS AN ET
    DAY. A Saturday 8pm ET kickoff is Sunday in UTC, and dating it by UTC
    puts half a college slate on the wrong day (ledger rule 107)."""
    if not iso:
        return None
    s = str(iso).replace("Z", "+00:00")
    for cut in (s, s[:19] + "+00:00"):
        try:
            t = datetime.fromisoformat(cut)
            break
        except ValueError:
            t = None
    if t is None:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return et(t).strftime("%Y-%m-%d")


def variants():
    """The URLs to sweep, widest last. ⚠️ EACH ONE IS A GUESS AT WHY A
    206-GAME SATURDAY CAME BACK AS 25 EVENTS; the report prints what each
    actually returned and lets the numbers pick."""
    today = et(datetime.now(timezone.utc)).strftime("%Y%m%d")
    v = [("default (what run 1 used)", f"{BASE}?limit=400")]
    if LEAGUE == "ncaaf":
        v += [
            (f"groups={GROUP_FBS} (FBS)", f"{BASE}?groups={GROUP_FBS}&limit=400"),
            ("dates=<today ET>", f"{BASE}?dates={today}&limit=400"),
            (f"groups={GROUP_FBS} + dates=<today ET>",
             f"{BASE}?groups={GROUP_FBS}&dates={today}&limit=400"),
        ]
    else:
        v += [("dates=<today ET>", f"{BASE}?dates={today}&limit=400")]
    return v


HEADERS_SEEN = {}


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        # 🔴 THE HEADERS DECIDE THE ARCHITECTURE, so keep them.
        # ⚠️ If ESPN sends `Access-Control-Allow-Origin: *`, THE BROWSER
        # CAN POLL IT DIRECTLY and a live tab needs NO cron, no stored
        # file and no commit — exactly how MLB's live tab already works
        # off `statsapi.mlb.com`. If it does not, the score has to be
        # fetched server-side and written to disk, and GitHub's scheduler
        # (which drops runs and cannot go below 5-minute granularity)
        # becomes the ceiling on how "live" the tab can be.
        # ⛔ TWO COMPLETELY DIFFERENT BUILDS. Worth one dict.
        try:
            HEADERS_SEEN.update({
                k: r.headers.get(k) for k in
                ("Access-Control-Allow-Origin", "Cache-Control", "Age",
                 "Expires", "Date", "X-Cache") if r.headers.get(k)})
        except Exception:
            pass
        return r.status, json.loads(r.read().decode("utf-8"))


def our_slate_date(g):
    """The ET calendar day of one of OUR stored games.

    ⚠️ THE TWO LEAGUES STORE `start` DIFFERENTLY AND CONVERTING BOTH THE
    SAME WAY IS A BUG. CFBD gives a real UTC stamp (`...Z`), so it must be
    converted to ET. nflverse gives a LOCAL date and time with **no
    timezone at all** — `build_schedule` says so in its own comment and
    refuses to stitch a fake offset — so its date is taken AS WRITTEN.
    ⛔ Parsing a naive local stamp as UTC would drag every night game back
    a day."""
    s = str(g.get("start") or "")
    if not s:
        return None
    return et_date(s) if (s.endswith("Z") or "+" in s[10:]) else s[:10]


def stored_schedule():
    """Our own current-season schedule, or None. ⛔ Read-only."""
    import glob
    import gzip
    best = None
    for p in sorted(glob.glob(f"{LATEST}/schedule-*.json.gz")):
        try:
            d = json.load(gzip.open(p, "rt"))
        except Exception:
            continue
        if best is None or (d.get("season") or 0) > (best.get("season") or 0):
            best = d
    return best


def main():
    report = {
        "league": LEAGUE,
        "kind": "DIAGNOSTIC",
        "note": ("Can the football Scores tab be live? This writes a report "
                 "and changes nothing. It is FREE — ESPN's public scoreboard, "
                 "no key."),
        "url": URL,
        "written_at": stamp(),
        "usable": False,
    }

    # ══════════════════════════════════════════════════════════════════
    # 🔴 THE PARAMETER SWEEP. Run 1 got 25 events on a day our own
    # schedule holds 206 college games, and NOTHING IN THAT REPORT COULD
    # SAY WHY — because it asked one URL. ⛔ Adopting `groups=80` on the
    # strength of it being a plausible explanation would be exactly the
    # guess this project keeps paying for.
    # ✅ So: ask every candidate, PRINT WHAT EACH RETURNED, and take the
    # widest — the numbers choose, not me.
    # ══════════════════════════════════════════════════════════════════
    doc, chosen, errs = None, None, []
    sweep = []
    for _name, _u in variants():
        try:
            _st, _d = fetch(_u)
            _n = len(_d.get("events") or [])
            sweep.append({"variant": _name, "url": _u, "http": _st,
                          "events": _n})
            if doc is None or _n > len(doc.get("events") or []):
                doc, chosen = _d, _name
                report["http"] = _st
                report["url"] = _u
        except urllib.error.HTTPError as e:
            sweep.append({"variant": _name, "url": _u,
                          "error": f"HTTPError {e.code}"})
            errs.append(f"HTTPError {e.code}")
        except Exception as e:
            sweep.append({"variant": _name, "url": _u,
                          "error": f"{type(e).__name__}: {e}"})
            errs.append(f"{type(e).__name__}: {e}")
    report["variant_sweep"] = sweep
    report["variant_used"] = chosen
    if doc is None:
        report["error"] = errs[0] if errs else "no variant returned a payload"
        report["conclusion"] = (
            "Could not reach ESPN at all — every URL variant failed. "
            "⚠️ This may be the runner's network rather than the feed — "
            "re-run before concluding anything."
            if not any(e.startswith("HTTPError") for e in errs) else
            "ESPN refused the request. A live tab is not available on this "
            "source. ⚠️ This may still be the runner's network rather than "
            "the feed — re-run before concluding anything.")
    else:
        ev = doc.get("events") or []
        report["events"] = len(ev)

        # ══════════════════════════════════════════════════════════════
        # 🔴 REPORT THE SHAPE BEFORE PARSING IT, BECAUSE I HAVE NEVER RUN
        # THIS AGAINST A REAL PAYLOAD. ESPN is blocked from the build
        # sandbox, so every field name below is a HYPOTHESIS about the
        # schema — and a probe whose guesses are wrong must come back with
        # the REAL shape, not a stack trace.
        # ⛔ This is the difference between "the run failed" and "here is
        # exactly what to read instead."
        # ══════════════════════════════════════════════════════════════
        report["payload_shape"] = {"top_level": sorted(doc.keys())[:20]}
        if ev:
            e0 = ev[0]
            c0 = (e0.get("competitions") or [{}])[0]
            st0 = c0.get("status") or {}
            cs0 = (c0.get("competitors") or [{}])[0]
            report["payload_shape"].update({
                "event": sorted(e0.keys()),
                "competition": sorted(c0.keys()),
                "status": sorted(st0.keys()),
                "status_type": sorted((st0.get("type") or {}).keys()),
                "competitor": sorted(cs0.keys()),
                "team": sorted((cs0.get("team") or {}).keys())[:20],
            })
            # ⚠️ NAME THE FIELDS THIS PARSER DEPENDS ON, and say for each
            # whether it was actually there. A missing one is the finding.
            want = {
                "events[].id": "id" in e0,
                "…competitions[0].status.type.state": "state" in (st0.get("type") or {}),
                "…status.displayClock": "displayClock" in st0,
                "…status.period": "period" in st0,
                "…competitors[].score": "score" in cs0,
                "…competitors[].homeAway": "homeAway" in cs0,
                "…competitors[].team.displayName": "displayName" in (cs0.get("team") or {}),
            }
            report["fields_this_parser_needs"] = want
            report["all_needed_fields_present"] = all(want.values())

        # ── what state is each game in, in the feed's own words ────────
        states, rows, parse_errors = {}, [], []
        for e in ev:
            # ⛔ ONE ODD EVENT MUST NOT KILL THE PROBE. A schema
            #    surprise is the finding, not a crash.
            try:
                comp = (e.get("competitions") or [{}])[0]
                st = ((comp.get("status") or {}).get("type") or {})
                state = st.get("state")
                states[state] = states.get(state, 0) + 1
                cs = comp.get("competitors") or []

                def side(home):
                    for c in cs:
                        if (c.get("homeAway") == ("home" if home else "away")):
                            return c
                    return {}
                h, a = side(True), side(False)
                rows.append({
                    "id": str(e.get("id")),
                    "away": ((a.get("team") or {}).get("displayName")),
                    "home": ((h.get("team") or {}).get("displayName")),
                    "away_score": a.get("score"),
                    "home_score": h.get("score"),
                    "state": state,
                    "detail": st.get("shortDetail"),
                    "clock": (comp.get("status") or {}).get("displayClock"),
                    "period": (comp.get("status") or {}).get("period"),
                    "start": e.get("date"),
                })
            except Exception as _pe:
                parse_errors.append(f"{type(_pe).__name__}: {_pe}")

        report["by_state"] = states
        report["in_progress"] = states.get("in", 0)
        if parse_errors:
            report["parse_errors"] = parse_errors[:5]
            report["n_parse_errors"] = len(parse_errors)

        # 🔴 DOES IT CARRY LIVE STATE? Measured on the games that are
        # ACTUALLY IN PROGRESS -- a clock on a finished game proves
        # nothing, and a slate with none in progress cannot answer this.
        live = [r for r in rows if r["state"] == "in"]
        report["live_sample"] = live[:5]
        if live:
            report["live_state_fields"] = {
                "with a running clock": sum(1 for r in live if r["clock"]),
                "with a period": sum(1 for r in live if r["period"] is not None),
                "with both scores": sum(1 for r in live
                                        if r["away_score"] is not None
                                        and r["home_score"] is not None),
                "of": len(live),
            }
        else:
            report["live_state_fields"] = None
            report["live_state_note"] = (
                "⚠️ NOTHING WAS IN PROGRESS when this ran, so whether the "
                "feed carries a moving clock is NOT ANSWERED. Re-run while "
                "games are on. ⛔ Do not read a full slate of finals as "
                "evidence either way.")

        # ══════════════════════════════════════════════════════════════
        # 🔴 THE JOIN. This is the question that decides the feature.
        # ⚠️ THE HYPOTHESIS, STATED BEFORE THE NUMBER: CFBD's game ids
        # look like ESPN event ids. If they ARE, the join is exact and
        # free. If they are not, a live tab needs a name-and-date matcher
        # -- and this project has already measured what that costs
        # (0 of 322 on a direct lookup; a whole resolver to fix it).
        # ══════════════════════════════════════════════════════════════
        sched = stored_schedule()
        if not sched:
            report["join"] = {"error": "no stored schedule to join against"}
            report["coverage"] = {
                "measurable": False,
                "why_not": ("no stored schedule, so there is nothing to "
                            "measure ESPN's coverage AGAINST"),
            }
        else:
            games = sched.get("games", [])
            # 🔴 TWO CANDIDATE JOIN KEYS, MEASURED SEPARATELY.
            # `id` is what we store. `espn` is nflverse's own ESPN column,
            # which the NFL schedule started carrying on 2026-09-06 —
            # ⚠️ AND THE ARTIFACT ON DISK PREDATES THE FIELD until the
            # next rebuild (ledger rule 104), so a missing `espn` is an
            # expected state here, not a fault.
            by_id = {str(g.get("id") or g.get("game_id")): g
                     for g in games if (g.get("id") or g.get("game_id"))}
            by_espn = {str(g.get("espn")): g for g in games if g.get("espn")}
            theirs = {r["id"] for r in rows}
            hit_id, hit_espn = theirs & set(by_id), theirs & set(by_espn)
            if len(hit_espn) > len(hit_id):
                ours, hit, field = by_espn, hit_espn, "espn"
            else:
                ours, hit, field = by_id, hit_id, "id"
            report["join"] = {
                "our_schedule_season": sched.get("season"),
                "our_games": len(games),
                "espn_events": len(theirs),
                "join_field": f"our `{field}` vs ESPN `events[].id`",
                "matched_on_our_id": len(hit_id),
                "matched_on_our_espn_column": len(hit_espn),
                "our_games_carrying_an_espn_column": len(by_espn),
                "ids_in_common": len(hit),
                "pct_of_espn_events_matched": (
                    round(100 * len(hit) / len(theirs), 1) if theirs else None),
                "verdict": (
                    f"EXACT — our `{field}` IS ESPN's event id, so a live tab "
                    "needs no matcher at all"
                    if theirs and len(hit) == len(theirs) else
                    "PARTIAL — some ids line up and some do not; a live tab "
                    "would need a fallback matcher for the rest"
                    if hit else
                    "NONE — the two id spaces are unrelated. A live tab would "
                    "need a name-and-date matcher, which on this project's "
                    "own measurement is a real piece of work, not a lookup"),
                "n_unmatched": len(theirs - set(ours)),
                "unmatched_examples": [r for r in rows
                                       if r["id"] not in ours][:5],
                # ⛔ THE DIRECTION THIS NUMBER DOES *NOT* MEASURE, said out
                # loud: matching every event ESPN returned says nothing
                # about the games it did not return. That is `coverage`.
                "direction_note": (
                    "⚠️ THIS IS 'HOW MANY OF ESPN'S EVENTS ARE OURS'. It is "
                    "NOT 'how many of our games ESPN sent' — see `coverage`, "
                    "which is the direction that decides the feature."),
            }

            # ══════════════════════════════════════════════════════════
            # 🔴 COVERAGE — THE MISSING DIRECTION FROM RUN 1.
            # Run 1 said "100% of ESPN events matched" on a day our own
            # schedule held 206 college games and ESPN returned 25.
            # ⛔ A tab that goes live for 25 of 206 games and leaves 181
            # looking unstarted is worse than one honestly not live.
            # Ledger rules 88 (a check enumerating what is PRESENT cannot
            # see what is ABSENT) and 109 (an exclusion with a direction
            # must publish the direction).
            # ══════════════════════════════════════════════════════════
            if not hit:
                report["coverage"] = {
                    "measurable": False,
                    "why_not": ("nothing joined, so which of OUR games ESPN "
                                "returned cannot be counted at all. ⛔ Fix "
                                "the join first; coverage is meaningless "
                                "without it."),
                }
            else:
                days = {}
                for r in rows:
                    d = et_date(r.get("start"))
                    if d:
                        days.setdefault(d, set()).add(r["id"])
                per_date, worst = [], None
                for d in sorted(days):
                    mine = [g for g in games if our_slate_date(g) == d]
                    got = [g for g in mine
                           if str(g.get(field) or "") in days[d]]
                    pct = round(100 * len(got) / len(mine), 1) if mine else None
                    per_date.append({
                        "et_date": d,
                        "espn_events": len(days[d]),
                        "our_games": len(mine),
                        "ours_that_espn_returned": len(got),
                        "ours_MISSING_from_espn": len(mine) - len(got),
                        "pct_of_ours_present": pct,
                        "missing_examples": [
                            f'{g.get("away")} @ {g.get("home")}'
                            for g in mine
                            if str(g.get(field) or "") not in days[d]][:5],
                    })
                    if pct is not None and (worst is None or pct < worst):
                        worst = pct
                report["coverage"] = {
                    "measurable": True,
                    "counted_on": f"our `{field}`, ET slate day",
                    "per_date": per_date,
                    "worst_pct_of_ours_present": worst,
                    "verdict": (
                        "NOT MEASURED — no ET day in this response had any of "
                        "our games on it" if worst is None else
                        "FULL — ESPN returned every game we have on these "
                        "days, so a live tab can cover the whole slate"
                        if worst >= 99.5 else
                        f"🔴 PARTIAL — as low as {worst}% of our games on a "
                        "day. ⛔ A live tab built on this would leave the "
                        "rest looking unstarted; it must mark only the games "
                        "the feed actually returned and say so"),
                    "note": ("⚠️ ET SLATE DAY, NOT UTC. A Saturday 8pm ET "
                             "kickoff is Sunday in UTC and dating it by UTC "
                             "splits one slate across two days (rule 107)."),
                }

        # ══════════════════════════════════════════════════════════════
        # ⏱️ DOES IT ACTUALLY MOVE? Run 1 said, correctly, that ONE PULL
        # CANNOT MEASURE A REFRESH RATE — and then left it there, which
        # costs another dispatch to answer. ✅ So take the second pull
        # HERE, in the same free run, and compare the clocks.
        # ⛔ ONLY WHEN SOMETHING IS IN PROGRESS. Two identical pulls of a
        # board of finals measure nothing and would waste the wait.
        # ══════════════════════════════════════════════════════════════
        report["staleness_note"] = (
            "⛔ A SINGLE PULL CANNOT MEASURE HOW OFTEN THIS UPDATES — so "
            "this run takes a second one and compares, rather than leaving "
            "the question open.")
        if live:
            import time
            time.sleep(RECHECK_S)
            try:
                _st2, doc2 = fetch(report["url"])
                second = {}
                for e in (doc2.get("events") or []):
                    try:
                        c = (e.get("competitions") or [{}])[0]
                        s = c.get("status") or {}
                        cs = c.get("competitors") or []
                        second[str(e.get("id"))] = (
                            s.get("displayClock"), s.get("period"),
                            sorted(str(x.get("score")) for x in cs))
                    except Exception:
                        continue

                def _first(r):
                    return (r["clock"], r["period"],
                            sorted([str(r["away_score"]),
                                    str(r["home_score"])]))
                seen = [r for r in live if r["id"] in second]
                moved = [r for r in seen if second[r["id"]] != _first(r)]
                report["refresh_check"] = {
                    "seconds_apart": RECHECK_S,
                    "live_games_compared": len(seen),
                    "games_whose_clock_or_period_changed": len(moved),
                    "example": ({"id": moved[0]["id"],
                                 "was": f'{moved[0]["clock"]} Q{moved[0]["period"]}',
                                 "now": f'{second[moved[0]["id"]][0]} '
                                        f'Q{second[moved[0]["id"]][1]}'}
                                if moved else None),
                    "verdict": (
                        "✅ IT MOVES — the clock advanced on "
                        f"{len(moved)} of {len(seen)} live games in "
                        f"{RECHECK_S}s, so the feed is live enough for a "
                        "polling tab"
                        if moved else
                        f"⚠️ NOTHING CHANGED IN {RECHECK_S}s across "
                        f"{len(seen)} live games. ⛔ That is ONE window: it "
                        "points at a cache in front of the feed, but it is "
                        "not proof the feed never updates. Re-run before "
                        "concluding."
                        if seen else
                        "NOT MEASURED — the second pull returned none of the "
                        "games that were live in the first"),
                }
            except Exception as _re:
                report["refresh_check"] = {
                    "error": f"{type(_re).__name__}: {_re}",
                    "verdict": ("the second pull failed, so the refresh rate "
                                "is NOT ANSWERED — the first pull stands on "
                                "its own"),
                }
        else:
            report["refresh_check"] = None
            report["refresh_note"] = (
                "⛔ NOT MEASURED, ON PURPOSE. Nothing was in progress, and "
                "two identical pulls of a board of finals measure nothing.")

        # 🔴 CAN THE BROWSER POLL IT ITSELF? This decides whether a live
        # tab is a page change or a whole collection pipeline.
        _acao = HEADERS_SEEN.get("Access-Control-Allow-Origin")
        report["browser_can_poll_directly"] = {
            "access_control_allow_origin": _acao,
            "cache_control": HEADERS_SEEN.get("Cache-Control"),
            "age": HEADERS_SEEN.get("Age"),
            "verdict": (
                "✅ YES — the header allows any origin, so index.html can "
                "fetch this the same way the MLB tab already polls "
                "statsapi. NO cron, NO stored file, NO commit; the page "
                "is as live as the feed."
                if _acao == "*" else
                f"⚠️ RESTRICTED to {_acao!r} — the browser cannot fetch "
                "this directly, so a live tab must be collected "
                "server-side and GitHub's scheduler becomes the ceiling "
                "on how live it can be."
                if _acao else
                "⛔ NO CORS HEADER SEEN. That usually means the browser "
                "will be refused, but this was measured from a SERVER "
                "request, which does not send an Origin — so it is not "
                "conclusive. A one-line fetch from the page settles it."),
        }

        report["usable"] = bool(ev)
        _cov = report.get("coverage") or {}
        report["conclusion"] = (
            f"{len(ev)} events via [{chosen}], {states.get('in', 0)} in "
            f"progress. JOIN: "
            + (report["join"].get("verdict", "") if sched else "no schedule")
            + " | COVERAGE: "
            + (_cov.get("verdict") or _cov.get("why_not") or "not measured")
        )

    os.makedirs(LATEST, exist_ok=True)
    out = f"{LATEST}/live-probe.json"
    with open(out, "w") as fh:
        json.dump(report, fh, indent=1)
    log(f"live-probe[{LEAGUE}] -> {out}")
    log(f"  {report.get('conclusion') or report.get('error')}")
    if report.get("join"):
        log(f"  join: {report['join'].get('ids_in_common')} of "
            f"{report['join'].get('espn_events')} ESPN events matched our "
            f"stored schedule")
    # ⛔ A PROBE THAT COULD NOT REACH ITS SOURCE MUST FAIL THE RUN. A
    # green run with an error report in it is the "green line on a red
    # run" defect wearing a different hat.
    return 0 if report.get("usable") else 1


if __name__ == "__main__":
    sys.exit(main())
