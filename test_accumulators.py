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
# @vacuity a partial possession table is never written at all
#   file: nfl.py
#   find: if len(teams) < TOP_MIN_TEAMS:
#   with: if False:
#
# 📌 THE OTHER TWO POSSESSION MUTATIONS MOVED WITH THE CODE THEY DRIVE.
#    `"seconds": int(...)` and the per-drive key now live in
#    `possession.py` and are declared in `test_possession.py`, which
#    drives them on two whole real seasons. ⛔ Not dropped — a mutation
#    declared against a line that no longer exists is reported MALFORMED
#    by the harness, which is how this was noticed.
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

section("4. 📌 THE POSSESSION ARTIFACT — WIRED HERE, JUDGED ELSEWHERE")
# ⛔ THE POSSESSION GUARDS MOVED, THEY WERE NOT DROPPED, and they got
#    stronger on the way. `[2026-09-17]` The builder used to emit RAW
#    DERIVED SECONDS, and raw seconds are biased by how much of a game's
#    clock the derivation happened to see — on the college side that
#    inverted the ranking outright. Both leagues now go through ONE
#    implementation of the coverage-and-share maths.
#      `test_possession.py`      — possession.py: the floor, the share,
#                                  per-game averaging, and the NFL
#                                  regulation-clock identity, driven on
#                                  two WHOLE real seasons.
#      `test_cfb_possession.py`  — the college derivation that produces
#                                  the seconds in the first place.
# ✅ WHAT BELONGS HERE IS THE ACCUMULATOR QUESTION: the builder is hooked
#    into a mode a cron reaches, and it refuses rather than half-writes.
_NS = json.load(gzip.open(os.path.join(
    ROOT, "research", "pbp_possession_sample_2025.json.gz"), "rt"))
_npay, _nrep = nfl.possession_from_rows(_NS["rows"], 2025, lambda *a: None)
ck(_npay is not None and _nrep["usable"],
   "⚠️ the NFL builder produces a table from the real season",
   "⛔ a builder that produces nothing would make the wiring question "
   "below meaningless. rep=%s" % {k: _nrep.get(k) for k in
                                  ("teams", "error")})
ck("nfl-logs" in _REACHABLE,
   "🔴 ...and it is built in `nfl-logs`, which a cron arm names",
   "⛔ rule 78 cuts the other way for a builder whose INPUT is the "
   "expensive thing: this rides a download `nfl-logs` already pays for. "
   "Reachable: %s" % sorted(_REACHABLE))
ck("build_possession" in (_BRANCHES.get("nfl-logs") or ""),
   "   ...by name, in that branch",
   "⛔ a builder nothing calls is a builder that rots")
_few = [r for r in _NS["rows"] if (r.get("posteam") or "") in ("BUF", "NO")]
_p2, _r2b = nfl.possession_from_rows(_few, 2025, lambda *a: None)
ck(_p2 is None,
   "🔴🔴 ...AND IT REFUSES A PARTIAL TABLE RATHER THAN HALF-WRITING ONE",
   "⛔ possession present for some teams and absent for the rest is "
   "missingness clustered BY TEAM — the shape that killed CFB targets. "
   "Got %s" % str(_p2)[:120])
ck("writing NOTHING" in (_r2b.get("error") or ""),
   "   ...saying so in the probe it writes either way",
   str(_r2b.get("error"))[:160])
note("📌 The possession artifact is built in `nfl-logs`, which pays the "
     "play-by-play download already. `test_possession.py` owns what the "
     "numbers in it must MEAN; this file owns that it is reachable.")
