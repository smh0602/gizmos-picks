#!/usr/bin/env python3
"""
THE GAME LINES ON A CARD BELONG TO THAT CARD'S DAY.

🔴 THE DEFECT, REPORTED BY SAM AND MEASURED ON THE LIVE CARDS 2026-09-14:

    NFL card dated 2026-09-13    7 lines on 09-13 · 1 on 09-14
                                 · 7 lines on 09-20   ⛔ NEXT WEEK
    CFB card dated 2026-09-12    ZERO lines from its own slate
                                 · 8 lines on 09-18 and 09-19  ⛔ ALL of it

Sam: *"there is games for next week already in the game lines tab, we
should only be providing picks for the current week not the weeks in the
future."*

⛔ **LEDGER RULE 101 — ONE DAY FILTER, GOVERNING EVERY SURFACE THE CARD
PUBLISHES — WAS NEVER APPLIED HERE.** It reached the board and it reached
the parlays. `game_lines` shipped two drops later and never picked it up.

➡️ **SO THE CARD CONTRADICTED ITS OWN LABEL.** The header reads *"📅
Sunday, September 13 only. Every row here is a game on that day"* and the
list underneath it printed September 20. **That is worse than either
answer on its own**, because a reader who trusts the header cannot tell
which half is wrong.

════════════════════════════════════════════════════════════════════════
⛔ WHAT THIS FILE DOES NOT CLAIM: that one day is a better product than
one week. That is Sam's call. What is owned here is that the list and the
LABEL ABOVE IT agree — whatever the window is, the card must not say one
thing and show another.
"""
import gzip
import json
import os
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import card_fb as C  # noqa: E402


def _snap(games):
    """A gamelines snapshot whose games are exactly `games`.

    Every game carries three books at one signed number so it clears
    SHOP_MIN_BOOKS and produces a row — the day filter is the only thing
    under test, so nothing else may be what excludes a game.
    """
    out = []
    for i, (gid, commence) in enumerate(games):
        out.append({
            "id": gid, "away": "A%d" % i, "home": "H%d" % i,
            "commence": commence,
            "books": {b: {"h2h": {"A%d" % i: {"px": px, "pt": None}}}
                      for b, px in (("draftkings", -110), ("fanduel", -105),
                                    ("betmgm", -120))},
        })
    return {"games": out}


print("═══ 1. 🔴 A GAME ON ANOTHER DAY IS NOT ON THIS CARD ═══")
# ⛔ DRIVEN, NOT READ. A source check cannot tell a filter that runs from
#    one that is written and never called (rule 217).
snap = _snap([
    ("same",     "2026-09-13T17:00:00Z"),   # Sun 1:00pm ET  — the slate
    ("same2",    "2026-09-13T20:25:00Z"),   # Sun 4:25pm ET  — the slate
    ("nextweek", "2026-09-20T17:00:00Z"),   # ⛔ SEVEN DAYS LATER
])
rows, meta = C.build_game_lines(snap, n=None, slate="2026-09-13")
ids = {r["game_id"] for r in rows}
ck("🔴 next week's game is NOT on this card",
   "nextweek" not in ids,
   "⛔ THIS IS THE DEFECT SAM REPORTED. Got %s" % sorted(ids))
ck("✅ ...and both of the slate's games still are",
   {"same", "same2"} <= ids,
   "the filter must remove the other day and nothing else. Got %s"
   % sorted(ids))
ck("⛔ the drop is COUNTED and the date is NAMED",
   meta["off_day_games"] == 1 and meta["off_day_dates"] == ["2026-09-20"],
   "a filter that silently drops rows is indistinguishable from a feed "
   "that never carried them (rule 217). Got %r / %r"
   % (meta["off_day_games"], meta["off_day_dates"]))

print("\n═══ 2. 🔴 ET, NEVER THE UTC STRING ═══")
# 🔴 THE TRAP THAT WOULD MAKE THIS FILTER WRONG IN THE OTHER DIRECTION. A
#    Sunday 8:20pm ET kickoff is 00:20Z MONDAY. Slicing the raw UTC string
#    files it under the wrong day and would throw Sunday Night Football
#    off Sunday's own card — the same defect ledger rule 60 exists for,
#    arriving through a different door.
snap = _snap([("snf", "2026-09-14T00:20:00Z")])       # Sun 8:20pm ET
rows, meta = C.build_game_lines(snap, n=None, slate="2026-09-13")
ck("🔴 a Sunday 8:20pm ET kickoff stays on SUNDAY's card",
   {r["game_id"] for r in rows} == {"snf"},
   "⛔ 2026-09-14T00:20Z is Sunday night in ET. A UTC string slice files "
   "it under Monday and drops it. Got %s rows, off_day=%s"
   % (len(rows), meta["off_day_games"]))
snap = _snap([("mnf", "2026-09-15T00:15:00Z")])       # Mon 8:15pm ET
rows, meta = C.build_game_lines(snap, n=None, slate="2026-09-13")
ck("✅ ...and Monday night is correctly NOT on Sunday's card",
   not rows and meta["off_day_dates"] == ["2026-09-14"],
   "the boundary has to cut in both directions or it is not a boundary. "
   "Got %d rows / %r" % (len(rows), meta["off_day_dates"]))

print("\n═══ 3. ⛔ NO SLATE MEANS NO FILTER, AND THAT IS DELIBERATE ═══")
snap = _snap([("a", "2026-09-13T17:00:00Z"), ("b", "2026-09-20T17:00:00Z")])
rows, meta = C.build_game_lines(snap, n=None)
ck("⛔ `slate=None` returns every game",
   len({r["game_id"] for r in rows}) == 2 and meta["off_day_games"] == 0,
   "the parameter is opt-in so a caller that has no card date cannot be "
   "silently given a filtered list it did not ask for. Got %d" % len(rows))

print("\n═══ 4. 🔴 THE EMPTY STATE NAMES ITS OWN CAUSE ═══")
# 🔴 TWO EMPTY STATES, TWO CAUSES, AND ONLY ONE RESOLVES BY WAITING
#    (rule 222). "The books have not agreed on a number yet" and "every
#    open line belongs to another day" are different facts, and on a
#    Monday the college card is legitimately the second one.
snap = _snap([("x", "2026-09-19T17:00:00Z"), ("y", "2026-09-18T23:00:00Z")])
rows, meta = C.build_game_lines(snap, n=None, slate="2026-09-12")
txt = C.game_lines_rule(rows, meta)
ck("🔴 an all-off-day board explains itself in the OTHER sentence",
   not rows and "belongs to a different day" in txt,
   "⛔ the generic 'not enough agreement to compare prices' would be "
   "FALSE here — the books agree fine, the games are just next week. "
   "Got: %r" % txt[:200])
ck("✅ ...and it names the card's day and the dates it dropped",
   "2026-09-12" in txt and "2026-09-19" in txt,
   "a reader must be able to see WHICH day the card is and WHICH days "
   "the open lines are, or the sentence is an apology instead of a fact")
snap = _snap([("z", "2026-09-13T17:00:00Z")])
snap["games"][0]["books"] = {"draftkings": {"h2h": {"A0": {"px": -110, "pt": None}}}}
rows, meta = C.build_game_lines(snap, n=None, slate="2026-09-13")
ck("⛔ ...and a thin-agreement board still gets the ORIGINAL sentence",
   not rows and "not enough agreement" in C.game_lines_rule(rows, meta),
   "one book is not three. Collapsing this into the day sentence would "
   "tell a reader to come back next week for a board that will be "
   "priced in an hour")

print("\n═══ 5. 🔴 AND THE LIVE CARDS AGREE WITH THEIR OWN LABEL ═══")
# 🔴 THE ASSERTION THAT WOULD HAVE CAUGHT THIS IN PRODUCTION. Every stored
#    football card must satisfy it, so a card that ships a foreign day
#    fails here rather than on Sam's screen.
#
# ⚠️ AND IT IS GATED ON A STRUCTURAL MARKER, NOT ON A DATE. A stored card
#    built BEFORE this filter shipped still carries the defect, and it
#    stays on disk until the next `card-fb` cron rewrites it — so a bare
#    assertion here would go RED on upload, through no fault of the code,
#    and then quietly go green on its own. That is rule 227 exactly: a
#    check whose subject is "has the cron run yet" is a check about the
#    calendar.
# ✅ `game_lines_meta.slate` EXISTS ONLY ON A CARD BUILT BY THE FIXED
#    BUILDER. So the gate is the card's own SHAPE — a card that had the
#    filter and leaked anyway FAILS, and a card that predates it is
#    reported as not exercised. ⛔ It can never silently excuse the case
#    it exists to catch, and it expires by itself the moment every card
#    has been rebuilt.
_checked = _old = 0
for lg in ("ncaaf", "nfl"):
    p = os.path.join(ROOT, "picks", "fb-%s-latest.json" % lg)
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    slate = d.get("date")
    meta = d.get("game_lines_meta") or {}
    if "slate" not in meta:
        _old += 1
        note("⚠️ %s: this stored card predates the day filter (no "
             "`game_lines_meta.slate`), so it is NOT asserted. The next "
             "card-fb run rewrites it. ⛔ Reported, not passed." % lg)
        continue
    bad = sorted({C.et_date(r.get("commence")) for r in (d.get("game_lines") or [])
                  if C.et_date(r.get("commence")) not in (slate, None)})
    _checked += 1
    ck("🔴 %s: every published game line is on the card's own day (%s)"
       % (lg, slate),
       not bad,
       "⛔ the card's header promises ONE day, and this card was built by "
       "a builder that HAS the filter — so a foreign date here means the "
       "filter stopped working, not that the card is old. Present: %s"
       % bad)
if not (_checked or _old):
    note("⚠️ NOT EXERCISED: no stored football card in this tree, so "
         "section 5 proved nothing. ⛔ Reported rather than passed.")
else:
    note("asserted %d card(s); %d predate the filter and were reported "
         "rather than asserted" % (_checked, _old))

note("⛔ WHAT IS NOT DECIDED HERE: whether the window should be a DAY or "
     "a WEEK. The card says 'only' and names a date, so today the list "
     "must match that. Widening it is a product change that moves the "
     "LABEL too, and it is Sam's to make.")
