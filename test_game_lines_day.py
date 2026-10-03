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

`[2026-09-28]` §5 asserts a card BUILT here; the live cards are reported.
# @vacuity §5: a freeze that drags the old slate's started lines back into the list
#   file: card_fb.py
#   find: if d and d != _gl_day:
#   with: if False:
#
# @vacuity §5: the shown list holds only the card's own day [Sam, 2026-10-01]
#   file: card_fb.py
#   find: if et_date(p.get("commence")) != slate:
#   with: if False:
#
# @vacuity §5: main keeps the shown list on the card's own day [Sam, 2026-10-01]
#   file: card_fb.py
#   find: gl_meta = {"source": "fb-model.json", "slate": slate, "card_slate": slate,
#   with: gl_meta = {"source": "fb-model.json", "slate": _gl_slate, "card_slate": slate,
"""
import datetime
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
                                    ("hardrockbet", -120))},
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
#
# ══════════════════════════════════════════════════════════════════════
# 🔴 `[2026-09-28]` THE LIVE CARDS ARE NOW REPORTED; A BUILT CARD IS ASSERTED.
# ══════════════════════════════════════════════════════════════════════
# ⛔ THE ASSERTION ABOVE WAS "ANOTHER GUARD IS SILENT ON PRODUCTION DATA".
#    It judged `picks/fb-*-latest.json` — written by whatever builder last
#    ran, not by the code under test — and went red on EVERY collect run
#    from 09-20 (test_card_frozen.py §5 records it), and on a PR it judged
#    that PR's code by a card main's code had built. The production
#    question already has its own monitor: `watchdog.check_card_day_
#    agreement` asks exactly this of the live cards, on every run.
# ✅ SO THE SAME TWO QUESTIONS ARE ASKED OF A CARD BUILT HERE, every run:
#    the next-slate choice, the one-day list, and the freeze onto a card
#    already published with STARTED lines from the slate before — the
#    path that broke on 09-20 — composed the way `card_fb.main` composes
#    them, and `main` is read to prove it still does. Kickoffs are at
#    17:00Z, where the ET and UTC dates agree, so no zone data is needed.
def _foreign_days(d):
    """ET days in a card's game lines that are not the list's own slate."""
    _ls = (d.get("game_lines_meta") or {}).get("slate")
    return sorted({C.et_date(r.get("commence"))
                   for r in (d.get("game_lines") or [])
                   if C.et_date(r.get("commence")) not in (_ls, None)})


def _marks_its_day(d):
    meta = d.get("game_lines_meta") or {}
    return meta.get("slate") == d.get("date") or meta.get("is_next_slate") is True


import tempfile  # noqa: E402
_card_day = "2026-09-19"                                   # a Saturday card
# 🔴 `[Sam, 2026-10-01]` the card SHOWS the game model's picks for ITS OWN day
#    (~~the next slate's price gaps~~), composed the way `card_fb.main` now
#    composes them. ⚠️ The first rebuild after that change still meets cards
#    built the old way: a published list on ANOTHER day, started. It must go
#    to the archive, never back into the list.
_now5 = "2026-09-19T19:00:00Z"
_mp = lambda gid, at: {"game": "Away %s at Home %s" % (gid, gid), "commence": at,
                       "market": "spread", "side": "home", "team": "Home %s" % gid,
                       "book": "FanDuel", "line": {"value": -3.5}, "price": {"value": -110},
                       "model_probability": {"value": 55.0}, "break_even": {"value": 52.4}}
_picks5 = [_mp("fri", "2026-09-18T17:00:00Z"), _mp("sat", "2026-09-19T17:00:00Z"),
           _mp("sat3", "2026-09-19T23:30:00Z"), _mp("thu", "2026-09-24T17:00:00Z")]
_old_rows = C.card_game_lines(_picks5, [], {}, "2026-09-18")    # an old card's other-day list
_pubcard = {"date": _card_day, "game_lines_meta": {"slate": "2026-09-18"}, "game_lines": _old_rows}
_new = {"date": _card_day, "game_lines": C.card_game_lines(_picks5, [], {}, _card_day),
        "game_lines_meta": {"source": "fb-model.json", "slate": _card_day,
                            "card_slate": _card_day, "is_next_slate": False}}
_tmp5 = tempfile.mkdtemp()
try:
    _pub = os.path.join(_tmp5, "fb-ncaaf-latest.json")
    with open(_pub, "w", encoding="utf-8") as fh:
        json.dump(_pubcard, fh)
    _built, _ = C.freeze_published(_new, _pub, _now5, log=lambda *a, **k: None)
finally:
    import shutil  # noqa: E402
    shutil.rmtree(_tmp5, ignore_errors=True)
ck("🔴 a card built here puts every game line on the list's own day, "
   "across a slate change and a freeze",
   bool(_old_rows) and bool(_built.get("game_lines"))
   and not _foreign_days(_built) and _built.get(C.GL_EARLIER),
   "⛔ the list prints ONE date and every row must be on it. slate %s; "
   "foreign days present: %s (published rows %d, built rows %d)"
   % ((_built.get("game_lines_meta") or {}).get("slate"),
      _foreign_days(_built), len(_old_rows), len(_built.get("game_lines") or [])))
ck("⛔ ...and the list's day IS the card's day",
   (_built.get("game_lines_meta") or {}).get("slate") == _card_day
   and _marks_its_day(_built), "meta %s" % (_built.get("game_lines_meta") or {}))
_main = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
_main = _main[_main.index("\ndef main("):]
ck("🔴 ...and `card_fb.main` still composes the list exactly that way",
   "game_lines = card_game_lines(" in _main
   and 'gl_meta = {"source": "fb-model.json", "slate": slate, "card_slate": slate,' in _main
   and "freeze_published(" in _main,
   "⛔ a built card composed differently from main's would prove nothing "
   "about the card main writes")

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
             "`game_lines_meta.slate`). The next card-fb run rewrites it."
             % lg)
        continue
    # ⚠️ CHECKED AGAINST THE LIST'S OWN SLATE, NOT THE CARD'S DATE.
    #    Since 2026-09-14 the game lines deliberately follow the NEXT day
    #    with games (Sam: college plays midweek), so they are ALLOWED to
    #    differ from the card — what is never allowed is the list holding
    #    more than one day, or disagreeing with the label it prints.
    _checked += 1
    bad = _foreign_days(d)
    note("%s live card (DESCRIPTIVE — the watchdog asks this of production): "
         "list day %s, card day %s, foreign days %s, marked %s"
         % (lg, meta.get("slate"), slate, bad or "none",
            _marks_its_day(d)))
if not (_checked or _old):
    note("no stored football card in this tree")


print("\n═══ 6. 🔴🔴 THE LIST FOLLOWS THE NEXT SLATE, NOT THE CARD'S ═══")
# 🔴 `[Sam, 2026-09-14: "for college we should be checking daily for games
#    because cfb has a different schedule than nfl, they may play games on
#    wednesdays, fridays, tuesday"]`
# ⚠️ MEASURED ACROSS THE 2026 SCHEDULE, 1,609 Division I games:
#        Sat 1422 · Fri 82 · Thu 63 · Tue 18 · Wed 15 · Sun 8 · Mon 1
#    **187 games are not on a Saturday.** So anchoring this list to the
#    card's own slate left the tab EMPTY for the four days between slates
#    while live Thursday lines sat in a snapshot already paid for.
# ⛔ AND IT MUST MOVE THE WINDOW, NOT WIDEN IT. Showing Thursday AND
#    Saturday together is the September-20-under-a-September-13-header
#    defect wearing a different date.
_now = datetime.datetime(2026, 9, 14, 18, 0, tzinfo=datetime.timezone.utc)
snap = _snap([("thu", "2026-09-17T23:00:00Z"),
               ("fri", "2026-09-19T00:00:00Z"),
               ("sat", "2026-09-19T17:00:00Z"),
               ("done", "2026-09-12T23:00:00Z")])   # already played
nxt = C.next_line_slate(snap, _now)
ck("🔴 the next slate is the earliest UNSTARTED day",
   nxt == "2026-09-17",
   "⛔ a slate that kicked off is not 'next' — its lines are off the "
   "board. Got %r" % nxt)
rows, meta = C.build_game_lines(snap, n=None, slate=nxt)
_days = sorted({C.et_date(r["commence"]) for r in rows})
ck("🔴 ...and the list is ONE day, not a week of futures",
   _days == ["2026-09-17"],
   "⛔ this is the whole reason the window MOVES instead of widening. "
   "Got %s" % _days)
meta["is_next_slate"] = True
_txt = C.game_lines_rule(rows, meta)
ck("🔴 the list states its OWN date when it differs from the card's",
   "2026-09-17" in _txt and "next day with games" in _txt,
   "⛔ a section on a different day than the header MUST say so, or it "
   "is the contradiction Sam reported, with better arithmetic. Got %r"
   % _txt[:140])
ck("⛔ ...and the sentence names no sport",
   "College" not in _txt and "NFL" not in _txt,
   "⚠️ `game_lines_rule` is SHARED. The first draft said 'College plays "
   "midweek' and printed it on the NFL card — a true fact about the "
   "wrong sport is how a reader learns to skip the copy")
ck("⚠️ a snapshot with nothing left to play has no next slate",
   C.next_line_slate(_snap([("old", "2026-09-12T23:00:00Z")]), _now) is None,
   "and the caller falls back to the card's own slate rather than "
   "inventing a day")

note("✅ DECIDED 2026-09-14, BY SAM: not a week — the NEXT DAY WITH "
     "GAMES, checked daily, because the college calendar has no week to "
     "anchor to. ⛔ The list is still exactly one day; what changed is "
     "WHICH day, and that it carries its own label when it differs from "
     "the card's.")
