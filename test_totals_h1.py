#!/usr/bin/env python3
"""THE LIVE FIRST-HALF TOTAL — ONE MARKET, ONE REGION, PER GAME.

🔴 THIS IS THE ONLY PER-GAME MARKET ON THE GAMELINES JOB, which makes it
the one that walks toward the ceiling. `budget.py` says so in its own
output before this existed: *"anything that widens that window, or adds
a per-GAME market, spends against the CEILING and not against the
measurement."* Measured on this branch: the ceiling goes 219% -> 235% of
plan, +3,191 credits a month.

⛔ SO THE SHAPE OF THE SPEND IS GUARDED, NOT JUST THE SHAPE OF THE DATA:
one market, one region, no events-list call, nothing bought on a day with
no kickoff in the window, and `budget.py`'s printed price matched against
the request the collector actually builds.

⚠️ THE REGION IS `us2` BY DECISION, NOT BY DEFAULT. `[Sam, 2026-09-18]`
`us` carries four of his five books and `us2` carries Hard Rock, the one
he bets; the rule that settles it is `CLAUDE.md`'s *"a price from a book
he cannot bet is not a better price"*. ⛔ The cost of that choice is that
this market is NOT SHOPPED, and §1 has to say so rather than let a
one-book line sit in the same style as a five-book best price.

# @vacuity ⛔ exactly ONE market, and team_totals_h1 is not built
#   file: collect.py
#   find: HALF_LIVE_MARKETS = ["totals_h1"]
#   with: HALF_LIVE_MARKETS = ["totals_h1", "team_totals_h1"]
#
# @vacuity ⛔ exactly ONE region, and it is us2
#   file: collect.py
#   find: HALF_LIVE_REGION = "us2"
#   with: HALF_LIVE_REGION = "us,us2"
#
# @vacuity ...and swapping the region for `us` loses the book he bets
#   file: collect.py
#   find: HALF_LIVE_REGION = "us2"
#   with: HALF_LIVE_REGION = "us"
#
# ⚠️ THE LOCAL IS `window_end`, NOT `cutoff`, AND THAT IS WHY. The props
#    pull one function up uses `cutoff` for the same idea, so
#    `if when <= cutoff:` occurs TWICE in collect.py and the harness
#    rightly called this declaration MALFORMED — a `find` that matches
#    two places is not a mutation (rule 244). Renaming the local makes
#    the gate uniquely addressable AND reads better.
# @vacuity a day with no kickoff in the window buys NOTHING
#   file: collect.py
#   find:         if when <= window_end:
#   with:         if True:
#
# @vacuity ⛔ no events-list call — the bulk response already has the ids
#   file: collect.py
#   find:     half, half_spent, left = collect_half_totals(body, left)
#   with:     half, half_spent, left = collect_half_totals(odds_get(f"/sports/{SPORT}/events", {})[0], left)
#
# @vacuity budget.py prices the per-game half total, never at zero
#   file: budget.py
#   find:         return GAME_M * 2 + HALF_LIVE_M * HALF_LIVE_R * FB_GAMES[lg]
#   with:         return GAME_M * 2
#
# @vacuity §1 never lets a one-book line read as a shopped price
#   file: dossier_fb.py
#   find:             "shopping": "ONE BOOK",
#   with:             "shopping": "BEST OF FIVE",
"""
import ast
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section

CSRC = io.open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
BSRC = io.open(os.path.join(ROOT, "budget.py"), encoding="utf-8").read()

import collect          # noqa: E402  (imports after path setup, like the suite)
import dossier_fb       # noqa: E402


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 ONE MARKET, AND IT IS totals_h1")
# ══════════════════════════════════════════════════════════════════════
ck("the live list exists and is its own definition",
   isinstance(collect.HALF_LIVE_MARKETS, list),
   "HALF_LIVE_MARKETS=%r" % (collect.HALF_LIVE_MARKETS,))
ck("🔴 EXACTLY ONE market is requested",
   len(collect.HALF_LIVE_MARKETS) == 1,
   "⛔ a second market doubles a PER-GAME spend. asked: %s"
   % (collect.HALF_LIVE_MARKETS,))
ck("...and it is totals_h1",
   collect.HALF_LIVE_MARKETS == ["totals_h1"],
   "asked: %s" % (collect.HALF_LIVE_MARKETS,))
ck("⛔ team_totals_h1 is NOT in the live pull anywhere",
   "team_totals_h1" not in str(collect.HALF_LIVE_MARKETS)
   and 'markets": ",".join(HALF_LIVE_MARKETS)' in CSRC.replace("\n", " ")
   or "team_totals_h1" not in str(collect.HALF_LIVE_MARKETS),
   "6 books to totals_h1's 15, and it doubles a per-game spend")

# 🔴 THE PROBE'S LIST IS UNTOUCHED, AND THAT IS THE POINT OF TWO NAMES.
# ⛔ `HALFTIME_MARKETS` is the QUESTION `halftime-probe` asked and
#    `budget.py` prices that probe by parsing it. One line meaning two
#    things would silently reprice the probe (rule 117).
ck("⚠️ the PROBE's list still holds BOTH markets, untouched",
   collect.HALFTIME_MARKETS == ["totals_h1", "team_totals_h1"],
   "⛔ the live pull must not have been built by editing the probe's "
   "list. HALFTIME_MARKETS=%s" % (collect.HALFTIME_MARKETS,))
ck("...so they are two different definitions, not one reused",
   collect.HALFTIME_MARKETS is not collect.HALF_LIVE_MARKETS
   and collect.HALFTIME_MARKETS != collect.HALF_LIVE_MARKETS,
   "one name per meaning")


# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 EXACTLY ONE REGION, AND IT IS us2")
# ══════════════════════════════════════════════════════════════════════
R = collect.HALF_LIVE_REGION
ck("🔴 EXACTLY ONE region is requested",
   len([x for x in R.split(",") if x]) == 1,
   "⛔ a second region doubles a per-game spend against a ceiling already "
   "over 200%% of plan. region=%r" % (R,))
ck("🔴 ...and it is us2, the region Hard Rock lives in",
   R == "us2",
   "⛔ `us` carries four of the five books but NOT the one he bets, and "
   "CLAUDE.md is explicit: a price from a book he cannot bet is not a "
   "better price. region=%r" % (R,))
# ⛔ MEASURED AGAINST `BOOKS`, not asserted: the claim "us2 is where Hard
#    Rock lives" has to be checkable from this repo's own book table.
ck("⚠️ Hard Rock really is in this repo's book table under that name",
   any(v == "Hard Rock" for v in collect.BOOKS.values()),
   "BOOKS=%s" % (sorted(set(collect.BOOKS.values())),))
ck("the request the collector builds uses that constant, not a literal",
   '"regions": HALF_LIVE_REGION,' in CSRC,
   "⛔ a hardcoded region string would make the guard above decorative")


# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 NO EVENTS-LIST CALL — THE IDS ARE ALREADY IN HAND")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ THIS IS A CREDIT A RUN, and it is also what makes the ceiling
#    arithmetic come out at 1 per game.
_fn = CSRC[CSRC.index("def collect_half_totals("):]
_fn = _fn[:_fn.index("\ndef ")]
# ⛔ "/events" IS IN THE PER-EVENT ODDS PATH TOO — my first version of
#    this check asserted the substring was absent and went RED on
#    correct code, because `/sports/{SPORT}/events/{id}/odds` is exactly
#    what this function is supposed to call. ✅ The question is whether it
#    asks the events LIST, so every path it requests is read and each one
#    must be a per-event odds path.
# ⛔ AND IT COVERS THE CALL SITE, NOT JUST THE FUNCTION. My first version
#    read only `collect_half_totals`, so an events-list call added in
#    `collect_gamelines` — where the half pull is wired in — passed
#    green. The vacuity harness caught it: a mutation that buys the
#    events list at the call site proved nothing.
_gl = CSRC[CSRC.index("def collect_gamelines("):]
_gl = _gl[:_gl.index("\ndef ")]
_paths = re.findall(r'odds_get\(\s*\n?\s*f?"([^"]+)"', _fn + "\n" + _gl)
note("paths the gamelines job requests: %s" % (_paths,))
ck("🔴 the ONLY paths the gamelines job asks for are the bulk board and "
   "per-event odds",
   bool(_paths) and all(
       x == "/sports/{SPORT}/odds" or (x.endswith("/odds")
                                       and "/events/" in x)
       for x in _paths),
   "⛔ the bulk response of this same run already carries every event's "
   "id and commence_time, so an events LIST call would be a credit a run "
   "for a fact in hand. paths=%s" % (_paths,))
ck("...and none of them is the bare events list",
   not any(re.search(r"/events\}?$", x) for x in _paths),
   "paths=%s" % (_paths,))
ck("...and it takes the bulk response as its argument instead",
   "def collect_half_totals(body, left)" in CSRC
   and "collect_half_totals(body, left)" in CSRC,
   "it is handed `body` from the bulk call")
ck("...and it reads the id and the kickoff off those rows",
   'g.get("commence_time"), g.get("id")' in _fn,
   "the two fields it needs are the two the bulk response carries")


# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 A DAY WITH NO KICKOFF IN THE WINDOW BUYS NOTHING")
# ══════════════════════════════════════════════════════════════════════
# ⛔ DRIVEN, NOT READ. A comment saying it stands down is a comment.
import datetime


def drive(commences, league="ncaaf", left=5000):
    """Run the half pull against a synthetic board. Returns (out, spent, calls)."""
    calls = []

    def fake_get(path, params):
        calls.append((path, dict(params or {})))
        return ({"bookmakers": [
            {"key": "hardrockbet", "markets": [
                {"key": "totals_h1", "outcomes": [
                    {"name": "Over", "point": 21.5, "price": -110},
                    {"name": "Under", "point": 21.5, "price": -110}]}]}]},
            1, left - len(calls))

    body = [{"id": "ev%d" % i, "commence_time": c,
             "home_team": "H%d" % i, "away_team": "A%d" % i}
            for i, c in enumerate(commences)]
    old_get, old_lg = collect.odds_get, collect.LEAGUE
    collect.odds_get, collect.LEAGUE = fake_get, league
    try:
        out, spent, _left = collect.collect_half_totals(body, left)
    finally:
        collect.odds_get, collect.LEAGUE = old_get, old_lg
    return out, spent, calls


_now = datetime.datetime.now(datetime.timezone.utc)


def _iso(hours):
    return (_now + datetime.timedelta(hours=hours)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


W = collect.FB_PROPS_WINDOW_H
note("the paid window is %dh, and it is freshness.FB_PROPS_WINDOW_H — the "
     "SAME constant the props pull uses, not a second copy" % W)
ck("⚠️ the window really is the shared constant, not a local number",
   "FB_PROPS_WINDOW_H" in _fn and str(W) not in _fn.replace(
       "FB_PROPS_WINDOW_H", ""),
   "⛔ a second copy of the window would drift from the props pull "
   "(rule 117)")

out, spent, calls = drive([_iso(W + 48), _iso(W + 72)])
ck("🔴 a board whose games are all outside the window spends ZERO",
   spent == 0 and not calls and out == {},
   "⛔ a college gamelines cron fires every day of the week and a college "
   "slate is Saturday. spent=%s calls=%d" % (spent, len(calls)))

out, spent, calls = drive([])
ck("an EMPTY board spends zero", spent == 0 and not calls,
   "spent=%s calls=%d" % (spent, len(calls)))

out, spent, calls = drive([_iso(2), _iso(W + 48)])
ck("🔴 ...and exactly the games INSIDE the window are bought, no more",
   spent == 1 and len(calls) == 1 and sorted(out) == ["ev0"],
   "one of two games kicks off inside %dh. spent=%s out=%s"
   % (W, spent, sorted(out)))
ck("...one credit per game, which is one market x one region",
   spent == len(calls) * len(collect.HALF_LIVE_MARKETS)
   * len([x for x in R.split(",") if x]),
   "spent=%s calls=%s" % (spent, len(calls)))
ck("...and every call asked for exactly the declared market and region",
   all(c[1].get("markets") == "totals_h1"
       and c[1].get("regions") == "us2" for c in calls),
   "calls=%s" % (calls,))

ck("⛔ a game with NO kickoff time is dropped, never bought",
   drive([{"x": 1} and None])[1] == 0
   if False else drive([None])[1] == 0,
   "unbounded is not buyable")

_o, _s, _c = drive([_iso(2)], league="mlb")
ck("🔴 MLB never reaches this — its gamelines price is unchanged",
   _s == 0 and not _c and _o == {},
   "⛔ football only. MLB spent=%s calls=%d" % (_s, len(_c)))

_o, _s, _c = drive([_iso(2)] * 40, left=collect.RESERVE + 5)
ck("⛔ it stands down rather than eating the reserve",
   _s == 0 and not _c,
   "40 games at 1 credit against a reserve of %d. spent=%s"
   % (collect.RESERVE, _s))


# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 budget.py PRICES WHAT IS ACTUALLY REQUESTED (CROSS-FILE)")
# ══════════════════════════════════════════════════════════════════════
# ⛔ THE SAME CROSS-FILE QUESTION `test_halftime_probe.py` ALREADY ASKS OF
#    THE PROBE: the printed price has to match the request the collector
#    builds, or the budget is a number somebody typed.
ck("budget.py reads the live market list by its OWN name",
   "HALF_LIVE_MARKETS" in BSRC,
   "⛔ pricing it by widening the probe's regex would reprice the probe")
ck("...and the region by its own name too",
   "HALF_LIVE_REGION" in BSRC, "so a region change reprices this and "
   "nothing else")
ck("...and it FAILS LOUD rather than pricing a per-game market at zero",
   "refusing to price a PER-GAME market at zero" in BSRC,
   "rule 68, three times in this file's own history")
ck("⛔ the PROBE's own price still parses HALFTIME_MARKETS, untouched",
   "HALFTIME_MARKETS" in BSRC and "HALF_M * 1 + 1 + HALF_M * 2" in BSRC,
   "two prices, two definitions")

_out = subprocess.run([sys.executable, os.path.join(ROOT, "budget.py")],
                      capture_output=True, text=True, cwd=ROOT)
ck("budget.py runs clean", _out.returncode == 0,
   (_out.stderr or "")[-300:])
_gm = len(re.findall(r'"', re.search(
    r'^GAME_MARKETS\s*=\s*\[(.*?)\]', CSRC, re.S | re.M).group(1))) // 2
_games = {lg: n for lg, n in re.findall(
    r'"(ncaaf|nfl)":\s*(\d+)', re.search(
        r'^FB_GAMES\s*=\s*\{(.*?)\}', BSRC, re.S | re.M).group(1))}
for _lg, _n in sorted(_games.items()):
    want = _gm * 2 + len(collect.HALF_LIVE_MARKETS) * 1 * int(_n)
    got = re.search(r"%s\s+\S+ \S+ \S+ \S+ \S+\s+gamelines\s+(\d+)/run"
                    % _lg, _out.stdout)
    ck("🔴 %s gamelines priced at %d/run — bulk %d plus %d game(s) x 1"
       % (_lg, want, _gm * 2, int(_n)),
       bool(got) and int(got.group(1)) == want,
       "⛔ the printed price must equal the request the collector builds. "
       "printed=%s" % (got.group(1) if got else "not found"))
ck("⚠️ and the CEILING moved, which is the honest half of this change",
   "CEILING, NOT A FORECAST" in _out.stdout,
   "a per-game market spends against the ceiling; budget.py says so "
   "itself and this PR does not soften it")


# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 §1 NEVER LETS ONE BOOK READ AS A SHOPPED PRICE")
# ══════════════════════════════════════════════════════════════════════
_row = {"total": 45.5, "n_books": 5, "run_line": -3.5,
        "first_half_total": {"point": 21.5, "over": -110, "under": -110,
                             "book": "Hard Rock", "n_books": 1,
                             "region": "us2"}}
_s1 = dossier_fb.s_market(_row, None)
ck("§1 still reports MARKET provenance, never MODEL",
   _s1.get("basis") == dossier_fb.MARKET,
   "basis=%r" % (_s1.get("basis"),))
ck("the half total reaches §1", (_s1.get("first_half") or {}).get(
    "total") == 21.5, "first_half=%s" % (_s1.get("first_half"),))
ck("🔴 ...labelled ONE BOOK, on the value itself",
   (_s1.get("first_half") or {}).get("shopping") == "ONE BOOK",
   "⛔ rule 55: the label travels with the number. first_half=%s"
   % (_s1.get("first_half"),))
ck("🔴 ...and the sentence says it is NOT the best available",
   "may not be the best" in (_s1.get("first_half") or {}).get("why", ""),
   "a reader must be able to tell this from a five-book best price. "
   "why=%r" % ((_s1.get("first_half") or {}).get("why"),))
ck("...and it names the book", "Hard Rock" in (
    _s1.get("first_half") or {}).get("why", ""),
   "why=%r" % ((_s1.get("first_half") or {}).get("why"),))

_s0 = dossier_fb.s_market({"total": 45.5, "n_books": 5}, None)
ck("⛔ an unpriced game says so, and says it is about OUR request",
   _s0.get("first_half") is None
   and "what we asked for" in (_s0.get("first_half_note") or ""),
   "⛔ an absence in a response is evidence about the request, never "
   "about the book. note=%r" % (_s0.get("first_half_note"),))

# 🔴 THE MONEYLINE HALF IS A STATED GAP, IN READER ENGLISH.
ck("🔴 the first-half moneyline is named as a gap, not left silent",
   "no first-half moneyline" in (_s1.get("known_gap") or "").lower(),
   "known_gap=%r" % (_s1.get("known_gap"),))
ck("...with a remedy, the same register §6 uses",
   bool(_s1.get("known_gap_remedy")),
   "a gap that does not say what would change it is a shrug")
# ⛔ THE CLEAN-LOOK RULE GOVERNS EVERY WORD. verify_card.py fails the MLB
#    build on a jargon list; the same standard applies to what the page
#    prints here.
for _bad in ("us2", "HALF_LIVE", "totals_h1", "credits", "regions",
             "markets x", "per-game pull" if False else "endpoint"):
    ck("⛔ no jargon on the page: %r is absent from §1's prose" % _bad,
       not any(_bad in str(v) for k, v in _s1.items()
               if k in ("why", "known_gap", "known_gap_remedy",
                        "first_half_note")
               ) and _bad not in (_s1.get("first_half") or {}).get("why", ""),
       "Sam: lose the technical wording")


# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 THE PAGE PRINTS THE BUILDER'S STRING, AND FLAGS ONE BOOK")
# ══════════════════════════════════════════════════════════════════════
import jsblock                                          # noqa: E402
_js = jsblock.js_block("fbDosFacts", os.path.join(ROOT, "index.html"))
ck("the panel reads the half total from the section",
   "s.first_half" in _js, "it renders what the builder wrote")
ck("🔴 ...and marks it as one book rather than styling it like the rest",
   "Not shopped" in _js and "donebook" in _js,
   "⛔ a bare li() would tell the reader it was shopped the same way")
ck("🔴 the gap sentence is printed VERBATIM — no regex edit in the page",
   "s.known_gap}" in _js.replace(" ", "")
   or "${s.known_gap}" in _js,
   "rule 132: print the builder's own string. My first version "
   "sentence-cased it here with .replace(), which is the page editing "
   "the model's words.")
ck("⛔ ...and nothing in the panel rewrites that string",
   "known_gap.replace" not in _js,
   "found a transform on the builder's prose")
ck("the absent case is SHOWN, not hidden",
   "first_half_note" in _js,
   "an unavailable reading is displayed, the same as an UNAVAILABLE "
   "section")
_css = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
ck("the one new class is actually defined",
   ".donebook{" in _css, "an undefined class styles nothing")
