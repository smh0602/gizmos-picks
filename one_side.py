#!/usr/bin/env python3
"""one_side.py — ONE TEAM PER GAME: every side pick is on the model's expected winner.

`[Sam, 2026-10-16]` "i noticed that the model picked huskies on the moneyline for
college foootbal but also picked the -3.5 spread for purdue; the huskies opponent.
these two picks go directly against one another and we can't have our model choosing
both sides at once" — "fixed as whole for all leagues so it doesn't happen again".
Asked which side stays, he chose the EXPECTED WINNER: every moneyline, spread,
alternate spread and run-line pick, in all three leagues, is on the team the Game
Lines tab picks to win (the higher model win chance; winners.py reads `expected_side`
from here, so the tab and every list can never disagree). A total backs no team and
is never touched. `[Sam, 2026-10-16]` ~~spread, alternate spread~~ for FOOTBALL: a
spread and its alternate follow the model's predicted score instead ("purdue will win
25-23 ... gizmos picks should like the +3.5 spread for washington", "Yes, everywhere";
fb_model.score_pick, `score_side_ok` below), so they can back the expected loser; the
moneyline stays on the expected winner.

Why the clash happened: each market is picked on its own (football: three separate
fits, the moneyline taking the best-value side, often the underdog; MLB: the run line
taking its own higher side, usually the +1.5 underdog). Measured 2026-10-16: 18 of 55
college games and 5 of 13 NFL games in the model's pick list, and 6 of 11 MLB games
with game-line picks, backed both teams.

⛔ It only REMOVES a pick. It never adds one, re-ranks, re-prices or changes a chance,
and it runs AFTER each market's own pick (never inside fb_model.best_pick, whose
walk-forward record is graded history). No expected winner (no win chance) means no
side pick, as the Game Lines tab then names no winner. Stdlib only; imports nothing
from the repo.

`[Sam, 2026-10-16]` AND ONE SIDE PER PROP. The same props model took both sides of 5
props that day (the card's Hunter Tipton Under 3.5 at 55%, its own pick list's Over
3.5 at 45%, because +162 paid). Asked, Sam chose "Model's 50%+ side only: Every list
shows only the side the model gives 50% or more." `prop_side` / `keep_props`: for each
wager (one game, player, market and line) only the side whose number is 50 or more AND
above the other side's; an exact tie keeps neither. ~~A one-sided market (anytime TD "yes")
has no other side and is left alone~~: an anytime TD "yes" at 22% is the plus-money value
side Sam declined ("Keep value picks"), so it needs 50% too. `one_per_wager`: a wager with
no number on either side still never shows both ways (the first in the list's own order).
"""
TOTAL_WORDS = ("total",)          # total, totals, alternate_total(s), team totals: no team side


def expected_side(p_home):
    """'home' or 'away' from the HOME team's win chance in PERCENT (0-100), or None
    without one. ⛔ The Game Lines tab's own rule (winners.make_row): the higher chance,
    the home team on an exact tie."""
    if p_home is None:
        return None
    return "home" if p_home >= 100 - p_home else "away"


def backs(row):
    """The team a pick backs, 'home' or 'away'; None for a total. A row naming its team
    instead of a side (the price-gap rows: `side` is the outcome name) is matched on
    `home` / `away`, or on the "away @ home" in `game`; a side pick whose team cannot be
    told is '?', and `keep` drops it (fail closed)."""
    mk = str(row.get("market") or "").lower()
    if any(w in mk for w in TOTAL_WORDS):
        return None
    side = row.get("side")
    if side in ("home", "away"):
        return side
    home, away = row.get("home"), row.get("away")
    if (home is None or away is None) and " @ " in str(row.get("game") or ""):
        away, home = str(row["game"]).split(" @ ", 1)
    if side is not None and side == home:
        return "home"
    if side is not None and side == away:
        return "away"
    return "?"


def keep(rows, winner):
    """-> (kept, dropped). `winner(row)` -> 'home' / 'away' / None: the expected winner
    of the row's game. A total always stays; a side pick stays only on its game's
    expected winner."""
    kept, dropped = [], []
    for r in rows or []:
        b = backs(r)
        (kept if b is None or (b != "?" and b == winner(r)) else dropped).append(r)
    return kept, dropped


def by_names(win_chances):
    """A `winner(row)` from football fb-model.json `win_chances`, joined on the two team
    names (the board and the model name a game by different ids; the names are the same
    odds-feed names on both)."""
    side = {(w.get("away"), w.get("home")): expected_side(w.get("p_home")) for w in win_chances or []}

    def winner(r):
        away, home = r.get("away"), r.get("home")
        if (away is None or home is None) and " @ " in str(r.get("game") or ""):
            away, home = str(r["game"]).split(" @ ", 1)
        return side.get((away, home))
    return winner


def prop_side(p_over, p_under, half=0.5):
    """'over' / 'under': the side the model gives 50% or more AND more than the other, or
    None (an exact tie, or no number). `half` is 0.5 for chances, 50 for percents."""
    if p_over is None or p_under is None or p_over == p_under:
        return None
    side, p = ("over", p_over) if p_over > p_under else ("under", p_under)
    return side if p >= half else None


def keep_props(rows, key, value):
    """-> (kept, dropped). `key(row)`: the wager (one game, player, market and line);
    `value(row)`: the model's number for the row's side (0-100), or None. Per wager, only
    the rows on the side with the highest number, when that number is 50 or more and no
    other side ties it (a one-sided "yes" needs 50% as well). A wager with no number on
    any side is left as it is (`one_per_wager` then keeps one side)."""
    best = {}
    for r in rows or []:
        v = value(r)
        if v is not None:
            best.setdefault(key(r), {})
            s = best[key(r)]
            s[r.get("side")] = max(v, s.get(r.get("side"), v))
    kept, dropped = [], []
    for r in rows or []:
        s = best.get(key(r))
        if s is None:
            kept.append(r)
            continue
        top = max(s.values())
        sides = [x for x, v in s.items() if v == top]
        v = value(r)
        ok = len(sides) == 1 and sides[0] == r["side"] and top >= 50 and v is not None and v >= 50
        (kept if ok else dropped).append(r)
    return kept, dropped


def one_per_wager(rows, key):
    """-> (kept, dropped): never both sides of one wager, the first row of each in the
    list's own order kept (MLB's select_board rule). For rows that carry no number."""
    seen, kept, dropped = set(), [], []
    for r in rows or []:
        k = key(r)
        (dropped if k in seen else kept).append(r)
        seen.add(k)
    return kept, dropped


def prop_conflicts(rows, key, value=None):
    """The guard: wagers shown on BOTH sides, and (given `value`) a row the model gives
    under 50% -> [(wager, why)]."""
    sides, out = {}, []
    for r in rows or []:
        sides.setdefault(key(r), set()).add(r.get("side"))
        v = value(r) if value else None
        if v is not None and v < 50:
            out.append((key(r), "a side the model gives under 50%"))
    out += [(k, "both sides") for k, s in sides.items() if len(s) > 1]
    return out


def conflicts(rows, winner=None, game=lambda r: r.get("game_id") or r.get("game")):
    """The games whose side picks break the rule -> [(game, why)]: picks on BOTH teams,
    and (given `winner`) a pick on the team the model does not expect to win. The guard
    the builders' tests and verify_card.py run."""
    seen = {}
    for r in rows or []:
        b = backs(r)
        if b is not None:
            seen.setdefault(game(r), []).append((b, r))
    out = []
    for g, picks in seen.items():
        teams = {b for b, _ in picks}
        if len(teams) > 1:
            out.append((g, "picks on both teams"))
        elif winner is not None and any(b == "?" or b != winner(r) for b, r in picks):
            out.append((g, "a pick on the team the model does not expect to win"))
    return out


# ══════════════════════════════════════════════════════════════════════
# `[Sam, 2026-10-16]` AND ON THE PREDICTED SCORE'S SIDE. The football model's predicted score
# comes from its moneyline and total fits, each spread pick from a separate fit: 13 of 66
# college spread and total picks sat on the side the model's own score said loses (Purdue -3.5
# beside "Purdue by 1.2"). Sam chose "Must match the score".
# ══════════════════════════════════════════════════════════════════════
def score_side_ok(row, score, point):
    """`[Sam, 2026-10-16]` "Must match the score: A spread or total pick, and a parlay's
    line leg, shows only when the predicted score lands on its side." -> True / False, or
    None for a row that is neither a spread nor a total (a moneyline is the expected
    winner's, `keep`). `score`: {"home", "away"} (fb_model.predicted_score, as the Game
    Lines tab prints it); `point`: the team's OWN point on a spread, the line on a total.
    Landing ON the number is not its side; no score or no point is never its side."""
    mk = str(row.get("market") or "").lower()
    total = any(w in mk for w in TOTAL_WORDS)
    if not total and "spread" not in mk:
        return None
    if not score or score.get("home") is None or score.get("away") is None or point is None:
        return False
    h, a = float(score["home"]), float(score["away"])
    # ⚠️ compared after rounding: 21.1 - 14.1 - 7 is 1.8e-15 in binary, which is ON the number
    if total:
        s = str(row.get("side") or "").lower()
        d = round(h + a - point, 6)
        return d > 0 if s == "over" else d < 0 if s == "under" else False
    b = backs(row)
    return b in ("home", "away") and round(((h - a) if b == "home" else (a - h)) + point, 6) > 0


def score_keep(rows, score, point=lambda r: r.get("line")):
    """-> (kept, dropped): every spread and total row whose predicted score (`score(row)`)
    lands on its side; every other row as it is."""
    kept, dropped = [], []
    for r in rows or []:
        ok = score_side_ok(r, score(r), point(r))
        (kept if ok is None or ok else dropped).append(r)
    return kept, dropped


def scores_by_names(win_chances):
    """A `score(row)` from football fb-model.json `win_chances`, joined on the two team
    names, as `by_names` joins the expected winner."""
    sc = {(w.get("away"), w.get("home")): w.get("score") for w in win_chances or []}

    def score(r):
        away, home = r.get("away"), r.get("home")
        if (away is None or home is None) and " @ " in str(r.get("game") or ""):
            away, home = str(r["game"]).split(" @ ", 1)
        return sc.get((away, home))
    return score
