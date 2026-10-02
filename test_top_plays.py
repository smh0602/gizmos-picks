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

`[2026-09-28]` Every mutation below is caught by the PLANTED board (§2b),
whatever the live college board holds that day:

# @vacuity a top play labelled MODEL is caught on the planted card
#   file: card_fb.py
#   find: out.append(x)
#   with: out.append(dict(x, confidence_basis="MODEL"))
#
# @vacuity a top play with no book is caught on the planted card
#   file: card_fb.py
#   find: out.append(x)
#   with: out.append({k: v for k, v in x.items() if k != "book"})
#
# @vacuity the -400 payable floor is enforced on the planted card
#   file: card_fb.py
#   find: if x["price"] <= TOP_PRICE_FLOOR:
#   with: if False:
#
# @vacuity the payable floor drops the row AT -400, not only below it
#   file: card_fb.py
#   find: if x["price"] <= TOP_PRICE_FLOOR:
#   with: if x["price"] < TOP_PRICE_FLOOR:
#
# @vacuity build_top_plays sorts its own pool (the caller's sort hides it end to end)
#   file: card_fb.py
#   find: pool.sort(key=lambda x: -x["confidence"])
#   with: pass
#
# @vacuity the next day's game never reaches the planted card's top plays
#   file: card_fb.py
#   find: rows = [r for r in rows if et_date(r.get("commence")) in (slate, None)]
#   with: rows = list(rows)
#
# @vacuity "held back" is printed only when a row WAS held back
#   file: card_fb.py
#   find: if top_meta["same_game_already_listed"] else
#   with: if True else
#
# @vacuity "held back" is printed whenever a row was held back
#   file: card_fb.py
#   find: if top_meta["same_game_already_listed"] else
#   with: if False else
#
# @vacuity a name join under its gate strips the rate from the player who matched
#   file: card_fb.py
#   find: r.pop("confidence", None)
#   with: pass
#
# @vacuity a MARKET-only board keeps its rows (and its "rows are priced" sentence)
#   file: card_fb.py
#   find: board = rows[:BOARD_MAX] if rated else fill_board(rows, BOARD_MAX)
#   with: board = rows[:BOARD_MAX] if rated else []
#
# @vacuity [Sam, 2026-10-01] the page no longer prints the top plays' rule sentence
#   file: index.html
#   find: <h2>Top ${t.length} play${t.length === 1 ? '' : 's'} of the day</h2>
#   with: <h2>Top ${t.length} play${t.length === 1 ? '' : 's'} of the day</h2><p>${C.top_plays_rule || ''}</p>
#
# @vacuity [Sam, 2026-10-01] the top plays carry no explanation box
#   file: index.html
#   find: <div class="p">${sgn(x.price)}</div>`).join('')}</div></div>`;
#   with: <div class="p">${sgn(x.price)}</div>`).join('')}</div><div class="note">Every number here is the player's own record.</div></div>`;
"""
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from tcheck import ck, note, copy_module, shown  # ⚠️ copies the SUBJECT'S OWN IMPORTS too — a hand-listed
#                                 fixture went red on all four harnesses at once
#                                 the day card_fb.py gained one import

ROOT = os.path.dirname(os.path.abspath(__file__))
FAIL = []


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
    # @vacuity the isolated tree must carry the subject's OWN imports
    #   file: tcheck.py
    #   find: if os.path.exists(os.path.join(root, cand)):
    #   with: if False:
    # ⚠️ DECLARED HERE AND NOT IN ALL FOUR: the mutation is one edit to
    #    `tcheck.py` and this is the fastest of the harnesses that would
    #    catch it. `[the class the guard protects: a fixture that
    #    hand-lists its subject's dependencies — 2026-09-16, four of them
    #    went red in one commit]`
    copy_module("card_fb", tmp)


def build(tmp):
    """Run the REAL card_fb.py in `tmp` and read the card it writes."""
    r = subprocess.run([sys.executable, "card_fb.py"], cwd=tmp,
                       env=dict(os.environ, LEAGUE="ncaaf"),
                       capture_output=True, text=True)
    lp = os.path.join(tmp, "picks/fb-ncaaf-latest.json")
    if r.returncode != 0 or not os.path.exists(lp):
        print(shown(r.stdout[-1200:]), shown(r.stderr[-1200:]))
        return None
    return json.load(open(lp))


def run(tmp, mutate=None):
    stage(tmp)
    p = os.path.join(tmp, "data/ncaaf/latest/props.json.gz")
    if mutate:
        B = json.load(gzip.open(p, "rt"))
        mutate(B)
        with gzip.open(p, "wt") as fh:
            json.dump(B, fh)
    return build(tmp)


# ══════════════════════════════════════════════════════════════════════
# 🔴 THE PLANTED BOARD. `[2026-09-28]` Every end-to-end check in this file
#    used to read a copy of the LIVE college props board, so which of them
#    tested anything depended on the day: on 2026-09-10 the board held 0
#    games and every top-play check passed over an empty list (rule 67 —
#    pattern P3, a guard that waits for live data to show its case).
# ✅ So each question is now ALSO asked of a board this file writes, the
#    way e4b04844 (#156) planted the dossier's cases: fixed kickoffs, fixed
#    logs, a known answer. The live run stays as an extra that is asserted
#    when it holds the case and REPORTED when it does not.
# ⚠️ Kickoffs are 17:00Z, so the ET date and the UTC date agree even where
#    `card_fb.et()` falls back to UTC (a machine without tzdata).
# ══════════════════════════════════════════════════════════════════════
PLANT_DAY, PLANT_NEXT = "2026-09-12T17:00:00Z", "2026-09-13T17:00:00Z"
# name -> games (of 10) over 40.5 receiving yards. One position each, so
# every position pool is under PRIOR_MIN and the prior is exactly 0.5:
# confidence = round(100 * (hits + 6) / 22)  ->  10: 73, 9: 68, 8: 64, 7: 59
PLANT_HITS = {"Alpha One": 10, "Alpha Two": 9, "Bravo One": 10,
              "Bravo Two": 8, "Charlie One": 9, "Delta One": 7, "Echo One": 10}


def _pg(yds):
    return {"rec": 3, "rec_yds": yds, "car": 0, "rush_yds": 0, "rec_td": 0,
            "rush_td": 0, "pass_yds": 0, "pass_td": 0, "att": 0,
            "team": "T", "game_id": "x", "d": "2025-10-01"}


def _pprop(who, price, market="player_reception_yds", line=40.5):
    return {"player": who, "market": market, "line": line,
            "sides": {"over": {"price": price, "book": "fanduel",
                               "n_books": 3, "link": "x"}}}


def planted_board(one_per_game=False):
    """Four games on the slate day and one on the next.

    g1  Alpha One 73 (plus a second, weaker market) and Alpha Two 68
        -> Alpha Two is HELD BACK for a repeat game, Alpha One's second
           row for a repeat PLAYER.
    g2  Bravo One 73 at -450 (clears the -700 board floor, NOT the -400
        payable floor) and Bravo Two 64 -> Bravo Two is g2's play.
    g3  Charlie One 68.   g4  Delta One 59 at +120.
    g5  Echo One 73 on the NEXT day -> never on this card.
    """
    g1 = [_pprop("Alpha One", -110)]
    if not one_per_game:
        g1 += [_pprop("Alpha One", -110, "player_receptions", 3.5),
               _pprop("Alpha Two", -110)]
    g2 = ([_pprop("Bravo One", -450)] if not one_per_game else []) \
        + [_pprop("Bravo Two", -120)]
    games = [("g1", PLANT_DAY, g1), ("g2", PLANT_DAY, g2),
             ("g3", PLANT_DAY, [_pprop("Charlie One", -105)]),
             ("g4", PLANT_DAY, [_pprop("Delta One", 120)]),
             ("g5", PLANT_NEXT, [_pprop("Echo One", -110)])]
    return {"pulled_at": "2026-09-11T22:31:00Z", "n_games": len(games),
            "books_seen": ["fanduel"],
            "games": [{"id": i, "away": "A%s" % i, "home": "H%s" % i,
                       "commence": c, "props": pr} for i, c, pr in games]}


def planted_logs():
    return {"season": 2025, "scope": "all FBS conferences",
            "players": {str(k): {"name": who, "pos": "P%d" % k,
                                 "g": [_pg(60 if j < h else 20) for j in range(10)]}
                        for k, (who, h) in enumerate(sorted(PLANT_HITS.items()))}}


def run_planted(board):
    """card_fb.py over a tree holding ONLY the planted board and logs."""
    t = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(t, "data/ncaaf/latest"))
        os.makedirs(os.path.join(t, "picks"))
        with gzip.open(os.path.join(t, "data/ncaaf/latest/props.json.gz"), "wt") as fh:
            json.dump(board, fh)
        with gzip.open(os.path.join(t, "data/ncaaf/latest/players-2025.json.gz"), "wt") as fh:
            json.dump(planted_logs(), fh)
        copy_module("card_fb", t)
        return build(t)
    finally:
        shutil.rmtree(t, ignore_errors=True)


def rename_all_but(keep):
    def _m(B):
        i = 0
        for g in B.get("games", []):
            for pr in g.get("props", []):
                if pr["player"] != keep:
                    pr["player"] = "Zzz Nomatch %d" % i
                    i += 1
        return B
    return _m


tmp = tempfile.mkdtemp()
C = run(tmp)
shutil.rmtree(tmp, ignore_errors=True)

if ck("the builder produces a card", C is not None):
    T = C["top_plays"]
    M = C["top_plays_excluded"]
    # 🔴 THE CAP IS THE RULE. "THERE ARE TOP PLAYS" IS A DEMAND THAT DATA
    #    EXIST. `[2026-09-10]` this read `0 < len(T) <= TOP_N` and went
    #    red on a Thursday college card with **nothing priced at all** —
    #    `n_priced: 0`. An empty list is the CORRECT output of an empty
    #    pool, and section 3 of this same file asserts exactly that for a
    #    board with no records. ⛔ So the emptiness is REPORTED, never
    #    passed over silently, and the cap is still enforced.
    ck("the top-play list never exceeds the cap",
       len(T) <= card_fb.TOP_N,
       "%d play(s), cap %d" % (len(T), card_fb.TOP_N))
    if not T:
        # ⛔ NO LONGER A SET OF CHECKS PASSING OVER AN EMPTY LIST. Every
        #    question below is asked of the PLANTED card in §2b every run;
        #    on the live card it is asked when the live card lists plays.
        note("⚠️ NOT EXERCISED ON THE LIVE CARD: it lists 0 top plays. "
             "n_priced=%s — an empty pool yields an empty list by design. "
             "The planted card in §2b asks every one of these questions. "
             "Not a pass." % C.get("n_priced"))
    else:
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

    # 🔴 ONE PLAY PER GAME. `[Sam's decision, 2026-09-06]` The list was
    # measured at 18 of 20 players shared with the board's own first rows
    # — very nearly a second copy of it — and he chose to force it apart.
    # ⛔ THIS IS THE CHECK THAT MAKES IT A DIFFERENT LIST rather than a
    # relabelled one.
    gids = [x.get("game_id") for x in T]
    if T:
        ck("ONE PLAY PER GAME — no game appears twice",
           len(set(gids)) == len(gids),
           "%d distinct game(s) across %d play(s)" % (len(set(gids)), len(gids)))
    ck("the card declares the one-per-game rule for the page to read",
       M.get("one_per_game") is True)
    ck("rows held back for a repeat GAME are counted separately from a "
       "repeat PLAYER",
       "same_game_already_listed" in M and "same_player_already_listed" in M,
       "%s by game, %s by player — different facts, different counts"
       % (M["same_game_already_listed"], M["same_player_already_listed"]))
    if T:
        # ⚠️ AND THE COST IS ASSERTED, NOT GLOSSED. One per game means the
        # cap is a ceiling the slate rarely reaches; a list still pinned at
        # 20 would mean the rule is not biting.
        ck("nothing is padded back up to the cap",
           len(T) <= min(card_fb.TOP_N, len(set(gids))),
           "%d play(s) from %d game(s), cap %d"
           % (len(T), len(set(gids)), card_fb.TOP_N))
        ck("nothing is priced at or worse than the payable floor",
           all(x["price"] > card_fb.TOP_PRICE_FLOOR for x in T),
           "shortest price on the list %+d" % min(x["price"] for x in T))
        ck("the list is in descending confidence order",
           all(T[i]["confidence"] >= T[i + 1]["confidence"] for i in range(len(T) - 1)))

        # ⛔ SINGLE-DAY, INHERITED FROM THE SAME FILTER THE BOARD USES.
        days = sorted({card_fb.et_date(x.get("commence")) for x in T} - {None})
        _off = [d for d in days if d != C["date"]]
        ck("every top play is on the card's own date",
           not _off, "card %s, list %s, OFF-DATE %s" % (C["date"], days, _off))

    # ⛔ AND IT MUST BE DRAWN FROM THE BOARD'S OWN POOL, not a wider one.
    ids = {(x["player"], x["market"], x["side"], x["line"]) for x in C["picks"]}
    strays = [x for x in T
              if (x["player"], x["market"], x["side"], x["line"]) not in ids]
    note("%d of %d top plays are also rows on the 50-row board; %d are not "
         "(a row can be top-20 by confidence and still miss a 50-row board "
         "that is itself capped)" % (len(T) - len(strays), len(T), len(strays)))

    # ⚠️ THE SENTENCE MUST CARRY THE *CURRENT* OVERLAP, NOT THE ONE THAT
    # PROMPTED THE CHANGE. A rule that quotes the number it was built to
    # fix, forever, is a rule describing a version that no longer exists.
    # 🔴 AND WHEN THE LIST IS EMPTY THE SENTENCE MUST GIVE THE RIGHT
    #    REASON. `[2026-09-10]` the card printed "⛔ Not because the board
    #    is empty" on a board that held **zero priced rows** — the reader
    #    was told rows existed and were all rejected. Both branches are
    #    checked here, so neither can go wrong silently.
    # ⚠️ Each branch runs only when the LIVE card is in that state; all
    #    three are also driven on planted boards in §2b, every run.
    if T:
        # ⛔ ~~str(shared) in rule~~ TIGHTENED 2026-09-28: the sentence always
        #    carries "18 of 20", "2026-09-06" and "-400", so a bare number
        #    such as 0, 1, 2, 4, 6, 8, 9, 18 or 20 matched whatever it said.
        ck("the rule sentence carries the measured overlap, not a claim",
           ("It is now %d of %d, over %d game(s)"
            % (M["shared_with_board_head"], M["board_head_size"],
               M["distinct_games"])) in C["top_plays_rule"]
           and "ONE PLAY PER GAME" in C["top_plays_rule"],
           "%d of %d players shared with the board's head"
           % (M["shared_with_board_head"], M["board_head_size"]))
    elif not C["picks"]:
        ck("🔴 an EMPTY board is not blamed on 'no row carries a record'",
           "Nothing is priced for this day yet" in C["top_plays_rule"]
           and "Not because the board is empty"
               not in C["top_plays_rule"],
           C["top_plays_rule"][:110])
    else:
        ck("a board with rows but no records says exactly that",
           "Not because the board is empty" in C["top_plays_rule"]
           and "none carries a record" in C["top_plays_rule"],
           C["top_plays_rule"][:110])
    note("%d payable rows in the pool, %d game(s) represented, %d repeat "
         "player(s) skipped, %d dropped by the price gate"
         % (M["pool_after_price_gate"], M["distinct_games"],
            M["same_player_already_listed"], M["below_payable_floor"]))

# ───────────────────────────────────────────────────────────────
print("\n═══ 2b. 🔴 THE SAME QUESTIONS, ON A PLANTED BOARD — EVERY RUN ═══")
# ⛔ NOT A COPY OF THE LIVE DATA AND NOT WAITING FOR IT. The board above is
#    `planted_board()`: its answer is known before the builder runs, so each
#    check below has its case on every day of the year, off-season included.
PC = run_planted(planted_board())
if ck("🔴 the builder produces a card from the planted board", PC is not None):
    PT, PM = PC["top_plays"], PC["top_plays_excluded"]
    # ⚠️ THE CASE EXISTS FIRST (rule 67): exactly the four plays the board
    #    was built to give, one per slate game, in this order.
    ck("🔴🔴 the planted card lists exactly its four plays, best first",
       [x["player"] for x in PT] == ["Alpha One", "Charlie One", "Bravo Two", "Delta One"],
       "got %s" % [(x["player"], x.get("confidence"), x.get("price")) for x in PT])
    ck("🔴 EVERY planted top play carries a confidence, labelled RECORD",
       bool(PT) and all(x.get("confidence") is not None for x in PT)
       and {x.get("confidence_basis") for x in PT} == {"RECORD"},
       "ledger rule 55 — football has no MODEL: %s"
       % sorted({x.get("confidence_basis") for x in PT}))
    ck("🔴 ...and a price and a book",
       bool(PT) and all(x.get("price") is not None and x.get("book") for x in PT))
    ck("🔴 one per player and ONE PER GAME",
       bool(PT) and len({x["player"] for x in PT}) == len(PT)
       and len({x["game_id"] for x in PT}) == len(PT),
       "%s" % [(x["player"], x["game_id"]) for x in PT])
    ck("🔴 the -450 row (the best in its game) is NOT listed: payable floor",
       bool(PT) and all(x["price"] > card_fb.TOP_PRICE_FLOOR for x in PT)
       and "Bravo One" not in {x["player"] for x in PT},
       "⛔ it clears the -700 board floor and must still miss the -400 "
       "payable one. got %s" % [(x["player"], x["price"]) for x in PT])
    ck("🔴 descending confidence order",
       len(PT) >= 2
       and all(PT[i]["confidence"] >= PT[i + 1]["confidence"] for i in range(len(PT) - 1)),
       "%s" % [x.get("confidence") for x in PT])
    ck("🔴 the next day's game never reaches the card's own list",
       bool(PT) and PC.get("date") == "2026-09-12"
       and all(card_fb.et_date(x.get("commence")) == "2026-09-12" for x in PT)
       and "Echo One" not in {x["player"] for x in PT},
       "⛔ Echo One is 73%% on 2026-09-13; card %s, list %s"
       % (PC.get("date"), [(x["player"], x.get("commence")) for x in PT]))
    _want = {"below_payable_floor": 1, "same_player_already_listed": 1,
             "same_game_already_listed": 1, "pool_after_price_gate": 6,
             "distinct_games": 4, "shared_with_board_head": 4,
             "board_head_size": 7}
    ck("🔴 the counts the card publishes are the planted board's own",
       {k: PM.get(k) for k in _want} == _want,
       "want %s, got %s" % (_want, {k: PM.get(k) for k in _want}))
    _rule = PC.get("top_plays_rule") or ""
    ck("🔴 the rule sentence carries THIS card's overlap and its held-back count",
       "It is now 4 of 7, over 4 game(s)" in _rule
       and "ONE PLAY PER GAME" in _rule
       and "1 row(s) were held back because their game was already represented" in _rule
       and "No row was held back for a repeat game" not in _rule,
       _rule[:400])
# ⛔ AND THE OTHER DIRECTION OF THE SAME SENTENCE: nothing held back.
PC1 = run_planted(planted_board(one_per_game=True))
if ck("the builder produces a card from the one-row-per-game board", PC1 is not None):
    _rule1 = PC1.get("top_plays_rule") or ""
    ck("🔴 with nothing held back the sentence SAYS nothing was held back",
       len(PC1["top_plays"]) == 4
       and PC1["top_plays_excluded"].get("same_game_already_listed") == 0
       and "No row was held back for a repeat game" in _rule1
       and "held back because their game was already represented" not in _rule1,
       "%d play(s); %s" % (len(PC1["top_plays"]), _rule1[:400]))

# ⚠️ ORDER AND FLOOR ON THE FUNCTION ITSELF. End to end the caller already
#    sorts by confidence (and drops everything below -700), which hides a
#    missing sort or a floor at the wrong boundary inside build_top_plays.
_asc = [{"player": "S%d" % i, "price": -110, "confidence": 50 + i,
         "game_id": "s%d" % i} for i in range(6)]
_ord, _ = card_fb.build_top_plays(_asc, [])
ck("🔴 build_top_plays puts an ASCENDING pool in strictly descending order",
   [x["confidence"] for x in _ord] == [55, 54, 53, 52, 51, 50],
   "got %s" % [x["confidence"] for x in _ord])
_fl, _flm = card_fb.build_top_plays(
    [{"player": "F1", "price": card_fb.TOP_PRICE_FLOOR - 50, "confidence": 99, "game_id": "f1"},
     {"player": "F2", "price": card_fb.TOP_PRICE_FLOOR, "confidence": 98, "game_id": "f2"},
     {"player": "F3", "price": card_fb.TOP_PRICE_FLOOR + 1, "confidence": 60, "game_id": "f3"}], [])
ck("🔴 the payable floor drops the row AT %d and below, and keeps %d"
   % (card_fb.TOP_PRICE_FLOOR, card_fb.TOP_PRICE_FLOOR + 1),
   [x["player"] for x in _fl] == ["F3"] and _flm["below_payable_floor"] == 2,
   "got %s, %s dropped" % ([x["player"] for x in _fl], _flm["below_payable_floor"]))

# ⛔ THE EMPTY-LIST SENTENCES, THROUGH THE BUILDER: a MARKET-only board, a
#    board whose name join FAILS ITS GATE with one real player on it, and a
#    board with nothing priced at all.
PMK = run_planted(rename_all_but(None)(planted_board()))
if ck("the builder produces a card from the planted MARKET-only board", PMK is not None):
    ck("🔴 the planted MARKET-only board HAS rows, and every one is MARKET",
       len(PMK["picks"]) == 7
       and {x.get("confidence_basis") for x in PMK["picks"]} == {"MARKET"},
       "⛔ rule 67: a MARKET-only board of 0 rows is an EMPTY board. %d rows, %s"
       % (len(PMK["picks"]), sorted({x.get("confidence_basis") for x in PMK["picks"]})))
    ck("🔴 ...no top plays, and the sentence says the rows exist but carry no record",
       PMK["top_plays"] == []
       and "Not because the board is empty" in PMK["top_plays_rule"]
       and "none carries a record" in PMK["top_plays_rule"]
       and ("%d row(s) are priced" % len(PMK["picks"])) in PMK["top_plays_rule"],
       PMK["top_plays_rule"][:200])
PGT = run_planted(rename_all_but("Alpha One")(planted_board()))
if ck("the builder produces a card when the name join fails its gate", PGT is not None):
    _a1 = [x for x in PGT["picks"] if x["player"] == "Alpha One"]
    ck("🔴 a join under 60% strips the rate from the player who DID match",
       bool(_a1) and all(x.get("confidence_basis") == "MARKET"
                         and x.get("confidence") is None for x in PGT["picks"])
       and PGT["top_plays"] == [],
       "⛔ 1 of 7 names matched; a record left on Alpha One would rank a "
       "board the run decided it did not trust. Alpha One rows %s, top %d"
       % ([(x.get("confidence_basis"), x.get("confidence")) for x in _a1],
          len(PGT["top_plays"])))
PEM = run_planted(dict(planted_board(), games=[], n_games=0))
if ck("the builder produces a card from a board with no games", PEM is not None):
    ck("🔴 an EMPTY planted board is not blamed on 'no row carries a record'",
       PEM["picks"] == [] and PEM["top_plays"] == []
       and "Nothing is priced for this day yet" in PEM["top_plays_rule"]
       and "Not because the board is empty" not in PEM["top_plays_rule"],
       PEM["top_plays_rule"][:160])

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
    # ⛔ `<= {"MARKET"}` is the identical assertion on any non-empty
    #    board — no row claims a record — and does not demand rows exist.
    ck("that board is MARKET-only",
       {x.get("confidence_basis") for x in MK["picks"]} <= {"MARKET"},
       "%d rows" % len(MK["picks"]))
    ck("and it produces NO top plays at all", MK["top_plays"] == [],
       "not a price-ranked list wearing a 'most likely to hit' heading")
    if not MK["picks"]:
        # 🔴 THE FIXTURE BREAKS NAMES; IT CANNOT MANUFACTURE GAMES.
        #    `[2026-09-10]` the real props board held 0 games, so breaking
        #    every name produced a board with 0 rows — which is an EMPTY
        #    board, not a market-only one, and the wording check below is
        #    asking about a state this run never reached.
        note("⚠️ NOT EXERCISED: the real props board holds 0 games, so the "
             "name-break fixture yields 0 rows — an empty board, not a "
             "MARKET-only one. The wording check needs a priced row.")
    else:
        ck("the card says why, and does not blame an empty board",
           "no row on it carries a record" in MK["top_plays_rule"]
           or "none carries a record" in MK["top_plays_rule"],
           MK["top_plays_rule"][:70])
        ck("...and it says the board is NOT the reason",
           "Not because the board is empty" in MK["top_plays_rule"],
           MK["top_plays_rule"][:70])

# ⚠️ The cap must hold even when the pool is enormous.
# ⚠️ ONE GAME PER PLAY MEANS THE FIXTURE NEEDS ENOUGH GAMES. The first
# version of this gave 500 rows only FOUR game ids and then asserted the
# cap was reached — which the one-per-game rule correctly refuses. ⛔ The
# expectation was stale, not the code; both shapes are checked now.
big = [{"player": "P%d" % i, "price": -110, "confidence": 90 - i % 30,
        "game_id": "g%d" % i} for i in range(500)]
plays, meta = card_fb.build_top_plays(big, [])
ck("the cap holds on a 500-row pool with 500 games",
   len(plays) == card_fb.TOP_N, "%d" % len(plays))
ck("dedup holds on a 500-row pool",
   len({x["player"] for x in plays}) == len(plays))

# 🔴 AND THE RULE BITES WHEN THE SLATE IS SMALL, which is the whole cost
# of Sam's choice: four games can only ever produce four top plays.
few = [{"player": "Q%d" % i, "price": -110, "confidence": 90 - i % 30,
        "game_id": "g%d" % (i % 4)} for i in range(500)]
plays4, meta4 = card_fb.build_top_plays(few, [])
ck("a four-game slate yields exactly four top plays", len(plays4) == 4,
   "%d — one per game, not padded toward the cap of %d"
   % (len(plays4), card_fb.TOP_N))
ck("and the rows held back for a repeat game are counted",
   meta4["same_game_already_listed"] > 0,
   "%d" % meta4["same_game_already_listed"])

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
    # ⚠️ The sentence now reports the GAME dedup rather than the price
    # gate, because one-per-game is what actually shapes this list —
    # the price gate drops ~1 row of 384 on football.
    ck("the card's own wording reports the rule that actually shaped it",
       (M["same_game_already_listed"] > 0) ==
       ("held back because their game was already represented"
        in C["top_plays_rule"]),
       "%d row(s) held back for a repeat game"
       % M["same_game_already_listed"])

# ───────────────────────────────────────────────────────────────
print("\n═══ 5. THE PAGE PRINTS IT, AND DOES NOT RE-DERIVE IT ═══")
h = open(os.path.join(ROOT, "index.html")).read()
i = h.index("function fbTopPlays(")
j = h.index("\nfunction ", i + 10)
blk = h[i:j]
ck("the page renders top_plays from the card", "C.top_plays" in blk)
# `[Sam, 2026-10-01]` THIS USED TO REQUIRE the card's own rule sentence
#    (`top_plays_rule`) under the heading, beside a note box explaining the
#    one-play-per-game rule from `top_plays_excluded`. Sam removed every
#    explanation from every tab, so the list is now required WITHOUT them.
#    ⛔ card_fb.py still writes `top_plays_rule` and `top_plays_excluded`,
#    and §2-§4 above still check the sentence the builder writes.
ck("[Sam, 2026-10-01] and no longer prints the card's rule sentence or its note box",
   "top_plays_rule" not in blk and "top_plays_excluded" not in blk and 'class="note"' not in blk,
   "Sam: 'i just want what's supposed to be in each tab to be in each tab'")
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
