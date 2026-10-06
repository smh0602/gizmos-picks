#!/usr/bin/env python3
"""
EVERY REPO ARTIFACT THE PAGE READS MUST HAVE A FRESHNESS CONTRACT ROW.

🔴🔴 THE CLASS, NOT THE FOUR FILES THAT WERE MISSING. `freshness.py`'s
own comment already states the rule it could not enforce:

    "an artifact nothing tracks is an artifact nobody misses"

…and it wrote that about `top-<season>.json.gz`, which shipped with no
entry and read `stale: False, ok: True` while not existing at all. ⛔ The
fix at the time was to add that one row. **This repo has shipped the
guard-the-instance mistake twice already (rules 246, 130)**, so the
question here is the class: *what does `index.html` fetch out of this
repository, and does the contract name it?*

`[measured 2026-09-19]` the answer was **three families, both leagues**:

    {lg}/latest/offense-by-position-{season}.json.gz   Trends, offence side
    {lg}/latest/players-{season}.json.gz               every football table
    {lg}/latest/dossiers.json.gz                       ALL EIGHT sections

⚠️ AND ONE THE CONTRACT CANNOT FIX: `data/nfl/latest/teams.json` is
fetched by the page for both leagues and **does not exist** — only
college has a `cfb-teams` writer. A contract row would go red forever
against a file nothing writes, which is a guard firing on the absence of
a FEATURE rather than on a defect. It is reported here as a `note()` and
nothing else; the writer is Sam's call, not a diff's.

══════════════════════════════════════════════════════════════════════
⛔ THE DERIVATION IS FROM THE PAGE, NEVER FROM A LIST TYPED HERE.

A list of names is the thing that goes stale (rule 166). This reads the
real `index.html`, pulls every `data/…` or `picks/…` path it fetches,
resolves the league placeholders against the real `LG_DATA` map, and
diffs against `freshness.contract()` for the real data directories.
✅ So an artifact added to the page next month is covered by this line
with no edit here.

⚠️ EXEMPTIONS ARE NAMED WITH A REASON, ONE LINE EACH, AND THEY ARE THE
ONLY WAY TO PASS. There is no wildcard and no "starts with" escape: a
new unexplained fetch fails this file until somebody writes down why.
"""
import datetime
import gzip
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section   # noqa: E402

import freshness as F                  # noqa: E402
import jsblock                         # noqa: E402

HTML = os.path.join(ROOT, "index.html")
NOW = datetime.datetime(2026, 9, 19, 17, 0, tzinfo=datetime.timezone.utc)

# The real data directories the collector passes, and the page's own map.
DATA_DIRS = ("data", "data/ncaaf", "data/nfl")
FB_DIRS = ("data/ncaaf", "data/nfl")

# ⛔ EVERY EXEMPTION CARRIES ITS REASON. Nothing else may pass.
EXEMPT = {
    "data/latest/freshness.json":
        "the contract's OWN OUTPUT — a row on it would ask the report "
        "whether the report is fresh",
    "picks/{day}.json":
        "MLB. ⛔ FROZEN, and already covered by the `card` row for the "
        "current slate; older days are the permanent record, which is "
        "never rewritten and therefore never late",
    "data/latest/mlb-refit.json":
        "written WEEKLY by its own workflow (`mlb-refit.yml`), not by "
        "collect.py — a contract row would send `converge` to rebuild it "
        "through a mode the collector does not have. Its Monday cron is "
        "stamped, so `runs_report.py` reports a missed fire",
    "data/nfl/latest/teams.json":
        "fetched by the page for BOTH leagues and NOTHING WRITES IT — "
        "only college has a `cfb-teams` writer. A row would be red "
        "forever against a missing FEATURE, not a defect (see the "
        "header). The writer is Sam's call",
}


def page_paths():
    """Every repo path `index.html` fetches, league placeholders resolved."""
    src = jsblock.source(HTML)
    out = set()
    # jget / jgetGz / fetch, single- double- or back-quoted
    # ⛔ THE LEAGUE-TEMPLATED FORMS ARE THE POINT, NOT AN EXTRA. A
    #    pattern anchored on `data/` misses every `${LG_DATA[...]}/...`
    #    fetch — which is BOTH football leagues and most of the page.
    #    `[caught 2026-09-19 by this file's own §1, on the first run]`
    for m in re.finditer(
            r"""(?:jgetGz|jget|fetch)\(\s*(['"`])"""
            r"""((?:data/|picks/|\$\{LG_DATA\[)[^'"`]*)\1""",
            src):
        out.add(m.group(2))
    # 🔴 AND ANY PATH-SHAPED LITERAL, NOT ONLY A DIRECT FETCH ARGUMENT.
    #    `[measured 2026-09-22]` the Track Record drill-down is fetched
    #    through a variable — `const path = ... || `${LG_DATA[lg]}/latest/
    #    record-detail.json.gz``; `jgetGz(path)` — so the pattern above
    #    never saw it and nothing in the contract covered it.
    for m in re.finditer(
            r"""(['"`])((?:data/|picks/|\$\{LG_DATA\[)[^'"`\s<>]*\.json(?:\.gz)?)\1""",
            src):
        # ⚠️ a literal still carrying a JS placeholder other than the
        #    league map and the season is a fragment `fbPath()` expands
        #    below — not a path.
        if re.search(r"\$\{(?!LG_DATA\[|season\})", m.group(2)):
            continue
        out.add(m.group(2))
    # `fbPath()` builds its own; take both stems it can return
    if "function fbPath" in src:
        body = jsblock.js_block("fbPath", HTML)
        for stem in re.findall(r"===\s*'off'\s*\?\s*'(\w+)'\s*:\s*'(\w+)'", body):
            for st in stem:
                out.add("${LG_DATA[LEAGUE]}/latest/%s-by-position-${season}"
                        ".json.gz" % st)
    return out


def resolve(p):
    """A page path -> the concrete repo paths it can name."""
    season = F.current_football_season(NOW)
    outs = []
    if "${LG_DATA[" in p:
        # ⚠️ THE MAP HOLDS MLB TOO, AND THESE CALL SITES STILL RESOLVE
        #    FOOTBALL-ONLY — said as a modelling decision, with the check
        #    that keeps it true in §1 rather than a hope in a comment.
        # 🔴 MLB is fetched by LITERAL path (`jget('data/latest/board.json')`)
        #    at its own call sites; the templated form is the football
        #    switcher, and the football tabs do not render for `mlb`
        #    (`LEAGUE === 'mlb' ? ... : ...`). ⛔ Resolving these to
        #    `data` as well would demand contract rows for MLB files the
        #    page never asks for — a guard firing on correct code, which
        #    is the other failure and not a safe one.
        for d in FB_DIRS:
            outs.append(re.sub(r"\$\{LG_DATA\[\w+\]\}", d, p))
    else:
        outs.append(p)
    # `picks/fb-${LEAGUE}-latest.json` names one file per league.
    expanded = []
    for o in outs:
        if "${LEAGUE}" in o:
            expanded += [o.replace("${LEAGUE}", lg) for lg in ("ncaaf", "nfl")]
        else:
            expanded.append(o)
    outs = expanded
    fixed = []
    for o in outs:
        o = (o.replace("${season}", str(season))
              .replace("${y}", str(season))
              .replace("${LEAGUE}", "LEAGUEPLACEHOLDER")
              .replace("${todayET()}", "{day}")
              .replace("${day}", "{day}"))
        fixed.append(o)
    return fixed


def covered():
    """Every target any contract row names, at any hour of a whole week.

    🔴 THE CONTRACT IS TIME-DEPENDENT AND THE QUESTION IS NOT.
    `_props_warranted()` withdraws `props-board` on a day with no game
    in the window, and `card-fb` is withdrawn before a league's first
    paid pull. ⛔ Asking at ONE instant would report an artifact
    unwatched because this happens to be Saturday afternoon — a check
    whose answer depends on when it runs is a check nobody can act on.
    ✅ So: does ANY reachable contract state name this file?
    """
    out = set()
    for day in range(7):
        for hour in (2, 8, 13, 18, 23):
            t = NOW.replace(hour=hour) + datetime.timedelta(days=day)
            for d in DATA_DIRS:
                for row in F.contract(d, now=t):
                    out.add(row[1][1])
    return out


# ══════════════════════════════════════════════════════════════════════
section("1. ⚠️ THE DERIVATION HAS A SUBJECT, OR EVERYTHING BELOW IS VACUOUS")
# ══════════════════════════════════════════════════════════════════════
_PAGE = page_paths()
ck("⚠️ the page's fetch targets are extractable at all",
   len(_PAGE) >= 8,
   "⛔ rule 67 — over an empty set this whole file passes having asked "
   "nothing. found %d: %s" % (len(_PAGE), sorted(_PAGE)))
ck("⚠️ ...including at least one built from the league map",
   any("LG_DATA" in p for p in _PAGE),
   "⛔ if the league-templated fetches stop matching, the football half "
   "of the question is silently not asked. found: %s" % sorted(_PAGE))
# ⛔ THE ASSUMPTION `resolve()` RESTS ON, CHECKED RATHER THAN ASSUMED.
#    If MLB ever moves to the templated form, football-only resolution
#    silently stops asking about MLB and this file goes quiet about it.
_SRC = jsblock.source(HTML)
ck("⛔ MLB is still fetched by LITERAL path, which is what makes the "
   "templated fetches football-only",
   all(("'%s'" % lit) in _SRC for lit in
       ("data/latest/board.json", "data/latest/record.json",
        "data/latest/news.json")),
   "🔴 `resolve()` maps `${LG_DATA[...]}` to the two football dirs "
   "ONLY, on the grounds that MLB has its own literal call sites. If "
   "MLB moved to the templated form that reasoning is void and every "
   "MLB artifact would go unasked.")
_COV = covered()
ck("⚠️ the contract has rows to compare against",
   len(_COV) >= 20,
   "⛔ rule 67 again, from the other side: an empty contract would make "
   "every page path look uncovered and this file would cry wolf on "
   "everything. found %d" % len(_COV))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 NOTHING THE PAGE READS IS UNWATCHED AND UNEXPLAINED")
# ══════════════════════════════════════════════════════════════════════
_UNCOVERED = []
for _p in sorted(_PAGE):
    for _r in resolve(_p):
        if _r in _COV or _r in EXEMPT:
            continue
        _UNCOVERED.append(_r)
ck("🔴🔴 EVERY ARTIFACT THE PAGE READS HAS A CONTRACT ROW OR A REASON",
   not _UNCOVERED,
   "⛔ an artifact nothing tracks is an artifact nobody misses — "
   "`freshness.py` says so itself, about the row it had to add after "
   "living through this. Add the row, or add an EXEMPT entry saying why "
   "a row would be wrong. %d unwatched:\n%s"
   % (len(_UNCOVERED), "\n".join("       %s" % u for u in _UNCOVERED)))

# ⛔ AND THE EXEMPTIONS MUST STILL BE REACHABLE. An exemption for a path
#    the page no longer fetches is a dead line that makes the list look
#    more considered than it is.
_RESOLVED = {r for p in _PAGE for r in resolve(p)}
_DEAD = sorted(set(EXEMPT) - _RESOLVED)
ck("⛔ ...and no exemption names a path the page stopped fetching",
   not _DEAD,
   "🔴 a stale exemption is a hole held open for a file nobody reads "
   "any more, and it hides the next one. dead: %s" % _DEAD)
ck("⚠️ ...and every exemption gives a reason, not just a name",
   all(len(v.strip()) >= 30 for v in EXEMPT.values()),
   "⛔ 'exempt' with no argument is how a list of four becomes a list of "
   "forty. short: %s" % [k for k, v in EXEMPT.items() if len(v.strip()) < 30])

# ══════════════════════════════════════════════════════════════════════
section("3. ✅ THE THREE ROWS THIS BRANCH ADDED ARE REALLY IN THE CONTRACT")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ NOT A RESTATEMENT OF §2. §2 asks whether the page is covered; this
#    asks whether the rows landed under the mode and deadline they were
#    meant to, because a row under the wrong mode is repaired by the
#    wrong job and a row under the wrong deadline is red at the wrong
#    time. ⛔ Both are derived from the contract, never typed.
for _d in FB_DIRS:
    _rows = F.contract(_d, now=NOW)
    _by = {}
    for _r in _rows:
        _by.setdefault(_r[1][1], _r)
    _season = F.current_football_season(NOW)
    _dos = _by.get("%s/latest/dossiers.json.gz" % _d)
    _card = _by.get("picks/fb-%s-latest.json" % _d.split("/")[-1])
    ck("✅ %s: the dossier rides the CARD's mode and deadline" % _d,
       bool(_dos) and bool(_card) and _dos[0] == _card[0]
       and _dos[2] == _card[2],
       "⛔ the dossier is built inside `card-fb`, so a different mode "
       "would ask a different job to repair it and a different deadline "
       "would be red at a time the builder was never due. dossier=%s "
       "card=%s" % (_dos and (_dos[0], _dos[2]), _card and (_card[0], _card[2])))
    _trend = _by.get("%s/latest/allowed-by-position-%d.json.gz" % (_d, _season))
    for _stem, _why in (("offense-by-position", "the offence side of Trends"),
                        ("players", "the log every football table is made from")):
        _new = _by.get("%s/latest/%s-%d.json.gz" % (_d, _stem, _season))
        ck("✅ %s: %s rides the SAME mode and deadline as the defence table"
           % (_d, _stem),
           bool(_new) and bool(_trend) and _new[0] == _trend[0]
           and _new[2] == _trend[2],
           "⛔ one builder writes all three — %s. A second mode would be "
           "a second job that does not exist. got=%s defence=%s"
           % (_why, _new and (_new[0], _new[2]),
              _trend and (_trend[0], _trend[2])))

# ⛔ AND NO NEW MODE WAS INVENTED, which is what "no new cron" means in
#    this file: converge plans its work from the modes these rows name.
_MODES = set()
for _d in DATA_DIRS:
    _MODES |= {r[0] for r in F.contract(_d, now=NOW)}
_KNOWN = {"scores", "results", "pitchers", "hitters", "record", "gamelines",
          "props-pitcher", "props-batter", "props-board", "lineups",
          "weather", "card", "news", "props-player", "card-fb",
          "cfb-probe", "nfl-logs", "fb-scores", "fb-record",
          "cfb-teams",
          # `[Sam, 2026-09-24]` the alt-line pull: an arm in `run_mode`, and
          # chained into the scheduled props pull (test_game_lines_fb.py).
          "alt-lines",
          # `[Sam, 2026-09-25]` the run-status file: an arm in `run_mode`
          # (test_runs_status.py §3), run hourly by runs.yml. Its row exists
          # only once that watcher is deployed.
          "runs",
          # `[Sam, 2026-10-06]` the MLB game model's own row: an arm in
          # `run_mode`, free (test_mlb_model_schedule.py).
          "game-model"}
# ⚠️ THIS LIST IS TYPED BY HAND, AND IT ONCE CARRIED `news-archive` — a
#    mode with no arm in `run_mode` — so this check passed while converge
#    printed "unknown mode" on every football pass. The question "does the
#    collector run it" is answered from collect.py's own source by
#    `test_contract_modes.py`; this list only asks "was a mode invented".
ck("🔴 no contract row names a mode the collector does not already have",
   not (_MODES - _KNOWN),
   "⛔ converge runs the mode a row names. A mode with no arm is a "
   "repair that can never run — rule 78 with extra steps. unknown: %s"
   % sorted(_MODES - _KNOWN))

# ══════════════════════════════════════════════════════════════════════
section("4. ⛔ THE NEW ROWS MUST NOT CRY WOLF ON A HEALTHY TREE")
# ══════════════════════════════════════════════════════════════════════
# 🔴 "A GUARD THAT FIRES ON CORRECT CODE IS THE OTHER FAILURE, NOT A SAFE
#    ONE." A contract row that is red the day it ships teaches everyone
#    to ignore the banner, which is the failure `freshness.py` argues
#    against in four separate places.
# ⚠️ THIS IS A STATEMENT ABOUT THE ROWS, NOT ABOUT THE TREE: it asks
#    only that the rows this branch added are not late while the file
#    they were modelled on — the defence table, and the card — is on
#    time.
# 🔴 `[2026-09-28]` ~~surveyed the LIVE tree with the real clock, while
#    naming its targets from the FROZEN season~~ — two defects in one
#    check. (P2) It asked production to stay silent: `card-fb` keeps the
#    card when the dossier build fails (collect.py: "the CARD IS FINE"),
#    so a live dossier going late beside a fresh card turned this red with
#    freshness.py unchanged — that is `verify_freshness.py`'s finding, not
#    this file's. (P1) One of each clock: from August 2027, once the 2027
#    logs exist, the survey names `-2027` paths while the targets said
#    `-2026`, and "no survey row" went red on correct code.
# ✅ So the question is asked of a TREE PINNED TO ONE INSTANT, at every
#    hour of a week: each sibling is written just after its own last
#    deadline, and each new row in the SAME run — its builder writes both
#    — so a new row can only be late if its DEADLINE differs. The targets
#    are read from the contract that survey uses, never rebuilt from a
#    clock. A planted twin writes the new row BEFORE its deadline and must
#    be caught, so the check is shown to bite. The live tree is reported.
_NEW_RX = re.compile(r"/latest/(dossiers|offense-by-position-\d{4}|players-\d{4})\.json\.gz$")
_MODEL_RX = re.compile(r"/latest/allowed-by-position-\d{4}\.json\.gz$")


def _iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path, when):
    """An artifact whose CONTENT carries its stamp (never an mtime)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    doc = {"built_at": _iso(when), "generated_at": _iso(when)}
    if path.endswith(".gz"):
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(doc, fh)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)


def _pairs(rows, d):
    """(new target row, the row it was modelled on) for league dir `d`,
    both taken from THIS survey — the same clock and the same tree."""
    card = "picks/fb-%s-latest.json" % d.split("/")[-1]
    by = {r["path"]: r for r in rows}
    model = [r for r in rows if _MODEL_RX.search(r["path"])]
    out = []
    for r in rows:
        if _NEW_RX.search(r["path"]):
            out.append((r, by.get(card) if "dossiers" in r["path"]
                        else (model[0] if len(model) == 1 else None)))
    return out


def _bad_of(rows, d):
    bad = []
    for r, m in _pairs(rows, d):
        if m is None:
            bad.append((r["path"], "no row it was modelled on"))
        elif r.get("stale") and not m.get("stale"):
            bad.append((r["path"], "stale while its own builder's other output "
                                   "(%s) is on time" % m["path"]))
    return bad


def _pinned(t, late=None):
    """Plant every league's gate files, the siblings and the new rows at
    instant `t` in a temp tree; survey there. `late` names one stem whose
    new row is written BEFORE its deadline. -> {d: survey rows}"""
    tree = tempfile.mkdtemp(prefix="pagecontract-")
    here = os.getcwd()
    try:
        os.chdir(tree)
        season = F.current_football_season(t)
        out = {}
        for d in FB_DIRS:
            lat = "%s/latest" % d
            # the gates: a props board (else card-fb is withdrawn) and the
            # season files (else the fallback names last season)
            _write("%s/props.json.gz" % lat, t)
            for stem in ("allowed-by-position", "offense-by-position", "players"):
                _write("%s/%s-%d.json.gz" % (lat, stem, season), t)
            rows = {r[1][1]: r for r in F.contract(d, now=t)}
            card ="picks/fb-%s-latest.json" % d.split("/")[-1]
            model = [p for p in rows if _MODEL_RX.search(p)]
            for sib in [card] + model:
                if sib in rows:
                    _write(sib, F.last_due(rows[sib][2], t) + datetime.timedelta(minutes=1))
            for path in rows:
                if not _NEW_RX.search(path):
                    continue
                sib = card if "dossiers" in path else (model[0] if model else None)
                if sib is None or sib not in rows:
                    continue
                when = F.last_due(rows[sib][2], t) + datetime.timedelta(minutes=1)
                if late and late in path:
                    when = F.last_due(rows[path][2], t) - datetime.timedelta(minutes=1)
                _write(path, when)
            out[d] = F.survey(d, now=t)
        return out
    finally:
        os.chdir(here)
        shutil.rmtree(tree, ignore_errors=True)


_INSTANTS = [NOW.replace(hour=h) + datetime.timedelta(days=day)
             for day in range(7) for h in (2, 8, 13, 18, 23)]
_BAD, _SEEN, _SIB_STALE = [], 0, []
for _t in _INSTANTS:
    for _d, _rows in _pinned(_t).items():
        _pr = _pairs(_rows, _d)
        _SEEN += len(_pr)
        _SIB_STALE += [(_iso(_t), m["path"]) for _r, m in _pr if m and m.get("stale")]
        _BAD += [(_iso(_t),) + b for b in _bad_of(_rows, _d)]
ck("⚠️ the pinned tree names all three new rows in both leagues, at every instant",
   _SEEN == 3 * len(FB_DIRS) * len(_INSTANTS),
   "⛔ rule 67: a target the survey does not name is a target this never "
   "asks about. seen %d of %d" % (_SEEN, 3 * len(FB_DIRS) * len(_INSTANTS)))
ck("⚠️ ...and every sibling written just after its deadline reads ON TIME",
   not _SIB_STALE,
   "⛔ a stale sibling makes the question below vacuous. %s" % _SIB_STALE[:3])
ck("⛔ no row added here is late while the file it was modelled on is not",
   not _BAD,
   "🔴 a row red on a tree its own builder just wrote is a row with the "
   "wrong deadline, and it would make the staleness banner noise. %s"
   % _BAD[:4])
# ⛔ AND THE CHECK CAN FAIL: a new row written BEFORE its own deadline,
#    beside an on-time sibling, is caught — one twin per kind of sibling.
for _stem, _sib in (("dossiers", "the card"), ("offense-by-position", "the defence table")):
    _tw = _pinned(NOW, late=_stem)
    _hits = [b for _d, _rows in _tw.items() for b in _bad_of(_rows, _d) if _stem in b[0]]
    ck("⛔ PLANTED: a %s row written before its deadline, beside %s on time, IS caught"
       % (_stem, _sib),
       len(_hits) == len(FB_DIRS),
       "one per league, got %s" % _hits)

# 📋 THE LIVE TREE, REPORTED — same clock and same tree for the survey AND
#    for which paths it names (never the frozen season).
_NOW = datetime.datetime.now(datetime.timezone.utc)
_LIVE = {d: F.survey(d, now=_NOW) for d in FB_DIRS}
_LBAD = [b for d, rows in _LIVE.items() for b in _bad_of(rows, d)]
note("%s live tree: %s"
     % ("⛔" if _LBAD else "✅",
        ("new rows late beside an on-time sibling — verify_freshness reports "
         "the site as stale: %s" % _LBAD) if _LBAD else
        "no new row is late while its sibling is on time"))
note("new rows and their ages right now: %s"
     % {r["path"]: r.get("age_min") for d, rows in _LIVE.items()
        for r, _m in _pairs(rows, d)})
note("⛔ WHAT THIS FILE DOES NOT CLAIM: that the contract's DEADLINES are "
     "right, or that an artifact with a row is fresh. It claims only that "
     "nothing the page reads is unwatched without a written reason. "
     "➡️ Whether a deadline matches the job that writes it is "
     "`test_fb_freshness.py`'s question.")

# @vacuity 🔴🔴 an artifact the page reads with no contract row is caught
#   file: freshness.py
#   find:          "Dossier — all eight per-game checks"))
#   with:          "Dossier — all eight per-game checks")) if False else None
#
# @vacuity ⛔ §4 pinned tree: a dossier row on a deadline other than the card's is late beside it
#   file: freshness.py
#   find: ("card-fb", ("file", f"{latest}/dossiers.json.gz"), T["card"], False,
#   with: ("card-fb", ("file", f"{latest}/dossiers.json.gz"), T["props"], False,
#
# @vacuity ⛔ §4 pinned tree: the players log on a deadline other than the defence table's
#   file: freshness.py
#   find: ("file", lpath), T["trends"], False,
#   with: ("file", lpath), T["card"], False,
#
# @vacuity ⛔ §4 planted twins: a new row written before its deadline IS caught
#   file: freshness.py
#   find: stale = built is None or (due is not None and built < due)
#   with: stale = built is None
