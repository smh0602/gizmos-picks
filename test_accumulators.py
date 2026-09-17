#!/usr/bin/env python3
"""
A TOOL WIRED INTO A MODE NOBODY SCHEDULES HAS NOT BEEN WIRED.

🔴🔴 THIS REPO HAS SHIPPED THAT TWICE. `t54.py`'s counter sat in
`collect.py`'s `fb-record` branch — a mode that appears in `collect.yml`
exactly ONCE, in the workflow_dispatch dropdown text — so it had never run
and `t54.json` had never existed on disk. ⛔ And the sting: `own_mean` was
added to `record_fb.py` SPECIFICALLY so T54 could accumulate. The
predictor was carried onto every graded row and nothing consumed it.

⚠️ SO THE GUARD IS ON THE CLASS. The reachable mode set is DERIVED from
`collect.yml`, and EVERY mode branch that publishes an artifact of its own
must sit in that set. That catches the next orphaned accumulator with no
edit to this file — it is not a check that `t54` is in `card-fb`.
"""
import glob
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, note, section, copy_module

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import wfroutes  # noqa: E402
import nfl  # noqa: E402


# ══════════════════════════════════════════════════════════════════════
# @vacuity an accumulator must sit in a mode some cron routes to
#   file: collect.py
#   find: elif mode == "card-fb":
#   with: elif mode == "card-fb-renamed":
#
# @vacuity t54.json must actually be WRITTEN by the scheduled mode
#   file: collect.py
#   find: write(f"{LATEST}/t54.json", _rep)
#   with: pass  # write(f"{LATEST}/t54.json", _rep)
#
# @vacuity possession is stored in SECONDS, never the source string
#   file: nfl.py
#   find: "seconds": int(a["seconds"]),
#   with: "seconds": "%d:%02d" % (a["seconds"] // 60, a["seconds"] % 60),
#
# @vacuity a partial possession table is never written at all
#   file: nfl.py
#   find: if len(agg) < TOP_MIN_TEAMS:
#   with: if False:
#
# @vacuity possession counts each DRIVE once, not once per play
#   file: nfl.py
#   find: key = (r.get(gidc), r.get(drvc))
#   with: key = (r.get(gidc), r.get(drvc), id(r))
# ══════════════════════════════════════════════════════════════════════


def modes_of(src):
    """{mode: branch body} for every `elif mode == "..."` in run_mode().

    ⚠️ THE LAST BRANCH RUNS TO THE END OF THE FILE unless it is bounded,
    which silently handed `nfl-probe` every `write()` in the module below
    it. Each body stops at the first line indented less than its own.
    """
    out, parts = {}, re.split(r'\n        elif mode == "([^"]+)":', src)
    for i in range(1, len(parts), 2):
        body = []
        for ln in parts[i + 1].split("\n"):
            if ln.strip() and not re.match(r"^ {12,}", ln):
                break
            body.append(ln)
        out[parts[i]] = "\n".join(body)
    return out


# 🔴 A BRANCH THAT PUBLISHES AN ARTIFACT OF ITS OWN. `write(f"{LATEST}/..")`
# is the collector's publish helper — anchored so `fh.write(f"...")` inside
# a text report is not mistaken for one.
_PUBLISHES = re.compile(
    r'(?<![.\w])write\(\s*f"(\{(?:LATEST|base|DATA|PICKS)\}[^"]*)"')


section("1. 🔴🔴 EVERY MODE THAT PUBLISHES AN ARTIFACT IS CRON-REACHABLE")
_CSRC = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
_WF = open(os.path.join(ROOT, ".github/workflows/collect.yml"),
           encoding="utf-8").read()
_ROUTES = wfroutes.parse_routes(_WF)
# ⚠️ An arm may name SEVERAL modes ("news card-fb"), so the set is split.
_REACHABLE = {m for _c, _lg, arm in _ROUTES for m in arm.split()}
ck(len(_REACHABLE) >= 5,
   "⚠️ the reachable mode set is DERIVED from collect.yml (%d mode(s))"
   % len(_REACHABLE),
   "⛔ an empty set would make every claim below vacuous (rule 67). Got %s"
   % sorted(_REACHABLE))
_BRANCHES = modes_of(_CSRC)
ck(len(_BRANCHES) >= 10,
   "⚠️ ...and the collector's mode branches parsed (%d)" % len(_BRANCHES),
   "Got %s" % sorted(_BRANCHES)[:6])
# ⛔ AND THE BOUNDING IS PROVEN, not trusted: an unbounded last branch
# swallows the rest of the module and every claim below turns to mush.
ck(all(len(b) < 20000 for b in _BRANCHES.values())
   and "freshness.json" not in (_BRANCHES.get("nfl-probe") or ""),
   "⚠️ ...each bounded to its own body, not to the end of the file",
   "🔴 `nfl-probe` is the last branch; unbounded it inherits "
   "`_publish_freshness`'s writes and reads as a publisher it is not")

_publishers = {m: sorted(set(_PUBLISHES.findall(b)))
               for m, b in sorted(_BRANCHES.items())}
_publishers = {m: w for m, w in _publishers.items() if w}
ck(len(_publishers) >= 2,
   "⚠️ ...over a real set of publishing branches (%d)" % len(_publishers),
   "⛔ a sweep that found no publishers would pass having checked nothing "
   "(rule 67). Got %s" % _publishers)
_orphans = {m: w for m, w in _publishers.items() if m not in _REACHABLE}
ck(not _orphans,
   "🔴🔴 NO MODE PUBLISHES AN ARTIFACT FROM A BRANCH NO CRON REACHES",
   "⛔ THIS IS THE DEFECT. `t54.py`'s counter wrote `{LATEST}/t54.json` "
   "from the `fb-record` branch, which appears in collect.yml only in the "
   "workflow_dispatch dropdown text — so it had never run and the file "
   "had never existed. Orphaned: %s" % _orphans)
note("   publishers: %s" % {m: w[:2] for m, w in _publishers.items()})

# ⚠️ AND THE FINDING ITSELF, STATED AS A MEASUREMENT RATHER THAN A MEMORY.
ck("fb-record" not in _REACHABLE,
   "⚠️ `fb-record` is STILL reached by no cron — the finding was real",
   "🔴 nothing was moved INTO it; the accumulator was moved OUT")
# ⚠️ ASKED OF THE CODE, NOT THE PROSE. The struck-through comment left
# behind in `fb-record` names t54 on purpose, and a substring test would
# have failed on it — rule 249, a check that reads its own explanation.
_code = lambda m: "\n".join(
    l for l in (_BRANCHES.get(m) or "").split("\n")
    if l.strip() and not l.lstrip().startswith("#"))
ck("t54" not in _code("fb-record") and "t54" in _code("card-fb"),
   "🔴 ...and T54's counter now sits in `card-fb`, which eight arms name",
   "Got fb-record code=%r" % _code("fb-record")[:160])
# ⛔ WHY CONVERGE DOES NOT SAVE IT, MEASURED not assumed: `fb-record`'s
# freshness row probes `{latest}/record.json`, and `card-fb` writes that
# file itself by calling `build_record_fb()`. The row is therefore never
# stale, converge never plans the mode, and the branch never executes.
# `test_fb_freshness.py` already records the same fact from the other
# side: its `drivers` map reads {"fb-record": "card-fb"}.
_FBFRESH = open(os.path.join(ROOT, "test_fb_freshness.py"),
                encoding="utf-8").read()
ck('"fb-record": "card-fb"' in _FBFRESH
   and "build_record_fb()" in (_BRANCHES.get("card-fb") or ""),
   "🔴 ...and converge cannot save it: `card-fb` writes `record.json`, so "
   "`fb-record`'s freshness row is never stale and is never planned",
   "⛔ if that stops being true this reasoning is stale and the PR body "
   "that quoted it is wrong")


def tree():
    d = tempfile.mkdtemp(prefix="accum-")
    shutil.copytree(os.path.join(ROOT, "data", "nfl"),
                    os.path.join(d, "data", "nfl"))
    os.makedirs(os.path.join(d, "picks"), exist_ok=True)
    for f in glob.glob(os.path.join(ROOT, "picks", "fb-nfl-*.json")):
        shutil.copy(f, os.path.join(d, "picks"))
    copy_module("collect", d)
    copy_module("card_fb", d)
    copy_module("dossier_fb", d)
    copy_module("t54", d)
    return d


section("2. 🔴 t54.json IS PRODUCED BY RUNNING THE REAL MODE")
# ⛔ NOT ASSERTED ABOUT. The whole defect was that the hook existed and
#    the artifact did not, so only running the mode answers it.
_d = tree()
_p54 = os.path.join(_d, "data/nfl/latest/t54.json")
ck(not os.path.exists(_p54),
   "⚠️ the tree starts with NO t54.json",
   "⛔ finding a file that was already there proves nothing")
_r = subprocess.run([sys.executable, "collect.py", "card-fb"], cwd=_d,
                    timeout=1200, capture_output=True, text=True,
                    env=dict(os.environ, LEAGUE="nfl"))
_out = _r.stdout + _r.stderr
ck(os.path.exists(_p54),
   "🔴🔴 RUNNING `card-fb` WRITES t54.json — FOR THE FIRST TIME EVER",
   "⛔ it had never existed on disk. rc=%s %s" % (_r.returncode, _out[-300:]))
_T = json.load(open(_p54, encoding="utf-8")) if os.path.exists(_p54) else {}
ck(bool(_T.get("test") == "T54" and _T.get("verdict")),
   "   ...carrying a real verdict (%s)" % _T.get("verdict"),
   str(_T)[:200])
ck((_T.get("rows_with_own_mean") or 0) > 0,
   "🔴 ...and own_mean is finally being CONSUMED (%s of %s rows)"
   % (_T.get("rows_with_own_mean"), _T.get("graded_rows")),
   "⛔ THE STING: own_mean was added to record_fb.py specifically so T54 "
   "could accumulate, and nothing read it for weeks")

section("3. ⛔ THE CARD STILL SHIPS IF AN ACCUMULATOR FAILS")
# 🔴 The card is the product; a counter is a note about it.
_cards = glob.glob(os.path.join(_d, "picks", "fb-nfl-2*.json"))
ck(_cards, "⚠️ the same run produced a card", _out[-200:])
_d2 = tree()
_t54p = os.path.join(_d2, "t54.py")
open(_t54p, "w", encoding="utf-8").write(
    "raise RuntimeError('t54 is deliberately broken for this check')\n")
_r2 = subprocess.run([sys.executable, "collect.py", "card-fb"], cwd=_d2,
                     timeout=1200, capture_output=True, text=True,
                     env=dict(os.environ, LEAGUE="nfl"))
_cards2 = glob.glob(os.path.join(_d2, "picks", "fb-nfl-2*.json"))
ck(_cards2,
   "🔴🔴 A BROKEN ACCUMULATOR DOES NOT LOSE THE CARD",
   "⛔ the card is the product. rc=%s %s"
   % (_r2.returncode, (_r2.stdout + _r2.stderr)[-300:]))
ck("T54 did not run" in (_r2.stdout + _r2.stderr),
   "   ...and the failure is LOGGED, not swallowed",
   "🔴 a counter that fails silently is the same defect one level down")

section("4. 🔴 POSSESSION IS SECONDS, AN INTEGER, ON THE REAL COLUMN")
# ⛔ DRIVEN ON A REAL SLICE of nflverse play_by_play_2025, committed at
#    research/pbp_possession_sample_2025.json.gz — the ACTUAL column and
#    the ACTUAL `M:SS` format, not a fixture somebody invented.
_S = json.load(gzip.open(os.path.join(
    ROOT, "research", "pbp_possession_sample_2025.json.gz"), "rt"))
_rows = _S["rows"]
ck(len(_rows) > 1000, "⚠️ the real sample has plays to aggregate (%d)"
   % len(_rows), "⛔ a thin sample cannot clear the team bar and the "
   "section below would prove nothing")
ck(any(re.match(r"^\d+:\d\d$", str(r.get("drive_time_of_possession") or ""))
       for r in _rows),
   "⚠️ ...and the column really is `M:SS` in the source",
   "🔴 the whole reason this is parsed at write time")
_pay, _rep = nfl.possession_from_rows(_rows, 2025, lambda *a: None)
ck(_pay is not None, "the aggregation produced a table",
   "rep=%s" % _rep)
if _pay:
    _bad = [(t, v) for t, d in _pay["teams"].items()
            for k, v in d.items() if not isinstance(v, int)
            or isinstance(v, bool)]
    ck(not _bad,
       "🔴🔴 EVERY VALUE IS AN INT — NO STRING SURVIVES TO A CONSUMER",
       "⛔ `\"7:42\" + \"3:10\"` does not raise, it produces `\"7:423:10\"`. "
       "A string that looks numeric is how a sum silently becomes "
       "concatenation. Offenders: %s" % _bad[:4])
    ck(_pay["unit"] == "seconds", "   ...and the unit is declared")
    _spd = [d["seconds_per_drive"] for d in _pay["teams"].values()]
    ck(all(20 <= v <= 600 for v in _spd),
       "🔴 ...and a drive lasts a plausible number of seconds (%d-%d)"
       % (min(_spd), max(_spd)),
       "⛔ COUNTING EACH DRIVE ONCE PER PLAY would multiply every total by "
       "its play count — the numbers would still be ints and still be "
       "wrong. Got %s" % sorted(_spd)[:5])
    ck(len(_pay["teams"]) >= nfl.TOP_MIN_TEAMS,
       "   ...across %d teams" % len(_pay["teams"]))
    # ⛔ AND THE PHYSICAL BAR, WHICH IS WHAT ACTUALLY CATCHES PER-PLAY
    #    COUNTING. `seconds_per_drive` cannot: if every play becomes its
    #    own "drive" the mean per drive barely moves, because the column
    #    is the DRIVE's time repeated on each play. Two teams share one
    #    hour of game clock, so the sample's seconds-per-game must land
    #    near 3600 — MEASURED at 3600.6 on the real slice, and about 8x
    #    that if the column is summed row by row.
    _games = len({r.get("game_id") for r in _rows if r.get("game_id")})
    # ⚠️ SUMMED DEFENSIVELY so a non-int value fails the check ABOVE and
    #    does not take the rest of the file down with a TypeError.
    _tot = sum(d["seconds"] for d in _pay["teams"].values()
               if isinstance(d["seconds"], int)
               and not isinstance(d["seconds"], bool))
    _per_game = _tot / _games if _games else 0
    ck(_games > 4 and 3000 <= _per_game <= 4200,
       "🔴🔴 A GAME'S TWO TEAMS SHARE ONE HOUR OF CLOCK (%.0fs over %d "
       "games)" % (_per_game, _games),
       "⛔ `drive_time_of_possession` IS REPEATED ON EVERY PLAY OF THE "
       "DRIVE. Summing it row by row multiplies every total by the play "
       "count — the numbers stay integers and the per-drive mean stays "
       "plausible, so only the game-clock total catches it.")

section("5. ⛔ NO USABLE COLUMN -> NO ARTIFACT, AND SECTION 6 SAYS SO")
# 🔴 A PARTIAL TABLE IS WORSE THAN NONE: it reads as a real number for
#    some teams and silence for the rest, which is missingness clustered
#    BY TEAM — the shape that killed CFB targets.
_no_col = [{k: v for k, v in r.items() if k != "drive_time_of_possession"}
           for r in _rows[:500]]
_p2, _r2b = nfl.possession_from_rows(_no_col, 2025, lambda *a: None)
ck(_p2 is None, "🔴 a season with the column MISSING writes NOTHING",
   "⛔ rather than a table nobody can trust. Got %s" % str(_p2)[:120])
ck("does not carry the columns" in (_r2b.get("error") or ""),
   "   ...and the report says which columns were missing",
   str(_r2b))
_few = [r for r in _rows if r.get("posteam") in ("BUF", "NO")]
_p3, _r3 = nfl.possession_from_rows(_few, 2025, lambda *a: None)
ck(_p3 is None,
   "🔴🔴 ...AND A TWO-TEAM TABLE IS REFUSED TOO",
   "⛔ THE PARTIAL CASE IS THE DANGEROUS ONE — it looks like data. Got %s"
   % str(_p3)[:120])
ck("writing NOTHING" in (_r3.get("error") or ""),
   "   ...saying it chose to write nothing", str(_r3))

# ✅ AND SECTION 6 STAYS UNAVAILABLE WITH ITS REASON — driven both ways.
import dossier_fb as DF  # noqa: E402

_s6 = DF.s_possession("BUF", "NO", 2025, data=os.path.join(_d, "data/nfl"))
ck(_s6["state"] == "UNAVAILABLE",
   "🔴 with no artifact, section 6 is UNAVAILABLE",
   "Got %s" % _s6)
ck("remedy" in _s6 and "drive_time_of_possession" in (_s6.get("why") or ""),
   "   ...naming the column and the remedy", str(_s6)[:200])
_fake = os.path.join(_d, "data/nfl/latest/top-2025.json.gz")
with gzip.open(_fake, "wt") as fh:
    json.dump({"season": 2025, "unit": "seconds",
               "teams": {"BUF": {"drives": 10, "seconds": 1800,
                                 "seconds_per_drive": 180}}}, fh)
_s6b = DF.s_possession("BUF", "NO", 2025, data=os.path.join(_d, "data/nfl"))
ck(_s6b["state"] == "OK" and "BUF" in (_s6b.get("by_team") or {}),
   "✅ ...and it reads the artifact the moment one exists",
   "⛔ a section that can never turn OK is decoration. Got %s" % _s6b)
note("📌 The possession artifact is built in `nfl-logs`, which pays the "
     "play-by-play download already — rule 78 cuts the other way for a "
     "builder whose INPUT is the expensive thing. `nfl-logs` is in the "
     "derived reachable set, asserted in section 1.")
