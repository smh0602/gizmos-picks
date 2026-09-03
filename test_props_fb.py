#!/usr/bin/env python3
"""`collect_props_board_fb` — the football props join, on a fake pull.

🔴 WHY THIS IS TESTED BEFORE THE DATA EXISTS. The first football
`props-player` pull runs Thursday evening. ⛔ THE PULL COSTS CREDITS AND
ODDS HISTORY CANNOT BE RE-BOUGHT, so discovering the join was broken on
Friday morning means a slate that can never be recovered. The input
shape is already known -- read off a live MLB snapshot -- and the output
shape is ours, so there is nothing left to guess.

✅ WHAT THIS PINS, AND WHY EACH ONE WOULD LOOK FINE IF BROKEN:
  1. 🔴 BEST PRICE IS THE BEST PRICE FOR A BETTOR. American odds do not
     order numerically: -110 is BETTER than -130, and +140 beats both.
     ⛔ A naive min()/max() ships a board that quietly points at the
     WORST price on every row.
  2. Only Sam's five books count. A sixth book's price must not win.
  3. Books are COUNTED per side, so "1 book" never reads as consensus.
  4. Unknown markets are dropped rather than rendered with no label.
  5. ⛔ It writes NOTHING when there is no snapshot -- an empty board
     overwriting a real one is worse than no board.

⚠️ No network, no clock beyond the date the writer itself uses.
"""
import gzip
import json
import os
import shutil
import sys
import tempfile

os.environ.setdefault("LEAGUE", "ncaaf")
import collect as C

fails = []


def eq(got, want, label):
    ok = got == want
    print(f"  {'ok  ' if ok else '🔴 FAIL'} {label:<50} {got!r}")
    if not ok:
        fails.append(f"{label} (got {got!r} want {want!r})")


def outcome(who, side, pt, price, link=None):
    return {"description": who, "name": side, "point": pt,
            "price": price, "link": link}


def snapshot(bookmakers):
    return {"pulled_at": "2026-09-03T22:31:00Z", "regions": "us,us2",
            "n_events": 1,
            "events": [{"id": "g1", "home_team": "Rutgers",
                        "away_team": "UMass",
                        "commence_time": "2026-09-03T22:00:00Z",
                        "bookmakers": bookmakers}]}


def run(doc, day="2026-09-03"):
    """Write a fake snapshot where the collector will look, then join."""
    tmp = tempfile.mkdtemp()
    old_data, old_now = C.DATA, C.now
    try:
        C.DATA = tmp
        d = os.path.join(tmp, day, "props-player")
        os.makedirs(d, exist_ok=True)
        with gzip.open(os.path.join(d, "2231.json.gz"), "wt") as fh:
            json.dump(doc, fh)
        import datetime as _dt
        C.now = lambda: _dt.datetime(2026, 9, 3, 23, 0, tzinfo=_dt.timezone.utc)
        written = {}
        old_write = C.write
        C.write = lambda path, obj, compress=False: written.update({"path": path, "obj": obj})
        try:
            out = C.collect_props_board_fb("ncaaf")
        finally:
            C.write = old_write
        return out, written
    finally:
        C.DATA, C.now = old_data, old_now
        shutil.rmtree(tmp, ignore_errors=True)


MK = "player_reception_yds"

print("1. 🔴 BEST PRICE IS BEST FOR A BETTOR, NOT numerically smallest")
out, _ = run(snapshot([
    {"key": "draftkings", "title": "DK", "markets": [
        {"key": MK, "outcomes": [outcome("Ja'Marr Chase", "Over", 65.5, -130)]}]},
    {"key": "fanduel", "title": "FD", "markets": [
        {"key": MK, "outcomes": [outcome("Ja'Marr Chase", "Over", 65.5, -110)]}]},
    {"key": "betmgm", "title": "MGM", "markets": [
        {"key": MK, "outcomes": [outcome("Ja'Marr Chase", "Over", 65.5, -125)]}]},
]))
over = out["games"][0]["props"][0]["sides"]["over"]
eq(over["price"], -110, "-110 beats -130 and -125")
eq(over["book"], "fanduel", "and it names the right book")
eq(over["n_books"], 3, "three books counted on that side")

print("\n2. a plus price beats every minus price")
out, _ = run(snapshot([
    {"key": "draftkings", "title": "DK", "markets": [
        {"key": MK, "outcomes": [outcome("A. Player", "Under", 40.5, -105)]}]},
    {"key": "hardrockbet", "title": "HR", "markets": [
        {"key": MK, "outcomes": [outcome("A. Player", "Under", 40.5, 115)]}]},
]))
u = out["games"][0]["props"][0]["sides"]["under"]
eq(u["price"], 115, "+115 beats -105")
eq(u["book"], "hardrockbet", "named the book")

print("\n3. ⛔ a book outside Sam's five cannot win, or even be counted")
out, _ = run(snapshot([
    {"key": "draftkings", "title": "DK", "markets": [
        {"key": MK, "outcomes": [outcome("B. Player", "Over", 55.5, -120)]}]},
    # ⚠️ bovada offers a BETTER price and must be ignored entirely
    {"key": "bovada", "title": "Bovada", "markets": [
        {"key": MK, "outcomes": [outcome("B. Player", "Over", 55.5, 105)]}]},
]))
o = out["games"][0]["props"][0]["sides"]["over"]
eq(o["price"], -120, "🔴 the better outside price is NOT used")
eq(o["book"], "draftkings", "the five-book price wins")
eq(o["n_books"], 1, "and the outside book is not counted")
eq("bovada" in out["books_seen"], True, "  ...but it IS reported as seen")

print("\n4. unknown markets are dropped, known ones labelled")
out, _ = run(snapshot([
    {"key": "draftkings", "title": "DK", "markets": [
        {"key": "player_kicking_points",
         "outcomes": [outcome("K. Icker", "Over", 7.5, -110)]},
        {"key": "player_receptions",
         "outcomes": [outcome("R. Eceiver", "Over", 4.5, -115)]}]},
]))
props = out["games"][0]["props"]
eq(len(props), 1, "the unlisted market is dropped")
eq(props[0]["label"], "Receptions", "the known market is labelled")
eq(props[0]["unit"], "rec", "and carries a short unit")

print("\n5. ⛔ no snapshot -> writes NOTHING")
tmp = tempfile.mkdtemp()
old = C.DATA
C.DATA = tmp
try:
    eq(C.collect_props_board_fb("ncaaf"), None, "returns None, writes no board")
finally:
    C.DATA = old
    shutil.rmtree(tmp, ignore_errors=True)

print("\n6. the board says what it is (rule 55)")
out, w = run(snapshot([
    {"key": "draftkings", "title": "DK", "markets": [
        {"key": MK, "outcomes": [outcome("C. Player", "Over", 60.5, -110)]}]},
]))
eq(out["kind"], "MARKET", "kind is MARKET")
eq("no model" in out["note"], True, "the note says football has no model")
eq(w["path"].endswith("data/ncaaf/latest/props.json.gz"), True,
   "🔴 written to the LEAGUE's directory, not MLB's")
eq(out["n_props"], 1, "counts its rungs")

print()
if fails:
    print(f"🔴 {len(fails)} FAILED:")
    for f in fails:
        print("   " + f)
    sys.exit(1)
print("✅ football props board OK")
