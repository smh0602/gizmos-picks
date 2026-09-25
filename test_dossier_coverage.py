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
import datetime
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


_PRESTRIP = {}


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
    # 🔴🔴 AND THE DATED ARCHIVES TOO — THE STRIP COVERED ONE PATH AND THE
    # WRITER WRITES TWO. `[measured 2026-09-18: this is what turned the
    # suite red on every collector run of the day.]`
    # ⛔ `data/<lg>/<date>/dossiers/HHMM.json.gz` is COMMITTED, so the
    # copytree above carries every previous run's archive in, and a check
    # meant to count WHAT THIS RUN WROTE was counting what every run ever
    # wrote. It read 1 on the day it was written — when none had been
    # committed yet — and could never read 1 again. A premise that is
    # true only on the day you write it is rule 67 with a fuse on it.
    for _old in glob.glob(os.path.join(d, "data", lg, "*", "dossiers")):
        shutil.rmtree(_old, ignore_errors=True)
    # ✅ AND THE STRIP IS RECORDED, NOT TRUSTED. The archive count below
    #    means "what this run wrote" ONLY if this is 0, so the premise is
    #    asserted rather than assumed — that assumption is the whole bug.
    _PRESTRIP[lg] = len(glob.glob(os.path.join(d, "data", lg, "*",
                                               "dossiers", "*.json.gz")))
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
    # ⚠️ THE ARTIFACT'S OWN DECLARED COUNT (files built before signal 9
    #    declared nothing and carry eight). `[2026-09-24]` None may vanish.
    _want = _dos.get("sections_declared", 8)
    ck(_sections == {_want},
       "   %s: every dossier carries all %d declared sections" % (_lg, _want),
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
    # ══════════════════════════════════════════════════════════════════
    # 🔴 EVERY NUMBER JOINED FROM THE SCHEDULE SAYS WHERE IT CAME FROM.
    # `[2026-09-18]` A week matched on the full pair, a week matched on
    # ONE side plus the date, and a week PLACED by the season calendar
    # are three different strengths of claim. ⛔ A number with no
    # provenance beside it gets read as the strongest one available.
    # ⚠️ DERIVED FROM THE ARTIFACT, never a literal count — the college
    # board moved 88 -> 90 mid-session, and a hard-coded number reddens
    # on correct code (the trap #51 fixed).
    # ══════════════════════════════════════════════════════════════════
    _rows = _dos.get("dossiers") or []
    _wk = [x for x in _rows if x.get("week") is not None]
    ck(bool(_wk) and all(x.get("week_basis") for x in _wk),
       "   %s: every week says where it came from (%d of %d row(s))"
       % (_lg, len([x for x in _wk if x.get("week_basis")]), len(_wk)),
       "⛔ a week from the season calendar and a week off a schedule row "
       "are both correct and are not the same claim. Silent: %s"
       % [(x.get("home_name"), x.get("week")) for x in _wk
          if not x.get("week_basis")][:3])
    _nowk = [x for x in _rows if x.get("week") is None]
    ck(not [x for x in _nowk if x.get("week_basis")],
       "   %s: ...and a row with no week claims no provenance for one"
       % _lg,
       "🔴 a basis beside an absent number is worse than no basis")
    _joined = [x for x in _rows if x.get("game_id") is not None]
    ck(bool(_joined) and all(x.get("row_basis") for x in _joined),
       "   %s: every joined schedule row says HOW it was joined (%d)"
       % (_lg, len(_joined)),
       "⛔ the pair key and one-side-plus-date are different strengths. "
       "Silent: %s" % [x.get("home_name") for x in _joined
                       if not x.get("row_basis")][:3])
    ck(not [x for x in _rows
            if x.get("game_id") is None
            and "REFUSED" not in (x.get("row_basis") or "REFUSED")],
       "   %s: ...and a row with no schedule row either says nothing or "
       "says it REFUSED" % _lg,
       "🔴 a silent refusal is indistinguishable from an absent row")
    _venue_ok = [s_ for x in _rows for s_ in x["sections"]
                 if s_.get("n") == 8 and s_.get("state") == "OK"]
    ck(bool(_venue_ok) and all(v.get("venue") for v in _venue_ok),
       "   %s: every venue section that reads OK carries a venue (%d)"
       % (_lg, len(_venue_ok)),
       "⛔ DO NOT INVENT A VENUE — and do not read OK without one "
       "either. Empty: %d" % len([v for v in _venue_ok
                                  if not v.get("venue")]))
    # ⚠️ AND THE DATED ARCHIVE COMES THROUGH THE SAME WRITER, for free.
    _arch = glob.glob(os.path.join(_d, "data", _lg, "*", "dossiers",
                                   "*.json.gz"))
    ck(_PRESTRIP.get(_lg) == 0,
       "   %s: ⛔ the fixture inherited ZERO archives before the run "
       "(%s)" % (_lg, _PRESTRIP.get(_lg)),
       "🔴🔴 THE PREMISE OF THE NEXT CHECK. `data/<lg>/<date>/dossiers/` "
       "is COMMITTED, so copytree carries every previous run's archive "
       "in. Counting those as this run's output is what turned the suite "
       "red on every collector run of 2026-09-18, and it read 1 only on "
       "the day it was written. A count of THIS RUN'S output is a claim "
       "about the strip first.")
    ck(len(_arch) == 1,
       "   %s: one dated, write-once archive beside `latest/`" % _lg,
       "⛔ rule 285 — and a SECOND archive path would be a second thing "
       "to drift. Found: %s" % [os.path.relpath(a, _d) for a in _arch])
    # 🔴 AND IT IS THE SHAPE `daystore.py` DECLARES, NOT MERELY ONE FILE.
    # ⛔ The old error text claimed to guard against "a SECOND archive
    #    path" and NOTHING checked the path at all — an archive written
    #    as `dossiers/1808-nfl.json.gz`, or under `<lg>/dossiers/`, or
    #    dated to the wrong day, all passed a bare count of 1. Rule 249:
    #    a check must ask its own prose.
    _rel = [os.path.relpath(a, os.path.join(_d, "data", _lg))
            for a in _arch]
    _today = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d")
    _shape = [r for r in _rel
              if re.fullmatch(re.escape(_today) + r"[/\\]dossiers[/\\]"
                              r"(?:[01]\d|2[0-3])[0-5]\d\.json\.gz", r)]
    ck(len(_shape) == len(_arch) and bool(_arch),
       "   %s: ...and it is `<UTC today>/dossiers/HHMM.json.gz` (%s)"
       % (_lg, ", ".join(_rel) or "none"),
       "⛔ `daystore.path()` declares the shape and this is the only "
       "place that reads it back. A file that is not a valid clock time, "
       "or sits under another day or another directory, is a SECOND "
       "archive path — which is the thing the count was always supposed "
       "to be about. Off-shape: %s" % [r for r in _rel if r not in _shape])
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


# ══════════════════════════════════════════════════════════════════════
section("4. 🔴🔴 A `CARRIED` NAME THE SLATE LACKS IS NOT A DEFECT")
# ══════════════════════════════════════════════════════════════════════
# `[measured 2026-09-19]` THIS FILE PASSED 42/42 AGAINST `main` AT 10:11Z
# AND FAILED 4 OF 42 AGAINST `main` AT 16:04Z — **with no code change to
# it or to `dossier_fb.py`.** The only difference was 72 files the
# collector had committed under `data/`.
#
# ⛔ THE CAUSE WAS IN THE PRODUCT. `dossier_fb.audit()` refused to write
# the WHOLE dossier unless all seven `CARRIED` subtree names appeared
# somewhere in the output — and `meetings` is only there if some game on
# the board has a prior meeting inside 365 days. On a board where none
# does, the football tabs got nothing at all.
# ⚠️ Production was fine that day (all seven present, 87 of 87 college
# dossiers written) — but a one-game NFL Thursday between two teams who
# have not met would have written NOTHING.
#
# ✅ THE ANTI-PADDING QUESTION THE REFUSAL WAS REACHING FOR IS ASKED
#    STATICALLY, AND IT IS STRICTLY HARDER: every `CARRIED` name must be
#    a dict key THIS MODULE EMITS. A junk name added to silence a finding
#    fails that on a quiet Tuesday as surely as on a full Saturday, where
#    the old form could be satisfied by nothing more than a busy slate.
import ast as _ast                                          # noqa: E402
import dossier_fb as _D                                      # noqa: E402

_SRC = open(os.path.join(ROOT, "dossier_fb.py"), encoding="utf-8").read()


def _emitted_keys(src):
    """Every string key this module WRITES — dict literals AND subscript
    assignments.

    ⚠️ BOTH SHAPES, because the first draft of this check only read
    `ast.Dict` and reported `closing` as unemitted — it is written
    `d["closing"] = {…}` at line 435, a subscript, and it is one of the
    seven names the check exists to validate. ⛔ A scan that misses a
    real emitter accuses correct code, which is the same failure this
    whole section is about.
    """
    out = set()
    for n in _ast.walk(_ast.parse(src)):
        if isinstance(n, _ast.Dict):
            for k in n.keys:
                if isinstance(k, _ast.Constant) and isinstance(k.value, str):
                    out.add(k.value)
        elif isinstance(n, (_ast.Assign, _ast.AnnAssign)):
            tgts = n.targets if isinstance(n, _ast.Assign) else [n.target]
            for t in tgts:
                if isinstance(t, _ast.Subscript) \
                        and isinstance(t.slice, _ast.Constant) \
                        and isinstance(t.slice.value, str):
                    out.add(t.slice.value)
    return out


def _artifact_keys():
    """Every key that has ever appeared in a STORED dossier artifact.

    ✅ THE SECOND, INDEPENDENT LEG. A junk name added to `CARRIED` to
    silence a finding has never been written by anything, so it appears
    in no artifact — on any day. ⛔ Unlike the refusal this replaces, the
    answer does not move with today's board: it is the union over every
    stored dossier, `latest/` and the dated archives.
    """
    out = set()
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "*", "latest",
                                           "dossiers.json.gz"))) + \
             sorted(glob.glob(os.path.join(ROOT, "data", "*", "*",
                                           "dossiers", "*.json.gz"))):
        d = _jz(p)
        st = [d]
        while st:
            o = st.pop()
            if isinstance(o, dict):
                out.update(o.keys())
                st.extend(o.values())
            elif isinstance(o, list):
                st.extend(o)
    return out


_KEYS = _emitted_keys(_SRC)
_unemitted = [c for c in _D.CARRIED if c not in _KEYS]
note("dict-literal keys this module emits: %d · CARRIED: %s"
     % (len(_KEYS), list(_D.CARRIED)))
ck(not _unemitted,
   "🔴🔴 every CARRIED name is a dict key `dossier_fb.py` actually emits",
   "⛔ THE ANTI-PADDING GUARD. A name here that nothing emits is an "
   "exception surface with nothing behind it, and the walk would be "
   "skipping a subtree that could hold a verdict. Unemitted: %s"
   % (_unemitted,))
ck(len(_KEYS) > 50 and "sections" in _KEYS and "closing" in _KEYS,
   "⚠️ ...and the key scan really read the module, subscripts included",
   "⛔ rule 67: a scan that returns nothing makes the check above pass "
   "over an empty set — and one that misses `d[\"closing\"] = {…}` "
   "accuses correct code. found %d keys" % len(_KEYS))

# ✅ SECOND LEG, INDEPENDENT OF THE SOURCE: every CARRIED name has
#    actually been written into a stored artifact at some point.
_ART = _artifact_keys()
_never = [c for c in _D.CARRIED if c not in _ART]
note("keys across every stored dossier artifact: %d" % len(_ART))
ck(len(_ART) > 500,
   "⚠️ ...and there are stored dossiers to read",
   "⛔ rule 67 again. found %d keys" % len(_ART))
ck(not _never,
   "✅ every CARRIED name has really appeared in a stored dossier",
   "⛔ a name nothing has ever written is an exception surface with "
   "nothing behind it. Never seen: %s" % (_never,))
# ✅ AND IT IS PROVEN TO BITE, against a planted junk name.
ck([c for c in tuple(_D.CARRIED) + ("no_such_subtree",)
    if c not in _KEYS] == ["no_such_subtree"],
   "🔴 ...and a planted junk name in CARRIED is caught",
   "a guard that cannot fail is not a guard (rule 67)")

# ── the absence itself, driven on a document whose answer is known ────
_full = {"dossiers": [{"sections": [
    {"live": {}, "closing": {}, "meetings": {}, "by_team": {},
     "by_player": {}, "by_defence": {}, "weather": {}}]}]}
_found, _absent = _D.audit(_full)
ck(_found == [] and _absent == [],
   "✅ a document carrying every CARRIED subtree reports nothing absent",
   "found=%r absent=%r" % (_found, _absent))

_nomeet = json.loads(json.dumps(_full))
del _nomeet["dossiers"][0]["sections"][0]["meetings"]
_found, _absent = _D.audit(_nomeet)
ck(_absent == ["meetings"],
   "🔴🔴 a slate with no prior meeting reports `meetings` ABSENT",
   "⛔ and the caller must REPORT that, never refuse on it — refusing is "
   "what wrote nothing to the football tabs. got %r" % (_absent,))
ck(_found == [],
   "⛔ ...and an absent subtree does not invent a verdict finding",
   "found=%r" % (_found,))

# 🔴 THE REFUSAL THAT MUST STILL BITE — a real judgement field.
_verdict = json.loads(json.dumps(_full))
_verdict["dossiers"][0]["sections"][0]["confidence"] = 0.8
_found, _absent = _D.audit(_verdict)
ck(len(_found) == 1 and _found[0][1] == "confidence",
   "🔴🔴 a numeric judgement field IS still found, and still stops the write",
   "⛔ this artifact combines, ranks and scores NOTHING, and that gate is "
   "untouched by today's change. got %r" % (_found,))

# ⛔ AND THE WRITER NO LONGER RETURNS 1 ON AN ABSENCE — read structurally,
#    because the alternative is rebuilding a whole slate to observe it.
_gate = _SRC.split("bad, carried_absent = audit(doc)", 1)
ck(len(_gate) == 2,
   "⚠️ the writer's gate is where this test thinks it is",
   "⛔ if this split fails the two checks below read nothing (rule 67)")
_after = _gate[1][:1200]
ck('doc["carried_absent"] = carried_absent' in _after,
   "🔴 an absent subtree is recorded ON THE DOCUMENT",
   "⛔ a reader has to be able to see which source subtrees this slate "
   "carried. got:\n%s" % _after[:400])
_branch = "\n".join(l for l in _after.split("if bad:")[0].split("\n")
                    if not l.strip().startswith("#"))
ck("return 1" not in _branch,
   "🔴🔴 ...and the absence branch does NOT return 1",
   "⛔ THIS IS THE DEFECT. A `return 1` here writes nothing to the "
   "football tabs on a board that is entirely fine. ⚠️ Comments are "
   "stripped first — the struck ~~`return 1`~~ in the comment beside it "
   "is the record of the fix, not the fix undone. got:\n%s"
   % _branch[:400])
