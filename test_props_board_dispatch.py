#!/usr/bin/env python3
"""`props-board` runs the FOOTBALL join on a football league.

🔴🔴 `[measured 2026-09-21, runs #1633 / #1634 / #1638]` `run_mode`'s
`props-board` branch called the MLB-only `collect_props_board()` for every
league. Every football converge pass that planned `props-board` raised

    RuntimeError: no game logs at all — run the hitters and pitchers jobs first

and exited 1, and the workflow then blamed whatever mode the cron had
launched: "mode 'news' failed", "mode 'gamelines' failed", "mode
'props-player' failed" — while each of those modes had SUCCEEDED.

✅ Driven through the real `run_mode`, not read out of the source: both
builders are replaced by recorders, so this asks which one the dispatcher
actually calls, per league. ⛔ MLB is pinned too — the fix must not move
baseball onto the football join.

⚠️ No network, no data files, no clock.

# @vacuity 🔴🔴 football props-board runs the football join
#   file: collect.py
#   find:                 collect_props_board_fb()        # the BOARD, not a credit count
#   with:                 collect_props_board()
# `[2026-09-26]` ~~find: `left = (collect_props_board() if LEAGUE == "mlb"`~~
#   -- that line was rewritten when `left` stopped holding the football
#   board (test_run_mode_left.py); same intent, the football branch.
"""
import tempfile

import collect as K
from tcheck import ck, section

calls = []
K.collect_props_board = lambda *a, **k: calls.append("mlb")
K.collect_props_board_fb = lambda *a, **k: calls.append("fb")
K._ensure_cfb_team_directory = lambda *a, **k: None
K.DATA = tempfile.mkdtemp()          # nothing may land in the real tree

section("1. 🔴🔴 EACH LEAGUE GETS ITS OWN JOIN")
for lg, want in (("nfl", ["fb"]), ("ncaaf", ["fb"]), ("mlb", ["mlb"])):
    calls.clear()
    K.LEAGUE = lg
    err = None
    try:
        K.run_mode("props-board")
    except BaseException as e:           # noqa: BLE001 -- report, not hide
        err = "%s: %s" % (type(e).__name__, e)
    ck("%s: props-board calls the %s builder, once"
       % (lg, "football" if want == ["fb"] else "MLB"),
       calls == want and err is None,
       "called %s, raised %s" % (calls, err))
