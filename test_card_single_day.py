#!/usr/bin/env python3
"""
🔴 THE MLB CARD HOLDS ONLY GAMES ON ITS OWN ET DATE (ledger rule 101).

`[2026-10-01]` 10/01 had ONE game (PHI @ ATL) and the rolling board already
held the next round. `picks/2026-10-01.json` carried 17 of its 29 picks and
2 of its top 10 on 10/03 games, and the watchdog reported day:mlb:picks and
day:mlb:top10 BROKEN. card_fb.py has filtered this since 09-04; card.py
never did. ✅ One filter (`card.on_day`) now runs before the pairs, the top
10, the parlays and the board are built, and the card says what it held back.

THE CASE IS PLANTED, NEVER BORROWED FROM TODAY'S BOARD (rule 67): a
pitcher-props snapshot with three games between six starters from the
stored pull, ONE on the card's day and two on later days, the clock pinned
just after the pull, then the REAL board builder (`collect_props_board`) and
the REAL card (`card.main(dry=True)`) in an isolated tree.
`[2026-11-18, #249]` Every planted game also carries a Hard Rock strikeout ladder, and
the one-side rule's own input is recorded: two of the mutations below had stayed green
since 2026-10-16, when `card.one_side_pools` began masking them (the ladder check
before section 1, and the last check of section 3).
⚠️ The day is judged by the WATCHDOG's ET date (`watchdog._etd`), never by
card.py's own, and every dated list is DISCOVERED (`watchdog._dated_lists`),
so a list added later is covered the day it ships.

⛔ WHAT A PASS DOES NOT CLAIM: that `picks/2026-10-01.json` is right. It is
published and stays as it was; editing a published pick is Sam's call.

# @vacuity ⛔ the card keeps only its own day's rows
#   file: card.py
#   find:     return ([x for x in rows if et_date(x["commence"]) == day],
#   with:     return (list(rows),
#
# @vacuity the top 10 (and the pairs) are built from the filtered pool
#   file: card.py
#   find:     plays_all, _ = on_day(plays_all, today)
#   with:     _ = on_day(plays_all, today)
#
# @vacuity the board's pitcher seats are filled from the filtered rows
#   file: card.py
#   find:     plays, _off_p = on_day(plays, today)
#   with:     _off_p = on_day(plays, today)[1]
#
# @vacuity the card says HOW MANY rows wait for their own day
#   file: card.py
#   find:                      + (f": {len(off_day)} priced row(s) for {', '.join(off_dates)} "
#   with:                      + (f": some priced row(s) for {', '.join(off_dates)} "
#
# @vacuity the card records the held-back count for the page
#   file: card.py
#   find:         "n_off_slate_day": len(off_day),
#   with:         "n_off_slate_day": 0,
#
# @vacuity the card records the rows it priced, which the priced-flag check reads
#   file: card.py
#   find:     LAST_PRICED_ROWS[:] = plays_all + hitters + _late
#   with:     LAST_PRICED_ROWS[:] = []
#
# @vacuity 🔴 [Sam, 2026-10-16] the card keeps the game model it built its game lines from
#   file: card.py
#   find:         LAST_GAME_MODEL.update(_gmod or {})
#   with:         LAST_GAME_MODEL.update({})
#
# @vacuity 🔴 [Sam, 2026-11-18] the card main() builds carries the why stamp
#   file: card.py
#   find:         "why_rule": WHY_RULE,
#   with:         "why_rule": None,
#
# @vacuity 🔴 [Sam, 2026-11-18] ...and no why on it says "not part of the model's math"
#   file: card.py
#   find: f"and <b>{same} of {r['n']}</b> landed on this side of {line}.")
#   with: f"and <b>{same} of {r['n']}</b> landed on this side of {line}. That's recent history, not part of the model's math.")
#
# @vacuity 🔴 [2026-11-19] the card main() builds carries the own-number stamp
#   file: card.py
#   find:         "own_number_rule": OWN_NUMBER_RULE,
#   with:         "own_number_rule": None,
#
# @vacuity 🔴 [2026-11-19] ...and no sentence on it says a price made a number no price made
#   file: card.py
#   find:                  f"just to break even. We make it <b>{(blend if shown is None else shown):.0f}%</b>."
#   with:                  f"just to break even. We make it <b>{(blend if shown is None else shown):.0f}%</b>, checked against the price."
"""
import datetime
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, copy_latest, copy_module, note, section, shown  # noqa: E402

import collect as CM  # noqa: E402
import watchdog as W  # noqa: E402

TMP = tempfile.mkdtemp(prefix="single-day-")

DRIVER = r"""
import datetime as _d, contextlib, gzip, io, json, os, sys
root = os.path.dirname(os.path.abspath(__file__)); os.chdir(root); sys.path.insert(0, root)
FIX = _d.datetime.strptime(sys.argv[2], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_d.timezone.utc)
import collect, card
collect.now = lambda: FIX
class _DT(_d.datetime):
    @classmethod
    def now(cls, tz=None):
        return FIX if tz else FIX.replace(tzinfo=None)
card.datetime = _DT
# `[2026-11-18, #249]` what the one-side rule was handed, and what it dropped, by first pitch.
#    The REAL rule runs; this only records. (Its pools decide every list after it, so an
#    off-day row reaching it is the defect even when it happens to leave no list.)
_osp, ONE_SIDE = card.one_side_pools, []
def _one_side_seen(plays, plays_all, hitters):
    out = _osp(plays, plays_all, hitters)
    ONE_SIDE.append({"plays": [x.get("commence") for x in plays],
                     "plays_all": [x.get("commence") for x in plays_all],
                     "hitters": [x.get("commence") for x in hitters],
                     "dropped": [x.get("commence") for x in out[3]]})
    return out
card.one_side_pools = _one_side_seen
with contextlib.redirect_stdout(io.StringIO()):
    collect.collect_props_board()
    doc = card.main(dry=True)
board = json.load(gzip.open("data/latest/props.json.gz", "rt"))
priced = [{k: r.get(k) for k in ("pid", "market", "side", "line", "projection")}
          for r in card.LAST_PRICED_ROWS]
json.dump({"board": board, "card": doc, "priced": priced,
           "game_model": card.LAST_GAME_MODEL, "one_side": ONE_SIDE}, open(sys.argv[1], "w"),
          sort_keys=True)
"""


def _mkt(key, who, line, over, under):
    return {"key": key, "outcomes": [
        {"name": "Over", "description": who, "point": line, "price": over},
        {"name": "Under", "description": who, "point": line, "price": under}]}


# ── THE PLANTED TREE ──────────────────────────────────────────────────
tree = os.path.join(TMP, "tree")
os.makedirs(os.path.join(tree, "data"))
copy_module("card", tree)
copy_latest(os.path.join(ROOT, "data", "latest"), os.path.join(tree, "data", "latest"))
# 🔴 `[2026-10-18]` THE PULL IS PINNED: the complete 2026 season, as pulled 2026-10-17
#    (`research/mlb_pitchers_20261017.json.gz`, written once). ~~The live pull~~ is
#    rewritten for `now().year`: the first 2027 pull lands once ONE pitcher passes 20 IP
#    (mid-April), when fewer than six teams have a five-start model arm, so the draw
#    below came up short and this file died on an IndexError on correct code.
PINNED_PULL = os.path.join(ROOT, "research", "mlb_pitchers_20261017.json.gz")
shutil.copy(PINNED_PULL, os.path.join(tree, "data", "latest", "pitchers.json.gz"))
open(os.path.join(tree, "driver.py"), "w").write(DRIVER)
PD = json.load(gzip.open(os.path.join(tree, "data", "latest", "pitchers.json.gz"), "rt"))

# Six starters from six different teams, each name unique in the model pool
# (the same draw as test_mlb_tables (c1), so `resolve()` never refuses one).
mp = CM.model_pitchers(PD["players"])
names = {}
for v in mp.values():
    names[CM.norm_name(v["name"])] = names.get(CM.norm_name(v["name"]), 0) + 1
by_team = {}
for _pid, v in sorted(mp.items(), key=lambda kv: (-sum(1 for r in kv[1].get("g") or []
                                                      if r.get("gs")), kv[0])):
    starts = sum(1 for r in v.get("g") or [] if r.get("gs"))
    if (starts >= 5 and v.get("team") and v["team"] not in by_team
            and names[CM.norm_name(v["name"])] == 1):
        by_team[v["team"]] = v
six = list(by_team.values())[:6]
ck(len(six) == 6,
   "⚠️ six starters from six different teams, each name unique in the model pool, "
   "drawn from the pinned pull", "⛔ rule 67: got %d" % len(six))
if len(six) < 6:
    raise SystemExit(1)

pull_at = datetime.datetime.strptime(PD["pulled_at"], "%Y-%m-%dT%H:%M:%SZ")
FIX = (pull_at + datetime.timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
# 🔴 ONE game on the card's day, the next round two and three days later --
#    the 10/01 shape: a thin day with the board already rolled forward.
KO = [(pull_at + datetime.timedelta(days=d)).strftime("%Y-%m-%dT23:05:00Z")
      for d in (1, 3, 4)]
DAY = W._etd(KO[0])
events = []
for gi in range(3):
    aw, hm = six[2 * gi], six[2 * gi + 1]
    events.append({"id": "planted-%d" % gi, "commence_time": KO[gi],
                   "away_team": aw["team"], "home_team": hm["team"],
                   "bookmakers": [
                       {"key": bk, "markets": [
                           m for q in (aw, hm) for m in (
                               _mkt("pitcher_strikeouts", q["name"], 5.5, -115 + dx, -105 - dx),
                               _mkt("pitcher_outs", q["name"], 16.5, -110 + dx, -110 - dx))]}
                       for bk, dx in (("draftkings", 0), ("fanduel", 5))]
                      # 🔴 `[2026-11-18, #249]` A HARD ROCK STRIKEOUT LADDER ON EVERY GAME, the
                      #    card's day and the later ones. Without one the board held no alt rung,
                      #    and `card.one_side_pools` keeps a `plays_all` row only when it is an
                      #    alt rung or already in `plays` (filtered to the day), so an unfiltered
                      #    `plays_all` changed nothing here and the second mutation above stayed
                      #    green (nightly 11-02 -> 11-18). A real board carries Hard Rock's
                      #    ladder (collect.py: `ALT_MARKETS`, hardrockbet / hardrockbet_oh only).
                      + [{"key": "hardrockbet", "markets": [
                          {"key": "pitcher_strikeouts_alternate", "outcomes": [
                              {"name": "Over", "description": q["name"], "point": pt, "price": px}
                              for q in (aw, hm) for pt, px in ((3.5, -250), (4.5, -150))]}]}]})
snap = os.path.join(tree, "data", FIX[:10], "props-pitcher")
os.makedirs(snap)
with gzip.open(os.path.join(snap, FIX[11:13] + FIX[14:16] + ".json.gz"), "wt") as fh:
    json.dump({"pulled_at": FIX, "n_events": len(events), "events": events}, fh)

out = os.path.join(TMP, "out.json")
p = subprocess.run([sys.executable, "-B", "driver.py", out, FIX], cwd=tree,
                   capture_output=True, text=True, timeout=600,
                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
if p.returncode:
    print(shown(p.stdout[-2000:]), shown(p.stderr[-2000:]))
res = json.load(open(out, encoding="utf-8")) if not p.returncode else {}
B, C = res.get("board") or {}, res.get("card") or {}
TODAY_GAMES = {g["id"] for g in B.get("games") or [] if W._etd(g.get("commence")) == DAY}
LATER = sorted({W._etd(g.get("commence")) for g in B.get("games") or []} - {DAY})
note("planted: %d game(s) on %s %s, later days %s; card dated %s, %d picks, %d top 10"
     % (len(TODAY_GAMES), DAY, sorted(TODAY_GAMES), LATER, C.get("date"),
        len(C.get("picks") or []), len(C.get("top10") or [])))
note("the board holds %d game(s); the case needs one on the card's day and "
     "rows on later days, or the checks below pass blind" % len(B.get("games") or []))
# ⚠️ rule 67: an off-day ALT RUNG is the only row an unfiltered `plays_all` can carry
#    onto the card, so a board with no ladder would pass the top-10 check blind.
ck("⚠️ the planted board carries a Hard Rock ladder on every game, the card's day and the later ones",
   len(B.get("games") or []) == 3 and all(g.get("ladders") for g in B.get("games") or []),
   str([sorted(g.get("ladders") or {}) for g in B.get("games") or []]))


def on_card_day(rows):
    """Every row's game is today's one game, on the card's own ET date."""
    return all(r.get("game_id") in TODAY_GAMES and W._etd(r.get("commence")) == DAY
               for r in rows)


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 A ONE-GAME DAY: THE CARD CARRIES ONLY THAT GAME'S ROWS")
picks = C.get("picks") or []
ck("🔴 every pick is the one game on the card's day, and there are picks",
   C.get("date") == DAY and len(TODAY_GAMES) == 1 and len(LATER) == 2
   and picks and on_card_day(picks),
   "date %s, %d picks on %s"
   % (C.get("date"), len(picks),
      sorted({(r.get("game_id"), W._etd(r.get("commence"))) for r in picks})))

section("2. 🔴 THE TOP 10 LIKEWISE")
t10 = C.get("top10") or []
ck("🔴 every top-10 row is the one game on the card's day, and there is a top 10",
   C.get("date") == DAY and t10 and on_card_day(t10),
   "%d rows on %s" % (len(t10), sorted({W._etd(r.get("commence")) for r in t10})))
# ⚠️ NO PAIR OR PARLAY CHECK HERE, ON PURPOSE: this planted board builds none
#    with or without the filter (no planted leg beats its price), so a check
#    on them could not fail. They are built from the same filtered pool as
#    the top 10, and the second mutation above proves that pool is filtered.
note("pairs %d, parlays %s (none either way on this board)"
     % (len(C.get("pairs") or []), {k: len(v) for k, v in (C.get("parlays") or {}).items()}))

section("3. 🔴 EVERY DATED LIST, DISCOVERED -- NOT JUST THE TWO THAT BROKE")
lists = W._dated_lists(C)
leak = {k: sorted({W._etd(r.get("commence")) for r in v
                   if isinstance(r, dict) and W._etd(r.get("commence")) != DAY})
        for k, v in lists.items()}
leak = {k: v for k, v in leak.items() if v}
ck("🔴 no list on the card carries a row from another day",
   C.get("date") == DAY and "picks" in lists and not leak,
   "lists %s; off-day rows in %s" % (sorted(lists), leak))

# 🔴 `[2026-11-18, #249]` AND THE FILTER RUNS BEFORE THE ONE-SIDE RULE, ON EVERY POOL.
#    `card.one_side_pools` (2026-10-16) keeps a board row only when the day-filtered
#    `plays_all` holds it, so an unfiltered `plays` reaches no list: the third mutation
#    above left every published field the same and stayed green (nightly 11-02 -> 11-18).
#    What it did change was the rule's own work: it judged the later days' rows too and
#    reported them dropped. So the rule's input and output are asked, not only the card.
_os = res.get("one_side") or []
_os_days = {k: sorted({W._etd(c) for c in v}) for k, v in (_os[0] if _os else {}).items()}
ck("🔴 the one-side rule is handed only the card's day, every pool, and drops only the day's rows",
   len(_os) == 1 and _os[0].get("plays") and _os[0].get("plays_all")
   and all(set(v) <= {DAY} for v in _os_days.values()),
   "%d call(s); days per pool %s; %d dropped" % (
       len(_os), _os_days, len((_os[0] if _os else {}).get("dropped") or [])))

section("4. ✅ A THIN DAY SAYS SO")
n_off = C.get("n_off_slate_day")
ck("the card records how many priced rows wait for their own day, and which days",
   isinstance(n_off, int) and n_off > 0 and C.get("off_slate_dates") == LATER
   and C.get("single_day") is True and C.get("slate_date") == DAY,
   "n_off_slate_day=%r off_slate_dates=%r" % (n_off, C.get("off_slate_dates")))
cov = C.get("coverage") or ""
ck("...and the coverage line the page prints says it, with the number",
   ("This card is %s only" % DAY) in cov
   and ("%s priced row(s) for %s" % (n_off, ", ".join(LATER))) in cov,
   shown(cov[-260:]))

section("5. 🔴 AN ALL-PRICED BOARD PASSES verify_card's PRICED-FLAG CHECK")
# `[2026-10-01]` this planted board is the 20:11Z shape: every game still
# to start, every prop priced. verify_card.py's own lines (as in
# test_priced_flag.py) run on the REAL card and the rows card.main() says
# it priced -- so the builder's half of the contract is driven too.
_VS = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
_A, _B = "_MKT_FEED = {", 'ck("the price gate actually excluded something'
_got = {}
if _A in _VS and _B in _VS:
    exec(compile(_VS[_VS.index(_A):_VS.index(_B)], "verify_card.py#priced-flag", "exec"),
         {"doc": C, "_t10": C.get("top10") or [],
          "allrows": (C.get("picks") or []) + (C.get("below_price_floor") or []),
          "print": lambda *a, **k: None,
          "ck": lambda name, ok, detail="": _got.__setitem__(name.split(" (")[0], bool(ok)),
          "C": __import__("types").SimpleNamespace(LAST_PRICED_ROWS=res.get("priced") or [])})
_px = C.get("projections") or {}
note("planted card: %d of %d projection entries flagged priced"
     % (sum(1 for v in _px.values() if v.get("p")), len(_px)))
ck("🔴 the flag sits on exactly the rows the real card priced, on an all-priced board",
   _got.get("the priced flag sits on exactly the rows the card priced") is True
   and _px and all(v.get("p") for v in _px.values()), str(_got))
# `[Sam, 2026-10-16]` ONE TEAM PER GAME: verify_card.py judges the card's game lines against the
#    game model main() built them from (a dry run never writes mlb-game-model.json).
_gmk = res.get("game_model") or {}
ck("🔴 the REAL card keeps, in memory, the game model it built its game lines from (verify_card's input "
   "for one team per game)",
   "games" in _gmk and _gmk.get("slate") == (C.get("game_lines_meta") or {}).get("slate"),
   str(sorted(_gmk)[:8]))

section("6. 🔴 [Sam, 2026-11-18] THE REAL CARD IS STAMPED, AND NO WHY ON IT CARRIES A CAVEAT")
# "Drop them like football": "The 'One thing to know' line and the 'not part of the model's math'
#    endings go." This is the REAL card.main() on the planted board, so its pitcher whys carry the
#    opponent's recent starter log, the sentence the "not part of the model's math" ending sat on.
#    The hitter and outs branches are planted in test_plain_why.py (this board seats strikeouts
#    rows only).
import card as _K  # noqa: E402  the stamp and the one guard verify_card.py runs
_ow = [w for r in picks for w in r.get("why") or [] if "on this side of" in w]
ck("⚠️ rule 67: every pick on the real card carries the opponent-log sentence",
   picks and len(_ow) == len(picks) and all(r.get("opp_recent") for r in picks),
   "%d opponent-log sentence(s) on %d picks" % (len(_ow), len(picks)))
ck("🔴 the card main() built carries the why stamp, and no why on it carries a caveat phrase",
   C.get("why_rule") == _K.WHY_RULE and _K.why_caveats(C) == [],
   "why_rule %r, caveats %s" % (C.get("why_rule"), (_K.why_caveats(C) or [])[:3]))

section("7. 🔴 [2026-11-19] THE REAL CARD CARRIES THE OWN-NUMBER STAMP, AND NO SENTENCE ON IT SAYS A "
        "PRICE MADE A NUMBER NO PRICE MADE")
# Sam, 2026-10-11: "BASED ON THE MODELS CONFIDENCE SCORE NOT THE SPORTSBOOKS". Every pick here prints
#    its break-even sentence (the price may say what it needs); the corrected branches (C1, C2) are
#    planted in test_price_words.py (this tree holds no graded record, so no mapping is fitted).
_be = [r for r in picks if any("just to break even" in w for w in r.get("why") or [])]
ck("⚠️ rule 67: every pick on the real card carries its break-even sentence",
   picks and len(_be) == len(picks), "%d of %d" % (len(_be), len(picks)))
ck("🔴 the card main() built carries the own-number stamp, and no sentence on it says a price made "
   "a number whose method reads none",
   C.get("own_number_rule") == _K.OWN_NUMBER_RULE and _K.price_claims(C) == [],
   "own_number_rule %r, claims %s" % (C.get("own_number_rule"), (_K.price_claims(C) or [])[:3]))
