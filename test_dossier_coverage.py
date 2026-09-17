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
import ast
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
# ⛔ DERIVED FROM THE BUILDER, NOT LISTED. A section is PAIR-WISE if it
#    takes both `home` and `away` and uses them — so venue, whose
#    subject is the ground, is correctly not one, and a pair-wise
#    section added tomorrow is covered without editing this file.
_DSRC = open(os.path.join(ROOT, "dossier_fb.py"), encoding="utf-8").read()
_PAIRWISE_NAMES = set()
for _fn in ast.parse(_DSRC).body:
    if not (isinstance(_fn, ast.FunctionDef) and _fn.name.startswith("s_")):
        continue
    _a = {x.arg for x in _fn.args.args}
    _u = {x.id for x in ast.walk(_fn) if isinstance(x, ast.Name)}
    if not ({"home", "away"} <= (_a & _u)):
        continue
    for _c in ast.walk(_fn):
        if (isinstance(_c, ast.Call)
                and getattr(_c.func, "id", "") in ("unavailable",
                                                   "no_opponent")
                and len(_c.args) >= 2
                and isinstance(_c.args[1], ast.Constant)):
            _PAIRWISE_NAMES.add(_c.args[1].value)
ck(len(_PAIRWISE_NAMES) >= 3,
   "⛔ the PAIR-WISE sections are derived from the builder (%s)"
   % ", ".join(sorted(_PAIRWISE_NAMES)),
   "🔴 rule 67: an empty set would make every check below pass over "
   "nothing. Found %s" % sorted(_PAIRWISE_NAMES))
_seen, _totpart = [], []
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
    # ══════════════════════════════════════════════════════════════════
    # 🔴🔴 AND NO ROW WITH AN UNIDENTIFIED OPPONENT CARRIES AN `OK`
    # PAIR-WISE SECTION — ON THE REAL BOARD, FOR EVERY ROUTED LEAGUE.
    # `[2026-09-17]` 19 of 88 college rows published a null opponent with
    # five sections reading OK, including head to head asserting "no
    # meeting between these two" about a comparison never attempted.
    # ⛔ THE PAIR-WISE LIST IS DERIVED FROM THE BUILDER'S OWN SOURCE, not
    # written here: a section is pair-wise if it takes BOTH `home` and
    # `away` and uses them. Naming §2/§5/§6 would guard those three and
    # leave the next one open (rules 246, 130).
    # ⚠️ NFL contributes 0 partial rows and that is not a weakness of
    # this check — it is the measurement that explains why nothing caught
    # this for NFL. The sweep's own denominator is asserted below.
    # ══════════════════════════════════════════════════════════════════
    _partial = [x for x in (_dos.get("dossiers") or [])
                if x.get("unresolved_side")]
    _okp = sorted({(s.get("n"), s.get("name")) for x in _partial
                   for s in x["sections"]
                   if s.get("name") in _PAIRWISE_NAMES
                   and s.get("state") == "OK"})
    ck(not _okp,
       "   %s: %d partial row(s), and no pair-wise section reads OK on "
       "one" % (_lg, len(_partial)),
       "⛔ a section whose subject is the PAIR cannot answer when one "
       "side is unknown. Still OK: %s" % _okp)
    _unnamed = sorted({(x.get("home_name"), s.get("n")) for x in _partial
                       for s in x["sections"]
                       if s.get("name") in _PAIRWISE_NAMES
                       and x["unresolved_side"] not in (s.get("why") or "")})
    ck(not _unnamed,
       "   %s: ...and every such refusal NAMES the side it could not "
       "identify" % _lg,
       "⛔ 'not available' with no subject is unreadable, and the board "
       "always holds the name. Unnamed: %s" % _unnamed[:4])
    ck(all(x.get("away_name") and x.get("home_name")
           for x in (_dos.get("dossiers") or [])),
       "   %s: every row carries the board's own names for both sides"
       % _lg,
       "⛔ A GAME THE READER CAN NAME MUST NEVER RENDER AS None. Rows "
       "missing a name: %s" % [(x.get("home"), x.get("away"))
                               for x in (_dos.get("dossiers") or [])
                               if not (x.get("away_name")
                                       and x.get("home_name"))][:4])
    ck(_dos.get("n_partial") == len(_partial),
       "   %s: ...and the partial count is STATED (%s), not inferred"
       % (_lg, _dos.get("n_partial")),
       "⛔ rule 166: \"88 of 88\" read as full coverage while 19 rows had "
       "no identified opponent. Says %r, rows say %d"
       % (_dos.get("n_partial"), len(_partial)))
    _totpart.append(len(_partial))
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
# ══════════════════════════════════════════════════════════════════════
# ⛔⛔ ~~`ck(sum(_totpart) >= 1)`~~ — I WROTE THAT FLOOR AND IT WOULD HAVE
# REDDENED THE SUITE ON `main` ON CORRECT CODE. `[measured 2026-09-17,
# hours after writing it]`
# 🔴 THE PARTIAL-ROW COUNT IS A FACT ABOUT TODAY'S BOARD, NOT ABOUT THE
# CODE. Across the 36 college board snapshots stored under
# `data/ncaaf/*/gamelines/`, partial rows run 0 to 41 — and **2 of them
# carried ZERO, both on 2026-09-13**, 1 of the 16 days stored. Mid-slate
# on a Saturday the lower-division games have already kicked off, so the
# UPCOMING board is all top-division and the count is legitimately 0.
# ⛔ A floor demanding one would have failed a scheduled run and filed an
# issue about a perfectly good board — CLAUDE.md: a guard that fires on
# correct code is the other failure, not a safe one, and rule 238 says
# crying wolf kills the channel.
# ✅ SO THE COUNT IS REPORTED, NOT ASSERTED, and the rule-67 obligation
# moves to section 3 where it belongs: the case is DRIVEN on a synthetic
# row every run, whatever the board happens to hold today.
# ══════════════════════════════════════════════════════════════════════
note("⚠️ %d real partial row(s) on today's boards %s. ⛔ NOT A FLOOR: "
     "measured 0-41 across 36 stored college boards, ZERO on 2026-09-13 "
     "— legitimately, because mid-Saturday the lower-division games have "
     "already kicked off. Section 3 drives the case unconditionally."
     % (sum(_totpart), list(zip(_LEAGUES, _totpart))))
note("⚠️ ONE-SIDED IS NOT A FAILURE. The team file is the top-division "
     "list, so a lower-division opponent is absent from it by "
     "construction. Those games ARE described — §1's price is real and "
     "Sam can bet it — and every section that compares the two REFUSES "
     "BY NAME. Dropping them would lose 18 pct of the Saturday board.")

section("3. 🔴🔴 AND THE CASE IS DRIVEN WHATEVER TODAY'S BOARD HOLDS")
# ══════════════════════════════════════════════════════════════════════
# ⛔ UNCONDITIONAL, NOT "ONLY WHEN THE REAL BOARD IS THIN". A branch that
# executes on 1 day in 16 is a branch whose first real run is in
# production (ledger rule 235), and the 6 pct of days it covers are
# exactly the days the checks above prove nothing. One extra build is a
# couple of seconds; a guard nobody has driven is free and worthless.
# ⚠️ THREE GAMES ONLY. The question is whether the builder refuses, not
# whether it can describe a slate — the section above already did that on
# every real game.
# ══════════════════════════════════════════════════════════════════════
_lg3 = "ncaaf" if "ncaaf" in _LEAGUES else _LEAGUES[0]
_d3 = tree(_lg3)
_bp3 = os.path.join(_d3, "data", _lg3, "latest", "board.json")
_b3 = json.load(open(_bp3, encoding="utf-8"))
_keep = (_b3.get("games") or [])[:2]
ck(len(_keep) == 2,
   "⚠️ the fixture board really has games to build on (%d)" % len(_keep),
   "⛔ rule 67: an empty fixture would make every check below pass over "
   "nothing")
_b3["games"] = _keep + [dict(_keep[0], away="Slippery Rock Aardvarks")]
json.dump(_b3, open(_bp3, "w", encoding="utf-8"))
_p3 = subprocess.run([sys.executable, "-B", "dossier_fb.py"], cwd=_d3,
                     timeout=1200, capture_output=True, text=True,
                     env=dict(os.environ, LEAGUE=_lg3))
_out3 = (_p3.stdout or "") + (_p3.stderr or "")
_dos3 = _jz(os.path.join(_d3, "data", _lg3, "latest", "dossiers.json.gz"))
ck(_dos3 is not None and _p3.returncode == 0,
   "   %s: an unidentifiable opponent does not cost the slate its "
   "dossiers" % _lg3,
   "⛔ §1 is real and the game is bettable — the refusal is per SECTION, "
   "never the whole run. rc=%s %s" % (_p3.returncode, _out3[-300:]))
_row3 = [x for x in ((_dos3 or {}).get("dossiers") or [])
         if x.get("away_name") == "Slippery Rock Aardvarks"]
ck(len(_row3) == 1,
   "🔴🔴 %s: THE GAME IS DESCRIBED AND NAMED, NOT DROPPED" % _lg3,
   "⛔ A GAME THE READER CAN NAME MUST NEVER RENDER AS None, and it must "
   "not vanish either. Got %s"
   % [x.get("away_name") for x in ((_dos3 or {}).get("dossiers") or [])])
_s3 = {x.get("name"): x for x in ((_row3 or [{}])[0].get("sections") or [])}
_ok3 = sorted(n for n in _s3
              if n in _PAIRWISE_NAMES and _s3[n].get("state") == "OK")
ck(_s3 and not _ok3,
   "   🔴 ...and NO pair-wise section reads OK on it (%d checked)"
   % len([n for n in _s3 if n in _PAIRWISE_NAMES]),
   "⛔ a section whose subject is the PAIR cannot answer when one side "
   "is unknown. Still OK: %s" % _ok3)
ck(all("Slippery Rock Aardvarks" in (_s3[n].get("why") or "")
       for n in _s3 if n in _PAIRWISE_NAMES),
   "   ⛔ ...and each refusal NAMES the side it could not identify",
   "🔴 'not available' with no subject is unreadable. Got %s"
   % [(n, (_s3[n].get("why") or "")[:50]) for n in sorted(_s3)])
ck("No meeting between these two" not in ((_s3.get("Head to head") or {})
                                          .get("why") or ""),
   "   🔴🔴 ...and head to head does not assert a check that never ran",
   "⛔ a fact about a query is not a fact about the world — there is no "
   "'these two'. Got: %s"
   % ((_s3.get("Head to head") or {}).get("why") or "")[:140])
ck((_s3.get("Market") or {}).get("state") == "OK",
   "   ✅ ...while the market section STAYS OK",
   "⛔ do not suppress the game: the price is real. Got %s"
   % (_s3.get("Market") or {}).get("state"))
shutil.rmtree(_d3, ignore_errors=True)
