#!/usr/bin/env python3
"""Checks on data/latest/board.json -- the file every game card reads.

🔴 WHY THIS EXISTS AS ITS OWN SCRIPT.
`verify_card.py` gates the CARD, and the workflow runs it only on the
`card` and `refresh` modes. The `gamelines` mode rewrites board.json 28
times a day with NOTHING checking it. On 2026-08-26 that gap shipped six
game cards carrying the PREVIOUS NIGHT'S in-progress odds -- CHC at -4000
with a 4.5 total, Pittsburgh implied for 0 runs -- and three more cards
crediting the moneyline favourite with FEWER implied runs than the dog.

⛔ Do not fold these into verify_card.py. They must run on the gamelines
job, which is the job that writes the file.
"""
import json
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
def _read_json(path, what):
    """json.load(open(path)) that says WHICH FILE when it fails.

    🔴 A run on 2026-08-26 died with `JSONDecodeError: Expecting value:
    line 1 column 1 (char 0)` -- an empty file -- and the traceback named
    only Python's decoder. Nothing in the repo was empty by the time it
    could be inspected, so the file could never be identified. An error
    that cannot be diagnosed after the fact is barely an error message.
    """
    import json as _json
    try:
        with open(path) as fh:
            raw = fh.read()
    except FileNotFoundError:
        raise SystemExit(f"MISSING: {what} at {path} does not exist.")
    if not raw.strip():
        raise SystemExit(f"EMPTY: {what} at {path} is zero bytes. "
                         f"Nothing was verified. Re-run the job that writes it.")
    try:
        return _json.loads(raw)
    except Exception as e:
        raise SystemExit(f"UNREADABLE: {what} at {path} is not valid JSON "
                         f"({type(e).__name__}: {e}). First 120 chars: {raw[:120]!r}")


fails = []


def ck(name, ok, detail=""):
    print(("  PASS " if ok else "  FAIL ") + name + ("  " + detail if detail else ""))
    if not ok:
        fails.append(name)


path = os.path.join(ROOT, "data/latest/board.json")
if not os.path.exists(path):
    print("No board.json yet -- the collector has not written one. Nothing to check.")
    sys.exit(0)
B = _read_json(path, "the odds board")
games = B.get("games") or []
print(f"\nBOARD -- {len(games)} games, pulled {B.get('pulled_at')}")

print("\n1. IMPLIED RUNS -- the favourite may never be credited with fewer")
# ⛔ This is the check that would have caught the inverted run line. The
# moneyline is a single unambiguous market; the spread's LABEL is not, and
# books split on which side they show laying the runs.
bad = []
for g in games:
    wp, tt = g.get("win_pct") or {}, g.get("team_total") or {}
    if len(wp) != 2 or len(tt) != 2 or None in wp.values() or None in tt.values():
        continue
    fav, dog = max(wp, key=wp.get), min(wp, key=wp.get)
    if abs(wp[fav] - wp[dog]) < 2.0:      # a true pick-em expects nothing
        continue
    if tt[fav] < tt[dog]:
        bad.append(f"{g['away']} @ {g['home']}: {fav} favoured {wp[fav]}% "
                   f"but implied {tt[fav]} vs {tt[dog]}")
ck("no game credits the favourite with fewer implied runs", not bad, "; ".join(bad[:3]))

print("\n2. THE RUN LINE CARRIES ITS TEAM")
_rl = [g for g in games if g.get("run_line") is not None]
ck(f"every run line names the team it belongs to ({len(_rl)} priced)",
   all(g.get("run_line_team") for g in _rl),
   str([g["away"] for g in _rl if not g.get("run_line_team")][:3]))
_flag = [g for g in games if g.get("run_line_conflicted_with_moneyline")]
print(f"  NOTE  {len(_flag)} game(s) had a spread label that contradicted the "
      f"moneyline and were re-oriented to it")
for g in _flag[:4]:
    print(f"          {g['away']} @ {g['home']} -> {g['run_line']} ({g['run_line_team']})")

print("\n3. THE PAGE MUST BE ABLE TO TELL TWO GAMES APART")
# 🔴 THIS IS THE ONE THAT MATTERS. index.html matches a card to a board
# record on NEAREST FIRST PITCH, inside a window. If two records share a
# team-pair and sit closer together than that window, the page cannot
# choose between them and would guess -- which is precisely the bug.
# The window is READ OUT OF index.html so the two can never drift apart.
src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
m = re.search(r"BOARD_MATCH_WINDOW_MS\s*=\s*(\d+)\s*\*\s*(\d+)\s*\*\s*(\d+)", src)
ck("index.html still declares BOARD_MATCH_WINDOW_MS", bool(m))
if m:
    win_ms = int(m.group(1)) * int(m.group(2)) * int(m.group(3))
    print(f"  NOTE  the page's matching window is {win_ms/3600000:g} hours")
    from datetime import datetime
    def ts(x):
        return datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp() * 1000
    def _match(away, home, when):
        """index.html's rule, reimplemented: nearest commence, in window."""
        cand = [g for g in games if g["away"] == away and g["home"] == home]
        if not cand:
            return None
        if not when:
            return cand[0] if len(cand) == 1 else None
        t = ts(when)
        best, bg = None, float("inf")
        for g in cand:
            gap = abs(ts(g["commence"]) - t)
            if gap < bg:
                bg, best = gap, g
        return best if bg <= win_ms else None

    # ══════════════════════════════════════════════════════════════════
    # 🔴 ~~"no two records for one matchup sit inside the page's window"~~
    # STRUCK 2026-09-04, AND THE ARGUMENT IS MADE HERE.
    # ⛔ IT WAS A PROXY, AND THE PROXY WAS WRONG IN BOTH DIRECTIONS.
    # ⚠️ IT FIRED ON A CORRECT BOARD. `[measured 2026-09-04]` a Detroit /
    # Cleveland DOUBLEHEADER put two records exactly 4.00 hours apart
    # against a 4-hour window, and the run went red. But the window is a
    # MAXIMUM DISTANCE, not a resolution limit: nearest-match still picks
    # the right one. `test_board_match.js` passed 28 assertions on that
    # very board, including that pair -- **two checks disagreeing about
    # the same data, and the proximity one was the wrong question.**
    # 🔴 AND IT COULD NOT CATCH THE BUG IT WAS WRITTEN FOR. On 2026-08-26
    # six board records were the PREVIOUS NIGHT'S GAME -- one record per
    # matchup, no duplicates at all -- and cards showed CHC at -4000 with
    # a 4.5 total. **A proximity rule passes that without a murmur.**
    # ✅ THE REPLACEMENT ASKS THE REAL QUESTION, AND IT HAS GROUND TRUTH.
    # Every carded row stores the `game_id` of the record it was priced
    # from. So: run the PAGE'S OWN matcher on the row's first pitch, and
    # assert it returns THAT id. ⛔ Strictly harder -- it catches a wrong
    # match whether or not a duplicate exists, which is the whole class.
    # ══════════════════════════════════════════════════════════════════
    _ids = {str(g.get("id")) for g in games}
    _rows, _wrong, _lost, _nomatch = 0, [], 0, []
    # ⛔ `picks/` HOLDS TWO SPORTS AND A PLAIN `[-1:]` PICKS THE WRONG
    # ONE. `fb-ncaaf-latest.json` sorts AFTER every `2026-..-...json`, so
    # the naive form selected a FOOTBALL card, skipped it on `kind`, and
    # reconciled ZERO rows -- a vacuous pass, which is the same trap as
    # rule 76. Choose the newest MLB card explicitly.
    _cards = []
    for _f in glob.glob(os.path.join(ROOT, "picks", "*.json")):
        try:
            _d = json.load(open(_f, encoding="utf-8"))
        except Exception:
            continue
        if (_d.get("league") or "mlb").lower() != "mlb":
            continue
        if _d.get("kind") != "gizmos-card":
            continue
        _cards.append((_d.get("date") or "", _d))
    for _dt, _doc in sorted(_cards)[-1:]:
        _seen = set()
        for _r in _doc.get("picks", []):
            _key = (_r.get("away"), _r.get("home"), _r.get("commence"))
            if None in _key or _key in _seen:
                continue
            _seen.add(_key)
            _want = str(_r.get("game_id") or "")
            _got = _match(_r["away"], _r["home"], _r["commence"])
            if _want not in _ids:
                # 🔴 THE RECORD THIS ROW WAS PRICED FROM IS GONE. That is
                # only harmless if the page ALSO finds nothing -- the row
                # then renders with no odds, which is fail-closed.
                # ⛔ IF THE MATCHER STILL RETURNS SOMETHING, THE PAGE WILL
                # SHOW A PRICE FROM A RECORD THIS ROW WAS NEVER PRICED
                # FROM. That is the 2026-08-26 bug exactly -- and an
                # earlier draft of this check let it through, because
                # "rolled off" was treated as nothing-to-see rather than
                # as the dangerous half of the question.
                if _got is not None:
                    _wrong.append(
                        f"{_r['away']} @ {_r['home']} @{_r['commence']}: priced "
                        f"from {_want[:8]}, which is NOT on this board, yet the "
                        f"page would show {_got['commence']} "
                        f"({str(_got.get('id'))[:8]})")
                else:
                    _lost += 1      # rolled off, and the page shows no odds
                continue
            _rows += 1
            if _got is None:
                _nomatch.append(f"{_r['away']} @ {_r['home']}")
            elif str(_got.get("id")) != _want:
                _wrong.append(f"{_r['away']} @ {_r['home']} @{_r['commence']}: "
                              f"matched {_got['commence']} ({str(_got.get('id'))[:8]}) "
                              f"not {_want[:8]}")
    _dupes = sum(1 for v in
                 [[g for g in games if (g['away'], g['home']) == k]
                  for k in {(g['away'], g['home']) for g in games}] if len(v) > 1)
    print(f"  NOTE  {_dupes} matchup(s) appear twice on this board "
          f"(doubleheaders and next-day games -- not a defect by itself)")
    if _lost:
        print(f"  NOTE  {_lost} carded row(s) rolled off the board and the "
              f"page shows no odds for them — fail-closed, nothing to reconcile")
    # 🔴 ZERO ROWS IS NOT A PASS. A reconciliation that reconciled
    # nothing has asserted nothing, and this verifier's whole job is to
    # refuse a board it cannot vouch for. ⚠️ It is allowed to be zero for
    # ONE honest reason -- every carded record has rolled off the board --
    # and that reason is reported rather than assumed.
    ck(f"🔴 every carded row still matches the record it was PRICED from "
       f"({_rows} row(s) reconciled by game id)",
       not _wrong and (_rows > 0 or _lost > 0),
       "; ".join(_wrong[:3]) or
       ("" if (_rows or _lost) else "nothing reconciled and nothing rolled "
        "off — the card and the board share no rows at all"))
    # ⚠️ A row the matcher cannot resolve renders WITH NO ODDS. That is
    # fail-closed and correct, but it must be VISIBLE rather than silent.
    if _nomatch:
        print(f"  NOTE  {len(_nomatch)} row(s) resolve to no record and will "
              f"render without odds: {_nomatch[:3]}")

print(f"\n{'ALL BOARD CHECKS PASSED' if not fails else 'FAILURES: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
