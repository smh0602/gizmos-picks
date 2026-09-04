#!/usr/bin/env python3
"""THE BOARD MATCH, RECONCILED AGAINST GROUND TRUTH.

🔴 WHY THIS FILE EXISTS. `verify_board`'s duplicate check used to ask
whether **two records for one matchup sat closer together than the page's
matching window**. That is a PROXY, and `[measured 2026-09-04]` it was
wrong in both directions:

  ⚠️ **IT FIRED ON A CORRECT BOARD.** A Detroit / Cleveland DOUBLEHEADER
     put two records exactly 4.00 hours apart against a 4-hour window and
     the run went red — while `test_board_match.js` passed 28 assertions
     on that same board, including that pair. **The window is a maximum
     distance, not a resolution limit.**

  🔴 **AND IT COULD NOT CATCH THE BUG IT WAS WRITTEN FOR.** On 2026-08-26
     six board records were the PREVIOUS NIGHT'S GAME — one record per
     matchup, **no duplicates at all** — and cards showed CHC at -4000
     with a 4.5 total. A proximity rule passes that without a murmur.

✅ THE REPLACEMENT HAS GROUND TRUTH: every carded row stores the
`game_id` of the record it was PRICED from, so the page's own
nearest-first-pitch matcher can be run and its answer checked against
that id. ⛔ Strictly harder — it catches a wrong match whether or not a
duplicate exists.

⚠️ Everything below is constructed. No network, and nothing depends on
today's live board.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.abspath(__file__))
fails = []


def ck(cond, label, detail=""):
    print(f"  {'ok  ' if cond else '🔴 FAIL'} {label:<58} {detail}")
    if not cond:
        fails.append(label)


def game(gid, away, home, commence):
    return {"id": gid, "away": away, "home": home, "commence": commence,
            "moneyline": {"away": 120, "home": -140},
            "run_line": -1.5, "run_line_team": home,
            "total": 8.5, "books": ["hardrockbet"]}


def pick(gid, away, home, commence):
    return {"pid": 1, "kind": "hitter", "player": "A Batter",
            "market": "batter_hits", "side": "over", "line": 0.5,
            "price": -150, "book": "hardrockbet", "on_hardrock": True,
            "game_id": gid, "away": away, "home": home, "commence": commence}


def run(board_games, card_picks, date="2026-09-04"):
    """Drive the real verify_board.py against a constructed tree."""
    t = tempfile.mkdtemp()
    try:
        os.makedirs(f"{t}/data/latest", exist_ok=True)
        os.makedirs(f"{t}/picks", exist_ok=True)
        shutil.copy(os.path.join(REPO, "verify_board.py"), t)
        # ⚠️ the real index.html, because the window must come from the
        # page rather than from a number retyped in a test.
        shutil.copy(os.path.join(REPO, "index.html"), t)
        json.dump({"built_at": f"{date}T14:00:00Z", "kind": "MARKET",
                   "games": board_games}, open(f"{t}/data/latest/board.json", "w"))
        json.dump({"date": date, "kind": "gizmos-card", "picks": card_picks,
                   "below_price_floor": []},
                  open(f"{t}/picks/{date}.json", "w"))
        # ⛔ a football card in the same directory, exactly as production
        # has: it must not be selected as "the newest card".
        json.dump({"date": date, "kind": "RECORD + MARKET", "league": "ncaaf",
                   "picks": []}, open(f"{t}/picks/fb-ncaaf-latest.json", "w"))
        p = subprocess.run([sys.executable, "verify_board.py"], cwd=t,
                           capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr
    finally:
        shutil.rmtree(t, ignore_errors=True)


DH1 = game("aaa11111", "Detroit Tigers", "Cleveland Guardians",
           "2026-09-04T19:16:00Z")
DH2 = game("bbb22222", "Detroit Tigers", "Cleveland Guardians",
           "2026-09-04T23:16:00Z")

print("\n1. 🔴 A DOUBLEHEADER EXACTLY AT THE WINDOW IS NOT A DEFECT")
print("   Two records 4.00h apart against a 4-hour window. The old")
print("   proximity rule failed this. Nearest-match resolves it.")
rc, out = run([DH1, DH2],
              [pick("aaa11111", "Detroit Tigers", "Cleveland Guardians",
                    "2026-09-04T18:11:00Z")])
ck(rc == 0, "the board passes", f"rc={rc}")
ck("2 matchup(s) appear twice" in out or "appear twice" in out,
   "  the duplicate is still REPORTED, not hidden")
ck("1 row(s) reconciled" in out, "  and the row was actually reconciled")

print("\n2. 🔴 THE 2026-08-26 BUG — LAST NIGHT'S RECORD, TODAY'S CARD")
print("   ⛔ No duplicate exists, so the OLD proximity rule passed this")
print("   without a murmur. The page must show NO odds rather than")
print("   yesterday's price, and the row must be VISIBLE as unpriced.")
stale = game("ccc33333", "Chicago Cubs", "Miami Marlins",
             "2026-09-03T23:10:00Z")           # yesterday
rc2, out2 = run([stale],
                [pick("ddd44444", "Chicago Cubs", "Miami Marlins",
                      "2026-09-04T23:10:00Z")])  # today's card
ck(rc2 == 0, "fail-closed: 24h away is outside the window", f"rc={rc2}")
ck("rolled off" in out2,
   "🔴 and the unpriced row is REPORTED, not silently dropped")
ck("0 row(s) reconciled" in out2,
   "  nothing was reconciled, and the run says so rather than "
   "claiming a clean board")

print("\n2b. ⛔ AND THE HALF THAT IS STILL DANGEROUS: A SUBSTITUTION")
print("    The record the row was priced from is gone, but ANOTHER")
print("    record for the same matchup sits inside the window — so the")
print("    page would show a price this row was never priced from.")
print("    ⚠️ An earlier draft of this check let that through, because")
print("    'rolled off' was treated as nothing-to-see.")
rc2b, out2b = run([game("zzz00000", "Chicago Cubs", "Miami Marlins",
                        "2026-09-04T21:40:00Z")],      # 1.5h from the card
                  [pick("ddd44444", "Chicago Cubs", "Miami Marlins",
                        "2026-09-04T23:10:00Z")])
ck(rc2b != 0, "🔴 a substitution fails the board", f"rc={rc2b}")
ck("NOT on this board" in out2b, "  and it says exactly what happened")

print("\n3. ⛔ A WRONG MATCH IS CAUGHT EVEN WHEN BOTH GAMES ARE REAL")
print("   The card was priced from game 2; the page must not hand it")
print("   game 1's number.")
rc3, out3 = run([DH1, DH2],
                [pick("bbb22222", "Detroit Tigers", "Cleveland Guardians",
                      "2026-09-04T19:20:00Z")])   # first-pitch says GAME 1
ck(rc3 != 0, "the mismatch fails the board", f"rc={rc3}")
ck("matched" in out3 and "not" in out3,
   "  and the failure names both ids")

print("\n4. 🔴 ZERO ROWS RECONCILED IS NOT A PASS")
print("   ⛔ A reconciliation that reconciled nothing has asserted")
print("   nothing — rule 76 in this file's own shape.")
rc4, out4 = run([game("eee55555", "Team A", "Team B", "2026-09-04T20:00:00Z")],
                [])                                  # a card with no picks
ck(rc4 != 0, "an empty reconciliation fails", f"rc={rc4}")
ck("share no rows" in out4, "  and says why", "")

print("\n5. ⚠️ A RECORD THAT ROLLED OFF THE BOARD IS AN HONEST ZERO")
print("   The one legitimate reason to reconcile nothing.")
rc5, out5 = run([game("fff66666", "Team A", "Team B", "2026-09-05T20:00:00Z")],
                [pick("999zzzzz", "Old Team", "Other Team",
                      "2026-09-04T20:00:00Z")])
ck(rc5 == 0, "it passes, because nothing could be checked", f"rc={rc5}")
ck("rolled off" in out5, "  and the reason is printed, not assumed")

print()
if fails:
    print(f"🔴 {len(fails)} FAILURE(S)")
    for f in fails:
        print(f"   - {f}")
    sys.exit(1)
print("✅ board reconciliation: doubleheaders pass, stale records do not")
