#!/usr/bin/env python3
"""
THE GAME LINES TAB: THE MODEL'S PICK TO WIN EVERY GAME, IN ALL THREE LEAGUES.

`[Sam, 2026-10-01]` *"remove the game lines standalone tab with moneyline
predictions, in this tab you will simply just give the models pick on whos
going to win the game outright. do this for all leagues"*; asked what the tab
becomes: *"replace it with moneyline predictions and just have the models
picks for who wins outright"*.

One row per game on the slate: the two teams and the start, the team the
model gives the higher chance to win, that chance, and the best moneyline for
that team at the league's books. ⛔ No price floor and no edge rule: every
game gets its winner.
  MLB       `win` in data/latest/mlb-game-model.json (the card's day). A game
            whose two starters are not both named has no pick yet. The price
            is board.json's best of the five books.
  football  `win_chances` in fb-model.json (the moneyline model, both teams),
            for card_fb.next_line_slate's day, one day only; the price is the
            best of Hard Rock, FanDuel and DraftKings.

FROZEN AND GRADED ONCE, as fb_ledger does it: every run saves the picks of
games not yet started (daystore, write-once); a game's pick is the one in the
LAST save before its start; it is graded once from the final score (the first
stored grade stands) into ONE record per league, never mixed into another.
verify_record.py re-grades it a second way.
-> data/latest/winners.json (MLB), data/<lg>/latest/winners.json (football).
"""
import datetime
import glob
import gzip
import json
import os

import daystore

ROOT = os.path.dirname(os.path.abspath(__file__))
SNAP, GRADES = "winner-picks", "winner-grades"


def _json(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gz(p):
    try:
        return json.load(gzip.open(p, "rt"))
    except (OSError, ValueError):
        return {}


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def data_dir(lg, root=None):
    return os.path.join(root or ROOT, "data", *([] if lg == "mlb" else [lg]))


def make_row(gid, commence, away, home, p_home, px_home, px_away):
    """One game. The pick is the side with the higher chance; no chance, no pick."""
    r = {"game_id": str(gid), "commence": commence, "away": away, "home": home,
         "pick": None, "side": None, "chance": None, "price": None, "book": None}
    if p_home is None:
        return r
    side = "home" if p_home >= 100 - p_home else "away"
    q = (px_home if side == "home" else px_away) or {}
    p = p_home if side == "home" else 100 - p_home
    r.update(side=side, pick=home if side == "home" else away, chance=int(round(p)),
             chance_value=round(p, 1), price=q.get("price"), book=q.get("book"))
    return r


def mlb_rows(model, board):
    """Every game in the model's file; no pick until both starters are named."""
    import card
    out = []
    for g in (model or {}).get("games") or []:
        ml = (card.board_game(board, g) or {}).get("best_ml") or {}
        named = all(((g.get("starters") or {}).get(s) or {}).get("id") for s in ("home", "away"))
        out.append(make_row(g.get("game_pk"), g["commence"], g["away"], g["home"],
                            (g.get("win") or {}).get("home") if named else None,
                            ml.get(g["home"]), ml.get(g["away"])))
    return out


def fb_rows(model, slate, et_date):
    """Every game of ET day `slate` in the model's win chances."""
    return [make_row(g["game_id"], g["commence"], g["away"], g["home"], g.get("p_home"),
                     (g.get("best_ml") or {}).get("home"), (g.get("best_ml") or {}).get("away"))
            for g in (model or {}).get("win_chances") or [] if et_date(g["commence"]) == slate]


def frozen(data):
    """game id -> the pick in the LAST save taken before that game's start."""
    best = {}
    for p in glob.glob(os.path.join(data, "*", SNAP, "*.json.gz")):
        s = _gz(p)
        for r in s.get("rows") or []:
            t = s.get("taken_at") or ""
            if t < (r.get("commence") or "") and t > best.get(r["game_id"], ("",))[0]:
                best[r["game_id"]] = (t, r)
    return {k: dict(r, shown_at=t) for k, (t, r) in best.items()}


def finals(lg, root=None):
    """game id -> (state, home score, away score)."""
    out = {}
    if lg == "mlb":
        for p in sorted(glob.glob(os.path.join(data_dir(lg, root), "*", "results", "final.json.gz"))):
            for g in _gz(p).get("games") or []:
                sc = g.get("score") or {}
                out[str(g.get("gamePk"))] = (g.get("state"), sc.get("home"), sc.get("away"))
        return out
    import fb_ledger
    for k, g in fb_ledger.schedule_by_id(lg, root).items():
        out[k] = ("Final" if g.get("final") else None, g.get("home_score"), g.get("away_score"))
    return out


def grade(r, fin, void_states):
    """(state, won): a postponed game or a tie is a VOID, an unfinished one PENDING."""
    st, h, a = fin.get(r["game_id"], (None, None, None))
    if st in void_states or (st == "Final" and h is not None and h == a):
        return "void", None
    if st != "Final" or h is None or a is None:
        return "pending", None
    return "graded", (h > a) == (r["side"] == "home")


def stored_grades(data):
    """game id -> its FIRST stored grade, which is the one that stands."""
    out = {}
    for p in sorted(glob.glob(os.path.join(data, "*", GRADES, "*.json.gz"))):
        for g in _gz(p).get("grades") or []:
            out.setdefault(g["game_id"], g)
    return out


def build(lg=None, root=None, when=None, log=print):
    lg = (lg or os.environ.get("LEAGUE") or "mlb").lower()
    when = when or datetime.datetime.now(datetime.timezone.utc)
    now, data = _iso(when), data_dir(lg, root)
    latest = os.path.join(data, "latest")
    if lg == "mlb":
        from collect import VOID_STATES
        model = _json(os.path.join(latest, "mlb-game-model.json"))
        rows, slate = mlb_rows(model, _json(os.path.join(latest, "board.json"))), model.get("slate")
    else:
        import card_fb
        VOID_STATES = ()
        snap = card_fb.latest_gamelines_snapshot()[0]
        slate = card_fb.next_line_slate(snap) if snap else None
        rows = fb_rows(_json(os.path.join(latest, "fb-model.json")), slate, card_fb.et_date)
    live = [r for r in rows if r["pick"] and r["commence"] > now]
    if live:
        daystore.archive({"league": lg, "taken_at": now, "rows": live}, data, SNAP, log=log, when=when)
    fz = frozen(data)
    # ⛔ A STARTED GAME SHOWS ITS FROZEN PICK, never a rebuilt one.
    rows = [fz.get(r["game_id"], r) if r["commence"] <= now else r for r in rows]
    stored, fin, new = stored_grades(data), finals(lg, root), []
    for gid, r in fz.items():
        if gid not in stored:
            state, won = grade(r, fin, VOID_STATES)
            if state != "pending":
                new.append({"game_id": gid, "state": state, "won": won, "graded_at": now})
    if new:
        daystore.archive({"league": lg, "grades": new}, data, GRADES, log=log, when=when)
        for g in new:
            stored.setdefault(g["game_id"], g)
    g = [x for k, x in stored.items() if k in fz]
    w, n = sum(1 for x in g if x["won"]), sum(1 for x in g if x["state"] == "graded")
    doc = {"league": lg, "kind": "MODEL", "slate": slate, "built_at": now,
           "rule": ("The model's pick to win each game: the side it gives the higher chance, "
                    "frozen at the start and graded once from the final score."),
           "rows": sorted(rows, key=lambda r: (r["commence"], r["game_id"])),
           "record": {"w": w, "l": n - w, "n": n, "pct": round(100.0 * w / n, 1) if n else None,
                      "voids": sum(1 for x in g if x["state"] == "void")}}
    os.makedirs(latest, exist_ok=True)
    with open(os.path.join(latest, "winners.json"), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, separators=(",", ":"))
    log("%s winners: %d game(s) on %s, record %d-%d" % (lg, len(rows), slate, w, n - w))
    return doc


if __name__ == "__main__":
    build()
