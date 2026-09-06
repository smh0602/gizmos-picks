#!/usr/bin/env python3
"""wfroutes.py — THE ONE PARSER FOR THE WORKFLOW'S ROUTING TABLE.

    from wfroutes import parse_arms, parse_routes

⛔ THIS REGEX EXISTED IN **FIVE** PLACES — `budget.py` and four test
files — as byte-identical copies. When the routing table learned to name
TWO leagues on one arm (`LEAGUE="ncaaf nfl"`, added 2026-09-06 because
Sam asked for one run to serve both sports), **every one of the five
stopped matching those arms and said nothing.** The tests read fewer
routes and still passed their own shape checks, and `budget.py` would
have gone back to under-reporting football spend — the failure its own
header calls the worst one available to it.

✅ Same family as the fifteen byte-identical copies of `eq()` the test
harness replaced: **a helper duplicated is a helper that breaks in four
places you did not edit** (ledger rule 117).

⚠️ THIS MODULE IMPORTS NOTHING AND PRINTS NOTHING. It lives apart from
`budget.py` on purpose — that file is a top-to-bottom report, so
importing it for one function ran the whole budget.
"""
import re


# 🔴 THE ONE PARSER FOR THE WORKFLOW'S ROUTING TABLE. `[2026-09-06]`
# ⛔ THIS REGEX EXISTED IN **FIVE** PLACES — here, and in four test files
# — and they were byte-identical copies. When the routing table learned
# to name TWO leagues on one arm (`LEAGUE="ncaaf nfl"`), every one of the
# five stopped matching those arms **and said nothing**: the tests read
# fewer routes and still passed their own shape checks, and THIS FILE
# would have gone back to under-reporting football spend — the exact
# failure its own header calls the worst one available to it.
# ✅ ONE FUNCTION, IMPORTED BY ALL FIVE. Same family as the fifteen copies
# of `eq()` that the test harness replaced (ledger rule 117): a helper
# duplicated is a helper that breaks in four places you did not edit.
# ⚠️ IT YIELDS ONE ROW PER LEAGUE, so a two-league arm reads as two
# routes and every existing caller keeps working unchanged.
def parse_arms(wf_text):
    """[(cron, league_field, modes)] — ONE ROW PER `case` ARM, with the
    league field exactly as written (`nfl`, or `ncaaf nfl`).

    ⚠️ USE THIS WHEN THE QUESTION IS ABOUT THE FILE — duplicate arms,
    unreachable arms — because shell `case` takes the FIRST match and a
    second arm for the same cron string can never run."""
    return re.findall(
        r'"([\d ,*/-]+)"\)\s*LEAGUE="?([a-z ]+?)"?;\s*MODES="([a-z0-9 -]+)"',
        wf_text)


def parse_routes(wf_text):
    """[(cron, league, modes)] — ONE ROW PER LEAGUE.

    ⚠️ USE THIS WHEN THE QUESTION IS ABOUT A LEAGUE — what gets built for
    it, what it costs — so a two-league arm counts for both."""
    return [(c, one, ms) for c, lg, ms in parse_arms(wf_text)
            for one in lg.split()]


