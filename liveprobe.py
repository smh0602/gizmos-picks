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
URL = (f"https://site.api.espn.com/apis/site/v2/sports/{PATH}/scoreboard"
       "?limit=400")
DATA = f"data/{LEAGUE}"
LATEST = f"{DATA}/latest"
UA = "gizmos-picks/1.0 (+https://github.com/smh0602/gizmos-picks)"


def log(m):
    print(f"[{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}] {m}", flush=True)


def stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


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

    try:
        status, doc = fetch(URL)
        report["http"] = status
    except urllib.error.HTTPError as e:
        report["error"] = f"HTTPError {e.code}"
        report["conclusion"] = ("ESPN refused the request. A live tab is not "
                                "available on this source.")
    except Exception as e:
        report["error"] = f"{type(e).__name__}: {e}"
        report["conclusion"] = ("Could not reach ESPN at all. ⚠️ This may be "
                                "the runner's network rather than the feed — "
                                "re-run before concluding anything.")
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
        else:
            ours = {str(g.get("id") or g.get("game_id")): g
                    for g in sched.get("games", [])}
            theirs = {r["id"] for r in rows}
            hit = theirs & set(ours)
            report["join"] = {
                "our_schedule_season": sched.get("season"),
                "our_games": len(ours),
                "espn_events": len(theirs),
                "ids_in_common": len(hit),
                "pct_of_espn_events_matched": (
                    round(100 * len(hit) / len(theirs), 1) if theirs else None),
                "verdict": (
                    "EXACT — ESPN's event id IS our schedule's game id, so a "
                    "live tab needs no matcher at all"
                    if theirs and len(hit) == len(theirs) else
                    "PARTIAL — some ids line up and some do not; a live tab "
                    "would need a fallback matcher for the rest"
                    if hit else
                    "NONE — the two id spaces are unrelated. A live tab would "
                    "need a name-and-date matcher, which on this project's "
                    "own measurement is a real piece of work, not a lookup"),
                "unmatched_examples": [r for r in rows
                                       if r["id"] not in ours][:5],
            }

        # ⚠️ ONE PULL CANNOT MEASURE A REFRESH RATE, and saying otherwise
        # would be inventing a number. What it CAN report is whether the
        # payload carries its own freshness signal.
        report["staleness_note"] = (
            "⛔ A SINGLE PULL CANNOT MEASURE HOW OFTEN THIS UPDATES. To "
            "know that, run this twice a few minutes apart while a game is "
            "in progress and compare the clocks. This report is one "
            "snapshot and does not claim otherwise.")

        report["usable"] = bool(ev)
        report["conclusion"] = (
            f"{len(ev)} events, {states.get('in', 0)} in progress. "
            + (report["join"].get("verdict", "") if sched else "")
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
