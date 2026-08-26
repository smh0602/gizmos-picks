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
    pairs = {}
    for g in games:
        pairs.setdefault((g["away"], g["home"]), []).append(g)
    clash = []
    for (a, h), v in pairs.items():
        if len(v) < 2:
            continue
        v = sorted(v, key=lambda x: x["commence"])
        for x, y in zip(v, v[1:]):
            if abs(ts(y["commence"]) - ts(x["commence"])) <= win_ms:
                clash.append(f"{a} @ {h}: {x['commence']} and {y['commence']}")
    ck(f"no two records for one matchup sit inside the page's window "
       f"({sum(1 for v in pairs.values() if len(v) > 1)} matchup(s) appear twice)",
       not clash, "; ".join(clash[:3]))

print(f"\n{'ALL BOARD CHECKS PASSED' if not fails else 'FAILURES: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
