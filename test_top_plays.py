#!/usr/bin/env python3
"""
TOP PLAYS OF THE DAY.

Sam: *"top plays of the day, at the bottom of Gizmo's Picks, same
single-day rule, capped at 20."*

🔴 AND THE OWED CHECK FROM THE CHECKLIST, WHICH IS THE POINT OF HALF THIS
FILE. `claude/football-todo.md` says of the confidence item: *"Verify it
holds for Top Plays when that is built."* It is built, so it is verified
here — every row in the list carries a confidence, and every confidence
is labelled RECORD, never MODEL (ledger rule 55).

⛔ THE HONEST FINDING IS ASSERTED, NOT JUST WRITTEN IN A COMMENT. On
football this list is a HIGHLIGHT of the board rather than a second
opinion, because the two things that make MLB's version independent —
alternate ladder rungs, and a price gate that actually bites — do not
exist here. §4 measures that rather than trusting the docstring.
"""
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
FAIL = []


def ck(name, cond, extra=""):
    print(("  ✅ " if cond else "  ❌ ") + name + (("  — " + extra) if extra else ""))
    if not cond:
        FAIL.append(name)
    return cond


def note(s):
    print("  ⚪ " + s)


sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "ncaaf")
import card_fb  # noqa: E402

# ───────────────────────────────────────────────────────────────
print("\n═══ 1. SAM'S NUMBERS, AND THE ONE SHARED WITH card.py ═══")
ck("the cap is 20", card_fb.TOP_N == 20, "TOP_N=%s" % card_fb.TOP_N)

# 🔴 THE RULE 66 CROSS-CHECK. The payable floor is SAM'S number, stated
#    once for the MLB list. Restating it in a second file is the hazard
#    whether or not the two currently agree — the parlay bands are checked
#    the same way, for the same reason.
csrc = open(os.path.join(ROOT, "card.py")).read()
m = re.search(r"^TOP10_PRICE_FLOOR\s*=\s*(-?\d+)", csrc, re.M)
ck("card.py still declares TOP10_PRICE_FLOOR", m is not None)
if m:
    ck("football's payable floor equals MLB's, to the dollar",
       card_fb.TOP_PRICE_FLOOR == int(m.group(1)),
       "football %s vs mlb %s" % (card_fb.TOP_PRICE_FLOOR, m.group(1)))

fsrc = open(os.path.join(ROOT, "card_fb.py")).read()
i_top = fsrc.index("top_plays, top_meta = build_top_plays(")
i_gate = fsrc.index("JOIN TOO WEAK")
i_day = fsrc.index("off_day = [r for r in rows")
i_floor = fsrc.index('below = [r for r in rows if not r["clears_price_floor"]]')
ck("top plays are built AFTER the name gate", i_top > i_gate,
   "a MARKET-only board must not produce a 'most likely to hit' list")
ck("top plays are built AFTER the single-day filter", i_top > i_day)
ck("top plays are built AFTER the price floor", i_top > i_floor)

# ───────────────────────────────────────────────────────────────
print("\n═══ 2. END-TO-END, ON THE REAL BUILDER ═══")


def stage(tmp):
    shutil.copytree(os.path.join(ROOT, "data/ncaaf"), os.path.join(tmp, "data/ncaaf"))
    os.makedirs(os.path.join(tmp, "picks"), exist_ok=True)
    shutil.copy(os.path.join(ROOT, "card_fb.py"), tmp)


def run(tmp, mutate=None):
    stage(tmp)
    p = os.path.join(tmp, "data/ncaaf/latest/props.json.gz")
    if mutate:
        B = json.load(gzip.open(p, "rt"))
        mutate(B)
        with gzip.open(p, "wt") as fh:
            json.dump(B, fh)
    r = subprocess.run([sys.executable, "card_fb.py"], cwd=tmp,
                       env=dict(os.environ, LEAGUE="ncaaf"),
                       capture_output=True, text=True)
    lp = os.path.join(tmp, "picks/fb-ncaaf-latest.json")
    if r.returncode != 0 or not os.path.exists(lp):
        print(r.stdout[-1200:], r.stderr[-1200:])
        return None
    return json.load(open(lp))


tmp = tempfile.mkdtemp()
C = run(tmp)
shutil.rmtree(tmp, ignore_errors=True)

if ck("the builder produces a card", C is not None):
    T = C["top_plays"]
    M = C["top_plays_excluded"]
    ck("there are top plays and no more than the cap",
       0 < len(T) <= card_fb.TOP_N, "%d play(s), cap %d" % (len(T), card_fb.TOP_N))

    # 🔴 THE OWED CHECKLIST ITEM.
    ck("EVERY top play carries a confidence",
       all(x.get("confidence") is not None for x in T),
       "the checklist's owed check, now that the list exists")
    ck("every confidence is labelled RECORD, never MODEL",
       {x.get("confidence_basis") for x in T} == {"RECORD"},
       "ledger rule 55 — football has no MODEL: %s"
       % sorted({x.get("confidence_basis") for x in T}))
    ck("every top play carries a price and a book",
       all(x.get("price") is not None and x.get("book") for x in T))

    ck("one row per player — no repeats",
       len({x["player"] for x in T}) == len(T),
       "%d distinct of %d" % (len({x['player'] for x in T}), len(T)))
    ck("nothing is priced at or worse than the payable floor",
       all(x["price"] > card_fb.TOP_PRICE_FLOOR for x in T),
       "shortest price on the list %+d" % min(x["price"] for x in T))
    ck("the list is in descending confidence order",
       all(T[i]["confidence"] >= T[i + 1]["confidence"] for i in range(len(T) - 1)))

    # ⛔ SINGLE-DAY, INHERITED FROM THE SAME FILTER THE BOARD USES.
    days = sorted({card_fb.et_date(x.get("commence")) for x in T} - {None})
    ck("every top play is on the card's own date",
       days == [C["date"]], "card %s, list %s" % (C["date"], days))

    # ⛔ AND IT MUST BE DRAWN FROM THE BOARD'S OWN POOL, not a wider one.
    ids = {(x["player"], x["market"], x["side"], x["line"]) for x in C["picks"]}
    strays = [x for x in T
              if (x["player"], x["market"], x["side"], x["line"]) not in ids]
    note("%d of %d top plays are also rows on the 50-row board; %d are not "
         "(a row can be top-20 by confidence and still miss a 50-row board "
         "that is itself capped)" % (len(T) - len(strays), len(T), len(strays)))

    ck("the rule sentence carries the measured overlap, not a claim",
       str(M["shared_with_board_head"]) in C["top_plays_rule"]
       and "HIGHLIGHT" in C["top_plays_rule"],
       "%d of %d players shared with the board's head"
       % (M["shared_with_board_head"], M["board_head_size"]))
    note("%d payable rows in the pool, %d game(s) represented, %d repeat "
         "player(s) skipped, %d dropped by the price gate"
         % (M["pool_after_price_gate"], M["distinct_games"],
            M["same_player_already_listed"], M["below_payable_floor"]))

# ───────────────────────────────────────────────────────────────
print("\n═══ 3. A BOARD WITH NO RECORDS PRODUCES NO TOP PLAYS ═══")
# ⛔ Ranking rows that carry no record by PRICE would be ranking by which
#    bet pays worst, while calling it "most likely to hit". The correct
#    output is an empty list with a stated reason.
plays, meta = card_fb.build_top_plays(
    [{"player": "A", "price": -110, "confidence": None, "game_id": "g1"},
     {"player": "B", "price": -120, "confidence": None, "game_id": "g2"}], [])
ck("a MARKET-only board yields an empty list", plays == [],
   "not a price-ranked one")

# 🔴 AND THE WHOLE PATH, END TO END, ON A REAL MARKET-ONLY BOARD.
# ⚠️ The first draft of this check looked for the sentence in the SOURCE
#    and failed on correct code, because an f-string wraps it across two
#    lines — ledger 69/72, the substring-where-a-word-was-meant trap, for
#    the third time in two days. ✅ So it drives the builder instead: every
#    player name in the props is replaced with one that cannot match, the
#    name gate strips every rate, and the OUTPUT is read.
tmp = tempfile.mkdtemp()


def _break_names(B):
    i = 0
    for g in B.get("games", []):
        for pr in g.get("props", []):
            pr["player"] = "Zzz Nomatch %d" % i
            i += 1


MK = run(tmp, mutate=_break_names)
shutil.rmtree(tmp, ignore_errors=True)
if ck("a board whose name join fails still builds", MK is not None):
    ck("that board is MARKET-only",
       {x.get("confidence_basis") for x in MK["picks"]} == {"MARKET"},
       "%d rows" % len(MK["picks"]))
    ck("and it produces NO top plays at all", MK["top_plays"] == [],
       "not a price-ranked list wearing a 'most likely to hit' heading")
    ck("the card says why, and does not blame an empty board",
       "no row on it carries a record" in MK["top_plays_rule"]
       and "Not because the board is empty" in MK["top_plays_rule"],
       MK["top_plays_rule"][:70])

# ⚠️ The cap must hold even when the pool is enormous.
big = [{"player": "P%d" % i, "price": -110, "confidence": 90 - i % 30,
        "game_id": "g%d" % (i % 4)} for i in range(500)]
plays, meta = card_fb.build_top_plays(big, [])
ck("the cap holds on a 500-row pool", len(plays) == card_fb.TOP_N,
   "%d" % len(plays))
ck("dedup holds on a 500-row pool",
   len({x["player"] for x in plays}) == len(plays))

# ───────────────────────────────────────────────────────────────
print("\n═══ 4. THE HONEST FINDING, RE-MEASURED RATHER THAN TRUSTED ═══")
# 🔴 The docstring claims football has no alternate markets and that the
#    -400 gate does not bite. ⛔ A claim in a comment is a claim about the
#    day it was written. This re-measures it, so the day it stops being
#    true the card's own wording gets revisited instead of quietly lying.
B = json.load(gzip.open(os.path.join(ROOT, "data/ncaaf/latest/props.json.gz"), "rt"))
mkts = {p["market"] for g in B.get("games", []) for p in g.get("props", [])}
alts = sorted(m for m in mkts if "alternate" in m)
note("football props markets: %s" % ", ".join(sorted(mkts)))
if alts:
    note("🔴 ALTERNATE MARKETS NOW EXIST (%s) — the card's wording says this "
         "list is a highlight because they do not. REVISIT IT." % ", ".join(alts))
else:
    note("no alternate market in the feed, so the pool cannot be wider than "
         "the board's — the 'highlight, not a second opinion' wording holds")

if C:
    ck("the card's own wording matches what the gate actually did",
       (M["below_payable_floor"] > 0) ==
       ("were dropped by the price gate" in C["top_plays_rule"]),
       "gate dropped %d" % M["below_payable_floor"])

# ───────────────────────────────────────────────────────────────
print("\n═══ 5. THE PAGE PRINTS IT, AND DOES NOT RE-DERIVE IT ═══")
h = open(os.path.join(ROOT, "index.html")).read()
i = h.index("function fbTopPlays(")
j = h.index("\nfunction ", i + 10)
blk = h[i:j]
ck("the page renders top_plays from the card", "C.top_plays" in blk)
ck("and prints the card's own rule sentence", "top_plays_rule" in blk)
ck("the page does NOT re-rank or re-gate",
   ".sort(" not in blk and "-400" not in blk and "confidence >" not in blk,
   "a second copy of the selection rule is a second thing to drift")
ck("it filters to the games the board is showing, by GAME ID",
   "game_id" in blk and "team" not in blk.lower().split("game_id")[0][-200:],
   "ledger rule 54 — never by opponent name")
ck("it uses MLB's own .t10 grid rather than a second component",
   'class="t10"' in blk and '.t10{display:grid' in h)
ck("an empty list renders nothing at all, not an empty panel",
   "if (!all.length) return '';" in blk)
ck("Gizmo's Picks calls it, at the bottom",
   "fbTopPlays(C, kept)" in h
   and h.index("fbTopPlays(C, kept)") > h.index("v.append(wrap, host)"))

# ───────────────────────────────────────────────────────────────
# 🔴 THE FAILURE GATE IS THE LAST THING IN THIS FILE. Rule 97.
print()
if FAIL:
    print("❌ %d FAILED" % len(FAIL))
    for f in FAIL:
        print("   - " + f)
    sys.exit(1)
print("✅ all top-plays tests passed")
