#!/usr/bin/env python3
"""
A LEAGUE WITH A BOARD AND NO DOSSIER MUST FAIL SOMETHING.

🔴🔴 THE DEFECT, LIVE ON main UNTIL `[2026-09-17]`. `dossier_fb.build()`
opened with:

    if lg != "nfl":
        log("dossier_fb: %s is not built yet — NFL only.")
        return 0

⛔ **`return 0` IS SUCCESS.** The college card built, the chained call
ran, nothing raised, nothing was written, and every check in this repo
passed. The college board carried **88 games with no signals 1–8 at all**
— on the biggest slate of the week — and the refusal was explicit in the
LOG and invisible to every WATCHER.

➡️ **AN UNIMPLEMENTED BRANCH MUST RETURN A STATE THE WATCHERS CAN SEE, OR
IT IS INDISTINGUISHABLE FROM A WORKING ONE.** The more carefully that
refusal was written, the less anything noticed it.

⚠️ AND THE DISTINGUISHING FACT WAS MEASURED, not assumed: `card-fb`
rebuilt the college card at 11:48:14Z that day and no dossier came with
it. Not a dropped cron, not "it has not fired yet".

══════════════════════════════════════════════════════════════════════
⛔ THE LEAGUE LIST IS DERIVED. `if league == "ncaaf"` would guard the
INSTANCE, and this repo has shipped that mistake twice (rules 246, 130).
The leagues checked are the ones `collect.yml` routes to `card-fb` — so
the day a third league gets a card, this check covers it with no edit.
⚠️ MLB is not among them and must never be: it has no `card-fb` arm, and
`CLAUDE.md` forbids a scheduled check that reads MLB state.

══════════════════════════════════════════════════════════════════════
⛔ IT RUNS THE BUILDER; IT DOES NOT READ THE ARTIFACT ON DISK.
🔴 THE FIRST DRAFT OF THIS FILE CHECKED FOR `dossiers.json.gz` UNDER
`data/`, AND THAT WAS THE WRONG QUESTION. Only the collector writes that
file, so on a fresh checkout — which is every CI run — it is absent until
the next `card-fb` fires. The check would have been RED ON ITS OWN MERGE
and gone green later on its own, which is rule 273: a guard that needs
history false-alarms on its deploy day, and this session already shipped
that mistake once today (`test_accumulators.py`'s empty-tree premise).
✅ So it BUILDS each league in a throwaway tree and asks whether a
dossier came out. Deterministic, works on a fresh checkout, and it still
catches the exact hole — `build("ncaaf")` returned 0 and wrote nothing.
⚠️ Whether the artifact is CURRENT on disk is a freshness question, and
`freshness.py` owns that. Conflating the two is what made the first
draft wrong.
══════════════════════════════════════════════════════════════════════
"""
import glob
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

from tcheck import ck, note, section, copy_module

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import wfroutes  # noqa: E402


# ══════════════════════════════════════════════════════════════════════
# @vacuity a league with a board and a card must have a dossier
#   file: dossier_fb.py
#   with: LEAGUES_BUILT = ("nfl",)   # ⛔ the refusal this file exists for
#   find: LEAGUES_BUILT = ("nfl", "ncaaf")
# ══════════════════════════════════════════════════════════════════════


def _jz(p):
    try:
        return json.load(gzip.open(p, "rt"))
    except Exception:
        return None


def tree(lg):
    """A throwaway repo with one league's data and the builder."""
    d = tempfile.mkdtemp(prefix="doscov-")
    shutil.copytree(os.path.join(ROOT, "data", lg),
                    os.path.join(d, "data", lg))
    os.makedirs(os.path.join(d, "picks"), exist_ok=True)
    for f in glob.glob(os.path.join(ROOT, "picks", "fb-%s-*.json" % lg)):
        shutil.copy(f, os.path.join(d, "picks"))
    # ⛔ STRIPPED, so "a dossier came out" means THIS run produced one.
    #    The same premise that went stale in `test_accumulators.py`.
    for rel in ("data/%s/latest/dossiers.json.gz" % lg,):
        if os.path.exists(os.path.join(d, rel)):
            os.remove(os.path.join(d, rel))
    copy_module("dossier_fb", d)
    copy_module("collect", d)
    return d


section("1. ⚠️ THE LEAGUES ARE DERIVED FROM THE WORKFLOW, NOT LISTED HERE")
_WF = open(os.path.join(ROOT, ".github/workflows/collect.yml"),
           encoding="utf-8").read()
_LEAGUES = sorted({lg for _c, lg, modes in wfroutes.parse_routes(_WF)
                   if "card-fb" in modes.split()})
ck(len(_LEAGUES) >= 2,
   "⚠️ %d league(s) are routed to `card-fb` (%s)"
   % (len(_LEAGUES), ", ".join(_LEAGUES)),
   "⛔ a one-league or empty list would make the sweep below vacuous "
   "(rule 67) — and a hardcoded 'ncaaf' would guard the instance")
ck("mlb" not in _LEAGUES,
   "⛔ ...and MLB is not one of them",
   "🔴 CLAUDE.md forbids a scheduled check that reads MLB state, and the "
   "freeze is not a flag this file may flip")

section("2. 🔴🔴 EVERY ROUTED LEAGUE BUILDS A DOSSIER OVER ITS OWN BOARD")
_seen = []
for _lg in _LEAGUES:
    _d = tree(_lg)
    _p = subprocess.run([sys.executable, "-B", "dossier_fb.py"], cwd=_d,
                        timeout=1200, capture_output=True, text=True,
                        env=dict(os.environ, LEAGUE=_lg))
    _out = (_p.stdout or "") + (_p.stderr or "")
    _dos = _jz(os.path.join(_d, "data", _lg, "latest", "dossiers.json.gz"))
    _board = json.load(open(os.path.join(_d, "data", _lg, "latest",
                                         "board.json"), encoding="utf-8"))
    _games = len(_board.get("games") or [])
    ck(_dos is not None,
       "🔴🔴 %s: RUNNING THE BUILDER PRODUCES A DOSSIER" % _lg,
       "⛔ `return 0` on an unimplemented path is a SILENT PRODUCT HOLE — "
       "the card builds, the chained call runs, nothing raises, and the "
       "board has no signals on it. rc=%s %s" % (_p.returncode, _out[-300:]))
    if _dos is None:
        continue
    _n = _dos.get("n_dossiers") or 0
    _sk = len(_dos.get("skipped") or [])
    _seen.append((_lg, _games, _n, _sk, len(_dos.get("one_sided") or [])))
    ck(_games and _n + _sk >= _games,
       "   %s: all %d board game(s) described or NAMED as skipped (%d + %d)"
       % (_lg, _games, _n, _sk),
       "⛔ a game that is neither described nor named has silently "
       "vanished from the report")
    _sections = {len(x.get("sections") or []) for x in (_dos.get("dossiers") or [])}
    ck(_sections == {8},
       "   %s: every dossier carries all eight sections" % _lg,
       "⛔ a section that cannot answer says UNAVAILABLE; it never "
       "vanishes. Counts seen: %s" % sorted(_sections))
    _bad = sorted({s.get("basis") for x in (_dos.get("dossiers") or [])
                   for s in x["sections"]
                   if s.get("basis") not in (None, "MARKET", "DESCRIPTIVE")})
    ck(not _bad,
       "   %s: every number is MARKET or DESCRIPTIVE — zero MODEL (rule 55)"
       % _lg,
       "⛔ this artifact combines, ranks and scores NOTHING. Found: %s" % _bad)
    # ⚠️ AND THE DATED ARCHIVE COMES THROUGH THE SAME WRITER, for free.
    _arch = glob.glob(os.path.join(_d, "data", _lg, "*", "dossiers",
                                   "*.json.gz"))
    ck(len(_arch) == 1,
       "   %s: one dated, write-once archive beside `latest/`" % _lg,
       "⛔ rule 285 — and a SECOND archive path would be a second thing "
       "to drift. Found: %s" % [os.path.relpath(a, _d) for a in _arch])
    shutil.rmtree(_d, ignore_errors=True)
note("   league / board games / dossiers / named skips / one-sided: %s"
     % (_seen,))
note("⚠️ ONE-SIDED IS NOT A FAILURE. `teams.json` is the FBS list, so an "
     "FCS opponent is absent from it by construction. Those games ARE "
     "described and the missing side is NAMED — dropping them would lose "
     "18 pct of the Saturday board.")
